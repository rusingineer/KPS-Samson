# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\Samson\UP_s11\client_test\library\ESKLP\SmnnGrlsLfNomenclatureExpenseEditorEx.ui'
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

class Ui_SmnnGrlsLfNomenclatureExpenseEditorEx(object):
    def setupUi(self, SmnnGrlsLfNomenclatureExpenseEditorEx):
        SmnnGrlsLfNomenclatureExpenseEditorEx.setObjectName(_fromUtf8("SmnnGrlsLfNomenclatureExpenseEditorEx"))
        SmnnGrlsLfNomenclatureExpenseEditorEx.resize(835, 346)
        self.gridLayout = QtGui.QGridLayout(SmnnGrlsLfNomenclatureExpenseEditorEx)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.buttonBox = QtGui.QDialogButtonBox(SmnnGrlsLfNomenclatureExpenseEditorEx)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 3, 1, 1, 2)
        self.edtFindSmnnName = QtGui.QLineEdit(SmnnGrlsLfNomenclatureExpenseEditorEx)
        self.edtFindSmnnName.setObjectName(_fromUtf8("edtFindSmnnName"))
        self.gridLayout.addWidget(self.edtFindSmnnName, 0, 1, 1, 1)
        self.chkOnlyExists = QtGui.QCheckBox(SmnnGrlsLfNomenclatureExpenseEditorEx)
        self.chkOnlyExists.setObjectName(_fromUtf8("chkOnlyExists"))
        self.gridLayout.addWidget(self.chkOnlyExists, 0, 2, 1, 1)
        self.lblFindGrlsLfName = QtGui.QLabel(SmnnGrlsLfNomenclatureExpenseEditorEx)
        self.lblFindGrlsLfName.setObjectName(_fromUtf8("lblFindGrlsLfName"))
        self.gridLayout.addWidget(self.lblFindGrlsLfName, 1, 0, 1, 1)
        self.edtFindGrlsLfName = QtGui.QLineEdit(SmnnGrlsLfNomenclatureExpenseEditorEx)
        self.edtFindGrlsLfName.setObjectName(_fromUtf8("edtFindGrlsLfName"))
        self.gridLayout.addWidget(self.edtFindGrlsLfName, 1, 1, 1, 1)
        self.lblFindSmnnName = QtGui.QLabel(SmnnGrlsLfNomenclatureExpenseEditorEx)
        self.lblFindSmnnName.setObjectName(_fromUtf8("lblFindSmnnName"))
        self.gridLayout.addWidget(self.lblFindSmnnName, 0, 0, 1, 1)
        self.tblSmnn = CSortFilterProxyTableView(SmnnGrlsLfNomenclatureExpenseEditorEx)
        self.tblSmnn.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tblSmnn.setObjectName(_fromUtf8("tblSmnn"))
        self.gridLayout.addWidget(self.tblSmnn, 2, 0, 1, 3)

        self.retranslateUi(SmnnGrlsLfNomenclatureExpenseEditorEx)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), SmnnGrlsLfNomenclatureExpenseEditorEx.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), SmnnGrlsLfNomenclatureExpenseEditorEx.reject)
        QtCore.QMetaObject.connectSlotsByName(SmnnGrlsLfNomenclatureExpenseEditorEx)
        SmnnGrlsLfNomenclatureExpenseEditorEx.setTabOrder(self.edtFindSmnnName, self.chkOnlyExists)
        SmnnGrlsLfNomenclatureExpenseEditorEx.setTabOrder(self.chkOnlyExists, self.edtFindGrlsLfName)
        SmnnGrlsLfNomenclatureExpenseEditorEx.setTabOrder(self.edtFindGrlsLfName, self.tblSmnn)
        SmnnGrlsLfNomenclatureExpenseEditorEx.setTabOrder(self.tblSmnn, self.buttonBox)

    def retranslateUi(self, SmnnGrlsLfNomenclatureExpenseEditorEx):
        SmnnGrlsLfNomenclatureExpenseEditorEx.setWindowTitle(_translate("SmnnGrlsLfNomenclatureExpenseEditorEx", "Выбор МНН и Формы выпуска", None))
        self.chkOnlyExists.setText(_translate("SmnnGrlsLfNomenclatureExpenseEditorEx", "Только в наличии", None))
        self.lblFindGrlsLfName.setText(_translate("SmnnGrlsLfNomenclatureExpenseEditorEx", "Лекарственная форма", None))
        self.lblFindSmnnName.setText(_translate("SmnnGrlsLfNomenclatureExpenseEditorEx", "МНН", None))

from library.SortFilterProxyTableView import CSortFilterProxyTableView
