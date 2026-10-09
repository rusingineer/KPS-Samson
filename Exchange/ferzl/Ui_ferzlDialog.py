# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'E:\projects\Samson\UP_s11\client\Exchange\ferzl\ferzlDialog.ui'
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

class Ui_ferzlDialog(object):
    def setupUi(self, ferzlDialog):
        ferzlDialog.setObjectName(_fromUtf8("ferzlDialog"))
        ferzlDialog.resize(485, 528)
        self.gridLayout_4 = QtGui.QGridLayout(ferzlDialog)
        self.gridLayout_4.setObjectName(_fromUtf8("gridLayout_4"))
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.label = QtGui.QLabel(ferzlDialog)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.cmbRbDoc = QtGui.QComboBox(ferzlDialog)
        self.cmbRbDoc.setObjectName(_fromUtf8("cmbRbDoc"))
        self.cmbRbDoc.addItem(_fromUtf8(""))
        self.cmbRbDoc.addItem(_fromUtf8(""))
        self.cmbRbDoc.addItem(_fromUtf8(""))
        self.cmbRbDoc.addItem(_fromUtf8(""))
        self.cmbRbDoc.addItem(_fromUtf8(""))
        self.cmbRbDoc.addItem(_fromUtf8(""))
        self.cmbRbDoc.addItem(_fromUtf8(""))
        self.cmbRbDoc.addItem(_fromUtf8(""))
        self.cmbRbDoc.addItem(_fromUtf8(""))
        self.cmbRbDoc.addItem(_fromUtf8(""))
        self.gridLayout.addWidget(self.cmbRbDoc, 0, 1, 1, 1)
        self.label_2 = QtGui.QLabel(ferzlDialog)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)
        self.seria = QtGui.QLineEdit(ferzlDialog)
        self.seria.setObjectName(_fromUtf8("seria"))
        self.gridLayout.addWidget(self.seria, 1, 1, 1, 1)
        self.label_3 = QtGui.QLabel(ferzlDialog)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.gridLayout.addWidget(self.label_3, 2, 0, 1, 1)
        self.number = QtGui.QLineEdit(ferzlDialog)
        self.number.setObjectName(_fromUtf8("number"))
        self.gridLayout.addWidget(self.number, 2, 1, 1, 1)
        self.gridLayout_4.addLayout(self.gridLayout, 0, 0, 1, 1)
        self.gridLayout_2 = QtGui.QGridLayout()
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout_2.addItem(spacerItem, 0, 0, 1, 1)
        self.btnSearch = QtGui.QPushButton(ferzlDialog)
        self.btnSearch.setObjectName(_fromUtf8("btnSearch"))
        self.gridLayout_2.addWidget(self.btnSearch, 0, 1, 1, 1)
        self.gridLayout_4.addLayout(self.gridLayout_2, 1, 0, 1, 1)
        self.tableView = CTableView(ferzlDialog)
        self.tableView.setObjectName(_fromUtf8("tableView"))
        self.gridLayout_4.addWidget(self.tableView, 2, 0, 1, 1)
        self.gridLayout_3 = QtGui.QGridLayout()
        self.gridLayout_3.setObjectName(_fromUtf8("gridLayout_3"))
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout_3.addItem(spacerItem1, 0, 0, 1, 1)
        self.btnAdd = QtGui.QPushButton(ferzlDialog)
        self.btnAdd.setObjectName(_fromUtf8("btnAdd"))
        self.gridLayout_3.addWidget(self.btnAdd, 0, 1, 1, 1)
        self.btnClose = QtGui.QPushButton(ferzlDialog)
        self.btnClose.setObjectName(_fromUtf8("btnClose"))
        self.gridLayout_3.addWidget(self.btnClose, 0, 2, 1, 1)
        self.gridLayout_4.addLayout(self.gridLayout_3, 3, 0, 1, 1)

        self.retranslateUi(ferzlDialog)
        QtCore.QMetaObject.connectSlotsByName(ferzlDialog)

    def retranslateUi(self, ferzlDialog):
        ferzlDialog.setWindowTitle(_translate("ferzlDialog", "ФЕРЗЛ", None))
        self.label.setText(_translate("ferzlDialog", "Тип документа", None))
        self.cmbRbDoc.setItemText(0, _translate("ferzlDialog", "Паспорт РФ", None))
        self.cmbRbDoc.setItemText(1, _translate("ferzlDialog", "Свидетельство о рождении ", None))
        self.cmbRbDoc.setItemText(2, _translate("ferzlDialog", "Полис ОМС старого образца", None))
        self.cmbRbDoc.setItemText(3, _translate("ferzlDialog", "Временное свидетельство в форме бумажного бланка", None))
        self.cmbRbDoc.setItemText(4, _translate("ferzlDialog", "Временное свидетельство в форме электронного", None))
        self.cmbRbDoc.setItemText(5, _translate("ferzlDialog", "Бумажный полис ОМС единого образца", None))
        self.cmbRbDoc.setItemText(6, _translate("ferzlDialog", "Электронный полис ОМС единого образца", None))
        self.cmbRbDoc.setItemText(7, _translate("ferzlDialog", "Полис ОМС в составе универсальной электронной карты", None))
        self.cmbRbDoc.setItemText(8, _translate("ferzlDialog", "Цифровой полис ОМС", None))
        self.cmbRbDoc.setItemText(9, _translate("ferzlDialog", "ЕНП", None))
        self.label_2.setText(_translate("ferzlDialog", "Серия", None))
        self.label_3.setText(_translate("ferzlDialog", "Номер ", None))
        self.btnSearch.setText(_translate("ferzlDialog", "Искать", None))
        self.btnAdd.setText(_translate("ferzlDialog", "Добавить пациента", None))
        self.btnClose.setText(_translate("ferzlDialog", "Отмена", None))

from library.TableView import CTableView
