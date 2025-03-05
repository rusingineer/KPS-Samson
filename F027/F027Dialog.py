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
##
## Форма 027: "Протокол"
##
#############################################################################

from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import Qt, QDate, QDateTime, QModelIndex, QObject, QTime, QVariant, pyqtSignature, SIGNAL

from Events.RelatedEventAndActionListDialog import CRelatedEventAndActionListDialog
from library.Attach.AttachAction  import getAttachAction
from library.crbcombobox        import CRBComboBox
from library.ICDInDocTableCol   import CICDExInDocTableCol
from library.ICDMorphologyInDocTableCol import CMKBMorphologyCol
from library.InDocTable           import CMKBListInDocTableModel, CBoolInDocTableCol, CInDocTableCol, CRBInDocTableCol
from library.interchange          import getDatetimeEditValue, getLineEditValue, getRBComboBoxValue, setDatetimeEditValue, setRBComboBoxValue

from library.PrintInfo            import CInfoProxyList, CDateInfo, CDateTimeInfo
from library.PrintTemplates       import applyTemplate, customizePrintButton, getPrintButton
from library.TNMS.TNMSComboBox    import CTNMSCol
from library.MKBExSubclassComboBox import CMKBExSubclassCol
from library.Utils                import copyFields, forceBool, forceDate, forceInt, forceRef, forceString, formatNum, toVariant, variantEq, forceStringEx

from Events.ActionEditDialog      import CActionEditDialog
from Events.Action                import CAction, CActionType, CActionTypeCache, getActionDefaultAmountEx
from Events.ActionInfo            import CCookedActionInfo, CLocActionInfoList
from Events.ActionPropertiesTable import CActionPropertiesTableModel
from Events.ActionsSummaryModel import CFxxxActionsSummaryModel
from Events.ActionStatus          import CActionStatus
from Events.DiagnosisType       import CDiagnosisTypeCol
from Events.EventEditDialog     import CEventEditDialog, CDiseaseCharacter, CDiseaseStage, CDiseasePhases, CToxicSubstances, getToxicSubstancesIdListByMKB
from Events.EventInfo             import CCureMethodInfo, CCureTypeInfo, CDiagnosticInfoProxyList, CEventInfo, CEventTypeInfo, CPatientModelInfo, CResultInfo
from Events.Utils                 import checkDiagnosis, checkIsHandleDiagnosisIsChecked, CTableSummaryActionsMenuMixin, getAvailableCharacterIdByMKB, getDiagnosisId2, getEventContext, getEventContextData, getEventDurationRange, getEventMesRequired, getEventName, getEventPeriodEx, getEventPurposeId, getEventResultId, getEventServiceId, getEventSetPerson, getEventShowTime, getHealthGroupFilter, setActionPropertiesColumnVisible, setAskedClassValueForDiagnosisManualSwitch, getEventIsPrimary, getActionTypeIdListByFlatCode, getEventTypeForm
from F025.PreF025Dialog           import CPreF025Dialog, CPreF025DagnosticAndActionPresets
from Orgs.OrgComboBox             import CPolyclinicComboBox
from Orgs.Orgs                    import selectOrganisation
from Orgs.PersonComboBoxEx        import CPersonFindInDocTableCol
from Orgs.PersonInfo              import CPersonInfo
from Orgs.Utils import getOrganisationShortName, getPersonOrgStructureChiefs, COrgInfo, getPersonChiefs
from Registry.AmbCardMixin      import getClientActions
from Registry.Utils               import CClientInfo
from Users.Rights                 import urAccessF025planner, urAccessF090planner, urAdmin, urEditSubservientPeopleAction, urEditEndDateEvent, urEditOtherpeopleAction, urRegTabWriteRegistry, urRegTabReadRegistry, urCanReadClientVaccination, urCanEditClientVaccination, urEditOtherPeopleActionSpecialityOnly

from F027.Ui_F027                 import Ui_Dialog


class CProtocolEventEditDialog(CEventEditDialog):


    def getEventInfo(self, context, infoClass=CEventInfo):
        selfId = self.itemId()
        if selfId is None:
            selfId = False
        result = context.getInstance(CEventInfo, selfId)

        date = self.eventDate if self.eventDate else QDate.currentDate()
        record = self.record()
        showTime = getEventShowTime(self.eventTypeId)
        dateInfoClass = CDateTimeInfo if showTime else CDateInfo
        # инициализация свойств
        result._eventType = context.getInstance(CEventTypeInfo, self.eventTypeId)
        result._externalId = self.getExternalId()
        result._org = context.getInstance(COrgInfo, self.orgId)
        result._relegateOrg = context.getInstance(COrgInfo, self.getRelegateOrgId())
        result._curator = context.getInstance(CPersonInfo, self.getCuratorId())
        result._assistant = context.getInstance(CPersonInfo, self.getAssistantId())
        result._client = context.getInstance(CClientInfo, self.clientId, date)
        result._order = self.cmbOrder.currentIndex()+1 if hasattr(self, 'cmbOrder') else 0
        result._prevEventDate = dateInfoClass(self.getPrevEventDateTime())
        result._setDate = dateInfoClass(self.getSetDateTime())
        result._setPerson = context.getInstance(CPersonInfo, self.getSetPersonId())
        result._execDate = dateInfoClass(self.getExecDateTime())
        result._execPerson = context.getInstance(CPersonInfo, self.getExecPersonId())
        result._result = context.getInstance(CResultInfo, self.cmbResult.value())
        result._nextEventDate = None
        result._contract = None
        result._tariffDescr = None
        result._localContract = None
        result._mes = None
        result._mesSpecification = None
        result._note = self.getNote()
        result._payStatus = record.value('payStatus') if record else 0
        result._patientModel = context.getInstance(CPatientModelInfo, self.getPatientModelId())
        result._cureType     = context.getInstance(CCureTypeInfo, self.getCureTypeId())
        result._cureMethod   = context.getInstance(CCureMethodInfo, self.getCureMethodId())
        # формальная инициализация таблиц
        result._actions = []
        result._diagnosises = []
        result._visits = []
        result._ok = True
        result._loaded = True
        self.setupVisitsIsExposedPopupMenu()
        return result


    def setEventTypeId(self, eventTypeId, title='', titleF027= ''):
        self.eventTypeId = eventTypeId
        self.eventTypeName  = getEventName(eventTypeId)
        self.eventPurposeId = getEventPurposeId(eventTypeId)
        self.eventServiceId = getEventServiceId(eventTypeId)
        self.eventPeriod    = getEventPeriodEx(eventTypeId)
        self.eventContext   = getEventContext(eventTypeId)
        self.mesRequired    = getEventMesRequired(eventTypeId)

        orgName = getOrganisationShortName(self.orgId)
        eventPurposeName = forceString(QtGui.qApp.db.translate('rbEventTypePurpose', 'id', self.eventPurposeId, 'name'))
        self.setWindowTitle(u'%s %s %s - %s: %s' % (title, orgName, titleF027, eventPurposeName, self.eventTypeName))
        if hasattr(self, 'tblActions'):
            if title != u'Ф.001':
                self.addObject('actAPActionsAdd', QtGui.QAction(u'Добавить ...', self))
                self.actAPActionsAdd.setShortcut(Qt.Key_F9)
                #self.mnuAction.addAction(self.actAPActionsAdd)
                self.connect(self.actAPActionsAdd, SIGNAL('triggered()'), self.on_actAPActionsAdd_triggered)


    def getServiceActionCode(self):
        return None


    def getExternalId(self):
        return forceString(self.edtEventExternalIdValue.text())

    def getCuratorId(self):
        return self.cmbEventCurator.value()


    def getAssistantId(self):
        return self.cmbEventAssistant.value()


    def getPatientModelId(self):
        return self.cmbPatientModel.value()


    def getCureTypeId(self):
        return self.cmbCureType.value()


    def getCureMethodId(self):
        return self.cmbCureMethod.value()


    def getRelegateOrgId(self):
        return self.cmbRelegateOrg.value()


class CF027Dialog(CProtocolEventEditDialog, Ui_Dialog, CTableSummaryActionsMenuMixin):
    defaultEventResultId = None
    defaultDiagnosticResultId = None
    dfAccomp = 2 # Сопутствующий

    @pyqtSignature('')
    def on_actActionEdit_triggered(self): CTableSummaryActionsMenuMixin.on_actActionEdit_triggered(self)
    @pyqtSignature('')
    def on_actAPActionAddSuchAs_triggered(self): CTableSummaryActionsMenuMixin.on_actAPActionAddSuchAs_triggered(self)
    @pyqtSignature('')
    def on_actDeleteRow_triggered(self): CTableSummaryActionsMenuMixin.on_actDeleteRow_triggered(self)
    @pyqtSignature('')
    def on_actUnBindAction_triggered(self): CTableSummaryActionsMenuMixin.on_actUnBindAction_triggered(self)

    def __init__(self, parent):
# ctor
        CProtocolEventEditDialog.__init__(self, parent)
        self.mapSpecialityIdToDiagFilter = {}
        self.notSetCmbResult = False

# create models
        self.addModels('PreliminaryDiagnostics', CF003PreliminaryDiagnosticsModel(self))
        self.addModels('FinalDiagnostics',       CF003FinalDiagnosticsModel(self))
        self.addModels('ActionsSummary',         CFxxxActionsSummaryModel(self))
        self.addModels('APActionProperties',     CActionPropertiesTableModel(self))
# ui
        self.createSaveAndCreateAccountButton()
        self.addObject('actEditClient', QtGui.QAction(u'Открыть регистрационную карточку', self))
        self.addObject('actPortal_Doctor', QtGui.QAction(u'Перейти на портал врача', self))
        self.addObject('actShowAttachedToClientFiles', getAttachAction('Client_FileAttach',  self))
        self.addObject('actShowContingentsClient', QtGui.QAction(u'Показать все наблюдаемые контингенты', self))
        self.addObject('actOpenClientVaccinationCard', QtGui.QAction(u'Открыть прививочную карту', self))
        self.addObject('btnPrint', getPrintButton(self, ''))
        # self.addObject('btnMedicalCommission', QtGui.QPushButton(u'ВК', self))
        self.addObject('btnPlanning', QtGui.QPushButton(u'Планировщик', self))
        self.addObject('btnRelatedEvent', QtGui.QPushButton(u'Связанные события', self))
        self.setupUi(self)

        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setWindowTitleEx(u'Осмотр Ф.027')
        self.tabToken.setFocusProxy(self.tblFinalDiagnostics)
        self.tabMisc.setEventEditor(self)
        self.tabMisc.setActionTypeClass(3)
        # self.buttonBox.addButton(self.btnMedicalCommission, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnRelatedEvent, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnPrint, QtGui.QDialogButtonBox.ActionRole)
        if QtGui.qApp.defaultKLADR()[:2] in ['23', '01']:
            self.buttonBox.addButton(self.btnPlanning, QtGui.QDialogButtonBox.ActionRole)
        self.setupSaveAndCreateAccountButton()
        self.setupActionSummarySlots()
# tables to rb and combo-boxes

# assign models
        self.tblPreliminaryDiagnostics.setModel(self.modelPreliminaryDiagnostics)
        self.tblFinalDiagnostics.setModel(self.modelFinalDiagnostics)
        self.tblActions.setModel(self.modelAPActionProperties)
        self.modelActionsSummary.addModel(self.tabMisc.modelAPActions)

# popup menus
        self.txtClientInfoBrowser.actions.append(self.actEditClient)
        self.txtClientInfoBrowser.actions.append(self.actPortal_Doctor)
        self.txtClientInfoBrowser.actions.append(self.actShowAttachedToClientFiles)
        self.txtClientInfoBrowser.actions.append(self.actShowContingentsClient)
        self.txtClientInfoBrowser.actions.append(self.actOpenClientVaccinationCard)
        self.actOpenClientVaccinationCard.setEnabled(QtGui.qApp.userHasAnyRight([urCanReadClientVaccination, urCanEditClientVaccination]))
        self.actEditClient.setEnabled(QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]))
        self.tblPreliminaryDiagnostics.addCopyDiagnosisToFinal(self)
#        CTableSummaryActionsMenuMixin.__init__(self)

# default values
#        db = QtGui.qApp.db
#        table = db.table('rbScene')
        self.setupDirtyCather()
        self.setIsDirty(False)
        self.blankMovingIdList = []
        self.clientId = None
        self.prolongateEvent = False
        self.prevEventId = None
        self.cmbCureType.setTable('rbCureType')
        self.cmbCureMethod.setTable('rbCureMethod')
        self.cmbPatientModel.setEventEditor(self)
        self.valueForAllActionEndDate = None
        self.postSetupUi()
        if hasattr(self, 'edtEndDate'):
            self.edtEndDate.setEnabled(QtGui.qApp.userHasRight(urEditEndDateEvent))
        if hasattr(self, 'edtEndTime'):
            self.edtEndTime.setEnabled(QtGui.qApp.userHasRight(urEditEndDateEvent))
# done


        for actionsTab in self.getActionsTabsList():
            self.connect(actionsTab, SIGNAL('APSetPersonIdChanged()'), self.on_APSetPersonIdChanged)
        self.connect(self.modelActionsSummary, SIGNAL('APSetPersonIdChanged()'), self.on_APSetPersonIdChanged)


    # done

    def openMainActionInEditor(self):
        oldAction = self.modelAPActionProperties.action
        if oldAction:
            oldRecord = oldAction.getRecord()

            dialog = CActionEditDialog(self)

            dialog.save = lambda: True

            dialog.setForceClientId(self.clientId)

            dialog.setRecord(QtSql.QSqlRecord(oldRecord))

            dialog.setReduced(True)

            self.copyAction(oldAction, dialog.action)

            if dialog.exec_():
                self.modelAPActionProperties.action = dialog.action
                self.modelAPActionProperties.emitDataChanged()

                record = dialog.getRecord()

                setDatetimeEditValue(self.edtBegDate, self.edtBegTime, record, 'begDate')
                setDatetimeEditValue(self.edtEndDate, self.edtEndTime, record, 'endDate')
                self.cmbPersonManager.setValue(forceRef(record.value('person_id')))
                self.cmbPersonMedicineHead.setValue(forceRef(record.value('setPerson_id')))
                self.cmbPersonExpert.setValue(forceRef(record.value('assistant_id')))



    def copyAction(self, sourceAction, targetAction):
        targetAction._propertiesByName.clear()
        targetAction._propertiesById.clear()
        targetAction._executionPlan.clear()
        targetAction._properties = []

        for sourceProperty in sourceAction.getProperties():
            sourcePropertyTypeId = sourceProperty.type().id
            targetProperty = targetAction.getPropertyById(sourcePropertyTypeId)
            targetProperty.copy(sourceProperty)


    def destroy(self):
        CEventEditDialog.deleteLater(self)
        self.tblPreliminaryDiagnostics.setModel(None)
        self.tblFinalDiagnostics.setModel(None)
        self.tblActions.setModel(None)
        self.tabMisc.deleteLater()
        del self.modelPreliminaryDiagnostics
        del self.modelFinalDiagnostics
        del self.modelActionsSummary
        self.tabAmbCard.deleteLater()


    def keyPressEvent(self, event):
        key = event.key()
        if hasattr(self, 'tabWidget'):
            widget = self.tabWidget.currentWidget()
            cond = []
            if hasattr(self, 'tabToken'):
                cond.append(self.tabToken)
            if widget in cond:
                if key == Qt.Key_F2:
                    self.openMainActionInEditor()
        CProtocolEventEditDialog.keyPressEvent(self, event)



    def setEventDataPlanning(self, eventData):
        pass


    def updatePropTable(self, action):
        self.tblActions.model().setAction(action, self.clientId, self.clientSex, self.clientAge, self.eventTypeId)
        self.tblActions.resizeRowsToContents()


    def btnRelatedEventHighlight(self):
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        tablePWS = db.table('vrbPersonWithSpeciality')
        tableCreatePWS = db.table('vrbPersonWithSpeciality').alias('CPWS')
        tableActionType = db.table('ActionType')
        tableAction = db.table('Action')
        cols = [tableEvent['id'].alias('eventId')]

        cond = [tableEvent['deleted'].eq(0),
                tableEventType['context'].like(u'relatedAction%'),
                tableAction['deleted'].eq(0),
                tableEvent['client_id'].eq(self.clientId)
                ]

        table = tableEvent.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
        table = table.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
        table = table.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
        table = table.leftJoin(tablePWS, tablePWS['id'].eq(tableAction['person_id']))
        table = table.leftJoin(tableCreatePWS, tableCreatePWS['id'].eq(tableAction['createPerson_id']))
        record = db.getRecordEx(table, cols, cond)

        if record:
            self.btnRelatedEvent.setStyleSheet("""
                QPushButton {
                    background-color: #F28a64;
                }
                QPushButton:hover {
                    background-color: #F6b096;
                }
            """)
        else:
            self.btnRelatedEvent.setGraphicsEffect(None)
            self.btnRelatedEvent.setStyleSheet("")


    @pyqtSignature('')
    def on_btnRelatedEvent_clicked(self):
        currentEventId = self.itemId()
        if not currentEventId:
            QtGui.QMessageBox.warning(self, u'Внимание!',
                                      u'Для доступа к связанным событиям необходимо сохранить текущее событие',
                                      QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
        else:
            self.relDialog = CRelatedEventAndActionListDialog(self, currentEventId, self.prevEventId)
            self.relDialog.exec_()
            self.relDialog.deleteLater()


    def createAction(self):
        eventId = self.itemId()
        action = None
        if self.clientId:
            db = QtGui.qApp.db
            tableAction = db.table('Action')
            record = None
            actionTypeIdList = getActionTypeIdListByFlatCode(u'protocol')
            if eventId and actionTypeIdList:
                cond = [tableAction['deleted'].eq(0),
                        tableAction['event_id'].eq(eventId),
                        tableAction['actionType_id'].eq(actionTypeIdList[0])
                        ]
                record = db.getRecordEx(tableAction, '*', cond)
                if record:
                    
                    action = CAction(record=record)
                    setDatetimeEditValue(self.edtBegDate, self.edtBegTime, record, 'begDate')
                    setDatetimeEditValue(self.edtEndDate, self.edtEndTime, record, 'endDate')
                    self.cmbPersonManager.setValue(forceRef(record.value('person_id')))
                    self.cmbPersonMedicineHead.setValue(forceRef(record.value('setPerson_id')))
                    self.cmbPersonExpert.setValue(forceRef(record.value('assistant_id')))
            if not record:
                actionTypeId = actionTypeIdList[0] if len(actionTypeIdList) else None
                if actionTypeId:
                    record = tableAction.newRecord()
                    record.setValue('event_id', toVariant(eventId))
                    record.setValue('actionType_id', toVariant(actionTypeId))
                    record.setValue('begDate', toVariant(QDateTime(self.edtBegDate.date(), self.edtBegTime.time())))
                    record.setValue('endDate', toVariant(QDateTime(self.edtEndDate.date(), self.edtEndTime.time())))
                    record.setValue('status',  toVariant(2))
                    record.setValue('person_id', toVariant(self.cmbPersonManager.value()))
                    record.setValue('setPerson_id', toVariant(self.cmbPersonMedicineHead.value()))
                    record.setValue('assistant_id', toVariant(self.cmbPersonExpert.value()))
                    record.setValue('org_id',  toVariant(QtGui.qApp.currentOrgId()))
                    record.setValue('amount',  toVariant(1))
                    action = CAction(record=record)
            if action:
                status = forceInt(record.value('status'))
                personManagerId = self.cmbPersonManager.value()
                personId = self.cmbPerson.value()
                personMedicineHeadId = self.cmbPersonMedicineHead.value()
                eventCuratorId = self.cmbEventCurator.value()
                personExpertId = self.cmbPersonExpert.value()
                eventAssistantId = self.cmbEventAssistant.value()
                if status == CActionStatus.finished and (personId or personManagerId or personMedicineHeadId or eventCuratorId or personExpertId or eventAssistantId):
                    personSpecialityId = self.getSpecialityId(personId)
                    action._locked = not ( QtGui.qApp.userId == personId
                                     or QtGui.qApp.userId == personManagerId
                                     or QtGui.qApp.userId == personMedicineHeadId
                                     or QtGui.qApp.userId == eventCuratorId
                                     or QtGui.qApp.userId == personExpertId
                                     or QtGui.qApp.userId == eventAssistantId
                                     or QtGui.qApp.userHasRight(urEditOtherpeopleAction)
                                     or (QtGui.qApp.userHasRight(urEditOtherPeopleActionSpecialityOnly) and QtGui.qApp.userSpecialityId == personSpecialityId)
                                     or QtGui.qApp.userId in getPersonChiefs(personId)
                                     or (QtGui.qApp.userHasRight(urEditSubservientPeopleAction) and QtGui.qApp.userId in getPersonOrgStructureChiefs(personId))
                                   )
                else:
                    self._locked = False
                setActionPropertiesColumnVisible(action._actionType, self.tblActions)
                self.updatePropTable(action)
                canEdit = not action.isLocked() if action else True
                self.tblActions.setEnabled(canEdit)
        return action

    def getSpecialityId(self, personId):
        specialityId = None
        if personId:
            db = QtGui.qApp.db
            tablePerson = db.table('Person')
            record = db.getRecordEx(tablePerson, [tablePerson['speciality_id']], [tablePerson['deleted'].eq(0), tablePerson['id'].eq(personId)])
            specialityId = forceRef(record.value('speciality_id')) if record else None
        return specialityId

    def _prepare(self, clientId, eventTypeId, orgId, personId, eventSetDatetime, eventDatetime, weekProfile, numDays,
                 presetDiagnostics, presetActions, disabledActions, externalId, assistantId, curatorId,
                 actionTypeIdValue = None, valueProperties = [], relegateOrgId = None, relegatePersonId=None,
                 diagnos = None, financeId = None, protocolQuoteId = None, actionByNewEvent = [], order = 1,
                 relegateInfo=[], plannedEndDate = None, isEdit = False):
        if not isEdit:
            self.eventSetDateTime = eventSetDatetime if isinstance(eventSetDatetime, QDateTime) else QDateTime(eventSetDatetime)
            self.eventDate = eventDatetime.date() if isinstance(eventDatetime, QDateTime) else eventDatetime


            self.setOrgId(orgId if orgId else QtGui.qApp.currentOrgId())
            self.setEventTypeId(eventTypeId)
            self.setClientId(clientId)
            self.prolongateEvent = True if actionByNewEvent else False
            self.cmbRelegateOrg.setValue(relegateOrgId)
            self.edtEventExternalIdValue.setText(externalId)
            self.cmbEventAssistant.setValue(assistantId)
            self.cmbEventCurator.setValue(curatorId)
            self.setExternalId(externalId)
            self.cmbPerson.setValue(personId)
            setPerson = getEventSetPerson(self.eventTypeId)
            if setPerson == 0:
                self.setPerson = personId
            elif setPerson == 1:
                self.setPerson = QtGui.qApp.userId
            self.edtBegDate.setDate(self.eventSetDateTime.date())
            self.edtBegTime.setTime(eventSetDatetime.time() if isinstance(eventSetDatetime, QDateTime) else QTime())
            self.edtEndDate.setDate(self.eventDate)
            self.edtEndTime.setTime(eventDatetime.time() if isinstance(eventDatetime, QDateTime) else QTime())
            self.chkPrimary.setChecked(getEventIsPrimary(eventTypeId)==0)
            self.cmbOrder.setCurrentIndex(order)
            self.createAction()
            resultId = QtGui.qApp.session("F027_resultId")
            self.cmbResult.setValue(resultId)
            self.initFocus()

            if presetDiagnostics:
                for model in (self.modelPreliminaryDiagnostics, self.modelFinalDiagnostics):
                    for MKB, dispanserId, healthGroupId, visitTypeId in presetDiagnostics:
                        item = model.getEmptyRecord()
                        item.setValue('MKB', toVariant(MKB))
                        item.setValue('dispanser_id',   toVariant(dispanserId))
                        item.setValue('healthGroup_id', toVariant(healthGroupId))
                        characterIdList = getAvailableCharacterIdByMKB(MKB)
                        if characterIdList:
                            item.setValue('character_id', toVariant(characterIdList[0]))
                        model.items().append(item)
                    model.reset()
        self.prepareActions(presetActions, disabledActions, actionTypeIdValue, valueProperties, diagnos, financeId, protocolQuoteId, actionByNewEvent, plannedEndDate)
        self.setIsDirty(False)
        self.cmbPatientModel.setEventEditor(self)
        self.notSetCmbResult = True
        self.setFilterResult(self.eventSetDateTime.date())
        return True and self.checkDeposit()


    def prepare(self, clientId, eventTypeId, orgId, personId, eventSetDatetime, eventDatetime, weekProfile,
                numDays, externalId, assistantId, curatorId, flagHospitalization = False,
                actionTypeIdValue = None, valueProperties = [], tissueTypeId=None, selectPreviousActions=False,
                relegateOrgId = None, relegatePersonId=None, diagnos = None, financeId = None,
                protocolQuoteId = None, actionByNewEvent = [], order = 1,  actionListToNewEvent = [], typeQueue = -1,
                docNum=None, relegateInfo=[], plannedEndDate = None, mapJournalInfoTransfer = [], voucherParams = {}, isEdit=False):
        self.setPersonId(personId)
        eventDate = eventDatetime.date() if isinstance(eventDatetime, QDateTime) else eventDatetime
        if not eventDate and eventSetDatetime:
            eventDate = eventSetDatetime.date() if isinstance(eventSetDatetime, QDateTime) else eventSetDatetime
        else:
            eventDate = QDate.currentDate()
        presentActionTypes = []
        for item in self.modelActionsSummary.items():
            actionTypeId = forceString(item.value('actionType_id'))
            if actionTypeId not in presentActionTypes:
                presentActionTypes.append(actionTypeId)
        form = getEventTypeForm(eventTypeId)
        if (form != u'090' and QtGui.qApp.userHasRight(urAccessF025planner)) or (form == u'090' and QtGui.qApp.userHasAnyRight([urAccessF090planner,])):
            dlg = CPreF025Dialog(self)
            try:
                dlg.setBegDateEvent(eventSetDatetime.date() if isinstance(eventSetDatetime, QDateTime) else eventSetDatetime)
                dlg.prepare(clientId, eventTypeId, eventDate, self.personId, self.personSpecialityId, self.personTariffCategoryId, 
                            flagHospitalization, actionTypeIdValue, tissueTypeId, presentActionTypes = presentActionTypes)
                if dlg.diagnosticsTableIsNotEmpty() or dlg.actionsTableIsNotEmpty():
                    if not dlg.exec_():
                        return False
                return self._prepare(clientId, eventTypeId, orgId, personId, eventSetDatetime, eventDatetime, weekProfile,
                                     numDays, dlg.diagnostics(), dlg.actions(), dlg.disabledActionTypeIdList, externalId,
                                     assistantId, curatorId, actionTypeIdValue, valueProperties, relegateOrgId, relegatePersonId,
                                     diagnos, financeId, protocolQuoteId, actionByNewEvent, order, relegateInfo, plannedEndDate, isEdit)
            finally:
                dlg.deleteLater()
        else:
            presets = CPreF025DagnosticAndActionPresets(clientId, eventTypeId, eventDate, self.personSpecialityId, flagHospitalization, actionTypeIdValue, presentActionTypes = presentActionTypes)
            presets.setBegDateEvent(eventSetDatetime.date() if isinstance(eventSetDatetime, QDateTime) else eventSetDatetime)
            return self._prepare(clientId, eventTypeId, orgId, personId, eventSetDatetime, eventDatetime, weekProfile, numDays,
                                 presets.unconditionalDiagnosticList, presets.unconditionalActionList, presets.disabledActionTypeIdList,
                                 externalId, assistantId, curatorId, None, [], relegateOrgId, relegatePersonId,
                                 diagnos, financeId, protocolQuoteId, actionByNewEvent, order, relegateInfo, plannedEndDate, isEdit)


    def getQuotaTypeId(self):
        quotaTypeId = None
        action = self.tblActions.model().action
        if action:
            propertiesByIdList = action._actionType._propertiesById
            for propertiesBy in propertiesByIdList.values():
                if u'квота пациента' in propertiesBy.typeName.lower():
                    propertiesById = propertiesBy.id
                    if propertiesById:
                        quotaId = action._propertiesById[propertiesById].getValue()
                        if quotaId:
                            db = QtGui.qApp.db
                            tableClientQuoting = db.table('Client_Quoting')
                            record = db.getRecordEx(tableClientQuoting, [tableClientQuoting['quotaType_id']], [tableClientQuoting['deleted'].eq(0), tableClientQuoting['id'].eq(quotaId)])
                            if record:
                                quotaTypeId = forceRef(record.value('quotaType_id'))
        return quotaTypeId


    def getEventDataPlanning(self, eventId):
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableAction = db.table('Action')
        tableActionType = db.table('ActionType')
        tableEventType = db.table('EventType')
        cond =[ tableActionType['flatCode'].like(u'hospitalDirection'),
                tableActionType['deleted'].eq(0)
              ]
        actionTypeList = db.getIdList(tableActionType, 'id', cond)
        if eventId:
            cols = [tableEvent['patientModel_id'],
                    tableEvent['cureType_id'],
                    tableEvent['cureMethod_id'],
                    tableEvent['contract_id'],
                    tableEvent['externalId'],
                    tableEvent['note'],
                    tableEvent['setDate'],
                    tableEventType['name']
                    ]
            cond = [tableEvent['deleted'].eq(0),
                    tableEvent['id'].eq(eventId)
                    ]
            table = tableEvent.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
            record = db.getRecordEx(table, cols, cond)
            if record:
                patientModelId = forceRef(record.value('patientModel_id'))
                if patientModelId:
                    self.cmbPatientModel.setValue(patientModelId)
                cureTypeId = forceRef(record.value('cureType_id'))
                if cureTypeId:
                    self.cmbCureType.setValue(cureTypeId)
                cureMethodId = forceRef(record.value('cureMethod_id'))
                if cureMethodId:
                    self.cmbCureMethod.setValue(cureMethodId)
                if self.prolongateEvent:
                    #self.cmbContract.setValue(forceRef(record.value('contract_id')))
                    self.edtEventExternalIdValue.setText(forceString(record.value('externalId')))
                    self.tabNotes.edtEventNote.setText(forceString(record.value('note')))
                    self.prevEventId = eventId
                    self.lblProlongateEvent.setText(u'п')
                    self.tabNotes.edtPrevEventInfo.setText(u'Продолжение обращения: %s от %s.'%(forceString(record.value('name')), forceDate(record.value('setDate')).toString('dd.MM.yyyy')))
            if actionTypeList:
                cols = [tableAction['person_id']]
                cond = [tableAction['event_id'].eq(eventId),
                        tableAction['deleted'].eq(0),
                        tableAction['actionType_id'].inlist(actionTypeList),
                        tableAction['endDate'].isNotNull()
                        ]
                record = db.getRecordEx(tableAction, cols, cond, 'Action.endDate DESC')
                if record:
                    personId = forceRef(record.value('person_id'))
                    if personId:
                        tablePerson = db.table('Person')
                        tableRBPost = db.table('rbPost')
                        queryTable = tablePerson.innerJoin(tableRBPost, tablePerson['post_id'].eq(tableRBPost['id']))
                        recordPerson = db.getRecordEx(queryTable, ['''IF(rbPost.code < '3', 1, 0) AS codePost'''], [tablePerson['deleted'].eq(0), tablePerson['id'].eq(personId)])
                        if recordPerson:
                            codePost = forceInt(recordPerson.value('codePost'))
                            if codePost:
                                self.cmbPersonManager.setValue(personId)
            if self.prolongateEvent:
                self.loadEventDiagnostics(self.modelPreliminaryDiagnostics, self.prevEventId)
            else:
                self.createDiagnostics(eventId)
        else:
            if self.clientId:
                tableActionProperty = db.table('ActionProperty')
                tableActionPT = db.table('ActionPropertyType')
                tableActionPS = db.table('ActionProperty_String')
                if actionTypeList:
                    table = tableEvent.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
                    cols = [tableAction['id'].alias('actionId'),
                            tableAction['event_id'].alias('eventId'),
                            tableAction['actionType_id'].alias('actionTypeId'),
                            tableAction['person_id']
                            ]
                    cond = [tableEvent['client_id'].eq(self.clientId),
                            tableEvent['deleted'].eq(0),
                            tableAction['deleted'].eq(0),
                            tableAction['actionType_id'].inlist(actionTypeList),
                            tableAction['endDate'].isNotNull()
                            ]
                    record = db.getRecordEx(table, cols, cond, 'Action.endDate DESC')
                    if record:
                        personId = forceRef(record.value('person_id'))
                        if personId:
                            tablePerson = db.table('Person')
                            tableRBPost = db.table('rbPost')
                            queryTable = tablePerson.innerJoin(tableRBPost, tablePerson['post_id'].eq(tableRBPost['id']))
                            recordPerson = db.getRecordEx(queryTable, ['''IF(rbPost.code < '3', 1, 0) AS codePost'''], [tablePerson['deleted'].eq(0), tablePerson['id'].eq(personId)])
                            if recordPerson:
                                codePost = forceInt(recordPerson.value('codePost'))
                                if codePost:
                                    self.cmbPersonManager.setValue(personId)
                        actionId = forceRef(record.value('actionId'))
                        prevEventId = forceRef(record.value('eventId'))
                        actionTypeId = forceRef(record.value('actionTypeId'))
                        cols = [tableActionPS['value'].alias('diagnos')]
                        cond = [tableActionPT['actionType_id'].eq(actionTypeId),
                                tableActionPT['deleted'].eq(0),
                                tableActionPT['name'].like(u'Диагноз'),
                                tableActionProperty['action_id'].eq(actionId),
                                tableActionProperty['deleted'].eq(0)
                                ]
                        table = tableActionProperty.innerJoin(tableActionPT, tableActionPT['id'].eq(tableActionProperty['type_id']))
                        table = table.innerJoin(tableActionPS, tableActionPS['id'].eq(tableActionProperty['id']))
                        record = db.getRecordEx(table, cols, cond)
                        if record:
                            diagnos = forceString(record.value('diagnos'))
                            if diagnos:
                                action = self.tblActions.model().action
                                if action:
                                    action[u'Диагноз'] = diagnos
                        if prevEventId:
                            self.loadEventDiagnostics(self.modelPreliminaryDiagnostics, prevEventId)


    def createDiagnostics(self, eventId):
        if eventId:
            self.loadDiagnostics(self.modelPreliminaryDiagnostics, eventId)
            self.loadDiagnostics(self.modelFinalDiagnostics, eventId)


    def prepareActions(self, presetActions, disabledActions, actionTypeIdValue, valueProperties, diagnos, financeId, protocolQuoteId, actionByNewEvent, plannedEndDate=None):
        def addActionType(actionTypeId, amount, idListActionType, idListActionTypeIPH, actionFinance, idListActionTypeMoving, plannedEndDate):
            db = QtGui.qApp.db
            tableOrgStructure = db.table('OrgStructure')
            for iModel, tab in enumerate(self.getActionsTabsList()):
                model = tab.modelAPActions
                if actionTypeId in model.actionTypeIdList:
                    if actionTypeId in idListActionType and not actionByNewEvent:
                        model.addRow(actionTypeId, amount)
                        i = self.modelActionsSummary.itemIndex.index((iModel, model.rowCount()-2))
                        self.onActionChanged(i)
                        record, action = model.items()[-1]
                        # if plannedEndDate:
                        #     record.setValue('directionDate', QVariant(plannedEndDate))
                        if u'Приемное отделение' in action._actionType._propertiesByName:
                            curOrgStructureId = QtGui.qApp.currentOrgStructureId()
                            if curOrgStructureId:
                                recOS = db.getRecordEx(tableOrgStructure,
                                               [tableOrgStructure['id']],
                                               [tableOrgStructure['deleted'].eq(0),
                                                tableOrgStructure['id'].eq(curOrgStructureId),
                                                tableOrgStructure['type'].eq(4)])
                                if recOS:
                                    curOSId = forceRef(recOS.value('id'))
                                    action[u'Приемное отделение'] = curOSId if curOSId else None
                        if valueProperties and len(valueProperties) > 0 and valueProperties[0]:
                            action[u'Направлен в отделение'] = valueProperties[0]
                        if protocolQuoteId:
                            action[u'Квота'] = protocolQuoteId
                        if actionFinance == 0:
                            record.setValue('finance_id', toVariant(financeId))
                    elif actionTypeId in idListActionTypeIPH:
                        model.addRow(actionTypeId, amount)
                        i = self.modelActionsSummary.itemIndex.index((iModel, model.rowCount()-2))
                        self.onActionChanged(i)
                        record, action = model.items()[-1]
                        if diagnos:
                            record, action = model.items()[-1]
                            action[u'Диагноз'] = diagnos
                    #[self.eventActionFinance, self.receivedFinanceId, orgStructureTransfer, orgStructurePresence, oldBegDate, movingQuoting, personId]
                    elif actionByNewEvent and actionTypeId in idListActionTypeMoving:
                        model.addRow(actionTypeId, amount)
                        i = self.modelActionsSummary.itemIndex.index((iModel, model.rowCount()-2))
                        self.onActionChanged(i)
                        record, action = model.items()[-1]
                        if actionByNewEvent[0] == 0:
                            record.setValue('finance_id', toVariant(actionByNewEvent[1]))
                        action[u'Отделение пребывания'] = actionByNewEvent[2]
                        if actionByNewEvent[3]:
                            action[u'Переведен из отделения'] = actionByNewEvent[3]
                        if actionByNewEvent[4]:
                            record.setValue('begDate', toVariant(actionByNewEvent[4]))
                        else:
                            record.setValue('begDate', toVariant(QDateTime.currentDateTime()))
                        if u'Квота' in action._actionType._propertiesByName and actionByNewEvent[5]:
                            action[u'Квота'] = actionByNewEvent[5]
                        if actionByNewEvent[6]:
                            record.setValue('person_id', toVariant(actionByNewEvent[6]))
                    elif (actionByNewEvent and actionTypeId not in idListActionType) or not actionByNewEvent:
                        model.addRow(actionTypeId, amount)
                        i = self.modelActionsSummary.itemIndex.index((iModel, model.rowCount()-2))
                        self.onActionChanged(i)
                        record, action = model.items()[-1]

        def disableActionType(actionTypeId):
            for model in (self.tabStatus.modelAPActions,
                          self.tabDiagnostic.modelAPActions,
                          self.tabCure.modelAPActions,
                          self.tabMisc.modelAPActions):
                if actionTypeId in model.actionTypeIdList:
                    model.disableActionType(actionTypeId)
                    break

        if disabledActions:
            for actionTypeId in disabledActions:
                disableActionType(actionTypeId)
        if presetActions:
            db = QtGui.qApp.db
            tableActionType = db.table('ActionType')
            tableEventType = db.table('EventType')
            idListActionType = db.getIdList(tableActionType, [tableActionType['id']], [tableActionType['flatCode'].like(u'received%'), tableActionType['deleted'].eq(0)])
            idListActionTypeIPH = db.getIdList(tableActionType, [tableActionType['id']], [tableActionType['flatCode'].like(u'inspectPigeonHole%'), tableActionType['deleted'].eq(0)])
            idListActionTypeMoving = db.getIdList(tableActionType, [tableActionType['id']], [tableActionType['flatCode'].like(u'moving%'), tableActionType['deleted'].eq(0)])
            eventTypeId = self.getEventTypeId()
            actionFinance = None
            if eventTypeId:
                recordET = db.getRecordEx(tableEventType, [tableEventType['actionFinance']], [tableEventType['deleted'].eq(0), tableEventType['id'].eq(eventTypeId)])
                actionFinance = forceInt(recordET.value('actionFinance')) if recordET else None
            if actionByNewEvent:
                actionTypeMoving = False
                for actionTypeId, amount, cash in presetActions:
                    if actionTypeId in idListActionTypeMoving:
                        actionTypeMoving = True
                        break
                if not actionTypeMoving and idListActionTypeMoving:
                    presetActions.append((idListActionTypeMoving[0], 1.0, False))
            for actionTypeId, amount, cash in presetActions:
                addActionType(actionTypeId, amount, idListActionType, idListActionTypeIPH, actionFinance, idListActionTypeMoving)


    def setLeavedAction(self, actionTypeIdValue, params = {}):
        currentDateTime = params.get('ExecDateTime', QDateTime.currentDateTime())
        person = params.get('ExecPerson', None)
        result = params.get('ExecResult', None)
        hospitalBedId = None
        flatCode = [u'moving', u'received']
        db = QtGui.qApp.db
        tableActionType = db.table('ActionType')
        idListActionType = db.getIdList(tableActionType, [tableActionType['id']], [tableActionType['flatCode'].inlist(flatCode), tableActionType['deleted'].eq(0)])
        for model in (self.tabMisc.modelAPActions, ):
            if actionTypeIdValue in model.actionTypeIdList:
                orgStructureLeaved = None
                movingQuoting = None
                orgStructureMoving = False
                for record, action in model.items():
                    actionTypeId = forceRef(record.value('actionType_id'))
                    if actionTypeId in idListActionType:
                        if not forceDate(record.value('endDate')):
                            record.setValue('endDate', toVariant(currentDateTime))
                            record.setValue('status', toVariant(2))
                        actionType = CActionTypeCache.getById(actionTypeId) if actionTypeId else None
                        if u'moving' in actionType.flatCode.lower():
                            orgStructureMoving = True
                            orgStructurePresence = action[u'Отделение пребывания']
                            orgStructureTransfer = action[u'Переведен в отделение']
                            hospitalBedId = action[u'койка']
                            if not person:
                                person = forceInt(record.value('person_id'))
                            movingQuoting = action[u'Квота'] if u'Квота' in action._actionType._propertiesByName else None
                            if not orgStructureTransfer and orgStructurePresence:
                                orgStructureLeaved = orgStructurePresence
                        else:
                            orgStructureLeaved = None
                            movingQuoting = None
                        amount = actionType.amount
                        if actionTypeId:
                            if not(amount and actionType.amountEvaluation == CActionType.userInput):
                                amount = getActionDefaultAmountEx(self, actionType, record, action)
                        else:
                            amount = 0
                        record.setValue('amount', toVariant(amount))
                        model.updateActionAmount(len(model.items())-1)
                model.addRow(actionTypeIdValue)
                record, action = model.items()[-1]
                if not orgStructureLeaved and not orgStructureMoving:
                    currentOrgStructureId = QtGui.qApp.currentOrgStructureId()
                    if currentOrgStructureId:
                        typeRecord = QtGui.qApp.db.getRecordEx('OrgStructure', 'type', 'id = %d AND type = 4 AND deleted = 0'%(currentOrgStructureId))
                        if typeRecord and (typeRecord.value('type')) == 4:
                            orgStructureLeaved = currentOrgStructureId
                if orgStructureLeaved and u'Отделение' in action._actionType._propertiesByName:
                    action[u'Отделение'] = orgStructureLeaved
                if u'Квота' in action._actionType._propertiesByName and movingQuoting:
                    action[u'Квота'] = movingQuoting
                if person:
                    record.setValue('person_id', toVariant(person))
                if result:
                    action[u'Исход госпитализации'] = result
                if hospitalBedId:
                    tableOSHB = db.table('OrgStructure_HospitalBed')
                    recordProfile = db.getRecordEx(tableOSHB, [tableOSHB['profile_id']], [tableOSHB['id'].eq(hospitalBedId)])
                    if recordProfile:
                        profileId = forceRef(recordProfile.value('profile_id'))
                        if u'Профиль' in action._actionType._propertiesByName and profileId:
                            action[u'Профиль'] = profileId
                record.setValue('begDate', toVariant(currentDateTime))
                record.setValue('endDate', toVariant(currentDateTime))
                record.setValue('directionDate', toVariant(currentDateTime))
                record.setValue('status', toVariant(2))
                model.updateActionAmount(len(model.items())-1)
                if action._actionType.closeEvent:
                    self.edtEndDate.setDate(currentDateTime.date() if isinstance(currentDateTime, QDateTime) else QDate())
                    self.edtEndTime.setTime(currentDateTime.time() if isinstance(currentDateTime, QDateTime) else QTime())


    def initFocus(self):
        self.tblFinalDiagnostics.setFocus(Qt.OtherFocusReason)


    def newDiagnosticRecord(self, template):
        result = self.tblFinalDiagnostics.model().getEmptyRecord()
        return result


    def setRecord(self, record):
        CProtocolEventEditDialog.setRecord(self, record)
        setDatetimeEditValue(self.edtBegDate, self.edtBegTime, record, 'setDate')
        setDatetimeEditValue(self.edtEndDate, self.edtEndTime, record, 'execDate')
        setRBComboBoxValue(self.cmbPerson,    record, 'execPerson_id')
        self.chkPrimary.setChecked(forceInt(record.value('isPrimary'))==1)
        self.setExternalId(forceString(record.value('externalId')))
        self.cmbOrder.setCurrentIndex(forceInt(record.value('order'))-1)
        setRBComboBoxValue(self.cmbResult,    record, 'result_id')

        self.cmbRelegateOrg.setValue(forceRef(record.value('relegateOrg_id')))
        self.tabNotes.setId(self.edtEventExternalIdValue, record, 'externalId')
        setRBComboBoxValue(self.cmbEventAssistant, record, 'assistant_id')
        setRBComboBoxValue(self.cmbEventCurator, record, 'curator_id')
        setRBComboBoxValue(self.cmbPatientModel, record, 'patientModel_id')
        setRBComboBoxValue(self.cmbCureType, record, 'cureType_id')
        setRBComboBoxValue(self.cmbCureMethod, record, 'cureMethod_id')
        self.setPerson = forceRef(record.value('setPerson_id'))
        self._updateNoteByPrevEventId()

        self.setPersonId(self.cmbPerson.value())
        self.tabNotes.setNotes(record)
        self.loadDiagnostics(self.modelPreliminaryDiagnostics, self.itemId())
        self.loadDiagnostics(self.modelFinalDiagnostics, self.itemId())
        self.loadActions()
        self.cmbPatientModel.setEventEditor(self)
        self.createAction()
        self.on_cmbResult_currentIndexChanged()
        self.initFocus()
        self.setIsDirty(False)
        self.blankMovingIdList = []
        self.notSetCmbResult = (False if self.cmbResult.value() else True)
        self.protectClosedEvent()
        self.btnRelatedEventHighlight()


#    def loadEventDiagnostics(self, modelDiagnostics, eventId):
#        db = QtGui.qApp.db
#        tableDiagnostic = db.table('Diagnostic')
#        tableRBDiagnosisType = db.table('rbDiagnosisType')
#        table = tableDiagnostic.innerJoin(tableRBDiagnosisType, tableRBDiagnosisType['id'].eq(tableDiagnostic['diagnosisType_id']))
#        cond = [tableDiagnostic['deleted'].eq(0), tableDiagnostic['event_id'].eq(eventId)]
#        cond.append('''(rbDiagnosisType.code = '1'
#OR (rbDiagnosisType.code = '2'
#AND (NOT EXISTS (SELECT DC.id FROM Diagnostic AS DC
#INNER JOIN rbDiagnosisType AS DT ON DT.id = DC.diagnosisType_id WHERE DT.code = '1'
#AND DC.event_id = %s
#LIMIT 1))))'''%(str(eventId)))
#        rawItems = db.getRecordList(table, '*', cond, 'Diagnostic.id')
#        items = []
#        isDiagnosisManualSwitch = modelDiagnostics.manualSwitchDiagnosis()
#        for record in rawItems:
#            specialityId = forceRef(record.value('speciality_id'))
#            diagnosisId     = record.value('diagnosis_id')
#            MKB             = db.translate('Diagnosis', 'id', forceRef(diagnosisId), 'MKB')
#            MKBEx           = db.translate('Diagnosis', 'id', forceRef(diagnosisId), 'MKBEx')
#            morphologyMKB   = db.translate('Diagnosis', 'id', forceRef(diagnosisId), 'morphologyMKB')
#            setDate         = forceDate(record.value('setDate'))
#            TNMS            = forceString(record.value('TNMS'))
#            diagnosisTypeCode = forceString(record.value('code'))
#            newRecord =  modelDiagnostics.getEmptyRecord()
#            copyFields(newRecord, record)
#            newRecord.setValue('MKB',           MKB)
#            newRecord.setValue('MKBEx',         MKBEx)
#            newRecord.setValue('TNMS',          toVariant(TNMS))
#            newRecord.setValue('morphologyMKB', morphologyMKB)
#            if diagnosisTypeCode != 7:
#                diagnosisTypeId = db.translate('rbDiagnosisType', 'code', '7', 'id')
#                newRecord.setValue('diagnosisType_id', toVariant(diagnosisTypeId))
#            currentEventId = self.itemId()
#            if eventId != currentEventId:
#                newRecord.setValue('id', toVariant(None))
#                newRecord.setValue('event_id', toVariant(currentEventId))
#                newRecord.setValue('diagnosis_id', toVariant(None))
#                newRecord.setValue('handleDiagnosis', QVariant(0))
#            else:
#                if isDiagnosisManualSwitch:
#                    isCheckedHandleDiagnosis = checkIsHandleDiagnosisIsChecked(setDate,
#                                                                               self.clientId,
#                                                                               diagnosisId)
#                    newRecord.setValue('handleDiagnosis', QVariant(isCheckedHandleDiagnosis))
#
#            items.append(newRecord)
#        modelDiagnostics.setItems(items)


    def loadDiagnostics(self, modelDiagnostics, eventId):
        db = QtGui.qApp.db
        table = db.table('Diagnostic')
        rawItems = db.getRecordList(table, '*', [table['deleted'].eq(0), table['event_id'].eq(eventId), modelDiagnostics.filter], 'id')
        items = []
        isDiagnosisManualSwitch = modelDiagnostics.manualSwitchDiagnosis()
        for record in rawItems:
#            specialityId = forceRef(record.value('speciality_id'))
            diagnosisId     = record.value('diagnosis_id')
            MKB             = db.translate('Diagnosis', 'id', forceRef(diagnosisId), 'MKB')
            MKBEx           = db.translate('Diagnosis', 'id', forceRef(diagnosisId), 'MKBEx')
            exSubclassMKB   = db.translate('Diagnosis', 'id', forceRef(diagnosisId), 'exSubclassMKB')
            morphologyMKB   = db.translate('Diagnosis', 'id', forceRef(diagnosisId), 'morphologyMKB')
            setDate         = forceDate(record.value('setDate'))
            TNMS            = forceString(record.value('TNMS'))
            newRecord =  modelDiagnostics.getEmptyRecord()
            copyFields(newRecord, record)
            newRecord.setValue('MKB',           MKB)
            newRecord.setValue('MKBEx',         MKBEx)
            newRecord.setValue('exSubclassMKB', exSubclassMKB)
            newRecord.setValue('TNMS',          toVariant(TNMS))
            newRecord.setValue('morphologyMKB', morphologyMKB)
            modelDiagnostics.updateMKBTNMS(newRecord, MKB)
            modelDiagnostics.updateMKBToExSubclass(newRecord, MKB)
            currentEventId = self.itemId()
            if eventId != currentEventId:
                newRecord.setValue('id', toVariant(None))
                newRecord.setValue('event_id', toVariant(currentEventId))
                newRecord.setValue('diagnosis_id', toVariant(None))
                newRecord.setValue('handleDiagnosis', QVariant(0))
            else:
                if isDiagnosisManualSwitch:
                    isCheckedHandleDiagnosis = checkIsHandleDiagnosisIsChecked(setDate,
                                                                               self.clientId,
                                                                               diagnosisId)
                    newRecord.setValue('handleDiagnosis', QVariant(isCheckedHandleDiagnosis))

            items.append(newRecord)
        modelDiagnostics.setItems(items)
        modelDiagnostics.cols()[modelDiagnostics.getColIndex('healthGroup_id')].setFilter(getHealthGroupFilter(forceString(self.clientBirthDate.toString('yyyy-MM-dd')), forceString(self.eventSetDateTime.date().toString('yyyy-MM-dd'))))


    def loadActions(self):
        items = self.loadActionsInternal()
        self.tabMisc.loadActions(items.values())
        self.modelActionsSummary.regenerate()


    def getRecord(self):
        record = CProtocolEventEditDialog.getRecord(self)
        showTime = getEventShowTime(self.eventTypeId)
        self.getShowButtonAccount()
        self.getShowButtonTemperatureList()
        self.getShowButtonNomenclatureExpense()
        self.getShowButtonJobTickets()
#перенести в exec_ в случае успеха или в accept?
        CF027Dialog.defaultEventResultId = self.cmbResult.value()
        CF027Dialog.defaultDiagnosticResultId = self.modelFinalDiagnostics.resultId()

        getDatetimeEditValue(self.edtBegDate, self.edtBegTime, record, 'setDate', showTime)
        record.setValue('setPerson_id', self.setPerson)
        getDatetimeEditValue(self.edtEndDate, self.edtEndTime, record, 'execDate', showTime)
        getRBComboBoxValue(self.cmbPerson,      record, 'execPerson_id')
        getRBComboBoxValue(self.cmbResult,      record, 'result_id')
        record.setValue('isPrimary', toVariant(1 if self.chkPrimary.isChecked() else 2))
        record.setValue('order',  toVariant(self.cmbOrder.currentIndex()+1))
        if self.prolongateEvent:
            record.setValue('order', toVariant(5))
        record.setValue('relegateOrg_id', toVariant(self.cmbRelegateOrg.value()))
        getLineEditValue(self.edtEventExternalIdValue, record, 'externalId')
        getRBComboBoxValue(self.cmbEventAssistant, record, 'assistant_id')
        getRBComboBoxValue(self.cmbEventCurator, record, 'curator_id')
        getRBComboBoxValue(self.cmbPatientModel, record, 'patientModel_id')
        getRBComboBoxValue(self.cmbCureType, record, 'cureType_id')
        getRBComboBoxValue(self.cmbCureMethod, record, 'cureMethod_id')
        self.tabNotes.getNotes(record, self.eventTypeId)
        # Это хак: удаляем payStatus из записи
        result = type(record)(record) # copy record
        result.remove(result.indexOf('payStatus'))
        return result


    @pyqtSignature('')
    def on_btnSelectRelegateOrg_clicked(self):
        orgId = selectOrganisation(self, self.cmbRelegateOrg.value(), False, filter=CPolyclinicComboBox.filter)
        self.cmbRelegateOrg.updateModel()
        if orgId:
            self.cmbRelegateOrg.setValue(orgId)


    @pyqtSignature('int')
    def on_cmbResult_currentIndexChanged(self, index):
        if self.notSetCmbResult and self.cmbResult.code() == '1':
            db = QtGui.qApp.db
            tableActionType = db.table('ActionType')
            idListActionType = db.getIdList(tableActionType, [tableActionType['id']], [tableActionType['flatCode'].like(u'planning%'), tableActionType['deleted'].eq(0)])
            if idListActionType:
                actionTypeId = None
                for model in (self.tabMisc.modelAPActions, ):
                    for actionTypeId in idListActionType:
                        if actionTypeId in model.actionTypeIdList:
                            for record, action in model.items():
                                if actionTypeId == action._actionType.id:
                                    return
                res = QtGui.QMessageBox.warning(self,
                               u'Внимание!',
                               u'В событии отсутствует действие "Планирование".\nДобавить его?',
                               QtGui.QMessageBox.Ok|QtGui.QMessageBox.Cancel,
                               QtGui.QMessageBox.Cancel)
                if res == QtGui.QMessageBox.Ok:
                    personId = self.cmbPersonManager.value()
                    orgStructureId = forceRef(db.translate('Person', 'id', personId, 'orgStructure_id')) if personId else None
                    for model in (self.tabMisc.modelAPActions, ):
                        if actionTypeId in model.actionTypeIdList:
                            model.addRow(actionTypeId)
                            record, action = model.items()[-1]
                            if orgStructureId:
                                action[u'подразделение'] = orgStructureId
                            self.tabWidget.setCurrentIndex(1)
                            self.tabMisc.edtAPPlannedEndDate.setFocus(Qt.OtherFocusReason)
                        break
        self.notSetCmbResult = True


    def on_cmbPatientModel_valueChanged(self):
        patientModelId = self.cmbPatientModel.value()
        db = QtGui.qApp.db
        tablePatientModelItem = db.table('rbPatientModel_Item')
        cond = [tablePatientModelItem['master_id'].eq(patientModelId)]
        cureTypeIdList = db.getDistinctIdList(tablePatientModelItem, [tablePatientModelItem['cureType_id']], cond)
        if cureTypeIdList:
            self.cmbCureType.setFilter('rbCureType.id IN (%s)'%(u','.join(str(cureTypeId) for cureTypeId in cureTypeIdList if cureTypeId)))
            cureTypeId = self.cmbCureType.value()
            cond = [tablePatientModelItem['cureType_id'].eq(cureTypeId),
                    tablePatientModelItem['master_id'].eq(patientModelId)]
            cureMethodIdList = db.getDistinctIdList(tablePatientModelItem, [tablePatientModelItem['cureMethod_id']], cond)
            if cureMethodIdList:
                self.cmbCureMethod.setFilter('rbCureMethod.id IN (%s)'%(u','.join(str(cureMethodId) for cureMethodId in cureMethodIdList if cureMethodId)))
            else:
                cond = [tablePatientModelItem['master_id'].eq(patientModelId)]
                cureMethodIdList = db.getDistinctIdList(tablePatientModelItem, [tablePatientModelItem['cureMethod_id']], cond)
                if cureMethodIdList:
                    self.cmbCureMethod.setFilter('rbCureMethod.id IN (%s)'%(u','.join(str(cureMethodId) for cureMethodId in cureMethodIdList if cureMethodId)))
                else:
                    self.cmbCureMethod.setFilter('rbCureMethod.id IS NULL')
            self.cmbCureMethod.setCurrentIndex(0)
        else:
            self.cmbCureType.setFilter('rbCureType.id IS NULL')
        self.cmbCureType.setCurrentIndex(0)


    @pyqtSignature('int')
    def on_cmbCureType_currentIndexChanged(self, index):
        db = QtGui.qApp.db
        cureTypeId = self.cmbCureType.value()
        patientModelId = self.cmbPatientModel.value()
        tablePatientModelItem = db.table('rbPatientModel_Item')
        if cureTypeId:
            cond = [tablePatientModelItem['cureType_id'].eq(cureTypeId),
                    tablePatientModelItem['master_id'].eq(patientModelId)]
            cureMethodIdList = db.getDistinctIdList(tablePatientModelItem, [tablePatientModelItem['cureMethod_id']], cond)
            if cureMethodIdList:
                self.cmbCureMethod.setFilter('rbCureMethod.id IN (%s)'%(u','.join(str(cureMethodId) for cureMethodId in cureMethodIdList if cureMethodId)))
            else:
                self.cmbCureMethod.setFilter('rbCureMethod.id IS NULL')
        elif patientModelId:
            cond = [tablePatientModelItem['master_id'].eq(patientModelId)]
            cureMethodIdList = db.getDistinctIdList(tablePatientModelItem, [tablePatientModelItem['cureMethod_id']], cond)
            if cureMethodIdList:
                self.cmbCureMethod.setFilter('rbCureMethod.id IN (%s)'%(u','.join(str(cureMethodId) for cureMethodId in cureMethodIdList if cureMethodId)))
            else:
                self.cmbCureMethod.setFilter('rbCureMethod.id IS NULL')
        else:
            self.cmbCureMethod.setFilter('rbCureMethod.id IS NULL')
        self.cmbCureMethod.setCurrentIndex(0)


    def saveInternals(self, eventId):
        self.saveDiagnostics(self.modelPreliminaryDiagnostics, eventId)
        self.saveDiagnostics(self.modelFinalDiagnostics, eventId)
        setAskedClassValueForDiagnosisManualSwitch(None)
        self.saveActions(eventId)
        self.saveBlankUsers(self.blankMovingIdList)
        #self.tabNotes.saveAttachedFiles(eventId)
        self.saveTrailerActions(eventId)


    def saveTrailerActions(self, eventId):
        if self.trailerActions:
            for action in self.trailerActions:
                prevActionId = self.trailerIdList.get(action.trailerIdx - 1, None)
                action.getRecord().setValue('prevAction_id', toVariant(prevActionId))
                action.save(eventId)


    def afterSave(self):
        CEventEditDialog.afterSave(self)
        QtGui.qApp.session("F027_resultId", self.cmbResult.value())


    def saveDiagnostics(self, modelDiagnostics, eventId):
        items = modelDiagnostics.items()
        isDiagnosisManualSwitch = modelDiagnostics.manualSwitchDiagnosis()
#        isFirst = True
        begDate = self.edtBegDate.date()
        endDate = self.edtEndDate.date()
        date = endDate if endDate else begDate

#        personIdVariant = toVariant(self.personId)
#        specialityIdVariant = QtGui.qApp.db.translate('Person', 'id', personIdVariant, 'speciality_id')
        MKBDiagnosisIdPairList = []
        prevId=0
        for item in items:
            MKB = forceStringEx(item.value('MKB'))
            MKBEx = forceStringEx(item.value('MKBEx'))
            TNMS = forceStringEx(item.value('TNMS'))
            morphologyMKB = forceStringEx(item.value('morphologyMKB'))
            diagnosisTypeId = forceRef(item.value('diagnosisType_id'))
            personId = forceRef(item.value('person_id'))
            specialityId = forceRef(QtGui.qApp.db.translate('Person', 'id', personId, 'speciality_id'))
            item.setValue('speciality_id', toVariant(specialityId))
            item.setValue('setDate', toVariant(begDate))
            item.setValue('endDate', toVariant(endDate))
            diagnosisId = forceRef(item.value('diagnosis_id'))
            characterId = forceRef(item.value('character_id'))
            diagnosisId, characterId = getDiagnosisId2(
                date,
                self.personId,
                self.clientId,
                diagnosisTypeId,
                MKB,
                MKBEx,
                forceRef(item.value('character_id')),
                forceRef(item.value('dispanser_id')),
                forceRef(item.value('traumaType_id')),
                diagnosisId,
                forceRef(item.value('id')),
                isDiagnosisManualSwitch,
                forceBool(item.value('handleDiagnosis')),
                TNMS=TNMS,
                morphologyMKB=morphologyMKB,
                dispanserBegDate=forceDate(item.value('endDate')),
                exSubclassMKB=forceStringEx(item.value('exSubclassMKB')))
            item.setValue('diagnosis_id', toVariant(diagnosisId))
            item.setValue('TNMS', toVariant(TNMS))
            item.setValue('character_id', toVariant(characterId))
            itemId = forceInt(item.value('id'))
            if prevId>itemId:
                item.setValue('id', QVariant())
                prevId=0
            else:
               prevId=itemId
#            isFirst = False
            MKBDiagnosisIdPairList.append((MKB, diagnosisId))
        modelDiagnostics.saveItems(eventId)
        self.modifyDiagnosises(MKBDiagnosisIdPairList)


    def getFinalDiagnosisMKB(self):
        MKB, MKBEx = self.modelFinalDiagnostics.getFinalDiagnosisMKB()
        if not MKB:
            MKB, MKBEx = self.modelPreliminaryDiagnostics.getFinalDiagnosisMKB()
        return MKB, MKBEx


    def getFinalDiagnosisId(self):
        id = self.modelFinalDiagnostics.getFinalDiagnosisId()
        if not id:
            id = self.modelPreliminaryDiagnostics.getFinalDiagnosisId()
        return id


    def saveActions(self, eventId):
        self.tabMisc.saveActions(eventId)
        self.saveAPropertys(eventId)


    def saveAPropertys(self, eventId):
        if self.modelAPActionProperties.action:
            record = self.modelAPActionProperties.action._record
            record.setValue('event_id', toVariant(eventId))
            record.setValue('begDate', toVariant(QDateTime(self.edtBegDate.date(), self.edtBegTime.time())))
            record.setValue('endDate', toVariant(QDateTime(self.edtEndDate.date(), self.edtEndTime.time())))
            record.setValue('person_id', toVariant(self.cmbPersonManager.value()))
            record.setValue('setPerson_id', toVariant(self.cmbPersonMedicineHead.value()))
            record.setValue('assistant_id', toVariant(self.cmbPersonExpert.value()))
            self.modelAPActionProperties.action.save()


    def setOrgId(self, orgId):
        self.orgId = orgId
        self.cmbPerson.setOrgId(orgId)
        self.tabMisc.setOrgId(orgId)


    def setOrgStructureTitle(self):
        title = u''
        orgStructureName = u''
        eventId = self.itemId()
        if eventId:
            db = QtGui.qApp.db
            tableAPHB = db.table('ActionProperty_HospitalBed')
            tableAPT = db.table('ActionPropertyType')
            tableAP = db.table('ActionProperty')
            tableActionType = db.table('ActionType')
            tableAction = db.table('Action')
            tableEvent = db.table('Event')
            tableOSHB = db.table('OrgStructure_HospitalBed')
            tableOS = db.table('OrgStructure')
            cols = [tableEvent['id'].alias('eventId'),
                    tableOS['name'].alias('nameOS')
                   ]
            queryTable = tableActionType.innerJoin(tableAction, tableActionType['id'].eq(tableAction['actionType_id']))
            queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.innerJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
            queryTable = queryTable.innerJoin(tableAP, tableAP['type_id'].eq(tableAPT['id']))
            queryTable = queryTable.innerJoin(tableAPHB, tableAPHB['id'].eq(tableAP['id']))
            queryTable = queryTable.innerJoin(tableOSHB, tableOSHB['id'].eq(tableAPHB['value']))
            queryTable = queryTable.innerJoin(tableOS, tableOS['id'].eq(tableOSHB['master_id']))
            cond = [ tableActionType['flatCode'].like(u'moving%'),
                     tableAction['event_id'].eq(eventId),
                     tableAction['deleted'].eq(0),
                     tableEvent['deleted'].eq(0),
                     tableAP['deleted'].eq(0),
                     tableActionType['deleted'].eq(0),
                     tableAPT['deleted'].eq(0),
                     tableOS['deleted'].eq(0),
                     tableAPT['typeName'].like('HospitalBed'),
                     tableAP['action_id'].eq(tableAction['id'])
                   ]
            cond.append(u'Action.begDate = (SELECT MAX(A.begDate) AS begDateMax FROM ActionType AS AT INNER JOIN Action AS A ON AT.id=A.actionType_id INNER JOIN Event AS E ON A.event_id=E.id INNER JOIN ActionPropertyType AS APT ON APT.actionType_id=AT.id INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id INNER JOIN ActionProperty_HospitalBed AS APHB ON APHB.id=AP.id INNER JOIN OrgStructure_HospitalBed AS OSHB ON OSHB.id=APHB.value INNER JOIN OrgStructure AS OS ON OS.id=OSHB.master_id WHERE (AT.flatCode LIKE \'moving%%\') AND (APT.typeName LIKE \'HospitalBed\') AND (A.deleted=0) AND (E.deleted=0) AND (AP.deleted=0) AND (AT.deleted=0) AND (APT.deleted=0) AND (OS.deleted=0) AND (AP.action_id=Action.id) AND (A.event_id = %d))'%(eventId))
            recordsMoving = db.getRecordList(queryTable, cols, cond)
            for record in recordsMoving:
                eventIdRecord = forceRef(record.value('eventId'))
                if eventId == eventIdRecord:
                    orgStructureName = u'подразделение: ' + forceString(record.value('nameOS'))
            title = orgStructureName
            def findTitle(flatCode, flatTitle):
                cols = [tableEvent['id'].alias('eventId'),
                        tableAction['id']
                       ]
                queryTable = tableActionType.innerJoin(tableAction, tableActionType['id'].eq(tableAction['actionType_id']))
                queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
                queryTable = queryTable.innerJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
                queryTable = queryTable.innerJoin(tableAP, tableAP['type_id'].eq(tableAPT['id']))
                cond = [ tableActionType['flatCode'].like(flatCode),
                         tableAction['deleted'].eq(0),
                         tableAction['event_id'].eq(eventId),
                         tableEvent['deleted'].eq(0),
                         tableAP['deleted'].eq(0),
                         tableActionType['deleted'].eq(0),
                         tableAPT['deleted'].eq(0),
                         tableAP['action_id'].eq(tableAction['id'])
                       ]
                group = u'Event.id, Action.`id`'
                recordsReceived = db.getRecordListGroupBy(queryTable, cols, cond, group)
                for record in recordsReceived:
                    eventIdRecord = forceRef(record.value('eventId'))
                    if eventId == eventIdRecord:
                       actionId = forceRef(record.value('id'))
                       if actionId:
                          return  flatTitle
                return  u''
            if title == u'':
                title = findTitle(u'received%', u'ПРИЕМНЫЙ ПОКОЙ')
            if title == u'':
                title = findTitle(u'planning%', u'ПЛАНИРОВАНИЕ')
        return title


    def setEventTypeId(self, eventTypeId):
        self.eventTypeId = eventTypeId
        titleF027 = self.setOrgStructureTitle()
        CProtocolEventEditDialog.setEventTypeId(self, eventTypeId, u'Ф.027', titleF027)
        showTime = getEventShowTime(eventTypeId)
        self.getShowButtonAccount()
        self.getShowButtonTemperatureList()
        self.getShowButtonNomenclatureExpense()
        self.getShowButtonJobTickets()
        self.edtBegTime.setVisible(showTime)
        self.edtEndTime.setVisible(showTime)
        self.cmbResult.setTable('rbResult', True, 'eventPurpose_id=\'%d\'' % self.eventPurposeId)
        # self.cmbResult.setValue(CF027Dialog.defaultEventResultId)
        cols = self.modelFinalDiagnostics.cols()
        resultCol = cols[len(cols)-1]
        resultCol.filter = 'eventPurpose_id=\'%d\'' % self.eventPurposeId
        customizePrintButton(self.btnPrint, self.eventContext if self.eventContext else 'F027')


    def resetActionTemplateCache(self):
        self.tabMisc.actionTemplateCache.reset()


    def checkDataEntered(self):
        result = CEventEditDialog.checkDataEntered(self)
        self.blankMovingIdList = []
#        mesRequired = getEventMesRequired(self.eventTypeId)
        result = result and (self.cmbPerson.value() or self.checkInputMessage(u'врача', False, self.cmbPerson))
        result = result and self.checkExecPersonSpeciality(self.cmbPerson.value(), self.cmbPerson)
        showTime = getEventShowTime(self.eventTypeId)
        begDateCheck = self.edtBegDate.date()
        endDateCheck = self.edtEndDate.date()
        if showTime:
            begDate = QDateTime(self.edtBegDate.date(), self.edtBegTime.time())
            endDate = QDateTime(self.edtEndDate.date(), self.edtEndTime.time())
        else:
            begDate = self.edtBegDate.date()
            endDate = self.edtEndDate.date()
        result = result and (begDate or self.checkInputMessage(u'дату назначения', False, self.edtBegDate))
        result = result and (not endDate or self.cmbResult.value() or self.checkInputMessage(u'результат', True, self.cmbResult))
        if not endDateCheck:
            pass
        else:
            result = result and self.checkActionDataEntered(begDate, QDateTime(), endDate, self.tabToken, self.edtBegDate, None, self.edtEndDate)
            result = result and self.checkEventDate(begDate, endDate, None, self.tabToken, None, self.edtEndDate, True)
            minDuration,  maxDuration = getEventDurationRange(self.eventTypeId)
            if minDuration<=maxDuration:
                result = result and (begDateCheck.daysTo(endDateCheck)+1>=minDuration or self.checkValueMessage(u'Длительность должна быть не менее %s'%formatNum(minDuration, (u'дня', u'дней', u'дней')), False, self.edtEndDate))
                result = result and (maxDuration==0 or begDateCheck.daysTo(endDateCheck)+1<=maxDuration or self.checkValueMessage(u'Длительность должна быть не более %s'%formatNum(maxDuration, (u'дня', u'дней', u'дней')), False, self.edtEndDate))
            result = result and self.checkExecPersonSpeciality(self.cmbPerson.value(), self.cmbPerson)
            #result = result and (len(self.modelFinalDiagnostics.items())>0 or self.checkInputMessage(u'диагноз', False, self.tblFinalDiagnostics))
        #result = result and self.checkDiagnosticsDataEntered(endDate)
        result = result and self.checkActionsDateEnteredActuality(begDate, endDate, [self.tabMisc])
        result = result and self.checkActionsPlanningDataEntered([self.tabMisc])
        result = result and self.checkActionsDataEntered(begDate, endDate)
        result = result and self.checkDeposit(True)
        result = result and self.checkActionsPropertiesDataEntered([self.tblActions])
        result = result and self.checkTabNotesEventExternalId()
        self.valueForAllActionEndDate = None
        if self.edtEndDate.date():
            result = result and self.checkAndUpdateExpertise(self.edtEndDate.date(), self.cmbPerson.value())
        result = result and self.selectNomenclatureAddedActions([self.tabMisc])
        return result
    

    def checkActionsPlanningDataEntered(self, tabList):
        for actionTab in tabList:
            model = actionTab.tblAPActions.model()
            for row, (record, action) in enumerate(model.items()):
                if action and action._actionType.id:
                    actionTypeItem = action.getType()
#                    nameActionType = action._actionType.name
                    if actionTypeItem and (u'planning' in actionTypeItem.flatCode.lower()):
                        endDate = forceDate(record.value('endDate'))
                        plannedEndDate = forceDate(record.value('plannedEndDate'))
                        if endDate and not plannedEndDate:
                            if not self.checkValueMessage(u'Введите плановую дату госпитализации', False, actionTab.tblAPActions, row, 0, actionTab.edtAPPlannedEndDate):
                                return False
        return True


    def checkActionsPropertiesDataEntered(self, tabList):
        for actionTab in tabList:
            model = actionTab.model()
            action = model.action
            if action and action._actionType.id:
                if not self.checkActionProperties(actionTab, action, actionTab):
                    return False
        return True


    def checkDiagnosticsDataEntered(self, endDate):
        result = True
        result = result and self.checkDiagnostics(self.modelPreliminaryDiagnostics, self.tblPreliminaryDiagnostics, None, endDate)
        result = result and self.checkDiagnostics(self.modelFinalDiagnostics, self.tblFinalDiagnostics, self.cmbPerson.value(), endDate)
        return result


    def checkDiagnostics(self, model, table, finalPersonId, endDate):
        for row, record in enumerate(model.items()):
            if not self.checkDiagnosticDataEntered(table, row, record, endDate):
                return False
        return True


    def checkDiagnosticDataEntered(self, table, row, record, endDate):
        result = True
        if result:
            MKB = forceString(record.value('MKB'))
            MKBEx = forceString(record.value('MKBEx'))
            personId = forceRef(record.value('person_id'))
            specialityId = forceRef(QtGui.qApp.db.translate('Person', 'id', personId, 'speciality_id'))
            result = specialityId or self.checkValueMessage(u'Отсутствует специальность врача', False, table, row, record.indexOf('person_id'))
            result = result and MKB or self.checkInputMessage(u'диагноз', False, table, row, record.indexOf('MKB'))
            result = result and self.checkActualMKB(table, self.edtBegDate.date(), MKB, record, row)
            if result:
                char = MKB[:1]
                blockMKB = forceInt(MKB[1:3])
                traumaTypeId = forceRef(record.value('traumaType_id'))
                if char in 'ST' and not (char in 'T' and 36 <= blockMKB <= 78):
                    if not traumaTypeId:
                        result = self.checkValueMessage(u'Необходимо указать тип травмы',  True if QtGui.qApp.controlTraumaType()==0 else False, self.tblFinalDiagnostics, row, record.indexOf('traumaType_id'))
                    if result:
                        result = MKBEx or self.checkInputMessage(u'Дополнительный диагноз', True if QtGui.qApp.controlMKBExForTraumaType()==0 else False, table, row, record.indexOf('MKBEx'))
                        if result:
                            charEx = MKBEx[:1]
                            if charEx not in 'VWXY':
                                result = self.checkValueMessage(u'Доп.МКБ не соотвествует Доп.МКБ при травме', True, table, row, record.indexOf('MKBEx'))
                if char not in 'ST' and traumaTypeId:
                    result = self.checkValueMessage(u'Необходимо удалить тип травмы', False, table, row, record.indexOf('traumaType_id'))
                result = self.checkRequiresFillingDispanser(result, table, record, row, MKB)
        if result and endDate and table == self.tblFinalDiagnostics:
            resultId = forceRef(record.value('result_id'))
            result = resultId or self.checkInputMessage(u'результат', False, self.tblFinalDiagnostics, row, record.indexOf('result_id'))
        result = result and self.checkPersonSpeciality(record, row, self.tblFinalDiagnostics)
        result = result and self.checkPeriodResultHealthGroup(record, row, self.tblFinalDiagnostics)
        return result


    def getDiagFilter(self):
        specialityId = self.personSpecialityId
        result = self.mapSpecialityIdToDiagFilter.get(specialityId, None)
        if result is None:
            result = QtGui.qApp.db.translate('rbSpeciality', 'id', specialityId, 'mkbFilter')
            if result is None:
                result = ''
            else:
                result = forceString(result)
            self.mapSpecialityIdToDiagFilter[specialityId] = forceString(result)
        return result


    def checkDiagnosis(self, MKB):
        diagFilter = self.getDiagFilter()
        return checkDiagnosis(self, MKB, diagFilter, self.clientId, self.clientSex, self.clientAge, self.edtBegDate.date())



    def getDiagnosisTypeId(self, dt):
        return forceRef(QtGui.qApp.db.translate('rbDiagnosisType', 'code', '2' if dt else '9', 'id'))


    def getEventInfo(self, context):
        result = CProtocolEventEditDialog.getEventInfo(self, context)
        # ручная инициализация свойств
        result._isPrimary = self.chkPrimary.isChecked()
        # ручная инициализация таблиц
        record = self.modelAPActionProperties.action._record if self.modelAPActionProperties.action else None
        if record:
            record.setValue('event_id', toVariant(self.itemId()))
            record.setValue('begDate', toVariant(QDateTime(self.edtBegDate.date(), self.edtBegTime.time())))
            record.setValue('endDate', toVariant(QDateTime(self.edtEndDate.date(), self.edtEndTime.time())))
            record.setValue('person_id', toVariant(self.cmbPersonManager.value()))
            record.setValue('setPerson_id', toVariant(self.cmbPersonMedicineHead.value()))
            record.setValue('assistant_id', toVariant(self.cmbPersonExpert.value()))
        #TODO: разобраться, зачем этот record нужен???
        result._actions = CActionInfoProxyListProtocol(context,
                [self.tabMisc.modelAPActions],
                self.modelAPActionProperties,
                result)
        result._diagnosises = CDiagnosticInfoProxyList(context, [self.modelPreliminaryDiagnostics, self.modelFinalDiagnostics])
        return result


    @pyqtSignature('int')
    def on_tabWidget_currentChanged(self, index):
        widget = self.tabWidget.widget(index)
        if widget is not None:
            focusProxy = widget.focusProxy()
            if focusProxy:
                focusProxy.setFocus(Qt.OtherFocusReason)
        if index == 2: # amb card page
            self.tabAmbCard.resetWidgets()


    @pyqtSignature('QDate')
    def on_edtBegDate_dateChanged(self, date):
        self.eventSetDateTime.setDate(QDate(date))
        self.setFilterResult(date)
        self.cmbPerson.setBegDate(self.eventSetDateTime.date())
        self.setPersonDate(self.eventSetDateTime.date())
        self.tabMisc.setEndDate(self.eventSetDateTime.date())
        self.emitUpdateActionsAmount()


    @pyqtSignature('QTime')
    def on_edtBegTime_timeChanged(self, time):
        self.eventSetDateTime.setTime(time)
        self.emitUpdateActionsAmount()


    @pyqtSignature('QDate')
    def on_edtEndDate_dateChanged(self, date):
        self.eventDate = QDate(date)
        self.cmbPerson.setEndDate(self.eventDate)
        self.emitUpdateActionsAmount()
        self.setEnabledChkCloseEvent(self.eventDate)
        if getEventShowTime(self.eventTypeId):
            time = QTime.currentTime() if date else QTime()
            self.edtEndTime.setTime(time)


    @pyqtSignature('QTime')
    def on_edtEndTime_timeChanged(self, time):
        self.emitUpdateActionsAmount()


    @pyqtSignature('int')
    def on_cmbPerson_currentIndexChanged(self):
        oldPersonId = self.personId
        self.setPersonId(self.cmbPerson.value())
# что-то сомнительным показалось - ну поменяли отв. врача,
# всё равно менять врачей в действии вроде неправильно. или правильно?
        self.tabMisc.updatePersonId(oldPersonId, self.personId)


    @pyqtSignature('')
    def on_modelFinalDiagnostics_resultChanged(self):
        if forceBool(QtGui.qApp.preferences.appPrefs.get('fillDiagnosticsEventsResults', True)):
            CF027Dialog.defaultDiagnosticResultId = self.modelFinalDiagnostics.resultId()
            self.cmbResult.setValue(getEventResultId(CF027Dialog.defaultDiagnosticResultId, self.eventPurposeId))


    @pyqtSignature('')
    def on_actDiagnosticsAddAccomp_triggered(self):
        currentRow = self.tblFinalDiagnostics.currentIndex().row()
        if currentRow>=0:
            currentRecord = self.modelFinalDiagnostics.items()[currentRow]
            newRecord = self.modelFinalDiagnostics.getEmptyRecord()
            newRecord.setValue('diagnosisType', QVariant(CF027Dialog.dfAccomp))
            newRecord.setValue('speciality_id', currentRecord.value('speciality_id'))
            newRecord.setValue('healthGroup_id', currentRecord.value('healthGroup_id'))
            self.modelFinalDiagnostics.insertRecord(currentRow+1, newRecord)
            self.tblFinalDiagnostics.setCurrentIndex(self.modelFinalDiagnostics.index(currentRow+1, newRecord.indexOf('MKB')))

    def on_actAPActionsAdd_triggered(self):
        pass

    @pyqtSignature('QModelIndex')
    def on_tblActions_doubleClicked(self, index):
        pass
#        row = index.row()
#        page, row = self.modelActionsSummary.itemIndex[row]
#        self.tabWidget.setCurrentIndex(page+2)
#        tbl = [self.tabMisc.tblAPActions][page]
#        tbl.setCurrentIndex(tbl.model().index(row, 0))

    @pyqtSignature('')
    def on_btnPlanning_clicked(self):
        actionListToNewEvent = []
        self.prepare(self.clientId, self.eventTypeId, self.orgId, self.personId, self.eventDate, self.eventDateNone, None, None, None, None, isEdit=True)
        self.initPrevEventTypeId(self.eventTypeId, self.clientId)
        self.initPrevEventId(None)
        self.addActions(actionListToNewEvent)

        
    @pyqtSignature('int')
    def on_btnPrint_printByTemplate(self, templateId):
        if self.checkPrintByTemplateAllowed(templateId):
            data = getEventContextData(self)
            clientInfo = data['client']
            idList = getClientActions(clientInfo.id, dict([]), 1)
            actions = CLocActionInfoList(clientInfo.context, idList, clientInfo.sexCode, clientInfo.ageTuple)
            data['all_actions'] = actions
            applyTemplate(self, templateId, data, signAndAttachHandler=None)


# # # Actions # # #

#
# #####################################################################################33
#

class CF003BaseDiagnosticsModel(CMKBListInDocTableModel):
    __pyqtSignals__ = ('diagnosisChanged()',
                      )
    MKB_allowed_morphology = ['C', 'D']

    def __init__(self, parent, finishDiagnosisTypeCode, baseDiagnosisTypeCode, accompDiagnosisTypeCode, complicDiagnosisTypeCode):
        CMKBListInDocTableModel.__init__(self, 'Diagnostic', 'id', 'event_id', parent)
        self._parent = parent
        self.isManualSwitchDiagnosis = QtGui.qApp.defaultIsManualSwitchDiagnosis()
        self.isMKBMorphology = QtGui.qApp.defaultMorphologyMKBIsVisible()
        self.characterIdForHandleDiagnosis = None
        self.diagnosisTypeCol = CF003DiagnosisTypeCol( u'Тип', 'diagnosisType_id', 2, [finishDiagnosisTypeCode, baseDiagnosisTypeCode, accompDiagnosisTypeCode, complicDiagnosisTypeCode], smartMode=False)
        self.addCol(self.diagnosisTypeCol)
        self.addCol(CPersonFindInDocTableCol(u'Врач', 'person_id',  20, 'vrbPersonWithSpecialityAndOrgStr', parent=parent))
        self.addExtCol(CICDExInDocTableCol(u'МКБ',         'MKB',   7), QVariant.String)
        if QtGui.qApp.isExSubclassMKBVisible():
            self.addExtCol(CMKBExSubclassCol(u'РСК', 'exSubclassMKB', 20), QVariant.String).setToolTip(u'Расширенная субклассификация МКБ')
        self.addExtCol(CICDExInDocTableCol(u'Доп.МКБ',     'MKBEx', 7), QVariant.String)
        if QtGui.qApp.isTNMSVisible():
            self.addCol(CTNMSCol(u'TNM-Ст', 'TNMS',  10))
        if self.isMKBMorphology:
            self.addExtCol(CMKBMorphologyCol(u'Морф.', 'morphologyMKB', 10, 'MKB_Morphology', filter='`group` IS NOT NULL'), QVariant.String)
        self.addCol(CDiseaseCharacter(     u'Хар',         'character_id',   7, showFields=CRBComboBox.showCode, preferredWidth=150)).setToolTip(u'Характер')
        if self.isManualSwitchDiagnosis:
            self.addExtCol(CBoolInDocTableCol( u'П',   'handleDiagnosis', 10), QVariant.Int)
            self.characterIdForHandleDiagnosis = forceRef(QtGui.qApp.db.translate('rbDiseaseCharacter', 'code', '1', 'id'))

        self.addCol(CDiseasePhases(        u'Фаза',        'phase_id',       7, showFields=CRBComboBox.showCode, preferredWidth=150)).setToolTip(u'Фаза')
        self.addCol(CDiseaseStage(         u'Ст',          'stage_id',       7, showFields=CRBComboBox.showCode, preferredWidth=150)).setToolTip(u'Стадия')
        self.addCol(CRBInDocTableCol(    u'ДН',            'dispanser_id',   7, 'rbDispanser', showFields=CRBComboBox.showCode, preferredWidth=150)).setToolTip(u'Диспансерное наблюдение')
#        self.addCol(CRBLikeEnumInDocTableCol(u'Госп',      'hospital',       7, CHospitalInfo.names, showFields=CRBComboBox.showCode, preferredWidth=150)).setToolTip(u'Потребность в госпитализации')
        self.addCol(CRBInDocTableCol(    u'Травма',        'traumaType_id', 10, 'rbTraumaType', addNone=True, showFields=CRBComboBox.showName, preferredWidth=150))
        self.addCol(CToxicSubstances(u'ТоксВещ', 'toxicSubstances_id', 10, addNone=True, showFields=CRBComboBox.showName, preferredWidth=150)).setToolTip(u'Токсичное вещество')
        self.addCol(CRBInDocTableCol(    u'ГрЗд',          'healthGroup_id', 7, 'rbHealthGroup', addNone=True, showFields=CRBComboBox.showCode, preferredWidth=150)).setToolTip(u'Группа здоровья')
        self.addCol(CInDocTableCol(u'Описание',     'freeInput', 15))
        self.columnHandleDiagnosis = self.getColIndex('handleDiagnosis', None)
        self.setFilter(self.table['diagnosisType_id'].inlist([id for id in self.diagnosisTypeCol.ids if id]))
        self.readOnly = False
        self.eventEditor = parent
        self.getDispanserIdLists()


    def getDispanserIdLists(self):
        db = QtGui.qApp.db
        self.observedDispanserIdList = db.getDistinctIdList('rbDispanser', 'id', ['observed = 1'])
        recordIdList = db.getDistinctIdList('rbDispanser', 'id', ['code = 2'])
        self.takenDispanserId = recordIdList[0] if len(recordIdList) > 0 else None
        self.takenDispanserIdList = db.getDistinctIdList('rbDispanser', 'id', ['code = 2 OR code = 6'])
        consistDispanserIdList = db.getDistinctIdList('rbDispanser', 'id', ['code = 1'])
        self.consistDispanserId = consistDispanserIdList[0] if len(consistDispanserIdList) > 0 else None


    def setReadOnly(self, value):
        self.readOnly = value


    def manualSwitchDiagnosis(self):
        return self.isManualSwitchDiagnosis


    def flags(self, index=QModelIndex()):
        if self.readOnly:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        result = CMKBListInDocTableModel.flags(self, index)
        row = index.row()
        if row < len(self._items):
            column = index.column()
            if self.isManualSwitchDiagnosis and index.isValid():
                if column == self.columnHandleDiagnosis:
                    characterId = forceRef(self.items()[row].value('character_id'))
                    if characterId != self.characterIdForHandleDiagnosis:
                        result = (result & ~Qt.ItemIsUserCheckable)
#                        return result
            if self.isMKBMorphology and index.isValid():
                if column == self.getColIndex('morphologyMKB'):
                    mkb = forceString(self.items()[row].value('MKB'))
                    if not (bool(mkb) and mkb[0] in CF003BaseDiagnosticsModel.MKB_allowed_morphology):
                        result = (result & ~Qt.ItemIsEditable)
            if QtGui.qApp.isExSubclassMKBVisible() and index.isValid():
                if column == self.getColIndex('exSubclassMKB'):
                    mkb = forceString(self.items()[row].value('MKB'))
                    if len(mkb) != 6:
                        return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return result


    def getEmptyRecord(self):
#        eventEditor = QObject.parent(self)
        result = CMKBListInDocTableModel.getEmptyRecord(self)
        result.append(QtSql.QSqlField('diagnosis_id',     QVariant.Int))
        result.append(QtSql.QSqlField('speciality_id',    QVariant.Int))
        result.append(QtSql.QSqlField('setDate',          QVariant.DateTime))
        result.append(QtSql.QSqlField('endDate',          QVariant.DateTime))
        result.append(QtSql.QSqlField('payStatus',        QVariant.Int))
        result.append(QtSql.QSqlField('cTumor_id',        QVariant.Int))
        result.append(QtSql.QSqlField('cNodus_id',        QVariant.Int))
        result.append(QtSql.QSqlField('cMetastasis_id',   QVariant.Int))
        result.append(QtSql.QSqlField('cTNMphase_id',     QVariant.Int))
        result.append(QtSql.QSqlField('pTumor_id',        QVariant.Int))
        result.append(QtSql.QSqlField('pNodus_id',        QVariant.Int))
        result.append(QtSql.QSqlField('pMetastasis_id',   QVariant.Int))
        result.append(QtSql.QSqlField('pTNMphase_id',     QVariant.Int))
        if self.items():
            result.setValue('diagnosisType_id',  toVariant(self.diagnosisTypeCol.ids[2]))
        else:
            result.setValue('diagnosisType_id',  toVariant(self.diagnosisTypeCol.ids[0] if self.diagnosisTypeCol.ids[0] else self.diagnosisTypeCol.ids[1]))
            result.setValue('result_id',  toVariant(CF027Dialog.defaultDiagnosticResultId))
        result.setValue('person_id',  toVariant(QtGui.qApp.userId if QtGui.qApp.userSpecialityId else self._parent.personId))
        return result


    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if 0 <= row < len(self._items):
            if role == Qt.EditRole:
                if QtGui.qApp.isTNMSVisible() and 0 <= row < len(self.items()) and column == self.items()[row].indexOf('TNMS'):
                    col = self._cols[column]
                    record = self._items[row]
                    tnmsMap = {}
                    for keyName, fieldName in CEventEditDialog.TNMSFieldsDict.items():
                        tnmsMap[keyName] = forceRef(record.value(fieldName))
                    return QVariant([forceString(record.value(col.fieldName())), tnmsMap])
        return CMKBListInDocTableModel.data(self, index, role)


    def setData(self, index, value, role=Qt.EditRole):
        column = index.column()
        row = index.row()
        if not variantEq(self.data(index, role), value):
            eventEditor = QObject.parent(self)
            if column == 0: # тип диагноза
                result = CMKBListInDocTableModel.setData(self, index, value, role)
                if result:
                    self.updateDiagnosisType(set([row]))
                    self.emitDiagnosisChanged()
                return result
            elif column == 1: # врач
                personId = forceRef(value)
                if not eventEditor.checkClientAttendanceEE(personId):
                    return False
                result = CMKBListInDocTableModel.setData(self, index, value, role)
                if result:
                    self.updateDiagnosisType(set())
                return result
            elif column == 2: # код МКБ
                newMKB = forceString(value)
                if not newMKB:
                    specifiedMKB = ''
                    specifiedMKBEx = ''
                    specifiedCharacterId = None
                    specifiedTraumaTypeId = None
                    specifiedDispanserId = None
                    specifiedRequiresFillingDispanser = 0
                    specifiedProlongMKB = False
                else:
                    acceptable, specifiedMKB, specifiedMKBEx, specifiedCharacterId, specifiedTraumaTypeId, specifiedDispanserId, specifiedRequiresFillingDispanser, specifiedProlongMKB = eventEditor.specifyDiagnosis(newMKB)
                    if not acceptable:
                        return False
                value = toVariant(specifiedMKB)
                oldMKB = forceString(self.items()[row].value('MKB')) if 0 <= row < len(self.items()) else None
                result = CMKBListInDocTableModel.setData(self, index, value, role)
                if result:
                    if specifiedRequiresFillingDispanser == 2:
                        self.updateDispanserByMKB(row, specifiedDispanserId, specifiedProlongMKB)
                    self.updateCharacterByMKB(row, specifiedMKB, specifiedCharacterId)
                    self.updateTraumaType(row, specifiedMKB, specifiedTraumaTypeId)
                    self.updateToxicSubstancesByMKB(row, specifiedMKB)
                    self.updateTNMS(index, self.items()[row], specifiedMKB)
                    self.updateMKBTNMS(self.items()[row], specifiedMKB)
                    self.inheritMKBTNMS(self.items()[row], oldMKB, specifiedMKB, eventEditor.clientId, eventEditor.eventSetDateTime)
                    self.updateExSubclass(index, self.items()[row], specifiedMKB)
                    self.updateMKBToExSubclass(self.items()[row], specifiedMKB)
                    self.emitDiagnosisChanged()
                return result
            if 0 <= row < len(self.items()) and column == self.items()[row].indexOf('MKBEx'): # доп. код МКБ
                newMKB = forceString(value)
                if not newMKB:
                    pass
                else:
                    acceptable = eventEditor.checkDiagnosis(newMKB)
                    if not acceptable:
                        return False
                value = toVariant(newMKB)
                result = CMKBListInDocTableModel.setData(self, index, value, role)
#                if result:
#                    self.updateCharacterByMKB(row, specifiedMKB)
                return result
            if QtGui.qApp.isTNMSVisible() and 0 <= row < len(self.items()) and column == self.items()[row].indexOf('TNMS'):
                record = self.items()[row]
                self.updateMKBTNMS(record, forceString(record.value('MKB')))
                if value:
                    valueList = value.toList()
                    valueTNMS = valueList[0]
                    tnmsMap = valueList[1].toMap()
                    for name, TNMSId in tnmsMap.items():
                        if name in CEventEditDialog.TNMSFieldsDict.keys():
                            record.setValue(CEventEditDialog.TNMSFieldsDict[forceString(name)], TNMSId)
                    self.emitRowChanged(row)
                    return CMKBListInDocTableModel.setData(self, index, valueTNMS, role)
            if QtGui.qApp.isExSubclassMKBVisible() and 0 <= row < len(self.items()) and column == self.items()[row].indexOf('exSubclassMKB'):
                record = self.items()[row]
                self.updateMKBToExSubclass(record, forceStringEx(record.value('MKB')))
                return CMKBListInDocTableModel.setData(self, index, value, role)
            return CMKBListInDocTableModel.setData(self, index, value, role)
        else:
            return True


    def updateMKBToExSubclass(self, record, MKB):
        if QtGui.qApp.isExSubclassMKBVisible():
            self.cols()[record.indexOf('exSubclassMKB')].setMKB(forceString(MKB))


    def updateExSubclass(self, index, record, MKB):
        if QtGui.qApp.isExSubclassMKBVisible():
            newMKB = forceString(MKB)
            if self.cols()[record.indexOf('exSubclassMKB')].MKB != newMKB:
                record.setValue('exSubclassMKB', toVariant(u''))
                self.emitRowChanged(index.row())


    def updateMKBTNMS(self, record, MKB):
        if QtGui.qApp.isTNMSVisible():
            self.cols()[record.indexOf('TNMS')].setMKB(forceString(MKB))


    def updateTNMS(self, index, record, MKB):
        if QtGui.qApp.isTNMSVisible():
            newMKB = forceString(MKB)
            if self.cols()[record.indexOf('TNMS')].MKB != newMKB:
                row = index.row()
                tnmsMap = {}
                for keyName, fieldName in CEventEditDialog.TNMSFieldsDict.items():
                    tnmsMap[keyName] = None
                    record.setValue(fieldName, toVariant(None))
                record.setValue('TNMS', toVariant(u''))
                self.emitRowChanged(row)


    def inheritMKBTNMS(self, record, oldMKB, newMKB, clientId, eventSetDate):
        if QtGui.qApp.isTNMSVisible() and not oldMKB and newMKB and (newMKB[:1] == 'C' or newMKB[:2] == 'D0'):
            query = QtGui.qApp.db.query(u"""SELECT Diagnostic.* 
                                            FROM Diagnostic 
                                            left JOIN Diagnosis ON Diagnosis.id = Diagnostic.diagnosis_id
                                            left JOIN rbDiagnosisType ON rbDiagnosisType.id = Diagnostic.diagnosisType_id
                                          WHERE Diagnosis.client_id = {clientId} 
                                            AND rbDiagnosisType.code = '1'
                                            AND Diagnosis.MKB = '{mkb}'
                                            AND Diagnostic.endDate <= '{date}'
                                          ORDER BY Diagnostic.endDate DESC 
                                          LIMIT 1""".format(clientId=clientId,
                                                            mkb=forceString(newMKB),
                                                            date=forceDate(eventSetDate).toString(
                                                                'yyyy-MM-dd')))
            if query.first():
                recordOldDiagnostic = query.record()
                record.setValue('TNMS', recordOldDiagnostic.value('TNMS'))
                record.setValue('cTumor_id', recordOldDiagnostic.value('cTumor_id'))
                record.setValue('cNodus_id', recordOldDiagnostic.value('cNodus_id'))
                record.setValue('cMetastasis_id', recordOldDiagnostic.value('cMetastasis_id'))
                record.setValue('cTNMphase_id', recordOldDiagnostic.value('cTNMphase_id'))
                record.setValue('pTumor_id', recordOldDiagnostic.value('pTumor_id'))
                record.setValue('pNodus_id', recordOldDiagnostic.value('pNodus_id'))
                record.setValue('pMetastasis_id', recordOldDiagnostic.value('pMetastasis_id'))
                record.setValue('pTNMphase_id', recordOldDiagnostic.value('pTNMphase_id'))


    def payStatus(self, row):
        if 0 <= row < len(self.items()):
            return forceInt(self.items()[row].value('payStatus'))
        else:
            return 0


    def removeRowEx(self, row):
        self.removeRows(row, 1)


    def updateDiagnosisType(self, fixedRowSet):
        mapPersonIdToRow = {}
        diagnosisTypeIds = []
        endDiagnosisTypeIds = None
        endPersonId = None
        endRow = -1
        for row, item in enumerate(self.items()):
            personId = forceRef(item.value('person_id'))
            rows = mapPersonIdToRow.setdefault(personId, [])
            rows.append(row)
            diagnosisTypeId = forceRef(item.value('diagnosisType_id'))
            diagnosisTypeIds.append(diagnosisTypeId)
            if self.diagnosisTypeCol.ids[0] == diagnosisTypeId and personId == self._parent.personId:
                endDiagnosisTypeIds = diagnosisTypeId
                endPersonId = personId
                endRow = row

        for personId, rows in mapPersonIdToRow.iteritems():
            usedDiagnosisTypeIds = [diagnosisTypeIds[row] for row in fixedRowSet.intersection(set(rows))]
            listFixedRowSet = [row for row in fixedRowSet.intersection(set(rows))]
            if ((self.diagnosisTypeCol.ids[0] in usedDiagnosisTypeIds) or (self.diagnosisTypeCol.ids[0] == diagnosisTypeIds[rows[0]])) and personId == self._parent.personId:
                firstDiagnosisId = self.diagnosisTypeCol.ids[0]
            elif (self.diagnosisTypeCol.ids[0] in usedDiagnosisTypeIds) and personId != self._parent.personId:
                 res = QtGui.QMessageBox.warning(self._parent,
                                           u'Внимание!',
                                           u'Смена заключительного диагноза.\nОтветственный будет заменен на \'%s\'.\nВы подтверждаете изменения?' % (forceString(QtGui.qApp.db.translate('vrbPersonWithSpeciality', 'id', personId, 'name'))),
                                           QtGui.QMessageBox.Ok|QtGui.QMessageBox.Cancel,
                                           QtGui.QMessageBox.Cancel)
                 if res == QtGui.QMessageBox.Ok:
                     self._parent.personId = personId
                     self._parent.cmbPerson.setValue(self._parent.personId)
                     firstDiagnosisId = self.diagnosisTypeCol.ids[0]
                     rowEndPersonId = mapPersonIdToRow[endPersonId] if endPersonId else None
                     diagnosisTypeColIdsEnd = -1
                     if rowEndPersonId and len(rowEndPersonId) > 1:
                         for rowPerson in rowEndPersonId:
                             if diagnosisTypeIds[rowPerson] == self.diagnosisTypeCol.ids[1] or diagnosisTypeIds[rowPerson] == self.diagnosisTypeCol.ids[0]:
                                if endRow > -1 and endDiagnosisTypeIds == self.diagnosisTypeCol.ids[0] and endRow != rowPerson:
                                     diagnosisTypeColIdsEnd = self.diagnosisTypeCol.ids[2]
                                     break
                         if diagnosisTypeColIdsEnd == -1:
                             diagnosisTypeColIdsEnd = self.diagnosisTypeCol.ids[1]
                     else:
                         if endRow > -1 and endDiagnosisTypeIds == self.diagnosisTypeCol.ids[0]:
                             diagnosisTypeColIdsEnd = self.diagnosisTypeCol.ids[1]
                     if diagnosisTypeColIdsEnd > -1:
                         self.items()[endRow].setValue('diagnosisType_id', toVariant(diagnosisTypeColIdsEnd))
                         self.emitCellChanged(endRow, self.items()[endRow].indexOf('diagnosisType_id'))
                         diagnosisTypeIds[endRow] = forceRef(self.items()[endRow].value('diagnosisType_id'))
                 else:
                     if endRow > -1 and endDiagnosisTypeIds == self.diagnosisTypeCol.ids[0]:
                         self.items()[endRow].setValue('diagnosisType_id', toVariant(endDiagnosisTypeIds))
                         self.emitCellChanged(endRow, self.items()[endRow].indexOf('diagnosisType_id'))
                         diagnosisTypeIds[endRow] = forceRef(self.items()[endRow].value('diagnosisType_id'))
                     firstDiagnosisId = self.diagnosisTypeCol.ids[1]
                     diagnosisTypeColIdsRows = -1
                     if len(rows) > 1:
                         for rowPerson in rows:
                             if diagnosisTypeIds[rowPerson] == self.diagnosisTypeCol.ids[1] or diagnosisTypeIds[rowPerson] == self.diagnosisTypeCol.ids[0] and (rowPerson not in listFixedRowSet):
                                 diagnosisTypeColIdsRows = self.diagnosisTypeCol.ids[2]
                                 break
                         if diagnosisTypeColIdsRows == -1:
                            diagnosisTypeColIdsRows = self.diagnosisTypeCol.ids[1]
                     else:
                         diagnosisTypeColIdsRows = self.diagnosisTypeCol.ids[1]
                     if diagnosisTypeColIdsRows > -1:
                         for rowFixed in listFixedRowSet:
                             self.items()[rowFixed].setValue('diagnosisType_id', toVariant(diagnosisTypeColIdsRows))
                             self.emitCellChanged(rowFixed, self.items()[rowFixed].indexOf('diagnosisType_id'))
                             diagnosisTypeIds[rowFixed] = forceRef(self.items()[rowFixed].value('diagnosisType_id'))
                     usedDiagnosisTypeIds = [diagnosisTypeIds[row] for row in fixedRowSet.intersection(set(rows))]
            else:
                firstDiagnosisId = self.diagnosisTypeCol.ids[1]
            otherDiagnosisId = self.diagnosisTypeCol.ids[2]

            diagnosisTypeId = firstDiagnosisId if firstDiagnosisId not in usedDiagnosisTypeIds else otherDiagnosisId
            freeRows = set(rows).difference(fixedRowSet)
            for row in rows:
                if (row in freeRows) or diagnosisTypeIds[row] not in (firstDiagnosisId, otherDiagnosisId):
                    if diagnosisTypeId != diagnosisTypeIds[row] and diagnosisTypeIds[row] != self.diagnosisTypeCol.ids[3]:
                        self.items()[row].setValue('diagnosisType_id', toVariant(diagnosisTypeId))
                        self.emitCellChanged(row, self.items()[row].indexOf('diagnosisType_id'))
                        diagnosisTypeId = forceRef(self.items()[row].value('diagnosisType_id'))
                        diagnosisTypeIds[row] = diagnosisTypeId
                    diagnosisTypeId = otherDiagnosisId


    def updateDispanserByMKB(self, row, specifiedDispanserId, specifiedProlongMKB):
        item = self.items()[row]
        if specifiedProlongMKB and specifiedDispanserId and specifiedDispanserId in self.observedDispanserIdList:
            dispanserId = specifiedDispanserId if specifiedDispanserId not in self.takenDispanserIdList else self.consistDispanserId
            item.setValue('dispanser_id', toVariant(dispanserId))
            self.emitCellChanged(row, item.indexOf('dispanser_id'))
        elif not specifiedProlongMKB:
            item.setValue('dispanser_id', toVariant(self.takenDispanserId))
            self.emitCellChanged(row, item.indexOf('dispanser_id'))


    def updateCharacterByMKB(self, row, MKB, specifiedCharacterId):
        characterIdList = getAvailableCharacterIdByMKB(MKB)
        item = self.items()[row]
        if specifiedCharacterId in characterIdList:
            characterId = specifiedCharacterId
        else:
            characterId = forceRef(item.value('character_id'))
            if (characterId in characterIdList) or (characterId is None and not characterIdList):
                return
            if characterIdList:
                characterId = characterIdList[0]
            else:
                characterId = None
        item.setValue('character_id', toVariant(characterId))
        self.emitCellChanged(row, item.indexOf('character_id'))


    def updateTraumaType(self, row, MKB, specifiedTraumaTypeId):
        item = self.items()[row]
        prevTraumaTypeId = forceRef(item.value('traumaType_id'))
        if specifiedTraumaTypeId:
            traumaTypeId = specifiedTraumaTypeId
        else:
            traumaTypeId = prevTraumaTypeId
        if traumaTypeId != prevTraumaTypeId:
            item.setValue('traumaType_id', toVariant(traumaTypeId))
            self.emitCellChanged(row, item.indexOf('traumaType_id'))


    def updateToxicSubstancesByMKB(self, row, MKB):
        toxicSubstanceIdList = getToxicSubstancesIdListByMKB(MKB)
        item = self.items()[row]
        toxicSubstanceId = forceRef(item.value('toxicSubstances_id'))
        if toxicSubstanceId and toxicSubstanceId in toxicSubstanceIdList:
            return
        item.setValue('toxicSubstances_id', toVariant(None))
        self.emitCellChanged(row, item.indexOf('toxicSubstances_id'))


    def getFinalDiagnosisMKB(self):
        finalDiagnosisTypeId = self.diagnosisTypeCol.ids[0] or self.diagnosisTypeCol.ids[1]
        items = self.items()
        for item in items:
            diagnosisTypeId = forceRef(item.value('diagnosisType_id'))
            if diagnosisTypeId == finalDiagnosisTypeId:
                return forceString(item.value('MKB')), forceString(item.value('MKBEx'))
        return '', ''


    def getFinalDiagnosisId(self):
        finalDiagnosisTypeId = self.diagnosisTypeCol.ids[0]
        items = self.items()
        for item in items:
            diagnosisTypeId = forceRef(item.value('diagnosisType_id'))
            if diagnosisTypeId == finalDiagnosisTypeId:
                return forceRef(item.value('diagnosis_id'))
        return None


    def emitDiagnosisChanged(self):
        self.emit(SIGNAL('diagnosisChanged()'))



class CF003PreliminaryDiagnosticsModel(CF003BaseDiagnosticsModel):
    def __init__(self, parent):
        CF003BaseDiagnosticsModel.__init__(self, parent, None, '7', '11', None)


    def getMainDiagnosisTypeIdList(self):
        return [self.diagnosisTypeCol.ids[1]]
    
    
    def getEmptyRecord(self):
        result = CF003BaseDiagnosticsModel.getEmptyRecord(self)
        return result


class CF003FinalDiagnosticsModel(CF003BaseDiagnosticsModel):
    __pyqtSignals__ = ('resultChanged()',
                      )

    def __init__(self, parent):
        CF003BaseDiagnosticsModel.__init__(self, parent, '1', '2', '9', '3')
        self.addCol(CRBInDocTableCol(    u'Результат',     'result_id',     10, 'rbDiagnosticResult', showFields=CRBComboBox.showNameAndCode, preferredWidth=350))


    def getCloseOrMainDiagnosisTypeIdList(self):
        return self.diagnosisTypeCol.ids[:2]


    def setData(self, index, value, role=Qt.EditRole):
        resultId = self.resultId()
        result = CF003BaseDiagnosticsModel.setData(self, index, value, role)
        if resultId != self.resultId():
            self.emitResultChanged()
        return result


    def removeRowEx(self, row):
        resultId = self.resultId()
        self.removeRows(row, 1)
        if resultId != self.resultId():
            self.emitResultChanged()


    def resultId(self):
        items = self.items()
        diagnosisTypeId = self.diagnosisTypeCol.ids[0]
        for item in items:
            if forceRef(item.value('diagnosisType_id')) == diagnosisTypeId:
                return forceRef(item.value('result_id'))
        else:
            return None


    def emitResultChanged(self):
        self.emit(SIGNAL('resultChanged()'))


# ###################################################################


class CF003DiagnosisTypeCol(CDiagnosisTypeCol):
    def __init__(self, title=u'Тип', fieldName='diagnosisType_id', width=5, diagnosisTypeCodes=[], smartMode=True, **params):
        CDiagnosisTypeCol.__init__(self, title, fieldName, width, diagnosisTypeCodes, smartMode, **params)
        self.namesF003 = [u'Закл', u'Осн', u'Соп', u'Осл']


    def toString(self, val, record):
        id = forceRef(val)
        if id in self.ids:
            return toVariant(self.namesF003[self.ids.index(id)])
        return QVariant()


    def setEditorData(self, editor, value, record):
        editor.clear()
        if value.isNull():
            value = record.value(self.fieldName())
        id = forceRef(value)
        if self.smartMode:
            if id == self.ids[0]:
                editor.addItem(self.namesF003[0], toVariant(self.ids[0]))
            elif id == self.ids[1]:
                if self.ids[0]:
                    editor.addItem(self.namesF003[0], toVariant(self.ids[0]))
                editor.addItem(self.namesF003[1], toVariant(self.ids[1]))
            else:
                editor.addItem(self.namesF003[2], toVariant(self.ids[2]))
                editor.addItem(self.namesF003[3], toVariant(self.ids[3]))
        else:
            for itemName, itemId in zip(self.namesF003, self.ids):
                if itemId:
                    editor.addItem(itemName, toVariant(itemId))
        currentIndex = editor.findData(toVariant(id))
        editor.setCurrentIndex(currentIndex)


class CActionInfoProxyListProtocol(CInfoProxyList):
    def __init__(self, context, models, protocol, eventInfo):
        CInfoProxyList.__init__(self, context)
        self._rawItems = []
        for model in models:
            self._rawItems.extend(model.items())
        protocolItem = [(protocol.action._record, protocol.action)] if protocol.action else []
        self._rawItems.extend(protocolItem)
        self._items = [ None ]*len(self._rawItems)
        self._eventInfo = eventInfo


    def __getitem__(self, key):
        v = self._items[key]
        if v is None:
            record, action = self._rawItems[key]
            v = self.getInstance(CCookedActionInfo, record, action)
            v._eventInfo = self._eventInfo
            self._items[key] = v
        return v
