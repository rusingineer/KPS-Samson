# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2020 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

import json
import re

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QByteArray, QMimeData, pyqtSignature, QString, SIGNAL

from library.HierarchicalItemsListDialog import CHierarchicalItemsListDialog
from library.interchange                 import getLineEditValue, setLineEditValue
from library.SortFilterProxyTreeModel    import CSortFilterProxyTreeModel
from library.DialogBase                  import CDialogBase

from library.ItemsListDialog             import CItemEditorBaseDialog
from library.TableModel                  import CTextCol, CTableModel, sortDataModel
from library.TreeModel                   import CDragDropDBTreeModel, CDBTreeItem
from library.Utils                       import forceInt, forceRef, forceString, toVariant

from Ui_RBThesaurusItemEditor            import Ui_ThesaurusItemEditorDialog
from Ui_RBThesaurusFilter                import Ui_RBThesaurusFilterDialog


class CDBTreeItemWithCode(CDBTreeItem):
    def __init__(self, parent, name, code, id, model):
       CDBTreeItem.__init__(self, parent, name, id, model)
       self._code = code

    def code(self):
        return self._code



class CPreloadDragDropDBTreeModel(CDragDropDBTreeModel):
    def __init__(self, parent, tableName, idColName, groupColName, nameColName, codeColName, order=None):
        CDragDropDBTreeModel.__init__(self, parent, tableName, idColName, groupColName, nameColName, order)
        self.codeColName = codeColName
        self._records = {}  # { group_id : [ records ] }
        self.__preload()


    def __preload(self):
        db = QtGui.qApp.db
        table = db.table(self.tableName)
        cols = [self.idColName, self.nameColName, self.codeColName, self.groupColName]
        cond = []
        if self._filter:
            cond.append(self._filter)
        if table.hasField('deleted'):
            cond.append(table['deleted'].eq(0))
        if not self.leavesVisible:
            alias = table.alias(self.tableName+'2')
            cond.append(db.existsStmt(alias, alias[self.groupColName].eq(table[self.idColName])))

        self._records = {}
        for record in db.getRecordList(self.tableName, cols, cond, self.order):
            group = forceRef(record.value(3))
            if not self._records.has_key(group):
                self._records[group] = []
            self._records[group].append(record)


    def getItemListByRecords(self, recordList, group):
        result = []
        for record in recordList:
            id   = forceRef(record.value(0))
            name = forceString(record.value(1))
            code = forceString(record.value(2))
            result.append(CDBTreeItemWithCode(group, name, code, id, self))
        return result


    def loadChildrenItems(self, group):
        recordList = self._records[group._id] if self._records.has_key(group._id) else []
        alfNumKey_sort(recordList, lambda s: forceString(s.value('code')))
        return self.getItemListByRecords(recordList, group)


    def reset(self):
        self.__preload()
        CDragDropDBTreeModel.reset(self)


    def update(self):
        self.__preload()
        CDragDropDBTreeModel.update(self)



class CFilterModel(CSortFilterProxyTreeModel):
    def __init__(self, parent, sourceModel):
        CSortFilterProxyTreeModel.__init__(self, parent, sourceModel)
        self.filterName = ''
        self.filterCode = ''


    def acceptItem(self, item):
        result = True
        if self.filterName:
            result = result and (item.name().upper().find(self.filterName.upper()) != -1)
        if self.filterCode:
            result = result and item.code().upper().startswith(self.filterCode.upper())
        return result


    def hasFilters(self):
        return bool(self.filterName) or bool(self.filterCode)



class CRBThesaurus(CHierarchicalItemsListDialog):
    mimeTypeThesaurusItems = 'application/x-s11/thesaurusItems'
    mimeTypeItemIdList     = 'application/x-s11/itemIdList'


    def __init__(self, parent):
        CHierarchicalItemsListDialog.__init__(self, parent, [
            CTextCol(   u'Код',          ['code'], 20),
            CTextCol(   u'Наименование', ['name'],   40),
            ], 'rbThesaurus', ['code', 'name', 'id'], filterClass=CRBThesaurusFilterDialog)
        self.setWindowTitleEx(u'Тезаурус')
        self.treeItems.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
        self.connect(self.modelTree, SIGNAL('saveExpandedState()'),  self.saveExpandedState)
        self.connect(self.modelTree, SIGNAL('restoreExpandedState()'),  self.restoreExpandedState)
        self.tblItems.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tblItems.setSortingEnabled(True)
        self.tblItems.horizontalHeader().sectionClicked.connect(self.setSort)
        self.headerSortIndicator = None
        self.setSort(0)


    def preSetupUi(self):
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.addModels('Tree', CFilterModel(self, CPreloadDragDropDBTreeModel(self, self.tableName, 'id', 'group_id', 'name', 'code', self.order)))
        self.addModels('Table', CTableModel(self, self.cols, self.tableName))

        self.modelTree.sourceModel().setLeavesVisible(True)
        self.modelTree.sourceModel().setOrder('code')
        self.addObject('actSelectAll',      QtGui.QAction(u'Выделить все строки', self))
        self.addObject('actClearSelection', QtGui.QAction(u'Снять выделение',     self))
        self.addObject('actDelete',         QtGui.QAction(u'Удалить выделенные строки', self))
        self.addObject('actDuplicate',      QtGui.QAction(u'Дублировать', self))
        self.addObject('actCopy',           QtGui.QAction(u'Копировать', self))
        self.addObject('actCut',           QtGui.QAction(u'Вырезать', self))
        self.addObject('actPaste',          QtGui.QAction(u'Вставить', self))
        self.actSelectAll.setShortcut(QtGui.QKeySequence.SelectAll)


    def postSetupUi(self):
        CHierarchicalItemsListDialog.postSetupUi(self)
        self.tblItems.createPopupMenu([self.actSelectAll,
                                       self.actClearSelection,
                                       self.actDelete,
                                       self.actDuplicate,
                                       '-',
                                       self.actCopy,
                                       self.actCut,
                                       self.actPaste,
                                       ]
                                     )
        self.connect(self.tblItems.popupMenu(), SIGNAL('aboutToShow()'), self.popupMenuAboutToShow)


    def getItemEditor(self):
        editor = CThesaurusItemEditor(self)
        editor.setGroupId(self.currentGroupId())
        return editor


    def popupMenuAboutToShow(self):
        currentItemId = self.currentItemId()
        selectedIdList = self.tblItems.selectedItemIdList()
        mimeData = QtGui.qApp.clipboard().mimeData()

        self.actDuplicate.setEnabled(bool(currentItemId))
        self.actDelete.setEnabled(bool(selectedIdList)
                                  and not any(self.itemIsUsed(itemId) for itemId in selectedIdList)
                                 )
        self.actCopy.setEnabled(bool(selectedIdList))
        self.actCut.setEnabled(bool(selectedIdList)
                                  and not any(self.itemIsUsed(itemId) for itemId in selectedIdList)
                                 )
        self.actPaste.setEnabled(mimeData.hasFormat(self.mimeTypeThesaurusItems))


    def itemIsUsed(self, itemId):
        db = QtGui.qApp.db
        if db.translate('rbThesaurus', 'group_id', itemId, 'id'):
            return True
        return False


    def __getItemsForClipboard(self, itemIdList):
        result = []
        for itemId in itemIdList:
            result.append(self.__getItemForClipboard(itemId))
        return result


    def __getItemForClipboard(self, itemId):
        db = QtGui.qApp.db
        table = db.table('rbThesaurus')
        record = db.getRecord(table, '*', itemId)
        result = { 'code':     forceString(record.value('code')),
                   'name':     forceString(record.value('name')),
                   'template': forceString(record.value('template')),
                 }
        del record
        itemIdList = db.getIdList(table, 'id', table['group_id'].eq(itemId), order='code')
        if itemIdList:
            result['items'] = self.__getItemsForClipboard(itemIdList)
        return result


    def __pasteItems(self, items, groupId):
        result = []
        for item in items:
            result.append(self.__pasteItem(item, groupId))
        return result


    def __pasteItem(self, item, groupId):
        db = QtGui.qApp.db
        table = db.table('rbThesaurus')
        record = table.newRecord()
        record.setValue('group_id', groupId)
        record.setValue('code',     item['code'])
        record.setValue('name',     item['name'])
        record.setValue('template', item['template'])
        newItemId = db.insertRecord(table, record)
        items = item.get('items', None)
        if items:
            self.__pasteItems(items, newItemId)
        return newItemId


    def select(self, props, withValues = False):
        table = self.modelTable.table()
        groupId = self.currentGroupId()
        code = props.get('code')
        name = props.get('name')

        cond = [ table['group_id'].eq(groupId) ]
        if code:
            cond.append(table['code'].like('%s%%' % code))
            self.modelTree.filterCode = code
        else:
            self.modelTree.filterCode = ''

        if name:
            cond.append(table['name'].contain(name))
            self.modelTree.filterName = name
        else:
            self.modelTree.filterName = ''

        self.modelTree.invalidateFilter()
        recordList = QtGui.qApp.db.getRecordList(table.name(), 'id, code, name', cond, self.order)
        if withValues:
            return recordList
        else:
            alfNumKey_sort(recordList, lambda s: forceString(s.value('code')), False)
            idList = []
            for record in recordList:
                idList.append(forceInt(record.value('id')))
        return idList
    
    
    def setSort(self, col):
        model = self.tblItems.model()
        header = self.tblItems.horizontalHeader()
        header.setSortIndicatorShown(True)
        if self.headerSortIndicator == Qt.DescendingOrder:
            self.headerSortIndicator = Qt.AscendingOrder
        else:
            self.headerSortIndicator = Qt.DescendingOrder
        header.setSortIndicator(col, self.headerSortIndicator)
        items = self.select(self.props, True)
        if col == 0:
            alfNumKey_sort(items, lambda s: forceString(s.value('code')), reverse = self.headerSortIndicator == Qt.AscendingOrder)
        else:
            items.sort(key = lambda s: forceString(s.value('name')).lower(), reverse = self.headerSortIndicator == Qt.DescendingOrder)
        idList = []
        for record in items:
            idList.append(forceInt(record.value('id')))
        model.setIdList(idList)
        model.reset()


    @pyqtSignature('')
    def on_actSelectAll_triggered(self):
        self.tblItems.selectAll()
        self.popupMenuAboutToShow()


    @pyqtSignature('')
    def on_actClearSelection_triggered(self):
        self.tblItems.clearSelection()
        self.popupMenuAboutToShow()


    @pyqtSignature('')
    def on_actDelete_triggered(self):
        QtGui.qApp.setWaitCursor()
        try:
            rows = self.tblItems.selectedRowList()
            currentRow = self.tblItems.currentIndex().row()
            currentRow -= sum( row<currentRow for row in rows)
            itemIdList = self.tblItems.selectedItemIdList()
            db = QtGui.qApp.db
            table = db.table('rbThesaurus')
            db.deleteRecord(table, table['id'].inlist(itemIdList))
            self.renewListAndSetTo()
            self.tblItems.setCurrentRow(currentRow)
        finally:
            QtGui.qApp.restoreOverrideCursor()


    @pyqtSignature('')
    def on_actDuplicate_triggered(self):
        QtGui.qApp.setWaitCursor()
        try:
            itemIdList = self.tblItems.selectedItemIdList()
            items = self.__getItemsForClipboard(itemIdList)
            itemIdList = self.__pasteItems(items, self.currentGroupId())
            self.renewListAndSetTo(itemIdList[-1] if itemIdList else None)
        finally:
            QtGui.qApp.restoreOverrideCursor()


    @pyqtSignature('')
    def on_actCopy_triggered(self):
        QtGui.qApp.setWaitCursor()
        try:
            itemIdList = self.tblItems.selectedItemIdList()
            items = self.__getItemsForClipboard(itemIdList)
            bytes = QByteArray(json.dumps(items))
            mimeData = QMimeData()
            mimeData.setData(self.mimeTypeThesaurusItems, bytes)
            QtGui.qApp.clipboard().setMimeData(mimeData)
        finally:
            QtGui.qApp.restoreOverrideCursor()
    
    
    @pyqtSignature('')
    def on_actCut_triggered(self):
        QtGui.qApp.setWaitCursor()
        try:
            itemIdList = self.tblItems.selectedItemIdList()
            items = self.__getItemsForClipboard(itemIdList)
            bytes = QByteArray(json.dumps(items))
            mimeData = QMimeData()
            mimeData.setData(self.mimeTypeThesaurusItems, bytes)
            QtGui.qApp.clipboard().setMimeData(mimeData)
            
            rows = self.tblItems.selectedRowList()
            currentRow = self.tblItems.currentIndex().row()
            currentRow -= sum( row<currentRow for row in rows)
            db = QtGui.qApp.db
            table = db.table('rbThesaurus')
            db.deleteRecord(table, table['id'].inlist(itemIdList))
            self.renewListAndSetTo()
            self.tblItems.setCurrentRow(currentRow)
        finally:
            QtGui.qApp.restoreOverrideCursor()


    @pyqtSignature('')
    def on_actPaste_triggered(self):
        QtGui.qApp.setWaitCursor()
        try:
            mimeData = QtGui.qApp.clipboard().mimeData()
            if mimeData.hasFormat(self.mimeTypeThesaurusItems):
                bytes = mimeData.data(self.mimeTypeThesaurusItems)
                items = json.loads(str(bytes))
                itemIdList = self.__pasteItems(items, self.currentGroupId())
            self.renewListAndSetTo(itemIdList[-1] if itemIdList else None)
        finally:
            QtGui.qApp.restoreOverrideCursor()

#
# ##########################################################################
#

class CRBThesaurusFilterDialog(CDialogBase, Ui_RBThesaurusFilterDialog):
    def __init__(self, parent=None):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.setWindowTitleEx(u'Параметры фильтрации')
        self.buttonBox.button(QtGui.QDialogButtonBox.Reset).clicked.connect(self.resetFilters)


    def setProps(self, prop):
        self.edtCode.setText(prop.get('code', ''))
        self.edtName.setText(prop.get('name', ''))


    def props(self):
        result = {}
        result['code'] = unicode(self.edtCode.text())
        result['name'] = unicode(self.edtName.text())
        return result


    def resetFilters(self):
        self.edtCode.setText('')
        self.edtName.setText('')

#
# ##########################################################################
#

class CThesaurusItemEditor(CItemEditorBaseDialog, Ui_ThesaurusItemEditorDialog):
    def __init__(self,  parent):
        CItemEditorBaseDialog.__init__(self, parent, 'rbThesaurus')
        self.setupUi(self)
        self.setWindowTitleEx(u'Жалоба')
        self.setupDirtyCather()
        self.groupId = None
        self.prevName = self.edtName.text()
        self.edtTemplate.setText(self.autoTemplate(self.prevName))


    def setGroupId(self, id):
        self.groupId = id


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        setLineEditValue(   self.edtCode,           record, 'code')
        setLineEditValue(   self.edtName,           record, 'name')
        setLineEditValue(   self.edtTemplate,       record, 'template')
        self.groupId = forceRef(record.value('group_id'))
#        record.setValue('group_id', toVariant(self.groupId))

#        setRBComboBoxValue( self.cmbGroup,          record, 'group_id')
#        setComboBoxValue(   self.cmbSex,            record, 'sex')
#        (begUnit, begCount, endUnit, endCount) = parseAgeSelector(forceString(record.value('age')))
#        self.cmbBegAgeUnit.setCurrentIndex(begUnit)
#        self.edtBegAgeCount.setText(str(begCount))
#        self.cmbEndAgeUnit.setCurrentIndex(endUnit)
#        self.edtEndAgeCount.setText(str(endCount))

        self.prevName = self.edtName.text()
        self.setIsDirty(False)


    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        getLineEditValue( self.edtCode,     record, 'code')
        getLineEditValue( self.edtName,     record, 'name')
        getLineEditValue( self.edtTemplate, record, 'template')
        record.setValue('group_id', toVariant(self.groupId))
#        getRBComboBoxValue( self.cmbGroup,          record, 'group_id')
#        getComboBoxValue(   self.cmbSex,            record, 'sex')
#        record.setValue('age',        toVariant(composeAgeSelector(
#                    self.cmbBegAgeUnit.currentIndex(),  forceStringEx(self.edtBegAgeCount.text()),
#                    self.cmbEndAgeUnit.currentIndex(),  forceStringEx(self.edtEndAgeCount.text())
#                        )))
        return record


    def checkDataEntered(self):
        result = CItemEditorBaseDialog.checkDataEntered(self)
#        result = result and (self.checkRecursion(self.cmbGroup.value()) or self.checkValueMessage(u'попытка создания циклической группировки', False, self.cmbGroup))
#        result = result and (self.cmbPurpose.value() or self.checkInputMessage(u'назначение', False, self.cmbPurpose))
        return result


    def autoTemplate(self, name):
        return '%s: '+name


    @pyqtSignature('QString')
    def on_edtName_textEdited(self, text):
        if self.autoTemplate(self.prevName) == self.edtTemplate.text():
            self.edtTemplate.setText(self.autoTemplate(text))
            self.prevName = self.edtName.text()


def alfNumKey_sort(result, key=lambda s:s, reverse=False):
    def getNumKeyFunc(key):
        convert = lambda text: int(text) if text.isdigit() else text
        return lambda s: [convert(c) for c in re.split('([0-9]+)', unicode(key(s)) if isinstance(key(s), (QString, str)) else key(s))] if isinstance(key(s), (QString, str, unicode)) else key(s)
    sort_key = getNumKeyFunc(key)
    result.sort(key=sort_key, reverse=reverse)