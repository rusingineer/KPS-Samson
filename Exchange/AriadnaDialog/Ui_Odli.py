# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\projects\Samson\UP_s11\client_test\Exchange\AriadnaDialog\Odli.ui'
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

class Ui_DialogOdli(object):
    def setupUi(self, DialogOdli):
        DialogOdli.setObjectName(_fromUtf8("DialogOdli"))
        DialogOdli.resize(1090, 852)
        self.verticalLayout = QtGui.QVBoxLayout(DialogOdli)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.groupBox = QtGui.QGroupBox(DialogOdli)
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.gridLayout_4 = QtGui.QGridLayout(self.groupBox)
        self.gridLayout_4.setObjectName(_fromUtf8("gridLayout_4"))
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.lblEndDate = QtGui.QLabel(self.groupBox)
        self.lblEndDate.setObjectName(_fromUtf8("lblEndDate"))
        self.gridLayout.addWidget(self.lblEndDate, 0, 2, 1, 1)
        self.cmbDate = CDateEdit(self.groupBox)
        self.cmbDate.setObjectName(_fromUtf8("cmbDate"))
        self.gridLayout.addWidget(self.cmbDate, 0, 1, 1, 1)
        self.cmbEndDate = CDateEdit(self.groupBox)
        self.cmbEndDate.setObjectName(_fromUtf8("cmbEndDate"))
        self.gridLayout.addWidget(self.cmbEndDate, 0, 3, 1, 1)
        self.lblBegDate = QtGui.QLabel(self.groupBox)
        self.lblBegDate.setObjectName(_fromUtf8("lblBegDate"))
        self.gridLayout.addWidget(self.lblBegDate, 0, 0, 1, 1)
        self.gridLayout_4.addLayout(self.gridLayout, 0, 0, 1, 1)
        self.gridLayout_3 = QtGui.QGridLayout()
        self.gridLayout_3.setObjectName(_fromUtf8("gridLayout_3"))
        self.lblStatus = QtGui.QLabel(self.groupBox)
        self.lblStatus.setObjectName(_fromUtf8("lblStatus"))
        self.gridLayout_3.addWidget(self.lblStatus, 0, 0, 1, 1)
        self.cmbStatus = QtGui.QComboBox(self.groupBox)
        self.cmbStatus.setObjectName(_fromUtf8("cmbStatus"))
        self.cmbStatus.addItem(_fromUtf8(""))
        self.cmbStatus.setItemText(0, _fromUtf8(""))
        self.cmbStatus.addItem(_fromUtf8(""))
        self.cmbStatus.addItem(_fromUtf8(""))
        self.cmbStatus.addItem(_fromUtf8(""))
        self.cmbStatus.addItem(_fromUtf8(""))
        self.gridLayout_3.addWidget(self.cmbStatus, 0, 1, 1, 1)
        self.gridLayout_4.addLayout(self.gridLayout_3, 1, 0, 1, 1)
        self.gridLayout_2 = QtGui.QGridLayout()
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.btnCancel_2 = QtGui.QPushButton(self.groupBox)
        self.btnCancel_2.setObjectName(_fromUtf8("btnCancel_2"))
        self.gridLayout_2.addWidget(self.btnCancel_2, 0, 2, 1, 1)
        self.btnAply = QtGui.QPushButton(self.groupBox)
        self.btnAply.setObjectName(_fromUtf8("btnAply"))
        self.gridLayout_2.addWidget(self.btnAply, 0, 1, 1, 1)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout_2.addItem(spacerItem, 0, 0, 1, 1)
        self.gridLayout_4.addLayout(self.gridLayout_2, 10, 0, 1, 1)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.gridLayout_4.addLayout(self.horizontalLayout, 2, 0, 1, 1)
        self.gridLayout_6 = QtGui.QGridLayout()
        self.gridLayout_6.setObjectName(_fromUtf8("gridLayout_6"))
        self.lblClient = QtGui.QLabel(self.groupBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblClient.sizePolicy().hasHeightForWidth())
        self.lblClient.setSizePolicy(sizePolicy)
        self.lblClient.setObjectName(_fromUtf8("lblClient"))
        self.gridLayout_6.addWidget(self.lblClient, 0, 0, 1, 1)
        self.Client = QtGui.QLineEdit(self.groupBox)
        self.Client.setObjectName(_fromUtf8("Client"))
        self.gridLayout_6.addWidget(self.Client, 0, 1, 1, 1)
        self.gridLayout_4.addLayout(self.gridLayout_6, 3, 0, 1, 1)
        self.gridLayout_7 = QtGui.QGridLayout()
        self.gridLayout_7.setObjectName(_fromUtf8("gridLayout_7"))
        self.lblNumber = QtGui.QLabel(self.groupBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblNumber.sizePolicy().hasHeightForWidth())
        self.lblNumber.setSizePolicy(sizePolicy)
        self.lblNumber.setObjectName(_fromUtf8("lblNumber"))
        self.gridLayout_7.addWidget(self.lblNumber, 0, 0, 1, 1)
        self.Number = QtGui.QLineEdit(self.groupBox)
        self.Number.setObjectName(_fromUtf8("Number"))
        self.gridLayout_7.addWidget(self.Number, 0, 1, 1, 1)
        self.gridLayout_4.addLayout(self.gridLayout_7, 6, 0, 1, 1)
        self.verticalLayout.addWidget(self.groupBox)
        self.tblActionODLI = CTableView(DialogOdli)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tblActionODLI.sizePolicy().hasHeightForWidth())
        self.tblActionODLI.setSizePolicy(sizePolicy)
        self.tblActionODLI.setObjectName(_fromUtf8("tblActionODLI"))
        self.verticalLayout.addWidget(self.tblActionODLI)
        self.lblRecordsCount = QtGui.QLabel(DialogOdli)
        self.lblRecordsCount.setText(_fromUtf8(""))
        self.lblRecordsCount.setObjectName(_fromUtf8("lblRecordsCount"))
        self.verticalLayout.addWidget(self.lblRecordsCount)
        self.gridLayout_5 = QtGui.QGridLayout()
        self.gridLayout_5.setHorizontalSpacing(9)
        self.gridLayout_5.setObjectName(_fromUtf8("gridLayout_5"))
        self.btnOk = QtGui.QPushButton(DialogOdli)
        self.btnOk.setObjectName(_fromUtf8("btnOk"))
        self.gridLayout_5.addWidget(self.btnOk, 0, 1, 1, 1)
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout_5.addItem(spacerItem1, 0, 0, 1, 1)
        self.btnClose = QtGui.QPushButton(DialogOdli)
        self.btnClose.setObjectName(_fromUtf8("btnClose"))
        self.gridLayout_5.addWidget(self.btnClose, 0, 2, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout_5)

        self.retranslateUi(DialogOdli)
        QtCore.QMetaObject.connectSlotsByName(DialogOdli)

    def retranslateUi(self, DialogOdli):
        DialogOdli.setWindowTitle(_translate("DialogOdli", "Обмен данными лабораторных исследований", None))
        self.groupBox.setTitle(_translate("DialogOdli", "Фильтр", None))
        self.lblEndDate.setText(_translate("DialogOdli", "по", None))
        self.lblBegDate.setText(_translate("DialogOdli", "Дата создания направления с", None))
        self.lblStatus.setText(_translate("DialogOdli", "Статус ", None))
        self.cmbStatus.setItemText(1, _translate("DialogOdli", "Не выгружен в ЛИС", None))
        self.cmbStatus.setItemText(2, _translate("DialogOdli", "Заказ успешно выгружен в ЛИС", None))
        self.cmbStatus.setItemText(3, _translate("DialogOdli", "Результат загружен из ЛИС", None))
        self.cmbStatus.setItemText(4, _translate("DialogOdli", "Исследование отменено", None))
        self.btnCancel_2.setText(_translate("DialogOdli", "Сбросить", None))
        self.btnAply.setText(_translate("DialogOdli", "Применить ", None))
        self.lblClient.setText(_translate("DialogOdli", "Пациент", None))
        self.lblNumber.setText(_translate("DialogOdli", "Номер направления", None))
        self.btnOk.setText(_translate("DialogOdli", "Отправить и получить результаты", None))
        self.btnClose.setText(_translate("DialogOdli", "Отменить ", None))

from library.DateEdit import CDateEdit
from library.TableView import CTableView
