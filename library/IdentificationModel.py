# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2016-2025 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QDateTime, QSize, QModelIndex, QVariant, SIGNAL, pyqtSignature, QEvent

from Orgs.PersonComboBox import CPersonComboBox
from library.InDocTable import CInDocTableModel, CRecordListModel, CDateInDocTableCol, CInDocTableCol
from library.TableModel import CTableModel, CTextCol, CCol
from library.TableView  import CTableView
from library.database   import decorateString, CTableRecordCache, checkViewURN
from library.Utils      import trim, forceRef, forceStringEx, forceBool, forceString, forceInt, toVariant, getPref, setPref
from library.crbcombobox import CRBComboBox
from library.Ui_IdentificationComboBoxExPopup import Ui_IdentificationComboBoxExPopup

__all__ = ( 'CIdentificationModel',
            'checkIdentification',
            'CAccountingSystemComboBox',
            'CAccountingSystemInDocTableColHybrid',
            # 'CAccountingSystemIdentification'
          )


class CIdentificationModel(CInDocTableModel):

    def __init__(self, parent, tableName, key):
        CInDocTableModel.__init__(self, tableName, 'id', 'master_id', parent)

        filter = u'''FIND_IN_SET(%s, REPLACE(domain, ' ', ''))>0 OR domain='' ''' % decorateString(key)
        self.addCol(CAccountingSystemInDocTableCol(u'Справочник', 'system_id', 40, filter=filter))
        stmt = u"""select column_name from information_schema.COLUMNS where table_name like '"""+ forceString(tableName) +"' and COLUMN_NAME like 'value_spr'"
        query = QtGui.qApp.db.query(stmt)
        if query.next():
            record = query.record()
            if forceString(record.value('column_name')) == u'value_spr':
                self.addCol(CAccountingSystemInDocTableColHybrid(    u'Идентификатор справочник', 'value_spr', 30, filter=filter))
        self.addCol(CInDocTableCol(    u'Идентификатор', 'value', 30, filter=filter))
        self.addCol(CDateInDocTableCol(u'Дата подтверждения', 'checkDate', 20))
        self.addCol(CInDocTableCol(u'Примечание', 'note', 40))
        self.isEditableSystem = {}
        self.isDeletableSystem = {}
        systemRecords = self.cols()[0]._getItems()
        self.row_system_id = None
        for record in systemRecords:
            systemId = forceRef(record.value('id'))
            self.isEditableSystem[systemId] = forceBool(record.value('isEditable'))
            self.isDeletableSystem[systemId] = forceBool(record.value('isDeletable'))

    def set_row_system_id(self, current, previous):
        if current.model().value(current.row(), u'system_id'):
            self.row_system_id = forceInt(current.model().value(current.row(), u'system_id'))


    def on_dataChanged(self, topLeft, bottomRight):
        if topLeft.column() == 0:
            if forceInt(topLeft.model().value(topLeft.row(), u'system_id')) != self.row_system_id:
                self.setValue(topLeft.row(), u'value_spr', u'')


    def identificationPresent(self, systemId, value):
        for item in self.items():
            if (     forceRef(item.value('system_id')) == systemId
                 and forceStringEx(item.value('value')) == value
               ):
                   return True
        return False


    def addIdentification(self, systemId, value):
        trimmedValue = trim(value)
        if self.identificationPresent(systemId, trimmedValue):
            return False
        item = self.getEmptyRecord()
        item.setValue('system_id', systemId)
        item.setValue('value', trimmedValue)
        item.setValue('checkDate', QDateTime.currentDateTime())
        self.addRecord(item)
    

    def loadItems(self, masterId):
        CInDocTableModel.loadItems(self, masterId)
        self.isEditable = {}
        self.isDeletable = {}
        for item in self.items():
            id = forceRef(item.value('id'))
            if id:
                systemId = forceRef(item.value('system_id'))
                self.isEditable[id] = self.isEditableSystem.get(systemId, False)
                self.isDeletable[id] = self.isDeletableSystem.get(systemId, False)


    def flags(self, index = QModelIndex()):
        column = index.column()
        if column in (0, 1):  # system_id, identifier
            row = index.row()
            items = self.items()
            record = items[row] if 0 <= row < len(items) else None
            if record:
                id = forceRef(record.value('id'))
                if id and not self.isEditable[id]:
                    return Qt.ItemIsSelectable | Qt.ItemIsEnabled
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
        if column in (2, 3):  # checkDate, note
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
        return CInDocTableModel.flags(self, index)


    def delRowsChecker(self, rows):
        items = self.items()
        for row in rows:
            record = items[row]
            id = forceRef(record.value('id'))
            if id and not self.isDeletable[id]:
                return False
        return True


def checkIdentification(dialog, tableWidget):
    model = tableWidget.model()
    for row, item in enumerate(model.items()):
        systemId = forceRef(item.value('system_id'))
        value    = forceStringEx(item.value('value'))
        value_spr = forceStringEx(item.value('value_spr')) if item.value('value_spr') else None
        if not (systemId or dialog.checkInputMessage(u'справочник',  False, tableWidget, row, 0)):
            return False
        if not (value or value_spr or dialog.checkInputMessage(u'идентификатор', False, tableWidget, row, 1)):
            return False
    return True


class CAccountingSystemComboBox(QtGui.QComboBox):
    def __init__(self, parent=None):
        QtGui.QComboBox.__init__(self, parent)
        self._model = CRecordListModel(self)
        self._model.addCol(CInDocTableCol(u'Код', 'code', 20))
        self._model.addCol(CInDocTableCol(u'Наименование', 'name', 40))
        self._model.addCol(CInDocTableCol(u'urn', 'urn', 40))
        
        self._view = CTableView(None)
        self._view.setModel(self._model)
        self.setView(self._view)
        self.setModel(self._model)
        self.setModelColumn(1)
        self._view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self._view.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    
    
    def showPopup(self):
        width = self.parent().width()
        self.view().setMinimumWidth(width)
        self.view().setMaximumWidth(width)
        super(CAccountingSystemComboBox, self).showPopup()


    def value(self):
        row = self.currentIndex()
        return self._model.items()[row].value('id')


    def setValue(self, itemId):
        idList = [r.value('id') for r in self._model.items()]
        index = 0
        try:
            index = idList.index(itemId)
        except ValueError:
            index = 0
        self.setCurrentIndex(index)


    def setItems(self, recordList):
        self._model.setItems(recordList)


class CAccountingSystemInDocTableCol(CInDocTableCol):
    mapFilterToRecords = {}

    def __init__(self, title, fieldName, width, **params):
        CInDocTableCol.__init__(self, title, fieldName, width, **params)
        self.filter = params.get('filter', '')


    def _getItems(self):
        recordList = self.mapFilterToRecords.get(self.filter, None)
        if recordList is None:
            recordList = QtGui.qApp.db.getRecordList('rbAccountingSystem', 'id,code,name,urn,isEditable,isDeletable', self.filter)
            self.mapFilterToRecords[self.filter] = recordList
        return recordList


    def toString(self, val, record):
        for item in self._getItems():
            if forceInt(item.value('id')) == forceInt(val):
                return forceString(item.value('name'))


    def toSortString(self, val, record):
        return forceString(self.toString(val, record)).lower()


    def getSortString(self, val, record):
        return toVariant(self.toSortString(val, record))


    def toStatusTip(self, val, record):
        return self.toString(val, record)


    def createEditor(self, parent):
        editor = CAccountingSystemComboBox(parent)
        recordList = self._getItems()
        editor.setItems(recordList)
        prefs = getPref(QtGui.qApp.preferences.windowPrefs, u'CAccountingSystemComboBox_view', {})
        editor._view.loadPreferences(prefs)
        return editor



    def setEditorData(self, editor, value, record):
        editor.setValue(forceInt(value))


    def getEditorData(self, editor):
        data = toVariant(editor.value())
        prefs = editor._view.savePreferences()
        setPref(QtGui.qApp.preferences.windowPrefs, u'CAccountingSystemComboBox_view', prefs)
        return data


def identificationInfo(parent, actionTypeId, tableName, key):
    from library.InDocTable import CInDocTableView
    layout = QtGui.QGridLayout(parent)
    tableView = CInDocTableView(parent)
    model = CIdentificationModel(parent, tableName, key)
    model.setReadOnly(True)
    tableView.setModel(model)
    infoWidget = QtGui.QDialog()
    infoWidget.setWindowTitle(u'Идентификаторы')
    infoWidget.resize(QSize(600, 150))
    layout.addWidget(tableView)
    infoWidget.setLayout(layout)
    model.loadItems(actionTypeId)
    infoWidget.exec_()

    

# class CAccountingSystemInDocTableColHybrid(CInDocTableCol):
#     mapFilterToRecords = {}
#     def __init__(self, title, fieldName, width, **params):
#         CInDocTableCol.__init__(self, title, fieldName, width, **params)
#         self.filter = params.get('filter', '')
# 
# 
#     def getUrn(self, parent=None, systemid=None):
#         if parent:
#             system_id = parent.parent().currentItem().value('system_id').toString()
#             stmt = u"""select urn from rbAccountingSystem where id =""" + forceString(system_id)
#             db = QtGui.qApp.db
#             query = db.query(stmt)
#             if query.next():
#                 rec_urn = query.record()
#                 urn = forceString(rec_urn.value('urn'))
#                 if urn and urn != '':
#                     urn = urn.replace('urn:oid:', 'v')
#                     return urn
#             else:
#                 return None
#         elif systemid:
#             stmt = u"""select urn from rbAccountingSystem where id =""" + forceString(systemid)
#             db = QtGui.qApp.db
#             query = db.query(stmt)
#             if query.next():
#                 rec_urn = query.record()
#                 urn = forceString(rec_urn.value('urn'))
#                 if urn and urn != '':
#                     urn = urn.replace('urn:oid:', 'v')
#                     return urn
#             else:
#                 return None
# 
# 
#     def createEditor(self, parent):
#         urn = self.getUrn(parent=parent)
#         checkExistView = self.checkViewURN(urn)
#         if checkExistView:
#             editor = CAccountingSystemIdentification(parent)
#             viewName = "`"+ urn + "`"
#             recordList = self._getItems(urn=viewName)
#             editor.setItems(recordList)
#             prefs = getPref(QtGui.qApp.preferences.windowPrefs, u'CAccountingSystemIdentification_view', {})
#             editor._view.loadPreferences(prefs)
#         else:
#             editor = QtGui.QLineEdit(parent)
#             editor.setReadOnly(True)
#         return editor
# 
#         
#     def setEditorData(self, editor, value, record):
#         if type(editor) == QtGui.QLineEdit:
#             editor.setText(forceStringEx(value))
#         else:
#             editor.setValue(forceInt(value))
# 
# 
#     def getEditorData(self, editor):
#         if type(editor) == QtGui.QLineEdit:
#             text = trim(editor.text())
#             if text:
#                 return toVariant(text)
#             else:
#                 return QVariant()
#         else:
#             data = toVariant(editor.value())
#             prefs = editor._view.savePreferences()
#             setPref(QtGui.qApp.preferences.windowPrefs, u'CAccountingSystemIdentification_view', prefs)
#             return data
# 
#     def _getItems(self, urn=None):
#         recordList = self.mapFilterToRecords.get(self.filter, None)
#         if urn:
#             if recordList is None:
#                 recordList = QtGui.qApp.db.getRecordList(urn, 'code,title')
#                 self.mapFilterToRecords[self.filter] = recordList
#         else:
#             if recordList is None:
#                 recordList = QtGui.qApp.db.getRecordList('rbAccountingSystem', 'id,code,name,urn,isEditable,isDeletable', self.filter)
#                 self.mapFilterToRecords[self.filter] = recordList
#         return recordList
# 
#     def toString(self, val, record):
#         system_id = forceInt(record.value(0))
#         urn = self.getUrn(systemid=system_id)
#         viewExists = self.checkViewURN(urn)
#         if viewExists:
#             urn = "`"+urn+"`"
#             for item in self._getItems(urn=urn):
#                 if forceInt(item.value('code')) == forceInt(val):
#                     return forceString(item.value('title'))
#         else:
#             # for item in self._getItems():
#             #     if forceInt(item.value('code')) == forceInt(val):
#             return forceString(val)
# 
#     def checkViewURN(self, urn):
#         db = QtGui.qApp.db
#         stmt = u"""select * from information_schema.VIEWS v where v.TABLE_NAME like  '"""+ forceString(urn)+u"'"
#         query = db.query(stmt)
#         if query.next():
#             return True
#         else:
#             return False

# Столбец "Идентификатор" в виде ComboBox без поиска
# class CAccountingSystemIdentification(QtGui.QComboBox):             # В теории
#     def __init__(self, parent=None):
#         QtGui.QComboBox.__init__(self, parent)
#         self._model = CRecordListModel(self)
#         # self._model.addCol(CInDocTableCol(u'ID', 'id', 20))
#         self._model.addCol(CInDocTableCol(u'Код', 'code', 20))
#         self._model.addCol(CInDocTableCol(u'Наименование', 'title', 20))
#         self._view = CTableView(None)
#         self._view.setModel(self._model)
#         self.setView(self._view)
#         self.setModel(self._model)
#         self.setModelColumn(1)
#         self._view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
#         self._view.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
#         # self.tabWidget.addTab(self._view, u"Результат")                 # Это первая вкладка должна быть
#         # self.layout_research = QtGui.QGridLayout()
#         # self.label_code = QtGui.QLabel(u'Код: ')
#         # self.code_field = QtGui.QLineEdit()
#         # self.layout_research.addWidget(self.label_code, 0, 0, 1, 1)
#         # self.layout_research.addWidget(self.code_field, 0, 1, 1, 1)
#         # self.label_title = QtGui.QLabel(u'Наименование: ')
#         # self.title_field = QtGui.QLineEdit()
#         # self.layout_research.addWidget(self.label_title, 1, 0, 1, 1)
#         # self.layout_research.addWidget(self.title_field, 1, 1, 1, 1)
#         # self.vertical_spacer = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
#         # self.layout_research.addItem(self.vertical_spacer, 2, 0, 2, 3)
#         # self.buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Reset)
#         # self.layout_research.addWidget(self.buttonBox, 3, 3, 1, 1)
#         # self.tabWidget.addTab(self.layout_research, u"Поиск")
#
#     def showPopup(self):
#         width = self.parent().width()
#         self.view().setMinimumWidth(width)
#         self.view().setMaximumWidth(width)
#         super(CAccountingSystemIdentification, self).showPopup()
#
#
#     def value(self):
#         row = self.currentIndex()
#         return self._model.items()[row].value('code')
#
#
#     def setValue(self, itemId):
#         idList = [r.value('code') for r in self._model.items()]
#         index = 0
#         try:
#             index = idList.index(itemId)
#         except ValueError:
#             index = 0
#         self.setCurrentIndex(index)
#
#
#     def setItems(self, recordList):
#         self._model.setItems(recordList)


class CAccountingSystemInDocTableColHybrid(CInDocTableCol):
    mapFilterToRecords = {}
    def __init__(self, title, fieldName, width, **params):
        CInDocTableCol.__init__(self, title, fieldName, width, **params)
        self.filter = params.get('filter', '')


    def createEditor(self, parent, option=None, index=None):
        urn = self.getUrn(parent=parent)
        checkExistView = checkViewURN(urn) if urn else False
        if checkExistView:
            tableName = u"`"+urn+u"`"
            temp_code = None
            if forceString(parent.parent().currentItem().value('value_spr')) != '':
                temp_code = forceString(parent.parent().currentItem().value('value_spr'))
            editor = CSprComboBoxEx(parent, tableName, temp_code)
            if tableName == u'`v1.2.643.5.1.13.13.11.1078`':
                editor.setFilter(u"`v1.2.643.5.1.13.13.11.1078`.ACTUAL = 'true'")
            # editor._code = forceString(parent.parent().currentItem().value('value_spr')) if forceString(parent.parent().currentItem().value('value_spr')) != '' \
            #                            else forceString(parent.parent().currentItem().value('value'))
        else:
            # editor = QtGui.QLineEdit(parent)
            # editor.setReadOnly(True)
            editor = QtGui.QLabel(parent)
        return editor

    
    def setEditorData(self, editor, value, record):
        # if type(editor) == QtGui.QLineEdit:
        #     editor.setText(forceStringEx(value))
        if type(editor) == QtGui.QLabel:
            editor.setText(u'')
        else:
            editor.setValue(forceRef(value))

    def getEditorData(self, editor):
        # if type(editor) == QtGui.QLineEdit:
        #     text = trim(editor.text())
        #     if text:
        #         return toVariant(text)
        #     else:
        #         return QVariant()
        if type(editor) == QtGui.QLabel:
            return QVariant()
        else:
            return toVariant(editor.value())
        

    def getUrn(self, parent=None, systemid=None):
        if parent:
            if hasattr(parent.parent().currentItem(), 'value'):
                system_id = parent.parent().currentItem().value('system_id').toString()
                if system_id:
                    stmt = u"""select urn from rbAccountingSystem where id =""" + forceString(system_id)
                    db = QtGui.qApp.db
                    query = db.query(stmt)
                    if query.next():
                        rec_urn = query.record()
                        urn = forceString(rec_urn.value('urn'))
                        if urn and urn != '':
                            urn = urn.replace('urn:oid:', 'v')
                            return urn
                    else:
                        return None
                else:
                    return None
            else:
                return None
        elif systemid:
            stmt = u"""select urn from rbAccountingSystem where id =""" + forceString(systemid)
            db = QtGui.qApp.db
            query = db.query(stmt)
            if query.next():
                rec_urn = query.record()
                urn = forceString(rec_urn.value('urn'))
                if urn and urn != '':
                    urn = urn.replace('urn:oid:', 'v')
                    return urn
            else:
                return None

    def toString(self, val, record):
        system_id = forceInt(record.value(0))
        urn = self.getUrn(systemid=system_id)
        viewExists = checkViewURN(urn) if urn else False
        if viewExists:
            urn = "`"+urn+"`"
            for item in self._getItems(urn=urn):
                if forceInt(item.value('id')) == forceInt(val):
                    return forceString(item.value('name'))
        else:
            # for item in self._getItems():
            #     if forceInt(item.value('code')) == forceInt(val):
            return forceString(val)

    def _getItems(self, urn=None):
        recordList = self.mapFilterToRecords.get(self.filter, None)
        if urn:
            if recordList is None:
                recordList = QtGui.qApp.db.getRecordList(urn, 'id,code,name')
                self.mapFilterToRecords[self.filter] = recordList
        else:
            if recordList is None:
                recordList = QtGui.qApp.db.getRecordList('rbAccountingSystem', 'id,code,name,urn,isEditable,isDeletable', self.filter)
                self.mapFilterToRecords[self.filter] = recordList
        return recordList


class CSpr_ComboBox(CRBComboBox):
    def __init__(self, parent, tableName=None):
        CRBComboBox.__init__(self, parent)
        self._tableName = tableName
        self._addNone = False
        self._customFilter = None
        self.setOrderByCode()
        if self._tableName:
            CRBComboBox.setTable(self, self._tableName, self._addNone, self.compileFilter(), self._order)
        
        
    def setTable(self, tableName, addNone=True, filter='', order=None):
        assert False

    def setAddNone(self, addNone=True):
        if self._addNone != addNone:
            self._addNone = addNone
            self.updateFilter()

    def compileFilter(self):
        if not QtGui.qApp.db:
            QtGui.qApp.openDatabase()
        db = QtGui.qApp.db
        cond = []
        if self._customFilter:
            cond.append(self._customFilter)
        return db.joinAnd(cond)


    def setOrderByCode(self):
        self._order = 'code, name'


    def setOrderByTitle(self):
        self._order = 'name, code'

    def setFilter(self, filter):
        if self._customFilter != filter:
            self._customFilter = filter
            self.updateFilter()

    def updateFilter(self):
        v = self.value()
        CRBComboBox.setTable(self, self._tableName, self._addNone, self.compileFilter(), self._order)
        self.setValue(v)



class CSprComboBoxEx(CSpr_ComboBox):
    __pyqtSignals__ = ('textChanged(QString)',
                       'textEdited(QString)'
                       )

    
    def __init__(self, parent, tableName=None, code=None):
        CSpr_ComboBox.__init__(self, parent, tableName)
        self._popup = None
        self._specialValueCount = 0
        self._tableName = tableName
        self._code = code
        
    def getActualEmptyRecord(self):
        self._createPopup()
        return self._popup.getActualEmptyRecord()
    
    def addNotSetValue(self):
        record = self.getActualEmptyRecord()
        record.setValue('code', QVariant(u"----"))
        record.setValue('name', QVariant(u"Значение не задано"))
        self.setSpecialValues(((-1,record),))

    def setSpecialValues(self, specialValues):
        self._createPopup()
        self._popup.setSpecialValues(specialValues)
        sv = []
        for id, record in specialValues:
            sv.append((id, forceString(record.value('code')), forceString(record.value('name'))))
        CPersonComboBox.setSpecialValues(self, sv)
        self._specialValueCount = len(sv)

    def _createPopup(self):
        if not self._popup:
            self._popup = CSprComboBoxExPopup(self, self._tableName, self._code)
            self.connect(self._popup, SIGNAL('sprCodeSelected(int)'), self.setValue)
            #

    def showPopup(self):
        if not self.isReadOnly():
            self._createPopup()
            self._popup.setFilter(self._customFilter)
            pos = self.rect().bottomLeft()
            pos = self.mapToGlobal(pos)
            size = self._popup.sizeHint()
            screen = QtGui.QApplication.desktop().availableGeometry(pos)
            size.setWidth(screen.width()/2)
            pos.setX(max(min(pos.x(), screen.right() - size.width()), screen.left()))
            pos.setY(max(min(pos.y(), screen.bottom() - size.height()), screen.top()))
            self._popup.move(pos)
            self._popup.resize(size)
            if self._code:
                self._popup.setSprCode(self._code)
            else:
                self._popup.on_buttonBox_apply()
            self._popup.show()

    # def setCode(self, code):
    #     self._code = code
    #     pass


class CSprComboBoxExPopup(QtGui.QFrame, Ui_IdentificationComboBoxExPopup):
    __pyqtSignals__ = ('sprCodeSelected(int)')
    
    def __init__(self, parent=None, sprName=None, code=None):
        QtGui.QFrame.__init__(self, parent, Qt.Popup)
        self.setFrameShape(QtGui.QFrame.StyledPanel)
        self.setAttribute(Qt.WA_WindowPropagation)
        self.tableModel = CSprTableModel(self, sprName)
        self.tableSelectionModel = QtGui.QItemSelectionModel(self.tableModel, self)
        self.tableSelectionModel.setObjectName('tableSelectionModel')
        self.setupUi(self)
        self.tblSpr.setModel(self.tableModel)
        self.tblSpr.setSelectionModel(self.tableSelectionModel)
        self.tblSpr.setSortingEnabled(True)
        self.buttonBox.button(QtGui.QDialogButtonBox.Apply).setDefault(True)
        self.buttonBox.button(QtGui.QDialogButtonBox.Apply).setShortcut(Qt.Key_Return)
        self.spr_code = code
        self.spr_title = None
        self.tblSpr.installEventFilter(self)
        preferences = getPref(QtGui.qApp.preferences.windowPrefs, 'CIdentificationComboBoxExPopup', {})
        self.tblSpr.loadPreferences(preferences)
        self.prevColumn = None
        self.asc = True
        self.connect(self.tblSpr.horizontalHeader(), SIGNAL('sectionClicked(int)'), self._setSprOrderByColumn)
        self.buttonBox.setVisible(False)
        self.edit_title.setText('')
        self.leCode.setText('')
        self._parent = parent
        self._customFilter = None
        self._tableName = sprName
        self._setSprOrderByColumn(2)
        self.tblSpr.horizontalHeader().setSortIndicator(1, Qt.AscendingOrder)

    # def getActualEmptyRecord(self):
    #     return self.tableModel.getActualEmptyRecord()
    
    def getStringValue(self, id):
        return self.tableModel.getStringValue(id)

    # def addNotSetValue(self):
    #     self.tableModel.addNotSetValue()

    def setFilter(self, filter):
        self._customFilter = filter

    def mousePressEvent(self, event):
        parent = self.parentWidget()
        if parent is not None:
            opt = QtGui.QStyleOptionComboBox()
            opt.init(parent)
            arrowRect = parent.style().subControlRect(
                QtGui.QStyle.CC_ComboBox, opt, QtGui.QStyle.SC_ComboBoxArrow, parent)
            arrowRect.moveTo(parent.mapToGlobal(arrowRect.topLeft()))
            if arrowRect.contains(event.globalPos()) or self.rect().contains(event.pos()):
                self.setAttribute(Qt.WA_NoMouseReplay)
        QtGui.QFrame.mousePressEvent(self, event)

    def closeEvent(self, event):
        preferences = self.tblSpr.savePreferences()
        setPref(QtGui.qApp.preferences.windowPrefs, 'CIdentificationComboBoxExPopup', preferences)
        QtGui.QFrame.closeEvent(self, event)


    def eventFilter(self, watched, event):
        if watched == self.tblSpr:
            if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Select):
                event.accept()
                index = self.tblSpr.currentIndex()
                self.tblSpr.emit(SIGNAL('doubleClicked(QModelIndex)'), index)
                return True
        return QtGui.QFrame.eventFilter(self, watched, event)

    @pyqtSignature('QModelIndex')
    def on_tblSpr_doubleClicked(self, index):
        if index.isValid():
            if Qt.ItemIsEnabled & self.tableModel.flags(index):
                code = self.getCurrentCode()
                self.selectCode(code)

    def getCurrentCode(self):
        return forceString(self.tblSpr.currentItem().value('id'))
    
    def setSprCode(self, code):
        self.spr_code = code
        self.on_buttonBox_apply(code)

    def selectCode(self, code):
        self.spr_code = code
        self.emit(SIGNAL('sprCodeSelected(int)'), forceInt(code))
        self.close()

    def _setSprOrderByColumn(self, column):
        code = self.leCode.text()
        title = self.edit_title.text()
        id = self.tblSpr.currentItemId()
        updateTable = self.getSprIdList(self._tableName, code, title, orderByColumn=column)
        self.setSprIdList(updateTable, id)
        self.prevColumn = column

    def initModel(self, id=None):
        self.on_buttonBox_apply(id)

    def setSprIdList(self, idList, posToId):
        if idList:
            self.tblSpr.setIdList(idList, posToId)
            # self.tabWidget.setCurrentIndex(0)
            # self.tabWidget.setTabEnabled(0,True)
        else:
            self.tblSpr.setIdList(idList)
            # self.tabWidget.setTabEnabled(0, True)


    @pyqtSignature('QAbstractButton*')
    def on_buttonBox_clicked(self, button):
        buttonCode = self.buttonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.on_buttonBox_apply()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_buttonBox_reset()

    def on_buttonBox_reset(self):
        self.edit_title.setText("")
        self.leCode.setText("")

    def on_buttonBox_apply(self, id=None):
        code = forceString(self.leCode.text())
        title = forceString(self.edit_title.text())
        
        crIdList = self.getSprIdList(self._tableName, code, title)
        real_id = self.getSprRealId(self._tableName, id) if id else None
        if real_id != None and len(real_id) > 0 :
            self.setSprIdList(crIdList, forceInt(real_id[0]))
        else:
            self.setSprIdList(crIdList, real_id)
            
    def getSprIdList(self, tableName, code, title, orderByColumn=1):
        db = QtGui.qApp.db
        if not QtGui.qApp.dbInside.databaseName() in tableName:
            tableName = QtGui.qApp.dbInside.databaseName() + u'.'+tableName
        tableSpr = db.table(tableName)
        
        cond = []
        if code:
            cond.append(tableSpr['code'].eq(code))
        if title:
            cond.append(tableSpr['name'].like(forceString(u'%'+title+u'%')))
        if self._customFilter:
            cond.append(self._customFilter)

        order = tableName+ u".name "
        asc = u'ASC'
        desc = u'DESC'
        orderName = u", " + tableName + u".name "
        if orderByColumn == 0:
            order = tableName + u".code"
        if orderByColumn == 1:
            order = tableName+ u".name "

        if self.prevColumn == orderByColumn and self.asc:
            self.asc = False
            order+=u' '+desc + u' '+ orderName + asc
        elif self.prevColumn == orderByColumn and not self.asc:
            self.asc = True
            order+= u' '+asc + u' '+ orderName + asc
        else:
            self.asc = True
            order+= u' '+ asc + u' '+orderName + asc
        order = str(order)
        idList = db.getDistinctIdList(tableSpr, [tableSpr['id'].name(), tableSpr['code'].name(), tableSpr['name'].name()],
                                      where=cond,
                                      order=order,
                                      #limit=1000 ???
                                      )
        # fakeIdList = self.tableModel.getSpecialValuesKeys()
        # if fakeIdList:
        #     return fakeIdList+idList
        return idList

    def getSprRealId(self, tableName, code):
        db = QtGui.qApp.db
        if not QtGui.qApp.dbInside.databaseName() in tableName:
            tableName = QtGui.qApp.dbInside.databaseName() + u'.'+tableName
        tableSpr = db.table(tableName)
        cond = []
        if code:
            cond.append(tableSpr['id'].eq(forceString(code)))
        order = u' id asc'
        id = db.getDistinctIdList(tableSpr, [tableSpr['id'].name()], where=cond, order=order, limit=1)
        return id

    @pyqtSignature('QString')
    def on_edit_title_textChanged(self, text):
        self.on_buttonBox_apply()


    @pyqtSignature('QString')
    def on_leCode_textChanged(self, text):
        self.on_buttonBox_apply()



class CSprTableModel(CTableModel):
    def __init__(self, parent, tableName):
        CTableModel.__init__(self, parent)
        self._parent = parent
        self._specialValues = []
        # self.addColumn(CTextCol(u'ИД', ['id'], 10))
        self.addColumn(CTextCol(u"Код",['code'],30))
        self.addColumn(CTextCol(u"Наименование", ['name'], 30))
        self._fieldNames = [tableName+u".id",tableName+u".code", tableName+u".name"]
        self.setTable(tableName)
        self._tableName = tableName
        # self._cols[0].setDefaultHidden(True)

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    # def getActualEmptyRecord(self):
    #     record = QtSql.QSqlRecord()
    #     record.append(QtSql.QSqlField('group_id', QVariant.Int))
    #     record.append(QtSql.QSqlField('npp', QVariant.Int))
    #     record.append(QtSql.QSqlField('code', QVariant.String))
    #     record.append(QtSql.QSqlField('name', QVariant.String))
    #     record.append(QtSql.QSqlField('deleted', QVariant.Int))
    #     record.append(QtSql.QSqlField('version', QVariant.String))
    #     record.append(QtSql.QSqlField('DATA_END', QVariant.String))
    #     record.append(QtSql.QSqlField('urn', QVariant.String))
    #     record.append(QtSql.QSqlField('can_choose', QVariant.Int))
    #     return record

    def getStringValue(self, id):
        row = self._idList.index(id) if id in self._idList else None
        if row is not None:
            title = forceStringEx(self.data(self.index(row, 1)))
            return title
        return forceString(QtGui.qApp.db.translate(self._tableName, 'id', id, 'name'))


    def setSpecialValues(self, specialValues):
        if self._specialValues != specialValues:
            self._specialValues = specialValues
            self.setTable(specialValues)  # WTF? таки specialValues или tableName?

    def getSpecialValuesKeys(self):
        return [key for key, item in self._specialValues]


    def setTable(self, tableName):  # WFT? tableName не используется?
        db = QtGui.qApp.db
        if not QtGui.qApp.dbInside.databaseName() in tableName:
            tableName = QtGui.qApp.dbInside.databaseName() + u'.' +tableName
        tableSpr = db.table(tableName)
        loadFields = []
        loadFields.append(u'DISTINCT ' + u', '.join(self._fieldNames))
        self._table = tableSpr
        self._recordsCache = CTableRecordCache(db, self._table, loadFields, fakeValues=self._specialValues)


