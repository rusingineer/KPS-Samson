# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\samson\Stock\InventoryFillDialog.ui'
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

class Ui_InventoryFillDialog(object):
    def setupUi(self, InventoryFillDialog):
        InventoryFillDialog.setObjectName(_fromUtf8("InventoryFillDialog"))
        InventoryFillDialog.resize(480, 118)
        self.gridLayout = QtGui.QGridLayout(InventoryFillDialog)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.lblClass = QtGui.QLabel(InventoryFillDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblClass.sizePolicy().hasHeightForWidth())
        self.lblClass.setSizePolicy(sizePolicy)
        self.lblClass.setObjectName(_fromUtf8("lblClass"))
        self.gridLayout.addWidget(self.lblClass, 0, 0, 1, 1)
        self.cmbType = CRBComboBox(InventoryFillDialog)
        self.cmbType.setObjectName(_fromUtf8("cmbType"))
        self.gridLayout.addWidget(self.cmbType, 2, 1, 1, 2)
        self.cmbKind = CRBComboBox(InventoryFillDialog)
        self.cmbKind.setObjectName(_fromUtf8("cmbKind"))
        self.gridLayout.addWidget(self.cmbKind, 1, 1, 1, 2)
        self.cmbClass = CRBComboBox(InventoryFillDialog)
        self.cmbClass.setObjectName(_fromUtf8("cmbClass"))
        self.gridLayout.addWidget(self.cmbClass, 0, 1, 1, 2)
        self.lblKind = QtGui.QLabel(InventoryFillDialog)
        self.lblKind.setObjectName(_fromUtf8("lblKind"))
        self.gridLayout.addWidget(self.lblKind, 1, 0, 1, 1)
        self.lblType = QtGui.QLabel(InventoryFillDialog)
        self.lblType.setObjectName(_fromUtf8("lblType"))
        self.gridLayout.addWidget(self.lblType, 2, 0, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(InventoryFillDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.buttonBox.sizePolicy().hasHeightForWidth())
        self.buttonBox.setSizePolicy(sizePolicy)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Apply|QtGui.QDialogButtonBox.Reset)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 5, 2, 1, 1)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 4, 1, 1, 1)
        self.edtName = QtGui.QLineEdit(InventoryFillDialog)
        self.edtName.setObjectName(_fromUtf8("edtName"))
        self.gridLayout.addWidget(self.edtName, 3, 1, 1, 2)
        self.lblName = QtGui.QLabel(InventoryFillDialog)
        self.lblName.setObjectName(_fromUtf8("lblName"))
        self.gridLayout.addWidget(self.lblName, 3, 0, 1, 1)
        self.lblClass.setBuddy(self.cmbClass)
        self.lblKind.setBuddy(self.cmbKind)
        self.lblType.setBuddy(self.cmbType)

        self.retranslateUi(InventoryFillDialog)
        QtCore.QMetaObject.connectSlotsByName(InventoryFillDialog)
        InventoryFillDialog.setTabOrder(self.cmbClass, self.cmbKind)
        InventoryFillDialog.setTabOrder(self.cmbKind, self.cmbType)
        InventoryFillDialog.setTabOrder(self.cmbType, self.edtName)
        InventoryFillDialog.setTabOrder(self.edtName, self.buttonBox)

    def retranslateUi(self, InventoryFillDialog):
        InventoryFillDialog.setWindowTitle(_translate("InventoryFillDialog", "По отбору", None))
        self.lblClass.setText(_translate("InventoryFillDialog", "&Класс", None))
        self.lblKind.setText(_translate("InventoryFillDialog", "&Вид", None))
        self.lblType.setText(_translate("InventoryFillDialog", "&Тип", None))
        self.lblName.setText(_translate("InventoryFillDialog", "Наименование cодержит", None))

from library.crbcombobox import CRBComboBox
