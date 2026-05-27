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
from PyQt4.QtCore import QDateTime, QTime

from library.Utils import forceBool, forceDate, forceDateTime, forceInt, forceRef, forceString, forceTime
from library.recordWrapper import CSqlRecordWrapper, field

from Timeline.Schedule import invertGapList, calcTimePlanForCapacity
from Resources.JobTicketStatus        import CJobTicketStatus


# ####################################################################


class COrgStructureJobTemplate(CSqlRecordWrapper):
    tableName = 'OrgStructure_JobTemplate'

    def getEmptyRecord(self):
        return QtGui.qApp.db.table(self.tableName).newRecord()

    id                   = field('id',                    forceRef)
    orgStructureId       = field('master_id',             forceRef)
    day                  = field('day',                   forceInt)
    jobTypeId            = field('jobType_id',            forceInt)
    jobPurposeId         = field('jobPurpose_id',         forceRef)
    begTime              = field('begTime',               forceTime)
    endTime              = field('endTime',               forceTime)
    quantity             = field('quantity',              forceInt)
    capacity             = field('capacity',              forceInt)


    def save(self):
        QtGui.qApp.db.insertOrUpdate(self.tableName, self._record)


    def isEmpty(self):
        return self.orgStructureId is None


# ####################################################################


class CJobTicket(CSqlRecordWrapper):

    def __init__(self, record = None):
        if record:
            is_used = forceBool(record.value('isUsed'))
            record.remove(record.indexOf('isUsed'))
        else:
            is_used = False
        CSqlRecordWrapper.__init__(self, record)
        if self.id is None:
            self._isUsed = False
        elif self.resConnectionId:
            self._isUsed = True
        else:
            self._isUsed = is_used


    def getEmptyRecord(self):
        return QtGui.qApp.db.table('Job_Ticket').newRecord()

    id = field('id')
    deleted          = field('deleted',         forceBool)
    jobId            = field('master_id',       forceRef)
    idx              = field('idx',             forceInt)
    datetime         = field('datetime',        forceDateTime)
    resTimestamp     = field('resTimestamp',    forceDateTime)
    resConnectionId  = field('resConnectionId', forceInt)
    status           = field('status',          forceInt)

    begDateTime      = field('begDateTime',     forceDateTime)
    endDateTime      = field('endDateTime',     forceDateTime)
    label            = field('label',           forceString)
    orgStructureId   = field('orgStructure_id', forceRef)
    note             = field('note',            forceString)
    isExceedQuantity = field('isExceedQuantity',forceBool)


    def save(self):
        return QtGui.qApp.db.insertOrUpdate('Job_Ticket', self._record)


    def reload(self):
        self.setRecord(QtGui.qApp.db.getRecord('Job_Ticket', '*', self.id))


    def delete(self):
        id = self.id
        if id:
            QtGui.qApp.db.markRecordsDeleted('Job_Ticket', 'id=%d' % id)
            self.deleted = 1


    def getIsUsed(self):
#         if self._isUsed is None:
#             if self.id is None:
#                 self._isUsed = False
#             elif self.resConnectionId:
#                 self._isUsed = True
#             else:
# #                self._isUsed = forceBool(QtGui.qApp.db.translate('vJobTicket', 'id', self.id, 'isUsed'))
#                 self._isUsed = forceBool(QtGui.qApp.db.translate('ActionProperty_Job_Ticket', 'value', self.id, 'id'))
        return self._isUsed


    isUsed = property(getIsUsed)


class CJob(CSqlRecordWrapper):
    def __init__(self, record = None):
        self.items = []
        self.cntOutOfOrder = 0
        self.cntReserved   = 0
        self.cntBusy       = 0
        self.cntExecuted   = 0
        CSqlRecordWrapper.__init__(self, record)


    def getEmptyRecord(self):
        return QtGui.qApp.db.table('Job').newRecord()


    def setRecord(self, record):
        CSqlRecordWrapper.setRecord(self, record)
        self.items = []
        if record:
            self._loadItems()


    id                   = field('id',                 forceRef)
    jobTypeId            = field('jobType_id',         forceRef)
    jobPurposeId         = field('jobPurpose_id',      forceRef)
    orgStructureId       = field('orgStructure_id',    forceRef)
    date                 = field('date',               forceDate)
    begTime              = field('begTime',            forceTime)
    endTime              = field('endTime',            forceTime)
    quantity             = field('quantity',           forceInt)
    capacity             = field('capacity',           forceInt)


    def _loadItems(self):
        id = self.id
        if id:
            db = QtGui.qApp.db
            table = db.table('Job_Ticket')
            records = db.getRecordList(table, '*, EXISTS(SELECT 1 FROM ActionProperty_Job_Ticket WHERE value = Job_Ticket.id) AS isUsed',
                                       [table['deleted'].eq(0),
                                        table['master_id'].eq(id)],
                                       'isExceedQuantity, idx, datetime'
                                      )
            for record in records:
                self.items.append(CJobTicket(record))
            self.updateStatistic()


    def updateStatistic(self):
        cntOutOfOrder = cntReserved = cntBusy = cntExecuted = 0
        for item in self.items:
            if item.isExceedQuantity:
                cntOutOfOrder += 1
            if item.isUsed:
                status = item.status
                if status in (CJobTicketStatus.wait, CJobTicketStatus.enqueued):
                    cntReserved += 1
                elif status == CJobTicketStatus.doing:
                    cntBusy += 1
                elif status == CJobTicketStatus.done:
                    cntExecuted += 1

        self.cntOutOfOrder = cntOutOfOrder
        self.cntReserved   = cntReserved
        self.cntBusy       = cntBusy
        self.cntExecuted   = cntExecuted


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
            item = CJobTicket()
            item.setDict(itemData)
            self.items.append(item)


    def calcTimePlan(self):
        times = calcTimePlanForOrgStructure(self.begTime, self.endTime, self.quantity, self.orgStructureId, True)
        if len(times) == len(self.items) and all(time == item.time.time() for time, item in zip(times, self.items)):
            return

        self.quantity = len(times)
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
            for cnt in xrange(max(1, self.capacity)):
                item = CJobTicket()
                item.datetime = datetime
                self.items.append(item)


    def cleanItems(self):
        self.items = []


    def calcTimePlanIfRequired(self):
        if self.isFreeToChange():
            if self.jobTypeId and not self.items:
                self.calcTimePlan()


    def save(self):
        self.calcTimePlanIfRequired()

        db = QtGui.qApp.db
        if self.id is None or self.isDirty:
            id = db.insertOrUpdate('Job', self._record)
            self.isDirty = False
        else:
            id = self.id
        idList = []
        for i, item in enumerate(self.items):
            idx = i
            if item.isDirty or item.jobId != id or item.idx != idx or item.id is None:
                item.jobId = id
                if not item.isExceedQuantity:
                    item.idx = idx
                jtId = item.save()
                item.id = jtId

            idList.append(item.id)
        # подчистка "хвостов"
        table = db.table('Job_Ticket')
        cond = [table['master_id'].eq(id), table['id'].notInlist(idList)]
        db.markRecordsDeleted(table, cond)


    def delete(self):
        id = self.id
        if id:
            QtGui.qApp.db.markRecordsDeleted('Job', 'id=%d' % id)
            QtGui.qApp.db.markRecordsDeleted('Job_Ticket', 'master_id=%d' % id)


    def isEmpty(self):
        return self.jobTypeId is None


    def isFreeToChange(self):
        if not self.id:
            return True
        return not any(item.isUsed for item in self.items)


#    def getQueuedClientsCount(self):
#        return sum(bool(item.clientId) for item in self.items)

## #####################################################
#
## возможно, что эту и следующую функцию лучше куда-то перенести
#def confirmAndFreeScheduleItem(widget, scheduleItemId, recordPersonId, clientId):
#    # освободить schedule item с подтверждением
#    # widget должен быть наследником CRecordLockMixin
#    # recordPersonId
#    # clientId передаётся для защиты от возможной порчи данных разными клиентами
#
#    if (   QtGui.qApp.userHasRight(urDeleteOtherQueue)
#        or (QtGui.qApp.userHasRight(urDeleteOwnQueue) and recordPersonId == QtGui.qApp.userId)
#       ):
#        confirmation = QtGui.QMessageBox.warning(widget,
#                u'Внимание!',
#                u'Подтвердите удаление записи к врачу',
#                QtGui.QMessageBox.Ok|QtGui.QMessageBox.Cancel,
#                QtGui.QMessageBox.Cancel)
#        if confirmation != QtGui.QMessageBox.Ok:
#            return
#        freeScheduleItem(widget, scheduleItemId, clientId)
#
#
#def freeScheduleItemInt(record):
#    db = QtGui.qApp.db
#    table = db.table('Schedule_Item')
#    if forceBool(record.value('isExceedQuantity')):
#        record.setValue('deleted', toVariant(1))
#    else:
#        newRecord = type(record)(record)
#        newRecord.setNull('id')
#        newRecord.setValue('deleted', toVariant(1))
#        db.insertRecord(table, newRecord)
#
#        record.setNull('client_id')
#        record.setNull('recordPerson_id')
#        record.setNull('recordDatetime')
#        record.setValue('recordClass', toVariant(CScheduleItem.rcSamson))
#        record.setValue('complaint', toVariant(''))
#        record.setValue('note', toVariant(''))
#        record.setValue('checked', toVariant(0))
#    db.updateRecord(table, record)
#
#
#def freeScheduleItem(widget, scheduleItemId, clientId):
#    # освободить schedule item
#    # widget должен быть наследником CRecordLockMixin
#    # clientId передаётся для защиты от возможной порчи данных разными клиентами
#    db = QtGui.qApp.db
#    lockId = widget.lock('Schedule_Item', scheduleItemId)
#    try:
#        db.transaction()
#        try:
#            oldRecord = db.getRecord('Schedule_Item', '*', scheduleItemId)
#            if forceRef(oldRecord.value('client_id')) == clientId and not forceBool(oldRecord.value('deleted')):
#                # всё чисто, никто не удалил и не изменил критическим образом запись
#                # для нормальной записи -
#                # делаем новую запись копией старой с пометкой удаления
#                # а старую очищаем
#                # для "внеочередной" записи (isExceedQuantity)
#                # просто удаляем запись
#                freeScheduleItemInt(oldRecord)
#                db.commit()
##                return True
#        except:
#            db.rollback()
#            QtGui.qApp.logCurrentException()
#            raise
#    finally:
#        widget.releaseLock(lockId)
##    return False
#
#
#def getScheduleItemIdListForClient(clientId, specialityId, date=None):
#    db = QtGui.qApp.db
#    tableSchedule = db.table('Schedule')
#    tableScheduleItem = db.table('Schedule_Item')
#    tablePerson = db.table('Person')
#    tableRBSpeciality = db.table('rbSpeciality')
#    tableQuery = tableScheduleItem
#    tableQuery = tableQuery.leftJoin(tableSchedule, tableSchedule['id'].eq(tableScheduleItem['master_id']))
#    tableQuery = tableQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableSchedule['person_id']))
#    tableQuery = tableQuery.leftJoin(tableRBSpeciality, tableRBSpeciality['id'].eq(tablePerson['speciality_id']))
#    cols = [tableScheduleItem['id']]
#    cond = [tableScheduleItem['deleted'].eq(0),
#            tableSchedule['deleted'].eq(0),
#            tablePerson['deleted'].eq(0),
#            tableScheduleItem['client_id'].eq(clientId),
#            tableSchedule['date'].ge(date if date else QDate.currentDate()),
#           ]
#    OKSOCode = forceString(db.translate('rbSpeciality', 'id', specialityId, 'OKSOCode'))
#    OKSOCodeList = ('040122', '040819', '040110')
#    if OKSOCode in OKSOCodeList:
#        cond.append(tableRBSpeciality['OKSOCode'].inlist(OKSOCodeList))
#    else:
#        cond.append(tablePerson['speciality_id'].eq(specialityId))
#    return db.getIdList(tableQuery, cols, cond)
#
#
## #####################################################
#
#

def getGapListForOrgStructure(orgStructureId):
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
    result = []
    while orgStructureId:
        orgStructureGapRecordList = db.getRecordList('OrgStructure_Gap',
                                                     'begTime, endTime',
                                                     'master_id=%d AND person_id IS NULL AND speciality_id IS NULL'%orgStructureId,
                                                     'begTime, endTime')
        for record in orgStructureGapRecordList:
            addGap(result, record)
        recordInheritGaps = db.getRecordEx('OrgStructure', 'inheritGaps', 'id=%d'%(orgStructureId))
        inheritGaps = forceBool(recordInheritGaps.value(0)) if recordInheritGaps else (False if orgStructureGapRecordList else True)
        if not inheritGaps:
            break
        orgStructureId = forceRef(db.translate('OrgStructure', 'id', orgStructureId, 'parent_id'))
    result.sort()
    return result


def calcTimePlanForOrgStructure(begTime, endTime, quantity, orgStructureId, allowGaps):
    if begTime.secsTo(endTime) and quantity > 0:
        if allowGaps:
            gapList = getGapListForOrgStructure(orgStructureId)
        else:
            gapList = []
        fullWorkList = invertGapList(gapList)
        return calcTimePlanForCapacity(begTime, endTime, quantity, fullWorkList)
    return []

