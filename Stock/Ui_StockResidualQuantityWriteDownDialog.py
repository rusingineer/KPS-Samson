# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\samson\Stock\StockResidualQuantityWriteDownDialog.ui'
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

class Ui_StockResidualQuantityWriteDownDialog(object):
    def setupUi(self, StockResidualQuantityWriteDownDialog):
        StockResidualQuantityWriteDownDialog.setObjectName(_fromUtf8("StockResidualQuantityWriteDownDialog"))
        StockResidualQuantityWriteDownDialog.resize(685, 457)
        self.gridLayout = QtGui.QGridLayout(StockResidualQuantityWriteDownDialog)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.lblSupplier = QtGui.QLabel(StockResidualQuantityWriteDownDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblSupplier.sizePolicy().hasHeightForWidth())
        self.lblSupplier.setSizePolicy(sizePolicy)
        self.lblSupplier.setObjectName(_fromUtf8("lblSupplier"))
        self.gridLayout.addWidget(self.lblSupplier, 2, 0, 1, 1)
        self.lblNote = QtGui.QLabel(StockResidualQuantityWriteDownDialog)
        self.lblNote.setObjectName(_fromUtf8("lblNote"))
        self.gridLayout.addWidget(self.lblNote, 4, 0, 1, 1)
        self.edtNumber = QtGui.QLineEdit(StockResidualQuantityWriteDownDialog)
        self.edtNumber.setObjectName(_fromUtf8("edtNumber"))
        self.gridLayout.addWidget(self.edtNumber, 0, 1, 1, 1)
        self.lblNumber = QtGui.QLabel(StockResidualQuantityWriteDownDialog)
        self.lblNumber.setObjectName(_fromUtf8("lblNumber"))
        self.gridLayout.addWidget(self.lblNumber, 0, 0, 1, 1)
        self.cmbSupplier = CStorageComboBox(StockResidualQuantityWriteDownDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cmbSupplier.sizePolicy().hasHeightForWidth())
        self.cmbSupplier.setSizePolicy(sizePolicy)
        self.cmbSupplier.setObjectName(_fromUtf8("cmbSupplier"))
        self.gridLayout.addWidget(self.cmbSupplier, 2, 1, 1, 1)
        self.lblSupplierPerson = QtGui.QLabel(StockResidualQuantityWriteDownDialog)
        self.lblSupplierPerson.setObjectName(_fromUtf8("lblSupplierPerson"))
        self.gridLayout.addWidget(self.lblSupplierPerson, 3, 0, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(StockResidualQuantityWriteDownDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 6, 0, 1, 2)
        self.lblDate = QtGui.QLabel(StockResidualQuantityWriteDownDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblDate.sizePolicy().hasHeightForWidth())
        self.lblDate.setSizePolicy(sizePolicy)
        self.lblDate.setObjectName(_fromUtf8("lblDate"))
        self.gridLayout.addWidget(self.lblDate, 1, 0, 1, 1)
        self.edtNote = QtGui.QLineEdit(StockResidualQuantityWriteDownDialog)
        self.edtNote.setObjectName(_fromUtf8("edtNote"))
        self.gridLayout.addWidget(self.edtNote, 4, 1, 1, 1)
        self.cmbSupplierPerson = CPersonComboBoxEx(StockResidualQuantityWriteDownDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cmbSupplierPerson.sizePolicy().hasHeightForWidth())
        self.cmbSupplierPerson.setSizePolicy(sizePolicy)
        self.cmbSupplierPerson.setObjectName(_fromUtf8("cmbSupplierPerson"))
        self.gridLayout.addWidget(self.cmbSupplierPerson, 3, 1, 1, 1)
        self.tabWidget = QtGui.QTabWidget(StockResidualQuantityWriteDownDialog)
        self.tabWidget.setObjectName(_fromUtf8("tabWidget"))
        self.tab = QtGui.QWidget()
        self.tab.setObjectName(_fromUtf8("tab"))
        self.verticalLayout = QtGui.QVBoxLayout(self.tab)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.tblItems = CInDocTableView(self.tab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tblItems.sizePolicy().hasHeightForWidth())
        self.tblItems.setSizePolicy(sizePolicy)
        self.tblItems.setObjectName(_fromUtf8("tblItems"))
        self.verticalLayout.addWidget(self.tblItems)
        self.lblSummaryInfo = QtGui.QLabel(self.tab)
        self.lblSummaryInfo.setText(_fromUtf8(""))
        self.lblSummaryInfo.setObjectName(_fromUtf8("lblSummaryInfo"))
        self.verticalLayout.addWidget(self.lblSummaryInfo)
        self.tabWidget.addTab(self.tab, _fromUtf8(""))
        self.gridLayout.addWidget(self.tabWidget, 5, 0, 1, 2)
        self.widget = QtGui.QWidget(StockResidualQuantityWriteDownDialog)
        self.widget.setObjectName(_fromUtf8("widget"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.widget)
        self.horizontalLayout.setMargin(0)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.edtDate = CDateEdit(self.widget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.edtDate.sizePolicy().hasHeightForWidth())
        self.edtDate.setSizePolicy(sizePolicy)
        self.edtDate.setObjectName(_fromUtf8("edtDate"))
        self.horizontalLayout.addWidget(self.edtDate)
        self.edtTime = QtGui.QTimeEdit(self.widget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.edtTime.sizePolicy().hasHeightForWidth())
        self.edtTime.setSizePolicy(sizePolicy)
        self.edtTime.setObjectName(_fromUtf8("edtTime"))
        self.horizontalLayout.addWidget(self.edtTime)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.gridLayout.addWidget(self.widget, 1, 1, 1, 1)
        self.lblSupplier.setBuddy(self.cmbSupplier)
        self.lblNote.setBuddy(self.edtNote)
        self.lblSupplierPerson.setBuddy(self.cmbSupplierPerson)
        self.lblDate.setBuddy(self.edtDate)

        self.retranslateUi(StockResidualQuantityWriteDownDialog)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), StockResidualQuantityWriteDownDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), StockResidualQuantityWriteDownDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(StockResidualQuantityWriteDownDialog)
        StockResidualQuantityWriteDownDialog.setTabOrder(self.edtNumber, self.edtDate)
        StockResidualQuantityWriteDownDialog.setTabOrder(self.edtDate, self.edtTime)
        StockResidualQuantityWriteDownDialog.setTabOrder(self.edtTime, self.cmbSupplier)
        StockResidualQuantityWriteDownDialog.setTabOrder(self.cmbSupplier, self.cmbSupplierPerson)
        StockResidualQuantityWriteDownDialog.setTabOrder(self.cmbSupplierPerson, self.edtNote)
        StockResidualQuantityWriteDownDialog.setTabOrder(self.edtNote, self.buttonBox)

    def retranslateUi(self, StockResidualQuantityWriteDownDialog):
        StockResidualQuantityWriteDownDialog.setWindowTitle(_translate("StockResidualQuantityWriteDownDialog", "Dialog", None))
        self.lblSupplier.setText(_translate("StockResidualQuantityWriteDownDialog", "Подразделение", None))
        self.lblNote.setText(_translate("StockResidualQuantityWriteDownDialog", "Примечания", None))
        self.lblNumber.setText(_translate("StockResidualQuantityWriteDownDialog", "Номер", None))
        self.lblSupplierPerson.setText(_translate("StockResidualQuantityWriteDownDialog", "Ответственный", None))
        self.lblDate.setText(_translate("StockResidualQuantityWriteDownDialog", "Дата", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("StockResidualQuantityWriteDownDialog", "ЛСиИМН", None))
        self.edtTime.setDisplayFormat(_translate("StockResidualQuantityWriteDownDialog", "HH:mm", None))

from Orgs.OrgStructComboBoxes import CStorageComboBox
from Orgs.PersonComboBoxEx import CPersonComboBoxEx
from library.DateEdit import CDateEdit
from library.InDocTable import CInDocTableView
