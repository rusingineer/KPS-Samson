# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\samson\Stock\StockBatchListEditor.ui'
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

class Ui_StockBatchListEditor(object):
    def setupUi(self, StockBatchListEditor):
        StockBatchListEditor.setObjectName(_fromUtf8("StockBatchListEditor"))
        StockBatchListEditor.resize(558, 389)
        self.gridLayout = QtGui.QGridLayout(StockBatchListEditor)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.lblBatch = QtGui.QLabel(StockBatchListEditor)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblBatch.sizePolicy().hasHeightForWidth())
        self.lblBatch.setSizePolicy(sizePolicy)
        self.lblBatch.setObjectName(_fromUtf8("lblBatch"))
        self.gridLayout.addWidget(self.lblBatch, 0, 0, 1, 1)
        self.edtBatch = QtGui.QLineEdit(StockBatchListEditor)
        self.edtBatch.setObjectName(_fromUtf8("edtBatch"))
        self.gridLayout.addWidget(self.edtBatch, 0, 1, 1, 2)
        self.lblShelfTime = QtGui.QLabel(StockBatchListEditor)
        self.lblShelfTime.setObjectName(_fromUtf8("lblShelfTime"))
        self.gridLayout.addWidget(self.lblShelfTime, 1, 0, 1, 1)
        self.edtShelfTime = CDateEdit(StockBatchListEditor)
        self.edtShelfTime.setCalendarPopup(True)
        self.edtShelfTime.setObjectName(_fromUtf8("edtShelfTime"))
        self.gridLayout.addWidget(self.edtShelfTime, 1, 1, 1, 1)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 1, 2, 1, 1)
        self.lblFinance = QtGui.QLabel(StockBatchListEditor)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblFinance.sizePolicy().hasHeightForWidth())
        self.lblFinance.setSizePolicy(sizePolicy)
        self.lblFinance.setObjectName(_fromUtf8("lblFinance"))
        self.gridLayout.addWidget(self.lblFinance, 2, 0, 1, 1)
        self.cmbFinance = CRBComboBox(StockBatchListEditor)
        self.cmbFinance.setObjectName(_fromUtf8("cmbFinance"))
        self.gridLayout.addWidget(self.cmbFinance, 2, 1, 1, 2)
        self.lblMedicalAidKind = QtGui.QLabel(StockBatchListEditor)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblMedicalAidKind.sizePolicy().hasHeightForWidth())
        self.lblMedicalAidKind.setSizePolicy(sizePolicy)
        self.lblMedicalAidKind.setObjectName(_fromUtf8("lblMedicalAidKind"))
        self.gridLayout.addWidget(self.lblMedicalAidKind, 3, 0, 1, 1)
        self.cmbMedicalAidKind = CRBComboBox(StockBatchListEditor)
        self.cmbMedicalAidKind.setObjectName(_fromUtf8("cmbMedicalAidKind"))
        self.gridLayout.addWidget(self.cmbMedicalAidKind, 3, 1, 1, 2)
        self.chkDetailBySGTIN = QtGui.QCheckBox(StockBatchListEditor)
        self.chkDetailBySGTIN.setEnabled(False)
        self.chkDetailBySGTIN.setObjectName(_fromUtf8("chkDetailBySGTIN"))
        self.gridLayout.addWidget(self.chkDetailBySGTIN, 4, 1, 1, 2)
        self.buttonBoxFilter = QtGui.QDialogButtonBox(StockBatchListEditor)
        self.buttonBoxFilter.setStandardButtons(QtGui.QDialogButtonBox.Apply|QtGui.QDialogButtonBox.Reset)
        self.buttonBoxFilter.setObjectName(_fromUtf8("buttonBoxFilter"))
        self.gridLayout.addWidget(self.buttonBoxFilter, 5, 0, 1, 3)
        self.splitter = QtGui.QSplitter(StockBatchListEditor)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName(_fromUtf8("splitter"))
        self.tblStockBatchList = CStockBatchView(self.splitter)
        self.tblStockBatchList.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tblStockBatchList.setObjectName(_fromUtf8("tblStockBatchList"))
        self.tblStockSGTINCodes = CTableView(self.splitter)
        self.tblStockSGTINCodes.setObjectName(_fromUtf8("tblStockSGTINCodes"))
        self.gridLayout.addWidget(self.splitter, 6, 0, 1, 3)
        self.buttonBox = QtGui.QDialogButtonBox(StockBatchListEditor)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 7, 0, 1, 3)
        self.lblBatch.setBuddy(self.edtBatch)

        self.retranslateUi(StockBatchListEditor)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), StockBatchListEditor.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), StockBatchListEditor.reject)
        QtCore.QMetaObject.connectSlotsByName(StockBatchListEditor)
        StockBatchListEditor.setTabOrder(self.edtBatch, self.edtShelfTime)
        StockBatchListEditor.setTabOrder(self.edtShelfTime, self.cmbFinance)
        StockBatchListEditor.setTabOrder(self.cmbFinance, self.cmbMedicalAidKind)
        StockBatchListEditor.setTabOrder(self.cmbMedicalAidKind, self.chkDetailBySGTIN)
        StockBatchListEditor.setTabOrder(self.chkDetailBySGTIN, self.buttonBoxFilter)
        StockBatchListEditor.setTabOrder(self.buttonBoxFilter, self.tblStockBatchList)
        StockBatchListEditor.setTabOrder(self.tblStockBatchList, self.buttonBox)

    def retranslateUi(self, StockBatchListEditor):
        StockBatchListEditor.setWindowTitle(_translate("StockBatchListEditor", "Dialog", None))
        self.lblBatch.setText(_translate("StockBatchListEditor", "Серия", None))
        self.lblShelfTime.setText(_translate("StockBatchListEditor", "Срок годности", None))
        self.edtShelfTime.setDisplayFormat(_translate("StockBatchListEditor", "dd.MM.yyyy", None))
        self.lblFinance.setText(_translate("StockBatchListEditor", "Тип финансирования", None))
        self.lblMedicalAidKind.setText(_translate("StockBatchListEditor", "Вид мед. помощи", None))
        self.chkDetailBySGTIN.setText(_translate("StockBatchListEditor", "Детализировать по коду вторичной упаковки", None))

from Stock.StockBatchView import CStockBatchView
from library.DateEdit import CDateEdit
from library.TableView import CTableView
from library.crbcombobox import CRBComboBox
