# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Samson\UP_s11\client_test\RefBooks\ActionType\ActionTypeFindDialog.ui'
#
# Created: Tue Dec 12 12:36:03 2023
#      by: PyQt4 UI code generator 4.11.3
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

class Ui_ActionTypeFindDialog(object):
    def setupUi(self, ActionTypeFindDialog):
        ActionTypeFindDialog.setObjectName(_fromUtf8("ActionTypeFindDialog"))
        ActionTypeFindDialog.resize(670, 398)
        ActionTypeFindDialog.setSizeGripEnabled(True)
        self.gridLayout = QtGui.QGridLayout(ActionTypeFindDialog)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.cmbTissueType = CRBComboBox(ActionTypeFindDialog)
        self.cmbTissueType.setObjectName(_fromUtf8("cmbTissueType"))
        self.gridLayout.addWidget(self.cmbTissueType, 5, 1, 1, 2)
        self.tblActionTypeFound = CTableView(ActionTypeFindDialog)
        self.tblActionTypeFound.setObjectName(_fromUtf8("tblActionTypeFound"))
        self.gridLayout.addWidget(self.tblActionTypeFound, 8, 0, 1, 3)
        self.btnSelectService = QtGui.QToolButton(ActionTypeFindDialog)
        self.btnSelectService.setObjectName(_fromUtf8("btnSelectService"))
        self.gridLayout.addWidget(self.btnSelectService, 6, 2, 1, 1)
        self.lblTissueType = QtGui.QLabel(ActionTypeFindDialog)
        self.lblTissueType.setObjectName(_fromUtf8("lblTissueType"))
        self.gridLayout.addWidget(self.lblTissueType, 5, 0, 1, 1)
        self.edtCode = QtGui.QLineEdit(ActionTypeFindDialog)
        self.edtCode.setObjectName(_fromUtf8("edtCode"))
        self.gridLayout.addWidget(self.edtCode, 0, 1, 1, 2)
        self.edtNomenclativeCode = QtGui.QLineEdit(ActionTypeFindDialog)
        self.edtNomenclativeCode.setObjectName(_fromUtf8("edtNomenclativeCode"))
        self.gridLayout.addWidget(self.edtNomenclativeCode, 2, 1, 1, 2)
        self.edtName = QtGui.QLineEdit(ActionTypeFindDialog)
        self.edtName.setObjectName(_fromUtf8("edtName"))
        self.gridLayout.addWidget(self.edtName, 1, 1, 1, 2)
        self.lblName = QtGui.QLabel(ActionTypeFindDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblName.sizePolicy().hasHeightForWidth())
        self.lblName.setSizePolicy(sizePolicy)
        self.lblName.setObjectName(_fromUtf8("lblName"))
        self.gridLayout.addWidget(self.lblName, 1, 0, 1, 1)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setSpacing(4)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.buttonBox = QtGui.QDialogButtonBox(ActionTypeFindDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.buttonBox.sizePolicy().hasHeightForWidth())
        self.buttonBox.setSizePolicy(sizePolicy)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Apply|QtGui.QDialogButtonBox.Close|QtGui.QDialogButtonBox.Reset)
        self.buttonBox.setCenterButtons(False)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.horizontalLayout.addWidget(self.buttonBox)
        self.gridLayout.addLayout(self.horizontalLayout, 11, 0, 1, 3)
        self.lblRecordsCount = QtGui.QLabel(ActionTypeFindDialog)
        self.lblRecordsCount.setObjectName(_fromUtf8("lblRecordsCount"))
        self.gridLayout.addWidget(self.lblRecordsCount, 10, 0, 1, 3)
        self.lblNomenclativeCode = QtGui.QLabel(ActionTypeFindDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblNomenclativeCode.sizePolicy().hasHeightForWidth())
        self.lblNomenclativeCode.setSizePolicy(sizePolicy)
        self.lblNomenclativeCode.setObjectName(_fromUtf8("lblNomenclativeCode"))
        self.gridLayout.addWidget(self.lblNomenclativeCode, 2, 0, 1, 1)
        self.lblProfilePayment = QtGui.QLabel(ActionTypeFindDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblProfilePayment.sizePolicy().hasHeightForWidth())
        self.lblProfilePayment.setSizePolicy(sizePolicy)
        self.lblProfilePayment.setObjectName(_fromUtf8("lblProfilePayment"))
        self.gridLayout.addWidget(self.lblProfilePayment, 6, 0, 1, 1)
        self.cmbService = CRBComboBox(ActionTypeFindDialog)
        self.cmbService.setObjectName(_fromUtf8("cmbService"))
        self.gridLayout.addWidget(self.cmbService, 6, 1, 1, 1)
        self.lblCode = QtGui.QLabel(ActionTypeFindDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblCode.sizePolicy().hasHeightForWidth())
        self.lblCode.setSizePolicy(sizePolicy)
        self.lblCode.setObjectName(_fromUtf8("lblCode"))
        self.gridLayout.addWidget(self.lblCode, 0, 0, 1, 1)
        self.lblContext = QtGui.QLabel(ActionTypeFindDialog)
        self.lblContext.setObjectName(_fromUtf8("lblContext"))
        self.gridLayout.addWidget(self.lblContext, 3, 0, 1, 1)
        self.edtContext = QtGui.QLineEdit(ActionTypeFindDialog)
        self.edtContext.setObjectName(_fromUtf8("edtContext"))
        self.gridLayout.addWidget(self.edtContext, 3, 1, 1, 2)
        self.lblCodeReports = QtGui.QLabel(ActionTypeFindDialog)
        self.lblCodeReports.setObjectName(_fromUtf8("lblCodeReports"))
        self.gridLayout.addWidget(self.lblCodeReports, 4, 0, 1, 1)
        self.edtCodeReports = QtGui.QLineEdit(ActionTypeFindDialog)
        self.edtCodeReports.setObjectName(_fromUtf8("edtCodeReports"))
        self.gridLayout.addWidget(self.edtCodeReports, 4, 1, 1, 2)
        self.lblTissueType.setBuddy(self.cmbTissueType)
        self.lblName.setBuddy(self.edtName)
        self.lblNomenclativeCode.setBuddy(self.edtNomenclativeCode)
        self.lblProfilePayment.setBuddy(self.cmbService)
        self.lblCode.setBuddy(self.edtCode)

        self.retranslateUi(ActionTypeFindDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), ActionTypeFindDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), ActionTypeFindDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(ActionTypeFindDialog)
        ActionTypeFindDialog.setTabOrder(self.edtCode, self.edtName)
        ActionTypeFindDialog.setTabOrder(self.edtName, self.edtNomenclativeCode)
        ActionTypeFindDialog.setTabOrder(self.edtNomenclativeCode, self.edtContext)
        ActionTypeFindDialog.setTabOrder(self.edtContext, self.cmbTissueType)
        ActionTypeFindDialog.setTabOrder(self.cmbTissueType, self.cmbService)
        ActionTypeFindDialog.setTabOrder(self.cmbService, self.btnSelectService)
        ActionTypeFindDialog.setTabOrder(self.btnSelectService, self.tblActionTypeFound)

    def retranslateUi(self, ActionTypeFindDialog):
        ActionTypeFindDialog.setWindowTitle(_translate("ActionTypeFindDialog", "Dialog", None))
        self.btnSelectService.setText(_translate("ActionTypeFindDialog", "...", None))
        self.lblTissueType.setText(_translate("ActionTypeFindDialog", "&Тип ткани", None))
        self.lblName.setText(_translate("ActionTypeFindDialog", "&Наименование", None))
        self.lblRecordsCount.setText(_translate("ActionTypeFindDialog", "Список пуст", None))
        self.lblNomenclativeCode.setText(_translate("ActionTypeFindDialog", "Номенклатурный код", None))
        self.lblProfilePayment.setText(_translate("ActionTypeFindDialog", "&Услуга", None))
        self.lblCode.setText(_translate("ActionTypeFindDialog", "&Код", None))
        self.lblContext.setText(_translate("ActionTypeFindDialog", "Контекст печати", None))
        self.lblCodeReports.setText(_translate("ActionTypeFindDialog", "Код для отчетов", None))

from library.crbcombobox import CRBComboBox
from library.TableView import CTableView
