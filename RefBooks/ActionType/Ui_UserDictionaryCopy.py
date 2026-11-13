# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/work/kmivc-arch/Samson/client_test/RefBooks/ActionType/UserDictionaryCopy.ui'
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

class Ui_UserDictionaryCopyDialog(object):
    def setupUi(self, UserDictionaryCopyDialog):
        UserDictionaryCopyDialog.setObjectName(_fromUtf8("UserDictionaryCopyDialog"))
        UserDictionaryCopyDialog.resize(384, 445)
        UserDictionaryCopyDialog.setSizeGripEnabled(True)
        self.gridLayout_3 = QtGui.QGridLayout(UserDictionaryCopyDialog)
        self.gridLayout_3.setMargin(4)
        self.gridLayout_3.setSpacing(4)
        self.gridLayout_3.setObjectName(_fromUtf8("gridLayout_3"))
        self.buttonBox = QtGui.QDialogButtonBox(UserDictionaryCopyDialog)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout_3.addWidget(self.buttonBox, 2, 1, 1, 1)
        self.progressBar = QtGui.QProgressBar(UserDictionaryCopyDialog)
        self.progressBar.setProperty("value", 24)
        self.progressBar.setObjectName(_fromUtf8("progressBar"))
        self.gridLayout_3.addWidget(self.progressBar, 2, 0, 1, 1)
        self.tblCopyUserDictionary = CInDocTableView(UserDictionaryCopyDialog)
        self.tblCopyUserDictionary.setObjectName(_fromUtf8("tblCopyUserDictionary"))
        self.gridLayout_3.addWidget(self.tblCopyUserDictionary, 1, 0, 1, 2)
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.cmbActionTypeSource = CActionTypeComboBoxEx(UserDictionaryCopyDialog)
        self.cmbActionTypeSource.setObjectName(_fromUtf8("cmbActionTypeSource"))
        self.gridLayout.addWidget(self.cmbActionTypeSource, 0, 1, 1, 1)
        self.lblActionTypeSource = QtGui.QLabel(UserDictionaryCopyDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblActionTypeSource.sizePolicy().hasHeightForWidth())
        self.lblActionTypeSource.setSizePolicy(sizePolicy)
        self.lblActionTypeSource.setObjectName(_fromUtf8("lblActionTypeSource"))
        self.gridLayout.addWidget(self.lblActionTypeSource, 0, 0, 1, 1)
        self.lblActionTypeNew = QtGui.QLabel(UserDictionaryCopyDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblActionTypeNew.sizePolicy().hasHeightForWidth())
        self.lblActionTypeNew.setSizePolicy(sizePolicy)
        self.lblActionTypeNew.setObjectName(_fromUtf8("lblActionTypeNew"))
        self.gridLayout.addWidget(self.lblActionTypeNew, 1, 0, 1, 1)
        self.cmbActionTypeNew = CActionTypeComboBoxEx(UserDictionaryCopyDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cmbActionTypeNew.sizePolicy().hasHeightForWidth())
        self.cmbActionTypeNew.setSizePolicy(sizePolicy)
        self.cmbActionTypeNew.setObjectName(_fromUtf8("cmbActionTypeNew"))
        self.gridLayout.addWidget(self.cmbActionTypeNew, 1, 1, 1, 1)
        self.gridLayout_3.addLayout(self.gridLayout, 0, 0, 1, 2)

        self.retranslateUi(UserDictionaryCopyDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), UserDictionaryCopyDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), UserDictionaryCopyDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(UserDictionaryCopyDialog)

    def retranslateUi(self, UserDictionaryCopyDialog):
        UserDictionaryCopyDialog.setWindowTitle(_translate("UserDictionaryCopyDialog", "Копирование словаря пользователя", None))
        self.lblActionTypeSource.setText(_translate("UserDictionaryCopyDialog", "Источник", None))
        self.lblActionTypeNew.setText(_translate("UserDictionaryCopyDialog", "Назначение", None))

from Events.ActionTypeComboBoxEx import CActionTypeComboBoxEx
from library.InDocTable import CInDocTableView
