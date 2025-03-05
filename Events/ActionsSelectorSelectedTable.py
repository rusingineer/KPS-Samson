# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2022 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import Qt, QDate, QVariant, SIGNAL, QTime, QDateTime

from Events.ActionTemplateChoose import CActionTemplateComboBox
from library.ICDInDocTableCol   import CICDExInDocTableCol
from library.InDocTable         import (
    CRecordListModel, CBoolInDocTableCol, CDateInDocTableCol, CDateTimeInDocTableCol, CFloatInDocTableCol, CInDocTableCol,
    CInDocTableView, CIntInDocTableCol, CLocItemDelegate, CRBInDocTableCol)
from library.Utils              import forceDate, forceDateTime, forceTime, forceDouble, forceInt, forceRef, forceString, forceStringEx, toVariant
from library.Calendar           import wpFiveDays, addWorkDays
from Events.Action              import CAction, CActionType, CActionTypeCache, getActionDefaultContractId
from Events.ActionProperty      import CToothActionPropertyValueType, CNomenclatureActionPropertyValueType, CStringActionPropertyValueType, CNomenclatureUsingTypeActionPropertyValueType
from Events.ExecutionPlanDialog import CGetExecutionPlan
from Events.ExecutionPlan.ExecutionPlanType import executionPlanType
from Events.Utils               import getEventActionContract
from Orgs.OrgComboBox           import CContractComboBox

_RECIPE = 1
_DOSES  = 2
_SIGNA  = 3
_ACTIVESUBSTANCE = 4

def _getNomenclatureValues(nomenclatureId, cache):
    if nomenclatureId not in cache:
        db = QtGui.qApp.db
        nomenclatureRecord = db.getRecord('rbNomenclature', 'unit_id, dosageValue', nomenclatureId)
        dosageUnitId = forceRef(nomenclatureRecord.value('unit_id'))
        result = {'dosageValue': forceDouble(nomenclatureRecord.value('dosageValue'))}
        if dosageUnitId:
            unitRecord = db.getRecord('rbUnit', 'code, name', dosageUnitId)
            name = ' | '.join([forceString(unitRecord.value('name')), forceString(unitRecord.value('code'))])
        else:
            name = ''
        result['name'] = name
        cache[nomenclatureId] = result

    return cache[nomenclatureId]


class CCheckedActionsModel(CRecordListModel):
    class CLocEnableCol(CBoolInDocTableCol):
        def __init__(self, selector):
            CBoolInDocTableCol.__init__(self, u'Включить', 'checked', 10)
            self.selector = selector

        def toCheckState(self, val, record):
            return CBoolInDocTableCol.toCheckState(self, val, record)


    class CContractInDocTableCol(CInDocTableCol):
        def __init__(self, model, nomenclatureLS=False):
            CInDocTableCol.__init__(self, u'Договор', 'contract_id', 20)
            self.model = model


        def toString(self, val, record):
            contractId = forceRef(val)
            if contractId:
                names = ['number', 'date', 'resolution']
                record = QtGui.qApp.db.getRecord('Contract', names, contractId)
                str = ' '.join([forceString(record.value(name)) for name in names])
            else:
                str = u'не задано'
            return QVariant(str)


        def createEditor(self, parent):
            eventEditor = self.model.parentWidget.eventEditor
            editor = CContractComboBox(parent)
            editor.setOrgId(eventEditor.orgId)
            editor.setClientInfo(eventEditor.clientId,
                                 eventEditor.clientSex,
                                 eventEditor.clientAge,
                                 eventEditor.clientWorkOrgId,
                                 eventEditor.clientPolicyInfoList)
            return editor

        def getEditorData(self, editor):
            return QVariant(editor.value())


        def setEditorData(self, editor, value, record):
            eventEditor = self.model.parentWidget.eventEditor
            financeId = forceRef(record.value('finance_id')) or eventEditor.eventFinanceId
            editor.setFinanceId(financeId)
            editor.setActionTypeId(forceRef(record.value('actionType_id')))
            contractId = forceRef(value)
            if contractId is None:
                if financeId == eventEditor.eventFinanceId:
                    contractId = eventEditor.contractId
            editor.setValue(contractId)
            editor.setBegDate(forceDate(record.value('directionDate')) or QDate.currentDate())
            editor.setEndDate(forceDate(record.value('endDate')) or QDate.currentDate())

    class CActionTemplateInDocTableCol(CInDocTableCol):
        def __init__(self, model):
            CInDocTableCol.__init__(self, u'Шаблон действия', 'actionTemplateId', 20)
            self.model = model


        def toString(self, val, record):
            actionTemplateId = forceRef(val)
            if actionTemplateId:
                record = QtGui.qApp.db.getRecord('ActionTemplate', 'name', actionTemplateId)
                str = forceString(record.value('name'))
            else:
                str = u'не задано'
            return QVariant(str)


        def createEditor(self, parent):
            eventEditor = self.model.parentWidget.eventEditor
            editor = CActionTemplateComboBox(parent)
            return editor

        def getEditorData(self, editor):
            return QVariant(editor.value())


        def setEditorData(self, editor, value, record):
            eventEditor = self.model.parentWidget.eventEditor
            actionTypeId = forceRef(record.value('actionType_id'))
            editor.setFilter(actionTypeId, None, None, None, eventEditor.clientSex, eventEditor.clientAge)
            editor.setValue(forceRef(value))


    class CDosagePropertyTableCol(CInDocTableCol):
        def __init__(self, model):
            CInDocTableCol.__init__(self, u'Doses', 'doses', 10)
            self._nomenclatureCache = model._nomenclatureCache
            self._model = model

        def toString(self, index, val, record):
            propertyValue = None

            row = index.row()
            column = index.column()
            actionTypeId = forceRef(record.value('actionType_id'))
            values  = self._model._mapActionTypeIdToPropertyValues.get(actionTypeId, None)
            if values:
                fieldName  = self._model._cols[column].fieldName()
                cellValues = values.get(fieldName, None)
                if cellValues:
                    action = self._model._idRowToAction[(actionTypeId, row)]
                    propertyType = cellValues['propertyType']
                    property = action.getPropertyById(propertyType.id)
                    propertyValue = property.getText()

            if not propertyValue:
                return QVariant()

            nomenclatureId = None
            cellValues = values.get('recipe', None)
            if cellValues:
                action = self._model._idRowToAction[(actionTypeId, row)]
                propertyType = cellValues['propertyType']
                if isinstance(propertyType.valueType, CNomenclatureActionPropertyValueType):
                    property = action.getPropertyById(propertyType.id)
                    nomenclatureId = property.getValue()

            if not nomenclatureId:
                return QVariant('{0:.2f}'.format(propertyValue))

            values = _getNomenclatureValues(nomenclatureId, self._nomenclatureCache)
            name = values.get('name')

            return QVariant(
                u'{0:.2f} {1}'.format(propertyValue, name)
            )


    class CLocDateTimeInDocTableCol(CDateTimeInDocTableCol):

        def createEditor(self, parent):
            editor = QtGui.QDateTimeEdit(parent)
            editor.setDisplayFormat('dd.MM.yyyy HH:mm')
#            editor.setCalendarPopup(True)
            return editor

        def getEditorData(self, editor):
            return toVariant(editor.dateTime())

        def setEditorData(self, editor, value, record):
            editor.setDateTime(forceDateTime(value))

        def toString(self, val, record):
            if not val.isNull():
                return QVariant(forceString(val))
            return QVariant()


    def __init__(self, parent, existsActionsModel, actionTypesModel=None, includeTooth=False, nomenclatureLS=False):
        CRecordListModel.__init__(self, parent)

        self._nomenclatureCache = {}

        self.addExtCol(CCheckedActionsModel.CLocEnableCol(parent),
                       QVariant.Bool)
        self.addExtCol(CBoolInDocTableCol(u'Срочный','isUrgent', 10), QVariant.Bool)
        self.addExtCol(CRBInDocTableCol(u'Действие', 'actionType_id', 15, 'ActionType', showFields=2).setReadOnly(),
                       QVariant.Int)
        self.addExtCol(CCheckedActionsModel.CLocDateTimeInDocTableCol(u'Назначить', 'directionDate', 10),
                       QVariant.DateTime)
        self.addExtCol(CCheckedActionsModel.CLocDateTimeInDocTableCol(u'Начать', 'begDate', 10),
                       QVariant.DateTime)
        self.addExtCol(CICDExInDocTableCol(u'МКБ', 'MKB', 7),
                       QVariant.String)
        self.addExtCol(CFloatInDocTableCol(u'Количество', 'amount', 10, precision=2),
                       QVariant.Double)
        if includeTooth:
            self.addExtCol(CInDocTableCol(u'Зуб', 'tooth', 10), QVariant.String)
        self.addExtCol(CIntInDocTableCol(u'Количество процедур', 'quantity', 10),
                       QVariant.Int)
        self.addExtCol(CIntInDocTableCol(u'Длительность', 'duration', 10),
                       QVariant.Int)
        self.addExtCol(CIntInDocTableCol(u'Интервал', 'periodicity', 10),
                       QVariant.Int)
        self.addExtCol(CIntInDocTableCol(u'Кратность', 'aliquoticity', 10),
                       QVariant.Int)
        self.addExtCol(CDateInDocTableCol(u'План', 'plannedEndDate', 10),
                       QVariant.Date)
        self.addExtCol(CRBInDocTableCol(u'Тип финансирования', 'finance_id', 10, 'rbFinance', showFields=2),
                       QVariant.Int)
        self.addExtCol(CCheckedActionsModel.CContractInDocTableCol(self),
                       QVariant.Int)
        self.addExtCol(CFloatInDocTableCol(u'Сумма', 'price', 10, precision=2),
                       QVariant.Double)
        self.addExtCol(CInDocTableCol(u'Recipe', 'recipe', 10),
                       QVariant.String)
        self.addExtCol(CCheckedActionsModel.CDosagePropertyTableCol(self),
                       QVariant.String)
        self.addExtCol(CRBInDocTableCol(u'Signa', 'signa', 10, 'rbNomenclatureUsingType', showFields=2),
                       QVariant.Int)
        self.addExtCol(CInDocTableCol(u'Действующее вещество', 'activeSubstance_id', 10),
                       QVariant.String)
        self.addExtCol(CCheckedActionsModel.CActionTemplateInDocTableCol(self), QVariant.Int)

#        if nomenclatureLS:
#            self.addExtCol(CIntInDocTableCol(u'Шаг', 'offset', 10), QVariant.Int)
        self._existsActionsModel = existsActionsModel
        self._actionTypesModel   = actionTypesModel
        self.clientId = None
        self.medicalAidKindId = parent.eventEditor.eventMedicalAidKindId if hasattr(parent.eventEditor, 'eventMedicalAidKindId') and parent.eventEditor.eventMedicalAidKindId else None
        self.parentWidget = parent
        self._table            = QtGui.qApp.db.table('Action')
        self._dbFieldNamesList = [field.fieldName.replace('`', '') for field in self._table.fields]
        self.prices = []
        self._mapPropertyTypeCellsActivity = {}
        self._propertyColsNames = ['recipe', 'doses', 'signa', 'activeSubstance_id', 'reaction', 'cancelDate']
        if includeTooth:
            self._propertyColsNames.append('tooth')
#        if nomenclatureLS:
#            self._propertyColsNames.append('offset')
        self._propertyColsIndexes = [self.getColIndex(name) for name in self._propertyColsNames]
        self._mapActionTypeIdToPropertyValues = {}
        self._rowToAction = {}
        self._idRowToAction = {}
        self._idToRows = {}

        boldFont = QtGui.QFont()
        boldFont.setWeight(QtGui.QFont.Bold)
        self._qBoldFont = QVariant(boldFont)


    def setClientId(self, clientId):
        self.clientId = clientId

    def cellReadOnly(self, index):
        column = index.column()
        if column == self.getColIndex('plannedEndDate'):
            return not self.isRowPlanEndDateEdited(index.row())
        elif column in self._propertyColsIndexes:
            return not self._mapPropertyTypeCellsActivity.get((index.row(), column), False)
        return False

    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.ToolTipRole:
                if section == self.getColIndex('duration'):
                    return QVariant(u'Длительность курса лечения в днях.')
                elif section == self.getColIndex('periodicity'):
                    result = '\n'.join(
                                       [
                                        u'0 - каждый день,',
                                        u'1 - через 1 день,',
                                        u'2 - через 2 дня,',
                                        u'3 - через 3 дня,',
                                        u'и т.д.'
                                       ]
                                      )
                    return QVariant(result)
                elif section == self.getColIndex('aliquoticity'):
                    return QVariant(u'Сколько раз в сутки.')
        return CRecordListModel.headerData(self, section, orientation, role)

    def isRowPlanEndDateEdited(self, row):
        return not (self.isRowDpedBegDatePlusAmount(row) or self.isRowDpedBegDatePlusDuration(row))

    def getDefaultPlannedEndDate(self, actionTypeId):
        return CActionTypeCache.getById(actionTypeId).defaultPlannedEndDate

    def getDefaultEndDate(self, actionTypeId):
        return CActionTypeCache.getById(actionTypeId).defaultEndDate

    def isDpedEndDateActionBegDate(self, actionTypeId):
        return self.getDefaultEndDate(actionTypeId) == CActionType.dedActionBegDate

    def isDpedBegDatePlusAmount(self, actionTypeId):
        return self.getDefaultPlannedEndDate(actionTypeId) == CActionType.dpedBegDatePlusAmount

    def isDpedBegDatePlusDuration(self, actionTypeId):
        return self.getDefaultPlannedEndDate(actionTypeId) == CActionType.dpedBegDatePlusDuration

    def isRowDpedBegDatePlusAmount(self, row):
        actionTypeId = forceRef(self.items()[row].value('actionType_id'))
        return self.isDpedBegDatePlusAmount(actionTypeId)

    def isRowDpedBegDatePlusDuration(self, row):
        actionTypeId = forceRef(self.items()[row].value('actionType_id'))
        return self.isDpedBegDatePlusDuration(actionTypeId)

    def isRowDpedEndDateActionBegDate(self, row):
        actionTypeId = forceRef(self.items()[row].value('actionType_id'))
        return self.isDpedEndDateActionBegDate(actionTypeId)
        
    def regenerate(self):
        count = len(self.items())
        self.prices = [0.0]*count
        self.updatePricesAndSums(0, count-1)


#    def getActionRecord(self, actionTypeId):
#        row = self._idToRow[actionTypeId]
#        item = self._items[row]
#        return self.getClearActionRecord(item)

    def getPropertiesValues(self, actionTypeId):
        result = {}
        values = self._mapActionTypeIdToPropertyValues.get(actionTypeId, None)
        if values:
            for value in values.values():
                if value['value'].isValid():
                    result[value['propertyType'].id] = value['value']
        return result

    def getContractId(self):
        return self.parentWidget.getContractId()

    def getPrice(self, record):
        actionTypeId = forceRef(record.value('actionType_id'))
        financeId    = forceRef(record.value('finance_id'))
        contractId   = forceRef(record.value('contract_id'))
        return self.getPriceEx(actionTypeId, contractId, financeId)

    def getPriceEx(self, actionTypeId, contractId, financeId):
        return self.parentWidget.getPrice(actionTypeId, contractId, financeId)

    def getClearActionRecord(self, item):
        record = self._table.newRecord()
        for iCol in xrange(record.count()):
            fieldName = record.fieldName(iCol)
            record.setValue(fieldName, item.value(fieldName))
        return record

    def insertSameActionByRow(self, row):
        if row >= 0:
            actionTypeId = self._rowToAction[row].getType().id
            self.parentWidget.insertActionIntoCheckedModel(actionTypeId)


    def add(self, actionTypeId, amount=None, financeId=None, contractId=None, recipe=None, doses=None, signa=None, duration=None, periodicity=None, aliquoticity=None, offset=0, piRecords=None, quantity=None, activeSubstanceId=None, actionTemplate_id=None):
        row = len(self._items)
        record = self.getEmptyRecord(self.getPropertyTypeCellsSettings(actionTypeId, row))
        action = CAction.getFilledAction(self.parentWidget.eventEditor, record, actionTypeId, initPresetValues=True)
        record.setValue('checked', QVariant(Qt.Checked))
        record.setValue('price', QVariant(self.getPrice(record)))
        record.setValue('actionTemplateId', toVariant(actionTemplate_id))
      #  action._record.setValue('actionTemplate_id', toVariant(actionTemplate_id))
        if amount:
            record.setValue('amount', QVariant(amount))
        if financeId:
            record.setValue('finance_id', QVariant(financeId))
        if self.medicalAidKindId:
            record.setValue('medicalAidKind_id', QVariant(self.medicalAidKindId))
        if contractId:
            record.setValue('contract_id', QVariant(contractId))
        if quantity is not None:
            record.setValue('quantity', toVariant(quantity))
        if duration is not None:
            record.setValue('duration', toVariant(duration))
        if periodicity is not None:
            record.setValue('periodicity', toVariant(periodicity))
        if aliquoticity is not None:
            record.setValue('aliquoticity', toVariant(aliquoticity))
        values = self._mapActionTypeIdToPropertyValues.get(actionTypeId, None)
        if recipe:
            fieldNameRecipe = record.fieldName(record.indexOf('recipe'))
            propertyType = values[forceString(fieldNameRecipe)]['propertyType']
            property     = action.getPropertyById(propertyType.id)
            #property.preApplyDependents(action)
            if propertyType.inActionsSelectionTable == _RECIPE:
                propertyName = propertyType.name
                if action and propertyName:
                    action[propertyName] = recipe
                record.setValue('recipe', QVariant(recipe))
            #property.applyDependents(action)
        if doses:
            fieldNameDoses = record.fieldName(record.indexOf('doses'))
            propertyType = values[forceString(fieldNameDoses)]['propertyType']
            property     = action.getPropertyById(propertyType.id)
            property.preApplyDependents(action)
            if propertyType.inActionsSelectionTable == _DOSES:
                propertyName = propertyType.name
                if action and propertyName:
                    action[propertyName] = doses
                record.setValue('doses', QVariant(doses))
            property.applyDependents(action)
        if signa:
            fieldNameSigna = record.fieldName(record.indexOf('signa'))
            propertyType = values[forceString(fieldNameSigna)]['propertyType']
            property     = action.getPropertyById(propertyType.id)
            property.preApplyDependents(action)
            if propertyType.inActionsSelectionTable == _SIGNA:
                propertyName = propertyType.name
                if action and propertyName:
                    action[propertyName] = signa
                record.setValue('signa', QVariant(signa))
            property.applyDependents(action)
        if activeSubstanceId:
            fieldNameActiveSubstance = record.fieldName(record.indexOf('activeSubstance_id'))
            propertyType = values[forceString(fieldNameActiveSubstance)]['propertyType']
            property     = action.getPropertyById(propertyType.id)
            property.preApplyDependents(action)
            if propertyType.inActionsSelectionTable == _ACTIVESUBSTANCE:
                propertyName = propertyType.name
                if action and propertyName:
                    action[propertyName] = activeSubstanceId
                record.setValue('activeSubstance_id', QVariant(activeSubstanceId))
            property.applyDependents(action)
        if piRecords:
            curDate = QDate.currentDate()
            record.setValue('directionDate', QVariant(curDate))
            record.setValue('begDate', QVariant(curDate.addDays(offset)))
            record.setValue('endDate', QVariant(None))
            actionType = action.getType()
            if actionType.isNomenclatureExpense and not actionType.isDoesNotInvolveExecutionCourse:
                action.updateExecutionPlanByRecord(forceDuration=True)
            dateIdxList = []
            piDateCount = 0
            piRecordsDuration = len(piRecords)
            for piRecord in piRecords:
                date_idx = forceInt(piRecord.value('date_idx'))
                if date_idx not in dateIdxList:
                    dateIdxList.append(date_idx)
                piDateCount = len(dateIdxList)
            actionEPDuration = action.getExecutionPlan().duration
            if piDateCount > actionEPDuration:
                ept = executionPlanType(action.getExecutionPlan())
                ept.addDaysToEP(piRecordsDuration - actionEPDuration)
                eptItems = ept.addDaysToEP(piRecordsDuration - actionEPDuration)
                if eptItems:
                    action.getExecutionPlan().items = eptItems
            executionPlanDuration = len(action.getExecutionPlan().items)
            if piRecordsDuration > executionPlanDuration:
                piDuration = piRecordsDuration - executionPlanDuration
                piItem = []
                ept = executionPlanType(action.getExecutionPlan())
                for piNew in range(0, piDuration):
                    item = ept.addNewDateTimeItem()
                    piItem.append(item)
                if piItem:
                    action.getExecutionPlan().items.extend(piItem)
            executionPlanDuration = len(action.getExecutionPlan().items)
            begDate = action.getExecutionPlan().begDate
            for epItem in action.getExecutionPlan().items:
                epItem.date = QDate()
            items = action.getExecutionPlan().items
            newItems = []
            piRecords.sort(key=lambda x: forceInt(x.value('idx')))
            for piRow, piRecord in enumerate(piRecords):
                if 0 <= piRow < executionPlanDuration:
                    epItem = items[piRow]
                    epItem.idx = forceInt(piRecord.value('idx'))
                    epItem.time = forceTime(piRecord.value('time'))
                    epItem.date = begDate.addDays(forceInt(piRecord.value('date_idx')) - 1)
                    if epItem.nomenclature:
                        epItem.nomenclature.dosage = forceDouble(piRecord.value('dosage'))
                        epItem.nomenclature.nomenclatureId = forceRef(piRecord.value('nomenclature_id'))
                        newItems.append(epItem)
            if newItems:
                action.getExecutionPlan().items = newItems
        self.insertRecord(row, record)
        rows = self._idToRows.setdefault(actionTypeId, [])
        rows.append(row)
#        action = CAction(record=record)
        action.setMedicalAidKindId(self.medicalAidKindId)
        action.updateSpecifiedName()
        self._idRowToAction[(actionTypeId, row)] = action
        self._rowToAction[row] = action
        self.prices.append(0.0)
        if not self.isRowPlanEndDateEdited(row):
            self.updatePlannedEndDate(row)
        self.emitPricesAndSumsUpdated()
        return row


    def getSelectedAction(self, actionTypeId):
        result = []
        if actionTypeId not in self._idToRows.keys():
            return result
        rows = self._idToRows[actionTypeId]
        for row in rows:
            action = self._idRowToAction[(actionTypeId, row)]
            action._actionTemplateId = forceRef(action._record.value('actionTemplateId'))
            action.updateByTemplate(forceRef(action._record.value('actionTemplateId')))
            action._record = self.getClearActionRecord(action._record)

            result.append(action)
        return result


    def getPropertyTypeCellsSettings(self, actionTypeId, row):
        cellSettings = {}
        actionType = CActionTypeCache.getById(actionTypeId)
        toothEists = False
        for propertyType in actionType.getPropertiesById().values():
            if propertyType.inActionsSelectionTable:
                column = self._propertyColsIndexes[propertyType.inActionsSelectionTable-1]
                result = self._mapPropertyTypeCellsActivity.get((row, column), None)
                if result is None:
                    self._cols[column].setValueType(propertyType.valueType.variantType)
                    self._mapPropertyTypeCellsActivity[(row, column)] = True
                    cellName = self._propertyColsNames[propertyType.inActionsSelectionTable-1]
                    cellSettings[cellName] = True
                    values = self._mapActionTypeIdToPropertyValues.get(actionTypeId, None)
                    if values is None:
                        values = {cellName: {'propertyType': propertyType, 'value':QVariant()}}
                        self._mapActionTypeIdToPropertyValues[actionTypeId] = values
                    else:
                        values[cellName] = {'propertyType': propertyType, 'value':QVariant()}

            if isinstance(propertyType.valueType, CToothActionPropertyValueType) and not toothEists: # wtf
                column = self.getColIndex(u'tooth')
                result = self._mapPropertyTypeCellsActivity.get((row, column), None)
                if result is None:
                    self._cols[column].setValueType(propertyType.valueType.variantType)
                    self._mapPropertyTypeCellsActivity[(row, column)] = True
                    cellName = u'tooth'
                    cellSettings[cellName] = True
                    values = self._mapActionTypeIdToPropertyValues.get(actionTypeId, None)
                    if values is None:
                        values = {cellName: {'propertyType': propertyType, 'value':QVariant()}}
                        self._mapActionTypeIdToPropertyValues[actionTypeId] = values
                    else:
                        values[cellName] = {'propertyType': propertyType, 'value':QVariant()}
                toothEists = True
        return cellSettings


    def removeAll(self):
        self.removeRows(0, len(self._items))
        self._idToRows.clear()
        self._rowToAction.clear()
        self._idRowToAction.clear()
        self._items = []
        self.prices = []
        self.emitPricesAndSumsUpdated()


    def remove(self, actionTypeId):
        rows = self._idToRows.get(actionTypeId, [])
        deletedRows = []
        for row in rows:
            rowShift = 0
            for deletedRow in deletedRows:
                rowShift = rowShift+1 if row > deletedRow else rowShift
            self.removeRows(row-rowShift, 1)
            deletedRows.append(row)
            action = self._rowToAction.pop(row)
            jobTicketId = action.findFireableJobTicketId()
            for i in self._rowToAction:
                otherAction = self._rowToAction[i]
                otherJobTicketId = otherAction.findFireableJobTicketId()
                if jobTicketId == otherJobTicketId:
                    jobTicketId = None
                    break
            if jobTicketId:
                QtGui.qApp.jobTicketReserveHolder.delJobTicketReservation(jobTicketId)
        self._idRowToAction.clear()
        self._idToRows.clear()

        tmpRowToAction = {}
        tmpPrices = []
        for newRow, (oldRow, action) in enumerate(self._rowToAction.items()):
            actionTypeId = action.getType().id
            tmpRowToAction[newRow] = action
            self._idRowToAction[(actionTypeId, newRow)] = action
            rows = self._idToRows.setdefault(actionTypeId, [])
            rows.append(newRow)

            tmpPrices.append(self.prices[oldRow])

        self.prices = tmpPrices
        self._rowToAction = tmpRowToAction

        self.emitPricesAndSumsUpdated()



    def getEmptyRecord(self, propertyTypeCellsSettings={}):
        record = self._table.newRecord()
        for col in self._cols:
            if col.fieldName() not in self._dbFieldNamesList:
                record.append(QtSql.QSqlField(col.fieldName(), col.valueType()))
        for name in self._propertyColsNames:
            isActive = propertyTypeCellsSettings.get(name, False)
            if not isActive:
                record.setValue(name, QVariant(u'----'))
        return record


    def hasExistsInSelected(self):
        for id in self._idToRows.keys():
            if self._existsActionsModel.hasActionTypeId(id):
                return True
        return False


    def flags(self, index):
        column = index.column()
        if column == self.getColIndex('MKB'):
            action = self._rowToAction[index.row()]
            actionType = action.getType()
            if actionType.defaultMKB == CActionType.dmkbNotUsed:
                return Qt.ItemIsSelectable # | Qt.ItemIsEnabled
        if column in [self.getColIndex('quantity'), self.getColIndex('duration'), self.getColIndex('periodicity'), self.getColIndex('aliquoticity')]:
            action = self._rowToAction[index.row()]
            actionType = action.getType()
            if column == self.getColIndex('quantity') and not actionType.isDoesNotInvolveExecutionCourse:
                return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return CRecordListModel.flags(self, index)


    def data(self, index, role=Qt.DisplayRole):
        column = index.column()

        if column == self.getColIndex('doses') and role in (Qt.StatusTipRole, Qt.DisplayRole):
            row = index.row()
            col = self._cols[column]
            record = self._items[row]
            return col.toString(index, record.value(col.fieldName()), record)

        if role == Qt.DisplayRole:
            if column == self.getColIndex('actionType_id'):
                row = index.row()
                record = self._items[row]
                outName = forceString(record.value('specifiedName'))
                actionTypeId = forceRef(record.value('actionType_id'))
                if actionTypeId:
                    actionType = CActionTypeCache.getById(actionTypeId)
                    if actionType:
                        actionTypeName = u' | '.join([actionType.code, actionType.name])
                        outName = actionTypeName + ' ' +outName if outName else actionTypeName
                    return QVariant(outName)

            elif column in self._propertyColsIndexes:
                row                 = index.row()
                actionTypeId        = forceRef(self._items[row].value('actionType_id'))
                values              = self._mapActionTypeIdToPropertyValues.get(actionTypeId, None)
                if values:
                    fieldName           = self._cols[column].fieldName()
                    cellValues          = values.get(fieldName, None)
                    if cellValues:
                        action              = self._idRowToAction[(actionTypeId, row)]
                        propertyType        = cellValues['propertyType']
                        property            = action.getPropertyById(propertyType.id)
                        return toVariant(property.getText())

        elif role == Qt.FontRole:
            row = index.row()
            record = self._items[row]
            actionTypeId = forceRef(record.value('actionType_id'))
            if self._existsActionsModel and self._existsActionsModel.hasActionTypeId(actionTypeId):
                return self._qBoldFont
        elif role == Qt.BackgroundRole and column == self.getColIndex('checked'):
            row = index.row()
            record = self._items[row]
            actionTypeId = forceRef(record.value('actionType_id'))
            return self._actionTypesModel.getColor(actionTypeId)
        return CRecordListModel.data(self, index, role)


    def setSelected(self, actionTypeId, row, value):
        if len(self._idToRows[actionTypeId]) == 1:
            self.parentWidget.setSelected(actionTypeId, value, resetMainModel=True)
        else:
            self.removeRows(row, 1)
            del self._rowToAction[row]
            self._idRowToAction.clear()
            self._idToRows.clear()
            tmpRowToAction = {}
            tmpPrices = []
            for newRow, (oldRow, action) in enumerate(self._rowToAction.items()):
                actionTypeId = action.getType().id
                tmpRowToAction[newRow] = action
                self._idRowToAction[(actionTypeId, newRow)] = action
                rows = self._idToRows.setdefault(actionTypeId, [])
                rows.append(newRow)
                tmpPrices.append(self.prices[oldRow])

            self.prices = tmpPrices
            self._rowToAction = tmpRowToAction

            self.emitPricesAndSumsUpdated()


    def setData(self, index, value, role=Qt.EditRole):
        column = index.column()
        row = index.row()
        record = self._items[row]
        if role == Qt.CheckStateRole:
            if column == 0:
                actionTypeId = forceRef(record.value('actionType_id'))
                self.setSelected(actionTypeId, row, forceInt(value) == Qt.Checked)
                return False
            elif column == record.indexOf('isUrgent'):
                record.setValue('isUrgent', toVariant(forceInt(value) == Qt.Checked))
                self.emitValueChanged(row, 'isUrgent')
                return False

        col = self.cols()[column]
        fieldName = col.fieldName()

        if fieldName == 'directionDate':
            begDate = forceDateTime(record.value('begDate'))
            if begDate and begDate < forceDateTime(value):
                return False
        elif fieldName == 'begDate':
            directionDate = forceDateTime(record.value('directionDate'))
            if directionDate and directionDate > forceDateTime(value):
                return False

        result = CRecordListModel.setData(self, index, value, role)

        actionType = CActionTypeCache.getById(forceRef(record.value('actionType_id')))
        if fieldName == 'finance_id':
            self.initContract(row)
            self.updatePricesAndSums(row, row)
        elif fieldName == 'contract_id':
            self.updatePricesAndSums(row, row)
        elif fieldName == 'amount':
            amount = forceDouble(value)
            actionTypeId = forceRef(record.value('actionType_id'))
            personId = forceRef(record.value('person_id'))
            financeId = forceRef(record.value('finance_id'))
            contractId = forceRef(record.value('contract_id'))
            eventEditor = self.parentWidget.eventEditor
            uet = amount*eventEditor.getUet(actionTypeId, personId, financeId, contractId)
            record.setValue('uet', toVariant(uet))
            self.updatePricesAndSums(row, row)
            if self.isRowDpedBegDatePlusAmount(row):
                self.updatePlannedEndDate(row)
            actionType = CActionTypeCache.getById(forceRef(record.value('actionType_id')))
            action = self._idRowToAction[(actionTypeId, row)]
            if actionType and action and actionType.isNomenclatureExpense and action.nomenclatureExpense:
                action.nomenclatureExpense._actionAmount = amount
                action.nomenclatureExpense.set(actionType=actionType)
#        elif fieldName == 'quantity' and not actionType.isNomenclatureExpense:
#            self.updateExecutionPlanByRecord(row)
        elif fieldName == 'duration':
            if not actionType.isNomenclatureExpense:
                pass
#                duration = forceInt(record.value('duration'))
#                if duration > 0:
#                    record.setValue('quantity', toVariant(calcQuantity(record)))
#                if forceInt(record.value('quantity')):
#                    self.updatePlannedEndDate(row)
#                    self.updateExecutionPlanByRecord(row)
            else:
                self.updatePlannedEndDate(row)
                if actionType.isDoesNotInvolveExecutionCourse:
                    actionTypeId = forceRef(record.value('actionType_id'))
                    self.updateNomenclatureDosage(actionTypeId, actionType, record, row)
                self.updateExecutionPlanByRecord(row)
        elif fieldName == 'periodicity':
            if not actionType.isNomenclatureExpense:
                pass
#                if not forceInt(record.value('quantity')) or forceInt(record.value('duration')) > 0:
#                    record.setValue('quantity', toVariant(calcQuantity(record)))
#                if forceInt(record.value('quantity')):
#                    self.updateExecutionPlanByRecord(row)
            else:
                if actionType.isDoesNotInvolveExecutionCourse:
                    actionTypeId = forceRef(record.value('actionType_id'))
                    self.updateNomenclatureDosage(actionTypeId, actionType, record, row)
                self.updateExecutionPlanByRecord(row)
        elif fieldName == 'aliquoticity':
            if not actionType.isNomenclatureExpense:
                pass
#                if not forceInt(record.value('quantity')) or forceInt(record.value('duration')) > 0:
#                    record.setValue('quantity', toVariant(calcQuantity(record)))
#                if forceInt(record.value('quantity')):
#                    self.updateExecutionPlanByRecord(row)
            else:
                if actionType.isDoesNotInvolveExecutionCourse:
                    actionTypeId = forceRef(record.value('actionType_id'))
                    self.updateNomenclatureDosage(actionTypeId, actionType, record, row)
                self.updateExecutionPlanByRecord(row)
        elif fieldName == 'begDate':
            actionType = CActionTypeCache.getById(forceRef(record.value('actionType_id')))
            if actionType.defaultEndDate == CActionType.dedSyncActionBegDate:
                record.setValue('endDate', toVariant(record.value('begDate')))
            if forceInt(record.value('quantity')) <= 1:
                self.updatePlannedEndDate(row)
            if actionType.isNomenclatureExpense:
                self.updateExecutionPlanByRecord(row)
        elif fieldName == 'recipe':
            actionTypeId        = forceRef(record.value('actionType_id'))
            action              = self._idRowToAction[(actionTypeId, row)]
            values              = self._mapActionTypeIdToPropertyValues.get(actionTypeId, None)
            propertyType        = values[fieldName]['propertyType']
            property            = action.getPropertyById(propertyType.id)
            property.preApplyDependents(action)

            if isinstance(propertyType.valueType, CNomenclatureActionPropertyValueType):
                (nomenclatureId, financeId) = value
                record.setValue('recipe', toVariant(nomenclatureId))
                if nomenclatureId:
                    if financeId:
                        self.setData(self.index(row, self.getColIndex('finance_id')), toVariant(financeId))
                    nomenclatureValues = _getNomenclatureValues(nomenclatureId, self._nomenclatureCache)
                    dosageValue = nomenclatureValues.get('dosageValue')
                    dosesColumnIndex = self.getColIndex('doses')
                    dosesIndex = self.index(row, dosesColumnIndex)
                    dosesPropertyType = values['doses']['propertyType']
                    dosesProperty = action.getPropertyById(dosesPropertyType.id)
                    dosesProperty.setValue(dosageValue)
                    self.setData(dosesIndex, toVariant(dosageValue))

                    usingTypes = self.getNomenclatureUsingTypes(nomenclatureId)
                    if usingTypes:
                        signaValues = values.get('signa')
                        if signaValues:
                            signaPropertyType = signaValues['propertyType']
                            if isinstance(signaPropertyType.valueType, CNomenclatureUsingTypeActionPropertyValueType):
                                signaProperty = action.getPropertyById(signaPropertyType.id)
                                signaProperty.setValue(usingTypes[0])
                                signaColumnIndex = self.getColIndex('signa')
                                signaIndex = self.index(row, signaColumnIndex)
                                self.setData(signaIndex, toVariant(usingTypes[0]))

            #property.applyDependents(action)

        elif fieldName == 'doses':
            actionTypeId = forceRef(record.value('actionType_id'))
            action = self._idRowToAction[(actionTypeId, row)]
            values = self._mapActionTypeIdToPropertyValues.get(actionTypeId, None)
            if values:
                propertyType = values['recipe']['propertyType']
                if isinstance(propertyType.valueType, CNomenclatureActionPropertyValueType):
                    property = action.getPropertyById(propertyType.id)
                    nomenclatureId = property.getValue()
                    if nomenclatureId:
                        action.updateNomenclatureDosageValue(nomenclatureId, forceDouble(value), force=True)
        return result


    def updateNomenclatureDosage(self, actionTypeId, actionType, record, row):
        actionTypeId = forceRef(record.value('actionType_id'))
        action = self._idRowToAction[(actionTypeId, row)]
        values = self._mapActionTypeIdToPropertyValues.get(actionTypeId, None)
        if values:
            propertyType = values['recipe']['propertyType']
            if isinstance(propertyType.valueType, CNomenclatureActionPropertyValueType):
                property = action.getPropertyById(propertyType.id)
                nomenclatureId = property.getValue()
                if nomenclatureId:
                    dosesPropertyType = values['doses']['propertyType']
                    dosesProperty = action.getPropertyById(dosesPropertyType.id)
                    doses = dosesProperty.getValue()
                    action.updateNomenclatureDosageValue(nomenclatureId, forceDouble(doses), force=True)
                    if actionType.isNomenclatureExpense:
                        self.updateExecutionPlanByRecord(row)


    def updateExecutionPlanByRecord(self, row):
        actionTypeId = forceRef(self._items[row].value('actionType_id'))
        action = self._idRowToAction[(actionTypeId, row)]
        daysExecutionPlan = []
        actionType = action.getType()
        if actionType.isNomenclatureExpense and not actionType.isDoesNotInvolveExecutionCourse:
            action.updateExecutionPlanByRecord(daysExecutionPlan=daysExecutionPlan)
        values = self._mapActionTypeIdToPropertyValues.get(actionTypeId, None)
        if values and forceStringEx('recipe') in values.keys() and forceStringEx('doses') in values.keys():
            propertyTypeRecipe = values['recipe']['propertyType']
            if isinstance(propertyTypeRecipe.valueType, CNomenclatureActionPropertyValueType):
                propertyRecipe = action.getPropertyById(propertyTypeRecipe.id)
                nomenclatureId = propertyRecipe.getValue()
                if nomenclatureId:
                    propertyTypeDoses = values['doses']['propertyType']
                    propertyDoses = action.getPropertyById(propertyTypeDoses.id)
                    doses = propertyDoses.getValue()
                    if action.getExecutionPlan():
                        for epItem in action.getExecutionPlan().items:
                            if epItem.nomenclature:
                                epItem.nomenclature.dosage = forceDouble(doses)
                                epItem.nomenclature.nomenclatureId = forceRef(nomenclatureId)


    def updatePlannedEndDate(self, row):
        if self.isRowDpedBegDatePlusAmount(row):
            item = self.items()[row]
            begDate = forceDateTime(item.value('begDate'))
            amountValue = forceInt(item.value('amount'))
            date = begDate.addDays(amountValue-1) if begDate and amountValue else QDate()
            item.setValue('plannedEndDate', toVariant(date))
            self.emitValueChanged(row, 'plannedEndDate')
        else:
            item = self.items()[row]
            begDate = forceDateTime(item.value('begDate'))
            durationValue = forceInt(item.value('duration'))
            date = begDate.addDays(durationValue-1) if begDate and durationValue else QDate()
            item.setValue('plannedEndDate', toVariant(date))
            self.emitValueChanged(row, 'plannedEndDate')


    def updateEndDate(self, row):
        item = self.items()[row]
        begDate = forceDateTime(item.value('begDate'))
        directionDate = forceDateTime(item.value('directionDate'))
        endDate = max(begDate, directionDate)
        item.setValue('endDate', toVariant(endDate))
        self.emitValueChanged(row, 'endDate')


    def initContract(self, row):
        item = self.items()[row]
        actionTypeId = forceRef(item.value('actionType_id'))
        financeId = forceRef(item.value('finance_id'))
        if financeId:
            eventEditor = self.parentWidget.eventEditor
            if financeId == eventEditor.eventFinanceId and getEventActionContract(eventEditor.eventTypeId):
                contractId = eventEditor.contractId
            else:
                begDate = forceDate(item.value('directionDate'))
                endDate = forceDate(item.value('endDate'))
                contractId = getActionDefaultContractId(self.parentWidget.eventEditor,
                                                        actionTypeId,
                                                        financeId,
                                                        begDate,
                                                        endDate,
                                                        None)
        else:
            contractId = None
        item.setValue('contract_id', toVariant(contractId))
        self.emitValueChanged(row, 'contract_id')

    def getTotalSum(self):
        result = 0
        for item in self._items:
            result += forceDouble(item.value('price'))
        return result

    def updatePricesAndSums(self, top, bottom):
        sumChanged = False
        for i in xrange(top, bottom+1):
            sumChanged = self.updatePriceAndSum(i, self.items()[i]) or sumChanged
        self.emitPricesAndSumsUpdated()

    def emitPricesAndSumsUpdated(self):
        self.emit(SIGNAL('pricesAndSumsUpdated()'))


    def updatePriceAndSum(self, row, item):
        actionTypeId = forceRef(item.value('actionType_id'))
        eventEditor = self.parentWidget.eventEditor
        if actionTypeId:
            contractId = forceRef(item.value('contract_id'))
            if contractId and contractId != eventEditor.contractId:
                financeId = forceRef(QtGui.qApp.db.translate('Contract', 'id', contractId, 'finance_id'))
            else:
                contractId = eventEditor.contractId
                financeId = eventEditor.eventFinanceId
            priceEx = self.getPriceEx(actionTypeId, contractId, financeId)
            price = (priceEx if priceEx is not None else 0.0) * forceDouble(item.value('amount'))
        else:
            price = 0.0
        if self.prices[row] != price:
            self.prices[row] = price
            item.setValue('price', price)
            self.emitValueChanged(row, 'price')


    def createEditor(self, index, parent):
        column = index.column()
        if column in self._propertyColsIndexes:
            return self.createPropertyEditor(index, parent)
        else:
            return CRecordListModel.createEditor(self, index, parent)

    def createPropertyEditor(self, index, parent):
        row          = index.row()
        column       = index.column()
        actionTypeId = forceRef(self._items[row].value('actionType_id'))
        values       = self._mapActionTypeIdToPropertyValues.get(actionTypeId, None)
        fieldName    = self._cols[column].fieldName()
        cellValues   = values[fieldName]
        propertyType = cellValues['propertyType']
        eventEditor  = self.parentWidget.eventEditor
        # actionType = CActionTypeCache.getById(actionTypeId)
        action = self._idRowToAction[(actionTypeId, row)]
        # action = CAction(actionType)
        if column == self.getColIndex(u'recipe') or column == self.getColIndex(u'activeSubstance_id'):
            editor       = propertyType.createEditor(action, parent, self.clientId, eventEditor.eventTypeId,  eventEditor)
        else:
            editor       = propertyType.createEditor(action, parent, self.clientId, eventEditor.eventTypeId)

        if propertyType.inActionsSelectionTable == _SIGNA:  # signa
            if isinstance(propertyType.valueType, CStringActionPropertyValueType):
                recipeCellValues = values.get('recipe')
                if not recipeCellValues:
                    return editor

                recipePropertyType = recipeCellValues['propertyType']
                if not isinstance(recipePropertyType.valueType, CNomenclatureActionPropertyValueType):
                    return editor

                recipeProperty = action.getPropertyById(recipePropertyType.id)
                nomenclatureId = recipeProperty.getValue()
                if not nomenclatureId:
                    return editor

                usingTypes = self.getNomenclatureUsingTypes(nomenclatureId)
                if not usingTypes:
                    return editor

                if not isinstance(editor, QtGui.QComboBox):
                    editorClass = propertyType.valueType.CComboBoxPropEditor
                    editor = editorClass(
                        action, propertyType.valueType.domain, parent, self.clientId, eventEditor.eventTypeId
                    )

                editor.addItems(usingTypes)

        return editor

    def getNomenclatureUsingTypes(self, nomenclatureId):
        if not nomenclatureId:
            return []

        db = QtGui.qApp.db
        table = db.table('rbNomenclature_UsingType')
        recordList = db.getRecordList(
            table, [table['usingType_id']], where=table['master_id'].eq(nomenclatureId), order=table['idx'].name()
        )
        return [forceRef(r.value('usingType_id')) for r in recordList]


    def setEditorData(self, index, editor, value, record):
        column = index.column()
        if column in self._propertyColsIndexes:
            return self.setPropertyEditorData(index, editor, value, record)
        else:
            return CRecordListModel.setEditorData(self, column, editor, value, record)

    def setPropertyEditorData(self, index, editor, value, record):
        editor.setValue(value)


    def getEditorData(self, index, editor):
        column = index.column()
        if column in self._propertyColsIndexes:
            return self.getPropertyEditorData(index, editor)
        else:
            return CRecordListModel.getEditorData(self, column, editor)


    def getPropertyEditorData(self, index, editor):
        value               = editor.value()
        row                 = index.row()
        column              = index.column()
        actionTypeId        = forceRef(self._items[row].value('actionType_id'))
        values              = self._mapActionTypeIdToPropertyValues.get(actionTypeId, None)
        fieldName           = self._cols[column].fieldName()
        cellValues          = values[fieldName]
        cellValues['value'] = toVariant(value)
        action              = self._idRowToAction[(actionTypeId, row)]
        propertyType        = cellValues['propertyType']
        property            = action.getPropertyById(propertyType.id)
        value = propertyType.convertQVariantToPyValue(value) if type(value) == QVariant else value
        property.setValue(value)
        if property.isActionNameSpecifier():
            action.updateSpecifiedName()
            self.emitValueChanged(row, 'actionType_id')
        if column == self.getColIndex(u'recipe'):
            if hasattr(editor, '_popup'):
                if hasattr(editor._popup, '_financeId'):
                    return (value,  editor._popup._financeId)
            return (value,  None)
        return value

# ###########################################################

class CCheckedActionsItemDelegate(CLocItemDelegate):
    def __init__(self, parent):
        CLocItemDelegate.__init__(self, parent)
        self._nomenclatureCaches = {}
        self.orgStructureId = None


    def setOrgStructureId(self, value):
        self.orgStructureId = value


    def getNomenclatureCaches(self, nomenclatureId):
        if nomenclatureId not in self._nomenclatureCaches.keys():
            db = QtGui.qApp.db
            record = db.getRecord('rbNomenclature', '*', nomenclatureId)
            if record:
                self._nomenclatureCaches[nomenclatureId] = record
        return self._nomenclatureCaches.get(nomenclatureId, None)
    
    
    def createEditor(self, parent, option, index):
        column = index.column()
        editor = index.model().createEditor(index, parent)
        model = index.model()
        items = model.items()
        row = index.row()
        if index.isValid() and column in [model.getColIndex('directionDate'), model.getColIndex('begDate')]:
            if row >= 0 and row < len(items):
                if column == model.getColIndex('begDate'):
                    editor.setMinimumDate(forceDate(items[row].value('directionDate')))
                if column == model.getColIndex('directionDate'):
                    editor.setMaximumDate(forceDate(items[row].value('begDate')))
        elif index.isValid() and column == model.getColIndex('recipe') and row >= 0 and row < len(items):
            nomenclatureId = forceRef(items[row].value('recipe'))
            if nomenclatureId:
                nomenclatureRecord = self.getNomenclatureCaches(nomenclatureId)
                if nomenclatureRecord:
                    editor.setFindNomenclatureName(forceStringEx(nomenclatureRecord.value('name')))
            if self.orgStructureId:
                editor.setOrgStructureId(self.orgStructureId)
        self.connect(editor, SIGNAL('commit()'), self.emitCommitData)
        self.connect(editor, SIGNAL('editingFinished()'), self.commitAndCloseEditor)
        self.editor   = editor
        self.row      = index.row()
        self.rowcount = index.model().rowCount(None)
        self.column   = column
        return editor


    def setEditorData(self, editor, index):
        if editor is not None:
            row    = index.row()
            model  = index.model()
            if row < len(model.items()):
                record = model.items()[row]
            else:
                record = model.getEmptyRecord()
            model.setEditorData(index, editor, model.data(index, Qt.EditRole), record)


    def setModelData(self, editor, model, index):
        if editor is not None:
            model.setData(index, index.model().getEditorData(index, editor))


    def updateEditorGeometry(self, editor, option, index):
        def checkOnTextEdit(widget):
            if isinstance(widget, QtGui.QTextEdit):
                return True
            for child in widget.children():
                if checkOnTextEdit(child):
                    return True
            return False
        CLocItemDelegate.updateEditorGeometry(self, editor, option, index)
        if checkOnTextEdit(editor):
            editor.resize(editor.width(), 8*editor.height())


class CCheckedActionsTableView(CInDocTableView):
    def __init__(self, parent):
        CInDocTableView.__init__(self, parent)
        self.setItemDelegate(CCheckedActionsItemDelegate(self))
        self.__actGetExecutionPlan = None
        self.__actInsertSameAction = None
        self.__actSelectAllUrgentAction = None
        self.__actClearSelectionUrgentAction = None
        self.orgStructureId = None

    
    def setOrgStructureId(self, value):
        self.orgStructureId = value
        self.itemDelegate().setOrgStructureId(self.orgStructureId)


    def addGetExecutionPlan(self):
        if self._popupMenu is None:
            self.createPopupMenu()
        self.__actGetExecutionPlan = QtGui.QAction(u'План выполнения назначений', self)
        self.__actGetExecutionPlan.setObjectName('actGetExecutionPlan')
        self.__actGetExecutionPlan.setShortcut(Qt.Key_F2)
        self.addAction(self.__actGetExecutionPlan)
        self._popupMenu.addAction(self.__actGetExecutionPlan)
        self.connect(self.__actGetExecutionPlan, SIGNAL('triggered()'), self.getExecutionPlan)


    def addInsertSameAction(self):
        if self._popupMenu is None:
            self.createPopupMenu()
        self.__actInsertSameAction = QtGui.QAction(u'Добавить действие подобного типа', self)
        self.__actInsertSameAction.setShortcut(Qt.Key_F9)
        self.addAction(self.__actInsertSameAction)
        self._popupMenu.addAction(self.__actInsertSameAction)
        self.connect(self.__actInsertSameAction, SIGNAL('triggered()'), self.on_insertSameAction)


    def addSelectAllUrgentAction(self):
        if self._popupMenu is None:
            self.createPopupMenu()
        self.__actSelectAllUrgentAction = QtGui.QAction(u'Установить всем признак "Срочный"', self)
        self.addAction(self.__actSelectAllUrgentAction)
        self._popupMenu.addAction(self.__actSelectAllUrgentAction)
        self.connect(self.__actSelectAllUrgentAction, SIGNAL('triggered()'), self.on_selectAllUrgentAction)


    def addClearSelectionUrgentAction(self):
        if self._popupMenu is None:
            self.createPopupMenu()
        self.__actClearSelectionUrgentAction = QtGui.QAction(u'Снять у всех признак "Срочный"', self)
        self.addAction(self.__actClearSelectionUrgentAction)
        self._popupMenu.addAction(self.__actClearSelectionUrgentAction)
        self.connect(self.__actClearSelectionUrgentAction, SIGNAL('triggered()'), self.on_clearSelectionUrgentAction)


    def on_insertSameAction(self):
        currentIndex = self.currentIndex()
        self.model().insertSameActionByRow(currentIndex.row())


    def getExecutionPlan(self):
        currentRow = self.currentIndex().row()
        model = self.model()
        items = model.items()
        if 0 <= currentRow < len(items):
            actionTypeId = forceRef(items[currentRow].value('actionType_id'))
            action = model._idRowToAction[(actionTypeId, currentRow)] if actionTypeId else None
            record = action.getRecord() if action else None
            if record and action:
                orgStructureIdList = []
                if not action.getType().isNomenclatureExpense:
                    currentOrgStructureId = QtGui.qApp.currentOrgStructureId()
                    userOrgStructureId = QtGui.qApp.userOrgStructureId
                    currentOrgStructureIdList = []
                    userOrgStructureIdList = []
                    db = QtGui.qApp.db
                    tableOrgStructure = db.table('OrgStructure')
                    if currentOrgStructureId:
                        recordOS = db.getRecordEx(tableOrgStructure, [tableOrgStructure['parent_id']], [tableOrgStructure['id'].eq(currentOrgStructureId), tableOrgStructure['deleted'].eq(0)])
                        parentOSId = forceRef(recordOS.value('parent_id')) if recordOS else None
                        currentOrgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', parentOSId if parentOSId else currentOrgStructureId)
                    if userOrgStructureId:
                        recordOS = db.getRecordEx(tableOrgStructure, [tableOrgStructure['parent_id']], [tableOrgStructure['id'].eq(userOrgStructureId), tableOrgStructure['deleted'].eq(0)])
                        parentOSId = forceRef(recordOS.value('parent_id')) if recordOS else None
                        userOrgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', parentOSId if parentOSId else userOrgStructureId)
                    orgStructureIdList = list(set(currentOrgStructureIdList)|set(userOrgStructureIdList))
                dialog = CGetExecutionPlan(self, record, action.getExecutionPlan(), action = action, orgStructureIdList = orgStructureIdList)
#                dialog.setVisibleBtn(True)
                dialog.exec_()
                if action.getType().isNomenclatureExpense:
                    begDate = forceDateTime(record.value('begDate'))
                    duration = forceInt(record.value('duration'))
                    record.setValue('plannedEndDate', toVariant(begDate.addDays(duration-1)))
                    record.setValue('periodicity', toVariant(forceInt(action.getRecord().value('periodicity'))))
                    if action.executionPlanManager:
                        action.executionPlanManager.recountOrder()
                else:
                    dateTimeExecJob = None
                    execOrgStructureId = dialog.getOrgStructureId()
                    executionPlan = action.getExecutionPlan()
                    if executionPlan:
                        items = executionPlan.items
                        if items:
                            sortedItemsByDate = sorted(items, key=lambda x: x.date.toPyDate(), reverse=False)
                            for item in sortedItemsByDate:
                                if bool(item.date):
                                    dateTimeExecJob = item.date
                                    break
                        record.setValue('duration', toVariant(forceInt(action.getRecord().value('duration'))))
                        record.setValue('periodicity', toVariant(forceInt(action.getRecord().value('periodicity'))))
                        record.setValue('aliquoticity', toVariant(forceInt(action.getRecord().value('aliquoticity'))))
                        record.setValue('quantity', toVariant(forceInt(action.getRecord().value('quantity'))))
                        if dateTimeExecJob:
                            begDateTimeAction = forceDateTime(record.value('begDate'))
                            begTimeAction = begDateTimeAction.time() if begDateTimeAction else QTime()
                            newBegDateTime = QDateTime(dateTimeExecJob, begTimeAction)
                            record.setValue('begDate', toVariant(newBegDateTime))
                            directionDate = forceDate(record.value('directionDate'))
                            plannedEndDate = None
                            if directionDate:
                                defaultPlannedEndDate = action.getType().defaultPlannedEndDate
                                if defaultPlannedEndDate == CActionType.dpedNextDay:
                                    plannedEndDate = directionDate.addDays(1)
                                elif defaultPlannedEndDate == CActionType.dpedNextWorkDay:
                                    plannedEndDate = addWorkDays(directionDate, 1, wpFiveDays)
                            if defaultPlannedEndDate == CActionType.dpedJobTicketDate:
                                plannedEndDate = dateTimeExecJob
                            begDate = forceDate(record.value('begDate'))
                            if begDate:
                                if defaultPlannedEndDate == CActionType.dpedBegDatePlusAmount:
                                    plannedEndDate = begDate.addDays(dialog.quantityExec)
                                elif defaultPlannedEndDate == CActionType.dpedBegDatePlusDuration:
                                    plannedEndDate = begDate.addDays(dialog.duration)
                            record.setValue('plannedEndDate', toVariant(plannedEndDate))
                            #record.setValue('plannedEndDate', toVariant(dateTimeExecJob.addDays(dialog.quantityExec-1)))
                            for property in action.getType()._propertiesById.itervalues():
                                if property.isJobTicketValueType() and property.valueType.initPresetValue:
                                    prop = action.getPropertyById(property.id)
                                    if prop._type:
                                        prop._type.valueType.setIsExceedJobTicket(True)
                                        prop._type.valueType.setIsNearestJobTicket(True)
                                        prop._type.valueType.setDateTimeExecJob(dateTimeExecJob)
                                        prop._type.valueType.setExecOrgStructureId(execOrgStructureId)
    #                                    QtGui.qApp.setJTR(self)
    #                                    try:
    #                                        #prop._value = prop._type.valueType.getPresetValueWithoutAutomatic(action)
    #                                        prop._type.valueType.resetParams()
    #                                        prop._changed = True
    #                                    finally:
    #                                        QtGui.qApp.unsetJTR(self)
                            self.model()._idRowToAction[(actionTypeId, currentRow)] = action
                        else:
                            begDate = forceDateTime(record.value('begDate'))
                            record.setValue('plannedEndDate', toVariant(begDate.addDays(dialog.quantityExec-1)))
                        #action.executionPlanManager.recountOrder()
                        #action.executionPlanManager.recountMixedOrder()
                    else:
                        record.setValue('duration', toVariant(None))
                        record.setValue('periodicity', toVariant(None))
                        record.setValue('aliquoticity', toVariant(None))
                        record.setValue('quantity', toVariant(None))


    def on_selectAllUrgentAction(self):
        model = self.model()
        items = model.items()
        for row, item in enumerate(items):
            actionTypeId = forceRef(item.value('actionType_id'))
            action = model._idRowToAction[(actionTypeId, row)] if actionTypeId else None
            if action:
                action.getRecord().setValue('isUrgent', toVariant(True))
                self.model()._idRowToAction[(actionTypeId, row)] = action


    def on_clearSelectionUrgentAction(self):
        model = self.model()
        items = model.items()
        for row, item in enumerate(items):
            actionTypeId = forceRef(item.value('actionType_id'))
            action = model._idRowToAction[(actionTypeId, row)] if actionTypeId else None
            if action:
                action.getRecord().setValue('isUrgent', toVariant(False))
                self.model()._idRowToAction[(actionTypeId, row)] = action


    def on_popupMenu_aboutToShow(self):
        row = self.currentIndex().row()
        rowCount = len(self.model().items())
        if self.__actGetExecutionPlan:
            enable = 0<=row<rowCount
            if enable:
                model = self.model()
                item = model.items()[row]
                actionTypeId = forceRef(item.value('actionType_id'))
                action = model._idRowToAction[(actionTypeId, row)] if actionTypeId else None
                enable = (enable and action and not action.getType().isDoesNotInvolveExecutionCourse)
            self.__actGetExecutionPlan.setEnabled(enable)
        if self.__actInsertSameAction:
            self.__actInsertSameAction.setEnabled(0<=row<rowCount)
        if self.__actSelectAllUrgentAction:
            self.__actSelectAllUrgentAction.setEnabled(0<=row<rowCount)
        if self.__actClearSelectionUrgentAction:
            self.__actClearSelectionUrgentAction.setEnabled(0<=row<rowCount)

