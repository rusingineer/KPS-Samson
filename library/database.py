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

from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import Qt, QDateTime, QVariant, QDate, QTime

from library.DBReconnectProgressDialog import CDBReconnectProgressDialog
from library.Utils import forceString, toVariant, forceLong, forceDateTime, forceInt, forceDate, forceStringEx
from library.exception import CException


def decorateString(s):
    u = unicode(s)
    return '\''+u.replace('\\', '\\\\').replace('\'', '\\\'')+'\''


class CPreparedQueryCacheItem(object):
    __slots__ = 'prev','next','stmt','prepared'

    def __init__(self, stmt, prepared):
        self.prev = self.next = None
        self.stmt = stmt
        self.prepared = prepared


    def extract(self):
        self.prev.next = self.next
        self.next.prev = self.prev
        self.prev = self.next = None


    def insert(self, prev, next):
        self.prev = prev
        self.next = next
        prev.next = next.prev = self


class CPreparedQueryCache(object):
    __slots__ = 'prev','next','capacity','d', 'prepare'

    def __init__(self, capacity=10):
        self.capacity = capacity
        self.clear()


    def clear(self):
        self.d = {}
        self.prev = self # типа кольцевой двусвязный список, сюда добавляем
        self.next = self # отсюда удаляем


    def get(self, stmt):
        item = self.d.get(stmt, None)
        if item is not None:
            if self.prev != item:
                item.extract()
                item.insert(self.prev, self)
            return item.prepared
        else:
            prepared = self.prepare(stmt)
            item = CPreparedQueryCacheItem(stmt, prepared)
            self.d[stmt] = item
            item.insert(self.prev, self)
            if len(self.d) > self.capacity:
                del self.d[self.next.stmt]
                self.next.extract()
            return prepared


class CDatabaseException(CException):
    """
       Root of all database exceptions
    """
    def __init__(self, message, sqlError=None):
#        if self.sqlError and sqlError.type() != QtSql.QSqlError.NoError:
        if sqlError:
            message = message + '\n' + sqlError.driverText() + '\n' + sqlError.databaseText()
        CException.__init__(self, unicode(message))
#        print self._message
        self.sqlError = sqlError


class CDatabaseExceptionTrigger(CException):
    def __init__(self, message, sqlError=None):
        if sqlError:
            message = u"{0} \n{1} \n{2}".format(
                message,
                sqlError.driverText(),
                unicode(sqlError.databaseText()).encode('latin-1').decode('utf-8')
            )
        CException.__init__(self, unicode(message))
        self.sqlError = sqlError


#    def __str__(self):
#        return unicode(self._message)
class CSqlRecord(QtSql.QSqlRecord):
    def __init__(self, *args, **kwargs):
        QtSql.QSqlRecord.__init__(self, *args, **kwargs)
        if len(args) == 1 and type(args[0]) == CSqlRecord:
            self._dirty = args[0]._dirty
        else:
            self._dirty = False

    def setValue(self, name, val):
        if name not in ("modifyDatetime", "modifyPerson_id", "createDatetime", "createPerson_id"):
            prev_value = QtSql.QSqlRecord.value(self, name)
            if type(val) != QVariant:
                val = QVariant(val)
            if val != prev_value:
                if val.typeName():
                    different = prev_value.toString() != val.toString()
                else:
                    different = not (prev_value.isNull() and prev_value.isValid())
                if different:
                    self.setIsDirty(True)
        QtSql.QSqlRecord.setValue(self, name, val)

    def setNull(self, name):
        if not QtSql.QSqlRecord.value(self, name).isNull():
            self.setIsDirty(True)
        QtSql.QSqlRecord.setNull(self, name)


    def isDirty(self):
        return self._dirty
    
    
    def setIsDirty(self, isDirty):
        self._dirty = isDirty


class CField(object):
    def __init__(self, database, tableName, field):
        self.database = database
        self.tableName = tableName
        self.fieldName = database.escapeFieldName(field.name())
        self.field = field


    def __dateAdd(self, intervalType, count):
        fieldName = self.database.dateAdd(self.name(), intervalType, count)
        return CWrappedField(fieldName, self.field.type(), self.database)


    def dateAddDay(self, count):
        return self.__dateAdd('DAY', count)


    def toDate(self):
        self.database.toDate(self.name())


    def name(self):
        return self.tableName+'.'+self.fieldName


    def type(self):
        return self.field.type()


    def __str__(self):
        return self.name()


    def alias(self, name=''):
        if name:
            return self.name()+' AS '+self.database.escapeFieldName(name)
        else:
            return self.name()+' AS '+self.fieldName


    def toTable(self, tableName):
        return CField(self.database, tableName, self.field)


    def signEx(self, sign, expr):
        return unicode(self.name()+sign+expr)


    def formatValue(self, value):
        if isinstance(value, CField):
            return value.name()
        else:
            return self.database.formatValueEx(self.field.type(), value)


    def sign(self, sign, val):
        return self.signEx(sign,self.formatValue(val))


    def eq(self, val):
        if val is None:
            return self.isNull()
        else:
            return self.sign('=', val)


    def eqEx(self, val):
        if val is None:
            return self.isNull()
        else:
            return self.signEx('=', val)


    def lt(self, val):
        return self.sign('<', val)


    def le(self, val):
        return self.sign('<=', val)


    def gt(self, val):
        return self.sign('>', val)


    def ge(self, val):
        return self.sign('>=', val)


    def ne(self, val):
        if val is None:
            return self.isNotNull()
        else:
            return self.sign('!=', val)

    def nullSafeNe(self, val):
        return 'NOT %s' % self.nullSafeEq(val)


    def nullSafeEq(self, val):
        return self.sign('<=>', val)


    def isNull(self):
        return unicode(self.name()+' IS NULL')


    def position(self, val):
        return unicode('POSITION(' + '\'%s\' IN ' % (val) + self.name() + ')')


    def cast(self, type):
        return unicode('CAST(' + self.name()+' AS %s)' % (type))


    def isNotCast(self, type):
        return unicode('NOT CAST(' + self.name()+' AS %s)' % (type))


    def isNotNull(self):
        return unicode(self.name()+' IS NOT NULL')


    def trim(self):
        return 'TRIM('+unicode(self.name()+')')


    def decoratedlist(self, list):
        if not list:
            return '()'
        else:
            decoratedList = []
            for value in list:
                decoratedList.append(self.database.formatValueEx(self.field.type(), value))
            return unicode('('+(','.join(decoratedList))+')')


    def inlist(self, list):
        if not list:
            return 'false' # false
        else:
            return unicode(self.name()+' IN '+ self.decoratedlist(list))


    def notInlist(self, list):
        if not list:
            return 'true' # true; any value not in empty list
        else:
            return unicode(self.name()+' NOT IN '+ self.decoratedlist(list))


    def like(self, val):
        return self.sign(' LIKE ', undotLikeMask(val))


    def contain(self, val):
        return self.sign(' LIKE ', undotLikeMask('%'+val+'%'))


    def notlike(self, val):
        return self.sign(' NOT LIKE ', undotLikeMask(val))


    def likeBinary(self, val):
        return self.sign(' LIKE BINARY ', undotLikeMask(val))


    def regexp(self, val):
        return self.sign(' REGEXP ', val)


    def between(self, low, high):
        return u'(%s BETWEEN %s AND %s)' % (self.name(), self.formatValue(low), self.formatValue(high))
    
    
    def textBetween(self, low, high):
        return u'left({0}, {1}) >= {2} AND left({0}, {3}) <= {4}'.format(self.name(), len(low), self.formatValue(low), len(high), self.formatValue(high))


    def dateEq(self, val):
        if val is None:
            return self.isNull()
        else:
            return 'DATE('+self.name()+')=DATE('+unicode(self.formatValue(val)+')')


    def dateNe(self, val):
        if val is None:
            return self.isNull()
        else:
            return 'DATE(' + self.name() + ')!=DATE(' + unicode(self.formatValue(val) + ')')


    def dateLe(self, val):
        if val is None:
            return self.isNull()
        else:
            return 'DATE('+self.name()+')<=DATE('+unicode(self.formatValue(val)+')')


    def dateLt(self, val):
        if val is None:
            return self.isNull()
        else:
            return 'DATE('+self.name()+')<DATE('+unicode(self.formatValue(val)+')')


    def dateGe(self, val):
        if val is None:
            return self.isNull()
        else:
            return 'DATE('+self.name()+')>=DATE('+unicode(self.formatValue(val)+')')


    def dateGt(self, val):
        if val is None:
            return self.isNull()
        else:
            return 'DATE('+self.name()+')>DATE('+unicode(self.formatValue(val)+')')


    def dateBetween(self, low, high):
        return u'(DATE(%s) BETWEEN %s AND %s)' % (self.name(), self.formatValue(low), self.formatValue(high))


    def date_ADDYEAR(self, val):
        return u' DATE_ADD(\'%s\', INTERVAL %s YEAR) ' % (self.name(), self.formatValue(val))


    def monthGe(self, val):
        if val is None:
            return self.isNull()
        else:
            if self.database.name in ('mysql', 'interbase'):
                return 'MONTH('+self.name()+')>=MONTH('+unicode(self.formatValue(val)+')')
            else:
                return 'extract(month from '+self.name()+') >= extract(month from date '+unicode(self.formatValue(val))+')'


    def yearGe(self, val):
        if val is None:
            return self.isNull()
        else:
            if self.database.name in ('mysql', 'interbase'):
                return 'YEAR('+self.name()+')>=YEAR('+unicode(self.formatValue(val)+')')
            else:
                return 'extract(year from '+self.name()+') >= extract(year from date '+unicode(self.formatValue(val))+')'


    def yearEq(self, val):
        if val is None:
            return self.isNull()
        else:
            if self.database.name in ('mysql', 'interbase'):
                return 'YEAR('+self.name()+')=YEAR('+unicode(self.formatValue(val)+')')
            else:
                return 'extract(year from '+self.name()+') = extract(year from date '+unicode(self.formatValue(val))+')'


class CSurrogateField(CField):
    def __init__(self, name, type):
        self.database = None
        self.tableName = ''
        self.fieldName = name
        self.field = QtSql.QSqlField(name, type)


class CWrappedField(CSurrogateField):
    def __init__(self, name, type, database):
        CSurrogateField.__init__(self, name, type)
        self.database = database

    def name(self):
        return self.fieldName


class CTable(object):
    def __init__(self, tableName, database):
        self.fields = []
        self.fieldsDict = {}
        self.database = database
        self.tableName = str(tableName)
        self._idField = None
        self._idFieldName = None
        self.index_hint = None
        record = database.record(self.tableName)
        for i in range(record.count()):
            qtfield = record.field(i)
            field = CField(self.database, self.tableName, qtfield)
            self.fields.append(field)
            self.fieldsDict[str(qtfield.name())] = field


    def name(self, alias=''):
        if alias:
            return self.tableName+' AS '+unicode(alias)
        else:
            return self.tableName


    def alias(self, name):
        return CTableAlias(self, name)


    def getMainTable(self):
        return self


    def setIdFieldName(self, name, idTableName=''):
        self._idField = self.__getitem__(name)
        self._idFieldName = name


    def idField(self):
        if not self._idField:
            self.setIdFieldName('id')
##            raise CDatabaseException(CDatabase.errNoIdField % (self.tableName))
        return self._idField


    def idFieldName(self):
        if not self._idField:
            self.setIdFieldName('id')
##            raise CDatabaseException(CDatabase.errNoIdField % (self.tableName))
        return self._idFieldName


    def findField(self, fieldName):
        parts = fieldName.split('.')
        if len(parts) <= 1:
            findFieldName = fieldName
            findTableName = self.name()
        else:
            findFieldName = parts[len(parts) - 1]
            findTableName = u'.'.join(part for i, part in enumerate(parts) if i < (len(parts) - 1))
        if self.database.name == 'postgres':
            findFieldName = findFieldName.lower()
        return self.fieldsDict.get(findFieldName, None) if findTableName == self.name() else None


    def __getitem__(self, fieldName):
        fieldName = str(fieldName)
        result = self.findField(fieldName)
        if result:
            return result
        raise CDatabaseException(CDatabase.errFieldNotFound % (self.tableName, fieldName) )


    def hasField(self, fieldName):
        return self.fieldsDict.has_key(fieldName)


    def newRecord(self, fields=None):
        record = CSqlRecord() #QtSql.QSqlRecord()
        if fields:
            for field in self.fields:
                if field.field.name() in fields:
                    record.append( QtSql.QSqlField(field.field) )
        else:
            for field in self.fields:
                record.append( QtSql.QSqlField(field.field) )
        return record


    def beforeInsert(self, record):
        return


    def beforeUpdate(self, record):
        return


    def beforeDelete(self, record):
        return


    def join(self, table, onCond):
        return self.database.join(self, table, onCond)


    def leftJoin(self, table, onCond):
        return self.database.leftJoin(self, table, onCond)


    def innerJoin(self, table, onCond):
        return self.database.innerJoin(self, table, onCond)


class CTableAlias(object):
    def __init__(self, table, name):
        self.table = table
        self.tableName = str(name)
        self.fieldsDict = {}
        self.database = table.database
        self._idField = None
        self._idFieldName = None


    def name(self):
        return self.table.name()+' AS '+self.tableName


    def hasField(self, fieldName):
        return self.table.hasField(fieldName)


    def newRecord(self, fields=None):
        return self.table.newRecord(fields)


    def getMainTable(self):
        return self


    def setIdFieldName(self, name):
        self._idField = self.__getitem__(name)
        self._idFieldName = name


    def idField(self):
        if not self._idField:
            self.setIdFieldName('id')
        return self._idField


    def idFieldName(self):
        if not self._idField:
            self.setIdFieldName('id')
        return self._idFieldName


    def findField(self, fieldName):
        result = self.fieldsDict.get(fieldName, None)
        if not result:
            field = self.table.findField(fieldName)
            if field:
                result = field.toTable(self.tableName)
        return result


    def __getitem__(self, fieldName):
        fieldName = str(fieldName)
        result = self.findField(fieldName)
        if result:
            return result
        raise CDatabaseException(CDatabase.errFieldNotFound % (self.name(), fieldName) )


    def beforeInsert(self, record):
        self.table.beforeInsert(record)


    def beforeUpdate(self, record):
        self.table.beforeUpdate(record)


    def beforeDelete(self, record):
        self.table.beforeDelete(record)
        return


    def join(self, table, onCond):
        return self.database.join(self, table, onCond)


    def leftJoin(self, table, onCond):
        return self.database.leftJoin(self, table, onCond)


    def innerJoin(self, table, onCond):
        return self.database.innerJoin(self, table, onCond)


class CDocumentTable(CTable):
    # fields in DocumentTables:
    dtfCreateDatetime = 'createDatetime'
    dtfCreateUserId   = 'createPerson_id'
    dtfModifyDatetime = 'modifyDatetime'
    dtfModifyUserId   = 'modifyPerson_id'
    dtfDeleted        = 'deleted'

    def __init__(self, tableName, database):
        CTable.__init__(self, tableName, database)


    def beforeInsert(self, record):
        # now = toVariant(QDateTime.currentDateTime())
        query = QtGui.qApp.db.query('SELECT NOW() as dt')
        if query.next():
            now = toVariant(forceDateTime(query.record().value('dt')))
        else:
            now = toVariant(QDateTime.currentDateTime())

        userId = toVariant(QtGui.qApp.userId)
#        userId = toVariant(None)
        if record.indexOf(CDocumentTable.dtfCreateDatetime)<0:
            record.append(QtSql.QSqlField(CDocumentTable.dtfCreateDatetime, QVariant.DateTime))
        if record.indexOf(CDocumentTable.dtfCreateUserId)<0:
            record.append(QtSql.QSqlField(CDocumentTable.dtfCreateUserId, QVariant.Int))
        if record.indexOf(CDocumentTable.dtfModifyDatetime)<0:
            record.append(QtSql.QSqlField(CDocumentTable.dtfModifyDatetime, QVariant.DateTime))
        if record.indexOf(CDocumentTable.dtfModifyUserId)<0:
            record.append(QtSql.QSqlField(CDocumentTable.dtfModifyUserId,  QVariant.Int))

        record.setValue(CDocumentTable.dtfCreateDatetime, now)
        record.setValue(CDocumentTable.dtfCreateUserId,   userId)
        record.setValue(CDocumentTable.dtfModifyDatetime, now)
        record.setValue(CDocumentTable.dtfModifyUserId,   userId)
        return

    def beforeUpdate(self, record):
        # now = toVariant(QDateTime.currentDateTime())
        query = QtGui.qApp.db.query('SELECT NOW() as dt')
        if query.next():
            now = toVariant(forceDateTime(query.record().value('dt')))
        else:
            now = toVariant(QDateTime.currentDateTime())

        userId = toVariant(QtGui.qApp.userId)
#        userId = toVariant(None)

        if record.indexOf(CDocumentTable.dtfModifyDatetime)<0:
            record.append(QtSql.QSqlField(CDocumentTable.dtfModifyDatetime, QVariant.DateTime))
        if record.indexOf(CDocumentTable.dtfModifyUserId)<0:
            record.append(QtSql.QSqlField(CDocumentTable.dtfModifyUserId, QVariant.Int))

        record.setValue(CDocumentTable.dtfModifyDatetime, now)
        record.setValue(CDocumentTable.dtfModifyUserId,   userId)
        return


    def beforeUpdateNoDatetimeModifying(self, record):
        # now = toVariant(QDateTime.currentDateTime())
        userId = toVariant(QtGui.qApp.userId)
        #        userId = toVariant(None)

        # if record.indexOf(CDocumentTable.dtfModifyDatetime) < 0:
        #     record.append(QtSql.QSqlField(CDocumentTable.dtfModifyDatetime, QVariant.DateTime))
        if record.indexOf(CDocumentTable.dtfModifyUserId) < 0:
            record.append(QtSql.QSqlField(CDocumentTable.dtfModifyUserId, QVariant.Int))

        # record.setValue(CDocumentTable.dtfModifyDatetime, now)
        record.setValue(CDocumentTable.dtfModifyUserId, userId)
        return


#    def beforeDelete(self, record):
#        record.setValue(CDocumentTable.dtfModifyDatetime, toVariant(Now()))
#        record.setValue(CDocumentTable.dtfModifyUserId,   toVariant(???))
#        record.setValue(CDocumentTable.dtfModifyUserId,   toVariant(True))
#        return

class CJoin(object):
    def __init__(self, firstTable, secondTable, onCond, stmt='JOIN'):
        self.firstTable = firstTable
        self.secondTable = secondTable
        self.onCond = onCond
        self.stmt = stmt
        self.database = firstTable.database
        self._idField = None
        self._idFieldName = None
        assert firstTable.database == secondTable.database


    def name(self):
        return u'%s %s %s %s ' % (' '.join([self.firstTable.name(), self.firstTable.index_hint if hasattr(self.firstTable, 'index_hint') and self.firstTable.index_hint else '']), self.stmt, self.secondTable.name(), ('ON %s'%self.onCond) if self.onCond else '')


    def join(self, table, onCond):
        return self.database.join(self, table, onCond)


    def leftJoin(self, table, onCond):
        return self.database.leftJoin(self, table, onCond)


    def innerJoin(self, table, onCond):
        return self.database.innerJoin(self, table, onCond)


    def getMainTable(self):
        return self.firstTable.getMainTable()


    def setIdFieldName(self, name):
        self._idField = self.__getitem__(name)
        self._idFieldName = name

    #    def idField(self):
    #        if not self._idField:
    #            self.setIdFieldName(self.firstTable.idField())
    #        return self._idField


    def idFieldName(self):
        if not self._idField:
            self.setIdFieldName(self.firstTable.idField())
        return self._idFieldName


    def idField(self):
        return self._idField if self._idField else self.firstTable.idField()


    def findField(self, fieldName):
        return self.firstTable.findField(fieldName) or self.secondTable.findField(fieldName)


    def __getitem__(self, key):
        key = str(key)
        result = self.findField(key)
        if result:
            return result
        raise CDatabaseException(CDatabase.errFieldNotFound % (self.name(), key) )


################################################################
#

DocumentTables = []

def registerDocumentTable(tableName):
    DocumentTables.append(tableName)



class CDatabase(object):
    # уровни изоляции транзакций:
    READ_UNCOMMITTED = 'READ UNCOMMITTED'
    READ_COMMITTED   = 'READ COMMITTED'
    REPEATABLE_READ  = 'REPEATABLE READ'
    SERIALIZABLE     = 'SERIALIZABLE'

    errUndefinedDriver         = u'Драйвер базы данных "%s" не зарегистрирован'
    errCannotConnectToDatabase = u'Невозможно подключиться к базе данных "%s"'
    errCannotOpenDatabase      = u'Невозможно открыть базу данных "%s"'
    errDatabaseIsNotOpen       = u'База данных не открыта'
    errTransactionError        = u'Ошибка открытия тразнакции'
    errCommitError             = u'Ошибка закрытия тразнакции'
    errRollbackError           = u'Ошибка отмены тразнакции'
    errTableNotFound           = u'Таблица "%s" не найдена'
    errFieldNotFound           = u'В таблице %s не найдено поле "%s"'
    errQueryError              = u'Ошибка выполнения запроса\n%s'
    errNoIdField               = u'В таблице %s не определен первичный ключ'
    errIdFieldIsNull           = u'В таблице %s значение первичного ключа пусто'

    dbGl                         = None
    parentGl                     = None
    isCloseApp                   = 0
    connectionIDGL               = 0

    # добавлено для formatQVariant
    convMethod = {
                    QVariant.Int       : lambda val: unicode(val.toInt()[0]),
                    QVariant.UInt      : lambda val: unicode(val.toUInt()[0]),
                    QVariant.LongLong  : lambda val: unicode(val.toLongLong()[0]),
                    QVariant.ULongLong : lambda val: unicode(val.toULongLong()[0]),
                    QVariant.Double    : lambda val: unicode(val.toDouble()[0]),
                    QVariant.Bool      : lambda val: u'1' if val.toBool() else u'0',
                    QVariant.Char      : lambda val: decorateString(val.toString()),
                    QVariant.String    : lambda val: decorateString(val.toString()),
                    QVariant.Date      : lambda val: decorateString(val.toDate().toString(Qt.ISODate)),
                    QVariant.Time      : lambda val: decorateString(val.toTime().toString(Qt.ISODate)),
                    QVariant.DateTime  : lambda val: decorateString(val.toDateTime().toString(Qt.ISODate)),
                    QVariant.ByteArray : lambda val: 'x\''+str(val.toByteArray().toHex())+'\'',
                 }


    def __init__(self, logger=None):
        self.db = None
        self.tables = {}
        self.connectionId = 'undefined'
        self.logger = logger


    def escapeIdentifier(self, name, type):
        return unicode(self.driver().escapeIdentifier(name, type))


    def escapeFieldName(self, name):
        return unicode(self.driver().escapeIdentifier(name, QtSql.QSqlDriver.FieldName))


    def escapeTableName(self, name):
        return unicode(self.driver().escapeIdentifier(name, QtSql.QSqlDriver.TableName))


    escapeSchemaName = escapeTableName


#    def getConnectionId(self):
#        return self.connectionId


    @staticmethod
    def dummyRecord():
        return QtSql.QSqlRecord()


# Добавлено из-за обнаруженной ошибки в qt4 v.4.5.3:
# - значения полей типа DOUBLE считываются не как QVariant.Double а как QVariant.String
#   поведение в windows не исследовано, а в linux строка записывается с десятичной запятой.
#   при этом документированный способ исправить положение
#   query.setNumericalPrecisionPolicy(QSql.LowPrecisionDouble)
#   не срабатывает из-за того, что driver.hasFeature(QSqlDriver.LowPrecisionNumbers)
#   возвращает false
# - при записи значения в запрос формируется значение с запятой, что неприемлемо для MySql сервера
# поэтому принято решение написать свой вариант formatValue

    @classmethod
    def formatQVariant(cls, fieldType, val):
        if val.isNull():
            return 'NULL'
        return cls.convMethod[fieldType](val)


    @classmethod
    def formatValue(cls, field):
        return cls.formatQVariant(field.type(), field.value())


    @classmethod
    def formatValueEx(cls, fieldType, value):
        if isinstance(value, QVariant):
            return cls.formatQVariant(fieldType, value)
        else:
            return cls.formatQVariant(fieldType, toVariant(value))


    def createConnection(self, connectionName):
        if connectionName:
            db = QtSql.QSqlDatabase.addDatabase(self.driverName, connectionName)
        else:
            db = QtSql.QSqlDatabase.addDatabase(self.driverName)
        if not db.isValid():
            raise CDatabaseException(CDatabase.errCannotConnectToDatabase % self.driverName, db.lastError())
        return db


    def connect(self, db, serverName, serverPort, databaseName, userName, password):
        db.setHostName(serverName)
        if serverPort:
            db.setPort(serverPort)
        db.setDatabaseName(databaseName)
        db.setUserName(userName)
        db.setPassword(password)
        if not db.open():
            raise CDatabaseException(CDatabase.errCannotOpenDatabase % databaseName, db.lastError())
        self.db = db
        QtGui.qApp.dbInside = db
        self.connectionId = '%s://%s' % (self.driverName, databaseName)
        if serverName:
            self.connectionId += '@%s' % serverName
            if serverPort:
                self.connectionId += ':%s' % serverPort
        if self.logger:
            self.logger.info(u'DB:%s connect' % self.connectionId)


#    def __del__(self):
#        self.close()


    def close(self):
        if self.db:
            #connectionName = self.db.connectionName()
            self.db.close()
#            self.driver = None
            self.db = None
            #QtSql.QSqlDatabase.removeDatabase(connectionName)
            if self.logger:
                self.logger.info(u'DB:%s close' % self.connectionId)
        self.tables = {}

#ymd st

    def setSonnectionIDGL(self):
        query = QtSql.QSqlQuery(self.db)
        if self.driverName == "QMYSQL":
            query.exec_("select CONNECTION_ID() as CONNECTION_ID from dual")
        if query.next():
            record = query.record()
            self.connectionIDGL = forceInt(record.value(0))

    def execDBNotCheck(self, stm):
        if not QtSql.QSqlQuery(self.db).exec_(stm):
            return 0
        return 1

    def remoteConnect(self):
        QtGui.qApp.openDatabaseReConnect()
        self.db = QtGui.qApp.dbInside

    def reconnectDB(self):
        checkString = ""
        if self.driverName == "QMYSQL":
            checkString = "select 1 as id from dual"
        if (self.execDBNotCheck(checkString) == 0 and QtGui.qApp.isBusyReconnect == 0):
            QtGui.qApp.isBusyReconnect = 1
            try:
                oldconnectionIDGL = self.connectionIDGL

                progressDialog = CDBReconnectProgressDialog(self, self.parentGl)
                progressDialog.exec_()
                #self.remoteConnect()

                self.setSonnectionIDGL()
                self.execDBNotCheck("update AppLock set connectionId=%s where connectionId=%s" % (self.connectionIDGL, oldconnectionIDGL))

                if self.driverName == "QMYSQL":
                    checkString = "CALL getAppLock_prepare()"
                self.execDBNotCheck(checkString)
            finally:
                QtGui.qApp.isBusyReconnect = 0

    def checkdb(self):
        if hasattr(QtGui.qApp, 'disableCheckDB') and not QtGui.qApp.disableCheckDB():
            if self.isCloseApp == 0:
                if self.parentGl is not None:
                    self.reconnectDB()
        if not self.isOpen():
            raise CDatabaseException(CDatabase.errDatabaseIsNotOpen)

# ymd end


    def isOpen(self):
        return self.db and self.db.isValid() and self.db.isOpen()


    def driver(self):
        return self.db.driver()


    def forceTable(self, table):
        if isinstance(table, (CTable, CTableAlias, CJoin)):
            return table
        elif isinstance(table, basestring):
            return self.table(table)
        else:
            raise TypeError, u'Недопустимый тип'


    def table(self, tableName):
        self.checkdb()
        if self.tables.has_key(tableName):
            return self.tables[tableName]
        else:
            if tableName in DocumentTables:
                table = CDocumentTable(tableName, self)
            else:
                table = CTable(tableName, self)
            self.tables[tableName] = table
            return table


    def record(self, tableName):
        parts = tableName.split('.', 1)
        if len(parts) <= 1:
            res = self.db.record(tableName)
        else:
            currentDatabaseName = self.db.databaseName()
            databaseName = parts[0]
            try:
                self.query('USE %s' % self.escapeSchemaName(databaseName))
                res = self.db.record(parts[1])
                self.query('USE %s' % self.escapeSchemaName(currentDatabaseName))
            finally:
                pass
        if res.isEmpty():
            raise CDatabaseException(CDatabase.errTableNotFound % tableName)
        return CSqlRecord(res)


    def mainTable(self, tableExpr):
        if isinstance(tableExpr, (CTable, CTableAlias, CJoin)):
            return tableExpr
        elif isinstance(tableExpr, basestring):
            name = tableExpr.split(None, 1)[0] if ' ' in tableExpr else tableExpr
            return self.table(name)
        else:
            raise TypeError, u'Недопустимый тип'


    def getTableName(self, table):
        if isinstance(table, (CTable, CTableAlias, CJoin)):
            return table.name()
        elif isinstance(table, basestring):
            return table
        else:
            raise TypeError, u'Недопустимый тип'


    def formatDate(self, val):
        return '\''+str(val.toString(Qt.ISODate))+'\''


    def formatTime(self, val):
        return '\''+str(val.toString(Qt.ISODate))+'\''


    def joinAnd(self, list):
        if list:
            return '('+(') AND ('.join(list))+')'
        else:
            return '1'


    def joinOr(self, list):
        if list:
            return '(('+(') OR ('.join(list))+'))'
        else:
            return '0'


    def joinXor(self, list):
        if list:
            return '(('+(') XOR ('.join(list))+'))'
        else:
            return '0'


    def if_(self, cond, thenPart, elsePart):
        return 'IF('+cond+','+thenPart+','+elsePart+')'


    def prepareFieldList(self, fields):
        if isinstance(fields, (list, tuple)):
            return  ', '.join([field.name() if isinstance(field, CField) else field for field in fields])
        return fields.name() if isinstance(fields, CField) else fields


    def prepareWhere(self, cond):
        if isinstance(cond, (list, tuple)):
            cond = self.joinAnd(cond)
        if cond:
            return ' WHERE '+ cond
        else:
            return ''


    def prepareHaving(self, having):
        if isinstance(having, (list, tuple)):
            having = self.joinAnd(having)
        if having:
            return ' HAVING '+ having
        else:
            return ''


    def prepareOrder(self, order):
        if isinstance(order, (list, tuple)):
            order = ', '.join(order)
        if order:
            return ' ORDER BY '+ order
        else:
            return ''


    def prepareGroup(self, group):
        if isinstance(group, (list, tuple)):
            group = ', '.join(group)
        if group:
            return ' GROUP BY '+ group
        else:
            return ''


    def prepareLimit(self, limit):
        assert False


    def selectStmt(self, table, fields='*', where='', order='', limit=None):
        self.checkdb()
        table = self.forceTable(table)
        return ' '.join([
            'SELECT', self.prepareFieldList(fields),
            'FROM', table.name(),
            self.prepareWhere(where),
            self.prepareOrder(order)])

#        return 'SELECT %s FROM %s %s %s %s' % (self.prepareFieldList(fields),
#                                          table.name(),
#                                          self.prepareWhere(where),
#                                          self.prepareOrder(order),
#                                          self.prepareLimit(limit))


    def selectStmtGroupBy(self, table, fields='*', where='', group='', order='', limit=None):
        self.checkdb()
        table = self.forceTable(table)
        return ' '.join([
            'SELECT', self.prepareFieldList(fields),
            'FROM', table.name(),
            self.prepareWhere(where),
            self.prepareGroup(group),
            self.prepareOrder(order),
            self.prepareLimit(limit)])


    def selectDistinctStmt(self, table, fields='*', where='', order='', limit=None):
        self.checkdb()
        tableName = self.getTableName(table)
        return ' '.join([
            'SELECT DISTINCT', self.prepareFieldList(fields),
            'FROM', tableName,
            self.prepareWhere(where),
            self.prepareOrder(order)])


    def existsStmt(self, table, where):
        self.checkdb()
        table = self.forceTable(table)
#        if isinstance(table, CJoin):
#            mainTable = table.getMainTable()
#        else:
#            mainTable = table
#        if mainTable.hasField('id'):
#            field = mainTable['id'].name()
#        else:
#            field = 'NULL'
#        return 'EXISTS (%s)' % self.selectStmt(table, field, where)
        return 'EXISTS (%s)' % self.selectStmt(table, 'NULL', where)


    def notExistsStmt(self, table, where):
        return 'NOT %s' % self.existsStmt(table, where)


    def join(self, firstTable, secondTable, onCond, stmt='JOIN'):
        self.checkdb()
        if isinstance(onCond, (list, tuple)):
            onCond = self.joinAnd(onCond)
        return CJoin(self.forceTable(firstTable), self.forceTable(secondTable), onCond, stmt)


    def leftJoin(self, firstTable, secondTable, onCond):
        return self.join(firstTable, secondTable, onCond, 'LEFT JOIN')


    def innerJoin(self, firstTable, secondTable, onCond):
        return self.join(firstTable, secondTable, onCond, 'INNER JOIN')


    def transaction(self, isolationLevel=None):
        self.checkdb()
        if isolationLevel is not None:
            stmt = 'SET TRANSACTION ISOLATION LEVEL %s;' % isolationLevel
            query = self.db.exec_(stmt)
            if query.lastError():
                raise CDatabaseException(CDatabase.errTransactionError, self.db.lastError())
            if self.logger:
                self.logger.info(u'DB:%s transaction with %s' % (self.connectionId, stmt))
        else:
            if self.logger:
                self.logger.info(u'DB:%s transaction' % self.connectionId)
        if not self.db.transaction():
            raise CDatabaseException(CDatabase.errTransactionError, self.db.lastError())


    def commit(self):
        self.checkdb()
        if self.logger:
            self.logger.info(u'DB:%s commit' % self.connectionId)
        if not self.db.commit():
            raise CDatabaseException(CDatabase.errCommitError, self.db.lastError())


    def rollback(self):
        self.checkdb()
        if self.logger:
            self.logger.info(u'DB:%s rollback' % self.connectionId)
        if not self.db.rollback():
            raise CDatabaseException(CDatabase.errRollbackError, self.db.lastError())


    def query(self, stmt):
        self.checkdb()
        query = QtSql.QSqlQuery(self.db)
        query.setForwardOnly(True)
        query.setNumericalPrecisionPolicy(QtSql.QSql.LowPrecisionDouble)

        if self.logger:
            self.logger.info(u'DB:%s query %s' % (self.connectionId, stmt))
#            for i, v enumerate(query.boundValues().values()):
#                self.logger.info(u'arg#%d = %s' % (i, v.toString()[:128])
            time = QTime()
            time.start()

        if not query.exec_(stmt):
            self.onError(stmt, query.lastError())

        if self.logger:
            self.logger.info(u'DB:%s request took %.3f secs, %d rows affected, %d rows selected' % (
                                                                self.connectionId,
                                                                time.elapsed()*0.001,
                                                                query.numRowsAffected(),
                                                                query.size()
                                                            )
                            )
        return query


    def prepare(self, stmt):
        self.checkdb()
        result = QtSql.QSqlQuery(self.db)
        result.setForwardOnly(True)
        result.setNumericalPrecisionPolicy(QtSql.QSql.LowPrecisionDouble)
        if not result.prepare(stmt):
            self.onError(stmt, result.lastError())
        return result


    def execPreparedQuery(self, query):
        self.checkdb()
        if self.logger:
            self.logger.info(u'DB:%s prepared query %s' % (self.connectionId, query.executedQuery()))
            time = QTime()
            time.start()
        if not query.exec_():
            self.onError(unicode(query.executedQuery()), query.lastError())
        if self.logger:
            self.logger.info(u'DB:%s request took %.3f secs, %d rows affected, %d rows selected' % (
                                                                self.connectionId,
                                                                time.elapsed()*0.001,
                                                                query.numRowsAffected(),
                                                                query.size()
                                                            )
                            )
        return query


    def onError(self, stmt, sqlError):
        raise CDatabaseException(CDatabase.errQueryError % stmt, sqlError)

    def onErrorTrigger(self, stmt, sqlError):
        raise CDatabaseExceptionTrigger(CDatabase.errQueryError % stmt, sqlError)


    def isProcedureExists(self, procedureName, schemaName=None):
        raise NotImplementedError('abstract method call')


    def getRecordEx(self, table, cols, where='', order=''):
        stmt = self.selectStmt(table, cols, where, order, 1)
        query = self.query(stmt)
        if query.first():
            record=query.record()
#            del query
            return CSqlRecord(record)
        else:
            return None


    def getRecord(self, table, cols, recordId):
        self.checkdb()
        idCol = self.mainTable(table).idField()
        return self.getRecordEx(table, cols, idCol.eq(recordId))


    def updateRecord(self, table, record):
        self.checkdb()
        table = self.forceTable(table)
        table.beforeUpdate(record)
        fieldsCount = record.count()
        idFieldName = table.idFieldName()
        values = []
        cond   = ''
        recordId = None
        for i in range(fieldsCount):

#My insertion for 'rbImageMap' table
            if table.name() == 'rbImageMap':
                pair = self.escapeFieldName(record.fieldName(i)) + '=' + self.formatValue(record.field(i))
                if record.fieldName(i) == idFieldName:
                    cond = pair
                    recordId = record.value(i).toInt()[0]
                elif record.fieldName(i) == 'image':
                    pass
                else:
                    values.append(pair)
            else:
                pair = self.escapeFieldName(record.fieldName(i)) + '=' + self.formatValue(record.field(i))
                if record.fieldName(i) == idFieldName:
                    cond = pair
                    recordId = record.value(i).toInt()[0]
                else:
                    values.append(pair)
        stmt = 'UPDATE ' + table.name() + ' SET ' + (', '.join(values)) + ' WHERE ' + cond
###         print unicode(stmt).encode('cp866')
        self.query(stmt)
        return recordId


    def insertRecord(self, table, record):
        self.checkdb()
        table = self.forceTable(table)
        table.beforeInsert(record)
        fieldsCount = record.count()
        fields = []
        values = []
        for i in range(fieldsCount):
            if not record.value(i).isNull():
                fields.append(self.escapeFieldName(record.fieldName(i)))
                values.append(self.formatValue(record.field(i)))
        stmt = ('INSERT INTO ' +  table.name() +
                '(' + (', '.join(fields)) + ') '+
                'VALUES (' + (', '.join(values)) + ')')
###        print unicode(stmt).encode('cp866')
        recordId = self.query(stmt).lastInsertId().toInt()[0]
        idFieldName = table.idFieldName()
        record.setValue(idFieldName, QVariant(recordId))
        return recordId


    def insertRecordList(self, table, recordList):
        self.checkdb()
        table = self.forceTable(table)
        fields = []
        valuesList = []
        for record in recordList:
            fieldsCount = record.count()
            values = []
            for i in range(fieldsCount):
                if len(fields) < fieldsCount:
                    fields.append(self.escapeFieldName(record.fieldName(i)))
                values.append(self.formatValue(record.field(i)))
            valuesList.append('(' + (', '.join(values)) + ')')
        stmt = ('INSERT IGNORE INTO ' + table.name() + '(' + (', '.join(fields)) + ') ' + 'VALUES ' + ', '.join(valuesList))
        query = self.query(stmt)
        return query


    def insertOrUpdate(self, table, record):
        table = self.forceTable(table)
        idFieldName = table.idFieldName()
        if record.isNull(idFieldName):
            return self.insertRecord(table, record)
        else:
            return self.updateRecord(table, record)


    def deleteRecord(self, table, where):
        self.checkdb()
        table = self.forceTable(table)
        if table.hasField(CDocumentTable.dtfDeleted):
            self.markRecordsDeleted(table, where)
        else:
            stmt = 'DELETE FROM ' + table.name() + self.prepareWhere(where)
            self.query(stmt)


    def deleteRecordSimple(self, table, where):
        self.checkdb()
        table = self.forceTable(table)
        stmt = 'DELETE FROM '+table.name()+self.prepareWhere(where)
        self.query(stmt)


    def markRecordsDeleted(self, table, where):
        self.checkdb()
        table = self.forceTable(table)
#        table.beforeUpdate(record)
        stmt = 'UPDATE  '+table.name() + ' SET %s=1' % CDocumentTable.dtfDeleted;
        if table.hasField(CDocumentTable.dtfModifyDatetime):
            stmt += ', %s=NOW()' % CDocumentTable.dtfModifyDatetime;
        if table.hasField(CDocumentTable.dtfModifyUserId):
            stmt += ', %s=%s' %(CDocumentTable.dtfModifyUserId, (QtGui.qApp.userId or 'NULL'))
        whereEx = ['%s=0'% CDocumentTable.dtfDeleted]
        if isinstance(where, (list, tuple)):
            whereEx.extend(where)
        elif where:
            whereEx.append(where)
        stmt += ' ' + self.prepareWhere(whereEx)
        self.query(stmt)


    def updateRecords(self, table, expr, where = None):
        recQuery = None
        if table and expr:
            self.checkdb()
            table = self.forceTable(table)
            if isinstance(expr, QtSql.QSqlRecord):
                tmpRecord = QtSql.QSqlRecord(expr)
                sets = []
            else:
                tmpRecord = QtSql.QSqlRecord()
                sets = []
                if not isinstance(expr, (list, tuple)):
                    sets = [expr]
                else:
                    sets.extend(expr)
            table.beforeUpdate(tmpRecord)
            for i in xrange(tmpRecord.count()):
                sets.append(table[tmpRecord.fieldName(i)].eq(tmpRecord.value(i)))
            stmt = 'UPDATE ' + table.name() + ' SET ' + ','.join(sets) + self.prepareWhere(where)
            recQuery = self.query(stmt)
        return recQuery


    def updateRecordsNoDatetimeModifying(self, table, expr, where = None):
        recQuery = None
        if table and expr:
            self.checkdb()
            table = self.forceTable(table)
            if isinstance(expr, QtSql.QSqlRecord):
                tmpRecord = QtSql.QSqlRecord(expr)
                sets = []
            else:
                tmpRecord = QtSql.QSqlRecord()
                sets = []
                if not isinstance(expr, (list, tuple)):
                    sets = [expr]
                else:
                    sets.extend(expr)
            table.beforeUpdateNoDatetimeModifying(tmpRecord)
            for i in xrange(tmpRecord.count()):
                sets.append(table[tmpRecord.fieldName(i)].eq(tmpRecord.value(i)))
            stmt = 'UPDATE ' + table.name() + ' SET ' + ','.join(sets) + self.prepareWhere(where)
            recQuery = self.query(stmt)
        return recQuery


    def getSum(self, table, sumCol='*', where=''):
        stmt = self.selectStmt(table, 'SUM(%s)'%sumCol, where)
        query = self.query(stmt)
        if query.first():
            return query.value(0)
        else:
            return 0


    def getMax(self, table, maxCol='id', where=''):
        stmt = self.selectStmt(table, 'MAX(%s)'%maxCol, where)
        query = self.query(stmt)
        if query.first():
            return query.value(0)
        else:
            return None


    def getCurrentDatetime(self):
        query = self.query('SELECT NOW()')
        if query.first():
            return forceDateTime(query.value(0))
        else:
            return QDateTime.currentDateTime()


    def getCurrentDate(self):
        query = self.query('SELECT CURDATE()')
        if query.first():
            return forceDate(query.value(0))
        else:
            return QDate.currentDate()


    def getMin(self, table, maxCol='id', where=''):
        stmt = self.selectStmt(table, 'MIN(%s)'%maxCol, where)
        query = self.query(stmt)
        if query.first():
            return query.value(0)
        else:
            return None


    def getCount(self, table, countCol='1', where=''):
        stmt = self.selectStmt(table, 'COUNT(%s)'%countCol, where)
        query = self.query(stmt)
        if query.first():
            return query.value(0).toInt()[0]
        else:
            return 0


    def getDistinctCount(self, table, countCol='*', where=''):
        stmt = self.selectStmt(table, 'COUNT(DISTINCT %s)'%countCol, where)
        query = self.query(stmt)
        if query.first():
            return query.value(0).toInt()[0]
        else:
            return 0

    def getIdList(self, table, idCol='id', where='', order='', limit=None):
        stmt = self.selectStmt(table, idCol, where, order, limit)
        query = self.query(stmt)
        result = []
        while query.next():
            result.append(query.value(0).toInt()[0])
        return result


    def getDistinctIdList(self, table, idCol=['id'], where='', order='', limit=None):
        stmt = self.selectDistinctStmt(table, idCol, where, order, limit)
        query = self.query(stmt)
        result = []
        while query.next():
            result.append(query.value(0).toInt()[0])
        return result


    def getIdListGroupBy(self, table, idCol='id', where='', group='', order='', limit=None):
        stmt = self.selectStmtGroupBy(table, idCol, where, group, order, limit)
        query = self.query(stmt)
        result = []
        while query.next():
            result.append(query.value(0).toInt()[0])
        return result


#    def getIdList(self, table, idCol='id', where='', order=''):
#        stmt = self.selectStmt(table, idCol, where,  order)
#        query = self.query(stmt)
#        idColIdx = query.record().indexOf(idCol)
#        assert idColIdx>=0
#        result = []
#        while query.next():
#            result.append(query.value(idColIdx).toInt()[0])
#        return result


    def getRecordList(self, table, cols='*', where='', order='', limit=None):
        stmt = self.selectStmt(table, cols, where,  order, limit)
        res = []
        query = self.query(stmt)
        while query.next():
            record = query.record()
            res.append(CSqlRecord(record))
        return res


    def getRecordListHaving(self, table, cols='*', where='', having='', order='', limit=None):
        stmt = self.selectHavingStmt(table, cols, where, having, order, limit)
        res = []
        query = self.query(stmt)
        while query.next():
            res.append(query.record())
        return res


    def getRecordListGroupBy(self, table, cols='*', where='', group='', order='', limit=None):
        stmt = self.selectStmtGroupBy(table, cols, where, group, order, limit)
        res = []
        query = self.query(stmt)
        while query.next():
            res.append(query.record())
        return res


    def getDistinctRecordList(self, table, cols='*', where='', order='', limit=None):
        stmt = self.selectDistinctStmt(table, cols, where,  order, limit)
        res = []
        query = self.query(stmt)
        while query.next():
            res.append(query.record())
        return res


    def translate(self, table, keyCol, keyVal, valCol, nonDeleted=False):
        if keyCol == 'id' and keyVal is None:
            return None
        self.checkdb()
        table = self.forceTable(table)
        if not isinstance(keyCol, CField):
            keyCol = table[keyCol]
        where = [keyCol.eq(keyVal)]
        if nonDeleted:
            where.append(table['deleted'].eq(0))
        record = self.getRecordEx(table, valCol, where)
        if record:
            return record.value(0)
        else:
            return None


    def copyDepended(self, table, masterKeyCol, currentId, newId):
        self.checkdb()
        table = self.forceTable(table)
        if not isinstance(masterKeyCol, CField):
            masterKeyCol = table[masterKeyCol]
        masterKeyColName = masterKeyCol.field.name()
        result = []
        stmt = self.selectStmt(table, '*', masterKeyCol.eq(currentId), 'id')
        qquery = self.query(stmt)
        while qquery.next():
            record = qquery.record()
            record.setNull('id')
            record.setValue(masterKeyColName, toVariant(newId))
            result.append( self.insertRecord(table, record) )
        return result


    def getDescendants(self, table, groupCol, recordId, where=''):
        self.checkdb()
        table = self.forceTable(table)
        group = table[groupCol]

        result = set([recordId])
        parents = set([recordId])

        while parents:
            isChild = group.inlist(parents)
            childrenWhere = self.joinAnd([where, isChild]) if where else isChild
            children = set(self.getIdList(table, where=childrenWhere))
            newChildren = children-result
            result |= newChildren
            parents = newChildren
        return list(result)


    def getLeafes(self, table, groupCol, recordId, where=''):
        children = self.getDescendants(table, groupCol, recordId, where)
        tableParent   = self.forceTable(table).alias('P')
        tableChildren = self.forceTable(table).alias('C')
        table = tableParent.leftJoin(tableChildren, tableChildren[groupCol].eq(tableParent['id']))
        cond = [ tableParent['id'].inlist(children),
                 tableChildren['id'].isNull(),
               ]
        leafes = self.getIdList(table,
                                idCol=tableParent['id'].name(),
                                where=self.joinAnd(cond)
                               )
        return leafes


    def getTheseAndParents(self, table, groupCol, idList):
        self.checkdb()
        table = self.forceTable(table)
        idField    = table['id']
        groupField = table[groupCol]

        result = set(idList)
        children = idList

        while children:
            parents = set(self.getDistinctIdList(table,
                                                 idCol=groupCol,
                                                 where=[idField.inlist(children), groupField.isNotNull()]))
            newParents = parents-result
            result |= newParents
            children = newParents
        return list(result)


    def countRefs(self, table, id):
        raise NotImplementedError('abstract method call')


    def selectRefs(self, table, id):
        raise NotImplementedError('abstract method call')

    def toDate(self, name):
        raise NotImplementedError('abstract method call')

    def dateAdd(self, name, a, b):
        raise NotImplementedError('abstract method call')


def _convDate(val):
    result = val.toDate().toString(Qt.ISODate)
    if not result:
        result = val.toString()
    else:
        result = decorateString(result)
    return result


def _convTime(val):
    result = val.toTime().toString(Qt.ISODate)
    if not result:
        result = val.toString()
    else:
        result = decorateString(result)
    return result


def _convDateTime(val):
    result = val.toDateTime().toString(Qt.ISODate)
    if not result:
        result = val.toString()
    else:
        result = decorateString(result)
    return result


class CMySqlDatabase(CDatabase):
    driverName = 'QMYSQL'
    limit1 = 'LIMIT 0, %d'
    limit2 = 'LIMIT %d, %d'
    CR_SERVER_GONE_ERROR = 2006
    CR_SERVER_LOST = 2013
    S_TRIGGER_MYSQL_ERRNO = 20001
    name = 'mysql'

    def __init__(self, serverName, serverPort, databaseName, userName, password, connectionName=None, compressData=False, logger=None):
        CDatabase.__init__(self, logger)
        self.preparedQueryCache = CPreparedQueryCache(100)
        self.preparedQueryCache.prepare = self.prepare
        db = self.createConnection(connectionName)
        options = ['CLIENT_INTERACTIVE=1']
        if compressData:
            options.append('CLIENT_COMPRESS=1')
        if options:
            db.setConnectOptions(';'.join(options))
        self.connect(db, serverName, serverPort, databaseName, userName, password)
        self.query('SET NAMES \'utf8\' COLLATE \'utf8_general_ci\';')
        # это эквивалентно
        # SET character_set_client=utf8;
        # SET character_set_connection=utf8;
        # SET character_set_results=utf8;
        self.query('SET SQL_AUTO_IS_NULL=0;')
        self.query('SET SQL_MODE=\'\';')
        self.query('SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;')
        self.query('SET interactive_timeout = GREATEST(CONVERT(@@interactive_timeout, SIGNED), 24*60*60);')

    def close(self):
        self.preparedQueryCache.clear()
        CDatabase.close(self)



    def escapeFieldName(self, name):
        u = unicode(name)
        if u.startswith('`') and u.endswith('`'):
            return u
        else:
            return '`'+u+'`'


    escapeTableName = escapeFieldName
    escapeSchemaName = escapeFieldName


    def onError(self, stmt, sqlError=None):
        if sqlError and sqlError.number() in (CMySqlDatabase.CR_SERVER_GONE_ERROR, CMySqlDatabase.CR_SERVER_LOST):
            app = QtGui.qApp
            QtGui.QMessageBox.critical(app.mainWindow,
                u'Критическая ошибка',
                u'Потеряна связь с сервером.\nНеобходимо перезапустить приложение')
            try:
                CDatabase.onError(self, stmt, sqlError)
            finally:
                app.doneTrace()
                self.db = None
        elif sqlError and sqlError.number() == CMySqlDatabase.S_TRIGGER_MYSQL_ERRNO:
            CDatabase.onErrorTrigger(self, stmt, sqlError)
        else:
            CDatabase.onError(self, stmt, sqlError)


    def isProcedureExists(self, procedureName, schemaName=None):
        stmt = 'SELECT NULL FROM INFORMATION_SCHEMA.ROUTINES' \
               ' WHERE ROUTINE_SCHEMA = %s'                   \
                 ' AND ROUTINE_NAME = %s'                     \
                 ' AND ROUTINE_TYPE = \'PROCEDURE\'' % (decorateString(schemaName) if schemaName else 'DATABASE()',
                                                        decorateString(procedureName)
                                                       )
        return self.query(stmt).next()


    def prepareLimit(self, limit):
        if isinstance(limit, (list, tuple)):
            assert len(limit) == 2
            return self.limit2 % limit
        elif isinstance(limit, int):
            return self.limit1 % limit
        else:
            return ''


    def selectStmt(self, table, fields='*', where='', order='', limit=None):
        self.checkdb()
        tableName = self.getTableName(table)
        return ' '.join([
            'SELECT', self.prepareFieldList(fields),
            'FROM', tableName,
            self.prepareWhere(where),
            self.prepareOrder(order),
            self.prepareLimit(limit)])


    def selectHavingStmt(self, table, fields='*', where='', having='', order='', limit=None):
        self.checkdb()
        tableName = self.getTableName(table)
        return ' '.join([
            'SELECT', self.prepareFieldList(fields),
            'FROM', tableName,
            self.prepareWhere(where),
            self.prepareHaving(having),
            self.prepareOrder(order),
            self.prepareLimit(limit)])


    def selectDistinctStmt(self, table, fields='*', where='', order='', limit=None):
        self.checkdb()
        tableName = self.getTableName(table)
        return ' '.join([
            'SELECT DISTINCT', self.prepareFieldList(fields),
            'FROM', tableName,
            self.prepareWhere(where),
            self.prepareOrder(order),
            self.prepareLimit(limit)])


    def updateRecord(self, table, record):
        self.checkdb()
        table = self.forceTable(table)
        table.beforeUpdate(record)
        fieldsCount = record.count()
        idFieldNameIndex = record.indexOf(table.idFieldName())
        if idFieldNameIndex < 0:
            raise CDatabaseException(CDatabase.errNoIdField % table.name())
        if record.isNull(idFieldNameIndex):
            raise CDatabaseException(CDatabase.errIdFieldIsNull % table.name())
        parts  = []
        values = []
        cond   = ''
        recordId = None
        for i in xrange(fieldsCount):
            if i == idFieldNameIndex:
                cond = self.escapeFieldName(record.fieldName(i)) + '=?'
                recordId = record.value(i)
            elif record.value(i).typeName() == 'QByteArray' and not record.value(i).isNull():
                parts.append(self.escapeFieldName(record.fieldName(i)) + '=UNHEX(?)')
                values.append(record.value(i).toByteArray().toHex())
            else:
                parts.append(self.escapeFieldName(record.fieldName(i)) + '=?')
                values.append(record.value(i))
        if type(record) == CSqlRecord and not record.isDirty():
            return recordId.toInt()[0]
        values.append(recordId)
        stmt = 'UPDATE ' + table.name() + ' SET ' + ', '.join(parts) + ' WHERE ' + cond
        preparedQuery = self.preparedQueryCache.get(stmt)
        for i, value in enumerate(values):
            preparedQuery.bindValue(i, values[i])
        self.execPreparedQuery(preparedQuery)
        return recordId.toInt()[0]


    def insertRecord(self, table, record):
        self.checkdb()
        table = self.forceTable(table)
        table.beforeInsert(record)
        fieldsCount = record.count()
        fields = []
        placeholders = []
        values = []
        for i in range(fieldsCount):
            value = record.value(i)
            if not value.isNull():
                fields.append(self.escapeFieldName(record.fieldName(i)))
                if value.typeName() == 'QByteArray':
                    values.append(value.toByteArray().toHex())
                    placeholders.append('UNHEX(?)')
                else:
                    values.append(value)
                    placeholders.append('?')
        stmt = 'INSERT INTO ' + table.name() + '(' + ', '.join(fields) + ') ' + 'VALUES (' + ', '.join(placeholders) + ')'
        preparedQuery = self.preparedQueryCache.get(stmt)
        for i, value in enumerate(values):
            preparedQuery.bindValue(i, values[i])
        self.execPreparedQuery(preparedQuery)
        recordId = preparedQuery.lastInsertId()
        idFieldName = table.idFieldName()
        record.setValue(idFieldName, recordId)
        return recordId.toInt()[0]


    def countRefs(self, table, id):
        u'Подсчёт числа важных ссылок на запись в таблице table с заданным id; это небыстро!'
        self.checkdb()
        table = self.forceTable(table)
        stmt = 'CALL countRefs(NULL, %s, %s)' % (decorateString(table.name()),
                                                 str(id) if id is not None else 'NULL'
                                                )
        query = self.query(stmt)
        if query.first():
            record=query.record()
            return record.value(0).toInt()[0]
        else:
            return 0


    def selectRefs(self, table, id):
        u'список важных ссылок на запись в таблице table с заданным id; это ещё тормознее!'
        self.checkdb()
        table = self.forceTable(table)
        stmt = 'CALL selectRefs(NULL, %s, %s)' % (decorateString(table.name()),
                                                  str(id) if id is not None else 'NULL'
                                                )
        res = []
        query = self.query(stmt)
        while query.next():
            res.append(query.record())
        return res


    def rbChecksum(self, tableName):
        return self.dbChecksum(tableName, 'code, name', '')

    def dbChecksum(self, tableName, fieldName,  filter):
        if filter:
            wherePart = 'WHERE '+filter
        else:
            wherePart = ''
        query = QtGui.qApp.db.query('SELECT SUM(CRC32(CONCAT_WS(CHAR(127), id, %s))) FROM %s %s' % (fieldName, tableName, wherePart))
        if query.next():
            record = query.record()
            return forceLong(record.value(0))
        else:
            return None

    def toDate(self, name):
        return 'DATE(%s)'%name

    def dateAdd(self, name, intervalType, count):
        return 'DATE_ADD({fieldName}, INTERVAL {count} {intervalType})'.format(fieldName=name,
                                                                                   intervalType=intervalType,
                                                                                   count=count)

class CPostgresqlDatabase(CDatabase):
    driverName = 'QPSQL'
    limit1 = 'LIMIT %d'
    limit2 = 'LIMIT %d OFFSET %d'
    name = 'postgres'

    convMethod = {
                QVariant.Int       : lambda val: unicode(val.toInt()[0]),
                QVariant.UInt      : lambda val: unicode(val.toUInt()[0]),
                QVariant.LongLong  : lambda val: unicode(val.toLongLong()[0]),
                QVariant.ULongLong : lambda val: unicode(val.toULongLong()[0]),
                QVariant.Double    : lambda val: unicode(val.toDouble()[0]),
                QVariant.Bool      : lambda val: u'1' if val.toBool() else u'0',
                QVariant.Char      : lambda val: decorateString(val.toString()),
                QVariant.String    : lambda val: decorateString(val.toString()),
                #QVariant.Date      : lambda val: decorateString(val.toDate().toString(Qt.ISODate)),
                #QVariant.Time      : lambda val: decorateString(val.toTime().toString(Qt.ISODate)),
                #QVariant.DateTime  : lambda val: decorateString(val.toDateTime().toString(Qt.ISODate)),
                QVariant.Date      : _convDate,
                QVariant.Time      : _convTime,
                QVariant.DateTime  : _convDateTime,
                QVariant.ByteArray : lambda val: 'x\''+str(val.toByteArray().toHex())+'\'',
             }



    def __init__(self, serverName, serverPort, databaseName, userName, password, connectionName=None, compressData=False, logger=None):
        CDatabase.__init__(self, logger)
        db = self.createConnection(connectionName)
        self.connect(db, serverName, serverPort, databaseName, userName, password)
        self.preparedQueryCache = CPreparedQueryCache(100)
        self.preparedQueryCache.prepare = self.prepare


    def isProcedureExists(self, procedureName, schemaName=None):
        return False


    def escapeFieldName(self, name):
        name = unicode(name)
        if name in ('order'):
            name = u'"%s"'%name
        return name


    def prepareLimit(self, limit):
        if isinstance(limit, (list, tuple)):
            assert len(limit) == 2
            off, lim = limit
            return self.limit2 % (lim, off)
        elif isinstance(limit, int):
            return self.limit1 % limit
        else:
            return ''


    def selectStmt(self, table, fields='*', where='', order='', limit=None):
        self.checkdb()
        tableName = self.getTableName(table)
        return ' '.join([
            'SELECT', self.prepareFieldList(fields),
            'FROM', tableName,
            self.prepareWhere(where),
            self.prepareOrder(order),
            self.prepareLimit(limit)])


    def selectDistinctStmt(self, table, fields='*', where='', order='', limit=None):
        self.checkdb()
        if type(fields) in (str, unicode):
            fields = fields.split(',')
        if order:
            fieldList = fields[:]
            if type(order) != list:
                order = order.split(',')
            for o in order:
                o = o.strip().split(' ')[0]
                if o not in fieldList:
                    fieldList.append(o)
            innerStmt = ' '.join(['SELECT DISTINCT ON (%s) %s'%(','.join(fields), ', '.join(fieldList)),
                'FROM', self.getTableName(table),
                self.prepareWhere(where),
                ])
            return u'select * from (%s) as request %s'%(innerStmt, ' '.join([self.prepareOrder([op.split('.')[-1] for op in order]), self.prepareLimit(limit)] ))
        else:
            tableName = self.getTableName(table)
            return ' '.join([
                'SELECT DISTINCT', self.prepareFieldList(fields),
                'FROM', tableName,
                self.prepareWhere(where),
                self.prepareOrder(order),
                self.prepareLimit(limit)])

    def selectStmtGroupBy(self, table, fields='*', where='', group='', order='', limit=None):
        self.checkdb()
        if type(fields) in (str, unicode):
            fields = fields.split(',')
        fieldList = fields[:]
        if order:
            if type(order) != list:
                order = order.split(',')
            for o in order:
                o = o.strip().split(' ')[0]
                if o not in [unicode(f).split(' ')[-1] for f in fieldList]:
                    fieldList.append(o)
        if group:
            if type(group) != list:
                group = group.split(',')
            for o in group:
                o = o.strip().split(' ')[0]
                if o not in [unicode(f).split(' ')[-1] for f in fieldList]:
                    fieldList.append(o)
        table = self.forceTable(table)
        return ' '.join([
            'SELECT', self.prepareFieldList(fieldList),
            'FROM', table.name(),
            self.prepareWhere(where),
            self.prepareGroup(group),
            self.prepareOrder(order)])


    def record(self, tableName):
        res = self.db.record(tableName)
        if res.isEmpty():
            raise CDatabaseException(CDatabase.errTableNotFound % tableName)
        return res

    def rbChecksum(self, tableName):
        return self.dbChecksum(tableName, 'code,name')

    def dbChecksum(self, tableName, fieldName,  filter = None):
        filterString = 'WHERE %s'%filter if filter else ''
        fields = ' || '.join(fieldName.split(','))
        query = QtGui.qApp.db.query("select sum(('x' || md5(%s))::bit(32)::bigint) as hash from %s %s" % (fields, tableName, filterString))
        if query.next():
            record = query.record()
            return forceLong(record.value(0))
        else:
            return 0

    def toDate(self, name):
        return 'date %s' %name

    def dateAdd(self, name, intervalType, count):
        return "{fieldName} + interval '{count} {intervalType}'".format(fieldName=name,
                                                                                   intervalType=intervalType,
                                                                                   count=count)

    def insertRecord(self, table, record):
#        self.checkdb()
#        table = self.forceTable(table)
#        table.beforeInsert(record)
#        fieldsCount = record.count()
#        fields = []
#        values = []
#        for i in range(fieldsCount):
#            value = record.value(i)
#            if not record.value(i).isNull():
#                fields.append(self.escapeFieldName(record.fieldName(i)))
#                values.append(value)
#        stmt = 'INSERT INTO ' +  table.name() + '(' + ', '.join(fields) + ') '+'VALUES (' + ', '.join(['?']*len(fields)) + ') RETURNING %s'%table.idField().fieldName
#        preparedQuery = self.preparedQueryCache.get(stmt)
#        for i, value in enumerate(values):
#            preparedQuery.bindValue(i, values[i])
#        self.execPreparedQuery(preparedQuery)
#        recordId = None
#        if preparedQuery.next():
#            recordId = preparedQuery.record().value(0)
#        else:
#            raise CDatabaseException(u'Ошибка при попытке записать данные')
#        idFieldName = table.idFieldName()
#        record.setValue(idFieldName, recordId)
#        return recordId.toInt()[0]

        #в целях дебага не буду пользоваться подготовленными запросами
        self.checkdb()
        table = self.forceTable(table)
        table.beforeInsert(record)
        fieldsCount = record.count()
        fields = []
        values = []
        for i in range(fieldsCount):
            if not record.value(i).isNull():
                fields.append(self.escapeFieldName(record.fieldName(i)))
                values.append(self.formatValue(record.field(i)))
        stmt = ('INSERT INTO ' +  table.name() +
                '(' + (', '.join(fields)) + ') '+
                'VALUES (' + (', '.join(values)) + ') returning id')
        query = self.query(stmt)
        recordId = None
        if query.next():
            recordId = query.record().value(0)
        else:
            raise CDatabaseException(u'Ошибка при попытке записать данные')
        idFieldName = table.idFieldName()
        record.setValue(idFieldName, recordId)
        return recordId.toInt()[0]

class CInterbaseDatabase(CDatabase):
    driverName = 'QIBASE'
    limit1 = 'FIRST %d'
    limit2 = 'FIRST %d SKIP %d'
    name = 'interbase'
    convMethod = {
                    QVariant.Int       : lambda val: unicode(val.toInt()[0]),
                    QVariant.UInt      : lambda val: unicode(val.toUInt()[0]),
                    QVariant.LongLong  : lambda val: unicode(val.toLongLong()[0]),
                    QVariant.ULongLong : lambda val: unicode(val.toULongLong()[0]),
                    QVariant.Double    : lambda val: unicode(val.toDouble()[0]),
                    QVariant.Bool      : lambda val: u'1' if val.toBool() else u'0',
                    QVariant.Char      : lambda val: decorateString(val.toString()),
                    QVariant.String    : lambda val: decorateString(val.toString()),
                    QVariant.Date      : lambda val: decorateString(val.toDate().toString('dd.MM.yyyy')), #!!!
                    QVariant.Time      : lambda val: decorateString(val.toTime().toString('hh:mm:ss')),
                    QVariant.DateTime  : lambda val: decorateString(val.toDateTime().toString('dd.MM.yyyy hh:mm:ss')),
                    QVariant.ByteArray : lambda val: 'x\''+str(val.toByteArray().toHex())+'\'',
                 }

    def __init__(self, serverName, serverPort, databaseName, userName, password, connectionName=None, logger=None):
        CDatabase.__init__(self, logger)
        db = self.createConnection(connectionName)
        db.setConnectOptions('ISC_DPB_LC_CTYPE=Win_1251')
        self.connect(db, serverName, serverPort, databaseName, userName, password)


    def escapeFieldName(self, name):
        u = unicode(name)
        if u.startswith('"') and u.endswith('"'):
            return u
        else:
            return '"'+u.replace('"', '""')+'"'


    escapeTableName = escapeFieldName

    def prepareLimit(self, limit):
        if isinstance(limit, (list, tuple)):
            assert len(limit) == 2
            return self.limit2 % (limit[1], limit[0])
        elif isinstance(limit, int):
            return self.limit1 % limit
        else:
            return ''


    def selectStmt(self, table, fields='*', where='', order='', limit=None):
        self.checkdb()
        table = self.forceTable(table)
        return ' '.join([
            'SELECT',
            self.prepareLimit(limit),
            self.prepareFieldList(fields),
            'FROM', table.name(),
            self.prepareWhere(where),
            self.prepareOrder(order),
            ])



class CODBCDatabase(CDatabase):
    driverName = 'QODBC3'
#    limit1 = 'FIRST %d'
#    limit2 = 'FIRST %d SKIP %d'

    def __init__(self, serverName, serverPort, databaseName, userName, password, connectionName=None, logger=None):
        CDatabase.__init__(self)
        db = self.createConnection(connectionName)
        db.setConnectOptions('SQL_ATTR_ACCESS_MODE=SQL_MODE_READ_ONLY')
        self.connect(db, serverName, serverPort, databaseName, userName, password)


    def escapeFieldName(self, name):
        u = unicode(name)
        if u.startswith('"') and u.endswith('"'):
            return u
        else:
            return '"'+u.replace('"', '""')+'"'


    escapeTableName = escapeFieldName


#    def prepareLimit(self, limit):
#        if isinstance(limit, (list, tuple)):
#            assert len(limit) == 2
#            return self.limit2 % (limit[1], limit[0])
#        elif isinstance(limit, int):
#            return self.limit1 % limit
#        else:
#            return ''

    def selectStmt(self, table, fields='*', where='', order='', limit=None):
        self.checkdb()
        table = self.forceTable(table)
        return ' '.join([
            'SELECT', self.prepareFieldList(fields),
            'FROM', table.name(),
            self.prepareWhere(where),
            self.prepareOrder(order),
#            self.prepareLimit(limit)
            ])



class CSqliteDatabase(CDatabase):
    driverName = 'QSQLITE'

    def __init__(self, serverName, serverPort, databaseName, userName, password, connectionName=None, logger=None):
        CDatabase.__init__(self, logger)
        db = self.createConnection(connectionName)
        self.connect(db, serverName, serverPort, databaseName, userName, password)


    def escapeFieldName(self, name):
        u = unicode(name)
        if u.startswith('"') and u.endswith('"'):
            return u
        else:
            return '"'+u.replace('"', '""')+'"'


    escapeTableName = escapeFieldName


    def prepareLimit(self, limit):
        if isinstance(limit, (list, tuple)):
            assert len(limit) == 2
            return 'FIRST %d OFFSET %d' % (limit[1], limit[0])
        elif isinstance(limit, int):
            return 'FIRST %d' % limit
        else:
            return ''


    def selectStmt(self, table, fields='*', where='', order='', limit=None):
        self.checkdb()
        table = self.forceTable(table)
        return ' '.join([
            'SELECT', self.prepareFieldList(fields),
            'FROM', table.name(),
            self.prepareWhere(where),
            self.prepareOrder(order),
            self.prepareLimit(limit)
            ])


#WFT? какие такие fakeValues? они же будут вытестены из кеша!
#Нет, не будут, т.к. вытесняется только то, что есть в queue, а fakeValues не появляются в queue
class CRecordCache(object):
    """
    Кэш записей QSqlRecord в виде словаря, в общем случае может быть использован для хранения любых обектов.
    Имеет методы для добавления объекта в кэш, получения объекта по ключу, проверки наличия объекта. Автоматически
    вытесняет старые объекты из кэша при превышении объёма. Также поддерживает добавление в кэш объектов fakeValues,
    которые не будут вытесняться из кэша и не отслеживаются при проверке занятого объёма
    """
    def __init__(self, capacity=200, fakeValues=[]):
        self.map = {}               #: Основной элемент класса - словарь, содержащий кэш
        self.queue = []             #: Список ключей, содержащихся в map, для поддержки вытеснения старых элементов
        self.fakeKeys = []          #: Список ключей элементов кэша, которые не будут вытесняться из него
        self.capacity = capacity    #: Максимальное количество элементов в кэше
        #: Список пар (ключ, значение) для добавления в кэш, эти записи не будут вытесняться из кэша
        self.fakeValues = fakeValues
        if fakeValues:
            self.loadFakeValues(fakeValues)


    def loadFakeValues(self, fakeValues):
        """
        Загрузка объектов fakeValues в кэш

        :param fakeValues: список пар (ключ, значение) для добавления в кэш
        :type fakeValues: list
        """
        if fakeValues:
            self.clearFakeValues()
            for fakeKey, fakeRecord in fakeValues:
                self.fakeKeys.append(fakeKey)
                self.map[fakeKey] = fakeRecord
        else:
            self.clearFakeValues()


    def clearFakeValues(self):
        """
        Удаление fakeValues из кэша
        """
        for key in self.fakeKeys:
            if key in self.map:
                del (self.map[key])
        self.fakeKeys = []


    def invalidate(self):
        """
        Очистка кэша и перезагрузка fakeValues
        """
        self.map = {}
        self.queue = []
        self.fakeKeys = []
        if self.fakeValues:
            self.loadFakeValues(self.fakeValues)


    def has_key(self, key):
        """
        Проверка наличия ключа в кэше

        :param key: проверяемый ключ
        """
        return self.map.has_key(key)


    def get(self, key):
        """
        Получение записи из кэша по ключу

        :param key: ключ, по которому требуется получить значение
        """
        return self.map.get(key, None)


    def put(self, key, record):
        """
        Добавление записи в кэш

        :param key: ключ записи для добавления в словарь кэша
        :param record: добавляемая в словарь кэша запись
        """
        if self.map.has_key(key):
            self.map[key] = record
        else:
            if self.capacity and len(self.queue) >= self.capacity:
                top = self.queue[0]
                del(self.queue[0])
                del(self.map[top])
            self.queue.append(key)
            self.map[key] = record


class CTableRecordCache(CRecordCache):
    """
    Создаёт таблицу одного из типов CTable, CTableAlias, CJoin, CDocumentTable. Загружает записи из БД в созданную
    таблицу, позволяет получить запись по ID из кэша или из БД
    """
    #WFT? какие такие fakeValues? ониже будут вытестены из кеша!
    def __init__(self, database, table, cols='*', capacity=300, fakeValues=[]):
        CRecordCache.__init__(self, capacity, fakeValues)
        # self.database = database                        #: Объект БД типа CMySqlDatabase
        self.table = QtGui.qApp.db.forceTable(table)    #: Таблица
        self.cols = cols if not isinstance(cols, (list, tuple)) else ', '.join(cols)    #: Список полей таблицы
        self.idCol = QtGui.qApp.db.mainTable(self.table).idField()  #: Поле ID, объект типа CField


    def fetch(self, idList):
        """
        Загрузка данных из БД в кэш

        :param idList: список ID записей для загрузки из БД
        :type idList: int
        """
        filteredIdList = [recordId for recordId in idList if not self.has_key(recordId)]
        if filteredIdList:
            #records = self.database.getRecordList(self.table, self.cols, self.idCol.inlist(idList))
            records = QtGui.qApp.db.getRecordList(self.table, self.cols, self.idCol.inlist(idList)) #ymd
            fieldName = self.idCol.field.name()
            for record in records:
                recordId = record.value(fieldName).toInt()[0]
                self.put(recordId, record)


    def weakFetch(self, recordId, idList):
        """
        Загрузка записей idList в случае если recordId отсутствует в кэше

        :param recordId: ID записи, наличие которой проверяется в кэше
        :type recordId: int
        :param idList: список ID записей для загрузки из БД
        :type idList: int
        """
        if not self.has_key(recordId):
            self.fetch(idList)


    def get(self, recordId):
        """
        Получение записи по recordId. Если запись есть в кэше - будет возвращено значение из кэша, если записи в кэше
        нет - она будет получена из БД и помещена в кэш

        :param recordId: ID получаемой записи
        :type recordId: int
        :return: запись QSqlRecord, соответствующая переданному recordId
        :rtype: int
        """
        if type(recordId) == QVariant:
            recordId = recordId.toInt()[0]
        res = CRecordCache.get(self, recordId)
        if res is None:
            #res = self.database.getRecordEx(self.table, self.cols, self.idCol.eq(recordId))
            res = QtGui.qApp.db.getRecordEx(self.table, self.cols, self.idCol.eq(recordId)) #ymd
            self.put(recordId, res)
        return res


class CTableRecordCacheEx(CTableRecordCache):
    def __init__(self, database, table, cols='*', capacity=300, fakeValues=[], idFieldName='id'):
        CTableRecordCache.__init__(self, database, table, cols, capacity, fakeValues)
        QtGui.qApp.db.mainTable(self.table).setIdFieldName(idFieldName)
        self.idCol = QtGui.qApp.db.mainTable(self.table).idField()  #: Поле к примеру UUID, объект типа CField


    def get(self, recordId):
        if type(recordId) == QVariant:
            recordId = forceStringEx(recordId)
        res = CRecordCache.get(self, recordId)
        if res is None:
            res = QtGui.qApp.db.getRecordEx(self.table, self.cols, self.idCol.eq(recordId))
            self.put(recordId, res)
        return res


# # # # #

def undotLikeMask(val):
    if val.endswith('...'):
        val = val[:-3]+'%'
    return val.replace('...','%').replace('%%', '%')


def addCondLike(cond, field, val):
    if val.strip(' .'):
        if val.find('...') != -1:
            cond.append(field.like(val.strip()))
        else:
            cond.append(field.eq(val.strip()))

# # # # #

def addCondEq(cond, field, val):
    if val:
        cond.append(field.eq(val))

def addDateInRange(cond, field, begDate, endDate):
    if begDate:
        cond.append(field.ge(begDate))
    if endDate:
        cond.append(field.lt(endDate.addDays(1)))


def connectDataBase(driverName, serverName, serverPort, databaseName, userName, password, connectionName=None, compressData=False, logger=None):
    driverName = unicode(driverName).upper()
    if driverName == 'MYSQL':
# ymd st
        db = CMySqlDatabase(serverName, serverPort, databaseName, userName, password, connectionName, compressData=compressData, logger=logger)
        db.setSonnectionIDGL()
        return db
# ymd end
    elif driverName == 'POSTGRES':
        return CPostgresqlDatabase(serverName, serverPort, databaseName, userName, password, connectionName, compressData=compressData, logger=logger)
    elif driverName in ('INTERBASE', 'FIREBIRD'):
        return CInterbaseDatabase(serverName, serverPort, databaseName, userName, password, connectionName, logger=logger)
    elif driverName == 'ODBC':
        return CODBCDatabase(serverName, serverPort, databaseName, userName, password, connectionName)
    elif driverName == 'SQLITE':
        return CSqliteDatabase(serverName, serverPort, databaseName, userName, password, connectionName, logger=logger)
    else:
        raise CDatabaseException(CDatabase.errUndefinedDriver % driverName)
    

def checkViewURN(urn):
    db = QtGui.qApp.db
    stmt = u"""select * from information_schema.VIEWS v where v.TABLE_SCHEMA = '{}' and v.TABLE_NAME like '{}'""".format(unicode(db.db.databaseName()), forceString(urn.split('.`')[-1].replace('`','')))
    query = db.query(stmt)
    if query.next():
        return True
    else:
        return False
