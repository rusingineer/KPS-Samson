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
import datetime
import re

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, SIGNAL, QAbstractTableModel, QLocale, QModelIndex, QVariant, QString, QDate, QTime, \
    QDateTime, QSize

from library.database import CTableRecordCache
from library.Utils import forceDate, forceDouble, forceInt, forceRef, forceString, nameCase, toVariant, forceStringEx

from library.crbcombobox import CRBModelDataCache, CRBComboBox

__all__ = ( 'CCol',
            'CTextCol',
            'CIntCol',
            'CDoubleCol',
            'CNameCol',
            'CNumCol',
            'CSumCol',
            'CSumDecimalPlaceCol',
            'CDateCol',
            'CTimeCol',
            'CDateTimeCol',
            'CDateTimeFixedCol',
            'CBoolCol',
            'CEnumCol',
            'CDesignationCol',
            'CRefBookCol',
            'CColorCol',
            'CTableModel',
          )


class CCol(object):
    """
      Root of all columns
    """
    alg = { 'l':  QVariant(Qt.AlignLeft    + Qt.AlignVCenter),
            'c':  QVariant(Qt.AlignHCenter + Qt.AlignVCenter),
            'r':  QVariant(Qt.AlignRight   + Qt.AlignVCenter),
            'j':  QVariant(Qt.AlignJustify + Qt.AlignVCenter)
          }

    invalid   = QVariant()

    def __init__(self, title, fields, defaultWidth, alignment, **kwargs):
        assert isinstance(fields, (list, tuple))
        self._title    = QVariant(title)
        self._toolTip  = CCol.invalid
        self._whatsThis = CCol.invalid
        self._fields = fields
        self._defaultWidth = defaultWidth
        self._align  = CCol.alg[alignment]
        self._fieldindexes = []
        self._adopted = False
        self._defaultHidden = kwargs.get('defaultHidden', False)
        self._switchOff = kwargs.get('switchOff', True)


    def switchOff(self):
        return self._switchOff


    @property
    def defaultHidden(self):
        return self._defaultHidden


    def adoptRecord(self, record):
        if record:
            self._fieldindexes = []
            if isinstance(self._fields, (list, tuple)):
                for fieldName in self._fields:
                    fieldIndex = record.indexOf(fieldName)
                    assert fieldIndex>=0
                    self._fieldindexes.append(fieldIndex)
            self._adopted = True


    def extractValuesFromRecord(self, record):
        if not self._adopted:
            self.adoptRecord(record)
        result = []
        if record:
            for i in self._fieldindexes:
                result.append( record.value(i) )
        else:
            for i in self._fieldindexes:
                result.append( QVariant() )
        result.append(record)
        return result


    def setTitle(self, title):
        self._title = toVariant(title)


    def title(self):
        return self._title


    def setToolTip(self, toolTip):
        self._toolTip = toVariant(toolTip)
        return self


    def toolTip(self):
        return self._toolTip


    def setWhatsThis(self, whatsThis):
        self._whatsThis = toVariant(whatsThis)


    def whatsThis(self):
        return self._whatsThis


    def fields(self):
        return self._fields


    def defaultWidth(self):
        return self._defaultWidth


    def alignment(self):
        return self._align


    def format(self, values):
        return values[0]


    def checked(self, values):
        return CCol.invalid


    def getForegroundColor(self, values):
        return CCol.invalid


    def getBackgroundColor(self, values):
        return CCol.invalid


    def getValue(self, values):
        return forceStringEx(values[0])


    def invalidateRecordsCache(self):
        pass


class CTextCol(CCol):
    """
      General text column
    """
    def __init__(self, title, fields, defaultWidth, alignment='l'):
        CCol.__init__(self, title, fields, defaultWidth, alignment)


class CTextListCol(CTextCol):
    """
      Multiple fields as string with separator
    """
    def __init__(self, title, fields, defaultWidth, alignment='l'):
        self._separator = ' '
        CTextCol.__init__(self, title, fields, defaultWidth, alignment)

    def setSeparator(self, separator):
        self._separator = toVariant(separator)

    def separator(self):
        return self._separator

    def format(self, values):
        return self._separator.join([forceString(value) for value in values[:-1]])


class CIntCol(CCol):
    """
      General int column
    """
    def __init__(self, title, fields, defaultWidth, alignment='l'):
        CCol.__init__(self, title, fields, defaultWidth, alignment)

    def format(self, values):
        return toVariant(forceInt(values[0]))

    def getValue(self, values):
        return forceInt(values[0])


class CDoubleCol(CCol):
    """
      General int column
    """
    def __init__(self, title, fields, defaultWidth, alignment='l'):
        CCol.__init__(self, title, fields, defaultWidth, alignment)

    def format(self, values):
        return toVariant(forceDouble(values[0]))

    def getValue(self, values):
        return forceDouble(values[0])


class CNameCol(CTextCol):
    """
      Name column: with appropriate capitalization
    """
    def __init__(self, title, fields, defaultWidth, alignment='l'):
        CTextCol.__init__(self, title, fields, defaultWidth, alignment)

    def format(self, values):
        val = unicode(values[0].toString())
        return QVariant(nameCase(val))

    def getValue(self, values):
        val = unicode(values[0].toString())
        return nameCase(val)


class CNumCol(CCol):
    """
      Numeric column: right aligned
    """
    def __init__(self, title, fields, defaultWidth, alignment='r'):
        CCol.__init__(self, title, fields, defaultWidth, alignment)


class CSumCol(CNumCol):
    """
      Numeric column: right aligned, sum formatted
    """
    locale = QLocale()

    def format(self, values):
        sum = forceDouble(values[0])
        return toVariant(self.locale.toString(sum, 'f', 2))

    def getValue(self, values):
        sum = forceDouble(values[0])
        return self.locale.toString(sum, 'f', 2)


class CSumDecimalPlaceCol(CNumCol):
    """
      Decimal Place
    """
    locale = QLocale()

    def __init__(self, title, fields, defaultWidth, alignment='r', decimals=2):
        CCol.__init__(self, title, fields, defaultWidth, alignment)
        self.decimals = decimals

    def format(self, values):
        sum = forceDouble(values[0])
        return toVariant(self.locale.toString(sum, 'f', self.decimals))

    def getValue(self, values):
        sum = forceDouble(values[0])
        return self.locale.toString(sum, 'f', self.decimals)


class CDateCol(CCol):
    """
      Date column
    """
    def __init__(self, title, fields, defaultWidth, alignment='l', highlightRedDate=True):
        CCol.__init__(self, title, fields, defaultWidth, alignment)
        self.highlightRedDate = highlightRedDate and QtGui.qApp.highlightRedDate()

    def format(self, values):
#        u"""Преобразует дату в строку в формате dd.mm.yy. Это не очень удобно. А если нужно иметь 4 цифры года?"""
#        тогда не нужно тормозить - нужно почитать код...
        val = values[0]
        if val.type() in (QVariant.Date, QVariant.DateTime):
            val = val.toDate()
            return QVariant(val.toString('dd.MM.yyyy'))
        return CCol.invalid

    def getValue(self, values):
        val = values[0]
        if val.type() in (QVariant.Date, QVariant.DateTime):
            return val.toDate()
        return QDate()

    def getForegroundColor(self, values):
        val = values[0]
        date = forceDate(val)
        if self.highlightRedDate and date and QtGui.qApp.calendarInfo.getDayOfWeek(date) in (6, 7):
            return QVariant(QtGui.QColor(255, 0, 0))
        return QVariant()


class CTimeCol(CCol):
    """
      Time column
    """
    def __init__(self, title, fields, defaultWidth, alignment='l'):
        CCol.__init__(self, title, fields, defaultWidth, alignment)

    def format(self, values):
        val = values[0]
        if val.type() in (QVariant.Time, QVariant.DateTime):
            val = val.toTime()
            return QVariant(val.toString('hh:mm:ss'))
        return CCol.invalid

    def getValue(self, values):
        val = values[0]
        if val.type() in (QVariant.Time, QVariant.DateTime):
            return val.toTime()
        return QTime()


class CDateTimeCol(CDateCol):
#    """
#      Date and time column
#    """
    def format(self, values):
        val = values[0]
        if val.type() == QVariant.Date:
            val = val.toDate()
            return QVariant(val.toString('dd.MM.yyyy'))
        elif val.type() == QVariant.DateTime:
            val = val.toDateTime()
            return QVariant(val.toString('dd.MM.yyyy hh:mm:ss'))
        return CCol.invalid

    def getValue(self, values):
        val = values[0]
        if val.type() == QVariant.Date:
            return val.toDate()
        elif val.type() == QVariant.DateTime:
            return val.toDateTime()
        return QDateTime()


class CDateFixedCol(CDateCol):
#    """
#      Date and time column
#    """

    def format(self, values):
        val = values[0]
        if val.type() in (QVariant.Date, QVariant.Time, QVariant.DateTime):
            val = val.toDate()
            return QVariant(val.toString('dd.MM.yyyy'))
        return CCol.invalid


class CDateTimeFixedCol(CDateCol):
#    """
#      Date and time column
#    """

    def format(self, values):
        val = values[0]
        if val.type() == QVariant.Date:
            val = val.toDate()
            return QVariant(val.toString('dd.MM.yyyy'))
        elif val.type() == QVariant.DateTime:
            val = val.toDateTime()
            return QVariant(val.toString('dd.MM.yyyy hh:mm'))

        return CCol.invalid

    def getValue(self, values):
        val = values[0]
        if val.type() == QVariant.Date:
            val = val.toDate()
            return val.toString('dd.MM.yyyy')
        elif val.type() == QVariant.DateTime:
            val = val.toDateTime()
            return val.toString('dd.MM.yyyy hh:mm')
        return ''


class CBoolCol(CCol):
#    """
#      Boolean column
#    """
    valChecked   = QVariant(Qt.Checked)
    valUnchecked = QVariant(Qt.Unchecked)

    def __init__(self, title, fields, defaultWidth, alignment='c'):
        CCol.__init__(self, title, fields, defaultWidth, alignment)

    def format(self, values):
        return CCol.invalid

    def checked(self, values):
        val = values[0]
        if val.toBool():
            return CBoolCol.valChecked
        else:
            return CBoolCol.valUnchecked

    def getValue(self, values):
        val = values[0]
        if val.toBool():
            return CBoolCol.valChecked
        else:
            return CBoolCol.valUnchecked


class CEnumCol(CCol):
#    """
#      Enum column (like sex etc)
#    """
    def __init__(self, title, fields, vallist, defaultWidth, alignment='l'):
        CCol.__init__(self, title, fields, defaultWidth, alignment)
        self._vallist = vallist

    def format(self, values):
        val = values[0]
        if val:
            i = val.toInt()[0]
            if 0 <= i <len(self._vallist):
                return QVariant(self._vallist[i])
            else:
                return QVariant('{%s}' % val.toString())

    def getValue(self, values):
        val = values[0]
        if val:
            i = val.toInt()[0]
            if 0 <= i <len(self._vallist):
                return self._vallist[i]
            else:
                return '{%s}' % val.toString()

class CFileNameCol(CCol):
    def __init__(self, title, fields, defaultWidth):
        CCol.__init__(self, title, fields, defaultWidth, 'l')
        self.caches = {}

    def format(self, values):
        self.caches = {}
        fileAttachExportId  = forceRef(values[0])
        fileAttach = QtGui.qApp.db.translate('Action_FileAttach', 'id', fileAttachExportId, 'path')
        if fileAttach:
            self.caches[fileAttachExportId] = forceString(fileAttach).split('/')[-1]
            return toVariant(forceString(fileAttach).split('/')[-1])
        return CCol.invalid


class CActionNameCol(CCol):
    def __init__(self, title, fields, defaultWidth):
        CCol.__init__(self, title, fields, defaultWidth, 'l')
        self.caches = {}

    def format(self, values):
        fileAttachExportId  = forceRef(values[0])
        if self.caches.has_key(fileAttachExportId):
            return toVariant(self.caches.get(fileAttachExportId, None))
        actionName = None
        stmt = """SELECT at.title, date(a.endDate) AS dat FROM Action_FileAttach afa
  LEFT JOIN Action a ON afa.master_id = a.id
  LEFT JOIN ActionType at ON a.actionType_id = at.id
  WHERE afa.id = %s""" %(fileAttachExportId)
        query = QtGui.qApp.db.query(stmt)
        while query.next():
            record = query.record()
            actionName = forceString(record.value('title'))
            actionEndDate = forceDate(record.value('dat')).toString('dd.MM.yyyy')
        if actionName:
            self.caches[fileAttachExportId] = forceString(actionName + u' от ' + actionEndDate)
            return toVariant(forceString(actionName + u' от ' + actionEndDate))
        return CCol.invalid


class CStatusREMD_FileAttachCol(CCol):
    def __init__(self, title, fields, defaultWidth):
        CCol.__init__(self, title, fields, defaultWidth, 'l')
        self.caches = {}

    def format(self, values):
        fileAttachExportId  = forceRef(values[0])
        if self.caches.has_key(fileAttachExportId):
            return toVariant(self.caches.get(fileAttachExportId, None))
        status = None
        stmt = """  SELECT status,Message AS msg, RemdRegNumber FROM Information_Messages
    WHERE id = (SELECT MAX(id) FROM Information_Messages  WHERE typeMessages = 'REMDStatus' AND IdMedDocumentMis_id =%s
  AND ((status = 'Success' AND IdFedRequest IS NOT NULL ) OR (status = 'Failed')) ) OR id = (SELECT MAX(id) FROM Information_Messages  WHERE typeMessages = 'REMDStatus' AND IdMedDocumentMis_id =%s
  AND (status = 'Success' AND IdFedRequest IS NOT NULL  AND RemdRegNumber !='') ) 
ORDER BY status DESC limit 1 """ %(fileAttachExportId,fileAttachExportId)
        query = QtGui.qApp.db.query(stmt)
        while query.next():
            record = query.record()
            status = forceString(record.value('status'))
            msg = forceString(record.value('msg'))
            remdRegNumber = forceString(record.value('RemdRegNumber'))
        if status and msg:
            if len(remdRegNumber)>1:
                temp_message = u'Успех - ' + msg
            else:
                temp_message = u'Ожидается валидация документа на федеральном уровне'
            self.caches[fileAttachExportId] = forceString(u'Ошибка - ' + msg if status == 'Failed' else temp_message)
            return toVariant(forceString(u'Ошибка - ' + msg if status == 'Failed' else temp_message))
        else:
            self.caches[fileAttachExportId] = u'Информация еще не получена'
            return toVariant(u'Информация еще не получена')
        return CCol.invalid


class CDesignationCol(CCol):
#    u"""
#        Ссылка в базу данных с простым разыменованием
#    """
    def __init__(self, title, fields, designationChain, defaultWidth, alignment='l'):
        CCol.__init__(self, title, fields, defaultWidth, alignment)
        db = QtGui.qApp.db
        if not isinstance(designationChain, list):
            designationChain = [designationChain]
        self._caches = []
        for tableName, fieldName in designationChain:
            self._caches.append(CTableRecordCache(db, tableName, fieldName))


    def format(self, values):
        val = values[0]
        for cache in self._caches:
            recordId  = val.toInt()[0]
            if recordId:
                record = cache.get(recordId)
                if record:
                    val = record.value(0)
                else:
                    return QVariant()
#                    return CCol.invalid
            else:
                return QVariant()
#                return CCol.invalid
        return val


    def invalidateRecordsCache(self):
        for cache in self._caches:
            cache.invalidate()


class CRefBookCol(CCol):
#    """
#      RefBook column
#    """
    def __init__(self, title, fields, tableName, defaultWidth, showFields=CRBComboBox.showName, alignment='l'):
        CCol.__init__(self, title, fields, defaultWidth, alignment)
        self.tableName = tableName
        self.data = CRBModelDataCache.getData(tableName, True, '')
        self.showFields = showFields

    def format(self, values):
        recordId = forceRef(values[0])
        if recordId:
            return toVariant(self.data.getStringById(recordId, self.showFields))
        else:
            return CCol.invalid

    def invalidateRecordsCache(self):
        self.data = CRBModelDataCache.getData(self.tableName, True, '')

    def getValue(self, values):
        recordId = forceRef(values[0])
        if recordId:
            return self.data.getStringById(recordId, self.showFields)
        else:
            return ''


class CColorCol(CCol):
    def getBackgroundColor(self, values):
        val = values[0]
        colorName = forceString(val)
        if colorName:
            return QVariant(QtGui.QColor(colorName))
        return CCol.invalid

    def format(self, values):
        return CCol.invalid


class CTableModel(QAbstractTableModel):
#    Модель для хранения содержимого таблицы БД
    __pyqtSignals__ = ('itemsCountChanged(int)',
                      )
    idFieldName = 'id'
    fetchSize = 20

    def __init__(self, parent, cols=[], tableName=''):
        QAbstractTableModel.__init__(self, parent)
        self._cols = []
        self._recordsCache = None
        self._table = None
        self._loadFields = []
        self._mapColumnToOrder = {}
        self.headerSortingCol = {}
        self.readOnly = False

        self.setIdList([])
        self._cols.extend(cols)
        if tableName:
            self.setTable(tableName)


    def setReadOnly(self, value):
        self.readOnly = value


    def getReadOnly(self):
        return self.readOnly


    def flags(self, index):
        if self.readOnly:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        flags = QAbstractTableModel.flags(self, index)
        if self.cellReadOnly(index):
            flags = flags & (~Qt.ItemIsEditable) & (~Qt.ItemIsUserCheckable)
        return flags


    def cellReadOnly(self, index):
        return False


    def getOrder(self, fieldName, column):
        if hasattr(self._cols[column], 'extraFields'):
            if len(self._cols[column].extraFields) > 0:
                fieldName = self._cols[column].extraFields[0]
        return self._mapColumnToOrder[fieldName]


    def addColumn(self, col):
        self._cols.append(col)
        return col


    def cols(self):
        return self._cols


    def loadField(self, field):
        self._loadFields.append(field)


    def setTable(self, table, recordCacheCapacity=300):
        db = QtGui.qApp.db
        self._table = db.forceTable(table)
        loadFields = [self.idFieldName]
        loadFields.extend(self._loadFields)
        for col in self._cols:
            loadFields.extend(col.fields())
        loadFields = set(loadFields)
        if '*' in loadFields:
            loadFields = '*'
        else:
            loadFields = ', '.join([self._table[fieldName].name() for fieldName in loadFields])
#            loadFields = ', '.join([self._table[fieldName].name() if self._table.hasField(fieldName) else fieldName+' AS '+db.escapeIdentifier(fieldName) for fieldName in loadFields])
        self._recordsCache = CTableRecordCache(db, self._table, loadFields, recordCacheCapacity)


    def table(self):
        return self._table


    def recordCache(self):
        return self._recordsCache


    def invalidateRecordsCache(self):
        if self._recordsCache:
            self._recordsCache.invalidate()
        for col in self._cols:
            col.invalidateRecordsCache()


    def setIdList(self, idList, realItemCount=None):
        self._idList = idList
        self._realItemCount = realItemCount
        self._prevColumn = None
        self._prevRow    = None
        self._prevData   = None
        self.invalidateRecordsCache()
        self.reset()
        self.emitItemsCountChanged()


    def idList(self):
        return self._idList


    def getRealItemCount(self):
        return self._realItemCount


    def getRecordValueByIdCol(self, column, recordId):
        if column >= 0 and recordId:
            col = self._cols[column]
            if col:
                record = self.getRecordById(recordId)
                if record:
                    value = col.getValue(col.extractValuesFromRecord(record))
                    if value and isinstance(value, (QString, str, unicode)):
                        if isinstance(value, basestring):
                            return value.lower()
                        elif isinstance(value, QString):
                            return unicode(value).lower()
                    return value
        return None


    def getRecordByRow(self, row):
        recordId = self._idList[row]
        self._recordsCache.weakFetch(recordId, self._idList[max(0, row-self.fetchSize):(row+self.fetchSize)])
        return self._recordsCache.get(recordId)


    def getRecordById(self, recordId):
        return self._recordsCache.get(recordId)


    def findItemIdIndex(self, recordId):
        if self._idList:
            if recordId in self._idList:
                return self._idList.index(recordId)
        else:
            return -1


    def getRecordValues(self, column, row):
        col = self._cols[column]
        if self._prevColumn != column or self._prevRow != row or self._prevData is None:
            recordId = self._idList[row]
            self._recordsCache.weakFetch(recordId, self._idList[max(0, row-self.fetchSize):(row+self.fetchSize)])
            record = self._recordsCache.get(recordId)
            self._prevData   = col.extractValuesFromRecord(record)
            self._prevColumn = column
            self._prevRow    = row
        return (col, self._prevData)


    def columnCount(self, index = None):
        return len(self._cols)


    def rowCount(self, index = None):
        if self._idList:
            return len(self._idList)
        else:
            return 0


    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        column = index.column()
        row    = index.row()
        if role == Qt.DisplayRole: ### or role == Qt.EditRole:
            (col, values) = self.getRecordValues(column, row)
            return col.format(values)
        elif role == Qt.TextAlignmentRole:
            col = self._cols[column]
            return col.alignment()
        elif role == Qt.CheckStateRole:
            (col, values) = self.getRecordValues(column, row)
            return col.checked(values)
        elif role == Qt.ForegroundRole:
            (col, values) = self.getRecordValues(column, row)
            return col.getForegroundColor(values)
        elif role == Qt.BackgroundRole:
            (col, values) = self.getRecordValues(column, row)
            return col.getBackgroundColor(values)
        return QVariant()


    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                if section < len(self._cols):
                    return self._cols[section].title()
            if role == Qt.ToolTipRole:
                return self._cols[section].toolTip()
            if role == Qt.WhatsThisRole:
                return self._cols[section].whatsThis()
#        elif orientation == Qt.Vertical:
#            if role == Qt.DisplayRole:
#                return QVariant(self._idList[section])
        return QVariant()


    def canRemoveRow(self, row):
        return self.canRemoveItem(self._idList[row])


    def canRemoveItem(self, itemId):
        return True


    def confirmRemoveRow(self, view, row, multiple=False):
        return self.confirmRemoveItem(view, self._idList[row], multiple)


    def confirmRemoveItem(self, view, itemId, multiple=False):
        # multiple: запрос относительно одного элемента из множества, нужно предусмотреть досрочный выход из серии вопросов
        # результат: True: можно удалять
        #            False: нельзя удалять
        #            None: удаление прервано
        buttons = QtGui.QMessageBox.Yes|QtGui.QMessageBox.No
        if multiple:
            buttons |= QtGui.QMessageBox.Cancel
        mbResult = QtGui.QMessageBox.question(view, u'Внимание!', u'Действительно удалить?', buttons, QtGui.QMessageBox.No)
        return {QtGui.QMessageBox.Yes: True,
                QtGui.QMessageBox.No: False}.get(mbResult, None)


    def beforeRemoveItem(self, itemId):
        pass


    def afterRemoveItem(self, itemId):
        pass


    def removeRow(self, row, parent = QModelIndex()):
        if self._idList and 0<=row<len(self._idList):
            itemId = self._idList[row]
            if self.canRemoveItem(itemId):
                QtGui.qApp.setWaitCursor()
                try:
                    db = QtGui.qApp.db
                    table = self._table
                    db.transaction()
                    try:
                        self.beforeRemoveItem(itemId)
#                        db.deleteRecord(table, table[self.idFieldName].eq(itemId))
                        self.deleteRecord(table, itemId)
                        self.afterRemoveItem(itemId)
                        db.commit()
                    except:
                        db.rollback()
                        raise
                    self.beginRemoveRows(parent, row, row)
                    del self._idList[row]
                    self.endRemoveRows()
                    self.emitItemsCountChanged()
                    return True
                finally:
                    QtGui.qApp.restoreOverrideCursor()
        return False


    def deleteRecord(self, table, itemId):
        QtGui.qApp.db.deleteRecord(table, table[self.idFieldName].eq(itemId))


    def emitItemsCountChanged(self):
        self.emit(SIGNAL('itemsCountChanged(int)'), len(self._idList) if self._idList else 0)


    def emitDataChanged(self):
        leftTop = self.index(0, 0)
        rightBottom = self.index(self.rowCount(), self.columnCount())
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), leftTop, rightBottom)


    def sortDataModel(self):
        for col, value in self.headerSortingCol.items():
            self.idList().sort(key=lambda recordId: self.getRecordValueByIdCol(col, recordId), reverse=value)
        self.reset()


class CQueryModel(QAbstractTableModel):
#    Модель для хранения списка QSqlRecord
    def __init__(self, parent, cols=None):
        QAbstractTableModel.__init__(self, parent)
        self._cols = []
        if cols:
            self._cols.extend(cols)
        self._records = []
        self._orderColumn = None
        self._orderDesc = False


    def addColumn(self, col):
        self._cols.append(col)
        return col


    def cols(self):
        return self._cols


    def setRecords(self, records):
        self._records = records
        self.reset()


    def records(self):
        return self._records


    def recordByIndex(self, index):
        return self._records[index.row()] if index.isValid() else None


    def getRecordValues(self, column, row):
        col = self._cols[column]
        record = self._records[row]
        values = col.extractValuesFromRecord(record)
        return (col, values)


    def columnCount(self, index = None):
        return len(self._cols)


    def rowCount(self, index = None):
        return len(self._records)


    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        column = index.column()
        row    = index.row()
        if role == Qt.DisplayRole:
            (col, values) = self.getRecordValues(column, row)
            return col.format(values)
        elif role == Qt.TextAlignmentRole:
            col = self._cols[column]
            return col.alignment()
        elif role == Qt.CheckStateRole:
            (col, values) = self.getRecordValues(column, row)
            return col.checked(values)
        elif role == Qt.ForegroundRole:
            (col, values) = self.getRecordValues(column, row)
            return col.getForegroundColor(values)
        elif role == Qt.BackgroundRole:
            (col, values) = self.getRecordValues(column, row)
            return col.getBackgroundColor(values)
        return QVariant()


    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                if section < len(self._cols):
                    return self._cols[section].title()
            if role == Qt.ToolTipRole:
                return self._cols[section].toolTip()
            if role == Qt.WhatsThisRole:
                return self._cols[section].whatsThis()
        return QVariant()
    

    def setOrder(self, fieldName, orderDesc=False):
        column = self.columnIndexByFieldName(fieldName)
        if column is None:
            self._orderColumn = None
            self._orderDesc = False
        else:
            self._orderColumn = column
            self._orderDesc = orderDesc
    

    def columnIndexByFieldName(self, fieldName):
        for index, col in enumerate(self.cols()):
            if col.fields()[0] == fieldName:
                return index


    def toggleOrder(self, orderColumn):
        if orderColumn == self._orderColumn:
            self._orderDesc = not self._orderDesc
        else:
            self._orderColumn = orderColumn
            self._orderDesc = False
    

    def formatOrderBy(self, orderFields):
        if self._orderColumn is not None:
            orderCol = self.cols()[self._orderColumn]
            fieldName = forceString(orderCol.fields()[0])
            orderFields = orderFields.get(fieldName)
            if orderFields:
                if not isinstance(orderFields, (list, tuple)):
                    orderFields = [orderFields]
                return ', '.join([str(orderField) + (' desc' if self._orderDesc else ' asc') for orderField in orderFields])
        return None


    def orderColumn(self):
        return self._orderColumn


    def sortIndicator(self):
        return Qt.DescendingOrder if self._orderDesc else Qt.AscendingOrder


def sortDateTimeModel(model):
    for col, value in model.headerSortingCol.items():
        model.items.sort(key=lambda x: datetime.datetime.strptime(forceString(x[col]), u'%d.%m.%Y %H:%M' if len(forceString(x[col])) > 10 else u'%d.%m.%Y') if x[col] else datetime.datetime(1970, 1, 1), reverse=value)
    model.reset()


def alfNumKey_sort(list, key=lambda s:s, reverse=True):
    def getNumKeyFunc(key):
        convert = lambda text: int(text) if text.isdigit() else text
        return lambda s: [convert(c) for c in re.split('([0-9]+)', unicode(key(s)) if isinstance(key(s), (QString, str)) else key(s))] if isinstance(key(s), (QString, str, unicode)) else key(s)
    sort_key = getNumKeyFunc(key)
    list.sort(key=sort_key, reverse=reverse)


def sortDataModel(model):
    for col, value in model.headerSortingCol.items():
        alfNumKey_sort(model.items, key=lambda x: x[col], reverse=value)
    model.reset()
