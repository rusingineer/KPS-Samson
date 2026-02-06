# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\projects\Samson\UP_s11\client\Users\Login.ui'
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

class Ui_LoginDialog(object):
    def setupUi(self, LoginDialog):
        LoginDialog.setObjectName(_fromUtf8("LoginDialog"))
        LoginDialog.resize(197, 103)
        self.gridlayout = QtGui.QGridLayout(LoginDialog)
        self.gridlayout.setMargin(6)
        self.gridlayout.setSpacing(6)
        self.gridlayout.setObjectName(_fromUtf8("gridlayout"))
        self.lblPassword = QtGui.QLabel(LoginDialog)
        self.lblPassword.setObjectName(_fromUtf8("lblPassword"))
        self.gridlayout.addWidget(self.lblPassword, 1, 0, 1, 1)
        self.lblLogin = QtGui.QLabel(LoginDialog)
        self.lblLogin.setObjectName(_fromUtf8("lblLogin"))
        self.gridlayout.addWidget(self.lblLogin, 0, 0, 1, 1)
        self.edtPassword = CPasswordEdit(LoginDialog)
        self.edtPassword.setEchoMode(QtGui.QLineEdit.Password)
        self.edtPassword.setObjectName(_fromUtf8("edtPassword"))
        self.gridlayout.addWidget(self.edtPassword, 1, 1, 1, 1)
        self.edtLogin = QtGui.QLineEdit(LoginDialog)
        self.edtLogin.setObjectName(_fromUtf8("edtLogin"))
        self.gridlayout.addWidget(self.edtLogin, 0, 1, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(LoginDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridlayout.addWidget(self.buttonBox, 3, 0, 1, 2)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridlayout.addItem(spacerItem, 2, 0, 1, 1)
        self.lblPassword.setBuddy(self.edtPassword)
        self.lblLogin.setBuddy(self.edtLogin)

        self.retranslateUi(LoginDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), LoginDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), LoginDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(LoginDialog)
        LoginDialog.setTabOrder(self.edtLogin, self.edtPassword)
        LoginDialog.setTabOrder(self.edtPassword, self.buttonBox)

    def retranslateUi(self, LoginDialog):
        LoginDialog.setWindowTitle(_translate("LoginDialog", "Регистрация", None))
        self.lblPassword.setText(_translate("LoginDialog", "&Пароль", None))
        self.lblLogin.setText(_translate("LoginDialog", "&Имя", None))

from library.PasswordEdit import CPasswordEdit
