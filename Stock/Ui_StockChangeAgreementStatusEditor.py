# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\samson\Stock\StockChangeAgreementStatusEditor.ui'
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

class Ui_StockChangeAgreementStatusEditor(object):
    def setupUi(self, StockChangeAgreementStatusEditor):
        StockChangeAgreementStatusEditor.setObjectName(_fromUtf8("StockChangeAgreementStatusEditor"))
        StockChangeAgreementStatusEditor.resize(690, 146)
        self.gridLayout = QtGui.QGridLayout(StockChangeAgreementStatusEditor)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.lblAgreementStatus = QtGui.QLabel(StockChangeAgreementStatusEditor)
        self.lblAgreementStatus.setObjectName(_fromUtf8("lblAgreementStatus"))
        self.gridLayout.addWidget(self.lblAgreementStatus, 0, 0, 1, 1)
        self.edtAgreementDate = CDateEdit(StockChangeAgreementStatusEditor)
        self.edtAgreementDate.setCalendarPopup(True)
        self.edtAgreementDate.setObjectName(_fromUtf8("edtAgreementDate"))
        self.gridLayout.addWidget(self.edtAgreementDate, 1, 1, 1, 1)
        spacerItem = QtGui.QSpacerItem(407, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 1, 2, 1, 2)
        self.lblAgreementNote = QtGui.QLabel(StockChangeAgreementStatusEditor)
        self.lblAgreementNote.setObjectName(_fromUtf8("lblAgreementNote"))
        self.gridLayout.addWidget(self.lblAgreementNote, 3, 0, 1, 1)
        spacerItem1 = QtGui.QSpacerItem(380, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem1, 0, 3, 1, 1)
        self.lblAgreement = QtGui.QLabel(StockChangeAgreementStatusEditor)
        self.lblAgreement.setObjectName(_fromUtf8("lblAgreement"))
        self.gridLayout.addWidget(self.lblAgreement, 1, 0, 1, 1)
        self.lblAgreementPerson = QtGui.QLabel(StockChangeAgreementStatusEditor)
        self.lblAgreementPerson.setObjectName(_fromUtf8("lblAgreementPerson"))
        self.gridLayout.addWidget(self.lblAgreementPerson, 2, 0, 1, 1)
        self.cmbAgreementStatus = QtGui.QComboBox(StockChangeAgreementStatusEditor)
        self.cmbAgreementStatus.setObjectName(_fromUtf8("cmbAgreementStatus"))
        self.cmbAgreementStatus.addItem(_fromUtf8(""))
        self.cmbAgreementStatus.addItem(_fromUtf8(""))
        self.cmbAgreementStatus.addItem(_fromUtf8(""))
        self.gridLayout.addWidget(self.cmbAgreementStatus, 0, 1, 1, 2)
        self.cmbAgreementPerson = CPersonComboBoxEx(StockChangeAgreementStatusEditor)
        self.cmbAgreementPerson.setObjectName(_fromUtf8("cmbAgreementPerson"))
        self.gridLayout.addWidget(self.cmbAgreementPerson, 2, 1, 1, 3)
        self.buttonBox = QtGui.QDialogButtonBox(StockChangeAgreementStatusEditor)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 5, 0, 1, 4)
        self.edtAgreementNote = QtGui.QLineEdit(StockChangeAgreementStatusEditor)
        self.edtAgreementNote.setObjectName(_fromUtf8("edtAgreementNote"))
        self.gridLayout.addWidget(self.edtAgreementNote, 3, 1, 1, 3)
        spacerItem2 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem2, 4, 1, 1, 1)
        self.lblAgreementNote.setBuddy(self.edtAgreementNote)

        self.retranslateUi(StockChangeAgreementStatusEditor)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), StockChangeAgreementStatusEditor.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), StockChangeAgreementStatusEditor.reject)
        QtCore.QMetaObject.connectSlotsByName(StockChangeAgreementStatusEditor)
        StockChangeAgreementStatusEditor.setTabOrder(self.cmbAgreementStatus, self.edtAgreementDate)
        StockChangeAgreementStatusEditor.setTabOrder(self.edtAgreementDate, self.cmbAgreementPerson)
        StockChangeAgreementStatusEditor.setTabOrder(self.cmbAgreementPerson, self.edtAgreementNote)
        StockChangeAgreementStatusEditor.setTabOrder(self.edtAgreementNote, self.buttonBox)

    def retranslateUi(self, StockChangeAgreementStatusEditor):
        StockChangeAgreementStatusEditor.setWindowTitle(_translate("StockChangeAgreementStatusEditor", "Изменение статуса согласования", None))
        self.lblAgreementStatus.setText(_translate("StockChangeAgreementStatusEditor", "Статус согласования", None))
        self.edtAgreementDate.setDisplayFormat(_translate("StockChangeAgreementStatusEditor", "dd.MM.yyyy", None))
        self.lblAgreementNote.setText(_translate("StockChangeAgreementStatusEditor", "Примечание к согласованию", None))
        self.lblAgreement.setText(_translate("StockChangeAgreementStatusEditor", "Дата согласования", None))
        self.lblAgreementPerson.setText(_translate("StockChangeAgreementStatusEditor", "Ответственный", None))
        self.cmbAgreementStatus.setItemText(0, _translate("StockChangeAgreementStatusEditor", "Не согласовано", None))
        self.cmbAgreementStatus.setItemText(1, _translate("StockChangeAgreementStatusEditor", "Согласовано", None))
        self.cmbAgreementStatus.setItemText(2, _translate("StockChangeAgreementStatusEditor", "Отклонено", None))

from Orgs.PersonComboBoxEx import CPersonComboBoxEx
from library.DateEdit import CDateEdit
