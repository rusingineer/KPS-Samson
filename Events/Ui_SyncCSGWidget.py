# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\projects\Samson\UP_s11\client\Events\SyncCSGWidget.ui'
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

class Ui_SyncCSGDialog(object):
    def setupUi(self, SyncCSGDialog):
        SyncCSGDialog.setObjectName(_fromUtf8("SyncCSGDialog"))
        SyncCSGDialog.resize(827, 307)
        self.gridLayout = QtGui.QGridLayout(SyncCSGDialog)
        self.gridLayout.setMargin(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.tblActions = QtGui.QTableView(SyncCSGDialog)
        self.tblActions.setObjectName(_fromUtf8("tblActions"))
        self.gridLayout.addWidget(self.tblActions, 2, 0, 1, 3)
        spacerItem = QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 3, 1, 1, 1)
        self.lblInfo = QtGui.QLabel(SyncCSGDialog)
        self.lblInfo.setObjectName(_fromUtf8("lblInfo"))
        self.gridLayout.addWidget(self.lblInfo, 1, 0, 1, 3)
        self.buttonBox = QtGui.QDialogButtonBox(SyncCSGDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 5, 0, 1, 3)

        self.retranslateUi(SyncCSGDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), SyncCSGDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), SyncCSGDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(SyncCSGDialog)

    def retranslateUi(self, SyncCSGDialog):
        SyncCSGDialog.setWindowTitle(_translate("SyncCSGDialog", "Синхронизация Действий движения с КСГ", None))
        self.lblInfo.setText(_translate("SyncCSGDialog", "Синхронизация Действий движения с КСГ", None))

