# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\Project\Samson\UP_s11\client_test\library\CSG\CSGComboBoxPopup.ui'
#
# Created: Thu Feb 12 12:22:00 2026
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

class Ui_CSGComboBoxPopup(object):
    def setupUi(self, CSGComboBoxPopup):
        CSGComboBoxPopup.setObjectName(_fromUtf8("CSGComboBoxPopup"))
        CSGComboBoxPopup.resize(545, 247)
        self.gridlayout = QtGui.QGridLayout(CSGComboBoxPopup)
        self.gridlayout.setMargin(0)
        self.gridlayout.setSpacing(0)
        self.gridlayout.setObjectName(_fromUtf8("gridlayout"))
        self.tabWidget = QtGui.QTabWidget(CSGComboBoxPopup)
        self.tabWidget.setTabPosition(QtGui.QTabWidget.South)
        self.tabWidget.setTabShape(QtGui.QTabWidget.Rounded)
        self.tabWidget.setObjectName(_fromUtf8("tabWidget"))
        self.tabCSG = QtGui.QWidget()
        self.tabCSG.setObjectName(_fromUtf8("tabCSG"))
        self.vboxlayout = QtGui.QVBoxLayout(self.tabCSG)
        self.vboxlayout.setSpacing(4)
        self.vboxlayout.setMargin(4)
        self.vboxlayout.setObjectName(_fromUtf8("vboxlayout"))
        self.tblCSG = CTableView(self.tabCSG)
        self.tblCSG.setObjectName(_fromUtf8("tblCSG"))
        self.vboxlayout.addWidget(self.tblCSG)
        self.chkContractTariff = QtGui.QCheckBox(self.tabCSG)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.chkContractTariff.sizePolicy().hasHeightForWidth())
        self.chkContractTariff.setSizePolicy(sizePolicy)
        self.chkContractTariff.setChecked(True)
        self.chkContractTariff.setObjectName(_fromUtf8("chkContractTariff"))
        self.vboxlayout.addWidget(self.chkContractTariff)
        self.tabWidget.addTab(self.tabCSG, _fromUtf8(""))
        self.gridlayout.addWidget(self.tabWidget, 0, 0, 1, 1)

        self.retranslateUi(CSGComboBoxPopup)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(CSGComboBoxPopup)

    def retranslateUi(self, CSGComboBoxPopup):
        CSGComboBoxPopup.setWindowTitle(_translate("CSGComboBoxPopup", "Form", None))
        self.chkContractTariff.setText(_translate("CSGComboBoxPopup", "Учитывать наличие в договоре", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabCSG), _translate("CSGComboBoxPopup", "&Номенклатура", None))

from library.TableView import CTableView
