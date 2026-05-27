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

u"""
Санаторий
"""
from PyQt4 import QtGui
from PyQt4.QtCore import (Qt,
                          pyqtSignature,
                          SIGNAL,
                          QChar,
                          QDate,
                          QDateTime,
                          QEvent,
                          QObject,
                          QString,
                          QTime,
                         )
from library.database             import addCondLike, CTableRecordCache
from library.DialogBase           import CDialogBase
from library.PrintInfo            import CDateInfo, CInfoContext, CTimeInfo
from library.PrintTemplates       import (CPrintAction,
                                          applyTemplate,
                                          applyTemplateInt,
                                          getPrintButton,
                                          getPrintTemplates,
                                          htmlTemplate
                                         )
from library.RecordLock           import CRecordLockMixin
from library.Utils                import (calcAge,
                                          copyFields,
                                          forceBool,
                                          forceDate,
                                          forceDateTime,
                                          forceInt,
                                          forceRef,
                                          forceString,
                                          forceStringEx,
                                          forceTime,
                                          formatDate,
                                          formatName,
                                          formatRecordsCount,
                                          getAgeRangeCond,
                                          toVariant,
                                          calcAgeTuple,
                                          trim,
                                         )
from library.TableModel           import sortDataModel, sortDateTimeModel
from library.Counter import CCounterController
from Events.Action                import (CAction,
                                          CActionType,
                                          CActionTypeCache,
                                         )
from Events.ActionEditDialog      import CActionEditDialog
from Events.ActionInfo            import CActionInfo
from Events.ActionsPage           import CActionsPage
from Events.ActionStatus          import CActionStatus
from Events.ActionPropertiesTable import CActionPropertiesTableModel
from Events.ActionTypeDialog      import CActionTypeDialogTableModel
from Events.AmbCardDialog         import CAmbCardDialog
from Events.ActionsSelector       import selectActionTypes
from Resources.GroupJobAppointmentDialog import CGroupJobAppointmentDialog
from Resources.TreatmentAppointmentDialog import CTreatmentAppointmentDialog
from Events.CreateEvent           import requestNewEvent, saveTransferData
from Events.EditDispatcher        import getEventFormClass
from Events.EventEditDialog       import CEventEditDialog
from Events.EventFeedPage         import CFeedPageDialog
from Events.EventInfo             import CEventInfo, CContractInfo
from Events.InputDialog import CDateTimeInputDialog
from Events.Utils import (cutFeed,
                          getActionTypeDescendants,
                          getDiagnosisId2,
                          getActionTypeIdListByFlatCode,
                          getChiefId,
                          getEventCSGRequired,
                          getEventShowTime,
                          checkTissueJournalStatusByActions,
                          getEventPrevEventTypeId,
                          getPrevEventIdByEventTypeId, getEventCounterId
                          )
from F003.ExecPersonListEditorDialog import CExecPersonListEditorDialog
from HospitalBeds.CheckPeriodActions         import CCheckPeriodActions
from HospitalBeds.DocumentLocationListDialog import CDocumentLocationListDialog
from HospitalBeds.HospitalBedEditorDialog    import CHospitalBedEditorDialog
from HospitalBeds.HospitalizationTransferDialog import CHospitalizationTransferDialog
from HospitalBeds.HospitalBedsEvent          import CHospitalBedsEventDialog
from HospitalBeds.HospitalBedsReport         import CHospitalBedsReport, getFeedData, CFeedReportDialog, CDietList, CMealTimeList, CFinanceList, CEventListWithDopInfo
from HospitalBeds.HospitalizationEventDialog import CHospitalizationEventDialog, CFindClientInfoDialog
from HospitalBeds.HospitalizationFromQueue   import CHospitalizationFromQueue
from HospitalBeds.HospitalizationPlanningFromQueue import CHospitalizationPlanningFromQueue
from HospitalBeds.HospitalBedInfo            import CHospitalEventInfo, CHospitalBedsListInfo
from HospitalBeds.HospitalBedPlacementEditorDialog import CHospitalBedPlacementEditorDialog
from HealthResort.HealthResortModel          import (CAttendanceActionsTableModel,
                                                     CHospitalActionsTableModel,
                                                     CHealthResortModel,
                                                     CInvoluteBedsModel,
                                                     CLeavedModel,
                                                     CPresenceModel,
                                                     CQueueModel,
                                                     CReceivedModel,
                                                     CTransferModel,
                                                     CHBPatronEditorDialog,
                                                     CHospitalizationExecDialog,
                                                     CReportF001SetupDialog,
                                                    )
from HospitalBeds.DiagnosisHospitalBedsDialog import CDiagnosisHospitalBedsDialog
from Orgs.OrgStructComboBoxes     import COrgStructureModel
from Orgs.OrgComboBox             import CPolyclinicComboBox
from Orgs.Orgs                    import selectOrganisation
from Orgs.Utils                   import (COrgStructure,
                                          COrgStructureInfo,
                                         )
from RefBooks.Finance.Info        import CFinanceInfo
from RefBooks.Menu.List           import CGetRBMenu
from Registry.AmbCardMixin        import CAmbCardMixin
from Registry.Utils               import (CCheckNetMixin,
                                          formatClientString,
                                          getClientInfo,
                                          getClientInfoEx,
                                          getClientPhonesEx,
                                          canAddActionToExposedEvent,
                                         )
from Registry.StatusObservationClientEditor import CStatusObservationClientEditor
from Registry.ClientVaccinationCard         import openClientVaccinationCard
from Registry.UpdateEventTypeByEvent   import CUpdateEventTypeByEvent
from Reports.ReportBase           import CReportBase, createTable
from Reports.ReportView           import CReportViewDialog
from Reports.ReportThermalSheet   import CReportThermalSheet
from Reports.StationaryTallySheetMoving import CStationaryTallySheetMoving
from Reports.HospitalBedProfileListDialog import CHospitalBedProfileListDialog
from Reports.StationaryF007       import (CStationaryF007ClientList,
                                          CStationaryF007Moving,
                                         )
from Reports.StationaryF007DS     import (CStationaryF007DSClientList,
                                          CStationaryF007DSMoving,
                                         )
from Reports.Utils                import dateRangeAsStr, updateLIKE
from Users.Rights                 import (urAdmin,
                                          urEditCheckPeriodActions,
                                          urEditLocationCard,
                                          urHBCanChangeOrgStructure,
                                          urHBEditClientInfo,
                                          urHBEditCurrentDateFeed,
                                          urHBEditEvent,
                                          urHBEditHospitalBed,
                                          urHBEditObservationStatus,
                                          urHBEditPatron,
                                          urHBEditThermalSheet,
                                          urHBFeed,
                                          urHBHospitalization,
                                          urHBLeaved,
                                          urHBTransfer,
                                          urHBPlanning,
                                          urHBReadClientInfo,
                                          urHBReadEvent,
                                          urHospitalTabPlanning,
                                          urHospitalTabReceived,
                                          urLeavedTabPresence,
                                          urReadCheckPeriodActions,
                                          urRegTabReadLocationCard,
                                          urRegTabReadAmbCard,
                                          urRegTabWriteAmbCard,
                                          urEditEventJournalOfPerson,
                                          urGroupEditorLocatAccountDocument,
                                          urUpdateEventTypeByEvent,
                                          urHBEditReceivedMKB,
                                          urHBActionEdit,
                                          urCanReadClientVaccination,
                                          urCanEditClientVaccination,
                                          urAccessTreatmentAppointment,
                                          urNomenclatureExpenseLaterDate,
                                          urHBEditAction
                                         )
from HospitalBeds.RelatedEventListDialog       import CRelatedEventListDialog
from ThermalSheet.TemperatureListEditor import CTemperatureListEditorDialog
from ThermalSheet.TemperatureListGroupEditor import CTemperatureListGroupEditorDialog
from Stock.GroupClientInvoice import CGroupClientInvoice
from HospitalBeds.temperatureList_html import CONTENT

from Ui_HealthResort import Ui_HealthResortDialog


class CHealthResortDialog(CDialogBase, CAmbCardMixin, CCheckNetMixin, CRecordLockMixin, Ui_HealthResortDialog):
    mapActionStatusToDateField = {CActionStatus.started  : 'begDate',
                                  CActionStatus.finished : 'endDate',
                                  CActionStatus.appointed: 'directionDate',
                                 }

    @pyqtSignature('')
    def on_tblAmbCardStatusActions_popupMenuAboutToShow(self): CAmbCardMixin.on_tblAmbCardStatusActions_popupMenuAboutToShow(self)
    @pyqtSignature('')
    def on_tblAmbCardDiagnosticActions_popupMenuAboutToShow(self): CAmbCardMixin.on_tblAmbCardDiagnosticActions_popupMenuAboutToShow(self)
    @pyqtSignature('')
    def on_tblAmbCardCureActions_popupMenuAboutToShow(self): CAmbCardMixin.on_tblAmbCardCureActions_popupMenuAboutToShow(self)
    @pyqtSignature('')
    def on_tblAmbCardMiscActions_popupMenuAboutToShow(self): CAmbCardMixin.on_tblAmbCardMiscActions_popupMenuAboutToShow(self)
    @pyqtSignature('')
    def on_actAmbCardActionTypeGroupId_triggered(self): CAmbCardMixin.on_actAmbCardActionTypeGroupId_triggered(self)
    @pyqtSignature('')
    def on_actAmbCardOpenActionELMK_triggered(self): CAmbCardMixin.on_actAmbCardOpenActionELMK_triggered(self)
    @pyqtSignature('QModelIndex')
    def on_tblAmbCardStatusActions_doubleClicked(self, *args): CAmbCardMixin.on_tblAmbCardStatusActions_doubleClicked(self, *args)
    @pyqtSignature('QModelIndex')
    def on_tblAmbCardDiagnosticActions_doubleClicked(self, *args): CAmbCardMixin.on_tblAmbCardDiagnosticActions_doubleClicked(self, *args)
    @pyqtSignature('QModelIndex')
    def on_tblAmbCardCureActions_doubleClicked(self, *args): CAmbCardMixin.on_tblAmbCardCureActions_doubleClicked(self, *args)
    @pyqtSignature('QModelIndex')
    def on_tblAmbCardMiscActions_doubleClicked(self, *args): CAmbCardMixin.on_tblAmbCardMiscActions_doubleClicked(self, *args)
    @pyqtSignature('int')
    def on_cmbAmbCardDiagnosticsSpeciality_currentIndexChanged(self, *args): CAmbCardMixin.on_cmbAmbCardDiagnosticsSpeciality_currentIndexChanged(self, *args)
    @pyqtSignature('QAbstractButton*')
    def on_cmdAmbCardDiagnosticsButtonBox_clicked(self, *args): CAmbCardMixin.on_cmdAmbCardDiagnosticsButtonBox_clicked(self, *args)
    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAmbCardDiagnostics_currentRowChanged(self, *args): CAmbCardMixin.on_selectionModelAmbCardDiagnostics_currentRowChanged(self, *args)
    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAmbCardVisits_currentRowChanged(self, *args): CAmbCardMixin.on_selectionModelAmbCardVisits_currentRowChanged(self, *args)
    @pyqtSignature('int')
    def on_tabAmbCardDiagnosticDetails_currentChanged(self, *args): CAmbCardMixin.on_tabAmbCardDiagnosticDetails_currentChanged(self, *args)
    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAmbCardDiagnosticsActions_currentRowChanged(self, *args): CAmbCardMixin.on_selectionModelAmbCardDiagnosticsActions_currentRowChanged(self, *args)
    @pyqtSignature('')
    def on_actDiagnosticsShowPropertyHistory_triggered(self): CAmbCardMixin.on_actDiagnosticsShowPropertyHistory_triggered(self)
    @pyqtSignature('')
    def on_actDiagnosticsShowPropertiesHistory_triggered(self): CAmbCardMixin.on_actDiagnosticsShowPropertiesHistory_triggered(self)
    @pyqtSignature('int')
    def on_tabAmbCardContent_currentChanged(self, *args): CAmbCardMixin.on_tabAmbCardContent_currentChanged(self, *args)
    @pyqtSignature('')
    def on_actAmbCardPrintEvents_triggered(self): CAmbCardMixin.on_actAmbCardPrintEvents_triggered(self)
    @pyqtSignature('int')
    def on_actAmbCardPrintCaseHistory_printByTemplate(self, *args): CAmbCardMixin.on_actAmbCardPrintCaseHistory_printByTemplate(self, *args)
    @pyqtSignature('')
    def on_mnuAmbCardPrintActions_aboutToShow(self): CAmbCardMixin.on_mnuAmbCardPrintActions_aboutToShow(self)
    @pyqtSignature('int')
    def on_actAmbCardPrintAction_printByTemplate(self, *args): CAmbCardMixin.on_actAmbCardPrintAction_printByTemplate(self, *args)
    @pyqtSignature('')
    def on_actAmbCardPrintActions_triggered(self): CAmbCardMixin.on_actAmbCardPrintActions_triggered(self)
    @pyqtSignature('')
    def on_actAmbCardCopyAction_triggered(self): CAmbCardMixin.on_actAmbCardCopyAction_triggered(self)
    @pyqtSignature('int')
    def on_actAmbCardPrintActionsHistory_printByTemplate(self, *args): CAmbCardMixin.on_actAmbCardPrintActionsHistory_printByTemplate(self, *args)
    @pyqtSignature('QAbstractButton*')
    def on_cmdAmbCardStatusButtonBox_clicked(self, *args): CAmbCardMixin.on_cmdAmbCardStatusButtonBox_clicked(self, *args)
    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAmbCardStatusActions_currentRowChanged(self, *args): CAmbCardMixin.on_selectionModelAmbCardStatusActions_currentRowChanged(self, *args)
    @pyqtSignature('')
    def on_actStatusShowPropertyHistory_triggered(self): CAmbCardMixin.on_actStatusShowPropertyHistory_triggered(self)
    @pyqtSignature('')
    def on_actStatusShowPropertiesHistory_triggered(self): CAmbCardMixin.on_actStatusShowPropertiesHistory_triggered(self)
    @pyqtSignature('QAbstractButton*')
    def on_cmdAmbCardDiagnosticButtonBox_clicked(self, *args): CAmbCardMixin.on_cmdAmbCardDiagnosticButtonBox_clicked(self, *args)
    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAmbCardDiagnosticActions_currentRowChanged(self, *args): CAmbCardMixin.on_selectionModelAmbCardDiagnosticActions_currentRowChanged(self, *args)
    @pyqtSignature('')
    def on_actDiagnosticShowPropertyHistory_triggered(self): CAmbCardMixin.on_actDiagnosticShowPropertyHistory_triggered(self)
    @pyqtSignature('')
    def on_actDiagnosticShowPropertiesHistory_triggered(self): CAmbCardMixin.on_actDiagnosticShowPropertiesHistory_triggered(self)
    @pyqtSignature('QAbstractButton*')
    def on_cmdAmbCardCureButtonBox_clicked(self, *args): CAmbCardMixin.on_cmdAmbCardCureButtonBox_clicked(self, *args)
    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAmbCardCureActions_currentRowChanged(self, *args): CAmbCardMixin.on_selectionModelAmbCardCureActions_currentRowChanged(self, *args)
    @pyqtSignature('')
    def on_actCureShowPropertyHistory_triggered(self): CAmbCardMixin.on_actCureShowPropertyHistory_triggered(self)
    @pyqtSignature('')
    def on_actCureShowPropertiesHistory_triggered(self): CAmbCardMixin.on_actCureShowPropertiesHistory_triggered(self)
    @pyqtSignature('QAbstractButton*')
    def on_cmdAmbCardVisitButtonBox_clicked(self, *args): CAmbCardMixin.on_cmdAmbCardVisitButtonBox_clicked(self, *args)
    @pyqtSignature('')
    def on_actAmbCardPrintVisits_triggered(self): CAmbCardMixin.on_actAmbCardPrintVisits_triggered(self)
    @pyqtSignature('QAbstractButton*')
    def on_cmdAmbCardMiscButtonBox_clicked(self, *args): CAmbCardMixin.on_cmdAmbCardMiscButtonBox_clicked(self, *args)
    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAmbCardMiscActions_currentRowChanged(self, *args): CAmbCardMixin.on_selectionModelAmbCardMiscActions_currentRowChanged(self, *args)
    @pyqtSignature('')
    def on_actMiscShowPropertyHistory_triggered(self): CAmbCardMixin.on_actMiscShowPropertyHistory_triggered(self)
    @pyqtSignature('')
    def on_actMiscShowPropertiesHistory_triggered(self): CAmbCardMixin.on_actMiscShowPropertiesHistory_triggered(self)
    @pyqtSignature('')
    def on_tblAmbCardSurveyActions_popupMenuAboutToShow(self): CAmbCardMixin.on_tblAmbCardSurveyActions_popupMenuAboutToShow(self)
    @pyqtSignature('QModelIndex')
    def on_tblAmbCardSurveyActions_doubleClicked(self, *args): CAmbCardMixin.on_tblAmbCardSurveyActions_doubleClicked(self, *args)
    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAmbCardSurveyActions_currentRowChanged(self, *args): CAmbCardMixin.on_selectionModelAmbCardSurveyActions_currentRowChanged(self, *args)
    @pyqtSignature('QAbstractButton*')
    def on_cmdAmbCardSurveyButtonBox_clicked(self, *args): CAmbCardMixin.on_cmdAmbCardSurveyButtonBox_clicked(self, *args)
    @pyqtSignature('')
    def on_actSurveyShowPropertyHistory_triggered(self): CAmbCardMixin.on_actSurveyShowPropertyHistory_triggered(self)
    @pyqtSignature('')
    def on_actSurveyShowPropertiesHistory_triggered(self): CAmbCardMixin.on_actSurveyShowPropertiesHistory_triggered(self)

    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        CCheckNetMixin.__init__(self)
        CRecordLockMixin.__init__(self)
        currentOrgStructureId = QtGui.qApp.currentOrgStructureId()
        orgStructureFilter = None
        if currentOrgStructureId and not (QtGui.qApp.userHasRight(urHBCanChangeOrgStructure) or QtGui.qApp.isAdmin()):
            orgStructureFilter = 'OrgStructure.id = %i'% currentOrgStructureId
        self.addModels('OrgStructure', COrgStructureModel(self, QtGui.qApp.currentOrgId(), None, None, None, orgStructureFilter))
        self.addModels('HospitalBeds', CHealthResortModel(self))
        self.addModels('InvoluteBeds',  CInvoluteBedsModel(self))
        self.addModels('Presence', CPresenceModel(self))
        self.addModels('ActionList', CHospitalActionsTableModel(self))
        self.addModels('ActionsStatus', CAttendanceActionsTableModel(self))
        self.addModels('ActionsStatusProperties', CActionPropertiesTableModel(self))
        self.addModels('ActionsDiagnostic', CAttendanceActionsTableModel(self))
        self.addModels('ActionsDiagnosticProperties', CActionPropertiesTableModel(self))
        self.addModels('ActionsCure', CAttendanceActionsTableModel(self))
        self.addModels('ActionsCureProperties', CActionPropertiesTableModel(self))
        self.addModels('ActionsMisc', CAttendanceActionsTableModel(self))
        self.addModels('ActionsMiscProperties', CActionPropertiesTableModel(self))
        self.addModels('Received', CReceivedModel(self))
        self.addModels('Transfer', CTransferModel(self))
        self.addModels('Leaved', CLeavedModel(self))
        self.addModels('Queue', CQueueModel(self))
        self.addObject('btnPrint', getPrintButton(self, ''))
        self.addObject('btnTemperatureList', QtGui.QPushButton(u'Температурный лист', self))
        self.addObject('btnTreatmentAppointment', QtGui.QPushButton(u'Циклы', self))
        self.addObject('btnFeed', QtGui.QPushButton(u'Питание', self))
        self.setupHospitalBedsMenu()
        self.setupActionListMenu()
        self.setupEditActionEventMenu()
        self.setupBtnFeedMenu()
        self.setupBtnTemperatureList()
        self.printMenu = {}
        self.setupUi(self)
        self.cmbFilterActionList.insertSpecialValue(u'Не учитывать', None, 1)
        self.cmbFilterActionList.insertSpecialValue(u'Назначено/Начато', (CActionStatus.started, CActionStatus.appointed), 1)
        self.cmbFilterActionStatus.insertSpecialValue(u'Не учитывать', None, 1)
        self.cmbFilterActionStatus.insertSpecialValue(u'Назначено/Начато', (CActionStatus.started, CActionStatus.appointed), 1)
        self.cmbFilterActionType.setAllSelectable(True)
        self._defaultOrgStructureEventTypeIdList = []
        self._isEnabledChkDefaultOrgStructure = False
        self._isChkDefaultOrgStructureVisible = False
        self._applyDefaultOrgStructureSettings()
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setModels(self.treeOrgStructure, self.modelOrgStructure, self.selectionModelOrgStructure)
        self.setModels(self.tblHospitalBeds,  self.modelHospitalBeds, self.selectionModelHospitalBeds)
        self.setModels(self.tblInvoluteBeds, self.modelInvoluteBeds, self.selectionModelInvoluteBeds)
        self.setModels(self.tblPresence,  self.modelPresence, self.selectionModelPresence)
        self.setModels(self.tblActionList,  self.modelActionList, self.selectionModelActionList)
        self.setModels(self.tblActionsStatus, self.modelActionsStatus, self.selectionModelActionsStatus)
        self.setModels(self.tblActionsStatusProperties, self.modelActionsStatusProperties, self.selectionModelActionsStatusProperties)
        self.setModels(self.tblActionsDiagnostic, self.modelActionsDiagnostic, self.selectionModelActionsDiagnostic)
        self.setModels(self.tblActionsDiagnosticProperties, self.modelActionsDiagnosticProperties, self.selectionModelActionsDiagnosticProperties)
        self.setModels(self.tblActionsCure, self.modelActionsCure, self.selectionModelActionsCure)
        self.setModels(self.tblActionsCureProperties, self.modelActionsCureProperties, self.selectionModelActionsCureProperties)
        self.setModels(self.tblActionsMisc, self.modelActionsMisc, self.selectionModelActionsMisc)
        self.setModels(self.tblActionsMiscProperties, self.modelActionsMiscProperties, self.selectionModelActionsMiscProperties)
        self.setModels(self.tblReceived,  self.modelReceived, self.selectionModelReceived)
        self.setModels(self.tblTransfer,  self.modelTransfer, self.selectionModelTransfer)
        self.setModels(self.tblLeaved,  self.modelLeaved, self.selectionModelLeaved)
        self.setModels(self.tblQueue,  self.modelQueue, self.selectionModelQueue)
        self.cmbFilterType.setTable('rbHospitalBedType', addNone=True)
        self.cmbFilterBedProfile.setTable('rbHospitalBedProfile', addNone=True)
        self.cmbFilterSchedule.setTable('rbHospitalBedShedule', addNone=True)
        self.cmbFilterAccountingSystem.setTable('rbAccountingSystem',  True)
        self.cmbFilterAccountingSystem.setValue(
                                       forceRef(QtGui.qApp.preferences.appPrefs.get('FilterAccountingSystem', 0))
                                               )
        self.cmbFilterAccountingSystemPlaning.setTable('rbAccountingSystem',  True)
        self.cmbFilterAccountingSystemPlaning.setValue(
                                       forceRef(QtGui.qApp.preferences.appPrefs.get('FilterAccountingSystem', 0))
                                               )
        self.cmbFilterPlacement.setTable('OrgStructure_Placement')
        self.cmbFilterDiet.setTable('rbDiet')
        self.cmbFilterDocumentTypeForTracking.setTable('rbDocumentTypeForTracking', specialValues=[(u'specialValueID', u'99' , u'отсутствует')])
        self.prepareDeliverFilter()
        self.cmbStatusObservation.setTable('rbStatusObservationClientType',  True)
        self.cmbFinance.setTable('rbFinance', addNone=True)
        self.cmbStatusObservationPlaning.setTable('rbStatusObservationClientType',  True)
        self.cmbFinancePlaning.setTable('rbFinance', addNone=True)
        self.cmbAttachTypePlaning.setTable('rbAttachType', addNone=True)
        self.isSrcRegion = False
        db = QtGui.qApp.db
        self.organisationCache = CTableRecordCache(db, db.forceTable('Organisation'), u'*', capacity=None)
        self.cmbSrcCity.setAreaSelectable(True)
        # self.cmbSrcCity.setCode(QtGui.qApp.defaultKLADR())
        self.cmbSrcRegion.setEnabled(True)
        self.cmbEventType.setTable('EventType', True, filter=u'(EventType.medicalAidType_id IN (SELECT rbMedicalAidType.id from rbMedicalAidType where rbMedicalAidType.code IN (\'8\')))')
        self.cmbProfileDirections.setTable('rbHospitalBedProfile', addNone = False, specialValues = [(-1, u'-', u'не задано'), (0, u'0', u'не указан')])
        self.cmbActionTypePlaning.setFlatCode(u'planning%')
        self.edtFilterBegDate.canBeEmpty()
        self.edtFilterEndDate.canBeEmpty()
        self.buttonBox.addButton(self.btnFeed, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnTreatmentAppointment, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnTemperatureList, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnPrint, QtGui.QDialogButtonBox.ActionRole)
        self.btnTransfer.setShortcut(Qt.Key_F5)
        self.btnLeaved.setShortcut(Qt.Key_F8)
        self.templateNames = {
            self.tabFund: 'mHospitalBeds', 
            self.tabPresence: 'mPresence', 
            self.tabReceived: 'mReceived', 
            self.tabTransfer: 'mTransfer', 
            self.tabLeaved: 'mLeaved', 
            self.tabQueue: 'mQueue'}
        self.btnFeed.setMenu(self.mnuBtnFeed)
        self.btnTemperatureList.setMenu(self.mnuBtnTemperatureList)
        self.tblHospitalBeds.setPopupMenu(self.mnuHospitalBeds)
        self.tblPresence.setPopupMenu(self.mnuHospitalBeds)
        self.tblActionList.setPopupMenu(self.mnuActionList)
        self.tblActionsStatus.setPopupMenu(self.mnuEditActionEvent)
        self.tblActionsDiagnostic.setPopupMenu(self.mnuEditActionEvent)
        self.tblActionsCure.setPopupMenu(self.mnuEditActionEvent)
        self.tblActionsMisc.setPopupMenu(self.mnuEditActionEvent)
        self.tblActionsStatusProperties.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.tblActionsDiagnosticProperties.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.tblActionsCureProperties.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.tblActionsMiscProperties.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.tblReceived.setPopupMenu(self.mnuHospitalBeds)
        self.tblTransfer.setPopupMenu(self.mnuHospitalBeds)
        self.tblLeaved.setPopupMenu(self.mnuHospitalBeds)
        self.tblQueue.installEventFilter(self)
        self.tblQueue.setPopupMenu(self.mnuHospitalBeds)
        self.edtVoucherNumber.installEventFilter(self)
        self.reasonRenunciation()
        self.reasonRenunciateDeath()
        self.placeCallReceived()
        self.cmbInvolute.setEnabled(False)
        self.documentLocationList=[]
        self.resetFilter()
        orgStructureIndex = self.modelOrgStructure.findItemId(QtGui.qApp.currentOrgStructureId())
        self.filterAsText = ''
        self.btnLeavedEvent = False
        self.notSelectedRows = True
        if orgStructureIndex and orgStructureIndex.isValid():
            self.treeOrgStructure.setCurrentIndex(orgStructureIndex)
            self.treeOrgStructure.setExpanded(orgStructureIndex, True)
            self.firstInput = True
        else:
            self.firstInput = False
        self.__actionTypeIdListByClassPage = [None] * 4
        self.isUpdateTabWidgetFilter = False
        self.on_tabWidget_currentChanged(1)
        self.grbActionFilter.setVisible(False)
        self.cmbFilterActionList.setCurrentIndex(1)
        self.cmbFilterActionStatus.setCurrentIndex(1)
        self.tblActionsStatus.setClientInfoHidden(False)
        self.tblActionsDiagnostic.setClientInfoHidden(False)
        self.tblActionsCure.setClientInfoHidden(False)
        self.tblActionsMisc.setClientInfoHidden(False)
        self.cmbPerson.setOnlyDoctorsIfUnknowPost(True)
        self.cmbPerson.setSpecialityId(None)
        self.headerPresenceCol = self.tblPresence.horizontalHeader()
        self.headerPresenceCol.setClickable(True)
        QObject.connect(self.headerPresenceCol,
                               SIGNAL('sectionClicked(int)'),
                               self.onHeaderPresenceColClicked)
        self.headerReceivedCol = self.tblReceived.horizontalHeader()
        self.headerReceivedCol.setClickable(True)
        QObject.connect(self.headerReceivedCol,
                               SIGNAL('sectionClicked(int)'),
                               self.onHeaderReceivedColClicked)
        self.headerTransferCol = self.tblTransfer.horizontalHeader()
        self.headerTransferCol.setClickable(True)
        QObject.connect(self.headerTransferCol,
                               SIGNAL('sectionClicked(int)'),
                               self.onHeaderTransferColClicked)
        self.headerLeavedCol = self.tblLeaved.horizontalHeader()
        self.headerLeavedCol.setClickable(True)
        QObject.connect(self.headerLeavedCol,
                               SIGNAL('sectionClicked(int)'),
                               self.onHeaderLeavedColClicked)
        self.headerQueueCol = self.tblQueue.horizontalHeader()
        self.headerQueueCol.setClickable(True)
        QObject.connect(self.headerQueueCol,
                               SIGNAL('sectionClicked(int)'),
                               self.onHeaderQueueColClicked)
        QObject.connect(self.tblActionsStatus.horizontalHeader(), SIGNAL('sectionClicked(int)'), self._setActionsOrderByColumn)
        QObject.connect(self.tblActionsDiagnostic.horizontalHeader(), SIGNAL('sectionClicked(int)'), self._setActionsOrderByColumn)
        QObject.connect(self.tblActionsCure.horizontalHeader(), SIGNAL('sectionClicked(int)'), self._setActionsOrderByColumn)
        QObject.connect(self.tblActionsMisc.horizontalHeader(), SIGNAL('sectionClicked(int)'), self._setActionsOrderByColumn)
        self.tblPresence.enableColsHide()
        self.tblPresence.enableColsMove()
        self.tblActionList.enableColsHide()
        self.tblActionList.enableColsMove()
        self.tblReceived.enableColsHide()
        self.tblReceived.enableColsMove()
        self.tblTransfer.enableColsHide()
        self.tblTransfer.enableColsMove()
        self.tblLeaved.enableColsHide()
        self.tblLeaved.enableColsMove()
        self.tblQueue.enableColsHide()
        self.tblQueue.enableColsMove()
        self.tblActionsStatus.enableColsHide()
        self.tblActionsStatus.enableColsMove()
        self.tblActionsDiagnostic.enableColsHide()
        self.tblActionsDiagnostic.enableColsMove()
        self.tblActionsCure.enableColsHide()
        self.tblActionsCure.enableColsMove()
        self.tblActionsMisc.enableColsHide()
        self.tblActionsMisc.enableColsMove()
        self.getContextShortcut()
        self.hospitalBedProfileList = []
        self.on_btnContract_clicked()
        self.on_btnContractPlaning_clicked()
        self.tabWidgetFilter.removeTab(self.tabWidgetFilter.indexOf(self.tabFilterHospitalBeds))
        self.tabWidgetFilter.removeTab(self.tabWidgetFilter.indexOf(self.tabFilterEvent))


    @pyqtSignature('')
    def on_btnSelectSrcOrg_clicked(self):
        orgId = selectOrganisation(self, self.cmbSrcOrg.value(), False, filter=CPolyclinicComboBox.filter)
        self.cmbSrcOrg.updateModel()
        if orgId:
            self.cmbSrcOrg.setValue(orgId)


    @pyqtSignature('int')
    def on_cmbMKBFilter_currentIndexChanged(self, index):
        mode = bool(index)
        for widget in (self.edtMKBFrom, self.edtMKBTo):
            widget.setEnabled(mode)


    @pyqtSignature('int')
    def on_cmbSrcMKBFilter_currentIndexChanged(self, index):
        mode = bool(index)
        for widget in (self.edtSrcMKBFrom, self.edtSrcMKBTo):
            widget.setEnabled(mode)


    @pyqtSignature('int')
    def on_cmbSrcOrg_currentIndexChanged(self):
        if not self.isSrcRegion:
            orgId = self.cmbSrcOrg.value()
            okato = None
            record = self.organisationCache.get(orgId)
            if record:
                okato = forceStringEx(record.value('OKATO'))
                okato = QString(okato).left(5) if len(okato) > 5 else okato
            if self.cmbSrcRegion.value() != okato:
                self.cmbSrcRegion.setValue(okato)
        self.isSrcRegion = False


    @pyqtSignature('int')
    def on_cmbSrcCity_currentIndexChanged(self, index):
        code = self.cmbSrcCity.code()
        self.cmbSrcRegion.setKladrCode(code)


    @pyqtSignature('int')
    def on_cmbSrcRegion_currentIndexChanged(self, index):
        orgId = self.cmbSrcOrg.value()
        okato = self.cmbSrcRegion.value()
        filter = u'''Organisation.isMedical != 0'''
        if okato:
            filter += u''' AND Organisation.OKATO LIKE '%s%%' '''%(okato)
        if self.cmbSrcOrg.filter != filter:
            self.isSrcRegion = True
            self.cmbSrcOrg.setFilter(filter)
            self.isSrcRegion = True
            self.cmbSrcOrg.setValue(orgId)


    def _setActionsOrderByColumn(self, column):
        table = self.getCurrentActionsTable()
        table.setOrder(column)
        self.on_buttonBoxAction_apply()


    def setQueueWidgetVisible(self, value):
        if not self.firstInput:
            if value:
                self.isUpdateTabWidgetFilter = True
                self.tabWidgetFilter.removeTab(0)
                self.tabWidgetFilter.insertTab(0, self.tabFilterPlanning, u'Направление')
                self.tabWidgetFilter.setCurrentIndex(self.tabWidgetFilter.indexOf(self.tabFilterPlanning))
            elif self.isUpdateTabWidgetFilter:
                self.tabWidgetFilter.removeTab(0)
                self.tabWidgetFilter.insertTab(0, self.tabFilterAllParams, u'Общие параметры')
                self.tabWidgetFilter.setCurrentIndex(self.tabWidgetFilter.indexOf(self.tabFilterAllParams))
        else:
            self.tabWidgetFilter.removeTab(self.tabWidgetFilter.indexOf(self.tabFilterPlanning))
            self.tabWidgetFilter.setCurrentIndex(self.tabWidgetFilter.indexOf(self.tabFilterAllParams))


    @pyqtSignature('')
    def on_btnFinance_clicked(self):
        filter = {}
        currentDateYear = QDate.currentDate().year()
        filter['financeId'] = self.cmbFinancePlaning.value()
        filter['begDate'] = QDate(currentDateYear, 1, 1)
        filter['endDate'] = QDate(currentDateYear, 12, 31)
        filter['enableInAccounts'] = 1
        self.btnFinance.setVisible(False)
        self.cmbFinance.setVisible(False)
        self.btnContract.setVisible(True)
        self.cmbContract.setVisible(True)
        self.cmbContract.setFilter(filter)


    @pyqtSignature('')
    def on_btnContract_clicked(self):
        self.btnContract.setVisible(False)
        self.cmbContract.setVisible(False)
        self.btnFinance.setVisible(True)
        self.cmbFinance.setVisible(True)


    @pyqtSignature('')
    def on_btnFinancePlaning_clicked(self):
        filter = {}
        currentDateYear = QDate.currentDate().year()
        filter['financeId'] = self.cmbFinancePlaning.value()
        filter['begDate'] = QDate(currentDateYear, 1, 1)
        filter['endDate'] = QDate(currentDateYear, 12, 31)
        filter['enableInAccounts'] = 1
        self.btnFinancePlaning.setVisible(False)
        self.cmbFinancePlaning.setVisible(False)
        self.btnContractPlaning.setVisible(True)
        self.cmbContractPlaning.setVisible(True)
        self.cmbContractPlaning.setFilter(filter)


    @pyqtSignature('')
    def on_btnContractPlaning_clicked(self):
        self.btnContractPlaning.setVisible(False)
        self.cmbContractPlaning.setVisible(False)
        self.btnFinancePlaning.setVisible(True)
        self.cmbFinancePlaning.setVisible(True)


    @pyqtSignature('')
    def on_btnHospitalBedProfileList_clicked(self):
        self.hospitalBedProfileList = []
        self.lblHospitalBedProfileList.setText(u'не задано')
        dialog = CHospitalBedProfileListDialog(self)
        if dialog.exec_():
            self.hospitalBedProfileList = dialog.values()
            if self.hospitalBedProfileList:
                db = QtGui.qApp.db
                table = db.table('rbHospitalBedProfile')
                records = db.getRecordList(table, [table['name']], [table['id'].inlist(self.hospitalBedProfileList)])
                nameList = []
                for record in records:
                    nameList.append(forceString(record.value('name')))
                self.lblHospitalBedProfileList.setText(u', '.join(name for name in nameList if name))


    def prepareDeliverFilter(self):
        db = QtGui.qApp.db
        tableAT = db.table('ActionType')
        tableAPT = db.table('ActionPropertyType')
        table = tableAT.leftJoin(tableAPT, tableAPT['actionType_id'].eq(tableAT['id']))
        cond = [tableAT['deleted'].eq(0),
                    tableAT['flatCode'].eq('received'),
                    tableAPT['name'].eq(u'Кем доставлен')]

        self.filterDeliverByValues = [u'не задано', u'без уточнения']
        record = db.getRecordEx(table, tableAPT['valueDomain'].name(), cond)
        if record:
            domain = forceString(record.value(0))
            self.filterDeliverByValues.extend(domain.replace('\'', '').split(','))
        self.cmbFilterDeliverBy.addItems(self.filterDeliverByValues)


    def getContextShortcut(self):
        for table in [self.tblPresence, self.tblReceived, self.tblTransfer, self.tblLeaved, ]:
            self.addObject('qshcFilterEvent', QtGui.QShortcut('F7', table, self.focusFilterEvent))
            self.addObject('qshcPeriodActionsDialog', QtGui.QShortcut('F3', table, self.on_actPeriodActionsDialog_triggered))
            self.addObject('qshcOpenEvent', QtGui.QShortcut('F4', table, self.on_actOpenEvent_triggered))
            self.addObject('qshcEditClientInfo', QtGui.QShortcut('Shift+F4', table, self.on_actEditClientInfoBeds_triggered))
            self.addObject('qshcStatusObservationClient', QtGui.QShortcut('Shift+F5', table, self.on_actStatusObservationClient_triggered))
            table.installEventFilter(self)
        for table in [self.tblPresence, self.tblReceived, self.tblQueue]:
            self.addObject('qshcBTNHospitalization', QtGui.QShortcut('F9', table, self.requestNewEventQueue))
            table.installEventFilter(self)
        if table in [self.tblPresence] :
            self.addObject('qshcTemperatureListEditor', QtGui.QShortcut('F2', table, self.on_actTemperatureListEditor_triggered))
            self.qshcTemperatureListEditor.setContext(Qt.WidgetShortcut)
        for table in [self.tblHospitalBeds, self.tblPresence, self.tblReceived, self.tblTransfer, self.tblLeaved, self.tblQueue]:
            self.addObject('qshcAddAction', QtGui.QShortcut('Shift+F8', table, self.on_actAddAction_triggered))
            table.installEventFilter(self)
        for table in [self.tblActionsStatus, self.tblActionsCure, self.tblActionsMisc, self.tblActionsDiagnostic]:
            self.addObject('qshcAddActionEvent', QtGui.QShortcut('Shift+F8', table, self.on_actAddActionEvent_triggered))
            table.installEventFilter(self)
        self.addObject('qshcPeriodActionsDialog', QtGui.QShortcut('F3', self.tblQueue, self.on_actPeriodActionsDialog_triggered))
        self.addObject('qshcOpenEvent', QtGui.QShortcut('F4', self.tblQueue, self.on_actOpenEvent_triggered))
        self.addObject('qshcEditClientInfo', QtGui.QShortcut('Shift+F4', self.tblQueue, self.on_actEditClientInfoBeds_triggered))
        self.addObject('qshcFilterEventPlanning', QtGui.QShortcut('F7', self.tblQueue, self.focusFilterEventPlanning))
        self.addObject('qshcOpenPlanningEditor', QtGui.QShortcut('Shift+F3', self.tblQueue, self.on_actOpenPlanningEditor_triggered))
        self.addObject('qshcBTNPlanning', QtGui.QShortcut('Shift+F7', self.tblQueue, self.on_actPlanning_triggered))
        self.addObject('qshcStatusObservationClient', QtGui.QShortcut('Shift+F5', self.tblQueue, self.on_actStatusObservationClient_triggered))
        self.tblQueue.installEventFilter(self)
        self.qshcOpenPlanningEditor.setContext(Qt.WidgetShortcut)
        self.qshcFilterEvent.setContext(Qt.WidgetShortcut)
        self.qshcFilterEventPlanning.setContext(Qt.WidgetShortcut)
        self.qshcPeriodActionsDialog.setContext(Qt.WidgetShortcut)
        self.qshcOpenEvent.setContext(Qt.WidgetShortcut)
        self.qshcEditClientInfo.setContext(Qt.WidgetShortcut)
        self.qshcBTNHospitalization.setContext(Qt.WidgetShortcut)
        self.qshcBTNPlanning.setContext(Qt.WidgetShortcut)


    def preparePrintBtn(self,  index = 1):
        btn = self.btnPrint
        enabled = True
        if index == 1:
            menu = self.getPresenceMenu()
        else:
            menu = self.getPrintBtnMenu(index)
        if not menu:
            menu = QtGui.QMenu()
            act = menu.addAction(u'Нет шаблонов печати')
            act.setEnabled(False)
            enabled = False
        btn.setMenu(menu)
        btn.setEnabled(enabled)
        self.printMenu[index] = menu

    def getPresenceMenu(self):
        self.reportFunc = {
                      -10:[u'Сводка по пациентам без питания', self.on_actPrintAllNoFeed_triggered],
                      -9:[u'Сводка. Форма 007', self.clientListReport007],
                      -8:[u'Листок учета. Форма 007', self.movingReport007],
                      -7:[u'Сводка. Форма 007ДС', self.clientListReport007DS],
                      -6:[u'Листок учета. Форма 007ДС', self.movingReport007DS],
                      -5:[u'Листок учета с питанием', self.stationaryTallySheetMoving],
                      -4:[u'Сводка', self.printReport],
                      -3:[u'Сводка по выписке', self.reportLeaved],
                      -2:[u'Журнал', self.printJournal],
                      -1:[u'Отчет по данным температурного листа', self.getReportThermalSheet]
                      }
        if 1 in self.printMenu:
            menu = self.printMenu[1]
        else:
            menu = QtGui.QMenu()
            btn = self.btnPrint

            templates = getPrintTemplates('feed')
            templates += getPrintTemplates('mPresence')
            index = self.tabWidgetActionsClasses.currentIndex()
            if index == 0 and self.notSelectedRows:
                templates += getPrintTemplates('mPresenceActions')
            subMenuDict={}
            if templates:
                for i, template in enumerate(templates):
                    if not template.group:
                        action = CPrintAction(template.name, template.id,  self.btnPrint,  self.btnPrint)
                        menu.addAction(action)
                    else:
                        subMenu = subMenuDict.get(template.group)
                        if subMenu is None:
                            subMenu = QtGui.QMenu(template.group, self.parentWidget())
                            subMenuDict[template.group] = subMenu
                        action = CPrintAction(template.name, template.id, self.btnPrint, self.btnPrint)
                        subMenu.addAction(action)
                if subMenuDict:
                    for subMenuKey in sorted(subMenuDict.keys()):
                        menu.addMenu(subMenuDict[subMenuKey])
            else:
                menu = btn.menu()
                if not menu:
                    menu = QtGui.QMenu(btn)
                    btn.setMenu(menu)
                act = menu.addAction(u'Нет шаблонов печати')
                act.setEnabled(False)
            menu.addSeparator()
            for key in sorted(self.reportFunc):
                menu.addAction( CPrintAction(self.reportFunc[key][0],  key,  self.btnPrint,  self.btnPrint) )
        return menu


    def getPrintBtnMenu(self, index):
        self.reportFunc = {
                          -4:[u'Сводка', self.printReport]
                          }
        if index==2:
                self.reportFunc[-2] = [u'Журнал', self.printJournal]
        if index in self.printMenu:
            menu = self.printMenu[index]
        else:
            menu = QtGui.QMenu()
            subMenuDict={}
            templates = getPrintTemplates(self.templateNames[self.tabWidget.widget(index)])
            if templates:
                for i, template in enumerate(templates):
                    if not template.group:
                        action = CPrintAction(template.name, template.id, self.btnPrint, self.btnPrint)
                        menu.addAction(action)
                    else:
                        subMenu = subMenuDict.get(template.group)
                        if subMenu is None:
                            subMenu = QtGui.QMenu(template.group, self.parentWidget())
                            subMenuDict[template.group] = subMenu
                        action = CPrintAction(template.name, template.id, self.btnPrint, self.btnPrint)
                        subMenu.addAction(action)
                if subMenuDict:
                    for subMenuKey in sorted(subMenuDict.keys()):
                        menu.addMenu(subMenuDict[subMenuKey])
            else:
                act = menu.addAction(u'Нет шаблонов печати')
                act.setEnabled(False)
            menu.addSeparator()
            for key in sorted(self.reportFunc):
                menu.addAction( CPrintAction(self.reportFunc[key][0], key, self.btnPrint, self.btnPrint) )
        return menu

    def setupPrintBtnMenu(self, index):
        pass


    def _applyDefaultOrgStructureSettings(self):
        orgStructureId = QtGui.qApp.currentOrgStructureId()
        if orgStructureId:
            db = QtGui.qApp.db

            orgStructure = COrgStructure.get(orgStructureId)

            if orgStructure.type == COrgStructure.ostEmergencyDepartment:
                self._isEnabledChkDefaultOrgStructure = True
                orgStructureEventTypeIdList = db.getIdList('OrgStructure_EventType',
                                                           'eventType_id',
                                                           'master_id=%d'%orgStructureId)
                self._defaultOrgStructureEventTypeIdList = orgStructureEventTypeIdList

                self.chkDefaultOrgStructure.setChecked(bool(orgStructureEventTypeIdList))


    def eventFilter(self, watched, event):
        if watched == self.tblQueue:
            if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Space:
                event.accept()
                self.requestNewEventQueue()
                return True
        elif watched == self.tblPresence:
            if event.type() == QEvent.KeyPress and event.key() == Qt.Key_F2:
                event.accept()
                self.on_actTemperatureListEditor_triggered()
                return True
        elif watched == self.edtVoucherNumber:
            if event.type() == QEvent.MouseButtonPress:
                event.accept()
                maskLen = len(trim(self.edtVoucherNumber.inputMask())) - 1
                curPos = self.edtVoucherNumber.cursorPositionAt(event.pos())
                pos = len(trim(self.edtVoucherNumber.text()))
                if not pos or curPos == maskLen:
                    self.edtVoucherNumber.setCursorPosition(0)
                    return True
                elif curPos > pos:
                    self.edtVoucherNumber.setCursorPosition(pos)
                    return True
        return QtGui.QDialog.eventFilter(self, watched, event)


    def focusFilterEvent(self):
        self.edtFilterEventId.setFocus(Qt.ShortcutFocusReason)


    def focusFilterEventPlanning(self):
        self.edtFilterEventIdPlaning.setFocus(Qt.ShortcutFocusReason)


    def getOnHeaderColClicked(self):
        widgetIndex = self.tabWidget.currentIndex()
        return [None,
                self.onHeaderPresenceColClicked,
                self.onHeaderReceivedColClicked,
                self.onHeaderTransferColClicked,
                self.onHeaderLeavedColClicked,
                self.onHeaderQueueColClicked][widgetIndex]


    def onHeaderPresenceColClicked(self, col):
        #if col in (7, 8, 9, 12, 13, 16, 17, 18, 19, 3, 4, 20, 29):
        headerSortingCol = self.modelPresence.headerSortingCol.get(col, False)
        self.modelPresence.headerSortingCol = {}
        self.modelPresence.headerSortingCol[col] = not headerSortingCol
        if col in (12, 13, 14):
            sortDateTimeModel(self.modelPresence)
        else:
            sortDataModel(self.modelPresence)


    def onHeaderReceivedColClicked(self, col):
        #if col in (4, 5, 6, 9, 10, 11, 14, 15, 19):
        headerSortingCol = self.modelReceived.headerSortingCol.get(col, False)
        self.modelReceived.headerSortingCol = {}
        self.modelReceived.headerSortingCol[col] = not headerSortingCol
        if col in (9, 10, 11):
            sortDateTimeModel(self.modelReceived)
        else:
            sortDataModel(self.modelReceived)


    def onHeaderTransferColClicked(self, col):
        #if col in (4, 5, 6, 9, 10, 11, 16, 19):
        headerSortingCol = self.modelTransfer.headerSortingCol.get(col, False)
        self.modelTransfer.headerSortingCol = {}
        self.modelTransfer.headerSortingCol[col] = not headerSortingCol
        if col in (9, 10, 11):
            sortDateTimeModel(self.modelTransfer)
        else:
            sortDataModel(self.modelTransfer)


    def onHeaderLeavedColClicked(self, col):
        #if col in (3, 4, 5, 8, 9, 10, 11, 14, 15, 19):
        headerSortingCol = self.modelLeaved.headerSortingCol.get(col, False)
        self.modelLeaved.headerSortingCol = {}
        self.modelLeaved.headerSortingCol[col] = not headerSortingCol
        if col in (8, 9, 10):
            sortDateTimeModel(self.modelLeaved)
        else:
            sortDataModel(self.modelLeaved)


    def onHeaderQueueColClicked(self, col):
        #if col in (1, 2, 4, 7, 9, 11, 14, 15, 21):
        headerSortingCol = self.modelQueue.headerSortingCol.get(col, False)
        self.modelQueue.headerSortingCol = {}
        self.modelQueue.headerSortingCol[col] = not headerSortingCol
        if col in (7, 8, 9, 11):
            sortDateTimeModel(self.modelQueue)
        else:
            sortDataModel(self.modelQueue)


    @pyqtSignature('QModelIndex')
    def on_tblPresence_doubleClicked(self, index):
        if index.isValid():
            row = index.row()
            column = index.column()
            model = self.tblPresence.model()
            if column == model.bedColumn or column == model.placementColumn:
                isHBEditHospitalBed = QtGui.qApp.userHasRight(urHBEditHospitalBed) or QtGui.qApp.isAdmin()
                if isHBEditHospitalBed:
                    actionId         = model.getActionId(row)
                    actionTypeId     = model.getActionTypeId(row)
                    clientId         = model.getClientId(row)
                    actionTypeIdList = getActionTypeIdListByFlatCode(u'moving%')
                    if actionId and (actionTypeId and actionTypeId in actionTypeIdList) and clientId:
                        action = CAction.getActionById(actionId)
                        if action:
                            if column == model.bedColumn:
                                dialog = CHospitalBedEditorDialog(self)
                                try:
                                    sex = 0
                                    dialog.cmbHospitalBed.setPlannedEndDate(forceDate(action._record.value('plannedEndDate')))
                                    dialog.cmbHospitalBed.setBegDateAction(forceDate(action._record.value('begDate')))
                                    bedId = forceRef(action[u'койка'])
                                    if bedId:
                                        orgStructureId = forceRef(QtGui.qApp.db.translate('OrgStructure_HospitalBed', 'id', bedId, 'master_id'))
                                    else:
                                        orgStructureId = action[u'Отделение пребывания'] if (u'moving' in action._actionType.flatCode.lower()) else None
                                    sex = forceInt(QtGui.qApp.db.translate('Client', 'id', clientId, 'sex'))
                                    dialog.cmbHospitalBed.setOrgStructureId(orgStructureId)
                                    dialog.cmbHospitalBed.setBedId(bedId)
                                    dialog.cmbHospitalBed.setSex(sex)
                                    dialog.cmbHospitalBed.setDomain('')
                                    dialog.cmbHospitalBed.setValue(bedId)
                                    if dialog.exec_():
                                        bedId = dialog.values()
                                        if bedId:
                                            eventId = forceRef(action._record.value('event_id'))
                                            if CEventEditDialog(self).checkMovingBeds(clientId, eventId, actionId, forceDateTime(action._record.value('begDate')), forceDateTime(action._record.value('endDate')), None, 0, 0, None):
                                                action[u'койка'] = bedId
                                                action.save(idx=-1)
                                                self.loadDataPresence()
                                finally:
                                    dialog.deleteLater()
                            else:
                                dialog = CHospitalBedPlacementEditorDialog(self)
                                try:
                                    sex = 0
                                    dialog.cmbPlacement.setFilter('master_id = %i'%forceInt(action[u'Отделение пребывания']))
                                    placementId = forceRef(action[u'Помещение'])
                                    dialog.cmbPlacement.setValue(placementId)
                                    if dialog.exec_():
                                        placementId = dialog.values()
                                        if placementId != action[u'Помещение']:
                                            action[u'Помещение'] = placementId
                                            action.save(idx=-1)
                                            self.loadDataPresence()
                                except:
                                    pass
                                finally:
                                    dialog.deleteLater()
                        self.tblPresence.setCurrentRow(row)
                        self.updateActionsList({}, [self.getCurrentEventId(1)])
                    else:
                        self.on_actOpenEvent_triggered()
                else:
                    QtGui.QMessageBox.warning( self,
                         u'Внимание!',
                         u'Нет права на изменение данных о месте пребывания!',
                         QtGui.QMessageBox.Ok,
                         QtGui.QMessageBox.Ok)
            elif column == model.feedColumn or column == model.extraFeedColumn:
                app = QtGui.qApp
                isHBEditFeed = app.userHasRight(urHBFeed) or app.userHasRight(urHBEditCurrentDateFeed) or app.isAdmin()
                if isHBEditFeed:
                    patronId = model.getPatronId(row)
                    feedDialog = CFeedPageDialog(self)
                    feedDialog.feedWidget.setClientId(model.getClientId(row))
                    feedDialog.feedWidget.setPatronId(patronId)
                    feedDialog.feedWidget.setFilterDiet(model.getSetDate(row).date(), model.getEndDate(row).date())
                    if column == model.feedColumn:
                        feedDialog.feedWidget.tabWidget.setCurrentIndex(0)
                    else:
                        if patronId:
                            feedDialog.feedWidget.tabWidget.setCurrentIndex(1)
                        else:
                            QtGui.QMessageBox.warning( self,
                             u'Внимание!',
                             u'Нельзя назначить питание лицу по уходу, так как лицо по уходу не указано!',
                             QtGui.QMessageBox.Ok,
                             QtGui.QMessageBox.Ok)
                    if column == model.feedColumn or patronId :
                        feedDialog.setClientId(model.getClientId(row))
                        feedDialog.setEnablePatronTab(True if patronId else False)
                        feedDialog.loadData(model.getEventId(row))
                        if feedDialog.exec_():
                            self.loadDataPresence()
                    feedDialog.destroy()
                    feedDialog.deleteLater()
                    self.tblPresence.setCurrentRow(row)
                    self.updateActionsList({}, [self.getCurrentEventId(1)])
                else:
                    QtGui.QMessageBox.warning( self,
                         u'Внимание!',
                         u'Нет права на изменение данных о питании!',
                         QtGui.QMessageBox.Ok,
                         QtGui.QMessageBox.Ok)

            elif column == model.patronColumn:
                app = QtGui.qApp
                isHBEditPatron = app.userHasRight(urHBEditPatron) or app.isAdmin()
                if isHBEditPatron:
                    medicalDayBegTime = QtGui.qApp.medicalDayBegTime()
                    if not medicalDayBegTime:
                        medicalDayBegTime = QTime(9, 0)
                    if (QDateTime.fromString(model.getReceivedDate(row), "dd.MM.yyyy hh:mm").date().daysTo(QDateTime.currentDateTime().date()) == 0 and (QDateTime.fromString(model.getReceivedDate(row), "dd.MM.yyyy hh:mm").time() > medicalDayBegTime and QDateTime.currentDateTime().time() >= medicalDayBegTime)) or (QDateTime.fromString(model.getReceivedDate(row), "dd.MM.yyyy hh:mm").date().daysTo(QDateTime.currentDateTime().date()) == 1  and QDateTime.currentDateTime().time() < medicalDayBegTime):
                        self.changePatron(model, row)
                    else:
                        if app.controlHBPatronChanges() == 0:
                            buttons = QtGui.QMessageBox.Yes |QtGui.QMessageBox.No | QtGui.QMessageBox.Cancel
                        else:
                            buttons = QtGui.QMessageBox.Ok |QtGui.QMessageBox.Cancel
                        msg = u'В связи с изменениями в поле "Лицо по уходу", требуется создать дополнительное действие "Движения" в событии лечения.'
                        boxResult = QtGui.QMessageBox.question(self,
                        u'Внимание!',
                        msg,
                        buttons,
                        QtGui.QMessageBox.Cancel
                        )
                        if boxResult == QtGui.QMessageBox.Cancel:
                            pass
                        elif boxResult == QtGui.QMessageBox.No:
                            self.changePatron(model, row)
                        elif boxResult == QtGui.QMessageBox.Yes or boxResult == QtGui.QMessageBox.Ok:
                            self.transfer(model.getEventId(row), model.getClientId(row), row)
                else:
                    QtGui.QMessageBox.warning( self,
                         u'Внимание!',
                         u'Нет права на изменение данных о лице по уходу!',
                         QtGui.QMessageBox.Ok,
                         QtGui.QMessageBox.Ok)
            else:
                self.on_actOpenEvent_triggered()


    @pyqtSignature('QModelIndex')
    def on_tblReceived_doubleClicked(self, index):
        if index and index.isValid():
            column = index.column()
            if column == self.modelReceived.MKBColumn:
                self.updateReceivedMKB(index.row())
            else:
                self.on_actOpenEvent_triggered()

    def changePatron(self, model, row):
        patronId = model.getPatronId(row)
        patronDialog = CHBPatronEditorDialog(self)
        patronDialog.setClientId(model.getClientId(row))
        if patronId:
            patronDialog.setCurrentPatronId(patronId)
        if patronDialog.exec_():
            patronId = patronDialog.getPatronId()
            eventId = model.getEventId(row)
            db = QtGui.qApp.db
            tableEvent = db.table('Event')
            record = db.getRecord(tableEvent, 'id, relative_id', eventId)
            record.setValue('relative_id', patronId)
            db.updateRecord(tableEvent, record)
            actionId = model.getActionId(row)
            action = CAction.getActionById(actionId)
            action[u'Патронаж'] = u'Да' if patronId else u'Нет'
            action.save(idx=-1)
            self.loadDataPresence()
        patronDialog.destroy()
        patronDialog.deleteLater()
        self.tblPresence.setCurrentRow(row)


    def updateReceivedMKB(self, row):
        if QtGui.qApp.userHasRight(urHBEditReceivedMKB):
            eventId = self.modelReceived.getEventId(row)
            actionId = self.modelReceived.getActionId(row)
            if actionId and eventId:
                db = QtGui.qApp.db
                tableAction = db.table('Action')
                recordAction = db.getRecordEx(tableAction, u'*', [tableAction['id'].eq(actionId), tableAction['deleted'].eq(0)])
                action = CAction(record=recordAction) if recordAction else None
                if action:
                    dialog = CDiagnosisHospitalBedsDialog(self)
                    try:
                        tableEvent = db.table('Event')
                        tableClient = db.table('Client')
                        table = tableEvent.innerJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
                        recordClient = db.getRecordEx(table,
                                                      [tableClient['id'], tableClient['sex'], u'age(Client.birthDate, Event.setDate) AS clientAge'],
                                                      [tableEvent['id'].eq(eventId), tableEvent['deleted'].eq(0)])
                        if recordClient:
                            clientId = forceRef(recordClient.value('id'))
                            clientSex = forceInt(recordClient.value('sex'))
                            clientAge = forceInt(recordClient.value('clientAge'))
                        else:
                            clientId = clientSex = clientAge = None
                        MKB = forceString(recordAction.value('MKB'))
                        dialog.setAPMKBBegDateFilter(forceDate(recordAction.value('begDate')))
                        dialog.setAPMKB(MKB)
                        namePropertis = [u'диагноз направившего учереждения', u'диагноз направителя', u'диагноз при поступлении']
                        dialog.tblAPProps.model().setAction(action, clientId, clientSex, clientAge, namePropertis)
                        dialog.tblAPProps.model().reset()
                        dialog.tblAPProps.resizeRowsToContents()
                        if dialog.exec_():
                            self.loadDataReceived()
                    finally:
                        dialog.deleteLater()


    @pyqtSignature('QModelIndex')
    def on_tblTransfer_doubleClicked(self, index):
        self.on_actOpenEvent_triggered()


    @pyqtSignature('QModelIndex')
    def on_tblLeaved_doubleClicked(self, index):
        self.on_actOpenEvent_triggered()


    @pyqtSignature('QModelIndex')
    def on_tblQueue_doubleClicked(self, index):
        self.on_actOpenPlanningEditor_triggered()


    def setupActionListMenu(self):
        self.addObject('mnuActionList', QtGui.QMenu(self))
        self.addObject('actTranslateStatusActionInBegin', QtGui.QAction(u'Перевести статус действия в начато', self))
        self.mnuActionList.addAction(self.actTranslateStatusActionInBegin)


    def setupHospitalBedsMenu(self):  # + +
        self.addObject('mnuHospitalBeds', QtGui.QMenu(self))
        self.addObject('actOpenEvent', QtGui.QAction(u'Открыть обращение', self))
        self.addObject('actAddAction', QtGui.QAction(u'Добавить действие', self))
        self.addObject('actGroupJobAppointment', QtGui.QAction(u'Групповое назначение', self))
        self.addObject('actEditMKB', QtGui.QAction(u'Изменить диагноз направителя', self))
        self.addObject('actAmbCardShow',    QtGui.QAction(u'Открыть медицинскую карту', self))
        self.addObject('actEditClientInfoBeds', QtGui.QAction(u'Открыть регистрационную карточку', self))
        self.addObject('actOpenClientVaccinationCard',   QtGui.QAction(u'Открыть прививочную карту', self))
        self.addObject('actGetFeedFromMenu', QtGui.QAction(u'Назначить питание по шаблону текущему пациенту', self))
        self.addObject('actGetFeedPatronFromMenu', QtGui.QAction(u'Назначить питание по шаблону текущему лицу по уходу', self))
        self.addObject('actTemperatureListEditor', QtGui.QAction(u'Редактор температурного листа', self))
        self.addObject('actStatusObservationClient', QtGui.QAction(u'Изменить статус наблюдения пациента', self))
        self.addObject('actPlanning', QtGui.QAction(u'Поставить в очередь', self))
        self.addObject('actRelatedEventClient', QtGui.QAction(u'Показать связанные обращения', self))
        self.addObject('actPeriodActionsDialog', QtGui.QAction(u'Показать действия обращений', self))
        self.addObject('actEditClientFeatures', QtGui.QAction(u'Открыть редактор особенностей пациента', self))
        self.addObject('actEditPatronFeatures', QtGui.QAction(u'Открыть редактор особенностей лица по уходу', self))
        self.addObject('actOpenClientDocumentTrackingHistory', QtGui.QAction(u'Открыть журнал хранения учетных документов', self))
        self.addObject('actDocumentLocationGroupEditor', QtGui.QAction(u'Групповой редактор места нахождения учетного документа', self))
        self.addObject('actUpdateEventTypeByEvent', QtGui.QAction(u'Изменить тип события', self))
        self.addObject('actEventJournalOfPerson', QtGui.QAction(u'Журнал назначения лечащего врача', self))
        self.addObject('actOpenPlanningEditor', QtGui.QAction(u'Открыть редактор действия планирование', self))
        self.actStatusObservationClient.setShortcut('Shift+F5')
        self.actOpenEvent.setShortcut(Qt.Key_F4)
        self.actTemperatureListEditor.setShortcut(Qt.Key_F2)
        self.actPeriodActionsDialog.setShortcut(Qt.Key_F3)
        self.actAddAction.setShortcut('Shift+F8')
        self.mnuHospitalBeds.addAction(self.actOpenEvent)
        self.mnuHospitalBeds.addAction(self.actAddAction)
        self.mnuHospitalBeds.addAction(self.actGroupJobAppointment)
        self.mnuHospitalBeds.addAction(self.actEditMKB)
        self.mnuHospitalBeds.addAction(self.actAmbCardShow)
        self.mnuHospitalBeds.addAction(self.actOpenClientVaccinationCard)
        self.actEditClientInfoBeds.setShortcut('Shift+F4')
        self.actOpenPlanningEditor.setShortcut('Shift+F3')
        self.mnuHospitalBeds.addAction(self.actEditClientInfoBeds)
        self.mnuHospitalBeds.addAction(self.actGetFeedFromMenu)
        self.mnuHospitalBeds.addAction(self.actGetFeedPatronFromMenu)
        self.mnuHospitalBeds.addAction(self.actTemperatureListEditor)
        self.mnuHospitalBeds.addAction(self.actStatusObservationClient)
        self.mnuHospitalBeds.addAction(self.actPlanning)
        self.mnuHospitalBeds.addAction(self.actRelatedEventClient)
        self.mnuHospitalBeds.addAction(self.actPeriodActionsDialog)
        self.mnuHospitalBeds.addAction(self.actEditClientFeatures)
        self.mnuHospitalBeds.addAction(self.actEditPatronFeatures)
        self.mnuHospitalBeds.addAction(self.actOpenClientDocumentTrackingHistory)
        self.mnuHospitalBeds.addAction(self.actDocumentLocationGroupEditor)
        self.mnuHospitalBeds.addAction(self.actUpdateEventTypeByEvent)
        self.actUpdateEventTypeByEvent.setEnabled(QtGui.qApp.userHasAnyRight([urAdmin, urUpdateEventTypeByEvent]))
        self.mnuHospitalBeds.addAction(self.actEventJournalOfPerson)
        self.mnuHospitalBeds.addAction(self.actOpenPlanningEditor)


    def setupEditActionEventMenu(self):  # + +
        self.addObject('mnuEditActionEvent', QtGui.QMenu(self))
        self.addObject('actEditActionEvent', QtGui.QAction(u'Открыть обращение', self))
        self.addObject('actAddActionEvent', QtGui.QAction(u'Добавить действие', self))
        self.addObject('actAmbCardShowToAction', QtGui.QAction(u'Открыть медицинскую карту', self))
        self.addObject('actEditClientInfo', QtGui.QAction(u'Открыть регистрационную карточку', self))
        self.addObject('actEditStatusObservationClient', QtGui.QAction(u'Изменить статус наблюдения пациента', self))
        self.addObject('actTranslateStatusActionInBeginClass', QtGui.QAction(u'Перевести статус действия в начато', self))
        self.actAddActionEvent.setShortcut('Shift+F8')
        self.mnuEditActionEvent.addAction(self.actEditActionEvent)
        self.mnuEditActionEvent.addAction(self.actAddActionEvent)
        self.mnuEditActionEvent.addAction(self.actAmbCardShowToAction)
        self.mnuEditActionEvent.addAction(self.actEditClientInfo)
        self.mnuEditActionEvent.addAction(self.actEditStatusObservationClient)
        self.mnuEditActionEvent.addAction(self.actTranslateStatusActionInBeginClass)


    def setupBtnPrintMenu(self):
        self.addObject('mnuBtnPrint', QtGui.QMenu(self))
        self.addObject('actPrintReport', QtGui.QAction(u'Сводка', self))
        self.addObject('actReportLeaved', QtGui.QAction(u'Сводка по выписке', self))
        self.addObject('actPrintJournal', QtGui.QAction(u'Журнал', self))
        self.addObject('actMovingReport007', QtGui.QAction(u'Листок учета. Форма 007', self))
        self.addObject('actClientListReport007', QtGui.QAction(u'Сводка. Форма 007', self))
        self.addObject('actPrintFeedReport', QtGui.QAction(u'Порционник', self))
        self.addObject('actPrintFinanceFeedReport', QtGui.QAction(u'Порционник с финансированием', self))
        self.addObject('actPrintThermalSheet', QtGui.QAction(u'Температурный лист (список)', self))
        self.mnuBtnPrint.addAction(self.actPrintReport)
        self.mnuBtnPrint.addAction(self.actReportLeaved)
        self.mnuBtnPrint.addAction(self.actPrintJournal)
        self.mnuBtnPrint.addAction(self.actMovingReport007)
        self.mnuBtnPrint.addAction(self.actClientListReport007)
        self.mnuBtnPrint.addAction(self.actPrintFeedReport)
        self.mnuBtnPrint.addAction(self.actPrintFinanceFeedReport)
        self.mnuBtnPrint.addAction(self.actPrintThermalSheet)


    def setupBtnFeedMenu(self):  # + +
        self.addObject('mnuBtnFeed', QtGui.QMenu(self))
        self.addObject('actSelectAllFeedClient', QtGui.QAction(u'Выделить всех пациентов с питанием', self))
        self.addObject('actSelectAllNoFeedClient', QtGui.QAction(u'Выделить всех пациентов без питания', self))
        self.addObject('actSelectionRefusalToEatClient', QtGui.QAction(u'Выделить всех пациентов с отказом от питания', self))
        self.addObject('actSelectAllFeedPatron', QtGui.QAction(u'Выделить всех по уходу с питанием', self))
        self.addObject('actSelectAllNoFeedPatron', QtGui.QAction(u'Выделить всех по уходу без питания', self))
        self.addObject('actSelectionRefusalToEatPatron', QtGui.QAction(u'Выделить всех по уходу с отказом от питания', self))
        self.addObject('actSelectionAllRow', QtGui.QAction(u'Выделить всех', self))
        self.addObject('actClearSelectionRow', QtGui.QAction(u'Снять выделение', self))
        self.addObject('actProlongationFeed', QtGui.QAction(u'Пролонгация питания пациента', self))
        self.addObject('actProlongationPatronFeed', QtGui.QAction(u'Пролонгация питания по уходу', self))
        self.addObject('actGetFeedFromMenuAll', QtGui.QAction(u'Назначить питание пациенту по шаблону', self))
        self.addObject('actGetFeedPatronFromMenuAll', QtGui.QAction(u'Назначить питание по уходу по шаблону', self))
        self.mnuBtnFeed.addAction(self.actSelectAllFeedClient)
        self.mnuBtnFeed.addAction(self.actSelectAllNoFeedClient)
        self.mnuBtnFeed.addAction(self.actSelectionRefusalToEatClient)
        self.mnuBtnFeed.addAction(self.actSelectAllFeedPatron)
        self.mnuBtnFeed.addAction(self.actSelectAllNoFeedPatron)
        self.mnuBtnFeed.addAction(self.actSelectionRefusalToEatPatron)
        self.mnuBtnFeed.addAction(self.actSelectionAllRow)
        self.mnuBtnFeed.addAction(self.actClearSelectionRow)
        self.mnuBtnFeed.addAction(self.actProlongationFeed)
        self.mnuBtnFeed.addAction(self.actProlongationPatronFeed)
        self.mnuBtnFeed.addAction(self.actGetFeedFromMenuAll)
        self.mnuBtnFeed.addAction(self.actGetFeedPatronFromMenuAll)


    def setupBtnTemperatureList(self):
        self.addObject('mnuBtnTemperatureList', QtGui.QMenu(self))
        self.addObject('actTemperatureList', QtGui.QAction(u'Индивидуальный температурный лист', self))
        self.addObject('actTemperatureListGroup', QtGui.QAction(u'Ввод данных в температурные листы выбранных пациентов ', self))
        self.mnuBtnTemperatureList.addAction(self.actTemperatureList)
        self.mnuBtnTemperatureList.addAction(self.actTemperatureListGroup)


    def getOrgStructureIdList(self, treeIndex):
        treeItem = treeIndex.internalPointer() if treeIndex.isValid() else None
        return treeItem.getItemIdList() if treeItem else []


    def reasonRenunciation(self):
        self.cmbRenunciation._model.clear()
        domain = u'\'не определено\','
        renunciationType = self.cmbRenunciationAction.currentIndex()
        if renunciationType == 0:
            record = self.reasonRenunciationDomain(u'received%')
        elif renunciationType == 1:
            record = self.reasonRenunciationDomain(u'leaved%')
        elif renunciationType == 2:
            record = self.reasonRenunciationDomain(u'planning%')
        if record:
            domainR = QString(forceString(record))
            if u'*' in domainR:
                index = domainR.indexOf(u'*', 0, Qt.CaseInsensitive)
                if domainR[index - 1] != u',':
                    domainR.replace(QString('*'), QString(','))
                else:
                    domainR.remove(QChar('*'), Qt.CaseInsensitive)
            domain += domainR
        self.cmbRenunciation.setDomain(domain)


    def reasonRenunciationDomain(self, flatCode = u'received%'):
        db = QtGui.qApp.db
        tableAPT = db.table('ActionPropertyType')
        tableActionType = db.table('ActionType')
        tableAction = db.table('Action')
        cond =[tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode(flatCode)),
               tableAPT['name'].like(u'Причина отказа%'),
               tableAPT['typeName'].like(u'String')
               ]
        queryTable = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
        queryTable = queryTable.innerJoin(tableAPT, tableActionType['id'].eq(tableAPT['actionType_id']))
        record = db.getRecordEx(queryTable, [tableAPT['valueDomain']], cond)
        if record:
            return record.value(0)
        return None


    def placeCallReceived(self):
        self.cmbPlaceCall._model.clear()
        domain = u''
        record = self.placeCallReceivedDomain(u'received%')
        if record:
            domainR = QString(forceString(record))
            if u'*' in domainR:
                index = domainR.indexOf(u'*', 0, Qt.CaseInsensitive)
                if domainR[index - 1] != u',':
                    domainR.replace(QString('*'), QString(','))
                else:
                    domainR.remove(QChar('*'), Qt.CaseInsensitive)
            if domainR.indexOf(QString('\'\'')) == -1:
               domain = u'\'не определено\','
            domain += domainR
        self.cmbPlaceCall.setDomain(domain)


    def placeCallReceivedDomain(self, flatCode = u'received%'):
        db = QtGui.qApp.db
        tableAPT = db.table('ActionPropertyType')
        tableActionType = db.table('ActionType')
        tableAction = db.table('Action')
        cond =[tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode(flatCode)),
               tableAPT['name'].like(u'Место вызова%'),
               tableAPT['typeName'].like(u'String')
               ]
        queryTable = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
        queryTable = queryTable.innerJoin(tableAPT, tableActionType['id'].eq(tableAPT['actionType_id']))
        record = db.getRecordEx(queryTable, [tableAPT['valueDomain']], cond)
        if record:
            return record.value(0)
        return None


    def reasonRenunciateDeath(self, death = False):
        domain = u'\'не определено\''
        recordReceived = self.reasonRenunciateDeathDomain()
        if recordReceived:
            domainR = QString(forceString(recordReceived))
            if u'*' in domainR:
                index = domainR.indexOf(u'*', 0, Qt.CaseInsensitive)
                if domainR[index - 1] != u',':
                    domainR.replace(QString('*'), QString(','))
                else:
                    domainR.remove(QChar('*'), Qt.CaseInsensitive)
            if death:
                domainS = u''
                domainList = domainR.split(",")
                for domainI in domainList:
                    if domainI.contains(u'умер', Qt.CaseInsensitive) or domainI.contains(u'смерть', Qt.CaseInsensitive):
                        domainS += ',' + domainI
                domain += domainS
            else:
                domain += u',' + domainR
        if domain != u'':
            self.cmbDeath.setDomain(domain)


    def reasonRenunciateDeathDomain(self):
        db = QtGui.qApp.db
        tableAPT = db.table('ActionPropertyType')
        tableActionType = db.table('ActionType')
        tableAction = db.table('Action')
        cond =[ tableAction['deleted'].eq(0),
                tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode('leaved%')),
                tableAPT['name'].like(u'Исход госпитализации'),
                tableAPT['typeName'].like(u'String')
               ]
        queryTable = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
        queryTable = queryTable.innerJoin(tableAPT, tableActionType['id'].eq(tableAPT['actionType_id']))
        record = db.getRecordEx(queryTable, [tableAPT['valueDomain']], cond)
        if record:
            return record.value(0)
        return None


    def resetFilter(self):
        personId = None
        if QtGui.qApp.isGetPersonStationary():
            personId = QtGui.qApp.userId if QtGui.qApp.userSpecialityId else None
        self.cmbPerson.setValue(personId)
        self.cmbFilterAccountingSystem.setValue(None)
        self.cmbStatusObservation.setValue(None)
        self.edtFilterClientId.setText('')
        self.edtFilterEventId.setText('')
        self.edtFilterCode.setText('')
        self.cmbPersonPlaning.setValue(personId)
        self.cmbPersonExecPlaning.setValue(None)
        self.cmbOrgPlaning.setValue(None)
        self.chkFilterRegionSMOPlaning.setChecked(False)
        self.cmbFilterRegionTypeSMOPlaning.setCurrentIndex(0)
        self.cmbFilterRegionSMOPlaning.setCode('')
        self.cmbFilterAccountingSystemPlaning.setValue(None)
        self.cmbStatusObservationPlaning.setValue(None)
        self.edtFilterClientIdPlaning.setText('')
        self.edtFilterEventIdPlaning.setText('')
        self.edtFilterCode.setText('')
        self.cmbSexBed.setCurrentIndex(0)
        self.cmbFilterIsPermanent.setCurrentIndex(0)
        self.cmbFilterType.setValue(None)
        self.hospitalBedProfileList = []
        self.cmbFilterBedProfile.setValue(None)
        self.cmbFinance.setValue(None)
        self.cmbContract.setValue(None)
        self.cmbFinancePlaning.setValue(None)
        self.cmbContractPlaning.setValue(None)
        self.cmbAttachTypePlaning.setValue(None)
        self.spbBedAgeFor.setValue(0)
        self.spbBedAgeTo.setValue(self.spbBedAgeTo.maximum())
        self.cmbFilterSchedule.setValue(None)
        self.edtFilterBegDate.setDate(QDate.currentDate())
        self.edtFilterBegTime.setTime(QtGui.qApp.medicalDayBegTime())
        self.edtFilterEndDate.setDate(QDate())
        self.edtFilterEndTime.setTime(QtGui.qApp.medicalDayBegTime().addSecs(-60))
        self.edtPresenceDayValue.setValue(0)
        self.cmbFilterBusy.setCurrentIndex(0)
        self.chkInvolution.setChecked(False)
        self.cmbInvolute.setCurrentIndex(0)
        self.cmbInvolute.setEnabled(False)
        self.cmbLocationClient.setCurrentIndex(0)
        self.chkAttachTypePlaning.setChecked(False)
        self.cmbAttachTypePlaning.setCurrentIndex(0)
        self.cmbAttachTypePlaning.setEnabled(False)
        self.cmbFeed.setCurrentIndex(0)
        self.edtDateFeed.setDate(QDate.currentDate())
        self.cmbReceived.setCurrentIndex(0)
        self.cmbTransfer.setCurrentIndex(0)
        self.cmbLeaved.setCurrentIndex(0)
        self.chkStayOrgStructure.setChecked(True)
        self.edtMES.setText(u'')
        self.cmbSrcMKBFilter.setCurrentIndex(0)
        self.edtSrcMKBFrom.setText(u'A00')
        self.edtSrcMKBTo.setText(u'Z99.9')
        self.cmbMKBFilter.setCurrentIndex(0)
        self.edtMKBFrom.setText(u'A00')
        self.edtMKBTo.setText(u'Z99.9')
        self.cmbOrder.setCurrentIndex(0)
        self.cmbEventType.setValue(None)
        self.cmbPlaceCall.setCurrentIndex(0)
        self.cmbRenunciation.setCurrentIndex(0)
        self.cmbRenunciationAction.setCurrentIndex(0)
        self.cmbDeath.setCurrentIndex(0)
        self.cmbSex.setCurrentIndex(0)
        self.spbAgeFor.setValue(0)
        self.spbAgeTo.setValue(self.spbAgeTo.maximum())
        self.cmbSexPlaning.setCurrentIndex(0)
        self.spbAgeForPlaning.setValue(0)
        self.spbAgeToPlaning.setValue(self.spbAgeTo.maximum())
        self.cmbFilterActionType.setValue(0)
        self.cmbFilterActionStatus.setCurrentIndex(1)
        self.chkFilterIsUrgent.setChecked(False)
        self.edtFilterBegDatePlan.setDate(QDate())
        self.edtFilterEndDatePlan.setDate(QDate())
        self.edtFilterBegDateByStatus.setDate(QDate())
        self.edtFilterEndDateByStatus.setDate(QDate())
        self.cmbFilterPlacement.setValue(0)
        self.cmbFilterDeliverBy.setCurrentIndex(0)
        self.cmbFilterDiet.setValue(0)
        self.cmbFilterDocumentTypeForTracking.setValue(0)
        self.documentLocationList = []
        if self.chkPresenceActionActiviti.isVisible():
            self.chkPresenceActionActiviti.setChecked(True)
        self.lblDocumentLocationList.setText(u'не задано')
        self.cmbActionStatus.setValue([CActionStatus.started, CActionStatus.wait, CActionStatus.withoutResult, CActionStatus.appointed])
        self.cmbProfileDirections.setValue(None)
        self.edtEventSrcNumber.setText('')
        self.cmbActionTypePlaning.setValue(None)
        self.chkNoPlannedEndDate.setChecked(False)
        self.edtPlanActionBegDate.setDate(QDate())
        self.chkPlanActionBegDate.setChecked(False)
        self.edtPlanActionEndDate.setDate(QDate())
        self.chkPlanActionBegDate.setChecked(False)
        self.edtPlannedBegDate.setDate(QDate())
        self.chkPlannedDate.setChecked(False)
        self.edtPlannedEndDate.setDate(QDate())
        self.chkPlannedDate.setChecked(False)
        self.edtPlanWaitingBegDate.setValue(0)
        self.chkPlanWaitingPeriod.setChecked(False)
        self.edtPlanWaitingEndDate.setValue(0)
        self.chkPlanWaitingPeriod.setChecked(False)
        self.edtPlanBeforeOnsetBegDate.setValue(0)
        self.chkPlanPeriodBeforeOnset.setChecked(False)
        self.edtPlanBeforeOnsetEndDate.setValue(0)
        self.chkPlanPeriodBeforeOnset.setChecked(False)
        self.edtPlanExceedingDays.setValue(0)
        self.chkPlanExceedingDays.setChecked(False)
        self.cmbHospitalization.setCurrentIndex(0)
        self.chkHospitalization.setChecked(False)
        self.edtVoucherSerial.setText(u'')
        self.edtVoucherNumber.setText(u'')
        self.cmbSrcRegion.setValue(None)
        self.cmbSrcOrg.setValue(None)
        self.cmbSrcCity.setCode('')
        self.edtVoucherNumber.setCursorPosition(len(trim(self.edtVoucherNumber.text())))


    def resetData(self):
        self.resetFilter()
        self.getDialogParams()


    def updateHospitalBeds(self):
        code = forceStringEx(self.edtFilterCode.text())
        sexIndexBed = self.cmbSexBed.currentIndex()
        ageForBed = self.spbBedAgeFor.value()
        ageToBed = self.spbBedAgeTo.value()
        permanent = self.cmbFilterIsPermanent.currentIndex()
        type = self.cmbFilterType.value()
        bedProfile = self.cmbFilterBedProfile.value()
        schedule = self.cmbFilterSchedule.value()
        begDate = self.edtFilterBegDate.date()
        endDate = self.edtFilterEndDate.date()
        begTime = self.edtFilterBegTime.time()
        endTime = self.edtFilterEndTime.time()
        if not begTime.isNull():
            begDateTime = QDateTime(begDate, begTime)
            begDate = begDateTime
        if not endTime.isNull():
            endDateTime = QDateTime(endDate, endTime)
            endDate = endDateTime
        busy = self.cmbFilterBusy.currentIndex()
        now = QDateTime.currentDateTime().toString(Qt.ISODate)
        involution = self.cmbInvolute.currentIndex()

        db = QtGui.qApp.db
        table = db.table('OrgStructure_HospitalBed')
        tableInvolution = db.table('OrgStructure_HospitalBed_Involution')
        tableOrgStructure = db.table('OrgStructure')
        tableEx = table.join(tableOrgStructure, tableOrgStructure['id'].eq(table['master_id']))
        tableEx = tableEx.leftJoin(tableInvolution, tableInvolution['master_id'].eq(table['id']))
        orgStructureIdList = self.getOrgStructureIdList(self.treeOrgStructure.currentIndex())
        cond = [ table['master_id'].inlist(orgStructureIdList) ]
        addCondLike(cond, table['code'], code)
        if sexIndexBed:
            cond.append(table['sex'].eq(sexIndexBed))
        if ageForBed <= ageToBed:
            ageForBedCount = ageForBed
            if ageForBed == 0:
                ageList = [u'']
            else:
                ageList = []
            while ageForBedCount <= ageToBed:
                ageList.append(str(ageForBedCount))
                ageForBedCount += 1
            if ageList:
                cond.append(u'''(SELECT TRIM(BOTH 'г'
                FROM (SELECT TRIM(BOTH '-'
                FROM OrgStructure_HospitalBed.age)))) IN (%s)'''%(u','.join(age for age in ageList if age)))
        if permanent != 0:
            cond.append(table['isPermanent'].eq(permanent-1))
        if type:
            cond.append(table['type_id'].eq(type))
        if bedProfile:
            cond.append(table['profile_id'].eq(bedProfile))
        if schedule:
            cond.append(table['schedule_id'].eq(schedule))
        if begDate:
            cond.append(db.joinOr([table['begDate'].le(begDate), table['begDate'].isNull()]))
        if endDate:
            cond.append(db.joinOr([table['endDate'].ge(endDate), table['endDate'].isNull()]))
        if busy == 1:
            cond.append('NOT isHospitalBedBusy(OrgStructure_HospitalBed.id, \'%s\')' % now)
        elif busy == 2:
            cond.append('isHospitalBedBusy(OrgStructure_HospitalBed.id, \'%s\')' % now)
        if self.chkInvolution.isChecked():
            cond.append(tableInvolution['involutionType'].eq(involution + 1))
            if begDate:
                cond.append('''(OrgStructure_HospitalBed_Involution.begDate IS NULL
                               OR OrgStructure_HospitalBed_Involution. endDate IS NULL
                               OR (OrgStructure_HospitalBed_Involution.begDate >= '%s'
                               AND OrgStructure_HospitalBed_Involution. endDate <= '%s'))'''%(begDate.toString(Qt.ISODate), begDate.toString(Qt.ISODate)))
        idList = db.getIdList(tableEx, idCol=table['id'].name(),  where=cond, order='OrgStructure.name, OrgStructure_HospitalBed.idx')
        self.tblHospitalBeds.setIdList(idList)

        cnt = len(idList)
        if busy == 1:
            cntBusy = 0
        elif busy == 2:
            cntBusy = cnt
        else:
            cond = [ table['id'].inlist(idList),
                    'isHospitalBedBusy(OrgStructure_HospitalBed.id, \'%s\')' % now
                   ]
            if begDate:
                cond.append('''NOT EXISTS(SELECT OrgStructure_HospitalBed_Involution.id
                               FROM OrgStructure_HospitalBed_Involution
                               WHERE OrgStructure_HospitalBed_Involution.master_id = OrgStructure_HospitalBed.id
                               AND OrgStructure_HospitalBed_Involution.involutionType != 0
                               AND (OrgStructure_HospitalBed_Involution.begDate IS NULL
                               OR OrgStructure_HospitalBed_Involution. endDate IS NULL
                               OR (OrgStructure_HospitalBed_Involution.begDate >= '%s'
                               AND OrgStructure_HospitalBed_Involution. endDate <= '%s')))'''%(begDate.toString(Qt.ISODate), begDate.toString(Qt.ISODate)))
            cntBusy = db.getCount(table, countCol='OrgStructure_HospitalBed.id', where=cond)

        cntInvolute = 0
        cond = [table['id'].inlist(idList)
               ]
        if self.chkInvolution.isChecked():
            cond.append(tableInvolution['involutionType'].eq(involution + 1))
            if begDate:
                cond.append('''(OrgStructure_HospitalBed_Involution.begDate IS NULL
                               OR OrgStructure_HospitalBed_Involution. endDate IS NULL
                               OR (OrgStructure_HospitalBed_Involution.begDate >= '%s'
                               AND OrgStructure_HospitalBed_Involution. endDate <= '%s'))'''%(begDate.toString(Qt.ISODate), begDate.toString(Qt.ISODate)))
        tableBusy = table.innerJoin(tableInvolution, tableInvolution['master_id'].eq(table['id']))
        cntInvolute = db.getCount(tableBusy, countCol='OrgStructure_HospitalBed.id', where=cond)

        self.lblInvoluteValue.setText(str(cntInvolute))
        self.lblTotalValue.setText(str(cnt))
        self.lblFreeValue.setText(str(cnt - cntBusy - cntInvolute))
        self.lblBusyValue.setText(str(cntBusy))

        filterAsText = []
        if code: filterAsText.append(u'код : '+code)
        if permanent: filterAsText.append(u'штат : ' + unicode(self.cmbFilterIsPermanent.currentText()))
        if type:      filterAsText.append(u'тип : ' + unicode(self.cmbFilterType.currentText()))
        if bedProfile:   filterAsText.append(u'профиль : ' + unicode(self.cmbFilterBedProfile.currentText()))
        if schedule:  filterAsText.append(u'график : ' + unicode(self.cmbFilterSchedule.currentText()))
        if sexIndexBed: filterAsText.append(u'пол койки : '+unicode(['', u'М', u'Ж'][sexIndexBed]))
        if ageForBed: filterAsText.append(u'возраст койки от : '+unicode(ageForBed))
        if ageToBed:  filterAsText.append(u'возраст койки до : '+unicode(ageToBed))
        if begDate:   filterAsText.append(u'начало : ' + forceString(begDate))
        if endDate:   filterAsText.append(u'окончание : ' + forceString(endDate))
        if busy:      filterAsText.append(unicode(self.cmbFilterBusy.currentText()))
        filterAsText.append(u'отчёт составлен : ' + forceString(QDateTime.currentDateTime()))
        self.filterAsText = '\n'.join(filterAsText)


    def getCurrentEventId(self, indexWidget = 0):
        hospitalBedId = None
        if indexWidget == 0:
            hospitalBedId = self.tblHospitalBeds.currentItemId()
        elif indexWidget == 1:
            index = self.tblPresence.currentIndex()
            row = index.row()
            if row >= 0 and row < len(self.modelPresence.items):
                return self.modelPresence.getEventId(row)
        elif indexWidget == 2:
            index = self.tblReceived.currentIndex()
            row = index.row()
            if row >= 0 and row < len(self.modelReceived.items):
                return self.modelReceived.getEventId(row)
        elif indexWidget == 3:
            index = self.tblTransfer.currentIndex()
            row = index.row()
            if row >= 0 and row < len(self.modelTransfer.items):
                return self.modelTransfer.getEventId(row)
        elif indexWidget == 4:
            index = self.tblLeaved.currentIndex()
            row = index.row()
            if row >= 0 and row < len(self.modelLeaved.items):
                return self.modelLeaved.getEventId(row)
        elif indexWidget == 5:
            index = self.tblQueue.currentIndex()
            row = index.row()
            if row >= 0 and row < len(self.modelQueue.items):
                return self.modelQueue.getEventId(row)
        if hospitalBedId:
            CHospitalBedsEventDialog(self, hospitalBedId).exec_()
            self.on_selectionModelOrgStructure_currentChanged(None, None)
        return None


    def getEventSetDate(self, eventId):
        if eventId:
            db = QtGui.qApp.db
            table = db.table('Event')
            cond = [table['deleted'].eq(0),
                    '''Event.id = (SELECT getFirstEventId(%s))'''%(eventId)
                    ]
            record = db.getRecordEx(table, 'Event.setDate', cond)
            return forceDate(record.value('setDate')) if record else QDate()
        return QDate()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelOrgStructure_currentChanged(self, current, previous):
        begDays = ''
        widgetIndex = self.tabWidget.currentIndex()
        if widgetIndex == 0:
            self.updateHospitalBeds()
        elif widgetIndex == 1:
            movingOSIdList = []
            receivedOSIdList = []
            self.btnTreatmentAppointment.setEnabled(QtGui.qApp.userHasRight(urAccessTreatmentAppointment) and bool(self.getOrgStructureId(self.treeOrgStructure.currentIndex())))
            orgStructureId = self.treeOrgStructure.currentIndex()
            db = QtGui.qApp.db
            tablePlacement = db.table('OrgStructure_Placement')
            if orgStructureId:
                treeItem = orgStructureId.internalPointer() if orgStructureId.isValid() else None
                orgStructureIdList = self.getOrgStructureIdList(orgStructureId) if treeItem and treeItem._id else []
                self.cmbFilterActionList.setCurrentIndex(1)
                self.edtBegDirectionDate.setDate(self.getEventSetDate(self.getCurrentEventId(1)))
                self.edtEndDirectionDate.setDate(QDate())
                self.chkListStatus.setChecked(False)
                self.chkListDiagnostic.setChecked(True)
                self.chkListCure.setChecked(True)
                self.chkListMisc.setChecked(False)
                if orgStructureIdList:
                    tableOS = db.table('OrgStructure')
                    movingOSIdList = db.getIdList(tableOS, tableOS['id'], [tableOS['id'].inlist(orgStructureIdList), tableOS['type'].ne(4), tableOS['deleted'].eq(0)])
                    receivedOSIdList = db.getIdList(tableOS, tableOS['id'], [tableOS['id'].inlist(orgStructureIdList), tableOS['type'].eq(4), tableOS['deleted'].eq(0)])
                    if receivedOSIdList and not movingOSIdList:
                        self.chkListStatus.setChecked(True)
                        self.chkListMisc.setChecked(True)
                    if current:
                        self.cmbFilterPlacement.setFilter(tablePlacement['master_id'].inlist(orgStructureIdList))
                        self.cmbFilterPlacement.setValue(0)
                elif current:
                    self.cmbFilterPlacement.setFilter('')
                    self.cmbFilterPlacement.setValue(0)
            self.loadDataPresence()
            self.tblPresence.setFocus(Qt.TabFocusReason)
            rowCount = self.modelPresence.rowCount()
            if rowCount > 0:
                self.tblPresence.setCurrentRow(0)
            self.updateActionsList({}, [self.getCurrentEventId(1)])
            countBegDays = self.modelPresence.getBegDays()
            begDays = (u'   (' + forceString(countBegDays) + u' койко-дней)') if countBegDays else u''
        elif widgetIndex == 2:
            self.loadDataReceived()
        elif widgetIndex == 3:
            self.loadDataTransfer()
        elif widgetIndex == 4:
            self.loadDataLeaved()
            countBegDays = self.modelLeaved.getBegDays()
            begDays = (u'   (' + forceString(countBegDays) + u' койко-дней)') if countBegDays else u''
        elif widgetIndex == 5:
            self.loadDataQueue()
        self.lblCountRecordList.setText(formatRecordsCount(self.getCurrentWidgetRowCount(self.tabWidget.currentIndex())) + begDays)


    def getDialogParams(self):
        self.dialogParams = {}
        if self.tabWidget.currentIndex() != self.tabWidget.indexOf(self.tabQueue):
            self.dialogParams['filterBegDate'] = self.edtFilterBegDate.date()
            self.dialogParams['filterEndDate'] = self.edtFilterEndDate.date()
            self.dialogParams['filterBegTime'] = self.edtFilterBegTime.time()
            self.dialogParams['filterEndTime'] = self.edtFilterEndTime.time()
            self.dialogParams['leavedIndex']   = self.cmbLeaved.currentIndex()
            self.dialogParams['indexSex'] = self.cmbSex.currentIndex()
            self.dialogParams['ageFor'] = self.spbAgeFor.value()
            self.dialogParams['ageTo'] = self.spbAgeTo.value()
            self.dialogParams['codeAttachType'] = None
            self.dialogParams['finance'] = self.cmbFinance.value() if (self.btnFinance.isVisible() and self.cmbFinance.isEnabled()) else None
            self.dialogParams['contractId'] = self.cmbContract.value() if (self.btnContract.isVisible() and self.cmbContract.isEnabled()) else None
            self.dialogParams['personId'] = self.cmbPerson.value()
            self.dialogParams['conclusion'] = unicode(self.cmbDeath.currentText())
            self.dialogParams['accountingSystemId'] = self.cmbFilterAccountingSystem.value()
            self.dialogParams['filterClientId'] = forceStringEx(self.edtFilterClientId.text())
            self.dialogParams['filterEventId'] = forceStringEx(self.edtFilterEventId.text())
            self.dialogParams['statusObservation'] = self.cmbStatusObservation.value()
            self.dialogParams['indexLocalClient'] = self.cmbLocationClient.currentIndex() if (self.cmbLocationClient.isVisible() and self.cmbLocationClient.isEnabled()) else None
            self.dialogParams['presenceDay'] = self.edtPresenceDayValue.value() if self.edtPresenceDayValue.isVisible() else None
            self.dialogParams['receivedIndex'] = self.cmbReceived.currentIndex() if self.cmbReceived.isEnabled() else None
            self.dialogParams['feed'] = self.cmbFeed.currentIndex() if self.cmbFeed.isVisible() else None
            self.dialogParams['dateFeed'] = self.edtDateFeed.date() if (self.cmbFeed.isVisible() and self.edtDateFeed.isVisible() and self.cmbFeed.currentIndex() > 0) else None
            self.dialogParams['reason'] = self.cmbRenunciation.text()
            self.dialogParams['renunciationActionIndex'] = self.cmbRenunciationAction.currentIndex()
            self.dialogParams['transfer'] = self.cmbTransfer.currentIndex() if self.cmbTransfer.isVisible() else None
            self.dialogParams['eventClosedType'] = self.cmbEventClosedType.currentIndex()
            self.dialogParams['dietId'] = self.cmbFilterDiet.value() if self.cmbFilterDiet.isVisible() else None
            if self.chkPresenceActionActiviti.isVisible():
                self.dialogParams['isPresenceActionActiviti'] = self.chkPresenceActionActiviti.isChecked()
            self.dialogParams['scheduleId'] = self.cmbFilterSchedule.value()
        self.dialogParams['filterMES']     = self.edtMES.text()
        self.dialogParams['srcCity'] = self.cmbSrcCity.code()
        self.dialogParams['srcRegion'] = self.cmbSrcRegion.value()
        self.dialogParams['srcOrg'] = self.cmbSrcOrg.value()
        self.dialogParams['MKBSrcFilter']  = self.cmbSrcMKBFilter.currentIndex()
        self.dialogParams['MKBSrcFrom']    = unicode(self.edtSrcMKBFrom.text())
        self.dialogParams['MKBSrcTo']      = unicode(self.edtSrcMKBTo.text())
        self.dialogParams['MKBFilter']     = self.cmbMKBFilter.currentIndex()
        self.dialogParams['MKBFrom']       = unicode(self.edtMKBFrom.text())
        self.dialogParams['MKBTo']         = unicode(self.edtMKBTo.text())
        self.dialogParams['voucherSerial'] = unicode(self.edtVoucherSerial.text())
        self.dialogParams['voucherNumber'] = unicode(self.edtVoucherNumber.text())
        self.dialogParams['orgStructureId'] = self.treeOrgStructure.currentIndex()
        self.dialogParams['permanent'] = self.cmbFilterIsPermanent.currentIndex() if self.cmbFilterIsPermanent.isEnabled() else None
        self.dialogParams['type'] = self.cmbFilterType.value() if self.cmbFilterType.isEnabled() else None
        self.dialogParams['bedProfile'] = self.cmbFilterBedProfile.value() if self.cmbFilterBedProfile.isEnabled() else None
        self.dialogParams['treatmentProfile'] = self.hospitalBedProfileList
        self.dialogParams['order'] = forceInt(self.cmbOrder.currentIndex())
        self.dialogParams['eventTypeId'] = forceInt(self.cmbEventType.value())
        self.dialogParams['placeCall'] = unicode(self.cmbPlaceCall.text())
        self.dialogParams['codeBeds'] = self.edtFilterCode.text()
        self.dialogParams['stayOrgStructure'] = self.chkStayOrgStructure.isChecked() if self.chkStayOrgStructure.isVisible() else None
        self.dialogParams['defaultOrgStructureEventTypeIdList'] = self._defaultOrgStructureEventTypeIdList if (self._isChkDefaultOrgStructureVisible and self.chkDefaultOrgStructure.isChecked()and self.chkDefaultOrgStructure.isVisible()) else []
        self.dialogParams['isPlacementChecked'] = self.chkPlacement.isChecked()
        self.dialogParams['placementId'] = self.cmbFilterPlacement.value()
        deliverIndex = self.cmbFilterDeliverBy.currentIndex()
        self.dialogParams['deliverBy'] = self.filterDeliverByValues[deliverIndex] if deliverIndex else None
        self.dialogParams['documentTypeForTracking'] = self.cmbFilterDocumentTypeForTracking.value()
        self.dialogParams['documentLocation'] = self.documentLocationList if self.documentLocationList else None
        if self.tabWidget.currentIndex() == self.tabWidget.indexOf(self.tabQueue):
            self.dialogParams['statusObservationPlaning'] = self.cmbStatusObservationPlaning.value()
            self.dialogParams['indexSexPlaning'] = self.cmbSexPlaning.currentIndex()
            self.dialogParams['ageForPlaning'] = self.spbAgeForPlaning.value()
            self.dialogParams['ageToPlaning'] = self.spbAgeToPlaning.value()
            self.dialogParams['codeAttachTypePlaning'] = self.cmbAttachTypePlaning.code() if (self.chkAttachTypePlaning.isChecked() and self.cmbAttachTypePlaning.isEnabled()) else None
            self.dialogParams['financePlaning'] = self.cmbFinancePlaning.value() if (self.btnFinancePlaning.isVisible() and self.cmbFinancePlaning.isEnabled()) else None
            self.dialogParams['contractIdPlaning'] = self.cmbContractPlaning.value() if (self.btnContractPlaning.isVisible() and self.cmbContractPlaning.isEnabled()) else None
            self.dialogParams['personIdPlaning'] = self.cmbPersonPlaning.value()
            if self.chkFilterRegionSMOPlaning.isChecked():
                self.dialogParams['regionSMOPlaning'] = (self.chkFilterRegionSMOPlaning.isChecked(), self.cmbFilterRegionTypeSMOPlaning.currentIndex(), self.cmbFilterRegionSMOPlaning.code())
                self.dialogParams['insurerIdPlaning'] = None
            else:
                self.dialogParams['insurerIdPlaning'] = self.cmbOrgPlaning.value()
                self.dialogParams['regionSMOPlaning'] = (False, 0, None)
            self.dialogParams['personExecIdPlaning'] = self.cmbPersonExecPlaning.value()
            self.dialogParams['accountingSystemIdPlaning'] = self.cmbFilterAccountingSystemPlaning.value()
            self.dialogParams['filterClientIdPlaning'] = forceStringEx(self.edtFilterClientIdPlaning.text())
            self.dialogParams['filterEventIdPlaning'] = forceStringEx(self.edtFilterEventIdPlaning.text())
            self.dialogParams['eventClosedTypePlaning'] = self.cmbEventClosedTypePlaning.currentIndex()
            self.dialogParams['actionStatus'] = self.cmbActionStatus.value() if self.cmbActionStatus.isVisible() else None
            self.dialogParams['profileDirectionsId'] = self.cmbProfileDirections.value() if self.cmbProfileDirections.isVisible() else None
            self.dialogParams['eventSrcNumber'] = forceString(self.edtEventSrcNumber.text()) if self.edtEventSrcNumber.isVisible() else None
            self.dialogParams['actionTypePlaningId'] = self.cmbActionTypePlaning.value() if self.cmbActionTypePlaning.isVisible() else None
            self.dialogParams['isNoPlannedEndDate'] = self.chkNoPlannedEndDate.isChecked() if self.chkNoPlannedEndDate.isVisible() else None
            self.dialogParams['planActionBegDate'] = self.edtPlanActionBegDate.date() if (self.edtPlanActionBegDate.isVisible() and self.chkPlanActionBegDate.isChecked()) else None
            self.dialogParams['planActionEndDate'] = self.edtPlanActionEndDate.date() if (self.edtPlanActionEndDate.isVisible() and self.chkPlanActionBegDate.isChecked()) else None
            self.dialogParams['plannedBegDate'] = self.edtPlannedBegDate.date() if (self.edtPlannedBegDate.isVisible() and self.chkPlannedDate.isChecked()) else None
            self.dialogParams['plannedEndDate'] = self.edtPlannedEndDate.date() if (self.edtPlannedEndDate.isVisible() and self.chkPlannedDate.isChecked()) else None
            self.dialogParams['planWaitingBegDate'] = self.edtPlanWaitingBegDate.value() if (self.edtPlanWaitingBegDate.isVisible() and self.chkPlanWaitingPeriod.isChecked()) else None
            self.dialogParams['planWaitingEndDate'] = self.edtPlanWaitingEndDate.value() if (self.edtPlanWaitingEndDate.isVisible() and self.chkPlanWaitingPeriod.isChecked()) else None
            self.dialogParams['planBeforeOnsetBegDate'] = self.edtPlanBeforeOnsetBegDate.value() if (self.edtPlanBeforeOnsetBegDate.isVisible() and self.chkPlanPeriodBeforeOnset.isChecked()) else None
            self.dialogParams['planBeforeOnsetEndDate'] = self.edtPlanBeforeOnsetEndDate.value() if (self.edtPlanBeforeOnsetEndDate.isVisible() and self.chkPlanPeriodBeforeOnset.isChecked()) else None
            self.dialogParams['planExceedingDays'] = self.edtPlanExceedingDays.value() if (self.edtPlanExceedingDays.isVisible() and self.chkPlanExceedingDays.isChecked()) else None
            self.dialogParams['isHospitalization'] = self.cmbHospitalization.currentIndex() if self.chkHospitalization else None


    def loadDataLeaved(self):
        self.getDialogParams()
        self.modelLeaved.loadData(self.dialogParams)


    def loadDataQueue(self):
        self.getDialogParams()
        self.modelQueue.loadData(self.dialogParams)


    def loadDataPresence(self):
        self.getDialogParams()
        self.modelPresence.loadData(self.dialogParams)
        self.btnDayClientInvoices.setEnabled(bool(self.modelPresence.items))


    def loadDataTransfer(self):
        self.getDialogParams()
        self.modelTransfer.loadData(self.dialogParams)


    def loadDataReceived(self):
        self.getDialogParams()
        self.modelReceived.loadData(self.dialogParams)


    @pyqtSignature('QAbstractButton*')
    def on_buttonBoxFilter_clicked(self, button):
        buttonCode = self.buttonBoxFilter.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.on_selectionModelOrgStructure_currentChanged(None, None)
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.resetFilter()
            self.on_selectionModelOrgStructure_currentChanged(None, None)


    @pyqtSignature('QAbstractButton*')
    def on_buttonBox_clicked(self, button):
        buttonCode = self.buttonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Close:
            self.reject()


    def getClientString(self, clientId, atDate=None):
        info = getClientInfo(clientId)
        return formatClientString(info, atDate)


    def getClientFullName(self, clientId, atDate=None):
        info = getClientInfo(clientId)
        result = formatName(info.lastName, info.firstName,  info.patrName)
        return result


    def getCurrentActionsTableTitle(self):
        index = self.tabWidgetActionsClasses.currentIndex()
        return [u'Список', u'Статус', u'Диагностика', u'Лечение', u'Мероприятия'][index]


    @pyqtSignature('')
    def on_btnPrintActionList_clicked(self):
        clientId = self.tblPresence.model().items[self.tblPresence.currentRow()][7]
        tblActions = self.tblActionList
        model = tblActions.model()
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Лист назначений пациента:')
        cursor.insertBlock()
        cursor.insertText(u'%s'%(self.getClientFullName(clientId) if clientId else u'пациент не известен'))
        self.dumpParams(cursor)
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()
        colWidths  = [ tblActions.columnWidth(i) for i in xrange(model.columnCount()-1) ]
        colWidths.insert(0,10)
        totalWidth = sum(colWidths)
        tableColumns = []
        iColNumber = False
        for iCol, colWidth in enumerate(colWidths):
            widthInPercents = str(max(1, colWidth*90/totalWidth))+'%'
            if iColNumber == False:
                tableColumns.append((widthInPercents, [u'№'], CReportBase.AlignRight))
                iColNumber = True
            tableColumns.append((widthInPercents, [forceString(model._cols[iCol].title())], CReportBase.AlignLeft))
        table = createTable(cursor, tableColumns)
        for iModelRow in xrange(model.rowCount()):
            iTableRow = table.addRow()
            table.setText(iTableRow, 0, iModelRow+1)
            for iModelCol in xrange(model.columnCount()):
                index = model.createIndex(iModelRow, iModelCol)
                text = forceString(model.data(index))
                table.setText(iTableRow, iModelCol+1, text)
        html = doc.toHtml('utf-8')
        view = CReportViewDialog(self)
        view.setText(html)
        view.exec_()


    @pyqtSignature('')
    def on_btnPrintActionListVariant_clicked(self):
        tblActions = self.getCurrentActionsTable()
        model = tblActions.model()
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.getCurrentActionsTableTitle())
        cursor.insertBlock()
        self.dumpParams(cursor)
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()
        colWidths  = [ tblActions.columnWidth(i) for i in xrange(model.columnCount()-1) ]
        colWidths.insert(0,10)
        totalWidth = sum(colWidths)
        tableColumns = []
        iColNumber = False
        for iCol, colWidth in enumerate(colWidths):
            widthInPercents = str(max(1, colWidth*100/totalWidth))+'%'
            if iColNumber == False:
                tableColumns.append((widthInPercents, [u'№'], CReportBase.AlignRight))
                tableColumns.append((widthInPercents, [u'ФИО'], CReportBase.AlignLeft))
                iColNumber = True
            tableColumns.append((widthInPercents, [forceString(model._cols[iCol].title())], CReportBase.AlignLeft))
        table = createTable(cursor, tableColumns)
        for iModelRow in xrange(model.rowCount()):
            iTableRow = table.addRow()
            table.setText(iTableRow, 0, iModelRow+1)
            table.setText(iTableRow, 1, forceString(self.getVerticalHeaderForAction(model, iModelRow)))
            for iModelCol in xrange(model.columnCount()):
                index = model.createIndex(iModelRow, iModelCol)
                text = forceString(model.data(index))
                table.setText(iTableRow, iModelCol+2, text)
        html = doc.toHtml('utf-8')
        view = CReportViewDialog(self)
        view.setText(html)
        view.exec_()


    def getVerticalHeaderForAction(self, model, section):
        id = model._idList[section]
        model._recordsCache.weakFetch(id, model._idList[max(0, section-model.fetchSize):(section+model.fetchSize)])
        record = model._recordsCache.get(id)
        clientValues   = model.clientCol.extractValuesFromRecord(record)
        clientValue = forceString(model.clientCol.format(clientValues))
        clientIdentifier = ''
        clientIdentifierValues = model.clientIdentifierCol.extractValuesFromRecord(record)
        clientIdentifier = forceString(model.clientIdentifierCol.format(clientIdentifierValues))
        clientBirthDateValues = model.clientBirthDateCol.extractValuesFromRecord(record)
        clientBirthDate = forceString(model.clientBirthDateCol.format(clientBirthDateValues))
        clientSexValues = model.clientSexCol.extractValuesFromRecord(record)
        clientSex = forceString(model.clientSexCol.format(clientSexValues))
        clientFIOSex = u', '.join([clientValue, clientSex])
        birthDateSex = u', '.join([clientIdentifier, clientBirthDate])
        result =  u'\n'.join([clientFIOSex, birthDateSex])
        return result


    @pyqtSignature('')
    def on_btnFindClientInfo_clicked(self):
        self.cmbFilterAccountingSystem.setValue(None)
        self.edtFilterClientId.setText('')
        clientIdList = self.getClientIdList()
        HospitalizationEvent = CFindClientInfoDialog(self, clientIdList)
        if HospitalizationEvent:
            widgetIndex = self.tabWidget.currentIndex()
            app = QtGui.qApp
            hospitalBedsHasRight = False
            if widgetIndex != 3:
                if app.userHasRight(urHBHospitalization):
                    hospitalBedsHasRight = True
                elif widgetIndex in (1, 2) and app.userHasRight(urHospitalTabReceived):
                    hospitalBedsHasRight = True
                elif widgetIndex == 5 and app.userHasRight(urHospitalTabPlanning):
                    hospitalBedsHasRight = True
            HospitalizationEvent.setHospitalBedsHasRight(hospitalBedsHasRight)
            HospitalizationEvent.setWindowTitle(u'''Поиск пациента''')
            HospitalizationEvent.exec_()
            self.edtFilterClientId.setText(forceString(HospitalizationEvent.filterClientId))


    @pyqtSignature('')
    def on_btnFindClientInfoPlaning_clicked(self):
        self.cmbFilterAccountingSystemPlaning.setValue(None)
        self.edtFilterClientIdPlaning.setText('')
        clientIdList = self.getClientIdList()
        HospitalizationEvent = CFindClientInfoDialog(self, clientIdList)
        if HospitalizationEvent:
            widgetIndex = self.tabWidget.currentIndex()
            app = QtGui.qApp
            hospitalBedsHasRight = False
            if app.userHasRight(urHBHospitalization):
                hospitalBedsHasRight = True
            elif widgetIndex in (1, 2) and app.userHasRight(urHospitalTabReceived):
                hospitalBedsHasRight = True
            elif widgetIndex == 5 and app.userHasRight(urHospitalTabPlanning):
                hospitalBedsHasRight = True
            HospitalizationEvent.setHospitalBedsHasRight(hospitalBedsHasRight)
            HospitalizationEvent.setWindowTitle(u'''Поиск пациента''')
            HospitalizationEvent.exec_()
            self.edtFilterClientIdPlaning.setText(forceString(HospitalizationEvent.filterClientId))


    def getClientIdList(self):
        clientIdKeyList = {1:7, 2:4, 3:5, 4:3, 5:2}
        modelList = {1:self.modelPresence, 2:self.modelReceived, 3:self.modelTransfer, 4:self.modelLeaved, 5:self.modelQueue}
        clientIdList = []
        tabWidgetIndex = self.tabWidget.currentIndex()
        if tabWidgetIndex:
            model = modelList.get(tabWidgetIndex, None)
            clientIdKey = clientIdKeyList.get(tabWidgetIndex, None)
            if clientIdKey:
                for row in range(0, len(model.items)):
                    clientId = model.items[row][clientIdKey]
                    if clientId and (clientId not in clientIdList):
                        clientIdList.append(clientId)
        return clientIdList


    def getConditionFilter(self):
        sexList = (u'не определено', u'мужской', u'женский')
        rows = []

        titleDescription = u''
        begDate = self.edtFilterBegDate.date()
        endDate = self.edtFilterEndDate.date()
        sexIndex = self.cmbSex.currentIndex()
        ageFor = self.spbAgeFor.value()
        ageTo = self.spbAgeTo.value()
        sexIndexBed = self.cmbSexBed.currentIndex()
        ageForBed = self.spbBedAgeFor.value()
        ageToBed = self.spbBedAgeTo.value()
        begTime = self.edtFilterBegTime.time()
        endTime = self.edtFilterEndTime.time()
        if not begTime.isNull():
            begDateTime = QDateTime(begDate, begTime)
            begDate = begDateTime
        if not endTime.isNull():
            endDateTime = QDateTime(endDate, endTime)
            endDate = endDateTime
        if begDate.date() or endDate.date():
            titleDescription = dateRangeAsStr(u'за период', begDate, endDate)
        currentIndexOS = self.treeOrgStructure.currentIndex()
        if currentIndexOS:
            orgStructureId = self.getOrgStructureId(currentIndexOS)
            if orgStructureId:
                titleDescription += u'\n' + u'подразделение ' + forceString(QtGui.qApp.db.translate('OrgStructure', 'id', orgStructureId, 'name'))
            else:
                titleDescription += u'\n' + u'ЛПУ'
        accountingSystemId = self.cmbFilterAccountingSystem.value()
        if accountingSystemId:
            accountingSystemName = forceString(QtGui.qApp.db.translate('rbAccountingSystem', 'id', accountingSystemId, 'name'))
            titleDescription += u'\n' + u'внешняя учётная система ' + accountingSystemName
            rows.append(u'Внешняя учётная система ' + accountingSystemName)
        filterClientId = forceStringEx(self.edtFilterClientId.text())
        if filterClientId:
            titleDescription += u'\n' + u'идентификатор пациента %s'%(str(filterClientId))
            rows.append(u'идентификатор пациента %s'%(str(filterClientId)))
        edtFilterEventId = forceStringEx(self.edtFilterEventId.text())
        if edtFilterEventId:
            titleDescription += u'\n' + u'номер документа (Карта) %s'%(str(edtFilterEventId))
            rows.append(u'номер документа (Карта) %s'%(str(edtFilterEventId)))
        statusObservationId = self.cmbStatusObservation.value()
        if statusObservationId:
            statusObservationName = forceString(QtGui.qApp.db.translate('rbStatusObservationClientType', 'id', statusObservationId, 'name'))
            titleDescription += u'\n' + u'статус наблюдения пациента: ' + statusObservationName
            rows.append(u'Статус наблюдения пациента: ' + statusObservationName)
        order = self.cmbOrder.currentIndex()
        titleDescription += u'\n' + u'порядок ' + [u'не определен', u'плановый', u'экстренный', u'самотёком', u'принудительный', u'внутренний перевод', u'неотложная'][order]
        rows.append(u'Порядок ' + [u'не определен', u'плановый', u'экстренный', u'самотёком', u'принудительный', u'внутренний перевод', u'неотложная'][order])
        eventTypeId = self.cmbEventType.value()
        if eventTypeId:
            titleDescription += u'\n' + u'тип события ' + self.cmbEventType.currentText()
            rows.append(u'Тип события ' + self.cmbEventType.currentText())
        if self.cmbPlaceCall.isEnabled():
            titleDescription += u'\n' + self.lblPlaceCall.text() + u': ' + self.cmbPlaceCall.text()
            rows.append(self.lblPlaceCall.text() + u': ' + self.cmbPlaceCall.text())
        personId = self.cmbPerson.value()
        if personId:
            personName = forceString(QtGui.qApp.db.translate('vrbPersonWithSpeciality', 'id', personId, 'name'))
            titleDescription += u'\n' + u'врач ' + personName
            rows.append(u'Врач ' + personName)
        if sexIndex:
            titleDescription += u'\n' + u'пол ' + sexList[sexIndex]
            rows.append(u'Пол ' + sexList[sexIndex])
        if ageFor or ageTo:
            titleDescription += u'\n' + u'возраст' + u' с '+forceString(ageFor) + u' по '+forceString(ageTo)
            rows.append(u'Возраст' + u' с '+forceString(ageFor) + u' по '+forceString(ageTo))
        if self.hospitalBedProfileList:
            db = QtGui.qApp.db
            table = db.table('rbHospitalBedProfile')
            records = db.getRecordList(table, [table['name']], [table['id'].inlist(self.hospitalBedProfileList)])
            nameList = []
            for record in records:
                nameList.append(forceString(record.value('name')))
            titleDescription += u'\n' + u'профиль %s'%(u','.join(name for name in nameList if name))
            rows.append(u'Профиль лечения %s'%(u','.join(name for name in nameList if name)))
#        relegateOrg = self.cmbRelegateOrg.value()
#        if relegateOrg:
#            relegateOrg = self.cmbRelegateOrg.currentText()
#            titleDescription += u'\n' + u'направитель ' + forceString(relegateOrg)
#            rows.append(u'Направитель ' + forceString(relegateOrg))
        documentTypeForTracking= self.cmbFilterDocumentTypeForTracking.value()
        if documentTypeForTracking:
            documentTypeForTracking = self.cmbFilterDocumentTypeForTracking.currentText()
            titleDescription += u'\n' + u'вид учетного документа ' + forceString(documentTypeForTracking)
            rows.append(u'Вид учетного документа ' + forceString(documentTypeForTracking))
        documentLocation = self.documentLocationList if self.documentLocationList else None
        if documentLocation:
            db = QtGui.qApp.db
            table = db.table('rbDocumentTypeLocation')
            records = db.getRecordList(table, [table['name']], [table['id'].inlist(documentLocation)])
            nameList = []
            for record in records:
                nameList.append(forceString(record.value('name')))
            titleDescription += u'\n' + u'Место нахождения учетного документа:  %s'%(u','.join(name for name in nameList if name))
            rows.append(u'Место нахождения учетного документа:  %s'%(u','.join(name for name in nameList if name)))
        if self.chkInvolution.isChecked():
            titleDescription += u'\n' + u'сворачивание койки ' + forceString(self.cmbInvolute.currentText())
        if self.cmbFilterIsPermanent.currentIndex():
            permanent = self.cmbFilterIsPermanent.currentText()
            titleDescription += u'\n' + u'штат ' + forceString(permanent)
            rows.append(u'Штат койки ' + forceString(permanent))
        type = self.cmbFilterType.value()
        if type:
            type = self.cmbFilterType.currentText()
            titleDescription += u'\n' + u'тип ' + forceString(type)
            rows.append(u'Тип койки ' + forceString(type))
        bedProfile = self.cmbFilterBedProfile.value()
        if bedProfile:
            bedProfile = self.cmbFilterBedProfile.currentText()
            titleDescription += u'\n' + u'профиль ' + forceString(bedProfile)
            rows.append(u'Профиль койки ' + forceString(bedProfile))
        if sexIndexBed:
            titleDescription += u'\n' + u'пол койки ' + sexList[sexIndexBed]
            rows.append(u'Пол койки ' + sexList[sexIndexBed])
        if ageForBed or ageToBed:
            titleDescription += u'\n' + u'возраст койки' + u' с '+forceString(ageForBed) + u' по '+forceString(ageToBed)
            rows.append(u'Возраст койки' + u' с '+forceString(ageForBed) + u' по '+forceString(ageToBed))
        if self.btnFinance.isVisible():
            codeFinance = self.cmbFinance.value()
            if codeFinance:
                codeFinance = self.cmbFinance.currentText()
                titleDescription += u'\n' + u'источник финансирования ' + forceString(codeFinance)
                rows.append(u'Источник финансирования ' + forceString(codeFinance))
        if self.btnContract.isVisible():
            contractId = self.cmbContract.value()
            if contractId:
                contractName = self.cmbContract.currentText()
                titleDescription += u'\n' + u'договор ' + forceString(contractName)
                rows.append(u'Договор ' + forceString(contractName))
        if self.cmbFeed.isEnabled():
            titleDescription += u'\n' + u'питание: ' + forceString(self.cmbFeed.currentText())
            if self.edtDateFeed.isEnabled():
                titleDescription += u' на дату: ' + forceString(self.edtDateFeed.date())
        if self.edtPresenceDayValue.isEnabled():
            presenceDayValue = self.edtPresenceDayValue.value()
            if presenceDayValue:
                titleDescription += u'\n' + self.lblPresenceDay.text() + u': ' + forceString(presenceDayValue)
        if self.cmbReceived.isEnabled():
            received = self.cmbReceived.currentIndex()
            titleDescription += u'\n' + self.lblReceived.text() + u': ' + [u'в ЛПУ', u'в отделение', u'в приемное отделение', u'без движения', u'в амбулаторию', u'без уточнения'][received]
            rows.append(self.lblReceived.text() + u': ' + [u'в ЛПУ', u'в отделение', u'в приемное отделение', u'без движения', u'в амбулаторию', u'без уточнения'][received])
        if self.cmbTransfer.isEnabled():
            transfer = self.cmbTransfer.currentIndex()
            titleDescription += u'\n' + self.lblTransfer.text() + u': ' + [u'из отделения', u'в отделение'][transfer]
            rows.append(self.lblTransfer.text() + u': ' + [u'из отделения', u'в отделение'][transfer])
        if self.chkStayOrgStructure.isEnabled():
            titleDescription += u'\n' + u'с учетом "Отделения пребывания"'
            rows.append(u'с учетом "Отделения пребывания"')
        if self.cmbLeaved.isEnabled():
            leaved = self.cmbLeaved.currentIndex()
            titleDescription += u'\n' + self.lblLeaved.text() + u': ' + [u'из ЛПУ', u'без выписки', u'из отделений'][leaved]
            rows.append(self.lblLeaved.text() + u': ' + [u'из ЛПУ', u'без выписки', u'из отделений'][leaved])
        if self.cmbRenunciation.isEnabled():
            titleDescription += u'\n' + self.lblRenunciation.text() + u': ' + self.cmbRenunciation.text()
            rows.append(self.lblRenunciation.text() + u': ' + self.cmbRenunciation.text())
        if self.cmbDeath.isEnabled():
            titleDescription += u'\n' + self.lblDeath.text() + u': ' + self.cmbDeath.text()
            rows.append(self.lblDeath.text() + u': ' + self.cmbDeath.text())
        if self.cmbRenunciationAction.isEnabled():
            renunciationAction = self.cmbRenunciationAction.currentIndex()
            titleDescription += u'\n' + self.lblRenunciationAction.text() + u': ' + [u'Госпитализации', u'Планировании'][renunciationAction]
            rows.append(self.lblRenunciationAction.text() + u': ' + [u'Госпитализации', u'Планировании'][renunciationAction])
        titleBed = u''
        scheduleBed = self.cmbFilterSchedule.currentText()
        if scheduleBed:
            titleBed += u'\n' + u'режим ' + forceString(scheduleBed)
        busyBed = self.cmbFilterBusy.currentText()
        if busyBed:
            titleBed += u'\n' + u'занятость ' + forceString(busyBed)
        codeBed = self.edtFilterCode.text()
        if codeBed:
            titleBed += u'\n' + u'код койки ' + forceString(codeBed)
        if self.cmbLocationClient.isEnabled():
            titleDescription += u'\n' + u'размещение пациента: ' + forceString(self.cmbLocationClient.currentText())
            rows.append(u'Размещение пациента: ' + forceString(self.cmbLocationClient.currentText()))
        titlePresenceDay = titleDescription
        titleDescription += u'\n' + u'отчёт составлен: ' + forceString(QDateTime.currentDateTime())
        return titleDescription, titlePresenceDay, rows


    def printReport(self):
        widgetIndex = self.tabWidget.currentIndex()
        titleDescription, titlePresenceDay, rows = self.getConditionFilter()
        if widgetIndex == 0:
            report = CHospitalBedsReport(self)
            view = CReportViewDialog(self)
            view.setText(report.build(self.filterAsText, self.modelHospitalBeds.idList()))
            view.exec_()
        elif widgetIndex == 1:
            self.tblPresence.setReportHeader(u'Присутствуют в стационаре')
            presenceDay = self.edtPresenceDayValue.value()
            if presenceDay:
                titlePresenceDay += u'\n' + u'присутсвуют дней ' + forceString(presenceDay)
            titlePresenceDay += u'\n' + u'отчёт составлен: ' + forceString(QDateTime.currentDateTime())
            self.tblPresence.setReportDescription(titlePresenceDay)
            self.tblPresence.printContent(orientation=QtGui.QPrinter.Landscape)
        elif widgetIndex == 2:
            self.tblReceived.setReportHeader(u'Поступили %s' % (self.cmbReceived.currentText()))
            self.tblReceived.setReportDescription(titleDescription)
            self.tblReceived.printContent()
        elif widgetIndex == 3:
            self.tblTransfer.setReportHeader(u'Переведены %s'%(self.cmbTransfer.currentText()))
            self.tblTransfer.setReportDescription(titleDescription)
            self.tblTransfer.printContent()
        elif widgetIndex == 4:
            self.tblLeaved.setReportHeader(u'Выбыло %s' % (self.cmbLeaved.currentText()))
            self.tblLeaved.setReportDescription(titleDescription)
            self.tblLeaved.printContent()
        elif widgetIndex == 5:
            self.tblQueue.setReportHeader(u'Направление')
            self.tblQueue.setReportDescription(titleDescription)
            self.tblQueue.printContent()


    def getContextData(self):
        context = CInfoContext()
        orgStructureId = self.modelOrgStructure.itemId(self.treeOrgStructure.currentIndex())
        events = []
        for (i, item) in enumerate(self.modelPresence.items):
            event = context.getInstance(CHospitalEventInfo, item[18])
            event._action = context.getInstance(CActionInfo, item[24])
            event._finance = item[1]
            event._hasFeed = item[3]
            event._feed = forceString(self.modelPresence.feedTextValueItems[i])
            event._extraFeed = forceString(self.modelPresence.extraFeedTextValueItems[i])
            event._bedCode = item[15]
            events = events + [event, ]
        data = { 'events' : events,
                 'orgStructure': context.getInstance(COrgStructureInfo, orgStructureId)
                }
        return data


    @pyqtSignature('')
    def on_actPrintThermalSheet_triggered(self):
        # widgetIndex == 1
        data = self.getContextData()
        #applyTemplateInt(self, u"Присутствующие на отделении", temperatureList_html.CONTENT, data, templateType=htmlTemplate)
        applyTemplateInt(self, u"Присутствующие на отделении", CONTENT, data, templateType=htmlTemplate)


    def printJournal(self):
        self.getStationaryReportF001()


    def getTreeOrgSructureId(self):
        treeIndex = self.treeOrgStructure.currentIndex()
        treeItem = treeIndex.internalPointer() if treeIndex.isValid() else None
        return treeItem.id() if treeItem else None


    def movingReport007(self):
        currentOrgStrucrureId = self.getTreeOrgSructureId()
        CStationaryF007Moving(self, currentOrgStrucrureId).exec_()


    def clientListReport007(self):
        currentOrgStrucrureId = self.getTreeOrgSructureId()
        CStationaryF007ClientList(self, currentOrgStrucrureId).exec_()


    def clientListReport007DS(self):
        currentOrgStrucrureId = self.getTreeOrgSructureId()
        CStationaryF007DSClientList(self, currentOrgStrucrureId).exec_()


    def movingReport007DS(self):
        currentOrgStrucrureId = self.getTreeOrgSructureId()
        CStationaryF007DSMoving(self, currentOrgStrucrureId).exec_()


    def stationaryTallySheetMoving(self):
        CStationaryTallySheetMoving(self).exec_()


    def getReportThermalSheet(self):
        CReportThermalSheet(self).exec_()


    def reportLeaved(self):
        self.getReportLeaved()

    @pyqtSignature('int')
    def on_btnPrint_printByTemplate(self, templateId):
        if templateId < 0:
            self.reportFunc[templateId][1]()
        else:
            context = forceString(QtGui.qApp.db.translate('rbPrintTemplate', 'id', templateId, 'context'))
            data = None
            if context == u'feed':
                data = self.getFeedContextData()
            elif context == u'mReceived':
                data = self.getEventsListContextData(self.tblReceived)
                data['clientId'] = self.getClientIdFromTable(self.tblReceived)
            elif context == u'mLeaved':
                data = self.getEventsListContextData(self.tblLeaved)
                data['clientId'] = self.getClientIdFromTable(self.tblLeaved)
            elif context == u'mPresence':
                data = self.getEventsListContextData(self.tblPresence)
                data['clientId'] = self.getClientIdFromTable(self.tblPresence)
            elif context == u'mTransfer':
                data = self.getEventsListContextData(self.tblTransfer)
                data['clientId'] = self.getClientIdFromTable(self.tblTransfer)
            elif context == u'mQueue':
                data = self.getEventsListContextData(self.tblQueue)
                data['clientId'] = self.getClientIdFromTable(self.tblQueue)
            elif context == u'mPresenceActions':
                data = self.getPresenceActionsContextData()
            elif context == u'mHospitalBeds':
                data = self.getHospitalBedsContextData()
            if data:
                applyTemplate(self, templateId, data)


    def getClientIdFromTable(self, table):
        item = table.currentRow()
        if item:
            return table.model().getClientId(item)

    def getHospitalBedsContextData(self):
        context = CInfoContext()
        bedsIdList = self.modelHospitalBeds._idList
        bedsData = CHospitalBedsListInfo(context, bedsIdList)
        data = {
                'HospitalBeds': bedsData
                }
        return data

    def getFeedContextData(self):
        clientIdList = []
        patronIdList = []
        for row in range(0, len(self.modelPresence.items)):
            clientId = self.modelPresence.getClientId(row)
            if clientId and (clientId not in clientIdList):
                clientIdList.append(clientId)
            patronId = self.modelPresence.getPatronId(row)
            if patronId and (patronId not in patronIdList):
                patronIdList.append(patronId)

        dialog = CFeedReportDialog()
        if not dialog.exec_():
            return None
        params = dialog.params()
        feedDate = params.get('feedDate', QDate())
        type = params.get('typePrint', 0)

        currentIndexOS = self.treeOrgStructure.currentIndex()
        orgStructureId = self.getOrgStructureId(currentIndexOS)
        context = CInfoContext()
        feedData,  ccount, pcount = getFeedData(context,  clientIdList, feedDate, type)
        dietList = context.getInstance(CDietList, None)
        mealTimeList = context.getInstance(CMealTimeList, None)
        financeList = context.getInstance(CFinanceList, None)
        orgStructureInfo = context.getInstance(COrgStructureInfo, orgStructureId)
        data = {'recordList': feedData,
                    'clientsCount': len(clientIdList),
                    'clientsWithFeed': len(ccount),
                    'patronsCount': len(patronIdList),
                    'patronsWithFeed': len(pcount),
                    'dietList': dietList,
                    'mealTimeList': mealTimeList,
                    'financeList': financeList,
                    'orgStructure': orgStructureInfo,
                    'reportDate': CDateInfo(feedDate),
                    'reportType': type
                    }
        return data

    def getEventsListContextData(self, table):
        eventIndex = self.getEventIndex(table)
        if not eventIndex:
            return None
        items = table.model().items
        eventIdList = []
        selectedEventIdList = []
        filter = {}
        model = table.model()
        rows = self.getSelectedRows(table)
        if len(rows) > 0:
            for row in rows:
                selectedEventIdList.append(items[row][eventIndex])
        for row, item in enumerate(items):
            eventId = item[eventIndex]
            if eventId and (eventId not in eventIdList):
                eventIdList.append(eventId)
        context = CInfoContext()
        begDate = CDateInfo(self.edtFilterBegDate.date())
        endDate = CDateInfo(self.edtFilterEndDate.date())
        begTime = CTimeInfo(self.edtFilterBegTime.time())
        endTime = CTimeInfo(self.edtFilterEndTime.time())
        received = self.cmbReceived.currentIndex()
        eventCloseTypeIndex = self.cmbEventClosedType.currentIndex()
        orgStructureId = self.getOrgStructureId( self.treeOrgStructure.currentIndex() )
        filter = {'begDate': begDate if begDate else None,
        'endDate': endDate if endDate else None,
        'begTime': begTime if begTime else None,
        'endTime': endTime if endTime else None,
        'received': [u'в ЛПУ', u'в отделение', u'в приемное отделение', u'без движения', u'в амбулаторию', u'без уточнения'][received] if self.cmbReceived.isEnabled() else None,
        'finance': context.getInstance(CFinanceInfo, self.cmbFinance.value()) if (self.cmbFinance.isEnabled() and self.btnFinance.isVisible()) else None,
        'contract': context.getInstance(CContractInfo, self.cmbContract.value()) if (self.cmbContract.isEnabled() and self.btnContract.isVisible()) else None,
        'orgStructure': context.getInstance(COrgStructureInfo, orgStructureId),
        'eventCloseType': [u'Все', u'Только закрытые', u'Только открытые'][eventCloseTypeIndex] if self.cmbEventClosedType.isEnabled() else None
        }

        eventListInfo = CEventListWithDopInfo(context, eventIdList, model.itemByName)
        selectedEventListInfo = CEventListWithDopInfo(context, selectedEventIdList, model.itemByName)
        data = {'rows': eventListInfo,
                'selectedRows': selectedEventListInfo,
                'filter': filter}
        return data

    def getPresenceActionsContextData(self):
        context = CInfoContext()
        idList = self.getCurrentActionsTable().model().idList()

        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableClient = db.table('Client')
        tableAction = db.table('Action')
        table = tableEvent.leftJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
        table = table.leftJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
        records = db.getRecordList(table, [tableAction['id'].alias('actionId'), tableEvent['id'].alias('eventId')], tableAction['id'].inlist(idList))
        actions = []
        events = []
        eventList = []

        for record in records:
            eventId = forceInt(record.value('eventId'))
            actionId = forceInt(record.value('actionId'))
            event = context.getInstance(CEventInfo, eventId)
            action = CActionInfo(context, actionId)
            index = eventList.index(eventId) if eventId in eventList else None
            if index is None:
                events.append(event)
                eventList.append(eventId)
                actions.append([action])
            else:
                actions[index].append(action)

        if len(eventList) == 1:
            eventId = eventList[0]
            model = self.tblPresence.model()
            orgStr = model.itemByName[eventId]['orgStructure']
        else:
            orgStr = None
        data = {
                    'actions': actions,
                    'events': events,
                    'orgStructure': orgStr
                }
        return data

    def getEventIndex(self, table):
        if table:
            return table.model().eventColumn
        return None


    @pyqtSignature('')
    def on_btnDayClientInvoices_clicked(self):
        date = QDateTime.currentDateTime()

        orgStructureId = self.getTreeOrgSructureId()
        clientIds = [i[self.modelPresence.clientIdColumn] for i in self.modelPresence.items]
        clientInvoices = CGroupClientInvoice(orgStructureId, self)
        clientInvoices.load(clientIds=clientIds, date=date, orgStructureId=QtGui.qApp.currentOrgStructureId())
        clientInvoices.exec_()


    @pyqtSignature('')
    def on_btnLeaved_clicked(self):
        widgetIndex = self.tabWidget.currentIndex()
        if widgetIndex in [1, 5]:
            if widgetIndex == 1:
                index = self.tblPresence.currentIndex()
                row = index.row() if index.isValid() else -1
                if row >= 0:
                    actionEndDate = self.modelPresence.getEndDate(row)
                    if actionEndDate:
                        self.checkPresenceEndDate(actionEndDate, row)
                        return
            eventId = self.getCurrentEventId(widgetIndex)
            if eventId:
                if QtGui.qApp.isLockUpdateEventHospitalBeds():
                    lockId = self.lock('Event', eventId)
                    if lockId:
                        try:
                            self.leave(eventId)
                        finally:
                            self.releaseLock(lockId)
                else:
                    self.leave(eventId)


    def leave(self, eventId):
        dialog = CHospitalizationExecDialog(eventId)
        try:
            if dialog.exec_():
                self.leavingParams = dialog.params()
                QtGui.qApp.callWithWaitCursor(self, self.setLeavedAction)
        finally:
                dialog.deleteLater()


    def requestNewEventQueue(self):
        widgetIndex = self.tabWidget.currentIndex()
        app = QtGui.qApp
        if app.userHasRight(urHBHospitalization) or \
            (widgetIndex in (1, 2) and app.userHasRight(urHospitalTabReceived)) or \
            (widgetIndex == 5 and app.userHasRight(urHospitalTabPlanning)):
            self.on_btnHospitalization_clicked()


    def messageActionByNextEventCreation(self):
        QtGui.QMessageBox.warning(self,
                       u'Внимание!',
                       u'Пациент не направлен в отделение, перевод невозможен.',
                       QtGui.QMessageBox.Ok,
                       QtGui.QMessageBox.Ok)
        return True


    @pyqtSignature('')
    def on_btnTransfer_clicked(self):
        widgetIndex = self.tabWidget.currentIndex()
        if widgetIndex == 1:
            index = self.tblPresence.currentIndex()
            row = index.row() if index.isValid() else -1
            if row >= 0:
                actionEndDate = self.modelPresence.getEndDate(row)
                if not actionEndDate:
                    eventId = self.modelPresence.getEventId(row)
                    clientId = self.modelPresence.getClientId(row)
                    if eventId and clientId:
                        if QtGui.qApp.isLockUpdateEventHospitalBeds():
                            lockId = self.lock('Event', eventId)
                            if lockId:
                                try:
                                    self.transfer(eventId, clientId, row)
                                finally:
                                    self.releaseLock(lockId)
                        else:
                            self.transfer(eventId, clientId, row)
                else:
                    self.checkPresenceEndDate(actionEndDate, row)


    def checkPresenceEndDate(self, actionEndDate, row):
        name = None
        actionId = self.modelPresence.getActionId(row)
        personName = self.modelPresence.getPersonName(row)
        if actionId:
            stmt = u''' SELECT OS.name
                        FROM Action
                            INNER JOIN ActionPropertyType AS APT ON APT.actionType_id = Action.actionType_id
                            INNER JOIN ActionProperty AS AP ON AP.type_id = APT.id
                            INNER JOIN ActionProperty_OrgStructure AS APOS ON APOS.id=AP.id
                            INNER JOIN OrgStructure AS OS ON OS.id=APOS.value
                        WHERE AP.action_id = %(actionId)s AND Action.id = %(actionId)s AND APT.deleted = 0 AND APT.name %(nameProperty)s AND AP.deleted = 0 AND Action.deleted = 0
                              AND OS.deleted = 0
                        LIMIT 1'''%(dict(actionId = actionId,
                                         nameProperty = updateLIKE(u'Переведен в отделение')))
            query = QtGui.qApp.db.query(stmt)
            if query.first():
                record = query.record()
                name = forceString(record.value('name'))
        if name:
            message = u'Выписка или перевод данного пациента запрещены, так как %(actionEndDate)s пользователем %(personName)s был осуществлен Перевод!'%(dict(actionEndDate = actionEndDate.toString('dd.MM.yyyy'),
                                                                                                                                                               personName    = personName))
        else:
            message = u'Выписка или перевод данного пациента запрещены, так как %(actionEndDate)s пользователем %(personName)s была осуществлена Выписка!'%(dict(actionEndDate = actionEndDate.toString('dd.MM.yyyy'),
                                                                                                                                                                 personName    = personName))
        QtGui.QMessageBox.warning( self,
                                 u'Внимание!',
                                 message,
                                 QtGui.QMessageBox.Ok,
                                 QtGui.QMessageBox.Ok)


    def transfer(self, eventId, clientId, row):
        newEventId = None
        isUpdateAction = False
        actionTypeIdList = getActionTypeIdListByFlatCode(u'moving%')
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        tableAction = db.table('Action')
        tablePerson = db.table('Person')
        tableRBPost = db.table('rbPost')
        cols = [tableAction['id'].alias('actionId'),
                tableAction['actionType_id']]
        cond = [tableAction['actionType_id'].inlist(actionTypeIdList),
                tableAction['deleted'].eq(0),
                tableAction['event_id'].eq(eventId),
                tableAction['endDate'].isNull()]
        recordActionList = db.getRecordEx(tableAction, cols, cond, order='Action.id DESC')
        actionId = forceRef(recordActionList.value('actionId')) if recordActionList else None
        actionTypeId = forceRef(recordActionList.value('actionType_id')) if recordActionList else None
        if actionId and (actionTypeId and actionTypeId in actionTypeIdList) and clientId:
            action = CAction.getActionById(actionId)
            if action and (u'moving' in action._actionType.flatCode.lower()):
                recordPurpose = db.getRecordEx(tableEvent.innerJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id'])),
                                     [tableEventType['purpose_id']], [tableEvent['id'].eq(eventId), tableEvent['deleted'].eq(0), tableEventType['deleted'].eq(0)])
                eventPurposeId = forceRef(recordPurpose.value('purpose_id')) if recordPurpose else None
                actionType = CActionTypeCache.getById(actionTypeId) if actionTypeId else None
                prevRecord = action._record
                visibleMKB = True
                if actionType.defaultMKB == CActionType.dmkbNotUsed:
                    enableMKB  = False
                    visibleMKB = False
                elif actionType.defaultMKB in (CActionType.dmkbSyncFinalDiag,
                                               CActionType.dmkbSyncSetPersonDiag):
                    enableMKB = not forceString(prevRecord.value('MKB'))
                else:
                    enableMKB = True
                canEdit = (not action.isLocked() if action else True)

                dialog = CHospitalizationTransferDialog(self, eventPurposeId)
                try:
                    dialog.setDiagnosisVisible(visibleMKB, enableMKB, canEdit)
                    actionByNextEventCreation = CActionsPage(self).checkActionByNextEventCreation()
                    dialog.setFromEventVisible(forceBool(actionByNextEventCreation))
                    recordEvent = db.getRecordEx(tableEvent, '*',
                                                 [tableEvent['deleted'].eq(0),
                                                  tableEvent['id'].eq(eventId)])
                    oldOrgStructureId = action[u'Отделение пребывания'] if u'Отделение пребывания' in action._actionType._propertiesByName else None
                    #orgStructureTransferId = action[u'Переведен в отделение'] if u'Переведен в отделение' in action._actionType._propertiesByName else None
                    orgStructureId = oldOrgStructureId
                    #oldPersonId = forceRef(prevRecord.value('person_id'))
                    #if not oldPersonId:
                    oldPersonId = forceRef(recordEvent.value('execPerson_id'))
                    dialog.setPersonId(oldPersonId)
                    transferChiefId = getChiefId(orgStructureId)
                    dialog.setExecPerson(transferChiefId if transferChiefId else oldPersonId)
                    dialog.setOrgStructureId(orgStructureId if orgStructureId else QtGui.qApp.currentOrgStructureId(), oldPersonId, propertyOrgStructure = True)
                    diagnosis = forceString(prevRecord.value('MKB')) if visibleMKB else u''
                    dialog.setDiagnosis(diagnosis)
                    dialog.setMinimumDate(forceDateTime(prevRecord.value('begDate')))
                    MKBEnd = u''
                    tableClient = db.table('Client')
                    recordClient = db.getRecordEx(tableClient, [tableClient['sex'], tableClient['birthDate']], [tableClient['id'].eq(clientId), tableClient['deleted'].eq(0)])
                    clientSex = 0
                    clientBirthDate = None
                    if recordClient:
                        clientSex = forceInt(recordClient.value('sex'))
                        clientBirthDate = forceDate(recordClient.value('birthDate'))
                    if actionByNextEventCreation:
                        tableDiagnosis = db.table('Diagnosis')
                        tableDiagnostic = db.table('Diagnostic')
                        tableMKB = db.table('MKB')
                        tableRBDiagnosisType = db.table('rbDiagnosisType')
                        queryTable = tableEvent.innerJoin(tableDiagnostic, tableEvent['id'].eq(tableDiagnostic['event_id']))
                        queryTable = queryTable.innerJoin(tableDiagnosis, tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']))
                        queryTable = queryTable.innerJoin(tableRBDiagnosisType, tableDiagnostic['diagnosisType_id'].eq(tableRBDiagnosisType['id']))
                        cols = [tableDiagnosis['id'].alias('diagnosisId'),
                                tableDiagnostic['id'].alias('diagnosticId'),
                                tableDiagnosis['MKB'],
                                tableDiagnosis['character_id'],
                                tableDiagnostic['result_id']]
                        cond = [tableEvent['id'].eq(eventId),
                                tableEvent['deleted'].eq(0),
                                tableDiagnosis['deleted'].eq(0),
                                tableDiagnostic['deleted'].eq(0)
                               ]
                        cond.append(u'''rbDiagnosisType.code = '1'
                        OR (rbDiagnosisType.code = '2' AND Diagnostic.person_id = Event.execPerson_id
                        AND (NOT EXISTS (SELECT DC.id
                                         FROM Diagnostic AS DC
                                         INNER JOIN rbDiagnosisType AS DT ON DT.id = DC.diagnosisType_id
                                         WHERE DT.code = '1' AND DC.event_id = Event.id
                                         LIMIT 1)))''')
                        recordDiagnosis = db.getRecordEx(queryTable, cols, cond)
                        if recordDiagnosis:
                            diagnosisId = forceRef(recordDiagnosis.value('diagnosisId'))
                            MKBEnd = forceString(recordDiagnosis.value('MKB'))
                            dialog.setDiagnosisEnd(MKBEnd)
                            diseaseCharacterId = forceRef(recordDiagnosis.value('character_id'))
                            MKBResultId = forceRef(recordDiagnosis.value('result_id'))
                            dialog.setDiseaseCharacter(diseaseCharacterId)
                            dialog.setMKBResult(MKBResultId)
                        else:
                            diagnosisId = None
                            diseaseCharacterId = None
                            MKBResultId = None
                        dialog.setMes(forceRef(recordEvent.value('MES_id')))
                        dialog.setMesSpecification(forceRef(recordEvent.value('mesSpecification_id')))
                        dialog.setResultEvent(forceRef(recordEvent.value('result_id')))
                    if dialog.exec_():
                        newDate = QDateTime(dialog.getActionDate(), dialog.getActionTime())
                        nextChiefId = dialog.execPerson()
                        personId = dialog.getPersonId()
                        orgStructureId = dialog.getOrgStructureId()
                        if nextChiefId:
                            chiefId = nextChiefId
                        else:
                            chiefId = getChiefId(orgStructureId)
                            if not chiefId:
                                cond = [tablePerson['deleted'].eq(0),
                                            tablePerson['orgStructure_id'].eq(orgStructureId)
                                           ]
                                cond.append(db.joinOr([tableRBPost['code'].like('1%%'), tableRBPost['code'].like('2%%')]))
                                tablePatron = tablePerson.innerJoin(tableRBPost, tableRBPost['id'].eq(tablePerson['post_id']))
                                recordPerson = db.getRecordEx(tablePatron, [tablePerson['id']], cond, order='rbPost.code')
                                chiefId = forceRef(recordPerson.value('id')) if recordPerson else None
                        newRecord = tableAction.newRecord()
                        newRecord.setValue('event_id',      toVariant(None))
                        newRecord.setValue('begDate',       toVariant(newDate))
                        newRecord.setValue('status',        toVariant(0))
                        newRecord.setValue('idx',           toVariant(9999))
                        newRecord.setValue('specifiedName', toVariant(prevRecord.value('specifiedName')))
                        newRecord.setValue('duration',      toVariant(prevRecord.value('duration')))
                        newRecord.setValue('periodicity',   toVariant(prevRecord.value('periodicity')))
                        newRecord.setValue('aliquoticity',  toVariant(prevRecord.value('aliquoticity')))
                        newRecord.setValue('actionType_id', toVariant(actionTypeId))
                        newRecord.setValue('directionDate', toVariant(prevRecord.value('directionDate')))
                        newRecord.setValue('setPerson_id',  toVariant(personId))
                        newRecord.setValue('person_id',     toVariant(None))
                        newRecord.setValue('org_id',        toVariant(prevRecord.value('org_id')))
                        newRecord.setValue('amount',        toVariant(prevRecord.value('amount')))
                        newRecord.setValue('MKB',           toVariant(dialog.getDiagnosis() if visibleMKB else u''))
                        newAction = CAction(record=newRecord)
                        if u'Патронаж' in newAction._actionType._propertiesByName:
                            newAction[u'Патронаж'] = u'Нет' if dialog.getDropPatron() else action[u'Патронаж']
                        if u'Переведен из отделения' in newAction._actionType._propertiesByName:
                            newAction[u'Переведен из отделения'] = oldOrgStructureId
                        if u'Отделение пребывания' in newAction._actionType._propertiesByName:
                            newAction[u'Отделение пребывания'] = orgStructureId
                        if u'Переведен в отделение' in action._actionType._propertiesByName:
                            action[u'Переведен в отделение'] = orgStructureId
                        prevRecord.setValue('endDate', toVariant(newDate))
                        prevRecord.setValue('status', toVariant(2))
                        prevRecord.setValue('person_id',  toVariant(personId))
                        if chiefId:
                            recordEvent.setValue('execPerson_id', toVariant(chiefId))
                        if actionByNextEventCreation:
                            diagnosisEnd = dialog.getDiagnosisEnd()
                            newDiseaseCharacterId = dialog.getDiseaseCharacter()
                            newMKBResultId = dialog.getMKBResult()
                            if recordDiagnosis:
                                recordDiagnosis.setValue('MKB', toVariant(diagnosisEnd))
                                recordDiagnosis.setValue('character_id', toVariant(diseaseCharacterId))
                                recordDiagnosis.setValue('result_id', toVariant(MKBResultId))
                            MesId = dialog.getMes()
                            MesSpecificationId = dialog.getMesSpecification()
                            resultEventId = dialog.getResultEvent()
                            recordEvent.setValue('MES_id', toVariant(MesId))
                            recordEvent.setValue('mesSpecification_id', toVariant(MesSpecificationId))
                            recordEvent.setValue('result_id', toVariant(resultEventId))
                            recordEvent.setValue('execPerson_id', toVariant(personId))
                            recordEvent.setValue('execDate', toVariant(newDate))
                            recordEvent.setValue('isClosed', toVariant(1))
                            if dialog.getDropPatron():
                                recordEvent.setValue('relative_id', toVariant(None))
                            if self.checkActionsProperties(eventId, clientSex, clientBirthDate):
                                eventId = saveTransferData(self, 'Event', recordEvent)
                                if eventId:
                                    transferDataList = (recordEvent, recordDiagnosis, newAction, eventId)
                                    params = {}
                                    params['widget'] = self
                                    params['clientId'] = clientId
                                    params['flagHospitalization'] = False
                                    params['actionTypeId'] = actionTypeId
                                    params['valueProperties'] = [orgStructureId]
                                    params['eventTypeFilterHospitalization'] = 2
                                    params['dateTime'] = newDate
                                    params['personId'] = chiefId
                                    params['planningEventId'] = None
                                    params['diagnos'] = None
                                    params['financeId'] = None
                                    params['protocolQuoteId'] = None
                                    params['actionByNewEvent'] = []
                                    params['externalId'] = forceString(recordEvent.value('externalId'))
                                    params['transferDataList'] = transferDataList
                                    params['relegateOrgId'] = forceRef(recordEvent.value('relegateOrg_id'))
                                    params['order'] = 2 #forceInt(recordEvent.value('order'))
                                    params['moving'] = True
                                    newEventId = requestNewEvent(params)
                                    if newEventId:
                                        date = None
                                        recordDate = db.getRecordEx(tableEvent, [tableEvent['setDate'], tableEvent['execDate']], [tableEvent['id'].eq(newEventId), tableEvent['deleted'].eq(0)])
                                        if recordDate:
                                            newSetDate = forceDateTime(recordDate.value('setDate'))
                                            newExecDate = forceDateTime(recordDate.value('execDate'))
                                            date = newExecDate if newExecDate else newSetDate
                                        if (MKBEnd != diagnosisEnd or newDiseaseCharacterId != diseaseCharacterId or newMKBResultId != MKBResultId) and diagnosisId:
                                            recordMKB = db.getRecordEx(tableDiagnosis, '*', [tableDiagnosis['deleted'].eq(0), tableDiagnosis['id'].eq(diagnosisId)])
                                            if recordMKB:
                                                recordMKB.setValue('MKB', toVariant(diagnosisEnd))
                                                recordMKB.setValue('character_id', toVariant(newDiseaseCharacterId))
                                                saveTransferData(self, 'Diagnosis', recordMKB)
                                            queryTableMKB = tableDiagnosis.innerJoin(tableDiagnostic, tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']))
                                            queryTableMKB = queryTableMKB.innerJoin(tableEvent, tableEvent['id'].eq(tableDiagnostic['event_id']))
                                            queryTableMKB = queryTableMKB.innerJoin(tableRBDiagnosisType, tableDiagnostic['diagnosisType_id'].eq(tableRBDiagnosisType['id']))
                                            queryTableMKB = queryTableMKB.innerJoin(tableMKB, tableMKB['DiagID'].eq(tableDiagnosis['MKB']))
                                            condResultMKB = [tableDiagnostic['deleted'].eq(0),
                                                             tableEvent['deleted'].eq(0),
                                                             tableDiagnosis['deleted'].eq(0),
                                                             tableDiagnostic['diagnosis_id'].eq(diagnosisId),
                                                             tableEvent['id'].eq(eventId)]
                                            condResultMKB.append(u'''rbDiagnosisType.code = '1'
                                OR (rbDiagnosisType.code = '2' AND Diagnostic.person_id = Event.execPerson_id
                                AND (NOT EXISTS (SELECT DC.id
                                                 FROM Diagnostic AS DC
                                                 INNER JOIN rbDiagnosisType AS DT ON DT.id = DC.diagnosisType_id
                                                 WHERE DT.code = '1' AND DC.event_id = Event.id
                                                 LIMIT 1)))''')
                                            recordResultMKB = db.getRecordEx(queryTableMKB, 'Diagnostic.*', condResultMKB)
                                            if recordResultMKB:
                                                recordResultMKB.setValue('result_id', toVariant(newMKBResultId))
                                                saveTransferData(self, 'Diagnostic', recordResultMKB)
                                        elif not diagnosisId:
                                            #self.on_actOpenEvent_triggered()
                                            self.saveNewDiagnostics(eventId, personId, clientId, date, newSetDate, newExecDate, diagnosisEnd, newDiseaseCharacterId, newMKBResultId)
                                        action.save(eventId, -1)
                                        newAction.save(newEventId, -1)
                                        self.saveDiagnostics(eventId, newEventId, personId, clientId, date)
                                    isUpdateAction = True
                        else:
                            if self.checkActionProperties(action, clientSex, clientBirthDate):
                                if dialog.getDropPatron():
                                    recordEvent.setValue('relative_id', toVariant(None))
                                saveTransferData(self, 'Event', recordEvent)
                                action.save(eventId, -1)
                                idx=forceInt(action.getRecord().value('idx'))+1
                                newAction.save(eventId, idx)
                                newEventId = eventId
                                isUpdateAction = True
                        if isUpdateAction:
                            if chiefId:
                                tableEJOP = db.table('Event_JournalOfPerson')
                                recordEJOP = tableEJOP.newRecord()
                                recordEJOP.setValue('master_id', toVariant(newEventId))
                                recordEJOP.setValue('execPerson_id', toVariant(chiefId))
                                recordEJOP.setValue('setPerson_id', toVariant(personId if personId else forceRef(recordEvent.value('execPerson_id'))))
                                if newDate:
                                    recordEJOP.setValue('setDate', toVariant(newDate))
                                else:
                                    recordEJOP.setValue('setDate', toVariant(QDateTime.currentDateTime()))
                                db.insertRecord(tableEJOP, recordEJOP)
                            cutFeed(eventId, newDate, newEventId if not dialog.getDropFeed() else None)
                            self.loadDataPresence()
                finally:
                    dialog.deleteLater()
            self.tblPresence.setCurrentRow(row)
            self.updateActionsList({}, [self.getCurrentEventId(1)])
        else:
            self.messageActionByNextEventCreation()


    def checkActionsProperties(self, eventId, clientSex, clientBirthDate):
        db = QtGui.qApp.db
        tableAction = db.table('Action')
        cond = [tableAction['event_id'].eq(eventId),
                tableAction['deleted'].eq(0)
                ]
        actionIdList = db.getDistinctIdList(tableAction, [tableAction['id']], cond, order='Action.begDate')
        for row, actionId in enumerate(actionIdList):
            action = CAction.getActionById(actionId)
            if action:
                if not self.checkActionProperties(action, clientSex, clientBirthDate):
                    return False
        return True


    def checkActionProperties(self, action, clientSex, clientBirthDate):
        def isNull(val, typeName):
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
            if isinstance(val, list):
                return bool(val)
            if type(val) == QDate:
                return not val.isValid()
            return False
        actionEndDate = forceDate(action.getRecord().value('endDate'))
        clientAge = calcAgeTuple(clientBirthDate, actionEndDate)
        actionType = action.getType()
        propertyTypeList = actionType.getPropertiesById().items()
        propertyTypeList.sort(key=lambda x: (x[1].idx, x[0]))
        propertyTypeList = [x[1] for x in propertyTypeList if x[1].applicable(clientSex, clientAge)]
        for row, propertyType in enumerate(propertyTypeList):
            penalty = propertyType.penalty
            needChecking = penalty > 0
            if not propertyType.canChangeOnlyOwner:
                needChecking = needChecking and actionEndDate
            if needChecking or propertyType.isFill:
                skippable = (penalty < 100) or propertyType.isFill
                property = action.getPropertyById(propertyType.id)
                if isNull(property._value, propertyType.typeName):
                    actionTypeName = action._actionType.name
                    propertyTypeName = propertyType.name
                    if not self.checkValueMessage(u'%sНеобходимо заполнить значение свойства "%s" в действии "%s"' %(u'Свойство "%s" является обязательным для заполнения.\n'%(propertyTypeName), propertyTypeName, actionTypeName), skippable, None, None, None):
                        return False
        return True


    def saveNewDiagnostics(self, eventId, personId, clientId, date, newSetDate, newExecDate, MKB, diseaseCharacterId, MKBResultId):
        db = QtGui.qApp.db
        table = db.table('Diagnostic')
        specialityId = forceRef(db.translate('Person', 'id', personId, 'speciality_id'))
        diagnosisTypeId = forceRef(db.translate('rbDiagnosisType', 'code', '1', 'id'))
        diagnosisId, characterId = getDiagnosisId2(
            date,
            personId,
            clientId,
            diagnosisTypeId,
            MKB,
            '',
            diseaseCharacterId,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None)

        newRecord =  table.newRecord()
        newRecord.setValue('person_id', toVariant(personId))
        newRecord.setValue('diagnosis_id', toVariant(diagnosisId))
        newRecord.setValue('character_id', toVariant(characterId))
        newRecord.setValue('diagnosisType_id', toVariant(diagnosisTypeId))
        newRecord.setValue('result_id',     toVariant(MKBResultId))
        newRecord.setValue('speciality_id', toVariant(specialityId))
        newRecord.setValue('setDate',       toVariant(newSetDate))
        newRecord.setValue('endDate',       toVariant(newExecDate))
        newRecord.setValue('MKB',           toVariant(MKB))
        newRecord.setValue('id',            toVariant(None))
        newRecord.setValue('event_id',      toVariant(eventId))
        saveTransferData(self, 'Diagnostic', newRecord)


    def saveDiagnostics(self, eventId, newEventId, personId, clientId, date):
        db = QtGui.qApp.db
        table = db.table('Diagnostic')
        tableDiagnosis = db.table('Diagnosis')
        records = db.getRecordList(table, '*', [table['deleted'].eq(0), table['event_id'].eq(eventId)], 'id')
        for record in records:
            diagnosisId     = forceRef(record.value('diagnosis_id'))
            recordDiagnosis = db.getRecordEx(tableDiagnosis, [tableDiagnosis['MKB'], tableDiagnosis['MKBEx'], tableDiagnosis['morphologyMKB']],
                            [tableDiagnosis['id'].eq(diagnosisId), tableDiagnosis['deleted'].eq(0)])
            if recordDiagnosis:
                MKB             = forceString(recordDiagnosis.value('MKB'))
                MKBEx           = forceString(recordDiagnosis.value('MKBEx'))
                morphologyMKB   = forceString(recordDiagnosis.value('morphologyMKB'))

                TNMS  = forceString(record.value('TNMS'))
                diagnosisTypeId = db.translate('rbDiagnosisType', 'code', '7', 'id')
                characterId = forceRef(record.value('character_id'))
                diagnosisId, characterId = getDiagnosisId2(
                    date,
                    personId,
                    clientId,
                    diagnosisTypeId,
                    MKB,
                    MKBEx,
                    forceRef(record.value('character_id')),
                    forceRef(record.value('dispanser_id')),
                    forceRef(record.value('traumaType_id')),
                    diagnosisId,
                    forceRef(record.value('id')),
                    None,
                    forceBool(record.value('handleDiagnosis')),
                    TNMS,
                    morphologyMKB=morphologyMKB,
                    dispanserBegDate=forceDate(record.value('endDate')))

                newRecord =  table.newRecord()
                copyFields(newRecord, record)
                newRecord.setValue('diagnosisType_id', toVariant(diagnosisTypeId))
                newRecord.setValue('diagnosis_id', toVariant(diagnosisId))
                newRecord.setValue('character_id', toVariant(characterId))
                newRecord.setValue('MKB',           toVariant(MKB))
                newRecord.setValue('MKBEx',         toVariant(MKBEx))
                newRecord.setValue('morphologyMKB', toVariant(morphologyMKB))
                newRecord.setValue('id',            toVariant(None))
                newRecord.setValue('event_id',      toVariant(newEventId))
                saveTransferData(self, 'Diagnostic', newRecord)


    @pyqtSignature('')
    def on_btnHospitalization_clicked(self):
        HospitalizationEvent = None
        widgetIndex = self.tabWidget.currentIndex()
        app = QtGui.qApp
        if app.userHasRight(urHBHospitalization) or \
            (widgetIndex in (1, 2) and app.userHasRight(urHospitalTabReceived)) or \
            (widgetIndex == 5 and app.userHasRight(urHospitalTabPlanning)):
            if widgetIndex == 5:
                clientId = None
                eventId = None
                index = self.tblQueue.currentIndex()
                if index.isValid():
                    row = index.row()
                    if row >= 0:
                        planningActionId = self.modelQueue.getPlanningActionId(row)
                        clientId = self.modelQueue.getClientId(row)
                        eventId = self.modelQueue.getEventId(row)
                        directionInfo = [
                                            self.modelQueue.getExternalId(row),
                                            self.modelQueue.getRelegateOrgId(row),
                                            self.modelQueue.getRelegatePersonId(row),
                                            self.modelQueue.getSrcDate(row),
                                            self.modelQueue.getSrcNumber(row),
                                            self.modelQueue.getSrcDate(row),
                                            self.modelQueue.getSetPersonId(row),
                                            self.modelQueue.getMKB(row),
                                         ]
                    HospitalizationEvent = CHospitalizationFromQueue(self, clientId, eventId, directionInfo, isHealthResort = True, planningActionId=planningActionId)
                    HospitalizationEvent.requestNewEvent()
            else:
                HospitalizationEvent = CHospitalizationEventDialog(self, isHealthResort = True)
                HospitalizationEvent.exec_()
            if HospitalizationEvent and HospitalizationEvent.newEventId:
                self.on_selectionModelOrgStructure_currentChanged(None, None)
                self.tabWidget.setCurrentIndex(2)
                self.tblReceived.setFocus(Qt.OtherFocusReason)
                countRow = self.modelReceived.rowCount()
                row = -1
                while row != (countRow - 1):
                    row += 1
                    if HospitalizationEvent.newEventId == self.modelReceived.items[row][16]:
                        self.tblReceived.setCurrentRow(row)
                        break
            HospitalizationEvent = None


    @pyqtSignature('')
    def on_actTemperatureListEditor_triggered(self):
        index = self.tblPresence.currentIndex()
        if index.isValid():
            row = index.row()
            eventId = self.modelPresence.getEventId(row) if row >= 0 else None
            actionTypeIdList = getActionTypeIdListByFlatCode(u'temperatureSheet%')
            clientId = self.modelPresence.getClientId(row)
            if eventId and actionTypeIdList and clientId:
                db = QtGui.qApp.db
                tableClient = db.table('Client')
                tableEvent = db.table('Event')
                clientRecord = db.getRecordEx(tableClient, [tableClient['sex'], tableClient['birthDate']], [tableClient['id'].eq(clientId), tableClient['deleted'].eq(0)])
                clientSex = forceInt(clientRecord.value('sex'))
                clientAge = calcAge(forceDate(clientRecord.value('birthDate')), QDate.currentDate())
                setDateRecord = db.getRecordEx(tableEvent, [tableEvent['setDate']], [tableEvent['id'].eq(eventId), tableEvent['deleted'].eq(0)])
                setDate = forceDateTime(setDateRecord.value('setDate')) if setDateRecord else None
                dialog = CTemperatureListEditorDialog(self, clientId, eventId, actionTypeIdList, clientSex, clientAge, setDate)
                try:
                    if dialog.exec_():
                        if dialog.action:
                            dialog.action.save()
                finally:
                    dialog.deleteLater()


    def on_actTemperatureListGroupEditor_triggered(self):
        selectedRows = self.getSelectedRows()
        model = self.tblPresence.model()
        modelItems = model.items
        actionTypeIdList = getActionTypeIdListByFlatCode(u'temperatureSheet')
        dialog = CTemperatureListGroupEditorDialog(self, model, selectedRows, modelItems, actionTypeIdList)
        try:
            if dialog.exec_():
                pass
        finally:
            dialog.deleteLater()


    @pyqtSignature('')
    def on_actGetFeedFromMenu_triggered(self):
        eventIdList = self.getEventIdList()
        self.getFeedFromMenu(eventIdList, 0)


    @pyqtSignature('')
    def on_actGetFeedPatronFromMenu_triggered(self):
        eventIdList = self.getEventIdList()
        self.getFeedFromMenu(eventIdList, 1)


    def getFeedFromMenu(self, eventIdList, typeFeed):
        if eventIdList:
            eventData = eventIdList[0]
            eventId = eventData[0] if eventData else None
            db = QtGui.qApp.db
            tableEvent = db.table('Event')
            tableEventType = db.table('EventType')
            tableContract = db.table('Contract')
            financeId = None
            dietClientId = None
            if eventId:
                eventRecord = db.getRecordEx(tableEvent.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id'])),
                                            [tableContract['finance_id'], tableEvent['client_id'], tableEvent['relative_id']], [tableEvent['id'].eq(eventId), tableEvent['deleted'].eq(0)])
                if eventRecord:
                    financeId = forceRef(eventRecord.value('finance_id'))
                    clientId = forceRef(eventRecord.value('client_id'))
                    relativeId = forceRef(eventRecord.value('relative_id'))
                    if len(eventIdList) == 1:
                        if typeFeed:
                           dietClientId = relativeId
                        else:
                            dietClientId = clientId
            dialog = CGetRBMenu(self, financeId, dietClientId)
            id = dialog.exec_()
            if id:
                for eventData in eventIdList:
                    eventId = eventData[0] if eventData else None
                    if eventId:
                        table = tableEvent.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
                        eventTypeRecord = db.getRecordEx(table, [tableEventType['id'], tableEvent['relative_id']], [tableEvent['id'].eq(eventId), tableEventType['form'].like('003')])
                        if eventTypeRecord:
                            eventType = forceRef(eventTypeRecord.value('id'))
                            if eventType:
                                patronId = forceRef(eventTypeRecord.value('relative_id'))
                                if typeFeed and not patronId:
                                    return
                                begDatePresence = eventData[1] if len(eventData) >= 2 else None
                                plannedEndDatePresence = eventData[2] if len(eventData) >= 3 else None
                                endDatePresence = eventData[3] if len(eventData) >= 4 else None
                                QtGui.qApp.setWaitCursor()
                                try:
                                    begDate = dialog.edtBegDate.date()
                                    endDate = dialog.edtEndDate.date()
                                    if begDate and endDate and begDate <= endDate:
                                        tableEventFeed = db.table('Event_Feed')
                                        newRecords = []
#                                        menuId = None
                                        records = db.getRecordList('rbMenu_Content', '*', 'master_id = %d' % (id))
                                        if records:
                                            if begDatePresence and begDate < begDatePresence.date():
                                                begDate = begDatePresence.date()
                                            if endDatePresence and endDate > endDatePresence.date():
                                                endDate = endDatePresence.date()
                                            if (not plannedEndDatePresence or begDate < plannedEndDatePresence) and (not begDatePresence or begDate >= begDatePresence.date()) and (not endDatePresence or endDate <= endDatePresence.date()):
                                                nextDate = begDate
                                                while nextDate <= endDate:
                                                    for record in records:
                                                        financeId = forceRef(record.value('finance_id'))
                                                        newRecord = tableEventFeed.newRecord()
                                                        newRecord.setValue('date', toVariant(nextDate))
                                                        newRecord.setValue('mealTime_id', record.value('mealTime_id'))
                                                        newRecord.setValue('finance_id', toVariant(dialog.cmbFinance.value()))
                                                        newRecord.setValue('refusalToEat', toVariant(dialog.chkRefusalToEat.isChecked()))
                                                        newRecord.setValue('featuresToEat', toVariant(dialog.edtFeaturesToEat.text()))
                                                        newRecord.setValue('typeFeed', toVariant(typeFeed))
                                                        if typeFeed:
                                                            newRecord.setValue('patron_id', toVariant(patronId))
                                                        newRecord.setValue('diet_id', record.value('diet_id'))
                                                        newRecords.append(newRecord)
                                                    nextDate = nextDate.addDays(1)
                                                tableEventFeed = db.table('Event_Feed')
                                                cond = [tableEventFeed['event_id'].eq(eventId), tableEventFeed['deleted'].eq(0), tableEventFeed['typeFeed'].eq(typeFeed)]
                                                eventFeedRecords = db.getRecordList(tableEventFeed, '*', cond, 'Event_Feed.date ASC')
                                                if eventFeedRecords:
                                                    newEventFeedRecords = []
                                                    if dialog.chkUpdate.isChecked():
                                                        for record in newRecords:
                                                            for eventFeedRecord in eventFeedRecords:
                                                                date = forceDate(record.value('date'))
                                                                if date == forceDate(eventFeedRecord.value('date')) and not forceInt(eventFeedRecord.value('deleted')):
                                                                    eventFeedRecord.setValue('diet_id', toVariant(None))
                                                        for record in newRecords:
                                                            boolSetRecord = False
                                                            for eventFeedRecord in eventFeedRecords:
                                                                date = forceDate(record.value('date'))
                                                                if date == forceDate(eventFeedRecord.value('date')) and not forceInt(eventFeedRecord.value('deleted')) and forceRef(eventFeedRecord.value('mealTime_id')) == forceRef(record.value('mealTime_id')):
                                                                    record.setValue('id', eventFeedRecord.value('id'))
                                                                    newEventFeedRecords.append(record)
                                                                    boolSetRecord = True
                                                                    break
                                                            if not boolSetRecord:
                                                                newEventFeedRecords.append(record)
                                                    else:
                                                        for record in newRecords:
                                                            boolSetRecord = False
                                                            for eventFeedRecord in eventFeedRecords:
                                                                date = forceDate(record.value('date'))
                                                                if date == forceDate(eventFeedRecord.value('date')) and not forceInt(eventFeedRecord.value('deleted')):
                                                                    boolSetRecord = True
                                                                    break
                                                            if not boolSetRecord:
                                                                newEventFeedRecords.append(record)
                                                    for newEventFeedRecord in newEventFeedRecords:
                                                        eventFeedRecords.append(newEventFeedRecord)
                                                else:
                                                    eventFeedRecords = newRecords
                                                self.saveFeedFromMenu(eventId, eventFeedRecords, typeFeed)
                                                self.modelPresence.reset()
                                                self.on_selectionModelOrgStructure_currentChanged(None, None)
                                finally:
                                    QtGui.qApp.restoreOverrideCursor()


    def saveFeedFromMenu(self, masterId, records, typeFeed):
        if (records is not None) and masterId:
            db = QtGui.qApp.db
            table = db.table('Event_Feed')
            masterId = toVariant(masterId)
            idList = []
            for record in records:
                if forceDate(record.value('date')) and forceRef(record.value('diet_id')):
                    record.setValue('event_id', masterId)
                    id = db.insertOrUpdate(table, record)
                    record.setValue('id', toVariant(id))
                    idList.append(id)
            filter = [table['event_id'].eq(masterId), table['typeFeed'].eq(typeFeed),
                      'NOT ('+table['id'].inlist(idList)+')']
            db.deleteRecord(table, filter)


    def getOrgStructureId(self, treeIndex):
        treeItem = treeIndex.internalPointer() if treeIndex.isValid() else None
        return treeItem._id if treeItem else None


    def dumpParams(self, cursor, chkSelectClients=False):
        sexList = (u'не определено', u'мужской', u'женский')
        db = QtGui.qApp.db
        description = []
        begDate = self.edtFilterBegDate.date()
        endDate = self.edtFilterEndDate.date()
        currentIndexOS = self.treeOrgStructure.currentIndex()
        sexIndex = self.cmbSex.currentIndex()
        ageFor = self.spbAgeFor.value()
        ageTo = self.spbAgeTo.value()
        begTime = self.edtFilterBegTime.time()
        endTime = self.edtFilterEndTime.time()
        if not begTime.isNull():
            begDateTime = QDateTime(begDate, begTime)
            begDate = begDateTime
        if not endTime.isNull():
            endDateTime = QDateTime(endDate, endTime)
            endDate = endDateTime
        if begDate.date() or endDate.date():
            description.append(dateRangeAsStr(u'за период', begDate, endDate))
        if currentIndexOS:
            orgStructureId = self.getOrgStructureId(currentIndexOS)
            if orgStructureId:
                description.append(u'подразделение ' + forceString(db.translate('OrgStructure', 'id', orgStructureId, 'name')))
            else:
                description.append(u'ЛПУ')
        if chkSelectClients:
            description.append(u'Только пациенты из стац.монитора')
        order = self.cmbOrder.currentIndex()
        description.append(u'Порядок ' + [u'не определен', u'плановый', u'экстренный', u'самотёком', u'принудительный', u'внутренний перевод', u'неотложная'][order])
        eventTypeId = self.cmbEventType.value()
        if eventTypeId:
            description.append(u'Тип события ' + self.cmbEventType.currentText())
        if self.cmbPlaceCall.isEnabled():
            description.append(self.lblPlaceCall.text() + u': ' + self.cmbPlaceCall.text())
        if sexIndex:
            description.append(u'пол ' + sexList[sexIndex])
        if ageFor or ageTo:
            description.append(u'возраст' + u' с '+forceString(ageFor) + u' по '+forceString(ageTo))
        personId = self.cmbPerson.value()
        if personId:
            personName = forceString(QtGui.qApp.db.translate('vrbPersonWithSpeciality', 'id', personId, 'name'))
            description.append(u'Врач ' + personName)
        if self.hospitalBedProfileList:
            db = QtGui.qApp.db
            table = db.table('rbHospitalBedProfile')
            records = db.getRecordList(table, [table['name']], [table['id'].inlist(self.hospitalBedProfileList)])
            nameList = []
            for record in records:
                nameList.append(forceString(record.value('name')))
            description.append(u'Профиль лечения %s'%(u','.join(name for name in nameList if name)))
#        relegateOrg = self.cmbRelegateOrg.value()
#        if relegateOrg:
#            relegateOrg = self.cmbRelegateOrg.currentText()
#            description.append(u'Направитель ' + forceString(relegateOrg))
        documentTypeForTracking = self.cmbFilterDocumentTypeForTracking.value()
        if documentTypeForTracking:
            documentTypeForTracking = self.cmbFilterDocumentTypeForTracking.currentText()
            description.append(u'Вид учетного документа ' + forceString(documentTypeForTracking))
        documentLocation = self.documentLocationList if self.documentLocationList else None
        if documentLocation:
            db = QtGui.qApp.db
            queryTable = db.queryTable('rbDocumentTypeLocation')
            records = db.getRecordList(queryTable, [queryTable['name']], [queryTable['id'].inlist(documentLocation)])
            nameList = []
            for record in records:
                nameList.append(forceString(record.value('name')))
            description.append(u'место нахождения учетного документа:  %s'%(u','.join(name for name in nameList if name)))
        else:
            description.append(u'место нахождения учетного документа:  не задано')
        type = self.cmbFilterType.value()
        if type:
            type = self.cmbFilterType.currentText()
            description.append(u'Тип койки ' + forceString(type))
        bedProfile = self.cmbFilterBedProfile.value()
        if bedProfile:
            bedProfile = self.cmbFilterBedProfile.currentText()
            description.append(u'Профиль койки ' + forceString(bedProfile))
        sexIndexBed = self.cmbSexBed.currentIndex()
        if sexIndexBed:
            description.append(u'Пол койки ' + sexList[sexIndexBed])
        ageForBed = self.spbBedAgeFor.value()
        ageToBed = self.spbBedAgeTo.value()
        if ageForBed or ageToBed:
            description.append(u'Возраст койки' + u' с '+forceString(ageForBed) + u' по '+forceString(ageToBed))
        codeFinance = self.cmbFinance.value()
        if codeFinance:
            codeFinance = self.cmbFinance.currentText()
            description.append(u'Источник финансирования ' + forceString(codeFinance))
        if self.cmbFeed.isEnabled():
           feed = self.cmbFeed.currentIndex()
           if feed:
               dateFeed = self.edtDateFeed.date()
               description.append(u'Питание: ' + [u'не учитывать', u'не назначено', u'назначено', u'отказ от питания', u'учитывать'][feed] + u' на дату ' + dateFeed.toString('dd.MM.yyyy'))
        if self.cmbLocationClient.isEnabled():
            description.append(u'Размещение пациента: ' + forceString(self.cmbLocationClient.currentText()))
        if self.edtPresenceDayValue.isEnabled():
            presenceDayValue = self.edtPresenceDayValue.value()
            if presenceDayValue:
                description.append(self.lblPresenceDay.text() + u': ' + forceString(presenceDayValue))
        if self.cmbReceived.isEnabled():
            received = self.cmbReceived.currentIndex()
            description.append(self.lblReceived.text() + u': ' + [u'в ЛПУ', u'в отделение', u'в приемное отделение', u'без движения', u'в амбулаторию', u'без уточнения'][received])
        if self.cmbTransfer.isEnabled():
            transfer = self.cmbTransfer.currentIndex()
            description.append(self.lblTransfer.text() + u': ' + [u'из отделения', u'в отделение'][transfer])
        if self.chkStayOrgStructure.isEnabled():
            description.append(u'с учетом "Отделения пребывания"')
        if self.cmbLeaved.isEnabled():
            leaved = self.cmbLeaved.currentIndex()
            description.append(self.lblLeaved.text() + u': ' + [u'из ЛПУ', u'без выписки', u'из отделений'][leaved])
        if self.cmbRenunciation.isEnabled():
            description.append(self.lblRenunciation.text() + u': ' + self.cmbRenunciation.text())
        if self.cmbDeath.isEnabled():
            description.append(self.lblDeath.text() + u': ' + self.cmbDeath.text())
        if self.cmbRenunciationAction.isEnabled():
            renunciationAction = self.cmbRenunciationAction.currentIndex()
            description.append(self.lblRenunciationAction.text() + u': ' + [u'Госпитализации', u'Планировании'][renunciationAction])

        description.append(u'отчёт составлен: ' + forceString(QDateTime.currentDateTime()))
        columns = [ ('100%', [], CReportBase.AlignLeft) ]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()


    def getReportLeaved(self):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Сводка по выписке')
        cursor.insertBlock()
        self.dumpParams(cursor)
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()
        cols = [('5%',[u'№'], CReportBase.AlignRight),
                ('15%', [u'№ истории болезни'], CReportBase.AlignLeft),
                ('20%', [u'ФИО пациента'], CReportBase.AlignLeft),
                ('15%', [u'Отделение'], CReportBase.AlignLeft),
                ('15%', [u'Дата госпитализации'], CReportBase.AlignLeft),
                ('15%', [u'Дата выписки'], CReportBase.AlignLeft),
                ('15%', [u'Ответственный'], CReportBase.AlignLeft),
                ('15%', [u'Кол-во дней'], CReportBase.AlignLeft)
               ]
        table = createTable(cursor, cols)
        cnt = 0
        items = self.modelLeaved.items
        for item in items:
            i = table.addRow()
            cnt += 1
            table.setText(i, 0, cnt)
            table.setText(i, 1, item[18])
            table.setText(i, 2, item[5])
            table.setText(i, 3, ((item[12] + u' - ') if item[12] else u'') + item[13])
            table.setText(i, 4, item[8].toString('dd.MM.yyyy hh:mm:ss'))
            table.setText(i, 5, item[10].toString('dd.MM.yyyy hh:mm:ss'))
            table.setText(i, 6, item[14])
            begDate = item[8]
            endDate = item[10]
            table.setText(i, 7, begDate.daysTo(endDate) if begDate.date() != endDate.date() else 1)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.setCharFormat(CReportBase.ReportBody)
        reportView = CReportViewDialog(self)  #(self, QtGui.QPrinter.Landscape)
        reportView.setWindowTitle(u'Сводка по выписке')
        reportView.setOrientation(QtGui.QPrinter.Landscape)
        reportView.setText(doc)
        reportView.exec_()


    def getStationaryReportF001(self):
        orgStructureId = self.treeOrgStructure.currentIndex()
        begDate = self.edtFilterBegDate.date()
        endDate = self.edtFilterEndDate.date()
        sexIndex = self.cmbSex.currentIndex()
        ageFor = self.spbAgeFor.value()
        ageTo = self.spbAgeTo.value()
        begTime = self.edtFilterBegTime.time()
        endTime = self.edtFilterEndTime.time()
        begDateTime = QDateTime(begDate, begTime)
        endDateTime = QDateTime(endDate, endTime)
        report = CReportBase()
        params = report.getDefaultParams()
        setupDialog = CReportF001SetupDialog(self)
        setupDialog.setParams(params)
        if not setupDialog.exec_():
            return
        params = setupDialog.params()
        report.saveDefaultParams(params)
        chkSelectClients = params.get('chkSelectClients', False)
        chkClientId = params.get('chkClientId', False)
        chkEventId = params.get('chkEventId', False)
        chkExternalEventId = params.get('chkExternalEventId', False)
        chkPrintTypeEvent = params.get('chkPrintTypeEvent', False)
        condSort = params.get('condSort', 0)
        condOrgStructure = params.get('condOrgStructure', 0)
        printTypeMKB = params.get('printTypeMKB', 0)

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Учет приема больных и отказов в госпитализации')
        cursor.insertBlock()
        self.dumpParams(cursor, chkSelectClients)
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()
        cols = [('2%',[u'№'], CReportBase.AlignRight),
                ('5%', [u'Поступление', u'дата'], CReportBase.AlignLeft),
                ('5%', [u'', u'час'], CReportBase.AlignLeft),
                ('7%', [u'Фамилия, И., О.'], CReportBase.AlignLeft),
                ('5%', [u'Дата рождения'], CReportBase.AlignLeft),
                ('12%', [u'Постоянное место жительства или адрес  родственников, близких и № телефона'], CReportBase.AlignLeft),
                ('7%', [u'Каким учреждением был направлен или доставлен'], CReportBase.AlignLeft),
                ('7%', [u'Отделение, в которое помещен больной'], CReportBase.AlignLeft),
                ('7%', [u'№ карты стационарного больного'], CReportBase.AlignLeft),
                ('7%', [u'Предварительный диагноз МКБ'], CReportBase.AlignLeft),
                ('5%', [u'Выписан, переведен в другой  стационар, умер'], CReportBase.AlignLeft),
                ('7%', [u'Отметка о сообщении родственникам или учреждению'], CReportBase.AlignLeft),
                ('7%', [u'Если не был госпитализирован', u'причина и принятые меры'], CReportBase.AlignLeft),
                ('7%', [u'', u'отказ в приеме первичный, повторный'], CReportBase.AlignLeft),
                ('5%', [u'Место работы'], CReportBase.AlignLeft),
                ('5%', [u'Примечание'], CReportBase.AlignLeft)
               ]
        table = createTable(cursor, cols)
        table.mergeCells(0, 0, 2, 1) # №
        table.mergeCells(0, 1, 1, 2) # Поступление
        table.mergeCells(0, 3, 2, 1) # ФИО
        table.mergeCells(0, 4, 2, 1) # Дата рождения
        table.mergeCells(0, 5, 2, 1) # Адрес
        table.mergeCells(0, 6, 2, 1) # Учреждение кем доставлен
        table.mergeCells(0, 7, 2, 1) # Отделение
        table.mergeCells(0, 8, 2, 1) # Диагноз
        table.mergeCells(0, 9, 2, 1) # № карты
        table.mergeCells(0, 10, 2, 1) # Выписан
        table.mergeCells(0, 11, 2, 1) # Отметка о сообщении
        table.mergeCells(0, 12, 1, 2) # не был госпитализирован
        table.mergeCells(0, 13, 2, 1) # Примечание


        def queryProperty(flatCode, colsVal = u'', condVal = u'', flag = None, actionIdLeaved = None):
            colsClientId = []
            condClientId = [ tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode(flatCode)),
                             tableAction['deleted'].eq(0),
                             tableEvent['deleted'].eq(0),
                             tableAP['deleted'].eq(0),
                             tableAPT['deleted'].eq(0),
                             tableClient['deleted'].eq(0),
                             tableAP['action_id'].eq(tableAction['id'])
                           ]
            condClientId.append(tableAction['event_id'].eq(forceRef(records.value('eventId'))))
            condClientId.append(tableEvent['client_id'].eq(clientId))
            if flag != 3:
                if actionIdLeaved is not None:
                    condClientId.append(tableAction['id'].eq(actionIdLeaved))
                else:
                    condClientId.append(tableAction['id'].eq(forceRef(records.value('id'))))
                condClientId.append(tableAPT['name'].like(condVal))
            queryTableClientId = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
            queryTableClientId = queryTableClientId.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
            queryTableClientId = queryTableClientId.leftJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
            queryTableClientId = queryTableClientId.innerJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
            queryTableClientId = queryTableClientId.innerJoin(tableAP, tableAP['type_id'].eq(tableAPT['id']))
            if flag == 0:
                queryTableClientId = queryTableClientId.innerJoin(tableAPO, tableAPO['id'].eq(tableAP['id']))
                queryTableClientId = queryTableClientId.innerJoin(tableOrg, tableOrg['id'].eq(tableAPO['value']))
                colsClientId.append(tableOrg['shortName'].alias(colsVal))
                condClientId.append(tableOrg['deleted'].eq(0))
            elif flag == 1:
                queryTableClientId = queryTableClientId.innerJoin(tableAPOS, tableAPOS['id'].eq(tableAP['id']))
                queryTableClientId = queryTableClientId.innerJoin(tableOS, tableOS['id'].eq(tableAPOS['value']))
                colsClientId.append(tableOS['code'].alias(colsVal) if condOrgStructure else tableOS['name'].alias(colsVal))
            elif flag == 3:
                  colsClientId.append(tableAction['id'].alias('actionIdLeaved'))
                  colsClientId.append(tableAction['begDate'].alias('begDateLeaved'))
                  colsClientId.append(tableAction['note'].alias('noteLeaved'))
            else:
                queryTableClientId = queryTableClientId.innerJoin(tableAPS, tableAPS['id'].eq(tableAP['id']))
                colsClientId.append(tableAPS['value'].alias(colsVal))
            stmt = db.selectDistinctStmt(queryTableClientId, colsClientId, condClientId, u'')
            return db.query(stmt)

        cnt = 0
        db = QtGui.qApp.db
        tableAPT = db.table('ActionPropertyType')
        tableAP = db.table('ActionProperty')
        tableActionType = db.table('ActionType')
        tableAction = db.table('Action')
        tableEvent = db.table('Event')
        tableClient = db.table('Client')
        tableAPS = db.table('ActionProperty_String')
        tableAPO = db.table('ActionProperty_Organisation')
        tableOrg = db.table('Organisation')
        tableAPOS = db.table('ActionProperty_OrgStructure')
        tableOS = db.table('OrgStructure')
        tableDiagnosis = db.table('Diagnosis')
        tableMKB = db.table('MKB')
        tableDiagnostic = db.table('Diagnostic')
        tableRBDiagnosisType = db.table('rbDiagnosisType')
        cols = [tableAction['id'],
                tableEvent['id'].alias('eventId'),
                tableEvent['eventType_id'],
                tableEvent['client_id'],
                tableEvent['externalId'],
                tableClient['lastName'],
                tableClient['firstName'],
                tableClient['patrName'],
                tableClient['sex'],
                tableClient['birthDate'],
                tableAction['begDate'],
                tableAction['note'],
                tableAction['finance_id'],
                tableEvent['contract_id']
                ]
        queryTable = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
        queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
        queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
        queryTable = queryTable.innerJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
        queryTable = queryTable.innerJoin(tableAP, tableAP['type_id'].eq(tableAPT['id']))
        cond = [ tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode(u'received%')),
                 tableAction['deleted'].eq(0),
                 tableEvent['deleted'].eq(0),
                 tableAP['deleted'].eq(0),
                 tableAPT['deleted'].eq(0),
                 tableClient['deleted'].eq(0),
                 tableAP['action_id'].eq(tableAction['id'])
               ]
        if begDateTime.date():
            cond.append(db.joinOr([tableAction['begDate'].isNull(), tableAction['begDate'].ge(begDateTime)]))
        if endDateTime.date():
            cond.append(db.joinOr([tableAction['begDate'].isNull(), tableAction['begDate'].le(endDateTime)]))
        if sexIndex > 0:
            cond.append(tableClient['sex'].eq(sexIndex))
        if ageFor <= ageTo:
            cond.append(getAgeRangeCond(ageFor, ageTo))
        if chkSelectClients:
            clientIdList = self.getClientIdList()
            cond.append(tableClient['id'].inlist(clientIdList))
        if orgStructureId:
            if self.getOrgStructureId(orgStructureId):
                orgStructureIdList = self.getOrgStructureIdList(orgStructureId)
                queryTable = queryTable.innerJoin(tableAPOS, tableAPOS['id'].eq(tableAP['id']))
                queryTable = queryTable.innerJoin(tableOS, tableOS['id'].eq(tableAPOS['value']))
                cond.append(tableOS['id'].inlist(orgStructureIdList))
        stmt = db.selectDistinctStmt(queryTable, cols, cond, [u'Client.lastName, Client.firstName, Client.patrName', u'Action.begDate', u'Client.id', u'Event.id', u'CAST(Event.externalId AS SIGNED)'][condSort])
        query = db.query(stmt)
        while query.next():
            records = query.record()
            clientId = forceRef(records.value('client_id'))
            eventId = forceRef(records.value('eventId'))
            begDateTime = forceDateTime(records.value('begDate'))
            begDate = forceDate(records.value('begDate'))
            begTime = forceTime(records.value('begDate'))
            note = forceString(records.value('note'))
            contractId = forceRef(records.value('contract_id'))
            financeId = forceRef(records.value('finance_id'))
            noteText = u''
            if note != u'':
                noteText = note + u'. '
            if clientId:
                clientInfo = getClientInfoEx(clientId)
                clientInfo['phones'] = getClientPhonesEx(clientId)
                adress = u''
                if clientInfo['regAddress']:
                    adress = u'регистрация: ' + clientInfo['regAddress']
                if clientInfo['locAddress']:
                    adress += u', проживание: ' + clientInfo['locAddress']
                if clientInfo['phones']:
                    adress += u', телефон: ' + clientInfo['phones']
                i = table.addRow()
                cnt += 1
                table.setText(i, 0, cnt)
                table.setText(i, 1, begDate.toString('dd.MM.yyyy'))
                table.setText(i, 2, begTime.toString('hh:mm:ss'))
                table.setText(i, 3, clientInfo['fullName'])
                table.setText(i, 4, formatDate(clientInfo['birthDate']) + u'(' + clientInfo['age'] + u')')
                table.setText(i, 5, adress)
                table.setText(i, 14, clientInfo['work'])
                numberCardStr = u''
                numberCardList = []
                if chkClientId:
                    numberCardList.append(clientId)
                if chkEventId:
                    numberCardList.append(forceRef(records.value('eventId')))
                if chkExternalEventId:
                    numberCardList.append(forceRef(records.value('externalId')))
                #numberCardList.sort()
                numberCardStr = ','.join(str(numberCard) for numberCard in numberCardList if numberCard)
                table.setText(i, 8, numberCardStr)
                whoDirecting = u''
                queryClientId = queryProperty(u'received%', u'whoDirecting', u'Кем направлен%', 0)
                if queryClientId.first():
                    record = queryClientId.record()
                    whoDirecting = u'Направлен: ' + forceString(record.value('whoDirecting')) + u' '
                queryClientId = queryProperty(u'received%', u'whoDelivered', u'Кем доставлен%')
                if queryClientId.first():
                    record = queryClientId.record()
                    whoDirecting += u'Доставлен: ' + forceString(record.value('whoDelivered'))
                table.setText(i, 6, whoDirecting)
                nameOSTypeEventList = []
                queryClientId = queryProperty(u'received%', u'orgStructure', u'Направлен в отделение%', 1)
                if queryClientId.first():
                    record = queryClientId.record()
                    nameOSTypeEventList.append(forceString(record.value('orgStructure')))
                if chkPrintTypeEvent:
                    tableRBFinance = db.table('rbFinance')
                    if financeId:
                        recordFinance = db.getRecordEx(tableRBFinance, [tableRBFinance['name']], [tableRBFinance['id'].eq(financeId)])
                        nameOSTypeEventList.append(u'\n' + forceString(recordFinance.value('name')) if recordFinance else '')
                    else:
                        if contractId:
                            tableContract = db.table('Contract')
                            tableFinanceQuery = tableContract.innerJoin(tableRBFinance, tableContract['finance_id'].eq(tableRBFinance['id']))
                            recordFinance = db.getRecordEx(tableFinanceQuery, [tableRBFinance['name']], [tableContract['id'].eq(contractId), tableContract['deleted'].eq(0)])
                            nameOSTypeEventList.append(u'\n' + forceString(recordFinance.value('name')) if recordFinance else '')
                table.setText(i, 7, u'; '.join(nameOSTypeEvent for nameOSTypeEvent in nameOSTypeEventList if nameOSTypeEvent))
                diagnosisList = []
                if printTypeMKB == 1 or printTypeMKB == 2 or printTypeMKB == 0:
                    queryTableMKB = tableEvent.innerJoin(tableDiagnostic, tableEvent['id'].eq(tableDiagnostic['event_id']))
                    queryTableMKB = queryTableMKB.innerJoin(tableDiagnosis, tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']))
                    queryTableMKB = queryTableMKB.innerJoin(tableRBDiagnosisType, tableDiagnostic['diagnosisType_id'].eq(tableRBDiagnosisType['id']))
                    queryTableMKB = queryTableMKB.innerJoin(tableMKB, tableMKB['DiagID'].eq(tableDiagnosis['MKB']))
                    condMKB = [tableEvent['deleted'].eq(0),
                               tableEvent['id'].eq(eventId),
                               tableDiagnosis['deleted'].eq(0),
                               tableDiagnostic['deleted'].eq(0),
                               tableRBDiagnosisType['code'].eq(7)
                               ]
                    stmt = db.selectDistinctStmt(queryTableMKB, u'Diagnosis.MKB,MKB.DiagName', condMKB)
                    queryClientId = db.query(stmt)
                    while queryClientId.next():
                        record = queryClientId.record()
                        if printTypeMKB == 2:
                            diagnosisList.append(forceString(record.value('DiagName'))+u'('+forceString(record.value('MKB'))+u')')
                        if printTypeMKB == 0:
                            diagnosisList.append(forceString(record.value('DiagName')))
                        if printTypeMKB == 1:
                            diagnosisList.append(forceString(record.value('MKB')))
                if printTypeMKB == 0 or printTypeMKB == 2:
                    queryClientId = queryProperty(u'received%', u'diagnosis', u'Диагноз направителя%')
                    while queryClientId.next():
                        record = queryClientId.record()
                        diagnosisList.append(forceString(record.value('DiagName'))+u'('+forceString(record.value('MKB'))+u')')
                table.setText(i, 9, u', '.join(diagnos for diagnos in diagnosisList if diagnos))
                queryClientId = queryProperty(u'received%', u'nameRenuncReason', u'Причина отказа%')
                nameRenunciate = u''
                if queryClientId.first():
                    record = queryClientId.record()
                    nameRenunciate = u'Причина: ' + forceString(record.value('nameRenuncReason')) + u' '
                queryClientId = queryProperty(u'received%', u'nameRenuncMeasure', u'Принятые меры при отказе%')
                if queryClientId.first():
                    record = queryClientId.record()
                    nameRenunciate += u'Меры: ' + forceString(record.value('nameRenuncMeasure'))
                table.setText(i, 12, nameRenunciate)
                queryClientId = queryProperty(u'received%', u'refusal', u'Отказ в приеме%')
                if queryClientId.first():
                    record = queryClientId.record()
                    table.setText(i, 13, forceString(record.value('refusal')))
                queryClientId = queryProperty(u'leaved%', u'', u'', 3)
                if queryClientId.first():
                    record = queryClientId.record()
                    actionIdLeaved = forceRef(record.value('actionIdLeaved'))
                    noteText += forceString(record.value('noteLeaved'))
                    if actionIdLeaved:
                        result = u''
                        queryClientId = queryProperty(u'leaved%', u'resultHaspital', u'Исход госпитализации%', None, actionIdLeaved)
                        if queryClientId.first():
                            record = queryClientId.record()
                            resultHaspital = forceString(record.value('resultHaspital'))
                            result = resultHaspital + u' '
                            begDateLeaved = forceDate(record.value('begDateLeaved'))
                            if begDateLeaved:
                                result += begDateLeaved.toString('dd.MM.yyyy') + u' '
                        queryClientId = queryProperty(u'leaved%', u'transferOrganisation', u'Переведен в стационар%', None, actionIdLeaved)
                        if queryClientId.first():
                            record = queryClientId.record()
                            transferOrganisation = forceString(record.value('transferOrganisation'))
                            result += u'Перевод: ' + transferOrganisation
                        table.setText(i, 10, result)
                        queryClientId = queryProperty(u'leaved%', u'messageRelative', u'Сообщение родственникам%', None, actionIdLeaved)
                        if queryClientId.first():
                            record = queryClientId.record()
                            table.setText(i, 11, forceString(record.value('messageRelative')))
                table.setText(i, 15, noteText)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.setCharFormat(CReportBase.ReportBody)
        reportView = CReportViewDialog(self)
        reportView.setWindowTitle(u'Журнал')
        reportView.setOrientation(QtGui.QPrinter.Landscape)
        reportView.setText(doc)
        reportView.exec_()


    @pyqtSignature('')
    def on_mnuBtnPrint_aboutToShow(self):
        self.on_mnuHospitalBeds_aboutToShow()


    @pyqtSignature('')
    def on_mnuBtnFeed_aboutToShow(self):
        self.on_mnuFeed_aboutToShow()


    @pyqtSignature('')
    def on_mnuFeed_aboutToShow(self): # + +
        app = QtGui.qApp
        isAdmin = app.isAdmin()
        isHBFeed = app.userHasRight(urHBFeed) or app.userHasRight(urHBEditCurrentDateFeed) or isAdmin
        self.tblPresence.setFocus(Qt.OtherFocusReason)
        currentIndex = self.tblPresence.currentIndex()
        isBusy = currentIndex.row() >= 0
        self.actSelectAllFeedClient.setEnabled(isBusy and (self.tabWidget.currentIndex() == 1))
        self.actSelectAllNoFeedClient.setEnabled(isBusy and (self.tabWidget.currentIndex() == 1))
        self.actSelectionRefusalToEatClient.setEnabled(isBusy and (self.tabWidget.currentIndex() == 1))
        self.actSelectAllFeedPatron.setEnabled(isBusy and (self.tabWidget.currentIndex() == 1))
        self.actSelectAllNoFeedPatron.setEnabled(isBusy and (self.tabWidget.currentIndex() == 1))
        self.actSelectionRefusalToEatPatron.setEnabled(isBusy and (self.tabWidget.currentIndex() == 1))
        self.actSelectionAllRow.setEnabled(isBusy and (self.tabWidget.currentIndex() == 1))
        rows = self.getSelectedRows()
        self.actClearSelectionRow.setEnabled(isBusy and (self.tabWidget.currentIndex() == 1) and bool(rows))
        self.actProlongationFeed.setEnabled(isBusy and (self.tabWidget.currentIndex() == 1) and bool(rows) and isHBFeed)
        self.actProlongationPatronFeed.setEnabled(isBusy and (self.tabWidget.currentIndex() == 1) and bool(rows) and isHBFeed)
        self.actGetFeedFromMenuAll.setEnabled(isBusy and (self.tabWidget.currentIndex() == 1) and bool(rows) and isHBFeed)
        self.actGetFeedPatronFromMenuAll.setEnabled(isBusy and (self.tabWidget.currentIndex() == 1) and bool(rows) and isHBFeed)


    @pyqtSignature('')
    def on_mnuBtnTemperatureList_aboutToShow(self):
        app = QtGui.qApp
        isAdmin = app.isAdmin()
        isEditThermalSheet = app.userHasRight(urHBEditThermalSheet) or isAdmin
        self.tblPresence.setFocus(Qt.OtherFocusReason)
        currentIndex = self.tblPresence.currentIndex()
        isBusy = currentIndex.row() >= 0
        rows = self.getSelectedRows()
        self.actTemperatureList.setEnabled(isBusy and (self.tabWidget.currentIndex() == 1) and bool(rows) and isEditThermalSheet)
        self.actTemperatureListGroup.setEnabled(isBusy and (self.tabWidget.currentIndex() == 1) and bool(rows) and isEditThermalSheet)


    def getSelectedRows(self, table = None):
        if not table:
            table = self.tblPresence
        rowCount = table.model().rowCount()
        rowSet = set([index.row() for index in table.selectedIndexes() if index.row()<rowCount])
        result = list(rowSet)
        result.sort()
        return result


    @pyqtSignature('')
    def on_actSelectAllFeedClient_triggered(self):
        self.notSelectedRows = False
        self.tblPresence.clearSelection()
        self.tblPresence.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
        items = self.tblPresence.model().items
        selectRowList = []
        for row, item in enumerate(items):
            if item[3] and (row not in selectRowList):
                self.tblPresence.selectRow(row)
                selectRowList.append(row)
        self.tblPresence.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.setActionsIdList([], None)


    @pyqtSignature('')
    def on_actSelectAllFeedPatron_triggered(self):
        self.notSelectedRows = False
        self.tblPresence.clearSelection()
        self.tblPresence.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
        items = self.tblPresence.model().items
        selectRowList = []
        for row, item in enumerate(items):
            if item[4] and (row not in selectRowList):
                self.tblPresence.selectRow(row)
                selectRowList.append(row)
        self.tblPresence.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.setActionsIdList([], None)


    @pyqtSignature('')
    def on_actSelectionRefusalToEatClient_triggered(self):
        self.notSelectedRows = False
        self.tblPresence.clearSelection()
        self.tblPresence.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
        items = self.tblPresence.model().items
        selectRowList = []
        for row, item in enumerate(items):
            if item[36] and (row not in selectRowList):
                self.tblPresence.selectRow(row)
                selectRowList.append(row)
        self.tblPresence.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.setActionsIdList([], None)


    @pyqtSignature('')
    def on_actSelectionRefusalToEatPatron_triggered(self):
        self.notSelectedRows = False
        self.tblPresence.clearSelection()
        self.tblPresence.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
        items = self.tblPresence.model().items
        selectRowList = []
        for row, item in enumerate(items):
            if item[38] and (row not in selectRowList):
                self.tblPresence.selectRow(row)
                selectRowList.append(row)
        self.tblPresence.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.setActionsIdList([], None)


    @pyqtSignature('')
    def on_actSelectAllNoFeedClient_triggered(self):
        self.notSelectedRows = False
        self.tblPresence.clearSelection()
        self.tblPresence.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
        items = self.tblPresence.model().items
        selectRowList = []
        for row, item in enumerate(items):
            if (not item[3]) and (row not in selectRowList):
                self.tblPresence.selectRow(row)
                selectRowList.append(row)
        self.tblPresence.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.setActionsIdList([], None)


    @pyqtSignature('')
    def on_actSelectAllNoFeedPatron_triggered(self):
        self.notSelectedRows = False
        self.tblPresence.clearSelection()
        self.tblPresence.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
        items = self.tblPresence.model().items
        selectRowList = []
        for row, item in enumerate(items):
            if (not item[4]) and item[36] and (row not in selectRowList):
                self.tblPresence.selectRow(row)
                selectRowList.append(row)
        self.tblPresence.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.setActionsIdList([], None)


    def on_actPrintAllNoFeed_triggered(self):
        report = CReportBase()
        params = report.getDefaultParams()
        report.saveDefaultParams(params)
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Сводка по пациентам без питания')
        cursor.insertBlock()
        self.dumpParams(cursor)
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()
        cols = [('3%',[u'№'], CReportBase.AlignRight),
                ('3%', [u'Статус наблюдения пациента'], CReportBase.AlignLeft),
                ('4%', [u'Источник финансирования'], CReportBase.AlignLeft),
                ('5%', [u'Договор'], CReportBase.AlignLeft),
                ('5%', [u'Номер'], CReportBase.AlignLeft),
                ('5%', [u'Карта'], CReportBase.AlignLeft),
                ('10%', [u'ФИО'], CReportBase.AlignLeft),
                ('10%', [u'Госпитализирован'], CReportBase.AlignLeft),
                ('10%', [u'Поступил'], CReportBase.AlignLeft),
                ('10%', [u'Плановая дата выбытия'], CReportBase.AlignLeft),
                ('5%', [u'МКБ'], CReportBase.AlignLeft),
                ('10%', [u'Койка'], CReportBase.AlignLeft),
                ('10%', [u'Подразделение'], CReportBase.AlignLeft),
                ('10%', [u'Ответсвенный'], CReportBase.AlignLeft)
               ]
        table = createTable(cursor, cols)
        items = self.tblPresence.model().items
        cnt = 0
        selectRowList = []
        for row, item in enumerate(items):
            if (not item[3]) and (row not in selectRowList):
                selectRowList.append(row)
                i = table.addRow()
                cnt += 1
                table.setText(i, 0, cnt)
                table.setText(i, 1, item[0])
                table.setText(i, 2, item[1])
                table.setText(i, 3, item[2])
                table.setText(i, 4, item[7])
                table.setText(i, 5, item[8])
                table.setText(i, 6, item[9] + u' (' + item[9] + u' ' + item[10] + u') ')
                table.setText(i, 7, item[12])
                table.setText(i, 8, item[13])
                table.setText(i, 9, item[14].toString('dd.MM.yyyy'))
                table.setText(i, 10, item[15])
                table.setText(i, 11, item[16])
                table.setText(i, 12, item[17])
                table.setText(i, 13, item[18])
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.setCharFormat(CReportBase.ReportBody)
        reportView = CReportViewDialog(self)
        reportView.setWindowTitle(u'Сводка по пациентам без питания')
        reportView.setOrientation(QtGui.QPrinter.Landscape)
        reportView.setText(doc)
        reportView.exec_()


    @pyqtSignature('')
    def on_actTemperatureList_triggered(self):
        self.on_actTemperatureListEditor_triggered()


    @pyqtSignature('')
    def on_actTemperatureListGroup_triggered(self):
        self.on_actTemperatureListGroupEditor_triggered()


    @pyqtSignature('')
    def on_actSelectionAllRow_triggered(self):
        self.notSelectedRows = False
        self.tblPresence.clearSelection()
        self.tblPresence.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
        self.tblPresence.selectAll()
        self.tblPresence.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.setActionsIdList([], None)


    @pyqtSignature('')
    def on_actClearSelectionRow_triggered(self):
        self.notSelectedRows = True
        self.tblPresence.clearSelection()
        rowCount = self.modelPresence.rowCount()
        if rowCount > 0:
            self.tblPresence.setCurrentRow(0)


    @pyqtSignature('')
    def on_actProlongationFeed_triggered(self):
        self.notSelectedRows = True
        eventIdList = self.getEventIdList()
        self.prolongationFeed(eventIdList, 0)
        rowCount = self.modelPresence.rowCount()
        if rowCount > 0:
            self.tblPresence.setCurrentRow(0)


    @pyqtSignature('')
    def on_actProlongationPatronFeed_triggered(self):
        self.notSelectedRows = True
        eventIdList = self.getEventIdList()
        self.prolongationFeed(eventIdList, 1)
        rowCount = self.modelPresence.rowCount()
        if rowCount > 0:
            self.tblPresence.setCurrentRow(0)


    @pyqtSignature('')
    def on_actGetFeedFromMenuAll_triggered(self):
        self.notSelectedRows = True
        eventIdList = self.getEventIdList()
        self.getFeedFromMenu(eventIdList, 0)
        rowCount = self.modelPresence.rowCount()
        if rowCount > 0:
            self.tblPresence.setCurrentRow(0)


    @pyqtSignature('')
    def on_actGetFeedPatronFromMenuAll_triggered(self):
        self.notSelectedRows = True
        eventIdList = self.getEventIdList()
        self.getFeedFromMenu(eventIdList, 1)
        rowCount = self.modelPresence.rowCount()
        if rowCount > 0:
            self.tblPresence.setCurrentRow(0)


    def getEventByActionIdList(self):
        items = self.tblPresence.model().items
        selectIndexes = self.tblPresence.selectedIndexes()
        selectRowList = []
        eventIdList = {}
        for selectIndex in selectIndexes:
            selectRow = selectIndex.row()
            if selectRow not in selectRowList:
                selectRowList.append(selectRow)
        for row, item in enumerate(items):
            if row in selectRowList:
                eventId = self.modelPresence.getEventId(row)
                actionId = self.modelPresence.getActionId(row)
                clientId = self.modelPresence.getClientId(row)
                if eventId and (eventId not in eventIdList.keys()):
                    eventIdList[eventId] = (clientId, actionId)
        return eventIdList


    def getEventIdList(self):
        items = self.tblPresence.model().items
        selectIndexes = self.tblPresence.selectedIndexes()
        selectRowList = []
        eventIdList = []
        for selectIndex in selectIndexes:
            selectRow = selectIndex.row()
            if selectRow not in selectRowList:
                selectRowList.append(selectRow)
        for row, item in enumerate(items):
            if row in selectRowList:
                eventId = self.modelPresence.getEventId(row)
                if eventId and (eventId not in eventIdList):
                    eventData = [eventId, item[38], item[14], item[39]]
                    eventIdList.append(eventData)
        return eventIdList


    def getSelectedEventIdList(self, widgetIndex):
        if widgetIndex == 4:
            table = self.tblLeaved
            model = self.modelLeaved
        else:
           table =  self.tblPresence
           model = self.modelPresence
        items = table.model().items
        selectIndexes = table.selectedIndexes()
        selectRowList = []
        eventIdList = []
        for selectIndex in selectIndexes:
            selectRow = selectIndex.row()
            if selectRow not in selectRowList:
                selectRowList.append(selectRow)
        for row, item in enumerate(items):
            if row in selectRowList:
                eventId = model.getEventId(row)
                if eventId and (eventId not in eventIdList):
                    eventData = [eventId]
                    eventIdList.append(eventData)
        return eventIdList

    def prolongationFeed(self, eventIdList, typeFeed):
        for eventData in eventIdList:
            eventId = eventData[0] if eventData else None
            if eventId:
                db = QtGui.qApp.db
                tableEvent = db.table('Event')
                tableEventType = db.table('EventType')
                tableRBMealTime = db.table('rbMealTime')
                table = tableEvent.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
                eventTypeRecord = db.getRecordEx(table, [tableEventType['id'], tableEvent['relative_id']], [tableEvent['id'].eq(eventId), tableEventType['form'].like('003')])
                if eventTypeRecord:
                    eventType = forceRef(eventTypeRecord.value('id'))
                    if eventType:
                        patronId = forceRef(eventTypeRecord.value('relative_id'))
                        if typeFeed and not patronId:
                            return
                        begDatePresence = eventData[1] if len(eventData) >= 2 else None
                        plannedEndDatePresence = eventData[2] if len(eventData) >= 3 else None
                        endDatePresence = eventData[3] if len(eventData) >= 4 else None
                        QtGui.qApp.setWaitCursor()
                        try:
                            currentDate = QDate.currentDate()
                            nextDateFeed = QDateTime(currentDate.addDays(1), QTime()) if currentDate else None
                            if currentDate and nextDateFeed:
                                tableEventFeed = db.table('Event_Feed')
                                cond = [tableEventFeed['deleted'].eq(0),
                                        tableEventFeed['event_id'].eq(eventId),
                                        tableEventFeed['typeFeed'].eq(typeFeed)
                                        ]
                                recordsAll = db.getRecordList(tableEventFeed, '*', cond, 'Event_Feed.date ASC')
                                prevEventIdList = {}
                                if not recordsAll:
                                    prevEventId = None
                                    prevEventRecord = db.getRecordEx(tableEvent, [tableEvent['id'], tableEvent['prevEvent_id']], [tableEvent['id'].eq(eventId), tableEvent['deleted'].eq(0)])
                                    if prevEventRecord:
                                        prevId = forceRef(prevEventRecord.value('id'))
                                        prevEventId = forceRef(prevEventRecord.value('prevEvent_id'))
                                        prevEventIdList[prevId] = prevEventId
                                    while prevEventId:
                                        prevEventRecord = db.getRecordEx(tableEvent, [tableEvent['id'], tableEvent['prevEvent_id']], [tableEvent['id'].eq(prevEventId), tableEvent['deleted'].eq(0)])
                                        if prevEventRecord:
                                            prevEventId = forceRef(prevEventRecord.value('prevEvent_id'))
                                            prevId = forceRef(prevEventRecord.value('id'))
                                            prevEventIdList[prevId] = prevEventId
                                        else:
                                            prevEventId = None
                                newRecords = []
                                records = []
                                if not recordsAll and prevEventIdList:
                                    for prevId, prevEventId in prevEventIdList.items():
                                        if not records:
                                            cond = [tableEventFeed['deleted'].eq(0),
                                                    tableEventFeed['date'].dateEq(currentDate),
                                                    tableEventFeed['event_id'].eq(prevEventId),
                                                    tableEventFeed['typeFeed'].eq(typeFeed)
                                                    ]
                                            records = db.getRecordList(tableEventFeed, '*', cond, 'Event_Feed.date ASC')
                                else:
                                    cond = [tableEventFeed['deleted'].eq(0),
                                            tableEventFeed['date'].dateEq(currentDate),
                                            tableEventFeed['event_id'].eq(eventId),
                                            tableEventFeed['typeFeed'].eq(typeFeed)
                                            ]
                                    records = db.getRecordList(tableEventFeed, '*', cond, 'Event_Feed.date ASC')
                                cond = [tableEventFeed['deleted'].eq(0),
                                        tableEventFeed['date'].dateEq(nextDateFeed.date()),
                                        tableEventFeed['event_id'].eq(eventId),
                                        tableEventFeed['typeFeed'].eq(typeFeed)
                                        ]
                                recordsNextDate = db.getRecordList(tableEventFeed, '*', cond, 'Event_Feed.date ASC')
                                if not recordsNextDate:
                                    dateTimeList = [begDatePresence if begDatePresence else QDateTime(),
                                                    endDatePresence if endDatePresence else (QDateTime(plannedEndDatePresence) if plannedEndDatePresence else QDateTime())
                                                    ]
                                    if (not dateTimeList[0] or nextDateFeed.date() >= dateTimeList[0].date()) and (not dateTimeList[1] or nextDateFeed.date() <= dateTimeList[1].date()):
                                        for record in records:
                                            recordMealTime = db.getRecordEx(tableRBMealTime, '*', [tableRBMealTime['id'].eq(forceRef(record.value('mealTime_id')))])
                                            begTime = forceTime(recordMealTime.value('begTime'))
                                            endTime = forceTime(recordMealTime.value('endTime'))
                                            nextBegDateTime = nextDateFeed.setTime(begTime)
                                            nextBegDateTime = nextDateFeed
                                            nextEndDateTime = nextDateFeed.setTime(endTime)
                                            nextEndDateTime = nextDateFeed
                                            if ((not dateTimeList[0] or not nextBegDateTime or nextBegDateTime >= dateTimeList[0]) and (not dateTimeList[1] or not nextEndDateTime or nextEndDateTime.date() <= dateTimeList[1].date())) or ((not dateTimeList[0] or not nextBegDateTime or nextBegDateTime <= dateTimeList[0]) and (not dateTimeList[0] or not nextEndDateTime or nextEndDateTime > dateTimeList[0])) or ((not dateTimeList[1] or not nextBegDateTime or nextBegDateTime.date() < dateTimeList[1].date()) and (not dateTimeList[1] or not nextEndDateTime or nextEndDateTime.date() >= dateTimeList[1].date())):
                                                newRecord = tableEventFeed.newRecord()
                                                newRecord.setValue('date', toVariant(nextDateFeed))
                                                newRecord.setValue('mealTime_id', record.value('mealTime_id'))
                                                newRecord.setValue('finance_id', record.value('finance_id'))
                                                newRecord.setValue('refusalToEat', record.value('refusalToEat'))
                                                newRecord.setValue('typeFeed', toVariant(typeFeed))
                                                if typeFeed:
                                                    newRecord.setValue('patron_id', record.value('patron_id'))
                                                newRecord.setValue('diet_id', record.value('diet_id'))
                                                newRecords.append(newRecord)
                                        for newRecord in newRecords:
                                            recordsAll.append(newRecord)
                                        if recordsAll:
                                            self.saveFeedFromMenu(eventId, recordsAll, typeFeed)
                                        self.modelPresence.reset()
                                        self.on_selectionModelOrgStructure_currentChanged(None, None)
                        finally:
                            QtGui.qApp.restoreOverrideCursor()


    @pyqtSignature('')
    def on_mnuActionList_aboutToShow(self):
        widgetIndex = self.tabWidget.currentIndex()
        if widgetIndex == 1:
            widgetIndex = self.tabWidgetActionsClasses.currentIndex()
            if widgetIndex == 0:
                self.tblActionList.setFocus(Qt.TabFocusReason)
                currentIndex = self.tblActionList.currentIndex()
                self.actTranslateStatusActionInBegin.setEnabled(currentIndex.row() >= 0 and self.getIsAppointed())


    @pyqtSignature('')
    def on_mnuHospitalBeds_aboutToShow(self):
        widgetIndex = self.tabWidget.currentIndex()
        if widgetIndex == 0:
            self.tblHospitalBeds.setFocus(Qt.OtherFocusReason)
            currentIndex = self.tblHospitalBeds.currentIndex()
            isBusy = currentIndex.row() >= 0 and self.modelHospitalBeds.isBusy(currentIndex)
        elif widgetIndex == 1:
            self.tblPresence.setFocus(Qt.TabFocusReason)
            currentIndex = self.tblPresence.currentIndex()
            isBusy = currentIndex.row() >= 0
        elif widgetIndex == 2:
            self.tblReceived.setFocus(Qt.OtherFocusReason)
            currentIndex = self.tblReceived.currentIndex()
            isBusy = currentIndex.row() >= 0
        elif widgetIndex == 3:
            self.tblTransfer.setFocus(Qt.OtherFocusReason)
            currentIndex = self.tblTransfer.currentIndex()
            isBusy = currentIndex.row() >= 0
        elif widgetIndex == 4:
            self.tblLeaved.setFocus(Qt.OtherFocusReason)
            currentIndex = self.tblLeaved.currentIndex()
            isBusy = currentIndex.row() >= 0
        elif widgetIndex == 5:
            self.tblQueue.setFocus(Qt.OtherFocusReason)
            currentIndex = self.tblQueue.currentIndex()
            isBusy = currentIndex.row() >= 0
        app = QtGui.qApp
        isAdmin = app.isAdmin()
        isHBFeed = app.userHasRight(urHBFeed) or app.userHasRight(urHBEditCurrentDateFeed) or isAdmin
        isHBEditThermalSheet = app.userHasRight(urHBEditThermalSheet) or isAdmin
        isHBReadEvent = app.userHasRight(urHBReadEvent) or isAdmin
        isHBEditEvent = app.userHasRight(urHBEditEvent) or isAdmin
        isHBReadClientInfo = app.userHasRight(urHBReadClientInfo) or isAdmin
        isHBEditClientInfo = app.userHasRight(urHBEditClientInfo) or isAdmin
        isHBPlanning = app.userHasRight(urHBPlanning) or isAdmin
        isHBEditObservationStatus = False if widgetIndex == 0 else (app.userHasRight(urHBEditObservationStatus) or isAdmin)
        self.actOpenEvent.setEnabled(isBusy and widgetIndex and (isHBReadEvent or isHBEditEvent))
        self.actGroupJobAppointment.setEnabled(isBusy and widgetIndex==1) # and (isHBReadEvent or isHBEditEvent))
        self.actOpenClientVaccinationCard.setEnabled(isBusy and widgetIndex and QtGui.qApp.userHasAnyRight([urCanReadClientVaccination, urCanEditClientVaccination]))
        self.actEditMKB.setEnabled(isBusy and widgetIndex == 2 and app.userHasRight(urHBEditReceivedMKB))
        isRegTabReadAmbCard = app.userHasRight(urRegTabReadAmbCard) or isAdmin
        isRegTabWriteAmbCard = app.userHasRight(urRegTabWriteAmbCard) or isAdmin
        self.actAmbCardShow.setEnabled(isBusy and widgetIndex and (isRegTabReadAmbCard or isRegTabWriteAmbCard))
        self.actAmbCardShowToAction.setEnabled(isBusy and widgetIndex and (isRegTabReadAmbCard or isRegTabWriteAmbCard))
        self.actEditClientInfoBeds.setEnabled(isBusy and widgetIndex and (isHBReadClientInfo or isHBEditClientInfo))
        self.actGetFeedFromMenu.setVisible(forceBool(widgetIndex == 1) and isHBFeed)
        self.actGetFeedFromMenu.setEnabled(forceBool(widgetIndex == 1) and isBusy and isHBFeed)
        self.actGetFeedPatronFromMenu.setVisible(forceBool(widgetIndex == 1) and isHBFeed)
        self.actGetFeedPatronFromMenu.setEnabled(forceBool(widgetIndex == 1) and isBusy and isHBFeed)
        self.actTemperatureListEditor.setVisible(forceBool(widgetIndex == 1) and isHBEditThermalSheet)
        self.actTemperatureListEditor.setEnabled(forceBool(widgetIndex == 1) and isBusy and isHBEditThermalSheet)
        self.actStatusObservationClient.setEnabled(True if isBusy and isHBEditObservationStatus else False)
        self.actPlanning.setVisible(forceBool(widgetIndex == 6))
        self.actPlanning.setEnabled(True if isHBPlanning else False)
        self.actRelatedEventClient.setEnabled(isBusy)
        self.actPeriodActionsDialog.setEnabled(isBusy)
        self.actEditClientFeatures.setVisible(forceBool(widgetIndex == 1))
        self.actEditClientFeatures.setEnabled(isBusy)
        self.actEditPatronFeatures.setVisible(forceBool(widgetIndex == 1))
        self.actEditPatronFeatures.setEnabled(isBusy)
        self.actOpenClientDocumentTrackingHistory.setVisible(widgetIndex in (1, 4))
        self.actOpenClientDocumentTrackingHistory.setEnabled(app.userHasAnyRight([urRegTabReadLocationCard, urEditLocationCard]))
        self.actDocumentLocationGroupEditor.setVisible(widgetIndex in (1, 4))
        self.actDocumentLocationGroupEditor.setEnabled(True if app.userHasRight(urGroupEditorLocatAccountDocument) else False)
        self.actUpdateEventTypeByEvent.setEnabled(isBusy and widgetIndex > self.tabWidget.indexOf(self.tabFund) and (isAdmin or app.userHasRight(urUpdateEventTypeByEvent)))
        self.actEventJournalOfPerson.setEnabled(widgetIndex == 1 and app.isCheckEventJournalOfPerson() and QtGui.qApp.userHasRight(urEditEventJournalOfPerson))
        self.actEventJournalOfPerson.setVisible(widgetIndex == 1 and app.isCheckEventJournalOfPerson())
        self.actOpenPlanningEditor.setVisible(forceBool(widgetIndex == 6))
        self.actOpenPlanningEditor.setEnabled(forceBool(widgetIndex == 6))
        self.actAddAction.setVisible(forceBool(self.tabWidget.currentIndex() == self.tabWidget.indexOf(self.tabPresence)))
        if self.actAddAction.isVisible():
            currentActionsTable = self.getCurrentWidgetActionsClasses()
            isClosedEvent = self.getEventIsClosed(currentActionsTable.model().getEventId(currentActionsTable.currentRow()))
            self.actAddAction.setEnabled(forceBool(self.tabWidget.currentIndex() == self.tabWidget.indexOf(self.tabPresence)) and isBusy and app.userHasRight(urHBEditAction) and not isClosedEvent)

    @pyqtSignature('')
    def on_mnuEditActionEvent_aboutToShow(self):  # + +
        app = QtGui.qApp
        isAdmin = app.isAdmin()
        isHBReadEvent = app.userHasRight(urHBReadEvent) or isAdmin
        isHBEditEvent = app.userHasRight(urHBEditEvent) or isAdmin
        isHBReadClientInfo = app.userHasRight(urHBReadClientInfo) or isAdmin
        isHBEditClientInfo = app.userHasRight(urHBEditClientInfo) or isAdmin
        currentIndex = self.getCurrentActionsTable().currentIndex()
        self.actEditActionEvent.setEnabled(currentIndex.row() >= 0 and (isHBReadEvent or isHBEditEvent))
        self.actEditClientInfo.setEnabled(currentIndex.row() >= 0 and (isHBReadClientInfo or isHBEditClientInfo))
        self.actEditStatusObservationClient.setEnabled(currentIndex.row() >= 0)
        self.actTranslateStatusActionInBeginClass.setEnabled(currentIndex.row() >= 0 and self.getIsAppointed())
        currentActionsTable = self.getCurrentWidgetActionsClasses()
        self.actAddActionEvent.setEnabled(
            currentIndex.row() >= 0 and app.userHasRight(urHBEditAction) and
            not self.getEventIsClosed(currentActionsTable.model().getEventId(currentActionsTable.currentRow()))
        )

    def getIsAppointed(self):
        isAppointed = False
        if QtGui.qApp.userHasAnyRight([urHBActionEdit]):
            table = self.getCurrentActionsTable()
            selectedRows = self.getSelectedRows(table)
            for row in selectedRows:
                record = table.model().getRecordByRow(row)
                if record:
                    status = forceInt(record.value('status'))
                    if CActionStatus.appointed == status:
                        isAppointed = True
                        break
        return isAppointed


    def getCurrentActionsTableClientId(self, actionId):
        db = QtGui.qApp.db
        tableAction = db.table('Action')
        tableEvent = db.table('Event')
        table = tableAction.leftJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
        record = db.getRecord(table, 'Event.client_id', actionId)
        return forceRef(record.value('client_id')) if record else None


    @pyqtSignature('')
    def on_actAmbCardShow_triggered(self):
        self.ambCardShow()


    @pyqtSignature('')
    def on_actAmbCardShowToAction_triggered(self):
        self.ambCardShow()


    def ambCardShow(self):
        isRightAdmin =  QtGui.qApp.isAdmin()
        isRegTabReadAmbCard = QtGui.qApp.userHasRight(urRegTabReadAmbCard) or isRightAdmin
        isRegTabWriteAmbCard = QtGui.qApp.userHasRight(urRegTabWriteAmbCard) or isRightAdmin
        if isRegTabReadAmbCard or isRegTabWriteAmbCard:
            currentTableIndex = self.tabWidget.currentIndex()
            actionsClassesIndex = self.tabWidgetActionsClasses.currentIndex()
            if currentTableIndex == 1 and actionsClassesIndex != 0:
                currentTable = self.getCurrentActionsTable()
                actionId = currentTable.currentItemId()
                clientId = self.getCurrentActionsTableClientId(actionId) if actionId else None
                currentRow = currentTable.currentRow()
            else:
                currentTable = self.getCurrentTable()
                currentRow = currentTable.currentRow()
                clientId = currentTable.model().getClientId(currentRow)
            if clientId:
                try:
                    dialog = CAmbCardDialog(self, clientId)
                    if dialog.exec_():
                        pass
                finally:
                    dialog.deleteLater()
            currentTable.setCurrentRow(currentRow)
            if currentTableIndex == 1:
                self.on_tabWidgetActionsClasses_currentChanged(actionsClassesIndex)
        else:
            QtGui.QMessageBox.warning( self,
                                     u'Внимание!',
                                     u'Нет права на чтение и редактирование Мед.карты!',
                                     QtGui.QMessageBox.Ok,
                                     QtGui.QMessageBox.Ok)


    @pyqtSignature('')
    def on_actEditClientInfoBeds_triggered(self):
        self.editClient()

    @pyqtSignature('')
    def on_actEditClientFeatures_triggered(self):
        self.editClientFeatures()

    @pyqtSignature('')
    def on_actEditPatronFeatures_triggered(self):
        self.editPatronFeatures()

    @pyqtSignature('')
    def on_actOpenClientDocumentTrackingHistory_triggered(self):
        self.openClientDocumentTrackingHistory()

    @pyqtSignature('')
    def on_actDocumentLocationGroupEditor_triggered(self):
        self.openDocumentLocationgroupEditor()

    @pyqtSignature('')
    def on_actUpdateEventTypeByEvent_triggered(self):
        eventId = self.getCurrentEventId(self.tabWidget.currentIndex())
        if eventId:
            db = QtGui.qApp.db
            accountItemId = forceRef(db.translate('Account_Item', 'event_id', eventId, 'id'))
            if accountItemId:
                QtGui.QMessageBox.warning(self, u'Внимание!',
                                          u'По событию выставлен счёт, поэтому его тип не может быть изменён.',
                                          QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
            else:
                self.updateEventTypeByEvent(eventId)

    def updateEventTypeByEvent(self, eventId):
        if QtGui.qApp.userHasAnyRight([urAdmin, urUpdateEventTypeByEvent]):
            db = QtGui.qApp.db
            tableET = db.table('Event')
            record = db.getRecordEx(tableET, '*', [tableET['id'].eq(eventId), tableET['deleted'].eq(0)])
            eventTypeId = forceRef(record.value('eventType_id')) if record else None
            oldPrevEventId = forceRef(record.value('prevEvent_id')) if record else None
            clientId = forceRef(record.value('client_id')) if record else None
            date = forceDate(record.value('execDate')) if record else None
            setDate = forceDate(record.value('setDate')) if record else None
            orgId = forceInt(record.value('org_id')) if record else None
            if eventTypeId:
                tableETE = db.table('EventType_Event')
                cols = [tableETE['eventType_id']
                        ]
                cond = [tableETE['master_id'].eq(eventTypeId)
                        ]
                eventTypeIdList = db.getDistinctIdList(tableETE, cols, cond, 'EventType_Event.id')
                if eventTypeIdList:
                    dialog = CUpdateEventTypeByEvent(self, eventTypeIdList, eventTypeId, date, orgId, forceInt(clientId), setDate, eventId)
                    try:
                        if dialog.exec_():
                            newEventTypeId = dialog.getNewEventTypeId()
                            if newEventTypeId:
                                order = dialog.getOrder()
                                contractId = dialog.getContractId()
                                # eventTypeRecord = db.getRecordEx('EventType', 'changeExternalId', 'EventType.deleted=0 and EventType.id = {}'.format(newEventTypeId))
                                # if eventTypeRecord:
                                #     changeExternalId = forceBool(eventTypeRecord.value('changeExternalId'))
                                # else:
                                #     changeExternalId = False
                                # if changeExternalId:
                                #     counterId = getEventCounterId(newEventTypeId)
                                #     if counterId:
                                #         try:
                                #             externalId = QtGui.qApp.getDocumentNumber(clientId, counterId)
                                #             record.setValue('externalId', externalId)
                                #         except Exception as e:
                                #             QtGui.QMessageBox.critical(QtGui.qApp.mainWindow,
                                #                                     u'Внимание!',
                                #                                     u'Произошла ошибка при получении значения счетчика\n%s' % e,
                                #                                     QtGui.QMessageBox.Ok)
                                #             return False
                                #     else:
                                #         record.setValue('externalId', '')
                                record.setValue('eventType_id', toVariant(newEventTypeId))
                                if order > -1:
                                    record.setValue('order', toVariant(order+1))
                                if contractId:
                                    record.setValue('contract_id', toVariant(contractId))
                                idList = set([])
                                idListParents = set(db.getTheseAndParents(tableET, 'prevEvent_id',
                                                                          [eventId if eventId else self.prevEventId]))
                                idList ^= idListParents
                                idListDescendant = set(db.getDescendants(tableET, 'prevEvent_id',
                                                                         eventId if eventId else self.prevEventId))
                                idList ^= idListDescendant
                                if len(idList) < 2:
                                    prevEventTypeId = getEventPrevEventTypeId(newEventTypeId)
                                    prevEventId = getPrevEventIdByEventTypeId(prevEventTypeId,
                                                                              clientId) if prevEventTypeId else None
                                    if prevEventTypeId and oldPrevEventId != prevEventId:
                                        record.setValue('prevEvent_id', toVariant(prevEventId))
                            db.updateRecord(tableET, record)
                            self.on_selectionModelOrgStructure_currentChanged(None, None)
                    finally:
                        dialog.deleteLater()

    @pyqtSignature('')
    def on_actEventJournalOfPerson_triggered(self):
        index = self.tblPresence.currentIndex()
        row = index.row()
        eventId = self.modelPresence.getEventId(row) if row >= 0 else None
        if eventId:
            dialog = CExecPersonListEditorDialog(self, eventId)
            try:
                if dialog.exec_():
                    db = QtGui.qApp.db
                    tableEvent = db.table('Event')
                    cond = [tableEvent['deleted'].eq(0),
                            tableEvent['id'].eq(eventId)
                            ]
                    recordEvent = db.getRecordEx(tableEvent, '*', cond)
                    if recordEvent:
                        personId = forceRef(recordEvent.value('execPerson_id'))
                        setDate = forceDateTime(recordEvent.value('setDate'))
                        execDate = forceDateTime(recordEvent.value('execDate'))

                        tableEJOP = db.table('Event_JournalOfPerson')
                        cond = [tableEJOP['deleted'].eq(0),
                                tableEJOP['master_id'].eq(eventId)
                                ]
                        if setDate:
                            cond.append(tableEJOP['setDate'].ge(setDate))
                        if execDate:
                            cond.append(tableEJOP['setDate'].le(execDate))
                        record = db.getRecordEx(tableEJOP, [tableEJOP['execPerson_id']], cond, order = u'Event_JournalOfPerson.setDate DESC')
                        execPersonId = forceRef(record.value('execPerson_id')) if record else None
                        if execPersonId:
                            if personId != execPersonId:
                                res = QtGui.QMessageBox.warning(self,
                                                           u'Внимание!',
                                                           u'''Смена ответственного врача.\nОтветственный '%s' будет заменен на '%s'.\nВы подтверждаете изменения?''' % (forceString(QtGui.qApp.db.translate('vrbPersonWithSpeciality', 'id', personId, 'name')),
                                                                                                                                                                         forceString(QtGui.qApp.db.translate('vrbPersonWithSpeciality', 'id', execPersonId, 'name'))),
                                                           QtGui.QMessageBox.Ok|QtGui.QMessageBox.Cancel,
                                                           QtGui.QMessageBox.Cancel)
                                if res == QtGui.QMessageBox.Ok:
                                    recordEvent.setValue('execPerson_id', toVariant(execPersonId))
                                    db.updateRecord(tableEvent, recordEvent)
            finally:
                dialog.deleteLater()


    @pyqtSignature('')
    def on_actEditClientInfo_triggered(self):
        self.editClient()


    def editClient(self):
        isRightAdmin =  QtGui.qApp.isAdmin()
        isHBReadClientInfo = QtGui.qApp.userHasRight(urHBReadClientInfo) or isRightAdmin
        isHBEditClientInfo = QtGui.qApp.userHasRight(urHBEditClientInfo) or isRightAdmin
        if isHBReadClientInfo or isHBEditClientInfo:
            table = self.getCurrentTable()
            if table:
                tableIndex = table.currentIndex()
                row = tableIndex.row()
                if row > -1:
                    if self.tabWidget.currentIndex() in (6, ):
                        clientId = table.model().items[row][2]
                    elif self.tabWidget.currentIndex() in (4, 7, 8):
                        clientId = table.model().items[row][3]
                    elif self.tabWidget.currentIndex() == 1:
                        clientId = table.model().items[row][7]
                    else:
                        clientId = table.model().items[row][4]
                    if clientId:
                        from Registry.ClientEditDialog  import CClientEditDialog
                        dialog = CClientEditDialog(self)
                        try:
                            if clientId:
                                dialog.load(clientId)
                            dialog.setHBEditClientInfoRight(isHBEditClientInfo, True)
                            if dialog.exec_():
                                clientId = dialog.itemId()
                        finally:
                            dialog.deleteLater()
                        self.on_tabWidget_currentChanged(self.tabWidget.currentIndex())
        else:
            QtGui.QMessageBox.warning( self,
                         u'Внимание!',
                         u'Нет права на чтение и редактирование карты пациента!',
                         QtGui.QMessageBox.Ok,
                         QtGui.QMessageBox.Ok)


    def editClientFeatures(self):
        table = self.getCurrentTable()
        if table:
            tableIndex = table.currentIndex()
            row = tableIndex.row()
            if row > -1:
                if self.tabWidget.currentIndex() in (6, ):
                    clientId = table.model().items[row][2]
                elif self.tabWidget.currentIndex() in (4, 7, 8):
                    clientId = table.model().items[row][3]
                elif self.tabWidget.currentIndex() == 1:
                    clientId = table.model().items[row][7]
                else:
                    clientId = table.model().items[row][4]
                if clientId:
                    from HospitalBeds.ClientFeaturesEditDialog  import CClientFeaturesEditDialog
                    dialog = CClientFeaturesEditDialog(self, clientId)
                    try:
                        if clientId:
                            dialog.load(clientId)
                        if dialog.exec_():
                            clientId = dialog.itemId()
                            self.loadDataPresence()
                    finally:
                        dialog.deleteLater()
        return None

    def editPatronFeatures(self):
        table = self.getCurrentTable()
        if table:
            tableIndex = table.currentIndex()
            row = tableIndex.row()
            if row > -1:
                if self.tabWidget.currentIndex() in (6, ):
                    clientId = table.model().items[row][2]
                elif self.tabWidget.currentIndex() in (4, 7, 8):
                    clientId = table.model().items[row][3]
                elif self.tabWidget.currentIndex() == 1:
                    clientId = table.model().items[row][7]
                else:
                    clientId = table.model().items[row][4]
                if clientId:
                    patronId = forceRef(QtGui.qApp.db.translate('Event', 'client_id', clientId, 'relative_id'))
                    if patronId:
                        from HospitalBeds.ClientFeaturesEditDialog  import CClientFeaturesEditDialog
                        dialog = CClientFeaturesEditDialog(self, patronId)
                        try:
                            if patronId:
                                dialog.load(patronId)
                            if dialog.exec_():
                                patronId = dialog.itemId()
                                self.loadDataPresence()
                        finally:
                            dialog.deleteLater()
                    else:
                        QtGui.QMessageBox.warning( self,
                         u'Внимание!',
                         u'У данного пациента не определено лицо по уходу!',
                         QtGui.QMessageBox.Ok,
                         QtGui.QMessageBox.Ok)
        return None

    def openClientDocumentTrackingHistory(self):
        if QtGui.qApp.userHasAnyRight([urRegTabReadLocationCard, urEditLocationCard]):
            table = self.getCurrentTable()
            if table:
                tableIndex = table.currentIndex()
                row = tableIndex.row()
                clientId = table.model().getClientId(row)
                if clientId:
                    from Registry.ClientDocumentTracking import CClientDocumentTrackingList
                    dialog = CClientDocumentTrackingList(self, clientId)
                    try:
                        if dialog.exec_():
                            clientId = dialog.itemId()
                            self.loadDataPresence()
                    finally:
                        dialog.deleteLater()
        return None

    def openDocumentLocationgroupEditor(self):
        table = self.getCurrentTable()
        widgetIndex = self.tabWidget.currentIndex()
        if table:
            self.notSelectedRows = True
            eventIdList = self.getSelectedEventIdList(widgetIndex)
            if eventIdList:
                    QtGui.QMessageBox.information(self,
                            u'Внимание!',
                            u'В режиме группового изменения мест нахождения учетных документов, поиск соответствующих документов ведется от даты начала госпитализации!')
                    from Registry.ClientDocumentTracking import CDocumentLocationGroupEditor
                    dialog = CDocumentLocationGroupEditor(self, eventIdList)
                    try:
                        dialog.exec_()
                        if widgetIndex == 1:
                            self.loadDataPresence()
                        elif widgetIndex == 4:
                            self.loadDataLeaved()
                    finally:
                        dialog.deleteLater()
        return None

    def getCurrentTable(self):
        index = self.tabWidget.currentIndex()
        return [None, self.tblPresence, self.tblReceived, self.tblTransfer, self.tblLeaved, self.tblQueue][index]


    @pyqtSignature('')
    def on_actStatusObservationClient_triggered(self):
        self.updateStatusObservationClient()


    @pyqtSignature('')
    def on_btnPlanning_clicked(self):
        self.on_actPlanning_triggered()


    @pyqtSignature('')
    def on_actPlanning_triggered(self):
        widgetIndex = self.tabWidget.currentIndex()
        if widgetIndex==6:
            HospitalizationEvent = CHospitalizationPlanningFromQueue(self)
            HospitalizationEvent.exec_()
            self.on_selectionModelOrgStructure_currentChanged(None, None)
        HospitalizationEvent = None


    @pyqtSignature('')
    def on_actTranslateStatusActionInBeginClass_triggered(self):
        self.translateStatusActionInBegin()


    @pyqtSignature('')
    def on_actTranslateStatusActionInBegin_triggered(self):
        self.translateStatusActionInBegin()


    def translateStatusActionInBegin(self):
        widgetIndex = self.tabWidget.currentIndex()
        if widgetIndex == 1:
            try:
                actionIdList = []
                table = self.getCurrentActionsTable()
                if table:
                    selectedRows = self.getSelectedRows(table)
                    for row in selectedRows:
                        record = table.model().getRecordByRow(row)
                        if record:
                            status = forceInt(record.value('status'))
                            if CActionStatus.appointed == status:
                                actionId = forceRef(record.value('id'))
                                if actionId and actionId not in actionIdList:
                                    actionIdList.append(actionId)
                    if actionIdList:
                        db = QtGui.qApp.db
                        table = db.table('Action')
                        db.updateRecords(table, table['status'].eq(CActionStatus.started), [table['id'].inlist(actionIdList)])
                        self.on_tabWidgetActionsClasses_currentChanged(self.tabWidgetActionsClasses.currentIndex())
            except:
                pass


    @pyqtSignature('')
    def on_actRelatedEventClient_triggered(self):
        eventId = self.getCurrentEventId(self.tabWidget.currentIndex())
        if eventId:
            CRelatedEventListDialog(self, eventId).exec_()


    @pyqtSignature('')
    def on_actPeriodActionsDialog_triggered(self):
        if QtGui.qApp.userHasRight(urReadCheckPeriodActions) or QtGui.qApp.userHasRight(urEditCheckPeriodActions):
            widgetIndex = self.tabWidget.currentIndex()
            eventId = self.getCurrentEventId(widgetIndex)
            dialog = CCheckPeriodActions(self, [], eventId, None, True)
            try:
                if dialog.exec_():
                    pass
            finally:
                dialog.deleteLater()


    @pyqtSignature('')
    def on_actOpenPlanningEditor_triggered(self):
        eventId = self.modelQueue.getEventId(self.selectionModelQueue.selectedRows()[0].row())
        planningActionId = self.modelQueue.getPlanningActionId(eventId)
        if planningActionId:
            self.editAction(planningActionId)
            self.on_selectionModelOrgStructure_currentChanged(None, None)


    @pyqtSignature('')
    def on_actEditStatusObservationClient_triggered(self):
        self.updateStatusObservationClient()


    def updateStatusObservationClient(self):
        try:
            clientIdList = []
            table = self.getCurrentTable()
            if table:
                selectedRows = self.getSelectedRows(table)
                for row in selectedRows:
                    if self.tabWidget.currentIndex() in (4, 7, 8):
                        clientIdList.append(table.model().items[row][3])
                    elif self.tabWidget.currentIndex() in (6, ):
                        clientIdList.append(table.model().items[row][2])
                    elif self.tabWidget.currentIndex() == 1:
                        clientIdList.append(table.model().items[row][7])
                    else:
                        clientIdList.append(table.model().items[row][4])
                if clientIdList:
                    dialog = CStatusObservationClientEditor(self, clientIdList)
                    try:
                        if dialog.exec_():
                            self.on_selectionModelOrgStructure_currentChanged(None, None)
                    finally:
                        dialog.deleteLater()
        except:
            pass

    @pyqtSignature('')
    def on_actEditActionEvent_triggered(self):
        currentActionsTable = self.getCurrentActionsTable()
        actionId = currentActionsTable.currentItemId()
        if actionId:
            eventId = forceRef(QtGui.qApp.db.translate('Action', 'id', actionId, 'event_id'))
            if eventId:
                formClass = getEventFormClass(eventId)
                dialog = formClass(self)
                try:
                    QtGui.qApp.setCurrentClientId(currentActionsTable.model().getClientId(currentActionsTable.currentRow()))
                    dialog.load(eventId)
                    if dialog.exec_():
                        filter = {}
                        actionType = self.cmbFilterActionType.value()
                        if actionType:
                            filter['actionTypeId'] = actionType
                        filter['status'] = self.cmbFilterActionStatus.value()
                        filter['isUrgent'] = self.chkFilterIsUrgent.isChecked()
                        filter['begDatePlan'] = self.edtFilterBegDatePlan.date()
                        filter['endDatePlan'] = self.edtFilterEndDatePlan.date()
                        filter['begDateByStatus'] = self.edtFilterBegDateByStatus.date()
                        filter['endDateByStatus'] = self.edtFilterEndDateByStatus.date()
                        self.updateActionsList(filter, self.modelPresence.eventIdList if self.tabWidgetActionsClasses.currentIndex() > 0 else [self.getCurrentEventId(1)])
                finally:
                    QtGui.qApp.setCurrentClientId(None)
                    dialog.deleteLater()
        if not actionId:
            currentActionsTable.setFocus(Qt.TabFocusReason)
        elif actionId:
            currentActionsTable.setCurrentItemId(actionId)

    @pyqtSignature('')
    def on_actAddAction_triggered(self):
        widgetIndex = self.tabWidget.currentIndex()
        if widgetIndex == self.tabWidget.indexOf(self.tabPresence):
            if self.tabWidgetActionsClasses.currentIndex() == self.tabWidgetActionsClasses.indexOf(self.tabActionList):
                eventId = self.getCurrentEventId(widgetIndex)
                if eventId:
                    currentTable, currentRow, newActionIdList = self.addActionTabPresence(eventId, 0)
                    # for actionId in newActionIdList:
                    #     if actionId and QtGui.qApp.userHasAnyRight([urHBActionEdit]):
                    #         self.editAction(actionId)
                    self.updateActionsList({}, [self.getCurrentEventId(self.tabWidget.indexOf(self.tabPresence))])
                    currentTable.setCurrentRow(currentRow)

    @pyqtSignature('')
    def on_actAddActionEvent_triggered(self):
        widgetIndex = self.tabWidgetActionsClasses.currentIndex()
        if widgetIndex in [self.tabWidgetActionsClasses.indexOf(self.tabActionsStatus),
                           self.tabWidgetActionsClasses.indexOf(self.tabActionsDiagnostic),
                           self.tabWidgetActionsClasses.indexOf(self.tabActionsCure),
                           self.tabWidgetActionsClasses.indexOf(self.tabActionsMisc)]:
            currentActionsTable = self.getCurrentWidgetActionsClasses()
            actionId = currentActionsTable.currentItemId()
            if actionId:
                db = QtGui.qApp.db
                table = db.table('Action')
                record = db.getRecordEx(table, [table['event_id']], [table['id'].eq(actionId), table['deleted'].eq(0)])
                eventId = forceRef(record.value('event_id')) if record else None
                if eventId and canAddActionToExposedEvent(self, eventId):
                    currentTable, currentRow, newActionIdList = self.addActionTabPresence(eventId, widgetIndex)
                    # for actionId in newActionIdList:
                    #     if actionId:
                    #         self.editAction(actionId)
                    self.cmbFilterActionType.setClass(widgetIndex - 1)
                    self.cmbFilterActionType.setValue(self.__actionTypeIdListByClassPage[widgetIndex - 1])
                    self.on_buttonBoxAction_apply()
                    currentTable.setCurrentRow(currentRow)
    
    @pyqtSignature('')
    def on_actOpenEvent_triggered(self):
        QtGui.qApp.callWithWaitCursor(self, self.openEvent)


    @pyqtSignature('')
    def on_actGroupJobAppointment_triggered(self):
        self.openGroupJobAppointment()


    def openGroupJobAppointment(self):
        currentTable = self.getCurrentTable()
        currentRow = currentTable.currentRow()
        eventData = self.getEventByActionIdList()
        if eventData:
            eventIdList = eventData.keys()
            if eventIdList:
                try:
                    db = QtGui.qApp.db
                    clientCache = CTableRecordCache(db, db.forceTable('Client'), u'*', capacity=None)
                    dialog = CGroupJobAppointmentDialog(self, eventIdList, eventData, clientCache)
                    if dialog.exec_():
                        pass
                finally:
                    dialog.deleteLater()
        currentTable.setCurrentRow(currentRow)


    @pyqtSignature('')
    def on_btnTreatmentAppointment_clicked(self):
        self.openTreatmentAppointment()


    def openTreatmentAppointment(self):
        orgStructureId = self.getOrgStructureId(self.treeOrgStructure.currentIndex())
        if orgStructureId:
            currentTable = self.getCurrentTable()
            currentRow = currentTable.currentRow()
            currentTable.selectAll()
            eventData = self.getEventByActionIdList()
            if eventData:
                eventIdList = eventData.keys()
                if eventIdList:
                    try:
                        db = QtGui.qApp.db
                        clientCache = CTableRecordCache(db, db.forceTable('Client'), u'*', capacity=None)
                        dialog = CTreatmentAppointmentDialog(self, orgStructureId, eventIdList, eventData, clientCache)
                        if dialog.exec_():
                                pass
                    finally:
                        dialog.deleteLater()
        currentTable.setCurrentRow(currentRow)


    @pyqtSignature('')
    def on_actOpenClientVaccinationCard_triggered(self):
        table = self.getCurrentTable()
        row = table.currentRow()
        if row >= 0:
            clientId = table.model().getClientId(row)
            if clientId:
                openClientVaccinationCard(self, clientId)


    @pyqtSignature('')
    def on_actEditMKB_triggered(self):
        currentIndex = self.tblReceived.currentIndex()
        if currentIndex and currentIndex.isValid():
            self.updateReceivedMKB(currentIndex.row())


    def setLeavedAction(self):
        isRightAdmin =  QtGui.qApp.isAdmin()
        isHBEditEvent = QtGui.qApp.userHasRight(urHBEditEvent) or isRightAdmin
        isLeavedTabPresence = QtGui.qApp.userHasRight(urLeavedTabPresence) or isRightAdmin
        isHBLeaved = QtGui.qApp.userHasRight(urHBLeaved) or isRightAdmin
        if isHBEditEvent or isLeavedTabPresence or isHBLeaved:
            widgetIndex = self.tabWidget.currentIndex()
            eventId = self.getCurrentEventId(widgetIndex)
            if eventId:
                try:
                    formClass = getEventFormClass(eventId)
                    dialog = formClass(self)
                    record = QtGui.qApp.db.getRecord(QtGui.qApp.db.table('Event'), '*', eventId)
                    dialog.setRecord(record)
                    flatCode = u'leaved%'
                    db = QtGui.qApp.db
                    tableActionType = db.table('ActionType')
                    idListActionType = db.getIdList(tableActionType, [tableActionType['id']], [tableActionType['flatCode'].like(flatCode), tableActionType['deleted'].eq(0)])
                    actionTypeIdValue = None
                    if len(idListActionType) > 1:
                        dialogActionType = CActionTypeDialogTableModel(self, idListActionType)
                        if dialogActionType.exec_():
                            actionTypeIdValue = dialogActionType.currentItemId()
                    else:
                        actionTypeIdValue = idListActionType[0] if idListActionType else None
                    if actionTypeIdValue:
                        dialog.setLeavedAction(actionTypeIdValue, self.leavingParams)
                    dialog.tabMes.cmbMes.setValue(self.leavingParams['mesId'])
                    dialog.tabMes.cmbMesSpecification.setValue(self.leavingParams['mesSpecification'])
                    dialog.done(1)
                    if dialog.result() == QtGui.QDialog.Accepted:
                        cutFeed(eventId, self.leavingParams['ExecDateTime'])
                    self.on_selectionModelOrgStructure_currentChanged(None, None)
                finally:
                    dialog.deleteLater()
        else:
            QtGui.QMessageBox.warning( self,
                                     u'Внимание!',
                                     u'Нет права на выписывание пациента!',
                                     QtGui.QMessageBox.Ok,
                                     QtGui.QMessageBox.Ok)

    def openEvent(self):
        isRightAdmin =  QtGui.qApp.isAdmin()
        isHBReadEvent = QtGui.qApp.userHasRight(urHBReadEvent) or isRightAdmin
        isHBEditEvent = QtGui.qApp.userHasRight(urHBEditEvent) or isRightAdmin
        if isHBReadEvent or isHBEditEvent:
            currentTable = self.getCurrentTable()
            currentRow = currentTable.currentRow()
            widgetIndex = self.tabWidget.currentIndex()
            col = -1
            reverse = False
            headerClickable = currentTable.horizontalHeader().isClickable()
            if headerClickable:
                headerSortingCol = currentTable.model().headerSortingCol.items()
                if len(headerSortingCol) > 0:
                    col, reverse = headerSortingCol[0]
            eventId = self.getCurrentEventId(widgetIndex)
            if eventId:
                try:
                    formClass = getEventFormClass(eventId)
                    dialog = formClass(self)
                    QtGui.qApp.setCurrentClientId(currentTable.model().getClientId(currentRow))
                    dialog.load(eventId)
                    QtGui.qApp.restoreOverrideCursor()
                    dialog.setHBUpdateEventRight(isHBEditEvent, True)
                    if dialog.exec_():
                        self.on_selectionModelOrgStructure_currentChanged(None, None)
                        if headerClickable and col >= 0:
                            onHeaderColClicked = self.getOnHeaderColClicked()
                            if onHeaderColClicked:
                                currentTable.horizontalHeader().setSortIndicator(col, reverse)
                                currentTable.model().headerSortingCol[col] = not reverse
                                onHeaderColClicked(col)
                finally:
                    QtGui.qApp.setCurrentClientId(None)
                    dialog.deleteLater()
            currentTable.setCurrentRow(currentRow)
            if widgetIndex == 1:
                self.updateActionsList({}, [self.getCurrentEventId(1)])
        else:
            QtGui.QMessageBox.warning( self,
                                     u'Внимание!',
                                     u'Нет права на чтение и редактирование события!',
                                     QtGui.QMessageBox.Ok,
                                     QtGui.QMessageBox.Ok)


    @pyqtSignature('bool')
    def on_chkDefaultOrgStructure_clicked(self, checked):
        tabIndex = self.tabWidget.currentIndex()
        if tabIndex == 1:
            self.loadDataPresence()
        elif tabIndex == 2:
            self.loadDataReceived()


    @pyqtSignature('bool')
    def on_chkInvolution_clicked(self, checked):
        self.cmbInvolute.setEnabled(checked)
        self.cmbInvolute.setCurrentIndex(0)


    @pyqtSignature('int')
    def on_cmbReceived_currentIndexChanged(self, index):
        if index == 1:
            self.cmbLocationClient.setEnabled(True)
        else:
            self.cmbLocationClient.setEnabled(False)
        self.cmbFilterIsPermanent.setEnabled(index == 1)
        self.cmbFilterType.setEnabled(index == 1)
        self.cmbFilterBedProfile.setEnabled(index == 1)


    @pyqtSignature('int')
    def on_cmbLeaved_currentIndexChanged(self, index):
        widgetIndex = self.tabWidget.currentIndex()
        if widgetIndex == 4:
            self.cmbFilterIsPermanent.setEnabled(index != 0)
            self.cmbFilterType.setEnabled(index != 0)
            self.cmbFilterBedProfile.setEnabled(index != 0)
        elif widgetIndex == 5:
            self.cmbFilterIsPermanent.setEnabled(True)
            self.cmbFilterType.setEnabled(True)
            self.cmbFilterBedProfile.setEnabled(True)


    @pyqtSignature('int')
    def on_cmbRenunciationAction_currentIndexChanged(self, index):
        self.cmbFilterIsPermanent.setEnabled(index == 1)
        self.cmbFilterType.setEnabled(index == 1)
        self.cmbFilterBedProfile.setEnabled(index == 1)
        self.reasonRenunciation()


    @pyqtSignature('int')
    def on_cmbFeed_currentIndexChanged(self, index):
        if index == 0:
            self.edtDateFeed.setDate(QDate.currentDate())
        self.edtDateFeed.setEnabled(forceBool(index) and self.cmbFeed.isEnabled())


    @pyqtSignature('int')
    def on_tabWidget_currentChanged(self, index):
        app = QtGui.qApp
        begDays = u''
        self.setQueueWidgetVisible(False)
        self.btnHospitalization.setEnabled(False)
        self.btnHospitalization.setText(u'Госпитализация (F9)')
        self.btnTransfer.setEnabled(False)
        self.cmbFilterAccountingSystem.setEnabled(False)
        self.cmbStatusObservation.setEnabled(False)
        self.edtFilterClientId.setEnabled(False)
        self.btnFindClientInfo.setEnabled(False)
        self.edtFilterEventId.setEnabled(False)
        self.btnLeaved.setEnabled(False)
        self.edtFilterCode.setEnabled(False)
        self.cmbSexBed.setEnabled(False)
        self.spbBedAgeFor.setEnabled(False)
        self.spbBedAgeTo.setEnabled(False)
        self.cmbFilterIsPermanent.setEnabled(False)
        self.cmbFilterType.setEnabled(False)
        self.cmbFilterBedProfile.setEnabled(False)
        self.btnHospitalBedProfileList.setEnabled(True)
        self.cmbDeath.setEnabled(False)
        self.cmbFilterSchedule.setEnabled(False)
        self.chkInvolution.setChecked(False)
        self.cmbInvolute.setCurrentIndex(0)
        self.cmbInvolute.setEnabled(False)
        self.chkInvolution.setEnabled(False)
        self.btnFinance.setEnabled(True)
        self.cmbFinance.setEnabled(True)
        self.btnContract.setEnabled(True)
        self.cmbContract.setEnabled(True)
        self.cmbFeed.setEnabled(False)
        self.edtDateFeed.setEnabled(False)
        self.cmbFilterBusy.setEnabled(False)
        self.cmbLocationClient.setEnabled(True)
        self.cmbLocationClient.setCurrentIndex(0)
        self.lblReceived.setVisible(False)
        self.cmbReceived.setVisible(False)
        self.lblTransfer.setVisible(False)
        self.cmbTransfer.setVisible(False)
        self.lblLeaved.setVisible(False)
        self.cmbLeaved.setVisible(False)
        self.cmbOrder.setEnabled(False)
        self.cmbEventType.setEnabled(False)
        self.cmbPlaceCall.setEnabled(False)
        self.chkStayOrgStructure.setVisible(False)
        self.cmbRenunciation.setEnabled(False)
        self.cmbRenunciationAction.setEnabled(False)
        self.edtPresenceDayValue.setEnabled(False)
        self.edtFilterBegDate.setEnabled(True)
        self.edtFilterEndDate.setEnabled(True)
        self.edtFilterBegTime.setEnabled(True)
        self.edtFilterEndTime.setEnabled(True)
        self.cmbSex.setEnabled(True)
        self.spbAgeFor.setEnabled(True)
        self.spbAgeTo.setEnabled(True)
        self.btnFeed.setVisible(False)
        self.btnTreatmentAppointment.setVisible(False)
        self.btnTemperatureList.setVisible(False)
        self.chkDefaultOrgStructure.setVisible(False)
        self._isChkDefaultOrgStructureVisible = False
        self.cmbEventClosedType.setEnabled(False)
        self.chkPlacement.setEnabled(False)
        self.chkPlacement.setChecked(False)
        self.cmbFilterDeliverBy.setEnabled(False)
        self.cmbFilterDocumentTypeForTracking.setEnabled(False)
        self.edtMES.setEnabled(False)
        self.cmbMKBFilter.setEnabled(True)
        self.chkPresenceActionActiviti.setVisible(False)
        self.btnPlanning.setVisible(False)
        self.btnHospitalization.setEnabled(False)
        if index == 0:
            self.edtFilterCode.setEnabled(True)
            self.cmbSexBed.setEnabled(True)
            self.spbBedAgeFor.setEnabled(True)
            self.spbBedAgeTo.setEnabled(True)
            self.cmbFilterSchedule.setEnabled(True)
            self.cmbFilterBusy.setEnabled(True)
            self.chkInvolution.setEnabled(True)
            self.cmbOrder.setEnabled(False)
            self.cmbEventType.setEnabled(False)
            self.cmbPlaceCall.setEnabled(False)
            self.cmbSex.setEnabled(False)
            self.spbAgeFor.setEnabled(False)
            self.spbAgeTo.setEnabled(False)
            self.btnFinance.setEnabled(False)
            self.cmbFinance.setEnabled(False)
            self.btnContract.setEnabled(False)
            self.cmbContract.setEnabled(False)
            self.btnHospitalBedProfileList.setEnabled(False)
            self.cmbMKBFilter.setEnabled(False)
            self.updateHospitalBeds()
        elif index == 1:
            self.chkPresenceActionActiviti.setVisible(True)
            self.btnHospitalization.setEnabled(app.userHasRight(urHBHospitalization))
            self.btnTransfer.setEnabled(app.userHasRight(urAdmin) or app.userHasRight(urHBTransfer) or app.userHasRight(urHospitalTabReceived))
            self.edtFilterCode.setEnabled(True)
            self.edtFilterBegDate.setDate(QDate.currentDate())
            self.edtFilterEndDate.setDate(QDate())
            self.edtFilterBegTime.setTime(QtGui.qApp.medicalDayBegTime())
            self.edtFilterEndTime.setTime(QtGui.qApp.medicalDayBegTime().addSecs(-60))
            #self.edtFilterBegDate.setEnabled(False)
            #self.edtFilterEndDate.setEnabled(False)
            #self.edtFilterBegTime.setEnabled(True)
            #self.edtFilterEndTime.setEnabled(False)
            self.cmbFilterSchedule.setEnabled(True)
            self.edtPresenceDayValue.setEnabled(True)
            self.cmbFeed.setEnabled(True)
            self.edtDateFeed.setEnabled(self.cmbFeed.isEnabled() and self.cmbFeed.currentIndex() > 0)
            self.cmbLocationClient.setEnabled(True)
            self.btnLeaved.setEnabled(app.userHasRight(urAdmin) or app.userHasRight(urHBLeaved) or app.userHasRight(urLeavedTabPresence))
            self.btnFeed.setVisible(True)
            self.btnTreatmentAppointment.setVisible(True)
            self.btnTemperatureList.setVisible(app.userHasRight(urAdmin) or app.userHasRight(urHBEditThermalSheet))
            self.chkDefaultOrgStructure.setVisible(self._isEnabledChkDefaultOrgStructure)
            self._isChkDefaultOrgStructureVisible = True
            self.chkPlacement.setEnabled(True)
            self.cmbFilterIsPermanent.setEnabled(True)
            self.cmbFilterType.setEnabled(True)
            self.cmbFilterBedProfile.setEnabled(True)
            self.cmbFilterDocumentTypeForTracking.setEnabled(True)
            if not self.firstInput:
                self.loadDataPresence()
                self.tblPresence.setFocus(Qt.TabFocusReason)
                rowCount = self.modelPresence.rowCount()
                if rowCount > 0:
                    self.tblPresence.setCurrentRow(0)
                self.updateActionsList({}, [self.getCurrentEventId(1)])
                countBegDays = self.modelPresence.getBegDays()
                begDays = (u'   (' + forceString(countBegDays) + u' койко-дней)') if countBegDays else u''
            else:
                self.firstInput = False
        elif index == 2:
            self.btnHospitalization.setEnabled(app.userHasRight(urHBHospitalization) or app.userHasRight(urHospitalTabReceived))
            self.lblReceived.setVisible(True)
            self.cmbReceived.setVisible(True)
            self.cmbPlaceCall.setEnabled(True)
            self.cmbFeed.setEnabled(True)
            self.edtDateFeed.setEnabled(self.cmbFeed.isEnabled() and self.cmbFeed.currentIndex() > 0)
            self.cmbLocationClient.setEnabled(self.cmbReceived.currentIndex() == 1)
            self.btnHospitalBedProfileList.setEnabled(True)
            self.chkDefaultOrgStructure.setVisible(self._isEnabledChkDefaultOrgStructure)
            self._isChkDefaultOrgStructureVisible = True
            self.cmbFilterDeliverBy.setEnabled(True)
            self.loadDataReceived()
        elif index == 3:
            self.cmbFeed.setEnabled(True)
            self.cmbFilterSchedule.setEnabled(True)
            self.edtDateFeed.setEnabled(self.cmbFeed.isEnabled() and self.cmbFeed.currentIndex() > 0)
            self.cmbLocationClient.setEnabled(True)
            self.lblTransfer.setVisible(True)
            self.cmbTransfer.setVisible(True)
            self.chkStayOrgStructure.setEnabled(True)
            self.loadDataTransfer()
        elif index == 4:
            self.cmbFilterSchedule.setEnabled(True)
            self.cmbEventClosedType.setEnabled(True)
            self.lblLeaved.setVisible(True)
            self.cmbLeaved.setVisible(True)
            self.cmbLeaved.setItemText(1, u'без выписки')
            self.cmbLeaved.setItemText(2, u'из отделений')
            self.cmbFilterDocumentTypeForTracking.setEnabled(True)
            self.reasonRenunciateDeath()
            self.cmbDeath.setEnabled(True)
            self.edtMES.setEnabled(True)
            self.lblDeath.setText(u'Исход госпитализации')
            self.loadDataLeaved()
            countBegDays = self.modelLeaved.getBegDays()
            begDays = (u'   (' + forceString(countBegDays) + u' койко-дней)') if countBegDays else u''
        elif index == 5:
            self.setQueueWidgetVisible(True)
            self.btnHospitalization.setEnabled(app.userHasRight(urHBHospitalization) or app.userHasRight(urHospitalTabPlanning))
            self.cmbFilterDocumentTypeForTracking.setEnabled(True)
            self.btnPlanning.setVisible(True)
            self.loadDataQueue()
        if index != 0:
            self.cmbFilterAccountingSystem.setEnabled(True)
            self.cmbStatusObservation.setEnabled(True)
            self.edtFilterClientId.setEnabled(True)
            self.btnFindClientInfo.setEnabled(True)
            self.cmbOrder.setEnabled(True)
            self.cmbEventType.setEnabled(True)
            self.edtFilterEventId.setEnabled(True)
        self.lblCountRecordList.setText(formatRecordsCount(self.getCurrentWidgetRowCount(index)) + begDays)
        self.preparePrintBtn(index)


    @pyqtSignature('int')
    def on_tabWidgetActionsClasses_currentChanged(self, index):
        self.grbActionFilter.setVisible(not index == 0)
        if index > 0:
            if not self.notSelectedRows:
                self.on_actClearSelectionRow_triggered()
            self.cmbFilterActionType.setClass(index-1)
            self.cmbFilterActionType.setValue(self.__actionTypeIdListByClassPage[index-1])
            self.on_buttonBoxAction_apply()
        else:
            self.tblPresence.setFocus(Qt.TabFocusReason)
            if self.notSelectedRows:
                self.updateActionsList({}, [self.getCurrentEventId(1)])
            else:
                self.setActionsIdList([], None)


    def getCurrentActionsTable(self):
        index = self.tabWidgetActionsClasses.currentIndex()
        return [self.tblActionList, self.tblActionsStatus, self.tblActionsDiagnostic, self.tblActionsCure, self.tblActionsMisc][index]


    def setActionsIdList(self, idList, posToId):
        self.getCurrentActionsTable().setIdList(idList, posToId)


    @pyqtSignature('bool')
    def on_chkFileAttachActionList_clicked(self, checked):
        self.cmbFileAttachActionList.setEnabled(checked)
        self.cmbFilterActionList.setEnabled(not checked)


    @pyqtSignature('bool')
    def on_chkFileAttachStatus_clicked(self, checked):
        self.cmbFileAttachStatus.setEnabled(checked)
        self.cmbFilterActionStatus.setEnabled(not checked)


    def updateActionsList(self, filter, eventIdList = [], posToId=None):
        actionClass = self.tabWidgetActionsClasses.currentIndex()-1
        if eventIdList and self.notSelectedRows:
            db = QtGui.qApp.db
            table = db.table('Action')
            tableEvent = db.table('Event')
            currentTable = self.getCurrentActionsTable()
            order = currentTable.order() if currentTable.order() else ['Event.execDate DESC', table['id'].name()]
            queryTable = table.leftJoin(tableEvent, tableEvent['id'].eq(table['event_id']) )
            cond = [table['deleted'].eq(0), tableEvent['deleted'].eq(0)]
            if 'Client' in order:
                tableClient = db.table('Client')
                queryTable = queryTable.leftJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
            if 'AT.name' in order:
                tableAT = db.table('ActionType').alias('AT')
                queryTable = queryTable.leftJoin(tableAT, db.joinAnd([tableAT['id'].eq(table['actionType_id']), tableAT['deleted'].eq(0)]))
            if 'vrbSetPersonWithSpeciality.name' in order:
                tableSetPerson = db.table('vrbPersonWithSpeciality').alias('vrbSetPersonWithSpeciality')
                queryTable = queryTable.leftJoin(tableSetPerson, tableSetPerson['id'].eq(table['setPerson_id']))
            if 'vrbPersonWithSpeciality.name' in order:
                tablePersonSP = db.table('vrbPersonWithSpeciality')
                queryTable = queryTable.leftJoin(tablePersonSP, tablePersonSP['id'].eq(table['person_id']))
            cond.append(table['event_id'].inlist(eventIdList))
            actionTypeTSIdList = getActionTypeIdListByFlatCode(u'temperatureSheet%')
            if actionClass > -1:
                if 'actionTypeId' in filter:
                    actionTypeIdList = getActionTypeDescendants(filter['actionTypeId'], actionClass)
                    cond.append(table['actionType_id'].inlist(actionTypeIdList))
                else:
                    cond.append(table['actionType_id'].name()+' IN (SELECT ActionType.id FROM ActionType WHERE ActionType.class=%d)' % actionClass)
                if actionTypeTSIdList:
                    cond.append(table['actionType_id'].notInlist(actionTypeTSIdList))
                begDatePlan = filter.get('begDatePlan', None)
                isUrgent = filter.get('isUrgent', 0)
                endDatePlan = filter.get('endDatePlan', None)
                if isUrgent:
                    cond.append(table['isUrgent'].eq(1))
                if begDatePlan or endDatePlan:
                    cond.append('DATE(Action.`plannedEndDate`) != 0')
                if begDatePlan:
                    cond.append(table['plannedEndDate'].dateGe(begDatePlan))
                if endDatePlan:
                    cond.append(table['plannedEndDate'].dateLe(endDatePlan))
                status =  filter.get('status', None)
                if status in CHealthResortDialog.mapActionStatusToDateField:
                    dateFieldName = CHealthResortDialog.mapActionStatusToDateField[status]
                    begDateByStatus = filter.get('begDateByStatus', QDate())
                    if begDateByStatus:
                        cond.append(table[dateFieldName].dateGe(begDateByStatus))
                    endDateByStatus = filter.get('endDateByStatus', QDate())
                    if endDateByStatus:
                        cond.append(table[dateFieldName].dateLe(begDateByStatus))
                if self.chkFileAttachStatus.isChecked():
                    tableActionFA = db.table('Action_FileAttach')
                    fileAttachActionList = self.cmbFileAttachStatus.currentIndex()
                    if fileAttachActionList == 0:
                        condAF = [tableActionFA['deleted'].eq(0),
                                  tableActionFA['master_id'].eq(table['id'])]
                        cond.append(db.notExistsStmt(tableActionFA, condAF))
                    else:
                        queryTable = queryTable.innerJoin(tableActionFA, tableActionFA['master_id'].eq(table['id']))
                        cond.append(tableActionFA['deleted'].eq(0))
                        if fileAttachActionList == 1:
                            cond.append(tableActionFA['respSignatureBytes'].isNull())
                            cond.append(tableActionFA['orgSignatureBytes'].isNull())
                        elif fileAttachActionList == 2:
                            cond.append(tableActionFA['respSignatureBytes'].isNotNull())
                            cond.append(tableActionFA['orgSignatureBytes'].isNull())
                        elif fileAttachActionList == 3:
                            cond.append(tableActionFA['orgSignatureBytes'].isNotNull())
                else:
                    if status is None:
                        pass
                    elif isinstance(status, (list, tuple)):
                        cond.append(table['status'].inlist(status))
                    else:
                        cond.append(table['status'].eq(status))
            elif actionClass == -1:
                if self.chkFileAttachActionList.isChecked():
                    tableActionFA = db.table('Action_FileAttach')
                    fileAttachActionList = self.cmbFileAttachActionList.currentIndex()
                    if fileAttachActionList == 0:
                        condAF = [tableActionFA['deleted'].eq(0),
                                  tableActionFA['master_id'].eq(table['id'])]
                        cond.append(db.notExistsStmt(tableActionFA, condAF))
                    else:
                        queryTable = queryTable.innerJoin(tableActionFA, tableActionFA['master_id'].eq(table['id']))
                        cond.append(tableActionFA['deleted'].eq(0))
                        if fileAttachActionList == 1:
                            cond.append(tableActionFA['respSignatureBytes'].isNull())
                            cond.append(tableActionFA['orgSignatureBytes'].isNull())
                        elif fileAttachActionList == 2:
                            cond.append(tableActionFA['respSignatureBytes'].isNotNull())
                            cond.append(tableActionFA['orgSignatureBytes'].isNull())
                        elif fileAttachActionList == 3:
                            cond.append(tableActionFA['orgSignatureBytes'].isNotNull())
                else:
                    status = self.cmbFilterActionList.value()
                    if status is None:
                        pass
                    elif isinstance(status, (list, tuple)):
                        cond.append(table['status'].inlist(status))
                    else:
                        cond.append(table['status'].eq(status))
                begDirectionDate = self.edtBegDirectionDate.date()
                if begDirectionDate:
                    cond.append(table['directionDate'].dateGe(begDirectionDate))
                endDirectionDate = self.edtEndDirectionDate.date()
                if endDirectionDate:
                    cond.append(table['directionDate'].dateLe(endDirectionDate))
                classActions = []
                if self.chkListStatus.isChecked():
                    classActions.append(u'0')
                if self.chkListDiagnostic.isChecked():
                    classActions.append(u'1')
                if self.chkListCure.isChecked():
                    classActions.append(u'2')
                if self.chkListMisc.isChecked():
                    classActions.append(u'3')
                if classActions:
                    cond.append(table['actionType_id'].name()+' IN (SELECT ActionType.id FROM ActionType WHERE ActionType.class IN ('+', '.join([classAction for classAction in classActions])+'))')
                if actionTypeTSIdList:
                    cond.append(table['actionType_id'].notInlist(actionTypeTSIdList))
            try:
                QtGui.qApp.setWaitCursor()
                idList = db.getDistinctIdList(queryTable,
                               table['id'].name(),
                               cond,
                               order)
                self.setActionsIdList(idList, posToId)
            finally:
                QtGui.qApp.restoreOverrideCursor()
        else:
            self.setActionsIdList([], None)


    def getActionTypeDescendants2(self, actionTypeId):
        db = QtGui.qApp.db
        tableActionType = db.table('ActionType')
        result = set([actionTypeId])
        parents = [actionTypeId]
        classCond = db.joinOr([tableActionType['class'].eq(1), tableActionType['class'].eq(2)])
        while parents:
            cond = tableActionType['group_id'].inlist(parents)
            if classCond:
                cond = [cond, classCond]
                children = set(db.getIdList(tableActionType, where=cond))
                newChildren = children-result
                result |= newChildren
                parents = newChildren
        return list(result)


    @pyqtSignature('QAbstractButton*')
    def on_buttonBoxActionList_clicked(self, button):
        buttonCode = self.buttonBoxActionList.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.updateActionsList({}, [self.getCurrentEventId(1)])
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.cmbFilterActionList.setCurrentIndex(1)
            self.edtBegDirectionDate.setDate(self.getEventSetDate(self.getCurrentEventId(1)))
            self.edtEndDirectionDate.setDate(QDate())
            self.chkListStatus.setChecked(False)
            self.chkListDiagnostic.setChecked(True)
            self.chkListCure.setChecked(True)
            self.chkListMisc.setChecked(False)
            self.chkFileAttachActionList.setChecked(False)
            self.cmbFileAttachActionList.setCurrentIndex(0)
            self.on_chkFileAttachActionList_clicked(False)
            self.updateActionsList({}, [self.getCurrentEventId(1)])


    @pyqtSignature('QAbstractButton*')
    def on_buttonBoxAction_clicked(self, button):
        buttonCode = self.buttonBoxAction.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.on_buttonBoxAction_apply()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_buttonBoxAction_reset()


    def on_buttonBoxAction_reset(self):
        self.cmbFilterActionType.setValue(0)
        self.cmbFilterActionStatus.setCurrentIndex(1)
        self.chkFilterIsUrgent.setChecked(False)
        self.edtFilterBegDatePlan.setDate(QDate())
        self.edtFilterEndDatePlan.setDate(QDate())
        self.edtFilterBegDateByStatus.setDate(QDate())
        self.edtFilterEndDateByStatus.setDate(QDate())
        self.chkFileAttachStatus.setChecked(False)
        self.cmbFileAttachStatus.setCurrentIndex(0)
        self.on_chkFileAttachStatus_clicked(False)
        filter = {}
        filter['status'] = self.cmbFilterActionStatus.value()
        filter['isUrgent'] = self.chkFilterIsUrgent.isChecked()
        filter['begDatePlan'] = self.edtFilterBegDatePlan.date()
        filter['endDatePlan'] = self.edtFilterEndDatePlan.date()
        filter['begDateByStatus'] = self.edtFilterBegDateByStatus.date()
        filter['endDateByStatus'] = self.edtFilterEndDateByStatus.date()
        self.updateActionsList(filter, self.modelPresence.eventIdList if self.tabWidgetActionsClasses.currentIndex()!= 0 else [self.getCurrentEventId(1)])


    def on_buttonBoxAction_apply(self):
        filter = {}
        actionType = self.cmbFilterActionType.value()
        if actionType:
            filter['actionTypeId'] = actionType
        filter['status'] = self.cmbFilterActionStatus.value()
        filter['isUrgent'] = self.chkFilterIsUrgent.isChecked()
        filter['begDatePlan'] = self.edtFilterBegDatePlan.date()
        filter['endDatePlan'] = self.edtFilterEndDatePlan.date()
        filter['begDateByStatus'] = self.edtFilterBegDateByStatus.date()
        filter['endDateByStatus'] = self.edtFilterEndDateByStatus.date()
        self.updateActionsList(filter, self.modelPresence.eventIdList if self.tabWidgetActionsClasses.currentIndex()!= 0 else [self.getCurrentEventId(1)])


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelHospitalBeds_currentRowChanged(self, current, previous):
        eventId = self.tblHospitalBeds.currentItemId()
        self.modelInvoluteBeds.loadItems(eventId)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelPresence_currentRowChanged(self, current, previous):
        if self.notSelectedRows:
            self.edtBegDirectionDate.setDate(self.getEventSetDate(self.getCurrentEventId(1)))
            self.updateActionsList({}, [self.getCurrentEventId(1)])
        else:
            self.setActionsIdList([], None)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelActionList_currentRowChanged(self, current, previous):
        actionTypeName = ''
        actionCountStr = ''
        actionId = self.tblActionList.currentItemId()
        if actionId:
            db = QtGui.qApp.db
            tableAction = db.table('Action')
            tableActionType = db.table('ActionType')
            record = db.getRecordEx(tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id'])), [tableActionType['name'], tableAction['specifiedName'], tableAction['aliquoticity'], tableAction['event_id'], tableAction['begDate'], tableAction['actionType_id']], [tableAction['id'].eq(actionId), tableAction['deleted'].eq(0), tableActionType['deleted'].eq(0)])
            if record:
                eventId = forceRef(record.value('event_id'))
                begDate = forceDate(record.value('begDate'))
                actionTypeId = forceRef(record.value('actionType_id'))
                name = forceString(record.value('name'))
                specifiedName = forceString(record.value('specifiedName'))
                actionTypeName = name + (' ' + specifiedName if specifiedName else '')
                if eventId:
                    actionCount = db.getDistinctCount(tableAction, 'Action.id', [tableAction['event_id'].eq(eventId), tableAction['actionType_id'].eq(actionTypeId), tableAction['deleted'].eq(0), tableAction['begDate'].dateEq(begDate)])
                    actionCountStr = QString('<b>[%s]</b> '%(forceString(actionCount)))
        self.lblActionTypeName.setText(actionCountStr + actionTypeName)


    @pyqtSignature('QModelIndex')
    def on_tblPresence_clicked(self, index):
        selectedRows = []
        rowCount = self.tblPresence.model().rowCount()
        for index in self.tblPresence.selectedIndexes():
            if index.row() < rowCount:
                row = index.row()
                if row not in selectedRows:
                    selectedRows.append(row)
        if len(selectedRows) > 1:
            self.notSelectedRows = False
            self.setActionsIdList([], None)
        else:
            self.notSelectedRows = True
            self.updateActionsList({}, [self.getCurrentEventId(1)])


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelActionsStatus_currentRowChanged(self, current, previous):
        actionId = self.tblActionsStatus.currentItemId()
        self.updateActionInfo(actionId)
        self.updateAmbCardPropertiesTable(current, self.tblActionsStatusProperties, previous)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelActionsDiagnostic_currentRowChanged(self, current, previous):
        actionId = self.tblActionsDiagnostic.currentItemId()
        self.updateActionInfo(actionId)
        self.updateAmbCardPropertiesTable(current, self.tblActionsDiagnosticProperties, previous)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelActionsCure_currentRowChanged(self, current, previous):
        actionId = self.tblActionsCure.currentItemId()
        self.updateActionInfo(actionId)
        self.updateAmbCardPropertiesTable(current, self.tblActionsCureProperties, previous)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelActionsMisc_currentRowChanged(self, current, previous):
        actionId = self.tblActionsMisc.currentItemId()
        self.updateActionInfo(actionId)
        self.updateAmbCardPropertiesTable(current, self.tblActionsMiscProperties, previous)


    @pyqtSignature('int')
    def on_modelActionsStatus_itemsCountChanged(self, count):
        self.lblActionsStatusCount.setText(formatRecordsCount(count))


    @pyqtSignature('int')
    def on_modelActionsDiagnostic_itemsCountChanged(self, count):
        self.lblActionsDiagnosticCount.setText(formatRecordsCount(count))


    @pyqtSignature('int')
    def on_modelActionsCure_itemsCountChanged(self, count):
        self.lblActionsCureCount.setText(formatRecordsCount(count))


    @pyqtSignature('int')
    def on_modelActionsMisc_itemsCountChanged(self, count):
        self.lblActionsMiscCount.setText(formatRecordsCount(count))


    @pyqtSignature('QModelIndex')
    def on_tblActionList_doubleClicked(self, index):
        self.on_btnActionEdit_clicked()


    @pyqtSignature('QModelIndex')
    def on_tblActionsStatus_doubleClicked(self, index):
        self.on_btnActionEdit_clicked()
        self.on_buttonBoxAction_apply()


    @pyqtSignature('QModelIndex')
    def on_tblActionsDiagnostic_doubleClicked(self, index):
        self.on_btnActionEdit_clicked()
        self.on_buttonBoxAction_apply()


    @pyqtSignature('QModelIndex')
    def on_tblActionsCure_doubleClicked(self, index):
        self.on_btnActionEdit_clicked()
        self.on_buttonBoxAction_apply()


    @pyqtSignature('QModelIndex')
    def on_tblActionsMisc_doubleClicked(self, index):
        self.on_btnActionEdit_clicked()
        self.on_buttonBoxAction_apply()


    @pyqtSignature('int')
    def on_cmbFilterActionType_currentIndexChanged(self, index):
        index = self.tabWidgetActionsClasses.currentIndex()-1
        if index > -1:
            self.__actionTypeIdListByClassPage[index] = self.cmbFilterActionType.value()


    @pyqtSignature('int')
    def on_cmbFilterActionStatus_currentIndexChanged(self, index):
        actionStatus = self.cmbFilterActionStatus.value()
        enabledDatesByStatus = actionStatus in CHealthResortDialog.mapActionStatusToDateField
        self.edtFilterBegDateByStatus.setEnabled(enabledDatesByStatus)
        self.edtFilterEndDateByStatus.setEnabled(enabledDatesByStatus)


    def focusActions(self, actionId=None, newActionId=None):
        currentActionsTable = self.getCurrentActionsTable()
        if not actionId and not newActionId:
            currentActionsTable.setFocus(Qt.TabFocusReason)
        elif newActionId:
            currentActionsTable.setCurrentItemId(newActionId)
        elif actionId:
            currentActionsTable.setCurrentItemId(actionId)


    def on_btnActionEdit_clicked(self):
        if QtGui.qApp.userHasAnyRight([urHBActionEdit]):
            actionId = self.getCurrentActionsTable().currentItemId()
            newActionId = None
            if actionId:
                newEventId, newActionId = self.editAction(actionId)
                self.updateActionsList({}, [self.getCurrentEventId(1)])
            self.focusActions(actionId, newActionId)


    @pyqtSignature('')
    def on_btnDocumentLocationList_clicked(self):
        self.documentLocationList = []
        self.lblDocumentLocationList.setText(u'не задано')
        dialog = CDocumentLocationListDialog(self)
        if dialog.exec_():
            self.documentLocationList = dialog.values()
            if self.documentLocationList:
                db = QtGui.qApp.db
                table = db.table('rbDocumentTypeLocation')
                records = db.getRecordList(table, [table['name']], [table['id'].inlist(self.documentLocationList)])
                nameList = []
                for record in records:
                    nameList.append(forceString(record.value('name')))
                self.lblDocumentLocationList.setText(u', '.join(name for name in nameList if name))


    def editAction(self, actionId):
        dialog = CActionEditDialog(self)
        try:
            dialog.load(actionId)
            if dialog.exec_():
                filter = {}
                actionType = self.cmbFilterActionType.value()
                if actionType:
                    filter['actionTypeId'] = actionType
                filter['status'] = self.cmbFilterActionStatus.value()
                filter['isUrgent'] = self.chkFilterIsUrgent.isChecked()
                filter['begDatePlan'] = self.edtFilterBegDatePlan.date()
                filter['endDatePlan'] = self.edtFilterEndDatePlan.date()
                filter['begDateByStatus'] = self.edtFilterBegDateByStatus.date()
                filter['endDateByStatus'] = self.edtFilterEndDateByStatus.date()
                self.updateActionsList(filter, self.modelPresence.eventIdList if self.tabWidgetActionsClasses.currentIndex()!= 0 else [self.getCurrentEventId(1)])
                return (dialog.itemId(), dialog.newActionId)
            else:
                self.updateActionInfo(actionId)
                self.updateClientsListRequest = True
            return (None, dialog.newActionId)
        finally:
            dialog.deleteLater()


    def updateActionInfo(self, actionId):
        db = QtGui.qApp.db
        tableAction = db.table('Action')
        tableEvent = db.table('Event')
        table = tableAction.leftJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
        record = db.getRecord(table, 'Event.client_id', actionId)
        clientId = forceRef(record.value('client_id')) if record else None
        if not clientId:
            clientId = self.currentClientId()
        QtGui.qApp.setCurrentClientId(clientId)


    def dateTimeToString(self, value):
        return  value.toString('dd.MM.yyyy hh:mm:ss')


    def currentClientId(self):
        return QtGui.qApp.currentClientId()


    def addEqCond(self, cond, table, fieldName, filter, name):
        if name in filter:
            cond.append(table[fieldName].eq(filter[name]))


    def getCurrentWidgetRowCount(self, widgetIndex):
        if widgetIndex == 0:
            return self.modelHospitalBeds.rowCount()
        elif widgetIndex == 1:
            return self.modelPresence.rowCount()
        elif widgetIndex == 2:
            return self.modelReceived.rowCount()
        elif widgetIndex == 3:
            return self.modelTransfer.rowCount()
        elif widgetIndex == 4:
            return self.modelLeaved.rowCount()
        elif widgetIndex == 5:
            return self.modelQueue.rowCount()
        return 0

    def addActionTabPresence(self, eventId, currentWidget):
        def removeExtCols(db, srcRecord):
            tableAction = db.table('Action')
            record = tableAction.newRecord()
            for i in xrange(record.count()):
                record.setValue(i, srcRecord.value(record.fieldName(i)))
            return record

        def getActionIdxLast(db, eventId, actionTypeClass):
            tableAction = db.table('Action')
            tableActionType = db.table('ActionType')
            recordAction = db.getRecordEx(tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id'])), 'MAX(Action.idx) AS idxLast', [tableAction['event_id'].eq(eventId), tableAction['deleted'].eq(0), tableActionType['deleted'].eq(0), tableActionType['class'].eq(actionTypeClass)])
            return forceInt(recordAction.value('idxLast')) if recordAction else -1

        def saveNewAction(db, eventId, actionTypeId, action, idxLastDict):
            actionType = CActionTypeCache.getById(actionTypeId)
            actionTypeClass = actionType.class_
            idxLast = idxLastDict.get(actionTypeClass, -1)
            if idxLast < 0:
                idxLast = getActionIdxLast(db, eventId, actionTypeClass) + 1
                idxLastDict[actionTypeClass] = idxLast
            else:
                idxLast += 1
                idxLastDict[actionTypeClass] = idxLast
            outRecord = removeExtCols(db, action.getRecord())
            if outRecord:
                action._record = outRecord
                id = action.save(eventId, idx=idxLast, checkModifyDate=False)
                if id:
                    if id not in newActionIdList:
                        newActionIdList.append(id)
                    action.getRecord().setValue('id', toVariant(id))
                    checkTissueJournalStatusByActions([(action.getRecord(), action)])
            return idxLastDict
        newActionIdList = []
        currentRow = None
        if eventId and currentWidget >= 0:
            actionTypes = []
            currentTable = self.getCurrentWidgetActionsClasses()
            currentRow = currentTable.currentRow()
            isCheckAddOutsideActions = False
            isCloseEventByAction = False
            formClass = getEventFormClass(eventId)
            dialog = formClass(self)
            QtGui.qApp.setCounterController(CCounterController(self))
            QtGui.qApp.setJTR(dialog)
            try:
                db = QtGui.qApp.db
                tableEvent = db.table('Event')
                dialog.load(eventId)
                record = db.getRecordEx(tableEvent, '*', [tableEvent['id'].eq(eventId), tableEvent['deleted'].eq(0)])
                dialog.setRecord(record)
                clientId = forceRef(record.value('client_id')) if record else None
                mesId = forceRef(record.value('MES_id')) if record else None
                mesSpecificationId = forceRef(record.value('mesSpecification_id')) if record else None
                dialog.tabMes.cmbMes.setValue(toVariant(mesId))
                dialog.tabMes.cmbMesSpecification.setValue(toVariant(mesSpecificationId))
                tabWidgetList = [dialog.tabToken,
                                 dialog.tabStatus,
                                 dialog.tabDiagnostic,
                                 dialog.tabCure,
                                 dialog.tabMisc
                                ]
                dialog.tabWidget.setCurrentWidget(tabWidgetList[currentWidget])
                actionTypes, actionTypeClasses, hasTblActions, widget = self.getNewActionTypes(dialog)
                updateTabList = []
                notAddedActions = []
                isEventCSGRequired = getEventCSGRequired(dialog.eventTypeId)
                actionsTabsList = dialog.getActionsTabsList()
                from Events.ActionCreateDialog import CActionCreateDialog
                showEditorForEveryAction = True
                
                for actionTypeId, action, csgRecord in actionTypes:
                    res = True
                    actionType = CActionTypeCache.getById(actionTypeId)
                    if u'moving' in actionType.flatCode.lower():
                        for record in dialog.modelActionsSummary._items:
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
                        
                relatedItems = {}
                for actionTypeId, action, csgRecord in actionTypes:
                    relatedActionTypes = CActionTypeCache.getById(actionTypeId).getRelatedActionTypes()
                    relatedItems[action] = []
                    for actionType, isRequired in relatedActionTypes.items():
                        if isRequired:
                            itemRecord = db.table('Action').newRecord()
                            itemRecord.setValue('actionType_id', actionType)
                            item = CAction.getFilledAction(dialog, itemRecord, actionType)
                            relatedItems[action].append((actionType, item, None))
                for items in relatedItems.values():
                    actionTypes.extend(items)
                if showEditorForEveryAction:
                    model = None
                    for actionTypeId, action, csgRecord in actionTypes:
                        createDialog = None
                        try:
                            createDialog = CActionCreateDialog(dialog)
                            createDialog.load(action.getRecord(), action, clientId)
                            if createDialog.exec_():
                                if len(actionTypeClasses) > 1:
                                    if hasTblActions:
                                        model = dialog.tblActions.model()
                                        for actionTypeId, action, csgRecord in actionTypes:
                                            class_ = forceInt(QtGui.qApp.db.translate('ActionType', 'id', actionTypeId, 'class'))
                                            actionsTab = actionsTabsList[class_]
                                            if actionsTab not in updateTabList:
                                                updateTabList.append(actionsTab)
                                            index = model.index(model.rowCount()-1, 0)
                                            model.setData(index, toVariant(actionTypeId), presetAction=action)
                                            if isEventCSGRequired:
                                                actionsTab.cmbCSG.addActionToCSG(action.getRecord(), csgRecord)
                                        model.emitAllChanged()
                                    else:
                                        for actionTypeId, action, csgRecord in actionTypes:
                                            class_ = forceInt(QtGui.qApp.db.translate('ActionType', 'id', actionTypeId, 'class'))
                                            actionsTab = actionsTabsList[class_]
                                            if actionsTab not in updateTabList:
                                                updateTabList.append(actionsTab)
                                            model = actionsTab.tblAPActions.model()
                                            model.addRow(actionTypeId, presetAction=action)
                                            if isEventCSGRequired:
                                                actionsTab.cmbCSG.addActionToCSG(action.getRecord(), csgRecord)
                                else:
                                    for actionTypeId, action, csgRecord in actionTypes:
                                        class_ = forceInt(QtGui.qApp.db.translate('ActionType', 'id', actionTypeId, 'class'))
                                        actionsTab = actionsTabsList[class_]
                                        if actionsTab not in updateTabList:
                                            updateTabList.append(actionsTab)
                                        model = actionsTab.tblAPActions.model()
                                        index = model.index(model.rowCount()-1, 0)
                                        model.setData(index, toVariant(actionTypeId), presetAction=action)
                                        if isEventCSGRequired:
                                            actionsTab.cmbCSG.addActionToCSG(action.getRecord(), csgRecord)
                            else:
                                notAddedActions.append((actionTypeId, action, csgRecord))
                        finally:
                            createDialog.deleteLater()
                    if model:
                        model.emitAllChanged()
                for item in notAddedActions:
                    actionTypes.remove(item)
                for actionsTab in updateTabList:
                    actionsTab.updateActionEditor()
                    actionsTab.onActionCurrentChanged()
                if len(actionTypeClasses) == 1:
                    dialog.tabWidget.setCurrentWidget(widget)
                isEventCSGRequired = getEventCSGRequired(dialog.eventTypeId)
                actionList = []
                for actionTypeId, action, csgRecord in actionTypes:
                    if action:
                        isActionClose = bool(action.getType().closeEvent)
                        if isActionClose and not isCloseEventByAction:
                            isCloseEventByAction = isActionClose
                        actionList.append((action.getRecord(), action))
                if actionList:
                    showTime = getEventShowTime(dialog.eventTypeId)
                    if showTime:
                        begDateEvent = QDateTime(dialog.edtBegDate.date(), dialog.edtBegTime.time())
                        endDateEvent = QDateTime(dialog.edtEndDate.date(), dialog.edtEndTime.time())
                    else:
                        begDateEvent = dialog.edtBegDate.date()
                        endDateEvent = dialog.edtEndDate.date()
                    isCheckAddOutsideActions = dialog.checkAddOutsideActionsDataEntered(begDateEvent, endDateEvent, actionList)
                dialog.done(0)
            finally:
                QtGui.qApp.unsetJTR(dialog)
                QtGui.qApp.delAllCounterValueIdReservation()
                QtGui.qApp.setCounterController(None)
                dialog.destroy()
                dialog.deleteLater()
            if isCheckAddOutsideActions:
                isAddAction = False
                idxLastDict = {}
                if len(actionTypes) > 0:
                    for actionTypeId, action, csgRecord in actionTypes:
                        if action:
                            if isEventCSGRequired and csgRecord:
                                action.getRecord().setValue('eventCSG_id', csgRecord.value('id'))
                            idxLastDict = saveNewAction(db, forceRef(action.getRecord().value('event_id')), actionTypeId, action, idxLastDict)
                            if action in relatedItems.keys() and action.getId():
                                for item in relatedItems[action]:
                                    item[1].setMasterId(action.getId())
                                    item[1].getRecord().setValue('master_id', action.getId())
                                    item[1].getRecord().setValue('person_id', action.getRecord().value('person_id'))
                            isAddAction = True
                if isCloseEventByAction and isAddAction:
                    recordEvent = db.getRecordEx(tableEvent, 'Event.*', [tableEvent['id'].eq(eventId), tableEvent['deleted'].eq(0)])
                    if recordEvent:
                        eventExecDate = forceDate(recordEvent.value('execDate'))
                        if not eventExecDate:
                            self.checkValueMessage(u'Добавлено Мероприятие требующее закрытия Случая Обслуживания! Для этого откройте на редактирование Случай Обслуживания и внесите необходимые правки.', False, None)
                if len(newActionIdList) > 1:
                    if currentWidget > 0:
                        self.cmbFilterActionType.setClass(currentWidget-1)
                        self.cmbFilterActionType.setValue(self.__actionTypeIdListByClassPage[currentWidget-1])
                        self.on_buttonBoxAction_apply()
                    else:
                        self.updateActionsList({}, [self.getCurrentEventId(self.tabWidget.indexOf(self.tabPresence))])
                    currentTable.setCurrentRow(currentRow)
        return currentTable, currentRow, newActionIdList

    def getCurrentWidgetActionsClasses(self):
        index = self.tabWidgetActionsClasses.currentIndex()
        return [self.tblPresence, self.tblActionsStatus, self.tblActionsDiagnostic, self.tblActionsCure, self.tblActionsMisc][index]

    def getNewActionTypes(self, dialog):
        if dialog.isReadOnly():
            return [], [], False, None
        if hasattr(dialog, 'tabWidget'):
            widget = dialog.tabWidget.currentWidget()
            cond = []
            widgetClass = {}
            if hasattr(dialog, 'tabToken'):
                cond.append(dialog.tabToken)
                widgetClass[dialog.tabToken] = [0, 1, 2, 3]
            if hasattr(dialog, 'tabMes'):
                cond.append(dialog.tabMes)
                widgetClass[dialog.tabMes] = [0, 1, 2, 3]
            if hasattr(dialog, 'tabStatus'):
                cond.append(dialog.tabStatus)
                widgetClass[dialog.tabStatus] = [0]
            if hasattr(dialog, 'tabDiagnostic'):
                cond.append(dialog.tabDiagnostic)
                widgetClass[dialog.tabDiagnostic] = [1]
            if hasattr(dialog, 'tabCure'):
                cond.append(dialog.tabCure)
                widgetClass[dialog.tabCure] = [2]
            if hasattr(dialog, 'tabMisc'):
                cond.append(dialog.tabMisc)
                widgetClass[dialog.tabMisc] = [3]
            if widget not in cond:
                return [], [], False, None
        else:
            return [], [], False, None
        if hasattr(dialog, 'tblActions'):
            hasTblActions = True
        else:
            hasTblActions = False
        orgStructureId = QtGui.qApp.currentOrgStructureId()
        financeCode = forceStringEx(QtGui.qApp.db.translate('rbFinance', 'id', dialog.eventFinanceId, 'code'))
        if financeCode:
            financeCode = financeCode in ('3', '4')
        existsActionTypesList = []
        if hasattr(dialog, 'modelActionsSummary'):
            for item in dialog.modelActionsSummary.items():
                existsActionTypesList.append(forceRef(item.value('actionType_id')))
        actionTypeClasses = widgetClass.get(widget, [0, 1, 2, 3])
        actionTypes = selectActionTypes( dialog if len(actionTypeClasses) != 1 else widget,
                                         dialog,
                                         actionTypeClasses,
                                         orgStructureId,
                                         dialog.eventTypeId,
                                         dialog.contractId,
                                         dialog.getMesId(),
                                         financeCode,
                                         dialog._id,
                                         existsActionTypesList,
                                         visibleTblSelected=True,
                                         contractTariffCache=dialog.contractTariffCache,
                                         clientMesInfo=dialog.getClientMesInfo(),
                                         eventDate = dialog.edtBegDate.date() if dialog.edtBegDate.date() else dialog.edtEndDate.date(),
                                       )
        return actionTypes, actionTypeClasses, hasTblActions, widget

    def getEventIsClosed(self, eventId):
        if eventId:
            db = QtGui.qApp.db
            tableEvent = db.table('Event')
            record = db.getRecordEx(tableEvent, [tableEvent['isClosed']], [tableEvent['id'].eq(eventId), tableEvent['deleted'].eq(0)])
            return forceBool(record.value('isClosed')) if record else True
        return True
