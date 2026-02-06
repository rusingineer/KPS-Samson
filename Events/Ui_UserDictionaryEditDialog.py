# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/work/kmivc-arch/Samson/client_test/Events/UserDictionaryEditDialog.ui'
#
# Created by: PyQt4 UI code generator 4.12.3
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

class Ui_UserDictionaryEditDialog(object):
    def setupUi(self, UserDictionaryEditDialog):
        UserDictionaryEditDialog.setObjectName(_fromUtf8("UserDictionaryEditDialog"))
        UserDictionaryEditDialog.resize(550, 568)
        self.verticalLayout = QtGui.QVBoxLayout(UserDictionaryEditDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.lblPropertyTypeName = QtGui.QLabel(UserDictionaryEditDialog)
        self.lblPropertyTypeName.setObjectName(_fromUtf8("lblPropertyTypeName"))
        self.verticalLayout.addWidget(self.lblPropertyTypeName)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.edtNewText = QtGui.QPlainTextEdit(UserDictionaryEditDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.edtNewText.sizePolicy().hasHeightForWidth())
        self.edtNewText.setSizePolicy(sizePolicy)
        self.edtNewText.setObjectName(_fromUtf8("edtNewText"))
        self.horizontalLayout.addWidget(self.edtNewText)
        self.btnAddNewText = QtGui.QPushButton(UserDictionaryEditDialog)
        self.btnAddNewText.setObjectName(_fromUtf8("btnAddNewText"))
        self.horizontalLayout.addWidget(self.btnAddNewText)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.lvUserDictionary = QtGui.QListView(UserDictionaryEditDialog)
        self.lvUserDictionary.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.lvUserDictionary.setAlternatingRowColors(True)
        self.lvUserDictionary.setTextElideMode(QtCore.Qt.ElideNone)
        self.lvUserDictionary.setWordWrap(True)
        self.lvUserDictionary.setObjectName(_fromUtf8("lvUserDictionary"))
        self.verticalLayout.addWidget(self.lvUserDictionary)
        self.buttonBox = QtGui.QDialogButtonBox(UserDictionaryEditDialog)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Apply|QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(UserDictionaryEditDialog)
        QtCore.QMetaObject.connectSlotsByName(UserDictionaryEditDialog)

    def retranslateUi(self, UserDictionaryEditDialog):
        UserDictionaryEditDialog.setWindowTitle(_translate("UserDictionaryEditDialog", "Пользовательский словарь", None))
        self.lblPropertyTypeName.setText(_translate("UserDictionaryEditDialog", "lblPropertyTypeName", None))
        self.btnAddNewText.setText(_translate("UserDictionaryEditDialog", "Добавить", None))

