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
from PyQt4.QtCore import Qt, QDate, QDateTime, QObject

from library.crbcombobox        import CRBComboBox
from library.InDocTable         import CInDocTableModel, CDateInDocTableCol, CRBInDocTableCol
from library.Utils              import forceDate, forceDateTime, forceInt, forceRef, toVariant, variantEq

from Events.Utils               import CEventTypeDescription, getEventAidTypeCode, getEventKeepVisitParity, getEventSceneId, getEventServiceId, getEventShowTime, getEventShowVisitTime, getEventVisitServiceFilter, getExactServiceId, getIsDayStationary
from Orgs.PersonComboBoxEx      import CPersonFindInDocTableCol
from RefBooks.Service.RBServiceComboBox import CRBServiceComboBox
from RefBooks.Tables            import rbFinance, rbScene, rbVisitType
from Users.Rights               import urEditAfterInvoicingEvent


class CVisitServiceInDocTableCol(CRBInDocTableCol):
    hospitalMedicalAidTypeCode = '7'
    def __init__(self, title, fieldName, width, tableName, **params):
        CRBInDocTableCol.__init__(self, title, fieldName, width, tableName, **params)
        self.eventEditor = params.get('eventEditor', None)


    def createEditor(self, parent):
        additionalIdList = []
        if self.eventEditor is not None:
            serviceId = getEventServiceId(self.eventEditor.eventTypeId)
            if serviceId:
                additionalIdList.append(serviceId)
        needFilter = getEventAidTypeCode(self.eventEditor.eventTypeId) == CVisitServiceInDocTableCol.hospitalMedicalAidTypeCode
        editor = CRBServiceComboBox(parent, filterByHospitalBedsProfile=needFilter, additionalIdList=additionalIdList)
        editor.loadData(addNone=self.addNone, filter=self.filter)
        editor.setShowFields(self.showFields)
        editor.setPreferredWidth(self.preferredWidth)
        return editor


    def setEditorData(self, editor, value, record):
        editor.setValue(forceInt(value))
        if self.eventEditor is not None:
            visitServiceFilter = getEventVisitServiceFilter(self.eventEditor.eventTypeId)
            editor.setServiceFilterByCode(visitServiceFilter)


class CEventVisitsModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Visit', 'id', 'event_id', parent)
        self.addCol(CPersonFindInDocTableCol(u'Врач',               'person_id',    20,  'vrbPersonWithSpecialityAndOrgStr', parent=parent))
        self.addCol(CPersonFindInDocTableCol(u'Ассистент',          'assistant_id', 20,  'vrbPersonWithSpecialityAndOrgStr', parent=parent))
        self.addCol(CRBInDocTableCol(        u'Место',              'scene_id',     10,  rbScene, addNone=False, preferredWidth=150))
        #self.addCol(CDateTimeInDocTableCol(  u'Дата',               'date',         20))
        self.addCol(CDateInDocTableCol(      u'Дата',               'date',         20))
        self.addCol(CRBInDocTableCol(        u'Тип',                'visitType_id', 10,  rbVisitType, addNone=False, showFields=CRBComboBox.showCodeAndName))
        self.addCol(CVisitServiceInDocTableCol( u'Услуга',             'service_id',   50,  'rbService', addNone=False, showFields=CRBComboBox.showCodeAndName, preferredWidth=150, eventEditor=parent))
        self.addCol(CRBInDocTableCol(        u'Тип финансирования', 'finance_id',   50,  rbFinance, addNone=False, showFields=CRBComboBox.showCodeAndName, preferredWidth=150))
        self.addHiddenCol('payStatus')
        self.hasAssistant = True
        self.defaultSceneId = None
        self.tryFindDefaultSceneId = True
        self.defaultVisitTypeId = None
        self.tryFindDefaultVisitTypeId = True
        self.readOnly = False


    def setReadOnly(self, value):
        self.readOnly = value


    def flags(self, index):
        if self.readOnly:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        column = index.column()
        flags = self._cols[column].flags()
        if self.cellReadOnly(index):
            flags = flags & (~Qt.ItemIsEditable) & (~Qt.ItemIsUserCheckable)
        return flags


    def addVisitByAction(self, action):
        actionRecord = action.getRecord()
        actionPersonId = forceRef(actionRecord.value('person_id'))
        actionEndDate = forceDateTime(actionRecord.value('endDate'))

        if actionPersonId and actionEndDate:
            isExists = self.isExists(actionPersonId, actionEndDate)
            if not isExists:
                actionType  = action.getType()
                sceneId     = actionType.addVisitSceneId
                visitTypeId = actionType.addVisitTypeId
                record      = self.getEmptyRecord(sceneId, actionPersonId)

                record.setValue('date', toVariant(actionEndDate))
                if visitTypeId:
                    record.setValue('visitType_id', toVariant(visitTypeId))
                self.addRecord(record)


    def addVisit(self, personId,  date,  sceneId,  visitTypeId):
        if personId and date:
            isExists = self.isExists(personId, date)
            if not isExists:
                record = self.getEmptyRecord(sceneId, personId)
                record.setValue('date', toVariant(date))
                if visitTypeId:
                    record.setValue('visitType_id', toVariant(visitTypeId))
                self.addRecord(record)
                return record
        return None


    def isExists(self, personId, date):
        date = forceDate(date)
        for item in self._items:
            locPersonId = forceRef(item.value('person_id'))
            locDate = forceDate(item.value('date'))

            if personId == locPersonId and date == locDate:
                return True
        return False


    def loadItems(self, eventId):
        CInDocTableModel.loadItems(self, eventId)
        self._items.sort(key=lambda x: forceDateTime(x.value('date') if x else None))
        if self.items():
            lastItem = self.items()[-1]
            if self.defaultSceneId is None:
                self.defaultSceneId = forceRef(lastItem.value('scene_id'))
            if self.defaultVisitTypeId is None:
                self.defaultVisitTypeId = forceRef(lastItem.value('visitType_id'))


    # Это хак: удаляем payStatus из записи
    def saveItems(self, masterId):
        if self._items is not None:
            db = QtGui.qApp.db
            table = self._table
            masterId = toVariant(masterId)
            masterIdFieldName = self._masterIdFieldName
            idFieldName = self._idFieldName
            idList = []
            self._items.sort(key=lambda x: forceDateTime(x.value('date') if x else None))
            for idx, record in enumerate(self._items):
                record.setValue(masterIdFieldName, masterId)
                if self._idxFieldName:
                    record.setValue(self._idxFieldName, toVariant(idx))
                if self._extColsPresent:
                    outRecord = self.removeExtCols(record)
                else:
                    outRecord = record

                tmpRecord = type(outRecord)(outRecord) # copy record
                tmpRecord.remove(tmpRecord.indexOf('payStatus'))
                id = db.insertOrUpdate(table, tmpRecord)
                record.setValue(idFieldName, toVariant(id))
                idList.append(id)
                self.saveDependence(idx, id)

            filter = [table[masterIdFieldName].eq(masterId),
                      'NOT ('+table[idFieldName].inlist(idList)+')']
            if self._filter:
                filter.append(self._filter)
            db.deleteRecord(table, filter)


    def getEmptyRecord(self, sceneId=None, personId=None):
        eventEditor = QObject.parent(self)
        personId = personId if personId else eventEditor.getSuggestedPersonId()
        assistantId = eventEditor.getAssistantId() if self.hasAssistant and personId and personId == eventEditor.personId else None
        result = CInDocTableModel.getEmptyRecord(self)
        result.setValue('person_id',     toVariant(personId))
        result.setValue('assistant_id',  toVariant(assistantId))
        result.setValue('scene_id',      toVariant(sceneId if sceneId else self.getDefaultSceneId()))
        if not getEventKeepVisitParity(QObject.parent(self).eventTypeId):
            visitTypeId = self.getDefaultVisitTypeId()
        else:
            visitTypeId = self.getLastVisitTypeId()
        result.setValue('visitType_id',  toVariant(visitTypeId))
        CEventTypeDescription.get(eventEditor.eventTypeId).mapPlannedInspectionSpecialityIdToServiceId = {}
        result.setValue('service_id',    toVariant(self.getServiceId(result)))
        result.setValue('finance_id',    self.getFinanceId())
        return result


    def getLastVisitTypeId(self):
        if self.items():
            return forceRef(self.items()[len(self.items())-1].value('visitType_id'))
        return self.getDefaultVisitTypeId()


    def payStatus(self, row):
        if 0 <= row < len(self.items()):
            return forceInt(self.items()[row].value('payStatus'))
        else:
            return 0


    def getServiceId(self, record):
        if self.items():
            prevServiceId = forceRef(self.items()[-1].value('service_id'))
        else:
            prevServiceId = None
        eventEditor = QObject.parent(self)
        eventTypeId = eventEditor.eventTypeId
        if getIsDayStationary(eventTypeId) and prevServiceId:
            return prevServiceId
        else:
            return self.getExactServiceId(record)


    def getServiceIdEx(self, record):
        return self.getExactServiceId(record)


    def setData(self, index, value, role=Qt.EditRole):
        column = index.column()
        row = index.row()
        visitId = forceRef(self.items()[row].value('id')) if 0 <= row < len(self.items()) else None
        eventId = forceRef(self.items()[row].value('event_id')) if 0 <= row < len(self.items()) else None
        if not self.canChangeVisit(self.payStatus(row), visitId, eventId):
            return False
        dateColIndex = self.getColIndex('date')
        if column in (dateColIndex, ) and not variantEq(forceDateTime(self.data(index, role)), forceDateTime(value)):
            result = CInDocTableModel.setData(self, index, value, role)
            if result:
                item = self.items()[row]
                item.setValue('date', toVariant(value))
                self.emitCellChanged(row, self.getColIndex('date')) # дата
            return result
        if not variantEq(self.data(index, role), value):
            personColIndex    = self.getColIndex('person_id')
            sceneColIndex     = self.getColIndex('scene_id')
            visitTypeColIndex = self.getColIndex('visitType_id')
            if column == personColIndex: # врач
                eventEditor = QObject.parent(self)
                personId = forceRef(value)
                if not eventEditor.checkClientAttendanceEE(personId):
                    return False
            if column in (personColIndex, sceneColIndex): # врач, место или тип
                result = CInDocTableModel.setData(self, index, value, role)
                if result:
                    item = self.items()[row]
                    item.setValue('service_id', toVariant(self.getServiceIdEx(item)))
                    self.emitCellChanged(row, self.getColIndex('service_id')) # услуга
                return result
            if column in (visitTypeColIndex, ): # тип
                if not getEventKeepVisitParity(QObject.parent(self).eventTypeId):
                    result = CInDocTableModel.setData(self, index, value, role)
                    if result:
                        item = self.items()[row]
                        item.setValue('service_id', toVariant(self.getServiceIdEx(item)))
                        self.emitCellChanged(row, self.getColIndex('service_id')) # услуга
                    return result
                else:
                    result = True
                    for rowLocal, item in enumerate(self.items()):
                        if forceRef(item.value('visitType_id')) != forceRef(value):
                            result = CInDocTableModel.setData(self, self.index(rowLocal, column), value, role)
                            if result:
                                item.setValue('service_id', toVariant(self.getServiceIdEx(item)))
                                self.emitCellChanged(rowLocal, self.getColIndex('service_id')) # услуга
                    return result
            else:
                return CInDocTableModel.setData(self, index, value, role)
        else:
            return True


    def getDefaultSceneId(self):
        if self.defaultSceneId is None:
            if self.tryFindDefaultSceneId:
                eventEditor = QObject.parent(self)
                self.defaultSceneId = getEventSceneId(eventEditor.eventTypeId)
                if not self.defaultSceneId:
                    self.defaultSceneId = forceRef(QtGui.qApp.db.translate(rbScene, 'code', '1', 'id'))
                self.tryFindDefaultSceneId = False
        return self.defaultSceneId


    def setDefaultVisitTypeId(self, visitTypeId):
        self.defaultVisitTypeId = visitTypeId
        if visitTypeId is None:
            self.tryFindDefaultVisitTypeId = True


    def getDefaultVisitTypeId(self):
        if self.defaultVisitTypeId is None:
            if self.tryFindDefaultVisitTypeId:
                self.defaultVisitTypeId = forceRef(QtGui.qApp.db.translate(rbVisitType, 'code', '', 'id'))
                self.tryFindDefaultVisitTypeId = False
        return self.defaultVisitTypeId


    def getExactServiceId(self, record):
        eventEditor = QObject.parent(self)
        eventTypeId     = eventEditor.eventTypeId
        diagnosisServiceId = eventEditor.getModelFinalDiagnostics().diagnosisServiceId()
        eventServiceId  = eventEditor.eventServiceId
        personId        = forceRef(record.value('person_id'))
        specialityId    = eventEditor.getPersonSpecialityId(personId)
        personServiceId = eventEditor.getPersonServiceId(personId)
        visitTypeId     = record.value('visitType_id')
        sceneId         = record.value('scene_id')
        serviceId       = getExactServiceId(diagnosisServiceId, eventServiceId, personServiceId, eventTypeId, visitTypeId, sceneId, specialityId, eventEditor.clientSex, eventEditor.clientAge)
        return toVariant(serviceId)


    def getFinanceId(self):
        eventEditor = QObject.parent(self)
        financeId = eventEditor.getVisitFinanceId()
        return toVariant(financeId)


    def setFinanceId(self, financeId):
        for item in self.items():
            item.setValue('finance_id', financeId)
        self.reset()


    def addAbsentPersons(self, personIdList, eventDate = None):
        eventEditor = QObject.parent(self)
        eventTypeId     = eventEditor.eventTypeId
        showTime = getEventShowTime(eventTypeId)
        showVisitTime = getEventShowVisitTime(eventTypeId)
        for item in self.items():
            personId = forceRef(item.value('person_id'))
            if personId in personIdList:
                personIdList.remove(personId)
        for personId in personIdList:
            item = self.getEmptyRecord(personId=personId)
            if showTime and showVisitTime:
                date = eventDate if isinstance(eventDate, QDateTime) else QDateTime.currentDateTime()
            else:
                eventDateVisit = eventDate.date() if isinstance(eventDate, QDateTime) else eventDate
                date = eventDateVisit if eventDateVisit else QDate.currentDate()
            item.setValue('date',  toVariant(date))
            self.items().append(item)
        if personIdList:
            self.reset()


    def updatePersonAndService(self):
        personId = QObject.parent(self).personId
        for row, item in enumerate(self.items()):
            item.setValue('person_id', toVariant(personId))
            item.setValue('service_id', self.getExactServiceId(item))
            self.emitCellChanged(row, self.getColIndex('service_id')) # услуга
            item.setValue('finance_id', self.getFinanceId())
            self.emitCellChanged(row, self.getColIndex('finance_id')) # тип финансирования


    def isExposed(self, row):
        if 0 <= row < len(self.items()):
            visitId = forceRef(self.items()[row].value('id')) if 0 <= row < len(self.items()) else None
            eventId = forceRef(self.items()[row].value('event_id')) if 0 <= row < len(self.items()) else None
            return not self.canChangeVisit(self.payStatus(row), visitId, eventId)
        return False


    def canChangeVisit(self, payStatus, visitId, eventId):
        if not payStatus and visitId and eventId:
            db = QtGui.qApp.db
            tableVisit = db.table('Visit')
            cond = [ tableVisit['event_id'].eq(eventId),
                     tableVisit['id'].eq(visitId),
                     tableVisit['payStatus'].ne(0),
                     tableVisit['deleted'].eq(0)
                   ]
            record = db.getRecordEx(tableVisit, [tableVisit['payStatus']], where=cond)
            payStatus = forceInt(record.value('payStatus')) if record else 0
        if payStatus and not QtGui.qApp.userHasRight(urEditAfterInvoicingEvent):
            return False
        return True


class CDentitionVisitsModel(CEventVisitsModel):
    def __init__(self, parent):
        CEventVisitsModel.__init__(self, parent)


    def getEmptyRecord(self, sceneId=None, personId=None):
        eventEditor = QObject.parent(self)
        personId = personId if personId else eventEditor.getSuggestedPersonId()
        assistantId = eventEditor.getAssistantId() if self.hasAssistant and personId and personId == eventEditor.personId else None
        result = CInDocTableModel.getEmptyRecord(self)
        result.setValue('person_id',     toVariant(personId))
        result.setValue('assistant_id',  toVariant(assistantId))
        result.setValue('scene_id',      toVariant(sceneId if sceneId else self.getDefaultSceneId()))
        result.setValue('visitType_id',  toVariant(self.getDefaultVisitTypeId()))
        CEventTypeDescription.get(eventEditor.eventTypeId).mapPlannedInspectionSpecialityIdToServiceId = {}
        result.setValue('service_id',    toVariant(self.getServiceId(result)))
        result.setValue('finance_id',    self.getFinanceId())
        return result


    def setData(self, index, value, role=Qt.EditRole):
        column = index.column()
        row = index.row()
        visitId = forceRef(self.items()[row].value('id')) if 0 <= row < len(self.items()) else None
        eventId = forceRef(self.items()[row].value('event_id')) if 0 <= row < len(self.items()) else None
        if not self.canChangeVisit(self.payStatus(row), visitId, eventId):
            return False
        dateColIndex = self.getColIndex('date')
        if column in (dateColIndex, ) and not variantEq(forceDateTime(self.data(index, role)), forceDateTime(value)):
            dateOld = None
            if row >= 0 and len(self.items()) > row:
                item = self.items()[row]
                dateOld = forceDateTime(item.value('date'))
                personId = forceRef(item.value('person_id'))
                eventId = forceRef(item.value('event_id'))
                visitId = forceRef(item.value('id'))
            result = CInDocTableModel.setData(self, index, value, role)
            if result:
                item = self.items()[row]
                if dateOld is None:
                    dateOld = forceDateTime(item.value('date'))
                    personId = forceRef(item.value('person_id'))
                    eventId = forceRef(item.value('event_id'))
                    visitId = forceRef(item.value('id'))
                item.setValue('date', toVariant(value))
                self.emitCellChanged(row, self.getColIndex('date')) # дата
                rowDent = self.updateActionDentitionDate(dateOld, personId, eventId, visitId, 1, forceDateTime(value))
                self.updateActionDentitionDate(dateOld, personId, eventId, visitId, 0, forceDateTime(value), rowDent)
            return result
        if not variantEq(self.data(index, role), value):
            personColIndex    = self.getColIndex('person_id')
            sceneColIndex     = self.getColIndex('scene_id')
            visitTypeColIndex = self.getColIndex('visitType_id')
            personIdOld = None
            if column == personColIndex: # врач
                eventEditor = QObject.parent(self)
                if row >= 0 and len(self.items()) > row:
                    item = self.items()[row]
                    personIdOld = forceRef(item.value('person_id'))
                    date = forceDateTime(item.value('date'))
                    eventId = forceRef(item.value('event_id'))
                    visitId = forceRef(item.value('id'))
                personId = forceRef(value)
                if not eventEditor.checkClientAttendanceEE(personId):
                    return False
            if column in (personColIndex, sceneColIndex, visitTypeColIndex): # врач, место или тип
                result = CInDocTableModel.setData(self, index, value, role)
                if result:
                    item = self.items()[row]
                    if column == personColIndex: # врач
                        if personIdOld is None:
                            personIdOld = forceRef(item.value('person_id'))
                            date = forceDateTime(item.value('date'))
                            eventId = forceRef(item.value('event_id'))
                            visitId = forceRef(item.value('id'))
                        rowDent = self.updateActionDentitionPerson(date, personIdOld, eventId, visitId, 1, personId)
                        self.updateActionDentitionPerson(date, personIdOld, eventId, visitId, 0, personId, rowDent)
                    item.setValue('service_id', toVariant(self.getServiceIdEx(item)))
                    self.emitCellChanged(row, self.getColIndex('service_id')) # услуга
                    if  getEventKeepVisitParity(QObject.parent(self).eventTypeId):
                        for rowLocal, item in enumerate(self.items()):
                            if forceRef(item.value('visitType_id')) != forceRef(value):
                                result = CInDocTableModel.setData(self, self.index(rowLocal, column), value, role)
                                item.setValue('service_id', toVariant(self.getServiceIdEx(item)))
                                self.emitCellChanged(row, self.getColIndex('service_id')) 
                return result
            else:
                return CInDocTableModel.setData(self, index, value, role)
        else:
            return True


    def updateActionDentitionDate(self, date, personId, eventId, visitId, dentType, value, row=None):
        eventEditor = QObject.parent(self)
        if not eventId:
            eventId = eventEditor.itemId()
        if dentType:
            record, action = eventEditor.actionDentitionList.pop((date.toPyDateTime(), personId, eventId), (None, None))
        else:
            record, action = eventEditor.actionParodentiumList.pop((date.toPyDateTime(), personId, eventId), (None, None))
        if not action:
            record, action = eventEditor.addActionTypeDentition(date, personId, eventId, dentType)
        else:
            record = action.getRecord() if action else None
            if record:
                record.setValue('directionDate', toVariant(value))
                record.setValue('begDate', toVariant(value))
                record.setValue('endDate', toVariant(value))
                record.setValue('person_id', toVariant(personId))
                record.setValue('visit_id', toVariant(visitId))
                record.setValue('event_id', toVariant(eventId))
            if dentType:
                eventEditor.actionDentitionList[(value.toPyDateTime(), personId, eventId)] = (record, action)
                row = eventEditor.modelClientDentitionHistory.updateDentitionHistoryItems(record, action, date, personId, eventId)
            else:
                eventEditor.actionParodentiumList[(value.toPyDateTime(), personId, eventId)] = (record, action)
                eventEditor.modelClientDentitionHistory.updateParadentiumHistoryItem(record, action, date, personId, eventId)
        eventEditor.modelClientDentitionHistory.reset()
        return row


    def updateActionDentitionPerson(self, date, personId, eventId, visitId, dentType, value, row=None):
        eventEditor = QObject.parent(self)
        if not eventId:
            eventId = eventEditor.itemId()
        if dentType:
            record, action = eventEditor.actionDentitionList.pop((date.toPyDateTime(), personId, eventId), (None, None))
        else:
            record, action = eventEditor.actionParodentiumList.pop((date.toPyDateTime(), personId, eventId), (None, None))
        if not action:
            record, action = eventEditor.addActionTypeDentition(date, personId, eventId, dentType)
        else:
            record = action.getRecord() if action else None
            if record:
                record.setValue('directionDate', toVariant(date))
                record.setValue('begDate', toVariant(date))
                record.setValue('endDate', toVariant(date))
                record.setValue('person_id', toVariant(value))
                record.setValue('visit_id', toVariant(visitId))
                record.setValue('event_id', toVariant(eventId))
            if dentType:
                eventEditor.actionDentitionList[(date.toPyDateTime(), value, eventId)] = (record, action)
                row = eventEditor.modelClientDentitionHistory.updateDentitionHistoryItems(record, action, date, personId, eventId)
            else:
                eventEditor.actionParodentiumList[(date.toPyDateTime(), value, eventId)] = (record, action)
                eventEditor.modelClientDentitionHistory.updateParadentiumHistoryItem(record, action, date, personId, eventId)
        eventEditor.modelClientDentitionHistory.reset()
        return row


    def saveItems(self, masterId):
        if self._items is not None:
            eventEditor = QObject.parent(self)
            db = QtGui.qApp.db
            table = self._table
            tableAction = db.table('Action')
            masterId = toVariant(masterId)
            masterIdFieldName = self._masterIdFieldName
            idFieldName = self._idFieldName
            idList = []
            actionIdList = []
            for idx, record in enumerate(self._items):
                record.setValue(masterIdFieldName, masterId)
                if self._idxFieldName:
                    record.setValue(self._idxFieldName, toVariant(idx))
                if self._extColsPresent:
                    outRecord = self.removeExtCols(record)
                else:
                    outRecord = record
                id = db.insertOrUpdate(table, outRecord)
                record.setValue(idFieldName, toVariant(id))
                idList.append(id)
                self.saveDependence(idx, id)

                personId = forceRef(outRecord.value('person_id'))
                date = forceDateTime(outRecord.value('date'))
                eventId = eventEditor.itemId()

                if not eventId:
                    record, action = eventEditor.actionDentitionList.pop((date.toPyDateTime(), personId, eventId), (None, None))
                else:
                    record, action = eventEditor.actionDentitionList.get((date.toPyDateTime(), personId, eventId), (None, None))
                if action:
                    action._record = self.removeActionExtCols(record)
                    actionRecord = action.getRecord()
                    actionRecord.setValue('visit_id', toVariant(id))
                    _id = action.save(masterId)
                    actionIdList.append(_id)
                    # для обновления данных в модели при нажатии кнопки "применить"
                    for fieldName in ['id', 'createDatetime', 'createPerson_id', 'modifyDatetime', 'modifyPerson_id', 'expose']:
                        record.setValue(fieldName, toVariant(action._record.value(fieldName)))
                    if not eventId:
                        eventEditor.actionDentitionList[(date.toPyDateTime(), personId, forceRef(masterId))] = (actionRecord, action)

                if not eventId:
                    record, action = eventEditor.actionParodentiumList.pop((date.toPyDateTime(), personId, eventId), (None, None))
                else:
                    record, action = eventEditor.actionParodentiumList.get((date.toPyDateTime(), personId, eventId), (None, None))
                if action:
                    action._record = self.removeActionExtCols(record)
                    actionRecord = action.getRecord()
                    actionRecord.setValue('visit_id', toVariant(id))
                    _id = action.save(masterId)
                    actionIdList.append(_id)
                    # для обновления данных в модели при нажатии кнопки "применить"
                    for fieldName in ['id', 'createDatetime', 'createPerson_id', 'modifyDatetime', 'modifyPerson_id', 'expose']:
                        record.setValue(fieldName, toVariant(action._record.value(fieldName)))
                    if not eventId:
                        eventEditor.actionParodentiumList[(date.toPyDateTime(), personId, forceRef(masterId))] = (actionRecord, action)

            filterAction = [tableAction[masterIdFieldName].eq(masterId),
                            'NOT ('+tableAction[idFieldName].inlist(actionIdList)+')',
                            tableAction['visit_id'].isNotNull()
                           ]
            db.deleteRecord(tableAction, filterAction)

            filter = [table[masterIdFieldName].eq(masterId),
                      'NOT ('+table[idFieldName].inlist(idList)+')']
            if self._filter:
                filter.append(self._filter)
            db.deleteRecord(table, filter)

    def removeActionExtCols(self, srcRecord):
        db = QtGui.qApp.db
        table = db.table('Action')
        record = table.newRecord()
        for i in xrange(record.count()):
            fieldName = record.fieldName(i)
            record.setValue(fieldName, srcRecord.value(fieldName))
        record._dirty = srcRecord._dirty
        return record
