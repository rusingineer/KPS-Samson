# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\projects\samson\UP_s11\client_pre_release\RefBooks\ContingentKindRemoval\RBContingentKindRemovalEditor.ui'
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

class Ui_ItemEditorDialog(object):
    def setupUi(self, ItemEditorDialog):
        ItemEditorDialog.setObjectName(_fromUtf8("ItemEditorDialog"))
        ItemEditorDialog.resize(400, 317)
        ItemEditorDialog.setSizeGripEnabled(True)
        self.verticalLayout = QtGui.QVBoxLayout(ItemEditorDialog)
        self.verticalLayout.setMargin(4)
        self.verticalLayout.setSpacing(4)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.tabWidget = QtGui.QTabWidget(ItemEditorDialog)
        self.tabWidget.setObjectName(_fromUtf8("tabWidget"))
        self.tabMain = QtGui.QWidget()
        self.tabMain.setObjectName(_fromUtf8("tabMain"))
        self.gridLayout_2 = QtGui.QGridLayout(self.tabMain)
        self.gridLayout_2.setMargin(4)
        self.gridLayout_2.setSpacing(4)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.edtBegDate = CDateEdit(self.tabMain)
        self.edtBegDate.setCalendarPopup(True)
        self.edtBegDate.setObjectName(_fromUtf8("edtBegDate"))
        self.gridLayout_2.addWidget(self.edtBegDate, 3, 1, 1, 1)
        self.lblCode = QtGui.QLabel(self.tabMain)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblCode.sizePolicy().hasHeightForWidth())
        self.lblCode.setSizePolicy(sizePolicy)
        self.lblCode.setObjectName(_fromUtf8("lblCode"))
        self.gridLayout_2.addWidget(self.lblCode, 0, 0, 1, 1)
        self.lblBegDate = QtGui.QLabel(self.tabMain)
        self.lblBegDate.setObjectName(_fromUtf8("lblBegDate"))
        self.gridLayout_2.addWidget(self.lblBegDate, 3, 0, 1, 1)
        self.lblName = QtGui.QLabel(self.tabMain)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblName.sizePolicy().hasHeightForWidth())
        self.lblName.setSizePolicy(sizePolicy)
        self.lblName.setObjectName(_fromUtf8("lblName"))
        self.gridLayout_2.addWidget(self.lblName, 1, 0, 1, 1)
        self.lblContingent = QtGui.QLabel(self.tabMain)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblContingent.sizePolicy().hasHeightForWidth())
        self.lblContingent.setSizePolicy(sizePolicy)
        self.lblContingent.setObjectName(_fromUtf8("lblContingent"))
        self.gridLayout_2.addWidget(self.lblContingent, 2, 0, 1, 1)
        spacerItem = QtGui.QSpacerItem(307, 63, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout_2.addItem(spacerItem, 5, 0, 1, 2)
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout_2.addItem(spacerItem1, 3, 2, 1, 1)
        self.edtName = QtGui.QLineEdit(self.tabMain)
        self.edtName.setObjectName(_fromUtf8("edtName"))
        self.gridLayout_2.addWidget(self.edtName, 1, 1, 1, 2)
        self.edtCode = QtGui.QLineEdit(self.tabMain)
        self.edtCode.setObjectName(_fromUtf8("edtCode"))
        self.gridLayout_2.addWidget(self.edtCode, 0, 1, 1, 2)
        self.cmbContingent = CRBComboBox(self.tabMain)
        self.cmbContingent.setObjectName(_fromUtf8("cmbContingent"))
        self.gridLayout_2.addWidget(self.cmbContingent, 2, 1, 1, 2)
        self.lblEndDate = QtGui.QLabel(self.tabMain)
        self.lblEndDate.setObjectName(_fromUtf8("lblEndDate"))
        self.gridLayout_2.addWidget(self.lblEndDate, 4, 0, 1, 1)
        self.edtEndDate = CDateEdit(self.tabMain)
        self.edtEndDate.setCalendarPopup(True)
        self.edtEndDate.setObjectName(_fromUtf8("edtEndDate"))
        self.gridLayout_2.addWidget(self.edtEndDate, 4, 1, 1, 1)
        spacerItem2 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout_2.addItem(spacerItem2, 4, 2, 1, 1)
        self.tabWidget.addTab(self.tabMain, _fromUtf8(""))
        self.tabIdentification = QtGui.QWidget()
        self.tabIdentification.setObjectName(_fromUtf8("tabIdentification"))
        self.gridLayout = QtGui.QGridLayout(self.tabIdentification)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.tblIdentification = CInDocTableView(self.tabIdentification)
        self.tblIdentification.setObjectName(_fromUtf8("tblIdentification"))
        self.gridLayout.addWidget(self.tblIdentification, 0, 0, 1, 1)
        self.tabWidget.addTab(self.tabIdentification, _fromUtf8(""))
        self.verticalLayout.addWidget(self.tabWidget)
        self.buttonBox = QtGui.QDialogButtonBox(ItemEditorDialog)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)
        self.lblCode.setBuddy(self.edtCode)
        self.lblName.setBuddy(self.edtName)
        self.lblContingent.setBuddy(self.cmbContingent)

        self.retranslateUi(ItemEditorDialog)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), ItemEditorDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), ItemEditorDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(ItemEditorDialog)
        ItemEditorDialog.setTabOrder(self.tabWidget, self.edtCode)
        ItemEditorDialog.setTabOrder(self.edtCode, self.edtName)
        ItemEditorDialog.setTabOrder(self.edtName, self.cmbContingent)
        ItemEditorDialog.setTabOrder(self.cmbContingent, self.edtBegDate)
        ItemEditorDialog.setTabOrder(self.edtBegDate, self.tblIdentification)
        ItemEditorDialog.setTabOrder(self.tblIdentification, self.buttonBox)

    def retranslateUi(self, ItemEditorDialog):
        ItemEditorDialog.setWindowTitle(_translate("ItemEditorDialog", "Редактор", None))
        self.edtBegDate.setDisplayFormat(_translate("ItemEditorDialog", "dd.MM.yyyy", None))
        self.lblCode.setText(_translate("ItemEditorDialog", "&Код", None))
        self.lblBegDate.setText(_translate("ItemEditorDialog", "Дата начала", None))
        self.lblName.setText(_translate("ItemEditorDialog", "&Наименование", None))
        self.lblContingent.setText(_translate("ItemEditorDialog", "Вид контингента", None))
        self.lblEndDate.setText(_translate("ItemEditorDialog", "Дата окончания", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabMain), _translate("ItemEditorDialog", "&Основная информация", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabIdentification), _translate("ItemEditorDialog", "&Идентификация", None))

from library.DateEdit import CDateEdit
from library.InDocTable import CInDocTableView
from library.crbcombobox import CRBComboBox
