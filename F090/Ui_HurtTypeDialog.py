# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\Samson\UP_s11\client\F090\HurtTypeDialog.ui'
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

class Ui_HurtTypeDialog(object):
    def setupUi(self, HurtTypeDialog):
        HurtTypeDialog.setObjectName(_fromUtf8("HurtTypeDialog"))
        HurtTypeDialog.resize(400, 300)
        self.gridLayout = QtGui.QGridLayout(HurtTypeDialog)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.tblHurtType = CTableView(HurtTypeDialog)
        self.tblHurtType.setObjectName(_fromUtf8("tblHurtType"))
        self.gridLayout.addWidget(self.tblHurtType, 0, 0, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(HurtTypeDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 1, 0, 1, 1)

        self.retranslateUi(HurtTypeDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), HurtTypeDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), HurtTypeDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(HurtTypeDialog)

    def retranslateUi(self, HurtTypeDialog):
        HurtTypeDialog.setWindowTitle(_translate("HurtTypeDialog", "Выполняемые работы из регистрационной карты пациента", None))

from library.TableView import CTableView
