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

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, pyqtSignature, SIGNAL, QObject, QVariant

from Reports.ReportView import CReportViewDialog
from library.DialogBase import CDialogBase
from library.SortFilterProxyTableModel import CSortFilterProxyTableModel
from library.TableModel import CTableModel
from library.RecordLock import CRecordLockMixin
from library.Utils      import exceptionToUnicode, forceRef, forceString, forceStringEx, toVariant
from library.database import CDatabaseException, CDocumentTable, CSqlRecord

from Ui_ItemsListDialog import Ui_ItemsListDialog
from Ui_ItemsSplitListDialog import Ui_ItemsSplitListDialog
from Ui_ItemEditorDialog import Ui_ItemEditorDialog


class CItemsListDialog(CDialogBase, Ui_ItemsListDialog):
    idFieldName = 'id'

    def __init__(self, parent, cols, tableName, order, forSelect=False, filterClass=None, multiSelect=False):
        u"""
        order - column to sort by
        forSelect = True - records from query
        forSelect = False - recods from table
        filterClass - class for filter dialog
        """
        CDialogBase.__init__(self, parent)
        self.preSetupUi()
        self.setupUi(self)
        self.postSetupUi()
        self.setup(cols, tableName, order, forSelect, filterClass)
        if multiSelect:
            self.tblItems.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.isAscending = False


    def preSetupUi(self):
        self.addObject('btnPrint',  QtGui.QPushButton(u'Печать F6', self))
        self.addObject('btnNew',  QtGui.QPushButton(u'Вставка F9', self))
        self.addObject('btnEdit',  QtGui.QPushButton(u'Правка F4', self))
        self.addObject('btnFilter',  QtGui.QPushButton(u'Фильтр', self))
        self.addObject('btnSelect',  QtGui.QPushButton(u'Выбор', self))


    def postSetupUi(self):
        self.buttonBox.addButton(self.btnSelect, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnFilter, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnEdit, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnNew, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnPrint, QtGui.QDialogButtonBox.ActionRole)


    def setup(self, cols, tableName, order, forSelect=False, filterClass=None):
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
##        self.setWindowFlags(Qt.Dialog | Qt.WindowMaximizeButtonHint | Qt.WindowContextHelpButtonHint)
        self.forSelect = forSelect
        self.filterClass = filterClass
        self.props = {}
        self.order = order
        self.addModels('', CTableModel(self, cols))
        self.model.idFieldName = self.idFieldName
        self.model.setTable(tableName, recordCacheCapacity=QtGui.qApp.db.getCount(tableName, 'id'))
        self.setModels(self.tblItems, self.model, self.selectionModel)
#        self.createPopupMenu(self.tblItems)
        self.btnSelect.setEnabled(self.forSelect)
        self.btnSelect.setVisible(self.forSelect)
        self.btnSelect.setDefault(self.forSelect)
        self.btnFilter.setEnabled(self.forSelect and bool(self.filterClass))
        self.btnFilter.setEnabled(bool(self.filterClass))
        self.btnFilter.setVisible(bool(self.filterClass))
        self.btnEdit.setDefault(not self.forSelect)
        self.tblItems.setFocus(Qt.OtherFocusReason)

        self.btnNew.setShortcut('F9')
        self.btnEdit.setShortcut('F4')
        self.btnPrint.setShortcut('F6')
        QObject.connect(
            self.tblItems.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.setSort)


    def exec_(self):
        idList = self.select(self.props)
        self.model.setIdList(idList)
        if idList:
            itemId = self.props.get('itemId', None)
            if itemId:
                self.tblItems.setCurrentItemId(itemId)
            else:
                self.tblItems.selectRow(0)
        self.label.setText(u'всего: %d' % len(idList))
        return CDialogBase.exec_(self)


    def generateFilterByProps(self, props):
        cond = []
        table = self.model.table()
#        for key, value in props.iteritems():
#            if table.hasField(key):
#                cond.append(table['key'].eq(value))
        if hasattr(self, 'chkOnlyActive') and self.chkOnlyActive.isChecked():  # Только активные типы события (Для Справочники/Учет/Типы событий)
            if table.hasField('isActive'):
                cond.append(table['isActive'].eq(1))
        if table.hasField('deleted'):
            cond.append(table['deleted'].eq(0))
        return cond


    def select(self, props={}):
        db = QtGui.qApp.db
        table = self.model.table()
        return db.getIdList(table,
                            self.idFieldName,
                            self.generateFilterByProps(props),
                            self.order)


    def selectItem(self):
#        if self.filterClass is not None: etc.
        return self.exec_()


    def setCurrentItemId(self, itemId):
        self.tblItems.setCurrentItemId(itemId)


    def currentItemId(self):
        return self.tblItems.currentItemId()


    def currentData(self, col):
        row = self.tblItems.currentRow()
        index = self.model.createIndex(row, col)
        return self.model.data(index)


    def renewListAndSetTo(self, itemId=None):
        idList = self.select(self.props)
        self.tblItems.setIdList(idList, itemId)
        self.label.setText(u'всего: %d' % len(idList))


    def copyDependedTableData(self, tableName, refFieldName, newItemId, oldItemId):
        db = QtGui.qApp.db
        table = db.table(tableName)
        records = db.getRecordList(table, '*', table[refFieldName].eq(oldItemId))
        for record in records:
            record.setNull('id')
            record.setValue(refFieldName, toVariant(newItemId))
            db.insertRecord(table, record)


    def copyInternals(self, newItemId, oldItemId):
        pass


    def duplicateRecord(self, itemId):
        def duplicateRecordInternal():
            db = QtGui.qApp.db
            record = db.getRecord(self.model.table(), '*', itemId)
            code = forceString(record.value('code'))
            name = forceString(record.value('name'))

            record.setNull('id') # чтобы не дублировался id
            record.setValue('code', code + '*')
            record.setValue('name', name + u'(копия)')
            db.transaction()
            try:
                newItemId = db.insertRecord(self.model.table(), record)
                self.copyInternals(newItemId, itemId)
                db.commit()
                return newItemId
            except:
                db.rollback()
                raise
        ok, result = QtGui.qApp.call(self, duplicateRecordInternal)
        return result


    def duplicateCurrentRow(self):
        itemId = self.tblItems.currentItemId()
        newItemId = self.duplicateRecord(itemId)
        self.renewListAndSetTo(newItemId)


    def markCurrentRowDeleted(self):
        db = QtGui.qApp.db
        table = self.model.table()
        itemId = self.tblItems.currentItemId()
        db.markRecordsDeleted(table, table['id'].eq(itemId))
        self.model.setIdList(self.select())


    @pyqtSignature('')
    def on_chkOnlyActive_clicked(self):  # показывать все/только активные (Для Справочники/Учет/Типы событий)
        itemId = self.tblItems.currentItemId()
        self.renewListAndSetTo(itemId)

    @pyqtSignature('QModelIndex')
    def on_tblItems_doubleClicked(self, index):
        if self.forSelect:
            self.on_btnSelect_clicked()
        else:
            self.on_btnEdit_clicked()


    @pyqtSignature('')
    def on_btnFilter_clicked(self):
        if self.filterClass:
            dialog = self.filterClass(self)
            try:
                dialog.setProps(self.props)
                if dialog.exec_():
                    self.props = dialog.props()
                    self.renewListAndSetTo(None)
            finally:
                dialog.deleteLater()


    @pyqtSignature('')
    def on_btnSelect_clicked(self):
        self.accept()


    @pyqtSignature('')
    def on_btnNew_clicked(self):
        dialog = self.getItemEditor()
        try:
            if dialog.exec_():
                itemId = dialog.itemId()
                self.renewListAndSetTo(itemId)
        finally:
            dialog.deleteLater()


    @pyqtSignature('')
    def on_btnEdit_clicked(self):
        itemId = self.currentItemId()
        if itemId:
            dialog = self.getItemEditor()
            try:
                dialog.load(itemId)
                if dialog.exec_():
                    itemId = dialog.itemId()
                    self.renewListAndSetTo(itemId)
            finally:
                dialog.deleteLater()
        else:
            self.on_btnNew_clicked()


    def getReportHeader(self):
        return self.objectName()


    def getFilterAsText(self):
        return u''


    def contentToHTML(self):
        reportHeader=self.getReportHeader()
        self.tblItems.setReportHeader(reportHeader)
        reportDescription=self.getFilterAsText()
        self.tblItems.setReportDescription(reportDescription)
        return self.tblItems.contentToHTML()

    def GroupContentToHTML(self):
        self.tblItemGroups.setReportHeader('')
        reportDescription=self.getFilterAsText()
        self.tblItemGroups.setReportDescription(reportDescription)
        return self.tblItemGroups.contentToHTML()

    @pyqtSignature('')
    def on_btnPrint_clicked(self):
        html = self.contentToHTML()
        view = CReportViewDialog(self)
        view.setText(html)
        view.exec_()


    def setSort(self, col):
        name=self.model.cols()[col].fields()[0]
        self.order = name
        header=self.tblItems.horizontalHeader()
        header.setSortIndicatorShown(True)
        self.isAscending = not self.isAscending
        header.setSortIndicator(col, Qt.AscendingOrder if self.isAscending else Qt.DescendingOrder)
        if self.isAscending:
            self.order = self.order + u' ASC'
        else:
            self.order = self.order + u' DESC'
        self.renewListAndSetTo(self.currentItemId())

#
# #######################################################################
#


class CItemsSplitListDialog(Ui_ItemsSplitListDialog, CItemsListDialog):
    # Окно со сплиттером для элементов, связанных направленными соответствиями (не обязательно иерархическими)
    # Вверху - список элементов, внизу - соответствия каждого элемента
    def __init__(self, parent, tableName, cols, order, subTableName, subCols, mainColName, linkColName, forSelect=False, filterClass=None):
        CItemsListDialog.__init__(self, parent, cols, tableName, order, forSelect, filterClass)
        self.setupSubTable(subTableName, subCols, mainColName, linkColName)
#        QObject.connect(self.tblItems, SIGNAL('doubleClicked(QModelIndex)'), self.on_btnEdit_clicked)
        QObject.connect(self.tblItemGroups, SIGNAL('doubleClicked(QModelIndex)'), self.on_tblItemGroups_doubleClicked)


    def setupSubTable(self, subTableName, subCols, mainColName, linkColName):
        self.subModel = CTableModel(self, subCols)
        self.subModel.idFieldName = 'id'
        self.isAscendingSub = False
        self.subOrder = ''
        self.subModel.setTable(subTableName)
        self.mainColName = mainColName
        self.linkColName = linkColName
        self.updateSubTable()
        QObject.connect(self.tblItems.selectionModel(), SIGNAL('currentRowChanged(QModelIndex, QModelIndex)'), self.updateSubTable)
        QObject.connect(
            self.tblItemGroups.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.setSubSort)


    def renewSubListAndSetTo(self, itemId=None):
        idList = self.updateSubTable()
        self.tblItemGroups.setIdList(idList, itemId)


    def setSubSort(self, col):
        name=self.subModel.cols()[col].fields()[0]
        self.subOrder = name
        header=self.tblItemGroups.horizontalHeader()
        header.setSortIndicatorShown(True)
        self.isAscendingSub = not self.isAscendingSub
        header.setSortIndicator(col, Qt.AscendingOrder if self.isAscendingSub else Qt.DescendingOrder)
        if self.isAscendingSub:
            self.subOrder = self.subOrder + u' ASC'
        else:
            self.subOrder = self.subOrder + u' DESC'
        self.renewSubListAndSetTo(self.tblItemGroups.currentItemId())


    def updateSubTable(self):
        idList = []
        current = self.tblItems.currentItemId()
        if current:
            idList = QtGui.qApp.db.getIdList(table=self.subModel.table(), where='%s = %d'%(self.mainColName, current), order=self.subOrder)
            self.subModel.setIdList(idList)
            self.tblItemGroups.setModel(self.subModel)
            if len(idList):
                self.tblItemGroups.selectRow(0)
        return idList


    def on_tblItemGroups_doubleClicked(self, index):
        id = self.tblItemGroups.itemId(index)
        record = QtGui.qApp.db.getRecord(self.subModel.table(), self.linkColName, id)
        main_id = forceRef(record.value(self.linkColName))
        self.tblItems.setCurrentItemId(main_id)


#
# #######################################################################
#

class CItemsListDialogEx(CItemsListDialog):
    u"""Справочник с возможностью выделения, дублирования и удаления строчек
    и контроля уникальности кода"""
    def __init__(self, parent, cols, tableName, order, forSelect=False, filterClass=None, multiSelect=True, uniqueCode=False):
        CItemsListDialog.__init__(self, parent, cols, tableName, order, forSelect, filterClass)
        self.uniqueCode = uniqueCode
        if multiSelect:
            self.tblItems.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
            self.setPopupMenu()


    def addPopupAction(self, name, title, method):
        setattr(self, name, QtGui.QAction(title, self))
        self.tblItems.addPopupAction(getattr(self, name))
        self.connect(getattr(self, name), SIGNAL('triggered()'), method)


    def setPopupMenu(self):
        self.addPopupAction('actSelectAllRow', u'Выделить все строки', self.selectAllRowTblItem)
        self.addPopupAction('actClearSelectionRow', u'Снять выделение', self.clearSelectionRow)
        self.addPopupAction('actDelSelectedRows', u'Удалить выделенные строки', self.delSelectedRows)
        self.addPopupAction('actDuplicate', u'Дублировать', self.duplicateCurrentRow)


#    def select(self, props={}):
#        table = self.model.table()
#        return QtGui.qApp.db.getIdList(table.name(),
#                           'id',
#                           table['deleted'].eq(0),
#                           self.order)


#    def duplicateCurrentRow(self):
#        itemId = self.tblItems.currentItemId()
#        record = self.model.getRecordById(itemId)
#        code = forceString(record.value('code'))
#        name = forceString(record.value('name'))
#        if self.uniqueCode:
#            record.setValue('code', code + '*') # чтобы не дублировался код
#        record.setValue('name', name + '(копия)')
#        record.setValue('id', QVariant()) # чтобы не дублировался id
#        QtGui.qApp.db.insertRecord(self.model.table(), record)
#        self.model.setIdList(self.select())
#        self.tblItems.setCurrentItemId(itemId)


    def selectAllRowTblItem(self):
        self.tblItems.selectAll()


    def clearSelectionRow(self):
        self.tblItems.clearSelection()


    def delSelectedRows(self):
        selectedRowList = self.tblItems.selectedRowList()
        if QtGui.QMessageBox.question(self, u'Подтверждение удаления',
                                    u'Вы уверены что хотите удалить выделенные строки?(количество строк: %d)'% len(selectedRowList),
                                    QtGui.QMessageBox.Yes|QtGui.QMessageBox.No,
                                    QtGui.QMessageBox.No
                                    ) == QtGui.QMessageBox.Yes:
            for row in selectedRowList[::-1]: # удаляем в обратном порядке, чтобы избежать сдвигов
                try:
                    self.model.removeRow(row)
                except CDatabaseException as e:
                    dbText = e.sqlError.databaseText()
                    message = u'Невозможно удалить строки, ошибка бд: %s'%dbText
                    if e.sqlError.type() == 2 and 'foreign key constraint fails' in dbText:
                        message = u'Невозможно удалить строки, данные используются'
                    QtGui.QMessageBox.critical(self, u'Внимание!', message)
        self.model.setIdList(self.select())


#
# ##########################################################################
#

class CItemsListDialogWithProxy(CItemsListDialog):
    u'CItemsListDialog, у которого для tblItems используется прокси-модель'
    def __init__(self, *args, **kwargs):
        CItemsListDialog.__init__(self, *args, **kwargs)

    def setup(self, cols, tableName, order, forSelect=False, filterClass=None):
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.forSelect = forSelect
        self.filterClass = filterClass
        self.props = {}
        self.order = order
        self.addModels('', CTableModel(self, cols))
        self.model.idFieldName = self.idFieldName
        self.model.setTable(tableName, recordCacheCapacity=QtGui.qApp.db.getCount(tableName, 'id'))
        self.proxyModel = CSortFilterProxyTableModel(self, self.model)
        self.tblItems.setModel(self.proxyModel)
        self.btnSelect.setEnabled(self.forSelect)
        self.btnSelect.setVisible(self.forSelect)
        self.btnSelect.setDefault(self.forSelect)
        self.btnFilter.setEnabled(self.forSelect and bool(self.filterClass))
        self.btnFilter.setEnabled(bool(self.filterClass))
        self.btnFilter.setVisible(bool(self.filterClass))
        self.btnEdit.setDefault(not self.forSelect)
        self.tblItems.setFocus(Qt.OtherFocusReason)

        self.btnNew.setShortcut('F9')
        self.btnEdit.setShortcut('F4')
        self.btnPrint.setShortcut('F6')
        self.tblItems.setSortingEnabled(True)

    def renewListAndSetTo(self, itemId=None):
        idList = self.select(self.props)
        self.tblItems.setIdList(idList, itemId)
        self.proxyModel.reset()
        self.label.setText(u'всего: %d' % len(idList))

    def exec_(self):
        idList = self.select(self.props)
        self.model.setIdList(idList)
        if idList:
            self.tblItems.selectRow(0)
        self.label.setText(u'всего: %d' % len(idList))
        return CDialogBase.exec_(self)

    def setCurrentItemId(self, itemId):
        row = self.model().findItemIdIndex(itemId)
        proxyIndex = self.proxyModel.index(row, 0)
        sourceIndex = self.proxyModel.mapToSource(proxyIndex)
        self.tblItems.setCurrentIndex(sourceIndex)

    def currentItemId(self):
        index = self.currentIndex()
        return self.tblItems.itemId(index)

    def currentIndex(self):
        proxyIndex = self.tblItems.currentIndex()
        sourceIndex = self.proxyModel.mapToSource(proxyIndex)
        return sourceIndex

    def currentData(self, col):
        index = self.currentIndex()
        return self.model.data(index)

#
# ##########################################################################
#
class CItemsSplitListDialogEx(CItemsSplitListDialog):
    # поскольку виртуальное наследование не поддерживается,
    # наследуем от одного класса, а методы второго просто копируем
    def __init__(self, parent, tableName, cols, order, subTableName, subCols, mainColName, linkColName, forSelect=False, filterClass=None, multiSelect=True, uniqueCode=False):
        CItemsSplitListDialog.__init__(self, parent, tableName, cols, order, subTableName, subCols, mainColName, linkColName, forSelect, filterClass)
        self.uniqueCode = uniqueCode
        if multiSelect:
            self.tblItems.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
            self.tblItemGroups.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
            self.setPopupMenu()

#    addPopupAction = CItemsListDialogEx.addPopupAction
#    setPopupMenu = CItemsListDialogEx.setPopupMenu
#    select = CItemsListDialogEx.select
#    duplicateCurrentRow = CItemsListDialogEx.duplicateCurrentRow
#    selectAllRowTblItem = CItemsListDialogEx.selectAllRowTblItem
#    clearSelectionRow = CItemsListDialogEx.clearSelectionRow
#    delSelectedRows = CItemsListDialogEx.delSelectedRows
    def addPopupAction(self, name, title, method):
        setattr(self, name, QtGui.QAction(title, self))
        self.tblItems.addPopupAction(getattr(self, name))
        self.connect(getattr(self, name), SIGNAL('triggered()'), method)


    def setPopupMenu(self):
        self.addPopupAction('actSelectAllRow', u'Выделить все строки', self.selectAllRowTblItem)
        self.addPopupAction('actClearSelectionRow', u'Снять выделение', self.clearSelectionRow)
        self.addPopupAction('actDelSelectedRows', u'Удалить выделенные строки', self.delSelectedRows)
        self.addPopupAction('actDuplicate', u'Дублировать', self.duplicateCurrentRow)


    def select(self, props={}):
        table = self.model.table()
        return QtGui.qApp.db.getIdList(table.name(),
                           'id',
                           table['deleted'].eq(0),
                           self.order)


#    def duplicateCurrentRow(self):
#        record = self.model.getRecordById(self.tblItems.currentItemId())
#        code = forceString(record.value('code'))
#        if self.uniqueCode:
#            record.setValue('code', toVariant(code + '*')) # чтобы не дублировался код
#        record.setValue('id', toVariant(0)) # чтобы не дублировался id
#        QtGui.qApp.db.insertRecord(self.model.table(), record)
#        self.model.setIdList(self.select({}))


    def selectAllRowTblItem(self):
        self.tblItems.selectAll()


    def clearSelectionRow(self):
        self.tblItems.clearSelection()


    def delSelectedRows(self):
        selectedRowList = self.tblItems.selectedRowList()
        if QtGui.QMessageBox.question(self, u'Подтверждение удаления',
                                    u'Вы уверены что хотите удалить выделенные строки?(количество строк: %d)'% len(selectedRowList),
                                    QtGui.QMessageBox.Yes|QtGui.QMessageBox.No,
                                    QtGui.QMessageBox.No
                                    ) == QtGui.QMessageBox.Yes:
            for row in selectedRowList[::-1]: # удаляем в обратном порядке, чтобы избежать сдвигов
                try:
                    self.model.removeRow(row)
                except CDatabaseException:
                    pass
        self.model.setIdList(self.select({}))

#
# #######################################################################
#


class CItemEditorBaseDialog(CDialogBase, CRecordLockMixin):
    idFieldName = 'id'

    def __init__(self, parent, tableName):
        CDialogBase.__init__(self, parent)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        CRecordLockMixin.__init__(self)
        self._id = None
        self._tableName = tableName
        self._record = None
        self._isAssertNoMessage = False


    def setIsAssertNoMessage(self, value):
        self._isAssertNoMessage = value


    def exec_(self):
        if self.lock(self._tableName, self._id):
            try:
                if self._id and not self._record:
                    db = QtGui.qApp.db
                    record = db.getRecord(db.table(self._tableName), '*', self._id)
                    self.setRecord(record)
                    self.setIsDirty(False)
                    if not self.checkDataBeforeOpen():
                        return QtGui.QDialog.Rejected
                result = CDialogBase.exec_(self)
            finally:
                self.releaseLock()
        else:
            result = QtGui.QDialog.Rejected
            self.setResult(result)
        return result


    def checkDataBeforeOpen(self):
        return True


    def saveData(self):
        return self.checkDataEntered() and self.save()


    def load(self, id):
        self._id = id


    def setRecord(self, record):
        if type(record) != CSqlRecord:
            record = CSqlRecord(record)
        self._record = record
        self._id     = forceRef(record.value(self.idFieldName))


    def setGroupId(self, id):
        pass


    def record(self):
        return self._record


    def getRecord(self):
        if not self._record:
            db = QtGui.qApp.db
            record = db.record(self._tableName)
            if self._id:
                record.setValue(self.idFieldName, toVariant(self._id))
            self._record = record
        return self._record


    def tableName(self):
        return self._tableName


    def itemId(self):
        return self._id


    def setItemId(self, itemId):
        self._id = itemId
        if self._record:
            self._record.setValue(self.idFieldName, toVariant(self._id))


    def checkDataEntered(self):
        return True


    def checkRecursion(self, newGroupId, groupIdFieldName='group_id'):
        if self._id:
            groupId = newGroupId
            db = QtGui.qApp.db
            table = db.table(self._tableName)
            while groupId and self._id != groupId:
                groupId = forceRef(db.translate(table, self.idFieldName, groupId, groupIdFieldName))
            return not groupId
        else:
            return True


    def save(self):
        try:
            prevId = self.itemId()
            db = QtGui.qApp.db
            db.transaction()
            try:
                record = self.getRecord()
                table = db.table(self._tableName)
                id = db.insertOrUpdate(table, record)
                self.saveInternals(id)
                db.commit()
            except:
                db.rollback()
                self.setItemId(prevId)
                raise
            self.setItemId(id)

            # для обновления данных в модели при нажатии кнопки "применить"
            if isinstance(table, CDocumentTable):
                for fieldName in [CDocumentTable.dtfCreateDatetime, CDocumentTable.dtfCreateUserId,
                                  CDocumentTable.dtfModifyDatetime, CDocumentTable.dtfModifyUserId]:
                    self._record.setValue(fieldName, record.value(fieldName))
            self.afterSave()
            return id
        except Exception, e:
            if self._isAssertNoMessage:
                return None
            QtGui.qApp.logCurrentException()
            QtGui.QMessageBox.critical( self,
                                        u'',
                                        exceptionToUnicode(e),
                                        QtGui.QMessageBox.Close)
            return None


    def saveInternals(self, id):
        return


    def afterSave(self):
        self.setIsDirty(False)


# #######################################################################


class CItemEditorDialog(Ui_ItemEditorDialog, CItemEditorBaseDialog):
    doCheckCode = True
    doCheckName = True

    def __init__(self, parent, tableName):
        CItemEditorBaseDialog.__init__(self, parent, tableName)
        self.preSetupUi()
        self.setupUi(self)
        self.postSetupUi()

#        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)


    def preSetupUi(self):
        pass


    def postSetupUi(self):
        pass


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        self.edtCode.setText(forceString(record.value('code')))
        self.edtName.setText(forceString(record.value('name')))


    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        record.setValue('code',  toVariant(forceStringEx(self.edtCode.text())))
        record.setValue('name',  toVariant(forceStringEx(self.edtName.text())))
        return record


    @pyqtSignature('QString')
    def on_edtCode_textEdited(self, text):
        self.setIsDirty()


    @pyqtSignature('QString')
    def on_edtName_textEdited(self, text):
        self.setIsDirty()


    def checkDataEntered(self):
#        result = CItemEditorBaseDialog.checkDataEntered(self)
        result = True
        if self.doCheckCode:
            code   = forceStringEx(self.edtCode.text())
            result = result and (code or self.checkInputMessage(u'код', False, self.edtCode))
        if self.doCheckName:
            name   = forceStringEx(self.edtName.text())
            result = result and (name or self.checkInputMessage(u'наименование', False, self.edtName))
        return result


#
################################################################################
#

class CRBItemsSplitListDialogEx(CItemsSplitListDialogEx):

    def copyInternals(self, newItemId, oldItemId):
        db = QtGui.qApp.db
        if QtGui.QMessageBox.question( self,
                                       u'Внимание!',
                                       u'Копировать данные подчиненной таблицы?',
                                       QtGui.QMessageBox.Yes|QtGui.QMessageBox.No,
                                       QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
            subTable = self.subModel.table()
            secondaryRecords = db.getRecordList(subTable, '*', [subTable['master_id'].eq(oldItemId)])
            for secondaryRecord in secondaryRecords:
                secondaryRecord.setValue('id', QVariant())
                secondaryRecord.setValue('master_id', toVariant(newItemId))
                db.insertRecord(subTable, secondaryRecord)

#    def duplicateCurrentRow(self):
#        currentId = self.tblItems.currentItemId()
#        record = self.model.getRecordById(currentId)
#        code = forceString(record.value('code'))
#        if self.uniqueCode:
#            record.setValue('code', toVariant(code + '*')) # чтобы не дублировался код
#        record.setValue('id', toVariant(0)) # чтобы не дублировался id
#        db = QtGui.qApp.db
#        newId = db.insertRecord(self.model.table(), record)
#        if newId and QtGui.QMessageBox.question( self,
#                                       u'Внимание!',
#                                       u'Копировать данные подчиненной таблицы?',
#                                       QtGui.QMessageBox.Yes|QtGui.QMessageBox.No,
#                                       QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
#            subTable = self.subModel.table()
#            secondaryRecords = db.getRecordList(subTable, '*', [subTable['master_id'].eq(currentId)])
#            for secondaryRecord in secondaryRecords:
#                secondaryRecord.setValue('id', toVariant(0))
#                secondaryRecord.setValue('master_id', toVariant(newId))
#                db.insertRecord(subTable, secondaryRecord)
#        self.model.setIdList(self.select({}))


    def delSelectedRows(self):
        db = QtGui.qApp.db
        selectedRowList = self.tblItems.selectedRowList()
        #table = self.model.table()
        if QtGui.QMessageBox.question(self, u'Подтверждение удаления',
                                    u'Вы уверены что хотите удалить выделенные строки?(количество строк: %d)'% len(selectedRowList),
                                    QtGui.QMessageBox.Yes|QtGui.QMessageBox.No,
                                    QtGui.QMessageBox.No
                                    ) == QtGui.QMessageBox.Yes:
            for row in selectedRowList[::-1]: # удаляем в обратном порядке, чтобы избежать сдвигов
                try:
                    currentId = self.model._idList[row]
                    if currentId:
                        subTable = self.subModel.table()
                        secondaryIdList = db.getDistinctIdList(subTable, 'id', subTable['master_id'].eq(currentId))
                        for secondaryId in secondaryIdList:
                            db.deleteRecord(subTable, subTable['id'].eq(secondaryId))
                    self.model.removeRow(row)
                except CDatabaseException:
                    pass
        self.model.setIdList(self.select())
