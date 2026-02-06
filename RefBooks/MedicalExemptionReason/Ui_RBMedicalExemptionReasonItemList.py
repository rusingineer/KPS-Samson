# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Projects\Samson\UP_s11\client_test\RefBooks\MedicalExemptionReason\RBMedicalExemptionReasonItemList.ui'
#
# Created: Tue Jun 10 15:18:38 2025
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

class Ui_RBMedicalExemptionReasonItemList(object):
    def setupUi(self, RBMedicalExemptionReasonItemList):
        RBMedicalExemptionReasonItemList.setObjectName(_fromUtf8("RBMedicalExemptionReasonItemList"))
        RBMedicalExemptionReasonItemList.resize(337, 249)
        self.gridLayout = QtGui.QGridLayout(RBMedicalExemptionReasonItemList)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.splitter = QtGui.QSplitter(RBMedicalExemptionReasonItemList)
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.splitter.setObjectName(_fromUtf8("splitter"))
        self.pnlItems = QtGui.QWidget(self.splitter)
        self.pnlItems.setObjectName(_fromUtf8("pnlItems"))
        self.verticalLayout = QtGui.QVBoxLayout(self.pnlItems)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setMargin(0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.tblItems = CTableView(self.pnlItems)
        self.tblItems.setObjectName(_fromUtf8("tblItems"))
        self.verticalLayout.addWidget(self.tblItems)
        self.gridLayout.addWidget(self.splitter, 0, 0, 1, 2)
        self.label = QtGui.QLabel(RBMedicalExemptionReasonItemList)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 1, 0, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(RBMedicalExemptionReasonItemList)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 1, 1, 1, 1)

        self.retranslateUi(RBMedicalExemptionReasonItemList)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), RBMedicalExemptionReasonItemList.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), RBMedicalExemptionReasonItemList.reject)
        QtCore.QMetaObject.connectSlotsByName(RBMedicalExemptionReasonItemList)

    def retranslateUi(self, RBMedicalExemptionReasonItemList):
        RBMedicalExemptionReasonItemList.setWindowTitle(_translate("RBMedicalExemptionReasonItemList", "Dialog", None))
        self.label.setText(_translate("RBMedicalExemptionReasonItemList", "Всего", None))

from library.TableView import CTableView
