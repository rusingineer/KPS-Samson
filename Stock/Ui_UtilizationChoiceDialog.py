# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\samson\Stock\UtilizationChoiceDialog.ui'
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

class Ui_UtilizationChoiceDialog(object):
    def setupUi(self, UtilizationChoiceDialog):
        UtilizationChoiceDialog.setObjectName(_fromUtf8("UtilizationChoiceDialog"))
        UtilizationChoiceDialog.resize(537, 120)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(UtilizationChoiceDialog.sizePolicy().hasHeightForWidth())
        UtilizationChoiceDialog.setSizePolicy(sizePolicy)
        self.gridLayout = QtGui.QGridLayout(UtilizationChoiceDialog)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.cmbDestructionType = CDestructionTypeComboBox(UtilizationChoiceDialog)
        self.cmbDestructionType.setObjectName(_fromUtf8("cmbDestructionType"))
        self.gridLayout.addWidget(self.cmbDestructionType, 1, 1, 1, 1)
        self.cmbReasonDestructionType = CReasonDestructionTypeComboBox(UtilizationChoiceDialog)
        self.cmbReasonDestructionType.setObjectName(_fromUtf8("cmbReasonDestructionType"))
        self.gridLayout.addWidget(self.cmbReasonDestructionType, 3, 1, 1, 1)
        self.edtDecisionWithDrawFromCirculation = QtGui.QLineEdit(UtilizationChoiceDialog)
        self.edtDecisionWithDrawFromCirculation.setObjectName(_fromUtf8("edtDecisionWithDrawFromCirculation"))
        self.gridLayout.addWidget(self.edtDecisionWithDrawFromCirculation, 0, 1, 1, 1)
        self.lblDestructionType = QtGui.QLabel(UtilizationChoiceDialog)
        self.lblDestructionType.setObjectName(_fromUtf8("lblDestructionType"))
        self.gridLayout.addWidget(self.lblDestructionType, 1, 0, 1, 1)
        self.lblDecisionWithDrawFromCirculation = QtGui.QLabel(UtilizationChoiceDialog)
        self.lblDecisionWithDrawFromCirculation.setObjectName(_fromUtf8("lblDecisionWithDrawFromCirculation"))
        self.gridLayout.addWidget(self.lblDecisionWithDrawFromCirculation, 0, 0, 1, 1)
        self.lblReasonDestructionType = QtGui.QLabel(UtilizationChoiceDialog)
        self.lblReasonDestructionType.setObjectName(_fromUtf8("lblReasonDestructionType"))
        self.gridLayout.addWidget(self.lblReasonDestructionType, 3, 0, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(UtilizationChoiceDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 5, 0, 1, 2)

        self.retranslateUi(UtilizationChoiceDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), UtilizationChoiceDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), UtilizationChoiceDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(UtilizationChoiceDialog)

    def retranslateUi(self, UtilizationChoiceDialog):
        UtilizationChoiceDialog.setWindowTitle(_translate("UtilizationChoiceDialog", "Dialog", None))
        self.lblDestructionType.setText(_translate("UtilizationChoiceDialog", "Основание передачи на уничтожение", None))
        self.lblDecisionWithDrawFromCirculation.setText(_translate("UtilizationChoiceDialog", "Решение Росздравнадзора о выводе из оборота", None))
        self.lblReasonDestructionType.setText(_translate("UtilizationChoiceDialog", "Причина передачи на уничтожение", None))

from Stock.Utils import CDestructionTypeComboBox, CReasonDestructionTypeComboBox
