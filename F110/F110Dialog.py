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
## Форма 110/У: Станция скорой медицинской помощи
##
#############################################################################

from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import Qt, QDate, QDateTime, QModelIndex, QObject, QTime, QVariant, pyqtSignature, SIGNAL

from Events.RelatedEventAndActionListDialog import CRelatedEventAndActionListDialog
from library.Attach.AttachAction import getAttachAction
from library.Utils import forceString, forceRef, toVariant, forceInt, forceDate, copyFields, disassembleSeconds, \
    forceStringEx, forceBool, formatNum, variantEq
from library.ICDInDocTableCol   import CICDExInDocTableCol
from library.ICDMorphologyInDocTableCol import CMKBMorphologyCol
from library.InDocTable         import CMKBListInDocTableModel, CInDocTableModel,  CBoolInDocTableCol, CInDocTableCol, CRBInDocTableCol, CRBLikeEnumInDocTableCol
from library.interchange        import getDatetimeEditValue, getLineEditValue, getRBComboBoxValue, getTextEditValue, setComboBoxValue, setDatetimeEditValue, setLineEditValue, setRBComboBoxValue, setTextEditValue
from library.ItemsListDialog    import CItemEditorBaseDialog
from library.PrintInfo          import CDateInfo, CDateTimeInfo, CInfoContext
from library.PrintTemplates     import applyTemplate, customizePrintButton, getPrintButton
from library.TNMS.TNMSComboBox import CTNMSCol
from library.MKBExSubclassComboBox import CMKBExSubclassCol
from library.crbcombobox import CRBComboBox

from Events.ActionInfo          import CActionInfoProxyList
from Events.ActionsSummaryModel import CActionsSummaryModel
from Events.DiagnosisType       import CDiagnosisTypeCol
from Events.EventEditDialog     import CEventEditDialog, CDiseaseCharacter, CDiseaseStage, CDiseasePhases, CToxicSubstances, getToxicSubstancesIdListByMKB
from Events.EventInfo           import CDiagnosticInfoProxyList, CEmergencyAccidentInfo, CEmergencyBrigadeInfo, CEmergencyCauseCallInfo, CEmergencyDeathInfo, CEmergencyDiseasedInfo, CEmergencyEbrietyInfo, CEmergencyEventInfo, CEmergencyMethodTransportInfo, CEmergencyPlaceCallInfo, CEmergencyPlaceReceptionCallInfo, CEmergencyReasondDelaysInfo, CEmergencyReceivedCallInfo, CEmergencyResultInfo, CEmergencyTransferTransportInfo, CEmergencyTypeAssetInfo, CHospitalInfo
from Events.Utils               import checkDiagnosis, checkIsHandleDiagnosisIsChecked, getAvailableCharacterIdByMKB, getDiagnosisId2, getEventDurationRange, getEventMesRequired, getEventResultId, getEventSetPerson, getEventShowTime, setAskedClassValueForDiagnosisManualSwitch, getEventIsPrimary
from F110.PreF110Dialog         import CPreF110Dialog, CPreF110DagnosticAndActionPresets
from Orgs.PersonComboBoxEx      import CPersonFindInDocTableCol
from Orgs.PersonInfo            import CPersonInfo
from Orgs.Utils                 import COrgStructureInfo
from Registry.ClientHousesList  import CClientHousesList
from Registry.Utils             import getAddress, getAddressId
from Users.Rights                import urAccessF110planner, urAdmin, urEditEndDateEvent, urRegTabWriteRegistry, urRegTabReadRegistry, urCanReadClientVaccination, urCanEditClientVaccination

from F110.Ui_F110               import Ui_Dialog


def formatDisassembledSeconds(secs):
    days, hours, minutes, seconds = disassembleSeconds(secs)
    result = u''

    if hours > 0:
        if hours > 9:
            result += u'%d' % (hours)
        else:
            result += u'0%d' % (hours)
    else:
        hours = 0
        result += u'00'

    if seconds > 29:
        minutes += 1
    if minutes > 0:
        if minutes > 9:
            result += u':%d  ' % (minutes)
        else:
            result += u':0%d  ' % (minutes)
    else:
        result += u':00  '

    if days > 0:
        result += formatNum(days, (u'день', u'дня', u'дней'))
    return result


class CEmergencyCallEditDialog(CItemEditorBaseDialog):
    def __init__(self, parent):
        CItemEditorBaseDialog.__init__(self, parent, 'EmergencyCall')


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)


    def getRecord(self):
        if not self.record():
            record = CItemEditorBaseDialog.getRecord(self)
        else:
            record = self.record()
        return record


    def saveEmergencyCall(self):
        self.save()


class CF110Dialog(CEventEditDialog, Ui_Dialog, CEmergencyCallEditDialog):
    defaultEventResultId = None
    defaultDiagnosticResultId = None
    dfAccomp = 2 # Сопутствующий

    def __init__(self, parent):
# ctor
        CEventEditDialog.__init__(self, parent)
        self.EmergencyCallEditDialog = CEmergencyCallEditDialog(self)
        self.mapSpecialityIdToDiagFilter = {}

# create models
        self.addModels('Personnel', CF110PersonnelModel(self))
        self.addModels('FinalDiagnostics', CF110FinalDiagnosticsModel(self))
        self.addModels('ActionsSummary', CActionsSummaryModel(self, True))
# ui
        self.addObject('actEditClient', QtGui.QAction(u'Открыть регистрационную карточку', self))
        self.addObject('actPortal_Doctor', QtGui.QAction(u'Перейти на портал врача', self))
        self.addObject('actShowAttachedToClientFiles', getAttachAction('Client_FileAttach',  self))
        self.addObject('actShowContingentsClient', QtGui.QAction(u'Показать все наблюдаемые контингенты', self))
        self.addObject('actOpenClientVaccinationCard', QtGui.QAction(u'Открыть прививочную карту', self))
        self.setupActionsMenu()
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
        self.setWindowTitleEx(u'Осмотр Ф.110')
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
        self.cmbOrgId.setIsMedical(2)
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
        self.buttonBox.addButton(self.btnPrint, QtGui.QDialogButtonBox.ActionRole)
        if QtGui.qApp.defaultKLADR()[:2] in ['23', '01']:
            self.buttonBox.addButton(self.btnPlanning, QtGui.QDialogButtonBox.ActionRole)
        # self.buttonBox.addButton(self.btnMedicalCommission, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnRelatedEvent, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnTemperatureList, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnPrintMedicalDiagnosis, QtGui.QDialogButtonBox.ActionRole)
        self.setupActionSummarySlots()
# tables to rb and combo-boxes

# assign models
        self.tblPersonnel.setModel(self.modelPersonnel)
        self.tblFinalDiagnostics.setModel(self.modelFinalDiagnostics)
        self.modelActionsSummary.addModel(self.tabStatus.modelAPActions)
        self.modelActionsSummary.addModel(self.tabDiagnostic.modelAPActions)
        self.modelActionsSummary.addModel(self.tabCure.modelAPActions)
        self.modelActionsSummary.addModel(self.tabMisc.modelAPActions)
        self.tabCash.addActionModel(self.tabStatus.modelAPActions)
        self.tabCash.addActionModel(self.tabDiagnostic.modelAPActions)
        self.tabCash.addActionModel(self.tabCure.modelAPActions)
        self.tabCash.addActionModel(self.tabMisc.modelAPActions)

# popup menus
        self.txtClientInfoBrowser.actions.append(self.actEditClient)
        self.txtClientInfoBrowser.actions.append(self.actPortal_Doctor)
        self.txtClientInfoBrowser.actions.append(self.actShowAttachedToClientFiles)
        self.txtClientInfoBrowser.actions.append(self.actShowContingentsClient)
        self.txtClientInfoBrowser.actions.append(self.actOpenClientVaccinationCard)
        self.actOpenClientVaccinationCard.setEnabled(QtGui.qApp.userHasAnyRight([urCanReadClientVaccination, urCanEditClientVaccination]))
        self.actEditClient.setEnabled(QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]))
        self.tblFinalDiagnostics.addPopupDelRow()
        self.tblPersonnel.addPopupDelRow()

# default values
        self.setupDirtyCather()
        self.setIsDirty(False)
        self.blankMovingIdList = []
        self.clientId = None
        self.tabNotes.setEventEditor(self)
        self.setupVisitsIsExposedPopupMenu()

        self.postSetupUi()
        if hasattr(self, 'edtEndDate'):
            self.edtEndDate.setEnabled(QtGui.qApp.userHasRight(urEditEndDateEvent))
        if hasattr(self, 'edtEndTime'):
            self.edtEndTime.setEnabled(QtGui.qApp.userHasRight(urEditEndDateEvent))
        self.clientLocHousesList = CClientHousesList(parent)
        self.cmbLocCity.setCode(QtGui.qApp.defaultKLADR())
        self.btnPrintMedicalDiagnosis.setVisible(False)
# done


    def destroy(self):
        CEventEditDialog.deleteLater(self)
        self.tblPersonnel.setModel(None)
        self.tblFinalDiagnostics.setModel(None)
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
        del self.modelPersonnel
        del self.modelFinalDiagnostics
        self.tabAmbCard.deleteLater()


#    def currentClientId(self): # for AmbCard mixin
#        return self.clientId


    @pyqtSignature('int')
    def on_cmbLocCity_currentIndexChanged(self,  index):
        code = self.cmbLocCity.code()
        self.cmbLocStreet.setCity(code)


    def setClientId(self, clientId):
        self.clientId = clientId
        self.updateClientInfo()
        if hasattr(self.clientInfo, 'locAddressInfo'):
            self.setLocAddress(self.clientInfo.locAddressInfo)
        if hasattr(self, 'tabAmbCard'):
            self.tabAmbCard.setClientId(clientId, self.clientSex, self.clientAge)


    def setLocAddress(self, locAddress):
        if locAddress:
            self.cmbLocCity.setCode(locAddress.KLADRCode)
            self.cmbLocStreet.setCity(locAddress.KLADRCode)
            self.cmbLocStreet.setCode(locAddress.KLADRStreetCode)
            self.edtLocHouse.setText(locAddress.number)
            self.edtLocCorpus.setText(locAddress.corpus)
            self.edtLocFlat.setText(locAddress.flat)
        else:
            self.cmbLocCity.setCode(QtGui.qApp.defaultKLADR())
            self.cmbLocStreet.setCity(QtGui.qApp.defaultKLADR())
            self.cmbLocStreet.setCode('')
            self.edtLocHouse.setText('')
            self.edtLocCorpus.setText('')
            self.edtLocFlat.setText('')


    def setLocAddressRecord(self, addressId):
        if addressId:
            locAddress = getAddress(addressId)
        else:
            locAddress = None
        self.setLocAddress(locAddress)


    @pyqtSignature('')
    def on_btnLocHouseList_clicked(self):
        streetCode = forceString(self.cmbLocStreet.code())
        if not streetCode:
            cityCode = forceString(self.cmbLocCity.code())
            streetCode = cityCode + u'000000'
        self.getHouseList(streetCode, 1)


    def getHouseList(self, streetCode, typeAddress):
        if streetCode:
            house = forceString(self.edtLocHouse.text())
            corp = forceString(self.edtLocCorpus.text())
            house, corp = self.clientLocHousesList.showHousesList(streetCode, house, corp)
            self.edtLocHouse.setText(house)
            self.edtLocCorpus.setText(corp)


    @pyqtSignature('')
    def on_btnTemperatureList_clicked(self):
        self.getTemperatureList(self.eventSetDateTime)


    def setupActionsMenu(self):
        self.addObject('mnuAction', QtGui.QMenu(self))
        self.addObject('actActionEdit', QtGui.QAction(u'Перейти к редактированию', self))
        self.actActionEdit.setShortcut(Qt.Key_F4)
        self.mnuAction.addAction(self.actActionEdit)


    def _prepare(self, clientId, eventTypeId, orgId, personId, eventSetDatetime, eventDatetime, weekProfile, numDays,
                 presetDiagnostics, presetActions, disabledActions, externalId, assistantId, curatorId,
                 actionTypeIdValue = None, valueProperties = [], relegateOrgId = None, relegatePersonId=None,
                 actionByNewEvent = [], eventOrder = 1, relegateInfo=[], plannedEndDate = None, isEdit = False):
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

        def prepNumberBrigade(personId):
            numberBrigade = None
            if personId:
                numberBrigade = forceRef(QtGui.qApp.db.translate('EmergencyBrigade_Personnel', 'person_id', personId, 'master_id'))
            return numberBrigade

        def prepPersonnelBrigade(numberBrigade = None):
            if numberBrigade:
                visits = []
                db = QtGui.qApp.db
                tablePersonnel = db.table('EmergencyBrigade_Personnel')
                records = db.getRecordList(tablePersonnel, [tablePersonnel['person_id']], [tablePersonnel['master_id'].eq(numberBrigade)], 'idx')
                for record in records:
                    visit = self.modelPersonnel.getEmptyRecord()
                    person_Id = forceRef(record.value('person_id'))
                    if person_Id:
                        visit.setValue('person_id', toVariant(person_Id))
                        visits.append(visit)
                self.modelPersonnel.setItems(visits)

        def prepOrgStructure(clientId):
            db = QtGui.qApp.db
            tableClientAttach = db.table('ClientAttach')
            cond = [tableClientAttach['id'].eqEx('getClientAttachIdForDate(%i, 0, %s)'%(clientId, db.formatDate(self.eventSetDateTime)))]
            record = db.getRecordEx(tableClientAttach, '*', cond)
            if record:
                lpuId = forceRef(record.value('LPU_id'))
                if lpuId == QtGui.qApp.currentOrgId():
                    orgStructure = forceRef(record.value('orgStructure_id'))
                    if orgStructure:
                        self.cmbOrgStructure.setValue(orgStructure)
        
        if not isEdit:
            self.eventSetDateTime = eventSetDatetime if isinstance(eventSetDatetime, QDateTime) else QDateTime(eventSetDatetime)
            self.eventDate = eventDatetime.date() if isinstance(eventDatetime, QDateTime) else QDate(eventDatetime)
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
            brigadeId = prepNumberBrigade(personId)
            if brigadeId:
                self.cmbNumberBrigade.setValue(brigadeId)
            self.edtBegDate.setDate(self.eventSetDateTime.date())
            self.edtBegTime.setTime(eventSetDatetime.time() if isinstance(eventSetDatetime, QDateTime) else QTime())
            self.edtPassDate.setDate(self.edtBegDate.date())
            self.edtPassTime.setTime(self.edtBegTime.time())
            self.edtDepartureDate.setDate(self.edtBegDate.date())
            self.edtDepartureTime.setTime(self.edtBegTime.time())
            self.edtArrivalDate.setDate(self.edtBegDate.date())
            self.edtArrivalTime.setTime(self.edtBegTime.time())
            self.edtFinishServiceDate.setDate(self.eventDate)
            self.edtFinishServiceTime.setTime(eventDatetime.time() if isinstance(eventDatetime, QDateTime) else QTime())
            self.edtEndDate.setDate(QDate())
            self.edtEndTime.setTime(QTime())
            self.edtNextDate.setDate(QDate())
            self.edtNextTime.setTime(QTime())
            self.cmbDispatcher.setCurrentIndex(0)
            self.cmbOrder.setCurrentIndex(getEventIsPrimary(eventTypeId))
            self.cmbOrderEvent.setCurrentIndex(eventOrder)
            self.cmbContract.setCurrentIndex(0)
            self.cmbTypeAsset.setCurrentIndex(0)
            self.edtNextDate.setEnabled(False)
            self.edtNextTime.setEnabled(False)
            self.cmbCauseCall.setCurrentIndex(0)
            self.cmbPlaceReceptionCall.setCurrentIndex(0)
            self.cmbReceivedCall.setCurrentIndex(0)
            self.cmbReasondDelays.setCurrentIndex(0)
            self.cmbResultCircumstanceCall.setCurrentIndex(0)
            self.cmbAccident.setCurrentIndex(0)
            self.cmbDeath.setCurrentIndex(0)
            self.cmbEbriety.setCurrentIndex(0)
            self.cmbDiseased.setCurrentIndex(0)
            self.cmbPlaceCall.setCurrentIndex(0)
            self.cmbMethodTransportation.setCurrentIndex(0)
            self.cmbTransferredTransportation.setCurrentIndex(0)

            visitTypeId = presetDiagnostics[0][3] if presetDiagnostics else None
            self.modelPersonnel.setDefaultVisitTypeId(visitTypeId)
            prepPersonnelBrigade(brigadeId)

            if presetDiagnostics:
                model = self.modelFinalDiagnostics
                if model:
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
            resultId = QtGui.qApp.session("F110_resultId")
            if resultId:
                self.cmbResult.setValue(resultId)
        self.prepareActions(presetActions, disabledActions, actionTypeIdValue, valueProperties)
        self.grpTempInvalid.pickupTempInvalid()
        self.grpAegrotat.pickupTempInvalid()
        self.grpDisability.pickupTempInvalid()
        self.grpVitalRestriction.pickupTempInvalid()
        self.setIsDirty(False)
        self.tabNotes.setEventEditor(self)
        prepOrgStructure(clientId)
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
        if QtGui.qApp.userHasRight(urAccessF110planner):
            dlg = CPreF110Dialog(self, self.contractTariffCache)
            try:
                dlg.setBegDateEvent(eventSetDatetime.date() if isinstance(eventSetDatetime, QDateTime) else eventSetDatetime)
                dlg.prepare(clientId, eventTypeId, eventDate, self.personId, self.personSpecialityId, self.personTariffCategoryId, 
                            flagHospitalization, actionTypeIdValue, tissueTypeId, presentActionTypes = presentActionTypes)
                if dlg.diagnosticsTableIsNotEmpty() or dlg.actionsTableIsNotEmpty():
                    if not dlg.exec_():
                        return False
                return self._prepare(clientId, eventTypeId, orgId, personId, eventSetDatetime, eventDatetime, weekProfile, numDays,
                                     dlg.diagnostics(), dlg.actions(), dlg.disabledActionTypeIdList, externalId, assistantId, curatorId,
                                     actionTypeIdValue, valueProperties, relegateOrgId, relegatePersonId, actionByNewEvent,
                                     order, relegateInfo, plannedEndDate, isEdit)
            finally:
                dlg.deleteLater()
        else:
            presets = CPreF110DagnosticAndActionPresets(clientId, eventTypeId, eventDate, self.personSpecialityId, flagHospitalization, actionTypeIdValue, presentActionTypes = presentActionTypes)
            presets.setBegDateEvent(eventSetDatetime.date() if isinstance(eventSetDatetime, QDateTime) else eventSetDatetime)
            return self._prepare(clientId, eventTypeId, orgId, personId, eventSetDatetime, eventDatetime, weekProfile, numDays,
                                 presets.unconditionalDiagnosticList, presets.unconditionalActionList, presets.disabledActionTypeIdList,
                                 externalId, assistantId, curatorId, None, [], relegateOrgId, relegatePersonId, actionByNewEvent,
                                     order, relegateInfo, plannedEndDate, isEdit)


    def prepareActions(self, presetActions, disabledActions, actionTypeIdValue, valueProperties):
        def addActionType(actionTypeId, amount, idListActionType):
            db = QtGui.qApp.db
            tableOrgStructure = db.table('OrgStructure')
            for iModel, model in enumerate([self.tabStatus.modelAPActions,
                          self.tabDiagnostic.modelAPActions,
                          self.tabCure.modelAPActions,
                          self.tabMisc.modelAPActions]):
                if actionTypeId in model.actionTypeIdList:
                    model.addRow(actionTypeId, amount)
                    i = self.modelActionsSummary.itemIndex.index((iModel, model.rowCount()-2))
                    self.onActionChanged(i)
                    if actionTypeId in idListActionType:
                        record, action = model.items()[-1]
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
                    break

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
            idListActionType = db.getIdList(tableActionType, [tableActionType['id']], [tableActionType['flatCode'].like(u'received%'), tableActionType['deleted'].eq(0)])
            for actionTypeId, amount, cash in presetActions:
                addActionType(actionTypeId, amount, idListActionType)


    def initFocus(self):
        if len(self.edtNumberCardCall.text()) == 0:
            self.edtNumberCardCall.setFocus(Qt.OtherFocusReason)
        else:
            self.tblFinalDiagnostics.setFocus(Qt.OtherFocusReason)


    def setRecord(self, record):
        CEventEditDialog.setRecord(self, record)
        setDatetimeEditValue(self.edtBegDate, self.edtBegTime, record, 'setDate')
        setDatetimeEditValue(self.edtNextDate, self.edtNextTime, record, 'nextEventDate')
        setRBComboBoxValue(self.cmbPerson,      record, 'execPerson_id')
        setRBComboBoxValue(self.cmbDispatcher,  record, 'curator_id')
        setRBComboBoxValue(self.cmbResult,      record, 'result_id')
        self.cmbOrder.setCurrentIndex(forceInt(record.value('isPrimary'))-1)
        self.cmbOrderEvent.setCurrentIndex(forceInt(record.value('order'))-1)
        self.setExternalId(forceString(record.value('externalId')))
        setComboBoxValue(self.cmbTypeAsset,     record, 'typeAsset_id')
        self.setPerson = forceRef(record.value('setPerson_id'))
        if not self.cmbTypeAsset.value():
            self.edtNextDate.setEnabled(False)
            self.edtNextTime.setEnabled(False)
        self.setPersonId(self.cmbPerson.value())
        setRBComboBoxValue(self.cmbContract, record, 'contract_id')
        self.tabNotes.setNotes(record)
        self.tabNotes.setEventEditor(self)
        self.loadDiagnostics(self.modelFinalDiagnostics)
        self.tabMedicalDiagnosis.load(self.itemId())
        self.loadPersonnel()
        self.grpTempInvalid.pickupTempInvalid()
        self.grpAegrotat.pickupTempInvalid()
        self.grpDisability.pickupTempInvalid()
        self.grpVitalRestriction.pickupTempInvalid()
        self.updateMesMKB()
        self.tabMes.setRecord(record)
        self.loadActions()
        self.on_cmbResult_currentIndexChanged()
        self.initFocus()
        self.tabCash.load(self.itemId())
        self.setIsDirty(False)
        self.loadEmergencyCall(forceRef(record.value('id')))
        self.cmbNumberBrigade.setEnabled(False)
        self.initFocus()
        self.blankMovingIdList = []
        self.protectClosedEvent()
        self.btnRelatedEventHighlight()


    def setRecordEmergencyCall(self, record):
        self.EmergencyCallEditDialog.setRecord(record)
        setDatetimeEditValue(self.edtEndDate, self.edtEndTime, record, 'endDate')
        setDatetimeEditValue(self.edtPassDate, self.edtPassTime, record, 'passDate')
        setDatetimeEditValue(self.edtDepartureDate, self.edtDepartureTime, record, 'departureDate')
        setDatetimeEditValue(self.edtArrivalDate, self.edtArrivalTime, record, 'arrivalDate')
        setDatetimeEditValue(self.edtFinishServiceDate, self.edtFinishServiceTime, record, 'finishServiceDate')
        setLineEditValue(self.edtWhoCallOnPhone, record, 'whoCallOnPhone')
        setLineEditValue(self.edtNumberPhone, record, 'numberPhone')
        setLineEditValue(self.edtStorey, record, 'storey')
        setLineEditValue(self.edtEntrance, record, 'entrance')
        setTextEditValue(self.edtAdditional, record, 'additional')
        setLineEditValue(self.edtNumberEpidemic, record, 'numberEpidemic')
        setLineEditValue(self.edtOrderNumber, record, 'order')
        setLineEditValue(self.edtNumberCardCall, record, 'numberCardCall')
        setLineEditValue(self.edtFaceRenunOfHospital, record, 'faceRenunOfHospital')
        self.grpRenunOfHospital.setChecked(forceInt(record.value('renunOfHospital')))
        self.chkDisease.setChecked(forceInt(record.value('disease')))
        self.chkBirth.setChecked(forceInt(record.value('birth')))
        self.chkPregnancyFailure.setChecked(forceInt(record.value('pregnancyFailure')))
        self.chkPregnancy.setChecked(forceInt(record.value('pregnancy')))
        setRBComboBoxValue(self.cmbNumberBrigade,             record, 'brigade_id')
        self.cmbNumberBrigade.setEnabled(False)
        setRBComboBoxValue(self.cmbCauseCall,                 record, 'causeCall_id')
        setRBComboBoxValue(self.cmbPlaceReceptionCall,        record, 'placeReceptionCall_id')
        setRBComboBoxValue(self.cmbReceivedCall,              record, 'receivedCall_id')
        setRBComboBoxValue(self.cmbReasondDelays,             record, 'reasondDelays_id')
        setRBComboBoxValue(self.cmbResultCircumstanceCall,    record, 'resultCall_id')
        setRBComboBoxValue(self.cmbAccident,                  record, 'accident_id')
        setRBComboBoxValue(self.cmbDeath,                     record, 'death_id')
        setRBComboBoxValue(self.cmbEbriety,                   record, 'ebriety_id')
        setRBComboBoxValue(self.cmbDiseased,                  record, 'diseased_id')
        setRBComboBoxValue(self.cmbPlaceCall,                 record, 'placeCall_id')
        setRBComboBoxValue(self.cmbMethodTransportation,      record, 'methodTransport_id')
        setRBComboBoxValue(self.cmbTransferredTransportation, record, 'transfTransport_id')
        setRBComboBoxValue(self.cmbGuidePerson,               record, 'guidePerson_id')
        setRBComboBoxValue(self.cmbOrgStructure,              record, 'orgStructure_id')
        setRBComboBoxValue(self.cmbOrgId,                     record, 'org_id')
        self.setLocAddressRecord(forceRef(record.value('address_id')))
        self.calculationTimeTo()


    def loadEmergencyCall(self, id):
        db = QtGui.qApp.db
        table = db.table('EmergencyCall')
        record = db.getRecordEx(table, '*', table['event_id'].eq(id))
        if record:
            self.setRecordEmergencyCall(record)


    def loadPersonnel(self):
        self.modelPersonnel.loadItems(self.itemId())


    def loadDiagnostics(self, modelDiagnostics):
        db = QtGui.qApp.db
        table = db.table('Diagnostic')
#        tablePerson = db.table('Person')
        isDiagnosisManualSwitch = modelDiagnostics.manualSwitchDiagnosis()
        rawItems = db.getRecordList(table, '*', [table['deleted'].eq(0), table['event_id'].eq(self.itemId()), modelDiagnostics.filter], 'id')
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
            if isDiagnosisManualSwitch:
                isCheckedHandleDiagnosis = checkIsHandleDiagnosisIsChecked(setDate,
                                                                           self.clientId,
                                                                           diagnosisId)
                newRecord.setValue('handleDiagnosis', QVariant(isCheckedHandleDiagnosis))

            items.append(newRecord)
        modelDiagnostics.setItems(items)


    def getRecord(self):
        record = CEventEditDialog.getRecord(self)
        showTime = getEventShowTime(self.eventTypeId)
        self.getShowButtonAccount()
        self.getShowButtonTemperatureList()
        self.getShowButtonNomenclatureExpense()
        self.getShowButtonJobTickets()
#перенести в exec_ в случае успеха или в accept?
        CF110Dialog.defaultEventResultId = self.cmbResult.value()

        getRBComboBoxValue(self.cmbContract,    record, 'contract_id')
        getDatetimeEditValue(self.edtBegDate, self.edtBegTime, record, 'setDate', showTime)
        getDatetimeEditValue(self.edtNextDate, self.edtNextTime, record, 'nextEventDate', showTime)
        record.setValue('setPerson_id', self.setPerson)
        getDatetimeEditValue(self.edtFinishServiceDate, self.edtFinishServiceTime, record, 'execDate', showTime)
        getRBComboBoxValue(self.cmbPerson,      record, 'execPerson_id')
        getRBComboBoxValue(self.cmbDispatcher,  record, 'curator_id')
        getRBComboBoxValue(self.cmbResult,      record, 'result_id')
        record.setValue('isPrimary', toVariant(self.cmbOrder.currentIndex()+1))
        record.setValue('order',  toVariant(self.cmbOrderEvent.currentIndex()+1))
        typeAssetId = self.cmbTypeAsset.currentIndex()
        record.setValue('typeAsset_id', toVariant(typeAssetId if typeAssetId != 0 else None))
###  payStatus
        self.tabMes.getRecord(record)
        self.tabNotes.getNotes(record, self.eventTypeId)
        # Это хак: удаляем payStatus из записи
        result = type(record)(record) # copy record
        result.remove(result.indexOf('payStatus'))
        return result


    def saveInternals(self, eventId):
        self.savePersonnel(eventId)
        self.saveDiagnostics(self.modelFinalDiagnostics, eventId)
        self.tabMedicalDiagnosis.save(eventId)
        self.tabMes.save(eventId)
        setAskedClassValueForDiagnosisManualSwitch(None)
        self.saveActions(eventId)
        self.getRecordEmergencyCall(eventId)
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
        QtGui.qApp.session("F110_resultId", self.cmbResult.value())


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
        self.calculationTimeTo()


    @pyqtSignature('QTime')
    def on_edtBegTime_timeChanged(self, time):
        self.eventSetDateTime.setTime(time)
        self.emitUpdateActionsAmount()
        self.calculationTimeTo()


    @pyqtSignature('QDate')
    def on_edtPassDate_dateChanged(self, date):
        self.calculationTimeTo()


    @pyqtSignature('QTime')
    def on_edtPassTime_timeChanged(self, time):
        self.calculationTimeTo()


    @pyqtSignature('QDate')
    def on_edtDepartureDate_dateChanged(self, date):
        self.calculationTimeTo()


    @pyqtSignature('QTime')
    def on_edtDepartureTime_timeChanged(self, time):
        self.calculationTimeTo()


    @pyqtSignature('QDate')
    def on_edtArrivalDate_dateChanged(self, date):
        self.calculationTimeTo()


    @pyqtSignature('QTime')
    def on_edtArrivalTime_timeChanged(self, time):
        self.calculationTimeTo()


    @pyqtSignature('QDate')
    def on_edtFinishServiceDate_dateChanged(self, date):
        self.eventDate = QDate(date)
        self.cmbContract.setDate(self.getDateForContract())
        self.emitUpdateActionsAmount()
        self.calculationTimeTo()


    @pyqtSignature('QTime')
    def on_edtFinishServiceTime_timeChanged(self, time):
        self.emitUpdateActionsAmount()
        self.calculationTimeTo()


    @pyqtSignature('QDate')
    def on_edtEndDate_dateChanged(self, date):
        if getEventShowTime(self.eventTypeId):
            time = QTime.currentTime() if date else QTime()
            self.edtEndTime.setTime(time)
        self.calculationTimeTo()


    @pyqtSignature('QTime')
    def on_edtEndTime_timeChanged(self, time):
        self.calculationTimeTo()


    def calculationTimeTo(self):
        begDateTime = QDateTime()
        passDateTime = QDateTime()
        departureDateTime = QDateTime()
        arrivalDateTime = QDateTime()
        finishServiceDateTime = QDateTime()
        endDateTime = QDateTime()
        begDateTime.setDate(self.edtBegDate.date())
        begDateTime.setTime(self.edtBegTime.time())
        passDateTime.setDate(self.edtPassDate.date())
        passDateTime.setTime(self.edtPassTime.time())
        departureDateTime.setDate(self.edtDepartureDate.date())
        departureDateTime.setTime(self.edtDepartureTime.time())
        arrivalDateTime.setDate(self.edtArrivalDate.date())
        arrivalDateTime.setTime(self.edtArrivalTime.time())
        finishServiceDateTime.setDate(self.edtFinishServiceDate.date())
        finishServiceDateTime.setTime(self.edtFinishServiceTime.time())
        endDateTime.setDate(self.edtEndDate.date())
        endDateTime.setTime(self.edtEndTime.time())
        if endDateTime.date() and begDateTime <= endDateTime:
            self.lblVisitsDurationValue.setText(formatDisassembledSeconds(begDateTime.secsTo(endDateTime)))
        elif begDateTime <= finishServiceDateTime and not endDateTime.date():
                self.lblVisitsDurationValue.setText(formatDisassembledSeconds(begDateTime.secsTo(finishServiceDateTime)))
        else:
            self.lblVisitsDurationValue.setText(u'--:--')
        if begDateTime <= passDateTime:
            self.lblTimeToPassDate.setText(formatDisassembledSeconds(begDateTime.secsTo(passDateTime)))
        else:
            self.lblTimeToPassDate.setText(u'--:--')
        if  passDateTime <= departureDateTime:
            self.lblTimeToDepartureDate.setText(formatDisassembledSeconds(passDateTime.secsTo(departureDateTime)))
        else:
            self.lblTimeToDepartureDate.setText(u'--:--')
        if departureDateTime <= arrivalDateTime:
            self.lblTimeToArrivalDate.setText(formatDisassembledSeconds(departureDateTime.secsTo(arrivalDateTime)))
        else:
            self.lblTimeToArrivalDate.setText(u'--:--')
        if arrivalDateTime <= finishServiceDateTime:
            self.lblTimeToFinishServiceDate.setText(formatDisassembledSeconds(arrivalDateTime.secsTo(finishServiceDateTime)))
        else:
            self.lblTimeToFinishServiceDate.setText(u'--:--')
        if endDateTime.date() and finishServiceDateTime.date() and finishServiceDateTime <= endDateTime:
            self.lblTimeToEndDate.setText(formatDisassembledSeconds(finishServiceDateTime.secsTo(endDateTime)))
        else:
            self.lblTimeToEndDate.setText(u'--:--')


    def getAddress(self):
        return { 'useKLADR'         : True,
                 'KLADRCode'        : self.cmbLocCity.code(),
                 'KLADRStreetCode'  : self.cmbLocStreet.code() if self.cmbLocStreet.code() else '', # без этого наростают адреса
                 'number'           : forceStringEx(self.edtLocHouse.text()),
                 'corpus'           : forceStringEx(self.edtLocCorpus.text()),
                 'flat'             : forceStringEx(self.edtLocFlat.text()),
                 'freeInput'        : ''}


    def getAddressRecord(self):
        address = self.getAddress()
        if address['useKLADR']:
            addressId = getAddressId(address)
        else:
            addressId = None
        return addressId


    def getRecordEmergencyCall(self, eventId):
        showTime = True
        record = self.EmergencyCallEditDialog.getRecord()
        record.setValue('event_id', toVariant(eventId))
        record.setValue('pregnancyFailure', toVariant(self.chkPregnancyFailure.isChecked()))
        record.setValue('pregnancy', toVariant(self.chkPregnancy.isChecked()))
        record.setValue('birth', toVariant(self.chkBirth.isChecked()))
        record.setValue('disease', toVariant(self.chkDisease.isChecked()))
        record.setValue('renunOfHospital', toVariant(self.grpRenunOfHospital.isChecked()))
        getLineEditValue(self.edtWhoCallOnPhone, record, 'whoCallOnPhone')
        getLineEditValue(self.edtNumberPhone, record, 'numberPhone')
        getLineEditValue(self.edtStorey, record, 'storey')
        getLineEditValue(self.edtEntrance, record, 'entrance')
        getTextEditValue(self.edtAdditional, record, 'additional')
        getLineEditValue(self.edtNumberEpidemic, record, 'numberEpidemic')
        getLineEditValue(self.edtOrderNumber, record, 'order')
        getLineEditValue(self.edtNumberCardCall, record, 'numberCardCall')
        getLineEditValue(self.edtFaceRenunOfHospital, record, 'faceRenunOfHospital')
        getDatetimeEditValue(self.edtBegDate, self.edtBegTime, record, 'begDate', showTime)
        getDatetimeEditValue(self.edtPassDate, self.edtPassTime, record, 'passDate', showTime)
        getDatetimeEditValue(self.edtDepartureDate, self.edtDepartureTime, record, 'departureDate', showTime)
        getDatetimeEditValue(self.edtArrivalDate, self.edtArrivalTime, record, 'arrivalDate', showTime)
        getDatetimeEditValue(self.edtEndDate, self.edtEndTime, record, 'endDate', showTime)
        getDatetimeEditValue(self.edtFinishServiceDate, self.edtFinishServiceTime, record, 'finishServiceDate', showTime)
        getRBComboBoxValue(self.cmbNumberBrigade,    record, 'brigade_id')
        getRBComboBoxValue(self.cmbDiseased,    record, 'diseased_id')
        getRBComboBoxValue(self.cmbPlaceCall,   record, 'placeCall_id')
        getRBComboBoxValue(self.cmbMethodTransportation, record, 'methodTransport_id')
        getRBComboBoxValue(self.cmbTransferredTransportation, record, 'transfTransport_id')
        getRBComboBoxValue(self.cmbGuidePerson, record, 'guidePerson_id')
        getRBComboBoxValue(self.cmbCauseCall, record, 'causeCall_id')
        getRBComboBoxValue(self.cmbPlaceReceptionCall,    record, 'placeReceptionCall_id')
        getRBComboBoxValue(self.cmbReceivedCall,    record, 'receivedCall_id')
        getRBComboBoxValue(self.cmbReasondDelays,    record, 'reasondDelays_id')
        getRBComboBoxValue(self.cmbResultCircumstanceCall,    record, 'resultCall_id')
        getRBComboBoxValue(self.cmbAccident,    record, 'accident_id')
        getRBComboBoxValue(self.cmbDeath,    record, 'death_id')
        getRBComboBoxValue(self.cmbEbriety,    record, 'ebriety_id')
        getRBComboBoxValue(self.cmbOrgStructure,    record, 'orgStructure_id')
        getRBComboBoxValue(self.cmbOrgId,        record, 'org_id')
        record.setValue('address_id', toVariant(self.getAddressRecord()))
        self.EmergencyCallEditDialog.saveEmergencyCall()


    def savePersonnel(self, eventId):
        items = self.modelPersonnel.items()
        itemVisit = []
        itemVisit = self.itemVisitPersonnelModel()
        sceneId = itemVisit[0]
        dateVisit = itemVisit[1]
        visitTypeId = itemVisit[2]
        financeId = itemVisit[3]
        serviceId = itemVisit[4]
        payStatus = itemVisit[5]
        for item in items:
            item.setValue('visitType_id', toVariant(forceRef(visitTypeId)))
            item.setValue('isPrimary', toVariant(self.cmbOrder.currentIndex()))
            item.setValue('date', toVariant(dateVisit))
            item.setValue('scene_id', toVariant(sceneId))
            item.setValue('payStatus', toVariant(payStatus))
            item.setValue('finance_id', toVariant(financeId))
            item.setValue('service_id', toVariant(serviceId))
        self.modelPersonnel.saveItems(eventId)


    def saveDiagnostics(self, modelDiagnostics, eventId):
        items = modelDiagnostics.items()
        isDiagnosisManualSwitch = modelDiagnostics.manualSwitchDiagnosis()
#        isFirst = True
        begDate = self.edtBegDate.date()
        endDate = self.edtFinishServiceDate.date()
        date = endDate if endDate else begDate
#        personIdVariant = toVariant(self.personId)
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
                None,
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
        diagnostics = self.modelFinalDiagnostics.items()
        if diagnostics:
            MKB   = forceString(diagnostics[0].value('MKB'))
            MKBEx = forceString(diagnostics[0].value('MKBEx'))
            return MKB, MKBEx
        else:
            return '', ''


    def getFinalDiagnosisId(self):
        diagnostics = self.modelFinalDiagnostics.items()
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
        CEventEditDialog.setEventTypeId(self, eventTypeId, u'Ф.110')
        self.tabCash.windowTitle = self.windowTitle()
        db = QtGui.qApp.db
        tableRBEB = db.table('EmergencyBrigade')
        filterRBEB = db.joinAnd([db.joinOr([tableRBEB['begDate'].isNull(), tableRBEB['begDate'].dateLe(self.eventSetDateTime)]),
                                 db.joinOr([tableRBEB['endDate'].isNull(), tableRBEB['endDate'].dateGe(self.eventSetDateTime)])
                                ])
        self.cmbNumberBrigade.setTable('EmergencyBrigade', addNone=False, filter=filterRBEB, order='code')
        self.cmbCauseCall.setTable('rbEmergencyCauseCall', order='code')
        self.cmbTypeAsset.setTable('rbEmergencyTypeAsset', order='code')
        self.cmbPlaceReceptionCall.setTable('rbEmergencyPlaceReceptionCall', addNone=False, order='code')
        self.cmbReceivedCall.setTable('rbEmergencyReceivedCall', addNone=False, order='code')
        self.cmbReasondDelays.setTable('rbEmergencyReasondDelays', order='code')
        self.cmbResultCircumstanceCall.setTable('rbEmergencyResult', addNone=False, order='code')
        self.cmbAccident.setTable('rbEmergencyAccident', order='code')
        self.cmbDeath.setTable('rbEmergencyDeath', order='code')
        self.cmbEbriety.setTable('rbEmergencyEbriety', order='code')
        self.cmbDiseased.setTable('rbEmergencyDiseased', addNone=False, order='code')
        self.cmbPlaceCall.setTable('rbEmergencyPlaceCall', addNone=False, order='code')
        self.cmbMethodTransportation.setTable('rbEmergencyMethodTransportation', order='code')
        self.cmbTransferredTransportation.setTable('rbEmergencyTransferredTransportation', order='code')
        showTime = getEventShowTime(eventTypeId)
        self.getShowButtonAccount()
        self.getShowButtonTemperatureList()
        self.getShowButtonNomenclatureExpense()
        self.getShowButtonJobTickets()
        self.edtBegTime.setVisible(showTime)
        self.edtPassTime.setVisible(showTime)
        self.edtDepartureTime.setVisible(showTime)
        self.edtArrivalTime.setVisible(showTime)
        self.edtFinishServiceTime.setVisible(showTime)
        self.edtEndTime.setVisible(showTime)
        self.cmbResult.setTable('rbResult', True, 'eventPurpose_id=\'%d\'' % self.eventPurposeId)
        cols = self.modelFinalDiagnostics.cols()
        resultCol = cols[len(cols)-1]
        resultCol.filter = 'eventPurpose_id=\'%d\'' % self.eventPurposeId
        self.cmbContract.setEventTypeId(eventTypeId)
        customizePrintButton(self.btnPrint, self.eventContext if self.eventContext else 'F110')


    def resetActionTemplateCache(self):
        self.tabStatus.actionTemplateCache.reset()
        self.tabDiagnostic.actionTemplateCache.reset()
        self.tabCure.actionTemplateCache.reset()
        self.tabMisc.actionTemplateCache.reset()


    def setEnabledChkCloseEvent(self, date):
        date = self.edtFinishServiceDate.date()
        if getEventShowTime(self.eventTypeId):
            time = self.edtFinishServiceTime.time()
            if time == QTime() or time == QTime(0, 0):
                date = QDate()
        self.tabNotes.setEnabledChkCloseEvent(date)


    def setCheckedChkCloseEvent(self):
        date = self.edtFinishServiceDate.date()
        if getEventShowTime(self.eventTypeId):
            time = self.edtFinishServiceTime.time()
            if time == QTime() or time == QTime(0, 0):
                date = QDate()
        self.tabNotes.setCheckedChkCloseEvent(date)


    def checkDataEntered(self):
        result = CEventEditDialog.checkDataEntered(self)
        tabList = [self.tabStatus, self.tabDiagnostic, self.tabCure, self.tabMisc]
        self.blankMovingIdList = []
        showTime = getEventShowTime(self.eventTypeId)
        if showTime:
            begDate = QDateTime(self.edtBegDate.date(), self.edtBegTime.time())
            endDate = QDateTime(self.edtEndDate.date(), self.edtEndTime.time())
            finishServiceDate = QDateTime(self.edtFinishServiceDate.date(), self.edtFinishServiceTime.time())
        else:
            begDate = self.edtBegDate.date()
            endDate = self.edtEndDate.date()
            finishServiceDate = self.edtFinishServiceDate.date()
        passDate = self.edtPassDate.date()
        departureDate = self.edtDepartureDate.date()
        arrivalDate = self.edtArrivalDate.date()

        nextDate = self.edtNextDate.date()
        mesRequired = getEventMesRequired(self.eventTypeId)
        result = result and self.checkExecPersonSpeciality(self.cmbPerson.value(), self.cmbPerson)
        #result = result and (finishServiceDate or self.checkInputMessage(u'Дату оконч. обслуж.', False, self.edtFinishServiceDate))
        if finishServiceDate.isValid():
            result = result and (self.orgId != QtGui.qApp.currentOrgId() or self.cmbContract.value() or self.checkInputMessage(u'договор', False, self.cmbContract))
            result = result and (self.cmbPerson.value() or self.checkInputMessage(u'ответственного врача', False, self.cmbPerson))
            result = result and (self.cmbDispatcher.value() or self.checkInputMessage(u'диспетчера', False, self.cmbDispatcher))
            result = result and (begDate or self.checkInputMessage(u'Дату приема вызова', False, self.edtBegDate))
            result = result and (passDate or self.checkInputMessage(u'Дату передачи бригаде', False, self.edtPassDate))
            result = result and (departureDate or self.checkInputMessage(u'Дату выезда', False, self.edtDepartureDate))
            result = result and (arrivalDate or self.checkInputMessage(u'Дату прибытия', False, self.edtArrivalDate))
            result = result and (endDate or self.checkInputMessage(u'Дату возвращения на станцию', True, self.edtEndDate))
            if self.cmbTypeAsset.value():
                result = result and (nextDate or self.checkInputMessage(u'Дату активного посещения', True, self.edtNextDate))
            result = result and self.checkEmergencyCallDate()
            result = result and self.checkActionDataEntered(begDate, QDateTime(), finishServiceDate, self.tabToken, self.edtBegDate, None, self.edtFinishServiceDate)
            result = result and self.checkEventDate(begDate, finishServiceDate, None, self.tabToken, None, self.edtFinishServiceDate, True)
            minDuration,  maxDuration = getEventDurationRange(self.eventTypeId)
            if minDuration<=maxDuration:
                result = result and (begDate.daysTo(finishServiceDate)+1>=minDuration or self.checkValueMessage(u'Длительность должна быть не менее %s'%formatNum(minDuration, (u'дня', u'дней', u'дней')), False, self.edtFinishServiceDate))
                result = result and (maxDuration==0 or begDate.daysTo(finishServiceDate)+1<=maxDuration or self.checkValueMessage(u'Длительность должна быть не более %s'%formatNum(maxDuration, (u'дня', u'дней', u'дней')), False, self.edtFinishServiceDate))
                result = result and (len(self.modelFinalDiagnostics.items())>0 or self.checkInputMessage(u'диагноз', False, self.tblFinalDiagnostics))
                result = result and (self.cmbResult.value()  or self.checkInputMessage(u'результат',   False, self.cmbResult))
            result = result and self.checkDiagnosticsType()
            if mesRequired:
                result = result and self.tabMes.checkMesAndSpecification()
                result = result and (self.tabMes.chechMesDuration() or self.checkValueMessage(u'Длительность события должна попадать в интервал минимальной и максимальной длительности по требованию к МЭС', True, self.edtBegDate))
                result = result and self.checkDiagnosticsMKBForMes(self.tblFinalDiagnostics, self.tabMes.cmbMes.value())

            result = result and self.checkDiagnosticsDataEntered()
            result = result and self.checkExecPersonSpeciality(self.cmbPerson.value(), self.cmbPerson)
            result = result and self.checkDiagnosticsPersonSpeciality()
            result = result and self.checkActionsDateEnteredActuality(begDate, finishServiceDate, tabList)
            result = result and self.checkActionsDataEntered(begDate, finishServiceDate)
            result = result and self.checkDeposit(True)
            result = result and (len(self.modelPersonnel.items())>0 or self.checkInputMessage(u'состав бригады', False, self.tblPersonnel))
            result = result and (((not self.grpRenunOfHospital.isChecked()) or (self.grpRenunOfHospital.isChecked() and len(self.edtFaceRenunOfHospital.text()) > 0)) or  self.checkInputMessage(u'Лицо отказа от госпитализации', False, self.edtFaceRenunOfHospital))
            result = result and ((len(self.edtNumberCardCall.text()) > 0) or  self.checkInputMessage(u'Карта вызова №', True, self.edtNumberCardCall))
            if self.edtFinishServiceDate.date() and QtGui.qApp.isUniqueNumberCardCall():
                result = result and self.checkNumberCardCall(self.edtNumberCardCall.text(), self.edtFinishServiceDate.date())
            #if self.cmbNumberBrigade.isEnabled():
            result = result and (self.cmbNumberBrigade.value() or  self.checkInputMessage(u'Номер бригады', False, self.cmbNumberBrigade))
            result = result and (self.cmbCauseCall.value() or  self.checkInputMessage(u'Повод к вызову', True, self.cmbCauseCall))
            result = result and ((len(self.edtWhoCallOnPhone.text()) > 0) or  self.checkInputMessage(u'Кто вызывал', True, self.edtWhoCallOnPhone))
            result = result and ((len(self.edtNumberPhone.text()) > 0) or  self.checkInputMessage(u'С какого телефона', True, self.edtNumberPhone))
            #result = result and (self.cmbOrder.currentIndex()>0 or  self.checkInputMessage(u'Вызов', False, self.cmbOrder))
            result = result and (self.cmbOrderEvent.currentIndex()>=0 or  self.checkInputMessage(u'Порядок', False, self.cmbOrderEvent))

            result = result and self.tabCash.checkDataLocalContract()
            result = result and self.checkSerialNumberEntered()
            result = result and self.checkTabNotesEventExternalId()
            result = result and self.checkHouses()
        else:
            result = result and self.checkDiagnosticsPersonSpeciality()
        if self.edtEndDate.date():
            result = result and self.checkAndUpdateExpertise(self.edtEndDate.date(), self.cmbPerson.value())
        result = result and self.selectNomenclatureAddedActions(tabList)
        return result


    def checkNumberCardCall(self, numberCardCall, execDate):
        db = QtGui.qApp.db
        table = db.table('Event')
        tableEC = db.table('EmergencyCall')
        cols = [table['id']]
        queryTable = table.innerJoin(tableEC, tableEC['event_id'].eq(table['id']))
        cond = [table['deleted'].eq(0),
                tableEC['deleted'].eq(0),
                tableEC['numberCardCall'].eq(numberCardCall),
                table['execDate'].yearEq(execDate)
                ]
        eventId = self.itemId()
        if eventId:
            cond.append(table['id'].ne(eventId))
        record = db.getRecordEx(queryTable, cols, cond)
        if record:
            return self.checkValueMessage(u'Номер карты вызова %s не уникален.'% (forceString(numberCardCall)), True if QtGui.qApp.isUniqueNumberCardCall() == 1 else False, self.edtNumberCardCall)
        return True


    def checkHouses(self):
        result = True
        locHouse = forceString(self.edtLocHouse.text())
        if locHouse:
            locStreetCode = self.cmbLocStreet.code()
            if not locStreetCode:
                cityCode = self.cmbLocCity.code()
                locStreetCode = cityCode + u'000000'
            if locStreetCode:
                res = self.checkHouseList(locStreetCode)
                if res:
                    base = self.clientLocHousesList.getCheckResult()
                    widgetHouse = self.edtLocHouse
                    result = result and self.checkStreetHouseMessage(u'Данные о номере дома по адресу %s %s, %s, %s отсутствуют в %s.'%(u'проживания',  self.cmbRegCity.currentText(), self.cmbRegStreet.currentText(), locHouse, base), res == 1, widgetHouse)
        return result


    def checkHouseList(self, streetCode):
        result = True
        if streetCode:
            house = forceString(self.edtLocHouse.text())
            corp = forceString(self.edtLocCorpus.text())
            result = self.clientLocHousesList.checkHouse(house, corp)
        return result


    def checkEmergencyCallDate(self):
        begDate = self.edtBegDate.date()
        endDate = self.edtEndDate.date()
        passDate = self.edtPassDate.date()
        departureDate = self.edtDepartureDate.date()
        arrivalDate = self.edtArrivalDate.date()
        finishServiceDate = self.edtFinishServiceDate.date()
        nextDate = self.edtNextDate.date()
        begTime = self.edtBegTime.time().toString('hh:mm')
        endTime = self.edtEndTime.time().toString('hh:mm')
        passTime = self.edtPassTime.time().toString('hh:mm')
        departureTime = self.edtDepartureTime.time().toString('hh:mm')
        arrivalTime = self.edtArrivalTime.time().toString('hh:mm')
        finishServiceTime = self.edtFinishServiceTime.time().toString('hh:mm')
        nextTime = self.edtNextTime.time().toString('hh:mm')

        result = True
        if endDate and begDate:
            result = result and (begDate <= endDate or self.checkValueMessage(u'Датa приема вызова %s не может быть позже даты возвр. на станц. %s'% (forceString(begDate), forceString(endDate)), False, self.edtBegDate))
        elif begDate and finishServiceDate:
              result = result and (begDate <= finishServiceDate or self.checkValueMessage(u'Датa приема вызова %s не может быть позже даты оконч. обслуж. %s'% (forceString(begDate), forceString(finishServiceDate)), False, self.edtBegDate))
        result = result and ((begDate <= passDate) or self.checkValueMessage(u'Датa приема вызова %s не может быть позже даты передачи вызова бригаде %s'% (forceString(begDate), forceString(passDate)), False, self.edtBegDate))
        if begDate == passDate:
            result = result and ((begTime <= passTime) or self.checkValueMessage(u'Время приема вызова %s не может быть позже времени передачи вызова бригаде %s'% (begTime, passTime), False, self.edtBegTime))
        result = result and ((passDate <= departureDate) or self.checkValueMessage(u'Дата передачи вызова бригаде %s не может быть позже даты выезда %s'% (forceString(passDate), forceString(departureDate)), False, self.edtPassDate))
        if passDate == departureDate:
            result = result and ((passTime <= departureTime) or self.checkValueMessage(u'Время передачи вызова бригаде %s не может быть позже времени выезда %s'% (passTime, departureTime), False, self.edtPassTime))
        result = result and ((departureDate <= arrivalDate) or self.checkValueMessage(u'Дата выезда %s не может быть позже даты прибытия %s'% (forceString(departureDate), forceString(arrivalDate)), False, self.edtDepartureDate))
        if departureDate == arrivalDate:
            result = result and ((departureTime <= arrivalTime) or self.checkValueMessage(u'Время выезда %s не может быть позже времени прибытия %s'% (departureTime, arrivalTime), False, self.edtDepartureTime))
        result = result and ((arrivalDate <= finishServiceDate) or self.checkValueMessage(u'Дата прибытия %s не может быть позже даты оконч. обслуж. %s'% (forceString(arrivalDate), forceString(finishServiceDate)), False, self.edtArrivalDate))
        if arrivalDate == finishServiceDate:
            result = result and ((arrivalTime <= finishServiceTime) or self.checkValueMessage(u'Время прибытия %s не может быть позже времени оконч. обслуж. %s'% (arrivalTime, finishServiceTime), False, self.edtArrivalTime))
        if self.cmbTypeAsset.value() and nextDate:
            result = result and ((finishServiceDate <= nextDate) or self.checkValueMessage(u'Дата активного посещения %s не может быть раньше даты оконч. обслуж. %s'% (forceString(nextDate), forceString(finishServiceDate)), False, self.edtNextDate))
            if nextDate == finishServiceDate:
                result = result and ((finishServiceTime <= nextTime) or self.checkValueMessage(u'Время активного посещения %s не может быть раньше времени оконч. обслуж. %s'% (nextTime, finishServiceTime), False, self.edtNextTime))
        if endDate:
            result = result and ((finishServiceDate <= endDate) or self.checkValueMessage(u'Дата оконч. обслуж. %s не может быть позже даты возвр. на станц. %s'% (forceString(finishServiceDate), forceString(endDate)), False, self.edtFinishServiceDate))
            if finishServiceDate == endDate:
                result = result and ((finishServiceTime <= endTime) or self.checkValueMessage(u'Время оконч. обслуж. %s не может быть позже времени возвр. на станц. %s'% (finishServiceTime, endTime), False, self.edtFinishServiceTime))
        return result

    
    def checkDiagnosticsPersonSpeciality(self):
        result = True
        result = result and self.checkPersonSpecialityDiagnostics(self.modelFinalDiagnostics, self.tblFinalDiagnostics)
        return result
    

    def checkDiagnosticsDataEntered(self):
        result = True
        result = result and self.checkDiagnostics(self.modelFinalDiagnostics, self.cmbPerson.value())
        return result


    def checkDiagnostics(self, model, finalPersonId):
        for row, record in enumerate(model.items()):
            if not self.checkDiagnosticDataEntered(row, record):
                return False
        return True


    def checkDiagnosticsType(self):
        result = True
        endDate = self.edtFinishServiceDate.date()
        if endDate:
            result = result and self.checkDiagnosticsTypeEnd(self.modelFinalDiagnostics) or self.checkValueMessage(u'Необходимо указать основной диагноз', True, self.tblFinalDiagnostics)
        return result


    def checkDiagnosticsTypeEnd(self, model):
        for row, record in enumerate(model.items()):
            if  forceInt(record.value('diagnosisType_id')) == model.diagnosisTypeCol.ids[0]:
                return True
        return False


    def checkDiagnosticDataEntered(self, row, record):
###     self.checkValueMessage(self, message, canSkip, widget, row=None, column=None):
        result = True
        if result:
            MKB = forceString(record.value('MKB'))
            MKBEx = forceString(record.value('MKBEx'))
            personId = forceRef(record.value('person_id'))
            specialityId = forceRef(QtGui.qApp.db.translate('Person', 'id', personId, 'speciality_id'))
            result = specialityId or self.checkValueMessage(u'Отсутствует специальность врача', False, self.tblFinalDiagnostics, row, record.indexOf('person_id'))
            result = result and MKB or self.checkInputMessage(u'диагноз', True, self.tblFinalDiagnostics, row, record.indexOf('MKB'))
            result = result and self.checkActualMKB(self.tblFinalDiagnostics, self.edtBegDate.date(), MKB, record, row)
            if result:
                char = MKB[:1]
                blockMKB = forceInt(MKB[1:3])
                traumaTypeId = forceRef(record.value('traumaType_id'))
                if char in 'ST' and not (char in 'T' and 36 <= blockMKB <= 78):
                    if not traumaTypeId:
                        result = self.checkValueMessage(u'Необходимо указать тип травмы',  True if QtGui.qApp.controlTraumaType()==0 else False, self.tblFinalDiagnostics, row, record.indexOf('traumaType_id'))
                    if result:
                        result = MKBEx or self.checkInputMessage(u'Дополнительный диагноз', True if QtGui.qApp.controlMKBExForTraumaType()==0 else False, self.tblFinalDiagnostics, row, record.indexOf('MKBEx'))
                        if result:
                            charEx = MKBEx[:1]
                            if charEx not in 'VWXY':
                                result = self.checkValueMessage(u'Доп.МКБ не соотвествует Доп.МКБ при травме', True, self.tblFinalDiagnostics, row, record.indexOf('MKBEx'))
                if char not in 'ST' and traumaTypeId:
                    result = self.checkValueMessage(u'Необходимо удалить тип травмы', False, self.tblFinalDiagnostics, row, record.indexOf('traumaType_id'))
        if result and row == 0:
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


    def getCuratorId(self):
        return self.cmbDispatcher.value()


    def getEventInfo(self, context):
        result = CEventEditDialog.getEventInfo(self, context, CEmergencyEventInfo)
        showTime = getEventShowTime(self.eventTypeId) if self.eventTypeId else True
        # ручная инициализация свойств
#        record = self.record()
        result._isPrimary = forceInt(self.cmbOrder.currentIndex())+1
        result._typeAsset = context.getInstance(CEmergencyTypeAssetInfo, self.cmbTypeAsset.value())
        recordEmergency = self.EmergencyCallEditDialog.record()
        result._numberCardCall = self.edtNumberCardCall.text()
        result._storey = self.edtStorey.text()
        result._entrance = self.edtEntrance.text()
        result._additional = self.edtAdditional.toPlainText()
        result._numberEpidemic = self.edtNumberEpidemic.text()
        result._numberOrder = self.edtOrderNumber.text()
        result._orgStructure = context.getInstance(COrgStructureInfo, self.cmbOrgStructure.value())
        result._guidePerson_id = context.getInstance(CPersonInfo, self.cmbGuidePerson.value())
        result._brigade = context.getInstance(CEmergencyBrigadeInfo, self.cmbNumberBrigade.value())
        result._causeCall = context.getInstance(CEmergencyCauseCallInfo, self.cmbCauseCall.value())
        result._whoCallOnPhone = self.edtWhoCallOnPhone.text()
        result._numberPhone = self.edtNumberPhone.text()
        if showTime:
            result._begDate = CDateTimeInfo(QDateTime(self.edtBegDate.date(), self.edtBegTime.time()))
            result._passDate = CDateTimeInfo(QDateTime(self.edtPassDate.date(), self.edtPassTime.time()))
            result._departureDate = CDateTimeInfo(QDateTime(self.edtDepartureDate.date(), self.edtDepartureTime.time()))
            result._arrivalDate = CDateTimeInfo(QDateTime(self.edtArrivalDate.date(), self.edtArrivalTime.time()))
            result._finishServiceDate = CDateTimeInfo(QDateTime(self.edtFinishServiceDate.date(), self.edtFinishServiceTime.time()))
            result._endDate = CDateTimeInfo(QDateTime(self.edtEndDate.date(), self.edtEndTime.time()))
        else:
            result._begDate = CDateInfo(self.edtBegDate.date())
            result._passDate = CDateInfo(self.edtPassDate.date())
            result._departureDate = CDateInfo(self.edtDepartureDate.date())
            result._arrivalDate = CDateInfo(self.edtArrivalDate.date())
            result._finishServiceDate = CDateInfo(self.edtFinishServiceDate.date())
            result._endDate = CDateInfo(self.edtEndDate.date())
        result._placeReceptionCall = context.getInstance(CEmergencyPlaceReceptionCallInfo, self.cmbPlaceReceptionCall.value())
        result._receivedCall = context.getInstance(CEmergencyReceivedCallInfo, self.cmbReceivedCall.value())
        result._reasondDelays = context.getInstance(CEmergencyReasondDelaysInfo, self.cmbReasondDelays.value())
        result._resultCall = context.getInstance(CEmergencyResultInfo, self.cmbResultCircumstanceCall.value())
        result._accident = context.getInstance(CEmergencyAccidentInfo, self.cmbAccident.value())
        result._death = context.getInstance(CEmergencyDeathInfo, self.cmbDeath.value())
        result._ebriety = context.getInstance(CEmergencyEbrietyInfo, self.cmbEbriety.value())
        result._diseased = context.getInstance(CEmergencyDiseasedInfo, self.cmbDiseased.value())
        result._placeCall = context.getInstance(CEmergencyPlaceCallInfo, self.cmbPlaceCall.value())
        result._methodTransport = context.getInstance(CEmergencyMethodTransportInfo, self.cmbMethodTransportation.value())
        result._transfTransport = context.getInstance(CEmergencyTransferTransportInfo, self.cmbTransferredTransportation.value())
        result._addressCity = self.cmbLocCity.currentText()
        result._addressStreet = self.cmbLocStreet.currentText()
        result._addressHouse = self.edtLocHouse.text()
        result._addressCorpus = self.edtLocCorpus.text()
        result._addressFlat = self.edtLocFlat.text()
        result._renunOfHospital = self.grpRenunOfHospital.isChecked()
        result._faceRenunOfHospital = self.edtFaceRenunOfHospital.text()
        result._disease = self.chkDisease.isChecked()
        result._birth = self.chkBirth.isChecked()
        result._pregnancyFailure = self.chkPregnancyFailure.isChecked()
        result._noteCall = forceString(recordEmergency.value('noteCall')) if recordEmergency else ''

        # ручная инициализация таблиц
        result._actions = CActionInfoProxyList(context,
                [self.tabStatus.modelAPActions, self.tabDiagnostic.modelAPActions, self.tabCure.modelAPActions, self.tabMisc.modelAPActions, self.tabMedicalDiagnosis.tblEventMedicalDiagnosis.model()],
                result)
        result._diagnosises = CDiagnosticInfoProxyList(context, [self.modelFinalDiagnostics])
        result._visits = self.getVisitsPersonell(context)
        return result


    def itemVisitPersonnelModel(self):
        contractId = self.cmbContract.value()
        codeScene = 4
        db = QtGui.qApp.db
        keyVal = u'СМП'  #В справочнике для типа визитов должна быть строка с кодом "СМП",
        record = db.translate('rbVisitType', 'code', keyVal, 'id')
        if not record:
           keyVal = u'' #если ее нет, то берется тип с пустым кодом
           record = db.translate('rbVisitType', 'code', keyVal, 'id')
        visitTypeId = forceRef(record)
        dateVisit = QDateTime()
        if self.edtFinishServiceDate.date():
            dateVisit.setDate(self.edtFinishServiceDate.date())
            if self.edtFinishServiceTime and self.edtFinishServiceTime.time():
                dateVisit.setTime(self.edtFinishServiceTime.time())
        elif self.edtArrivalDate.date():
          dateVisit.setDate(self.edtArrivalDate.date())
          if self.edtArrivalTime and self.edtArrivalTime.time():
            dateVisit.setTime(self.edtArrivalTime.time())
        sceneId = forceRef(db.translate('rbScene', 'code', codeScene, 'id'))
        financeId = forceRef(db.translate('Contract', 'id', contractId, 'finance_id')) #по договору(cmbContract)
        serviceId = None
        payStatus = 0
        return [sceneId, dateVisit, visitTypeId, financeId, serviceId, payStatus]


    def getVisitsPersonell(self, context):
        visits = []
        items = self.modelPersonnel.items()
        itemVisit = []
        itemVisit = self.itemVisitPersonnelModel()
        sceneId = itemVisit[0]
        dateVisit = itemVisit[1]
        visitTypeId = itemVisit[2]
        financeId = itemVisit[3]
        serviceId = itemVisit[4]
        payStatus = itemVisit[5]
        for item in items:
            visitItem = []
            visitItem.append(sceneId)
            visitItem.append(dateVisit)
            visitItem.append(visitTypeId)
            visitItem.append(forceRef(item.value('person_id')))
            visitItem.append(self.cmbOrder.currentIndex())
            visitItem.append(financeId)
            visitItem.append(serviceId)
            visitItem.append(payStatus)
        return visits


    def getTempInvalidInfo(self, context):
        return self.grpTempInvalid.getTempInvalidInfo(context)


    def updateMesMKB(self):
        MKB, MKBEx = self.getFinalDiagnosisMKB()
        self.tabMes.setMKB(MKB)
        self.tabMes.setMKBEx(MKBEx)


    def setContractId(self, contractId):
        if self.contractId != contractId:
            CEventEditDialog.setContractId(self, contractId)
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
    def on_modelFinalDiagnostics_diagnosisChanged(self):
        self.updateMesMKB()


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
        self.prepare(self.clientId, self.eventTypeId, self.orgId, self.personId, self.eventDate, self.eventDate, None, None, None, None, 
                         None, None, None, None, None, None, 
                          None, None, None, None, None, actionListToNewEvent, None, None, -1, True)
        self.initPrevEventTypeId(self.eventTypeId, self.clientId)
        self.initPrevEventId(None)
        self.addActions(actionListToNewEvent)


    @pyqtSignature('int')
    def on_cmbTypeAsset_currentIndexChanged(self):
        if self.cmbTypeAsset.value():
            self.edtNextDate.setEnabled(True)
            self.edtNextTime.setEnabled(True)
        else:
            self.edtNextDate.setEnabled(False)
            self.edtNextTime.setEnabled(False)


    def on_modelFinalDiagnostics_resultChanged(self, resultId):
        if forceBool(QtGui.qApp.preferences.appPrefs.get('fillDiagnosticsEventsResults', True)):
            CF110Dialog.defaultDiagnosticResultId = forceRef(resultId)
            defaultResultId = getEventResultId(CF110Dialog.defaultDiagnosticResultId, self.eventPurposeId)
            if defaultResultId:
                self.cmbResult.setValue(defaultResultId)


    @pyqtSignature('')
    def on_actDiagnosticsAddAccomp_triggered(self):
        currentRow = self.tblFinalDiagnostics.currentIndex().row()
        if currentRow>=0:
            currentRecord = self.modelFinalDiagnostics.items()[currentRow]
            newRecord = self.modelFinalDiagnostics.getEmptyRecord()
            newRecord.setValue('diagnosisType', QVariant(CF110Dialog.dfAccomp))
            newRecord.setValue('speciality_id', currentRecord.value('speciality_id'))
            newRecord.setValue('healthGroup_id', currentRecord.value('healthGroup_id'))
            self.modelFinalDiagnostics.insertRecord(currentRow+1, newRecord)
            self.tblFinalDiagnostics.setCurrentIndex(self.modelFinalDiagnostics.index(currentRow+1, newRecord.indexOf('MKB')))


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
            applyTemplate(self, templateId, data, signAndAttachHandler=None)


class CF110PersonnelModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Visit', 'id', 'event_id', parent)
        self.addCol(CPersonFindInDocTableCol(u'ФИО', 'person_id',  20, 'vrbPersonWithSpeciality', parent=parent))
        self.addHiddenCol('visitType_id')
        self.addHiddenCol('date')
        self.addHiddenCol('isPrimary')
        self.addHiddenCol('scene_id')
        self.addHiddenCol('payStatus')
        self.addHiddenCol('finance_id')
        self.addHiddenCol('service_id')
        self.defaultVisitTypeId = None
        self.tryFindDefaultVisitTypeId = True


    def loadItems(self, eventId):
        CInDocTableModel.loadItems(self, eventId)
        if self.items():
            lastItem = self.items()[-1]
            if self.defaultVisitTypeId is None:
                self.defaultVisitTypeId = forceRef(lastItem.value('visitType_id'))


    def getEmptyRecord(self, personId=None):
        result = CInDocTableModel.getEmptyRecord(self)
        result.setValue('person_id', toVariant(personId if personId else QObject.parent(self).getSuggestedPersonId()))
        return result


    def setData(self, index, value, role=Qt.EditRole):
        column = index.column()
        if not variantEq(self.data(index, role), value):
            if column == 0: # врач
                result = CInDocTableModel.setData(self, index, value, role)
                return result
            else:
                return CInDocTableModel.setData(self, index, value, role)
        else:
            return True


    def setDefaultVisitTypeId(self, visitTypeId):
        self.defaultVisitTypeId = visitTypeId
        if visitTypeId is None:
            self.tryFindDefaultVisitTypeId = True


    def getDefaultVisitTypeId(self):
        if self.defaultVisitTypeId is None:
            if self.tryFindDefaultVisitTypeId:
                self.defaultVisitTypeId = forceRef(QtGui.qApp.db.translate('rbVisitType', 'code', '', 'id'))
                self.tryFindDefaultVisitTypeId = False
        return self.defaultVisitTypeId


    def addAbsentPersons(self, personIdList, eventDate = None):
        for item in self.items():
            personId = forceRef(item.value('person_id'))
            if personId in personIdList:
                personIdList.remove(personId)
        for personId in personIdList:
            item = self.getEmptyRecord(personId=personId)
            date = eventDate if eventDate else QDate.currentDate()
            item.setValue('date', toVariant(date))
            self.items().append(item)
        if personIdList:
            self.reset()


class CF110DiagnosisTypeCol(CDiagnosisTypeCol):
    def __init__(self, title=u'Тип', fieldName='diagnosisType_id', width=5, diagnosisTypeCodes=[], smartMode=True, **params):
        CDiagnosisTypeCol.__init__(self, title, fieldName, width, diagnosisTypeCodes, smartMode, **params)
        self.namesF110 = [u'Осн', u'Соп', u'Осл']


    def toString(self, val, record):
        id = forceRef(val)
        if id in self.ids:
            return toVariant(self.namesF110[self.ids.index(id)])
        return QVariant()


    def setEditorData(self, editor, value, record):
        editor.clear()
        if value.isNull():
            value = record.value(self.fieldName())
        id = forceRef(value)
        if self.smartMode:
            if id == self.ids[0]:
                editor.addItem(self.namesF110[0], toVariant(self.ids[0]))
            elif id == self.ids[1]:
                if self.ids[0]:
                    editor.addItem(self.namesF110[0], toVariant(self.ids[0]))
                editor.addItem(self.namesF110[1], toVariant(self.ids[1]))
            else:
                editor.addItem(self.namesF110[2], toVariant(self.ids[2]))
        else:
            for itemName, itemId in zip(self.namesF110, self.ids):
                if itemId:
                    editor.addItem(itemName, toVariant(itemId))
        currentIndex = editor.findData(toVariant(id))
        editor.setCurrentIndex(currentIndex)


class CF110BaseDiagnosticsModel(CMKBListInDocTableModel):
    __pyqtSignals__ = ('typeOrPersonChanged()',
                       'diagnosisChanged()'
                      )
    MKB_allowed_morphology = ['C', 'D']

    def __init__(self, parent, baseDiagnosisTypeCode, accompDiagnosisTypeCode, complicDiagnosisTypeCode):
        CMKBListInDocTableModel.__init__(self, 'Diagnostic', 'id', 'event_id', parent)
        self._parent = parent
        self.isManualSwitchDiagnosis = QtGui.qApp.defaultIsManualSwitchDiagnosis()
        self.isMKBMorphology = QtGui.qApp.defaultMorphologyMKBIsVisible()
        self.characterIdForHandleDiagnosis = None
        self.diagnosisTypeCol = CF110DiagnosisTypeCol( u'Тип', 'diagnosisType_id', 2, [baseDiagnosisTypeCode, accompDiagnosisTypeCode, complicDiagnosisTypeCode], smartMode=False)
        self.addCol(self.diagnosisTypeCol)
        self.addCol(CPersonFindInDocTableCol(u'Врач', 'person_id',  20, 'vrbPersonWithSpeciality', parent=parent))
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
        self.addCol(CRBLikeEnumInDocTableCol(u'Госп',      'hospital',       7, CHospitalInfo.names, showFields=CRBComboBox.showCode, preferredWidth=150)).setToolTip(u'Потребность в госпитализации')
        self.addCol(CRBInDocTableCol(    u'Травма',        'traumaType_id', 10, 'rbTraumaType', addNone=True, showFields=CRBComboBox.showName, preferredWidth=150))
        self.addCol(CToxicSubstances(u'ТоксВещ', 'toxicSubstances_id', 10, addNone=True, showFields=CRBComboBox.showName, preferredWidth=150)).setToolTip(u'Токсичное вещество')
        self.addCol(CInDocTableCol(u'Описание',     'freeInput', 15))
        self.addCol(CRBInDocTableCol(    u'Результат',     'result_id',     10, 'rbDiagnosticResult', showFields=CRBComboBox.showNameAndCode, preferredWidth=350))
        self.columnResult = self.getColIndex('result_id', None)
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
                    if not (bool(mkb) and mkb[0] in CF110BaseDiagnosticsModel.MKB_allowed_morphology):
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
        result.append(QtSql.QSqlField('cTumor_id',        QVariant.Int))
        result.append(QtSql.QSqlField('cNodus_id',        QVariant.Int))
        result.append(QtSql.QSqlField('cMetastasis_id',   QVariant.Int))
        result.append(QtSql.QSqlField('cTNMphase_id',     QVariant.Int))
        result.append(QtSql.QSqlField('pTumor_id',        QVariant.Int))
        result.append(QtSql.QSqlField('pNodus_id',        QVariant.Int))
        result.append(QtSql.QSqlField('pMetastasis_id',   QVariant.Int))
        result.append(QtSql.QSqlField('pTNMphase_id',     QVariant.Int))
        result.setValue('person_id',     toVariant(QObject.parent(self).getSuggestedPersonId()))
        if self.items():
            result.setValue('diagnosisType_id',  toVariant(self.diagnosisTypeCol.ids[2]))
        else:
            result.setValue('diagnosisType_id',  toVariant(self.diagnosisTypeCol.ids[0] if self.diagnosisTypeCol.ids[0] else self.diagnosisTypeCol.ids[1]))
            result.setValue('result_id',  toVariant(CF110Dialog.defaultDiagnosticResultId))
            #CF110Dialog.defaultDiagnosticResultId = defaultResultId
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
                    self.emitTypeOrPersonChanged()
                return result
            elif column == 1: # врач
                result = CMKBListInDocTableModel.setData(self, index, value, role)
                if result:
                    self.updateDiagnosisType(set())
                    self.emitDiagnosisChanged()
                    self.emitTypeOrPersonChanged()
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
                    acceptable, specifiedMKB, specifiedMKBEx, specifiedCharacterId, specifiedTraumaTypeId, specifiedDispanserId, specifiedRequiresFillingDispanser, specifiedProlongMKB = QObject.parent(self).specifyDiagnosis(newMKB)
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
                    self.emitTypeOrPersonChanged()
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
                self.emitDiagnosisChanged()
                return result
            if row == 0 and column == self.columnResult:
                result = CMKBListInDocTableModel.setData(self, index, value, role)
                self.emitResultChanged(value)
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


    def removeRowEx(self, row):
        self.removeRows(row, 1)


    def updateDiagnosisType(self, fixedRowSet):
        mapPersonIdToRow = {}
        diagnosisTypeIds = []
        basePersonId = []
        for row, item in enumerate(self.items()):
            personId = forceRef(item.value('person_id'))
            rows = mapPersonIdToRow.setdefault(personId, [])
            rows.append(row)
            diagnosisTypeId = forceRef(item.value('diagnosisType_id'))
            diagnosisTypeIds.append(diagnosisTypeId)
        for personId, rows in mapPersonIdToRow.iteritems():
            basePersonId = []
            firstDiagnosisId = diagnosisTypeIds[rows[0]]
            for rowFixed in fixedRowSet.intersection(set(rows)):
                if (self.diagnosisTypeCol.ids[0] == diagnosisTypeIds[rowFixed]):
                    firstDiagnosisId = self.diagnosisTypeCol.ids[0]
                    if personId not in basePersonId:
                        basePersonId.append(personId)
                else:
                    firstDiagnosisId = diagnosisTypeIds[rowFixed]
            freeRows = set(rows).difference(fixedRowSet)
            for row in rows:
                if (row in freeRows) and firstDiagnosisId == self.diagnosisTypeCol.ids[0] and diagnosisTypeIds[row] == self.diagnosisTypeCol.ids[0] and (personId in basePersonId):
                    self.items()[row].setValue('diagnosisType_id', toVariant(self.diagnosisTypeCol.ids[1]))
                    self.emitCellChanged(row, self.items()[row].indexOf('diagnosisType_id'))
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


    def updateToxicSubstancesByMKB(self, row, MKB):
        toxicSubstanceIdList = getToxicSubstancesIdListByMKB(MKB)
        item = self.items()[row]
        toxicSubstanceId = forceRef(item.value('toxicSubstances_id'))
        if toxicSubstanceId and toxicSubstanceId in toxicSubstanceIdList:
            return
        item.setValue('toxicSubstances_id', toVariant(None))
        self.emitCellChanged(row, item.indexOf('toxicSubstances_id'))


    def emitTypeOrPersonChanged(self):
        self.emit(SIGNAL('typeOrPersonChanged()'))


    def emitDiagnosisChanged(self):
        self.emit(SIGNAL('diagnosisChanged()'))


    def deletedItems(self, masterId):
        if self._items is not None:
            db = QtGui.qApp.db
            table = self._table
            tableDiagnosis = db.table('Diagnosis')
            masterId = toVariant(masterId)
            masterIdFieldName = self._masterIdFieldName
            diagnosisIdList = db.getDistinctIdList(table, 'diagnosis_id',
                                                   [table['deleted'].eq(0), table['event_id'].eq(masterId)])
            if diagnosisIdList:
                db.deleteRecord(tableDiagnosis, tableDiagnosis['id'].inlist(diagnosisIdList))
            filter = [table[masterIdFieldName].eq(masterId)]
            if self._filter:
                filter.append(self._filter)
            db.deleteRecord(table, filter)


class CF110FinalDiagnosticsModel(CF110BaseDiagnosticsModel):
    __pyqtSignals__ = ('resultChanged(QVariant&)',
                      )
    def __init__(self, parent):
        CF110BaseDiagnosticsModel.__init__(self, parent, '2', '9', '3')
        self.mapMKBToServiceId = {}

    def getCloseOrMainDiagnosisTypeIdList(self):
        return [self.diagnosisTypeCol.codeToId(code) for code in ('1', '2')]
    
    
    def getMainDiagnosisTypeIdList(self):
        return [self.diagnosisTypeCol.codeToId('2')]

#    def getEmptyRecord(self):
#        result = CF110BaseDiagnosticsModel.getEmptyRecord(self)
#        if len(self.items()) == 0:
#            result.setValue('result_id',  toVariant(CF110Dialog.defaultEventResultId))
#        return result


    def emitResultChanged(self, resultId):
        self.emit(SIGNAL('resultChanged(QVariant&)'), resultId)
