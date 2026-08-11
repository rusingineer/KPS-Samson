# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Samson\UP_s11\client_test\Reports\TMKReports.ui'
#
# Created: Thu Mar 26 09:40:42 2026
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
        tmkReports.resize(942, 698)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(tmkReports.sizePolicy().hasHeightForWidth())
        tmkReports.setSizePolicy(sizePolicy)
        self.gridLayout = QtGui.QGridLayout(tmkReports)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.hrzLay_3 = QtGui.QHBoxLayout()
        self.hrzLay_3.setObjectName(_fromUtf8("hrzLay_3"))
        self.lblNumRec = QtGui.QLabel(tmkReports)
        self.lblNumRec.setObjectName(_fromUtf8("lblNumRec"))
        self.hrzLay_3.addWidget(self.lblNumRec)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.hrzLay_3.addItem(spacerItem)
        self.btnPrint = QtGui.QPushButton(tmkReports)
        self.btnPrint.setObjectName(_fromUtf8("btnPrint"))
        self.hrzLay_3.addWidget(self.btnPrint)
        self.gridLayout.addLayout(self.hrzLay_3, 1, 0, 1, 1)
        self.groupBoxFilters = QtGui.QGroupBox(tmkReports)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBoxFilters.sizePolicy().hasHeightForWidth())
        self.groupBoxFilters.setSizePolicy(sizePolicy)
        self.groupBoxFilters.setMaximumSize(QtCore.QSize(350, 16777215))
        self.groupBoxFilters.setObjectName(_fromUtf8("groupBoxFilters"))
        self.gridLayout_2 = QtGui.QGridLayout(self.groupBoxFilters)
        self.gridLayout_2.setMargin(4)
        self.gridLayout_2.setSpacing(2)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.vrtLay = QtGui.QVBoxLayout()
        self.vrtLay.setObjectName(_fromUtf8("vrtLay"))
        self.lblTemplatesId = QtGui.QLabel(self.groupBoxFilters)
        self.lblTemplatesId.setObjectName(_fromUtf8("lblTemplatesId"))
        self.vrtLay.addWidget(self.lblTemplatesId)
        self.cmbTemplatesId = QtGui.QComboBox(self.groupBoxFilters)
        self.cmbTemplatesId.setObjectName(_fromUtf8("cmbTemplatesId"))
        self.vrtLay.addWidget(self.cmbTemplatesId)
        self.lblCreateDate = QtGui.QLabel(self.groupBoxFilters)
        self.lblCreateDate.setObjectName(_fromUtf8("lblCreateDate"))
        self.vrtLay.addWidget(self.lblCreateDate)
        self.hrzLay = QtGui.QHBoxLayout()
        self.hrzLay.setObjectName(_fromUtf8("hrzLay"))
        self.chkBegDate = QtGui.QCheckBox(self.groupBoxFilters)
        self.chkBegDate.setChecked(False)
        self.chkBegDate.setObjectName(_fromUtf8("chkBegDate"))
        self.hrzLay.addWidget(self.chkBegDate)
        self.edtBegDate = CDateEdit(self.groupBoxFilters)
        self.edtBegDate.setEnabled(False)
        self.edtBegDate.setCalendarPopup(True)
        self.edtBegDate.setObjectName(_fromUtf8("edtBegDate"))
        self.hrzLay.addWidget(self.edtBegDate)
        self.chkEndDate = QtGui.QCheckBox(self.groupBoxFilters)
        self.chkEndDate.setObjectName(_fromUtf8("chkEndDate"))
        self.hrzLay.addWidget(self.chkEndDate)
        self.edtEndDate = CDateEdit(self.groupBoxFilters)
        self.edtEndDate.setEnabled(False)
        self.edtEndDate.setCalendarPopup(True)
        self.edtEndDate.setObjectName(_fromUtf8("edtEndDate"))
        self.hrzLay.addWidget(self.edtEndDate)
        self.vrtLay.addLayout(self.hrzLay)
        self.lblDirections = QtGui.QLabel(self.groupBoxFilters)
        self.lblDirections.setObjectName(_fromUtf8("lblDirections"))
        self.vrtLay.addWidget(self.lblDirections)
        self.cmbDirections = QtGui.QComboBox(self.groupBoxFilters)
        self.cmbDirections.setObjectName(_fromUtf8("cmbDirections"))
        self.cmbDirections.addItem(_fromUtf8(""))
        self.cmbDirections.addItem(_fromUtf8(""))
        self.cmbDirections.addItem(_fromUtf8(""))
        self.vrtLay.addWidget(self.cmbDirections)
        self.lblStatusName = QtGui.QLabel(self.groupBoxFilters)
        self.lblStatusName.setObjectName(_fromUtf8("lblStatusName"))
        self.vrtLay.addWidget(self.lblStatusName)
        self.cmbStatusName = CMultivalueComboBox(self.groupBoxFilters)
        self.cmbStatusName.setObjectName(_fromUtf8("cmbStatusName"))
        self.vrtLay.addWidget(self.cmbStatusName)
        self.lblOrganisation = QtGui.QLabel(self.groupBoxFilters)
        self.lblOrganisation.setObjectName(_fromUtf8("lblOrganisation"))
        self.vrtLay.addWidget(self.lblOrganisation)
        self.cmbOrganisation = CMultivalueComboBox(self.groupBoxFilters)
        self.cmbOrganisation.setObjectName(_fromUtf8("cmbOrganisation"))
        self.vrtLay.addWidget(self.cmbOrganisation)
        self.chkGetData = QtGui.QCheckBox(self.groupBoxFilters)
        self.chkGetData.setObjectName(_fromUtf8("chkGetData"))
        self.vrtLay.addWidget(self.chkGetData)
        spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.vrtLay.addItem(spacerItem1)
        self.hrzLay_2 = QtGui.QHBoxLayout()
        self.hrzLay_2.setObjectName(_fromUtf8("hrzLay_2"))
        self.btnFilterApply = QtGui.QPushButton(self.groupBoxFilters)
        self.btnFilterApply.setObjectName(_fromUtf8("btnFilterApply"))
        self.hrzLay_2.addWidget(self.btnFilterApply)
        self.btnFilterReset = QtGui.QPushButton(self.groupBoxFilters)
        self.btnFilterReset.setObjectName(_fromUtf8("btnFilterReset"))
        self.hrzLay_2.addWidget(self.btnFilterReset)
        self.vrtLay.addLayout(self.hrzLay_2)
        self.gridLayout_2.addLayout(self.vrtLay, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.groupBoxFilters, 0, 1, 2, 1)
        self.tblReport = CTableView(tmkReports)
        self.tblReport.setObjectName(_fromUtf8("tblReport"))
        self.gridLayout.addWidget(self.tblReport, 0, 0, 1, 1)

        self.retranslateUi(tmkReports)
        QtCore.QObject.connect(self.chkBegDate, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.edtBegDate.setEnabled)
        QtCore.QObject.connect(self.chkEndDate, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.edtEndDate.setEnabled)
        QtCore.QMetaObject.connectSlotsByName(tmkReports)

    def retranslateUi(self, tmkReports):
        tmkReports.setWindowTitle(_translate("tmkReports", "TestWindow", None))
        self.lblNumRec.setText(_translate("tmkReports", "Всего записей: 0", None))
        self.btnPrint.setText(_translate("tmkReports", "Печать", None))
        self.groupBoxFilters.setTitle(_translate("tmkReports", "Фильтры", None))
        self.lblTemplatesId.setText(_translate("tmkReports", "Получить данные отчета по шаблону", None))
        self.lblCreateDate.setText(_translate("tmkReports", "Время создания заявки ", None))
        self.chkBegDate.setText(_translate("tmkReports", "С", None))
        self.chkEndDate.setText(_translate("tmkReports", "по", None))
        self.lblDirections.setText(_translate("tmkReports", "Направления", None))
        self.cmbDirections.setItemText(0, _translate("tmkReports", "Все", None))
        self.cmbDirections.setItemText(1, _translate("tmkReports", "Входящие", None))
        self.cmbDirections.setItemText(2, _translate("tmkReports", "Исходящие", None))
        self.lblStatusName.setText(_translate("tmkReports", "Статус заявки", None))
        self.lblOrganisation.setText(_translate("tmkReports", "Целевая организация", None))
        self.chkGetData.setText(_translate("tmkReports", "Загрузить данные с сервера", None))
        self.btnFilterApply.setText(_translate("tmkReports", "Применить", None))
        self.btnFilterReset.setText(_translate("tmkReports", "Сбросить", None))

from library.MultivalueComboBox import CMultivalueComboBox
from library.TableView import CTableView
from library.DateEdit import CDateEdit
