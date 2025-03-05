# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2021 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import Qt, QEvent, SIGNAL, pyqtSignature

from Events.ActionsModel import CActionRecordItem
from library.PrintInfo import CInfoContext
from library.Utils import forceRef, toVariant, forceBool

from library.InDocTable              import CInDocTableView

from Events.ActionTypeComboBox       import CActionTypeComboBox
from Events.ActionEditDialog         import CActionEditDialog
from library.ClientRecordProperties import CRecordProperties
from Users.Rights                    import urCanDeleteActionNomenclatureExpense


class CActionsTableView(CInDocTableView):
    def __init__(self, parent):
        CInDocTableView.__init__(self, parent)

        self.delegate = CActionTypeItemDelegate(self)
        self.setItemDelegate(self.delegate)
        self.setTabKeyNavigation(False)
        self._actOpenInEditor = None
        self._actSortByBegDate = None
        self._actSortByEndDate = None

        self._parent = None

    def setModel(self, model):
        self._addIdentificationInfoAction()
        if getattr(model, '__groupingAllowed__', False):
            self._addTouchGroupingAction()
            self.connect(model, SIGNAL("rowIndexActivated(int)"), self._on_groupRowActivated)
        return CInDocTableView.setModel(self, model)

    def _on_groupRowActivated(self, row):
        if row < 0:
            return

        index = self.model().index(row, 0)
        self.setCurrentIndex(index)

    def setParentWidget(self, parent):
        self._parent = parent

    def _addIdentificationInfoAction(self):
        if self._popupMenu is None:
            self.createPopupMenu()
        self._actIdentificationInfo = QtGui.QAction(u'Показать идентификаторы действия', self)
        self._popupMenu.addAction(self._actIdentificationInfo)
        self.connect(self._actIdentificationInfo, SIGNAL('triggered()'), self.on_actIdentificationInfo_triggered)
        self.addAction(self._actIdentificationInfo)
    
    def _addTouchGroupingAction(self):
        if self._popupMenu is None:
            self.createPopupMenu()
        self.connect(self._popupMenu, SIGNAL('aboutToShow()'), self.on_actTouchGroupingShow)
        self._actTouchGrouping = QtGui.QAction(u'Группировать элементы', self)
        self._popupMenu.addAction(self._actTouchGrouping)
        self.connect(self._actTouchGrouping, SIGNAL('triggered()'), self.on_touchGrouping)
        self.connect(self, SIGNAL('doubleClicked(QModelIndex)'), self.on_touchGrouping)
        self.addAction(self._actTouchGrouping)

    
    def on_actTouchGroupingShow(self):
        row = self.currentIndex().row()
        model = self.model()
        self._actTouchGrouping.setEnabled(model.canRowBeGrouped(row))
        expanded = model.getExpandedByRow(row)
        if expanded:
            self._actTouchGrouping.setText(u'Группировать элементы')
        else:
            self._actTouchGrouping.setText(u'Раскрыть элементы')

    @pyqtSignature('QModelIndex')
    def on_actIdentificationInfo_triggered(self, index=None):
        row = index.row() if index else self.currentIndex().row()
        model = self.model()
        model.showIdentificationInfo(row)
    
    @pyqtSignature('QModelIndex')
    def on_touchGrouping(self, index=None):
        row = index.row() if index else self.currentIndex().row()
        model = self.model()
        model.touchGrouping(row)

    def addOpenInEditor(self):
        if self._popupMenu is None:
            self.createPopupMenu()
        self.connect(self._popupMenu, SIGNAL('aboutToShow()'), self.on_actOpenInEditorShow)
        self._actOpenInEditor = QtGui.QAction(u'Открыть в редакторе', self)
        self._actOpenInEditor.setShortcuts(['F2'])
        self._popupMenu.addAction(self._actOpenInEditor)
        self.connect(self._actOpenInEditor, SIGNAL('triggered()'), self.on_openInEditor)
        self.addAction(self._actOpenInEditor)


    def addSortingRow(self):
        if self._popupMenu is None:
            self.createPopupMenu()
        self.connect(self._popupMenu, SIGNAL('aboutToShow()'), self.on_actSortByBegDateShow)
        self._actSortByBegDate = QtGui.QAction(u'Отсортировать по дате начала', self)
        self._popupMenu.addAction(self._actSortByBegDate)
        self.connect(self._actSortByBegDate, SIGNAL('triggered()'), self.on_sortByBegDate)
        self.addAction(self._actSortByBegDate)
        self.connect(self._popupMenu, SIGNAL('aboutToShow()'), self.on_actSortByEndDateShow)
        self._actSortByEndDate = QtGui.QAction(u'Отсортировать по дате окончания', self)
        self._popupMenu.addAction(self._actSortByEndDate)
        self.connect(self._actSortByEndDate, SIGNAL('triggered()'), self.on_sortByEndDate)
        self.addAction(self._actSortByEndDate)


    def on_deleteRows(self):
        CInDocTableView.on_deleteRows(self)
        if getattr(self.model(), '__groupingAllowed__', False):
            self.model().afterRowsDeleting()
        self.emitDelRows()


    def emitDelRows(self):
        self.emit(SIGNAL('delRows()'))


    def on_actOpenInEditorShow(self):
        if self._actOpenInEditor:
            self._actOpenInEditor.setEnabled(bool(self.model().items()))


    def on_actSortByBegDateShow(self):
        if self._actSortByBegDate:
            self._actSortByBegDate.setEnabled(bool(self.model().items()))


    def on_actSortByEndDateShow(self):
        if self._actSortByEndDate:
            self._actSortByEndDate.setEnabled(bool(self.model().items()))


    def on_openInEditor(self):
        index = self.currentIndex()
        if index.isValid():
            row = index.row()
            items = self.model()._mapProxyRow2Group
            if 0 <= row < len(self.model()._actionModel.items()):
                oldRecord, oldAction = items[row].getItem(row)
                dialog = CActionEditDialog(self)
                dialog.save = lambda: True
                dialog.setForceClientId(self._parent.clientId())
                dialog.setRecord(QtSql.QSqlRecord(oldRecord))
                dialog.setReduced(True)
                self.copyAction(oldAction, dialog.action)
                eventInfo = self._parent.eventEditor.getEventInfo(CInfoContext())
                for i, (rec, act) in enumerate(eventInfo._actions._rawItems):
                    if act == oldAction:
                        del eventInfo._actions._rawItems[i]
                        del eventInfo._actions._items[i]
                dialog.setEventInfo(eventInfo)
                if dialog.exec_():
                    items[row].getItem(row)._data = CActionRecordItem(dialog.getRecord(), dialog.action)
                    self._parent.onActionCurrentChanged()
                    if hasattr(self._parent.eventEditor, 'modelActionsSummary'):
                        self._parent.eventEditor.modelActionsSummary.regenerate()
                    if hasattr(self._parent.eventEditor, 'tabCash') and hasattr(self._parent.eventEditor.tabCash, 'modelAccActions'):
                        self._parent.eventEditor.tabCash.modelAccActions.regenerate()
                    self._parent._onActionChanged()

                dialog.deleteLater()


    def on_sortByBegDate(self):
        self.model()._groups._setNewOrder('begDate')
        self.model()._resetData()
        self.model()._groups._resetModelNewItemsOrder()
        self.model().emitRowsChanged(0, len(self.model()._groups))



    def on_sortByEndDate(self):
        self.model()._groups._setNewOrder('endDate')
        self.model()._resetData()
        self.model()._groups._resetModelNewItemsOrder()
        self.model().emitRowsChanged(0, len(self.model()._groups))


    def sortByReferrals(self):
        self.model()._groups._setNewOrder('alfalab')
        self.model()._resetData()
        self.model()._groups._resetModelNewItemsOrder()
        self.model().emitRowsChanged(0, len(self.model()._groups))

    def copyAction(self, sourceAction, targetAction):
        targetAction._propertiesByName.clear()
        targetAction._propertiesById.clear()
        if hasattr(targetAction, '_executionPlan'):
            targetAction._executionPlan.clear()
        targetAction._properties = []

        for sourceProperty in sourceAction.getProperties():
            sourcePropertyTypeId = sourceProperty.type().id
            targetProperty = targetAction.getPropertyById(sourcePropertyTypeId)
            targetProperty.copy(sourceProperty)

    def showRecordProperties(self):
        currentRow = self.currentIndex().row()
        items = self.model().items()
        if currentRow < len(items):
            itemId = forceRef(items[currentRow][0].value('id'))
        else:
            return
        table = self.model().table
        CRecordProperties(self, table, itemId).exec_()


    def on_popupMenu_aboutToShow(self):
        from Events.Action import CActionTypeCache
        CInDocTableView.on_popupMenu_aboutToShow(self)
        if self._CInDocTableView__actDeleteRows:
            model = self.model()
            row = self.currentIndex().row()
            items = model.items()
            if 0 <= row < len(items):
                record, action = items[row]
                if record:
                    actionTypeId = forceRef(record.value('actionType_id'))
                    actionType = CActionTypeCache.getById(actionTypeId) if actionTypeId else None
                    if actionType and actionType.isNomenclatureExpense:
                        if QtGui.qApp.userHasRight(urCanDeleteActionNomenclatureExpense):
                            canDeleteRow = self._CInDocTableView__actDeleteRows.isEnabled()
                        else:
                            canDeleteRow = False
                        self._CInDocTableView__actDeleteRows.setEnabled(canDeleteRow)
                    # if actionType and u'inspection_mse' in actionType.flatCode.lower():
                    #     self._CInDocTableView__actDeleteRows.setEnabled(False)
        if self._CInDocTableView__actRecordProperties:
            enabled = False
            model = self.model()
            row = self.currentIndex().row()
            items = model.items()
            if 0 <= row < len(items):
                record, action = items[row]
                enabled = forceBool(record.value('id') if record else None)
            self._CInDocTableView__actRecordProperties.setEnabled(enabled)
        self.emit(SIGNAL('popupMenuAboutToShow()'))


class CActionTypeItemDelegate(QtGui.QItemDelegate):
    def __init__(self, parent):
        QtGui.QItemDelegate.__init__(self, parent)


    def createEditor(self, parent, option, index):
        editor = CActionTypeComboBox(parent)
        editor.setClass(index.model().actionTypeClass)
        editor.setDisabledActionTypeIdList(index.model().disabledActionTypeIdList)
        preferredWidth = self.parent().model().col.preferredWidth
        editor.setPreferredWidth(preferredWidth)
        dialog = index.model().eventEditor
        editor.setFilter(dialog.clientSex, dialog.clientAge)
        return editor


    def setEditorData(self, editor, index):
        model = index.model()
        editor.setValue(forceRef(model.data(index, Qt.EditRole)))


    def setModelData(self, editor, model, index):
        model.setData(index, toVariant(editor.value()))


    def emitCommitDataAndClose(self, editor, hint=QtGui.QAbstractItemDelegate.NoHint):
        self.emit(SIGNAL('commitData(QWidget *)'), editor)
        self.emit(SIGNAL('closeEditor(QWidget *,QAbstractItemDelegate::EndEditHint)'), editor, hint)


    def eventFilter(self, editor, event):
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Tab:
                if editor is not None:
                    self.emitCommitDataAndClose(editor)
                self.parent().focusNextChild()
                return True
            elif event.key() == Qt.Key_Backtab:
                if editor is not None:
                    self.emitCommitDataAndClose(editor)
                self.parent().focusPreviousChild()
                return True
            elif event.key() == Qt.Key_Return:
                if editor is not None:
                    self.emitCommitDataAndClose(editor)
#                event.accept()
                return True
        return QtGui.QItemDelegate.eventFilter(self, editor, event)
