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

from PyQt4 import QtGui
from PyQt4.QtCore             import Qt, pyqtSignature

from library.DialogBase       import CDialogBase
from library.PreferencesMixin import CDialogPreferencesMixin

from Events.NomenclatureExpense.Ui_UpdateDoseNomenclatureExpenseEditor import Ui_UpdateDoseNomenclatureExpenseEditor


class CUpdateDoseNomenclatureExpenseEditor(CDialogBase, Ui_UpdateDoseNomenclatureExpenseEditor, CDialogPreferencesMixin):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.params = {}


    @pyqtSignature('QAbstractButton*')
    def on_buttonBox_clicked(self, button):
        buttonCode = self.buttonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Ok:
            self.params = {}
            self.params['procent'] = self.edtProcent.value()
            self.params['change'] = 1 if self.chkReduce.isChecked() else (2 if self.chkIncrease.isChecked() else 0)
        elif buttonCode == QtGui.QDialogButtonBox.Cancel:
            self.params = {}


    @pyqtSignature('bool')
    def on_chkReduce_toggled(self, value):
        self.chkIncrease.setChecked(not self.chkReduce.isChecked())
        self.edtProcent.setFocus(Qt.TabFocusReason)


    @pyqtSignature('bool')
    def on_chkIncrease_toggled(self, value):
        self.chkReduce.setChecked(not self.chkIncrease.isChecked())
        self.edtProcent.setFocus(Qt.TabFocusReason)


    def getProcentParams(self):
        return self.params


    def saveData(self):
        return True

