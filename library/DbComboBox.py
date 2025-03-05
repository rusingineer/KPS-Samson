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

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QAbstractListModel, QDateTime, QModelIndex, QSize, QString, QVariant

from library.DbEntityCache import CDbEntityCache
from library.Utils         import forceInt, forceString


### CHECKSUM TABLE table EXTENDED

def getDBCheckSum(tableName, fieldName,  filter):
    return QtGui.qApp.db.dbChecksum(tableName, fieldName, filter)
#    if filter:
#        wherePart = 'WHERE '+filter
#    else:
#        wherePart = ''
#    query = QtGui.qApp.db.query('SELECT SUM(CRC32(CONCAT_WS(CHAR(127), id, %s))) FROM %s %s' % (fieldName, tableName, wherePart))
#    if query.next():
#        record = query.record()
#        return record.value(0).toInt()[0]
#    else:
#        return None


class CDbData(object):
    def __init__(self, idFieldName=None, idConvertFunc=forceInt):
        self.idFieldName = idFieldName
        self.idConvertFunc = idConvertFunc
        self.idList = []
        self.strList = []
        self.checkSum = None
        self.timestamp = QDateTime()
        self.minRealIndex = 0
        self.orderedByName = True


    def select(self, tableName, nameField, filter, addNone, noneTextIn, order):
        db = QtGui.qApp.db
        table = db.table(tableName)
        if self.idFieldName:
            table.setIdFieldName(self.idFieldName)
        self.idList=[]
        self.strList=[]
        if addNone:
            noneTextList = noneTextIn.split(u',') # Это - какая-то лажа...
            cnt = 0
            noneTextListS = noneTextList[::-1]
            for noneText in noneTextListS:
                if cnt == 0:
                    self.idList.append(None)
                else:
                    self.idList.append(cnt)
                self.strList.append(QVariant(noneText))
                cnt -= 1
        self.minRealIndex = len(self.idList)
        order = order if order else nameField
        self.orderedByName = order == nameField
        stmt = db.selectStmt(table, [table.idField(), nameField], filter, order)
        query = db.query(stmt)
        while query.next():
            record = query.record()
            self.idList.append(self.idConvertFunc(record.value(0))) # ещё какое-то хакерство...
            self.strList.append(record.value(1))



class CDbDataCache(CDbEntityCache):
    mapKeyToData = {}

    @classmethod
    def getData(cls, tableName, nameField, filter, addNone, noneText, order, idFieldName=None, idConvertFunc=forceInt):
        key = (tableName, nameField, filter, addNone, noneText, idFieldName, idConvertFunc)
        result = cls.mapKeyToData.get(key, None)
        now = QDateTime.currentDateTime()
        if not result or result.timestamp.secsTo(now) > 60 : ## magic
            checkSum = cls.getDBCheckSumFunc()(tableName, nameField, filter)
            if not result or result.checkSum != checkSum:
                result = CDbData(idFieldName, idConvertFunc)
                result.select(tableName, nameField, filter, addNone, noneText, order)
                result.checkSum = checkSum
                cls.connect()
                cls.mapKeyToData[key] = result
            result.timestamp = now
        return result


    @classmethod
    def getDBCheckSumFunc(cls):
        return getDBCheckSum


    @classmethod
    def purge(cls):
        cls.mapKeyToData.clear()



class CAbstractDbModel(QAbstractListModel):
    def __init__(self, parent):
        QAbstractListModel.__init__(self, parent)
        self.dbdata = None
        self.addNone = False

        if parent!=None:
            h = parent.fontMetrics().height()
        else:
            h = 14
        self.sizeHint = QVariant(QSize(h,h))
        self.readOnly = False


    def setReadOnly(self, value=False):
        self.readOnly = value


    def isReadOnly(self):
        return self.readOnly


    def flags(self, index=QModelIndex()):
        result = QAbstractListModel.flags(self, index)
        if self.readOnly:
            result = Qt.ItemIsEnabled
        return result


    def columnCount(self, index=None):
        return 1


    def dbDataAvailable(self):
        if not self.dbdata:
            self.initDbData()
        return bool(self.dbdata)


    def rowCount(self, index=None):
        if self.dbDataAvailable():
            return len(self.dbdata.idList)
        else:
            return 0


    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        elif role == Qt.DisplayRole or role == Qt.EditRole:
            row = index.row()
            if self.dbDataAvailable() and 0 <= row < len(self.dbdata.strList):
                return QVariant(self.dbdata.strList[row])
        elif role == Qt.SizeHintRole:
            return self.sizeHint
        return QVariant()


    def searchId(self, itemId):
        if self.dbDataAvailable():
            if itemId in self.dbdata.idList:
                return self.dbdata.idList.index(itemId)
        return -1


    def getNameById(self, itemId):
        row = self.searchId(itemId)
        if row>=0:
            return self.dbdata.strList[row]
        else:
            return ''

    def getIdByName(self, name):
        try:
            rowIndex = self.dbdata.strList.index(name)
            return self.dbdata.idList[rowIndex]
        except ValueError:
            pass
        return 0



    def getId(self, index):
        if self.dbdata and 0<=index<len(self.dbdata.idList):
            return self.dbdata.idList[index]
        else:
            return None


    def getName(self, index):
        if self.dbdata and 0<=index<len(self.dbdata.strList):
            return self.dbdata.strList[index]
        else:
            return ''


    def keyboardSearch(self, search):
        if self.dbDataAvailable():
            if self.dbdata.orderedByName:
                l = 0 if self.addNone else self.dbdata.minRealIndex
                h = len(self.dbdata.strList)-1
                while l <= h:
                    i = (l+h)/2
                    c = cmp(forceString(self.dbdata.strList[i]).upper(), search)
                    if c<0:
                        l = i+1
                    elif c>0:
                        h = i-1
                    else:
                        return i
                return l
            else:
                for i in xrange(self.dbdata.minRealIndex, len(self.dbdata.strList)):
                    if forceString(self.dbdata.strList[i]).upper().startswith(search):
                        return i
        return -1

    def update(self):
        pass


class CDbModel(CAbstractDbModel):
    def __init__(self, parent, idFieldName='id', idConvertFunc=forceInt):
        CAbstractDbModel.__init__(self, parent)
        self.tableName = ''
        self.nameField = 'name'
        self.filter = ''
        self.addNone = True
        self.noneText = ''
        self.order = ''
        self.idFieldName = idFieldName
        self.idConvertFunc = idConvertFunc
        self._dataCache = CDbDataCache

        if parent!=None:
            h = parent.fontMetrics().height()
        else:
            h = 14
        self.sizeHint = QVariant(QSize(h,h))


    def setDataCache(self, dataCache):
        self._dataCache = dataCache


    def setTable(self, tableName):
        if self.tableName != tableName:
            self.tableName = tableName
            if self.dbdata is not None:
                self.dbdata = None
                self.reset()


    def setNameField(self, nameField):
        if self.nameField != nameField:
            self.nameField = nameField
            if self.dbdata is not None:
                self.dbdata = None
                self.reset()


    def setFilter(self, filter):
        if self.filter != filter:
            self.filter = filter
            if self.dbdata is not None:
                self.dbdata = None
                self.reset()


    def setAddNone(self, addNone, noneText=''):
        if self.addNone != addNone or self.noneText != noneText:
            self.addNone = addNone
            self.noneText = noneText
            if self.dbdata is not None:
                self.dbdata = None
                self.reset()


    def setOrder(self, order):
        if self.order != order:
            self.order = order
            if self.dbdata is not None:
                self.dbdata = None
                self.reset()


    def initDbData(self):
#        self.dbdata = CDbData()
#        self.dbdata.select(self.tableName, self.nameField, self.filter, self.addNone, self.noneText)
        if self.tableName and self.nameField:
            self.dbdata = self._getDataCache().getData(self.tableName, self.nameField, self.filter, self.addNone, self.noneText, self.order, self.idFieldName, self.idConvertFunc)


    def update(self):
        oldData = self.dbdata
        self.dbdata = self._getDataCache().getData(self.tableName, self.nameField, self.filter, self.addNone, self.noneText, self.order, self.idFieldName, self.idConvertFunc)
        if oldData != self.dbdata:
            self.reset()


    def _getDataCache(self):
        return self._dataCache


##class CDbPopupView(QtGui.QTableView):
class CDbPopupView(QtGui.QListView):
    def __init__(self, parent):
        QtGui.QListView.__init__(self, parent)


class CAbstractDbComboBox(QtGui.QComboBox):
    def __init__(self, parent):
        QtGui.QComboBox.__init__(self, parent)
        self.__searchString = ''
        self.setMinimumContentsLength(20)
        self.__popupView = CDbPopupView(self)
        self.setView(self.__popupView)
        self.readOnly = False


    def setReadOnly(self, value=False):
        self.readOnly = value


    def isReadOnly(self):
        return self.readOnly


    def setModel(self, model):
        self.__model = model
        QtGui.QComboBox.setModel(self, model)


    def showPopup(self):
        if not self.isReadOnly():
            self.__searchString = ''
            QtGui.QComboBox.showPopup(self)

        view = self.view()
        viewFrame = view.parent()
        size = view.sizeHint()
        pos = self.rect().bottomLeft()
        pos = self.mapToGlobal(pos)
        screen = QtGui.QApplication.desktop().availableGeometry(pos)
        pos.setX(max(min(pos.x(), screen.right() - size.width()*2), screen.left()))
        pos.setY(max(min(pos.y(), screen.bottom() - size.height()*2), screen.top()))
        size.setWidth(size.width()*2)
        viewFrame.move(pos)
        viewFrame.resize(size)


    def focusInEvent(self, event):
        self.__searchString = ''
        QtGui.QComboBox.focusInEvent(self, event)


    def keyPressEvent(self, event):
        if self.model().isReadOnly(): # Это - ошибка! в RO комбо-боксах мы не должны сюда попадать!
            event.accept()
        else:
            key = event.key()
    #        text = unicode(event.text())
            if key == Qt.Key_Escape:
                event.ignore()
    #            QtGui.QComboBox.keyPressEvent(self, event)
            elif key in (Qt.Key_Return, Qt.Key_Enter):
                event.ignore()
    #            QtGui.QComboBox.keyPressEvent(self, event)
            if key in(Qt.Key_Delete, Qt.Key_Clear):
                self.__searchString = ''
                self.setCurrentIndex(0)
                event.accept()
            elif key == Qt.Key_Backspace : # BS
                self.__searchString = self.__searchString[:-1]
                self.lookup()
                event.accept()
            elif key == Qt.Key_Space:
                QtGui.QComboBox.keyPressEvent(self, event)
            elif not event.text().isEmpty():
                char = event.text().at(0)
                if char.isPrint():
                    self.__searchString = self.__searchString + unicode(QString(char)).upper()
                    self.lookup()
                    event.accept()
                else:
                    QtGui.QComboBox.keyPressEvent(self, event)
            else:
                QtGui.QComboBox.keyPressEvent(self, event)


    def lookup(self):
        i = self.__model.keyboardSearch(self.__searchString)
        if i>=0 and i != self.currentIndex():
            self.setCurrentIndex(i)


    def sizeHint(self):
        return QSize(20, 20)


    def setValue(self, itemId):
        rowIndex = max(self.__model.searchId(itemId), 0)
        self.setCurrentIndex(rowIndex)


    def value(self):
        rowIndex = self.currentIndex()
        return self.__model.getId(rowIndex)


    def setText(self, name):
        rowIndex = self.__model.keyboardSearch(name)
        self.setCurrentIndex(rowIndex)


    def text(self):
        rowIndex = self.currentIndex()
        return forceString(self.__model.getName(rowIndex))


    def addItem(self, item):
        pass


    def updateModel(self):
        itemId = self.value()
        self.__model.update()
        self.setValue(itemId)


class CDbComboBox(CAbstractDbComboBox):
    def __init__(self, parent, idFieldName='id', idConvertFunc=forceInt):
        CAbstractDbComboBox.__init__(self, parent)
        self.setModel(CDbModel(self, idFieldName, idConvertFunc))


    def setTable(self, tableName, nameField=None, addNone=None, order=''):
        model = self.model()
        if nameField is not None:
            model.setNameField(nameField)
        if addNone is not None:
            model.setAddNone(addNone)
        model.setOrder(order)
        model.setTable(tableName)


    def setNameField(self, nameField):
        self.model().setNameField(nameField)


    def setAddNone(self, addNone,  noneText=''):
        self.model().setAddNone(addNone, noneText)


    def setFilter(self, filter):
        self.model().setFilter(filter)


    def setOrder(self, order):
        self.model().setOrder(order)

    def filter(self):
        return self.model().filter


