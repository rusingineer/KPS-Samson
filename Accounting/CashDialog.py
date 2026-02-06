# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2021 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, pyqtSignature, QDateTime

from library.ItemsListDialog import CItemEditorBaseDialog
from library.PrintInfo import CInfoContext, CDateInfo, CDateTimeInfo
from library.PrintTemplates import getPrintButton, applyTemplate
from library.Utils import (forceDate, forceDouble, forceRef, forceString, toVariant, forceInt, forceDateTime)
from Events.EventInfo import CEventInfo, CCashOperationInfo

from Accounting.Ui_CashDialog import Ui_CashDialog


class CashDialogEditor(CItemEditorBaseDialog, Ui_CashDialog):
    def __init__(self,  parent):
        CItemEditorBaseDialog.__init__(self, parent, 'Event_Payment')
        self.addObject('btnPrint', getPrintButton(self, 'cashOrder'))
        self.setupUi(self)
        self.cmbCashOperation.setTable('rbCashOperation', True)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.buttonBox.addButton(self.btnPrint, QtGui.QDialogButtonBox.ActionRole)
        self.setupDirtyCather()
        self.eventId = None
        self.edtDateTime.setDateTime(QDateTime.currentDateTime())
        self.cashBox = ''


    def setEventId(self, eventId):
        self.eventId = eventId


    def setCashBox(self, cashBox):
        self.cashBox = cashBox


    def setEventSum(self, sum):
        self.edtSum.setValue(forceDouble(sum))


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        self.edtDateTime.setDateTime(forceDateTime(record.value('dateTime')))
        self.cmbCashOperation.setValue(forceRef(record.value('cashOperation_id')))
        self.cmbCashOperation.setCurrentIndex(forceInt(record.value('typePayment')))
        self.edtDocumentPayment.setText(forceString(record.value('documentPayment')))
        self.edtSum.setValue(forceDouble(record.value('sum')))
        self.eventId = forceRef(record.value('master_id'))
        self.cashBox = forceString(record.value('cashBox'))


    def checkDataEntered(self):
        return True


    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        record.setValue('master_id',         toVariant(self.eventId))
        record.setValue('dateTime',          toVariant(self.edtDateTime.dateTime()))
        record.setValue('cashOperation_id',  toVariant(self.cmbCashOperation.value()))
        record.setValue('typePayment',       toVariant(self.cmbTypePayment.currentIndex()))
        record.setValue('documentPayment',   toVariant(self.edtDocumentPayment.text()))
        record.setValue('sum',               toVariant(self.edtSum.value()))
        record.setValue('cashBox',           toVariant(self.cashBox))
        return record


    def save(self):
        if self.lock('Event', self.eventId):
            try:
                return CItemEditorBaseDialog.save(self)
            finally:
                self.releaseLock()
        else:
            return False


    @pyqtSignature('int')
    def on_btnPrint_printByTemplate(self, templateId):
        printCashOrder(self,
                       templateId,
                       self.eventId,
                       self.edtDateTime.dateTime(),
                       self.cmbCashOperation.value(),
                       self.edtSum.value(),
                       self.cashBox
                      )


def printCashOrder(widget, templateId, eventId, dateTime, cashOperationId, sum, cashBox):
    context = CInfoContext()
    eventInfo = context.getInstance(CEventInfo, eventId)
    data = { 'event'        : eventInfo,
             'client'       : eventInfo.client,
             'dateTime'     : CDateTimeInfo(dateTime),
             'cashOperation': context.getInstance(CCashOperationInfo, cashOperationId),
             'sum'          : sum,
             'cashBox'      : cashBox
           }
    applyTemplate(widget, templateId, data)
