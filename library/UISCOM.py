# coding=utf-8
from __future__ import unicode_literals

import json
import logging
import urllib
import urllib2
import time


from PyQt4 import QtGui, QtCore

from library import database
from library.Utils import forceString, forceInt, forceRef, forceBool

try:
    import websocket
except ImportError:
    websocket = None

STATE_CONNECTED = 'connected'
STATE_DISCONNECTED = 'disconnected'
STATE_DISABLED = 'disabled'
STATE_NO_MAPPING = 'noMapping'
STATE_STOPPED = 'stopped'

_RECONNECT_DELAYS = (15, 30, 60)
#_DISABLED_RETRY_DELAY  = 180

INFORMER_CALL_PRESET_REMINDER = 'reminder'
INFORMER_CALL_PRESET_CANCEL = 'cancel'

class UISComError(Exception):
    def __init__(self, status, detail):
        Exception.__init__(self, '{0}: {1}'.format(status, detail))
        self.status = status
        self.detail = detail

class _UISComRestAPI(object):
    """
    Объект отвечающий за REST часть клиента
    Собирает, проверяет и отправляет http запросы клиента
    """

    HEADERS = {b'Accept': b'application/json'}

    def __init__(self, servicesUrl, timeout=15):
        self._baseUrl = servicesUrl + '/api/UISCom/'
        self._timeout = timeout

    def _request(self, endpoint, payload=None):
        url = self._baseUrl + endpoint
        data = None
        headers = self.HEADERS
        if payload is not None:
            data = json.dumps(payload)
            headers[b'Content-Type'] = b'application/json'
        request = urllib2.Request(url, data, headers)
        try:
            response = urllib2.urlopen(request, timeout=self._timeout)
            responseData = response.read()
            return json.loads(responseData)
        except urllib2.HTTPError as e:
            try:
                detail = json.loads(e.read()).get('detail')
            except ValueError:
                detail = ''
            raise UISComError(e.code, detail or self._defaultStatusCodeDetail(e.code))
        except urllib2.URLError:
            raise UISComError(0, u'Ошибка подключения к серверу сервисов')
        except Exception as e:
            raise UISComError(0, 'Сервис недоступен: {0}'.format(e))


    @staticmethod
    def _defaultStatusCodeDetail(statusCode):
        return {
            400: 'Некорректный номер телефона',
            403: 'Отсутствует сопоставление сотрудника с employee_id UIS',
            423: 'Сервис "Телефония UIS" отключен',
            502: 'Ошибка на стороне UIS'
        }.get(statusCode, 'Неизвестная ошибка (HTTP {statusCode})'.format(statusCode=statusCode))

    def status(self):
        return self._request(endpoint='Status')

    def pending(self, personId, afterId=None):
        """
        Отправляет запрос для просмотра новых сообщений
        """
        # Режим poll: события после курсора afterId. Без afterId сервер вернёт текущий last_id.
        endpoint = 'pending?person_id={0}'.format(personId)
        if afterId is not None:
            endpoint += '&after_id={0}'.format(afterId)
        return self._request(endpoint)

    def makeCall(self, contactPhone, virtualPhoneNumber=None):
        result = self._request(endpoint='Call', payload={
            'person_id': QtGui.qApp.userId,
            'phone': contactPhone,
            'virtual_phone_number': virtualPhoneNumber,
        })
        data = (result.get('uis') or {}).get('data') or {}
        return data.get('call_session_id')

    def makeInformerCall(self, contactPhone, ttsMessage=None, preset=None, virtualPhoneNumber=None):
        # Шлём и tts_message, и preset — канал (TTS или media) выбирает сервер по informer_use_tts
        result = self._request(endpoint='CallInformer', payload={
            'person_id': QtGui.qApp.userId,
            'phone': contactPhone,
            'virtual_phone_number': virtualPhoneNumber,
            'tts_message': ttsMessage,
            'preset': preset,
        })
        data = (result.get('uis') or {}).get('data') or {}
        return data.get('call_session_id')

    def callsHistory(self, dateBeg, dateEnd, limit=100, offset=0, phone=None):
        # phone задан -> отчёт по конкретным номерам (сервис фильтрует по contact_phone_number)
        endpoint = 'CallsHistory?date_beg={0}&date_end={1}&limit={2}&offset={3}'.format(urllib.quote(dateBeg),
                                                                                    urllib.quote(dateEnd),
                                                                                    limit, offset)
        phones = phone if isinstance(phone, (list, tuple)) else ([phone] if phone else [])
        for ph in phones:
            if ph:
                endpoint += '&phone={0}'.format(urllib.quote(str(ph)))
        return self._request(endpoint)

class _UISComWSThread(QtCore.QThread):

    messageReceived = QtCore.pyqtSignal(object)
    stateChanged = QtCore.pyqtSignal(object)

    def __init__(self, wsUrl, parent=None):
        super(_UISComWSThread, self).__init__(parent)
        self._wsUrl = wsUrl
        self._stopRequested = False
        self._wsApp = None
        self._closeCode = None


    # колбэки вебсокета
    def _onOpen(self, *args):
        self._closeCode = None
        self.stateChanged.emit(STATE_CONNECTED)

    def _onClose(self, *args):
        if len(args) >= 2 and isinstance(args[1], int):
            self._closeCode = args[1]

    def _onError(self, *args):
        pass
        # Можно вывести какой то сигнал, ну или просто забить
        #print('UIS: ошибка WS: {0}'.format(args[-1]))

    def _onMessage(self, *args):
        raw = args[-1]
        try:
            if forceBool(QtGui.qApp.preferences.appPrefs.get('UISComIncCallNotificationEnabled', True)):
                self.messageReceived.emit(json.loads(raw))
        except (ValueError, TypeError):
            pass
            #print('UIS: не JSON сообщение по WS: {0}'.format(raw))

    # основная часть
    def _sleepInterruptible(self, seconds):
        for _ in range(int(seconds * 10)):
            if self._stopRequested:
                return
            time.sleep(0.1)

    def requestStop(self):
        self._stopRequested = True
        if self._wsApp is not None:
            try:
                self._wsApp.close()
            except Exception:
                pass

    def run(self):
        if websocket is None:
            #print('UIS: вебсокет не импортирован, websocket отключен')
            self.stateChanged.emit(STATE_DISCONNECTED)
            return

        attempt = 0
        while not self._stopRequested:
            self._wsApp = websocket.WebSocketApp(
                self._wsUrl,
                on_open=self._onOpen,
                on_error=self._onError,
                on_close=self._onClose,
                on_message=self._onMessage,
            )

            # можно добавить пинги по таймингу ping_interval= + ping_timeout=
            self._wsApp.run_forever()

            if self._stopRequested:
                break

            if self._closeCode == 4401:
                # В БД нет соответствия person_id <-> employee_id
                self.stateChanged.emit(STATE_NO_MAPPING)
                return
            elif self._closeCode == 4423:
                # В СП сервис отключен
                self.stateChanged.emit(STATE_DISABLED)
                return
                # delay = _DISABLED_RETRY_DELAY
                # attempt = 0
            else:
                # а тут фиг знает что произошло, так что пытаемся ловить коннект
                self.stateChanged.emit(STATE_DISCONNECTED)
                delay = _RECONNECT_DELAYS[min(attempt, len(_RECONNECT_DELAYS) -1)]
                attempt += 1

            self._sleepInterruptible(delay)

        self.stateChanged.emit(STATE_STOPPED)

class _UISCallThread(QtCore.QThread):

    callFinished = QtCore.pyqtSignal(object)

    def __init__(self, api, contactPhone, informerCall=False, virtualPhoneNumber=None, ttsMessage='', preset=None, parent=None):
        super(_UISCallThread, self).__init__(parent)
        self._api = api
        self._contactPhone = contactPhone
        self._informerCall = informerCall
        self._virtualPhoneNumber = virtualPhoneNumber
        self._ttsMessage = ttsMessage
        self._preset = preset

    def run(self):
        try:
            if not self._informerCall:
                sessionId = self._api.makeCall(self._contactPhone, self._virtualPhoneNumber)
            else:
                sessionId = self._api.makeInformerCall(self._contactPhone, self._ttsMessage,
                                                       preset=self._preset,
                                                       virtualPhoneNumber=self._virtualPhoneNumber)

            self.callFinished.emit({
                'ok': True,
                'contactPhone': self._contactPhone,
                'callSessionId': sessionId,
            })
        except UISComError as e:
            self.callFinished.emit({
                'ok': False,
                'status': e.status,
                'detail': e.detail,
                'contactPhone': self._contactPhone,
            })

class _UISComPollThread(QtCore.QThread):
    """
    Режим poll: опрашивает сервис (GET /pending) вместо WS
    """

    messageReceived = QtCore.pyqtSignal(object)
    stateChanged = QtCore.pyqtSignal(object)

    def __init__(self, api, personId, pollInterval=3, parent=None):
        super(_UISComPollThread, self).__init__(parent)
        self._api = api
        self._personId = personId
        self._pollInterval = pollInterval
        self._stopRequested = False
        self._afterId = None  # первый запрос вернёт last_id, историю не проигрываем

    def _sleepInterruptible(self, seconds):
        for _ in range(int(seconds * 10)):
            if self._stopRequested:
                return
            time.sleep(0.1)

    def requestStop(self):
        self._stopRequested = True

    def run(self):
        connected = False
        while not self._stopRequested:
            try:
                data = self._api.pending(self._personId, self._afterId)
            except UISComError as e:
                if e.status == 403:
                    self.stateChanged.emit(STATE_NO_MAPPING)
                    return
                if e.status == 423:
                    self.stateChanged.emit(STATE_DISABLED)
                    return
                    #connected = False
                    # self._sleepInterruptible(_DISABLED_RETRY_DELAY)
                    # continue
                self.stateChanged.emit(STATE_DISCONNECTED)
                connected = False
                self._sleepInterruptible(self._pollInterval)
                continue
            if not connected:
                connected = True
                self.stateChanged.emit(STATE_CONNECTED)
            self._afterId = data.get('last_id', self._afterId)
            if forceBool(QtGui.qApp.preferences.appPrefs.get('UISComIncCallNotificationEnabled', True)):
                for evt in (data.get('events') or []):
                    self.messageReceived.emit(evt)
            self._sleepInterruptible(self._pollInterval)
        self.stateChanged.emit(STATE_STOPPED)


class _UISComDbPollThread(QtCore.QThread):
    """
    Режим poll_db: читает soc_uiscom_NotificationEvent напрямую из БД
    """

    messageReceived = QtCore.pyqtSignal(object)
    stateChanged = QtCore.pyqtSignal(object)

    _SQL_MAX = 'SELECT COALESCE(MAX(id), 0) AS last_id FROM soc_uiscom_NotificationEvent'
    _SQL = (
        'SELECT ne.id AS id, ne.payload AS payload '
        'FROM soc_uiscom_NotificationEvent ne '
        'INNER JOIN Person_Identification pi ON pi.value = ne.employee_id AND pi.deleted = 0 '
        'WHERE pi.master_id = {personId} AND ne.id > {afterId} '
        'ORDER BY ne.id'
    )

    def __init__(self, personId, pollInterval=3, parent=None):
        super(_UISComDbPollThread, self).__init__(parent)
        self._personId = int(personId)
        self._pollInterval = pollInterval
        self._stopRequested = False
        self._afterId = None
        self._database = None
        self._connectionId = None

    def _sleepInterruptible(self, seconds):
        for _ in range(int(seconds * 10)):
            if self._stopRequested:
                return
            time.sleep(0.1)

    def requestStop(self):
        self._closeDatabase()
        self._stopRequested = True

    def _openDatabase(self):
        preferences = QtGui.qApp.preferences
        connectionName = "uiscom_" + str(QtCore.QThread.currentThreadId())
        self._database = database.connectDataBase(preferences.dbDriverName,
                                           preferences.dbServerName,
                                           preferences.dbServerPort,
                                           preferences.dbDatabaseName,
                                           preferences.dbUserName,
                                           preferences.dbPassword,
                                           connectionName=connectionName,
                                           compressData=preferences.dbCompressData,
                                           logger=logging.getLogger('DB') if QtGui.qApp.logSql else None
                                           )
        if not self._database:
            raise Exception('UISCom: Error due connecting to database!')
        query = self._database.query("select connection_id()")
        if query.first():
            self._connectionId = forceRef(query.value(0))

    def _closeDatabase(self):
        if self._database:
            self._database.close()
            self._database = None

    @property
    def _db(self):
        if self._database is not None:
            return self._database
        else:
            return QtGui.qApp.db

    def _initCursor(self):
        query = self._db.query(self._SQL_MAX)
        self._afterId = forceInt(query.record().value('last_id')) if query.next() else 0

    def run(self):
        connected = False
        self._openDatabase()
        while not self._stopRequested:
            events = []
            try:
                if self._afterId is None:
                    self._initCursor()
                query = self._db.query(self._SQL.format(personId=self._personId, afterId=self._afterId))
                while query.next():
                    record = query.record()
                    self._afterId = forceInt(record.value('id'))
                    try:
                        events.append(json.loads(forceString(record.value('payload'))))
                    except (ValueError, TypeError):
                        pass
            except Exception as e:
                print('UIS: ошибка чтения БД: {0}'.format(e))
                self.stateChanged.emit(STATE_DISCONNECTED)
                connected = False
                self._sleepInterruptible(self._pollInterval)
                continue
            if not connected:
                connected = True
                self.stateChanged.emit(STATE_CONNECTED)
            if forceBool(QtGui.qApp.preferences.appPrefs.get('UISComIncCallNotificationEnabled', True)):
                for evt in events:
                    self.messageReceived.emit(evt)
            self._sleepInterruptible(self._pollInterval)
        self.stateChanged.emit(STATE_STOPPED)


class _UISComBootstrapThread(QtCore.QThread):
    """
    Определяет режим доставки (GET /Status) вне GUI-потока, чтобы start() не блокировал интерфейс
    """

    resolved = QtCore.pyqtSignal(object)  # {'mode': ..., 'poll_interval': ...}

    def __init__(self, api, parent=None):
        super(_UISComBootstrapThread, self).__init__(parent)
        self._api = api

    def run(self):
        try:
            status = self._api.status()
        except UISComError:
            status = {}
        self.resolved.emit({
            'mode': status.get('delivery_mode', 'poll_db'),
            'poll_interval': status.get('poll_interval', 3),
        })


class UISComClient(QtCore.QObject):
    """
    Клиент для работы с сервисом телефонии UISCom (на CП)
    """

    # Основные сигналы для получения уведомлений, статуса и т.д.
    # Необходимо подключать в месте, где инициализируем клиент
    UISClientIncomingCall = QtCore.pyqtSignal(object)
    UISClientStateChanged = QtCore.pyqtSignal(object)
    UISClientCallFinished = QtCore.pyqtSignal(object)

    def __init__(self, timeout=15, parent=None):
        super(UISComClient, self).__init__(parent)
        baseUrl = forceString(QtGui.qApp.getGlobalPreference('23:servicesURL')).rstrip('/')
        #baseUrl = 'http://192.168.1.112:5100'
        self._api = _UISComRestAPI(servicesUrl=baseUrl, timeout=timeout)
        self._wsUrl = '{baseUrl}/api/UISCom/ws/{personId}'.format(
            baseUrl=baseUrl.replace('http://', 'ws://'),
            personId=QtGui.qApp.userId
        )
        self._notifyThread = None
        self._bootstrapThread = None
        self._callThreads = []
        self._connectState = None

    def start(self):
        """
        Как несложно понять - это запуск работы клиента
        """
        if self._notifyThread is not None and self._notifyThread.isRunning():
            return
        if self._bootstrapThread is not None and self._bootstrapThread.isRunning():
            return
        # Режим доставки задаётся на сервере (GET /Status). Определяем его вне GUI-потока,
        # чтобы start() не подвисал, если сервис недоступен.
        self._bootstrapThread = _UISComBootstrapThread(self._api, parent=self)
        self._bootstrapThread.resolved.connect(self._onModeResolved)
        self._bootstrapThread.start()

    def _onModeResolved(self, cfg):
        """
        Клиент получил тип получения уведомлений от сервиса UIS (СП)
        """
        if self._notifyThread is not None and self._notifyThread.isRunning():
            return
        mode = cfg.get('mode', 'ws')
        pollInterval = cfg.get('poll_interval', 3)
        personId = QtGui.qApp.userId

        if mode == 'poll':
            self._notifyThread = _UISComPollThread(self._api, personId, pollInterval, parent=self)
        elif mode == 'poll_db':
            self._notifyThread = _UISComDbPollThread(personId, pollInterval, parent=self)
        else:  # 'ws'
            self._notifyThread = _UISComWSThread(wsUrl=self._wsUrl, parent=self)

        self._notifyThread.messageReceived.connect(self.UISClientIncomingCall)
        self._notifyThread.stateChanged.connect(self._changeCurrentConnectState)
        self._notifyThread.start()

    def _changeCurrentConnectState(self, state):
        self._connectState = state
        self.UISClientStateChanged.emit(state)

    def isConnected(self):
        if self._connectState and self._connectState == STATE_CONNECTED:
            return True
        return False

    def stop(self):
        """
        Остановка всех потоков
        """
        if self._bootstrapThread is not None:
            # Отключаем resolved, чтобы поздний ответ /Status не поднял транспорт после stop()
            try:
                self._bootstrapThread.resolved.disconnect()
            except (TypeError, RuntimeError):
                pass
            self._bootstrapThread.wait(3000)
            self._bootstrapThread = None
        if self._notifyThread is not None:
            self._notifyThread.requestStop()
            self._notifyThread.wait(3000)
            self._notifyThread = None

    def makeCall(self, contactPhone, virtualPhoneNumber=None):
        """
        Создаёт синхронный звонок.
        GUI-поток блокируется до получения статуса звонка
        """
        return self._api.makeCall(contactPhone, virtualPhoneNumber)

    def makeCallAsync(self, contactPhone, virtualPhoneNumber=None):
        """
        Создаёт около-асинхронный звонок.
        GUI-поток не блокируется на время запроса звонка (возможно его наличие необязательно,
        надо тестить на реальном сценарии, т.к. ответ может прийти сразу, а может только после дозвона)
        """
        thread = _UISCallThread(self._api, contactPhone, virtualPhoneNumber=virtualPhoneNumber, parent=self)
        self._callThreads.append(thread)
        thread.callFinished.connect(self.UISClientCallFinished)
        thread.finished.connect(lambda t=thread: self._callThreads.remove(thread))
        thread.start()

    def makeInformerCallAsync(self, contactPhone, ttsMessage=None, preset=None, virtualPhoneNumber=None):
        """
        Создаёт около-асинхронный информ-звонок.
        Отличие только в том что нам нужно только передать сообщение для озвучки и всё
        GUI-поток не блокируется на время запроса звонка
        """
        # Шлём и ttsMessage, и preset; какой канал использовать — решает сервер (informer_use_tts)
        thread = _UISCallThread(self._api, contactPhone, informerCall=True, ttsMessage=ttsMessage,
                                preset=preset, virtualPhoneNumber=virtualPhoneNumber, parent=self)
        self._callThreads.append(thread)
        thread.callFinished.connect(self.UISClientCallFinished)
        thread.finished.connect(lambda t=thread: self._callThreads.remove(thread))
        thread.start()

    def getStatus(self):
        """
        Получаем статус сервиса с СП.
        Доп. Если работают WebSocket-сообщения, то покажет активных клиентов
        """
        return self._api.status()

    def callsHistory(self, dateBeg, dateEnd, limit=100, offset=0, phone=None):
        """
        Получение истории звонков за нужную дату
        При передаче номера пациента, то выведет только его историю, а иначе выдаст все звонки
        Предусмотрена стандартная пагинация на стороне UIS, просто передаём лимит и смещение
        """
        return self._api.callsHistory(dateBeg, dateEnd, limit, offset, phone=phone)

    def showCallHistory(self, phones, parent=None):
        """
        Открывает диалог истории звонков по номерам клиента
        """
        dialog = UISComCallHistoryDialog(self, phones, parent)
        return dialog.exec_()


class UISComCallHistoryDialog(QtGui.QDialog):
    """
    Окно с таблицей истории звонков по конкретному телефону клиента
    """

    _DIRECTION = {'in': 'Входящий', 'out': 'Исходящий'}
    # 'Время окончания',
    _COLUMNS = ['Дата/время начала', 'Направление', 'Номер клиента', 'Виртуальный номер',
                'Сотрудник', 'Разговор, с', 'Итого, с', 'Статус', 'Причина завершения звонка', 'Запись']
    _CALL_DISCONNECT_REASONS = {
        "numb_not_exists": "Виртуальный номер не найден",
        "incorrect_input": "Некорректный ввод",
        "numb_is_inactive": "Виртуальный номер не активен",
        "sitephone_is_not_configured": "Сайтфон не настроен",
        "app_is_inactive": "Клиент деактивирован",
        "numa_in_black_list": "Вызывающий абонент в черном списке",
        "no_active_scenario": "Не найден активный сценарий",
        "simple_forwarding_is_not_configured": "Аналитика: простая переадресация не настроена",
        "site_not_exists": "Сайт не найден",
        "call_generator_is_not_configured": "Лидогенератор не настроен",
        "add_cdr_timeout": "Не определена",
        "success_finish": "Не определена",
        "api_permission_denied": "Доступ к Call API запрещен",
        "api_ip_now_allowed": "IP-адрес не в списке разрешенных",
        "component_is_inactive": "Компонент не активен",
        "employee_not_exists": "Сотрудник не найден",
        "not_enough_money": "Недостаточно средств",
        "platform_not_found": "Обратитесь в службу технической поддержки",
        "internal_error": "Обратитесь в службу технической поддержки",
        "incorrect_config": "Недопустимая конфигурация",
        "communication_unavailable": "Недоступный тип связи",
        "subscriber_disconnects": "Абонент разорвал соединение",
        "no_operation": "Нет операции для обработки",
        "scenario_not_found": "Сценарий не найден",
        "transfer_disconnects": "Отключение сотрудника при трансфере",
        "scenario_disconnects": "Отключение сотрудника при запуске сценария",
        "fax_session_done": "Факс принят",
        "no_resources": "Лимит клиента исчерпан",
        "another_operator_answer": "Дозвонились до другого сотрудника",
        "subscriber_busy": "Абонент занят",
        "subscriber_not_responsible": "Абонент не отвечает",
        "subscriber_number_problems": "Проблемы с телефонным номером абонента. Обратитесь в службу технической поддержки.",
        "operator_answer": "Дозвонились до сотрудника",
        "locked_numb": "Звонки на этот номер запрещены настройками безопасности",
        "call_not_allowed_on_tp": "Звонок запрещен согласно тарифному плану",
        "account_not_found": "Не найден лицевой счет",
        "contract_not_found": "Не найден договор",
        "operator_busy": "Сотрудник занят",
        "operator_not_responsible": "Сотрудник не отвечает",
        "operator_disconnects": "Сотрудник разорвал соединение",
        "operator_number_problems": "Проблемы с телефонным номером сотрудника. Обратитесь в службу технической поддержки.",
        "timeout": "Время дозвона истекло",
        "operator_channels_busy": "Закончились доступные линии на номере переадресации",
        "locked_phone": "Проблемы с сетью",
        "max_in_call_reached": "Достигнут лимит линий для входящих звонков",
        "max_out_call_reached": "Достигнут лимит линий для исходящих звонков",
        "employee_busy": "Сотрудник разговаривает в другом звонке",
        "employee_busy_after_call": "Сотрудник занят после звонка",
        "phone_group_inactive_by_schedule": "Группа номеров неактивна согласно расписанию",
        "sip_offline": "SIP-линия не зарегистрирована",
        "employee_inactive": "Сотрудник неактивен",
        "employee_inactive_by_schedule": "Сотрудник неактивен согласно расписанию",
        "employee_phone_inactive": "Номер сотрудника неактивен",
        "employee_phone_inactive_by_schedule": "Номер сотрудника неактивен согласно расписанию",
        "action_interval_exceeded": "Превышен интервал, указанный на операции",
        "group_phone_inactive": "Номер в группе недоступен",
        "no_operator_confirmation": "Сотрудник не подтвердил вызов",
        "max_transition_count_exceeded": "Достигнуто максимальное количество переходов по операциям сценария",
        "disconnect_before_call_processing": "Разъединение до обработки вызова",
        "no_success_subscriber_call": "Не дозвонились до абонента",
        "no_success_operator_call": "Не дозвонились до сотрудника",
        "group_inactive_by_schedule": "Группа сотрудников неактивна согласно расписанию",
        "net_lock": "Сеть оператора заблокирована",
        "fmc_is_disabled": "Услуга FMC отключена",
        "fmc_is_locked": "FMC-линия заблокирована",
        "processing_method_not_found": "Способ обработки не найден",
        "employee_without_phones": "",
        "group_without_phones": "",
        "no_operator_cdr_found": "Вызовы сотрудникам не найдены",
        "in_call_not_allowed": "Прием входящих звонков запрещен",
        "phone_protocol_not_allowed_by_status": "Звонки с данного типа номера запрещены статусом",
        "employee_status_break": "Сотрудник в статусе \"Перерыв\"",
        "employee_status_do_not_disturb": "Сотрудник в статусе \"Не беспокоить\"",
        "employee_status_not_at_workplace": "Сотрудник в статусе \"Нет на месте\"",
        "employee_status_not_at_work": "Сотрудник в статусе \"Нет на работе\"",
        "sip_trunk_is_locked": "SIP-транк заблокирован",
        "numa_in_spam_list": "Спам-звонок",
        "numa_dnd_interval": "Звонили недавно",
        "limit_exceeded": "Достигнут финансовый лимит",
        "no_money": "Недостаточно средств",
        "out_call_not_allowed": "Исходящие звонки запрещены",
        "out_call_not_allowed_by_status": "Исходящие звонки запрещены статусом",
        "external_call_not_allowed": "Внешние звонки запрещены",
        "external_call_not_allowed_by_status": "Внешние звонки запрещены статусом",
        "internal_call_not_allowed": "Внутренние звонки запрещены",
        "internal_call_not_allowed_by_status": "Внутренние звонки запрещены статусом",
        "call_enqueued": "Вызов поставлен в очередь",
        "employee_status_auto_out_call": "Сотрудник в статусе \"Исходящий обзвон\"",
        "employee_status_available": "Сотрудник в статусе \"Доступен\"",
        "too_many_identical_incoming_calls": "Слишком много одинаковых входящих звонков",
        "employee_auto_status_do_not_disturb": "Сотрудник в автоматическом статусе \"Не беспокоить\"",
        "auto_out_calls_not_allowed_by_status": "Исходящий обзвон запрещен статусом",
    }

    def __init__(self, client, phones, parent=None):
        super(UISComCallHistoryDialog, self).__init__(parent)
        self._client = client
        # phones - один номер или список  храним списком
        self._phones = list(phones) if isinstance(phones, (list, tuple)) else ([phones] if phones else [])
        self.setWindowTitle('История звонков: {0}'.format(', '.join(self._phones) or ''))
        self.resize(900, 500)

        _today = QtCore.QDate.currentDate()
        _minDateBeg = _today.addDays(-89)
        self._dateBeg = QtGui.QDateEdit(_minDateBeg)
        self._dateBeg.setMinimumDate(_minDateBeg)
        self._dateBeg.setMaximumDate(_today)
        self._dateEnd = QtGui.QDateEdit(_today)
        for w in (self._dateBeg, self._dateEnd):
            w.setCalendarPopup(True)
            w.setDisplayFormat('dd.MM.yyyy')

        self._reloadBtn = QtGui.QPushButton('Обновить')
        self._reloadBtn.clicked.connect(self._reload)
        self._status = QtGui.QLabel('')

        self._table = QtGui.QTableWidget(0, len(self._COLUMNS), self)
        self._table.setHorizontalHeaderLabels(self._COLUMNS)
        self._table.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self._table.horizontalHeader().setStretchLastSection(True)

        top = QtGui.QHBoxLayout()
        top.addWidget(QtGui.QLabel('С'))
        top.addWidget(self._dateBeg)
        top.addWidget(QtGui.QLabel('по'))
        top.addWidget(self._dateEnd)
        top.addWidget(self._reloadBtn)
        top.addStretch(1)

        layout = QtGui.QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(self._table)
        layout.addWidget(self._status)

        #self._reload()

    def _reload(self):
        dateBeg = forceString(self._dateBeg.date().toString('yyyy-MM-dd')) + ' 00:00:00'
        dateEnd = forceString(self._dateEnd.date().toString('yyyy-MM-dd')) + ' 23:59:59'
        self._table.setRowCount(0)
        self._status.setText('Загрузка...')
        QtGui.qApp.setWaitCursor()
        try:
            result = self._client.callsHistory(dateBeg, dateEnd, limit=100, offset=0, phone=self._phones)
            rows = (result or {}).get('data') or []
            self._fill(rows)
            self._status.setText('Найдено записей: {0}'.format(len(rows)))
        except UISComError as e:
            self._status.setText('Ошибка: {0}'.format(e.detail))
            QtGui.QMessageBox.warning(self, 'История звонков',
                                      'Не удалось получить историю: {0}'.format(e.detail))
        finally:
            QtGui.qApp.restoreOverrideCursor()

    def _fill(self, rows):
        self._table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            status = 'Пропущен' if row.get('is_lost') else 'Отвечен'
            record = 'есть' if forceString(row.get('full_record_file_link')) else ''
            direction = forceString(row.get('direction'))
            callDisconnectReason = forceString(row.get('finish_reason'))
            values = [
                forceString(row.get('start_time')),
                #forceString(row.get('finish_time')),
                self._DIRECTION.get(direction, direction),
                forceString(row.get('contact_phone_number')),
                forceString(row.get('virtual_phone_number')),
                forceString(row.get('last_answered_employee_full_name')),
                forceString(row.get('talk_duration')),
                forceString(row.get('total_duration')),
                status,
                self._CALL_DISCONNECT_REASONS.get(callDisconnectReason, ''),
                record,
            ]
            for c, val in enumerate(values):
                self._table.setItem(r, c, QtGui.QTableWidgetItem(val))