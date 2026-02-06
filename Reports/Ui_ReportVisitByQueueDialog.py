# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\projects\Samson\UP_s11\client_kortis\Reports\ReportVisitByQueueDialog.ui'
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

class Ui_ReportVisitByQueueDialog(object):
    def setupUi(self, ReportVisitByQueueDialog):
        ReportVisitByQueueDialog.setObjectName(_fromUtf8("ReportVisitByQueueDialog"))
        ReportVisitByQueueDialog.resize(497, 262)
        self.gridLayout = QtGui.QGridLayout(ReportVisitByQueueDialog)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.chkTakeAccountVisitToOtherDoctor = QtGui.QCheckBox(ReportVisitByQueueDialog)
        self.chkTakeAccountVisitToOtherDoctor.setObjectName(_fromUtf8("chkTakeAccountVisitToOtherDoctor"))
        self.gridLayout.addWidget(self.chkTakeAccountVisitToOtherDoctor, 5, 1, 1, 4)
        self.label_5 = QtGui.QLabel(ReportVisitByQueueDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_5.sizePolicy().hasHeightForWidth())
        self.label_5.setSizePolicy(sizePolicy)
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.gridLayout.addWidget(self.label_5, 3, 0, 1, 1)
        self.lblOrgStructure = QtGui.QLabel(ReportVisitByQueueDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblOrgStructure.sizePolicy().hasHeightForWidth())
        self.lblOrgStructure.setSizePolicy(sizePolicy)
        self.lblOrgStructure.setObjectName(_fromUtf8("lblOrgStructure"))
        self.gridLayout.addWidget(self.lblOrgStructure, 1, 0, 1, 1)
        self.cmbOrgStructure = COrgStructureComboBox(ReportVisitByQueueDialog)
        self.cmbOrgStructure.setObjectName(_fromUtf8("cmbOrgStructure"))
        self.gridLayout.addWidget(self.cmbOrgStructure, 1, 1, 1, 4)
        self.lblSpeciality = QtGui.QLabel(ReportVisitByQueueDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblSpeciality.sizePolicy().hasHeightForWidth())
        self.lblSpeciality.setSizePolicy(sizePolicy)
        self.lblSpeciality.setObjectName(_fromUtf8("lblSpeciality"))
        self.gridLayout.addWidget(self.lblSpeciality, 2, 0, 1, 1)
        self.lblOrder = QtGui.QLabel(ReportVisitByQueueDialog)
        self.lblOrder.setObjectName(_fromUtf8("lblOrder"))
        self.gridLayout.addWidget(self.lblOrder, 8, 0, 1, 1)
        self.cmbSpeciality = CRBComboBox(ReportVisitByQueueDialog)
        self.cmbSpeciality.setObjectName(_fromUtf8("cmbSpeciality"))
        self.gridLayout.addWidget(self.cmbSpeciality, 2, 1, 1, 4)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 9, 0, 1, 1)
        self.chkNoteVisibled = QtGui.QCheckBox(ReportVisitByQueueDialog)
        self.chkNoteVisibled.setObjectName(_fromUtf8("chkNoteVisibled"))
        self.gridLayout.addWidget(self.chkNoteVisibled, 6, 1, 1, 4)
        self.lblBegScheduleDate = QtGui.QLabel(ReportVisitByQueueDialog)
        self.lblBegScheduleDate.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.lblBegScheduleDate.setObjectName(_fromUtf8("lblBegScheduleDate"))
        self.gridLayout.addWidget(self.lblBegScheduleDate, 0, 0, 1, 1)
        self.edtEndScheduleDate = CDateEdit(ReportVisitByQueueDialog)
        self.edtEndScheduleDate.setCalendarPopup(True)
        self.edtEndScheduleDate.setObjectName(_fromUtf8("edtEndScheduleDate"))
        self.gridLayout.addWidget(self.edtEndScheduleDate, 0, 3, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(ReportVisitByQueueDialog)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 10, 0, 1, 5)
        self.cmbPerson = CPersonComboBoxEx(ReportVisitByQueueDialog)
        self.cmbPerson.setObjectName(_fromUtf8("cmbPerson"))
        self.gridLayout.addWidget(self.cmbPerson, 3, 1, 1, 4)
        self.cmbOrder = QtGui.QComboBox(ReportVisitByQueueDialog)
        self.cmbOrder.setObjectName(_fromUtf8("cmbOrder"))
        self.cmbOrder.addItem(_fromUtf8(""))
        self.cmbOrder.addItem(_fromUtf8(""))
        self.cmbOrder.addItem(_fromUtf8(""))
        self.gridLayout.addWidget(self.cmbOrder, 8, 1, 1, 4)
        self.lblEndScheduleDate = QtGui.QLabel(ReportVisitByQueueDialog)
        self.lblEndScheduleDate.setAlignment(QtCore.Qt.AlignCenter)
        self.lblEndScheduleDate.setObjectName(_fromUtf8("lblEndScheduleDate"))
        self.gridLayout.addWidget(self.lblEndScheduleDate, 0, 2, 1, 1)
        spacerItem1 = QtGui.QSpacerItem(152, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem1, 0, 4, 1, 1)
        self.edtBegScheduleDate = CDateEdit(ReportVisitByQueueDialog)
        self.edtBegScheduleDate.setCalendarPopup(True)
        self.edtBegScheduleDate.setObjectName(_fromUtf8("edtBegScheduleDate"))
        self.gridLayout.addWidget(self.edtBegScheduleDate, 0, 1, 1, 1)
        self.chkListOnlyWithoutVisit = QtGui.QCheckBox(ReportVisitByQueueDialog)
        self.chkListOnlyWithoutVisit.setObjectName(_fromUtf8("chkListOnlyWithoutVisit"))
        self.gridLayout.addWidget(self.chkListOnlyWithoutVisit, 4, 1, 1, 4)
        self.chkPersonVisibled = QtGui.QCheckBox(ReportVisitByQueueDialog)
        self.chkPersonVisibled.setObjectName(_fromUtf8("chkPersonVisibled"))
        self.gridLayout.addWidget(self.chkPersonVisibled, 7, 1, 1, 1)
        self.label_5.setBuddy(self.cmbPerson)
        self.lblOrgStructure.setBuddy(self.cmbOrgStructure)
        self.lblSpeciality.setBuddy(self.cmbSpeciality)

        self.retranslateUi(ReportVisitByQueueDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), ReportVisitByQueueDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), ReportVisitByQueueDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(ReportVisitByQueueDialog)
        ReportVisitByQueueDialog.setTabOrder(self.edtBegScheduleDate, self.edtEndScheduleDate)
        ReportVisitByQueueDialog.setTabOrder(self.edtEndScheduleDate, self.cmbOrgStructure)
        ReportVisitByQueueDialog.setTabOrder(self.cmbOrgStructure, self.cmbSpeciality)
        ReportVisitByQueueDialog.setTabOrder(self.cmbSpeciality, self.cmbPerson)
        ReportVisitByQueueDialog.setTabOrder(self.cmbPerson, self.chkListOnlyWithoutVisit)
        ReportVisitByQueueDialog.setTabOrder(self.chkListOnlyWithoutVisit, self.chkTakeAccountVisitToOtherDoctor)
        ReportVisitByQueueDialog.setTabOrder(self.chkTakeAccountVisitToOtherDoctor, self.chkNoteVisibled)
        ReportVisitByQueueDialog.setTabOrder(self.chkNoteVisibled, self.cmbOrder)
        ReportVisitByQueueDialog.setTabOrder(self.cmbOrder, self.buttonBox)

    def retranslateUi(self, ReportVisitByQueueDialog):
        ReportVisitByQueueDialog.setWindowTitle(_translate("ReportVisitByQueueDialog", "dialog", None))
        self.chkTakeAccountVisitToOtherDoctor.setText(_translate("ReportVisitByQueueDialog", "Учитывать явившихся к другому врачу данной специальности", None))
        self.label_5.setText(_translate("ReportVisitByQueueDialog", "&Врач", None))
        self.lblOrgStructure.setText(_translate("ReportVisitByQueueDialog", "&Подразделение", None))
        self.lblSpeciality.setText(_translate("ReportVisitByQueueDialog", "&Специальность", None))
        self.lblOrder.setText(_translate("ReportVisitByQueueDialog", "Сортировка", None))
        self.chkNoteVisibled.setText(_translate("ReportVisitByQueueDialog", "Отображать Примечания", None))
        self.lblBegScheduleDate.setText(_translate("ReportVisitByQueueDialog", "Период с", None))
        self.edtEndScheduleDate.setDisplayFormat(_translate("ReportVisitByQueueDialog", "dd.MM.yyyy", None))
        self.cmbOrder.setItemText(0, _translate("ReportVisitByQueueDialog", "по дате", None))
        self.cmbOrder.setItemText(1, _translate("ReportVisitByQueueDialog", "по ФИО пациента", None))
        self.cmbOrder.setItemText(2, _translate("ReportVisitByQueueDialog", "по идентификатору пациента", None))
        self.lblEndScheduleDate.setText(_translate("ReportVisitByQueueDialog", "по", None))
        self.edtBegScheduleDate.setDisplayFormat(_translate("ReportVisitByQueueDialog", "dd.MM.yyyy", None))
        self.chkListOnlyWithoutVisit.setText(_translate("ReportVisitByQueueDialog", "Учитывать только не явившихся на прием", None))
        self.chkPersonVisibled.setText(_translate("ReportVisitByQueueDialog", "Отображать врача", None))

from Orgs.OrgStructComboBoxes import COrgStructureComboBox
from Orgs.PersonComboBoxEx import CPersonComboBoxEx
from library.DateEdit import CDateEdit
from library.crbcombobox import CRBComboBox
