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

import re

from PyQt4 import QtGui
from PyQt4.QtCore                 import (
                                          Qt,
                                          QDate,
                                          QDateTime,
                                          QEvent,
                                          QString,
                                          QStringList,
                                          QTime,
                                          QVariant,
                                          pyqtSignature,
                                          SIGNAL,
                                          QTimer
                                         )
from PyQt4.QtSql import QSqlField

from Events.ActionTypeListDialog import CActionTypeListDialog
from Events.ActionsModel import CActionRecordItem
from Events.CompletedEventsOMSWidget import CCompletedEventsOMSWidget
from Surveillance.SurveillancePlanningDialog import CSurveillancePlanningEditDialog
from library.Counter              import CCounterController
from library.TableModel import CTextCol
from library.crbcombobox          import CRBModelDataCache
from library.ICDUtils             import MKBwithoutSubclassification
from library.InDocTable           import CRBInDocTableCol
from library.ItemsListDialog      import CItemEditorBaseDialog
from library.MapCode              import createMapCodeToRowIdx
from library.PrintInfo import CDateInfo, CDateTimeInfo, CInfoContext, CTimeInfo
from library.PrintTemplates       import applyTemplate, getPrintTemplates, CPrintAction
from library.Utils import (
    calcAge,
    calcAgeTuple,
    copyFields,
    forceBool,
    forceDate,
    forceDateTime,
    forceDouble,
    forceInt,
    forceRef,
    forceString,
    forceStringEx,
    formatNameInt,
    formatSex,
    toDateTimeWithoutSeconds,
    toVariant,
    trim,
    pyDate
)

from Accounting.Tariff            import CTariff
from Events.Action                import CAction, CActionTypeCache, CActionType, getActionDefaultAmountEx
from Events.ActionInfo            import CMedicalDiagnosisInfoList
from Events.ActionsSelector       import selectActionTypes
from Events.ActionStatus          import CActionStatus
from Events.ActionTypeDialog import CActionTypeDialog
from Events.ContractTariffCache   import CContractTariffCache
from Events.EventInfo import (
    CContractInfo,
    CEventInfo,
    CEventTypeInfo,
    CPatientModelInfo,
    CCureMethodInfo,
    CCureTypeInfo,
    CMesInfo,
    CMesSpecificationInfo,
    CResultInfo,
    CDiagnosticInfoList,
    CCSGInfoList,
    CFeedInfoList,
    CVoucherInfoList, CActionDispansPhaseInfo, CEventIdentificationInfo,
)
from Events.EventJobTicketsEditor import CEventJobTicketsLockEditor
from Events.GetPrevActionIdHelper import CGetPrevActionIdHelper
from Events.MapActionTypeToServiceIdList import CMapActionTypeIdToServiceIdList
from Events.NomenclatureAddedActionsSelectDialog import CNomenclatureAddedActionsSelectDialog
from Events.Utils import (
    getExactVisitTypeIdList,
    getEventRestrictVisitTypeAgeSex,
    getActionTypeIdListByFlatCode,
    getEventEnableUnfinishedActions,
    getEventKeepVisitParity,
    getEventEnableActionsBeyondEvent,
    getHealthGroupFilter,
    isEventCheckedExecDateForVisit,
    isEventTerritorialBelonging,
    isEventAutoFillingExpertise,
    checkIsHandleDiagnosisIsChecked,
    checkTissueJournalStatusByActions,
    getAvailableCharacterIdByMKB,
    getClosingMKBValueForAction,
    getEventActionFinance,
    getEventActionsControlRequired,
    getEventAidTypeCode,
    getEventCode,
    getEventContext,
    getEventContextData,
    getEventDuration,
    getEventFinanceId,
    getEventMedicalAidKindId,
    getEventMesRequired,
    getEventMesRequiredParams,
    getEventName,
    getEventPeriodEx,
    getEventPrevEventTypeId,
    getEventPurposeId,
    getEventServiceId,
    getEventShowButtonAccount,
    getEventShowTime,
    getEventShowVisitTime,
    getEventTypeForm,
    getEventVisitFinance,
    getMKBValueBySetPerson,
    getPrevEventIdByEventTypeId,
    recordAcceptable,
    specifyDiagnosis,
    validCalculatorSettings,
    getEventOrder,
    getEventCSGRequired,
    getRelegationRequired,
    CEventTypeDescription,
    checkReferralLisLab,
    CFinanceType,
    getEventShowButtonTemperatureList,
    getEventShowButtonNomenclatureExpense,
    getEventShowButtonJobTickets,
    getEventProfileId,
    getEventTypeCheckCompletedEventsOMS)
from library.TimeoutLogout         import CTimeoutLogout
from HospitalBeds.CheckPeriodActions     import CCheckPeriodActionsForEvent # WFT?
from KLADR.Utils                  import KLADRMatch
from Resources.JobTicketStatus    import CJobTicketStatus

from Orgs.PersonInfo              import CPersonInfo
from Orgs.Utils import getOrganisationShortName, COrgInfo, getOrgStructureDescendants, \
    checkPersonByDefaultSettingsFromEventtype
from Orgs.PersonComboBoxEx        import CPersonFindInDocTableCol
from RefBooks.Finance.Info        import CFinanceInfo
from Registry.ClientEditDialog    import CClientEditDialog
from Registry.ClientDocumentTracking import CDocumentLocationInfo
from Registry.ShowContingentsClientDialog import CShowContingentsClientDialog
from Registry.Utils import (
    CCheckNetMixin,
    CClientInfo,
    getClientWork,
    getClientBanner,
    getClientCompulsoryPolicy,
    getClientVoluntaryPolicy,
    getClientAddressKLADRCode
)
from Registry.ClientVaccinationCard import openClientVaccinationCard
from Reports.ReportBase           import CReportBase, createTable
from Reports.ReportView           import CReportViewDialog
from Users.Rights import (
    urAdmin,
    urEditAfterInvoicingEvent,
    urEditCheckPeriodActions,
    urEditClosedEvent,
    urEditEndDateEvent,
    urHBEditEvent,
    urHBReadEvent,
    urReadCheckPeriodActions,
    urRegTabReadEvents,
    urRegTabWriteRegistry,
    urRegTabReadRegistry,
    urReadMedicalDiagnosis,
    urRegTabWriteEvents,
    urCanReadClientVaccination,
    urCanEditClientVaccination, urCanSaveEventWithMKBNotOMS, urEditAfterReturnEvent, urReadEventMedKart,
    urEditClosedEventCash
)

from Events.NomenclatureExpense.NomenclatureExpenseDialog import CNomenclatureExpenseDialog

from Events.Ui_ActionsControl import Ui_ActionsControlDialog


class CEventEditDialog(CItemEditorBaseDialog, CCheckNetMixin, CMapActionTypeIdToServiceIdList):
    # базовый диалог для всех форм событий
    __pyqtSignals__ = ('updateActionsAmount()',
                       'updateActionsPriceAndUet()',
                      )

    ctLocal = 1
    ctProvince = 2
    ctOther = 0
    ctRegAddress = 0
    ctLocAddress = 1
    ctInsurer = 2

    saveAndCreateAccount = 2

    TNMSFields = ['cTumor_id', 'cNodus_id', 'cMetastasis_id', 'cTNMphase_id', 'pTumor_id', 'pNodus_id', 'pMetastasis_id', 'pTNMphase_id']
    TNMSFieldsDict = {u'cT': u'cTumor_id', u'cN': u'cNodus_id', u'cM': u'cMetastasis_id', u'cS': u'cTNMphase_id',
                      u'pT': u'pTumor_id', u'pN': u'pNodus_id', u'pM': u'pMetastasis_id', u'pS': u'pTNMphase_id'}

    re_actionPropertyStringChecking = re.compile(u'[A-Za-zЁёА-я0-9]+')
    def __init__(self, parent):
        CItemEditorBaseDialog.__init__(self, parent, 'Event')
        CCheckNetMixin.__init__(self)
        CMapActionTypeIdToServiceIdList.__init__(self)
        self.orgId           = None
        self.clientId        = None
        self.clientLastName = None
        self.clientFirstName = None
        self.clientPatrName = None
        self.clientSex       = None
        self.clientBirthDate = None
        self.clientDeathDate = None
        self.clientAge       = None
        self.clientAgeCurrYearEnd = None
        self.clientAgePrevYearEnd = None
        self.clientWorkOrgId = None
        self.clientPolicyInfoList = []
        self.clientType      = CEventEditDialog.ctOther

        self.personId        = None
        self.personSpecialityId= None
        self.personServiceId = None
        self.personFinanceId = None
        self.personTariffCategoryId = None

        self.personSSFCache  = {}

        self.eventTypeId    = None
        self.eventTypeName  = ''
        self.eventPurposeId = None
        self.eventServiceId = None
        self.eventFinanceId = None
        self.eventMedicalAidKindId = None
        self.contractId     = None
        self.dateOfVisitExposition = None
        self.eventPeriod    = 0
        self.eventSetDateTime = None
        self.eventDate      = None
        self.eventContext   = ''
        self.actionTypeDepositIdList = []
        self.isHBDialog = False
        self.isHBEditEvent = False
        self.isTerritorialBelonging = None
        self.mruDescr = None
        self.valueForAllActionEndDate = None
        self.res = None
        self.primaryEntranceCheck = True
        self.isSaveActionsForNomenclatureExpense = False
        self.mapContractIdToFinance = dict()
        self.clientIntoleranceMedicamentRecords = []

#        self.externalId     = ''
#        self.assistantId    = None
#        self.curatorId      = None

        self.getPrevActionIdHelper = CGetPrevActionIdHelper(self)

        self.modifiableDiagnosisesMap = {} # отображение: код по МКБ -> id модифицируемого диагноза.
        self.contractTariffCache = CContractTariffCache()
        #self.setupVisitsIsExposedPopupMenu(parent)
        self._jobTicketRecordsMap2PostUpdate = None
        self.prevEventId = None
        self.setPerson = None
        self.trailerIdx = 0
        self.trailerIdList = {}
        self.trailerActions = []
        self.mapMKBTraumaList = createMapCodeToRowIdx( [row for row in [(u'S00 -T99.9')]]).keys()
        if hasattr(self, 'edtEndDate'):
            self.edtEndDate.setEnabled(QtGui.qApp.userHasRight(urEditEndDateEvent))
        if hasattr(self, 'edtEndTime'):
            self.edtEndTime.setEnabled(QtGui.qApp.userHasRight(urEditEndDateEvent))
        self.actionTypeMDIdList = getActionTypeIdListByFlatCode(u'medicalDiagnosis%')
        self.actionTypeTSIdList = getActionTypeIdListByFlatCode(u'temperatureSheet%')
        self.actionTypeProtocolIdList = getActionTypeIdListByFlatCode(u'protocol%')
        self.excludeList = self.actionTypeMDIdList
        self.excludeList.extend(self.actionTypeTSIdList)
        self.excludeList.extend(self.actionTypeProtocolIdList)
        self.actionTypeHBIdList = []
        self.actionTypeHBIdList.extend(getActionTypeIdListByFlatCode(u'received%'))
        self.actionTypeHBIdList.extend(getActionTypeIdListByFlatCode(u'moving%'))
        self.actionTypeHBIdList.extend(getActionTypeIdListByFlatCode(u'leaved%'))
        self._timeoutLogout = CTimeoutLogout(self)


    def destroy(self):
        pass


    def widgetsVisible(self):
        if not QtGui.qApp.showingFormTempInvalid():
            if hasattr(self, 'tabTempInvalidEtc'):
                self.tabWidget.removeTab(self.tabWidget.indexOf(self.tabTempInvalidEtc))


    def setMedicalDiagnosisContext(self):
        if hasattr(self, 'tabMedicalDiagnosis') and hasattr(self, 'btnPrintMedicalDiagnosis'):
            templates = getPrintTemplates(getMedicalDiagnosisContext())
            if not templates:
                self.btnPrintMedicalDiagnosis.setId(-1)
            else:
                for template in templates:
                    action = CPrintAction(template.name, template.id, self.btnPrintMedicalDiagnosis, self.btnPrintMedicalDiagnosis)
                    self.btnPrintMedicalDiagnosis.addAction(action)
                self.btnPrintMedicalDiagnosis.menu().addSeparator()
                self.btnPrintMedicalDiagnosis.addAction(CPrintAction(u'Напечатать Врачебный диагноз', -1, self.btnPrintMedicalDiagnosis, self.btnPrintMedicalDiagnosis))
            self.btnPrintMedicalDiagnosisEnabled(0)


    def getSurveillanceItems(self, modelDiagnostics):
        dispanserItems = []
        for model in modelDiagnostics:
            items = model.items()
            if items:
                items.sort(key=lambda x: forceDate(x.value('endDate')))
                for idx, record in enumerate(items):
                    dispanserId = forceRef(record.value('dispanser_id'))
                    if dispanserId:
                        dispanserItems.append(record)
        return dispanserItems


    def saveSurveillancePlanning(self, dispanserItems, eventId):
        result = True
        if not forceBool(QtGui.qApp.preferences.appPrefs.get('isPrefSurveillancePlanningDialog', False)):
            return result
        if dispanserItems:
            dialog = CSurveillancePlanningEditDialog(self)
            dialog.setEventEditor(self)
            eventRecord = self.getRecord()
            if eventId:
                eventRecord.setValue('id', toVariant(eventId))
            dialog.setEventRecord(eventRecord)
            dialog.setDiagnosticRecords(dispanserItems)
            try:
                result = dialog.exec_()
                if result == 0:
                    self.setIsAssertNoMessage(True)
            finally:
                dialog.deleteLater()
        return result


    def setupVisitsIsExposedPopupMenu(self):
        if hasattr(self, 'tblVisits'):
            tbl = self.tblVisits
            tbl.setDelRowsIsExposed(lambda rowsExp: not any(map(tbl.model().isExposed, rowsExp)))


    def getExactVisitTypeIdList(self, record):
#        personId     = forceRef(record.value('person_id')) if record else None
#        specialityId = self.getPersonSpecialityId(personId)
        specialityId = None
        return getExactVisitTypeIdList(self.eventTypeId, specialityId, self.clientSex, self.clientAge)


    def setFilterVisitTypeCol(self, index, table, model):
        column = index.column()
        visitTypeColumn = model.getColIndex('visitType_id')
        if getEventRestrictVisitTypeAgeSex(self.eventTypeId) and column == visitTypeColumn:
            visitTypeIdList = self.getExactVisitTypeIdList(table.currentItem())
            model.cols()[visitTypeColumn].setFilter(('id IN (%s) '%(','.join(forceString(visitTypeId) for visitTypeId in visitTypeIdList if visitTypeId))) if visitTypeIdList else '')


    def onActionChanged(self, actionsSummaryRow):
        # Закрытие события по действию нужно везде,
        # а так получалось что это работает только в четырех формах
        # По этому решено вместо заглушки вызывать соответствующие методы,
        # а в addVisitByAction проверять наличие таблицы визитов.
        self.addVisitByActionSummaryRow(actionsSummaryRow)
        self.closeEventByAction(actionsSummaryRow)


    @pyqtSignature('int')
    def on_tabWidget_currentChanged(self, index):
        if hasattr(self, 'tabMes'):
            if index == 1 and self.eventTypeId:
                self.tabMes.setMESServiceTemplate(self.eventTypeId)
        self.btnPrintMedicalDiagnosisEnabled(index)


    def btnPrintMedicalDiagnosisEnabled(self, index):
        if hasattr(self, 'tabMedicalDiagnosis') and hasattr(self, 'btnPrintMedicalDiagnosis'):
            hasRightMedDiag = QtGui.qApp.userHasRight(urReadMedicalDiagnosis)
            if hasRightMedDiag and self.tabWidget.indexOf(self.tabMedicalDiagnosis) == index:
                self.btnPrint.setVisible(not hasRightMedDiag)
                self.btnPrintMedicalDiagnosis.setVisible(hasRightMedDiag)
                self.btnPrintMedicalDiagnosis.setEnabled(hasRightMedDiag)
            else:
                self.btnPrintMedicalDiagnosis.setEnabled(False)
                self.btnPrintMedicalDiagnosis.setVisible(False)
                self.btnPrint.setVisible(True)


    def setFilterResult(self, date):
        filterResult = ('eventPurpose_id=\'%d\'' % (self.eventPurposeId)) if self.eventPurposeId else u''
        filterHealthGroup = u''
        if date:
            db = QtGui.qApp.db
            date = db.formatDate(date)
            filterResult += u'''AND (
            (begDate IS NULL AND endDate IS NULL)
            OR (begDate IS NOT NULL AND endDate IS NOT NULL AND begDate <= %s AND endDate >= %s)
            OR (begDate IS NOT NULL AND endDate IS NULL AND begDate <= %s)
            OR (begDate IS NULL AND endDate IS NOT NULL AND endDate >= %s)
            )'''%(date, date, date, date)
            filterHealthGroup = getHealthGroupFilter(forceString(self.clientBirthDate.toString('yyyy-MM-dd')), forceString(self.eventSetDateTime.date().toString('yyyy-MM-dd')))
        if hasattr(self, 'cmbResult'):
            resultId = self.cmbResult.value()
            self.cmbResult.setFilter(filterResult)
            self.cmbResult.setValue(resultId)
        if hasattr(self, 'modelDiagnostics') and hasattr(self.modelDiagnostics, 'getColIndex'):
            colResult = self.modelDiagnostics.getColIndex('result_id', None)
            if colResult is not None:
                columnResult = self.modelDiagnostics._cols[colResult]
                if isinstance(columnResult, CRBInDocTableCol):
                    self.modelDiagnostics._cols[colResult].setFilter(filterResult)
            colHealthGroup = self.modelDiagnostics.getColIndex('healthGroup_id', None)
            if colHealthGroup is not None:
                columnHealthGroup = self.modelDiagnostics._cols[colHealthGroup]
                if isinstance(columnHealthGroup, CRBInDocTableCol):
                    self.modelDiagnostics._cols[colHealthGroup].setFilter(filterHealthGroup)
        if hasattr(self, 'modelPreliminaryDiagnostics') and hasattr(self.modelPreliminaryDiagnostics, 'getColIndex'):
            colResult = self.modelPreliminaryDiagnostics.getColIndex('result_id', None)
            if colResult is not None:
                columnResult = self.modelPreliminaryDiagnostics._cols[colResult]
                if isinstance(columnResult, CRBInDocTableCol):
                    self.modelPreliminaryDiagnostics._cols[colResult].setFilter(filterResult)
            colHealthGroup = self.modelPreliminaryDiagnostics.getColIndex('healthGroup_id', None)
            if colHealthGroup is not None:
                columnHealthGroup = self.modelPreliminaryDiagnostics._cols[colHealthGroup]
                if isinstance(columnHealthGroup, CRBInDocTableCol):
                    self.modelPreliminaryDiagnostics._cols[colHealthGroup].setFilter(filterHealthGroup)
        if hasattr(self, 'modelFinalDiagnostics') and hasattr(self.modelFinalDiagnostics, 'getColIndex'):
            colResult = self.modelFinalDiagnostics.getColIndex('result_id', None)
            if colResult is not None:
                columnResult = self.modelFinalDiagnostics._cols[colResult]
                if isinstance(columnResult, CRBInDocTableCol):
                    self.modelFinalDiagnostics._cols[colResult].setFilter(filterResult)
            colHealthGroup = self.modelFinalDiagnostics.getColIndex('healthGroup_id', None)
            if colHealthGroup is not None:
                columnHealthGroup = self.modelFinalDiagnostics._cols[colHealthGroup]
                if isinstance(columnHealthGroup, CRBInDocTableCol):
                    self.modelFinalDiagnostics._cols[colHealthGroup].setFilter(filterHealthGroup)


    def protectClosedEvent(self):
        isClosed = self.tabNotes.isEventClosed()
        isProtected = isClosed and not QtGui.qApp.userHasRight(urEditClosedEvent) and not QtGui.qApp.userHasRight(urAdmin) 
        if self.isHBDialog:
            if not isProtected:
                isProtected = QtGui.qApp.userHasRight(urHBReadEvent) and not QtGui.qApp.userHasRight(urHBEditEvent)  # из стац.монитора
        else:
            if not isProtected:
                isProtected = not QtGui.qApp.userHasRight(urRegTabWriteEvents)  # Работа -> Обслуживание
        isProtected = bool(isProtected or self.isReadOnly())
        self.protectFromEdit(isProtected)
        if hasattr(self, 'modelVisits'):
            self.modelVisits.setReadOnly(isProtected)
        if hasattr(self, 'modelActionsSummary'):
            self.modelActionsSummary.setReadOnly(isProtected)
        if hasattr(self, 'modelDiagnostics'):
            self.modelDiagnostics.setReadOnly(isProtected)
        if hasattr(self, 'modelPreliminaryDiagnostics'):
            self.modelPreliminaryDiagnostics.setReadOnly(isProtected)
        if hasattr(self, 'modelFinalDiagnostics'):
            self.modelFinalDiagnostics.setReadOnly(isProtected)
        if hasattr(self, 'tabFeed'):
            if hasattr(self.tabFeed, 'modelClientFeed'):
                self.tabFeed.modelClientFeed.setReadOnly(isProtected)
            if hasattr(self.tabFeed, 'modelPatronFeed'):
                self.tabFeed.modelPatronFeed.setReadOnly(isProtected)
        if hasattr(self, 'modelWorkHurts'):
            self.modelWorkHurts.setReadOnly(isProtected)
        if hasattr(self, 'modelWorkHurtFactors'):
            self.modelWorkHurtFactors.setReadOnly(isProtected)
        if hasattr(self, 'modelDentition'):
            self.modelDentition.setReadOnly(isProtected)
        if hasattr(self, 'modelParodentium'):
            self.modelParodentium.setReadOnly(isProtected)
        if hasattr(self, 'tabMes'):
            self.tabMes.protectFromEdit(isProtected)
        for actionTab in self.getActionsTabsList():
            actionTab.protectFromEdit(isProtected)
            actionTab.modelAPActions.setReadOnly(isProtected)
            actionTab.modelAPActionProperties.setReadOnly(isProtected)
        if hasattr(self, 'tabCash'):
            self.tabCash.protectFromEdit(isProtected and not QtGui.qApp.userHasRight(urEditClosedEventCash))
        if hasattr(self, 'tabTempInvalidEtc'):
            self.grpTempInvalid.protectFromEdit(isProtected)
            self.grpAegrotat.protectFromEdit(isProtected)
            self.grpDisability.protectFromEdit(isProtected)
            self.grpVitalRestriction.protectFromEdit(isProtected)
        if hasattr(self, 'tabNotes'):
            self.tabNotes.protectFromEdit(isProtected and not QtGui.qApp.userHasRight(urEditClosedEventCash))
        if hasattr(self, 'tabVoucher'):
            self.tabVoucher.protectFromEdit(isProtected)


    def protectFromEdit(self, isProtected):
        isEditable = isProtected
        if hasattr(self, 'chkIsClosed'):
            self.chkIsClosed.setEnabled(not isEditable)
        if hasattr(self, 'btnAPActionsAdd'):
            self.btnAPActionsAdd.setEnabled(not isEditable or QtGui.qApp.userHasRight(urEditClosedEventCash))
        if hasattr(self, 'btnRefresh'):
            self.btnRefresh.setEnabled(not isEditable or QtGui.qApp.userHasRight(urEditClosedEventCash))
        if hasattr(self, 'cmbContract'):
            self.cmbContract.setReadOnly(isEditable)
        if hasattr(self, 'edtBegDate'):
            self.edtBegDate.setReadOnly(isEditable)
        if hasattr(self, 'edtBegTime'):
            self.edtBegTime.setReadOnly(isEditable)
        if hasattr(self, 'edtEndDate'):
            self.edtEndDate.setReadOnly(isEditable)
        if hasattr(self, 'edtEndTime'):
            self.edtEndTime.setReadOnly(isEditable)
        if hasattr(self, 'edtNextDate'):
            self.edtNextDate.setReadOnly(isEditable)
        if hasattr(self, 'edtNextTime'):
            self.edtNextTime.setReadOnly(isEditable)
        if hasattr(self, 'cmbPerson'):
            self.cmbPerson.setReadOnly(isEditable)
        if hasattr(self, 'cmbPrimary'):
            self.cmbPrimary.setReadOnly(isEditable)
        if hasattr(self, 'cmbMesSpecification'):
            self.cmbMesSpecification.setReadOnly(isEditable)
        if hasattr(self, 'cmbMes'):
            self.cmbMes.setReadOnly(isEditable)
        if hasattr(self, 'cmbClientRelationConsents'):
            self.cmbClientRelationConsents.setReadOnly(isEditable)
        if hasattr(self, 'chkPrimary'):
            self.chkPrimary.setEnabled(not isEditable)
        if hasattr(self, 'cmbOrder'):
            self.cmbOrder.setReadOnly(isEditable)
        if hasattr(self, 'edtPregnancyWeek'):
            self.edtPregnancyWeek.setReadOnly(isEditable)
        if hasattr(self, 'cmbResult'):
            self.cmbResult.setReadOnly(isEditable)
        if hasattr(self, 'chkConstraintActionTypes'):
            self.chkConstraintActionTypes.setEnabled(not isEditable)
        if hasattr(self, 'edtCommonUet'):
            self.edtCommonUet.setReadOnly(isEditable)
        if hasattr(self, 'cmbRelegatePerson'):
            self.cmbRelegatePerson.setReadOnly(isEditable)
        if hasattr(self, 'cmbRelegateOrg'):
            self.cmbRelegateOrg.setReadOnly(isEditable)
        if hasattr(self, 'btnSelectRelegateOrg'):
            self.btnSelectRelegateOrg.setEnabled(not isEditable)
        if hasattr(self, 'edtEventSrcDate'):
            self.edtEventSrcDate.setReadOnly(isEditable)
        if hasattr(self, 'edtEventSrcNumber'):
            self.edtEventSrcNumber.setReadOnly(isEditable)
        if hasattr(self, 'edtEventExternalIdValue'):
            self.edtEventExternalIdValue.setReadOnly(isEditable)
        if hasattr(self, 'edtEventNote'):
            self.edtEventNote.setReadOnly(isEditable)
        if hasattr(self, 'cmbPatientModel'):
            self.cmbPatientModel.setReadOnly(isEditable)
        if hasattr(self, 'cmbCureType'):
            self.cmbCureType.setReadOnly(isEditable)
        if hasattr(self, 'cmbCureMethod'):
            self.cmbCureMethod.setReadOnly(isEditable)
        if hasattr(self, 'cmbEventCurator'):
            self.cmbEventCurator.setReadOnly(isEditable)
        if hasattr(self, 'cmbPersonMedicineHead'):
            self.cmbPersonMedicineHead.setReadOnly(isEditable)
        if hasattr(self, 'cmbPersonManager'):
            self.cmbPersonManager.setReadOnly(isEditable)
        if hasattr(self, 'cmbPersonExpert'):
            self.cmbPersonExpert.setReadOnly(isEditable)
        if hasattr(self, 'cmbEventAssistant'):
            self.cmbEventAssistant.setReadOnly(isEditable)
        if hasattr(self, 'chkAutopsy'):
            self.chkAutopsy.setEnabled(not isEditable)
        if hasattr(self, 'edtNote'):
            self.edtNote.setReadOnly(isEditable)
        if hasattr(self, 'cmbPerson2'):
            self.cmbPerson2.setReadOnly(isEditable)
        if hasattr(self, 'edtNumber'):
            self.edtNumber.setReadOnly(isEditable)
        if hasattr(self, 'cmbOrg'):
            self.cmbOrg.setReadOnly(isEditable)
        if hasattr(self, 'btnSelectOrganisation'):
            self.btnSelectOrganisation.setEnabled(not isEditable)
        if hasattr(self, 'cmbSetPerson'):
            self.cmbSetPerson.setReadOnly(isEditable)
        if hasattr(self, 'cmbMKB'):
            self.cmbMKB.setReadOnly(isEditable)
        if hasattr(self, 'edtFreeInput'):
            self.edtFreeInput.setReadOnly(isEditable)
        if hasattr(self, 'cmbMorphology'):
            self.cmbMorphology.setReadOnly(isEditable)
        if hasattr(self, 'cmbCharacter'):
            self.cmbCharacter.setReadOnly(isEditable)
        if hasattr(self, 'cmbTraumaType'):
            self.cmbTraumaType.setReadOnly(isEditable)
        if hasattr(self, 'cmbExecPerson'):
            self.cmbExecPerson.setReadOnly(isEditable)
        if hasattr(self, 'cmbDiagnosticResult'):
            self.cmbDiagnosticResult.setReadOnly(isEditable)
        if hasattr(self, 'cmbTissueType'):
            self.cmbTissueType.setReadOnly(isEditable)
        if hasattr(self, 'edtTissueDate'):
            self.edtTissueDate.setReadOnly(isEditable)
        if hasattr(self, 'edtTissueTime'):
            self.edtTissueTime.setReadOnly(isEditable)
        if hasattr(self, 'cmbTissueExecPerson'):
            self.cmbTissueExecPerson.setReadOnly(isEditable)
        if hasattr(self, 'edtTissueAmount'):
            self.edtTissueAmount.setReadOnly(isEditable)
        if hasattr(self, 'cmbTissueUnit'):
            self.cmbTissueUnit.setReadOnly(isEditable)
        if hasattr(self, 'edtTissueExternalId'):
            self.edtTissueExternalId.setReadOnly(isEditable)
        if hasattr(self, 'edtTissueNumber'):
            self.edtTissueNumber.setReadOnly(isEditable)
        if hasattr(self, 'edtTissueNote'):
            self.edtTissueNote.setReadOnly(isEditable)
        if hasattr(self, 'cmbWorkOrganisation'):
            self.cmbWorkOrganisation.setReadOnly(isEditable)
        if hasattr(self, 'btnSelectWorkOrganisation'):
            self.btnSelectWorkOrganisation.setEnabled(not isEditable)
        if hasattr(self, 'edtWorkOrganisationFreeInput'):
            self.edtWorkOrganisationFreeInput.setReadOnly(isEditable)
        if hasattr(self, 'edtWorkPost'):
            self.edtWorkPost.setReadOnly(isEditable)
        if hasattr(self, 'cmbWorkOKVED'):
            self.cmbWorkOKVED.setReadOnly(isEditable)
        if hasattr(self, 'edtWorkStage'):
            self.edtWorkStage.setReadOnly(isEditable)
        if hasattr(self, 'edtPrevDate'):
            self.edtPrevDate.setReadOnly(isEditable)
        if hasattr(self, 'edtNumberCardCall'):
            self.edtNumberCardCall.setReadOnly(isEditable)
        if hasattr(self, 'cmbNumberBrigade'):
            self.cmbNumberBrigade.setReadOnly(isEditable)
        if hasattr(self, 'cmbCauseCall'):
            self.cmbCauseCall.setReadOnly(isEditable)
        if hasattr(self, 'edtWhoCallOnPhone'):
            self.edtWhoCallOnPhone.setReadOnly(isEditable)
        if hasattr(self, 'edtNumberPhone'):
            self.edtNumberPhone.setReadOnly(isEditable)
        if hasattr(self, 'edtStorey'):
            self.edtStorey.setReadOnly(isEditable)
        if hasattr(self, 'edtEntrance'):
            self.edtEntrance.setReadOnly(isEditable)
        if hasattr(self, 'cmbOrgStructure'):
            self.cmbOrgStructure.setReadOnly(isEditable)
        if hasattr(self, 'edtAdditional'):
            self.edtAdditional.setReadOnly(isEditable)
        if hasattr(self, 'edtPassDate'):
            self.edtPassDate.setReadOnly(isEditable)
        if hasattr(self, 'edtPassTime'):
            self.edtPassTime.setReadOnly(isEditable)
        if hasattr(self, 'edtDepartureDate'):
            self.edtDepartureDate.setReadOnly(isEditable)
        if hasattr(self, 'edtDepartureTime'):
            self.edtDepartureTime.setReadOnly(isEditable)
        if hasattr(self, 'edtArrivalDate'):
            self.edtArrivalDate.setReadOnly(isEditable)
        if hasattr(self, 'edtArrivalTime'):
            self.edtArrivalTime.setReadOnly(isEditable)
        if hasattr(self, 'edtFinishServiceDate'):
            self.edtFinishServiceDate.setReadOnly(isEditable)
        if hasattr(self, 'edtFinishServiceTime'):
            self.edtFinishServiceTime.setReadOnly(isEditable)
        if hasattr(self, 'cmbDispatcher'):
            self.cmbDispatcher.setReadOnly(isEditable)
        if hasattr(self, 'cmbGuidePerson'):
            self.cmbGuidePerson.setReadOnly(isEditable)
        if hasattr(self, 'cmbOrderEvent'):
            self.cmbOrderEvent.setReadOnly(isEditable)
        if hasattr(self, 'edtNumberEpidemic'):
            self.edtNumberEpidemic.setReadOnly(isEditable)
        if hasattr(self, 'edtOrderNumber'):
            self.edtOrderNumber.setReadOnly(isEditable)
        if hasattr(self, 'cmbTypeAsset'):
            self.cmbTypeAsset.setReadOnly(isEditable)
        if hasattr(self, 'edtFaceRenunOfHospital'):
            self.edtFaceRenunOfHospital.setReadOnly(isEditable)
        if hasattr(self, 'cmbPlaceReceptionCall'):
            self.cmbPlaceReceptionCall.setReadOnly(isEditable)
        if hasattr(self, 'cmbReceivedCall'):
            self.cmbReceivedCall.setReadOnly(isEditable)
        if hasattr(self, 'cmbReasondDelays'):
            self.cmbReasondDelays.setReadOnly(isEditable)
        if hasattr(self, 'cmbResultCircumstanceCall'):
            self.cmbResultCircumstanceCall.setReadOnly(isEditable)
        if hasattr(self, 'chkDisease'):
            self.chkDisease.setEnabled(not isEditable)
        if hasattr(self, 'chkBirth'):
            self.chkBirth.setEnabled(not isEditable)
        if hasattr(self, 'chkPregnancyFailure'):
            self.chkPregnancyFailure.setEnabled(not isEditable)
        if hasattr(self, 'cmbAccident'):
            self.cmbAccident.setReadOnly(isEditable)
        if hasattr(self, 'cmbDeath'):
            self.cmbDeath.setReadOnly(isEditable)
        if hasattr(self, 'cmbEbriety'):
            self.cmbEbriety.setReadOnly(isEditable)
        if hasattr(self, 'cmbDiseased'):
            self.cmbDiseased.setReadOnly(isEditable)
        if hasattr(self, 'cmbPlaceCall'):
            self.cmbPlaceCall.setReadOnly(isEditable)
        if hasattr(self, 'cmbMethodTransportation'):
            self.cmbMethodTransportation.setReadOnly(isEditable)
        if hasattr(self, 'cmbTransferredTransportation'):
            self.cmbTransferredTransportation.setReadOnly(isEditable)
        if hasattr(self, 'edtDentitionObjectively'):
            self.edtDentitionObjectively.treeView.setReadOnly(isEditable)
            self.edtDentitionObjectively.textEdit.setReadOnly(isEditable)
        if hasattr(self, 'edtDentitionMucosa'):
            self.edtDentitionMucosa.treeView.setReadOnly(isEditable)
            self.edtDentitionMucosa.textEdit.setReadOnly(isEditable)
        if hasattr(self, 'edtDentitionNote'):
            self.edtDentitionNote.setReadOnly(isEditable)
        if hasattr(self, 'cmbDentitionBite'):
            self.cmbDentitionBite.setReadOnly(isEditable)
        if hasattr(self, 'cmbDentitionSanitation'):
            self.cmbDentitionSanitation.setReadOnly(isEditable)
        if hasattr(self, 'cmbDentitionApparat'):
            self.cmbDentitionApparat.setReadOnly(isEditable)
        if hasattr(self, 'cmbDentitionProtezes'):
            self.cmbDentitionProtezes.setReadOnly(isEditable)
        if hasattr(self, 'cmbDentitionOrtodontCure'):
            self.cmbDentitionOrtodontCure.setReadOnly(isEditable)
        if hasattr(self, 'chkExpose'):
            self.chkExpose.setReadOnly(isEditable)
        if hasattr(self, 'btnPlanning'):
            self.btnPlanning.setEnabled(not isEditable)
        if hasattr(self, 'btnRelatedEvent'):
            self.btnRelatedEvent.setEnabled(not isEditable)
        if hasattr(self, 'btnNomenclatureExpense'):
            self.btnNomenclatureExpense.setEnabled((not self.isHBDialog and (not self.tabNotes.isEventClosed() or (self.tabNotes.isEventClosed() and QtGui.qApp.userHasRight(urEditClosedEvent)))) or (self.isHBDialog and (QtGui.qApp.userHasRight(urHBReadEvent) or QtGui.qApp.userHasRight(urHBEditEvent))))


    def getServiceActionCode(self):
        actionTypeIdList = []
        servicesCodeList = QStringList()
        for actionTab in self.getActionsTabsList():
            model = actionTab.modelAPActions
            for record, action in model.items():
                actionTypeId = forceRef(record.value('actionType_id'))
                if actionTypeId and actionTypeId not in actionTypeIdList:
                    actionTypeIdList.append(actionTypeId)
        serviceActionTypeIdList = []
        if actionTypeIdList:
            db = QtGui.qApp.db
            tableActionType = db.table('ActionType')
            tableActionTypeService = db.table('ActionType_Service')
            tableRBService = db.table('rbService')
            table = tableActionType.innerJoin(tableActionTypeService, tableActionType['id'].eq(tableActionTypeService['master_id']))
            table = table.innerJoin(tableRBService, tableRBService['id'].eq(tableActionTypeService['service_id']))
            cond = [tableActionType['id'].inlist(actionTypeIdList), tableActionType['deleted'].eq(0)]
            records = db.getRecordList(table, [tableRBService['infis'], tableActionType['id'].alias('actionTypeId')], cond)
            for record in records:
                actionTypeId = forceRef(record.value('actionTypeId'))
                if actionTypeId and actionTypeId not in serviceActionTypeIdList:
                    serviceActionTypeIdList.append(actionTypeId)
                code = forceString(record.value('infis'))
                if code and code not in servicesCodeList:
                    servicesCodeList.append(QString(code))
        return servicesCodeList


    def closeEventByAction(self, actionsSummaryRow):
        if not hasattr(self, 'modelActionsSummary'):
            return
        actionList = self.modelActionsSummary.items()
        if not (0 <= actionsSummaryRow < len(actionList)):
            return
        closeEvent = False
        eventShowTime = getEventShowTime(self.eventTypeId)
        if hasattr(self, 'edtEndDate'):
            actionEndDate = forceDate(self.edtEndDate.date()) if self.edtEndDate.date().isValid() else QDate()
        else:
            actionEndDate = QDate()
        actionShowTime = False
        for actionRecord in actionList:
            actionTypeId = forceRef(actionRecord.value('actionType_id'))
            actionType   = CActionTypeCache.getById(actionTypeId)
            showTime = actionType.showTime
            if (actionType and actionType.closeEvent):
                closeEvent = True
                endDate = forceDateTime(actionRecord.value('endDate')) if (eventShowTime and showTime) else forceDate(actionRecord.value('endDate'))
                if endDate > actionEndDate:
                    actionEndDate = endDate
                    actionShowTime = showTime
        if not closeEvent:
            return
        if not actionEndDate:
            return
        if eventShowTime and actionShowTime:
            self.setEndDateTime(actionEndDate.date(), actionEndDate.time())
        else:
            self.setEndDate(actionEndDate)


    def setLeavedAction(self, actionTypeIdValue, params = {}):
        currentDateTime = params.get('ExecDateTime', QDateTime.currentDateTime())
        person = params.get('ExecPerson', None)
        result = params.get('ExecResult', None)
        transferTo = params.get('transferTo', None)
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
                correctMovingAction = 0
                for record, action in model.items():
                    actionTypeId = forceRef(record.value('actionType_id'))
                    if actionTypeId in idListActionType:
                        actionType = CActionTypeCache.getById(actionTypeId) if actionTypeId else None
                        if u'moving' in actionType.flatCode.lower():
                            if not forceDate(record.value('endDate')):
                                orgStructureMoving = True
                                orgStructurePresence = action[u'Отделение пребывания']
                                orgStructureTransfer = action[u'Переведен в отделение']
                                hospitalBedId = action[u'койка']
                                if not person:
                                    person = forceInt(record.value('person_id'))
                                movingQuoting = action[u'Квота'] if u'Квота' in action._actionType._propertiesByName else None
                                if not orgStructureTransfer and orgStructurePresence:
                                    orgStructureLeaved = orgStructurePresence
                                correctMovingAction = 1
                        else:
                            orgStructureLeaved = None
                            movingQuoting = None
                        amount = actionType.amount
                        if not forceDate(record.value('endDate')):
                            record.setValue('endDate', toVariant(currentDateTime))
                            record.setValue('status', toVariant(2))
                            if person:
                                record.setValue('person_id', toVariant(person))
                        if actionTypeId:
                            if not(amount and actionType.amountEvaluation == CActionType.userInput):
                                amount = getActionDefaultAmountEx(self, actionType, record, action)
                        else:
                            amount = 0
                        record.setValue('amount', toVariant(amount))
                        model.updateActionAmount(len(model.items())-1)
                if correctMovingAction == 0:
                    QtGui.QMessageBox.critical(self,
                    u'Внимание!',
                    u'Отсутствует открытое действие Движение!',
                    QtGui.QMessageBox.Ok,
                    QtGui.QMessageBox.Ok)
                else:
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
                    if transferTo:
                        action[u'Переведен в стационар'] = transferTo
                    record.setValue('begDate', toVariant(currentDateTime))
                    record.setValue('endDate', toVariant(currentDateTime))
                    record.setValue('directionDate', toVariant(currentDateTime))
                    record.setValue('status', toVariant(2))
                    model.updateActionAmount(len(model.items())-1)
                    if action._actionType.closeEvent:
                        self.edtEndDate.setDate(currentDateTime.date() if isinstance(currentDateTime, QDateTime) else QDate())
                        self.edtEndTime.setTime(currentDateTime.time() if isinstance(currentDateTime, QDateTime) else QTime())


    def translate2ActionsSummaryRow(self, model, modelRow):
        if hasattr(self, 'modelActionsSummary'):
            return self.modelActionsSummary.translate2ActionsSummaryRow(model, modelRow)
        return None

    def checkPersonIdIsEventPerson(self, personId):
        return personId == self.personId


    def checkEqDateAndPersonDuringAddingVisitByAction(self, visitDate, actionEndDate, visitPersonId, actionPersonId):
        return visitDate == actionEndDate and visitPersonId == actionPersonId


    def addVisitByActionSummaryRow(self, actionsSummaryRow, checkActionPersonIdIsEventPerson=False):
        showTime = getEventShowTime(self.eventTypeId)
        if not hasattr(self, 'tblVisits'):
            return
        visitRecord = None

        actionList = self.modelActionsSummary.items()
        visitList = self.modelActionsSummary.visitList
        if not (0 <= actionsSummaryRow < len(actionList)):
            return

        actionRecord = actionList[actionsSummaryRow]
        visitRecord = visitList.get(actionRecord)
        if not visitRecord:
            visitId = forceRef(actionRecord.value('visit_id'))
        actionTypeId = forceRef(actionRecord.value('actionType_id'))
        actionType   = CActionTypeCache.getById(actionTypeId)
        if not (actionType and actionType.addVisit):
            return

        actionEndDate = forceDateTime(actionRecord.value('endDate')) if showTime else forceDate(actionRecord.value('endDate'))
        if not actionEndDate:
            return

        actionPersonId = forceRef(actionRecord.value('person_id'))
        if not actionPersonId:
            return

        addVisit    = True
        visitsModel = self.tblVisits.model()
        visitList   = visitsModel.items()


        if not visitRecord:
            for record in visitList:
                if forceInt(record.value('id')) == visitId:
                    visitRecord = record

        if visitRecord:
            visitRecord.setValue('person_id', actionPersonId )
            visitRecord.setValue('date', actionEndDate )
            visitsModel.reset()
        else:

            if checkActionPersonIdIsEventPerson and not self.checkPersonIdIsEventPerson(actionPersonId):
                return

            for visitRecord in visitList:
                visitDate = forceDate(visitRecord.value('date'))
                visitPersonId = forceRef(visitRecord.value('person_id'))
                if self.checkEqDateAndPersonDuringAddingVisitByAction(visitDate, actionEndDate, visitPersonId, actionPersonId):
                    addVisit = False
                    break

            if addVisit:
                sceneId     = actionType.addVisitSceneId
                visitTypeId = actionType.addVisitTypeId
                visitRecord = visitsModel.addVisit(actionPersonId,  actionEndDate,  sceneId,  visitTypeId)
                self.modelActionsSummary.visitList[ actionRecord ] = visitRecord


    def setPersonDate(self, date):
        def setDateCol(model, date):
            for colName in ('person_id', 'assistant_id', 'setPerson_id'):
                colIndex = model.getColIndex(colName)
                if colIndex > -1:
                    modelCol = model._cols[colIndex]
                    if isinstance(modelCol, CPersonFindInDocTableCol):
                        modelCol.setDate(date)
        if hasattr(self, 'modelVisits'):
            setDateCol(self.modelVisits, date)
        if hasattr(self, 'modelActionsSummary'):
            setDateCol(self.modelActionsSummary, date)
        if hasattr(self, 'modelDiagnostics'):
            setDateCol(self.modelDiagnostics, date)
        if hasattr(self, 'modelPreliminaryDiagnostics'):
            setDateCol(self.modelPreliminaryDiagnostics, date)
        if hasattr(self, 'modelFinalDiagnostics'):
            setDateCol(self.modelFinalDiagnostics, date)
        if hasattr(self, 'modelPersonnel'):
            setDateCol(self.modelPersonnel, date)


    def setExternalId(self, externalId):
        self.lblValueExternalId.setText((u'Номер документа: ' + externalId + u', ') if externalId else '')


    def setMesInfo(self, mesCode):
        self.lblValueMesCode.setText(mesCode)


    def setEndDate(self, date):
        if hasattr(self, 'edtEndDate'):
            # endDate = self.getExecDateTime()
            # if not forceDate(endDate):
            self.edtEndDate.setDate(date)


    def setEndDateTime(self, date, time):
        if hasattr(self, 'edtEndDate'):
            # endDate = self.getExecDateTime()
            # if not forceDate(endDate):
            self.edtEndDate.setDate(date)
            if hasattr(self, 'edtEndTime'):
                self.edtEndTime.setTime(time)


#    TODO: с временем события по закрытию действия отложим пока.
#    def setEndTime(self, time):
#        if hasattr(self, 'edtEndTime'):
#            if not self.edtEndTime.isHidden():
#                print 'asd'
#                currentTime = self.edtEndTime.time()
#                if (not (bool(currentTime) and currentTime.isValid())) and currentTime.hour()==0 and currentTime.minute()==0:
#                    self.edtEndTime.setTime(time)


    def addVisitByAction(self, action):
        if hasattr(self, 'tblVisits'):
            self.tblVisits.model().addVisitByAction(action)


    def setEnabledChkCloseEvent(self, date):
        if hasattr(self, 'tabNotes') and hasattr(self, 'setEnabledChkCloseEvent'):
            self.tabNotes.setEnabledChkCloseEvent(self.getExecDateTime())


    def setCheckedChkCloseEvent(self):
        if hasattr(self, 'tabNotes') and hasattr(self, 'edtEndDate'):
            date = self.edtEndDate.date()
            self.tabNotes.setCheckedChkCloseEvent(date)


    # WTF?
    def setHBUpdateEventRight(self, isHBEditEvent, isHBDialog):
        self.isHBDialog = isHBDialog
        self.isHBEditEvent = isHBEditEvent


    # WTF?
    def getHBUpdateEventRight(self):
        if self.isHBDialog:
            if not self.isHBEditEvent:
                QtGui.QMessageBox.warning( self,
                                         u'Внимание!',
                                         u'Нет права на редактирование события!',
                                         QtGui.QMessageBox.Ok,
                                         QtGui.QMessageBox.Ok)
                return False
        return True


    def checkDataEntered(self):
        result = True
        self.actionTypeDepositIdList = []
        if hasattr(self, 'tabNotes'):
            if self.tabNotes.isEventClosed():
                if not QtGui.qApp.userHasAnyRight([urEditClosedEvent, urEditClosedEventCash]):
                    result = result and self.checkValueMessage(u'Событие закрыто, сохранение данных невозможно!',
                                                               False,
                                                               self.tabNotes.chkIsClosed,
                                                               setFocus=True)
            if getRelegationRequired(self.eventTypeId):
                result = result and self.checkRelegationEntered()

        for actionsTab in self.getActionsTabsList():
            result = result and actionsTab.checkAPRelatedAction()
        # TT4381 "Рассмотреть возможность автоматического добавления тд услуг по лабораторной диагностике из выбранных свойств"
        if hasattr(self, 'tabDiagnostic'):
            result = result and self.tabDiagnostic.checkAPLabDirection()
        elif hasattr(self, 'tabActions'):
            result = result and self.tabActions.checkAPLabDirection()
        # result = result and self.checkDeposit(True)
        for actionsTab in self.getActionsTabsList():
            result = result and actionsTab.checkAPDataEntered()
            
        db = QtGui.qApp.db
        medicalAidTypeId = forceInt(db.translate('EventType', 'id', self.eventTypeId, 'medicalAidType_id'))
        if medicalAidTypeId and forceInt(db.translate('rbMedicalAidType', 'id', medicalAidTypeId, 'regionalCode')) in (111, 112):
            result = result and self.checkRefuseHospitalization()
            
        if getEventMesRequired(self.eventTypeId):
            if self.isActionLeavedEvent():
                result = result and self.checkTemporaryMes()
            mesId = self.getMesId()
            if mesId:
                result = result and self.checkEventMesPeriodicity(mesId)
        if getEventActionsControlRequired(self.eventTypeId):
            result = result and self.checkActionsControl()
        if QtGui.qApp.controlDiagnosticsBlock() in (1, 2):
            result = result and self.checkDiagnosticsControl()
        self.valueForAllActionEndDate = None
        self.res = None
        return result
    
    
    def checkRefuseHospitalization(self):
        from Events.ActionStatus import CActionStatus
        tabActions = None
        if hasattr(self, 'tabActions'):
            tabActions = self.tabActions
        elif hasattr(self, 'tabMisc'):
            tabActions = self.tabMisc
        if tabActions:
            recievedAction = None
            leavedAction = None
            for row, (record, action) in enumerate(tabActions.modelAPActions.items()):
                actionTypeId = forceRef(record.value('actionType_id'))
                actionType = CActionTypeCache.getById(actionTypeId) if actionTypeId else None
                if u'moving' in actionType.flatCode.lower():
                    return True
                if u'received' in actionType.flatCode.lower():
                    if forceRef(record.value('status')) == CActionStatus.finished:
                        recievedAction = (row, record, action)
                    else:
                        return True
                if u'leaved' in actionType.flatCode.lower():
                    if forceRef(record.value('status')) == CActionStatus.finished:
                        leavedAction = (row, record, action)
                    else:
                        return True
            if recievedAction and leavedAction:
                receivedPropertyRef = recievedAction[2].getProperty(u'Причина отказа от госпитализации')
                receivedPropertyAct = recievedAction[2].getProperty(u'Принятые меры при отказе в госпитализации')
                if not receivedPropertyRef.getValue():
                    self.checkValueMessage(u'Заполните поле "Причина отказа от госпитализации"',
                                           False, tabActions.tblAPActions, row=recievedAction[0], column=0)
                    index = tabActions.tblAPProps.model().index(recievedAction[2].getIndexByProperty(receivedPropertyRef), 1)
                    self.setFocusToWidget(tabActions.tblAPProps, recievedAction[2].getIndexByProperty(receivedPropertyRef), 1)
                    QTimer.singleShot(0, lambda: tabActions.tblAPProps.scrollTo(index, QtGui.QAbstractItemView.PositionAtTop))
                    return False
                if not receivedPropertyAct.getValue():
                    self.checkValueMessage(u'Заполните поле "Принятые меры при отказе в госпитализации"',
                                           False, tabActions.tblAPActions, row=recievedAction[0], column=0)
                    index = tabActions.tblAPProps.model().index(recievedAction[2].getIndexByProperty(receivedPropertyAct), 1)
                    self.setFocusToWidget(tabActions.tblAPProps, recievedAction[2].getIndexByProperty(receivedPropertyAct), 1)
                    QTimer.singleShot(0, lambda: tabActions.tblAPProps.scrollTo(index, QtGui.QAbstractItemView.PositionAtTop))
                    return False
        return True


    def checkDiagnosticsControl(self):
        result = True
        if QtGui.qApp.controlDiagnosticsBlock() == 1:
            skipable = True
        else:
            skipable = False
        if hasattr(self, 'modelDiagnostics') and hasattr(self.modelDiagnostics, 'getColIndex'):
            mkbIndex = self.modelDiagnostics.getColIndex('MKB', None)
            personIndex = self.modelDiagnostics.getColIndex('person_id', None)
            modelDiagnostics = self.modelDiagnostics
        elif hasattr(self, 'modelPreliminaryDiagnostics') and hasattr(self.modelPreliminaryDiagnostics, 'getColIndex'):
            mkbIndex = self.modelPreliminaryDiagnostics.getColIndex('MKB', None)
            personIndex = self.modelPreliminaryDiagnostics.getColIndex('person_id', None)
            modelDiagnostics = self.modelPreliminaryDiagnostics
        elif hasattr(self, 'modelFinalDiagnostics') and hasattr(self.modelFinalDiagnostics, 'getColIndex'):
            mkbIndex = self.modelFinalDiagnostics.getColIndex('MKB', None)
            personIndex = self.modelFinalDiagnostics.getColIndex('person_id', None)
            modelDiagnostics = self.modelFinalDiagnostics
        else:
            modelDiagnostics = None
        if modelDiagnostics:
            diagnostics = {}
            for row in range(modelDiagnostics.rowCount()):
                if forceString(modelDiagnostics.data(modelDiagnostics.index(row, mkbIndex))) != u'':
                    if personIndex:
                        personId = forceString(modelDiagnostics.data(modelDiagnostics.index(row, personIndex)))
                    else:
                        personId = self.cmbPerson.value()
                    if personId not in diagnostics.keys():
                        diagnostics[personId] = []
                    diagnostic = forceString(modelDiagnostics.data(modelDiagnostics.index(row, mkbIndex)))[:3]
                    diagnostics[personId].append(diagnostic)
            for key, value in diagnostics.items():
                if len(set(value)) < len(value) and self.eventContext and self.eventContext[:4] != u'f131':
                    message = u'Один и тот же врач не может устанавливать в одном и том же событии диагнозы из одного блока'
                    return self.checkValueMessage(message, skipable, modelDiagnostics, row, mkbIndex, setFocus=False)
        return result


    def checkEventResult(self):
        result = True
        if not bool(QtGui.qApp.provinceKLADR()[:2] == u'23' and CFinanceType.getCode(self.eventFinanceId) == 2):
            return result
        endDateCheck = self.edtEndDate.date()
        if hasattr(self, 'modelDiagnostics'):
            modelDiagnostics = self.modelDiagnostics
        elif hasattr(self, 'modelFinalDiagnostics'):
            modelDiagnostics = self.modelFinalDiagnostics
        else:
            modelDiagnostics = None
        if modelDiagnostics:
            diagResultId = modelDiagnostics.resultId()
            eventResultId = self.cmbResult.value()
            if eventResultId and diagResultId:
                db = QtGui.qApp.db
                table = db.table('soc_checkSpr12')
                ishlCode = forceString(db.translate('rbDiagnosticResult', 'id', diagResultId, 'regionalCode'))
                ishodObrCode = forceString(db.translate('rbResult', 'id', eventResultId, 'regionalCode'))
                cond = [table['code'].eq(ishodObrCode),
                        table['code_ishl'].contain(ishlCode),
                        table['begDate'].le(endDateCheck),
                        table['endDate'].gt(endDateCheck.addDays(1))
                        ]
                count = db.getCount(table, where=cond)
                result = count > 0
        if not result:
            return self.checkValueMessage(u'Результат обращения не соответствует результату лечения', False, self.cmbResult)
        return result


    def checkRelegationEntered(self):
        if getEventTypeForm(self.eventTypeId) == u'072':
            objOrgs = self.tabVoucher.cmbDirectionOrgs
            objDate = self.tabVoucher.edtDirectionDate
            objNumber = self.tabVoucher.edtDirectionNumber
        elif hasattr(self, 'tabNotes'):
            objOrgs = self.tabNotes.cmbRelegateOrg if hasattr(self.tabNotes, 'cmbRelegateOrg') else None
            objDate = self.tabNotes.edtEventSrcDate if hasattr(self.tabNotes, 'edtEventSrcDate') else None
            objNumber = self.tabNotes.edtEventSrcNumber if hasattr(self.tabNotes, 'edtEventSrcNumber') else None
        else:
            objOrgs = None
            objDate = None
            objNumber = None
        relegateOrg = self.getRelegateOrgId()
        if not relegateOrg and objOrgs:
            QtGui.QMessageBox.warning( self,
                         u'Внимание!',
                         u'Требуется указание направителя',
                         QtGui.QMessageBox.Ok,
                        QtGui.QMessageBox.Ok)
            self.setFocusToWidget(objOrgs, None, None)
            return False
        srcDate = self.getSrcDate()
        if not srcDate and objDate:
            QtGui.QMessageBox.warning( self,
                         u'Внимание!',
                         u'Требуется указание даты направления',
                         QtGui.QMessageBox.Ok,
                        QtGui.QMessageBox.Ok)
            self.setFocusToWidget(objDate, None, None)
            return False
        srcNumber = self.getSrcNumber()
        if not srcNumber and objNumber:
            QtGui.QMessageBox.warning( self,
                         u'Внимание!',
                         u'Требуется указание номера направления',
                         QtGui.QMessageBox.Ok,
                        QtGui.QMessageBox.Ok)
            self.setFocusToWidget(objNumber, None, None)
            return False
        return True


    def checkRequiresFillingDispanser(self, result, widget, record, row, MKB):
        db = QtGui.qApp.db
        table = db.table('MKB')
        recordMKB = db.getRecordEx(table, [table['requiresFillingDispanser']], [table['DiagID'].eq(MKB)], 'MKB.DiagID')
        requiresFillingDispanser = forceInt(recordMKB.value('requiresFillingDispanser')) if recordMKB else None
        if requiresFillingDispanser:
            dispanserId = forceRef(record.value('dispanser_id'))
            phaseCode = None
            phaseId = forceRef(record.value('phase_id'))
            if phaseId:
                tableDiseasePhases = db.table('rbDiseasePhases')
                recordDS = db.getRecordEx(tableDiseasePhases, [tableDiseasePhases['code']], [tableDiseasePhases['id'].eq(phaseId)])
                phaseCode = forceString(recordDS.value('code')) if recordDS else None
            if phaseCode != u'10' or requiresFillingDispanser != 2:
                result = result and dispanserId or self.checkValueMessage(u'Для диагноза %s необходимо указать статус ДН'%(MKB), True if requiresFillingDispanser == 1 else False, widget, row, record.indexOf('dispanser_id'))
            else:
                result = result and not dispanserId or self.checkValueMessage(u'Для диагноза %s с фазой Подозрение указано Диспансерное наблюдение. Вы уверены, что Диспансерное наблюдение должно быть заполнено?'%(MKB), True, widget, row, record.indexOf('dispanser_id'))
        return result


    def checkPersonSpeciality(self, record, row, widget):
        specialityId = forceRef(QtGui.qApp.db.translate('Person', 'id', forceRef(record.value('person_id')), 'speciality_id'))
        if not specialityId:
            self.checkValueMessage(u'Указанный врач не имеет специальности. Выберите врача со специальностью.', False, widget, row, record.indexOf('person_id'))
            return False
        return True

    
    def checkPersonSpecialityDiagnostics(self, model, table):
        for row, record in enumerate(model.items()):
            if not self.checkDiagnosticPersonSpeciality(row, record, table):
                return False
        return True


    def checkDiagnosticPersonSpeciality(self, row, record, table):
        return self.checkPersonSpeciality(record, row, table)
    

    def checkExecPersonSpeciality(self, personId, widget):
        specialityId = forceRef(QtGui.qApp.db.translate('Person', 'id', personId, 'speciality_id'))
        if not specialityId:
            self.checkValueMessage(u'У ответственного за событие не указана специальность. Выберите врача со специальностью.', False, widget)
            return False
        return True


    def checkPeriodResultHealthGroup(self, record, row, widget):
        db = QtGui.qApp.db
        resultId = forceRef(record.value('result_id'))
        healthGroupId = forceRef(record.value('healthGroup_id'))
        endDate = self.edtEndDate.date()
        if healthGroupId:
            tableHG = db.table('rbHealthGroup')
            cond = [tableHG['id'].eq(healthGroupId)]
            cond.append(db.joinOr([tableHG['begDate'].isNull(), tableHG['begDate'].le(endDate)]))
            cond.append(db.joinOr([tableHG['endDate'].isNull(), tableHG['endDate'].ge(endDate)]))
            recordRes = db.getRecordEx(tableHG, [tableHG['id']], cond)
            if not recordRes:
                self.checkValueMessage(u'Значение группы здоровья устарело', False, widget, row, record.indexOf('healthGroup_id'))
                return False
        if resultId:
            tableDR = db.table('rbDiagnosticResult')
            cond = [tableDR['id'].eq(resultId)]
            cond.append(db.joinOr([tableDR['begDate'].isNull(), tableDR['begDate'].le(endDate)]))
            cond.append(db.joinOr([tableDR['endDate'].isNull(), tableDR['endDate'].ge(endDate)]))
            recordRes = db.getRecordEx(tableDR, [tableDR['id']], cond)
            if not recordRes:
                self.checkValueMessage(u'Значение результата диагноза устарело', False, widget, row, record.indexOf('result_id'))
                return False
        return True


    def checkOfPeriodFeeds(self, setDate, execDate, showTime):
        result = True
        if hasattr(self, 'tabFeed'):
            if showTime:
                setDate = setDate.date()
                execDate = execDate.date()
            if hasattr(self.tabFeed, 'modelClientFeed'):
                result = result and self.checkOfPeriodFeed(setDate, execDate, self.tabFeed.modelClientFeed, self.tabFeed.tblClientFeed, 0)
            if hasattr(self.tabFeed, 'modelPatronFeed'):
                result = result and self.checkOfPeriodFeed(setDate, execDate, self.tabFeed.modelPatronFeed, self.tabFeed.tblPatronFeed, 1)
        return result


    def checkOfPeriodFeed(self, setDate, execDate, model, widget, feedIndex):
        result = True
        for row, date in enumerate(model.dates):
            if date:
                feedDate = QDate(date)
                if setDate:
                    result = result and (feedDate >= setDate or self.checkValueMessage(u'Период питания %s %s не может быть раньше даты начала события %s.' % (u'лица по уходу' if feedIndex else u'пациента', forceString(feedDate), forceString(setDate)), False, widget, row, 0))
                    if not result:
                        return result
                if execDate:
                    result = result and (feedDate <= execDate or self.checkValueMessage(u'Период питания %s %s не может быть позже даты окончания события %s.' % (u'лица по уходу' if feedIndex else u'пациента', forceString(feedDate), forceString(execDate)), False, widget, row, 0))
                    if not result:
                        return result
        return result


#    def getFinalMKB(self):
#        model = self.
#        for row, record in enumerate(model.items()):
#            if  forceInt(record.value('diagnosisType_id')) == model.diagnosisTypeCol.ids[0]:
#                return True
#        return False


    def checkActionsControl(self):
        db = QtGui.qApp.db
        table = db.table('EventType_ActionControl')
        rules = {}
        actions = {}
        actionGroups = {}
        actionTypeToActionMap = {}
        recordList = db.getRecordList(table, '*', table['eventType_id'].eq(self.eventTypeId))
        for record in recordList:
            template = forceString(record.value('template'))
            amount = forceInt(record.value('amount'))
            actionTypeId = forceInt(record.value('actionType_id'))
            rule = rules.setdefault(template, [])
            rule.append({'actionType': actionTypeId, 'amount': amount, 'founded': False})

        for actionTab in self.getActionsTabsList():
            model = actionTab.tblAPActions.model()
            for row, (record, action) in enumerate(model.items()):
                actionType = action.getType()
                MKB = forceString(record.value('MKB'))
                actions[(actionType.id, MKB)] = {'record': record, 'code': actionType.code}
        for tmpl in rules.keys():
            ruleRe = re.compile(tmpl)
            for (actionTypeId, MKB) in actions:
                actionTypeCode = actions[(actionTypeId, MKB)]['code']
                if ruleRe.search(actionTypeCode):
                    group = actionGroups.setdefault((tmpl, MKB), {'count': 0})
                    if 'founded' not in group:
                        group['founded'] = False
                        for rule in rules[tmpl]:
                            if (rule['actionType'], MKB) in actions :
                                group['founded'] = True
                                break

                    group['count'] += 1
                    group['record'] = actions[(actionTypeId, MKB)]['record']

        dlg = CActionsControlDialog(self)
        for g in sorted(actionGroups.keys()):
            for rule in rules[g[0]]:
                if actionGroups[g]['count'] >= rule['amount']:
                    if not actionGroups[g]['founded']:
                        index = dlg.addChoise(g[0], g[1], rule['actionType'])
                        actionTypeToActionMap[index] = (rule['actionType'], actionGroups[g]['record'])
        if dlg.ready:
            if dlg.exec_():
                indexes = dlg.getSelected()
                if hasattr(self, 'tblActions'):
                    model = self.tblActions.model()
                    for ATIndex in indexes:
                        (actionTypeId, record) = actionTypeToActionMap[ATIndex]
                        class_ = forceInt(QtGui.qApp.db.translate('ActionType', 'id', actionTypeId, 'class'))
                        index = model.index(model.rowCount()-1, 0)
                        model.setData(index, toVariant(actionTypeId))
                        actionRecord = model._items[model.rowCount()-2]
                        for field in ['MKB', 'setPerson_id', 'person_id', 'assistant_id', 'finance_id',
                                'directionDate', 'begDate', 'endDate', 'plannedDate']:
                            actionRecord.setValue(field, record.value(field))
                else:
                    actionsTabsList = self.getActionsTabsList()
                    if len(actionsTabsList) == 4:
                        for ATIndex in indexes:
                            (actionTypeId, record) = actionTypeToActionMap[ATIndex]
                            class_ = forceInt(QtGui.qApp.db.translate('ActionType', 'id', actionTypeId, 'class'))
                            actionsTab = actionsTabsList[class_]
                            model = actionsTab.tblAPActions.model()
                            model.addRow(actionTypeId)
                            actionRecord = model._items[model.rowCount()-2][0]
                            for field in ['MKB', 'setPerson_id', 'person_id', 'assistant_id', 'finance_id',
                                'directionDate', 'begDate', 'endDate', 'plannedDate']:
                                actionRecord.setValue(field, record.value(field))
                if indexes:
                    return False
        return True


    def checkActualMKB(self, widget, date, MKB, record = None, row=None):
        result = True
        db = QtGui.qApp.db
        tableMKB = db.table('MKB')
        cond = [tableMKB['DiagID'].eq(MKBwithoutSubclassification(MKB))]
        cond.append(db.joinOr([tableMKB['endDate'].isNull(), tableMKB['endDate'].dateGe(date)]))
        recordMKB = db.getRecordEx(tableMKB, [tableMKB['DiagID']], cond)
        result = result and (forceString(recordMKB.value('DiagID')) == MKBwithoutSubclassification(MKB) if recordMKB else False) or self.checkValueMessage(u'Диагноз %s не доступен для применения'%MKB, False, widget, row, record.indexOf('MKB') if record else None)
        
        # проверка на "оплачиваемость" диагноза в системе ОМС для КК
        if record and result:
            diagnosisTypeId = forceRef(record.value('diagnosisType_id'))
            diagnosisTypeCode = forceString(db.translate('rbDiagnosisType', 'id', diagnosisTypeId, 'code'))
            if result and QtGui.qApp.provinceKLADR()[:2] == u'23' and CFinanceType.getCode(self.eventFinanceId) == 2 and diagnosisTypeCode in ['1', '2']:
                tableSpr20 = db.table('soc_spr20')
                if date:
                    cond = [db.joinOr([tableSpr20['code'].eq(MKB), tableSpr20['code'].eq(MKB[:3])]),
                            db.joinOr([tableSpr20['dato'].isNull(), tableSpr20['dato'].dateGe(date)]),
                            tableSpr20['datn'].dateLe(date)]
                else:
                    cond = [db.joinOr([tableSpr20['code'].eq(MKB), tableSpr20['code'].eq(MKB[:3])]),
                            tableSpr20['dato'].isNull()]
                recordMKB = db.getRecordEx(tableSpr20, [tableSpr20['code']], cond)
                if not recordMKB:
                    result = self.checkValueMessage(u'Диагноз %s не оплачивается в системе ОМС!'%MKB, QtGui.qApp.userHasRight(urCanSaveEventWithMKBNotOMS), widget, row, record.indexOf('MKB') if record else None)
        return result
    

    def isActionLeavedEvent(self):
        for actionTab in self.getActionsTabsList():
            model = actionTab.tblAPActions.model()
            for row, (record, action) in enumerate(model.items()):
                if action and action._actionType.id:
                    actionTypeItem = action.getType()
                    if actionTypeItem and (u'leaved' in actionTypeItem.flatCode.lower()):
                        return True
        return True


    def checkTemporaryMes(self):
        u'''проверить временный МЭС?'''
        result = True
        eventId = self.itemId()
        if eventId or self.prevEventId:
            idList = set([])
            db = QtGui.qApp.db
            tableEvent = db.table('Event')
            idListParents = set(db.getTheseAndParents(tableEvent, 'prevEvent_id', [eventId if eventId else self.prevEventId]))
            idList |= idListParents
            idListDescendant = set(db.getDescendants(tableEvent, 'prevEvent_id', eventId if eventId else self.prevEventId))
            if len(idListDescendant) > 1 or (len(idListDescendant) == 1 and idListDescendant != set([eventId if eventId else self.prevEventId])):
                idList |= idListDescendant
            if idList:
                self.getCodeMesPrevEvent(idList)
                tableMES = db.table('mes.MES')
                mesCodeRecords = db.getRecordList(tableEvent.innerJoin(tableMES, tableMES['id'].eq(tableEvent['MES_id'])),
                                                  [tableEvent['id'].alias('event_id'), tableMES['code'], tableMES['id']],
                                                  [tableEvent['deleted'].eq(0), tableEvent['id'].inlist(idList), tableMES['code'].eq(u'000000')])
                if mesCodeRecords:
                    return False
        mesCode = self.getMesCode()
        if hasattr(self, 'tabMes'):
            result = result and ((not mesCode or mesCode != u'000000') or self.checkInputMessage(u'вместо внутреннего МЭСа корректный МЭС', False, self.tabMes.cmbMes))
        return result


    def getCodeMesPrevEvent(self, idList):
        u'''Получить событие предыдущего меса кода?'''
        db = QtGui.qApp.db
        tableMES = db.table('mes.MES')
        tableEvent = db.table('Event')
        mesCodeRecords = db.getRecordList(tableEvent.innerJoin(tableMES, tableMES['id'].eq(tableEvent['MES_id'])),
                                          [tableEvent['id'].alias('event_id'), tableMES['code'], tableMES['id']],
                                          [tableEvent['deleted'].eq(0), tableEvent['id'].inlist(idList), tableMES['code'].eq(u'000000')])
        for mesCodeRecord in mesCodeRecords:
            mesEventId = forceRef(mesCodeRecord.value('event_id'))
            res = QtGui.QMessageBox.warning( self,
                         u'Внимание!',
                         u'В Событие %d вместо внутреннего МЭСа необходимо ввести корректный МЭС'%(mesEventId),
                         QtGui.QMessageBox.Ok|QtGui.QMessageBox.Cancel,
                         QtGui.QMessageBox.Cancel)
            if res == QtGui.QMessageBox.Ok:
                self.openEvent(mesEventId)


    def openEvent(self, eventId):
        from EditDispatcher               import getEventFormClass
        if eventId:
            db = QtGui.qApp.db
            isHBReadEvent = QtGui.qApp.userHasRight(urHBReadEvent)
            isHBEditEvent = QtGui.qApp.userHasRight(urHBEditEvent)
            tableEvent = db.table('Event')
            record = db.getRecordEx(tableEvent,
                                    [tableEvent['payStatus'], tableEvent['id']],
                                    [tableEvent['id'].eq(eventId), tableEvent['deleted'].eq(0)])
            if not record:
                return
            payStatus = forceInt(record.value('payStatus'))
            if payStatus:
                isHBEditEvent = QtGui.qApp.userHasRight(urEditAfterInvoicingEvent)
                if isHBEditEvent:
                    message = u'Данное событие включено в счёт\nи его данные изменять нежелательно!\nВы настаиваете на изменении?'
                    if not QtGui.QMessageBox.critical(self, u'Внимание!', message, QtGui.QMessageBox.Yes|QtGui.QMessageBox.No, QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
                        return
                else:
                    message = u'Данное событие включено в счёт\nи его данные не могут быть изменены!'
                    QtGui.QMessageBox.critical(self, u'Внимание!', message)
                    if not isHBReadEvent:
                        return
            if isHBReadEvent or isHBEditEvent:
                try:
                    formClass = getEventFormClass(eventId)
                    dialog = formClass(self)
                    dialog.load(eventId)
                    QtGui.qApp.restoreOverrideCursor()
                    dialog.setHBUpdateEventRight(isHBEditEvent, True)
                    dialog.setReadOnly(isHBReadEvent and not isHBEditEvent)
                    if hasattr(dialog, 'tabMes'):
                        self.setFocusToWidget(dialog.tabMes.cmbMes, None, None)
                    if dialog.exec_():
                        pass
                finally:
                    dialog.deleteLater()
            else:
                QtGui.QMessageBox.warning( self,
                                         u'Внимание!',
                                         u'Нет права на чтение и редактирование события!',
                                         QtGui.QMessageBox.Ok,
                                         QtGui.QMessageBox.Ok)


    def _getEventIdChain(self):
        result = []
        if self.itemId():
            result.append(self.itemId())
        prevEventId = self.prevEventId
        while prevEventId:
            result.append(prevEventId)
            prevEventId = forceRef(QtGui.qApp.db.translate('Event', 'id', prevEventId, 'prevEvent_id'))
        return result


    def checkEventMesPeriodicity(self, mesId):
        db = QtGui.qApp.db
        periodicity = forceInt(db.translate('mes.MES', 'id', mesId, 'periodicity'))
        if periodicity:
            condDate = self.edtBegDate.date().addDays(-periodicity)
            if condDate:
                tableEvent = db.table('Event')
                cond = [tableEvent['deleted'].eq(0),
                        tableEvent['MES_id'].eq(mesId),
                        tableEvent['execDate'].isNotNull(),
                        tableEvent['execDate'].dateGt(condDate),
                        tableEvent['client_id'].eq(self.clientId)]
                if self.prevEventId:
                    cond.append(tableEvent['id'].notInlist(self._getEventIdChain()))
                else:
                    if self.itemId():
                        cond.append(tableEvent['id'].ne(self.itemId()))
                query = db.query('SELECT %s'%db.existsStmt(tableEvent, cond))
                if query.next():
                    if forceInt(query.value(0)):
                        return self.checkValueMessage(u'Событие пересекается по переодичности применения МЭСа с предыдущими', False if QtGui.qApp.isControlEventMesPeriodicity() else True, self.edtBegDate)
        return True


    def postSetupUi(self):
        self.createJobTicketsButton()
        self.createActionAddButton()
        self.createNomenclatureExpenseButton()
        self.createApplyButton()
        self.createRefreshButton()


    def createApplyButton(self):
        self.addObject('btnApply', QtGui.QPushButton(u'Применить', self))
        self.buttonBox.addButton(self.btnApply, QtGui.QDialogButtonBox.ApplyRole)
        self.connect(self.btnApply, SIGNAL('clicked()'), self.on_btnApply_clicked)


    def createRefreshButton(self):
        self.addObject('btnRefresh', QtGui.QPushButton(u'Обновить', self))
        self.buttonBox.addButton(self.btnRefresh, QtGui.QDialogButtonBox.ActionRole)
        self.connect(self.btnRefresh, SIGNAL('clicked()'), self.on_btnRefresh_clicked)


    def createNomenclatureExpenseButton(self):
        self.addObject('btnNomenclatureExpense', QtGui.QPushButton(u'Назначение ЛС', self))
        self.buttonBox.addButton(self.btnNomenclatureExpense, QtGui.QDialogButtonBox.ActionRole)
        self.connect(self.btnNomenclatureExpense, SIGNAL('clicked()'), self.on_btnNomenclatureExpense_clicked)
        self.btnNomenclatureExpense.setShortcut('Shift+F2')


    def createJobTicketsButton(self):
        self.addObject('btnJobTickets', QtGui.QPushButton(u'Работы', self))
        self.buttonBox.addButton(self.btnJobTickets, QtGui.QDialogButtonBox.ActionRole)
        self.connect(self.btnJobTickets, SIGNAL('clicked()'), self.on_btnJobTickets_clicked)


    def createActionAddButton(self):
        self.addObject('btnAPActionsAdd', QtGui.QPushButton(u'Добавить (F9)', self))
        self.buttonBox.addButton(self.btnAPActionsAdd, QtGui.QDialogButtonBox.ActionRole)
        self.connect(self.btnAPActionsAdd, SIGNAL('clicked()'), self.on_btnAPActionsAdd_triggered)

    def on_btnNomenclatureExpense_clicked(self):
        nomenclatureExpenseGroups = []
        for tab in self.getActionsTabsList():
            items = tab.modelAPActions.items()
            for group in items.groupsIterator:
                if hasattr(group, 'requireEP') and group.requireEP:
                    nomenclatureExpenseGroups.append(group)

        dialog = CNomenclatureExpenseDialog(self, eventEditor=self, groups=nomenclatureExpenseGroups)
        dialog.setEventEditor(self)
        dialog.setHBUpdateEvent(self.isHBDialog)
        if self.isHBDialog:
            dialog.setReadOnly(QtGui.qApp.userHasRight(urHBReadEvent) and not QtGui.qApp.userHasRight(urHBEditEvent))
        dialog.protectWidgetFromEdit()
        dialog.exec_()
        self.clientIntoleranceMedicamentRecords = dialog.getClientIntoleranceMedicamentRecords()


    def loadEventDiagnostics(self, modelDiagnostics, eventId):
        db = QtGui.qApp.db
        tableDiagnostic = db.table('Diagnostic')
        tableRBDiagnosisType = db.table('rbDiagnosisType')
        table = tableDiagnostic.innerJoin(tableRBDiagnosisType, tableRBDiagnosisType['id'].eq(tableDiagnostic['diagnosisType_id']))
        cond = [tableDiagnostic['deleted'].eq(0), tableDiagnostic['event_id'].eq(eventId)]
        cond.append('''(rbDiagnosisType.code = '1'
OR (rbDiagnosisType.code = '2'
AND (NOT EXISTS (SELECT DC.id FROM Diagnostic AS DC
INNER JOIN rbDiagnosisType AS DT ON DT.id = DC.diagnosisType_id WHERE DT.code = '1'
AND DC.event_id = %s
LIMIT 1))))'''%(str(eventId)))
        rawItems = db.getRecordList(table, '*', cond, 'Diagnostic.id')
        items = []
        isDiagnosisManualSwitch = modelDiagnostics.manualSwitchDiagnosis()
        for record in rawItems:
#            specialityId = forceRef(record.value('speciality_id'))
            diagnosisId     = record.value('diagnosis_id')
            MKB             = db.translate('Diagnosis', 'id', forceRef(diagnosisId), 'MKB')
            MKBEx           = db.translate('Diagnosis', 'id', forceRef(diagnosisId), 'MKBEx')
            morphologyMKB   = db.translate('Diagnosis', 'id', forceRef(diagnosisId), 'morphologyMKB')
            setDate         = forceDate(record.value('setDate'))
            TNMS            = forceString(record.value('TNMS'))
            diagnosisTypeCode = forceString(record.value('code'))
            newRecord =  modelDiagnostics.getEmptyRecord()
            copyFields(newRecord, record)
            newRecord.setValue('MKB',           MKB)
            newRecord.setValue('MKBEx',         MKBEx)
            newRecord.setValue('TNMS',          toVariant(TNMS))
            newRecord.setValue('morphologyMKB', morphologyMKB)
            if diagnosisTypeCode != 7:
                diagnosisTypeId = db.translate('rbDiagnosisType', 'code', '7', 'id')
                newRecord.setValue('diagnosisType_id', toVariant(diagnosisTypeId))
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


    def createSaveAndCreateAccountButton(self):
        self.addObject('btnSaveAndCreateAccount', QtGui.QPushButton(u'Сохранить и создать счёт', self))


    def setupSaveAndCreateAccountButton(self):
        if hasattr(self, 'btnSaveAndCreateAccount'):
            self.buttonBox.addButton(self.btnSaveAndCreateAccount, QtGui.QDialogButtonBox.ActionRole)


    def setupActionSummarySlots(self):
        self.connect(self.modelActionsSummary, SIGNAL('currentRowMovedTo(int)'), self.onActionsSummaryCurrentRowMovedTo)


    def getPayStatusAdditional(self, tableName, eventId):
        db = QtGui.qApp.db
        table = db.table(tableName)
        record = db.getRecordEx(table, [table['payStatus']], [table['event_id'].eq(eventId),
                                                              table['payStatus'].ne(0),
                                                              table['deleted'].eq(0)])
        return forceInt(record.value('payStatus')) if record else 0

    def getPayStatusReason(self, tableName, eventId):
        db = QtGui.qApp.db
        table = db.table(tableName)
        record = db.getRecordEx(table, [table['refuseType_id'], table['reexposeItem_id'], table['number'], table['date']],
                                [table['event_id'].eq(eventId),
                                 table['refuseType_id'].isNotNull(),
                                 table['reexposeItem_id'].isNull(),
                                 table['number'].isNotNull(),
                                 table['date'].isNotNull()])
        if record:
            return 0 #отказ
        else:
            return -1  #

    def checkDataBeforeOpen(self):
        record = self.record()
        if record:
            if not self.isReadOnly() and self.cmbContract.value() != forceRef(record.value('contract_id')):
                self.setIsDirty(True)

            payStatus = forceInt(record.value('payStatus'))
            isClosed  = forceInt(record.value('isClosed'))

            eventId = forceRef(record.value('id'))

            payStatusReason = self.getPayStatusReason('Account_Item', eventId)

            payStatusVisit  = self.getPayStatusAdditional('Visit', eventId)
            payStatusAction = self.getPayStatusAdditional('Action', eventId)
            isRegTabReadEvent = QtGui.qApp.userHasRight(urRegTabReadEvents)

            if (payStatusReason != 0) or (payStatusReason == 0 and not QtGui.qApp.userHasRight(urEditAfterReturnEvent)):
                if payStatus or (isClosed and (payStatusVisit or payStatusAction)):
                    if QtGui.qApp.userHasRight(urEditAfterInvoicingEvent):
                        message = u''
                        if payStatus:
                            message = u'Данное событие выставлено в счёт\nи его данные изменять нежелательно!\nВы настаиваете на изменении?'
                        elif payStatusVisit or payStatusAction:
                            message = u'%s из закрытого события были выставлены в счет\nи его данные изменять нежелательно!\nВы настаиваете на изменении?'%(u'Визит и Действие' if (payStatusVisit and payStatusAction) else (u'Визиты' if payStatusVisit else u'Действия'))
                        if not QtGui.QMessageBox.critical(QtGui.qApp.mainWindow, u'Внимание!', message, QtGui.QMessageBox.Yes|QtGui.QMessageBox.No, QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
                            if isRegTabReadEvent:
                                self.setReadOnly(isRegTabReadEvent)
                                if hasattr(self, 'btnPlanning'):
                                    self.btnPlanning.setEnabled(False)
                                self.btnRelatedEvent.setEnabled(False)
                            else:
                                return False
                    else:
                        self.buttonBox.button(QtGui.QDialogButtonBox.Cancel).setText(u"Закрыть")
                        message = u''
                        if payStatus:
                            message = u'Данное событие выставлено в счёт, редактирование запрещено!'
                        elif payStatusVisit or payStatusAction:
                            message = u'%s из закрытого события были выставлены в счет, редактирование запрещено!'%(u'Визит и Действие' if (payStatusVisit and payStatusAction) else (u'Визиты' if payStatusVisit else u'Действия'))
                        QtGui.QMessageBox.critical(QtGui.qApp.mainWindow, u'Внимание!', message)
                        if isRegTabReadEvent:
                            self.setReadOnly(isRegTabReadEvent)
                            if hasattr(self, 'btnPlanning'):
                                self.btnPlanning.setEnabled(False)
                            self.btnRelatedEvent.setEnabled(False)
                            if hasattr(self, 'btnRefresh'):
                                self.btnRefresh.setEnabled(False)
                        else:
                            return False
            if isClosed:
                if not QtGui.qApp.userHasRight(urEditClosedEvent) and not QtGui.qApp.userHasRight(urAdmin):
                    self.buttonBox.button(QtGui.QDialogButtonBox.Cancel).setText(u"Закрыть")
                    if not QtGui.qApp.userHasRight(urEditClosedEventCash):
                        if isRegTabReadEvent:
                            self.setReadOnly(isRegTabReadEvent)
                            if hasattr(self, 'btnPlanning'):
                                self.btnPlanning.setEnabled(False)
                            self.btnRelatedEvent.setEnabled(False)
                        else:
                            QtGui.QMessageBox.critical(QtGui.qApp.mainWindow, u'Внимание!', u'Событие закрыто!\nНет права на изменение закрытых событий!')
                            return False
                    else:
                        self.restrictToPayment() 
        else:
            return False
        return True


    @pyqtSignature('')
    def on_actShowContingentsClient_triggered(self):
        try:
            if self.clientId:
                dialog = CShowContingentsClientDialog(self, self.clientId)
                try:
                    if dialog.exec_():
                        pass
                finally:
                    dialog.deleteLater()
        except:
            pass


    def exec_(self):
        updateEventId = False
        if not QtGui.qApp.counterController():
            QtGui.qApp.setCounterController(CCounterController(self))
        QtGui.qApp.setJTR(self)
        result = None
        if QtGui.qApp.getEventTimeout() != 0 and bool(self.itemId()):
            self._timeoutLogout.setup(QtGui.qApp.getEventTimeout() * 60000, u'обращение')
        try:
            result = CItemEditorBaseDialog.exec_(self)
        finally:
            if result:
                self.__jobTicketRecordsMap2PostUpdate()
                QtGui.qApp.delAllCounterValueIdReservation()
                updateEventId = self.checkCompletedEventsOMS()
            else:
                QtGui.qApp.resetAllCounterValueIdReservation()
                self._checkNotCreatedActions()
            QtGui.qApp.unsetJTR(self)
        if self.itemId() and self.mruDescr:
            QtGui.qApp.addMruEvent(self.itemId(), self.mruDescr)
        if result == self.saveAndCreateAccount:
            counterController = QtGui.qApp.counterController()
            counterController.setIgnoreSequence(True)
            try:
                from Accounting.InstantAccountDialog import createInstantAccount
                createInstantAccount(self.itemId())
            except:
                QtGui.qApp.logCurrentException()
            counterController.setIgnoreSequence(False)
        QtGui.qApp.setCounterController(None)
        QtGui.qApp.disconnectClipboard()
        if updateEventId:
            from Events.CreateEvent import editEvent
            editEvent(self, updateEventId)
        return result

    def _checkNotCreatedActions(self):
        for record, action in self.getActionsModelsItemsList():
            if forceRef(record.value('id')):
                continue

            if not action or action.nomenclatureClientReservation is None:
                continue

            action.nomenclatureClientReservation.cancel()


    def save(self):
        if self.edtEndDate.date().isValid():
            self.checkNomenclatureReservationComplete()
            self.removeClientObservationStatuses()
        eventProfileId = getEventProfileId(self.eventTypeId)
        checkDiag = True
        eventProfileRegionalCode = forceString(
            QtGui.qApp.db.translate('rbEventProfile', 'id', eventProfileId, 'regionalCode'))
        if eventProfileRegionalCode == u'8023' and self.edtEndDate.date().isValid():
            checkDiag = self.checkDiagnosticsFor8023Profile()
        result = CItemEditorBaseDialog.save(self) if checkDiag else None
        if self.clientIntoleranceMedicamentRecords:
            CNomenclatureExpenseDialog.saveClientIntoleranceMedicamentRecords(self.clientIntoleranceMedicamentRecords, self.clientId)
        return result


    def done(self, result):
        if self.isReadOnly():
            scd = self.cdDiscard
        elif result < 0: # закрытие из closeEvent или Esc
            scd = self.askSaveDiscardContinueEdit()
        elif result == 0:   # закрытие кнопкой отмены
            scd = self.cdDiscard
        else:               # закрытие кнопкой "ok"
            scd = self.cdSave
            if self.getEventId() and hasattr(self, 'tabNotes') and self.tabNotes.isEventClosed():
                scd = self.askSaveDiscardContinueEdit()

        if scd == self.cdDiscard:
            self.discardData()

        if scd == self.cdDiscard or (scd == self.cdSave and self.saveData()):
            self.saveDialogPreferences()
            if result < 0:
                result = 1 if scd == self.cdSave else 0
            # При закрытии редактора события проверяем необходимость планирования явки по ДН
            if (result
                    and forceBool(QtGui.qApp.preferences.appPrefs.get('isPrefSurveillancePlanningDialog', False))
                    and self.itemId()
                    and self.eventContext and self.eventContext[:4] in (u'f131', u'f025', u'f030')):
                self.checkSurveillancePlanning()
            QtGui.QDialog.done(self, result)


    def askSaveContinueEdit(self):
        if self.isDirty():
            msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning,
                                       u'Внимание!',
                                       u'Данные были изменены.\nСохранить данные?',
                                       QtGui.QMessageBox.Save | QtGui.QMessageBox.Cancel,
                                       self)
            msgBox.setWindowFlags(msgBox.windowFlags() | Qt.WindowStaysOnTopHint)
            msgBox.setDefaultButton(QtGui.QMessageBox.Save)
            res = msgBox.exec_()
            return {QtGui.QMessageBox.Save: self.cdSave}.get(res, self.cdContinueEdit)
        else:
            msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning,
                                       u'Внимание!',
                                       u'Нет данных для сохранения',
                                       QtGui.QMessageBox.Ok,
                                       self)
            msgBox.setWindowFlags(msgBox.windowFlags() | Qt.WindowStaysOnTopHint)
            msgBox.setDefaultButton(QtGui.QMessageBox.Ok)
            msgBox.exec_()
        return self.cdContinueEdit


    def saveData(self):
        if self.isSaveActionsForNomenclatureExpense:
            return self.checkActionsForNomenclatureExpense() and self.save()
        else:
            return self.checkUnfinishedActions() and self.checkDataEntered() and self.save()


    def setIsSaveActionsForNomenclatureExpense(self, value):
        self.isSaveActionsForNomenclatureExpense = value


    def checkActionsForNomenclatureExpense(self):
        result = True
        showTime = getEventShowTime(self.eventTypeId)
        if showTime:
            begDate = QDateTime(self.edtBegDate.date(), self.edtBegTime.time())
            endDate = QDateTime(self.edtEndDate.date(), self.edtEndTime.time())
        else:
            begDate = self.edtBegDate.date()
            endDate = self.edtEndDate.date()
        tabs = self.getActionsTabsList()
        for tab in tabs:
            groups = tab.modelAPActions._items._groups
            for group in groups:
                mapItem2Row = group._mapItem2Row
                for action, row in mapItem2Row.items():
                    if action:
                        if action.action and action.action.getType().isNomenclatureExpense:
                            result = result and tab.checkAPDataEntered()
                            result = result and self.checkActionsNEDataEnteredEx(begDate, endDate, action.action, row, tab)
        return result


    def checkSurveillancePlanning(self):
        if hasattr(self, 'modelPreliminaryDiagnostics') and hasattr(self, 'modelFinalDiagnostics'):
            modelDiagnostics = [self.modelPreliminaryDiagnostics, self.modelFinalDiagnostics]
        elif hasattr(self, 'modelDiagnostics'):
            modelDiagnostics = [self.modelDiagnostics]
        else:
            modelDiagnostics = []
        if modelDiagnostics:
            dispanserItems = self.getSurveillanceItems(modelDiagnostics)
            if dispanserItems:
                observed = False
                for record in dispanserItems:
                    dispanserId = forceRef(record.value('dispanser_id'))
                    if dispanserId and forceInt(QtGui.qApp.db.translate('rbDispanser', 'id', dispanserId, 'observed')) == 1:
                        observed = True
                        break
                planMessage = u'Запланировать явку по диспансерному наблюдению?' if observed else u'Открыть Контрольную карту диспансерного наблюдения?'
                messagesaveSurveillancePlanning = QtGui.QMessageBox(QtGui.QMessageBox.Warning, u'Внимание!',
                                                                    planMessage,
                                                                    QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel,
                                                                    self)
                messagesaveSurveillancePlanning.setDefaultButton(QtGui.QMessageBox.Ok)
                res = messagesaveSurveillancePlanning.exec_()
                if res == QtGui.QMessageBox.Ok:
                    for record in dispanserItems:
                        record.append(QSqlField('diagnosisDispanser_id', QVariant.Int))
                        record.setValue('diagnosisDispanser_id', QtGui.qApp.db.translate('Diagnosis', 'id', forceRef(record.value('diagnosis_id')), 'dispanser_id'))
                    self.saveSurveillancePlanning(dispanserItems, self.itemId())


    def checkActionsNEDataEnteredEx(self, eventDirectionDate, eventEndDate, action, row, actionTab):
        self.actionTypeDepositIdList = []
        record = action.getRecord()
        if action and action._actionType.id:
            if action._actionType.id not in self.actionTypeDepositIdList:
                self.actionTypeDepositIdList.append(action._actionType.id)
            if not self.checkSetPerson(row, record, action, actionTab.tblAPActions, actionTab.cmbAPSetPerson):
                return False
            if not self.checkExecPerson(row, record, action,
                                        actionTab.tblAPActions, actionTab.cmbAPPerson):
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
        return True


    def checkActionsNEDateEnteredActuality(self, begDate, endDate, action, row, actionTab):
        result = True
        db = QtGui.qApp.db
        table = db.table('EventType_Action')
        tableActionType = db.table('ActionType')
        cols = [table['actuality']]
        record = action.getRecord()
        if action and action._actionType.id:
            showTime = action._actionType.showTime and getEventShowTime(self.eventTypeId)
            forceDateOrDateTime = forceDateTime if showTime else forceDate
            rowEndDate = forceDateOrDateTime(record.value('endDate'))
            rowEndDateToCompare = self._date2StringToCompare(rowEndDate)
            if rowEndDate:
                actuality = None
                expirationDate = 0
                actionTypeId = action._actionType.id
                if self.eventTypeId and actionTypeId:
                    cond = [table['eventType_id'].eq(self.eventTypeId),
                            table['actionType_id'].eq(actionTypeId)
                            ]
                    recordActuality = db.getRecordEx(table, cols, cond, 'EventType_Action.eventType_id')
                    if recordActuality:
                        actuality = forceInt(recordActuality.value(0))
                if not actuality and actionTypeId:
                    recordExpirationDate = db.getRecordEx(tableActionType, [tableActionType['expirationDate']],
                                                          [tableActionType['id'].eq(actionTypeId),
                                                           tableActionType['deleted'].eq(0)])
                    if recordExpirationDate:
                        expirationDate = forceInt(recordExpirationDate.value(0))
                        if expirationDate and not actuality:
                            actuality = expirationDate
                if actuality:
                    if endDate:
                        nextDate = endDate.addMonths(+actuality)
                        endDateToCompare = self._date2StringToCompare(
                            nextDate.date() if isinstance(nextDate, QDateTime) and not showTime else nextDate)
                        if rowEndDateToCompare > endDateToCompare:
                            result = result and self.checkValueMessage(
                                u'Дата выполнения должна быть не позже %s ( с учетом срока "годности" данных)' % forceString(
                                    endDate), True, actionTab.tblAPActions, row, 0, actionTab.edtAPEndDate)
                    if begDate:
                        lowDate = begDate.addMonths(-actuality)
                        lowDateToCompare = self._date2StringToCompare(
                            lowDate.date() if isinstance(lowDate, QDateTime) and not showTime else lowDate)
                        if rowEndDateToCompare < lowDateToCompare:
                            result = result and self.checkValueMessage(
                                u'Дата выполнения должна быть не раньше %s( с учетом срока "годности" данных)' % forceString(
                                    lowDate), False, actionTab.tblAPActions, row, 0, actionTab.edtAPEndDate)
        return result


    def checkUnfinishedActions(self):
        enableUnfinishedActions = getEventEnableUnfinishedActions(self.eventTypeId)
        if bool(enableUnfinishedActions):
            return self.checkOpenActions(enableUnfinishedActions) if self.primaryEntranceCheck else self.checkActionsEndDate(enableUnfinishedActions)
        return True


    def restrictToPayment(self):
        if hasattr(self, 'tabCash'):
            tabCashIndex = self.tabWidget.indexOf(self.tabCash)
            tabNotesIndex = self.tabWidget.indexOf(self.tabNotes) if hasattr(self, 'tabNotes') else -1
            for i in xrange(self.tabWidget.count()):
                if i != tabCashIndex and i != tabNotesIndex:
                    self.tabWidget.setTabEnabled(i, False)
            self.tabWidget.setCurrentIndex(tabCashIndex)
            self.tabCash.tabCach.setCurrentIndex(1)
            return True
        else:
            return False


    def onActionsSummaryCurrentRowMovedTo(self, row):
        self.setFocusToWidget(self.tblActions, row, 0)
#        self.tblActions.setCurrentIndex(self.modelActionsSummary.index(row, 0))


    def _updateNoteByPrevEventId(self):
        if hasattr(self, 'tabNotes') and self.prevEventId:
            self.lblProlongateEvent.setText(u'п')
            db = QtGui.qApp.db
            tableEvent = db.table('Event')
            tableEventType = db.table('EventType')
            prevEventRecord = db.getRecordEx(tableEvent.innerJoin(tableEventType, tableEvent['eventType_id'].eq((tableEventType['id']))), [tableEventType['name'], tableEvent['setDate']], [tableEvent['deleted'].eq(0), tableEvent['id'].eq(self.prevEventId)])
            if prevEventRecord:
                self.tabNotes.edtPrevEventInfo.setText(u'Продолжение обращения: %s от %s.'%(forceString(prevEventRecord.value('name')), forceDate(prevEventRecord.value('setDate')).toString('dd.MM.yyyy')))


    def initPrevEventTypeId(self, eventTypeId, clientId):
        prevEventTypeId = getEventPrevEventTypeId(eventTypeId)
        if prevEventTypeId and not self.prevEventId:
            self.prevEventId = getPrevEventIdByEventTypeId(prevEventTypeId, clientId)
            if not self.prevEventId:
                currEventType = u' | '.join([getEventCode(eventTypeId), getEventName(eventTypeId)])
                prevEventType = u' | '.join([getEventCode(prevEventTypeId),  getEventName(prevEventTypeId)])
                if QtGui.QMessageBox.question(self,
                                        u'Внимание!',
                                        u'Событие типа \'%s\' должно являться продолжением \'%s\',\nно подобрать предшествующее событие не удается.\nПродолжить создание события?' % (currEventType, prevEventType),
                                        QtGui.QMessageBox.No|QtGui.QMessageBox.Yes,
                                        QtGui.QMessageBox.No) != QtGui.QMessageBox.Yes:
                                            return False
        if self.prevEventId:
            self._updateNoteByPrevEventId()
        return True


    def initPrevEventId(self, prevEventId):
        self.prevEventId = prevEventId


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        orgId = forceRef(record.value('org_id'))
        self.setOrgId(orgId if orgId else QtGui.qApp.currentOrgId())
        self.setEventTypeId(forceRef(record.value('eventType_id')))
        self.eventSetDateTime = forceDateTime(record.value('setDate'))
        self.eventDate = forceDate(record.value('execDate'))
        self.setContractId(forceRef(record.value('contract_id')))
        self.setClientId(forceRef(record.value('client_id')))
        self.prevEventId = forceRef(record.value('prevEvent_id'))
        if hasattr(self, 'edtPregnancyWeek'):
            self.edtPregnancyWeek.setValue(forceInt(record.value('pregnancyWeek')))


    def checkEventCreationRestriction(self):
        if QtGui.qApp.isRestrictedEventCreationByContractPresence() and self.cmbContract.value() is None:
            QtGui.QMessageBox().critical(self,
                                         u'Внимание!',
                                         u'Обслуживание пациента запрещено, так как нельзя подобрать договор',
                                         QtGui.QMessageBox.Close)
            return False
        return True


    def getRecord(self):
        if not self.record():
            record = CItemEditorBaseDialog.getRecord(self)
            record.setValue('eventType_id', toVariant(self.eventTypeId))
            record.setValue('org_id',       toVariant(self.orgId))
            record.setValue('client_id',    toVariant(self.clientId))
            record.setValue('isPrimary',    QVariant(1))
            record.setValue('order',  QVariant(getEventOrder(self.eventTypeId)+1))
        else:
            record = self.record()
        record.setValue('prevEvent_id', toVariant(self.prevEventId))
        if hasattr(self, 'edtPregnancyWeek'):
            record.setValue('pregnancyWeek',    QVariant(self.edtPregnancyWeek.value()))

        self.setCheckedChkCloseEvent()

        # Это хак: удаляем payStatus из записи
        result = type(record)(record) # copy record
        result.remove(result.indexOf('payStatus'))
        result._dirty = True # при сохранении эвента всегда пытаемся сохранить запись, чтоб modifyDatetime обновлялась
        return result


    def afterSave(self):
        CItemEditorBaseDialog.afterSave(self)
        self.checkTissueJournalStatusByActions()
        # обработка направлений на исследования Альфа-Лаб
        if hasattr(self, 'hasReferralLisLab'):
            checkReferralLisLab(self, self.getEventId())
        if hasattr(self, 'planningActionId'):
            self.updatePlanningAction()
        self.modifiableDiagnosisesMap = {}


    def checkTissueJournalStatusByActions(self):
        actionsModelsItemsList = self.getActionsModelsItemsList()
        checkTissueJournalStatusByActions(actionsModelsItemsList)


    def updatePlanningAction(self):
        db = QtGui.qApp.db
        tableAction = db.table('Action')
        recordAction = db.getRecord(tableAction, '*', self.planningActionId)
        setDate = forceDateTime(self.getSetDateTime())
        if not forceDate(recordAction.value('endDate')):
            recordAction.setValue('endDate', toVariant(setDate))
            recordAction.setValue('status', toVariant(2))
            if not forceDate(recordAction.value('begDate')):
                recordAction.setValue('begDate', toVariant(setDate))
            db.updateRecord(tableAction, recordAction)


    def checkNomenclatureReservationComplete(self):
        actionsModelsItemsList = self.getActionsModelsItemsList()
        for record, action in actionsModelsItemsList:
            actionTypeId = forceRef(record.value('actionType_id'))
            if actionTypeId:
                actionType = CActionTypeCache.getById(actionTypeId)
                status = forceInt(record.value('status'))
                if actionType.isNomenclatureExpense and status in (CActionStatus.started, CActionStatus.appointed):
                    record.setValue('status', toVariant(CActionStatus.canceled))
                    action.cancel()


    def checkDiagnosticsFor8023Profile(self):
        diagOK = True
        modelDiagnostics = None
        if hasattr(self, 'modelFinalDiagnostics'):
            modelDiagnostics = self.modelFinalDiagnostics
        elif hasattr(self, 'modelDiagnostics'):
            modelDiagnostics = self.modelDiagnostics
        # if hasattr(self, 'tblFinalDiagnostics'):
        #     tblDiagnostics = self.tblFinalDiagnostics
        # elif hasattr(self, 'tblInspections'):
        #     tblDiagnostics = self.tblInspections
        if modelDiagnostics:
            listDiagnostics = []
            for item in modelDiagnostics.items():
                mkb = forceString(item.value('MKB'))
                characterId = forceString(item.value('character_id'))
                if not mkb.startswith(u'Z'):
                    diagType = forceString(QtGui.qApp.db.translate('rbDiagnosisType', 'id', forceRef(item.value('diagnosisType_id')), 'code'))
                    if diagType in [u'9', u'1']:
                        listDiagnostics.append(mkb)

            actionsModelsItemsList = self.getActionsModelsItemsList()
            actionsMKBList = []
            for record, action in actionsModelsItemsList:
                actionMKB = forceString(record.value('MKB'))
                if actionMKB:
                    actionsMKBList.append(actionMKB)
            for mkb in actionsMKBList:
                if not mkb.startswith(u'Z') and not mkb in listDiagnostics:
                    # вот тут вывести ошибочку
                    message = u'Диагноз ' + mkb + u' должен быть занесён как сопутствующий на вкладке Стат. учёт!'
                    QtGui.QMessageBox.critical(self, u'Внимание!', message, QtGui.QMessageBox.Close)
                    diagOK = False
        return diagOK


    def removeClientObservationStatuses(self):
        description = CEventTypeDescription.get(self.eventTypeId)
        if not (description.isStationary or description.isDayStationary or description.isHealthResort):
            return
        db = QtGui.qApp.db
        tableStatusObservation = db.table('Client_StatusObservation')
        cond = [
            tableStatusObservation['deleted'].eq(0),
            tableStatusObservation['master_id'].eq(self.clientId),
            'statusObservationType_id IN (SELECT id FROM rbStatusObservationClientType WHERE removeStatus = 1)',
        ]
        db.deleteRecord(tableStatusObservation, cond)


    def getActionsTabsList(self):
        result = []
        if hasattr(self, 'tabActions'):
            result.append(self.tabActions)
        else:
            if hasattr(self, 'tabStatus'):
                result.append(self.tabStatus)
            if hasattr(self, 'tabDiagnostic'):
                result.append(self.tabDiagnostic)
            if hasattr(self, 'tabCure'):
                result.append(self.tabCure)
            if hasattr(self, 'tabMisc'):
                result.append(self.tabMisc)
        return result


    def getActionsModelsItemsList(self, filter=None):
        actionsModelsItemsList = []
        for actionsTab in self.getActionsTabsList():
            items = filter(actionsTab.modelAPActions.items()) if filter else actionsTab.modelAPActions.items()
            actionsModelsItemsList.extend(items)
        return actionsModelsItemsList


    def getActionsItemsJobTicketsList(self, filter):
        actionsModelsItemsList = []
        actionsJobTicketIdList = []
        for actionsTab in self.getActionsTabsList():
            items, jobTicketIdList = filter(actionsTab.modelAPActions.items())
            actionsModelsItemsList.extend(items)
            actionsJobTicketIdList.extend(jobTicketIdList)
        return actionsModelsItemsList, actionsJobTicketIdList


    def getJobTicketsList(self, filter):
        actionsModelsItemsList, actionsJobTicketIdList = self.getActionsItemsJobTicketsList(filter)
        if not actionsJobTicketIdList:
            return actionsModelsItemsList
        db = QtGui.qApp.db
        tableEvent                   = db.table('Event')
        tableAction                  = db.table('Action')
        tableActionType              = db.table('ActionType')
        tableActionPropertyType      = db.table('ActionPropertyType')
        tableActionProperty          = db.table('ActionProperty')
        tableActionPropertyJobTicket = db.table('ActionProperty_Job_Ticket')
        tableJobTicket               = db.table('Job_Ticket')
        tableJob                     = db.table('Job')
        queryTable = tableEvent.innerJoin(tableAction,
                                          tableAction['event_id'].eq(tableEvent['id']))
        queryTable = queryTable.innerJoin(tableActionType,
                                          tableActionType['id'].eq(tableAction['actionType_id']))
        queryTable = queryTable.innerJoin(tableActionProperty,
                                          tableActionProperty['action_id'].eq(tableAction['id']))
        queryTable = queryTable.innerJoin(tableActionPropertyType,
                                          tableActionPropertyType['id'].eq(tableActionProperty['type_id']))
        queryTable = queryTable.innerJoin(tableActionPropertyJobTicket,
                                          tableActionPropertyJobTicket['id'].eq(tableActionProperty['id']))
        queryTable = queryTable.innerJoin(tableJobTicket,
                                          tableJobTicket['id'].eq(tableActionPropertyJobTicket['value']))
        queryTable = queryTable.innerJoin(tableJob,
                                          tableJob['id'].eq(tableJobTicket['master_id']))
        cond = [tableEvent['deleted'].eq(0),
                tableAction['deleted'].eq(0),
                tableAction['status'].notInlist([2, 3]),
                tableActionType['deleted'].eq(0),
                tableActionPropertyType['deleted'].eq(0),
                tableActionProperty['deleted'].eq(0),
                tableJob['deleted'].eq(0),
                tableActionType['id'].eq(tableActionPropertyType['actionType_id']),
                tableJobTicket['id'].inlist(actionsJobTicketIdList),
                tableEvent['id'].ne(self.itemId()),
                tableEvent['client_id'].eq(self.clientId)
                ]
        itemsRec = []
        records = db.getRecordList(queryTable, 'Action.*', cond, db.joinAnd([tableJobTicket['datetime'].name(), tableJobTicket['id'].name()]))
        for record in records:
            action = CAction(record=record)
            itemsRec.append((record, action))
        if filter:
           items = filter(itemsRec)[0]
        else:
            items = itemsRec
        actionsModelsItemsList.extend(items)
        return actionsModelsItemsList


    def checkNeedLaboratoryCalculator(self, propertyTypeList, clipboardSlot):
        actualPropertyTypeList = [propType for propType in propertyTypeList if validCalculatorSettings(propType.laboratoryCalculator)]
        if actualPropertyTypeList:
            QtGui.qApp.connectClipboard(clipboardSlot)
        else:
            QtGui.qApp.disconnectClipboard()
        return actualPropertyTypeList


    def setEventTypeId(self, eventTypeId, title='', titleF003 = ''):
        self.eventTypeId = eventTypeId
        self.eventTypeName  = getEventName(eventTypeId)
        self.eventPurposeId = getEventPurposeId(eventTypeId)
        self.eventServiceId = getEventServiceId(eventTypeId)
        self.eventPeriod    = getEventPeriodEx(eventTypeId)
        self.eventContext   = getEventContext(eventTypeId)
        self.mesRequired    = getEventMesRequired(eventTypeId)
        self.mesRequiredParams = getEventMesRequiredParams(eventTypeId)
        self.csgRequired    = getEventCSGRequired(eventTypeId)
        self.eventMedicalAidKindId = getEventMedicalAidKindId(eventTypeId)

        orgName = getOrganisationShortName(self.orgId)
        eventPurposeName = forceString(QtGui.qApp.db.translate('rbEventTypePurpose', 'id', self.eventPurposeId, 'name'))
        self.setWindowTitle(u'%s %s %s - %s: %s' % (title, orgName, titleF003, eventPurposeName, self.eventTypeName))
        if hasattr(self, 'tabMes'):
            if self.mesRequired or self.csgRequired:
                self.tabMes.setEventTypeId(eventTypeId)
            else:
                self.tabWidget.setTabEnabled(self.tabWidget.indexOf(self.tabMes), False)
        if hasattr(self, 'tabNotes'):
            self.tabNotes.enableEditors(self.eventTypeId)
        if hasattr(self, 'tabVoucher'):
            self.tabVoucher.edtVoucherNumberEnabled(self.eventTypeId)
        if hasattr(self, 'btnAPActionsAdd'):
            self.btnAPActionsAdd.setVisible(False)
        if hasattr(self, 'tblActions'):
            if title != u'Ф.001':
                if hasattr(self, 'btnAPActionsAdd'):
                    self.btnAPActionsAdd.setVisible(True)
                self.addObject('actAPActionsAdd', QtGui.QAction(u'Добавить ...', self))
                self.actAPActionsAdd.setShortcut(Qt.Key_F9)
                self.mnuAction.addAction(self.actAPActionsAdd)
                self.connect(self.actAPActionsAdd, SIGNAL('triggered()'), self.on_btnAPActionsAdd_triggered)
        if hasattr(self, 'tabMedicalDiagnosis'):
            self.tabWidget.setTabEnabled(self.tabWidget.indexOf(self.tabMedicalDiagnosis), QtGui.qApp.userHasRight(urReadMedicalDiagnosis))
        if hasattr(self, 'tabAmbCard'):
            if not QtGui.qApp.userHasRight(urReadEventMedKart):
                self.tabWidget.removeTab(self.tabWidget.indexOf(self.tabAmbCard))
        self.widgetsVisible()


    def setVisitAssistantVisible(self, table, visible):
        model = table.model()
        model.hasAssistant = visible
        table.setColumnHidden(model.getColIndex('assistant_id'), not visible)


    def keyPressEvent(self, event):
        key = event.key()
        if hasattr(self, 'tabWidget'):
            widget = self.tabWidget.currentWidget()
            cond = []
            if hasattr(self, 'tabToken'):
                cond.append(self.tabToken)
            if hasattr(self, 'tabStatus'):
                cond.append(self.tabStatus)
            if hasattr(self, 'tabDiagnostic'):
                cond.append(self.tabDiagnostic)
            if hasattr(self, 'tabCure'):
                cond.append(self.tabCure)
            if hasattr(self, 'tabMisc'):
                cond.append(self.tabMisc)
            if hasattr(self, 'tabMes'):
                cond.append(self.tabMes)
            if hasattr(self, 'tabTempInvalidEtc'):
                cond.append(self.tabTempInvalidEtc)
            if hasattr(self, 'tabMedicalDiagnosis'):
                cond.append(self.tabMedicalDiagnosis)
            if widget in cond:
                if event.type() == QEvent.KeyPress:
                    if key == Qt.Key_F9:
                        self.on_btnAPActionsAdd_triggered()
            if key == Qt.Key_F3:
                if QtGui.qApp.userHasRight(urReadCheckPeriodActions) or QtGui.qApp.userHasRight(urEditCheckPeriodActions):
                    self.checkPeriodActionsDialog(self.getActionsTabsList())
        if key in (Qt.Key_Enter, Qt.Key_Return):
            self.accept()
        CItemEditorBaseDialog.keyPressEvent(self, event)


    def getEventId(self):
        return self.itemId()


    def getEventTypeId(self):
        return self.eventTypeId


    def getExternalId(self):
        if getEventTypeForm(self.eventTypeId) == u'072':
            obj = self
        elif hasattr(self, 'tabNotes'):
            obj = self.tabNotes
        else:
            obj = None
        if obj:
            return forceString(obj.edtEventExternalIdValue.text())
        if self.record():
            return forceString(self.record().value('externalId'))
        return ''


    def getDateForContract(self):
        if self.eventDate:
            return self.eventDate
        elif self.eventSetDateTime:
            return self.eventSetDateTime.date()
        return QDate.currentDate()


    def getCuratorId(self):
        if hasattr(self, 'tabNotes'):
            return self.tabNotes.cmbEventCurator.value()
        if self.record():
            return forceRef(self.record().value('curator_id'))
        return None


    def getAssistantId(self):
        if hasattr(self, 'tabNotes'):
            return self.tabNotes.cmbEventAssistant.value()
        if self.record():
            return forceRef(self.record().value('assistant_id'))
        return None


    def getPatientModelId(self):
        if hasattr(self, 'tabNotes'):
            return self.tabNotes.cmbPatientModel.value()
        if self.record():
            return forceRef(self.record().value('patientModel_id'))
        return None


    def getCureTypeId(self):
        if hasattr(self, 'tabNotes'):
            return self.tabNotes.cmbCureType.value()
        if self.record():
            return forceRef(self.record().value('cureType_id'))
        return None


    def getCureMethodId(self):
        if hasattr(self, 'tabNotes'):
            return self.tabNotes.cmbCureMethod.value()
        if self.record():
            return forceRef(self.record().value('cureMethod_id'))
        return None


    def getNote(self):
        if hasattr(self, 'tabNotes'):
            return self.tabNotes.edtEventNote.toPlainText()
        if self.record():
            return forceString(self.record().value('note'))
        return ''


    def getSrcDate(self):
        if getEventTypeForm(self.eventTypeId) == u'072':
            return self.tabVoucher.edtDirectionDate.date()
        elif hasattr(self, 'tabNotes'):
            return self.tabNotes.edtEventSrcDate.date()
        if self.record():
            return forceDate(self.record().value('srcDate'))
        return QDate()


    def getVouchers(self, context):
        items = {}
        items['finance'] = context.getInstance(CFinanceInfo, self.tabVoucher.cmbVoucherFinance.value())
        items['org'] = context.getInstance(COrgInfo, self.tabVoucher.cmbVoucherOrgs.value())
        items['begDate'] = CDateInfo(self.tabVoucher.edtVoucherBegDate.date())
        items['endDate'] = CDateInfo(self.tabVoucher.edtVoucherEndDate.date())
        items['serial'] = forceString(self.tabVoucher.edtVoucherSerial.text())
        items['number'] = forceString(self.tabVoucher.edtVoucherNumber.text())

        return items


    def getSrcNumber(self):
        if getEventTypeForm(self.eventTypeId) == u'072':
            return unicode(self.tabVoucher.edtDirectionNumber.text())
        elif hasattr(self, 'tabNotes'):
            return unicode(self.tabNotes.edtEventSrcNumber.text())
        if self.record():
            return forceString(self.record().value('srcNumber'))
        return ''


    def getRelegateOrgId(self):
        if getEventTypeForm(self.eventTypeId) == u'072':
            return self.tabVoucher.cmbDirectionOrgs.value()
        elif hasattr(self, 'tabNotes'):
            return self.tabNotes.cmbRelegateOrg.value()
        if self.record():
            return forceRef(self.record().value('relegateOrg_id'))
        return None


    def getRelegatePersonId(self):
        if getEventTypeForm(self.eventTypeId) == u'072':
            return self.tabVoucher.cmbDirectionPerson.value()
        elif hasattr(self, 'tabNotes'):
            return self.tabNotes.cmbRelegatePerson.value()
        if self.record():
            return forceRef(self.record().value('relegatePerson_id'))
        return None

    def getContractId(self):
#        if hasattr(self, 'cmbContract'):
#            return self.cmbContract.value()
#        else:
#            return None
        return self.contractId


    def getPrevEventDateTime(self):
        if hasattr(self, 'edtPrevDate'):
            d = self.edtPrevDate.date()
            t = self.edtPrevTime.time() if hasattr(self, 'edtPrevTime') else QTime()
            return QDateTime(d, t)
        if self.record():
            return forceDateTime(self.record().value('prevEventDate'))
        return QDateTime()


    def getSetDateTime(self):
        if hasattr(self, 'edtBegDate'):
            d = self.edtBegDate.date()
            t = self.edtBegTime.time() if hasattr(self, 'edtBegTime') else QTime()
            return QDateTime(d, t)
        return QDateTime()

    def getExecDateTime(self):
        if hasattr(self, 'edtEndDate'):
            d = self.edtEndDate.date()
            t = self.edtEndTime.time() if hasattr(self, 'edtEndTime') else QTime()
            return QDateTime(d, t)
        return QDateTime()


    def getNextEventDateTime(self):
        if hasattr(self, 'edtNextDate'):
            d = self.edtNextDate.date()
            t = self.edtNextTime.time() if hasattr(self, 'edtNextTime') else QTime()
            return QDateTime(d, t)
        if self.record():
            return forceDateTime(self.record().value('nextEventDate'))
        return QDateTime()


    @pyqtSignature('QTime')
    def on_edtEndTime_timeChanged(self, time):
        self.emitUpdateActionsAmount()

#        result._nextEventDate = CDateInfo(self.edtNextDate.date())


    def getClientMesInfo(self):
        if hasattr(self, 'tabMes'):
            return self.tabMes.cmbMes.getClientAgeSex()
        else:
            return None


    def getMesId(self):
        if hasattr(self, 'tabMes'):
            return self.tabMes.cmbMes.value()
        else:
            return None


    def getMesCode(self):
        if hasattr(self, 'tabMes'):
            return self.tabMes.cmbMes.code()
        else:
            return None


    def getMesSpecificationId(self):
        if hasattr(self, 'tabMes'):
            return self.tabMes.cmbMesSpecification.value()
        else:
            return None


    def getDefaultMKBValue(self, defaultMKB, setPersonId):
        defaultValue = '', ''
        diagnostics = None
        diagnosticsRecordList = []
        diagnosisTypeIdList = []
        if defaultMKB == 6 and hasattr(self, 'modelPreliminaryDiagnostics'):
            diagnostics = self.modelPreliminaryDiagnostics
        elif hasattr(self, 'modelFinalDiagnostics'):
            diagnostics = self.modelFinalDiagnostics
        elif hasattr(self, 'modelDiagnostics'):
            diagnostics = self.modelDiagnostics
        elif getEventTypeForm(self.eventTypeId) == u'001':
            diagnosticsRecord, diagnosisTypeId = self.getDiagnosticRecordAndTypeId()
            diagnosticsRecordList = [diagnosticsRecord]
            diagnosisTypeIdList   = [diagnosisTypeId]
        else:
            return defaultValue
        if diagnostics:
            diagnosticsRecordList = diagnostics.items()
            if defaultMKB == 6:
                diagnosisTypeIdList = diagnostics.getMainDiagnosisTypeIdList()
            else:
                diagnosisTypeIdList = diagnostics.getCloseOrMainDiagnosisTypeIdList()
        if defaultMKB in (1, 3): #  1-по заключительному, 3-синхронизация по заключительному
            return getClosingMKBValueForAction(diagnosticsRecordList, diagnosisTypeIdList)
        elif defaultMKB in (2, 4):# 2-по диагнозу назначившего действие, 4-синхронизация по диагнозу назначившего действие
            eventPersonId = self.getSuggestedPersonId()
            return getMKBValueBySetPerson(diagnosticsRecordList, setPersonId, diagnosisTypeIdList, eventPersonId)
        elif defaultMKB == 6: # 6-синхронизация по предварительному
            return getClosingMKBValueForAction(diagnosticsRecordList, diagnosisTypeIdList)
        return defaultValue


    def getMKBValueForActionDuringSaving(self, record, action):
        actionType  = action.getType()
        defaultMKB  = actionType.defaultMKB
        defaultMKBValue = ''
        defaultMorphologyMKBValue = ''
        if defaultMKB in (3, 4, 6):
            setPersonId = forceRef(record.value('setPerson_id'))
            result = self.getDefaultMKBValue(defaultMKB, setPersonId)
            defaultMKBValue, defaultMorphologyMKBValue = result
        if bool(defaultMKBValue):
            record.setValue('MKB', QVariant(defaultMKBValue))
            action._record.setValue('MKB', QVariant(defaultMKBValue))
        if bool(defaultMorphologyMKBValue):
            record.setValue('morphologyMKB', QVariant(defaultMorphologyMKBValue))
            action._record.setValue('morphologyMKB', QVariant(defaultMorphologyMKBValue))


    def setClientId(self, clientId):
        self.clientId = clientId
        if hasattr(self, 'tabMes'):
            self.tabMes.setClientId(clientId)
        self.updateClientInfo()
        if hasattr(self, 'tabAmbCard'):
            self.tabAmbCard.setClientId(clientId, self.clientSex, self.clientAge)


    def checkDeposit(self, actionSave=False):
        result = True
        result = result and self.checkDepositClient(actionSave)
        result = result and self.checkLimitContract(actionSave)
        return result


    def checkDepositClient(self, actionSave=False):
        from Events.ClientDepositDialog import CClientDepositDialog
        sumAction = 0.0
        sumItem = 0.0
        serviceBool = False
        self.btnExit = False
        if actionSave and not self.actionTypeDepositIdList:
            return True
        buttonBoxIgnore = True
        contractIdList = {}
        eventId  = self.itemId()
        if hasattr(self, 'cmbContract'):
            if hasattr(self, 'tabCash'):
                for row, record in enumerate(self.tabCash.modelAccActions._items):
                    accContractId = forceRef(record.value('contract_id'))
                    if accContractId:
                        actionTypeId = forceRef(record.value('actionType_id'))
                        if actionTypeId and actionTypeId not in self.actionTypeDepositIdList:
                            self.actionTypeDepositIdList.append(actionTypeId)
                        sum = forceDouble(self.tabCash.modelAccActions.items()[row].value('sum'))
                        contractSumList = contractIdList.get(accContractId, 0.0)
                        contractSumList += sum
                        contractIdList[accContractId] = contractSumList
            db = QtGui.qApp.db
            tableAction = db.table('Action')
            tableEvent = db.table('Event')
            tableContract = db.table('Contract')
            tableAccountItem = db.table('Account_Item')
            tableClientDeposit = db.table('ClientDeposit')

            cols = [tableClientDeposit['contract_id']]
            cols.append('SUM(ClientDeposit.contractSum) AS contractSum')
            records = db.getRecordListGroupBy(tableClientDeposit,
                                       cols,
                                       [tableClientDeposit['deleted'].eq(0), tableClientDeposit['client_id'].eq(self.clientId)],
                                       u'ClientDeposit.contract_id')
            for record in records:
                contractId = forceRef(record.value('contract_id'))
                contractSum = forceDouble(record.value('contractSum'))
                if contractId:
                    sumAction += contractIdList.get(contractId, 0.0)
                    contractRecord = db.getRecordEx(tableContract,
                                               [tableContract['limitExceeding'], tableContract['limitOfFinancing']],
                                               [tableContract['deleted'].eq(0), tableContract['id'].eq(contractId)])
                    if contractRecord:
                        limitExceeding = forceDouble(contractRecord.value('limitExceeding'))
                        limitOfFinancing = forceDouble(contractRecord.value('limitOfFinancing'))

                #  payStatus != 0
                    cond = [tableAction['deleted'].eq(0),
                            tableEvent['deleted'].eq(0),
                            tableAccountItem['deleted'].eq(0),
                            tableAction['contract_id'].eq(contractId),
                            tableAction['payStatus'].ne(0),
                            tableAccountItem['refuseType_id'].isNull()
                            ]
                    if eventId:
                        cond.append(tableEvent['id'].ne(eventId))
                    table = tableEvent.innerJoin(tableAction, tableEvent['id'].eq(tableAction['event_id']))
                    table = table.innerJoin(tableAccountItem, tableAction['id'].eq(tableAccountItem['action_id']))
                    if self.clientId:
                        cond.append(tableEvent['client_id'].eq(self.clientId))
                    records = db.getRecordListGroupBy(table, u'SUM(Account_Item.sum) AS sumAction', cond, u'Action.contract_id')
                    if records:
                        newRecord = records[0]
                        sumAction += forceDouble(newRecord.value('sumAction'))

                #  payStatus == 0
                    tableActionTypeService = db.table('ActionType_Service')
                    tableContractTariff = db.table('Contract_Tariff')
                    tableA = db.table('Action').alias('A')
                    cols = u'''SUM(IF(A.amount > Contract_Tariff.amount AND Contract_Tariff.amount != 0, Contract_Tariff.amount * Contract_Tariff.price,
                    A.amount * Contract_Tariff.price))'''
                    cond = [tableContractTariff['deleted'].eq(0),
                            tableContractTariff['master_id'].eq(contractId),
                            tableContractTariff['tariffType'].eq(CTariff.ttActionAmount)
                            ]
                    cond.append(u'A.id = Action.id')
                    if self.clientAge:
                        cond.append(db.joinOr([tableContractTariff['age'].eq(''), tableContractTariff['age'].ge(self.clientAge[3])]))
                    cond.append(u'''ActionType_Service.`service_id`=(SELECT ATS.`service_id`
                                    FROM ActionType_Service AS ATS
                                    WHERE ATS.`master_id`=ActionType_Service.`master_id`
                                    AND (ATS.`finance_id` IS NULL OR A.`finance_id`=ATS.`finance_id`)
                                    ORDER BY ATS.`finance_id` DESC
                                    LIMIT 1)''')
                    cond.append(db.joinOr([tableContractTariff['sex'].eq(0), tableContractTariff['sex'].eq(self.clientSex)]))
                    table = tableA.innerJoin(tableActionTypeService, tableA['actionType_id'].eq(tableActionTypeService['master_id']))
                    table = table.innerJoin(tableContractTariff, tableActionTypeService['service_id'].eq(tableContractTariff['service_id']))
                    stmt = db.selectStmtGroupBy(table, cols, cond, u'A.contract_id')

                    condQuery = [tableAction['deleted'].eq(0),
                                tableEvent['deleted'].eq(0),
                                tableAction['contract_id'].eq(contractId),
                                tableAction['payStatus'].eq(0)
                                ]
                    if eventId:
                        condQuery.append(tableEvent['id'].ne(eventId))
                    condQuery.append(tableEvent['client_id'].eq(self.clientId))
                    tableQuery = tableEvent.innerJoin(tableAction, tableEvent['id'].eq(tableAction['event_id']))
                    colsQuery = [u'(%s) AS sumItem'%stmt,
                                 tableAction['contract_id']
                                 ]
                    records = db.getRecordList(tableQuery, colsQuery, condQuery)
                    for newRecord in records:
                        contractId = forceRef(newRecord.value('contract_id'))
                        sumItem += forceDouble(newRecord.value('sumItem'))
                    limitSum = contractSum
                    limitSumContract = limitOfFinancing
                    if limitExceeding >= limitOfFinancing:
                        limitSumContract = limitExceeding
                        if contractSum >= limitExceeding:
                           limitSum = limitSumContract
                    else:
                        limitSumContract = limitOfFinancing
                        if contractSum >= limitOfFinancing:
                           limitSum = limitSumContract
                    sumDeposit = (sumAction + sumItem)
                    if contractSum > 0:
                        serviceBool = True
                    if sumDeposit >= limitOfFinancing and actionSave:
                        if sumDeposit > limitOfFinancing:
                            buttonBoxIgnore = False
                        else:
                            buttonBoxIgnore = True
                    if forceBool(limitExceeding) or forceBool(limitOfFinancing):
                        if ((sumAction + sumItem) > limitExceeding or limitSum < sumDeposit):
                            CClientDepositDialog(self, self.clientId, self.clientAge, self.clientSex, buttonBoxIgnore, title=u'Превышение общей стоимости услуг по договору').exec_()
                            if (sumAction + sumItem) > limitExceeding and self.btnExit:
                                if buttonBoxIgnore:
                                    return True
                                else:
                                    return False
                            else:
                                return False
                    elif (sumAction + sumItem) > contractSum:
                        CClientDepositDialog(self, self.clientId, self.clientAge, self.clientSex, buttonBoxIgnore, title=u'Превышение общей стоимости услуг по договору').exec_()
                        if (sumAction + sumItem) > limitExceeding and self.btnExit:
                            return True
                        else:
                            return False
        if serviceBool and not actionSave:
            CClientDepositDialog(self, self.clientId, self.clientAge, self.clientSex, True, title=u'У пациента есть депозит по договору').exec_()
            if self.btnExit:
                return True
            else:
                return False
        return True


    def checkRequireAction(self, eventTypeId, tabList, specialityId, diagnosisItems):
        result = True
        existingActionIds = []  # Список id actionType всех документов
        actionGroups = {}
        selectedActions = []
        diagnosisCodes = [forceString(record.value('MKB')) for record in diagnosisItems]
        for tab in tabList:
            items = tab.modelAPActions.items()
            for (record, action) in items:
                existingActionIds.append(action._actionType.id)

        db = QtGui.qApp.db
        table = db.table('EventType_RequireAction')
        records = db.getRecordList(table, [table['actionType_id'], table['selectionGroup'], table['speciality_id'], table['mkb']], table['eventType_id'].eq(eventTypeId))  # Список id actionType по eventTypeId

        group100Match = []
        group100Dop = []
        group100Priority = {
            3: [],  # Полное совпадение: и специальность и диагноз
            2: [],  # Совпадение только по диагнозу
            1: [],  # Совпадение только по специальности
            0: []  # Без фильтров (запасной вариант)
        }

        for record in records:
            actionTypeId = forceInt(record.value('actionType_id'))
            selectionGroup = forceInt(record.value('selectionGroup'))
            specialityIdsStr = forceString(record.value('speciality_id'))
            mkbFilter = forceString(record.value('mkb'))
            specialityFilter = [id_str.strip() for id_str in specialityIdsStr.split(',')] if specialityIdsStr else []
            mkbFilterList = [mkb.strip() for mkb in mkbFilter.split(',')] if mkbFilter else []
            matchesSpeciality = not specialityFilter or str(specialityId) in specialityFilter
            matchesDiagnosis = not mkbFilterList or any(diagnosis in mkbFilterList for diagnosis in diagnosisCodes)
            hasSpecialityFilter = bool(specialityFilter)
            hasDiagnosisFilter = bool(mkbFilterList)
            if selectionGroup == 100:
                if hasSpecialityFilter and hasDiagnosisFilter and matchesSpeciality and matchesDiagnosis:
                    group100Priority[3].append(actionTypeId)  # Полное совпадение
                elif hasDiagnosisFilter and matchesDiagnosis and (not hasSpecialityFilter or matchesSpeciality):
                    group100Priority[2].append(actionTypeId)  # Совпадение по диагнозу
                elif hasSpecialityFilter and matchesSpeciality and (not hasDiagnosisFilter or matchesDiagnosis):
                    group100Priority[1].append(actionTypeId)  # Совпадение по специальности
                elif not hasSpecialityFilter and not hasDiagnosisFilter:
                    group100Priority[0].append(actionTypeId)  # Без фильтров

            elif matchesSpeciality and matchesDiagnosis:
                if selectionGroup not in actionGroups:
                    actionGroups[selectionGroup] = []
                actionGroups[selectionGroup].append(actionTypeId)
        for priority in [3, 2, 1, 0]:
            if group100Priority[priority]:
                selectedActions.extend(group100Priority[priority])
                break
        for selectionGroup, actionTypeIds in sorted(actionGroups.items()):
            if actionTypeIds:
                groupSatisfied = any(action_id in existingActionIds for action_id in actionTypeIds)
                if not groupSatisfied:
                    if selectionGroup == 1:
                        selectedActions.extend(actionTypeIds)
                    if selectionGroup >= 2:
                        result = False
                        dialog = CActionTypeDialogTableModel(self, actionTypeIds, skipable=False)
                        dialog.setWindowTitle(u"Требуется выбрать одно обязательное мероприятие)")
                        if dialog.exec_():
                            selectedActions.append(dialog.currentItemId())
                    if selectionGroup == 0:
                        dialog = CActionTypeListDialog(self, filter='id in (%s)' % ','.join(
                            str(typeId) for typeId in actionTypeIds))
                        dialog.setWindowTitle(u"Можно выбрать одно или несколько мероприятий")
                        if dialog.exec_():
                            dialog.getCheckedIdList()
                            selectedActions.extend(dialog.values())

        return result, selectedActions if selectedActions else None

    def checkEventTypeNextEventDate(self, eventTypeId, execDate, clientId):
        res = True
        db = QtGui.qApp.db
        tableEventType = db.table('EventType')
        tableRBMedicalAidType = db.table('rbMedicalAidType')
        table = tableEventType.innerJoin(tableRBMedicalAidType,
                                          tableRBMedicalAidType['id'].eq(tableEventType['medicalAidType_id']))

        cond = [tableRBMedicalAidType['regionalCode'].inlist(['211', '232', '252', '262', '261']),
                tableEventType['id'].eq(eventTypeId),
                tableEventType['nextEventDateRequired'].eq(1)
                ]
        count = db.getCount(table, where=cond)
        if count:
            NextEventDate = self.getSocStatusProfBegDate(clientId, execDate)
            if not NextEventDate:
                self.enterNextEventDate(eventTypeId, execDate, clientId)
            res = self.checkNextEventDate(execDate, clientId)
        return res

    def enterNextEventDate(self, eventTypeId, execDate, clientId):
        self.checkValueMessage(u"Требуется указать дату прохождения следующего профилактического мероприятия в регистрационной карте пациента\n на вкладке Соц.статус", False, None)
        self.editClient('tabSocStatus')

    def getSocStatusProfBegDate(self, clientId, execDate):
        db = QtGui.qApp.db
        socStatusClassId = forceInt(db.translate('rbSocStatusClass', 'code', 'profilac', 'id'))

        tableClientSocStatus = db.table('ClientSocStatus')
        cond = [
            tableClientSocStatus['deleted'].eq(0),
            tableClientSocStatus['client_id'].eq(clientId),
            tableClientSocStatus['socStatusClass_id'].eq(socStatusClassId),
        ]
        # (18 -> 1 ПФ62167)
        if self.clientAge and self.clientAge[3] < 1:
            cond.append(tableClientSocStatus['begDate'].gt(execDate))
        else:
            cond.append('YEAR(begDate)>\'%d\'' % execDate.year())

        return db.getRecordEx(tableClientSocStatus, 'begDate', cond, order='%s.id DESC' % tableClientSocStatus.name())

    def checkNextEventDate(self, execDate, clientId):
        res = True
        NextEventDate = self.getSocStatusProfBegDate(clientId, execDate)
        if not NextEventDate:
            res = False
        return res

    def editClient(self, focusWidget=''):
        if QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]):
            dialog = CClientEditDialog(self)
            try:
                dialog.load(self.clientId)
                if hasattr(dialog, focusWidget):
                        QtGui.qApp.restoreOverrideCursor()
                        dialog.setFocusToWidget(getattr(dialog, focusWidget))
                if dialog.exec_():
                    self.updateClientInfo()
            finally:
                dialog.deleteLater()

    def checkLimitContract(self, actionSave=False):
        from Events.CheckLimitContractClientDialog import CCheckLimitContractClientDialog
        sumAction = 0.0
        sumItem = 0.0
        serviceBool = False
        self.btnExit = False
        if actionSave and not self.actionTypeDepositIdList:
            return True
        buttonBoxIgnore = True
        contractIdList = {}
        eventId  = self.itemId()
        if hasattr(self, 'cmbContract'):
            if hasattr(self, 'tabCash'):
                for row, record in enumerate(self.tabCash.modelAccActions._items):
                    accContractId = forceRef(record.value('contract_id'))
                    if accContractId:
                        actionTypeId = forceRef(record.value('actionType_id'))
                        if actionTypeId and actionTypeId not in self.actionTypeDepositIdList:
                            self.actionTypeDepositIdList.append(actionTypeId)
                        sum = forceDouble(self.tabCash.modelAccActions.items()[row].value('sum'))
                        contractSumList = contractIdList.get(accContractId, 0.0)
                        contractSumList += sum
                        contractIdList[accContractId] = contractSumList
            db = QtGui.qApp.db
            tableAction = db.table('Action')
            tableEvent = db.table('Event')
            tableContract = db.table('Contract')
            tableAccountItem = db.table('Account_Item')
            tableClientDeposit = db.table('ClientDeposit')
            if self.clientId:
                cols = [tableClientDeposit['contract_id']]
                depositContractIdList = db.getDistinctIdList(tableClientDeposit,
                                           cols,
                                           [tableClientDeposit['deleted'].eq(0), tableClientDeposit['client_id'].eq(self.clientId)],
                                           u'ClientDeposit.contract_id')
                for contractId in contractIdList.keys():
                    limitExceeding = 0.0
                    limitOfFinancing = 0.0
                    if contractId not in depositContractIdList:
                        sumAction += contractIdList.get(contractId, 0.0)
                        contractRecord = db.getRecordEx(tableContract,
                                                   [tableContract['limitExceeding'], tableContract['limitOfFinancing']],
                                                   [tableContract['deleted'].eq(0), tableContract['id'].eq(contractId)])
                        if contractRecord:
                            limitExceeding = forceDouble(contractRecord.value('limitExceeding'))
                            limitOfFinancing = forceDouble(contractRecord.value('limitOfFinancing'))
                    if limitExceeding or limitOfFinancing:
                        #  payStatus != 0
                            cond = [tableAction['deleted'].eq(0),
                                    tableEvent['deleted'].eq(0),
                                    tableAccountItem['deleted'].eq(0),
                                    tableAction['contract_id'].eq(contractId),
                                    tableAction['payStatus'].ne(0),
                                    tableAccountItem['refuseType_id'].isNull()
                                    ]
                            if eventId:
                                cond.append(tableEvent['id'].ne(eventId))
                            table = tableEvent.innerJoin(tableAction, tableEvent['id'].eq(tableAction['event_id']))
                            table = table.innerJoin(tableAccountItem, tableAction['id'].eq(tableAccountItem['action_id']))
                            cond.append(tableEvent['client_id'].eq(self.clientId))
                            records = db.getRecordListGroupBy(table, u'SUM(Account_Item.sum) AS sumAction', cond, u'Action.contract_id')
                            if records:
                                newRecord = records[0]
                                sumAction += forceDouble(newRecord.value('sumAction'))

                        #  payStatus == 0
                            tableActionTypeService = db.table('ActionType_Service')
                            tableContractTariff = db.table('Contract_Tariff')
                            tableA = db.table('Action').alias('A')
                            cols = u'''SUM(IF(A.amount > Contract_Tariff.amount AND Contract_Tariff.amount != 0, Contract_Tariff.amount * Contract_Tariff.price,
                            A.amount * Contract_Tariff.price))'''
                            cond = [tableContractTariff['deleted'].eq(0),
                                    tableContractTariff['master_id'].eq(contractId),
                                    tableContractTariff['tariffType'].eq(CTariff.ttActionAmount)
                                    ]
                            cond.append(u'A.id = Action.id')
                            if self.clientAge:
                                cond.append(db.joinOr([tableContractTariff['age'].eq(''), tableContractTariff['age'].ge(self.clientAge[3])]))
                            cond.append(u'''ActionType_Service.`service_id`=(SELECT ATS.`service_id`
                                            FROM ActionType_Service AS ATS
                                            WHERE ATS.`master_id`=ActionType_Service.`master_id`
                                            AND (ATS.`finance_id` IS NULL OR A.`finance_id`=ATS.`finance_id`)
                                            ORDER BY ATS.`finance_id` DESC
                                            LIMIT 1)''')
                            cond.append(db.joinOr([tableContractTariff['sex'].eq(0), tableContractTariff['sex'].eq(self.clientSex)]))
                            table = tableA.innerJoin(tableActionTypeService, tableA['actionType_id'].eq(tableActionTypeService['master_id']))
                            table = table.innerJoin(tableContractTariff, tableActionTypeService['service_id'].eq(tableContractTariff['service_id']))
                            stmt = db.selectStmtGroupBy(table, cols, cond, u'A.contract_id')

                            condQuery = [tableAction['deleted'].eq(0),
                                        tableEvent['deleted'].eq(0),
                                        tableAction['contract_id'].eq(contractId),
                                        tableAction['payStatus'].eq(0)
                                        ]
                            if eventId:
                                condQuery.append(tableEvent['id'].ne(eventId))
                            condQuery.append(tableEvent['client_id'].eq(self.clientId))
                            tableQuery = tableEvent.innerJoin(tableAction, tableEvent['id'].eq(tableAction['event_id']))
                            colsQuery = [u'(%s) AS sumItem'%stmt,
                                         tableAction['contract_id']
                                         ]
                            records = db.getRecordList(tableQuery, colsQuery, condQuery)
                            for newRecord in records:
                                sumItem += forceDouble(newRecord.value('sumItem'))

                            contractSumAllClients = self.getContractSumAllClients(contractId, contractIdList, eventId)
                            if limitOfFinancing and limitOfFinancing <= contractSumAllClients:
                                if limitOfFinancing < contractSumAllClients:
                                    bbIgnore = False
                                else:
                                    bbIgnore = True
                                CCheckLimitContractClientDialog(self, contractId, self.clientId, self.clientAge, self.clientSex, bbIgnore, title=u'Превышение лимита финансирования услуг по договору').exec_()
                                if self.btnExit:
                                    return True
                                else:
                                    return False
                            if limitExceeding and limitExceeding <= contractSumAllClients:
                                CCheckLimitContractClientDialog(self, contractId, self.clientId, self.clientAge, self.clientSex, True, title=u'Превышение предела финансирования услуг по договору').exec_()
                                if self.btnExit:
                                    return True
                                else:
                                    return False
                            contractSum = limitOfFinancing
                            limitSum = contractSum
                            limitSumContract = limitOfFinancing
                            if limitExceeding >= limitOfFinancing:
                                limitSumContract = limitExceeding
                                if contractSum >= limitExceeding:
                                   limitSum = limitSumContract
                            else:
                                limitSumContract = limitOfFinancing
                                if contractSum >= limitOfFinancing:
                                   limitSum = limitSumContract
                            sumDeposit = (sumAction + sumItem)
                            if sumDeposit > 0:
                                serviceBool = True
                            if sumDeposit > limitOfFinancing and actionSave:
                                buttonBoxIgnore = False
                            elif sumDeposit == limitOfFinancing and actionSave:
                                buttonBoxIgnore = True
                            if forceBool(limitExceeding) or forceBool(limitOfFinancing):
                                if ((sumAction + sumItem) > limitExceeding or limitSum < sumDeposit):
                                    CCheckLimitContractClientDialog(self, contractId, self.clientId, self.clientAge, self.clientSex, buttonBoxIgnore, title=u'Превышение общей стоимости услуг по договору').exec_()
                                    if (sumAction + sumItem) > limitExceeding and self.btnExit:
                                        if buttonBoxIgnore:
                                            return True
                                        else:
                                            return False
                                    else:
                                        return False
                            elif (sumAction + sumItem) > contractSum:
                                CCheckLimitContractClientDialog(self, contractId, self.clientId, self.clientAge, self.clientSex, buttonBoxIgnore, title=u'Превышение общей стоимости услуг по договору').exec_()
                                if (sumAction + sumItem) > limitExceeding and self.btnExit:
                                    return True
                                else:
                                    return False
        if serviceBool and not actionSave:
            CCheckLimitContractClientDialog(self, contractId, self.clientId, self.clientAge, self.clientSex, True, title=u'Предел стоимости услуг по договору').exec_()
            if self.btnExit:
                return True
            else:
                return False
        return True


    def getContractSumAllClients(self, contractId, contractIdList, eventId):
        contractSum = 0.0
        if contractId:
            sumAction = 0
            sumItem = 0
            db = QtGui.qApp.db
            tableAction = db.table('Action')
            tableAccountItem = db.table('Account_Item')
        #  payStatus != 0
            cond = [tableAction['deleted'].eq(0),
                    tableAccountItem['deleted'].eq(0),
                    tableAction['contract_id'].eq(contractId),
                    tableAction['payStatus'].ne(0),
                    tableAccountItem['refuseType_id'].isNull()
                    ]
            if eventId:
                cond.append(tableAction['event_id'].ne(eventId))
            table = tableAction.innerJoin(tableAccountItem, tableAction['id'].eq(tableAccountItem['action_id']))
            records = db.getRecordListGroupBy(table, u'SUM(Account_Item.sum) AS sumAction', cond, u'Action.contract_id')
            if records:
                record = records[0]
                sumAction += forceDouble(record.value('sumAction'))

        #  payStatus == 0
            tableActionTypeService = db.table('ActionType_Service')
            tableContractTariff = db.table('Contract_Tariff')
            tableEvent = db.table('Event')
            tableA = db.table('Action').alias('A')
            cols = u'''SUM(IF(A.amount > Contract_Tariff.amount AND Contract_Tariff.amount != 0, Contract_Tariff.amount * Contract_Tariff.price,
            A.amount * Contract_Tariff.price))'''
            cond = [tableContractTariff['deleted'].eq(0),
                    tableContractTariff['master_id'].eq(contractId),
                    tableContractTariff['tariffType'].eq(CTariff.ttActionAmount)
                    ]
            cond.append(u'A.id = Action.id')
            cond.append(u'''ActionType_Service.`service_id`=(SELECT ATS.`service_id`
                            FROM ActionType_Service AS ATS
                            WHERE ATS.`master_id`=ActionType_Service.`master_id`
                            AND (ATS.`finance_id` IS NULL OR A.`finance_id`=ATS.`finance_id`)
                            ORDER BY ATS.`finance_id` DESC
                            LIMIT 1)''')
            table = tableA.innerJoin(tableActionTypeService, tableA['actionType_id'].eq(tableActionTypeService['master_id']))
            table = table.innerJoin(tableContractTariff, tableActionTypeService['service_id'].eq(tableContractTariff['service_id']))
            stmt = db.selectStmtGroupBy(table, cols, cond, u'A.contract_id')
            condQuery = [tableAction['deleted'].eq(0),
                        tableEvent['deleted'].eq(0),
                        tableAction['contract_id'].eq(contractId),
                        tableAction['payStatus'].eq(0)
                        ]
            if eventId:
                condQuery.append(tableEvent['id'].ne(eventId))
            tableQuery = tableEvent.innerJoin(tableAction, tableEvent['id'].eq(tableAction['event_id']))
            colsQuery = [u'(%s) AS sumItem'%stmt,
                         tableAction['contract_id']
                         ]
            records = db.getRecordList(tableQuery, colsQuery, condQuery)
            for newRecord in records:
                sumItem += forceDouble(newRecord.value('sumItem'))

        contractSum = sumAction + sumItem + contractIdList.get(contractId, 0.0)
        return contractSum


    def updateClientInfo(self):
        date = self.eventDate
        if not date and self.eventSetDateTime:
            date = self.eventSetDateTime.date()
        if not date:
            date = QDate.currentDate()

        compulsoryPolicyRecord = None
        voluntaryPolicyRecord = None

        # возраст определяем на дату начала лечения
        dateAge = self.eventSetDateTime.date() if self.eventSetDateTime else QDate.currentDate()

        # обновление блока информации о пациенте
        self.txtClientInfoBrowser.setHtml(getClientBanner(self.clientId, date))

        # получение данных пациента
        db = QtGui.qApp.db
        record = db.getRecord('Client', ['lastName', 'firstName', 'patrName', 'birthDate', 'sex', 'deathDate'], self.clientId)
        if record:
            self.clientLastName = forceString(record.value('lastName'))
            self.clientFirstName = forceString(record.value('firstName'))
            self.clientPatrName = forceString(record.value('patrName'))
            self.clientSex = forceInt(record.value('sex'))
            self.clientBirthDate = forceDate(record.value('birthDate'))
            self.clientDeathDate = forceDate(record.value('deathDate'))
            self.clientAge = calcAgeTuple(self.clientBirthDate, dateAge)
            self.clientAgePrevYearEnd = calcAgeTuple(self.clientBirthDate, QDate(dateAge.year() - 1, 12, 31))
            self.clientAgeCurrYearEnd = calcAgeTuple(self.clientBirthDate, QDate(dateAge.year(), 12, 31))

            self.mruDescr = u'%s:\t%s, %s, %s' % (self.eventTypeName,
                                  formatNameInt(self.clientLastName,
                                                self.clientFirstName,
                                                self.clientPatrName),
                                  forceString(self.clientBirthDate),
                                  formatSex(self.clientSex),
                                  )

        self.actShowAttachedToClientFiles.setMasterId(self.clientId)
        self.resetActionTemplateCache()

        # обновляем данные в комбобоксе "Договор"
        if hasattr(self, 'cmbContract'):
            self.clientPolicyInfoList = []
            workRecord = getClientWork(self.clientId)
            self.setWorkRecord(workRecord)
            self.clientWorkOrgId = forceRef(workRecord.value('org_id')) if workRecord else None

            compulsoryPolicyRecord = getClientCompulsoryPolicy(self.clientId, date, self.itemId())
            if compulsoryPolicyRecord:
                self.clientPolicyInfoList.append([forceRef(compulsoryPolicyRecord.value('insurer_id')), forceRef(compulsoryPolicyRecord.value('policyType_id'))])

            voluntaryPolicyRecord = getClientVoluntaryPolicy(self.clientId, date)
            if voluntaryPolicyRecord:
                self.clientPolicyInfoList.append([forceRef(voluntaryPolicyRecord.value('insurer_id')), forceRef(voluntaryPolicyRecord.value('policyType_id'))])

            self.cmbContract.setClientInfo(self.clientId, self.clientSex, self.clientAge, self.clientWorkOrgId, self.clientPolicyInfoList)
            if not self.itemId() and not self.cmbContract.value():
                self.cmbContract.setCurrentIndex(0)

        # обновляем видимость недели беременности
        if hasattr(self, 'edtPregnancyWeek'):
            pregnancyVisible = bool((self.clientSex == 2) and self.clientAge and self.clientAge[3] >= 12)
            self.lblPregnancyWeek.setVisible(pregnancyVisible)
            self.edtPregnancyWeek.setVisible(pregnancyVisible)

        # обновляем данные во вкладке "Стандарт"
        if hasattr(self, 'tabMes'):
            self.tabMes.setClientInfo(date, self.clientSex, self.clientBirthDate, self.clientAge, self.clientAgePrevYearEnd, self.clientAgeCurrYearEnd)

        # Определяем тип пациента
        clientKLADRCode = ''
        self.isTerritorialBelonging = isEventTerritorialBelonging(self.eventTypeId)
        if self.isTerritorialBelonging == CEventEditDialog.ctLocAddress:
            clientKLADRCode = getClientAddressKLADRCode(self.clientId, CEventEditDialog.ctLocAddress)
        elif self.isTerritorialBelonging == CEventEditDialog.ctInsurer:
            if CFinanceType.getCode(self.eventFinanceId) == 3:
                if voluntaryPolicyRecord:
                    clientKLADRCode = forceString(voluntaryPolicyRecord.value('area'))
            else:
                if compulsoryPolicyRecord:
                    clientKLADRCode = forceString(compulsoryPolicyRecord.value('area'))
        if not clientKLADRCode:
            clientKLADRCode = getClientAddressKLADRCode(self.clientId, CEventEditDialog.ctRegAddress)

        if KLADRMatch(clientKLADRCode, QtGui.qApp.defaultKLADR()):
            self.clientType = CEventEditDialog.ctLocal
        elif KLADRMatch(clientKLADRCode, QtGui.qApp.provinceKLADR()):
            self.clientType = CEventEditDialog.ctProvince
        else:
            self.clientType = CEventEditDialog.ctOther


    def getSetPersonId(self):
        return self.personId


    def getExecPersonId(self):
        return self.personId


    def getShowButtonAccount(self):
        showButtonAccount = getEventShowButtonAccount(self.eventTypeId)
        if hasattr(self, 'btnSaveAndCreateAccount'):
            self.btnSaveAndCreateAccount.setVisible(showButtonAccount)


    def getShowButtonTemperatureList(self):
        showButtonTemperatureList = getEventShowButtonTemperatureList(self.eventTypeId)
        if hasattr(self, 'btnTemperatureList'):
            self.btnTemperatureList.setVisible(showButtonTemperatureList)


    def getShowButtonNomenclatureExpense(self):
        showButtonNomenclatureExpense = getEventShowButtonNomenclatureExpense(self.eventTypeId)
        if hasattr(self, 'btnNomenclatureExpense'):
            self.btnNomenclatureExpense.setVisible(showButtonNomenclatureExpense)


    def getShowButtonJobTickets(self):
        showButtonJobTickets = getEventShowButtonJobTickets(self.eventTypeId)
        if hasattr(self, 'btnJobTickets'):
            self.btnJobTickets.setVisible(showButtonJobTickets)

    def getEventInfo(self, context, infoClass=CEventInfo):
        selfId = self.itemId()
        if selfId is None:
            selfId = False
        result = context.getInstance(infoClass, selfId)

        date = self.eventDate if self.eventDate else QDate.currentDate()
        record = self.record()
        showTime = getEventShowTime(self.eventTypeId)
        dateInfoClass = CDateTimeInfo if showTime else CDateInfo
        # инициализация свойств
        result._eventType = context.getInstance(CEventTypeInfo, self.eventTypeId)
        result._identify = context.getInstance(CEventIdentificationInfo, self.eventTypeId)
        result._externalId = self.getExternalId()
        result._org = context.getInstance(COrgInfo, self.orgId)
        result._relegateOrg = context.getInstance(COrgInfo, self.getRelegateOrgId())
        result._relegatePerson = context.getInstance(CPersonInfo, self.getRelegatePersonId())
        result._curator = context.getInstance(CPersonInfo, self.getCuratorId())
        result._assistant = context.getInstance(CPersonInfo, self.getAssistantId())
        result._client = context.getInstance(CClientInfo, self.clientId, date)
        result._clientId = self.clientId
        result._order = self.cmbOrder.currentIndex()+1 if hasattr(self, 'cmbOrder') else 0
        result._prevEventDate = dateInfoClass(self.getPrevEventDateTime())
        result._setDate = dateInfoClass(self.getSetDateTime())
        if showTime:
            result._setTime = CTimeInfo(self.getSetDateTime())
            result._execTime = CTimeInfo(self.getExecDateTime())
        result._setPerson = context.getInstance(CPersonInfo, self.getSetPersonId())
        result._execDate = dateInfoClass(self.getExecDateTime())
        result._execPerson = context.getInstance(CPersonInfo, self.getExecPersonId())
        result._result = context.getInstance(CResultInfo, self.cmbResult.value())
        result._nextEventDate = dateInfoClass(self.getNextEventDateTime())
        result._contract = context.getInstance(CContractInfo, self.contractId)
        result._tariffDescr = self.contractTariffCache.getTariffDescr(self.contractId, self)
        result._localContract = self.tabCash.getLocalContractInfo(context, selfId) if hasattr(self, 'tabCash') else None
        result._mes = context.getInstance(CMesInfo, self.getMesId())
        result._mesSpecification = context.getInstance(CMesSpecificationInfo, self.getMesSpecificationId())
        result._note = self.getNote()
        result._payStatus = record.value('payStatus') if record else 0
        result._patientModel = context.getInstance(CPatientModelInfo, self.getPatientModelId())
        result._cureType     = context.getInstance(CCureTypeInfo, self.getCureTypeId())
        result._cureMethod   = context.getInstance(CCureMethodInfo, self.getCureMethodId())
        result._prevEvent = context.getInstance(CEventInfo, forceRef(record.value('prevEvent_id')) if record else None)
        result._pregnancyWeek = self.edtPregnancyWeek.value() if hasattr(self, 'edtPregnancyWeek') else None
        result._diagnosises = context.getInstance(CDiagnosticInfoList, selfId)
        result._clientEvents = result.getEventCount(result._clientId) # WTF?!
        if self.prevEventId:
            result._dispansIIPhase = context.getInstance(CActionDispansPhaseInfo, selfId, 2)
            result._dispansIPhase = context.getInstance(CActionDispansPhaseInfo, self.prevEventId, 1)
        else:
            result._dispansIPhase = context.getInstance(CActionDispansPhaseInfo, selfId, 1)
            if selfId:
                db = QtGui.qApp.db
                tableEvent = db.table('Event')
                recordNextId = db.getRecordEx(tableEvent, [tableEvent['id']], [tableEvent['prevEvent_id'].eq(selfId), tableEvent['deleted'].eq(0)])
                nextEventId = forceRef(recordNextId.value('id')) if recordNextId else None
                if nextEventId:
                    result._dispansIIPhase = context.getInstance(CActionDispansPhaseInfo, nextEventId, 2)
                else:
                    result._dispansIIPhase = None
        if record:
            result._relative = context.getInstance(CClientInfo, forceRef(record.value('relative_id')))
            result._createDatetime = dateInfoClass(QDateTime(forceDateTime(record.value('createDatetime'))))
            result._modifyDatetime = dateInfoClass(QDateTime(forceDateTime(record.value('modifyDatetime'))))
            result._modifyPerson = context.getInstance(CPersonInfo, forceRef(record.value('modifyPerson_id')))
            result._createPerson = context.getInstance(CPersonInfo, forceRef(record.value('createPerson_id')))
        else:
            result._relative = context.getInstance(CClientInfo, None)
            result._createDatetime = dateInfoClass(QDateTime())
            result._modifyDatetime = dateInfoClass(QDateTime())
            result._modifyPerson = context.getInstance(CPersonInfo, None)
            result._createPerson = context.getInstance(CPersonInfo, None)
        result._feeds = context.getInstance(CFeedInfoList, selfId)
        result._csgList = context.getInstance(CCSGInfoList, selfId) if record else None # WHY?
        result._srcDate = CDateInfo(self.getSrcDate())
        result._srcNumber = self.getSrcNumber()
        result._documentLocation = context.getInstance(CDocumentLocationInfo, self.clientId, result._externalId)
        if selfId:
            result._vouchers = context.getInstance(CVoucherInfoList, selfId)
        elif getEventTypeForm(self.eventTypeId) == u'072':
            result._vouchers = [ self.getVouchers(context) ]
        else:
            result._vouchers = context.getInstance(CVoucherInfoList, None)
        tempInvalidInfo = None
        if hasattr(self, 'grpTempInvalid'):
            tempInvalidInfo = self.grpTempInvalid.getTempInvalidInfo(context)
        result._tempInvalidList = result.getTempInvalidList(forceDate(  self.getSetDateTime()),
                                                                                            forceDate(self.getExecDateTime()),
                                                                                            self.clientId,
                                                                                            None,
                                                                                            tempInvalidInfo)
        result._tempInvalidPatronageList = result.getTempInvalidList(forceDate(  self.getSetDateTime()),
                                                                                            forceDate(self.getExecDateTime()),
                                                                                            self.clientId,
                                                                                            None,
                                                                                            tempInvalidInfo,
                                                                                            patronage=True)
        # формальная инициализация таблиц
        result._actions = []
        result._visits = []
        result._ok = True
        result._loaded = True
        result._isDirty = self.isDirty()
        return result


    def recordAcceptable(self, record, setEventDate = None, birthDate = None):
        return recordAcceptable(self.clientSex, self.clientAge, record, setEventDate = setEventDate, birthDate = birthDate)


    def setWorkRecord(self, record):
        pass


    def checkClientAttendanceEE(self, personId):
        return self.checkClientAttendanceEx(personId, self.clientSex, self.clientAge) or \
               self.confirmClientAttendance(self, personId, self.clientId)


    def getPersonSSF(self, personId):
        key = personId, self.clientType
        result = self.personSSFCache.get(key, None)
        if not result:
            record = QtGui.qApp.db.getRecord('Person LEFT JOIN rbSpeciality ON rbSpeciality.id = Person.speciality_id',
                                             'speciality_id, service_id, provinceService_id, otherService_id, finance_id, tariffCategory_id',
                                             personId
                                            )
            if record:
                specialityId      = forceRef(record.value('speciality_id'))
                serviceId         = forceRef(record.value('service_id'))
                provinceServiceId = forceRef(record.value('provinceService_id'))
                otherServiceId    = forceRef(record.value('otherService_id'))
                financeId         = forceRef(record.value('finance_id'))
                tariffCategoryId  = forceRef(record.value('tariffCategory_id'))
                if self.clientType == CEventEditDialog.ctOther and otherServiceId:
                    serviceId = otherServiceId
                elif self.clientType == CEventEditDialog.ctProvince and provinceServiceId:
                    serviceId = provinceServiceId
                result = (specialityId, serviceId, financeId, tariffCategoryId)
            else:
                result = (None, None, None, None)
            self.personSSFCache[key] = result
        return result

    def cachePersonSSF(self, personIdList):
        notFoundPersons = []
        for personId in personIdList:
            key = personId, self.clientType
            result = self.personSSFCache.get(key, None)
            if not result:
                notFoundPersons.append(personId)
        if notFoundPersons:
            db = QtGui.qApp.db
            tablePerson = db.table('Person')
            tableSpeciality = db.table('rbSpeciality')
            table = tablePerson.leftJoin(tableSpeciality, tableSpeciality['id'].eq(tablePerson['speciality_id']))
            cols = [tablePerson['id'],
                    tablePerson['speciality_id'],
                    tableSpeciality['service_id'],
                    tableSpeciality['provinceService_id'],
                    tableSpeciality['otherService_id'],
                    tablePerson['finance_id'],
                    tablePerson['tariffCategory_id'],
                    ]
            records = db.getRecordList(table, cols, where=tablePerson['id'].inlist(notFoundPersons))
            for record in records:
                personId = forceRef(record.value('id'))
                specialityId = forceRef(record.value('speciality_id'))
                serviceId = forceRef(record.value('service_id'))
                provinceServiceId = forceRef(record.value('provinceService_id'))
                otherServiceId = forceRef(record.value('otherService_id'))
                financeId = forceRef(record.value('finance_id'))
                tariffCategoryId = forceRef(record.value('tariffCategory_id'))
                if self.clientType == CEventEditDialog.ctOther and otherServiceId:
                    serviceId = otherServiceId
                elif self.clientType == CEventEditDialog.ctProvince and provinceServiceId:
                    serviceId = provinceServiceId
                result = (specialityId, serviceId, financeId, tariffCategoryId)
                key = personId, self.clientType
                self.personSSFCache[key] = result


    def getPersonSpecialityId(self, personId):
        return self.getPersonSSF(personId)[0]

    def getPersonServiceId(self, personId):
        return self.getPersonSSF(personId)[1]


    def getPersonFinanceId(self, personId):
        return self.getPersonSSF(personId)[2]


    def getPersonTariffCategoryId(self, personId):
        return self.getPersonSSF(personId)[3]


    def setPersonId(self, personId):
        self.personId = personId
        self.personSpecialityId, self.personServiceId, self.personFinanceId, self.personTariffCategoryId = self.getPersonSSF(personId)
        self.resetActionTemplateCache()
        if hasattr(self, 'tabMes'):
            self.tabMes.setSpeciality(self.personSpecialityId)
    
    
    def initOrder(self, availableOrders, defaultOrder, form110=False):
        cmbOrder = self.cmbOrderEvent if form110 else self.cmbOrder
        cmbOrder.setCurrentIndex(defaultOrder-1)
        if availableOrders:
            for index in range(cmbOrder.count()):
                if forceString(index+1) not in forceString(availableOrders):
                    cmbOrder.model().item(index).setEnabled(False)


    def getSuggestedPersonId(self):
        return QtGui.qApp.userId if QtGui.qApp.userSpecialityId else self.personId


    def getVisitFinanceId(self, personId=None):
        financeId = None
        if getEventVisitFinance(self.eventTypeId):
            financeId = self.getPersonFinanceId(personId) if personId else self.personFinanceId
        if not financeId:
            financeId = forceRef(QtGui.qApp.db.translate('Contract', 'id', self.cmbContract.value(), 'finance_id'))
        return financeId


    def getActionFinanceId(self, actionRecord):
        finance = getEventActionFinance(self.eventTypeId)
        if finance == 1:
            return self.eventFinanceId
        elif finance == 2:
            personId = forceRef(actionRecord.value('setPerson_id'))
            return self.getPersonFinanceId(personId) if personId else self.personFinanceId
        elif finance == 3:
            personId = forceRef(actionRecord.value('person_id'))
            return self.getPersonFinanceId(personId) if personId else self.personFinanceId
        else:
            return None


    def specifyDiagnosis(self, MKB):
        diagFilter = self.getDiagFilter()
        date = min(d for d in (self.eventSetDateTime.date(), self.eventDate, QDate.currentDate()) if d)
        acceptable, specifiedMKB, specifiedMKBEx, specifiedCharacterId, specifiedTraumaTypeId, modifiableDiagnosisId, specifiedDispanserId, specifiedRequiresFillingDispanser, specifiedProlongMKB = specifyDiagnosis(self, MKB, diagFilter, self.clientId, self.clientSex, self.clientAge, date, self.mapMKBTraumaList)
        self.modifiableDiagnosisesMap[specifiedMKB] = modifiableDiagnosisId
        return acceptable, specifiedMKB, specifiedMKBEx, specifiedCharacterId, specifiedTraumaTypeId, specifiedDispanserId, specifiedRequiresFillingDispanser, specifiedProlongMKB


    def modifyDiagnosises(self, MKBDiagnosisIdPairList):
        db = QtGui.qApp.db
        for MKB, newDiagnosisId in MKBDiagnosisIdPairList:
            oldDiagnosisId = self.modifiableDiagnosisesMap.get(MKB, None)
            if oldDiagnosisId:
                db.query('UPDATE Diagnosis SET mod_id=%d WHERE id=%d AND mod_id IS NULL AND deleted=0'%(newDiagnosisId, oldDiagnosisId))
                db.query('UPDATE Diagnosis AS DOld, Diagnosis AS DNew '
                         'SET DNew.setDate=DOld.setDate '
                         'WHERE DNew.id=%d AND DOld.id=%d AND DOld.mod_id=DNew.id AND '
                         'DNew.setDate IS NOT NULL AND DOld.setDate IS NOT NULL AND DOld.setDate<DNew.setDate'%(newDiagnosisId, oldDiagnosisId))


    def resetActionTemplateCache(self):
        pass


    def getVisitCount(self):
        return 1


    def getEventDuration(self, weekProfile):
        startDate = self.eventSetDateTime.date() if self.eventSetDateTime else QDate.currentDate()
        stopDate = self.eventDate if self.eventDate else QDate.currentDate()
        return getEventDuration(startDate, stopDate, weekProfile, self.eventTypeId)


    def emitUpdateActionsAmount(self):
        self.emit(SIGNAL('updateActionsAmount()'))


    def getPrevActionId(self, action, type):
        return self.getPrevActionIdHelper.getPrevActionId(action, type)


    def checkAndUpdateExpertise(self, endDate, personId):
        result = True
        if hasattr(self, 'tabNotes') and hasattr(self.tabNotes, 'edtExpertiseDate') and hasattr(self.tabNotes, 'cmbExpertPerson'):
            expertiseDate = self.tabNotes.edtExpertiseDate.date()
            expertPersonId = self.tabNotes.cmbExpertPerson.value()
            if isEventAutoFillingExpertise(self.eventTypeId) and not expertiseDate and not expertPersonId:
                self.tabNotes.edtExpertiseDate.setDate(endDate)
                self.tabNotes.cmbExpertPerson.setValue(personId)
            result = result and ((expertiseDate and expertPersonId) or self.checkExpertiseInfo(expertiseDate, expertPersonId))
        return result


    def checkExpertiseInfo(self, expertiseDate, expertPersonId):
        result = True
        if not expertiseDate and not expertPersonId:
            return result
        if not expertiseDate:
            result = self.checkValueMessage(u'Необходимо указать Дату экспертизы случая', False, self.tabNotes.edtExpertiseDate)
        if not expertPersonId:
            result = self.checkValueMessage(u'Необходимо указать Эксперта', False, self.tabNotes.cmbExpertPerson)
        return result


    def checkDiagnosisType(self, model, table):
        personIdData = {}
        for row, record in enumerate(model.items()):
            personId = forceRef(record.value('person_id'))
            diagnosisTypeId = forceRef(record.value('diagnosisType_id'))
            if diagnosisTypeId and diagnosisTypeId in [model.diagnosisTypeCol.ids[0], model.diagnosisTypeCol.ids[1]]:
                personIdLine = personIdData.get(personId, [])
                personIdLine.append(diagnosisTypeId)
                personIdData[personId] = personIdLine
                if len(personIdLine) > 1:
                    if not self.checkValueMessage(u'В событии у врача %s существуют основной и заключительный диагнозы. Необходимо исправить!'%(forceString(QtGui.qApp.db.translate('vrbPersonWithSpeciality', 'id', personId, 'name'))), True, table, row, record.indexOf('diagnosisType_id')):
                        return False
        return True


    def checkDiagnosticsType(self, model):
        result = True
        endDate = self.edtEndDate.date()
        if endDate:
            result = result and self.checkDiagnosticsTypeEnd(model) or self.checkValueMessage(u'Необходимо указать заключительный диагноз', False, self.tblFinalDiagnostics)
        return result


    def checkDiagnosticsTypeEnd(self, model):
        for row, record in enumerate(model.items()):
            if  forceInt(record.value('diagnosisType_id')) == model.diagnosisTypeCol.ids[0]:
                return True
        return False


    def checkDiagnosticsMKBForMes(self, tableFinalDiagnostics, mesId):
        model = tableFinalDiagnostics.model()
        result, finalDiagnosis = self.checkMKBForMes(tableFinalDiagnostics, mesId, model.diagnosisTypeCol.ids[0])
        if result and not finalDiagnosis:
            result, finalDiagnosis = self.checkMKBForMes(tableFinalDiagnostics, mesId, model.diagnosisTypeCol.ids[1])
        return result


    def checkMKBForMes(self, tableFinalDiagnostics, mesId, diagnosisTypeId):
        finalDiagnosis = False
        model = tableFinalDiagnostics.model()
        db = QtGui.qApp.db
        table = db.table('mes.MES_mkb')
        if mesId:
            for row, record in enumerate(model.items()):
                if  forceInt(record.value('diagnosisType_id')) == diagnosisTypeId:
                    MKB = forceString(record.value('MKB'))
                    if MKB:
                        finalDiagnosis = True
                        recordMES = db.getRecordEx(table, [table['id'], table['mkb']], [table['master_id'].eq(mesId), table['deleted'].eq(0), table['mkb'].isNotNull()])
                        if not recordMES:
                            return True, finalDiagnosis
                        recordMES = db.getRecordEx(table, [table['id'], table['mkb']], [table['master_id'].eq(mesId), table['deleted'].eq(0), table['mkb'].like(MKB)])
                        if not recordMES:
                            if not self.checkValueMessage(u'Несоответствие шифра МКБ заключительного диагноза %s требованиям МЭС'%(MKB), True, tableFinalDiagnostics, row, record.indexOf('MKB')):
                                return False, finalDiagnosis
        return True, finalDiagnosis

    def checkCorrectlyEnteredPersons(self, cmbPerson, diagnostic=[]):
        message = u''
        result = True
        widgetFocus = rowFocus = columnFocus = detailWdigetFocus = None
        if not checkPersonByDefaultSettingsFromEventtype(cmbPerson.value(), self.eventTypeId):
            message += u'   - исполнитель в обращении (%s)\n' % cmbPerson.name()
            widgetFocus = cmbPerson
        if hasattr(self, 'tblVisits'):
            model = self.tblVisits.model()
            for row, record in enumerate(model.items()):
                personId = forceRef(record.value('person_id'))
                if not checkPersonByDefaultSettingsFromEventtype(personId, self.eventTypeId):
                    message += u'   - врач в посещении (%s)\n' % forceString(
                        model.data(model.index(row, model.getColIndex('person_id'))))
                    if not widgetFocus:
                        widgetFocus = self.tblVisits
                        rowFocus = row
                        columnFocus = model.getColIndex('person_id')
        if diagnostic:
            tblInspections, modelDiagnostics = diagnostic
            for row, record in enumerate(modelDiagnostics.items()):
                personId = forceRef(record.value('person_id'))
                specialityId = forceRef(record.value('speciality_id'))
                if not checkPersonByDefaultSettingsFromEventtype(personId, self.eventTypeId, specialityId):
                    message += u'   - врач в диагностике (%s)\n' % forceString(
                        modelDiagnostics.data(modelDiagnostics.index(row, modelDiagnostics.getColIndex('person_id'))))
                    if not widgetFocus:
                        widgetFocus = tblInspections
                        rowFocus = row
                        columnFocus = modelDiagnostics.getColIndex('person_id')
        for actionTab in self.getActionsTabsList():
            model = actionTab.tblAPActions.model()
            for row, (record, action) in enumerate(model.items()):
                if action and action.getType().id:
                    if not checkPersonByDefaultSettingsFromEventtype(forceInt(record.value('person_id')),
                                                                     self.eventTypeId):
                    # if not action.getType().getPFOrgStructureRecordList() and not action.getType().getPFSpecialityRecordList() and not checkPersonByDefaultSettingsFromEventtype(
                    #         forceInt(record.value('person_id')), self.eventTypeId):
                        message += u'   - врач в типе действия %s (%s)\n' % (action.getType().name,
                                                                        actionTab.cmbAPPerson.itemText(
                                                                            actionTab.cmbAPPerson.model().searchId(
                                                                                forceInt(record.value('person_id')))))
                        if not widgetFocus:
                            widgetFocus = actionTab.tblAPActions
                            rowFocus = row
                            columnFocus = 0
                            detailWdigetFocus = actionTab.cmbAPPerson
        if message:
            message = u'Врач не соответствует умолчаниям типа события\n' + message
            result = result and self.checkValueMessage(message, QtGui.qApp.checkGlobalPreference('23:checkChosenPerson',
                                                                                                 u'мягкий'),
                                                       widgetFocus, rowFocus, columnFocus, detailWdigetFocus)
        return result
    def getDiagnosisForOnko(self):
        return '', '', ''

    def checkNeedTNMS(self, tblDiagnostics, cColumns, pColumns):
        if not QtGui.qApp.isTNMSVisible():
            return True

        controlOnkoTNMS = QtGui.qApp.controlOnkoTNMS()
        if controlOnkoTNMS not in (1, 2):
            return True

        from Events.Utils import mkbIsOnko
        mkb = self.getDiagnosisForOnko()
        if not mkbIsOnko(mkb[0], mkb[2], includeHematologyMKB=0):
            return True

        result = True

        try:
            from library.TNMS.TNMSComboBox import CTNMSComboBox

            # создавать комбобокс только при необходимости
            class CTNMSSingleton(object):
                _instance = None
                def __new__(cls, *args, **kwargs):
                    if cls._instance is None:
                        cls._instance = super(CTNMSSingleton, cls).__new__(cls, *args, **kwargs)
                        cls._instance.tnmsComboBox = None
                    return cls._instance

                def __init__(self, parent, date, MKB):
                    if self.tnmsComboBox is None:
                        self.tnmsComboBox = CTNMSComboBox(parent)
                        self.tnmsComboBox.setEndDate(date)
                        self.tnmsComboBox.setMKB(MKB)
                        self.tnmsComboBox._popup = self.tnmsComboBox.createPopup()
                        for idx in range(self.tnmsComboBox._popup.layout().count()):
                            wgt = self.tnmsComboBox._popup.layout().itemAt(idx).widget()
                            if wgt is not None:
                                wgt.blockSignals(True)
                        self.tnmsComboBox.updatePopupBeforeShow()

                def getPopup(self):
                    return self.tnmsComboBox._popup

            tnms = None
            modelDiagnostics = tblDiagnostics.model()
            rowFocus = None
            for idx, record in enumerate(modelDiagnostics.items()):
                if forceRef(record.value('diagnosisType_id')) in (1, 2):
                    date = self.edtEndDate.date() if self.edtEndDate.date() else self.edtBegDate.date()
                    # условие в соответствии со счетами
                    if forceRef(record.value('cTNMphase_id')):
                        count = 0
                        if 'cTumor_id' in cColumns \
                                and (forceRef(record.value('cTumor_id'))
                                     or CTNMSSingleton(self, date, mkb[0]).getPopup().cmbCTumor.count() == 1):
                            count += 1
                        if 'cNodus_id' in cColumns \
                                and (forceRef(record.value('cNodus_id'))
                                     or CTNMSSingleton(self, date, mkb[0]).getPopup().cmbCNodus.count() == 1):
                            count += 1
                        if 'cMetastasis_id' in cColumns \
                                and (forceRef(record.value('cMetastasis_id'))
                                     or CTNMSSingleton(self, date, mkb[0]).getPopup().cmbCMetastasis.count() == 1):
                            count += 1
                        if 'cTNMphase_id' in cColumns \
                                and (forceRef(record.value('cTNMphase_id'))
                                     or CTNMSSingleton(self, date, mkb[0]).getPopup().cmbCStage.count() == 1):
                            count += 1
                        tnms = count == len(cColumns)
                        # tnms = all(forceRef(record.value(col)) for col in cColumns)
                    elif forceRef(record.value('pTNMphase_id')):
                        count = 0
                        if 'pTumor_id' in pColumns \
                                and (forceRef(record.value('pTumor_id'))
                                     or CTNMSSingleton(self, date, mkb[0]).getPopup().cmbPTumor.count() == 1):
                            count += 1
                        if 'pNodus_id' in pColumns \
                                and (forceRef(record.value('pNodus_id'))
                                     or CTNMSSingleton(self, date, mkb[0]).getPopup().cmbPNodus.count() == 1):
                            count += 1
                        if 'pMetastasis_id' in pColumns \
                                and (forceRef(record.value('pMetastasis_id'))
                                     or CTNMSSingleton(self, date, mkb[0]).getPopup().cmbPMetastasis.count() == 1):
                            count += 1
                        if 'pTNMphase_id' in pColumns \
                                and (forceRef(record.value('pTNMphase_id'))
                                     or CTNMSSingleton(self, date, mkb[0]).getPopup().cmbPStage.count() == 1):
                            count += 1
                        tnms = count == len(pColumns)
                        # tnms = all(forceRef(record.value(col)) for col in pColumns)
                    elif CTNMSSingleton(self, date, mkb[0]).getPopup().cmbCStage.count() == 1:
                        tnms = True
                    rowFocus = idx
                    break
            if not tnms:
                result = self.checkValueMessage(u"Необходимо заполнить 'TNM-Ст'", controlOnkoTNMS == 1, tblDiagnostics,
                                                row=rowFocus, column=modelDiagnostics.getColIndex('TNMS'))
        except:
            QtGui.qApp.logCurrentException()
        return result

    def checkServiceDates(self, begDate, endDate):
        result = True
        if hasattr(self, 'tabNotes') and hasattr(self.tabNotes, 'chkExpose') and self.tabNotes.chkExpose.isChecked():
            if endDate:
                from Exchange.ExportR23Native import CExportPage1

                tableService = QtGui.qApp.db.table('rbService')
                cond = [
                    QtGui.qApp.db.joinOr([tableService['infis'].inlist(CExportPage1.reabilitationKuslList),
                                          tableService['infis'].inlist(CExportPage1.diabetSchoolKuslList) if endDate >= QDate(2025, 3, 1) else '0',
                                          tableService['infis'].inlist(CExportPage1.chronicDiseaseSchoolKuslList) if endDate >= QDate(2025, 10, 1) else '0'])
                ]
                begDates = endDates = []
                if isinstance(begDate, QDateTime):
                    begDate = begDate.date()
                if isinstance(endDate, QDateTime):
                    endDate = endDate.date()

                for actionTab in self.getActionsTabsList():
                    model = actionTab.tblAPActions.model()
                    for record, action in model.items():
                        financeId = forceRef(record.value('finance_id'))
                        if financeId is None or CFinanceType.getCode(financeId) == CFinanceType.CMI:
                            serviceIdList = self.getActionTypeServiceIdList(action.getType().id, CFinanceType.CMI)
                            if serviceIdList:
                                endDates.append(forceDate(record.value('endDate')))
                                # проверка на дату начала услуги как в выставлении счетов
                                if action.getType().name.upper().startswith(u'ОБРАЩЕН') or QtGui.qApp.db.getCount(
                                        tableService, where=cond + [tableService['id'].inlist(serviceIdList)]):
                                    begDates.append(forceDate(record.value('begDate')))
                                else:
                                    begDates.append(forceDate(record.value('endDate')))

                if not (begDate in begDates and endDate in endDates):
                    result = result and self.checkValueMessage(
                    u'Нет услуги, у которой "Дата начала" совпадала бы с "Датой начала лечения" или "Дата окончания" совпадала бы с "Датой окончания лечения"',
                    False, self)
        return result

    def selectNomenclatureAddedActions(self, tabList):
        result = True
        actionExpenseItems = []
        db = QtGui.qApp.db
        tableATN = db.table('ActionType_Nomenclature')
        for actionTab in tabList:
            model = actionTab.tblAPActions.model()
            items = model.items()
            for recordExpense, actionExpense in items:
                record = actionExpense.getRecord()
                status = forceInt(record.value('status'))
                stockMotionId = forceRef(record.value('stockMotion_id'))
                actionTypeId = forceRef(record.value('actionType_id'))
                if actionTypeId and actionExpense.getType().isNomenclatureExpense and actionExpense.nomenclatureExpense and not stockMotionId:
                    nomenclatureIdList = db.getDistinctIdList(tableATN, [tableATN['id']], [tableATN['master_id'].eq(actionTypeId)])
                    if nomenclatureIdList:
                        if not actionExpense._actionType.generateAfterEventExecDate or bool(actionExpense._actionType.generateAfterEventExecDate and self.eventDate):
                            if actionExpense.nomenclatureExpense and status == CActionStatus.finished and (
                                    actionExpense.nomenclatureExpense.getStockMotionId() or actionExpense.nomenclatureExpense.stockMotionItems()):
                                actionExpenseItems.append((recordExpense, actionExpense))
        if actionExpenseItems:
            dialog = CNomenclatureAddedActionsSelectDialog(self, actionExpenseItems)
            try:
                if dialog.exec_():
                    actionExpenseItems = dialog.getActionExpenseItems()
                    result = True
                else:
                    result = False
            finally:
                dialog.deleteLater()
        return result


    def checkActionsDateEnteredActuality(self, begDate, endDate, tabList):
        result = True
        db = QtGui.qApp.db
        table = db.table('EventType_Action')
        tableActionType = db.table('ActionType')
        cols = [table['actuality']]
        actionHospitalBeds = False
        for actionTab in tabList:
            model = actionTab.tblAPActions.model()
            for row, (record, action) in enumerate(model.items()):
                if action and action._actionType.id:
                    showTime = action._actionType.showTime and getEventShowTime(self.eventTypeId)
                    forceDateOrDateTime = forceDateTime if showTime else forceDate
                    rowEndDate = forceDateOrDateTime(record.value('endDate'))
                    rowEndDateToCompare = self._date2StringToCompare(rowEndDate)
                    if rowEndDate:
                        actuality = None
                        expirationDate = 0
                        actionTypeId = action._actionType.id
                        actionTypeItem = action.getType()
                        if self.eventTypeId and actionTypeId:
                            cond = [table['eventType_id'].eq(self.eventTypeId),
                                    table['actionType_id'].eq(actionTypeId)
                                    ]
                            recordActuality = db.getRecordEx(table, cols, cond, 'EventType_Action.eventType_id')
                            if recordActuality:
                                actuality = forceInt(recordActuality.value(0))
                        if not actuality and actionTypeId:
                            recordExpirationDate = db.getRecordEx(tableActionType, [tableActionType['expirationDate']], [tableActionType['id'].eq(actionTypeId), tableActionType['deleted'].eq(0)])
                            if recordExpirationDate:
                                expirationDate = forceInt(recordExpirationDate.value(0))
                                if expirationDate and not actuality:
                                        actuality = expirationDate
                        if actuality:
                            if endDate:
                                nextDate = endDate.addMonths(+actuality)
                                endDateToCompare = self._date2StringToCompare(nextDate.date() if isinstance(nextDate, QDateTime) and not showTime else nextDate)
                                if rowEndDateToCompare > endDateToCompare:
                                    result = result and self.checkValueMessage(u'Дата выполнения должна быть не позже %s (с учётом срока "годности" данных)' % forceString(endDate), True, actionTab.tblAPActions, row, 0, actionTab.edtAPEndDate)
                            if begDate:
                                lowDate = begDate.addMonths(-actuality)
                                lowDateToCompare = self._date2StringToCompare(lowDate.date() if isinstance(lowDate, QDateTime) and not showTime else lowDate)
                                if rowEndDateToCompare < lowDateToCompare:
                                    result = result and self.checkValueMessage(u'Дата выполнения должна быть не раньше %s (с учётом срока "годности" данных)' % forceString(lowDate), False, actionTab.tblAPActions, row, 0, actionTab.edtAPEndDate)
                        if actionTypeItem and (u'received' in actionTypeItem.flatCode.lower()
                               or u'moving' in actionTypeItem.flatCode.lower()
                               or u'leaved' in actionTypeItem.flatCode.lower()):
                            actionHospitalBeds = result
        if not result and actionHospitalBeds:
            dialog = CCheckPeriodActionsForEvent(self, tabList, self.itemId(), self.prevEventId)
            try:
                if dialog.exec_():
                    pass
            finally:
                dialog.deleteLater()
        return result


    def checkActionProperties(self, actionTab, action, tblAPProps, actionRow=None):
        def isNull(val, typeName=None):
            if val is None:
                return True
            if isinstance(val, (QString, str, unicode)):
                if typeName == 'ImageMap':
                    return 'object' not in val
                if typeName == 'Html':
                    edt = QtGui.QTextEdit()
                    edt.setHtml(val)
                    val = edt.toPlainText()
                if not trim(val):
                    return True
                # строка не должна состоять только из точек, тире или
                # прочих незначимых символов, которыми пользователи обходят штрафы.
                # +по тз проверять минимальную длину в 3 символа(
                if typeName in ('String', 'Text') and QtGui.qApp.getGlobalPreference(
                        '23:checkActionPropertyStringValue') == u'да':
                    # any(symb.isalnum() for symb in val):
                    if not CEventEditDialog.re_actionPropertyStringChecking.search(val):
                        return True
            if isinstance(val, list):
                return bool(val)
            if type(val) == QDate:
                return not val.isValid()
            return False

        actionType = action.getType()
        propertyTypeList = actionType.getPropertiesById().items()
        propertyTypeList.sort(key=lambda x: (x[1].idx, x[0]))
        propertyTypeList = [x[1] for x in propertyTypeList if x[1].applicable(self.clientSex, self.clientAge)]
        propertyAssignedRequired = False
        if actionType.propertyAssignedVisible:
            propertyAssignedRequired = actionType.propertyAssignedRequired
        actionEndDate = forceDate(action.getRecord().value('endDate'))
        assignedAny = False
        assignedRow = -1
        actionTypeName = actionType.name
        for row, propertyType in enumerate(propertyTypeList):
            property = action.getPropertyById(propertyType.id)
            if propertyType.isAssignable:
                if assignedRow < 0:
                    assignedRow = row
                if property._isAssigned:
                    assignedAny = True
            penalty = propertyType.penalty
            needChecking = penalty > 0 and ((penalty < 50 and not isNull(actionEndDate)) or (50 <= penalty < 75) or (75 <= penalty < 100 and not isNull(self.eventDate)) or penalty == 100)
            if needChecking or propertyType.isFill:
                skippable = (penalty < 50 and isNull(actionEndDate)) or (50 <= penalty < 75) or (75 <= penalty < 100 and isNull(self.eventDate)) or propertyType.isFill
                if propertyType.isJobTicketValueType() and forceInt(action._record.value('status')) == CActionStatus.withoutResult:
                    skippable = False
                if isNull(property._value, propertyType.typeName):
                    if actionTab:
                        actionRow = actionTab.tblAPActions.model()._mapModelRow2ProxyRow[actionRow]
                    propertyTypeName = propertyType.name
                    if actionRow and actionTab:
                        actionTab.tblAPActions.setCurrentIndex(actionTab.tblAPActions.model().createIndex(actionRow, 0))
                    result = self.checkValueMessage(u'%sНеобходимо заполнить значение свойства "%s" в действии "%s"' %(u'Свойство "%s" является обязательным для заполнения.\n'%(propertyTypeName), propertyTypeName, actionTypeName), skippable, tblAPProps, row, 1)
                    if not result:
                        return result
        if propertyAssignedRequired and assignedRow > -1 and not assignedAny:
            result = self.checkValueMessage(u'В действии "{}" необходимо назначить хотя бы один показатель.'.format(actionTypeName), False, tblAPProps, assignedRow, 1)
            if not result:
                return result
        return True


    def checkVisitsDataEntered(self, begDate, endDate):
        if hasattr(self, 'modelVisits'):
            visitsServiceIdList = []
            for row, record in enumerate(self.modelVisits.items()):
                if not self.checkVisitDataEntered(begDate, endDate, row, record):
                    return False
                if not self.checkDoubleVisitsBySpecialityEntered(row, record):
                    return False
                if not self.checkDoubleVisitsEntered(row, record):
                    return False
                serviceId = forceRef(record.value('service_id'))
                if serviceId not in visitsServiceIdList:
                    visitsServiceIdList.append(serviceId)
            if getEventAidTypeCode(self.eventTypeId) == '7' and len(visitsServiceIdList) > 1:
                if not self.checkValueMessage(u'У визитов разные профили оплаты. Отредактировать по первому визиту?',
                                              True, None):
                    serviceId = visitsServiceIdList[0]
                    for record in self.modelVisits.items():
                        record.setValue('service_id', toVariant(serviceId))
        return True


    def checkVisitDataEntered(self, begDateTime, endDateTime, row, record):
        result = True
        showVisitTime = getEventShowVisitTime(self.eventTypeId)
        showTime = getEventShowTime(self.eventTypeId)

        if showVisitTime and showTime:
            begDate = toDateTimeWithoutSeconds(begDateTime)
            endDate = toDateTimeWithoutSeconds(endDateTime)
        else:
            begDate = begDateTime.date() if isinstance(begDateTime, QDateTime) else begDateTime
            endDate = endDateTime.date() if isinstance(endDateTime, QDateTime) else endDateTime

        date = toDateTimeWithoutSeconds(forceDateTime(record.value('date'))) if showVisitTime and showTime else forceDate(record.value('date'))
        currentDate = toDateTimeWithoutSeconds(QDateTime.currentDateTime()) if showVisitTime and showTime else QDate.currentDate()
        possibleDeathDate = QDate()
        if self.clientBirthDate:
            possibleDeathDate = self.clientBirthDate.addYears(QtGui.qApp.maxLifeDuration)
        result = result and (date or self.checkInputMessage(u'дату', False, self.tblVisits, row, record.indexOf('date')))
        result = result and (date <= currentDate or self.checkValueMessage(u'Датa посещения %s не может быть позже текущей даты %s'% (forceString(date), forceString(currentDate)), True if (getEventTypeForm(self.eventTypeId) == u'030' and not self.tabNotes.isEventClosed() and self.dateOfVisitExposition in [1, 2]) else False, self.tblVisits, row, record.indexOf('date')))
        if showVisitTime and showTime:
            result = result and (begDate<=date or self.checkUpdateDateTimeMessage(u'Датa посещения %s предшествует дате назначения %s.\nИзменить дату назначения на %s?' % (forceString(date), forceString(begDate), forceString(date)), self.edtBegDate, self.edtBegTime, self.tblVisits, date, row, record.indexOf('date')))
        else:
            result = result and (begDate<=date or self.checkUpdateMessage(u'Датa посещения %s предшествует дате назначения %s.\nИзменить дату назначения на %s?' % (forceString(date), forceString(begDate), forceString(date)), self.edtBegDate, self.tblVisits, date, row, record.indexOf('date')))
        if endDate:
            result = result and (date<=endDate or self.checkValueMessage(u'Датa посещения %s после даты завершения %s' % (forceString(date), forceString(endDate)), False, self.tblVisits, row, record.indexOf('date')))
        if self.clientBirthDate:
            result = result and (date >= self.clientBirthDate or self.checkValueMessage(u'Дата посещения %s не может быть раньше даты рождения пациента %s' % (forceString(date), forceString(self.clientBirthDate)), False, self.tblVisits, row, record.indexOf('date')))
        if self.clientDeathDate:
            result = result and ((date.date() if isinstance(date, QDateTime) else date) <= self.clientDeathDate or self.eventPurposeId == 6 or self.checkValueMessage(u'Дата посещения %s не может быть позже имеющейся даты смерти пациента %s' % (forceString(date.date()) if isinstance(date, QDateTime) else forceString(date), forceString(self.clientDeathDate)), False, self.tblVisits, row, record.indexOf('date')))
        if possibleDeathDate:
            result = result and ((date.date() if isinstance(date, QDateTime) else date) <= possibleDeathDate or self.eventPurposeId == 6 or self.checkValueMessage(u'Дата посещения %s не может быть позже возможной даты смерти пациента %s' % (forceString(date.date()) if isinstance(date, QDateTime) else forceString(date), forceString(possibleDeathDate)), False, self.tblVisits, row, record.indexOf('date')))
        result = result and (forceRef(record.value('scene_id')) or self.checkInputMessage(u'место визита', False, self.tblVisits, row, record.indexOf('scene_id')))
        result = result and (forceRef(record.value('visitType_id')) or self.checkInputMessage(u'тип визита', False, self.tblVisits, row, record.indexOf('visitType_id')))
        result = result and (forceRef(record.value('person_id')) or self.checkInputMessage(u'исполнитель', False, self.tblVisits, row, record.indexOf('person_id')))
        result = result and (forceRef(record.value('finance_id')) or self.checkInputMessage(u'тип финансирования', False, self.tblVisits, row, record.indexOf('finance_id')))
        return result


    def checkExecDateForVisit(self, execDate):
        if hasattr(self, 'modelVisits') and isEventCheckedExecDateForVisit(self.eventTypeId):
            items = self.modelVisits.items()
            if items:
                items.sort(key=lambda x: forceDate(x.value('date')), reverse=True)
                date = forceDate(items[0].value('date'))
                if date != execDate:
                    return self.checkValueMessage(u'Дата выполнения События %s не равна дате последнего визита %s'% (forceString(execDate), forceString(date)), False, self.edtEndDate)
        return True


    def checkDoubleVisitsBySpecialityEntered(self, row, record):
        result = True
        eventId  = self.itemId()
        serviceId = forceRef(record.value('service_id'))
        personId = forceRef(record.value('person_id'))
        date = forceDate(record.value('date'))
        currentVisitId = forceRef(record.value('id'))
        nameSpeciality = u''
        currentVisitIdList = []
        keepVisitParity = getEventKeepVisitParity(self.eventTypeId)
        if serviceId and date and (self.eventSetDateTime.date() <= date) and QtGui.qApp.isCheckDoubleVisitsEnteredBySpeciality() in (1, 2):
            db = QtGui.qApp.db
            specialityId = forceRef(db.translate('Person', 'id', personId, 'speciality_id'))
            nameSpeciality = forceString(db.translate('rbSpeciality', 'id', specialityId, 'name'))
            if not keepVisitParity:
                if currentVisitId:
                    for rowVisits, recordVisits in enumerate(self.modelVisits.items()):
                        visitId = forceRef(recordVisits.value('id'))
                        if forceRef(db.translate('Person', 'id', recordVisits.value('person_id'), 'speciality_id')) == specialityId and forceDate(recordVisits.value('date')) == date and visitId != currentVisitId:
                            if visitId not in currentVisitIdList:
                                currentVisitIdList.append(visitId)
                            if  QtGui.qApp.isCheckDoubleVisitsEnteredBySpeciality()==1:
                                result = result and self.checkValueMessage(u'Посещение %s со специальностью %s не уникально в данном событии'% (forceString(date), nameSpeciality), True, self.tblVisits, row)
                            elif QtGui.qApp.isCheckDoubleVisitsEnteredBySpeciality()==2:
                                result = result and self.checkValueMessage(u'Посещение %s со специальностью %s не уникально в данном событии'% (forceString(date), nameSpeciality), False, self.tblVisits, row)
                            if not result:
                                return result
                else:
                    checkQuantity = 0
                    for rowVisits, recordVisits in enumerate(self.modelVisits.items()):
                        if forceRef(db.translate('Person', 'id', recordVisits.value('person_id'), 'speciality_id')) == specialityId and forceDate(recordVisits.value('date')) == date:
                            if checkQuantity > 0:
                                if  QtGui.qApp.isCheckDoubleVisitsEnteredBySpeciality()==1:
                                    result = result and self.checkValueMessage(u'Посещение %s со специальностью %s не уникально в данном событии'% (forceString(date), nameSpeciality), True, self.tblVisits, row)
                                elif  QtGui.qApp.isCheckDoubleVisitsEnteredBySpeciality()==2:
                                    result = result and self.checkValueMessage(u'Посещение %s со специальностью %s не уникально в данном событии'% (forceString(date), nameSpeciality), False, self.tblVisits, row)
                                if not result:
                                    return result
                            checkQuantity += 1
            if self.clientId:
                tableEvent = db.table('Event')
                tableVisit = db.table('Visit')
                tableVrbPersonWithSpeciality = db.table('vrbPersonWithSpeciality')
                cols = [tableVisit['id'],
                        tableVisit['date'],
                        tableVisit['service_id'],
                        tableVisit['person_id'],
                        tableEvent['setDate'],
                        tableEvent['execDate'],
                        tableVrbPersonWithSpeciality['name'].alias('namePerson')
                        ]
                table = tableEvent.innerJoin(tableVisit, tableVisit['event_id'].eq(tableEvent['id']))
                table = table.innerJoin(tableVrbPersonWithSpeciality, tableVrbPersonWithSpeciality['id'].eq(tableEvent['execPerson_id']))
                condEvents = [tableVisit['date'].eq(date),
                              tableVrbPersonWithSpeciality['speciality_id'].eq(specialityId),
                              tableEvent['client_id'].eq(self.clientId),
                              tableEvent['deleted'].eq(0),
                              tableVisit['deleted'].eq(0)
                             ]
                if eventId:
                    condEvents.append(tableEvent['id'].ne(eventId))
                if currentVisitIdList != []:
                    condEvents.append(tableVisit['id'].notInlist(currentVisitIdList))
                recordListEvents = db.getRecordList(table, cols, condEvents, 'Event.eventType_id')
                visitId = None
                for recordEvents in recordListEvents:
                    if currentVisitId:
                        visitId = forceRef(recordEvents.value('id'))
                        if visitId != currentVisitId:
                            if  QtGui.qApp.isCheckDoubleVisitsEnteredBySpeciality()==1:
                                result = result and self.checkValueMessage(u'Посещение %s со специальностью %s не уникально.\nИ находится в событии: %s за период с %s по %s ответственный %s'% (forceString(date), nameSpeciality, forceString(recordEvents.value('nameEventType')), forceString(recordEvents.value('setDate')), forceString(recordEvents.value('execDate')), forceString(recordEvents.value('namePerson'))), True, self.tblVisits, row)
                            elif QtGui.qApp.isCheckDoubleVisitsEnteredBySpeciality()==2:
                                result = result and self.checkValueMessage(u'Посещение %s со специальностью %s не уникально.\nИ находится в событии: %s за период с %s по %s ответственный %s'% (forceString(date), nameSpeciality, forceString(recordEvents.value('nameEventType')), forceString(recordEvents.value('setDate')), forceString(recordEvents.value('execDate')), forceString(recordEvents.value('namePerson'))), False, self.tblVisits, row)
                            if not result:
                                return result
                    else:
                        if forceRef(db.translate('Person', 'id', recordEvents.value('person_id'), 'speciality_id')) == specialityId and forceDate(recordEvents.value('date')) == date:
                            if  QtGui.qApp.isCheckDoubleVisitsEnteredBySpeciality()==1:
                                result = result and self.checkValueMessage(u'Посещение %s со специальностью %s не уникально.\nИ находится в событии: %s за период с %s по %s ответственный %s'% (forceString(date), nameSpeciality, forceString(recordEvents.value('nameEventType')), forceString(recordEvents.value('setDate')), forceString(recordEvents.value('execDate')), forceString(recordEvents.value('namePerson'))), True, self.tblVisits, row)
                            elif  QtGui.qApp.isCheckDoubleVisitsEnteredBySpeciality()==2:
                                result = result and self.checkValueMessage(u'Посещение %s со специальностью %s не уникально.\nИ находится в событии: %s за период с %s по %s ответственный %s'% (forceString(date), nameSpeciality, forceString(recordEvents.value('nameEventType')), forceString(recordEvents.value('setDate')), forceString(recordEvents.value('execDate')), forceString(recordEvents.value('namePerson'))), False, self.tblVisits, row)
                            if not result:
                                return result
        return result


    def checkDoubleVisitsEntered(self, row, record):
        result = True
        eventId  = self.itemId()
        serviceId = forceRef(record.value('service_id'))
        date = forceDate(record.value('date'))
        currentVisitId = forceRef(record.value('id'))
#        eventTypeId = self.eventTypeId
        nameService = u''
        currentVisitIdList = []
        keepVisitParity = getEventKeepVisitParity(self.eventTypeId)
        if serviceId and date and (self.eventSetDateTime.date() <= date) and QtGui.qApp.isCheckDoubleVisitsEnteredByService() in (1, 2):
            db = QtGui.qApp.db
            nameService = forceString(db.translate('rbService', 'id', serviceId, 'code'))
            if not keepVisitParity:
                if currentVisitId:
                    for rowVisits, recordVisits in enumerate(self.modelVisits.items()):
                        visitId = forceRef(recordVisits.value('id'))
                        if forceRef(recordVisits.value('service_id')) == serviceId and forceDate(recordVisits.value('date')) == date and visitId != currentVisitId:
                            if visitId not in currentVisitIdList:
                                currentVisitIdList.append(visitId)
                            if QtGui.qApp.isCheckDoubleVisitsEnteredByService()==1:
                                result = result and self.checkValueMessage(u'Посещение %s с услугой %s не уникально в данном событии'% (forceString(date), nameService), True, self.tblVisits, row, record.indexOf('service_id'))
                            elif QtGui.qApp.isCheckDoubleVisitsEnteredByService()==2:
                                result = result and self.checkValueMessage(u'Посещение %s с услугой %s не уникально в данном событии'% (forceString(date), nameService), False, self.tblVisits, row, record.indexOf('service_id'))
                            if not result:
                                return result
                else:
                    checkQuantity = 0
                    for rowVisits, recordVisits in enumerate(self.modelVisits.items()):
                        if forceRef(recordVisits.value('service_id')) == serviceId and forceDate(recordVisits.value('date')) == date:
                            if checkQuantity > 0:
                                if QtGui.qApp.isCheckDoubleVisitsEnteredByService()==1:
                                    result = result and self.checkValueMessage(u'Посещение %s с услугой %s не уникально в данном событии'% (forceString(date), nameService), True, self.tblVisits, row, record.indexOf('service_id'))
                                elif  QtGui.qApp.isCheckDoubleVisitsEnteredByService()==2:
                                    result = result and self.checkValueMessage(u'Посещение %s с услугой %s не уникально в данном событии'% (forceString(date), nameService), False, self.tblVisits, row, record.indexOf('service_id'))
                                if not result:
                                    return result
                            checkQuantity += 1
            if self.clientId:
                tableEvent = db.table('Event')
                tableVisit = db.table('Visit')
                tableEventType = db.table('EventType')
                tableVrbPersonWithSpeciality = db.table('vrbPersonWithSpeciality')
                cols = [tableVisit['id'],
                        tableVisit['date'],
                        tableVisit['service_id'],
                        tableEventType['name'].alias('nameEventType'),
                        tableEvent['setDate'],
                        tableEvent['execDate'],
                        tableVrbPersonWithSpeciality['name'].alias('namePerson')
                        ]
                table = tableEvent.innerJoin(tableVisit, tableVisit['event_id'].eq(tableEvent['id']))
                table = table.innerJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
                table = table.innerJoin(tableVrbPersonWithSpeciality, tableVrbPersonWithSpeciality['id'].eq(tableEvent['execPerson_id']))
                condEvents = [tableVisit['date'].eq(date),
                              tableVisit['service_id'].eq(serviceId),
                              tableEvent['client_id'].eq(self.clientId),
                              tableEvent['deleted'].eq(0),
                              tableVisit['deleted'].eq(0),
                              tableEventType['deleted'].eq(0)
                             ]
                if eventId:
                    condEvents.append(tableEvent['id'].ne(eventId))
                if currentVisitIdList != []:
                    condEvents.append(tableVisit['id'].notInlist(currentVisitIdList))
                recordListEvents = db.getRecordList(table, cols, condEvents, 'Event.eventType_id')
                visitId = None
                for recordEvents in recordListEvents:
                    if currentVisitId:
                        visitId = forceRef(recordEvents.value('id'))
                        if visitId != currentVisitId:
                            if  QtGui.qApp.isCheckDoubleVisitsEnteredByService()==1:
                                result = result and self.checkValueMessage(u'Посещение %s с услугой %s не уникально.\nИ находится в событии: %s за период с %s по %s ответственный %s'% (forceString(date), nameService, forceString(recordEvents.value('nameEventType')), forceString(recordEvents.value('setDate')), forceString(recordEvents.value('execDate')), forceString(recordEvents.value('namePerson'))), True, self.tblVisits, row, record.indexOf('service_id'))
                            elif QtGui.qApp.isCheckDoubleVisitsEnteredByService()==2:
                                result = result and self.checkValueMessage(u'Посещение %s с услугой %s не уникально.\nИ находится в событии: %s за период с %s по %s ответственный %s'% (forceString(date), nameService, forceString(recordEvents.value('nameEventType')), forceString(recordEvents.value('setDate')), forceString(recordEvents.value('execDate')), forceString(recordEvents.value('namePerson'))), False, self.tblVisits, row, record.indexOf('service_id'))
                            if not result:
                                return result
                    else:
                        if forceRef(recordEvents.value('service_id')) == serviceId and forceDate(recordEvents.value('date')) == date:
                            if  QtGui.qApp.isCheckDoubleVisitsEnteredByService()==1:
                                result = result and self.checkValueMessage(u'Посещение %s с услугой %s не уникально.\nИ находится в событии: %s за период с %s по %s ответственный %s'% (forceString(date), nameService, forceString(recordEvents.value('nameEventType')), forceString(recordEvents.value('setDate')), forceString(recordEvents.value('execDate')), forceString(recordEvents.value('namePerson'))), True, self.tblVisits, row, record.indexOf('service_id'))
                            elif  QtGui.qApp.isCheckDoubleVisitsEnteredByService()==2:
                                result = result and self.checkValueMessage(u'Посещение %s с услугой %s не уникально.\nИ находится в событии: %s за период с %s по %s ответственный %s'% (forceString(date), nameService, forceString(recordEvents.value('nameEventType')), forceString(recordEvents.value('setDate')), forceString(recordEvents.value('execDate')), forceString(recordEvents.value('namePerson'))), False, self.tblVisits, row, record.indexOf('service_id'))
                            if not result:
                                return result
        return result


    def checkResultEvent(self, resultId, endDate, widget):
        result = True
        if resultId and endDate:
            db = QtGui.qApp.db
            table = db.table('rbResult')
            cond = [table['id'].eq(resultId)]
            cond.append(db.joinOr([db.joinAnd([table['begDate'].isNull(),
                                               table['endDate'].isNull()
                                               ]),
                                   db.joinAnd([table['begDate'].isNotNull(),
                                               table['endDate'].isNotNull(),
                                               table['begDate'].dateLe(endDate),
                                               table['endDate'].dateGe(endDate)
                                               ]),
                                   db.joinAnd([table['begDate'].isNotNull(),
                                               table['endDate'].isNull(),
                                               table['begDate'].dateLe(endDate)
                                                ]),
                                   db.joinAnd([table['endDate'].isNotNull(),
                                               table['begDate'].isNull(),
                                               table['endDate'].dateGe(endDate)
                                               ])
                                               ]))
            record = db.getRecordEx(table, [table['id']], cond)
            if not record:
                self.checkValueMessage(u'Значение результата события устарело', False, widget)
                return False
        return result


# WTF? что такое directionDateF? почему widget где-то в середине?
    def checkEventDate(self, directionDateF, endDateF, nextDateF, widget, widgetNextDateF, widgetEndDateF = None, boolEvent = False, row = None, column = None, enableActionsBeyondEvent = 0):
        directionDate = directionDateF.date() if isinstance(directionDateF, QDateTime) else directionDateF
        endDate = endDateF.date() if isinstance(endDateF, QDateTime) else endDateF
        nextDate = nextDateF.date() if isinstance(nextDateF, QDateTime) else nextDateF
        widgetNextDate = widgetNextDateF.date() if isinstance(widgetNextDateF, QDateTime) else widgetNextDateF
        widgetEndDate = widgetEndDateF.date() if isinstance(widgetEndDateF, QDateTime) else widgetEndDateF
        result = True
        if nextDate and directionDate:
            result = result and (nextDate >= directionDate or self.checkValueMessage(u'Дата следующей явки %s не должна быть раньше даты назначения %s' % (forceString(nextDate), forceString(directionDate)), False, widget, row, column, widgetNextDate))
            result = result and (nextDate != directionDate or self.checkValueMessage(u'Дата следующей явки %s не должна быть равна дате назначения %s' % (forceString(nextDate), forceString(directionDate)), False, widget, row, column, widgetNextDate))
        if nextDate and endDate:
            result = result and (nextDate >= endDate or self.checkValueMessage(u'Дата следующей явки %s не должна быть раньше даты выполнения %s' % (forceString(nextDate), forceString(endDate)), False, widget, row, column, widgetNextDate))
            result = result and (nextDate != endDate or self.checkValueMessage(u'Дата следующей явки %s не должна быть равна дате выполнения %s' % (forceString(nextDate), forceString(endDate)), False, widget, row, column, widgetNextDate))
        directionDate = QDate.currentDate()
        if boolEvent:
            if self.orgId == QtGui.qApp.currentOrgId():
                if endDate and directionDate:
                    result = result and (endDate <= directionDate or self.checkValueMessage(u'Дата выполнения %s не должна быть позже текущей даты %s' % (forceString(endDate), forceString(directionDate)), True, widget, row, column, widgetEndDate))
        else:
            if endDate and directionDate and enableActionsBeyondEvent:
                result = result and (endDate <= directionDate or self.checkValueMessage(u'Дата выполнения %s не должна быть позже текущей даты %s' % (forceString(endDate), forceString(directionDate)), True, widget, row, column, widgetEndDate))
        return result


    def checkActionsEndDate(self, enableUnfinishedActions):
        self.valueForAllActionEndDate = None
        self.res = None
        tabList = self.getActionsTabsList()
        showTime = getEventShowTime(self.eventTypeId)
        if showTime:
            eventEndDate = QDateTime(self.edtEndDate.date(), self.edtEndTime.time())
        else:
            eventEndDate = self.edtEndDate.date()
        for actionTab in tabList:
            model = actionTab.tblAPActions.model()
            for row, (record, action) in enumerate(model.items()):
                if action and action._actionType.id:
#                    actionTypeItem = action.getType()
                    nameActionType = action._actionType.name #название типа действия
                    status = forceInt(record.value('status'))
                    actionShowTime = action._actionType.showTime
                    showTime = getEventShowTime(self.eventTypeId) and actionShowTime
                    forceDateOrDateTime = forceDateTime if actionShowTime else forceDate
                    actionEndDate = forceDateOrDateTime(record.value('endDate'))
                    actionEndDate = actionEndDate if showTime else actionEndDate.date() if isinstance(actionEndDate, QDateTime) else actionEndDate
                    if eventEndDate and not actionEndDate and status == CActionStatus.started and enableUnfinishedActions: # статус: начато
                        if len(nameActionType) > 0:
                            strNameActionType = u': ' + nameActionType
                        if not self.checkActionEndDate(strNameActionType, actionTab.tblAPActions, row, 0, actionTab.edtAPEndDate, enableUnfinishedActions = enableUnfinishedActions, tblAPProps = actionTab.tblAPProps):
                            return False
        self.res = None
        return True


    def checkActionEndDate(self, strNameActionType, tblWidget, row, column, widgetEndDate, enableUnfinishedActions = 1, tblAPProps = None):
        def getDateTime(res):
            if res in [2, 5]:
                return QDateTime(self.edtBegDate.date(), self.edtBegTime.time())
            elif res in [3, 6]:
                return QDateTime(self.edtEndDate.date(), self.edtEndTime.time())
            elif res in [4, 7]:
                return QDateTime.currentDateTime()
            return None

        if self.valueForAllActionEndDate is None:
            buttons = QtGui.QMessageBox.Ok
            if enableUnfinishedActions == 1:
                buttons |= QtGui.QMessageBox.Ignore
            message = u'Должна быть указана дата выполнения действия%s' % (strNameActionType)
            messageBox = CCheckActionEndDateMessageBox(QtGui.QMessageBox.Warning,
                                                       u'Внимание!',
                                                       message,
                                                       buttons,
                                                       self
                                                       )
            messageBox.setDefaultButton(QtGui.QMessageBox.Ok)
            messageBox.setEscapeButton(QtGui.QMessageBox.Ok)
            menu = QtGui.QMenu()
            actionBegin = menu.addAction(u"Закрыть датой начала события")
            actionBegin.triggered.connect(messageBox.on_begin)
            actionOut = menu.addAction(u"Закрыть датой окончания события")
            actionOut.triggered.connect(messageBox.on_out)
            actionCurrent = menu.addAction(u"Закрыть текущей датой")
            actionCurrent.triggered.connect(messageBox.on_current)
            currentDateButton = QtGui.QPushButton(u'Закрыть')
            currentDateButton.setMenu(menu)
            menuAll = QtGui.QMenu()
            actionBeginAll = menuAll.addAction(u"Закрыть датой начала события")
            actionBeginAll.triggered.connect(messageBox.on_beginAll)
            actionOutAll = menuAll.addAction(u"Закрыть датой окончания события")
            actionOutAll.triggered.connect(messageBox.on_outAll)
            actionCurrentAll = menuAll.addAction(u"Закрыть текущей датой")
            actionCurrentAll.triggered.connect(messageBox.on_currentAll)
            currentDateForAllButton = QtGui.QPushButton(u'Закрыть(для всех)')
            currentDateForAllButton.setMenu(menuAll)
            if enableUnfinishedActions == 1:
                ignoreForAllButton = QtGui.QPushButton(u'игнорировать(для всех)')
                messageBox.addButton(ignoreForAllButton, QtGui.QMessageBox.AcceptRole)
            messageBox.addButton(currentDateButton, QtGui.QMessageBox.AcceptRole)
            messageBox.addButton(currentDateForAllButton, QtGui.QMessageBox.AcceptRole)
            res = messageBox.exec_()
            clickedButton = messageBox.clickedButton()
            if res in (QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ignore):
                if res == QtGui.QMessageBox.Ok:
                    model = tblWidget.model()
                    tblWidget.setCurrentIndex(model.index(row, 0))
                    self.setFocusToWidget(widgetEndDate, row, column)
                    return False
                elif res == QtGui.QMessageBox.Ignore:
                    return True
                else:
                    return True

            if not clickedButton and res in [2, 3, 4]:
                dateTimeValue = getDateTime(res)
                if not dateTimeValue:
                    return False
                model = tblWidget.model()
                record, action = model._items[row]
                record.setValue('endDate', QVariant(dateTimeValue))
                record.setValue('status', QVariant(CActionStatus.finished))
                if action:
                    actionTypeId = forceRef(record.value('actionType_id'))
                    if actionTypeId:
                        actionType = CActionTypeCache.getById(actionTypeId)
                        if actionType:
                            showTime = actionType.showTime and getEventShowTime(self.eventTypeId)
                            jobTicketIdList = []
                            for property in action.getType()._propertiesById.itervalues():
                                if property.isJobTicketValueType():
                                    jobTicketId = action[property.name]
                                    if jobTicketId and jobTicketId not in jobTicketIdList:
                                        jobTicketIdList.append(jobTicketId)
                            if jobTicketIdList:
                                endDate = forceDateTime(record.value('endDate')) if showTime else forceDate(record.value('endDate'))
                                db = QtGui.qApp.db
                                tableJobTicket = db.table('Job_Ticket')
                                cond = [tableJobTicket['id'].eq(jobTicketId),
                                        tableJobTicket['deleted'].eq(0)
                                        ]
                                if showTime:
                                    cond.append(tableJobTicket['datetime'].ge(endDate))
                                else:
                                    cond.append(tableJobTicket['datetime'].dateGe(endDate))
                                records = db.getRecordList(tableJobTicket, '*', cond)
                                for recordJT in records:
                                    datetime = forceDateTime(recordJT.value('datetime')) if showTime else forceDate(recordJT.value('datetime'))
                                    if datetime > endDate:
                                        action[property.name] = None
                                if tblAPProps:
                                    tblAPProps.model().reset()
                            model.reset()
                return True
            elif not clickedButton and res in [5, 6, 7]:
                self.valueForAllActionEndDate = True
                self.res = res
            elif clickedButton == ignoreForAllButton:
                self.valueForAllActionEndDate = False
            else:
                return True

        if self.valueForAllActionEndDate == True:
            dateTimeValue = getDateTime(self.res)
            if not dateTimeValue:
                return False
            model = tblWidget.model()
            record, action = model._items[row]
            record.setValue('endDate', QVariant(dateTimeValue))
            record.setValue('status', QVariant(CActionStatus.finished))
            if action:
                actionTypeId = forceRef(record.value('actionType_id'))
                if actionTypeId:
                    actionType = CActionTypeCache.getById(actionTypeId)
                    if actionType:
                        showTime = actionType.showTime and getEventShowTime(self.eventTypeId)
                        jobTicketIdList = []
                        for property in action.getType()._propertiesById.itervalues():
                            if property.isJobTicketValueType():
                                jobTicketId = action[property.name]
                                if jobTicketId and jobTicketId not in jobTicketIdList:
                                    jobTicketIdList.append(jobTicketId)
                        if jobTicketIdList:
                            endDate = forceDateTime(record.value('endDate')) if showTime else forceDate(record.value('endDate'))
                            db = QtGui.qApp.db
                            tableJobTicket = db.table('Job_Ticket')
                            cond = [tableJobTicket['id'].eq(jobTicketId),
                                    tableJobTicket['deleted'].eq(0)
                                    ]
                            if showTime:
                                cond.append(tableJobTicket['datetime'].ge(endDate))
                            else:
                                cond.append(tableJobTicket['datetime'].dateGe(endDate))
                            records = db.getRecordList(tableJobTicket, '*', cond)
                            for recordJT in records:
                                datetime = forceDateTime(recordJT.value('datetime')) if showTime else forceDate(recordJT.value('datetime'))
                                if datetime > endDate:
                                    action[property.name] = None
                            if tblAPProps:
                                tblAPProps.model().reset()
                        model.reset()
            return True
        elif self.valueForAllActionEndDate == False:
            return True
        else:
            return True


    def checkOpenActions(self, enableUnfinishedActions):
        # --- проверяем на заполнение поле даты выбытия
        execDate = self.edtEndDate.date()
        if execDate:
            # --- считаем пустые поля Дата завершения
            counter = 0
            tabList = self.getActionsTabsList()
            for actionTab in tabList:
                model = actionTab.tblAPActions.model()
                for row, (record, action) in enumerate(model.items()):
                    actionType = CActionTypeCache.getById(forceRef(record.value('actionType_id')))
                    status = forceInt(record.value('status'))
                    if not forceDate(record.value('endDate')) and not (actionType.isNomenclatureExpense and status in (CActionStatus.started, CActionStatus.appointed)):
                        if status not in [CActionStatus.canceled, CActionStatus.refused]: # не отменено, не отказ
                            counter += 1
            # --- если пустых полей нет - выходим
            if counter == 0:
                return True
            # --- пустые поля есть - спрашиваем что делать
            message = u'Есть незавершенные действия в событии'
            messageBox = CCheckActionEndDateMessageBox(QtGui.QMessageBox.Warning,
                                                       u'Внимание!',
                                                       message,
                                                       QtGui.QMessageBox.Cancel,
                                                       self
                                                       )
            messageBox.setDefaultButton(QtGui.QMessageBox.Ok)
            messageBox.setEscapeButton(QtGui.QMessageBox.Ok)
            menu = QtGui.QMenu()
            actionBegin = menu.addAction(u"Закрыть датой начала события")
            actionBegin.triggered.connect(messageBox.on_begin)
            actionOut = menu.addAction(u"Закрыть датой окончания события")
            actionOut.triggered.connect(messageBox.on_out)
            actionCurrent = menu.addAction(u"Закрыть текущей датой")
            actionCurrent.triggered.connect(messageBox.on_current)
            btnClose = QtGui.QPushButton(u"Закрыть")
            btnClose.setMenu(menu)
            messageBox.addButton(btnClose, QtGui.QMessageBox.AcceptRole)
            if enableUnfinishedActions == 1:
                messageBox.addButton(QtGui.QMessageBox.Ignore)
                btnCheck = QtGui.QPushButton(u'Проверить')
                messageBox.addButton(btnCheck, QtGui.QMessageBox.AcceptRole)
            res = messageBox.exec_()
            clickedButton = messageBox.clickedButton()
            if enableUnfinishedActions == 1 and clickedButton == btnCheck:
                self.primaryEntranceCheck = False
                return self.checkActionsEndDate(enableUnfinishedActions)
            elif res in (QtGui.QMessageBox.RejectRole, QtGui.QMessageBox.Cancel):
                return False
            elif  res == QtGui.QMessageBox.Ignore:
                return True
            # --- перебираем пустые поля с закрытием, исходя из выбора оператора
            for actionTab in tabList:
                model = actionTab.tblAPActions.model()
                for row, (record, action) in enumerate(model.items()):
                    actionType = CActionTypeCache.getById(forceRef(record.value('actionType_id')))
                    status = forceInt(record.value('status'))
                    if not forceDate(record.value('endDate')) and not (actionType.isNomenclatureExpense and status in (CActionStatus.started, CActionStatus.appointed)):
                        date = QDate()
                        if res == 2:
                            eventDate = self.edtBegDate.date()
                            eventTime = self.edtBegTime.time()
                        elif res == 3:
                            eventDate = self.edtEndDate.date()
                            eventTime = self.edtEndTime.time()
                        elif res == 4:
                            currentDateTime = QDateTime.currentDateTime()
                            eventDate = currentDateTime.date()
                            eventTime = currentDateTime.time()
                        else:
                            currentDateTime = QDateTime.currentDateTime()
                            eventDate = currentDateTime.date()
                            eventTime = currentDateTime.time()
                        date = eventDate
                        status = forceInt(record.value('status'))
                        if status not in [CActionStatus.canceled, CActionStatus.refused]:  # не отменено, не отказ
                            actionTypeId = forceRef(record.value('actionType_id'))
                            if actionTypeId:
                                actionType = CActionTypeCache.getById(actionTypeId)
                                if actionType:
                                    showTime = actionType.showTime and getEventShowTime(self.eventTypeId)
                                    if showTime:
                                        date = QDateTime(eventDate, eventTime)
                                    record.setValue('endDate', toVariant(date))
                                    record.setValue('status', toVariant(CActionStatus.finished))
                                    if action:
                                        jobTicketIdList = []
                                        for property in action.getType()._propertiesById.itervalues():
                                            if property.isJobTicketValueType():
                                                jobTicketId = action[property.name]
                                                if jobTicketId and jobTicketId not in jobTicketIdList:
                                                    jobTicketIdList.append(jobTicketId)
                                        if jobTicketIdList:
                                            endDate = forceDateTime(record.value('endDate')) if showTime else forceDate(record.value('endDate'))
                                            db = QtGui.qApp.db
                                            tableJobTicket = db.table('Job_Ticket')
                                            cond = [tableJobTicket['id'].eq(jobTicketId),
                                                    tableJobTicket['deleted'].eq(0)
                                                    ]
                                            if showTime:
                                                cond.append(tableJobTicket['datetime'].ge(endDate))
                                            else:
                                                cond.append(tableJobTicket['datetime'].dateGe(endDate))
                                            records = db.getRecordList(tableJobTicket, '*', cond)
                                            for recordJT in records:
                                                datetime = forceDateTime(recordJT.value('datetime')) if showTime else forceDate(recordJT.value('datetime'))
                                                if datetime > endDate:
                                                    action[property.name] = None
                                            actionTab.tblAPProps.model().reset()
                            model.reset()
            return True
        return True


    def checkActionsDataEntered(self, eventDirectionDate, eventEndDate):
        eventId = self.itemId()
        self.actionTypeDepositIdList = []
        tabList = self.getActionsTabsList()
        actionsBeyondEvent = getEventEnableActionsBeyondEvent(self.eventTypeId)
        if hasattr(self, 'hasReferralLisLab'):
            del self.hasReferralLisLab
        for actionTab in tabList:
            model = actionTab.tblAPActions.model()
            for row, (record, action) in enumerate(model.items()):
                if action and action._actionType.id:
                    if action._actionType.id not in self.actionTypeDepositIdList:
                        self.actionTypeDepositIdList.append(action._actionType.id)
                    actionTypeItem = action.getType()
                    nameActionType = action._actionType.name #название типа действия
                    status = forceInt(record.value('status'))
                    actionShowTime = action._actionType.showTime
                    forceDateOrDateTime = forceDateTime if actionShowTime else forceDate
                    directionDate = forceDateOrDateTime(record.value('directionDate'))
                    begDate = forceDateOrDateTime(record.value('begDate'))
                    endDate = forceDateOrDateTime(record.value('endDate'))
                    
                    if actionTypeItem and actionTypeItem.flatCode == u'referralLisLab':
                        self.hasReferralLisLab = True

                    # проверка заполнения МКБ в действии Поступление (по ОМС) для КК
                    if QtGui.qApp.provinceKLADR()[:2] == u'23' and u'received' in actionTypeItem.flatCode.lower():
                        checkMKBreceivedOMS = QtGui.qApp.getStrictCheckMKBreceivedOMS()
                        if checkMKBreceivedOMS:
                            if self.eventFinanceId == CFinanceType.CMI and not forceString(
                                    record.value('MKB')) and not self.checkValueMessage(
                                    u'Для действия Поступление не указан код МКБ.', checkMKBreceivedOMS == 1,
                                    actionTab.tblAPActions, row, 0, actionTab.cmbAPMKB):
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

                    # # Проверка наличия регионального кода для ЛР в КК
                    # if actionTypeItem and actionTypeItem.context.lower() == u'recipe' and QtGui.qApp.defaultKLADR()[:2] == u'23':
                    #     personId = forceRef(record.value('person_id'))
                    #     if not personId:
                    #         self.checkInputMessage(u'Исполнителя', False, actionTab.tblAPActions, row, 0)
                    #         return False
                    #     else:
                    #         personCode = forceStringEx(QtGui.qApp.db.translate('Person', 'id', personId, 'regionalCode'))
                    #         if not personCode:
                    #             self.checkValueMessage(u'Дальнейшее сохранение рецепта невозможно.\nОтсутствует региональный код врача, выписавшего рецепт', False, actionTab.tblAPActions, row, 0, actionTab.cmbAPPerson)
                    #             return False

                    actionId = forceRef(record.value('id'))
                    if not self.checkBegDateAction(row, record, action, actionTab.tblAPActions, actionTab.edtAPBegDate):
                        return False
                    if not self.checkActionMKB(row, record, action,
                                                      actionTab.tblAPActions, actionTab.cmbAPMKB):
                        return False
                    if not self.checkSetPerson(row, record, action, actionTab.tblAPActions, actionTab.cmbAPSetPerson):
                        return False
                    if not self.checkExecPerson(row, record, action,
                                                      actionTab.tblAPActions, actionTab.cmbAPPerson):
                        return False
                    if actionTypeItem and (u'received' in actionTypeItem.flatCode.lower()
                                           or u'moving' in actionTypeItem.flatCode.lower()
                                           or u'leaved' in actionTypeItem.flatCode.lower()):
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
                        self.getActionList(tabList, actionTypeItem)
                        return False
                    if not self.checkExistsActionsForCurrentDay(row, record, action, actionTab):
                        self.getActionList(tabList, actionTypeItem)
                        return False
                    if not self.checkActionMorphology(row, record, action,
                                                      actionTab.tblAPActions, actionTab.cmbAPMorphologyMKB):
                        return False
                    if not self.checkPlannedEndDate(row, record, action,
                                                      actionTab.tblAPActions, actionTab.edtAPPlannedEndDate):
                        return False
        return True


    def checkBegDateAction(self, row, record, action, widget, widgetBegDate, column=0):
        isControlActionBegDate = QtGui.qApp.isControlActionBegDate()
        if isControlActionBegDate and action and record:
            actionType = action.getType()
            if actionType:
                begDate = forceDate(record.value('begDate'))
                return bool(begDate or self.checkValueMessage(u'Отсутствует Дата начала действия "%s"! Исправить?'%(actionType.name), True if isControlActionBegDate == 1 else False, widget, row, column, 0, widgetBegDate))
        return True


    def checkPlannedEndDate(self, row, record, action, tblAPActions, edtAPPlannedEndDate, column=0):
        if action:
            actionType = action.getType()
            if actionType and actionType.isPlannedEndDateRequired in [CActionType.dpedControlMild, CActionType.dpedControlHard]:
                if not forceDate(record.value('plannedEndDate')):
                    skippable = True if actionType.isPlannedEndDateRequired == CActionType.dpedControlMild else False
                    message = u'Необходимо указать Плановую дату выполнения у действия %s'%(actionType.name)
                    return self.checkValueMessage(message, skippable, tblAPActions, row, column, 0, edtAPPlannedEndDate)
        return True


    def checkPrintByTemplateAllowed(self, templateId):
        '''
        Проверяет параметр шаблона печати "Требует идентификатор события" (rbPrintTemplate.needEventId)
        Mantis 0016238
        :param templateId: id проверяемого ШП (int)
        :return: bool
        '''
        eventId = self.itemId()
        if not eventId:
            db = QtGui.qApp.db
            printNotAllowed = forceBool(db.translate('rbPrintTemplate', 'id', templateId, 'needEventId'))
            if printNotAllowed:
                messageBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning, u'Внимание!',
                                               u'Требуется сохранить случай обслуживания до формирования печатной формы документа! Для сохранения без закрытия редактора нажмите кнопку "Применить".',
                                               QtGui.QMessageBox.Ok)
                messageBox.setWindowFlags(messageBox.windowFlags() | Qt.WindowStaysOnTopHint)
                messageBox.exec_()
                return False
        return True


    def checkLeavedEndDate(self, eventEndDate, row, action, widget, widgetEndDate):
        result = True
        if action:
            actionType = action.getType()
            if actionType and actionType.defaultEndDate == CActionType.dedEventExecDate:
                record = action.getRecord()
                actionEndDate = forceDateTime(record.value('endDate'))
                showTime = getEventShowTime(self.eventTypeId) and actionType.showTime
                eventEndDate = eventEndDate if showTime else eventEndDate.date() if isinstance(eventEndDate, QDateTime) else eventEndDate
                eventEndDateToCompare = self._date2StringToCompare(eventEndDate)
                actionEndDate = actionEndDate if showTime else actionEndDate.date() if isinstance(actionEndDate, QDateTime) else actionEndDate
                actionEndDateToCompare = self._date2StringToCompare(actionEndDate)
                result = result and (actionEndDateToCompare == eventEndDateToCompare or self.checkValueMessage(u'Дата выполнения действия Выписка %s не соотвествует дате выполнения события %s' % (forceString(actionEndDate), forceString(eventEndDate)), True, widget, row, 0, widgetEndDate))
        return result


    def getActionList(self, tabList, actionTypeItem):
        if actionTypeItem and (u'received' in actionTypeItem.flatCode.lower()
                               or u'moving' in actionTypeItem.flatCode.lower()
                               or u'leaved' in actionTypeItem.flatCode.lower()):
            self.checkPeriodActionsDialog(tabList)


    def checkPeriodActionsDialog(self, tabList):
        dialog = CCheckPeriodActionsForEvent(self, tabList, self.itemId(), self.prevEventId)
        try:
            if dialog.exec_():
                pass
        finally:
            dialog.deleteLater()


    def checkAddOutsideActionsDataEntered(self, eventBegDate, eventEndDate, actionList):
        eventId = self.itemId()
        actionsBeyondEvent = getEventEnableActionsBeyondEvent(self.eventTypeId)
        for record, action in actionList:
            if action and action._actionType.id:
                actionTypeItem = action.getType()
                nameActionType = action._actionType.name
                status = forceInt(record.value('status'))
                actionShowTime = action._actionType.showTime
                forceDateOrDateTime = forceDateTime if actionShowTime else forceDate
                directionDate = forceDateOrDateTime(record.value('directionDate'))
                begDate = forceDateOrDateTime(record.value('begDate'))
                endDate = forceDateOrDateTime(record.value('endDate'))
                if not self.checkActionDataEntered(directionDate, begDate, endDate, None, None, None, None, None, None):
                    return False
                if not self.checkEventDate(directionDate, endDate, None, None, None, None, False, None, None, enableActionsBeyondEvent=actionsBeyondEvent):
                    return False
                if not self.checkEventActionDateEntered(eventBegDate, eventEndDate, status, directionDate, begDate, endDate, None, None, None, None, None, nameActionType, actionShowTime=actionShowTime, enableActionsBeyondEvent=actionsBeyondEvent):
                    return False
#                if not self.checkActionProperties(None, action, None, None):
#                    return False
                if not self.checkExistsActionsForCurrentDay(None, record, action, None):
                    return False
                if not self.checkActionMorphology(None, record, action, None, None):
                    return False
                if not self.checkActionMKB(None,record,action,None,None):
                    return False
                if not self.checkExecPerson(None,record,action,None,None):
                    return False
                if not self.checkPlannedEndDate(None, record, action, None, None):
                    return False
        tabList = self.getActionsTabsList()
        for actionTab in tabList:
            model = actionTab.tblAPActions.model()
            for row, (record, action) in enumerate(model.items()):
                if action and action._actionType.id:
                    actionTypeItem = action.getType()
                    actionId = forceRef(record.value('id'))
                    if actionTypeItem and (u'received' in actionTypeItem.flatCode.lower()
                                           or u'moving' in actionTypeItem.flatCode.lower()
                                           or u'leaved' in actionTypeItem.flatCode.lower()):
                        begDateTime = forceDateTime(record.value('begDate'))
                        endDateTime = forceDateTime(record.value('endDate'))
                        if  eventEndDate and u'received' in actionTypeItem.flatCode.lower():
                            isControlActionReceivedBegDate = QtGui.qApp.isControlActionReceivedBegDate()
                            if isControlActionReceivedBegDate:
                                showTime = getEventShowTime(self.eventTypeId) and action._actionType.showTime
                                setDate = toDateTimeWithoutSeconds(eventBegDate if showTime else (eventBegDate.date() if isinstance(eventBegDate, QDateTime) else eventBegDate))
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
                        if not self.checkDateActionsMoving(model, begDateTime, endDateTime, None, row, 0, None):
                            return False
                        if u'moving' in actionTypeItem.flatCode.lower():
                            for i in xrange(len(action._properties)):
                                if action._properties[i]._type.typeName.lower() == (u'HospitalBed').lower():
                                    if not self.checkMovingBeds(self.clientId, eventId, actionId, forceDateTime(action._record.value('begDate')), forceDateTime(action._record.value('endDate')), None, None, None, None):
                                        return False
        return True


    def checkActionMorphology(self, row, record, action, tblAPActions, cmbAPMorphologyMKB):
        status = forceInt(record.value('status'))
        if QtGui.qApp.defaultMorphologyMKBIsVisible() and (status in (2, 4)):
            actionTypeItem = action.getType()
            defaultMKB = actionTypeItem.defaultMKB
            isMorphologyRequired = actionTypeItem.isMorphologyRequired
            morphologyMKB = forceString(record.value('morphologyMKB'))
            if cmbAPMorphologyMKB and not cmbAPMorphologyMKB.isValid(morphologyMKB) and defaultMKB > 0 and isMorphologyRequired > 0:
                if status == 4 and isMorphologyRequired == 2:
                    return True
                skippable = True if isMorphologyRequired == 1 else False
                message = u'Необходимо ввести корректную морфологию диагноза действия `%s`' % actionTypeItem.name
                return self.checkValueMessage(message, skippable, tblAPActions, row, 0, cmbAPMorphologyMKB)
        return True

    
    def checkActionMKB(self, row, record, action, tblAPActions, cmbMKB):
        status = forceInt(record.value('status'))
        if (status in (0, 1, 2, 4, 5)):
            actionTypeItem = action.getType()
            isMKBRequired = actionTypeItem.isMKBRequired
            MKB = forceString(record.value('MKB'))
            if MKB == '' and isMKBRequired > 0:
                if status == 4 and isMKBRequired == 2:
                    return True
                skippable = True if isMKBRequired == 1 else False
                message = u'Необходимо ввести корректное МКБ действия `%s`' % actionTypeItem.name
                return self.checkValueMessage(message, skippable, tblAPActions, row, 0, cmbMKB)
        return True
    
    
    def checkExecPerson(self, row, record, action, tblAPActions, cmbAPPerson):
        status = forceInt(record.value('status'))
        if (status in (0, 1, 2, 4, 5)):
            actionTypeItem = action.getType()
            ExecPerson = forceString(record.value('person_id'))
            
            if actionTypeItem:
                specIdList = []
                for item in actionTypeItem.getPFSpecialityRecordList():
                    specIdList.append(forceRef(item.value('speciality_id')))
                orgStructIdList = []
                for item in actionTypeItem.getPFOrgStructureRecordList():
                    orgStruct = forceInt(item.value('orgStructure_id'))
                    orgStructIdList.append(orgStruct)
                    for orgStructDescendant in getOrgStructureDescendants(orgStruct):
                        orgStructIdList.append(orgStructDescendant)
                db = QtGui.qApp.db
                personRecord = db.getRecord('Person', 'speciality_id, orgStructure_id', ExecPerson)
                if personRecord:
                    if (specIdList and forceInt(personRecord.value('speciality_id')) not in specIdList) or \
                        (orgStructIdList and forceInt(personRecord.value('orgStructure_id')) not in orgStructIdList):
                            record.setValue('person_id', None)
            
            isExecPersonRequired = actionTypeItem.isExecPersonRequired
            if not ExecPerson and isExecPersonRequired > 0:
                if status == 4 and isExecPersonRequired == 2:
                    return True
                skippable = True if isExecPersonRequired == 1 else False
                message = u'Необходимо указать корректного исполнителя действия `%s`' % actionTypeItem.name
                return self.checkValueMessage(message, skippable, tblAPActions, row, 0, cmbAPPerson)
        return True


    def checkSetPerson(self, row, record, action, tblAPActions, cmbAPSetPerson):
        setPerson = forceRef(record.value('setPerson_id'))
        if not setPerson:
            actionTypeItem = action.getType()
            if actionTypeItem and actionTypeItem.defaultSetPersonInEvent != CActionType.dspUndefined:
                message = u'Необходимо указать назначившего действия `%s`' % actionTypeItem.name
                return self.checkValueMessage(message, False, tblAPActions, row, 0, cmbAPSetPerson)
        return True
    

    def checkExistsActionsForCurrentDay(self, row, record, action, actionTab):
        return True


    def checkDateActionsMoving(self, model, begDateAction, endDateAction, widget, rowAction, column, widgetBegDate):
        begDateActionToCompare = self._date2StringToCompare(begDateAction)
        endDateActionToCompare = self._date2StringToCompare(endDateAction)
        if begDateActionToCompare and endDateActionToCompare and begDateActionToCompare > endDateActionToCompare:
            return self.checkValueMessage(u'Дата начала %s не может быть больше даты окончания %s' % (forceString(begDateAction), forceString(endDateAction)), False, widget, rowAction, column, widgetBegDate)

        for row, (record, action) in enumerate(model.items()):
            if action and action._actionType.id:
                actionTypeItem = action.getType()
                if actionTypeItem and (u'received' in actionTypeItem.flatCode.lower()
                                        or u'moving' in actionTypeItem.flatCode.lower()
                                        or u'leaved' in actionTypeItem.flatCode.lower()) and row != rowAction:
                    begDate = forceDateTime(record.value('begDate'))
                    endDate = forceDateTime(record.value('endDate'))

                    begDateToCompare = self._date2StringToCompare(begDate)
                    endDateToCompare = self._date2StringToCompare(endDate)

                    emptyOneActionDates = not ((begDateActionToCompare or endDateActionToCompare) and (begDateToCompare or endDateToCompare))
                    if emptyOneActionDates or (endDateActionToCompare > begDateToCompare and endDateToCompare > begDateActionToCompare):


#                    if (not begDateAction and not endDateAction) or (not begDate and not endDate) or (begDateAction and ((not begDate) or begDateAction >= begDate) and ((not endDate) or begDateAction < endDate)) or (endDateAction and begDate and (endDateAction > begDate) and ((not endDate) or endDateAction <= endDate)) or (begDateAction and ((not begDate) or begDateAction <= begDate) and (((not endDateAction) and (not endDate)) or (endDateAction and endDate and endDateAction >= endDate and endDate > begDateAction))):
                        return self.checkValueMessage(u'Попытка ввести период (%s - %s) пересекающийся с уже имеющимся (%s - %s)' % (forceString(begDateAction), forceString(endDateAction), forceString(begDate), forceString(endDate)), False, widget, rowAction, column, widgetBegDate)
        return True


    def checkMovingBeds(self, clientId, eventId, actionId, begDate, endDate, widget, rowAction, column, widgetBegDate):
        records = []
        db = QtGui.qApp.db
        tableAPHB = db.table('ActionProperty_HospitalBed')
        tableAPT = db.table('ActionPropertyType')
        tableAP = db.table('ActionProperty')
        tableActionType = db.table('ActionType')
        tableAction = db.table('Action')
        tableEvent = db.table('Event')
        tableClient = db.table('Client')
        tableOSHB = db.table('OrgStructure_HospitalBed')
        tableOS = db.table('OrgStructure')

        cond = [ tableActionType['flatCode'].like(u'moving%'),
                 tableAction['deleted'].eq(0),
                 tableEvent['deleted'].eq(0),
                 tableAP['deleted'].eq(0),
                 tableActionType['deleted'].eq(0),
                 tableOS['deleted'].eq(0),
                 tableClient['deleted'].eq(0),
                 tableAPT['deleted'].eq(0),
                 tableAPT['typeName'].like('HospitalBed'),
                 tableAP['action_id'].eq(tableAction['id']),
                 tableAction['status'].notInlist([CActionStatus.canceled, CActionStatus.refused])
               ]
        if begDate and endDate:
            whereDate = db.joinOr([db.joinAnd([tableAction['begDate'].ge(begDate),
                                               tableAction['begDate'].lt(endDate)]),
                                   db.joinAnd([tableAction['endDate'].gt(begDate),
                                               tableAction['endDate'].le(endDate)]),
                                   db.joinAnd([tableAction['begDate'].le(begDate),
                                               tableAction['endDate'].ge(endDate)])
                                   ]
                                 )
        elif not endDate and begDate:
            whereDate = db.joinOr([db.joinAnd([tableAction['begDate'].isNull(), tableAction['endDate'].isNull()]),
                        db.joinAnd([tableAction['begDate'].isNotNull(),
                        db.joinOr([tableAction['begDate'].ge(begDate),
                        db.joinAnd([tableAction['begDate'].lt(begDate),
                        db.joinOr([tableAction['endDate'].isNull(), tableAction['endDate'].gt(begDate)])])])]),
                        db.joinAnd([tableAction['begDate'].isNull(), tableAction['endDate'].isNotNull(), tableAction['endDate'].gt(begDate)])
                        ])
        elif endDate and not begDate:
            whereDate = db.joinOr([db.joinAnd([tableAction['begDate'].isNull(), tableAction['endDate'].isNull()]),
                        db.joinAnd([tableAction['begDate'].isNotNull(), tableAction['begDate'].lt(endDate)]),
                        tableAction['begDate'].isNull()])
        else:
            whereDate = u''
        if len(whereDate) > 0:
            cond.append(whereDate)
        eventClientId = None
        if actionId:
            cond.append(tableAction['id'].ne(actionId))
            if not eventId:
                queryTableParams = tableAction.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
                recordEvent = db.getRecordEx(queryTableParams, [tableEvent['client_id'], tableEvent['id']], [tableAction['id'].eq(actionId), tableEvent['deleted'].eq(0), tableAction['deleted'].eq(0)])
                eventId = forceRef(recordEvent.value('id'))
                eventClientId = forceRef(recordEvent.value('client_id'))
        if eventId and not eventClientId:
            recordEvent = db.getRecordEx(tableEvent, [tableEvent['client_id']], [tableEvent['id'].eq(eventId), tableEvent['deleted'].eq(0)])
            clientId = forceRef(recordEvent.value(0))
        elif eventId and eventClientId:
            clientId = eventClientId
        if eventId:
            cond.append(tableEvent['id'].ne(eventId))
        if not clientId:
            clientId = self.clientId
        if clientId:
            cond.append(tableEvent['client_id'].eq(clientId))
            queryTable = tableActionType.innerJoin(tableAction, tableActionType['id'].eq(tableAction['actionType_id']))
            queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
            queryTable = queryTable.innerJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
            queryTable = queryTable.innerJoin(tableAP, tableAP['type_id'].eq(tableAPT['id']))
            queryTable = queryTable.innerJoin(tableAPHB, tableAPHB['id'].eq(tableAP['id']))
            queryTable = queryTable.innerJoin(tableOSHB, tableOSHB['id'].eq(tableAPHB['value']))
            queryTable = queryTable.innerJoin(tableOS, tableOS['id'].eq(tableOSHB['master_id']))
            records = db.getRecordList(queryTable, [tableAction['id'], tableEvent['client_id']], cond)
        if len(records) > 0:
            return self.checkValueMessage(u'Пациент уже занимает койку в этом периоде', False, widget, rowAction, column, widgetBegDate)
        return True

    # Это сделано так как в случае с QDateTime сравниваются и секунды и милисекунды, на что мы
    # в редакторе ни как повлиять не можем.
    def _date2StringToCompare(self, date):
        if isinstance(date, QDate):
            return unicode(date.toString('yyyy.MM.dd'))
        if isinstance(date, QDateTime):
            return unicode(date.toString('yyyy.MM.dd HH:mm'))


    def checkEventActionDateEntered(self, eventDirectionDate, eventEndDate, status, actionDirectionDate, actionBegDate, actionEndDate, widget, widgetEndDate = None, widgetBegDate = None, row = None, column = None, nameActionType = u'', actionShowTime=False, enableActionsBeyondEvent=0):
        showTime = getEventShowTime(self.eventTypeId) and actionShowTime
        actionDirectionDate = forceDate(actionDirectionDate)
        actionBegDate = actionBegDate if showTime else actionBegDate.date() if isinstance(actionBegDate, QDateTime) else actionBegDate
        actionEndDate = actionEndDate if showTime else actionEndDate.date() if isinstance(actionEndDate, QDateTime) else actionEndDate
        eventDirectionDate = eventDirectionDate if showTime else eventDirectionDate.date() if isinstance(eventDirectionDate, QDateTime) else eventDirectionDate
        eventEndDate = eventEndDate if showTime else eventEndDate.date() if isinstance(eventEndDate, QDateTime) else eventEndDate
        actionBegDateToCompare = self._date2StringToCompare(actionBegDate)
        actionEndDateToCompare = self._date2StringToCompare(actionEndDate)
        eventDirectionDateToCompare = self._date2StringToCompare(eventDirectionDate)
        eventEndDateToCompare = self._date2StringToCompare(eventEndDate)
        result = True
        if eventDirectionDate and actionDirectionDate:
            if actionBegDate:
                result = result and (actionBegDateToCompare >= eventDirectionDateToCompare or self.checkValueMessage(u'Дата начала действия %s не должна быть раньше даты назначения события %s' % (forceString(actionBegDate), forceString(eventDirectionDate)), True, widget, row, column, widgetBegDate))
            if actionEndDate:
                result = result and (actionEndDateToCompare >= eventDirectionDateToCompare or self.checkValueMessage(u'Дата выполнения действия %s не должна быть раньше даты назначения события %s' % (forceString(actionEndDate), forceString(eventDirectionDate)), True, widget, row, column, widgetEndDate))
        if eventEndDateToCompare:
            if actionBegDate and enableActionsBeyondEvent:
                result = result and (actionBegDateToCompare <= eventEndDateToCompare or self.checkValueMessage(u'Дата начала действия %s не должна быть позже даты выполнения события %s' % (forceString(actionBegDate), forceString(eventEndDate)), True if enableActionsBeyondEvent == 1 else False, widget, row, column, widgetBegDate))
            if actionEndDate and enableActionsBeyondEvent:
                result = result and (actionEndDateToCompare <= eventEndDateToCompare or self.checkValueMessage(u'Дата выполнения действия %s не должна быть позже даты выполнения события %s' % (forceString(actionEndDate), forceString(eventEndDate)), True if enableActionsBeyondEvent == 1 else False, widget, row, column, widgetEndDate))
        if eventEndDateToCompare and (actionEndDate and actionEndDateToCompare >= eventDirectionDateToCompare and (not eventEndDate or eventEndDateToCompare >= actionEndDateToCompare)) and actionBegDate:
            result = result and (actionBegDateToCompare >= eventDirectionDateToCompare or self.checkValueMessage(u'Дата начала действия %s не должна быть раньше даты начала события %s' % (forceString(actionBegDate), forceString(eventDirectionDate)), True, widget, row, column, widgetBegDate))
        return result


    def checkActionDataEntered(self, directionDate, begDate, endDate, widget, widgetDirectionDate = None, widgetBegDate = None, widgetEndDate = None, row = None, column = None):
        showTime = getEventShowTime(self.eventTypeId)
        begDateToCompare = self._date2StringToCompare(begDate if showTime else begDate.date() if isinstance(begDate, QDateTime) else begDate)
        begDateToCompareWithDeath = self._date2StringToCompare(begDate.date() if isinstance(begDate, QDateTime) else begDate)
        endDateToCompare = self._date2StringToCompare(endDate if showTime else endDate.date() if isinstance(endDate, QDateTime) else endDate)
        endDateToCompareWithDeath = self._date2StringToCompare(endDate.date() if isinstance(endDate, QDateTime) else endDate)
        directionDateToCompare = self._date2StringToCompare(directionDate if showTime else directionDate.date() if isinstance(directionDate, QDateTime) else directionDate)
        directionDateToCompareWithDeath = self._date2StringToCompare(directionDate.date() if isinstance(directionDate, QDateTime) else directionDate)
        clientDeathDateToCompare = self._date2StringToCompare(self.clientDeathDate) if self.clientDeathDate else ''
        result = True
        possibleDeathDate = QDateTime()
        if self.clientBirthDate:
            possibleDeathDate = QDateTime(self.clientBirthDate.addYears(QtGui.qApp.maxLifeDuration), QTime())
            possibleDeathDateToCompare = self._date2StringToCompare(possibleDeathDate)
            clientBirthDateToCompare = self._date2StringToCompare(self.clientBirthDate)
        if endDate:
            if directionDate:
                result = result and (endDateToCompare >= directionDateToCompare or self.checkValueMessage(u'Дата выполнения (окончания) %s не может быть раньше даты назначения %s' % (forceString(endDate), forceString(directionDate)), False, widget, row, column, widgetEndDate))
            if begDate:
                result = result and (endDateToCompare >= begDateToCompare or self.checkValueMessage(u'Дата выполнения (окончания) %s не может быть раньше даты начала %s' % (forceString(endDate), forceString(begDate)), False, widget, row, column, widgetEndDate))
            if self.clientBirthDate:
                result = result and (endDateToCompare >= clientBirthDateToCompare or self.checkValueMessage(u'Дата выполнения (окончания) %s не может быть раньше даты рождения пациента %s' % (forceString(endDate), forceString(self.clientBirthDate)), False, widget, row, column, widgetEndDate))
            # if self.clientDeathDate:
            #     result = result and (endDateToCompareWithDeath <= clientDeathDateToCompare or self.eventPurposeId == 6 or self.checkValueMessage(u'Дата выполнения (окончания) %s не может быть позже имеющейся даты смерти пациента %s' % (forceString(endDate), forceString(self.clientDeathDate)), False, widget, row, column, widgetEndDate))
            # else:
            #     if possibleDeathDate:
            #         result = result and (endDateToCompare <= possibleDeathDateToCompare or self.eventPurposeId == 6 or self.checkValueMessage(u'Дата выполнения (окончания) %s не может быть позже возможной даты смерти пациента %s' % (forceString(endDate), forceString(possibleDeathDate)), False, widget, row, column, widgetEndDate))
        if directionDate and begDate:
            result = result and (directionDateToCompare <= begDateToCompare or self.checkValueMessage(u'Дата назначения %s не может быть позже даты начала %s' % (forceString(directionDate), forceString(begDate)), False, widget, row, column, widgetDirectionDate))
        if self.clientBirthDate:
            if directionDate:
                result = result and (directionDateToCompare >= clientBirthDateToCompare or self.checkValueMessage(u'Дата назначения %s не может быть раньше даты рождения пациента %s' % (forceString(directionDate), forceString(self.clientBirthDate)), False, widget, row, column, widgetDirectionDate))
            if begDate:
                result = result and (begDateToCompare >= clientBirthDateToCompare or self.checkValueMessage(u'Дата начала %s не может быть раньше даты рождения пациента %s' % (forceString(begDate), forceString(self.clientBirthDate)), False, widget, row, column, widgetBegDate))
        if self.clientDeathDate:
            if directionDate:
                result = result and (directionDateToCompareWithDeath <= clientDeathDateToCompare or self.eventPurposeId == 6 or self.checkValueMessage(u'Дата назначения %s не может быть позже имеющейся даты смерти пациента %s' % (forceString(directionDate), forceString(self.clientDeathDate)), False, widget, row, column, widgetDirectionDate))
            if begDate:
                result = result and (begDateToCompareWithDeath <= clientDeathDateToCompare or self.eventPurposeId == 6 or self.checkValueMessage(u'Дата начала %s не может быть позже имеющейся даты смерти пациента %s' % (forceString(begDate), forceString(self.clientDeathDate)), False, widget, row, column, widgetBegDate))
        else:
            if possibleDeathDate:
                if directionDate:
                    result = result and (directionDateToCompare <= possibleDeathDateToCompare or self.eventPurposeId == 6 or self.checkValueMessage(u'Дата назначения %s не может быть позже возможной даты смерти пациента %s' % (forceString(directionDate), forceString(possibleDeathDate)), False, widget, row, column, widgetDirectionDate))
                if begDate:
                    result = result and (begDateToCompare <= possibleDeathDateToCompare or self.eventPurposeId == 6 or self.checkValueMessage(u'Дата начала %s не может быть позже возможной даты смерти пациента %s' % (forceString(begDate), forceString(possibleDeathDate)), False, widget, row, column, widgetBegDate))
        return result


    def setClientBirthDate(self, clientBirthDate):
        self.clientBirthDate = clientBirthDate


    def setClientDeathDate(self, clientDeathDate):
        self.clientDeathDate = clientDeathDate


    def setEventPurposeId(self, eventPurposeId):
        self.eventPurposeId = eventPurposeId


    def setClientSex(self, clientSex):
        self.clientSex = clientSex


    def setClientAge(self, clientAge):
        self.clientAge = clientAge


    def setEventTypeIdToAction(self, eventTypeId):
        self.eventTypeId = eventTypeId


    def checkTabNotesEventExternalId(self):
        if getEventTypeForm(self.eventTypeId) == u'072':
            obj = self
        elif hasattr(self, 'tabNotes'):
            obj = self.tabNotes
        else:
            obj = None
        if obj:
            setDate = self.eventSetDateTime.date() if self.eventSetDateTime else None
            sameExternalIdListInfo = obj.checkEventExternalId(setDate, self.itemId())
            if bool(sameExternalIdListInfo):
                sameExternalIdListText = '\n'.join(sameExternalIdListInfo)
                message = u'Подобный внешний идентификатор уже существует в других событиях:\n%s\n\n%s'%(
                                                                                    sameExternalIdListText, u'Исправить?')
                return self.checkValueMessage(message, True, obj.edtEventExternalIdValue)
        return True


    def checkTabVoucherPageVoucherNumber(self):
        isControlVoucherNumber = QtGui.qApp.isControlVoucherNumber()
        if isControlVoucherNumber:
            setDate = self.eventSetDateTime.date() if self.eventSetDateTime else None
            sameVoucherNumberInfo = self.tabVoucher.checkVoucherNumber(setDate, self.itemId(), isControlVoucherNumber)
            if bool(sameVoucherNumberInfo):
                sameVoucherNumberText = '\n'.join(sameVoucherNumberInfo)
                message = u'Подобный номер путевки уже существует в других событиях:\n%s\n\n%s'%(sameVoucherNumberText, u'Исправить?')
                return self.checkValueMessage(message, True if isControlVoucherNumber == 1 else False, self.tabVoucher.edtVoucherSerial)
        return True


    def checkSerialNumberEntered(self):
        self.blankMovingIdList = []
        for actionTab in self.getActionsTabsList():
            model = actionTab.modelAPActions
            for row, (record, action) in enumerate(model.items()):
                if action:
                    actionType = action.getType()
                    for actionPropertyType in actionType.getPropertiesTypeByTypeName('BlankSerialNumber'):
                        serialAndNumber = action.getPropertyById(actionPropertyType.id).getValue()
                        if serialAndNumber:
                            parts = serialAndNumber.rsplit(None, 1)
                            if len(parts) == 1:
                                parts.insert(0, '')
                            serial = trim(parts[0])
                            number = forceInt(parts[1])
                            if serial and number:
                                blankParams = self.getBlankIdList(action)
                                ok, blankMovingId = self.checkBlankParams(blankParams, serial, number, actionTab.tblAPActions, row)
                                self.blankMovingIdList.append(blankMovingId)
                                if not ok:
                                    return False
        return True


    def checkBlankParams(self, blankParams, serial, number, table, row):
        result = True
        for blankMovingId, blankInfo in blankParams.items():
            checkSumLen = forceInt(blankInfo.get('checkSumLen', 0))
            if checkSumLen < 0:
                number = QString(number).right(len(str(number))+ checkSumLen)
            elif checkSumLen > 0:
                number = QString(number).left(len(str(number))- checkSumLen)
            checkingSerialCache = forceInt(toVariant(blankInfo.get('checkingSerial', 0)))
            serialCache = forceString(blankInfo.get('serial', u''))
            if checkingSerialCache and serial:
                result = result and (serialCache == serial or self.checkValueMessage(u'Серия не соответствует документу', True if checkingSerialCache == 1 else False, table, row))
            if result:
                checkingNumberCache = forceInt(toVariant(toVariant(blankInfo.get('checkingNumber', 0))))
                if checkingNumberCache and number:
                    numberFromCache = forceInt(toVariant(blankInfo.get('numberFrom', 0)))
                    numberToCache = forceInt(toVariant(blankInfo.get('numberTo', 0)))
                    result = result and ((number >= numberFromCache and  number <= numberToCache) or self.checkValueMessage(u'Номер не соответствует диапазону номеров документа', True if checkingNumberCache == 1 else False, table, row))
            if result:
                checkingAmountCache = forceInt(toVariant(blankInfo.get('checkingAmount', 0)))
                if checkingAmountCache:
                    returnAmount = forceInt(blankInfo.get('returnAmount', 0))
                    used = forceInt(blankInfo.get('used', 0))
                    received = forceInt(blankInfo.get('received', 0))
                    balance = received - used - returnAmount
#                    result = result and (balance > 0 or self.checkValueMessage(u'В партии закончились соответствующие документы', False, table, row))
                    #Для льготных рецептов КК отключаем эту проверку 
                    if QtGui.qApp.defaultKLADR()[:2] != u'23':
                        result = result and (balance > 0 or self.checkValueMessage(u'В партии закончились соответствующие документы', True if checkingAmountCache == 1 else False, table, row))
            return result, forceRef(blankMovingId)
        return result, None


    def getBlankIdList(self, action):
        blankParams = {}
        docTypeId = action._actionType.id
        if docTypeId:
            db = QtGui.qApp.db
            tableEvent = db.table('Event')
            tableRBBlankActions = db.table('rbBlankActions')
            tableBlankActionsParty = db.table('BlankActions_Party')
            tableBlankActionsMoving = db.table('BlankActions_Moving')
            tablePerson = db.table('Person')
            eventId = forceRef(action._record.value('event_id'))
            personId = None
            orgStructureId = None
            if eventId:
                record = db.getRecordEx(tableEvent, [tableEvent['execPerson_id'], tableEvent['setDate']], [tableEvent['deleted'].eq(0), tableEvent['id'].eq(eventId)])
                if record:
                    personId = forceRef(record.value('execPerson_id')) if record else None
                    setDate = forceDate(record.value('setDate')) if record else None
            else:
                personId = forceRef(action._record.value('person_id'))
            if not personId:
                personId = forceRef(action._record.value('setPerson_id'))
            if not personId:
                personId = QtGui.qApp.userId
            if personId:
                orgStructRecord = db.getRecordEx(tablePerson, [tablePerson['orgStructure_id']], [tablePerson['deleted'].eq(0), tablePerson['id'].eq(personId)])
                orgStructureId = forceRef(orgStructRecord.value('orgStructure_id')) if orgStructRecord else None
            if not orgStructureId:
               orgStructureId = QtGui.qApp.currentOrgStructureId()

            date = forceDate(action._record.value('begDate'))
            if not date and setDate:
                date = setDate
            cond = [tableRBBlankActions['doctype_id'].eq(docTypeId),
                    tableBlankActionsParty['deleted'].eq(0),
                    tableBlankActionsMoving['deleted'].eq(0)
                    ]
            if date:
                cond.append(tableBlankActionsMoving['date'].le(date))
                cond.append(db.joinOr([tableBlankActionsMoving['returnDate'].ge(date), tableBlankActionsMoving['returnDate'].isNull()]))
            if personId and orgStructureId:
                cond.append(db.joinOr([tableBlankActionsMoving['person_id'].eq(personId), tableBlankActionsMoving['orgStructure_id'].eq(orgStructureId)]))
            elif personId:
                cond.append(tableBlankActionsMoving['person_id'].eq(personId))
            elif orgStructureId:
                cond.append(tableBlankActionsMoving['orgStructure_id'].eq(orgStructureId))
            queryTable = tableRBBlankActions.innerJoin(tableBlankActionsParty, tableBlankActionsParty['doctype_id'].eq(tableRBBlankActions['id']))
            queryTable = queryTable.innerJoin(tableBlankActionsMoving, tableBlankActionsMoving['blankParty_id'].eq(tableBlankActionsParty['id']))
            records = db.getRecordList(queryTable, u'BlankActions_Moving.numberFrom, BlankActions_Moving.numberTo, BlankActions_Moving.returnAmount, BlankActions_Moving.used, BlankActions_Moving.received, BlankActions_Moving.id AS blankMovingId, BlankActions_Party.serial, rbBlankActions.checkingSerial, rbBlankActions.checkingNumber, rbBlankActions.checkingAmount, rbBlankActions.checkSumLen', cond, u'rbBlankActions.checkingSerial, rbBlankActions.checkingNumber, rbBlankActions.checkingAmount DESC')
            for record in records:
                blankInfo = {}
                blankMovingId = forceRef(record.value('blankMovingId'))
                checkingSerial = forceInt(record.value('checkingSerial'))
                checkingNumber = forceInt(record.value('checkingNumber'))
                checkingAmount = forceInt(record.value('checkingAmount'))
                checkSumLen = forceInt(record.value('checkSumLen'))
                serial = forceString(record.value('serial'))
                numberFromString = forceString(record.value('numberFrom'))
                numberToString = forceString(record.value('numberTo'))
                if checkSumLen < 0:
                    
                    numberFromStringCS = numberFromString[-checkSumLen:]
                    numberToStringCS   = numberToString[-checkSumLen:]
                elif checkSumLen > 0:
                    
                    numberFromStringCS = numberFromString[:-checkSumLen]
                    numberToStringCS   = numberToString[:-checkSumLen]
                else:
                    numberFromStringCS = numberFromString
                    numberToStringCS = numberToString
                numberFrom = forceInt(numberFromStringCS) if numberFromStringCS else 0
                numberTo = forceInt(numberToStringCS) if numberToStringCS else 0
                returnAmount = forceInt(record.value('returnAmount'))
                used = forceInt(record.value('used'))
                received = forceInt(record.value('received'))
                blankInfo['blankMovingId'] = blankMovingId
                blankInfo['checkingSerial'] = checkingSerial
                blankInfo['checkingNumber'] = checkingNumber
                blankInfo['checkingAmount'] = checkingAmount
                blankInfo['checkSumLen'] = checkSumLen
                blankInfo['serial'] = serial
                blankInfo['numberFrom'] = numberFrom
                blankInfo['numberTo'] = numberTo
                blankInfo['returnAmount'] = returnAmount
                blankInfo['used'] = used
                blankInfo['received'] = received
                blankParams[blankMovingId] = blankInfo
        return blankParams


    def saveBlankUsers(self, blankMovingIdList = []):
        db = QtGui.qApp.db
        tableBlankActionsMoving = db.table('BlankActions_Moving')
        tableBlankActionsParty = db.table('BlankActions_Party')
        for blankMovingId in blankMovingIdList:
            recordMoving = db.getRecordEx(tableBlankActionsMoving, u'*', [tableBlankActionsMoving['deleted'].eq(0), tableBlankActionsMoving['id'].eq(blankMovingId)])
            blankPartyId = None
            if recordMoving:
                used = forceInt(recordMoving.value('used'))
                blankPartyId = forceRef(recordMoving.value('blankParty_id'))
                recordMoving.setValue('used', toVariant(used + 1))
                db.updateRecord(tableBlankActionsMoving, recordMoving)
            if blankPartyId:
                recordParty = db.getRecordEx(tableBlankActionsParty, u'*', [tableBlankActionsParty['id'].eq(blankPartyId), tableBlankActionsParty['deleted'].eq(0)])
                if recordParty:
                    used = forceInt(recordParty.value('used'))
                    recordParty.setValue('used', toVariant(used + 1))
                    db.updateRecord(tableBlankActionsParty, recordParty)


    def setContractId(self, contractId):
        if self.contractId != contractId:
            if contractId:
                db = QtGui.qApp.db
                table = db.table('Contract')
                record = db.getRecordEx(table, [table['finance_id'], table['dateOfVisitExposition']], [table['id'].eq(contractId)])
                self.eventFinanceId = forceRef(record.value('finance_id')) if record else None
                self.dateOfVisitExposition = forceInt(record.value('dateOfVisitExposition')) if record else None
            else:
                self.eventFinanceId = getEventFinanceId(self.eventTypeId)
                self.dateOfVisitExposition = None
            self.contractId = contractId
            self.emit(SIGNAL('updateActionsPriceAndUet()'))
            self.updateTotalUet()
            if hasattr(self, 'tabMes'):
                self.tabMes.setContractId(contractId)


    def getUet(self, actionTypeId, personId, financeId, contractId):
        if not contractId:
            contractId = self.contractId
            financeId = self.eventFinanceId
        if contractId and actionTypeId:
            serviceIdList = self.getActionTypeServiceIdList(actionTypeId, financeId)
            tariffCategoryId = self.getPersonTariffCategoryId(personId)
            tariffDescr = self.contractTariffCache.getTariffDate(contractId, self, self.eventSetDateTime, financeId)
            uet = CContractTariffCache.getUetToDate(tariffDescr.dateTariffMap, serviceIdList, tariffCategoryId, self.eventSetDateTime)
            return uet
        return 0


    def updateTotalUet(self):
        if hasattr(self, 'lblShowTotalUet') and hasattr(self, 'modelActionsSummary'):
            uet = self.modelActionsSummary.calcTotalUet()
            self.frmTotalUet.setVisible(bool(uet))
            self.lblShowTotalUet.setNum(uet)


    def regenerateAccActions(self, top, bottom):
        if hasattr(self, 'tabCash') and hasattr(self.tabCash, 'modelAccActions'):
            self.tabCash.modelAccActions.regenerate(top, bottom)

    def checkConsultationOrEpicris(self, tabList):
        flatCodeList = []
        needsListNazOnko = False
        for actionTab in tabList:
            model = actionTab.tblAPActions.model()
            for record, action in model.items():
                if action and action.actionType().id:
                    flatCode = action.actionType().flatCode
                    if flatCode in [u'appointments', u'directionCancer', u'List_covid',
                                    u'KRIT', u'Code_MDV', u'ControlListOnko', u'list_naz_onko']:
                        flatCodeList.append(flatCode)
                        try:
                            if flatCode == u'ControlListOnko' and action.getProperty(u'Тип лечения').getValue() in [u'Лекарственная противоопухолевая терапия', u'Химиолучевая терапия']:
                                needsListNazOnko = True
                        except KeyError:
                            pass
        if flatCodeList:
            return True, flatCodeList, needsListNazOnko
        return False, flatCodeList, needsListNazOnko

    def setActionCons(self, flatCode):
        actionTypeIdList = getActionTypeIdListByFlatCode(flatCode)
        self.setActionIEMK(actionTypeIdList)

    def setActionConsbyIds(self, actionTypeIdList):
        self.setActionIEMK(actionTypeIdList)

    def setActionIEMK(self, actionTypeIdList):
        self.listAction = []
        for model in [self.tabStatus.tblAPActions.model(), self.tabDiagnostic.tblAPActions.model(),
                      self.tabCure.tblAPActions.model(), self.tabMisc.tblAPActions.model()]:
            for row, (record, action) in enumerate(model.items()):
                if action and action._actionType.id:
                    if action._actionType.id not in self.listAction:
                        self.listAction.append(action._actionType.id)

        actionTypeIdsIEMK = list(set(actionTypeIdList) & set(self.listAction))
        if not actionTypeIdsIEMK:
            for actionTypeId in actionTypeIdList: #if len(actionTypeIdList) == 1:
             #   actionTypeId = actionTypeIdList[0]
                actionTypeClass = self.getActionTypeClass(actionTypeId)
                if actionTypeClass == 0:
                    modelSt = self.tabStatus.tblAPActions.model()
                    index = modelSt.index(modelSt.rowCount() - 1, 0)
                    self.tabStatus.tblAPActions.setCurrentIndex(index)
                    modelSt.setData(index, toVariant(actionTypeId))
                elif actionTypeClass == 1:
                    modelDgn = self.tabDiagnostic.tblAPActions.model()
                    index = modelDgn.index(modelDgn.rowCount() - 1, 0)
                    self.tabDiagnostic.tblAPActions.setCurrentIndex(index)
                    modelDgn.setData(index, toVariant(actionTypeId))
                elif actionTypeClass == 2:
                    modelCure = self.tabCure.tblAPActions.model()
                    index = modelCure.index(modelCure.rowCount() - 1, 0)
                    self.tabCure.tblAPActions.setCurrentIndex(index)
                    modelCure.setData(index, toVariant(actionTypeId))
                elif actionTypeClass == 3:
                    modelMisc = self.tabMisc.tblAPActions.model()
                    index = modelMisc.index(modelMisc.rowCount() - 1, 0)
                    self.tabMisc.tblAPActions.setCurrentIndex(index)
                    modelMisc.setData(index, toVariant(actionTypeId))

    def getActionTypeClass(self, actionTypeId):
        return forceInt(QtGui.qApp.db.translate('ActionType', 'id', actionTypeId, 'class'))

    def getKRITValue(self, valueTypeName):
        code = None
        for actionTab in self.getActionsTabsList():
            model = actionTab.modelAPActions
            for record, action in model.items():
                actionTypeId = forceRef(record.value('actionType_id'))
                actionType = CActionTypeCache.getById(actionTypeId) if actionTypeId else None
                if actionType.flatCode == 'KRIT':
                    for prop in action._properties:
                        if prop.type().name == valueTypeName:
                            value = prop.getValue()
                            if value:
                                code = forceString(QtGui.qApp.db.translate('soc_spr80', 'id', value, 'code'))
        return code

    @pyqtSignature('')
    def on_actEditClient_triggered(self):
        self.editClient()

    @pyqtSignature('')
    def on_actPortal_Doctor_triggered(self):
        templateId = None
        result = QtGui.qApp.db.getRecordEx('rbPrintTemplate', 'id',
                                           '`default` LIKE "%s" AND deleted = 0' % ('%/EMK_V3/indexV2.php%'))

        data = getEventContextData(self)

        if result:
            templateId = result.value('id').toString()
            if templateId:
                QtGui.qApp.call(self, applyTemplate, (self, templateId, data))
            else:
                QtGui.QMessageBox.information(self, u'Ошибка', u'Шаблон для перехода на портал врача не найден',
                                              QtGui.QMessageBox.Close, QtGui.QMessageBox.Close)
        else:
            QtGui.QMessageBox.information(self, u'Ошибка', u'Шаблон для перехода на портал врача не найден',
                                          QtGui.QMessageBox.Close, QtGui.QMessageBox.Close)


    @pyqtSignature('')
    def on_actOpenClientVaccinationCard_triggered(self):
        if self.clientId and QtGui.qApp.userHasAnyRight([urCanReadClientVaccination, urCanEditClientVaccination]):
            openClientVaccinationCard(self, self.clientId)


    @pyqtSignature('')
    def on_actSurveillancePlanningClients_triggered(self):
        self.surveillancePlanningShow(self.clientId)


    def surveillancePlanningShow(self, clientId, monitoringIdList=None):
        # if forceBool(QtGui.qApp.preferences.appPrefs.get('isPrefSurveillancePlanningDialog', False)):
        if clientId:
            db = QtGui.qApp.db
            tableDiagnosis = db.table('Diagnosis')
            tableDiagnostic = db.table('Diagnostic')
            queryTable = tableDiagnosis.leftJoin(tableDiagnostic, tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']))
            cond = [tableDiagnosis['deleted'].eq(0),
                    tableDiagnostic['deleted'].eq(0),
                    tableDiagnosis['dispanser_id'].isNotNull(),
                    tableDiagnostic['dispanser_id'].isNotNull(),
                    tableDiagnosis['client_id'].eq(clientId)
                    ]
            if monitoringIdList:
                cond.append(tableDiagnostic['id'].inlist(monitoringIdList))
            cols = [u'Diagnostic.*',
                    tableDiagnosis['MKB'],
                    tableDiagnosis['MKBEx'],
                    tableDiagnosis['dispanserBegDate'],
                    tableDiagnosis['dispanser_id'].alias('diagnosisDispanser_id'),
                    tableDiagnostic['endDate'],
                    'max(Diagnosis.endDate) as maxDiagnosisEndDate',
                    'max(Diagnostic.endDate) as maxDiagnosticEndDate'
                    ]
            dispanserItems = db.getRecordListGroupBy(queryTable, cols, cond, group = 'MKB', order='maxDiagnosisEndDate DESC, maxDiagnosticEndDate DESC')
            if dispanserItems:
                try:
                    dialog = CSurveillancePlanningEditDialog(self)
                    dialog.setEventEditor(self)
                    eventRecord = None
                    eventIdList = []
                    for dispanserItem in dispanserItems:
                        eventId = forceRef(dispanserItem.value('event_id'))
                        if eventId and eventId not in eventIdList:
                            eventIdList.append(eventId)
                    if eventIdList:
                        tableEvent = db.table('Event')
                        eventRecord = db.getRecordEx(tableEvent, u'*', [tableEvent['id'].inlist(eventIdList), tableEvent['deleted'].eq(0)], u'Event.setDate DESC')
                        dialog.setEventRecord(eventRecord)
                        eventIdLast = forceRef(eventRecord.value('id')) if eventRecord else None
                        if eventIdLast:
                            cond = [tableDiagnostic['event_id'].eq(eventIdLast),
                                    tableDiagnosis['deleted'].eq(0),
                                    tableDiagnostic['deleted'].eq(0),
                                    tableDiagnosis['dispanser_id'].isNotNull(),
                                    tableDiagnostic['dispanser_id'].isNotNull(),
                                    tableDiagnosis['client_id'].eq(clientId)
                                    ]
                            dispanserEventLastItems = db.getRecordListGroupBy(queryTable, cols, cond, group = 'MKB', order='maxDiagnosisEndDate DESC, maxDiagnosticEndDate DESC')
                            dialog.setDiagnosticEventLastRecords(dispanserEventLastItems)
                        dialog.setDiagnosticRecords(dispanserItems)
                        dialog.exec_()
                finally:
                    dialog.deleteLater()


    @pyqtSignature('')
    def on_cmbContract_valueChanged(self):
        self.setContractId(self.cmbContract.value())


    @pyqtSignature('int')
    def on_cmbResult_currentIndexChanged(self):
        db = QtGui.qApp.db
        if QtGui.qApp.provinceKLADR()[:2] == u'23' and CFinanceType.getCode(self.eventFinanceId) == 2:
            if hasattr(self, 'modelDiagnostics'):
                modelDiagnostics = self.modelDiagnostics
            elif hasattr(self, 'modelFinalDiagnostics'):
                modelDiagnostics = self.modelFinalDiagnostics
            else:
                modelDiagnostics = None

            if modelDiagnostics and modelDiagnostics.getColIndex('result_id', None):
                ishodObrCode = self.cmbResult.code()
                endDateCheck = self.edtEndDate.date()
                if not endDateCheck:
                    endDateCheck = self.edtBegDate.date()
                table = db.table('soc_checkSpr12')
                cond = [table['code'].eq(ishodObrCode),
                        table['begDate'].le(endDateCheck),
                        table['endDate'].gt(endDateCheck.addDays(1))
                        ]
                record = db.getRecordEx(table, 'code_ishl', cond)
                codeIshl = ''
                if record:
                    codeIshl = forceString(record.value('code_ishl')).split(',')

                table = db.table('rbDiagnosticResult')
                cond = [table['eventPurpose_id'].eq(self.eventPurposeId),
                        db.joinOr([table['begDate'].isNull(), table['begDate'].le(endDateCheck)]),
                        db.joinOr([table['endDate'].isNull(), table['endDate'].ge(endDateCheck)])]

                if codeIshl:
                    cond.append(table['regionalCode'].inlist(codeIshl))

                modelDiagnostics.cols()[modelDiagnostics.getColIndex('result_id', None)].filter = db.joinAnd(cond)

        if self.isVisible():
            if hasattr(self, 'tabMisc'):
                actionsTab = self.tabMisc
            elif hasattr(self, 'tabActions'):
                actionsTab = self.tabActions
            else:
                return
            items = actionsTab.modelAPActions.items()
            for item in items:
                record, action = item
                if record:
                    if u'leaved' in action._actionType.flatCode.lower():
                        prop = action.getProperty(u'Исход госпитализации')
                        if prop:
                            resultName = forceString(db.translate('rbResult', 'id', self.cmbResult.value(), 'name'))
                            if resultName.lower() in (u'умер', u'смерть') and prop._value != u'умер':
                                prop.setValue(u'умер')
                            elif resultName.lower() == u'выписан' and prop._value != u'выписан':
                                prop.setValue(u'выписан')


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelActionsSummary_dataChanged(self, leftTop, rightBottom):
        self.updateTotalUet()
        self.regenerateAccActions(leftTop.row(), rightBottom.row())


    @pyqtSignature('')
    def on_modelActionsSummary_modelReset(self):
        self.updateTotalUet()


    @pyqtSignature('QModelIndex, int, int')
    def on_modelActionsSummary_rowsInserted(self, parent, start, end):
        self.updateTotalUet()
        self.regenerateAccActions(start, end)


    @pyqtSignature('QModelIndex, int, int')
    def on_modelActionsSummary_rowsRemoved(self, parent, start, end):
        self.updateTotalUet()
        self.regenerateAccActions(start, end)


    @pyqtSignature('')
    def on_btnAPActionsAdd_triggered(self):
        if self.isReadOnly():
            return
        if hasattr(self, 'tabWidget'):
            widget = self.tabWidget.currentWidget()
            currentIndexWidget = self.tabWidget.currentIndex()
            if hasattr(self, 'tabMedicalDiagnosis') and currentIndexWidget == self.tabWidget.indexOf(self.tabMedicalDiagnosis):
                self.tabMedicalDiagnosis.createAction()
                return
            elif hasattr(self, 'tabTempInvalidEtc') and hasattr(self, 'tabTempInvalidAndAegrotat') and currentIndexWidget == self.tabWidget.indexOf(self.tabTempInvalidEtc):
                tempInvalidIndex = self.tabTempInvalidAndAegrotat.currentIndex()
                if hasattr(self, 'tabTempInvalid') and tempInvalidIndex == self.tabTempInvalidAndAegrotat.indexOf(self.tabTempInvalid):
                    self.grpTempInvalid.newTempInvalid()
                elif hasattr(self, 'tabAegrotat') and tempInvalidIndex == self.tabTempInvalidAndAegrotat.indexOf(self.tabAegrotat):
                    self.grpAegrotat.newTempInvalid()
                elif hasattr(self, 'tabVitalRestriction') and tempInvalidIndex == self.tabTempInvalidAndAegrotat.indexOf(self.tabVitalRestriction):
                    self.grpVitalRestriction.newTempInvalid()
                return
            cond = []
            widgetClass = {}
            if hasattr(self, 'tabToken'):
                cond.append(self.tabToken)
                widgetClass[self.tabToken] = [0, 1, 2, 3]
            if hasattr(self, 'tabMes'):
                cond.append(self.tabMes)
                widgetClass[self.tabMes] = [0, 1, 2, 3]
            if hasattr(self, 'tabStatus'):
                cond.append(self.tabStatus)
                widgetClass[self.tabStatus] = [0]
            if hasattr(self, 'tabDiagnostic'):
                cond.append(self.tabDiagnostic)
                widgetClass[self.tabDiagnostic] = [1]
            if hasattr(self, 'tabCure'):
                cond.append(self.tabCure)
                widgetClass[self.tabCure] = [2]
            if hasattr(self, 'tabMisc'):
                cond.append(self.tabMisc)
                widgetClass[self.tabMisc] = [3]
            if widget not in cond:
                return
        else:
            return
        if hasattr(self, 'tblActions'):
            hasTblActions = True
        else:
            hasTblActions = False

        orgStructureId = QtGui.qApp.currentOrgStructureId()
        financeCode = forceStringEx(QtGui.qApp.db.translate('rbFinance', 'id', self.eventFinanceId, 'code'))
        if financeCode:
            financeCode = financeCode in ('3', '4')
        existsActionTypesList = []
        if hasattr(self, 'modelActionsSummary'):
            for item in self.modelActionsSummary.items():
                existsActionTypesList.append(forceRef(item.value('actionType_id')))
        actionTypeClasses = widgetClass.get(widget, [0, 1, 2, 3])
        actionTypes = selectActionTypes(self if len(actionTypeClasses) != 1 else widget,
                                 self,
                                 actionTypeClasses,
                                 orgStructureId,
                                 self.eventTypeId,
                                 self.contractId,
                                 self.getMesId(),
                                 financeCode,
                                 self._id,
                                 existsActionTypesList,
                                 visibleTblSelected=True,
                                 contractTariffCache=self.contractTariffCache,
                                 clientMesInfo=self.getClientMesInfo(),
                                 eventDate=self.edtEndDate.date() if self.edtEndDate.date() else self.edtBegDate.date()
                               )
        updateTabList = []
        isEventCSGRequired = getEventCSGRequired(self.eventTypeId)
        actionsTabsList = self.getActionsTabsList()
        labGroup = set()
        hasAlfaLabActions = False
        referralActionTypeId = forceRef(QtGui.qApp.db.translate('ActionType', 'flatCode', 'referralLisLab', 'id'))
        
        for actionTypeId, action, csgRecord in actionTypes:
            res = True
            actionType = CActionTypeCache.getById(actionTypeId)
            if u'moving' in actionType.flatCode.lower():
                for record in self.modelActionsSummary._items:
                    if action:
                        actionTypeItem = CActionTypeCache.getById(forceString(record.value('actionType_id')))
                        if actionTypeItem and (u'received' in actionTypeItem.flatCode.lower()):
                            if not forceDate(record.value('endDate')):
                                res = actionType.checkReceivedMovingLeaved(u'Действие "Движение" не может появится при наличии не законченного действия "Поступление"')
                                break
                            break
                else:
                    res = actionType.checkReceivedMovingLeaved(u'Действие "Движение" не должно применяться пока нет действия "Поступление"')
            if not res:
                actionTypes.remove((actionTypeId, action, csgRecord))
                
        if len(actionTypeClasses) != 1:
            if hasTblActions:
                model = self.tblActions.model()
                for item in actionsTabsList[1].tblAPActions.model().items():
                    record, action = item
                    actionType = action.actionType()
                    if actionType.flatCode == 'referralLisLab':
                        labGroup.add((pyDate(forceDate(action.getDirectionDate())), action[u'Группа забора'], action.getId()))
                for actionTypeId, action, csgRecord in actionTypes:
                    class_ = forceInt(QtGui.qApp.db.translate('ActionType', 'id', actionTypeId, 'class'))
                    actionsTab = actionsTabsList[class_]
                    # model = actionsTab.tblAPActions.model()
                    if actionsTab not in updateTabList:
                        updateTabList.append(actionsTab)
                    if 'alfalabgroup_' in action.actionType().flatCode:
                        hasAlfaLabActions = True
                        if (pyDate(forceDate(action.getDirectionDate())), action.actionType().flatCode, action.getPrescriptionId()) not in labGroup:
                            labGroup.add((pyDate(forceDate(action.getDirectionDate())), action.actionType().flatCode, action.getPrescriptionId()))
                            index = model.index(model.rowCount() - 1, 0)
                            model.setData(index, toVariant(referralActionTypeId))
                            actionsTab.tblAPActions.setCurrentIndex(index)
                            record, referralAction = model.models[1].items()[model.models[1].rowCount() - 2]
                            record.setValue('directionDate', forceDateTime(action.getDirectionDate()))
                            record.setValue('begDate', forceDateTime(action.getDirectionDate()))
                            referralAction[u'Группа забора'] = action.actionType().flatCode
                            actionsTab._onActionChanged()

                    index = model.index(model.rowCount()-1, 0)
                    model.setData(index, toVariant(actionTypeId), presetAction=action, related=True)
                    if isEventCSGRequired:
                        actionsTab.cmbCSG.addActionToCSG(action.getRecord(), csgRecord)
                # model.emitAllChanged()
            else:
                if len(actionsTabsList) == 4:
                    for item in actionsTabsList[1].tblAPActions.model().items():
                        record, action = item
                        actionType = action.actionType()
                        if actionType.flatCode == 'referralLisLab':
                            labGroup.add((pyDate(forceDate(action.getDirectionDate())), action[u'Группа забора'], action.getId()))
                    for actionTypeId, action, csgRecord in actionTypes:
                        class_ = forceInt(QtGui.qApp.db.translate('ActionType', 'id', actionTypeId, 'class'))
                        actionsTab = actionsTabsList[class_]
                        if actionsTab not in updateTabList:
                            updateTabList.append(actionsTab)
                        model = actionsTab.tblAPActions.model()
                        if 'alfalabgroup_' in action.actionType().flatCode:
                            hasAlfaLabActions = True
                            if (pyDate(forceDate(action.getDirectionDate())), action.actionType().flatCode, action.getPrescriptionId()) not in labGroup:
                                labGroup.add((pyDate(forceDate(action.getDirectionDate())), action.actionType().flatCode, action.getPrescriptionId()))
                                index = model.index(model.rowCount() - 1, 0)
                                model.setData(index, toVariant(referralActionTypeId))
                                actionsTab.tblAPActions.setCurrentIndex(index)
                                record, referralAction = model.items()[model.rowCount() - 2]
                                record.setValue('directionDate', forceDateTime(action.getDirectionDate()))
                                record.setValue('begDate', forceDateTime(action.getDirectionDate()))
                                referralAction[u'Группа забора'] = action.actionType().flatCode
                                actionsTab._onActionChanged()
                        model.addRow(actionTypeId, presetAction=action)
                        if isEventCSGRequired:
                            actionsTab.cmbCSG.addActionToCSG(action.getRecord(), csgRecord)
        else:
            for item in actionsTabsList[1].tblAPActions.model().items():
                record, action = item
                actionType = action.actionType()
                if actionType.flatCode == 'referralLisLab':
                    labGroup.add((pyDate(forceDate(action.getDirectionDate())), action[u'Группа забора'], action.getId()))
            for actionTypeId, action, csgRecord in actionTypes:
                class_ = forceInt(QtGui.qApp.db.translate('ActionType', 'id', actionTypeId, 'class'))
                actionsTab = actionsTabsList[class_]
                if actionsTab not in updateTabList:
                    updateTabList.append(actionsTab)
                model = actionsTab.tblAPActions.model()
                if 'alfalabgroup_' in action.actionType().flatCode:
                    hasAlfaLabActions = True
                    if (pyDate(forceDate(action.getDirectionDate())), action.actionType().flatCode, action.getPrescriptionId()) not in labGroup:
                        labGroup.add((pyDate(forceDate(action.getDirectionDate())), action.actionType().flatCode, action.getPrescriptionId()))
                        index = model.index(model.rowCount() - 1, 0)
                        model.setData(index, toVariant(referralActionTypeId))
                        actionsTab.tblAPActions.setCurrentIndex(index)
                        record, referralAction = model.items()[model.rowCount() - 2]
                        record.setValue('directionDate', forceDateTime(action.getDirectionDate()))
                        record.setValue('begDate', forceDateTime(action.getDirectionDate()))
                        referralAction[u'Группа забора'] = action.actionType().flatCode
                        actionsTab._onActionChanged()
                index = model.index(model.rowCount() - 1, 0)
                model.setData(index, toVariant(actionTypeId), presetAction=action)
                if isEventCSGRequired:
                    actionsTab.cmbCSG.addActionToCSG(action.getRecord(), csgRecord)
        if hasAlfaLabActions:
            actionsTabsList[1].tblAPActions.sortByReferrals()
            # if hasTblActions:
            #     self.tblActions.model().regenerate()
        for actionsTab in updateTabList:
            # actionsTab.updateActionEditor()
            actionsTab.onActionCurrentChanged()

        if len(actionTypeClasses) == 1:
            self.tabWidget.setCurrentWidget(widget)
        if hasattr(self, 'modelActionsSummary'):
            self.modelActionsSummary.regenerate()
        if hasattr(self, 'tabCash') and hasattr(self.tabCash, 'modelAccActions'):
            self.tabCash.modelAccActions.regenerate()


    @pyqtSignature('')
    def on_btnMedicalCommission_clicked(self):
        actionTypeId = None
        currentTable = None
        currentRow = None
        actionTypeIdList = getActionTypeIdListByFlatCode(u'inspection_case%')
        if actionTypeIdList:
            if len(actionTypeIdList) > 1:
                try:
                    dialog = CActionTypeDialogTableModel(self, actionTypeIdList)
                    dialog.setWindowTitle(u'Выберите тип направления на ВК')
                    if dialog.exec_():
                        actionTypeId = dialog.currentItemId()
                finally:
                    dialog.deleteLater()
            else:
                actionTypeId = actionTypeIdList[0]
            if actionTypeId:
                actionType = CActionTypeCache.getById(actionTypeId)
                actionTypeClass = actionType.class_
                actionsTabsList = self.getActionsTabsList()
                for table in actionsTabsList:
                    model = table.modelAPActions
                    if actionTypeId in model.actionTypeIdList and actionTypeClass == model.actionTypeClass:
                        model.addRow(actionTypeId, actionType.amount)
                        currentTable = table.tblAPActions
                        currentRow = len(model.items())-1
                        break
                if currentTable:
                    self.setFocusToWidget(currentTable, currentRow, 0)


    @pyqtSignature('int')
    def on_btnPrint_printByTemplate(self, templateId):
        if self.checkPrintByTemplateAllowed(templateId):
            data = getEventContextData(self)
            applyTemplate(self, templateId, data, signAndAttachHandler=self.tabNotes.btnAttachedFiles.getSignAndAttachHandler())


    @pyqtSignature('int')
    def on_btnPrintMedicalDiagnosis_printByTemplate(self, templateId):
        if hasattr(self, 'tabMedicalDiagnosis') and QtGui.qApp.userHasRight(urReadMedicalDiagnosis):
            model = self.tabMedicalDiagnosis.tblEventMedicalDiagnosis.model()
            if templateId == -1:
                doc = QtGui.QTextDocument()
                cursor = QtGui.QTextCursor(doc)
                cursor.setCharFormat(CReportBase.ReportTitle)
                cursor.insertText(u'Врачебный диагноз')
                cursor.setCharFormat(CReportBase.ReportBody)
                cursor.insertBlock()
                cursor.insertText(u'Отчёт составлен: ' + forceString(QDateTime.currentDateTime()))
                cursor.insertBlock()
                colWidths  = [ self.tabMedicalDiagnosis.tblEventMedicalDiagnosis.columnWidth(i) for i in xrange(model.columnCount()) ]
                totalWidth = sum(colWidths)
                tableColumns = []
                for iCol, colWidth in enumerate(colWidths):
                    widthInPercents = str(max(1, colWidth*90/totalWidth))+'%'
                    tableColumns.append((widthInPercents, [forceString(model._cols[iCol].title())], CReportBase.AlignLeft))
                table = createTable(cursor, tableColumns)
                for iModelRow in xrange(model.rowCount()):
                    iTableRow = table.addRow()
                    for iModelCol in xrange(model.columnCount()):
                        index = model.createIndex(iModelRow, iModelCol)
                        text = forceString(model.data(index))
                        table.setText(iTableRow, iModelCol, text)
                html = doc.toHtml('utf-8')
                view = CReportViewDialog(self)
                view.setText(html)
                view.exec_()
            else:
                context = CInfoContext()
                data = { 'medicalDiagnosis': CMedicalDiagnosisInfoList(context, [model], None) }
                QtGui.qApp.call(self, applyTemplate, (self, templateId, data))


    @pyqtSignature('')
    def on_btnSaveAndCreateAccount_clicked(self):
        self.done(self.saveAndCreateAccount)


    def setItemId(self, itemId):
        CItemEditorBaseDialog.setItemId(self, itemId)
        if itemId:
            record = QtGui.qApp.db.getRecord('Event', '*', itemId)
            if record:
                self.tabNotes.setNotes(record)


    @pyqtSignature('')
    def on_btnApply_clicked(self):
        prevId = self.itemId()
        if self.applyChanges():
            self.getPrevActionIdHelper.prevActionIdCache = {} # Из-за кэша неправильно отрабатывает копирование из предыдущего тт2046
            if self.itemId() != prevId and hasattr(self, 'btnRelatedEvent'):
                self.btnRelatedEventHighlight()
            buttons = QtGui.QMessageBox.Ok
            messageBox = QtGui.QMessageBox()
            messageBox.setWindowFlags(messageBox.windowFlags() | Qt.WindowStaysOnTopHint)
            messageBox.setWindowTitle(u'Внимание!')
            messageBox.setText(u'Данные сохранены')
            messageBox.setStandardButtons(buttons)
            messageBox.setDefaultButton(QtGui.QMessageBox.Ok)
            messageBox.exec_()


    @pyqtSignature('')
    def on_btnRefresh_clicked(self):
        prevId = self.itemId()
        if self.applyChanges():
            if self.itemId() != prevId and hasattr(self, 'btnRelatedEvent'):
                self.btnRelatedEventHighlight()
            self.loadActions()
            buttons = QtGui.QMessageBox.Ok
            messageBox = QtGui.QMessageBox()
            messageBox.setWindowFlags(messageBox.windowFlags() | Qt.WindowStaysOnTopHint)
            messageBox.setWindowTitle(u'Внимание!')
            messageBox.setText(u'Данные обновлены')
            messageBox.setStandardButtons(buttons)
            messageBox.setDefaultButton(QtGui.QMessageBox.Ok)
            messageBox.exec_()


    def applyChanges(self):
        if self.getEventId() and hasattr(self, 'tabNotes') and self.tabNotes.isEventClosed():
            res = self.askSaveContinueEdit()
        else:
            res = self.cdSave
        if res == self.cdSave and self.saveData():
            QtGui.qApp.delAllCounterValueIdReservation()
            self.lock(self._tableName, self._id)
            return True
        else:
            return False


    def on_btnJobTickets_clicked(self):

        def hasActionEmptyJobTicketValue(action):
            actionType       = action.getType()
            propertyTypeList = actionType.getPropertiesById().values()
            for propertyType in propertyTypeList:
                property     = action.getPropertyById(propertyType.id)
                if property.type().isJobTicketValueType():
                    return not bool(property.getValue())
            return False

        def filterAction(action):
            actionType       = action.getType()
            propertyTypeList = actionType.getPropertiesById().values()
            for propertyType in propertyTypeList:
                property     = action.getPropertyById(propertyType.id)
                if property.type().isJobTicketValueType():
                    return property.getValue()
            return None


        def filterEmpty(items):
            return [(record, action)
                    for (record, action) in items
                    if hasActionEmptyJobTicketValue(action)
                   ]

        def jobTicketDone(jobTicketId):
            return forceRef(QtGui.qApp.db.translate('Job_Ticket', 'id', jobTicketId, 'status')) == CJobTicketStatus.done


        def filterFull(items):
            fullItemList = []
            jobTicketIdList = []
            for (record, action) in items:
                status = forceInt(record.value('status'))
                if status in (CActionStatus.finished, CActionStatus.canceled, CActionStatus.refused, CActionStatus.withoutResult):
                    continue

                propertyValue = forceRef(filterAction(action))
                if bool(propertyValue):
                    if jobTicketDone(propertyValue):
                        continue

                    jobTicketIdList.append(propertyValue)
                    fullItemList.append((record, action))
            return fullItemList, jobTicketIdList

        emptyActionsModelsItemList = self.getActionsModelsItemsList(filterEmpty)
        fullActionsModelsItemList = self.getJobTicketsList(filterFull)
        dlg = CEventJobTicketsLockEditor(self, emptyActionsModelsItemList,
                                     fullActionsModelsItemList, self.clientId, self)
        if dlg.exec_():
            for actionsTab in self.getActionsTabsList():
                actionsTab.onActionCurrentChanged()
            self._jobTicketRecordsMap2PostUpdate = dlg.getJobTicketRecordsMap2PostUpdate()
        return fullActionsModelsItemList


    def __jobTicketRecordsMap2PostUpdate(self):
        if self._jobTicketRecordsMap2PostUpdate:
            for record in self._jobTicketRecordsMap2PostUpdate.values():
                QtGui.qApp.db.updateRecord('Job_Ticket', record)


    def getTemperatureList(self, setDate):
        try:

            from ThermalSheet.TemperatureListEditor import CTemperatureListEditorDialog
            eventId = self.itemId()
            actionTypeIdList = getActionTypeIdListByFlatCode(u'temperatureSheet%')
            if eventId and actionTypeIdList and self.clientId:
                db = QtGui.qApp.db
                tableClient = db.table('Client')
                clientRecord = db.getRecordEx(tableClient, [tableClient['sex'], tableClient['birthDate']], [tableClient['id'].eq(self.clientId), tableClient['deleted'].eq(0)])
                clientSex = forceInt(clientRecord.value('sex'))
                date = self.eventDate
                if not date and self.eventSetDateTime:
                    date = self.eventSetDateTime.date()
                clientAge = calcAge(forceDate(clientRecord.value('birthDate')), date if date else QDate.currentDate())
                dialog = CTemperatureListEditorDialog(self, self.clientId, eventId, actionTypeIdList, clientSex, clientAge, setDate)
                try:
                    if dialog.exec_():
                        if dialog.action:
                            dialog.action.save()
                finally:
                    dialog.deleteLater()
        except:
            QtGui.qApp.logCurrentException()


    def loadActions(self):
        items = self.loadActionsInternal()
        self.tabStatus.loadActions(items.get(0, []))
        self.tabDiagnostic.loadActions(items.get(1, []))
        self.tabCure.loadActions(items.get(2, []))
        self.tabMisc.loadActions(items.get(3, []))
        self.modelActionsSummary.regenerate()
        self.tabCash.modelAccActions.regenerateOnLoad()
        for i in [0,1,2,3]:
            for item in items.get(i, []):
                item.record._dirty = False


    def loadActionsInternal(self):
        # массовая загрузка действий в событие
        eventId = self.itemId()
        db = QtGui.qApp.db
        table = db.table('Action')
        tableActionType = db.table('ActionType')
        tableQuery = table.leftJoin(tableActionType, tableActionType['id'].eq(table['actionType_id']))
        cond = [table['deleted'].eq(0), tableActionType['deleted'].eq(0)]
        if eventId:
            cond.append(table['event_id'].eq(eventId))
        if self.excludeList:
            cond.append(table['actionType_id'].notInlist(self.excludeList))

        records = db.getRecordList(tableQuery, 'Action.*', cond, 'idx, id')
        ATset = set()
        personSet = set()
        personSpecialityMap = dict()
        actionTypeMap = dict()
        for record in records:
            ATset.add(forceRef(record.value('actionType_id')))
            personId = forceRef(record.value('person_id'))
            personSet.add(personId)
            actionTypeMap[forceRef(record.value('id'))] = forceRef(record.value('actionType_id'))

        # массовое кэширование ТД для события
        CActionTypeCache.getByIds(ATset)

        # массовая загрузка специальностей исполнителей действий
        if personSet:
            db = QtGui.qApp.db
            tablePerson = db.table('Person')
            recordsSpeciality = db.getRecordList(tablePerson, [tablePerson['id'], tablePerson['speciality_id']],
                                    [tablePerson['deleted'].eq(0), tablePerson['id'].inlist(personSet)])
            for record in recordsSpeciality:
                specialityId = forceRef(record.value('speciality_id'))
                personId = forceRef(record.value('id'))
                personSpecialityMap[personId] = specialityId

        # массовая загрузка связей действий с резервированием ЛСиИМН
        tableActionNR = db.table('Action_NomenclatureReservation')
        nomenclatureReservationRecords = db.getRecordList(tableActionNR, '*',
                                                          [tableActionNR['action_id'].inlist(actionTypeMap.keys())])
        mapReservation = {}
        for recordReservation in nomenclatureReservationRecords:
            actionId = forceRef(recordReservation.value('action_id'))
            reservation_id = forceRef(recordReservation.value('reservation_id'))
            mapReservation[actionId] = reservation_id

        # массовая загрузка элементов плана выполнения
        mapExecutionPlan = {}
        tableActionEPI = db.table('ActionExecutionPlan_Item')
        executionPlanItemRecords = db.getRecordList(tableActionEPI, '*',
                                                    [tableActionEPI['action_id'].inlist(actionTypeMap.keys())])
        for recordExecutionPlan in executionPlanItemRecords:
            actionId = forceRef(recordExecutionPlan.value('action_id'))
            mapExecutionPlan.setdefault(actionId, []).append(recordExecutionPlan)

        # массовая загрузка прикрепленных файлов
        mapFileAttach = {}
        mapFileAttachIdToActionId = {}
        mapFileAttachSign = {}
        mapFileAttachPT = {}
        tableFileAttach = db.table('Action_FileAttach')
        fileAttachRecords = db.getRecordList(tableFileAttach, '*',
                                             [tableFileAttach['master_id'].inlist(actionTypeMap.keys()),
                                              tableFileAttach['deleted'].eq(0)])
        for recordFileAttach in fileAttachRecords:
            actionId = forceRef(recordFileAttach.value('master_id'))
            fileAttachId = forceRef(recordFileAttach.value('id'))
            mapFileAttachIdToActionId[fileAttachId] = actionId
            mapFileAttach.setdefault(actionId, []).append(recordFileAttach)

        if mapFileAttachIdToActionId:
            # массовая загрузка дополнительных подписей
            tableFileAttachSign = db.table('Action_FileAttach_Signature')
            fileAttachSignRecords = db.getRecordList(tableFileAttachSign, '*',
                                                 [tableFileAttachSign['master_id'].inlist(mapFileAttachIdToActionId.keys()),
                                                  tableFileAttachSign['deleted'].eq(0)])
            for recordFileAttachSign in fileAttachSignRecords:
                fileAttachId = forceRef(recordFileAttachSign.value('master_id'))
                actionId = mapFileAttachIdToActionId.get(fileAttachId)
                mapFileAttachSign.setdefault(actionId, []).append((fileAttachId, recordFileAttachSign))

            # массовая загрузка шаблонов печати прикрепленных файлов
            tableFileAttachPT = db.table('Action_FileAttach_PrintTemplate')
            fileAttachPTRecords = db.getRecordList(tableFileAttachPT, '*',
                                                     [tableFileAttachPT['id'].inlist(mapFileAttachIdToActionId.keys())])
            for recordFileAttachPT in fileAttachPTRecords:
                fileAttachId = forceRef(recordFileAttachPT.value('id'))
                actionId = mapFileAttachIdToActionId.get(fileAttachId)
                mapFileAttachPT.setdefault(actionId, []).append((fileAttachId, recordFileAttachPT))

        # массовая загрузка свойств действий
        tableActionProperty = db.table('ActionProperty')
        APRecords = db.getRecordList(tableActionProperty, '*',
                                     [tableActionProperty['action_id'].inlist(actionTypeMap.keys()),
                                      tableActionProperty['deleted'].eq(0)])
        mapValuesTable = {}
        mapProperties = {}
        mapValues = {}
        for propertyRecord in APRecords:
            propertyTypeId = forceRef(propertyRecord.value('type_id'))
            actionId = forceRef(propertyRecord.value('action_id'))
            actionType = CActionTypeCache.getById(actionTypeMap[actionId])
            if actionType.propertyTypeIdPresent(propertyTypeId):
                tableName = actionType.getPropertyTypeById(propertyTypeId).tableName
                mapValuesTable.setdefault(tableName, []).append(forceRef(propertyRecord.value('id')))
                mapProperties.setdefault(actionId, []).append(propertyRecord)

        for key in mapValuesTable.keys():
            valueTable = db.table(key)
            valueRecords = db.getRecordList(valueTable, '*', valueTable['id'].inlist(mapValuesTable[key]))
            for rec in valueRecords:
                mapValues.setdefault(forceRef(rec.value('id')), []).append(rec)
        items = dict()
        for record in records:
            actionId = forceRef(record.value('id'))
            actionType = CActionTypeCache.getById(actionTypeMap[actionId])
            propertyRecords = mapProperties.get(actionId, [])
            reservationId = mapReservation.get(actionId, -1)
            executionPlanRecord = mapExecutionPlan.get(actionId, [])
            fileAttachRecords = mapFileAttach.get(actionId, [])
            fileAttachSignRecords = mapFileAttachSign.get(actionId, [])
            fileAttachPTRecords = mapFileAttachPT.get(actionId, [])
            personId = forceRef(record.value('person_id'))
            specialityId = personSpecialityMap.get(personId, -1)
            mapActionValueRecords = dict()
            for prop in propertyRecords:
                mapActionValueRecords[forceRef(prop.value('id'))] = mapValues.get(forceRef(prop.value('id')), [])
            addition_data = {"propertyRecords": propertyRecords,
                             "valueRecords": mapActionValueRecords,
                             "reservationId": reservationId,
                             "executionPlanRecord": executionPlanRecord,
                             "fileAttachRecords": fileAttachRecords,
                             "fileAttachSignRecords": fileAttachSignRecords,
                             "fileAttachPTRecords": fileAttachPTRecords,
                             "specialityId": specialityId}
            action = CAction(actionType=actionType, record=record, addition_data=addition_data)
            items.setdefault(action.getType().class_, []).append(CActionRecordItem(action.getRecord(), action))

        return items


    def getDiagnosticIdList(self, clientId):
        diagnosticIdList = []
        if clientId:
            date = QDate.currentDate()
            db = QtGui.qApp.db
            tableDiagnosis = db.table('Diagnosis')
            tableDiagnostic = db.table('Diagnostic')
            tableRBDispanser = db.table('rbDispanser')
            cond = [tableDiagnosis['client_id'].eq(clientId),
                    tableDiagnosis['deleted'].eq(0),
                    tableDiagnostic['deleted'].eq(0),
                    tableDiagnostic['dispanser_id'].isNotNull(),
                    db.joinOr([db.joinAnd([tableDiagnostic['endDate'].isNotNull(), tableDiagnostic['endDate'].le(date)]),
                               db.joinAnd([tableDiagnostic['endDate'].isNull(), tableDiagnostic['setDate'].le(date)])]),
                    ]
            queryTable = tableDiagnosis.innerJoin(tableDiagnostic, tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']))
            queryTable = queryTable.innerJoin(tableRBDispanser, tableRBDispanser['id'].eq(tableDiagnostic['dispanser_id']))
            cond.append(u'''NOT EXISTS(SELECT DC.id
                                   FROM Diagnostic AS DC
                                   INNER JOIN rbDispanser AS rbDP ON rbDP.id = DC.dispanser_id
                                   WHERE DC.diagnosis_id = Diagnosis.id AND DC.endDate <= %s AND DC.deleted = 0 AND rbDP.name LIKE '%s')'''%(db.formatDate(date), u'%снят%'))
            diagnosticIdList = db.getDistinctIdList(queryTable, [u'Diagnostic.id'], where=cond, order='Diagnostic.endDate DESC')
        return diagnosticIdList
    
    
    def saveTempInvalid(self):
        if hasattr(self, 'grpDisability'):
            self.grpDisability.save()
        if hasattr(self, 'grpTempInvalid'):
            self.grpTempInvalid.save()
        if hasattr(self, 'grpAegrotat'):
            self.grpAegrotat.save()
        if hasattr(self, 'grpVitalRestriction'):
            self.grpVitalRestriction.save()
    
    
    def checkCompletedEventsOMS(self):
        u"""
        Контроль законченных случаев по ОМС для сокращения 307-й ошибки в ЛПУ.
        Этот метод выполняет ряд проверок, чтобы определить, соответствует ли текущее событие критериям,
        чтобы запустить контроль.
        Если все эти проверки пройдены и соответствующая запись найдена, метод создает и отображает CCompletedEventsOMSWidget.
        return:
            Найденный eventId, если виджет принят; в противном случае False.
        """
        if not getEventTypeCheckCompletedEventsOMS(self.eventTypeId):
            return False
        
        if not getEventTypeForm(self.eventTypeId) in (u'025', u'030', u'043'):
            return False
        
        if not hasattr(self.tabNotes, 'chkExpose') or not self.tabNotes.chkExpose.isChecked(): 
            return False
        
        if not self.eventDate:
            return False
        
        if not hasattr(self, 'cmbOrder') or self.cmbOrder.currentIndex()+1 != 1:
            return False
        
        if not hasattr(self, 'cmbContract') or CFinanceType.getCode(self.eventFinanceId) != 2:
            return False
        
        db = QtGui.qApp.db
        tableAccountItem = db.table('Account_Item')
        cond = [tableAccountItem['deleted'].eq(0),
                tableAccountItem['refuseType_id'].isNull(),
                tableAccountItem['event_id'].eq(self.itemId())
                ]
        record = db.getRecordEx(tableAccountItem, 'id', cond)
        if record:
            return False
        
        tableService = db.table('rbService')
        tableActionService = db.table('ActionType_Service')
        existRecord = None
        actionTypes = []
        for actionTab in self.getActionsTabsList():
            serviceIds = []
            model = actionTab.tblAPActions.model()
            for record, action in model.items():
                if forceDate(record.value('endDate')):
                    if forceInt(record.value('status')) == 2:
                        if not forceInt(record.value('org_id')):
                            actionType = forceInt(record.value('actionType_id'))
                            if not actionType in actionTypes:
                                actionServiceRecords = db.getRecordList(tableActionService, '*', tableActionService['master_id'].eq(actionType))
                                actionTypes.append(actionType)
                                for actionServiceRecord in actionServiceRecords:
                                    if CFinanceType.getCode(forceInt(actionServiceRecord.value('finance_id'))) in (0, 2):
                                        serviceId = forceInt(actionServiceRecord.value('service_id'))
                                        if serviceId not in serviceIds:
                                            serviceIds.append(serviceId)
            if serviceIds:
                cond = [
                    tableService['id'].inlist(serviceIds),
                    db.joinAnd([tableService['name'].notlike(u'%беремен%'),
                                tableService['name'].notlike(u'%обращение по поводу%'),
                                tableService['name'].notlike(u'%патронаж%'),
                                tableService['name'].notlike(u'%инокраев%')]),
                    db.joinOr([u"""
                    (rbService.infis LIKE 'B01%' AND SUBSTRING(rbService.infis, 5, 3) IN 
                    ('001','002','004','005','007','008','010','014','015','018','023','025',
                    '026','027','028','029','031','037','038','040','047','048','049','050',
                    '053','057','058','063','064','065','067'))""",
                    u"""(rbService.infis LIKE 'B02%' AND SUBSTRING(rbService.infis, 5, 3) IN ('001','031','047'))"""])
                ]
                existRecord = db.getRecordEx(tableService, 'id', cond)
                if existRecord:
                    break
        if not existRecord:
            return False
        
        
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        tableDiagnosis = db.table('Diagnosis')
        tableDiagnostic = db.table('Diagnostic')
        tableRBDiagnosisType = db.table('rbDiagnosisType')
        tablePerson = db.table('Person')
        tableRBSpeciality = db.table('rbSpeciality')
        tableOrgStructure = db.table('OrgStructure')
        tableAction = db.table('Action')
        tableActionType = db.table('ActionType')
        tableRBFinance = db.table('rbFinance')
        
        table = tableEvent.leftJoin(tableAccountItem, tableEvent['id'].eq(tableAccountItem['event_id']))
        table = table.leftJoin(tableDiagnostic, tableEvent['id'].eq(tableDiagnostic['event_id']))
        table = table.leftJoin(tableDiagnosis, tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']))
        table = table.innerJoin(tableRBDiagnosisType, tableRBDiagnosisType['id'].eq(tableDiagnostic['diagnosisType_id']))
        table = table.leftJoin(tablePerson, tablePerson['id'].eq(tableEvent['execPerson_id']))
        table = table.leftJoin(tableRBSpeciality, tableRBSpeciality['id'].eq(tablePerson['speciality_id']))
        table = table.leftJoin(tableOrgStructure, tableOrgStructure['id'].eq(tablePerson['orgStructure_id']))
        table = table.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
        table = table.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
        table = table.leftJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
        table = table.leftJoin(tableActionService, tableActionService['master_id'].eq(tableActionType['id']))
        table = table.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableActionService['finance_id']))
        table = table.leftJoin(tableService, tableService['id'].eq(tableActionService['service_id']))
        
        cols = [tableEvent['id'],
                tableEvent['execDate'],
                tableDiagnosis['MKB'],
                tableRBSpeciality['name'].alias('specialityName'),
                tablePerson['lastName'],
                tablePerson['firstName'],
                tablePerson['patrName'],
                tableOrgStructure['name'].alias('orgStructureName'),
                tableEventType['checkCompletedEventsOMS'],
                'MIN(Event.setDate) as setDate',
                'MIN(Action.begDate) as minBegDate',
                'MAX(Action.endDate) as maxEndDate'
                ]
        
        MKBrecord = db.getRecordEx(table, tableDiagnosis['MKB'], [tableEvent['id'].eq(self.itemId()),
                                                                    tableDiagnostic['deleted'].eq(0),
                                                                    tableRBDiagnosisType['code'].eq(1),
                                                                    tableDiagnosis['deleted'].eq(0)])
        MKB = forceString(MKBrecord.value('MKB'))
          
        clientId = self.clientId
        eventTypeId = self.eventTypeId
        date = self.eventDate
        contractId = self.cmbContract.value()
        specialityId = self.getPersonSpecialityId(self.personId)
        cond = [
            tableEvent['id'].ne(self.itemId()),
            tableEvent['client_id'].eq(clientId),
            tableEvent['eventType_id'].eq(eventTypeId),
            tableEvent['deleted'].eq(0),
            db.joinOr([tableEvent['execDate'].isNull(), tableEvent['execDate'].lt(date)]),
            u"YEAR(Event.execDate) = YEAR({0}) AND MONTH(Event.execDate) = MONTH({0})".format(db.formatDate(date)),
            tableEvent['contract_id'].eq(contractId),
            tableEvent['expose'].eq(1),
            tableAccountItem['id'].isNull(),
            tableDiagnostic['deleted'].eq(0),
            tableRBDiagnosisType['code'].eq(1),
            tableDiagnosis['deleted'].eq(0),
            tableDiagnosis['MKB'].eq(MKB),
            tableRBSpeciality['id'].eq(specialityId),
            u"""
            (rbFinance.code is NULL or rbFinance.code = 2)
            AND Action.status = 2
            AND Action.endDate is not NULL
            AND Action.org_id is NULL
            AND rbService.name NOT LIKE '%беремен%'
            AND rbService.name NOT LIKE '%обращение по поводу%'
            AND rbService.name NOT LIKE '%патронаж%'
            AND rbService.name NOT LIKE '%инокраев%'
            AND (
                (rbService.infis LIKE 'B01%' AND SUBSTRING(rbService.infis, 5, 3) IN 
                ('001','002','004','005','007','008','010','014','015','018','023','025',
                '026','027','028','029','031','037','038','040','047','048','049','050',
                '053','057','058','063','064','065','067'))
                OR
                (rbService.infis LIKE 'B02%' AND SUBSTRING(rbService.infis, 5, 3) IN ('001','031','047')))
                """
        ]
        
        record = None
        record = db.getRecordListGroupBy(table, cols, cond,"Action.event_id", 'Event.setDate', 1)
        if record:
            record = record[0]
            widget = CCompletedEventsOMSWidget(record, self.itemId(), self)
            if widget.exec_():
                return widget.eventId
        else:
            return False


    def checkMaxOccursLimit(self, actionTypeId):
        if hasattr(self, 'modelActionsSummary'):
            actionType = CActionTypeCache.getById(actionTypeId)
            count = 0
            for item in self.modelActionsSummary.items():
                if item and forceString(item.value('actionType_id')) == actionTypeId:
                    count += 1
            result = actionType.checkMaxOccursLimit(count, False)
            return result
        return False


# == столбики для редактирования характера и стадии в диагнозах


class CDiseaseCharacter(CRBInDocTableCol):
    def __init__(self, title, fieldName, width, **params):
        CRBInDocTableCol.__init__(self, title, fieldName, width, 'rbDiseaseCharacter', **params)


    def setEditorData(self, editor, value, record):
        db = QtGui.qApp.db
        MKB  = forceString(record.value('MKB'))
        codeIdList = getAvailableCharacterIdByMKB(MKB)
        table = db.table('rbDiseaseCharacter')
        editor.setTable(table.name(), not bool(codeIdList), filter=table['id'].inlist(codeIdList))
        editor.setValue(forceRef(value))


class CDiseaseStage(CRBInDocTableCol):
    def __init__(self, title, fieldName, width, **params):
        CRBInDocTableCol.__init__(self, title, fieldName, width, 'rbDiseaseStage', **params)


    def setEditorData(self, editor, value, record):
        db = QtGui.qApp.db
        MKB  = forceString(record.value('MKB'))
        characterId = forceRef(record.value('character_id'))
        characterDataCache = CRBModelDataCache.getData('rbDiseaseCharacter', True)
        characterCode = characterDataCache.getCodeById(characterId)
        enabledCharacterReations = [0]
        if MKB.startswith('Z'):
            enabledCharacterReations.append(4)
        else:
            if characterCode == '1':
                enabledCharacterReations.append(1)
            else:
                enabledCharacterReations.append(2)
            enabledCharacterReations.append(3)
        table = db.table('rbDiseaseStage')
#        editor.setTable(table.name(), MKB.startswith('Z'), filter=table['characterRelation'].inlist(enabledCharacterReations))
        editor.setTable(table.name(), True, filter=table['characterRelation'].inlist(enabledCharacterReations))
        editor.setValue(forceRef(value))


class CDiseasePhases(CRBInDocTableCol):
    def __init__(self, title, fieldName, width, **params):
        CRBInDocTableCol.__init__(self, title, fieldName, width, 'rbDiseasePhases', **params)


    def setEditorData(self, editor, value, record):
        db = QtGui.qApp.db
        MKB  = forceString(record.value('MKB'))
        characterId = forceRef(record.value('character_id'))
        characterDataCache = CRBModelDataCache.getData('rbDiseaseCharacter', True)
        characterCode = characterDataCache.getCodeById(characterId)
        enabledCharacterReations = [0]
        if MKB.startswith('Z'):
            enabledCharacterReations.append(4)
        else:
            if characterCode == '1':
                enabledCharacterReations.append(1)
            else:
                enabledCharacterReations.append(2)
            enabledCharacterReations.append(3)
        table = db.table('rbDiseasePhases')
#        editor.setTable(table.name(), MKB.startswith('Z'), filter=table['characterRelation'].inlist(enabledCharacterReations))
        editor.setTable(table.name(), True, filter=table['characterRelation'].inlist(enabledCharacterReations))
        editor.setValue(forceRef(value))


def getToxicSubstancesIdListByMKB(MKB):
    # получить список id записей Токсичных веществ в соответствии с кодом МКБ
    db = QtGui.qApp.db
    fixedMKB = MKBwithoutSubclassification(MKB)
    tableToxicSubstances = db.table('rbToxicSubstances')
    return db.getDistinctIdList(tableToxicSubstances, [tableToxicSubstances['id']], [tableToxicSubstances['MKB'].eq(fixedMKB)], order = tableToxicSubstances['name'].name())


class CToxicSubstances(CRBInDocTableCol):
    def __init__(self, title, fieldName, width, **params):
        CRBInDocTableCol.__init__(self, title, fieldName, width, 'rbToxicSubstances', **params)


    def setEditorData(self, editor, value, record):
        db = QtGui.qApp.db
        MKB = forceString(record.value('MKB'))
        toxicSubstancesIdList = getToxicSubstancesIdListByMKB(MKB)
        table = db.table('rbToxicSubstances')
        editor.setTable(table.name(), addNone=True, filter=table['id'].inlist(toxicSubstancesIdList))
        editor.setValue(forceRef(value))


# WTF? таблиы с чек-боксами уже недостаточно? mainLayout умеет рисовать линейку прокрутки? ЭТО точно должно быть в этом модуле?
class CActionsControlDialog(QtGui.QDialog, Ui_ActionsControlDialog):
    def __init__(self, parent = None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.buttonBox.addButton(u'Игнорировать', QtGui.QDialogButtonBox.RejectRole)
        self.ready = False
        self.codes = []
        self.labels = []
        self.chkBoxes = []

    def addChoise(self, code, mkb, actionType):
        if (code, mkb) not in self.codes:
            if len(self.codes):
                self.addLine()
            label = QtGui.QLabel(self)
            diag = ''
            if mkb:
                diag = u' (Диагноз %s)'%mkb
            label.setText(u'Для правила "%s"%s желательно добавить действия:'%(code, diag))
            self.mainLayout.addWidget(label)
            self.codes.append((code, mkb))
        db = QtGui.qApp.db
        actionTypeName = forceString(db.translate('ActionType', 'id', actionType, 'name'))
        chkBox = QtGui.QCheckBox(self)
        chkBox.setChecked(True)
        chkBox.setText(actionTypeName)
        self.mainLayout.addWidget(chkBox)
        self.chkBoxes.append((chkBox, actionType))
        self.ready = True
        return len(self.chkBoxes) - 1

    def addLine(self):
        line = QtGui.QFrame(self)
        line.setFrameShape(QtGui.QFrame.HLine)
        line.setFrameShadow(QtGui.QFrame.Sunken)
        #line.setObjectName(_fromUtf8("line"))
        self.mainLayout.addWidget(line)

    def getSelected(self):
        result = []
        for i in xrange(len(self.chkBoxes)):
            (chkBox, actionType) = self.chkBoxes[i]
            if chkBox.isChecked():
                result.append(i)
        return result


class CCheckActionEndDateMessageBox(QtGui.QMessageBox):
    def __init__(self, icon, title, message, buttons, parent):
        QtGui.QMessageBox.__init__(self, icon, title, message, buttons, parent)


    def on_begin(self):
        self.done(2)


    def on_out(self):
        self.done(3)


    def on_current(self):
        self.done(4)

    def on_beginAll(self):
        self.done(5)


    def on_outAll(self):
        self.done(6)


    def on_currentAll(self):
        self.done(7)


def getMedicalDiagnosisContext():
    return ['medicalDiagnosis']

class CActionTypeDialogTableModel(CActionTypeDialog):
    def __init__(self, parent, idList, skipable=True):
        CActionTypeDialog.__init__(self, parent, [
            CTextCol(u'Код', ['code'],  20),
            CTextCol(u'Наименование действия', ['name'], 40)
            ], 'ActionType', ['id'], False, None, idList, skipable)

