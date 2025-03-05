# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\projects\samson\UP_s11\client_pre_release\RefBooks\ActionTypeGroup\RBActionTypeGroupEditor.ui'
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

class Ui_ActionTypeGroupEditorDialog(object):
    def setupUi(self, ActionTypeGroupEditorDialog):
        ActionTypeGroupEditorDialog.setObjectName(_fromUtf8("ActionTypeGroupEditorDialog"))
        ActionTypeGroupEditorDialog.resize(548, 381)
        self.verticalLayout = QtGui.QVBoxLayout(ActionTypeGroupEditorDialog)
        self.verticalLayout.setMargin(4)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.formLayout = QtGui.QFormLayout()
        self.formLayout.setFieldGrowthPolicy(QtGui.QFormLayout.ExpandingFieldsGrow)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.lblGroupCode = QtGui.QLabel(ActionTypeGroupEditorDialog)
        self.lblGroupCode.setObjectName(_fromUtf8("lblGroupCode"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.lblGroupCode)
        self.edtGroupCode = QtGui.QLineEdit(ActionTypeGroupEditorDialog)
        self.edtGroupCode.setObjectName(_fromUtf8("edtGroupCode"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.edtGroupCode)
        self.lblGroupName = QtGui.QLabel(ActionTypeGroupEditorDialog)
        self.lblGroupName.setObjectName(_fromUtf8("lblGroupName"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.lblGroupName)
        self.edtGroupName = QtGui.QLineEdit(ActionTypeGroupEditorDialog)
        self.edtGroupName.setObjectName(_fromUtf8("edtGroupName"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.edtGroupName)
        self.lblGroupAvailability = QtGui.QLabel(ActionTypeGroupEditorDialog)
        self.lblGroupAvailability.setObjectName(_fromUtf8("lblGroupAvailability"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.lblGroupAvailability)
        self.cmbAvailability = QtGui.QComboBox(ActionTypeGroupEditorDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cmbAvailability.sizePolicy().hasHeightForWidth())
        self.cmbAvailability.setSizePolicy(sizePolicy)
        self.cmbAvailability.setObjectName(_fromUtf8("cmbAvailability"))
        self.cmbAvailability.addItem(_fromUtf8(""))
        self.cmbAvailability.addItem(_fromUtf8(""))
        self.cmbAvailability.addItem(_fromUtf8(""))
        self.formLayout.setWidget(2, QtGui.QFormLayout.FieldRole, self.cmbAvailability)
        self.lblEnableOffset = QtGui.QLabel(ActionTypeGroupEditorDialog)
        self.lblEnableOffset.setObjectName(_fromUtf8("lblEnableOffset"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.LabelRole, self.lblEnableOffset)
        self.chkEnableOffset = QtGui.QCheckBox(ActionTypeGroupEditorDialog)
        self.chkEnableOffset.setText(_fromUtf8(""))
        self.chkEnableOffset.setObjectName(_fromUtf8("chkEnableOffset"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.FieldRole, self.chkEnableOffset)
        self.verticalLayout.addLayout(self.formLayout)
        self.lblGroupName_3 = QtGui.QLabel(ActionTypeGroupEditorDialog)
        self.lblGroupName_3.setObjectName(_fromUtf8("lblGroupName_3"))
        self.verticalLayout.addWidget(self.lblGroupName_3)
        self.tblActionTypes = CInDocTableView(ActionTypeGroupEditorDialog)
        self.tblActionTypes.setObjectName(_fromUtf8("tblActionTypes"))
        self.verticalLayout.addWidget(self.tblActionTypes)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.btnAddActions = QtGui.QPushButton(ActionTypeGroupEditorDialog)
        self.btnAddActions.setObjectName(_fromUtf8("btnAddActions"))
        self.horizontalLayout.addWidget(self.btnAddActions)
        self.btnDelActions = QtGui.QPushButton(ActionTypeGroupEditorDialog)
        self.btnDelActions.setObjectName(_fromUtf8("btnDelActions"))
        self.horizontalLayout.addWidget(self.btnDelActions)
        self.buttonBox = QtGui.QDialogButtonBox(ActionTypeGroupEditorDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.horizontalLayout.addWidget(self.buttonBox)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.lblGroupCode.setBuddy(self.edtGroupCode)
        self.lblGroupName.setBuddy(self.edtGroupName)
        self.lblGroupAvailability.setBuddy(self.cmbAvailability)
        self.lblEnableOffset.setBuddy(self.chkEnableOffset)
        self.lblGroupName_3.setBuddy(self.tblActionTypes)

        self.retranslateUi(ActionTypeGroupEditorDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), ActionTypeGroupEditorDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), ActionTypeGroupEditorDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(ActionTypeGroupEditorDialog)

    def retranslateUi(self, ActionTypeGroupEditorDialog):
        ActionTypeGroupEditorDialog.setWindowTitle(_translate("ActionTypeGroupEditorDialog", "Редактирование шаблона назначения действий", None))
        self.lblGroupCode.setText(_translate("ActionTypeGroupEditorDialog", "Код", None))
        self.lblGroupName.setText(_translate("ActionTypeGroupEditorDialog", "Наименование", None))
        self.lblGroupAvailability.setText(_translate("ActionTypeGroupEditorDialog", "Доступность", None))
        self.cmbAvailability.setItemText(0, _translate("ActionTypeGroupEditorDialog", "Всем", None))
        self.cmbAvailability.setItemText(1, _translate("ActionTypeGroupEditorDialog", "По специальности", None))
        self.cmbAvailability.setItemText(2, _translate("ActionTypeGroupEditorDialog", "Владельцу", None))
        self.lblEnableOffset.setText(_translate("ActionTypeGroupEditorDialog", "Учитывать хронологию", None))
        self.lblGroupName_3.setText(_translate("ActionTypeGroupEditorDialog", "Выбранные типы действий", None))
        self.btnAddActions.setText(_translate("ActionTypeGroupEditorDialog", "Добавить действия", None))
        self.btnDelActions.setText(_translate("ActionTypeGroupEditorDialog", "Удалить действия", None))

from library.InDocTable import CInDocTableView
