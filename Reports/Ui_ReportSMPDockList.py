# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ReportSMPDockList.ui'
#
# Created: Wed Mar 19 13:47:25 2025
#      by: PyQt4 UI code generator 4.11.2
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

class Ui_ReportSMPDockList(object):
    def setupUi(self, ReportSMPDockList):
        ReportSMPDockList.setObjectName(_fromUtf8("ReportSMPDockList"))
        ReportSMPDockList.setWindowModality(QtCore.Qt.ApplicationModal)
        ReportSMPDockList.resize(549, 366)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(ReportSMPDockList.sizePolicy().hasHeightForWidth())
        ReportSMPDockList.setSizePolicy(sizePolicy)
        ReportSMPDockList.setSizeGripEnabled(True)
        self.gridlayout = QtGui.QGridLayout(ReportSMPDockList)
        self.gridlayout.setMargin(4)
        self.gridlayout.setSpacing(4)
        self.gridlayout.setObjectName(_fromUtf8("gridlayout"))
        self.edtEndDate = CDateEdit(ReportSMPDockList)
        self.edtEndDate.setCalendarPopup(True)
        self.edtEndDate.setObjectName(_fromUtf8("edtEndDate"))
        self.gridlayout.addWidget(self.edtEndDate, 1, 1, 1, 1)
        self.edtBegDate = CDateEdit(ReportSMPDockList)
        self.edtBegDate.setCalendarPopup(True)
        self.edtBegDate.setObjectName(_fromUtf8("edtBegDate"))
        self.gridlayout.addWidget(self.edtBegDate, 0, 1, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(ReportSMPDockList)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridlayout.addWidget(self.buttonBox, 15, 0, 1, 3)
        self.lblBegDate = QtGui.QLabel(ReportSMPDockList)
        self.lblBegDate.setObjectName(_fromUtf8("lblBegDate"))
        self.gridlayout.addWidget(self.lblBegDate, 0, 0, 1, 1)
        self.lblEndDate = QtGui.QLabel(ReportSMPDockList)
        self.lblEndDate.setObjectName(_fromUtf8("lblEndDate"))
        self.gridlayout.addWidget(self.lblEndDate, 1, 0, 1, 1)
        self.lblOrgStructure = QtGui.QLabel(ReportSMPDockList)
        self.lblOrgStructure.setObjectName(_fromUtf8("lblOrgStructure"))
        self.gridlayout.addWidget(self.lblOrgStructure, 4, 0, 1, 1)
        self.cmbOrgStructure = COrgStructureComboBox(ReportSMPDockList)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cmbOrgStructure.sizePolicy().hasHeightForWidth())
        self.cmbOrgStructure.setSizePolicy(sizePolicy)
        self.cmbOrgStructure.setObjectName(_fromUtf8("cmbOrgStructure"))
        self.gridlayout.addWidget(self.cmbOrgStructure, 4, 1, 1, 2)
        self.gridLayout_2 = QtGui.QGridLayout()
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.chb03 = QtGui.QCheckBox(ReportSMPDockList)
        self.chb03.setObjectName(_fromUtf8("chb03"))
        self.gridLayout_2.addWidget(self.chb03, 1, 1, 1, 1)
        self.chbDoctorCome = QtGui.QCheckBox(ReportSMPDockList)
        self.chbDoctorCome.setObjectName(_fromUtf8("chbDoctorCome"))
        self.gridLayout_2.addWidget(self.chbDoctorCome, 2, 1, 1, 1)
        self.chbNMP = QtGui.QCheckBox(ReportSMPDockList)
        self.chbNMP.setObjectName(_fromUtf8("chbNMP"))
        self.gridLayout_2.addWidget(self.chbNMP, 0, 1, 1, 1)
        self.chbShowEventName = QtGui.QCheckBox(ReportSMPDockList)
        self.chbShowEventName.setObjectName(_fromUtf8("chbShowEventName"))
        self.gridLayout_2.addWidget(self.chbShowEventName, 7, 1, 1, 1)
        self.chbShowCallOccasion = QtGui.QCheckBox(ReportSMPDockList)
        self.chbShowCallOccasion.setObjectName(_fromUtf8("chbShowCallOccasion"))
        self.gridLayout_2.addWidget(self.chbShowCallOccasion, 6, 1, 1, 1)
        self.lblShow = QtGui.QLabel(ReportSMPDockList)
        self.lblShow.setObjectName(_fromUtf8("lblShow"))
        self.gridLayout_2.addWidget(self.lblShow, 4, 0, 1, 1)
        self.chbShowDiseaseBasic = QtGui.QCheckBox(ReportSMPDockList)
        self.chbShowDiseaseBasic.setObjectName(_fromUtf8("chbShowDiseaseBasic"))
        self.gridLayout_2.addWidget(self.chbShowDiseaseBasic, 4, 1, 1, 1)
        self.chbShowComplaints = QtGui.QCheckBox(ReportSMPDockList)
        self.chbShowComplaints.setObjectName(_fromUtf8("chbShowComplaints"))
        self.gridLayout_2.addWidget(self.chbShowComplaints, 5, 1, 1, 1)
        spacerItem = QtGui.QSpacerItem(10, 20, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.gridLayout_2.addItem(spacerItem, 3, 1, 1, 1)
        self.gridlayout.addLayout(self.gridLayout_2, 6, 0, 1, 2)
        self.lblAge = QtGui.QLabel(ReportSMPDockList)
        self.lblAge.setObjectName(_fromUtf8("lblAge"))
        self.gridlayout.addWidget(self.lblAge, 5, 0, 1, 1)
        self.cmbAgeGroup = QtGui.QComboBox(ReportSMPDockList)
        self.cmbAgeGroup.setObjectName(_fromUtf8("cmbAgeGroup"))
        self.cmbAgeGroup.addItem(_fromUtf8(""))
        self.cmbAgeGroup.addItem(_fromUtf8(""))
        self.cmbAgeGroup.addItem(_fromUtf8(""))
        self.gridlayout.addWidget(self.cmbAgeGroup, 5, 1, 1, 2)
        self.lblBegDate.setBuddy(self.edtBegDate)
        self.lblEndDate.setBuddy(self.edtEndDate)
        self.lblOrgStructure.setBuddy(self.cmbOrgStructure)

        self.retranslateUi(ReportSMPDockList)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), ReportSMPDockList.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), ReportSMPDockList.reject)
        QtCore.QMetaObject.connectSlotsByName(ReportSMPDockList)
        ReportSMPDockList.setTabOrder(self.edtBegDate, self.edtEndDate)
        ReportSMPDockList.setTabOrder(self.edtEndDate, self.buttonBox)

    def retranslateUi(self, ReportSMPDockList):
        ReportSMPDockList.setWindowTitle(_translate("ReportSMPDockList", "Отчёт о количестве вызовов СМП/НМП", None))
        self.lblBegDate.setText(_translate("ReportSMPDockList", "Дата &начала периода", None))
        self.lblEndDate.setText(_translate("ReportSMPDockList", "Дата &окончания периода", None))
        self.lblOrgStructure.setText(_translate("ReportSMPDockList", "&Подразделение", None))
        self.chb03.setText(_translate("ReportSMPDockList", "03", None))
        self.chbDoctorCome.setText(_translate("ReportSMPDockList", "СМП (Актив.)", None))
        self.chbNMP.setText(_translate("ReportSMPDockList", "НМП", None))
        self.chbShowEventName.setText(_translate("ReportSMPDockList", "Статус вызова", None))
        self.chbShowCallOccasion.setText(_translate("ReportSMPDockList", "Повод к вызову", None))
        self.lblShow.setText(_translate("ReportSMPDockList", "Отображать", None))
        self.chbShowDiseaseBasic.setText(_translate("ReportSMPDockList", "Основной диагноз", None))
        self.chbShowComplaints.setText(_translate("ReportSMPDockList", "Жалобы", None))
        self.lblAge.setText(_translate("ReportSMPDockList", "Возраст", None))
        self.cmbAgeGroup.setItemText(0, _translate("ReportSMPDockList", "Все", None))
        self.cmbAgeGroup.setItemText(1, _translate("ReportSMPDockList", "Дети (0-17)", None))
        self.cmbAgeGroup.setItemText(2, _translate("ReportSMPDockList", "Взрослые (18 и старше)", None))

from library.DateEdit import CDateEdit
from Orgs.OrgStructComboBoxes import COrgStructureComboBox
