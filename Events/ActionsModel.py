# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2023 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt, QAbstractTableModel, QModelIndex, QVariant, SIGNAL, QDate
from Events.ActionRelations.Groups import CRelationsProxyModelGroup

from library.InDocTable import CRBInDocTableCol, CEnumInDocTableCol, CIntInDocTableCol, CDateInDocTableCol, CFloatInDocTableCol, CInDocTableCol, forcePyType
from library.Utils import (
    forceDate, forceDouble, forceInt, forceRef, forceString, toVariant, getDentitionActionTypeId,
    forceDateTime, forceStringEx, forceDateTime, trim, ActionTypeServiceMixin)

from Events.Action import CAction, CActionType, CActionTypeCache, getActionDefaultAmountEx, getActionDuration
from Events.ActionStatus                import CActionStatus
from Events.ActionProperty import CActionPropertyValueTypeRegistry
from Events.ExecutionPlan.Groups        import CActionExecutionPlanGroup, CExecutionPlanProxyModelGroup
from Events.ExecutionPlan.ExecutionPlan import CActionExecutionPlan, CActionExecutionPlanItem
from Events.Utils import getActionTypeIdListByClass, getEventMedicalAidKindId, getLfFormIdList
from Resources.JobTicketStatus          import CJobTicketStatus
from RefBooks.ActionTypeGroup.RBActionTypeGroupEditor import CSmnnInDocTableCol, CLfFormInDocTableCol
from Stock.NomenclatureComboBox import CNomenclatureInDocTableCol
from library.blmodel.Query              import CQuery
from library.crbcombobox import CRBComboBox, CRBModelDataCache
from library.database                   import CSqlRecord

from Users.Rights import urAccessEditCentralizedAccounting


__all__ = [
            'CActionsModel',
            'getActionDefaultAmountEx',
            'CGroupActionsProxyModel',
            'CActionsModelEx',
            'CGroupActionsProxyModelEx'
          ]


class CActionRecordItem(object):
    def __init__(self, record, action):
        self._data = (record, action)

    @property
    def id(self):
        return self.action.getId()

    @property
    def record(self):
        return self._data[0]

    @property
    def action(self):
        return self._data[1]

    def __iter__(self):
        return iter(self._data)

    def __getitem__(self, index):
        return self._data[index]


class CActionsModel(QAbstractTableModel):

    __pyqtSignals__ = ('amountChanged(int)',
                      )

    def __init__(self, parent, actionTypeClass=None):
        QAbstractTableModel.__init__(self, parent)
        self.actionTypeClass = None
        self.actionTypeIdList = []
        self.disabledActionTypeIdList = []
        self.col = CRBInDocTableCol(u'',  'actionType_id', 10, 'ActionType', addNone=True, preferredWidth=300)
        self._items = []   # each item is pair (record, action)
        self._loadedActionIdListWithEndDate = []
        self.eventEditor = None
        if actionTypeClass is not None:
            self.setActionTypeClass(actionTypeClass)
        self.idxFieldName = 'idx'  # :( для обеспечения возможности перемещения строк.
        self.table = QtGui.qApp.db.table('Action')
        self.readOnly = False
        self.ttjForDeleteIdList = []
        self.cachedFreeJobTicket = []
        self.cachedFreeJobTicketActionProperty = []
        self.actionIdForMarkDeleted = []


    def setReadOnly(self, value):
        self.readOnly = value


    def getReadOnly(self):
        return self.readOnly


    def setActionTypeClass(self, actionTypeClass):
        self.actionTypeClass = actionTypeClass
        self.actionTypeIdList = getActionTypeIdListByClass(actionTypeClass)
        self.col.filter = 'class=%d' % actionTypeClass

    def items(self):
        return self._items


    def updatePersonId(self, oldPersonId, newPersonId):
        pass
#        def replacePerson(record, field):
#            if forceRef(record.value(field)) == oldPersonId:
#                record.setValue(field, toVariant(newPersonId))
#
#        if oldPersonId and newPersonId and oldPersonId != newPersonId:
#            for item in self._items:
#                record = item[0]
##                replacePerson(record, 'setPerson_id')
#                replacePerson(record, 'person_id')


    def emitAmountChanged(self, row):
        self.emit(SIGNAL('amountChanged(int)'), row)


    def updateActionsAmount(self):  # по изменению в событии
        for row, item in enumerate(self._items):
            record, action = item
            actionTypeId = forceRef(record.value('actionType_id'))
            if actionTypeId:
                actionType = CActionTypeCache.getById(actionTypeId)
                if actionType.amountEvaluation in (CActionType.eventVisitCount,
                                                   CActionType.eventDurationWithFiveDayWorking,
                                                   CActionType.eventDurationWithSixDayWorking,
                                                   CActionType.eventDurationWithSevenDayWorking):
                    prevValue = forceDouble(record.value('amount'))
                    value = float(self.getDefaultAmountEx(actionType, record, action))
                    if prevValue != value:
                        record.setValue('amount', toVariant(value))
                        self.emitRowsChanged(row, row)
                        self.emitAmountChanged(row)
                        self.emitActionsUpdated(['amount'])

                # TT 1012 "Синхронизировать даты действия с датами события"
                if actionType.defaultDirectionDate == CActionType.dddSyncEventBegDate:
                    prevDirectionDate = forceDateTime(record.value('directionDate'))
                    directionDate = forceDateTime(self.eventEditor.eventSetDateTime)
                    if prevDirectionDate != directionDate:
                        record.setValue('directionDate', toVariant(directionDate))
                        self.emitRowsChanged(row, row)
                        self.emitActionsUpdated(['directionDate'])
                elif actionType.defaultDirectionDate == CActionType.dddSyncEventEndDate:
                    prevDirectionDate = forceDateTime(record.value('directionDate'))
                    directionDate = forceDateTime(self.eventEditor.getExecDateTime())
                    if prevDirectionDate != directionDate:
                        record.setValue('directionDate', toVariant(directionDate))
                        self.emitRowsChanged(row, row)
                        self.emitActionsUpdated(['directionDate'])

                if actionType.defaultBegDate == CActionType.dbdSyncEventBegDate:
                    prevBegDate = forceDateTime(record.value('begDate'))
                    begDate = forceDateTime(self.eventEditor.eventSetDateTime)
                    if prevBegDate != begDate:
                        record.setValue('begDate', toVariant(begDate))
                        self.emitRowsChanged(row, row)
                        self.emitActionsUpdated(['begDate'])
                elif actionType.defaultBegDate == CActionType.dbdSyncEventEndDate:
                    prevBegDate = forceDateTime(record.value('begDate'))
                    begDate = forceDateTime(self.eventEditor.getExecDateTime())
                    if prevBegDate != begDate:
                        record.setValue('begDate', toVariant(begDate))
                        self.emitRowsChanged(row, row)
                        self.emitActionsUpdated(['begDate'])

                if actionType.defaultEndDate == CActionType.dedSyncEventBegDate:
                    prevEndDate = forceDateTime(record.value('endDate'))
                    endDate = forceDateTime(self.eventEditor.eventSetDateTime)
                    if prevEndDate != endDate:
                        record.setValue('endDate', toVariant(endDate))
                        record.setValue('status', toVariant(CActionStatus.finished if not endDate.isNull() else CActionStatus.started))
                        self.emitRowsChanged(row, row)
                        self.emitActionsUpdated(['endDate','status'])
                elif actionType.defaultEndDate == CActionType.dedSyncEventEndDate:
                    prevEndDate = forceDateTime(record.value('endDate'))
                    endDate = forceDateTime(self.eventEditor.getExecDateTime())
                    if prevEndDate != endDate:
                        record.setValue('endDate', toVariant(endDate))
                        record.setValue('status', toVariant(CActionStatus.finished if not endDate.isNull() else CActionStatus.started))
                        self.emitRowsChanged(row, row)
                        self.emitActionsUpdated(['endDate','status'])


    def updateActionAmount(self, row):  # по изменению в самом действии
        record, action = self._items[row]
        actionTypeId = forceRef(record.value('actionType_id'))
        if actionTypeId:
            actionType = CActionTypeCache.getById(actionTypeId)
            if actionType.amountEvaluation in (CActionType.eventVisitCount,
                                               CActionType.eventDurationWithFiveDayWorking,
                                               CActionType.eventDurationWithSixDayWorking,
                                               CActionType.eventDurationWithSevenDayWorking,
                                               CActionType.actionDurationWithFiveDayWorking,
                                               CActionType.actionDurationWithSixDayWorking,
                                               CActionType.actionDurationWithSevenDayWorking,
                                               CActionType.actionFilledPropsCount,
                                               CActionType.actionAssignedPropsCount,
                                               CActionType.actionDurationFact):
                prevValue = forceDouble(record.value('amount'))
                value = float(self.getDefaultAmountEx(actionType, record, action))
                if prevValue != value:
                    record.setValue('amount', toVariant(value))
                    self.emitRowsChanged(row, row)
                    self.emitAmountChanged(row)


    def disableActionType(self, actionTypeId):
        self.disabledActionTypeIdList.append(actionTypeId)


    def getActionDuration(self, record, weekProfile):
        return getActionDuration(self.eventEditor.eventTypeId, record, weekProfile)


    def getDefaultAmountEx(self, actionType, record, action):
        return getActionDefaultAmountEx(self.eventEditor, actionType, record, action)


    def getDefaultAmount(self, actionTypeId, record, action):
        if actionTypeId:
            actionType = CActionTypeCache.getById(actionTypeId)
            result = self.getDefaultAmountEx(actionType, record, action)
        else:
            result = 0
        return result


    def columnCount(self, index=None, *args, **kwargs):
        return 1


    def rowCount(self, index=None, *args, **kwargs):
        return len(self._items)+1


    def flags(self, index):
        if self.readOnly:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        row = index.row()
#        if self.isLocked(row):
#            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if row < len(self._items):
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if self.isExposed(row):
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable


    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return QVariant(u'Наименование')
        return QVariant()


    def data(self, index, role=Qt.DisplayRole):
        row = index.row()
        if row < len(self._items):
            if role == Qt.EditRole:
                record = self._items[row][0]
                return record.value('actionType_id')
            if role == Qt.DisplayRole:
                record = self._items[row][0]
                outName = forceString(record.value('specifiedName'))
                actionTypeId = forceRef(record.value('actionType_id'))
                actionBegDate = forceString(forceDate(record.value('begDate')))
                if actionTypeId:
                    actionType = CActionTypeCache.getById(actionTypeId)
                    if actionType:
                        outName = actionType.name + ' '+outName if outName else actionType.name
                        # showBegDate = self.showBegDate(actionTypeId)
                        if actionType.showBegDate:
                            outName = outName + ', ' + actionBegDate
                return QVariant(outName)
            if role == Qt.StatusTipRole or role == Qt.ToolTipRole:
                record, action = self._items[row]
                specifiedName = forceString(record.value('specifiedName'))
                actionTypeId = forceRef(record.value('actionType_id'))
                actionType = CActionTypeCache.getById(actionTypeId) if actionTypeId else None
                actionName = (actionType.code + ': ' + actionType.name) if actionType else ''
                actionBegDate = forceString(forceDate(record.value('begDate')))
                if actionTypeId and actionType:
                    showBegDate = actionType.showBegDate  # self.showBegDate(actionTypeId)
                    if role == Qt.StatusTipRole:
                        actionName = actionName + u' ' + specifiedName
                    if showBegDate:
                        actionName = actionName + u', ' + actionBegDate

                prevActionId = forceRef(record.value('prevAction_id'))
                if action and ((action.trailerIdx > 0 and not bool(action.trailerIdx & 1)) or prevActionId):
                    if not prevActionId:
                        actionName += u' связано с действием ...'
                    else:
                        prevAction = CAction.getActionById(prevActionId)
                        if prevAction:
                            prevActionType = prevAction.getType()
                            actionName += u' связано с действием ' + (prevActionType.code + ': ' + prevActionType.name) if prevActionType else ''
                return QVariant(actionName)
            if role == Qt.ForegroundRole:
                record, action = self._items[row]
                if action and action.getType().isRequiredCoordination and record.isNull('coordDate'):
                    return QVariant(QtGui.QColor(255, 0, 0))
        return QVariant()


    def setData(self, index, value, role=Qt.EditRole, presetAction=None):  # presetAction - это ошибка!
        if role == Qt.EditRole:
            row = index.row()
            actionTypeId = forceRef(value)
            if actionTypeId and not (self.checkMaxOccursLimit(actionTypeId) and
                                     self.checkMovingNoLeaved(actionTypeId) and
                                     self.checkMovingAfterReceived(actionTypeId) and
                                     self.checkLeavedAfterMoving(actionTypeId) and
                                     self.checkLeavedAfterMovingDate(actionTypeId)):
                return False
            if row == len(self._items):  # Это ошибка!
                if actionTypeId is None:
                    return False

                self.addRow(presetAction=presetAction)
            if not presetAction:
                record = self._items[row][0]
                action = self.getFilledAction(record, actionTypeId)
            else:
                record = presetAction.getRecord()
                action = presetAction
            if action.findNomenclaturePropertyValue():
                self.applyPropertyDependencies(action)
            self._items[row] = CActionRecordItem(record, action)
            if not presetAction:
                record.setValue('amount', toVariant(self.getDefaultAmount(actionTypeId, record, action)))
            self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)
            self.emitItemsCountChanged()
            actionsSummaryRowRow = self.eventEditor.translate2ActionsSummaryRow(self, row)
            if actionsSummaryRowRow is not None:
                self.eventEditor.onActionChanged(actionsSummaryRowRow)
            return True
    
    
    def applyPropertyDependencies(self, action):
        propertyList = action.getProperties()
        for actionProperty in propertyList:
            propertyType = actionProperty.type()
            if propertyType.isNomenclatureValueType():
                property = action.getPropertyById(propertyType.id)
                property.preApplyDependents(action)
                property.setValue(propertyType.convertQVariantToPyValue(action.findNomenclaturePropertyValue()))
                if property.isActionNameSpecifier():
                    action.updateSpecifiedName()
                property.applyDependents(action)
                if propertyType.isJobTicketValueType():
                    action.setPlannedEndDateOnJobTicketChanged(property.getValue())


    def appendOuterAction(self, action):
        item = (action.getRecord(), action)
        self._items.append(item)
        index = QModelIndex()
        cnt = len(self._items)
        self.beginInsertRows(index, cnt, cnt)
        self.insertRows(cnt, 1, index)
        self.endInsertRows()
        self.emitItemsCountChanged()



    def emitItemsCountChanged(self):
        self.emit(SIGNAL('itemsCountChanged()'))


    def addRow(self, actionTypeId=None, amount=None, financeId=None, contractId=None, presetAction=None):
        if not presetAction:
            record = QtGui.qApp.db.table('Action').newRecord()
            action = self.getFilledAction(record, actionTypeId, amount, financeId, contractId)
            item = CActionRecordItem(record, action)
        else:
            item = CActionRecordItem(presetAction.getRecord(), presetAction)
        self._items.append(item)
        index = QModelIndex()
        cnt = len(self._items)
        self.beginInsertRows(index, cnt, cnt)
        self.insertRows(cnt, 1, index)
        self.endInsertRows()
        self.emitItemsCountChanged()
        return cnt-1


    def getFilledAction(self, record, actionTypeId, amount=None, financeId=None, contractId=None, orgStructureId=None, **kwargs):
        return CAction.getFilledAction(self.eventEditor, record, actionTypeId, amount, financeId, contractId, orgStructureId=orgStructureId)


    def delVisit(self, record):
        eventEditor = self.eventEditor
        if not hasattr(eventEditor, 'tblVisits'):
            return
        visitId = forceRef(record.value('visit_id'))
        visitList = eventEditor.modelActionsSummary.visitList
        visitRecord = visitList.get(record)
        visitsModel = eventEditor.modelVisits
        visitList   = visitsModel.items()
        visitRow = None

        if visitRecord:
            visitRow = visitList.index(visitRecord)

        if visitId and not visitRow:
            for i, record in enumerate(visitList):
                id = forceInt(record.value('id'))
                if id == visitId:
                    visitRow = i
        if visitRow is not None:
            visitsModel.removeRows(visitRow, 1)


    def getClientReservationToActions(self):
        clientReservationToAction = {}
        if self.eventEditor:
            for record, action in self.eventEditor.getActionsModelsItemsList():
                actionId = forceRef(record.value('id'))
                if actionId and action:
                    if action.nomenclatureClientReservation is not None:
                        reservationId = forceRef(action.nomenclatureClientReservation._record.value('id'))
                        reservationToActionLine = clientReservationToAction.get(reservationId, [])
                        if actionId and actionId not in reservationToActionLine:
                            reservationToActionLine.append(actionId)
                            clientReservationToAction[reservationId] = reservationToActionLine
        return clientReservationToAction


    def removeRows(self, row, count, parentIndex=QModelIndex(), *args, **kwargs):
        if 0 <= row and row + count <= len(self._items):
            if not self.checkDirectionDeleted(row, count):
                return False
            for i in xrange(count):
                if self.isLocked(row+i):
                    return False
                record, action = self._items[row]
                actionTypeId = forceRef(record.value('actionType_id'))
                if actionTypeId and not (self.checkReceivedDeleted(actionTypeId) and
                                         self.checkMovingDeleted(actionTypeId, row)):
                    return False
                self.delVisit(record)
                ttjId = forceRef(record.value('takenTissueJournal_id'))
                if ttjId:
                    self.ttjForDeleteIdList.append(ttjId)
                if action:
                    for property in action._propertiesById.itervalues():
                        propertyType = property.type()
                        if propertyType.isJobTicketValueType():
                            jobTicketId = action[propertyType.name]
                            if jobTicketId:
                                if jobTicketId not in self.cachedFreeJobTicket:
                                    self.cachedFreeJobTicket.append(jobTicketId)
                                propertyRecord = property.getRecord()
                                propertyId = forceRef(propertyRecord.value('id')) if propertyRecord else None
                                if propertyId and propertyId not in self.cachedFreeJobTicketActionProperty:
                                    self.cachedFreeJobTicketActionProperty.append(propertyId)
                    actionId = forceRef(record.value('id'))
                    if action.nomenclatureClientReservation is not None and not actionId:
                        action.nomenclatureClientReservation.cancelEx(self.getClientReservationToActions())
                        action.nomenclatureClientReservation = None
                    if (action.nomenclatureExpense is not None and not actionId) or (action.nomenclatureExpense is not None and actionId and action.getNomenclatureExpenseChange()):
                        action.nomenclatureExpense.cancel()
                        action.nomenclatureExpense = None
                if action.getId():
                    self.actionIdForMarkDeleted.append(action.getId())
            self.beginRemoveRows(parentIndex, row, row+count-1)
            del self._items[row:row+count]
            self.emit(SIGNAL('removeRows()'))
            self.endRemoveRows()
            return True
        else:
            return False


    def loadItems(self, items):
        items.sort(key=lambda x: forceInt(x.record.value('idx')))
        self._items = items

        for item in self._items:
            record = item.record
            if forceDate(record.value('endDate')):
                self._loadedActionIdListWithEndDate.append(forceRef(record.value('id')))
        self.reset()

    def loadedActionIdListWithEndDate(self):
        return self._loadedActionIdListWithEndDate


    def saveItems(self, eventId):
        db = QtGui.qApp.db
        table = db.table('Action')
        idList = []
        dentActionTypeId, parodentActionTypeId = getDentitionActionTypeId()
        actionTypeDentIdList = []
        if dentActionTypeId:
            actionTypeDentIdList.append(dentActionTypeId)
        if parodentActionTypeId:
            actionTypeDentIdList.append(parodentActionTypeId)
        for row, item in enumerate(self._items):
            record, action = item
            if action:
                if self.table.newRecord().count() != record.count():
                    action._record = self.removeExtCols(record)
                self.eventEditor.getMKBValueForActionDuringSaving(record, action)
                if hasattr(self.eventEditor, 'modelActionsSummary'):
                    visitList = self.eventEditor.modelActionsSummary.visitList
                    visitRecord = visitList.get(record)
                    if visitRecord:
                        visitId = forceRef(visitRecord.value('id'))
                        if visitId:
                            action._record.setValue('visit_id', visitId)
                            record.setValue('visit_id', toVariant(visitId))
                if not actionTypeDentIdList or forceRef(record.value('actionType_id')) not in actionTypeDentIdList:
                    _id = None
                    if action.trailerIdx > 0:
                        if bool(action.trailerIdx & 1):  # нечет
                            _id = action.save(eventId, len(idList))
                            # для обновления данных в модели при нажатии кнопки "применить"
                            for fieldName in ['id', 'createDatetime', 'createPerson_id', 'modifyDatetime',
                                              'modifyPerson_id', 'expose']:
                                record.setValue(fieldName, toVariant(action._record.value(fieldName)))
                            idList.append(_id)
                        else:  # чет
                            prevActionId = self.eventEditor.trailerIdList.get(action.trailerIdx-1, None)
                            if prevActionId:
                                action._record.setValue('prevAction_id', toVariant(prevActionId))
                                _id = action.save(eventId, len(idList))
                                # для обновления данных в модели при нажатии кнопки "применить"
                                for fieldName in ['id', 'createDatetime', 'createPerson_id', 'modifyDatetime',
                                                  'modifyPerson_id', 'expose']:
                                    record.setValue(fieldName, toVariant(action._record.value(fieldName)))
                                idList.append(_id)
                            else:
                                self.eventEditor.trailerActions.append(action)
                    else:
                        _id = action.save(eventId, len(idList))
                        # для обновления данных в модели при нажатии кнопки "применить"
                        for fieldName in ['id', 'createDatetime', 'createPerson_id', 'modifyDatetime', 'modifyPerson_id', 'expose']:
                            record.setValue(fieldName, toVariant(action._record.value(fieldName)))
                        idList.append(_id)
                    if _id and action.nomenclatureExpense:
                        if action and action.actionType().isDoesNotInvolveExecutionCourse and forceInt(action.getRecord().value('status')) != CActionStatus.canceled:
                            if action.executionPlanManager.executionPlan:
                                currentExecutionPlanItem = action.executionPlanManager._currentItem
                                action.executionPlanManager.setCurrentItemIndex(action.executionPlanManager.executionPlan.items.index(currentExecutionPlanItem))
                                nextExecutionPlanItem = action.executionPlanManager.getNextItem()
                                while nextExecutionPlanItem:
                                    action.executionPlanManager.setCurrentItemIndex(action.executionPlanManager.executionPlan.items.index(nextExecutionPlanItem))
                                    nextExecutionPlanItem = action.executionPlanManager.getNextItem()
                                if not nextExecutionPlanItem and not action.executionPlanManager.hasItemsToDo():
                                    if action.nomenclatureClientReservation:
                                        action.nomenclatureClientReservation.cancel()
                                action.executionPlanManager.setCurrentItemIndex(action.executionPlanManager.executionPlan.items.index(currentExecutionPlanItem))
                            else:
                                nextExecutionPlanItem = action.executionPlanManager.getNextItem()
                                if not nextExecutionPlanItem and action.executionPlanManager.currentItem and not action.executionPlanManager.hasItemsToDo():
                                    if action.nomenclatureClientReservation:
                                        action.nomenclatureClientReservation.cancel()
                                elif action and action.actionType().isDoesNotInvolveExecutionCourse and forceInt(action.getRecord().value('status')) == CActionStatus.finished:
                                    if action.nomenclatureClientReservation:
                                        action.nomenclatureClientReservation.cancel()
                        else:
                            nextExecutionPlanItem = action.executionPlanManager.getNextItem()
                            if not nextExecutionPlanItem and not action.executionPlanManager.hasItemsToDo():
                                if action.nomenclatureClientReservation:
                                    action.nomenclatureClientReservation.cancel()
        if QtGui.qApp.controlNomenclatureExpense():
            message = u''
            tableNomenclature = db.table('rbNomenclature')
            actionTypeIdExpense = []
            for recordExpense, actionExpense in self._items:
                status = forceInt(actionExpense.getRecord().value('status'))
                if actionExpense.nomenclatureExpense:
                    if not actionExpense._actionType.generateAfterEventExecDate or bool(actionExpense._actionType.generateAfterEventExecDate and actionExpense.event.execDate):
                        if actionExpense.nomenclatureExpense and status == CActionStatus.finished and (
                                actionExpense.nomenclatureExpense.getStockMotionId() or actionExpense.nomenclatureExpense.stockMotionItems()):
                            if actionExpense.nomenclatureExpense._noAvialableQnt and actionExpense._actionType.getNomenclatureRecordList():
                                actionTypeId = actionExpense._actionType.id
                                if actionTypeId and actionTypeId not in actionTypeIdExpense:
                                    actionTypeIdExpense.append(actionTypeId)
                                    nomenclatureLine = actionExpense.nomenclatureExpense._noAvialableQnt.get(actionTypeId, [])
                                    if nomenclatureLine:
                                        if actionExpense.nomenclatureExpense.selectNomenclatureIdList:
                                            nomenclatureLine = list(set(nomenclatureLine) & set(actionExpense.nomenclatureExpense.selectNomenclatureIdList))
                                        nomenclatureName = u''
                                        records = db.getRecordList(tableNomenclature, [tableNomenclature['name']], [tableNomenclature['id'].inlist(nomenclatureLine)], order = tableNomenclature['name'].name())
                                        for recordNomenclature in records:
                                            nomenclatureName += u'\n' + forceString(recordNomenclature.value('name'))
                                        message += u'''Действие типа %s.\nОтсутствуют ЛСиИМН: %s!\n''' % (actionExpense._actionType.name, nomenclatureName)
            if message:
                QtGui.QMessageBox().warning(None,
                                            u'Внимание!',
                                            message,
                                            QtGui.QMessageBox.Ok,
                                            QtGui.QMessageBox.Ok)
        cond = [table['event_id'].eq(eventId), table['deleted'].eq(0), 'NOT ('+table['id'].inlist(idList)+')']
        if self.actionTypeClass is not None:
            cond.append('EXISTS(SELECT NULL FROM ActionType WHERE ActionType.id = Action.actionType_id AND ActionType.`class` = {0})'.format(self.actionTypeClass))

        if self.actionIdForMarkDeleted:
            tableActionProperty = db.table('ActionProperty')
            filter = [tableActionProperty['action_id'].inlist(self.actionIdForMarkDeleted), tableActionProperty['deleted'].eq(0)]
            db.markRecordsDeleted(tableActionProperty, filter)

            tableActionExecutionPlan = db.table('Action_ExecutionPlan')
            filter = [tableActionExecutionPlan['master_id'].inlist(self.actionIdForMarkDeleted), tableActionExecutionPlan['deleted'].eq(0)]
            db.markRecordsDeleted(tableActionExecutionPlan, filter)

            tableStockMotion = db.table('StockMotion')
            tableStockMotionItem = db.table('StockMotion_Item')
            tableActionNR = db.table('Action_NomenclatureReservation')
            filterActionNR = [tableActionNR['action_id'].inlist(self.actionIdForMarkDeleted)]
            if idList:
                filterActionNR.append(tableActionNR['action_id'].notInlist(idList))
            reservationIdList = db.getDistinctIdList(tableActionNR, [tableActionNR['reservation_id']], filterActionNR)
            if reservationIdList:
                filterSINR = [tableStockMotionItem['master_id'].inlist(reservationIdList),
                              tableStockMotionItem['deleted'].eq(0)]
                db.deleteRecord(tableStockMotionItem, filterSINR)
                filterSNR = [tableStockMotion['id'].inlist(reservationIdList), tableStockMotion['deleted'].eq(0)]
                db.deleteRecord(tableStockMotion, filterSNR)
                db.deleteRecord(tableActionNR, filterActionNR)

            filter = [table['id'].inlist(self.actionIdForMarkDeleted), table['deleted'].eq(0)]
            stockMotionIdList = db.getDistinctIdList(table, [table['stockMotion_id']], filter)
            if stockMotionIdList:
                filter = [tableStockMotionItem['master_id'].inlist(stockMotionIdList), tableStockMotionItem['deleted'].eq(0)]
                db.deleteRecord(tableStockMotionItem, filter)
                filter = [tableStockMotion['id'].inlist(stockMotionIdList), tableStockMotion['deleted'].eq(0)]
                db.deleteRecord(tableStockMotion, filter)

            filter = [table['id'].inlist(self.actionIdForMarkDeleted), table['deleted'].eq(0)]
            db.markRecordsDeleted(table, filter)
        if self.ttjForDeleteIdList:
            tableTTJ = db.table('TakenTissueJournal')
            filter = [tableTTJ['id'].inlist(self.ttjForDeleteIdList), tableTTJ['deleted'].eq(0)]
            db.deleteRecord(tableTTJ, filter)
        if self.cachedFreeJobTicketActionProperty:
            tableAPJT = db.table('ActionProperty_Job_Ticket')
            filter = [tableAPJT['id'].inlist(self.cachedFreeJobTicketActionProperty)]
            db.deleteRecord(tableAPJT, filter)
        if self.cachedFreeJobTicket:
            tableJobTicket = db.table('Job_Ticket')
            records = db.getRecordList(tableJobTicket, '*', [tableJobTicket['id'].inlist(self.cachedFreeJobTicket), tableJobTicket['deleted'].eq(0)])
            for recordJobTicket in records:
                recordJobTicket.setValue('status', toVariant(CJobTicketStatus.wait))
                recordJobTicket.setValue('begDateTime', toVariant(None))
                recordJobTicket.setValue('endDateTime', toVariant(None))
                recordJobTicket.setValue('orgStructure_id', toVariant(None))
                db.updateRecord(tableJobTicket, recordJobTicket)


    def removeExtCols(self, srcRecord):
        record = self.table.newRecord()
        for i in xrange(record.count()):
            record.setValue(i, srcRecord.value(record.fieldName(i)))
        if type(srcRecord) == CSqlRecord:
            record._dirty = srcRecord._dirty
        return record


    def isLocked(self, row):
        if 0 <= row < len(self._items):
            action = self._items[row][1]
            if action:
                return action.isLocked()
        return False


    def isCanDeletedByUser(self, row):
        if 0 <= row < len(self._items):
            action = self._items[row][1]
            if action:
                return action.isCanDeletedByUser()
        return True


    def isLockedOrExposed(self, row):
        db = QtGui.qApp.db
        if 0 <= row < len(self._items):
            recod, action = self._items[row]
            if action.getId():
                table = db.table('Account_Item')
                cond  = [table['deleted'].eq(0)]
                cond.append(table['action_id'].eq(action.getId()))
                cond.append(table['refuseType_id'].isNotNull())
                cond.append(table['reexposeItem_id'].isNull())
                if db.getRecordList(table, 'id', cond):
                    return action and action.isLocked()
            return forceInt(recod.value('payStatus')) != 0 or (action and action.isLocked())
        return False


    def isExposed(self, row):
        if 0 <= row < len(self._items):
            record, action = self._items[row]
            if action:
                return action.isExposed()
        return False


    def actionTypeId(self, row):
        if 0 <= row < len(self._items):
            return forceInt(self._items[row][0].value('actionType_id'))
        else:
            return None


    def payStatus(self, row):
        if 0 <= row < len(self._items):
            return forceInt(self._items[row][0].value('payStatus'))
        else:
            return 0


#    def changeActionType(self, row, newActionTypeId):
#        self._items[row].setValue('actionType_id', QVariant(newActionTypeId))
#        self.emitCellChanged(row, 0)


    def removeRowEx(self, row):
        self.removeRows(row, 1)


    def upRow(self, row):
        if 0 < row < len(self._items):
            self._items[row-1], self._items[row] = self._items[row], self._items[row-1]
            self.emitRowsChanged(row-1, row)
            return True
        else:
            return False


    def downRow(self, row):
        if 0 <= row < len(self._items)-1:
            self._items[row+1], self._items[row] = self._items[row], self._items[row+1]
            self.emitRowsChanged(row, row+1)
            return True
        else:
            return False


    def checkMaxOccursLimit(self, actionTypeId):
        actionType = CActionTypeCache.getById(actionTypeId)
        count = 0
        for record, action in self._items:
            if action and action.getType() == actionType:
                count += 1
        result = actionType.checkMaxOccursLimit(count, True)
        return result


    def checkReceivedDeleted(self, actionTypeId):
        result = True
        actionType = CActionTypeCache.getById(actionTypeId)
        if u'received' in actionType.flatCode.lower():
            for record, action in self._items:
                if action:
                    actionTypeItem = action.getType()
                    if actionTypeItem and (u'moving' in actionTypeItem.flatCode.lower()):
                        return actionType.checkReceivedMovingLeaved(u'Нельзя удалить действие "Поступление" если есть "Движение"')
                    if actionTypeItem and (u'leaved' in actionTypeItem.flatCode.lower()):
                        return actionType.checkReceivedMovingLeaved(u'Нельзя удалить действие "Поступление" если есть "Выписка"')
        return result


    def checkMovingDeleted(self, actionTypeId, rowCurrent):
        result = True
        actionType = CActionTypeCache.getById(actionTypeId)
        if u'moving' in actionType.flatCode.lower():
            for row, item in enumerate(self.items()):
                record, action = item
                if action:
                    actionTypeItem = action.getType()
                    if actionTypeItem and (u'leaved' in actionTypeItem.flatCode.lower()):
                        return actionType.checkReceivedMovingLeaved(u'Нельзя удалить действие "Движение" если есть "Выписка"')
                    elif row > rowCurrent and actionTypeItem and (u'moving' in actionTypeItem.flatCode.lower()):
                       return actionType.checkReceivedMovingLeaved(u'Нельзя удалить действие "Движение" если после него есть "Движение"')
        return result


    def checkMovingNoLeaved(self, actionTypeId):
        result = True
        actionType = CActionTypeCache.getById(actionTypeId)
        if u'moving' in actionType.flatCode.lower():
            for record, action in self._items:
                if action:
                    actionTypeItem = action.getType()
                    if actionTypeItem and (u'leaved' in actionTypeItem.flatCode.lower()):
                        return actionType.checkReceivedMovingLeaved(u'Действие "Движение" не должно применяться после действия "Выписка"')
                    elif actionTypeItem and (u'moving' in actionTypeItem.flatCode.lower()):
                        if not forceDate(record.value('endDate')):
                            return actionType.checkReceivedMovingLeaved(u'Действие "Движение" не может появится при наличии не законченного "Движение"')
        return result


    def checkMovingAfterReceived(self, actionTypeId):
        actionType = CActionTypeCache.getById(actionTypeId)
        if u'moving' in actionType.flatCode.lower():
            for record, action in self._items:
                if action:
                    actionTypeItem = action.getType()
                    if actionTypeItem and (u'received' in actionTypeItem.flatCode.lower()):
                        if not forceDate(record.value('endDate')):
                            return actionType.checkReceivedMovingLeaved(u'Действие "Движение" не может появится при наличии не законченного действия "Поступление"')
                        return True
            return actionType.checkReceivedMovingLeaved(u'Действие "Движение" не должно применяться пока нет действия "Поступление"')
        return True


    def checkLeavedAfterMoving(self, actionTypeId):
        actionType = CActionTypeCache.getById(actionTypeId)
        if u'leaved' in actionType.flatCode.lower():
            for record, action in self._items:
                if action:
                    actionTypeItem = action.getType()
                    if actionTypeItem and (u'moving' in actionTypeItem.flatCode.lower()):
                        return True
            return actionType.checkReceivedMovingLeaved(u'Действие "Выписка" не должно применяться пока нет действия "Движение"')
        return True


    def checkLeavedAfterMovingDate(self, actionTypeId):
        actionType = CActionTypeCache.getById(actionTypeId)
        if u'leaved' in actionType.flatCode.lower():
            for record, action in self._items:
                if action:
                    actionTypeItem = action.getType()
                    if actionTypeItem and (u'moving' in actionTypeItem.flatCode.lower()):
                        if not forceDate(record.value('endDate')):
                            return actionType.checkReceivedMovingLeaved(u'Действие "Выписка" не может появится при наличии не законченного действия "Движение"')
        return True


    def emitRowsChanged(self, row1, row2):
        index1 = self.index(row1, 0)
        index2 = self.index(row2, self.columnCount() - 1)
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index1, index2)
    
    
    def emitActionsUpdated(self, updatedList = []):
        self.emit(SIGNAL('onUpdateActionsAmount(PyQt_PyObject)'), updatedList)


    def reloadItem(self, row):
        db = QtGui.qApp.db
        table = db.table('Action')
        if 0 <= row < len(self._items):
            item = self._items[row]
            action = item.action
            actionId = action.getId()
            newRecord = db.getRecord(table, '*', actionId)
            action.setRecord(newRecord)
            item._data = (newRecord, action)
            self.emitRowsChanged(row, row)
    

    def checkDirectionDeleted(self, row, count):
        for record, action in self._items[row:row+count]:
            actionTypeId = forceRef(record.value('actionType_id'))
            actionType = CActionTypeCache.getById(actionTypeId)
            if (actionType.flatCode.lower() == u'consultationDirection'.lower()
                and u'Идентификатор направления' in actionType._propertiesByName
                and u'Причина аннулирования' in actionType._propertiesByName
                and action[u'Идентификатор направления'] is not None
                and action[u'Идентификатор направления'] != ''
                and action[u'Причина аннулирования'] is None
            ):
                QtGui.QMessageBox.critical(
                    self.eventEditor,
                    u'Произошла ошибка',
                    u'Перед удалением направления необходимо его аннулировать!',
                    QtGui.QMessageBox.Close
                )
                return False
        return True


_emptyValue = object()
_nomenclatureIndex = 1


class CGroups(object):
    def __init__(self, model):
        self._mapProxyRow2Group = {}
        self._groups = []
        self.idx = None
        self._model = model
        self.proxyRow = 0

    def upGroup(self, proxyRow, group):
        if group not in self._groups:
            return False

        index = self._groups.index(group)
        if index == 0:
            return False

        upperGroup = self._groups[index-1]
        upperGroup.proxyRow = proxyRow
        upperGroup.increaseItemsIdx(group.itemsCount(), upperGroup)
        group.idx = upperGroup.idx
        group.decreaseItemsIdx(upperGroup.itemsCount(), upperGroup)

        self._groups[index], self._groups[index - 1] = upperGroup, group

        self._resetModelNewItemsOrder()

        return True

    def getGroupProxyRow(self, group):
        result = 0
        for targetGroup in self._groups:
            if group is targetGroup:
                return result
            result += len(group)
        return -1

    def downGroup(self, proxyRow, group):
        if group not in self._groups:
            return False

        index = self._groups.index(group)
        if index == len(self._groups) - 1:
            return False

        downerGroup = self._groups[index + 1]
        downerGroup.proxyRow = proxyRow
        downerGroup.decreaseItemsIdx(group.itemsCount(), downerGroup)
        group.idx = downerGroup.idx

        group.increaseItemsIdx(downerGroup.itemsCount(), downerGroup)

        self._groups[index], self._groups[index + 1] = downerGroup, group

        self._resetModelNewItemsOrder()

        return True


    def _setNewOrder(self, sortKey):
        self._groups.sort(key=lambda x: x.getSortValue(sortKey))
        for idx, group in enumerate(self._groups):
            group.idx = idx
            for item in group.items:
                record = item.record
                record.setValue('idx', toVariant(idx))


    def _resetModelNewItemsOrder(self):
        model = self._model.model()

        items = {}
        for group in self._groups:
            for item in group:
                record = item[0]
                items.setdefault(forceInt(record.value('idx')), []).append(item)

        newItemsList = []
        for idx in sorted(items.keys()):
            newItemsList.extend(items[idx])

        model.items()[:] = newItemsList

    def clear(self):
        self._mapProxyRow2Group.clear()
        self._groups = []

    @property
    def groupsIterator(self):
        return iter(self._groups)

    def __iter__(self):
        return iter(self._model.model().items())

    def __len__(self):
        return self.rowsCount()

    def __getitem__(self, proxyRow):
        if proxyRow < 0:
            modelRowsCount = self._model.rowCount() - 1
            proxyRow += modelRowsCount
        return self.getItem(proxyRow)

    def delete(self, group):
        for proxyRow in group.proxyRows:
            group.deleteProxyRow(proxyRow, self._model.model())
            del self._mapProxyRow2Group[proxyRow]
        self._groups.remove(group)

    def newGroup(self, actionTypeId = None):
        group = CRelationsProxyModelGroup(self._model) if bool(CActionTypeCache.getById(actionTypeId).getRelatedActionTypes()) else CExecutionPlanProxyModelGroup(self._model)
        self._groups.append(group)
        return group

    def addGroup(self, group):
        self._groups.append(group)

    def mapGroup(self, proxyRow, group):
        self._mapProxyRow2Group[proxyRow] = group

    def getItem(self, proxyRow):
        return self._mapProxyRow2Group[proxyRow].getItem(proxyRow)

    @property
    def groupsCount(self):
        return len(self._groups)

    def rowsCount(self):
        return sum([len(g) for g in self._groups])


class CGroupActionsProxyModel(QtGui.QProxyModel, ActionTypeServiceMixin):
    __groupingAllowed__ = True

    __pyqtSignals__ = (
        'amountChanged(int)',
        'itemsCountChanged()'
    )

    def __init__(self, parent):
        actionModel = CActionsModel(parent)

        QtGui.QProxyModel.__init__(self, parent)
        QtGui.QProxyModel.setModel(self, actionModel)
        ActionTypeServiceMixin.__init__(self)

        self._parent = parent
        self._actionModel = actionModel

        self._groups = CGroups(self)
        self._mapProxyRow2Group = {}
        self._mapModelRow2ProxyRow = {}

        boldFont = QtGui.QFont()
        boldFont.setWeight(QtGui.QFont.Bold)

        self._qBoldFont = QVariant(boldFont)

        boldFont.setItalic(QtGui.QFont.StyleItalic)
        self._qBoldItalicFont = QVariant(boldFont)

        italicFont = QtGui.QFont()
        italicFont.setItalic(QtGui.QFont.StyleItalic)
        self._qItalicFont = QVariant(italicFont)

        self._groupItemsShift = u' ' * 3

        self.connect(self._actionModel, SIGNAL('dataChanged(QModelIndex, QModelIndex)'), self._emitDataChanged)
        self.connect(self._actionModel, SIGNAL('amountChanged(int)'), self._emitAmountChanged)
        self.connect(self._actionModel, SIGNAL('itemsCountChanged()'), self._emitItemsCountChanged)
        self.connect(self._actionModel, SIGNAL('onUpdateActionsAmount(PyQt_PyObject)'), self._emitActionsUpdated)

    @property
    def eventEditor(self):
        return self._actionModel.eventEditor

    @eventEditor.setter
    def eventEditor(self, eventEditor):
        self._actionModel.eventEditor = eventEditor

    def _emitDataChanged(self, index1, index2):
        mr1, mr2 = index1.row(), index2.row()
        if mr1 not in self._mapModelRow2ProxyRow or mr2 not in self._mapModelRow2ProxyRow:
            return
        r1, r2 = self._mapModelRow2ProxyRow[mr1], self._mapModelRow2ProxyRow[mr2]
        i1, i2 = self.index(r1, 0), self.index(r2, 0)
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), i1, i2)
    
    def _emitActionsUpdated(self, updatedList = []):
        self.emit(SIGNAL('onUpdateActionsAmount(PyQt_PyObject)'), updatedList)

    def _emitAmountChanged(self, row):
        row = self._mapModelRow2ProxyRow[row]
        self.emit(SIGNAL('amountChanged(int)'), row)

    def _emitItemsCountChanged(self):
        self.emit(SIGNAL('itemsCountChanged()'))

    def setModel(self, model):
        # Это довольно специфическое решение. Запретим задавать целевую модель. Она задается в конструкторе.
        raise AttributeError()

    def __getattr__(self, attributeName):
        return getattr(self._actionModel, attributeName)

    def setData(self, index, value, group=None, *args, **kwargs):
        proxyRow = index.row()
        if 'related' in kwargs.keys():
            ifRelated = kwargs.pop('related')
        else:
            ifRelated = True

        if proxyRow not in self._mapProxyRow2Group and (proxyRow == len(self._mapModelRow2ProxyRow) or proxyRow == len(self._mapProxyRow2Group)):
            modelRow = len(self._actionModel.items())

        elif proxyRow not in self._mapProxyRow2Group:
            return False

        else:
            group = self._mapProxyRow2Group[proxyRow]
            modelRow = group.getModelRow(proxyRow, self._actionModel)

        index = self._actionModel.index(modelRow, 0)

        self._actionModel.blockSignals(True)

        result = self._actionModel.setData(index, value, *args, **kwargs)

        self._actionModel.blockSignals(False)

        if result:
            self._addNewItem(group)
            index = self.index(proxyRow, 0)
            self.emit(SIGNAL('rowsInserted(QModelIndex, int, int)'), index, proxyRow, proxyRow+1)
            self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)
            self.emit(SIGNAL('onAddNewAction(int)'), modelRow)
            self.emitRowIndexActivated(proxyRow)
            if ifRelated:
                self.addRelatedActions(forceRef(value), index)

        return result


    def addRelatedActions(self, actionType_id, index=None):
        from collections import OrderedDict
        actionTypes = CActionTypeCache.getById(actionType_id).getRelatedActionTypes()
        order = CActionTypeCache.getById(actionType_id).getRelatedActionTypesOrder()
        actionTypes = OrderedDict(sorted(actionTypes.items(), key=lambda x: order.get(x[0], 0)))
        group = None
        if not index:
            index = self.index(self.rowCount()-2, 0)
        for actionType, isRequired in actionTypes.items():
            if isRequired:
                group = self._mapProxyRow2Group[index.row()]
                self.setData(self.index(index.row()+1, 0), actionType, self._mapProxyRow2Group[index.row()])
        if group and not group.expanded:
            self.touchGrouping(index.row())
   
    
    def loadItems(self, eventId):
        self._actionModel._items = []
        self._items.clear()
        self._groups.clear()
        self._remapRows()
        self._actionModel.loadItems(eventId)
        self._group()

    def addGroup(self, actionTypeId, modelRow, item, mapActionTypeGroups=None):
        group = self._groups.newGroup(actionTypeId)
        self._mapProxyRow2Group[self._groups.groupsCount - 1] = group

        group.addItem(modelRow, item)

        if mapActionTypeGroups is not None:
            mapActionTypeGroups.setdefault(actionTypeId, []).append(group)

        return group

    def _group(self):
        actionTypeGroups = {}
        unadded = []
        for modelRow, item in enumerate(self._actionModel.items()):
            record, action = item

            actionTypeId = action.getType().id

            if action.getMasterId():
                unadded.append((modelRow, item, False))
                continue
            
            if actionTypeId not in actionTypeGroups:
                self.addGroup(actionTypeId, modelRow, item, actionTypeGroups)
                continue

            added = False

            for group in actionTypeGroups[actionTypeId]:
                if isinstance(group, CRelationsProxyModelGroup):
                    continue
                if group.addItem(modelRow, item):
                    added = True
                    break
            if added:
                continue

            self.addGroup(actionTypeId, modelRow, item, actionTypeGroups)      
        for modelRow, item, added in unadded:
            for key, groups in actionTypeGroups.items():
                for group in groups:
                    if isinstance(group, CRelationsProxyModelGroup): 
                        record, action = item 
                        if group.firstItem.id == action.getMasterId() or (not group.firstItem.id and id(group.firstItem) == action.getMasterId()):
                            group.addItem(modelRow, item)
                            added = True
                    if not group.expanded and len(group.items)>1:
                        group.setExpanded(not group.expanded)
                        self._resetData()
                    if added:
                        continue
            if not added:
                self.addGroup(actionTypeId, modelRow, item, actionTypeGroups)  
        self._remapRows()

    def _remapRows(self):
        self._mapProxyRow2Group.clear()
        self._mapModelRow2ProxyRow.clear()

        modelItems = self._actionModel.items()

        proxyRow = 0
        for group in self._groups.groupsIterator:
            group.resetMapping(self._actionModel)
            for item in group.items:
                group.mapRows(proxyRow, item)
                self._mapProxyRow2Group[proxyRow] = group
                self._groups.mapGroup(proxyRow, group)
                self._mapModelRow2ProxyRow[modelItems.index(item)] = proxyRow
                if group.expanded:
                    proxyRow += 1
            if not group.expanded:
                proxyRow += 1


    def data(self, index, role=Qt.DisplayRole):
        row = index.row()
        if row not in self._mapProxyRow2Group:
            return QVariant()

        group = self._mapProxyRow2Group[row]
        modelRow = group.getModelRow(row, self._actionModel)

        modelIndex = self._actionModel.index(modelRow, 0)

        isHeadItem = group.isHeadItem(row, self._actionModel)

        if role == Qt.DisplayRole and not isHeadItem:
            value = forceString(self._actionModel.data(modelIndex, role))
            return QVariant(self._groupItemsShift+value)

        elif role == Qt.FontRole:
            items = self._actionModel.items()
            if 0 <= row < len(items):
                record, action = items[row]
                if action and action.getType():
                    actionTypeId = action.getType().id
                    actionTypeCache = CActionTypeCache.getById(actionTypeId)
                    code = actionTypeCache.code
                    numService = actionTypeCache.nomenclativeServiceId
                    if not self.checkActionTypeService(actionTypeId, code, numService):
                        return self._qBoldItalicFont
                if isHeadItem and group.canBeGrouped():
                    if action and ((action.trailerIdx > 0 and not bool(action.trailerIdx & 1)) or forceRef(record.value('prevAction_id'))):
                        return self._qBoldItalicFont
                    return self._qBoldFont
                if action and ((action.trailerIdx > 0 and not bool(action.trailerIdx & 1)) or forceRef(record.value('prevAction_id'))):
                    return self._qItalicFont

        elif role == Qt.ToolTipRole:
            items = self._actionModel.items()
            if 0 <= row < len(items):
                record, action = items[row]
                if action and action.getType():
                    actionTypeId = action.getType().id
                    actionTypeCache = CActionTypeCache.getById(actionTypeId)
                    code = actionTypeCache.code
                    numService = actionTypeCache.nomenclativeServiceId
                    if not self.checkActionTypeService(actionTypeId, code, numService):
                        return u"Услуга в типе действия не является актуальной"

        return self._actionModel.data(modelIndex, role)

    def index(self, row, column, parent=QtCore.QModelIndex(), *args, **kwargs):
        return QtGui.QProxyModel.index(self, row, column, parent)

    def columnCount(self, index=None, *args, **kwargs):
        return 1

    def rowCount(self, index=None, *args, **kwargs):
        count = 1
        for group in self._groups.groupsIterator:
            count += len(group) if group.expanded else 1
        return count

    def canRowBeGrouped(self, proxyRow):
        if proxyRow not in self._mapProxyRow2Group:
            return False

        group = self._mapProxyRow2Group[proxyRow]
        return group.canBeGrouped()


    def removeRows(self, row, count, parentIndex=QModelIndex(), *args, **kwargs):
        if not (0 <=row and row+count <= self.rowCount()):
            return False

        for proxyRow in xrange(row, row+count):
            self._removeRow(proxyRow)

        return True

    def afterRowsDeleting(self):
        self._emitItemsCountChanged()

    def _removeRow(self, proxyRow, removeRelated = False, unbind = False):
        tabs = {}
        if hasattr(self.eventEditor, 'tabStatus'):
            tabs[0] = self.eventEditor.tabStatus
        if hasattr(self.eventEditor, 'tabDiagnostic'):
            tabs[1] = self.eventEditor.tabDiagnostic
        if hasattr(self.eventEditor, 'tabCure'):
            tabs[2] = self.eventEditor.tabCure
        if hasattr(self.eventEditor, 'tabMisc'):
            tabs[3] = self.eventEditor.tabMisc
        if not tabs:
            tabs = {0: self.eventEditor.tabActions,
                    1: self.eventEditor.tabActions,
                    2: self.eventEditor.tabActions,
                    3: self.eventEditor.tabActions}
        if proxyRow not in self._mapProxyRow2Group:
            return
        group = self._mapProxyRow2Group[proxyRow]
        if not group.expanded:
            self.touchGrouping(proxyRow)
        parentActionType = group.firstItem.action.getType()
        relatedActionTypes = CActionTypeCache.getById(parentActionType.id).getRelatedActionTypes()
        required = []
        for item in relatedActionTypes:
            relatedActionType = CActionTypeCache.getById(item)
            if parentActionType.class_ != relatedActionType.class_:
                required.append(relatedActionType.class_)
        required = set(required)
        if isinstance(group, CRelationsProxyModelGroup) and (len(group.items) > 1 or required) and group.getItem(proxyRow) == group.firstItem and not removeRelated and not unbind:
            res = QtGui.QMessageBox().warning(
                                            None,
                                            u'Внимание!',
                                            u"При удалении родительского действия удалятся и все подчиненные. Продолжить?",
                                            QtGui.QMessageBox.Ok|QtGui.QMessageBox.Cancel,
                                            QtGui.QMessageBox.Cancel)
            if res == QtGui.QMessageBox.Ok:
                for itemClass in required:
                    if itemClass in tabs.keys():
                        for item in tabs[itemClass].modelAPActions._groups.groupsIterator:
                            if item.firstItem.action.getMasterId() == group.firstItem.id:
                                tabs[itemClass].modelAPActions._removeRow(item._mapItem2Row[item.firstItem], removeRelated = True)
                for item in reversed(sorted(group.proxyRows[1:])):
                    self._removeRow(item, removeRelated = True) 
            else:
                return False
        modelRow = group.getModelRow(proxyRow, self._actionModel)    
        removed = self._actionModel.removeRow(modelRow)
        if removed:
            del self._mapModelRow2ProxyRow[modelRow]
            group.deleteProxyRow(proxyRow, self._actionModel)
            if not len(group):
                self._groups.delete(group)
            del self._mapProxyRow2Group[proxyRow]
            self._remapRows()
            self.reset()

    
    def _unbindRow(self, proxyRow):
        if proxyRow not in self._mapProxyRow2Group:
            return
        group = self._mapProxyRow2Group[proxyRow]
        if not group.expanded:
            self.touchGrouping(proxyRow)
        for item in reversed(sorted(group.proxyRows)):
            self._removeRow(item, removeRelated = True, unbind = True) 


    def showIdentificationInfo(self, proxyRow):
        if self._mapProxyRow2Group and proxyRow < len(self._mapProxyRow2Group):
            actionTypeId = self._mapProxyRow2Group[proxyRow].actionTypeId
            if actionTypeId:
                from library.IdentificationModel import identificationInfo
                identificationInfo(self._parent, actionTypeId, 'ActionType_Identification', 'ActionType')
    

    def touchGrouping(self, proxyRow):
        if self._mapProxyRow2Group and proxyRow < len(self._mapProxyRow2Group):
            group = self._mapProxyRow2Group[proxyRow]
            group.setExpanded(not group.expanded)
            self._resetData()

    def getExpandedByRow(self, proxyRow):
        if proxyRow not in self._mapProxyRow2Group:
            return None
        group = self._mapProxyRow2Group[proxyRow]
        return group.expanded

    @property
    def _items(self):
        return self._groups

    def items(self):
        return self._groups

    def _resetData(self, remap=True):
        if hasattr(self, 'beginResetModel'):
            self.beginResetModel()
        if remap:
            self._remapRows()
        # self.reset()
        if hasattr(self, 'endResetModel'):
            self.endResetModel()
        else:
            self.reset()


    def _addNewItem(self, group = None):
        newItem = self._actionModel.items()[-1]
        modelRow = len(self._actionModel.items()) - 1
        newRecord, newAction = newItem
        if not newAction:
            return None, None

        begDateTime = forceDateTime(newRecord.value('begDate'))
        if not begDateTime or not begDateTime.isValid():
            newRecord.setValue('begDate', toVariant(QtCore.QDateTime().currentDateTime()))

        actionTypeId = newItem[1].getType().id

        added = False

        if group:
            if isinstance(group, CRelationsProxyModelGroup) and not newAction.getMasterId():
                newAction.setMasterId(id(group.firstItem))
            group.addItem(modelRow, newItem)
        else:
            for group in self._groups.groupsIterator:
                if group.actionTypeId != actionTypeId or isinstance(group, CRelationsProxyModelGroup):
                    continue

                if group.addItem(modelRow, newItem):
                    added = True
                    break

            if not added:
                group = self.addGroup(actionTypeId, modelRow, newItem)
        self._resetData()

        return group, newItem

    def addRow(self, *args, **kwargs):
        if 'related' in kwargs.keys():
            ifRelated = kwargs.pop('related')
        else:
            ifRelated = True
        subgroup = None
        if 'subgroup' in kwargs.keys():
            subgroup = kwargs.pop('subgroup')
        result = self._actionModel.addRow(*args, **kwargs)
        group, _ = self._addNewItem(subgroup)
        self.emitRowIndexActivated(self._groups.getGroupProxyRow(group))
        if ifRelated: 
            self.addRelatedActions(args[0], index = None)
        return result


    def addNewGroup(self, group):
        result = self._actionModel.addRow(presetAction=group.isHeadItem.action)
        self._groups.addGroup(group)
        return result


    def emitRowIndexActivated(self, row):
        self.emit(SIGNAL("rowIndexActivated(int)"), row)

    def flags(self, index):
        proxyRow = index.row()

        if proxyRow not in self._mapProxyRow2Group and proxyRow == len(self._groups):
            modelRow = len(self._actionModel.items())

        elif proxyRow not in self._mapProxyRow2Group:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        else:
            group = self._mapProxyRow2Group[proxyRow]
            modelRow = group.getModelRow(proxyRow, self._actionModel)

        return self._actionModel.flags(self._actionModel.index(modelRow, 0))

    def upRow(self, proxyRow):
        if proxyRow not in self._mapProxyRow2Group:
            result = False

        else:
            group = self._mapProxyRow2Group[proxyRow]

            if group.canUpInGroup(proxyRow):
                result = group.upProxyRow(proxyRow)

            else:
                result = self._groups.upGroup(proxyRow, group)

        if result:
            self._remapRows()
            self.emitAllChanged()

        return result

    def downRow(self, proxyRow):
        if proxyRow not in self._mapProxyRow2Group:
            result = False

        else:
            group = self._mapProxyRow2Group[proxyRow]

            if group.canDownInGroup(proxyRow):
                result = group.downProxyRow(proxyRow)

            else:
                result = self._groups.downGroup(proxyRow, group)

        if result:
            self._remapRows()
            self.emitAllChanged()

        return result

    def emitAllChanged(self):
        index1 = self.index(0, 0)
        index2 = self.index(self.rowCount(), self.columnCount())
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index1, index2)

    def updateActionAmount(self, proxyRow):
        if proxyRow not in self._mapProxyRow2Group:
            return

        group = self._mapProxyRow2Group[proxyRow]
        modelRow = group.getModelRow(proxyRow, self._actionModel)
        self._actionModel.updateActionAmount(modelRow)

    def getFilledAction(self, newRecord, *args, **kwargs):
        plannedEndDate = directionDate = None
        saveDirectionDate = kwargs.pop('saveDirectionDates', False) and newRecord
        if saveDirectionDate:
            directionDate = forceDateTime(newRecord.value('directionDate'))
            plannedEndDate = forceDateTime(newRecord.value('plannedEndDate'))

        action = self._actionModel.getFilledAction(newRecord, *args, **kwargs)

        if saveDirectionDate:
            action.getRecord().setValue('directionDate', directionDate)
            action.getRecord().setValue('plannedEndDate', plannedEndDate)

        return action
    
    
    def addMasterIds(self):
        db = QtGui.qApp.db
        table = db.table('Action')
        for group in self._groups.groupsIterator:
            if isinstance(group, CRelationsProxyModelGroup):  
                ids = []
                for item in group.items:
                    if item != group.firstItem:
                        ids.append(item.id)
                        item.record.setValue('master_id', toVariant(group.firstItem.id))
                    item.record.setValue('id', toVariant(item.id))
                if ids:
                    db.updateRecords(table, 'master_id = {}'.format(group.firstItem.id), table['id'].inlist(ids))
        

    def saveItems(self, eventId):
        def _getEpItemsMap():
            epItems = {}
            for item in self._actionModel.items():
                action = item.action
                ep = action.getExecutionPlan()
                if not ep or not ep.id:
                    continue

                epItems.setdefault(ep.id, set()).update([i.id for i in ep.items if i.id])
            return epItems

        self._actionModel.saveItems(eventId)
        self.addMasterIds()

        newEpItemsMap = _getEpItemsMap()

        for epId, itemsIds in newEpItemsMap.items():
            itemsCond = [
                CActionExecutionPlanItem.masterId == epId
            ]
            if not itemsIds:
                CQuery.delete(CActionExecutionPlan, CActionExecutionPlan.id == epId)
            else:
                itemsCond.append(CActionExecutionPlanItem.id.notInlist(itemsIds))

            CQuery.delete(
                CActionExecutionPlanItem, itemsCond
            )




class CGroupActionsProxyModelEx(CGroupActionsProxyModel):
    __groupingAllowed__ = True

    __pyqtSignals__ = (
        'amountChanged(int)',
        'itemsCountChanged()'
    )


    def __init__(self, parent):
        actionModel = CActionsModelEx(parent)

        CGroupActionsProxyModel.__init__(self, parent)
        QtGui.QProxyModel.setModel(self, actionModel)

        self._parent = parent
        self._actionModel = actionModel

        self._groups = CGroups(self)
        self._mapProxyRow2Group = {}
        self._mapModelRow2ProxyRow = {}
        self._nomenclatureAnalogCache = {}

        boldFont = QtGui.QFont()
        boldFont.setWeight(QtGui.QFont.Bold)

        self._qBoldFont = QVariant(boldFont)

        italicFont = QtGui.QFont()
        italicFont.setItalic(QtGui.QFont.StyleItalic)
        self._qItalicFont = QVariant(italicFont)

        self._groupItemsShift = u' ' * 3

        self.connect(self._actionModel, SIGNAL('dataChanged(QModelIndex, QModelIndex)'), self._emitDataChanged)
        self.connect(self._actionModel, SIGNAL('amountChanged(int)'), self._emitAmountChanged)
        self.connect(self._actionModel, SIGNAL('itemsCountChanged()'), self._emitItemsCountChanged)
        self.connect(self._actionModel, SIGNAL('onUpdateActionsAmount(PyQt_PyObject)'), self._emitActionsUpdated)


    def columnCount(self, index=None):
        return len(self._actionModel._cols)


    def rowCount(self, index=None):
        count = 0
        for group in self._groups.groupsIterator:
            count += len(group) if group.expanded else 1
        return count

    
    def flags(self, index):
        row = index.row()
        proxyColumn = index.column()
        if row not in self._mapProxyRow2Group and row == len(self._groups):
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        elif row not in self._mapProxyRow2Group:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        else:
            group = self._mapProxyRow2Group[row]
            if group:
                proxyRow = group._mapProxyRow2ModelRow[row]
                action = group._mapRow2Item[proxyRow].action
                if not action:
                    return Qt.ItemIsEnabled | Qt.ItemIsSelectable
                if not action.executionPlanManager.hasItemsToDo():
                    return Qt.ItemIsEnabled | Qt.ItemIsSelectable
                record = group._mapRow2Item[proxyRow].record
                if not record:
                    return Qt.ItemIsEnabled | Qt.ItemIsSelectable
                status = forceInt(record.value('status')) if record else -1
                if status in (CActionStatus.started, CActionStatus.appointed) and QtGui.qApp.userHasRight(urAccessEditCentralizedAccounting) and proxyColumn in (self._actionModel.Col_Nomenclature, self._actionModel.Col_Doses):
                    return self._actionModel.flags(self._actionModel.index(proxyRow, proxyColumn))
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable
    

    def data(self, index, role=Qt.DisplayRole):
        row = index.row()
        if row not in self._mapProxyRow2Group:
            return QVariant()

        group = self._mapProxyRow2Group[row]
        modelRow = group.getModelRow(row, self._actionModel)

        modelIndex = self._actionModel.index(modelRow, index.column())

        #isHeadItem = group.isHeadItem(row, self._actionModel)

        #if role == Qt.DisplayRole and not isHeadItem:
        #    value = forceString(self._actionModel.data(modelIndex, role))
        #    return QVariant(self._groupItemsShift+value)

        #elif role == Qt.FontRole:
        #    items = self._actionModel.items()
        #    if 0<= row < len(items):
        #        record, action = items[row]
        #        if isHeadItem and group.canBeGrouped():
        #            if action and ((action.trailerIdx > 0 and not bool(action.trailerIdx & 1)) or forceRef(record.value('prevAction_id'))):
        #                self._qBoldFont.setItalic(QtGui.QFont.StyleItalic)
        #            return self._qBoldFont
        #        if action and ((action.trailerIdx > 0 and not bool(action.trailerIdx & 1)) or forceRef(record.value('prevAction_id'))):
        #            return self._qItalicFont

        return self._actionModel.data(modelIndex, role)


    def setData(self, index, value, *args, **kwargs):
        row = index.row()
        proxyColumn = index.column()
        if row not in self._mapProxyRow2Group and row == len(self._groups):
            modelRow = len(self._actionModel.items())
        elif row not in self._mapProxyRow2Group:
            return False
        else:
            group = self._mapProxyRow2Group[row]
            modelRow = group.getModelRow(row, self._actionModel)
        index = self._actionModel.index(modelRow, proxyColumn)
        if proxyColumn in (self._actionModel.Col_Nomenclature, self._actionModel.Col_Doses):
            items = self._actionModel.items()
            if 0<= row < len(items):
                group = self._mapProxyRow2Group[row]
                proxyRow = group._mapProxyRow2ModelRow[row]
                action = group._mapRow2Item[proxyRow].action
                record = group._mapRow2Item[proxyRow].record
                if not group or not action:
                    return False
                isExistsDoneByIndex = action.executionPlanManager.hasItemsToDo()
                if proxyColumn == self._actionModel.Col_Nomenclature and isExistsDoneByIndex:
                    newNomenclatureId = forceRef(value)
                    oldNomenclatureId = action.findNomenclaturePropertyValue()
                    if oldNomenclatureId != newNomenclatureId:
                        self._actionModel.blockSignals(True)
                        result = self._actionModel.setData(index, value, *args, **kwargs)
                        if not result:
                            return False
                        group.setIsDirty(newNomenclatureId and not oldNomenclatureId)
                        action.setNomenclaturePropertyValue(newNomenclatureId)
                        nomenclatureOldAnalogId = self.getNomenclatureAnalog(oldNomenclatureId) if oldNomenclatureId else None #0014428:0058806
                        nomenclatureAnalogId = self.getNomenclatureAnalog(newNomenclatureId) if newNomenclatureId else None
                        if nomenclatureOldAnalogId != nomenclatureAnalogId or not nomenclatureOldAnalogId or not nomenclatureAnalogId:
                            #if not action.getSmnnUUIDPropertyValue() or not action.getSmnnGrlsLfPropertyValue():
                                group = self.updateDosageNomenclatureByIndex(action, group)
                            #else:
                            #    action = self._setItemsNomenclature(action, group)
                            #    group = self.setNomenclatureInExists(action, group)
                        elif nomenclatureOldAnalogId and nomenclatureOldAnalogId == nomenclatureAnalogId:
                            action = self._setItemsNomenclature(action, group)
                            group = self.setNomenclatureInExists(action, group)
                        if not trim(action.findSignaPropertyValue()): #0011445:0056953:пункт 1
                            action.setSignaPropertyValue(self.getSignaToNomenclatureId(newNomenclatureId, action))
                            action.setSignaCommentPropertyValue(action.findSignaCommentTypePropertyText())
                        #action, group = self.updateSmnn_SmnnGrlslf(action, group, newNomenclatureId, oldNomenclatureId)
                        self._actionModel.blockSignals(False)
                        index = self.index(proxyRow, proxyColumn)
                        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)
                        #self.emitRowIndexActivated(proxyRow)
                        return True
                isNotExecutedItemByDate = action.executionPlanManager.hasItemsToDo()
                if proxyColumn == self._actionModel.Col_Doses and isNotExecutedItemByDate:
                    oldDosage = action.findDosagePropertyValue()
                    newDosage = forceDouble(value)
                    if oldDosage != newDosage:
                        self._actionModel.blockSignals(True)
                        result = self._actionModel.setData(index, value, *args, **kwargs)
                        if not result:
                            self._actionModel.blockSignals(False)
                            return False
                        begDate = forceDate(record.value('begDate'))
                        if begDate:
                            action.setDosagePropertyValue(newDosage)
                            group = self._setItemsDefaultToDateFirstItemDosesValueAndNomenclature(action, group, begDate)
                            if newDosage != oldDosage:
                                group = self.updateDosageToDateFirstItemInExists(index, group, newDosage, begDate)
                                group.updateSpecifiedName()
                        self._actionModel.blockSignals(False)
                        index = self.index(proxyRow, proxyColumn)
                        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)
                        #self.emitRowIndexActivated(proxyRow)
                        return True
        return False


    def setModelActionsProxyGroupExpanded(self):
        for row, group in self._mapProxyRow2Group.items():
            if not self.getExpandedByRow(row):
                group.setExpanded(not group.expanded)
                self._resetData()

    
    def getSignaToNomenclatureId(self, nomenclatureId, action):
        if nomenclatureId and action:
            db = QtGui.qApp.db
            table = db.table('rbNomenclature')
            tableUsingType = db.table('rbNomenclature_UsingType')
            tableRBUsingType = db.table('rbNomenclatureUsingType')
            queryTable = table.innerJoin(tableUsingType, tableUsingType['master_id'].eq(table['id']))
            queryTable = queryTable.innerJoin(tableRBUsingType, tableRBUsingType['id'].eq(tableUsingType['usingType_id']))
            record = db.getRecordEx(queryTable, [tableRBUsingType['id'].alias('usingTypeId'), tableRBUsingType['name'].alias('usingType')], [table['id'].eq(nomenclatureId)], order=tableUsingType['idx'].name())
            if action.isNomenclatureUsingTypeActionPropertyValueType():
                return forceRef(record.value('usingTypeId')) if record else None
            else:
                return forceString(record.value('usingType')) if record else u''
        return u''
        

    def updateDosageByIndex(self, index, group, dosage):
        if not index.isValid():
            return
        if group:
            group.setDosageInExists(dosage)

    
    def updateDosageToProcentByIndex(self, group, procent, change):
        if group:
            group.setDosageToProcentInExists(procent, change)
    
    
    def updateDosageToDateToProcentByIndex(self, group, procent, change, date):
        if group and date:
            group.setDosageToDateToProcentInExists(procent, change, date)
        return group
            

    def _setItemsDefaultDosesValueAndNomenclature(self, action, group):
        doses = action.findDosagePropertyValue()
        nomenclatureId = action.findNomenclaturePropertyValue()
        actionEP = group.headItem.action
        for epItem in actionEP.getExecutionPlan().items:
            if epItem.nomenclature:
                epItem.nomenclature.dosage = doses
                epItem.nomenclature.nomenclatureId = nomenclatureId
                nomenclatureItem = epItem.nomenclature
                nomenclatureItem.actionExecutionPlanItem = epItem
                epItem.setIsDirty(True)
        return group


    def setNomenclatureInExists(self, action, group):
        if action:
            nomenclatureId = action.findNomenclaturePropertyValue()
            group.setNomenclatureInExists(nomenclatureId)
        return group


    def _setItemsNomenclature(self, action, group):
        nomenclatureId = action.findNomenclaturePropertyValue()
        actionEP = group.headItem.action
        for epItem in actionEP.getExecutionPlan().items:
            if epItem.nomenclature and not epItem.executedDatetime:
                epItem.nomenclature.nomenclatureId = nomenclatureId
                nomenclatureItem = epItem.nomenclature
                nomenclatureItem.actionExecutionPlanItem = epItem
                epItem.setIsDirty(True)
        return action


    def updateDosageNomenclatureByIndex(self, action, group):
        if action and group:
            dosage = action.findDosagePropertyValue()
            nomenclatureId = action.findNomenclaturePropertyValue()
            group.setDosageNomenclatureInExists(dosage, nomenclatureId)
        return group


    def existsDoneByIndex(self, group, date):
        items = group.getItemsByDate(date)
        if not items:
            return False
        for item in items:
            if item.executedDatetime:
                return True
        return False

    
    def hasNotExecutedItemByDate(self, group, date):
        items = group.getItemsByDate(date)
        if not items:
            return False
        for item in items:
            if not item.executedDatetime:
                return True
        return False


    def getCalculationParamValueProperties(self, clientId):
        if not clientId:
            return {}
        valuePropertyToTemplateItems = {}
        propertyIdHeader = []
        db = QtGui.qApp.db
        tableMonitoring = db.table('Client_Monitoring')
        tableAPTemplate = db.table('ActionPropertyTemplate')
        queryTable = tableMonitoring.innerJoin(tableAPTemplate, tableAPTemplate['id'].eq(tableMonitoring['propertyTemplate_id']))
        cond = [tableAPTemplate['isCalcParamDoseNomenclatureExpense'].eq(1),
                tableMonitoring['deleted'].eq(0),
                tableAPTemplate['deleted'].eq(0),
                tableMonitoring['client_id'].eq(clientId)
                ]
        cols = [tableAPTemplate['id'],
                tableAPTemplate['name']
                ]
        records = db.getRecordList(queryTable, cols, cond, order='ActionPropertyTemplate.code, ActionPropertyTemplate.name')
        for record in records:
            templateId = forceRef(record.value('id'))
            if templateId and templateId not in propertyIdHeader:
                propertyIdHeader.append(templateId)
        if len(propertyIdHeader) > 1:
            valuePropertyToTemplateItems = self.getCalculationParamValuePropertyToTemplateItems(clientId, valuePropertyToTemplateItems, propertyIdHeader)
        templateIdList = db.getDistinctIdList(tableAPTemplate, [tableAPTemplate['id']], [tableAPTemplate['isCalcParamDoseNomenclatureExpense'].eq(1)])
        if templateIdList:
            valuePropertyToTemplateItems = self.getCalculationParamValuePropertyToTemplateItems(clientId, valuePropertyToTemplateItems, templateIdList)
        return valuePropertyToTemplateItems


    def getCalculationParamValuePropertyToTemplateItems(self, clientId, valuePropertyToTemplateItems, templateIdList):
        if clientId and templateIdList:
            db = QtGui.qApp.db
            tableEvent = db.table('Event')
            tableAction = db.table('Action')
            tableActionType = db.table('ActionType')
            tableActionProperty = db.table('ActionProperty')
            tableActionPropertyType = db.table('ActionPropertyType')
            tableMonitoring = db.table('Client_Monitoring')
            tableAPTemplate = db.table('ActionPropertyTemplate')
            queryTable = tableEvent.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
            queryTable = queryTable.innerJoin(tableActionProperty, tableActionProperty['action_id'].eq(tableAction['id']))
            queryTable = queryTable.innerJoin(tableActionPropertyType, tableActionPropertyType['actionType_id'].eq(tableActionType['id']))
            queryTable = queryTable.innerJoin(tableAPTemplate, tableAPTemplate['id'].eq(tableActionPropertyType['template_id']))
            queryTable = queryTable.innerJoin(tableMonitoring, tableMonitoring['propertyTemplate_id'].eq(tableAPTemplate['id']))
            cond = [tableEvent['client_id'].eq(clientId),
                    tableAPTemplate['isCalcParamDoseNomenclatureExpense'].eq(1),
                    tableEvent['deleted'].eq(0),
                    tableAction['deleted'].eq(0),
                    tableAction['endDate'].isNotNull(),
                    tableActionPropertyType['template_id'].isNotNull(),
                    tableActionType['deleted'].eq(0),
                    tableActionPropertyType['deleted'].eq(0),
                    tableAPTemplate['deleted'].eq(0),
                    tableMonitoring['deleted'].eq(0),
                    tableActionProperty['deleted'].eq(0),
                    tableActionPropertyType['template_id'].inlist(templateIdList),
                    tableActionProperty['type_id'].eq(tableActionPropertyType['id'])
                    ]
            cols = [u'DISTINCT ActionPropertyType.typeName, ActionPropertyType.valueDomain',]
            records = db.getRecordList(queryTable, cols, cond)
            cols = [tableAction['endDate'],
                    tableActionPropertyType['template_id'],
                    tableActionPropertyType['typeName'],
                    tableActionPropertyType['valueDomain']
                    ]
            for record in records:
                queryTableProperty = queryTable
                typeName = forceString(record.value('typeName'))
                valueDomain = forceString(record.value('valueDomain'))
                propertyType = CActionPropertyValueTypeRegistry.get(typeName, valueDomain)
                if propertyType:
                    tablePropertyType = db.table(propertyType.getTableName())
                    queryTableProperty = queryTableProperty.leftJoin(tablePropertyType, db.joinAnd([tablePropertyType['id'].eq(tableActionProperty['id']), tablePropertyType['value'].trim()+' IS NOT NULL']))
                    cols.append(tablePropertyType['value'].alias('value'+typeName))
                    queryTable = queryTableProperty
            if len(cols) > 4:
                order = [u'Action.endDate DESC']
                records = db.getDistinctRecordList(queryTable, cols, cond, order)
                for record in records:
                    templateId = forceRef(record.value('template_id'))
                    endDate = forceDate(record.value('endDate'))
                    if templateId and endDate:
                        typeName = forceString(record.value('typeName'))
                        valueDomain = forceString(record.value('valueDomain'))
                        value = record.value('value'+typeName)
                        propertyType = CActionPropertyValueTypeRegistry.get(typeName, valueDomain)
                        if propertyType:
                            valueProperty = propertyType.convertQVariantToPyValue(value) if type(value) == QVariant else value
                            if valueProperty:
                                if type(valueProperty) is int:
                                    reportLine = valuePropertyToTemplateItems.setdefault(templateId, (0, None))
                                    if not reportLine[1] or reportLine[1] < endDate:
                                        reportLine = (valueProperty, endDate)
                                        valuePropertyToTemplateItems[templateId] = reportLine
                                elif type(valueProperty) is float:
                                    reportLine = valuePropertyToTemplateItems.setdefault(templateId, (0.0, None))
                                    if not reportLine[1] or reportLine[1] < endDate:
                                        reportLine = (valueProperty, endDate)
                                        valuePropertyToTemplateItems[templateId] = reportLine
        return valuePropertyToTemplateItems


    def calculationDosageByIndex(self, group, calculationParam):
        if group:
            group.setCalculationDosageInExists(calculationParam)


    def calculationDosageToDateByIndex(self, group, calculationParam, date):
        if group and date:
            group.setCalculationDosageToDateInExists(calculationParam, date)
        return group
            

    def updateSmnn_SmnnGrlslf(self, action, group, nomenclatureId, oldNomenclatureId):
        if nomenclatureId and nomenclatureId != oldNomenclatureId:
            oldSmnnUUID = action.getSmnnUUIDPropertyValue()
            db = QtGui.qApp.db
            tableEsklp_Smnn = db.table('esklp.Smnn')
            tableNC = db.table('rbNomenclature')
            tableESKLP_Klp = db.table('esklp.Klp')
            cond = []
            order = u'esklp.Smnn.code, esklp.Smnn.mnn, esklp.Smnn.form'
            queryTable = tableNC.innerJoin(tableESKLP_Klp, tableESKLP_Klp['UUID'].eq(tableNC['esklpUUID']))
            queryTable = queryTable.innerJoin(tableEsklp_Smnn, tableEsklp_Smnn['id'].eq(tableESKLP_Klp['smnn_id']))
            cond.append(tableNC['id'].eq(nomenclatureId))
            records = db.getRecordList(queryTable, [tableEsklp_Smnn['UUID']], cond, order=order)
            newSmnnUUID = ''
            if len(records) == 1:
                record = records[0]
                newSmnnUUID = forceStringEx(record.value('UUID')) if record else ''
            if oldSmnnUUID != newSmnnUUID:
                group.setSmnnUUID(newSmnnUUID, updateExecutionPlan=False)
                action.setSmnnUUIDPropertyValue(newSmnnUUID)
            if newSmnnUUID:
                oldSmnnGrlsLfId = action.getSmnnGrlsLfPropertyValue()
                lfFormIdList = getLfFormIdList(nomenclatureId = nomenclatureId, smnnUUID = newSmnnUUID)
                if len(lfFormIdList) == 1:
                    newSmnnGrlsLfId = lfFormIdList[0]
                    if oldSmnnGrlsLfId != newSmnnGrlsLfId:
                        group.setLfFormId(newSmnnGrlsLfId, updateExecutionPlan=False)
                        action.setSmnnGrlsLfPropertyValue(newSmnnGrlsLfId)
                elif oldSmnnGrlsLfId not in lfFormIdList:
                    group.setLfFormId(None, updateExecutionPlan=False)
                    action.setSmnnGrlsLfPropertyValue(None)
            else:
                group.setLfFormId(None, updateExecutionPlan=False)
                action.setSmnnGrlsLfPropertyValue(None)
        return action, group


    def getNomenclatureAnalog(self, nomenclatureId):
        if nomenclatureId not in self._nomenclatureAnalogCache.keys():
            db = QtGui.qApp.db
            record = db.getRecord('rbNomenclature', 'analog_id', nomenclatureId)
            analogId = forceRef(record.value('analog_id')) if record else None
            self._nomenclatureAnalogCache[nomenclatureId] = analogId
        return self._nomenclatureAnalogCache.get(nomenclatureId, None)
    
    
    def emitCellChanged(self, row, column):
        index = self.index(row, column)
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)
        

class CActionsModelEx(CActionsModel):
    Col_ActionType = 0
    Col_smnnUUID   = 5
    Col_Nomenclature = 7
    Col_Doses = 7
    Col_Signa = 11
    Col_SignaComment = 12

    __pyqtSignals__ = ('amountChanged(int)',
                      )
    
    class CLocActionPropertyTemplateInDocTableCol(CRBInDocTableCol):
        def __init__(self, title, fieldName, width, tableName, **params):
            CRBInDocTableCol.__init__(self, title, fieldName, width, tableName, **params)

        def toString(self, val, record):
            cache = CRBModelDataCache.getData(self.tableName, True)
            text = cache.getStringById(forceInt(val), self.showFields)
            return toVariant('' if (text=='0' or not text) else text)
        

    class CLocSignaInDocTableCol(CInDocTableCol):
        def __init__(self, title, fieldName, width, tableName, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)

        def toString(self, val, record):
            text = forceStringEx(val)
            if text:
                return toVariant('' if (text=='0' or not text) else text)
            return toVariant('')

    class CLocSignaCommentInDocTableCol(CInDocTableCol):
        _SIGNA  = 3
        def __init__(self, title, fieldName, width, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, readOnly=True)
            self.caches = {}

        def toString(self, val, record):
            actionId = forceRef(val)
            if actionId:
                action = self.caches.get(actionId, None)
                if not action:
                    action = CAction.getActionById(actionId)
                    self.caches[actionId] = action
                if action:
                    return toVariant(action.findSignaCommentPropertyText())
            return QVariant()

        def toSortString(self, val, record):
            return forcePyType(self.toString(val, record))

        def toStatusTip(self, val, record):
            return self.toString(val, record)

    class CLocNomenclatureInDocTableCol(CNomenclatureInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CNomenclatureInDocTableCol.__init__(self, title, fieldName, width, **params)

        def createEditor(self, parent):
            editor = CNomenclatureInDocTableCol.createEditor(self, parent)
            editor.setOnlySmnn(True)
            editor.setOnlyNomenclature(True)
            return editor

        def setEditorData(self, editor, value, record):
            actionTypeId = forceRef(record.value('actionType_id'))
            actionType = CActionTypeCache.getById(actionTypeId) if actionTypeId else None
            isSMNN = False
            isOnlyMnnEsklpFormVisible = False
            smnnUUID = None
            smnnGrlsLfId = None
            smnnName = ''
            if actionType:
                for propertyType in actionType.getPropertiesById().values():
                    if propertyType.isNomenclatureSmnnActionPropertyValueType() or propertyType.isNomenclatureSmnnGrlsLfActionPropertyValueType():
                        isSMNN = True
                        break
            if isSMNN:
                smnnGrlsLfId = forceRef(record.value('lfForm_id'))
                smnnUUID = forceStringEx(record.value('smnnUUID'))
                smnnName = forceStringEx(record.value('smnnName'))
                isOnlyMnnEsklpFormVisible = bool(smnnUUID) and bool(smnnGrlsLfId)
            editor.setIsOnlyMnnEsklpFormVisible(isOnlyMnnEsklpFormVisible)
            editor.setNomenclatureSmnnUUID(smnnUUID)
            editor.setNomenclatureSmnnName(smnnName if smnnName is not None else '')
            editor.setLfFormId(smnnGrlsLfId)
            editor.setOnlyExists(actionType.isNomenclatureExpense if actionType else True)
            financeId = forceRef(record.value('finance_id'))
            medicalAidKindId = forceRef(record.value('medicalAidKind_id'))
            if not medicalAidKindId:
                eventTypeId = forceRef(record.value('eventType_id'))
                medicalAidKindId = getEventMedicalAidKindId(eventTypeId) if eventTypeId else None
            supplierId = forceRef(record.value('orgStructure_id'))
            editor.setFinanceId(financeId)
            editor.setMedicalAidKindId(medicalAidKindId)
            editor.setOrgStructureId(supplierId if supplierId else QtGui.qApp.currentOrgStructureId())
            editor.getFilterData()
            editor.setFilter(editor._filter)
            editor.setValue(forceRef(value))
    
    class CLocDosesInDocTableCol(CFloatInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CFloatInDocTableCol.__init__(self, title, fieldName, width, **params)

        def toString(self, val, record):
            dosesName = forceStringEx(record.value('dosesName'))
            return toVariant(dosesName)
        
        def createEditor(self, parent):
            editor = QtGui.QDoubleSpinBox(parent)
            editor.setMaximum(10000)
            editor.setMinimum(0)
            editor.setDecimals(2)
            return editor

        def setEditorData(self, editor, value, record):
            val = forceDouble(value)
            editor.setValue(val)

        def getEditorData(self, editor):
            return toVariant(editor.value())
    
    class CLocLfFormInDocTableCol(CLfFormInDocTableCol):
        def __init__(self, title, fieldName, width, tableName, **params):
            CLfFormInDocTableCol.__init__(self, title, fieldName, width, tableName, **params)

        def toString(self, val, record):
            cache = CRBModelDataCache.getData(self.tableName, True)
            text = cache.getStringById(forceInt(val), self.showFields)
            lfFormName = forceStringEx(record.value('lfFormName'))
            return toVariant('') if forceString(text).lower() == u'не задано' else toVariant('')#lfFormName)

        def setEditorData(self, editor, value, record):
            orgStructureId = forceRef(record.value('orgStructure_id'))
            nomenclatureId = forceRef(record.value('nomenclature_id'))
            smnnUUID = forceStringEx(record.value('smnnUUID'))
            editor.setOrgStructureId(orgStructureId if orgStructureId else QtGui.qApp.currentOrgStructureId())
            editor.setNomenclatureId(nomenclatureId)
            editor.setNomenclatureSmnnUUID(smnnUUID)
            editor.setValue(forceRef(value))

    class CLocActionTypeGroupInDocTableCol(CRBInDocTableCol):
        def __init__(self, title, fieldName, width, tableName, **params):
            CRBInDocTableCol.__init__(self, title, fieldName, width, tableName, **params)

        def toString(self, val, record):
            cache = CRBModelDataCache.getData(self.tableName, True)
            text = cache.getStringById(forceInt(val), self.showFields)
            return toVariant('' if (text=='0' or not text) else text)
        
    def __init__(self, parent, actionTypeClass=None):
        CActionsModel.__init__(self, parent, actionTypeClass=actionTypeClass)
        self.actionTypeClass = None
        self.actionTypeIdList = []
        self.disabledActionTypeIdList = []
        self._cols = []
        self._items = []
        self._loadedActionIdListWithEndDate = []
        self.eventEditor = None
        if actionTypeClass is not None:
            self.setActionTypeClass(actionTypeClass)
        self.idxFieldName = 'idx'
        self.readOnly = False
        self.ttjForDeleteIdList = []
        self.cachedFreeJobTicket = []
        self.cachedFreeJobTicketActionProperty = []
        self.actionIdForMarkDeleted = []
        self.addCol(CRBInDocTableCol(u'Тип действия', 'actionType_id', 14, 'ActionType', showFields=CRBComboBox.showName).setReadOnly(True))
        self.addCol(CEnumInDocTableCol(u'Статус', 'status', 10, CActionStatus.names)).setReadOnly(True)
        self.addCol(self.CLocActionTypeGroupInDocTableCol(u'Схема', 'actionTypeGroup_id', 14, 'ActionTypeGroup', showFields=CRBComboBox.showCode).setReadOnly(True))
        self.addCol(CDateInDocTableCol(u'Дата назначения', 'directionDate', 10).setReadOnly(True))
        self.addCol(CDateInDocTableCol(u'Дата начала', 'begDate', 10).setReadOnly(True))
        self.addCol(CSmnnInDocTableCol(u'МНН', 'smnnUUID', 22).setReadOnly(True))
        self.addCol(self.CLocLfFormInDocTableCol(u'Форма выпуска', 'lfForm_id',  10, 'rbLfForm').setReadOnly(True))
        self.addCol(self.CLocNomenclatureInDocTableCol(u'ЛС',  'nomenclature_id', 15, showFields = CRBComboBox.showName).setReadOnly(not QtGui.qApp.userHasRight(urAccessEditCentralizedAccounting)))
        self.addCol(CDateInDocTableCol(u'План', 'plannedEndDate', 10).setReadOnly(True))
        self.addCol(self.CLocActionPropertyTemplateInDocTableCol(u'Параметр расчета', 'actionPropertyTemplate_id', 10, 'ActionPropertyTemplate', addNone=False, showFields=CRBComboBox.showCode, filter=u'ActionPropertyTemplate.isCalcParamDoseNomenclatureExpense=1').setReadOnly(True))
        self.addCol(self.CLocDosesInDocTableCol(u'Доза', 'doses', 10).setReadOnly(not QtGui.qApp.userHasRight(urAccessEditCentralizedAccounting)))
        self.addCol(self.CLocSignaInDocTableCol(u'СП', 'signa', 10, 'rbNomenclatureUsingType', addNone=False, showFields=CRBComboBox.showName).setReadOnly(True))
        self.addCol(self.CLocSignaCommentInDocTableCol(u'Комментарий к СП', 'id', 20).setReadOnly(True))
        self.addCol(CIntInDocTableCol(u'Д', 'duration', 10).setReadOnly(True))
        self.addCol(CIntInDocTableCol(u'И', 'periodicity', 10).setReadOnly(True))
        self.addCol(CIntInDocTableCol(u'К', 'aliquoticity', 10).setReadOnly(True))
        self.addCol(CInDocTableCol(u'Примечание', 'note', 20).setReadOnly(True))
        self.table = QtGui.qApp.db.table('Action')

    def cols(self):
        return self._cols
    

    def addCol(self, col):
        self._cols.append(col)
        return col


    def columnCount(self, index=None):
        return len(self._cols)


    def rowCount(self, index=None):
        return len(self._items)
    
    
    def sort(self, column, ascending):
        col = self._cols[column]
        self._items.sort(key=lambda item: col.toSortString(item[0].value(col.fieldName()), item[0]), reverse=not ascending)
        self.emitRowsChanged(0, len(self._items)-1)


    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return self._cols[section].title()
            if role == Qt.ToolTipRole:
                return self._cols[section].toolTip()
            if role == Qt.WhatsThisRole:
                return self._cols[section].whatsThis()
        return QVariant()

    
    def flags(self, index):
        if self.readOnly:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        row = index.row()
        if self.isExposed(row):
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        column = index.column()
        if column in (self.Col_Nomenclature, self.Col_Doses) and QtGui.qApp.userHasRight(urAccessEditCentralizedAccounting):
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable
    

    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if 0 <= row < len(self._items):
            if role == Qt.EditRole:
                col = self._cols[column]
                record = self._items[row][0]
                return record.value(col.fieldName())
            if role == Qt.DisplayRole:
                col = self._cols[column]
                record = self._items[row][0]
                #if column == CActionsModelEx.Col_ActionType:
                #    outName = forceString(record.value('specifiedName'))
                #    actionTypeId = forceRef(record.value('actionType_id'))
                #    if actionTypeId:
                #        actionType = CActionTypeCache.getById(actionTypeId)
                #        if actionType:
                #            outName = actionType.name + ' ' + outName if outName else actionType.name
                #            if actionType.showBegDate:
                #                outName += ', ' + forceString(forceDate(record.value('begDate')))
                #            return QVariant(outName)
                return col.toString(record.value(col.fieldName()), record)
            if role == Qt.StatusTipRole:
                col = self._cols[column]
                record = self._items[row][0]
                return col.toStatusTip(record.value(col.fieldName()), record)
            if role == Qt.TextAlignmentRole:
                col = self._cols[column]
                return col.alignment()
            if role == Qt.CheckStateRole:
                col = self._cols[column]
                record = self._items[row][0]
                return col.toCheckState(record.value(col.fieldName()), record)
            if role == Qt.ForegroundRole:
                col = self._cols[column]
                record = self._items[row][0]
                return col.getForegroundColor(record.value(col.fieldName()), record)
        return QVariant()


    def actionTypeId(self, row):
        if 0 <= row < len(self._items):
            return forceInt(self._items[row][CActionsModelEx.Col_ActionType].value('actionType_id'))
        else:
            return None


    def setActionTypeClass(self, actionTypeClass):
        self.actionTypeClass = actionTypeClass
        self.actionTypeIdList = getActionTypeIdListByClass(actionTypeClass)
        self._cols[CActionsModelEx.Col_ActionType].filter = 'class=%d'%actionTypeClass


    def setData(self, index, value, role=Qt.EditRole, presetAction=None):
        if not index.isValid():
            return False
        if role == Qt.EditRole:
            row = index.row()
            if row >= 0 and row < len(self._items):
                column = index.column()
                record = self._items[row][0]
                actionTypeId = forceRef(record.value('actionType_id'))
                if actionTypeId is None:
                    return False
                if actionTypeId and not ( self.checkMaxOccursLimit(actionTypeId) and
                                          self.checkMovingNoLeaved(actionTypeId) and
                                          self.checkMovingAfterReceived(actionTypeId) and
                                          self.checkLeavedAfterMoving(actionTypeId) and
                                          self.checkLeavedAfterMovingDate(actionTypeId) ):
                    return False
                action = self._items[row][1]
                if column == self.Col_Nomenclature:
                    newNomenclatureId = forceRef(value)
                    oldNomenclatureId = forceRef(record.value('nomenclature_id'))
                    if oldNomenclatureId != newNomenclatureId:
                        action.setNomenclaturePropertyValue(newNomenclatureId)
                    return True
                elif column == self.Col_Doses:
                    oldDosage = action.findDosagePropertyValue()
                    newDosage = forceDouble(value)
                    if oldDosage != newDosage:
                        action.setDosagePropertyValue(newDosage)
                    return True
                self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)
                self.emitItemsCountChanged()
            return False


    def createEditor(self, index, parent):
        column = index.column()
        if hasattr(self._cols[column], 'setIndex'):
            self._cols[column].setIndex(index)
        return self._cols[column].createEditor(parent)


    def setEditorData(self, column, editor, value, record):
        return self._cols[column].setEditorData(editor, value, record)


    def getEditorData(self, column, editor):
        return self._cols[column].getEditorData(editor)


    def afterUpdateEditorGeometry(self, editor, index):
        pass
    
    def emitRowDataChanged(self, row):
        index1 = self.index(row, 0)
        index2 = self.index(row, self.columnCount())
        self.emit(QtCore.SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index1, index2)


    def emitAllDataChanged(self):
        index1 = self.index(0, 0)
        index2 = self.index(self.rowCount(), self.columnCount())
        self.emit(QtCore.SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index1, index2)

