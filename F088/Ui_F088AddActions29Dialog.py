# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\Samson\UP_s11\client_test\F088\F088AddActions29Dialog.ui'
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

class Ui_F088AddActions30Dialog(object):
    def setupUi(self, F088AddActions30Dialog):
        F088AddActions30Dialog.setObjectName(_fromUtf8("F088AddActions30Dialog"))
        F088AddActions30Dialog.resize(1129, 231)
        self.gridLayout = QtGui.QGridLayout(F088AddActions30Dialog)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.btnSelectClearAll = QtGui.QPushButton(F088AddActions30Dialog)
        self.btnSelectClearAll.setObjectName(_fromUtf8("btnSelectClearAll"))
        self.gridLayout.addWidget(self.btnSelectClearAll, 1, 9, 1, 1)
        self.btnCancel = QtGui.QPushButton(F088AddActions30Dialog)
        self.btnCancel.setObjectName(_fromUtf8("btnCancel"))
        self.gridLayout.addWidget(self.btnCancel, 1, 10, 1, 1)
        self.edtFindByCode = QtGui.QLineEdit(F088AddActions30Dialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.edtFindByCode.sizePolicy().hasHeightForWidth())
        self.edtFindByCode.setSizePolicy(sizePolicy)
        self.edtFindByCode.setObjectName(_fromUtf8("edtFindByCode"))
        self.gridLayout.addWidget(self.edtFindByCode, 1, 6, 1, 1)
        self.btnSelectAll = QtGui.QPushButton(F088AddActions30Dialog)
        self.btnSelectAll.setObjectName(_fromUtf8("btnSelectAll"))
        self.gridLayout.addWidget(self.btnSelectAll, 1, 8, 1, 1)
        self.chkCheckMKB = QtGui.QCheckBox(F088AddActions30Dialog)
        self.chkCheckMKB.setChecked(True)
        self.chkCheckMKB.setObjectName(_fromUtf8("chkCheckMKB"))
        self.gridLayout.addWidget(self.chkCheckMKB, 2, 4, 1, 1)
        self.lblSelectedCount = QtGui.QLabel(F088AddActions30Dialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblSelectedCount.sizePolicy().hasHeightForWidth())
        self.lblSelectedCount.setSizePolicy(sizePolicy)
        self.lblSelectedCount.setObjectName(_fromUtf8("lblSelectedCount"))
        self.gridLayout.addWidget(self.lblSelectedCount, 1, 0, 1, 2)
        self.btnSave = QtGui.QPushButton(F088AddActions30Dialog)
        self.btnSave.setObjectName(_fromUtf8("btnSave"))
        self.gridLayout.addWidget(self.btnSave, 1, 7, 1, 1)
        self.tblF088AddActions30 = CTableView(F088AddActions30Dialog)
        self.tblF088AddActions30.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
        self.tblF088AddActions30.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tblF088AddActions30.setObjectName(_fromUtf8("tblF088AddActions30"))
        self.gridLayout.addWidget(self.tblF088AddActions30, 0, 0, 1, 11)
        self.chkCheckAge = QtGui.QCheckBox(F088AddActions30Dialog)
        self.chkCheckAge.setChecked(True)
        self.chkCheckAge.setObjectName(_fromUtf8("chkCheckAge"))
        self.gridLayout.addWidget(self.chkCheckAge, 2, 3, 1, 1)
        self.lblFindByCode = QtGui.QLabel(F088AddActions30Dialog)
        self.lblFindByCode.setObjectName(_fromUtf8("lblFindByCode"))
        self.gridLayout.addWidget(self.lblFindByCode, 1, 2, 1, 4)
        self.chkAdditional = QtGui.QCheckBox(F088AddActions30Dialog)
        self.chkAdditional.setObjectName(_fromUtf8("chkAdditional"))
        self.gridLayout.addWidget(self.chkAdditional, 2, 0, 1, 3)
        self.cmbCheckMKB = QtGui.QComboBox(F088AddActions30Dialog)
        self.cmbCheckMKB.setObjectName(_fromUtf8("cmbCheckMKB"))
        self.cmbCheckMKB.addItem(_fromUtf8(""))
        self.cmbCheckMKB.addItem(_fromUtf8(""))
        self.cmbCheckMKB.addItem(_fromUtf8(""))
        self.cmbCheckMKB.addItem(_fromUtf8(""))
        self.gridLayout.addWidget(self.cmbCheckMKB, 2, 5, 1, 2)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 2, 7, 1, 4)

        self.retranslateUi(F088AddActions30Dialog)
        QtCore.QObject.connect(self.btnSave, QtCore.SIGNAL(_fromUtf8("clicked()")), F088AddActions30Dialog.accept)
        QtCore.QObject.connect(self.chkCheckMKB, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.cmbCheckMKB.setEnabled)
        QtCore.QMetaObject.connectSlotsByName(F088AddActions30Dialog)
        F088AddActions30Dialog.setTabOrder(self.tblF088AddActions30, self.edtFindByCode)
        F088AddActions30Dialog.setTabOrder(self.edtFindByCode, self.btnSave)
        F088AddActions30Dialog.setTabOrder(self.btnSave, self.btnSelectAll)
        F088AddActions30Dialog.setTabOrder(self.btnSelectAll, self.btnSelectClearAll)
        F088AddActions30Dialog.setTabOrder(self.btnSelectClearAll, self.btnCancel)
        F088AddActions30Dialog.setTabOrder(self.btnCancel, self.chkCheckMKB)
        F088AddActions30Dialog.setTabOrder(self.chkCheckMKB, self.cmbCheckMKB)

    def retranslateUi(self, F088AddActions30Dialog):
        F088AddActions30Dialog.setWindowTitle(_translate("F088AddActions30Dialog", "Выберите действия", None))
        self.btnSelectClearAll.setText(_translate("F088AddActions30Dialog", "Очистить выбор", None))
        self.btnCancel.setText(_translate("F088AddActions30Dialog", "Отмена", None))
        self.btnSelectAll.setText(_translate("F088AddActions30Dialog", "Выбрать всё", None))
        self.chkCheckMKB.setText(_translate("F088AddActions30Dialog", "Учитывать диагноз:", None))
        self.lblSelectedCount.setText(_translate("F088AddActions30Dialog", "Количество выбранных", None))
        self.btnSave.setText(_translate("F088AddActions30Dialog", "ОК", None))
        self.chkCheckAge.setText(_translate("F088AddActions30Dialog", "Учитывать возраст", None))
        self.lblFindByCode.setText(_translate("F088AddActions30Dialog", "| Поиск по коду или наименованию", None))
        self.chkAdditional.setText(_translate("F088AddActions30Dialog", "Дополнительное", None))
        self.cmbCheckMKB.setItemText(0, _translate("F088AddActions30Dialog", "основное заболевание", None))
        self.cmbCheckMKB.setItemText(1, _translate("F088AddActions30Dialog", "осложнения основного заболевания", None))
        self.cmbCheckMKB.setItemText(2, _translate("F088AddActions30Dialog", "сопутствующие заболевания", None))
        self.cmbCheckMKB.setItemText(3, _translate("F088AddActions30Dialog", "осложнения сопутствующих заболеваний", None))

from library.TableView import CTableView
