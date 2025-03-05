# coding=utf-8
#############################################################################
##
## Copyright (C) 2024 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
from PyQt4.QtCore import Qt, pyqtSignature

from Stock.Ui_UtilizationChoiceDialog import Ui_UtilizationChoiceDialog
from library.DialogBase import CDialogBase


class CUtilizationChoiceDialog(CDialogBase, Ui_UtilizationChoiceDialog):
    def __init__(self, parent=None):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.setWindowTitle(u'Сведения по утилизации')
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint)
        self.cmbDestructionType.setItems()
        self.cmbReasonDestructionType.setItems()
        self.decisionWithDrawFromCirculation = None
        self.destructionType = None
        self.reasonDestructionType = None

    def setDecisionWithDrawFromCirculation(self, val):
        self.edtDecisionWithDrawFromCirculation.setText(val or u'')

    def setDestructionType(self, index):
        self.cmbDestructionType.setCurrentIndex(index or 0)

    def setReasonDestructionType(self, index):
        self.cmbReasonDestructionType.setCurrentIndex(index or 0)
