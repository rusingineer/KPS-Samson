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
from PyQt4.QtCore import pyqtSignature, QDateTime

from library.interchange     import setCheckBoxValue, setDatetimeEditValue, setDoubleBoxValue, setLineEditValue, setRBComboBoxValue
from library.ItemsListDialog import CItemEditorBaseDialog
from library.PrintTemplates  import customizePrintButton
from library.Utils           import forceDate, forceInt, forceRef, toVariant, forceDateTime
from Events.Action           import CActionType, CActionTypeCache, CAction
from Events.ActionStatus     import CActionStatus
from Events.Utils            import getActionTypeIdListByFlatCode, getEventSceneId, getEventPurposeId
from F090.F090EditDialog     import CF090EditDialog
from F090.HurtTypeDialog     import CHurtTypeDialog
from F001.PreF001Dialog      import CPreF001Dialog
#from Registry.Utils          import preFillingActionRecordMSI


def createF090(obj, recordEvent = None):
    result = False
    eventId = None
    actionId = None
    db = QtGui.qApp.db
    tableAction = db.table('Action')
    clientId = forceRef(recordEvent.value('client_id')) if recordEvent else None
    if not clientId:
        return
    actionTypeIdList = getActionTypeIdListByFlatCode(u'%medical_examination')
    if actionTypeIdList and len(actionTypeIdList) == 1:
        actionTypeId = actionTypeIdList[0]
        if actionTypeId:
            dialogF090 = CF090CreateDialog(obj)
            try:
                actionType = CActionTypeCache.getById(actionTypeId)
                defaultStatus = actionType.defaultStatus
                defaultOrgId = actionType.defaultOrgId
                defaultExecPersonId = actionType.defaultExecPersonId
                newRecord = tableAction.newRecord()
                newRecord.setValue('createDatetime', toVariant(QDateTime.currentDateTime()))
                newRecord.setValue('createPerson_id',toVariant(QtGui.qApp.userId))
                newRecord.setValue('modifyDatetime', toVariant(QDateTime.currentDateTime()))
                newRecord.setValue('modifyPerson_id',toVariant(QtGui.qApp.userId))
                newRecord.setValue('actionType_id',  toVariant(actionTypeId))
                newRecord.setValue('prevAction_id',  toVariant(None))
                newRecord.setValue('status',         toVariant(defaultStatus))
                newRecord.setValue('begDate',        toVariant(QDateTime.currentDateTime()))
                newRecord.setValue('directionDate',  toVariant(QDateTime.currentDateTime()))
                newRecord.setValue('org_id',         toVariant(defaultOrgId if defaultOrgId else QtGui.qApp.currentOrgId()))
                newRecord.setValue('setPerson_id',   toVariant(QtGui.qApp.userId))
                newRecord.setValue('person_id',      toVariant(defaultExecPersonId))
                newRecord.setValue('id',             toVariant(None))
                newAction = CAction(record=newRecord)
                if not newAction:
                    return
                newRecord = newAction.getRecord()
                dialogF090.load(newRecord, newAction, clientId, recordEvent=recordEvent, preDiagnostics = obj.preDiagnostics, preSpecialityIdList = obj.preSpecialityIdList, isSelectionGroupOne = obj.isSelectionGroupOne)
#                newRecord = dialogF090.preFillingActionRecord090(recordEvent, newRecord, actionTypeId, actionType.amount, financeId=None, contractId=None, orgStructureId=None)
#                setDatetimeEditValue(dialogF090.edtDirectionDate, dialogF090.edtDirectionTime, newRecord, 'directionDate')
#                setDatetimeEditValue(dialogF090.edtPlannedEndDate, dialogF090.edtPlannedEndTime, newRecord, 'plannedEndDate')
#                setDatetimeEditValue(dialogF090.edtBegDate, dialogF090.edtBegTime, newRecord, 'begDate')
#                setDatetimeEditValue(dialogF090.edtEndDate, dialogF090.edtEndTime, newRecord, 'endDate')
#                setDoubleBoxValue(dialogF090.edtAmount, newRecord, 'amount')
#                setDoubleBoxValue(dialogF090.edtUet, newRecord, 'uet')
#                setRBComboBoxValue(dialogF090.cmbPerson, newRecord, 'person_id')
#                setRBComboBoxValue(dialogF090.cmbSetPerson, newRecord, 'setPerson_id')
                dialogF090.exec_()
                if dialogF090.isBtnSave:
                    result = True
                    eventId = dialogF090.eventId
                    actionId = dialogF090.itemId()
            finally:
                dialogF090.deleteLater()
    return result, eventId, actionId


class CF090CreateDialog(CF090EditDialog):
    def __init__(self, parent):
        CF090EditDialog.__init__(self, parent, isCreate=True)
        self.setIsFillPersonValueUserId(True)
        self.setIsFillPersonValueFinished(False)


    def getHurtTypeIdList(self):
        hurtTypeId = None
        if self.clientId:
            db = QtGui.qApp.db
            tableCW       = db.table('ClientWork')
            tableCWH      = db.table('ClientWork_Hurt')
            tableHurtType = db.table('rbHurtType')
            queryTable = tableCW.innerJoin(tableCWH, tableCWH['master_id'].eq(tableCW['id']))
            queryTable = queryTable.innerJoin(tableHurtType, tableHurtType['id'].eq(tableCWH['hurtType_id']))
            cond = [tableCW['client_id'].eq(self.clientId),
                    tableCW['deleted'].eq(0)
                    ]
            if self.hurtTypeCond:
                cond.append(self.hurtTypeCond)
            hurtTypeIdList = db.getDistinctIdList(queryTable, [tableHurtType['id']], cond)
            if len(hurtTypeIdList) > 1:
                dialog = CHurtTypeDialog(self, hurtTypeIdList)
                try:
                    dialog.setWindowTitle(u'Выполняемые работы из регистрационной карты пациента')
                    if dialog.exec_():
                        hurtTypeId = dialog.getCheckedId()
                finally:
                    dialog.deleteLater()
            else:
                hurtTypeId = hurtTypeIdList[0] if hurtTypeIdList else None
            self.cmbHurtType.setValue(hurtTypeId)


    def load(self, record, action, clientId = None, recordEvent = None, preDiagnostics = [], preSpecialityIdList = [], isSelectionGroupOne = False):
        self.clientId = clientId
        self.action = action
        self.getHurtTypeSetTable(self.action)
        self.getHurtTypeIdList()
        actionType = self.action.getType() if self.action else None
        self.actionTypeId = actionType.id if actionType else None
        self.recordEvent = recordEvent
        self.initNewData()
#        self.chkEpidemicIndications.setReadOnly(self.isProtected)
        self.setRecord(record)
        if not preDiagnostics:
            dlg = CPreF001Dialog(self, self.contractTariffCache)
            try:
                dlg.setBegDateEvent(self.eventSetDateTime.date() if isinstance(self.eventSetDateTime, QDateTime) else self.eventSetDateTime)
                dlg.prepare(self.clientId, self.eventTypeId, self.eventSetDateTime.date(), self.personId, self.personSpecialityId, self.personTariffCategoryId)
                #self.loadDiagnostics(dlg.modelDiagnostics.items(), self.eventId)
                self.preDiagnostics = dlg.modelDiagnostics.items()
                self.modelDiagnostics.setPreSpecialityIdList(dlg.preSpecialityIdList)
                self.modelDiagnostics.isSelectionGroupOne = dlg.isSelectionGroupOne
            finally:
                dlg.deleteLater()
        else:
            self.preDiagnostics = preDiagnostics
            self.modelDiagnostics.setPreSpecialityIdList(preSpecialityIdList)
            self.modelDiagnostics.isSelectionGroupOne = isSelectionGroupOne
        if not self.preDiagnostics:
            self.prepareDiagnositics()
        if self.preDiagnostics:
            self.prepareDiagnostics(self.preDiagnostics, addVisit = True)
        #self.setComboBoxes()
        #self.setIsDirty(False)


    def prepareDiagnositics(self):
        if self.personId and self.personSpecialityId:
            db = QtGui.qApp.db
            tablePerson = db.table('Person')
            personRecord = db.getRecordEx(tablePerson, [tablePerson['post_id']], [tablePerson['id'].eq(self.personId), tablePerson['deleted'].eq(0)])
            postId = forceRef(personRecord.value('post_id')) if personRecord else None
            defaultSceneId = getEventSceneId(self.eventTypeId) if self.eventTypeId else None
            if not defaultSceneId:
                tableRBScene = db.table('rbScene')
                defaultSceneId = forceRef(db.translate(tableRBScene, 'code', '1', 'id'))
            item = self.modelDiagnostics.getEmptyRecord()
            item.setValue('speciality_id',  toVariant(self.personSpecialityId))
            item.setValue('post_id',        toVariant(postId))
            item.setValue('person_id',      toVariant(self.personId))
            item.setValue('scene_id',       toVariant(defaultSceneId))
            item.setValue('selectionGroup', toVariant(1))
            item.setValue('price',          toVariant(0.0))
            self.preDiagnostics.append(item)


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
        self.eventPurposeId = None
        self.eventSetDate = None
        self.eventSetDateTime = None
        self.eventDate = None
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
        self.orgId = currentOrgId
        if not self.clientId:
            self.clientId = self.getClientId(self.eventId) if self.eventId else None
        if self.recordEvent and not self.eventId:
            self.eventId = forceRef(self.recordEvent.value('id'))
            self.eventTypeId = forceRef(self.recordEvent.value('eventType_id'))
            self.action.getRecord().setValue('event_id', toVariant(self.eventId))
        if self.eventTypeId:
            recordEventType = db.getRecordEx(tableEventType, [tableEventType['id'], tableEventType['order'], tableEventType['isPrimary']], [tableEventType['id'].eq(self.eventTypeId), tableEventType['deleted'].eq(0)])
            order = forceInt(recordEventType.value('order')) if recordEventType else 0
            isPrimary = forceInt(recordEventType.value('isPrimary')) if recordEventType else 0
        if self.eventId and not self.recordEvent:
            self.recordEvent = db.getRecordEx(tableEvent, '*', [tableEvent['id'].eq(self.eventId), tableEvent['deleted'].eq(0)])
        if not self.recordEvent:
            if not self.eventTypeId:
                recordEventType = db.getRecordEx(tableEventType, [tableEventType['id'], tableEventType['order'], tableEventType['isPrimary']], [tableEventType['form'].like(u'090'), tableEventType['deleted'].eq(0)], u'EventType.id')
                self.eventTypeId = forceRef(recordEventType.value('id')) if recordEventType else None
                order = forceInt(recordEventType.value('order')) if recordEventType else 0
                isPrimary = forceInt(recordEventType.value('isPrimary')) if recordEventType else 0
            if self.eventTypeId:
                self.recordEvent = tableEvent.newRecord()
                self.recordEvent.setValue('id', toVariant(None))
                self.recordEvent.setValue('createDatetime', toVariant(QDateTime.currentDateTime()))
                self.recordEvent.setValue('createPerson_id',toVariant(QtGui.qApp.userId))
                self.recordEvent.setValue('modifyDatetime', toVariant(QDateTime.currentDateTime()))
                self.recordEvent.setValue('modifyPerson_id',toVariant(QtGui.qApp.userId))
                self.recordEvent.setValue('setDate',        toVariant(QDateTime.currentDateTime()))
                self.recordEvent.setValue('execDate',       toVariant(QDateTime.currentDateTime()))
                self.recordEvent.setValue('eventType_id',   toVariant(self.eventTypeId))
                self.recordEvent.setValue('relegatePerson_id', toVariant(QtGui.qApp.userId))
                self.recordEvent.setValue('relegateOrg_id', toVariant(QtGui.qApp.currentOrgId()))
                self.recordEvent.setValue('isPrimary', toVariant(isPrimary))
                self.recordEvent.setValue('order', toVariant(order))
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
        if self.eventTypeId:
            self.eventPurposeId = getEventPurposeId(self.eventTypeId)
        if self.eventPurposeId:
            resultColIndex = self.modelDiagnostics.getColIndex('result_id', None)
            if resultColIndex >= 0:
                self.modelDiagnostics.cols()[resultColIndex].setFilter(u'''rbDiagnosticResult.eventPurpose_id=%d'''%(self.eventPurposeId))
        if self.recordEvent and self.clientId and not forceRef(self.recordEvent.value('client_id')):
            self.recordEvent.setValue('client_id', toVariant(self.clientId))
        self.getActionTypeToEventType()
        actionType = self.action.getType()
        if not self.isActionSave:
            self.setComboBoxes()
        self.isRelationRepresentativeSetClientId = True
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
        record = self.preFillingActionRecord090(self.recordEvent, record, self.actionTypeId, actionType.amount, financeId=None, contractId=None, orgStructureId=None)
        setDatetimeEditValue(self.edtDirectionDate,    self.edtDirectionTime,    record, 'directionDate')
        setDatetimeEditValue(self.edtPlannedEndDate,   self.edtPlannedEndTime,   record, 'plannedEndDate')
        setDatetimeEditValue(self.edtBegDate,          self.edtBegTime,          record, 'begDate')
        setDatetimeEditValue(self.edtEndDate,          self.edtEndTime,          record, 'endDate')
        setDate = forceDateTime(record.value('begDate')) if record else None
        execDate = forceDateTime(record.value('endDate')) if record else None
        self.recordEvent.setValue('setDate', toVariant(setDate))
        if execDate and execDate.isValid():
            self.recordEvent.setValue('isClosed', toVariant(1))
        self.recordEvent.setValue('execDate', toVariant(execDate))
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
                       self.buttonBox.button(QtGui.QDialogButtonBox.Save)
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
        self.edtDirectionDate.setEnabled(not self.isProtected)
        self.edtDirectionTime.setEnabled(bool(self.edtDirectionDate.date()) and not self.isProtected)
        self.chkIsUrgent.setReadOnly(self.isProtected)
        self.initDateParamsFilter(self.edtEndDate.date())
        self.setProperties(isCreate=True)
        self.tabNotes.setEventEditor(self)
        self.tabNotes.initContract()
        if self.recordEvent:
            self.tabNotes.setNotes(self.recordEvent)
        self.modelMembersMSIPerson.setAction(self.action)
        self.modelInfectionDiseases.setAction(self.action)
        self.modelClientDiseases.setAction(self.action)
        self.modelVaccinations.setAction(self.action)
        self.modelClientVaccinations.setAction(self.action)
        self.modelStatusActions.setAction(self.action)
        self.modelClientStatusActions.setAction(self.action)
        self.modelLabDiagnosticActions.setAction(self.action)
        self.modelToolDiagnosticActions.setAction(self.action)
        self.modelClientDiagnosticActions.setAction(self.action)
        self.modelExport.setIdList([])
#        self.tblInfectionDiseases.setRowHidden(1, True)
        self.tblInfectionDiseases.resizeColumnToContents(2)
#        self.tblClientDiseases.setRowHidden(1, True)
        self.tblClientDiseases.resizeColumnToContents(4)
        self.isActionSave = False
        self.setIsDirty(False)
        self.getInfectionVaccinations()
        self.getPostIdList()
        self.getNomenclativeServiceIdList()


    @pyqtSignature('int')
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


