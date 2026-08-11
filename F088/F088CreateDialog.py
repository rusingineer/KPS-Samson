# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2021 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignature, QDate, QTime, QDateTime, QVariant, QString

from Events.Utils import CEventTypeDescription, checkTissueJournalStatusByActions
from library.interchange import setCheckBoxValue, setDatetimeEditValue, setDoubleBoxValue, setLineEditValue, setRBComboBoxValue
from library.ItemsListDialog import CItemEditorBaseDialog
from library.PrintTemplates import customizePrintButton
from library.Utils import forceDate, forceInt, forceRef, toVariant, forceDateTime, trim, forceString, forceBool
from Events.Action import CActionType
from Events.ActionStatus import CActionStatus
from F088.F088EditDialog import CF088EditDialog
from Users.Rights import urLoadActionTemplate, urEditOtherpeopleAction, urSaveActionTemplate


class CF088CreateDialog(CF088EditDialog):
    def __init__(self, parent, eventTypeId=None):
        CF088EditDialog.__init__(self, parent, isCreate=True)
        self.setIsFillPersonValueUserId(True)
        self.setIsFillPersonValueFinished(False)
        self.eventTypeId = eventTypeId
        self.eventId = None
        self.tabWidget.setTabEnabled(self.tabWidget.indexOf(self.tabExtendedMSE), forceBool(self.servicesURL))


    def load(self, record, action, clientId=None, recordFirstEvent=None):
        self.clientId = clientId
        self.action = action
        self.recordEvent = recordFirstEvent
        self.initNewData()
        self.setRecord(record)
        self.setComboBoxes()
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
        # self.eventTypeId = None
        self.eventSetDate = None
        self.eventSetDateTime = None
        self.eventDate = None
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        if self.eventId and not self.recordEvent:
            self.recordEvent = db.getRecordEx(tableEvent, '*', [tableEvent['id'].eq(self.eventId), tableEvent['deleted'].eq(0)])
        elif not self.recordEvent:
            # recordEventType = db.getRecordEx(tableEventType, [tableEventType['id']], [tableEventType['context'].like(u'inspection%'), tableEventType['deleted'].eq(0)], u'EventType.id')
            # eventTypeId = forceRef(recordEventType.value('id')) if recordEventType else None
            if self.eventTypeId:
                self.recordEvent = tableEvent.newRecord()
                self.recordEvent.setValue('createDatetime', toVariant(QDateTime().currentDateTime()))
                self.recordEvent.setValue('createPerson_id', toVariant(QtGui.qApp.userId))
                self.recordEvent.setValue('modifyDatetime', toVariant(QDateTime().currentDateTime()))
                self.recordEvent.setValue('modifyPerson_id', toVariant(QtGui.qApp.userId))
                self.recordEvent.setValue('setDate',        toVariant(QDateTime().currentDateTime()))
                self.recordEvent.setValue('eventType_id',   toVariant(self.eventTypeId))
                self.recordEvent.setValue('relegatePerson_id', toVariant(QtGui.qApp.userId))
                self.recordEvent.setValue('relegateOrg_id', toVariant(QtGui.qApp.currentOrgId()))
                self.recordEvent.setValue('org_id', toVariant(QtGui.qApp.currentOrgId()))
        if self.recordEvent:
            self.eventTypeId = forceRef(self.recordEvent.value('eventType_id'))
            self.eventSetDate = forceDate(self.recordEvent.value('setDate'))
            self.eventSetDateTime = forceDateTime(self.recordEvent.value('setDate'))
            self.eventDate = forceDate(self.recordEvent.value('execDate'))
        self.idx = forceInt(record.value('idx'))
        if not self.clientId:
            self.clientId = self.getClientId(self.eventId) if self.eventId else None
        if self.recordEvent and self.clientId and not forceRef(self.recordEvent.value('client_id')):
            self.recordEvent.setValue('client_id', toVariant(self.clientId))
        actionType = self.action.getType()
        self.actionTypeId = actionType.id
        self.isRelationRepresentativeSetClientId = True
        self.cmbClientRelationRepresentative.clear()
        self.cmbClientRelationRepresentative.setClientId(self.clientId)
        self.cmbClientRelationRepresentative.setValue(forceRef(self.recordEvent.value('relative_id')) if self.recordEvent else None)
        self.tabNotes.cmbClientRelationConsents.clear()
        self.tabNotes.cmbClientRelationConsents.setClientId(self.clientId)
        self.tabNotes.cmbClientRelationConsents.setValue(forceRef(self.recordEvent.value('relative_id')))
        self.isRelationRepresentativeSetClientId = False
        showTime = actionType.showTime
        self.edtDirectionTime.setVisible(showTime)
        self.edtPlannedEndTime.setVisible(showTime)
        self.edtBegTime.setVisible(showTime)
        self.edtEndTime.setVisible(showTime)
        self.lblAssistant.setVisible(actionType.hasAssistant)
        self.cmbAssistant.setVisible(actionType.hasAssistant)
        self.setWindowTitle(actionType.code + '|' + actionType.name)
        setCheckBoxValue(self.chkIsUrgent, record, 'isUrgent')
        setDatetimeEditValue(self.edtDirectionDate,    self.edtDirectionTime,    record, 'directionDate')
        setDatetimeEditValue(self.edtPlannedEndDate,   self.edtPlannedEndTime,   record, 'plannedEndDate')
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
        self.cmbOrg.setValue(forceRef(record.value('org_id')))
        if (self.cmbPerson.value() is None
                and actionType.defaultPersonInEditor in (CActionType.dpUndefined, CActionType.dpCurrentUser, CActionType.dpCurrentMedUser)
                and QtGui.qApp.userSpecialityId) and self.isFillPersonValueUserId:
            self.cmbPerson.setValue(QtGui.qApp.userId)

        self.setPersonId(self.cmbPerson.value())
        self.updateClientInfo()
        context = actionType.context if actionType else ''
        customizePrintButton(self.btnPrint, context)
        self.btnAttachedFiles.setAttachedFileItemList(self.action.getAttachedFileItemList())
        self.btnAttachedFiles.setAction(self.action)

        if QtGui.qApp.userHasRight(urLoadActionTemplate) and (self.cmbStatus.value() != CActionStatus.finished or not self.cmbPerson.value() or QtGui.qApp.userId == self.cmbPerson.value() or QtGui.qApp.userHasRight(urEditOtherpeopleAction)):
            actionTemplateTreeModel = self.actionTemplateCache.getModel(actionType.id)
            self.btnLoadTemplate.setModel(actionTemplateTreeModel)
        else:
            self.btnLoadTemplate.setEnabled(False)
        self.btnSaveAsTemplate.setEnabled(QtGui.qApp.userHasRight(urSaveActionTemplate))

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
        if not QtGui.qApp.userHasRight(urLoadActionTemplate) and not (self.cmbStatus.value() != CActionStatus.finished or not self.cmbPerson.value() or QtGui.qApp.userId == self.cmbPerson.value() or QtGui.qApp.userHasRight(urEditOtherpeopleAction)) and not canEdit:
            self.btnLoadTemplate.setEnabled(False)

        canEditPlannedEndDate = canEdit and actionType.defaultPlannedEndDate not in (CActionType.dpedBegDatePlusAmount,
                                                                                     CActionType.dpedBegDatePlusDuration)
        self.edtPlannedEndDate.setEnabled(canEditPlannedEndDate)
        self.edtPlannedEndTime.setEnabled(canEditPlannedEndDate and bool(self.edtPlannedEndDate.date()))
        self.edtBegTime.setEnabled(bool(self.edtBegDate.date()) and canEdit)
        self.edtEndTime.setEnabled(bool(self.edtEndDate.date()) and canEdit)
        self.edtPlannedEndTime.setEnabled(bool(self.edtPlannedEndDate.date()) and canEdit)
        self.setProperties(isCreate=True)
        if self.recordEvent:
            self.tabNotes.setNotes(self.recordEvent)
        self.tabNotes.setEventEditor(self)
        self.modelTempInvalidYear.setAction(self.action)
        self.modelTempInvalidYear.loadItems(self.clientId)
        self.grpTempInvalid.pickupTempInvalid()
        self.grpAegrotat.pickupTempInvalid()
        self.grpDisability.pickupTempInvalid()
        self.grpVitalRestriction.pickupTempInvalid()
        actionId = self.itemId()
        lpu_guid = forceString(db.translate('Organisation', 'id', QtGui.qApp.currentOrgId(), 'usishCode'))
        self.tabExtendedMSE.setClientInfo({'clientId': self.clientId, 'lpuGuid': lpu_guid, 'actionId': actionId})


    def save(self):
        self.setTextEdits()
        action = self.getAction()
        eventRecordMSI = self.getEventRecord()
        newActionId = None
        db = QtGui.qApp.db
        if action:
            tableEvent = db.table('Event')
            recordEvent = tableEvent.newRecord()
            if eventRecordMSI:
                for i in xrange(recordEvent.count()):
                    recordEvent.setValue(i, eventRecordMSI.value(recordEvent.fieldName(i)))
                recordEvent.setValue('eventType_id', toVariant(self.eventTypeId))
                if self.clientId and not forceRef(recordEvent.value('client_id')):
                    recordEvent.setValue('client_id', toVariant(self.clientId))
            else:
                recordEvent.setValue('createDatetime', toVariant(QDateTime().currentDateTime()))
                recordEvent.setValue('createPerson_id', toVariant(QtGui.qApp.userId))
                recordEvent.setValue('modifyDatetime', toVariant(QDateTime().currentDateTime()))
                recordEvent.setValue('modifyPerson_id', toVariant(QtGui.qApp.userId))
                recordEvent.setValue('setPerson_id', toVariant(QtGui.qApp.userId))
                recordEvent.setValue('eventType_id', toVariant(self.eventTypeId))
                recordEvent.setValue('client_id', toVariant(self.clientId))
                recordEvent.setValue('relegatePerson_id', toVariant(QtGui.qApp.userId))
                recordEvent.setValue('relegateOrg_id', toVariant(QtGui.qApp.currentOrgId()))
                recordEvent.setValue('org_id', toVariant(QtGui.qApp.currentOrgId()))

            recordEvent.setValue('execPerson_id', toVariant(action.getRecord().value('person_id')))
            recordEvent.setValue('setDate', toVariant(action.getRecord().value('begDate')))
            if forceDateTime(action.getRecord().value('endDate')):
                recordEvent.setValue('execDate', action.getRecord().value('endDate'))
                recordEvent.setValue('isClosed', QVariant(1))
            else:
                recordEvent.setValue('execDate', QVariant(None))
                recordEvent.setValue('isClosed', QVariant(0))
            recordEvent.setValue('order', QVariant(1))  # порядок события всегда плановый
            tableRbDiagnosticResult = QtGui.qApp.db.table('rbDiagnosticResult')
            eventType = CEventTypeDescription.get(self.eventTypeId)
            recDiagResult = QtGui.qApp.db.getRecordEx(tableRbDiagnosticResult,
                                                      [tableRbDiagnosticResult['result_id']],
                                                      tableRbDiagnosticResult['eventPurpose_id'].eq(
                                                          eventType.purposeId))
            recordEvent.setValue('result_id', recDiagResult.value('result_id') if recDiagResult else None)
            isPrimary = 1
            for property in action._propertiesById.itervalues():
                propertyType = property.type()
                if trim(propertyType.shortName) == '18':
                    value = property._value
                    propertyValue = propertyType.convertQVariantToPyValue(value) if type(
                        value) == QVariant else value
                    if isinstance(propertyValue, basestring) or type(propertyValue) == QString:
                        propertyValue = trim(propertyValue)
                        if propertyValue == u'18.2. повторно':
                            isPrimary = 2
                        else:
                            isPrimary = 1
            recordEvent.setValue('isPrimary', QVariant(isPrimary))
            checkTissueJournalStatusByActions([(action.getRecord(), action)])
            self.eventId = db.insertOrUpdate(tableEvent, recordEvent)
            if self.eventId:
                recordEvent.setValue('id', toVariant(self.eventId))
                self.recordEvent = recordEvent
                newActionId = action.save(self.eventId, idx=self.idx, checkModifyDate=False)
                if newActionId:
                    action.getRecord().setValue('id', toVariant(newActionId))
                    self.setRecord(action.getRecord())
            if self.eventId and newActionId:
                if hasattr(self, 'modelVisits'):
                    if not self.modelVisits.items():
                        visit = self.modelVisits.getEmptyRecord(sceneId=None, personId=self.personId)
                        visit.setValue('date', toVariant(self.eventSetDate))
                    else:
                        visit = self.modelVisits.items()[0]
                        visit.setValue('date', toVariant(self.action.getRecord().value('begDate')))
                        visit.setValue('person_id', toVariant(self.personId))
                    self.modelVisits.setItems([visit])
                    self.modelVisits.saveItems(self.eventId)
                if hasattr(self, 'tabNotes') and hasattr(self.tabNotes, 'saveAttachedFiles'):
                    self.tabNotes.saveAttachedFiles(self.eventId)
                if hasattr(self, 'modelDiagnosisDisease_30_2'):
                    self.saveDiagnostics(self.modelDiagnosisDisease_30_2, self.eventId)
                if hasattr(self, 'modelDiagnosisDisease_30_3'):
                    self.saveDiagnostics(self.modelDiagnosisDisease_30_3, self.eventId)
                if hasattr(self, 'modelDiagnosisDisease_30_5'):
                    self.saveDiagnostics(self.modelDiagnosisDisease_30_5, self.eventId)
                if hasattr(self, 'modelDiagnosisDisease_30_6'):
                    self.saveDiagnostics(self.modelDiagnosisDisease_30_6, self.eventId)
                self.tabExtendedMSE.saveData()
        return True


    @pyqtSignature('int')
    def on_cmbStatus_currentIndexChanged(self, index):
        actionStatus = self.cmbStatus.value()
        if actionStatus in (CActionStatus.finished, ):
            if not self.edtEndDate.date():
                now = QDateTime().currentDateTime()
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
