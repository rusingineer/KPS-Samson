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
## Форма 003: лечение в стационаре и т.п.
##
#############################################################################


from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import Qt, QDate, QDateTime, QModelIndex, QObject, QTime, QVariant, pyqtSignature, SIGNAL

from Events.ExportMIS import iniExportEvent
from Events.RelatedEventAndActionListDialog import CRelatedEventAndActionListDialog
from Events.TeethEventInfo import CTeethEventInfo
from F088.F0882022EditDialog import CEventExportTableModel, CAdvancedExportTableModel
from Orgs.Utils import getOrgstructureListByEventtypeId, getPersonListByEventtypeId
from library.Attach.AttachAction import getAttachAction
from library.Calendar import wpSevenDays, wpSixDays, wpFiveDays
from library.crbcombobox        import CRBComboBox
from library.ICDInDocTableCol   import CICDExInDocTableCol
from library.ICDMorphologyInDocTableCol import CMKBMorphologyCol
from library.InDocTable         import CMKBListInDocTableModel, CBoolInDocTableCol, CInDocTableCol, CRBInDocTableCol, CEnumInDocTableCol
from library.interchange        import getDatetimeEditValue, getRBComboBoxValue, setDatetimeEditValue, setRBComboBoxValue
from library.PrintInfo          import CInfoContext
from library.PrintTemplates     import applyTemplate, customizePrintButton, getPrintButton
from library.TNMS.TNMSComboBox  import CTNMSCol
from library.MKBExSubclassComboBox import CMKBExSubclassCol
from library.Utils              import copyFields, forceBool, forceDate, forceDateTime, forceInt, forceRef, forceString, formatNum, toVariant, variantEq, forceStringEx, toDateTimeWithoutSeconds, calcAgeInYears

from Events.Action import CActionType, CActionTypeCache
from Events.ActionInfo          import CActionInfoProxyList
from Events.ActionsModel import getActionDefaultAmountEx
from Events.ActionsSummaryModel import CFxxxActionsSummaryModel
from Events.DiagnosisType       import CDiagnosisTypeCol
from Events.EventEditDialog     import CEventEditDialog, CDiseaseCharacter, CDiseaseStage, CDiseasePhases, CToxicSubstances, getToxicSubstancesIdListByMKB
from Events.EventInfo           import CDiagnosticInfoProxyList
from Events.Utils import getEventAvailableOrders, getEventEnableActionsBeyondEvent, checkDiagnosis, checkIsHandleDiagnosisIsChecked, \
    CTableSummaryActionsMenuMixin, getAvailableCharacterIdByMKB, getDiagnosisId2, getEventDurationRange, \
    getHealthGroupFilter, \
    updateDurationTakingIntoMedicalDaysEvent, updateDurationEvent, getEventMesRequired, getEventResultId, \
    getEventSetPerson, getEventShowTime, setAskedClassValueForDiagnosisManualSwitch, getEventIsPrimary, \
    getEventDuration, CFinanceType, getEventDurationRule, getNewResultCond, \
    isDefaultResultIdValid, isDispanserisation, mkbIsOnko, getEventAidTypeRegionalCode, getEventTypeForm, \
    mkbIsVIMIS
from F003.PreF003Dialog         import CPreF003Dialog, CPreF003DagnosticAndActionPresets
from Users.Rights               import urAccessF003planner, urAccessF090planner, urAdmin, urEditEndDateEvent, urRegTabWriteRegistry, urRegTabReadRegistry, urEditEventJournalOfPerson, urCanReadClientVaccination, urCanEditClientVaccination
from F003.ExecPersonListEditorDialog import CExecPersonListEditorDialog
from Orgs.PersonComboBoxEx      import CPersonFindInDocTableCol
from F003.Ui_F003               import Ui_Dialog


class CF003Dialog(CEventEditDialog, Ui_Dialog, CTableSummaryActionsMenuMixin):
    defaultEventResultId = None
#    defaultDiagnosticResultId = None
    dfAccomp = 2  # Сопутствующий

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
        self.addModels('PreliminaryDiagnostics', CF003PreliminaryDiagnosticsModel(self))
        self.addModels('FinalDiagnostics',       CF003FinalDiagnosticsModel(self))
        self.addModels('ActionsSummary',         CFxxxActionsSummaryModel(self, True))
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
        self.addObject('btnPrint', getPrintButton(self, ''))
        self.addObject('btnPlanning', QtGui.QPushButton(u'Планировщик', self))
        # self.addObject('btnMedicalCommission', QtGui.QPushButton(u'ВК', self))
        self.addObject('btnRelatedEvent', QtGui.QPushButton(u'Связанные события', self))
        self.addObject('btnTemperatureList', QtGui.QPushButton(u'Температурный лист', self))
        self.addObject('btnPrintMedicalDiagnosis', getPrintButton(self, '', u'Врачебный диагноз'))
        self.setupUi(self)

        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setWindowTitleEx(u'Осмотр Ф.003')
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
        self.tblPreliminaryDiagnostics.setModel(self.modelPreliminaryDiagnostics)
        self.tblFinalDiagnostics.setModel(self.modelFinalDiagnostics)
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
        self.tblPreliminaryDiagnostics.addCopyDiagnosisToFinal(self)
        self.setupVisitsIsExposedPopupMenu()
        CTableSummaryActionsMenuMixin.__init__(self)
        self.btnExecPersonList.setEnabled(QtGui.qApp.isCheckEventJournalOfPerson() and QtGui.qApp.userHasRight(urEditEventJournalOfPerson))
        self.btnExecPersonList.setVisible(QtGui.qApp.isCheckEventJournalOfPerson())

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
        self.valueForAllActionEndDate = None
        self.execPersonId = None

        self.tblExport.enableColsHide()
        self.tblExport.enableColsMove()

        self.tblExport_FileAttach.enableColsHide()
        self.tblExport_FileAttach.enableColsMove()

        self.tblExport_VIMIS.enableColsHide()
        self.tblExport_VIMIS.enableColsMove()

        self.postSetupUi()

        self.mapJournalOfPerson = []
        self.mapJournalInfoTransfer = []
        self.tblActions.enableColsHide()
        self.tblActions.enableColsMove()
        if hasattr(self, 'edtEndDate'):
            self.edtEndDate.setEnabled(QtGui.qApp.userHasRight(urEditEndDateEvent))
        if hasattr(self, 'edtEndTime'):
            self.edtEndTime.setEnabled(QtGui.qApp.userHasRight(urEditEndDateEvent))
        self.btnPrintMedicalDiagnosis.setVisible(False)
        self.V036map = dict()

# done


    def destroy(self):
        CEventEditDialog.deleteLater(self)
        self.tblPreliminaryDiagnostics.setModel(None)
        self.tblFinalDiagnostics.setModel(None)
#        self.tblFeed.setModel(None)
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
        self.tabFeed.deleteLater()
        self.tabMes.deleteLater()
        del self.modelPreliminaryDiagnostics
        del self.modelFinalDiagnostics
        del self.modelActionsSummary
        self.tabAmbCard.deleteLater()


#    def currentClientId(self): # for AmbCard mixin
#        return self.clientId


    def _prepare(self, clientId, eventTypeId, orgId, personId, eventSetDatetime, eventDatetime, weekProfile, numDays,
                 presetDiagnostics, presetActions, disabledActions, externalId, assistantId, curatorId,
                 actionTypeIdValue = None, valueProperties = [], relegateOrgId = None, relegatePersonId=None,
                 diagnos = None, financeId = None, protocolQuoteId = None, actionByNewEvent = [],
                 order = 1, actionListToNewEvent = [], docNum=None, relegateInfo=[], plannedEndDate = None, isEdit = False):
        if not isEdit:
            self.eventSetDateTime = eventSetDatetime if isinstance(eventSetDatetime, QDateTime) else QDateTime(eventSetDatetime)
            self.eventDate = eventDatetime.date() if isinstance(eventDatetime, QDateTime) else eventDatetime


            self.setOrgId(orgId if orgId else QtGui.qApp.currentOrgId())
            self.setEventTypeId(eventTypeId)
            self.setClientId(clientId)
            self.prolongateEvent = True if actionByNewEvent or actionListToNewEvent else False
            self.tabNotes.setNotesEx(externalId, assistantId, curatorId, relegateOrgId, relegatePersonId, clientId, relegateInfo)
            self.setExternalId(externalId)
            self.setOrgStructAndPersonsInCmbPersons(eventTypeId)
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
            self.initOrder(forceString(getEventAvailableOrders(eventTypeId)), order+1)
            self.cmbContract.setCurrentIndex(0)
            self.tabFeed.prepare()
            self.tabFeed.setClientId(clientId)
            self.tabFeed.setPatronId(self.tabNotes.cmbClientRelationConsents.value())
            self.tabFeed.setContractId(self.cmbContract.value())
            self.tabFeed.setFilterDiet(self.eventSetDateTime.date(), self.eventDate)
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
        if not actionListToNewEvent:
            self.prepareActions(presetActions, disabledActions, actionTypeIdValue, valueProperties,
                                diagnos, financeId, protocolQuoteId, actionByNewEvent, docNum, relegateInfo, plannedEndDate)
        self.grpTempInvalid.pickupTempInvalid()
        self.grpAegrotat.pickupTempInvalid()
        self.grpDisability.pickupTempInvalid()
        self.grpVitalRestriction.pickupTempInvalid()
        self.setIsDirty(False)
        self.tabNotes.setEventEditor(self)
        self.primaryExec = False
        self.setFilterResult(self.eventSetDateTime.date())
        return self.checkEventCreationRestriction() and self.checkDeposit()


    def prepare(self, clientId, eventTypeId, orgId, personId, eventSetDatetime, eventDatetime, weekProfile,
                numDays, externalId, assistantId, curatorId, flagHospitalization = False,
                actionTypeIdValue = None, valueProperties = [], tissueTypeId=None, selectPreviousActions=False,
                relegateOrgId = None, relegatePersonId=None, diagnos = None, financeId = None,
                protocolQuoteId = None, actionByNewEvent = [], order = 1,  actionListToNewEvent = [],
                typeQueue = -1, docNum=None, relegateInfo=[], plannedEndDate = None, mapJournalInfoTransfer = [], voucherParams = {}, isEdit=False):
        self.primaryExec = True
        self.mapJournalInfoTransfer = mapJournalInfoTransfer
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
        if (form != u'090' and QtGui.qApp.userHasRight(urAccessF003planner)) or (form == u'090' and QtGui.qApp.userHasAnyRight([urAccessF090planner,])):
            dlg = CPreF003Dialog(self, self.contractTariffCache)
            try:
                dlg.setBegDateEvent(eventSetDatetime.date() if isinstance(eventSetDatetime, QDateTime) else eventSetDatetime)
                dlg.prepare(clientId, eventTypeId, eventDate, self.personId, self.personSpecialityId, self.personTariffCategoryId, 
                            flagHospitalization, actionTypeIdValue, tissueTypeId, presentActionTypes = presentActionTypes, maxOccursLimitActionTypes = maxOccursLimitActionTypes)
                if dlg.diagnosticsTableIsNotEmpty() or dlg.actionsTableIsNotEmpty():
                    if not dlg.exec_():
                        return False
                return self._prepare(clientId, eventTypeId, orgId, personId, eventSetDatetime, eventDatetime, weekProfile,
                                     numDays, dlg.diagnostics(), dlg.actions(), dlg.disabledActionTypeIdList,
                                     externalId, assistantId, curatorId, actionTypeIdValue, valueProperties,
                                     relegateOrgId, relegatePersonId, diagnos, financeId, protocolQuoteId,
                                     actionByNewEvent, order, actionListToNewEvent, docNum, relegateInfo, plannedEndDate, isEdit)
            finally:
                dlg.deleteLater()
        else:
            presets = CPreF003DagnosticAndActionPresets(clientId, eventTypeId, eventDate, self.personSpecialityId, 
                                                        flagHospitalization, actionTypeIdValue, presentActionTypes = presentActionTypes, 
                                                        maxOccursLimitActionTypes = maxOccursLimitActionTypes)
            presets.setBegDateEvent(eventSetDatetime.date() if isinstance(eventSetDatetime, QDateTime) else eventSetDatetime)
            return self._prepare(clientId, eventTypeId, orgId, personId, eventSetDatetime, eventDatetime, weekProfile,
                                 numDays, presets.unconditionalDiagnosticList, presets.unconditionalActionList,
                                 presets.disabledActionTypeIdList, externalId, assistantId, curatorId,
                                 actionTypeIdValue, valueProperties, relegateOrgId, relegatePersonId, diagnos,
                                 financeId, protocolQuoteId, actionByNewEvent, order, actionListToNewEvent,
                                 docNum, relegateInfo, plannedEndDate, isEdit)


    def addActions(self, actionsList):
        for action in actionsList:
            record = action.getRecord()
            actionTypeId = forceRef(record.value('actionType_id'))
            for model in (self.tabStatus.modelAPActions,
                              self.tabDiagnostic.modelAPActions,
                              self.tabCure.modelAPActions,
                              self.tabMisc.modelAPActions):
                if actionTypeId in model.actionTypeIdList:
                    model.addRow(None, None, None, None, action)

    def setCmbResult(self, result):
        if result:
            self.cmbResult.setValue(result)

    def prepareActions(self, presetActions, disabledActions, actionTypeIdValue, valueProperties, diagnos,
                       financeId, protocolQuoteId, actionByNewEvent, docNum=None, relegateInfo=[], plannedEndDate=None):
        def addActionType(actionTypeId, amount, idListActionType, idListActionTypeIPH, actionFinance, idListActionTypeMoving, relegateInfo, plannedEndDate):
            db = QtGui.qApp.db
            currentDateTime = QDateTime.currentDateTime()
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
                        if relegateInfo:
                            # if u'Кем направлен' in action._actionType._propertiesByName:
                            #     action[u'Кем направлен'] =  forceString(QtGui.qApp.db.translate('Organisation', 'id', relegateInfo[3], 'fullName'))
                            if u'Номер направления' in action._actionType._propertiesByName:
                                action[u'Номер направления'] = relegateInfo[1]
                            elif u'№ направления' in action._actionType._propertiesByName:
                                action[u'№ направления'] = relegateInfo[1]
                            if u'Дата направления' in action._actionType._propertiesByName:
                                action[u'Дата направления'] = relegateInfo[2]
                            if u'Диагноз направителя' in action._actionType._propertiesByName:
                                action[u'Диагноз направителя'] = relegateInfo[5]
                        elif docNum:
                            action[u'Номер направления'] = docNum
                        if hasattr(self, 'emergencyInfo'):
                            if u'Доставлен по' in action._actionType._propertiesByName:
                                action[u'Доставлен по'] = u'экстренным показаниям'
                            if u'Кем доставлен' in action._actionType._propertiesByName:
                                action[u'Кем доставлен'] = u'СМП'
                            if u'Диагноз СМП' in action._actionType._propertiesByName and 'diagnosis' in self.emergencyInfo:
                                action[u'Диагноз СМП'] = self.emergencyInfo['diagnosis']
                            if u'Бригада СМП' in action._actionType._propertiesByName and 'team' in self.emergencyInfo:
                                action[u'Бригада СМП'] = self.emergencyInfo['team']
                            if u'Место вызова' in action._actionType._propertiesByName and 'callAddress' in self.emergencyInfo:
                                action[u'Место вызова'] = self.emergencyInfo['callAddress']
                            if u'Сигнальный лист СМП' in action._actionType._propertiesByName and 'callInfo' in self.emergencyInfo:
                                action[u'Сигнальный лист СМП'] = self.emergencyInfo['callInfo']
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
                            record.setValue('begDate', toVariant(currentDateTime))
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
                addActionType(actionTypeId, amount, idListActionType, idListActionTypeIPH, actionFinance, idListActionTypeMoving, relegateInfo, plannedEndDate)


    def setLeavedAction(self, actionTypeIdValue, params = {}):
        currentDateTime = params.get('ExecDateTime', QDateTime.currentDateTime())
        person = params.get('ExecPerson', None)
        result = params.get('ExecResult', None)
        hospitalBedId = None
        flatCode = [u'moving', u'received']
        db = QtGui.qApp.db
        tableActionType = db.table('ActionType')
        idListActionType = db.getIdList(tableActionType, [tableActionType['id']], [tableActionType['flatCode'].inlist(flatCode), tableActionType['deleted'].eq(0)])
        for model in (self.tabStatus.modelAPActions,
                      self.tabDiagnostic.modelAPActions,
                      self.tabCure.modelAPActions,
                      self.tabMisc.modelAPActions):
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
        if self.cmbContract.count() != 1:
            self.cmbContract.setFocus(Qt.OtherFocusReason)
        else:
            self.tblFinalDiagnostics.setFocus(Qt.OtherFocusReason)


    def newDiagnosticRecord(self, template):
        result = self.tblFinalDiagnostics.model().getEmptyRecord()
        return result


    def setRecord(self, record):
        self.primaryExec = True
        CEventEditDialog.setRecord(self, record)
        setDatetimeEditValue(self.edtBegDate, self.edtBegTime, record, 'setDate')
        setDatetimeEditValue(self.edtEndDate, self.edtEndTime, record, 'execDate')
        setRBComboBoxValue(self.cmbPerson,      record, 'execPerson_id')
#        setDateEditValue(self.edtNextDate,      record, 'nextEventDate')
        self.chkPrimary.setChecked(forceInt(record.value('isPrimary'))==1)
        self.setExternalId(forceString(record.value('externalId')))
        self.initOrder(forceString(getEventAvailableOrders(record.value('eventType_id'))), forceInt(record.value('order')))
        setRBComboBoxValue(self.cmbResult,      record, 'result_id')
        self.setPerson = forceRef(record.value('setPerson_id'))

        self._updateNoteByPrevEventId()
        self.tabNotes.setNotes(record)

        self.setPersonId(self.cmbPerson.value())
        setRBComboBoxValue(self.cmbContract, record, 'contract_id')
        self.loadDiagnostics(self.modelPreliminaryDiagnostics, self.itemId())
        self.loadDiagnostics(self.modelFinalDiagnostics, self.itemId())
        self.tabMedicalDiagnosis.load(self.itemId())
        self.tabFeed.setClientId(self.clientId)
        self.grpTempInvalid.pickupTempInvalid()
        self.grpAegrotat.pickupTempInvalid()
        self.grpDisability.pickupTempInvalid()
        self.grpVitalRestriction.pickupTempInvalid()
        self.updateMesMKB()
        self.tabMes.setRecord(record)
        self.loadActions()
        self.tabCash.load(self.itemId())
        self.tabFeed.setPatronId(self.tabNotes.cmbClientRelationConsents.value())
        self.tabFeed.setContractId(self.cmbContract.value())
        self.tabFeed.setFilterDiet(self.eventSetDateTime.date(), self.eventDate)
        self.tabFeed.load(self.itemId())
        iniExportEvent(self)
        self.on_cmbResult_currentIndexChanged()
        self.initFocus()
        self.setIsDirty(False)
        self.blankMovingIdList = []
        self.protectClosedEvent()
        self.primaryExec = False
        self.btnRelatedEventHighlight()
        self.setOrgStructAndPersonsInCmbPersons(self.eventTypeId)

    def setOrgStructAndPersonsInCmbPersons(self, eventTypeId):
        orgstructureListByEventtype = getOrgstructureListByEventtypeId(eventTypeId)
        personListByEventtype = getPersonListByEventtypeId(eventTypeId)
        self.cmbPerson.setOrgStructureList(orgstructureListByEventtype)
        self.cmbPerson.setPersonIdList(personListByEventtype)
        self.modelActionsSummary._cols[
            self.modelActionsSummary.getColIndex('person_id')].orgStructureIdList = orgstructureListByEventtype
        self.modelActionsSummary._cols[
            self.modelActionsSummary.getColIndex('person_id')].personIdList = personListByEventtype

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


    def btnNextActionSetFocus(self):
        modelFind = self.tabMisc.modelAPActions
        items = modelFind.items()
        for rowFind, item in enumerate(items):
            record, actionItem = item
            if record:
                actionTypeIdFind = forceRef(record.value('actionType_id'))
                actionTypeFind = CActionTypeCache.getById(actionTypeIdFind) if actionTypeIdFind else None
                if u'received' in actionTypeFind.flatCode.lower():
                    self.tabWidget.setCurrentIndex(6)
                    self.tabMisc.tblAPActions.setCurrentIndex(modelFind.index(rowFind, 0))
                    self.tabMisc.btnNextAction.setFocus(Qt.OtherFocusReason)
                    break


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
        CF003Dialog.defaultEventResultId = self.cmbResult.value()
#        CF003Dialog.defaultDiagnosticResultId = self.modelFinalDiagnostics.resultId()

        getRBComboBoxValue(self.cmbContract,    record, 'contract_id')
        getDatetimeEditValue(self.edtBegDate, self.edtBegTime, record, 'setDate', showTime)
        record.setValue('setPerson_id', self.setPerson)
        getDatetimeEditValue(self.edtEndDate, self.edtEndTime, record, 'execDate', showTime)
        getRBComboBoxValue(self.cmbPerson,      record, 'execPerson_id')
        getRBComboBoxValue(self.cmbResult,      record, 'result_id')
#        getDateEditValue(self.edtNextDate,      record, 'nextEventDate')
        record.setValue('isPrimary', toVariant(1 if self.chkPrimary.isChecked() else 2))
        record.setValue('order',  toVariant(self.cmbOrder.currentIndex()+1))
        if self.prolongateEvent:
            record.setValue('order', toVariant(5))
###  payStatus
        self.tabMes.getRecord(record)
        self.tabNotes.getNotes(record, self.eventTypeId)
        # Это хак: удаляем payStatus из записи
        result = type(record)(record) # copy record
        result.remove(result.indexOf('payStatus'))
        return result


    def saveInternals(self, eventId):
        self.saveDiagnostics(self.modelPreliminaryDiagnostics, eventId)
        self.saveDiagnostics(self.modelFinalDiagnostics, eventId)
        self.tabMedicalDiagnosis.save(eventId)
        self.tabMes.save(eventId)
        setAskedClassValueForDiagnosisManualSwitch(None)
        self.saveActions(eventId)
#        self.modelFeed.saveData(eventId)
        self.tabFeed.save(eventId)
        self.tabCash.save(eventId)
        self.saveBlankUsers(self.blankMovingIdList)
        self.saveMapJournalOfPerson(eventId)
        self.tabNotes.saveAttachedFiles(eventId)
        self.saveTrailerActions(eventId)


    def saveTrailerActions(self, eventId):
        if self.trailerActions:
            for action in self.trailerActions:
                prevActionId = self.trailerIdList.get(action.trailerIdx - 1, None)
                action.getRecord().setValue('prevAction_id', toVariant(prevActionId))
                action.save(eventId)


    def saveMapJournalOfPerson(self, masterId):
        if self.mapJournalOfPerson is not None:
            db = QtGui.qApp.db
            table = db.table('Event_JournalOfPerson')
            masterId = toVariant(masterId)
            masterIdFieldName = u'master_id'
            idFieldName = u'id'
            idList = []
            for idx, record in enumerate(self.mapJournalOfPerson):
                record.setValue(masterIdFieldName, masterId)
                outRecord = record
                id = db.insertOrUpdate(table, outRecord)
                record.setValue(idFieldName, toVariant(id))
                idList.append(id)

            filter = [table[masterIdFieldName].eq(masterId),
                      'NOT ('+table[idFieldName].inlist(idList)+')']
            db.deleteRecord(table, filter)


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
            item.setValue('TMNS',  toVariant(TNMS))
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
                group = u'Event.id, Action.id'
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
        titleF003 = self.setOrgStructureTitle()
        CEventEditDialog.setEventTypeId(self, eventTypeId, u'Ф.003', titleF003)
        self.tabCash.windowTitle = self.windowTitle()
        showTime = getEventShowTime(eventTypeId)
        self.getShowButtonAccount()
        self.getShowButtonTemperatureList()
        self.getShowButtonNomenclatureExpense()
        self.getShowButtonJobTickets()
        self.edtBegTime.setVisible(showTime)
        self.edtEndTime.setVisible(showTime)
        self.cmbResult.setTable('rbResult', True, 'eventPurpose_id=\'%d\'' % self.eventPurposeId)
        # self.cmbResult.setValue(CF003Dialog.defaultEventResultId)
        cols = self.modelFinalDiagnostics.cols()
        resultCol = cols[len(cols)-1]
        resultCol.filter = 'eventPurpose_id=\'%d\'' % self.eventPurposeId
        self.cmbContract.setEventTypeId(eventTypeId)
        customizePrintButton(self.btnPrint, self.eventContext if self.eventContext else 'F003')
#        if CF003Dialog.defaultDiagnosticResultId:
#            db = QtGui.qApp.db
#            table = db.table('rbDiagnosticResult')
#            record = db.getRecordEx(table, 'eventPurpose_id', 'id=%i'%CF003Dialog.defaultDiagnosticResultId)
#            purposeId = forceInt(record.value(0)) if record else None
#            if purposeId != self.eventPurposeId:
#                CF003Dialog.defaultDiagnosticResultId = None


    def resetActionTemplateCache(self):
        self.tabStatus.actionTemplateCache.reset()
        self.tabDiagnostic.actionTemplateCache.reset()
        self.tabCure.actionTemplateCache.reset()
        self.tabMisc.actionTemplateCache.reset()


    def checkDataEntered(self):
        result = CEventEditDialog.checkDataEntered(self)
        tabList = [self.tabStatus, self.tabDiagnostic, self.tabCure, self.tabMisc]
        self.blankMovingIdList = []
        mesRequired = getEventMesRequired(self.eventTypeId)
        result = result and (self.orgId != QtGui.qApp.currentOrgId() or self.cmbContract.value() or self.checkInputMessage(u'договор', False, self.cmbContract))
        result = result and (self.cmbPerson.value() or self.checkInputMessage(u'врача', False, self.cmbPerson))
        result = result and self.checkExecPersonSpeciality(self.cmbPerson.value(), self.cmbPerson)
        showTime = getEventShowTime(self.eventTypeId)
        if showTime:
            begDate = QDateTime(self.edtBegDate.date(), self.edtBegTime.time())
            endDate = QDateTime(self.edtEndDate.date(), self.edtEndTime.time())
        else:
            begDate = self.edtBegDate.date()
            endDate = self.edtEndDate.date()
        endDateCheck = self.edtEndDate.date()
        result = result and (not ((showTime and not begDate.date()) or not begDate) or self.checkInputMessage(u'дату назначения', False, self.edtBegDate))
#        result = result and (endDate or self.checkInputMessage(u'дату выполнения', False, self.edtEndDate))
        result = result and (not endDateCheck or self.cmbResult.value() or self.checkInputMessage(u'результат', False, self.cmbResult))
        result = result and (not endDateCheck or self.checkEventResult())
        if (showTime and not endDate.date()) or not endDate:
            result = result and self.checkDiagnosticsPersonSpeciality() 
#            maxEndDate = self.getMaxEndDateByVisits()
#            if maxEndDate:
#                if QtGui.QMessageBox.question(self,
#                                    u'Внимание!',
#                                    u'Дата выполнения обращения не указана.\nУстановить дату завершения по максимальной дате посещений',
#                                    QtGui.QMessageBox.No|QtGui.QMessageBox.Yes,
#                                    QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
#                    self.edtEndDate.setDate(maxEndDate)
#                    endDate = maxEndDate
        else:
            if QtGui.qApp.isCheckEventJournalOfPerson():
                result = result and self.checkEventJournalOfPerson(begDate, endDate)
            result = result and self.checkActionDataEntered(begDate, QDateTime(), endDate, self.tabToken, self.edtBegDate, None, self.edtEndDate)
            result = result and self.checkDateActionsFeed(self.tabFeed.modelClientFeed, u'countClientToFeeds', u'Количество дней питания пациента = %s в действии %s не совпадает с количеством дней питания = %s на вкладке "Питание пациента"!')
            result = result and self.checkDateActionsFeed(self.tabFeed.modelPatronFeed, u'countPatronToFeeds', u'Количество дней питания лица по уходу = %s в действии %s не совпадает с количеством дней питания = %s на вкладке "Питание лица по уходу"!')
            result = result and self.checkEventDate(begDate, endDate, None, self.tabToken, None, self.edtEndDate, True)
            minDuration,  maxDuration = getEventDurationRange(self.eventTypeId)
            if minDuration<=maxDuration:
                result = result and (begDate.daysTo(endDate)+1>=minDuration or self.checkValueMessage(u'Длительность должна быть не менее %s'%formatNum(minDuration, (u'дня', u'дней', u'дней')), False, self.edtEndDate))
                result = result and (maxDuration==0 or begDate.daysTo(endDate)+1<=maxDuration or self.checkValueMessage(u'Длительность должна быть не более %s'%formatNum(maxDuration, (u'дня', u'дней', u'дней')), False, self.edtEndDate))
            result = result and (len(self.modelFinalDiagnostics.items())>0 or self.checkInputMessage(u'диагноз', False, self.tblFinalDiagnostics))
            result = result and self.checkDiagnosticsType(self.modelFinalDiagnostics)
            if mesRequired:
                result = result and self.tabMes.checkMesAndSpecification()
                result = result and (self.tabMes.chechMesDuration() or self.checkValueMessage(u'Длительность события должна попадать в интервал минимальной и максимальной длительности по требованию к МЭС', True, self.edtBegDate))
                result = result and self.checkDiagnosticsMKBForMes(self.tblFinalDiagnostics, self.tabMes.cmbMes.value())
            result = result and self.checkDiagnosticsDataEntered(endDate)
        result = result and self.checkExecPersonSpeciality(self.cmbPerson.value(), self.cmbPerson)
        result = result and self.checkDiagnosticsPersonSpeciality()
        result = result and self.checkActionsDateEnteredActuality(begDate, endDate, tabList)
        result = result and self.checkActionsDataEntered(begDate, endDate)
        result = result and self.checkOfPeriodFeeds(begDate, endDate, showTime)
        result = result and self.checkDeposit(True)
        result = result and (self.checkCorrectlyEnteredPersons(self.cmbPerson
            ) if not QtGui.qApp.checkGlobalPreference('23:checkChosenPerson',
                                                      u'не выполнять') else True)
        result = result and self.tabCash.checkDataLocalContract()
        result = result and self.checkSerialNumberEntered()
        result = result and self.checkTabNotesEventExternalId()
        self.valueForAllActionEndDate = None
        checkEpic, ConsFlatCodeList, needsListNazOnko = self.checkConsultationOrEpicris(tabList)
        if self.edtEndDate.date():
            checkRequireAction, ActionTypeIdList = self.checkRequireAction(self.eventTypeId, tabList, self.personSpecialityId, self.modelFinalDiagnostics.items())
            result = result and checkRequireAction
            if ActionTypeIdList:
                self.setActionConsbyIds(ActionTypeIdList)
            result = result and self.checkAndUpdateExpertise(self.edtEndDate.date(), self.cmbPerson.value())
            if CFinanceType.getCode(self.eventFinanceId) == CFinanceType.CMI and QtGui.qApp.defaultKLADR()[:2] == u'23':
                if u'List_covid' not in ConsFlatCodeList:
                    codeKSG, addList_covid = self.getConditionForList_covid(ConsFlatCodeList)
                    if addList_covid:
                        self.setActionCons([u'List_covid'])
                        result = result and self.checkValueMessage(u"Необходимо заполнить Л/С для лечения COVID-19", False, self.tabCure)
                    else:
                        result = result and codeKSG

                result = result and self.needOnkoDocs(ConsFlatCodeList, needsListNazOnko, tabList)
                result = result and self.checkNeedTNMS(self.tblFinalDiagnostics,
                                                       ['cTumor_id', 'cNodus_id', 'cMetastasis_id', 'cTNMphase_id'],
                                                       ['pTumor_id', 'pNodus_id', 'pMetastasis_id', 'pTNMphase_id'])
        result = result and self.selectNomenclatureAddedActions(tabList)
        if CFinanceType.getCode(self.eventFinanceId) == CFinanceType.CMI and QtGui.qApp.defaultKLADR()[:2] == u'23':
            result = result and self.checkOperationImplants(tabList, ConsFlatCodeList)
        if CFinanceType.getCode(self.eventFinanceId) == CFinanceType.CMI:
            result = result and self.checkDirection()
        if hasattr(self, 'tabMes'):
            result = result and self.tabMes.checkDataEntered()
        if hasattr(self, 'tabMisc') and hasattr(self, 'tabMes') and u'мэса нет' in unicode(self.tabMes.cmbMes.currentText()).lower():
            result = result and self.tabMisc.syncCSG()
        return result


    def getConditionForList_covid(self, ConsFlatCodeList):
        setDate = self.edtBegDate.date()
        execDate = self.edtEndDate.date()
        age = calcAgeInYears(forceDate(QtGui.qApp.db.translate('Client', 'id', self.clientId, 'birthDate')), setDate)
        eventtype = self.getEventTypeId()  # eventtype тип события

        codeKSG = self.getKRITValue(u'Ковид')
        mkb = self.getDiagnosisForOnko()

        if mkb and (setDate >= QDate(2018, 8, 1) or execDate >= QDate(2018, 8, 1)):
            mkb1, mkb2, mkb3 = mkb[0], mkb[1], mkb[2]
            if (mkb1 in (u'U07.1', u'U07.2') and not mkb3.startswith((u'O', u'Z34', u'Z35')) and isDispanserisation(
                eventtype) and age >= 18):
                if not codeKSG and u'KRIT' not in ConsFlatCodeList:
                    self.checkValueMessage(
                        u"Необходимо заполнить поле Ковид в Типе действия\n Дополнительные критерии лечения при определении КСГ",
                        False, self.tabMisc)
                    self.setActionCons([u'KRIT'])
                    return False, False
                elif codeKSG == 'stt5':
                    return True, False
                else:
                    return True, True
            else:
                return True, False
        return True, False

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

    def needOnkoDocs(self, ConsFlatCodeList, needsListNazOnko, tabList):
        mkb = self.getDiagnosisForOnko()
        if mkbIsOnko(mkb[0], mkb[2]):
            regionalCode = getEventAidTypeRegionalCode(self.eventTypeId)
            if regionalCode not in ['301', '302', '511', '522'] and u'ControlListOnko' not in ConsFlatCodeList:
                self.setActionCons([u'ControlListOnko'])
                self.checkValueMessage(u"Необходимо заполнить Контрольный лист учета при новообразовании", False, self.tabStatus)
                return False
            if regionalCode in ['11', '12', '41', '42', '51', '52']:
                if needsListNazOnko and u'list_naz_onko' not in ConsFlatCodeList:
                    if not self.checkValueMessage(u"Необходимо заполнить Лист назначений (онко)", True, self.tabCure):
                        self.setActionCons([u'list_naz_onko'])
                        return False
                if u'KRIT' not in ConsFlatCodeList and self.checkNeedKrit(tabList):
                    if not self.checkValueMessage(u"Необходимо заполнить Дополнительные критерии лечения при определении КСГ", True, self.tabMisc):
                        self.setActionCons([u'KRIT'])
                        return False
        return True

    def checkNeedKrit(self, tabList):
        def getAgeCategory():
            ageCategory = []
            if self.clientAge:
                if self.clientAge[0] <= 28:
                    ageCategory.append(1)
                elif self.clientAge[0] <= 90:
                    ageCategory.append(2)
                elif self.clientAge[3] < 1:
                    ageCategory.append(3)
                if self.clientAge[3] < 2:
                    ageCategory.append(4)
                if self.clientAge[3] < 18:
                    ageCategory.append(5)
                else:
                    ageCategory.append(6)
            return ageCategory

        if self.tabMes.cmbMes.code():
            try:
                db = QtGui.qApp.db
                date = self.eventDate
                if not date:
                    date = self.eventSetDateTime

                table69 = db.table('soc_spr69')
                cond = [
                    table69['ksgkusl'].eq(self.tabMes.cmbMes.code()),
                    table69['KRIT'].isNotNull(),
                    table69['datn'].le(date),
                    db.joinOr([table69['dato'].ge(date),
                               table69['dato'].isNull()]),
                ]

                # Основной диагноз
                MKB, _ = self.modelFinalDiagnostics.getFinalDiagnosisMKB()
                if MKB:
                    cond.append(
                        db.joinOr([
                            table69['mkb'].isNull(),
                            table69['mkb'].eq(MKB),
                            # table69['mkb'].eq('LEFT(%s.`mkb`, 3)' % table69.name),
                            "'{mkb}' BETWEEN LEFT({tableName}.`mkb`, 3) AND RIGHT({tableName}.`mkb`, 3)".format(
                                mkb=MKB[:3], tableName=table69.name())]
                        )
                    )
                else:
                    cond.append(table69['mkb'].isNull())
                # Сопутствующий диагноз
                MKBAcc = self.modelFinalDiagnostics.getAssociatedDiagnosisMKB()
                if MKBAcc:
                    cond.append(
                        db.joinOr([
                            table69['mkb2'].isNull(),
                            table69['mkb2'].eq(MKBAcc),
                            # table69['mkb'].eq('LEFT(%s.`mkb`, 3)' % table69.name),
                            "'{mkb}' BETWEEN LEFT({tableName}.`mkb2`, 3) AND RIGHT({tableName}.`mkb2`, 3)".format(
                                mkb=MKBAcc[:3], tableName=table69.name())]
                        )
                    )
                else:
                    cond.append(table69['mkb2'].isNull())

                # Пол пациента
                if self.clientSex:
                    cond.append(
                        db.joinOr([
                            table69['pol'].isNull(),
                            table69['pol'].eq("'%s'" % u'М' if self.clientSex == 1 else u'Ж'),]
                        )
                    )
                else:
                    cond.append(table69['pol'].isNull())

                # Длительность обращения
                # Никто не знает, как правильно это считать. В положении описание скудное. Но это не похоже на дни
                # длительность пребывания, койко(пациенто)-дней: 1 – пребывание до 3х дней включительно
                # Пока не учитывать
                # if self.lblDurationValue.text():
                #     cond.append(
                #         db.joinOr([
                #             table69['dlit'].isNull(),
                #             table69['dlit'].eq(self.lblDurationValue.text()),]
                #         )
                #     )
                # else:
                #     cond.append(table69['dlit'].isNull())

                # Возрастная категория пациента
                ageCategory = getAgeCategory()
                if ageCategory:
                    cond.append(
                        db.joinOr([
                            table69['age'].isNull(),
                            table69['age'].inlist(ageCategory), ]
                        )
                    )
                else:
                    cond.append(table69['age'].isNull())
                # Услуги
                serviceList = []
                fr = None
                for actionTab in tabList:
                    items = actionTab.tblAPActions.model().items()
                    for row, (record, action) in enumerate(items):
                        serviceId = action.getType().nomenclativeServiceId
                        #услуги
                        if serviceId:
                            serviceList.append(db.translate('rbService', 'id', serviceId, 'infis'))
                        #количество фракций
                        if action.actionType().id and action.actionType().flatCode == 'ControlListOnko':
                            a = action.getProperty(u'Количество фракций проведения лучевой терапии')
                            if a:
                                fr = a.getValue()

                if serviceList:
                    cond.append(db.joinOr([table69['kusl'].inlist(serviceList), table69['kusl'].isNull()]))
                else:
                    cond.append(table69['kusl'].isNull())

                # Количество фракций
                if fr:
                    cond.append(
                        db.joinOr([
                            table69['fr'].isNull(),
                            u'''regexp_substr(fr,'^fr\\\\K[0-9]{1,}') <= %d 
                                and regexp_substr(fr,'[-]\\\\K[0-9]{1,}') >= %d''' % (fr, fr),
                        ])
                    )
                else:
                    cond.append(table69['fr'].isNull())

                if db.getCount(table69, table69['ksgkusl'], cond):
                    return True
            except Exception:
                QtGui.qApp.logCurrentException()
        return False


    def checkOperationImplants(self, tabList, ConsFlatCodeList):
        if getEventAidTypeRegionalCode(self.eventTypeId) not in ['11', '12', '41', '42', '51', '52']:
            return True
        db = QtGui.qApp.db
        if not self.V036map:
            tableV36 = db.table('soc_V036')
            tableService = db.table('rbService')
            table = tableV36.leftJoin(tableService, tableService['infis'].eq(tableV36['serviceCode']))
            date = self.eventDate
            if not date:
                date = self.eventSetDateTime
            cond = [tableV36['begDate'].le(date),
                    db.joinOr([tableV36['endDate'].ge(date),
                               tableV36['endDate'].isNull()])]
            cols = [tableService['id'], tableV36['parameter']]
            records = db.getRecordList(table, cols=cols, where=cond)
            for record in records:
                serviceId = forceRef(record.value('id'))
                parameter = forceInt(record.value('parameter'))
                if parameter in [1, 3]:
                    self.V036map[serviceId] = parameter

        result = True

        for actionTab in tabList:
            model = actionTab.tblAPActions.model()
            items = model.items()
            for row, (record, action) in enumerate(items):
                serviceId = action.getType().nomenclativeServiceId
                if serviceId in self.V036map:
                    if u'Code_MDV' not in ConsFlatCodeList:
                        self.setActionCons([u'Code_MDV'])
                        self.checkValueMessage(u"Необходимо заполнить Сведения об имплантированных изделиях", False, self.tabCure)
                        return False
        return result


    def checkDateActionsFeed(self, modelFeed, flatCode, message, column = 0):
        tabList = self.getActionsTabsList()
        for actionTab in tabList:
            model = actionTab.tblAPActions.model()
            for row, (record, action) in enumerate(model.items()):
                if action and action._actionType.id:
                    actionTypeItem = action.getType()
                    if actionTypeItem and flatCode.lower() in actionTypeItem.flatCode.lower():
                        countActionFeeds = forceInt(record.value('amount'))
                        countFeeds = len(modelFeed.dates)-1
                        if countActionFeeds != countFeeds:
                            return self.checkValueMessage(message % (forceString(countActionFeeds), actionTypeItem.code, forceString(countFeeds)), True, actionTab.tblAPActions, row, column)
        return True


    def checkEventJournalOfPerson(self, begDate, endDate):
        db = QtGui.qApp.db
        tableEJOP = db.table('Event_JournalOfPerson')
        cond = [tableEJOP['deleted'].eq(0),
                tableEJOP['master_id'].eq(self.itemId())
                ]
        if begDate:
            cond.append(tableEJOP['setDate'].ge(begDate))
        if endDate:
            cond.append(tableEJOP['setDate'].le(endDate))
        record = db.getRecordEx(tableEJOP, [tableEJOP['execPerson_id']], cond, order = u'Event_JournalOfPerson.setDate DESC')
        self.execPersonId = forceRef(record.value('execPerson_id')) if record else None
        if self.execPersonId:
            personId = self.cmbPerson.value()
            if personId != self.execPersonId:
                QtGui.QMessageBox.warning(self,
                                           u'Внимание!',
                                           u'''Ответственный врач '%s' не соответствует врачу '%s' из Журнала назначения лечащего врача!''' % (forceString(QtGui.qApp.db.translate('vrbPersonWithSpeciality', 'id', personId, 'name')),
                                                                                                                                      forceString(QtGui.qApp.db.translate('vrbPersonWithSpeciality', 'id', self.execPersonId, 'name'))),
                                           QtGui.QMessageBox.Cancel,
                                           QtGui.QMessageBox.Cancel)
                self.setFocusToWidget(self.cmbPerson)
                return False
        return True


#    def checkActionLeavedEndDate(self, tblWidget, row, column, widgetEndDate, nameActionType, actionEndDate, actionEndTime, eventEndDate):
#        result = True
#        if not actionEndDate:
#            strNameActionType = u''
#            if len(nameActionType) > 0:
#                strNameActionType = u': ' + nameActionType
#            result = self.checkValueMessage(u'Должна быть указана дата выполнения действия%s' % (strNameActionType), True, tblWidget, row, column, widgetEndDate)
#        else:
#            if not eventEndDate and actionEndDate:
#                if not self.checkValueMessage(u'Установить дату события по дате законченного действия "выписка" %s?' % (forceString(actionEndDate)), True, tblWidget, row, column, widgetEndDate):
#                    self.edtEndDate.setDate(actionEndDate)
#                    self.edtEndTime.setTime(actionEndTime)
#        return result

    
    def checkDiagnosticsPersonSpeciality(self):
        result = True
        result = result and self.checkPersonSpecialityDiagnostics(self.modelPreliminaryDiagnostics, self.tblPreliminaryDiagnostics)
        result = result and self.checkPersonSpecialityDiagnostics(self.modelFinalDiagnostics, self.tblFinalDiagnostics)
        return result
    

    def checkDiagnosticsDataEntered(self, endDate):
        result = True
        result = result and self.checkDiagnostics(self.modelPreliminaryDiagnostics, self.tblPreliminaryDiagnostics, None, endDate)
        result = result and self.checkDiagnostics(self.modelFinalDiagnostics, self.tblFinalDiagnostics, self.cmbPerson.value(), endDate)
        result = result and self.checkDiagnosisType(self.modelFinalDiagnostics, self.tblFinalDiagnostics)
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
                # result = self.checkRequiresFillingDispanser(result, table, record, row, MKB)
        if result and endDate and table == self.tblFinalDiagnostics:
            resultId = forceRef(record.value('result_id'))
            result = resultId or self.checkInputMessage(u'Необходимо указать результат', False, self.tblFinalDiagnostics, row, record.indexOf('result_id'))
        if result and not forceRef(record.value('person_id')):
            result = result and self.checkValueMessage(u'Необходимо указать врача установившего диагноз', False, self.tblFinalDiagnostics, row, record.indexOf('person_id'))
        result = result and self.checkPersonSpeciality(record, row, self.tblFinalDiagnostics)
        result = result and self.checkPeriodResultHealthGroup(record, row, self.tblFinalDiagnostics)
        return result


    def checkActionsDataEntered(self, eventDirectionDate, eventEndDate):
        eventId = self.itemId()
        tabList = self.getActionsTabsList()
        actionsBeyondEvent = getEventEnableActionsBeyondEvent(self.eventTypeId)
        if hasattr(self, 'hasReferralLisLab'):
            del self.hasReferralLisLab
        for actionTab in tabList:
            model = actionTab.tblAPActions.model()
            for row, (record, action) in enumerate(model.items()):
                if action and action._actionType.id:
                    actionTypeItem = action.getType()
                    nameActionType = action._actionType.name  # название типа действия
                    status = forceInt(record.value('status'))
                    actionShowTime = action._actionType.showTime
                    forceDateOrDateTime = forceDateTime if actionShowTime else forceDate
                    directionDate = forceDateOrDateTime(record.value('directionDate'))
                    begDate = forceDateOrDateTime(record.value('begDate'))
                    endDate = forceDateOrDateTime(record.value('endDate'))
                    actionId = forceRef(record.value('id'))
                    if not self.checkBegDateAction(row, record, action, actionTab.tblAPActions, actionTab.edtAPBegDate):
                        return False
                    
                    if actionTypeItem and actionTypeItem.flatCode == u'referralLisLab':
                        self.hasReferralLisLab = True
                    if not self.checkActionMKB(row, record, action,
                                                      actionTab.tblAPActions, actionTab.cmbAPMorphologyMKB):
                        return False
                    if not self.checkSetPerson(row, record, action, actionTab.tblAPActions, actionTab.cmbAPSetPerson):
                        return False
                    if not self.checkExecPerson(row, record, action,
                                                      actionTab.tblAPActions, actionTab.cmbAPPerson):
                        return False    
                    if actionTypeItem and (u'received' in actionTypeItem.flatCode.lower()
                                           or u'moving' in actionTypeItem.flatCode.lower()
                                           or u'leaved' in actionTypeItem.flatCode.lower()):
                        # проверка заполнения МКБ в действии Поступление (по ОМС) для КК
                        if QtGui.qApp.provinceKLADR()[:2] == u'23' and u'received' in actionTypeItem.flatCode.lower():
                            checkMKBreceivedOMS = QtGui.qApp.getStrictCheckMKBreceivedOMS()
                            if checkMKBreceivedOMS:
                                if self.eventFinanceId == CFinanceType.CMI and not forceString(record.value('MKB')) and not self.checkValueMessage(u'Для действия Поступление не указан код МКБ.', checkMKBreceivedOMS == 1, actionTab.tblAPActions, row, 0, actionTab.cmbAPMKB):
                                    return False

                        # проверка заполнения поля доставлен СМП и Бригада смп в действии Поступление для КК
                        if QtGui.qApp.provinceKLADR()[:2] == u'23' and u'received' in actionTypeItem.flatCode.lower():
                            checkReceivedControlSMP = QtGui.qApp.getStrictCheckReceivedControlSMP()
                            if checkReceivedControlSMP:
                                if action.hasProperty(u'Кем доставлен'):
                                    prop = action.getProperty(u'Кем доставлен').getValue()
                                    if prop and (u'СМП' in prop or u'скорая' in prop):
                                        if not action.getProperty(u'Бригада СМП').getValue() \
                                                and not self.checkValueMessage(u'Для пациентов, доставляемых СМП необходимо заполнить свойство "Бригада СМП" при регистрации поступления.', checkReceivedControlSMP == 1, actionTab.tblAPActions, row):
                                            return False

                        begDateTime = forceDateTime(record.value('begDate'))
                        endDateTime = forceDateTime(record.value('endDate'))
                        if  eventEndDate and u'received' in actionTypeItem.flatCode.lower():
                            isControlActionReceivedBegDate = QtGui.qApp.isControlActionReceivedBegDate()
                            if isControlActionReceivedBegDate:
                                showTime = getEventShowTime(self.eventTypeId) and actionShowTime
                                setDate = toDateTimeWithoutSeconds(eventDirectionDate if showTime else (eventDirectionDate.date() if isinstance(eventDirectionDate, QDateTime) else eventDirectionDate))
                                actionBegDate = toDateTimeWithoutSeconds(begDateTime if showTime else (begDateTime.date() if isinstance(begDateTime, QDateTime) else begDateTime))
                                if setDate != actionBegDate:
                                    if isControlActionReceivedBegDate == 1:
                                        message = u'Дата начала случая обслуживания %s не совпадает с датой начала действия Поступление %s. Исправить?'%(forceString(setDate), forceString(actionBegDate))
                                        skippable = True
                                    else:
                                        message = u'Дата начала случая обслуживания %s не совпадает с датой начала действия Поступление %s. Необходимо исправить.'%(forceString(setDate), forceString(actionBegDate))
                                        skippable = False
                                    if not self.checkValueMessage(message, skippable, actionTab.tblAPActions, row, 0, actionTab.edtAPBegDate):
                                        return False
                        if not self.checkDateActionsMoving(model, begDateTime, endDateTime, actionTab.tblAPActions, row, 0, actionTab.edtAPBegDate):
                            return False
                        if u'moving' in actionTypeItem.flatCode.lower():
                            for i in xrange(len(action._properties)):
                                if action._properties[i]._type.typeName.lower() == (u'HospitalBed').lower():
                                    if not self.checkMovingBeds(self.clientId, eventId, actionId, forceDateTime(action._record.value('begDate')), forceDateTime(action._record.value('endDate')), actionTab.tblAPActions, row, 0, actionTab.edtAPBegDate):
                                        return False
                        if eventEndDate and u'leaved' in actionTypeItem.flatCode.lower():
                            if not self.checkLeavedEndDate(eventEndDate, row, action, actionTab.tblAPActions, actionTab.edtAPEndDate):
                                return False
                    if not self.checkActionDataEntered(directionDate, begDate, endDate, actionTab.tblAPActions, actionTab.edtAPDirectionDate, actionTab.edtAPBegDate, actionTab.edtAPEndDate, row, 0):
                        self.getActionList(tabList, actionTypeItem)
                        return False
                    if not self.checkEventDate(directionDate, endDate, None, actionTab.tblAPActions, None, actionTab.edtAPEndDate, False, row, 0, enableActionsBeyondEvent=actionsBeyondEvent):
                        self.getActionList(tabList, actionTypeItem)
                        return False
                    if not self.checkEventActionDateEntered(eventDirectionDate, eventEndDate, status, directionDate, begDate, endDate, actionTab.tblAPActions, actionTab.edtAPEndDate, actionTab.edtAPBegDate, row, 0, nameActionType, actionShowTime=actionShowTime, enableActionsBeyondEvent=actionsBeyondEvent):
                        self.getActionList(tabList, actionTypeItem)
                        return False
                    if not self.checkActionProperties(actionTab, action, actionTab.tblAPProps, row):
                        return False
                    if not self.checkExistsActionsForCurrentDay(row, record, action, actionTab):
                        return False
                    if not self.checkActionMorphology(row, record, action,
                                                      actionTab.tblAPActions, actionTab.cmbAPMorphologyMKB):
                        return False
                    if not self.checkPlannedEndDate(row, record, action,
                                                      actionTab.tblAPActions, actionTab.edtAPPlannedEndDate):
                        return False
#                    if u'leaved' in action._actionType.flatCode.lower():
#                        if not self.checkActionLeavedEndDate(actionTab.tblAPActions, row, 0, actionTab.edtAPEndDate, nameActionType, endDate, endTime, eventEndDate):
#                            return False
        return True


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


    def checkDirection(self):
        regionalCode = getEventAidTypeRegionalCode(self.eventTypeId)
        if regionalCode in ['11', '12', '301', '302', '41', '42', '411', '422', '43', '51', '52', '511', '522']:
            order = self.cmbOrder.currentIndex()
            if order == 0:
                message = u'Необходимо заполнить поле(я):\n '
                check = True
                if not self.tabNotes.cmbRelegateOrg.value():
                    message += u'Направитель\n '
                    check = False
                if not self.tabNotes.edtEventSrcDate.date():
                    message += u'Дата направления\n '
                    check = False
                if not self.tabNotes.edtEventSrcNumber.text():
                    message += u'Номер направления'
                    check = False
                if not check:
                    return self.checkValueMessage(message, False, self.tabNotes)
                else:
                    return True
            # elif order == 1:
            #     if self.tabNotes.cmbRelegateOrg.value() or self.tabNotes.edtEventSrcDate.date() or self.tabNotes.edtEventSrcNumber.text():
            #         return self.checkValueMessage(u"Необходимо удалить данные о направителе и направлении", False, self.tabNotes)
            #     else:
            #         return True
            else:
                return True
        else:
            return True


    def getDiagnosisTypeId(self, dt):
        return forceRef(QtGui.qApp.db.translate('rbDiagnosisType', 'code', '2' if dt else '9', 'id'))


    def getEventInfo(self, context):
        result = CEventEditDialog.getEventInfo(self, context, CTeethEventInfo)
        # ручная инициализация свойств
        result._isPrimary = forceInt(toVariant(1 if self.chkPrimary.isChecked() else 2))
        # ручная инициализация таблиц
        result._actions = CActionInfoProxyList(context,
                [self.tabStatus.modelAPActions, self.tabDiagnostic.modelAPActions, self.tabCure.modelAPActions, self.tabMisc.modelAPActions, self.tabMedicalDiagnosis.tblEventMedicalDiagnosis.model()],
                result)
        result.initActions()  # инициализируем _action_stomat и _action_parodent
        result._diagnosises = CDiagnosticInfoProxyList(context, [self.modelPreliminaryDiagnostics, self.modelFinalDiagnostics])
        return result


    def updateDuration(self):
        if not getEventShowTime(self.eventTypeId) or not QtGui.qApp.isDurationTakingIntoMedicalDays():
            self.lblDurationValue.setText(updateDurationEvent(self.edtBegDate.date(), self.edtEndDate.date(), self.eventTypeId))
        else:
            self.lblDurationValue.setText(updateDurationTakingIntoMedicalDaysEvent(QDateTime(self.edtBegDate.date(), self.edtBegTime.time()), QDateTime(self.edtEndDate.date(), self.edtEndTime.time()), self.eventTypeId))
        
        def getWeekProfile(index):
            return {0: wpFiveDays,
             1: wpSixDays,
             2: wpSevenDays}.get(index, wpSevenDays)  
             
        begDate = self.edtBegDate.date()
        endDate = self.edtEndDate.date()
        if not endDate:
            endDate = QDate.currentDate()
        text = '-'
        if begDate:
            if QtGui.qApp.defaultKLADR()[:2] == u'23':
                eventWeekProfile = getWeekProfile(forceInt(QtGui.qApp.db.getRecord('EventType', 'weekProfileCode', self.eventTypeId).value('weekProfileCode')))
                duration = getEventDuration(begDate, endDate, eventWeekProfile, self.eventTypeId)
            else:
                duration = begDate.daysTo(endDate)+getEventDurationRule(self.eventTypeId)
            if duration > 0:
                text = str(duration)
        self.lblDurationValue.setText(text)


    def updateMesMKB(self):
        MKB, MKBEx = self.getFinalDiagnosisMKB()
        associatedMKB = self.getAssociatedDiagnosisMKB()
        complicationMKB = self.getComplicationDiagnosisMKB()
        self.tabMes.setMKB(MKB)
        self.tabMes.setMKBEx(MKBEx)
        self.tabMes.setAssociatedMKB(associatedMKB)
        self.tabMes.setComplicationMKB(complicationMKB)
        for actionTab in self.getActionsTabsList():
            model = actionTab.modelAPActions
            for record, action in model.items():
                actionTypeId = forceRef(record.value('actionType_id'))
                actionType = CActionTypeCache.getById(actionTypeId) if actionTypeId else None
                if actionType.flatCode == 'KRIT':
                    for prop in action._properties:
                        if prop.type().valueType.name == u'Доп. классиф. критерий':
                            prop.type().valueType.filterByMKB(MKB)


    def setContractId(self, contractId):
        if self.contractId != contractId:
            CEventEditDialog.setContractId(self, contractId)
            cols = self.tblActions.model().cols()
            if cols:
                cols[0].setContractId(contractId)
            self.tabCash.modelAccActions.setContractId(contractId)
            self.tabCash.updatePaymentsSum()
    
    
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

# # #
    @pyqtSignature('int')
    def on_tabWidget_currentChanged(self, index):
        widget = self.tabWidget.widget(index)
        if widget is not None:
            focusProxy = widget.focusProxy()
            if focusProxy:
                focusProxy.setFocus(Qt.OtherFocusReason)
        self.btnPrintMedicalDiagnosisEnabled(index)
        if index in [3,4,5,6]:  # action page
            [self.tabStatus, self.tabCure, self.tabDiagnostic, self.tabMisc][index - 3].onActionCurrentChanged()
        if index == 7: # amb card page
            self.tabAmbCard.resetWidgets()
        if index == 2 and self.eventTypeId:
            self.tabMes.setMESServiceTemplate(self.eventTypeId)
            criteriaList = []
            fractions = None
            for actionTab in self.getActionsTabsList():
                model = actionTab.modelAPActions
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
                            if prop.type().shortName == u'K_FR':
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
        self.cmbPerson.setBegDate(date)
        self.setPersonDate(self.eventSetDateTime.date())
        self.tabStatus.setEndDate(self.eventSetDateTime.date())
        self.tabDiagnostic.setEndDate(self.eventSetDateTime.date())
        self.tabCure.setEndDate(self.eventSetDateTime.date())
        self.tabMisc.setEndDate(self.eventSetDateTime.date())
        self.tabMes.setEventBegDate(self.eventSetDateTime.date())
        self.updateDuration()
        self.emitUpdateActionsAmount()
        if not self.primaryExec:
            if QtGui.qApp.isCheckEventJournalOfPerson():
                self.updateExecPerson()
            self.tabFeed.setFilterDiet(self.eventSetDateTime.date(), self.eventDate)


    @pyqtSignature('QTime')
    def on_edtBegTime_timeChanged(self, time):
        self.eventSetDateTime.setTime(time)
        self.updateDuration()
        self.emitUpdateActionsAmount()
        if not self.primaryExec and QtGui.qApp.isCheckEventJournalOfPerson():
            self.updateExecPerson()


    @pyqtSignature('QDate')
    def on_edtEndDate_dateChanged(self, date):
        self.eventDate = QDate(date)
        self.cmbPerson.setEndDate(date)
        self.cmbContract.setDate(self.getDateForContract())
        self.updateDuration()
        self.emitUpdateActionsAmount()
        self.setEnabledChkCloseEvent(self.eventDate)
        self.tabMes.setExecDate(self.eventDate)
        if getEventShowTime(self.eventTypeId):
            time = QTime.currentTime() if date else QTime()
            self.edtEndTime.setTime(time)
        else:
            if not self.primaryExec and QtGui.qApp.isCheckEventJournalOfPerson():
                self.updateExecPerson()
        if not self.primaryExec:
            self.tabFeed.setFilterDiet(self.eventSetDateTime.date(), self.eventDate)


    @pyqtSignature('QTime')
    def on_edtEndTime_timeChanged(self, time):
        #self.eventDate.setTime(time)
        self.updateDuration()
        self.emitUpdateActionsAmount()
        if not self.primaryExec and QtGui.qApp.isCheckEventJournalOfPerson():
            self.updateExecPerson()


    @pyqtSignature('')
    def on_cmbContract_valueChanged(self):
        contractId = self.cmbContract.value()
        self.setContractId(contractId)
        cols = self.tblActions.model().cols()
        if cols:
            cols[0].setContractId(contractId)
        self.tabFeed.setContractId(self.cmbContract.value())


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
        if QtGui.qApp.isCheckEventJournalOfPerson():
            if not self.primaryExec and not self.mapJournalInfoTransfer:
                self.getExecPersonId()
                if self.execPersonId:
                    personId = self.cmbPerson.value()
                    if personId and personId != self.execPersonId:
                        if QtGui.qApp.userHasRight(urEditEventJournalOfPerson):
                            res = QtGui.QMessageBox.warning(self,
                                                       u'Внимание!',
                                                       u'''Ответственный врач '%s' не соответствует Журналу назначения лечащего врача.\nВнести изменения в Журнал назначения лечащего врача?''' % (forceString(QtGui.qApp.db.translate('vrbPersonWithSpeciality', 'id', personId, 'name'))),
                                                       QtGui.QMessageBox.Ok|QtGui.QMessageBox.Cancel,
                                                       QtGui.QMessageBox.Cancel)
                            if res == QtGui.QMessageBox.Ok:
                                dialog = CExecPersonListEditorDialog(self, self.itemId())
                                try:
                                    if not self.itemId() or self.mapJournalOfPerson:
                                        dialog.setJournalOfPersonData(self.mapJournalOfPerson)
                                        dialog.setExecPersonInfo(personId, self.eventDate, QtGui.qApp.userId)
                                        if dialog.exec_():
                                            self.mapJournalOfPerson = dialog.getJournalOfPersonData()
                                    else:
                                        dialog.setExecPersonInfo(personId, self.eventDate, QtGui.qApp.userId)
                                        dialog.exec_()
                                        self.mapJournalOfPerson = dialog.getJournalOfPersonData()
                                finally:
                                    dialog.deleteLater()
                            else:
                                res = QtGui.QMessageBox.warning(self,
                                                           u'Внимание!',
                                                           u'''Смена ответственного врача.\nОтветственный '%s' будет заменен на '%s'.\nВы подтверждаете изменения?''' % (forceString(QtGui.qApp.db.translate('vrbPersonWithSpeciality', 'id', personId, 'name')),
                                                                                                                                                                         forceString(QtGui.qApp.db.translate('vrbPersonWithSpeciality', 'id', self.execPersonId, 'name'))),
                                                           QtGui.QMessageBox.Ok|QtGui.QMessageBox.Cancel,
                                                           QtGui.QMessageBox.Cancel)
                                if res == QtGui.QMessageBox.Ok:
                                    self.cmbPerson.setValue(self.execPersonId)
                        else:
                            res = QtGui.QMessageBox.warning(self,
                                                       u'Внимание!',
                                                       u'''Смена ответственного врача.\nОтветственный '%s' будет заменен на '%s'.\nВы подтверждаете изменения?''' % (forceString(QtGui.qApp.db.translate('vrbPersonWithSpeciality', 'id', personId, 'name')),
                                                                                                                                                                     forceString(QtGui.qApp.db.translate('vrbPersonWithSpeciality', 'id', self.execPersonId, 'name'))),
                                                       QtGui.QMessageBox.Ok|QtGui.QMessageBox.Cancel,
                                                       QtGui.QMessageBox.Cancel)
                            if res == QtGui.QMessageBox.Ok:
                                self.cmbPerson.setValue(self.execPersonId)
            elif self.mapJournalInfoTransfer and QtGui.qApp.userHasRight(urEditEventJournalOfPerson):
                self.getExecPersonId()
                dialog = CExecPersonListEditorDialog(self, self.itemId())
                try:
                    personId = self.mapJournalInfoTransfer[0]
                    eventDate = self.mapJournalInfoTransfer[1]
                    setPersonId = self.mapJournalInfoTransfer[2]
                    if not self.itemId() or self.mapJournalOfPerson:
                        dialog.setJournalOfPersonData(self.mapJournalOfPerson)
                        dialog.setExecPersonInfo(personId, eventDate, setPersonId if setPersonId else QtGui.qApp.userId)
                        self.mapJournalOfPerson = dialog.getJournalOfPersonData()
                    else:
                        dialog.setExecPersonInfo(personId, eventDate, setPersonId if setPersonId else QtGui.qApp.userId)
                        self.mapJournalOfPerson = dialog.getJournalOfPersonData()
                finally:
                    dialog.deleteLater()
                    self.mapJournalInfoTransfer = []
#        self.grpTempInvalid.pickupTempInvalid()
#        self.grpAegrotat.pickupTempInvalid()
#        self.grpDisability.pickupTempInvalid()
#        self.grpVitalRestriction.pickupTempInvalid()


    def on_modelPreliminaryDiagnostics_diagnosisChanged(self):
        self.updateMesMKB()


    def on_modelFinalDiagnostics_diagnosisChanged(self):
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
            CF003Dialog.defaultDiagnosticResultId = self.modelFinalDiagnostics.resultId()
            defaultResultId = getEventResultId(CF003Dialog.defaultDiagnosticResultId, self.eventPurposeId)
            if defaultResultId and isDefaultResultIdValid(defaultResultId, self.eventPurposeId, resultCond):
                self.cmbResult.setValue(defaultResultId)
            else:
                self.cmbResult.setValue(currentValue)
        else:
            self.cmbResult.setValue(currentValue)


    @pyqtSignature('')
    def on_actDiagnosticsAddAccomp_triggered(self):
        currentRow = self.tblFinalDiagnostics.currentIndex().row()
        if currentRow >= 0:
            currentRecord = self.modelFinalDiagnostics.items()[currentRow]
            newRecord = self.modelFinalDiagnostics.getEmptyRecord()
            newRecord.setValue('diagnosisType', QVariant(CF003Dialog.dfAccomp))
            newRecord.setValue('speciality_id', currentRecord.value('speciality_id'))
            newRecord.setValue('healthGroup_id', currentRecord.value('healthGroup_id'))
            self.modelFinalDiagnostics.insertRecord(currentRow+1, newRecord)
            self.tblFinalDiagnostics.setCurrentIndex(self.modelFinalDiagnostics.index(currentRow+1, newRecord.indexOf('MKB')))



    @pyqtSignature('QModelIndex')
    def on_tblActions_doubleClicked(self, index):
        row = index.row()
        column = index.column()
        if 0 <= row < len(self.modelActionsSummary.items()):
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

    @pyqtSignature('')
    def on_btnExecPersonList_clicked(self):
        self.execPersonId = None
        eventId = self.itemId()
        dialog = CExecPersonListEditorDialog(self, eventId)
        try:
            if not eventId or self.mapJournalOfPerson:
                dialog.setJournalOfPersonData(self.mapJournalOfPerson)
                if dialog.exec_():
                    self.mapJournalOfPerson = dialog.getJournalOfPersonData()
                    self.updateExecPerson()
            else:
                if dialog.exec_():
                    self.mapJournalOfPerson = dialog.getJournalOfPersonData()
                    self.updateExecPerson()
        finally:
            dialog.deleteLater()

    def getExecPersonId(self):
        if not self.primaryExec and QtGui.qApp.isCheckEventJournalOfPerson():
            eventId = self.itemId()
            if eventId:
                record = None
                db = QtGui.qApp.db
                tableEJOP = db.table('Event_JournalOfPerson')
                cond = [tableEJOP['deleted'].eq(0),
                        tableEJOP['master_id'].eq(self.itemId())
                        ]
                if self.eventSetDateTime:
                    cond.append(tableEJOP['setDate'].ge(self.eventSetDateTime))
                if self.eventDate:
                    cond.append(tableEJOP['setDate'].le(self.eventDate))
                record = db.getRecordEx(tableEJOP, [tableEJOP['execPerson_id']], cond, order = u'Event_JournalOfPerson.setDate DESC')
                self.execPersonId = forceRef(record.value('execPerson_id')) if record else self.cmbPerson.value()
            else:
                if self.mapJournalOfPerson:
                    self.mapJournalOfPerson.sort(key=lambda x: forceDateTime(x.value('setDate') if x else None), reverse=True)
                if self.mapJournalOfPerson:
                    for record in self.mapJournalOfPerson:
                        setDate = forceDateTime(record.value('setDate'))
                        if setDate:
                            if self.eventSetDateTime and self.eventDate and setDate >= self.eventSetDateTime and setDate <= self.eventDate:
                                self.execPersonId = forceRef(record.value('execPerson_id'))
                                return self.execPersonId
                            if self.eventSetDateTime and setDate >= self.eventSetDateTime:
                                self.execPersonId = forceRef(record.value('execPerson_id'))
                                return self.execPersonId
                            if self.eventDate and setDate <= self.eventDate:
                                self.execPersonId = forceRef(record.value('execPerson_id'))
                                return self.execPersonId
                else:
                    self.execPersonId = self.cmbPerson.value()
        else:
            self.execPersonId = self.cmbPerson.value()
        return self.execPersonId

    def getSetPersonId(self):
        return self.setPerson

    def updateExecPerson(self):
        self.getExecPersonId()
        if self.execPersonId:
            personId = self.cmbPerson.value()
            if personId != self.execPersonId:
                res = QtGui.QMessageBox.warning(self,
                                           u'Внимание!',
                                           u'''Смена ответственного врача.\nОтветственный '%s' будет заменен на '%s'.\nВы подтверждаете изменения?''' % (forceString(QtGui.qApp.db.translate('vrbPersonWithSpeciality', 'id', personId, 'name')),
                                                                                                                                                         forceString(QtGui.qApp.db.translate('vrbPersonWithSpeciality', 'id', self.execPersonId, 'name'))),
                                           QtGui.QMessageBox.Ok|QtGui.QMessageBox.Cancel,
                                           QtGui.QMessageBox.Cancel)
                if res == QtGui.QMessageBox.Ok:
                    self.cmbPerson.setValue(self.execPersonId)



    def exec_(self):
        result = CEventEditDialog.exec_(self)
        return result

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
#        self.addCol(CRBLikeEnumInDocTableCol(u'Госп',      'hospital',       7, CHospitalInfo.names, showFields=CRBComboBox.showCode, preferredWidth=150)).setToolTip(u'Потребность в госпитализации')
        self.addCol(CRBInDocTableCol(    u'Травма',        'traumaType_id', 10, 'rbTraumaType', addNone=True, showFields=CRBComboBox.showName, preferredWidth=150))
        self.addCol(CToxicSubstances(u'ТоксВещ', 'toxicSubstances_id', 10, addNone=True, showFields=CRBComboBox.showName, preferredWidth=150)).setToolTip(u'Токсичное вещество')
        self.addCol(CRBInDocTableCol(    u'ГрЗд',          'healthGroup_id', 7, 'rbHealthGroup', addNone=True, showFields=CRBComboBox.showCode, preferredWidth=150)).setToolTip(u'Группа здоровья')
        self.addCol(CInDocTableCol(u'Описание',     'freeInput', 15))
        self.columnHandleDiagnosis = self.getColIndex('handleDiagnosis', None)
        self.setFilter(self.table['diagnosisType_id'].inlist([id for id in self.diagnosisTypeCol.ids if id]))
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
            if index.isValid():
                if column == self.getColIndex('MKBEx'):
                    mkb = forceString(self.items()[row].value('MKB'))
                    if not (bool(mkb) and mkb[0] in (u'S', u'T')):
                        return result & ~Qt.ItemIsEnabled
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
#            result.setValue('result_id',  toVariant(CF003Dialog.defaultDiagnosticResultId))
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
                self.emitDiagnosisChanged()
#                if result:
#                    self.updateCharacterByMKB(row, specifiedMKB)
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
            baseDiagnosisId = self.diagnosisTypeCol.ids[1]
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


    def emitDiagnosisChanged(self):
        self.emit(SIGNAL('diagnosisChanged()'))



class CF003PreliminaryDiagnosticsModel(CF003BaseDiagnosticsModel):
    def __init__(self, parent):
        CF003BaseDiagnosticsModel.__init__(self, parent, None, '7', '11', '12')

    
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

