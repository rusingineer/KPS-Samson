# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2022 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui

from Ui_ExposeConfirmationDialog import Ui_ExposeConfirmationDialog
from library.DialogBase import CDialogBase
from library.Utils import firstMonthDay


class CExposeConfirmationDialog(CDialogBase, Ui_ExposeConfirmationDialog):
    def __init__(self,  parent, message, orgStructureId, date):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.lblMessage.setText(message)
        self.edtEndDate.setDate(date)
        self.edtBegDate.setDate(firstMonthDay(date.addDays(-1).addMonths(-1)))
        if orgStructureId:
            self.chkFilterPaymentByOrgStructure.setChecked(QtGui.qApp.filterPaymentByOrgStructure())
            self.chkFilterPaymentByOrgStructure.setEnabled(True)
        else:
            self.chkFilterPaymentByOrgStructure.setChecked(False)
            self.chkFilterPaymentByOrgStructure.setEnabled(False)
        if QtGui.qApp.defaultKLADR()[:2] == '23':
            self.chkMesCheck.setVisible(False)
            self.chkMesCheck.setChecked(False)
        else:
            self.chkMesCheck.setVisible(True)
            self.chkMesCheck.setChecked(True)
        self.chkOnlyDispCOVID.setChecked(False)
        self.chkOnlyResearchOnCOVID.setChecked(False)
        self.buttonBox.button(QtGui.QDialogButtonBox.Cancel).setDefault(True)

    def options(self):
        return (self.edtBegDate.date(),
                self.edtEndDate.date(),
                self.chkFilterPaymentByOrgStructure.isChecked(),
                self.chkReExpose.isChecked(),
                self.chkSeparateReExpose.isChecked(),
                self.chkMesCheck.isChecked(),
                self.chkOnlyDispCOVID.isChecked(),
                self.chkOnlyResearchOnCOVID.isChecked())
