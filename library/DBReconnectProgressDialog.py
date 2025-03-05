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
        while self.isRunning and self.parent.tryConnection == 1:
            counterProgress += 1
            self.progressUpdated.emit(counterProgress)
            sleep(0.1)

            if counterProgress >= self.parent.progressBar.maximum():
                counterProgress = 0

    def tryConnect(self):
        while self.isRunning and self.parent.tryConnection == 1:
            try:
                self.parent.dbconnection.remoteConnect()
            except Exception:
                pass

            if self.parent.dbconnection.execDBNotCheck("select 1 as id from dual") == 1:
                self.isRunning = False
                self.parent.tryConnection = 0
                self.connectionSuccessful.emit()
                break
            sleep(1)

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

        self.tryConnection = 1
        self.worker = None

    def exec_(self):
        self.worker = ConnectBackgroundWorker(self, 1)
        self.worker.connectionSuccessful.connect(self.onConnectionSuccess)
        self.worker.start()

        self.progressWorker = ConnectBackgroundWorker(self, 2)
        self.progressWorker.progressUpdated.connect(self.updateProgressBar)
        self.progressWorker.start()

        return QtGui.QDialog.exec_(self)

    @pyqtSignature('')
    def on_abortBtn_clicked(self):
        self.tryConnection = 0
        if self.worker:
            self.worker.stop()
        if hasattr(self, 'progressWorker') and self.progressWorker:
            self.progressWorker.stop()
        self.dbconnection.isCloseApp = 1
        self.close()
        self.dbconnection.parentGl.close()

    def updateProgressBar(self, value):
        self.progressBar.setValue(value)

    def onConnectionSuccess(self):
        self.close()
