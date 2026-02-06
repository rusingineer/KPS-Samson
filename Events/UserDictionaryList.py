# -*- coding: utf-8 -*-

from PyQt4 import QtGui

from PyQt4.QtCore import Qt, QVariant, pyqtSignature, QAbstractListModel

from library.Utils import forceString

from RefBooks.Person.List import getSamePersonIdList


class CUserDictionaryListModel(QAbstractListModel):
    def __init__(self, parent):
        self.records = []
        self.personIdList = getSamePersonIdList(QtGui.qApp.userId)
        QAbstractListModel.__init__(self, parent)
    
    def clear(self):
        self.records = []
        self.reset()
    
    def load(self, actionPropertyTypeId):
        db = QtGui.qApp.db
        tableUserDictionary = db.table('UserDictionary')
        cond = [
            tableUserDictionary['person_id'].inlist(self.personIdList),
            tableUserDictionary['actionPropertyType_id'].eq(actionPropertyTypeId)
        ]
        self.records = db.getRecordList(tableUserDictionary, cols='text', where=cond, order='text')
        self.reset()
    
    def rowCount(self, parent):
        return len(self.records)
    
    def data(self, index, role=Qt.DisplayRole):
        if role in (Qt.DisplayRole, Qt.EditRole):
            row = index.row()
            record = self.records[row]
            return record.value('text')
        return QVariant()


class CUserDictionaryListView(QtGui.QListView):
    def __init__(self, parent):
        QtGui.QListView.__init__(self, parent)
        self.sourceModel = CUserDictionaryListModel(self)
        self.sortFilterModel = QtGui.QSortFilterProxyModel()
        self.sortFilterModel.setSourceModel(self.sourceModel)
        self.sortFilterModel.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.setModel(self.sortFilterModel)
        self.clicked.connect(self.on_clicked)
    
    def load(self, propertyType):
        self.sourceModel.load(propertyType.id)
    
    def clear(self):
        self.sourceModel.clear()

    def propertyEditor(self):
        return self.focusProxy()

    def setPropertyEditor(self, editor):
        if self.propertyEditor():
            self.propertyEditor().setCompleter(None)
        self.setFocusProxy(editor)
        if editor:
            self.setStyleSheet("QListView::item:hover { background: #DCDEF1; }")
            self.setMouseTracking(True)
            completer = QtGui.QCompleter(self)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            completer.setModelSorting(QtGui.QCompleter.CaseInsensitivelySortedModel)
            completer.setModel(self.sourceModel)
            editor.setCompleter(completer)
        else:
            self.setStyleSheet("")
            self.setMouseTracking(False)
            self.setCursor(Qt.ArrowCursor)
    
    def supportsPropertyType(self, propertyType):
        return (propertyType.typeName == 'Text')
    
    def mouseMoveEvent(self, event):
        if self.propertyEditor():
            index = self.indexAt(event.pos())
            self.setCursor(Qt.PointingHandCursor if index.isValid() else Qt.ArrowCursor)
        QtGui.QListView.mouseMoveEvent(self, event)
    
    def setFilter(self, filterText):
        self.sortFilterModel.setFilterFixedString(filterText)

    @pyqtSignature('QModelIndex')
    def on_clicked(self, index):
        editor = self.propertyEditor()
        if editor:
            newText = forceString(self.model().data(index))
            cursor = editor.textCursor()
            cursor.insertText(newText)
            editor.setTextCursor(cursor)