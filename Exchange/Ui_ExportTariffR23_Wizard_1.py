# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\Exchange\ExportTariffR23_Wizard_1.ui'
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

class Ui_ExportTariff_Wizard_1(object):
    def setupUi(self, ExportTariff_Wizard_1):
        ExportTariff_Wizard_1.setObjectName(_fromUtf8("ExportTariff_Wizard_1"))
        ExportTariff_Wizard_1.setWindowModality(QtCore.Qt.NonModal)
        ExportTariff_Wizard_1.resize(411, 286)
        self.gridLayout = QtGui.QGridLayout(ExportTariff_Wizard_1)
        self.gridLayout.setMargin(0)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.chkActive = QtGui.QCheckBox(ExportTariff_Wizard_1)
        self.chkActive.setObjectName(_fromUtf8("chkActive"))
        self.gridLayout.addWidget(self.chkActive, 3, 0, 1, 1)
        self.btnSelectAll = QtGui.QPushButton(ExportTariff_Wizard_1)
        self.btnSelectAll.setObjectName(_fromUtf8("btnSelectAll"))
        self.gridLayout.addWidget(self.btnSelectAll, 10, 1, 1, 1)
        self._2 = QtGui.QHBoxLayout()
        self._2.setObjectName(_fromUtf8("_2"))
        self.label = QtGui.QLabel(ExportTariff_Wizard_1)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setObjectName(_fromUtf8("label"))
        self._2.addWidget(self.label)
        self.edtFilterBegDateFrom = CDateEdit(ExportTariff_Wizard_1)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.edtFilterBegDateFrom.sizePolicy().hasHeightForWidth())
        self.edtFilterBegDateFrom.setSizePolicy(sizePolicy)
        self.edtFilterBegDateFrom.setMinimumSize(QtCore.QSize(120, 0))
        self.edtFilterBegDateFrom.setObjectName(_fromUtf8("edtFilterBegDateFrom"))
        self._2.addWidget(self.edtFilterBegDateFrom)
        self.label_2 = QtGui.QLabel(ExportTariff_Wizard_1)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self._2.addWidget(self.label_2)
        self.edtFilterBegDateTil = CDateEdit(ExportTariff_Wizard_1)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.edtFilterBegDateTil.sizePolicy().hasHeightForWidth())
        self.edtFilterBegDateTil.setSizePolicy(sizePolicy)
        self.edtFilterBegDateTil.setMinimumSize(QtCore.QSize(120, 0))
        self.edtFilterBegDateTil.setObjectName(_fromUtf8("edtFilterBegDateTil"))
        self._2.addWidget(self.edtFilterBegDateTil)
        self.gridLayout.addLayout(self._2, 2, 0, 1, 3)
        spacerItem = QtGui.QSpacerItem(229, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 10, 0, 1, 1)
        self.btnClearSelection = QtGui.QPushButton(ExportTariff_Wizard_1)
        self.btnClearSelection.setObjectName(_fromUtf8("btnClearSelection"))
        self.gridLayout.addWidget(self.btnClearSelection, 10, 2, 1, 1)
        self.chkExportExternalTariff = QtGui.QCheckBox(ExportTariff_Wizard_1)
        self.chkExportExternalTariff.setObjectName(_fromUtf8("chkExportExternalTariff"))
        self.gridLayout.addWidget(self.chkExportExternalTariff, 8, 0, 1, 1)
        self.tblItems = CInDocTableView(ExportTariff_Wizard_1)
        self.tblItems.setTabKeyNavigation(False)
        self.tblItems.setAlternatingRowColors(True)
        self.tblItems.setObjectName(_fromUtf8("tblItems"))
        self.gridLayout.addWidget(self.tblItems, 7, 0, 1, 3)
        self.chkExportAll = QtGui.QCheckBox(ExportTariff_Wizard_1)
        self.chkExportAll.setObjectName(_fromUtf8("chkExportAll"))
        self.gridLayout.addWidget(self.chkExportAll, 6, 0, 1, 3)
        self.chkExportExternalTariffToZero = QtGui.QCheckBox(ExportTariff_Wizard_1)
        self.chkExportExternalTariffToZero.setObjectName(_fromUtf8("chkExportExternalTariffToZero"))
        self.gridLayout.addWidget(self.chkExportExternalTariffToZero, 9, 0, 1, 1)

        self.retranslateUi(ExportTariff_Wizard_1)
        QtCore.QMetaObject.connectSlotsByName(ExportTariff_Wizard_1)
        ExportTariff_Wizard_1.setTabOrder(self.edtFilterBegDateFrom, self.edtFilterBegDateTil)
        ExportTariff_Wizard_1.setTabOrder(self.edtFilterBegDateTil, self.chkActive)
        ExportTariff_Wizard_1.setTabOrder(self.chkActive, self.chkExportAll)
        ExportTariff_Wizard_1.setTabOrder(self.chkExportAll, self.tblItems)
        ExportTariff_Wizard_1.setTabOrder(self.tblItems, self.chkExportExternalTariff)
        ExportTariff_Wizard_1.setTabOrder(self.chkExportExternalTariff, self.chkExportExternalTariffToZero)
        ExportTariff_Wizard_1.setTabOrder(self.chkExportExternalTariffToZero, self.btnSelectAll)
        ExportTariff_Wizard_1.setTabOrder(self.btnSelectAll, self.btnClearSelection)

    def retranslateUi(self, ExportTariff_Wizard_1):
        ExportTariff_Wizard_1.setWindowTitle(_translate("ExportTariff_Wizard_1", "Выбор экспортируемых тарифов", None))
        self.chkActive.setText(_translate("ExportTariff_Wizard_1", "Действующие на дату", None))
        self.btnSelectAll.setText(_translate("ExportTariff_Wizard_1", "Выбрать все", None))
        self.label.setText(_translate("ExportTariff_Wizard_1", "Дата начала тарифа    с", None))
        self.label_2.setText(_translate("ExportTariff_Wizard_1", "по", None))
        self.btnClearSelection.setText(_translate("ExportTariff_Wizard_1", "Очистить", None))
        self.chkExportExternalTariff.setText(_translate("ExportTariff_Wizard_1", "Экспортировать внешние тарифы", None))
        self.tblItems.setWhatsThis(_translate("ExportTariff_Wizard_1", "список записей", "ура!"))
        self.chkExportAll.setText(_translate("ExportTariff_Wizard_1", "Выгружать всё", None))
        self.chkExportExternalTariffToZero.setText(_translate("ExportTariff_Wizard_1", "Обнулять суммы на внешних тарифах", None))

from library.DateEdit import CDateEdit
from library.InDocTable import CInDocTableView
