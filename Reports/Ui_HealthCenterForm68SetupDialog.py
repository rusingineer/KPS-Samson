# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Projects\Samson\client_test\Reports\HealthCenterForm68SetupDialog.ui'
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

class Ui_HealthCenterForm68SetupDialog(object):
    def setupUi(self, HealthCenterForm68SetupDialog):
        HealthCenterForm68SetupDialog.setObjectName(_fromUtf8("HealthCenterForm68SetupDialog"))
        HealthCenterForm68SetupDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        HealthCenterForm68SetupDialog.resize(309, 168)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(HealthCenterForm68SetupDialog.sizePolicy().hasHeightForWidth())
        HealthCenterForm68SetupDialog.setSizePolicy(sizePolicy)
        HealthCenterForm68SetupDialog.setSizeGripEnabled(True)
        HealthCenterForm68SetupDialog.setModal(True)
        self.gridLayout = QtGui.QGridLayout(HealthCenterForm68SetupDialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.lblType = QtGui.QLabel(HealthCenterForm68SetupDialog)
        self.lblType.setObjectName(_fromUtf8("lblType"))
        self.gridLayout.addWidget(self.lblType, 0, 0, 1, 1)
        self.cmbType = QtGui.QComboBox(HealthCenterForm68SetupDialog)
        self.cmbType.setObjectName(_fromUtf8("cmbType"))
        self.cmbType.addItem(_fromUtf8(""))
        self.cmbType.addItem(_fromUtf8(""))
        self.gridLayout.addWidget(self.cmbType, 0, 1, 1, 1)
        self.lblReportYear = QtGui.QLabel(HealthCenterForm68SetupDialog)
        self.lblReportYear.setObjectName(_fromUtf8("lblReportYear"))
        self.gridLayout.addWidget(self.lblReportYear, 1, 0, 1, 1)
        self.edtReportYear = QtGui.QSpinBox(HealthCenterForm68SetupDialog)
        self.edtReportYear.setMinimum(2000)
        self.edtReportYear.setMaximum(2500)
        self.edtReportYear.setObjectName(_fromUtf8("edtReportYear"))
        self.gridLayout.addWidget(self.edtReportYear, 1, 1, 1, 1)
        self.chkCumulativeTotal = QtGui.QCheckBox(HealthCenterForm68SetupDialog)
        self.chkCumulativeTotal.setObjectName(_fromUtf8("chkCumulativeTotal"))
        self.gridLayout.addWidget(self.chkCumulativeTotal, 2, 1, 1, 1)
        self.lblMonth = QtGui.QLabel(HealthCenterForm68SetupDialog)
        self.lblMonth.setObjectName(_fromUtf8("lblMonth"))
        self.gridLayout.addWidget(self.lblMonth, 3, 0, 1, 1)
        self.cmbMonth = QtGui.QComboBox(HealthCenterForm68SetupDialog)
        self.cmbMonth.setObjectName(_fromUtf8("cmbMonth"))
        self.cmbMonth.addItem(_fromUtf8(""))
        self.cmbMonth.addItem(_fromUtf8(""))
        self.cmbMonth.addItem(_fromUtf8(""))
        self.cmbMonth.addItem(_fromUtf8(""))
        self.cmbMonth.addItem(_fromUtf8(""))
        self.cmbMonth.addItem(_fromUtf8(""))
        self.cmbMonth.addItem(_fromUtf8(""))
        self.cmbMonth.addItem(_fromUtf8(""))
        self.cmbMonth.addItem(_fromUtf8(""))
        self.cmbMonth.addItem(_fromUtf8(""))
        self.cmbMonth.addItem(_fromUtf8(""))
        self.cmbMonth.addItem(_fromUtf8(""))
        self.gridLayout.addWidget(self.cmbMonth, 3, 1, 1, 1)
        spacerItem = QtGui.QSpacerItem(129, 20, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 4, 0, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(HealthCenterForm68SetupDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 5, 1, 1, 1)

        self.retranslateUi(HealthCenterForm68SetupDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), HealthCenterForm68SetupDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), HealthCenterForm68SetupDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(HealthCenterForm68SetupDialog)
        HealthCenterForm68SetupDialog.setTabOrder(self.edtReportYear, self.buttonBox)

    def retranslateUi(self, HealthCenterForm68SetupDialog):
        HealthCenterForm68SetupDialog.setWindowTitle(_translate("HealthCenterForm68SetupDialog", "Центр Здоровья. Форма 68. ", None))
        self.lblType.setText(_translate("HealthCenterForm68SetupDialog", "Тип отчета", None))
        self.cmbType.setItemText(0, _translate("HealthCenterForm68SetupDialog", "Годовой", None))
        self.cmbType.setItemText(1, _translate("HealthCenterForm68SetupDialog", "Месячный", None))
        self.lblReportYear.setText(_translate("HealthCenterForm68SetupDialog", "Год отчета", None))
        self.chkCumulativeTotal.setText(_translate("HealthCenterForm68SetupDialog", "Накопительным итогом", None))
        self.lblMonth.setText(_translate("HealthCenterForm68SetupDialog", "Месяц", None))
        self.cmbMonth.setItemText(0, _translate("HealthCenterForm68SetupDialog", "Январь", None))
        self.cmbMonth.setItemText(1, _translate("HealthCenterForm68SetupDialog", "Февраль", None))
        self.cmbMonth.setItemText(2, _translate("HealthCenterForm68SetupDialog", "Март", None))
        self.cmbMonth.setItemText(3, _translate("HealthCenterForm68SetupDialog", "Апрель", None))
        self.cmbMonth.setItemText(4, _translate("HealthCenterForm68SetupDialog", "Май", None))
        self.cmbMonth.setItemText(5, _translate("HealthCenterForm68SetupDialog", "Июнь", None))
        self.cmbMonth.setItemText(6, _translate("HealthCenterForm68SetupDialog", "Июль", None))
        self.cmbMonth.setItemText(7, _translate("HealthCenterForm68SetupDialog", "Август", None))
        self.cmbMonth.setItemText(8, _translate("HealthCenterForm68SetupDialog", "Сентябрь", None))
        self.cmbMonth.setItemText(9, _translate("HealthCenterForm68SetupDialog", "Октябрь", None))
        self.cmbMonth.setItemText(10, _translate("HealthCenterForm68SetupDialog", "Ноябрь", None))
        self.cmbMonth.setItemText(11, _translate("HealthCenterForm68SetupDialog", "Декабрь", None))

