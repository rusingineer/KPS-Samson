# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Samson\UP_s11\client_test\Users\SelectPersonDialog.ui'
#
# Created: Tue Jan 30 11:53:08 2024
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

class Ui_SelectPersonDialog(object):
    def setupUi(self, SelectPersonDialog):
        SelectPersonDialog.setObjectName(_fromUtf8("SelectPersonDialog"))
        SelectPersonDialog.resize(812, 300)
        self.gridLayout = QtGui.QGridLayout(SelectPersonDialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.tblPerson = CTableView(SelectPersonDialog)
        self.tblPerson.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.tblPerson.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tblPerson.setObjectName(_fromUtf8("tblPerson"))
        self.gridLayout.addWidget(self.tblPerson, 0, 0, 1, 1)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.chkOrgStructurePerson = QtGui.QCheckBox(SelectPersonDialog)
        self.chkOrgStructurePerson.setObjectName(_fromUtf8("chkOrgStructurePerson"))
        self.horizontalLayout.addWidget(self.chkOrgStructurePerson)
        self.buttonBox = QtGui.QDialogButtonBox(SelectPersonDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.horizontalLayout.addWidget(self.buttonBox)
        self.gridLayout.addLayout(self.horizontalLayout, 1, 0, 1, 1)

        self.retranslateUi(SelectPersonDialog)
        QtCore.QMetaObject.connectSlotsByName(SelectPersonDialog)

    def retranslateUi(self, SelectPersonDialog):
        SelectPersonDialog.setWindowTitle(_translate("SelectPersonDialog", "Сотрудники", None))
        self.chkOrgStructurePerson.setText(_translate("SelectPersonDialog", "Подразделение брать из учетки", None))

from library.TableView import CTableView
