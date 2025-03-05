# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\projects\samson\UP_s11\client_test\ThermalSheet\TemperatureListGroupEditor.ui'
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

class Ui_TemperatureListGroupEditor(object):
    def setupUi(self, TemperatureListGroupEditor):
        TemperatureListGroupEditor.setObjectName(_fromUtf8("TemperatureListGroupEditor"))
        TemperatureListGroupEditor.resize(437, 368)
        self.gridLayout = QtGui.QGridLayout(TemperatureListGroupEditor)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.edtTime = QtGui.QTimeEdit(TemperatureListGroupEditor)
        self.edtTime.setObjectName(_fromUtf8("edtTime"))
        self.gridLayout.addWidget(self.edtTime, 1, 3, 1, 1)
        self.edtDate = CDateEdit(TemperatureListGroupEditor)
        self.edtDate.setCalendarPopup(True)
        self.edtDate.setObjectName(_fromUtf8("edtDate"))
        self.gridLayout.addWidget(self.edtDate, 1, 0, 1, 1)
        self.lblLastTime = QtGui.QLabel(TemperatureListGroupEditor)
        self.lblLastTime.setText(_fromUtf8(""))
        self.lblLastTime.setObjectName(_fromUtf8("lblLastTime"))
        self.gridLayout.addWidget(self.lblLastTime, 1, 1, 1, 1)
        self.lblExecPerson = QtGui.QLabel(TemperatureListGroupEditor)
        self.lblExecPerson.setObjectName(_fromUtf8("lblExecPerson"))
        self.gridLayout.addWidget(self.lblExecPerson, 2, 0, 1, 1)
        self.lblTime = QtGui.QLabel(TemperatureListGroupEditor)
        self.lblTime.setObjectName(_fromUtf8("lblTime"))
        self.gridLayout.addWidget(self.lblTime, 1, 2, 1, 1)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 1, 4, 1, 1)
        self.cmbExecPerson = CPersonComboBoxEx(TemperatureListGroupEditor)
        self.cmbExecPerson.setObjectName(_fromUtf8("cmbExecPerson"))
        self.gridLayout.addWidget(self.cmbExecPerson, 2, 1, 1, 4)
        self.tblThermalSheet = CInDocTableView(TemperatureListGroupEditor)
        self.tblThermalSheet.setObjectName(_fromUtf8("tblThermalSheet"))
        self.gridLayout.addWidget(self.tblThermalSheet, 3, 0, 1, 5)
        self.buttonBox = QtGui.QDialogButtonBox(TemperatureListGroupEditor)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Save)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 4, 0, 1, 5)

        self.retranslateUi(TemperatureListGroupEditor)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), TemperatureListGroupEditor.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), TemperatureListGroupEditor.reject)
        QtCore.QMetaObject.connectSlotsByName(TemperatureListGroupEditor)
        TemperatureListGroupEditor.setTabOrder(self.edtDate, self.edtTime)
        TemperatureListGroupEditor.setTabOrder(self.edtTime, self.cmbExecPerson)
        TemperatureListGroupEditor.setTabOrder(self.cmbExecPerson, self.tblThermalSheet)
        TemperatureListGroupEditor.setTabOrder(self.tblThermalSheet, self.buttonBox)

    def retranslateUi(self, TemperatureListGroupEditor):
        TemperatureListGroupEditor.setWindowTitle(_translate("TemperatureListGroupEditor", "Ввод данных в температурные листы выбранных пациентов", None))
        self.lblExecPerson.setText(_translate("TemperatureListGroupEditor", "Исполнитель", None))
        self.lblTime.setText(_translate("TemperatureListGroupEditor", "Время", None))

from Orgs.PersonComboBoxEx import CPersonComboBoxEx
from library.DateEdit import CDateEdit
from library.InDocTable import CInDocTableView
