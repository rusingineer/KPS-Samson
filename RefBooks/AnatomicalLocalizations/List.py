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

from PyQt4                          import QtGui
from PyQt4.QtCore                   import pyqtSignature, QDateTime, Qt, QModelIndex
from library.Utils                  import forceRef, forceString, forceBool, toVariant
from library.TreeModel              import CDBTreeModel
from library.TableModel             import CTableModel, CTextCol, CRefBookCol
from library.IdentificationModel    import CIdentificationModel
from library.DialogBase             import CDialogBase
from Ui_ListDialog                  import Ui_ListDialog
from Ui_EditDialog                  import Ui_EditDialog
from Ui_FilterDialog                import Ui_FilterDialog


class CRBAnatomicalLocalizationsList(CDialogBase, Ui_ListDialog):
    def __init__(self, parent=None):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.setWindowTitle(u'Анатомические локализации')
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.treeModel = CDBTreeModel(self, 'rbAnatomicalLocalizations', 'id', 'group_id', 'name')
        self.tableModel = CAnatomicalLocalizationsModel(self)
        self.treeModel.setLeavesVisible(True)
        self.treeView.setModel(self.treeModel)
        self.tableView.setModel(self.tableModel)
        self.treeView.setHeaderHidden(True)
        self.tableView.horizontalHeader().setSortIndicatorShown(True)
        self.tableView.horizontalHeader().sectionClicked.connect(self.setOrder)
        self.tableView.enableColsHide()
        self.tableView.enableColsMove()
        self._filterDialog = CRBAnatomicalLocalizationsFilterDialog(self)

        self.setOrder(2)  # сортировка по наименованию
        self.treeView.selectionModel().selectionChanged.connect(self.on_selectionChanged)
        index = self.treeModel.index(0, 0)
        self.selectionFlags = QtGui.QItemSelectionModel.ClearAndSelect | QtGui.QItemSelectionModel.Rows
        self.treeView.setExpanded(index, True)
        self.treeView.selectionModel().select(index, self.selectionFlags)


    def resetAndSelectItem(self, itemId):
        self.saveExpandedState()
        self.treeModel.getRootItem().update()
        self.restoreExpandedState()
        self.on_selectionChanged(None, None)
        if not itemId:
            return
        db = QtGui.qApp.db
        groupId = forceRef(db.translate('rbAnatomicalLocalizations', 'id', itemId, 'group_id'))
        index = self.treeModel.findItemId(groupId)
        if index and index.isValid():
            self.treeView.selectionModel().select(index, self.selectionFlags)
            while index and index.isValid():
                self.treeView.setExpanded(index, True)
                index = index.parent()
        self.tableView.setCurrentItemId(itemId)


    def setOrder(self, column):
        self.tableView.setOrder(column)
        self.tableModel.headerSortingCol = {column: self.tableView._isDesc}
        self.tableModel.sortDataModel()


    def saveExpandedState(self):
        def saveStateInternal(model,  parent=QModelIndex(),  prefix=''):
            for column in xrange(model.columnCount(parent)):
                for row in xrange(model.rowCount(parent)):
                    index = model.index(row, column, parent)
                    if index.isValid():
                        prefix += index.internalPointer().name() + '_'
                        isExpanded = self.treeView.isExpanded(index)
                        if isExpanded:
                            self.expandedItemsState[prefix] = isExpanded
                            saveStateInternal(model, index, prefix)
        self.expandedItemsState = {}
        # self.selectedIndexes = self.treeView.selectionModel().selectedIndexes()
        saveStateInternal(self.treeModel)


    def restoreExpandedState(self):
        def restoreStateInternal(model,  parent=QModelIndex(),  prefix=''):
            for column in xrange(model.columnCount(parent)):
                for row in xrange(model.rowCount(parent)):
                    index = model.index(row, column, parent)
                    if index.isValid():
                        prefix += index.internalPointer().name() + '_'
                        isExpanded = self.expandedItemsState.get(prefix, False)
                        if isExpanded:
                            self.treeView.setExpanded(index, isExpanded)
                            restoreStateInternal(model, index, prefix)
        restoreStateInternal(self.treeModel)
        self.expandedItemsState.clear()
        # for index in self.selectedIndexes:
        #     self.treeView.selectionModel().select(index, self.selectionFlags)
        self.selectedIndexes = []


    @pyqtSignature('bool')
    def on_btnClose_clicked(self, checked=False):
        self.accept()


    @pyqtSignature('bool')
    def on_btnNew_clicked(self, checked=False):
        dialog = CEditDialog(self)
        if dialog.exec_():
            self.resetAndSelectItem(dialog.itemId())


    @pyqtSignature('bool')
    def on_btnEdit_clicked(self, checked=False):
        itemId = self.tableView.currentItemId()
        if itemId:
            editDialog = CEditDialog(self)
            editDialog.setItemId(itemId)
            if editDialog.exec_():
                self.resetAndSelectItem(itemId)


    @pyqtSignature('QModelIndex')
    def on_tableView_doubleClicked(self, index):
        self.on_btnEdit_clicked()


    @pyqtSignature('bool')
    def on_btnFilter_clicked(self, checked=False):
        if self._filterDialog.exec_():
            itemId = self._filterDialog.filteredItemId()
            self.resetAndSelectItem(itemId)


    def on_selectionChanged(self, select, deselect):
        indexes = self.treeView.selectionModel().selectedIndexes()
        if indexes:
            index = indexes[0]
            if index.isValid():
                db = QtGui.qApp.db
                table = db.table('rbAnatomicalLocalizations')
                item = index.internalPointer()
                cond = table['group_id'].eq(item.id()) if item and item.id() else table['group_id'].isNull()
                idList = db.getIdList(table, 'id', cond, self.tableView.order())
                self.tableModel.setIdList(idList)


class CEditDialog(CDialogBase, Ui_EditDialog):
    def __init__(self, parent=None):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.setWindowTitle(u'Анатомические локализации: редактор')
        self.cmbGroup.setTable('rbAnatomicalLocalizations')
        self.cmbGroup.setValue(None)
        self._itemId = None
        self.modelIdentification = CAnatomicalLocalizationsIdentificationModel(self)
        self.tblIdentification.setModel(self.modelIdentification)
        self.tblIdentification.addPopupDelRow()
        self.tblIdentification.setDelRowsChecker(self.modelIdentification.delRowsChecker)


    def setItemId(self, itemId):
        self._itemId = itemId
        record = QtGui.qApp.db.getRecord('rbAnatomicalLocalizations', '*', itemId)
        self.edtCode.setText(forceString(record.value('code')))
        self.edtName.setText(forceString(record.value('name')))
        self.edtLatinName.setText(forceString(record.value('latinName')))
        self.cmbGroup.setValue(forceRef(record.value('group_id')))
        self.edtArea.setText(forceString(record.value('area')))
        self.edtSynonyms.setText(forceString(record.value('synonyms')))
        self.chkLaterality.setChecked(forceBool(record.value('laterality')))
        self.modelIdentification.loadItems(itemId)


    def itemId(self):
        return self._itemId


    def getRecord(self):
        record = QtGui.qApp.db.record('rbAnatomicalLocalizations')
        if not self._itemId:
            record.setValue('createPerson_id', toVariant(QtGui.qApp.userId))
            record.setValue('createDatetime', toVariant(QDateTime.currentDateTime()))
        record.setValue('id', toVariant(self._itemId))
        record.setValue('modifyPerson_id', toVariant(QtGui.qApp.userId))
        record.setValue('modifyDatetime', toVariant(QDateTime.currentDateTime()))
        record.setValue('code', toVariant(self.edtCode.text()))
        record.setValue('name', toVariant(self.edtName.text()))
        record.setValue('latinName', toVariant(self.edtLatinName.text()))
        record.setValue('group_id', toVariant(self.cmbGroup.value()))
        record.setValue('area', toVariant(self.edtArea.text()))
        record.setValue('synonyms', toVariant(self.edtSynonyms.text()))
        record.setValue('laterality', toVariant(self.chkLaterality.isChecked()))
        return record


    def accept(self):
        record = self.getRecord()
        itemId = QtGui.qApp.db.insertOrUpdate('rbAnatomicalLocalizations', record)
        self.modelIdentification.saveItems(itemId)
        self._itemId = itemId
        CDialogBase.accept(self)



class CAnatomicalLocalizationsIdentificationModel(CIdentificationModel):
    def __init__(self, parent):
        CIdentificationModel.__init__(self, parent, 'rbAnatomicalLocalizations_Identification', '')
        self._cols[0].setFilter('domain = "rbAnatomicalLocalizations"')
        self._cols[2].canBeEmpty = True
        self.addHiddenCol('createDatetime')
        self.addHiddenCol('modifyDatetime')
        self.addHiddenCol('createPerson_id')
        self.addHiddenCol('modifyPerson_id')


    def saveItems(self, masterId):
        for record in self._items:
            if forceRef(record.value('master_id')) == masterId:
                record.setValue('modifyPerson_id', toVariant(QtGui.qApp.userId))
                record.setValue('modifyDatetime', toVariant(QDateTime.currentDateTime()))
            if record.isNull('createPerson_id'):
                record.setValue('createPerson_id', toVariant(QtGui.qApp.userId))
                record.setValue('modifyPerson_id', toVariant(QtGui.qApp.userId))
            if record.isNull('createDatetime'):
                record.setValue('createDatetime', toVariant(QDateTime.currentDateTime()))
                record.setValue('modifyDatetime', toVariant(QDateTime.currentDateTime()))
        CIdentificationModel.saveItems(self, masterId)



class CAnatomicalLocalizationsModel(CTableModel):
    def __init__(self, parent=None):
        CTableModel.__init__(self, parent, [
                CRefBookCol(u'Группа', ['group_id'], 'rbAnatomicalLocalizations', 40),
                CTextCol(u'Код', ['code'], 20),
                CTextCol(u'Наименование', ['name'], 40),
                CTextCol(u'Область', ['area'], 20),
            ], 'rbAnatomicalLocalizations')
        self._mapColumnToOrder = {
            'code': 'code',
            'name': 'name',
            'area': 'area',
            'group_id': 'group_id',
        }


class CRBAnatomicalLocalizationsFilterDialog(CDialogBase, Ui_FilterDialog):
    def __init__(self, parent=None):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.setWindowTitle(u'Анатомические локализации: фильтр')
        self.cmbGroup.setTable('rbAnatomicalLocalizations',
            filter='EXISTS(SELECT NULL FROM rbAnatomicalLocalizations T WHERE T.group_id = rbAnatomicalLocalizations.id)')
        self.cmbGroup.setValue(None)
        self.tableModel = CAnatomicalLocalizationsModel(self)
        self.tableView.setModel(self.tableModel)
        self.tableView.horizontalHeader().setSortIndicatorShown(True)
        self.tableView.horizontalHeader().sectionClicked.connect(self.setOrder)
        self._itemId = None
        self.tableView.enableColsHide()
        self.tableView.enableColsMove()
        self.setOrder(2)  # сортировка по наименованию


    def setOrder(self, column):
        self.tableView.setOrder(column)
        self.tableModel.headerSortingCol = {column: self.tableView._isDesc}
        self.tableModel.sortDataModel()


    def filteredItemId(self):
        return self._itemId


    def applyFilter(self):
        code = forceString(self.edtCode.text())
        name = forceString(self.edtName.text())
        groupId = self.cmbGroup.value()
        db = QtGui.qApp.db
        table = db.table('rbAnatomicalLocalizations')
        cond = []
        if code:
            cond.append(table['code'].like('%' + code + '%'))
        if name:
            cond.append(table['name'].like('%' + name + '%'))
        if groupId:
            cond.append(table['group_id'].eq(groupId))
        idList = db.getIdList(table, 'id', cond, self.tableView.order())
        self.tableModel.setIdList(idList)


    @pyqtSignature('QModelIndex')
    def on_tableView_doubleClicked(self, index):
        self._itemId = self.tableView.currentItemId()
        self.accept()


    @pyqtSignature('bool')
    def on_btnReset_clicked(self, checked=False):
        self.edtCode.setText('')
        self.edtName.setText('')
        self.cmbGroup.setValue(None)
        self.tableModel.setIdList([])


    @pyqtSignature('bool')
    def on_btnApply_clicked(self, checked=False):
        self.applyFilter()
        if self.tableModel.rowCount() == 1:
            self._itemId = self.tableModel._idList[0]
            self.accept()


    @pyqtSignature('bool')
    def on_btnCancel_clicked(self, checked=False):
        self.reject()


    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Enter, Qt.Key_Return):
            self.on_btnApply_clicked()
        else:
            CDialogBase.keyPressEvent(self, event)
