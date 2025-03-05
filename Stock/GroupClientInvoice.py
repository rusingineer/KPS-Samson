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

from decimal import Decimal
from contextlib import contextmanager

from PyQt4 import QtGui, QtCore, QtSql
from PyQt4.QtCore import Qt, QVariant, QDate, pyqtSignature, QDateTime

from Events.ActionStatus import CActionStatus
from Events.Action import CAction
from Events.InputDialog import CDateTimeInputDialog
from library.DialogBase import CDialogBase
from library.RecordLock import CRecordLockMixin
from library.InDocTable import CRecordListModel, CInDocTableCol, CBoolInDocTableCol, forcePyType, CDateInDocTableCol
from library.ProgressBar import CProgressBar
from library.PrintTemplates import getPrintButton
from Reports.PlannedClientInvoiceNomenclaturesReport import CPlannedClientInvoiceNomenclaturesReport
from library.Utils import formatNameByRecord, forceRef, toVariant, forceString, forceDouble, forceBool, forceDate, forceInt, forceStringEx
from Users.Rights import (urNomenclatureExpenseLaterDate, urNoRestrictRetrospectiveNEClient)
from Stock.Service import CStockService

from Stock.Ui_GroupClientInvoice import Ui_GroupClientInvoice


class _CTables(object):
    def __init__(self):
        db = QtGui.qApp.db

        self.E = db.table('Event')
        self.A = db.table('Action')
        self.AT = db.table('ActionType')
        self.C = db.table('Client')

        self.APn = db.table('ActionProperty').alias('APn')
        self.APTn = db.table('ActionPropertyType').alias('APTn')
        self.APN = db.table('ActionProperty_rbNomenclature')
        self.N = db.table('rbNomenclature')

        self.APd = db.table('ActionProperty').alias('APd')
        self.APTd = db.table('ActionPropertyType').alias('APTd')
        self.APD = db.table('ActionProperty_Double')

        self.APs = db.table('ActionProperty').alias('APs')
        self.APTs = db.table('ActionPropertyType').alias('APTs')
        self.APS = db.table('ActionProperty_String')


class _CInvoiceProcessContext(object):
    def __init__(self, locker, tables):
        self._locker = locker
        self._tables = tables
        self._lockId = None

        self._oldConfirmLock = locker._confirmLock

        self._action = None
        self._failedData = {}
        self._successActionIds = set()

    @property
    def successActionIds(self):
        return self._successActionIds

    @property
    def failedData(self):
        return self._failedData

    @contextmanager
    def actionLock(self, action):
        if self._lockId:
            try:
                self._locker.releaseLock(self._lockId)
            finally:
                self._lockId = None
                raise RuntimeError(
                    "Could not process action lock. Previous lock %d was not released" % self._lockId
                )

        try:
            self._action = action
            lockId = self._locker.lock(self._tables.A.name(), action.getId())
            if lockId:
                self._successActionIds.add(action.getId())
                self._lockId = lockId

            yield bool(lockId)

        finally:
            if self._lockId:
                self._locker.releaseLock(self._lockId)

            self._action = self._lockId = None

    def _confirmLock(self, message):
        if self._action:
            self.fail(self._action.getId(), message)

    def fail(self, actionId, message):
        if actionId in self.successActionIds:
            self._successActionIds.remove(actionId)

        self._failedData[actionId] = message

    def __enter__(self):
        self._locker._confirmLock = self._confirmLock

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._locker._confirmLock = self._oldConfirmLock
        self._successActionIds.clear()
        self._failedData.clear()


class CGroupClientInvoice(CDialogBase, CRecordLockMixin, Ui_GroupClientInvoice):
    def __init__(self, orgStructureId, parent=None, isControlPageVisible=True):
        CDialogBase.__init__(self, parent)
        CRecordLockMixin.__init__(self)
        self.isControlPageVisible = isControlPageVisible
        self._filters = {}
        self._refreshFilters = {}
        self._orgStructureId = orgStructureId
        self.setupUi(self)
        self.setWindowFlags(Qt.Window | Qt.WindowSystemMenuHint | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
        self.setWindowState(Qt.WindowMaximized)
        self.setWindowTitle(u'Списание ЛСиИМН')
        self.addModels('ClientNomenclatures', CGroupClientInvoiceModel(self))
        self.addModels('ClientNomenclaturesControl', CGroupClientInvoiceModel(self, 1))
        self.setModels(self.tblClientNomenclatures, self.modelClientNomenclatures)
        self.setModels(self.tblClientNomenclaturesControl, self.modelClientNomenclaturesControl)

        self.addObject('btnDoInvoices', QtGui.QPushButton(u'Списать', self))
        self.buttonBox.addButton(self.btnDoInvoices, QtGui.QDialogButtonBox.ActionRole)
        self.connect(self.btnDoInvoices, QtCore.SIGNAL('clicked()'), self._doInvoices)

        self.addObject('btnRefresh', QtGui.QPushButton(u'Обновить', self))
        self.buttonBox.addButton(self.btnRefresh, QtGui.QDialogButtonBox.ActionRole)
        self.connect(self.btnRefresh, QtCore.SIGNAL('clicked()'), self.load)

        self.addObject('btnPrint', getPrintButton(self, '', u'Печать'))
        self.buttonBox.addButton(self.btnPrint, QtGui.QDialogButtonBox.ActionRole)
        self.btnPrint.setEnabled(True)
        self.preparePrintBtn()
        if not self.isControlPageVisible:
            self.tabWidget.setTabEnabled(self.tabWidget.indexOf(self.tabClientNomenclaturesControl), self.isControlPageVisible)

        self._tables = _CTables()

        self._setResultColumnVisible(False)
        self.edtDateFilter = None

        self.actSetCheckAll = QtGui.QAction(u'Выделить все', self)
        self.actSetUnCheckedAll = QtGui.QAction(u'Снять все выделения', self)
        self.actSetActionCanceled = QtGui.QAction(u'Отменить выделенные назначения', self)
        self.actSetActionCanceled.setEnabled(QtGui.qApp.userHasRight(u'canSetClientInvoiceActionCanceled'))

        self.tblClientNomenclatures.createPopupMenu([self.actSetCheckAll, self.actSetUnCheckedAll])
        self.tblClientNomenclaturesControl.createPopupMenu([self.actSetCheckAll, self.actSetUnCheckedAll, self.actSetActionCanceled])

        self.connect(self.actSetCheckAll, QtCore.SIGNAL('triggered()'), self.on_setCheckedAll)
        self.connect(self.actSetUnCheckedAll, QtCore.SIGNAL('triggered()'), self.on_setUnCheckedAll)
        self.connect(self.actSetActionCanceled, QtCore.SIGNAL('triggered()'), self.on_setActionCanceled)
        self.connect(self.tblClientNomenclatures.popupMenu(), QtCore.SIGNAL('aboutToShow()'), self.on_popupMenuAboutToShow)
        self.connect(self.tblClientNomenclaturesControl.popupMenu(), QtCore.SIGNAL('aboutToShow()'), self.on_popupMenuAboutToShow)
        self.connect(self.modelClientNomenclatures, QtCore.SIGNAL('dataChanged(QModelIndex, QModelIndex)'), self.on_modelClientNomenclatures_dataChanged)
        self.connect(self.modelClientNomenclaturesControl, QtCore.SIGNAL('dataChanged(QModelIndex, QModelIndex)'), self.on_modelClientNomenclaturesControl_dataChanged)
        self.edtDate.connect(self.edtDate.lineEdit, QtCore.SIGNAL('editingFinished()'), self.on_edtDate_editingFinished)

        self._progressBar = CProgressBar()
        self._progressBar.setFormat(u'%v из %m')
        self._progressBar.setMinimum(0)


    def setRefreshParams(self, **filters):
        self._refreshFilters = {}
        if bool(filters):
            self._refreshFilters = filters


    def setDateParams(self):
        self.edtDate.setCurrentDate(False)
        currentDate = QDate.currentDate()
        if not QtGui.qApp.userHasRight(urNomenclatureExpenseLaterDate):
            self.edtDate.setMaximumDate(currentDate)
            self.edtDate.setCurrentDate(True)
        if not QtGui.qApp.userHasRight(urNoRestrictRetrospectiveNEClient):
            if QtGui.qApp.admissibilityNomenclatureExpensePostDates() == 1:
                self.edtDate.setMinimumDate(currentDate.addDays(-1))
            elif QtGui.qApp.admissibilityNomenclatureExpensePostDates() == 2:
                self.edtDate.setMinimumDate(QDate(currentDate.year(), currentDate.month(), 1))


    def _prepareProgressBar(self, steps):
        self._progressBar.setMaximum(steps)
        self._progressBar.setValue(0)
        self._progressBar.setMaximumHeight(self.statusBar.height() / 2)
        return self._progressBar


    def closeEvent(self, event):
        QtGui.qApp.preferences.appPrefs['GroupClientInvoiceModel_isDescOrder'+str(0)] = toVariant(self.tblClientNomenclatures.getSortAscending())
        QtGui.qApp.preferences.appPrefs['GroupClientInvoiceModel_ColumnOrder'+str(0)] = toVariant(self.tblClientNomenclatures.getSortColumn())
        QtGui.qApp.preferences.appPrefs['GroupClientInvoiceModel_isDescOrder'+str(1)] = toVariant(self.tblClientNomenclaturesControl.getSortAscending())
        QtGui.qApp.preferences.appPrefs['GroupClientInvoiceModel_ColumnOrder'+str(1)] = toVariant(self.tblClientNomenclaturesControl.getSortColumn())
        CDialogBase.closeEvent(self, event)

    def on_modelClientNomenclatures_dataChanged(self, topLeft, bottomRight):
        index = self.tblClientNomenclatures.currentIndex()
        if index.isValid():
            column = index.column()
            if column == CGroupClientInvoiceModel.NOTE_COLUMN:
                items = self.modelClientNomenclatures.items()
                row = index.row()
                if row >= 0 and len(items) > row:
                    record = items[row]
                    if record:
                        actionId = forceRef(record.value('actionId'))
                        if actionId:
                            action = CAction.getActionById(actionId)
                            if action:
                                noteNew = forceStringEx(record.value('note'))
                                noteOld = forceStringEx(action.getRecord().value('note'))
                                if noteNew != noteOld:
                                    action.getRecord().setValue('note', toVariant(noteNew))
                                    action.save(idx=forceInt(action.getRecord().value('idx')))


    def on_modelClientNomenclaturesControl_dataChanged(self, topLeft, bottomRight):
        index = self.tblClientNomenclaturesControl.currentIndex()
        if index.isValid():
            column = index.column()
            if column == CGroupClientInvoiceModel.NOTE_COLUMN:
                items = self.modelClientNomenclaturesControl.items()
                row = index.row()
                if row >= 0 and len(items) > row:
                    record = items[row]
                    if record:
                        actionId = forceRef(record.value('actionId'))
                        if actionId:
                            action = CAction.getActionById(actionId)
                            if action:
                                noteNew = forceStringEx(record.value('note'))
                                noteOld = forceStringEx(action.getRecord().value('note'))
                                if noteNew != noteOld:
                                    action.getRecord().setValue('note', toVariant(noteNew))
                                    action.save(idx=forceInt(action.getRecord().value('idx')))


    @pyqtSignature('int')
    def on_tabWidget_currentChanged(self, index):
#        widgetIndex = self.tabWidget.currentIndex()
#        widgetIndexOld = (widgetIndex - 1) if widgetIndex else (widgetIndex + 1)
#        table = [self.tblClientNomenclatures, self.tblClientNomenclaturesControl][widgetIndexOld]
#        QtGui.qApp.preferences.appPrefs['GroupClientInvoiceModel_isDescOrder'+str(widgetIndexOld)] = toVariant(table.getSortAscending())
#        QtGui.qApp.preferences.appPrefs['GroupClientInvoiceModel_ColumnOrder'+str(widgetIndexOld)] = toVariant(table.getSortColumn())
        self.edtDateFilter = None
        self.on_edtDate_editingFinished()


    def on_popupMenuAboutToShow(self):
        widgetIndex = self.tabWidget.currentIndex()
        if widgetIndex == 1:
            hasChecked = self.modelClientNomenclaturesControl.hasChecked()
            allChecked = self.modelClientNomenclaturesControl.allChecked()
            self.actSetCheckAll.setEnabled(not allChecked)
            self.actSetUnCheckedAll.setEnabled(hasChecked)
            self.actSetActionCanceled.setEnabled(
                len(self.tblClientNomenclaturesControl.getSelectedRows()) > 0 \
                and QtGui.qApp.userHasRight(u'canSetClientInvoiceActionCanceled'))
        else:
            hasChecked = self.modelClientNomenclatures.hasChecked()
            allChecked = self.modelClientNomenclatures.allChecked()
            self.actSetCheckAll.setEnabled(not allChecked)
            self.actSetUnCheckedAll.setEnabled(hasChecked)


    def on_setCheckedAll(self):
        widgetIndex = self.tabWidget.currentIndex()
        if widgetIndex == 1:
            self.modelClientNomenclaturesControl.setCheckedAll()
        else:
            self.modelClientNomenclatures.setCheckedAll()


    def on_setUnCheckedAll(self):
        widgetIndex = self.tabWidget.currentIndex()
        if widgetIndex == 1:
            self.modelClientNomenclaturesControl.setUnCheckedAll()
        else:
            self.modelClientNomenclatures.setUnCheckedAll()


    def on_setActionCanceled(self):
#        QtGui.qApp.preferences.appPrefs['GroupClientInvoiceModel_isDescOrder'+str(0)] = toVariant(self.tblClientNomenclatures.getSortAscending())
#        QtGui.qApp.preferences.appPrefs['GroupClientInvoiceModel_ColumnOrder'+str(0)] = toVariant(self.tblClientNomenclatures.getSortColumn())
#        QtGui.qApp.preferences.appPrefs['GroupClientInvoiceModel_isDescOrder'+str(1)] = toVariant(self.tblClientNomenclaturesControl.getSortAscending())
#        QtGui.qApp.preferences.appPrefs['GroupClientInvoiceModel_ColumnOrder'+str(1)] = toVariant(self.tblClientNomenclaturesControl.getSortColumn())
        actionIdList = []
        rows = self.tblClientNomenclaturesControl.getSelectedRows()
        rows.sort(reverse=True)
        items = self.modelClientNomenclaturesControl.items()
        for row in rows:
            if items and row >= 0 and len(items) > row:
                record = items[row]
                if record:
                    actionId = forceRef(record.value('actionId'))
                    if actionId and actionId not in actionIdList:
                        actionIdList.append(actionId)
        if not actionIdList:
            return
        self.modelClientNomenclaturesControl.setActionCanceled(actionIdList)
        self.edtDateFilter = None
        self.on_edtDate_editingFinished()


    def preparePrintBtn(self):
        btn = self.btnPrint
        menu = QtGui.QMenu()
        action = QtGui.QAction(u'Отчет о выдаче ЛС на выбранный период',  self)
        action.triggered.connect(self.plannedClientInvoiceNomenclaturesReport)
        menu.addAction(action)
        btn.setMenu(menu)


    def plannedClientInvoiceNomenclaturesReport(self):
        CPlannedClientInvoiceNomenclaturesReport(self).exec_()


    def _setResultColumnVisible(self, value):
        headerControl = self.tblClientNomenclaturesControl.horizontalHeader()
        headerControl.setSectionHidden(CGroupClientInvoiceModel.RESULT_COLUMN, not value)
        header = self.tblClientNomenclatures.horizontalHeader()
        header.setSectionHidden(CGroupClientInvoiceModel.RESULT_COLUMN, not value)


    def _doInvoices(self):
        widgetIndex = self.tabWidget.currentIndex()
        if widgetIndex == 1:
            model = self.modelClientNomenclaturesControl
        else:
            model =  self.modelClientNomenclatures
        items = [
            record for record in model.items()
            if forceBool(record.value('isChecked'))
            ]

        if not items:
            return
        
        groupingItems = {}
        sortedItems = []
        for item in items:
            groupId = forceInt(item.value('group_id'))
            subactionId = forceRef(item.value('actionId'))
            subaction = CAction.getActionById(subactionId)
            if not groupId:
                sortedItems.append(item)
            elif groupId == forceInt(item.value('EPIID')):
                if not groupId in groupingItems.keys():
                    groupingItems[groupId] = [(item,subaction)]
                else:
                    groupingItems[groupId].append((item,subaction))
                sortedItems.append(item)
            else:
                if not groupId in groupingItems.keys():
                    groupingItems[groupId] = [(item,subaction)]
                else:
                    groupingItems[groupId].append((item,subaction))

        progressBar = self._prepareProgressBar(len(sortedItems))
        self.statusBar.addWidget(progressBar)

        try:
            progressBar.show()
            QtGui.qApp.callWithWaitCursor(self, self.__doInvoices, sortedItems, progressBar, groupingItems)

        finally:
            self.statusBar.removeWidget(progressBar)


    def __doInvoices(self, items, progressBar, groupingItems):
        filterDlg = CDateTimeInputDialog(self)
        if not QtGui.qApp.userHasRight(urNomenclatureExpenseLaterDate):
            filterDlg.setMaximumDate(QDate().currentDate())
            filterDlg.setCurrentDate(True)
        filterDlg.exec_()
        self._filters['date'] = QDateTime(filterDlg.date(), filterDlg.time())
        
        processContext = _CInvoiceProcessContext(self, self._tables)

        actionIdsToReload = []

        with processContext:
            for record in items:
                progressBar.step()

                actionId = forceRef(record.value('actionId'))
                action = CAction.getActionById(actionId)
                if not action:
                    processContext.fail(actionId, u"Действие не найдено!")
                    continue

#                action.executionPlanManager.load()
                action.executionPlanManager.setCurrentItemIndex()
                with processContext.actionLock(action) as isLocked:
                    if not isLocked:
                        continue

                    if not action.checkOptimisticLock():
                        processContext.fail(
                            actionId, u'В процессе списания данные действия были изменены другим пользователем! Повторите попытку.')
                        actionIdsToReload.append(actionId)
                        continue

                    try:
                        actionOrgStructureId = forceRef(action.getRecord().value('orgStructure_id'))
                        clientId = forceRef(record.value('clientId'))
                        groupingRecords = groupingItems[forceInt(record.value('group_id'))] if forceInt(record.value('group_id')) in groupingItems.keys() else [(record, action)]
                        for rec, recaction in groupingRecords:
                            recactionId = forceRef(rec.value('actionId'))
                            processContext._successActionIds.add(recactionId)
                        res, messageExecWriteOffNomenclatureExpense = CStockService.doClientInvoice(action, record, actionOrgStructureId if actionOrgStructureId else self._orgStructureId, self._filters['date'], clientId=clientId, groupingRecords=groupingRecords)
                        if messageExecWriteOffNomenclatureExpense:
                            messageFail = messageExecWriteOffNomenclatureExpense + processContext.failedData.get(actionId, u'')
                            processContext.fail(actionId, messageFail)
                    except:
                        processContext.fail(actionId, u'Ошибка в процессе списания!')
                        QtGui.qApp.logCurrentException()
            widgetIndex = self.tabWidget.currentIndex()
            if widgetIndex == 1:
                self.modelClientNomenclaturesControl.setResults(processContext.failedData)
                self.modelClientNomenclaturesControl.removeIds(processContext.successActionIds)
                self.modelClientNomenclaturesControl.reloadActionIds(actionIdsToReload)
            else:
                self.modelClientNomenclatures.setResults(processContext.failedData)
                self.modelClientNomenclatures.removeIds(processContext.successActionIds)
                self.modelClientNomenclatures.reloadActionIds(actionIdsToReload)
            self._setResultColumnVisible(True)

    
    
    def setFilterDate(self, date):
        self.edtDate.setDate(date)
        

    def load(self, **filters):
        self.edtDateFilter = None
        if bool(filters):
            self._filters = filters
        elif bool(self._refreshFilters):
            self._filters = self._refreshFilters
        if 'date' not in filters.keys():
            date = self.edtDate.date()
            self._filters['date'] = date
        else:
            date = self._filters['date']
        widgetIndex = self.tabWidget.currentIndex()
        if widgetIndex == 1:
            model = self.modelClientNomenclaturesControl
        else:
            model =  self.modelClientNomenclatures
        if date:
            if date != self.edtDateFilter:
                model.load(self._filters)
        else:
            model.clearItems()
        self.edtDateFilter = date


    def on_edtDate_editingFinished(self):
        if 'date' not in self._filters.keys():
            date = self.edtDate.date()
            self._filters['date'] = date
        else:
            date = self._filters['date']
        widgetIndex = self.tabWidget.currentIndex()
        if widgetIndex == 1:
            model = self.modelClientNomenclaturesControl
        else:
            model =  self.modelClientNomenclatures
        if date:
            if date != self.edtDateFilter:
                model.load(self._filters)
        else:
            model.clearItems()
        self.edtDateFilter = date


class CLocClientCol(CInDocTableCol):
    def __init__(self, model):
        CInDocTableCol.__init__(self, u'ФИО пациента', 'actionId', 15, readOnly=True)
        self._model = model

    def toString(self, val, record):
        return toVariant(self._model.getClientName(forceRef(val)))


class CLocNomenclatureCol(CInDocTableCol):
    def __init__(self, model):
        CInDocTableCol.__init__(self, u'Наименование ЛС', 'actionId', 15, readOnly=True)
        self._model = model

    def toString(self, val, record):
        return toVariant(self._model.getNomenclatureName(forceRef(val)))


class CLocQntCol(CInDocTableCol):
    def __init__(self, model):
        CInDocTableCol.__init__(self, u'Количество', 'actionId', 15, readOnly=True)
        self._model = model

    def toString(self, val, record):
        return toVariant(self._model.getQnt(forceRef(val)))


class CLocResultCol(CInDocTableCol):
    def __init__(self, model):
        CInDocTableCol.__init__(self, u'Результат', 'actionId', 20, readOnly=True)
        self._model = model

    def toString(self, val, record):
        return toVariant(self._model.getResult(forceRef(val)))


class CLocActionPropertySignaColumn(CInDocTableCol):
    _SIGNA  = 3
    def __init__(self, model):
        CInDocTableCol.__init__(self, u'Способ применения', 'actionId', 20, readOnly=True)
        self.caches = {}
        self._model = model

    def toString(self, val, record):
        actionId = forceRef(val)
        if actionId:
            action = self.caches.get(actionId, None)
            if not action:
                action = CAction.getActionById(actionId)
                self.caches[actionId] = action
            if action:
                return toVariant(action.findSignaPropertyValue())
        return QVariant()

    def toSortString(self, val, record):
        return forcePyType(self.toString(val, record))

    def toStatusTip(self, val, record):
        return self.toString(val, record)


class CLocActionPropertyColumn(CInDocTableCol):
    _SIGNA  = 3
    def __init__(self, model):
        CInDocTableCol.__init__(self, u'Способ применения', 'actionId', 20, readOnly=True)
        self.caches = {}
        self._model = model

    def toString(self, val, record):
        actionId = forceRef(val)
        if actionId:
            action = self.caches.get(actionId, None)
            if not action:
                action = CAction.getActionById(actionId)
                self.caches[actionId] = action
            if action:
                return toVariant(action.findSignaPropertyValue())
        return QVariant()

    def toSortString(self, val, record):
        return forcePyType(self.toString(val, record))

    def toStatusTip(self, val, record):
        return self.toString(val, record)

class CLocActionPropertySignaCommentColumn(CInDocTableCol):
    _SIGNA  = 3
    def __init__(self, model):
        CInDocTableCol.__init__(self, u'Комментарий к СП', 'actionId', 20, readOnly=True)
        self.caches = {}
        self._model = model

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


class CLocActionDayDataValueColumn(CInDocTableCol):
    def __init__(self, model):
        CInDocTableCol.__init__(self, u'Прием', 'actionId', 20, readOnly=True)
        self.caches = {}
        self._model = model
        self.date = None
        self.type = 0

    def setType(self, value):
        self.type = value

    def setDate(self, date):
        self.date = date

    def toString(self, val, record):
        actionId = forceRef(val)
        if actionId and self.date:
            action = self.caches.get(actionId, None)
            if not action:
                action = CAction.getActionById(actionId)
                self.caches[actionId] = action
            if action:
                executionPlan = action.getExecutionPlan()
                if executionPlan:
                    executionPlan_Items = executionPlan.items
                    if executionPlan_Items:
                        if isinstance(self.date, QDateTime):
                            date = self.date.date()
                        else:
                            date = self.date
                        if self.type:
                            items = executionPlan_Items.getItemsByDate(forceDate(action.getRecord().value('begDate')))
                        else:
                            items = executionPlan_Items.getItemsByDate(date)
                        if not items:
                            return QVariant()
                        planItems = len(items)
                        not_done_items = []
                        for item in items:
                            executedDatetime = item.executedDatetime
                            if executedDatetime is None:
                                not_done_items.append(item)
                            elif executedDatetime.isNull() or not executedDatetime.isValid():
                                not_done_items.append(item)
                        return toVariant(u'%i/%i'%(planItems-len(not_done_items)+1, planItems))
        return QVariant()

    def toSortString(self, val, record):
        return forcePyType(self.toString(val, record))

    def toStatusTip(self, val, record):
        return self.toString(val, record)


class _CItemsContainer(object):
    def __init__(self, model, items=None):
        self._model = model
        self._id2item = {}
        self._records = []
        self._extSqlFields = []

        if self._model._extColsPresent:
            for col in self._model.cols():
                if col.external():
                    fieldName = col.fieldName()
                    self._extSqlFields.append(QtSql.QSqlField(fieldName, col.valueType()))

        items and map(self.add, items)

    def removeIds(self, ids):
        self._records = [r for r in self._records if forceRef(r.value('actionId')) not in ids]
        for id in ids:
            del self._id2item[id]

    def __len__(self):
        return len(self._records)

    def __iter__(self):
        return iter(self._records)

    def __getitem__(self, index):
        return self._records[index]

    def getQnt(self, actionId):
        return self._id2item[actionId][CGroupClientInvoiceModel.QNT_COLUMN]

    def getNomenclatureName(self, actionId):
        return self._id2item[actionId][CGroupClientInvoiceModel.NOMENCLATURE_COLUMN]

    def getClientName(self, actionId):
        return self._id2item[actionId][CGroupClientInvoiceModel.CLIENT_COLUMN]

    def getResult(self, actionId):
        return self._id2item[actionId].get(CGroupClientInvoiceModel.RESULT_COLUMN, u'')


    def getNote(self, actionId):
        return self._id2item[actionId].get(CGroupClientInvoiceModel.NOTE_COLUMN, u'')


    def add(self, record):
        self._addExtFields(record)

        self._records.append(record)

        self._setItem(record)

    def _addExtFields(self, record):
        for field in self._extSqlFields:
            record.append(field)

    def _setItem(self, record):
        actionId = forceRef(record.value('actionId'))
        clientName = formatNameByRecord(record)
        nomenclatureName = ' | '.join([forceString(record.value('nCode')), forceString(record.value('nName'))])
        doses = Decimal(str(forceDouble(record.value('doses'))))
        dosageValue = Decimal(str(forceDouble(record.value('dosageValue'))))
        clientQnt = Decimal('1')
        if dosageValue:
            clientQnt = doses / dosageValue
        note = forceStringEx(record.value('note'))

        self._id2item[actionId] = {
            CGroupClientInvoiceModel.CLIENT_COLUMN: clientName,
            CGroupClientInvoiceModel.NOMENCLATURE_COLUMN: nomenclatureName,
            CGroupClientInvoiceModel.QNT_COLUMN: float(clientQnt),
            CGroupClientInvoiceModel.NOTE_COLUMN: note
        }

    def reloadRecords(self, records):
        newRecordsMap = {}
        for r in records:
            self._addExtFields(r)
            newRecordsMap[forceRef(r.value('actionId'))] = r
            self._setItem(r)

        self._records = [newRecordsMap.get(forceRef(r.value('actionId')), r) for r in self._records]

    def setResults(self, results):
        for actionId, value in results.items():
            if actionId in self._id2item:
                self._id2item[actionId][CGroupClientInvoiceModel.RESULT_COLUMN] = value


    def setNote(self, actionId, row):
        if actionId in self._id2item:
            value = self._id2item[actionId].get(CGroupClientInvoiceModel.NOTE_COLUMN, u'')
            self._id2item[actionId][CGroupClientInvoiceModel.NOTE_COLUMN] = value


class CGroupClientInvoiceModel(CRecordListModel):
    CHECKED_COLUMN = 0
    BEGDATE_COLUMN = 1
    CLIENT_COLUMN = 2
    NOMENCLATURE_COLUMN = 3
    QNT_COLUMN = 4
    SIGNA_COLUMN = 5
    SIGNACOMMENT_COLUMN = 6
    DAYDATA_COLUMN = 7
    NOTE_COLUMN = 8
    RESULT_COLUMN = 9

    def __init__(self, parent=None, type = 0):
        CRecordListModel.__init__(self, parent)
        self.type = type
        self._filters = None
        self._tables = _CTables()
        self.date = None

        self.addExtCol(CBoolInDocTableCol(u'Списать', 'isChecked', 5), QtCore.QVariant.Bool)
        self.addCol(CDateInDocTableCol(u'Дата', 'begDate', 12, canBeEmpty=True)).setSortable(True)
        self.addCol(CLocClientCol(self)).setSortable(True)
        self.addCol(CLocNomenclatureCol(self)).setSortable(True)
        self.addCol(CLocQntCol(self))
        self.addCol(CLocActionPropertySignaColumn(self))
        #self.addCol(CLocActionPropertyColumn(self))
        self.addCol(CLocActionPropertySignaCommentColumn(self))
        self.addCol(CLocActionDayDataValueColumn(self))
        self.addCol(CInDocTableCol(u'Примечание', 'note', 20, readOnly = False)).setSortable(False)
        self.addCol(CLocResultCol(self))
        self._cols[CGroupClientInvoiceModel.DAYDATA_COLUMN].setType(self.type)

    def isNomenclatureExpenseRight(self, begDate):
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

    def cellReadOnly(self, index):
        column = index.column()
        row = index.row()
        if column == self.NOTE_COLUMN:
            if 0 <= row < len(self._items):
                return False
        if column == self.CHECKED_COLUMN:
            if 0 <= row < len(self._items):
                record = self._items[row]
                begDate = forceDate(record.value('begDate'))
                return not self.isNomenclatureExpenseRight(begDate)
        return True

    def data(self, index, role=Qt.DisplayRole):
        row = index.row()
        if 0 <= row < len(self._items):
            if role == Qt.ForegroundRole:#Qt.BackgroundColorRole:
                record = self._items[row]
                if record and not self.isNomenclatureExpenseRight(forceDate(record.value('begDate'))):
                    return toVariant(QtGui.QColor(Qt.lightGray))
                else:
                    return QVariant()
        return CRecordListModel.data(self, index, role)
    
    def setData(self, index, value, role=Qt.EditRole):
        result = CRecordListModel.setData(self, index, value, role)
        if result and role == Qt.CheckStateRole:
            column = index.column()
            row = index.row()
            state = value.toInt()[0]
            if row == len(self._items):
                if state == Qt.Unchecked:
                    return False
                self._addEmptyItem()
            record = self._items[row]
            col = self._cols[column]
            if column == 0:
                for row, item in enumerate(self._items):
                    if forceInt(item.value('group_id')) and forceInt(item.value('group_id')) == forceInt(record.value('group_id')):
                        item.setValue(col.fieldName(), QVariant(0 if state == Qt.Unchecked else 1))
                        self.emitCellChanged(row, column)
            return True

    def items(self):
        return self._items._records

    def sortData(self, column, ascending):
        col = self._cols[column]
        self._items._records.sort(key = lambda(item): col.toSortString(item.value(col.fieldName()), item), reverse = not ascending)
        self.emitRowsChanged(0, len(self._items)-1)
        QtGui.qApp.preferences.appPrefs['GroupClientInvoiceModel_isDescOrder'+str(self.type)] = toVariant(ascending)
        QtGui.qApp.preferences.appPrefs['GroupClientInvoiceModel_ColumnOrder'+str(self.type)] = toVariant(column)

    def getQnt(self, actionId):
        return self._items.getQnt(actionId)

    def getNomenclatureName(self, actionId):
        return self._items.getNomenclatureName(actionId)

    def getClientName(self, actionId):
        return self._items.getClientName(actionId)

    def getResult(self, actionId):
        return self._items.getResult(actionId)

    def getNote(self, actionId):
        return self._items.getNote(actionId)

    def setNote(self, actionId):
        self._items.setNote(actionId)

    def setResults(self, results):
        self._items.setResults(results)

    def removeIds(self, ids):
        self._items.removeIds(ids)
        self.reset()

    def _iterItems(self, key=None):
        for item in self._items:
            yield key(item) if key else item

    def hasChecked(self):
        return any(self._iterItems(key=lambda i: forceBool(i.value('isChecked'))))

    def allChecked(self):
        return not any(self._iterItems(key=lambda i: not forceBool(i.value('isChecked'))))

    def setCheckedAll(self):
        self._setCheckValueAll(True)

    def setUnCheckedAll(self):
        self._setCheckValueAll(False)

    def _setCheckValueAll(self, value):
        if value:
            map(lambda i: i.setValue('isChecked', toVariant(value) if self.isNomenclatureExpenseRight(forceDate(i.value('begDate'))) else toVariant(False)), self._items)
        else:
            map(lambda i: i.setValue('isChecked', toVariant(value)), self._items)
        self.emitColumnChanged(self.CHECKED_COLUMN)

    def setActionCanceled(self, actionIdList):
        for actionId in actionIdList:
            if actionId:
                action = CAction.getActionById(actionId)
                if action:
                    action.getRecord().setValue('status', toVariant(CActionStatus.canceled))
                    action.getRecord().setValue('endDate', toVariant(None))
                    action.getRecord().setValue('person_id', toVariant(QtGui.qApp.userId if (QtGui.qApp.userId and QtGui.qApp.userSpecialityId) else forceRef(action.getRecord().value('setPerson_id'))))
                    if action.nomenclatureClientReservation is not None:
                        action.cancel()
                    action.save(idx=forceInt(action.getRecord().value('idx')))

    def setItems(self, records):
        CRecordListModel.setItems(self, _CItemsContainer(self, records))

    def _queryTable(self):
        tables = self._tables

        db = QtGui.qApp.db

        queryTable = tables.E
        queryTable = queryTable.innerJoin(tables.C, tables.C['id'].eq(tables.E['client_id']))
        queryTable = queryTable.innerJoin(tables.A, tables.A['event_id'].eq(tables.E['id']))
        queryTable = queryTable.innerJoin(tables.AT, tables.AT['id'].eq(tables.A['actionType_id']))
        queryTable = queryTable.innerJoin(tables.APTn, tables.APTn['actionType_id'].eq(tables.AT['id']))
        queryTable = queryTable.innerJoin(
            tables.APn,
            db.joinAnd(
                [tables.APn['action_id'].eq(tables.A['id']), tables.APn['type_id'].eq(tables.APTn['id'])]
            )
        )
        queryTable = queryTable.innerJoin(tables.APN, tables.APN['id'].eq(tables.APn['id']))
        queryTable = queryTable.innerJoin(tables.N, tables.N['id'].eq(tables.APN['value']))

        queryTable = queryTable.innerJoin(
            tables.APTd,
            # Доза это 2
            db.joinAnd([tables.APTd['actionType_id'].eq(tables.AT['id']), tables.APTd['inActionsSelectionTable'].eq(2)])
        )
        queryTable = queryTable.innerJoin(
            tables.APd,
            db.joinAnd(
                [tables.APd['action_id'].eq(tables.A['id']), tables.APd['type_id'].eq(tables.APTd['id'])]
            )
        )
        queryTable = queryTable.innerJoin(tables.APD, tables.APD['id'].eq(tables.APd['id']))

        return queryTable

    def load(self, filters):
        self._filters = filters
        self.date = filters.get('date')
        self._cols[CGroupClientInvoiceModel.DAYDATA_COLUMN].setDate(self.date)
        self._load(self._filters)

    def _load(self, filters):
        records = self._getRecordList(filters)
        self.setItems(records)

    def _getRecordList(self, filters):
        db = QtGui.qApp.db
        queryTable = self._queryTable()
        tables = self._tables
        date = filters.get('date')
        nomenclatureId = filters.get('nomenclatureId')
        clientIds = filters.get('clientIds')
        actionIds = filters.get('actionIds')
        orgStructureIds = filters.get('orgStructureId')
        cond = [tables.A['deleted'].eq(0),
                tables.E['deleted'].eq(0),
                tables.AT['deleted'].eq(0),
                tables.AT['isDoesNotInvolveExecutionCourse'].eq(0),
                tables.APn['deleted'].eq(0),
                tables.APTn['deleted'].eq(0),
                tables.APd['deleted'].eq(0),
                tables.APTd['deleted'].eq(0),
                tables.A['status'].inlist([CActionStatus.started, CActionStatus.appointed])]
        if orgStructureIds[0]:
            cond.append(tables.A['orgStructure_id'].inlist(orgStructureIds))
        if date:
            if self.type == 1:
                cond.append(tables.A['begDate'].dateLt(date))
            else:
                cond.append(tables.A['begDate'].dateEq(date))
        if nomenclatureId:
            cond.append(tables.APN['value'].eq(nomenclatureId))
        else:
            cond.append(tables.APN['value'].isNotNull())
        cond.append(tables.APD['value'].gt(0))
        if clientIds:
            cond.append(tables.E['client_id'].inlist(clientIds))
        if actionIds:
            cond.append(tables.A['id'].inlist(actionIds))

        isDescOrder = forceBool(QtGui.qApp.preferences.appPrefs.get('GroupClientInvoiceModel_isDescOrder'+str(self.type), True))
        columnOrder = forceInt(QtGui.qApp.preferences.appPrefs.get('GroupClientInvoiceModel_ColumnOrder'+str(self.type), self.CLIENT_COLUMN))
        if self.BEGDATE_COLUMN == columnOrder:
            orderBy = [tables.A['begDate'].name()]
        elif self.NOMENCLATURE_COLUMN == columnOrder:
            orderBy = [tables.N['code'].name(),
                       tables.N['name'].name()]
        else:
            orderBy = [tables.C['lastName'].name(),
                       tables.C['firstName'].name(),
                       tables.C['patrName'].name(),
                       tables.A['id'].name()]
        order = ','.join(orderBy) + (u' ASC' if isDescOrder else u' DESC')
        actionIdList = db.getDistinctIdList(queryTable, [tables.A['id']], where=cond, order=order)
        if actionIdList:
            tableEPI = db.table('ActionExecutionPlan_Item')
            queryTable = queryTable.innerJoin(tableEPI, tableEPI['action_id'].eq(tables.A['id']))
            cond.append(tables.A['id'].inlist(actionIdList))
            cond.append(u'''NOT EXISTS(SELECT E2.id FROM Event AS E2 WHERE E2.id = getActionLeavedNextEventId(Event.id) AND E2.deleted = 0)
            OR EXISTS(SELECT E.id FROM Event AS E WHERE E.id = getActionLeavedNextEventId(Event.id) AND E.deleted = 0 AND E.execDate IS NULL
            AND EXISTS(SELECT A.id
            FROM Action AS A INNER JOIN ActionType AS AT ON AT.id = A.actionType_id
            WHERE A.event_id = E.id AND A.deleted = 0
            AND AT.deleted = 0 AND AT.flatCode LIKE 'leaved%%'
            AND ((A.endDate IS NOT NULL AND A.endDate >= Action.begDate)
            OR (A.endDate IS NULL AND A.plannedEndDate IS NOT NULL AND A.plannedEndDate >= Action.begDate)
            OR (A.endDate IS NULL AND A.plannedEndDate IS NULL AND A.begDate IS NOT NULL  AND A.begDate >= Action.begDate)
            OR (A.endDate IS NULL AND A.plannedEndDate IS NULL AND A.begDate IS NULL )))) ''')
            fields = [
                tables.N['id'].alias('nId'),
                tables.N['name'].alias('nName'),
                tables.N['code'].alias('ncode'),
                tables.N['dosageValue'],
                tables.A['id'].alias('actionId'),
                tables.C['id'].alias('clientId'),
                tables.C['lastName'],
                tables.C['firstName'],
                tables.C['patrName'],
                tables.APD['value'].alias('doses'),
                tables.A['begDate'],
                tables.A['note'],
                tableEPI['group_id'],
                tableEPI['id'].alias('EPIID')
            ]
            return db.getRecordList(queryTable, fields, where=cond, order=order)
        return []

    def reloadActionIds(self, actionIds):
        filters = dict(self._filters) if self._filters else {}
        filters['actionIds'] = actionIds

        records = self._getRecordList(filters)

        self._items.reloadRecords(records)

        self.emitAllChanged()

