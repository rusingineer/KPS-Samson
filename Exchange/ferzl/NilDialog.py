# -*- coding: utf-8 -*-
#############################################################################
##
## Диалог поиска сведений о НИЛ через внешний сервис ФЕРЗЛ.
## Форма: Ui_NilDialog.py
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QDate, QDateTime, QRegExp, QPoint, pyqtSignature

from library.DialogBase import CDialogBase
from library.Utils import (
    forceString, forceInt, forceDate, forceRef, forceStringEx,
)

from Ui_NilDialog import Ui_NilDialog

from Registry.Ferzl_service import Ferzl_service
from Registry.ClientEditDialog import CClientEditDialog

from Users.Rights import (
    urAdmin, urRegTabReadRegistry, urRegTabWriteRegistry, urRegTabNewWriteRegistry,
)
import calendar
from datetime import datetime

class CNilDialog(CDialogBase, Ui_NilDialog):
    """
    Диалог поиска сведений о НИЛ.
    Результаты отображаются в tableView (вкладка «Результат поиска»).
    """

    def __init__(self, parent=None, **kwargs):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)

        # ------------ Кэш полученных записей (результат findNils) ------------
        # Список dict-ов. Используется для получения oip при открытии
        # регистрационной карты без повторного вызова findNils.
        self._items = []

        # ------------ Модель результатов ------------
        self.resultsModel = CNilResultsModel(self)
        self.tableView.setModel(self.resultsModel)
        self.tableView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tableView.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.tableView.setAlternatingRowColors(True)
        self.tableView.setSortingEnabled(True)
        self.tableView.horizontalHeader().setStretchLastSection(True)
        self.tableView.verticalHeader().setVisible(False)

        # ------------ Контекстное меню таблицы ------------
        self._setupTableViewMenu()

        # ------------ Валидаторы возраста ------------
        age_validator = QtGui.QRegExpValidator(QRegExp(r'\d{1,3}'), self)
        self.edtAgeStart.setValidator(age_validator)
        self.edtedtAgeEnd.setValidator(age_validator)

        # ------------ Начальное состояние ------------
        self.tabWidget.setCurrentIndex(1)  # открываем вкладку «Поиск»
        self.edtLastName.setFocus(Qt.OtherFocusReason)

    # ==================================================================
    #  Контекстное меню таблицы
    # ==================================================================
    def _setupTableViewMenu(self):
        self.tableView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableView.customContextMenuRequested.connect(
            self.on_tableView_contextMenu
        )

        self.mnuNilTable = QtGui.QMenu(self)
        self.actOpenRegistryCard = QtGui.QAction(u'Регистрационная карта', self)
        self.actOpenRegistryCard.triggered.connect(self.on_actOpenRegistryCard_triggered)
        self.actInfo = QtGui.QAction(u'Запросить подробные сведения о НИЛ', self)
        self.actInfo.triggered.connect(self.on_actInfo_triggered)
        self.mnuNilTable.addAction(self.actOpenRegistryCard)
        self.mnuNilTable.addAction(self.actInfo)

    @pyqtSignature('QPoint')
    def on_tableView_contextMenu(self, pos):
        index = self.tableView.indexAt(pos)
        if not index.isValid():
            return
        # Выделяем строку, по которой кликнули ПКМ
        self.tableView.selectRow(index.row())
        self.mnuNilTable.exec_(self.tableView.viewport().mapToGlobal(pos))

    # ==================================================================
    #  Информация
    # ==================================================================

    @pyqtSignature('')
    def on_actInfo_triggered(self):
        index = self.tableView.currentIndex()
        if not index.isValid():
            return
        row = index.row()
        if row < 0 or row >= len(self._items):
            return

        oip = forceString(self._items[row].get('oip')).strip()
        if not oip:
            QtGui.QMessageBox.warning(
                self, u'НИЛ',
                u'У выбранной записи отсутствует ОИП.',
                QtGui.QMessageBox.Ok
            )
            return

        # ---------------- Запрос к сервису ----------------
        service = Ferzl_service()
        try:
            result = QtGui.qApp.callWithWaitCursor(self, service.getNilsData, oip)
        except Exception, e:
            QtGui.QMessageBox.critical(
                self, u'Ошибка',
                u'Не удалось получить данные НИЛ:\n%s' % unicode(e),
                QtGui.QMessageBox.Ok
            )
            return

        if not result or not result.get('result'):
            # Сервис сам показал сообщение об ошибке
            return

        # ---------------- Разбор ответа ----------------
        data = result.get('data') or {}
        nil_item = self._extractNilItem(data)
        if not nil_item:
            QtGui.QMessageBox.warning(
                self, u'НИЛ',
                u'Некорректный формат данных НИЛ, полученных от сервиса.',
                QtGui.QMessageBox.Ok
            )
            return
        else:
            if isinstance(nil_item, dict) and isinstance(nil_item.get('nil'), dict):
                nil_item = nil_item.get('nil')

            def _s(v):
                if v is None:
                    return u''
                if isinstance(v, unicode):
                    return v
                if isinstance(v, str):
                    return v.decode('utf-8', 'replace')
                return unicode(v)

            def add_line(lines, label, value):
                value = _s(value).strip()
                if value:
                    lines.append(u'%s %s' % (label, value))

            lines = []

            add_line(lines, u'Фамилия (Предполагаемая):', nil_item.get('surnameEstim'))
            add_line(lines, u'Имя (Предполагаемое):', nil_item.get('firstNameEstim'))
            add_line(lines, u'Отчество (Предполагаемое):', nil_item.get('patronymicEstim'))
            add_line(lines, u'Дата рождения:', nil_item.get('birthday'))

            age_b = _s(nil_item.get('estimAgeB')).strip()
            age_e = _s(nil_item.get('estimAgeE')).strip()
            if age_b and age_e:
                lines.append(u'Возраст с %s по %s' % (age_b, age_e))
            elif age_b:
                lines.append(u'Возраст с %s' % age_b)
            elif age_e:
                lines.append(u'Возраст по %s' % age_e)

            gender = _s(nil_item.get('gender')).strip()
            if gender:
                gender_map = {
                    u'0': u'Неизвестен',
                    u'1': u'Мужской',
                    u'2': u'Женский',
                }
                lines.append(u'Пол: %s' % gender_map.get(gender, gender))

            add_line(lines, u'Место рождения:', nil_item.get('birthPlace'))

            no_cit = _s(nil_item.get('noCizizenship')).strip()
            if no_cit:
                cit_map = {
                    u'0': u'есть гражданство',
                    u'1': u'нет гражданства',
                }
                lines.append(u'Признак отсутствия гражданства: %s' % cit_map.get(no_cit, no_cit))

            add_line(lines, u'ОКАТО МО, которая регистрирует НИЛа:', nil_item.get('moOkato'))
            add_line(lines, u'ОИП персоны, к которой привязан НИЛ:', nil_item.get('oip'))
            add_line(lines, u'Номер листа регистрации:', nil_item.get('nLr'))

            wd = _s(nil_item.get('whenAdmittedDate')).strip()
            wt = _s(nil_item.get('whenAdmittedTime')).strip()
            if wd or wt:
                when = u' '.join([x for x in (wd, wt) if x])
                lines.append(u'Дата поступления: %s' % when)

            appearance = nil_item.get('appearanceDescription') or {}
            if not isinstance(appearance, dict):
                appearance = {}

            physique = _s(appearance.get('physique')).strip()
            if physique:
                phys_map = {
                    u'1': u'Нормостеническое',
                    u'2': u'Астеническое',
                    u'3': u'Гиперстеническое',
                }
                lines.append(u'Телосложение: %s' % phys_map.get(physique, physique))

            eyecolor = _s(appearance.get('eyecolor')).strip()
            if eyecolor:
                eye_map = {
                    u'1': u'Чёрный',
                    u'2': u'Тёмно-карий',
                    u'3': u'Светло-карий',
                    u'4': u'Жёлтый',
                    u'5': u'Буро-жёлто-зелёный',
                    u'6': u'Зелёный',
                    u'7': u'Серо-зелёный',
                    u'8': u'Светлый с буро-желтым венчиком',
                    u'9': u'Серый',
                    u'10': u'Серо-голубой',
                    u'11': u'Голубой',
                    u'12': u'Синий',
                }
                lines.append(u'Цвет глаз: %s' % eye_map.get(eyecolor, eyecolor))

            add_line(lines, u'Рост:', appearance.get('hgrow'))
            add_line(lines, u'Особые приметы:', appearance.get('specFeat'))

            # ---------------- Личные вещи / лекарства / документы ----------------
            personal = nil_item.get('personalItemsOrMedications') or {}
            if not isinstance(personal, dict):
                personal = {}

            add_line(lines, u'Личные вещи:', personal.get('persThings'))
            add_line(lines, u'Лекарства:', personal.get('persDrug'))
            add_line(lines, u'Описание документов, бирок, медальонов и т.д:', personal.get('persIdent'))

            text = u'\n'.join(lines)
            if not text:
                text = u'Нет данных для отображения.'

            QtGui.QMessageBox.warning(
                self, u'НИЛ',
                text,
                QtGui.QMessageBox.Ok
            )
            return

    # ==================================================================
    #  Регистрационная карта
    # ==================================================================

    @pyqtSignature('')
    def on_actOpenRegistryCard_triggered(self):
        index = self.tableView.currentIndex()
        if not index.isValid():
            return

        row = index.row()
        if row < 0 or row >= len(self._items):
            return

        oip = forceString(self._items[row].get('oip')).strip()
        if not oip:
            QtGui.QMessageBox.warning(
                self, u'НИЛ',
                u'У выбранной записи отсутствует ОИП.',
                QtGui.QMessageBox.Ok
            )
            return

        # ---------------- Запрос к сервису ----------------
        service = Ferzl_service()
        try:
            result = QtGui.qApp.callWithWaitCursor(self, service.getNilsData, oip)
        except Exception, e:
            QtGui.QMessageBox.critical(
                self, u'Ошибка',
                u'Не удалось получить данные НИЛ:\n%s' % unicode(e),
                QtGui.QMessageBox.Ok
            )
            return

        if not result or not result.get('result'):
            # Сервис сам показал сообщение об ошибке
            return

        # ---------------- Разбор ответа ----------------
        data = result.get('data') or {}
        nil_item = self._extractNilItem(data)
        if not nil_item:
            QtGui.QMessageBox.warning(
                self, u'НИЛ',
                u'Некорректный формат данных НИЛ, полученных от сервиса.',
                QtGui.QMessageBox.Ok
            )
            return

        surnameEstim    = forceString(nil_item.get('surnameEstim')).strip()
        firstNameEstim  = forceString(nil_item.get('firstNameEstim')).strip()
        patronymicEstim = forceString(nil_item.get('patronymicEstim')).strip()
        birthday        = forceString(nil_item.get('birthday')).strip()
        gender          = forceString(nil_item.get('gender')).strip()

        if not surnameEstim or not firstNameEstim or not birthday:
            QtGui.QMessageBox.warning(
                self, u'НИЛ',
                u'В данных НИЛ отсутствуют обязательные поля '
                u'(Фамилия / Имя / Дата рождения).',
                QtGui.QMessageBox.Ok
            )
            return

        # ---------------- Поиск в МИС ----------------
        clientId = self._findClientInMis(
            surnameEstim, firstNameEstim, patronymicEstim, birthday
        )

        if clientId:
            # Пациент найден — предложить открыть карту
            res = QtGui.QMessageBox.question(
                self, u'НИЛ',
                u'Данный пациент найден в МИС, открыть карту пациента?',
                QtGui.QMessageBox.Ok | QtGui.QMessageBox.Close,
                QtGui.QMessageBox.Ok
            )
            if res == QtGui.QMessageBox.Ok:
                self._openClientCard(clientId)
        else:
            # Пациент не найден — предложить создать карту
            res = QtGui.QMessageBox.question(
                self, u'НИЛ',
                u'Данный пациент не найден в МИС, создать карту пациента?',
                QtGui.QMessageBox.Ok | QtGui.QMessageBox.Close,
                QtGui.QMessageBox.Ok
            )
            if res == QtGui.QMessageBox.Ok:
                self._createClientCard(
                    surnameEstim, firstNameEstim, patronymicEstim,
                    birthday, gender
                )

    # ------------------------------------------------------------------
    #  Извлечение nil-записи из ответа getNilsData
    # ------------------------------------------------------------------
    @staticmethod
    def _extractNilItem(data):
        """
        Из ответа вида
            {'nil': {'nil': {...}}}
        возвращает внутренний словарь {...}.
        """
        if not isinstance(data, dict):
            return None

        nil_outer = data.get('nil')
        if isinstance(nil_outer, dict):
            nil_inner = nil_outer.get('nil')
            if isinstance(nil_inner, dict):
                return nil_inner
            # Иногда сервис возвращает напрямую {'nil': {...}}
            return nil_outer
        return None

    # ------------------------------------------------------------------
    #  Поиск пациента в МИС
    # ------------------------------------------------------------------
    @staticmethod
    def _findClientInMis(lastName, firstName, patrName, birthDateStr):
        """
        Ищет клиента по ФИО + дате рождения.
        patrName — опционально.
        birthDateStr — 'YYYY-MM-DD'.
        Возвращает clientId (int) или None.
        """
        if not lastName or not firstName or not birthDateStr:
            return None

        birthQDate = QDate.fromString(birthDateStr, 'yyyy-MM-dd')
        if not birthQDate.isValid():
            # Попробуем DD.MM.YYYY на всякий случай
            birthQDate = QDate.fromString(birthDateStr, 'dd.MM.yyyy')
        if not birthQDate.isValid():
            return None

        db = QtGui.qApp.db
        tableClient = db.table('Client')
        cond = [
            tableClient['deleted'].eq(0),
            tableClient['lastName'].eq(lastName),
            tableClient['firstName'].eq(firstName),
            tableClient['birthDate'].eq(birthQDate),
        ]
        # if patrName:
        #     cond.append(tableClient['patrName'].eq(patrName))

        record = db.getRecordEx(tableClient, [tableClient['id']], cond)
        if record:
            return forceRef(record.value('id'))
        return None

    # ------------------------------------------------------------------
    #  Открытие существующей карты пациента
    # ------------------------------------------------------------------
    def _openClientCard(self, clientId):
        if not QtGui.qApp.userHasAnyRight(
            [urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]
        ):
            QtGui.QMessageBox.warning(
                self, u'НИЛ',
                u'Недостаточно прав для открытия карты пациента.',
                QtGui.QMessageBox.Ok
            )
            return

        dialog = CClientEditDialog(self)
        try:
            dialog.load(clientId)
            dialog.exec_()
        finally:
            dialog.deleteLater()

    # ------------------------------------------------------------------
    #  Создание новой карты пациента (с предзаполнением)
    # ------------------------------------------------------------------
    def _createClientCard(self, lastName, firstName, patrName,
                          birthDateStr, genderStr):
        if not QtGui.qApp.userHasAnyRight([urRegTabNewWriteRegistry]):
            QtGui.QMessageBox.warning(
                self, u'НИЛ',
                u'Недостаточно прав для создания карты пациента.',
                QtGui.QMessageBox.Ok
            )
            return

        dialogInfo = {
            'lastName':  lastName,
            'firstName': firstName,
            'patrName':  patrName,
        }

        birthQDate = QDate.fromString(birthDateStr, 'yyyy-MM-dd')
        if not birthQDate.isValid():
            birthQDate = QDate.fromString(birthDateStr, 'dd.MM.yyyy')
        if birthQDate.isValid():
            dialogInfo['birthDate'] = birthQDate

        # Пол: 1 = М, 2 = Ж (в JSON gender приходит строкой '1'/'2')
        try:
            gender_int = int(forceString(genderStr).strip() or 0)
        except (TypeError, ValueError):
            gender_int = 0
        if gender_int in (1, 2):
            dialogInfo['sex'] = gender_int

        dialog = CClientEditDialog(self)
        try:
            dialog.setClientDialogInfo(dialogInfo)
            if dialog.exec_():
                clientId = dialog.itemId()
                # При желании тут можно что-то сделать с новым clientId
        finally:
            dialog.deleteLater()

    # ==================================================================
    #  Кнопки
    # ==================================================================
    @pyqtSignature('')
    def on_btnApply_clicked(self):
        self.doSearch()

    @pyqtSignature('')
    def on_btnClose_clicked(self):
        self.close()

    # ==================================================================
    #  Утилиты преобразования
    # ==================================================================
    @staticmethod
    def _dateStr(date_edit):
        """QDate → 'yyyy-MM-dd' или None, если дата не задана."""
        d = date_edit.date()
        if d and d.isValid():
            return d.toString('yyyy-MM-dd')
        return None

    @staticmethod
    def _intStr(line_edit):
        """QLineEdit → 'N' или None, если пусто / не число."""
        text = forceStringEx(line_edit.text()).strip()
        if not text:
            return None
        try:
            return forceString(int(text))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _text(line_edit):
        """QLineEdit → строка без пробелов, либо None, если пусто."""
        v = forceStringEx(line_edit.text()).strip()
        return v if v else None

    # ==================================================================
    #  Сбор параметров фильтра
    # ==================================================================
    def getFilterParams(self):
        """
        Собирает словарь с параметрами для сервиса.
        Поле попадает в словарь, только если:
          - соответствующий чекбокс включён,
          - поле не пустое.
        """
        params = {}

        # --- ФИО (предполагаемые) ---
        if self.chkLastName.isChecked():
            v = self._text(self.edtLastName)
            if v:
                params['surnameEstim'] = v
        if self.chkFirstName.isChecked():
            v = self._text(self.edtFirstName)
            if v:
                params['firstNameEstim'] = v
        if self.chkPatrName.isChecked():
            v = self._text(self.edtPatrName)
            if v:
                params['patronymicEstim'] = v

        # --- Возраст ---
        if self.chkAge.isChecked():
            v_from = self._intStr(self.edtAgeStart)
            v_to = self._intStr(self.edtedtAgeEnd)
            if v_from is not None:
                params['estimAgeB'] = v_from
            if v_to is not None:
                params['estimAgeE'] = v_to

        # --- Лист регистрации (nlr) ---
        if self.chkNlr.isChecked():
            v = self._text(self.edtChkNlr)
            if v:
                params['nlr'] = v

        # --- Номер бригады СМП ---
        if self.chkNumberSMP.isChecked():
            v = self._text(self.edtNumberSMP)
            if v:
                params['teamNum'] = v

        # --- Код станции СМП ---
        if self.chkCodeSMP.isChecked():
            v = self._text(self.edtCodeSMP)
            if v:
                params['subst'] = v

        # --- Номер наряда СМП ---
        if self.chkTeamSMP.isChecked():
            v = self._text(self.edtTeamSMP)
            if v:
                params['assignNum'] = v

        # --- Дата поступления ---
        d_from = self._dateStr(self.edtDateKhodatSince)
        d_to = self._dateStr(self.edtDateKhodatTill)
        if d_from:
            params['dateKhodatSince'] = d_from
        if d_to:
            params['dateKhodatTill'] = d_to

        return params

    # ==================================================================
    #  Поиск
    # ==================================================================
    def doSearch(self):
        def _parseDate(s):
            """Преобразует строку из CDateEdit (QString/str) в date. None, если пусто/не распознано."""
            if not s:
                return None
            if not isinstance(s, basestring):
                try:
                    s = unicode(s)
                except Exception:
                    s = str(s)
            else:
                s = unicode(s)
            for fmt in (u'%d.%m.%Y', u'%Y-%m-%d', u'%d-%m-%Y', u'%d/%m/%Y'):
                try:
                    return datetime.strptime(s, fmt).date()
                except ValueError:
                    continue
            return None

        def _addMonth(d):
            """Дата d + 1 календарный месяц (с корректировкой дня для коротких месяцев)."""
            m = d.month + 1
            y = d.year
            if m > 12:
                m = 1
                y += 1
            last_day = calendar.monthrange(y, m)[1]
            return d.replace(year=y, month=m, day=min(d.day, last_day))

        def _validateDateRange(params):
            """
            Проверяет даты в params.
            Возвращает True, если всё ок, иначе показывает сообщение и возвращает False.
            """
            d_from = params.get('dateKhodatSince')
            d_to = params.get('dateKhodatTill')

            dt_from = _parseDate(d_from)
            dt_to = _parseDate(d_to)
            today = datetime.now().date()

            # d_to не может быть в будущем
            if dt_to is not None and dt_to > today:
                QtGui.QMessageBox.information(
                    self, u'Поиск НИЛ',
                    u'Дата окончания не может превышать текущую дату.',
                    QtGui.QMessageBox.Ok
                )
                return False

            # интервал между d_from и d_to не больше месяца
            if dt_from is not None and dt_to is not None:
                if dt_to < dt_from:
                    QtGui.QMessageBox.information(
                        self, u'Поиск НИЛ',
                        u'Дата окончания не может быть раньше даты начала.',
                        QtGui.QMessageBox.Ok
                    )
                    return False
                if dt_to > _addMonth(dt_from):  # <-- было self._addMonth(...)
                    QtGui.QMessageBox.information(
                        self, u'Поиск НИЛ',
                        u'Интервал не может превышать месяц.',
                        QtGui.QMessageBox.Ok
                    )
                    return False

            return True

        params = self.getFilterParams()
        if not _validateDateRange(params):
            return
        # ... дальнейший код поиска по params
        if not params:
            QtGui.QMessageBox.information(
                self, u'Поиск НИЛ',
                u'Не задано ни одного условия поиска.',
                QtGui.QMessageBox.Ok
            )
            return

        try:
            result = QtGui.qApp.callWithWaitCursor(self, self.searchNil, params)
        except Exception, e:
            QtGui.QMessageBox.critical(
                self, u'Ошибка',
                u'Не удалось выполнить поиск:\n%s' % unicode(e),
                QtGui.QMessageBox.Ok
            )
            return

        # Переключаемся на вкладку результатов
        self.tabWidget.setCurrentIndex(0)
        self.tabWidget.setTabEnabled(0, True)

        if not result or not result.get('result'):
            self._items = []
            self.resultsModel.setRecords([])
            return

        items = result.get('elements') or []
        self._items = items               # ← сохраняем для getNilsData
        self.resultsModel.setRecords(items)

        if not items:
            QtGui.QMessageBox.information(
                self, u'Поиск НИЛ',
                u'По заданным условиям ничего не найдено.',
                QtGui.QMessageBox.Ok
            )

    # ==================================================================
    #  ТОЧКА РАСШИРЕНИЯ — вызов внешнего сервиса
    # ==================================================================
    def searchNil(self, params):
        """
        Вызывает Ferzl_service.findNils.
        :param params: dict (см. getFilterParams)
        :return: {'result': bool, 'elements': [...], 'pagination': {...}, 'message': u''}
        """
        service = Ferzl_service()
        return service.findNils(params)


# ----------------------------------------------------------------------
#  Модель для отображения результатов
# ----------------------------------------------------------------------
class CNilResultsModel(QtGui.QStandardItemModel):
    """
    Отображает список dict-ов, полученных от Ferzl_service.findNils.
    Каждая запись — результат разбора блока 'nil'.
    """

    COLUMNS = [
        (u'ФИО (предполагаемые)', ('fioEstim',)),
        (u'Дата рождения',        ('birthDay',)),
        (u'Пол',                  ('gender',)),
        (u'№ листа регистрации',  ('nlr',)),
        (u'ОКАТО',                ('moOkato',)),
    ]

    def __init__(self, parent=None):
        QtGui.QStandardItemModel.__init__(self, parent)
        self._initHeaders()

    def _initHeaders(self):
        self.setColumnCount(len(self.COLUMNS))
        self.setHorizontalHeaderLabels([c[0] for c in self.COLUMNS])

    def setRecords(self, records):
        """Заполнить модель списком dict-ов."""
        self.clear()
        self._initHeaders()

        if not records:
            return

        for record in records:
            if not isinstance(record, dict):
                continue

            row = []
            for header, keys in self.COLUMNS:
                value = self._pickValue(record, keys)
                item = QtGui.QStandardItem(self._formatValue(value, header))
                item.setEditable(False)
                # Прячем «сырое» значение — пригодится при двойном клике
                item.setData(value, Qt.UserRole)
                row.append(item)
            self.appendRow(row)

    @staticmethod
    def _pickValue(record, keys):
        for key in keys:
            if key in record and record[key] not in (None, u''):
                return record[key]
        return None

    @staticmethod
    def _formatValue(value, header=u''):
        if value is None:
            return u''

        # ---- Пол ----
        if header == u'Пол':
            try:
                v = int(value)
                return {0: u'Неизвестен', 1: u'М', 2: u'Ж'}.get(v, forceString(value))
            except (TypeError, ValueError):
                return forceString(value)

        # ---- Даты: 'ГГГГ-ММ-ДД' → 'ДД.ММ.ГГГГ' ----
        if header == u'Дата рождения':
            s = forceString(value)
            if len(s) == 10 and s[4] == u'-' and s[7] == u'-':
                return u'%s.%s.%s' % (s[8:10], s[5:7], s[0:4])
            return s

        if isinstance(value, QDate):
            return value.toString('dd.MM.yyyy') if value.isValid() else u''
        if isinstance(value, QDateTime):
            return value.toString('dd.MM.yyyy hh:mm') if value.isValid() else u''
        if isinstance(value, bool):
            return u'Да' if value else u'Нет'

        return forceString(value)


