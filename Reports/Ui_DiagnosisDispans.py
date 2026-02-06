# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Projects\Samson\client_test\Reports\DiagnosisDispans.ui'
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

class Ui_DiagnosisDispansDialog(object):
    def setupUi(self, DiagnosisDispansDialog):
        DiagnosisDispansDialog.setObjectName(_fromUtf8("DiagnosisDispansDialog"))
        DiagnosisDispansDialog.resize(381, 269)
        self.gridLayout = QtGui.QGridLayout(DiagnosisDispansDialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.lblDate = QtGui.QLabel(DiagnosisDispansDialog)
        self.lblDate.setObjectName(_fromUtf8("lblDate"))
        self.gridLayout.addWidget(self.lblDate, 0, 0, 1, 1)
        self.edtDate = CDateEdit(DiagnosisDispansDialog)
        self.edtDate.setObjectName(_fromUtf8("edtDate"))
        self.gridLayout.addWidget(self.edtDate, 0, 1, 1, 1)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 0, 2, 1, 1)
        self.lblOrgStructure = QtGui.QLabel(DiagnosisDispansDialog)
        self.lblOrgStructure.setObjectName(_fromUtf8("lblOrgStructure"))
        self.gridLayout.addWidget(self.lblOrgStructure, 1, 0, 1, 1)
        self.cmbOrgStructure = COrgStructureComboBox(DiagnosisDispansDialog)
        self.cmbOrgStructure.setObjectName(_fromUtf8("cmbOrgStructure"))
        self.gridLayout.addWidget(self.cmbOrgStructure, 1, 1, 1, 2)
        self.lblSpeciality = QtGui.QLabel(DiagnosisDispansDialog)
        self.lblSpeciality.setObjectName(_fromUtf8("lblSpeciality"))
        self.gridLayout.addWidget(self.lblSpeciality, 2, 0, 2, 2)
        self.cmbSpeciality = CRBComboBox(DiagnosisDispansDialog)
        self.cmbSpeciality.setObjectName(_fromUtf8("cmbSpeciality"))
        self.gridLayout.addWidget(self.cmbSpeciality, 3, 1, 1, 2)
        self.label_4 = QtGui.QLabel(DiagnosisDispansDialog)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.gridLayout.addWidget(self.label_4, 4, 0, 1, 1)
        self.cmbPerson = CPersonComboBoxEx(DiagnosisDispansDialog)
        self.cmbPerson.setObjectName(_fromUtf8("cmbPerson"))
        self.gridLayout.addWidget(self.cmbPerson, 4, 1, 1, 2)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.lblMKB = QtGui.QLabel(DiagnosisDispansDialog)
        self.lblMKB.setObjectName(_fromUtf8("lblMKB"))
        self.horizontalLayout_2.addWidget(self.lblMKB)
        self.cmbMKBFilter = QtGui.QComboBox(DiagnosisDispansDialog)
        self.cmbMKBFilter.setObjectName(_fromUtf8("cmbMKBFilter"))
        self.cmbMKBFilter.addItem(_fromUtf8(""))
        self.cmbMKBFilter.addItem(_fromUtf8(""))
        self.horizontalLayout_2.addWidget(self.cmbMKBFilter)
        self.edtMKBFrom = CICDCodeEdit(DiagnosisDispansDialog)
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
        self.edtMKBTo = CICDCodeEdit(DiagnosisDispansDialog)
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
        self.gridLayout.addLayout(self.horizontalLayout_2, 5, 0, 1, 3)
        self.lblSocStatusClass = QtGui.QLabel(DiagnosisDispansDialog)
        self.lblSocStatusClass.setObjectName(_fromUtf8("lblSocStatusClass"))
        self.gridLayout.addWidget(self.lblSocStatusClass, 6, 0, 1, 1)
        self.cmbSocStatusClass = CSocStatusComboBox(DiagnosisDispansDialog)
        self.cmbSocStatusClass.setObjectName(_fromUtf8("cmbSocStatusClass"))
        self.gridLayout.addWidget(self.cmbSocStatusClass, 6, 1, 1, 2)
        self.lblSocStatusType = QtGui.QLabel(DiagnosisDispansDialog)
        self.lblSocStatusType.setObjectName(_fromUtf8("lblSocStatusType"))
        self.gridLayout.addWidget(self.lblSocStatusType, 7, 0, 1, 1)
        self.cmbSocStatusType = CRBComboBox(DiagnosisDispansDialog)
        self.cmbSocStatusType.setObjectName(_fromUtf8("cmbSocStatusType"))
        self.gridLayout.addWidget(self.cmbSocStatusType, 7, 1, 1, 2)
        self.lblOrgStructureAttach = QtGui.QLabel(DiagnosisDispansDialog)
        self.lblOrgStructureAttach.setObjectName(_fromUtf8("lblOrgStructureAttach"))
        self.gridLayout.addWidget(self.lblOrgStructureAttach, 8, 0, 1, 1)
        spacerItem2 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem2, 9, 0, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(DiagnosisDispansDialog)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 10, 1, 1, 1)
        self.cmbOrgStructureAttach = CAreaComboBox(DiagnosisDispansDialog)
        self.cmbOrgStructureAttach.setObjectName(_fromUtf8("cmbOrgStructureAttach"))
        self.gridLayout.addWidget(self.cmbOrgStructureAttach, 8, 1, 1, 2)
        self.lblOrgStructure.setBuddy(self.cmbOrgStructure)
        self.lblSpeciality.setBuddy(self.cmbSpeciality)
        self.lblMKB.setBuddy(self.cmbMKBFilter)
        self.lblSocStatusClass.setBuddy(self.cmbSocStatusClass)
        self.lblSocStatusType.setBuddy(self.cmbSocStatusType)
        self.lblOrgStructureAttach.setBuddy(self.cmbOrgStructureAttach)

        self.retranslateUi(DiagnosisDispansDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), DiagnosisDispansDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(DiagnosisDispansDialog)

    def retranslateUi(self, DiagnosisDispansDialog):
        DiagnosisDispansDialog.setWindowTitle(_translate("DiagnosisDispansDialog", "Параметры", None))
        self.lblDate.setText(_translate("DiagnosisDispansDialog", "На дату", None))
        self.lblOrgStructure.setText(_translate("DiagnosisDispansDialog", "&Подразделение", None))
        self.lblSpeciality.setText(_translate("DiagnosisDispansDialog", "&Специальность", None))
        self.cmbSpeciality.setWhatsThis(_translate("DiagnosisDispansDialog", "<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"></p></body></html>", None))
        self.label_4.setText(_translate("DiagnosisDispansDialog", "Врач", None))
        self.lblMKB.setText(_translate("DiagnosisDispansDialog", "Коды диагнозов по &МКБ", None))
        self.cmbMKBFilter.setItemText(0, _translate("DiagnosisDispansDialog", "Игнор.", None))
        self.cmbMKBFilter.setItemText(1, _translate("DiagnosisDispansDialog", "Интервал", None))
        self.edtMKBFrom.setInputMask(_translate("DiagnosisDispansDialog", "a00.00", None))
        self.edtMKBFrom.setText(_translate("DiagnosisDispansDialog", "A.", None))
        self.edtMKBTo.setInputMask(_translate("DiagnosisDispansDialog", "a00.00", None))
        self.edtMKBTo.setText(_translate("DiagnosisDispansDialog", "Z99.9", None))
        self.lblSocStatusClass.setText(_translate("DiagnosisDispansDialog", "Класс соц.статуса", None))
        self.lblSocStatusType.setText(_translate("DiagnosisDispansDialog", "Тип соц.статуса", None))
        self.lblOrgStructureAttach.setText(_translate("DiagnosisDispansDialog", "Прикрепление к &участку", None))

from Orgs.OrgStructComboBoxes import CAreaComboBox, COrgStructureComboBox
from Orgs.PersonComboBoxEx import CPersonComboBoxEx
from Registry.SocStatusComboBox import CSocStatusComboBox
from library.DateEdit import CDateEdit
from library.ICDCodeEdit import CICDCodeEdit
from library.crbcombobox import CRBComboBox
