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

from PyQt4 import QtGui
from PyQt4.QtGui import QAction, QItemSelection
from PyQt4.QtCore import Qt, pyqtSignature, QAbstractTableModel, QVariant, QModelIndex
from library.HierarchicalItemsListDialog import CHierarchicalItemsListDialog
from library.TreeModel import CDragDropDBTreeModelWithClassItems
from library.TableModel import CTableModel, CEnumCol, CRefBookCol, CTextCol #, CDateCol
from Ui_RBActionTypeSelectorDialog import Ui_ActionTypeSelectorDialog
from RefBooks.ActionType.List import CFindDialog
from library.Utils import formatRecordsCountInt

SexList = ['', u'М', u'Ж']

def formatCountSelectedRows(count):
    return u';  выделено ' + formatRecordsCountInt(count)


class CActionTypeSelector(Ui_ActionTypeSelectorDialog, CHierarchicalItemsListDialog):

    def __init__(self, parent):
        CHierarchicalItemsListDialog.__init__(self,
                                                  parent,
                                                  [CEnumCol(u'Класс', ['class'], [u'статус', u'диагностика', u'лечение', u'прочие мероприятия'], 10),
                                                   CRefBookCol(u'Группа', ['group_id'], 'ActionType', 10),
                                                   CTextCol(u'Код', ['code'], 20),
                                                   CTextCol(u'Наименование', ['name'], 40),
                                                   CEnumCol(u'Пол', ['sex'], SexList, 10),
                                                   CTextCol(u'Возраст', ['age'], 10),
                                                   CTextCol(u'Каб', ['office'], 5)],
                                                  'ActionType',
                                                  ['class', 'group_id', 'code', 'name', 'id'],
                                                  forSelect=True,
                                                  findClass=CFindDialog
                                                  )
        self.setWindowTitleEx(u'Выбор типов действий для добавления в шаблон')
        self.setSettingsTblItems()

    def preSetupUi(self):
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.addModels('Tree', CDragDropDBTreeModelWithClassItems(self, self.tableName, 'id', 'group_id', 'name', 'class', self.order))
        self.addModels('Table',CTableModel(self, self.cols, self.tableName))
        self.addModels('SelectBox', selectBoxDataModel())
        self.modelTree.setLeavesVisible(True)
        self.modelTree.setClassItems((
                                     (u'Статус', 0),
                                     (u'Диагностика', 1),
                                     (u'Лечение', 2),
                                     (u'Прочие мероприятия', 3)))
        self.addObject('actSelectAllRow', QtGui.QAction(u'Выделить все строки', self))
        self.addObject('actClearSelection', QtGui.QAction(u'Снять выделение', self))
        self.addObject('actAddItemsToSelectBox', QtGui.QAction(u'Добавить к выбранным', self))
        self.addObject('actSelectAllInSelectBox', QtGui.QAction(u'Выделить все строки', self))
        self.addObject('actClearAllInSelectBox', QtGui.QAction(u'Снять выделение', self))
        self.addObject('actDelItemsFromSelectBox', QtGui.QAction(u'Удалить из списка', self))

    def postSetupUi(self):
        # comboboxes
        # Блокируем сигналы от комбобоксов перед инициализацией,
        # иначе в консоли будут ошибки от неинициализированных комбобоксов
        specialValues = [(-2, u'не определен', u'не определен'),
                         (-1, u'определен', u'определен')]
        self.cmbService.setTable('rbService', addNone=True, specialValues=specialValues)
        self.cmbService.setValue(0)
        self.cmbQuotaType.setTable('QuotaType', addNone=True, specialValues=specialValues)
        self.cmbQuotaType.setValue(0)
        self.cmbTissueType.setTable('rbTissueType', addNone=True, specialValues=specialValues)
        self.cmbTissueType.setValue(0)
        self.cmbServiceType.insertSpecialValue('-', None)
        CHierarchicalItemsListDialog.postSetupUi(self)
        self.tblItems.addPopupActions([self.actSelectAllRow,
                                       self.actClearSelection,
                                       self.actAddItemsToSelectBox])
        self.itemSelectBox.addPopupActions([self.actSelectAllInSelectBox,
                                       self.actClearAllInSelectBox,
                                       self.actDelItemsFromSelectBox])
        self.itemListControlsEnable(bool(self.tblItems.model().rowCount()))
        self.selectBoxContrlosEnable(bool(self.modelSelectBox.rowCount()))
        self.btnEdit.setVisible(False)
        self.btnNew.setVisible(False)
        self.setupItemSelectBoxView()
        self.setModels(self.itemSelectBox, self.modelSelectBox, self.selectionModelSelectBox)
        self.modelSelectBox.reset()
        # Соединяем сигналы
        self.tblItems.selectionModel().selectionChanged.connect(self.tableItemsSelectionChanged)
        self.tableItemsSelectionChanged(QItemSelection(), QItemSelection())
        self.btnAddItemToSelectBox.clicked.connect(self.on_actAddItemsToSelectBox_triggered)
        self.btnRemoveItemFromSelectBox.clicked.connect(self.on_actDelItemsFromSelectBox_triggered)
        self.tblItems.doubleClicked.connect(self.on_actAddItemsToSelectBox_triggered)
        self.itemSelectBox.doubleClicked.connect(self.on_actDelItemsFromSelectBox_triggered)
        self.cmbService.currentIndexChanged.connect(self.filterCmbCurrentIndexChanged)
        self.cmbQuotaType.currentIndexChanged.connect(self.filterCmbCurrentIndexChanged)
        self.cmbTissueType.currentIndexChanged.connect(self.filterCmbCurrentIndexChanged)
        self.cmbServiceType.currentIndexChanged.connect(self.filterCmbCurrentIndexChanged)
        self.cmbIsPreferable.currentIndexChanged.connect(self.filterCmbCurrentIndexChanged)
        self.cmbShowInForm.currentIndexChanged.connect(self.filterCmbCurrentIndexChanged)
        self.treeItems.expandToDepth(0)

    def tableItemsSelectionChanged(self, selected, deselected):
        self.lblCountSelectedRows.setText(formatCountSelectedRows(len(self.tblItems.selectedItemIdList())))

    def setupItemSelectBoxView(self):
        self.itemSelectBox.verticalHeader().hide()
        self.itemSelectBox.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.itemSelectBox.setAlternatingRowColors(True)
        self.itemSelectBox.horizontalHeader().setStretchLastSection(True)

    def setSettingsTblItems(self):
        self.tblItems.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.itemSelectBox.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)

    def getSelectedItems(self):
        records = []
        selectedIdList = self.tblItems.selectedItemIdList()
        for id in selectedIdList:
            records.append(self.modelTable.getRecordById(id))
        return records

    def updateAvailableTreeIdList(self):
        filterCond = self.filterConditions()
        cond = filterCond if filterCond else '1'
        table = self.modelTable.table()
        list = QtGui.qApp.db.getIdList(table.name(),
                          'id',
                           cond)
        allList = QtGui.qApp.db.getTheseAndParents(table, 'group_id', list)
        self.modelTree.setAvailableItemIdList(allList)

    def filterConditions(self):
        db = QtGui.qApp.db
        tables = [(db.table('ActionType_Service'), 'service_id'),
                  (db.table('ActionType_QuotaType'), 'quotaType_id'),
                  (db.table('ActionType_TissueType'), 'tissueType_id')]
        serviceId = self.cmbService.value()
        quotaTypeId = self.cmbQuotaType.value()
        tissueTypeId = self.cmbTissueType.value()

        tableActionType = db.table('ActionType')
        cond = []
        for idx, id in enumerate([serviceId, quotaTypeId, tissueTypeId]):
            table, fieldName = tables[idx]
            condTmp = [table['master_id'].eq(tableActionType['id'])]
            if id > 0:
                condTmp.append(table[fieldName].eq(id))
                cond.append(db.existsStmt(table, condTmp))
            elif id == -1:
                cond.append(db.existsStmt(table, condTmp))
            elif id == -2:
                cond.append(db.notExistsStmt(table, condTmp))

        serviceType = self.cmbServiceType.value()
        if serviceType is not None:
            cond.append(self.modelTable.table()['serviceType'].eq(serviceType))

        showInForm = self.cmbShowInForm.currentText()
        if showInForm != u'не определено':
            cond.append(self.modelTable.table()['showInForm'].eq(int(showInForm == u'да')))
            self.modelTree.setShowInForm(True) if showInForm == u'да' else self.modelTree.setShowInForm(False)
        else:
            self.modelTree.setShowInForm(False)

        isPreferable = self.cmbIsPreferable.currentText()
        if isPreferable != u'не определено':
            cond.append(self.modelTable.table()['isPreferable'].eq(int(isPreferable == u'да')))

        return cond

    def filterCmbCurrentIndexChanged(self):
        id = self.currentItemId()
        self.updateAvailableTreeIdList()
        self.findById(id)

    def currentClass(self):
        return self.modelTree.itemClass(self.treeItems.currentIndex())

    def select(self, props=None):
        table = self.modelTable.table()
        groupId = self.currentGroupId()
        className = self.currentClass()
        cond = [ table['group_id'].eq(groupId) ]
        cond.append(table['deleted'].eq(0))
        cond.append(table['class'].eq(className))

        filterCond = self.filterConditions()
        if filterCond:
            cond.extend(filterCond)

        list = QtGui.qApp.db.getIdList(table.name(),
                           'id',
                           cond,
                           self.order)
        self.lblCountRows.setText(formatRecordsCount(len(list)))
        selectedRows = 1 if len(list) > 0 else 0
        return list

    def renewListAndSetToWithoutUpdate(self, itemId=None):
        if not itemId:
            itemId = self.tblItems.currentItemId()
        idList = self.select(self.props)
        self.tblItems.setIdList(idList, itemId)
        self.itemListControlsEnable(bool(idList))

    def itemListControlsEnable(self, enable):
        self.actSelectAllRow.setEnabled(enable)
        self.actClearSelection.setEnabled(enable)
        self.btnAddItemToSelectBox.setEnabled(enable)
        self.actAddItemsToSelectBox.setEnabled(enable)

    def selectBoxContrlosEnable(self, enable):
        self.actSelectAllInSelectBox.setEnabled(enable)
        self.actClearAllInSelectBox.setEnabled(enable)
        self.actDelItemsFromSelectBox.setEnabled(enable)
        self.btnRemoveItemFromSelectBox.setEnabled(enable)
        self.btnSelect.setEnabled(enable)

    @pyqtSignature('')
    def on_actAddItemsToSelectBox_triggered(self):
        selList = self.getSelectedItems()
        for record in selList:
            newindex = self.modelSelectBox.addItem(record)
        self.modelSelectBox.reset()
        self.itemSelectBox.setCurrentIndex(newindex)
        self.selectBoxContrlosEnable(bool(self.modelSelectBox.rowCount()))

    @pyqtSignature('')
    def on_actDelItemsFromSelectBox_triggered(self):
        indexList = self.selectionModelSelectBox.selectedRows()
        if indexList:
            removeItemsCount = len(indexList)
            indexList.sort(key=lambda index: index.row())
            tailItemRow = indexList[-1].row()
            for index in reversed(indexList):
                if index.isValid():
                    self.modelSelectBox.removeRows(index.row(), index.row(), QModelIndex())
            rowToSelect = tailItemRow + 1 - removeItemsCount
            if (rowToSelect < self.modelSelectBox.rowCount()):
                self.itemSelectBox.selectRow(rowToSelect)
            else:
                self.itemSelectBox.selectRow(self.modelSelectBox.rowCount() - 1)
            self.selectBoxContrlosEnable(bool(self.modelSelectBox.rowCount()))

    @pyqtSignature('')
    def on_actSelectAllInSelectBox_triggered(self):
        self.itemSelectBox.selectAll()

    @pyqtSignature('')
    def on_actClearAllInSelectBox_triggered(self):
        self.itemSelectBox.clearSelection()

    @pyqtSignature('')
    def on_actSelectAllRow_triggered(self):
        self.tblItems.selectAll()

    @pyqtSignature('')
    def on_actClearSelection_triggered(self):
        self.tblItems.clearSelection()

    @pyqtSignature('QModelIndex')
    def on_tblItems_doubleClicked(self, index):
        pass


class selectBoxDataModel(QAbstractTableModel):
    def __init__(self):
        super(selectBoxDataModel, self).__init__()
        self._modelData = []
        self._rows = 0

    def rowCount(self, parent=QModelIndex()):
        return self._rows

    def columnCount(self, parent = QModelIndex()):
        return 2

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        column = index.column()
        row    = index.row()

        if role == Qt.DisplayRole:
            if column == 0:
                return self._modelData[row].value('code')
            elif column == 1:
                return self._modelData[row].value('name')

    def headerData(self, col, orientation, role):
        if role == Qt.DisplayRole:
            if col == 0 and orientation == Qt.Horizontal:
                return u'Код'
            elif col == 1 and orientation == Qt.Horizontal:
                return u'Наименование'

    def addItem(self, item):
        self._modelData.append(item)
        newindex = self.createIndex(self._rows, 0, self)
        self._rows += 1
        return newindex

    def removeRows(self, row, count, parent):
        if 0 <= row < self._rows:
            self.beginRemoveRows(parent, row, count)
            self._modelData.pop(row)
            self._rows -= 1
            self.endRemoveRows()


def formatRecordsCount(count):
    if count:
        return u'в списке '+formatRecordsCountInt(count)
    else:
        return u'список пуст'