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

from random import randint
from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import Qt, QAbstractTableModel, QDateTime, QModelIndex, QString, QVariant

from library.DbEntityCache import CDbEntityCache
from library.SortFilterProxyTableModel import CSortFilterProxyTableModel
from library.adjustPopup import adjustPopupToWidget


def getRBCheckSum(tableName):
    return QtGui.qApp.db.rbChecksum(tableName)


class CAbstractRBModelData(object):
    def __init__(self):
        self.buff = []
        self.maxCodeLen = 0
        self.mapIdToIndex = {}

    def addItem(self, id, code, name):
        self.mapIdToIndex[id] = len(self.buff)
        self.buff.append((id, code, name))
        self.maxCodeLen = max(self.maxCodeLen, len(code))

    def getCount(self):
        return len(self.buff)

    def getId(self, index):
        if index < 0:
            return None
        return self.buff[index][0]

    def getCode(self, index):
        if index < 0:
            return None
        return self.buff[index][1]

    def getName(self, index):
        return self.buff[index][2]

    def getIndexById(self, id):
        result = self.mapIdToIndex.get(id, -1)
        if result < 0 and not id:
            result = self.mapIdToIndex.get(None, -1)
        return result

    def getIndexByCode(self, code):
        for i, item in enumerate(self.buff):
            if item[1] == code:
                return i
        return -1

    def getIndexByName(self, name):
        for i, item in enumerate(self.buff):
            if item[2] == name:
                return i
        return -1

    def getIndexByCodeName(self, code, name):
        for i, item in enumerate(self.buff):
            if item[1] == code and item[2] == name:
                return i
        return -1

    def getNameById(self, id):
        index = self.getIndexById(id)
        if index >= 0:
            return self.getName(index)
        return '{' + str(id) + '}'

    def getCodeById(self, id):
        index = self.getIndexById(id)
        if index >= 0:
            return self.getCode(index)
        return '{' + str(id) + '}'

    def getIdByCode(self, code):
        index = self.getIndexByCode(code)
        return self.getId(index)

    def getString(self, index, showFields):
        if showFields == 0:
            return self.getCode(index)
        elif showFields == 1:
            return self.getName(index)
        elif showFields == 2:
            return '%-*s | %s' % (self.maxCodeLen, self.getCode(index), self.getName(index))
        elif self._tableName == 'rbTest':
            return '%-*s | %s' % (self.maxCodeLen, self.getCode(index), self.getName(index))
        else:
            return 'bad field %s' % showFields

    def getStringById(self, id, showFields):
        index = self.getIndexById(id)
        if index >= 0:
            return self.getString(index, showFields)
        return '{' + str(id) + '}'


class CRBModelData(CAbstractRBModelData):
    """class for store data of ref book"""

    def __init__(self, tableName, addNone, filter, order, specialValues):
        CAbstractRBModelData.__init__(self)
        self._tableName = tableName
        self._addNone = addNone
        self._filter = filter
        self._order = order
        self._checkSum = None
        self._timestamp = None
        self._specialValues = specialValues
        self._notLoaded = True

    def getCount(self):
        if self._notLoaded:
            self.load()
        return len(self.buff)

    def getId(self, index):
        if self._notLoaded:
            self.load()
        return CAbstractRBModelData.getId(self, index)

    def getCode(self, index):
        if self._notLoaded:
            self.load()
        return CAbstractRBModelData.getCode(self, index)

    def getName(self, index):
        if self._notLoaded:
            self.load()
        return CAbstractRBModelData.getName(self, index)

    def getIndexById(self, id):
        if self._notLoaded:
            self.load()
        return CAbstractRBModelData.getIndexById(self, id)

    def getIndexByCode(self, code):
        if self._notLoaded:
            self.load()
        return CAbstractRBModelData.getIndexByCode(self, code)

    def getIndexByCodeName(self, code, name):
        if self._notLoaded:
            self.load()
        return CAbstractRBModelData.getIndexByCodeName(self, code, name)

    def getIndexByName(self, name):
        if self._notLoaded:
            self.load()
        return CAbstractRBModelData.getIndexByName(self, name)

    def getNameById(self, id):
        if self._notLoaded:
            self.load()
        return CAbstractRBModelData.getNameById(self, id)

    def getCodeById(self, id):
        if self._notLoaded:
            self.load()
        return CAbstractRBModelData.getCodeById(self, id)

    def getString(self, index, showFields):
        if self._notLoaded:
            self.load()
        return CAbstractRBModelData.getString(self, index, showFields)

    def getStringById(self, id, showFields):
        if self._notLoaded:
            self.load()
        return CAbstractRBModelData.getStringById(self, id, showFields)

    def load(self):
        if self._specialValues:
            for fakeId, fakeCode, name in self._specialValues:
                self.addItem(fakeId, fakeCode, name)
        if self._addNone:
            self.addItem(None, '0', u'не задано')
        db = QtGui.qApp.db
        where = (' WHERE ' + self._filter) if self._filter else ''
        # добавил cast(code as signed) для корректной сортировки
        order = ' ORDER BY ' + (self._order if self._order else 'cast(code as signed), code, name')
        query = db.query('SELECT id, code, name FROM ' + self._tableName + where + order)
        value = query.value
        while query.next():
            id = value(0).toInt()[0]
            code = value(1).toString()
            name = value(2).toString()
            self.addItem(id, code, name)
        self._timestamp = QDateTime.currentDateTime()
        self._checkSum = getRBCheckSum(self._tableName)
        self._notLoaded = False

    def isObsolete(self):
        now = QDateTime.currentDateTime()
        if self._timestamp and self._timestamp.secsTo(now) > randint(300, 600):  ## magic
            checkSum = getRBCheckSum(self._tableName)
            if self._checkSum == checkSum:
                self._timestamp = now
                return False
            return True
        else:
            return False

    def isLoaded(self):
        return not self._notLoaded


class CRBTestModelData(CRBModelData):

    def addItem(self, id, code, name, fedCode=None):
        self.mapIdToIndex[id] = len(self.buff)
        self.buff.append((id, code, name, fedCode))
        self.maxCodeLen = max(self.maxCodeLen, len(code))

    def load(self):
        if self._specialValues:
            for fakeId, fakeCode, name in self._specialValues:
                self.addItem(fakeId, fakeCode, name)
        if self._addNone:
            self.addItem(None, '0', u'не задано')
        db = QtGui.qApp.db
        where = (' WHERE ' + self._filter) if self._filter else ''
        # добавил cast(code as signed) для корректной сортировки
        order = ' ORDER BY ' + (self._order if self._order else 'cast(code as signed), code, name')
        query = db.query('SELECT id, code, name, federalCode FROM ' + self._tableName + where + order)
        value = query.value
        while query.next():
            id = value(0).toInt()[0]
            code = value(1).toString()
            name = value(2).toString()
            fedCode = value(3).toString() if value(3).toString() else None
            self.addItem(id, code, name, fedCode)
        self._timestamp = QDateTime.currentDateTime()
        self._checkSum = getRBCheckSum(self._tableName)
        self._notLoaded = False

    def getFederalCode(self, index):
        if self._notLoaded:
            self.load()
        if index < 0:
            return None
        return self.buff[index][3]

    def getString(self, index, showFields):
        if showFields == 0:
            return self.getCode(index)
        elif showFields == 1:
            return self.getName(index)
        elif showFields == 2:
            return '%-*s | %s' % (self.maxCodeLen, self.getCode(index), self.getName(index))
        elif showFields == 3:
            return self.getFederalCode(index)
        else:
            return 'bad field %s' % showFields


class CRBModelDataCache(CDbEntityCache):
    mapTableToData = {}

    @classmethod
    def getData(cls, tableName, addNone=True, filter='', order=None, specialValues=None, needCache=True, force=False):
        strTableName = unicode(tableName)
        if isinstance(specialValues, list):
            specialValues = tuple(specialValues)
        key = (strTableName, addNone, filter, order, specialValues)
        result = cls.mapTableToData.get(key, None)
        if not result or force or result.isObsolete():
            if strTableName == 'rbTest':
                result = CRBTestModelData(strTableName, addNone, filter, order, specialValues)
            else:
                result = CRBModelData(strTableName, addNone, filter, order, specialValues)
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


class CRBModel(QAbstractTableModel):
    def __init__(self, parent):
        QAbstractTableModel.__init__(self, parent)
        self.d = None
        self.resetRequired = False
        self.readOnly = False

    def setReadOnly(self, value=False):
        self.readOnly = value

    def isReadOnly(self):
        return self.readOnly

    def flags(self, index=QModelIndex()):
        result = QAbstractTableModel.flags(self, index)
        if self.readOnly:
            result = Qt.ItemIsEnabled
        return result

    def setTable(self, tableName, addNone=True, filter='', order=None, specialValues=None, needCache=True, force=False):
        d = self.d
        if d and d.isLoaded() or self.resetRequired:
            if hasattr(self, 'beginResetModel'):
                self.beginResetModel()
            self.d = CRBModelDataCache.getData(tableName, addNone, filter, order, specialValues, needCache, force)
            if hasattr(self, 'endResetModel'):
                self.endResetModel()
            else:
                self.reset()
        else:
            self.d = CRBModelDataCache.getData(tableName, addNone, filter, order, specialValues, needCache, force)

    def columnCount(self, index=None):
        return 3

    def rowCount(self, index=None):
        if self.d:
            return self.d.getCount()
        else:
            self.resetRequired = True
            return 0

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                if section == 0:
                    return QVariant(u'Код')
                elif section == 1:
                    return QVariant(u'Наименование')
        return QVariant()

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        elif role == Qt.DisplayRole or role == Qt.EditRole:
            row = index.row()
            if row < self.d.getCount():
                return QVariant(self.d.getString(row, index.column()))
        return QVariant()

    #    def codes(self):
    #        return [forceString(self.data(self.index(i, 0), Qt.DisplayRole)) for i in xrange(self.rowCount())]

    #    def names(self):
    #        return [forceString(self.data(self.index(i, 1), Qt.DisplayRole)) for i in xrange(self.rowCount())]

    def searchId(self, itemId):
        return self.d.getIndexById(itemId)

    #    def searchCode(self, code):
    #        return self.d.getIndexByCode(code)

    def searchName(self, name):
        return self.d.getIndexByName(name)

    def searchNameEx(self, name):
        s = unicode(name).upper()
        for i in xrange(self.d.getCount()):
            if s in unicode(self.d.getName(i)).upper():
                return i
        return -1

    def getId(self, index):
        return self.d.getId(index)

    def getName(self, index):
        return self.d.getName(index)

    def getCode(self, index):
        return self.d.getCode(index)
    
    def getFederalCode(self, index):
        return self.d.getFederalCode(index)

    def getRecordByRow(self, row):
        # для CSortFilterProxyTableModel
        record = QtSql.QSqlRecord()
        record.append(QtSql.QSqlField('id', QVariant.Int))
        record.append(QtSql.QSqlField('code', QVariant.String))
        record.append(QtSql.QSqlField('name', QVariant.String))
        record.setValue('id', self.getId(row))
        record.setValue('name', self.getName(row))
        record.setValue('code', self.getCode(row))
        return record

    def cols(self):
        # для CSortFilterProxyTableModel
        from library.TableModel import CCol
        return [
            CCol('', ['code'], 0, 'l'),
            CCol('', ['name'], 0, 'l'),
        ]

    def searchCode(self, code):
        code = unicode(code).upper()
        n = self.d.getCount()
        for i in xrange(n):
            if unicode(self.d.getCode(i)).upper().startswith(code):
                return i
        for i in xrange(n):
            if unicode(self.d.getName(i)).upper().startswith(code):
                return i
        return -1

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
            itemCode = unicode(self.d.getCode(i)).upper()
            commonLen = maxCommonLen(itemCode, code)
            if commonLen == codeLen == len(itemCode):
                return i, code
            if commonLen > maxLen:
                maxLen, maxLenAt = commonLen, i
        for i in xrange(n):
            itemName = unicode(self.d.getName(i)).upper()
            commonLen = maxCommonLen(itemName, code)
            if commonLen == codeLen == len(itemName):
                return i, code
            if commonLen > maxLen:
                maxLen, maxLenAt = commonLen, i
        return maxLenAt, code[:maxLen]


class CRBTestModel(CRBModel):

    def columnCount(self, index=None):
        return 4

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                if section == 0:
                    return QVariant(u'Код')
                elif section == 1:
                    return QVariant(u'Наименование')
                elif section == 3:
                    return QVariant(u'Федеральный код')
        return QVariant()

    def cols(self):
        # для CSortFilterProxyTableModel
        from library.TableModel import CCol
        return [
            CCol('', ['code'], 0, 'l'),
            CCol('', ['name'], 0, 'l'),
            CCol('', ['federalCode'], 0, 'l'),
        ]

    def getRecordByRow(self, row):
        # для CSortFilterProxyTableModel
        record = QtSql.QSqlRecord()
        record.append(QtSql.QSqlField('id', QVariant.Int))
        record.append(QtSql.QSqlField('code', QVariant.String))
        record.append(QtSql.QSqlField('name', QVariant.String))
        record.append(QtSql.QSqlField('federalCode', QVariant.String))
        record.setValue('id', self.getId(row))
        record.setValue('name', self.getName(row))
        record.setValue('code', self.getCode(row))
        record.setValue('federalCode', self.getFederalCode(row))
        return record


class CRBLikeEnumModel(CRBModel):
    def __init__(self, parent):
        CRBModel.__init__(self, parent)
        self.d = None

    def setValues(self, values):
        self.d = CAbstractRBModelData()
        for i, val in enumerate(values):
            id = i
            code = str(i)
            name = val
            self.d.addItem(id, code, name)


class CRBSelectionModel(QtGui.QItemSelectionModel):
    def select(self, indexOrSelection, command):
        if isinstance(indexOrSelection, QModelIndex):
            index = indexOrSelection
            ##            print 'select-2', index.column()
            if index.column() > 1:
                correctIndex = self.model().index(index.row(), 1)
            else:
                correctIndex = index
            if command & QtGui.QItemSelectionModel.Select and not (command & QtGui.QItemSelectionModel.Current):
                self.setCurrentIndex(correctIndex,
                                     QtGui.QItemSelectionModel.Clear | QtGui.QItemSelectionModel.Select | QtGui.QItemSelectionModel.Current)
            else:
                QtGui.QItemSelectionModel.select(self, correctIndex, command)

        else:
            QtGui.QItemSelectionModel.select(self, indexOrSelection, command)


#        index = None
#        if isinstance(indexOrSelection, QtGui.QItemSelection):
#            QtGui.QItemSelectionModel.select(self, indexOrSelection, command)
#            indexes = indexOrSelection.indexes()
#            if indexes:
#                index = indexes[0]
#        elif isinstance(indexOrSelection, QModelIndex):
#            index = indexOrSelection
#        if index:
#            print 'select', index.column()
#            if index.column() > 1:
#                correctIndex = self.model().index(index.row(), 1)
#            else:
#                correctIndex = index
#            QtGui.QItemSelectionModel.select(self, correctIndex, command)
#        else:
#            QtGui.QItemSelectionModel.select(self, indexOrSelection, command)
#        QtGui.QItemSelectionModel.select(self, index, command)


class CRBPopupView(QtGui.QTableView):
    def __init__(self, parent):
        QtGui.QTableView.__init__(self, parent)
## does not work        self.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
## does not work        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
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


class CRBComboBox(QtGui.QComboBox):
    u"""ComboBox, в котором отображается содержимое таблицы - справочника"""
    showCode = 0
    showName = 1
    showCodeAndName = 2
    showNameAndCode = 2

    def __init__(self, parent):
        QtGui.QComboBox.__init__(self, parent)
        self._searchString = ''
        self.showFields = CRBComboBox.showName
        self._tableName = ''
        self._addNone   = True
        self._needCache = True
        self._filier    = ''
        self._order     = ''
        self._specialValues = None
        self.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToMinimumContentsLength)
        self.preferredWidth = None
        self.popupView = CRBPopupView(self)
        self.setModelColumn(self.showFields)
        self.setView(self.popupView)
        self.setModel(CRBModel(self))
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


    def setTable(self, tableName, addNone=True, filter='', order=None, specialValues=None, needCache=True, force=False):
        self._tableName = tableName
        self._addNone   = addNone
        self._filier    = filter
        self._order     = order
        self._needCache = needCache
        self._specialValues = specialValues
        self._model.setTable(tableName, addNone, filter, order, specialValues, needCache, force=force)


    def setSpecialValues(self, specialValues):
        if self._specialValues != specialValues:
            self._specialValues = specialValues
            self.reloadData()


    def addFilterAnd(self, filter): # WTF?
        if self._filier:
            self._filier = ' AND '.join([self._filier, filter])
        else:
            self._filier = filter
        self.reloadData()


    def setFilter(self, filter='', order=None):
        self._filier    = filter
        self._order     = order
        self.setTable(self._tableName, self._addNone, filter, order, self._specialValues, self._needCache)


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


    def setShowFields(self, showFields):
        self.showFields = showFields
        self.setModelColumn(self.showFields)


    def setModel(self, model):
        self._model = model
        self.proxyModel = CSortFilterProxyTableModel(self, self._model)
        QtGui.QComboBox.setModel(self, self.proxyModel)
        self._selectionModel = CRBSelectionModel(self.proxyModel)
        self.popupView.setSelectionModel(self._selectionModel)
        self.popupView.hideColumn(2)


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


    def setCode(self, code):
        u"""поле code записи"""
        row = self._model.searchCode(code)
        if row == -1:
            self.setCurrentIndex(-1)
        else:
            sourceIndex = self._model.index(row, 0)
            proxyIndex = self.proxyModel.mapFromSource(sourceIndex)
            self.setCurrentIndex(proxyIndex.row())


    def code(self):
        u"""поле code записи"""
        row = self.currentIndex()
        rowIndex = self.proxyModel.index(row, 0)
        sourceIndex = self.proxyModel.mapToSource(rowIndex)
        return self._model.getCode(sourceIndex.row())


    def name(self):
        u"""поле name записи"""
        row = self.currentIndex()
        rowIndex = self.proxyModel.index(row, 0)
        sourceIndex = self.proxyModel.mapToSource(rowIndex)
        return self._model.getName(sourceIndex.row())


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
                    view.setFixedHeight( view.rowHeight(0)*visibleItems + tblHeaderHeight )
                frame = view.parent()
                sizeHint = view.sizeHint()
                # устанавливаем рекомендуемую ширину по максимальной ширине кода + названия + 1
                #codes, names = self._model.codes(), self._model.names()
                maxWidthCode = max(view.fontMetrics().width(self._model.getCode(i) + ' ') for i in xrange(totalItems))
                preferredWidth = maxWidthCode
                preferredWidth += max(view.fontMetrics().width(self._model.getName(i)+' ') for i in xrange(totalItems))
                preferredWidth *= 1.1 # почему-то ширина не дотягивает
                view.horizontalHeader().setDefaultSectionSize(maxWidthCode+5)
                adjustPopupToWidget(self, frame, True, max(preferredWidth, self.preferredWidth, sizeHint.width()), view.height()+2)
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
                self.lookup(True)
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


    def lookup(self, reset=False):
        i, self._searchString = self._model.searchCodeEx(self._searchString)
        if reset:
            self.setValue(0)
        else:
            if i>=0 and i!=self.currentIndex():
                self.setCurrentIndex(i)


    def eventFilter(self,  obj,  event):
        if self.isReadOnly():
            event.accept()
            return False
        return False


class CRBTestComboBox(CRBComboBox):
    def __init__(self, parent):
        QtGui.QComboBox.__init__(self, parent)
        self._searchString = ''
        self.showFields = CRBComboBox.showName
        self._tableName = ''
        self._addNone   = True
        self._needCache = True
        self._filier    = ''
        self._order     = ''
        self._specialValues = None
        self.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToMinimumContentsLength)
        self.preferredWidth = None
        self.popupView = CRBPopupView(self)
        self.setModelColumn(self.showFields)
        self.setView(self.popupView)
        self.setModel(CRBTestModel(self))
        self.popupView.setFrameShape(QtGui.QFrame.NoFrame)
        self.readOnly = False
        self.installEventFilter(self)

    def federalCode(self):
        u"""поле federalCode записи"""
        row = self.currentIndex()
        rowIndex = self.proxyModel.index(row, 0)
        sourceIndex = self.proxyModel.mapToSource(rowIndex)
        return self._model.getName(sourceIndex.row())
