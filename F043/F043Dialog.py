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
## Форма 043: стоматология и другие зубные дела
##
#############################################################################


from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import Qt, QDate, QDateTime, QModelIndex, QObject, QTime, QVariant, SIGNAL, pyqtSignature

from Events.ExportMIS import iniExportEvent
from Events.RelatedEventAndActionListDialog import CRelatedEventAndActionListDialog
from F088.F0882022EditDialog import CEventExportTableModel, CAdvancedExportTableModel
from Orgs.Utils import getOrgstructureListByEventtypeId, getPersonListByEventtypeId
from library.Attach.AttachAction        import getAttachAction
from library.crbcombobox                import CRBComboBox
from library.ICDInDocTableCol           import CICDExInDocTableCol
from library.ICDMorphologyInDocTableCol import CMKBMorphologyCol
from library.InDocTable                 import CMKBListInDocTableModel, CBoolInDocTableCol, CDateTimeForEventInDocTableCol, CInDocTableCol, CRBInDocTableCol
from library.interchange                import getDateEditValue, getDatetimeEditValue, getRBComboBoxValue, setDateEditValue, setDatetimeEditValue, setRBComboBoxValue
from library.PrintInfo                  import CInfoContext
from library.PrintTemplates             import customizePrintButton, getPrintButton, applyTemplate
from library.TNMS.TNMSComboBox          import CTNMSCol
from library.MKBExSubclassComboBox import CMKBExSubclassCol
from library.Utils                      import copyFields, forceBool, forceDate, forceDateTime, forceDouble, forceInt, forceRef, forceString, formatNum, toVariant, variantEq, getDentitionActionTypeId, forceStringEx

from Events.Action                      import initActionProperties
from Events.ActionInfo                  import CActionInfoProxyList
from Events.ActionsSummaryModel         import CFxxxActionsSummaryModel
from Events.DiagnosisType               import CDiagnosisTypeCol
from Events.EventEditDialog             import CEventEditDialog, CDiseaseCharacter, CDiseaseStage, CDiseasePhases, CToxicSubstances, getToxicSubstancesIdListByMKB
from Events.EventInfo                   import CDiagnosticInfoProxyList, CVisitInfoProxyList
from Events.EventVisitsModel            import CDentitionVisitsModel
from Events.TeethEventInfo              import CTeethEventInfo
from Events.Utils import checkDiagnosis, checkIsHandleDiagnosisIsChecked, getAvailableCharacterIdByMKB, getDiagnosisId2, \
    getDiagnosticResultId, getEventAddVisit, getEventAvailableOrders, getEventDurationRange, getEventIsPrimary, getEventMesRequired, \
    getEventResultId, getEventSetPerson, getEventShowTime, getEventShowVisitTime, getHealthGroupFilter, \
    hasEventVisitAssistant, setAskedClassValueForDiagnosisManualSwitch, CTableSummaryActionsMenuMixin, \
    getEventCSGRequired, CFinanceType, getNewResultCond, isDefaultResultIdValid, mkbIsVIMIS
from F043.DentitionTable                import CClientDentitionHistoryModel, CDentitionModel, CParodentiumModel
from F043.PreF043Dialog                 import CPreF043Dialog, CPreF043DagnosticAndActionPresets
from Orgs.PersonComboBoxEx              import CPersonFindInDocTableCol
from RefBooks.Tables                    import rbDispanser, rbHealthGroup, rbTraumaType
from Users.Rights import urAccessF043planner, urAdmin, urEditEndDateEvent, urRegTabWriteRegistry, urRegTabReadRegistry, urCanReadClientVaccination, urCanEditClientVaccination, \
    urCanSaveF043WithoutStom

from F043.Ui_F043                       import Ui_F043Dialog


INSPECTION_DENTITION_TAB_INDEX = 0
INSPECTION_DENTITION_ADDITIONAL_TAB_INDEX = 1
RESULT_DENTITION_TAB_INDEX = 2


class CF043Dialog(CEventEditDialog, Ui_F043Dialog, CTableSummaryActionsMenuMixin):
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
        CEventEditDialog.__init__(self, parent)
        self.dentitionActionTypeId = forceRef(
                                    QtGui.qApp.db.translate('ActionType', 'flatCode', 'dentitionInspection', 'id'))
        self.parodentActionTypeId = forceRef(
                                    QtGui.qApp.db.translate('ActionType', 'flatCode', 'parodentInsp', 'id'))
        self.mapSpecialityIdToDiagFilter = {}
        self.addModels('Visits', CDentitionVisitsModel(self))
        self.addModels('Diagnostics', CF043FinalDiagnosticsModel(self))
        self.addModels('ActionsSummary', CFxxxActionsSummaryModel(self, True))
        self.addModels('ClientDentitionHistory', CClientDentitionHistoryModel(self))
        self.addModels('Dentition', CDentitionModel(self, self.modelClientDentitionHistory))
        self.addModels('Parodentium', CParodentiumModel(self, self.modelClientDentitionHistory))
        self.addModels('Export', CEventExportTableModel(self))
        self.addModels('Export_FileAttach', CAdvancedExportTableModel(self))
        self.addModels('Export_VIMIS', CAdvancedExportTableModel(self))
        self.modelDentition.setIsExistsDentitionAction(bool(self.dentitionActionTypeId))
        self.modelParodentium.setIsExistsDentitionAction(bool(self.parodentActionTypeId))

        self.addObject('actEditClient', QtGui.QAction(u'Открыть регистрационную карточку', self))
        self.addObject('actPortal_Doctor', QtGui.QAction(u'Перейти на портал врача', self))
        self.addObject('actShowAttachedToClientFiles', getAttachAction('Client_FileAttach',  self))
        self.addObject('actShowContingentsClient', QtGui.QAction(u'Показать все наблюдаемые контингенты', self))
        self.addObject('actOpenClientVaccinationCard', QtGui.QAction(u'Открыть прививочную карту', self))
        self.setupDiagnosticsMenu()
        self.addObject('btnPrint', getPrintButton(self, ''))
        # self.addObject('btnMedicalCommission', QtGui.QPushButton(u'ВК', self))
        self.addObject('btnPlanning', QtGui.QPushButton(u'Планировщик', self))
        self.addObject('btnRelatedEvent', QtGui.QPushButton(u'Связанные события', self))
        self.addObject('btnTemperatureList', QtGui.QPushButton(u'Температурный лист', self))
        self.addObject('btnPrintMedicalDiagnosis', getPrintButton(self, '', u'Врачебный диагноз'))
        self.createSaveAndCreateAccountButton()

        self.setupUi(self)

        self.setupSaveAndCreateAccountButton()

        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setWindowTitleEx(u'Стоматология Ф.043')

        self.setMedicalDiagnosisContext()
        self.tabToken.setFocusProxy(self.tblDiagnostics)
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
        # self.buttonBox.addButton(self.btnMedicalCommission, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnRelatedEvent, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnTemperatureList, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnPrintMedicalDiagnosis, QtGui.QDialogButtonBox.ActionRole)
        self.setupActionSummarySlots()

        self.tblVisits.setModel(self.modelVisits)
        self.tblVisits.setSelectionModel(self.selectionModelVisits)
        self.tblDiagnostics.setModel(self.modelDiagnostics)
        self.setModels(self.tblClientDentitionHistory,
                       self.modelClientDentitionHistory,
                       self.selectionModelClientDentitionHistory)
        self.setModels(self.tblDentition,
                       self.modelDentition,
                       self.selectionModelDentition)
        self.setModels(self.tblParodentium,
                       self.modelParodentium,
                       self.selectionModelParodentium)

        self.tblDentition.addInspectionActions()
        self.tblParodentium.addParodentActions()
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
        self.actOpenClientVaccinationCard.setEnabled(QtGui.qApp.userHasAnyRight([urCanReadClientVaccination, urCanEditClientVaccination]))
        self.actEditClient.setEnabled(QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]))
        self.tblVisits.setEventEditor(self)
        self.tblVisits.addPopupDelRow()
        self.setupVisitsIsExposedPopupMenu()
        self.tblDiagnostics.setPopupMenu(self.mnuDiagnostics)
        CTableSummaryActionsMenuMixin.__init__(self)

        self.setupDirtyCather()
        self.setIsDirty(False)
        self.blankMovingIdList = []
        self.isResultDentitionLoadedByInspection = False
        self.isNewDentitionActionInitialized = False
        self.clientId = None
        self.prolongateEvent = False
        self.prevEventId = None
        self.tabNotes.setEventEditor(self)
        self.edtDentitionObjectively.getThesaurus(1)
        self.edtDentitionMucosa.getThesaurus(2)
        self.tblActions.enableColsHide()
        self.tblActions.enableColsMove()

        self.tblExport.enableColsHide()
        self.tblExport.enableColsMove()

        self.tblExport_FileAttach.enableColsHide()
        self.tblExport_FileAttach.enableColsMove()

        self.tblExport_VIMIS.enableColsHide()
        self.tblExport_VIMIS.enableColsMove()

        self.postSetupUi()

        self._applyUETCountConnection()
        if hasattr(self, 'edtEndDate'):
            self.edtEndDate.setEnabled(QtGui.qApp.userHasRight(urEditEndDateEvent))
        if hasattr(self, 'edtEndTime'):
            self.edtEndTime.setEnabled(QtGui.qApp.userHasRight(urEditEndDateEvent))
        self.actionDentitionList = {}
        self.actionParodentiumList = {}
        self.btnPrintMedicalDiagnosis.setVisible(False)


    def _applyUETCountConnection(self):
        for actionsTab in self.getActionsTabsList():
            self.connect(actionsTab.modelAPActions, SIGNAL('itemsCountChanged()'), self.on_actionItemsCountChanged)
            self.connect(actionsTab, SIGNAL('actionUetChanged()'), self.on_actionUetChanged)


    def getActionsTabsList(self):
        result = []
        if hasattr(self, 'tabStatus'):
            result.append(self.tabStatus)
        if hasattr(self, 'tabDiagnostic'):
            result.append(self.tabDiagnostic)
        if hasattr(self, 'tabCure'):
            result.append(self.tabCure)
        if hasattr(self, 'tabMisc'):
            result.append(self.tabMisc)
        return result


    def on_actionUetChanged(self):
        self._recountCommonUet()


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


    def on_actionItemsCountChanged(self):
        self._recountCommonUet()


    def getServiceActionCode(self):
        return None


    def _recountCommonUet(self):
        result = 0.0
        actionItemsList = self.getActionsModelsItemsList()
        for (record, action) in actionItemsList:
            result += forceDouble(record.value('uet'))
        self.edtCommonUet.setValue(result)


    def destroy(self):
        CEventEditDialog.deleteLater(self)
        self.tblVisits.setModel(None)
        self.tblDiagnostics.setModel(None)
        self.tblClientDentitionHistory.setModel(None)
        self.tblDentition.setModel(None)
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
        del self.modelDentition
        del self.modelClientDentitionHistory
        self.tabAmbCard.deleteLater()


    def getModelFinalDiagnostics(self):
        return self.modelDiagnostics


#    def currentClientId(self): # for AmbCard mixin
#        return self.clientId


    def onActionChanged(self, actionsSummaryRow):
        self.addVisitByActionSummaryRow(actionsSummaryRow, checkActionPersonIdIsEventPerson=True)
        self.closeEventByAction(actionsSummaryRow)


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


    @pyqtSignature('')
    def on_btnTemperatureList_clicked(self):
        self.getTemperatureList(self.eventSetDateTime)


    def setupDiagnosticsMenu(self):
        self.addObject('mnuDiagnostics', QtGui.QMenu(self))
        self.addObject('actDiagnosticsRemove', QtGui.QAction(u'Удалить запись', self))
        self.mnuDiagnostics.addAction(self.actDiagnosticsRemove)


    def getFinalDiagnosisId(self):
        diagnostics = self.modelDiagnostics.items()
        return forceRef(diagnostics[0].value('diagnosis_id')) if diagnostics else None
        
    
    def getFinalDiagnosisMKB(self):
        diagnostics = self.modelDiagnostics.items()
        if diagnostics:
            MKB   = forceString(diagnostics[0].value('MKB'))
            MKBEx = forceString(diagnostics[0].value('MKBEx'))
            return MKB, MKBEx
        else:
            return '', ''


    def _prepare(self, contractId, clientId, eventTypeId, orgId, personId, eventSetDatetime, eventDatetime,
                 weekProfile, numDays, presetDiagnostics, presetActions, disabledActions, externalId,
                 assistantId, curatorId, movingActionTypeId = None, valueProperties = [], relegateOrgId = None,
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
    #        self.chkPrimary.setChecked(getPrimary(clientId, eventTypeId, personId))
            self.initOrder(forceString(getEventAvailableOrders(eventTypeId)), eventOrder+1)
            self.cmbContract.setCurrentIndex(0)
            self.cmbResult.setCurrentIndex(0)
            self.cmbPrimary.setCurrentIndex(getEventIsPrimary(eventTypeId))
            self.initFocus()

            visitTypeId = presetDiagnostics[0][3] if presetDiagnostics else None
            self.modelVisits.setDefaultVisitTypeId(visitTypeId)
            visits = []
            date = QDate()
            resultId = QtGui.qApp.session("F043_resultId")
            if resultId:
                self.cmbResult.setValue(resultId)
            if self.eventDate:
                date = self.eventDate
#                resultId = self.cmbResult.value()
#                if not resultId:
#                    if self.cmbResult.model().rowCount() > 1:
#                        self.cmbResult.setValue(self.cmbResult.model().getId(1))
            elif self.eventSetDateTime and self.eventSetDateTime.date():
                  date = self.eventSetDateTime.date()
            else:
                 date = QDate.currentDate()
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
            if not len(visits):
                QtGui.QMessageBox.warning( self,
                                                 u'Внимание!',
                                                 u'Для события по форме 043 требуется обязательное указание параметра "Добавлять визит при создании" на вкладке "Визиты" в справочнике "Типы событий"',
                                                 QtGui.QMessageBox.Ok,
                                                 QtGui.QMessageBox.Ok)
                return False
            self.modelVisits.setItems(visits)
            self.updateVisitsInfo()
        self.setOrgStructAndPersonsInCmbPersons(eventTypeId)
        self.modelDentition.setClientId(self.clientId)
        self.modelParodentium.setClientId(self.clientId)
        if not isEdit:
            date = forceDateTime(visits[0].value('date')) if len(visits) else forceDateTime(self.eventSetDateTime.date())
            personId = forceRef(visits[0].value('person_id')) if len(visits) else personId
            self.prepareDentition(actionTypeId=None, date=date, personId=personId)
            self.prepareParodentium(actionTypeId=None, date=date, personId=personId)
            if presetDiagnostics:
                resultId = None
                if self.cmbResult.model().rowCount() > 1:
                    resultId = getDiagnosticResultId(self.cmbResult.model().getId(1))
                for MKB, dispanserId, healthGroupId, visitTypeId in presetDiagnostics:
                    item = self.modelDiagnostics.getEmptyRecord()
                    item.setValue('MKB', toVariant(MKB))
                    item.setValue('dispanser_id',   toVariant(dispanserId))
                    item.setValue('healthGroup_id', toVariant(healthGroupId))
                    characterIdList = getAvailableCharacterIdByMKB(MKB)
                    if characterIdList:
                        item.setValue('character_id', toVariant(characterIdList[0]))
    #                    item.setValue('result_id', toVariant(resultId)) WTF?! почему rbResult.id = rbDiagnosticResult.id?   
                    self.modelDiagnostics.items().append(item)
                self.modelDiagnostics.reset()
        self.prepareActions(contractId, presetActions, disabledActions, movingActionTypeId, valueProperties, diagnos, financeId, protocolQuoteId, actionByNewEvent, plannedEndDate)
        self.grpTempInvalid.pickupTempInvalid()
        self.grpAegrotat.pickupTempInvalid()
        self.grpDisability.pickupTempInvalid()
        self.grpVitalRestriction.pickupTempInvalid()
        self.setIsDirty(False)
        self.modelDentition.setClientId(self.clientId)
        self.modelParodentium.setClientId(self.clientId)
        self.tabNotes.setEventEditor(self)
        self.setFilterResult(self.eventSetDateTime.date())
        return self.checkEventCreationRestriction() and self.checkDeposit()


    def prepareActions(self, contractId, presetActions, disabledActions, actionTypeIdValue, valueProperties, diagnos, financeId,
                       protocolQuoteId, actionByNewEvent, plannedEndDate):
        def addActionType(actionTypeId, amount, financeId, contractId, idListActionType, idListActionTypeIPH, actionFinance, idListActionTypeMoving, plannedEndDate):
            db = QtGui.qApp.db
            tableOrgStructure = db.table('OrgStructure')
            for iModel, model in enumerate([self.tabStatus.modelAPActions,
                          self.tabDiagnostic.modelAPActions,
                          self.tabCure.modelAPActions,
                          self.tabMisc.modelAPActions]):
                if actionTypeId in model.actionTypeIdList:
                    if actionTypeId in idListActionType and not actionByNewEvent:
                        model.addRow(actionTypeId, amount, financeId, contractId)
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
                        model.addRow(actionTypeId, amount, financeId, contractId)
                        i = self.modelActionsSummary.itemIndex.index((iModel, model.rowCount()-2))
                        self.onActionChanged(i)
                        record, action = model.items()[-1]
                        if diagnos:
                            record, action = model.items()[-1]
                            action[u'Диагноз'] = diagnos
                    #[self.eventActionFinance, self.receivedFinanceId, orgStructureTransfer, orgStructurePresence, oldBegDate, movingQuoting, personId]
                    elif actionByNewEvent and actionTypeId in idListActionTypeMoving:
                        model.addRow(actionTypeId, amount, financeId, contractId)
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
                        model.addRow(actionTypeId, amount, financeId, contractId)
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
                addActionType(actionTypeId, amount, financeId if cash else None, contractId if cash else None, idListActionType, idListActionTypeIPH, actionFinance, idListActionTypeMoving, plannedEndDate)


    def prepare(self, clientId, eventTypeId, orgId, personId, eventSetDatetime, eventDatetime, weekProfile,
                numDays, externalId, assistantId, curatorId, flagHospitalization = False,
                movingActionTypeId = None, valueProperties = [], tissueTypeId=None, selectPreviousActions=False,
                relegateOrgId = None, relegatePersonId=None, diagnos = None, financeId = None,
                protocolQuoteId = None, actionByNewEvent = [], order = 1,
                actionListToNewEvent = [], typeQueue = -1, docNum=None, relegateInfo=[], plannedEndDate = None,
                mapJournalInfoTransfer = [], voucherParams = {},  isEdit=False):
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
        if QtGui.qApp.userHasAnyRight([urAccessF043planner, urAdmin]):
            dlg = CPreF043Dialog(self, self.contractTariffCache)
            try:
                dlg.setBegDateEvent(eventSetDatetime.date() if isinstance(eventSetDatetime, QDateTime) else eventSetDatetime)
                dlg.prepare(clientId, eventTypeId, eventDate, self.personId, self.personSpecialityId, self.personTariffCategoryId, 
                            flagHospitalization, movingActionTypeId, tissueTypeId, presentActionTypes = presentActionTypes, maxOccursLimitActionTypes = maxOccursLimitActionTypes)
                if dlg.diagnosticsTableIsNotEmpty() or dlg.actionsTableIsNotEmpty():
                    if not dlg.exec_():
                        return False
                result = self._prepare(dlg.contractId, clientId, eventTypeId, orgId, personId, eventSetDatetime,
                                       eventDatetime, weekProfile, numDays, dlg.diagnostics(), dlg.actions(),
                                       dlg.disabledActionTypeIdList, externalId, assistantId, curatorId,
                                       movingActionTypeId, valueProperties, relegateOrgId, relegatePersonId,
                                       diagnos, financeId, protocolQuoteId, actionByNewEvent, order,
                                       typeQueue, relegateInfo, plannedEndDate, isEdit)
                return result
            finally:
                dlg.deleteLater()
        else:
            presets = CPreF043DagnosticAndActionPresets(clientId, eventTypeId, eventDate, self.personSpecialityId, 
                                                        flagHospitalization, movingActionTypeId, presentActionTypes = presentActionTypes, 
                                                        maxOccursLimitActionTypes = maxOccursLimitActionTypes)
            presets.setBegDateEvent(eventSetDatetime.date() if isinstance(eventSetDatetime, QDateTime) else eventSetDatetime)
            return self._prepare(None, clientId, eventTypeId, orgId, personId, eventSetDatetime, eventDatetime, weekProfile, numDays,
                                 presets.unconditionalDiagnosticList, presets.unconditionalActionList, presets.disabledActionTypeIdList,
                                 externalId, assistantId, curatorId, None, [], relegateOrgId, relegatePersonId,
                                 diagnos, financeId, protocolQuoteId, actionByNewEvent, order, typeQueue, relegateInfo, plannedEndDate, isEdit)


    def addActionTypeDentition(self, date, personId, eventId, dentType):
        db = QtGui.qApp.db
        #tableActionType = db.table('ActionType')
        tablePerson     = db.table('vrbPersonWithSpeciality')
        actionTypeId = None
        newAction = None
        newRecord = None
        dentActionTypeId, parodentActionTypeId = getDentitionActionTypeId()
        if not dentType:
            actionTypeId = parodentActionTypeId
        else:
            actionTypeId = dentActionTypeId
        for model in (self.tabStatus.modelAPActions,
                      self.tabDiagnostic.modelAPActions,
                      self.tabCure.modelAPActions,
                      self.tabMisc.modelAPActions):
            if actionTypeId in model.actionTypeIdList:
                model.addRow(actionTypeId)
                newRecord, newAction = model.items()[-1]
                initActionProperties(newAction)
                newRecord.setValue('directionDate', QVariant(date))
                newRecord.setValue('begDate', QVariant(date))
                newRecord.setValue('endDate', QVariant(date))
                newRecord.setValue('person_id', QVariant(personId))
                newRecord.setValue('event_id', QVariant(eventId))
                recordAction = newAction.getRecord()
                recordAction.setValue('directionDate', QVariant(date))
                recordAction.setValue('begDate', QVariant(date))
                recordAction.setValue('endDate', QVariant(date))
                recordAction.setValue('person_id', QVariant(personId))
                recordAction.setValue('event_id', QVariant(eventId))
                break
        actionEventId = forceRef(recordAction.value('event_id')) if recordAction else None
        isCurrentDentitionAction = (eventId != actionEventId)
        actionId = forceRef(newRecord.value('id')) if newRecord else None
        personName = forceString(db.translate(tablePerson, 'id', personId, 'name'))
        isChecked = 0
        isLoaded = False
        if not dentType:
            if len(self.modelClientDentitionHistory._resultDentitionHistoryItems) > 0:
                self.modelClientDentitionHistory._resultDentitionHistoryItems.sort(key=lambda x: forceDateTime(x[0].value('begDate')) if forceRef(x[0].value('event_id')) == eventId and forceDateTime(x[0].value('begDate')) <= date else None)
                self.modelClientDentitionHistory._resultDentitionHistoryItems.reverse()
            self.modelClientDentitionHistory.addNewParodentiumForVisitItem(newRecord, newAction, actionId, eventId, isChecked, personName)
            penultimateItemAction = self.modelParodentium.getPenultimateItemAction()
            if penultimateItemAction:
                self.modelParodentium.copyParodent(action=penultimateItemAction)
                isLoaded = True
            isInit = True
            if not isLoaded or (isInit and not self.modelParodentium.teethIsSet()):
                self.modelParodentium.setDefaults(self.clientAge[3]>8)
            self.actionParodentiumList[(date.toPyDateTime(), personId, eventId)] = (newRecord, newAction)
            self.modelParodentium.loadAction(newRecord, newAction, isCurrentDentitionAction)
            if len(self.modelClientDentitionHistory._resultDentitionHistoryItems) > 0:
                self.modelClientDentitionHistory._resultDentitionHistoryItems.sort(key=lambda x: forceDateTime(x[0].value('begDate')))
                self.modelClientDentitionHistory._resultDentitionHistoryItems.reverse()
            if len(self.modelClientDentitionHistory._dentitionHistoryItems) > 0:
                self.modelClientDentitionHistory._dentitionHistoryItems.sort(key=lambda x: forceDateTime(x[0].value('begDate')))
                self.modelClientDentitionHistory._dentitionHistoryItems.reverse()
            self.modelClientDentitionHistory.setCurrentDentitionItems(newRecord, newAction, eventId)
        else:
            if len(self.modelClientDentitionHistory._dentitionHistoryItems) > 0:
                self.modelClientDentitionHistory._dentitionHistoryItems.sort(key=lambda x: forceDateTime(x[0].value('begDate')) if forceRef(x[0].value('event_id')) == eventId and forceDateTime(x[0].value('begDate')) <= date else None)
                self.modelClientDentitionHistory._dentitionHistoryItems.reverse()
            self.modelClientDentitionHistory.addNewDentitionForVisitItem(newRecord, newAction, actionId, eventId, isChecked, personName)
            penultimateItemAction = self.modelDentition.getPenultimateItemAction()
            if penultimateItemAction:
                self.modelDentition.copyInspection(skippingNames=[u'Статус', u'Санация'],
                                                   action=penultimateItemAction)
                isLoaded = True
            self.tblClientDentitionHistory.setCurrentIndex(self.modelClientDentitionHistory.index(0, 0))
            self.isNewDentitionActionInitialized = True
            if not isLoaded or (self.isNewDentitionActionInitialized and not self.modelDentition.teethIsSet()):
                self.modelDentition.setDefaults(self.clientAge[3]>8)
            self.actionDentitionList[(date.toPyDateTime(), personId, eventId)] = (newRecord, newAction)
            self.modelClientDentitionHistory.setCurrentDentitionItems(newRecord, newAction, eventId)
        self.modelClientDentitionHistory.reset()
        return newRecord, newAction


    def setEventTypeId(self, eventTypeId):
        CEventEditDialog.setEventTypeId(self, eventTypeId, u'Ф.043')
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
        if forceBool(QtGui.qApp.preferences.appPrefs.get('fillDiagnosticsEventsResults', True)):
            self.cmbResult.setValue(CF043Dialog.defaultEventResultId)
        cols = self.modelDiagnostics.cols()
        resultCol = cols[len(cols)-1]
        resultCol.filter = 'eventPurpose_id=\'%d\'' % self.eventPurposeId
        self.cmbContract.setEventTypeId(eventTypeId)
        self.setVisitAssistantVisible(self.tblVisits, hasEventVisitAssistant(eventTypeId))
        customizePrintButton(self.btnPrint, self.eventContext if self.eventContext else 'F043')


    def setOrgId(self, orgId):
        self.orgId = orgId
        self.cmbContract.setOrgId(orgId)
        self.cmbPerson.setOrgId(orgId)


    def setRecord(self, record):
        CEventEditDialog.setRecord(self, record)
        setDatetimeEditValue(self.edtBegDate, self.edtBegTime, record, 'setDate')
        setRBComboBoxValue(self.cmbPerson,      record, 'setPerson_id')
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
        self.loadDiagnostics()
        self.tabMedicalDiagnosis.load(self.itemId())
        self.updateMesMKB()
        self.tabMes.setRecord(record)
        self.loadActions()
        self.modelDentition.setClientId(self.clientId)
        self.modelParodentium.setClientId(self.clientId)
        self.setIsDirty(False)

        self.grpTempInvalid.pickupTempInvalid()
        self.grpAegrotat.pickupTempInvalid()
        self.grpDisability.pickupTempInvalid()
        self.grpVitalRestriction.pickupTempInvalid()
        self.loadDentition()
        self.loadParodentium()
        self._recountCommonUet()
        self.tabCash.load(self.itemId())
        self.on_cmbResult_currentIndexChanged()
        self.initFocus()
        self.setIsDirty(False)
        self.blankMovingIdList = []
        self.protectClosedEvent()
        iniExportEvent(self)
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
        self.modelActionsSummary._cols[
            self.modelActionsSummary.getColIndex('person_id')].personIdList = personListByEventtype

    def getDiagnosisTypeId(self, dt):
        return forceRef(QtGui.qApp.db.translate('rbDiagnosisType', 'code', '2' if dt else '9', 'id'))


    def loadVisits(self):
        self.modelVisits.loadItems(self.itemId())
        self.updateVisitsInfo()


    def loadDiagnostics(self):
        db = QtGui.qApp.db
        table = db.table('Diagnostic')
#        tablePerson = db.table('Person')
        isDiagnosisManualSwitch = self.modelDiagnostics.manualSwitchDiagnosis()
        rawItems = db.getRecordList(table, '*', [table['deleted'].eq(0), table['event_id'].eq(self.itemId())], 'id')
        items = []
        for record in rawItems:
#            specialityId = forceRef(record.value('speciality_id'))
            diagnosisId     = record.value('diagnosis_id')
            MKB             = db.translate('Diagnosis', 'id', forceRef(diagnosisId), 'MKB')
            MKBEx           = db.translate('Diagnosis', 'id', forceRef(diagnosisId), 'MKBEx')
            exSubclassMKB   = db.translate('Diagnosis', 'id', forceRef(diagnosisId), 'exSubclassMKB')
            morphologyMKB   = db.translate('Diagnosis', 'id', forceRef(diagnosisId), 'morphologyMKB')
            setDate         = forceDate(record.value('setDate'))
            newRecord = self.modelDiagnostics.getEmptyRecord()
            copyFields(newRecord, record)
            newRecord.setValue('MKB',           MKB)
            newRecord.setValue('MKBEx',         MKBEx)
            newRecord.setValue('exSubclassMKB', exSubclassMKB)
            newRecord.setValue('morphologyMKB', morphologyMKB)
            self.modelDiagnostics.updateMKBTNMS(newRecord, MKB)
            self.modelDiagnostics.updateMKBToExSubclass(newRecord, MKB)
            if isDiagnosisManualSwitch:
                isCheckedHandleDiagnosis = checkIsHandleDiagnosisIsChecked(setDate,
                                                                           self.clientId,
                                                                           diagnosisId)
                newRecord.setValue('handleDiagnosis', QVariant(isCheckedHandleDiagnosis))

            newRecord._dirty = False
            items.append(newRecord)
        self.modelDiagnostics.setItems(items)
        self.modelDiagnostics.cols()[self.modelDiagnostics.getColIndex('healthGroup_id')].setFilter(getHealthGroupFilter(forceString(self.clientBirthDate.toString('yyyy-MM-dd')), forceString(self.eventSetDateTime.date().toString('yyyy-MM-dd'))))


    def loadDentition(self):
        model = self.modelClientDentitionHistory
        setDate = self.eventSetDateTime.date()
        currentEventId = self.itemId()
        model.loadClientDentitionHistory(self.clientId, setDate)
        self.modelDentition.setAdultDefaults(self.clientAge[3]>8)
        for tab in (self.tabStatus,
                    self.tabDiagnostic,
                    self.tabCure,
                    self.tabMisc):
            modelAPActions = tab.tblAPActions.model()
            for record, action in modelAPActions.items():
                actionType = action.getType()
                if actionType.flatCode == u'dentitionInspection':
                    eventId = forceRef(record.value('event_id'))
                    if currentEventId and currentEventId == eventId:
                        date = forceDateTime(record.value('begDate'))
                        personId = forceRef(record.value('person_id'))
                        self.actionDentitionList[(date.toPyDateTime(), personId, eventId)] = (record, action)
                        model.setCurrentDentitionItems(record, action, currentEventId)
        if len(self.modelClientDentitionHistory._dentitionHistoryItems) > 0:
            self.modelClientDentitionHistory._dentitionHistoryItems.sort(key=lambda x: forceDateTime(x[0].value('begDate')) if x[0] else None)
            self.modelClientDentitionHistory._dentitionHistoryItems.reverse()
        record, action, id, eventId, isChecked, personName = self.modelClientDentitionHistory.getItemByRow(0)
        self.modelClientDentitionHistory.setCurrentDentitionItem(record, action)
        currentEventId = self.itemId()
        actionEventId = forceRef(record.value('event_id')) if record else None
        self.modelDentition.setIsCurrentDentitionAction(currentEventId == actionEventId)


    def loadParodentium(self):
        self.modelParodentium.setAdultDefaults(self.clientAge[3]>8)
        for tab in (self.tabStatus,
                    self.tabDiagnostic,
                    self.tabCure,
                    self.tabMisc):
            modelAPActions = tab.tblAPActions.model()
            for record, action in modelAPActions.items():
                actionType = action.getType()
                if actionType.flatCode == u'parodentInsp':
                    actionEventId = forceRef(record.value('event_id'))
                    date = forceDateTime(record.value('begDate'))
                    personId = forceRef(record.value('person_id'))
                    eventId = forceRef(record.value('event_id'))
                    self.actionParodentiumList[(date.toPyDateTime(), personId, eventId)] = (record, action)
        if len(self.modelClientDentitionHistory._resultDentitionHistoryItems) > 0:
            self.modelClientDentitionHistory._resultDentitionHistoryItems.sort(key=lambda x: forceDateTime(x[0].value('begDate')) if x[0] else None)
            self.modelClientDentitionHistory._resultDentitionHistoryItems.reverse()
        record, action, id, eventId, isChecked, personName = self.modelClientDentitionHistory.getParadentiumItem(0)
        self.modelClientDentitionHistory.setCurrentParadentiumItem(record, action)
        currentEventId = self.itemId()
        actionEventId = forceRef(record.value('event_id')) if record else None
        self.modelParodentium.setIsCurrentParadentiumAction(currentEventId == actionEventId)
        self.tblVisits.setCurrentIndex(self.modelVisits.index(len(self.modelVisits.items())-1, 0))
        self.tblClientDentitionHistory.setCurrentIndex(self.modelClientDentitionHistory.index(0, 0))


    def loadDentitionAdditional(self, record, action, isCurrentDentitionAction):
        #дополнительные свойства для Dentition
        for widget in (self.edtDentitionObjectively,
                       self.cmbDentitionBite,
                       self.cmbDentitionApparat,
                       self.cmbDentitionProtezes,
                       self.cmbDentitionOrtodontCure,
                       self.edtDentitionMucosa,
                       self.edtDentitionNote,
                       self.cmbDentitionSanitation):
            widget.setEnabled(isCurrentDentitionAction)
        if action:
            if u'Объективность' in action._actionType._propertiesByName:
                dentitionObjectivelyText = action.getProperty(u'Объективность').getText()
                dentitionObjectivelyText = dentitionObjectivelyText if dentitionObjectivelyText else u''
                self.edtDentitionObjectively.setValue(dentitionObjectivelyText)

            if u'Прикус' in action._actionType._propertiesByName:
                self.cmbDentitionBite.blockSignals(True)
                dentitionBiteProperty = action.getProperty(u'Прикус')
                self.cmbDentitionBite.setDomain(dentitionBiteProperty.type().valueDomain)
                dentitionBiteText = dentitionBiteProperty.getText() or ''
                self.cmbDentitionBite.setEditText(dentitionBiteText)
                self.cmbDentitionBite.blockSignals(False)

            if u'Аппарат' in action._actionType._propertiesByName:
                self.cmbDentitionApparat.blockSignals(True)
                dentitionApparatProperty = action.getProperty(u'Аппарат')
                self.cmbDentitionApparat.setDomain(dentitionApparatProperty.type().valueDomain)
                dentitionApparatText = dentitionApparatProperty.getText() or ''
                self.cmbDentitionApparat.setEditText(dentitionApparatText)
                self.cmbDentitionApparat.blockSignals(False)

            if u'Протезы' in action._actionType._propertiesByName:
                self.cmbDentitionProtezes.blockSignals(True)
                dentitionProtezesProperty = action.getProperty(u'Протезы')
                self.cmbDentitionProtezes.setDomain(dentitionProtezesProperty.type().valueDomain)
                dentitionProtezesText = dentitionProtezesProperty.getText() or ''
                self.cmbDentitionProtezes.setEditText(dentitionProtezesText)
                self.cmbDentitionProtezes.blockSignals(False)

            if u'Ортодонтическое лечение' in action._actionType._propertiesByName:
                self.cmbDentitionOrtodontCure.blockSignals(True)
                dentitionOrtodontCureProperty = action.getProperty(u'Ортодонтическое лечение')
                self.cmbDentitionOrtodontCure.setDomain(dentitionOrtodontCureProperty.type().valueDomain)
                dentitionOrtodontCureText = dentitionOrtodontCureProperty.getText() or ''
                self.cmbDentitionOrtodontCure.setEditText(dentitionOrtodontCureText)
                self.cmbDentitionOrtodontCure.blockSignals(False)

            if u'Санация' in action._actionType._propertiesByName:
                self.cmbDentitionSanitation.blockSignals(True)
                dentitionSanitationProperty = action.getProperty(u'Санация')
                self.cmbDentitionSanitation.setDomain(dentitionSanitationProperty.type().valueDomain)
                dentitionSanitationText = dentitionSanitationProperty.getText() or ''
                self.cmbDentitionSanitation.setValue(dentitionSanitationText)
                self.cmbDentitionSanitation.blockSignals(False)

            if u'Слизистая' in action._actionType._propertiesByName:
                dentitionMucosaText = action.getProperty(u'Слизистая').getText() or ''
                self.edtDentitionMucosa.setValue(dentitionMucosaText)

            if u'Примечание' in action._actionType._propertiesByName:
                dentitionNoteText = action.getProperty(u'Примечание').getText() or ''
                self.edtDentitionNote.setPlainText(dentitionNoteText)


    def updateActionProperties(self, oldAction, newAction):
        newActionType = newAction.getType()
        actionTypeList = newActionType.getPropertiesById().items()
        for actionPropertyType in actionTypeList:
            actionPropertyType = actionPropertyType[1]
            actionPropertyTypeName = actionPropertyType.name
            actionPropertyTypeValue = newAction.getProperty(actionPropertyTypeName).getText()
            oldAction.getProperty(actionPropertyTypeName).setValue(
                                actionPropertyType.convertQVariantToPyValue(actionPropertyTypeValue))
        return oldAction


    def prepareDentition(self, actionTypeId = None, date = None, personId = None):
        db = QtGui.qApp.db
        tablePerson = db.table('vrbPersonWithSpeciality')
        eventId = self.itemId()
        if not actionTypeId:
            actionTypeIdList = db.getIdList('ActionType', 'id', '`flatCode`=\'dentitionInspection\' AND `deleted`=0')
            if actionTypeIdList:
                actionTypeId = actionTypeIdList[0]
        setDate = self.eventSetDateTime.date()
        self.modelClientDentitionHistory.loadClientDentitionHistory(self.clientId, setDate)
        isLoaded = False
        if actionTypeId:
            #actionType = CActionTypeCache.getById(actionTypeId)
            for actionsModel in (self.tabStatus.modelAPActions,
                                 self.tabDiagnostic.modelAPActions,
                                 self.tabCure.modelAPActions,
                                 self.tabMisc.modelAPActions):
                if actionTypeId in actionsModel.actionTypeIdList:
                    actionsModel.addRow(actionTypeId)
                    newRecord, newAction = actionsModel.items()[-1]
                    initActionProperties(newAction)
                    newRecord.setValue('directionDate', QVariant(date))
                    newRecord.setValue('begDate', QVariant(date))
                    newRecord.setValue('endDate', QVariant(date))
                    newRecord.setValue('person_id', QVariant(personId))
                    newRecord.setValue('event_id', QVariant(eventId))
                    recordAction = newAction.getRecord()
                    recordAction.setValue('directionDate', QVariant(date))
                    recordAction.setValue('begDate', QVariant(date))
                    recordAction.setValue('endDate', QVariant(date))
                    recordAction.setValue('person_id', QVariant(personId))
                    recordAction.setValue('event_id', QVariant(eventId))
                    if not self.modelDentition.getClientId():
                        return
                    actionId = forceRef(newRecord.value('id')) if newRecord else None
                    personName = forceString(db.translate(tablePerson, 'id', personId, 'name'))
                    isChecked = 0
                    self.modelClientDentitionHistory.addNewDentitionForVisitItem(newRecord, newAction, actionId, eventId, isChecked, personName)
                    penultimateItemAction = self.modelDentition.getPenultimateItemAction()
                    if penultimateItemAction:
                        self.modelDentition.copyInspection(skippingNames=[u'Статус', u'Санация'],
                                                           action=penultimateItemAction)
                        isLoaded = True
                    self.tblClientDentitionHistory.setCurrentIndex(self.modelClientDentitionHistory.index(0, 0))
                    self.modelClientDentitionHistory.setCurrentDentitionItems(newRecord, newAction, eventId)
                    self.modelClientDentitionHistory.reset()
                    self.isNewDentitionActionInitialized = True
                    self.actionDentitionList[(date.toPyDateTime(), personId, self.itemId())] = (newRecord, newAction)
            if not isLoaded or (self.isNewDentitionActionInitialized and not self.modelDentition.teethIsSet()):
                self.modelDentition.setDefaults(self.clientAge[3]>8)


    def prepareParodentium(self, actionTypeId = None, date = None, personId = None):
        db = QtGui.qApp.db
        tablePerson = db.table('vrbPersonWithSpeciality')
        eventId = self.itemId()
        if not actionTypeId:
            actionTypeIdList = db.getIdList('ActionType', 'id', '`flatCode`=\'parodentInsp\' AND `deleted`=0')
            if actionTypeIdList:
                actionTypeId = actionTypeIdList[0]

        isLoaded = False
        isInit   = False
        if actionTypeId:
            for actionsModel in (self.tabStatus.modelAPActions,
                                 self.tabDiagnostic.modelAPActions,
                                 self.tabCure.modelAPActions,
                                 self.tabMisc.modelAPActions):
                if actionTypeId in actionsModel.actionTypeIdList:
                    actionsModel.addRow(actionTypeId)
                    newRecord, newAction = actionsModel.items()[-1]
                    initActionProperties(newAction)
                    newRecord.setValue('directionDate', QVariant(date))
                    newRecord.setValue('begDate', QVariant(date))
                    newRecord.setValue('endDate', QVariant(date))
                    newRecord.setValue('person_id', QVariant(personId))
                    newRecord.setValue('event_id', QVariant(eventId))
                    recordAction = newAction.getRecord()
                    recordAction.setValue('directionDate', QVariant(date))
                    recordAction.setValue('begDate', QVariant(date))
                    recordAction.setValue('endDate', QVariant(date))
                    recordAction.setValue('person_id', QVariant(personId))
                    recordAction.setValue('event_id', QVariant(eventId))
                    self.modelParodentium.clientId = self.clientId
                    if not self.modelParodentium.clientId:
                        return
                    actionId = forceRef(newRecord.value('id')) if newRecord else None
                    personName = forceString(db.translate(tablePerson, 'id', personId, 'name'))
                    isChecked = 0
                    self.modelClientDentitionHistory.addNewParodentiumForVisitItem(newRecord, newAction, actionId, eventId, isChecked, personName)
                    self.modelParodentium.loadAction(newRecord, newAction, False)
                    penultimateItemAction = self.modelParodentium.getPenultimateItemAction()
                    if penultimateItemAction:
                        self.modelParodentium.copyParodent(action=penultimateItemAction)
                        isLoaded = True
                    isInit = True
                    self.actionParodentiumList[(date.toPyDateTime(), personId, eventId)] = (newRecord, newAction)
            if not isLoaded or (isInit and not self.modelParodentium.teethIsSet()):
                self.modelParodentium.setDefaults(self.clientAge[3]>8)
        self.tblClientDentitionHistory.setCurrentIndex(self.modelClientDentitionHistory.index(0, 0))



    def updateMesMKB(self):
        MKB, MKBEx = self.getFinalDiagnosisMKB()
        self.tabMes.setMKB(MKB)
        self.tabMes.setMKBEx(MKBEx)


    @pyqtSignature('QDate')
    def on_edtBegDate_dateChanged(self, date):
        self.cmbContract.setDate(self.getDateForContract())
        self.tabMes.setEventBegDate(date)
        self.setFilterResult(date)
        self.setPersonDate(date)


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
    def on_modelDiagnostics_diagnosisChanged(self):
        self.updateMesMKB()


    @pyqtSignature('')
    def on_edtDentitionObjectively_editingFinished(self):
        txt = forceString(self.edtDentitionObjectively.value())
        current = self.tblClientDentitionHistory.currentIndex()
        record, action, id, eventId, isChecked, personName = self.modelClientDentitionHistory.getItem(current)
        if action:
            action[u'Объективность'] = txt


    @pyqtSignature('QString')
    def on_cmbDentitionBite_editTextChanged(self, txt):
        current = self.tblClientDentitionHistory.currentIndex()
        record, action, id, eventId, isChecked, personName = self.modelClientDentitionHistory.getItem(current)
        if action:
            action[u'Прикус'] = unicode(txt)


    @pyqtSignature('QString')
    def on_cmbDentitionApparat_editTextChanged(self, txt):
        current = self.tblClientDentitionHistory.currentIndex()
        record, action, id, eventId, isChecked, personName = self.modelClientDentitionHistory.getItem(current)
        if action:
            action[u'Аппарат'] = unicode(txt)


    @pyqtSignature('QString')
    def on_cmbDentitionProtezes_editTextChanged(self, txt):
        current = self.tblClientDentitionHistory.currentIndex()
        record, action, id, eventId, isChecked, personName = self.modelClientDentitionHistory.getItem(current)
        if action:
            action[u'Протезы'] = unicode(txt)


    @pyqtSignature('QString')
    def on_cmbDentitionOrtodontCure_editTextChanged(self, txt):
        current = self.tblClientDentitionHistory.currentIndex()
        record, action, id, eventId, isChecked, personName = self.modelClientDentitionHistory.getItem(current)
        if action:
            action[u'Ортодонтическое лечение'] = unicode(txt)


    @pyqtSignature('QString')
    def on_cmbDentitionSanitation_editTextChanged(self, txt):
        current = self.tblClientDentitionHistory.currentIndex()
        record, action, id, eventId, isChecked, personName = self.modelClientDentitionHistory.getItem(current)
        if action:
            action[u'Санация'] = unicode(txt)


    @pyqtSignature('')
    def on_edtDentitionMucosa_editingFinished(self):
        txt = forceString(self.edtDentitionMucosa.value())
        current = self.tblClientDentitionHistory.currentIndex()
        record, action, id, eventId, isChecked, personName = self.modelClientDentitionHistory.getItem(current)
        if action:
            action[u'Слизистая'] = txt


    @pyqtSignature('')
    def on_edtDentitionNote_textChanged(self):
        txt = unicode(self.edtDentitionNote.toPlainText())
        current = self.tblClientDentitionHistory.currentIndex()
        record, action, id, eventId, isChecked, personName = self.modelClientDentitionHistory.getItem(current)
        if action:
            action[u'Примечание'] = txt


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelVisits_currentChanged(self, current, previous):
        if current.isValid():
            self.setFilterVisitTypeCol(current, self.tblVisits, self.modelVisits)
            row = current.row()
            items = self.modelVisits.items()
            if row >= 0 and row < len(items):
                item = items[row]
                date = forceDateTime(item.value('date'))
                personId = forceRef(item.value('person_id'))
                eventId = forceRef(item.value('event_id'))
                if not eventId:
                    eventId = self.itemId()
                recordDentition, actionDentition = self.actionDentitionList.get((date.toPyDateTime(), personId, eventId), (None, None))
                actionRecordDentition = actionDentition.getRecord() if actionDentition else None
                actionEventId = forceRef(actionRecordDentition.value('event_id')) if actionRecordDentition else None
                isCurrentDentitionAction = (eventId == actionEventId)
                self.modelDentition.loadAction(actionRecordDentition, actionDentition, isCurrentDentitionAction)
                self.loadDentitionAdditional(actionRecordDentition, actionDentition, isCurrentDentitionAction)
                recordParodentium, actionParodentium = self.actionParodentiumList.get((date.toPyDateTime(), personId, eventId), (None, None))
                actionRecordParodentium = actionParodentium.getRecord() if actionParodentium else None
                self.modelParodentium.loadAction(actionRecordParodentium, actionParodentium, isCurrentDentitionAction)
                self.modelClientDentitionHistory.setCurrentParadentiumItem(actionRecordParodentium, actionParodentium)
                currentRow = self.modelClientDentitionHistory.setCurrentDentitionItem(actionRecordDentition, actionDentition)
                if currentRow is not None:
                    self.tblClientDentitionHistory.setCurrentIndex(self.modelClientDentitionHistory.index(currentRow, 0))


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelClientDentitionHistory_currentChanged(self, current, previous):
        if current.isValid():
            currentRow = current.row()
            self.modelClientDentitionHistory.setCurrentHistoryRow(currentRow)
            record, action, id, eventId, isChecked, personName = self.modelClientDentitionHistory.getItem(current)
            isCurrentDentitionAction = self.modelClientDentitionHistory.isCurrentDentitionAction(currentRow) and (self.itemId() == eventId)
            self.modelDentition.loadAction(record, action, isCurrentDentitionAction)
            self.loadDentitionAdditional(record, action, isCurrentDentitionAction)
            paradentiumItem = self.modelClientDentitionHistory.getParadentiumItem(currentRow)
            self.modelParodentium.loadAction(paradentiumItem[0], paradentiumItem[1], isCurrentDentitionAction)


    def initFocus(self):
        if self.cmbContract.count() != 1:
            self.cmbContract.setFocus(Qt.OtherFocusReason)
        else:
            self.tblDiagnostics.setFocus(Qt.OtherFocusReason)

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


    def isPrimary(self):
        return self.cmbPrimary.currentIndex() == 1


    def getRecord(self):
        record = CEventEditDialog.getRecord(self)
        showTime = getEventShowTime(self.eventTypeId)
        self.getShowButtonAccount()
        self.getShowButtonTemperatureList()
        self.getShowButtonNomenclatureExpense()
        self.getShowButtonJobTickets()
        CF043Dialog.defaultEventResultId = self.cmbResult.value()
        getRBComboBoxValue(self.cmbContract,    record, 'contract_id')
        getDatetimeEditValue(self.edtBegDate, self.edtBegTime, record, 'setDate', showTime)
        record.setValue('setPerson_id', self.setPerson)
        getDatetimeEditValue(self.edtEndDate, self.edtEndTime, record, 'execDate', showTime)
        getRBComboBoxValue(self.cmbPerson,      record, 'execPerson_id')
        getRBComboBoxValue(self.cmbResult,      record, 'result_id')
        getDateEditValue(self.edtNextDate,      record, 'nextEventDate')
        record.setValue('isPrimary', toVariant(self.cmbPrimary.currentIndex()+1))
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
        self.saveDiagnostics(eventId)
        self.tabMedicalDiagnosis.save(eventId)
        self.tabMes.save(eventId)
        setAskedClassValueForDiagnosisManualSwitch(None)
        self.saveActions(eventId)
        self.tabCash.save(eventId)
        self.saveBlankUsers(self.blankMovingIdList)
        self.tabNotes.saveAttachedFiles(eventId)
        self.saveTrailerActions(eventId)


    def saveTrailerActions(self, eventId):
        if self.trailerActions:
            for action in self.trailerActions:
                prevActionId = self.trailerIdList.get(action.trailerIdx - 1, None)
                action.getRecord().setValue('prevAction_id', toVariant(prevActionId))
                action.save(eventId)


    def afterSave(self):
        CEventEditDialog.afterSave(self)
        QtGui.qApp.session("F043_resultId", self.cmbResult.value())


    def saveVisits(self, eventId):
        self.modelVisits.saveItems(eventId)


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
        MKBDiagnosisIdPairList = []
        prevId = 0
        for row, item in enumerate(items):
            MKB = forceStringEx(item.value('MKB'))
            MKBEx = forceStringEx(item.value('MKBEx'))
            TNMS = forceStringEx(item.value('TNMS'))
            morphologyMKB = forceStringEx(item.value('morphologyMKB'))
            personId = forceRef(item.value('person_id'))
            specialityId = forceRef(QtGui.qApp.db.translate('Person', 'id', personId, 'speciality_id'))
            diagnosisTypeId = self.getDiagnosisTypeId(isFirst)
            diagnosticTypeId = forceRef(item.value('diagnosisType_id'))
            if not diagnosticTypeId:
                item.setValue('diagnosisType_id', toVariant(diagnosisTypeId))
            item.setValue('speciality_id', toVariant(specialityId))
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
            if prevId > itemId:
                item.setValue('id', QVariant())
                prevId=0
            else:
               prevId = itemId
            isFirst = False
            MKBDiagnosisIdPairList.append((MKB, diagnosisId))
        self.modelDiagnostics.saveItems(eventId)
        self.modifyDiagnosises(MKBDiagnosisIdPairList)


    def saveActions(self, eventId):
        self.tabStatus.saveActions(eventId)
        self.tabDiagnostic.saveActions(eventId)
        self.tabCure.saveActions(eventId)
        self.tabMisc.saveActions(eventId)


    def checkDataEntered(self):
        result = CEventEditDialog.checkDataEntered(self)
        tabList = [self.tabStatus, self.tabDiagnostic, self.tabCure, self.tabMisc]
        self.blankMovingIdList = []
        mesRequired = getEventMesRequired(self.eventTypeId)
        csgRequired  = getEventCSGRequired(self.eventTypeId)

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
        result = result and (self.orgId != QtGui.qApp.currentOrgId() or self.cmbContract.value() or self.checkInputMessage(u'договор', False, self.cmbContract))
        result = result and (self.cmbPerson.value() or self.checkInputMessage(u'врача', False, self.cmbPerson))
        result = result and self.checkExecPersonSpeciality(self.cmbPerson.value(), self.cmbPerson)
        result = result and (not begDateCheck.isNull() or self.checkInputMessage(u'дату назначения', False, self.edtBegDate))
        if endDateCheck:
            checkRequireAction, ActionTypeIdList = self.checkRequireAction(self.eventTypeId, tabList, self.personSpecialityId, self.modelDiagnostics.items())
            result = result and checkRequireAction
            if ActionTypeIdList:
                self.setActionConsbyIds(ActionTypeIdList)
            result = result and self.checkActionDataEntered(begDate, QDateTime(), endDate, self.tabToken, self.edtBegDate, None, self.edtEndDate)
            result = result and self.checkEventDate(begDate, endDate, nextDate, self.tabToken, self.edtNextDate,self.edtEndDate, True)
            minDuration,  maxDuration = getEventDurationRange(self.eventTypeId)
            if minDuration<=maxDuration:
                result = result and (begDateCheck.daysTo(endDateCheck)+1>=minDuration or self.checkValueMessage(u'Длительность должна быть не менее %s'%formatNum(minDuration, (u'дня', u'дней', u'дней')), False, self.edtEndDate))
                result = result and (maxDuration==0 or begDateCheck.daysTo(endDateCheck)+1<=maxDuration or self.checkValueMessage(u'Длительность должна быть не более %s'%formatNum(maxDuration, (u'дня', u'дней', u'дней')), False, self.edtEndDate))
            result = result and (len(self.modelDiagnostics.items())>0 or self.checkInputMessage(u'диагноз', False, self.tblDiagnostics))
            result = result and self.checkDiagnosticsType(self.modelDiagnostics)
            result = result and (self.cmbResult.value()  or self.checkInputMessage(u'результат',   False, self.cmbResult))
            result = result and self.checkEventResult()
            result = result and self.checkDiagnosticsDataEntered()
            result = result and self.checkExecDateForVisit(endDateCheck)
            result = result and self.checkExecPersonSpeciality(self.cmbPerson.value(), self.cmbPerson)
            result = result and self.checkDiagnosticsPersonSpeciality()
            if mesRequired:
                result = result and self.tabMes.checkMesAndSpecification()
                result = result and (self.tabMes.chechMesDuration() or self.checkValueMessage(u'Длительность события должна попадать в интервал минимальной и максимальной длительности по требованию к МЭС', True, self.edtBegDate))
            if csgRequired:
                result = result and self.tabMes.checkCsg()
#                result = result and self.checkInspectionsMKBForMes(self.tblInspections, self.tabMes.cmbMes.value())
        else:
            result = result and self.checkDiagnosticsPersonSpeciality()
        result = result and self.checkActionsDateEnteredActuality(begDate, endDate, tabList)
        result = result and self.checkActionsDataEntered(begDate, endDate)
        result = result and self.checkDeposit(True)
        result = result and (self.checkCorrectlyEnteredPersons( self.cmbPerson
            ) if not QtGui.qApp.checkGlobalPreference('23:checkChosenPerson',
                                                      u'не выполнять') else True)
        result = result and (len(self.modelVisits.items())>0 or self.checkInputMessage(u'посещение', False, self.tblVisits))
        #result = result and self.checkVisitsDataEntered(begDate.date() if isinstance(begDate, QDateTime) else begDate, endDate.date() if isinstance(endDate, QDateTime) else endDate)
        result = result and self.checkVisitsDataEntered(begDate, endDate)
        result = result and self.tabCash.checkDataLocalContract()
        result = result and self.checkSerialNumberEntered()
        result = result and self.checkTabNotesEventExternalId()
        self.valueForAllActionEndDate = None
        if self.edtEndDate.date():
            result = result and self.checkAndUpdateExpertise(self.edtEndDate.date(), self.cmbPerson.value())
            if CFinanceType.getCode(self.eventFinanceId) == CFinanceType.CMI and QtGui.qApp.defaultKLADR()[:2] == u'23':
                result = result and self.checkServiceDates(begDate, endDate)
        result = result and self.selectNomenclatureAddedActions(tabList)
        if result and self.eventFinanceId == CFinanceType.CMI and QtGui.qApp.defaultKLADR()[:2] == u'23':
            result = self.check357()
        return result


    def checkDiagnosticsType(self, model):
        result = True
        endDate = self.edtEndDate.date()
        if endDate:
            result = result and self.checkDiagnosticsTypeEnd(model) or self.checkValueMessage(u'Необходимо указать заключительный диагноз', False, self.tblDiagnostics)
        return result


    def checkDiagnosticsTypeEnd(self, model):
        for row, record in enumerate(model.items()):
            if  forceInt(record.value('diagnosisType_id')) == model.diagnosisTypeCol.ids[0]:
                return True
        return False

    
    def checkDiagnosticsPersonSpeciality(self):
        result = True
        result = result and self.checkPersonSpecialityDiagnostics(self.modelDiagnostics, self.tblDiagnostics)
        return result


    def checkDiagnosticsDataEntered(self):
        result = True
        result = result and self.checkDiagnostics(self.modelDiagnostics, self.cmbPerson.value())
        result = result and self.checkDiagnosisType(self.modelDiagnostics, self.tblDiagnostics)
        return result


    def checkDiagnostics(self, model, finalPersonId):
        for row, record in enumerate(model.items()):
            if not self.checkDiagnosticDataEntered(row, record):
                return False
        return True
        
    def check357(self):
        result = True
        self.blankMovingIdList = []
        dateDict = dict()

        for tab in (self.tabStatus,
                      self.tabDiagnostic,
                      self.tabCure,
                      self.tabMisc):
                          
            model = tab.modelAPActions
            for row, (record, action) in enumerate(model.items()):
                serviceId = action._actionType.nomenclativeServiceId
                if serviceId:
                    date = forceDate(record.value('endDate'))
                    if not date:
                        date = forceDate(record.value('begDate'))
                    date = date.toPyDate()
                    serviceCode = forceString(QtGui.qApp.db.translate('rbService', 'id', serviceId, 'infis'))
                    if (serviceCode[:7] in ('B01.063', 'B01.064', 'B01.065', 'B01.066', 'B01.067', 
                            'B04.063', 'B04.064', 'B04.065', 'B04.066', 'B04.067') or serviceCode in ('B02.065.001', 'B02.065.002')) and serviceCode not in (
                            'B01.063.004',  'B01.063.005', 'B01.063.006', 'B01.063.007', 'B01.063.010', 'B01.063.011', 'B01.063.012',
                            'B01.064.005', 'B01.064.006', 'B01.064.007',
                            'B01.065.009', 'B01.065.010', 'B01.065.011', 
                            'B01.067.004'):
                        dateDict[date] = 1
                    else:
                        dateDict[date] = dateDict.get(date, 0)
        dateStr = ', '.join([forceString(key.strftime('%d.%m.%Y')) for key in sorted(dateDict.keys()) if dateDict[key] == 0])
        if dateStr:
            dateStr = (u'дату ' if len(dateStr) == 10 else u'даты ') + dateStr
            text = u'На {0:s} отсутствует статистическая услуга приема врача-стоматолога/ортодонта или зубного врача'.format(dateStr)
            buttons = QtGui.QMessageBox.Ok
            if QtGui.qApp.userHasRight(urCanSaveF043WithoutStom):
                buttons = buttons | QtGui.QMessageBox.Ignore
            
            res = QtGui.QMessageBox.warning(self,
                                         u'Внимание!',
                                         text,
                                         buttons,
                                         QtGui.QMessageBox.Ok)
            if res == QtGui.QMessageBox.Ok:
                result = False
        return result


    def checkDiagnosticDataEntered(self, row, record):
        result = True
        if result:
            MKB = forceString(record.value('MKB'))
            MKBEx = forceString(record.value('MKBEx'))
            personId = forceRef(record.value('person_id'))
            specialityId = forceRef(QtGui.qApp.db.translate('Person', 'id', personId, 'speciality_id'))
            result = specialityId or self.checkValueMessage(u'Отсутствует специальность врача', False, self.tblDiagnostics, row, record.indexOf('person_id'))
            result = result and MKB or self.checkInputMessage(u'диагноз', False, self.tblDiagnostics, row, record.indexOf('MKB'))
            result = result and self.checkActualMKB(self.tblDiagnostics, self.edtBegDate.date(), MKB, record, row)
            if result:
                char = MKB[:1]
                blockMKB = forceInt(MKB[1:3])
                traumaTypeId = forceRef(record.value('traumaType_id'))
                if char in 'ST' and not (char in 'T' and 36 <= blockMKB <= 78):
                    if not traumaTypeId:
                        result = self.checkValueMessage(u'Необходимо указать тип травмы',  True if QtGui.qApp.controlTraumaType()==0 else False, self.tblDiagnostics, row, record.indexOf('traumaType_id'))
                    if result:
                        result = MKBEx or self.checkInputMessage(u'Дополнительный диагноз', True if QtGui.qApp.controlMKBExForTraumaType()==0 else False, self.tblDiagnostics, row, record.indexOf('MKBEx'))
                        if result:
                            charEx = MKBEx[:1]
                            if charEx not in 'VWXY':
                                result = self.checkValueMessage(u'Доп.МКБ не соотвествует Доп.МКБ при травме', True, self.tblDiagnostics, row, record.indexOf('MKBEx'))
                if char not in 'ST' and traumaTypeId:
                    result = self.checkValueMessage(u'Необходимо удалить тип травмы', False, self.tblDiagnostics, row, record.indexOf('traumaType_id'))
                result = self.checkRequiresFillingDispanser(result, self.tblDiagnostics, record, row, MKB)
                if not forceRef(record.value('person_id')):
                    result = result and self.checkValueMessage(u'Необходимо указать врача установившего диагноз', False, self.tblDiagnostics, row, record.indexOf('person_id'))
            result = result and self.checkPersonSpeciality(record, row, self.tblDiagnostics)
            if not forceRef(record.value('result_id')):
                result = result and self.checkValueMessage(u'Необходимо указать результат', False, self.tblDiagnostics, row, record.indexOf('result_id'))
            result = result and self.checkPeriodResultHealthGroup(record, row, self.tblDiagnostics)
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


    def getEventInfo(self, context):
        result = CEventEditDialog.getEventInfo(self, context, CTeethEventInfo)
        # инициализация свойств
        result._isPrimary = self.cmbPrimary.currentIndex()+1
        # инициализация таблиц
        result._actions = CActionInfoProxyList(context,
                [self.tabStatus.modelAPActions, self.tabDiagnostic.modelAPActions, self.tabCure.modelAPActions, self.tabMisc.modelAPActions, self.tabMedicalDiagnosis.tblEventMedicalDiagnosis.model()],
                result)
        result.initActions() # инициализируем _action_stomat и _action_parodent
        result._diagnosises = CDiagnosticInfoProxyList(context, [self.modelDiagnostics])
        result._visits = CVisitInfoProxyList(context, self.modelVisits)
        return result


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


    @pyqtSignature('int')
    def on_dentitionTabWidget_currentChanged(self, index):
        model = self.modelClientDentitionHistory
        if index == INSPECTION_DENTITION_TAB_INDEX:
            model.setShownHistoryType(model.dentitionIsShown)
        elif index == RESULT_DENTITION_TAB_INDEX:
            model.setShownHistoryType(model.paradentiumIsShown)


    @pyqtSignature('int')
    def on_tabWidget_currentChanged(self, index):
        widget = self.tabWidget.widget(index)
        if widget is not None:
            focusProxy = widget.focusProxy()
            if focusProxy:
                focusProxy.setFocus(Qt.OtherFocusReason)
        self.btnPrintMedicalDiagnosisEnabled(index)
        if widget == self.tabMes and self.eventTypeId:
            self.tabMes.setMESServiceTemplate(self.eventTypeId)
        if widget == self.tabAmbCard: # amb card page
            self.tabAmbCard.resetWidgets()
        if widget == self.tabToken:
            self._recountCommonUet()


    def getTempInvalidInfo(self, context):
        return self.grpTempInvalid.getTempInvalidInfo(context)


    @pyqtSignature('')
    def on_mnuDiagnostics_aboutToShow(self):
        canRemove = False
        currentRow = self.tblDiagnostics.currentIndex().row()
        if currentRow>=0:
#            canRemove = self.modelDiagnostics.payStatus(currentRow) == 0
            canRemove = True
        self.actDiagnosticsRemove.setEnabled(canRemove)


    @pyqtSignature('')
    def on_actDiagnosticsRemove_triggered(self):
        currentRow = self.tblDiagnostics.currentIndex().row()
        self.modelDiagnostics.removeRowEx(currentRow)
        self.updateDiagnosisTypes()


    @pyqtSignature('QVariant&')
    def on_modelDiagnostics_resultChanged(self, resultId):
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
            CF043Dialog.defaultDiagnosticResultId = self.modelDiagnostics.resultId()
            defaultResultId = getEventResultId(CF043Dialog.defaultDiagnosticResultId, self.eventPurposeId)
            if defaultResultId and isDefaultResultIdValid(defaultResultId, self.eventPurposeId, resultCond):
                self.cmbResult.setValue(defaultResultId)
            else:
                self.cmbResult.setValue(currentValue)
        else:
            self.cmbResult.setValue(currentValue)


    @pyqtSignature('int')
    def on_cmbPerson_currentIndexChanged(self):
        self.setPersonId(self.cmbPerson.value())


# #####################################################################

class CF043BaseDiagnosticsModel(CMKBListInDocTableModel):
    __pyqtSignals__ = ('typeOrPersonChanged()',
                       'diagnosisChanged()',
                       'resultChanged()',
                      )
    MKB_allowed_morphology = ['C', 'D']

    def __init__(self, parent, finishDiagnosisTypeCode, baseDiagnosisTypeCode, accompDiagnosisTypeCode):
        CMKBListInDocTableModel.__init__(self, 'Diagnostic', 'id', 'event_id', parent)
        self.isManualSwitchDiagnosis = QtGui.qApp.defaultIsManualSwitchDiagnosis()
        self.isMKBMorphology = QtGui.qApp.defaultMorphologyMKBIsVisible()
        self.characterIdForHandleDiagnosis = None
        self._parent = parent
        self.diagnosisTypeCol = CDiagnosisTypeCol( u'Тип', 'diagnosisType_id', 2, [finishDiagnosisTypeCode, baseDiagnosisTypeCode, accompDiagnosisTypeCode], smartMode=False)
        self.addCol(self.diagnosisTypeCol)
        self.addCol(CPersonFindInDocTableCol(u'Врач', 'person_id',  20, 'vrbPersonWithSpecialityAndOrgStr', parent=parent))
        self.addExtCol(CICDExInDocTableCol(u'МКБ',         'MKB',   7), QVariant.String)
        if QtGui.qApp.isExSubclassMKBVisible():
            self.addExtCol(CMKBExSubclassCol(u'РСК', 'exSubclassMKB', 10), QVariant.String).setToolTip(u'Расширенная субклассификация МКБ')
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
        self.addCol(CRBInDocTableCol(    u'ДН',            'dispanser_id',   7, rbDispanser, showFields=CRBComboBox.showCode, preferredWidth=150)).setToolTip(u'Диспансерное наблюдение')
#        self.addCol(CRBLikeEnumInDocTableCol(u'Госп',      'hospital',       7, CHospitalInfo.names, showFields=CRBComboBox.showCode, preferredWidth=150)).setToolTip(u'Потребность в госпитализации')
        self.addCol(CRBInDocTableCol(    u'Травма',        'traumaType_id', 10, rbTraumaType, addNone=True, showFields=CRBComboBox.showName, preferredWidth=150))
        self.addCol(CToxicSubstances(u'ТоксВещ', 'toxicSubstances_id', 10, addNone=True, showFields=CRBComboBox.showName, preferredWidth=150)).setToolTip(u'Токсичное вещество')
        self.addCol(CRBInDocTableCol(    u'ГрЗд',          'healthGroup_id', 7, rbHealthGroup, addNone=True, showFields=CRBComboBox.showCode, preferredWidth=150)).setToolTip(u'Группа здоровья')
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
                    if not (bool(mkb) and mkb[0] in CF043BaseDiagnosticsModel.MKB_allowed_morphology):
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
        result.append(QtSql.QSqlField('cTumor_id', QVariant.Int))
        result.append(QtSql.QSqlField('cNodus_id', QVariant.Int))
        result.append(QtSql.QSqlField('cMetastasis_id', QVariant.Int))
        result.append(QtSql.QSqlField('cTNMphase_id', QVariant.Int))
        result.append(QtSql.QSqlField('pTumor_id', QVariant.Int))
        result.append(QtSql.QSqlField('pNodus_id', QVariant.Int))
        result.append(QtSql.QSqlField('pMetastasis_id', QVariant.Int))
        result.append(QtSql.QSqlField('pTNMphase_id', QVariant.Int))
        result.setValue('person_id',     toVariant(eventEditor.getSuggestedPersonId()))
        if self.items():
            result.setValue('diagnosisType_id',  toVariant(self.diagnosisTypeCol.ids[1] if QtGui.qApp.diagnosisTypeAfterFinalForm043() else self.diagnosisTypeCol.ids[2]))
        else:
            result.setValue('diagnosisType_id',  toVariant(self.diagnosisTypeCol.ids[0] if self.diagnosisTypeCol.ids[0] else self.diagnosisTypeCol.ids[1]))
            result.setValue('result_id',  toVariant(CF043Dialog.defaultDiagnosticResultId))
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
                    self.emitTypeOrPersonChanged()
                return result
            elif column == 1: # врач
                personId = forceRef(value)
                if not eventEditor.checkClientAttendanceEE(personId):
                    return False
                result = CMKBListInDocTableModel.setData(self, index, value, role)
                if result:
                    self.updateDiagnosisType(set())
                    #self.emitTypeOrPersonChanged()
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
                    self.emitTypeOrPersonChanged()
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
        for row, item in enumerate(self.items()):
            personId = forceRef(item.value('person_id'))
            rows = mapPersonIdToRow.setdefault(personId, [])
            rows.append(row)
            diagnosisTypeId = forceRef(item.value('diagnosisType_id'))
            diagnosisTypeIds.append(diagnosisTypeId)
        for personId, rows in mapPersonIdToRow.iteritems():
            if self.diagnosisTypeCol.ids[0] and personId == self._parent.personId:
                firstDiagnosisId = self.diagnosisTypeCol.ids[0]
            else:
                firstDiagnosisId = self.diagnosisTypeCol.ids[1]
            baseDiagnosisId = self.diagnosisTypeCol.ids[1] if QtGui.qApp.diagnosisTypeAfterFinalForm043() else self.diagnosisTypeCol.ids[2]
            usedDiagnosisTypeIds = [diagnosisTypeIds[row] for row in fixedRowSet.intersection(set(rows))]
            freeRows = set(rows).difference(fixedRowSet)
            if firstDiagnosisId != baseDiagnosisId and self.diagnosisTypeCol.ids[0] in usedDiagnosisTypeIds and freeRows:
                for row in rows:
                    if row in freeRows and diagnosisTypeIds[row] == firstDiagnosisId:
                        self.items()[row].setValue('diagnosisType_id', toVariant(baseDiagnosisId))
                        self.emitCellChanged(row, item.indexOf('diagnosisType_id'))
                        diagnosisTypeIds[row] = forceRef(self.items()[row].value('diagnosisType_id'))
            if firstDiagnosisId == baseDiagnosisId and self.diagnosisTypeCol.ids[0] in usedDiagnosisTypeIds:
                for row in fixedRowSet.intersection(set(rows)):
                    usedDiagnosisTypeId = diagnosisTypeIds[row]
                    if self.diagnosisTypeCol.ids[0] == usedDiagnosisTypeId:
                        self.items()[row].setValue('diagnosisType_id', toVariant(baseDiagnosisId))
                        self.emitCellChanged(row, item.indexOf('diagnosisType_id'))
                        diagnosisTypeIds[row] = forceRef(self.items()[row].value('diagnosisType_id'))


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


    def emitTypeOrPersonChanged(self):
        self.emit(SIGNAL('typeOrPersonChanged()'))


class CF043FinalDiagnosticsModel(CF043BaseDiagnosticsModel):
    __pyqtSignals__ = ('resultChanged(QVariant&)',
                      )

    def __init__(self, parent):
        CF043BaseDiagnosticsModel.__init__(self, parent, '1', '2', '9')
        self.addCol(CRBInDocTableCol(    u'Результат',     'result_id',     10, 'rbDiagnosticResult', showFields=CRBComboBox.showNameAndCode, preferredWidth=350))
        self.mapMKBToServiceId = {}


    def getCloseOrMainDiagnosisTypeIdList(self):
        return [self.diagnosisTypeCol.codeToId(code) for code in ('1', '2')]
    
    
    def getMainDiagnosisTypeIdList(self):
        return [self.diagnosisTypeCol.codeToId('2')]


    def setData(self, index, value, role=Qt.EditRole):
        result = CF043BaseDiagnosticsModel.setData(self, index, value, role)
        if result:
            column = index.column()
            if column == 0 or column == self.getColIndex('result_id'): # тип диагноза и результат
                row = index.row()
                item = self.items()[row]
                diagnosisTypeId = forceRef(item.value('diagnosisType_id'))
                if diagnosisTypeId == self.diagnosisTypeCol.ids[0]:
                    self.emitResultChanged(item.value('result_id'))
        return result


    def resultId(self):
        finalDiagnosisId = self.diagnosisTypeCol.ids[0]
        items = self.items()
        for item in items:
            diagnosisTypeId = forceRef(item.value('diagnosisType_id'))
            if diagnosisTypeId == finalDiagnosisId:
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


    def emitResultChanged(self, resultId):
        self.emit(SIGNAL('resultChanged(QVariant&)'), resultId)
        
    
    def saveItems(self, masterId = None):
        CMKBListInDocTableModel.saveItems(self, masterId)
        self.prophylaxisPlanningSync()
