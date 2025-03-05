# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\Samson\UP_s11\client_test\library\ESKLP\SmnnGrlsLfComboBoxPopupEx.ui'
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

class Ui_SmnnGrlsLfComboBoxPopupEx(object):
    def setupUi(self, SmnnGrlsLfComboBoxPopupEx):
        SmnnGrlsLfComboBoxPopupEx.setObjectName(_fromUtf8("SmnnGrlsLfComboBoxPopupEx"))
        SmnnGrlsLfComboBoxPopupEx.resize(687, 453)
        self.gridLayout = QtGui.QGridLayout(SmnnGrlsLfComboBoxPopupEx)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.tblSmnn = CTableView(SmnnGrlsLfComboBoxPopupEx)
        self.tblSmnn.setObjectName(_fromUtf8("tblSmnn"))
        self.gridLayout.addWidget(self.tblSmnn, 4, 0, 1, 2)
        self.chkOnlyExists = QtGui.QCheckBox(SmnnGrlsLfComboBoxPopupEx)
        self.chkOnlyExists.setObjectName(_fromUtf8("chkOnlyExists"))
        self.gridLayout.addWidget(self.chkOnlyExists, 3, 0, 1, 2)

        self.retranslateUi(SmnnGrlsLfComboBoxPopupEx)
        QtCore.QMetaObject.connectSlotsByName(SmnnGrlsLfComboBoxPopupEx)

    def retranslateUi(self, SmnnGrlsLfComboBoxPopupEx):
        SmnnGrlsLfComboBoxPopupEx.setWindowTitle(_translate("SmnnGrlsLfComboBoxPopupEx", "Form", None))
        self.chkOnlyExists.setText(_translate("SmnnGrlsLfComboBoxPopupEx", "Только в наличии", None))

from library.TableView import CTableView
