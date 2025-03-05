# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\projects\samson\UP_s11\client_test\ThermalSheet\TemperatureListParameters.ui'
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

class Ui_TemperatureListParameters(object):
    def setupUi(self, TemperatureListParameters):
        TemperatureListParameters.setObjectName(_fromUtf8("TemperatureListParameters"))
        TemperatureListParameters.resize(386, 159)
        self.gridLayout = QtGui.QGridLayout(TemperatureListParameters)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.label_2 = QtGui.QLabel(TemperatureListParameters)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 1)
        self.edtBegDate = CDateEdit(TemperatureListParameters)
        self.edtBegDate.setCalendarPopup(True)
        self.edtBegDate.setObjectName(_fromUtf8("edtBegDate"))
        self.gridLayout.addWidget(self.edtBegDate, 0, 1, 1, 1)
        self.edtEndDate = CDateEdit(TemperatureListParameters)
        self.edtEndDate.setCalendarPopup(True)
        self.edtEndDate.setObjectName(_fromUtf8("edtEndDate"))
        self.gridLayout.addWidget(self.edtEndDate, 0, 2, 1, 1)
        spacerItem = QtGui.QSpacerItem(20, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 0, 3, 1, 1)
        self.chkTemperature = QtGui.QCheckBox(TemperatureListParameters)
        self.chkTemperature.setChecked(True)
        self.chkTemperature.setObjectName(_fromUtf8("chkTemperature"))
        self.gridLayout.addWidget(self.chkTemperature, 1, 0, 1, 1)
        self.chkPulse = QtGui.QCheckBox(TemperatureListParameters)
        self.chkPulse.setObjectName(_fromUtf8("chkPulse"))
        self.gridLayout.addWidget(self.chkPulse, 1, 1, 1, 2)
        self.chkAPMax = QtGui.QCheckBox(TemperatureListParameters)
        self.chkAPMax.setObjectName(_fromUtf8("chkAPMax"))
        self.gridLayout.addWidget(self.chkAPMax, 2, 0, 1, 1)
        self.chkAPMin = QtGui.QCheckBox(TemperatureListParameters)
        self.chkAPMin.setObjectName(_fromUtf8("chkAPMin"))
        self.gridLayout.addWidget(self.chkAPMin, 2, 1, 1, 2)
        self.lblMultipleDimension = QtGui.QLabel(TemperatureListParameters)
        self.lblMultipleDimension.setObjectName(_fromUtf8("lblMultipleDimension"))
        self.gridLayout.addWidget(self.lblMultipleDimension, 3, 0, 1, 1)
        self.edtMultipleDimension = QtGui.QSpinBox(TemperatureListParameters)
        self.edtMultipleDimension.setMinimum(1)
        self.edtMultipleDimension.setMaximum(4)
        self.edtMultipleDimension.setObjectName(_fromUtf8("edtMultipleDimension"))
        self.gridLayout.addWidget(self.edtMultipleDimension, 3, 1, 1, 1)
        spacerItem1 = QtGui.QSpacerItem(136, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem1, 3, 2, 1, 2)
        spacerItem2 = QtGui.QSpacerItem(20, 23, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem2, 4, 0, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(TemperatureListParameters)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 5, 1, 1, 3)

        self.retranslateUi(TemperatureListParameters)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), TemperatureListParameters.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), TemperatureListParameters.reject)
        QtCore.QMetaObject.connectSlotsByName(TemperatureListParameters)

    def retranslateUi(self, TemperatureListParameters):
        TemperatureListParameters.setWindowTitle(_translate("TemperatureListParameters", "Параметры", None))
        self.label_2.setText(_translate("TemperatureListParameters", "Период", None))
        self.chkTemperature.setText(_translate("TemperatureListParameters", "Температура", None))
        self.chkPulse.setText(_translate("TemperatureListParameters", "Пульс", None))
        self.chkAPMax.setText(_translate("TemperatureListParameters", "Максимальное давление", None))
        self.chkAPMin.setText(_translate("TemperatureListParameters", "Минимальное давление", None))
        self.lblMultipleDimension.setText(_translate("TemperatureListParameters", "Кратность измерений", None))

from library.DateEdit import CDateEdit
