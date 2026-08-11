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
## Страница настройки - печать
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore       import pyqtSignature

from library.Utils            import (
                                         forceBool,
                                         forceString,
                                         toVariant,
                                     )

from Ui_PrintPage import Ui_printPage


class CPrintPage(Ui_printPage, QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setupUi(self)

        if 'QPrinterInfo' in QtGui.__dict__: # work-around for current version of pyqt in ubuntu 8.04
            printerNames = [ unicode(pi.printerName()) for pi in QtGui.QPrinterInfo.availablePrinters() ]
        else:
            printerNames = []
        printerNames.insert(0,'')
        self.cmbLabelPrinter.addItems(printerNames)
        self.lblEnablePreview.setVisible(False)
        self.chkEnablePreview.setVisible(False)


    def setProps(self, props):
        self.chkEnableFastPrint.setChecked(forceBool(props.get('enableFastPrint', False)))
        iPrinter = self.cmbLabelPrinter.findText(forceString(props.get('labelPrinter', '')))
        self.cmbLabelPrinter.setCurrentIndex(iPrinter)
        self.chkPrintBlackWhite.setChecked(forceBool(props.get('printBlackWhite', True)))
        self.chkEnablePreview.setChecked(forceBool(props.get('enablePreview', False)))
        self.chkTemplateEdit.setChecked(forceBool(props.get('templateEdit', False)))
        if not QtGui.qApp.enableFastPrint():
            self.chkShowPageSetup.setChecked(forceBool(props.get('showPageSetup', False)))
        else:
            self.chkShowPageSetup.setChecked(False)
            self.chkShowPageSetup.setEnabled(False)
            self.lblShowPageSetup.setEnabled(False)
        self.chkPrintFullPage.setChecked(forceBool(props.get('printFullPage', False)))


    def getProps(self, props):
        props['enableFastPrint']        = toVariant(self.chkEnableFastPrint.isChecked())
        props['labelPrinter']           = toVariant(self.cmbLabelPrinter.currentText())
        props['printBlackWhite']        = toVariant(self.chkPrintBlackWhite.isChecked())
        props['enablePreview']          = toVariant(self.chkEnablePreview.isChecked())
        props['showPageSetup']          = toVariant(self.chkShowPageSetup.isChecked())
        props['templateEdit']           = toVariant(self.chkTemplateEdit.isChecked())
        props['printFullPage']          = toVariant(self.chkPrintFullPage.isChecked())


    @pyqtSignature('')
    def on_chkEnableFastPrint_clicked(self):
        if self.chkEnableFastPrint.isChecked():
            self.chkShowPageSetup.setChecked(False)
            self.chkShowPageSetup.setEnabled(False)
            self.lblShowPageSetup.setEnabled(False)
        else:
            self.chkShowPageSetup.setEnabled(True)
            self.chkShowPageSetup.setChecked(False)
            self.lblShowPageSetup.setEnabled(True)
