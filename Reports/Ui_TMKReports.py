# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Samson\UP_s11\client_test\Reports\TMKReports.ui'
#
# Created: Thu Mar 14 11:57:41 2024
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

class Ui_tmkReports(object):
    def setupUi(self, tmkReports):
        tmkReports.setObjectName(_fromUtf8("tmkReports"))
        tmkReports.resize(944, 698)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(tmkReports.sizePolicy().hasHeightForWidth())
        tmkReports.setSizePolicy(sizePolicy)
        self.gridLayout = QtGui.QGridLayout(tmkReports)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.tableWidget = QtGui.QTableWidget(tmkReports)
        self.tableWidget.setObjectName(_fromUtf8("tableWidget"))
        self.tableWidget.setColumnCount(0)
        self.tableWidget.setRowCount(0)
        self.gridLayout.addWidget(self.tableWidget, 0, 0, 1, 1)
        self.groupBoxFilters = QtGui.QGroupBox(tmkReports)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBoxFilters.sizePolicy().hasHeightForWidth())
        self.groupBoxFilters.setSizePolicy(sizePolicy)
        self.groupBoxFilters.setMaximumSize(QtCore.QSize(278, 16777215))
        self.groupBoxFilters.setObjectName(_fromUtf8("groupBoxFilters"))
        self.gridLayout_2 = QtGui.QGridLayout(self.groupBoxFilters)
        self.gridLayout_2.setMargin(4)
        self.gridLayout_2.setSpacing(2)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.lblTemplatesId = QtGui.QLabel(self.groupBoxFilters)
        self.lblTemplatesId.setObjectName(_fromUtf8("lblTemplatesId"))
        self.verticalLayout.addWidget(self.lblTemplatesId)
        self.cmbTemplatesId = QtGui.QComboBox(self.groupBoxFilters)
        self.cmbTemplatesId.setObjectName(_fromUtf8("cmbTemplatesId"))
        self.verticalLayout.addWidget(self.cmbTemplatesId)
        self.lblTimeCreateApplication = QtGui.QLabel(self.groupBoxFilters)
        self.lblTimeCreateApplication.setObjectName(_fromUtf8("lblTimeCreateApplication"))
        self.verticalLayout.addWidget(self.lblTimeCreateApplication)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.chkCreateApplicationBegDate = QtGui.QCheckBox(self.groupBoxFilters)
        self.chkCreateApplicationBegDate.setChecked(False)
        self.chkCreateApplicationBegDate.setObjectName(_fromUtf8("chkCreateApplicationBegDate"))
        self.horizontalLayout.addWidget(self.chkCreateApplicationBegDate)
        self.edtCreateApplicationBegDate = QtGui.QDateEdit(self.groupBoxFilters)
        self.edtCreateApplicationBegDate.setEnabled(False)
        self.edtCreateApplicationBegDate.setCalendarPopup(True)
        self.edtCreateApplicationBegDate.setObjectName(_fromUtf8("edtCreateApplicationBegDate"))
        self.horizontalLayout.addWidget(self.edtCreateApplicationBegDate)
        self.chkCreateApplicationEndDate = QtGui.QCheckBox(self.groupBoxFilters)
        self.chkCreateApplicationEndDate.setObjectName(_fromUtf8("chkCreateApplicationEndDate"))
        self.horizontalLayout.addWidget(self.chkCreateApplicationEndDate)
        self.edtCreateApplicationEndDate = QtGui.QDateEdit(self.groupBoxFilters)
        self.edtCreateApplicationEndDate.setEnabled(False)
        self.edtCreateApplicationEndDate.setCalendarPopup(True)
        self.edtCreateApplicationEndDate.setObjectName(_fromUtf8("edtCreateApplicationEndDate"))
        self.horizontalLayout.addWidget(self.edtCreateApplicationEndDate)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.lblTimeCreateApplication_2 = QtGui.QLabel(self.groupBoxFilters)
        self.lblTimeCreateApplication_2.setObjectName(_fromUtf8("lblTimeCreateApplication_2"))
        self.verticalLayout.addWidget(self.lblTimeCreateApplication_2)
        self.cmbFilterI = CMultivalueComboBox(self.groupBoxFilters)
        self.cmbFilterI.setEnabled(True)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cmbFilterI.sizePolicy().hasHeightForWidth())
        self.cmbFilterI.setSizePolicy(sizePolicy)
        self.cmbFilterI.setObjectName(_fromUtf8("cmbFilterI"))
        self.verticalLayout.addWidget(self.cmbFilterI)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.chkGetData = QtGui.QCheckBox(self.groupBoxFilters)
        self.chkGetData.setObjectName(_fromUtf8("chkGetData"))
        self.verticalLayout.addWidget(self.chkGetData)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.btnFilterApply = QtGui.QPushButton(self.groupBoxFilters)
        self.btnFilterApply.setObjectName(_fromUtf8("btnFilterApply"))
        self.horizontalLayout_2.addWidget(self.btnFilterApply)
        self.btnFilterReset = QtGui.QPushButton(self.groupBoxFilters)
        self.btnFilterReset.setObjectName(_fromUtf8("btnFilterReset"))
        self.horizontalLayout_2.addWidget(self.btnFilterReset)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.gridLayout_2.addLayout(self.verticalLayout, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.groupBoxFilters, 0, 1, 1, 1)

        self.retranslateUi(tmkReports)
        QtCore.QObject.connect(self.chkCreateApplicationBegDate, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.edtCreateApplicationBegDate.setEnabled)
        QtCore.QObject.connect(self.chkCreateApplicationEndDate, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.edtCreateApplicationEndDate.setEnabled)
        QtCore.QMetaObject.connectSlotsByName(tmkReports)

    def retranslateUi(self, tmkReports):
        tmkReports.setWindowTitle(_translate("tmkReports", "TestWindow", None))
        self.groupBoxFilters.setTitle(_translate("tmkReports", "Фильтры", None))
        self.lblTemplatesId.setText(_translate("tmkReports", "Получить данные отчета по шаблону", None))
        self.lblTimeCreateApplication.setText(_translate("tmkReports", "Время создания заявки ", None))
        self.chkCreateApplicationBegDate.setText(_translate("tmkReports", "С", None))
        self.chkCreateApplicationEndDate.setText(_translate("tmkReports", "по", None))
        self.lblTimeCreateApplication_2.setText(_translate("tmkReports", "Спрятать колонки", None))
        self.chkGetData.setText(_translate("tmkReports", "Получать данные с сервера ", None))
        self.btnFilterApply.setText(_translate("tmkReports", "Применить", None))
        self.btnFilterReset.setText(_translate("tmkReports", "Сбросить", None))

from library.MultivalueComboBox import CMultivalueComboBox
