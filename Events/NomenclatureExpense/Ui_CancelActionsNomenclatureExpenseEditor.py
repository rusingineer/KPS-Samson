# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\stock2\Events\NomenclatureExpense\CancelActionsNomenclatureExpenseEditor.ui'
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

class Ui_CancelActionsNomenclatureExpenseEditor(object):
    def setupUi(self, CancelActionsNomenclatureExpenseEditor):
        CancelActionsNomenclatureExpenseEditor.setObjectName(_fromUtf8("CancelActionsNomenclatureExpenseEditor"))
        CancelActionsNomenclatureExpenseEditor.resize(505, 212)
        self.gridLayout = QtGui.QGridLayout(CancelActionsNomenclatureExpenseEditor)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.lblNomenclatureActiveSubstance = QtGui.QLabel(CancelActionsNomenclatureExpenseEditor)
        self.lblNomenclatureActiveSubstance.setObjectName(_fromUtf8("lblNomenclatureActiveSubstance"))
        self.gridLayout.addWidget(self.lblNomenclatureActiveSubstance, 4, 0, 1, 1)
        self.lblPower = QtGui.QLabel(CancelActionsNomenclatureExpenseEditor)
        self.lblPower.setObjectName(_fromUtf8("lblPower"))
        self.gridLayout.addWidget(self.lblPower, 7, 0, 1, 1)
        self.edtCancelDate = CDateEdit(CancelActionsNomenclatureExpenseEditor)
        self.edtCancelDate.setCalendarPopup(False)
        self.edtCancelDate.setObjectName(_fromUtf8("edtCancelDate"))
        self.gridLayout.addWidget(self.edtCancelDate, 1, 1, 1, 1)
        self.lblNotes = QtGui.QLabel(CancelActionsNomenclatureExpenseEditor)
        self.lblNotes.setObjectName(_fromUtf8("lblNotes"))
        self.gridLayout.addWidget(self.lblNotes, 8, 0, 1, 1)
        self.lblReactionManifestation = QtGui.QLabel(CancelActionsNomenclatureExpenseEditor)
        self.lblReactionManifestation.setObjectName(_fromUtf8("lblReactionManifestation"))
        self.gridLayout.addWidget(self.lblReactionManifestation, 6, 0, 1, 1)
        self.lblReactionType = QtGui.QLabel(CancelActionsNomenclatureExpenseEditor)
        self.lblReactionType.setObjectName(_fromUtf8("lblReactionType"))
        self.gridLayout.addWidget(self.lblReactionType, 5, 0, 1, 1)
        self.lblCancelDate = QtGui.QLabel(CancelActionsNomenclatureExpenseEditor)
        self.lblCancelDate.setObjectName(_fromUtf8("lblCancelDate"))
        self.gridLayout.addWidget(self.lblCancelDate, 1, 0, 1, 1)
        self.chkReaction = QtGui.QCheckBox(CancelActionsNomenclatureExpenseEditor)
        self.chkReaction.setObjectName(_fromUtf8("chkReaction"))
        self.gridLayout.addWidget(self.chkReaction, 3, 0, 1, 5)
        self.cmbNomenclatureActiveSubstance = CRBComboBox(CancelActionsNomenclatureExpenseEditor)
        self.cmbNomenclatureActiveSubstance.setEnabled(False)
        self.cmbNomenclatureActiveSubstance.setObjectName(_fromUtf8("cmbNomenclatureActiveSubstance"))
        self.gridLayout.addWidget(self.cmbNomenclatureActiveSubstance, 4, 1, 1, 4)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 1, 3, 1, 2)
        self.cmbReactionType = CRBComboBox(CancelActionsNomenclatureExpenseEditor)
        self.cmbReactionType.setEnabled(False)
        self.cmbReactionType.setObjectName(_fromUtf8("cmbReactionType"))
        self.gridLayout.addWidget(self.cmbReactionType, 5, 1, 1, 4)
        spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem1, 9, 1, 1, 1)
        self.edtCancelTime = CTimeEdit(CancelActionsNomenclatureExpenseEditor)
        self.edtCancelTime.setObjectName(_fromUtf8("edtCancelTime"))
        self.gridLayout.addWidget(self.edtCancelTime, 1, 2, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(CancelActionsNomenclatureExpenseEditor)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 10, 0, 1, 5)
        self.cmbReactionManifestation = CRBComboBox(CancelActionsNomenclatureExpenseEditor)
        self.cmbReactionManifestation.setEnabled(False)
        self.cmbReactionManifestation.setObjectName(_fromUtf8("cmbReactionManifestation"))
        self.gridLayout.addWidget(self.cmbReactionManifestation, 6, 1, 1, 4)
        self.edtNotes = QtGui.QLineEdit(CancelActionsNomenclatureExpenseEditor)
        self.edtNotes.setEnabled(False)
        self.edtNotes.setObjectName(_fromUtf8("edtNotes"))
        self.gridLayout.addWidget(self.edtNotes, 8, 1, 1, 4)
        self.cmbPower = QtGui.QComboBox(CancelActionsNomenclatureExpenseEditor)
        self.cmbPower.setEnabled(False)
        self.cmbPower.setObjectName(_fromUtf8("cmbPower"))
        self.cmbPower.addItem(_fromUtf8(""))
        self.cmbPower.addItem(_fromUtf8(""))
        self.cmbPower.addItem(_fromUtf8(""))
        self.cmbPower.addItem(_fromUtf8(""))
        self.cmbPower.addItem(_fromUtf8(""))
        self.gridLayout.addWidget(self.cmbPower, 7, 1, 1, 4)
        self.edtCanceledTime = CTimeEdit(CancelActionsNomenclatureExpenseEditor)
        self.edtCanceledTime.setObjectName(_fromUtf8("edtCanceledTime"))
        self.gridLayout.addWidget(self.edtCanceledTime, 2, 2, 1, 1)
        self.lblCanceledDate = QtGui.QLabel(CancelActionsNomenclatureExpenseEditor)
        self.lblCanceledDate.setObjectName(_fromUtf8("lblCanceledDate"))
        self.gridLayout.addWidget(self.lblCanceledDate, 2, 0, 1, 1)
        self.edtCanceledDate = CDateEdit(CancelActionsNomenclatureExpenseEditor)
        self.edtCanceledDate.setCalendarPopup(True)
        self.edtCanceledDate.setObjectName(_fromUtf8("edtCanceledDate"))
        self.gridLayout.addWidget(self.edtCanceledDate, 2, 1, 1, 1)

        self.retranslateUi(CancelActionsNomenclatureExpenseEditor)
        QtCore.QObject.connect(self.chkReaction, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.cmbNomenclatureActiveSubstance.setEnabled)
        QtCore.QObject.connect(self.chkReaction, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.cmbReactionType.setEnabled)
        QtCore.QObject.connect(self.chkReaction, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.cmbReactionManifestation.setEnabled)
        QtCore.QObject.connect(self.chkReaction, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.cmbPower.setEnabled)
        QtCore.QObject.connect(self.chkReaction, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.edtNotes.setEnabled)
        QtCore.QMetaObject.connectSlotsByName(CancelActionsNomenclatureExpenseEditor)
        CancelActionsNomenclatureExpenseEditor.setTabOrder(self.buttonBox, self.edtCancelDate)
        CancelActionsNomenclatureExpenseEditor.setTabOrder(self.edtCancelDate, self.edtCancelTime)
        CancelActionsNomenclatureExpenseEditor.setTabOrder(self.edtCancelTime, self.chkReaction)
        CancelActionsNomenclatureExpenseEditor.setTabOrder(self.chkReaction, self.cmbNomenclatureActiveSubstance)
        CancelActionsNomenclatureExpenseEditor.setTabOrder(self.cmbNomenclatureActiveSubstance, self.cmbReactionType)
        CancelActionsNomenclatureExpenseEditor.setTabOrder(self.cmbReactionType, self.cmbReactionManifestation)
        CancelActionsNomenclatureExpenseEditor.setTabOrder(self.cmbReactionManifestation, self.cmbPower)
        CancelActionsNomenclatureExpenseEditor.setTabOrder(self.cmbPower, self.edtNotes)

    def retranslateUi(self, CancelActionsNomenclatureExpenseEditor):
        CancelActionsNomenclatureExpenseEditor.setWindowTitle(_translate("CancelActionsNomenclatureExpenseEditor", "Параметры отмены назначения ЛС", None))
        self.lblNomenclatureActiveSubstance.setText(_translate("CancelActionsNomenclatureExpenseEditor", "Действующее вещество", None))
        self.lblPower.setText(_translate("CancelActionsNomenclatureExpenseEditor", "Степень", None))
        self.edtCancelDate.setDisplayFormat(_translate("CancelActionsNomenclatureExpenseEditor", "dd.MM.yyyy", None))
        self.lblNotes.setText(_translate("CancelActionsNomenclatureExpenseEditor", "Примечание", None))
        self.lblReactionManifestation.setText(_translate("CancelActionsNomenclatureExpenseEditor", "Проявление реакции", None))
        self.lblReactionType.setText(_translate("CancelActionsNomenclatureExpenseEditor", "Тип реакции", None))
        self.lblCancelDate.setText(_translate("CancelActionsNomenclatureExpenseEditor", "Отменяемое назначение", None))
        self.chkReaction.setText(_translate("CancelActionsNomenclatureExpenseEditor", "Реакция", None))
        self.edtCancelTime.setDisplayFormat(_translate("CancelActionsNomenclatureExpenseEditor", "HH:mm", None))
        self.cmbPower.setItemText(0, _translate("CancelActionsNomenclatureExpenseEditor", "0 - не известно", None))
        self.cmbPower.setItemText(1, _translate("CancelActionsNomenclatureExpenseEditor", "1 - малая", None))
        self.cmbPower.setItemText(2, _translate("CancelActionsNomenclatureExpenseEditor", "2 - средняя", None))
        self.cmbPower.setItemText(3, _translate("CancelActionsNomenclatureExpenseEditor", "3 - высокая", None))
        self.cmbPower.setItemText(4, _translate("CancelActionsNomenclatureExpenseEditor", "4 - строгая", None))
        self.edtCanceledTime.setDisplayFormat(_translate("CancelActionsNomenclatureExpenseEditor", "HH:mm", None))
        self.lblCanceledDate.setText(_translate("CancelActionsNomenclatureExpenseEditor", "Дата и время отмены", None))

from library.DateEdit import CDateEdit
from library.TimeEdit import CTimeEdit
from library.crbcombobox import CRBComboBox
