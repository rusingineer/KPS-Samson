# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Projects\Samson\UP_s11\client_test\RefBooks\MedicalExemptionReason\RBMedicalExemptionReasonEditor.ui'
#
# Created: Tue Jun 10 14:39:18 2025
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

class Ui_RBMedicalExemptionReasonEditor(object):
    def setupUi(self, RBMedicalExemptionReasonEditor):
        RBMedicalExemptionReasonEditor.setObjectName(_fromUtf8("RBMedicalExemptionReasonEditor"))
        RBMedicalExemptionReasonEditor.resize(298, 108)
        self.gridLayout = QtGui.QGridLayout(RBMedicalExemptionReasonEditor)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.lblCode = QtGui.QLabel(RBMedicalExemptionReasonEditor)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblCode.sizePolicy().hasHeightForWidth())
        self.lblCode.setSizePolicy(sizePolicy)
        self.lblCode.setObjectName(_fromUtf8("lblCode"))
        self.gridLayout.addWidget(self.lblCode, 0, 0, 1, 1)
        self.edtCode = QtGui.QLineEdit(RBMedicalExemptionReasonEditor)
        self.edtCode.setObjectName(_fromUtf8("edtCode"))
        self.gridLayout.addWidget(self.edtCode, 0, 1, 1, 1)
        self.lblName = QtGui.QLabel(RBMedicalExemptionReasonEditor)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblName.sizePolicy().hasHeightForWidth())
        self.lblName.setSizePolicy(sizePolicy)
        self.lblName.setObjectName(_fromUtf8("lblName"))
        self.gridLayout.addWidget(self.lblName, 1, 0, 1, 1)
        self.edtName = QtGui.QLineEdit(RBMedicalExemptionReasonEditor)
        self.edtName.setObjectName(_fromUtf8("edtName"))
        self.gridLayout.addWidget(self.edtName, 1, 1, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(RBMedicalExemptionReasonEditor)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 2, 0, 1, 2)
        self.lblCode.setBuddy(self.edtCode)
        self.lblName.setBuddy(self.edtName)

        self.retranslateUi(RBMedicalExemptionReasonEditor)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), RBMedicalExemptionReasonEditor.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), RBMedicalExemptionReasonEditor.reject)
        QtCore.QMetaObject.connectSlotsByName(RBMedicalExemptionReasonEditor)

    def retranslateUi(self, RBMedicalExemptionReasonEditor):
        RBMedicalExemptionReasonEditor.setWindowTitle(_translate("RBMedicalExemptionReasonEditor", "Dialog", None))
        self.lblCode.setText(_translate("RBMedicalExemptionReasonEditor", "&Код", None))
        self.lblName.setText(_translate("RBMedicalExemptionReasonEditor", "&Наименование", None))

