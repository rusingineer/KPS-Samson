# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\Samson\UP_s11\client_test\library\ESKLP\SmnnGrlsLfNomenclatureExpenseEditor.ui'
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

class Ui_SmnnGrlsLfNomenclatureExpenseEditor(object):
    def setupUi(self, SmnnGrlsLfNomenclatureExpenseEditor):
        SmnnGrlsLfNomenclatureExpenseEditor.setObjectName(_fromUtf8("SmnnGrlsLfNomenclatureExpenseEditor"))
        SmnnGrlsLfNomenclatureExpenseEditor.resize(835, 346)
        self.gridLayout = QtGui.QGridLayout(SmnnGrlsLfNomenclatureExpenseEditor)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.tblSmnn = CSortFilterProxyTableView(SmnnGrlsLfNomenclatureExpenseEditor)
        self.tblSmnn.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tblSmnn.setObjectName(_fromUtf8("tblSmnn"))
        self.gridLayout.addWidget(self.tblSmnn, 1, 0, 1, 2)
        self.buttonBox = QtGui.QDialogButtonBox(SmnnGrlsLfNomenclatureExpenseEditor)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 2, 0, 1, 2)
        self.edtFindName = QtGui.QLineEdit(SmnnGrlsLfNomenclatureExpenseEditor)
        self.edtFindName.setObjectName(_fromUtf8("edtFindName"))
        self.gridLayout.addWidget(self.edtFindName, 0, 0, 1, 1)
        self.chkOnlyExists = QtGui.QCheckBox(SmnnGrlsLfNomenclatureExpenseEditor)
        self.chkOnlyExists.setObjectName(_fromUtf8("chkOnlyExists"))
        self.gridLayout.addWidget(self.chkOnlyExists, 0, 1, 1, 1)

        self.retranslateUi(SmnnGrlsLfNomenclatureExpenseEditor)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), SmnnGrlsLfNomenclatureExpenseEditor.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), SmnnGrlsLfNomenclatureExpenseEditor.reject)
        QtCore.QMetaObject.connectSlotsByName(SmnnGrlsLfNomenclatureExpenseEditor)
        SmnnGrlsLfNomenclatureExpenseEditor.setTabOrder(self.edtFindName, self.chkOnlyExists)
        SmnnGrlsLfNomenclatureExpenseEditor.setTabOrder(self.chkOnlyExists, self.tblSmnn)
        SmnnGrlsLfNomenclatureExpenseEditor.setTabOrder(self.tblSmnn, self.buttonBox)

    def retranslateUi(self, SmnnGrlsLfNomenclatureExpenseEditor):
        SmnnGrlsLfNomenclatureExpenseEditor.setWindowTitle(_translate("SmnnGrlsLfNomenclatureExpenseEditor", "Выбор МНН и Формы выпуска", None))
        self.chkOnlyExists.setText(_translate("SmnnGrlsLfNomenclatureExpenseEditor", "Только в наличии", None))

from library.SortFilterProxyTableView import CSortFilterProxyTableView
