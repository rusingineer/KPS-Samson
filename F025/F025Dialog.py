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
##
## Форма 025: стат.талон и т.п.
##
#############################################################################

from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import Qt, QDate, QDateTime, QModelIndex, QObject, QTime, QVariant, pyqtSignature, SIGNAL

from Events.Action import CActionTypeCache, CAction
from Events.ExportMIS import iniExportEvent
from Events.RelatedEventAndActionListDialog import CRelatedEventAndActionListDialog
from Events.TeethEventInfo import CTeethEventInfo
from F088.F0882022EditDialog import CEventExportTableModel, CAdvancedExportTableModel
from Orgs.Utils import getOrgstructureListByEventtypeId, getPersonListByEventtypeId
from library.Attach.AttachAction import getAttachAction
from library.Calendar           import getNextWorkDay
from library.crbcombobox        import CRBComboBox
from library.ICDInDocTableCol   import CICDExInDocTableCol
from library.ICDMorphologyInDocTableCol import CMKBMorphologyCol
from library.InDocTable         import CBoolInDocTableCol, CDateTimeForEventInDocTableCol, CInDocTableCol, CMKBListInDocTableModel, CRBInDocTableCol, CRBLikeEnumInDocTableCol, CEnumInDocTableCol
from library.interchange        import getDateEditValue, getDatetimeEditValue, getRBComboBoxValue, setDateEditValue, setDatetimeEditValue, setRBComboBoxValue
from library.PrintInfo          import CInfoContext
from library.PrintTemplates     import applyTemplate, customizePrintButton, getPrintButton
from library.TNMS.TNMSComboBox  import CTNMSCol
from library.MKBExSubclassComboBox import CMKBExSubclassCol
from library.Utils import copyFields, forceBool, forceDate, forceInt, forceRef, forceString, formatNum, toVariant, \
    variantEq, forceStringEx, forceDateTime

from Events.ActionInfo          import CActionInfoProxyList
from Events.ActionServiceType   import CActionServiceType
from Events.ActionsSummaryModel import CFxxxActionsSummaryModel
from Events.EventEditDialog     import CEventEditDialog, CDiseaseCharacter, CDiseaseStage, CDiseasePhases, CToxicSubstances, getToxicSubstancesIdListByMKB
from Events.EventInfo           import CDiagnosticInfoProxyList, CHospitalInfo, CVisitInfoProxyList
from Events.EventVisitsModel    import CEventVisitsModel
from Events.DiagnosisType       import CDiagnosisTypeCol
from Events.Utils import checkDiagnosis, checkIsHandleDiagnosisIsChecked, CTableSummaryActionsMenuMixin, \
    getAvailableCharacterIdByMKB, getDiagnosisId2, getDiagnosisPrimacy, getEventAddVisit, getEventAvailableOrders, getEventDurationRange, \
    getEventIsPrimary, getEventMesRequired, getEventResultId, getEventSetPerson, getEventShowTime, \
    getEventShowVisitTime, getHealthGroupFilter, hasEventVisitAssistant, isEventLong, \
    setAskedClassValueForDiagnosisManualSwitch, getEventAidTypeRegionalCode, getNewResultCond, \
    isDefaultResultIdValid, CFinanceType, mkbIsOnko, getEventTypeForm, mkbIsVIMIS
from F025.PreF025Dialog         import CPreF025Dialog, CPreF025DagnosticAndActionPresets
from Users.Rights               import urAccessF025planner, urAccessF090planner, urAdmin, urEditEndDateEvent, urRegTabWriteRegistry, urRegTabReadRegistry, urCanReadClientVaccination, urCanEditClientVaccination

from F025.Ui_F025               import Ui_Dialog


class CF025Dialog(CEventEditDialog, Ui_Dialog, CTableSummaryActionsMenuMixin):
    defaultEventResultId = None
    defaultDiagnosticResultId = None

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
        self.addModels('Diagnostics', CF025DiagnosticsModel(self))
        self.addModels('ActionsSummary', CFxxxActionsSummaryModel(self, True))
        self.addModels('Export', CEventExportTableModel(self))
        self.addModels('Export_FileAttach', CAdvancedExportTableModel(self))
        self.addModels('Export_VIMIS', CAdvancedExportTableModel(self))
        self.createSaveAndCreateAccountButton()

# ui
        self.addObject('actEditClient', QtGui.QAction(u'Открыть регистрационную карточку', self))
        self.addObject('actPortal_Doctor', QtGui.QAction(u'Перейти на портал врача', self))
        self.addObject('actShowAttachedToClientFiles', getAttachAction('Client_FileAttach',  self))
        self.addObject('actShowContingentsClient', QtGui.QAction(u'Показать все наблюдаемые контингенты', self))
        self.addObject('actOpenClientVaccinationCard', QtGui.QAction(u'Открыть прививочную карту', self))
        self.addObject('actSurveillancePlanningClients', QtGui.QAction(u'Контрольная карта диспансерного наблюдения', self))
        self.setupDiagnosticsMenu()
        self.addObject('btnPrint', getPrintButton(self, ''))
        # self.addObject('btnMedicalCommission', QtGui.QPushButton(u'ВК', self))
        self.addObject('btnPlanning', QtGui.QPushButton(u'Планировщик', self))
        self.addObject('btnRelatedEvent', QtGui.QPushButton(u'Связанные события', self))
        self.addObject('btnTemperatureList', QtGui.QPushButton(u'Температурный лист', self))
        self.addObject('btnPrintMedicalDiagnosis', getPrintButton(self, '', u'Врачебный диагноз'))



        self.setupUi(self)

        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setWindowTitleEx(u'Осмотр Ф.025')

        self.setMedicalDiagnosisContext()
        self.tabToken.setFocusProxy(self.tblInspections)
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
        if QtGui.qApp.defaultKLADR()[:2] in ['23', '01']:
            self.buttonBox.addButton(self.btnPlanning, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnPrint, QtGui.QDialogButtonBox.ActionRole)
        self.setupSaveAndCreateAccountButton()
        # self.buttonBox.addButton(self.btnMedicalCommission, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnRelatedEvent, QtGui.QDialogButtonBox.ActionRole)

        self.buttonBox.addButton(self.btnTemperatureList, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnPrintMedicalDiagnosis, QtGui.QDialogButtonBox.ActionRole)
        self.setupActionSummarySlots()
# tables to rb and combo-boxes

# assign models
        self.tblVisits.setModel(self.modelVisits)
        if QtGui.qApp.defaultKLADR()[:2] != u'23':
            self.tblVisits.hideColumn(self.modelVisits.getColIndex('person_id'))
        self.tblInspections.setModel(self.modelDiagnostics)
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
        self.actEditClient.setEnabled(QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]))
        self.actOpenClientVaccinationCard.setEnabled(QtGui.qApp.userHasAnyRight([urCanReadClientVaccination, urCanEditClientVaccination]))
        self.tblVisits.addPopupDelRow()
        self.tblInspections.setPopupMenu(self.mnuDiagnostics)
        self.setupVisitsIsExposedPopupMenu()
        CTableSummaryActionsMenuMixin.__init__(self)


# default values
        db = QtGui.qApp.db
        table = db.table('rbScene')
        self.sceneListHome = QtGui.qApp.db.getIdList(table, 'id', table['code'].inlist(['2', '3']))
        self.sceneListAmb  = QtGui.qApp.db.getIdList(table, 'id', table['code'].inlist(['1']))

        self.setupDirtyCather()
        self.setIsDirty(False)
        self.blankMovingIdList = []
        self.clientId = None
        self.prolongateEvent = False
        self.prevEventId = None
        self.isSecondEntrance = True
        self.tabNotes.setEventEditor(self)

        self.tblActions.enableColsHide()
        self.tblActions.enableColsMove()

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
        self.tblInspections.addCreateF111(self)
        self.tblInspections.addUpdateF111(self)
# done


    def destroy(self):
        CEventEditDialog.deleteLater(self)
        self.tblVisits.setModel(None)
        self.tblInspections.setModel(None)
        self.tblActions.setModel(None)
        self.grpTempInvalid.deleteLater()
        self.grpAegrotat.deleteLater()
        self.grpDisability.deleteLater()
        self.grpVitalRestriction.deleteLater()
        self.tabStatus.deleteLater()
        self.tabDiagnostic.deleteLater()
        self.tabCure.deleteLater()
        self.tabMisc.deleteLater()
        self.tabCash.deleteLater()
        self.tabMes.deleteLater()
        del self.modelVisits
        del self.modelDiagnostics
        self.tabAmbCard.deleteLater()


    def getSuggestedPersonId(self):
        return self.personId


    def getModelFinalDiagnostics(self):
        return self.modelDiagnostics

    def onActionChanged(self, actionsSummaryRow):
        self.addVisitByActionSummaryRow(actionsSummaryRow, checkActionPersonIdIsEventPerson=False)
        self.closeEventByAction(actionsSummaryRow)


    def checkEqDateAndPersonDuringAddingVisitByAction(self, visitDate, actionEndDate, visitPersonId, actionPersonId):
        return visitDate == actionEndDate

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
    def on_btnPlanning_clicked(self):
        actionListToNewEvent = []
        self.prepare(self.clientId, self.eventTypeId, self.orgId, self.personId, self.eventDate, self.eventDate, None, None, None, None, None, isEdit=True)
        self.initPrevEventTypeId(self.eventTypeId, self.clientId)
        self.initPrevEventId(None)
        self.addActions(actionListToNewEvent)


    @pyqtSignature('')
    def on_btnTemperatureList_clicked(self):
        self.getTemperatureList(self.eventSetDateTime)


    def setupDiagnosticsMenu(self):
        self.addObject('mnuDiagnostics', QtGui.QMenu(self))
        self.addObject('actDiagnosticsRemove', QtGui.QAction(u'Удалить запись', self))
        self.mnuDiagnostics.addAction(self.actDiagnosticsRemove)


    def _prepare(self, clientId, eventTypeId, orgId, personId, eventSetDatetime, eventDatetime, weekProfile, numDays,
                 presetDiagnostics, presetActions, disabledActions, externalId, assistantId, curatorId,
                 actionTypeIdValue = None, valueProperties = [], relegateOrgId = None, relegatePersonId=None,
                 diagnos = None, financeId = None, protocolQuoteId = None, actionByNewEvent = [], order = 1,
                 typeQueue = -1, relegateInfo = [], plannedEndDate = None, isEdit = False):
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
        self.isSecondEntrance = False
        if not isEdit:
            self.eventSetDateTime = eventSetDatetime if isinstance(eventSetDatetime, QDateTime) else QDateTime(eventSetDatetime)
            self.eventDate = eventDatetime.date() if isinstance(eventDatetime, QDateTime) else eventDatetime
            self.edtBegDate.setDate(self.eventSetDateTime.date())
            self.edtBegTime.setTime(eventSetDatetime.time() if isinstance(eventSetDatetime, QDateTime) else QTime())
            self.edtEndDate.setDate(self.eventDate)
            self.edtEndTime.setTime(eventDatetime.time() if isinstance(eventDatetime, QDateTime) else QTime())
            self.setEnabledChkCloseEvent(self.eventDate)

            self.setOrgId(orgId if orgId else QtGui.qApp.currentOrgId())
            self.setEventTypeId(eventTypeId)
            self.setClientId(clientId)
            self.tabNotes.setNotesEx(externalId, assistantId, curatorId, relegateOrgId, relegatePersonId, clientId, relegateInfo)
            self.setExternalId(externalId)
            self.cmbPerson.setValue(personId)
            setPerson = getEventSetPerson(self.eventTypeId)
            if setPerson == 0:
                self.setPerson = personId
            elif setPerson == 1:
                self.setPerson = QtGui.qApp.userId
            self.edtNextDate.setDate(QDate())
            self.cmbPrimary.setCurrentIndex(getEventIsPrimary(eventTypeId))
            self.initOrder(forceString(getEventAvailableOrders(eventTypeId)), order+1)
            self.cmbContract.setCurrentIndex(0)
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
                visits.append(prepVisit(self.eventDate, personId))
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
            if presetDiagnostics:
                for MKB, dispanserId, healthGroupId, visitTypeId in presetDiagnostics:
                    item = self.modelDiagnostics.getEmptyRecord()
                    item.setValue('MKB', toVariant(MKB))
                    item.setValue('dispanser_id',   toVariant(dispanserId))
                    item.setValue('healthGroup_id', toVariant(healthGroupId))
                    characterIdList = getAvailableCharacterIdByMKB(MKB)
                    if characterIdList:
                        item.setValue('character_id', toVariant(characterIdList[0]))
                    self.modelDiagnostics.items().append(item)
                self.modelDiagnostics.reset()
        self.prepareActions(presetActions, disabledActions, actionTypeIdValue, valueProperties, diagnos, financeId, protocolQuoteId, actionByNewEvent, plannedEndDate)
        self.grpTempInvalid.pickupTempInvalid()
        self.grpAegrotat.pickupTempInvalid()
        self.grpDisability.pickupTempInvalid()
        self.grpVitalRestriction.pickupTempInvalid()
        self.setIsDirty(False)
        self.tabNotes.setEventEditor(self)
        self.isSecondEntrance = True
        self.setFilterResult(self.eventSetDateTime.date())
        return self.checkEventCreationRestriction() and self.checkDeposit()


    def prepare(self, clientId, eventTypeId, orgId, personId, eventSetDatetime, eventDatetime, weekProfile,
                numDays, externalId, assistantId, curatorId, flagHospitalization = False, actionTypeIdValue = None,
                valueProperties = [], tissueTypeId=None, selectPreviousActions=False, relegateOrgId = None,
                relegatePersonId=None, diagnos = None, financeId = None, protocolQuoteId = None,
                actionByNewEvent = [], order = 1,  actionListToNewEvent = [], typeQueue = -1, docNum=None, relegateInfo=[],
                plannedEndDate = None, mapJournalInfoTransfer = [], voucherParams = {}, isEdit=False):
        self.setPersonId(personId)
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
        if (form != u'090' and QtGui.qApp.userHasRight(urAccessF025planner)) or (form == u'090' and QtGui.qApp.userHasAnyRight([urAccessF090planner,])):
            dlg = CPreF025Dialog(self, self.contractTariffCache)
            try:
                dlg.setBegDateEvent(eventSetDatetime.date() if isinstance(eventSetDatetime, QDateTime) else eventSetDatetime)
                dlg.prepare(clientId, eventTypeId, eventDate, self.personId, self.personSpecialityId, self.personTariffCategoryId, 
                            flagHospitalization, actionTypeIdValue, tissueTypeId, self.itemId(), presentActionTypes = presentActionTypes, maxOccursLimitActionTypes = maxOccursLimitActionTypes)
                if dlg.diagnosticsTableIsNotEmpty() or dlg.actionsTableIsNotEmpty():
                    if not dlg.exec_():
                        return False
                return self._prepare(clientId, eventTypeId, orgId, personId, eventSetDatetime, eventDatetime, weekProfile, numDays,
                                     dlg.diagnostics(), dlg.actions(), dlg.disabledActionTypeIdList,
                                     externalId, assistantId, curatorId, actionTypeIdValue, valueProperties,
                                     relegateOrgId, relegatePersonId, diagnos, financeId, protocolQuoteId,
                                     actionByNewEvent, order, typeQueue, relegateInfo, plannedEndDate, isEdit)
            finally:
                dlg.deleteLater()
        else:
            presets = CPreF025DagnosticAndActionPresets(clientId, eventTypeId, eventDate, self.personSpecialityId,
                                                        flagHospitalization, actionTypeIdValue, presentActionTypes = presentActionTypes,
                                                        maxOccursLimitActionTypes = maxOccursLimitActionTypes)
            presets.setBegDateEvent(eventSetDatetime.date() if isinstance(eventSetDatetime, QDateTime) else eventSetDatetime)
            return self._prepare(clientId, eventTypeId, orgId, personId, eventSetDatetime, eventDatetime, weekProfile, numDays,
                                 presets.unconditionalDiagnosticList, presets.unconditionalActionList, presets.disabledActionTypeIdList,
                                 externalId, assistantId, curatorId, None, [], relegateOrgId, relegatePersonId,
                                 diagnos, financeId, protocolQuoteId, actionByNewEvent, order, typeQueue, relegateInfo, plannedEndDate, isEdit)

    def prepareActions(self, presetActions, disabledActions, actionTypeIdValue, valueProperties, diagnos, financeId, protocolQuoteId, actionByNewEvent, plannedEndDate=None):
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
        eventTypeId = self.getEventTypeId()
        def getServiceType(actionTypeId, serviceTypeResult, serviceTypeATIdList):
            if actionTypeId and actionTypeId not in serviceTypeATIdList:
                db = QtGui.qApp.db
                tableActionType = db.table('ActionType')
                recordST = db.getRecordEx(tableActionType, [tableActionType['serviceType']], [tableActionType['deleted'].eq(0), tableActionType['id'].eq(actionTypeId)])
                serviceType = forceInt(recordST.value('serviceType')) if recordST else None
                if serviceType == CActionServiceType.initialInspection:
                    serviceTypeResult = serviceType
                elif serviceType == CActionServiceType.reinspection and serviceTypeResult != 1:
                    serviceTypeResult = serviceType
                serviceTypeATIdList.append(actionTypeId)
            return serviceTypeResult, serviceTypeATIdList
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
            self.tblInspections.setFocus(Qt.OtherFocusReason)


#    def getQuotaTypeId(self):
#        quotaTypeId = None
#        db = QtGui.qApp.db
#        tableClientQuoting = db.table('Client_Quoting')
#        tableActionType = db.table('ActionType')
#        recordActionType = db.getRecordEx(tableActionType, [tableActionType['id']], [tableActionType['deleted'].eq(0), tableActionType['flatCode'].like(u'protocol')])
#        actionTypeId = forceRef(recordActionType.value('id')) if recordActionType else None
#
#        def getQuotaTypeIsModel(model):
#            db = QtGui.qApp.db
#            tableClientQuoting = db.table('Client_Quoting')
#            for record, action in model.items():
#                propertiesByIdList = action._actionType._propertiesById
#                for propertiesBy in propertiesByIdList.values():
#                    if u'квота пациента' in propertiesBy.typeName.lower():
#                        propertiesById = propertiesBy.id
#                        if propertiesById:
#                            quotaId = action._propertiesById[propertiesById].getValue()
#                            if quotaId:
#                                record = db.getRecordEx(tableClientQuoting, [tableClientQuoting['quotaType_id']], [tableClientQuoting['deleted'].eq(0), tableClientQuoting['id'].eq(quotaId)])
#                                if record:
#                                    quotaTypeId = forceRef(record.value('quotaType_id'))
#                                    if quotaTypeId:
#                                        return quotaTypeId
#            return None
#
#        for model in (self.tabStatus.modelAPActions,
#              self.tabDiagnostic.modelAPActions,
#              self.tabCure.modelAPActions,
#              self.tabMisc.modelAPActions):
#            if actionTypeId in model.actionTypeIdList:
#                for record, action in model.items():
#                    if actionTypeId == action._actionType.id:
#                        quotaTypeId = getQuotaTypeIsModel(model)
#
#
#
#
#        return quotaTypeId


    def newDiagnosticRecord(self, template):
        result = self.tblInspections.model().getEmptyRecord()
        return result


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
        self.loadVisits()
        self.loadDiagnostics(self.itemId())
        self.tabMedicalDiagnosis.load(self.itemId())
        self.grpTempInvalid.pickupTempInvalid()
        self.grpAegrotat.pickupTempInvalid()
        self.grpDisability.pickupTempInvalid()
        self.grpVitalRestriction.pickupTempInvalid()
        self.updateMesMKB()
        self.tabMes.setRecord(record)
        self.loadActions()
        self.tabCash.load(self.itemId())
        self.initFocus()
        self.setIsDirty(False)
        self.blankMovingIdList = []
        self.on_cmbResult_currentIndexChanged()
        self.protectClosedEvent()
        iniExportEvent(self)
        self.actSurveillancePlanningClients.setEnabled(bool(self.getDiagnosticIdList(self.clientId)))
        self.btnRelatedEventHighlight()
        self.setOrgStructAndPersonsInCmbPersons(self.eventTypeId)

    def setOrgStructAndPersonsInCmbPersons(self, eventTypeId):
        orgstructureListByEventtype = getOrgstructureListByEventtypeId(eventTypeId)
        personListByEventtype = getPersonListByEventtypeId(eventTypeId)
        self.cmbPerson.setOrgStructureList(orgstructureListByEventtype)
        self.cmbPerson.setPersonIdList(personListByEventtype)
        self.modelVisits._cols[self.modelVisits.getColIndex('person_id')].orgStructureIdList = orgstructureListByEventtype
        self.modelVisits._cols[self.modelVisits.getColIndex('person_id')].personIdList = personListByEventtype
        self.modelActionsSummary._cols[
            self.modelActionsSummary.getColIndex('person_id')].orgStructureIdList = orgstructureListByEventtype
        self.modelActionsSummary._cols[self.modelActionsSummary.getColIndex('person_id')].personIdList = personListByEventtype

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
            self.createDiagnostics(eventId)


    def createDiagnostics(self, eventId):
        if eventId:
            self.loadDiagnostics(eventId)


    def loadDiagnostics(self, eventId):
        db = QtGui.qApp.db
        table = db.table('Diagnostic')
#        tablePerson = db.table('Person')
        isDiagnosisManualSwitch = self.modelDiagnostics.manualSwitchDiagnosis()
        rawItems = db.getRecordList(table, '*', [table['deleted'].eq(0), table['event_id'].eq(eventId)], 'id')
        items = []
        for record in rawItems:
#            specialityId = forceRef(record.value('speciality_id'))
            diagnosisId     = record.value('diagnosis_id')
            MKB             = db.translate('Diagnosis', 'id', forceRef(diagnosisId), 'MKB') #wtf? три transtale подряд.
            MKBEx           = db.translate('Diagnosis', 'id', forceRef(diagnosisId), 'MKBEx')
            morphologyMKB   = db.translate('Diagnosis', 'id', forceRef(diagnosisId), 'morphologyMKB')
            exSubclassMKB   = db.translate('Diagnosis', 'id', forceRef(diagnosisId), 'exSubclassMKB')
            setDate         = forceDate(record.value('setDate'))
            newRecord = self.modelDiagnostics.getEmptyRecord()
            copyFields(newRecord, record)
            newRecord.setValue('MKB',           MKB)
            newRecord.setValue('MKBEx',         MKBEx)
            newRecord.setValue('exSubclassMKB', exSubclassMKB)
            newRecord.setValue('morphologyMKB', morphologyMKB)
            self.modelDiagnostics.updateMKBTNMS(newRecord, MKB)
            self.modelDiagnostics.updateMKBToExSubclass(newRecord, MKB)
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
        self.modelDiagnostics.setItems(items)
        self.modelDiagnostics.cols()[self.modelDiagnostics.getColIndex('healthGroup_id')].setFilter(getHealthGroupFilter(forceString(self.clientBirthDate.toString('yyyy-MM-dd')), forceString(self.eventSetDateTime.date().toString('yyyy-MM-dd'))))


    def getRecord(self):
        record = CEventEditDialog.getRecord(self)
        showTime = getEventShowTime(self.eventTypeId)
        self.getShowButtonAccount()
        self.getShowButtonTemperatureList()
        self.getShowButtonNomenclatureExpense()
        self.getShowButtonJobTickets()

#перенести в exec_ в случае успеха или в accept?
        CF025Dialog.defaultEventResultId = self.cmbResult.value()

        getRBComboBoxValue(self.cmbContract,    record, 'contract_id')
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
###  payStatus
        self.tabNotes.getNotes(record, self.eventTypeId)
        # Это хак: удаляем payStatus из записи
        result = type(record)(record) # copy record
        result.remove(result.indexOf('payStatus'))
        return result


    def saveInternals(self, eventId):
        self.saveVisits(eventId)
        self.saveDiagnostics(eventId)
        self.tabMedicalDiagnosis.save(eventId)
        self.tabMes.save(eventId)
        setAskedClassValueForDiagnosisManualSwitch(None)
        self.saveActions(eventId)
        self.tabCash.save(eventId)
        self.saveBlankUsers(self.blankMovingIdList)
        self.tabNotes.saveAttachedFiles(eventId)
        self.saveTrailerActions(eventId)
        self.setIsAssertNoMessage(False)


    def saveTrailerActions(self, eventId):
        if self.trailerActions:
            for action in self.trailerActions:
                prevActionId = self.trailerIdList.get(action.trailerIdx - 1, None)
                action.getRecord().setValue('prevAction_id', toVariant(prevActionId))
                action.save(eventId)


    def afterSave(self):
        CEventEditDialog.afterSave(self)
        QtGui.qApp.session("F025_resultId", self.cmbResult.value())

    def saveVisits(self, eventId):
#        items = self.modelVisits.items()                                                           #ymd
#        personIdVariant = toVariant(self.personId)                                                 #ymd
#        financeIdVariant = QtGui.qApp.db.translate('Person', 'id', personIdVariant, 'finance_id')  #ymd

#        for item in items:                                                                         #ymd
#            if QtGui.qApp.defaultKLADR()[:2] != u'23' and item.value('person_id') == None:
#                item.setValue('person_id', personIdVariant)                                        #ymd
#            item.setValue('finance_id', financeIdVariant)
        self.modelVisits.saveItems(eventId)
    
    def updatePersonSpecialityDiagnostics(self):
        db = QtGui.qApp.db
        items = self.modelDiagnostics.items()
        personIdVariant = toVariant(self.personId)
        specialityIdVariant = db.translate('Person', 'id', personIdVariant, 'speciality_id')
        for row, item in enumerate(items):
            item.setValue('speciality_id', specialityIdVariant)
            item.setValue('person_id', toVariant(self.personId))
            self.modelDiagnostics.emitRowChanged(row)
            

    def updateDiagnosisTypes(self):
        items = self.modelDiagnostics.items()
        isFirst = True
        for item in items:
            diagnosisTypeId = self.getDiagnosisTypeId(isFirst)
            item.setValue('diagnosisType_id', toVariant(diagnosisTypeId))
            isFirst = False


    def saveDiagnostics(self, eventId):
        items = self.modelDiagnostics.items()
        isDiagnosisManualSwitch = self.modelDiagnostics.manualSwitchDiagnosis()
        isFirst = True
        endDate = self.edtEndDate.date()
        endDateVariant = toVariant(endDate)
        personIdVariant = toVariant(self.personId)
        specialityIdVariant = QtGui.qApp.db.translate('Person', 'id', personIdVariant, 'speciality_id')
        MKBDiagnosisIdPairList = []
        prevId = 0
        for row, item in enumerate(items):
            MKB = forceStringEx(item.value('MKB'))
            MKBEx = forceStringEx(item.value('MKBEx'))
            TNMS = forceStringEx(item.value('TNMS'))
            morphologyMKB = forceStringEx(item.value('morphologyMKB'))
            diagnosisTypeId = self.getDiagnosisTypeId(isFirst)

            item.setValue('diagnosisType_id', toVariant(diagnosisTypeId))
            item.setValue('speciality_id', specialityIdVariant)
            item.setValue('person_id', toVariant(self.personId) )
            item.setValue('setDate', endDateVariant )
            item.setValue('endDate', endDateVariant )
            diagnosisId = forceRef(item.value('diagnosis_id'))
            characterId = forceRef(item.value('character_id'))

            diagnosisId, characterId = getDiagnosisId2(
                    endDate,
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
                    exSubclassMKB=forceStringEx(item.value('exSubclassMKB'))
                    )
            item.setValue('diagnosis_id', toVariant(diagnosisId))
            item.setValue('TNMS', toVariant(TNMS))
            item.setValue('character_id', toVariant(characterId))
            itemId = forceInt(item.value('id'))
            if prevId>itemId:
                item.setValue('id', QVariant())
                prevId=0
            else:
               prevId=itemId
            isFirst = False
            MKBDiagnosisIdPairList.append((MKB, diagnosisId))
        self.modelDiagnostics.saveItems(eventId)
        self.modifyDiagnosises(MKBDiagnosisIdPairList)


    def getFinalDiagnosisMKB(self):
        diagnostics = self.modelDiagnostics.items()
        if diagnostics:
            MKB   = forceString(diagnostics[0].value('MKB'))
            MKBEx = forceString(diagnostics[0].value('MKBEx'))
            return MKB, MKBEx
        else:
            return '', ''


    def getFinalDiagnosisId(self):
        diagnostics = self.modelDiagnostics.items()
        return forceRef(diagnostics[0].value('diagnosis_id')) if diagnostics else None


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
        CEventEditDialog.setEventTypeId(self, eventTypeId, u'Ф.025')
        self.getShowButtonAccount()
        self.getShowButtonTemperatureList()
        self.getShowButtonNomenclatureExpense()
        self.getShowButtonJobTickets()
        self.tabCash.windowTitle = self.windowTitle()
        showTime = getEventShowTime(eventTypeId)
        showVisitTime = getEventShowVisitTime(self.eventTypeId)
        if showVisitTime:
            self.modelVisits._cols[self.modelVisits.getColIndex('date')] = CDateTimeForEventInDocTableCol(u'Дата', 'date', 20)
        self.edtBegTime.setVisible(showTime)
        self.edtEndTime.setVisible(showTime)
        self.cmbResult.setTable('rbResult', True, 'eventPurpose_id=\'%d\'' % self.eventPurposeId)
        if forceBool(QtGui.qApp.preferences.appPrefs.get('fillDiagnosticsEventsResults', True)):
            resultId = QtGui.qApp.session("F025_resultId")
            self.cmbResult.setValue(resultId)
        cols = self.modelDiagnostics.cols()
        resultCol = cols[len(cols)-1]
        resultCol.filter = 'eventPurpose_id=\'%d\'' % self.eventPurposeId
        self.cmbContract.setEventTypeId(eventTypeId)
        self.setVisitAssistantVisible(self.tblVisits, hasEventVisitAssistant(eventTypeId))
        customizePrintButton(self.btnPrint, self.eventContext if self.eventContext else 'F025')


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
        tabList = [self.tabStatus, self.tabDiagnostic, self.tabCure, self.tabMisc]
        result = CEventEditDialog.checkDataEntered(self)
        self.blankMovingIdList = []
        mesRequired = getEventMesRequired(self.eventTypeId)
        result = result and (self.orgId != QtGui.qApp.currentOrgId() or self.cmbContract.value() or self.checkInputMessage(u'договор', False, self.cmbContract))
        result = result and (self.cmbPerson.value() or self.checkInputMessage(u'врач', False, self.cmbPerson))
        result = result and self.checkExecPersonSpeciality(self.cmbPerson.value(), self.cmbPerson)
#        result = result and (self.cmbResult.value()   or self.checkInputMessage(u'результат',   False, self.cmbResult))
        showTime = getEventShowTime(self.eventTypeId)
        begDateCheck = self.edtBegDate.date()
        endDateCheck = self.edtEndDate.date()
        if showTime:
            begDate = QDateTime(self.edtBegDate.date(), self.edtBegTime.time())
            endDate = QDateTime(self.edtEndDate.date(), self.edtEndTime.time())
        else:
            begDate = self.edtBegDate.date()
            endDate = self.edtEndDate.date()
        nextDate = self.edtNextDate.date()
        result = result and (begDateCheck.isValid() or self.checkInputMessage(u'дату назначения', False, self.edtBegDate))
        # fix TT 1026 "Отключить требование закрытия события для формы 025"
        # result = result and (endDateCheck.isValid() or self.checkInputMessage(u'дату выполнения', True, self.edtEndDate))
        if begDateCheck.isValid():
            result = result and self.checkActionDataEntered(begDate, QDateTime(), endDate, self.tabToken, self.edtBegDate, None, self.edtEndDate)
            result = result and self.checkEventDate(begDate, endDate, nextDate, self.tabToken, self.edtNextDate, self.edtEndDate, True)
            minDuration, maxDuration = getEventDurationRange(self.eventTypeId)
            if minDuration <= maxDuration and endDateCheck.isValid():
                result = result and (begDateCheck.daysTo(endDateCheck) + 1 >= minDuration or self.checkValueMessage(u'Длительность должна быть не менее %s' % formatNum(minDuration, (u'дня', u'дней', u'дней')), False, self.edtEndDate))
                result = result and (maxDuration==0 or begDateCheck.daysTo(endDateCheck)+1<=maxDuration or self.checkValueMessage(u'Длительность должна быть не более %s'%formatNum(maxDuration, (u'дня', u'дней', u'дней')), False, self.edtEndDate))

#        if not endDate:
#            maxEndDate = self.getMaxEndDateByVisits()
#            if maxEndDate:
#                if QtGui.QMessageBox.question(self,
#                                    u'Внимание!',
#                                    u'Дата выполнения обращения не указана.\nУстановить дату завершения по максимальной дате посещений',
#                                    QtGui.QMessageBox.No|QtGui.QMessageBox.Yes,
#                                    QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
#                    self.edtEndDate.setDate(maxEndDate)
#                    endDate = maxEndDate
        if endDateCheck.isValid():
            result = result and (self.cmbResult.value() or self.checkInputMessage(u'результат', False, self.cmbResult))
            result = result and self.checkEventResult()
            result = result and self.checkResultEvent(self.cmbResult.value(), endDateCheck, self.cmbResult)
            result = result and (len(self.modelDiagnostics.items()) > 0 or self.checkInputMessage(u'диагноз', False, self.tblInspections))
            result = result and self.checkDiagnosticsDataEntered()
            result = result and self.checkExecDateForVisit(endDateCheck)
            result = result and self.checkExecPersonSpeciality(self.cmbPerson.value(), self.cmbPerson)
            result = result and self.checkDiagnosticsPersonSpeciality()
            checkRequireAction, ActionTypeIdList = self.checkRequireAction(self.eventTypeId, tabList, self.personSpecialityId, self.modelDiagnostics.items())
            result = result and checkRequireAction
            if ActionTypeIdList:
                self.setActionConsbyIds(ActionTypeIdList)
            if mesRequired:
                result = result and self.tabMes.checkMesAndSpecification()
                result = result and (self.tabMes.chechMesDuration() or self.checkValueMessage(u'Длительность события должна попадать в интервал минимальной и максимальной длительности по требованию к МЭС', True, self.edtBegDate))
                result = result and self.checkInspectionsMKBForMes(self.tblInspections, self.tabMes.cmbMes.value())
        else:
            result = result and self.checkDiagnosticsPersonSpeciality()
        if getEventAddVisit(self.eventTypeId):
            result = result and (len(self.modelVisits.items()) > 0 or self.checkInputMessage(u'посещение', False, self.tblVisits))
        #result = result and self.checkVisitsDataEntered(begDate.date() if isinstance(begDate, QDateTime) else begDate, endDate.date() if isinstance(endDate, QDateTime) else endDate)
        result = result and self.checkVisitsDataEntered(begDate, endDate)
        result = result and self.checkActionsDateEnteredActuality(begDate, endDate, tabList)
        result = result and self.checkActionsDataEntered(begDate, endDate)
        result = result and self.checkDeposit(True)
        result = result and (self.checkCorrectlyEnteredPersons(self.cmbPerson
                                                              ) if not QtGui.qApp.checkGlobalPreference('23:checkChosenPerson',
                                                                                                        u'не выполнять') else True)
        result = result and (self.itemId() or self.primaryCheck())
        result = result and self.tabCash.checkDataLocalContract()
        result = result and self.checkSerialNumberEntered()
        result = result and self.checkTabNotesEventExternalId()
        if self.edtEndDate.date():
            result = result and self.checkAndUpdateExpertise(self.edtEndDate.date(), self.cmbPerson.value())
            if CFinanceType.getCode(self.eventFinanceId) == CFinanceType.CMI and QtGui.qApp.defaultKLADR()[:2] == u'23':
                checkEpic, ConsFlatCodeList, needsListNazOnko = self.checkConsultationOrEpicris(tabList)
                result = result and self.needOnkoDocs(ConsFlatCodeList)
                result = result and self.checkNeedTNMS(self.tblInspections, ['cTNMphase_id'], ['pTNMphase_id'])
                result = result and self.checkServiceDates(begDate, endDate)
        result = result and self.selectNomenclatureAddedActions(tabList)
        return result

    
    def checkDiagnosticsPersonSpeciality(self):
        result = True
        result = result and self.checkPersonSpecialityDiagnostics(self.modelDiagnostics, self.tblInspections)
        return result


    def checkInspectionsMKBForMes(self, tableFinalDiagnostics, mesMKB):
        result, finalDiagnosis = self.checkMKBForMes(tableFinalDiagnostics, mesMKB, 2)
        return result


#    def getMaxEndDateByVisits(self):
#        result = QDate()
#        for record in self.modelVisits.items():
#            date = forceDate(record.value('date'))
#            if not date or result<date:
#                result = date
#        return result


    def checkDiagnosticsDataEntered(self):
        for row, record in enumerate(self.modelDiagnostics.items()):
            if not self.checkDiagnosticDataEntered(row, record):
                return False
        return True


    def checkDiagnosticDataEntered(self, row, record):
        result = True
        if result:
            MKB = forceString(record.value('MKB'))
            MKBEx = forceString(record.value('MKBEx'))
            specialityId = forceRef(QtGui.qApp.db.translate('Person', 'id', self.personId, 'speciality_id'))
            result = specialityId or self.checkValueMessage(u'Отсутствует специальность врача', False, self.tblInspections, row, record.indexOf('person_id'))
            result = result and MKB or self.checkInputMessage(u'диагноз', False, self.tblInspections, row, record.indexOf('MKB'))
            result = result and self.checkActualMKB(self.tblInspections, self.edtBegDate.date(), MKB, record, row)
            if result:
                char = MKB[:1]
                blockMKB = forceInt(MKB[1:3])
                traumaTypeId = forceRef(record.value('traumaType_id'))
                if char in 'ST' and not (char in 'T' and 36 <= blockMKB <= 78):
                    if not traumaTypeId:
                        result = self.checkValueMessage(u'Необходимо указать тип травмы',  True if QtGui.qApp.controlTraumaType()==0 else False, self.tblInspections, row, record.indexOf('traumaType_id'))
                    if result:
                        result = MKBEx or self.checkInputMessage(u'Дополнительный диагноз', True if QtGui.qApp.controlMKBExForTraumaType()==0 else False, self.tblInspections, row, record.indexOf('MKBEx'))
                        if result:
                            charEx = MKBEx[:1]
                            if charEx not in 'VWXY':
                                result = self.checkValueMessage(u'Доп.МКБ не соотвествует Доп.МКБ при травме', True, self.tblInspections, row, record.indexOf('MKBEx'))
                if char not in 'ST' and traumaTypeId:
                    result = self.checkValueMessage(u'Необходимо удалить тип травмы', False, self.tblInspections, row, record.indexOf('traumaType_id'))
                if getEventAidTypeRegionalCode(self.eventTypeId) not in ['111', '112', '241', '242']:
                    result = self.checkRequiresFillingDispanser(result, self.tblInspections, record, row, MKB)
        if result and row == 0:
            resultId = forceRef(record.value('result_id'))
            result = result and resultId or self.checkInputMessage(u'результат', False, self.tblInspections, row, record.indexOf('result_id'))
#        result = result and (self.cmbResult.value()   or self.checkInputMessage(u'результат',   False, self.cmbResult))
        result = result and self.checkPersonSpeciality(record, row, self.tblInspections)
        result = result and self.checkPeriodResultHealthGroup(record, row, self.tblInspections)
        return result

    def getDiagnosisForOnko(self):
        diagnostics = self.modelDiagnostics.items()
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
        return True

    def checkRowEndDate(self, begDate, endDate, row, record, widget):
        result = True
        column = record.indexOf('endDate')
        rowEndDate = forceDate(record.value('endDate'))
        if rowEndDate:
            if rowEndDate>endDate:
                result = result and self.checkValueMessage(u'Дата выполнения должна быть не позже %s' % forceString(endDate), False, widget, row, column)
#            if rowEndDate < lowDate:
#                result = result and self.checkValueMessage(u'Дата выполнения должна быть не раньше %s' % forceString(lowDate), False, widget, row, column)
        return result


    def primaryCheck(self):
        record = self.modelDiagnostics.items()[0] if self.modelDiagnostics.items() else None
        if record:
            MKB = forceString(record.value('MKB'))
            characterId = forceRef(record.value('character_id'))
            diagnosisPrimacy = getDiagnosisPrimacy(self.clientId, self.eventDate, MKB, characterId)
            newValue = 0 if diagnosisPrimacy else 1
            isPrimary = self.cmbPrimary.currentIndex()
            if isPrimary < 2 and newValue != isPrimary:
                if QtGui.QMessageBox.question(self,
                                    u'Внимание!',
                                    u'Указание первичности обращения противоречит данным ЛУД.\nИзменить признак первичности?',
                                    QtGui.QMessageBox.No|QtGui.QMessageBox.Yes,
                                    QtGui.QMessageBox.Yes) == QtGui.QMessageBox.Yes:
                    self.cmbPrimary.setCurrentIndex(newValue)
        return True


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
        return forceRef(QtGui.qApp.db.translate('rbDiagnosisType', 'code', '1' if dt else '9', 'id'))


    def getEventInfo(self, context):
        result = CEventEditDialog.getEventInfo(self, context, CTeethEventInfo)
        # ручная инициализация свойств
        result._isPrimary = self.cmbPrimary.currentIndex()+1
        # ручная инициализация таблиц
        result._actions = CActionInfoProxyList(context,
                [self.tabStatus.modelAPActions, self.tabDiagnostic.modelAPActions, self.tabCure.modelAPActions, self.tabMisc.modelAPActions, self.tabMedicalDiagnosis.tblEventMedicalDiagnosis.model()],
                result)
        self.updateDiagnosisTypes()
        result.initActions()  # инициализируем _action_stomat и _action_parodent
        result._diagnosises = CDiagnosticInfoProxyList(context, [self.modelDiagnostics])
        result._visits = CVisitInfoProxyList(context, self.modelVisits)
        return result


    def updateMesMKB(self):
        MKB, MKBEx = self.getFinalDiagnosisMKB()
        self.tabMes.setMKB(MKB)
        self.tabMes.setMKBEx(MKBEx)


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
        widget = self.tabWidget.widget(index)
        if widget is not None:
            focusProxy = widget.focusProxy()
            if focusProxy:
                focusProxy.setFocus(Qt.OtherFocusReason)
        self.btnPrintMedicalDiagnosisEnabled(index)
        if index == 2 and self.eventTypeId:
            self.tabMes.setMESServiceTemplate(self.eventTypeId)
        if index == 7: # amb card page
            self.tabAmbCard.resetWidgets()


    @pyqtSignature('QDate')
    def on_edtBegDate_dateChanged(self, date):
        self.eventSetDateTime.setDate(date)
        if self.isSecondEntrance:
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
        if QtGui.qApp.userHasRight(urEditEndDateEvent):
            self.eventDate = QDate(date) # так как на самом деле мы получаем ссылку на дату
            self.cmbPerson.setEndDate(date)
            self.cmbContract.setDate(self.getDateForContract())
            self.emitUpdateActionsAmount()
            self.setEnabledChkCloseEvent(self.eventDate)
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
        self.updatePersonSpecialityDiagnostics()
        # self.modelVisits.updatePersonAndService()
# что-то сомнительным показалось - ну поменяли отв. врача,
# всё равно менять врачей в действии вроде неправильно. или правильно?
        self.tabStatus.updatePersonId(oldPersonId, self.personId)
        self.tabDiagnostic.updatePersonId(oldPersonId, self.personId)
        self.tabCure.updatePersonId(oldPersonId, self.personId)
        self.tabMisc.updatePersonId(oldPersonId, self.personId)
# # #


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


    @pyqtSignature('')
    def on_mnuDiagnostics_aboutToShow(self):
        canRemove = False
        currentRow = self.tblInspections.currentIndex().row()
        if currentRow>=0:
            canRemove = self.modelDiagnostics.payStatus(currentRow) == 0
        self.actDiagnosticsRemove.setEnabled(canRemove)


    @pyqtSignature('')
    def on_modelDiagnostics_diagnosisChanged(self):
        self.updateMesMKB()


    @pyqtSignature('')
    def on_modelDiagnostics_diagnosisServiceChanged(self):
        self.modelVisits.updatePersonAndService()


    @pyqtSignature('')
    def on_modelDiagnostics_resultChanged(self):
        currentValue = self.cmbResult.value()
        if QtGui.qApp.provinceKLADR()[:2] == u'23' and CFinanceType.getCode(self.eventFinanceId) == 2:
            endDateCheck = self.edtEndDate.date()
            if not endDateCheck:
                endDateCheck = self.edtBegDate.date()
            resultCond = getNewResultCond(self.modelDiagnostics.resultId(), endDateCheck)
        else:
            resultCond = ''
        self.cmbResult.setTable('rbResult', True, 'eventPurpose_id=\'%d\'  %s' % (self.eventPurposeId, resultCond))
        if forceBool(QtGui.qApp.preferences.appPrefs.get('fillDiagnosticsEventsResults', True)):
            CF025Dialog.defaultDiagnosticResultId = self.modelDiagnostics.resultId()
            defaultResultId = getEventResultId(CF025Dialog.defaultDiagnosticResultId, self.eventPurposeId)
            if defaultResultId and isDefaultResultIdValid(defaultResultId, self.eventPurposeId, resultCond):
                self.cmbResult.setValue(defaultResultId)
            else:
                self.cmbResult.setValue(currentValue)
        else:
            self.cmbResult.setValue(currentValue)


    @pyqtSignature('')
    def on_actDiagnosticsRemove_triggered(self):
        currentRow = self.tblInspections.currentIndex().row()
        self.modelDiagnostics.removeRowEx(currentRow)
        self.updateDiagnosisTypes()


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


    def getTempInvalidInfo(self, context):
        return self.grpTempInvalid.getTempInvalidInfo(context)


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

# # # Actions # # #

#
# #####################################################################################33
#

class CF025DiagnosticsModel(CMKBListInDocTableModel):
    __pyqtSignals__ = ('diagnosisServiceChanged()',
                       'diagnosisChanged()',
                       'resultChanged()'
                      )
    MKB_allowed_morphology = ['C', 'D']
    def __init__(self, parent):
        CMKBListInDocTableModel.__init__(self, 'Diagnostic', 'id', 'event_id', parent)
        self.isManualSwitchDiagnosis = QtGui.qApp.defaultIsManualSwitchDiagnosis()
        self.isMKBMorphology = QtGui.qApp.defaultMorphologyMKBIsVisible()
        self.characterIdForHandleDiagnosis = None
        finishDiagnosisTypeCode = '1'
        accompDiagnosisTypeCode = '9'
        self.diagnosisTypeCol = CF025DiagnosisTypeCol( u'Тип', 'diagnosisType_id', 2, [finishDiagnosisTypeCode, accompDiagnosisTypeCode], smartMode=False)
        self.addCol(self.diagnosisTypeCol)
        self.addExtCol(CICDExInDocTableCol(u'МКБ',         'MKB',   7), QVariant.String)
        if QtGui.qApp.isExSubclassMKBVisible():
            self.addExtCol(CMKBExSubclassCol(u'РСК', 'exSubclassMKB', 20), QVariant.String).setToolTip(u'Расширенная субклассификация МКБ')
        self.addExtCol(CICDExInDocTableCol(u'Доп.МКБ',     'MKBEx', 7), QVariant.String)
        if QtGui.qApp.isTNMSVisible():
            self.addCol(CTNMSCol(u'TNM-Ст', 'TNMS',  10))
        if QtGui.qApp.isClinicalGroupDiagnosticVisible():
            self.addCol(CEnumInDocTableCol(u'КГ', 'clinicalGroup', 30, [u'', u'1а - подозрение', u'1б - предрак', u'2 - подлежат радикальному лечению', u'3 - ремиссия', u'4 - подлежат паллиативному лечению'])).setToolTip(u'Клиническая группа')
        if self.isMKBMorphology:
            self.addExtCol(CMKBMorphologyCol(u'Морф.', 'morphologyMKB', 10, 'MKB_Morphology', filter='`group` IS NOT NULL'), QVariant.String)
        self.addCol(CDiseaseCharacter(     u'Хар',           'character_id',   7, showFields=CRBComboBox.showCode, preferredWidth=150)).setToolTip(u'Характер')
        if self.isManualSwitchDiagnosis:
            self.addExtCol(CBoolInDocTableCol( u'П',   'handleDiagnosis', 10), QVariant.Int)
            self.characterIdForHandleDiagnosis = forceRef(QtGui.qApp.db.translate('rbDiseaseCharacter', 'code', '1', 'id'))

        self.addCol(CDiseasePhases(        u'Фаза',          'phase_id',       7, showFields=CRBComboBox.showCode, preferredWidth=150)).setToolTip(u'Фаза')
        self.addCol(CDiseaseStage(         u'Ст',            'stage_id',       7, showFields=CRBComboBox.showCode, preferredWidth=150)).setToolTip(u'Стадия')
        self.addCol(CRBInDocTableCol(      u'ДН',            'dispanser_id',   7, 'rbDispanser', showFields=CRBComboBox.showCode, preferredWidth=150)).setToolTip(u'Диспансерное наблюдение')
        self.addCol(CRBLikeEnumInDocTableCol(u'Госп',        'hospital',       7, CHospitalInfo.names, showFields=CRBComboBox.showCode, preferredWidth=150)).setToolTip(u'Потребность в госпитализации')
        self.addCol(CRBInDocTableCol(      u'Травма',        'traumaType_id', 10, 'rbTraumaType', addNone=True, showFields=CRBComboBox.showName, preferredWidth=150))
        self.addCol(CToxicSubstances(u'ТоксВещ', 'toxicSubstances_id', 10, addNone=True, showFields=CRBComboBox.showName, preferredWidth=150)).setToolTip(u'Токсичное вещество')
        self.addCol(CRBInDocTableCol(      u'ГрЗд',          'healthGroup_id', 7, 'rbHealthGroup', addNone=True, showFields=CRBComboBox.showCode, preferredWidth=150)).setToolTip(u'Группа здоровья')
        self.addCol(CInDocTableCol(u'Описание',     'freeInput', 15))
        self.addCol(CRBInDocTableCol(      u'Результат',     'result_id',     10, 'rbDiagnosticResult', showFields=CRBComboBox.showNameAndCode, preferredWidth=350))
        self.columnHandleDiagnosis = self.getColIndex('handleDiagnosis', None)
        self.columnResult = self.getColIndex('result_id', None)
        self.mapMKBToServiceId = {}
        self.eventEditor = parent
        self.readOnly = False
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


    def getEmptyRecord(self):
        result = CMKBListInDocTableModel.getEmptyRecord(self)
        result.append(QtSql.QSqlField('diagnosis_id',     QVariant.Int))
        result.append(QtSql.QSqlField('diagnosisType_id', QVariant.Int))
        result.append(QtSql.QSqlField('speciality_id',    QVariant.Int))
        result.append(QtSql.QSqlField('person_id',        QVariant.Int))
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
        empty = not self.items()
        if empty:
            result.setValue('result_id',  toVariant(CF025Dialog.defaultDiagnosticResultId))
        result.setValue('diagnosisType_id',  toVariant(self.eventEditor.getDiagnosisTypeId(empty)))
        result.setValue('person_id', toVariant(self.eventEditor.getSuggestedPersonId()))
        return result


    def getCloseOrMainDiagnosisTypeIdList(self):
        items = self.items()
        idList = []
        if len(items) > 0:
            idList = [forceRef(self.items()[0].value('diagnosisType_id'))]
        return idList
    
    
    def getMainDiagnosisTypeIdList(self):
        return []


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
                    if not (bool(mkb) and mkb[0] in CF025DiagnosticsModel.MKB_allowed_morphology):
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
            if index.isValid() and role == Qt.BackgroundRole and QtGui.qApp.preferences.propertyColor and index.column() == 1:
                if mkbIsVIMIS(forceString(self.items()[row].value('MKB'))):
                    return QVariant(QtGui.QBrush(QtGui.QColor(QtGui.qApp.preferences.propertyColor)))
            if index.isValid() and role == Qt.BackgroundRole and column == self.getColIndex('MKBEx'):
                if not Qt.ItemIsEnabled & index.flags():
                    return QVariant(QtGui.QBrush(QtGui.QColor(226, 228, 230)))
        return CMKBListInDocTableModel.data(self, index, role)

    def setData(self, index, value, role=Qt.EditRole):
        column = index.column()
        row = index.row()
        eventEditor = QObject.parent(self)
        if not variantEq(self.data(index, role), value):
            if column == 1: # код МКБ

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
                    acceptable, specifiedMKB, specifiedMKBEx, specifiedCharacterId, specifiedTraumaTypeId, specifiedDispanserId, specifiedRequiresFillingDispanser, specifiedProlongMKB = QObject.parent(self).specifyDiagnosis(newMKB)
                    if not acceptable:
                        return False
                value = toVariant(specifiedMKB)
                serviceId = self.diagnosisServiceId() if row == 0 else None
                oldMKB = forceString(self.items()[row].value('MKB')) if 0 <= row < len(self.items()) else None
                result = CMKBListInDocTableModel.setData(self, index, value, role)
                if result:
                    if specifiedRequiresFillingDispanser == 2:
                        self.updateDispanserByMKB(row, specifiedDispanserId, specifiedProlongMKB)
                    self.updateCharacterByMKB(row, specifiedMKB, specifiedCharacterId)
                    self.updateTraumaType(row, specifiedMKB, specifiedTraumaTypeId)
                    self.updateClinicalGroup(row, oldMKB, specifiedMKB, self.eventEditor.itemId(), self.eventEditor.clientId, self.eventEditor.eventSetDateTime.date())
                    self.updateToxicSubstancesByMKB(row, specifiedMKB)
                    self.updateTNMS(index, self.items()[row], specifiedMKB)
                    self.updateMKBTNMS(self.items()[row], specifiedMKB)
                    self.inheritMKBTNMS(self.items()[row], oldMKB, specifiedMKB, eventEditor.clientId, eventEditor.eventSetDateTime)
                    self.updateExSubclass(index, self.items()[row], specifiedMKB)
                    self.updateMKBToExSubclass(self.items()[row], specifiedMKB)
                    if row == 0:
                        self.emit(SIGNAL('diagnosisChanged()'))
                        if serviceId != self.diagnosisServiceId():
                            self.emit(SIGNAL('diagnosisServiceChanged()'))
                return result
            if 0 <= row < len(self.items()) and column == self.items()[row].indexOf('MKBEx'): # доп. код МКБ
                newMKB = forceString(value)
                if not newMKB:
                    pass
                else:
                    acceptable = QObject.parent(self).checkDiagnosis(newMKB)
                    if not acceptable:
                        return False
                value = toVariant(newMKB)
                result = CMKBListInDocTableModel.setData(self, index, value, role)
#                if result:
#                    self.updateCharacterByMKB(row, specifiedMKB)
                self.emit(SIGNAL('diagnosisChanged()'))
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
            result = CMKBListInDocTableModel.setData(self, index, value, role)
            if row == 0 and column == self.columnResult:
                self.emitResultChanged()
            return result
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


    def payStatus(self, row):
        if 0 <= row < len(self.items()):
            return forceInt(self.items()[row].value('payStatus'))
        else:
            return 0


    def removeRowEx(self, row):
        self.removeRows(row, 1)
        if row == 0:
            self.emitResultChanged()


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


    def resultId(self):
        items = self.items()
        if items:
            return forceRef(items[0].value('result_id'))
        else:
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
        
    
    def saveItems(self, masterId = None):
        CMKBListInDocTableModel.saveItems(self, masterId)
        self.prophylaxisPlanningSync()


class CF025DiagnosisTypeCol(CDiagnosisTypeCol):
    def __init__(self, title=u'Тип', fieldName='diagnosisType_id', width=5, diagnosisTypeCodes=[], smartMode=True, **params):
        CDiagnosisTypeCol.__init__(self, title, fieldName, width, diagnosisTypeCodes, smartMode, **params)
        self.namesF025 = [u'Закл', u'Соп']


    def toString(self, val, record):
        id = forceRef(val)
        if id in self.ids:
            return toVariant(self.namesF025[self.ids.index(id)])
        return QVariant()


    def setEditorData(self, editor, value, record):
        editor.clear()
        if value.isNull():
            value = record.value(self.fieldName())
        id = forceRef(value)
        if self.smartMode:
            if id == self.ids[0]:
                editor.addItem(self.namesF025[0], toVariant(self.ids[0]))
            elif id == self.ids[1]:
                if self.ids[0]:
                    editor.addItem(self.namesF025[0], toVariant(self.ids[0]))
                editor.addItem(self.namesF025[1], toVariant(self.ids[1]))
            else:
                editor.addItem(self.namesF025[2], toVariant(self.ids[2]))
                editor.addItem(self.namesF025[3], toVariant(self.ids[3]))
        else:
            for itemName, itemId in zip(self.namesF025, self.ids):
                if itemId:
                    editor.addItem(itemName, toVariant(itemId))
        currentIndex = editor.findData(toVariant(id))
        editor.setCurrentIndex(currentIndex)
