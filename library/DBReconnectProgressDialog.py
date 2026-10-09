# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2025 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import pyqtSignature, Qt
from time import sleep

from Ui_DBReconnectProgressDialog import Ui_DialogDBReconnect

class ConnectBackgroundWorker(QtCore.QThread):
    progressUpdated = QtCore.pyqtSignal(int)
    connectionSuccessful = QtCore.pyqtSignal()
    
    def __init__(self, parent, runType):
        super(ConnectBackgroundWorker, self).__init__()
        self.parent = parent
        self.runType = runType
        self.isRunning = True

    def run(self):
        sleep(1)
        if self.runType == 1:
            self.tryConnect()
        elif self.runType == 2:
            self.progressBarProcess()

    def progressBarProcess(self):
        counterProgress = 0
        maximum = self.parent.progressBar.maximum()
        while self.isRunning and self.parent.tryConnection:
            counterProgress = (counterProgress + 1) % (maximum + 1)
            self.progressUpdated.emit(counterProgress)
            sleep(0.1)

        self.finished.emit()

    def tryConnect(self):
        while self.isRunning and self.parent.tryConnection:
            try:
                self.parent.dbconnection.remoteConnect()
            except Exception:
                pass

            if self.parent.dbconnection.execDBNotCheck("select 1 as id from dual") == 1:
                self.connectionSuccessful.emit()
                break
            sleep(1)
        self.finished.emit()

    def stop(self):
        self.isRunning = False


class CDBReconnectProgressDialog(Ui_DialogDBReconnect, QtGui.QDialog):
    
    def __init__(self, parent, parentg):
        QtGui.QDialog.__init__(self, parentg)
        self.dbconnection = parent
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setWindowFlags(self.windowFlags() | Qt.CustomizeWindowHint)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self.tryConnection = True
        self.workers = []


    def exec_(self):
        self.startWorkers()
        result = super(CDBReconnectProgressDialog, self).exec_()
        self.cleanupWorkers()
        return result


    def startWorkers(self):
        workerConnection = ConnectBackgroundWorker(self, runType=1)
        workerConnection.connectionSuccessful.connect(self.onConnectionSuccess, QtCore.Qt.QueuedConnection)
        workerConnection.finished.connect(lambda w=workerConnection: self.removeWorker(w))
        workerConnection.finished.connect(workerConnection.deleteLater)
        workerConnection.start()
        self.workers.append(workerConnection)

        workerProgress = ConnectBackgroundWorker(self, runType=2)
        workerProgress.progressUpdated.connect(self.progressBar.setValue)
        workerProgress.finished.connect(lambda w=workerProgress: self.removeWorker(w))
        workerProgress.finished.connect(workerProgress.deleteLater)
        workerProgress.start()
        self.workers.append(workerProgress)


    def cleanupWorkers(self):
        for worker in list(self.workers):
            worker.stop()
            worker.wait(1000)
        self.workers[:] = []


    def onConnectionSuccess(self):
        self.tryConnection = False
        self.cleanupWorkers()
        QtCore.QMetaObject.invokeMethod(self, 'accept', QtCore.Qt.QueuedConnection)
        
        
    def removeWorker(self, worker):
        try:
            self.workers.remove(worker)
        except ValueError:
            pass


    @pyqtSignature('')
    def on_abortBtn_clicked(self):
        self.tryConnection = False
        self.cleanupWorkers()
        self.dbconnection.isCloseApp = 1
        self.close()
        self.dbconnection.parentGl.close()

