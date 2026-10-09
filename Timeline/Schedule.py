# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2017 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import QDate, QDateTime, QTime

from library.recordWrapper import CSqlRecordWrapper, field
from library.Utils import forceBool, forceDate, forceDateTime, forceInt, forceRef, forceString, forceTime, toVariant, \
    calcAgeInYears
from Registry.Utils import CAppointmentPurposeCache, getPostIdentCodeByPersonId
from Users.Rights import urDeleteOtherQueue, urDeleteOwnQueue


def getPeriodLength(period, customLength):
    l = ( 1, # 0 == один день
          2, # 1 == нечет/чёт
          0, # 2 == произвольный график
          7, # 3 == неделя
         14, # 4 == две недели
         21, # 5 == три недели
         28, # 6 == четыре недели
        )
    if period == 2:
        return min(max(customLength, 3), 31)
    if 0<=period<len(l):
        return l[period]
    else:
        return 0 # неизвестный период


# ####################################################################


class CScheduleTemplate(CSqlRecordWrapper):
    tableName = 'Person_ScheduleTemplate'

    def getEmptyRecord(self):
        return QtGui.qApp.db.table(self.tableName).newRecord()

    id                   = field('id',                    forceRef)
    personId             = field('master_id',             forceRef)
    day                  = field('day',                   forceInt)
    appointmentType      = field('appointmentType',       forceInt)
    appointmentPurposeId = field('appointmentPurpose_id', forceRef)
    office               = field('office',                forceString)
    begTime              = field('begTime',               forceTime)
    endTime              = field('endTime',               forceTime)
    duration             = field('duration',              forceTime)
    capacity             = field('capacity',              forceInt)
    activityId           = field('activity_id',           forceRef)


    def save(self):
        QtGui.qApp.db.insertOrUpdate(self.tableName, self._record)


    def isEmpty(self):
        return self.appointmentType == 0


# ####################################################################


class CScheduleItem(CSqlRecordWrapper):
    rcSamson     = 0 # recordClass: samson
    rcInfomat    = 1 # recordClass: инфомат
    rcCallCenter = 2 # recordClass: call-центр
    rcInternet   = 3 # recordClass: интернет

    KT = u'к'
    NKT = u'н'
    MKT = u'м'
    dynamicItemType = None  # Тип талона. Изменяется от условий. Виды: КТ, НКТ, МКТ

    id = field('id')
    scheduleId     = field('master_id',       forceRef)
    idx            = field('idx',             forceInt)
    time           = field('time',            forceDateTime)
    overtime       = field('overtime',        forceBool)
    endOfReserve   = field('endOfReserve',    forceDateTime)
    appointmentPurposeId = field('appointmentPurpose_id', forceRef)
    clientId       = field('client_id',       forceRef)
    srcOrgId       = field('srcOrg_id',       forceRef)
    srcPerson      = field('srcPerson',       forceString)
    srcSpecialityId= field('srcSpeciality_id',forceRef)
    srcDate        = field('srcDate',         forceDate)
    srcNumber      = field('srcNumber',       forceString)
    recordClass    = field('recordClass',     forceInt)
    recordDatetime = field('recordDatetime',  forceDateTime)
    recordPersonId = field('recordPerson_id', forceRef)
    complaint      = field('complaint',       forceString)
    note           = field('note',            forceString)
    checked        = field('checked',         forceBool)
    homeCallStatus = field('homeCallStatus',  forceInt)  #WFT?
    invitation     = field('invitation',      forceBool) #WFT?
    inWaitingArea  = field('inWaitingArea',   forceBool) #WFT?
    recordType     = field('recordType',      forceInt)
    isUrgent       = field('isUrgent',        forceInt)
    enableQueueing = True

    def getEmptyRecord(self):
        return QtGui.qApp.db.table('Schedule_Item').newRecord()


    def save(self):
        return QtGui.qApp.db.insertOrUpdate('Schedule_Item', self._record)


    def reload(self):
        self.setRecord( QtGui.qApp.db.getRecord('Schedule_Item', '*', self.id))


    def delete(self):
        id = self.id
        if id:
            QtGui.qApp.db.markRecordsDeleted('Schedule_Item', 'id=%d' % id)

    def getDynamicItemType(self, context):
        financeType = context.getFinanceType(self)
        if (financeType and financeType != '2') or context.isReStaging:
            return u''
        appointment = CAppointmentPurposeCache.getItem(self.appointmentPurposeId)
        isNKT = appointment and (not appointment.enablePrimaryRecord
                                 and not appointment.enableConsultancyRecord
                                 and not appointment.enableRecordViaInfomat
                                 and not appointment.enableRecordViaCallCenter
                                 and not appointment.enableRecordViaInternet
                                 and appointment.enableOwnRecord)
        isKT = not appointment or (appointment and (
                                   appointment.enablePrimaryRecord
                                   or appointment.enableConsultancyRecord
                                   or appointment.enableRecordViaInfomat
                                   or appointment.enableRecordViaCallCenter
                                   or appointment.enableRecordViaInternet))
        baseType = self.KT if isKT else self.NKT if isNKT else u''

        if context.postIdentificationCode in context.postForMainLogicRecord:
            return self.MKT if (not context.isExternal and isKT) else baseType
        elif context.postIdentificationCode in context.postForInterofficeRecord:
            return self.MKT
        return baseType


class CSchedule(CSqlRecordWrapper):
    atNone      = 0
    atAmbulance = 1
    atHome      = 2
    atExp       = 3
    atNames     = (u'Нет приёма', u'Амбулаторно', u'На дому', u'МК')

    def __init__(self, record = None):
        self.items = []
        CSqlRecordWrapper.__init__(self, record)


    def getEmptyRecord(self):
        return QtGui.qApp.db.table('Schedule').newRecord()


    def setRecord(self, record):
        CSqlRecordWrapper.setRecord(self, record)
        self.items = []
        if record:
            self._loadItems()


    id                   = field('id',                    forceRef)
    appointmentType      = field('appointmentType',       forceInt)
    appointmentPurposeId = field('appointmentPurpose_id', forceRef)
    personId             = field('person_id',             forceRef)
    office               = field('office',                forceString)
    date                 = field('date',                  forceDate)
    begTime              = field('begTime',               forceTime)
    endTime              = field('endTime',               forceTime)
    duration             = field('duration',              forceTime)
    capacity             = field('capacity',              forceInt)
    reasonOfAbsenceId    = field('reasonOfAbsence_id',    forceRef)
    done                 = field('done',                  forceInt)
    doneTime             = field('doneTime',              forceTime)
    activityId           = field('activity_id',           forceRef)

    def _loadItems(self):
        id = self.id
        if id:
            db = QtGui.qApp.db
            table = db.table('Schedule_Item')
            records = db.getRecordList(table, '*', [table['deleted'].eq(0),
                                                    table['master_id'].eq(id),
                                                   ],
                                       'overtime, idx, time'
                                      )
            for record in records:
                self.items.append(CScheduleItem(record))


    def reloadItems(self):
        self.items = []
        self._loadItems()


    def asDict(self):
        result = CSqlRecordWrapper.asDict(self)
        result['items'] = [item.asDict() for item in self.items]
        return result


    def setDict(self, data):
        CSqlRecordWrapper.setDict(self, data)

        self.items = []
        for itemData in data.get('items', []):
            item = CScheduleItem()
            item.setDict(itemData)
            self.items.append(item)


    def calcTimePlan(self):
        times = calcTimePlan(self.begTime, self.endTime, self.duration, self.capacity, self.personId, True)
        if len(times) == len(self.items) and all(time == item.time.time() for time, item in zip(times, self.items)):
            return

        self.capacity = len(times)
        for item in self.items:
            item.delete()
        self.items = []
        prevTime = self.begTime
        date = self.date
        for time in times:
            if time<prevTime:
                date.addDays(1)
            prevTime = time
            datetime = QDateTime(date, time)
            item = CScheduleItem()
            item.time = datetime
            item.appointmentPurposeId = self.appointmentPurposeId
            self.items.append(item)


    def cleanItems(self):
        self.items = []


    def calcTimePlanIfRequired(self):
        if self.isFreeToChange():
            if self.appointmentType != 0 and not self.items:
                if self.appointmentType:
                    self.calcTimePlan()
                else:
                    #self.items = []
                    pass


    def save(self):
        self.calcTimePlanIfRequired()

        db = QtGui.qApp.db
        if self.id is None or self.isDirty:
            id = db.insertOrUpdate('Schedule', self._record)
            self.isDirty = False
        else:
            id = self.id
        idList = []
        for i, item in enumerate(self.items):
            if item.isDirty or item.scheduleId != id or item.idx != i or item.id is None:
                item.scheduleId = id
                item.idx = i
                item.save()
            idList.append(item.id)
        # подчистка "хвостов"
        table = db.table('Schedule_Item')
        cond = [table['master_id'].eq(id), table['id'].notInlist(idList)]
        db.markRecordsDeleted(table, cond)


    def delete(self):
        id = self.id
        if id:
            QtGui.qApp.db.markRecordsDeleted('Schedule', 'id=%d' % id)
            QtGui.qApp.db.markRecordsDeleted('Schedule_Item', 'master_id=%d' % id)


    def isEmpty(self):
        return self.appointmentType == 0


    def isFreeToChange(self):
        if not self.id:
            return True
        for item in self.items:
            if item.clientId: # or item.endOfReserve:
                return False
        return True

    def isFreeToChange_Custom(self):
        if not self.id:
            return True
        for item in self.items:
            db = QtGui.qApp.db
            oldRecord = db.getRecord('Schedule_Item', '*', item.id)
            if forceRef(oldRecord.value('client_id')):
                return False
        return True

    def isFreeToChangeCustomWithoutItemsNoId(self):
        db = QtGui.qApp.db
        tableScheduleItem = db.table('Schedule_Item')
        tableSchedule = db.table('Schedule')
        table = tableSchedule.leftJoin(tableScheduleItem,
                                       [tableSchedule['id'].eq(tableScheduleItem['master_id']),
                                        tableScheduleItem['client_id'].isNotNull(),
                                        tableScheduleItem['deleted'].eq(0)])
        columns = [tableSchedule['id'].name(), tableScheduleItem['client_id'].name()]
        cond = [tableSchedule['deleted'].eq(0),
                tableSchedule['person_id'].eq(self.personId),
                tableSchedule['date'].eq(self.date)]
        record = db.getRecordEx(table, columns, cond, tableScheduleItem['client_id'].name() + ' DESC')
        if record:
            scheduleId = forceRef(record.value('id'))
            clientId = forceRef(record.value('client_id'))
            if scheduleId:
                self.id = scheduleId
            if clientId:
                return False
            else:
                return True
        else:
            return True

    def isFreeToChange_CustomWithoutItems(self):
        if not self.id:
            return True
        db = QtGui.qApp.db
        tableScheduleItem = db.table('Schedule_Item')
        record = db.getRecordEx(tableScheduleItem,
                                tableScheduleItem['client_id'].name(),
                                [tableScheduleItem['deleted'].eq(0),
                                 tableScheduleItem['master_id'].eq(self.id)],
                                tableScheduleItem['client_id'].name()+' DESC')
        if record and forceRef(record.value('client_id')):
            return False
        return True

    def checkAndUpdateItems(self, showMessage=True):
        """
        1. Функция сравнивает количество записанных пациентов с БД, в случае
        различия восстанавливает актуальное значение и возвращает True.
        2. Функция сравнивает id в модели и БД, и в случае если например отчистили
        талон (создалась копия), то меняет id текущего талона на новый. Во втором
        случае я не буду возвращать True, т.к. это не блокировка сохранения, а
        просто подмена записи на её копию.
        """
        if not self.id:
            # Тут ноувэй нормально проверить запись, та и должна сработать отдельная проверка (noId) при сохранении,
            # ну либо это доп. период в рамках дня
            return False

        db = QtGui.qApp.db
        currentItems = filter(lambda i: i.clientId, self.items)

        table = db.table('Schedule_Item')
        #cols = [table['time'], table['client_id']]
        cols = [u"SUM(IF(Schedule_Item.client_id IS NOT NULL, 1, 0)) AS clientsCount",
                u"SUM(Schedule_Item.id) AS checksumOfIds",
                u"GROUP_CONCAT(CONCAT(Schedule_Item.id, '=', Schedule_Item.time)) AS idList"]
        cond = [table['deleted'].eq(0), table['master_id'].eq(self.id)]
        record = db.getRecordEx(table, cols, cond)

        if record:
            clientsCount = forceInt(record.value('clientsCount'))
            checksumOfDBIds = forceInt(record.value('checksumOfIds'))
            idAndTimeListStr = forceString(record.value('idList'))
        else:
            clientsCount, checksumOfDBIds, idAndTimeListStr = 0, 0, u''

        if clientsCount != len(currentItems):
            if showMessage:
                if clientsCount > 0:
                    message = u'Обнаружен записанный пациент!'
                else:
                    message = u'Обнаружены изменения в периоде!'
                QtGui.QMessageBox.information( None,
                                              u'Внимание!',
                                              message,
                                              QtGui.QMessageBox.Ok)
            self.restoreValuesFromRecord()
            return True
        else:
            # внутри else по причине того, что если у нас есть запись пациента, то весь период будет взят из базы (вместе с items)
            # для проверки изменений id'шников проще всего брать сумму id и сравнивать с базой (что-то типа контрольной суммы)

            # Логика такова, через фильтр проверяем все талоны на отсутствие в базе (c del=0), после проходим
            # по полученным талонам и по времени находим копию (время по идее не будет пересекаться в рамках периода),
            # после чего присвоим новый id (нового свободного номерка, но по факту копии того) и восстановим из БД

            checksumOfModelIds = sum(map(lambda i: i.id, self.items))
            if checksumOfDBIds and idAndTimeListStr:
                if checksumOfModelIds != checksumOfDBIds:
                    if showMessage and checksumOfModelIds > 0:
                        message = u'Обнаружены изменения в талонах периода!'
                        QtGui.QMessageBox.information(None,
                                                      u'Внимание!',
                                                      message,
                                                      QtGui.QMessageBox.Ok)
                    self.findAndUpdateDeletedRecord(idAndTimeListStr)
        return False

    def restoreValuesFromRecord(self):
        db = QtGui.qApp.db
        table = db.table('Schedule')
        record = db.getRecordEx(table, '*', table['id'].eq(self.id))
        if record:
            self.setRecord(record)
        if not self.items:
            self._loadItems()


    def findAndUpdateDeletedRecord(self, idAndTimeListStr):
        """
        Проверяем на то что талон с записью был "отчищен" от записи пациента,
        а при текущей логике при освобождении талона создаётся новый.
        Если найден удалённый талон в модели, то мы ищем его не удалённую
        копию в бд и по новому id указываем новый record.
        :param idAndTimeListStr: - Это строка из БД вида: 'id=datetime,id=datetime,...'. Где datetime это колонка time в таб. Schedule_Item, ну и собственно id из неё же.
        """
        idAndTimeList = [i.split(u'=') for i in idAndTimeListStr.split(u',')]
        idsList = [i[0] for i in idAndTimeList]
        idToTimeDict = {i[1]: i[0] for i in idAndTimeList}
        deletedItems = filter(lambda i: i.id not in idsList, self.items)
        for deletedItem in deletedItems:
            newItemId = idToTimeDict.get(unicode(deletedItem.time.toString('yyyy-MM-dd HH:mm:ss')))
            if newItemId:
                deletedItem.id = newItemId
                deletedItem.reload()

    def getQueuedClientsCount(self):
        return sum(bool(item.clientId) for item in self.items)

    def getCapacityAppointmentPurpose(self, appointmentPurposeId, personId):
        capacity = 0
        for item in self.items:
            if item.appointmentPurposeId == appointmentPurposeId or item.appointmentPurposeId is None:
                capacity += 1
            else:
                appointmentPurpose = CAppointmentPurposeCache.getItem(item.appointmentPurposeId)
                if personId == QtGui.qApp.userId and appointmentPurpose.enableOwnRecord:
                    capacity += 1
                elif QtGui.qApp.userSpecialityId and personId != QtGui.qApp.userId and appointmentPurpose.enableConsultancyRecord:
                    capacity += 1
                elif not QtGui.qApp.userSpecialityId and appointmentPurpose.enablePrimaryRecord:
                    capacity += 1
        return capacity


# #####################################################


def getDynamicItemType(scheduleItem, personId):
    u"""
    Получение (и прописывание) дин. типа для одного талона с созданием контекста внутри
    """
    if isinstance(scheduleItem, CScheduleItem):
        dynamicItemType = scheduleItem.getDynamicItemType(CDynamicItemTypeContext(personId))
        scheduleItem.dynamicItemType = dynamicItemType
        return dynamicItemType
    else:
        return None


def updateDynamicItemTypes(items, personId, appointmentType, context=None):
    u"""
    Пересчитывает тип талонов (КТ|НКТ|МКТ)
    """
    if not items:
        return
    elif not isinstance(items, list):
        items = [items]
    if appointmentType == CSchedule.atHome or not personId:
        for item in items:
            item.dynamicItemType = u''
        return
    if context is None:
        context = CDynamicItemTypeContext(personId)
    for item in items:
        item.dynamicItemType = item.getDynamicItemType(context)


_postListsForInterofficeLogic = None


def fillPostListsForInterofficeLogic(postForMainLogicRecord, postForInterofficeRecord):
    """
    Получения списка должностей для вычисления МКЗ
    перенёс сюда, чтоб не дублировать и по логике вроде тоже подходит
    """
    records = QtGui.qApp.db.getRecordList('GetPositionList', ['code_last', 'code'], 'code_last IN (13,14)')
    for record in records:
        if record.value('code_last') == 13:
            postForMainLogicRecord.append(forceRef(record.value('code')))
        else:
            postForInterofficeRecord.append(forceRef(record.value('code')))


def getPostListsForInterofficeLogic():
    global _postListsForInterofficeLogic
    if _postListsForInterofficeLogic is None:
        postForMainLogicRecord, postForInterofficeRecord = [], []
        fillPostListsForInterofficeLogic(postForMainLogicRecord, postForInterofficeRecord)
        _postListsForInterofficeLogic = (postForMainLogicRecord, postForInterofficeRecord)
    return _postListsForInterofficeLogic


class CDynamicItemTypeContext(object):
    u"""
    Контекст для расчёта типа талона (КТ|НКТ|МКТ)
    Сделано для хранения и нахождения одинаковых значений в одном месте
    """

    def __init__(self, personId):
        self.personId = personId
        self.postForMainLogicRecord, self.postForInterofficeRecord = getPostListsForInterofficeLogic()
        self.postIdentificationCode = getPostIdentCodeByPersonId(personId)
        self.isExternal = forceBool(QtGui.qApp.db.translate('Person', 'id', personId, 'availableForExternal'))
        self.isReStaging = QtGui.qApp.isReStagingInQueue()
        self._financeCache = {}

    def getFinanceType(self, scheduleItem):
        key = scheduleItem.appointmentPurposeId
        if key not in self._financeCache:
            record = getScheduleItemIdFinance(scheduleItem)
            self._financeCache[key] = forceString(record.value('code')) if record else None
        return self._financeCache[key]


# #####################################################
# Проверки при записи к врачу (желательно выноссить в одно место) + вспомогательные функции


def checkIsNKTReservedForTMK(widget, personId, date, clientId):
    """
    Проверяем нужно ли зарезервировать НКТ талон под ТМК при записи
    Проверка вынесена в одно место для удобной правки в будущем и DRY
    Предполагается что проверка вызывается только если
    номерок при записи имеет дин. тип НКТ, не сверхплановый и
    recordType не 4 (не ТМК)
    True - зарезервирован (т.е. проверку не прошёл)
    Связанные TT: 4889, 4902 (возможно скажу себе спасибо в будущем)
    """
    db = QtGui.qApp.db
    # 25.08.2026 по просьбе добавил пропуск проверки если пациенту меньше 18 лет
    if calcAgeInYears(forceDate(db.translate('Client', 'id', clientId, 'birthDate')), QDate.currentDate()) < 18:
        return False

    #4902 настройка по должностям для кого должно применяться ограничение на нкт талон для тмк
    widgetHasPostsList = hasattr(widget, 'postForCheckNKTReservedForTMK')
    if widgetHasPostsList and widget.postForCheckNKTReservedForTMK:
        postsList = widget.postForCheckNKTReservedForTMK
    else:
        records = db.getRecordList('GetPositionList', 'code', 'code_last = 15')
        postsList = [forceRef(record.value(0)) for record in records]
        if widgetHasPostsList:
            widget.postForCheckNKTReservedForTMK = postsList
    # пропуск если должности врача нет в списке
    if getPostIdentCodeByPersonId(personId) not in postsList:
        return False

    # получаем все талоны по всем периодам в этот день и определяем их тип
    items = getDayScheduleItems(personId, date, CSchedule.atAmbulance)
    updateDynamicItemTypes(items, personId, CSchedule.atAmbulance)

    # получаем только НКТ талоны за день
    itemsNKT = [item for item in items if not item.overtime and item.dynamicItemType == CScheduleItem.NKT]
    if not itemsNKT:
        return False

    # Выделили мин. кол-во в БД чтоб при каких то изменениях не лезть в код (0 = отключено)
    minReservedSlotsForTMK = forceInt(db.translate('rbExchangePreferences', 'code', 'minReservedSlotsForTMK', 'value'))

    # Смотрим кол-во уже активных ТМК записей и достигнуто ли минимально нужное кол-во
    countTMKItems = len([item for item in itemsNKT if item.clientId and item.recordType == 4])
    if countTMKItems >= minReservedSlotsForTMK:
        return False

    # Получаем кол-во оставшихся свободных и учитываем наличие сущ. ТМК записей и смотрим можно ли
    # записать ещё не затрагивая мин. резерв
    freeItemsNKT = [item for item in itemsNKT if not item.clientId]
    if len(freeItemsNKT) <= minReservedSlotsForTMK - countTMKItems:
        QtGui.QMessageBox.critical(widget, u'Внимание!',
                                   u'Данный талон предназначен для ТМК',
                                   QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
        return True

    return False


def getDayScheduleItems(personId, date, appointmentType):
    """
    Все талончики по периодам на дату
    """
    db = QtGui.qApp.db
    tableSchedule = db.table('Schedule')
    tableScheduleItem = db.table('Schedule_Item')
    table = tableScheduleItem.innerJoin(tableSchedule, tableScheduleItem['master_id'].eq(tableSchedule['id']))
    records = db.getRecordList(table, 'Schedule_Item.*', [tableSchedule['deleted'].eq(0),
                                                             tableSchedule['person_id'].eq(personId),
                                                             tableSchedule['date'].eq(date),
                                                             tableSchedule['appointmentType'].eq(appointmentType),
                                                             tableScheduleItem['overtime'].eq(0),
                                                             tableScheduleItem['deleted'].eq(0),
                                                            ])
    return [CScheduleItem(record) for record in records]


# #####################################################

# возможно, что эту и следующую функцию лучше куда-то перенести
def confirmAndFreeScheduleItem(widget, scheduleItemId, recordPersonId, clientId):
    # освободить schedule item с подтверждением
    # widget должен быть наследником CRecordLockMixin
    # recordPersonId
    # clientId передаётся для защиты от возможной порчи данных разными клиентами

    if (   QtGui.qApp.userHasRight(urDeleteOtherQueue)
        or (QtGui.qApp.userHasRight(urDeleteOwnQueue) and recordPersonId == QtGui.qApp.userId)
       ):
        confirmation = QtGui.QMessageBox.warning(widget,
                u'Внимание!',
                u'Подтвердите удаление записи к врачу',
                QtGui.QMessageBox.Ok|QtGui.QMessageBox.Cancel,
                QtGui.QMessageBox.Cancel)
        if confirmation != QtGui.QMessageBox.Ok:
            return
        freeScheduleItem(widget, scheduleItemId, clientId)


def freeScheduleItemInt(record, deleteForTransfer=False, additionalDeleteNote=u''):
    db = QtGui.qApp.db
    table = db.table('Schedule_Item')
    newRecordId = None
    deleteNote = u'Запись отменена через клиент Самсон'
    if forceBool(record.value('overtime')):
        record.setValue('deleted', toVariant(1))
        record.setValue('checked', toVariant(0))
        record.setValue('homeCallStatus', toVariant(0))
    else:
        # --- После 10.02.2026 у новой записи очищаем все поля и deleted = 0
        newRecord = type(record)(record)
        newRecord.setNull('id')
        newRecord.setValue('deleted', toVariant(0))
        newRecord.setNull('client_id')
        newRecord.setNull('recordPerson_id')
        newRecord.setNull('recordDatetime')
        newRecord.setNull('srcNumber')
        newRecord.setValue('recordClass', toVariant(0))
        newRecord.setValue('complaint', toVariant(''))
        newRecord.setValue('note', toVariant(''))
        newRecord.setValue('checked', toVariant(0))
        newRecord.setValue('homeCallStatus', toVariant(0))
        newRecord.setNull('system_guid')
        newRecord.setNull('recordType')
        newRecord.setNull('infections')
        newRecord.setValue('isUrgent', toVariant(0))
        db.insertRecord(table, newRecord)

        # --- После 10.02.2026 у старой записи deleted = 1
        record.setValue('deleted', toVariant(1))
        record.setNull('endOfReserve')

        if deleteForTransfer:
            record.setNull('system_guid')
            deleteNote = u'Запись перенесена через клиент Самсон'

        if additionalDeleteNote:
            deleteNote += u' ({note})'.format(note=additionalDeleteNote)

        record.setValue('note', toVariant(deleteNote))

        # --- Было ранее 10.02.2026
        # newRecord = type(record)(record)
        # newRecord.setNull('id')
        # newRecord.setValue('deleted', toVariant(1))
        # newRecord.setNull('endOfReserve')
        # db.insertRecord(table, newRecord)
        #
        # record.setNull('client_id')
        # record.setNull('recordPerson_id')
        # record.setNull('recordDatetime')
        # record.setNull('srcNumber')
        # record.setValue('recordClass', toVariant(CScheduleItem.rcSamson))
        # record.setValue('complaint', toVariant(''))
        # record.setValue('note', toVariant(''))
        # record.setValue('checked', toVariant(0))
        # record.setValue('homeCallStatus', toVariant(0))
        # ---
    db.updateRecord(table, record)
    
    return newRecordId


def freeScheduleItem(widget, scheduleItemId, clientId, additionalDeleteNote=u''):
    # освободить schedule item
    # widget должен быть наследником CRecordLockMixin
    # clientId передаётся для защиты от возможной порчи данных разными клиентами
    db = QtGui.qApp.db
    lockId = widget.lock('Schedule_Item', scheduleItemId)
    if lockId:
        try:
            db.transaction()
            try:
                oldRecord = db.getRecord('Schedule_Item', '*', scheduleItemId)
                if forceRef(oldRecord.value('client_id')) == clientId and not forceBool(oldRecord.value('deleted')):
                    # всё чисто, никто не удалил и не изменил критическим образом запись
                    # для нормальной записи -
                    # делаем новую запись копией старой с пометкой удаления
                    # а старую очищаем
                    # для "внеочередной" записи (overtime)
                    # просто удаляем запись
                    freeScheduleItemInt(oldRecord, additionalDeleteNote=additionalDeleteNote)
                db.commit()
            except:
                db.rollback()
                QtGui.qApp.logCurrentException()
                raise
        finally:
            widget.releaseLock(lockId)


def getScheduleItemIdListForClient(clientId, specialityId, date=None, appointmentType=None):
    db = QtGui.qApp.db
    tableSchedule = db.table('Schedule')
    tableScheduleItem = db.table('Schedule_Item')
    tablePerson = db.table('Person')
    tableRBSpeciality = db.table('rbSpeciality')
    tableQuery = tableScheduleItem
    tableQuery = tableQuery.leftJoin(tableSchedule, tableSchedule['id'].eq(tableScheduleItem['master_id']))
    tableQuery = tableQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableSchedule['person_id']))
    tableQuery = tableQuery.leftJoin(tableRBSpeciality, tableRBSpeciality['id'].eq(tablePerson['speciality_id']))
    cols = [tableScheduleItem['id']]
    cond = [tableScheduleItem['deleted'].eq(0),
            tableSchedule['deleted'].eq(0),
            tablePerson['deleted'].eq(0),
            tableScheduleItem['client_id'].eq(clientId),
            # tableSchedule['date'].ge(date if date else QDate.currentDate()),
           ]
    if date and date == QDate.currentDate():
        cond.append(' Schedule.date = current_date ')
    else:
        cond.append(' Schedule.date >= ADDDATE(current_date, 1) ')
    cond.append(tableSchedule['appointmentType'].eq(appointmentType))
    OKSOCode = forceString(db.translate('rbSpeciality', 'id', specialityId, 'OKSOCode'))
    OKSOCodeList = ('040122', '040819', '040110')
    if OKSOCode in OKSOCodeList:
        cond.append(tableRBSpeciality['OKSOCode'].inlist(OKSOCodeList))
    else:
        cond.append(tablePerson['speciality_id'].eq(specialityId))
    return db.getIdList(tableQuery, cols, cond)


def getScheduleItemIdFinance(scheduleItem):
    db = QtGui.qApp.db
    tableRBAppointmentPurpose = db.table('rbAppointmentPurpose')
    tableRBFinance = db.table('rbFinance')
    tableQuery = tableRBAppointmentPurpose
    tableQuery = tableQuery.leftJoin(tableRBFinance, tableRBAppointmentPurpose['finance_id'].eq(tableRBFinance['id']))
    cols = [tableRBFinance['code']]
    cond = [tableRBAppointmentPurpose['id'].eq(scheduleItem.appointmentPurposeId)]
    return db.getRecordEx(tableQuery, cols, cond)


def getScheduleItemIdListForClient_OMS(scheduleItemIdList):
    db = QtGui.qApp.db
    tableScheduleItem = db.table('Schedule_Item')
    tableRBAppointmentPurpose = db.table('rbAppointmentPurpose')
    tableRBFinance = db.table('rbFinance')
    tableQuery = tableScheduleItem
    tableQuery = tableQuery.leftJoin(tableRBAppointmentPurpose, tableRBAppointmentPurpose['id'].eq(tableScheduleItem['appointmentPurpose_id']))
    tableQuery = tableQuery.leftJoin(tableRBFinance, tableRBAppointmentPurpose['finance_id'].eq(tableRBFinance['id']))
    cond = [tableScheduleItem['id'].inlist(scheduleItemIdList), tableScheduleItem['deleted'].eq(0), ' (rbFinance.id IS NULL OR rbFinance.code = 2) ']
    return db.getRecordEx(tableQuery, '1', cond)


def getExceptionSpecialty(specialty_id):
    db = QtGui.qApp.db
    tableRBSpeciality = db.table('rbSpeciality')
    tableRBSpeciality_Identification = db.table('rbSpeciality_Identification')
    tableQuery = tableRBSpeciality
    tableQuery = tableQuery.leftJoin(tableRBSpeciality_Identification, "rbSpeciality.id = rbSpeciality_Identification.master_id AND rbSpeciality_Identification.system_id = (SELECT id FROM rbAccountingSystem `as` WHERE `as`.urn='urn:oid:1.2.643.5.1.13.13.11.1066') AND rbSpeciality_Identification.deleted=0 ")
    cond = [tableRBSpeciality['id'].eq(specialty_id), ' rbSpeciality_Identification.value in (SELECT code FROM GetPositionList  WHERE code_last=11) OR (rbSpeciality.isHigh=0 and regionalCode NOT IN (95, 206, 208))']
    record = db.getRecordEx(tableQuery, '1', cond)
    if record:
        return forceRef(record.value('1'))
    else:
        return 0

# #####################################################


def getGapList(personId):
    # gapList is list of (begGapTime, endGapTime) ordered by begGapTime
    # gaps may owerlap
    # gaps cannot cross midnight

    def addGap(gapList, record):
        bTime = forceTime(record.value('begTime'))
        eTime = forceTime(record.value('endTime'))
        if bTime < eTime:
            gapList.append((bTime, eTime))
        elif bTime > eTime:
            gapList.append((bTime, QTime(23, 59, 59, 999)))
            gapList.append((QTime(0, 0), eTime))

    db = QtGui.qApp.db
    specialityId = forceRef(db.translate('Person', 'id', personId, 'speciality_id'))
    orgStructureBaseId = forceRef(db.translate('Person', 'id', personId, 'orgStructure_id'))
    result = []
    orgStructureId = orgStructureBaseId
    while orgStructureId:
        orgStructureGapRecordList = db.getRecordList('OrgStructure_Gap', 'begTime, endTime',  'master_id=%d%s AND person_id IS NULL'%(orgStructureId, u' AND (speciality_id=%d OR speciality_id IS NULL)'%(specialityId) if specialityId else u' AND speciality_id IS NULL'), 'begTime, endTime')
        for record in orgStructureGapRecordList:
            addGap(result, record)
        recordInheritGaps = db.getRecordEx('OrgStructure', 'inheritGaps', 'id=%d'%(orgStructureId))
        inheritGaps = forceBool(recordInheritGaps.value(0)) if recordInheritGaps else (False if orgStructureGapRecordList else True)
        if not inheritGaps:
            break
        orgStructureId = forceRef(db.translate('OrgStructure', 'id', orgStructureId, 'parent_id'))
    orgStructureId = orgStructureBaseId
    while orgStructureId:
        personGapRecordList = db.getRecordList('OrgStructure_Gap', 'begTime, endTime',  'master_id=%d AND person_id=%d' %(orgStructureId, personId), 'begTime, endTime')
        for record in personGapRecordList:
            addGap(result, record)
        orgStructureId = forceRef(db.translate('OrgStructure', 'id', orgStructureId, 'parent_id'))
    result.sort()
    return result


def invertGapList(gapList):
    # inverted gapList (workList) is list of (begWorkTime, endWorkTime) ordered by begWorkTime
    # work times must not overlap
    # work times cannot cross midnight
    result = []
    workTime = QTime(0, 0)
    for bTime, eTime in gapList:
        if workTime < bTime:
            result.append((workTime, bTime))
        workTime = max(workTime, eTime)
    lastTime = QTime(23, 59, 59, 999)
    if workTime < lastTime:
        result.append((workTime, lastTime))
    return result


def filterWorkList(workList, begTime, endTime):
    # filtered workList is list of (begWorkTime, endWorkTime) limited by range(begTime, endTime)
    result = []
    for bTime, eTime in workList:
        if eTime>begTime:
            bPTime = max(bTime, begTime)
            ePTime = min(eTime, endTime)
            if bPTime<ePTime:
                result.append((bPTime, ePTime))
        if bTime>=endTime:
            break
    return result


def calcTimePlan(begTime, endTime, duration, capacity, personId, allowGaps):
    durationInSeconds = QTime().secsTo(duration)
    if begTime.secsTo(endTime) and (durationInSeconds or capacity > 0):
        if allowGaps:
            gapList = getGapList(personId)
        else:
            gapList = []
        fullWorkList = invertGapList(gapList)
        if durationInSeconds:
            return calcTimePlanForDuration(begTime, endTime, durationInSeconds, fullWorkList)
        else:
            return calcTimePlanForCapacity(begTime, endTime, capacity, fullWorkList)
    return []


def calcTimePlanForDuration(begTime, endTime, duration, fullWorkList):
    result = []
    if begTime<endTime:
        workList = filterWorkList(fullWorkList, begTime, endTime)
    elif begTime>endTime:
        workList = filterWorkList(fullWorkList, QTime(0, 0), endTime)
        workList.extend(filterWorkList(fullWorkList, begTime, QTime(23, 59, 59, 999)))
    else:
        workList = fullWorkList

    for bTime, eTime in workList:
        workPeriodDuraion = bTime.secsTo(eTime)
        capacity, idleTime = divmod(workPeriodDuraion, duration)
        # я пока не знаю, что делать если в конце рабочего периода остаётся большой промежуток
        # может быть, нужно начинать приём и продолжать его после перерыва?
        # может быть, можно немного отложить перерыв?
        # или предпочтительней немного сократить приём - и уложить целое число приёмов?
        for i in xrange(capacity):
            result.append(bTime.addSecs(i*duration))
    result.sort()
    return result


def calcTimePlanForCapacity(begTime, endTime, capacity, fullWorkList):
    result = []
    if begTime<endTime:
        workList = filterWorkList(fullWorkList, begTime, endTime)
    elif begTime>endTime:
        workList = filterWorkList(fullWorkList, QTime(0, 0), endTime)
        workList.extend(filterWorkList(fullWorkList, begTime, QTime(23, 59, 59, 999)))
    else:
        workList = fullWorkList
    sbList = [(bTime.secsTo(eTime), bTime) for bTime, eTime in workList]
    sbList.sort()
    unallocatedSeconds = sum([sb[0] for sb in sbList])
    unallocated = capacity
    for seconds, bTime in sbList:
        # 0.4 - это такая цифровая магия
        # 10.5 номерков превратится в 10
        # a 10.6 в 11
        # при этом на следующие (бОльшие) периоды остаётся меньше номерков
        part = int(seconds*unallocated/float(unallocatedSeconds)+0.4) if unallocatedSeconds else unallocated
        if part>0:
            unit = seconds//part
            for j in xrange(part):
                result.append(bTime.addSecs(j*unit))
        unallocatedSeconds -= seconds
        unallocated -= part
    result.sort()
    return result
