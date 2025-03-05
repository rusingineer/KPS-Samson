# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2024 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore             import Qt, pyqtSignature, QDate, QTime, QDateTime

from library.DialogBase       import CDialogBase
from library.PreferencesMixin import CDialogPreferencesMixin

from Events.NomenclatureExpense.Ui_CancelActionsNomenclatureExpenseEditor import Ui_CancelActionsNomenclatureExpenseEditor


class CCancelActionsNomenclatureExpenseEditor(CDialogBase, Ui_CancelActionsNomenclatureExpenseEditor, CDialogPreferencesMixin):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.cmbNomenclatureActiveSubstance.setTable('rbNomenclatureActiveSubstance')
        self.cmbReactionType.setTable('rbReactionType')
        self.cmbReactionManifestation.setTable('rbReactionManifestation')
        self.params = {}
        self.begDateTimeActionLast = None
        self.edtCanceledTime.setTime(QTime.currentTime())


    @pyqtSignature('QDate')
    def on_edtCancelDate_dateChanged(self, date):
        pass

    @pyqtSignature('QTime')
    def on_edtCancelTime_timeChanged(self, time):
        if self.begDateTimeActionLast:
            if self.edtCancelDate.date() == self.begDateTimeActionLast.date():
                if time < self.begDateTimeActionLast.time():
                    self.edtCancelTime.setTime(self.begDateTimeActionLast.time())


    def setMinBegDate(self, begDateTimeActionLast):
        self.edtCancelDate.setReadOnly(True)
        self.edtCancelTime.setReadOnly(True)
        self.begDateTimeActionLast = begDateTimeActionLast
        if begDateTimeActionLast:
            min = begDateTimeActionLast.date()
            minTime = begDateTimeActionLast.time()
            if isinstance(min, QDate) and min.isValid():
                self.edtCancelDate.setDateRange(min, min)
                if self.edtCancelDate.date() < min or self.edtCancelDate.date() > min:
                    self.edtCancelDate.setDate(min)
            if isinstance(minTime, QTime) and minTime.isValid():
                self.edtCancelTime.setTime(minTime)
    
    
    def setNomenclature(self, nomenclatureId):
        self.cmbNomenclatureActiveSubstance.setValue(nomenclatureId)


    @pyqtSignature('QAbstractButton*')
    def on_buttonBox_clicked(self, button):
        buttonCode = self.buttonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Ok:
            self.on_buttonBox_ok()
        elif buttonCode == QtGui.QDialogButtonBox.Cancel:
            self.params = {}
            QtGui.QDialog.reject(self)


    def on_buttonBox_ok(self):
        if self.getCancelParams():
            QtGui.QDialog.accept(self)


    def getCancelParams(self):
        result = True
        self.params = {}
        cancelDateTime = QDateTime(self.edtCancelDate.date(), self.edtCancelTime.time())
        canceledDateTime = QDateTime(self.edtCanceledDate.date(), self.edtCanceledTime.time())
        result = result and (cancelDateTime or self.checkInputMessage(u'Дата и время отмены', False, self.edtCancelDate))
        if result:
            self.params['cancelDateTime'] = cancelDateTime
            self.params['canceledDateTime'] = canceledDateTime
            reaction = self.chkReaction.isChecked()
            self.params['reaction'] = reaction
            if reaction:
                activeSubstance = self.cmbNomenclatureActiveSubstance.value()
                self.params['activeSubstance'] = activeSubstance
                notes = self.edtNotes.text()
                self.params['notes'] = notes
                result = result and (notes or (activeSubstance or self.checkInputMessage(u'Действующее вещество или Примечание', False, self.cmbNomenclatureActiveSubstance)))
                if result and activeSubstance:
                    reactionType = self.cmbReactionType.value()
                    self.params['reactionType'] = reactionType
                    result = result and (reactionType or self.checkInputMessage(u'Тип реакции', False, self.cmbReactionType))
                    if result:
                        reactionManifestation = self.cmbReactionManifestation.value()
                        self.params['reactionManifestation'] = reactionManifestation
                        result = result and (reactionManifestation or self.checkInputMessage(u'Проявление реакции', False, self.cmbReactionManifestation))
                        if result:
                            power = self.cmbPower.currentIndex()
                            self.params['power'] = power
                            result = result and (power or self.checkInputMessage(u'Степень', False, self.cmbPower))
        if not result:
            self.params = {}
        return result


    def setCancelParams(self):
        cancelDateTime = self.params.get('cancelDateTime', None)
        self.edtCancelDate.setDate(cancelDateTime.date())
        self.edtCancelTime.setDate(cancelDateTime.time())
        self.chkReaction.setChecked(self.params.get('reaction', False))
        self.cmbNomenclatureActiveSubstance.setValue(self.params.get('activeSubstance', None))
        self.cmbReactionType.setValue(self.params.get('reactionType', None))
        self.cmbReactionManifestation.setValue(self.params.get('reactionManifestation', None))
        self.cmbPower.setCurrentIndex(self.params.get('power', 0))
        self.edtNotes.setText(self.params.get('notes', ''))


    def getCancelActionParams(self):
        return self.params


    @pyqtSignature('bool')
    def on_chkReaction_toggled(self, value):
        self.cmbNomenclatureActiveSubstance.setFocus(Qt.TabFocusReason)


    def saveData(self):
        return True

