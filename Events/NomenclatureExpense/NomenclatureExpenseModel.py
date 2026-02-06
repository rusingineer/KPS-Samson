# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2024 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

import itertools

from Events.ActionsModel import CActionRecordItem

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt, QVariant, QDateTime

from Events.Action import CAction, CActionTypeCache
from Events.ExecutionPlan.Groups import CExecutionPlanProxyModelGroup
from Events.ActionStatus  import CActionStatus
from Events.ActionProperty import CActionPropertyValueTypeRegistry
from Events.Utils        import calcQuantity, calcQuantityEx, getLfFormIdList
from Events.PropertyValueToTemplateComboBox import CPropertyValueToTemplateComboBox
#from Events.ExecutionPlan.Groups import CActionExecutionPlanGroup
from Stock.NomenclatureComboBox import CNomenclatureComboBox
from Stock.Utils                import getExistsNomenclatureAmount
from Orgs.OrgStructComboBoxes   import COrgStructureComboBox
from Orgs.Utils                 import getOrgStructureName #, getOrgStructureFullName
from library.ESKLP.SmnnNomenclatureExpenseComboBox import CSmnnNomenclatureExpenseComboBox
from library.ESKLP.GrlsLfNomenclatureExpenseComboBox import CGrlsLfNomenclatureExpenseComboBox
from library.DateEdit import CDateEdit
from library.DateTimeEdit import CDateTimeEdit
from library.ROComboBox import CROEditableComboBox
from library.crbcombobox import CRBComboBox
from library.Utils import forceDate, forceRef, forceString, forceDouble, forceInt, toVariant, forceStringEx, trim, forceDateTime, forceTime
from Events.NomenclatureExpense.Utils import (
    ORGSTRUCTURE_INDEX,
    GROUPING_INDEX,
    SCHEME_INDEX,
    DIREACTION_DATE_INDEX,
    BEG_DATE_INDEX,
    CANCEL_DATE_INDEX,
    SMNN_INDEX,
    SMNN_GRLSLF_INDEX,
    NOMENCLATURE_INDEX,
    REACTION_INDEX,
    PLAN_END_DATE,
    CALCULATIONPARAM_INDEX,
    DOSES_INDEX,
    SIGNA_INDEX,
    SIGNACOMMENT_INDEX,
    DURATION_INDEX,
    ALIQUOTICITY_INDEX,
    PERIODICITY_INDEX,
    NOTE_INDEX,
    CCellsSettings
)

DONE_COLOR = QtGui.QColor(Qt.green)
NOT_DONE_COLOR = QtGui.QColor(Qt.yellow)
OVERDUE_COLOR = QtGui.QColor(Qt.red)

_mapColumnIndex2ValueConverter = {
    DOSES_INDEX: forceDouble,
    SIGNA_INDEX: forceString,
    NOMENCLATURE_INDEX: forceRef
}

_mapColumnIndex2FieldName = {
    DURATION_INDEX: 'duration',
    ALIQUOTICITY_INDEX: 'aliquoticity',
    PERIODICITY_INDEX: 'periodicity'
}


class CExpenseNomenclatureComboBox(CNomenclatureComboBox):
    def __init__(self, parent):
        CNomenclatureComboBox.__init__(self, parent)


    def setValue(self, value):
        itemId = forceRef(value)
        if itemId:
#            self.setFilter('')  #0015270
            rowIndex = self._model.searchId(itemId)
            if rowIndex >= 0:
                self.setCurrentIndex(rowIndex)
        else:
            CNomenclatureComboBox.setValue(self, forceRef(value))


    def setFinanceMedicalAidKind(self, var):
        if self._financeId != self._popup._financeId:
            self.setFinanceId(self._popup._financeId)
        if self._medicalAidKindId != self._popup._medicalAidKindId:
            self.setMedicalAidKindId(self._popup._medicalAidKindId)
        self.getFilterData()
        self._filier = self._filter
        self.reloadData()
        self.setValue(var)


class CSIGNANomenclatureComboBox(CROEditableComboBox):
    def __init__(self, parent = None):
        CROEditableComboBox.__init__(self, parent)
        self.values = []


    def toString(self, val, record):
        str = forceStringEx(val).lower()
        for item in self.values:
            if trim(item.lower()) == str:
                return toVariant(item)
        if str:
            self.values.append(forceString(val))
        return toVariant(val)


    def createEditor(self, parent):
        editor = CROEditableComboBox(parent)
        for val in self.values:
            editor.addItem(val)
        return editor


    def setValues(self, values):
        self.values = values


class Col(object):
    def __init__(self, key, width, title, toolTip=u'', switchOff=True):
        self.key = key
        self.width = width
        self._title = QVariant(title)
        self._switchOff = switchOff
        self._toolTip = toolTip


    def switchOff(self):
        return self._switchOff


    def setTitle(self, title):
        self._title = toVariant(title)


    def title(self):
        return self._title


    def setToolTip(self, toolTip):
        self._toolTip = toVariant(toolTip)
        return self


    def toolTip(self):
        return self._toolTip


def _flagIteration(iterable, flag):
    for i in iterable:
        yield flag, i


class CNomenclatureExpenseModel(QtCore.QAbstractTableModel):
    STATIC_HEADERS = {
        ORGSTRUCTURE_INDEX: (u'Подразделение', 10, u'Подразделение выполнения назначения'),
        SCHEME_INDEX: (u'Схема', 10, u'Код шаблона назначения'),
        DIREACTION_DATE_INDEX: (u'Дата назначения', 10, u''),
        BEG_DATE_INDEX: (u'Дата начала', 10, u''),
        CANCEL_DATE_INDEX: (u'Дата отмены', 10, u''),
        SMNN_INDEX: (u'МНН', 10, u'Международное непатентованное наименование'),
        SMNN_GRLSLF_INDEX: (u'Форма выпуска', 10, u'Форма выпуска МНН'),
        PLAN_END_DATE: (u'План', 10, u''),
        GROUPING_INDEX: (u'|', 2, u'Группировка'),
        NOMENCLATURE_INDEX: (u'ЛС', 10, u'Лекарственное средство'),
        REACTION_INDEX: (u'Реакция на ЛС', 10, u'Реакция на лекарственное средство'),
        CALCULATIONPARAM_INDEX: (u'Параметр расчета', 10, u'Код шаблона свойства, на основании значения которого выполняется расчет дозы'),
        DOSES_INDEX: (u'Доза', 3, u'Доза на один прием'),
        SIGNA_INDEX: (u'СП', 3, u'Способ применения'),
        SIGNACOMMENT_INDEX: (u'Комментарий к СП', 10, u'Комментарий к способу применения'),
        DURATION_INDEX: (u'Д', 3, u'Длительность курса в днях'),
        ALIQUOTICITY_INDEX: (u'К', 3, u'Количество приемов в сутки (кратность)'),
        PERIODICITY_INDEX: (u'И', 3, u'Интервал между днями приема. 0 - каждый день, 1 - через 1 день, 2 - через 2 дня, 3 - через 3 дня, и т.д.'),
        NOTE_INDEX: (u'Примечание', 10, u'')
    }

    def cols(self):
        cols = []
        key = 0
        for key in sorted(self.STATIC_HEADERS.keys()):
            cols.append(Col(key, self.STATIC_HEADERS[key][1], self.STATIC_HEADERS[key][0], self.STATIC_HEADERS[key][2]))

        for monthKey in range(31):
            cols.append(Col(key+monthKey+1, 3, str(monthKey+1)))

        return cols


    def __init__(self, parent=None, date=None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self._readOnly = False
        self._isDirty = False
        self._groups = []
        self._mapGroupToCopy = {}
        self._originGroups = []
        self._newGroups = []
        self._date = date or QtCore.QDate.currentDate()
        self._cellsSettings = CCellsSettings(self)
        self._actionTypeId = None
        self._actionType = None
        self._showTime = False
        self._nomenclatureOrgStructureId = None
        self._nomenclatureId = None
        self._onlyActual = False
        self._ignoreTime = False
        self._isRequiresFillingNomenclature = False
        self._schemaId = None
        self._considerPeriod = False
        self._begDate = None
        self._endDate = None
        self._eventEditor = None
        self._stockOrgStructureId = None
        self._nomenclatureExistQntCache = {}
        self._nomenclatureAnalogCache = {}
        self._nomenclatureCaches = {}
        self._valuePropertyToTemplateItems = {}
        self._orgStructureNameCaches = {}


    def isDirty(self):
        return self._isDirty


    def setIsDirty(self, dirty=True):
        self._isDirty = dirty


    def getNomenclatureCaches(self, nomenclatureId):
        if nomenclatureId not in self._nomenclatureCaches.keys():
            db = QtGui.qApp.db
            record = db.getRecord('rbNomenclature', '*', nomenclatureId)
            if record:
                self._nomenclatureCaches[nomenclatureId] = record
        return self._nomenclatureCaches.get(nomenclatureId, None)


    def getNomenclatureAnalog(self, nomenclatureId):
        if nomenclatureId not in self._nomenclatureAnalogCache.keys():
            db = QtGui.qApp.db
            record = db.getRecord('rbNomenclature', 'analog_id', nomenclatureId)
            analogId = forceRef(record.value('analog_id')) if record else None
            self._nomenclatureAnalogCache[nomenclatureId] = analogId
        return self._nomenclatureAnalogCache.get(nomenclatureId, None)


    def groups(self):
        return self._groups


    def groupsToSavePrepare(self):
        return [g for g in self._groups if g in self._mapGroupToCopy.values()]


    def groupsToAdd(self):
        return self._newGroups


    def discardChanges(self):
        pass


    def setOrgStructureId(self, orgStructureId, isReset=True):
        self._stockOrgStructureId = orgStructureId
        self.setOriginGroups(self._originGroups, isReset=isReset)


    def setEventEditor(self, eventEditor):
        self._eventEditor = eventEditor


    def setBegDate(self, begDate):
        self._begDate = begDate
        self.setOriginGroups(self._originGroups)


    def setEndDate(self, endDate):
        self._endDate = endDate
        self.setOriginGroups(self._originGroups)


    def setActionTypeId(self, actionTypeId):
        self._actionTypeId = actionTypeId
        if self._actionTypeId:
            self._actionType = CActionTypeCache.getById(self._actionTypeId)
            self._nomenclatureOrgStructureId = self._actionType.getNomenclatureOrgStructureId()
        else:
            self._nomenclatureOrgStructureId = None
            self._actionType = None
        self._showTime = self._actionType.showTime if self._actionType else False
        self.setOriginGroups(self._originGroups)


    def setNomenclatureId(self, nomenclatureId):
        self._nomenclatureId = nomenclatureId
        self.setOriginGroups(self._originGroups)


    def setDate(self, date):
        self._date = date
        self.setOriginGroups(self._originGroups)


    def setOnlyActual(self, onlyActual):
        self._onlyActual = onlyActual
        self.setOriginGroups(self._originGroups)


    def setIgnoreTime(self, ignoreTime):
        self._ignoreTime = ignoreTime
        self.setOriginGroups(self._originGroups)


    def setIsRequiresFillingNomenclature(self, isRequiresFillingNomenclature):
        self._isRequiresFillingNomenclature = isRequiresFillingNomenclature
        self.setOriginGroups(self._originGroups)


    def setSchemaId(self, schemaId):
        self._schemaId = schemaId
        self.setOriginGroups(self._originGroups)


    def considerPeriod(self, considerPeriod):
        self._considerPeriod = considerPeriod
        self.setOriginGroups(self._originGroups)


    def rowCount(self, parent=None, *args, **kwargs):
        return len(self._groups) + 1


    def columnCount(self, parent=None, *args, **kwargs):
        return self._date.daysInMonth() + 1 + NOTE_INDEX


    def initGrouping(self, groups):
        for group in groups:
            if group.isGroupedAndSaved() and forceInt(group.currentItem._record.value('group_id')):
                if forceInt(group.currentItem._record.value('id')) == forceInt(group.currentItem._record.value('group_id')): 
                    group.setGroupingItem(group.currentItem)
                    if group.currentItem not in group.groupingInfo:
                        group.appendGroupingInfo(group.currentItem)
                else:
                    for subgroup in groups:
                        if subgroup.isGroupedAndSaved() and forceInt(subgroup.currentItem._record.value('id')) == forceInt(group.currentItem._record.value('group_id')):  
                            if group.currentItem not in subgroup.groupingInfo:
                                subgroup.appendGroupingInfo(group.currentItem)
                            group.setGroupingItem(subgroup.currentItem)
            else:
                if group.isGrouped():
                    if group.groupingItem == group.currentItem:
                        if group.currentItem not in group.groupingInfo:
                            group.appendGroupingInfo(group.currentItem)
                        group.setGroupingItem(group.currentItem)
                    else:
                        for subgroup in groups:
                            if subgroup.isGrouped() and group.groupingItem == subgroup.currentItem:
                                if group.currentItem not in subgroup.groupingInfo:
                                    subgroup.appendGroupingInfo(group.currentItem)
                                group.setGroupingItem(subgroup.currentItem)
                    
    
    
    def setOriginGroups(self, groups, isReset=True):
        self.initGrouping(groups)
        self._originGroups = groups
        groupsNoNew = []
        for g in groups:
            if g and g not in self._newGroups and g not in groupsNoNew:
                groupsNoNew.append(g)
        self._groups = []

        for isNew, group in itertools.chain(
                _flagIteration(groupsNoNew, False),
                _flagIteration(self._newGroups, True)):

            if self._stockOrgStructureId and self._stockOrgStructureId != group.lastOrgStructureId():
                continue

            if not self._actionTypeId or self._actionTypeId != group.actionTypeId:
                continue

            if self._isRequiresFillingNomenclature and group.nomenclatureId:
                continue

            if self._schemaId and self._schemaId != group.getActionTypeGroupId():
                continue

            canceled = False
            items = group.items
            for i in range(len(items)):
                if forceInt(group.items[i].action._record.value('status'))==3 and self._onlyActual:
                    canceled = True
                    break
            if canceled:
                continue

            if self._considerPeriod:
                if self._begDate and group.begDate() < self._begDate:
                    continue

                elif self._endDate and group.begDate() > self._endDate:
                    continue

            if self._date:
                begDate = group.begDate()
                begYM = (begDate.year(), begDate.month())
                planEndDate = group.planEndDate()
                planEndYM = (planEndDate.year(), planEndDate.month())
                YM = (self._date.year(), self._date.month())
                if not (begYM <= YM <= planEndYM):
                    continue

            if self._nomenclatureId and group.nomenclatureId and group.nomenclatureId != self._nomenclatureId:
                continue

            if group in self._mapGroupToCopy:
                self._groups.append(self._mapGroupToCopy[group])
            elif isNew:
                self._groups.append(group)
            else:
                copied = group.copy()
                self._mapGroupToCopy[group] = copied
                self._groups.append(copied)
        if isReset:
            self.reset()


    def _addNewGroup(self, nomenclatureId, orgStructureId = None, parentGroup = None):
        newGroup = CExecutionPlanProxyModelGroup(None)
        self._newGroups.append(newGroup)
        self._groups.append(newGroup)
        actionRecord = QtGui.qApp.db.table('Action').newRecord()
        action = CAction.getFilledAction(self._eventEditor, actionRecord, self._actionTypeId, orgStructureId=self._stockOrgStructureId)
        if orgStructureId:
            action.setOrgStructureId(orgStructureId)
        else:
            action.setOrgStructureId(self._stockOrgStructureId)
        action.updateExecutionPlanByRecord(forceDuration=True)
        item = CActionRecordItem(actionRecord, action)
        newGroup.addItem(None, item)
        self._cellsSettings.setGroupNomenclature(newGroup, nomenclatureId)
        self._cellsSettings.setGroupSigna(newGroup, self.getSignaToNomenclatureId(nomenclatureId, newGroup))
        self._cellsSettings.setGroupSignaCommentText(newGroup, forceString(self._cellsSettings.getGroupSignaCommentTypeText(newGroup)))
        doses = self._cellsSettings.getNomenclatureDoses(nomenclatureId)
        self._cellsSettings.setGroupDoses(newGroup, doses)
        self._cellsSettings.setGroupSmnn(newGroup, self._cellsSettings.getGroupSmnn(newGroup))
        self._cellsSettings.setGroupSmnnGrlsLf(newGroup, self._cellsSettings.getGroupSmnnGrlsLf(newGroup))
        newGroup = self.updateSmnn_SmnnGrlslf(newGroup, nomenclatureId, None)
        newGroup.setAliquoticity(newGroup.aliquoticity(), updateExecutionPlan=False)
        newGroup.setPeriodicity(newGroup.periodicity(), updateExecutionPlan=False)
        actionType = action.getType() if action else None
        action.setFinanceId(self._eventEditor.eventFinanceId)
        duration = newGroup.duration()
        if duration != 0:
            newGroup.setDuration(duration, updateExecutionPlan=False)
        elif duration == 0 and actionType and not actionType.isNomenclatureExpense:
            newGroup.setDuration(1, updateExecutionPlan=False)
        else:
            newGroup.setDuration(duration, updateExecutionPlan=False)
        action.updateSpecifiedName()

        if parentGroup and parentGroup.groupingItem and not newGroup.groupingItem:
            newGroup.setGroupingItem(parentGroup.groupingItem)
            action.setOrgStructureId(parentGroup.headItem.action.getOrgStructureId())
            newGroup.setDirectionDate(forceDateTime(parentGroup.headItem.action.getDirectionDate() if self._showTime else forceDate(parentGroup.headItem.action.getDirectionDate())))
            
            begDate = parentGroup.begDate()
            newGroup.setBegDate(begDate)
            begTime = forceTime(parentGroup.begTime()) if self._showTime else None
            newGroup.setBegTime(begTime)
            
            newGroup.setPlanEndDate(forceDate(parentGroup.headItem.action._record.value('plannedEndDate')))
            note = forceStringEx(newGroup.note())
            newGroup.setDuration(parentGroup.headItem.action.getDuration(), updateExecutionPlan=False)
            newGroup.setAliquoticity(parentGroup.headItem.action.getAliquoticity(), updateExecutionPlan=False)
            newGroup.setPeriodicity(parentGroup.headItem.action.getPeriodicity(), updateExecutionPlan=False)
            self.updateDosageNomenclatureByIndex(newGroup)
            newGroup.setNote(note, updateExecutionPlan=False)
            if self._cellsSettings.isNomenclatureUsingTypeActionPropertyValueType(newGroup):
                self._cellsSettings.setGroupSigna(newGroup, forceRef(self._cellsSettings.getGroupSigna(parentGroup)))
            else:
                self._cellsSettings.setGroupSigna(newGroup, forceString(self._cellsSettings.getGroupSigna(parentGroup)))
        self.calcQuantity(newGroup)
        for epItem in action.getExecutionPlan().items:
            if epItem.nomenclature:
                epItem.nomenclature.dosage = doses
                epItem.nomenclature.nomenclatureId = nomenclatureId
                nomenclatureItem = epItem.nomenclature
                nomenclatureItem.actionExecutionPlanItem = epItem
                epItem.setIsDirty(True)
        index = QtCore.QModelIndex()
        cnt = len(self._groups)
        self.beginInsertRows(index, cnt, cnt)
        self.insertRows(cnt, 1, index)
        self.endInsertRows()
        self.emitItemsCountChanged()
        return newGroup


    def _addNewGroupFromTemplate(self, newAction, notCalculationParamTemplateIdList={}):
        newGroup = CExecutionPlanProxyModelGroup(None)
        self._newGroups.append(newGroup)
        self._groups.append(newGroup)
        newRecord = newAction.getRecord()
        item = CActionRecordItem(newRecord, newAction)
        newGroup.addItem(None, item)
        if not newAction.getType().isNomenclatureExpense:
            newAction.updateExecutionPlanByRecord(forceDuration=True)
            self.calcQuantity(newGroup)
        UUID = self._cellsSettings.getGroupSmnn(newGroup)
        lfFormId = self._cellsSettings.getGroupSmnnGrlsLf(newGroup)
        calculationParamId = self._cellsSettings.getGroupCalculationParam(newGroup)
        newGroup.setSmnnUUID(UUID, updateExecutionPlan=False)
        newGroup.setLfFormId(lfFormId, updateExecutionPlan=False)
        self._cellsSettings.setGroupSmnn(newGroup, UUID)
        self._cellsSettings.setGroupSmnnGrlsLf(newGroup, lfFormId)
        newGroup.setDuration(newGroup.duration(), updateExecutionPlan=False)
        self._cellsSettings.setGroupCalculationParam(newGroup, calculationParamId)
        if calculationParamId:
            notCalculationParamTemplateIdList = self.calculationDoseNomenclatureFromTemplate(newGroup, notCalculationParamTemplateIdList)
        newAction.updateSpecifiedName()
        index = QtCore.QModelIndex()
        cnt = len(self._groups)
        self.beginInsertRows(index, cnt, cnt)
        self.insertRows(cnt, 1, index)
        self.endInsertRows()
        self.emitItemsCountChanged()
        return notCalculationParamTemplateIdList


    def calculationDoseNomenclatureFromTemplate(self, newGroup, notCalculationParamTemplateIdList={}):
        items = {}
        templateId = self._cellsSettings.getGroupCalculationParam(newGroup)
        if templateId:
            items = self._cellsSettings.getValuePropertyToTemplateItems(newGroup)
            if not items:
                if len(self._groups) > 0:
                    group = self._groups[0]
                    items = self._cellsSettings.getValuePropertyToTemplateItems(group)
                if not items:
                    items = self.getCalculationParamValueProperties()
            self._cellsSettings.setValuePropertyToTemplateItems(newGroup, items)
            paramLine = self._cellsSettings.getValuePropertyToTemplate(newGroup, templateId)
            calculationParam = paramLine[0] if len(paramLine) > 0 else 0
            if calculationParam > 0:
                newGroup.setCalculationDosageInExists(calculationParam)
                if newGroup._copiedFrom:
                    groupKeys = newGroup._copiedFrom._mapRow2Item.keys()
                    groupKeys.sort()
                    for groupKey in groupKeys:
                        item = newGroup._copiedFrom._mapRow2Item[groupKey]
                        if item.action.executionPlanManager.hasItemsToDo():
                            currentIndex = item.action.executionPlanManager.getCurrentItemIndex()
                            executionPlan = newGroup._epGroup.getExecutionPlan()
                            item.action.executionPlanManager.setExecutionPlan(executionPlan, force=True)
                            item.action.executionPlanManager.setCurrentItemIndex(currentIndex)
                            item.action.executionPlanManager.bindAction(item.action)
                            if item.action.getType().isNomenclatureExpense:
                                item.action.updateDosageFromExecutionPlan()
                            item.action.updateSpecifiedName()
                else:
                    action = newGroup.headItem.action
                    if action:
                        if action.executionPlanManager.hasItemsToDo():
                            action.updateDosageFromExecutionPlan()
                            action.updateSpecifiedName()
            else:
                nomenclatureList = notCalculationParamTemplateIdList.get(templateId, [])
                nomenclatureName = self._cellsSettings.getGroupNomenclatureText(newGroup)
                nomenclatureNameList = nomenclatureName.split(u'|')
                nomenclatureNameStr = nomenclatureNameList[0]
                nomenclatureList.append(nomenclatureNameStr if nomenclatureNameStr else self._cellsSettings.getGroupSmnnText(newGroup))
                notCalculationParamTemplateIdList[templateId] = nomenclatureList
            return notCalculationParamTemplateIdList


    def getCalculationParamValueProperties(self):
        self._valuePropertyToTemplateItems = {}
        propertyIdHeader = []
        clientId = self._eventEditor.clientId if self._eventEditor else None
        if not clientId:
            return
        if clientId:
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
                    tableActionPropertyType['template_id'].inlist(propertyIdHeader),
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
                                    reportLine = self._valuePropertyToTemplateItems.setdefault(templateId, (0, None))
                                    if not reportLine[1] or reportLine[1] < endDate:
                                        reportLine = (valueProperty, endDate)
                                        self._valuePropertyToTemplateItems[templateId] = reportLine
                                elif type(valueProperty) is float:
                                    reportLine = self._valuePropertyToTemplateItems.setdefault(templateId, (0.0, None))
                                    if not reportLine[1] or reportLine[1] < endDate:
                                        reportLine = (valueProperty, endDate)
                                        self._valuePropertyToTemplateItems[templateId] = reportLine
        self.getCalculationParamValuePropertiesCurrentEvent()
        for group in self._groups:
            self._cellsSettings.setValuePropertyToTemplateItems(group, self._valuePropertyToTemplateItems)
            self._cellsSettings.setGroupCalculationParam(group, self._cellsSettings.getGroupCalculationParam(group))
        return self._valuePropertyToTemplateItems


    def getCalculationParamValuePropertiesCurrentEvent(self):
        if self._eventEditor:
            db = QtGui.qApp.db
            tableAPTemplate = db.table('ActionPropertyTemplate')
            templateIdList = db.getDistinctIdList(tableAPTemplate, [tableAPTemplate['id']], [tableAPTemplate['isCalcParamDoseNomenclatureExpense'].eq(1)])
            if templateIdList:
                tabs = self._eventEditor.getActionsTabsList()
                for tab in tabs:
                    groups = tab.modelAPActions._items._groups
                    for group in groups:
                        mapItem2Row = group._mapItem2Row
                        for item, row in mapItem2Row.items():
                            if item.action:
                                actionType = item.action.getType()
                                for propertyType in actionType.getPropertiesById().values():
                                    templateId = propertyType.templateId
                                    if templateId and templateId in templateIdList:
                                        record = item.action.getRecord()
                                        endDate = forceDate(record.value('endDate'))
                                        if endDate and forceInt(record.value('status')) == CActionStatus.finished:
                                            value = item.action.getPropertyById(propertyType.id).getValue()
                                            valueProperty = propertyType.convertQVariantToPyValue(value) if type(value) == QVariant else value
                                            if valueProperty:
                                                if type(valueProperty) is int:
                                                    reportLine = self._valuePropertyToTemplateItems.setdefault(templateId, (0, None))
                                                    if not reportLine[1] or reportLine[1] < endDate:
                                                        reportLine = (valueProperty, endDate)
                                                        self._valuePropertyToTemplateItems[templateId] = reportLine
                                                elif type(valueProperty) is float:
                                                    reportLine = self._valuePropertyToTemplateItems.setdefault(templateId, (0.0, None))
                                                    if not reportLine[1] or reportLine[1] < endDate:
                                                        reportLine = (valueProperty, endDate)
                                                        self._valuePropertyToTemplateItems[templateId] = reportLine


    def calcQuantity(self, group):
        action = group.headItem.action
        if action:
            quantity = forceInt(calcQuantity(action.getRecord()))
            if group.currentItem == group.groupingItem:
                groupingItem = group.groupingItem
                group.clearGroupingInfo()
            else:
                groupingItem = None
            group.setQuantity(quantity if quantity else 1)
            if groupingItem:
                group.appendGroupingInfo(group.currentItem)
                for subgroup in self._groups:
                    if subgroup.groupingItem == groupingItem:
                        subgroup.setGroupingItem(group.currentItem)
                        group.appendGroupingInfo(subgroup.currentItem)
        group.setSmnnUUID(self._cellsSettings.getGroupSmnn(group), updateExecutionPlan=False)
        group.setLfFormId(self._cellsSettings.getGroupSmnnGrlsLf(group), updateExecutionPlan=False)


    def _setItemsDefaultDosesValueAndNomenclature(self, group):
        doses = self._cellsSettings.getGroupDoses(group)
        nomenclatureId = self._cellsSettings.getGroupNomenclature(group)
        action = group.headItem.action
        for epItem in action.getExecutionPlan().items:
            if epItem.nomenclature:
                epItem.nomenclature.dosage = doses
                epItem.nomenclature.nomenclatureId = nomenclatureId
                nomenclatureItem = epItem.nomenclature
                nomenclatureItem.actionExecutionPlanItem = epItem
                epItem.setIsDirty(True)


    def _setItemsNomenclature(self, group):
        nomenclatureId = self._cellsSettings.getGroupNomenclature(group)
        action = group.headItem.action
        for epItem in action.getExecutionPlan().items:
            if epItem.nomenclature and not epItem.executedDatetime:
                epItem.nomenclature.nomenclatureId = nomenclatureId
                nomenclatureItem = epItem.nomenclature
                nomenclatureItem.actionExecutionPlanItem = epItem
                epItem.setIsDirty(True)


    def itemsToOrigin(self, items):
        result = []
        for i in items:
            item = i.item
            if item.__origin__:
                item.mergeIntoOrigin()
            result.append(item.getOrigin())
        return result


    def updateDosageByIndex(self, index, dosage):
        if not index.isValid():
            return
        row = index.row()
        group = self._groups[row]
        if group:
            group.setDosageInExists(dosage)
            self.reset()


    def updateDosageToProcentByIndex(self, index, procent, change):
        if not index.isValid():
            return
        row = index.row()
        group = self._groups[row]
        if group:
            group.setDosageToProcentInExists(procent, change)
            self.reset()


    def setIsDirtyInExists(self, group, value):
        if group:
            group.setIsDirtyInExists(value)


    def calculationDosageByIndex(self, index, calculationParam):
        if not index.isValid():
            return
        row = index.row()
        group = self._groups[row]
        if group:
            group.setCalculationDosageInExists(calculationParam)
            self.reset()


    def updateDosageNomenclatureByIndex(self, group):
        if group:
            dosage = self._cellsSettings.getGroupDoses(group)
            nomenclatureId = self._cellsSettings.getGroupNomenclature(group)
            group.setDosageNomenclatureInExists(dosage, nomenclatureId)
            self.reset()


    def setNomenclatureInExists(self, group):
        if group:
            nomenclatureId = self._cellsSettings.getGroupNomenclature(group)
            group.setNomenclatureInExists(nomenclatureId)
            self.reset()


    def updateDosageNomenclatureFromDate(self, group, date):
        if group:
            dosage = self._cellsSettings.getGroupDoses(group)
            nomenclatureId = self._cellsSettings.getGroupNomenclature(group)
            group.setDosageNomenclatureFromDate(dosage, nomenclatureId, date)
            self.reset()


    @property
    def lastMainIndex(self):
        return NOTE_INDEX


    def setNomenclatureExistQntCache(self, nomenclatureId):
        if nomenclatureId not in self._nomenclatureExistQntCache.keys():
            existQnt = getExistsNomenclatureAmount(nomenclatureId, financeId = self._eventEditor.eventFinanceId, medicalAidKindId = self.getMedicalAidKindId(self._eventEditor.eventTypeId), orgStructureId=self._stockOrgStructureId if self._stockOrgStructureId else QtGui.qApp.currentOrgStructureId())
            self._nomenclatureExistQntCache[nomenclatureId] = existQnt
        return self._nomenclatureExistQntCache[nomenclatureId]


    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role not in (Qt.DisplayRole, Qt.ToolTipRole) or section < 0:
            return QtCore.QVariant()
        if orientation == Qt.Horizontal:
            if section in self.STATIC_HEADERS:
                if role == Qt.DisplayRole:
                    return QtCore.QVariant(self.STATIC_HEADERS[section][0])
                elif role == Qt.ToolTipRole:
                    return QtCore.QVariant(self.STATIC_HEADERS[section][2])
            return QtCore.QVariant(section - NOTE_INDEX)
        return QtCore.QVariant()


    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QtCore.QVariant()

        row = index.row()

        if not (0 <= row < len(self._groups)):
            return QtCore.QVariant()

        group = self._groups[row]
        column = index.column()

        if role == Qt.DisplayRole:
            if column == ORGSTRUCTURE_INDEX:
                orgStructureId = group.getLastOrgStructureId()
                orgStructureName = None
                if orgStructureId:
                    if orgStructureId in self._orgStructureNameCaches.keys():
                        orgStructureName = self._orgStructureNameCaches.get(orgStructureId, None)
                    if orgStructureName is None:
                        orgStructureName = getOrgStructureName(orgStructureId)
                        if orgStructureName:
                            self._orgStructureNameCaches[orgStructureId] = orgStructureName
                return QtCore.QVariant(orgStructureName)
            elif column == SCHEME_INDEX:
                return QtCore.QVariant(self._cellsSettings.getActionTypeGroupCode(group.getActionTypeGroupId()))
            elif column == DIREACTION_DATE_INDEX:
                if self._showTime:
                    return QtCore.QVariant(group.directionDate())
                else:
                    return QtCore.QVariant(group.directionDate().date())
            elif column == BEG_DATE_INDEX:
                if self._showTime:
                    return QtCore.QVariant(QDateTime(group.begDate(), group.begTime()))
                else:
                    return QtCore.QVariant(group.begDate())
            elif column == CANCEL_DATE_INDEX:
                return QtCore.QVariant(self._cellsSettings.getGroupCancelDateText(group))
            elif column == SMNN_INDEX:
                return QtCore.QVariant(self._cellsSettings.getGroupSmnnText(group))
            elif column == SMNN_GRLSLF_INDEX:
                return QtCore.QVariant(self._cellsSettings.getGroupSmnnGrlsLfText(group))
            elif column == PLAN_END_DATE:
                return QtCore.QVariant(group.planEndDate())
            elif column == NOMENCLATURE_INDEX:
                return QtCore.QVariant(self._cellsSettings.getGroupNomenclatureText(group))
            elif column == REACTION_INDEX:
                return QtCore.QVariant(self._cellsSettings.getGroupReactionText(group))
            elif column == CALCULATIONPARAM_INDEX:
                return QtCore.QVariant(self._cellsSettings.getGroupCalculationParamText(group))
            elif column == DOSES_INDEX:
                return QtCore.QVariant(self._cellsSettings.getGroupDosesTextEx(group))
            elif column == SIGNA_INDEX:
                return QtCore.QVariant(self._cellsSettings.getGroupSignaText(group))
            elif column == SIGNACOMMENT_INDEX:
                return QtCore.QVariant(self._cellsSettings.getGroupSignaCommentText(group))
            elif column == DURATION_INDEX:
                return QtCore.QVariant(group.duration())
            elif column == ALIQUOTICITY_INDEX:
                return QtCore.QVariant(group.aliquoticity())
            elif column == PERIODICITY_INDEX:
                return QtCore.QVariant(group.periodicity())
            elif column == NOTE_INDEX:
                return QtCore.QVariant(group.note())
            elif column == GROUPING_INDEX:
                return QtCore.QVariant()
            elif column > NOTE_INDEX:
                return QtCore.QVariant(self._getDayDataValue(row, column, group))

        elif role == Qt.BackgroundColorRole:
            items = group.items
            enabled = True
            for i in range(len(items)):
                if group.items[i].action._record.value('status')==3:
                    enabled = False
                    break
            if not enabled:
                return QtCore.QVariant(QtGui.QColor(Qt.gray))
            else:
                if column > NOTE_INDEX:
                    return QtCore.QVariant(self._getDayDataColor(row, column, group))

        elif role == Qt.FontRole:
            nomenclatureId = self._cellsSettings.getGroupNomenclature(group)
            if nomenclatureId and self.setNomenclatureExistQntCache(nomenclatureId) <= 0:
                result = QtGui.QFont()
                result.setWeight(QtGui.QFont.DemiBold)
                return QVariant(result)

        return QtCore.QVariant()


    def _getDayDataValue(self, row, column, group):
        year = self._date.year()
        month = self._date.month()
        day = column - NOTE_INDEX
        planItems = 0

        items = group.getItemsByDate(QtCore.QDate(year, month, day))
        if not items:
            return None
        planItems = len(items)

        not_done_items = []

        for item in items:
            executedDatetime = item.executedDatetime
            if executedDatetime is None:
                not_done_items.append(item)
            elif executedDatetime.isNull() or not executedDatetime.isValid():
                not_done_items.append(item)

        return u'%i/%i'%( planItems-len(not_done_items), planItems)


    def _getDayDataColor(self, row, column, group):
        year = self._date.year()
        month = self._date.month()
        day = column - NOTE_INDEX

        items = group.getItemsByDate(QtCore.QDate(year, month, day))
        if not items:
            return None

        not_done_items = []
        overdue_items = []

        for item in items:
            executedDatetime = item.executedDatetime
            if executedDatetime is None:
                not_done_items.append(item)

            elif executedDatetime.isNull() or not executedDatetime.isValid():
                not_done_items.append(item)

            elif executedDatetime > QtCore.QDateTime(item.date, item.time) and not self._ignoreTime:
                overdue_items.append(item)
            elif forceDate(executedDatetime) > QtCore.QDateTime(item.date) and self._ignoreTime:
                overdue_items.append(item)

        if not_done_items:
            return NOT_DONE_COLOR

        elif overdue_items:
            return OVERDUE_COLOR

        return DONE_COLOR


    def setReadOnly(self, value=False):
        self._readOnly = value


    def isReadOnly(self):
        return self._readOnly


    def flags(self, index):
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable

        if self._readOnly:
            return flags

        row = index.row()
        if row > len(self._groups):
            return flags

        editableFlags = flags | Qt.ItemIsEditable

        column = index.column()
        if column in (SCHEME_INDEX, SMNN_INDEX, SMNN_GRLSLF_INDEX):
            return flags

        if row == len(self._groups):
            if not self._stockOrgStructureId:
                return flags
            if self._actionTypeId and (column in (NOMENCLATURE_INDEX, SMNN_INDEX, SMNN_GRLSLF_INDEX)):
                return editableFlags
            return flags

        group = self._groups[row]
        if column > NOTE_INDEX:
            return flags

        if column == ORGSTRUCTURE_INDEX and self._nomenclatureOrgStructureId:
            return flags

        elif column == DOSES_INDEX and not group.hasExecutedItems() and group.groupDataNotChanged():
            return editableFlags

        elif column in (CALCULATIONPARAM_INDEX, ORGSTRUCTURE_INDEX, SIGNA_INDEX, SIGNACOMMENT_INDEX, NOTE_INDEX) and not group.hasExecutedItems() and group.groupDataNotChangedEx():
            return editableFlags

        elif column == ORGSTRUCTURE_INDEX and group.groupDataNotChangedEx():
            return editableFlags

        elif column == DURATION_INDEX and group.groupDataNotChanged() and not group.hasSavedItems() and not group.hasExecutedItems():
            return editableFlags

        if group.groupDataNotChanged():
            if column == DOSES_INDEX and group.hasExecutedItems():
                return flags
            elif column not in (DOSES_INDEX, ORGSTRUCTURE_INDEX) and ((self._cellsSettings.getGroupNomenclature(group) and not self.isGroupingDirty(group)) or column != NOMENCLATURE_INDEX) and (group.hasSavedItems() or group.hasExecutedItems()):
                return flags
            if column == ORGSTRUCTURE_INDEX and not group.hasNotExecutedItems():
                return flags
            else:
                return editableFlags

        elif group.hasExecutedItems():
            return flags

        elif group.hasSavedItems() and ((self._cellsSettings.getGroupNomenclature(group) and not self.isGroupingDirty(group)) or column != NOMENCLATURE_INDEX):
            return flags

        return editableFlags

    
    def isGroupingDirty(self, group):
        isDirty = True
        for subgroup in self._groups:
            if (subgroup.isGrouped() and group.isGrouped() or subgroup == group) and subgroup.groupingItem == group.groupingItem:
                isDirty = isDirty and subgroup.isDirty()
        return isDirty
        
    

    def createEditor(self, index, parent):
        column = index.column()
        row = index.row()

        assert 0 <= row <= len(self._groups)
        assert 0 <= column <= NOTE_INDEX

        if column == ORGSTRUCTURE_INDEX:
            group = None
            if 0 <= row < len(self._groups):
                group = self._groups[row]
            return self._createOrgStructureEditor(parent, group)

        elif column == DIREACTION_DATE_INDEX:
            if self._showTime:
                return CDateTimeEdit(parent)
            else:
                return CDateEdit(parent)

        elif column == BEG_DATE_INDEX:
            if self._showTime:
                return CDateTimeEdit(parent)
            else:
                return CDateEdit(parent)
        
        elif column == CANCEL_DATE_INDEX:
            return CDateTimeEdit(parent)

        elif column == SMNN_INDEX:
            group = None
            if 0 <= row < len(self._groups):
                group = self._groups[row]
            return self._createSmnnEditor(parent, group)

        elif column == SMNN_GRLSLF_INDEX:
            group = None
            if 0 <= row < len(self._groups):
                group = self._groups[row]
            return self._createSmnnGrlsLfEditor(parent, group)

        elif column == NOMENCLATURE_INDEX:
            group = None
            if 0 <= row < len(self._groups):
                group = self._groups[row]
            return self._createNomenclatureEditor(parent, group)

        elif column == PLAN_END_DATE:
            return CDateEdit(parent)

        elif column == CALCULATIONPARAM_INDEX:
            group = None
            if 0 <= row < len(self._groups):
                group = self._groups[row]
            return self._createCalculationParamEditor(parent, group)

        elif column == DOSES_INDEX:
            editor = QtGui.QDoubleSpinBox(parent)
            editor.setMaximum(10000)
            editor.setMinimum(0)
            editor.setDecimals(2)
            return editor

        elif column == SIGNA_INDEX:
            return self._createSIGNAEditor(parent, row)
            #return QtGui.QLineEdit(parent)

#        elif column == SIGNACOMMENT_INDEX:
#            return QtGui.QLineEdit(parent)

        elif column in (DURATION_INDEX, ALIQUOTICITY_INDEX, PERIODICITY_INDEX):
            editor = QtGui.QSpinBox(parent)
            editor.setMaximum(365)
            editor.setMinimum(0)
            return editor

        elif column not in (SCHEME_INDEX, SMNN_INDEX, SMNN_GRLSLF_INDEX):
            return QtGui.QLineEdit(parent)


    def setEditorData(self, index, editor):
        row = index.row()
        column = index.column()
        if not (0 <= row < len(self._groups)):
            return False

        group = self._groups[row]

        if column == ORGSTRUCTURE_INDEX:
            editor.setValue(group.getLastOrgStructureId())
            return True

        elif column == DIREACTION_DATE_INDEX:
            directionDate = group.directionDate()
            if self._showTime:
                if directionDate is None:
                    directionDate = QtCore.QDateTime()
            else:
                if directionDate is None:
                    directionDate = QtCore.QDate()
                else:
                    directionDate = directionDate.date()
            editor.setDate(directionDate)
            return True

        elif column == BEG_DATE_INDEX:
            if self._showTime:
                editor.setDate(QDateTime(group.begDate(), group.begTime()) or QtCore.QDateTime())
            else:
                editor.setDate(group.begDate() or QtCore.QDate())
            return True
        
        elif column == CANCEL_DATE_INDEX:
            editor.setDate(QDateTime().fromString(self._cellsSettings.getGroupCancelDateText(group), 'dd.MM.yyyy H:mm'))

        elif column == SMNN_INDEX:
            editor.setValue(self._cellsSettings.getGroupSmnn(group), self._cellsSettings.getGroupSmnnGrlsLf(group))
            return True

        elif column == SMNN_GRLSLF_INDEX:
            editor.setValue(self._cellsSettings.getGroupSmnn(group), self._cellsSettings.getGroupSmnnGrlsLf(group))
            return True

        elif column == PLAN_END_DATE:
            editor.setDate(group.planEndDate() or QtCore.QDate())
            return True

        elif column == NOMENCLATURE_INDEX:
            editor.setValue(self._cellsSettings.getGroupNomenclature(group))
            return True

        elif column == REACTION_INDEX:
            editor.setText(self._cellsSettings.getGroupReactionText(group) or '')
            return True

        elif column == CALCULATIONPARAM_INDEX:
            editor.setValue(self._cellsSettings.getGroupCalculationParam(group))
            return True

        elif column == DOSES_INDEX:
            editor.setValue(self._cellsSettings.getGroupDoses(group) or 1)
            return True

        elif column == SIGNA_INDEX:
            if self._cellsSettings.isNomenclatureUsingTypeActionPropertyValueType(group):
                editor.setValue(self._cellsSettings.getGroupSigna(group))
            else:
                editor.setText(self._cellsSettings.getGroupSigna(group) or '')
            return True

        elif column == SIGNACOMMENT_INDEX:
            editor.setText(self._cellsSettings.getGroupSignaCommentText(group) or '')
            return True

        elif column == DURATION_INDEX:
            value = group.duration() or 1
            if group.hasExecutedItems():
                editor.setMinimum(value)
            editor.setValue(group.duration() or 1)
            return True

        elif column == ALIQUOTICITY_INDEX:
            editor.setValue(group.aliquoticity() or 1)
            return True

        elif column == PERIODICITY_INDEX:
            editor.setValue(group.periodicity() or 1)
            return True

        elif column == NOTE_INDEX:
            editor.setText(group.note())
            return True

        return False


    def getEditorData(self, index, editor):
        row = index.row()
        column = index.column()
        if column == ORGSTRUCTURE_INDEX:
            return editor.value()
        elif column == DIREACTION_DATE_INDEX:
            return editor.date()
        elif column == BEG_DATE_INDEX:
            return editor.date()
        elif column == CANCEL_DATE_INDEX:
            return editor.date()
        elif column == SMNN_INDEX:
            return editor.value()
        elif column == SMNN_GRLSLF_INDEX:
            return editor.value()
        elif column == PLAN_END_DATE:
            return editor.date()
        elif column == NOMENCLATURE_INDEX:
            return editor.value()
        elif column == REACTION_INDEX:
            return unicode(editor.text())
        elif column == CALCULATIONPARAM_INDEX:
            if 0 <= row < len(self._groups):
                group = self._groups[row]
                if not self._cellsSettings.getValuePropertyToTemplateItems(group):
                    items = editor.getValuePropertyToTemplateItems()
                    if not items:
                        items = self.getCalculationParamValueProperties()
                    self._cellsSettings.setValuePropertyToTemplateItems(group, items)
            return editor.value()
        elif column == DOSES_INDEX:
            return editor.value()
        elif column == SIGNA_INDEX:
            if 0 <= row < len(self._groups):
                group = self._groups[row]
                if self._cellsSettings.isNomenclatureUsingTypeActionPropertyValueType(group):
                    return editor.value()
                else:
                    return unicode(editor.text())
            return editor.value()
        elif column == SIGNACOMMENT_INDEX:
            return unicode(editor.text())
        elif column == DURATION_INDEX:
            return editor.value()
        elif column == ALIQUOTICITY_INDEX:
            return editor.value()
        elif column == PERIODICITY_INDEX:
            return editor.value()
        elif column == NOTE_INDEX:
            return unicode(editor.text())


    def _createSIGNAEditor(self, parent, row): #0011445:0057123:пункт 1
        group = self._groups[row]
        nomenclatureId = self._cellsSettings.getGroupNomenclature(group)
        if self._cellsSettings.isNomenclatureUsingTypeActionPropertyValueType(group): #0015606
            editor = CRBComboBox(parent)
            usingTypeIdList = []
            db = QtGui.qApp.db
            table = db.table('rbNomenclature_UsingType')
            if nomenclatureId:
                usingTypeIdList = db.getDistinctIdList(table, table['usingType_id'].name(),
                                                       [table['master_id'].eq(nomenclatureId)],
                                                       order=table['idx'].name())
            if usingTypeIdList:
                filter = 'rbNomenclatureUsingType.id IN (%s)' % (
                    u','.join(str(usingTypeId) for usingTypeId in usingTypeIdList if usingTypeId))
            else:
                filter = u''
            editor.setTable('rbNomenclatureUsingType', addNone=True, filter=filter)
            editor.setShowFields(CRBComboBox.showName)
            return editor
        editor = CSIGNANomenclatureComboBox(parent) #0011445:0056953:пункт 1
        if nomenclatureId:
            signa = self._cellsSettings.getGroupSigna(group)
            values = self._cellsSettings.setNomenclatureUsingTypes(nomenclatureId, signa)
            for val in values:
                editor.addItem(val)
        return editor


    def _createSmnnEditor(self, parent, group):
        editor = CSmnnNomenclatureExpenseComboBox(parent)
        actionType = CActionTypeCache.getById(self._actionTypeId) if self._actionTypeId else None
        editor.setOnlyExists(actionType.isNomenclatureExpense if actionType else True)
        nomenclatureId = None
        editor.setOrgStructureId(self._stockOrgStructureId if self._stockOrgStructureId else QtGui.qApp.currentOrgStructureId())
        if group:
            nomenclatureId = self._cellsSettings.getGroupNomenclature(group)
        editor.setNomenclatureId(nomenclatureId)
        return editor


    def _createSmnnGrlsLfEditor(self, parent, group):
        editor = CGrlsLfNomenclatureExpenseComboBox(parent)
        editor.setOnlySmnnUUID(True)
        actionType = CActionTypeCache.getById(self._actionTypeId) if self._actionTypeId else None
        editor.setOnlyExists(actionType.isNomenclatureExpense if actionType else True)
        nomenclatureId = None
        smnnUUID = None
        editor.setOrgStructureId(self._stockOrgStructureId if self._stockOrgStructureId else QtGui.qApp.currentOrgStructureId())
        if group:
            nomenclatureId = self._cellsSettings.getGroupNomenclature(group)
            smnnUUID = self._cellsSettings.getGroupSmnn(group)
        editor.setNomenclatureId(nomenclatureId)
        editor.setNomenclatureSmnnUUID(smnnUUID)
        editor.setOnlySmnnUUID(True)
        return editor


    def _createNomenclatureEditor(self, parent, group):
        editor = CExpenseNomenclatureComboBox(parent)
        cols = ['nomenclatureClass_id', 'nomenclatureKind_id', 'nomenclatureType_id']  # wtf
        record = QtGui.qApp.db.getRecord('ActionType', cols, self._actionTypeId)
        nomenclatureClassId = forceRef(record.value('nomenclatureClass_id'))
        nomenclatureKindId = forceRef(record.value('nomenclatureKind_id'))
        nomenclatureTypeId = forceRef(record.value('nomenclatureType_id'))
        isSMNN = False
        isOnlyMnnEsklpFormVisible = False
        actionType = CActionTypeCache.getById(self._actionTypeId) if self._actionTypeId else None
#        for propertyType in actionType.getPropertiesById().values():
#            if propertyType.isNomenclatureSmnnActionPropertyValueType() or propertyType.isNomenclatureSmnnGrlsLfActionPropertyValueType():
#                isSMNN = True
#                break
        editor.setOnlyNomenclature(True)
        editor.setDefaultIds(nomenclatureClassId, nomenclatureKindId, nomenclatureTypeId)
        if self._eventEditor:
            editor.setUseClientUnitId()
            editor.setFinanceId(self._eventEditor.eventFinanceId)
            editor.setMedicalAidKindId(self.getMedicalAidKindId(self._eventEditor.eventTypeId))
        editor.setOrgStructureId(self._stockOrgStructureId if self._stockOrgStructureId else QtGui.qApp.currentOrgStructureId())
        editor.setOnlyExists(actionType.isNomenclatureExpense if actionType else True)
        smnnUUID = None
        smnnGrlsLfId = None
        smnnName = ''
        editor.setOrgStructureId(self._stockOrgStructureId if self._stockOrgStructureId else QtGui.qApp.currentOrgStructureId())
        if group:
            for propertyType in actionType.getPropertiesById().values():
                if propertyType.isNomenclatureSmnnActionPropertyValueType() or propertyType.isNomenclatureSmnnGrlsLfActionPropertyValueType():
                    isSMNN = True
                    break
            if isSMNN:
                smnnUUID = self._cellsSettings.getGroupSmnn(group)
                smnnName = self._cellsSettings.getGroupSmnnText(group)
                smnnGrlsLfId = self._cellsSettings.getGroupSmnnGrlsLf(group)
                isOnlyMnnEsklpFormVisible = bool(smnnUUID) and bool(smnnGrlsLfId)
        editor.setIsOnlyMnnEsklpFormVisible(isOnlyMnnEsklpFormVisible)
        editor.setNomenclatureSmnnUUID(smnnUUID)
        editor.setNomenclatureSmnnName(smnnName if smnnName is not None else '')
        editor.setLfFormId(smnnGrlsLfId)
        editor.getFilterData()
        editor.setFilter(editor._filter)
        return editor


    def _createCalculationParamEditor(self, parent, group):
        if self._eventEditor:
            self._eventEditor.clientId
            if self._eventEditor.clientId:
                items = self._cellsSettings.getValuePropertyToTemplateItems(group)
                if not items:
                    items = self.getCalculationParamValueProperties()
                editor = CPropertyValueToTemplateComboBox(parent, self._eventEditor.clientId)
                editor.setEventEditor(self._eventEditor)
                editor.setValuePropertyToTemplateItems(items)
                return editor
        return None


    def _createOrgStructureEditor(self, parent, group):
        editor = COrgStructureComboBox(parent, emptyRootName='-')
        editor.setOrgId(QtGui.qApp.currentOrgId())
        if group:
            orgStructureId = group.getLastOrgStructureId()
            editor.setValue(orgStructureId)
        return editor


    def getMedicalAidKindId(self, eventTypeId):
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        cond = [tableEventType['id'].eq(eventTypeId)]
        queryTable = tableEvent
        queryTable = queryTable.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
        record = db.getRecordEx(queryTable, tableEventType['medicalAidKind_id'], cond)
        if record:
            return forceInt(record.value('medicalAidKind_id'))
        return None


    def getSignaToNomenclatureId(self, nomenclatureId, group):
        if nomenclatureId and group:
            db = QtGui.qApp.db
            table = db.table('rbNomenclature')
            tableUsingType = db.table('rbNomenclature_UsingType')
            tableRBUsingType = db.table('rbNomenclatureUsingType')
            queryTable = table.innerJoin(tableUsingType, tableUsingType['master_id'].eq(table['id']))
            queryTable = queryTable.innerJoin(tableRBUsingType, tableRBUsingType['id'].eq(tableUsingType['usingType_id']))
            record = db.getRecordEx(queryTable, [tableRBUsingType['id'].alias('usingTypeId'), tableRBUsingType['name'].alias('usingType')], [table['id'].eq(nomenclatureId)], order=tableUsingType['idx'].name())
            if self._cellsSettings.isNomenclatureUsingTypeActionPropertyValueType(group):
                return forceRef(record.value('usingTypeId')) if record else None
            else:
                return forceString(record.value('usingType')) if record else u''
        return u''


    def updateSmnn_SmnnGrlslf(self, group, nomenclatureId, oldNomenclatureId):
        if nomenclatureId and nomenclatureId != oldNomenclatureId:
            oldSmnnUUID = self._cellsSettings.getGroupSmnn(group)
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
                self._cellsSettings.setGroupSmnn(group, newSmnnUUID)
            if newSmnnUUID:
                oldSmnnGrlsLfId = self._cellsSettings.getGroupSmnnGrlsLf(group)
                lfFormIdList = getLfFormIdList(nomenclatureId = nomenclatureId, smnnUUID = newSmnnUUID)
                if len(lfFormIdList) == 1:
                    newSmnnGrlsLfId = lfFormIdList[0]
                    if oldSmnnGrlsLfId != newSmnnGrlsLfId:
                        group.setLfFormId(newSmnnGrlsLfId, updateExecutionPlan=False)
                        self._cellsSettings.setGroupSmnnGrlsLf(group, newSmnnGrlsLfId)
                elif oldSmnnGrlsLfId not in lfFormIdList:
                    group.setLfFormId(None, updateExecutionPlan=False)
                    self._cellsSettings.setGroupSmnnGrlsLf(group, None)
            else:
                group.setLfFormId(None, updateExecutionPlan=False)
                self._cellsSettings.setGroupSmnnGrlsLf(group, None)
        return group


    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False

        if role != Qt.EditRole:
            return False

        column = index.column()

        row = index.row()
        if row == len(self._groups):
            if column not in (NOMENCLATURE_INDEX, SMNN_INDEX, SMNN_GRLSLF_INDEX):
                return False

            if not value or (isinstance(value, QtCore.QVariant) and value.isNull()):
                return False

            if not self._stockOrgStructureId:
                return False

            self._addNewGroup(forceRef(value) if column == NOMENCLATURE_INDEX else None)

        isExistsDoneByIndex = self.existsDoneByIndex(index)
        group = self._groups[row]

        if column == ORGSTRUCTURE_INDEX and not isExistsDoneByIndex:
            def setOrgStructure(subgroup, value):
                if value.isNull():
                    return False

                prevStockOrgStructureId = self._stockOrgStructureId
                newOrgStructureId = forceRef(value)
                subgroup.setLastOrgStructureId(newOrgStructureId)
                self.setIsDirtyInExists(subgroup, True)
                if prevStockOrgStructureId != newOrgStructureId:
                    self.setOrgStructureId(newOrgStructureId, isReset=False)
                    self.setOrgStructureId(prevStockOrgStructureId)
                else:
                    self.setOriginGroups(self._originGroups)
            
            for subgroup in self._groups:
                if (subgroup.isGrouped() and group.isGrouped() or subgroup == group) and subgroup.groupingItem == group.groupingItem:
                    setOrgStructure(subgroup, value)
                
            self.setIsDirty(True)
            return True

        elif column == DIREACTION_DATE_INDEX and not isExistsDoneByIndex:
            def setDirectionDate(subgroup, value):
                if not value.isValid():
                    return False

                if value.isNull():
                    return False

                subgroup.setDirectionDate(forceDateTime(value) if self._showTime else forceDate(value))
            
            for subgroup in self._groups:
                if (subgroup.isGrouped() and group.isGrouped() or subgroup == group) and subgroup.groupingItem == group.groupingItem:
                    setDirectionDate(subgroup, value)
                    
            self.setIsDirty(True)
            return True

        elif column == BEG_DATE_INDEX and not isExistsDoneByIndex:
            def setBegDate(subgroup, value):
                if not value.isValid():
                    return False

                if value.isNull():
                    return False
                if self._showTime:
                    begDate = forceDate(value)
                    begTime = forceTime(value)
                    if begDate == subgroup.begDate() and begTime == subgroup.begTime():
                        self.setIsDirty(True)
                        return True
                else:
                    begDate = forceDate(value)
                    if begDate == subgroup.begDate():
                        self.setIsDirty(True)
                        return True

                duration = max(subgroup.begDate().daysTo(subgroup.planEndDate())+1, 1)
                subgroup.setBegDate(begDate)
                begTime = forceTime(value) if self._showTime else None
                subgroup.setBegTime(begTime)
                subgroup.setPlanEndDate(begDate.addDays(duration))
                subgroup.setDuration(duration, updateExecutionPlan=False)
                self.calcQuantity(subgroup)
                self._setItemsDefaultDosesValueAndNomenclature(subgroup)
            
            for subgroup in self._groups:
                if (subgroup.isGrouped() and group.isGrouped() or subgroup == group) and subgroup.groupingItem == group.groupingItem:
                    setBegDate(subgroup, value)
            self.setIsDirty(True)
            return True
        
        elif column == CANCEL_DATE_INDEX and not isExistsDoneByIndex:
            cancelDate = forceDateTime(value)
            if cancelDate == QDateTime().fromString(self._cellsSettings.getGroupCancelDateText(group), 'dd.MM.yyyy H:mm'):
                self.setIsDirty(True)
                return True
            self._cellsSettings.setGroupCancelDate(group, forceDateTime(value))
            self.setIsDirty(True)
            return True
        
        elif column == SMNN_INDEX and not isExistsDoneByIndex:
            values = value.toList()
            newSmnnUUID = forceStringEx(values[0]) if len(values) > 0 else ''
            newSmnnGrlsLfId = forceRef(values[1]) if len(values) > 1 else None
            oldSmnnUUID = self._cellsSettings.getGroupSmnn(group)
            if oldSmnnUUID != newSmnnUUID:
                self._cellsSettings.setGroupSmnn(group, newSmnnUUID)
            oldSmnnGrlsLfId = self._cellsSettings.getGroupSmnnGrlsLf(group)
            if oldSmnnGrlsLfId != newSmnnGrlsLfId:
                self._cellsSettings.setGroupSmnnGrlsLf(group, newSmnnGrlsLfId)
            return True

        elif column == SMNN_GRLSLF_INDEX and not isExistsDoneByIndex:
            values = value.toList()
            newSmnnUUID = forceStringEx(values[0]) if len(values) > 0 else ''
            newSmnnGrlsLfId = forceRef(values[1]) if len(values) > 1 else None
            oldSmnnUUID = self._cellsSettings.getGroupSmnn(group)
            if oldSmnnUUID != newSmnnUUID:
                self._cellsSettings.setGroupSmnn(group, newSmnnUUID)
            oldSmnnGrlsLfId = self._cellsSettings.getGroupSmnnGrlsLf(group)
            if oldSmnnGrlsLfId != newSmnnGrlsLfId:
                self._cellsSettings.setGroupSmnnGrlsLf(group, newSmnnGrlsLfId)
            return True

        elif column == PLAN_END_DATE and not isExistsDoneByIndex:
            def setPlanDate(subgroup, value):
                plannEndDate = forceDate(value)
                if plannEndDate == subgroup.planEndDate():
                    self.setIsDirty(True)
                    return True

                subgroup.setPlanEndDate(plannEndDate)
                duration = max(subgroup.begDate().daysTo(plannEndDate)+1, 1)
                subgroup.setDuration(duration, updateExecutionPlan=False)
                self.calcQuantity(subgroup)
                self._setItemsDefaultDosesValueAndNomenclature(subgroup)
            
            for subgroup in self._groups:
                if (subgroup.isGrouped() and group.isGrouped() or subgroup == group) and subgroup.groupingItem == group.groupingItem:
                    setPlanDate(subgroup, value)
            self.setIsDirty(True)
            return True

        elif column == NOMENCLATURE_INDEX and not isExistsDoneByIndex:
            newNomenclatureId = forceRef(value)
            oldNomenclatureId = self._cellsSettings.getGroupNomenclature(group)
            if oldNomenclatureId != newNomenclatureId:
                group.setIsDirty(newNomenclatureId and not oldNomenclatureId)
                self._cellsSettings.setGroupNomenclature(group, newNomenclatureId)
                nomenclatureOldAnalogId = self.getNomenclatureAnalog(oldNomenclatureId) if oldNomenclatureId else None #0014428:0058806
                nomenclatureAnalogId = self.getNomenclatureAnalog(newNomenclatureId) if newNomenclatureId else None
                if nomenclatureOldAnalogId != nomenclatureAnalogId or not nomenclatureOldAnalogId or not nomenclatureAnalogId:
                    if not self._cellsSettings.getGroupSmnn(group) or not self._cellsSettings.getGroupSmnnGrlsLf(group):
                        self.updateDosageNomenclatureByIndex(group)
                    else:
                        self._setItemsNomenclature(group)
                        self.setNomenclatureInExists(group)
                elif nomenclatureOldAnalogId and nomenclatureOldAnalogId == nomenclatureAnalogId:
                    self._setItemsNomenclature(group)
                    self.setNomenclatureInExists(group)
                if not trim(self._cellsSettings.getGroupSigna(group)): #0011445:0056953:пункт 1
                    self._cellsSettings.setGroupSigna(group, self.getSignaToNomenclatureId(newNomenclatureId, group))
                    self._cellsSettings.setGroupSignaCommentText(group, forceString(self._cellsSettings.getGroupSignaCommentTypeText(group)))
                group = self.updateSmnn_SmnnGrlslf(group, newNomenclatureId, oldNomenclatureId)
            self.setIsDirty(True)
            return True

        elif column == REACTION_INDEX and not isExistsDoneByIndex:
            reaction = forceStringEx(value)
            if reaction == self._cellsSettings.getGroupReactionText(group):
                self.setIsDirty(True)
                return True
            self._cellsSettings.setGroupReaction(group, forceString(value))
            self.setIsDirty(True)
            return True

        elif column == CALCULATIONPARAM_INDEX and not isExistsDoneByIndex:
            newCalculationParamId = forceRef(value)
            oldCalculationParamId = self._cellsSettings.getGroupCalculationParam(group)
            if newCalculationParamId != oldCalculationParamId:
                group.setIsDirty(newCalculationParamId and not oldCalculationParamId)
                self._cellsSettings.setGroupCalculationParam(group, newCalculationParamId)
            self.setIsDirty(True)
            return True

        elif column == DOSES_INDEX:
            oldDosage = self._cellsSettings.getGroupDoses(group)
            self._cellsSettings.setGroupDoses(group, forceDouble(value))
            self._setItemsDefaultDosesValueAndNomenclature(group)
            newDosage = self._cellsSettings.getGroupDoses(group)
            if newDosage != oldDosage:
                self.updateDosageByIndex(index, newDosage)
                group.updateSpecifiedName()
            self.setIsDirty(True)
            return True

        elif column == SIGNA_INDEX and not isExistsDoneByIndex:
            def setSigna(subgroup, value):
                if self._cellsSettings.isNomenclatureUsingTypeActionPropertyValueType(subgroup):
                    self._cellsSettings.setGroupSigna(subgroup, forceRef(value))
                else:
                    self._cellsSettings.setGroupSigna(subgroup, forceString(value))
                    
            for subgroup in self._groups:
                if (subgroup.isGrouped() and group.isGrouped() or subgroup == group) and subgroup.groupingItem == group.groupingItem:
                    setSigna(subgroup, value)
            self.setIsDirty(True)
            return True

        elif column == SIGNACOMMENT_INDEX and not isExistsDoneByIndex:
            signaComment = forceStringEx(value)
            if signaComment == self._cellsSettings.getGroupSignaCommentText(group):
                self.setIsDirty(True)
                return True
            self._cellsSettings.setGroupSignaCommentText(group, forceString(value))
            self.setIsDirty(True)
            return True

        elif column == DURATION_INDEX and not isExistsDoneByIndex:
            def setDuration(subgroup, value):
                currentDuration = subgroup.duration()
                duration = forceInt(value)
                if duration == currentDuration:
                    self.setIsDirty(True)
                    return True

                if subgroup.hasExecutedItems():
                    if duration < currentDuration:
                        return False
                    note = forceStringEx(subgroup.note())
                    doses = self._cellsSettings.getGroupDoses(subgroup)
                    nomenclatureId = self._cellsSettings.getGroupNomenclature(subgroup)
                    items = subgroup.addDaysToEP(duration-currentDuration)
                    for item in items:
                        if item.nomenclature:
                            item.nomenclature.dosage = doses
                            item.nomenclature.nomenclatureId = nomenclatureId
                    subgroup.setNote(note, updateExecutionPlan=False)
                    self.setIsDirty(True)
                    return True
                note = forceStringEx(subgroup.note())
                subgroup.setDuration(duration, updateExecutionPlan=False)
                self.calcQuantity(subgroup)
                self.updateDosageNomenclatureByIndex(subgroup)
                subgroup.setNote(note, updateExecutionPlan=False)
            
            for subgroup in self._groups:
                if (subgroup.isGrouped() and group.isGrouped() or subgroup == group) and subgroup.groupingItem == group.groupingItem:
                    setDuration(subgroup, value)
            self.setIsDirty(True)
            return True

        elif column == ALIQUOTICITY_INDEX and not isExistsDoneByIndex:
            def setAliquoticity(subgroup, value):
                aliquoticity = forceInt(value)
                if aliquoticity == subgroup.aliquoticity():
                    self.setIsDirty(True)
                    return True
                note = forceStringEx(subgroup.note())
                subgroup.setAliquoticity(forceInt(value), updateExecutionPlan=False)
                self.calcQuantity(subgroup)
                self.updateDosageNomenclatureByIndex(subgroup)
                subgroup.setNote(note, updateExecutionPlan=False)
                
            for subgroup in self._groups:
                if (subgroup.isGrouped() and group.isGrouped() or subgroup == group) and subgroup.groupingItem == group.groupingItem:
                    setAliquoticity(subgroup, value)
            self.setIsDirty(True)
            return True

        elif column == PERIODICITY_INDEX and not isExistsDoneByIndex:
            def setPeriodicity(subgroup, value):
                periodicity = forceInt(value)
                if periodicity == subgroup.periodicity():
                    self.setIsDirty(True)
                    return True
                note = forceStringEx(subgroup.note())
                subgroup.setPeriodicity(forceInt(value), updateExecutionPlan=False)
                self.calcQuantity(subgroup)
                self.updateDosageNomenclatureByIndex(subgroup)
                subgroup.setNote(note, updateExecutionPlan=False)
            
            for subgroup in self._groups:
                if (subgroup.isGrouped() and group.isGrouped() or subgroup == group) and subgroup.groupingItem == group.groupingItem:
                    setPeriodicity(subgroup, value)
            self.setIsDirty(True)
            return True

        elif column == NOTE_INDEX:
            note = forceStringEx(value)
            if note == group.note():
                self.setIsDirty(True)
                return True
            group.setNote(note, updateExecutionPlan=False)
            self.setIsDirty(True)
            return True

        self.emitRowDataChanged(row)
        self.emitAllDataChanged()


    def emitRowDataChanged(self, row):
        self.setIsDirty(True)
        index1 = self.index(row, 0)
        index2 = self.index(row, self.columnCount())
        self.emit(QtCore.SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index1, index2)


    def emitAllDataChanged(self):
        self.setIsDirty(True)
        index1 = self.index(0, 0)
        index2 = self.index(self.rowCount(), self.columnCount())
        self.emit(QtCore.SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index1, index2)


    def emitItemsCountChanged(self):
        self.emit(QtCore.SIGNAL('itemsCountChanged()'))


    def getItemsByIndex(self, index):
        row = index.row()
        if not (0 <= row < len(self._groups)):
            return []

        column = index.column()
        if column in self.STATIC_HEADERS:
            return []

        date = QtCore.QDate(self._date.year(), self._date.month(), column - NOTE_INDEX)
        group = self._groups[row]

        return group.getItemsByDate(date)


    def existsByIndex(self, index):
        return bool(self.getItemsByIndex(index))


    def existsDoneByIndex(self, index):
        items = self.getItemsByIndex(index)
        if not items:
            return False

        for item in items:
            if item.executedDatetime:
                return True
        return False


    def existsDoneActionItemExecToDateByIndex(self, index):
        row = index.row()
        if not (0 <= row < len(self._groups)):
            return False
        column = index.column()
        if column in self.STATIC_HEADERS:
            return False
        date = QtCore.QDate(self._date.year(), self._date.month(), column - NOTE_INDEX)
        group = self._groups[row]
        return group.existsDoneActionItemExecToDate(date)


    def existsDoneAfterIndex(self, index):
        row = index.row()
        if not (0 <= row < len(self._groups)):
            return False

        column = index.column()
        if column in self.STATIC_HEADERS:
            return False

        date = QtCore.QDate(self._date.year(), self._date.month(), column - NOTE_INDEX)
        group = self._groups[row]
        return group.existsDoneAfterDate(date)


    def existsDoneActionAfterIndex(self, index):
        row = index.row()
        if not (0 <= row < len(self._groups)):
            return False

        column = index.column()
        if column in self.STATIC_HEADERS:
            return False

        date = QtCore.QDate(self._date.year(), self._date.month(), column - NOTE_INDEX)
        group = self._groups[row]
        return group.existsDoneActionAfterDate(date)


    def isIndexAfterBegDate(self, index):
        row = index.row()

        if not (0 <= row < len(self._groups)):
            return False

        column = index.column()
        if column in self.STATIC_HEADERS:
            return False

        date = QtCore.QDate(self._date.year(), self._date.month(), column - NOTE_INDEX)
        group = self._groups[row]
        return group.begDate() <= date


    def getDosageUnitName(self, row):
        group = self._groups[row]
        return self._cellsSettings.getNomenclatureDosageUnitName(group.nomenclatureId)


    def setItemsForDayIndex(self, index, items, isApplyChangesCourseNextDays=False):
        row = index.row()
        if not (0 <= row < len(self._groups)):
            return

        column = index.column()
        if column in self.STATIC_HEADERS:
            return

        if isApplyChangesCourseNextDays:
            group = self._groups[row]
            cols = self.cols()
            for col in range(column, len(cols)):
                if col not in self.STATIC_HEADERS:
                    date = QtCore.QDate(self._date.year(), self._date.month(), col - NOTE_INDEX)
                    itemsAlreadyExists = bool(group.getItemsByDate(date))
                    if itemsAlreadyExists:
                        group.setItemsByDate(date, items)
        else:
            date = QtCore.QDate(self._date.year(), self._date.month(), column - NOTE_INDEX)
            group = self._groups[row]
            itemsAlreadyExists = bool(group.getItemsByDate(date))
            group.setItemsByDate(date, items)
            if not itemsAlreadyExists:
                maxDate = group.getMaxItemDate()
                group.setDuration(group.begDate().daysTo(maxDate) + 1, updateExecutionPlan=False)


    def setDurationForDayIndex(self, index, quantityDay, skipAfterLastDayCourse=0, isLastDayCourse=False):
        row = index.row()
        if not (0 <= row < len(self._groups)):
            return
        if quantityDay > 0:
            group = self._groups[row]
            for subgroup in self._groups:
                if (subgroup.isGrouped() and group.isGrouped() or subgroup == group) and subgroup.groupingItem == group.groupingItem:
                    maxDate = subgroup.getMaxItemDate()
                    quantity = forceInt(calcQuantityEx(subgroup.aliquoticity(), subgroup.periodicity(), quantityDay))
                    quantityAdd = quantity if quantity else 1
                    items = subgroup.addDaysToEP(daysCount=quantityDay, quantityAdd=quantityAdd, skipAfterLastDayCourse=skipAfterLastDayCourse, isLastDayCourse=isLastDayCourse)
                    if not isLastDayCourse:
                        self.updateDosageNomenclatureFromDate(subgroup, maxDate)
                    newMaxDate = subgroup.getMaxItemDate()
                    subgroup.setDuration(subgroup.begDate().daysTo(newMaxDate) + 1, updateExecutionPlan=False)
        return items


    def deleteItemsByIndex(self, index):
        row = index.row()
        if not (0 <= row < len(self._groups)):
            return

        column = index.column()
        if column in self.STATIC_HEADERS:
            return

        date = QtCore.QDate(self._date.year(), self._date.month(), column - NOTE_INDEX)
        group = self._groups[row]
        for subgroup in self._groups:
            if (subgroup.isGrouped() and group.isGrouped() or subgroup == group) and subgroup.groupingItem == group.groupingItem:
                subgroup.deleteItemsByDate(date)
    
    
    def sort(self, column, order=Qt.AscendingOrder):
        self._groups.sort(key=lambda item: (item.groupingItem if item.groupingItem else item.firstItem.action.getBegDatetime(), 0 if item.groupingInfo else float('inf'), item.proxyRows[0] if item.proxyRows else float('inf'), item.firstItem.action.getBegDatetime()), reverse=order)
        self.reset()
