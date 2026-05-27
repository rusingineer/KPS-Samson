# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2025 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

# Множественный выбор добавляемых типов действий

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QDate, QEvent, QVariant, pyqtSignature, SIGNAL
from PyQt4.QtSql import QSqlField

from library.DialogBase         import CDialogBase
from library.ItemsListDialog import CItemEditorBaseDialog
from library.MES.Utils          import getServiceIdList, getMesServiceInfo, getServiceIdForAgeList
from library.TableModel         import CTableModel, CBoolCol, CCol, CDateCol, CEnumCol, CRefBookCol, CTextCol
from library.Utils              import (
    addDotsEx, forceBool, forceDate, forceDouble, forceInt, forceRef, forceString, forceStringEx, formatNum, toVariant, smartDict, trim, withWaitCursor, setPref, getPrefBool
)
from library.interchange import setComboBoxValue, getComboBoxValue

from library.database import CTable
from Accounting.Tariff          import CTariff
from Events.Action              import CActionTypeCache
from Events.ActionsSelectorSelectedTable import CCheckedActionsModel
from Events.ActionStatus        import CActionStatus
from Events.ActionTypeComboBox  import CActionTypeModel, getActionTypeIdListWithLimitationByContractTariffAttachByDate
from Events.Utils               import (
    CEventTypeDescription, getEventContractCondition, getEventIncludeTooth, getEventCSGRequired, getEventMESCondition, getEventNomenclatureCondition,
    getEventOrgStructureCondition, getEventPlannerCondition, getEventRequiredCondition, getEventOnlyNotExistsCondition
)
from Orgs.Utils                 import getOrgStructureActionTypeIdSet

from RefBooks.ActionTypeGroup.List import CActionTypeGroupsModel, ACTION_TYPE_GROUP_APPOINTMENT
from RefBooks.ActionTypeGroup.RBActionTypeGroupEditor import ActionTypeGroupEditor

from Users.Rights import urAdmin, urCanCreateNewActionTypeGroup, urEditContractConditionF9, urCanDeleteForeignActionTypeGroup

from Events.Ui_ActionsSelectorDialog import Ui_ActionTypesSelectorDialog
from Events.Ui_SelectorTemplateEditor import Ui_SelectorTemplateEditor


_TREE_TAB_INDEX = 0
_TEMPLATES_TAB_INDEX = 1

_RECIPE =1
_DOSES  = 2
_SIGNA  = 3
_ACTIVESUBSTANCE = 4


def getActionTypeIdListByMesId(mesId, isNecessary=False, clientMesInfo=None, eventDate=None):
    if clientMesInfo:
        serviceIdList = getServiceIdForAgeList(mesId, isNecessary, clientMesInfo, eventDate)
    else:
        serviceIdList = getServiceIdList(mesId, isNecessary, clientMesInfo, eventDate)
    db = QtGui.qApp.db
    tableActionType = db.table('ActionType')
    cond = [tableActionType['deleted'].eq(0),
            tableActionType['showInForm'].ne(0),
            tableActionType['nomenclativeService_id'].inlist(serviceIdList)
           ]
    result = db.getDistinctIdList(tableActionType, tableActionType['id'].name(), cond)
    return result


def selectActionTypes(parent, eventEditor, actionTypeClasses=[], orgStructureId=None, eventTypeId=None, contractId=None, mesId=None, chkContractByFinanceId=None, eventId=None, existsActionTypesList=[], visibleTblSelected=True, contractTariffCache=None, clientMesInfo=None, eventDate=None, preActionTypeIdList=[]):
    QtGui.qApp.setOverrideCursor(QtGui.QCursor(Qt.WaitCursor))
    dlg = CActionTypesSelectionDialog(parent, eventEditor, eventTypeId)    
    try:      
        dlg.setBlockSignals(True)
        try:
            dlg.setExistsActionTypes(existsActionTypesList)
            dlg.setOrgStructurePriority(eventTypeId)
            if hasattr(eventEditor, 'cmbPerson'):
                dlg.setExecPerson(eventEditor.cmbPerson.value())
            dlg.setMesId(mesId, clientMesInfo)
            dlg.setActionTypeClasses(actionTypeClasses)
            dlg.setSexAndAge(eventEditor.clientSex, eventEditor.clientAge, eventEditor.clientBirthDate)
            dlg.setEventId(eventId)
            dlg.setEventDate(eventDate or eventEditor.eventDate)
            dlg.setSpecialityId()
            dlg.setEventTypeId(eventTypeId)
            dlg.setCSGEnabled(eventEditor)
            dlg.setOrgStructureId(orgStructureId)
            dlg.setContractId(contractId, chkContractByFinanceId)
            dlg.updateSelectedCount()
            dlg.getDepositClient()
            dlg.setVisibleTblSelected(visibleTblSelected)
            dlg.setPreActionTypeIdList(preActionTypeIdList)
            dlg.setContractTariffCache(contractTariffCache)
            dlg.setClientId()
            dlg.updateContractTariffLimitationsChecked()
            dlg.updateConditionsByEventTypeDefaults()
        finally:
            dlg.loadChkBoxPreferences()
            dlg.updateTreeData()
            dlg.setBlockSignals(False)

        QtGui.qApp.restoreOverrideCursor()
        if dlg.exec_():
            result = dlg.getSelectedList()
        else:
            result = []
    finally:
        dlg.saveChkBoxPreferences()
        dlg.deleteLater()
    return result


def selectActionTypesEx(parent, eventEditor, actionTypeClasses=[], orgStructureId=None, eventTypeId=None, contractId=None, mesId=None, chkContractByFinanceId=None, eventId=None, existsActionTypesList=[], visibleTblSelected=True, contractTariffCache=None, clientMesInfo=None, eventDate=None, preActionTypeIdList=[]):
    QtGui.qApp.setOverrideCursor(QtGui.QCursor(Qt.WaitCursor))
    dlg = CActionTypesSelectionDialog(parent, eventEditor, eventTypeId)
    result = []
    try:
        dlg.setBlockSignals(True)
        try:
            dlg.setExistsActionTypes(existsActionTypesList)
            dlg.setOrgStructurePriority(eventTypeId)
            if hasattr(eventEditor, 'cmbPerson'):
                dlg.setExecPerson(eventEditor.cmbPerson.value())
            dlg.setMesId(mesId, clientMesInfo)
            dlg.setActionTypeClasses(actionTypeClasses)
            dlg.setSexAndAge(eventEditor.clientSex, eventEditor.clientAge, eventEditor.clientBirthDate)
            dlg.setEventId(eventId)
            dlg.setEventDate(eventDate or eventEditor.eventDate)
            dlg.setSpecialityId()
            dlg.setEventTypeId(eventTypeId)
            dlg.setCSGEnabled(eventEditor)
            dlg.setOrgStructureId(orgStructureId)
            dlg.setContractId(contractId, chkContractByFinanceId)
            dlg.updateSelectedCount()
            dlg.getDepositClient()
            dlg.setVisibleTblSelected(visibleTblSelected)
            dlg.setPreActionTypeIdList(preActionTypeIdList)
            dlg.setContractTariffCache(contractTariffCache)
            dlg.setClientId()
            dlg.updateContractTariffLimitationsChecked()
            dlg.updateConditionsByEventTypeDefaults()
        finally:
            dlg.chkOnlyNotExists.setChecked(False)
            dlg.chkPreferable.setChecked(False)
            dlg.chkContract.setChecked(True)
            dlg.chkSexAndAge.setChecked(True)
            dlg.chkPriceList.setChecked(False)
            dlg.chkNomenclative.setChecked(True)
            dlg.chkMes.setChecked(True)
            dlg.tblActionTypes.model().setCheckMesGroups(True)
            dlg.chkIsNecessary.setChecked(False)
            dlg.chkContractTariffLimitations.setChecked(False)
            dlg.chkOrgStructure.setChecked(False)
            dlg.chkPlanner.setChecked(False)
            dlg.isOrgStructirePriority = False
            dlg.cmbSpeciality.setEnabled(False)
            dlg.cmbOrgStructure.setEnabled(False)
            dlg.updateTreeData()
            dlg.setBlockSignals(False)
            dlg.on_bntSelectAll_pressed()
        QtGui.qApp.restoreOverrideCursor()
        if dlg.exec_():
            result = dlg.getSelectedList()
        else:
            result = []
        QtGui.qApp.restoreOverrideCursor()
    finally:
        dlg.deleteLater()
    return result


class CActionTypesSelectionManager(object):

    def updateSelectedCount(self):
        n = len(self.selectedActionTypeIdList)
        if n == 0:
            msg = u'ничего не выбрано'
        else:
            msg = u'выбрано '+formatNum(n, [u'действие', u'действия', u'действий'])
        self.lblSelectedCount.setText(msg)


    def getSelectedList(self):
        return self.getSelectedActionTypeIdList()


    def getSelectedActionTypeIdList(self):
        return self.selectedActionTypeIdList


    def setSelected(self, actionTypeId, value):
        present = self.isSelected(actionTypeId)
        if value:
            if not present:
                self.selectedActionTypeIdList.append(actionTypeId)
                self.updateSelectedCount()
                return True
        else:
            if present:
                self.selectedActionTypeIdList.remove(actionTypeId)
                self.updateSelectedCount()
                return True
        return False


    def isSelected(self, actionTypeId):
        return actionTypeId in self.selectedActionTypeIdList


    def findByCode(self, value):
        uCode = unicode(value).upper()
        codes = self.actionsCacheByCode.keys()
        codes.sort()
        for c in codes:
            if unicode(c).startswith(uCode):
                return self.actionsCacheByCode[c]
        return self.findByName(value)

    def findByName(self, name):
        uName = unicode(name).upper()
        names = self.actionsCodeCacheByName.keys()
        for n in names:
            if uName in n:
                code = self.actionsCodeCacheByName[n]
                return self.actionsCacheByCode.get(code, None)
        return None


class CActionTypesSelectionDialog(CDialogBase, CActionTypesSelectionManager, Ui_ActionTypesSelectorDialog):
    cachePlannedActionTypesBySpeciality   = {}
    cachePlannedActionTypesByOrgStructure = {}

    def __init__(self, parent, eventEditor, eventTypeId=None):
        CDialogBase.__init__(self, parent)

        self._visibleTblSelected = True

        self.parentWidget = parent
        self.eventEditor  = eventEditor

        self.addModels('ActionTypes', CActionsModel(self))
        self.addModels('ExistsClientActions', CExistsClientActionsModel(self))
        self.addModels('SelectedActionTypes', CCheckedActionsModel(self,
                                                                   self.modelExistsClientActions,
                                                                   self.modelActionTypes,
                                                                   getEventIncludeTooth(eventTypeId)))
        self.addModels('Templates', CActionTypeGroupsTemplatesModel(self))

        self.addModels('ActionTypeGroups', CActionTypeModel(self))
        self.exitsProxyModel = CExistsProxyModel(self)
        self.exitsProxyModel.setModel(self.modelExistsClientActions)
#        self.setClientId()

        self.addObject('bntSelectAll', QtGui.QPushButton(u'Выбрать всё', self))
        self.addObject('bntClearSelection', QtGui.QPushButton(u'Очистить выбор', self))
        self.addObject('btnSaveTemplate', QtGui.QPushButton(u'Сохранить шаблон', self))
        self.modelActionTypeGroups.setAllSelectable(True)
        self.setupUi(self)
        self.modelActionTypeGroups.setRootItemVisible(True)
        self.modelActionTypeGroups.setLeavesVisible(False)
        self.setModels(self.treeActionTypeGroups, self.modelActionTypeGroups, self.selectionModelActionTypeGroups)
        self.setModels(self.tblActionTypes, self.modelActionTypes, self.selectionModelActionTypes)
        self.setModels(self.tblSelectedActionTypes, self.modelSelectedActionTypes, self.selectionModelSelectedActionTypes)
        self.setModels(self.tblExistsClientActions, self.exitsProxyModel)
        self.setModels(self.tblTemplates, self.modelTemplates, self.selectionModelTemplates)

        self.tblTemplates.addPopupDelRow()

        self.buttonBox.addButton(self.bntSelectAll, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.bntClearSelection, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnSaveTemplate, QtGui.QDialogButtonBox.ActionRole)

        self.selectedActionTypeIdList = []
        self.clientSex = None
        self.clientAge = None
        self.eventDate = None
        self.clientBirthDate = None
        self.orgStructureId = None
        self.eventId = None
        self.eventTypeId = None
        self.contractId = None
        self.contractSum = 0
        self.specialityId = None
        self.specialityRegionalCode = None
        self.mesId = None
        self.clientMesInfo = None
        self.nomenclativeActionTypes = None
        self.preferableActionTypes = None
        self.actionTypeWithoutService = None
        self.orgStructureActionTypes = None
        self.preActionTypeIdList = []
        self.plannedActionTypes = None
        self.mapContractId2ActionTypes = {}
        self.enabledActionTypes = None
        self.execPerson = None
        self.findFilterText = None
        self.actionsCacheByCode = {}
        self.actionsCodeCacheByName = {}
        self.actionTypeIdListBySex = None
        self.actionTypeIdListByFindFilter = None
        self.actionTypeIdListByCSGCode = None
        self.CSGId = None
        self.mesActionTypeIdList = []
        self.actionTypeClasses = []
        self._clientAttachTypeId = None
        self.edtFindByCode.installEventFilter(self)
        self.mesActionTypes = None
        self.disabledActionTypeIdList = None
        self.cmbSpeciality.setTable('rbSpeciality')
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinMaxButtonsHint)
        self.isOrgStructirePriority = None
        self.existsActionTypesList = []
        self.sumDeposit = 0.0
        self._contractTariffCache = None
        self.indexCmbCSGOLD = -1
        self._tmpValueIsCheckedContract = False
        self.tblSelectedActionTypes.addGetExecutionPlan()
        self.tblSelectedActionTypes.addInsertSameAction()
        self.tblSelectedActionTypes.addSelectAllUrgentAction()
        self.tblSelectedActionTypes.addClearSelectionUrgentAction()
        self.tblSelectedActionTypes.enableColsHide()
        self.tblSelectedActionTypes.enableColsMove()
        self._payableFinanceId = forceRef(QtGui.qApp.db.translate('rbFinance', 'code', '4', 'id'))

        self._sortActionType = smartDict(order='code, name', isAscending=False, column=0)
        self._sortTemplates = smartDict(order='ActionTypeGroup.code, ActionTypeGroup.name', isAscending=False, column=0)

        self.connect(self.modelSelectedActionTypes, SIGNAL('pricesAndSumsUpdated()'), self.on_pricesAndSumsUpdated)

        self.connect(self.tblActionTypes.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.on_sortActions)

        self.connect(self.tblTemplates.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.on_sortTemplates)
        self.setFocusToWidget(self.edtFindByCode)
        self.splSelectedActionTypes.setCollapsible(0, False)
        
        self.treeActionTypeGroups.header().setVisible(False)
        self.btnSaveTemplate.setEnabled(QtGui.qApp.userHasRight(urAdmin) or QtGui.qApp.userHasRight(urCanCreateNewActionTypeGroup))

    def setPreActionTypeIdList(self, preActionTypeIdList):
        self.preActionTypeIdList = preActionTypeIdList


    def loadChkBoxPreferences(self):
        chkBoxPreferences = QtGui.qApp.preferences.appPrefs
        self.chkOnlyNotExists.setChecked(getPrefBool(chkBoxPreferences, 'ASchkOnlyNotExists', True))
        self.chkPreferable.setChecked(getPrefBool(chkBoxPreferences, 'ASchkPreferable', True))
        self.chkContract.setChecked(getPrefBool(chkBoxPreferences, 'ASchkContract', False))
        self.chkSexAndAge.setChecked(getPrefBool(chkBoxPreferences, 'ASchkSexAndAge', True))
        self.chkPriceList.setChecked(getPrefBool(chkBoxPreferences, 'ASchkPriceList', False))
        self.chkNomenclative.setChecked(getPrefBool(chkBoxPreferences, 'ASchkNomenclative', False))
        self.chkMes.setChecked(getPrefBool(chkBoxPreferences, 'ASchkMes', False))
        self.tblActionTypes.model().setCheckMesGroups(self.chkMes.isChecked())
        self.chkIsNecessary.setChecked(getPrefBool(chkBoxPreferences, 'ASchkIsNecessary', False))
        self.chkContractTariffLimitations.setChecked(getPrefBool(chkBoxPreferences, 'ASchkContractTariffLimitations', False))
        self.chkOrgStructure.setChecked(getPrefBool(chkBoxPreferences, 'ASchkOrgStructure', False))
        self.chkPlanner.setChecked(getPrefBool(chkBoxPreferences, 'ASchkPlanner', False))
        self.isOrgStructirePriority = not self.chkPlanner.isChecked()
        self.cmbSpeciality.setEnabled(self.chkPlanner.isChecked())
        self.cmbOrgStructure.setEnabled(self.chkOrgStructure.isChecked())
        
        
    def saveChkBoxPreferences(self):
        chkBoxPreferences = QtGui.qApp.preferences.appPrefs
        setPref(chkBoxPreferences, 'ASchkOnlyNotExists', QVariant(self.chkOnlyNotExists.isChecked()))
        setPref(chkBoxPreferences, 'ASchkPreferable', QVariant(self.chkPreferable.isChecked()))
        setPref(chkBoxPreferences, 'ASchkContract', QVariant(self.chkContract.isChecked()))
        setPref(chkBoxPreferences, 'ASchkSexAndAge', QVariant(self.chkSexAndAge.isChecked()))
        setPref(chkBoxPreferences, 'ASchkPriceList', QVariant(self.chkPriceList.isChecked()))
        setPref(chkBoxPreferences, 'ASchkNomenclative', QVariant(self.chkNomenclative.isChecked()))
        setPref(chkBoxPreferences, 'ASchkMes', QVariant(self.chkMes.isChecked()))
        setPref(chkBoxPreferences, 'ASchkIsNecessary', QVariant(self.chkIsNecessary.isChecked()))
        setPref(chkBoxPreferences, 'ASchkContractTariffLimitations', QVariant(self.chkContractTariffLimitations.isChecked()))
        setPref(chkBoxPreferences, 'ASchkOrgStructure', QVariant(self.chkOrgStructure.isChecked()))
        setPref(chkBoxPreferences, 'ASchkPlanner', QVariant(self.chkPlanner.isChecked()))


    def setCSGEnabled(self, eventEditor):
        if self.eventTypeId:
            value = getEventCSGRequired(self.eventTypeId)
            self.chkCSG.setEnabled(value)
            self.cmbCSG.setEnabled(value and self.chkCSG.isChecked())
            self.cmbCSG.setEventEditor(eventEditor)
            self.cmbCSG.setItems()
        else:
            self.chkCSG.setEnabled(False)
            self.cmbCSG.setEnabled(False)


    def getSumDepositForContract(self):
        clientId = self.getClientId()
        eventId = self.getEventId()
        sumAction = 0.0
        sumItem = 0.0
        contractIdList = {}
        if self.eventEditor and clientId and self.contractId:
            contractIdList = {}
            if hasattr(self.eventEditor, 'cmbContract'):
                if hasattr(self.eventEditor, 'tabCash'):
                    for row, record in enumerate(self.eventEditor.tabCash.modelAccActions._items):
                        accContractId = forceRef(record.value('contract_id'))
                        if accContractId:
                            actionTypeId = forceRef(record.value('actionType_id'))
                            if actionTypeId and actionTypeId not in self.eventEditor.actionTypeDepositIdList:
                                self.eventEditor.actionTypeDepositIdList.append(actionTypeId)
                            sum = forceDouble(self.eventEditor.tabCash.modelAccActions.items()[row].value('sum'))
                            contractSumList = contractIdList.get(accContractId, 0.0)
                            contractSumList += sum
                            contractIdList[accContractId] = contractSumList
                sumAction += contractIdList.get(self.contractId, 0.0)
                db = QtGui.qApp.db
                tableAction = db.table('Action')
                tableEvent = db.table('Event')
                tableAccountItem = db.table('Account_Item')
                tableActionType = db.table('ActionType')
            #  payStatus != 0
                cond = [tableAction['deleted'].eq(0),
                        tableEvent['deleted'].eq(0),
                        tableAccountItem['deleted'].eq(0),
                        tableAction['contract_id'].eq(self.contractId),
                        tableAction['payStatus'].ne(0),
                        tableAccountItem['refuseType_id'].isNull()
                        ]
                if eventId:
                    cond.append(tableEvent['id'].ne(eventId))
                table = tableEvent.innerJoin(tableAction, tableEvent['id'].eq(tableAction['event_id']))
                table = table.innerJoin(tableAccountItem, tableAction['id'].eq(tableAccountItem['action_id']))
                if clientId:
                    cond.append(tableEvent['client_id'].eq(clientId))
                records = db.getRecordListGroupBy(table, u'SUM(Account_Item.sum) AS sumAction', cond, u'Action.contract_id')
                if records:
                    newRecord = records[0]
                    sumAction += forceDouble(newRecord.value('sumAction'))
            #  payStatus == 0
                tableActionTypeService = db.table('ActionType_Service')
                tableRBService = db.table('rbService')
                tableContractTariff = db.table('Contract_Tariff')
                cols = u'''SUM(IF(Action.amount > Contract_Tariff.amount AND Contract_Tariff.amount != 0, Contract_Tariff.amount * Contract_Tariff.price,
                Action.amount * Contract_Tariff.price)) AS sumItem, Action.contract_id'''
                cond = [tableAction['deleted'].eq(0),
                        tableEvent['deleted'].eq(0),
                        tableActionType['deleted'].eq(0),
                        tableContractTariff['deleted'].eq(0),
                        tableAction['contract_id'].eq(self.contractId),
                        tableContractTariff['master_id'].eq(self.contractId),
                        tableAction['payStatus'].eq(0),
                        tableContractTariff['tariffType'].eq(CTariff.ttActionAmount),
                        tableActionType['id'].eq(tableActionTypeService['master_id'])
                        ]
                if eventId:
                    cond.append(tableEvent['id'].ne(eventId))
                if self.clientAge:
                    cond.append(db.joinOr([tableContractTariff['age'].eq(''), tableContractTariff['age'].ge(self.clientAge[3])]))
                if clientId:
                    cond.append(tableEvent['client_id'].eq(clientId))
                cond.append(db.joinOr([tableContractTariff['sex'].eq(0), tableContractTariff['sex'].eq(self.clientSex)]))
                table = tableEvent.innerJoin(tableAction, tableEvent['id'].eq(tableAction['event_id']))
                table = table.innerJoin(tableActionType, tableAction['actionType_id'].eq(tableActionType['id']))
                table = table.innerJoin(tableActionTypeService, tableAction['finance_id'].eq(tableActionTypeService['finance_id']))
                table = table.innerJoin(tableRBService, tableActionTypeService['service_id'].eq(tableRBService['id']))
                table = table.innerJoin(tableContractTariff, tableRBService['id'].eq(tableContractTariff['service_id']))
                records = db.getRecordListGroupBy(table, cols, cond, u'Action.contract_id')
                for newRecord in records:
                    sumItem = forceDouble(newRecord.value('sumItem'))
        return sumAction + sumItem


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


    def getDepositClient(self):
        clientId = self.getClientId()
        if self.contractId and clientId:
            db = QtGui.qApp.db
            table = db.table('ClientDeposit')
            record = db.getRecordEx(table, table['contractSum'],
                                    [table['deleted'].eq(0), table['client_id'].eq(clientId), table['contract_id'].eq(self.contractId)])
            if record:
                self.contractSum = forceDouble(record.value('contractSum'))
        self.on_pricesAndSumsUpdated()


    def setClientId(self):
        clientId = self.getClientId()
        if self._visibleTblSelected:
            self.modelSelectedActionTypes.setClientId(clientId)
            self.modelExistsClientActions.setCurrentEventItems(self.getCurrentEventItems())
            self.modelExistsClientActions.setClientId(clientId)

        db = QtGui.qApp.db

        currentDate = QDate.currentDate()
        currentDateString = db.formatValueEx(QVariant.Date, currentDate)


        tableClientAttach = db.table('ClientAttach')
        tableCA = db.table('ClientAttach').alias('CA')

        cond2 = [tableCA['client_id'].eq(clientId),
                 tableClientAttach['deleted'].eq(0),
                 tableCA['begDate'].dateLe(currentDateString),
                 db.joinOr([tableCA['endDate'].dateGe(currentDateString), tableCA['endDate'].isNull()])]
        stmt2 = db.selectStmt(tableCA, 'MAX(CA.id)', cond2)

        cond1 = [tableClientAttach['client_id'].eq(clientId),
                 tableClientAttach['id'].eq(stmt2)]

        result = db.getRecordEx(tableClientAttach, tableClientAttach['attachType_id'], cond1)
        if result:
            result = forceRef(result.value('attachType_id'))

#        stmt = 'SELECT ClientAttach.attachType_id FROM ClientAttach WHERE ClientAttach.client_id = %d AND ClientAttach.id = (SELECT MAX(CA.id) FROM ClientAttach AS CA WHERE CA.client_id = %d AND ClientAttach.deleted = 0 AND CA.begDate <= %s AND (CA.endDate >= %s OR CA.endDate IS NULL))' %(clientId, clientId, currentDateString, currentDateString)
#        result = db.query(stmt)
#        result.first()
#
#        self._clientAttachTypeId = forceRef(result.value(0))

        self._clientAttachTypeId = result

    def clientAttachTypeId(self):
        return self._clientAttachTypeId


    def getCurrentEventItems(self):
        return self.eventEditor.getActionsModelsItemsList()


    def setContractTariffCache(self, contractTariffCache):
        self._contractTariffCache = contractTariffCache


    def getPrice(self, actionTypeId, contractId, financeId):
        if self._contractTariffCache:
            tariffDescr = self._contractTariffCache.getTariffDescr(contractId, self)
            tariffMap = tariffDescr.actionTariffMap
            serviceIdList = self.getActionTypeServiceIdList(actionTypeId, financeId)
            price = self._contractTariffCache.getPrice(tariffMap, serviceIdList, self.getTariffCategoryId())
            return price
        return None


    def getClientId(self):
        return self.eventEditor.clientId


    def getFinanceId(self):
        return self.eventEditor.eventFinanceId


    def getMedicalAidKindId(self):
        return self.eventEditor.eventMedicalAidKindId


    def getEventId(self):
        return self.eventId


    def getTariffCategoryId(self):
        return self.eventEditor.personTariffCategoryId


    def getActionTypeServiceIdList(self, actionTypeId, financeId):
        return self.eventEditor.getActionTypeServiceIdList(actionTypeId, financeId)


    def recordAcceptable(self, record):
        return self.eventEditor.recordAcceptable(record)


    def setVisibleTblSelected(self, value):
        self._visibleTblSelected = value
        self.pnlSelectedActionTypes.setVisible(value)
        if not value:
            self.setObjectName('ActionTypesSelectorDialogWithoutSelected')


    def getSelectedList(self):
        if self._visibleTblSelected:
            return self.getSelectedActionList()
        else:
            return CActionTypesSelectionManager.getSelectedActionTypeIdList(self)

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
        csgRecord = None
        if self.chkCSG.isChecked():
            indexCSG = self.cmbCSG.currentIndex()
            if indexCSG > 0:
                csgRecord = self.cmbCSG.mapIndexToCSGRecord.get(indexCSG, None)
        for actionTypeId in self.selectedActionTypeIdList:
            actions = self.modelSelectedActionTypes.getSelectedAction(actionTypeId)
            for action in actions:
                self.updatePresetValuesConditions(action)
                action.initPresetValues()
                if self.chkCSG.isChecked():
                    record = action.getRecord()
                    eventCSGId = forceRef(csgRecord.value('id')) if csgRecord else None
                    record.setValue('eventCSG_id', toVariant(eventCSGId))

                actionType = action.getType()
                if actionType.isNomenclatureExpense:
                    medicalAidKindId = action.getMedicalAidKindId()
                    action.initNomenclatureReservation(self.getClientId(), financeId=action.getFinanceId(), medicalAidKindId=medicalAidKindId)
                if not action.deleteMark:
                    item = (actionTypeId, action, csgRecord)
                    result.append(item)
        return result


    def eventEditorOwner(self):
        if len(self.actionTypeClasses) > 1:
            return self
        else:
            return self.parentWidget


    def setSelected(self, actionTypeId, value, resetMainModel=False):
        if self._visibleTblSelected:
            present = self.isSelected(actionTypeId)
            if value:
                if not present:
                    self.selectedActionTypeIdList.append(actionTypeId)
#                    self.modelSelectedActionTypes.add(actionTypeId)
                    if self.tabWgtActionTypes.currentIndex() == _TEMPLATES_TAB_INDEX:
                        records = self.getActionTypeItemsByTemplate(actionTypeId)
                        for record in records:
                            recipe = forceRef(record.value('nomenclature_id'))
                            doses = forceString(record.value('doses'))
                            signa = forceString(record.value('signa'))
                            activeSubstanceId = forceRef(record.value('activeSubstance_id'))
                            self.insertActionIntoCheckedModel(actionTypeId, recipe, doses, signa, activeSubstanceId)
                    else:
                        self.insertActionIntoCheckedModel(actionTypeId)
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
        else:
            return CActionTypesSelectionManager.setSelected(self, actionTypeId, value)


    def insertActionIntoCheckedModel(self, actionTypeId, recipe=None, doses=None, signa=None, activeSubstanceId=None):
        templateId = self.tblTemplates.currentItemId()
        actionTemplate_id = None
        if templateId:
            db = QtGui.qApp.db
            table = db.table('ActionTypeGroup_Item')
            items = db.getDistinctIdList(
                table, 'actionTemplate_id', where=[table['deleted'].eq(0), table['master_id'].eq(templateId), table['actionType_id'].eq(actionTypeId)]
            )
            actionTemplate_id = items[0] if items else None

        if self.chkPriceList.isChecked() and self.cmbPriceListContract.value():
            self.modelSelectedActionTypes.add(actionTypeId,
                                              self.getMESqwt(actionTypeId),
                                              self._payableFinanceId,
                                              self.cmbPriceListContract.value(), recipe, doses, signa, activeSubstanceId, actionTemplate_id)
        else:
            self.modelSelectedActionTypes.add(actionTypeId, self.getMESqwt(actionTypeId), recipe=recipe, doses=doses, signa=signa, activeSubstanceId=activeSubstanceId, actionTemplate_id=actionTemplate_id)


    def emitModelActionTypesDataChanged(self):
        self.modelActionTypes.emitDataChanged()


    def exec_(self):
        self.updateTreeData()
        return CDialogBase.exec_(self)


    def setBlockSignals(self, val):
        widgets = [self.chkOnlyNotExists,
                   self.chkContract,
                   self.chkPreferable,
                   self.chkSexAndAge,
                   self.chkOrgStructure,
                   self.cmbOrgStructure,
                   self.chkNomenclative,
                   self.chkMes,
                   self.chkIsNecessary,
                   self.chkPlanner,
                   self.cmbSpeciality,
                   self.chkPriceList,
                   self.cmbPriceListContract,
                   self.chkContractTariffLimitations]
        for w in widgets:
            w.blockSignals(val)


    @classmethod
    def getCachedPlannedActionTypesBySpeciality(cls, specialityId, eventTypeId):
        key = (specialityId, eventTypeId)
        return cls.cachePlannedActionTypesBySpeciality.get(key, None)


    @classmethod
    def setCachedPlannedActionTypesBySpeciality(cls, specialityId, eventTypeId, setIdList):
        key = (specialityId, eventTypeId)
        cls.cachePlannedActionTypesBySpeciality[key] = setIdList


    @classmethod
    def getCachedActionTypesByOrgStructure(cls, orgStructureId):
        return cls.cachePlannedActionTypesByOrgStructure.get(orgStructureId, None)


    @classmethod
    def setCachedActionTypesByOrgStructure(cls, orgStructureId, setIdList):
        cls.cachePlannedActionTypesByOrgStructure[orgStructureId] = setIdList


    def setExistsActionTypes(self, existsActionTypesList):
        self.existsActionTypesList = existsActionTypesList


    def setOrgStructurePriority(self, eventTypeId):
        self.isOrgStructirePriority = forceBool(QtGui.qApp.preferences.appPrefs.get('orgStructurePriorityForAddActions', QVariant()))
        if not self.isOrgStructirePriority and eventTypeId:
            self.isOrgStructirePriority = CEventTypeDescription.get(eventTypeId).isOrgStructurePriority
            pass

    def setExecPerson(self, execPerson):
        self.execPerson = execPerson
    


    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            key = event.key()
            if obj == self.edtFindByCode:
                if key == Qt.Key_Space:
                    index = self.tblActionTypes.currentIndex()
                    currentValue = forceInt(self.modelActionTypes.data(
                                            self.modelActionTypes.createIndex(index.row(), 0),
                                            Qt.CheckStateRole))
                    value = 2 if currentValue == 0 else 0
                    if self.modelActionTypes.setData(index, value, Qt.CheckStateRole):
                        self.edtFindByCode.selectAll()
                    self.tblActionTypes.model().emitDataChanged()
                    return True
                elif key in (Qt.Key_Up, Qt.Key_Down):
                    self.tblActionTypes.keyPressEvent(event)
                    return True
        return False
#
#    def keyPressEvent(self, event):
#        if event.type() == QEvent.KeyPress:
#            key = event.key()
#            if key in (Qt.Key_Up, Qt.Key_Down):
#                self.tblActionTypes.keyPressEvent(event)
#            self.edtFindByCode.setFocus()
#            self.edtFindByCode.keyPressEvent(event)
#        CDialogBase.keyPressEvent(self, event)



    def setCmbOrgStructure(self, orgStructureId):
        orgId = QtGui.qApp.currentOrgId()
        if orgId:
            self.cmbOrgStructure.setOrgId(orgId)
            if orgStructureId:
                self.cmbOrgStructure.setValue(orgStructureId)
        else:
            self.cmbOrgStructure.setEnabled(False)


    def setActionTypeClasses(self, actionTypeClasses):
        if None in actionTypeClasses:
            actionTypeClasses = [0, 1, 2, 3]
        self.actionTypeClasses = actionTypeClasses
        self.modelActionTypeGroups.setClasses(actionTypeClasses)
        self.modelActionTypeGroups.setClassesVisible(len(actionTypeClasses)>1)


    def setSexAndAge(self, clientSex, clientAge, clientBirthDate):
        self.clientSex = clientSex
        self.clientAge = clientAge
        self.chkSexAndAge.setEnabled(bool(self.clientSex and self.clientAge))
        self.clientBirthDate = clientBirthDate


    def setFindFilterText(self, findFilterText):
        self.findFilterText = findFilterText


    def setEventDate(self, eventDate):
        self.eventDate = eventDate


    def getActionTypeIdListByClientSexAndAge(self):
        if self.actionTypeIdListBySex is None:
            self.actionTypeIdListBySex = set([])
            if self.clientSex:
                db = QtGui.qApp.db
                tableActionType =db.table('ActionType')
                cond = [tableActionType['deleted'].eq(0),
                        tableActionType['showInForm'].ne(0),
                        '''(SELECT isSexAndAgeSuitable(%s, %s, ActionType.sex, ActionType.age, %s))'''%(self.clientSex, db.formatDate(self.clientBirthDate), db.formatDate(self.eventDate))
                       ]
                self.actionTypeIdListBySex = set(db.getIdList(tableActionType, 'id', cond))
        return self.actionTypeIdListBySex


    def getActionTypeIdListByFindFilter(self):
        self.actionTypeIdListByFindFilter = set([])
        if self.findFilterText:
            db = QtGui.qApp.db
            tableActionType =db.table('ActionType')
            cond = [tableActionType['deleted'].eq(0),
                    tableActionType['showInForm'].ne(0),
                    db.joinOr([tableActionType['code'].like(self.findFilterText), tableActionType['name'].like(self.findFilterText)])
                   ]
            self.actionTypeIdListByFindFilter = set(db.getIdList(tableActionType, 'id', cond))
        return self.actionTypeIdListByFindFilter


    def setOrgStructureId(self, orgStructureId):
        if not orgStructureId:
            execPersonId = self.execPerson
            if not execPersonId and self.eventId:
                record = QtGui.qApp.db.getRecord('Event', 'execPerson_id', self.eventId)
                if record:
                    execPersonId = forceRef(record.value('execPerson_id'))
            if execPersonId:
                orgStructureId = forceRef(QtGui.qApp.db.translate('Person',
                                                                          'id',
                                                                          execPersonId,
                                                                          'orgStructure_id'))
        self.orgStructureId = orgStructureId
        self.setCmbOrgStructure(orgStructureId)
        self.chkOrgStructure.setEnabled(bool(QtGui.qApp.currentOrgId()))
        if not self.mesId:
#            if not QtGui.qApp.db.getRecordEx('EventType_Action', '*',
#                                             'eventType_id=%d'%self.eventTypeId):
            b = ((bool(QtGui.qApp.currentOrgStructureId()) or bool(orgStructureId)) and not bool(self.chkPlanner.isChecked()))
            if b:
                self.chkOrgStructure.setChecked(bool(self.orgStructureId))
            self.cmbOrgStructure.setEnabled(True)

    def setEventId(self, eventId):
        self.eventId = eventId

    def getEventTypeId(self):
        return self.eventTypeId

    def setEventTypeId(self, eventTypeId):
        self.eventTypeId = eventTypeId
        b = bool(self.eventTypeId)
        self.chkPlanner.setEnabled(b)
        if not self.mesId and not QtGui.qApp.currentOrgStructureId() and not self.isOrgStructirePriority:
            b = bool(self.getPlannedActionTypes())
            self.chkPlanner.setChecked(b)
            self.cmbSpeciality.setEnabled(b)

        canHavePayableActions = forceBool(QtGui.qApp.db.translate('EventType', 'id', eventTypeId, 'canHavePayableActions'))
        self.chkPriceList.setEnabled(canHavePayableActions)
        requiredCondition = getEventRequiredCondition(eventTypeId)
        if self.mesId:
            if requiredCondition == 1:
                self.chkIsNecessary.setChecked(True)
            elif requiredCondition == 2:
                self.chkIsNecessary.setChecked(False)

    def checkDataEntered(self):
        result = True
        if QtGui.qApp.controlFillingFieldsNomenclatureExpense():
            model = self.tblSelectedActionTypes.model()
            items = model.items()
            for row, item in enumerate(items):
                isPropertyTypeRECIPE = False
                isPropertyTypeDOSES = False
                isPropertyTypeACTIVESUBSTANCE = False
                actionType = CActionTypeCache.getById(forceRef(item.value('actionType_id')))
                if actionType.isNomenclatureExpense and not actionType.getNomenclatureRecordList():
                    for propertyTypeName, propertyType in actionType._propertiesByName.items():
                        if propertyType.inActionsSelectionTable == _RECIPE:
                            isPropertyTypeRECIPE = True
                        if propertyType.inActionsSelectionTable == _DOSES:
                            isPropertyTypeDOSES = True
                        if propertyType.inActionsSelectionTable == _ACTIVESUBSTANCE:
                            isPropertyTypeACTIVESUBSTANCE = True
                    if isPropertyTypeRECIPE and isPropertyTypeACTIVESUBSTANCE:
                        recipe = forceRef(item.value('recipe'))
                        activeSubstanceId = forceRef(item.value('activeSubstance_id'))
                        result = result and (recipe or activeSubstanceId or self.checkValueMessage(
                            u'Должно быть заполнено поле "Recipe" или "Действующее вещество"!', False,
                            self.tblSelectedActionTypes, row, model.getColIndex('recipe')))
                    elif isPropertyTypeRECIPE and not isPropertyTypeACTIVESUBSTANCE:
                        recipe = forceDouble(item.value('recipe'))
                        result = result and (
                                    recipe or self.checkInputMessage(u'Recipe', False, self.tblSelectedActionTypes, row,
                                                                     model.getColIndex('recipe')))
                    elif isPropertyTypeACTIVESUBSTANCE and not isPropertyTypeRECIPE:
                        activeSubstanceId = forceRef(item.value('activeSubstance_id'))
                        result = result and (activeSubstanceId or self.checkInputMessage(u'Действующее вещество', False,
                                                                                         self.tblSelectedActionTypes,
                                                                                         row, model.getColIndex(
                                'activeSubstance_id')))
                    if isPropertyTypeDOSES:
                        doses = forceDouble(item.value('doses'))
                        result = result and (
                                    doses or self.checkInputMessage(u'Doses', False, self.tblSelectedActionTypes, row,
                                                                    model.getColIndex('doses')))
                    duration = forceInt(item.value('duration'))
                    result = result and (
                                duration or self.checkInputMessage(u'Длительность', False, self.tblSelectedActionTypes,
                                                                   row, model.getColIndex('duration')))
                    aliquoticity = forceInt(item.value('aliquoticity'))
                    result = result and (
                                aliquoticity or self.checkInputMessage(u'Кратность', False, self.tblSelectedActionTypes,
                                                                       row, model.getColIndex('aliquoticity')))
                    directionDate = forceDate(item.value('directionDate'))
                    result = result and (directionDate or self.checkInputMessage(u'Назначить', False,
                                                                                 self.tblSelectedActionTypes, row,
                                                                                 model.getColIndex('directionDate')))
                    begDate = forceDate(item.value('begDate'))
                    result = result and (
                                begDate or self.checkInputMessage(u'Начать', False, self.tblSelectedActionTypes, row,
                                                                  model.getColIndex('begDate')))
                    result = result and (begDate >= directionDate or self.checkValueMessage(
                        u'"Дата начала" не может быть меньше "Даты назначения"!', False, self.tblSelectedActionTypes,
                        row, model.getColIndex('begDate')))
        return result


    def saveData(self):
        if not self.checkDataEntered():
            return False
        if self.modelSelectedActionTypes.hasExistsInSelected():
            result = QtGui.qApp.isExistsActionControlledInAddActionF9()
            if result:
                skipable = result == 1
                return self.checkValueMessage(u'Обнаружена попытка повторной регистрации уже имеющихся у пациента назначений',
                                              skipable,
                                              self.tblSelectedActionTypes)
        return True


    def updateConditionsByEventTypeDefaults(self):
        onlyNotExistsCondition = getEventOnlyNotExistsCondition(self.eventTypeId)
        if onlyNotExistsCondition != CEventTypeDescription.cDefault:
            self.chkOnlyNotExists.setChecked(onlyNotExistsCondition == CEventTypeDescription.cYes)

        plannerCondition = getEventPlannerCondition(self.eventTypeId)
        if plannerCondition != CEventTypeDescription.cDefault:
            self.chkPlanner.setChecked(plannerCondition == CEventTypeDescription.cYes)

        orgStructureCondition = getEventOrgStructureCondition(self.eventTypeId)
        if orgStructureCondition != CEventTypeDescription.cDefault:
            self.chkOrgStructure.setChecked(orgStructureCondition == CEventTypeDescription.cYes)

        nomenclatureCondition = getEventNomenclatureCondition(self.eventTypeId)
        if nomenclatureCondition != CEventTypeDescription.cDefault:
            self.chkNomenclative.setChecked(nomenclatureCondition == CEventTypeDescription.cYes)

        mesCondition = getEventMESCondition(self.eventTypeId)
        if mesCondition != CEventTypeDescription.cDefault:
            self.chkMes.setChecked(mesCondition == CEventTypeDescription.cYes)

#        self.showActionTypesWithoutService = getEventShowActionTypesWithoutService(self.eventTypeId)


    def setContractId(self, contractId, chkContractByFinanceId):
        self.contractId = contractId
        enabled = bool(self.contractId)

        contractCondition = getEventContractCondition(self.eventTypeId)
        if contractCondition == CEventTypeDescription.cDefault:
            isChecked = bool(self.contractId and bool(chkContractByFinanceId))
        else:
            isChecked = contractCondition == CEventTypeDescription.cYes

        self.chkContract.setChecked(isChecked)
        self._tmpValueIsCheckedContract = isChecked
        self.chkContract.setEnabled(QtGui.qApp.userHasRight(urEditContractConditionF9) and enabled)
        self.cmbPriceListContract.setFinanceId(self._payableFinanceId)
        self.cmbPriceListContract.setAddNone(False)

        priceListCount = self.cmbPriceListContract.count()
        if priceListCount:
            self.cmbPriceListContract.setCurrentIndex(0)
        else:
            self.chkPriceList.setEnabled(False)


    def getContractId(self):
        return self.contractId

    def setMesId(self, mesId, clientMesInfo):
        self.mesId = mesId
        self.chkMes.setEnabled(bool(self.mesId))
        self.chkIsNecessary.setEnabled(bool(self.mesId))
        self.chkAmountFromMES.setEnabled(bool(self.mesId))
        self.chkNomenclative.setChecked(bool(self.mesId))
        self.chkMes.setChecked(bool(self.mesId))
        self.tblActionTypes.model().setMesId(self.mesId)
        self.clientMesInfo = clientMesInfo


    def getPreferableActionTypes(self):
        if self.preferableActionTypes is None:
            db = QtGui.qApp.db
            tableActionType = db.table('ActionType')
            idList = QtGui.qApp.db.getIdList(tableActionType,
                               'id',
                               [tableActionType['deleted'].eq(0),
                                tableActionType['showInForm'].ne(0),
                                tableActionType['isPreferable'].ne(0),
                               ])
            self.preferableActionTypes = set(idList)
        return self.preferableActionTypes


    def getActionTypesWithoutService(self):
        if self.actionTypeWithoutService is None:
            db = QtGui.qApp.db
            tableActionType = db.table('ActionType')
            tableActionTypeService = db.table('ActionType_Service')
            tableActionType = tableActionType.leftJoin(tableActionTypeService, tableActionTypeService['master_id'].eq(tableActionType['id']))
            idList = db.getIdList(tableActionType,
                               tableActionType['id'],
                               [tableActionTypeService['id'].isNull(),
                                tableActionType['deleted'].eq(0)
                               ])
            self.actionTypeWithoutService = idList
        return self.actionTypeWithoutService


    def getNomenclativeActionTypes(self):
        if self.nomenclativeActionTypes is None:
            db = QtGui.qApp.db
            tableActionType = db.table('ActionType')
            idList = db.getIdList(tableActionType,
                               'id',
                               [tableActionType['deleted'].eq(0),
                                tableActionType['showInForm'].ne(0),
                                tableActionType['nomenclativeService_id'].isNotNull(),
                               ])
            self.nomenclativeActionTypes = set(idList)
        return self.nomenclativeActionTypes


    def getOrgStructureActionTypes(self):
        if self.cmbOrgStructure.isEnabled():
            orgStructureId = self.cmbOrgStructure.value()
        else:
            orgStructureId = self.orgStructureId
        idSet = self.getCachedActionTypesByOrgStructure(orgStructureId)
        if not bool(idSet):
            idSet = getOrgStructureActionTypeIdSet(orgStructureId)
            self.setCachedActionTypesByOrgStructure(orgStructureId, idSet)
        self.orgStructureActionTypes = idSet
        return self.orgStructureActionTypes


    def setSpecialityId(self):
        specialityId = QtGui.qApp.userSpecialityId
        if QtGui.qApp.defaultKLADR()[:2] == u'23':
            specialityId = None
            
        if not specialityId:
            execPersonId = self.execPerson
            if not execPersonId and self.eventId:
                record = QtGui.qApp.db.getRecord('Event', 'execPerson_id', self.eventId)
                if record:
                    execPersonId = forceRef(record.value('execPerson_id'))
            if execPersonId:
                specialityId = forceRef(QtGui.qApp.db.translate('Person',
                                                'id',
                                                execPersonId,
                                                'speciality_id'))
        if specialityId:
            self.specialityId = specialityId
            self.cmbSpeciality.setValue(self.specialityId)
            self.specialityRegionalCode = forceString(QtGui.qApp.db.translate('rbSpeciality', 'id', self.specialityId, 'regionalCode'))


    def getPlannedActionTypes(self):
        if self.isOrgStructirePriority:
            return set()
        specialityId = self.cmbSpeciality.value()
        idSet = self.getCachedPlannedActionTypesBySpeciality(specialityId, self.eventTypeId)
        if bool(idSet):
            self.plannedActionTypes = idSet
        else:
            db = QtGui.qApp.db
            tableETA = db.table('EventType_Action')
            tableActionType = db.table('ActionType')
            table = tableETA.innerJoin(tableActionType,
                                       tableActionType['id'].eq(tableETA['actionType_id'])
                                      )
            cond = [tableETA['eventType_id'].eq(self.eventTypeId),
                    tableETA['actionType_id'].isNotNull(),
                    tableActionType['deleted'].eq(0),
                    tableActionType['showInForm'].ne(0),
                   ]
            if specialityId:
                cond.append(db.joinOr([tableETA['speciality_id'].eq(specialityId),
                                       tableETA['speciality_id'].isNull()]))
            else:
                cond.append(tableETA['speciality_id'].isNull())
            idList = db.getIdList(table,
                                  tableETA['actionType_id'].name(),
                                  cond
                                  )
            idSet = set(idList)
            self.setCachedPlannedActionTypesBySpeciality(specialityId, self.eventTypeId, idSet)
            self.plannedActionTypes = idSet
        return self.plannedActionTypes


    def getNotRestrictActionTypes(self):
        clientId = self.getClientId()
        if not clientId:
            return set()
        date = self.eventDate
        if not date:
            if hasattr(self, 'eventEditor') and hasattr(self.eventEditor, 'eventSetDateTime'):
                date = self.eventEditor.eventSetDateTime
            else:
                date = QDate.currentDate()
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableAction = db.table('Action')
        tableActionType = db.table('ActionType')
        cond = [tableEvent['client_id'].eq(clientId),
                tableEvent['deleted'].eq(0),
                tableAction['deleted'].eq(0),
                tableActionType['deleted'].eq(0),
                tableAction['endDate'].dateLe(date),
                u'''(ActionType.isRestrictExpirationDate = 1
                        AND DATE(DATE_ADD(Action.endDate, INTERVAL ActionType.expirationDate MONTH)) >= DATE(%s))'''%(db.formatDate(date))
                ]
        if self.eventId:
            cond.append(tableEvent['id'].ne(self.eventId))
        queryTable = tableEvent.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
        queryTable = queryTable.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
        idList = db.getIdList(queryTable, u'actionType_id', cond, u'Action.endDate DESC')
        setIdList = set(idList)
        return setIdList


    def getActionTypeIdListWithLimitationByContractTariffAttach(self, contractId=None, eventDate=None):
        if contractId is None:
            contractId = self.contractId
            
        if eventDate is None:
            eventDate = self.eventDate
        if eventDate is None:
            eventDate = QDate.currentDate()
            
        contractTariffLimitationsIsChecked = False

        if self.chkContractTariffLimitations.isEnabled():
            contractTariffLimitationsIsChecked = self.chkContractTariffLimitations.isChecked()

        key = (contractId, contractTariffLimitationsIsChecked, eventDate)

        result = self.mapContractId2ActionTypes.get(key, None)
        if result is None:
            actionTypeIdListByContract, limitationCache = getActionTypeIdListWithLimitationByContractTariffAttachByDate(contractId, eventDate, 
                                                                                    contractTariffLimitationsIsChecked)
            if bool(actionTypeIdListByContract):
                contractActionTypes = set(actionTypeIdListByContract)
            else:
                contractActionTypes = set([])
            result = (contractActionTypes, limitationCache, eventDate)
            self.mapContractId2ActionTypes[key] = result
        return result


    def getContractActionTypes(self, contractId=None):
        return self.getActionTypeIdListWithLimitationByContractTariffAttach(contractId)[0]


    def getContractTariffAttachCache(self, contractId):
        return self.getActionTypeIdListWithLimitationByContractTariffAttach(contractId)[1]


    def getMesActionTypes(self):
        isNecessary = self.chkIsNecessary.isChecked()
        idList = getActionTypeIdListByMesId(self.mesId, isNecessary, self.clientMesInfo, self.eventDate)
        idSet = set(idList) if idList else set()
        return idSet, idSet


    def filterByContractTariffAttachLimitation(self, enabledActionTypes):
        if self.chkContractTariffLimitations.isEnabled() and self.chkContractTariffLimitations.isChecked():
            if self.chkContract.isChecked():
                contractId = self.contractId
            elif self.chkPriceList.isChecked():
                contractId = self.cmbPriceListContract.value()
            else:
                return enabledActionTypes
            if contractId:
                contractTariffAttachCache = self.getContractTariffAttachCache(contractId)
                return list(set(enabledActionTypes) & set(contractTariffAttachCache.keys()))
        return enabledActionTypes


    @withWaitCursor
    def updateTreeData(self):
        self.modelActionTypes.setContractTariffAttachCache({})
        if self.chkSexAndAge.isChecked() and bool(self.clientSex) and bool(self.clientAge):
            self.modelActionTypeGroups.setFilter(self.clientSex, self.clientAge, self.eventDate, self.clientBirthDate)
        else:
            self.modelActionTypeGroups.setFilter(0, None)
        sets = []
        mesActionTypeIdList = []
        self.mesActionTypeIdList = []
        if self.chkMes.isChecked() and self.mesId:
            mesActionTypeGroupId, mesActionTypeIdList = self.getMesActionTypes()
            sets.append(mesActionTypeGroupId)
        if self.chkPreferable.isChecked():
            sets.append(self.getPreferableActionTypes())
        if self.chkNomenclative.isChecked():
            sets.append(self.getNomenclativeActionTypes())
        if self.chkOrgStructure.isChecked() and self.orgStructureId:
            sets.append(self.getOrgStructureActionTypes())
        if self.chkPlanner.isChecked() and self.eventTypeId:
            sets.append(self.getPlannedActionTypes())
        if self.chkContract.isChecked():
            if self.contractId:
                self.modelActionTypes.setContractTariffAttachCache(self.getContractTariffAttachCache(self.contractId))
                sets.append(self.getContractActionTypes())
        if self.chkSexAndAge.isChecked():
            sets.append(self.getActionTypeIdListByClientSexAndAge())
        elif self.chkPriceList.isChecked():
            contractId = self.cmbPriceListContract.value()
            if contractId:
                self.modelActionTypes.setContractTariffAttachCache(self.getContractTariffAttachCache(contractId))
                sets.append(self.getContractActionTypes(contractId))
        if sets:
            enabledActionTypes = list(reduce(lambda x, y: x&y, sets))
            enabledActionTypes = self.filterByContractTariffAttachLimitation(enabledActionTypes)
            enabledActionTypes = QtGui.qApp.db.getTheseAndParents('ActionType', 'group_id', enabledActionTypes)
            self.mesActionTypes = self.mesActionTypeIdList = list( set(mesActionTypeIdList) & set(enabledActionTypes) )
        else:
            enabledActionTypes = None
        restrictActionTypes = self.getNotRestrictActionTypes()
        if restrictActionTypes and enabledActionTypes:
            enabledActionTypes = list(set(enabledActionTypes or []) - restrictActionTypes)
        if self.chkOnlyNotExists.isChecked():
            self.disabledActionTypeIdList = list(self.existsActionTypesList)
            if self.chkMes.isChecked():
                for mesActionTypeId in mesActionTypeIdList:
                    if mesActionTypeId not in self.existsActionTypesList:
                        continue
                    checkMesGroupsHelper = self.tblActionTypes.model().getCheckMesGroupsHelper()
                    mesExistsList = checkMesGroupsHelper.getListByIdOverGroupCodeLimit(mesActionTypeId)
                    for at in mesExistsList:
                        self.disabledActionTypeIdList.append(at.id)
        else:
            self.disabledActionTypeIdList = None
        index = self.treeActionTypeGroups.currentIndex()
        if index.isValid() and index.internalPointer():
            currentGroupId = index.internalPointer().id()
        else:
            currentGroupId = None
#        if self.showActionTypesWithoutService:
#            actionTypesWithoutService = self.getActionTypesWithoutService()
#            enabledActionTypes = enabledActionTypes + actionTypesWithoutService
        self.enabledActionTypes = enabledActionTypes
        if self.chkFindFilter.isChecked() and self.findFilterText:
            findFilterActionTypes = self.getActionTypeIdListByFindFilter()
            enabledActionTypes = list(set(enabledActionTypes) & findFilterActionTypes) if enabledActionTypes else findFilterActionTypes
            self.enabledActionTypes = enabledActionTypes
        if self.chkCSG.isChecked():
            indexCSG = self.cmbCSG.currentIndex()
            if indexCSG > 0:
                csgRecord = self.cmbCSG.mapIndexToCSGRecord.get(indexCSG, None)
                CSGCode = forceString(csgRecord.value('CSGCode'))
                db = QtGui.qApp.db
                tableCSG =db.table('mes.CSG')
                recordCSG = db.getRecordEx(tableCSG, 'mes.CSG.id', [tableCSG['code'].like(CSGCode)])
                self.CSGId = forceRef(recordCSG.value('id')) if recordCSG else None
                CSGCodeActionTypes = self.getActionTypeIdListByCSGCode()
                enabledActionTypes = list(set(enabledActionTypes) & CSGCodeActionTypes) if enabledActionTypes else CSGCodeActionTypes
                self.enabledActionTypes = enabledActionTypes

        self.modelActionTypeGroups.setEnabledActionTypeIdList(enabledActionTypes)
        self.modelActionTypeGroups.setDisabledActionTypeIdList(self.disabledActionTypeIdList)

        pref = QtGui.qApp.preferences
        props = pref.appPrefs
        expand = forceInt(props.get('actionTypeTreeExpand',  QVariant()))
        if not expand:
            self.treeActionTypeGroups.expandToDepth(0)
        elif expand == 1:
            self.treeActionTypeGroups.expandAll()
        else:
            expandLevel = forceInt(props.get('actionTypeTreeExpandLevel',  QVariant(1)))
            self.treeActionTypeGroups.expandToDepth(expandLevel)

        index = self.modelActionTypeGroups.findItemId(currentGroupId)
        if not index:
            index = self.modelActionTypeGroups.index(0, 0, None)
        self.treeActionTypeGroups.setCurrentIndex(index)
        if not self.enabledActionTypes:
            self.clearGroup()
        for atId in self.preActionTypeIdList:
            self.setSelected(atId, True, resetMainModel=True)


    def getActionTypeIdListByCSGCode(self):
        self.actionTypeIdListByCSGCode = set([])
        if self.CSGId:
            db = QtGui.qApp.db
            tableActionType = db.table('ActionType')
            tableCSGService = db.table('mes.CSG_Service')
            cond = [tableActionType['deleted'].eq(0),
                    tableActionType['showInForm'].ne(0),
                    tableCSGService['master_id'].eq(self.CSGId)
                   ]
            queryTable = tableCSGService.innerJoin(tableActionType, tableActionType['code'].eq(tableCSGService['serviceCode']))
            self.actionTypeIdListByCSGCode = set(db.getIdList(queryTable, 'ActionType.id', cond))
        return self.actionTypeIdListByCSGCode


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
            groupIdList = db.getDistinctIdList(tableActionType, [tableActionType['id']], [tableActionType['group_id'].inlist(groupIdList), tableActionType['deleted'].eq(0), tableActionType['showInForm'].ne(0)])
            groupIdList.append(groupId)
            cond.append(tableActionType['group_id'].inlist(groupIdList))
        else:
            cond.append(u'(ActionType.group_id IS NULL OR'
                        u' (EXISTS(SELECT AT.id FROM ActionType AS AT WHERE'
                        u' AT.id = ActionType.group_id AND AT.showInForm != 0 AND AT.deleted = 0)))')
        if _class is not None:
            cond.append(tableActionType['class'].eq(_class))
        if self.mesActionTypeIdList:
            cond.append('NOT EXISTS(SELECT id FROM ActionType AS at WHERE ActionType.id NOT IN (%s) AND at.group_id = ActionType.id AND at.deleted = 0)' % (u','.join(str(mesActionTypeId) for mesActionTypeId in self.mesActionTypeIdList if mesActionTypeId)))
        else:
            cond.append('NOT EXISTS(SELECT id FROM ActionType AS at WHERE at.group_id = ActionType.id AND at.deleted = 0)')
        recordList = QtGui.qApp.db.getRecordList(tableActionType, 'id, code, name', cond, 'code, id desc')
        if recordList:
            idList = []
            codeSet = set()

            enabledActionTypesSet = set(self.enabledActionTypes) if self.enabledActionTypes else set()
            disabledActionTypeIdListSet = set(self.disabledActionTypeIdList) if self.disabledActionTypeIdList else set()
            for record in recordList:
                id = forceRef(record.value('id'))
                # этот костыль для победы над mariaDB
                if self.enabledActionTypes is not None and id not in enabledActionTypesSet:
                    continue
                if self.disabledActionTypeIdList and id in disabledActionTypeIdListSet:
                    continue

                if self.isActionTypeIdValidByContractTariffAttach(id):
                    code = forceString(record.value('code')).upper()
                    if code not in codeSet:
                        codeSet.add(code)
                        idList.append(id)
                        idList.append(id)

            # возвращаем необходимую сортировку
            recordList = QtGui.qApp.db.getRecordList(tableActionType, 'id, code, name', tableActionType['id'].inlist(idList), self._sortActionType.order)
            idList = []
            for index, record in enumerate(recordList):
                id = forceRef(record.value('id'))
                idList.append(id)
                code = forceString(record.value('code')).upper()
                name = forceString(record.value('name')).upper()
                existCode = self.actionsCacheByCode.get(code, None)
                if existCode is None:
                    self.actionsCacheByCode[code] = index
                existName = self.actionsCodeCacheByName.get(name, None)
                if existName is None:
                    self.actionsCodeCacheByName[name] = code

        else:
            idList = []

        self.tblActionTypes.setIdList(idList)


    def on_sortActions(self, logicalIndex):
        header=self.tblActionTypes.horizontalHeader()
        if logicalIndex:
            self._sortActionType.order = 'code %s, name' if logicalIndex == 1 else 'name %s, code'
            if self._sortActionType.column == logicalIndex:
                self._sortActionType.isAscending = not self._sortActionType.isAscending
            else:
                self._sortActionType.column = logicalIndex
                self._sortActionType.isAscending = True

            header.setSortIndicatorShown(True)
            header.setSortIndicator(self._sortActionType.column,
                                    Qt.AscendingOrder if self._sortActionType.isAscending else Qt.DescendingOrder)

            if self._sortActionType.isAscending:
                self._sortActionType.order = self._sortActionType.order % 'ASC'
            else:
                self._sortActionType.order = self._sortActionType.order % 'DESC'

            index = self.treeActionTypeGroups.currentIndex()
            self.on_selectionModelActionTypeGroups_currentChanged(index, index)

        else:
            if self._sortActionType.column != logicalIndex:
                header.setSortIndicatorShown(False)
                self._sortActionType.order = 'code, name'
                self._sortActionType.column = 0
                index = self.treeActionTypeGroups.currentIndex()
                self.on_selectionModelActionTypeGroups_currentChanged(index, index)

    def on_sortTemplates(self, logicalIndex):
        header=self.tblTemplates.horizontalHeader()
        self._sortTemplates.order = 'ActionTypeGroup.name %s' if logicalIndex else 'ActionTypeGroup.code %s'
        if self._sortTemplates.column == logicalIndex:
            self._sortTemplates.isAscending = not self._sortTemplates.isAscending
        else:
            self._sortTemplates.column = logicalIndex
            self._sortTemplates.isAscending = True

        header.setSortIndicatorShown(True)
        header.setSortIndicator(self._sortTemplates.column,
                                Qt.AscendingOrder if self._sortTemplates.isAscending else Qt.DescendingOrder)

        if self._sortTemplates.isAscending:
            self._sortTemplates.order = self._sortTemplates.order % 'ASC'
        else:
            self._sortTemplates.order = self._sortTemplates.order % 'DESC'

        self.modelTemplates.setTemplatesOrder(self._sortTemplates.order)


    def isActionTypeIdValidByContractTariffAttach(self, actionTypeId):
        if self.chkContractTariffLimitations.isChecked():

            contractTariffAttachCache = None
            if self.chkContract.isChecked():
                if self.contractId:
                    contractTariffAttachCache = self.getContractTariffAttachCache(self.contractId)

            elif self.chkPriceList.isChecked():
                contractId = self.cmbPriceListContract.value()
                if contractId:
                    contractTariffAttachCache = self.getContractTariffAttachCache(contractId)

            if contractTariffAttachCache:
                clientAttachTypeId = self.clientAttachTypeId()
                contractTariffAttcahList = contractTariffAttachCache.get(actionTypeId, None)
                if contractTariffAttcahList:
                    if clientAttachTypeId:
                        for attach in contractTariffAttcahList:
                            if attach[0] == clientAttachTypeId:
                                return True
                    return False
        return True


    def clearGroup(self):
        self.tblActionTypes.setIdList([])


    def invalidateChecks(self):
        model = self.modelActionTypes
        lt = model.index(0, 0)
        rb = model.index(model.rowCount()-1, 1)
        model.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), lt, rb)


    def rebuildActionTypes(self, force=False):
        if not self.modelActionTypes.idList() or force:
            index = self.treeActionTypeGroups.currentIndex()
            self.on_selectionModelActionTypeGroups_currentChanged(index, index)


    def getMESqwt(self, actionTypeId):
        if self.mesActionTypes and self.chkMes.isChecked() and self.chkAmountFromMES.isChecked():
            if actionTypeId in self.mesActionTypes:
                item = self.modelActionTypes.getRecordById(actionTypeId)
                if item:
                    code = forceString(item.value('code'))
                    record = getMesServiceInfo(code, self.mesId)
                    if record:
                        return forceInt(record.value('averageQnt'))
        return None

    def updateContractTariffLimitationsChecked(self):
        value = self.chkContract.isChecked() or self.chkPriceList.isChecked()
        self.chkContractTariffLimitations.setEnabled(value)


    @pyqtSignature('bool')
    def on_chkOnlyNotExists_toggled(self, value):
        self.updateTreeData()
        self.rebuildActionTypes()


    @pyqtSignature('bool')
    def on_chkSexAndAge_toggled(self, value):
        self.updateTreeData()
        self.rebuildActionTypes()


    @pyqtSignature('bool')
    def on_chkCSG_toggled(self, value):
        self.updateTreeData()
        self.rebuildActionTypes()


    @pyqtSignature('bool')
    def on_chkPreferable_toggled(self, value):
        self.updateTreeData()
        self.rebuildActionTypes()


    @pyqtSignature('bool')
    def on_chkNomenclative_toggled(self, value):
        self.updateTreeData()
        self.rebuildActionTypes()


    @pyqtSignature('bool')
    def on_chkOrgStructure_toggled(self, value):
        self.updateTreeData()
        self.rebuildActionTypes()


    @pyqtSignature('bool')
    def on_chkPlanner_toggled(self, value):
        self.isOrgStructirePriority = not value
        self.updateTreeData()
        self.rebuildActionTypes()


    @pyqtSignature('bool')
    def on_chkContract_toggled(self, value):
        self._tmpValueIsCheckedContract = value
        self.chkPriceList.blockSignals(True)
        self.chkContractTariffLimitations.blockSignals(True)
        if value:
            self.chkPriceList.setChecked(False)
        self.updateContractTariffLimitationsChecked()
        self.chkPriceList.blockSignals(False)
        self.chkContractTariffLimitations.blockSignals(False)
        self.updateTreeData()
        self.rebuildActionTypes()


    @pyqtSignature('bool')
    def on_chkPriceList_toggled(self, value):
        self.chkContract.blockSignals(True)
        self.chkContractTariffLimitations.blockSignals(True)
        if value:
            self.chkContract.setChecked(False)
        else:
            self.chkContract.setChecked(self._tmpValueIsCheckedContract)
        self.updateContractTariffLimitationsChecked()
        self.chkContract.blockSignals(False)
        self.chkContractTariffLimitations.blockSignals(False)
        self.updateTreeData()
        self.rebuildActionTypes()


    @pyqtSignature('bool')
    def on_chkContractTariffLimitations_toggled(self, value):
        self.updateTreeData()
        self.rebuildActionTypes()


    @pyqtSignature('bool')
    def on_chkMes_toggled(self, value):
        self.tblActionTypes.model().setCheckMesGroups(value)
        self.updateTreeData()
        self.rebuildActionTypes()


    @pyqtSignature('int')
    def on_cmbCSG_currentIndexChanged(self, index):
        if self.chkCSG.isChecked() and index > 0 and index != self.indexCmbCSGOLD:
            self.updateTreeData()
            self.rebuildActionTypes()
            self.indexCmbCSGOLD = index


    @pyqtSignature('int')
    def on_cmbOrgStructure_currentIndexChanged(self, index):
        self.updateTreeData()
        self.rebuildActionTypes()

    @pyqtSignature('int')
    def on_cmbSpeciality_currentIndexChanged(self, index):
        self.updateTreeData()
        self.rebuildActionTypes()


    @pyqtSignature('int')
    def on_cmbPriceListContract_currentIndexChanged(self, index):
        self.updateTreeData()
        self.rebuildActionTypes()



    @pyqtSignature('bool')
    def on_chkIsNecessary_toggled(self, value):
        self.updateTreeData()
        self.rebuildActionTypes()

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


    @pyqtSignature('const QModelIndex&,const QModelIndex&')
    def on_selectionModelActionTypeGroups_currentChanged(self, current, previous):
        self._updateActionTypesByTree(current)


    def _updateActionTypesByTemplate(self):
        templateId = self.tblTemplates.currentItemId()
        if not templateId:
            self.tblActionTypes.setIdList([])
            return
        db = QtGui.qApp.db
        table = db.table('ActionTypeGroup_Item')
        tableActionType = db.table('ActionType')
        queryTable = tableActionType.innerJoin(table, table['actionType_id'].eq(tableActionType['id']))
        cond = [table['deleted'].eq(0),
                table['master_id'].eq(templateId),
                tableActionType['showInForm'].ne(0),
                tableActionType['deleted'].eq(0)
                ]
        idList = db.getDistinctIdList(queryTable, 'actionType_id', where=cond)
        self.tblActionTypes.setIdList(idList)


    def getActionTypeItemsByTemplate(self, actionTypeId):
        templateId = self.tblTemplates.currentItemId()
        if not templateId:
            self.tblActionTypes.setIdList([])
            return None
        db = QtGui.qApp.db
        table = db.table('ActionTypeGroup_Item')
        return db.getRecordList(table, '*', [table['deleted'].eq(0), table['master_id'].eq(templateId), table['actionType_id'].eq(actionTypeId)], [table['id'].name()])


    @pyqtSignature('const QModelIndex&,const QModelIndex&')
    def on_selectionModelTemplates_currentChanged(self, current, previous):
        self._updateActionTypesByTemplate()


    @pyqtSignature('int')
    def on_tabWgtActionTypes_currentChanged(self, index):
        if index == _TREE_TAB_INDEX:
            self._updateActionTypesByTree(self.treeActionTypeGroups.currentIndex())
        elif index == _TEMPLATES_TAB_INDEX:
            self.modelTemplates.loadData(self.actionTypeClasses[0] if len(self.actionTypeClasses) == 1 else None)
            self._updateActionTypesByTemplate()


    @pyqtSignature('')
    @withWaitCursor
    def on_bntSelectAll_pressed(self):
        notSelected = []
        chkMes = self.chkMes.isChecked()
        self.setEnabled(False)
        try:
            for i, actionTypeId in enumerate(self.modelActionTypes.idList()):
                if i % 50 == 0:
                    QtGui.qApp.processEvents()
                if chkMes:
                    if actionTypeId not in notSelected:
                        checkMesGroupsHelper = self.tblActionTypes.model().getCheckMesGroupsHelper()
                        mesExistsList = checkMesGroupsHelper.getListByIdOverGroupCodeLimit(actionTypeId)
                        mesExistsListId = [at.id for at in mesExistsList]
                        actionType = CActionTypeCache.getById(actionTypeId)
                        if actionTypeId in mesExistsListId:
                            # ТТ 2691 исключение должно быть для услуг врачей терапевта B04.047 или врача общей практики B04.026
                            if actionType.code.startswith('B04.047') \
                                or actionType.code.startswith('B04.026') \
                                or actionType.code == 'B01.026.001' \
                                or actionType.code == 'B01.047.005':
                                if (bool(actionType.code.startswith('B04.047') or bool(actionType.code == 'B01.047.005')) and self.specialityRegionalCode in ['76', '206']) \
                                    or (bool(actionType.code.startswith('B04.026') or bool(actionType.code == 'B01.026.001')) and self.specialityRegionalCode in ['39', '224']):
                                    mesExistsListId.pop(mesExistsListId.index(actionTypeId))
                                    notSelected += mesExistsListId
                                else:
                                    notSelected.append(actionTypeId)
                            else:
                                mesExistsListId.pop(mesExistsListId.index(actionTypeId))
                                notSelected += mesExistsListId
                if actionTypeId not in notSelected:
                    self.setSelected(actionTypeId, True)
                else:
                    if chkMes:
                        self.setSelected(actionTypeId, False)
            self.invalidateChecks()
        finally:
            self.setEnabled(True)


    @pyqtSignature('')
    def on_bntClearSelection_pressed(self):
        self.selectedActionTypeIdList = []
        self.updateSelectedCount()
        self.invalidateChecks()
        self.modelSelectedActionTypes.removeAll()


    @pyqtSignature('')
    def on_btnSaveTemplate_pressed(self):
#        class_ = self.actionTypeClasses[0] if len(self.actionTypeClasses) == 1 else None
        # т.к. редактор шаблонов требует во входных данных информацию о классе каждого добавляемого действия -
        # вытаскиваем эту информацию из БД, т.к. информация о классах действий не хранится в диалоге
        db = QtGui.qApp.db
        table = CTable('ActionType', db)
        recs = db.getRecordList(table, ['id', 'class'], table['id'].inlist(self.selectedActionTypeIdList))
        mapActionTypeIdToClass = {}
        for rec in recs:
            mapActionTypeIdToClass[forceRef(rec.value('id'))] = forceInt(rec.value('class'))
        actionsList = []
        for record in self.tblSelectedActionTypes.model().items():
            newRecord = record
            newRecord.append(QSqlField('class', QVariant.Int))  # Для редактора шаблона нужна информация о классе добавляемого действия
            newRecord.setValue('class', toVariant(mapActionTypeIdToClass.get(forceRef(newRecord.value('actionType_id')), None)))
            actionsList.append(newRecord)

        curTemplateId = None
        dlg = ActionTypeGroupEditor(self, curTemplateId)
        dlg.setActionTypes(actionsList)
        dlg.exec_()


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


    @pyqtSignature('int')
    def on_chkFindFilter_stateChanged(self, state):
        if state in (Qt.Unchecked, Qt.Checked):
            self.updateTreeData()
            self.rebuildActionTypes()


    @pyqtSignature('QString')
    def on_edtFindFilter_textChanged(self, text):
        if text and self.chkFindFilter.isChecked():
            self.setFindFilterText(addDotsEx(forceStringEx(text)))
            self.updateTreeData()
            self.rebuildActionTypes()


    @pyqtSignature('')
    def on_btnFindTemplates_clicked(self):
        self.modelTemplates.setFindFilterText(unicode(self.edtFindTemplates.text()))
        self.modelTemplates.loadData(self.actionTypeClasses[0] if len(self.actionTypeClasses) == 1 else None)
        self._updateActionTypesByTemplate()


    @pyqtSignature('QString')
    def on_edtNecessity_valueChanged(self, val):
        self.updateTreeData()
        self.rebuildActionTypes()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelActionTypes_currentChanged(self, current, previous):
        if self.mesActionTypes:
            id = self.tblActionTypes.currentItemId()
            if id and id in self.mesActionTypes:
                item = self.tblActionTypes.currentItem()
                code = forceString(item.value('code'))
                record = getMesServiceInfo(code, self.mesId)
                if record:
                    averageQnt      = forceInt(record.value('averageQnt'))
                    necessity       = forceDouble(record.value('necessity'))
                    doctorWTU       = forceDouble(record.value('doctorWTU'))
                    paramedicalWTU  = forceDouble(record.value('paramedicalWTU'))
                    text = u'СК: %d; ЧП: %.1f; УЕТвр: %.1f; УЕТср: %.1f' %(averageQnt,
                                                                           necessity,
                                                                           doctorWTU,
                                                                           paramedicalWTU)
                    self.lblMesInfo.setText(text)
                    return
        self.lblMesInfo.clear()


class CCheckMesGroupsHelper(object):
    def __init__(self, mesId=None):
        self.mesId = mesId
        self.dictById = {}
        self.dictByGroupCode = {}


    def setMesId(self, mesId):
        if mesId != self.mesId:
            self.mesId = mesId
            self.loadActionTypes()


    def loadActionTypes(self):
        self.dictById.clear()
        self.dictByGroupCode.clear()
        if not self.mesId:
            return
        stmt = '''
SELECT
    ActionType.id AS id, ActionType.code AS code, mes.MES_service.groupCode
FROM
    mes.MES_service
LEFT JOIN mes.mrbService ON mes.MES_service.service_id = mes.mrbService.id
LEFT JOIN rbService ON rbService.code = mes.mrbService.code
LEFT JOIN ActionType ON ActionType.nomenclativeService_id = rbService.id
WHERE ActionType.deleted = 0 AND ActionType.showInForm = 1
  AND mes.MES_service.master_id = %d
GROUP BY ActionType.code, ActionType.id
ORDER BY mes.MES_service.groupCode, ActionType.code, mes.mrbService.name, mes.mrbService.id
''' % self.mesId
        query = QtGui.qApp.db.query(stmt)
        while query.next():
            record = query.record()
            at = smartDict()
            at.id = forceRef(record.value('id'))
            at.code = forceString(record.value('code'))
            at.groupCode = forceInt(record.value('groupCode'))
            self.dictById[at.id] = at
            byGroupCode = self.dictByGroupCode.setdefault(at.groupCode, [])
            byGroupCode.append(at)


    def getById(self, id):
        return self.dictById.get(id, None)


    def getListByGroupCode(self, groupCode):
        return self.dictByGroupCode.get(groupCode, [])


    def getListById(self, id):
        at = self.getById(id)
        if at:
            return self.getListByGroupCode(at.groupCode)
        return []


    def getListByIdOverGroupCodeLimit(self, id, limit=0):
        at = self.getById(id)
        if at:
            if at.groupCode > limit:
                return self.getListByGroupCode(at.groupCode)
        return []


class CActionsModel(CTableModel):
    def __init__(self, parent):
        self._contractTariffAtachCache = {}
        self._actionTypeId2Color = {}
        cols = [CEnableCol(u'Включить',     ['id'],   20,  parent),
                CTextCol(u'Код',            ['code'], 20),
                CTextCol(u'Наименование',   ['name'], 20),
                 ]
        self.initModel(parent, cols)


    def setContractTariffAttachCache(self, contractTariffAtachCache):
        self._contractTariffAtachCache = contractTariffAtachCache


    def getColor(self, actionTypeId):
        color = self._actionTypeId2Color.get(actionTypeId, None)
        if color is None:
            color = CCol.invalid
            attachList = self._contractTariffAtachCache.get(actionTypeId, None)
            if attachList:
                clientAttachTypeId = self.parentWidget.clientAttachTypeId()
                for attach in attachList:
                    if attach[0] == clientAttachTypeId:
                        color = self.getColorByContractTariffAttachValues(*attach[1:])
            self._actionTypeId2Color[actionTypeId] = color
        return color


    def getColorByContractTariffAttachValues(self, amount, agreement, exception):
        if exception:
            return QVariant(QtGui.QColor('#E75480'))
        elif agreement:
            return QVariant(QtGui.QColor(Qt.yellow))
        elif amount:
            return QVariant(QtGui.QColor(Qt.green))
        return CCol.invalid


    def initModel(self, parent, cols):
        self.parentWidget = parent
        self.checkMesGroupsHelper = CCheckMesGroupsHelper()
        self.checkMesGroups = False
        CTableModel.__init__(self, parent, cols, 'ActionType')


    def setCheckMesGroups(self, val):
        self.checkMesGroups = val


    def getCheckMesGroupsHelper(self):
        return self.checkMesGroupsHelper


    def setMesId(self, mesId):
        self.checkMesGroupsHelper.setMesId(mesId)
        self.setCheckMesGroups(bool(mesId))


    def flags(self, index):
        result = CTableModel.flags(self, index)
        if index.column() == 0:
            result |= Qt.ItemIsUserCheckable
        return result


    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        if role == Qt.BackgroundRole:
            row = index.row()
            return self.getColor(self._idList[row])
        else:
            return CTableModel.data(self, index, role)


    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.CheckStateRole:
            row = index.row()
            id = self._idList[row]
            if self.checkMesGroups and forceInt(value) == Qt.Checked:
                actionTypeGroupCodeList = self.checkMesGroupsHelper.getListByIdOverGroupCodeLimit(id)
                for at in actionTypeGroupCodeList:
                    if at.id != id:
                        self.parentWidget.setSelected(at.id, False)
                        #atIndex = self.index(self.findItemIdIndex(at.id), 0)
            if id and not (self.checkMaxOccursLimit(id)):
                return False
            self.parentWidget.setSelected(self._idList[row], forceInt(value) == Qt.Checked)
            self.emitDataChanged()
            return True
        return False


    def checkMaxOccursLimit(self, actionTypeId):
            actionType = CActionTypeCache.getById(actionTypeId)
            count = 0
            for existsActionTypeId in self.parentWidget.existsActionTypesList:
                if existsActionTypeId == actionTypeId:
                    count += 1
            result = actionType.checkMaxOccursLimit(count, True)
            return result    


class CEnableCol(CBoolCol):
    def __init__(self, title, fields, defaultWidth, selector):
        CBoolCol.__init__(self, title, fields, defaultWidth)
        self.selector = selector

    def checked(self, values):
        actionTypeId = forceRef(values[0])
        if self.selector.isSelected(actionTypeId):
            return CBoolCol.valChecked
        else:
            return CBoolCol.valUnchecked


# ######################################################################


class CExistsProxyModel(QtGui.QProxyModel):
    def __init__(self, parent):
        QtGui.QProxyModel.__init__(self, parent)
        self._mapProxyColumn2RealColumn = {0 : 0,
                                           1 : 4,
                                           2 : 5,
                                           3 : 1,
                                           4 : 3,
                                           5 : 2}

    def data(self, index, role=Qt.DisplayRole):
        row    = index.row()
        column = index.column()
        model  = self.model()
        return model.data(model.index(row, self.getRealColumn(column)), role)


    def headerData(self, section, orientation, role=Qt.DisplayRole):
        model  = self.model()
        if orientation == Qt.Horizontal:
            return model.headerData(self.getRealColumn(section), orientation, role)
        elif orientation == Qt.Vertical:
            return model.headerData(section, orientation, role)
        return QVariant()


    def getRealColumn(self, column):
        return self._mapProxyColumn2RealColumn.get(column, column)


    def idList(self):
        return self.model().idList()


    def recordCache(self):
        return self.model().recordCache()


    def columnCount(self, index=None):
        return self.model().columnCount(index)


    def rowCount(self, index=None):
        return self.model().rowCount(index)



class CExistsClientActionsModel(CTableModel):
    actionTypeNameColIndex = 4
    def __init__(self, parent):
        cols = [CDateCol(u'Назначено', ['directionDate'], 10),
                CDateCol(u'Начато', ['begDate'], 10),
                CEnumCol(u'Статус', ['status'], CActionStatus.names, 10),
                CDateCol(u'План', ['plannedEndDate'], 10),
                CRefBookCol(u'Действие', ['actionType_id'], 'ActionType', 20, showFields=2),
                CRefBookCol(u'Назначил', ['setPerson_id'], 'vrbPersonWithSpeciality', 25)]
        CTableModel.__init__(self, parent, cols)
        self.loadField('*')
        self.setTable('Action', recordCacheCapacity=None)
        self._currentEventItems = {}
        self._currentEventItemsIdList = []
        self._currentEventItemsFakeIdList = []
        self._actionTypeIdList = []


        boldFont = QtGui.QFont()
        boldFont.setWeight(QtGui.QFont.Bold)
        self._qBoldFont = QVariant(boldFont)


    def setClientId(self, clientId):
        db =  QtGui.qApp.db

        tableAction = self._table
        tableEvent  = db.table('Event')

        queryTable = tableAction.innerJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))

        #plannedEndDateCond = [tableAction['plannedEndDate'].dateGe(QDate.currentDate()),
        #                      'DATE(Action.`plannedEndDate`)=\'0000-00-00\'']

        cond = [tableAction['deleted'].eq(0),
                tableAction['status'].inlist([CActionStatus.started, CActionStatus.appointed, CActionStatus.finished]),
                #db.joinOr(plannedEndDateCond),
                tableEvent['client_id'].eq(clientId),
                tableEvent['deleted'].eq(0)]
        if self._currentEventItemsIdList:
            cond.append(tableAction['id'].notInlist(self._currentEventItemsIdList))

        idList = []
        recordList = db.getRecordList(queryTable, 'Action.*', cond)
        for record in recordList:
            actionId = forceRef(record.value('id'))
            actionTypeId = forceRef(record.value('actionType_id'))
            if actionTypeId not in self._actionTypeIdList:
                self._actionTypeIdList.append(actionTypeId)
            actionType = CActionTypeCache.getById(actionTypeId)
            actualAppointmentDuration = actionType.actualAppointmentDuration
            if self.isValidRecord(record, actualAppointmentDuration):
                idList.append(actionId)

        self.setIdList(self._currentEventItemsFakeIdList+idList)
        for fakeId, item in self._currentEventItems.items():
            record, action = item
            self.recordCache().put(fakeId, record)

#        actionTypeIdList = db.getDistinctIdList(tableAction,
#                                                tableAction['actionType_id'].name(),
#                                                tableAction['id'].inlist(idList))
#        self._actionTypeIdList.extend(actionTypeIdList)


    def setCurrentEventItems(self, items):
        self._currentEventItemsFakeIdList = []
        self._currentEventItemsIdList = []
        self._actionTypeIdList = []
        self._currentEventItems.clear()
        for idx, item in enumerate(items):
            record, action = item
            if action:
                actionType = action.getType()
                actualAppointmentDuration = actionType.actualAppointmentDuration
                if self.isValidRecord(record, actualAppointmentDuration):
                    fakeId = str(idx)
                    self._currentEventItems[fakeId] = item
                    self._currentEventItemsFakeIdList.append(fakeId)
                    realId = forceRef(record.value('id'))
                    if realId:
                        self._currentEventItemsIdList.append(realId)
                    self._actionTypeIdList.append(forceRef(record.value('actionType_id')))


    def isValidRecord(self, record, actualAppointmentDuration):
        status = forceInt(record.value('status'))
        plannedEndDate = forceDate(record.value('plannedEndDate'))
        currentDate = QDate.currentDate()
        if status in (CActionStatus.started, CActionStatus.appointed, CActionStatus.finished):
            if plannedEndDate and plannedEndDate >= currentDate:
                return True
            else:
                if status in (CActionStatus.started, CActionStatus.appointed) and not plannedEndDate:
                    return True
                if actualAppointmentDuration:
                    directionDate = forceDate(record.value('directionDate'))
                    if directionDate.addDays(actualAppointmentDuration-1) >= currentDate:
                        return True
                else:
                    return False

        return False



    def getRecordValues(self, column, row):
        return CTableModel.getRecordValues(self, column, row)


    def isCurrentEventActionId(self, actionId):
        return actionId in self._currentEventItemsIdList


    def hasActionTypeId(self, actionTypeId):
        return actionTypeId in self._actionTypeIdList


    def updateRecord(self, row, record):
        id = self._idList[row]
        self.recordCache().put(id, record)
        if id in self._currentEventItemsFakeIdList:
            actionRecord, action = self._currentEventItems[id]
            self.syncRecords(record, actionRecord)
        self.emitDataChanged()

    def syncRecords(self, sourceRecord, targetRecord):
        for fieldIdx in xrange(sourceRecord.count()):
            fieldName = sourceRecord.fieldName(fieldIdx)
            targetRecord.setValue(fieldName, sourceRecord.value(fieldName))


    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()

        column = index.column()
        row = index.row()
        actionId = self.idList()[row]
        record = self.recordCache().get(actionId)
        if role == Qt.DisplayRole and column == CExistsClientActionsModel.actionTypeNameColIndex:
            actionTypeId = forceRef(record.value('actionType_id'))
            if actionTypeId:
                outName = forceString(record.value('specifiedName'))
                actionType = CActionTypeCache.getById(actionTypeId)
                if actionType:
                    actionTypeName = u' | '.join([actionType.code, actionType.name])
                    outName = actionTypeName + ' ' + outName if outName else actionTypeName
                return QVariant(outName)
        if role == Qt.FontRole:
            if forceInt(record.value('status')) in (CActionStatus.started, CActionStatus.appointed):
                return self._qBoldFont
        return CTableModel.data(self, index, role)


# #########################################################

class CActionTypeGroupsTemplatesModel(CActionTypeGroupsModel):
    def __init__(self, parent):
        CActionTypeGroupsModel.__init__(self, parent, show_class=False)
        self.findFilterText = None
        self.templates_order = 'ActionTypeGroup.code ASC'
        self.last_class = None
        self.filter = u''
        self._type = 0


    def setFilter(self, filter):
        self.filter = filter


    def setFindFilterText(self, findFilterText):
        self.findFilterText = findFilterText
        self._loaded = False


    def canRemoveItem(self, itemId):
        result = QtGui.qApp.userHasRight(urCanDeleteForeignActionTypeGroup)
        if not result:
            record = self.getRecordById(itemId)
            if record:
                createPersonId = forceRef(record.value('createPerson_id'))
                result = QtGui.qApp.userId == createPersonId
        return result


    def setTemplatesOrder(self, order):
        self.templates_order = order
        self.reloadData()


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
        idList = db.getIdList(queryTable, 'ActionTypeGroup.id', cond, order=self.templates_order)
        self.setIdList(idList)
