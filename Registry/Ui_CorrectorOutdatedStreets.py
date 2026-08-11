# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\work\_SVN\client_test\Registry\CorrectorOutdatedStreets.ui'
#
# Created: Fri Aug 08 13:46:46 2025
#      by: PyQt4 UI code generator 4.11.3
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

class Ui_CorrectorOutdatedStreetsDialog(object):
    def setupUi(self, CorrectorOutdatedStreetsDialog):
        CorrectorOutdatedStreetsDialog.setObjectName(_fromUtf8("CorrectorOutdatedStreetsDialog"))
        CorrectorOutdatedStreetsDialog.resize(748, 584)
        self.gridLayout = QtGui.QGridLayout(CorrectorOutdatedStreetsDialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.lblAddress = QtGui.QLabel(CorrectorOutdatedStreetsDialog)
        self.lblAddress.setObjectName(_fromUtf8("lblAddress"))
        self.gridLayout.addWidget(self.lblAddress, 0, 0, 1, 1)
        self.cmbAddress = CKLADRComboBox(CorrectorOutdatedStreetsDialog)
        self.cmbAddress.setObjectName(_fromUtf8("cmbAddress"))
        self.gridLayout.addWidget(self.cmbAddress, 0, 1, 1, 1)
        self.lblStreet = QtGui.QLabel(CorrectorOutdatedStreetsDialog)
        self.lblStreet.setObjectName(_fromUtf8("lblStreet"))
        self.gridLayout.addWidget(self.lblStreet, 1, 0, 1, 1)
        self.edtStreet = QtGui.QLineEdit(CorrectorOutdatedStreetsDialog)
        self.edtStreet.setObjectName(_fromUtf8("edtStreet"))
        self.gridLayout.addWidget(self.edtStreet, 1, 1, 1, 1)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.btnUpdate = QtGui.QPushButton(CorrectorOutdatedStreetsDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnUpdate.sizePolicy().hasHeightForWidth())
        self.btnUpdate.setSizePolicy(sizePolicy)
        self.btnUpdate.setObjectName(_fromUtf8("btnUpdate"))
        self.horizontalLayout.addWidget(self.btnUpdate)
        self.gridLayout.addLayout(self.horizontalLayout, 1, 2, 1, 1)
        self.lblInfo = QtGui.QLabel(CorrectorOutdatedStreetsDialog)
        self.lblInfo.setObjectName(_fromUtf8("lblInfo"))
        self.gridLayout.addWidget(self.lblInfo, 3, 0, 1, 1)
        self.tbl = CTableView(CorrectorOutdatedStreetsDialog)
        self.tbl.setSortingEnabled(True)
        self.tbl.setObjectName(_fromUtf8("tbl"))
        self.gridLayout.addWidget(self.tbl, 2, 0, 1, 3)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.buttonBox = QtGui.QDialogButtonBox(CorrectorOutdatedStreetsDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.buttonBox.sizePolicy().hasHeightForWidth())
        self.buttonBox.setSizePolicy(sizePolicy)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.horizontalLayout_2.addWidget(self.buttonBox)
        self.gridLayout.addLayout(self.horizontalLayout_2, 3, 1, 1, 2)

        self.retranslateUi(CorrectorOutdatedStreetsDialog)
        QtCore.QMetaObject.connectSlotsByName(CorrectorOutdatedStreetsDialog)

    def retranslateUi(self, CorrectorOutdatedStreetsDialog):
        CorrectorOutdatedStreetsDialog.setWindowTitle(_translate("CorrectorOutdatedStreetsDialog", "Dialog", None))
        self.lblAddress.setText(_translate("CorrectorOutdatedStreetsDialog", "Населенный пункт", None))
        self.lblStreet.setText(_translate("CorrectorOutdatedStreetsDialog", "Поиск улицы", None))
        self.btnUpdate.setText(_translate("CorrectorOutdatedStreetsDialog", "Обновить", None))
        self.lblInfo.setText(_translate("CorrectorOutdatedStreetsDialog", "Всего записей: 0", None))

from library.TableView import CTableView
from KLADR.kladrComboxes import CKLADRComboBox
