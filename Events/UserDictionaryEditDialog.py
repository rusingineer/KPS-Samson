# -*- coding: utf-8 -*-

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, pyqtSignature, QVariant, QAbstractListModel, QModelIndex

from library.DialogBase import CConstructHelperMixin
from library.Utils import forceString, forceRef

from RefBooks.Person.List import getSamePersonIdList

from Ui_UserDictionaryEditDialog import Ui_UserDictionaryEditDialog


class CUserDictionaryEditDialog(QtGui.QDialog, CConstructHelperMixin, Ui_UserDictionaryEditDialog):
    def __init__(self, parent, propertyType):
        QtGui.QDialog.__init__(self, parent)
        self.addObject('mnuUserDictionary', QtGui.QMenu(self))
        self.addObject('actDeleteRow', QtGui.QAction(u'Удалить запись', self))
        self.setupUi(self)
        self.propertyType = propertyType
        self.setPropertyTypeName()
        self.addModels('UserDictionary', CUserDictionaryEditListModel(self, propertyType.id))
        self.setModels(self.lvUserDictionary, self.modelUserDictionary, self.selectionModelUserDictionary)
        self.mnuUserDictionary.addAction(self.actDeleteRow)
        self.lvUserDictionary.setItemDelegateForColumn(0, CPlainTextEditDelegate())
        self.dataModified = False
    
    def setPropertyTypeName(self):
        db = QtGui.qApp.db
        tableAPT = db.table('ActionPropertyType')
        tableAT = db.table('ActionType')
        query = tableAPT.leftJoin(tableAT, tableAT['id'].eq(tableAPT['actionType_id']))
        cols = [
            tableAT['name'].alias('atName'),
            tableAPT['name'].alias('aptName')
        ]
        record = db.getRecord(query, cols, self.propertyType.id)
        atName = forceString(record.value('atName'))
        aptName = forceString(record.value('aptName'))
        self.lblPropertyTypeName.setText(atName + ': ' + aptName)

    @pyqtSignature('QAbstractButton*')
    def on_buttonBox_clicked(self, button):
        buttonCode = self.buttonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Ok:
            self.modelUserDictionary.save()
            self.dataModified = True
            self.accept()
        elif buttonCode == QtGui.QDialogButtonBox.Apply:
            self.modelUserDictionary.save()
            self.dataModified = True
            self.modelUserDictionary.load()
        elif buttonCode == QtGui.QDialogButtonBox.Cancel:
            self.reject()
    
    @pyqtSignature('')
    def on_btnAddNewText_clicked(self):
        self.modelUserDictionary.insert(self.edtNewText.toPlainText())
        self.edtNewText.setPlainText('')
    
    @pyqtSignature('')
    def on_actDeleteRow_triggered(self):
        row = self.selectionModelUserDictionary.currentIndex().row()
        self.modelUserDictionary.delete(row)

    @pyqtSignature('QPoint')
    def on_lvUserDictionary_customContextMenuRequested(self, pos):
        index = self.selectionModelUserDictionary.currentIndex()
        self.actDeleteRow.setEnabled(index.isValid())
        self.mnuUserDictionary.exec_(self.lvUserDictionary.mapToGlobal(pos))


class CPlainTextEditDelegate(QtGui.QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        return QtGui.QPlainTextEdit(parent)
    
    def sizeHint(self, option, index):
        addHeight = option.fontMetrics.height() / 2
        size = QtGui.QStyledItemDelegate.sizeHint(self, option, index)
        size.setHeight(size.height() + addHeight)
        return size


class CUserDictionaryEditListModel(QAbstractListModel):
    def __init__(self, parent, actionPropertyTypeId):
        QAbstractListModel.__init__(self, parent)
        self.personId = QtGui.qApp.userId
        self.personIdList = getSamePersonIdList(self.personId)
        self.actionPropertyTypeId = actionPropertyTypeId
        self.load()

    def load(self):
        db = QtGui.qApp.db
        tableUserDictionary = db.table('UserDictionary')
        cond = [
            tableUserDictionary['person_id'].inlist(self.personIdList),
            tableUserDictionary['actionPropertyType_id'].eq(self.actionPropertyTypeId)
        ]
        self.records = db.getRecordList(tableUserDictionary, cols='id, text', where=cond, order='text')
        self.deletedIds = []
        self.modifiedRecords = set()
        self.reset()
    
    def save(self):
        db = QtGui.qApp.db
        tableUserDictionary = db.table('UserDictionary')
        if self.deletedIds:
            db.deleteRecord(tableUserDictionary, tableUserDictionary['id'].inlist(self.deletedIds))
        for record in self.modifiedRecords:
            db.insertOrUpdate(tableUserDictionary, record)
        self.load()
    
    def insert(self, text):
        db = QtGui.qApp.db
        tableUserDictionary = db.table('UserDictionary')
        record = tableUserDictionary.newRecord()
        record.setValue('person_id', self.personId)
        record.setValue('actionPropertyType_id', self.actionPropertyTypeId)
        record.setValue('text', text)
        row = len(self.records)
        self.beginInsertRows(QModelIndex(), row, row)
        self.records.append(record)
        self.modifiedRecords.add(record)
        self.insertRows(row, row)
        self.endInsertRows()
    
    def delete(self, row):
        record = self.records[row]
        id = forceRef(record.value('id'))
        if id:
            self.deletedIds.append(id)
        self.beginRemoveRows(QModelIndex(), row, row)
        self.modifiedRecords.discard(record)
        del self.records[row]
        self.removeRows(row, row)
        self.endRemoveRows()
    
    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
    
    def rowCount(self, parent):
        return len(self.records)

    def data(self, index, role=Qt.DisplayRole):
        if role in (Qt.DisplayRole, Qt.EditRole):
            row = index.row()
            record = self.records[row]
            return record.value('text')
        return QVariant()

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            row = index.row()
            record = self.records[row]
            record.setValue('text', value)
            self.modifiedRecords.add(record)
            self.dataChanged.emit(index, index)
            return True
        return False