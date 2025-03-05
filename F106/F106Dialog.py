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
## Форма 106: свидетельство о смерти
##
#############################################################################

from PyQt4          import QtGui, QtSql
from PyQt4.QtCore   import (Qt, QDate, QDateTime, QModelIndex,
                            QTime, QVariant, pyqtSignature, SIGNAL, QEvent)

from library.Attach.AttachAction        import getAttachAction
from library.crbcombobox                import CRBComboBox
from library.ICDInDocTableCol           import CICDExInDocTableCol
from library.ICDMorphologyInDocTableCol import CMKBMorphologyCol
from library.InDocTable                 import (CMKBListInDocTableModel,
                                                CBoolInDocTableCol,
                                                CInDocTableCol,
                                                CRBInDocTableCol)

from library.interchange            import (getDatetimeEditValue,
                                            getLineEditValue,
                                            setComboBoxValue,
                                            getRBComboBoxValue,
                                            getTextEditValue,
                                            setDatetimeEditValue,
                                            setLineEditValue,
                                            setRBComboBoxValue,
                                            setTextEditValue)
from library.TNMS.TNMSComboBox      import CTNMSCol
from library.MKBExSubclassComboBox  import CMKBExSubclassCol
from library.Utils                  import (copyFields,
                                            forceBool,
                                            forceDate,
                                            forceInt,
                                            forceRef,
                                            forceString,
                                            toVariant,
                                            variantEq,
                                            forceStringEx,
                                            trim)

from library.PrintTemplates         import customizePrintButton, getPrintButton, applyTemplate
from library.PrintInfo              import CInfoContext

from Events.ActionInfo              import CActionInfoProxyList
from Events.EventEditDialog         import (CEventEditDialog,
                                            CDiseaseCharacter,
                                            CDiseaseStage,
                                            CDiseasePhases,
                                            CToxicSubstances,
                                            getToxicSubstancesIdListByMKB)
from Events.EventInfo               import CDiagnosticInfoProxyList, CEmergencyEventInfo
from Events.RelatedEventAndActionListDialog import CRelatedEventAndActionListDialog
from Events.Utils import (checkDiagnosis,
                          checkIsHandleDiagnosisIsChecked,
                          getAvailableCharacterIdByMKB,
                          getDiagnosisId2,
                          getEventShowTime,
                          recordAcceptable,
                          setAskedClassValueForDiagnosisManualSwitch,
                          mkbIsOnko,
                          CFinanceType,
                          checkAttachOnDate,
                          getEventAidTypeRegionalCode)

from F106.F106DiagnosisSelectionDialog  import CDiagnosisSelectionDialog

from F106.PreF106Dialog             import CPreF106Dialog, CPreF106DagnosticAndActionPresets
from Registry.Utils                 import getAddressId, getAddress, CAddressInfo, saveSurveillanceRemoveDeath
from Users.Rights                   import (urAccessF025planner,
                                            urAdmin,
                                            urEditEndDateEvent,
                                            urRegTabWriteRegistry,
                                            urRegTabReadRegistry,
                                            urCanReadClientVaccination,
                                            urCanEditClientVaccination)

from RefBooks.DeathPlaceType.Info                   import CDeathPlaceTypeInfo
from RefBooks.DeathCauseType.Info                   import CDeathCauseTypeInfo
from RefBooks.GroundsForDeathCause.Info             import CGroundsForDeathCauseInfo
from RefBooks.EmployeeTypeDeterminedDeathCause.Info import CEmployeeTypeDeterminedDeathCauseInfo
from F106.Ui_F106                                   import Ui_Dialog


def setClientDeathDate(clientId, deathDate, deathPlace):
    db = QtGui.qApp.db

    tableClient = db.table('Client')
    record = db.getRecord(tableClient, 'id, deathDate, deathPlaceType_id', clientId)
    if record:
        record.setValue('deathDate', toVariant(deathDate))
        record.setValue('deathPlaceType_id', toVariant(deathPlace))
        db.updateRecord(tableClient, record)

    tableClientAttach = db.table('ClientAttach')
    cond = [
        tableClientAttach['deleted'].eq(0),
        tableClientAttach['client_id'].eq(clientId),
        tableClientAttach['endDate'].isNull(),
    ]
    recordList = db.getRecordList(tableClientAttach, '*', cond)
    if recordList:
        for record in recordList:
            record.setValue('endDate', toVariant(deathDate))
            db.updateRecord(tableClientAttach, record)


class CF106Dialog(CEventEditDialog, Ui_Dialog):

    dfAccomp = 2 # Сопутствующий

    def __init__(self, parent):
        CEventEditDialog.__init__(self, parent)
        self.mapSpecialityIdToDiagFilter = {}
        self.setupUi(self)

        # create models
        self.addModels('PreliminaryDiagnostics', CF106DiagnosticsModel(self, '8', '10'))
        self.addModels('FinalDiagnostics',       CF106FinalDiagnosticsModel(self, self.tblFinalDiagnostics))

        # ui
        self.scrollArea.installEventFilter(self)
        self.scrollArea.verticalScrollBar().installEventFilter(self)
        self.addObject('actEditClient', QtGui.QAction(u'Открыть регистрационную карточку', self))
        self.addObject('actPortal_Doctor', QtGui.QAction(u'Перейти на портал врача', self))
        self.addObject('actShowAttachedToClientFiles', getAttachAction('Client_FileAttach',  self))
        self.addObject('actShowContingentsClient', QtGui.QAction(u'Показать все наблюдаемые контингенты', self))
        self.addObject('actOpenClientVaccinationCard', QtGui.QAction(u'Открыть прививочную карту', self))
        self.addObject('btnPlanning', QtGui.QPushButton(u'Планировщик', self))
        self.addObject('btnRelatedEvent', QtGui.QPushButton(u'Связанные события', self))
        self.createSaveAndCreateAccountButton()

        # 0013313: Не открывается регистрационная карточка из события
        self.actEditClient.triggered.connect(self.on_actEditClient_triggered)
        self.actPortal_Doctor.triggered.connect(self.on_actPortal_Doctor_triggered)
        self.actShowContingentsClient.triggered.connect(self.on_actShowContingentsClient_triggered)
        self.actOpenClientVaccinationCard.triggered.connect(self.on_actOpenClientVaccinationCard_triggered)

        self.setupSaveAndCreateAccountButton()
        self.addObject('btnPrint', getPrintButton(self, ''))
        # self.addObject('btnMedicalCommission', QtGui.QPushButton(u'ВК', self))
        self.addObject('btnPrintMedicalDiagnosis', getPrintButton(self, '', u'Врачебный диагноз'))

        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setWindowTitleEx(u'Ф.106/у')

        self.setMedicalDiagnosisContext()
        self.tabToken.setFocusProxy(self.tblPreliminaryDiagnostics)

        self.tabStatus.setEventEditor(self)
        self.tabMedicalDiagnosis.setEventEditor(self)
        self.tabMisc.setEventEditor(self)
        self.tabCash.setEventEditor(self)
        self.tabStatus.setActionTypeClass(0)
        self.tabMisc.setActionTypeClass(3)
        if QtGui.qApp.defaultKLADR()[:2] in ['23', '01']:
            self.buttonBox.addButton(self.btnPlanning, QtGui.QDialogButtonBox.ActionRole)


        # self.buttonBox.addButton(self.btnMedicalCommission, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnRelatedEvent, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnPrint, QtGui.QDialogButtonBox.ActionRole)
        # self.buttonBox.addButton(self.btnMedicalCommission, QtGui.QDialogButtonBox.ActionRole)
        self.connect(self.btnPrint, SIGNAL('printByTemplate(int)'), self.on_btnPrint_printByTemplate)
        self.modelFinalDiagnostics.view = self.tblFinalDiagnostics

        # tables to rb and combo-boxes
        # мы полагаем, что cmbPerson - свой врач,
        # мы полагаем, что cmbPerson2 - любой паталогоанатом (код специальности - 51)
        self.cmbPerson2.setOrgId(None)
        self.cmbPerson2.setSpecialityId(forceRef(QtGui.qApp.db.translate('rbSpeciality', 'code', '51', 'id'))) # magic!
        # мы полагаем, что cmbStatusPerson - свой врач,
        # мы полагаем, что cmbMiscPerson - свой врач,

        # assign models
        self.tblPreliminaryDiagnostics.setModel(self.modelPreliminaryDiagnostics)
        self.tblFinalDiagnostics.setModel(self.modelFinalDiagnostics)
        self.tabCash.addActionModel(self.tabStatus.modelAPActions)
        self.tabCash.addActionModel(self.tabMisc.modelAPActions)

        # popup menus
        self.txtClientInfoBrowser.actions.append(self.actEditClient)
        self.txtClientInfoBrowser.actions.append(self.actPortal_Doctor)
        self.txtClientInfoBrowser.actions.append(self.actShowAttachedToClientFiles)
        self.txtClientInfoBrowser.actions.append(self.actShowContingentsClient)
        self.txtClientInfoBrowser.actions.append(self.actOpenClientVaccinationCard)
        self.actOpenClientVaccinationCard.setEnabled(QtGui.qApp.userHasAnyRight([urCanReadClientVaccination, urCanEditClientVaccination]))
        self.actEditClient.setEnabled(QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]))
        self.tblPreliminaryDiagnostics.addCopyDiagnosisToFinal(self)

        # default values
        self.buttonBox.addButton(self.btnPrintMedicalDiagnosis, QtGui.QDialogButtonBox.ActionRole)
        self.setupDirtyCather()
        self.setIsDirty(False)
        self.blankMovingIdList = []
        self.tabNotes.setEventEditor(self)
        self.setupVisitsIsExposedPopupMenu()

        self.postSetupUi()
        if hasattr(self, 'edtEndDate'):
            self.edtEndDate.setEnabled(QtGui.qApp.userHasRight(urEditEndDateEvent))
        if hasattr(self, 'edtEndTime'):
            self.edtEndTime.setEnabled(QtGui.qApp.userHasRight(urEditEndDateEvent))
        self.btnPrintMedicalDiagnosis.setVisible(False)
        self.cmbDeathPlaceType.setTable('rbDeathPlaceType')
        self.cmbDeathCauseType.setTable('rbDeathCauseType')
        self.cmbEmployeeTypeDeterminedDeathCause.setTable('rbEmployeeTypeDeterminedDeathCause')
        self.cmbGroundsForDeathCause.setTable('rbGroundsForDeathCause')
        self.chkKLADR.setChecked(True)
        self.cmbCity.setCode(QtGui.qApp.defaultKLADR())
        self.cmbStreet.setCity(QtGui.qApp.defaultKLADR())
        self.cmbStreet.setCode('')
        self.createActionAddButton()
        # done


    def destroy(self):
        CEventEditDialog.deleteLater(self)
        self.tblPreliminaryDiagnostics.setModel(None)
        self.tblFinalDiagnostics.setModel(None)
        del self.modelPreliminaryDiagnostics
        del self.modelFinalDiagnostics

        self.tabStatus.deleteLater()
        self.tabMisc.deleteLater()
        self.tabCash.deleteLater()


    def eventFilter(self, obj, event):
        if event.type() == QEvent.ShortcutOverride:
            event.ignore()
            return True
        elif obj == self.scrollArea and event.type() == QEvent.Resize or obj == self.scrollArea.verticalScrollBar() and (event.type() == QEvent.Hide or event.type() == QEvent.Show):
            width = self.size().width()-9
            if self.scrollArea.verticalScrollBar().isVisible():
                width -= self.scrollArea.verticalScrollBar().width()
            self.scrollAreaWidgetContents.setMaximumWidth(width)
        event.accept()
        return False


    def setExternalId(self, externalId):
        pass


    def getServiceActionCode(self):
        return None


    def setMesInfo(self, mesCode):
        pass


    def _prepare(self, clientId, eventTypeId, orgId, personId, eventSetDatetime, eventDatetime, weekProfile, numDays, presetDiagnostics,
                 presetActions, disabledActions, externalId, assistantId, curatorId, actionTypeIdValue = None, valueProperties = [],
                 relegateOrgId = None, relegatePersonId=None, diagnos = None, financeId = None, protocolQuoteId = None, actionByNewEvent = [],
                 order = 1, relegateInfo=[], plannedEndDate = None, isEdit = False):
        if not isEdit:
            self.eventSetDateTime = eventSetDatetime if isinstance(eventSetDatetime, QDateTime) else QDateTime(eventSetDatetime)
            self.eventDate = eventDatetime.date() if isinstance(eventDatetime, QDateTime) else eventDatetime
            self.setOrgId(orgId if orgId else QtGui.qApp.currentOrgId())
            self.cmbOrg.setValue(self.orgId)
            self.setEventTypeId(eventTypeId)
            self.setClientId(clientId)
            self.tabNotes.setNotesEx(externalId, assistantId, curatorId, relegateOrgId, relegatePersonId, clientId, relegateInfo)
            self.setPersonId(personId)
            self.cmbPerson.setValue(personId)
            self.cmbPerson2.setValue(None)
            self.edtBegDate.setDate(self.eventDate)
            self.edtEndDate.setDate(self.eventSetDateTime.date())
            self.edtBegTime.setTime(eventDatetime.time() if isinstance(eventDatetime, QDateTime) else QTime())
            self.edtEndTime.setTime(eventSetDatetime.time() if isinstance(eventSetDatetime, QDateTime) else QTime())
            self.cmbContract.setCurrentIndex(0)
            self.initFocus()
        self.prepareActions(presetActions, disabledActions, actionTypeIdValue, valueProperties, diagnos, financeId, protocolQuoteId, actionByNewEvent, plannedEndDate)
        self.setIsDirty(False)
        self.tabNotes.setEventEditor(self)
        self.setFilterResult(self.eventSetDateTime.date())
        return True and self.checkDeposit()


    def prepare(self, clientId, eventTypeId, orgId, personId, eventSetDatetime, eventDatetime, weekProfile,
                numDays, externalId, assistantId, curatorId, flagHospitalization = False,
                actionTypeIdValue = None, valueProperties = [], tissueTypeId=None, selectPreviousActions=False,
                relegateOrgId = None, relegatePersonId=None, diagnos = None, financeId = None,
                protocolQuoteId = None, actionByNewEvent = [], order = 1,
                actionListToNewEvent = [], typeQueue = -1, docNum=None, relegateInfo=[], plannedEndDate = None,
                mapJournalInfoTransfer = [], voucherParams = {}, isEdit=False):
        self.setPersonId(personId)
        eventDate = eventDatetime.date() if isinstance(eventDatetime, QDateTime) else eventDatetime
        if not eventDate and eventSetDatetime:
            eventDate = eventSetDatetime.date() if isinstance(eventSetDatetime, QDateTime) else eventSetDatetime
        else:
            eventDate = QDate.currentDate()
        result = True
        if QtGui.qApp.userHasRight(urAccessF025planner):
            dlg = CPreF106Dialog(self, self.contractTariffCache)
            try:
                dlg.setBegDateEvent(eventSetDatetime.date() if isinstance(eventSetDatetime, QDateTime) else eventSetDatetime)
                dlg.prepare(clientId, eventTypeId, eventDate, self.personId, self.personSpecialityId, self.personTariffCategoryId, flagHospitalization, actionTypeIdValue, tissueTypeId)
                if dlg.diagnosticsTableIsNotEmpty() or dlg.actionsTableIsNotEmpty():
                    if not dlg.exec_():
                        return False
                result = self._prepare(clientId, eventTypeId, orgId, personId, eventSetDatetime, eventDatetime, weekProfile, numDays,
                                     dlg.diagnostics(), dlg.actions(), dlg.disabledActionTypeIdList,
                                     externalId, assistantId, curatorId, actionTypeIdValue, valueProperties,
                                     relegateOrgId, relegatePersonId, diagnos, financeId, protocolQuoteId,
                                     actionByNewEvent, order, relegateInfo, plannedEndDate, isEdit = False)
            finally:
                dlg.deleteLater()
        else:
            presets = CPreF106DagnosticAndActionPresets(clientId, eventTypeId, eventDate, self.personSpecialityId, flagHospitalization, actionTypeIdValue)
            presets.setBegDateEvent(eventSetDatetime.date() if isinstance(eventSetDatetime, QDateTime) else eventSetDatetime)
            result = self._prepare(clientId, eventTypeId, orgId, personId, eventSetDatetime, eventDatetime, weekProfile, numDays,
                                 presets.unconditionalDiagnosticList, presets.unconditionalActionList, presets.disabledActionTypeIdList,
                                 externalId, assistantId, curatorId, None, [], relegateOrgId, relegatePersonId, diagnos,
                                 financeId, protocolQuoteId, actionByNewEvent, order, relegateInfo, plannedEndDate, isEdit = False)

        if result:
            diagSelectDlg = CDiagnosisSelectionDialog(self)
            if diagSelectDlg.findDiagnosis(clientId):
                if diagSelectDlg.exec_():
                    mkbrecord = diagSelectDlg.getDiagnosis()
                    record = self.modelFinalDiagnostics.getEmptyRecord()
                    record.setValue('MKB', mkbrecord.value('MKB'))
                    record.setValue('MKBEx', mkbrecord.value('MKBEx'))
                    record.setValue('traumaType_id', mkbrecord.value('traumaType_id'))
                    record.setValue('character_id', mkbrecord.value('character_id'))
                    record.setValue('phase_id', mkbrecord.value('phase_id'))
                    record.setValue('stage_id', mkbrecord.value('stage_id'))
                    self.modelFinalDiagnostics.addRecord(record)
                    record = self.modelPreliminaryDiagnostics.getEmptyRecord()
                    record.setValue('MKB', mkbrecord.value('MKB'))
                    record.setValue('MKBEx', mkbrecord.value('MKBEx'))
                    record.setValue('traumaType_id', mkbrecord.value('traumaType_id'))
                    record.setValue('character_id', mkbrecord.value('character_id'))
                    record.setValue('phase_id', mkbrecord.value('phase_id'))
                    record.setValue('stage_id', mkbrecord.value('stage_id'))
                    self.modelPreliminaryDiagnostics.addRecord(record)
                    db = QtGui.qApp.db
                    tableResult = db.table('rbResult')
                    cond = [tableResult['eventPurpose_id'].eq(self.eventPurposeId),
                            tableResult['code'].eq('0')]
                    resultRecord = db.getRecordEx(tableResult, 'id', cond)
                    if resultRecord:
                        resultId = forceInt(resultRecord.value(0))
                        self.cmbResult.setValue(resultId)
        return result


    def prepareActions(self, presetActions, disabledActions, actionTypeIdValue, valueProperties, diagnos, financeId, protocolQuoteId, actionByNewEvent, plannedEndDate=None):
        def addActionType(actionTypeId, amount, idListActionType, idListActionTypeIPH, actionFinance, idListActionTypeMoving, plannedEndDate):
            db = QtGui.qApp.db
            tableOrgStructure = db.table('OrgStructure')
            for model in (self.tabStatus.modelAPActions, self.tabMisc.modelAPActions):
                if actionTypeId in model.actionTypeIdList:
                    if actionTypeId in idListActionType and not actionByNewEvent:
                        model.addRow(actionTypeId, amount)
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
                        record, action = model.items()[-1]
                        if diagnos:
                            record, action = model.items()[-1]
                            action[u'Диагноз'] = diagnos
                    elif actionByNewEvent and actionTypeId in idListActionTypeMoving:
                        model.addRow(actionTypeId, amount)
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
                        record, action = model.items()[-1]

        def disableActionType(actionTypeId):
            for model in (self.tabStatus.modelAPActions,
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


    def setLeavedAction(self, actionTypeIdValue, params = {}):
        pass


    def initFocus(self):
        self.chkAutopsy.setFocus(Qt.OtherFocusReason)
#        self.tblPreliminaryDiagnostics.setFocus(Qt.OtherFocusReason)


    def newDiagnosticRecord(self, template):
        result = self.tblPreliminaryDiagnostics.model().getEmptyRecord()
        return result


    def setRecord(self, record):
        CEventEditDialog.setRecord(self, record)
        setLineEditValue(self.edtNumber,        record, 'externalId')
        setDatetimeEditValue(self.edtBegDate, self.edtBegTime, record, 'setDate')
        setDatetimeEditValue(self.edtEndDate, self.edtEndTime, record, 'execDate')
        setRBComboBoxValue(self.cmbPerson,      record, 'execPerson_id')
        setRBComboBoxValue(self.cmbPerson2,     record, 'setPerson_id')
        self.chkAutopsy.setChecked(forceInt(record.value('isPrimary'))==1)
        setComboBoxValue(self.cmbAutopsyType,   record, 'isAutopsyType')
        self.setPersonId(self.cmbPerson.value())
        setRBComboBoxValue(self.cmbResult,      record, 'result_id')
        setRBComboBoxValue(self.cmbContract,    record, 'contract_id')
        setTextEditValue(self.edtNote,          record, 'note')
        self.tabNotes.setNotes(record)
        self.tabNotes.setEventEditor(self)
        self.loadDiagnostics(self.modelPreliminaryDiagnostics)
        self.loadDiagnostics(self.modelFinalDiagnostics)
        self.tabMedicalDiagnosis.load(self.itemId())
        self.loadActions()
        self.tabCash.load(self.itemId())
        self.loadDeathInfo()
        self.on_cmbResult_currentIndexChanged()
        self.initFocus()
        self.setIsDirty(False)
        self.blankMovingIdList = []
        self.protectClosedEvent()
        self.btnRelatedEventHighlight()


    def loadDiagnostics(self, modelDiagnostics):
        db = QtGui.qApp.db
        table = db.table('Diagnostic')
        isDiagnosisManualSwitch = modelDiagnostics.manualSwitchDiagnosis()
        rawItems = db.getRecordList(table, '*', [
            table['deleted'].eq(0),
            table['event_id'].eq(self.itemId()),
            modelDiagnostics.filter
        ], 'id')
        items = []
        for record in rawItems:
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
            if isDiagnosisManualSwitch:
                isCheckedHandleDiagnosis = checkIsHandleDiagnosisIsChecked(
                    setDate, self.clientId, diagnosisId)
                newRecord.setValue('handleDiagnosis', QVariant(isCheckedHandleDiagnosis))

            items.append(newRecord)
        modelDiagnostics.setItems(items)


    def loadActions(self):
        items = self.loadActionsInternal()
        self.tabStatus.loadActions(items.get(0, []))
        self.tabMisc.loadActions(items.get(3, []))
        self.tabCash.modelAccActions.regenerate()


    def loadDeathInfo(self):
        self.chkKLADR.setChecked(True)
        eventId = self.itemId()
        record = QtGui.qApp.db.getRecordEx('Event_Death', '*', 'master_id = %d' % eventId)
        addressId = forceRef(record.value('address_id')) if record else None
        if record:
            setRBComboBoxValue(self.cmbDeathPlaceType, record, 'deathPlaceType_id')
            setRBComboBoxValue(self.cmbDeathCauseType, record, 'deathCauseType_id')
            setRBComboBoxValue(self.cmbEmployeeTypeDeterminedDeathCause, record, 'employeeTypeDeterminedDeathCause_id')
            setRBComboBoxValue(self.cmbGroundsForDeathCause, record, 'groundsForDeathCause_id')
            setLineEditValue(self.edtFreeInput, record, 'freeInput')
            address = getAddress(addressId)
            if address.KLADRCode:
                self.cmbCity.setCode(address.KLADRCode)
                self.cmbStreet.setCity(address.KLADRCode)
                self.cmbStreet.setCode(address.KLADRStreetCode)
                self.edtHouse.setText(address.number)
                self.edtCorpus.setText(address.corpus)
                self.edtFlat.setText(address.flat)
            else:
                self.cmbCity.setCode(QtGui.qApp.defaultKLADR())
                self.cmbStreet.setCity(QtGui.qApp.defaultKLADR())
                self.cmbStreet.setCode('')
                self.edtHouse.setText('')
                self.edtCorpus.setText('')
                self.edtFlat.setText('')
        else:
            self.cmbCity.setCode(QtGui.qApp.defaultKLADR())
            self.cmbStreet.setCity(QtGui.qApp.defaultKLADR())
            self.cmbStreet.setCode('')
            self.edtHouse.setText('')
            self.edtCorpus.setText('')
            self.edtFlat.setText('')
            self.cmbDeathPlaceType.setValue(None)
            self.cmbDeathCauseType.setValue(None)
            self.cmbEmployeeTypeDeterminedDeathCause.setValue(None)
            self.cmbGroundsForDeathCause.setValue(None)


    def getRecord(self):
        record = CEventEditDialog.getRecord(self)
        showTime = getEventShowTime(self.eventTypeId)
        self.getShowButtonAccount()
        self.getShowButtonTemperatureList()
        self.getShowButtonNomenclatureExpense()
        self.getShowButtonJobTickets()

        getRBComboBoxValue(self.cmbContract, record, 'contract_id')
        getLineEditValue(self.edtNumber, record, 'externalId')
        getDatetimeEditValue(self.edtBegDate, self.edtBegTime, record, 'setDate', showTime)
        getDatetimeEditValue(self.edtEndDate, self.edtEndTime, record, 'execDate', showTime)
        getRBComboBoxValue(self.cmbPerson2, record, 'setPerson_id')
        getRBComboBoxValue(self.cmbPerson, record, 'execPerson_id')
        getRBComboBoxValue(self.cmbResult, record, 'result_id')
        record.setValue('order', toVariant(1))
        record.setValue('isPrimary', toVariant(1 if self.chkAutopsy.isChecked() else 2))
        record.setValue('isAutopsyType',
            toVariant(self.cmbAutopsyType.currentIndex() if self.chkAutopsy.isChecked() else None))
        getTextEditValue(self.edtNote, record, 'note')
        self.tabNotes.getNotes(record, self.eventTypeId)
        return record


    def saveInternals(self, eventId):
        self.saveDiagnostics(self.modelPreliminaryDiagnostics, eventId)
        self.saveFinalDiagnostics(self.modelFinalDiagnostics, eventId)
        self.tabMedicalDiagnosis.save(eventId)
        setAskedClassValueForDiagnosisManualSwitch(None)
        self.saveActions(eventId)
        self.tabCash.save(eventId)
        setClientDeathDate(self.clientId, QDateTime(self.edtBegDate.date(), self.edtBegTime.time()) , self.cmbDeathPlaceType.value())
        self.saveBlankUsers(self.blankMovingIdList)
        self.tabNotes.saveAttachedFiles(eventId)
        self.saveTrailerActions(eventId)
        self.saveEventDeath(eventId)
        saveSurveillanceRemoveDeath(self.edtBegDate.date(), self.clientId, self.cmbPerson.value())


    def saveEventDeath(self, eventId):
        db = QtGui.qApp.db
        addressId = self.getAddressId()
        record = db.getRecordEx('Event_Death', '*', 'master_id = %d' % eventId)
        if record is None:
            record = db.record('Event_Death')
            record.setValue('master_id', toVariant(eventId))

        record.setValue('deathPlaceType_id', toVariant(self.cmbDeathPlaceType.value()))
        record.setValue('deathCauseType_id', toVariant(self.cmbDeathCauseType.value()))
        record.setValue('employeeTypeDeterminedDeathCause_id', toVariant(self.cmbEmployeeTypeDeterminedDeathCause.value()))
        record.setValue('groundsForDeathCause_id', toVariant(self.cmbGroundsForDeathCause.value()))
        record.setValue('address_id', toVariant(addressId))
        record.setValue('freeInput', toVariant(forceStringEx(self.edtFreeInput.text())))
        db.insertOrUpdate('Event_Death', record)

    def saveTrailerActions(self, eventId):
        if self.trailerActions:
            for action in self.trailerActions:
                prevActionId = self.trailerIdList.get(action.trailerIdx - 1, None)
                action.getRecord().setValue('prevAction_id', toVariant(prevActionId))
                action.save(eventId)


    def saveDiagnostics(self, modelDiagnostics, eventId):
        items = modelDiagnostics.items()
        isDiagnosisManualSwitch = modelDiagnostics.manualSwitchDiagnosis()
        isFirst = True
        date = self.edtBegDate.date()
        dateVariant = toVariant(date)
        personIdVariant = toVariant(self.personId)
        specialityIdVariant = QtGui.qApp.db.translate('Person', 'id', personIdVariant, 'speciality_id')
        MKBDiagnosisIdPairList = []
        prevId=0
        for item in items:
            MKB = forceStringEx(item.value('MKB'))
            MKBEx = forceStringEx(item.value('MKBEx'))
            TNMS = forceStringEx(item.value('TNMS'))
            morphologyMKB = forceStringEx(item.value('morphologyMKB'))
            diagnosisTypeId = modelDiagnostics.getDiagnosisTypeId(isFirst)
            item.setValue('diagnosisType_id', toVariant(diagnosisTypeId))
            item.setValue('speciality_id', specialityIdVariant)
            item.setValue('person_id', toVariant(self.personId) )
            item.setValue('setDate', dateVariant )
            item.setValue('endDate', dateVariant )
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
            isFirst = False
            MKBDiagnosisIdPairList.append((MKB, diagnosisId))
        modelDiagnostics.saveItems(eventId)
        self.modifyDiagnosises(MKBDiagnosisIdPairList)


    def saveFinalDiagnostics(self, modelDiagnostics, eventId):
        items = modelDiagnostics.items()
        isDiagnosisManualSwitch = modelDiagnostics.manualSwitchDiagnosis()
        date = self.edtBegDate.date()
        dateVariant = toVariant(date)
        personIdVariant = toVariant(self.personId)
        specialityIdVariant = QtGui.qApp.db.translate('Person', 'id', personIdVariant, 'speciality_id')
        MKBDiagnosisIdPairList = []
        prevId = 0
        for item in items:
            MKB   = forceStringEx(item.value('MKB'))
            MKBEx = forceStringEx(item.value('MKBEx'))
            TNMS  = forceStringEx(item.value('TNMS'))
            morphologyMKB = forceStringEx(item.value('morphologyMKB'))
            diagnosisTypeId = forceRef(item.value('diagnosisType_id'))
            item.setValue('speciality_id', specialityIdVariant)
            item.setValue('person_id', toVariant(self.personId) )
            item.setValue('setDate', dateVariant )
            item.setValue('endDate', dateVariant )
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
            if prevId > itemId:
                item.setValue('id', QVariant())
                prevId = 0
            else:
               prevId = itemId
            MKBDiagnosisIdPairList.append((MKB, diagnosisId))
        modelDiagnostics.saveItems(eventId)
        self.modifyDiagnosises(MKBDiagnosisIdPairList)


    def saveActions(self, eventId):
        self.tabStatus.saveActions(eventId)
        self.tabMisc.saveActions(eventId)


    def setOrgId(self, orgId):
        self.orgId = orgId
        self.cmbContract.setOrgId(orgId)
        self.tabStatus.setOrgId(orgId)
        self.tabMisc.setOrgId(orgId)
        self.cmbOrg.setValue(self.orgId)


    def setEventTypeId(self, eventTypeId):
        CEventEditDialog.setEventTypeId(self, eventTypeId, u'Ф.106')
        self.tabCash.windowTitle = self.windowTitle()
        showTime = getEventShowTime(eventTypeId)
        self.getShowButtonAccount()
        self.getShowButtonTemperatureList()
        self.getShowButtonNomenclatureExpense()
        self.getShowButtonJobTickets()
        self.edtBegTime.setVisible(showTime)
        self.edtEndTime.setVisible(showTime)
        self.cmbResult.setTable('rbResult', True, 'eventPurpose_id=\'%d\'' % self.eventPurposeId)
        self.cmbContract.setEventTypeId(eventTypeId)
        customizePrintButton(self.btnPrint, self.eventContext if self.eventContext else 'F106')


    def resetActionTemplateCache(self):
        self.tabStatus.actionTemplateCache.reset()
        self.tabMisc.actionTemplateCache.reset()


    def checkDataEntered(self):
        result = CEventEditDialog.checkDataEntered(self)
        tabList = [self.tabStatus, self.tabMisc]
        self.blankMovingIdList = []
#        result = result and (self.orgId != QtGui.qApp.currentOrgId() or self.cmbContract.value() or self.checkInputMessage(u'договор', False, self.cmbContract))
        showTime = getEventShowTime(self.eventTypeId)
        if showTime:
            begDate = QDateTime(self.edtBegDate.date(), self.edtBegTime.time())
            endDate = QDateTime(self.edtEndDate.date(), self.edtEndTime.time())
        else:
            begDate = self.edtBegDate.date()
            endDate = self.edtEndDate.date()
        result = result and (begDate or self.checkInputMessage(u'дату смерти', False, self.edtBegDate))
        result = result and (endDate or self.checkInputMessage(u'дату констатации', False, self.edtEndDate))
        result = result and (self.cmbResult.value() or self.checkInputMessage(u'результат', False, self.cmbResult))
        result = result and (self.cmbPerson.value() or self.checkInputMessage(u'врач', False, self.cmbPerson))
        result = result and self.checkExecPersonSpeciality(self.cmbPerson.value(), self.cmbPerson)
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
        if begDate and endDate:
            result = result and self.checkActionDataEntered(begDate, QDateTime(), endDate, self.tabToken, self.edtBegDate, None, self.edtEndDate)
            result = result and self.checkEventDate(begDate, endDate, None, self.tabToken, None, self.edtEndDate, True)
        result = result and (len(self.modelPreliminaryDiagnostics.items())>0 or self.checkInputMessage(u'предварительный диагноз', False, self.tblPreliminaryDiagnostics))
        if self.edtEndDate.date():
            result = result and self.checkDiagnosticsDataEntered(self.tblPreliminaryDiagnostics)
            result = result and self.checkDiagnosticsDataEntered(self.tblFinalDiagnostics)
            result = result and (len(self.modelFinalDiagnostics.items())>0 or self.checkInputMessage(u'заключительный диагноз', False, self.tblFinalDiagnostics))
            result = result and self.checkDiagnosticsAndResultDivergence()
            result = result and self.checkExecPersonSpeciality(self.personId, self.cmbPerson)
            result = result and self.checkDiagnosticsPersonSpeciality()
        else:
            result = result and self.checkDiagnosticsPersonSpeciality()
            result = result and self.checkDiseaseCharactersDataEntered(self.modelPreliminaryDiagnostics, self.tblPreliminaryDiagnostics)
            result = result and self.checkDiseaseCharactersDataEntered(self.modelFinalDiagnostics, self.tblFinalDiagnostics)

        result = result and self.checkActionsDateEnteredActuality(begDate, endDate, tabList)
        result = result and self.checkActionsDataEntered(begDate, endDate)
        result = result and self.checkDeposit(True)
        result = result and self.tabCash.checkDataLocalContract()
        result = result and self.checkSerialNumberEntered()
        result = result and self.checkTabNotesEventExternalId()
        if self.edtEndDate.date():
            result = result and self.checkAndUpdateExpertise(self.edtEndDate.date(), self.cmbPerson.value())
            if CFinanceType.getCode(self.eventFinanceId) == CFinanceType.CMI and QtGui.qApp.defaultKLADR()[:2] == u'23':
                checkEpic, ConsFlatCodeList, needsListNazOnko = self.checkConsultationOrEpicris(tabList)
                result = result and self.needOnkoDocs(ConsFlatCodeList)
        result = result and self.selectNomenclatureAddedActions(tabList)
        result = result and self.checkAddress()
        return result


    def checkAddress(self):
        result = True
        if trim(self.edtFreeInput.text()):
            return True
        boolCorpus = (trim(self.edtFlat.text()) or trim(self.edtHouse.text()) or trim(self.edtCorpus.text()))
        result = result and (self.cmbCity.code() or self.checkInputMessage(u'Адрес места смерти. Введите населённый пункт.', not boolCorpus, self.cmbCity))
        if self.cmbStreet.count() > 0:
            result = result and (self.cmbStreet.code() or self.checkInputMessage(u'Адрес места смерти. Введите название улицы.', not boolCorpus, self.cmbStreet))
        result = result and (trim(self.edtFlat.text()) or self.checkInputMessage(u'Адрес места смерти. Введите номер квартиры.', True, self.edtFlat))
        result = result and (trim(self.edtHouse.text()) or self.checkInputMessage(u'Адрес места смерти. Введите номер дома.', not(trim(self.edtFlat.text()) or trim(self.edtCorpus.text()) or self.cmbStreet.code()), self.edtHouse))
        boolCorpus = (trim(self.edtFlat.text()) or trim(self.edtHouse.text()))
        if boolCorpus:
            result = result and (trim(self.edtCorpus.text()) or self.checkInputMessage(u'Адрес места смерти. Введите корпус.', True, self.edtCorpus))
        return result


    def getAddressId(self):
        address = {
            'useKLADR': self.chkKLADR.isChecked(),
            'KLADRCode': self.cmbCity.code(),
            'KLADRStreetCode': self.cmbStreet.code() if self.cmbStreet.code() else '',
            'number': forceStringEx(self.edtHouse.text()),
            'corpus': forceStringEx(self.edtCorpus.text()),
            'flat': forceStringEx(self.edtFlat.text()),
            'freeInput': forceStringEx(self.edtFreeInput.text()),
        }
        return getAddressId(address) if address['useKLADR'] else None


    def checkSerialNumberEntered(self):
        result = True
        self.blankMovingIdList = []
        db = QtGui.qApp.db
        table = db.table('ActionPropertyType')
        actionTypeIdListSerial = db.getDistinctIdList(table, [table['actionType_id']], [table['deleted'].eq(0), table['typeName'].like('BlankSerialNumber')])
        #actionTypeIdListNumber = db.getDistinctIdList(table, [table['actionType_id']], [table['deleted'].eq(0), table['typeName'].like('BlankNumber')])

        for tab in (self.tabStatus,
                      self.tabMisc):
            model = tab.modelAPActions
            for actionTypeIdSerial in actionTypeIdListSerial:
                if actionTypeIdSerial in model.actionTypeIdList:
                    for row, (record, action) in enumerate(model.items()):
                        if action and action._actionType.id:
                            actionTypeId = action._actionType.id
                            if actionTypeId == actionTypeIdSerial:
                                blank = action[u'Серия и номер бланка']
                                if blank:
                                    # #Проверка серий и номеров льготных рецептов на дубляж перед сохранением (для КК)
                                    # if QtGui.qApp.defaultKLADR()[:2] == u'23' and action._actionType.context == 'recipe' and not checkLGSerialNumber(self, blank, action, self.clientId):
                                    #     return False
                                    blankList = blank.split(" ")
                                    if len(blankList) == 2:
                                        serial = blankList[0]
                                        number = forceInt(blankList[1])
                                        if serial and number:
                                            blankParams = self.getBlankIdList(action)
                                            result, blankMovingId = self.checkBlankParams(blankParams, serial, number, tab.tblAPActions, row)
                                            self.blankMovingIdList.append(blankMovingId)
                                            if not result:
                                                return result
        return result

    
    def checkDiagnosticsPersonSpeciality(self):
        result = True
        result = result and self.checkPersonSpecialityDiagnostics(self.modelPreliminaryDiagnostics, self.tblPreliminaryDiagnostics)
        result = result and self.checkPersonSpecialityDiagnostics(self.modelFinalDiagnostics, self.tblFinalDiagnostics)
        return result
    
    
    def checkDiagnosticsAndResultDivergence(self):
        itemsPre = self.tblPreliminaryDiagnostics.model().items()
        itemsFin = self.tblFinalDiagnostics.model().items()
        divergence = False
        lenPre = len(itemsPre)
        lenFin = len(itemsFin)
        if lenPre != lenFin:
            divergence = True
        else:
            for i in range(0, lenPre):
                if forceString(itemsPre[i].value('MKB'))[:3] != forceString(itemsFin[i].value('MKB'))[:3]:
                    divergence = True

        result = True
        if self.cmbResult.currentIndex() <= 1 and divergence:
            result = result and self.checkValueMessage(u'Расхождение диагнозов не установлено, но диагнозы отличаются.', True, self.cmbResult)
        elif self.cmbResult.currentIndex() > 1 and not divergence:
            result = result and self.checkValueMessage(u'Установлено расхождение диагнозов, но диагнозы не отличаются.', True, self.cmbResult)
        return result


    def checkDiagnosticsDataEntered(self, tbl):
        for row, record in enumerate(tbl.model().items()):
            if not self.checkDiagnosticDataEntered(tbl, row, record):
                return False
        return True


    def checkDiagnosticDataEntered(self, tbl, row, record):
        result = True
        if result:
            MKB = forceString(record.value('MKB'))
            MKBEx = forceString(record.value('MKBEx'))
            specialityId = forceRef(QtGui.qApp.db.translate('Person', 'id', self.personId, 'speciality_id'))
            result = specialityId or self.checkValueMessage(u'Отсутствует специальность врача', False, tbl, row, record.indexOf('person_id'))
            result = result and MKB or self.checkInputMessage(u'диагноз', False, tbl, row, record.indexOf('MKB'))
            result = result and self.checkActualMKB(tbl, self.edtBegDate.date(), MKB, record, row)
            if result:
                char = MKB[:1]
                blockMKB = forceInt(MKB[1:3])
                traumaTypeId = forceRef(record.value('traumaType_id'))
                if char in 'ST' and not (char in 'T' and 36 <= blockMKB <= 78):
                    if not traumaTypeId:
                        result = self.checkValueMessage(u'Необходимо указать тип травмы',  True if QtGui.qApp.controlTraumaType()==0 else False, tbl, row, record.indexOf('traumaType_id'))
                    if result:
                        result = MKBEx or self.checkInputMessage(u'Дополнительный диагноз', True if QtGui.qApp.controlMKBExForTraumaType()==0 else False, tbl, row, record.indexOf('MKBEx'))
                        if result:
                            charEx = MKBEx[:1]
                            if charEx not in 'VWXY':
                                result = self.checkValueMessage(u'Доп.МКБ не соотвествует Доп.МКБ при травме', True, tbl, row, record.indexOf('MKBEx'))
                if char not in 'ST' and traumaTypeId:
                    result = self.checkValueMessage(u'Необходимо удалить тип травмы', False, tbl, row, record.indexOf('traumaType_id'))
            result = result and self.checkPersonSpeciality(record, row, tbl)
            # result = result and self.checkDiseaseCharacterDataEntered(row, record, MKB, tbl)
            result = result and self.checkPeriodResultHealthGroup(record, row, tbl)
        return result

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


    def recordAcceptable(self, record):
        return recordAcceptable(self.clientSex, self.clientAge, record)


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
        result = CEventEditDialog.getEventInfo(self, context, CEmergencyEventInfo)
        # ручная инициализация свойств
        result._isPrimary = False
        # ручная инициализация таблиц
        result._actions = CActionInfoProxyList(context, [self.tabStatus.modelAPActions, self.tabMisc.modelAPActions], result)
        result._diagnosises = CDiagnosticInfoProxyList(context, [self.modelPreliminaryDiagnostics, self.modelFinalDiagnostics])

        result._deathPlaceType = CDeathPlaceTypeInfo(context, self.cmbDeathPlaceType.value())
        result._deathCauseType = CDeathCauseTypeInfo(context, self.cmbDeathCauseType.value())
        result._employeeTypeDeterminedDeathCause = CEmployeeTypeDeterminedDeathCauseInfo(context, self.cmbEmployeeTypeDeterminedDeathCause.value())
        result._groundsForDeathCause = CGroundsForDeathCauseInfo(context, self.cmbGroundsForDeathCause.value())
        result._deathAddress = CAddressInfo(context, self.getAddressId()) if self.chkKLADR.isChecked() else None
        result._deathAddressFreeInput = forceStringEx(self.edtFreeInput.text())

        return result


    def getTempInvalidInfo(self, context):
        return None


    def setContractId(self, contractId):
        if self.contractId != contractId:
            CEventEditDialog.setContractId(self, contractId)
            self.tabCash.modelAccActions.setContractId(contractId)
            self.tabCash.updatePaymentsSum()


    @pyqtSignature('int')
    def on_cmbCity_currentIndexChanged(self, val):
        code = self.cmbCity.code()
        self.cmbStreet.setCity(code)


# # #
    @pyqtSignature('int')
    def on_tabWidget_currentChanged(self, index):
        widget = self.tabWidget.widget(index)
        if widget is not None:
            focusProxy = widget.focusProxy()
            if focusProxy:
                focusProxy.setFocus(Qt.OtherFocusReason)
        self.btnPrintMedicalDiagnosisEnabled(index)


    @pyqtSignature('QDate')
    def on_edtBegDate_dateChanged(self, date):
        self.eventDate = QDate(date)
        self.setFilterResult(date)
#        contractId = self.cmbContract.value()
        self.cmbContract.setDate(self.getDateForContract())
#        self.cmbContract.setValue(contractId)
        self.cmbPerson.setBegDate(date)
        self.cmbPerson2.setBegDate(date)
        self.setPersonDate(date)


    @pyqtSignature('QDate')
    def on_edtEndDate_dateChanged(self, date):
        self.eventSetDateTime.setDate(date)
        self.cmbContract.setDate(self.getDateForContract())
        self.cmbPerson.setEndDate(self.eventSetDateTime.date())
        self.cmbPerson2.setEndDate(self.eventSetDateTime.date())
        self.tabStatus.setEndDate(self.eventSetDateTime.date())
        self.tabMisc.setEndDate(self.eventSetDateTime.date())
        self.setEnabledChkCloseEvent(self.eventSetDateTime.date())
        if getEventShowTime(self.eventTypeId):
            time = QTime.currentTime() if date else QTime()
            self.edtEndTime.setTime(time)


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

        
    @pyqtSignature('QTime')
    def on_edtEndTime_timeChanged(self, time):
        self.eventSetDateTime.setTime(time)


    @pyqtSignature('int')
    def on_cmbOrg_currentIndexChanged(self):
        self.setOrgId(self.cmbOrg.value())


    @pyqtSignature('int')
    def on_cmbPerson_currentIndexChanged(self):
        oldPersonId = self.personId
        self.setPersonId(self.cmbPerson.value())
        # что-то сомнительным показалось - ну поменяли отв. врача,
        # всё равно менять врачей в действии вроде неправильно. или правильно?
        self.tabStatus.updatePersonId(oldPersonId, self.personId)
        self.tabMisc.updatePersonId(oldPersonId, self.personId)


    @pyqtSignature('int')
    def on_btnPrint_printByTemplate(self, templateId):
        if self.checkPrintByTemplateAllowed(templateId):
            context = CInfoContext()
            eventInfo = self.getEventInfo(context)

            data = {'event': eventInfo,
                    'client': eventInfo.client
                    }
            applyTemplate(self, templateId, data, signAndAttachHandler=None)


    @pyqtSignature('bool')
    def on_chkKLADR_toggled(self, checked):
        self.cmbCity.setEnabled(checked)
        self.cmbStreet.setEnabled(checked)
        self.edtHouse.setEnabled(checked)
        self.edtCorpus.setEnabled(checked)
        self.edtFlat.setEnabled(checked)
        self.edtFreeInput.setDisabled(checked)


# # #


    @pyqtSignature('')
    def on_actDiagnosticsAddAccomp_triggered(self):
        tbl = self.tblPreliminaryDiagnostics
        model = tbl.model()
        currentRow = tbl.currentIndex().row()
        if currentRow >= 0:
            currentRecord = model.items()[currentRow]
            newRecord = model.getEmptyRecord()
            newRecord.setValue('diagnosisType', QVariant(CF106Dialog.dfAccomp))
            newRecord.setValue('speciality_id', currentRecord.value('speciality_id'))
            newRecord.setValue('healthGroup_id', currentRecord.value('healthGroup_id'))
            model.insertRecord(currentRow+1, newRecord)
            tbl.setCurrentIndex(model.index(currentRow+1, newRecord.indexOf('MKB')))



# # # Actions # # #

    def getPrevActionId(self, action, type):
        return None


#
# #####################################################################################33
#


class CF106DiagnosticsModel(CMKBListInDocTableModel):
    MKB_allowed_morphology = ['C', 'D']
    deathDiagnosisTypes = True

    def __init__(self, parent, mainDiagnosisTypeCode, accompDiagnosisTypeCode):
        CMKBListInDocTableModel.__init__(self, 'Diagnostic', 'id', 'event_id', parent)
        self.parent = parent
        self.isManualSwitchDiagnosis = QtGui.qApp.defaultIsManualSwitchDiagnosis()
        self.isMKBMorphology = QtGui.qApp.defaultMorphologyMKBIsVisible()
        self.characterIdForHandleDiagnosis = None
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
        self.addCol(CRBInDocTableCol(    u'Травма',        'traumaType_id', 10, 'rbTraumaType', addNone=True, showFields=CRBComboBox.showName, preferredWidth=150))
        self.addCol(CToxicSubstances(u'ТоксВещ', 'toxicSubstances_id', 10, addNone=True, showFields=CRBComboBox.showName, preferredWidth=150)).setToolTip(u'Токсичное вещество')
        self.addCol(CInDocTableCol(u'Описание',     'freeInput', 15))
        self.columnHandleDiagnosis = self.getColIndex('handleDiagnosis', None)
        db = QtGui.qApp.db
        self.mainDiagnosisTypeId   = forceRef(db.translate('rbDiagnosisType', 'code', mainDiagnosisTypeCode, 'id'))
        self.accompDiagnosisTypeId = forceRef(db.translate('rbDiagnosisType', 'code', accompDiagnosisTypeCode, 'id'))
        self.setFilter(self.table['diagnosisType_id'].inlist([self.mainDiagnosisTypeId, self.accompDiagnosisTypeId]))
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

    def getCloseOrMainDiagnosisTypeIdList(self):
        return []
    
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
                        # return result
            if self.isMKBMorphology and index.isValid():
                if column == self.getColIndex('morphologyMKB'):
                    mkb = forceString(self.items()[row].value('MKB'))
                    if not (bool(mkb) and mkb[0] in CF106DiagnosticsModel.MKB_allowed_morphology):
                        result = (result & ~Qt.ItemIsEditable)
            if QtGui.qApp.isExSubclassMKBVisible() and index.isValid():
                if column == self.getColIndex('exSubclassMKB'):
                    mkb = forceString(self.items()[row].value('MKB'))
                    if len(mkb) != 6:
                        return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return result


    def getDiagnosisTypeId(self, first):
        if first:
            return self.mainDiagnosisTypeId
        else:
            return self.accompDiagnosisTypeId


    def getEmptyRecord(self):
        isFirst = not bool(self.items())
        result = CMKBListInDocTableModel.getEmptyRecord(self)
        result.append(QtSql.QSqlField('diagnosis_id',     QVariant.Int))
        result.append(QtSql.QSqlField('diagnosisType_id', QVariant.Int))
        result.append(QtSql.QSqlField('speciality_id',    QVariant.Int))
        result.append(QtSql.QSqlField('person_id',        QVariant.Int))
        result.append(QtSql.QSqlField('dispanser_id',     QVariant.Int))
        result.append(QtSql.QSqlField('hospital',         QVariant.Int))
        result.append(QtSql.QSqlField('healthGroup_id',   QVariant.Int))
        result.append(QtSql.QSqlField('result_id',        QVariant.Int))
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
        result.append(QtSql.QSqlField('MKBAdditional_id', QVariant.Int))
        result.setValue('diagnosisType_id', QVariant(self.getDiagnosisTypeId(isFirst)))
        result.setValue('person_id',        QVariant(self.parent.personId))
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
            eventEditor = self.parent
            if column == self.getColIndex('MKB'):  # код МКБ

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
                    acceptable, specifiedMKB, specifiedMKBEx, specifiedCharacterId, specifiedTraumaTypeId, specifiedDispanserId, specifiedRequiresFillingDispanser, specifiedProlongMKB = self.parent.specifyDiagnosis(newMKB)
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
                return result
            if 0 <= row < len(self.items()) and column == self.getColIndex('MKBEx'):  # доп. код МКБ
                newMKB = forceString(value)
                if not newMKB:
                    pass
                else:
                    acceptable = self.parent.checkDiagnosis(newMKB)
                    if not acceptable:
                        return False
                value = toVariant(newMKB)
                result = CMKBListInDocTableModel.setData(self, index, value, role)
                # if result:
                #     self.updateCharacterByMKB(row, specifiedMKB)
                return result
            if QtGui.qApp.isTNMSVisible() and 0 <= row < len(self.items()) and column == self.getColIndex('TNMS'):
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
            if QtGui.qApp.isExSubclassMKBVisible() and 0 <= row < len(self.items()) and column == self.getColIndex('exSubclassMKB'):
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


class NotCRBInDocTableCol(CRBInDocTableCol):
    def __init__(self, title, fieldName, width, tableName, **params):
        CRBInDocTableCol.__init__(self, title, fieldName, width, tableName, **params)
        self.filter = {}  # свой фильтр у каждой строки
        self.view = params['view']

    def toString(self, val, record):
        variant = QtGui.qApp.db.translate(self.tableName, 'id', forceInt(val), 'name')
        if variant and variant.isValid() and not variant.isNull():
            return variant
        return toVariant(u'не задано')

    def toSortString(self, val, record):
        return forceString(self.toString(val, record))

    def getSortString(self, val, record):
        return self.toString(val, record)

    def toStatusTip(self, val, record):
        return self.toString(val, record)

    def createEditor(self, parent):
        filter = self.filter.get(self.view.currentIndex().row(), 'FALSE')
        records = QtGui.qApp.db.getRecordList(self.tableName, 'name', filter)
        items = [ u'не задано' ] + [ forceString(r.value('name')) for r in records ]
        editor = QtGui.QComboBox(parent)
        editor.addItems(items)
        return editor

    def setEditorData(self, editor, value, record):
        record = QtGui.qApp.db.getRecord(self.tableName, 'name', forceInt(value))
        if record:
            name = forceString(record.value('name'))
            index = editor.findText(name)
            editor.setCurrentIndex(max(index, 0))
        else:
            editor.setCurrentIndex(0)

    def getEditorData(self, editor):
        db = QtGui.qApp.db
        name = forceString(editor.currentText())
        if name == u'не задано':
            return toVariant(None)
        table = db.table(self.tableName)
        record = db.getRecordEx(table, 'id', table['name'].eq(name))
        if record:
            return record.value('id')
        return toVariant(None)


class CF106FinalDiagnosticsModel(CF106DiagnosticsModel):
    def __init__(self, parent, view):
        CF106DiagnosticsModel.__init__(self, parent, '4', '9')
        self.view = view

        cond = u"code LIKE '4%' OR code = '9'"
        idList = QtGui.qApp.db.getIdList('rbDiagnosisType', 'id', cond)
        self.setFilter('Diagnostic.diagnosisType_id IN (%s)' % ','.join(str(i) for i in idList))

        self.addCol(NotCRBInDocTableCol(u'ДСК', 'MKBAdditional_id', 10, 'MKBAdditionalSubclass',
                    addNone=True,
                    showFields=CRBComboBox.showName,
                    filter='FALSE',
                    view=self.view), 1)
        self.addCol(CRBInDocTableCol(u'Тип', 'diagnosisType_id', 10, 'rbDiagnosisType',
                    addNone=True,
                    showFields=CRBComboBox.showName,
                    filter="replaceInDiagnosis = '2'"), 0)

        self.dataChanged.connect(self.on_dataChanged)


    def setItems(self, items):
        CF106DiagnosticsModel.setItems(self, items)
        self.updateFilters(self._items)


    def addRecord(self, record):
        CF106DiagnosticsModel.addRecord(self, record)
        self.updateFilters(self._items)


    def updateFilters(self, records):
        MKBAdditionalColIndex = self.getColIndex('MKBAdditional_id')
        MkbAdditionalCol = self.cols()[MKBAdditionalColIndex]
        for row, record in enumerate(records):
            value = forceString(record.value('MKB'))
            MkbAdditionalCol.filter[row] = ("MKB = '%s'" % value) if value else 'FALSE'


    def on_dataChanged(self, topLeft, bottomRight, roles=None):
        MKBColIndex = self.getColIndex('MKB')
        row = self.view.currentIndex().row()
        col = self.view.currentIndex().column()
        if col == MKBColIndex:
            MKBAdditionalColIndex = self.getColIndex('MKBAdditional_id')
            MkbAdditionalCol = self.cols()[MKBAdditionalColIndex]
            modelIndex = self.index(row, MKBColIndex)
            value = forceString(self.data(modelIndex))
            MkbAdditionalCol.filter[row] = ("MKB = '%s'" % value) if value else 'FALSE'
