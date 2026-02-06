# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\projects\Samson\UP_s11\client\Events\ActionGroupSignPage1.ui'
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

class Ui_ActionGroupSignPage1(object):
    def setupUi(self, ActionGroupSignPage1):
        ActionGroupSignPage1.setObjectName(_fromUtf8("ActionGroupSignPage1"))
        ActionGroupSignPage1.resize(891, 868)
        self.verticalLayout = QtGui.QVBoxLayout(ActionGroupSignPage1)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.splitter = QtGui.QSplitter(ActionGroupSignPage1)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.splitter.sizePolicy().hasHeightForWidth())
        self.splitter.setSizePolicy(sizePolicy)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setObjectName(_fromUtf8("splitter"))
        self.layoutWidget = QtGui.QWidget(self.splitter)
        self.layoutWidget.setObjectName(_fromUtf8("layoutWidget"))
        self.gridLayout = QtGui.QGridLayout(self.layoutWidget)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.btnResetFilters = QtGui.QPushButton(self.layoutWidget)
        self.btnResetFilters.setObjectName(_fromUtf8("btnResetFilters"))
        self.gridLayout.addWidget(self.btnResetFilters, 7, 0, 1, 1)
        self.chkSetPerson = QtGui.QCheckBox(self.layoutWidget)
        self.chkSetPerson.setObjectName(_fromUtf8("chkSetPerson"))
        self.gridLayout.addWidget(self.chkSetPerson, 4, 0, 1, 1)
        self.cmbSetPerson = CPersonComboBoxEx(self.layoutWidget)
        self.cmbSetPerson.setEnabled(False)
        self.cmbSetPerson.setObjectName(_fromUtf8("cmbSetPerson"))
        self.gridLayout.addWidget(self.cmbSetPerson, 4, 1, 1, 2)
        self.lblCountRecords = QtGui.QLabel(self.layoutWidget)
        self.lblCountRecords.setObjectName(_fromUtf8("lblCountRecords"))
        self.gridLayout.addWidget(self.lblCountRecords, 9, 0, 1, 2)
        self.edtExecBegDate = CDateEdit(self.layoutWidget)
        self.edtExecBegDate.setEnabled(False)
        self.edtExecBegDate.setObjectName(_fromUtf8("edtExecBegDate"))
        self.gridLayout.addWidget(self.edtExecBegDate, 2, 1, 1, 1)
        self.chkActionStatus = QtGui.QLabel(self.layoutWidget)
        self.chkActionStatus.setObjectName(_fromUtf8("chkActionStatus"))
        self.gridLayout.addWidget(self.chkActionStatus, 0, 0, 1, 1)
        self.chkSetDate = QtGui.QCheckBox(self.layoutWidget)
        self.chkSetDate.setObjectName(_fromUtf8("chkSetDate"))
        self.gridLayout.addWidget(self.chkSetDate, 1, 0, 1, 1)
        self.chkWithoutDocuments = QtGui.QCheckBox(self.layoutWidget)
        self.chkWithoutDocuments.setObjectName(_fromUtf8("chkWithoutDocuments"))
        self.gridLayout.addWidget(self.chkWithoutDocuments, 5, 0, 1, 3)
        self.edtSetBegDate = CDateEdit(self.layoutWidget)
        self.edtSetBegDate.setEnabled(False)
        self.edtSetBegDate.setCalendarPopup(True)
        self.edtSetBegDate.setObjectName(_fromUtf8("edtSetBegDate"))
        self.gridLayout.addWidget(self.edtSetBegDate, 1, 1, 1, 1)
        self.cmbActionStatus = QtGui.QComboBox(self.layoutWidget)
        self.cmbActionStatus.setObjectName(_fromUtf8("cmbActionStatus"))
        self.cmbActionStatus.addItem(_fromUtf8(""))
        self.cmbActionStatus.addItem(_fromUtf8(""))
        self.cmbActionStatus.addItem(_fromUtf8(""))
        self.cmbActionStatus.addItem(_fromUtf8(""))
        self.cmbActionStatus.addItem(_fromUtf8(""))
        self.cmbActionStatus.addItem(_fromUtf8(""))
        self.cmbActionStatus.addItem(_fromUtf8(""))
        self.cmbActionStatus.addItem(_fromUtf8(""))
        self.gridLayout.addWidget(self.cmbActionStatus, 0, 1, 1, 2)
        self.tblActions = CInDocTableView(self.layoutWidget)
        self.tblActions.setObjectName(_fromUtf8("tblActions"))
        self.gridLayout.addWidget(self.tblActions, 8, 0, 1, 3)
        self.cmbPerson = CPersonComboBoxEx(self.layoutWidget)
        self.cmbPerson.setEnabled(False)
        self.cmbPerson.setObjectName(_fromUtf8("cmbPerson"))
        self.gridLayout.addWidget(self.cmbPerson, 3, 1, 1, 2)
        self.chkExecDate = QtGui.QCheckBox(self.layoutWidget)
        self.chkExecDate.setObjectName(_fromUtf8("chkExecDate"))
        self.gridLayout.addWidget(self.chkExecDate, 2, 0, 1, 1)
        self.chkPerson = QtGui.QCheckBox(self.layoutWidget)
        self.chkPerson.setObjectName(_fromUtf8("chkPerson"))
        self.gridLayout.addWidget(self.chkPerson, 3, 0, 1, 1)
        self.edtExecEndDate = CDateEdit(self.layoutWidget)
        self.edtExecEndDate.setEnabled(False)
        self.edtExecEndDate.setObjectName(_fromUtf8("edtExecEndDate"))
        self.gridLayout.addWidget(self.edtExecEndDate, 2, 2, 1, 1)
        self.edtSetEndDate = CDateEdit(self.layoutWidget)
        self.edtSetEndDate.setEnabled(False)
        self.edtSetEndDate.setObjectName(_fromUtf8("edtSetEndDate"))
        self.gridLayout.addWidget(self.edtSetEndDate, 1, 2, 1, 1)
        self.chkExportSuitable = QtGui.QCheckBox(self.layoutWidget)
        self.chkExportSuitable.setObjectName(_fromUtf8("chkExportSuitable"))
        self.gridLayout.addWidget(self.chkExportSuitable, 6, 0, 1, 3)
        self.txtReport = CReportBrowser(self.splitter)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("MS Shell Dlg 2"))
        font.setPointSize(10)
        self.txtReport.setFont(font)
        self.txtReport.setObjectName(_fromUtf8("txtReport"))
        self.verticalLayout.addWidget(self.splitter)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.btnSelectAll = QtGui.QPushButton(ActionGroupSignPage1)
        self.btnSelectAll.setObjectName(_fromUtf8("btnSelectAll"))
        self.horizontalLayout.addWidget(self.btnSelectAll)
        self.btnClearAll = QtGui.QPushButton(ActionGroupSignPage1)
        self.btnClearAll.setObjectName(_fromUtf8("btnClearAll"))
        self.horizontalLayout.addWidget(self.btnClearAll)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(ActionGroupSignPage1)
        QtCore.QObject.connect(self.chkSetDate, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.edtSetBegDate.setEnabled)
        QtCore.QObject.connect(self.chkSetDate, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.edtSetEndDate.setEnabled)
        QtCore.QObject.connect(self.chkExecDate, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.edtExecBegDate.setEnabled)
        QtCore.QObject.connect(self.chkExecDate, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.edtExecEndDate.setEnabled)
        QtCore.QObject.connect(self.chkPerson, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.cmbPerson.setEnabled)
        QtCore.QObject.connect(self.chkSetPerson, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.cmbSetPerson.setEnabled)
        QtCore.QMetaObject.connectSlotsByName(ActionGroupSignPage1)

    def retranslateUi(self, ActionGroupSignPage1):
        ActionGroupSignPage1.setWindowTitle(_translate("ActionGroupSignPage1", "Групповое подписание", None))
        self.btnResetFilters.setText(_translate("ActionGroupSignPage1", "Сбросить", None))
        self.chkSetPerson.setText(_translate("ActionGroupSignPage1", "Назначивший", None))
        self.lblCountRecords.setText(_translate("ActionGroupSignPage1", "Всего записей: 0", None))
        self.chkActionStatus.setText(_translate("ActionGroupSignPage1", "Состояние", None))
        self.chkSetDate.setText(_translate("ActionGroupSignPage1", "Начато", None))
        self.chkWithoutDocuments.setText(_translate("ActionGroupSignPage1", "Не имеет прикрепленного и подписанного документа", None))
        self.cmbActionStatus.setItemText(0, _translate("ActionGroupSignPage1", "Не задано", None))
        self.cmbActionStatus.setItemText(1, _translate("ActionGroupSignPage1", "Начато", None))
        self.cmbActionStatus.setItemText(2, _translate("ActionGroupSignPage1", "Ожидание", None))
        self.cmbActionStatus.setItemText(3, _translate("ActionGroupSignPage1", "Закончено", None))
        self.cmbActionStatus.setItemText(4, _translate("ActionGroupSignPage1", "Отменено", None))
        self.cmbActionStatus.setItemText(5, _translate("ActionGroupSignPage1", "Без результата", None))
        self.cmbActionStatus.setItemText(6, _translate("ActionGroupSignPage1", "Назначено", None))
        self.cmbActionStatus.setItemText(7, _translate("ActionGroupSignPage1", "Отказ", None))
        self.chkExecDate.setText(_translate("ActionGroupSignPage1", "Выполнено", None))
        self.chkPerson.setText(_translate("ActionGroupSignPage1", "Исполнитель", None))
        self.chkExportSuitable.setText(_translate("ActionGroupSignPage1", "Подлежат выгрузке в РЭМД, ВИМИС", None))
        self.btnSelectAll.setText(_translate("ActionGroupSignPage1", "Выбрать все", None))
        self.btnClearAll.setText(_translate("ActionGroupSignPage1", "Очистить все", None))

from Orgs.PersonComboBoxEx import CPersonComboBoxEx
from Reports.ReportBrowser import CReportBrowser
from library.DateEdit import CDateEdit
from library.InDocTable import CInDocTableView
