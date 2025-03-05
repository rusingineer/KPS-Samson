# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\Samson\UP_s11\client_test\RefBooks\Nomenclature\ReleaseFormComboBox.ui'
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

class Ui_ReleaseComboBoxPopup(object):
    def setupUi(self, ReleaseComboBoxPopup):
        ReleaseComboBoxPopup.setObjectName(_fromUtf8("ReleaseComboBoxPopup"))
        ReleaseComboBoxPopup.resize(569, 326)
        ReleaseComboBoxPopup.setFrameShape(QtGui.QFrame.StyledPanel)
        ReleaseComboBoxPopup.setFrameShadow(QtGui.QFrame.Raised)
        self.gridLayout = QtGui.QGridLayout(ReleaseComboBoxPopup)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.edtName = QtGui.QLineEdit(ReleaseComboBoxPopup)
        self.edtName.setObjectName(_fromUtf8("edtName"))
        self.gridLayout.addWidget(self.edtName, 0, 1, 1, 2)
        self.edtDosage = QtGui.QLineEdit(ReleaseComboBoxPopup)
        self.edtDosage.setObjectName(_fromUtf8("edtDosage"))
        self.gridLayout.addWidget(self.edtDosage, 1, 1, 1, 2)
        self.lblDosage = QtGui.QLabel(ReleaseComboBoxPopup)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblDosage.sizePolicy().hasHeightForWidth())
        self.lblDosage.setSizePolicy(sizePolicy)
        self.lblDosage.setObjectName(_fromUtf8("lblDosage"))
        self.gridLayout.addWidget(self.lblDosage, 1, 0, 1, 1)
        self.lblName = QtGui.QLabel(ReleaseComboBoxPopup)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblName.sizePolicy().hasHeightForWidth())
        self.lblName.setSizePolicy(sizePolicy)
        self.lblName.setObjectName(_fromUtf8("lblName"))
        self.gridLayout.addWidget(self.lblName, 0, 0, 1, 1)
        self.chkOnlyESKLP = QtGui.QCheckBox(ReleaseComboBoxPopup)
        self.chkOnlyESKLP.setObjectName(_fromUtf8("chkOnlyESKLP"))
        self.gridLayout.addWidget(self.chkOnlyESKLP, 2, 0, 1, 2)
        self.buttonBox = QtGui.QDialogButtonBox(ReleaseComboBoxPopup)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.buttonBox.sizePolicy().hasHeightForWidth())
        self.buttonBox.setSizePolicy(sizePolicy)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Apply|QtGui.QDialogButtonBox.Reset)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 2, 2, 1, 1)
        self.tableView = CTableView(ReleaseComboBoxPopup)
        self.tableView.setObjectName(_fromUtf8("tableView"))
        self.gridLayout.addWidget(self.tableView, 3, 0, 1, 3)

        self.retranslateUi(ReleaseComboBoxPopup)
        QtCore.QMetaObject.connectSlotsByName(ReleaseComboBoxPopup)

    def retranslateUi(self, ReleaseComboBoxPopup):
        self.lblDosage.setText(_translate("ReleaseComboBoxPopup", "Дозировка", None))
        self.lblName.setText(_translate("ReleaseComboBoxPopup", "Наименование", None))
        self.chkOnlyESKLP.setText(_translate("ReleaseComboBoxPopup", "Только по ЕСКЛП", None))

from library.TableView import CTableView
