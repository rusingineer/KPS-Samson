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


u"""
Экспорт данных в Web-сервис “Прикрепленное население”
"""
from PyQt4 import QtCore, QtGui

import Exchange.AttachService as AttachService

from Ui_ReAttach import Ui_Dialog


class CReAttach(QtGui.QDialog, Ui_Dialog):
    def __init__(self,  parent):
        QtGui.QDialog.__init__(self, parent)
        self.clearLog()
        self.setupUi(self)

    def setClientIdList(self, clientIdList):
        self.clientIdList = clientIdList
        self.labelCount.setText(u'Выбрано человек: %i' % len(self.clientIdList))
       
    def startImport(self):
        self.clearLog()
        self.appendLog(u'Экспорт данных.Ожидайте...', False)
        self.showLog()
        try:
            response = AttachService.callServiceReAttach('clientReAttach', {'reattachlist': self.clientIdList}, timeout=1200, returnRawResult=True)
            if 'responsemessage' not in response:
                self.appendLog(u'Неопознанная ошибка', False)
            else:
                self.appendLog(u'Экспорт данных завершен!', False)
                resCode = response['responsecode']
                resMessage = response['responsemessage']
                self.appendLog(u'', False)
                if resMessage:
                    self.appendLog(resMessage, False)
                    self.appendLog(u'', False)
                self.appendLog(u'Открепление - запрос', True)
                self.appendLog(response['deattach']['request'], True)
                self.appendLog(u'', True)
                self.appendLog(u'Открепление - ответ', True)
                self.appendLog(response['deattach']['response'], True)
                self.appendLog(u'', True)
                self.appendLog(u'Прикрепление - запрос', True)
                self.appendLog(response['attach']['request'], True)
                self.appendLog(u'', True)
                self.appendLog(u'Прирепление - ответ', True)
                self.appendLog(response['attach']['response'], True)
                self.appendLog(u'', True)
                if resCode == 1001:
                    self.appendLog(u'Успешно выгружено %i человек' % response['success'], False)
                    self.appendLog(u'', False)
                    self.appendLog(response['message'], False)
        finally:
            self.showLog()
    
    def clearLog(self):
        self.shortLog = u''
        self.fullLog = u''
    
    def appendLog(self, text, fullLogOnly):
        self.fullLog += text
        self.fullLog += u'\r\n'
        if not fullLogOnly:
            self.shortLog += text
            self.shortLog += u'\r\n'
    
    def showLog(self):
        if self.chbFullLog.isChecked():
            self.log.setPlainText(self.fullLog)
        else:
            self.log.setPlainText(self.shortLog)
        QtGui.qApp.processEvents()
    
    @QtCore.pyqtSignature('bool')
    def on_chbFullLog_toggled(self, checked):
        self.showLog()

    @QtCore.pyqtSignature('')
    def on_btnExport_clicked(self):
        self.startImport()
        
    @QtCore.pyqtSignature('')
    def on_btnClose_clicked(self):
        self.close()
