# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Projects\Samson\client_test\Events\PropertyEditorAmbCardDialog.ui'
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

class Ui_PropertyEditorAmbCardDialog(object):
    def setupUi(self, PropertyEditorAmbCardDialog):
        PropertyEditorAmbCardDialog.setObjectName(_fromUtf8("PropertyEditorAmbCardDialog"))
        PropertyEditorAmbCardDialog.resize(1022, 712)
        self.gridLayout_3 = QtGui.QGridLayout(PropertyEditorAmbCardDialog)
        self.gridLayout_3.setObjectName(_fromUtf8("gridLayout_3"))
        self.splitter_2 = QtGui.QSplitter(PropertyEditorAmbCardDialog)
        self.splitter_2.setOrientation(QtCore.Qt.Vertical)
        self.splitter_2.setObjectName(_fromUtf8("splitter_2"))
        self.edtPropertyText = QtGui.QTextEdit(self.splitter_2)
        self.edtPropertyText.setObjectName(_fromUtf8("edtPropertyText"))
        self.widget = QtGui.QWidget(self.splitter_2)
        self.widget.setObjectName(_fromUtf8("widget"))
        self.gridLayout_2 = QtGui.QGridLayout(self.widget)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.gbFilters = QtGui.QGroupBox(self.widget)
        self.gbFilters.setObjectName(_fromUtf8("gbFilters"))
        self.gridLayout = QtGui.QGridLayout(self.gbFilters)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.cmbGroup = CActionTypeComboBox(self.gbFilters)
        self.cmbGroup.setMinimumSize(QtCore.QSize(120, 0))
        self.cmbGroup.setObjectName(_fromUtf8("cmbGroup"))
        self.cmbGroup.addItem(_fromUtf8(""))
        self.gridLayout.addWidget(self.cmbGroup, 0, 4, 1, 1)
        self.edtBegDate = CDateEdit(self.gbFilters)
        self.edtBegDate.setCalendarPopup(True)
        self.edtBegDate.setObjectName(_fromUtf8("edtBegDate"))
        self.gridLayout.addWidget(self.edtBegDate, 0, 1, 1, 1)
        self.cmbStatus = CActionStatusComboBox(self.gbFilters)
        self.cmbStatus.setEnabled(True)
        self.cmbStatus.setObjectName(_fromUtf8("cmbStatus"))
        self.gridLayout.addWidget(self.cmbStatus, 2, 4, 1, 1)
        self.chkHasProperties = QtGui.QCheckBox(self.gbFilters)
        self.chkHasProperties.setObjectName(_fromUtf8("chkHasProperties"))
        self.gridLayout.addWidget(self.chkHasProperties, 2, 6, 1, 1)
        self.lblBegDate = QtGui.QLabel(self.gbFilters)
        self.lblBegDate.setObjectName(_fromUtf8("lblBegDate"))
        self.gridLayout.addWidget(self.lblBegDate, 0, 0, 2, 1)
        self.cmbOrgStructure = COrgStructureComboBox(self.gbFilters)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cmbOrgStructure.sizePolicy().hasHeightForWidth())
        self.cmbOrgStructure.setSizePolicy(sizePolicy)
        self.cmbOrgStructure.setMinimumSize(QtCore.QSize(80, 0))
        self.cmbOrgStructure.setObjectName(_fromUtf8("cmbOrgStructure"))
        self.gridLayout.addWidget(self.cmbOrgStructure, 0, 5, 1, 2)
        self.lblEndDate = QtGui.QLabel(self.gbFilters)
        self.lblEndDate.setObjectName(_fromUtf8("lblEndDate"))
        self.gridLayout.addWidget(self.lblEndDate, 0, 2, 2, 1)
        self.chkHasAttachedFiles = QtGui.QCheckBox(self.gbFilters)
        self.chkHasAttachedFiles.setObjectName(_fromUtf8("chkHasAttachedFiles"))
        self.gridLayout.addWidget(self.chkHasAttachedFiles, 2, 5, 1, 1)
        self.cmbSpeciality = CRBComboBox(self.gbFilters)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cmbSpeciality.sizePolicy().hasHeightForWidth())
        self.cmbSpeciality.setSizePolicy(sizePolicy)
        self.cmbSpeciality.setMinimumSize(QtCore.QSize(120, 0))
        self.cmbSpeciality.setObjectName(_fromUtf8("cmbSpeciality"))
        self.cmbSpeciality.addItem(_fromUtf8(""))
        self.gridLayout.addWidget(self.cmbSpeciality, 2, 0, 1, 4)
        self.edtEndDate = CDateEdit(self.gbFilters)
        self.edtEndDate.setCalendarPopup(True)
        self.edtEndDate.setObjectName(_fromUtf8("edtEndDate"))
        self.gridLayout.addWidget(self.edtEndDate, 0, 3, 1, 1)
        self.btnFiltersButtonBox = QtGui.QDialogButtonBox(self.gbFilters)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnFiltersButtonBox.sizePolicy().hasHeightForWidth())
        self.btnFiltersButtonBox.setSizePolicy(sizePolicy)
        self.btnFiltersButtonBox.setOrientation(QtCore.Qt.Horizontal)
        self.btnFiltersButtonBox.setStandardButtons(QtGui.QDialogButtonBox.Apply|QtGui.QDialogButtonBox.Reset)
        self.btnFiltersButtonBox.setObjectName(_fromUtf8("btnFiltersButtonBox"))
        self.gridLayout.addWidget(self.btnFiltersButtonBox, 1, 8, 2, 1)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 2, 7, 1, 1)
        self.gridLayout_2.addWidget(self.gbFilters, 0, 0, 1, 1)
        self.splitter = QtGui.QSplitter(self.widget)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName(_fromUtf8("splitter"))
        self.tblActions = CRegistryActionsTableView(self.splitter)
        self.tblActions.setObjectName(_fromUtf8("tblActions"))
        self.tblActionProperties = CF088ActionPropertiesTableView(self.splitter)
        self.tblActionProperties.setObjectName(_fromUtf8("tblActionProperties"))
        self.gridLayout_2.addWidget(self.splitter, 1, 0, 1, 1)
        self.gridLayout_2.setRowStretch(1, 5)
        self.gridLayout_3.addWidget(self.splitter_2, 0, 0, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(PropertyEditorAmbCardDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout_3.addWidget(self.buttonBox, 1, 0, 1, 1)

        self.retranslateUi(PropertyEditorAmbCardDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), PropertyEditorAmbCardDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), PropertyEditorAmbCardDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(PropertyEditorAmbCardDialog)

    def retranslateUi(self, PropertyEditorAmbCardDialog):
        PropertyEditorAmbCardDialog.setWindowTitle(_translate("PropertyEditorAmbCardDialog", "Dialog", None))
        self.gbFilters.setTitle(_translate("PropertyEditorAmbCardDialog", "Фильтр", None))
        self.cmbGroup.setItemText(0, _translate("PropertyEditorAmbCardDialog", "Тип (группа?)", None))
        self.chkHasProperties.setText(_translate("PropertyEditorAmbCardDialog", "Имеет свойства", None))
        self.lblBegDate.setText(_translate("PropertyEditorAmbCardDialog", "Начат с", None))
        self.lblEndDate.setText(_translate("PropertyEditorAmbCardDialog", "По", None))
        self.chkHasAttachedFiles.setText(_translate("PropertyEditorAmbCardDialog", "Имеет прикрепленные файлы", None))
        self.cmbSpeciality.setItemText(0, _translate("PropertyEditorAmbCardDialog", "Специальность", None))

from Events.ActionStatus import CActionStatusComboBox
from Events.ActionTypeComboBox import CActionTypeComboBox
from F088.F088ActionPropertiesCheckTable import CF088ActionPropertiesTableView
from Orgs.OrgStructComboBoxes import COrgStructureComboBox
from Registry.RegistryTable import CRegistryActionsTableView
from library.DateEdit import CDateEdit
from library.crbcombobox import CRBComboBox
