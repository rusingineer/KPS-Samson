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
from PyQt4.QtCore import pyqtSignature, Qt

from library.DialogBase     import CDialogBase
from library.PrintTemplates import getPrintButton
from library.Utils          import (
                                     calcAge,
                                     forceRef,
                                     forceString,
                                     formatDate,
                                     formatName,
                                     formatSex,
#                                     formatSNILS,
                                    )

from Registry.Utils         import getClientInfo, formatSocStatuses
from Reports.ReportView     import CReportViewDialog



from Ui_AmbCardJournalDialog import Ui_AmbCardJournalDialog

class CAmbCardJournalDialog(CDialogBase, Ui_AmbCardJournalDialog):
    def __init__(self, parent=None, clientId=None):
        CDialogBase.__init__(self, parent)
        self.addObject('btnPrint', getPrintButton(self, '', u'Печать'))
        self.setupUi(self)
        self.buttonBox.addButton(self.btnPrint, QtGui.QDialogButtonBox.ActionRole)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
#        self.btnPrint.setShortcut('F6')
        self.btnPrint.setEnabled(True)
        if clientId:
            self.setClientId(clientId)
        self.firstClick = True
        self.on_btnRowSelect_clicked()


    def exec_(self):
        self.loadDialogPreferences()
        self.ambCardPage.resetSortTable()
        result = QtGui.QDialog.exec_(self)
        return result


    @pyqtSignature('')
    def on_btnPrint_clicked(self):
        printData = self.ambCardPage.txtAmbCardReport.getPrintData()
        view = CReportViewDialog(self)
        view.setText(printData['templateResult'].content)
        view.setPageFormat(printData['pageFormat'])
        view.templateContent = printData['templateResult'].content
        view.exec_()


    @pyqtSignature('')
    def on_btnRowSelect_clicked(self):
        if not self.firstClick:
            if self.ambCardPage.isFocusWidget == 2:
                self.ambCardPage.isFocusWidget -= 1
                eventIndex = self.ambCardPage.tblEvents.currentIndex()
                self.ambCardPage.on_selectionModelEventsCurrentChanged(eventIndex, eventIndex)
            else:
                self.ambCardPage.isFocusWidget += 1
                actionIndex = self.ambCardPage.tblActions.currentIndex()
                self.ambCardPage.on_selectionModelActionsCurrentChanged(actionIndex, actionIndex)
        else:
            self.firstClick = False
        self.getBtnRowSelectText()


    def getBtnRowSelectText(self):
        db = QtGui.qApp.db
        if self.ambCardPage.isFocusWidget == 1:
            eventItem = self.ambCardPage.tblEvents.currentItem()
            if eventItem:
                eventTypeId = forceRef(eventItem.value('eventType_id'))
                begDate = forceString(eventItem.value('setDate'))
                endDate = forceString(eventItem.value('execDate'))
            else:
                eventTypeId = None
                begDate = u''
                endDate = u''
            if eventTypeId:
                typeName = u'Выбрано событие: '
                typeName += forceString(db.translate('EventType', 'id', eventTypeId, 'name'))
                typeName +=  u' ' + begDate + u' - ' + endDate
            else:
                typeName = u'Проблема с выбором'
                self.ambCardPage.txtAmbCardReport.setText(u'ОШИБКА ПОДБОРА ШАБЛОНА')
        elif self.ambCardPage.isFocusWidget == 2:
            actionItem = self.ambCardPage.tblActions.currentItem()
            if actionItem:
                actionTypeId = forceRef(actionItem.value('actionType_id'))
                begDate = forceString(actionItem.value('directionDate'))
                endDate = forceString(actionItem.value('endDate'))
            else:
                actionTypeId = None
                begDate = u''
                endDate = u''
            if actionTypeId:
                typeName = u'Выбрано действие: '
                typeName += forceString(db.translate('ActionType', 'id', actionTypeId, 'name'))
                typeName +=  u' ' + begDate + u' - ' + endDate
            else:
                typeName = u'Проблема с выбором'
                self.ambCardPage.txtAmbCardReport.setText(u'ОШИБКА ПОДБОРА ШАБЛОНА')
        else:
            typeName = u'Проблема с фокусом'
            self.ambCardPage.txtAmbCardReport.setText(u'ОШИБКА ПОДБОРА ШАБЛОНА')
        self.btnRowSelect.setText(typeName)


    def setClientId(self, clientId):
        self.ambCardPage.setClientId(clientId)
        self.setWindowTitle(u'Пациент: %s' % (self.getClientString(clientId) if clientId else u'не известен'))


    def getClientString(self, clientId, atDate=None):
        info = getClientInfo(clientId)
        return self.formatClientString(info, atDate)


    def formatClientString(self, info, atDate=None):
        id        = info.id
        name      = formatName(info.lastName, info.firstName, info.patrName)
        birthDate = formatDate(info.birthDate)
#        birthPlace= info.birthPlace
        age       = calcAge(info.birthDate, atDate)
        sex       = formatSex(info.sexCode)
#        SNILS     = formatSNILS(info.SNILS)
#        attaches  = info.get('attaches', [])
        socStatuses = info.get('socStatuses', [])
        bannerHTML = u'''%s, дата рождения: %s (%s)  пол: %s  код: %s  статус: %s''' % (name, birthDate, age, sex, id, formatSocStatuses(socStatuses))
        clientBanner = u'%s' % bannerHTML
        return clientBanner


