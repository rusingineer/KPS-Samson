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

# Форма 030: Этап диспансерного наблюдения

from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import Qt, QDate, QDateTime, QModelIndex, QObject, QTime, QVariant, pyqtSignature, SIGNAL

from Events.ExportMIS import iniExportEvent
from Events.RelatedEventAndActionListDialog import CRelatedEventAndActionListDialog
from F088.F0882022EditDialog import CEventExportTableModel, CAdvancedExportTableModel
from Orgs.Utils import getOrgstructureListByEventtypeId, getPersonListByEventtypeId
from library.Attach.AttachAction import getAttachAction
from Events.Action import CActionTypeCache
from library.Calendar           import getNextWorkDay
from library.crbcombobox        import CRBComboBox
from library.ICDInDocTableCol   import CICDExInDocTableCol
from library.ICDMorphologyInDocTableCol import CMKBMorphologyCol
from library.InDocTable          import CBoolInDocTableCol, CDateTimeForEventInDocTableCol, CInDocTableCol, CMKBListInDocTableModel, CRBInDocTableCol, CRBLikeEnumInDocTableCol, CEnumInDocTableCol
from library.interchange        import getDateEditValue, getDatetimeEditValue, getRBComboBoxValue, setDateEditValue, setDatetimeEditValue, setRBComboBoxValue
from library.PrintInfo          import CInfoContext
from library.PrintTemplates     import applyTemplate, customizePrintButton, getPrintButton
from library.TNMS.TNMSComboBox   import CTNMSCol
from library.MKBExSubclassComboBox import CMKBExSubclassCol
from library.Utils               import copyFields, forceBool, forceDate, forceInt, forceRef, forceString, formatNum, toVariant, variantEq, forceStringEx

from Events.ActionInfo          import CActionInfoProxyList
from Events.ActionsSummaryModel import CFxxxActionsSummaryModel
from Events.DiagnosisType       import CDiagnosisTypeCol
from Events.EventEditDialog     import CEventEditDialog, CDiseaseCharacter, CDiseaseStage, CDiseasePhases, CToxicSubstances, getToxicSubstancesIdListByMKB
from Events.EventInfo            import CDiagnosticInfoProxyList, CVisitInfoProxyList, CHospitalInfo
from Events.EventVisitsModel    import CEventVisitsModel
from Events.Utils import checkDiagnosis, checkIsHandleDiagnosisIsChecked, CTableSummaryActionsMenuMixin, \
    getAvailableCharacterIdByMKB, getDiagnosisId2, getEventAddVisit, getEventAvailableOrders, getEventDurationRange, getEventIsPrimary, \
    getEventMesRequired, getDiagnosticResultIdList, getEventResultId, getEventSetPerson, getEventShowTime, \
    getEventShowVisitTime, getHealthGroupFilter, hasEventVisitAssistant, isEventLong, \
    setAskedClassValueForDiagnosisManualSwitch, getNewResultCond, isDefaultResultIdValid, \
    CFinanceType, mkbIsOnko, getEventTypeForm, mkbIsVIMIS, getEventAidTypeRegionalCode
from F030.PreF030Dialog         import CPreF030Dialog, CPreF030DagnosticAndActionPresets
from Orgs.PersonComboBoxEx      import CPersonFindInDocTableCol
from Users.Rights                import urAccessF030planner, urAccessF090planner, urAdmin, urEditEndDateEvent, urRegTabWriteRegistry, urRegTabReadRegistry, urCanReadClientVaccination, urCanEditClientVaccination

from F030.Ui_F030               import Ui_Dialog


class CF030Dialog(CEventEditDialog, Ui_Dialog, CTableSummaryActionsMenuMixin):
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
        CEventEditDialog.__init__(self, parent)
        self.mapSpecialityIdToDiagFilter = {}

# create models
        self.addModels('Visits', CEventVisitsModel(self))
        self.addModels('PreliminaryDiagnostics', CF030PreliminaryDiagnosticsModel(self))
        self.addModels('FinalDiagnostics',       CF030FinalDiagnosticsModel(self))
        self.addModels('ActionsSummary', CFxxxActionsSummaryModel(self, True))
        self.addModels('Export', CEventExportTableModel(self))
        self.addModels('Export_FileAttach', CAdvancedExportTableModel(self))
        self.addModels('Export_VIMIS', CAdvancedExportTableModel(self))

# ui
        self.createSaveAndCreateAccountButton()
        self.addObject('actEditClient', QtGui.QAction(u'Открыть регистрационную карточку', self))
        self.addObject('actPortal_Doctor', QtGui.QAction(u'Перейти на портал врача', self))
        self.addObject('actShowAttachedToClientFiles', getAttachAction('Client_FileAttach',  self))
        self.addObject('actShowContingentsClient', QtGui.QAction(u'Показать все наблюдаемые контингенты', self))
        self.addObject('actOpenClientVaccinationCard', QtGui.QAction(u'Открыть прививочную карту', self))
        self.addObject('actSurveillancePlanningClients', QtGui.QAction(u'Контрольная карта диспансерного наблюдения', self))
        self.addObject('btnPrint', getPrintButton(self, ''))
        # self.addObject('btnMedicalCommission', QtGui.QPushButton(u'ВК', self))
        self.addObject('btnPlanning', QtGui.QPushButton(u'Планировщик', self))
        self.addObject('btnRelatedEvent', QtGui.QPushButton(u'Связанные события', self))
        self.addObject('btnTemperatureList',QtGui.QPushButton(u'Температурный лист', self))
        self.addObject('btnPrintMedicalDiagnosis', getPrintButton(self, '', u'Врачебный диагноз'))
        self.setupUi(self)

        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setWindowTitleEx(u'Осмотр Ф.030')
        self.setMedicalDiagnosisContext()
        self.tabToken.setFocusProxy(self.tblFinalDiagnostics)
        self.tabMes.setEventEditor(self)
        self.tabTempInvalidAndAegrotat.setCurrentIndex(1 if QtGui.qApp.tempInvalidDoctype() == '2' else 0)
        self.grpTempInvalid.setEventEditor(self)
        self.grpTempInvalid.setType(0, '1')
        self.grpAegrotat.setEventEditor(self)
        self.grpAegrotat.setType(0, '2')
        self.grpDisability.setEventEditor(self)
        self.grpDisability.setType(1)
        self.grpVitalRestriction.setEventEditor(self)
        self.grpVitalRestriction.setType(2)

        self.tabStatus.setEventEditor(self)
        self.tabMedicalDiagnosis.setEventEditor(self)
        self.tabDiagnostic.setEventEditor(self)
        self.tabCure.setEventEditor(self)
        self.tabMisc.setEventEditor(self)
        self.tabCash.setEventEditor(self)
        self.tabStatus.setActionTypeClass(0)
        self.tabDiagnostic.setActionTypeClass(1)
        self.tabCure.setActionTypeClass(2)
        self.tabMisc.setActionTypeClass(3)
        self.tabAmbCard.setEventEditor(self)
        self.buttonBox.addButton(self.btnPrint, QtGui.QDialogButtonBox.ActionRole)
        if QtGui.qApp.defaultKLADR()[:2] in ['23', '01']:
            self.buttonBox.addButton(self.btnPlanning, QtGui.QDialogButtonBox.ActionRole)
        self.setupSaveAndCreateAccountButton()
        # self.buttonBox.addButton(self.btnMedicalCommission, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnRelatedEvent, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnTemperatureList, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnPrintMedicalDiagnosis, QtGui.QDialogButtonBox.ActionRole)
        self.setupActionSummarySlots()
# tables to rb and combo-boxes

# assign models
        self.tblVisits.setModel(self.modelVisits)
        self.tblPreliminaryDiagnostics.setModel(self.modelPreliminaryDiagnostics)
        self.tblPreliminaryDiagnostics.setDelRowsChecker(None)
        self.tblFinalDiagnostics.setModel(self.modelFinalDiagnostics)
        self.tblFinalDiagnostics.setDelRowsChecker(None)
        self.tblActions.setModel(self.modelActionsSummary)
        self.modelActionsSummary.addModel(self.tabStatus.modelAPActions)
        self.modelActionsSummary.addModel(self.tabDiagnostic.modelAPActions)
        self.modelActionsSummary.addModel(self.tabCure.modelAPActions)
        self.modelActionsSummary.addModel(self.tabMisc.modelAPActions)
        self.tabCash.addActionModel(self.tabStatus.modelAPActions)
        self.tabCash.addActionModel(self.tabDiagnostic.modelAPActions)
        self.tabCash.addActionModel(self.tabCure.modelAPActions)
        self.tabCash.addActionModel(self.tabMisc.modelAPActions)
        self.setModels(self.tblExport, self.modelExport, self.selectionModelExport)
        self.setModels(self.tblExport_FileAttach, self.modelExport_FileAttach, self.selectionModelExport_FileAttach)
        self.setModels(self.tblExport_VIMIS, self.modelExport_VIMIS, self.selectionModelExport_VIMIS)

# popup menus
        self.txtClientInfoBrowser.actions.append(self.actEditClient)
        self.txtClientInfoBrowser.actions.append(self.actPortal_Doctor)
        self.txtClientInfoBrowser.actions.append(self.actShowAttachedToClientFiles)
        self.txtClientInfoBrowser.actions.append(self.actShowContingentsClient)
        self.txtClientInfoBrowser.actions.append(self.actOpenClientVaccinationCard)
        self.txtClientInfoBrowser.actions.append(self.actSurveillancePlanningClients)
        self.actOpenClientVaccinationCard.setEnabled(QtGui.qApp.userHasAnyRight([urCanReadClientVaccination, urCanEditClientVaccination]))
        self.actEditClient.setEnabled(QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]))
        self.tblPreliminaryDiagnostics.addCopyDiagnosisToFinal(self)
        self.tblVisits.addPopupDelRow()
        self.setupVisitsIsExposedPopupMenu()
        self.tblFinalDiagnostics.addCreateF111(self)
        self.tblFinalDiagnostics.addUpdateF111(self)
        self.tblActions.enableColsHide()
        CTableSummaryActionsMenuMixin.__init__(self)


# default values
#        db = QtGui.qApp.db
#        table = db.table('rbScene')
#?        self.sceneListHome = QtGui.qApp.db.getIdList(table, 'id', table['code'].inlist(['2', '3']))
#?        self.sceneListAmb  = QtGui.qApp.db.getIdList(table, 'id', table['code'].inlist(['1']))
#
        self.setupDirtyCather()
        self.setIsDirty(False)
        self.blankMovingIdList = []
        self.clientId = None
        self.prolongateEvent = False
        self.prevEventId = None
        self.tabNotes.setEventEditor(self)

        self.tblExport.enableColsHide()
        self.tblExport.enableColsMove()

        self.tblExport_FileAttach.enableColsHide()
        self.tblExport_FileAttach.enableColsMove()

        self.tblExport_VIMIS.enableColsHide()
        self.tblExport_VIMIS.enableColsMove()

        self.postSetupUi()
        if hasattr(self, 'edtEndDate'):
            self.edtEndDate.setEnabled(QtGui.qApp.userHasRight(urEditEndDateEvent))
        if hasattr(self, 'edtEndTime'):
            self.edtEndTime.setEnabled(QtGui.qApp.userHasRight(urEditEndDateEvent))
        self.btnPrintMedicalDiagnosis.setVisible(False)
# done


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelFinalDiagnostics_dataChanged(self, topLeft, bottomRight):
        pass



    def destroy(self):
        pass

    def getModelFinalDiagnostics(self):
        return self.modelFinalDiagnostics


#    def currentClientId(self): # for AmbCard mixin
#        return self.clientId

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


    @pyqtSignature('')
    def on_btnTemperatureList_clicked(self):
        self.getTemperatureList(self.eventSetDateTime)

    # я этого не хотел :(
    # что такое, например, diagnos, protocolQuoteId или typeQueue?
    def _prepare(self, clientId, eventTypeId, orgId, personId, eventSetDatetime, eventDatetime, weekProfile,
                 numDays, presetDiagnostics, presetActions, disabledActions, externalId, assistantId,
                 curatorId, actionTypeIdValue = None, valueProperties = [], relegateOrgId = None,
                 relegatePersonId=None, diagnos = None, financeId = None, protocolQuoteId = None,
                 actionByNewEvent = [], eventOrder = 1, typeQueue = -1, relegateInfo=[], plannedEndDate = None, isEdit = False):
        def getPrimary(clientId, eventTypeId, personId):
            db = QtGui.qApp.db
            tableEvent = db.table('Event')
            tablePerson = db.table('Person')
            tableP1 = tablePerson.alias('p1')
            tableP2 = tablePerson.alias('p2')
            table = tableEvent.leftJoin(tableP1, tableP1['id'].eq(tableEvent['execPerson_id']))
            table = table.leftJoin(tableP2, tableP1['speciality_id'].eq(tableP2['speciality_id']))
            cond = [tableEvent['deleted'].eq(0),
                    tableEvent['client_id'].eq(clientId),
                    tableEvent['eventType_id'].eq(eventTypeId),
                    tableP2['id'].eq(personId),
                    ]
            record = db.getRecordEx(table, tableEvent['nextEventDate'].name(), cond, order=tableEvent['execDate'].name()+' DESC')
            return not(record and not record.value('nextEventDate').isNull())

        def prepVisit(date, personId):
            sceneId = None
            if typeQueue is not None and typeQueue > -1:
                db = QtGui.qApp.db
                tableRBScene = db.table('rbScene')
                recScene = db.getRecordEx(tableRBScene, 'id', [tableRBScene['appointmentType'].eq(typeQueue + 1)], 'rbScene.code')
                if recScene:
                    sceneId = forceRef(recScene.value('id'))
            visit = self.modelVisits.getEmptyRecord(sceneId=sceneId, personId=personId)
            visit.setValue('date', toVariant(date))
            return visit
        
        if not isEdit:
            self.eventSetDateTime = eventSetDatetime if isinstance(eventSetDatetime, QDateTime) else QDateTime(eventSetDatetime)
            self.eventDate = eventDatetime.date() if isinstance(eventDatetime, QDateTime) else eventDatetime
            self.setOrgId(orgId if orgId else QtGui.qApp.currentOrgId())
            self.setEventTypeId(eventTypeId)
            self.setClientId(clientId)
            self.prolongateEvent = True if actionByNewEvent else False
            self.tabNotes.setNotesEx(externalId, assistantId, curatorId, relegateOrgId, relegatePersonId, clientId, relegateInfo)
            self.setExternalId(externalId)
            self.cmbPerson.setValue(personId)
            setPerson = getEventSetPerson(self.eventTypeId)
            if setPerson == 0:
                self.setPerson = personId
            elif setPerson == 1:
                self.setPerson = QtGui.qApp.userId
            self.edtBegDate.setDate(self.eventSetDateTime.date())
            self.edtEndDate.setDate(self.eventDate)
            self.edtBegTime.setTime(eventSetDatetime.time() if isinstance(eventSetDatetime, QDateTime) else QTime())
            self.edtEndTime.setTime(eventDatetime.time() if isinstance(eventDatetime, QDateTime) else QTime())
            self.edtNextDate.setDate(QDate())
            self.cmbPrimary.setCurrentIndex(getEventIsPrimary(eventTypeId))
            self.initOrder(forceString(getEventAvailableOrders(eventTypeId)), eventOrder+1)
            self.cmbContract.setCurrentIndex(0)
            resultId = QtGui.qApp.session("F030_resultId")
            self.cmbResult.setValue(resultId)
            self.initFocus()

            visitTypeId = presetDiagnostics[0][3] if presetDiagnostics else None
            self.modelVisits.setDefaultVisitTypeId(visitTypeId)
            visits = []

            if isEventLong(eventTypeId) and numDays >= 1:
                date = self.eventSetDateTime.date().addDays(-1)
                availDays = numDays
                while availDays>1:
                    date = getNextWorkDay(date, weekProfile)
                    visits.append(prepVisit(date, personId))
                    availDays -= 1
                visits.append(prepVisit(self.eventDate, personId) )
            else:
                if getEventAddVisit(eventTypeId):
                    showTime = getEventShowTime(eventTypeId)
                    showVisitTime = getEventShowVisitTime(eventTypeId)
                    if showVisitTime:
                        if not showTime:
                            if self.eventDate:
                                date = QDateTime(self.eventDate, QTime.currentTime())
                            elif self.eventSetDateTime and self.eventSetDateTime.date():
                                date = QDateTime(self.eventSetDateTime.date(), QTime.currentTime())
                            else:
                                date = QDateTime.currentDateTime()
                        else:
                            if self.eventDate:
                                date = eventDatetime
                            elif self.eventSetDateTime and self.eventSetDateTime.date():
                                date = self.eventSetDateTime
                            else:
                                date = QDateTime.currentDateTime()
                    else:
                        if self.eventDate:
                            date = self.eventDate
                        elif self.eventSetDateTime and self.eventSetDateTime.date():
                            date = self.eventSetDateTime.date()
                        else:
                            date = QDate.currentDate()
                    visits.append(prepVisit(date, personId))
            self.modelVisits.setItems(visits)
            self.updateVisitsInfo()
            self.setOrgStructAndPersonsInCmbPersons(eventTypeId)
            if presetDiagnostics and personId:
                for MKB, dispanserId, healthGroupId, visitTypeId in presetDiagnostics:
                    item = self.modelFinalDiagnostics.getEmptyRecord()
                    item.setValue('MKB', toVariant(MKB))
                    item.setValue('dispanser_id',   toVariant(dispanserId))
                    item.setValue('healthGroup_id', toVariant(healthGroupId))
                    characterIdList = getAvailableCharacterIdByMKB(MKB)
                    if characterIdList:
                        item.setValue('character_id', toVariant(characterIdList[0]))
                    self.modelFinalDiagnostics.items().append(item)
                self.modelFinalDiagnostics.reset()
        self.prepareActions(presetActions, disabledActions, actionTypeIdValue, valueProperties, diagnos, financeId, protocolQuoteId, actionByNewEvent, plannedEndDate)
        self.grpTempInvalid.pickupTempInvalid()
        self.grpAegrotat.pickupTempInvalid()
        self.grpDisability.pickupTempInvalid()
        self.grpVitalRestriction.pickupTempInvalid()
        self.setIsDirty(False)
        self.tabNotes.setEventEditor(self)
        self.setFilterResult(self.eventSetDateTime.date())
        return self.checkEventCreationRestriction() and self.checkDeposit()


    def prepare(self, clientId, eventTypeId, orgId, personId, eventSetDatetime, eventDatetime, weekProfile,
                numDays, externalId, assistantId, curatorId, flagHospitalization = False,
                actionTypeIdValue = None, valueProperties = [], tissueTypeId=None, selectPreviousActions=False,
                relegateOrgId = None, relegatePersonId=None, diagnos = None, financeId = None,
                protocolQuoteId = None, actionByNewEvent = [], order = 1,
                actionListToNewEvent = [], typeQueue = -1, docNum=None, relegateInfo=[], plannedEndDate = None,
                mapJournalInfoTransfer = [], voucherParams = {}, isEdit=False):
        self.setPersonId(personId)
        self.flagHospitalization = flagHospitalization
        eventDate = eventDatetime.date() if isinstance(eventDatetime, QDateTime) else eventDatetime
        if not eventDate and eventSetDatetime:
            eventDate = eventSetDatetime.date() if isinstance(eventSetDatetime, QDateTime) else eventSetDatetime
        else:
            eventDate = QDate.currentDate()
        presentActionTypes = []
        maxOccursLimitActionTypes = []
        for item in self.modelActionsSummary.items():
            actionTypeId = forceString(item.value('actionType_id'))
            if actionTypeId not in presentActionTypes:
                presentActionTypes.append(actionTypeId)
                if not self.checkMaxOccursLimit(actionTypeId) and actionTypeId not in maxOccursLimitActionTypes:
                    maxOccursLimitActionTypes.append(actionTypeId)
        form = getEventTypeForm(eventTypeId)
        if (form != u'090' and QtGui.qApp.userHasRight(urAccessF030planner)) or (form == u'090' and QtGui.qApp.userHasAnyRight([urAccessF090planner,])):
            dlg = CPreF030Dialog(self, self.contractTariffCache)
            try:
                dlg.setBegDateEvent(eventSetDatetime.date() if isinstance(eventSetDatetime, QDateTime) else eventSetDatetime)
                dlg.prepare(clientId, eventTypeId, eventDate, self.personId, self.personSpecialityId, self.personTariffCategoryId, 
                            flagHospitalization, actionTypeIdValue, tissueTypeId, presentActionTypes = presentActionTypes, maxOccursLimitActionTypes = maxOccursLimitActionTypes)
                if dlg.diagnosticsTableIsNotEmpty() or dlg.actionsTableIsNotEmpty():
                    if not dlg.exec_():
                        return False
                return self._prepare(clientId, eventTypeId, orgId, personId, eventSetDatetime, eventDatetime,
                                     weekProfile, numDays, dlg.diagnostics(), dlg.actions(),
                                     dlg.disabledActionTypeIdList, externalId, assistantId, curatorId,
                                     actionTypeIdValue, valueProperties, relegateOrgId, relegatePersonId,
                                     diagnos, financeId, protocolQuoteId, actionByNewEvent, order,
                                     typeQueue, relegateInfo, plannedEndDate, isEdit)
            finally:
                dlg.deleteLater()
        else:
            presets = CPreF030DagnosticAndActionPresets(clientId, eventTypeId, eventDate, self.personSpecialityId, 
                                                        flagHospitalization, actionTypeIdValue, presentActionTypes = presentActionTypes, 
                                                        maxOccursLimitActionTypes = maxOccursLimitActionTypes)
            presets.setBegDateEvent(eventSetDatetime.date() if isinstance(eventSetDatetime, QDateTime) else eventSetDatetime)
            return self._prepare(clientId, eventTypeId, orgId, personId, eventSetDatetime, eventDatetime, weekProfile, numDays,
                                 presets.unconditionalDiagnosticList, presets.unconditionalActionList, presets.disabledActionTypeIdList,
                                 externalId, assistantId, curatorId, None, [], relegateOrgId, relegatePersonId, diagnos,
                                 financeId, protocolQuoteId, actionByNewEvent, order, typeQueue, relegateInfo, plannedEndDate, isEdit)


    def prepareActions(self, presetActions, disabledActions, actionTypeIdValue, valueProperties, diagnos, financeId, protocolQuoteId, actionByNewEvent, plannedEndDate):
        def addActionType(actionTypeId, amount, idListActionType, idListActionTypeIPH, actionFinance, idListActionTypeMoving, plannedEndDate):
            db = QtGui.qApp.db
            tableOrgStructure = db.table('OrgStructure')
            for iModel, model in enumerate([self.tabStatus.modelAPActions,
                          self.tabDiagnostic.modelAPActions,
                          self.tabCure.modelAPActions,
                          self.tabMisc.modelAPActions]):
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
                addActionType(actionTypeId, amount, idListActionType, idListActionTypeIPH, actionFinance, idListActionTypeMoving, plannedEndDate)



    def initFocus(self):
        if self.cmbContract.count() != 1:
            self.cmbContract.setFocus(Qt.OtherFocusReason)
        else:
            self.tblFinalDiagnostics.setFocus(Qt.OtherFocusReason)


#    def newDiagnosticRecord(self, template):
#        result = self.tblFinalDiagnostics.model().getEmptyRecord()
#        return result


    def setRecord(self, record):
        CEventEditDialog.setRecord(self, record)
        setDatetimeEditValue(self.edtBegDate, self.edtBegTime, record, 'setDate')
        setDatetimeEditValue(self.edtEndDate, self.edtEndTime, record, 'execDate')
        setRBComboBoxValue(self.cmbPerson,      record, 'execPerson_id')
        setRBComboBoxValue(self.cmbResult,      record, 'result_id')
        setDateEditValue(self.edtNextDate,      record, 'nextEventDate')
        self.cmbPrimary.setCurrentIndex(forceInt(record.value('isPrimary')) - 1)
        self.setExternalId(forceString(record.value('externalId')))
        self.initOrder(forceString(getEventAvailableOrders(record.value('eventType_id'))), forceInt(record.value('order')))
        self.setPersonId(self.cmbPerson.value())
        setRBComboBoxValue(self.cmbContract, record, 'contract_id')
        self.setPerson = forceRef(record.value('setPerson_id'))
        self._updateNoteByPrevEventId()
        self.tabNotes.setNotes(record)
        self.tabNotes.setEventEditor(self)
        self.loadDiagnostics(self.modelPreliminaryDiagnostics, self.itemId())
        self.loadDiagnostics(self.modelFinalDiagnostics, self.itemId())
        self.tabMedicalDiagnosis.load(self.itemId())
        self.loadVisits()
        self.setOrgStructAndPersonsInCmbPersons(self.eventTypeId)
        self.grpTempInvalid.pickupTempInvalid()
        self.grpAegrotat.pickupTempInvalid()
        self.grpDisability.pickupTempInvalid()
        self.grpVitalRestriction.pickupTempInvalid()
        self.updateMesMKB()
        self.tabMes.setRecord(record)
        self.loadActions()
        self.tabCash.load(self.itemId())
        self.on_cmbResult_currentIndexChanged()
        self.initFocus()
        self.setIsDirty(False)
        self.blankMovingIdList = []
        self.protectClosedEvent()
        iniExportEvent(self)
        self.actSurveillancePlanningClients.setEnabled(bool(self.getDiagnosticIdList(self.clientId)))
        self.btnRelatedEventHighlight()

    def setOrgStructAndPersonsInCmbPersons(self, eventTypeId):
        orgstructureListByEventtype = getOrgstructureListByEventtypeId(eventTypeId)
        personListByEventtype = getPersonListByEventtypeId(eventTypeId)
        self.cmbPerson.setOrgStructureList(orgstructureListByEventtype)
        self.cmbPerson.setPersonIdList(personListByEventtype)
        self.modelActionsSummary._cols[
            self.modelActionsSummary.getColIndex('person_id')].orgStructureIdList = orgstructureListByEventtype
        self.modelActionsSummary._cols[
            self.modelActionsSummary.getColIndex('person_id')].personIdList = personListByEventtype

    def loadVisits(self):
        self.modelVisits.loadItems(self.itemId())
        self.updateVisitsInfo()


    def getEventDataPlanning(self, eventId):
        if eventId:
            db = QtGui.qApp.db
            tableEvent = db.table('Event')
            tableEventType = db.table('EventType')
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
                    tableEvent['id'].eq(eventId),
                    tableEventType['deleted'].eq(0)
                    ]
            table = tableEvent.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
            record = db.getRecordEx(table, cols, cond)
            if record:
                patientModelId = forceRef(record.value('patientModel_id'))
                if patientModelId:
                    self.tabNotes.cmbPatientModel.setValue(patientModelId)
                cureTypeId = forceRef(record.value('cureType_id'))
                if cureTypeId:
                    self.tabNotes.cmbCureType.setValue(cureTypeId)
                cureMethodId = forceRef(record.value('cureMethod_id'))
                if cureMethodId:
                    self.tabNotes.cmbCureMethod.setValue(cureMethodId)
                if self.prolongateEvent:
                    self.cmbContract.setValue(forceRef(record.value('contract_id')))
                    self.tabNotes.edtEventExternalIdValue.setText(forceString(record.value('externalId')))
                    self.tabNotes.edtEventNote.setText(forceString(record.value('note')))
                    self.prevEventId = eventId
                    self.lblProlongateEvent.setText(u'п')
                    self.tabNotes.edtPrevEventInfo.setText(u'Продолжение обращения: %s от %s.'%(forceString(record.value('name')), forceDate(record.value('setDate')).toString('dd.MM.yyyy')))
            if self.prolongateEvent or self.flagHospitalization:
                self.loadEventDiagnostics(self.modelPreliminaryDiagnostics, self.prevEventId)
            else:
                self.createDiagnostics(eventId)


    def createDiagnostics(self, eventId):
        if eventId:
            self.loadDiagnostics(self.modelPreliminaryDiagnostics, eventId)
            self.loadDiagnostics(self.modelFinalDiagnostics, eventId)


    def loadDiagnostics(self, modelDiagnostics, eventId):
        db = QtGui.qApp.db
        table = db.table('Diagnostic')
#        tablePerson = db.table('Person')
        isDiagnosisManualSwitch = modelDiagnostics.manualSwitchDiagnosis()
        rawItems = db.getRecordList(table, '*', [table['deleted'].eq(0), table['event_id'].eq(eventId), modelDiagnostics.filter], 'id')
        items = []
        for record in rawItems:
#            specialityId = forceRef(record.value('speciality_id'))
            diagnosisId     = record.value('diagnosis_id')
            MKB             = db.translate('Diagnosis', 'id', forceRef(diagnosisId), 'MKB')
            MKBEx           = db.translate('Diagnosis', 'id', forceRef(diagnosisId), 'MKBEx')
            exSubclassMKB   = db.translate('Diagnosis', 'id', forceRef(diagnosisId), 'exSubclassMKB')
            morphologyMKB   = db.translate('Diagnosis', 'id', forceRef(diagnosisId), 'morphologyMKB')
            setDate         = forceDate(record.value('setDate'))
            newRecord =  modelDiagnostics.getEmptyRecord()
            copyFields(newRecord, record)
            newRecord.setValue('MKB',           MKB)
            newRecord.setValue('MKBEx',         MKBEx)
            newRecord.setValue('exSubclassMKB', exSubclassMKB)
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

            newRecord._dirty = False
            items.append(newRecord)
        modelDiagnostics.setItems(items)
        modelDiagnostics.cols()[modelDiagnostics.getColIndex('healthGroup_id')].setFilter(getHealthGroupFilter(forceString(self.clientBirthDate.toString('yyyy-MM-dd')), forceString(self.eventSetDateTime.date().toString('yyyy-MM-dd'))))



    def getRecord(self):
        record = CEventEditDialog.getRecord(self)
        showTime = getEventShowTime(self.eventTypeId)
        self.getShowButtonAccount()
        self.getShowButtonTemperatureList()
        self.getShowButtonNomenclatureExpense()
        self.getShowButtonJobTickets()
#перенести в exec_ в случае успеха или в accept?
        CF030Dialog.defaultEventResultId = self.cmbResult.value()
        getRBComboBoxValue(self.cmbContract,    record, 'contract_id')
#        getDateEditValue(self.edtPrevDate,      record, 'prevEventDate')
        getDatetimeEditValue(self.edtBegDate, self.edtBegTime, record, 'setDate', showTime)
        record.setValue('setPerson_id', self.setPerson)
        getDatetimeEditValue(self.edtEndDate, self.edtEndTime, record, 'execDate', showTime)
        getRBComboBoxValue(self.cmbPerson,      record, 'execPerson_id')
        getRBComboBoxValue(self.cmbResult,      record, 'result_id')
        getDateEditValue(self.edtNextDate,      record, 'nextEventDate')
        record.setValue('isPrimary', toVariant(self.cmbPrimary.currentIndex() + 1))
        record.setValue('order',  toVariant(self.cmbOrder.currentIndex()+1))
        if self.prolongateEvent:
            record.setValue('order', toVariant(5))
        self.tabMes.getRecord(record)
        self.tabNotes.getNotes(record, self.eventTypeId)
        # Это хак: удаляем payStatus из записи
        result = type(record)(record) # copy record
        result.remove(result.indexOf('payStatus'))
        return result


    def saveInternals(self, eventId):
        self.saveVisits(eventId)
        self.saveDiagnostics(self.modelPreliminaryDiagnostics, eventId)
        self.saveDiagnostics(self.modelFinalDiagnostics, eventId)
        self.tabMedicalDiagnosis.save(eventId)
        self.tabMes.save(eventId)
        setAskedClassValueForDiagnosisManualSwitch(None)
        self.saveActions(eventId)
        self.tabCash.save(eventId)
        self.saveBlankUsers(self.blankMovingIdList)
        self.tabNotes.saveAttachedFiles(eventId)
        self.saveTrailerActions(eventId)
        self.setIsAssertNoMessage(False)
        self.saveTempInvalid()


    def saveTrailerActions(self, eventId):
        if self.trailerActions:
            for action in self.trailerActions:
                prevActionId = self.trailerIdList.get(action.trailerIdx - 1, None)
                action.getRecord().setValue('prevAction_id', toVariant(prevActionId))
                action.save(eventId)


    def afterSave(self):
        CEventEditDialog.afterSave(self)
        QtGui.qApp.session("F030_resultId", self.cmbResult.value())


    def saveVisits(self, eventId):
        items = self.modelVisits.items()
        personIdVariant = toVariant(self.personId)
#        financeIdVariant = QtGui.qApp.db.translate('Person', 'id', personIdVariant, 'finance_id')

        for item in items:
            if not forceRef(item.value('person_id')):
                item.setValue('person_id', personIdVariant)
            if not forceDate(item.value('date')):
                item.setValue('date', toVariant(self.eventSetDateTime))
#            item.setValue('finance_id', financeIdVariant)
        self.modelVisits.saveItems(eventId)


    def saveDiagnostics(self, modelDiagnostics, eventId):
        items = modelDiagnostics.items()
        isDiagnosisManualSwitch = modelDiagnostics.manualSwitchDiagnosis()
#        isFirst = True
        begDate = self.edtBegDate.date()
        endDate = self.edtEndDate.date()
        date = endDate if endDate else begDate
        MKBDiagnosisIdPairList = []
        prevId=0
        for item in items:    #Date of registration at the dispensary  dispanserBegDate
            MKB = forceStringEx(item.value('MKB'))
            MKBEx = forceStringEx(item.value('MKBEx'))
            TNMS = forceStringEx(item.value('TNMS'))
            morphologyMKB = forceStringEx(item.value('morphologyMKB'))
            diagnosisTypeId = forceRef(item.value('diagnosisType_id'))
            personId = forceRef(item.value('person_id'))
            if not personId:
                personId = self.personId
                item.setValue('person_id', toVariant(self.personId))
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


    def getAssociatedDiagnosisMKB(self):
        MKB = self.modelFinalDiagnostics.getAssociatedDiagnosisMKB()
        if not MKB:
            MKB = self.modelPreliminaryDiagnostics.getAssociatedDiagnosisMKB()
        return MKB


    def getComplicationDiagnosisMKB(self):
        MKB = self.modelFinalDiagnostics.getComplicationDiagnosisMKB()
        if not MKB:
            MKB = self.modelPreliminaryDiagnostics.getComplicationDiagnosisMKB()
        return MKB


    def getFinalDiagnosisId(self):
        id = self.modelFinalDiagnostics.getFinalDiagnosisId()
        if not id:
            id = self.modelPreliminaryDiagnostics.getFinalDiagnosisId()
        return id


    def saveActions(self, eventId):
        self.tabStatus.saveActions(eventId)
        self.tabDiagnostic.saveActions(eventId)
        self.tabCure.saveActions(eventId)
        self.tabMisc.saveActions(eventId)


    def setOrgId(self, orgId):
        self.orgId = orgId
        self.cmbContract.setOrgId(orgId)
        self.cmbPerson.setOrgId(orgId)
        self.tabStatus.setOrgId(orgId)
        self.tabDiagnostic.setOrgId(orgId)
        self.tabCure.setOrgId(orgId)
        self.tabMisc.setOrgId(orgId)


    def setEventTypeId(self, eventTypeId):
        CEventEditDialog.setEventTypeId(self, eventTypeId, u'Ф.030')
        self.tabCash.windowTitle = self.windowTitle()
        showTime = getEventShowTime(eventTypeId)
        showVisitTime = getEventShowVisitTime(self.eventTypeId)
        if showVisitTime:
            self.modelVisits._cols[self.modelVisits.getColIndex('date')] = CDateTimeForEventInDocTableCol(u'Дата', 'date', 20)
        self.getShowButtonAccount()
        self.getShowButtonTemperatureList()
        self.getShowButtonNomenclatureExpense()
        self.getShowButtonJobTickets()
        self.edtBegTime.setVisible(showTime)
        self.edtEndTime.setVisible(showTime)
        self.cmbResult.setTable('rbResult', True, 'eventPurpose_id=\'%d\'' % self.eventPurposeId)
        cols = self.modelFinalDiagnostics.cols()
        resultCol = cols[len(cols)-1]
        resultCol.filter = 'eventPurpose_id=\'%d\'' % self.eventPurposeId
        self.cmbContract.setEventTypeId(eventTypeId)
        self.setVisitAssistantVisible(self.tblVisits, hasEventVisitAssistant(eventTypeId))
        customizePrintButton(self.btnPrint, self.eventContext if self.eventContext else 'F030')


    def resetActionTemplateCache(self):
        self.tabStatus.actionTemplateCache.reset()
        self.tabDiagnostic.actionTemplateCache.reset()
        self.tabCure.actionTemplateCache.reset()
        self.tabMisc.actionTemplateCache.reset()


    # этот код повторяется 4 раза!
    def updateVisitsInfo(self):
        items = self.modelVisits.items()
        self.lblVisitsCountValue.setText(str(len(items)))
        minDate = maxDate = None
        for item in items:
            date = forceDate(item.value('date'))
            if date:
                if minDate:
                    minDate = min(minDate, date)
                    maxDate = max(maxDate, date)
                else:
                    minDate = maxDate = date
        if minDate:
            days = minDate.daysTo(maxDate)+1
        else:
            days = 0
        self.lblVisitsDurationValue.setText(str(days))


    def checkDataEntered(self):
        result = CEventEditDialog.checkDataEntered(self)
        tabList = [self.tabStatus, self.tabDiagnostic, self.tabCure, self.tabMisc]
        self.blankMovingIdList = []
        showTime = getEventShowTime(self.eventTypeId)
        if showTime:
            begDate = QDateTime(self.edtBegDate.date(), self.edtBegTime.time())
            endDate = QDateTime(self.edtEndDate.date(), self.edtEndTime.time())
        else:
            begDate = self.edtBegDate.date()
            endDate = self.edtEndDate.date()
        begDateCheck = self.edtBegDate.date()
        endDateCheck = self.edtEndDate.date()
        nextDate = self.edtNextDate.date()
        mesRequired = getEventMesRequired(self.eventTypeId)
        result = result and (self.orgId != QtGui.qApp.currentOrgId() or self.cmbContract.value() or self.checkInputMessage(u'договор', False, self.cmbContract))
        result = result and (self.cmbPerson.value() or self.checkInputMessage(u'врача', False, self.cmbPerson))
        result = result and self.checkExecPersonSpeciality(self.cmbPerson.value(), self.cmbPerson)
        result = result and (begDateCheck or self.checkInputMessage(u'дату назначения', False, self.edtBegDate))
#        result = result and (endDate or self.checkInputMessage(u'дату выполнения', False, self.edtEndDate))
        if not endDateCheck:
            result = result and self.checkDiagnosticsPersonSpeciality()
            result = result and self.checkEventDate(begDate, endDate, nextDate, self.tabToken, self.edtNextDate,  self.edtEndDate, True)
        else:
#            maxEndDate = self.getMaxEndDateByVisits()
#            if maxEndDate:
#                if QtGui.QMessageBox.question(self,
#                                    u'Внимание!',
#                                    u'Дата выполнения обращения не указана.\nУстановить дату завершения по максимальной дате посещений',
#                                    QtGui.QMessageBox.No|QtGui.QMessageBox.Yes,
#                                    QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
#                    self.edtEndDate.setDate(maxEndDate)
#                    endDate = maxEndDate
            result = result and self.checkActionDataEntered(begDate, QDateTime(), endDate, self.tabToken, self.edtBegDate, None, self.edtEndDate)
            result = result and self.checkEventDate(begDate, endDate, nextDate, self.tabToken, self.edtNextDate,  self.edtEndDate, True)
            minDuration,  maxDuration = getEventDurationRange(self.eventTypeId)
            if minDuration<=maxDuration:
                result = result and (begDateCheck.daysTo(endDateCheck)+1>=minDuration or self.checkValueMessage(u'Длительность должна быть не менее %s'%formatNum(minDuration, (u'дня', u'дней', u'дней')), False, self.edtEndDate))
                result = result and (maxDuration==0 or begDateCheck.daysTo(endDateCheck)+1<=maxDuration or self.checkValueMessage(u'Длительность должна быть не более %s'%formatNum(maxDuration, (u'дня', u'дней', u'дней')), False, self.edtEndDate))
            result = result and (len(self.modelFinalDiagnostics.items())>0 or self.checkInputMessage(u'диагноз', False, self.tblFinalDiagnostics))
            result = result and (self.cmbResult.value()  or self.checkInputMessage(u'результат',   False, self.cmbResult))
            result = result and self.checkEventResult()
            result = result and self.checkDiagnosticsType()
            if mesRequired:
                result = result and self.tabMes.checkMesAndSpecification()
                result = result and (self.tabMes.chechMesDuration() or self.checkValueMessage(u'Длительность события должна попадать в интервал минимальной и максимальной длительности по требованию к МЭС', True, self.edtBegDate))
                result = result and self.checkDiagnosticsMKBForMes(self.tblFinalDiagnostics, self.tabMes.cmbMes.value())
            result = result and self.checkDiagnosticsDataEntered()
            result = result and self.checkExecDateForVisit(endDateCheck)
            result = result and self.checkExecPersonSpeciality(self.cmbPerson.value(), self.cmbPerson)
            result = result and self.checkDiagnosticsPersonSpeciality()
#            result = result and self.checkActionsDataEntered(begDate, endDate)
        result = result and self.checkActionsDateEnteredActuality(begDate, endDate, tabList)
        result = result and self.checkActionsDataEntered(begDate, endDate)
        result = result and self.checkDeposit(True)
        result = result and (self.checkCorrectlyEnteredPersons(self.cmbPerson
            ) if not QtGui.qApp.checkGlobalPreference('23:checkChosenPerson',
                                                      u'не выполнять') else True)
        result = result and (len(self.modelVisits.items())>0 or self.checkInputMessage(u'посещение', False, self.tblVisits))
        #result = result and self.checkVisitsDataEntered(begDate.date() if isinstance(begDate, QDateTime) else begDate, endDate.date() if isinstance(endDate, QDateTime) else endDate)
        result = result and self.checkVisitsDataEntered(begDate, endDate)
        result = result and self.tabCash.checkDataLocalContract()
        result = result and self.checkSerialNumberEntered()
        result = result and self.checkTabNotesEventExternalId()
        if self.edtEndDate.date():
            checkRequireAction, ActionTypeIdList = self.checkRequireAction(self.eventTypeId, tabList, self.personSpecialityId, self.modelFinalDiagnostics.items())
            result = result and checkRequireAction
            if ActionTypeIdList:
                self.setActionConsbyIds(ActionTypeIdList)
            result = result and self.checkAndUpdateExpertise(self.edtEndDate.date(), self.cmbPerson.value())
            if CFinanceType.getCode(self.eventFinanceId) == CFinanceType.CMI and QtGui.qApp.defaultKLADR()[:2] == u'23':
                checkEpic, ConsFlatCodeList, needsListNazOnko = self.checkConsultationOrEpicris(tabList)
                result = result and self.needOnkoDocs(ConsFlatCodeList)
                result = result and self.checkServiceDates(begDate, endDate)
        result = result and self.selectNomenclatureAddedActions(tabList)
        return result

    
    def checkDiagnosticsPersonSpeciality(self):
        result = True
        result = result and self.checkPersonSpecialityDiagnostics(self.modelPreliminaryDiagnostics, self.tblPreliminaryDiagnostics)
        result = result and self.checkPersonSpecialityDiagnostics(self.modelFinalDiagnostics, self.tblFinalDiagnostics)
        return result


    def checkDiagnosticsDataEntered(self):
        result = True
        result = result and self.checkDiagnostics(self.modelPreliminaryDiagnostics, self.tblPreliminaryDiagnostics, None)
        result = result and self.checkDiagnostics(self.modelFinalDiagnostics, self.tblFinalDiagnostics, self.cmbPerson.value())
        result = result and self.checkDiagnosisType(self.modelFinalDiagnostics, self.tblFinalDiagnostics)
        return result


    def checkDiagnostics(self, model, table, finalPersonId):
        for row, record in enumerate(model.items()):
            if not self.checkDiagnosticDataEntered(table, row, record):
                return False
        return True


    def checkDiagnosticsType(self):
        result = True
        endDate = self.edtEndDate.date()
        if endDate:
            result = result and self.checkDiagnosticsTypeEnd(self.modelFinalDiagnostics) or self.checkValueMessage(u'Необходимо указать заключительный диагноз', False, self.tblFinalDiagnostics)
        return result


    def checkDiagnosticsTypeEnd(self, model):
        for row, record in enumerate(model.items()):
            if  forceInt(record.value('diagnosisType_id')) == model.diagnosisTypeCol.ids[0]:
                return True
        return False


    def checkDiagnosticDataEntered(self, table, row, record):
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
        if result and forceInt(record.value('diagnosisType_id')) == table.model().diagnosisTypeCol.ids[0] and table == self.tblFinalDiagnostics:
            resultId = forceRef(record.value('result_id'))
            result = resultId or self.checkInputMessage(u'результат', False, table, row, record.indexOf('result_id'))
        result = result and self.checkPersonSpeciality(record, row, self.tblFinalDiagnostics)
        result = result and self.checkPeriodResultHealthGroup(record, row, table)
        return result


    def getVisitCount(self):
        return len(self.modelVisits.items())


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

    def getDiagnosisForOnko(self):
        diagnostics = self.modelFinalDiagnostics.items()
        mkb1, mkb2, mkb3 = '', '', ''
        if diagnostics:
            for record in diagnostics:
                diagnosis = forceRef(record.value('diagnosisType_id'))
                if diagnosis == 1:
                    mkb1 = forceString(record.value('MKB'))
                elif diagnosis == 5:
                    mkb3 = forceString(record.value('MKB'))
                elif diagnosis == 2 and mkb1 == '':
                    mkb1 = forceString(record.value('MKB'))
                else:
                    mkb2 = forceString(record.value('MKB'))
            return mkb1, mkb2, mkb3
        else:
            return '', '', ''

    def needOnkoDocs(self, ConsFlatCodeList):
        mkb = self.getDiagnosisForOnko()
        if mkbIsOnko(mkb[0], mkb[2]):
            regionalCode = getEventAidTypeRegionalCode(self.eventTypeId)
            if regionalCode not in ['301', '302', '511', '522'] and u'ControlListOnko' not in ConsFlatCodeList:
                self.setActionCons([u'ControlListOnko'])
                self.checkValueMessage(
                    u"Необходимо заполнить Контрольный лист учета при новообразовании", False, self.tabStatus)
                return False
            # if u'list_naz_onko' not in ConsFlatCodeList:
            #     self.setActionCons([u'list_naz_onko'])
            #     self.checkValueMessage(u"Необходимо заполнить Лист назначений (онко)", False, self.tabCure)
            #     return False
            # if u'KRIT' not in ConsFlatCodeList:
            #     self.setActionCons([u'KRIT'])
            #     self.checkValueMessage(
            #         u"Необходимо заполнить Дополнительные критерии лечения при определении КСГ", False, self.tabMisc)
            #     return False
        return True

    def getEventInfo(self, context):
        result = CEventEditDialog.getEventInfo(self, context)
        # ручная инициализация свойств
        result._isPrimary = self.cmbPrimary.currentIndex()+1
        # ручная инициализация таблиц
        result._actions = CActionInfoProxyList(context,
                [self.tabStatus.modelAPActions, self.tabDiagnostic.modelAPActions, self.tabCure.modelAPActions, self.tabMisc.modelAPActions, self.tabMedicalDiagnosis.tblEventMedicalDiagnosis.model()],
                result)
        result._diagnosises = CDiagnosticInfoProxyList(context, [self.modelPreliminaryDiagnostics, self.modelFinalDiagnostics])
        result._visits = CVisitInfoProxyList(context, self.modelVisits)
        return result


    def getTempInvalidInfo(self, context):
        return self.grpTempInvalid.getTempInvalidInfo(context)


    def updateVisitsByDiagnostics(self, diagnosticsModel):
        personIdList = diagnosticsModel.getPersonsWithSignificantDiagnosisType()
        self.modelVisits.addAbsentPersons(personIdList, self.eventDate)
        self.updateVisitsInfo()


    def updateMesMKB(self):
        MKB, MKBEx = self.getFinalDiagnosisMKB()
        associatedMKB = self.getAssociatedDiagnosisMKB()
        complicationMKB = self.getComplicationDiagnosisMKB()
        self.tabMes.setMKB(MKB)
        self.tabMes.setMKBEx(MKBEx)
        self.tabMes.setAssociatedMKB(associatedMKB)
        self.tabMes.setComplicationMKB(complicationMKB)


    def setContractId(self, contractId):
        if self.contractId != contractId:
            CEventEditDialog.setContractId(self, contractId)
            cols = self.tblActions.model().cols()
            if cols:
                cols[0].setContractId(contractId)
            self.tabCash.modelAccActions.setContractId(contractId)
            self.tabCash.updatePaymentsSum()

# # #

    @pyqtSignature('int')
    def on_tabWidget_currentChanged(self, index):
        self.tabMes.setEventEditor(self)
        widget = self.tabWidget.widget(index)
        if widget is not None:
            focusProxy = widget.focusProxy()
            if focusProxy:
                focusProxy.setFocus(Qt.OtherFocusReason)
        self.btnPrintMedicalDiagnosisEnabled(index)
        if index == 7: # amb card page
            self.tabAmbCard.resetWidgets()
        if index == 2 and self.eventTypeId:
            self.tabMes.setMESServiceTemplate(self.eventTypeId)
        for actionTab in self.getActionsTabsList():
            model = actionTab.modelAPActions
            criteriaList = []
            fractions = None
            for record, action in model.items():
                actionTypeId = forceRef(record.value('actionType_id'))
                actionType = CActionTypeCache.getById(actionTypeId) if actionTypeId else None
                if actionType.flatCode == 'KRIT':
                    for prop in action._properties:
                        if prop.type().valueType.name == u'Доп. классиф. критерий':
                            value = prop.getValue()
                            if value:
                                code = forceString(QtGui.qApp.db.translate('soc_spr80', 'id', value, 'code'))
                                criteriaList.append(code)
                if actionType.flatCode == 'ControlListOnko':
                    for prop in action._properties:
                        if prop.type().valueType.name == u'Количество фракций проведения лучевой терапии':
                            fractions = prop.getValue()
            self.tabMes.setAdditionalCriteria(criteriaList)
            self.tabMes.setFractions(fractions)


    @pyqtSignature('QDate')
    def on_edtBegDate_dateChanged(self, date):
        self.eventSetDateTime.setDate(date)
        self.setFilterResult(date)
#        contractId = self.cmbContract.value()
        self.cmbContract.setDate(self.getDateForContract())
#        self.cmbContract.setValue(contractId)
        self.cmbPerson.setBegDate(self.eventSetDateTime.date())
        self.setPersonDate(self.eventSetDateTime.date())
        self.tabStatus.setEndDate(self.eventSetDateTime.date())
        self.tabDiagnostic.setEndDate(self.eventSetDateTime.date())
        self.tabCure.setEndDate(self.eventSetDateTime.date())
        self.tabMisc.setEndDate(self.eventSetDateTime.date())
        self.tabMes.setEventBegDate(self.eventSetDateTime.date())
        self.emitUpdateActionsAmount()


    @pyqtSignature('QTime')
    def on_edtBegTime_timeChanged(self, time):
        self.eventSetDateTime.setTime(time)
        self.emitUpdateActionsAmount()


    @pyqtSignature('QDate')
    def on_edtEndDate_dateChanged(self, date):
        self.eventDate = QDate(date)
        self.cmbContract.setDate(self.getDateForContract())
        self.emitUpdateActionsAmount()
        self.setEnabledChkCloseEvent(self.eventDate)
        self.cmbPerson.setEndDate(date)
        self.tabMes.setExecDate(self.eventDate)
        if getEventShowTime(self.eventTypeId):
            time = QTime.currentTime() if date else QTime()
            self.edtEndTime.setTime(time)


    @pyqtSignature('')
    def on_cmbContract_valueChanged(self):
        contractId = self.cmbContract.value()
        self.setContractId(contractId)
        cols = self.tblActions.model().cols()
        if cols:
            cols[0].setContractId(contractId)


    @pyqtSignature('int')
    def on_cmbPerson_currentIndexChanged(self):
        oldPersonId = self.personId
        self.setPersonId(self.cmbPerson.value())
# что-то сомнительным показалось - ну поменяли отв. врача,
# всё равно менять врачей в действии вроде неправильно. или правильно?
        self.tabStatus.updatePersonId(oldPersonId, self.personId)
        self.tabDiagnostic.updatePersonId(oldPersonId, self.personId)
        self.tabCure.updatePersonId(oldPersonId, self.personId)
        self.tabMisc.updatePersonId(oldPersonId, self.personId)


    @pyqtSignature('')
    def on_modelPreliminaryDiagnostics_diagnosisChanged(self):
        self.updateVisitsByDiagnostics(self.sender())
        self.updateMesMKB()


    @pyqtSignature('')
    def on_modelFinalDiagnostics_diagnosisChanged(self):
        self.updateVisitsByDiagnostics(self.sender())
        self.updateMesMKB()


    @pyqtSignature('')
    def on_modelFinalDiagnostics_resultChanged(self):
        currentValue = self.cmbResult.value()
        if QtGui.qApp.provinceKLADR()[:2] == u'23' and CFinanceType.getCode(self.eventFinanceId) == 2:
            endDateCheck = self.edtEndDate.date()
            if not endDateCheck:
                endDateCheck = self.edtBegDate.date()
            resultCond = getNewResultCond(self.modelFinalDiagnostics.resultId(), endDateCheck)
        else:
            resultCond = ''
        self.cmbResult.setTable('rbResult', True, 'eventPurpose_id=\'%d\'  %s' % (self.eventPurposeId, resultCond))
        if forceBool(QtGui.qApp.preferences.appPrefs.get('fillDiagnosticsEventsResults', True)):
            CF030Dialog.defaultDiagnosticResultId = self.modelFinalDiagnostics.resultId()
            defaultResultId = getEventResultId(CF030Dialog.defaultDiagnosticResultId, self.eventPurposeId)
            if defaultResultId and isDefaultResultIdValid(defaultResultId, self.eventPurposeId, resultCond):
                self.cmbResult.setValue(defaultResultId)
            else:
                self.cmbResult.setValue(currentValue)
        else:
            self.cmbResult.setValue(currentValue)

# # #


    @pyqtSignature('')
    def on_actDiagnosticsAddAccomp_triggered(self):
        currentRow = self.tblFinalDiagnostics.currentIndex().row()
        if currentRow>=0:
            currentRecord = self.modelFinalDiagnostics.items()[currentRow]
            newRecord = self.modelFinalDiagnostics.getEmptyRecord()
            newRecord.setValue('diagnosisType', QVariant(CF030Dialog.dfAccomp))
            newRecord.setValue('speciality_id', currentRecord.value('speciality_id'))
            newRecord.setValue('healthGroup_id', currentRecord.value('healthGroup_id'))
            self.modelFinalDiagnostics.insertRecord(currentRow+1, newRecord)
            self.tblFinalDiagnostics.setCurrentIndex(self.modelFinalDiagnostics.index(currentRow+1, newRecord.indexOf('MKB')))


    @pyqtSignature('QModelIndex')
    def on_tblVisits_clicked(self, index):
        if index.isValid():
            self.setFilterVisitTypeCol(index, self.tblVisits, self.modelVisits)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelVisits_dataChanged(self, topLeft, bottomRight):
        self.updateVisitsInfo()


    @pyqtSignature('QModelIndex, int, int')
    def on_modelVisits_rowsInserted(self, parent, start, end):
        self.updateVisitsInfo()
        self.emitUpdateActionsAmount()


    @pyqtSignature('QModelIndex, int, int')
    def on_modelVisits_rowsRemoved(self, parent, start, end):
        self.updateVisitsInfo()
        self.emitUpdateActionsAmount()


    @pyqtSignature('int')
    def on_modelActionsSummary_currentRowMovedTo(self, row):
        self.tblActions.setCurrentIndex(self.modelActionsSummary.index(row, 0))


    @pyqtSignature('QModelIndex')
    def on_tblActions_doubleClicked(self, index):
        row = index.row()
        column = index.column()
        if 0 <= row < len(self.modelActionsSummary.itemIndex):
            page, row = self.modelActionsSummary.itemIndex[row]
            if page in [0, 1, 2, 3] and not column in [3, 4, 5, 7, 8]:
                self.tabWidget.setCurrentIndex(page+3)
                tbl = [self.tabStatus.tblAPActions, self.tabDiagnostic.tblAPActions, self.tabCure.tblAPActions, self.tabMisc.tblAPActions][page]
                tbl.setCurrentIndex(tbl.model().index(row, 0))


    @pyqtSignature('int')
    def on_btnPrint_printByTemplate(self, templateId):
        if self.checkPrintByTemplateAllowed(templateId):
            context = CInfoContext()
            eventInfo = self.getEventInfo(context)
            tempInvalidInfo = self.getTempInvalidInfo(context)

            data = {'event': eventInfo,
                    'client': eventInfo.client,
                    'tempInvalid': tempInvalidInfo
                    }
            applyTemplate(self, templateId, data, signAndAttachHandler=self.tabNotes.btnAttachedFiles.getSignAndAttachHandler())
        
    @pyqtSignature('')
    def on_btnPlanning_clicked(self):
        actionListToNewEvent = []
        self.prepare(self.clientId, self.eventTypeId, self.orgId, self.personId, self.eventDate, self.eventDate, None, None, None, None, None, isEdit=True)
        self.initPrevEventTypeId(self.eventTypeId, self.clientId)
        self.initPrevEventId(None)
        self.addActions(actionListToNewEvent)


# # # Actions # # #

class CF030BaseDiagnosticsModel(CMKBListInDocTableModel):
    __pyqtSignals__ = ('diagnosisChanged()',
                      )
    MKB_allowed_morphology = ['C', 'D']

    def __init__(self, parent, finishDiagnosisTypeCode, baseDiagnosisTypeCode, accompDiagnosisTypeCode, complicDiagnosisTypeCode):
        CMKBListInDocTableModel.__init__(self, 'Diagnostic', 'id', 'event_id', parent)
        self._parent = parent
        self.isManualSwitchDiagnosis = QtGui.qApp.defaultIsManualSwitchDiagnosis()
        self.isMKBMorphology = QtGui.qApp.defaultMorphologyMKBIsVisible()
        self.characterIdForHandleDiagnosis = None
        self.diagnosisTypeCol = CF030DiagnosisTypeCol( u'Тип', 'diagnosisType_id', 2, [finishDiagnosisTypeCode, baseDiagnosisTypeCode, accompDiagnosisTypeCode, complicDiagnosisTypeCode], smartMode=False)
        self.addCol(self.diagnosisTypeCol)
        self.addCol(CPersonFindInDocTableCol(u'Врач', 'person_id',  20, 'vrbPersonWithSpecialityAndOrgStr', parent=parent))
        self.addExtCol(CICDExInDocTableCol(u'МКБ',         'MKB',   7), QVariant.String)
        if QtGui.qApp.isExSubclassMKBVisible():
            self.addExtCol(CMKBExSubclassCol(u'РСК', 'exSubclassMKB', 10), QVariant.String).setToolTip(u'Расширенная субклассификация МКБ')
        self.addExtCol(CICDExInDocTableCol(u'Доп.МКБ',     'MKBEx', 7), QVariant.String)
        if QtGui.qApp.isTNMSVisible():
            self.addCol(CTNMSCol(u'TNM-Ст', 'TNMS',  10))
        if QtGui.qApp.isClinicalGroupDiagnosticVisible():
            self.addCol(CEnumInDocTableCol(u'КГ', 'clinicalGroup', 30, [u'', u'1а - подозрение', u'1б - предрак', u'2 - подлежат радикальному лечению', u'3 - ремиссия', u'4 - подлежат паллиативному лечению'])).setToolTip(u'Клиническая группа')
        if self.isMKBMorphology:
            self.addExtCol(CMKBMorphologyCol(u'Морф.', 'morphologyMKB', 10, 'MKB_Morphology', filter='`group` IS NOT NULL'), QVariant.String)
        self.addCol(CDiseaseCharacter(     u'Хар',         'character_id',   7, showFields=CRBComboBox.showCode, preferredWidth=150)).setToolTip(u'Характер')
        if self.isManualSwitchDiagnosis:
            self.addExtCol(CBoolInDocTableCol( u'П',   'handleDiagnosis', 10), QVariant.Int)
            self.characterIdForHandleDiagnosis = forceRef(QtGui.qApp.db.translate('rbDiseaseCharacter', 'code', '1', 'id'))

        self.addCol(CDiseasePhases(        u'Фаза',        'phase_id',       7, showFields=CRBComboBox.showCode, preferredWidth=150)).setToolTip(u'Фаза')
        self.addCol(CDiseaseStage(         u'Ст',          'stage_id',       7, showFields=CRBComboBox.showCode, preferredWidth=150)).setToolTip(u'Стадия')
        self.addCol(CRBInDocTableCol(    u'ДН',            'dispanser_id',   7, 'rbDispanser', showFields=CRBComboBox.showCode, preferredWidth=150)).setToolTip(u'Диспансерное наблюдение')
        self.addCol(CRBLikeEnumInDocTableCol(u'Госп',      'hospital',       7, CHospitalInfo.names, showFields=CRBComboBox.showCode, preferredWidth=150)).setToolTip(u'Потребность в госпитализации')
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
                    if not (bool(mkb) and mkb[0] in CF030BaseDiagnosticsModel.MKB_allowed_morphology):
                        result = (result & ~Qt.ItemIsEditable)
            if QtGui.qApp.isExSubclassMKBVisible() and index.isValid():
                if column == self.getColIndex('exSubclassMKB'):
                    mkb = forceString(self.items()[row].value('MKB'))
                    if len(mkb) != 6:
                        return Qt.ItemIsSelectable | Qt.ItemIsEnabled
            if index.isValid():
                if column == self.getColIndex('MKBEx'):
                    mkb = forceString(self.items()[row].value('MKB'))
                    if not (bool(mkb) and mkb[0] in (u'S', u'T')):
                        return result & ~Qt.ItemIsEnabled
        return result


    def getEmptyRecord(self):
        eventEditor = QObject.parent(self)
        result = CMKBListInDocTableModel.getEmptyRecord(self)
        result.append(QtSql.QSqlField('diagnosis_id',     QVariant.Int))
        result.append(QtSql.QSqlField('speciality_id',    QVariant.Int))
        result.append(QtSql.QSqlField('setDate',          QVariant.DateTime))
        result.append(QtSql.QSqlField('endDate',          QVariant.DateTime))
        result.append(QtSql.QSqlField('cTumor_id',        QVariant.Int))
        result.append(QtSql.QSqlField('cNodus_id',        QVariant.Int))
        result.append(QtSql.QSqlField('cMetastasis_id',   QVariant.Int))
        result.append(QtSql.QSqlField('cTNMphase_id',     QVariant.Int))
        result.append(QtSql.QSqlField('pTumor_id',        QVariant.Int))
        result.append(QtSql.QSqlField('pNodus_id',        QVariant.Int))
        result.append(QtSql.QSqlField('pMetastasis_id',   QVariant.Int))
        result.append(QtSql.QSqlField('pTNMphase_id',     QVariant.Int))
        result.setValue('person_id',     toVariant(eventEditor.getSuggestedPersonId()))
        if self.items():
            result.setValue('diagnosisType_id',  toVariant(self.diagnosisTypeCol.ids[2]))
        else:
            result.setValue('diagnosisType_id',  toVariant(self.diagnosisTypeCol.ids[0] if self.diagnosisTypeCol.ids[0] else self.diagnosisTypeCol.ids[1]))
            result.setValue('result_id',  toVariant(CF030Dialog.defaultDiagnosticResultId if CF030Dialog.defaultDiagnosticResultId in getDiagnosticResultIdList(eventEditor.eventPurposeId, eventEditor.cmbResult.value()) else None))
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
            if index.isValid() and role == Qt.BackgroundRole and QtGui.qApp.preferences.propertyColor and index.column() == 2:
                if mkbIsVIMIS(forceString(self.items()[row].value('MKB'))):
                    return QVariant(QtGui.QBrush(QtGui.QColor(QtGui.qApp.preferences.propertyColor)))
            if index.isValid() and role == Qt.BackgroundRole and column == self.getColIndex('MKBEx'):
                if not Qt.ItemIsEnabled & index.flags():
                    return QVariant(QtGui.QBrush(QtGui.QColor(226, 228, 230)))
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
                    self.emitDiagnosisChanged()
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
                    self.updateClinicalGroup(row, oldMKB, specifiedMKB, eventEditor.itemId(), eventEditor.clientId, eventEditor.eventSetDateTime.date())
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
                self.emitDiagnosisChanged()
                return result
            elif row == len(self.items()) and column == self.getColIndex('MKBEx'):
                return False
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


    def updateToxicSubstancesByMKB(self, row, MKB):
        toxicSubstanceIdList = getToxicSubstancesIdListByMKB(MKB)
        item = self.items()[row]
        toxicSubstanceId = forceRef(item.value('toxicSubstances_id'))
        if toxicSubstanceId and toxicSubstanceId in toxicSubstanceIdList:
            return
        item.setValue('toxicSubstances_id', toVariant(None))
        self.emitCellChanged(row, item.indexOf('toxicSubstances_id'))


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


    def getPersonsWithSignificantDiagnosisType(self):
        result = []
        significantDiagnosisTypeIdList = [self.diagnosisTypeCol.ids[0], self.diagnosisTypeCol.ids[1]]
        for item in self.items():
            diagnosisTypeId = forceRef(item.value('diagnosisType_id'))
            if diagnosisTypeId and diagnosisTypeId in significantDiagnosisTypeIdList:
                personId = forceRef(item.value('person_id'))
                if personId and personId not in result:
                    result.append(personId)
        return result


    def getFinalDiagnosisMKB(self):
        finalDiagnosisTypeId = self.diagnosisTypeCol.ids[0] or self.diagnosisTypeCol.ids[1]
        items = self.items()
        for item in items:
            diagnosisTypeId = forceRef(item.value('diagnosisType_id'))
            if diagnosisTypeId == finalDiagnosisTypeId:
                return forceString(item.value('MKB')), forceString(item.value('MKBEx'))
        return '', ''


    def getAssociatedDiagnosisMKB(self):
        associatedDiagnosisTypeId = self.diagnosisTypeCol.ids[2]
        items = self.items()
        for item in items:
            diagnosisTypeId = forceRef(item.value('diagnosisType_id'))
            if diagnosisTypeId == associatedDiagnosisTypeId:
                return forceString(item.value('MKB'))
        return ''


    def getComplicationDiagnosisMKB(self):
        complicationDiagnosisTypeId = self.diagnosisTypeCol.ids[3]
        items = self.items()
        for item in items:
            diagnosisTypeId = forceRef(item.value('diagnosisType_id'))
            if diagnosisTypeId == complicationDiagnosisTypeId:
                return forceString(item.value('MKB'))
        return ''


    def getFinalDiagnosisId(self):
        finalDiagnosisTypeId = self.diagnosisTypeCol.ids[0]
        items = self.items()
        for item in items:
            diagnosisTypeId = forceRef(item.value('diagnosisType_id'))
            if diagnosisTypeId == finalDiagnosisTypeId:
                return forceRef(item.value('diagnosis_id'))
        return None


    def getBaseServiceIdMKB(self):
        serviceId = None
        MKB, MKBEx = self.getFinalDiagnosisMKB()
        if MKB:
            db = QtGui.qApp.db
            table = db.table('MKB')
            cond = [table['DiagID'].like(MKB)]
            record = db.getRecordEx(table, ['service_id'], cond)
            serviceId = forceRef(record.value('service_id')) if record else None
        return serviceId


    def emitDiagnosisChanged(self):
        self.emit(SIGNAL('diagnosisChanged()'))

    
    def saveItems(self, masterId = None):
        CMKBListInDocTableModel.saveItems(self, masterId)
        self.prophylaxisPlanningSync()


class CF030PreliminaryDiagnosticsModel(CF030BaseDiagnosticsModel):
    def __init__(self, parent):
        CF030BaseDiagnosticsModel.__init__(self, parent, None, '7', '11', None)


    def getMainDiagnosisTypeIdList(self):
        return [self.diagnosisTypeCol.ids[1]]
    
    
    def getEmptyRecord(self):
        result = CF030BaseDiagnosticsModel.getEmptyRecord(self)
        return result


class CF030FinalDiagnosticsModel(CF030BaseDiagnosticsModel):
    __pyqtSignals__ = ('resultChanged()',
                      )

    def __init__(self, parent):
        CF030BaseDiagnosticsModel.__init__(self, parent, '1', '2', '9', '3')
        self.addCol(CRBInDocTableCol(    u'Результат',     'result_id',     10, 'rbDiagnosticResult', showFields=CRBComboBox.showNameAndCode, preferredWidth=350))
        self.mapMKBToServiceId = {}


    def getCloseOrMainDiagnosisTypeIdList(self):
        return self.diagnosisTypeCol.ids[:2]


    def setData(self, index, value, role=Qt.EditRole):
        resultId = self.resultId()
        result = CF030BaseDiagnosticsModel.setData(self, index, value, role)
        eventEditor = QObject.parent(self)
        if resultId != self.resultId() or eventEditor.cmbResult.value() != self.resultId():
            self.emitResultChanged()
        return result


    def removeRowEx(self, row):
        resultId = self.resultId()
        self.removeRows(row, 1)
        eventEditor = QObject.parent(self)
        if resultId != self.resultId() or eventEditor.cmbResult.value() != self.resultId():
            self.emitResultChanged()


    def resultId(self):
        finalDiagnosisTypeId = self.diagnosisTypeCol.ids[0]
        items = self.items()
        for item in items:
            diagnosisTypeId = forceRef(item.value('diagnosisType_id'))
            if diagnosisTypeId == finalDiagnosisTypeId:
                return forceRef(item.value('result_id'))
        return None


    def diagnosisServiceId(self):
        items = self.items()
        if items:
            code = forceString(items[0].value('MKB'))
            if code in self.mapMKBToServiceId:
                return self.mapMKBToServiceId[code]
            else:
                serviceId = forceRef(QtGui.qApp.db.translate('MKB', 'DiagID', code, 'service_id'))
                self.mapMKBToServiceId[code] = serviceId
                return serviceId
        else:
            return None


    def emitResultChanged(self):
        self.emit(SIGNAL('resultChanged()'))


# ###################################################################


class CF030DiagnosisTypeCol(CDiagnosisTypeCol):
    def __init__(self, title=u'Тип', fieldName='diagnosisType_id', width=5, diagnosisTypeCodes=[], smartMode=True, **params):
        CDiagnosisTypeCol.__init__(self, title, fieldName, width, diagnosisTypeCodes, smartMode, **params)
        self.namesF030 = [u'Закл', u'Осн', u'Соп', u'Осл']


    def toString(self, val, record):
        id = forceRef(val)
        if id in self.ids:
            return toVariant(self.namesF030[self.ids.index(id)])
        return QVariant()


    def setEditorData(self, editor, value, record):
        editor.clear()
        if value.isNull():
            value = record.value(self.fieldName())
        id = forceRef(value)
        if self.smartMode:
            if id == self.ids[0]:
                editor.addItem(self.namesF030[0], toVariant(self.ids[0]))
            elif id == self.ids[1]:
                if self.ids[0]:
                    editor.addItem(self.namesF030[0], toVariant(self.ids[0]))
                editor.addItem(self.namesF030[1], toVariant(self.ids[1]))
            else:
                editor.addItem(self.namesF030[2], toVariant(self.ids[2]))
                editor.addItem(self.namesF030[3], toVariant(self.ids[3]))
        else:
            for itemName, itemId in zip(self.namesF030, self.ids):
                if itemId:
                    editor.addItem(itemName, toVariant(itemId))
        currentIndex = editor.findData(toVariant(id))
        editor.setCurrentIndex(currentIndex)
