# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\projects\samson\UP_s11\client\Reports\DiagnosisDispansPlanedList.ui'
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

class Ui_DiagnosisDispansPlanedListDialog(object):
    def setupUi(self, DiagnosisDispansPlanedListDialog):
        DiagnosisDispansPlanedListDialog.setObjectName(_fromUtf8("DiagnosisDispansPlanedListDialog"))
        DiagnosisDispansPlanedListDialog.resize(398, 273)
        self.gridLayout = QtGui.QGridLayout(DiagnosisDispansPlanedListDialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.lblBegDate = QtGui.QLabel(DiagnosisDispansPlanedListDialog)
        self.lblBegDate.setObjectName(_fromUtf8("lblBegDate"))
        self.horizontalLayout.addWidget(self.lblBegDate)
        self.edtBegDate = CDateEdit(DiagnosisDispansPlanedListDialog)
        self.edtBegDate.setObjectName(_fromUtf8("edtBegDate"))
        self.horizontalLayout.addWidget(self.edtBegDate)
        self.lblEndDate = QtGui.QLabel(DiagnosisDispansPlanedListDialog)
        self.lblEndDate.setObjectName(_fromUtf8("lblEndDate"))
        self.horizontalLayout.addWidget(self.lblEndDate)
        self.edtEndDate = CDateEdit(DiagnosisDispansPlanedListDialog)
        self.edtEndDate.setObjectName(_fromUtf8("edtEndDate"))
        self.horizontalLayout.addWidget(self.edtEndDate)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.gridLayout.addLayout(self.horizontalLayout, 0, 0, 1, 3)
        self.cmbSpeciality = CRBComboBox(DiagnosisDispansPlanedListDialog)
        self.cmbSpeciality.setObjectName(_fromUtf8("cmbSpeciality"))
        self.gridLayout.addWidget(self.cmbSpeciality, 2, 1, 1, 2)
        self.lblOrgStructure = QtGui.QLabel(DiagnosisDispansPlanedListDialog)
        self.lblOrgStructure.setObjectName(_fromUtf8("lblOrgStructure"))
        self.gridLayout.addWidget(self.lblOrgStructure, 1, 0, 1, 1)
        self.label_4 = QtGui.QLabel(DiagnosisDispansPlanedListDialog)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.gridLayout.addWidget(self.label_4, 3, 0, 1, 1)
        self.lblSpeciality = QtGui.QLabel(DiagnosisDispansPlanedListDialog)
        self.lblSpeciality.setObjectName(_fromUtf8("lblSpeciality"))
        self.gridLayout.addWidget(self.lblSpeciality, 2, 0, 1, 1)
        self.cmbOrgStructure = COrgStructureComboBox(DiagnosisDispansPlanedListDialog)
        self.cmbOrgStructure.setObjectName(_fromUtf8("cmbOrgStructure"))
        self.gridLayout.addWidget(self.cmbOrgStructure, 1, 1, 1, 2)
        self.cmbPerson = CPersonComboBoxEx(DiagnosisDispansPlanedListDialog)
        self.cmbPerson.setObjectName(_fromUtf8("cmbPerson"))
        self.gridLayout.addWidget(self.cmbPerson, 3, 1, 1, 2)
        self.lblSocStatusClass = QtGui.QLabel(DiagnosisDispansPlanedListDialog)
        self.lblSocStatusClass.setObjectName(_fromUtf8("lblSocStatusClass"))
        self.gridLayout.addWidget(self.lblSocStatusClass, 5, 0, 1, 2)
        self.cmbSocStatusClass = CSocStatusComboBox(DiagnosisDispansPlanedListDialog)
        self.cmbSocStatusClass.setObjectName(_fromUtf8("cmbSocStatusClass"))
        self.gridLayout.addWidget(self.cmbSocStatusClass, 5, 2, 1, 1)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.lblMKB = QtGui.QLabel(DiagnosisDispansPlanedListDialog)
        self.lblMKB.setObjectName(_fromUtf8("lblMKB"))
        self.horizontalLayout_2.addWidget(self.lblMKB)
        self.cmbMKBFilter = QtGui.QComboBox(DiagnosisDispansPlanedListDialog)
        self.cmbMKBFilter.setObjectName(_fromUtf8("cmbMKBFilter"))
        self.cmbMKBFilter.addItem(_fromUtf8(""))
        self.cmbMKBFilter.addItem(_fromUtf8(""))
        self.horizontalLayout_2.addWidget(self.cmbMKBFilter)
        self.edtMKBFrom = CICDCodeEdit(DiagnosisDispansPlanedListDialog)
        self.edtMKBFrom.setEnabled(False)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.edtMKBFrom.sizePolicy().hasHeightForWidth())
        self.edtMKBFrom.setSizePolicy(sizePolicy)
        self.edtMKBFrom.setMaximumSize(QtCore.QSize(60, 16777215))
        self.edtMKBFrom.setMaxLength(6)
        self.edtMKBFrom.setObjectName(_fromUtf8("edtMKBFrom"))
        self.horizontalLayout_2.addWidget(self.edtMKBFrom)
        self.edtMKBTo = CICDCodeEdit(DiagnosisDispansPlanedListDialog)
        self.edtMKBTo.setEnabled(False)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.edtMKBTo.sizePolicy().hasHeightForWidth())
        self.edtMKBTo.setSizePolicy(sizePolicy)
        self.edtMKBTo.setMaximumSize(QtCore.QSize(60, 16777215))
        self.edtMKBTo.setMaxLength(6)
        self.edtMKBTo.setObjectName(_fromUtf8("edtMKBTo"))
        self.horizontalLayout_2.addWidget(self.edtMKBTo)
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.horizontalLayout_2.setStretch(2, 1)
        self.horizontalLayout_2.setStretch(3, 1)
        self.gridLayout.addLayout(self.horizontalLayout_2, 4, 0, 1, 3)
        self.lblSocStatusType = QtGui.QLabel(DiagnosisDispansPlanedListDialog)
        self.lblSocStatusType.setObjectName(_fromUtf8("lblSocStatusType"))
        self.gridLayout.addWidget(self.lblSocStatusType, 6, 0, 1, 1)
        spacerItem2 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem2, 8, 0, 1, 1)
        self.cmbSocStatusType = CRBComboBox(DiagnosisDispansPlanedListDialog)
        self.cmbSocStatusType.setObjectName(_fromUtf8("cmbSocStatusType"))
        self.gridLayout.addWidget(self.cmbSocStatusType, 6, 2, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(DiagnosisDispansPlanedListDialog)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 9, 2, 1, 1)
        self.lblOrgStructureAttach = QtGui.QLabel(DiagnosisDispansPlanedListDialog)
        self.lblOrgStructureAttach.setObjectName(_fromUtf8("lblOrgStructureAttach"))
        self.gridLayout.addWidget(self.lblOrgStructureAttach, 7, 0, 1, 1)
        self.cmbOrgStructureAttach = CAreaComboBox(DiagnosisDispansPlanedListDialog)
        self.cmbOrgStructureAttach.setObjectName(_fromUtf8("cmbOrgStructureAttach"))
        self.gridLayout.addWidget(self.cmbOrgStructureAttach, 7, 2, 1, 1)
        self.lblOrgStructure.setBuddy(self.cmbOrgStructure)
        self.lblSpeciality.setBuddy(self.cmbSpeciality)
        self.lblSocStatusClass.setBuddy(self.cmbSocStatusClass)
        self.lblMKB.setBuddy(self.cmbMKBFilter)
        self.lblSocStatusType.setBuddy(self.cmbSocStatusType)
        self.lblOrgStructureAttach.setBuddy(self.cmbOrgStructureAttach)

        self.retranslateUi(DiagnosisDispansPlanedListDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), DiagnosisDispansPlanedListDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(DiagnosisDispansPlanedListDialog)

    def retranslateUi(self, DiagnosisDispansPlanedListDialog):
        DiagnosisDispansPlanedListDialog.setWindowTitle(_translate("DiagnosisDispansPlanedListDialog", "Параметры", None))
        self.lblBegDate.setText(_translate("DiagnosisDispansPlanedListDialog", "с", None))
        self.lblEndDate.setText(_translate("DiagnosisDispansPlanedListDialog", "по", None))
        self.cmbSpeciality.setWhatsThis(_translate("DiagnosisDispansPlanedListDialog", "<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"></p></body></html>", None))
        self.lblOrgStructure.setText(_translate("DiagnosisDispansPlanedListDialog", "&Подразделение врача", None))
        self.label_4.setText(_translate("DiagnosisDispansPlanedListDialog", "Врач", None))
        self.lblSpeciality.setText(_translate("DiagnosisDispansPlanedListDialog", "&Специальность", None))
        self.lblSocStatusClass.setText(_translate("DiagnosisDispansPlanedListDialog", "Класс соц.статуса", None))
        self.lblMKB.setText(_translate("DiagnosisDispansPlanedListDialog", "Коды диагнозов по &МКБ", None))
        self.cmbMKBFilter.setItemText(0, _translate("DiagnosisDispansPlanedListDialog", "Игнор.", None))
        self.cmbMKBFilter.setItemText(1, _translate("DiagnosisDispansPlanedListDialog", "Интервал", None))
        self.edtMKBFrom.setInputMask(_translate("DiagnosisDispansPlanedListDialog", "a00.00; ", None))
        self.edtMKBFrom.setText(_translate("DiagnosisDispansPlanedListDialog", "A.", None))
        self.edtMKBTo.setInputMask(_translate("DiagnosisDispansPlanedListDialog", "a00.00; ", None))
        self.edtMKBTo.setText(_translate("DiagnosisDispansPlanedListDialog", "Z99.9", None))
        self.lblSocStatusType.setText(_translate("DiagnosisDispansPlanedListDialog", "Тип соц.статуса", None))
        self.lblOrgStructureAttach.setText(_translate("DiagnosisDispansPlanedListDialog", "Прикрепление к &участку", None))

from Orgs.OrgStructComboBoxes import CAreaComboBox, COrgStructureComboBox
from Orgs.PersonComboBoxEx import CPersonComboBoxEx
from Registry.SocStatusComboBox import CSocStatusComboBox
from library.DateEdit import CDateEdit
from library.ICDCodeEdit import CICDCodeEdit
from library.crbcombobox import CRBComboBox
