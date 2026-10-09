# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2026 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

# Форма 030: Этап диспансерного наблюдения

from Registry.ChangeDispanserBegDateLUD import CChangeDispanserBegDateLUD
from Registry.ProphylaxisPlanningInfo import CProphylaxisPlanningInfoProxyList
from Surveillance.ChangeDispanserPerson import CChangeDispanserPerson
from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QDate, QDateTime, QTime, QVariant, pyqtSignature, SIGNAL

from library.Attach.AttachAction import getAttachAction
from library.Calendar import getNextWorkDay
from library.InDocTable import CDateTimeForEventInDocTableCol
from library.interchange import getDateEditValue, getDatetimeEditValue, getRBComboBoxValue, setDateEditValue, setDatetimeEditValue, setRBComboBoxValue
from library.PrintInfo import CInfoContext
from library.PrintTemplates import applyTemplate, customizePrintButton, getPrintButton
from library.Utils import copyFields, forceBool, forceDate, forceInt, forceRef, forceString, formatNum, toVariant, forceStringEx, formatDate

from Events.Action import CActionTypeCache
from Events.ActionInfo import CActionInfoProxyList
from Events.ActionsSummaryModel import CFxxxActionsSummaryModel
from Events.EventAddChronicDiseasesDialog import CChronicDiseasesLoadDialog
from Events.EventEditDialog import CEventEditDialog
from Events.EventInfo import CDiagnosticInfoProxyList, CVisitInfoProxyList
from Events.EventVisitsModel import CEventVisitsModel
from Events.ExportMIS import iniExportEvent
from Events.RelatedEventAndActionListDialog import CRelatedEventAndActionListDialog
from Events.Utils import checkDiagnosis, checkIsHandleDiagnosisIsChecked, CTableSummaryActionsMenuMixin, \
    getAvailableCharacterIdByMKB, getDiagnosisId2, getEventAddVisit, getEventAvailableOrders, getEventDurationRange, getEventIsPrimary, \
    getEventMesRequired, getEventResultId, getEventSetPerson, getEventShowTime, \
    getEventShowVisitTime, getHealthGroupFilter, hasEventVisitAssistant, isEventLong, \
    setAskedClassValueForDiagnosisManualSwitch, getNewResultCond, isDefaultResultIdValid, \
    CFinanceType, mkbIsOnko, getEventTypeForm, getEventAidTypeRegionalCode
    
from F030.F030Models import CF030SurveillanceModel, CF030FinalDiagnosticsModel 
from F030.PreF030Dialog import CPreF030Dialog, CPreF030DagnosticAndActionPresets
from F088.F0882022EditDialog import CEventExportTableModel, CAdvancedExportTableModel
from Orgs.Utils import getOrgstructureListByEventtypeId, getPersonListByEventtypeId, getPersonInfo

from Users.Rights import urAccessF030planner, urAccessF090planner, urAdmin, urEditEndDateEvent, urRegTabWriteRegistry, urRegTabReadRegistry, urCanReadClientVaccination, urCanEditClientVaccination

from F030.Ui_F030 import Ui_Dialog


class CF030Dialog(CEventEditDialog, Ui_Dialog, CTableSummaryActionsMenuMixin):
    defaultEventResultId = None
    defaultDiagnosticResultId = None
    dfFinished = 1  # Заключительный
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
        self.addModels('FinalDiagnostics', CF030FinalDiagnosticsModel(self))
        self.addModels('Surveillance', CF030SurveillanceModel(self))
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
        self.addObject('actAddChronicDiseases', QtGui.QAction(u'Добавить хронические диагнозы', self))
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
        self.tblSurveillance.setModel(self.modelSurveillance)
        self.tblSurveillance.setDelRowsChecker(None)
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
        self.tblVisits.addPopupDelRow()
        self.setupVisitsIsExposedPopupMenu()
        self.tblFinalDiagnostics.addPopupAction(self.actAddChronicDiseases)
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
        self.connect(self.modelFinalDiagnostics, SIGNAL('diagnosisChanged(QString)'), self.on_modelFinalDiagnostics_diagnosisChanged)
        self.connect(self.modelFinalDiagnostics, SIGNAL('resultChanged()'), self.on_modelFinalDiagnostics_resultChanged)

        self.addObject('actChangePersonDN', QtGui.QAction(u'Изменить врача ДН', self))
        self.connect(self.actChangePersonDN, SIGNAL('triggered()'), self.on_actChangePersonDN_triggered)
        self.tblSurveillance.addPopupAction(self.actChangePersonDN)
        self.addObject('actChangeDispanserDate', QtGui.QAction(u'Изменить дату постановки на учет', self))
        self.connect(self.actChangeDispanserDate, SIGNAL('triggered()'), self.on_actChangeDispanserDate_triggered)
        self.tblSurveillance.addPopupAction(self.actChangeDispanserDate)
        self.connect(self.tblSurveillance.popupMenu(), SIGNAL('aboutToShow()'), self.on_popupMenu_aboutToShow)
        self.btnPrintMedicalDiagnosis.setVisible(False)
        
        # signal-slot bound
        self.tblFinalDiagnostics.popupMenuAboutToShow.connect(self.setFinalDiagnosticsMenuControlsState)
# done

    def setFinalDiagnosticsMenuControlsState(self):
        """
        Активность пункта меню "Вставить хронические диагнозы" в таблице Заключительный диагноз
        """
        self.actAddChronicDiseases.setEnabled(False)
        current = self.tblFinalDiagnostics.currentItem()
        if current and current.value('diagnosisType_id') == self.modelFinalDiagnostics.diagnosisTypeCol.codeToId(CF030Dialog.dfFinished):
            self.actAddChronicDiseases.setEnabled(True)


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
        
        self.loadDiagnostics(self.modelFinalDiagnostics, self.itemId())
        self.modelSurveillance.setEventEditor(self)
        self.modelSurveillance.setDiagnosticRecords(self.modelFinalDiagnostics.surveillanceRecords(self.clientId))
        self.modelSurveillance.setClientId(self.clientId)
        self.modelSurveillance.loadItems(None)
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
                pass
            else:
                self.createDiagnostics(eventId)


    def createDiagnostics(self, eventId):
        if eventId:
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
        self.saveDiagnostics(self.modelFinalDiagnostics, eventId)
        self.modelSurveillance.saveItems()
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
        return MKB, MKBEx


    def getAssociatedDiagnosisMKB(self):
        MKB = self.modelFinalDiagnostics.getAssociatedDiagnosisMKB()
        return MKB


    def getComplicationDiagnosisMKB(self):
        MKB = self.modelFinalDiagnostics.getComplicationDiagnosisMKB()
        return MKB


    def getFinalDiagnosisId(self):
        id = self.modelFinalDiagnostics.getFinalDiagnosisId()
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
        if not endDateCheck:
            result = result and self.checkDiagnosticsPersonSpeciality()
            result = result and self.checkEventDate(begDate, endDate, nextDate, self.tabToken, self.edtNextDate,  self.edtEndDate, True)
        else:
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
        result = result and self.checkSurveillanceDiagnosis()
        result = result and self.checkSurveillanceData()
        result = result and self.checkActionsDateEnteredActuality(begDate, endDate, tabList)
        result = result and self.checkActionsDataEntered(begDate, endDate)
        result = result and self.checkDeposit(True)
        result = result and (self.checkCorrectlyEnteredPersons(self.cmbPerson
            ) if not QtGui.qApp.checkGlobalPreference('23:checkChosenPerson',
                                                      u'не выполнять') else True)
        result = result and (len(self.modelVisits.items())>0 or self.checkInputMessage(u'посещение', False, self.tblVisits))
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
        result = result and self.checkPersonSpecialityDiagnostics(self.modelFinalDiagnostics, self.tblFinalDiagnostics)
        return result


    def checkDiagnosticsDataEntered(self):
        result = True
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
    
    
    def checkSurveillanceDiagnosis(self):
        result = True
        db = QtGui.qApp.db
        tableDiagnosis = db.table('Diagnosis')
        tableDispanser = db.table('rbDispanser')
        table = tableDiagnosis.leftJoin(tableDispanser, tableDispanser['id'].eq(tableDiagnosis['dispanser_id']))
        for row, item in enumerate(self.modelFinalDiagnostics.items()):
            if forceRef(item.value('dispanser_id')) in self.modelFinalDiagnostics.observedDispanserIdList:
                MKB = forceString(item.value('MKB'))
                if MKB:
                    diag = MKB
                    if len(MKB) >= 3:
                        diag = MKB[:3]
                    
                    cols = [
                        tableDiagnosis['id'],
                        tableDispanser['observed'],
                        tableDiagnosis['MKB']
                    ]
                    cond = [
                        tableDiagnosis['client_id'].eq(self.clientId),
                        tableDiagnosis['deleted'].eq(0),
                        '''EXISTS(SELECT Diagnostic.id
                                FROM Diagnostic
                                LEFT JOIN Event ON Event.id = Diagnostic.event_id
                                WHERE Diagnostic.diagnosis_id = Diagnosis.id
                                    AND Diagnostic.deleted = 0
                                    AND Event.deleted = 0)''',
                        tableDiagnosis['MKB'].like(diag+'%')
                    ]
                    diagnosisItems = db.getRecordList(table, cols, cond, tableDiagnosis['endDate'].name() + ' DESC')
                    if diagnosisItems:
                        haveObs = False
                        needCheck = True
                        for diagnosisItem in diagnosisItems:
                            diagMKB = forceString(diagnosisItem.value('MKB'))
                            observed = forceInt(diagnosisItem.value('observed'))
                            if diagMKB and observed:
                                if diagMKB == MKB:
                                    needCheck = False
                                    break
                                else:
                                    haveObs = True
                                    diag = diagMKB
                                    
                        if haveObs:
                            message = QtGui.QMessageBox.warning( self,
                                         u'Внимание!',
                                         u'''Внимание, в блоке диагнозов указан МКБ "{}" Пациент состоит на диспансерном наблюдении по {} . Указанный МКБ корректный?'''.format(MKB, diag),
                                         QtGui.QMessageBox.Yes|QtGui.QMessageBox.No,
                                         QtGui.QMessageBox.No)
                            if message == QtGui.QMessageBox.No:
                                self.setFocusToWidget(self.tblFinalDiagnostics, row, item.indexOf('MKB'))
                                return False
                        elif needCheck:
                            return self.checkValueMessage(u'''Внимание, в блоке диагнозов указан МКБ "{}" по которому пациент не состоит на диспансерном наблюдении. Для регистрации случая проведения Диспансерного приема пациент должен состоять на ДН по диагнозу данной группы'''.format(MKB), 
                                                            True, 
                                                            self.tblFinalDiagnostics, 
                                                            row, 
                                                            item.indexOf('MKB'))
                    else:
                        return self.checkValueMessage(u'''Внимание, в блоке диагнозов указан МКБ "{}" по которому пациент не состоит на диспансерном наблюдении. Для регистрации случая проведения Диспансерного приема пациент должен состоять на ДН по диагнозу данной группы'''.format(MKB), 
                                                        True, 
                                                        self.tblFinalDiagnostics, 
                                                        row, 
                                                        item.indexOf('MKB'))
                    
        return result 
    
    
    def checkSurveillanceData(self):
        result = True
        for row, item in enumerate(self.modelFinalDiagnostics.items()):
            if forceRef(item.value('dispanser_id')) in self.modelFinalDiagnostics.observedDispanserIdList:
                MKB = forceString(item.value('MKB'))
                if MKB:
                    diag = MKB
                    if len(MKB) >= 3:
                        diag = MKB[:3]
                for row, item in enumerate(self.modelSurveillance.items()):
                    sMKB = forceString(item.value('MKB'))
                    if sMKB:
                        sDiag = sMKB
                        if len(sMKB) >= 3:
                            sDiag = sMKB[:3]
                    if sDiag == diag:
                        result = forceDate(item.value(item.indexOf('endDate'))) or self.checkInputMessage(u'дату следующей явки', False, self.tblSurveillance, row, item.indexOf('endDate'))
                        if not result: 
                            return result
                        result = forceRef(item.value(item.indexOf('person_id'))) or self.checkInputMessage(u'врача по ДН', False, self.tblSurveillance, row, item.indexOf('person_id'))
                        if not result: 
                            return result
                        result = forceDate(item.value(item.indexOf('takenDate'))) or self.checkInputMessage(u'дату взятия на ДН', False, self.tblSurveillance, row, item.indexOf('takenDate'))
                        if not result: 
                            return result
                        self.syncPP()
        return result 

    
    def syncPP(self):
        db = QtGui.qApp.db
        tableRBDispanser = db.table('rbDispanser')
        table = db.table('ProphylaxisPlanning')
        for row, item in enumerate(self.modelSurveillance.items()):
            # Синхронизация данных с ЛУД
            MKB = forceStringEx(item.value('MKB'))
            diag = MKB
            if len(MKB) >= 3:
                diag = MKB[:3]
            filter = [table['parent_id'].isNull(),
                      table['client_id'].eq(self.clientId),
                      table['deleted'].eq(0),
                      table['MKB'].like(diag + '%')]
            order = [table['takenDate'].name() + u'ASC', table['removeDate'].name() + u'DESC']
            ppItems = db.getRecordList(table, '*', filter, order)
            filteredItems = []
            for ppItem in ppItems:
                dispanserId = forceRef(ppItem.value('dispanser_id'))
                observed = 0
                if dispanserId:
                    recObserved = db.getRecordEx(tableRBDispanser, [tableRBDispanser['observed']],
                                                    [tableRBDispanser['id'].eq(dispanserId)])
                    observed = forceInt(recObserved.value('observed')) if recObserved else 0
                if observed:
                    filteredItems.append(ppItem)
            
            if filteredItems:
                filteredItem = filteredItems[0]
                personId = forceRef(filteredItem.value('person_id'))
                takenDate = forceDate(filteredItem.value('takenDate'))
                specialityId = forceRef(QtGui.qApp.db.translate('Person', 'id', personId, 'speciality_id'))
                diagnosticRecord = self.modelSurveillance.diagnosticRecords.get(MKB, None)
                if not diagnosticRecord:
                    MKBGroup = MKB[:3] if len(MKB) > 3 else MKB
                    diagnosticRecord = self.modelSurveillance.diagnosticGroupRecords.get(MKBGroup, None)
                diagnosisId = forceRef(diagnosticRecord.value('diagnosis_id')) if diagnosticRecord else None
                diagEndDate = None
                if diagnosisId:
                    diagnosisRecord = QtGui.qApp.db.getRecordEx('Diagnosis', 'dispanserPerson_id, dispanserBegDate, endDate, dispanser_id', 'id=%s' % diagnosisId)
                    dispanserPersonId = forceRef(diagnosisRecord.value('dispanserPerson_id'))
                    dispanserBegDate = forceDate(diagnosisRecord.value('dispanserBegDate'))
                    diagnosticRemovedRecord = QtGui.qApp.db.getRecordEx('Diagnostic', 'endDate', 'diagnosis_id={} AND dispanser_id in (3, 4, 5) AND deleted=0'.format(diagnosisId), order='endDate DESC')
                    diagEndDate = None
                    if diagnosticRemovedRecord:
                        diagEndDate = forceDate(diagnosticRemovedRecord.value('endDate'))
                    if not diagEndDate:
                        diagEndDate = forceDate(diagnosisRecord.value('endDate')) if forceDate(diagnosisRecord.value('endDate')) else QDate().currentDate()
                    dispanser = QtGui.qApp.db.getRecordEx('rbDispanser', 'name', 'code="{}"'.format(forceString(diagnosisRecord.value('dispanser_id'))))
                    if not dispanserPersonId or not dispanserBegDate:
                        valuesList = []
                        if not dispanserPersonId:
                            valuesList.append(u'врача по ДН')
                        if not dispanserBegDate:
                            valuesList.append(u'дату взятия')
                        self.tblSurveillance.setCurrentRow(row)
                        QtGui.QMessageBox.warning(self,
                                                    u'Внимание!',
                                                    u'Синхронизация данных по ДН с ЛУД\nдиагноз: %s\nдата взятия на ДН: %s\nврач: %s\nНеобходимо указать %s' % (
                                                    MKB,
                                                    formatDate(dispanserBegDate) if dispanserBegDate else u'отсутствует',
                                                    getPersonInfo(dispanserPersonId)['fullName'] if dispanserPersonId else u'отсутствует',
                                                    u' и '.join(valuesList)),
                                                    QtGui.QMessageBox.Ok,
                                                    QtGui.QMessageBox.Ok)
                        return False

                    personInfo = getPersonInfo(dispanserPersonId)
                    orgStructureId = forceRef(filteredItem.value('orgStructure_id'))
                    diagnosisDispanserId = forceInt(diagnosisRecord.value('dispanser_id'))
                    if forceInt(filteredItem.value('dispanser_id')) in (1,2,6) and (personId != dispanserPersonId or takenDate != dispanserBegDate or specialityId != personInfo['specialityId'] or orgStructureId != personInfo['orgStructureId'] or \
                        (diagnosisDispanserId != forceInt(filteredItem.value('dispanser_id')))):

                        self.tblSurveillance.setCurrentRow(row)
                        diagnosisDispanserCheck = diagnosisDispanserId and diagnosisDispanserId not in (1,2,6)
                        QtGui.QMessageBox.warning(self,
                                                    u'Внимание!',
                                                    u'''Синхронизация данных по ДН с ЛУД\nдиагноз: {}\nдата взятия на ДН: {}\nврач: {}\nспециальность: {}\nподразделение: {}\nдолжность: {}\nДН: {}\nДата снятия: {}\n'''.format(MKB, 
                                                                        formatDate(dispanserBegDate), 
                                                                        personInfo['fullName'], 
                                                                        personInfo['specialityName'], 
                                                                        personInfo['orgStructureName'], 
                                                                        personInfo['postName'],
                                                                        forceString(dispanser.value('name')) if dispanser else u'',
                                                                        forceString(diagEndDate) if diagnosisRecord and diagnosisDispanserCheck else u''),
                                                    QtGui.QMessageBox.Ok,
                                                    QtGui.QMessageBox.Ok)
                        if dispanserPersonId:
                            filteredItem.setValue('person_id', dispanserPersonId)
                        if personInfo['specialityId']:
                            filteredItem.setValue('speciality_id', personInfo['specialityId'])
                        if personInfo['orgStructureId']:
                            filteredItem.setValue('orgStructure_id', personInfo['orgStructureId'])
                        filteredItem.setValue('takenDate', dispanserBegDate)
                        filteredItem.setValue('removeDate', diagEndDate if diagnosisDispanserCheck else None)
                        filteredItem.setValue('dispanser_id', diagnosisRecord.value('dispanser_id'))
                        filteredItem.setValue('removeReason_id', 1 if diagnosisDispanserCheck else None)
                        id = db.insertOrUpdate(table, filteredItem)


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
        result._diagnosises = CDiagnosticInfoProxyList(context, [self.modelFinalDiagnostics])
        result._surveillance = CProphylaxisPlanningInfoProxyList(context, [self.modelSurveillance])
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
    def on_modelFinalDiagnostics_diagnosisChanged(self, MKB=''):
        self.updateVisitsByDiagnostics(self.sender())
        self.updateMesMKB()
        #self.updateActionsDiagnosisByDiagnostics()
        diagnosticRecords = self.modelFinalDiagnostics.surveillanceRecords(self.clientId)
        if diagnosticRecords:
            self.modelSurveillance.setEventEditor(self)
            self.modelSurveillance.setDiagnosticRecords(diagnosticRecords)
            self.modelSurveillance.setClientId(self.clientId)
            self.modelSurveillance.loadItem(forceString(MKB))
        
        
    @pyqtSignature('QModelIndex, int, int')
    def on_modelFinalDiagnostics_rowsRemoved(self, parent, start, end):
        diagnosticRecords = self.modelFinalDiagnostics.surveillanceRecords(self.clientId)
        self.modelSurveillance.setEventEditor(self)
        self.modelSurveillance.setDiagnosticRecords(diagnosticRecords)
        self.modelSurveillance.setClientId(self.clientId)
        if diagnosticRecords:
            self.modelSurveillance.loadItem(forceString(diagnosticRecords[0].value('MKB')))
        else:
            self.modelSurveillance.loadItems(None)
        self.modelSurveillance.reset()


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
    def on_actAddChronicDiseases_triggered(self):
        """
        Добавляем хронические диагнозы к списку диагнозов
        :return:
        """
        dialog = CChronicDiseasesLoadDialog(self.clientId, self.modelFinalDiagnostics, self)
        if dialog.exec_():
            for rowNum, item in enumerate(dialog.modelChronicDiagnoses.items()):
                index = dialog.modelChronicDiagnoses.index(rowNum, 0)
                if index in dialog.selectionModelChronicDiagnoses.selectedRows():
                    record = self.modelFinalDiagnostics.getEmptyRecord()
                    record.setValue('MKB', item.value('MKB'))
                    record.setValue('MKBEx', item.value('MKBEx'))
                    record.setValue('TNMS', item.value('TNMS'))
                    record.setValue('exSubclassMKB', item.value('exSubclassMKB'))
                    record.setValue('morphologyMKB', item.value('morphologyMKB'))
                    record.setValue('character_id', item.value('character_id'))
                    record.setValue('dispanser_id', item.value('dispanser_id'))
                    record.setValue('traumaType_id', item.value('traumaType_id'))
                    self.modelFinalDiagnostics.addRecord(record)
        
    @pyqtSignature('')
    def on_btnPlanning_clicked(self):
        actionListToNewEvent = []
        self.prepare(self.clientId, self.eventTypeId, self.orgId, self.personId, self.eventDate, self.eventDate, None, None, None, None, None, isEdit=True)
        self.initPrevEventTypeId(self.eventTypeId, self.clientId)
        self.initPrevEventId(None)
        self.addActions(actionListToNewEvent)


    def on_actChangePersonDN_triggered(self):
        model = self.tblSurveillance.model()
        item = self.tblSurveillance.currentItem()
        if item:
            MKB = forceString(item.value('MKB'))
            record = model.diagnosticRecords.get(MKB, None)
            if not record:
                MKBGroup = MKB[:3] if len(MKB) > 3 else MKB
                record = model.diagnosticGroupRecords.get(MKBGroup, None)
            diagnosisId = forceRef(record.value('diagnosis_id')) if record else None
            dialog = CChangeDispanserPerson(self)
            if forceInt(item.value('dispanser_id')) == forceInt(record.value('diagnosisDispanser_id')):
                dialog.load(diagnosisId)
            if dialog.exec_():
                personId = dialog.getPersonId()
                dispanserPersonId = forceRef(personId)
                personRecord = QtGui.qApp.db.getRecordEx('Person', 'speciality_id, orgStructure_id', 'id=%s' % dispanserPersonId)
                specialityId = forceRef(personRecord.value('speciality_id'))
                orgStructureId = forceRef(personRecord.value('orgStructure_id'))
                item.setValue('person_id', dispanserPersonId)
                item.setValue('speciality_id', specialityId)
                item.setValue('orgStructure_id', orgStructureId)
                model.reset()


    @pyqtSignature('')
    def on_actChangeDispanserDate_triggered(self):
        model = self.tblSurveillance.model()
        item = self.tblSurveillance.currentItem()
        if item:
            MKB = forceString(item.value('MKB'))
            record = model.diagnosticRecords.get(MKB, None)
            if not record:
                MKBGroup = MKB[:3] if len(MKB) > 3 else MKB
                record = model.diagnosticGroupRecords.get(MKBGroup, None)
            diagnosisId = forceRef(record.value('diagnosis_id')) if record else None
            dialog = CChangeDispanserBegDateLUD(self)
            if forceInt(item.value('dispanser_id')) == forceInt(record.value('diagnosisDispanser_id')):
                dialog.load(diagnosisId)
            if dialog.exec_():
                date = dialog.getDate()
                item.setValue('takenDate', date)
                model.reset()


    def on_popupMenu_aboutToShow(self):
        model = self.tblSurveillance.model()
        rowCount = model.realRowCount() if hasattr(model, 'realRowCount') else model.rowCount()
        row = self.tblSurveillance.currentIndex().row()
        self.actChangeDispanserDate.setEnabled(0 <= row < rowCount)
        self.actChangePersonDN.setEnabled(0 <= row < rowCount)
        self.tblSurveillance.on_popupMenu_aboutToShow()