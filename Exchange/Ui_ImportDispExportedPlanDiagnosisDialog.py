# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Samson\UP_s11\client_test\Exchange\ImportDispExportedPlanDiagnosisDialog.ui'
#
# Created: Tue Dec 19 15:21:04 2023
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

class Ui_ImportDispExportedPlanDiagnosisDialog(object):
    def setupUi(self, ImportDispExportedPlanDiagnosisDialog):
        ImportDispExportedPlanDiagnosisDialog.setObjectName(_fromUtf8("ImportDispExportedPlanDiagnosisDialog"))
        ImportDispExportedPlanDiagnosisDialog.resize(716, 542)
        self.verticalLayout = QtGui.QVBoxLayout(ImportDispExportedPlanDiagnosisDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.label = QtGui.QLabel(ImportDispExportedPlanDiagnosisDialog)
        self.label.setObjectName(_fromUtf8("label"))
        self.horizontalLayout.addWidget(self.label)
        self.sbYear = QtGui.QSpinBox(ImportDispExportedPlanDiagnosisDialog)
        self.sbYear.setMinimum(2017)
        self.sbYear.setMaximum(9999)
        self.sbYear.setObjectName(_fromUtf8("sbYear"))
        self.horizontalLayout.addWidget(self.sbYear)
        self.label_2 = QtGui.QLabel(ImportDispExportedPlanDiagnosisDialog)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.horizontalLayout.addWidget(self.label_2)
        self.cmbMonth = QtGui.QComboBox(ImportDispExportedPlanDiagnosisDialog)
        self.cmbMonth.setObjectName(_fromUtf8("cmbMonth"))
        self.cmbMonth.addItem(_fromUtf8(""))
        self.cmbMonth.addItem(_fromUtf8(""))
        self.cmbMonth.addItem(_fromUtf8(""))
        self.cmbMonth.addItem(_fromUtf8(""))
        self.cmbMonth.addItem(_fromUtf8(""))
        self.cmbMonth.addItem(_fromUtf8(""))
        self.cmbMonth.addItem(_fromUtf8(""))
        self.cmbMonth.addItem(_fromUtf8(""))
        self.cmbMonth.addItem(_fromUtf8(""))
        self.cmbMonth.addItem(_fromUtf8(""))
        self.cmbMonth.addItem(_fromUtf8(""))
        self.cmbMonth.addItem(_fromUtf8(""))
        self.horizontalLayout.addWidget(self.cmbMonth)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.btnSelectNotFound = QtGui.QPushButton(ImportDispExportedPlanDiagnosisDialog)
        self.btnSelectNotFound.setObjectName(_fromUtf8("btnSelectNotFound"))
        self.horizontalLayout.addWidget(self.btnSelectNotFound)
        self.btnRefresh = QtGui.QPushButton(ImportDispExportedPlanDiagnosisDialog)
        self.btnRefresh.setObjectName(_fromUtf8("btnRefresh"))
        self.horizontalLayout.addWidget(self.btnRefresh)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.lblExpPlanCount = QtGui.QLabel(ImportDispExportedPlanDiagnosisDialog)
        self.lblExpPlanCount.setObjectName(_fromUtf8("lblExpPlanCount"))
        self.verticalLayout.addWidget(self.lblExpPlanCount)
        self.tblExportedPlan = CTableView(ImportDispExportedPlanDiagnosisDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(3)
        sizePolicy.setHeightForWidth(self.tblExportedPlan.sizePolicy().hasHeightForWidth())
        self.tblExportedPlan.setSizePolicy(sizePolicy)
        self.tblExportedPlan.setObjectName(_fromUtf8("tblExportedPlan"))
        self.verticalLayout.addWidget(self.tblExportedPlan)
        self.label_4 = QtGui.QLabel(ImportDispExportedPlanDiagnosisDialog)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.verticalLayout.addWidget(self.label_4)
        self.tblExportedPlanErrors = CTableView(ImportDispExportedPlanDiagnosisDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.tblExportedPlanErrors.sizePolicy().hasHeightForWidth())
        self.tblExportedPlanErrors.setSizePolicy(sizePolicy)
        self.tblExportedPlanErrors.setObjectName(_fromUtf8("tblExportedPlanErrors"))
        self.verticalLayout.addWidget(self.tblExportedPlanErrors)
        self.lblDeleteStatus = QtGui.QLabel(ImportDispExportedPlanDiagnosisDialog)
        self.lblDeleteStatus.setObjectName(_fromUtf8("lblDeleteStatus"))
        self.verticalLayout.addWidget(self.lblDeleteStatus)
        self.pbDeleteProgress = QtGui.QProgressBar(ImportDispExportedPlanDiagnosisDialog)
        self.pbDeleteProgress.setObjectName(_fromUtf8("pbDeleteProgress"))
        self.verticalLayout.addWidget(self.pbDeleteProgress)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.btnPrint = QtGui.QPushButton(ImportDispExportedPlanDiagnosisDialog)
        self.btnPrint.setObjectName(_fromUtf8("btnPrint"))
        self.horizontalLayout_2.addWidget(self.btnPrint)
        self.btnSelectAll = QtGui.QPushButton(ImportDispExportedPlanDiagnosisDialog)
        self.btnSelectAll.setObjectName(_fromUtf8("btnSelectAll"))
        self.horizontalLayout_2.addWidget(self.btnSelectAll)
        self.btnDeleteSelected = QtGui.QPushButton(ImportDispExportedPlanDiagnosisDialog)
        self.btnDeleteSelected.setObjectName(_fromUtf8("btnDeleteSelected"))
        self.horizontalLayout_2.addWidget(self.btnDeleteSelected)
        self.btnClose = QtGui.QPushButton(ImportDispExportedPlanDiagnosisDialog)
        self.btnClose.setObjectName(_fromUtf8("btnClose"))
        self.horizontalLayout_2.addWidget(self.btnClose)
        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.retranslateUi(ImportDispExportedPlanDiagnosisDialog)
        self.cmbMonth.setCurrentIndex(11)
        QtCore.QMetaObject.connectSlotsByName(ImportDispExportedPlanDiagnosisDialog)

    def retranslateUi(self, ImportDispExportedPlanDiagnosisDialog):
        ImportDispExportedPlanDiagnosisDialog.setWindowTitle(_translate("ImportDispExportedPlanDiagnosisDialog", "Список граждан из ТФОМС, запланированных на диспансерные осмотры", None))
        self.label.setText(_translate("ImportDispExportedPlanDiagnosisDialog", "Год:", None))
        self.label_2.setText(_translate("ImportDispExportedPlanDiagnosisDialog", "Месяц", None))
        self.cmbMonth.setItemText(0, _translate("ImportDispExportedPlanDiagnosisDialog", "январь", None))
        self.cmbMonth.setItemText(1, _translate("ImportDispExportedPlanDiagnosisDialog", "февраль", None))
        self.cmbMonth.setItemText(2, _translate("ImportDispExportedPlanDiagnosisDialog", "март", None))
        self.cmbMonth.setItemText(3, _translate("ImportDispExportedPlanDiagnosisDialog", "апрель", None))
        self.cmbMonth.setItemText(4, _translate("ImportDispExportedPlanDiagnosisDialog", "май", None))
        self.cmbMonth.setItemText(5, _translate("ImportDispExportedPlanDiagnosisDialog", "июнь", None))
        self.cmbMonth.setItemText(6, _translate("ImportDispExportedPlanDiagnosisDialog", "июль", None))
        self.cmbMonth.setItemText(7, _translate("ImportDispExportedPlanDiagnosisDialog", "август", None))
        self.cmbMonth.setItemText(8, _translate("ImportDispExportedPlanDiagnosisDialog", "сентябрь", None))
        self.cmbMonth.setItemText(9, _translate("ImportDispExportedPlanDiagnosisDialog", "октябрь", None))
        self.cmbMonth.setItemText(10, _translate("ImportDispExportedPlanDiagnosisDialog", "ноябрь", None))
        self.cmbMonth.setItemText(11, _translate("ImportDispExportedPlanDiagnosisDialog", "декабрь", None))
        self.btnSelectNotFound.setText(_translate("ImportDispExportedPlanDiagnosisDialog", "Выбрать не найденных", None))
        self.btnRefresh.setText(_translate("ImportDispExportedPlanDiagnosisDialog", "Загрузить список", None))
        self.lblExpPlanCount.setText(_translate("ImportDispExportedPlanDiagnosisDialog", "На сервисе: 0 записей", None))
        self.label_4.setText(_translate("ImportDispExportedPlanDiagnosisDialog", "Ошибки при удалении:", None))
        self.lblDeleteStatus.setText(_translate("ImportDispExportedPlanDiagnosisDialog", "Отправка пакетов...", None))
        self.pbDeleteProgress.setFormat(_translate("ImportDispExportedPlanDiagnosisDialog", "%v из %m", None))
        self.btnPrint.setText(_translate("ImportDispExportedPlanDiagnosisDialog", "Печать", None))
        self.btnSelectAll.setText(_translate("ImportDispExportedPlanDiagnosisDialog", "Выбрать всех", None))
        self.btnDeleteSelected.setText(_translate("ImportDispExportedPlanDiagnosisDialog", "Удалить выбранные", None))
        self.btnClose.setText(_translate("ImportDispExportedPlanDiagnosisDialog", "Закрыть", None))

from library.TableView import CTableView
