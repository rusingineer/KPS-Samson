# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\projects\Samson\UP_s11\client\Events\AnatomicalLocalizationsComboBoxPopup.ui'
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

class Ui_AnatomicalLocalizationsComboBoxPopup(object):
    def setupUi(self, AnatomicalLocalizationsComboBoxPopup):
        AnatomicalLocalizationsComboBoxPopup.setObjectName(_fromUtf8("AnatomicalLocalizationsComboBoxPopup"))
        AnatomicalLocalizationsComboBoxPopup.resize(680, 371)
        self.gridLayout = QtGui.QGridLayout(AnatomicalLocalizationsComboBoxPopup)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.buttonBox = QtGui.QDialogButtonBox(AnatomicalLocalizationsComboBoxPopup)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 8, 0, 1, 2)
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.tblAnatomicalLocalizations = QtGui.QTreeView(AnatomicalLocalizationsComboBoxPopup)
        self.tblAnatomicalLocalizations.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
        self.tblAnatomicalLocalizations.setObjectName(_fromUtf8("tblAnatomicalLocalizations"))
        self.tblAnatomicalLocalizations.header().setVisible(False)
        self.verticalLayout.addWidget(self.tblAnatomicalLocalizations)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.lblSearch = QtGui.QLabel(AnatomicalLocalizationsComboBoxPopup)
        self.lblSearch.setObjectName(_fromUtf8("lblSearch"))
        self.horizontalLayout.addWidget(self.lblSearch)
        self.edtFindWord = QtGui.QLineEdit(AnatomicalLocalizationsComboBoxPopup)
        self.edtFindWord.setObjectName(_fromUtf8("edtFindWord"))
        self.horizontalLayout.addWidget(self.edtFindWord)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.gridLayout.addLayout(self.verticalLayout, 7, 0, 1, 1)

        self.retranslateUi(AnatomicalLocalizationsComboBoxPopup)
        QtCore.QMetaObject.connectSlotsByName(AnatomicalLocalizationsComboBoxPopup)

    def retranslateUi(self, AnatomicalLocalizationsComboBoxPopup):
        AnatomicalLocalizationsComboBoxPopup.setWindowTitle(_translate("AnatomicalLocalizationsComboBoxPopup", "Form", None))
        self.lblSearch.setText(_translate("AnatomicalLocalizationsComboBoxPopup", "Поиск", None))

