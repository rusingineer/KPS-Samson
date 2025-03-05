# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2017-2021 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

# редактор разных умолчаний


from PyQt4 import QtGui
from PyQt4.QtCore import Qt, pyqtSignature, QVariant

from library.Utils            import forceBool, forceInt, forceRef, forceString, toVariant

from Orgs.Orgs                import selectOrganisation

from Ui_appPreferencesDialog  import Ui_appPreferencesDialog


DefaultAverageDuration = 28


class CAppPreferencesDialog(QtGui.QDialog, Ui_appPreferencesDialog):
    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)


    def setProps(self, props):
        self.cmbOrganisation.setValue(forceRef(props.get('orgId', QVariant())))
        self.cmbOrgStructure.setValue(forceRef(props.get('orgStructureId', QVariant())))
        self.chkUseCurrentUser.setChecked(forceBool(props.get('useCurrentUser', False)))
        self.edtContractNumberMask.setText(forceString(props.get('contractNumberMask',  '')))
        self.edtContractResolutionMask.setText(forceString(props.get('contractResolutionMask',  '')))
        self.edtContractGroupingMask.setText(forceString(props.get('contractGroupingMask',  '')))
        self.edtAccountNumberMask.setText(forceString(props.get('accountNumberMask',  '')))
        self.chkPrintPayer.setChecked(forceBool(props.get('printPayer', False)))
        self.chkPrintAccountNumber.setChecked(forceBool(props.get('printAccountNumber', False)))
        self.chkPrintDuplicate.setChecked(forceBool(props.get('printDuplicate', False)))
        self.edtCashBox.setText(forceString(props.get('cashBox',  '')))
        self.chkVatTaxPayer.setChecked(forceBool(props.get('vatTaxPayer', False)))

        self.cmbDriver.setCurrentIndex(forceInt(props.get('driver', 0)))
        self.edtPassword.setText(forceString(props.get('password', '')))
        self.edtOperatorPassword.setText(forceString(props.get('operatorPassword', '')))
        self.edtSysAdminPassword.setText(forceString(props.get('sysAdminPassword', '')))
        (self.getLinkButton(forceString(props.get('link', 'usb'))) or self.rbUsb).setChecked(True)
        self.edtSerialPort.setText(forceString(props.get('serialPort',  '/dev/ttyACM0')))
        self.setSerialBaudrate(forceInt(props.get('serialBaudrate', 0)))
        baudrate = forceInt(props.get('serialBaudrate', 0))
        baudrateIndex = self.cmbSerialBaudrate.findText(str(baudrate), Qt.MatchFixedString)
        self.cmbSerialBaudrate.setCurrentIndex(baudrateIndex if baudrateIndex>=0 else self.cmbSerialBaudrate.count()//2)
        self.edtUsbPort.setText(forceString(props.get('usbPort', 'auto')))
        self.edtTcpIpHost.setText(forceString(props.get('tcpIpHost', '')))
        self.edtTcpIpPort.setValue(forceInt(props.get('tcpIpPort', 5555)))
        self.edtBluetoothMacAddress.setText(forceString(props.get('bluetoothMacAddress', '00:00:00:00:00:00')))


    def props(self):
        result = {}

        result['orgId']                  = toVariant(self.cmbOrganisation.value())
        result['orgStructureId']         = toVariant(self.cmbOrgStructure.value())
        result['useCurrentUser']         = toVariant(self.chkUseCurrentUser.isChecked())
        result['contractNumberMask']     = toVariant(self.edtContractNumberMask.text())
        result['contractResolutionMask'] = toVariant(self.edtContractResolutionMask.text())
        result['contractGroupingMask']   = toVariant(self.edtContractGroupingMask.text())
        result['accountNumberMask']      = toVariant(self.edtAccountNumberMask.text())
        result['printPayer']             = toVariant(self.chkPrintPayer.isChecked())
        result['printAccountNumber']     = toVariant(self.chkPrintAccountNumber.isChecked())
        result['printDuplicate']         = toVariant(self.chkPrintDuplicate.isChecked())
        result['cashBox']                = toVariant(self.edtCashBox.text())
        result['vatTaxPayer']            = toVariant(self.chkVatTaxPayer.isChecked())

        result['driver']                 = toVariant(self.cmbDriver.currentIndex())
        result['password']               = toVariant(self.edtPassword.text())
        result['operatorPassword']       = toVariant(self.edtOperatorPassword.text())
        result['sysAdminPassword']       = toVariant(self.edtSysAdminPassword.text())
        result['link']                   = toVariant(self.getLinkName())
        result['serialPort']             = toVariant(self.edtSerialPort.text())
        result['serialBaudrate']         = toVariant(int(self.cmbSerialBaudrate.currentText()))
        result['usbPort']                = toVariant(self.edtUsbPort.text())
        result['tcpIpHost']              = toVariant(self.edtTcpIpHost.text())
        result['tcpIpPort']              = toVariant(self.edtTcpIpPort.text())
        result['bluetoothMacAddress']    = toVariant(self.edtBluetoothMacAddress.text())
        return result


    def getMapLinkNameToButton(self):
        return {'serial port': self.rbSerialPort,
                'usb'        : self.rbUsb,
                'tcp/ip'     : self.rbTcpIp,
                'bluetooth'  : self.rbBluetooth
               }


    def getLinkName(self):
        for linkName, button in self.getMapLinkNameToButton().iteritems():
            if button.isChecked():
                return linkName
        return None


    def getLinkButton(self, linkName):
        m = self.getMapLinkNameToButton()
        return m.get(linkName)


    def setSerialBaudrate(self, baudrate):
        baudrateIndex = self.cmbSerialBaudrate.findText(str(baudrate), Qt.MatchFixedString)
        if baudrateIndex<0:
            baudrateIndex = self.cmbSerialBaudrate.findText('38400', Qt.MatchFixedString)
        if baudrateIndex<0:
            baudrateIndex = self.cmbSerialBaudrate.count()//2
        self.cmbSerialBaudrate.setCurrentIndex(baudrateIndex)


    @pyqtSignature('int')
    def on_cmbOrganisation_currentIndexChanged(self, index):
        orgId = self.cmbOrganisation.value()
        self.cmbOrgStructure.setOrgId(orgId)


    @pyqtSignature('')
    def on_btnSelectOrganisation_clicked(self):
        orgId = selectOrganisation(self, self.cmbOrganisation.value(), False)
        self.cmbOrganisation.updateModel()
        if orgId:
            self.cmbOrganisation.setValue(orgId)


    @pyqtSignature('int')
    def on_cmbDriver_currentIndexChanged(self, index):
        if index == 1: # АТОЛ
            self.lblPassword.setEnabled(True)
            self.edtPassword.setEnabled(True)
            self.lblOperatorPassword.setEnabled(True)
            self.edtOperatorPassword.setEnabled(True)
            self.lblSysAdminPassword.setEnabled(False)
            self.lblSysAdminPassword.setEnabled(False)
            self.edtPassword.setInputMask('99999999;')
            self.edtOperatorPassword.setInputMask('99999999;')
        elif index == 2: # Штрих
            self.lblPassword.setEnabled(False)
            self.edtPassword.setEnabled(False)
            self.lblOperatorPassword.setEnabled(True)
            self.edtOperatorPassword.setEnabled(True)
            self.lblSysAdminPassword.setEnabled(True)
            self.edtSysAdminPassword.setEnabled(True)
            self.edtOperatorPassword.setInputMask('99;')
            self.edtSysAdminPassword.setInputMask('99;')
        else:
            self.lblPassword.setEnabled(False)
            self.edtPassword.setEnabled(False)
            self.lblOperatorPassword.setEnabled(False)
            self.edtOperatorPassword.setEnabled(False)
            self.lblSysAdminPassword.setEnabled(False)
            self.lblSysAdminPassword.setEnabled(False)
