# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\projects\samson\UP_s11\client_pre_release\appendix\mes\ExchangeLocal\ExportXML_Wizard_1.ui'
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

class Ui_ExportXML_Wizard_1(object):
    def setupUi(self, ExportXML_Wizard_1):
        ExportXML_Wizard_1.setObjectName(_fromUtf8("ExportXML_Wizard_1"))
        ExportXML_Wizard_1.setWindowModality(QtCore.Qt.NonModal)
        ExportXML_Wizard_1.resize(766, 272)
        self.gridLayout = QtGui.QGridLayout(ExportXML_Wizard_1)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.tblItems = CInDocTableView(ExportXML_Wizard_1)
        self.tblItems.setTabKeyNavigation(False)
        self.tblItems.setAlternatingRowColors(True)
        self.tblItems.setObjectName(_fromUtf8("tblItems"))
        self.gridLayout.addWidget(self.tblItems, 1, 0, 1, 2)
        spacerItem = QtGui.QSpacerItem(564, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 2, 0, 1, 1)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.btnSelectAll = QtGui.QPushButton(ExportXML_Wizard_1)
        self.btnSelectAll.setObjectName(_fromUtf8("btnSelectAll"))
        self.horizontalLayout.addWidget(self.btnSelectAll)
        self.btnClearSelection = QtGui.QPushButton(ExportXML_Wizard_1)
        self.btnClearSelection.setObjectName(_fromUtf8("btnClearSelection"))
        self.horizontalLayout.addWidget(self.btnClearSelection)
        self.gridLayout.addLayout(self.horizontalLayout, 2, 1, 1, 1)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.lblCodeFilter = QtGui.QLabel(ExportXML_Wizard_1)
        self.lblCodeFilter.setObjectName(_fromUtf8("lblCodeFilter"))
        self.horizontalLayout_2.addWidget(self.lblCodeFilter)
        self.edtCodeFilter = QtGui.QLineEdit(ExportXML_Wizard_1)
        self.edtCodeFilter.setObjectName(_fromUtf8("edtCodeFilter"))
        self.horizontalLayout_2.addWidget(self.edtCodeFilter)
        self.lblNameFilter = QtGui.QLabel(ExportXML_Wizard_1)
        self.lblNameFilter.setObjectName(_fromUtf8("lblNameFilter"))
        self.horizontalLayout_2.addWidget(self.lblNameFilter)
        self.edtNameFilter = QtGui.QLineEdit(ExportXML_Wizard_1)
        self.edtNameFilter.setObjectName(_fromUtf8("edtNameFilter"))
        self.horizontalLayout_2.addWidget(self.edtNameFilter)
        self.btnFilter = QtGui.QPushButton(ExportXML_Wizard_1)
        self.btnFilter.setObjectName(_fromUtf8("btnFilter"))
        self.horizontalLayout_2.addWidget(self.btnFilter)
        self.gridLayout.addLayout(self.horizontalLayout_2, 0, 0, 1, 2)

        self.retranslateUi(ExportXML_Wizard_1)
        QtCore.QMetaObject.connectSlotsByName(ExportXML_Wizard_1)
        ExportXML_Wizard_1.setTabOrder(self.edtCodeFilter, self.edtNameFilter)
        ExportXML_Wizard_1.setTabOrder(self.edtNameFilter, self.btnFilter)
        ExportXML_Wizard_1.setTabOrder(self.btnFilter, self.tblItems)
        ExportXML_Wizard_1.setTabOrder(self.tblItems, self.btnSelectAll)
        ExportXML_Wizard_1.setTabOrder(self.btnSelectAll, self.btnClearSelection)

    def retranslateUi(self, ExportXML_Wizard_1):
        ExportXML_Wizard_1.setWindowTitle(_translate("ExportXML_Wizard_1", "Выбор экспортируемых МЭСов", None))
        self.tblItems.setWhatsThis(_translate("ExportXML_Wizard_1", "список записей", "ура!"))
        self.btnSelectAll.setText(_translate("ExportXML_Wizard_1", "Выбрать все", None))
        self.btnClearSelection.setText(_translate("ExportXML_Wizard_1", "Очистить", None))
        self.lblCodeFilter.setText(_translate("ExportXML_Wizard_1", "Код", None))
        self.lblNameFilter.setText(_translate("ExportXML_Wizard_1", "Наименование", None))
        self.btnFilter.setText(_translate("ExportXML_Wizard_1", "Применить", None))

from library.InDocTable import CInDocTableView
