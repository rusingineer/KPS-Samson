# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2025 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSlot, QDateTime

from library.interchange     import setCheckBoxValue, setDatetimeEditValue, setDoubleBoxValue, setLineEditValue, setRBComboBoxValue
from library.ItemsListDialog import CItemEditorBaseDialog
from library.PrintTemplates  import customizePrintButton
from library.Utils           import forceDate, forceInt, forceRef, toVariant, forceDateTime
from Events.Action           import CActionType
from Events.ActionStatus     import CActionStatus
from F111.F111EditDialog     import CF111EditDialog


class CF111CreateDialog(CF111EditDialog):
    def __init__(self, parent):
        CF111EditDialog.__init__(self, parent, isCreate=True)
        self.setIsFillPersonValueUserId(True)
        self.setIsFillPersonValueFinished(False)
        self.setInitDate()


    def load(self, record, action, clientId = None, recordFirstEvent = None):
        self.clientId = clientId
        self.action = action
        actionType = self.action.getType() if self.action else None
        self.actionTypeId = actionType.id if actionType else None
        self.recordEvent = recordFirstEvent
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
        self.eventTypeId = None
        self.eventSetDate = None
        self.eventSetDateTime = None
        self.eventDate = None
        self.recordClient = None
        self.recordClientSocStatus = None
        self.newRecordClientSocStatus = None
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        currentOrgId = forceRef(self.recordEvent.value('org_id')) if self.recordEvent else None
        if not currentOrgId:
            if QtGui.qApp.userId:
                recordPerson = db.getRecord('Person', ['org_id'], QtGui.qApp.userId)
                if recordPerson:
                    currentOrgId = forceRef(recordPerson.value('org_id'))
        if not currentOrgId:
            currentOrgId = QtGui.qApp.currentOrgId()
        if not self.clientId:
            self.clientId = self.getClientId(self.eventId) if self.eventId else None
        if self.recordEvent and not self.eventId:
            self.eventId = forceRef(self.recordEvent.value('id'))
            self.action.getRecord().setValue('event_id', toVariant(self.eventId))
        if self.eventId and not self.recordEvent:
            self.recordEvent = db.getRecordEx(tableEvent, '*', [tableEvent['id'].eq(self.eventId), tableEvent['deleted'].eq(0)])
        elif not self.recordEvent and not self.eventId:
            if self.clientId:
                queryTable = tableEvent.innerJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
                cond = [tableEventType['code'].like(u'KBiR%'),
                        tableEvent['execDate'].isNull(),
                        tableEvent['client_id'].eq(self.clientId),
                        tableEvent['deleted'].eq(0),
                        tableEventType['deleted'].eq(0),
                        ]
                self.recordEvent = db.getRecordEx(queryTable, 'Event.*', cond, u'Event.id DESC')
                self.eventId = forceRef(self.recordEvent.value('id')) if self.recordEvent else None
        if not self.recordEvent:
            recordEventType = db.getRecordEx(tableEventType, [tableEventType['id']], [tableEventType['code'].like(u'KBiR%'), tableEventType['deleted'].eq(0)], u'EventType.id')
            eventTypeId = forceRef(recordEventType.value('id')) if recordEventType else None
            if eventTypeId:
                self.recordEvent = tableEvent.newRecord()
                self.recordEvent.setValue('createDatetime', toVariant(QDateTime.currentDateTime()))
                self.recordEvent.setValue('createPerson_id',toVariant(QtGui.qApp.userId))
                self.recordEvent.setValue('modifyDatetime', toVariant(QDateTime.currentDateTime()))
                self.recordEvent.setValue('modifyPerson_id',toVariant(QtGui.qApp.userId))
                self.recordEvent.setValue('setDate',        toVariant(QDateTime.currentDateTime()))
                self.recordEvent.setValue('eventType_id',   toVariant(eventTypeId))
                self.recordEvent.setValue('relegatePerson_id', toVariant(QtGui.qApp.userId))
                self.recordEvent.setValue('relegateOrg_id', toVariant(QtGui.qApp.currentOrgId()))
        if self.recordEvent:
            if not forceRef(self.recordEvent.value('org_id')):
                self.recordEvent.setValue('org_id', toVariant(currentOrgId))
            if not forceDate(self.recordEvent.value('setDate')):
                self.recordEvent.setValue('setDate', toVariant(QDateTime.currentDateTime()))
            self.eventTypeId = forceRef(self.recordEvent.value('eventType_id'))
            self.eventSetDate = forceDate(self.recordEvent.value('setDate'))
            self.eventSetDateTime = forceDateTime(self.recordEvent.value('setDate'))
            self.eventDate = forceDate(self.recordEvent.value('execDate'))
            self.action.getRecord().setValue('event_id', toVariant(self.eventId))
        self.idx = forceInt(record.value('idx'))
        self.edtNVNBDZKDate.setDate(self.eventDate)
        if self.recordEvent and self.clientId and not forceRef(self.recordEvent.value('client_id')):
            self.recordEvent.setValue('client_id', toVariant(self.clientId))
        actionType = self.action.getType()
        self.getDiagnosisMKB()
        self.setComboBoxes()
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
        canEditPlannedEndDate = canEdit and actionType.defaultPlannedEndDate not in (CActionType.dpedBegDatePlusAmount,
                                                                                     CActionType.dpedBegDatePlusDuration)
        self.edtPlannedEndDate.setEnabled(canEditPlannedEndDate)
        self.edtPlannedEndTime.setEnabled(canEditPlannedEndDate and bool(self.edtPlannedEndDate.date()))
        self.edtBegTime.setEnabled(bool(self.edtBegDate.date()) and canEdit)
        self.edtEndTime.setEnabled(bool(self.edtEndDate.date()) and canEdit)
        self.edtPlannedEndTime.setEnabled(bool(self.edtPlannedEndDate.date()) and canEdit)
        self.setProperties(isCreate=True)
        self.modelSOPSvORNM.setAction(self.action)
        self.modelSOPSvORNM.loadItems(self.clientId)
        self.modelNVNBVARRS.setAction(self.action)
        self.modelNVNBVARRS.loadItems(self.clientId)
        self.modelNVNBAR.setAction(self.action)
        self.modelNVNBAR.loadItems(self.clientId)
        self.modelNVNBSGVB.setAction(self.action)
        self.modelNVNBSGVB.loadItems(self.clientId)
        self.modelPreviousPregnancy.loadItems(self.action.getId())
        conActionId = self.modelPreviousPregnancy.getActionIdToRow(0)
        conItems = self.modelPreviousPregnancy.items()
        if conItems and hasattr(conItems[0], 'aboutChildrenProperties'):
            self.modelPreviousPregnancyChildren.setItems(conItems[0].aboutChildrenProperties.getItems())
        else:
            self.modelPreviousPregnancyChildren.clearItems()
        self.updatePreviousPregnancyChildren(self.modelPreviousPregnancy.index(0, 0), self.tblPreviousPregnancyChildren, actionId=conActionId)
        if record:
            self.tabNotes.setNotes(record)
            self.tabNotes.setEventEditor(self)
        self.on_btnBoxPregnancyRetrospect_apply()
        date = self.edtNVNBDZKDate.date()
        if date and date.isValid():
            self.lblCloseReason.setVisible(True)
            self.edtCloseReason.setVisible(True)
        else:
            self.lblCloseReason.setVisible(False)
            self.edtCloseReason.setVisible(False)    
            self.edtCloseReason.setText('')


    @pyqtSlot(int)
    def on_cmbStatus_currentIndexChanged(self, index):
        actionStatus = self.cmbStatus.value()
        if actionStatus in (CActionStatus.finished, CActionStatus.canceled, CActionStatus.refused):
            if not self.edtEndDate.date():
                now = QDateTime.currentDateTime()
                self.edtEndDate.setDate(now.date())
                if self.edtEndTime.isVisible():
                    self.edtEndTime.setTime(now.time())
            if self.isFillPersonValueFinished:
                if QtGui.qApp.userId and QtGui.qApp.userSpecialityId:
                    self.cmbPerson.setValue(QtGui.qApp.userId)
            if actionStatus in (CActionStatus.canceled, CActionStatus.refused) and not self.cmbPerson.value():
                if QtGui.qApp.userId and QtGui.qApp.userSpecialityId:
                    self.cmbPerson.setValue(QtGui.qApp.userId)
                else:
                    self.cmbPerson.setValue(self.cmbSetPerson.value())

