# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\Samson\UP_s11\client_test\library\ESKLP\SmnnComboBoxPopupEx.ui'
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

class Ui_SmnnComboBoxPopupEx(object):
    def setupUi(self, SmnnComboBoxPopupEx):
        SmnnComboBoxPopupEx.setObjectName(_fromUtf8("SmnnComboBoxPopupEx"))
        SmnnComboBoxPopupEx.resize(687, 453)
        self.gridLayout = QtGui.QGridLayout(SmnnComboBoxPopupEx)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.chkOnlyExists = QtGui.QCheckBox(SmnnComboBoxPopupEx)
        self.chkOnlyExists.setObjectName(_fromUtf8("chkOnlyExists"))
        self.gridLayout.addWidget(self.chkOnlyExists, 2, 1, 1, 1)
        self.edtFindName = QtGui.QLineEdit(SmnnComboBoxPopupEx)
        self.edtFindName.setObjectName(_fromUtf8("edtFindName"))
        self.gridLayout.addWidget(self.edtFindName, 2, 0, 1, 1)
        self.tblSmnn = CSortFilterProxyTableView(SmnnComboBoxPopupEx)
        self.tblSmnn.setObjectName(_fromUtf8("tblSmnn"))
        self.gridLayout.addWidget(self.tblSmnn, 3, 0, 1, 2)

        self.retranslateUi(SmnnComboBoxPopupEx)
        QtCore.QMetaObject.connectSlotsByName(SmnnComboBoxPopupEx)
        SmnnComboBoxPopupEx.setTabOrder(self.edtFindName, self.chkOnlyExists)
        SmnnComboBoxPopupEx.setTabOrder(self.chkOnlyExists, self.tblSmnn)

    def retranslateUi(self, SmnnComboBoxPopupEx):
        SmnnComboBoxPopupEx.setWindowTitle(_translate("SmnnComboBoxPopupEx", "Form", None))
        self.chkOnlyExists.setText(_translate("SmnnComboBoxPopupEx", "Только в наличии", None))

from library.SortFilterProxyTableView import CSortFilterProxyTableView
