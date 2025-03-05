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
from PyQt4.QtCore import Qt, pyqtSignature, SIGNAL, QVariant, QDate

from library.DialogBase         import CDialogBase
from library.Utils              import forceInt, forceRef, forceString, smartDict, trim, toVariant, forceDate, forceStringEx, forceDateTime, forceDouble, forceTime, addDotsEx
from library.InDocTable         import CRecordListModel, CBoolInDocTableCol, CRBInDocTableCol, CFloatInDocTableCol, CInDocTableCol, CDateInDocTableCol, CIntInDocTableCol
from library.ICDInDocTableCol   import CICDExInDocTableCol
from library.crbcombobox        import CRBComboBox
from Events.Action              import CActionType, CActionTypeCache, CAction
from Events.ActionProperty      import CNomenclatureActionPropertyValueType, CNomenclatureUsingTypeActionPropertyValueType, CToothActionPropertyValueType
from Events.ActionsSelectorSelectedTable import CCheckedActionsModel, _getNomenclatureValues
from Events.ActionsSelector     import CActionsModel, CActionTypeGroupsTemplatesModel, CActionTypesSelectionManager
from Events.NomenclatureExpense.QueriesStatements import getNomenclatureActionTypesIds
from Events.ExecutionPlan.ExecutionPlanType import executionPlanType
from Events.Utils               import getEventIncludeTooth
from Stock.Utils                 import getExistsNomenclatureAmount
from RefBooks.ActionTypeGroup.RBActionTypeGroupEditor import CSmnnInDocTableCol, CLfFormInDocTableCol

from Events.NomenclatureExpense.Ui_NomenclatureExpenseLoadTemplate import Ui_LoadTemplateDialog

_TREE_TAB_INDEX = 0
_TEMPLATES_TAB_INDEX = 1

_RECIPE = 1
_DOSES  = 2
_SIGNA  = 3
_ACTIVESUBSTANCE = 4


class CNomenclatureExpenseLoadTemplate(CDialogBase, CActionTypesSelectionManager, Ui_LoadTemplateDialog):
    def __init__(self, parent, eventEditor, eventTypeId=None, _class=None):
        CDialogBase.__init__(self, parent)
        self.eventEditor = eventEditor
        self.existsActionTypesList = []
        self.addModels('ActionTypes', CActionsModel(self))
        self.addModels('SelectedActionTypes', CCheckedSelectedActionTypesModel(self,
                                                                   None,
                                                                   self.modelActionTypes,
                                                                   getEventIncludeTooth(eventTypeId),
                                                                   nomenclatureLS = True))
        self.addModels('Templates', CActionTypeGroupsNETemplatesModel(self))
        self.setupUi(self)
        self.setModels(self.tblActionTypes, self.modelActionTypes, self.selectionModelActionTypes)
        self.setModels(self.tblSelectedActionTypes, self.modelSelectedActionTypes, self.selectionModelSelectedActionTypes)
        self.setModels(self.tblTemplates, self.modelTemplates, self.selectionModelTemplates)
        self.tblTemplates.addPopupDelRow()
#        self.tblSelectedActionTypes.addGetExecutionPlan()
#        self.tblSelectedActionTypes.addInsertSameAction()
        self.tblSelectedActionTypes.addSelectAllUrgentAction()
        self.tblSelectedActionTypes.addClearSelectionUrgentAction()
        self.tblSelectedActionTypes.enableColsHide()
        self.tblSelectedActionTypes.enableColsMove()
        self.orgStructureId = None
        self.classFirstUpdate = True
        self.actionTypeId = None
        self.selectedActionTypeIdList = []
        self.contractSum = 0
        self.sumDeposit = 0.0
        self.actionTypeClasses = []
        self.cmbClass.setCurrentIndex((_class + 1) if _class is not None else 0)
        self.actionsCacheByCode = {}
        self.actionsCodeCacheByName = {}
        self._sortActionType = smartDict(order='code, name', isAscending=False, column=0)
        self._sortTemplates = smartDict(order='ActionTypeGroup.code, ActionTypeGroup.name', isAscending=False, column=0)
        self.connect(self.modelSelectedActionTypes, SIGNAL('pricesAndSumsUpdated()'), self.on_pricesAndSumsUpdated)
        self.connect(self.tblActionTypes.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.on_sortActions)
        self.connect(self.tblTemplates.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.on_sortTemplates)
        self.setFocusToWidget(self.edtFindByCode)
        self.modelTemplates.setFilter(self.setActionTypeFilter())


    def setActionTypeNomenclatureIdList(self):
        db = QtGui.qApp.db
        table = db.table('ActionType')
        idList = getNomenclatureActionTypesIds()
        descendants = []
        for id in idList:
            descendants.extend(db.getDescendants(table, 'group_id', id))
        return db.getTheseAndParents(table, 'group_id', descendants)


    def setActionTypeFilter(self):
        idList = self.setActionTypeNomenclatureIdList()
        return u'ActionTypeGroup.id IN (SELECT ActionTypeGroup_Item.master_id FROM ActionTypeGroup_Item WHERE ActionTypeGroup_Item.deleted = 0 AND ActionTypeGroup_Item.actionType_id IN (%s))'%(u','.join(str(id) for id in idList if id))


    @pyqtSignature('int')
    def on_cmbClass_currentIndexChanged(self, index):
        self.actionTypeClasses = [index-1] if index else range(4)
        if not self.classFirstUpdate:
            self.updateTemplates()
        else:
            self.classFirstUpdate = False


    def exec_(self):
        self.updateTemplates()
        return CDialogBase.exec_(self)


    def setActionTypeId(self, actionTypeId):
        self.actionTypeId = actionTypeId
        self.modelTemplates.setActionTypeId(actionTypeId)


    def updateTemplates(self):
        self.modelTemplates.loadData(self.actionTypeClasses[0] if len(self.actionTypeClasses) == 1 else None)
        self._updateActionTypesByTemplate()


    def _updateActionTypesByTemplate(self):
        templateId = self.tblTemplates.currentItemId()
        if not templateId:
            self.tblActionTypes.setIdList([])
            return
        idList = self.setActionTypeNomenclatureIdList()
        if not idList:
            self.tblActionTypes.setIdList([])
            return
        db = QtGui.qApp.db
        table = db.table('ActionTypeGroup_Item')
        idList = db.getDistinctIdList(
            table, 'actionType_id', where=[table['deleted'].eq(0), table['master_id'].eq(templateId), table['actionType_id'].inlist(idList)]
        )
        self.tblActionTypes.setIdList(idList)


    def getActionTypeItemsByTemplate(self, actionTypeId):
        templateId = self.tblTemplates.currentItemId()
        if not templateId:
            self.tblActionTypes.setIdList([])
            return None
        db = QtGui.qApp.db
        table = db.table('ActionTypeGroup_Item')
        return db.getRecordList(table, '*', [table['deleted'].eq(0), table['master_id'].eq(templateId), table['actionType_id'].eq(actionTypeId)], [table['id'].name()])


    def getPlanItemsByTemplate(self, templateItemId):
        db = QtGui.qApp.db
        tablePI = db.table('ActionTypeGroup_Plan_Item')
        tablePIN = db.table('ActionTypeGroup_Plan_Item_Nomenclature')
        queryTable = tablePI.innerJoin(tablePIN, tablePIN['master_id'].eq(tablePI['id']))
        cols = [tablePI['id'].alias('piId'),
                tablePI['master_id'].alias('piMasterId'),
                tablePI['idx'],
                tablePI['date_idx'],
                tablePI['time'],
                tablePI['group_id'],
                tablePIN['id'].alias('pinId'),
                tablePIN['master_id'].alias('pinMasterId'),
                tablePIN['nomenclature_id'],
                tablePIN['dosage'],
                ]
        cond = [tablePI['master_id'].eq(templateItemId)]
        return db.getRecordList(queryTable, cols, cond, [tablePI['idx'].name()])


    @pyqtSignature('const QModelIndex&,const QModelIndex&')
    def on_selectionModelTemplates_currentChanged(self, current, previous):
        isEnabled = False
        self._updateActionTypesByTemplate()
        templateId = self.tblTemplates.currentItemId()
        if templateId:
            db = QtGui.qApp.db
            table = db.table('ActionTypeGroup')
            record = db.getRecordEx(table, [table['createPerson_id']], [table['id'].eq(templateId), table['deleted'].eq(0)])
            createPersonId = forceRef(record.value('createPerson_id')) if record else None
            isEnabled = createPersonId and createPersonId == QtGui.qApp.userId
        self.btnUpdateTemplate.setEnabled(isEnabled)


    def getMESqwt(self, actionTypeId):
        return None


    def getPrice(self, actionTypeId, contractId, financeId):
        return None


    def getClientId(self):
        return self.eventEditor.clientId


    def getMedicalAidKindId(self):
        return self.eventEditor.eventMedicalAidKindId


    def getFinanceId(self):
        return self.eventEditor.eventFinanceId


    def setOrgStructureId(self, value):
        self.orgStructureId = value
        self.modelSelectedActionTypes.setOrgStructureId(value)
        self.tblSelectedActionTypes.setOrgStructureId(value)


    def insertActionIntoCheckedModel(self, actionTypeId, recipe=None, doses=None, signa=None, duration=None, periodicity=None, aliquoticity=None, offset=0, piRecords=None, templateId=None, smnnUUID=None, lfFormId=None, actionPropertyTemplateId=None):
        row = self.modelSelectedActionTypes.add(actionTypeId, self.getMESqwt(actionTypeId), recipe=recipe, doses=doses, signa=signa, duration=duration, periodicity=periodicity, aliquoticity=aliquoticity, offset=offset, piRecords=piRecords, templateId=templateId, smnnUUID=smnnUUID, lfFormId=lfFormId, actionPropertyTemplateId=actionPropertyTemplateId)
        self.setExistQntRows(recipe, row)


    def setExistQntRows(self, recipe, row):
        existQnt = getExistsNomenclatureAmount(recipe, financeId = self.getFinanceId(), medicalAidKindId = self.getMedicalAidKindId(), orgStructureId=self.orgStructureId)
        if existQnt <= 0:
            self.modelSelectedActionTypes.addExistQntRows(row)
        else:
            self.modelSelectedActionTypes.removedExistQntRows(row)


    def updatePresetValuesConditions(self, action):
        apm = action.executionPlanManager
        if not apm.currentItem:
            return
        firstItem = apm.currentItem
        action.updatePresetValuesConditions({
            'courseDate': firstItem.date,
            'courseTime': firstItem.time,
            'firstInCourse': True
        })


    def getSelectedActionList(self):
        result = []
        for actionTypeId in self.selectedActionTypeIdList:
            actions = self.modelSelectedActionTypes.getSelectedAction(actionTypeId)
            for action in actions:
                self.updatePresetValuesConditions(action)
                action.initPresetValues()
                if not action.deleteMark:
                    result.append(action)
        return result


    def getSelectedList(self):
        return self.getSelectedActionList()


    def setSelected(self, actionTypeId, value, resetMainModel=False):
        present = self.isSelected(actionTypeId)
        if value:
            if not present:
                self.selectedActionTypeIdList.append(actionTypeId)
                records = self.getActionTypeItemsByTemplate(actionTypeId)
                for record in records:
                    recipe = forceRef(record.value('nomenclature_id'))
                    doses = forceString(record.value('doses'))
                    smnnUUID = forceStringEx(record.value('smnnUUID'))
                    lfFormId = forceRef(record.value('lfForm_id'))
                    actionPropertyTemplateId = forceRef(record.value('actionPropertyTemplate_id'))
                    signa = forceString(record.value('signa'))
                    duration = forceInt(record.value('duration'))
                    periodicity = forceInt(record.value('periodicity'))
                    aliquoticity = forceInt(record.value('aliquoticity'))
                    offset = forceInt(record.value('offset'))
                    templateItemId = forceRef(record.value('id'))
                    templateId = forceRef(record.value('master_id'))
                    piRecords = self.getPlanItemsByTemplate(templateItemId) if templateItemId else None
                    self.insertActionIntoCheckedModel(actionTypeId, recipe, doses, signa, duration, periodicity, aliquoticity, offset=offset, piRecords=piRecords, templateId=templateId, smnnUUID=smnnUUID, lfFormId=lfFormId, actionPropertyTemplateId=actionPropertyTemplateId)
                self.updateSelectedCount()
                if resetMainModel:
                    self.modelActionTypes.emitDataChanged()
                return True
        else:
            if present:
                self.selectedActionTypeIdList.remove(actionTypeId)
                self.modelSelectedActionTypes.remove(actionTypeId)
                self.updateSelectedCount()
                if resetMainModel:
                    self.modelActionTypes.emitDataChanged()
                return True
        return False


    def on_pricesAndSumsUpdated(self):
        sum = self.modelSelectedActionTypes.getTotalSum()
        text = u'Назначить: %.2f' % sum if sum else u'Назначить'
        self.lblSelectedActionTypes.setText(text)
        payDeposit = 0.0
        if self.contractSum:
            self.sumDeposit = self.getSumDepositForContract()
            payDeposit = self.contractSum - (self.sumDeposit + sum)
            self.lblDeposit.setText(u'Остаток по депозиту = %s  '%forceString(payDeposit))
        if payDeposit < 0 and self.contractSum:
            palette = QtGui.QPalette()
            brush = QtGui.QBrush(QtGui.QColor(255, 0, 0))
            brush.setStyle(Qt.SolidPattern)
            palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.WindowText, brush)
            brush = QtGui.QBrush(QtGui.QColor(255, 0, 0))
            brush.setStyle(Qt.SolidPattern)
            palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.WindowText, brush)
            brush = QtGui.QBrush(QtGui.QColor(144, 141, 139))
            brush.setStyle(Qt.SolidPattern)
            palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.WindowText, brush)
            self.lblDeposit.setPalette(palette)
        elif self.contractSum:
            palette = QtGui.QPalette()
            brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
            brush.setStyle(Qt.SolidPattern)
            palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.WindowText, brush)
            brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
            brush.setStyle(Qt.SolidPattern)
            palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.WindowText, brush)
            brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
            brush.setStyle(Qt.SolidPattern)
            palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.WindowText, brush)
            self.lblDeposit.setPalette(palette)


    def on_sortActions(self, logicalIndex):
        header = self.tblActionTypes.horizontalHeader()
        if logicalIndex:
            self._sortActionType.order = 'code %s, name' if logicalIndex == 1 else 'name %s, code'
            if self._sortActionType.column == logicalIndex:
                self._sortActionType.isAscending = not self._sortActionType.isAscending
            else:
                self._sortActionType.column = logicalIndex
                self._sortActionType.isAscending = True
            header.setSortIndicatorShown(True)
            header.setSortIndicator(self._sortActionType.column, Qt.AscendingOrder if self._sortActionType.isAscending else Qt.DescendingOrder)
            if self._sortActionType.isAscending:
                self._sortActionType.order = self._sortActionType.order % 'ASC'
            else:
                self._sortActionType.order = self._sortActionType.order % 'DESC'
        else:
            if self._sortActionType.column != logicalIndex:
                header.setSortIndicatorShown(False)
                self._sortActionType.order = 'code, name'
                self._sortActionType.column = 0


    def on_sortTemplates(self, logicalIndex):
        header = self.tblTemplates.horizontalHeader()
        self._sortTemplates.order = 'ActionTypeGroup.name %s' if logicalIndex else 'ActionTypeGroup.code %s'
        if self._sortTemplates.column == logicalIndex:
            self._sortTemplates.isAscending = not self._sortTemplates.isAscending
        else:
            self._sortTemplates.column = logicalIndex
            self._sortTemplates.isAscending = True
        header.setSortIndicatorShown(True)
        header.setSortIndicator(self._sortTemplates.column, Qt.AscendingOrder if self._sortTemplates.isAscending else Qt.DescendingOrder)
        if self._sortTemplates.isAscending:
            self._sortTemplates.order = self._sortTemplates.order % 'ASC'
        else:
            self._sortTemplates.order = self._sortTemplates.order % 'DESC'
        self.modelTemplates.setTemplatesOrder(self._sortTemplates.order)


    def _updateActionTypesByTree(self, current):
        if current.isValid() and current.internalPointer():
            actionTypeId = current.internalPointer().id()
            _class = current.internalPointer().class_()
        else:
            actionTypeId = None
            _class = None
        self.setGroupId(actionTypeId, _class)
        text = trim(self.edtFindByCode.text())
        if text:
            self.on_edtFindByCode_textChanged(text)


    @pyqtSignature('QString')
    def on_edtFindByCode_textChanged(self, text):
        if text:
            row = self.findByCode(text)
            if row is not None:
                self.tblActionTypes.setCurrentRow(row)
            else:
                self.tblActionTypes.setCurrentRow(0)
        else:
            self.tblActionTypes.setCurrentRow(0)


    @pyqtSignature('const QModelIndex&,const QModelIndex&')
    def on_selectionModelActionTypeGroups_currentChanged(self, current, previous):
        self._updateActionTypesByTree(current)


    def setGroupId(self, groupId, _class=None):
        if not self.actionTypeClasses:
            return
        self.actionsCacheByCode.clear()
        self.actionsCodeCacheByName.clear()
        db = QtGui.qApp.db
        tableActionType = db.table('ActionType')
        cond = [tableActionType['deleted'].eq(0),
                tableActionType['showInForm'].ne(0),
                tableActionType['class'].inlist(self.actionTypeClasses)
               ]
        if groupId:
            groupIdList = db.getDescendants('ActionType', 'group_id', groupId)
            cond.append(tableActionType['group_id'].inlist(groupIdList))
        if _class is not None:
            cond.append(tableActionType['class'].eq(_class))
        cond.append('NOT EXISTS(SELECT id FROM ActionType AS at WHERE at.group_id = ActionType.id)')
        recordList = QtGui.qApp.db.getRecordListGroupBy(tableActionType, 'id, code, name', cond, 'code',  self._sortActionType.order)
        if recordList:
            idList = []
            for index, record in enumerate(recordList):
                id = forceRef(record.value('id'))
                code = forceString(record.value('code')).upper()
                name = forceString(record.value('name')).upper()
                idList.append(id)
                existCode = self.actionsCacheByCode.get(code, None)
                if existCode is None:
                    self.actionsCacheByCode[code] = index
                existName = self.actionsCodeCacheByName.get(name, None)
                if existName is None:
                    self.actionsCodeCacheByName[name] = code
        else:
            idList = []
        self.tblActionTypes.setIdList(idList)


    @pyqtSignature('')
    def on_btnUpdateTemplate_pressed(self):
        templateId = self.tblTemplates.currentItemId()
        if not templateId:
            return
        class_ = self.actionTypeClasses[0] if len(self.actionTypeClasses) == 1 else None
        db = QtGui.qApp.db
        db.transaction()
        try:
            table = db.table('ActionTypeGroup_Item')
            items = self.tblSelectedActionTypes.model().items()
            mapActionTypeIdToPropertyValues = self.tblSelectedActionTypes.model()._mapActionTypeIdToPropertyValues
            idRowToAction = self.tblSelectedActionTypes.model()._idRowToAction
            recordTemplates = self.tblTemplates.model().getRecordById(templateId)
            isOffset = forceInt(recordTemplates.value('isOffset')) if recordTemplates else 0
            groupsList = self.tblSelectedActionTypes.model()._rowToAction.values()
            groupsList.sort(key=lambda x: forceDate(x.getRecord().value('begDate')))
            offsetDate = forceDate(groupsList[0].getRecord().value('begDate')) if len(groupsList) > 0 else None
            rows = []
            db.deleteRecord(table, [table['master_id'].eq(templateId), table['deleted'].eq(0)])
            for actionTypeId in self.selectedActionTypeIdList:
                for row, item in enumerate(items):
                    if row not in rows and actionTypeId == forceRef(item.value('actionType_id')):
                        newRecord = table.newRecord()
                        newRecord.setValue('master_id', templateId)
                        newRecord.setValue('actionType_id', actionTypeId)
                        fieldNameRecipe = item.fieldName(item.indexOf('recipe'))
                        fieldNameDoses = item.fieldName(item.indexOf('doses'))
                        fieldNameSigna = item.fieldName(item.indexOf('signa'))
                        fieldNameActiveSubstance = item.fieldName(item.indexOf('activeSubstance_id'))
                        fieldNameSmnnUUID = item.fieldName(item.indexOf('smnnUUID'))
                        fieldNameLfFormId = item.fieldName(item.indexOf('lfForm_id'))
                        fieldNameActionPropertyTemplateId = item.fieldName(item.indexOf('actionPropertyTemplate_id'))
                        action = idRowToAction[(actionTypeId, row)]
                        if action:
                            record = action.getRecord()
                            if record:
                                begDate = forceDate(record.value('begDate'))
                                values = mapActionTypeIdToPropertyValues.get(actionTypeId, None)
                                if values:
                                    if fieldNameRecipe == 'recipe' and forceString(fieldNameRecipe) in values.keys():
                                        value = values[forceString(fieldNameRecipe)]
                                        if u'propertyType' in value.keys():
                                            propertyType = value['propertyType']
                                            if propertyType.inActionsSelectionTable == _RECIPE:
                                                property = action.getPropertyById(propertyType.id)
                                                newRecord.setValue('nomenclature_id', toVariant(property.getValue()))
                                    if fieldNameDoses == 'doses' and forceString(fieldNameDoses) in values.keys():
                                        value = values[forceString(fieldNameDoses)]
                                        if u'propertyType' in value.keys():
                                            propertyType = value['propertyType']
                                            if propertyType.inActionsSelectionTable == _DOSES:
                                                property = action.getPropertyById(propertyType.id)
                                                newRecord.setValue('doses', toVariant(property.getText()))
                                    if fieldNameSigna == 'signa' and forceString(fieldNameSigna) in values.keys():
                                        value = values[forceString(fieldNameSigna)]
                                        if u'propertyType' in value.keys():
                                            propertyType = value['propertyType']
                                            if propertyType.inActionsSelectionTable == _SIGNA:
                                                property = action.getPropertyById(propertyType.id)
                                                newRecord.setValue('signa', toVariant(property.getValue()))
                                    if fieldNameActiveSubstance == 'activeSubstance_id' and forceString(fieldNameActiveSubstance) in values.keys():
                                        value = values[forceString(fieldNameActiveSubstance)]
                                        if u'propertyType' in value.keys():
                                            propertyType = value['propertyType']
                                            if propertyType.inActionsSelectionTable == _ACTIVESUBSTANCE:
                                                property = action.getPropertyById(propertyType.id)
                                                newRecord.setValue('activeSubstance_id', toVariant(property.getValue()))
                                    if fieldNameSmnnUUID == 'smnnUUID' and forceString(fieldNameSmnnUUID) in values.keys():
                                        value = values[forceString(fieldNameSmnnUUID)]
                                        if u'propertyType' in value.keys():
                                            propertyType = value['propertyType']
                                            if propertyType.isNomenclatureSmnnActionPropertyValueType():
                                                property = action.getPropertyById(propertyType.id)
                                                newRecord.setValue('smnnUUID', toVariant(property.getValue()))
                                    if fieldNameLfFormId == 'lfForm_id' and forceString(fieldNameLfFormId) in values.keys():
                                        value = values[forceString(fieldNameLfFormId)]
                                        if u'propertyType' in value.keys():
                                            propertyType = value['propertyType']
                                            if propertyType.isNomenclatureSmnnGrlsLfActionPropertyValueType():
                                                property = action.getPropertyById(propertyType.id)
                                                newRecord.setValue('lfForm_id', toVariant(property.getValue()))
                                    if fieldNameActionPropertyTemplateId == 'actionPropertyTemplate_id' and forceString(fieldNameActionPropertyTemplateId) in values.keys():
                                        value = values[forceString(fieldNameActionPropertyTemplateId)]
                                        if u'propertyType' in value.keys():
                                            propertyType = value['propertyType']
                                            if propertyType.isNomenclatureCalculationParamActionPropertyValueType():
                                                property = action.getPropertyById(propertyType.id)
                                                newRecord.setValue('actionPropertyTemplate_id', toVariant(property.getValue()))
                                newRecord.setValue('duration', toVariant(action.getDuration()))
                                newRecord.setValue('periodicity', toVariant(action.getPeriodicity()))
                                newRecord.setValue('aliquoticity', toVariant(action.getAliquoticity()))
                                offset = offsetDate.daysTo(begDate) if (isOffset and offsetDate) else 0
                                newRecord.setValue('offset', toVariant(offset))
                                actionTypeGroupItemId = db.insertRecord(table, newRecord)
                                rows.append(row)
                                if actionTypeGroupItemId:
                                    items = action.getExecutionPlan().items
                                    if items:
                                        tablePI = db.table('ActionTypeGroup_Plan_Item')
                                        tablePINomenclature = db.table('ActionTypeGroup_Plan_Item_Nomenclature')
                                        for item in items:
                                            idx = item.idx
                                            time = item.time
                                            date = item.date
                                            dateIdx = (begDate.daysTo(item.date) + 1) if begDate != date else 1
                                            newRecordPI = tablePI.newRecord()
                                            newRecordPI.setValue('master_id', toVariant(actionTypeGroupItemId))
                                            newRecordPI.setValue('idx', toVariant(idx))
                                            newRecordPI.setValue('date_idx', toVariant(dateIdx))
                                            newRecordPI.setValue('time', toVariant(time))
                                            planItemId = db.insertRecord(tablePI, newRecordPI)
                                            if planItemId and item.nomenclature:
                                                doses = item.nomenclature.dosage
                                                nomenclatureId = item.nomenclature.nomenclatureId
                                                newRecordPIN = tablePINomenclature.newRecord()
                                                newRecordPIN.setValue('master_id', toVariant(planItemId))
                                                newRecordPIN.setValue('nomenclature_id', toVariant(nomenclatureId))
                                                newRecordPIN.setValue('dosage', toVariant(doses))
                                                db.insertRecord(tablePINomenclature, newRecordPIN)
            self.modelTemplates.reloadData(class_)
            self.tblTemplates.setCurrentItemId(templateId)
        except:
            db.rollback()
            raise
        else:
            db.commit()


    @pyqtSignature('')
    def on_btnFindTemplates_clicked(self):
        self.modelTemplates.setFindFilterText(unicode(self.edtFindTemplates.text()))
        self.modelTemplates.loadData(self.actionTypeClasses[0] if len(self.actionTypeClasses) == 1 else None)
        self._updateActionTypesByTemplate()


class CCheckedSelectedActionTypesModel(CCheckedActionsModel):
    def __init__(self, parent, existsActionsModel, actionTypesModel=None, includeTooth=False, nomenclatureLS=False):
        CCheckedActionsModel.__init__(self, parent, existsActionsModel, actionTypesModel, includeTooth, nomenclatureLS)
        self._cols = []
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
#        self.addExtCol(CInDocTableCol(u'Signa', 'signa', 10), QVariant.String)
        self.addExtCol(CRBInDocTableCol(u'Signa', 'signa', 10, 'rbNomenclatureUsingType', showFields=2),
                       QVariant.Int)
        self.addExtCol(CInDocTableCol(u'Действующее вещество', 'activeSubstance_id', 10),
                       QVariant.String)
        self.addExtCol(CSmnnInDocTableCol(u'МНН', 'smnnUUID', 22), QVariant.String)
        self.addExtCol(CLfFormInDocTableCol(u'Форма выпуска', 'lfForm_id',  10, 'rbLfForm'), QVariant.Int)
        self.addExtCol(CRBInDocTableCol(u'Параметр расчета', 'actionPropertyTemplate_id', 10, 'ActionPropertyTemplate', showFields=CRBComboBox.showCodeAndName, filter=u'ActionPropertyTemplate.isCalcParamDoseNomenclatureExpense=1'),
                       QVariant.Int)
#        if nomenclatureLS:
#            self.addExtCol(CIntInDocTableCol(u'Шаг', 'offset', 10), QVariant.Int)
        self._existsActionsModel = existsActionsModel
        self._actionTypesModel   = actionTypesModel
        self.clientId = None
        # self.medicalAidKindId = parent.eventEditor.eventMedicalAidKindId if parent.eventEditor.eventMedicalAidKindId else None
        self.medicalAidKindId = parent.eventEditor.eventMedicalAidKindId if hasattr(parent.eventEditor,
                                'eventMedicalAidKindId') and parent.eventEditor.eventMedicalAidKindId else None
        self.parentWidget = parent
        self._table            = QtGui.qApp.db.table('Action')
        self._dbFieldNamesList = [field.fieldName.replace('`', '') for field in self._table.fields]
        self.prices = []
        self._mapPropertyTypeCellsActivity = {}
        self.existQntRows = []
        self._nomenclatureAnalogCache = {}
        self.orgStructureId = None
        self._propertyColsNames = ['recipe', 'doses', 'signa', 'activeSubstance_id', 'smnnUUID', 'lfForm_id', 'actionPropertyTemplate_id']
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

            if propertyType.isNomenclatureSmnnActionPropertyValueType():
                column = self.getColIndex(u'smnnUUID')
                result = self._mapPropertyTypeCellsActivity.get((row, column), None)
                if result is None:
                    self._cols[column].setValueType(propertyType.valueType.variantType)
                    self._mapPropertyTypeCellsActivity[(row, column)] = True
                    cellName = u'smnnUUID'
                    cellSettings[cellName] = True
                    values = self._mapActionTypeIdToPropertyValues.get(actionTypeId, None)
                    if values is None:
                        values = {cellName: {'propertyType': propertyType, 'value':QVariant()}}
                        self._mapActionTypeIdToPropertyValues[actionTypeId] = values
                    else:
                        values[cellName] = {'propertyType': propertyType, 'value':QVariant()}

            if propertyType.isNomenclatureSmnnGrlsLfActionPropertyValueType():
                column = self.getColIndex(u'lfForm_id')
                result = self._mapPropertyTypeCellsActivity.get((row, column), None)
                if result is None:
                    self._cols[column].setValueType(propertyType.valueType.variantType)
                    self._mapPropertyTypeCellsActivity[(row, column)] = True
                    cellName = u'lfForm_id'
                    cellSettings[cellName] = True
                    values = self._mapActionTypeIdToPropertyValues.get(actionTypeId, None)
                    if values is None:
                        values = {cellName: {'propertyType': propertyType, 'value':QVariant()}}
                        self._mapActionTypeIdToPropertyValues[actionTypeId] = values
                    else:
                        values[cellName] = {'propertyType': propertyType, 'value':QVariant()}

            if propertyType.isNomenclatureCalculationParamActionPropertyValueType():
                column = self.getColIndex(u'actionPropertyTemplate_id')
                result = self._mapPropertyTypeCellsActivity.get((row, column), None)
                if result is None:
                    self._cols[column].setValueType(propertyType.valueType.variantType)
                    self._mapPropertyTypeCellsActivity[(row, column)] = True
                    cellName = u'actionPropertyTemplate_id'
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


    def add(self, actionTypeId, amount=None, financeId=None, contractId=None, recipe=None, doses=None, signa=None, duration=None, periodicity=None, aliquoticity=None, offset=0, piRecords=None, quantity=None, activeSubstanceId=None, templateId=None, smnnUUID=None, lfFormId=None, actionPropertyTemplateId=None):
        row = len(self._items)
        record = self.getEmptyRecord(self.getPropertyTypeCellsSettings(actionTypeId, row))
        action = CAction.getFilledAction(self.parentWidget.eventEditor, record, actionTypeId, orgStructureId=self.orgStructureId, initPresetValues=True)
        action.setOrgStructureId(self.orgStructureId)
        record.setValue('checked', QVariant(Qt.Checked))
        record.setValue('price', QVariant(self.getPrice(record)))
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
            property.preApplyDependents(action)
            if propertyType.inActionsSelectionTable == _RECIPE:
                propertyName = propertyType.name
                if action and propertyName:
                    action[propertyName] = recipe
                record.setValue('recipe', QVariant(recipe))
            property.applyDependents(action)
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
        if templateId:
            record.setValue('actionTypeGroup_id', QVariant(templateId))
        if smnnUUID:
            fieldNameSmnnUUID = record.fieldName(record.indexOf('smnnUUID'))
            propertyType = values[forceString(fieldNameSmnnUUID)]['propertyType']
            property     = action.getPropertyById(propertyType.id)
            if propertyType.isNomenclatureSmnnActionPropertyValueType():
                property.preApplyDependents(action)
                propertyName = propertyType.name
                if action and propertyName:
                    action[propertyName] = smnnUUID
                record.setValue('smnnUUID', QVariant(smnnUUID))
                property.applyDependents(action)
        if lfFormId:
            fieldNameLfFormId = record.fieldName(record.indexOf('lfForm_id'))
            propertyType = values[forceString(fieldNameLfFormId)]['propertyType']
            property     = action.getPropertyById(propertyType.id)
            if propertyType.isNomenclatureSmnnGrlsLfActionPropertyValueType():
                property.preApplyDependents(action)
                propertyName = propertyType.name
                if action and propertyName:
                    action[propertyName] = lfFormId
                record.setValue('lfForm_id', QVariant(lfFormId))
                property.applyDependents(action)
        if actionPropertyTemplateId:
            fieldNameActionPropertyTemplateId = record.fieldName(record.indexOf('actionPropertyTemplate_id'))
            propertyType = values[forceString(fieldNameActionPropertyTemplateId)]['propertyType']
            property     = action.getPropertyById(propertyType.id)
            if propertyType.isNomenclatureCalculationParamActionPropertyValueType():
                property.preApplyDependents(action)
                propertyName = propertyType.name
                if action and propertyName:
                    action[propertyName] = actionPropertyTemplateId
                record.setValue('actionPropertyTemplate_id', QVariant(actionPropertyTemplateId))
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
                    epItem.groupingItem = (forceInt(piRecord.value('group_id')), forceInt(piRecord.value('group_id')) == forceInt(piRecord.value('piId')))
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


    def setOrgStructureId(self, value):
        self.orgStructureId = value


    def getNomenclatureAnalog(self, nomenclatureId):
        if nomenclatureId not in self._nomenclatureAnalogCache.keys():
            db = QtGui.qApp.db
            record = db.getRecord('rbNomenclature', 'analog_id', nomenclatureId)
            analogId = forceRef(record.value('analog_id')) if record else None
            self._nomenclatureAnalogCache[nomenclatureId] = analogId
        return self._nomenclatureAnalogCache.get(nomenclatureId, None)


    def addExistQntRows(self, row):
        if row >= 0 and row not in self.existQntRows:
            self.existQntRows.append(row)


    def removedExistQntRows(self, row):
        while row in self.existQntRows:
            self.existQntRows.remove(row)


    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.FontRole:
            row = index.row()
            record = self._items[row]
            actionTypeId = forceRef(record.value('actionType_id'))
            if row >= 0 and row in self.existQntRows:
                    result = QtGui.QFont()
                    result.setWeight(QtGui.QFont.DemiBold)
                    return QVariant(result)
            elif self._existsActionsModel and self._existsActionsModel.hasActionTypeId(actionTypeId):
                return self._qBoldFont
        return CCheckedActionsModel.data(self, index, role)


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
        if fieldName == 'recipe':
            oldNomenclatureId = forceRef(record.value('recipe')) if record else None
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
        elif fieldName == 'duration':
            if not actionType.isNomenclatureExpense:
                pass
            else:
                self.updatePlannedEndDate(row)
                if actionType.isDoesNotInvolveExecutionCourse:
                    actionTypeId = forceRef(record.value('actionType_id'))
                    self.updateNomenclatureDosage(actionTypeId, actionType, record, row)
                self.updateExecutionPlanByRecord(row)
        elif fieldName == 'periodicity':
            if not actionType.isNomenclatureExpense:
                pass
            else:
                if actionType.isDoesNotInvolveExecutionCourse:
                    actionTypeId = forceRef(record.value('actionType_id'))
                    self.updateNomenclatureDosage(actionTypeId, actionType, record, row)
                self.updateExecutionPlanByRecord(row)
        elif fieldName == 'aliquoticity':
            if not actionType.isNomenclatureExpense:
                pass
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
            values              = self._mapActionTypeIdToPropertyValues[actionTypeId]
            propertyType        = values[fieldName]['propertyType']
            property            = action.getPropertyById(propertyType.id)
            property.preApplyDependents(action)
            if isinstance(propertyType.valueType, CNomenclatureActionPropertyValueType):
                (nomenclatureId, financeId) = value
#                oldNomenclatureId = forceRef(record.value('recipe'))
                record.setValue('recipe', toVariant(nomenclatureId))
                if nomenclatureId:
                    if financeId:
                        self.setData(self.index(row, self.getColIndex('finance_id')), toVariant(financeId))
                    nomenclatureValues = _getNomenclatureValues(nomenclatureId, self._nomenclatureCache)
                    #self.setData(dosesIndex, toVariant(dosageValue))
                    property = action.getPropertyById(propertyType.id)
                    if nomenclatureId:
                        if actionType.isNomenclatureExpense:
                            if oldNomenclatureId != nomenclatureId:
                                nomenclatureOldAnalogId = self.getNomenclatureAnalog(oldNomenclatureId) if oldNomenclatureId else None
                                nomenclatureAnalogId = self.getNomenclatureAnalog(nomenclatureId) if nomenclatureId else None
                                if nomenclatureOldAnalogId != nomenclatureAnalogId or not nomenclatureOldAnalogId or not nomenclatureAnalogId:
                                    dosageValue = nomenclatureValues.get('dosageValue')
                                    dosesColumnIndex = self.getColIndex('doses')
                                    dosesIndex = self.index(row, dosesColumnIndex)
                                    dosesPropertyType = values['doses']['propertyType']
                                    dosesProperty = action.getPropertyById(dosesPropertyType.id)
                                    dosesProperty.setValue(dosageValue)
                                    CRecordListModel.setData(self, dosesIndex, toVariant(dosageValue), role)
                                    action.updateNomenclatureDosageValue(nomenclatureId, forceDouble(dosageValue), force=True)
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
                                                CRecordListModel.setData(self, signaIndex, toVariant(usingTypes[0]), role)
                                    self.updateExecutionPlanByRecord(row)
                                elif nomenclatureOldAnalogId and nomenclatureOldAnalogId == nomenclatureAnalogId:
                                    if action.getExecutionPlan():
                                        for epItem in action.getExecutionPlan().items:
                                            if epItem.nomenclature:
                                                epItem.nomenclature.nomenclatureId = forceRef(nomenclatureId)
                                existQnt = getExistsNomenclatureAmount(nomenclatureId, financeId = financeId, medicalAidKindId = self.medicalAidKindId, orgStructureId=self.orgStructureId)
                                if existQnt <= 0:
                                    self.addExistQntRows(row)
                                else:
                                    self.removedExistQntRows(row)
            property.applyDependents(action)
        elif fieldName == 'doses':
            actionTypeId = forceRef(record.value('actionType_id'))
            action = self._idRowToAction[(actionTypeId, row)]
            values = self._mapActionTypeIdToPropertyValues[actionTypeId]
            propertyType = values['recipe']['propertyType']
            if isinstance(propertyType.valueType, CNomenclatureActionPropertyValueType):
                property = action.getPropertyById(propertyType.id)
                nomenclatureId = property.getValue()
                if nomenclatureId:
                    action.updateNomenclatureDosageValue(nomenclatureId, forceDouble(value), force=True)
                    if actionType.isNomenclatureExpense:
                        self.updateExecutionPlanByRecord(row)
        return result


class CActionTypeGroupsNETemplatesModel(CActionTypeGroupsTemplatesModel):
    def __init__(self, parent):
        CActionTypeGroupsTemplatesModel.__init__(self, parent)
        self.actionTypeId = None


    def setActionTypeId(self, value):
        self.actionTypeId = value


    def reloadData(self, class_=None):
        db = QtGui.qApp.db
        self._class = class_
        tablePerson = db.table('Person')
        queryTable = self._table.leftJoin(tablePerson, tablePerson['id'].eq(self._table['createPerson_id']))
        cond = [self._table['deleted'].eq(0),
                self._table['type'].eq(self._type),
                db.joinOr([self._table['availability'].eq(0),
                           db.joinAnd([self._table['availability'].eq(1), self._table['id'].isNotNull(),
                                       tablePerson['speciality_id'].eq(QtGui.qApp.userSpecialityId)]),
                           db.joinAnd([self._table['availability'].eq(2), tablePerson['id'].eq(QtGui.qApp.userId)]),
                          ])
                ]
        if class_ is None:
            if self.last_class is not None:
                cond.append(self._table['class'].eq(self.last_class))
        else:
            self.last_class = class_
            cond.append(self._table['class'].eq(class_))
        if self.filter:
            cond.append(self.filter)
        if self.findFilterText:
            cond.append(db.joinOr([self._table['code'].like(addDotsEx(self.findFilterText)), self._table['name'].like(addDotsEx(self.findFilterText))]))
        if self.actionTypeId:
            tableActionTypeGroupItem = db.table('ActionTypeGroup_Item')
            cond.append(tableActionTypeGroupItem['deleted'].eq(0))
            cond.append(tableActionTypeGroupItem['actionType_id'].eq(self.actionTypeId))
            queryTable = queryTable.innerJoin(tableActionTypeGroupItem, tableActionTypeGroupItem['master_id'].eq(self._table['id']))
        idList = db.getDistinctIdList(queryTable, 'ActionTypeGroup.id', cond, order=self.templates_order)
        self.setIdList(idList)
