# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\Project\Samson\UP_s11\client_test\Exchange\ExportAttachDoctorSectionInfoDialog.ui'
#
# Created: Fri Nov 15 14:51:16 2024
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

class Ui_ExportAttachDoctorSectionInfoDialog(object):
    def setupUi(self, ExportAttachDoctorSectionInfoDialog):
        ExportAttachDoctorSectionInfoDialog.setObjectName(_fromUtf8("ExportAttachDoctorSectionInfoDialog"))
        ExportAttachDoctorSectionInfoDialog.resize(1370, 819)
        ExportAttachDoctorSectionInfoDialog.setSizeGripEnabled(True)
        self.gridLayout_2 = QtGui.QGridLayout(ExportAttachDoctorSectionInfoDialog)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.pbExportProgress = QtGui.QProgressBar(ExportAttachDoctorSectionInfoDialog)
        self.pbExportProgress.setObjectName(_fromUtf8("pbExportProgress"))
        self.gridLayout_2.addWidget(self.pbExportProgress, 5, 0, 1, 1)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.label_5 = QtGui.QLabel(ExportAttachDoctorSectionInfoDialog)
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.horizontalLayout_2.addWidget(self.label_5)
        self.rbShowAll = QtGui.QRadioButton(ExportAttachDoctorSectionInfoDialog)
        self.rbShowAll.setChecked(True)
        self.rbShowAll.setObjectName(_fromUtf8("rbShowAll"))
        self.horizontalLayout_2.addWidget(self.rbShowAll)
        self.rbShowErrors = QtGui.QRadioButton(ExportAttachDoctorSectionInfoDialog)
        self.rbShowErrors.setObjectName(_fromUtf8("rbShowErrors"))
        self.horizontalLayout_2.addWidget(self.rbShowErrors)
        self.cmbOrgStructure = COrgStructureComboBox(ExportAttachDoctorSectionInfoDialog)
        self.cmbOrgStructure.setMinimumSize(QtCore.QSize(230, 0))
        self.cmbOrgStructure.setObjectName(_fromUtf8("cmbOrgStructure"))
        self.horizontalLayout_2.addWidget(self.cmbOrgStructure)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.btnRefresh = QtGui.QPushButton(ExportAttachDoctorSectionInfoDialog)
        self.btnRefresh.setObjectName(_fromUtf8("btnRefresh"))
        self.horizontalLayout_2.addWidget(self.btnRefresh)
        self.gridLayout_2.addLayout(self.horizontalLayout_2, 0, 0, 1, 1)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.chbFullLog = QtGui.QCheckBox(ExportAttachDoctorSectionInfoDialog)
        self.chbFullLog.setObjectName(_fromUtf8("chbFullLog"))
        self.horizontalLayout.addWidget(self.chbFullLog)
        self.btnExport = QtGui.QPushButton(ExportAttachDoctorSectionInfoDialog)
        self.btnExport.setEnabled(False)
        self.btnExport.setObjectName(_fromUtf8("btnExport"))
        self.horizontalLayout.addWidget(self.btnExport)
        self.btnClose = QtGui.QPushButton(ExportAttachDoctorSectionInfoDialog)
        self.btnClose.setObjectName(_fromUtf8("btnClose"))
        self.horizontalLayout.addWidget(self.btnClose)
        self.gridLayout_2.addLayout(self.horizontalLayout, 7, 0, 1, 1)
        self.lblPersonOrderCount = QtGui.QLabel(ExportAttachDoctorSectionInfoDialog)
        self.lblPersonOrderCount.setObjectName(_fromUtf8("lblPersonOrderCount"))
        self.gridLayout_2.addWidget(self.lblPersonOrderCount, 1, 0, 1, 1)
        self.lblExportStatus = QtGui.QLabel(ExportAttachDoctorSectionInfoDialog)
        self.lblExportStatus.setEnabled(True)
        self.lblExportStatus.setObjectName(_fromUtf8("lblExportStatus"))
        self.gridLayout_2.addWidget(self.lblExportStatus, 3, 0, 1, 1)
        self.edExportResults = QtGui.QPlainTextEdit(ExportAttachDoctorSectionInfoDialog)
        self.edExportResults.setEnabled(True)
        self.edExportResults.setMinimumSize(QtCore.QSize(0, 235))
        self.edExportResults.setReadOnly(True)
        self.edExportResults.setObjectName(_fromUtf8("edExportResults"))
        self.gridLayout_2.addWidget(self.edExportResults, 4, 0, 1, 1)
        self.tblPersonOrder = CTableView(ExportAttachDoctorSectionInfoDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(3)
        sizePolicy.setHeightForWidth(self.tblPersonOrder.sizePolicy().hasHeightForWidth())
        self.tblPersonOrder.setSizePolicy(sizePolicy)
        self.tblPersonOrder.setObjectName(_fromUtf8("tblPersonOrder"))
        self.gridLayout_2.addWidget(self.tblPersonOrder, 2, 0, 1, 1)

        self.retranslateUi(ExportAttachDoctorSectionInfoDialog)
        QtCore.QMetaObject.connectSlotsByName(ExportAttachDoctorSectionInfoDialog)

    def retranslateUi(self, ExportAttachDoctorSectionInfoDialog):
        ExportAttachDoctorSectionInfoDialog.setWindowTitle(_translate("ExportAttachDoctorSectionInfoDialog", "Экспорт сведений о врачах и участках", None))
        self.pbExportProgress.setFormat(_translate("ExportAttachDoctorSectionInfoDialog", "%v из %m", None))
        self.label_5.setText(_translate("ExportAttachDoctorSectionInfoDialog", "Показать записи:", None))
        self.rbShowAll.setText(_translate("ExportAttachDoctorSectionInfoDialog", "все", None))
        self.rbShowErrors.setText(_translate("ExportAttachDoctorSectionInfoDialog", "с ошибками", None))
        self.btnRefresh.setText(_translate("ExportAttachDoctorSectionInfoDialog", "Обновить", None))
        self.chbFullLog.setText(_translate("ExportAttachDoctorSectionInfoDialog", "Отображать лог", None))
        self.btnExport.setText(_translate("ExportAttachDoctorSectionInfoDialog", "Экспорт", None))
        self.btnClose.setText(_translate("ExportAttachDoctorSectionInfoDialog", "Закрыть", None))
        self.lblPersonOrderCount.setText(_translate("ExportAttachDoctorSectionInfoDialog", "Всего записей: 0", None))
        self.lblExportStatus.setText(_translate("ExportAttachDoctorSectionInfoDialog", "Отправка пакетов...", None))

from library.TableView import CTableView
from Orgs.OrgStructComboBoxes import COrgStructureComboBox
