# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'EventAddChronicDiseasesDialog.ui'
#
# Created by: PyQt4 UI code generator 4.12.1
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

class Ui_EventAddChronicDiseasesDialog(object):
    def setupUi(self, EventAddChronicDiseasesDialog):
        EventAddChronicDiseasesDialog.setObjectName(_fromUtf8("EventAddChronicDiseasesDialog"))
        EventAddChronicDiseasesDialog.resize(542, 420)
        self.verticalLayout = QtGui.QVBoxLayout(EventAddChronicDiseasesDialog)
        self.verticalLayout.setMargin(4)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.tblChronicalDiagnoses = CInDocTableView(EventAddChronicDiseasesDialog)
        self.tblChronicalDiagnoses.setObjectName(_fromUtf8("tblChronicalDiagnoses"))
        self.verticalLayout.addWidget(self.tblChronicalDiagnoses)
        self.buttonBox = QtGui.QDialogButtonBox(EventAddChronicDiseasesDialog)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(EventAddChronicDiseasesDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), EventAddChronicDiseasesDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), EventAddChronicDiseasesDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(EventAddChronicDiseasesDialog)

    def retranslateUi(self, EventAddChronicDiseasesDialog):
        EventAddChronicDiseasesDialog.setWindowTitle(_translate("EventAddChronicDiseasesDialog", "Выберите хронические диагнозы", None))

from library.InDocTable import CInDocTableView
