# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2017 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################


from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignature, QDate, QTime, QDateTime


from library.interchange     import setCheckBoxValue, setDatetimeEditValue, setDoubleBoxValue, setLabelText, setLineEditValue, setRBComboBoxValue
from library.ItemsListDialog import CItemEditorBaseDialog
from library.PrintTemplates  import customizePrintButton
from library.Utils           import exceptionToUnicode, forceDate, forceInt, forceRef, forceString
from Events.Action           import CActionType
from Events.ActionStatus     import CActionStatus
from Events.ActionEditDialog import CActionEditDialog
from Events.Utils            import setActionPropertiesColumnVisible
from Users.Rights            import urCanUseNomenclatureButton, urCopyPrevAction, urLoadActionTemplate, urEditOtherpeopleAction, urSaveActionTemplate, urEditOtherPeopleActionSpecialityOnly


class CActionCreateDialog(CActionEditDialog):
    def __init__(self, parent):
        CActionEditDialog.__init__(self, parent)
        self.setIsFillPersonValueUserId(True)
        self.setIsFillPersonValueFinished(False)


    def load(self, record, action, clientId = None):
        self.clientId = clientId
        self.action = action
        self.setRecord(record)
        self.setIsDirty(False)


    def setIsFillPersonValueUserId(self, value):
        self.isFillPersonValueUserId = value


    def setIsFillPersonValueFinished(self, value):
        self.isFillPersonValueFinished = value


    def getAction(self):
        self.action._record = self.getRecord()
        return self.action


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        self.eventId = forceRef(record.value('event_id'))
        self.eventTypeId = forceRef(QtGui.qApp.db.translate('Event', 'id', self.eventId, 'eventType_id'))
        self.eventSetDate = forceDate(QtGui.qApp.db.translate('Event', 'id', self.eventId, 'setDate'))
        self.idx = forceInt(record.value('idx'))
        if not self.clientId:
            self.clientId = self.getClientId(self.eventId) if self.eventId else None
        actionType = self.action.getType()
        setActionPropertiesColumnVisible(actionType, self.tblProps)
        showTime = actionType.showTime
        self.edtDirectionTime.setVisible(showTime)
        self.edtPlannedEndTime.setVisible(showTime)
        self.edtCoordTime.setVisible(showTime)
        self.edtBegTime.setVisible(showTime)
        self.edtEndTime.setVisible(showTime)
        self.lblAssistant.setVisible(actionType.hasAssistant)
        self.cmbAssistant.setVisible(actionType.hasAssistant)
        self.setWindowTitle(actionType.code + '|' + actionType.name)
        setCheckBoxValue(self.chkIsUrgent, record, 'isUrgent')
        setDatetimeEditValue(self.edtDirectionDate,    self.edtDirectionTime,    record, 'directionDate')
        setDatetimeEditValue(self.edtPlannedEndDate,   self.edtPlannedEndTime,   record, 'plannedEndDate')
        setDatetimeEditValue(self.edtCoordDate, self.edtCoordTime, record, 'coordDate')
        setLabelText( self.lblCoordText, record, 'coordText')
        setDatetimeEditValue(self.edtBegDate,          self.edtBegTime,          record, 'begDate')
        setDatetimeEditValue(self.edtEndDate,          self.edtEndTime,          record, 'endDate')
        setRBComboBoxValue(self.cmbStatus,      record, 'status')
        setDoubleBoxValue(self.edtAmount,       record, 'amount')
        setDoubleBoxValue(self.edtUet,          record, 'uet')
        setRBComboBoxValue(self.cmbPerson,      record, 'person_id')
        setRBComboBoxValue(self.cmbSetPerson,   record, 'setPerson_id')
        setLineEditValue(self.edtOffice,        record, 'office')
        setRBComboBoxValue(self.cmbAssistant,   record, 'assistant_id')
        setLineEditValue(self.edtNote,          record, 'note')
        self.edtQuantity.setValue(forceInt(record.value('quantity')))
        self.edtDuration.setValue(forceInt(record.value('duration')))
        self.edtPeriodicity.setValue(forceInt(record.value('periodicity')))
        self.edtAliquoticity.setValue(forceInt(record.value('aliquoticity')))

        mkbVisible = bool(actionType.defaultMKB)
        mkbEnabled = actionType.defaultMKB in (CActionType.dmkbByFinalDiag,
                                               CActionType.dmkbBySetPersonDiag,
                                               CActionType.dmkbUserInput
                                              )
        self.cmbMKB.setVisible(mkbVisible)
        self.lblMKB.setVisible(mkbVisible)
        self.cmbMKB.setEnabled(mkbEnabled)
        self.cmbMKB.setText(forceString(record.value('MKB')))

        morphologyMKBVisible = mkbVisible and QtGui.qApp.defaultMorphologyMKBIsVisible()
        self.cmbMorphologyMKB.setVisible(morphologyMKBVisible)
        self.lblMorphologyMKB.setVisible(morphologyMKBVisible)
        self.cmbMorphologyMKB.setEnabled(mkbEnabled)
        self.cmbMorphologyMKB.setText(forceString(record.value('morphologyMKB')))

        self.cmbOrg.setValue(forceRef(record.value('org_id')))
        if (self.cmbPerson.value() is None
                and actionType.defaultPersonInEditor in (CActionType.dpUndefined, CActionType.dpCurrentUser, CActionType.dpCurrentMedUser)
                and QtGui.qApp.userSpecialityId) and self.isFillPersonValueUserId:
            self.cmbPerson.setValue(QtGui.qApp.userId)

        self.setPersonId(self.cmbPerson.value())
        self.updateClientInfo()
        self.cmbOrgStructure.setValue(forceRef(record.value('orgStructure_id')))

        self.modelActionProperties.setAction(self.action, self.clientId, self.clientSex, self.clientAge, self.eventTypeId)
        self.modelActionProperties.reset()
        self.tblProps.resizeRowsToContents()

        context = actionType.context if actionType else ''
        customizePrintButton(self.btnPrint, context)
        self.btnAttachedFiles.setAttachedFileItemList(self.action.getAttachedFileItemList())
        self.btnAttachedFiles.setAction(self.action)

        if QtGui.qApp.userHasRight(urLoadActionTemplate) and (self.cmbStatus.value() != CActionStatus.finished
                                                              or not self.cmbPerson.value()
                                                              or QtGui.qApp.userId == self.cmbPerson.value()
                                                              or (QtGui.qApp.userHasRight(urEditOtherPeopleActionSpecialityOnly) and QtGui.qApp.userSpecialityId == self.getSpecialityId(self.cmbPerson.value()))
                                                              or QtGui.qApp.userHasRight(urEditOtherpeopleAction)):
            actionTemplateTreeModel = self.actionTemplateCache.getModel(actionType.id)
            self.btnLoadTemplate.setModel(actionTemplateTreeModel)
        else:
            self.btnLoadTemplate.setEnabled(False)
        self.btnSaveAsTemplate.setEnabled(QtGui.qApp.userHasRight(urSaveActionTemplate))
        executionPlan = self.action.getExecutionPlan()
        self.edtQuantity.setEnabled(QtGui.qApp.userHasRight(urCopyPrevAction)
                                    and QtGui.qApp.userId == self.cmbSetPerson.value()
                                    and bool(executionPlan)
                                    and not executionPlan #executionPlan.type == CActionExecutionPlanType.type
                                    and self.cmbStatus.value() in (CActionStatus.appointed, )
                                    and not self.edtEndDate.date())

        self.edtDuration.setEnabled(QtGui.qApp.userHasRight(urCopyPrevAction)
                                    and QtGui.qApp.userId == self.cmbSetPerson.value()
                                    and not self.action.getExecutionPlan()
                                    and self.cmbStatus.value() in (CActionStatus.started, CActionStatus.appointed)
                                    and not self.edtEndDate.date())
        self.edtPeriodicity.setEnabled(QtGui.qApp.userHasRight(urCopyPrevAction)
                                       and QtGui.qApp.userId == self.cmbSetPerson.value()
                                       and not self.action.getExecutionPlan()
                                       and self.cmbStatus.value() in (CActionStatus.started, CActionStatus.appointed)
                                       and not self.edtEndDate.date())
        self.edtAliquoticity.setEnabled(QtGui.qApp.userHasRight(urCopyPrevAction)
                                        and QtGui.qApp.userId == self.cmbSetPerson.value()
                                        and not self.action.getExecutionPlan()
                                        and self.cmbStatus.value() in (CActionStatus.started, CActionStatus.appointed)
                                        and not self.edtEndDate.date())

        canEdit = not self.action.isLocked() if self.action else True
        for widget in (self.edtPlannedEndDate, self.edtPlannedEndTime,
                       self.cmbStatus, self.edtBegDate, self.edtBegTime,
                       self.edtEndDate, self.edtEndTime,
                       self.cmbPerson, self.edtOffice,
                       self.cmbAssistant,
                       self.edtUet,
                       self.edtNote, self.cmbOrg,
                       self.buttonBox.button(QtGui.QDialogButtonBox.Ok)
                      ):
                widget.setEnabled(canEdit)
        self.edtAmount.setEnabled(actionType.amountEvaluation == 0 and canEdit)
        if not QtGui.qApp.userHasRight(urLoadActionTemplate) and not (self.cmbStatus.value() != CActionStatus.finished
                                                                      or not self.cmbPerson.value()
                                                                      or QtGui.qApp.userId == self.cmbPerson.value()
                                                                      or (QtGui.qApp.userHasRight(urEditOtherPeopleActionSpecialityOnly) and QtGui.qApp.userSpecialityId == self.getSpecialityId(self.cmbPerson.value()))
                                                                      or QtGui.qApp.userHasRight(urEditOtherpeopleAction)) and not canEdit:
            self.btnLoadTemplate.setEnabled(False)

        canEditPlannedEndDate = canEdit and actionType.defaultPlannedEndDate not in (CActionType.dpedBegDatePlusAmount,
                                                                                     CActionType.dpedBegDatePlusDuration)
        self.edtPlannedEndDate.setEnabled(canEditPlannedEndDate)
        self.edtPlannedEndTime.setEnabled(canEditPlannedEndDate and bool(self.edtPlannedEndDate.date()))

        #btnNextActionEnabled = (self.edtDuration.value() > 1 or self.edtAliquoticity.value() > 1) and not self.edtEndDate.date()

        isEnable = self.btnNextActionMustBeEnabled()
        if self.action.getType().isNomenclatureExpense:
            isEnable = isEnable and self.isEnabledNomenclatureExpense(self.action)
        self.btnNextAction.setEnabled(isEnable)

        if self.edtDuration.value() > 0:
            self.btnPlanNextAction.setEnabled(True)
        else:
            self.btnPlanNextAction.setEnabled(False)
        self.on_edtDuration_valueChanged(forceInt(record.value('duration')))
        self.edtBegTime.setEnabled(bool(self.edtBegDate.date()) and canEdit)
        self.edtEndTime.setEnabled(bool(self.edtEndDate.date()) and canEdit)
        self.edtPlannedEndTime.setEnabled(bool(self.edtPlannedEndDate.date()) and canEdit)
        if not self.getNomenclatureExpenseEnabled(self.action, actionType):
            self.btnAPNomenclatureExpense.setVisible(False)
        elif not QtGui.qApp.userHasAnyRight([urCanUseNomenclatureButton]):
            self.btnAPNomenclatureExpense.setEnabled(False)
        self.setActionCoordinationEnable(actionType.isRequiredCoordination)


    def save(self):
        try:
            prevId = self.itemId()
            db = QtGui.qApp.db
            db.transaction()
            try:
                self.action._record = self.getRecord()
                id = self.saveInternals(None)
                db.commit()
            except:
                db.rollback()
                self.setItemId(prevId)
                raise
            self.setItemId(id)
            self.afterSave()
            return id
        except Exception, e:
            QtGui.qApp.logCurrentException()
            QtGui.QMessageBox.critical( self,
                                        u'',
                                        exceptionToUnicode(e),
                                        QtGui.QMessageBox.Close)
            return None


    @pyqtSignature('int')
    def on_cmbStatus_currentIndexChanged(self, index):
        actionStatus = self.cmbStatus.value()
        if actionStatus in (CActionStatus.finished, CActionStatus.withoutResult):
            if not self.edtEndDate.date():
                now = QDateTime.currentDateTime()
                self.edtEndDate.setDate(now.date())
                if self.edtEndTime.isVisible():
                    self.edtEndTime.setTime(now.time())
            if self.isFillPersonValueFinished:
                if QtGui.qApp.userId and QtGui.qApp.userSpecialityId:
                    self.cmbPerson.setValue(QtGui.qApp.userId)
        elif actionStatus in (CActionStatus.canceled, CActionStatus.refused):
            self.edtEndDate.setDate(QDate())
            self.edtEndTime.setTime(QTime())
            if QtGui.qApp.userId and QtGui.qApp.userSpecialityId:
                self.cmbPerson.setValue(QtGui.qApp.userId)
            else:
                self.cmbPerson.setValue(self.cmbSetPerson.value())
        else:
            self.edtEndDate.setDate(QDate())
            self.edtEndTime.setTime(QTime())
        
        isEnable = self.btnNextActionMustBeEnabled()
        if self.action.getType().isNomenclatureExpense:
            isEnable = isEnable and self.isEnabledNomenclatureExpense(self.action)
        self.btnNextAction.setEnabled(isEnable)


class CTempInvalidActionCreateDialog(CActionCreateDialog):
    def __init__(self, parent):
        CActionCreateDialog.__init__(self, parent)


    def saveInternals(self, id):
        return id


    def save(self):
        try:
            try:
                self.action._record = self.getRecord()
            except:
                raise
            return True
        except Exception, e:
            QtGui.qApp.logCurrentException()
            QtGui.QMessageBox.critical( self,
                                        u'',
                                        exceptionToUnicode(e),
                                        QtGui.QMessageBox.Close)
            return None

