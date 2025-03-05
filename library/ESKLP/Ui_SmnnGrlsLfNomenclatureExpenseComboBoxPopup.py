# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\Samson\UP_s11\client_test\library\ESKLP\SmnnGrlsLfNomenclatureExpenseComboBoxPopup.ui'
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

class Ui_SmnnGrlsLfNomenclatureExpenseComboBoxPopup(object):
    def setupUi(self, SmnnGrlsLfNomenclatureExpenseComboBoxPopup):
        SmnnGrlsLfNomenclatureExpenseComboBoxPopup.setObjectName(_fromUtf8("SmnnGrlsLfNomenclatureExpenseComboBoxPopup"))
        SmnnGrlsLfNomenclatureExpenseComboBoxPopup.resize(687, 453)
        self.gridLayout = QtGui.QGridLayout(SmnnGrlsLfNomenclatureExpenseComboBoxPopup)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.chkOnlyExists = QtGui.QCheckBox(SmnnGrlsLfNomenclatureExpenseComboBoxPopup)
        self.chkOnlyExists.setObjectName(_fromUtf8("chkOnlyExists"))
        self.gridLayout.addWidget(self.chkOnlyExists, 2, 1, 1, 1)
        self.edtFindName = QtGui.QLineEdit(SmnnGrlsLfNomenclatureExpenseComboBoxPopup)
        self.edtFindName.setObjectName(_fromUtf8("edtFindName"))
        self.gridLayout.addWidget(self.edtFindName, 2, 0, 1, 1)
        self.tblSmnn = CSortFilterProxyTableView(SmnnGrlsLfNomenclatureExpenseComboBoxPopup)
        self.tblSmnn.setObjectName(_fromUtf8("tblSmnn"))
        self.gridLayout.addWidget(self.tblSmnn, 3, 0, 1, 2)

        self.retranslateUi(SmnnGrlsLfNomenclatureExpenseComboBoxPopup)
        QtCore.QMetaObject.connectSlotsByName(SmnnGrlsLfNomenclatureExpenseComboBoxPopup)
        SmnnGrlsLfNomenclatureExpenseComboBoxPopup.setTabOrder(self.edtFindName, self.chkOnlyExists)
        SmnnGrlsLfNomenclatureExpenseComboBoxPopup.setTabOrder(self.chkOnlyExists, self.tblSmnn)

    def retranslateUi(self, SmnnGrlsLfNomenclatureExpenseComboBoxPopup):
        SmnnGrlsLfNomenclatureExpenseComboBoxPopup.setWindowTitle(_translate("SmnnGrlsLfNomenclatureExpenseComboBoxPopup", "Form", None))
        self.chkOnlyExists.setText(_translate("SmnnGrlsLfNomenclatureExpenseComboBoxPopup", "Только в наличии", None))

from library.SortFilterProxyTableView import CSortFilterProxyTableView
