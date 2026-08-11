# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2019 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
##
## Страница настройки - расчёты
##
#############################################################################

from PyQt4 import QtGui

from library.Utils            import (
                                         forceBool,
                                         forceString,
                                         toVariant,
                                     )

from Ui_AccountingPage import Ui_accountingPage


class CAccountingPage(Ui_accountingPage, QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setupUi(self)


    def setProps(self, props):
        self.edtCachBox.setText(forceString(props.get('cashBox',  '')))
        self.chkFilterPaymentByOrgStructure.setChecked(forceBool(props.get('filterPaymentByOrgStructure', False)))
        self.edtPositionInvoice.setText(forceString(props.get('positionInvoice',  '')))
        self.chkUseNativeFileDialog.setChecked(forceBool(props.get('useNativeFileDialog', False)))


    def getProps(self, props):
        props['cashBox']  = toVariant(self.edtCachBox.text())
        props['filterPaymentByOrgStructure'] = toVariant(bool(self.chkFilterPaymentByOrgStructure.isChecked()))
        props['positionInvoice']  = toVariant(self.edtPositionInvoice.text())
        props['useNativeFileDialog'] = toVariant(bool(self.chkUseNativeFileDialog.isChecked()))
