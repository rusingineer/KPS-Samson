# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\samson\Accounting\CashDialog.ui'
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

class Ui_CashDialog(object):
    def setupUi(self, CashDialog):
        CashDialog.setObjectName(_fromUtf8("CashDialog"))
        CashDialog.resize(306, 165)
        CashDialog.setSizeGripEnabled(True)
        CashDialog.setModal(True)
        self.gridLayout = QtGui.QGridLayout(CashDialog)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.lblDate = QtGui.QLabel(CashDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblDate.sizePolicy().hasHeightForWidth())
        self.lblDate.setSizePolicy(sizePolicy)
        self.lblDate.setObjectName(_fromUtf8("lblDate"))
        self.gridLayout.addWidget(self.lblDate, 0, 0, 1, 1)
        self.edtDateTime = QtGui.QDateTimeEdit(CashDialog)
        self.edtDateTime.setObjectName(_fromUtf8("edtDateTime"))
        self.gridLayout.addWidget(self.edtDateTime, 0, 1, 1, 1)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 0, 2, 1, 1)
        self.lblCashOperation = QtGui.QLabel(CashDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblCashOperation.sizePolicy().hasHeightForWidth())
        self.lblCashOperation.setSizePolicy(sizePolicy)
        self.lblCashOperation.setObjectName(_fromUtf8("lblCashOperation"))
        self.gridLayout.addWidget(self.lblCashOperation, 1, 0, 1, 1)
        self.cmbCashOperation = CRBComboBox(CashDialog)
        self.cmbCashOperation.setEnabled(True)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Ignored, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cmbCashOperation.sizePolicy().hasHeightForWidth())
        self.cmbCashOperation.setSizePolicy(sizePolicy)
        self.cmbCashOperation.setObjectName(_fromUtf8("cmbCashOperation"))
        self.gridLayout.addWidget(self.cmbCashOperation, 1, 1, 1, 2)
        self.lblSum = QtGui.QLabel(CashDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblSum.sizePolicy().hasHeightForWidth())
        self.lblSum.setSizePolicy(sizePolicy)
        self.lblSum.setObjectName(_fromUtf8("lblSum"))
        self.gridLayout.addWidget(self.lblSum, 4, 0, 1, 1)
        self.edtSum = QtGui.QDoubleSpinBox(CashDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.edtSum.sizePolicy().hasHeightForWidth())
        self.edtSum.setSizePolicy(sizePolicy)
        self.edtSum.setMaximum(9999999.99)
        self.edtSum.setObjectName(_fromUtf8("edtSum"))
        self.gridLayout.addWidget(self.edtSum, 4, 1, 1, 1)
        spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem1, 5, 0, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(CashDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 6, 0, 1, 3)
        self.lblTypePayment = QtGui.QLabel(CashDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblTypePayment.sizePolicy().hasHeightForWidth())
        self.lblTypePayment.setSizePolicy(sizePolicy)
        self.lblTypePayment.setObjectName(_fromUtf8("lblTypePayment"))
        self.gridLayout.addWidget(self.lblTypePayment, 2, 0, 1, 1)
        self.cmbTypePayment = QtGui.QComboBox(CashDialog)
        self.cmbTypePayment.setObjectName(_fromUtf8("cmbTypePayment"))
        self.cmbTypePayment.addItem(_fromUtf8(""))
        self.cmbTypePayment.addItem(_fromUtf8(""))
        self.cmbTypePayment.addItem(_fromUtf8(""))
        self.gridLayout.addWidget(self.cmbTypePayment, 2, 1, 1, 2)
        self.lblDocumentPayment = QtGui.QLabel(CashDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblDocumentPayment.sizePolicy().hasHeightForWidth())
        self.lblDocumentPayment.setSizePolicy(sizePolicy)
        self.lblDocumentPayment.setObjectName(_fromUtf8("lblDocumentPayment"))
        self.gridLayout.addWidget(self.lblDocumentPayment, 3, 0, 1, 1)
        self.edtDocumentPayment = QtGui.QLineEdit(CashDialog)
        self.edtDocumentPayment.setObjectName(_fromUtf8("edtDocumentPayment"))
        self.gridLayout.addWidget(self.edtDocumentPayment, 3, 1, 1, 2)
        self.lblDate.setBuddy(self.edtDateTime)
        self.lblCashOperation.setBuddy(self.cmbCashOperation)
        self.lblSum.setBuddy(self.edtSum)
        self.lblTypePayment.setBuddy(self.cmbTypePayment)
        self.lblDocumentPayment.setBuddy(self.edtDocumentPayment)

        self.retranslateUi(CashDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), CashDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), CashDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(CashDialog)
        CashDialog.setTabOrder(self.edtDateTime, self.cmbCashOperation)
        CashDialog.setTabOrder(self.cmbCashOperation, self.edtSum)
        CashDialog.setTabOrder(self.edtSum, self.buttonBox)

    def retranslateUi(self, CashDialog):
        CashDialog.setWindowTitle(_translate("CashDialog", "Приём оплаты", None))
        self.lblDate.setText(_translate("CashDialog", "Дата и время", None))
        self.lblCashOperation.setText(_translate("CashDialog", "&Кассовая операция", None))
        self.lblSum.setText(_translate("CashDialog", "&Сумма", None))
        self.lblTypePayment.setText(_translate("CashDialog", "&Тип оплаты", None))
        self.cmbTypePayment.setItemText(0, _translate("CashDialog", "наличный", None))
        self.cmbTypePayment.setItemText(1, _translate("CashDialog", "безналичный", None))
        self.cmbTypePayment.setItemText(2, _translate("CashDialog", "по реквизитам", None))
        self.lblDocumentPayment.setText(_translate("CashDialog", "Документ &об оплате", None))

from library.crbcombobox import CRBComboBox
