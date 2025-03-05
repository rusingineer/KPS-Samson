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
##
## Складской учёт: Централизованный учет
##
#############################################################################
from PyQt4 import QtGui, QtSql, QtCore
from PyQt4.QtCore import Qt, pyqtSignature, QDate, QVariant, SIGNAL, QDateTime
from library.database         import CTableRecordCache
from Events.Action            import CAction, CActionTypeCache
from Events.ActionsModel      import CActionRecordItem, CGroupActionsProxyModelEx
from Events.ActionStatus      import CActionStatus
from library.DialogBase       import CDialogBase
from library.PrintInfo        import CInfoContext, CDateInfo
from Events.ActionInfo        import CActionTypeInfo, CActionInfoListEx, CActionTypeGroupInfo
from Events.EventInfo         import CCentralizedAccountingEventInfoList
from Events.Utils             import getEventMedicalAidKindId
from Events.NomenclatureExpense.UpdateDoseNomenclatureExpenseEditor import CUpdateDoseNomenclatureExpenseEditor
from Orgs.Utils               import COrgStructureInfo
from library.PrintTemplates   import CPrintAction, getPrintTemplates, applyTemplate
from Reports.ReportBase       import CReportBase, createTable
from Reports.ReportView       import CReportViewDialog
from library.RecordLock       import CRecordLockMixin
from library.TableModel       import CTextCol, CCol, CTableModel
from library.Utils            import formatName, toVariant, forceString, forceDate, forceBool, forceRef, formatRecordsCount, forceStringEx, forceInt, addDots, getPref, setPref
from Orgs.Utils               import getOrgStructureDescendants
from Registry.RegistryWindow  import convertFilterToTextItem, CIdValidator
from Registry.Utils           import CClientInfo
from Events.NomenclatureExpense.QueriesStatements import getNomenclatureActionTypesIds
from Stock.GroupClientInvoice import CGroupClientInvoice
from Users.Rights             import urNomenclatureExpenseLaterDate, urNoRestrictRetrospectiveNEClient

from Ui_CentralizedAccountingDialog import Ui_CentralizedAccountingDialog


class CCentralizedAccountingDialog(CDialogBase, CRecordLockMixin, Ui_CentralizedAccountingDialog):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        CRecordLockMixin.__init__(self)
        self.addModels('CentralizedAccounting', CCentralizedAccountingModel(self))
        self.addModels('Actions',               CGroupActionsProxyModelEx(self))
        self.setObjectName('CentralizedAccountingDialog')
        self.setupUi(self)
        self.setWindowFlags(Qt.Window | Qt.WindowSystemMenuHint | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
        self.setWindowState(Qt.WindowMaximized)
        self.setWindowTitle(u'Централизованный учёт')
        self.addObject('mnuActions', QtGui.QMenu(self))
        self.addObject('actCalculationDoseNomenclature', QtGui.QAction(u'Рассчитать дозу', self))
        self.actCalculationDoseNomenclature.setShortcut('F2')
        self.connect(self.actCalculationDoseNomenclature, SIGNAL('triggered()'), self.on_actCalculationDoseNomenclature_triggered)
        self.addObject('actUpdateDoseNomenclature', QtGui.QAction(u'Изменить дозу', self))
        self.actUpdateDoseNomenclature.setShortcut('F3')
        self.connect(self.actUpdateDoseNomenclature, SIGNAL('triggered()'), self.on_actUpdateDoseNomenclature_triggered)
        templates = getPrintTemplates(['CentralizedAccountingDialog'])
        if not templates:
            self.btnPrint.setId(-1)
        else:
            for template in templates:
                action = CPrintAction(template.name, template.id, self.btnPrint, self.btnPrint)
                self.btnPrint.addAction(action)
            self.btnPrint.menu().addSeparator()
            self.btnPrint.addAction(CPrintAction(u'Напечатать список', -1, self.btnPrint, self.btnPrint))
        self.tblActions.setCentralizedAccountingActionsPopupMenu(self.mnuActions)
        self.mnuActions.addActions([self.actCalculationDoseNomenclature, self.actUpdateDoseNomenclature])
        self.addObject('qshcCalculationDoseNomenclature', QtGui.QShortcut('F2', self.tblActions, self.on_actCalculationDoseNomenclature_triggered))
        self.qshcCalculationDoseNomenclature.setContext(Qt.WidgetShortcut)
        self.addObject('qshcUpdateDoseNomenclature', QtGui.QShortcut('F3', self.tblActions, self.on_actUpdateDoseNomenclature_triggered))
        self.qshcUpdateDoseNomenclature.setContext(Qt.WidgetShortcut)
        self.setModels(self.tblCentralizedAccounting, self.modelCentralizedAccounting, self.selectionModelCentralizedAccounting)
        self.setModels(self.tblActions, self.modelActions, self.selectionModelActions)
        self.hBedOSIdDict = {}
        self.idValidator = CIdValidator(self)
        self.edtClientId.setValidator(self.idValidator)
        self.edtFilterEventId.setValidator(self.idValidator)
        self.cmbFilterOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.setCmbActionTypeFilter()
        #self.cmbFilterStatus.setValue([CActionStatus.started, CActionStatus.appointed])
        self.chkFilterStatus.setChecked(True)
        self.cmbFilterSchema.setTable('ActionTypeGroup')
        self.updateSchemaItems()
        self.tblCentralizedAccounting.enableColsHide()
        self.tblCentralizedAccounting.enableColsMove()
        self.tblActions.enableColsHide()
        self.tblActions.enableColsMove()
        self.tblCentralizedAccounting.setEventEditor(self)
        self.eventCache = {}
        self.chkFilterActionType.setChecked(forceBool(QtGui.qApp.preferences.appPrefs.get('CCentralizedAccountingDialog_chkFilterActionType', False)))
        if self.chkFilterActionType.isChecked():
            self.cmbFilterActionType.setValue(forceRef(QtGui.qApp.preferences.appPrefs.get('CCentralizedAccountingDialog_cmbFilterActionType', None)))
        self.chkFilterStatus.setChecked(forceBool(QtGui.qApp.preferences.appPrefs.get('CCentralizedAccountingDialog_chkFilterStatus', False)))
        statusValue = [CActionStatus.started, CActionStatus.appointed]
        if self.chkFilterStatus.isChecked():
            status = QtGui.qApp.preferences.appPrefs.get('CCentralizedAccountingDialog_cmbFilterStatus', None)
            if status:
                statusValueTemp = []
                statusQVariantValues = status.toList()
                for statusQVariantValue in statusQVariantValues:
                    statusValueTemp.append(forceInt(statusQVariantValue))
                if statusValueTemp:
                    statusValue = statusValueTemp
        self.cmbFilterStatus.setValue(statusValue)
        self.chkFilterSchema.setChecked(forceBool(QtGui.qApp.preferences.appPrefs.get('CCentralizedAccountingDialog_chkFilterSchema', False)))
        if self.chkFilterSchema.isChecked():
            self.cmbFilterSchema.setValue(forceRef(QtGui.qApp.preferences.appPrefs.get('CCentralizedAccountingDialog_cmbFilterSchema', None)))
        self.on_buttonBoxFilter_apply()
#        self.setFocusProxy(self.grpTables)
        self.grpTables.setFocusProxy(self.tblCentralizedAccounting)
        #self.connect(self.tblCentralizedAccounting.horizontalHeader(), SIGNAL('sectionClicked(int)'), self._setSAOrderByColumn)
        #self.connect(self.modelActions, QtCore.SIGNAL('dataChanged(QModelIndex, QModelIndex)'), self.on_modelActions_dataChanged)
        self.edtFilterDate.connect(self.edtFilterDate.lineEdit, QtCore.SIGNAL('editingFinished()'), self.on_edtFilterDate_editingFinished)
        self.tblActions.loadPreferences(getPref(QtGui.qApp.preferences.windowPrefs, 'CCentralizedAccountingDialog_tblActions', {}))
        self.tblCentralizedAccounting.loadPreferences(getPref(QtGui.qApp.preferences.windowPrefs, 'CCentralizedAccountingDialog_tblCentralizedAccounting', {}))


    def closeEvent(self, event):
        QtGui.qApp.preferences.appPrefs['CCentralizedAccountingDialog_chkFilterActionType'] = toVariant(self.chkFilterActionType.isChecked())
        QtGui.qApp.preferences.appPrefs['CCentralizedAccountingDialog_cmbFilterActionType'] = toVariant(forceRef(self.cmbFilterActionType.value()) if self.chkFilterActionType.isChecked() else None)
        QtGui.qApp.preferences.appPrefs['CCentralizedAccountingDialog_chkFilterStatus'] = QVariant(self.chkFilterStatus.isChecked())
        QtGui.qApp.preferences.appPrefs['CCentralizedAccountingDialog_cmbFilterStatus'] = QVariant(self.cmbFilterStatus.value() if self.chkFilterStatus.isChecked() else [0, 5])
        QtGui.qApp.preferences.appPrefs['CCentralizedAccountingDialog_chkFilterSchema'] = toVariant(self.chkFilterSchema.isChecked())
        QtGui.qApp.preferences.appPrefs['CCentralizedAccountingDialog_cmbFilterSchema'] = toVariant(forceRef(self.cmbFilterSchema.value()) if self.chkFilterSchema.isChecked() else None)
        setPref(QtGui.qApp.preferences.windowPrefs, 'CCentralizedAccountingDialog_tblActions', self.tblActions.savePreferences())
        setPref(QtGui.qApp.preferences.windowPrefs, 'CCentralizedAccountingDialog_tblCentralizedAccounting', self.tblCentralizedAccounting.savePreferences())
        CDialogBase.closeEvent(self, event)


    def setCmbActionTypeFilter(self):
        db = QtGui.qApp.db
        table = db.table('ActionType')
        idList = getNomenclatureActionTypesIds()
        descendants = []
        for id in idList:
            descendants.extend(db.getDescendants(table, 'group_id', id))
        idList = db.getTheseAndParents(table, 'group_id', descendants)
        self.cmbFilterActionType.setEnabledActionTypeIdList(idList)


    def updateSchemaItems(self):
        schemaId = self.cmbFilterSchema.value()
        actionTypeId = self.cmbFilterActionType.value() if self.chkFilterActionType.isChecked() else None
        filter = u'0'
        templateIdList = []
        db = QtGui.qApp.db
        tableATG = db.table('ActionTypeGroup')
        tableATGItems = db.table('ActionTypeGroup_Item')
        if actionTypeId:
            queryTable = tableATG.innerJoin(tableATGItems, tableATGItems['master_id'].eq(tableATG['id']))
            templateIdList = db.getDistinctIdList(queryTable, [tableATG['id']], [tableATGItems['actionType_id'].eq(actionTypeId), tableATGItems['deleted'].eq(0), tableATG['deleted'].eq(0)], [tableATG['code'].name(), tableATG['name'].name()])
            if templateIdList:
                filter = tableATG['id'].inlist(templateIdList)
        else:
            enabledActionTypeIdList = self.cmbFilterActionType._model._enabledActionTypeIdList
            if enabledActionTypeIdList:
                queryTable = tableATG.innerJoin(tableATGItems, tableATGItems['master_id'].eq(tableATG['id']))
                templateIdList = db.getDistinctIdList(queryTable, [tableATG['id']], [tableATGItems['actionType_id'].inlist(enabledActionTypeIdList), tableATGItems['deleted'].eq(0), tableATG['deleted'].eq(0)], [tableATG['code'].name(), tableATG['name'].name()])
                if templateIdList:
                    filter = tableATG['id'].inlist(templateIdList)
        self.cmbFilterSchema.setTable(tableATG.name(), filter=filter)
        if self.chkFilterSchema.isChecked():
            self.cmbFilterSchema.setValue(schemaId)
        else:
            self.cmbFilterSchema.setValue(None)


    @pyqtSignature('int')
    def on_cmbFilterActionType_currentIndexChanged(self, index):
        self.updateSchemaItems()


    def _setSAOrderByColumn(self, column):
        self.tblCentralizedAccounting.setOrder(column)
        self.loadEvents()
        self.focusCentralizedAccountingList()


    def existsDoneByIndex(self, index):
        if index and index.isValid():
            row = index.row()
            if 0 <= row < len(self.modelActions._groups):
                group = self.modelActions._groups._mapProxyRow2Group[row]
                if group and row in group._mapProxyRow2ModelRow.keys():
                    proxyRow = group._mapProxyRow2ModelRow[row]
                    if proxyRow in group._mapRow2Item.keys():
                        record = group._mapRow2Item[proxyRow].record
                        return self.modelActions.existsDoneByIndex(group, forceDate(record.value('begDate')))
        return True


    def saveBeforeUpdate(self, action):
        if action:
            srcRecord = action.getRecord()
            clientId = None
            actionEventId = forceRef(srcRecord.value('event_id'))
            eventRecord = self.eventCache.get(actionEventId)
            if eventRecord:
                srcRecord.append(QtSql.QSqlField('eventType_id',  QVariant.Int))
                srcRecord.setValue('eventType_id', toVariant(forceRef(eventRecord.value('eventType_id'))))
                clientId = forceRef(eventRecord.value('client_id'))
            else:
                db = QtGui.qApp.db
                tableEvent = db.table('Event')
                eventRecord = db.getRecordEx(tableEvent, '*', [tableEvent['id'].eq(actionEventId), tableEvent['deleted'].eq(0)])
                if eventRecord:
                    srcRecord.append(QtSql.QSqlField('eventType_id',  QVariant.Int))
                    srcRecord.setValue('eventType_id', toVariant(forceRef(eventRecord.value('eventType_id'))))
                    clientId = forceRef(eventRecord.value('client_id'))
                    self.eventCache[actionEventId] = eventRecord
            if not clientId:
                return
            if self.getExecutionPlanIsDirty(action) and clientId:
                financeId = forceRef(srcRecord.value('finance_id'))
                medicalAidKindId = forceRef(srcRecord.value('medicalAidKind_id'))
                if not medicalAidKindId:
                    eventTypeId = forceRef(srcRecord.value('eventType_id'))
                    medicalAidKindId = getEventMedicalAidKindId(eventTypeId) if eventTypeId else None
                supplierId = forceRef(srcRecord.value('orgStructure_id'))
                if action.nomenclatureClientReservation is not None:
                    action.nomenclatureClientReservationCancel()
                nomenclatureId = action.findNomenclaturePropertyValue()
                if nomenclatureId and action.getType().isNomenclatureExpense:
                    action.initNomenclatureReservation(clientId, financeId=financeId, medicalAidKindId=medicalAidKindId, supplierId=supplierId, markToUpdate=True)
                    action.setNomenclatureClientReservationChange(True)
            record = self.removeExtCols(srcRecord)
            action._record = record
            action.save(idx=forceInt(action.getRecord().value('idx')))
            actionRecord = action.getRecord()
            actionRecord.append(QtSql.QSqlField('smnnUUID',  QVariant.String))
            actionRecord.setValue('smnnUUID', toVariant(action.getSmnnUUIDPropertyValue()))
            actionRecord.append(QtSql.QSqlField('smnnName',  QVariant.String))
            actionRecord.setValue('smnnName', toVariant(action.getSmnnUUIDPropertyText()))
            actionRecord.append(QtSql.QSqlField('lfForm_id',  QVariant.Int))
            actionRecord.setValue('lfForm_id', toVariant(action.getSmnnGrlsLfPropertyValue()))
            actionRecord.append(QtSql.QSqlField('lfFormName',  QVariant.String))
            actionRecord.setValue('lfFormName', toVariant(action.getSmnnGrlsLfPropertyText()))
            actionRecord.append(QtSql.QSqlField('nomenclature_id',  QVariant.Int))
            actionRecord.setValue('nomenclature_id', toVariant(action.findNomenclaturePropertyValue()))
            actionRecord.append(QtSql.QSqlField('actionPropertyTemplate_id',  QVariant.Int))
            actionRecord.setValue('actionPropertyTemplate_id', toVariant(action.getCalculationParamPropertyValue()))
            actionRecord.append(QtSql.QSqlField('signa',  QVariant.String))
            actionRecord.setValue('signa', toVariant(action.findSignaPropertyText()))
            actionRecord.append(QtSql.QSqlField('signaComment',  QVariant.String))
            actionRecord.setValue('signaComment', toVariant(action.findSignaCommentPropertyText()))
            actionRecord.append(QtSql.QSqlField('doses',  QVariant.String))
            actionRecord.setValue('doses', toVariant(action.findDosagePropertyValue()))
            actionRecord.append(QtSql.QSqlField('dosesName',  QVariant.String))
            actionRecord.setValue('dosesName', toVariant(action.getGroupDosesTextEx()))
            actionRecord.append(QtSql.QSqlField('finance_id',  QVariant.Int))
            actionRecord.setValue('finance_id', toVariant(forceRef(record.value('finance_id'))))
            actionRecord.append(QtSql.QSqlField('medicalAidKind_id',  QVariant.Int))
            actionRecord.setValue('medicalAidKind_id', toVariant(forceRef(record.value('medicalAidKind_id'))))
            actionRecord.append(QtSql.QSqlField('orgStructure_id',  QVariant.Int))
            actionRecord.setValue('orgStructure_id', toVariant(forceRef(record.value('orgStructure_id'))))
#           self.modelActions._items.mapGroup(row, CActionRecordItem(action.getRecord(), action))
#           self.modelActions.reset()
            self.modelActions.blockSignals(True)
            self.loadActions(forceRef(action.getRecord().value('event_id')))
            self.modelActions.blockSignals(False)
            self.setModelActionsProxyGroupExpanded()


    def isNomenclatureExpenseRight(self):
        begDate = self.edtFilterDate.date()
        if not begDate:
            return False
        isSelect = True
        currentDate = QDate.currentDate()
        if not QtGui.qApp.userHasRight(urNomenclatureExpenseLaterDate):
            isSelect = isSelect and begDate <= currentDate
        if not QtGui.qApp.userHasRight(urNoRestrictRetrospectiveNEClient):
            if QtGui.qApp.admissibilityNomenclatureExpensePostDates() == 1:
                isSelect = isSelect and begDate >= currentDate.addDays(-1)
            elif QtGui.qApp.admissibilityNomenclatureExpensePostDates() == 2:
                isSelect = isSelect and begDate >=  QDate(currentDate.year(), currentDate.month(), 1)
        return isSelect


    def hasItemsToDoActions(self):
        for group in self.modelActions._groups:
            if group:
                action = group.action
                if not action:
                    return False
                record = group.record
                if not record:
                    return False
                if forceInt(record.value('status')) in [CActionStatus.started, CActionStatus.appointed] and action.executionPlanManager.hasItemsToDo():
                    return True
        return False


    @pyqtSignature('')
    def on_actCalculationDoseNomenclature_triggered(self):
        templateIdList = {}
        if self.tblActions.isCentralizedAccountingActionsPopupMenuEnabled():
            selectedIndexes = self.tblActions.selectedIndexes()
            if selectedIndexes:
                selectedRows = []
                db = QtGui.qApp.db
                tableEvent = db.table('Event')
                for index in selectedIndexes:
                    if index and index.isValid():
                        row = index.row()
                        if 0 <= row < len(self.modelActions._groups) and row not in selectedRows: # and not self.existsDoneByIndex(index):
                            selectedRows.append(row)
                            group = self.modelActions._groups._mapProxyRow2Group[row]
                            if group:
                                proxyRow = group._mapProxyRow2ModelRow[row]
                                action = group._mapRow2Item[proxyRow].action
                                if not action:
                                    return
                                if not action.executionPlanManager.hasItemsToDo():
                                    return
                                recordAction = group._mapRow2Item[proxyRow].record
                                if not recordAction:
                                    return
                                clientId = None
                                eventId = forceRef(recordAction.value('event_id'))
                                if eventId:
                                    if self.lock(tableEvent.name(), eventId):
                                        try:
                                            eventRecord = self.eventCache.get(eventId)
                                            if eventRecord:
                                                clientId = forceRef(eventRecord.value('client_id'))
                                            else:
                                                eventRecord = db.getRecordEx(tableEvent, '*', [tableEvent['id'].eq(eventId), tableEvent['deleted'].eq(0)])
                                                if eventRecord:
                                                    clientId = forceRef(eventRecord.value('client_id'))
                                                    self.eventCache[eventId] = eventRecord
                                            if not clientId:
                                                return
                                            templateId = action.getCalculationParamPropertyValue()
                                            if templateId:
                                                items = action.getValuePropertyToTemplateItems()
                                                if not items:
                                                    items = self.modelActions.getCalculationParamValueProperties(clientId)
                                                    action.setValuePropertyToTemplateItems(items)
                                                paramLine = action.getValuePropertyToTemplate(templateId)
                                                calculationParam = paramLine[0] if len(paramLine) > 0 else 0
                                                if calculationParam > 0:
                                                    begDate = forceDate(recordAction.value('begDate'))
                                                    if not begDate:
                                                        return
                                                    group = self.modelActions.calculationDosageToDateByIndex(group, calculationParam, begDate)
                                                    if group._copiedFrom:
                                                        groupKeys = group._copiedFrom._mapRow2Item.keys()
                                                        groupKeys.sort()
                                                        for groupKey in groupKeys:
                                                            item = group._copiedFrom._mapRow2Item[groupKey]
                                                            if item.action.executionPlanManager.hasItemsToDo():
                                                                currentIndex = item.action.executionPlanManager.getCurrentItemIndex()
                                                                executionPlan = group._epGroup.getExecutionPlan()
                                                                item.action.executionPlanManager.setExecutionPlan(executionPlan, force=True)
                                                                item.action.executionPlanManager.setCurrentItemIndex(currentIndex)
                                                                item.action.executionPlanManager.bindAction(item.action)
                                                                if item.action.getType().isNomenclatureExpense:
                                                                    item.action.updateDosageFromExecutionPlan()
                                                                item.action.updateSpecifiedName()
                                                    else:
            #                                            action = group.headItem.action
            #                                            if action:
            #                                                if action.executionPlanManager.hasItemsToDo():
            #                                                    if action.getType().isNomenclatureExpense:
            #                                                        action.updateDosageFromExecutionPlan()
            #                                                    action.updateSpecifiedName()
                                                        if action.executionPlanManager.hasItemsToDo():
                                                            currentIndex = action.executionPlanManager.getCurrentItemIndex()
                                                            executionPlan = group._epGroup.getExecutionPlan()
                                                            action.executionPlanManager.setExecutionPlan(executionPlan, force=True)
                                                            action.executionPlanManager.setCurrentItemIndex(currentIndex)
                                                            action.executionPlanManager.bindAction(action)
                                                            if action.getType().isNomenclatureExpense:
                                                                action.updateDosageFromExecutionPlan()
                                                            action.updateSpecifiedName()
                                                    self.saveBeforeUpdate(action)
                                                    self.modelActions.emitRowDataChanged(row)
                                                    #self.modelActions.emitAllDataChanged()
                                                else:
                                                    nomenclatureList = templateIdList.get(templateId, [])
                                                    nomenclatureName = action.getNomenclaturePropertyText()
                                                    nomenclatureNameList = nomenclatureName.split(u'|')
                                                    nomenclatureNameStr = nomenclatureNameList[0]
                                                    nomenclatureList.append(nomenclatureNameStr if nomenclatureNameStr else action.getSmnnUUIDPropertyText())
                                                    templateIdList[templateId] = nomenclatureList
                                        finally:
                                            self.releaseLock()
        if templateIdList:
            templateNameList = {}
            message = u''
            db = QtGui.qApp.db
            tableAPT = db.table('ActionPropertyTemplate')
            records = db.getDistinctRecordList(tableAPT, [tableAPT['id'], tableAPT['name']], [tableAPT['id'].inlist(templateIdList.keys())], order = tableAPT['name'].name())
            for record in records:
                templateNameList[forceRef(record.value('id'))] = forceString(record.value('name'))
            for templateId, nomenclatureNameList in templateIdList.items():
                nomenclatureNames = u'<br>'.join(nomenclatureName for nomenclatureName in nomenclatureNameList)
                message += u'''Невозможно рассчитать дозу для ЛС:<br><b>%s</b><br>в связи с тем, что не определено значение параметра расчета <b>%s</b> для пациента.<br><br>'''%(nomenclatureNames, templateNameList.get(templateId, u''))
            if message:
                button = QtGui.QMessageBox.Ok
                QtGui.QMessageBox.warning(None,
                                          u'Внимание!',
                                          message,
                                          button,
                                          QtGui.QMessageBox.Ok)
        self.focusCentralizedAccountingList()


    @pyqtSignature('')
    def on_actUpdateDoseNomenclature_triggered(self):
        if self.tblActions.isCentralizedAccountingActionsPopupMenuEnabled():
            db = QtGui.qApp.db
            tableEvent = db.table('Event')
            selectedIndexes = self.tblActions.selectedIndexes()
            if selectedIndexes:
                procent = 0
                change = 0
                dialog = CUpdateDoseNomenclatureExpenseEditor(self)
                try:
                    if dialog.exec_():
                        params = dialog.getProcentParams()
                        procent = params.get('procent', 0)
                        change = params.get('change', 0)
                finally:
                    dialog.deleteLater()
                if procent > 0 and change > 0:
                    selectedRows = []
                    for index in self.tblActions.selectedIndexes():
                        if index and index.isValid():
                            row = index.row()
                            if 0 <= row < len(self.modelActions._groups) and row not in selectedRows: # and not self.existsDoneByIndex(index):
                                selectedRows.append(row)
                                group = self.modelActions._mapProxyRow2Group[row]
                                if group:
                                    proxyRow = group._mapProxyRow2ModelRow[row]
                                    action = group._mapRow2Item[proxyRow].action
                                    if not action:
                                        return
                                    if not action.executionPlanManager.hasItemsToDo():
                                        return
                                    recordAction = group._mapRow2Item[proxyRow].record
                                    if not recordAction:
                                        return
                                    eventId = forceRef(recordAction.value('event_id'))
                                    if eventId:
                                        if self.lock(tableEvent.name(), eventId):
                                            try:
                                                begDate = forceDate(recordAction.value('begDate'))
                                                if not begDate:
                                                    return
                                                group = self.modelActions.updateDosageToDateToProcentByIndex(group, procent, change, begDate)
                                                if group._copiedFrom:
                                                    groupKeys = group._copiedFrom._mapRow2Item.keys()
                                                    groupKeys.sort()
                                                    for groupKey in groupKeys:
                                                        item = group._copiedFrom._mapRow2Item[groupKey]
                                                        if item.action.executionPlanManager.hasItemsToDo():
                                                            currentIndex = item.action.executionPlanManager.getCurrentItemIndex()
                                                            executionPlan = group._epGroup.getExecutionPlan()
                                                            item.action.executionPlanManager.setExecutionPlan(executionPlan, force=True)
                                                            item.action.executionPlanManager.setCurrentItemIndex(currentIndex)
                                                            item.action.executionPlanManager.bindAction(item.action)
                                                            if item.action.getType().isNomenclatureExpense:
                                                                item.action.updateDosageFromExecutionPlan()
                                                            item.action.updateSpecifiedName()
                                                else:
            #                                        action = group.headItem.action
            #                                        if action:
            #                                            if action.executionPlanManager.hasItemsToDo():
            #                                                if action.getType().isNomenclatureExpense:
            #                                                    action.updateDosageFromExecutionPlan()
            #                                                action.updateSpecifiedName()
                                                    if action.executionPlanManager.hasItemsToDo():
                                                        currentIndex = action.executionPlanManager.getCurrentItemIndex()
                                                        executionPlan = group._epGroup.getExecutionPlan()
                                                        action.executionPlanManager.setExecutionPlan(executionPlan, force=True)
                                                        action.executionPlanManager.setCurrentItemIndex(currentIndex)
                                                        action.executionPlanManager.bindAction(action)
                                                        if action.getType().isNomenclatureExpense:
                                                            action.updateDosageFromExecutionPlan()
                                                        action.updateSpecifiedName()
                                                self.saveBeforeUpdate(action)
                                                self.modelActions.emitRowDataChanged(row)
                                                #self.modelActions.emitAllDataChanged()
                                            finally:
                                                self.releaseLock()
        self.focusCentralizedAccountingList()


    def setModelActionsProxyGroupExpanded(self):
        self.modelActions.blockSignals(True)
        for row, group in self.modelActions._mapProxyRow2Group.items():
            group.setExpanded(True)
            self.modelActions._resetData()
        self.modelActions.blockSignals(False)


    def setModelActionsGroupExpanded(self):
        self.modelActions.blockSignals(True)
        for row, group in self.modelActions._mapProxyRow2Group.items():
            if not self.modelActions.getExpandedByRow(row):
                group.setExpanded(not group.expanded)
                self.modelActions._resetData()
        self.modelActions.blockSignals(False)


    @pyqtSignature('int')
    def on_btnPrint_printByTemplate(self, templateId):
        if templateId == -1:
            doc = QtGui.QTextDocument()
            cursor = QtGui.QTextCursor(doc)
            cursor.setCharFormat(CReportBase.ReportTitle)
            cursor.insertText(u'Централизованный учёт')
            cursor.setCharFormat(CReportBase.ReportBody)
            cursor.insertBlock()
            self.dumpParams(cursor)
            cursor.insertBlock()
            model = self.tblCentralizedAccounting.model()
            colWidths  = [self.tblCentralizedAccounting.columnWidth(i) for i in xrange(model.columnCount())]
            totalWidth = sum(colWidths)
            tableColumns = []
            for iCol, colWidth in enumerate(colWidths):
                widthInPercents = str(max(1, colWidth*90/totalWidth)) + '%'
                tableColumns.append((widthInPercents, [forceString(model._cols[iCol].title())], CReportBase.AlignLeft))
            table = createTable(cursor, tableColumns)
            for iModelRow in xrange(model.rowCount()):
                iTableRow = table.addRow()
                for iModelCol in xrange(model.columnCount()):
                    index = model.createIndex(iModelRow, iModelCol)
                    text = forceString(model.data(index))
                    table.setText(iTableRow, iModelCol, text)
            cursor.movePosition(QtGui.QTextCursor.End)
            cursor.insertBlock()
            cursor.insertBlock()
            cursor.setCharFormat(CReportBase.ReportSubTitle)
            cursor.setCharFormat(CReportBase.ReportBody)
            model = self.tblActions.model()
            colWidths  = [self.tblActions.columnWidth(i) for i in xrange(model.columnCount())]
            totalWidth = sum(colWidths)
            tableColumns = []
            for iCol, colWidth in enumerate(colWidths):
                widthInPercents = str(max(1, colWidth*90/totalWidth)) + '%'
                tableColumns.append((widthInPercents, [forceString(model._cols[iCol].title())], CReportBase.AlignLeft))
            table = createTable(cursor, tableColumns)
            for iModelRow in xrange(model.rowCount()):
                iTableRow = table.addRow()
                for iModelCol in xrange(model.columnCount()):
                    index = model.createIndex(iModelRow, iModelCol)
                    text = forceString(model.data(index))
                    table.setText(iTableRow, iModelCol, text)
            cursor.movePosition(QtGui.QTextCursor.End)
            html = doc.toHtml('utf-8')
            view = CReportViewDialog(self)
            view.setText(html)
            view.exec_()
        else:
            selectedEventIdList = []
            actionIdList = []
            eventIdList = self.tblCentralizedAccounting.model().idList()
            selectedRows = []
            rowCount = self.tblCentralizedAccounting.model().rowCount()
            for index in self.tblCentralizedAccounting.selectedIndexes():
                if index.row() < rowCount:
                    row = index.row()
                    if row not in selectedRows:
                        selectedRows.append(row)
            for selectedRow in selectedRows:
                if selectedRow >= 0 and selectedRow < len(eventIdList):
                    eventId = eventIdList[selectedRow]
                    if eventId and eventId not in selectedEventIdList:
                        selectedEventIdList.append(eventId)
            if len(selectedEventIdList) == 1 and selectedEventIdList[0]:
                items = self.modelActions.items()
                for item in items:
                    rec = item[0]
                    actionId = forceRef(rec.value('id'))
                    if actionId and actionId not in actionIdList:
                        actionIdList.append(actionId)
            context = CInfoContext()
            eventList = context.getInstance(CCentralizedAccountingEventInfoList, eventIdList, isExecutionPlan=True, hBedOSIdDict=self.hBedOSIdDict, isSelected=False)
            selectedEventList = context.getInstance(CCentralizedAccountingEventInfoList, selectedEventIdList, isExecutionPlan=True, hBedOSIdDict=self.hBedOSIdDict, isSelected=True)
            actionList = context.getInstance(CActionInfoListEx, actionIdList, isExecutionPlan=True)
            actionTypeId = forceRef(self.cmbFilterActionType.value()) if self.chkFilterActionType.isChecked() else None
            filterActionType = CActionTypeCache.getById(actionTypeId)
            data = {'filterDate': CDateInfo(self.edtFilterDate.date()),
                    'filterActionType': context.getInstance(CActionTypeInfo, filterActionType),
                    'filterStatus': self.cmbFilterStatus.value() if self.chkFilterStatus.isChecked() else [0, 5],
                    'filterSchema': context.getInstance(CActionTypeGroupInfo, forceRef(self.cmbFilterSchema.value()) if self.chkFilterSchema.isChecked() else None),
                    'filterOrgStructure': context.getInstance(COrgStructureInfo, forceRef(self.cmbFilterOrgStructure.value()) if self.chkFilterOrgStructure.isChecked() else None),
                    'filterClient': context.getInstance(CClientInfo, forceRef(QVariant(self.edtClientId.text())) if self.chkClientId.isChecked() else None),
                    'filterLastName': forceStringEx(self.edtFilterLastName.text()) if self.chkFilterLastName.isChecked() else '',
                    'filterFirstName': forceStringEx(self.edtFilterFirstName.text()) if self.chkFilterFirstName.isChecked() else '',
                    'filterPatrName': forceStringEx(self.edtFilterPatrName.text()) if self.chkFilterPatrName.isChecked() else '',
                    'filterEventId': forceStringEx(self.edtFilterEventId.text()) if self.chkFilterEventId.isChecked() else '',
                    'filterExternalId': forceStringEx(self.edtFilterExternalId.text()) if self.chkFilterExternalId.isChecked() else '',
                    'events' : eventList,
                    'selectedEvents':selectedEventList,
                    'actions' : actionList
                    }
            QtGui.qApp.call(self, applyTemplate, (self, templateId, data))
        self.focusCentralizedAccountingList()


    def dumpParams(self, cursor):
        description = []
        description.append(self.getCentralizedAccountingFilterAsText() + u'\nОтчёт составлен: ' + forceString(QDateTime.currentDateTime()))
        columns = [ ('100%', [], CReportBase.AlignLeft) ]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()


    def getCentralizedAccountingFilterAsText(self):
        db = QtGui.qApp.db
        filter  = self.filter
        resList = []
        tmpList = [
            ('date',  u'Дата', forceString),
            ('actionTypeId', u'Тип действия',
                lambda id: forceString(db.translate('ActionType', 'id', id, 'name'))),
            ('status', u'Статус', lambda i: u','.join(CActionStatus.names[j] for j in i if (j is not None or j >= 0))),
            ('schemaId', u'Схема',
                lambda id: forceString(db.translate('ActionTypeGroup', 'id', id, 'name'))),
            ('orgStructureId', u'Подразделение пребывания',
                lambda id: forceString(db.translate('OrgStructure', 'id', id, 'name'))),
            ('clientId',  u'Код пациента', forceString),
            ('lastName',  u'Фамилия', forceString),
            ('firstName', u'Имя', forceString),
            ('patrName',  u'Отчество', forceString),
            ('eventId',   u'Код карточки', forceString),
            ('externalId',u'Карта', forceString),
            ]
        for (x, y, z) in tmpList:
            convertFilterToTextItem(resList, filter, x, y, z)
        return '\n'.join([': '.join(item) for item in resList])


#    def update(self):
#        self.loadEvents()
#        super(CCentralizedAccountingDialog, self).update()


    def focusCentralizedAccountingList(self):
        self.tblCentralizedAccounting.setFocus(Qt.TabFocusReason)


    def on_buttonBoxFilter_apply(self):
        self.filter = {}
        self.filter['date'] = self.edtFilterDate.date()
        if self.chkFilterActionType.isChecked():
            self.filter['actionTypeId'] = self.cmbFilterActionType.value()
        if self.chkFilterStatus.isChecked():
            self.filter['status'] = self.cmbFilterStatus.value()
        if self.chkFilterSchema.isChecked():
            self.filter['schemaId'] = self.cmbFilterSchema.value()
        self.filter['isSchema'] = self.chkFilterSchema.isChecked()
        if self.chkFilterOrgStructure.isChecked():
            self.filter['orgStructureId'] = self.cmbFilterOrgStructure.value()
        if self.chkClientId.isChecked():
            self.filter['clientId'] = forceStringEx(self.edtClientId.text())
        else:
            if self.chkFilterLastName.isChecked():
                self.filter['lastName'] = forceStringEx(self.edtFilterLastName.text())
            if self.chkFilterFirstName.isChecked():
                self.filter['firstName'] = forceStringEx(self.edtFilterFirstName.text())
            if self.chkFilterPatrName.isChecked():
                self.filter['patrName'] = forceStringEx(self.edtFilterPatrName.text())
        if self.chkFilterEventId.isChecked():
            self.filter['eventId'] = self.edtFilterEventId.text()
        if self.chkFilterExternalId.isChecked():
            self.filter['externalId'] = self.edtFilterExternalId.text()
        self.loadEvents()
        self.updateCentralizedAccounting()


    def on_buttonBoxFilter_reset(self):
        widgetIndex = self.tabFilter.currentIndex()
        if widgetIndex == 0:
            self.edtFilterDate.setDate(QDate.currentDate())
            self.chkFilterActionType.setChecked(False)
            self.cmbFilterActionType.setValue(None)
            self.cmbFilterStatus.setValue([CActionStatus.started, CActionStatus.appointed])
            self.chkFilterStatus.setChecked(True)
            self.chkFilterSchema.setChecked(False)
            self.cmbFilterSchema.setValue(None)
            self.chkFilterOrgStructure.setChecked(False)
            self.cmbFilterOrgStructure.setValue(None)
        elif widgetIndex == 1:
            self.chkClientId.setChecked(False)
            self.edtClientId.setText('')
            self.chkFilterLastName.setChecked(False)
            self.edtFilterLastName.setText('')
            self.chkFilterFirstName.setChecked(False)
            self.edtFilterFirstName.setText('')
            self.chkFilterPatrName.setChecked(False)
            self.edtFilterPatrName.setText('')
            self.chkFilterEventId.setChecked(False)
            self.edtFilterEventId.setText('')
            self.chkFilterExternalId.setChecked(False)
            self.edtFilterExternalId.setText('')
        self.on_buttonBoxFilter_apply()


    @pyqtSignature('QModelIndex')
    def on_tblCentralizedAccounting_doubleClicked(self, index):
        self.focusCentralizedAccountingList()


    def on_edtFilterDate_editingFinished(self):
        self.on_buttonBoxFilter_apply()


    @pyqtSignature('')
    def on_btnClose_clicked(self):
        self.close()


    @pyqtSignature('')
    def on_btnInvoices_clicked(self):
        actionIdList = []
        if self.isNomenclatureExpenseRight():
            actionIds = []
            clientIds = []
            orgStructureIds = []
            selectedRows = []
            rowCount = self.modelCentralizedAccounting.rowCount()
            for index in self.tblCentralizedAccounting.selectedIndexes():
                if index.row() < rowCount:
                    row = index.row()
                    if row not in selectedRows:
                        selectedRows.append(row)
            eventIdList = self.modelCentralizedAccounting.idList()
            for selectedRow in selectedRows:
                if selectedRow >= 0 and selectedRow < len(eventIdList):
                    eventId = eventIdList[selectedRow]
                    if eventId:
                        orgStructureId = self.cmbFilterOrgStructure.value() if self.chkFilterOrgStructure.isChecked() else None
                        db = QtGui.qApp.db
                        tableEvent = db.table('Event')
                        record = db.getRecordEx(tableEvent, [tableEvent['client_id']], [tableEvent['id'].eq(eventId), tableEvent['deleted'].eq(0)])
                        clientId = forceRef(record.value('client_id')) if record else None
                        if clientId:
                            actionIdList, orgStructureIdList = self.getActionIdList(eventId)
                            if actionIdList:
                                actionIds.extend(actionIdList)
                                clientIds.append(clientId)
                                if orgStructureIdList:
                                    orgStructureIds.extend(orgStructureIdList)
            clientInvoices = CGroupClientInvoice(orgStructureId, self, isControlPageVisible=False)
            try:
                date = self.filter.get('date', None)
                if date:
                    clientInvoices.setFilterDate(date)
                clientInvoices.setDateParams()
                if not orgStructureIds:
                    orgStructureIds = [QtGui.qApp.currentOrgStructureId()]
                clientInvoices.load(clientIds=clientIds, actionIds=actionIds, orgStructureId=orgStructureIds)
                clientInvoices.setRefreshParams(clientIds=clientIds, orgStructureId=orgStructureIds, date=date)
                clientInvoices.exec_()
            finally:
                    clientInvoices.deleteLater()
        if actionIdList:
            self.on_buttonBoxFilter_apply()
        else:
            self.focusCentralizedAccountingList()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelCentralizedAccounting_currentRowChanged(self, current, previous):
        self.updateCentralizedAccounting()


    def updateCentralizedAccounting(self):
        selectedRows = []
        rowCount = self.tblCentralizedAccounting.model().rowCount()
        for index in self.tblCentralizedAccounting.selectedIndexes():
            if index.row() < rowCount:
                row = index.row()
                if row not in selectedRows:
                    selectedRows.append(row)
        if len(selectedRows) > 1:
            self.loadActions(None)
            self.btnInvoices.setEnabled(len(selectedRows) > 0 and self.isNomenclatureExpenseRight() and self.getActionsToEvents(selectedRows))
        else:
            self.loadActions(self.tblCentralizedAccounting.currentItemId())
            self.btnInvoices.setEnabled(len(selectedRows) > 0 and self.isNomenclatureExpenseRight() and self.hasItemsToDoActions())
        self.setModelActionsProxyGroupExpanded()
        self.focusCentralizedAccountingList()


    @pyqtSignature('QItemSelection, QItemSelection')
    def on_selectionModelCentralizedAccounting_selectionChanged(self, selected, deselected):
        currentEventId = self.tblCentralizedAccounting.currentItemId()
        if not selected.indexes() and len(deselected.indexes()) > 0:
            if currentEventId:
                self.loadActions(currentEventId)
                self.setModelActionsProxyGroupExpanded()
                self.btnInvoices.setEnabled(len(self.modelActions.items()) > 0 and self.isNomenclatureExpenseRight() and self.hasItemsToDoActions())
                self.tblCentralizedAccounting.setCurrentItemId(currentEventId)
            else:
                self.tblCentralizedAccounting.setCurrentRow(0)
#                return
        elif len(selected.indexes()) > 0:
            selectedRows = []
            rowCount = self.tblCentralizedAccounting.model().rowCount()
            for index in self.tblCentralizedAccounting.selectedIndexes():
                if index.row() < rowCount:
                    row = index.row()
                    if row not in selectedRows:
                        selectedRows.append(row)
            if len(selectedRows) > 1:
                self.loadActions(None)
                self.setModelActionsProxyGroupExpanded()
                self.btnInvoices.setEnabled(len(selectedRows) > 0 and self.isNomenclatureExpenseRight() and self.getActionsToEvents(selectedRows))
                #self.btnInvoices.setEnabled(False)
            else:
                self.btnInvoices.setEnabled(len(selectedRows) > 0 and self.isNomenclatureExpenseRight() and self.hasItemsToDoActions())
        self.focusCentralizedAccountingList()


    def removeExtCols(self, srcRecord):
        db = QtGui.qApp.db
        tableAction = db.table('Action')
        record = tableAction.newRecord()
        for i in xrange(record.count()):
            record.setValue(i, srcRecord.value(record.fieldName(i)))
        return record


    def getExecutionPlanIsDirty(self, action):
        if action:
            executionPlan = action.getExecutionPlan()
            if executionPlan:
                items = executionPlan.items
                for item in items:
                    if item.getIsDirty():
                        return True
        return False


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelActions_dataChanged(self, topLeft, bottomRight):
        index = self.tblActions.currentIndex()
        if index.isValid():
            db = QtGui.qApp.db
            tableEvent = db.table('Event')
            column = index.column()
            if column in (self.modelActions.Col_Nomenclature, self.modelActions.Col_Doses):
                items = self.modelActions.items()
                row = index.row()
                if row >= 0 and len(items) > row:
                    action = items[row][1]
                    if action:
                        srcRecord = action.getRecord()
                        clientId = None
                        actionEventId = forceRef(srcRecord.value('event_id'))
                        if actionEventId:
                            if self.lock(tableEvent.name(), actionEventId):
                                try:
                                    eventRecord = self.eventCache.get(actionEventId)
                                    if eventRecord:
                                        srcRecord.append(QtSql.QSqlField('eventType_id',  QVariant.Int))
                                        srcRecord.setValue('eventType_id', toVariant(forceRef(eventRecord.value('eventType_id'))))
                                        clientId = forceRef(eventRecord.value('client_id'))
                                    else:
                                        eventRecord = db.getRecordEx(tableEvent, '*', [tableEvent['id'].eq(actionEventId), tableEvent['deleted'].eq(0)])
                                        if eventRecord:
                                            srcRecord.append(QtSql.QSqlField('eventType_id',  QVariant.Int))
                                            srcRecord.setValue('eventType_id', toVariant(forceRef(eventRecord.value('eventType_id'))))
                                            clientId = forceRef(eventRecord.value('client_id'))
                                            self.eventCache[actionEventId] = eventRecord
                                    if not clientId:
                                        self.focusCentralizedAccountingList()
                                        return
                                    if self.getExecutionPlanIsDirty(action) and clientId:
                                        financeId = forceRef(srcRecord.value('finance_id'))
                                        medicalAidKindId = forceRef(srcRecord.value('medicalAidKind_id'))
                                        if not medicalAidKindId:
                                            eventTypeId = forceRef(srcRecord.value('eventType_id'))
                                            medicalAidKindId = getEventMedicalAidKindId(eventTypeId) if eventTypeId else None
                                        supplierId = forceRef(srcRecord.value('orgStructure_id'))
                                        if action.nomenclatureClientReservation is not None:
                                            action.nomenclatureClientReservationCancel()
                                        nomenclatureId = action.findNomenclaturePropertyValue()
                                        if nomenclatureId and action.getType().isNomenclatureExpense:
                                            action.initNomenclatureReservation(clientId, financeId=financeId, medicalAidKindId=medicalAidKindId, supplierId=supplierId, markToUpdate=True)
                                            action.setNomenclatureClientReservationChange(True)
                                    record = self.removeExtCols(srcRecord)
                                    action._record = record
                                    action.save(idx=forceInt(action.getRecord().value('idx')))
                                    actionRecord = action.getRecord()
                                    actionRecord.append(QtSql.QSqlField('smnnUUID',  QVariant.String))
                                    actionRecord.setValue('smnnUUID', toVariant(action.getSmnnUUIDPropertyValue()))
                                    actionRecord.append(QtSql.QSqlField('smnnName',  QVariant.String))
                                    actionRecord.setValue('smnnName', toVariant(action.getSmnnUUIDPropertyText()))
                                    actionRecord.append(QtSql.QSqlField('lfForm_id',  QVariant.Int))
                                    actionRecord.setValue('lfForm_id', toVariant(action.getSmnnGrlsLfPropertyValue()))
                                    actionRecord.append(QtSql.QSqlField('lfFormName',  QVariant.String))
                                    actionRecord.setValue('lfFormName', toVariant(action.getSmnnGrlsLfPropertyText()))
                                    actionRecord.append(QtSql.QSqlField('nomenclature_id',  QVariant.Int))
                                    actionRecord.setValue('nomenclature_id', toVariant(action.findNomenclaturePropertyValue()))
                                    actionRecord.append(QtSql.QSqlField('actionPropertyTemplate_id',  QVariant.Int))
                                    actionRecord.setValue('actionPropertyTemplate_id', toVariant(action.getCalculationParamPropertyValue()))
                                    actionRecord.append(QtSql.QSqlField('signa',  QVariant.String))
                                    actionRecord.setValue('signa', toVariant(action.findSignaPropertyText()))
                                    actionRecord.append(QtSql.QSqlField('signaComment',  QVariant.String))
                                    actionRecord.setValue('signaComment', toVariant(action.findSignaCommentPropertyText()))
                                    actionRecord.append(QtSql.QSqlField('doses',  QVariant.String))
                                    actionRecord.setValue('doses', toVariant(action.findDosagePropertyValue()))
                                    actionRecord.append(QtSql.QSqlField('dosesName',  QVariant.String))
                                    actionRecord.setValue('dosesName', toVariant(action.getGroupDosesTextEx()))
                                    actionRecord.append(QtSql.QSqlField('finance_id',  QVariant.Int))
                                    actionRecord.setValue('finance_id', toVariant(forceRef(record.value('finance_id'))))
                                    actionRecord.append(QtSql.QSqlField('medicalAidKind_id',  QVariant.Int))
                                    actionRecord.setValue('medicalAidKind_id', toVariant(forceRef(record.value('medicalAidKind_id'))))
                                    actionRecord.append(QtSql.QSqlField('orgStructure_id',  QVariant.Int))
                                    actionRecord.setValue('orgStructure_id', toVariant(forceRef(record.value('orgStructure_id'))))
                                    self.modelActions.blockSignals(True)
                                    self.loadActions(forceRef(action.getRecord().value('event_id')))
                                    self.modelActions.blockSignals(False)
                                    self.setModelActionsProxyGroupExpanded()
                                    self.modelActions.reset()
                                finally:
                                    self.releaseLock()
        #self.focusCentralizedAccountingList()


    @pyqtSignature('')
    def on_tblCentralizedAccounting_popupMenuAboutToShow(self):
        self.focusCentralizedAccountingList()


    @pyqtSignature('bool')
    def on_chkFilterBirthDay_toggled(self, value):
        self.edtFilterEndBirthDay.setEnabled(value and self.chkFilterEndBirthDay.isChecked())


    @pyqtSignature('bool')
    def on_chkFilterActionType_toggled(self, value):
        self.updateSchemaItems()


    @pyqtSignature('bool')
    def on_chkClientId_toggled(self, value):
        if value:
            self.chkFilterLastName.setChecked(False)
            self.edtFilterLastName.setText('')
            self.chkFilterFirstName.setChecked(False)
            self.edtFilterFirstName.setText('')
            self.chkFilterPatrName.setChecked(False)
            self.edtFilterPatrName.setText('')
        self.chkFilterLastName.setEnabled(not value)
        self.chkFilterFirstName.setEnabled(not value)
        self.chkFilterPatrName.setEnabled(not value)


    @pyqtSignature('QAbstractButton*')
    def on_buttonBoxFilter_clicked(self, button):
        buttonCode = self.buttonBoxFilter.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.on_buttonBoxFilter_apply()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_buttonBoxFilter_reset()
        self.focusCentralizedAccountingList()


    def getActionIdList(self, eventId):
        actionIdList = []
        orgStructureIdList = []
        if eventId:
            currentOrgStructureId = QtGui.qApp.currentOrgStructureId()
            date = self.filter.get('date', None)
            actionTypeId = self.filter.get('actionTypeId', None)
            status = self.filter.get('status', None)
            isSchema = self.filter.get('isSchema', False)
            schemaId = self.filter.get('schemaId', None)
            #orgStructureId = self.filter.get('orgStructureId', None)
            db = QtGui.qApp.db
            tableAction = db.table('Action')
            tableActionType = db.table('ActionType')
            tableAXI = db.table('ActionExecutionPlan_Item')
            queryTable = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
#            queryTable = queryTable.leftJoin(tableAXI, db.joinAnd([tableAXI['action_id'].eq(tableAction['id']), tableAXI['executedDatetime'].isNull()]))
            queryTable = queryTable.leftJoin(tableAXI, tableAXI['action_id'].eq(tableAction['id']))
            cond = [tableAction['deleted'].eq(0),
                    tableAction['event_id'].eq(eventId),
                    tableActionType['deleted'].eq(0),
                    db.joinOr([tableActionType['isDoesNotInvolveExecutionCourse'].eq(1), tableAXI['id'].isNotNull()])
                    ]
            if date:
                cond.append(tableAction['begDate'].dateEq(date))
            if actionTypeId:
                cond.append(tableAction['actionType_id'].eq(actionTypeId))
            if status:
                cond.append(tableAction['status'].inlist(status))
            if isSchema:
                cond.append(tableAction['actionTypeGroup_id'].isNotNull())
                if schemaId:
                    cond.append(tableAction['actionTypeGroup_id'].eq(schemaId))
            if currentOrgStructureId:
                cond.append(tableAction['orgStructure_id'].eq(currentOrgStructureId))
            records = db.getRecordList(queryTable, 'Action.*', cond, order=[tableAction['idx'].name(), tableAction['id'].name()])
            for record in records:
                actionId = forceRef(record.value('id'))
                if actionId and actionId not in actionIdList:
                    actionIdList.append(actionId)
                    action = CAction(record=record)
                    actionRecord = action.getRecord()
                    actionOrgStructureId = forceRef(actionRecord.value('orgStructure_id')) if actionRecord else None
                    if actionOrgStructureId and actionOrgStructureId not in orgStructureIdList:
                        orgStructureIdList.append(actionOrgStructureId)
        return actionIdList, orgStructureIdList


    def getActionsToEvents(self, selectedRows):
        records = None
        selectedEventIdList = []
        eventIdList = self.modelCentralizedAccounting.idList()
        for selectedRow in selectedRows:
            if selectedRow >= 0 and selectedRow < len(eventIdList):
                eventId = eventIdList[selectedRow]
                if eventId and eventId not in selectedEventIdList:
                    selectedEventIdList.append(eventId)
        if selectedEventIdList:
            currentOrgStructureId = QtGui.qApp.currentOrgStructureId()
            date = self.filter.get('date', None)
            actionTypeId = self.filter.get('actionTypeId', None)
            status = self.filter.get('status', None)
            isSchema = self.filter.get('isSchema', False)
            schemaId = self.filter.get('schemaId', None)
            #orgStructureId = self.filter.get('orgStructureId', None)
            db = QtGui.qApp.db
            tableAction = db.table('Action')
            tableActionType = db.table('ActionType')
            tableAX = db.table('ActionExecutionPlan')
            tableAXI = db.table('ActionExecutionPlan_Item')
            tableEvent = db.table('Event')
            queryTable = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
            queryTable = queryTable.innerJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
#            queryTable = queryTable.leftJoin(tableAXI, db.joinAnd([tableAXI['action_id'].eq(tableAction['id']), tableAXI['executedDatetime'].isNull()]))
            queryTable = queryTable.leftJoin(tableAXI, tableAXI['action_id'].eq(tableAction['id']))
            queryTable = queryTable.leftJoin(tableAX, db.joinAnd([tableAX['id'].eq(tableAXI['master_id']), tableAX['deleted'].eq(0)]))
            cond = [tableAction['deleted'].eq(0),
                    tableEvent['deleted'].eq(0),
                    tableAction['event_id'].inlist(selectedEventIdList),
                    tableAction['status'].inlist([CActionStatus.started, CActionStatus.appointed]),
                    tableActionType['deleted'].eq(0),
                    db.joinOr([tableActionType['isDoesNotInvolveExecutionCourse'].eq(1), db.joinAnd([tableAXI['id'].isNotNull(), tableAX['deleted'].eq(0)])])
                    ]
            if date:
                cond.append(tableAction['begDate'].dateEq(date))
            if actionTypeId:
                cond.append(tableAction['actionType_id'].eq(actionTypeId))
            if status:
                cond.append(tableAction['status'].inlist(status))
            if isSchema:
                cond.append(tableAction['actionTypeGroup_id'].isNotNull())
                if schemaId:
                    cond.append(tableAction['actionTypeGroup_id'].eq(schemaId))
            if currentOrgStructureId:
                cond.append(tableAction['orgStructure_id'].eq(currentOrgStructureId))
            records = db.getRecordList(queryTable, 'Action.*', cond, order=[tableAction['idx'].name(), tableAction['id'].name()])
        return (len(records) > 0) if records else False


    def loadActions(self, eventId):
        items = []
        if eventId:
            currentOrgStructureId = QtGui.qApp.currentOrgStructureId()
            date = self.filter.get('date', None)
            actionTypeId = self.filter.get('actionTypeId', None)
            status = self.filter.get('status', None)
            isSchema = self.filter.get('isSchema', False)
            schemaId = self.filter.get('schemaId', None)
#            orgStructureId = self.filter.get('orgStructureId', None)
            actionIdList = []
            db = QtGui.qApp.db
            tableAction = db.table('Action')
            tableActionType = db.table('ActionType')
            tableAX = db.table('ActionExecutionPlan')
            tableAXI = db.table('ActionExecutionPlan_Item')
            tableEvent = db.table('Event')
            queryTable = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
            queryTable = queryTable.innerJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
#            queryTable = queryTable.leftJoin(tableAXI, db.joinAnd([tableAXI['action_id'].eq(tableAction['id']), tableAXI['executedDatetime'].isNull()]))
            queryTable = queryTable.leftJoin(tableAXI, tableAXI['action_id'].eq(tableAction['id']))
            queryTable = queryTable.leftJoin(tableAX, db.joinAnd([tableAX['id'].eq(tableAXI['master_id']), tableAX['deleted'].eq(0)]))
            cond = [tableAction['deleted'].eq(0),
                    tableEvent['deleted'].eq(0),
                    tableAction['event_id'].eq(eventId),
                    tableActionType['deleted'].eq(0),
                    db.joinOr([tableActionType['isDoesNotInvolveExecutionCourse'].eq(1), db.joinAnd([tableAXI['id'].isNotNull(), tableAX['deleted'].eq(0)])])
                    ]
            if date:
                cond.append(tableAction['begDate'].dateEq(date))
            if actionTypeId:
                cond.append(tableAction['actionType_id'].eq(actionTypeId))
            if status:
                cond.append(tableAction['status'].inlist(status))
            if isSchema:
                cond.append(tableAction['actionTypeGroup_id'].isNotNull())
                if schemaId:
                    cond.append(tableAction['actionTypeGroup_id'].eq(schemaId))
            if currentOrgStructureId:
                cond.append(tableAction['orgStructure_id'].eq(currentOrgStructureId))
            records = db.getRecordList(queryTable, 'Action.*', cond, order=[tableAction['idx'].name(), tableAction['id'].name()])
            for record in records:
                actionId = forceRef(record.value('id'))
                if actionId and actionId not in actionIdList:
                    actionIdList.append(actionId)
                    action = CAction(record=record)
                    actionRecord = action.getRecord()
                    actionRecord.append(QtSql.QSqlField('smnnUUID',  QVariant.String))
                    actionRecord.setValue('smnnUUID', toVariant(action.getSmnnUUIDPropertyValue()))
                    actionRecord.append(QtSql.QSqlField('smnnName',  QVariant.String))
                    actionRecord.setValue('smnnName', toVariant(action.getSmnnUUIDPropertyText()))
                    actionRecord.append(QtSql.QSqlField('lfForm_id',  QVariant.Int))
                    actionRecord.setValue('lfForm_id', toVariant(action.getSmnnGrlsLfPropertyValue()))
                    actionRecord.append(QtSql.QSqlField('lfFormName',  QVariant.String))
                    actionRecord.setValue('lfFormName', toVariant(action.getSmnnGrlsLfPropertyText()))
                    actionRecord.append(QtSql.QSqlField('nomenclature_id',  QVariant.Int))
                    actionRecord.setValue('nomenclature_id', toVariant(action.findNomenclaturePropertyValue()))
                    actionRecord.append(QtSql.QSqlField('actionPropertyTemplate_id',  QVariant.Int))
                    actionRecord.setValue('actionPropertyTemplate_id', toVariant(action.getCalculationParamPropertyValue()))
                    actionRecord.append(QtSql.QSqlField('signa',  QVariant.String))
                    actionRecord.setValue('signa', toVariant(action.findSignaPropertyText()))
                    actionRecord.append(QtSql.QSqlField('signaComment',  QVariant.String))
                    actionRecord.setValue('signaComment', toVariant(action.findSignaCommentPropertyText()))
                    actionRecord.append(QtSql.QSqlField('doses',  QVariant.String))
                    actionRecord.setValue('doses', toVariant(action.findDosagePropertyValue()))
                    actionRecord.append(QtSql.QSqlField('dosesName',  QVariant.String))
                    actionRecord.setValue('dosesName', toVariant(action.getGroupDosesTextEx()))
                    actionRecord.append(QtSql.QSqlField('finance_id',  QVariant.Int))
                    actionRecord.setValue('finance_id', toVariant(forceRef(record.value('finance_id'))))
                    actionRecord.append(QtSql.QSqlField('medicalAidKind_id',  QVariant.Int))
                    actionRecord.setValue('medicalAidKind_id', toVariant(forceRef(record.value('medicalAidKind_id'))))
                    actionRecord.append(QtSql.QSqlField('orgStructure_id',  QVariant.Int))
                    actionRecord.setValue('orgStructure_id', toVariant(forceRef(record.value('orgStructure_id'))))
                    actionEventId = forceRef(record.value('event_id'))
                    eventTypeId = None
                    eventRecord = self.eventCache.get(actionEventId)
                    if eventRecord:
                        actionRecord.append(QtSql.QSqlField('eventType_id',  QVariant.Int))
                        eventTypeId = forceRef(eventRecord.value('eventType_id'))
                        actionRecord.setValue('eventType_id', toVariant(eventTypeId))
                    else:
                        eventRecord = db.getRecordEx(tableEvent, '*', [tableEvent['id'].eq(actionEventId), tableEvent['deleted'].eq(0)])
                        if eventRecord:
                            actionRecord.append(QtSql.QSqlField('eventType_id',  QVariant.Int))
                            eventTypeId = forceRef(eventRecord.value('eventType_id'))
                            actionRecord.setValue('eventType_id', toVariant(eventTypeId))
                            self.eventCache[actionEventId] = eventRecord
                    if eventTypeId:
                        items.append(CActionRecordItem(action.getRecord(), action))
        self.modelActions.loadItems(items)


    def loadEvents(self):
        eventIdList = []
        self.hBedOSIdDict = {}
        date = self.filter.get('date', None)
        actionTypeId = self.filter.get('actionTypeId', None)
        status = self.filter.get('status', None)
        isSchema = self.filter.get('isSchema', False)
        schemaId = self.filter.get('schemaId', None)
        orgStructureId = self.filter.get('orgStructureId', None)
        clientId = self.filter.get('clientId', None)
        lastName = self.filter.get('lastName', None)
        firstName = self.filter.get('firstName', None)
        patrName = self.filter.get('patrName', None)
        eventId = self.filter.get('eventId', None)
        externalId = self.filter.get('externalId', None)
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableAction = db.table('Action')
        tableActionType = db.table('ActionType')
        tableClient = db.table('Client')
        tableAX = db.table('ActionExecutionPlan')
        tableAXI = db.table('ActionExecutionPlan_Item')
        queryTable = tableEvent.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
        queryTable = queryTable.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
        queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
#        queryTable = queryTable.leftJoin(tableAXI, db.joinAnd([tableAXI['action_id'].eq(tableAction['id']), tableAXI['executedDatetime'].isNull()]))
        queryTable = queryTable.leftJoin(tableAXI, tableAXI['action_id'].eq(tableAction['id']))
        queryTable = queryTable.leftJoin(tableAX, db.joinAnd([tableAX['id'].eq(tableAXI['master_id']), tableAX['deleted'].eq(0)]))
        cols = [u'DISTINCT Event.id AS eventId',
                #tableEvent['id'].alias(u'eventId'),
                selectOrgStructureHospitalBed(getOrgStructureDescendants(orgStructureId) if orgStructureId else [], date, [clientId] if clientId else [], lastName, firstName, patrName)
                ]
        cond = [tableEvent['deleted'].eq(0),
                tableAction['deleted'].eq(0),
                tableActionType['deleted'].eq(0),
                tableClient['deleted'].eq(0),
                db.joinOr([tableActionType['isDoesNotInvolveExecutionCourse'].eq(1), db.joinAnd([tableAXI['id'].isNotNull(), tableAX['deleted'].eq(0)])])
                ]
        if date:
            cond.append(tableAction['begDate'].dateEq(date))
        if actionTypeId:
            cond.append(tableAction['actionType_id'].eq(actionTypeId))
        if status:
            cond.append(tableAction['status'].inlist(status))
        if isSchema:
            cond.append(tableAction['actionTypeGroup_id'].isNotNull())
            if schemaId:
                cond.append(tableAction['actionTypeGroup_id'].eq(schemaId))
        if clientId:
            cond.append(tableEvent['client_id'].eq(clientId))
        else:
            if lastName:
                cond.append(tableClient['lastName'].like(addDots(lastName)))
            if firstName:
                cond.append(tableClient['firstName'].like(addDots(firstName)))
            if patrName:
                cond.append(tableClient['patrName'].like(addDots(patrName)))
        if eventId:
            cond.append(tableEvent['id'].eq(eventId))
        if externalId:
            cond.append(tableEvent['externalId'].eq(externalId))
        currentOrgStructureId = QtGui.qApp.currentOrgStructureId()
        if currentOrgStructureId:
            cond.append(tableAction['orgStructure_id'].inlist(getOrgStructureDescendants(currentOrgStructureId))) #inlist(getOrgStructureDescendants(orgStructureId))
        having = []
        if orgStructureId:
            having = [u'hBedOSId IN (%s)'%(','.join(map(str, getOrgStructureDescendants(orgStructureId))))]
        records = db.getRecordListHaving(queryTable, cols, cond, having, order=[tableClient['lastName'].name(), tableClient['firstName'].name(), tableClient['patrName'].name(), tableAction['begDate'].name()])
        for record in records:
            eventId = forceRef(record.value('eventId'))
            if eventId and eventId not in eventIdList:
                eventIdList.append(eventId)
            hBedOSId = forceRef(record.value('hBedOSId'))
            if hBedOSId:
                self.hBedOSIdDict[eventId] = hBedOSId
        if eventIdList:
            eventRecords = db.getRecordList(tableEvent, '*', [tableEvent['id'].inlist(eventIdList), tableEvent['deleted'].eq(0)])
            for eventRecord in eventRecords:
                eventId = forceRef(eventRecord.value('event_id'))
                if eventId and eventId not in self.eventCache.keys():
                    self.eventCache[eventId] = eventRecord
        currentEventId = self.tblCentralizedAccounting.currentItemId()
        self.modelCentralizedAccounting.setIdList(eventIdList)
        self.modelCentralizedAccounting.setHBedOSIdDict(self.hBedOSIdDict)
        if currentEventId:
            self.tblCentralizedAccounting.setCurrentItemId(currentEventId)
        else:
            self.tblCentralizedAccounting.setCurrentRow(0)
        self.lblRecordCount.setText(formatRecordsCount(len(eventIdList)))
        return eventIdList


class CCentralizedAccountingModel(CTableModel):
    Col_HBedOSName = 4
    class CLocClientColumn(CCol):
        def __init__(self, title, fields, defaultWidth, clientCache):
            CCol.__init__(self, title, fields, defaultWidth, 'l')
            self.clientCache = clientCache

        def format(self, values):
            val = values[0]
            clientId  = forceRef(val)
            clientRecord = self.clientCache.get(clientId)
            if clientRecord:
                name  = formatName(clientRecord.value('lastName'),
                                   clientRecord.value('firstName'),
                                   clientRecord.value('patrName'))
                return toVariant(name)
            return CCol.invalid

    class CLocHBedOSNameColumn(CCol):
        def __init__(self, title, fields, defaultWidth, orgStructureCache):
            CCol.__init__(self, title, fields, defaultWidth, 'l')
            self.orgStructureCache = orgStructureCache
            self.hBedOSIdDict = {}

        def setHBedOSIdDict(self, hBedOSIdDict):
            self.hBedOSIdDict = hBedOSIdDict

        def format(self, values):
            val = values[0]
            eventId = forceRef(val)
            if eventId:
                hBedOSId = self.hBedOSIdDict.get(eventId, None)
                if hBedOSId:
                    record = self.orgStructureCache.get(hBedOSId)
                    if record:
                        name = forceStringEx(record.value('name'))
                        return toVariant(name)
            return CCol.invalid

    def __init__(self, parent):
        self.clientCache = CTableRecordCache(QtGui.qApp.db, 'Client', ('id', 'lastName', 'firstName', 'patrName', 'birthDate', 'sex'), 300)
        self.orgStructureCache = CTableRecordCache(QtGui.qApp.db, 'OrgStructure', ('id', 'name'), 300)
        CTableModel.__init__(self, parent)
        self.hBedOSIdDict = {}
        self.addColumn(CTextCol(u'Код пациента', ['client_id'], 30))
        self.addColumn(self.CLocClientColumn( u'Ф.И.О.', ('client_id',), 60, self.clientCache))
        self.addColumn(CTextCol(u'Код карточки', ['id'], 30))
        self.addColumn(CTextCol(u'Карта', ['externalId'], 30))
        self.addColumn(self.CLocHBedOSNameColumn( u'Подразделение пребывания', ('id',), 60, self.orgStructureCache))
        self.setTable('Event')
        self._mapColumnToOrder = {'client_id'          :'CONCAT(Client.lastName, Client.firstName, Client.patrName)',
                                  'orgStructure_id'    :'OrgStructure.name',
                                  'id'                 :'Event.id',
                                  'externalId'         :'Event.externalId'
                                  }


    def setHBedOSIdDict(self, hBedOSIdDict):
        self.hBedOSIdDict = hBedOSIdDict
        self.cols()[CCentralizedAccountingModel.Col_HBedOSName].setHBedOSIdDict(self.hBedOSIdDict)


    def getOrder(self, fieldName, column):
        if hasattr(self._cols[column], 'extraFields'):
            if len(self._cols[column].extraFields) > 0:
                fieldName = self._cols[column].extraFields[0]
        return self._mapColumnToOrder[fieldName]


    def invalidateRecordsCache(self):
        self.clientCache.invalidate()
        CTableModel.invalidateRecordsCache(self)


def existsOrgStructureHospitalBed(orgStructureIdList, date, clientIdList, lastName, firstName, patrName):
    db = QtGui.qApp.db
    tableAPT = db.table('ActionPropertyType').alias(u'APT')
    tableAP = db.table('ActionProperty').alias(u'AP')
    tableActionType = db.table('ActionType').alias(u'AT')
    tableAction = db.table('Action').alias(u'A')
    tableEvent = db.table('Event').alias(u'E')
    tableClient = db.table('Client').alias(u'C')
    tableOS = db.table('OrgStructure').alias(u'OS')
    tableAPHB = db.table('ActionProperty_HospitalBed').alias(u'APHB')
    tableOSHB = db.table('OrgStructure_HospitalBed').alias(u'OSHB')
    queryTable = tableActionType.innerJoin(tableAction, tableActionType['id'].eq(tableAction['actionType_id']))
    queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
    queryTable = queryTable.leftJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
    queryTable = queryTable.innerJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
    queryTable = queryTable.innerJoin(tableAP, tableAP['type_id'].eq(tableAPT['id']))
    queryTable = queryTable.innerJoin(tableAPHB, tableAPHB['id'].eq(tableAP['id']))
    queryTable = queryTable.innerJoin(tableOSHB, tableOSHB['id'].eq(tableAPHB['value']))
    queryTable = queryTable.innerJoin(tableOS, tableOS['id'].eq(tableOSHB['master_id']))
    cond = [tableActionType['flatCode'].like('moving%'),
            tableAction['deleted'].eq(0),
            tableEvent['deleted'].eq(0),
            tableClient['deleted'].eq(0),
            tableAP['deleted'].eq(0),
            tableActionType['deleted'].eq(0),
            tableAPT['deleted'].eq(0),
            tableOS['deleted'].eq(0),
            tableAPT['typeName'].like('HospitalBed'),
            tableAP['action_id'].eq(tableAction['id'])
           ]
    cond.append(u'C.id = Client.id')
    if clientIdList:
        cond.append(tableClient['id'].inlist(clientIdList))
    else:
        if lastName:
            cond.append(tableClient['lastName'].like(lastName))
        if firstName:
            cond.append(tableClient['firstName'].like(firstName))
        if patrName:
            cond.append(tableClient['patrName'].like(patrName))
    if date:
        cond.append(db.joinAnd([tableAction['begDate'].dateLe(date),
                    db.joinOr([tableAction['endDate'].isNull(), tableAction['endDate'].dateGe(date)])]))
    if orgStructureIdList:
        cond.append(tableOS['id'].inlist(orgStructureIdList))
    return db.existsStmt(queryTable, cond)


def selectOrgStructureHospitalBed(orgStructureIdList, date, clientIdList, lastName, firstName, patrName):
    db = QtGui.qApp.db
    tableAPT = db.table('ActionPropertyType').alias(u'APT')
    tableAP = db.table('ActionProperty').alias(u'AP')
    tableActionType = db.table('ActionType').alias(u'AT')
    tableAction = db.table('Action').alias(u'A')
    tableEvent = db.table('Event').alias(u'E')
    tableClient = db.table('Client').alias(u'C')
    tableOS = db.table('OrgStructure').alias(u'OS')
    tableAPHB = db.table('ActionProperty_HospitalBed').alias(u'APHB')
    tableOSHB = db.table('OrgStructure_HospitalBed').alias(u'OSHB')
    queryTable = tableActionType.innerJoin(tableAction, tableActionType['id'].eq(tableAction['actionType_id']))
    queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
    queryTable = queryTable.leftJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
    queryTable = queryTable.innerJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
    queryTable = queryTable.innerJoin(tableAP, tableAP['type_id'].eq(tableAPT['id']))
    queryTable = queryTable.innerJoin(tableAPHB, tableAPHB['id'].eq(tableAP['id']))
    queryTable = queryTable.innerJoin(tableOSHB, tableOSHB['id'].eq(tableAPHB['value']))
    queryTable = queryTable.innerJoin(tableOS, tableOS['id'].eq(tableOSHB['master_id']))
    cond = [tableActionType['flatCode'].like('moving%'),
            tableAction['deleted'].eq(0),
            tableEvent['deleted'].eq(0),
            tableClient['deleted'].eq(0),
            tableAP['deleted'].eq(0),
            tableActionType['deleted'].eq(0),
            tableAPT['deleted'].eq(0),
            tableOS['deleted'].eq(0),
            tableAPT['typeName'].like('HospitalBed'),
            tableAP['action_id'].eq(tableAction['id'])
           ]
    cond.append(u'C.id = Client.id')
    if clientIdList:
        cond.append(tableClient['id'].inlist(clientIdList))
    else:
        if lastName:
            cond.append(tableClient['lastName'].like(lastName))
        if firstName:
            cond.append(tableClient['firstName'].like(firstName))
        if patrName:
            cond.append(tableClient['patrName'].like(patrName))
    if date:
        cond.append(db.joinAnd([tableAction['begDate'].dateLe(date),
                    db.joinOr([tableAction['endDate'].isNull(), tableAction['endDate'].dateGe(date)])]))
    if orgStructureIdList:
        cond.append(tableOS['id'].inlist(orgStructureIdList))
    stmt = db.selectDistinctStmt(queryTable, fields=[tableOS['id']], where=cond, order=[tableAction['begDate'].name(), tableAction['endDate'].name()], limit=1)
    return u'(' + stmt + u') AS hBedOSId'

