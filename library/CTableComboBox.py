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

import re
from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import Qt, QAbstractTableModel, QDateTime, QModelIndex, QString, QVariant, QEvent

from library.SortFilterProxyTableModel import CSortFilterProxyTableModel
from library.Utils import forceInt, forceString, forceRef 
from library.adjustPopup import adjustPopupToWidget
from library.DbEntityCache import CDbEntityCache
from library.database import checkViewURN


class CAbstractTableModelData(object):
    def __init__(self):
        self.buff = []
        self.mapIdToIndex = {}

    def addItem(self, id, fields):
        self.mapIdToIndex[id] = len(self.buff)
        self.buff.append((id, fields))

    def getCount(self):
        return len(self.buff)

    def getId(self, index):
        if index < 0:
            return None
        return self.buff[index][0]

    def getValue(self, index, showFields):
        if index < 0:
            return None
        return self.buff[index][1][showFields]

    def getIndexById(self, id):
        result = self.mapIdToIndex.get(id, -1)
        if result < 0 and not id:
            result = self.mapIdToIndex.get(None, -1)
        return result

    def getString(self, index, showFields):
        if showFields >= 0:
            return self.getValue(index, showFields)
        else:
            return 'bad field %s' % showFields

    def getStringById(self, id, showFields):
        index = self.getIndexById(id)
        if index >= 0:
            return self.getString(index, showFields)
        return '{' + str(id) + '}'


class CTableModelData(CAbstractTableModelData):
    """class for store data of ref book"""

    def __init__(self, tableName, addNone, filter, fields, order, specialValues):
        CAbstractTableModelData.__init__(self)
        self._tableName = tableName
        self._addNone = addNone
        self._filter = filter
        self._fields = fields
        self._order = order
        self._checkSum = None
        self._timestamp = None
        self._specialValues = specialValues
        self._notLoaded = True
        self._value = None

    def getCount(self):
        if self._notLoaded:
            self.load()
        return len(self.buff)

    def getId(self, index):
        if self._notLoaded:
            self.load()
        return CAbstractTableModelData.getId(self, index)

    def getValue(self, index, showFields):
        if self._notLoaded:
            self.load()
        return CAbstractTableModelData.getValue(self, index, showFields)

    def getIndexById(self, id):
        if self._value != id:
            self._value = id
            self._notLoaded = True
        if self._notLoaded or (id and CAbstractTableModelData.getIndexById(self, id) < 0):
            self.load(id)
        return CAbstractTableModelData.getIndexById(self, id)

    def getString(self, index, showFields):
        if self._notLoaded:
            self.load()
        return CAbstractTableModelData.getString(self, index, showFields)

    def getStringById(self, id, showFields):
        if self._notLoaded:
            self.load()
        return CAbstractTableModelData.getStringById(self, id, showFields)

    def load(self, valId = 0):
        self.buff = []
        self.mapIdToIndex = {}
        if self._addNone:
            item = []
            for field in self._fields[1:].split(','):
                item.append('')
            self.addItem(None, item)
        db = QtGui.qApp.db
        where = (' WHERE ' + self._filter) if self._filter else ''
        table = db.table(self._tableName)
        deletedField = table.findField('deleted')
        if deletedField:
            if valId is None:
                valId = 0
            if where:
                where += " AND deleted = 0 or id = {}".format(valId)
            else:
                where = 'WHERE deleted = 0 or id = {}'.format(valId)
        # добавил cast(code as signed) для корректной сортировки
        order = ' ORDER BY ' + (self._order if self._order else 'cast(id as signed)')
        query = db.query('SELECT id{} FROM '.format(self._fields) + self._tableName + where + order)
        while query.next():
            item = []
            record = query.record()
            id = forceInt(record.value('id'))
            for field in self._fields[1:].split(','):
                item.append(forceString(record.value(field)))
            self.addItem(id, item)
        self._timestamp = QDateTime.currentDateTime()
        self._notLoaded = False

    def isLoaded(self):
        return not self._notLoaded


class CTableModelDataCache(CDbEntityCache):
    mapTableToData = {}

    @classmethod
    def getData(cls, tableName, addNone=True, filter='', fields='', order=None, specialValues=None, needCache=True, force=False):
        strTableName = unicode(tableName)
        if isinstance(specialValues, list):
            specialValues = tuple(specialValues)
        key = (strTableName, addNone, filter, order, specialValues)
        result = cls.mapTableToData.get(key, None)
        if not result or force:
            result = CTableModelData(strTableName, addNone, filter, fields, order, specialValues)
            cls.connect()
            if needCache:
                cls.mapTableToData[key] = result
        return result

    @classmethod
    def reset(cls, tableName=None):
        if tableName:
            for key in cls.mapTableToData.keys():
                if key[0] == tableName:
                    del cls.mapTableToData[key]
        else:
            cls.mapTableToData.clear()

    @classmethod
    def purge(cls):
        cls.reset()


class CTableModel(QAbstractTableModel):
    def __init__(self, parent):
        QAbstractTableModel.__init__(self, parent)
        self.d = None
        self.resetRequired = False
        self.readOnly = False
        self._fieldNames = []
        self._fields = []

    def setReadOnly(self, value=False):
        self.readOnly = value

    def isReadOnly(self):
        return self.readOnly
    
    def setFieldNames(self, fieldNames):
        self._fieldNames = fieldNames

    def setFields(self, fields):
        self._fields = fields.split(',')
        
    def getValue(self, index, showFields=0):
        return self.d.getValue(index, showFields)

    def flags(self, index=QModelIndex()):
        result = QAbstractTableModel.flags(self, index)
        if self.readOnly:
            result = Qt.ItemIsEnabled
        return result
    

    def searchCodeEx(self, code):
        def maxCommonLen(c1, c2):
            n = min(len(c1), len(c2))
            for i in xrange(n):
                if c1[i] != c2[i]:
                    return i
            return n

        code = unicode(code).upper()
        codeLen = len(code)
        n = self.d.getCount()
        maxLen = -1
        maxLenAt = -1
        for i in xrange(n):
            itemCode = unicode(self.d.getValue(i, 1)).upper()
            commonLen = maxCommonLen(itemCode, code)
            if commonLen == codeLen == len(itemCode):
                return i, code
            if commonLen > maxLen:
                maxLen, maxLenAt = commonLen, i
        return maxLenAt, code[:maxLen]

    def setTable(self, tableName, addNone=True, filter='', fields='', fieldNames=[], order=None, specialValues=None, needCache=True, force=False):
        d = self.d
        self.setFieldNames(fieldNames)
        if d and d.isLoaded() or self.resetRequired:
            if hasattr(self, 'beginResetModel'):
                self.beginResetModel()
            self.d = CTableModelDataCache.getData(tableName, addNone, filter, fields, order, specialValues, needCache, force)
            if hasattr(self, 'endResetModel'):
                self.endResetModel()
            else:
                self.reset()
        else:
            self.d = CTableModelDataCache.getData(tableName, addNone, filter, fields, order, specialValues, needCache, force)

    def columnCount(self, index=None):
        return len(self._fieldNames)

    def rowCount(self, index=None):
        if self.d:
            return self.d.getCount()
        else:
            self.resetRequired = True
            return 0

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                if section >= 0:
                    return QVariant(self._fieldNames[section])
        return QVariant()

    def searchId(self, itemId):
        return self.d.getIndexById(itemId)

    def getId(self, index):
        return self.d.getId(index)

    def cols(self):
        # для CSortFilterProxyTableModel
        from library.TableModel import CCol
        cols = []
        for field in self._fields:
            cols.append(CCol('', [field], 0, 'l'))
        return cols
    
    
    def getRecordByRow(self, row):
        # для CSortFilterProxyTableModel
        record = QtSql.QSqlRecord()
        record.append(QtSql.QSqlField('id', QVariant.Int))
        record.append(QtSql.QSqlField(self._fields[1], QVariant.String))
        record.append(QtSql.QSqlField('name', QVariant.String))
        record.setValue('id', self.getId(row))
        record.setValue(self._fields[1], self.getValue(row, 0))
        return record    
    
    
    def _buildTreePathForId(self, idVal):
        if idVal is None:
            return None

        treeItems = getattr(self, '_treeItems', None)
        treeModel = getattr(self, '_treeModel', None)
        item = None
        if treeItems:
            item = treeItems.get(idVal, None)

        if item is None and treeModel is not None:
            def findRec(it):
                if it.data(Qt.UserRole) == idVal:
                    return it
                for i in range(it.rowCount()):
                    found = findRec(it.child(i))
                    if found:
                        return found
                return None

            for r in range(treeModel.rowCount()):
                top = treeModel.item(r)
                res = findRec(top)
                if res:
                    item = res
                    break
                if top.data(Qt.UserRole) == idVal:
                    item = top
                    break
        if item is None:
            return None

        parts = []
        it = item
        while it is not None:
            txt = forceString(it.text())
            txt = re.sub(ur'^\s*\d+\s*(?:[-–—\.:)]\s*)?', u'', txt, 1, re.UNICODE)
            if txt:
                parts.insert(0, txt)
            it = it.parent()
        if not parts:
            return None
        return u': '.join(parts)


    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        elif role == Qt.DisplayRole or role == Qt.EditRole:
            row = index.row()
            if row < self.d.getCount():
                recId = self.getId(row)
                if getattr(self, '_treeItems', None) or getattr(self, '_treeModel', None):
                    fullPath = self._buildTreePathForId(recId)
                    if fullPath:
                        return QVariant(fullPath)
                return QVariant(self.d.getString(row, index.column()))
        return QVariant()



class CTableSelectionModel(QtGui.QItemSelectionModel):
    def select(self, indexOrSelection, command):
        if isinstance(indexOrSelection, QModelIndex):
            index = indexOrSelection
            ##            print 'select-2', index.column()
            if index.column() > 1:
                correctIndex = self.model().index(index.row(), index.column())
            else:
                correctIndex = index
            if command & QtGui.QItemSelectionModel.Select and not (command & QtGui.QItemSelectionModel.Current):
                self.setCurrentIndex(correctIndex,
                                     QtGui.QItemSelectionModel.Clear | QtGui.QItemSelectionModel.Select | QtGui.QItemSelectionModel.Current)
            else:
                QtGui.QItemSelectionModel.select(self, correctIndex, command)

        else:
            QtGui.QItemSelectionModel.select(self, indexOrSelection, command)


class CTablePopupView(QtGui.QTableView):
    def __init__(self, parent):
        QtGui.QTableView.__init__(self, parent)
        self.verticalHeader().setResizeMode(QtGui.QHeaderView.Fixed)
        h = self.fontMetrics().height()
        self.verticalHeader().setDefaultSectionSize(3*h/2)
        self.verticalHeader().hide()
        self.horizontalHeader().setStretchLastSection(True)
        self.setSortingEnabled(True)


    def resizeEvent(self, resizeEvent):
        QtGui.QTableView.resizeEvent(self, resizeEvent)
        self.resizeColumnToContents(0)


    def keyboardSearch(self, search):
        proxyModel = self.model()
        sourceModel = proxyModel.sourceModel()
        row, search = sourceModel.searchCodeEx(search)
        if row >= 0:
            sourceIndex = sourceModel.index(row, 1)
            proxyIndex = proxyModel.mapFromSource(sourceIndex)
            self.setCurrentIndex(proxyIndex)


    def preferredWidth(self):
        return 100


class CTableComboBox(QtGui.QComboBox):
    u"""ComboBox, в котором отображается содержимое любой таблицы"""

    def __init__(self, parent):
        QtGui.QComboBox.__init__(self, parent)
        self._searchString = ''
        self._tableName = ''
        self._addNone   = True
        self._needCache = True
        self._filier    = ''
        self._order     = ''
        self._specialValues = None
        self.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToMinimumContentsLength)
        self.preferredWidth = None
        self.popupView = CTablePopupView(self)
        self.setView(self.popupView)
        self.setModel(CTableModel(self))
        self.popupView.setFrameShape(QtGui.QFrame.NoFrame)
        self.readOnly = False
        self.installEventFilter(self)


    def setReadOnly(self, value=False):
        self.readOnly = value
        self._model.setReadOnly(self.readOnly)


    def isReadOnly(self):
        return self.readOnly


    def setPreferredWidth(self, preferredWidth):
        self.preferredWidth = preferredWidth


    def setTable(self, tableName, addNone=True, filter='', fields='', fieldNames=[], order=None, specialValues=None, needCache=True, force=False, rawTable=None):
        if not checkViewURN(rawTable if rawTable else tableName):
            return False
        self._tableName = tableName
        self._addNone = addNone
        self._filier = filter
        self._fields = fields
        self._order = order
        self._needCache = needCache
        self._specialValues = specialValues
        self._model.setTable(tableName, addNone, filter, fields, fieldNames, order, specialValues, needCache, force=force)
        self._model.setFieldNames(fieldNames)
        self._model.setFields(fields)


    def setSpecialValues(self, specialValues):
        if self._specialValues != specialValues:
            self._specialValues = specialValues
            self.reloadData()


    def setFilter(self, filter='', order=None):
        self._filier    = filter
        self._order     = order
        self.setTable(self._tableName, self._addNone, filter, self._fields, self._model._fieldNames, order, self._specialValues, self._needCache)


    def setLocalFilter(self, recordFieldName, value, matchMethod=CSortFilterProxyTableModel.MatchExactly, isCaseSensitive=False):
        self.proxyModel.setFilter(recordFieldName, value, matchMethod, isCaseSensitive)


    def removeLocalFilter(self, recordFieldName):
        self.proxyModel.removeFilter(recordFieldName)


    def clearLocalFilters(self):
        self.proxyModel.clearFilters()


    def reloadData(self):
        self._model.setTable(self._tableName, self._addNone, self._filier,
                             self._order, self._specialValues, self._needCache,
                             True)


    updateModel = reloadData


    def hasTable(self):
        return bool(self._tableName)
            

    def setModel(self, model):
        self._model = model
        self.proxyModel = CSortFilterProxyTableModel(self, self._model)
        QtGui.QComboBox.setModel(self, self.proxyModel)
        self.setModelColumn(1)
        self._selectionModel = CTableSelectionModel(self.proxyModel)
        self.popupView.setSelectionModel(self._selectionModel)


    def model(self):
        return self._model


    def setValue(self, itemId):
        u"""id записи"""
        if not self.hasTable():
            return
        row = self._model.searchId(itemId)
        if row == -1:
            self.setCurrentIndex(-1)
        else:
            sourceIndex = self._model.index(row, 0)
            proxyIndex = self.proxyModel.mapFromSource(sourceIndex)
            self.setCurrentIndex(proxyIndex.row())


    def getValue(self):
        u"""id записи"""
        return self.value()


    def value(self):
        u"""id записи"""
        if not self.hasTable():
            return None
        row = self.currentIndex()
        rowIndex = self.proxyModel.index(row, 0)
        sourceIndex = self.proxyModel.mapToSource(rowIndex)
        return self._model.getId(sourceIndex.row())


    def idList(self):
        idList = []
        for row in xrange(self._model.rowCount(None)):
            idList.append(self._model.getId(row))
        return idList


    def addItem(self, item):
        pass


    def showPopup(self):
        if not self.isReadOnly():
            totalItems = self._model.rowCount(None)
            if totalItems>0:
                self._searchString = ''
                view = self.popupView
                selectionModel = view.selectionModel()
                selectionModel.setCurrentIndex(self.proxyModel.index(self.currentIndex(), 1),
                                                     QtGui.QItemSelectionModel.ClearAndSelect)
                tblHeaderHeight = view.horizontalHeader().height()
                maxVisibleItems = self.maxVisibleItems()
                visibleItems = min(maxVisibleItems, totalItems)
                if visibleItems > 0:
                    view.setFixedHeight( view.rowHeight(0)*visibleItems + tblHeaderHeight)
                frame = view.parent()
                sizeHint = view.sizeHint() * 0.01
                adjustPopupToWidget(self, frame, True, max(self.preferredWidth, sizeHint.width())*2, view.height()+2)
                frame.show()
                view.setFocus()
                scrollBar = view.horizontalScrollBar()
                scrollBar.setValue(0)


    def focusOutEvent(self, event):
        self._searchString = ''
        QtGui.QComboBox.focusOutEvent(self, event)


    def keyPressEvent(self, event):
        if self.isReadOnly():
            event.accept()
        else:
            key = event.key()
            if key == Qt.Key_Escape:
                event.ignore()
            elif key == Qt.Key_Return or key == Qt.Key_Enter:
                event.ignore()
            if key == Qt.Key_Delete:
                self._searchString = ''
                self.setCurrentIndex(-1)
                event.accept()
            elif key == Qt.Key_Backspace: # BS
                self._searchString = self._searchString[:-1]
                self.lookup()
                event.accept()
            elif key == Qt.Key_Space:
                QtGui.QComboBox.keyPressEvent(self, event)
            elif not event.text().isEmpty():
                char = event.text().at(0)
                if char.isPrint():
                    self._searchString = self._searchString + unicode(QString(char)).upper()
                    self.lookup()
                    event.accept()
                else:
                    QtGui.QComboBox.keyPressEvent(self, event)
            else:
                QtGui.QComboBox.keyPressEvent(self, event)


    def lookup(self):
        i, self._searchString = self._model.searchCodeEx(self._searchString)
        if i>=0 and i!=self.currentIndex():
            self.setCurrentIndex(i)


    def eventFilter(self,  obj,  event):
        if self.isReadOnly():
            event.accept()
            return False
        return False


class CTableSearchPopupView(QtGui.QFrame):
    def __init__(self, parent, popupView):
        QtGui.QFrame.__init__(self, parent)
        self.setFrameShape(QtGui.QFrame.StyledPanel)
        self.setAttribute(Qt.WA_WindowPropagation)
        self.setWindowFlags(Qt.Popup)
        self._cmb = parent
        self.filter = parent._filier
        self.table = popupView
        self.table.doubleClicked.connect(self.on_table_doubleClicked)
        layout = QtGui.QVBoxLayout(self)
        layoutFilter = QtGui.QHBoxLayout()
        
        self.lblCode = QtGui.QLabel()
        self.lblCode.setText(u'Код')
        self.edtCode = QtGui.QLineEdit()
        self.edtCode.textChanged.connect(self.on_edtCode_textChanged)
        layoutFilter.addWidget(self.lblCode)
        layoutFilter.addWidget(self.edtCode)
        
        self.lblName = QtGui.QLabel()
        self.lblName.setText(u'Наименование')
        self.edtName = QtGui.QLineEdit()
        self.edtName.textChanged.connect(self.on_edtName_textChanged)
        layoutFilter.addWidget(self.lblName)
        layoutFilter.addWidget(self.edtName)
        
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        layout.addLayout(layoutFilter)
        layout.addWidget(self.table)
        self.installEventFilter(self)


    def on_table_doubleClicked(self, index):
        self._cmb.setCurrentIndex(index.row())
        self._cmb.hidePopup()


    def on_edtCode_textChanged(self, code):
        db = QtGui.qApp.db
        table = db.table(self._cmb._tableName)
        _filter = []
        if code:
            _filter.append(table['code'].like('%' + unicode(code) + '%'))
        if self.filter and _filter:
            _filter = db.joinAnd([self.filter, db.joinAnd(_filter)])
        else:
            _filter = db.joinAnd(_filter)
        self._cmb.setFilter(_filter)


    def on_edtName_textChanged(self, name):
        db = QtGui.qApp.db
        table = db.table(self._cmb._tableName)
        _filter = []
        if name:
            _filter.append(table['name'].like('%' + unicode(name) + '%'))
        if self.filter and _filter:
            _filter = db.joinAnd([self.filter, db.joinAnd(_filter)])
        else:
            _filter = db.joinAnd(_filter)
        self._cmb.setFilter(_filter)


    def eventFilter(self, obj, event):
        if obj == self.table:
            if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Select):
                event.accept()
                index = self.table.currentIndex()
                self.on_table_doubleClicked(index)
                return True
        return QtGui.QFrame.eventFilter(self, obj, event)


class CTableSearchComboBox(CTableComboBox):
    u"""Combobox для таблицы с возможностью поиска по code и title"""
    def __init__(self, parent=None):
        CTableComboBox.__init__(self, parent)
        self.popupView = CTableSearchPopupView(self, self.popupView)


    def setCodeFilter(self, code):
        if code:
            self.setLocalFilter(self._fields[1:].split(',')[0], code, CSortFilterProxyTableModel.MatchContains, isCaseSensitive=False)
        else:
            self.removeLocalFilter(self._fields[1:].split(',')[0])


    def showPopup(self):
        if not self.isReadOnly():
            if 'code' not in self._fields[1:].split(','):
                self.popupView.lblCode.setVisible(False)
                self.popupView.edtCode.setVisible(False)
            if 'name' not in self._fields[1:].split(','):
                self.popupView.lblName.setVisible(False)
                self.popupView.edtName.setVisible(False)
            self._searchString = ''
            view = self.popupView.table
            frame = self.popupView
            frame.filter = ''
            sizeHint = view.sizeHint()
            selectionModel = view.selectionModel()
            selectionModel.setCurrentIndex(self._model.index(self.currentIndex(), 1),
                                           QtGui.QItemSelectionModel.ClearAndSelect)
            adjustPopupToWidget(self, frame, True, max(sizeHint.width(), self.preferredWidth)*2, sizeHint.height())
            frame.show()
            view.setFocus()


    def hidePopup(self):
        self.popupView.hide()


class CTableTreeSearchComboBox(CTableSearchComboBox):
    def setTable(self, tableName, fields={}, fieldNames=None, order='', parentCol=None, childCol=None, orderCol=None, filter='', rawTable=None):
        if not checkViewURN(rawTable if rawTable else tableName):
            return False
        CTableSearchComboBox.setTable(self, tableName, False, fields=','+','.join(fields), fieldNames=fields, order=order, filter=filter, rawTable=rawTable)

        try:
            table = QtGui.qApp.db.table(tableName)
        except Exception:
            return

        if not parentCol or not childCol:
            self._treeModel = None
            self._treeView = None
            self._treePopup = None
            return

        fetchFields = [u'id']
        if parentCol not in fetchFields:
            fetchFields.append(parentCol)
        if isinstance(fields, list):
            for k in fields:
                if k not in fetchFields:
                    fetchFields.append(k)

        if orderCol:
            sortKey = orderCol
        else:
            try:
                sortKey = fields.keys()[0]
            except Exception:
                sortKey = None

        where = filter if filter else u''
        try:
            records = QtGui.qApp.db.getRecordList(table, fetchFields, where=where, order=order)
        except Exception:
            self._treeModel = None
            return

        recs = []
        for rec in records:
            parentValue = None
            childValue = None
            try:
                rid = forceRef(rec.value('id'))
            except Exception:
                continue
            try:
                childValue = rec.value(childCol)
            except Exception:
                childValue = None
            try:
                parentValue = rec.value(parentCol)
            except Exception:
                parentValue = None
            childValue = forceString(childValue) if childValue is not None else u''
            parentValue = forceString(parentValue) if parentValue is not None else None
            recDict = {
                'id': rid,
                'childCol': childValue,
                'parentCol': parentValue,
            }
            if isinstance(fields, list):
                for k in fields:
                    recDict[k] = forceString(rec.value(k))
            recs.append(recDict)

        #mapParent = {}
        #for r in recs:
        #    pk = r['parentCol'] if r['parentCol'] else None
        #    mapParent.setdefault(pk, []).append(r)

        availableIds = set(r['childCol'] for r in recs)
        mapParent = {}
        for r in recs:
            parent = r['parentCol']
            if not parent or parent not in availableIds:
                parentKey = None
            else:
                parentKey = parent
            mapParent.setdefault(parentKey, []).append(r)
        
        def safeSortKey(r):
            _num_re = re.compile(ur'(\d+)', re.UNICODE)
            s = r.get(sortKey, u'') if sortKey in r else r.get(childCol, u'')
            if s is None:
                s = u''

            s = unicode(s)
            parts = _num_re.split(s) 
            key = []
            for p in parts:
                if p == u'':
                    continue
                if _num_re.match(p):
                    try:
                        key.append(int(p))
                    except Exception:
                        key.append(p.lower())
                else:
                    key.append(p.lower())
            return tuple(key)
        
        for k in mapParent.keys():
            mapParent[k].sort(key=safeSortKey)

        treeModel = QtGui.QStandardItemModel()
        treeModel.setHorizontalHeaderLabels([u''])
        items = {}

        def makeLabel(r):
            return u' - '.join([p for k, p in r.items() if k not in ('parentCol', 'childCol', 'id') and p])

        def appendChildren(parentCode, parentContainer):
            for child in mapParent.get(parentCode, []):
                label = makeLabel(child)
                item = QtGui.QStandardItem(label)
                item.setData(child['id'], Qt.UserRole)
                items[child['id']] = item
                if isinstance(parentContainer, QtGui.QStandardItemModel):
                    parentContainer.appendRow(item)
                else:
                    parentContainer.appendRow(item)
                appendChildren(child['childCol'], item)

        appendChildren(None, treeModel)

        self._treeModel = treeModel
        self._treeView = QtGui.QTreeView()
        self._treeView.setModel(self._treeModel)
        self._treeView.setHeaderHidden(True)
        self._treeView.setRootIsDecorated(True)
        self._treeView.expandAll()
        self._treeView.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self._treeView.doubleClicked.connect(self._onTreeDoubleClicked)
        self._treePopup = TreePopupFrame(self, self._treeView)
        self._treeItems = items
        self._model._treeItems = items
        self._model._treeModel = treeModel
        
        
    def getRootTextForId(self, idVal):
        item = self._treeItems.get(idVal, None)

        if item is None:
            item = self._findItemById(idVal)
        if item is None:
            return None

        while item.parent() is not None:
            item = item.parent()

        return forceString(item.text())
    
    
    def _findItemById(self, idVal):
        if not getattr(self, '_treeModel', None):
            return None

        def findRec(parent):
            for r in range(parent.rowCount()):
                it = parent.child(r) if parent is not None else self._treeModel.item(r)
                try:
                    if it.data(Qt.UserRole) == idVal:
                        return it
                except Exception:
                    pass
                found = findRec(it)
                if found:
                    return found
            return None

        for r in range(self._treeModel.rowCount()):
            top = self._treeModel.item(r)
            res = findRec(top)
            if res:
                return res
            if top.data(Qt.UserRole) == idVal:
                return top
        return None


    def _onTreeDoubleClicked(self, index):
        if not index.isValid():
            return
        if hasattr(self, '_treeModel'):
            item = self._treeModel.itemFromIndex(index)
        if item is None:
            return
        rid = item.data(Qt.UserRole)
        if rid:
            CTableSearchComboBox.setValue(self, forceRef(rid))
        if hasattr(self, '_treePopup') and self._treePopup:
            self._treePopup.hide()


    def showPopup(self):
        if self.isReadOnly():
            return
        if hasattr(self, '_treePopup') and hasattr(self, '_treeModel') and self._treePopup and self._treeModel:
            view = self._treeView
            frame = self._treePopup
            curVal = None
            try:
                curVal = self.getValue()
            except Exception:
                curVal = None
            if curVal is not None:
                def findItemById(model, id_val):
                    for r in range(model.rowCount()):
                        it = model.item(r)
                        res = findItemRec(it, id_val)
                        if res:
                            return res
                    return None
                def findItemRec(item, id_val):
                    if item.data(Qt.UserRole) == id_val:
                        return item
                    for i in range(item.rowCount()):
                        found = findItemRec(item.child(i), id_val)
                        if found:
                            return found
                    return None

                foundItem = findItemById(self._treeModel, curVal)
                if foundItem:
                    idx = self._treeModel.indexFromItem(foundItem)
                    view.setCurrentIndex(idx)
                    view.scrollTo(idx)

            sizeHint = view.sizeHint()
            preferWidth = max(self.preferredWidth or 200, sizeHint.width())
            adjustPopupToWidget(self, frame, True, preferWidth*2, sizeHint.height()+50)
            frame.show()
            view.setFocus()
            return
        #CTableSearchComboBox.showPopup(self)

    def hidePopup(self):
        if hasattr(self, '_treePopup') and self._treePopup:
            self._treePopup.hide()
        else:
            try:
                CTableSearchComboBox.hidePopup(self)
            except Exception:
                pass
            
            
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        opt = QtGui.QStyleOptionComboBox()
        self.initStyleOption(opt)
        style = QtGui.QApplication.style()
        style.drawComplexControl(QtGui.QStyle.CC_ComboBox, opt, painter, self)
        textRect = style.subControlRect(QtGui.QStyle.CC_ComboBox, opt,
                                        QtGui.QStyle.SC_ComboBoxEditField, self)
        fm = painter.fontMetrics()
        text = self.currentText()
        elided = fm.elidedText(text, Qt.ElideLeft, textRect.width())
        penColor = opt.palette.color(QtGui.QPalette.ButtonText)
        painter.setPen(penColor)
        padding = 0
        painter.drawText(textRect.adjusted(padding, 0, -padding, 0),
                         Qt.AlignVCenter | Qt.AlignLeft,
                         elided)
        painter.end()


class TreePopupFrame(QtGui.QFrame):
    def __init__(self, cmb, treeView):
        QtGui.QFrame.__init__(self, cmb)
        self.setFrameShape(QtGui.QFrame.StyledPanel)
        self.setAttribute(Qt.WA_WindowPropagation)
        self.setWindowFlags(Qt.Popup)
        self._cmb = cmb
        layout = QtGui.QVBoxLayout(self)
        layoutFilter = QtGui.QHBoxLayout()
        self.lblCode = QtGui.QLabel(u'Поиск')
        self.edtCode = QtGui.QLineEdit()
        layoutFilter.addWidget(self.lblCode)
        layoutFilter.addWidget(self.edtCode)
        layout.addLayout(layoutFilter)
        layout.addWidget(treeView)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        self.edtCode.textChanged.connect(self._onCodeChanged)

    def _onCodeChanged(self, text):
        txt = unicode(text).lower().strip()
        model = self._cmb._treeModel
        view = self._cmb._treeView
        
        def matchLabel(item):
            return txt in unicode(item.text()).lower()

        def filterItem(item):
            if matchLabel(item):
                return True
            for i in range(item.rowCount()):
                if filterItem(item.child(i)):
                    return True
            return False

        def applyFilter(item):
            visible = filterItem(item)
            view.setRowHidden(item.row(), item.parent().index() if item.parent() else QModelIndex(), not visible)
            for i in range(item.rowCount()):
                applyFilter(item.child(i))

        if txt == u'':
            for r in range(model.rowCount()):
                item = model.item(r)
                view.setRowHidden(r, QModelIndex(), False)
                for i in range(item.rowCount()):
                    view.setRowHidden(i, model.indexFromItem(item), False)
            return

        for r in range(model.rowCount()):
            applyFilter(model.item(r))

    def eventFilter(self, obj, event):
        return QtGui.QFrame.eventFilter(self, obj, event)