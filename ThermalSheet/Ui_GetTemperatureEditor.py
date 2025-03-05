# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\projects\samson\UP_s11\client_test\ThermalSheet\GetTemperatureEditor.ui'
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

class Ui_GetTemperatureEditor(object):
    def setupUi(self, GetTemperatureEditor):
        GetTemperatureEditor.setObjectName(_fromUtf8("GetTemperatureEditor"))
        GetTemperatureEditor.resize(327, 99)
        self.gridLayout = QtGui.QGridLayout(GetTemperatureEditor)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.buttonBox = QtGui.QDialogButtonBox(GetTemperatureEditor)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 3, 0, 1, 2)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 1, 1, 1, 1)
        self.lblNewTemperature = QtGui.QLabel(GetTemperatureEditor)
        self.lblNewTemperature.setObjectName(_fromUtf8("lblNewTemperature"))
        self.gridLayout.addWidget(self.lblNewTemperature, 0, 0, 1, 1)
        self.edtNewTemperature = QtGui.QDoubleSpinBox(GetTemperatureEditor)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.edtNewTemperature.sizePolicy().hasHeightForWidth())
        self.edtNewTemperature.setSizePolicy(sizePolicy)
        self.edtNewTemperature.setDecimals(1)
        self.edtNewTemperature.setMaximum(99.9)
        self.edtNewTemperature.setObjectName(_fromUtf8("edtNewTemperature"))
        self.gridLayout.addWidget(self.edtNewTemperature, 0, 1, 1, 1)

        self.retranslateUi(GetTemperatureEditor)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), GetTemperatureEditor.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), GetTemperatureEditor.reject)
        QtCore.QMetaObject.connectSlotsByName(GetTemperatureEditor)

    def retranslateUi(self, GetTemperatureEditor):
        GetTemperatureEditor.setWindowTitle(_translate("GetTemperatureEditor", "Выбор температуры", None))
        self.lblNewTemperature.setText(_translate("GetTemperatureEditor", "Температура", None))

