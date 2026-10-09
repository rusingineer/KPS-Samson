# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'E:\projects\Samson\UP_s11\client_test\Orgs\CreateAttachClientsForAreaDialog.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_CreateAttachClientsForAreaDialog(object):
    def setupUi(self, CreateAttachClientsForAreaDialog):
        CreateAttachClientsForAreaDialog.setObjectName(_fromUtf8("CreateAttachClientsForAreaDialog"))
        CreateAttachClientsForAreaDialog.resize(423, 241)
        self.gridLayout = QtGui.QGridLayout(CreateAttachClientsForAreaDialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.lblAreaAddressType = QtGui.QLabel(CreateAttachClientsForAreaDialog)
        self.lblAreaAddressType.setObjectName(_fromUtf8("lblAreaAddressType"))
        self.gridLayout.addWidget(self.lblAreaAddressType, 1, 0, 1, 1)
        self.chkUpdateData = QtGui.QCheckBox(CreateAttachClientsForAreaDialog)
        self.chkUpdateData.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.chkUpdateData.setObjectName(_fromUtf8("chkUpdateData"))
        self.gridLayout.addWidget(self.chkUpdateData, 4, 1, 1, 2)
        self.lblOrgStructure = QtGui.QLabel(CreateAttachClientsForAreaDialog)
        self.lblOrgStructure.setObjectName(_fromUtf8("lblOrgStructure"))
        self.gridLayout.addWidget(self.lblOrgStructure, 0, 0, 1, 1)
        self.chkAttach = QtGui.QCheckBox(CreateAttachClientsForAreaDialog)
        self.chkAttach.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.chkAttach.setChecked(False)
        self.chkAttach.setTristate(False)
        self.chkAttach.setObjectName(_fromUtf8("chkAttach"))
        self.gridLayout.addWidget(self.chkAttach, 2, 1, 1, 2)
        self.lblDeAttachType = QtGui.QLabel(CreateAttachClientsForAreaDialog)
        self.lblDeAttachType.setObjectName(_fromUtf8("lblDeAttachType"))
        self.gridLayout.addWidget(self.lblDeAttachType, 6, 0, 1, 1)
        self.cmbOrgStructure = COrgStructureComboBox(CreateAttachClientsForAreaDialog)
        self.cmbOrgStructure.setEnabled(True)
        self.cmbOrgStructure.setObjectName(_fromUtf8("cmbOrgStructure"))
        self.gridLayout.addWidget(self.cmbOrgStructure, 0, 1, 1, 2)
        self.edtDate = CDateEdit(CreateAttachClientsForAreaDialog)
        self.edtDate.setObjectName(_fromUtf8("edtDate"))
        self.gridLayout.addWidget(self.edtDate, 7, 1, 1, 1)
        self.cmbAreaAddressType = QtGui.QComboBox(CreateAttachClientsForAreaDialog)
        self.cmbAreaAddressType.setObjectName(_fromUtf8("cmbAreaAddressType"))
        self.cmbAreaAddressType.addItem(_fromUtf8(""))
        self.cmbAreaAddressType.addItem(_fromUtf8(""))
        self.gridLayout.addWidget(self.cmbAreaAddressType, 1, 1, 1, 2)
        self.lblDate = QtGui.QLabel(CreateAttachClientsForAreaDialog)
        self.lblDate.setObjectName(_fromUtf8("lblDate"))
        self.gridLayout.addWidget(self.lblDate, 7, 0, 1, 1)
        self.cmbDeAttachType = CRBComboBox(CreateAttachClientsForAreaDialog)
        self.cmbDeAttachType.setObjectName(_fromUtf8("cmbDeAttachType"))
        self.gridLayout.addWidget(self.cmbDeAttachType, 6, 1, 1, 2)
        self.progressBar = CProgressBar(CreateAttachClientsForAreaDialog)
        self.progressBar.setProperty("value", 24)
        self.progressBar.setObjectName(_fromUtf8("progressBar"))
        self.gridLayout.addWidget(self.progressBar, 9, 0, 1, 3)
        self.buttonBox = QtGui.QDialogButtonBox(CreateAttachClientsForAreaDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 8, 0, 1, 3)
        spacerItem = QtGui.QSpacerItem(195, 14, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 7, 2, 1, 1)
        self.chkSaveAttachType = QtGui.QCheckBox(CreateAttachClientsForAreaDialog)
        self.chkSaveAttachType.setEnabled(False)
        self.chkSaveAttachType.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.chkSaveAttachType.setChecked(False)
        self.chkSaveAttachType.setTristate(False)
        self.chkSaveAttachType.setObjectName(_fromUtf8("chkSaveAttachType"))
        self.gridLayout.addWidget(self.chkSaveAttachType, 5, 1, 1, 2)

        self.retranslateUi(CreateAttachClientsForAreaDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), CreateAttachClientsForAreaDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), CreateAttachClientsForAreaDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(CreateAttachClientsForAreaDialog)
        CreateAttachClientsForAreaDialog.setTabOrder(self.cmbOrgStructure, self.cmbAreaAddressType)
        CreateAttachClientsForAreaDialog.setTabOrder(self.cmbAreaAddressType, self.chkAttach)
        CreateAttachClientsForAreaDialog.setTabOrder(self.chkAttach, self.chkUpdateData)
        CreateAttachClientsForAreaDialog.setTabOrder(self.chkUpdateData, self.buttonBox)

    def retranslateUi(self, CreateAttachClientsForAreaDialog):
        CreateAttachClientsForAreaDialog.setWindowTitle(_translate("CreateAttachClientsForAreaDialog", "Выполнить прикрепление пациентов к участкам", None))
        self.lblAreaAddressType.setText(_translate("CreateAttachClientsForAreaDialog", "Участок по адресу", None))
        self.chkUpdateData.setText(_translate("CreateAttachClientsForAreaDialog", "Обновлять данные о прикреплении", None))
        self.lblOrgStructure.setText(_translate("CreateAttachClientsForAreaDialog", "Подразделение", None))
        self.chkAttach.setText(_translate("CreateAttachClientsForAreaDialog", "Учитывать тип прикрепления:  Прикрепление", None))
        self.lblDeAttachType.setText(_translate("CreateAttachClientsForAreaDialog", "Причина открепления", None))
        self.cmbAreaAddressType.setItemText(0, _translate("CreateAttachClientsForAreaDialog", "Регистрация", None))
        self.cmbAreaAddressType.setItemText(1, _translate("CreateAttachClientsForAreaDialog", "Проживание", None))
        self.lblDate.setText(_translate("CreateAttachClientsForAreaDialog", "Прикреплять на дату", None))
        self.chkSaveAttachType.setText(_translate("CreateAttachClientsForAreaDialog", "Сохранять последний тип прикрепления", None))

from OrgStructComboBoxes import COrgStructureComboBox
from library.DateEdit import CDateEdit
from library.ProgressBar import CProgressBar
from library.crbcombobox import CRBComboBox
