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
import json

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt, SIGNAL, pyqtSignature, QModelIndex, QVariant, SLOT, QDateTime, QTime, QDate
from PyQt4.QtSql import QSqlField
from Events.ActionsModel import CActionRecordItem
from Stock.NomenclatureComboBox import CNomenclatureComboBox

from library.DialogBase                 import CDialogBase
from NomenclatureExpenseModel           import CNomenclatureExpenseModel
from QueriesStatements                  import getNomenclatureActionTypesIds
from NomenclatureExpenseLoadTemplate    import CNomenclatureExpenseLoadTemplate
from UpdateDoseNomenclatureExpenseEditor import CUpdateDoseNomenclatureExpenseEditor
from CancelActionsNomenclatureExpenseEditor import CCancelActionsNomenclatureExpenseEditor
from Utils                              import (DIREACTION_DATE_INDEX,
                                                BEG_DATE_INDEX,
                                                PLAN_END_DATE,
                                                NOMENCLATURE_INDEX,
                                                DOSES_INDEX,
                                                DURATION_INDEX,
                                                ALIQUOTICITY_INDEX,
                                                SMNN_INDEX,
                                                SMNN_GRLSLF_INDEX,
                                                #ORGSTRUCTURE_INDEX
                                                )
from Events.Action                      import CAction, CActionTypeCache
from Events.ActionStatus                import CActionStatus
from Events.ActionInfo                  import CActionInfoProxyListEx, CActionInfoProxyList
from Events.EventInfo                   import CDiagnosticInfoProxyList, CVisitInfoProxyList
from Events.Utils                       import getEventShowTime, getEventEnableActionsBeyondEvent
from library.Utils                      import forceString, forceStringEx, forceInt, forceRef, forceDate, forceDateTime, forceBool, toVariant, getPref, setPref
from library.ESKLP.SmnnGrlsLfNomenclatureExpenseEditor import CSmnnGrlsLfNomenclatureExpenseEditor
from library.PrintInfo                  import CInfoContext
from Reports.ReportBase                 import CReportBase, createTable
from Reports.ReportView                 import CReportViewDialog
from library.PrintTemplates             import applyTemplate, CPrintAction, CPrintButton, getPrintTemplates
from Users.Rights                       import urEditChkOnlyExistsNomenclature, urAdmin, urCanCreateNewActionTypeGroup, urEditClosedEvent, urHBEditEvent, urHBReadEvent, urRegTabWriteEvents

from RefBooks.ActionTypeGroup.RBActionTypeGroupEditor import ActionTypeGroupEditor

from Ui_NomenclatureExpenseDialog   import Ui_NomenclatureExpenseDialog
from Ui_ExtendAppointmentNomenclatureDialog import Ui_ExtendAppointmentNomenclatureDialog


_RECIPE = 1
_DOSES  = 2
_SIGNA  = 3
_ACTIVESUBSTANCE = 4
_REACTION = 5

def _getDefaultValues():
    result = {}
    data = forceString(
        QtGui.qApp.preferences.appPrefs.get('NomenclatureExpenseDialogDefaultValues', '')
    )
    try:
        data = json.loads(data) if data else {}
    except:
        data = {}

    result['actionTypeId'] = data.get('actionTypeId', None)
    result['nomenclatureId'] = data.get('nomenclatureId', None)
    result['begDate'] = QtCore.QDate.fromString(data.get('begDate', QtCore.QDate.currentDate().toString('yyyy.MM.dd')), 'yyyy.MM.dd')
    result['endDate'] = QtCore.QDate.fromString(data.get('endDate', QtCore.QDate.currentDate().toString('yyyy.MM.dd')), 'yyyy.MM.dd')
    result['year'] = data.get('year', QtCore.QDate.currentDate().year())
    result['month'] = data.get('month', QtCore.QDate.currentDate().month() - 1)
    result['period'] = data.get('period', False)
    result['actual'] = data.get('actual', True)
    result['ignoreTime'] = data.get('ignoreTime', False)
    result['isRequiresFillingNomenclature'] = data.get('isRequiresFillingNomenclature', False)
    result['schemaId'] = data.get('schemaId', None)
    result['currentEvent'] = data.get('currentEvent', True)
    result['orgStructureId'] = data.get('orgStructureId', None)

    return result


class CNomenclatureExpenseDialog(CDialogBase, Ui_NomenclatureExpenseDialog):
    def __init__(self, parent=None, eventEditor=None, groups=None, fromEventEditor=True):
        CDialogBase.__init__(self, parent)

        self.modelNomenclatureExpense = None
        self.selectionModelNomenclatureExpense = None

        self.addModels('NomenclatureExpense', CNomenclatureExpenseModel(self))
        self.selectionModelNomenclatureExpenseDays = QtGui.QItemSelectionModel(self.modelNomenclatureExpense, self)
        self.selectionModelNomenclatureExpenseDays.setObjectName('selectionModelNomenclatureExpenseDays')
        self.addObject('btnPrint', CPrintButton(self, u'Печать'))
        self.addObject('btnSaveTemplate', QtGui.QPushButton(u'Сохранить шаблон', self))
        self.addObject('btnLoadTemplate', QtGui.QPushButton(u'Загрузить шаблон', self))
        self.btnPrint.setShortcut('F6')

        self.setupUi(self)

        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowMaximizeButtonHint)
        self.buttonBox.addButton(self.btnPrint, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnSaveTemplate, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnLoadTemplate, QtGui.QDialogButtonBox.ActionRole)
        self.isHBDialog = False
        templates = getPrintTemplates(self.getNomenclatureExpenseContext())
        if not templates:
            self.btnPrint.setId(-1)
        else:
            for template in templates:
                action = CPrintAction(template.name, template.id, self.btnPrint, self.btnPrint)
                self.btnPrint.addAction(action)
            self.btnPrint.menu().addSeparator()
            self.btnPrint.addAction(CPrintAction(u'Напечатать список', -1, self.btnPrint, self.btnPrint))
        self.cmbActionType.setClass(None)
        self.cmbActionType.setClassesVisible(True)
        self.setCmbActionTypeFilter()
        self.cmbNomenclature.setOnlyExists(True)
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbSchema.setTable('ActionTypeGroup')

        defaults = _getDefaultValues()

        self.cmbActionType.setValue(defaults['actionTypeId'])
        orgStructureId = defaults['orgStructureId']
        self.cmbOrgStructure.setValue(orgStructureId if orgStructureId else QtGui.qApp.currentOrgStructureId())
        self.cmbNomenclature.setValue(defaults['nomenclatureId'])
        self.cmbNomenclature.getFilterData()
        self.cmbNomenclature.setFilter(self.cmbNomenclature._filter)
        self.edtBegDate.setDate(defaults['begDate'])
        self.edtEndDate.setDate(defaults['endDate'])
        self.edtYear.setValue(defaults['year'])
        self.cmbMonth.setCurrentIndex(defaults['month'])
        self.chkPeriod.setChecked(defaults['period'])
        self.chkActual.setChecked(defaults['actual'])
        self.chkIgnoreTime.setChecked(defaults['ignoreTime'])
        self.chkRequiresFillingNomenclature.setChecked(defaults['isRequiresFillingNomenclature'])
        self.chkCurrentEvent.setChecked(defaults['currentEvent'])

        self._eventEditor = eventEditor
        self._fromEventEditor = fromEventEditor

        self.setWindowTitle(u'Назначение ЛС')

        self.setModels(
            self.tblNomenclatureExpense,
            self.modelNomenclatureExpense,
            self.selectionModelNomenclatureExpense
        )
        self.setModels(
            self.tblNomenclatureExpenseDays,
            self.modelNomenclatureExpense,
            self.selectionModelNomenclatureExpenseDays
        )
        self.tblNomenclatureExpenseDays.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tblNomenclatureExpenseDays.addEditDay()
        self.tblNomenclatureExpenseDays.addCopyDay()
        self.tblNomenclatureExpenseDays.addPasteDay()
        self.tblNomenclatureExpenseDays.addDeleteDays()
        self.modelNomenclatureExpense.setIgnoreTime(self.chkIgnoreTime.isChecked())

        self._hideDaysColumns(self.tblNomenclatureExpense)
        self._hideMainColumns(self.tblNomenclatureExpenseDays)

        self._cmbActionTypeWidgetsDependets = [
            self.cmbNomenclature, self.chkPeriod, self.chkActual, self.chkIgnoreTime, self.chkCurrentEvent, self.edtYear, self.cmbMonth,
            self.lblNomenclature, self.lblYear, self.lblMonth, self.chkRequiresFillingNomenclature, self.cmbSchema
        ]

        self.chkCurrentEvent.setVisible(False)

        self.addObject('mnuNomenclatureExpense', QtGui.QMenu(self))
        self.addObject('actDeleteRows', QtGui.QAction(u'Удалить назначение', self))
        self.connect(self.actDeleteRows, SIGNAL('triggered()'), self.on_actDeleteRows_triggered)

        self.addObject('actCancelActions', QtGui.QAction(u'Отменить назначение', self))
        self.connect(self.actCancelActions, SIGNAL('triggered()'), self.on_actCancelActions_triggered)

        self.addObject('actExtendAppointmentNomenclature', QtGui.QAction(u'Продлить назначение', self))
        self.connect(self.actExtendAppointmentNomenclature, SIGNAL('triggered()'), self.on_extendAppointmentNomenclature)
        
        self.addObject('actAddRows', QtGui.QAction(u'Добавить назначение в группу', self))
        self.actAddRows.setShortcut('F1')
        self.connect(self.actAddRows, SIGNAL('triggered()'), self.on_actAddRows_triggered)

        self.addObject('actCalculationDoseNomenclature', QtGui.QAction(u'Рассчитать дозу', self))
        self.actCalculationDoseNomenclature.setShortcut('F2')
        self.connect(self.actCalculationDoseNomenclature, SIGNAL('triggered()'), self.on_actCalculationDoseNomenclature_triggered)

        self.addObject('actUpdateDoseNomenclature', QtGui.QAction(u'Изменить дозу', self))
        self.actUpdateDoseNomenclature.setShortcut('F3')
        self.connect(self.actUpdateDoseNomenclature, SIGNAL('triggered()'), self.on_actUpdateDoseNomenclature_triggered)

        self.addObject('actShowAllOrgStructureAssignments', QtGui.QAction(u'Показать все назначения подразделения', self))
        self.connect(self.actShowAllOrgStructureAssignments, SIGNAL('triggered()'), self.on_actShowAllOrgStructureAssignment_triggered)

        self.tblNomenclatureExpense.setNomenclatureExpensePopupMenu(self.mnuNomenclatureExpense)
        self.mnuNomenclatureExpense.addActions([self.actDeleteRows, self.actCancelActions, self.actExtendAppointmentNomenclature, self.actAddRows, self.actCalculationDoseNomenclature, self.actUpdateDoseNomenclature, self.actShowAllOrgStructureAssignments])

        self.addObject('qshcCalculationDoseNomenclature', QtGui.QShortcut('F2', self.tblNomenclatureExpense, self.on_actCalculationDoseNomenclature_triggered))
        self.qshcCalculationDoseNomenclature.setContext(Qt.WidgetShortcut)

        self.addObject('qshcUpdateDoseNomenclature', QtGui.QShortcut('F3', self.tblNomenclatureExpense, self.on_actUpdateDoseNomenclature_triggered))
        self.qshcUpdateDoseNomenclature.setContext(Qt.WidgetShortcut)

        self.connect(self.cmbActionType, SIGNAL('currentIndexChanged(int)'), self.on_cmbActionTypeIndexChanged)
        self.connect(self.cmbNomenclature, SIGNAL('currentIndexChanged(int)'), self.on_cmbNomenclatureIndexChanged)
        self.connect(self.cmbMonth, SIGNAL('currentIndexChanged(int)'), self.on_cmbMonthIndexChanged)
        self.connect(self.edtYear, SIGNAL('valueChanged(int)'), self.on_edtYearValueChanged)
        self.connect(self.chkActual, SIGNAL('clicked(bool)'), self.on_chkActualClicked)
        self.connect(self.chkIgnoreTime, SIGNAL('clicked(bool)'), self.on_chkIgnoreTimeClicked)
        self.connect(self.chkRequiresFillingNomenclature, SIGNAL('clicked(bool)'), self.on_chkRequiresFillingNomenclatureClicked)
        self.connect(self.cmbSchema, SIGNAL('currentIndexChanged(int)'), self.on_cmbSchemaClicked)
        self.connect(self.chkPeriod, SIGNAL('clicked(bool)'), self.on_chkPeriodClicked)
        self.connect(self.tblNomenclatureExpense.verticalScrollBar(), SIGNAL('valueChanged(int)'), self.tblNomenclatureExpenseDays.verticalScrollBar(), SLOT('setValue(int)'))
        self.connect(self.tblNomenclatureExpenseDays.verticalScrollBar(), SIGNAL('valueChanged(int)'), self.tblNomenclatureExpense.verticalScrollBar(), SLOT('setValue(int)'))

        self.connect(
            self.selectionModelNomenclatureExpense,
            SIGNAL('currentChanged(QModelIndex, QModelIndex)'),
            self.on_nomenclatureExpenseSelectionChanged
        )

        self.connect(
            self.selectionModelNomenclatureExpenseDays,
            SIGNAL('currentChanged(QModelIndex, QModelIndex)'),
            self.on_nomenclatureExpenseDaysSelectionChanged
        )

        self.on_cmbActionTypeIndexChanged()
        self.cmbSchema.setValue(defaults['schemaId'])
        self.on_cmbNomenclatureIndexChanged()
        self.on_cmbMonthIndexChanged(self.cmbMonth.currentIndex())
        self.on_edtYearValueChanged(self.edtYear.value())
        self.on_chkActualClicked(self.chkActual.isChecked())
        self.on_chkIgnoreTimeClicked(self.chkIgnoreTime.isChecked())
        self.on_chkPeriodClicked()
        self.on_edtBegDate_dateChanged(self.edtBegDate.date())
        self.on_edtEndDate_dateChanged(self.edtEndDate.date())

        self.groups = groups
        self.groupsDeleted = []
        for group in self.groups:
            if group.groupingInfo:
                group.clearGroupingInfo()
        self.modelNomenclatureExpense.setOriginGroups(self.groups)
        self.updateSchemaItems()

        preferences = getPref(QtGui.qApp.preferences.windowPrefs, 'CNomenclatureExpenseDialog_tblNomenclatureExpense', {})
        self.tblNomenclatureExpense.loadPreferences(preferences)
        self.tblNomenclatureExpense.enableColsHide()
        self.tblNomenclatureExpense.enableColsMove()
        preferencesDays = getPref(QtGui.qApp.preferences.windowPrefs, 'CNomenclatureExpenseDialog_tblNomenclatureExpenseDays', {})
        self.tblNomenclatureExpenseDays.loadPreferences(preferencesDays)
#        self.tblNomenclatureExpenseDays.enableColsHide()
#        self.tblNomenclatureExpenseDays.enableColsMove()
        self.btnSaveTemplate.setEnabled(bool(self.cmbOrgStructure.value()) and (QtGui.qApp.userHasRight(urAdmin) or QtGui.qApp.userHasRight(urCanCreateNewActionTypeGroup)))
        self.btnLoadTemplate.setEnabled(bool(self.cmbOrgStructure.value()))
        self.clientIntoleranceMedicamentRecords = []
        self.modelNomenclatureExpense.sort(0)


    def setHBUpdateEvent(self, isHBDialog):
        self.isHBDialog = isHBDialog


    def protectWidgetFromEdit(self):
        isClosed = self._eventEditor.tabNotes.isEventClosed()
        isProtected = isClosed and not QtGui.qApp.userHasRight(urEditClosedEvent)
        if self.isHBDialog:
            if not isProtected:
                isProtected = QtGui.qApp.userHasRight(urHBReadEvent) and not QtGui.qApp.userHasRight(urHBEditEvent)  # из стац.монитора
        else:
            if not isProtected:
                isProtected = not QtGui.qApp.userHasRight(urRegTabWriteEvents)  # Работа -> Обслуживание
        isEditable = not isProtected
        if hasattr(self, 'modelNomenclatureExpense'):
            self.modelNomenclatureExpense.setReadOnly(isProtected)
        if hasattr(self, 'buttonBox'):
            self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(isEditable)
            self.btnSaveTemplate.setEnabled(isEditable and (bool(self.cmbOrgStructure.value()) and (QtGui.qApp.userHasRight(urAdmin) or QtGui.qApp.userHasRight(urCanCreateNewActionTypeGroup))))
            self.btnLoadTemplate.setEnabled(isEditable and bool(self.cmbOrgStructure.value()))


    def getEventInfo(self, context):
        from Events.EventEditDialog import  CEventEditDialog
        result = CEventEditDialog.getEventInfo(self._eventEditor, context)
        if hasattr(self._eventEditor, 'cmbPrimary'):
            result._isPrimary = self._eventEditor.cmbPrimary.currentIndex()+1
        elif hasattr(self._eventEditor, 'chkPrimary'):
            result._isPrimary = toVariant(1 if self._eventEditor.chkPrimary.isChecked() else 2)
        elif hasattr(self._eventEditor, 'cmbOrder'):
            result._isPrimary = forceInt(self._eventEditor.cmbOrder.currentIndex())+1
        else:
            result._isPrimary = 0
        actionsTabModels = []
        for actionsTab in self._eventEditor.getActionsTabsList():
            actionsTabModels.append(actionsTab.modelAPActions)
        result._actions = CActionInfoProxyList(context, actionsTabModels, result)
        diagnosticModels = []
        if hasattr(self._eventEditor, 'modelDiagnostics'):
            diagnosticModels.append(self._eventEditor.modelDiagnostics)
        if hasattr(self._eventEditor, 'modelPreliminaryDiagnostics'):
            diagnosticModels.append(self._eventEditor.modelPreliminaryDiagnostics)
        if hasattr(self._eventEditor, 'modelFinalDiagnostics'):
            diagnosticModels.append(self._eventEditor.modelFinalDiagnostics)
        if diagnosticModels:
            result._diagnosises = CDiagnosticInfoProxyList(context, diagnosticModels)
        if hasattr(self._eventEditor, 'modelVisits'):
            result._visits = CVisitInfoProxyList(context, self._eventEditor.modelVisits)
        return result


    @pyqtSignature('int')
    def on_btnPrint_printByTemplate(self, templateId):
        if templateId == -1:
            self.getNomenclatureExpensePrint()
        else:
            context = CInfoContext()
            eventInfo = self.getEventInfo(context)
            clientInfo = eventInfo.client
            actionsInfo = eventInfo.actions
            actionList = []
            model = self.tblNomenclatureExpense.model()
            for row, group in enumerate(model._groups):
                actionList.append((group.headItem.action.getRecord(), group.headItem.action))
            executionPlanActions = CActionInfoProxyListEx(context, actionList, eventInfo=eventInfo)
            data = { 'executionPlanActions': executionPlanActions,
                     'event': eventInfo,
                     'actions': actionsInfo,
                     'client': clientInfo
                    }
            QtGui.qApp.call(self, applyTemplate, (self, templateId, data))


    def getNomenclatureExpenseContext(self):
        return ['NomenclatureExpense']


    def dumpParams(self, cursor):
        db = QtGui.qApp.db
        description = []
        actionTypeId = self.cmbActionType.value()
        if actionTypeId:
            description.append(u'Тип действия: %s'%forceString(db.translate('ActionType', 'id', actionTypeId, 'name')))
        orgStructureId = self.cmbOrgStructure.value()
        if orgStructureId:
            description.append(u'Подразделение: %s'%forceString(db.translate('OrgStructure', 'id', orgStructureId, 'name')))
        actionTypeGroupId = self.cmbSchema.value()
        if actionTypeGroupId:
            description.append(u'Схема: %s'%forceString(db.translate('ActionTypeGroup', 'id', actionTypeGroupId, 'name')))
        nomenclatureId = self.cmbNomenclature.value()
        if nomenclatureId:
            description.append(u'ЛС: %s'%forceString(db.translate('rbNomenclature', 'id', nomenclatureId, 'name')))
        if self.chkActual.isChecked():
            description.append(u'Период с %s по %s'%(forceString(self.edtBegDate.date()), forceString(self.edtEndDate.date())))
        if self.chkPeriod.isChecked():
            description.append(u'Только актуальные')
        if self.chkIgnoreTime.isChecked():
            description.append(u'Игнорировать время')
        if self.chkRequiresFillingNomenclature.isChecked():
            description.append(u'Требует заполнения ЛС')
        if self.chkCurrentEvent.isChecked():
            description.append(u'Текущее событие')
        description.append(u'Год %s'%forceString(self.edtYear.value()))
        description.append(u'Месяц %s'%forceString(self.cmbMonth.currentText()))
        description.append(u'отчёт составлен: ' + forceString(QDateTime.currentDateTime()))
        columns = [ ('100%', [], CReportBase.AlignLeft) ]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()


    def getNomenclatureExpensePrint(self):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.windowTitle())
        self.dumpParams(cursor)
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        model = self.tblNomenclatureExpense.model()
        colWidths  = [ self.tblNomenclatureExpense.columnWidth(i) for i in xrange(model.columnCount()-1) ]
        colWidths.insert(0,10)
        totalWidth = sum(colWidths)
        tableColumns = []
        iColNumber = False
        for iCol, colWidth in enumerate(colWidths):
            widthInPercents = str(max(1, colWidth*90/totalWidth))+'%'
            if iColNumber == False:
                tableColumns.append((widthInPercents, [u'№'], CReportBase.AlignRight))
                iColNumber = True
            tableColumns.append((widthInPercents, [forceString(model.cols()[iCol].title())], CReportBase.AlignLeft))
        table = createTable(cursor, tableColumns)
        for iModelRow in xrange(model.rowCount()-1):
            iTableRow = table.addRow()
            table.setText(iTableRow, 0, iModelRow+1)
            for iModelCol in xrange(model.columnCount()):
                index = model.createIndex(iModelRow, iModelCol)
                text = forceString(model.data(index))
                table.setText(iTableRow, iModelCol+1, text)
        html = doc.toHtml('utf-8')
        view = CReportViewDialog(self)
        view.setText(html)
        view.exec_()


    def getSelectedRows(self):
        selectedRows = []
        selectedIndexes = self.tblNomenclatureExpense.selectedIndexes()
        if selectedIndexes:
            model = self.tblNomenclatureExpense.model()
            for index in selectedIndexes:
                if index and index.isValid():
                    row = index.row()
                    if 0 <= row < len(model.groups()) and row not in selectedRows:
                        selectedRows.append(row)
        selectedRows.sort()
        return selectedRows

    
    def on_actAddRows_triggered(self):
        if self.tblNomenclatureExpense.isNomenclatureExpensePopupMenuEnabled():
            nomenclatureId = None
            index = self.tblNomenclatureExpense.currentIndex()
            model = self.tblNomenclatureExpense.model()
            if index.row() <= len(model._groups)-1:
                group = model._groups[index.row()]
                nomenclatureId = self.selectNomenclature(group)
                orgStructureId = self.getOrgStructureId()
                if nomenclatureId:                    
                    if not group.groupingItem:
                        group.setGroupingItem(group.currentItem)
                    if not group.groupingInfo:
                        group.appendGroupingInfo(group.currentItem)
                    newgroup = model._addNewGroup(nomenclatureId, orgStructureId, group)
                    group.appendGroupingInfo(newgroup.currentItem)
                    newgroup.setGroupingItem(group.currentItem)
            if nomenclatureId:
                model.sort(0)
                self.setIsDirty(True)
    
    
    def selectNomenclature(self, group):
        dialog = QtGui.QDialog(self)
        layout = QtGui.QVBoxLayout(dialog)

        dialog.setWindowTitle(u"Выберите ЛС")
        dialog.cmb = self.modelNomenclatureExpense._createNomenclatureEditor(self, group)
        layout.addWidget(dialog.cmb)
        dialog.btnbox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        layout.addWidget(dialog.btnbox)
        dialog.btnbox.accepted.connect(dialog.accept)
        dialog.btnbox.rejected.connect(dialog.reject)
        if dialog.exec_():
            return dialog.cmb.value()
        else:
            return None
        

    def on_actDeleteRows_triggered(self):
        rows = self.getSelectedRows()
        for row in reversed(rows):
            if row <= len(self.modelNomenclatureExpense.groups()):
                headAction = self.modelNomenclatureExpense.groups()[row].headItem.action
                if not forceRef(headAction._record.value('id')):
                    group = self.modelNomenclatureExpense.groups()[row]   
                    if group.groupingItem == group.currentItem:
                        deleteGroupLast = None
                        if group.groupingInfo and group.currentItem in group.groupingInfo and len(group.groupingInfo)>1:
                            if QtGui.QMessageBox().question(self,
                                                            u'Внимание!',
                                                            u'При удалении группирующего элемента, удалится вся группа. Продолжить?',
                                                            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                                            QtGui.QMessageBox.No
                                                            ) == QtGui.QMessageBox.Yes:
                                for subrow, subgroup in enumerate(self.modelNomenclatureExpense.groups()):
                                    if subgroup.groupingItem == group.groupingItem and not subgroup.groupingItem == subgroup.currentItem:
                                        group.removeGroupingInfo(subgroup.currentItem)
                                        self.removeNewGroupRows(subrow, self.modelNomenclatureExpense.rowCount()-1,  subgroup)
                                    elif subgroup.groupingItem == group.groupingItem and subgroup.groupingItem == subgroup.currentItem:
                                        deleteGroupLast = (subrow, subgroup)
                                if deleteGroupLast:
                                    group.removeGroupingInfo(group.currentItem)
                                    self.removeNewGroupRows(deleteGroupLast[0], self.modelNomenclatureExpense.rowCount()-1,  deleteGroupLast[1])
                        else:
                            self.removeNewGroupRows(row, self.modelNomenclatureExpense.rowCount()-1,  group)
                    else:
                        for subgroup in self.modelNomenclatureExpense.groups():
                            if subgroup.currentItem == group.groupingItem:
                                if subgroup.groupingInfo and group.currentItem in subgroup.groupingInfo:
                                    subgroup.removeGroupingInfo(group.currentItem)
                        self.removeNewGroupRows(row, self.modelNomenclatureExpense.rowCount()-1,  group)
                    self.modelNomenclatureExpense.emitAllDataChanged()
        self.setIsDirty(True)


    def on_actCancelActions_triggered(self):
        rows = self.getSelectedRows()
        db = QtGui.qApp.db
        tableActiveSubstance = db.table('rbNomenclatureActiveSubstance')
        tableReactionType = db.table('rbReactionType')
        tableReactionManifestation = db.table('rbReactionManifestation')
        tblClientIntoleranceMedicament = db.table('ClientIntoleranceMedicament')
        recordIntoleranceMedicament = None
        for row in reversed(rows):
            if row <= len(self.modelNomenclatureExpense.groups()):
                headAction = self.modelNomenclatureExpense.groups()[row].headItem.action
                if forceRef(headAction._record.value('id')):
                    items = self.modelNomenclatureExpense.groups()[row].items
                    dialog = CCancelActionsNomenclatureExpenseEditor(self)
                    begDateActionLast = None
                    for i in range(len(items)):
                        begDateAction = forceDateTime(items[i].action._record.value('begDate'))
                        if not begDateActionLast:
                            begDateActionLast = begDateAction
                        elif begDateAction > begDateActionLast:
                            begDateActionLast = begDateAction
                    nomenclatureId = self.modelNomenclatureExpense._cellsSettings.getGroupNomenclature(self.modelNomenclatureExpense.groups()[row])
                    if nomenclatureId:
                        tableComposition = db.table('rbNomenclature_Composition')
                        compositionRecord = db.getRecordEx(tableComposition, [tableComposition['activeSubstance_id']], [tableComposition['master_id'].eq(nomenclatureId)])
                        composition = forceInt(compositionRecord.value('activeSubstance_id')) if compositionRecord else 0
                        if composition:
                            dialog.setNomenclature(composition)
                    dialog.setMinBegDate(begDateActionLast)
                    try:
                        if dialog.exec_():
                            for subrow, subgroup in enumerate(self.modelNomenclatureExpense.groups()):
                                if subgroup.groupingItem == self.modelNomenclatureExpense.groups()[row].groupingItem:
                                    subitems = subgroup.items
                                    if forceRef(subgroup.headItem.action._record.value('id')):
                                        if subrow in rows:
                                            rows.remove(subrow)
                                        params = dialog.getCancelActionParams()
                                        cancelDateTime = params.get('cancelDateTime', None)
                                        canceledDateTime = params.get('canceledDateTime', None)
                                        reaction = params.get('reaction', False)
                                        if reaction:
                                            recordIntoleranceMedicament = tblClientIntoleranceMedicament.newRecord()
                                            activeSubstance = params.get('activeSubstance', None)
                                            recordIntoleranceMedicament.setValue('activeSubstance_id', activeSubstance)
                                            reactionType = params.get('reactionType', None)
                                            recordIntoleranceMedicament.setValue('reactionType_id', reactionType)
                                            reactionManifestation = params.get('reactionManifestation', None)
                                            recordIntoleranceMedicament.setValue('reactionManifestation_id', reactionManifestation)
                                            power = params.get('power', 0)
                                            recordIntoleranceMedicament.setValue('power', power)
                                            notes = params.get('notes', '')
                                            recordIntoleranceMedicament.setValue('notes', notes)
                                            recordIntoleranceMedicament.setValue('createDate', toVariant(canceledDateTime))
                                        for i in range(len(subitems)):
                                            if forceInt(subitems[i].action._record.value('status')) !=2:
                                                subitems[i].action._record.setValue('status', toVariant(CActionStatus.canceled))
                                                if cancelDateTime:
                                                    subitems[i].action._record.setValue('begDate', toVariant(cancelDateTime))
                                                    subitems[i].action._record.setValue('endDate', toVariant(QDate()))
                                                if canceledDateTime:
                                                    subitems[i].action.setCancelDatePropertyValue(canceledDateTime)
                                                if reaction:
                                                    if activeSubstance:
                                                        reactionTypeName = u''
                                                        reactionManifestationName = u''
                                                        powerName = u''
                                                        activeSubstanceRecord = db.getRecordEx(tableActiveSubstance, [tableActiveSubstance['name']], [tableActiveSubstance['id'].eq(activeSubstance)])
                                                        activeSubstanceName = forceStringEx(activeSubstanceRecord.value('name')) if activeSubstanceRecord else u''
                                                        if reactionType:
                                                            reactionTypeRecord = db.getRecordEx(tableReactionType, [tableReactionType['name']], [tableReactionType['id'].eq(reactionType)])
                                                            reactionTypeName = forceStringEx(reactionTypeRecord.value('name')) if reactionTypeRecord else u''
                                                        if reactionManifestation:
                                                            reactionManifestationRecord = db.getRecordEx(tableReactionManifestation, [tableReactionManifestation['name']], [tableReactionManifestation['id'].eq(reactionManifestation)])
                                                            reactionManifestationName = forceStringEx(reactionManifestationRecord.value('name')) if reactionManifestationRecord else u''
                                                        if power >= 0:
                                                            powerName = [u'0 - не известно', u'1 - малая', u'2 - средняя', u'3 - высокая', u'4 - строгая'][power]
                                                        reactionNotes = u'''ДВ: %s, Тип реакции: %s, Проявление реакции: %s, Степень: %s, Примечание: %s.'''%(activeSubstanceName, reactionTypeName, reactionManifestationName, powerName, notes)
                                                    elif notes:
                                                        reactionNotes = notes
                                                    subitems[i].action.setReactionPropertyValue(reactionNotes)
                                                subitems[i].action.cancel()
                                        self.modelNomenclatureExpense.setOriginGroups(self.modelNomenclatureExpense._originGroups)
                                        self.modelNomenclatureExpense.emitAllDataChanged()
                                        if recordIntoleranceMedicament:
                                            self.clientIntoleranceMedicamentRecords.append(recordIntoleranceMedicament)
                    finally:
                        dialog.deleteLater()
        self.setIsDirty(True)

    
    def getClientIntoleranceMedicamentRecords(self):
        return self.clientIntoleranceMedicamentRecords
    
    
    @staticmethod
    def saveClientIntoleranceMedicamentRecords(records = [], client_id = None):
        if not client_id or not records:
            return
        
        db = QtGui.qApp.db
        db.transaction()
        try:
            tblClientIntoleranceMedicament = db.table('ClientIntoleranceMedicament')
            for record in records:
                record.setValue('client_id', client_id)
                db.insertOrUpdate(tblClientIntoleranceMedicament, record)
            db.commit()
        except:
            db.rollback()
            raise
        
#    def on_actDeleteRows_triggered(self):
#        rows = self.getSelectedRows()
#        for row in reversed(rows):
#            if row <= len(self.modelNomenclatureExpense.groups()):
#                headAction = self.modelNomenclatureExpense.groups()[row].headItem.action
#                if forceRef(headAction._record.value('id')):
#                    res = QtGui.QMessageBox.warning( self,
#                        u'Внимание!',
#                        u'Данное назначение можно только отменить. Отменить назначение?',
#                        QtGui.QMessageBox.Ok|QtGui.QMessageBox.Cancel,
#                        QtGui.QMessageBox.Cancel)
#                    if res == QtGui.QMessageBox.Ok:
#                        items = self.modelNomenclatureExpense.groups()[row].items
#                        for i in range(len(items)):
#                            if forceInt(items[i].action._record.value('status')) !=2:
#                                items[i].action._record.setValue('status', toVariant(CActionStatus.canceled))
#                                items[i].action.cancel()
#                        self.modelNomenclatureExpense.setOriginGroups(self.modelNomenclatureExpense._originGroups)
#                        self.modelNomenclatureExpense.emitAllDataChanged()
#                    else:
#                        return False
#                else:
#                    group = self.modelNomenclatureExpense.groups()[row]
#                    self.removeNewGroupRows(row, self.modelNomenclatureExpense.rowCount()-1,  group)
#                    self.modelNomenclatureExpense.emitAllDataChanged()
#        self.setIsDirty(True)


    @pyqtSignature('')
    def on_actCalculationDoseNomenclature_triggered(self):
        self.setIsDirty(True)
        templateIdList = {}
        if self.tblNomenclatureExpense.isNomenclatureExpensePopupMenuEnabled():
            selectedIndexes = self.tblNomenclatureExpense.selectedIndexes()
            if selectedIndexes:
                selectedRows = []
#                model = self.tblNomenclatureExpense.model()
                for index in self.tblNomenclatureExpense.selectedIndexes():
                    if index and index.isValid() and not self.modelNomenclatureExpense.existsDoneByIndex(index):
                        row = index.row()
                        if 0 <= row < len(self.modelNomenclatureExpense._groups) and row not in selectedRows:
                            selectedRows.append(row)
                            group = self.modelNomenclatureExpense._groups[row]
                            if group:
                                templateId = self.modelNomenclatureExpense._cellsSettings.getGroupCalculationParam(group)
                                if templateId:
                                    items = self.modelNomenclatureExpense._cellsSettings.getValuePropertyToTemplateItems(group)
                                    if not items:
                                        items = self.modelNomenclatureExpense.getCalculationParamValueProperties()
                                        self.modelNomenclatureExpense._cellsSettings.setValuePropertyToTemplateItems(group, items)
                                    paramLine = self.modelNomenclatureExpense._cellsSettings.getValuePropertyToTemplate(group, templateId)
                                    calculationParam = paramLine[0] if len(paramLine) > 0 else 0
                                    if calculationParam > 0:
                                        self.modelNomenclatureExpense.calculationDosageByIndex(index, calculationParam)
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
                                            action = group.headItem.action
                                            if action:
                                                if action.executionPlanManager.hasItemsToDo():
                                                    if action.getType().isNomenclatureExpense:
                                                        action.updateDosageFromExecutionPlan()
                                                    action.updateSpecifiedName()
                                        self.modelNomenclatureExpense.emitRowDataChanged(row)
                                        self.modelNomenclatureExpense.emitAllDataChanged()
                                    else:
                                        nomenclatureList = templateIdList.get(templateId, [])
                                        nomenclatureName = self.modelNomenclatureExpense._cellsSettings.getGroupNomenclatureText(group)
                                        nomenclatureNameList = nomenclatureName.split(u'|')
                                        nomenclatureNameStr = nomenclatureNameList[0]
                                        nomenclatureList.append(nomenclatureNameStr if nomenclatureNameStr else self.modelNomenclatureExpense._cellsSettings.getGroupSmnnText(group))
                                        templateIdList[templateId] = nomenclatureList
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


    @pyqtSignature('')
    def on_actShowAllOrgStructureAssignment_triggered(self):
        if self.tblNomenclatureExpense.isNomenclatureExpensePopupMenuEnabled():
            index = self.tblNomenclatureExpense.currentIndex()
            if index and index.isValid():
                row = index.row()
            if 0 <= row < len(self.modelNomenclatureExpense._groups):
                group = self.modelNomenclatureExpense._groups[row]
                if group:
                    action = group.headItem[1]
                    if action:
                        record = action.getRecord()
                        orgStructureId = forceRef(record.value('orgStructure_id'))
                        if orgStructureId:
                            self.cmbOrgStructure.setValue(orgStructureId)


    @pyqtSignature('')
    def on_actUpdateDoseNomenclature_triggered(self):
        self.setIsDirty(True)
        if self.tblNomenclatureExpense.isNomenclatureExpensePopupMenuEnabled():
            selectedIndexes = self.tblNomenclatureExpense.selectedIndexes()
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
                    for index in self.tblNomenclatureExpense.selectedIndexes():
                        if index and index.isValid() and not self.modelNomenclatureExpense.existsDoneByIndex(index):
                            row = index.row()
                            if 0 <= row < len(self.modelNomenclatureExpense._groups) and row not in selectedRows:
                                selectedRows.append(row)
                                group = self.modelNomenclatureExpense._groups[row]
                                if group:
                                    self.modelNomenclatureExpense.updateDosageToProcentByIndex(index, procent, change)
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
                                        action = group.headItem.action
                                        if action:
                                            if action.executionPlanManager.hasItemsToDo():
                                                if action.getType().isNomenclatureExpense:
                                                    action.updateDosageFromExecutionPlan()
                                                action.updateSpecifiedName()
                                    self.modelNomenclatureExpense.emitRowDataChanged(row)
                                    self.modelNomenclatureExpense.emitAllDataChanged()


    def on_extendAppointmentNomenclature(self):
        self.setIsDirty(True)
        dialog = CExtendAppointmentNomenclatureDialog(self)
        try:
            if dialog.exec_():
                extendParametrs = dialog.getExtendParametrs()
                quantityDay = forceInt(extendParametrs.get('quantityDay', 0))
                skipAfterLastDayCourse = forceInt(extendParametrs.get('skipAfterLastDayCourse', 0))
                isLastDayCourse = forceBool(extendParametrs.get('isLastDayCourse', False))
                index = self.tblNomenclatureExpense.currentIndex()
                if index.isValid() and quantityDay > 0:
                    self.tblNomenclatureExpense.model().setDurationForDayIndex(index, quantityDay, skipAfterLastDayCourse=skipAfterLastDayCourse, isLastDayCourse=isLastDayCourse)
                    self.tblNomenclatureExpense.model().reset()
        finally:
            dialog.deleteLater()


    def removeNewGroupRows(self, row, count, group, parentIndex = QModelIndex()):
        self.setIsDirty(True)
        self.modelNomenclatureExpense.beginRemoveRows(parentIndex, row, count)
        if group in self.modelNomenclatureExpense._newGroups:
            groupRow = self.modelNomenclatureExpense._newGroups.index(group)
            if groupRow >= 0 and groupRow < len(self.modelNomenclatureExpense._newGroups):
                del self.modelNomenclatureExpense._newGroups[groupRow]
                if group not in self.groupsDeleted:
                    self.groupsDeleted.append(group)
        if group in self.modelNomenclatureExpense._groups:
            groupRow = self.modelNomenclatureExpense._groups.index(group)
            if groupRow >= 0 and groupRow < len(self.modelNomenclatureExpense.groups()):
                del self.modelNomenclatureExpense._groups[groupRow]
                if group not in self.groupsDeleted:
                    self.groupsDeleted.append(group)
        if group in self.modelNomenclatureExpense._originGroups:
            groupRow = self.modelNomenclatureExpense._originGroups.index(group)
            if groupRow >= 0 and groupRow < len(self.modelNomenclatureExpense._originGroups):
                del self.modelNomenclatureExpense._originGroups[groupRow]
                if group not in self.groupsDeleted:
                    self.groupsDeleted.append(group)
        self.modelNomenclatureExpense.endRemoveRows()
        self.modelNomenclatureExpense.setOriginGroups(self.modelNomenclatureExpense._groups)


    def getOrgStructureId(self):
        return self.cmbOrgStructure.value()
    
    
    def nomenclatureGroupingRows(self, rows):
        model = self.tblNomenclatureExpense.model()
        for proxyRow in rows:
            group = model._groups[proxyRow]
            if group.isGrouped() and group.groupingItem != group.currentItem:
                for subrow in rows:
                    if model._groups[subrow].currentItem and model._groups[subrow].currentItem == group.groupingItem:
                        return True
                QtGui.QMessageBox().warning(self,
                            u'Предупреждение!',
                            u'Невозможно добавить действие без группирующего действия.',
                            QtGui.QMessageBox.Ok,
                            QtGui.QMessageBox.Ok)
                return False
        return True


    def on_chkPeriodClicked(self, v=None):
        self.modelNomenclatureExpense.considerPeriod(self.chkPeriod.isChecked())


    @pyqtSignature('QModelIndex')
    def on_tblNomenclatureExpense_doubleClicked(self, index):
        if self.tblNomenclatureExpense.model().isReadOnly():
            return
        if index and index.isValid() and not self.modelNomenclatureExpense.existsDoneByIndex(index):
            self.setIsDirty(True)
            col = index.column()
            currentRow = index.row()
            isOpenDialog = col in (SMNN_INDEX, SMNN_GRLSLF_INDEX) and (0 <= currentRow < len(self.modelNomenclatureExpense._groups) or (self.cmbOrgStructure.value() and currentRow == len(self.modelNomenclatureExpense._groups)))
            if isOpenDialog:
                if 0 <= currentRow < len(self.modelNomenclatureExpense._groups):
                    currentGroup = self.modelNomenclatureExpense._groups[currentRow]
                    if self.modelNomenclatureExpense._cellsSettings.getGroupNomenclature(currentGroup) and not currentGroup.isDirty() and (currentGroup.hasSavedItems() or currentGroup.hasExecutedItems()):
                        isOpenDialog = False
                if isOpenDialog:
                    model = self.tblNomenclatureExpense.model()
                    dialog = CSmnnGrlsLfNomenclatureExpenseEditor(self)
                    try:
                        dialog.setIsType(1 if col == SMNN_GRLSLF_INDEX else 0)
                        dialog.setOnlySmnnUUID(True)
                        actionTypeId = self.cmbActionType.value()
                        actionType = CActionTypeCache.getById(actionTypeId) if actionTypeId else None
                        dialog.setOnlyExists(actionType.isNomenclatureExpense if actionType else True)
                        nomenclatureId = None
                        smnnUUID = None
                        dialog.setOrgStructureId(self.modelNomenclatureExpense._stockOrgStructureId if self.modelNomenclatureExpense._stockOrgStructureId else QtGui.qApp.currentOrgStructureId())
                        group = None
                        if 0 <= currentRow < len(model._groups):
                            group = model._groups[currentRow]
                        if group:
                            nomenclatureId = self.modelNomenclatureExpense._cellsSettings.getGroupNomenclature(group)
                            smnnUUID = self.modelNomenclatureExpense._cellsSettings.getGroupSmnn(group)
                            dialog.setUUID(self.modelNomenclatureExpense._cellsSettings.getGroupSmnn(group))
                            dialog.setLfFormId(self.modelNomenclatureExpense._cellsSettings.getGroupSmnnGrlsLf(group))
                        dialog.setNomenclatureId(nomenclatureId)
                        if QtGui.qApp.controlSMFinance() in (1, 2):
                            dialog.setFinanceId(self.getFinanceId())
                        dialog.setNomenclatureSmnnUUID(smnnUUID)
                        if not QtGui.qApp.userHasRight(urEditChkOnlyExistsNomenclature):
                            dialog.setOnlyExistsEnabled(False)
                        dialog.on_buttonBox_apply()
                        if dialog.exec_():
                            UUID, lfFormId = dialog.getValue()
                            if UUID:
                                if currentRow == len(model._groups):
                                    group = None
                                    orgStructureId = self.getOrgStructureId()
                                    self.modelNomenclatureExpense._addNewGroup(None, orgStructureId)
                                    if 0 <= currentRow < len(self.modelNomenclatureExpense._groups):
                                        group = self.modelNomenclatureExpense._groups[currentRow]
                                if group:
                                    group.setSmnnUUID(UUID, updateExecutionPlan=False)
                                    group.setLfFormId(lfFormId, updateExecutionPlan=False)
                                    self.modelNomenclatureExpense._cellsSettings.setGroupSmnn(group, UUID)
                                    self.modelNomenclatureExpense._cellsSettings.setGroupSmnnGrlsLf(group, lfFormId)
                                    self.modelNomenclatureExpense.reset()
                    finally:
                        dialog.deleteLater()
                else:
                    self.emit(SIGNAL('doubleClicked(QModelIndex)'), index)


    @pyqtSignature('')
    def on_btnReset_pressed(self):
        actionTypeId = self.cmbActionType.value()
        actionType = CActionTypeCache.getById(actionTypeId)
        orgStructureId = actionType.getNomenclatureOrgStructureId()
        if not orgStructureId:
            self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())
        self.cmbNomenclature.setValue(None)
        self.chkPeriod.setChecked(False)
        self.chkActual.setChecked(True)
        self.chkIgnoreTime.setChecked(True)
        self.chkRequiresFillingNomenclature.setChecked(False)
        self.cmbSchema.setValue(None)
        currentDate = QtCore.QDate.currentDate()
        self.edtYear.setValue(currentDate.year())
        self.cmbMonth.setCurrentIndex(currentDate.month()-1)


    @pyqtSignature('')
    def on_btnSaveTemplate_pressed(self):
        """
        Обработчик кнопки 'Сохранить шаблон'
        Собираем данные о ВЫДЕЛЕННЫХ элементах в таблице действий и отправляем их в редактор шаблона.
        После сохранения шаблона обновляем таблицу ActionTypeGroup_Plan_Item
        """
        actionTypeId = self.cmbActionType.value()
        if actionTypeId:
            db = QtGui.qApp.db
            tableAT = db.table('ActionType')
            recordAT = db.getRecordEx(tableAT, [tableAT['class']], [tableAT['id'].eq(actionTypeId), tableAT['deleted'].eq(0)])
            if recordAT:
                groupsList = []
                rows = []
                table = db.table('ActionTypeGroup_Item')
                model = self.tblNomenclatureExpense.model()
                selectedRows = self.getSelectedRows()
                if not self.nomenclatureGroupingRows(selectedRows):
                    return False
                for row in selectedRows:
                    if 0 <= row < len(model._groups):
                        if row not in rows:
                            rows.append(row)
                            groupsList.append(model._groups[row])
                groupsList.sort(key=lambda x: forceDate(x.headItem.action.getRecord().value('begDate')))
                offsetDate = forceDate(groupsList[0].headItem.action.getRecord().value('begDate')) if len(groupsList) > 0 else None
                actionsList = []
                for groupIdx, groups in enumerate(groupsList):
                    action = groups.headItem.action
                    record = action.getRecord()
                    if action:
                        nomenclatureId = self.modelNomenclatureExpense._cellsSettings.getGroupNomenclature(groups)
                        smnnUUID = self.modelNomenclatureExpense._cellsSettings.getGroupSmnn(groups)
                        smnnGrlsLfId = self.modelNomenclatureExpense._cellsSettings.getGroupSmnnGrlsLf(groups)
                        actionPropertyTemplateId = self.modelNomenclatureExpense._cellsSettings.getGroupCalculationParam(groups)
                        if nomenclatureId or (smnnUUID and smnnGrlsLfId):
                            begDate = forceDate(record.value('begDate'))
                            offset = offsetDate.daysTo(begDate) if offsetDate else 0
                            newRecord = table.newRecord()
                            newRecord.setValue('actionType_id', actionTypeId)
                            newRecord.setValue('orgStructure_id', toVariant(self.cmbOrgStructure.value()))
                            propertyType = self.modelNomenclatureExpense._cellsSettings.getGroupSmnnPT(groups)
                            if propertyType and propertyType.isNomenclatureSmnnActionPropertyValueType():
                                newRecord.setValue('smnnUUID', toVariant(smnnUUID))
                            propertyType = self.modelNomenclatureExpense._cellsSettings.getGroupSmnnGrlsLfPT(groups)
                            if propertyType and propertyType.isNomenclatureSmnnGrlsLfActionPropertyValueType():
                                newRecord.setValue('lfForm_id', toVariant(smnnGrlsLfId))
                            propertyType = self.modelNomenclatureExpense._cellsSettings.getGroupCalculationParamPT(groups)
                            if propertyType and propertyType.isNomenclatureCalculationParamActionPropertyValueType():
                                newRecord.setValue('actionPropertyTemplate_id', toVariant(actionPropertyTemplateId))
                            propertyType = self.modelNomenclatureExpense._cellsSettings.getGroupNomenclaturePT(groups)
                            if propertyType and propertyType.inActionsSelectionTable == _RECIPE:
                                newRecord.setValue('nomenclature_id', toVariant(nomenclatureId))
                            propertyType = self.modelNomenclatureExpense._cellsSettings.getGroupDosesPT(groups)
                            if propertyType and propertyType.inActionsSelectionTable == _DOSES:
                                newRecord.setValue('doses', toVariant(self.modelNomenclatureExpense._cellsSettings.getGroupDoses(groups)))
                            propertyType = self.modelNomenclatureExpense._cellsSettings.getGroupSignaPT(groups)
                            if propertyType and propertyType.inActionsSelectionTable == _SIGNA:
                                newRecord.setValue('signa', toVariant(self.modelNomenclatureExpense._cellsSettings.getGroupSigna(groups)))
                            newRecord.setValue('duration', toVariant(groups.duration()))
                            newRecord.setValue('periodicity', toVariant(groups.periodicity()))
                            newRecord.setValue('aliquoticity', toVariant(groups.aliquoticity()))
                            newRecord.setValue('offset', toVariant(offset))
                            newRecord.append(QSqlField('class', QVariant.Int)) # Для редактора шаблона нужна информация о классе добавляемого действия
                            newRecord.append(QSqlField('proxyModelIndex',QVariant.Int))  # Маппинг индекса текущего действия в редакторе шаблона. Нужен для последующей обработки плана назначения
                            newRecord.setValue('class', toVariant(recordAT.value('class')))
                            newRecord.setValue('proxyModelIndex', toVariant(groupIdx))
                            actionsList.append(newRecord)
                curTemplateId = None
                dlg = ActionTypeGroupEditor(self, curTemplateId, enableOffset=True)
                dlg.setActionTypes(actionsList)
                dlg.exec_()
                db.transaction()
                try:
                    masterIds = {}
                    for record in dlg.modelActionTypes.items():
                        id = forceRef(record.value('id'))
                        groupIdx = forceInt(record.value('extItemIndex')) if not record.isNull('extItemIndex') else None
                        if id and groupIdx is not None:
                            items = groupsList[groupIdx]._epGroup._executionPlan.items
                            if items:
                                tablePI = db.table('ActionTypeGroup_Plan_Item')
                                tablePINomenclature = db.table('ActionTypeGroup_Plan_Item_Nomenclature')
                                for item in items:
                                    idx = item.idx
                                    time = item.time
                                    date = item.date
                                    dateIdx = (begDate.daysTo(item.date) + 1) if begDate != date else 1
                                    newRecordPI = tablePI.newRecord()
                                    newRecordPI.setValue('master_id', toVariant(id))
                                    newRecordPI.setValue('idx', toVariant(idx))
                                    newRecordPI.setValue('date_idx', toVariant(dateIdx))
                                    newRecordPI.setValue('time', toVariant(time))
                                    if item.groupId != item.id and item.groupId in masterIds.keys():
                                        newRecordPI.setValue('group_id', forceInt(masterIds[item.groupId]))
                                    planItemId = db.insertRecord(tablePI, newRecordPI)
                                    newRecordPI.setValue('id', planItemId)
                                    if item.groupId == item.id:
                                        newRecordPI.setValue('group_id', planItemId)
                                        db.updateRecord(tablePI, newRecordPI)
                                        masterIds[item.id] = planItemId
                                    if planItemId and item.nomenclature:
                                        doses = item.nomenclature.dosage
                                        nomenclatureId = item.nomenclature.nomenclatureId
                                        newRecordPIN = tablePINomenclature.newRecord()
                                        newRecordPIN.setValue('master_id', toVariant(planItemId))
                                        newRecordPIN.setValue('nomenclature_id', toVariant(nomenclatureId))
                                        newRecordPIN.setValue('dosage', toVariant(doses))
                                        db.insertRecord(tablePINomenclature, newRecordPIN)
                except:
                    db.rollback()
                    raise
                else:
                    db.commit()
            dlg.deleteLater()


    @pyqtSignature('')
    def on_btnLoadTemplate_pressed(self):
        self.setIsDirty(True)
        actionTypeId = self.cmbActionType.value()
        if actionTypeId:
            db = QtGui.qApp.db
            tableAT = db.table('ActionType')
            record = db.getRecordEx(tableAT, [tableAT['class']], [tableAT['id'].eq(actionTypeId), tableAT['deleted'].eq(0)])
            if record:
                dlg = CNomenclatureExpenseLoadTemplate(self, self._eventEditor, self._eventEditor.eventTypeId, forceInt(record.value('class')))
                dlg.setOrgStructureId(self.cmbOrgStructure.value())
                dlg.setActionTypeId(actionTypeId)
                if dlg.exec_():
                    db.transaction()
                    notCalculationParamTemplateIdList = {}
                    try:
                        actions = dlg.getSelectedList()
                        for action in actions:
                            notCalculationParamTemplateIdList = self.modelNomenclatureExpense._addNewGroupFromTemplate(action, notCalculationParamTemplateIdList)
                            if hasattr(action.executionPlanManager.currentItem, 'groupingItem'):
                                if action.executionPlanManager.currentItem.groupingItem[1]:
                                    action.executionPlanManager.currentItem.groupingItem = None
                                    action.executionPlanManager.groupingItem = action.executionPlanManager.currentItem
                                    action.executionPlanManager.groupingInfo.append(action.executionPlanManager.currentItem)
                                else:
                                    for subaction in actions:
                                        if subaction.executionPlanManager.currentItem.groupingItem and subaction.executionPlanManager.currentItem.groupingItem[1] and subaction.executionPlanManager.currentItem.groupingItem[0] == action.executionPlanManager.currentItem.groupingItem[0] \
                                            or subaction.executionPlanManager.groupingItem and subaction.executionPlanManager.groupingInfo:
                                                action.executionPlanManager.groupingItem = subaction.executionPlanManager.currentItem
                                                subaction.executionPlanManager.groupingInfo.append(action.executionPlanManager.currentItem)
                        if notCalculationParamTemplateIdList:
                            templateNameList = {}
                            message = u''
                            db = QtGui.qApp.db
                            tableAPT = db.table('ActionPropertyTemplate')
                            records = db.getDistinctRecordList(tableAPT, [tableAPT['id'], tableAPT['name']], [tableAPT['id'].inlist(notCalculationParamTemplateIdList.keys())], order = tableAPT['name'].name())
                            for record in records:
                                templateNameList[forceRef(record.value('id'))] = forceString(record.value('name'))
                            for templateId, nomenclatureNameList in notCalculationParamTemplateIdList.items():
                                nomenclatureNames = u'<br>'.join(nomenclatureName for nomenclatureName in nomenclatureNameList)
                                message += u'''Невозможно рассчитать дозу для ЛС:<br><b>%s</b><br>в связи с тем, что не определено значение параметра расчета <b>%s</b> для пациента.<br><br>'''%(nomenclatureNames, templateNameList.get(templateId, u''))
                            if message:
                                button = QtGui.QMessageBox.Ok
                                QtGui.QMessageBox.warning(None,
                                                          u'Внимание!',
                                                          message,
                                                          button,
                                                          QtGui.QMessageBox.Ok)
                        self.updateSchemaItems()
                    except:
                        db.rollback()
                        raise
                    else:
                        db.commit()
            dlg.deleteLater()


    @pyqtSignature('QDate')
    def on_edtBegDate_dateChanged(self, date):
        self.setIsDirty(True)
        self.modelNomenclatureExpense.setBegDate(date)


    @pyqtSignature('QDate')
    def on_edtEndDate_dateChanged(self, date):
        self.setIsDirty(True)
        self.modelNomenclatureExpense.setEndDate(date)


    @pyqtSignature('int')
    def on_cmbOrgStructure_currentIndexChanged(self, index):
        self.setIsDirty(True)
        orgStructureId = self.cmbOrgStructure.value()
        self.cmbNomenclature.setOrgStructureId(orgStructureId)
        self.modelNomenclatureExpense.setOrgStructureId(orgStructureId)
        self.btnSaveTemplate.setEnabled(bool(orgStructureId) and (QtGui.qApp.userHasRight(urAdmin) or QtGui.qApp.userHasRight(urCanCreateNewActionTypeGroup)) and (not self.isHBDialog or (self.isHBDialog and QtGui.qApp.userHasRight(urHBEditEvent))))
        self.btnLoadTemplate.setEnabled(bool(orgStructureId) and (not self.isHBDialog or (self.isHBDialog and QtGui.qApp.userHasRight(urHBEditEvent))))


    def on_nomenclatureExpenseSelectionChanged(self, i1, i2):
        self.selectionModelNomenclatureExpenseDays.clearSelection()


    def on_nomenclatureExpenseDaysSelectionChanged(self, i1, i2):
        self.selectionModelNomenclatureExpense.clearSelection()


    def _hideDaysColumns(self, tbl):
        header = tbl.horizontalHeader()
        start = tbl.model().lastMainIndex + 1
        self._hideHeaderColumns(header, start, header.count())


    def _hideMainColumns(self, tbl):
        header = tbl.horizontalHeader()
        stop = tbl.model().lastMainIndex + 1
        self._hideHeaderColumns(header, 0, stop)


    @staticmethod
    def _hideHeaderColumns(header, start, stop):
        for i in range(start, stop):
            header.setSectionHidden(i, True)


    @property
    def eventEditor(self):
        return self._eventEditor


    def setEventEditor(self, eventEditor):
        self._eventEditor = eventEditor
        self.modelNomenclatureExpense.setEventEditor(eventEditor)
        self.modelNomenclatureExpense.getCalculationParamValueProperties()


    def on_chkActualClicked(self, value):
        self.modelNomenclatureExpense.setOnlyActual(value)


    def on_chkIgnoreTimeClicked(self, value):
        self.modelNomenclatureExpense.setIgnoreTime(value)


    def on_cmbMonthIndexChanged(self, monthIndex):
        month = monthIndex + 1
        year = self.edtYear.value()
        self._updateModelDate(year, month)
        self._hideDaysColumns(self.tblNomenclatureExpense)


    def on_edtYearValueChanged(self, year):
        month = self.cmbMonth.currentIndex()+1
        self._updateModelDate(year, month)
        self._hideDaysColumns(self.tblNomenclatureExpense)


    def _updateModelDate(self, year, month):
        date = QtCore.QDate(year, month, 1)
        date = QtCore.QDate(year, month, date.daysInMonth())
        self.modelNomenclatureExpense.setDate(date)


    def setCmbActionTypeFilter(self):
        db = QtGui.qApp.db
        table = db.table('ActionType')
        idList = getNomenclatureActionTypesIds()
        descendants = []
        for id in idList:
            descendants.extend(db.getDescendants(table, 'group_id', id))
        idList = db.getTheseAndParents(table, 'group_id', descendants)
        self.cmbActionType.setEnabledActionTypeIdList(idList)


    def exec_(self):
        if not self.isDirty():
            if self.modelNomenclatureExpense.isDirty():
                self.setIsDirty(True)
            else:
                for row, group in enumerate(self.modelNomenclatureExpense._groups):
                    if group.isDirty():
                        self.setIsDirty(True)
                        break
        return CDialogBase.exec_(self)


    def on_cmbNomenclatureIndexChanged(self, index=None):
        nomenclatureId = self.cmbNomenclature.value()
        self.modelNomenclatureExpense.setNomenclatureId(nomenclatureId)


    def on_chkRequiresFillingNomenclatureClicked(self, value):
        self.modelNomenclatureExpense.setIsRequiresFillingNomenclature(value)


    def on_cmbSchemaClicked(self, value):
        self.modelNomenclatureExpense.setSchemaId(self.cmbSchema.value())


    def getActionTypeGroupIdListToSchema(self, schemaActionTypeId):
        actionTypeGroupIdList = []
        if schemaActionTypeId:
            model = self.tblNomenclatureExpense.model()
            for row, group in enumerate(model._groups):
                action = group.headItem.action
                record = action.getRecord()
                actionTypeId = forceRef(record.value('actionType_id')) if record else None
                if actionTypeId == schemaActionTypeId:
                    actionTypeGroupId = forceRef(record.value('actionTypeGroup_id'))
                    if actionTypeGroupId and actionTypeGroupId not in actionTypeGroupIdList:
                        actionTypeGroupIdList.append(actionTypeGroupId)
        return actionTypeGroupIdList


    def on_cmbActionTypeIndexChanged(self, index=None):
        actionTypeId = self.cmbActionType.value()
        if actionTypeId:
            actionType = CActionTypeCache.getById(actionTypeId)
            orgStructureId = actionType.getNomenclatureOrgStructureId()
        else:
            actionType = None
            orgStructureId = None
        if orgStructureId:
            self.cmbOrgStructure.setValue(orgStructureId)
            self.cmbOrgStructure.setReadOnly(True)
        else:
            defaults = _getDefaultValues()
            orgStructureId = defaults['orgStructureId']
            self.cmbOrgStructure.setValue(orgStructureId if orgStructureId else QtGui.qApp.currentOrgStructureId())
            self.cmbOrgStructure.setReadOnly(False)
        for wgt in self._cmbActionTypeWidgetsDependets:
            wgt.setEnabled(bool(actionTypeId))
        self.modelNomenclatureExpense.setActionTypeId(actionTypeId)
        self.chkPeriod.emit(SIGNAL('clicked(bool)'), self.chkPeriod.isChecked() and bool(actionTypeId))
        self.updateSchemaItems()
        if actionTypeId:
            self.cmbNomenclature.setOnlyExists(actionType.isNomenclatureExpense)
            isSMNN = False
            for propertyType in actionType.getPropertiesById().values():
                if propertyType.isNomenclatureSmnnActionPropertyValueType() or propertyType.isNomenclatureSmnnGrlsLfActionPropertyValueType():
                    isSMNN = True
                    break
            self.tblNomenclatureExpense.setHideSections([] if isSMNN else [SMNN_INDEX, SMNN_GRLSLF_INDEX])


    def updateSchemaItems(self):
        actionTypeId = self.cmbActionType.value()
        filter = u'0'
        templateIdList = []
        db = QtGui.qApp.db
        tableATG = db.table('ActionTypeGroup')
        if actionTypeId:
            actionTypeGroupIdList = self.getActionTypeGroupIdListToSchema(actionTypeId)
            if actionTypeGroupIdList:
                tableATGItems = db.table('ActionTypeGroup_Item')
                queryTable = tableATG.innerJoin(tableATGItems, tableATGItems['master_id'].eq(tableATG['id']))
                templateIdList = db.getDistinctIdList(queryTable, [tableATG['id']], [tableATG['id'].inlist(actionTypeGroupIdList), tableATGItems['actionType_id'].eq(actionTypeId), tableATGItems['deleted'].eq(0), tableATG['deleted'].eq(0)], [tableATG['code'].name(), tableATG['name'].name()])
                if templateIdList:
                    filter = tableATG['id'].inlist(templateIdList)
        self.cmbSchema.setTable(tableATG.name(), filter=filter)
        self.cmbSchema.setValue(None)


    def done(self, result):
        defaults = {
            'actionTypeId': self.cmbActionType.value(),
            'nomenclatureId': self.cmbNomenclature.value(),
            'begDate': str(self.edtBegDate.date().toString('yyyy.MM.dd')),
            'endDate': str(self.edtEndDate.date().toString('yyyy.MM.dd')),
            'year': self.edtYear.value(),
            'month': self.cmbMonth.currentIndex(),
            'period': self.chkPeriod.isChecked(),
            'actual': self.chkActual.isChecked(),
            'ignoreTime': self.chkIgnoreTime.isChecked(),
            'isRequiresFillingNomenclature': self.chkRequiresFillingNomenclature.isChecked(),
            'schemaId': self.cmbSchema.value(),
            'currentEvent': self.chkCurrentEvent.isChecked(),
            'orgStructureId': self.cmbOrgStructure.value()
        }

        defaults = json.dumps(defaults)

        QtGui.qApp.preferences.appPrefs['NomenclatureExpenseDialogDefaultValues'] = defaults
        self.saveDialogPreferences()
        preferences = self.tblNomenclatureExpense.savePreferences()
        setPref(QtGui.qApp.preferences.windowPrefs, 'CNomenclatureExpenseDialog_tblNomenclatureExpense', preferences)
        preferencesDays = self.tblNomenclatureExpenseDays.savePreferences()
        setPref(QtGui.qApp.preferences.windowPrefs, 'CNomenclatureExpenseDialog_tblNomenclatureExpenseDays', preferencesDays)

        return CDialogBase.done(self, result)


    def checkDataEntered(self):
        result = True
        if QtGui.qApp.controlFillingFieldsNomenclatureExpense():
            for row, group in enumerate(self.modelNomenclatureExpense._groups):
                begDate = forceDate(group.begDate())
                directionDate = forceDate(group.directionDate())
                smnnUUID = self.modelNomenclatureExpense._cellsSettings.getGroupSmnn(group)
                smnnGrlsLfId = self.modelNomenclatureExpense._cellsSettings.getGroupSmnnGrlsLf(group)
                nomenclatureId = self.modelNomenclatureExpense._cellsSettings.getGroupNomenclature(group)
                doses = self.modelNomenclatureExpense._cellsSettings.getGroupDoses(group)
                duration = group.duration()
                aliquoticity = group.aliquoticity()
                result = result and (nomenclatureId or (smnnUUID and smnnGrlsLfId) or self.checkInputMessage(u'ЛС', False, self.tblNomenclatureExpense, row, NOMENCLATURE_INDEX))
                result = result and (doses or (smnnUUID and smnnGrlsLfId) or self.checkInputMessage(u'Дозу', False, self.tblNomenclatureExpense, row, DOSES_INDEX))
                result = result and (duration or self.checkInputMessage(u'Длительность', False, self.tblNomenclatureExpense, row, DURATION_INDEX))
                result = result and (aliquoticity or self.checkInputMessage(u'Кратность', False, self.tblNomenclatureExpense, row, ALIQUOTICITY_INDEX))
                result = result and (directionDate or self.checkInputMessage(u'Дату назначения', False, self.tblNomenclatureExpense, row, DIREACTION_DATE_INDEX))
                result = result and (begDate or self.checkInputMessage(u'Дату начала', False, self.tblNomenclatureExpense, row, BEG_DATE_INDEX))
                result = result and (begDate >= directionDate or self.checkValueMessage(u'"Дата начала" не может быть меньше "Даты назначения"!', False, self.tblNomenclatureExpense, row, BEG_DATE_INDEX))
        result = result and self.checkActionsData()
        return result


    def checkActionsData(self):
        result = True
        if self._eventEditor:
            showTime = getEventShowTime(self._eventEditor.eventTypeId)
            if showTime:
                begDate = QDateTime(self._eventEditor.edtBegDate.date(), self._eventEditor.edtBegTime.time())
                endDate = QDateTime(self._eventEditor.edtEndDate.date(), self._eventEditor.edtEndTime.time())
            else:
                begDate = self._eventEditor.edtBegDate.date()
                endDate = self._eventEditor.edtEndDate.date()
            for row, group in enumerate(self.modelNomenclatureExpense._groups):
                for rowItem, item in enumerate(group.items[::-1] if group._reversedItems else group.items):
                    if item:
                        if item.action and item.action.getType().isNomenclatureExpense:
                            result = result and self.checkActionsNEDateEnteredActuality(begDate, endDate, item.action, row)
                            result = result and self.checkActionsNEDataEntered(begDate, endDate, item.action, row)
        return result


    def checkActionsNEDateEnteredActuality(self, begDate, endDate, action, row):
        result = True
        db = QtGui.qApp.db
        table = db.table('EventType_Action')
        tableActionType = db.table('ActionType')
        cols = [table['actuality']]
        record = action.getRecord()
        if action and action._actionType.id:
            showTime = action._actionType.showTime and getEventShowTime(self._eventEditor.eventTypeId)
            forceDateOrDateTime = forceDateTime if showTime else forceDate
            rowEndDate = forceDateOrDateTime(record.value('endDate'))
            rowEndDateToCompare = self._eventEditor._date2StringToCompare(rowEndDate)
            if rowEndDate:
                actuality = None
                expirationDate = 0
                actionTypeId = action._actionType.id
                if self._eventEditor.eventTypeId and actionTypeId:
                    cond = [table['eventType_id'].eq(self._eventEditor.eventTypeId),
                            table['actionType_id'].eq(actionTypeId)
                            ]
                    recordActuality = db.getRecordEx(table, cols, cond, 'EventType_Action.eventType_id')
                    if recordActuality:
                        actuality = forceInt(recordActuality.value(0))
                if not actuality and actionTypeId:
                    recordExpirationDate = db.getRecordEx(tableActionType, [tableActionType['expirationDate']],
                                                          [tableActionType['id'].eq(actionTypeId),
                                                           tableActionType['deleted'].eq(0)])
                    if recordExpirationDate:
                        expirationDate = forceInt(recordExpirationDate.value(0))
                        if expirationDate and not actuality:
                            actuality = expirationDate
                if actuality:
                    if endDate:
                        nextDate = endDate.addMonths(+actuality)
                        endDateToCompare = self._eventEditor._date2StringToCompare(
                            nextDate.date() if isinstance(nextDate, QDateTime) and not showTime else nextDate)
                        if rowEndDateToCompare > endDateToCompare:
                            result = result and self._eventEditor.checkValueMessage(
                                u'Дата выполнения должна быть не позже %s ( с учетом срока "годности" данных)' % forceString(
                                    endDate), True, self.tblNomenclatureExpense, row, PLAN_END_DATE, None)
                    if begDate:
                        lowDate = begDate.addMonths(-actuality)
                        lowDateToCompare = self._eventEditor._date2StringToCompare(
                            lowDate.date() if isinstance(lowDate, QDateTime) and not showTime else lowDate)
                        if rowEndDateToCompare < lowDateToCompare:
                            result = result and self._eventEditor.checkValueMessage(
                                u'Дата выполнения должна быть не раньше %s( с учетом срока "годности" данных)' % forceString(
                                    lowDate), False, self.tblNomenclatureExpense, row, PLAN_END_DATE, None)
        return result


    def checkActionsNEDataEntered(self, eventDirectionDate, eventEndDate, action, row):
        self._eventEditor.actionTypeDepositIdList = []
        actionsBeyondEvent = getEventEnableActionsBeyondEvent(self._eventEditor.eventTypeId)
        record = action.getRecord()
        if action and action._actionType.id:
            if action._actionType.id not in self._eventEditor.actionTypeDepositIdList:
                self._eventEditor.actionTypeDepositIdList.append(action._actionType.id)
            nameActionType = action._actionType.name
            status = forceInt(record.value('status'))
            actionShowTime = action._actionType.showTime
            forceDateOrDateTime = forceDateTime if actionShowTime else forceDate
            directionDate = forceDateOrDateTime(record.value('directionDate'))
            begDate = forceDateOrDateTime(record.value('begDate'))
            endDate = forceDateOrDateTime(record.value('endDate'))
            if not self._eventEditor.checkBegDateAction(row, record, action, self.tblNomenclatureExpense, None, BEG_DATE_INDEX):
                return False
            if not self._eventEditor.checkActionMKB(row, record, action, self.tblNomenclatureExpense, None):
                return False
            if not self.checkEventActionDateEntered(eventDirectionDate, eventEndDate, status, directionDate,
                                                    begDate, endDate, self.tblNomenclatureExpense,
                                                    None, None, row, 0,
                                                    nameActionType, actionShowTime=actionShowTime,
                                                    enableActionsBeyondEvent=actionsBeyondEvent):
                return False
            if not self.checkActionDataEntered(directionDate, begDate, endDate, self.tblNomenclatureExpense, None, None, None, row, 0):
                return False
            if not self.checkEventDate(directionDate, endDate, None, self.tblNomenclatureExpense, None, None, False, row, 0, enableActionsBeyondEvent=actionsBeyondEvent):
                return False
            if not self._eventEditor.checkPlannedEndDate(row, record, action, self.tblNomenclatureExpense, None, column=PLAN_END_DATE):
                return False
        return True


    def checkEventActionDateEntered(self, eventDirectionDate, eventEndDate, status, actionDirectionDate, actionBegDate,
                                    actionEndDate, widget, widgetEndDate=None, widgetBegDate=None, row=None,
                                    column=None, nameActionType=u'', actionShowTime=False, enableActionsBeyondEvent=0):
        showTime = getEventShowTime(self._eventEditor.eventTypeId) and actionShowTime
        actionDirectionDate = forceDate(actionDirectionDate)
        actionBegDate = actionBegDate if showTime else actionBegDate.date() if isinstance(actionBegDate,
                                                                                          QDateTime) else actionBegDate
        actionEndDate = actionEndDate if showTime else actionEndDate.date() if isinstance(actionEndDate,
                                                                                          QDateTime) else actionEndDate
        eventDirectionDate = eventDirectionDate if showTime else eventDirectionDate.date() if isinstance(
            eventDirectionDate, QDateTime) else eventDirectionDate
        eventEndDate = eventEndDate if showTime else eventEndDate.date() if isinstance(eventEndDate,
                                                                                       QDateTime) else eventEndDate
        actionBegDateToCompare = self._eventEditor._date2StringToCompare(actionBegDate)
        actionEndDateToCompare = self._eventEditor._date2StringToCompare(actionEndDate)
        eventDirectionDateToCompare = self._eventEditor._date2StringToCompare(eventDirectionDate)
        eventEndDateToCompare = self._eventEditor._date2StringToCompare(eventEndDate)
        result = True
        if eventDirectionDate and actionDirectionDate:
            if actionBegDate:
                result = result and (actionBegDateToCompare >= eventDirectionDateToCompare or self._eventEditor.checkValueMessage(
                    u'Дата начала действия %s не должна быть раньше даты назначения события %s' % (
                        forceString(actionBegDate), forceString(eventDirectionDate)), True, widget, row, BEG_DATE_INDEX, widgetBegDate))
            if actionEndDate:
                result = result and (actionEndDateToCompare >= eventDirectionDateToCompare or self._eventEditor.checkValueMessage(
                    u'Дата выполнения действия %s не должна быть раньше даты назначения события %s' % (
                        forceString(actionEndDate), forceString(eventDirectionDate)), True, widget, row, PLAN_END_DATE, widgetEndDate))
        if eventEndDate and actionDirectionDate:
            if actionBegDate:
                result = result and (actionBegDateToCompare <= eventEndDateToCompare or self._eventEditor.checkValueMessage(
                    u'Дата начала действия %s не должна быть позже даты выполнения события %s' % (
                        forceString(actionBegDate), forceString(eventEndDate)), True, widget, row, BEG_DATE_INDEX, widgetBegDate))
            if actionEndDate and enableActionsBeyondEvent:
                result = result and (actionEndDateToCompare <= eventEndDateToCompare or self._eventEditor.checkValueMessage(
                    u'Дата выполнения действия %s не должна быть позже даты выполнения события %s' % (forceString(actionEndDate), forceString(eventEndDate)),
                    True if enableActionsBeyondEvent == 1 else False, widget, row, PLAN_END_DATE, widgetEndDate))
        if eventDirectionDate and (actionEndDate and actionEndDateToCompare >= eventDirectionDateToCompare and (
                not eventEndDate or eventEndDateToCompare >= actionEndDateToCompare)) and actionBegDate:
            result = result and (actionBegDateToCompare >= eventDirectionDateToCompare or self._eventEditor.checkValueMessage(
                u'Дата начала действия %s не должна быть раньше даты начала события %s' % (
                    forceString(actionBegDate), forceString(eventDirectionDate)), True, widget, row, BEG_DATE_INDEX, widgetBegDate))
        return result


    def checkActionDataEntered(self, directionDate, begDate, endDate, widget, widgetDirectionDate=None,
                               widgetBegDate=None, widgetEndDate=None, row=None, column=None):
        showTime = getEventShowTime(self._eventEditor.eventTypeId)
        begDateToCompare = self._eventEditor._date2StringToCompare(
            begDate if showTime else begDate.date() if isinstance(begDate, QDateTime) else begDate)
        begDateToCompareWithDeath = self._eventEditor._date2StringToCompare(
            begDate.date() if isinstance(begDate, QDateTime) else begDate)
        endDateToCompare = self._eventEditor._date2StringToCompare(
            endDate if showTime else endDate.date() if isinstance(endDate, QDateTime) else endDate)
        endDateToCompareWithDeath = self._eventEditor._date2StringToCompare(
            endDate.date() if isinstance(endDate, QDateTime) else endDate)
        directionDateToCompare = self._eventEditor._date2StringToCompare(
            directionDate if showTime else directionDate.date() if isinstance(directionDate,
                                                                              QDateTime) else directionDate)
        directionDateToCompareWithDeath = self._eventEditor._date2StringToCompare(
            directionDate.date() if isinstance(directionDate, QDateTime) else directionDate)
        clientDeathDateToCompare = self._eventEditor._date2StringToCompare(self._eventEditor.clientDeathDate) if self._eventEditor.clientDeathDate else ''
        result = True
        possibleDeathDate = QDateTime()
        if self._eventEditor.clientBirthDate:
            possibleDeathDate = QDateTime(self._eventEditor.clientBirthDate.addYears(QtGui.qApp.maxLifeDuration), QTime())
            possibleDeathDateToCompare = self._eventEditor._date2StringToCompare(possibleDeathDate)
            clientBirthDateToCompare = self._eventEditor._date2StringToCompare(self._eventEditor.clientBirthDate)
        eventPurposeLethalityId = forceRef(QtGui.qApp.db.translate('rbEventTypePurpose', 'code', '5', 'id'))
        if endDate:
            if directionDate:
                result = result and (endDateToCompare >= directionDateToCompare or self._eventEditor.checkValueMessage(
                    u'Дата выполнения (окончания) %s не может быть раньше даты назначения %s' % (
                        forceString(endDate), forceString(directionDate)), False, widget, row, PLAN_END_DATE, widgetEndDate))
            if begDate:
                result = result and (endDateToCompare >= begDateToCompare or self._eventEditor.checkValueMessage(
                    u'Дата выполнения (окончания) %s не может быть раньше даты начала %s' % (
                        forceString(endDate), forceString(begDate)), False, widget, row, PLAN_END_DATE, widgetEndDate))
            if self._eventEditor.clientBirthDate:
                result = result and (endDateToCompare >= clientBirthDateToCompare or self._eventEditor.checkValueMessage(
                    u'Дата выполнения (окончания) %s не может быть раньше даты рождения пациента %s' % (
                        forceString(endDate), forceString(self._eventEditor.clientBirthDate)), False, widget, row, PLAN_END_DATE, widgetEndDate))
            if self._eventEditor.clientDeathDate:
                result = result and (
                        endDateToCompareWithDeath <= clientDeathDateToCompare or self._eventEditor.eventPurposeId == eventPurposeLethalityId or self._eventEditor.checkValueMessage(
                    u'Дата выполнения (окончания) %s не может быть позже имеющейся даты смерти пациента %s' % (
                        forceString(endDate), forceString(self._eventEditor.clientDeathDate)), False, widget, row, PLAN_END_DATE, widgetEndDate))
            else:
                if possibleDeathDate:
                    result = result and (
                            endDateToCompare <= possibleDeathDateToCompare or self._eventEditor.eventPurposeId == eventPurposeLethalityId or self._eventEditor.checkValueMessage(
                        u'Дата выполнения (окончания) %s не может быть позже возможной даты смерти пациента %s' % (
                            forceString(endDate), forceString(possibleDeathDate)), False, widget, row, PLAN_END_DATE, widgetEndDate))
        if directionDate and begDate:
            result = result and (directionDateToCompare <= begDateToCompare or self._eventEditor.checkValueMessage(
                u'Дата назначения %s не может быть позже даты начала %s' % (
                    forceString(directionDate), forceString(begDate)), False, widget, row, DIREACTION_DATE_INDEX, widgetDirectionDate))
        if self._eventEditor.clientBirthDate:
            if directionDate:
                result = result and (directionDateToCompare >= clientBirthDateToCompare or self._eventEditor.checkValueMessage(
                    u'Дата назначения %s не может быть раньше даты рождения пациента %s' % (
                        forceString(directionDate), forceString(self._eventEditor.clientBirthDate)), False, widget, row, DIREACTION_DATE_INDEX, widgetDirectionDate))
            if begDate:
                result = result and (begDateToCompare >= clientBirthDateToCompare or self._eventEditor.checkValueMessage(
                    u'Дата начала %s не может быть раньше даты рождения пациента %s' % (
                        forceString(begDate), forceString(self._eventEditor.clientBirthDate)), False, widget, row, BEG_DATE_INDEX, widgetBegDate))
        if self._eventEditor.clientDeathDate:
            if directionDate:
                result = result and (
                        directionDateToCompareWithDeath <= clientDeathDateToCompare or self._eventEditor.eventPurposeId == eventPurposeLethalityId or self._eventEditor.checkValueMessage(
                    u'Дата назначения %s не может быть позже имеющейся даты смерти пациента %s' % (
                        forceString(directionDate), forceString(self._eventEditor.clientDeathDate)), False, widget, row, DIREACTION_DATE_INDEX, widgetDirectionDate))
            if begDate:
                result = result and (
                        begDateToCompareWithDeath <= clientDeathDateToCompare or self._eventEditor.eventPurposeId == eventPurposeLethalityId or self._eventEditor.checkValueMessage(
                    u'Дата начала %s не может быть позже имеющейся даты смерти пациента %s' % (
                        forceString(begDate), forceString(self._eventEditor.clientDeathDate)), False, widget, row, BEG_DATE_INDEX, widgetBegDate))
        else:
            if possibleDeathDate:
                if directionDate:
                    result = result and (
                            directionDateToCompare <= possibleDeathDateToCompare or self._eventEditor.eventPurposeId == eventPurposeLethalityId or self._eventEditor.checkValueMessage(
                        u'Дата назначения %s не может быть позже возможной даты смерти пациента %s' % (
                            forceString(directionDate), forceString(possibleDeathDate)), False, widget, row, DIREACTION_DATE_INDEX, widgetDirectionDate))
                if begDate:
                    result = result and (
                            begDateToCompare <= possibleDeathDateToCompare or self._eventEditor.eventPurposeId == eventPurposeLethalityId or self._eventEditor.checkValueMessage(
                        u'Дата начала %s не может быть позже возможной даты смерти пациента %s' % (
                            forceString(begDate), forceString(possibleDeathDate)), False, widget, row, BEG_DATE_INDEX, widgetBegDate))
        return result


    def checkEventDate(self, directionDateF, endDateF, nextDateF, widget, widgetNextDateF, widgetEndDateF=None,
                       boolEvent=False, row=None, column=None, enableActionsBeyondEvent=0):
        directionDate = directionDateF.date() if isinstance(directionDateF, QDateTime) else directionDateF
        endDate = endDateF.date() if isinstance(endDateF, QDateTime) else endDateF
        nextDate = nextDateF.date() if isinstance(nextDateF, QDateTime) else nextDateF
        widgetNextDate = widgetNextDateF.date() if isinstance(widgetNextDateF, QDateTime) else widgetNextDateF
        widgetEndDate = widgetEndDateF.date() if isinstance(widgetEndDateF, QDateTime) else widgetEndDateF
        result = True
        if nextDate and directionDate:
            result = result and (nextDate >= directionDate or self._eventEditor.checkValueMessage(
                u'Дата следующей явки %s не должна быть раньше даты назначения %s' % (
                    forceString(nextDate), forceString(directionDate)), False, widget, row, DIREACTION_DATE_INDEX, widgetNextDate))
            result = result and (nextDate != directionDate or self._eventEditor.checkValueMessage(
                u'Дата следующей явки %s не должна быть равна дате назначения %s' % (
                    forceString(nextDate), forceString(directionDate)), False, widget, row, DIREACTION_DATE_INDEX, widgetNextDate))
        if nextDate and endDate:
            result = result and (nextDate >= endDate or self._eventEditor.checkValueMessage(
                u'Дата следующей явки %s не должна быть раньше даты выполнения %s' % (
                    forceString(nextDate), forceString(endDate)), False, widget, row, PLAN_END_DATE, widgetNextDate))
            result = result and (nextDate != endDate or self._eventEditor.checkValueMessage(
                u'Дата следующей явки %s не должна быть равна дате выполнения %s' % (
                    forceString(nextDate), forceString(endDate)), False, widget, row, PLAN_END_DATE, widgetNextDate))
        directionDate = QDate.currentDate()
        if boolEvent:
            if self._eventEditor.orgId == QtGui.qApp.currentOrgId():
                if endDate and directionDate:
                    result = result and (endDate <= directionDate or self._eventEditor.checkValueMessage(
                        u'Дата выполнения %s не должна быть позже текущей даты %s' % (
                            forceString(endDate), forceString(directionDate)), True, widget, row, PLAN_END_DATE, widgetEndDate))
        else:
            if endDate and directionDate and enableActionsBeyondEvent:
                result = result and (endDate <= directionDate or self._eventEditor.checkValueMessage(
                    u'Дата выполнения %s не должна быть позже текущей даты %s' % (
                        forceString(endDate), forceString(directionDate)), True, widget, row, PLAN_END_DATE, widgetEndDate))
        return result


    def saveData(self):
        if not self.checkDataEntered():
            return False
        if self._fromEventEditor:
            self._prepareGoupsToSave()
            self._addNewGroups()
            tabs = self._eventEditor.getActionsTabsList()
            for tab in tabs:
                for groupRemove in self.groupsDeleted:
                    mapItem2RowsGroupRemove = groupRemove._mapItem2Row
                    for actionRemove, rowRemove in mapItem2RowsGroupRemove.items():
                        groups = tab.modelAPActions._items._groups
                        for group in groups:
                            mapItem2Row = group._mapItem2Row
                            for action, row in mapItem2Row.items():
                                if actionRemove == action and rowRemove == row:
                                    if action.action and action.action.nomenclatureClientReservation:
                                        action.action.cancel()
                                    tab.modelAPActions.removeRows(row, 1)
            return True


    def discardData(self):
        if self._fromEventEditor:
            self.modelNomenclatureExpense.discardChanges()


    def getExecutionPlanIsDirty(self, action):
        if action:
            executionPlan = action.getExecutionPlan()
            if executionPlan:
                items = executionPlan.items
                for item in items:
                    if item.getIsDirty():
                        self.setIsDirty(True)
                        return True
        return False


    def _prepareGoupsToSave(self):
#        for group in self.modelNomenclatureExpense.groupsToSavePrepare():
        for group in self.modelNomenclatureExpense._mapGroupToCopy.values():
            if group not in self.modelNomenclatureExpense.groupsToAdd():
                group.prepareToSave()
                group.setIsDirty(False)
                isDirty = False
                for row, item in enumerate(group.items[::-1] if group._reversedItems else group.items) :
                    currentIndex = item.action.executionPlanManager.getCurrentItemIndex()
                    executionPlan = group._epGroup.getExecutionPlan()
                    item.action.executionPlanManager.setExecutionPlan(executionPlan, force=True)
                    #item.action.executionPlanManager.setCurrentItemIndex(currentIndex)
                    #item.action.executionPlanManager.bindAction(item.action)
                    if item.action.executionPlanManager.hasItemsToDo():
                        if item.action.getType().isNomenclatureExpense:
                            item.action.updateDosageFromExecutionPlan()
                        item.action.updateSpecifiedName()
                        if self.getExecutionPlanIsDirty(item.action):
                            isDirty = True
                            executionPlan.updateQuantity()
                            #currentItemIndex = item.action.executionPlanManager.getCurrentItemIndex()
                            action = item.action.executionPlanManager.executionPlan.items[row].action
                            if action:
                                record = action.getRecord()
                                duration = forceInt(record.value('duration'))
                                item.action.setDuration(duration)
                                aliquoticity = forceInt(record.value('aliquoticity'))
                                item.action.setAliquoticity(aliquoticity)
                                quantity = forceInt(record.value('quantity'))
                                item.action.setQuantity(quantity)
                        financeId = item.action.getFinanceId()
                        medicalAidKindId = item.action.getMedicalAidKindId() if item.action.getMedicalAidKindId() else self.getMedicalAidKindId()
                        supplierId = item.action.getOrgStructureId()
                        if self.cmbOrgStructure.value() and not supplierId:
                            supplierId = self.cmbOrgStructure.value()
                        if self.getExecutionPlanIsDirty(item.action):
                            if item.action.nomenclatureClientReservation is not None:
                                item.action.nomenclatureClientReservationCancel()
                            nomenclatureId = self.modelNomenclatureExpense._cellsSettings.getGroupNomenclature(group)
                            if nomenclatureId and item.action.getType().isNomenclatureExpense:
                                item.action.initNomenclatureReservation(self._eventEditor.clientId, financeId=financeId, medicalAidKindId=medicalAidKindId, supplierId=supplierId, markToUpdate=True)
                                item.action.setNomenclatureClientReservationChange(True)
                if isDirty:
                    for row, item in enumerate(group.items[::-1] if group._reversedItems else group.items):
                        item.action.executionPlanManager.setCurrentItemIndex(row)
                        currentItemIndex = item.action.executionPlanManager.getCurrentItemIndex()
                        action = item.action.executionPlanManager.executionPlan.items[currentItemIndex].action
                        if action:
                            record = action.getRecord()
                            duration = forceInt(record.value('duration'))
                            item.action.setDuration(duration)
                            aliquoticity = forceInt(record.value('aliquoticity'))
                            item.action.setAliquoticity(aliquoticity)
                            quantity = forceInt(record.value('quantity'))
                            item.action.setQuantity(quantity)


#    def closeEvent(self, event):
#        self.saveDialogPreferences()
#        preferences = self.tblNomenclatureExpense.savePreferences()
#        setPref(QtGui.qApp.preferences.windowPrefs, 'CNomenclatureExpenseDialog_tblNomenclatureExpense', preferences)
#        preferencesDays = self.tblNomenclatureExpenseDays.savePreferences()
#        setPref(QtGui.qApp.preferences.windowPrefs, 'CNomenclatureExpenseDialog_tblNomenclatureExpenseDays', preferencesDays)
#        CDialogBase.closeEvent(self, event)


    def getMedicalAidKindId(self):
        return self.eventEditor.eventMedicalAidKindId


    def getFinanceId(self):
        return self.eventEditor.eventFinanceId


    def _addNewGroups(self):
        if self._fromEventEditor:
            tabs = self._eventEditor.getActionsTabsList()
            differClasses = len(tabs) > 1
            for group in self.modelNomenclatureExpense.groupsToAdd():
                action = group.headItem.action
                supplierId = action.getOrgStructureId()
                if self.cmbOrgStructure.value() and not supplierId:
                    supplierId = self.cmbOrgStructure.value()
                    action.setOrgStructureId(supplierId)
                action.executionPlanManager.setCurrentItemIndex(0)
                action.executionPlanManager.setCurrentItem(action.executionPlanManager.currentItem)
                if action.executionPlanManager.hasItemsToDo():
                    if action.getType().isNomenclatureExpense:
                        action.updateDosageFromExecutionPlan()
                    action.updateSpecifiedName()
#                if QtGui.qApp.controlSMFinance() == 0:
#                    action.setFinanceId(None)
                financeId = action.getFinanceId()
                medicalAidKindId = action.getMedicalAidKindId() if action.getMedicalAidKindId() else self.getMedicalAidKindId()
                if action.nomenclatureClientReservation is not None and self.getExecutionPlanIsDirty(action):
                    action.nomenclatureClientReservationCancel()
                nomenclatureId = self.modelNomenclatureExpense._cellsSettings.getGroupNomenclature(group)
                if nomenclatureId and action.getType().isNomenclatureExpense:
                    action.initNomenclatureReservation(self._eventEditor.clientId, financeId=financeId, medicalAidKindId=medicalAidKindId, supplierId=supplierId)
                    action.setNomenclatureClientReservationChange(True)
                model = None
                if differClasses:
                    model = tabs[action.actionType().class_]
                else:
                    model = tabs[0]
                if model:
                    model = model.modelAPActions
                    action.updateSpecifiedName()
                    group.bindModel(model)
                    model.addRow(presetAction=action, related=False)
                    modelRow = len(model.items()) - 1
                    group.bindFirstItemModelRow(modelRow)

            for tab in tabs:
                if tab:
                    tab.onActionCurrentChanged()


class CExtendAppointmentNomenclatureDialog(CDialogBase, Ui_ExtendAppointmentNomenclatureDialog):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.setupDirtyCather()


    def getExtendParametrs(self):
        params = {}
        params['quantityDay'] = self.edtQuantityDay.value()
        params['skipAfterLastDayCourse'] = self.edtSkipAfterLastDayCourse.value()
        params['isLastDayCourse'] = self.chkLastDayCourse.isChecked()
        return params


class CNomenclatureExpenseHBDialog(CNomenclatureExpenseDialog):
    def __init__(self, parent=None, eventEditor=None, groups=None, fromEventEditor=True):
        CNomenclatureExpenseDialog.__init__(self, parent, eventEditor, groups, fromEventEditor)


    def done(self, result):
        defaults = {
            'actionTypeId': self.cmbActionType.value(),
            'nomenclatureId': self.cmbNomenclature.value(),
            'begDate': str(self.edtBegDate.date().toString('yyyy.MM.dd')),
            'endDate': str(self.edtEndDate.date().toString('yyyy.MM.dd')),
            'year': self.edtYear.value(),
            'month': self.cmbMonth.currentIndex(),
            'period': self.chkPeriod.isChecked(),
            'actual': self.chkActual.isChecked(),
            'ignoreTime': self.chkIgnoreTime.isChecked(),
            'isRequiresFillingNomenclature': self.chkRequiresFillingNomenclature.isChecked(),
            'schemaId': self.cmbSchema.value(),
            'currentEvent': self.chkCurrentEvent.isChecked(),
            'orgStructureId': self.cmbOrgStructure.value()
        }

        defaults = json.dumps(defaults)

        QtGui.qApp.preferences.appPrefs['NomenclatureExpenseDialogDefaultValues'] = defaults
        self.saveDialogPreferences()
        preferences = self.tblNomenclatureExpense.savePreferences()
        setPref(QtGui.qApp.preferences.windowPrefs, 'CNomenclatureExpenseDialog_tblNomenclatureExpense', preferences)
        preferencesDays = self.tblNomenclatureExpenseDays.savePreferences()
        setPref(QtGui.qApp.preferences.windowPrefs, 'CNomenclatureExpenseDialog_tblNomenclatureExpenseDays', preferencesDays)
        if result > 0:
            if self._eventEditor.checkActionsForNomenclatureExpense():
                result = self.doneEx(result)
                if result > 0 and self._eventEditor.save():
                    QtGui.QDialog.done(self._eventEditor, result)
                    QtGui.QDialog.done(self, result)
        else:
            return CDialogBase.done(self, result)
        return


    def doneEx(self, result):
        if self.isReadOnly():
            scd = self.cdDiscard
        else:
            scd = self.cdSave
        if scd == self.cdDiscard:
            self.discardData()
        if scd == self.cdDiscard:
            self.saveDialogPreferences()
            return 0
        elif (scd == self.cdSave and self.saveData()):
            self.saveDialogPreferences()
            return 1
        return 0

