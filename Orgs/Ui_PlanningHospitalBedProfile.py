# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Samson\UP_s11\client_test\Orgs\PlanningHospitalBedProfile.ui'
#
# Created: Thu Jan 25 13:15:23 2024
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

class Ui_PlanningHospitalBedProfileDialog(object):
    def setupUi(self, PlanningHospitalBedProfileDialog):
        PlanningHospitalBedProfileDialog.setObjectName(_fromUtf8("PlanningHospitalBedProfileDialog"))
        PlanningHospitalBedProfileDialog.resize(606, 590)
        self.gridLayout = QtGui.QGridLayout(PlanningHospitalBedProfileDialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.chkDate = QtGui.QCheckBox(PlanningHospitalBedProfileDialog)
        self.chkDate.setChecked(True)
        self.chkDate.setObjectName(_fromUtf8("chkDate"))
        self.horizontalLayout.addWidget(self.chkDate)
        self.edtBegDate = CDateEdit(PlanningHospitalBedProfileDialog)
        self.edtBegDate.setObjectName(_fromUtf8("edtBegDate"))
        self.horizontalLayout.addWidget(self.edtBegDate)
        self.label_2 = QtGui.QLabel(PlanningHospitalBedProfileDialog)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.horizontalLayout.addWidget(self.label_2)
        self.edtEndDate = CDateEdit(PlanningHospitalBedProfileDialog)
        self.edtEndDate.setObjectName(_fromUtf8("edtEndDate"))
        self.horizontalLayout.addWidget(self.edtEndDate)
        self.gridLayout.addLayout(self.horizontalLayout, 0, 0, 1, 2)
        self.chkOrgStructure = QtGui.QCheckBox(PlanningHospitalBedProfileDialog)
        self.chkOrgStructure.setObjectName(_fromUtf8("chkOrgStructure"))
        self.gridLayout.addWidget(self.chkOrgStructure, 1, 0, 1, 1)
        self.chkProfileBed = QtGui.QCheckBox(PlanningHospitalBedProfileDialog)
        self.chkProfileBed.setObjectName(_fromUtf8("chkProfileBed"))
        self.gridLayout.addWidget(self.chkProfileBed, 2, 0, 1, 1)
        self.btnFill = QtGui.QPushButton(PlanningHospitalBedProfileDialog)
        self.btnFill.setObjectName(_fromUtf8("btnFill"))
        self.gridLayout.addWidget(self.btnFill, 3, 0, 1, 2)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 5, 2, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(PlanningHospitalBedProfileDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Apply|QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 5, 3, 1, 1)
        self.tblItems = CInDocTableView(PlanningHospitalBedProfileDialog)
        self.tblItems.setObjectName(_fromUtf8("tblItems"))
        self.gridLayout.addWidget(self.tblItems, 4, 0, 1, 4)
        self.cmbOrgStructure = COrgStructureHospitalBedsComboBox(PlanningHospitalBedProfileDialog)
        self.cmbOrgStructure.setEnabled(False)
        self.cmbOrgStructure.setObjectName(_fromUtf8("cmbOrgStructure"))
        self.gridLayout.addWidget(self.cmbOrgStructure, 1, 1, 1, 3)
        self.cmbHospitalBedProfile = CRBComboBox(PlanningHospitalBedProfileDialog)
        self.cmbHospitalBedProfile.setEnabled(False)
        self.cmbHospitalBedProfile.setObjectName(_fromUtf8("cmbHospitalBedProfile"))
        self.gridLayout.addWidget(self.cmbHospitalBedProfile, 2, 1, 1, 3)

        self.retranslateUi(PlanningHospitalBedProfileDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), PlanningHospitalBedProfileDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), PlanningHospitalBedProfileDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(PlanningHospitalBedProfileDialog)
        PlanningHospitalBedProfileDialog.setTabOrder(self.chkDate, self.chkOrgStructure)
        PlanningHospitalBedProfileDialog.setTabOrder(self.chkOrgStructure, self.cmbOrgStructure)
        PlanningHospitalBedProfileDialog.setTabOrder(self.cmbOrgStructure, self.chkProfileBed)
        PlanningHospitalBedProfileDialog.setTabOrder(self.chkProfileBed, self.cmbHospitalBedProfile)
        PlanningHospitalBedProfileDialog.setTabOrder(self.cmbHospitalBedProfile, self.tblItems)

    def retranslateUi(self, PlanningHospitalBedProfileDialog):
        PlanningHospitalBedProfileDialog.setWindowTitle(_translate("PlanningHospitalBedProfileDialog", "Планирование загруженности коечного фонда", None))
        self.chkDate.setText(_translate("PlanningHospitalBedProfileDialog", "Период с", None))
        self.label_2.setText(_translate("PlanningHospitalBedProfileDialog", "по", None))
        self.chkOrgStructure.setText(_translate("PlanningHospitalBedProfileDialog", "Подразделение", None))
        self.chkProfileBed.setText(_translate("PlanningHospitalBedProfileDialog", "Профиль койки", None))
        self.btnFill.setText(_translate("PlanningHospitalBedProfileDialog", "Сгенерировать список подразделений", None))

from library.InDocTable import CInDocTableView
from library.crbcombobox import CRBComboBox
from OrgStructComboBoxes import COrgStructureHospitalBedsComboBox
from library.DateEdit import CDateEdit
