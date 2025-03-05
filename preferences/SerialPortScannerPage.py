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
## Страница настройки сканера штрих-кодов, подключаемого через посл. порт
## или в режиме эмуляции посл.порта
##
#############################################################################

import serial

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, pyqtSignature

from library.SerialSettings   import CSerialSettings
from library.Utils            import (
                                         exceptionToUnicode,
                                         forceBool,
                                         forceString,
                                         toVariant,
                                     )

from Ui_SerialPortScannerPage import Ui_serialPortScannerPage


class CSerialPortScannerPage(Ui_serialPortScannerPage, QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setupUi(self)


    def setProps(self, props):
        self.chkScanEnable.setChecked(forceBool(props.get('ScannerEnable', False)))
        self.setScannerPortSettings(forceString(props.get('ScannerPortSettings', '')))
        self.chkScanCorrectBackslashes.setChecked(forceBool(props.get('ScannerCorrectBackslashes', True)))
        self.chkScanConnectionReport.setChecked(forceBool(props.get('ScannerConnectionReport', True)))
        self.chkScanParseReport.setChecked(forceBool(props.get('ScannerParseReport', False)))
        self.chkScanPromobotEnable.setChecked(forceBool(props.get('ScanPromobotEnable', False)))
        self.edtScanPromobotAddress.setText(forceString(props.get('ScanPromobotAddress', '')))
        self.chkTabletSignEnable.setChecked(forceBool(props.get('TabletSignEnable', False)))


    def getProps(self, props):
        props['ScannerEnable']             = toVariant(int(self.chkScanEnable.isChecked()))
        props['ScannerPortSettings']       = toVariant(self.getScannerPortSettings())
        props['ScannerCorrectBackslashes'] = toVariant(int(self.chkScanCorrectBackslashes.isChecked()))
        props['ScannerConnectionReport']   = toVariant(int(self.chkScanConnectionReport.isChecked()))
        props['ScannerParseReport']        = toVariant(int(self.chkScanParseReport.isChecked()))
        props['ScanPromobotEnable'] = toVariant(int(self.chkScanPromobotEnable.isChecked()))
        props['ScanPromobotAddress'] = toVariant(self.edtScanPromobotAddress.text())
        props['TabletSignEnable'] = toVariant(int(self.chkTabletSignEnable.isChecked()))


    def setScannerPortSettings(self, prop):
        settings = CSerialSettings(prop)
        self.edtScanPort.setText(settings.port)
        self.cmbScanBaudrate.setCurrentIndex(self.cmbScanBaudrate.findText(str(settings.baudrate), Qt.MatchFixedString))
        self.cmbScanParity.setCurrentIndex(self.cmbScanParity.findText(str(settings.parity), Qt.MatchStartsWith))
        self.cmbScanStopBits.setCurrentIndex(self.cmbScanStopBits.findText(str(settings.stopbits), Qt.MatchFixedString))
        self.cmbScanFlowControl.setCurrentIndex( 1 if settings.rtscts else 2 if settings.xonxoff else 0 )


    def getScannerPortSettingsAsObject(self):
        settings = CSerialSettings()
        settings.port = unicode(self.edtScanPort.text())
        settings.baudrate = int(self.cmbScanBaudrate.currentText())
        settings.parity = str(self.cmbScanParity.currentText()[0])
        settings.stopbits = float(self.cmbScanStopBits.currentText())

        flowControl = self.cmbScanFlowControl.currentIndex()
        if flowControl == 1:
            settings.xonxoff = False
            settings.rtscts = True
        elif flowControl == 2:
            settings.xonxoff = True
            settings.rtscts = False
        else:
            settings.xonxoff = settings.rtscts = False
        return settings


    def getScannerPortSettings(self):
        settings = self.getScannerPortSettingsAsObject()
        return settings.asString()


    @pyqtSignature('')
    def on_btnScanTest_clicked(self):
        from ScanTestDialog import CScanTestDialog
        settings = self.getScannerPortSettingsAsObject()
        try:
            scanner = None
            try:
                scanner = serial.Serial(settings.port,
                                        baudrate=settings.baudrate,
                                        bytesize=8,
                                        parity=settings.parity,
                                        stopbits=settings.stopbits,
                                        xonxoff=settings.xonxoff,
                                        rtscts=settings.rtscts,
                                        timeout=0.1)
            except Exception as e:
                QtGui.qApp.logCurrentException()
                QtGui.QMessageBox.information(self,
                                              u'Ошибка подключения к сканеру',
                                              exceptionToUnicode(e),
                                              QtGui.QMessageBox.Close,
                                              QtGui.QMessageBox.Close)
                return
            testDialog = CScanTestDialog(self, scanner)
            testDialog.exec_()
        finally:
            if scanner is not None:
                scanner.close()
