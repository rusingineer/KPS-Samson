# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\projects\Samson\UP_s11\client\Exchange\ExportDispPlanDatesDialog.ui'
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

class Ui_ExportDispPlanDatesDialog(object):
    def setupUi(self, ExportDispPlanDatesDialog):
        ExportDispPlanDatesDialog.setObjectName(_fromUtf8("ExportDispPlanDatesDialog"))
        ExportDispPlanDatesDialog.resize(682, 478)
        self.verticalLayout = QtGui.QVBoxLayout(ExportDispPlanDatesDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.label_2 = QtGui.QLabel(ExportDispPlanDatesDialog)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.horizontalLayout.addWidget(self.label_2)
        self.cmbOrgStructure = CDbComboBox(ExportDispPlanDatesDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cmbOrgStructure.sizePolicy().hasHeightForWidth())
        self.cmbOrgStructure.setSizePolicy(sizePolicy)
        self.cmbOrgStructure.setObjectName(_fromUtf8("cmbOrgStructure"))
        self.horizontalLayout.addWidget(self.cmbOrgStructure)
        self.btnExport = QtGui.QPushButton(ExportDispPlanDatesDialog)
        self.btnExport.setObjectName(_fromUtf8("btnExport"))
        self.horizontalLayout.addWidget(self.btnExport)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.label_3 = QtGui.QLabel(ExportDispPlanDatesDialog)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.horizontalLayout_3.addWidget(self.label_3)
        self.edtDate = CDateEdit(ExportDispPlanDatesDialog)
        self.edtDate.setObjectName(_fromUtf8("edtDate"))
        self.horizontalLayout_3.addWidget(self.edtDate)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.tblPlanDates = CInDocTableView(ExportDispPlanDatesDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(3)
        sizePolicy.setHeightForWidth(self.tblPlanDates.sizePolicy().hasHeightForWidth())
        self.tblPlanDates.setSizePolicy(sizePolicy)
        self.tblPlanDates.setObjectName(_fromUtf8("tblPlanDates"))
        self.verticalLayout.addWidget(self.tblPlanDates)
        self.label = QtGui.QLabel(ExportDispPlanDatesDialog)
        self.label.setObjectName(_fromUtf8("label"))
        self.verticalLayout.addWidget(self.label)
        self.tblPlanDateErrors = CTableView(ExportDispPlanDatesDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.tblPlanDateErrors.sizePolicy().hasHeightForWidth())
        self.tblPlanDateErrors.setSizePolicy(sizePolicy)
        self.tblPlanDateErrors.setObjectName(_fromUtf8("tblPlanDateErrors"))
        self.verticalLayout.addWidget(self.tblPlanDateErrors)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.btnOK = QtGui.QPushButton(ExportDispPlanDatesDialog)
        self.btnOK.setObjectName(_fromUtf8("btnOK"))
        self.horizontalLayout_2.addWidget(self.btnOK)
        self.btnCancel = QtGui.QPushButton(ExportDispPlanDatesDialog)
        self.btnCancel.setObjectName(_fromUtf8("btnCancel"))
        self.horizontalLayout_2.addWidget(self.btnCancel)
        self.btnApply = QtGui.QPushButton(ExportDispPlanDatesDialog)
        self.btnApply.setObjectName(_fromUtf8("btnApply"))
        self.horizontalLayout_2.addWidget(self.btnApply)
        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.retranslateUi(ExportDispPlanDatesDialog)
        QtCore.QMetaObject.connectSlotsByName(ExportDispPlanDatesDialog)

    def retranslateUi(self, ExportDispPlanDatesDialog):
        ExportDispPlanDatesDialog.setWindowTitle(_translate("ExportDispPlanDatesDialog", "Даты запланированных мероприятий", None))
        self.label_2.setText(_translate("ExportDispPlanDatesDialog", "Подразделение:", None))
        self.btnExport.setText(_translate("ExportDispPlanDatesDialog", "Отправить", None))
        self.label_3.setText(_translate("ExportDispPlanDatesDialog", "С даты:", None))
        self.label.setText(_translate("ExportDispPlanDatesDialog", "Ошибки при экспорте:", None))
        self.btnOK.setText(_translate("ExportDispPlanDatesDialog", "OK", None))
        self.btnCancel.setText(_translate("ExportDispPlanDatesDialog", "Отмена", None))
        self.btnApply.setText(_translate("ExportDispPlanDatesDialog", "Применить", None))

from library.DateEdit import CDateEdit
from library.DbComboBox import CDbComboBox
from library.InDocTable import CInDocTableView
from library.TableView import CTableView
