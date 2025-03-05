# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2017 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import QObject, QTimer, SIGNAL, QThread, pyqtSignal, QEventLoop

from library.Utils import forceBool, forceRef
from library.plugins import hook
from library import database
import logging


class CJobTicketReserveLevel:
    @hook
    def __init__(self, key, prevLevel):
        self.key = key
        self.prevLevel = prevLevel
        self.reservedOnPrevLevels = prevLevel.getReservedOnAllLevels() if prevLevel else set([])
        self.reserved = set([])

    @hook
    def add(self, jobTicketId):
        self.reserved.add(jobTicketId)

    @hook
    def remove(self, jobTicketId):
        self.reserved.discard(jobTicketId)

    @hook
    def getReservedOnAllLevels(self):
        return self.reserved | self.reservedOnPrevLevels

    @hook
    def getUniqueReservedIdSet(self):
        return self.reserved - self.reservedOnPrevLevels

    def isAnythingReserved(self):
        return bool(self.reserved) or bool(self.reservedOnPrevLevels)


class ProlongWorker(QObject):
    finished = pyqtSignal()
    reserved_signal = pyqtSignal('bool')
    delReservation_signal = pyqtSignal('bool')

    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self.timer = None
        self.ticketList = set()
        self.db = None
        self.connectionId = None

    def openDatabase(self):
        preferences = QtGui.qApp.preferences
        connectionName = "ProlongWorker_" + str(QThread.currentThreadId())
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
            raise Exception('JobTicketReserve: No database available for prolongate query!')
        query = self.db.query("select connection_id()")
        if query.first():
            self.connectionId = forceRef(query.value(0))



    def __del__(self):
        if self.db:
            self.db.close()
        if self.timer:
            self.timer.stop()

    def addReservation(self, jobTicketId):
        query = self.db.query('SELECT addJobTicketReservation(%d)' %jobTicketId)
        if query.next():
            result = forceBool(query.record().value(0))
        else:
            result = False
        self.reserved_signal.emit(result)

    def delReservation(self, jobTicketId):
        query = self.db.query('SELECT delJobTicketReservation(%d)' %jobTicketId)
        if query.next():
            result = forceBool(query.record().value(0))
        else:
            result = False
        self.delReservation_signal.emit(result)

    @hook
    def prolongReservation(self):
        for jobTicketId in self.ticketList:
            self.db.query('SELECT checkJobTicketReservation(%d)' % jobTicketId)

    def addTicket(self, ticket_id):
        self.ticketList.add(ticket_id)

    def removeTicket(self, ticket_id):
        self.ticketList.remove(ticket_id)

    def start(self):
        if not self.db:
            self.openDatabase()
        self.timer = QTimer()
        self.timer.setInterval(60000)
        self.connect(self.timer, SIGNAL('timeout()'), self.prolongReservation)
        self.timer.start()

    def stop(self):
        if self.timer:
            self.timer.stop()
        if self.db:
            self.db.close()
            self.db = None
        self.finished.emit()


class CJobTicketReserveHolder(QObject):
    start = pyqtSignal()
    stop = pyqtSignal()
    addJobTicket = pyqtSignal('int')
    removeJobTicket = pyqtSignal('int')
    addReservation = pyqtSignal('int')
    delReservation = pyqtSignal('int')

    @hook
    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self.currLevel = None

        self.thread = QThread()
        self.worker = ProlongWorker()
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.start)
        self.stop.connect(self.worker.stop)
        self.addJobTicket.connect(self.worker.addTicket)
        self.removeJobTicket.connect(self.worker.removeTicket)
        self.worker.finished.connect(self.thread.quit)
        self.worker.delReservation_signal.connect(self.catchDelReservationSignal)
        self.worker.reserved_signal.connect(self.catchAddReservationSignal)
        self.addReservation.connect(self.worker.addReservation)
        self.delReservation.connect(self.worker.delReservation)
        self.addReservation_result = None
        self.delReservation_result = None
        self.thread.start()

    def __del__(self):
        if self.thread.isRunning():
            self.thread.quit()
            self.thread.wait(5000)

    def catchAddReservationSignal(self, res):
        self.addReservation_result = res

    def catchDelReservationSignal(self, res):
        self.delReservation_result = res

    def getConnectionId(self):
        return self.worker.connectionId

    @hook
    def addLevel(self, key):
        self.currLevel = CJobTicketReserveLevel(key, self.currLevel)

    @hook
    def delLevel(self, key, releaseReserve=True):
        assert self.currLevel is not None
        assert self.currLevel.key == key

        if releaseReserve:
            try:
                self.delAllJobTicketReservations()
            except:
                QtGui.qApp.logCurrentException()

        self.currLevel = self.currLevel.prevLevel
        if self.currLevel is None or not self.currLevel.isAnythingReserved():
            if self.thread.isRunning():
                self.stop.emit()

    @hook
    def addJobTicketReservation(self, jobTicketId):
        if self.currLevel:
            if not self.thread.isRunning():
                self.thread.start()
            self.addReservation_result = None
            loop = QEventLoop()
            timer = QTimer()
            timer.setSingleShot(True)
            timer.setInterval(2000)
            timer.timeout.connect(loop.quit)
            self.worker.reserved_signal.connect(loop.quit)
            self.addReservation.emit(jobTicketId)
            timer.start()
            loop.exec_()
            self.worker.reserved_signal.disconnect(loop.quit)
            if self.addReservation_result:
                if jobTicketId:
                    self.currLevel.add(jobTicketId)
                    self.addJobTicket.emit(jobTicketId)
            return self.addReservation_result
        return False

    @hook
    def getReservedJobTickets(self):
        assert self.currLevel is not None
        return list(self.currLevel.getReservedOnAllLevels())

    @hook
    def delJobTicketReservation(self, jobTicketId):
        if self.currLevel:
            if not self.thread.isRunning():
                self.thread.start()
            self.delReservation_result = None
            loop = QEventLoop()
            timer = QTimer()
            timer.setSingleShot(True)
            timer.setInterval(2000)
            timer.timeout.connect(loop.quit)
            self.worker.delReservation_signal.connect(loop.quit)
            self.delReservation.emit(jobTicketId)
            timer.start()
            loop.exec_()
            self.worker.delReservation_signal.disconnect(loop.quit)

            self.currLevel.remove(jobTicketId)
            self.removeJobTicket.emit(jobTicketId)

            if not self.currLevel.isAnythingReserved():
                if self.thread.isRunning():
                    self.stop.emit()
            return self.delReservation_result
        return False


    @hook
    def delAllJobTicketReservations(self):
        assert self.currLevel is not None

        getUniqueReservedIdSet = self.currLevel.getUniqueReservedIdSet()
        for jobTicketId in getUniqueReservedIdSet:
            self.delJobTicketReservation(jobTicketId)