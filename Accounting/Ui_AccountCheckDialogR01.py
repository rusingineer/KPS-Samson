# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\Samson\UP_s11\client_01\Accounting\AccountCheckDialogR01.ui'
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

class Ui_AccountCheckDialog(object):
    def setupUi(self, AccountCheckDialog):
        AccountCheckDialog.setObjectName(_fromUtf8("AccountCheckDialog"))
        AccountCheckDialog.setWindowModality(QtCore.Qt.WindowModal)
        AccountCheckDialog.resize(880, 631)
        self.gridLayout_4 = QtGui.QGridLayout(AccountCheckDialog)
        self.gridLayout_4.setMargin(4)
        self.gridLayout_4.setSpacing(4)
        self.gridLayout_4.setObjectName(_fromUtf8("gridLayout_4"))
        self.groupBox = QtGui.QGroupBox(AccountCheckDialog)
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.gridLayout = QtGui.QGridLayout(self.groupBox)
        self.gridLayout.setMargin(9)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.gridLayout_5 = QtGui.QGridLayout()
        self.gridLayout_5.setMargin(9)
        self.gridLayout_5.setSpacing(6)
        self.gridLayout_5.setObjectName(_fromUtf8("gridLayout_5"))
        self.chkSelectAllCheckTypes = QtGui.QCheckBox(self.groupBox)
        self.chkSelectAllCheckTypes.setChecked(True)
        self.chkSelectAllCheckTypes.setTristate(True)
        self.chkSelectAllCheckTypes.setObjectName(_fromUtf8("chkSelectAllCheckTypes"))
        self.gridLayout_5.addWidget(self.chkSelectAllCheckTypes, 0, 0, 1, 1)
        self.chkNotIsDone = QtGui.QCheckBox(self.groupBox)
        self.chkNotIsDone.setChecked(True)
        self.chkNotIsDone.setObjectName(_fromUtf8("chkNotIsDone"))
        self.gridLayout_5.addWidget(self.chkNotIsDone, 0, 1, 1, 1)
        self.cmbEventType = CRBComboBox(self.groupBox)
        self.cmbEventType.setObjectName(_fromUtf8("cmbEventType"))
        self.gridLayout_5.addWidget(self.cmbEventType, 0, 3, 1, 1)
        self.btnApply = QtGui.QPushButton(self.groupBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnApply.sizePolicy().hasHeightForWidth())
        self.btnApply.setSizePolicy(sizePolicy)
        self.btnApply.setObjectName(_fromUtf8("btnApply"))
        self.gridLayout_5.addWidget(self.btnApply, 0, 4, 1, 1)
        self.lblEventType = QtGui.QLabel(self.groupBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblEventType.sizePolicy().hasHeightForWidth())
        self.lblEventType.setSizePolicy(sizePolicy)
        self.lblEventType.setObjectName(_fromUtf8("lblEventType"))
        self.gridLayout_5.addWidget(self.lblEventType, 0, 2, 1, 1)
        self.btnPrintByOrgStructure = QtGui.QPushButton(self.groupBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnPrintByOrgStructure.sizePolicy().hasHeightForWidth())
        self.btnPrintByOrgStructure.setSizePolicy(sizePolicy)
        self.btnPrintByOrgStructure.setObjectName(_fromUtf8("btnPrintByOrgStructure"))
        self.gridLayout_5.addWidget(self.btnPrintByOrgStructure, 1, 4, 1, 1)
        self.cmbOrgStructure = COrgStructureComboBox(self.groupBox)
        self.cmbOrgStructure.setObjectName(_fromUtf8("cmbOrgStructure"))
        self.gridLayout_5.addWidget(self.cmbOrgStructure, 1, 3, 1, 1)
        self.gridLayout.addLayout(self.gridLayout_5, 0, 0, 1, 1)
        self.listCheckTypes = QtGui.QListWidget(self.groupBox)
        self.listCheckTypes.setObjectName(_fromUtf8("listCheckTypes"))
        self.gridLayout.addWidget(self.listCheckTypes, 1, 0, 1, 1)
        self.gridLayout_4.addWidget(self.groupBox, 0, 0, 1, 1)
        self.groupBox_3 = QtGui.QGroupBox(AccountCheckDialog)
        self.groupBox_3.setObjectName(_fromUtf8("groupBox_3"))
        self.gridLayout_2 = QtGui.QGridLayout(self.groupBox_3)
        self.gridLayout_2.setMargin(4)
        self.gridLayout_2.setHorizontalSpacing(4)
        self.gridLayout_2.setVerticalSpacing(3)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.tblFLC = CTableView(self.groupBox_3)
        self.tblFLC.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.tblFLC.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tblFLC.setSelectionBehavior(QtGui.QAbstractItemView.SelectItems)
        self.tblFLC.setObjectName(_fromUtf8("tblFLC"))
        self.gridLayout_2.addWidget(self.tblFLC, 0, 0, 1, 1)
        self.gridLayout_4.addWidget(self.groupBox_3, 1, 0, 1, 1)
        self.groupBox_4 = QtGui.QGroupBox(AccountCheckDialog)
        self.groupBox_4.setObjectName(_fromUtf8("groupBox_4"))
        self.gridLayout_3 = QtGui.QGridLayout(self.groupBox_4)
        self.gridLayout_3.setMargin(4)
        self.gridLayout_3.setSpacing(4)
        self.gridLayout_3.setObjectName(_fromUtf8("gridLayout_3"))
        self.textErrorDescription = QtGui.QTextEdit(self.groupBox_4)
        self.textErrorDescription.setAcceptRichText(False)
        self.textErrorDescription.setTextInteractionFlags(QtCore.Qt.TextSelectableByKeyboard|QtCore.Qt.TextSelectableByMouse)
        self.textErrorDescription.setObjectName(_fromUtf8("textErrorDescription"))
        self.gridLayout_3.addWidget(self.textErrorDescription, 0, 0, 1, 1)
        self.gridLayout_4.addWidget(self.groupBox_4, 2, 0, 1, 1)
        self.gridLayout_4.setRowStretch(0, 2)
        self.gridLayout_4.setRowStretch(1, 2)
        self.gridLayout_4.setRowStretch(2, 1)

        self.retranslateUi(AccountCheckDialog)
        QtCore.QMetaObject.connectSlotsByName(AccountCheckDialog)

    def retranslateUi(self, AccountCheckDialog):
        AccountCheckDialog.setWindowTitle(_translate("AccountCheckDialog", "Проверка счетов", None))
        self.groupBox.setTitle(_translate("AccountCheckDialog", "Типы ошибок ФЛК", None))
        self.chkSelectAllCheckTypes.setText(_translate("AccountCheckDialog", "Выбрать все", None))
        self.chkNotIsDone.setText(_translate("AccountCheckDialog", "Только не отработанные", None))
        self.btnApply.setText(_translate("AccountCheckDialog", "Применить", None))
        self.lblEventType.setText(_translate("AccountCheckDialog", "Тип события", None))
        self.btnPrintByOrgStructure.setText(_translate("AccountCheckDialog", "По отделениям", None))
        self.groupBox_3.setTitle(_translate("AccountCheckDialog", "Список ошибок ФЛК реестров счетов", None))
        self.groupBox_4.setTitle(_translate("AccountCheckDialog", "Все ошибки случая лечения", None))

from Orgs.OrgStructComboBoxes import COrgStructureComboBox
from library.TableView import CTableView
from library.crbcombobox import CRBComboBox
