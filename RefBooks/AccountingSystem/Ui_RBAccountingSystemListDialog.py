# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\Samson\UP_s11\client_test\RefBooks\AccountingSystem\RBAccountingSystemListDialog.ui'
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

class Ui_RBAccountingSystemListDialog(object):
    def setupUi(self, RBAccountingSystemListDialog):
        RBAccountingSystemListDialog.setObjectName(_fromUtf8("RBAccountingSystemListDialog"))
        RBAccountingSystemListDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        RBAccountingSystemListDialog.resize(689, 450)
        RBAccountingSystemListDialog.setSizeGripEnabled(True)
        RBAccountingSystemListDialog.setModal(True)
        self.gridLayout = QtGui.QGridLayout(RBAccountingSystemListDialog)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.edtUrnFilter = QtGui.QLineEdit(RBAccountingSystemListDialog)
        self.edtUrnFilter.setObjectName(_fromUtf8("edtUrnFilter"))
        self.gridLayout.addWidget(self.edtUrnFilter, 0, 3, 1, 1)
        self.lblNameFilter = QtGui.QLabel(RBAccountingSystemListDialog)
        self.lblNameFilter.setObjectName(_fromUtf8("lblNameFilter"))
        self.gridLayout.addWidget(self.lblNameFilter, 0, 4, 1, 1)
        self.edtNameFilter = QtGui.QLineEdit(RBAccountingSystemListDialog)
        self.edtNameFilter.setObjectName(_fromUtf8("edtNameFilter"))
        self.gridLayout.addWidget(self.edtNameFilter, 0, 5, 1, 1)
        self.lblUrnFilter = QtGui.QLabel(RBAccountingSystemListDialog)
        self.lblUrnFilter.setObjectName(_fromUtf8("lblUrnFilter"))
        self.gridLayout.addWidget(self.lblUrnFilter, 0, 2, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(RBAccountingSystemListDialog)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 2, 4, 1, 3)
        self.edtCodeFilter = QtGui.QLineEdit(RBAccountingSystemListDialog)
        self.edtCodeFilter.setObjectName(_fromUtf8("edtCodeFilter"))
        self.gridLayout.addWidget(self.edtCodeFilter, 0, 1, 1, 1)
        self.tblItems = CSortFilterProxyTableView(RBAccountingSystemListDialog)
        self.tblItems.setTabKeyNavigation(False)
        self.tblItems.setAlternatingRowColors(True)
        self.tblItems.setObjectName(_fromUtf8("tblItems"))
        self.gridLayout.addWidget(self.tblItems, 1, 0, 1, 7)
        self.lblCodeFilter = QtGui.QLabel(RBAccountingSystemListDialog)
        self.lblCodeFilter.setObjectName(_fromUtf8("lblCodeFilter"))
        self.gridLayout.addWidget(self.lblCodeFilter, 0, 0, 1, 1)
        self.statusBar = QtGui.QStatusBar(RBAccountingSystemListDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.statusBar.sizePolicy().hasHeightForWidth())
        self.statusBar.setSizePolicy(sizePolicy)
        self.statusBar.setSizeGripEnabled(False)
        self.statusBar.setObjectName(_fromUtf8("statusBar"))
        self.gridLayout.addWidget(self.statusBar, 3, 0, 1, 4)
        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setMargin(0)
        self.hboxlayout.setSpacing(6)
        self.hboxlayout.setObjectName(_fromUtf8("hboxlayout"))
        self.label = QtGui.QLabel(RBAccountingSystemListDialog)
        self.label.setObjectName(_fromUtf8("label"))
        self.hboxlayout.addWidget(self.label)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.hboxlayout.addItem(spacerItem)
        self.gridLayout.addLayout(self.hboxlayout, 2, 0, 1, 4)

        self.retranslateUi(RBAccountingSystemListDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), RBAccountingSystemListDialog.close)
        QtCore.QMetaObject.connectSlotsByName(RBAccountingSystemListDialog)
        RBAccountingSystemListDialog.setTabOrder(self.tblItems, self.edtUrnFilter)
        RBAccountingSystemListDialog.setTabOrder(self.edtUrnFilter, self.edtNameFilter)
        RBAccountingSystemListDialog.setTabOrder(self.edtNameFilter, self.buttonBox)

    def retranslateUi(self, RBAccountingSystemListDialog):
        RBAccountingSystemListDialog.setWindowTitle(_translate("RBAccountingSystemListDialog", "Список записей", None))
        self.lblNameFilter.setText(_translate("RBAccountingSystemListDialog", "Наименование", None))
        self.lblUrnFilter.setText(_translate("RBAccountingSystemListDialog", "urn", None))
        self.tblItems.setWhatsThis(_translate("RBAccountingSystemListDialog", "список записей", "ура!"))
        self.lblCodeFilter.setText(_translate("RBAccountingSystemListDialog", "Код", None))
        self.statusBar.setToolTip(_translate("RBAccountingSystemListDialog", "A status bar", None))
        self.statusBar.setWhatsThis(_translate("RBAccountingSystemListDialog", "A status bar.", None))
        self.label.setText(_translate("RBAccountingSystemListDialog", "всего: ", None))

from library.SortFilterProxyTableView import CSortFilterProxyTableView
