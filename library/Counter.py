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
import logging
import random

from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import SIGNAL, pyqtSignature, QDate, QObject, QTimer, QThread, pyqtSignal, QEventLoop, QVariant

from library.Utils import forceBool, forceInt, forceRef, forceString, forceDate
from library.plugins import hook
from library import database

__all__ = [ 'CCounterController',
          ]


class ProlongCounterWorker(QObject):
    finished = pyqtSignal()
    gotCounterValueCacheId_signal = pyqtSignal('int')
    resetCounterValueCacheId_signal = pyqtSignal('bool')
    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self.timer = None
        self.idList = set()
        self.db = None

    def __del__(self):
        if self.db:
            connectionName = self.db.db.connectionName()
            self.db.close()
            QtSql.QSqlDatabase.removeDatabase(connectionName)
        if self.timer:
            self.timer.stop()

    def getCounterValueCacheId(self, counterId, qvdate):
        if not self.db:
            self.openDatabase()
        date = forceDate(qvdate)
        cacheId = getCounterValueCacheId(self.db, counterId, date)
        self.gotCounterValueCacheId_signal.emit(cacheId)

    def resetCounterValueCacheId(self, cacheId):
        query = self.db.query('SELECT resetCounterValueCacheReservation(%d)' % cacheId)
        if query.next():
            result = forceBool(query.record().value(0))
        else:
            result = False
        self.resetCounterValueCacheId_signal.emit(result)

    @hook
    def prolongReservation(self):
        for counterValueCacheId in self.idList:
            try:
                self.db.query('SELECT prolongateCounterValueCacheReservation(%d)' % counterValueCacheId)
            except:
                QtGui.qApp.logCurrentException()

    def addValueCacheId(self, cacheId):
        if not self.db:
            self.openDatabase()
        self.idList.add(cacheId)

    def removeValueCacheId(self, cacheId):
        self.idList.remove(cacheId)
        if not self.idList and self.db:
            self.db.close()
            self.db = None

    def openDatabase(self):
        connectionName = "ProlongCounterWorker_" + str(random.randint(0, 100000))
        preferences = QtGui.qApp.preferences
        self.db = database.connectDataBase(preferences.dbDriverName,
                                           preferences.dbServerName,
                                           preferences.dbServerPort,
                                           preferences.dbDatabaseName,
                                           preferences.dbUserName,
                                           preferences.dbPassword,
                                           connectionName=connectionName,
                                           compressData=preferences.dbCompressData,
                                           logger=logging.getLogger('DB') if QtGui.qApp.logSql else None
                                           )
        if not self.db:
            raise Exception('CounterController: No database available for prolongate query!')

    def start(self):
        self.timer = QTimer()
        self.timer.setInterval(240000)
        self.connect(self.timer, SIGNAL('timeout()'), self.prolongReservation)
        self.timer.start()

    def stop(self):
        if self.timer:
            self.timer.stop()
        if self.db:
            connectionName = self.db.db.connectionName()
            self.db.close()
            QtSql.QSqlDatabase.removeDatabase(connectionName)
            self.db = None
        self.finished.emit()


class CCounterController(QObject):
    start = pyqtSignal()
    stop = pyqtSignal()
    addValueCacheId = pyqtSignal('int')
    removeValueCacheId = pyqtSignal('int')
    getCounterValueCacheId_signal = pyqtSignal('int', 'QVariant')
    resetCounterValueCacheId_signal = pyqtSignal('int')

    @hook
    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self.counterValueCacheId = None
        self.reservation = set()
        self.lastReservationId = None
        self.thread = QThread()
        self.worker = ProlongCounterWorker()
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.start)
        self.stop.connect(self.worker.stop)
        self.addValueCacheId.connect(self.worker.addValueCacheId)
        self.removeValueCacheId.connect(self.worker.removeValueCacheId)
        self.worker.finished.connect(self.thread.quit)
        self.getCounterValueCacheId_signal.connect(self.worker.getCounterValueCacheId)
        self.worker.gotCounterValueCacheId_signal.connect(self.gotCounterValueCacheId)
        self.resetCounterValueCacheId_result = None
        self.worker.resetCounterValueCacheId_signal.connect(self.catchResetCounterValueCacheId)
        self.resetCounterValueCacheId_signal.connect(self.worker.resetCounterValueCacheId)
        self.thread.start()

    def __del__(self):
        if self.thread.isRunning():
            self.thread.quit()
            self.thread.wait(5000)

    def gotCounterValueCacheId(self, value):
        self.counterValueCacheId = value

    def catchResetCounterValueCacheId(self, result):
        self.resetCounterValueCacheId_result = result

    @hook
    def getCounterValueCacheId(self, counterId, date):
        if not self.thread.isRunning():
            self.thread.start()
        loop = QEventLoop()
        timer = QTimer()
        timer.setSingleShot(True)
        timer.setInterval(3000)
        timer.timeout.connect(loop.quit)
        self.worker.gotCounterValueCacheId_signal.connect(loop.quit)
        self.getCounterValueCacheId_signal.emit(counterId, QVariant(date))
        timer.start()
        loop.exec_()
        self.worker.gotCounterValueCacheId_signal.disconnect(loop.quit)
        if self.counterValueCacheId:
            self.reservation.add(self.counterValueCacheId)
            self.addValueCacheId.emit(self.counterValueCacheId)
            self.lastReservationId = self.counterValueCacheId
            return self.counterValueCacheId
        else:
            raise Exception(u'Не удалось зарезервировать номер')

    @hook
    def getDocumentNumber(self, clientId, counterId, date=None):
        db = QtGui.qApp.db
        sequenceFlag = forceInt(db.translate('rbCounter', 'id', counterId, 'sequenceFlag'))
        if sequenceFlag:
            counterValueCacheId = self.getCounterValueCacheId(counterId, date)
            counterValue = forceInt(db.translate('rbCounter_Value_Cache', 'id', counterValueCacheId, 'value'))
        else:
            counterValue = getCounterValue(counterId, date)
        return getDocumentNumber(clientId, counterId, counterValue)

    @hook
    def delCounterValueCacheReservation(self, id):
        QtGui.qApp.db.deleteRecord('rbCounter_Value_Cache', 'id=%d' % id)

    @hook
    def delAllCounterValueIdReservation(self):
        while self.reservation:
            id = self.reservation.pop()
            self.delCounterValueCacheReservation(id)
        if self.thread.isRunning():
            self.stop.emit()

    @hook
    def resetCounterValueCacheReservation(self, counterId):
        if not self.thread.isRunning():
            self.thread.start()
        self.resetCounterValueCacheId_result = None
        loop = QEventLoop()
        timer = QTimer()
        timer.setSingleShot(True)
        timer.setInterval(3000)
        timer.timeout.connect(loop.quit)
        self.worker.resetCounterValueCacheId_signal.connect(loop.quit)
        self.resetCounterValueCacheId_signal.emit(counterId)
        timer.start()
        loop.exec_()
        self.worker.resetCounterValueCacheId_signal.disconnect(loop.quit)
        self.removeValueCacheId.emit(counterId)

        return self.resetCounterValueCacheId_result

    @hook
    def resetAllCounterValueIdReservation(self):
        while self.reservation:
            id = self.reservation.pop()
            self.resetCounterValueCacheReservation(id)
        if self.thread.isRunning():
            self.stop.emit()


    @pyqtSignature('')
    @hook
    def on_counterTimerTimeout(self, counterValueCacheId):
        if counterValueCacheId:
            QtGui.qApp.db.query('SELECT prolongateCounterValueCacheReservation(%d)' % counterValueCacheId)

# ##############################################################

@hook
def getCounterValueCacheId(db, counterId, date):
    # db = QtGui.qApp.db
    while True:
        query = db.query('SELECT getCounterValueCacheId(%d, %s)' % (counterId, db.formatDate(date) if date else 'CURRENT_DATE'))
        if query.next():
            counterValueCacheId = forceRef(query.value(0))
            if counterValueCacheId:
                return counterValueCacheId

@hook
def getCounterValue(counterId, date):
    db = QtGui.qApp.db
    while True:
        query = db.query('SELECT getCounterValue(%d, %s)' % (counterId, db.formatDate(date) if date else 'CURRENT_DATE'))
        if query.next():
            result = forceRef(query.value(0))
            if result is not None:
                return result


@hook
def getDocumentNumber(clientId, counterId, counterValue):
    if counterValue:
        record = QtGui.qApp.db.getRecord('rbCounter', 'prefix, postfix, rbCounter.separator, format', counterId)
        format = forceString(record.value('format'))
        if format:
            return formatDocumentNumber2(format, counterValue, clientId)
        else:
            prefix = forceString(record.value('prefix'))
            postfix = forceString(record.value('postfix'))
            separator = forceString(record.value('separator'))
            return formatDocumentNumber(prefix, postfix, separator, counterValue, clientId)
    return u''


# example: formatDocumentNumber('date(yy:MM:dd);id(2)', 'id();str(GD23)', '--', 111, 4442) ### `postfix` like `prefix`
def formatDocumentNumber(prefix, postfix, separator, value, clientId):
    def getDatePrefix(val):
        val = val.replace('Y', 'y').replace('m', 'M').replace('D', 'd')
        if val.count('y') not in (0, 2, 4) or val.count('M') > 2 or val.count('d') > 2:
            return None
        s = QtGui.qApp.db.getCurrentDate().toString(val)
        if QDate.fromString(s, val).isValid():
            return unicode(s)
        return None

    def getIdPrefix(val):
        if not clientId:
            return None
        if val == '':
            return str(clientId)
        stmt = 'SELECT `identifier` FROM ClientIdentification JOIN rbAccountingSystem ON rbAccountingSystem.`id`=ClientIdentification.`accountingSystem_id` WHERE ClientIdentification.`client_id`=%d AND rbAccountingSystem.`code`=\'%s\'' % (clientId, val)
        query = QtGui.qApp.db.query(stmt)
        if query.first():
            return forceString(query.value(0))
        return None

    def getStrAddition(val):
        return val

    def getPre_Post_fixValue(ppValue):
        prefixTypes = {'date': getDatePrefix, 'id': getIdPrefix, 'str': getStrAddition}
        prefixList = ppValue.split(';')
        result = []
        for p in prefixList:
            for t in prefixTypes:
                f = p.find(t)
                if f == 0:
                    tl = len(t)
                    val = p[tl:]
                    if val.startswith('(') and val.endswith(')'):
                        val = prefixTypes[t](val.replace('(', '').replace(')', ''))
                        if val:
                            result.append(val)
        return result
    prefix  = getPre_Post_fixValue(prefix)  if prefix  else []
    postfix = getPre_Post_fixValue(postfix) if postfix else []
    return separator.join(prefix+['%d' % value]+postfix)


def formatDocumentNumber2Int(format, value, clientId, date=None):
    class CLocClientIdFmt:
        def __init__(self,  clientId):
            self.clientId = clientId

        def __getattr__(self, attr):
            return self.__getIdentifier(attr)

        def __format__(self,  fmt):
            return self.clientId.__format__(fmt)

        def __getIdentifier(self, code):
            if self.clientId:
                db = QtGui.qApp.db
                tableClientIdentification = db.table('ClientIdentification')
                tableAccountingSystem     = db.table('rbAccountingSystem')
                table = tableClientIdentification.innerJoin(tableAccountingSystem, tableAccountingSystem['id'].eq(tableClientIdentification['accountingSystem_id']))
                record = db.getRecordEx(table,
                                        'identifier',
                                        db.joinAnd([tableClientIdentification['client_id'].eq(self.clientId),
                                                    tableClientIdentification['deleted'].eq(0),
                                                    tableAccountingSystem['code'].eq(code)
                                                   ]
                                                  )
                                       )
                if record:
                    return forceString(record.value(0))
            return ''

    if not date:
        # date = QDate.currentDate()
        date = QtGui.qApp.db.getCurrentDate()
    year, month, day = date.getDate()
    params = { 'value'    : value,
               'day'      : day,
#               'dd'       : '%02d' % day,
               'month'    : month,
#               'mm'       : '%02d' % month,
               'year'     : year,
               'yy'       : '%02d' % (year % 100),
#               'doy'      : date.dayOfYear(),
               'clientId' : CLocClientIdFmt(clientId)
             }
    return format.format(**params)



def formatDocumentNumber2(format, value, clientId):
    try:
        return formatDocumentNumber2Int(format, value, clientId)
    except:
        QtGui.qApp.logCurrentException()
        return u'*ОШИБКА*'


def delCachedValues(counterId, value):
    db = QtGui.qApp.db
    query = db.query('''SELECT rbCounter_Value_Cache.id, rbCounter_Value_Cache.value FROM rbCounter_Value_Cache 
                                LEFT JOIN rbCounter_Value ON rbCounter_Value.id = rbCounter_Value_Cache.master_id 
                                LEFT JOIN rbCounter ON rbCounter.id = rbCounter_Value.master_id
                                WHERE rbCounter.id = %d AND rbCounter_Value_Cache.resTimestamp IS NULL'''%counterId)
    while query.next():
        cachedValueId = forceInt(query.value(0))
        cachedValue = forceInt(query.value(1))
        if cachedValue <= value:
            db.query('DELETE FROM rbCounter_Value_Cache WHERE id = %i'%cachedValueId)
