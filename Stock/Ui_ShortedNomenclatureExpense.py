# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\samson\Stock\ShortedNomenclatureExpense.ui'
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

class Ui_NonenclatureExpenseDialog(object):
    def setupUi(self, NonenclatureExpenseDialog):
        NonenclatureExpenseDialog.setObjectName(_fromUtf8("NonenclatureExpenseDialog"))
        NonenclatureExpenseDialog.resize(542, 452)
        self.gridLayout = QtGui.QGridLayout(NonenclatureExpenseDialog)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.lblNote = QtGui.QLabel(NonenclatureExpenseDialog)
        self.lblNote.setObjectName(_fromUtf8("lblNote"))
        self.gridLayout.addWidget(self.lblNote, 0, 0, 1, 1)
        self.edtNote = QtGui.QLineEdit(NonenclatureExpenseDialog)
        self.edtNote.setObjectName(_fromUtf8("edtNote"))
        self.gridLayout.addWidget(self.edtNote, 0, 1, 1, 2)
        self.tblItems = CInDocTableView(NonenclatureExpenseDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tblItems.sizePolicy().hasHeightForWidth())
        self.tblItems.setSizePolicy(sizePolicy)
        self.tblItems.setObjectName(_fromUtf8("tblItems"))
        self.gridLayout.addWidget(self.tblItems, 1, 0, 1, 3)
        self.buttonBox = QtGui.QDialogButtonBox(NonenclatureExpenseDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 2, 0, 1, 3)
        self.lblNote.setBuddy(self.edtNote)

        self.retranslateUi(NonenclatureExpenseDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), NonenclatureExpenseDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), NonenclatureExpenseDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(NonenclatureExpenseDialog)
        NonenclatureExpenseDialog.setTabOrder(self.edtNote, self.tblItems)
        NonenclatureExpenseDialog.setTabOrder(self.tblItems, self.buttonBox)

    def retranslateUi(self, NonenclatureExpenseDialog):
        NonenclatureExpenseDialog.setWindowTitle(_translate("NonenclatureExpenseDialog", "Списание ЛСиИМН", None))
        self.lblNote.setText(_translate("NonenclatureExpenseDialog", "Примечания", None))

from library.InDocTable import CInDocTableView
