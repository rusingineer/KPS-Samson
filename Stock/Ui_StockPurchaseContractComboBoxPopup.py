# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\samson\Stock\StockPurchaseContractComboBoxPopup.ui'
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

class Ui_StockPurchaseContractComboBoxPopup(object):
    def setupUi(self, StockPurchaseContractComboBoxPopup):
        StockPurchaseContractComboBoxPopup.setObjectName(_fromUtf8("StockPurchaseContractComboBoxPopup"))
        StockPurchaseContractComboBoxPopup.resize(567, 186)
        self.gridlayout = QtGui.QGridLayout(StockPurchaseContractComboBoxPopup)
        self.gridlayout.setMargin(0)
        self.gridlayout.setSpacing(0)
        self.gridlayout.setObjectName(_fromUtf8("gridlayout"))
        self.tabWidget = QtGui.QTabWidget(StockPurchaseContractComboBoxPopup)
        self.tabWidget.setTabPosition(QtGui.QTabWidget.South)
        self.tabWidget.setTabShape(QtGui.QTabWidget.Rounded)
        self.tabWidget.setObjectName(_fromUtf8("tabWidget"))
        self.tabContracts = QtGui.QWidget()
        self.tabContracts.setObjectName(_fromUtf8("tabContracts"))
        self.vboxlayout = QtGui.QVBoxLayout(self.tabContracts)
        self.vboxlayout.setMargin(4)
        self.vboxlayout.setSpacing(4)
        self.vboxlayout.setObjectName(_fromUtf8("vboxlayout"))
        self.tblPurchaseContracts = CTableView(self.tabContracts)
        self.tblPurchaseContracts.setObjectName(_fromUtf8("tblPurchaseContracts"))
        self.vboxlayout.addWidget(self.tblPurchaseContracts)
        self.tabWidget.addTab(self.tabContracts, _fromUtf8(""))
        self.tabSearch = QtGui.QWidget()
        self.tabSearch.setObjectName(_fromUtf8("tabSearch"))
        self.gridLayout = QtGui.QGridLayout(self.tabSearch)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.edtNumber = QtGui.QLineEdit(self.tabSearch)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.edtNumber.sizePolicy().hasHeightForWidth())
        self.edtNumber.setSizePolicy(sizePolicy)
        self.edtNumber.setObjectName(_fromUtf8("edtNumber"))
        self.gridLayout.addWidget(self.edtNumber, 0, 1, 1, 4)
        self.buttonBox = QtGui.QDialogButtonBox(self.tabSearch)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.buttonBox.sizePolicy().hasHeightForWidth())
        self.buttonBox.setSizePolicy(sizePolicy)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Apply|QtGui.QDialogButtonBox.Reset)
        self.buttonBox.setCenterButtons(False)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 6, 4, 1, 1)
        self.lblName = QtGui.QLabel(self.tabSearch)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblName.sizePolicy().hasHeightForWidth())
        self.lblName.setSizePolicy(sizePolicy)
        self.lblName.setObjectName(_fromUtf8("lblName"))
        self.gridLayout.addWidget(self.lblName, 2, 0, 1, 1)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 6, 0, 1, 4)
        self.lblNumber = QtGui.QLabel(self.tabSearch)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblNumber.sizePolicy().hasHeightForWidth())
        self.lblNumber.setSizePolicy(sizePolicy)
        self.lblNumber.setObjectName(_fromUtf8("lblNumber"))
        self.gridLayout.addWidget(self.lblNumber, 0, 0, 1, 1)
        spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem1, 5, 0, 1, 5)
        self.edtName = QtGui.QLineEdit(self.tabSearch)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.edtName.sizePolicy().hasHeightForWidth())
        self.edtName.setSizePolicy(sizePolicy)
        self.edtName.setObjectName(_fromUtf8("edtName"))
        self.gridLayout.addWidget(self.edtName, 2, 1, 1, 4)
        self.lblDate = QtGui.QLabel(self.tabSearch)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblDate.sizePolicy().hasHeightForWidth())
        self.lblDate.setSizePolicy(sizePolicy)
        self.lblDate.setObjectName(_fromUtf8("lblDate"))
        self.gridLayout.addWidget(self.lblDate, 1, 0, 1, 1)
        self.edtDate = CDateEdit(self.tabSearch)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.edtDate.sizePolicy().hasHeightForWidth())
        self.edtDate.setSizePolicy(sizePolicy)
        self.edtDate.setCalendarPopup(True)
        self.edtDate.setObjectName(_fromUtf8("edtDate"))
        self.gridLayout.addWidget(self.edtDate, 1, 1, 1, 1)
        spacerItem2 = QtGui.QSpacerItem(325, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem2, 1, 2, 1, 3)
        self.tabWidget.addTab(self.tabSearch, _fromUtf8(""))
        self.gridlayout.addWidget(self.tabWidget, 0, 0, 1, 1)
        self.lblName.setBuddy(self.edtName)
        self.lblNumber.setBuddy(self.edtNumber)
        self.lblDate.setBuddy(self.edtDate)

        self.retranslateUi(StockPurchaseContractComboBoxPopup)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(StockPurchaseContractComboBoxPopup)
        StockPurchaseContractComboBoxPopup.setTabOrder(self.tabWidget, self.tblPurchaseContracts)
        StockPurchaseContractComboBoxPopup.setTabOrder(self.tblPurchaseContracts, self.edtNumber)
        StockPurchaseContractComboBoxPopup.setTabOrder(self.edtNumber, self.edtDate)
        StockPurchaseContractComboBoxPopup.setTabOrder(self.edtDate, self.edtName)
        StockPurchaseContractComboBoxPopup.setTabOrder(self.edtName, self.buttonBox)

    def retranslateUi(self, StockPurchaseContractComboBoxPopup):
        StockPurchaseContractComboBoxPopup.setWindowTitle(_translate("StockPurchaseContractComboBoxPopup", "Form", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabContracts), _translate("StockPurchaseContractComboBoxPopup", "&Договоры", None))
        self.lblName.setText(_translate("StockPurchaseContractComboBoxPopup", "На&именование", None))
        self.lblNumber.setText(_translate("StockPurchaseContractComboBoxPopup", "&Номер", None))
        self.lblDate.setText(_translate("StockPurchaseContractComboBoxPopup", "Д&ата", None))
        self.edtDate.setDisplayFormat(_translate("StockPurchaseContractComboBoxPopup", "dd.MM.yyyy", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabSearch), _translate("StockPurchaseContractComboBoxPopup", "&Поиск", None))

from library.DateEdit import CDateEdit
from library.TableView import CTableView
