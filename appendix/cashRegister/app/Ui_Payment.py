# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/green/s11_trunk/appendix/cashRegister/app/Payment.ui'
#
# Created by: PyQt4 UI code generator 4.12.1
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

class Ui_CPayment(object):
    def setupUi(self, CPayment):
        CPayment.setObjectName(_fromUtf8("CPayment"))
        CPayment.resize(205, 128)
        self.gridLayout = QtGui.QGridLayout(CPayment)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.lblAmount = QtGui.QLabel(CPayment)
        self.lblAmount.setObjectName(_fromUtf8("lblAmount"))
        self.gridLayout.addWidget(self.lblAmount, 0, 0, 1, 1)
        self.edtAmount = QtGui.QDoubleSpinBox(CPayment)
        self.edtAmount.setFocusPolicy(QtCore.Qt.NoFocus)
        self.edtAmount.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.edtAmount.setReadOnly(True)
        self.edtAmount.setPrefix(_fromUtf8(""))
        self.edtAmount.setDecimals(2)
        self.edtAmount.setMaximum(9999999.99)
        self.edtAmount.setObjectName(_fromUtf8("edtAmount"))
        self.gridLayout.addWidget(self.edtAmount, 0, 1, 1, 1)
        self.lblFee = QtGui.QLabel(CPayment)
        self.lblFee.setObjectName(_fromUtf8("lblFee"))
        self.gridLayout.addWidget(self.lblFee, 1, 0, 1, 1)
        self.edtFee = QtGui.QDoubleSpinBox(CPayment)
        self.edtFee.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.edtFee.setDecimals(2)
        self.edtFee.setMaximum(9999999.99)
        self.edtFee.setObjectName(_fromUtf8("edtFee"))
        self.gridLayout.addWidget(self.edtFee, 1, 1, 1, 1)
        self.lblChange = QtGui.QLabel(CPayment)
        self.lblChange.setObjectName(_fromUtf8("lblChange"))
        self.gridLayout.addWidget(self.lblChange, 2, 0, 1, 1)
        self.edtChange = QtGui.QDoubleSpinBox(CPayment)
        self.edtChange.setFocusPolicy(QtCore.Qt.NoFocus)
        self.edtChange.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.edtChange.setReadOnly(True)
        self.edtChange.setPrefix(_fromUtf8(""))
        self.edtChange.setDecimals(2)
        self.edtChange.setMinimum(-9999999.99)
        self.edtChange.setMaximum(9999999.99)
        self.edtChange.setObjectName(_fromUtf8("edtChange"))
        self.gridLayout.addWidget(self.edtChange, 2, 1, 1, 1)
        spacerItem = QtGui.QSpacerItem(20, 1, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 3, 0, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(CPayment)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 4, 0, 1, 2)
        self.lblAmount.setBuddy(self.edtAmount)
        self.lblFee.setBuddy(self.edtFee)
        self.lblChange.setBuddy(self.edtChange)

        self.retranslateUi(CPayment)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), CPayment.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), CPayment.reject)
        QtCore.QMetaObject.connectSlotsByName(CPayment)
        CPayment.setTabOrder(self.edtAmount, self.edtFee)
        CPayment.setTabOrder(self.edtFee, self.edtChange)
        CPayment.setTabOrder(self.edtChange, self.buttonBox)

    def retranslateUi(self, CPayment):
        CPayment.setWindowTitle(_translate("CPayment", "Оплата наличными", None))
        self.lblAmount.setText(_translate("CPayment", "Сумма по счёту", None))
        self.lblFee.setText(_translate("CPayment", "&Внесено", None))
        self.lblChange.setText(_translate("CPayment", "Сдача", None))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    CPayment = QtGui.QDialog()
    ui = Ui_CPayment()
    ui.setupUi(CPayment)
    CPayment.show()
    sys.exit(app.exec_())

