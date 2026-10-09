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
## Обслуживание пациентов: Реестр пациентов + список событий + ....
##
#############################################################################
import json

from PyQt4         import QtGui
from PyQt4.QtCore import Qt, QDate, QDateTime, QMetaObject, QObject, QRegExp, QVariant, pyqtSignature, SIGNAL, QTime, QByteArray

from Surveillance.SurveillanceDialog import CSurveillanceDialog, isSurveillanceActive
from Events.ActionsSelector import selectActionTypes
from library.Attach.AttachedFile import CAttachedFilesModel
from library.Counter import CCounterController
from Events.TeethEventInfo import CEmergencyTeethEventInfo
from library.crbcombobox                    import CRBModel, CRBModelDataCache
from library.database                       import addCondLike, undotLikeMask, CTableRecordCache, decorateString
from library.DateEdit                       import CDateEdit
from library.DialogBase                     import CConstructHelperMixin
from library.ICDUtils                       import MKBwithoutSubclassification
from library.InDocTable import CRBLikeEnumInDocTableCol, CRecordListModel, CBoolInDocTableCol, CDateTimeInDocTableCol, CEnumInDocTableCol, CInDocTableCol, CRBInDocTableCol
from library.Pacs.Explorer                  import CPacsExplorer
from library.PreferencesMixin               import CDialogPreferencesMixin
from library.PrintInfo                      import CDateInfo, CInfoContext, CTimeInfo
from library.PrintTemplates                 import (addButtonActions,
                                                    additionalCustomizePrintButton,
                                                    applyTemplate,
                                                    directPrintTemplate,
                                                    getFirstPrintTemplate,
                                                    getPrintAction,
                                                    getPrintTemplates,
                                                    CPrintAction
                                                   )
from library.RBCheckTable                   import CRBCheckTableModel
from library.RecordLock                     import CRecordLockMixin
from library.Utils import (addDots, addDotsBefore, agreeNumberAndWord, copyFields, exceptionToUnicode, forceBool,
                           forceDate, forceDateTime, forceInt, forceRef, forceString, forceStringEx, formatDays,
                           formatNum, formatRecordsCount, formatRecordsCount2, formatSex, formatSNILS, getPref, quote,
                           smartDict, toVariant, trim, calcAgeTuple, getPrefBool, anyToUnicode, unformatSNILS)

from Accounting.AccountingDialog import CAccountingDialog
from DataCheck.RegistryControlDoubles import CRegistryControlDoubles
from DataCheck.RegistryClientListControlDoubles import CRegistryClientListControlDoubles
from Events.Action                          import CActionTypeCache, CAction, CActionType, initActionProperties
from Events.ActionStatus                    import CActionStatus
from Events.ActionEditDialog                import CActionEditDialog
from Events.ActionGroupSignDialog import CActionGroupSignDialog
from F088.F088EditDialog                    import CF088EditDialog
from F088.F0882022EditDialog                import CF0882022EditDialog
from F088.F088CreateDialog                  import CF088CreateDialog
from F090.F090CreateDialog                  import createF090
from F090.F090EditDialog                    import CF090EditDialog
from F111.F111EditDialog                    import CF111EditDialog
from Events.ActionInfo import CLocActionInfoList, CActionTypeInfo, CActionInfo
from Events.ActionPropertiesTable           import CActionPropertiesTableModel
from Events.ActionTypeDialog                import CActionTypeDialogTableModel
from Events.ActionCreateDialog              import CActionCreateDialog, CTempInvalidActionCreateDialog
from Events.CreateEvent                     import editEvent, requestNewEvent
from Events.EventInfo import CEmergencyEventInfoList, CVisitInfoListEx, CVisitInfo, CEventTypeInfo, CSceneInfo, CEventInfoList
from RefBooks.Service.Info                  import CServiceInfo
from Events.TempInvalidEditDialog           import CTempInvalidEditDialog, CTempInvalidCreateDialog, getEventListByDates, getTempInvalidIdOpen
from Events.TempInvalidInfo                 import CTempInvalidInfo, CTempInvalidAllInfoList
from Events.Utils import (checkTissueJournalStatusByActions,
                          getActionTypeDescendants,
                          getActionTypeIdListByFlatCode,
                          getEventContext, getEventCounterId,
                          getEventName,
                          getEventPrevEventTypeId,
                          getEventPurposeId,
                          getPayStatusMaskByCode,
                          getPayStatusValueByCode,
                          getPrevEventIdByEventTypeId,
                          getWorkEventTypeFilter,
                          payStatusText,
                          sendTempInvalidDocuments
                          )
from Exchange.ExchangeScanPromobot import scanning
from KLADR.Utils                            import getLikeMaskForRegion
from Notifications.NotificationRule import CNotificationRule
from Notifications.NotifyDialog import CNotifyDialog
from Notifications.NotificationLog import CNotificationLogList
from Orgs.Contracts                         import selectContract
from Orgs.Orgs                              import selectOrganisation
from Orgs.PersonInfo                        import CPersonInfo
from RefBooks.Speciality.Info               import CSpecialityInfo
from Orgs.Utils import getOrganisationShortName, getOrgStructureAddressIdList, getOrgStructureDescendants, \
    getOrgStructures, getOrgStructureFullName, COrgStructureInfo, getOrganisationDescendants, \
    getParentOrgStructureId
from RefBooks.ContingentType.List           import CContingentTypeTranslator
from RefBooks.Finance.Info                  import CFinanceInfo
from RefBooks.TempInvalidState              import CTempInvalidState
from Registry.BatchRegistrationLocationCard import CGetParamsBatchRegistrationLocationCard, CSetParamsBatchRegistrationLocationCard
from Registry.BeforeRecordClient            import printOrderByScheduleItem
from Registry.ClientDocumentTracking        import CClientDocumentTrackingList
from Registry.ClientEditDialog              import CClientEditDialog
from Registry.RelationsClientListDialog     import CRelationsClientListDialog
from Registry.ClientVaccinationCard         import openClientVaccinationCard
from Registry.ComplaintsEditDialog          import CComplaintsEditDialog
from Registry.RegistryTable                 import (CActionsTableModel,
                                                    CMedicalCommissionActionsTableModel,
                                                    CProtocolMCActionsTableModel,
                                                    CMedicalSocialInspectionActionsTableModel,
                                                    CClientsTableModel,
                                                    CEventActionsTableModel,
                                                    CEventDiagnosticsTableModel,
                                                    CEventsTableModel,
                                                    CEventVisitsTableModel,
                                                    CExpertTempInvalidDocumentsTableModel,
                                                    CExpertTempInvalidPeriodsTableModel,
                                                    CExpertTempInvalidTableModel,
                                                    CVisitsTableModel,
                                                    CEventExportFileTableModel
                                                    )
from Registry.ShowScheduleItemInfo          import showScheduleItemInfo
from Registry.SimplifiedClientSearch        import CSimplifiedClientSearch
from Registry.StatusObservationClientEditor import CStatusObservationClientEditor
from Registry.ShowContingentsClientDialog   import CShowContingentsClientDialog
from Registry.UpdateEventTypeByEvent        import CUpdateEventTypeByEvent
from Registry.Utils import (CCheckNetMixin, CClientInfo, CClientInfoListEx, getRightEditTempInvalid, expertiseClass,
                            replaceMask, deleteTempInvalid, formatAddressInt, formatDocument, formatPolicy,
                            getClientBanner, getClientContextData, getClientInfo2, getClientMiniInfo,
                            canChangePayStatusAdditional, canEditOtherpeopleAction, getClientSexAge,
                            addActionTabPresence, getJobTicketsToEvent, preFillingActionRecordMSI,
                            getAttachmentPersonInfo, checkClientAttachService, canAddActionToExposedEvent)
from Registry.VisitsBySchedules             import CVisitsBySchedulesDialog
from Reports.ReportBase import createTable
from Reports.ReportView import CReportViewDialog
from Reports.ReportClientServices           import CReportClientServices
from Reports.ReportView import CPageFormat
from Reports.ReportBase                     import CReportBase
from Reports.Report                         import CReport
from Reports.Utils                          import getStringProperty, updateLIKE, existsPropertyValue
from Resources.GroupJobAppointmentDialog    import CGroupJobAppointmentDialog
from Timeline.Schedule                      import CSchedule, confirmAndFreeScheduleItem
from FastSearchDialog import CFastSearchDialog
from Users.Rights import (urAdmin,
                          urRegTabEditExpertMC,
                          urCanOpenAnyAttachedFile,
                          urCanOpenOwnAttachedFile,
                          urBatchRegLocatCardProcess,
                          urCanEditClientVaccination,
                          urCanReadClientVaccination,
    #                                                    urEditAfterInvoicingEvent,
    #                                                    urEditClosedEvent,
                          urRegTabReadLocationCard,
                          urEditLocationCard,
                          urEditStatusObservationClient,
                          urRegControlDoubles,
    #                                                    urRegDeleteTempInvalid,
                          urRegTabReadActions,
                          urRegTabReadAmbCard,
                          urRegTabReadEvents,
                          urRegTabReadExpert,
                          urRegTabReadRegistry,
                          urRegTabReadVisits,
                          urRegTabWriteActions,
                          urRegTabWriteEvents,
    #                                                    urRegTabWriteExpert,
                          urRegTabWriteRegistry,
                          urRegTabWriteVisits,
                          urUpdateEventTypeByEvent,
                          urSendInternalNotifications,
                          urRegTabNewWriteRegistry, urRegEditClientVisibleTabResearch,
                          urCreateExpertConcurrentlyOnCloseVUT, urRegVisibleExecOwnActionsOrgStructureOnly,
                          urRegVisibleExecOwnActionsOnly, urRegVisibleExecOwnActionsParentOrgStructureOnly,
                          urRegVisibleOwnEventsOrgStructureOnly, urRegVisibleOwnEventsOnly,
                          urRegVisibleSetOwnActionsParentOrgStructureOnly, urRegVisibleSetOwnActionsOrgStructureOnly,
                          urRegVisibleOwnEventsParentOrgStructureOnly, urRegVisibleSetOwnActionsOnly,
                          urRegVisibleOwnAreaActionsOnly, urRegVisibleOwnAreaEventsOnly,
    #                                                    urEditOtherpeopleAction,
                          )
from Registry.Ui_Registry                   import Ui_RegistryWindow
from Registry.RegistryExpertPrintDialog     import CRegistryExpertPrintDialog
from Events.CheckActionPropertiesTableModel  import CCheckActionPropertiesTableModel


class CRegistryWindow(QtGui.QScrollArea, Ui_RegistryWindow, CDialogPreferencesMixin, CCheckNetMixin, CConstructHelperMixin, CRecordLockMixin):
    u"""
        Окно для просмотра списка пациентов,
        обеспечивает возможность фильтрации, сортировки, редактирования
        описания пациента, перехода к связанным с данным пациентом event-ов
        и создания новых event-ов
    """
    def __init__(self, parent):
        QtGui.QScrollArea.__init__(self, parent)
        CCheckNetMixin.__init__(self)
        CRecordLockMixin.__init__(self)

        self.updateClientsListRequest = False
        self.setObjectName('RegistryWindow')
        self.internal = QtGui.QWidget(self)
        self.setWidget(self.internal)

        self.addModels('Clients', CClientsTableModel(self))
        self.addModels('Schedules', CSchedulesModel(self))
        self.addModels('VisitsBySchedules', CVisitsBySchedulesModel(self))
        self.addModels('CanceledSchedules', CCanceledSchedulesModel(self))
        self.addModels('Events', CEventsTableModel(self, self.modelClients.recordCache()))
        self.addModels('EventDiagnostics', CEventDiagnosticsTableModel(self))
        self.addModels('EventActions', CEventActionsTableModel(self))
        self.addModels('EventVisits', CEventVisitsTableModel(self))
        self.addModels('EventExportFile', CEventExportFileTableModel(self))
        self.addModels('ActionsStatus', CActionsTableModel(self, self.modelClients.recordCache(), self.modelEvents.recordCache()))
        self.addModels('ActionsStatusProperties', CActionPropertiesTableModel(self))
        self.addModels('ActionsStatusAttachedDocuments', CAttachedFilesModel(self))
        self.addModels('ListOptionActionProperty', CCheckActionPropertiesTableModel(self))
        self.addModels('ActionsDiagnostic', CActionsTableModel(self, self.modelClients.recordCache(), self.modelEvents.recordCache()))
        self.addModels('ActionsDiagnosticProperties', CActionPropertiesTableModel(self))
        self.addModels('ActionsDiagnosticAttachedDocuments', CAttachedFilesModel(self))
        self.addModels('ActionsCure', CActionsTableModel(self, self.modelClients.recordCache(), self.modelEvents.recordCache()))
        self.addModels('ActionsCureProperties', CActionPropertiesTableModel(self))
        self.addModels('ActionsCureAttachedDocuments', CAttachedFilesModel(self))
        self.addModels('ActionsMisc', CActionsTableModel(self, self.modelClients.recordCache(), self.modelEvents.recordCache()))
        self.addModels('ActionsMiscProperties', CActionPropertiesTableModel(self))
        self.addModels('ActionsMiscAttachedDocuments', CAttachedFilesModel(self))
        self.addModels('ActionsAll', CActionsTableModel(self, self.modelClients.recordCache(), self.modelEvents.recordCache()))
        self.addModels('ActionsAllProperties', CActionPropertiesTableModel(self))
        self.addModels('ActionsAllAttachedDocuments', CAttachedFilesModel(self))
        self.addModels('ExpertTempInvalid', CExpertTempInvalidTableModel(self, self.modelClients.recordCache()))
        self.addModels('ExpertTempInvalidRelation', CExpertTempInvalidTableModel(self, self.modelClients.recordCache()))
        self.addModels('ExpertTempInvalidPeriods',    CExpertTempInvalidPeriodsTableModel(self))
        self.addModels('ExpertTempInvalidDocuments', CExpertTempInvalidDocumentsTableModel(self))
        self.addModels('ExpertTempInvalidDocumentsRelation', CExpertTempInvalidDocumentsTableModel(self))
        self.addModels('ExpertTempInvalidDocumentsEx', CExpertTempInvalidDocumentsTableModel(self))
        self.addModels('ExpertTempInvalidRelationDocumentsEx', CExpertTempInvalidDocumentsTableModel(self))
        self.addModels('ExpertTempInvalidPeriodsDocuments',    CExpertTempInvalidPeriodsTableModel(self))
        self.addModels('ExpertDisability', CExpertTempInvalidTableModel(self, self.modelClients.recordCache()))
        self.addModels('ExpertDisabilityRelation', CExpertTempInvalidTableModel(self, self.modelClients.recordCache()))
        self.addModels('ExpertDisabilityPeriods', CExpertTempInvalidPeriodsTableModel(self))
        self.addModels('ExpertDisabilityDocuments', CExpertTempInvalidDocumentsTableModel(self))
        self.addModels('ExpertDisabilityDocumentsRelation', CExpertTempInvalidDocumentsTableModel(self))
        self.addModels('ExpertDisabilityDocumentsEx', CExpertTempInvalidDocumentsTableModel(self))
        self.addModels('ExpertDisabilityRelationDocumentsEx', CExpertTempInvalidDocumentsTableModel(self))
        self.addModels('ExpertDisabilityPeriodsDocuments',    CExpertTempInvalidPeriodsTableModel(self))
        self.addModels('ExpertVitalRestriction', CExpertTempInvalidTableModel(self, self.modelClients.recordCache()))
        self.addModels('ExpertVitalRestrictionRelation', CExpertTempInvalidTableModel(self, self.modelClients.recordCache()))
        self.addModels('ExpertVitalRestrictionPeriods', CExpertTempInvalidPeriodsTableModel(self))
        self.addModels('ExpertVitalRestrictionDocuments', CExpertTempInvalidDocumentsTableModel(self))
        self.addModels('ExpertVitalRestrictionDocumentsRelation', CExpertTempInvalidDocumentsTableModel(self))
        self.addModels('ExpertVitalRestrictionDocumentsEx', CExpertTempInvalidDocumentsTableModel(self))
        self.addModels('ExpertVitalRestrictionRelationDocumentsEx', CExpertTempInvalidDocumentsTableModel(self))
        self.addModels('ExpertVitalRestrictionPeriodsDocuments',    CExpertTempInvalidPeriodsTableModel(self))
        self.addModels('ExpertDirectionsMC', CMedicalCommissionActionsTableModel(self, self.modelClients.recordCache(), self.modelEvents.recordCache()))
        self.addModels('ExpertProtocolsMC', CProtocolMCActionsTableModel(self, self.modelClients.recordCache(), self.modelEvents.recordCache()))
        self.addModels('ExpertMedicalSocialInspection', CMedicalSocialInspectionActionsTableModel(self, self.modelClients.recordCache(), self.modelEvents.recordCache()))
        self.addModels('ExpertDirectionsPropertiesMC', CActionPropertiesTableModel(self))
        self.addModels('ExpertProtocolsPropertiesMC', CActionPropertiesTableModel(self))
        self.addModels('ExpertMSIProperties', CActionPropertiesTableModel(self))
        self.addModels('FilterInfection', CRBCheckTableModel(self, 'rbInfection', u'Инфекции'))
        self.addModels('FilterVaccine', CRBCheckTableModel(self, 'rbVaccine', u'Вакцины'))
        self.addModels('Visits', CVisitsTableModel(self, self.modelClients.recordCache(), self.modelEvents.recordCache()))
        self.addModels('ExternalNotification',    CExternalNotificationModel(self))
        self.addObject('actEditClient', QtGui.QAction(u'Открыть регистрационную карточку', self))
        self.addObject('actRelationsClient', QtGui.QAction(u'Показать список связанных пациентов', self))
        self.addObject('actEventRelationsClient', QtGui.QAction(u'Показать список связанных пациентов', self))
        self.addObject('actAmbCardRelationsClient', QtGui.QAction(u'Показать список связанных пациентов', self))
        self.addObject('actActionsRelationsClient', QtGui.QAction(u'Показать список связанных пациентов', self))
        self.addObject('actExpertRelationsClient', QtGui.QAction(u'Показать список связанных пациентов', self))
        self.addObject('actVisitRelationsClient', QtGui.QAction(u'Показать список связанных пациентов', self))
        self.addObject('actOpenClientDocumentTrackingHistory', QtGui.QAction(u'Открыть журнал хранения учетных документов', self))
        self.addObject('actEditStatusObservationClient', QtGui.QAction(u'Изменить статус наблюдения пациента', self))
        self.addObject('actSurveillancePlanningClients', QtGui.QAction(u'Контрольная карта диспансерного наблюдения', self))
        self.actEditStatusObservationClient.setShortcut('Shift+F5')
        self.addObject('actUpdateF111', QtGui.QAction(u'Открыть карту беременной и родильницы', self))
        self.addObject('actShowContingentsClient', QtGui.QAction(u'Показать все наблюдаемые контингенты', self))
        self.addObject('actCheckClientAttach', QtGui.QAction(u'Проверить прикрепление', self))
        self.addObject('actPortal_Doctor', QtGui.QAction(u'Перейти на портал врача', self))
        self.addObject('actPrintClient', getPrintAction(self, 'token', u'Напечатать талон'))
        self.addObject('actPrintClientPs', getPrintAction(self, 'ps', u'Напечатать ответ'))
        self.addObject('actPrintClientLabel', QtGui.QAction(u'Напечатать визитку пациента', self))
        self.actPrintClientLabel.setShortcut('Shift+F6')
        self.clientLabelTemplate = getFirstPrintTemplate('clientLabel')
        self.addObject('actPrintClientList',   QtGui.QAction(u'Напечатать список пациентов', self))
        self.addObject('actEventPrint',  CPrintAction(u'Напечатать список обращений', None, self, self))
        self.addObject('actReportClientServices',  QtGui.QAction(u'Напечатать сводку об услугах на пациента', self))
        self.addObject('actEventEditClient',   QtGui.QAction(u'Открыть регистрационную карточку', self))
        self.addObject('actAmbCardEditClient', QtGui.QAction(u'Открыть регистрационную карточку', self))
        self.addObject('actActionEditClient',  QtGui.QAction(u'Открыть регистрационную карточку', self))
        self.addObject('actEventOpenClientVaccinationCard',   QtGui.QAction(u'Открыть прививочную карту', self))
        self.addObject('actAmbCardOpenClientVaccinationCard', QtGui.QAction(u'Открыть прививочную карту', self))
        self.addObject('actActionOpenClientVaccinationCard',  QtGui.QAction(u'Открыть прививочную карту', self))
        self.addObject('actCreateRelatedAction', QtGui.QAction(u'Создать связанное действие', self))
        self.addObject('actEditActionEvent',  QtGui.QAction(u'Редактировать обращение', self))
        self.addObject('actAddActionEvent',  QtGui.QAction(u'Добавить действие', self))
        self.actAddActionEvent.setShortcut('Shift+F8')
        self.addObject('actJobTicketsEvent',  QtGui.QAction(u'Работы', self))
        self.addObject('actEditVisitEvent',  QtGui.QAction(u'Редактировать обращение', self))
        self.addObject('actEditExpertMCEvent', QtGui.QAction(u'Редактировать обращение', self))
        self.addObject('actExpertPrint',  CPrintAction(u'Напечатать список документов ВУТ', None, self, self))
        self.addObject('actExpertEditClient',  QtGui.QAction(u'Открыть регистрационную карточку', self))
        self.addObject('actExpertTempInvalidChangeToOpen', QtGui.QAction(u'Изменить состояние продленного эпизода', self))
        self.addObject('actExpertTempInvalidNext',       QtGui.QAction(u'Следующий эпизод', self))
        self.addObject('actExpertTempInvalidPrev',       QtGui.QAction(u'Предыдущий эпизод', self))
        self.addObject('actExpertTempInvalidDelete',     QtGui.QAction(u'Удалить эпизод', self))
        self.addObject('actExpertDisabilityNext',        QtGui.QAction(u'Следующий эпизод', self))
        self.addObject('actExpertDisabilityPrev',        QtGui.QAction(u'Предыдущий эпизод', self))
        self.addObject('actExpertDisabilityDelete',      QtGui.QAction(u'Удалить эпизод', self))
        self.addObject('actExpertVitalRestrictionNext',  QtGui.QAction(u'Следующий эпизод', self))
        self.addObject('actExpertVitalRestrictionPrev',  QtGui.QAction(u'Предыдущий эпизод', self))
        self.addObject('actExpertVitalRestrictionDelete',QtGui.QAction(u'Удалить эпизод', self))
        self.addObject('actExpertMedicalCommissionSelected', QtGui.QAction(u'Выделить группу', self))
        self.addObject('actExpertMedicalCommissionUpdateGroup', QtGui.QAction(u'Редактировать группу', self))
        self.addObject('actExpertMedicalCommissionClear',    QtGui.QAction(u'Снять выделение', self))
        self.addObject('actExpertMedicalCommissionDelete', QtGui.QAction(u'Удалить', self))
        self.addObject('actExpertMedicalCommissionUpdate', QtGui.QAction(u'Редактировать', self))
        self.addObject('actExpertMedicalCommissionMSI',    QtGui.QAction(u'Направить на МСЭ', self))
        self.addObject('actExpertMCUpdateTempInvalid',     QtGui.QAction(u'Редактор ВУТ', self))
        self.addObject('actListVisitsBySchedules',       QtGui.QAction(u'Протокол обращений пациента по предварительной записи', self))
        self.addObject('actaddClients', QtGui.QAction(u'Отметить пациента', self))
        self.actaddClients.setShortcut('F2')
        self.addObject('actaClients', QtGui.QAction(u'Вывести список пациентов', self))
        self.actaClients.setShortcut('F3')
        self.addObject('actBatchRegLocatCard',           QtGui.QAction(u'Изменить место нахождения карты пациентов', self))
        self.actBatchRegLocatCard.setShortcut('F5')
        self.addObject('actSurveillancePlanningClientsByEvent', QtGui.QAction(u'Контрольная карта диспансерного наблюдения', self))
        self.addObject('actStatusObservationClient',     QtGui.QAction(u'Изменить статус наблюдения пациента', self))
        self.actStatusObservationClient.setShortcut('Shift+F5')
        self.addObject('actStatusObservationClientBrowserByEvent', QtGui.QAction(u'Изменить статус наблюдения пациента', self))
        self.actStatusObservationClientBrowserByEvent.setShortcut('Shift+F5')
        self.addObject('actStatusObservationClientByEvent', QtGui.QAction(u'Изменить статус наблюдения пациента', self))
        self.actStatusObservationClientByEvent.setShortcut('Shift+F5')
        self.addObject('actJumpToRegistry',              QtGui.QAction(u'Перейти в картотеку', self))
        self.addObject('actControlDoublesRecordClient',  QtGui.QAction(u'Логический контроль двойников', self))
        self.addObject('actControlDoublesRecordClientList',  QtGui.QAction(u'Логический контроль двойников по списку', self))
        self.addObject('actReservedOrderQueueClient',    QtGui.QAction(u'Использовать бронь в очереди', self))
        self.addObject('actOpenClientVaccinationCard',   QtGui.QAction(u'Открыть прививочную карту', self))
        self.addObject('actAmbCreateEvent',              QtGui.QAction(u'Новое обращение', self))
        self.addObject('actAmbDeleteOrder',              QtGui.QAction(u'Удалить из очереди', self))
        self.addObject('actAmbChangeNotes',              QtGui.QAction(u'Изменить жалобы', self))
        self.addObject('actAmbPrintOrder', getPrintAction(self, 'orderAmb', u'Напечатать направление', False))   #QtGui.QAction(u'Напечатать направление', self))
        self.addObject('actAmbHomePrintOrder', getPrintAction(self, 'orderHome', u'Напечатать направление (вызов на дом)', False))
        self.addObject('actJumpQueuePosition',  QtGui.QAction(u'Перейти в график', self))
        self.addObject('actPrintBeforeRecords',  QtGui.QAction(u'Печать предварительной записи', self))
        self.addObject('actShowPreRecordInfo', QtGui.QAction(u'Свойства записи', self))
        self.addObject('actShowPreRecordInfoVisitBySchedule', QtGui.QAction(u'Свойства записи', self))
        self.addObject('actShowPreRecordInfoCanceledSchedules', QtGui.QAction(u'Свойства записи', self))
        self.addObject('actOpenAccountingByEvent',  QtGui.QAction(u'Перейти к счетам', self))
        self.addObject('actGroupJobAppointment', QtGui.QAction(u'Групповое назначение', self))
        self.addObject('actUpdateEventTypeByEvent',  QtGui.QAction(u'Изменить тип события', self))
        self.addObject('actUndoExpertise', QtGui.QAction(u'Отменить экспертизу', self))
        self.addObject('actOpenAccountingByAction', QtGui.QAction(u'Перейти к счетам', self))
        self.addObject('actOpenAccountingBySingleAction', QtGui.QAction(u'Перейти к счетам', self))
        self.addObject('actOpenAccountingBySingleVisits', QtGui.QAction(u'Перейти к счетам', self))
        self.addObject('actOpenAccountingByVisit',  QtGui.QAction(u'Перейти к счетам', self))
        self.addObject('actConcatEvents',  QtGui.QAction(u'Объединить события', self))
        self.addObject('actMakePersonalAccount',  QtGui.QAction(u'Сформировать индивидуальный счет', self))
        self.addObject('actShowPacsImages',  QtGui.QAction(u'Показать все снимки', self))
        self.addObject('actNotify',  QtGui.QAction(u'Оповещение', self))
        self.addObject('actNotifyFromTabActions', QtGui.QAction(u'Оповещение', self))
        self.addObject('actNotificationLog', QtGui.QAction(u'Журнал оповещений пациента', self))
        self.addObject('actActionGroupSign', QtGui.QAction(u'Групповое подписание и прикрепление', self))
        self.addObject('mnuPrint', QtGui.QMenu(self))
        self.addObject('actSendEventFPUMP', QtGui.QAction(u'Выгрузить событие в "ГИС ОМС ФПУМП"', self))
        self.mnuPrint.addAction(self.actPrintClient)
        self.mnuPrint.addAction(self.actPrintClientPs)
        self.mnuPrint.addAction(self.actPrintClientLabel)
        self.mnuPrint.addAction(self.actPrintClientList)
        self.addBarcodeScanAction('actClientIdBarcodeScan')
        self.addObject('actSimplifiedClientSearch', QtGui.QAction(u'Упрощеный поиск пациента', self))
        self.actSimplifiedClientSearch.setShortcuts([QtGui.QKeySequence.Find,
                                                     'Alt+F7',
    #                                                     QtGui.QKeySequence(Qt.ALT+Qt.Key_F7),
                                                    ]
                                                   )
        self.addObject('actcacheTemplate', QtGui.QAction(u'Открыть последний сформированный шаблон печати', self))
        self.actcacheTemplate.setShortcuts(['Ctrl+H'])
        self.addObject('actCreateEvent', QtGui.QAction(u'Новое обращение', self))
        self.actCreateEvent.setShortcutContext(Qt.WidgetShortcut)
        self.actCreateEvent.setShortcut(Qt.Key_Space)
        self.addBarcodeScanAction('actEventIdBarcodeScan')
        self.addBarcodeScanAction('actEventJobTicketIdBarcodeScan')
        self.addBarcodeScanAction('actEventExternalIdBarcodeScan')

        self.clientsSortingCol = 0
        self.clientsSortingDest = 'ASC'

        self.setupUi(self.internal)
        self.tabMain.saveTabInfo()

        self.setWindowTitle(self.internal.windowTitle())
        self.setWidgetResizable(True)
        self.btnPrint.setMenu(self.mnuPrint)
        self.btnPrint.setShortcut('Alt+F6')
        # self.btnEventPrint_actions = [{'action': self.actEventPrint, 'slot': self.on_actEventPrint_triggered},
        #                               {'action': self.actReportClientServices, 'slot': self.on_actReportClientServices_triggered} ]
        eventTemplates = getPrintTemplates(getEventContextTemplate())
        self.addObject('mnuPrintEvent', QtGui.QMenu(self))
        self.mnuPrintEvent.addAction(self.actEventPrint)
        self.mnuPrintEvent.addAction(self.actReportClientServices)
        self.btnEventPrint.setMenu(self.mnuPrintEvent)
        self.btnEventPrint.menu().addSeparator()
        if eventTemplates:
            subMenuDict = {}
            for i, template in enumerate(eventTemplates):
                if not template.group:
                    action = CPrintAction(template.name, template.id, self.btnEventPrint, self.btnEventPrint)
                    self.btnEventPrint.addAction(action)
                else:
                    subMenu = subMenuDict.get(template.group)
                    if subMenu is None:
                        subMenu = QtGui.QMenu(template.group, self.parentWidget())
                        subMenuDict[template.group] = subMenu
                    action = CPrintAction(template.name, template.id, self.btnEventPrint, self.btnEventPrint)
                    subMenu.addAction(action)
            if subMenuDict:
                for subMenuKey in sorted(subMenuDict.keys()):
                    self.btnEventPrint.menu().addMenu(subMenuDict[subMenuKey])
            self.btnEventPrint.menu().addSeparator()
        visitTemplates = getPrintTemplates(getVisitContext())
        if not visitTemplates:
            self.btnVisitPrint.setId(-1)
        else:
            subMenuDict={}
            for i, template in enumerate(visitTemplates):
                if not template.group:
                    action = CPrintAction(template.name, template.id, self.btnVisitPrint, self.btnVisitPrint)
                    self.btnVisitPrint.addAction(action)
                else:
                    subMenu = subMenuDict.get(template.group)
                    if subMenu is None:
                        subMenu = QtGui.QMenu(template.group, self.parentWidget())
                        subMenuDict[template.group] = subMenu
                    action = CPrintAction(template.name, template.id, self.btnVisitPrint, self.btnVisitPrint)
                    subMenu.addAction(action)
            if subMenuDict:
                for subMenuKey in sorted(subMenuDict.keys()):
                    self.btnVisitPrint.menu().addMenu(subMenuDict[subMenuKey])
            self.btnVisitPrint.menu().addSeparator()
            self.btnVisitPrint.addAction(CPrintAction(u'Напечатать список визитов', -1, self.btnVisitPrint, self.btnVisitPrint))
        self.btnExpertPrint_actions = [{'action': self.actExpertPrint, 'slot': self.on_actExpertPrint_triggered}, ]
        actionTemplates = getPrintTemplates(getActionContext())
        if not actionTemplates:
            self.btnActionPrint.setId(-1)
            addButtonActions(self, self.btnExpertPrint, self.btnExpertPrint_actions)
        else:
            addButtonActions(self, self.btnExpertPrint, self.btnExpertPrint_actions)
            self.btnExpertPrint.menu().addSeparator()
            subMenuDict={}
            for i, template in enumerate(actionTemplates):
                if not template.group:
                    action = CPrintAction(template.name, template.id, self.btnActionPrint, self.btnActionPrint)
                    self.btnActionPrint.addAction(action)
                else:
                    subMenu = subMenuDict.get(template.group)
                    if subMenu is None:
                        subMenu = QtGui.QMenu(template.group, self.parentWidget())
                        subMenuDict[template.group] = subMenu
                    action = CPrintAction(template.name, template.id, self.btnActionPrint, self.btnActionPrint)
                    subMenu.addAction(action)
            if subMenuDict:
                if not self.btnActionPrint.menu():
                    menu = QtGui.QMenu(self)
                    self.btnActionPrint.setMenu(menu)
                for subMenuKey in sorted(subMenuDict.keys()):
                    self.btnActionPrint.menu().addMenu(subMenuDict[subMenuKey])
            self.btnActionPrint.menu().addSeparator()
            self.btnActionPrint.addAction(CPrintAction(u'Напечатать список', -1, self.btnActionPrint, self.btnActionPrint))
        clientTemplates = getPrintTemplates(getClientContext())
        if clientTemplates:
            self.btnPrint.menu().addSeparator()
            subMenuDict = {}
            for i, template in enumerate(clientTemplates):
                if not template.group:
                    action = CPrintAction(template.name, template.id, self.btnPrint, self.btnPrint)
                    self.btnPrint.addAction(action)
                else:
                    subMenu = subMenuDict.get(template.group)
                    if subMenu is None:
                        subMenu = QtGui.QMenu(template.group, self.parentWidget())
                        subMenuDict[template.group] = subMenu
                    action = CPrintAction(template.name, template.id, self.btnPrint, self.btnPrint)
                    subMenu.addAction(action)
            if subMenuDict:
                for subMenuKey in sorted(subMenuDict.keys()):
                    self.btnPrint.menu().addMenu(subMenuDict[subMenuKey])
            self.btnPrint.menu().addSeparator()

        self.setModels(self.tblFilterInfection,  self.modelFilterInfection,  self.selectionModelFilterInfection)
        self.setModels(self.tblFilterVaccine,    self.modelFilterVaccine,    self.selectionModelFilterVaccine)
        self.setModels(self.tblClients, self.modelClients, self.selectionModelClients)
        self.tblClients.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.setModels(self.tblSchedules, self.modelSchedules, self.selectionModelSchedules)
        self.tblSchedules.horizontalHeader().moveSection(9, 2)
        self.setModels(self.tblVisitsBySchedules, self.modelVisitsBySchedules, self.selectionModelVisitsBySchedules)
        self.setModels(self.tblExternalNotification, self.modelExternalNotification, self.selectionModelExternalNotification)
        self.tblVisitsBySchedules.horizontalHeader().moveSection(8, 2)
        self.setModels(self.tblCanceledSchedules, self.modelCanceledSchedules, self.selectionModelCanceledSchedules)
        self.tblCanceledSchedules.horizontalHeader().moveSection(8, 2)
        self.tblCanceledSchedules.setSortingEnabled(True)
#        self.tblExternalNotification.resizeColumnsToContents()
#        self.tblExternalNotification.resizeRowsToContents()
        self.tblExternalNotification.horizontalHeader().setStretchLastSection(True)
        self.setModels(self.tblEvents, self.modelEvents, self.selectionModelEvents)
        self.tblEvents.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tblEventDiagnostics.setModel(self.modelEventDiagnostics)
        self.tblEventActions.setModel(self.modelEventActions)
        self.tblEventVisits.setModel(self.modelEventVisits)
        self.setModels(self.tblEventExportFile, self.modelEventExportFile, self.selectionModelEventExportFile)
        self.tblEventExportFile.setSortingEnabled(True)

        self.setModels(self.tblActionsStatus, self.modelActionsStatus, self.selectionModelActionsStatus)
        self.setModels(self.tblActionsStatusProperties, self.modelActionsStatusProperties, self.selectionModelActionsStatusProperties)
        self.setModels(self.tblActionsStatusAttachedDocuments, self.modelActionsStatusAttachedDocuments, self.selectionModelActionsStatusAttachedDocuments)
        self.setModels(self.tblListOptionActionProperty, self.modelListOptionActionProperty, self.selectionModelListOptionActionProperty)
        self.setModels(self.tblActionsDiagnostic, self.modelActionsDiagnostic, self.selectionModelActionsDiagnostic)
        self.setModels(self.tblActionsDiagnosticProperties, self.modelActionsDiagnosticProperties, self.selectionModelActionsDiagnosticProperties)
        self.setModels(self.tblActionsDiagnosticAttachedDocuments, self.modelActionsDiagnosticAttachedDocuments, self.selectionModelActionsDiagnosticAttachedDocuments)
        self.setModels(self.tblActionsCure, self.modelActionsCure, self.selectionModelActionsCure)
        self.setModels(self.tblActionsCureProperties, self.modelActionsCureProperties, self.selectionModelActionsCureProperties)
        self.setModels(self.tblActionsCureAttachedDocuments, self.modelActionsCureAttachedDocuments, self.selectionModelActionsCureAttachedDocuments)
        self.setModels(self.tblActionsMisc, self.modelActionsMisc, self.selectionModelActionsMisc)
        self.setModels(self.tblActionsMiscProperties, self.modelActionsMiscProperties, self.selectionModelActionsMiscProperties)
        self.setModels(self.tblActionsMiscAttachedDocuments, self.modelActionsMiscAttachedDocuments, self.selectionModelActionsMiscAttachedDocuments)
        self.setModels(self.tblActionsAll, self.modelActionsAll, self.selectionModelActionsAll)
        self.setModels(self.tblActionsAllProperties, self.modelActionsAllProperties, self.selectionModelActionsAllProperties)
        self.setModels(self.tblActionsAllAttachedDocuments, self.modelActionsAllAttachedDocuments, self.selectionModelActionsAllAttachedDocuments)
        self.setModels(self.tblExpertTempInvalid, self.modelExpertTempInvalid, self.selectionModelExpertTempInvalid)
        self.setModels(self.tblExpertTempInvalidRelation, self.modelExpertTempInvalidRelation, self.selectionModelExpertTempInvalidRelation)
        self.setModels(self.tblExpertTempInvalidPeriods, self.modelExpertTempInvalidPeriods, self.selectionModelExpertTempInvalidPeriods)
        self.setModels(self.tblExpertTempInvalidDocuments, self.modelExpertTempInvalidDocuments, self.selectionModelExpertTempInvalidDocuments)
        self.setModels(self.tblExpertTempInvalidDocumentsEx, self.modelExpertTempInvalidDocumentsEx, self.selectionModelExpertTempInvalidDocumentsEx)
        self.setModels(self.tblExpertTempInvalidRelationDocumentsEx, self.modelExpertTempInvalidRelationDocumentsEx, self.selectionModelExpertTempInvalidRelationDocumentsEx)
        self.setModels(self.tblExpertTempInvalidPeriodsDocuments, self.modelExpertTempInvalidPeriodsDocuments, self.selectionModelExpertTempInvalidPeriodsDocuments)
        self.setModels(self.tblExpertDisability, self.modelExpertDisability, self.selectionModelExpertDisability)
        self.setModels(self.tblExpertDisabilityRelation, self.modelExpertDisabilityRelation, self.selectionModelExpertDisabilityRelation)
        self.setModels(self.tblExpertDisabilityPeriods, self.modelExpertDisabilityPeriods, self.selectionModelExpertDisabilityPeriods)
        self.setModels(self.tblExpertDisabilityDocuments, self.modelExpertDisabilityDocuments, self.selectionModelExpertDisabilityDocuments)
        self.setModels(self.tblExpertDisabilityDocumentsEx, self.modelExpertDisabilityDocumentsEx, self.selectionModelExpertDisabilityDocumentsEx)
        self.setModels(self.tblExpertDisabilityRelationDocumentsEx, self.modelExpertDisabilityRelationDocumentsEx, self.selectionModelExpertDisabilityRelationDocumentsEx)
        self.setModels(self.tblExpertDisabilityPeriodsDocuments, self.modelExpertDisabilityPeriodsDocuments, self.selectionModelExpertDisabilityPeriodsDocuments)
        self.setModels(self.tblExpertVitalRestriction, self.modelExpertVitalRestriction, self.selectionModelExpertVitalRestriction)
        self.setModels(self.tblExpertVitalRestrictionRelation, self.modelExpertVitalRestrictionRelation, self.selectionModelExpertVitalRestrictionRelation)
        self.setModels(self.tblExpertVitalRestrictionPeriods, self.modelExpertVitalRestrictionPeriods, self.selectionModelExpertVitalRestrictionPeriods)
        self.setModels(self.tblExpertVitalRestrictionDocuments, self.modelExpertVitalRestrictionDocuments, self.selectionModelExpertVitalRestrictionDocuments)
        self.setModels(self.tblExpertVitalRestrictionDocumentsEx, self.modelExpertVitalRestrictionDocumentsEx, self.selectionModelExpertVitalRestrictionDocumentsEx)
        self.setModels(self.tblExpertVitalRestrictionRelationDocumentsEx, self.modelExpertVitalRestrictionRelationDocumentsEx, self.selectionModelExpertVitalRestrictionRelationDocumentsEx)
        self.setModels(self.tblExpertVitalRestrictionPeriodsDocuments, self.modelExpertVitalRestrictionPeriodsDocuments,     self.selectionModelExpertVitalRestrictionPeriodsDocuments)
        self.setModels(self.tblExpertDirectionsMC, self.modelExpertDirectionsMC, self.selectionModelExpertDirectionsMC)
        self.setModels(self.tblExpertProtocolsMC, self.modelExpertProtocolsMC, self.selectionModelExpertProtocolsMC)
        self.setModels(self.tblExpertMedicalSocialInspection, self.modelExpertMedicalSocialInspection, self.selectionModelExpertMedicalSocialInspection)
        self.setModels(self.tblExpertDirectionsPropertiesMC, self.modelExpertDirectionsPropertiesMC, self.selectionModelExpertDirectionsPropertiesMC)
        self.setModels(self.tblExpertProtocolsPropertiesMC, self.modelExpertProtocolsPropertiesMC, self.selectionModelExpertProtocolsPropertiesMC)
        self.setModels(self.tblExpertMSIProperties, self.modelExpertMSIProperties, self.selectionModelExpertMSIProperties)
        self.setModels(self.tblVisits, self.modelVisits, self.selectionModelVisits)
        self.setModels(self.tblExternalNotification, self.modelExternalNotification, None)
        # self.cmbFilterDocumentType.setTable('rbDocumentType', True, 'group_id IN (SELECT id FROM rbDocumentTypeGroup WHERE code=\'1\')')
        self.edtFilterPolicyActualData.setDate(QDate.currentDate())
        # self.cmbFilterPolicyType.setTable('rbPolicyType', True, specialValues=((-1, u'ОМС', u'ОМС'), ))
        # self.cmbFilterPolicyKind.setTable('rbPolicyKind', True)
        self.cmbFilterAttachType.setTable('rbAttachType', True)
        # self.cmbFilterVisitScene.setTable('rbScene', True)
        # self.cmbFilterVisitType.setTable('rbVisitType', True)
        self.cmbFilterVisitProfile.setTable('rbService', True)
        self.cmbFilterServiceVisit.setTable('rbService', True)
        # self.cmbFilterSceneVisit.setTable('rbScene', True)
        # self.edtFilterEventFinance.setTable('rbFinance', True)
        # self.cmbFilterDocumentTypeForTracking.setTable('rbDocumentTypeForTracking', True)
        # self.edtFilterDocumentTypeForTrackingNumber.setValidator(QtGui.QIntValidator())
        # self.cmbFilterDocumentLocation.setTable('rbDocumentTypeLocation', True)
        # self.cmbFilterStatusObservationType.setTable('rbStatusObservationClientType', True)
        # self.cmbFilterVaccinationCalendar.setTable('rbVaccinationCalendar', addNone=True)
        # self.cmbFilterMedicalExemptionType.setTable('rbMedicalExemptionType', addNone=True)
        # self.cmbFilterClientConsentType.setTable('rbClientConsentType', addNone=True)
        # self.cmbFilterContingentType.setTable('rbContingentType', addNone=True)
        # self.cmbFilterContingentSpeciality.setTable('rbSpeciality', True)
        self.edtFilterClientConsentBegDate.setDate(QDate())
        self.edtFilterClientConsentEndDate.setDate(QDate())
        self.edtFilterClientConsentDate1.setDate(QDate())
        self.edtFilterClientConsentDate2.setDate(QDate())
        self.edtExternalNotificationBegDate.setDate(QDate.currentDate().addDays(-7))
        self.edtExternalNotificationEndDate.setDate(QDate.currentDate())
        self.edtExternalNotificationEndDate.setTime(QTime(23, 59, 59))
        # self.cmbFilterClientResearchKind.setTable('rbClientResearchKind', addNone=True)
        self.cmbFilterEventDispanser.setTable('rbDispanser', True)
        self.edtFilterClientResearchBegDate.setDate(QDate())
        self.edtFilterClientResearchEndDate.setDate(QDate())
        self.chkFilterClientResearch.setEnabled(QtGui.qApp.userHasRight(urRegEditClientVisibleTabResearch))


        self.idValidator = CIdValidator(self)
        self.edtFilterId.setValidator(self.idValidator)
        self.edtFilterBirthDay.setHighlightRedDate(False)
        self.cmbFilterAddressStreet.setAddNone(True)
        self.edtFilterSocStatusesBegDate.setDate(QDate())
        self.edtFilterSocStatusesEndDate.setDate(QDate())
        self.cmbFilterCreatePerson.setSpecialityPresent(False)
        self.cmbFilterModifyPerson.setSpecialityPresent(False)

        self.chkListOnClientsPage = [
            (self.chkFilterId,                    [self.edtFilterId,  self.cmbFilterAccountingSystem]),
            (self.chkFilterLastName,              [self.edtFilterLastName, self.chkFilterOldLastName]),
            (self.chkFilterOldLastName, [self.edtFilterLastName]),
            (self.chkFilterFirstName,             [self.edtFilterFirstName, self.chkFilterOldFirstName]),
            (self.chkFilterOldFirstName, [self.edtFilterFirstName]),
            (self.chkFilterPatrName,              [self.edtFilterPatrName, self.chkFilterOldPatrName]),
            (self.chkFilterOldPatrName, [self.edtFilterPatrName]),
            (self.chkFilterBirthDay,              [self.edtFilterBirthDay, self.chkFilterEndBirthDay]),
            (self.chkFilterEndBirthDay,           [self.edtFilterEndBirthDay]),
            (self.chkFilterSex,                   [self.cmbFilterSex]),
            (self.chkFilterContact,               [self.edtFilterContact]),
            (self.chkFilterSNILS,                 [self.edtFilterSNILS]),
            (self.chkFilterDocument,              [self.cmbFilterDocumentType,  self.edtFilterDocumentSerial,
                                                   self.edtFilterDocumentNumber]),
            (self.chkFilterPolicy,                [self.chkFilterPolicyOnlyActual, self.edtFilterPolicyActualData,
                                                   self.cmbFilterPolicyType, self.cmbFilterPolicyKind, self.cmbFilterPolicyInsurer,
                                                   self.edtFilterPolicySerial, self.edtFilterPolicyNumber, self.chkInsurerDescendents]),

            (self.chkFilterRegionSMO,             [self.cmbFilterRegionTypeSMO, self.cmbFilterRegionSMO]),
            (self.chkFilterPolicyOnlyActual,      [self.edtFilterPolicyActualData]),
            (self.chkFilterWorkOrganisation,      [self.cmbWorkOrganisation, self.btnSelectWorkOrganisation]),
            (self.chkSocStatuses,                 [self.chkSocStatusesCondition, self.lblFilterSocStatusesBegDate, self.lblFilterSocStatusesBegDate_2, self.edtFilterSocStatusesBegDate, self.edtFilterSocStatusesEndDate, self.cmbSocStatusesClass, self.cmbSocStatusesType]),
            (self.chkFilterDocumentLocation,      [self.lblBegDateFilterDocumentLocation, self.lblEndDateFilterDocumentLocation, self.cmbFilterDocumentLocation, self.edtBegDateFilterDocumentLocation, self.edtEndDateFilterDocumentLocation, self.cmbPersonDocumentLocation]),
            (self.chkFilterDocumentTypeForTracking,      [self.cmbFilterDocumentTypeForTracking]),
            (self.chkFilterDocumentTypeForTrackingNumber, [self.edtFilterDocumentTypeForTrackingNumber]),
            (self.chkFilterStatusObservationType, [self.cmbFilterStatusObservationType]),
            (self.chkFilterContingentType,        [self.cmbFilterContingentType, self.cmbFilterContingentEventTypeStatus, self.chkFilterContingentMKB,
                                                   self.cmbFilterContingentActionType, self.lblEventName, self.lblActionName,self.chkFilterContingentSpeciality ]),
            (self.chkFilterContingentSpeciality,  [self.cmbFilterContingentSpeciality]),
            (self.chkFilterContingentMKB,         [self.edtContingentMKBTo, self.edtContingentMKBFrom]),
            (self.chkFilterCreatePerson,          [self.cmbFilterCreatePerson]),
            (self.chkFilterCreateDate,            [self.edtFilterBegCreateDate, self.edtFilterEndCreateDate]),
            (self.chkFilterModifyPerson,          [self.cmbFilterModifyPerson]),
            (self.chkFilterModifyDate,            [self.edtFilterBegModifyDate, self.edtFilterEndModifyDate]),
            (self.chkFilterEvent,                 [self.chkFilterFirstEvent, self.edtFilterEventBegDate,
                                                   self.edtFilterEventEndDate]),
            (self.chkFilterEventOpen,             [self.edtFilterEventBegDate,
                                                   self.edtFilterEventEndDate]),
            (self.chkFilterAge,                   [self.edtFilterBegAge, self.cmbFilterBegAge,
                                                   self.edtFilterEndAge, self.cmbFilterEndAge, self.lblAge]),
            (self.chkFilterAddress,               [self.cmbFilterAddressType,
                                                   self.cmbFilterAddressRelation,
                                                   self.cmbFilterAddressCity,
                                                   self.cmbFilterAddressOkato,
                                                   self.cmbFilterAddressStreet,
                                                   self.lblFilterAddressHouse, self.edtFilterAddressHouse,
                                                   self.chkFilterAddressCorpus, self.edtFilterAddressCorpus,
                                                   self.lblFilterAddressFlat, self.edtFilterAddressFlat]),
            (self.chkResident,                    [self.cmbResident]),
            (self.chkFilterAddressCorpus,         [self.edtFilterAddressCorpus]),
            (self.chkFilterAddressOrgStructure,   [self.cmbFilterAddressOrgStructureType,
                                                   self.cmbFilterAddressOrgStructure]),
            (self.chkFilterBeds,                  [self.cmbFilterStatusBeds, self.cmbFilterOrgStructureBeds]),
            (self.chkFilterRegAddressIsEmpty,     []),
            (self.chkFilterLocAddressIsEmpty,     []),
            (self.chkFilterAttachType,            [self.cmbFilterAttachCategory, self.edtFilterAttachBegDate, self.edtFilterAttachEndDate,
                                                        self.cmbFilterAttachType, self.chkFilterToStatement]),
            (self.chkFilterToStatement,           [self.cmbFilterToStatement]),
            (self.chkFilterAttach,                [self.cmbFilterAttachOrganisation, self.chkFilterNotAttachOrganisation]),
            (self.chkFilterAttachNonBase,         []),
            (self.chkFilterTempInvalid,           [self.edtFilterBegTempInvalid, self.edtFilterEndTempInvalid]),
            (self.chkFilterTFUnconfirmed,         []),
            (self.chkFilterTFConfirmed,           [self.edtFilterBegTFConfirmed, self.edtFilterEndTFConfirmed]),
            (self.chkFilterClientConsent,         [self.cmbFilterClientConsentType, self.pnlFilterClientConsentDateRange,
                                                            self.cmbFilterPersonConsent, self.cmbFilterClientConsentValue,
                                                            self.edtFilterClientConsentBegDate, self.edtFilterClientConsentEndDate,
                                                            self.label_4, self.label_5]),
            (self.chkFilterVaccinationPeriod,     [self.edtFilterVaccinationBegDate,
                                                   self.edtFilterVaccinationEndDate]),
            (self.chkFilterVaccinationCalendar,   [self.cmbFilterVaccinationCalendar]),
            (self.chkFilterVaccinationSeria,      [self.edtFilterVaccinationSeria]),
            (self.chkFilterVaccinationType,       [self.cmbFilterVaccinationType]),
            (self.chkFilterContingent,            [self.cmbFilterContingent]),
            (self.chkFilterMedicalExemption,      [self.cmbFilterMedicalExemption]),
            (self.chkFilterMedicalExemptionType,  [self.cmbFilterMedicalExemptionType]),
            (self.chkFilterVaccinationPerson,     [self.cmbFilterVaccinationPerson]),
            (self.chkFilterExcludeDead, []),
            (self.chkFilterDead, [self.chkFilterDeathBegDate, self.edtFilterDeathBegDate, self.chkFilterDeathEndDate, self.edtFilterDeathEndDate]),
            (self.chkClientMKB, [self.edtClientMKBFrom, self.edtClientMKBTo]),
            (self.chkFilterClientNote,            [self.edtFilterClientNote]),
            (self.chkClientMKB, [self.edtClientMKBFrom, self.edtClientMKBTo]),
            (self.chkFilterExternalNotification, [self.lblENbegDate, self.lblENendDate, self.edtExternalNotificationBegDate, self.edtExternalNotificationEndDate]),
            (self.chkFilterClientResearch, [self.chkFilterClientNoResearch, self.cmbFilterClientResearchKind, self.lblCRBegDate, self.lblCREndDate, self.edtFilterClientResearchBegDate, self.edtFilterClientResearchEndDate]),
            (self.chkFilterClientNoResearch, []),
            ]

        self.tblActionsStatus.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tblActionsDiagnostic.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tblActionsCure.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tblActionsMisc.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tblActionsAll.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)

        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkSocStatuses, False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterDocumentLocation, False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterContingentType, False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterEventDispanser, False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterContingentMKB, False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterContingentSpeciality, False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterAttachType, False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterDocument, False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterRegionSMO, False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterAddress, False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterPolicy, False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterClientConsent, False)

        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterCreatePerson, False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterCreateDate, False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterModifyPerson, False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterModifyDate, False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterEvent, False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterEventOpen, False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterAge, False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterAddressOrgStructure, False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterBeds, False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterDead, False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterAttach, False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterTempInvalid, False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkClientMKB, False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterClientNote, False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterExternalNotification, False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterClientResearch, False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterTFConfirmed, False)

        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterVaccinationPeriod, False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterVaccinationCalendar, False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterVaccinationSeria, False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterVaccinationType, False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterContingent, False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterMedicalExemption, False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterMedicalExemptionType, False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterVaccinationPerson, False)

        for row in self.chkListOnClientsPage:
            if row[0] == self.chkFilterAttachType:
                for element in row[1]:
                    self.setChildElementsVisible(self.chkListOnClientsPage, element, False)

        if QtGui.qApp.getOpeningSnilsCardindex():
            self.chkFilterSNILS.setChecked(True)
            self.chkFilterSNILS.setEnabled(False)
            self.chkFilterId.setVisible(False)
            self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterId, False)
            self.onChkFilterToggled(self.chkFilterSNILS, True)
            self.cmbFilterEventByClient.setDisabled(True)
            self.cmbFilterAction.setDisabled(True)
        self.onChkFilterToggled(self.chkFilterClientConsent, False)

        self.edtFilterEventId.setValidator(self.idValidator)
        self.edtFilterJobTicketId.setValidator(self.idValidator)
        self.edtFilterActionJobTicketId.setValidator(self.idValidator)
        # self.cmbFilterEventPurpose.setTable('rbEventTypePurpose', False, filter='code != \'0\'')
        self.cmbFilterEventType.setTable('EventType', False, filter=getWorkEventTypeFilter(isApplyActive=True))
        # self.cmbFilterEventSpeciality.setTable('rbSpeciality', False)
        # self.cmbFilterEventDisease.setTable('rbDiseaseCharacter', False)
        self.cmbFilterEventPerson.setOrgId(None)

        self.cmbFilterEventPerson.setAddNone(False)
        self.cmbFilterEventPerson.addNotSetValue()
        self.cmbFilterEventCreatePerson.setSpecialityPresent(False)
        self.cmbFilterEventModifyPerson.setSpecialityPresent(False)

        self.edtFilterVaccinationBegDate.canBeEmpty(False)
        self.edtFilterVaccinationEndDate.canBeEmpty(False)
        self.cmbFilterIdentification.setTable('rbAccountingSystem', True, 'domain = \'client\'')
        self.cmbFilterIdentification.setValue(forceRef(QtGui.qApp.preferences.appPrefs.get('FilterAccountingSystemClient', 0)))
        self.cmbFilterEventActions.setClassesPopupVisible(True)
        self.cmbFilterEventActions.setClasses([0, 1, 2, 3])
        self.cmbFilterEventActions.setOrgStructure(None)

        self.chkListOnEventsPage = [
            (self.chkFilterEventPurpose, [self.cmbFilterEventPurpose]),
            (self.chkFilterEventType, [self.cmbFilterEventType]),
            (self.chkFilterEventSetDate, [self.edtFilterEventBegSetDate, self.edtFilterEventEndSetDate, self.edtFilterEventBegSetTime, self.edtFilterEventEndSetTime]),
            (self.chkFilterEventEmptyExecDate, []),
            (self.chkFilterEventExecDate, [self.edtFilterEventBegExecDate, self.edtFilterEventEndExecDate, self.edtFilterEventBegExecTime, self.edtFilterEventEndExecTime]),
            (self.chkFilterEventNextDate, [self.edtFilterEventBegNextDate, self.edtFilterEventEndNextDate]),
            (self.chkFilterEventOrgStructure, [self.cmbFilterEventOrgStructure]),
            (self.chkFilterEventSpeciality, [self.cmbFilterEventSpeciality]),
            (self.chkFilterEventPerson, [self.cmbFilterEventPerson]),
            (self.chkFilterEventIsPrimary, [self.cmbFilterEventIsPrimary]),
            (self.chkFilterEventOrder, [self.cmbFilterEventOrder]),
            (self.chkFilterEventDispanser, [self.cmbFilterEventDispanser]),
            (self.chkFilterEventLPU, [self.cmbFilterEventLPU]),
            (self.chkFilterEventNonBase, []),
            (self.chkRelegateOrg, [self.cmbRelegateOrg, self.chkEverythingExcept]),
            (self.chkFilterEventMes, [self.edtFilterEventMes]),
            (self.chkFilterEventCSG, [self.edtFilterEventCSG]),
            (self.chkFilterEventCSGDate, [self.edtFilterEventCSGBegDate, self.edtFilterEventCSGEndDate]),
            (self.chkFilterEventCSGMKB, [self.edtCSGMKBFrom, self.edtCSGMKBTo]),
            (self.chkFilterCSGPayStatus, [self.cmpFilterCSGPayStatusCode, self.cmbFilterCSGPayStatusFinance]),
            (self.chkMKB, [self.chkPreliminary, self.chkConcomitant, self.edtMKBFrom, self.edtMKBTo]),
            (self.chkFilterEventResult, [self.cmbFilterEventResult]),
            (self.chkFilterEventDisease, [self.cmbFilterEventDisease]),
            (self.chkFilterEventCreatePerson, [self.cmbFilterEventCreatePerson]),
            (self.chkFilterEventCreateDate, [self.edtFilterEventBegCreateDate, self.edtFilterEventEndCreateDate]),
            (self.chkFilterEventModifyPerson, [self.cmbFilterEventModifyPerson]),
            (self.chkFilterEventModifyDate, [self.edtFilterEventBegModifyDate, self.edtFilterEventEndModifyDate]),
            (self.chkErrorInDiagnostic, []),
            (self.chkFilterEventInAccountItems, [self.cmbFilterEventInAccountItems]),
            (self.chkFilterEventPayStatus, [self.cmpFilterEventPayStatusCode, self.cmbFilterEventPayStatusFinance]),
            (self.chkFilterVisitPayStatus, [self.cmpFilterVisitPayStatusCode, self.cmbFilterVisitPayStatusFinance]),
            (self.chkFilterEventId, [self.edtFilterEventId]),
            (self.chkFilterJobTicketId, [self.edtFilterJobTicketId]),
            (self.chkFilterExternalId, [self.edtFilterExternalId]),
            (self.chkFilterAccountSumLimit, [self.cmbFilterAccountSumLimit, self.edtFilterSumLimitFrom, self.edtFilterSumLimitTo, self.edtFilterSumLimitDelta, self.label, self.label_2, self.label_3]),
            (self.chkFilterVisits, [self.cmbFilterVisitScene, self.cmbFilterVisitType, self.cmbFilterVisitProfile]),
            (self.chkFilterEventPayer, [self.cmbFilterEventPayer, self.btnFilterEventSelectPayer]),
            (self.chkFilterEventFinance, [self.edtFilterEventFinance]),
            (self.chkFilterEventContract, [self.edtFilterEventContract, self.btnFilterEventContract]),
            (self.chkFilterEventExpertId, [self.cmbFilterEventExpertId]),
            (self.chkFilterEventExpertiseDate, [self.edtFilterEventBegExpertiseDate, self.edtFilterEventEndExpertiseDate]),
            (self.chkFilterEventExport, [self.cmbFilterEventExportStatus, self.cmbFilterEventExportSystem]),
            (self.chkFilterPayStatus, [self.chkFilterVisitPayStatus, self.chkFilterCSGPayStatus, self.chkFilterEventPayer, self.chkFilterEventFinance, self.chkFilterEventContract]),
            (self.chkFilterEventActions, [self.cmbFilterEventActions, self.chkFilterEventActionsExclude])
            ]

        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkMKB, False)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterVisits, False)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterPayStatus, False)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventActions, False)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventSetDate, False)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventExecDate, False)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventNextDate, False)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventOrgStructure, False)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventSpeciality, False)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventPerson, False)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventDispanser, False)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventIsPrimary, False)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventOrder, False)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventLPU, False)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkRelegateOrg, False)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventCSGDate, False)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventCSGMKB, False)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventResult, False)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventDisease, False)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkMKB, False)

        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventCreatePerson, False)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventCreateDate, False)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventModifyPerson, False)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventModifyDate, False)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventPayStatus, False)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventId, False)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterJobTicketId, False)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterExternalId, False)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterAccountSumLimit, False)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterVisits, False)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterPayStatus, False)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterVisitPayStatus, False)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterCSGPayStatus, False)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventPayer, False)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventContract, False)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventExpertId, False)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventExpertiseDate, False)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventExport, False)

        for row in self.chkListOnEventsPage:
            if row[0] == self.chkFilterPayStatus:
                for element in row[1]:
                    self.setChildElementsVisible(self.chkListOnEventsPage, element, False)

        self.cmbFilterActionType.setAllSelectable(True)
        self.cmbFilterActionType.setClass(0)
        self.cmbFilterActionType.setClassesPopup([0])
        self.cmbFilterActionType.setOrgStructure(None)
        # self.cmbFilterActionSetSpeciality.setTable('rbSpeciality', False)
        # self.cmbFilterActionExecSetSpeciality.setTable('rbSpeciality', False)
        # self.cmbFilterEventExportSystem.setTable('rbExternalSystem', True)
        self.cmbFilterActionSetPerson.setOrgId(None)
        self.cmbFilterActionSetPerson.setAddNone(True)
        self.cmbFilterActionExecSetPerson.setOrgId(None)
        self.cmbFilterActionExecSetPerson.setAddNone(True)
        self.cmbFilterActionExecSetPerson.addNotSetValue()
        self.cmbFilterActionAssistant.addNotSetValue()
        self.cmbFilterActionCreatePerson.setSpecialityPresent(False)
        self.cmbFilterActionModifyPerson.setSpecialityPresent(False)
        # self.cmbFilterActionFinance.setTable('rbFinance', addNone=True)

        self.__filterActionContractId = None
        self.chkListOnActionsPage = [
            (self.chkFilterActionType, [self.cmbFilterActionType, self.chkFilledProperty]),
            (self.chkFilterActionServiceType, [self.cmbFilterActionServiceType]),
            (self.chkFilterActionStatus,     [self.cmbFilterActionStatus]),
            (self.chkFilterActionOrg,        [self.cmbFilterActionOrg]),
            (self.chkFilterActionSetDate,    [self.edtFilterActionBegSetDate, self.edtFilterActionEndSetDate]),
            (self.chkFilterActionSetOrgStructure, [self.cmbFilterActionSetOrgStructure]),
            (self.chkFilterActionSetSpeciality, [self.cmbFilterActionSetSpeciality]),
            (self.chkFilterActionSetPerson, [self.cmbFilterActionSetPerson, self.chkFilterActionSNILSSetPerson]),
            (self.chkFilterActionIsUrgent, []),
            (self.chkFilterActionPlannedEndDate, [self.edtFilterActionBegPlannedEndDate, self.edtFilterActionEndPlannedEndDate]),
            (self.chkFilterActionBegDate, [self.edtFilterActionBegBegDate, self.edtFilterActionBegBegTime, self.edtFilterActionEndBegDate, self.edtFilterActionEndBegTime]),
            (self.chkFilterActionExecDate, [self.edtFilterActionBegExecDate, self.edtFilterActionBegExecTime, self.edtFilterActionEndExecDate, self.edtFilterActionEndExecTime]),
            (self.chkFilterActionExecSetPerson, [self.cmbFilterActionExecSetPerson, self.chkFilterActionSNILSExecSetPerson]),
            (self.chkFilterActionExecSetOrgStructure, [self.cmbFilterActionExecSetOrgStructure]),
            (self.chkFilterActionExecSetSpeciality, [self.cmbFilterActionExecSetSpeciality]),
            (self.chkFilterActionAssistant, [self.cmbFilterActionAssistant]),
            (self.chkFilterActionMKB, [self.edtFilterActionMKBFrom, self.edtFilterActionMKBTo]),
            (self.chkFilterActionTakenTissueJournal, [self.cmbFilterActionTakenTissueJournal]),
            (self.chkFilterActionUncoordinated, []),
            (self.chkFilterActionJobTicketId, [self.edtFilterActionJobTicketId]),
                        (self.chkFilterActionId, [self.edtFilterActionId]),
            (self.chkFilterActionCreatePerson, [self.cmbFilterActionCreatePerson]),
            (self.chkFilterActionCreateDate, [self.edtFilterActionBegCreateDate, self.edtFilterActionEndCreateDate]),
            (self.chkFilterActionModifyPerson, [self.cmbFilterActionModifyPerson]),
            (self.chkFilterActionModifyDate, [self.edtFilterActionBegModifyDate, self.edtFilterActionEndModifyDate]),
            (self.chkFilterActionPayStatus, [self.cmpFilterActionPayStatusCode, self.cmbFilterActionPayStatusFinance]),
            (self.chkTakeIntoAccountProperty, [self.chkFilledProperty, self.chkThresholdPenaltyGrade, self.chkFilledProperty, self.cmbFilledProperty,self.lblListProperty,self.cmbListPropertyCond,self.tblListOptionActionProperty, self.edtThresholdPenaltyGrade]),
            (self.chkThresholdPenaltyGrade, [self.edtThresholdPenaltyGrade]),
#            (self.chkListProperty, [self.cmbListPropertyCond, self.tblListOptionActionProperty]),
            (self.chkFilledProperty, [self.cmbFilledProperty, self.lblListProperty, self.cmbListPropertyCond, self.tblListOptionActionProperty]),
            (self.chkFilterActionFinance, [self.cmbFilterActionFinance]),
            (self.chkFilterActionPayer, [self.cmbFilterActionPayer, self.btnFilterActionSelectPayer]),
            (self.chkFilterActionContract, [self.edtFilterActionContract, self.btnFilterActionContract]),
            (self.chkFilterActionExport, [self.cmbFilterActionExportStatus, self.cmbFilterActionExportSystem]),
            (self.chkFilterActionAttachedFiles, [self.cmbFilterActionAttachedFiles, self.cmbFilterActionTypeDoc, self.cmbFilterActionSigned, self.lblActionTypeDoc, self.lblActionSigned,
                                                 self.chkFilterActionFileAttachId, self.edtFilterActionFileAttachId, self.chkFilterActionExportSuitable]),
            (self.chkFilterActionFileAttachId, [self.edtFilterActionFileAttachId]),
            ]

        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionSetDate, False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionSetOrgStructure, False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionSetSpeciality, False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionSetPerson, False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionSNILSSetPerson, False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionPlannedEndDate, False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionStatus, False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionBegDate, False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionExecDate, False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionExecSetOrgStructure, False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionExecSetSpeciality, False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionExecSetPerson, False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionSNILSExecSetPerson, False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionAssistant, False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionJobTicketId, False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionMKB, False)

        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionCreatePerson, False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionCreateDate, False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionModifyPerson, False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionModifyDate, False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkTakeIntoAccountProperty, False)
        # self.setChildElementsVisible(self.chkListOnActionsPage, self.chkListProperty, False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionPayStatus, False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionPayer, False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionContract, False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionExport, False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionAttachedFiles, False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionFileAttachId, False)
        
        self.__actionTypeIdListByClassPage = [None] * 4

        # self.cmbFilterVisitsType.setTable('rbVisitType', False)
        # self.cmbFilterExecSetSpecialityVisit.setTable('rbSpeciality', False)
        # self.cmbFilterVisitFinance.setTable('rbFinance', True)
        # self.cmbFilterActionExportSystem.setTable('rbExternalSystem', True)
        self.cmbFilterExecSetPersonVisit.setOrgId(None)
        self.cmbFilterExecSetPersonVisit.setAddNone(True)
        self.cmbFilterExecSetPersonVisit.addNotSetValue()
        self.cmbFilterVisitAssistant.addNotSetValue()
        self.cmbFilterVisitCreatePersonEx.setSpecialityPresent(False)
        self.cmbFilterVisitModifyPersonEx.setSpecialityPresent(False)
        self.chkListOnVisitsPage = [
            (self.chkFilterVisitType, [self.cmbFilterVisitsType]),
            (self.chkFilterVisitExecDate, [self.edtFilterVisitBegExecDate, self.edtFilterVisitBegExecTime, self.edtFilterVisitEndExecDate, self.edtFilterVisitEndExecTime]),
            (self.chkFilterExecSetOrgStructureVisit, [self.cmbFilterExecSetOrgStructureVisit]),
            (self.chkFilterExecSetSpecialityVisit, [self.cmbFilterExecSetSpecialityVisit]),
            (self.chkFilterExecSetPersonVisit, [self.cmbFilterExecSetPersonVisit]),
            (self.chkFilterVisitAssistant, [self.cmbFilterVisitAssistant]),
            (self.chkFilterVisitFinance, [self.cmbFilterVisitFinance]),
            (self.chkFilterServiceVisit, [self.cmbFilterServiceVisit]),
            (self.chkFilterSceneVisit, [self.cmbFilterSceneVisit]),
            (self.chkFilterVisitCreatePersonEx, [self.cmbFilterVisitCreatePersonEx]),
            (self.chkFilterVisitCreateDateEx, [self.edtFilterVisitBegCreateDateEx, self.edtFilterVisitEndCreateDateEx]),
            (self.chkFilterVisitModifyPersonEx, [self.cmbFilterVisitModifyPersonEx]),
            (self.chkFilterVisitModifyDateEx, [self.edtFilterVisitBegModifyDateEx, self.edtFilterVisitEndModifyDateEx]),
            (self.chkFilterVisitPayStatusEx, [self.cmpFilterVisitPayStatusCodeEx, self.cmbFilterVisitPayStatusFinanceEx])
            ]
        self.setChildElementsVisible(self.chkListOnVisitsPage, self.chkFilterVisitExecDate, False)
        self.setChildElementsVisible(self.chkListOnVisitsPage, self.chkFilterExecSetOrgStructureVisit, False)
        self.setChildElementsVisible(self.chkListOnVisitsPage, self.chkFilterExecSetSpecialityVisit, False)
        self.setChildElementsVisible(self.chkListOnVisitsPage, self.chkFilterExecSetPersonVisit, False)
        self.setChildElementsVisible(self.chkListOnVisitsPage, self.chkFilterVisitAssistant, False)
        self.setChildElementsVisible(self.chkListOnVisitsPage, self.chkFilterVisitFinance, False)
        self.setChildElementsVisible(self.chkListOnVisitsPage, self.chkFilterServiceVisit, False)
        self.setChildElementsVisible(self.chkListOnVisitsPage, self.chkFilterSceneVisit, False)
        self.setChildElementsVisible(self.chkListOnVisitsPage, self.chkFilterVisitCreatePersonEx, False)
        self.setChildElementsVisible(self.chkListOnVisitsPage, self.chkFilterVisitCreateDateEx, False)
        self.setChildElementsVisible(self.chkListOnVisitsPage, self.chkFilterVisitModifyPersonEx, False)
        self.setChildElementsVisible(self.chkListOnVisitsPage, self.chkFilterVisitModifyDateEx, False)
        self.setChildElementsVisible(self.chkListOnVisitsPage, self.chkFilterVisitPayStatusEx, False)

        self.chkListOnExpertPage = [
            (self.chkFilterExpertDocType, [self.cmbFilterExpertDocType]),
            (self.chkPrimaryOrDuble, [self.cmbPrimaryOrDuble]),
            (self.chkFilterTempInvalidDocType, [self.cmbFilterTempInvalidDocType]),
            (self.chkFilterExpertSerial,  [self.edtFilterExpertSerial]),
            (self.chkFilterExpertNumber,  [self.edtFilterExpertNumber]),
            (self.chkFilterExpertReason,  [self.cmbFilterExpertReason]),
            (self.chkFilterExpertResult,  [self.cmbFilterExpertResult]),
            (self.chkFilterExpertBegDate, [self.edtFilterExpertBegBegDate, self.edtFilterExpertEndBegDate]),
            (self.chkFilterExpertEndDate, [self.edtFilterExpertBegEndDate, self.edtFilterExpertEndEndDate]),
            (self.chkFilterExpertOrgStruct, [self.cmbFilterExpertOrgStruct]),
            (self.chkFilterExpertSpeciality, [self.cmbFilterExpertSpeciality]),
            (self.chkFilterExpertPerson,  [self.cmbFilterExpertPerson]),
            (self.chkFilterExpertMKB,     [self.edtFilterExpertBegMKB,     self.edtFilterExpertEndMKB]),
            (self.chkFilterExpertState,  [self.cmbFilterExpertState]),
            (self.chkFilterExpertDuration,[self.edtFilterExpertBegDuration, self.edtFilterExpertEndDuration]),
            (self.chkFilterExpertInsuranceOfficeMark,[self.cmbFilterExpertInsuranceOfficeMark]),
            (self.chkFilterExpertExportFSS, [self.cmbFilterExpertExportFSS]),
            (self.chkFilterExpertLinked,  []),
            (self.chkFilterExpertExternal, [self.cmbFilterExpertExternal]),
            (self.chkFilterExpertCreatePerson, [self.cmbFilterExpertCreatePerson]),
            (self.chkFilterExpertCreateDate,   [self.edtFilterExpertBegCreateDate, self.edtFilterExpertEndCreateDate]),
            (self.chkFilterExpertModifyPerson, [self.cmbFilterExpertModifyPerson]),
            (self.chkFilterExpertModifyDate,   [self.edtFilterExpertBegModifyDate, self.edtFilterExpertEndModifyDate]),
            ]
        self.initFilterExpertExpertiseMC()
        self.chkListOnExpertMCPage = [
            (self.chkFilterExpertExpertiseMC,  [self.cmbFilterExpertExpertiseMC]),
            (self.chkFilterExpertExpertiseTypeMC, [self.cmbFilterExpertExpertiseTypeMC]),
            (self.chkFilterExpertNumberExpertise, [self.edtFilterExpertNumberExpertise]),
            (self.chkFilterExpertNumberMC,     [self.edtFilterExpertNumberMC]),
            (self.chkFilterExpertSetPersonMC,  [self.cmbFilterExpertSetPersonMC]),
            (self.chkFilterExpertDirectionDateMC, [self.edtFilterExpertDirectionBegDateMC, self.edtFilterExpertDirectionEndDateMC]),
            (self.chkFilterExpertOrgStructMC,  [self.cmbFilterExpertOrgStructMC]),
            (self.chkFilterExpertSpecialityMC, [self.cmbFilterExpertSpecialityMC]),
            (self.chkFilterDirectDateOnMC,     [self.edtFilterBegDirectDateOnMC, self.edtFilterEndDirectDateOnMC]),
            (self.chkFilterExecDateMC,         [self.edtFilterBegExecDateMC, self.edtFilterEndExecDateMC]),
            (self.chkFilterExpertClosedMC,     [self.cmbFilterExpertClosedMC]),
            (self.chkFilterExpertExpertiseCharacterMC, [self.cmbFilterExpertExpertiseCharacterMC]),
            (self.chkFilterExpertExpertiseKindMC,      [self.cmbFilterExpertExpertiseKindMC]),
            (self.ghkFilterExpertExpertiseObjectMC,    [self.cmbFilterExpertExpertiseObjectMC]),
            (self.chkFilterExpertExpertiseArgumentMC,  [self.cmbFilterExpertExpertiseArgumentMC]),
            (self.chkExpertIdMC,               [self.cmbExpertIdMC]),
            (self.chkFilterExpertExportedToExternalISMC, [self.cmbFilterExpertExportedTypeMC, self.cmbFilterExpertIntegratedISMC]),
            (self.chkFilterExpertMKBMC,        [self.edtFilterExpertBegMKBMC, self.edtFilterExpertEndMKBMC]),
            (self.chkFilterExpertCreateDateMC, [self.edtFilterExpertBegCreateDateMC, self.edtFilterExpertEndCreateDateMC]),
            (self.chkFilterExpertCreatePersonMC, [self.cmbFilterExpertCreatePersonMC]),
            (self.chkFilterExpertModifyDateMC,   [self.edtFilterExpertBegModifyDateMC, self.edtFilterExpertEndModifyDateMC]),
            (self.chkFilterExpertModifyPersonMC, [self.cmbFilterExpertModifyPersonMC]),
            ]
        self.__tempInvalidDocTypeIdListByTypePage = [None] * 6
        self.cmbFilterExpertExportFSS.setEnabled(self.chkFilterExpertExportFSS.isChecked())

        QMetaObject.connectSlotsByName(self)  # т.к. в setupUi параметр не self

        self.tblActionsStatusProperties.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.tblActionsDiagnosticProperties.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.tblActionsCureProperties.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.tblActionsMiscProperties.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.tblActionsAllProperties.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.tblExpertDirectionsPropertiesMC.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.tblExpertProtocolsPropertiesMC.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.tblExpertMSIProperties.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.TFAccountingSystemId = QtGui.qApp.TFAccountingSystemId()
        if QtGui.qApp.defaultKLADR()[:2] == u'23':
            self.chkFilterTFConfirmed.setVisible(False)
            self.chkFilterTFUnconfirmed.setVisible(False)

        if not self.TFAccountingSystemId:
            self.chkFilterTFUnconfirmed.setEnabled(False)
            self.chkFilterTFConfirmed.setEnabled(False)
        
        attachedDocsTables = [
            self.tblActionsStatusAttachedDocuments, 
            self.tblActionsDiagnosticAttachedDocuments, 
            self.tblActionsCureAttachedDocuments,
            self.tblActionsMiscAttachedDocuments,
            self.tblActionsAllAttachedDocuments,
            ]
        
        for tab in attachedDocsTables:
            acts = [tab.actAddKey, tab.actAdd, tab.actRename, tab.actComment, tab.actDelete, tab.actSignAsResp, tab.actSignAsOrg]
            for act in acts:
                act.setVisible(False)
            tab.horizontalHeader().setStretchLastSection(True)
            tab.resizeColumnsToContents()
            tab.resizeRowsToContents()
        
        self.tabActionsStatusAttachedDocuments.setEnabled(QtGui.qApp.userHasAnyRight([urAdmin, urCanOpenOwnAttachedFile, urCanOpenAnyAttachedFile]))
        self.tabActionsDiagnosticAttachedDocuments.setEnabled(QtGui.qApp.userHasAnyRight([urAdmin, urCanOpenOwnAttachedFile, urCanOpenAnyAttachedFile]))
        self.tabActionsCureAttachedDocuments.setEnabled(QtGui.qApp.userHasAnyRight([urAdmin, urCanOpenOwnAttachedFile, urCanOpenAnyAttachedFile]))
        self.tabActionsMiscAttachedDocuments.setEnabled(QtGui.qApp.userHasAnyRight([urAdmin, urCanOpenOwnAttachedFile, urCanOpenAnyAttachedFile]))
        self.tabActionsAllAttachedDocuments.setEnabled(QtGui.qApp.userHasAnyRight([urAdmin, urCanOpenOwnAttachedFile, urCanOpenAnyAttachedFile]))
        
        self.__filter = {}
        self.__filterEventContractId = None
        self.filterEventContractParams = {}
        self.txtClientInfoBrowser.actions.append(self.actEditClient)
        self.txtClientInfoBrowser.actions.append(self.actRelationsClient)
        self.txtClientInfoBrowser.actions.append(self.actOpenClientDocumentTrackingHistory)
        self.txtClientInfoBrowser.actions.append(self.actEditStatusObservationClient)
        self.txtClientInfoBrowser.actions.append(self.actShowContingentsClient)
        self.txtClientInfoBrowser.actions.append(self.actSurveillancePlanningClients)
        self.txtClientInfoBrowser.actions.append(self.actUpdateF111)
        self.txtClientInfoBrowser.actions.append(self.actCheckClientAttach)
        self.txtClientInfoBrowser.actions.append(self.actPortal_Doctor)
        self.txtClientInfoBrowserEvents.actions.append(self.actEventEditClient)
        self.txtClientInfoBrowserEvents.actions.append(self.actEventRelationsClient)
        self.txtClientInfoBrowserEvents.actions.append(self.actEventOpenClientVaccinationCard)
        self.txtClientInfoBrowserEvents.actions.append(self.actStatusObservationClientBrowserByEvent)
        self.txtClientInfoBrowserEvents.actions.append(self.actSurveillancePlanningClients)
        self.txtClientInfoBrowserEvents.actions.append(self.actUpdateF111)
        self.addObject('qshcStatusObservationClientBrowserEvents', QtGui.QShortcut('Shift+F5', self.txtClientInfoBrowserEvents, self.on_actStatusObservationClientBrowserByEvent_triggered))
        self.qshcStatusObservationClientBrowserEvents.setContext(Qt.WidgetShortcut)
        self.txtClientInfoBrowserEvents.actions.append(self.actCheckClientAttach)
        self.txtClientInfoBrowserEvents.actions.append(self.actCreateRelatedAction)
        self.txtClientInfoBrowserEvents.actions.append(self.actPortal_Doctor)
        self.txtClientInfoBrowserEvents.actions.append(self.actJumpToRegistry)
        self.txtClientInfoBrowserAmbCard.actions.append(self.actAmbCardEditClient)
        self.txtClientInfoBrowserAmbCard.actions.append(self.actAmbCardRelationsClient)
        self.txtClientInfoBrowserAmbCard.actions.append(self.actAmbCardOpenClientVaccinationCard)
        self.txtClientInfoBrowserAmbCard.actions.append(self.actCheckClientAttach)
        self.txtClientInfoBrowserAmbCard.actions.append(self.actPortal_Doctor)
        self.txtClientInfoBrowserActions.actions.append(self.actActionEditClient)
        self.txtClientInfoBrowserActions.actions.append(self.actActionsRelationsClient)
        self.txtClientInfoBrowserActions.actions.append(self.actActionOpenClientVaccinationCard)
        self.txtClientInfoBrowserActions.actions.append(self.actCheckClientAttach)
        self.txtClientInfoBrowserActions.actions.append(self.actPortal_Doctor)
        self.txtClientInfoBrowserActions.actions.append(self.actJumpToRegistry)
        self.txtClientInfoBrowserExpert.actions.append(self.actExpertEditClient)
        self.txtClientInfoBrowserExpert.actions.append(self.actExpertRelationsClient)
        self.txtClientInfoBrowserExpert.actions.append(self.actCheckClientAttach)
        self.txtClientInfoBrowserExpert.actions.append(self.actPortal_Doctor)
        self.txtClientInfoBrowserVisits.actions.append(self.actActionEditClient)
        self.txtClientInfoBrowserVisits.actions.append(self.actVisitRelationsClient)
        self.txtClientInfoBrowserVisits.actions.append(self.actCheckClientAttach)
        self.txtClientInfoBrowserVisits.actions.append(self.actPortal_Doctor)
        self.tblClients.createPopupMenu(
                [
                    self.actSimplifiedClientSearch,
                    self.actCreateEvent,
                    self.actListVisitsBySchedules,
                    self.actBatchRegLocatCard,
                    self.actaddClients,
                    self.actaClients,
                    self.actStatusObservationClient,
                    self.actControlDoublesRecordClient,
                    self.actControlDoublesRecordClientList,
                    self.actReservedOrderQueueClient,
                    self.actOpenClientVaccinationCard,
                    self.actShowPacsImages,
                    self.actNotify,
                    self.actNotificationLog,
                    self.actShowContingentsClient,
                ]
                )
        self.tblClients.addPopupRecordProperies()

        self.tblEvents.addPopupAction(self.actOpenAccountingByEvent)
        self.tblEvents.addPopupAction(self.actGroupJobAppointment)
        self.tblEvents.addPopupAction(self.actUpdateEventTypeByEvent)
        self.tblEvents.addPopupAction(self.actConcatEvents)
        self.tblEvents.addPopupAction(self.actUndoExpertise)
        self.tblEvents.addPopupAction(self.actMakePersonalAccount)
        self.tblEvents.addPopupAction(self.actStatusObservationClientByEvent)
        self.tblEvents.addPopupAction(self.actSurveillancePlanningClientsByEvent)
        self.tblEvents.addPopupAction(self.actAddActionEvent)
        self.tblEvents.addPopupAction(self.actJobTicketsEvent)
        self.tblEvents.addPopupAction(self.actCreateRelatedAction)
        self.tblEvents.addPopupAction(self.actBatchRegLocatCard)
        if forceString(QtGui.qApp.getGlobalPreference('useServiceGISOMS')) == u'да':
            self.tblEvents.addPopupAction(self.actSendEventFPUMP)
        self.tblEvents.addPopupDelRow()
        self.addObject('qshcAddActionEvent', QtGui.QShortcut('Shift+F8', self.tblEvents, self.on_actAddActionEvent_triggered))
        self.tblEvents.installEventFilter(self)
        self.qshcAddActionEvent.setContext(Qt.WidgetShortcut)


        self.tblEventActions.addPopupAction(self.actOpenAccountingByAction)
        self.tblEventVisits.addPopupAction(self.actOpenAccountingByVisit)
        self.tblActionsStatus.createPopupMenu([self.actEditActionEvent, self.actNotifyFromTabActions, self.actActionGroupSign, self.actOpenAccountingBySingleAction])
        self.tblVisits.createPopupMenu([self.actEditVisitEvent])
        self.tblVisits.addPopupAction(self.actOpenAccountingBySingleVisits)
        self.tblActionsDiagnostic.createPopupMenu([self.actEditActionEvent, self.actNotifyFromTabActions, self.actActionGroupSign, self.actOpenAccountingBySingleAction])
        self.tblActionsCure.createPopupMenu([self.actEditActionEvent, self.actNotifyFromTabActions, self.actActionGroupSign, self.actOpenAccountingBySingleAction])
        self.tblActionsMisc.createPopupMenu([self.actEditActionEvent, self.actNotifyFromTabActions, self.actActionGroupSign, self.actOpenAccountingBySingleAction])
        self.tblActionsAll.createPopupMenu([self.actEditActionEvent, self.actNotifyFromTabActions, self.actActionGroupSign, self.actOpenAccountingBySingleAction])
        self.tblExpertTempInvalid.createPopupMenu([self.actExpertTempInvalidChangeToOpen, '-', self.actExpertTempInvalidNext, self.actExpertTempInvalidPrev, '-', self.actExpertTempInvalidDelete])
        self.tblExpertTempInvalidRelation.createPopupMenu([self.actExpertTempInvalidNext, self.actExpertTempInvalidPrev, '-', self.actExpertTempInvalidDelete])
        self.tblExpertDisability.createPopupMenu([self.actExpertDisabilityNext, self.actExpertDisabilityPrev, '-', self.actExpertDisabilityDelete])
        self.tblExpertDisabilityRelation.createPopupMenu([self.actExpertDisabilityNext, self.actExpertDisabilityPrev, '-', self.actExpertDisabilityDelete])
        self.tblExpertVitalRestriction.createPopupMenu([self.actExpertVitalRestrictionNext, self.actExpertVitalRestrictionPrev, '-', self.actExpertVitalRestrictionDelete])
        self.tblExpertVitalRestrictionRelation.createPopupMenu([self.actExpertVitalRestrictionNext, self.actExpertVitalRestrictionPrev, '-', self.actExpertVitalRestrictionDelete])
        self.tblExpertDirectionsMC.createPopupMenu([self.actExpertMedicalCommissionDelete, '-', self.actExpertMedicalCommissionSelected, self.actExpertMedicalCommissionUpdateGroup, self.actExpertMedicalCommissionClear, '-', self.actExpertMedicalCommissionUpdate, self.actExpertMCUpdateTempInvalid, '-', self.actEditExpertMCEvent])
        self.tblExpertProtocolsMC.createPopupMenu([self.actExpertMedicalCommissionDelete, '-', self.actExpertMedicalCommissionSelected, self.actExpertMedicalCommissionUpdateGroup, self.actExpertMedicalCommissionClear, '-', self.actExpertMedicalCommissionUpdate, self.actExpertMCUpdateTempInvalid, self.actExpertMedicalCommissionMSI, '-', self.actEditExpertMCEvent])
        self.tblExpertMedicalSocialInspection.createPopupMenu([self.actExpertMedicalCommissionDelete, '-', self.actExpertMedicalCommissionUpdate, '-', self.actExpertMCUpdateTempInvalid, '-', self.actEditExpertMCEvent])
        self.tblActionsStatus.addPopupRecordProperies()
        self.tblActionsDiagnostic.addPopupRecordProperies()
        self.tblActionsCure.addPopupRecordProperies()
        self.tblActionsMisc.addPopupRecordProperies()
        self.tblActionsAll.addPopupRecordProperies()
        self.tblSchedules.createPopupMenu([self.actAmbCreateEvent, self.actAmbDeleteOrder, self.actAmbChangeNotes, self.actAmbPrintOrder, self.actAmbHomePrintOrder, self.actJumpQueuePosition, self.actPrintBeforeRecords, self.actShowPreRecordInfo])
        self.tblVisitsBySchedules.createPopupMenu([self.actShowPreRecordInfoVisitBySchedule])
        self.tblCanceledSchedules.createPopupMenu([self.actShowPreRecordInfoCanceledSchedules])
        self.connect(self.tblEvents.horizontalHeader(), SIGNAL('sectionClicked(int)'), self._setEventsOrderByColumn)

        self.connect(self.modelFilterInfection,
                     SIGNAL('itemCheckingChanged()'),
                     self.on_modelFilterInfection_itemCheckingChanged)

        self.connect(self.modelFilterVaccine,
                     SIGNAL('itemCheckingChanged()'),
                     self.on_modelFilterVaccine_itemCheckingChanged)
        self.connect(self.tblActionsStatus.horizontalHeader(), SIGNAL('sectionClicked(int)'), self._setActionsOrderByColumn)
        self.connect(self.tblActionsDiagnostic.horizontalHeader(), SIGNAL('sectionClicked(int)'), self._setActionsOrderByColumn)
        self.connect(self.tblActionsCure.horizontalHeader(), SIGNAL('sectionClicked(int)'), self._setActionsOrderByColumn)
        self.connect(self.tblActionsMisc.horizontalHeader(), SIGNAL('sectionClicked(int)'), self._setActionsOrderByColumn)
        self.connect(self.tblActionsAll.horizontalHeader(), SIGNAL('sectionClicked(int)'), self._setActionsOrderByColumn)
        self.connect(self.tblExpertDirectionsMC.horizontalHeader(), SIGNAL('sectionClicked(int)'), self._setMedicalCommissionActionsOrderByColumn)
        self.connect(self.tblExpertProtocolsMC.horizontalHeader(), SIGNAL('sectionClicked(int)'), self._setMedicalCommissionActionsOrderByColumn)
        self.connect(self.tblExpertMedicalSocialInspection.horizontalHeader(), SIGNAL('sectionClicked(int)'), self._setMedicalCommissionActionsOrderByColumn)
        self.setFocusProxy(self.tabMain)
        self.internal.setFocusProxy(self.tabMain)
        self.tabMain.setFocusProxy(self.tblClients)  # на первый взгляд не нужно, но строка ниже не справляется...
        self.tabRegistry.setFocusProxy(self.tblClients)
        self.tabEvents.setFocusProxy(self.tblEvents)
        self.tabMainCurrentPage = 0
        self.currentClientFromEvent = False
        self.currentClientFromAction = False
        self.currentClientFromExpert = False
        self.sortAscendingList = {}
        self.controlSplitter = self.splitterRegistry
        self.loadDialogPreferences()
        self.cmbFilterAddressCity.setAreaSelectable(True)
        self.cmbFilterAddressCity.setCode(QtGui.qApp.defaultKLADR())
        self.personInfo = CRBModel(self)
        self.personInfo.setTable('vrbPersonWithSpeciality')
        self.connect(QtGui.qApp, SIGNAL('currentClientInfoChanged()'), self.updateCurrentClientInfo)
        self.tabRegistry.addAction(self.actClientIdBarcodeScan)
        self.tabRegistry.addAction(self.actBatchRegLocatCard)
        self.tabRegistry.addAction(self.actStatusObservationClient)
        self.tabRegistry.addAction(self.actaddClients)
        self.tabRegistry.addAction(self.actaClients)
        self.tabRegistry.addAction(self.actSimplifiedClientSearch)
        self.addAction(self.actcacheTemplate)
        self.tblClients.addAction(self.actCreateEvent)
        self.cmbFilterRegionSMO.setAreaSelectable(True)
        self.tabEvents.addAction(self.actEventIdBarcodeScan)
        self.actEventJobTicketIdBarcodeScan.setShortcut('Ctrl+N')
        self.tabEvents.addAction(self.actEventJobTicketIdBarcodeScan)
        self.actEventExternalIdBarcodeScan.setShortcut('Ctrl+L')
        self.tabEvents.addAction(self.actEventExternalIdBarcodeScan)
        self.tblEvents.enableColsHide()
        self.tblEvents.enableColsMove()
        self.tblEventDiagnostics.enableColsHide()
        self.tblEventDiagnostics.enableColsMove()
        self.tblEventActions.enableColsHide()
        self.tblEventActions.enableColsMove()
        self.tblEventVisits.enableColsHide()
        self.tblEventVisits.enableColsMove()
        self.tblEventExportFile.enableColsHide()
        self.tblEventExportFile.enableColsMove()
        # self.setSortable(self.tblEventDiagnostics, lambda: self.updateEventDiagnostics(self.currentEventId()))
        # self.setSortable(self.tblEventActions, lambda: self.updateEventActions(self.currentEventId()))
        # self.setSortable(self.tblEventVisits, lambda: self.updateEventVisits(self.currentEventId()))
        # self.setSortable(self.tblActionsStatus, lambda: self.updateActionsList(self.__actionFilter))
        # self.setSortable(self.tblActionsStatusProperties, lambda: self.tabAmbCardContent.updateAmbCardPropertiesTable(
        #     self.tblActionsStatus.currentIndex(), self.tblActionsStatusProperties))
        # self.setSortable(self.tblActionsDiagnostic, lambda: self.updateActionsList(self.__actionFilter))
        # self.setSortable(self.tblActionsDiagnosticProperties, lambda: self.tabAmbCardContent.updateAmbCardPropertiesTable(
        #     self.tblActionsDiagnostic.currentIndex(), self.tblActionsDiagnosticProperties))
        # self.setSortable(self.tblActionsCure, lambda: self.updateActionsList(self.__actionFilter))
        # self.setSortable(self.tblActionsCureProperties, lambda: self.tabAmbCardContent.updateAmbCardPropertiesTable(
        #     self.tblActionsCure.currentIndex(), self.tblActionsCureProperties))
        #
        # self.setSortable(self.tblActionsMisc, lambda: self.updateActionsList(self.__actionFilter))
        # self.setSortable(self.tblActionsMiscProperties, lambda: self.tabAmbCardContent.updateAmbCardPropertiesTable(
        #     self.tblActionsMisc.currentIndex(), self.tblActionsMiscProperties))
        #
        # self.setSortable(self.tblExpertTempInvalidPeriods,
        #                  lambda: self.updateCurrentTempPeriodTable(self.tblExpertTempInvalid.currentItemId()))
        # self.setSortable(self.tblExpertDisabilityPeriods,
        #                  lambda: self.updateCurrentTempPeriodTable(self.tblExpertDisability.currentItemId()))
        # self.setSortable(self.tblExpertVitalRestrictionPeriods,
        #                  lambda: self.updateCurrentTempPeriodTable(self.tblExpertVitalRestriction.currentItemId()))

        # self.setSortable(self.tblExpertTempInvalidDuplicates,
        #                  lambda: self.updateTempInvalidDublicates(self.tblExpertTempInvalid.currentItemId()))
        # self.setSortable(self.tblExpertDisability, self.setSortEx)
        # self.setSortable(self.tblExpertVitalRestriction, self.setSortEx)
        # self.setSortable(self.tblVisits, lambda: self.updateVisitsList(self.__visitFilter))
        self.tblActionsStatus.enableColsHide()
        self.tblActionsDiagnostic.enableColsHide()
        self.tblActionsCure.enableColsHide()
        self.tblActionsMisc.enableColsHide()
        self.tblActionsStatus.enableColsMove()
        self.tblActionsDiagnostic.enableColsMove()
        self.tblActionsCure.enableColsMove()
        self.tblActionsMisc.enableColsMove()
        self.tblActionsAll.enableColsHide()
        self.tblActionsAll.enableColsMove()
        self.tblVisits.enableColsHide()
        self.tblVisits.enableColsMove()
        self.tblExpertTempInvalid.enableColsHide()
        self.tblExpertTempInvalid.enableColsMove()
        self.tblExpertTempInvalidRelation.enableColsHide()
        self.tblExpertTempInvalidRelation.enableColsMove()
        self.tblExpertTempInvalidPeriods.enableColsHide()
        self.tblExpertTempInvalidPeriods.enableColsMove()
        self.tblExpertTempInvalidDocuments.enableColsHide()
        self.tblExpertTempInvalidDocuments.enableColsMove()
        self.tblExpertTempInvalidDocumentsEx.enableColsHide()
        self.tblExpertTempInvalidDocumentsEx.enableColsMove()
        self.tblExpertTempInvalidDocumentsEx.setSortingEnabled(True)
        self.tblExpertTempInvalidRelationDocumentsEx.enableColsHide()
        self.tblExpertTempInvalidRelationDocumentsEx.enableColsMove()
        self.tblExpertTempInvalidPeriodsDocuments.enableColsHide()
        self.tblExpertTempInvalidPeriodsDocuments.enableColsMove()
        self.tblExpertDisability.enableColsHide()
        self.tblExpertDisability.enableColsMove()
        self.tblExpertDisabilityRelation.enableColsHide()
        self.tblExpertDisabilityRelation.enableColsMove()
        self.tblExpertDisabilityPeriods.enableColsHide()
        self.tblExpertDisabilityPeriods.enableColsMove()
        self.tblExpertDisabilityDocuments.enableColsHide()
        self.tblExpertDisabilityDocuments.enableColsMove()
        self.tblExpertDisabilityDocumentsEx.enableColsHide()
        self.tblExpertDisabilityDocumentsEx.enableColsMove()
        self.tblExpertDisabilityRelationDocumentsEx.enableColsHide()
        self.tblExpertDisabilityRelationDocumentsEx.enableColsMove()
        self.tblExpertDisabilityPeriodsDocuments.enableColsHide()
        self.tblExpertDisabilityPeriodsDocuments.enableColsMove()
        self.tblExpertVitalRestriction.enableColsHide()
        self.tblExpertVitalRestriction.enableColsMove()
        self.tblExpertVitalRestrictionRelation.enableColsHide()
        self.tblExpertVitalRestrictionRelation.enableColsMove()
        self.tblExpertVitalRestrictionPeriods.enableColsHide()
        self.tblExpertVitalRestrictionPeriods.enableColsMove()
        self.tblExpertVitalRestrictionDocuments.enableColsHide()
        self.tblExpertVitalRestrictionDocuments.enableColsMove()
        self.tblExpertVitalRestrictionDocumentsEx.enableColsHide()
        self.tblExpertVitalRestrictionDocumentsEx.enableColsMove()
        self.tblExpertVitalRestrictionRelationDocumentsEx.enableColsHide()
        self.tblExpertVitalRestrictionRelationDocumentsEx.enableColsMove()
        self.tblExpertVitalRestrictionPeriodsDocuments.enableColsHide()
        self.tblExpertVitalRestrictionPeriodsDocuments.enableColsMove()
        self.tblExpertDirectionsMC.enableColsHide()
        self.tblExpertDirectionsMC.enableColsMove()
        self.tblExpertProtocolsMC.enableColsHide()
        self.tblExpertProtocolsMC.enableColsMove()
        self.tblExpertMedicalSocialInspection.enableColsHide()
        self.tblExpertMedicalSocialInspection.enableColsMove()
        self.tblClients.enableColsHide()
        self.tblClients.enableColsMove()
        self.tblSchedules.enableColsHide()
        self.tblSchedules.enableColsMove()
        self.tblVisitsBySchedules.enableColsHide()
        self.tblVisitsBySchedules.enableColsMove()
        self.tblCanceledSchedules.enableColsHide()
        self.tblCanceledSchedules.enableColsMove()
        self.tblExpertTempInvalid.enableColsHide()
        self.tblExpertTempInvalid.enableColsMove()
        self.tblExpertTempInvalidRelation.enableColsHide()
        self.tblExpertTempInvalidRelation.enableColsMove()
        self.tblExpertTempInvalidDocumentsEx.enableColsHide()
        self.tblExpertTempInvalidDocumentsEx.enableColsMove()
        self.tblExpertTempInvalidRelationDocumentsEx.enableColsHide()
        self.tblExpertTempInvalidRelationDocumentsEx.enableColsMove()
        self.tblExpertTempInvalidPeriods.enableColsHide()
        self.tblExpertTempInvalidPeriods.enableColsMove()
        self.tblExpertTempInvalidDocuments.enableColsHide()
        self.tblExpertTempInvalidDocuments.enableColsMove()
        self.tblExpertTempInvalidPeriodsDocuments.enableColsHide()
        self.tblExpertTempInvalidPeriodsDocuments.enableColsMove()
        self.tblExpertDisability.enableColsHide()
        self.tblExpertDisability.enableColsMove()
        self.tblExpertDisabilityRelation.enableColsHide()
        self.tblExpertDisabilityRelation.enableColsMove()
        self.tblExpertDisabilityPeriods.enableColsHide()
        self.tblExpertDisabilityPeriods.enableColsMove()
        self.tblExpertDisabilityDocuments.enableColsHide()
        self.tblExpertDisabilityDocuments.enableColsMove()
        self.tblExpertDisabilityDocumentsEx.enableColsHide()
        self.tblExpertDisabilityDocumentsEx.enableColsMove()
        self.tblExpertDisabilityRelationDocumentsEx.enableColsHide()
        self.tblExpertDisabilityRelationDocumentsEx.enableColsMove()
        self.tblExpertDisabilityPeriodsDocuments.enableColsHide()
        self.tblExpertDisabilityPeriodsDocuments.enableColsMove()
        self.tblExpertVitalRestriction.enableColsHide()
        self.tblExpertVitalRestriction.enableColsMove()
        self.tblExpertVitalRestrictionRelation.enableColsHide()
        self.tblExpertVitalRestrictionRelation.enableColsMove()
        self.tblExpertVitalRestrictionDocuments.enableColsHide()
        self.tblExpertVitalRestrictionDocuments.enableColsMove()
        self.tblExpertVitalRestrictionDocumentsEx.enableColsHide()
        self.tblExpertVitalRestrictionDocumentsEx.enableColsMove()
        self.tblExpertVitalRestrictionRelationDocumentsEx.enableColsHide()
        self.tblExpertVitalRestrictionRelationDocumentsEx.enableColsMove()

        if self.chkFilterSNILS.isChecked():
            tmp = trim(forceString(self.edtFilterSNILS.text()).replace('-','').replace(' ',''))
            self.__filter['SNILS'] = tmp

        self.setUserRights()
        self.isAscendingSchedules = False
        self.isAscendingBySchedules = False
        # считывание идентификационной карты (полиса, УЭК и т.п.)
        self.connect(QtGui.qApp, SIGNAL('identCardReceived(PyQt_PyObject)'), self.onIdentCardReceived)
        # сканирование штрих-кода; КЭР
        self.addBarcodeScanAction('actScanBarcodeTabExpert')
        self.tabExpert.addAction(self.actScanBarcodeTabExpert)
        self.connect(self.actScanBarcodeTabExpert, SIGNAL('triggered()'), self.on_actScanBarcodeTabExpert)
        QObject.connect(self.tblExpertTempInvalid.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.setSort)
        QObject.connect(self.tblExpertTempInvalidRelation.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.setXXXSort)
        QObject.connect(self.tblClients.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.setClientSort)
        QObject.connect(self.tblSchedules.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.setSchedulesSort)
        QObject.connect(self.tblVisitsBySchedules.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.setBySchedulesSort)
        self.loadSortAscendingList()
        self.identCard = None
        self.chkFilterEventContract.setChecked(forceBool(QtGui.qApp.preferences.appPrefs.get('Registry_chkFilterEventContract', False)))
        self.__filterEventContractId = forceRef(QtGui.qApp.preferences.appPrefs.get('Registry_filterEventContractId', None))
        self.edtFilterEventContract.setText(forceString(QtGui.qApp.preferences.appPrefs.get('Registry_edtFilterEventContract', '')))
        self.tblExpertTempInvalidRelation.setVisible(False)
        self.tblExpertDisabilityRelation.setVisible(False)
        self.tblExpertVitalRestrictionRelation.setVisible(False)
        self.tblExpertTempInvalidRelationDocumentsEx.setVisible(False)
        self.tblExpertDisabilityRelationDocumentsEx.setVisible(False)
        self.tblExpertVitalRestrictionRelationDocumentsEx.setVisible(False)
        self.initDocumentsTempInvalidTextEdit()
        # self.loadElementsFromTab(self.tabMain.indexOf(self.tabEvents))
        self.medicalCommissionSelectedRows = []
        self.loadElementsFromTab(self.tabMain.indexOf(self.tabEvents))
        self.tabAmbCardContent.updateAmbCardMonitoring(self.currentClientId())
        self.loadDialogPreferences()
        self.userTabWidgetRights(urRegTabReadEvents, self.tabEvents)  # отображение вкладки "Обращение"
        self.userTabWidgetRights(urRegTabReadAmbCard, self.tabAmbCard)  # отображение вкладки "Мед.карта"
        self.userTabWidgetRights(urRegTabReadActions, self.tabActions)  # отображение вкладки "Обслуживание"
        self.userTabWidgetRights(urRegTabReadExpert, self.tabExpert)  # отображение вкладки "КЭР"
        self.userTabWidgetRights(urRegTabReadVisits, self.tabVisits)  # отображение вкладки "Визиты"
        self.tabMain.setTabVisible(self.tabMyDoctorArea, QtGui.qApp.visibleMyDoctorArea)  # отображение вкладки "Мой участок"
        self.tabMain.setTabVisible(self.tabNotifications, QtGui.qApp.visibleNotifications)  # отображение вкладки "Уведомления"
        self.tabNotifications.setTabWidget(self.tabMain)
# тут переделать наши права на питерскую систему#
#        self.tabWidgetActionsClassesIndex = 0
#
#        self.userTabWidgetActionsClassesRights(urReadActionsStatus)  # отображение вкладки "Обслуживание/Статус"
#        self.userTabWidgetActionsClassesRights(urReadActionsDiagnostic)  # отображение вкладки "Обслуживание/Диагностика"
#        self.userTabWidgetActionsClassesRights(urReadActionsCure)  # отображение вкладки "Обслуживание/Лечение"
#        self.userTabWidgetActionsClassesRights(urReadActionsMisc)  # отображение вкладки "Обслуживание/Мероприятия"

        # Проверка на активность чекбокса "Автоматически показывать вкладку с уведомлениями" в "прочих настройках"
        # и проверка userId на принадлежность к участковым врачам
        checkExternalNotificationAuto = forceBool(QtGui.qApp.preferences.appPrefs.get('externalNotificationAuto', False))
        if checkExternalNotificationAuto:
            db = QtGui.qApp.db
            userIdBool = forceBool(db.getRecordEx('Person_Order', 'id',
                                                  'master_id = {0} AND type = 6 AND ((validToDate IS NULL OR LENGTH(validToDate) = 0) or validToDate > now())'.format(
                                                      QtGui.qApp.userId)))  # Проверяем, является ли пользователь участковым врачом
            if userIdBool:
                tableEN = db.table('ExternalNotification')
                cond = []
                cond.append('ExternalNotification.last_sync_date BETWEEN {0} AND {1}'.format(
                    db.formatDate(self.edtExternalNotificationBegDate.dateTime()),
                    db.formatDate(self.edtExternalNotificationEndDate.dateTime())))
                cntEN = db.getCount(tableEN, where=cond)
                if cntEN:
                    self.tabBeforeRecord.setCurrentIndex(2)  # Делаем активной вкладку "Уведомления"
                    self.chkFilterExternalNotification.setChecked(True)
                    begDateEN = db.formatDate(self.edtExternalNotificationBegDate.dateTime())
                    endDateEN = db.formatDate(self.edtExternalNotificationEndDate.dateTime())
                    self.modelExternalNotification.setDate(begDateEN, endDateEN)
                    _filter = {}
                    _filter['ENbegDate'] = begDateEN
                    _filter['ENendDate'] = endDateEN
                    self.updateClientsList(_filter)  # Отбираем только пациентов с уведомлениями за последние 7 дней

        self.actionsStatusCount = ''
        self.actionsDiagnosticCount = ''
        self.actionsCureCount = ''
        self.actionsMiscCount = ''
        self.tabFilter.setCurrentIndex(1)
        self.tabFilter.setCurrentIndex(0)
        if forceBool(QtGui.qApp.preferences.appPrefs.get('ScanPromobotEnable')):
            self.createScanButton()

        # self.tabMain.setCurrentIndex(tabIndex)


    def createScanButton(self):
        self.addObject('btnScan', QtGui.QPushButton(u'Сканировать', self))
        self.buttonBoxClient.addButton(self.btnScan, QtGui.QDialogButtonBox.ActionRole)
        self.connect(self.btnScan, SIGNAL('clicked()'), self.on_btnScan_clicked)

    
    # Проверка на доступ к отображению вкладок
    def userTabWidgetRights(self, right, tab):
        visible = QtGui.qApp.userHasRight(right)
        self.tabMain.setTabVisible(tab, visible)

    def userTabWidgetActionsClassesRights(self, right):
        if not QtGui.qApp.userHasRight(right):
            self.tabWidgetActionsClasses.removeTab(self.tabWidgetActionsClassesIndex)
        else:
            self.tabWidgetActionsClassesIndex += 1

    def setSortingIndicator(self, tbl, col, asc):
        tbl.setSortingEnabled(True)
        tbl.horizontalHeader().setSortIndicator(col, Qt.AscendingOrder if asc else Qt.DescendingOrder)

    def setSortable(self, tbl, update_function=None):
        def on_click(col):
            hs = tbl.horizontalScrollBar().value()
            model = tbl.model()
            sortingCol = model.headerSortingCol.get(col, False)
            model.headerSortingCol = {}
            model.headerSortingCol[col] = not sortingCol
            if update_function:
                update_function()
            else:
                model.loadData()
            self.setSortingIndicator(tbl, col, not sortingCol)
            tbl.horizontalScrollBar().setValue(hs)
        header = tbl.horizontalHeader()
        header.setClickable(True)
        QObject.connect(header, SIGNAL('sectionClicked(int)'), on_click)


    @pyqtSignature('')
    def on_actSurveillancePlanningClients_triggered(self):
        clientId = self.currentClientId()
        surPlanningShow = CSurveillanceDialog(self, isFake=True)
        surPlanningShow.surveillancePlanningShow(clientId)


    @pyqtSignature('')
    def on_actUpdateF111_triggered(self):
        clientId = self.currentClientId()
        if clientId:
            clientSex, clientAge = getClientSexAge(clientId)
            if clientSex == 2:
                db = QtGui.qApp.db
                tableEvent = db.table('Event')
                tableEventType = db.table('EventType')
                queryTable = tableEvent.innerJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
                cond = [tableEventType['code'].like(u'KBiR%'),
                        tableEvent['execDate'].isNull(),
                        tableEvent['client_id'].eq(clientId),
                        tableEvent['deleted'].eq(0),
                        tableEventType['deleted'].eq(0),
                        ]
                recordEvent = db.getRecordEx(queryTable, [tableEvent['id']], cond, u'Event.id DESC')
                eventId = forceRef(recordEvent.value('id')) if recordEvent else None
                if eventId:
                    actionTypeIdListByKBiR = getActionTypeIdListByFlatCode(u'111/y-20')
                    if actionTypeIdListByKBiR:
                        tableAction = db.table('Action')
                        cond = [tableAction['event_id'].eq(eventId),
                                tableAction['deleted'].eq(0),
                                tableAction['actionType_id'].inlist(actionTypeIdListByKBiR),
                                tableAction['endDate'].isNull()
                                ]
                        record = db.getRecordEx(tableAction, [tableAction['id']], cond, u'Action.begDate')
                        actionId = forceRef(record.value('id')) if record else None
                        if actionId:
                            dialog = CF111EditDialog(self)
                            try:
                                dialog.load(actionId)
                                if dialog.exec_():
                                    pass
                            finally:
                                dialog.deleteLater()
            self.actUpdateF111.setVisible(clientSex == 2)
            if self.actUpdateF111.isVisible():
                self.actUpdateF111.setEnabled(self.setIsUpdateF111Enable(clientId) and clientSex == 2)
    
    @pyqtSignature('')
    def on_actSurveillancePlanningClientsByEvent_triggered(self):
        clientId = self.currentClientId()
        surPlanningShow = CSurveillanceDialog(self, isFake=True)
        surPlanningShow.surveillancePlanningShow(clientId, eventId=self.currentEventId())

    def switchMainTabToSpecifiedTabByIndex(self,  tabIndex=0):
        self.tabMain.setCurrentIndex(tabIndex)


    def loadElementsFromTab(self, tabIndex=0):
        self.switchMainTabToSpecifiedTabByIndex(tabIndex)


    def initFilterExpertExpertiseMC(self):
        itemList = []
        for item in expertiseClass:
            itemList.append(item[0])
        self.cmbFilterExpertExpertiseMC.addItems(itemList)
        self.cmbFilterExpertExpertiseMC.setCurrentIndex(0)
        if not self.chkFilterExpertExpertiseMC.isChecked():
            self.on_cmbFilterExpertExpertiseMC_currentIndexChanged(0)


    def initDocumentsTempInvalidTextEdit(self):
        tempInvalidReasonCache = CRBModelDataCache.getData('rbTempInvalidReason', True, '')
        vrbPersonCache = CRBModelDataCache.getData('vrbPerson', True, '')
        tempInvalidDocumentCache = CRBModelDataCache.getData('rbTempInvalidDocument', True, '')
        tempInvalidBreakCache = CRBModelDataCache.getData('rbTempInvalidBreak', True, '')
        tempInvalidResultCache = CRBModelDataCache.getData('rbTempInvalidResult', True, '')
        tempInvalidRegimeCache = CRBModelDataCache.getData('rbTempInvalidRegime', True, '')
        self.edtExpertDocumentsTempInvalid.setDataCache(tempInvalidReasonCache, vrbPersonCache, tempInvalidDocumentCache, tempInvalidBreakCache, tempInvalidResultCache, tempInvalidRegimeCache)
        self.edtExpertDisabilityDocumentsTempInvalid.setDataCache(tempInvalidReasonCache, vrbPersonCache, tempInvalidDocumentCache, tempInvalidBreakCache, tempInvalidResultCache, tempInvalidRegimeCache)
        self.edtExpertVitalRestrictionDocumentsTempInvalid.setDataCache(tempInvalidReasonCache, vrbPersonCache, tempInvalidDocumentCache, tempInvalidBreakCache, tempInvalidResultCache, tempInvalidRegimeCache)


    @pyqtSignature('')
    def on_actRelationsClient_triggered(self):
        clientId = self.currentClientId()
        if not clientId:
            clientId = self.selectedClientId()
        if clientId:
            self.editRelationsClient(clientId)
        self.focusClients()


    @pyqtSignature('')
    def on_actEventRelationsClient_triggered(self):
        clientId = self.currentClientId()
        if not clientId:
            clientId = self.selectedClientId()
        if clientId:
            self.editRelationsClient(clientId)
        self.focusClients()


    @pyqtSignature('')
    def on_actAmbCardRelationsClient_triggered(self):
        clientId = self.currentClientId()
        if not clientId:
            clientId = self.selectedClientId()
        if clientId:
            self.editRelationsClient(clientId)
        self.focusClients()


    @pyqtSignature('')
    def on_actActionsRelationsClient_triggered(self):
        clientId = self.currentClientId()
        if not clientId:
            clientId = self.selectedClientId()
        if clientId:
            self.editRelationsClient(clientId)
        self.focusClients()


    @pyqtSignature('')
    def on_actExpertRelationsClient_triggered(self):
        clientId = self.currentClientId()
        if not clientId:
            clientId = self.selectedClientId()
        if clientId:
            self.editRelationsClient(clientId)
        self.focusClients()


    @pyqtSignature('')
    def on_actVisitRelationsClient_triggered(self):
        clientId = self.currentClientId()
        if not clientId:
            clientId = self.selectedClientId()
        if clientId:
            self.editRelationsClient(clientId)
        self.focusClients()


    def editRelationsClient(self, clientId):
        dialog = CRelationsClientListDialog(self, clientId)
        try:
            if dialog.exec_():
                clientId = dialog.itemId()
        finally:
            dialog.deleteLater()


    def setSchedulesSort(self, col):
        name = self.modelSchedules.cols()[col].fieldName()
        self.subOrder = name
        header=self.tblSchedules.horizontalHeader()
        header.setSortIndicatorShown(True)
        self.isAscendingSchedules = not self.isAscendingSchedules
        header.setSortIndicator(col, Qt.AscendingOrder if self.isAscendingSchedules else Qt.DescendingOrder)
        self.modelSchedules.sortData(col, self.isAscendingSchedules)


    def setBySchedulesSort(self, col):
        name = self.modelVisitsBySchedules.cols()[col].fieldName()
        self.subOrder = name
        header=self.tblVisitsBySchedules.horizontalHeader()
        header.setSortIndicatorShown(True)
        self.isAscendingBySchedules = not self.isAscendingBySchedules
        header.setSortIndicator(col, Qt.AscendingOrder if self.isAscendingBySchedules else Qt.DescendingOrder)
        self.modelVisitsBySchedules.sortData(col, self.isAscendingBySchedules)


    def setChildElementsVisible(self, chkList, parentChk, value):
        for row in chkList:
            if row[0] == parentChk:
                for childElement in row[1]:
                    childElement.setVisible(value)


    def setSortEx(self):
        table = self.getCurrentExpertTable()
        orderBy = u'TempInvalid.id'
        for key, value in table.model().headerSortingCol.items():
            if value:
                ASC = u'ASC'
            else:
                ASC = u'DESC'
            if key in [4, 5, 7, 8, 9, 10]:
                nameField = table.model().cols()[key].fields()[0]
                orderBy = table.model().table()[str(nameField)].name() + u" " + ASC
            elif key in [6, 11]:
                orderBy = u'rbTempInvalidReason.code %s, rbTempInvalidReason.name' % ASC if key == 6 else u'vrbPerson.code %s, vrbPerson.name' % ASC
            elif key in [0, 1]:
                orderBy = u'Client.lastName %s, Client.firstName, Client.patrName' % ASC if key == 0 else u'Client.birthDate %s' % ASC
            elif key == 2:
                orderBy = u'Client.sex %s' % ASC
            elif key == 3:
                orderBy = u'TempInvalid.insuranceOfficeMark %s' % ASC
            elif key == 12:
                orderBy = u'(select MKB from Diagnosis where id = TempInvalid.diagnosis_id) %s' % ASC
            elif key == 13:
                orderBy = u'(select concat(ti.serial, ti.number) from TempInvalid ti where ti.id = TempInvalid.prev_id) %s' % ASC
            elif key == 14:
                orderBy = u'TempInvalid.state %s' % ASC
            elif key == 15:
                orderBy = u'TempInvalid.duration %s' % ASC
            elif key == 16:
                orderBy = u'''
                (SELECT COUNT(Visit.id)
                FROM TempInvalid ti
                INNER JOIN Event ON ti.client_id = Event.client_id
                INNER JOIN Visit ON Visit.event_id = Event.id
                WHERE ti.id = TempInvalid.id AND Event.deleted = 0 AND Visit.deleted = 0 AND ti.deleted = 0
                AND DATE(Visit.date) >= ti.begDate AND DATE(Visit.date) <= ti.endDate) %s''' % ASC
            elif key == 17:
                orderBy = u'TempInvalid.notes %s' % ASC
            elif key == 18:
                orderBy = u'(select name from rbTempInvalidDocument where id = TempInvalid.doctype_id) %s' % ASC

        self.renewListAndSetTo(self.currentTempInvalidId(), [orderBy])


    def setSort(self, col):
        sortAscendingList = self.getSortAscendingList()
        sortAscending = not sortAscendingList.get(col, True)
        self.setSortAscendingList(col, sortAscending)
        preff = u' ASC' if sortAscending else ' DESC'
        if col in [5, 6, 7, 14, 15, 17, 19, 20, 21, 22, 23]:
            nameField = self.modelExpertTempInvalid.cols()[col].fields()[0]
            table = self.modelExpertTempInvalid.table()
            order = [table[str(nameField)].name() + preff]
        elif col in [4, 8]:
            order = [(u'rbTempInvalidReason.code%s, rbTempInvalidReason.name'%(preff) if col == 4 else u'vrbPerson.code%s, vrbPerson.name'%(preff))]
        elif col in [0, 1]:
            order = [(u'Client.lastName%s, Client.firstName, Client.patrName'%(preff) if col == 0 else u'Client.birthDate%s'%(preff))]
        elif col == 2:
            order = [u'Client.sex%s' % preff]
        elif col == 3:
            order = [u'TempInvalid.insuranceOfficeMark%s' % preff]
        elif col == 9:
            order = [u'(select MKB from Diagnosis where id = TempInvalid.diagnosis_id)%s' % preff]
        elif col == 10:
            order = [u'TempInvalid.state%s' % preff]
        elif col == 11:
            order = [u'TempInvalid.duration%s' % preff]
        elif col == 12:
            order = [u'''
            (SELECT COUNT(Visit.id)
            FROM TempInvalid ti
            INNER JOIN Event ON ti.client_id = Event.client_id
            INNER JOIN Visit ON Visit.event_id = Event.id
            WHERE ti.id = TempInvalid.id AND Event.deleted = 0 AND Visit.deleted = 0 AND ti.deleted = 0
            AND DATE(Visit.date) >= ti.begDate AND DATE(Visit.date) <= ti.endDate)%s''' % preff]
        elif col == 13:
            order = [u'(select name from rbTempInvalidDocument where id = TempInvalid.doctype_id)%s' % preff]
        elif col == 16:
            order = [u'(select name from rbTempInvalidBreak where id = TempInvalid.break_id)%s' % preff]
        elif col == 18:
            order = [u'(select name from rbTempInvalidResult where id = TempInvalid.result_id)%s' % preff]
        elif col == 24:
            order = [u'(select name from rbTempInvalidRegime where id = TempInvalid.disability_id)%s' % preff]

        header = self.tblExpertTempInvalid.horizontalHeader()
        header.setSortIndicatorShown(True)
        header.setSortIndicator(col, Qt.AscendingOrder if sortAscending else Qt.DescendingOrder)
        self.renewListAndSetTo(self.currentTempInvalidId(), order)


    def renewListAndSetTo(self, itemId=None, order=[]):
        self.updateTempInvalidList(self.__expertFilter, itemId, order)


    def setSortAscendingList(self, col, check):
        self.sortAscendingList[col] = check


    # def on_scannedReceived(self, data):
    #     if self.focusWidget() == QtGui.qApp.focusWidget():
    #         d = bytes(data)
    #         ok, policySerialAndNumber, lastName, firstName, patrName, sex, birthDate = parsePolicyBarCode(self, d)
    #         if ok:
    #             self.tabMain.setCurrentIndex(0)
    #             self.on_buttonBoxClient_reset()
    #             self.chkFilterLastName.setChecked(True)
    #             self.edtFilterLastName.setText(lastName)
    #             self.chkFilterFirstName.setChecked(True)
    #             self.edtFilterFirstName.setText(firstName)
    #             self.chkFilterPatrName.setChecked(True)
    #             self.edtFilterPatrName.setText(patrName)
    #             self.chkFilterBirthDay.setChecked(True)
    #             self.edtFilterBirthDay.setDate(birthDate)
    #             self.chkFilterSex.setChecked(True)
    #             self.cmbFilterSex.setCurrentIndex(sex)


    def onIdentCardReceived(self, identCard):
        if self.focusWidget() == QtGui.qApp.focusWidget():
            self.tabMain.setCurrentIndex(0)
            self.on_buttonBoxClient_reset()
            if identCard.lastName:
                self.chkFilterLastName.setChecked(True)
                self.edtFilterLastName.setText(identCard.lastName)
            if identCard.firstName:
                self.chkFilterFirstName.setChecked(True)
                self.edtFilterFirstName.setText(identCard.firstName)
            if identCard.patrName:
                self.chkFilterPatrName.setChecked(True)
                self.edtFilterPatrName.setText(identCard.patrName)
            if identCard.birthDate:
                self.chkFilterBirthDay.setChecked(True)
                self.edtFilterBirthDay.setDate(identCard.birthDate)
            if identCard.sex:
                self.chkFilterSex.setChecked(True)
                self.cmbFilterSex.setCurrentIndex(identCard.sex)

            if identCard.policy and identCard.policy.number:
                self.chkFilterPolicyOnlyActual.setChecked(False)
                self.edtFilterPolicyActualData.setDate(QDate())
                self.edtFilterPolicySerial.setText(identCard.policy.serial)
                self.edtFilterPolicyNumber.setText(identCard.policy.number)
                #self.cmbFilterPolicyInsurer.setValue(insurerId)
                self.cmbFilterPolicyInsurer.setValue(None)
                if not self.cmbFilterPolicyType.hasTable():
                    self.cmbFilterPolicyType.setTable('rbPolicyType', True, specialValues=((-1, u'ОМС', u'ОМС'),))
                self.cmbFilterPolicyType.setCode(u'ОМС') # ОМС
                if not self.cmbFilterPolicyKind.hasTable():
                    self.cmbFilterPolicyKind.setTable('rbPolicyKind', True)
                self.cmbFilterPolicyKind.setCode('4')
                self.chkFilterPolicy.setChecked(False)
            self.identCard = identCard
            self.on_buttonBoxClient_apply()


    def on_actScanBarcodeTabExpert(self):
        self.cmbFilterExpert.setCurrentIndex(2)
        chkWidgetList = [
#                        self.chkFilterExpertDocType,
                        self.chkPrimaryOrDuble,
                        self.chkFilterTempInvalidDocType,
                        self.chkFilterExpertSerial,
#                        self.chkFilterExpertNumber,
                        self.chkFilterExpertReason,
                        self.chkFilterExpertResult,
                        self.chkFilterExpertBegDate,
                        self.chkFilterExpertEndDate,
                        self.chkFilterExpertOrgStruct,
                        self.chkFilterExpertSpeciality,
                        self.chkFilterExpertPerson,
                        self.chkFilterExpertMKB,
                        self.chkFilterExpertState,
                        self.chkFilterExpertDuration,
                        self.chkFilterExpertInsuranceOfficeMark,
                        self.chkFilterExpertExportFSS,
                        self.chkFilterExpertLinked,
                        self.chkFilterDirectDateOnMC,
                        self.chkFilterExpertExternal,
                        self.chkDateKAK,
                        self.chkExpertIdKAK,
                        self.chkFilterExpertCreatePerson,
                        self.chkFilterExpertCreateDate,
                        self.chkFilterExpertModifyPerson,
                        self.chkFilterExpertModifyDate,
                        ]
        for chkWidget in chkWidgetList:
            chkWidget.setChecked(False)
        self.chkFilterExpertNumber.setChecked(True)


    def setUserRights(self):
        u"""Права доступа по вкладкам"""
        app = QtGui.qApp
        isAdmin = app.userHasRight(urAdmin)
        # чтение
        self.tabMain.setTabEnabled(0, isAdmin or app.userHasRight(urRegTabReadRegistry) or app.userHasRight(urRegTabWriteRegistry)) #Картотека
        self.tabMain.setTabEnabled(1, isAdmin or app.userHasRight(urRegTabReadEvents))  #Обращения
        self.tabMain.setTabEnabled(2, isAdmin or app.userHasRight(urRegTabReadAmbCard)) #Медкарта
        self.tabMain.setTabEnabled(3, isAdmin or app.userHasRight(urRegTabReadActions)) #Обслуживание
        self.tabMain.setTabEnabled(4, isAdmin or app.userHasRight(urRegTabReadExpert))  #КЭР
        self.tabMain.setTabEnabled(5, isAdmin or app.userHasRight(urRegTabReadVisits))  #Визиты
        # Запись\изменение
        # Вкладка Картотека: кнопки Редактировать и Регистрация
        self.btnEdit.setEnabled(isAdmin or app.userHasRight(urRegTabWriteRegistry))
        self.btnNew.setEnabled(isAdmin or app.userHasRight(urRegTabNewWriteRegistry))
        # Вкладка Обращение: кнопки Редактировать и Новый
        self.btnEventEdit.setEnabled(isAdmin or app.userHasRight(urRegTabWriteEvents))
        self.btnEventNew.setEnabled(isAdmin or app.userHasRight( urRegTabWriteEvents))
        # Вкладка Мед. Карта
        #   зарезервировано право urRegTabWriteAmbCard
        # Вкладка Обслуживание: кнопка Редактировать событие (обращение)
        self.btnActionEventEdit.setEnabled(isAdmin or app.userHasRight(urRegTabWriteEvents))
        # Вкладка Обслуживание: элемент контекстного меню
        self.actEditActionEvent.setEnabled(isAdmin or app.userHasRight(urRegTabWriteActions))
        # Вкладка Обслуживание: кнопка Редактировать
        self.btnActionEdit.setEnabled(isAdmin or app.userHasRight(urRegTabWriteActions))
        # Вкладка КЭР
        #   зарезервировано право urRegTabWriteExpert
        self.setBtnExpertEditEnabled()
        self.actExpertTempInvalidDelete.setEnabled(getRightEditTempInvalid(self.tblExpertTempInvalid.currentItemId()))
        self.actExpertDisabilityDelete.setEnabled(getRightEditTempInvalid(self.tblExpertDisability.currentItemId()))
        self.actExpertVitalRestrictionDelete.setEnabled(getRightEditTempInvalid(self.tblExpertVitalRestriction.currentItemId()))
        self.tabWidgetTempInvalidTypes.setTabEnabled(self.tabWidgetTempInvalidTypes.indexOf(self.tabExpertMedicalCommission), QtGui.qApp.userHasRight(urRegTabEditExpertMC))
        # Вкладка Визиты: кнопка Редактировать
        self.btnVisitEdit.setEnabled(isAdmin or app.userHasRight(urRegTabWriteVisits))
        self.actEditVisitEvent.setEnabled(isAdmin or app.userHasRight(urRegTabWriteVisits))
        # Вкладка  СМП
        #   зарезервировано право urRegTabWriteAmbulance
        # заполнение combobox-ов тип прикрепления
        self.setupCmbFilterAttachTypeCategory(0)
        # Оповещения
        self.actNotify.setEnabled(isAdmin or app.userHasRight(urSendInternalNotifications))
        # перенести в exec_
        self.updateClientsList(self.__filter)


    def setBtnExpertEditEnabled(self):
        tableList = [self.tblExpertTempInvalid, self.tblExpertDisability, self.tblExpertVitalRestriction, self.getCurrentExpertMedicalCommissionTable()]
        btnDeleteList = [self.actExpertTempInvalidDelete, self.actExpertDisabilityDelete, self.actExpertVitalRestrictionDelete, None]
        if self.tabWidgetTempInvalidTypes.currentIndex() != 1:
            active = getRightEditTempInvalid(tableList[self.tabWidgetTempInvalidTypes.currentIndex()].currentItemId())
            self.btnExpertEdit.setEnabled(active)
            if btnDeleteList[self.tabWidgetTempInvalidTypes.currentIndex()]:
                btnDeleteList[self.tabWidgetTempInvalidTypes.currentIndex()].setEnabled(active)
        else:
            active = forceBool(tableList[self.tabWidgetTempInvalidTypes.currentIndex()].currentItemId())
            self.btnExpertEdit.setEnabled(active)
            btnDeleteList[self.tabWidgetTempInvalidTypes.currentIndex()].setEnabled(active)


    def setupCmbFilterAttachTypeCategory(self, category, filterDict=None):
        if filterDict is None:
            filterDict = {1: 'temporary=0',
                          2: 'temporary',
                          3: 'outcome'}
        v = self.cmbFilterAttachType.value()
        self.cmbFilterAttachType.setFilter(filterDict.get(category, ''))
        if v:
            self.cmbFilterAttachType.setValue(v)


    def closeEvent(self, event):
        self.saveDialogPreferences()
        QtGui.qApp.preferences.appPrefs['FilterAccountingSystem'] = toVariant(self.cmbFilterAccountingSystem.value())
        QtGui.qApp.preferences.appPrefs['FilterAccountingSystemClient'] = toVariant(self.cmbFilterIdentification.value())
        QtGui.qApp.preferences.appPrefs['Registry_chkFilterEventContract'] = toVariant(self.chkFilterEventContract.isChecked())
        QtGui.qApp.preferences.appPrefs['Registry_filterEventContractId'] = toVariant(self._CRegistryWindow__filterEventContractId)
        QtGui.qApp.preferences.appPrefs['Registry_edtFilterEventContract'] = toVariant(self.edtFilterEventContract.text())
        QtGui.qApp.preferences.appPrefs['Registry_filterEventContractParams_financeId'] = toVariant(self.filterEventContractParams.get('financeId', None))
        QtGui.qApp.preferences.appPrefs['Registry_filterEventContractParams_groupingIndex'] = toVariant(self.filterEventContractParams.get('groupingIndex', 0))
        QtGui.qApp.preferences.appPrefs['Registry_filterEventContractParams_grouping'] = toVariant(self.filterEventContractParams.get('grouping', u''))
        QtGui.qApp.preferences.appPrefs['Registry_filterEventContractParams_resolutionIndex'] = toVariant(self.filterEventContractParams.get('resolutionIndex', 0))
        QtGui.qApp.preferences.appPrefs['Registry_filterEventContractParams_resolution'] = toVariant(self.filterEventContractParams.get('resolution', u''))
        QtGui.qApp.preferences.appPrefs['Registry_filterEventContractParams_priceList'] = toVariant(self.filterEventContractParams.get('priceList', 0))
        currentDate = QDate.currentDate()
        QtGui.qApp.preferences.appPrefs['Registry_filterEventContractParams_edtBegDate'] = toVariant(self.filterEventContractParams.get('edtBegDate', QDate(currentDate.year(), 1, 1)))
        QtGui.qApp.preferences.appPrefs['Registry_filterEventContractParams_edtEndDate'] = toVariant(self.filterEventContractParams.get('edtEndDate', QDate(currentDate.year(), 12, 31)))
        QtGui.qApp.preferences.appPrefs['Registry_filterEventContractParams_enableInAccounts'] = toVariant(self.filterEventContractParams.get('enableInAccounts', 0))
        QtGui.qApp.mainWindow.registry = None
        QtGui.QWidget.closeEvent(self, event)


    def syncSplitters(self, nextSplitter):
        if nextSplitter != self.controlSplitter:
            nextSplitter.setSizes(self.controlSplitter.sizes())
            self.controlSplitter = nextSplitter


    def focusClients(self):
        self.tblClients.setFocus(Qt.TabFocusReason)


    def focusEvents(self):
        self.tblEvents.setFocus(Qt.TabFocusReason)


    def showAccountingDialog(self, eventId=None, actionId=None, visitId=None):
        QtGui.qApp.setWaitCursor()
        dlg = CAccountingDialog(self)
        dlg.setWatchingFields(eventId, actionId, visitId)
        QtGui.qApp.restoreOverrideCursor()
        dlg.exec_()


    @pyqtSignature('int')
    def on_cmbFilterContingentType_currentIndexChanged(self, index):
        contingentTypeId = self.cmbFilterContingentType.value()
        if contingentTypeId:
            eventRecordList = CContingentTypeTranslator.getCondRecordList(CContingentTypeTranslator.CTETTName, contingentTypeId)
            actionRecordList = CContingentTypeTranslator.getCondRecordList(CContingentTypeTranslator.CTATTName, contingentTypeId)
            specialityRecordList = CContingentTypeTranslator.getCondRecordList(CContingentTypeTranslator.CTCKTName, contingentTypeId)
            self.cmbFilterContingentEventTypeStatus.setEnabled(bool(eventRecordList))
            self.cmbFilterContingentActionType.setEnabled(bool(actionRecordList))


    def getLeavedHospitalBeds(self, orgStructureIdList):
        currentDate = QDate.currentDate()
        db = QtGui.qApp.db
        tableAPHB = db.table('ActionProperty_HospitalBed')
        tableAPT = db.table('ActionPropertyType')
        tableAP = db.table('ActionProperty')
        tableActionType = db.table('ActionType')
        tableAction = db.table('Action')
        tableEvent = db.table('Event')
        tableOSHB = db.table('OrgStructure_HospitalBed')
        tableOS = db.table('OrgStructure')
        tableClient = db.table('Client')
        orgStructureBedsIdList = db.getDistinctIdList(tableOSHB, [tableOSHB['master_id']], [tableOSHB['master_id'].inlist(orgStructureIdList)])
        clientIdList = []
        if orgStructureBedsIdList:
            queryTable = tableActionType.innerJoin(tableAction, tableActionType['id'].eq(tableAction['actionType_id']))
            queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
            cond = [ tableActionType['flatCode'].like('leaved%'),
                     tableAction['deleted'].eq(0),
                     tableEvent['deleted'].eq(0),
                     tableActionType['deleted'].eq(0),
                     tableClient['deleted'].eq(0),
                     tableEvent['setDate'].le(currentDate),
                     tableAction['begDate'].le(currentDate),
                     tableAction['endDate'].isNull()
                   ]
            stmt = db.selectStmt(queryTable, [tableEvent['id'].alias('eventId'), tableAction['id'].alias('actionId')], cond)
            query = db.query(stmt)
            queryTable = queryTable.innerJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
            queryTable = queryTable.innerJoin(tableAP, tableAP['type_id'].eq(tableAPT['id']))
            queryTable = queryTable.innerJoin(tableAPHB, tableAPHB['id'].eq(tableAP['id']))
            queryTable = queryTable.innerJoin(tableOSHB, tableOSHB['id'].eq(tableAPHB['value']))
            queryTable = queryTable.innerJoin(tableOS, tableOS['id'].eq(tableOSHB['master_id']))
            while query.next():
                record = query.record()
                eventId = forceRef(record.value('eventId'))
                cond = [ tableActionType['flatCode'].like('moving%'),
                         tableAction['deleted'].eq(0),
                         tableEvent['deleted'].eq(0),
                         tableEvent['id'].eq(eventId),
                         tableAP['deleted'].eq(0),
                         tableActionType['deleted'].eq(0),
                         tableAPT['deleted'].eq(0),
                         tableOS['deleted'].eq(0),
                         tableClient['deleted'].eq(0),
                         tableEvent['setDate'].le(currentDate),
                         tableAction['begDate'].le(currentDate),
                         tableAPT['typeName'].like('HospitalBed'),
                         tableAP['action_id'].eq(tableAction['id'])
                       ]
                order = u'Action.begDate DESC'
                cols = [tableClient['id']]
                strListId = ' IN ('+(','.join(str(orgId) for orgId in orgStructureBedsIdList))+')'
                cols.append(u'IF(OrgStructure.id%s, 1, 0) AS boolOrgStructure'%(strListId))
                firstRecord = db.getRecordEx(queryTable, cols, cond, order)
                if firstRecord:
                    if forceBool(firstRecord.value('boolOrgStructure')):
                        clientIdList.append(forceInt(firstRecord.value('id')))
        return clientIdList


    def getHospitalBeds(self, orgStructureIdList, indexFlatCode = 0):
        flatCode = [u'', u'moving', u'leaved', u'planning']
        currentDate = QDate.currentDate()
        db = QtGui.qApp.db
        tableAPHB = db.table('ActionProperty_HospitalBed')
        tableAPT = db.table('ActionPropertyType')
        tableAP = db.table('ActionProperty')
        tableActionType = db.table('ActionType')
        tableAction = db.table('Action')
        tableEvent = db.table('Event')
        tableOSHB = db.table('OrgStructure_HospitalBed')
        tableOS = db.table('OrgStructure')
        tableClient = db.table('Client')
        orgStructureBedsIdList = db.getDistinctIdList(tableOSHB, [tableOSHB['master_id']], [tableOSHB['master_id'].inlist(orgStructureIdList)])
        if orgStructureBedsIdList:
            queryTable = tableActionType.innerJoin(tableAction, tableActionType['id'].eq(tableAction['actionType_id']))
            queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
            queryTable = queryTable.innerJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
            queryTable = queryTable.innerJoin(tableAP, tableAP['type_id'].eq(tableAPT['id']))
            queryTable = queryTable.innerJoin(tableAPHB, tableAPHB['id'].eq(tableAP['id']))
            queryTable = queryTable.innerJoin(tableOSHB, tableOSHB['id'].eq(tableAPHB['value']))
            queryTable = queryTable.innerJoin(tableOS, tableOS['id'].eq(tableOSHB['master_id']))
            cond = [ tableClient['deleted'].eq(0),
                     tableEvent['deleted'].eq(0),
                     tableAction['deleted'].eq(0),
                     tableAP['deleted'].eq(0),
                     tableActionType['deleted'].eq(0),
                     tableOS['deleted'].eq(0),
                     tableOS['id'].inlist(orgStructureBedsIdList),
                     tableEvent['setDate'].le(currentDate),
                     tableAction['begDate'].le(currentDate),
                     tableAPT['typeName'].like('HospitalBed'),
                     tableAP['action_id'].eq(tableAction['id'])
                   ]
            cond.append(db.joinOr([tableEvent['execDate'].isNull(), tableEvent['execDate'].ge(currentDate)]))
            cond.append(db.joinOr([tableAction['endDate'].isNull(), tableAction['endDate'].ge(currentDate)]))
            if indexFlatCode == 1 or indexFlatCode == 3:
                cond.append(tableActionType['flatCode'].like(flatCode[indexFlatCode]))
            else:
                cond.append(db.joinOr([tableActionType['flatCode'].like('moving'), tableActionType['flatCode'].like('planning')]))
            return db.getDistinctIdList(queryTable, [tableClient['id']], cond)
        else:
            return None


    def update(self):
        self.updateClientsList(self.__filter, self.currentClientId())
        # super(CRegistryWindow, self).update()


    def updateClientsList(self, filter, posToId=None):
        """
            в соответствии с фильтром обновляет список пациентов.
        """
        db = QtGui.qApp.db

        isEventJoined = False
        isSocStatusJoined = False

        def calcBirthDate(cnt, unit):
            result = QDate().currentDate()
            if unit == 3:  # дни
                result = result.addDays(-cnt)
            elif unit == 2:  # недели
                result = result.addDays(-cnt*7)
            elif unit == 1:  # месяцы
                result = result.addMonths(-cnt)
            else:  # года
                result = result.addYears(-cnt)
            return result

        def addAddressCond(cond, addrType, addrIdList):
            tableClientAddress = db.table('ClientAddress')
            subcond = [tableClientAddress['client_id'].eqEx('`Client`.`id`'),
                       tableClientAddress['id'].eqEx(u'getClientLocAddressId(Client.id)' if addrType else u'getClientRegAddressId(Client.id)')
                       ]
            if addrIdList is None:
                subcond.append(tableClientAddress['address_id'].isNull())
                subcondNoCAId = u'(SELECT %s IS NULL)'%(u'getClientLocAddressId(Client.id)' if addrType else u'getClientRegAddressId(Client.id)')
                cond.append(db.joinOr([db.existsStmt(tableClientAddress, subcond), subcondNoCAId]))
            else:
                subcond.append(tableClientAddress['address_id'].inlist(addrIdList))
                cond.append(db.existsStmt(tableClientAddress, subcond))

        def addExcludeLeavedCond(cond):
            db = QtGui.qApp.db
            tableCA = db.table('ClientAttach').alias('CA')
            tableCA2 = db.table('ClientAttach').alias('CA2')
            tableRBAT = db.table('rbAttachType').alias('rbAT')
            table = tableCA.leftJoin(tableRBAT, tableRBAT['id'].eq(tableCA['attachType_id']))

            localCond = [tableCA['client_id'].eqEx('Client.id'),
                         tableRBAT['outcome'].eq(1),
                         tableCA['deleted'].eq(0),
                         tableCA['id'].eqEx('(%s)' % db.selectStmt(tableCA2,
                                                                   'MAX(%s)' % tableCA2['id'].name(),
                                                                   [tableCA2['client_id'].eqEx('Client.id')]))]

            cond.append(db.notExistsStmt(table, localCond))

        def addAttachCond(cond, orgCond, attachCategory, attachTypeId, attachBegDate=QDate(), attachEndDate=QDate(), isStatement=0, isNotAttachOrganisation=False):
            outerCond = []
            innerCond = ['CA2.client_id = Client.id']
            noEndAttach = ''
            if isStatement:
                outerCond.append('ClientAttach.isStatement = %d' % (isStatement-1))
            if attachBegDate and attachEndDate:
                outerCond.append(db.joinOr([db.joinAnd(['DATE(ClientAttach.begDate) IS NULL',
                                                        'DATE(ClientAttach.endDate) IS NULL'
                                                        ]),

                                            db.joinAnd(['DATE(ClientAttach.begDate) IS NULL',
                                                        'DATE(ClientAttach.endDate) >= DATE(%s)' % (db.formatDate(attachBegDate))
                                                        ]),

                                            db.joinAnd(['DATE(ClientAttach.endDate) IS NULL',
                                                        'DATE(ClientAttach.begDate) < DATE(%s)' % (db.formatDate(attachEndDate))
                                                        ]),

                                            db.joinAnd(['DATE(ClientAttach.begDate) IS NOT NULL',
                                                        'DATE(ClientAttach.begDate) < DATE(%s)' % (db.formatDate(attachEndDate)),
                                            db.joinAnd(['DATE(ClientAttach.endDate) IS NOT NULL',
                                                        'DATE(ClientAttach.endDate) >= DATE(%s)' % (db.formatDate(attachBegDate))
                                                        ])
                                                        ])
                                            ])
                                )
            elif attachBegDate:
                outerCond.append(db.joinOr([db.joinAnd(['DATE(ClientAttach.begDate) IS NULL',
                                                        'DATE(ClientAttach.endDate) IS NULL'
                                                        ]),
                                            db.joinAnd(['DATE(ClientAttach.begDate) IS NOT NULL',
                                                        'DATE(ClientAttach.begDate) >= DATE(%s)' % (db.formatDate(attachBegDate))
                                                        ])
                                            ])
                                )
            elif attachEndDate:
                outerCond.append(db.joinOr([db.joinAnd(['DATE(ClientAttach.begDate) IS NULL',
                                                        'DATE(ClientAttach.endDate) IS NULL'
                                                        ]),
                                            db.joinAnd(['DATE(ClientAttach.endDate) IS NOT NULL',
                                                        'DATE(ClientAttach.endDate) < DATE(%s)' % (db.formatDate(attachEndDate))
                                                        ])
                                            ])
                                )
                outerCond.append('DATE(ClientAttach.begDate) >= DATE(%s)' % (db.formatDate(attachBegDate)))
                outerCond.append('DATE(ClientAttach.begDate) < DATE(%s)' % (db.formatDate(attachEndDate)))
            if orgCond:
                outerCond.append(orgCond)
            if attachTypeId:
                outerCond.append('attachType_id=%d' % attachTypeId)
                innerCond.append('CA2.attachType_id=%d' % attachTypeId)
            else:
                if attachCategory == 1:
                    innerCond.append('rbAttachType2.temporary=0')
                    noEndAttach = ''' AND (ClientAttach.endDate > NOW() or ClientAttach.endDate IS NULL )'''
                elif attachCategory == 2:
                    innerCond.append('rbAttachType2.temporary')
                elif attachCategory == 3:
                    innerCond.append('rbAttachType2.outcome')
                elif attachCategory == 0:
                    outerCond.append('rbAttachType.outcome=0')
                    innerCond.append('rbAttachType2.temporary=0')
            stmt = '''{0} EXISTS (SELECT ClientAttach.id
               FROM ClientAttach
               LEFT JOIN rbAttachType ON rbAttachType.id = ClientAttach.attachType_id
               WHERE ClientAttach.deleted=0
               AND %s
               %s
               AND ClientAttach.id = (SELECT MAX(CA2.id)
                           FROM ClientAttach AS CA2
                           LEFT JOIN rbAttachType AS rbAttachType2 ON rbAttachType2.id = CA2.attachType_id
                           WHERE CA2.deleted=0 AND %s))'''.format('NOT ' if isNotAttachOrganisation else '')
            cond.append(stmt % (db.joinAnd(outerCond),noEndAttach, db.joinAnd(innerCond)))

        try:
            QtGui.QApplication.setOverrideCursor(QtGui.QCursor(Qt.WaitCursor))
            self.__filter = filter
            tableClient = db.table('Client')
            table = tableClient
            cond = [tableClient['deleted'].eq(0)]
            if self.chkFilterExternalNotification.isChecked():
                conditionEN = []
                conditionEN.append('(last_sync_date BETWEEN {0} AND {1})'.format(filter['ENbegDate'], filter['ENendDate']))

                # Проверка пользователя на принадлежность к участковым врачам
                if forceBool(QtGui.qApp.preferences.appPrefs.get('externalNotificationOnlyAttach', False)):
                    tablePO = db.table('Person_Order')
                    tableEN = db.table('ExternalNotification')
                    column = tablePO['orgStructure_id']
                    condition = ['deleted = 0 and master_id = {0} AND type = 6 AND ((validToDate IS NULL OR LENGTH(validToDate) = 0) or validToDate > now())'.format(QtGui.qApp.userId)]
                    orgStructList = []
                    recordOrgStructure = db.getRecordList(tablePO, column, condition)
                    if recordOrgStructure:
                        for rec in recordOrgStructure:
                            orgStructList.append(forceInt(rec.value('orgStructure_id')))
                    conditionEN.append(tableEN['orgStructure_id'].inlist(orgStructList))

                # Фильтруем пациентов, имеющих уведомления за указанный период
                recClientId = db.getRecordList('ExternalNotification', 'client_id', conditionEN)
                recordClientIdList = []
                for rec in recClientId:
                    recordClientIdList.append(forceInt(rec.value('client_id')))
                cond.append(tableClient['id'].inlist(recordClientIdList))
            elif 'id' in filter:
                accountingSystemId = filter.get('accountingSystemId',  None)
                if accountingSystemId:
                    tableIdentification = db.table('ClientIdentification')
                    table = table.leftJoin(tableIdentification, tableIdentification['client_id'].eq(tableClient['id']))
                    cond.append(tableIdentification['accountingSystem_id'].eq(accountingSystemId))
                    cond.append(tableIdentification['identifier'].eq(filter['id']))
                    cond.append(tableIdentification['deleted'].eq(0))
                else:
                    cond.append(tableClient['id'].eq(filter['id']))
            addCondLike(cond, tableClient['lastName'],  addDots(filter.get('lastName', '')))
            addCondLike(cond, tableClient['firstName'], addDots(filter.get('firstName', '')))
            addCondLike(cond, tableClient['patrName'],  addDots(filter.get('patrName', '')))
            oldLastName = forceStringEx(filter.get('oldLastName', ''))
            oldFirstName = forceStringEx(filter.get('oldFirstName', ''))
            oldPatrName = forceStringEx(filter.get('oldPatrName', ''))
            if oldLastName or oldFirstName or oldPatrName:
                tableClientHistory = db.table('Client_History')
                table = table.innerJoin(tableClientHistory, tableClientHistory['master_id'].eq(tableClient['id']))
                cond.append(tableClientHistory['deleted'].eq(0))
                if oldLastName:
                    addCondLike(cond, tableClientHistory['lastName'], addDots(filter.get('oldLastName', '')))
                if oldFirstName:
                    addCondLike(cond, tableClientHistory['firstName'], addDots(filter.get('oldFirstName', '')))
                if oldPatrName:
                    addCondLike(cond, tableClientHistory['patrName'], addDots(filter.get('oldPatrName', '')))
            if 'birthDate' in filter:
                birthDate = filter['birthDate']
                if not birthDate:
                    birthDate = None
                if 'endBirthDate' in filter:
                    endBirthDate = filter['endBirthDate']
                    if not endBirthDate:
                        endBirthDate = None
                    cond.append(tableClient['birthDate'].ge(birthDate))
                    cond.append(tableClient['birthDate'].le(endBirthDate))
                else:
                    cond.append(tableClient['birthDate'].eq(birthDate))
            if 'dead' in filter:
                cond.append(tableClient['deathDate'].isNotNull())
                if 'begDeathDate' in filter:
                    begDeathDate = filter['begDeathDate']
                    if begDeathDate:
                        cond.append(tableClient['deathDate'].ge(begDeathDate))
                if 'endDeathDate' in filter:
                    endDeathDate = filter['endDeathDate']
                    if endDeathDate:
                        cond.append(tableClient['deathDate'].le(endDeathDate))
            self.addEqCond(cond, tableClient, 'createPerson_id', filter, 'createPersonIdEx')
            self.addDateCond(cond, tableClient, 'createDatetime', filter, 'begCreateDateEx', 'endCreateDateEx')
            self.addEqCond(cond, tableClient, 'modifyPerson_id', filter, 'modifyPersonIdEx')
            self.addDateCond(cond, tableClient, 'modifyDatetime', filter, 'begModifyDateEx', 'endModifyDateEx')
            event = filter.get('event', None)
            eventOpen = filter.get('eventOpen', None)
            if event or eventOpen:
                isEventJoined = True
                tableEvent = db.table('Event')
                tableEventType = db.table('EventType')
                tableEventTypePurpose = db.table('rbEventTypePurpose')
                table = table.innerJoin(tableEvent, tableEvent['client_id'].eq(tableClient['id']))
                table = table.innerJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
                table = table.innerJoin(tableEventTypePurpose, tableEventTypePurpose['id'].eq(tableEventType['purpose_id']))
                cond.append(tableEventTypePurpose['code'].notlike('0'))
                if event:
                    firstEvent, begDate, endDate = event
                    if begDate or endDate:
                        cond.append(tableEvent['setDate'].isNotNull())
                        cond.append(tableEvent['deleted'].eq(0))
                    if begDate:
                        cond.append(tableEvent['setDate'].dateGe(begDate))
                    if endDate:
                        cond.append(tableEvent['setDate'].dateLe(endDate))
                    if firstEvent and begDate:
                        cond.append('''NOT EXISTS(SELECT E.id FROM Event AS E WHERE E.client_id = Client.id AND Event.deleted = 0 AND DATE(E.setDate) < DATE(%s))'''%(db.formatDate(begDate)))
                else:
                    begDate, endDate = eventOpen
                    if begDate and endDate:
                        cond.append(db.notExistsStmt(tableEvent, db.joinAnd([tableEvent['execDate'].dateGe(begDate),tableEvent['execDate'].dateLe(endDate),tableEvent['deleted'].eq(0),tableEvent['client_id'].eq(tableClient['id'])])))
                    elif begDate:
                        cond.append(db.notExistsStmt(tableEvent, db.joinAnd([tableEvent['execDate'].dateGe(begDate),tableEvent['deleted'].eq(0),tableEvent['client_id'].eq(tableClient['id'])])))
                    elif endDate:
                        cond.append(db.notExistsStmt(tableEvent, db.joinAnd([tableEvent['execDate'].dateLe(endDate),tableEvent['deleted'].eq(0),tableEvent['client_id'].eq(tableClient['id'])])))
                    else:
                        cond.append(db.notExistsStmt(tableEvent, db.joinAnd([tableEvent['execDate'].isNotNull(),tableEvent['deleted'].eq(0),tableEvent['client_id'].eq(tableClient['id'])])))
            if 'age' in filter:
                lowAge, highAge = filter['age']
                cond.append(tableClient['birthDate'].le(calcBirthDate(*lowAge)))
                cond.append(tableClient['birthDate'].ge(calcBirthDate(*highAge)))
            if 'sex' in filter:
                cond.append(tableClient['sex'].eq(filter['sex']))
            if 'SNILS' in filter:
                cond.append(tableClient['SNILS'].eq(filter['SNILS']))
            if 'contact' in filter:
                tableContact = db.table('ClientContact')
                table = table.leftJoin(tableContact, tableContact['client_id'].eq(tableClient['id']))
                cond.append(tableContact['deleted'].eq(0))
                rep1 = replaceMask('ClientContact.contact', '\'(\'', '\'\'')
                rep2 = replaceMask(rep1, '\')\'', '\'\'')
                rep3 = replaceMask(rep2, '\'+\'', '\'\'')
                rep4 = replaceMask(rep3, '\'-\'', '\'\'')
                rep5 = replaceMask(rep4, '\' \'', '\'\'')
                rep  = replaceMask(rep5, '\'.\'', '\'\'')
                cond.append(rep + ' LIKE \'%s\'' % (undotLikeMask(contactToLikeMask(filter['contact']))))
            doc = filter.get('doc', None)
            if doc:
                tableDoc = db.table('ClientDocument')
                table = table.leftJoin(tableDoc,
                                       [tableDoc['client_id'].eq(tableClient['id']), tableDoc['deleted'].eq(0)]
                                       )
                typeId, serial, number = doc
                if typeId or serial or number:
                    if typeId:
                        cond.append(tableDoc['documentType_id'].eq(typeId))
                    if serial:
                        cond.append(tableDoc['serial'].eq(serial))
                    if number:
                        cond.append(tableDoc['number'].eq(number))
                else:
                    cond.append(cond.append(tableDoc['id'].isNull()))
            regionSMO = filter.get('regionSMO', None)
            policy = filter.get('policy', None)
            if policy or regionSMO:
                tablePolicy = db.table('ClientPolicy')
                tableOrganisation = db.table('Organisation')
                table = table.innerJoin(tablePolicy,
                                        [tablePolicy['client_id'].eq(tableClient['id']), tablePolicy['deleted'].eq(0)]
                                        )
                onlyPolicyActual = None
                if policy:
                    onlyPolicyActual, policyActualData, policyType, policyKind, insurerId, serial, number = policy
                    if onlyPolicyActual or policyType or policyKind or insurerId or serial or number:
                        if onlyPolicyActual:
                            if policyActualData:
                                cond.append(tablePolicy['begDate'].le(policyActualData))
                                cond.append(
                                            db.joinOr(
                                                      [
                                                       tablePolicy['endDate'].ge(policyActualData),
                                                       tablePolicy['endDate'].isNull()
                                                      ]
                                                     )
                                            )
                            stmtPolicyTypeId = u''
                            stmtPolicyKindId = u''
                            if policyType:
                                stmtPolicyTypeId = u'AND CP.policyType_id = ClientPolicy.policyType_id'
                            if policyKind:
                                stmtPolicyKindId = u'AND CP.policyKind_id = ClientPolicy.policyKind_id'
                            cond.append('''ClientPolicy.id = (SELECT MAX(CP.id) FROM ClientPolicy AS CP
                                   WHERE CP.deleted = 0
                                   AND   CP.insurer_id = ClientPolicy.insurer_id
                                   AND   CP.client_id = Client.id
                                   AND   CP.endDate is null
                                   %s
                                   %s
                                  )''' % (stmtPolicyTypeId, stmtPolicyKindId))
                        if policyType:
                            if policyType == -1:
                                cmbPolicyTypeModel = self.cmbFilterPolicyType.model()
                                if cmbPolicyTypeModel.d:
                                    # codes 1, 2 means that policy is compulsory
                                    policyTypeIdList = [cmbPolicyTypeModel.getId(cmbPolicyTypeModel.d.getIndexByCode(code)) for code in ('1', '2')]
                                    cond.append(tablePolicy['policyType_id'].inlist(policyTypeIdList))
                            else:
                                cond.append(tablePolicy['policyType_id'].eq(policyType))
                        if policyKind:
                            cond.append(tablePolicy['policyKind_id'].eq(policyKind))
                        if insurerId:
                            # cond.append(tablePolicy['insurer_id'].eq(insurerId))
                            cond.append(tablePolicy['insurer_id'].inlist(insurerId))
                            table = table.innerJoin(tableOrganisation,
                                                   [tableOrganisation['id'].eq(tablePolicy['insurer_id']), tableOrganisation['deleted'].eq(0)]
                                                  )
                        elif not regionSMO:
                            table = table.leftJoin(tableOrganisation,
                                                   [tableOrganisation['id'].eq(tablePolicy['insurer_id']), tableOrganisation['deleted'].eq(0)]
                                                  )
                        if serial:
                            cond.append(tablePolicy['serial'].eq(serial))
                        if number:
                            cond.append(tablePolicy['number'].eq(number))
                    else:
                        cond.append(tablePolicy['id'].isNull())
                if regionSMO:
                    regionTypeSMO, regionSMOCode = regionSMO
                    table = table.innerJoin(tableOrganisation,
                                            [tableOrganisation['id'].eq(tablePolicy['insurer_id']),
                                            tableOrganisation['deleted'].eq(0)]
                                           )
                    if regionSMOCode:
                        if regionTypeSMO:
                            cond.append(tableOrganisation['area'].notlike(regionSMOCode))
                        else:
                            cond.append(tableOrganisation['area'].like(regionSMOCode))
                    if not onlyPolicyActual:
                        cond.append('''ClientPolicy.id = (SELECT MAX(CP.id) FROM ClientPolicy AS CP
                                   WHERE CP.deleted = 0
                                   AND   CP.client_id = Client.id
                                   AND   CP.endDate is null)''')
            orgId = filter.get('orgId', None)
            if orgId:
                tableWork = db.table('ClientWork')
                joinCond = [ tableClient['id'].eq(tableWork['client_id']),
                             'ClientWork.id = (select max(CW.id) from ClientWork as CW where CW.client_id=Client.id)'
                           ]
                table = table.join(tableWork, joinCond)
                cond.append(tableWork['org_id'].eq(orgId))
            if filter.get('socStatuses'):
                isSocStatusJoined = True
                socStatusesCondition = filter.get('socStatusesCondition', None)
                socStatusesClass = filter.get('socStatusesClass', None)
                socStatusesType = filter.get('socStatusesType', None)
                socStatusesBegDate = filter.get('socStatusesBegDate', QDate())
                socStatusesEndDate = filter.get('socStatusesEndDate', QDate())
                tableClientSocStatus = db.table('ClientSocStatus')
                clientFilterTable = db.table('Client')
                socStatusFilterTable = db.table('ClientSocStatus')
                if socStatusesCondition and not socStatusesEndDate and not socStatusesBegDate and not socStatusesType and not socStatusesClass:
                    cond.append(tableClientSocStatus['id'].isNull())
                if socStatusesClass:
                    socStatusClassIdList = db.getDescendants('rbSocStatusClass', 'group_id', socStatusesClass)
                    if socStatusClassIdList:
                        stmtStatusTypeId = u'''SELECT DISTINCT rbSocStatusClassTypeAssoc.type_id
                FROM  rbSocStatusClassTypeAssoc
                WHERE rbSocStatusClassTypeAssoc.class_id IN (%s)'''%(u','.join(str(socStatusClassId) for socStatusClassId in socStatusClassIdList))
                        queryStatusTypeId = db.query(stmtStatusTypeId)
                        resultStatusTypeIdList = []
                        while queryStatusTypeId.next():
                            resultStatusTypeIdList.append(queryStatusTypeId.value(0).toInt()[0])
                            parentSocStatusClassIdList = db.getTheseAndParents('rbSocStatusClass', 'group_id', [socStatusesClass])
                        if socStatusesCondition:
                            clientFilterTable = clientFilterTable.leftJoin(socStatusFilterTable, db.joinAnd([clientFilterTable['id'].eq(socStatusFilterTable['client_id']), tableClientSocStatus['deleted'].eq(0)]))
                            if resultStatusTypeIdList:
                                clientFilterCond = [db.joinOr([socStatusFilterTable['socStatusType_id'].inlist(resultStatusTypeIdList), tableClientSocStatus['id'].isNull()])]
                                if socStatusesBegDate:
                                    clientFilterCond.append(db.joinOr([ socStatusFilterTable['endDate'].dateGe(socStatusesBegDate),
                                                            socStatusFilterTable['endDate'].isNull()
                                                          ]
                                                         )
                                               )
                                if socStatusesEndDate:
                                    clientFilterCond.append(db.joinOr([ socStatusFilterTable['begDate'].dateLe(socStatusesEndDate),
                                                            socStatusFilterTable['begDate'].isNull()
                                                          ]
                                                         )
                                               )
                                clientSocStatusesFilterIdList = db.getIdList(clientFilterTable, clientFilterTable['id'], clientFilterCond,  ['id'])
                                cond.append(tableClient['id'].notInlist(clientSocStatusesFilterIdList))
                            else:
                                clientFilterCond = [db.joinOr([db.joinAnd[(socStatusFilterTable['socStatusType_id'].inlist(parentSocStatusClassIdList), tableClientSocStatus['id'].isNull())], tableClientSocStatus['socStatusType_id'].isNull()])]
                        else:
                            if resultStatusTypeIdList:
                                cond.append(tableClientSocStatus['socStatusType_id'].inlist(resultStatusTypeIdList))
                            else:
                                cond.append(tableClientSocStatus['socStatusClass_id'].inlist(parentSocStatusClassIdList))
                                cond.append(tableClientSocStatus['socStatusType_id'].isNull())
                                cond.append(tableClientSocStatus['deleted'].eq(0))
                    else:
                        if socStatusesCondition:
                            clientFilterTable = clientFilterTable.leftJoin(socStatusFilterTable, db.joinAnd([clientFilterTable['id'].eq(socStatusFilterTable['client_id']), tableClientSocStatus['deleted'].eq(0)]))
                            clientFilterCond = [db.joinOr([socStatusFilterTable['socStatusClass_id'].eq(socStatusesClass), tableClientSocStatus['id'].isNull()])]
                            if socStatusesBegDate:
                                clientFilterCond.append(db.joinOr([ socStatusFilterTable['endDate'].dateGe(socStatusesBegDate),
                                                        socStatusFilterTable['endDate'].isNull()
                                                      ]
                                                     )
                                           )
                            if socStatusesEndDate:
                                clientFilterCond.append(db.joinOr([ socStatusFilterTable['begDate'].dateLe(socStatusesEndDate),
                                                        socStatusFilterTable['begDate'].isNull()
                                                      ]
                                                     )
                                           )
                            clientSocStatusesFilterIdList = db.getIdList(clientFilterTable, clientFilterTable['id'], clientFilterCond,  ['id'])
                            cond.append(tableClient['id'].notInlist(clientSocStatusesFilterIdList))
                        else:
                            cond.append(tableClientSocStatus['socStatusClass_id'].eq(socStatusesClass))
                            cond.append(tableClientSocStatus['deleted'].eq(0))
                if socStatusesType:
                    if socStatusesCondition:
                        if not socStatusesClass:
                            clientFilterTable = clientFilterTable.leftJoin(socStatusFilterTable, db.joinAnd([clientFilterTable['id'].eq(socStatusFilterTable['client_id']), tableClientSocStatus['deleted'].eq(0)]))
                        clientFilterCond = [db.joinOr([clientFilterTable['socStatusType_id'].eq(socStatusesType), clientFilterTable['id'].isNull()])]
                        if socStatusesBegDate:
                            clientFilterCond.append(db.joinOr([ socStatusFilterTable['endDate'].dateGe(socStatusesBegDate),
                                                    socStatusFilterTable['endDate'].isNull()
                                                  ]
                                                 )
                                       )
                        if socStatusesEndDate:
                            clientFilterCond.append(db.joinOr([ socStatusFilterTable['begDate'].dateLe(socStatusesEndDate),
                                                    socStatusFilterTable['begDate'].isNull()
                                                  ]
                                                 )
                                       )
                        clientSocStatusesFilterIdList = db.getIdList(clientFilterTable, clientFilterTable['id'], clientFilterCond,  ['id'])
                        cond.append(tableClient['id'].notInlist(clientSocStatusesFilterIdList))
                    else:
                        cond.append(tableClientSocStatus['socStatusType_id'].eq(socStatusesType))
                        cond.append(tableClientSocStatus['deleted'].eq(0))
                if not socStatusesCondition:
                    if socStatusesBegDate:
                        cond.append(db.joinOr([ tableClientSocStatus['endDate'].dateGe(socStatusesBegDate),
                                            tableClientSocStatus['endDate'].isNull()
                                          ]
                                         )
                               )
                    if socStatusesEndDate:
                        cond.append(db.joinOr([ tableClientSocStatus['begDate'].dateLe(socStatusesEndDate),
                                            tableClientSocStatus['begDate'].isNull()
                                          ]
                                         )
                               )
                table = table.leftJoin(tableClientSocStatus, db.joinAnd([tableClient['id'].eq(tableClientSocStatus['client_id']), tableClientSocStatus['deleted'].eq(0)]))
            documentTypeForTracking = filter.get('documentTypeForTracking', None)
            documentTypeForTrackingNumber = filter.get('documentTypeForTrackingNumber', None)
            documentLocation = filter.get('documentLocation', None)
            personDocumentLocation = filter.get('personDocumentLocation', None)
            begDateFilterDocumentLocation = filter.get('begDateFilterDocumentLocation', QDate())
            endDateFilterDocumentLocation = filter.get('endDateFilterDocumentLocation', QDate())
            if documentTypeForTracking or documentTypeForTrackingNumber:
                tableDocumentTypeForTracking = db.table('Client_DocumentTracking')
                cond.append(tableDocumentTypeForTracking['deleted'].eq(0))
                table = table.leftJoin(tableDocumentTypeForTracking, tableClient['id'].eq(tableDocumentTypeForTracking['client_id']))
                if documentTypeForTracking:
                    cond.append(tableDocumentTypeForTracking['documentTypeForTracking_id'].eq(documentTypeForTracking))
                if documentTypeForTrackingNumber:
                    cond.append(tableDocumentTypeForTracking['documentNumber'].eq(forceString(documentTypeForTrackingNumber)))
            if self.chkFilterDocumentLocation.isChecked():
                tableDocumentLocation = db.table('Client_DocumentTrackingItem')
                if not documentTypeForTracking:
                    tableDocumentTypeForTracking = db.table('Client_DocumentTracking')
                    table = table.leftJoin(tableDocumentTypeForTracking, tableClient['id'].eq(tableDocumentTypeForTracking['client_id']))
                    cond.append(tableDocumentTypeForTracking['deleted'].eq(0))
                table = table.leftJoin(tableDocumentLocation, tableDocumentTypeForTracking['id'].eq(tableDocumentLocation['master_id']))
                if documentLocation:
                    cond.append(tableDocumentLocation['documentLocation_id'].eq(documentLocation))
                if begDateFilterDocumentLocation:
                    cond.append(tableDocumentLocation['documentLocationDate'].ge(begDateFilterDocumentLocation))
                if endDateFilterDocumentLocation:
                    cond.append(tableDocumentLocation['documentLocationDate'].le(endDateFilterDocumentLocation))
                if personDocumentLocation:
                    cond.append(tableDocumentLocation['person_id'].eq(personDocumentLocation))
            statusObservationType = filter.get('statusObservationType', None)
            if statusObservationType:
                cond.append('((SELECT Client_StatusObservation.statusObservationType_id FROM Client_StatusObservation WHERE Client_StatusObservation.deleted = 0 AND Client_StatusObservation.master_id = Client.id ORDER BY Client_StatusObservation.createDatetime DESC LIMIT 1) = %d)'%(statusObservationType))

            resident = filter.get('resident', None)
            if resident != None:
                tableClientAddress = db.table('ClientAddress').alias('CliAddRes')
                table = table.leftJoin(tableClientAddress, tableClientAddress['client_id'].eq(tableClient['id']))
                cond.append('CliAddRes.id in (select max(ca.id) from ClientAddress ca where ca.deleted = 0 and ca.type = 1 and ca.client_id = Client.`id`)')
                if resident == 0:
                    cond.append(tableClientAddress['resident'].isNull())
                elif resident == 1:
                    cond.append(tableClientAddress['resident'].eq(0))
                elif resident == 2:
                    cond.append(tableClientAddress['resident'].eq(1))

            address = filter.get('address', None)
            if address:
                addrType, addrRelation, KLADRCode, Okato, KLADRStreetCode, KLADRStreetCodeList, house, chkCorpus, corpus, flat = address
                tableClientAddress = db.table('ClientAddress')
                tableAddressHouse = db.table('AddressHouse')
                tableAddress = db.table('Address')
                table = table.leftJoin(tableClientAddress, tableClientAddress['client_id'].eq(tableClient['id']))
                table = table.leftJoin(tableAddress, tableAddress['id'].eq(tableClientAddress['address_id']))
                table = table.leftJoin(tableAddressHouse, tableAddressHouse['id'].eq(tableAddress['house_id']))
                addrTypeCond = '' if addrType == 2 else "CA.type=%d AND " % addrType
                cond.append('''ClientAddress.id IN (SELECT MAX(CA.id) FROM ClientAddress AS CA WHERE {0} CA.deleted=0 AND CA.client_id=Client.id {1})'''.format(addrTypeCond, 'GROUP BY CA.type' if addrType == 2 else ''))
                if KLADRStreetCode:
                    cond.append(tableAddressHouse['KLADRStreetCode'].eq(KLADRStreetCode))
                    if Okato:
                        # какая-то чёрная магия.
                        # я верю, что это можно улучшить!
                        okatoCond = u'''kladr.DOMA.OCATD LIKE \'%s%%\'''' % Okato if Okato else '''1'''
                        findInSetCond = u'''FIND_IN_SET(%s, kladr.DOMA.flatHouseList)'''% u'''CONCAT_WS("к", AddressHouse.number, AddressHouse.corpus)''' if corpus else u'''AddressHouse.number'''
                        cond.append(u'''(SELECT DISTINCT kladr.STREET.CODE
                        FROM kladr.STREET INNER JOIN kladr.DOMA ON kladr.DOMA.level5 = kladr.STREET.level5
                        WHERE %skladr.STREET.actuality=\'00\'
                        AND kladr.STREET.CODE = \'%s\'
                        AND %s
                        AND kladr.STREET.CODE = AddressHouse.KLADRStreetCode
                        AND (IF(AddressHouse.number != '' AND AddressHouse.number != ' ', %s, 1))
                        ORDER BY kladr.STREET.NAME, kladr.STREET.SOCR, kladr.STREET.CODE)'''%((u'kladr.DOMA.CODE LIKE \'%s%%\' AND '%(KLADRCode[0:-2])) if KLADRCode else u'', KLADRStreetCode, okatoCond, findInSetCond))
                    #else:
                        #cond.append(tableAddressHouse['KLADRStreetCode'].eq(KLADRStreetCode))
                elif Okato:
                    cond.append(tableAddressHouse['KLADRStreetCode'].inlist(KLADRStreetCodeList))
                elif KLADRCode:
                    mask = getLikeMaskForRegion(KLADRCode)
                    if mask == KLADRCode:
                        if addrRelation:
                            cond.append(tableAddressHouse['KLADRCode'].ne(KLADRCode))
                            cond.append(tableAddressHouse['KLADRCode'].ne(''))
                        else:
                            cond.append(tableAddressHouse['KLADRCode'].eq(KLADRCode))
                    else:
                        if addrRelation:
                            cond.append(tableAddressHouse['KLADRCode'].notlike(mask))
                            cond.append(tableAddressHouse['KLADRCode'].ne(''))
                        else:
                            cond.append(tableAddressHouse['KLADRCode'].like(mask))
                else:
                    cond.append("trim(ifnull(ClientAddress.freeInput, '')) <> ''")
                if house:
                    cond.append(tableAddressHouse['number'].eq(house))
                if chkCorpus:
                    cond.append('''TRIM(AddressHouse.corpus) = TRIM('{0}')'''.format(corpus))
                if flat:
                    cond.append(tableAddress['flat'].eq(flat))
            #elif 'addressOrgStructure' in filter:
            if 'addressOrgStructure' in filter:
                addrType, orgStructureId = filter['addressOrgStructure']
                addrIdList = None
                cond2 = []
                if (addrType+1) & 1:
                    addrIdList = getOrgStructureAddressIdList(orgStructureId)
                    addAddressCond(cond2, 0, addrIdList)
                if (addrType+1) & 2:
                    if addrIdList is None:
                        addrIdList = getOrgStructureAddressIdList(orgStructureId)
                    addAddressCond(cond2, 1, addrIdList)
                if ((addrType+1) & 4):
                    if orgStructureId:
                        orgStructureIdList = getOrgStructureDescendants(orgStructureId)
                        addAttachCond(cond2, 'orgStructure_id IN (%s)'%(u','.join(forceString(orgStructureId) for orgStructureId in orgStructureIdList)), 1, None)
                    else:
                        addAttachCond(cond2, 'LPU_id=%d'%QtGui.qApp.currentOrgId(), 1, None)
                if cond2:
                    cond.append(db.joinOr(cond2))
            else:
                if 'regAddressIsEmpty' in filter:
                    addAddressCond(cond, 0, None)
                if 'locAddressIsEmpty'in filter:
                    addAddressCond(cond, 1, None)
            if 'beds' in filter:
                indexFlatCode, orgStructureId = filter['beds']
                if orgStructureId:
                    bedsIdList = getOrgStructureDescendants(orgStructureId)
                else:
                    bedsIdList = getOrgStructures(QtGui.qApp.currentOrgId())
                if indexFlatCode == 2:
                    clientBedsIdList = self.getLeavedHospitalBeds(bedsIdList)
                else:
                    clientBedsIdList = self.getHospitalBeds(bedsIdList, indexFlatCode)
                cond.append(tableClient['id'].inlist(clientBedsIdList))
            if 'attachTo' in filter:
                isNotAttachOrganisation = filter.get('isNotAttachOrganisation', False)
                attachOrgId = filter['attachTo']
                if attachOrgId:
                    addAttachCond(cond, 'LPU_id=%d' % attachOrgId, *filter.get('attachType', (0, None, QDate().currentDate(), QDate().currentDate())), isStatement = filter.get('isStatement', 0), isNotAttachOrganisation=isNotAttachOrganisation)
                else:
                    pass # добавить - не имеет пост. прикрепления
            elif 'attachToNonBase' in filter:
                addAttachCond(cond, 'LPU_id!=%d'%QtGui.qApp.currentOrgId(), *filter.get('attachType', (0, None, QDate(), QDate())), isStatement = filter.get('isStatement', 0))
            elif 'attachType' in filter:
                addAttachCond(cond, '', *filter['attachType'], isStatement = filter.get('isStatement', 0))
            if 'tempInvalid' in filter:
                begDate, endDate = filter['tempInvalid']
                if begDate or endDate:
                    tableTempInvalid = db.table('TempInvalid')
                    table = table.leftJoin(tableTempInvalid, tableTempInvalid['client_id'].eq(tableClient['id']))
                    if begDate:
                        cond.append(tableTempInvalid['endDate'].ge(begDate))
                    if endDate:
                        cond.append(tableTempInvalid['begDate'].le(endDate))
            if self.TFAccountingSystemId:
                if filter.get('TFUnconfirmed', False):
                    tableClientIdentification = db.table('ClientIdentification')
                    condClientIdentification  = [ tableClientIdentification['client_id'].eq(tableClient['id']),
                                                  tableClientIdentification['accountingSystem_id'].eq(self.TFAccountingSystemId),
                                                  tableClientIdentification['deleted'].eq(0),
                                                ]
                    cond.append('NOT '+db.existsStmt(tableClientIdentification, condClientIdentification))
                elif 'TFConfirmed' in filter:
                    begDate, endDate = filter['TFConfirmed']
                    tableClientIdentification = db.table('ClientIdentification')
                    condClientIdentification  = [ tableClientIdentification['client_id'].eq(tableClient['id']),
                                                  tableClientIdentification['accountingSystem_id'].eq(self.TFAccountingSystemId),
                                                  tableClientIdentification['deleted'].eq(0),
                                                ]
                    if begDate:
                        condClientIdentification.append(tableClientIdentification['checkDate'].ge(begDate))
                    if endDate:
                        condClientIdentification.append(tableClientIdentification['checkDate'].le(endDate))
                    cond.append(db.existsStmt(tableClientIdentification, condClientIdentification))

            if 'clientConsentTypeId' in filter:
                tableCC = db.table('ClientConsent')
                condClientConsent = [tableCC['client_id'].eq(tableClient['id']), tableCC['deleted'].eq(0)]
                clientConsentValue = filter.get('clientConsentValue', None)
                if clientConsentValue in (1, 2):
                    condClientConsent.append(tableCC['value'].eq(clientConsentValue - 1))
                clientConsentTypeId = filter['clientConsentTypeId']
                if clientConsentTypeId:
                    condClientConsent.append(tableCC['clientConsentType_id'].eq(clientConsentTypeId))
                clientConsentBegDate = filter.get('clientConsentBegDate', None)
                if clientConsentBegDate:
                    condClientConsent.append(db.joinOr([tableCC['endDate'].dateGe(clientConsentBegDate),
                                                        tableCC['endDate'].isNull()]))
                clientConsentEndDate = filter.get('clientConsentEndDate', None)
                if clientConsentEndDate:
                    condClientConsent.append(tableCC['date'].dateLe(clientConsentEndDate))
                clientConsentDate1 = filter.get('clientConsentDate1', None)
                if clientConsentDate1:
                    condClientConsent.append(tableCC['date'].dateGe(clientConsentDate1))
                clientConsentDate2 = filter.get('clientConsentDate2', None)
                if clientConsentDate2:
                    condClientConsent.append(tableCC['date'].dateLe(clientConsentDate2))
                clientPersonConsent = filter.get('clientPersonConsent', None)
                if clientPersonConsent:
                    condClientConsent.append(tableCC['createPerson_id'].eq(clientPersonConsent))
                if clientConsentValue == 3:
                    cond.append(db.notExistsStmt(tableCC, condClientConsent))
                else:
                    cond.append(db.existsStmt(tableCC, condClientConsent))

            if 'clientResearchKind' in filter or 'clientNoResearch' in filter:
                tableCR = db.table('ClientResearch')
                clientNoResearch = filter.get('clientNoResearch', None)
                condClientResearch = [tableCR['client_id'].eq(tableClient['id']), tableCR['deleted'].eq(0)]
                clientResearchKind = filter.get('clientResearchKind', None)
                if clientResearchKind:
                    condClientResearch.append(tableCR['researchKind_id'].eq(clientResearchKind))
                clientResearchBegDate = filter.get('clientResearchBegDate', None)
                if clientResearchBegDate:
                    condClientResearch.append(tableCR['begDate'].dateGe(clientResearchBegDate))
                clientResearchEndDate = filter.get('clientResearchEndDate', None)
                if clientResearchEndDate:
                    condClientResearch.append(tableCR['begDate'].dateLe(clientResearchEndDate))
                if clientNoResearch:
                    cond.append(db.notExistsStmt(tableCR, condClientResearch))
                else:
                    cond.append(db.existsStmt(tableCR, condClientResearch))

            self.appendVaccinationClientCond(filter, cond)
  
            table = self.appendContingentTypeCond(table, filter, cond, isEventJoined, isSocStatusJoined)

            if filter.get('excludeDead'):
                cond.append(tableClient['deathDate'].isNull())

            if 'clientMKBFrom' in filter:
                clientMKBFrom = filter.get('clientMKBFrom', None)
                clientMKBTo = filter.get('clientMKBTo', None)
                tableDiagnosis = db.table('Diagnosis')
                tableDiagnosisType = db.table('rbDiagnosisType')
                table = table.leftJoin(tableDiagnosis, tableDiagnosis['client_id'].eq(tableClient['id']))
                table = table.leftJoin(tableDiagnosisType, tableDiagnosisType['id'].eq(tableDiagnosis['diagnosisType_id']))
                if clientMKBFrom:
                    cond.append(tableDiagnosis['MKB'].ge(clientMKBFrom))
                if clientMKBTo:
                    cond.append(tableDiagnosis['MKB'].le(clientMKBTo))
                if clientMKBFrom or clientMKBTo:
                    cond.append(tableDiagnosisType['code'].inlist(['1', '2', '3', '4']))

            if 'clientNote' in filter:
                addCondLike(cond, tableClient['notes'],  addDotsBefore(addDots(filter.get('clientNote', ''))))

            if 'identification' in filter:
                identificationId = filter.get('identification',  None)
                tableIdentification = db.table('ClientIdentification')
                table = table.leftJoin(tableIdentification, tableIdentification['client_id'].eq(tableClient['id']))
                if identificationId:
                    cond.append(tableIdentification['accountingSystem_id'].eq(identificationId))    
                cond.append(tableIdentification['deleted'].eq(0))

            archive = filter.get('archive', 0)
            if archive == 0:
                cond.append(tableClient['endDate'].isNull())
            elif archive == 1:
                cond.append(tableClient['endDate'].isNotNull())
                
            clientsLimit = forceInt(QtGui.qApp.preferences.appPrefs.get('clientsLimit', 10000))
            getIdList = db.getDistinctIdList if table != tableClient else db.getIdList
            sort = []
            if self.clientsSortingCol in [0, 1, 2]:
                for name in [['lastName', 'firstName', 'patrName'],['firstName', 'lastName', 'patrName'],['patrName', 'lastName', 'firstName']][self.clientsSortingCol]:
                    sort.append('%s %s' % (tableClient[name].name(), self.clientsSortingDest))
            else:
                for name in ['lastName', 'firstName', 'patrName']:
                    sort.append('%s %s' % (tableClient[name].name(), self.clientsSortingDest))
                if self.clientsSortingCol == 3:
                    sort.insert(0, '%s %s' % (tableClient['birthDate'].name(), self.clientsSortingDest))
                elif self.clientsSortingCol == 5:
                    sort.insert(0, '%s %s' % (tableClient['SNILS'].name(), self.clientsSortingDest))
                else:
                    sort.append('%s %s' % (tableClient['birthDate'].name(), self.clientsSortingDest))

            # sort.append('%s %s' % (tableClient['id'].name(), self.clientsSortingDest))

            idList = getIdList(table,
                               tableClient['id'].name(),
                               cond,
                               sort,
                               limit=clientsLimit)

            if len(idList) < clientsLimit:
                clientCount = len(idList)
            else:
                getCount = db.getDistinctCount if table != tableClient else db.getCount
                clientCount = getCount(table, tableClient['id'].name(), cond)

            self.tblClients.setIdList(idList, posToId, clientCount)
            self.focusClients()
        finally:
            QtGui.QApplication.restoreOverrideCursor()

        self.updateClientsListRequest = False
        if not idList and len(cond) > 1 and QtGui.qApp.userHasRight(urRegTabNewWriteRegistry):
            if QtGui.qApp.gis_oms_enable():
                messageBox = QtGui.QMessageBox()
                messageBox.setWindowFlags(messageBox.windowFlags() | Qt.WindowStaysOnTopHint)
                messageBox.setWindowTitle(u'Внимание!')
                messageBox.setText(u'Пациент не обнаружен.\nХотите зарегистрировать пациента?')
                messageBox.addButton(QtGui.QPushButton(u'ОК'), QtGui.QMessageBox.ActionRole)
                messageBox.addButton(QtGui.QPushButton(u'Искать по ФЕРЗЛ'), QtGui.QMessageBox.ActionRole)
                messageBox.addButton(QtGui.QPushButton(u'Отмена'), QtGui.QMessageBox.ActionRole)
                res = messageBox.exec_()
                if res == 0:
                    self.editNewClient()
                    self.focusClients()
                elif res == 1:
                    from Exchange.ferzl.ferzlDialog import CferzlDialog
                    dlg = CferzlDialog(self)
                    if dlg.exec_() == CferzlDialog.Accepted:
                        result = dlg.getResult()
                        self.findClient(result['clientId'])
            else:
                res = QtGui.QMessageBox.warning(self,
                                                u'Внимание',
                                                u'Пациент не обнаружен.\nХотите зарегистрировать пациента?',
                                                QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel,
                                                QtGui.QMessageBox.Ok)
                if res == QtGui.QMessageBox.Ok:
                    self.editNewClient()
                    self.focusClients()
        elif clientCount == 1:
            clientId = idList[0]
            self.focusClients()
            if QtGui.qApp.userHasAnyRight([urBatchRegLocatCardProcess]):
                prefs = getPref(QtGui.qApp.preferences.reportPrefs, 'BatchRegLocatCardParams', {})
                batchRegLocatCardProcess = getPrefBool(prefs, 'BatchRegLocatCardProcess', False)
                if batchRegLocatCardProcess:
                    self.getParamsBatchRegistrationLocationCard = CGetParamsBatchRegistrationLocationCard(self, clientId)
                    clientLocationCardId = self.getParamsBatchRegistrationLocationCard.registrationLocationCard()
                    if not clientLocationCardId:
                        res = QtGui.QMessageBox.warning(self,
                                    u'Внимание',
                                    u'Ошибка регистрации статуса места нахождения карты пациента.\nСтатус не зарегистрирован.',
                                    QtGui.QMessageBox.Cancel,
                                    QtGui.QMessageBox.Cancel)
                    else:
                        self.showClientInfo(clientId)
            onSingleClientInSearchResult = QtGui.qApp.onSingleClientInSearchResult()
            if onSingleClientInSearchResult == 1:
                self.requestNewEvent()
            elif onSingleClientInSearchResult == 2:
                openClientVaccinationCard(self, clientId)
        else:
            self.focusClients()

        if not self.chkFilterPolicy.isChecked():
            self.edtFilterPolicyActualData.setDate(None)
            self.edtFilterPolicySerial.setText('')
            self.edtFilterPolicyNumber.setText('')
            self.cmbFilterPolicyInsurer.setValue(None)
            if not self.cmbFilterPolicyType.hasTable():
                self.cmbFilterPolicyType.setTable('rbPolicyType', True, specialValues=((-1, u'ОМС', u'ОМС'),))
            self.cmbFilterPolicyType.setCode(None)
            if not self.cmbFilterPolicyKind.hasTable():
                self.cmbFilterPolicyKind.setTable('rbPolicyKind', True)
            self.cmbFilterPolicyKind.setCode(None)


    def appendVaccinationClientCond(self, filter, clientCond):
        u''' Добавляет в clientCond условия по фильтрам из вкладки Иммунизация (Картотека) '''
        vaccinationBegDate     = filter.get('vaccinationBegDate',     None)
        vaccinationEndDate     = filter.get('vaccinationEndDate',     None)
        vaccinationCalendarId  = filter.get('vaccinationCalendarId',  None)
        infectionIdList        = filter.get('infectionIdList',        [])
        vaccineIdList          = filter.get('vaccineIdList',          [])
        vaccinationSeria       = filter.get('vaccinationSeria',       None)
        vaccinationType        = filter.get('vaccinationType',        [])
        vaccinationContingent  = filter.get('vaccinationContingent',  None)
        medicalExemption       = filter.get('medicalExemption',       None)
        medicalExemptionTypeId = filter.get('medicalExemptionTypeId', None)

        db = QtGui.qApp.db
        tableClient = db.table('Client')

        tableClientVaccination = db.table('ClientVaccination')
        tableVaccineSchema = db.table('rbVaccine_Schema')
        tableInfectionVaccine = db.table('rbInfection_rbVaccine')
        tableVaccinationCalendarInfection = db.table('rbVaccinationCalendar_Infection')

        tableClientMedicalExemption = db.table('ClientMedicalExemption')
        tableClientMedicalExemptionInfection = db.table('ClientMedicalExemption_Infection')


        # получить предыдущие типы прививок из rbVaccine_Schema
        def getPrevVaccinationTypes(vaccineId, vaccinationType):
            if not vaccinationType:
                return []
            stmt = '''SELECT vaccinationType
                FROM rbVaccine_Schema
                WHERE master_id = %d AND id < (
                    SELECT id
                    FROM rbVaccine_Schema
                    WHERE master_id = %d AND vaccinationType = %s
                    ORDER BY id
                    LIMIT 1
                )'''
            query = db.query(stmt % (
                forceInt(vaccineId),
                forceInt(vaccineId),
                decorateString(vaccinationType)),
            )
            items = []
            while query.next():
                items.append(forceString(query.value(0)))
            return items

        # получить предыдущие типы прививок по инфекции из rbVaccinationCalendar_Infection
        def getPrevInfectionVaccinationTypes(vaccinationCalendarId, infectionId, vaccinationType):
            if not vaccinationType:
                return []
            stmt = '''SELECT vaccinationType
                FROM rbVaccinationCalendar_Infection
                WHERE infection_id = %d AND master_id = %d
                    AND id < (
                        SELECT id
                        FROM rbVaccinationCalendar_Infection
                        WHERE infection_id = %d AND master_id = %d
                            AND vaccinationType = %s
                        ORDER BY id
                        LIMIT 1
                    )'''
            query = db.query(stmt % (
                forceInt(infectionId),
                forceInt(vaccinationCalendarId),
                forceInt(infectionId),
                forceInt(vaccinationCalendarId),
                decorateString(vaccinationType),
            ))
            items = []
            while query.next():
                items.append(forceString(query.value(0)))
            return items


        ##########################################
        # Контингент
        ##########################################
        cond = [
            tableClientVaccination['client_id'].eq(tableClient['id']),
            tableClientVaccination['deleted'].eq(0),
        ]
        if vaccinationBegDate:
            cond.append(tableClientVaccination['datetime'].dateGe(vaccinationBegDate))
        if vaccinationEndDate:
            cond.append(tableClientVaccination['datetime'].dateLe(vaccinationEndDate))
        if vaccinationSeria:
            cond.append(tableClientVaccination['seria'].eq(vaccinationSeria))
        if vaccinationType:
            cond.append(tableClientVaccination['vaccinationType'].eq(vaccinationType))
        if vaccineIdList:
            cond.append(tableClientVaccination['vaccine_id'].inlist(vaccineIdList))

        if vaccinationContingent == 0:  # не привиты
            clientCond.append(db.notExistsStmt(tableClientVaccination, cond))
        elif vaccinationContingent == 1:  # привиты
            clientCond.append(db.existsStmt(tableClientVaccination, cond))
        elif vaccinationContingent == 2:  # подлежат
            clientCond.append(tableClient['deathDate'].isNull())

            if vaccineIdList:
                cond = []  # игнорируем стандартные, при Контингент=Подлежат совсем другие правила
                for vaccineId in vaccineIdList:
                    cond = [
                        tableClientVaccination['client_id'].eq(tableClient['id']),
                        tableClientVaccination['deleted'].eq(0),
                        tableClientVaccination['vaccine_id'].eq(vaccineId),
                    ]
                    prevVaccinationTypes = getPrevVaccinationTypes(vaccineId, vaccinationType)
                    if prevVaccinationTypes:
                        # должен быть проведен последний предыдущий тип прививки этой вакцины, если он есть
                        cond.append(tableClientVaccination['vaccinationType'].eq(prevVaccinationTypes[-1]))
                        clientCond.append(db.existsStmt(tableClientVaccination, cond))
                    elif vaccinationType:
                        # задан тип прививки, но предыдущих нет - проверить отсутствие только этого типа прививки
                        cond.append(tableClientVaccination['vaccinationType'].eq(vaccinationType))
                        clientCond.append(db.notExistsStmt(tableClientVaccination, cond))
                    else:
                        # иначе подходят все пациенты без этой прививки или пациенты с любым типом этой прививки
                        # т.е. не проверяем ClientVaccination
                        pass
                    # если выбран План - нужно проверить на соответствие полу из плана (в rbVaccine_Schema только возраст)
                    if vaccinationCalendarId:
                        calendarCond = [
                            tableVaccinationCalendarInfection['master_id'].eq(vaccinationCalendarId),
                        ]
                        if vaccinationType:
                            calendarCond.append(
                                tableVaccinationCalendarInfection['vaccinationType'].eq(vaccinationType)
                            )
                        sexList = db.getDistinctIdList(tableVaccinationCalendarInfection, 'sex', calendarCond)
                        if len(sexList) > 0 and (0 not in sexList):
                            clientCond.append(tableClient['sex'].inlist(sexList))
                    # также нужно проверить возраст на дату начала или окончания периода
                    # (на текущую дату, если период не задан)
                    ageCond = [ tableVaccineSchema['master_id'].eq(vaccineId), ]
                    if vaccinationType:
                        ageCond.append(tableVaccineSchema['vaccinationType'].eq(vaccinationType))
                    for record in db.getDistinctRecordList(tableVaccineSchema, 'age', ageCond):
                        age = decorateString(record.value('age').toString())
                        if not age:
                            continue
                        if vaccinationBegDate and vaccinationEndDate:
                            begDate = decorateString(vaccinationBegDate.toString(Qt.ISODate))
                            endDate = decorateString(vaccinationEndDate.toString(Qt.ISODate))
                            clientCond.append(db.joinOr([
                                'isSexAndAgeSuitable(0,Client.birthDate,0,%s,%s)' % (age, begDate),
                                'isSexAndAgeSuitable(0,Client.birthDate,0,%s,%s)' % (age, endDate),
                            ]))
                        else:
                            clientCond.append(
                                'isSexAndAgeSuitable(0,Client.birthDate,0,%s,NOW())' % age
                            )

            elif vaccinationCalendarId and infectionIdList:
                cond = []  # игнорируем стандартные, при Контингент=Подлежат совсем другие правила
                for infectionId in infectionIdList:
                    prevVaccinationTypes = getPrevInfectionVaccinationTypes(
                        vaccinationCalendarId, infectionId, vaccinationType)
                    # получаем список прививок по инфекции
                    vaccineIdList = db.getIdList(tableInfectionVaccine, 'vaccine_id',
                        tableInfectionVaccine['infection_id'].eq(infectionId))
                    cond = [
                        tableClientVaccination['client_id'].eq(tableClient['id']),
                        tableClientVaccination['deleted'].eq(0),
                        tableClientVaccination['vaccine_id'].inlist(vaccineIdList),
                    ]
                    if prevVaccinationTypes:
                        # должен быть проведен последний предыдущий тип прививки этой вакцины, если он есть
                        cond.append(tableClientVaccination['vaccinationType'].eq(prevVaccinationTypes[-1]))
                        clientCond.append(db.existsStmt(tableClientVaccination, cond))
                    elif vaccinationType:
                        # задан тип прививки, но предыдущих нет - проверить отсутствие только этого типа прививки
                        cond.append(tableClientVaccination['vaccinationType'].eq(vaccinationType))
                        clientCond.append(db.notExistsStmt(tableClientVaccination, cond))
                    else:
                        # иначе подходят все пациенты без этой прививки или пациенты с любым типом этой прививки
                        # т.е. не проверяем ClientVaccination
                        pass
                    # также нужно проверить пол и возраст на дату начала или окончания периода
                    # (на текущую дату, если период не задан)
                    ageCond = [
                        tableVaccinationCalendarInfection['master_id'].eq(vaccinationCalendarId),
                        tableVaccinationCalendarInfection['infection_id'].eq(infectionId),
                    ]
                    if vaccinationType:
                        prevVaccinationTypes.append(vaccinationType)
                    if prevVaccinationTypes:
                        ageCond.append(tableVaccinationCalendarInfection['vaccinationType'].inlist(prevVaccinationTypes))
                    sexList = set()
                    for record in db.getDistinctRecordList(tableVaccinationCalendarInfection, 'vaccinationType, sex, age', ageCond):
                        sex = forceInt(record.value('sex'))
                        age = decorateString(record.value('age').toString())
                        sexList.add(sex)
                        if not age:
                            continue
                        if vaccinationType and vaccinationType != forceString(record.value('vaccinationType')):
                            # предыдущие типы прививок нужны только для пола
                            # возраст определять для текущего типа прививки (если указан)
                            continue
                        if vaccinationBegDate and vaccinationEndDate:
                            begDate = decorateString(vaccinationBegDate.toString(Qt.ISODate))
                            endDate = decorateString(vaccinationEndDate.toString(Qt.ISODate))
                            clientCond.append(db.joinOr([
                                'isSexAndAgeSuitable(0,Client.birthDate,0,%s,%s)' % (age, begDate),
                                'isSexAndAgeSuitable(0,Client.birthDate,0,%s,%s)' % (age, endDate),
                            ]))
                        else:
                            clientCond.append(
                                'isSexAndAgeSuitable(0,Client.birthDate,0,%s,NOW())' % age
                            )
                    if len(sexList) > 0 and (0 not in sexList):
                        clientCond.append(tableClient['sex'].inlist(sexList))

        ##########################################
        # Медотводы
        ##########################################
        cond = [
            tableClientMedicalExemption['client_id'].eq(tableClient['id']),
            tableClientMedicalExemption['deleted'].eq(0),
        ]

        if vaccinationBegDate and vaccinationEndDate:
            # дата окончания не указана для постоянных медотводов, ставим для удобства
            endDate = "IFNULL(ClientMedicalExemption.endDate, DATE('2100-01-01'))"
            begDate = "ClientMedicalExemption.date"
            filterBegDate = decorateString(vaccinationBegDate.toString(Qt.ISODate))
            filterEndDate = decorateString(vaccinationEndDate.toString(Qt.ISODate))
            # даты медотвода могут частично входить в диапазон дат из фильтра
            cond.append(db.joinOr([
                # дата начала из фильтра находится внутри периода медотвода
                '%s BETWEEN %s AND %s' % (filterBegDate, begDate, endDate),
                # дата окончания из фильтра находится внутри периода медотвода
                '%s BETWEEN %s AND %s' % (filterEndDate, begDate, endDate),
                # период медотвода находится внутри периода дат из фильтра
                '%s >= %s AND %s <= %s' % (begDate, filterBegDate, endDate, filterEndDate),
                # период дат из фильтра находится внутри периода медотвода
                '%s <= %s AND %s >= %s' % (begDate, filterBegDate, endDate, filterEndDate),
            ]))

        if medicalExemptionTypeId:
            cond.append(tableClientMedicalExemption['medicalExemptionType_id'].eq(medicalExemptionTypeId))

        table = tableClientMedicalExemption
        if infectionIdList:
            table = table.leftJoin(tableClientMedicalExemptionInfection,
                                tableClientMedicalExemptionInfection['master_id'].eq(tableClientMedicalExemption['id']))
            cond.append(tableClientMedicalExemptionInfection['infection_id'].inlist(infectionIdList))
        elif vaccinationCalendarId:
            table = table.leftJoin(tableClientMedicalExemptionInfection,
                                tableClientMedicalExemptionInfection['master_id'].eq(tableClientMedicalExemption['id']))
            cond.append(tableClientMedicalExemptionInfection['infection_id'].inlist(self.modelFilterInfection.idList()))

        if medicalExemption == 0:  # нет медотводов
            clientCond.append(db.notExistsStmt(table, cond))
        elif medicalExemption == 1: # есть медотвод
            clientCond.append(db.existsStmt(table, cond))
        elif medicalExemption == 2:  # временный
            cond.append(tableClientMedicalExemption['endDate'].isNotNull())
            clientCond.append(db.existsStmt(table, cond))
        elif medicalExemption == 3:  # постоянный
            cond.append(tableClientMedicalExemption['endDate'].isNull())
            clientCond.append(db.existsStmt(table, cond))


    def appendContingentTypeCond(self, table, filter, cond, isEventJoined, isSocStatusJoined):
        if 'contingentTypeId' not in filter.keys():
            return table
        db = QtGui.qApp.db
        contingentTypeId = filter.get('contingentTypeId', None)
        contingentEventTypeStatus = filter.get('contingentEventTypeStatus', 0)
        contingentActionTypeStatus = filter.get('contingentActionTypeStatus', 0)
        contingentMKBFrom = filter.get('contingentMKBFrom', None)
        contingentMKBTo = filter.get('contingentMKBTo', None)
        contingentSpeciality = filter.get('contingentSpeciality', 0)
        tableContingentKind = None
        contingentKindCond = ''

        contingentOperation = forceInt(db.translate(CContingentTypeTranslator.CTTName, 'id',
                                                    contingentTypeId, 'contingentOperation'))
        observedOperation = forceInt(db.translate(CContingentTypeTranslator.CTTName, 'id',
                                                    contingentTypeId, 'observedOperation'))
        eventOrActionOperation = forceInt(db.translate(CContingentTypeTranslator.CTTName, 'id',
                                                    contingentTypeId, 'eventOrActionOperation'))

        tableClient = db.table('Client')

        contingentTypeCond = []
        if CContingentTypeTranslator.isSexAgeSocStatusEnabled(contingentOperation):
            tmp = []
            if not isSocStatusJoined:
                tableClientSocStatus = db.table('ClientSocStatus')
                table = table.leftJoin(tableClientSocStatus, tableClient['id'].eq(tableClientSocStatus['client_id']))
            tableContingentKind = db.table('ClientContingentKind')
            table = table.leftJoin(tableContingentKind, tableClient['id'].eq(tableContingentKind['client_id']))
            sexAgeCond    = CContingentTypeTranslator.getSexAgeCond(contingentTypeId)
            socStatusCond = CContingentTypeTranslator.getSocStatusCond(contingentTypeId)
            contingentKindCond = CContingentTypeTranslator.getContingentKindCond(contingentTypeId)
            if CContingentTypeTranslator.isSexAgeSocStatusOperationType_OR(contingentOperation):
                if sexAgeCond:
                    tmp.extend(sexAgeCond)
                if socStatusCond:
                    tmp.extend(socStatusCond)
                if contingentKindCond:
                    tmp.extend(contingentKindCond)
                if tmp:
                    contingentTypeCond.append(db.joinOr(tmp))
            else:
                if sexAgeCond:
                    tmp.append(db.joinOr(sexAgeCond))
                if socStatusCond:
                    tmp.append(db.joinOr(socStatusCond))
                if contingentKindCond:
                    tmp.append(db.joinOr(contingentKindCond))
                if tmp:
                    contingentTypeCond.append(db.joinAnd(tmp))

        if contingentEventTypeStatus and (CContingentTypeTranslator.isEventTypeMESEnabled(observedOperation) or CContingentTypeTranslator.isHealthGroupEnabled(observedOperation)):
            tmp = []
            tableEvent = db.table('Event').alias('ContingentEvent')
            contingentEventJoinCond = [tableEvent['client_id'].eq(tableClient['id'])]
            eventTypeCond = CContingentTypeTranslator.getEventTypeJoinCond(contingentTypeId)
            MESCond       = CContingentTypeTranslator.getMESJoinCond(contingentTypeId)
            healtGroupCond= CContingentTypeTranslator.getHealtGroupJoinCond(contingentTypeId)
            if CContingentTypeTranslator.isEventTypeMESOperationType_OR(observedOperation):
                if eventTypeCond:
                    tmp.extend(eventTypeCond)
                if MESCond:
                    tmp.extend(MESCond)
                if tmp:
                    contingentEventJoinCond.append(db.joinOr(tmp))
            else:
                if eventTypeCond:
                    tmp.append(db.joinOr(eventTypeCond))
                if MESCond:
                    tmp.append(db.joinOr(MESCond))
                if tmp:
                    contingentEventJoinCond.append(db.joinAnd(tmp))

            if CContingentTypeTranslator.isHealthGroupOperationType_OR(observedOperation):
                if eventTypeCond and not CContingentTypeTranslator.isEventTypeMESOperationType_OR(observedOperation):
                    tmp.extend(eventTypeCond)
                if healtGroupCond:
                    tmp.extend(healtGroupCond)
                if tmp:
                    contingentEventJoinCond.append(db.joinOr(tmp))
            else:
                if eventTypeCond and not CContingentTypeTranslator.isEventTypeMESOperationType_OR(observedOperation):
                    tmp.append(db.joinOr(eventTypeCond))
                if healtGroupCond:
                    tmp.append(db.joinOr(healtGroupCond))
                if tmp:
                    contingentEventJoinCond.append(db.joinAnd(tmp))
            if contingentEventTypeStatus > 1:
                table = table.innerJoin(tableEvent, contingentEventJoinCond)
            else:
                table = table.leftJoin(tableEvent, contingentEventJoinCond)

            contingentEventCond = CContingentTypeTranslator.getEventStatusCond(contingentEventTypeStatus)
            if contingentEventCond:
                cond.extend(contingentEventCond)

        if contingentActionTypeStatus and CContingentTypeTranslator.isEventTypeActionTypeEnabled(eventOrActionOperation):
            tmp = []
            isEventTypeMES = not contingentEventTypeStatus or not CContingentTypeTranslator.isEventTypeMESEnabled(observedOperation)
            tableAction = db.table('Action').alias('ContingentAction')
            contingentActionJoinCond = []
            contingentEventActionCond = None
            if CContingentTypeTranslator.isEventTypeActionTypeOperationType_OR(eventOrActionOperation):
                if contingentActionTypeStatus == 1:
                    eventTypeCond = CContingentTypeTranslator.getEventTypeSubQueryJoinCond(contingentTypeId)
                    actionTypeCond = CContingentTypeTranslator.getActionTypeSubQueryJoinCond(contingentTypeId)
                    if eventTypeCond and isEventTypeMES:
                        tmp.extend(eventTypeCond)
                    if actionTypeCond:
                        tmp.extend(actionTypeCond)
                    if tmp:
                        contingentEventActionCond =  [u'''Client.`id` NOT IN (SELECT CE.client_id FROM Action AS CA INNER JOIN Event AS CE ON  CA.`event_id`=CE.`id` WHERE CE.`client_id`= Client.`id` AND  %s)'''%(db.joinOr(tmp))]
                else:
                    tableEvent = db.table('Event').alias('ContingentEvent')
                    eventTypeCond = None
                    if isEventTypeMES:
                        eventTypeCond = CContingentTypeTranslator.getEventTypeJoinCond(contingentTypeId)
                        table = table.innerJoin(tableEvent, tableEvent['client_id'].eq(tableClient['id']))
                    actionTypeCond = CContingentTypeTranslator.getActionTypeJoinCond(contingentTypeId)
                    if eventTypeCond and isEventTypeMES:
                        tmp.extend(eventTypeCond)
                    if actionTypeCond:
                        tmp.extend(actionTypeCond)
                    contingentActionJoinCond.append(tableEvent['id'].eq(tableAction['event_id']))
                    if tmp:
                        contingentActionJoinCond.append(db.joinOr(tmp))
                    table = table.innerJoin(tableAction, contingentActionJoinCond)
            else:
                if contingentActionTypeStatus == 1:
                    eventTypeCond = CContingentTypeTranslator.getEventTypeSubQueryJoinCond(contingentTypeId)
                    actionTypeCond = CContingentTypeTranslator.getActionTypeSubQueryJoinCond(contingentTypeId)
                    if eventTypeCond and isEventTypeMES:
                        tmp.append(db.joinOr(eventTypeCond))
                    if actionTypeCond:
                        tmp.append(db.joinOr(actionTypeCond))
                    contingentEventActionCond =  [u'''Client.`id` NOT IN (SELECT CE.client_id FROM Action AS CA INNER JOIN Event AS CE ON  CA.`event_id`=CE.`id` WHERE CE.`client_id`= Client.`id` AND  %s)'''%(db.joinAnd(tmp))]
                else:
                    eventTypeCond = None
                    tableEvent = db.table('Event').alias('ContingentEvent')
                    if isEventTypeMES:
                        eventTypeCond = CContingentTypeTranslator.getEventTypeJoinCond(contingentTypeId)
                        table = table.innerJoin(tableEvent, tableEvent['client_id'].eq(tableClient['id']))
                    actionTypeCond = CContingentTypeTranslator.getActionTypeJoinCond(contingentTypeId)
                    if eventTypeCond and isEventTypeMES:
                        tmp.append(db.joinOr(eventTypeCond))
                    if actionTypeCond:
                        tmp.append(db.joinOr(actionTypeCond))
                    contingentActionJoinCond.append(tableEvent['id'].eq(tableAction['event_id']))
                    if tmp:
                        contingentActionJoinCond.append(db.joinAnd(tmp))
                    table = table.innerJoin(tableAction, contingentActionJoinCond)
            if contingentActionTypeStatus != 1:
                contingentEventActionCond = CContingentTypeTranslator.getActionStatusCond(contingentActionTypeStatus)
            if contingentEventActionCond:
                cond.extend(contingentEventActionCond)
        if contingentMKBTo or contingentMKBFrom:
            if not tableContingentKind:
                tableContingentKind = db.table('ClientContingentKind')
                table = table.leftJoin(tableContingentKind, tableClient['id'].eq(tableContingentKind['client_id']))
            if contingentMKBFrom:
                cond.append(tableContingentKind['MKB'].ge(contingentMKBFrom))
            if contingentMKBTo:
                cond.append(tableContingentKind['MKB'].le(contingentMKBTo))
        if contingentSpeciality:
            if not tableContingentKind:
                tableContingentKind = db.table('ClientContingentKind')
                table = table.leftJoin(tableContingentKind, tableClient['id'].eq(tableContingentKind['client_id']))
            if 'speciality' not in contingentKindCond:
                cond.append(tableContingentKind['speciality_id'].eq(contingentSpeciality))
        if contingentTypeCond:
            cond.extend(contingentTypeCond)
        
        return table


    def getClientFilterAsText(self):
        def formatAge(value):
            unitMap = {0: (u'годa',   u'лет',     u'лет'),   # это родительный падеж, да?
                       1: (u'месяца', u'месяцев', u'месяцев'),
                       2: (u'недели', u'недель',  u'недель'),
                       3: (u'дня',    u'дней',    u'дней')
                      }
            (lowCnt, lowUnit), (highCnt, highUnit) = value
            return u'с %s до %s' %( formatNum(lowCnt,  unitMap.get(lowUnit)  or unitMap.get(0)),
                                     formatNum(highCnt, unitMap.get(highUnit) or unitMap.get(0)),
                                   )

        def formatAddress(value):
            addressType, addressRelation, addressCity, addressOKATO, addressStreet, addressStreetList, addressHouse, chkCorpus, addressCorpus, addressFlat = value
            #TODO: учесть addressOKATO и addressStreetList, да?
            address = smartDict()
            address.update({'KLADRCode': forceString(addressCity),
                            'KLADRStreetCode': forceString(addressStreet),
                            'number': forceString(addressHouse),
                            'corpus': forceString(addressCorpus) if chkCorpus else None,
                            'flat': forceString(addressFlat),
                            'freeInput': None})
            addressText = formatAddressInt(address)
            return {0: u'регистрации ', 1: u'проживания '}.get(addressType, u'') + {False: '', True: u' любой, кроме '}.get(addressRelation, u'') + addressText

        filter  = self.__filter
        resList = []
        convertFilterToTextItem(resList, filter, 'id',        u'Код пациента',  unicode)
        convertFilterToTextItem(resList, filter, 'lastName',  u'Фамилия')
        convertFilterToTextItem(resList, filter, 'firstName', u'Имя')
        convertFilterToTextItem(resList, filter, 'patrName',  u'Отчество')
        convertFilterToTextItem(resList, filter, 'birthDate', u'Дата рождения', forceString)
        convertFilterToTextItem(resList, filter, 'age',       u'Возраст',       formatAge)
        convertFilterToTextItem(resList, filter, 'sex',       u'Пол',           formatSex)
        convertFilterToTextItem(resList, filter, 'SNILS',     u'СНИЛС',         formatSNILS)
        convertFilterToTextItem(resList, filter, 'address',   u'Адрес',         formatAddress)
        convertFilterToTextItem(resList, filter, 'doc',       u'документ',      lambda doc: formatDocument(doc[0], doc[1], doc[2]))
        convertFilterToTextItem(resList, filter, 'policy',    u'полис',         lambda policy: formatPolicy(policy[3], policy[4], policy[5]))
        convertFilterToTextItem(resList, filter, 'orgId',     u'занятость',     getOrganisationShortName)
        convertFilterToTextItem(resList, filter, 'regAddressIsEmpty', u'адрес',    lambda dummy: u'пуст')
        return '\n'.join([item[0]+u': '+item[1] for item in resList])


    def showClientInfo(self, id):
        u"""
            показ информации о пациенте в панели наверху
        """
        self.updateClientInfo(id)
        self.actEditClient.setEnabled(bool(id))
        self.actRelationsClient.setEnabled(bool(id))
        self.actOpenClientDocumentTrackingHistory.setEnabled(bool(id) and QtGui.qApp.userHasAnyRight([urRegTabReadLocationCard, urEditLocationCard]))
        self.actEditStatusObservationClient.setEnabled(bool(id))
        self.actShowContingentsClient.setEnabled(bool(id))
        self.actCheckClientAttach.setEnabled(bool(id))
        self.actPortal_Doctor.setEnabled(bool(id))
        self.actSurveillancePlanningClients.setEnabled(bool(isSurveillanceActive(id, {}, {'begDate': QDate.currentDate()})))
        QtGui.qApp.setCurrentClientId(id)


    def setIsUpdateF111Enable(self, clientId):
        isUpdateF111Enable = False
        actionId = None
        if clientId:
            clientSex, clientAge = getClientSexAge(clientId)
            if clientSex == 2:
                db = QtGui.qApp.db
                tableEvent = db.table('Event')
                tableEventType = db.table('EventType')
                queryTable = tableEvent.innerJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
                cond = [tableEventType['code'].like(u'KBiR%'),
                        tableEvent['execDate'].isNull(),
                        tableEvent['client_id'].eq(clientId),
                        tableEvent['deleted'].eq(0),
                        tableEventType['deleted'].eq(0),
                        ]
                recordEvent = db.getRecordEx(queryTable, [tableEvent['id']], cond, u'Event.id DESC')
                eventId = forceRef(recordEvent.value('id')) if recordEvent else None
                if eventId:
                    actionTypeIdListByKBiR = getActionTypeIdListByFlatCode(u'111/y-20')
                    if actionTypeIdListByKBiR:
                        tableAction = db.table('Action')
                        cond = [tableAction['event_id'].eq(eventId),
                                tableAction['deleted'].eq(0),
                                tableAction['actionType_id'].inlist(actionTypeIdListByKBiR),
                                tableAction['endDate'].isNull()
                                ]
                        record = db.getRecordEx(tableAction, [tableAction['id']], cond, u'Action.begDate DESC')
                        actionId = forceRef(record.value('id')) if record else None
                isUpdateF111Enable = forceBool(actionId)
        return isUpdateF111Enable


    def clientId(self, index):
        return self.tblClients.itemId(index)


    def selectedClientId(self):
        return self.tblClients.currentItemId()


    @pyqtSignature('QModelIndex')
    def on_tblClients_clicked(self, index):
        selectedRows = []
        rowCount = self.tblClients.model().rowCount()
        for index in self.tblClients.selectedIndexes():
            if index.row() < rowCount:
                row = index.row()
                if row not in selectedRows:
                    selectedRows.append(row)

        self.lblClientsCount.setText(self.realCount1 +  u', из них выделено ' + forceString(len(selectedRows)))

    @pyqtSignature('QModelIndex')
    def on_tblEvents_clicked(self, index):
        selectedRows = []
        rowCount = self.tblEvents.model().rowCount()
        for index in self.tblEvents.selectedIndexes():
            if index.row() < rowCount:
                row = index.row()
                if row not in selectedRows:
                    selectedRows.append(row)

        self.lblEventsCount.setText(self.eventCount +  u', из них выделено ' + forceString(len(selectedRows)))

    @pyqtSignature('QModelIndex')
    def on_tblActionsStatus_clicked(self, index):
        selectedRows = []
        rowCount = self.tblActionsStatus.model().rowCount()
        for index in self.tblActionsStatus.selectedIndexes():
            if index.row() < rowCount:
                row = index.row()
                if row not in selectedRows:
                    selectedRows.append(row)

        self.lblActionsStatusCount.setText(self.actionsStatusCount +  u', из них выделено ' + forceString(len(selectedRows)))

    @pyqtSignature('QModelIndex')
    def on_tblActionsDiagnostic_clicked(self, index):
        selectedRows = []
        rowCount = self.tblActionsDiagnostic.model().rowCount()
        for index in self.tblActionsDiagnostic.selectedIndexes():
            if index.row() < rowCount:
                row = index.row()
                if row not in selectedRows:
                    selectedRows.append(row)

        self.lblActionsDiagnosticCount.setText(self.actionsDiagnosticCount + u', из них выделено ' + forceString(len(selectedRows)))

    @pyqtSignature('QModelIndex')
    def on_tblActionsCure_clicked(self, index):
        selectedRows = []
        rowCount = self.tblActionsCure.model().rowCount()
        for index in self.tblActionsCure.selectedIndexes():
            if index.row() < rowCount:
                row = index.row()
                if row not in selectedRows:
                    selectedRows.append(row)

        self.lblActionsCureCount.setText(self.actionsCureCount + u', из них выделено ' + forceString(len(selectedRows)))

    @pyqtSignature('QModelIndex')
    def on_tblActionsMisc_clicked(self, index):
        selectedRows = []
        rowCount = self.tblActionsMisc.model().rowCount()
        for index in self.tblActionsMisc.selectedIndexes():
            if index.row() < rowCount:
                row = index.row()
                if row not in selectedRows:
                    selectedRows.append(row)

        self.lblActionsMiscCount.setText(self.actionsMiscCount + u', из них выделено ' + forceString(len(selectedRows)))

    @pyqtSignature('QModelIndex')
    def on_tblExpertTempInvalid_clicked(self, index):
        selectedRows = []
        rowCount = self.tblExpertTempInvalid.model().rowCount()
        for index in self.tblExpertTempInvalid.selectedIndexes():
            if index.row() < rowCount:
                row = index.row()
                if row not in selectedRows:
                    selectedRows.append(row)

        self.lblExpertTempInvalidCount.setText(self.expertTempInvalidCount + u', из них выделено ' + forceString(len(selectedRows)))

    @pyqtSignature('QModelIndex')
    def on_tblExpertDisability_clicked(self, index):
        selectedRows = []
        rowCount = self.tblExpertDisability.model().rowCount()
        for index in self.tblExpertDisability.selectedIndexes():
            if index.row() < rowCount:
                row = index.row()
                if row not in selectedRows:
                    selectedRows.append(row)

        self.lblExpertDisabilityCount.setText(self.expertDisabilityCount + u', из них выделено ' + forceString(len(selectedRows)))

    @pyqtSignature('QModelIndex')
    def on_tblExpertVitalRestriction_clicked(self, index):
        selectedRows = []
        rowCount = self.tblExpertVitalRestriction.model().rowCount()
        for index in self.tblExpertVitalRestriction.selectedIndexes():
            if index.row() < rowCount:
                row = index.row()
                if row not in selectedRows:
                    selectedRows.append(row)

        self.lblExpertVitalRestrictionCount.setText(self.expertVitalRestrictionCount + u', из них выделено ' + forceString(len(selectedRows)))

    @pyqtSignature('QModelIndex')
    def on_tblVisits_clicked(self, index):
        selectedRows = []
        rowCount = self.tblVisits.model().rowCount()
        for index in self.tblVisits.selectedIndexes():
            if index.row() < rowCount:
                row = index.row()
                if row not in selectedRows:
                    selectedRows.append(row)

        self.lblVisitCount.setText(self.visitsCount + u', из них выделено ' + forceString(len(selectedRows)))

    def currentClientId(self):
        return QtGui.qApp.currentClientId()


    def editClient(self, clientId):
        if QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]):
            dialog = CClientEditDialog(self)
            try:
                if clientId:
                    dialog.load(clientId)
                if dialog.exec_():
                    clientId = dialog.itemId()
                    self.updateClientsList(self.__filter, clientId)
            finally:
                dialog.deleteLater()
    #            self.showClientInfo(clientId)


    def editCurrentClient(self):
        clientId = self.currentClientId()
        self.editClient(clientId)


    def findClient(self, clientId, clientRecord=None):
        self.tabMain.setCurrentIndex(0)
        if not clientRecord:
            db = QtGui.qApp.db
            clientRecord = db.getRecord('Client', 'lastName, firstName, patrName, sex, birthDate, SNILS', clientId)
        if clientRecord:
            filter = {}
            filter['id'] = clientId
            filter['accountingSystemId'] = None
            filter['lastName'] = forceString(clientRecord.value('lastName'))
            filter['firstName'] = forceString(clientRecord.value('firstName'))
            filter['patrName'] = forceString(clientRecord.value('patrName'))
            filter['sex'] = forceInt(clientRecord.value('sex'))
            filter['birthDate'] = forceDate(clientRecord.value('birthDate'))
            filter['SNILS'] = forceString(clientRecord.value('SNILS'))
            self.__filter = self.updateFilterWidgets(filter)
            if not self.__filter:
                self.__filter = self.updateFilterWidgets({'id': clientId, 'accountingSystemId':None}, True)
            self.updateClientsList(self.__filter, clientId)
            self.tabMain.setTabEnabled(1, True)


    def getParamsDialogFilter(self):
        dialogInfo = {}
        if self.chkFilterLastName.isChecked():
            if self.chkFilterOldLastName.isChecked():
                dialogInfo['oldLastName'] = forceString(self.edtFilterLastName.text())
            else:
                dialogInfo['lastName'] = forceString(self.edtFilterLastName.text())
        if self.chkFilterFirstName.isChecked():
            if self.chkFilterOldFirstName.isChecked():
                dialogInfo['oldFirstName'] = forceString(self.edtFilterFirstName.text())
            else:
                dialogInfo['firstName'] = forceString(self.edtFilterFirstName.text())
        if self.chkFilterPatrName.isChecked():
            if self.chkFilterOldPatrName.isChecked():
                dialogInfo['oldPatrName'] = forceString(self.edtFilterPatrName.text())
            else:
                dialogInfo['patrName'] = forceString(self.edtFilterPatrName.text())
        if self.chkFilterBirthDay.isChecked():
            dialogInfo['birthDate'] = forceDate(self.edtFilterBirthDay.date())
        if self.chkFilterSex.isChecked():
            dialogInfo['sex'] = self.cmbFilterSex.currentIndex()
        if self.chkFilterSNILS.isChecked():
            dialogInfo['SNILS'] = self.edtFilterSNILS.text()
        if self.chkFilterDocument.isChecked():
            dialogInfo['docType'] = self.cmbFilterDocumentType.value()
            serial = self.edtFilterDocumentSerial.text()
            for c in '-=/_|':
                serial = serial.replace(c, ' ')
            serial = trim(serial).split()
            dialogInfo['serialLeft'] = serial[0] if len(serial) >= 1 else ''
            dialogInfo['serialRight'] = serial[1] if len(serial) >= 2 else ''
            dialogInfo['docNumber'] = self.edtFilterDocumentNumber.text()
        if self.chkFilterContact.isChecked():
            dialogInfo['contact'] = forceString(self.edtFilterContact.text())
#        if self.chkFilterPolicy.isChecked():
        dialogInfo['polisSerial'] = forceString(self.edtFilterPolicySerial.text())
        dialogInfo['polisNumber'] = forceString(self.edtFilterPolicyNumber.text())
        dialogInfo['polisCompany'] = self.cmbFilterPolicyInsurer.value()
        dialogInfo['polisType'] = self.cmbFilterPolicyType.value()
        dialogInfo['polisKind'] = self.cmbFilterPolicyKind.value()
        dialogInfo['polisTypeName'] = self.cmbFilterPolicyType.model().getName(self.cmbFilterPolicyType.currentIndex())
        dialogInfo['polisBegDate'] = self.edtFilterPolicyActualData.date()
        if self.chkFilterAddress.isChecked():
            dialogInfo['addressType'] = self.cmbFilterAddressType.currentIndex()
            dialogInfo['addressRelation'] = self.cmbFilterAddressRelation.currentIndex()
            dialogInfo['regCity'] = self.cmbFilterAddressCity.code()
            dialogInfo['regStreet'] = self.cmbFilterAddressStreet.code()
            dialogInfo['regHouse'] = self.edtFilterAddressHouse.text()
            if self.chkFilterAddressCorpus.isChecked():
                dialogInfo['regCorpus'] = self.edtFilterAddressCorpus.text()
            dialogInfo['regFlat'] = self.edtFilterAddressFlat.text()
        if self.chkResident.isChecked():
            dialogInfo['resident'] = self.cmbResident.currentIndex()
        else:
            dialogInfo['resident'] = forceInt(QtGui.qApp.preferences.appPrefs.get('resident', 0))
        return dialogInfo


    def editNewClient(self):
        if QtGui.qApp.userHasAnyRight([urRegTabNewWriteRegistry]):
            dialog = CClientEditDialog(self)
            dialogInfo = self.getParamsDialogFilter()
            dialog.modelSocStatuses.loadItems(None)
            if dialogInfo:
                dialogInfo['identCard'] = self.identCard if hasattr(self, 'identCard') else None
                dialog.setClientDialogInfo(dialogInfo)
            try:
                if dialog.exec_():
                    clientId = dialog.itemId()
                    clientRecord = dialog.getRecord()
                    if clientId:
                        self.findClient(clientId, clientRecord)
            finally:
                dialog.deleteLater()


    def findControlledByChk(self, chk):
        for s in self.chkListOnClientsPage:
            if s[0] == chk:
                return s[1]
        for s in self.chkListOnEventsPage:
            if s[0] == chk:
                return s[1]
        for s in self.chkListOnActionsPage:
            if s[0] == chk:
                return s[1]
        for s in self.chkListOnExpertPage:
            if s[0] == chk:
                return s[1]
        for s in self.chkListOnExpertMCPage:
            if s[0] == chk:
                return s[1]
        for s in self.chkListOnVisitsPage:
            if s[0] == chk:
                return s[1]
        return None


    def activateFilterWdgets(self, alist):
        if alist:
            for s in alist:
                s.setEnabled(True)
                if isinstance(s, (QtGui.QLineEdit, CDateEdit)):
                    s.selectAll()
            alist[0].setFocus(Qt.ShortcutFocusReason)
            alist[0].update()


    def deactivateFilterWdgets(self, alist):
        for s in alist:
            s.setEnabled(False)


    def updateFilterWidgets(self, filter, force=False):
        def intUpdateClientFilterLineEdit(chk, widget, inFilter, name, outFilter):
            val = inFilter.get(name, None)
            if val and (chk.isChecked() or force):
                chk.setChecked(True)
                self.activateFilterWdgets([widget])
                widget.setText(unicode(val))
                outFilter[name] = val

        def intUpdateClientFilterComboBox(chk, widget, inFilter, name, outFilter):
            if name in inFilter and (chk.isChecked() or force):
                val = inFilter[name]
                chk.setChecked(True)
                self.activateFilterWdgets([widget])
                widget.setCurrentIndex(val)
                outFilter[name] = val

        def intUpdateClientFilterRBComboBox(chk, widget, inFilter, name, outFilter):
            if name in inFilter and (chk.isChecked() or force):
                val = inFilter[name]
                chk.setChecked(True)
                self.activateFilterWdgets([widget])
                widget.setValue(val)
                outFilter[name] = val

        def intUpdateClientFilterDateEdit(chk, widget, inFilter, name, outFilter):
            val = inFilter.get(name, None)
            if val and (chk.isChecked() or force):
                chk.setChecked(True)
                self.activateFilterWdgets([widget])
                widget.setDate(val)
                outFilter[name] = val

        outFilter = {}
        for s in self.chkListOnClientsPage:
            chk = s[0]
            if chk == self.chkFilterId:
                intUpdateClientFilterLineEdit(chk, s[1][0], filter, 'id', outFilter)
                intUpdateClientFilterRBComboBox(chk, s[1][1], filter, 'accountingSystemId', outFilter)
            elif chk == self.chkFilterLastName:
                intUpdateClientFilterLineEdit(chk, s[1][0], filter, 'lastName', outFilter)
            elif chk == self.chkFilterFirstName:
                intUpdateClientFilterLineEdit(chk, s[1][0], filter, 'firstName', outFilter)
            elif chk == self.chkFilterPatrName:
                intUpdateClientFilterLineEdit(chk, s[1][0], filter, 'patrName', outFilter)
            elif chk == self.chkFilterOldLastName:
                intUpdateClientFilterLineEdit(chk, s[1][0], filter, 'oldLastName', outFilter)
            elif chk == self.chkFilterOldFirstName:
                intUpdateClientFilterLineEdit(chk, s[1][0], filter, 'oldFirstName', outFilter)
            elif chk == self.chkFilterOldPatrName:
                intUpdateClientFilterLineEdit(chk, s[1][0], filter, 'oldPatrName', outFilter)
            elif chk == self.chkFilterSex:
                intUpdateClientFilterComboBox(chk, s[1][0], filter, 'sex', outFilter)
            elif chk == self.chkFilterBirthDay:
                intUpdateClientFilterDateEdit(chk, s[1][0], filter, 'birthDate', outFilter)
            elif chk == self.chkFilterContact:
                intUpdateClientFilterLineEdit(chk, s[1][0], filter, 'contact', outFilter)
            elif chk == self.chkFilterSNILS:
                intUpdateClientFilterLineEdit(chk, s[1][0], filter, 'SNILS', outFilter)
            else:
                chk.setChecked(False)
                self.deactivateFilterWdgets(s[1])
        return outFilter


    def onChkFilterToggled(self, chk, checked):
        controlled = self.findControlledByChk(chk)
        if checked:
            self.activateFilterWdgets(controlled)
        else:
            self.deactivateFilterWdgets(controlled)


    def findEvent(self, eventId):
        self.tabMain.setCurrentIndex(1)
        if eventId in self.modelEvents.idList():
            self.tblEvents.setCurrentItemId(eventId)
        else:
            filter = {}
            self.updateEventsList(filter, eventId)


    def setEventList(self, eventIdList):
        self.tabMain.setCurrentIndex(1)
        self.tblEvents.setIdList(eventIdList)
#            filter = {}
#            self.updateEventsList(filter, eventId)


    def requestNewEvent(self):
        clientId = self.currentClientId()
        if clientId:
            return requestNewEvent({'widget':self, 'clientId':clientId})
        return None


    def requestNewEventQueue(self, typeQueue=-1):
        clientId = self.currentClientId()
#        #WTF? у реестра просят создать событие, но он почему-то делегирует это дальше
#        #правильное решение: создавать самому + слать сигналы, которые учтут изменение в ресурсах.
#        dockFreeQueue = QtGui.qApp.mainWindow.dockFreeQueue
#        if dockFreeQueue and dockFreeQueue.content and dockFreeQueue.content.locked():
#            dockFreeQueue.content.on_actAmbCreateOrder_triggered()
#        elif clientId:
        if clientId:
            return requestNewEvent({'widget':self, 'clientId':clientId, 'typeQueue':typeQueue})
        return None

    #########################################################################

    def setCmbFilterEventTypeFilter(self, eventPurposeId):
        if eventPurposeId:
            filter = 'EventType.isActive = 1 AND EventType.purpose_id =%d' % eventPurposeId
        else:
            filter = getWorkEventTypeFilter(isApplyActive=True)
        self.cmbFilterEventType.setTable('EventType', False, filter=filter)


    def addEqCond(self, cond, table, fieldName, filter, name):
        if name in filter:
            cond.append(table[fieldName].eq(filter[name]))


    def addLikeCond(self, cond, table, fieldName, filter, name):
        if name in filter:
            cond.append(table[fieldName].like(filter[name]))


    def addDateCond(self, cond, table, fieldName, filter, begDateName, endDateName):
        begDate = filter.get(begDateName, None)
        if begDate:
            cond.append(table[fieldName].ge(begDate))
        endDate = filter.get(endDateName, None)
        if endDate:
            cond.append(table[fieldName].lt(endDate.addDays(1)))


    def addDateTimeCond(self, cond, table, fieldName, filter, begDateTimeName, endDateTimeName):
        begDateTime = filter.get(begDateTimeName, None)
        if begDateTime:
            cond.append(table[fieldName].ge(begDateTime))
        endDateTime = filter.get(endDateTimeName, None)
        if endDateTime:
            cond.append(table[fieldName].le(endDateTime))


    def addRangeCond(self, cond, table, fieldName, filter, begName, endName):
        if begName in filter:
            cond.append(table[fieldName].ge(filter[begName]))
        if endName in filter:
            cond.append(table[fieldName].le(filter[endName]))


    def updateEventListAfterEdit(self, eventId):
        if self.tabMain.currentIndex() == 1:
            self.updateEventsList(self.__eventFilter, eventId)
        QtGui.qApp.emitCurrentClientInfoChanged()
        self.showClientInfo(QtGui.qApp.currentClientId())


    def _setEventsOrderByColumn(self, column):
        self.tblEvents.setOrder(column)
        self.updateEventsList(self.__eventFilter, self.tblEvents.currentItemId())
        self.setSortingIndicator(self.tblEvents, column, not self.tblEvents._isDesc)


    def getFinanceByIndex(self, financeIndex):
        financeNames = [u'бюджет', u'ОМС', u'ДМС', u'платн%', u'целев%']
        db = QtGui.qApp.db
        table = db.table('rbFinance')
        cond = [table['name'].like(financeNames[financeIndex - 1])]
        record = db.getRecordEx(table, [table['code'], table['id']], cond)
        return forceInt(record.value('code')), forceInt(record.value('id'))


    def updateEventsList(self, filter, posToId=None):
        # в соответствии с фильтром обновляет список событий.
        self.__eventFilter = filter
        order = self.tblEvents.order() if self.tblEvents.order() else ['Event.setDate DESC', 'Event.id']
        db = QtGui.qApp.db
        table = db.table('Event')
        tableEventType = db.table('EventType')
        tableContract = db.table('Contract')
        tableEventTypePurpose = db.table('rbEventTypePurpose')
        tableVisit = db.table('Visit')

        queryTable = table
        cond = [table['deleted'].eq(0),
                # tableEventType['context'].notlike(u'inspection%'),
                tableEventType['context'].notlike(u'relatedAction%'),
                ]
        queryTable = queryTable.innerJoin(tableEventType, tableEventType['id'].eq(table['eventType_id']))
        queryTable = queryTable.innerJoin(tableEventTypePurpose, tableEventTypePurpose['id'].eq(tableEventType['purpose_id']))

        if 'Client' in order:
            tableClient = db.table('Client')
            queryTable = queryTable.leftJoin(tableClient, tableClient['id'].eq(table['client_id']))

        if 'MES' in order:
            tableMES = db.table('mes.MES')
            queryTable = queryTable.leftJoin(tableMES, tableMES['id'].eq(table['MES_id']))

        if 'Event.execPerson_id' in order or 'specialityId' in filter or 'orgStructureId' in filter or QtGui.qApp.userHasAnyRight([urRegVisibleOwnEventsOrgStructureOnly, urRegVisibleOwnEventsParentOrgStructureOnly]):
            tableExecPerson = db.table('Person')
            queryTable = queryTable.leftJoin(tableExecPerson, tableExecPerson['id'].eq(table['execPerson_id']))

        if 'rbResult' in order:
            tableResult = db.table('rbResult')
            queryTable = queryTable.leftJoin(tableResult, tableResult['id'].eq(table['result_id']))

        if 'MKB' in order or 'MKBEx' in order:
            tableDiagnosis = db.table('Diagnosis')
            queryTable = queryTable.leftJoin(tableDiagnosis, 'Diagnosis.id=getEventDiagnosis(Event.id)')

        if u'rbHealthGroup.code' in order:
            tableRBHealthGroup = db.table('rbHealthGroup')
            queryTable = queryTable.leftJoin(tableRBHealthGroup, 'rbHealthGroup.id=getEventHealthGroupDiagnostic(Event.id)')

        if u'rbDiagnosticResult.name' in order:
            tableRBDiagnosticResult = db.table('rbDiagnosticResult')
            queryTable = queryTable.leftJoin(tableRBDiagnosticResult, 'rbDiagnosticResult.id=getEventResultDiagnostic(Event.id)')

        cond.append(tableEventTypePurpose['code'].notlike('0'))
        self.addEqCond(cond, table, 'id', filter, 'id')
        self.addEqCond(cond, table, 'createPerson_id', filter, 'createPersonId')
        self.addDateCond(cond, table, 'createDatetime', filter, 'begCreateDate', 'endCreateDate')
        self.addEqCond(cond, table, 'modifyPerson_id', filter, 'modifyPersonId')
        self.addDateCond(cond, table, 'modifyDatetime', filter, 'begModifyDate', 'endModifyDate')
        if 'clientIds' in filter:
            clientIds = filter['clientIds']
            cond.append(table['client_id'].inlist(clientIds))
        if 'externalId' in filter:
            cond.append(table['externalId'].like(filter['externalId']))
        eventExpertId = filter.get('eventExpertId', False)
        if eventExpertId:
            cond.append(table['expert_id'].eq(eventExpertId))
        elif eventExpertId is None:
            cond.append(table['expert_id'].isNull())

        if 'begExpertiseDate' in filter:
            begExpertiseDate = filter.get('begExpertiseDate', None)
            endExpertiseDate = filter.get('endExpertiseDate', None)
            if not begExpertiseDate and not endExpertiseDate:
                cond.append(table['expertiseDate'].isNull())
            elif begExpertiseDate:
                cond.append(table['expertiseDate'].ge(begExpertiseDate))
            elif endExpertiseDate:
                cond.append(table['expertiseDate'].le(endExpertiseDate))

        if 'eventExportStatus' in filter:
            eventExportStatus = filter.get('eventExportStatus', None)
            eventExportSystem = filter.get('eventExportSystem', None)

            tableEventExport = db.table('Event_Export')
            eventExportCond = [ tableEventExport['master_id'].eq(table['id']),
                                tableEventExport['success'].eq(1),
                                ]
            if eventExportSystem:
                eventExportCond.append(tableEventExport['system_id'].eq(eventExportSystem))
            queryTable = queryTable.leftJoin(tableEventExport,
                                             eventExportCond
                                             )
            if eventExportStatus == 0:
                cond.append(tableEventExport['id'].isNotNull())
            else:
                cond.append(tableEventExport['id'].isNull())

        if 'accountSumLimit' in filter:
            accountSumLimit = filter.get('accountSumLimit', 0)
            sumLimitFrom = filter.get('sumLimitFrom', 0)
            sumLimitTo = filter.get('sumLimitTo', 0)
            sumLimitDelta = filter.get('sumLimitDelta', 0)
            tableEventLocalContract = db.table('Event_LocalContract')
            queryTable = queryTable.innerJoin(tableEventLocalContract, tableEventLocalContract['master_id'].eq(table['id']))
            cond.append(tableEventLocalContract['deleted'].eq(0))
            cond.append(tableEventLocalContract['sumLimit'].gt(0))
            if sumLimitFrom or sumLimitTo and sumLimitFrom <= sumLimitTo:
                cond.append(tableEventLocalContract['sumLimit'].ge(sumLimitFrom))
                cond.append(tableEventLocalContract['sumLimit'].le(sumLimitTo))
            if accountSumLimit == 1:
                cond.append(table['totalCost'].gt(tableEventLocalContract['sumLimit']))
                if sumLimitDelta > 0:
                    cond.append(u'Event.totalCost >= (Event_LocalContract.sumLimit + %d)'%(sumLimitDelta))
            elif accountSumLimit == 2:
                cond.append(table['totalCost'].lt(tableEventLocalContract['sumLimit']))
                if sumLimitDelta > 0:
                    cond.append(u'Event.totalCost <= (Event_LocalContract.sumLimit + %d)'%(sumLimitDelta))
        self.addDateTimeCond(cond, table, 'setDate', filter, 'begSetDateTime', 'endSetDateTime')
        if filter.get('emptyExecDate', False):
            cond.append(table['execDate'].isNull())
        self.addDateTimeCond(cond, table, 'execDate', filter, 'begExecDateTime', 'endExecDateTime')
        self.addDateCond(cond, table, 'nextEventDate', filter, 'begNextDate', 'endNextDate')
        eventPurposeId = filter.get('eventPurposeId', None)
        if eventPurposeId:
            cond.append(table['eventType_id'].name()+' IN (SELECT id FROM EventType WHERE EventType.purpose_id=%d)' % eventPurposeId)
        if 'eventTypeId' in filter:
            cond.append(table['eventType_id'].inlist(filter['eventTypeId'].split(', ')))
        elif not eventPurposeId:
            cond.append(table['eventType_id'].name()+' IN (SELECT id FROM EventType WHERE'+getWorkEventTypeFilter(False)+')')
        if 'personId' in filter:
            personId = filter['personId']
            if personId == -1:
                cond.append(table['execPerson_id'].isNull())
            else:
                cond.append(table['execPerson_id'].eq(personId))
        else:
            if 'specialityId' in filter:
                cond.append(tableExecPerson['speciality_id'].eq(filter['specialityId']))
            if 'orgStructureId' in filter:
                orgStructureId = filter.get('orgStructureId', None)
                if orgStructureId:
                    orgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', orgStructureId)
                    if orgStructureIdList:
                        cond.append(tableExecPerson['orgStructure_id'].inlist(orgStructureIdList))
        if 'isPrimary' in filter:
            cond.append(table['isPrimary'].eq(filter['isPrimary']))
        if 'order' in filter:
            cond.append(table['order'].eq(filter['order']))
        if 'relegateOrgId' in filter:
            if 'everythingExcept' in filter and filter['relegateOrgId'] is not None:
                cond.append('Event.`relegateOrg_id` != {0}'.format(filter['relegateOrgId']))
            else:
                cond.append(table['relegateOrg_id'].eq(filter['relegateOrgId']))
        if 'dispanserId' in filter:

            dispanserId = filter.get('dispanserId')
            dispanserList = dispanserId.split(', ')

            if 'None' not in dispanserList:
                condDispanser = "EXISTS (SELECT * FROM Diagnostic LEFT JOIN rbDispanser ON rbDispanser.ID = Diagnostic.dispanser_id WHERE Diagnostic.event_id = Event.id AND rbDispanser.id IN ({0}) AND Diagnostic.deleted = 0)".format(dispanserId)
                cond.append(condDispanser)

            elif dispanserList == ['None']:
                condDispanser = "EXISTS (SELECT * FROM Diagnostic LEFT JOIN rbDispanser ON rbDispanser.ID = Diagnostic.dispanser_id WHERE Diagnostic.event_id = Event.id AND rbDispanser.id IS NULL AND Diagnostic.deleted = 0)"
                cond.append(condDispanser)

            else:
                dispanserId = dispanserId.replace("None, ", "")
                condDispanser = "EXISTS (SELECT * FROM Diagnostic LEFT JOIN rbDispanser ON rbDispanser.ID = Diagnostic.dispanser_id WHERE Diagnostic.event_id = Event.id AND (rbDispanser.id IS NULL OR rbDispanser.id IN ({0})) AND Diagnostic.deleted = 0)".format(dispanserId)
                cond.append(condDispanser)

        self.addEqCond(cond, table, 'org_id', filter, 'LPUId')
        if filter.get('nonBase', False):
            cond.append(table['org_id'].ne(QtGui.qApp.currentOrgId()))
        mesCode = filter.get('mesCode', None)
        if mesCode is not None:
            if mesCode:
                condMes  = 'MES_id IN (SELECT id FROM mes.MES WHERE code LIKE %s)' % quote(undotLikeMask(mesCode))
                cond.append(condMes)
            else:
                cond.append(table['eventType_id'].name()+' IN (SELECT id FROM EventType WHERE EventType.mesRequired)')
                cond.append(table['MES_id'].isNull())
        csgCode = filter.get('csgCode', None)
        if (self.chkFilterEventCSG.isChecked() and csgCode) or self.chkFilterEventCSGDate.isChecked() or self.chkFilterEventCSGMKB.isChecked() or self.chkFilterCSGPayStatus.isChecked():
            tableEventCSG = db.table('Event_CSG')
            queryTable = queryTable.innerJoin(tableEventCSG, tableEventCSG['master_id'].eq(table['id']))
            if self.chkFilterEventCSG.isChecked() and csgCode:
                cond.append(tableEventCSG['CSGCode'].like(undotLikeMask(csgCode)))
            if self.chkFilterEventCSGDate.isChecked():
                csgBegDate = filter.get('csgBegDate', None)
                csgEndDate = filter.get('csgEndDate', None)
                if csgBegDate:
                    cond.append(db.joinAnd([tableEventCSG['endDate'].isNotNull(), tableEventCSG['endDate'].ge(csgBegDate)]))
                if csgEndDate:
                    cond.append(db.joinAnd([tableEventCSG['begDate'].isNotNull(), tableEventCSG['begDate'].le(csgEndDate)]))
            if self.chkFilterEventCSGMKB.isChecked():
                csgMKBFrom = filter.get('csgMKBFrom', u'A')
                csgMKBTo = filter.get('csgMKBTo', u'U')
                if csgMKBFrom or csgMKBTo:
                    if csgMKBFrom and not csgMKBTo:
                        csgMKBTo = u'U'
                    elif not csgMKBFrom and csgMKBTo:
                        csgMKBFrom = u'A'
                    cond.append('''EXISTS(SELECT Diagnosis.id
        FROM Diagnosis INNER JOIN Diagnostic ON Diagnostic.diagnosis_id=Diagnosis.id
        INNER JOIN rbDiagnosisType ON Diagnostic.diagnosisType_id=rbDiagnosisType.id
        WHERE Diagnostic.event_id = Event.id AND Diagnosis.deleted = 0 AND Diagnostic.deleted = 0 %s %s
        AND (rbDiagnosisType.code = '1'
        OR (rbDiagnosisType.code = '2' AND Diagnostic.person_id = Event.execPerson_id
        AND (NOT EXISTS (SELECT DC.id FROM Diagnostic AS DC
        INNER JOIN rbDiagnosisType AS DT ON DT.id = DC.diagnosisType_id WHERE DT.code = '1'
        AND DC.event_id = Event.id
        LIMIT 1)))))'''%((u'''AND Diagnosis.MKB LIKE '%s%%' '''% csgMKBFrom) if len(csgMKBFrom) == 3 else (u'''AND Diagnosis.MKB >= '%s' ''' % csgMKBFrom),
                         (u'''AND Diagnosis.MKB LIKE '%s%%' ''' % csgMKBTo) if len(csgMKBTo) == 3 else (u'''AND Diagnosis.MKB <= '%s' ''' % csgMKBTo)))
            if self.chkFilterCSGPayStatus.isChecked() and 'payStatusCodeCSG' in filter:
                payStatusFinanceCodeCSG = filter.get('payStatusFinanceCodeCSG', None)
                if payStatusFinanceCodeCSG:
                    payStatusCodeCSG = filter.get('payStatusCodeCSG', 0)
                    financeCodeCSG, financeIdCSG = self.getFinanceByIndex(payStatusFinanceCodeCSG)
                    mask  = getPayStatusMaskByCode(payStatusFinanceCodeCSG)
                    value = getPayStatusValueByCode(payStatusCodeCSG, financeCodeCSG)
                    cond.append('((%s & %d) = %d)' % (tableEventCSG['payStatus'].name(), mask, value))
        self.addEqCond(cond, table, 'result_id', filter, 'eventResultId')
        if filter.get('errorInDiagnostic', False):
            condErrInFinish = '(SELECT COUNT(*) FROM Diagnostic WHERE Diagnostic.event_id = Event.id AND diagnosisType_id=(SELECT id FROM rbDiagnosisType WHERE code=\'1\')) != 1'
            condErrInGroup  = 'EXISTS (SELECT * FROM Diagnostic WHERE Diagnostic.event_id = Event.id AND healthGroup_id IS NULL)'
            cond.append(db.joinOr([condErrInFinish, condErrInGroup]))
        eventInAccountItems = filter.get('eventInAccountItems', None)
        if eventInAccountItems is not None:
            tableAccountItem = db.table('Account_Item')
            queryTable = queryTable.leftJoin(tableAccountItem, [tableAccountItem['event_id'].eq(table['id']), tableAccountItem['deleted'].eq(0)])
            if eventInAccountItems == 0:
                cond.append(tableAccountItem['id'].isNotNull())
            else:
                cond.append(tableAccountItem['id'].isNull())
        payStatusFinanceCode = filter.get('payStatusFinanceCode', None)
        if payStatusFinanceCode:
            payStatusCode = filter.get('payStatusCode', 0)
            mask  = getPayStatusMaskByCode(payStatusFinanceCode)
            value = getPayStatusValueByCode(payStatusCode, payStatusFinanceCode)
            cond.append('((%s & %d) = %d)' % (table['payStatus'].name(), mask, value))
        if filter['filterVisits']:
            queryTable = queryTable.innerJoin(tableVisit, tableVisit['event_id'].eq(table['id']))
            cond.append(tableVisit['deleted'].eq(0))
            visitScene = filter.get('visitScene', None)
            if visitScene:
                cond.append(tableVisit['scene_id'].eq(visitScene))
            visitType = filter.get('visitType', None)
            if visitType:
                cond.append(tableVisit['visitType_id'].eq(visitType))
            visitProfile = filter.get('visitProfile', None)
            if visitProfile:
                cond.append(tableVisit['service_id'].eq(visitProfile))
        MKBFrom = filter.get('MKBFrom')
        MKBTo = filter.get('MKBTo')
        if MKBFrom or MKBTo:
            if MKBFrom and not MKBTo:
                MKBTo = u'U'
            elif not MKBFrom and MKBTo:
                MKBFrom = u'A'
            condTypeMKB = u''
            if filter.get('MKBisPreliminary'):
                condTypeMKB = u''' OR rbDiagnosisType.code = 7'''
            if filter.get('MKBisConcomitant') and not filter.get('MKBisPreliminary'):
                condTypeMKB = u''' OR rbDiagnosisType.code = 9'''
            elif filter.get('MKBisConcomitant') and filter.get('MKBisPreliminary'):
                condTypeMKB = u''' OR rbDiagnosisType.code = 11'''
            cond.append('''EXISTS(SELECT Diagnosis.id
FROM Diagnosis INNER JOIN Diagnostic ON Diagnostic.diagnosis_id=Diagnosis.id
INNER JOIN rbDiagnosisType ON Diagnostic.diagnosisType_id=rbDiagnosisType.id
WHERE Diagnostic.event_id = Event.id AND Diagnosis.deleted = 0 AND Diagnostic.deleted = 0 %s %s
AND (rbDiagnosisType.code = '1'
OR (rbDiagnosisType.code = '2' AND Diagnostic.person_id = Event.execPerson_id
AND (NOT EXISTS (SELECT DC.id FROM Diagnostic AS DC
INNER JOIN rbDiagnosisType AS DT ON DT.id = DC.diagnosisType_id WHERE DT.code = '1'
AND DC.event_id = Event.id
LIMIT 1)))%s))'''%((u'''AND Diagnosis.MKB >= '%s' ''' % MKBFrom),
                   (u'''AND Diagnosis.MKB <= '%s' ''' % MKBTo), condTypeMKB))
        if 'payStatusCodeVisit' in filter:
            if not filter['filterVisits']:
                queryTable = queryTable.innerJoin(tableVisit, tableVisit['event_id'].eq(table['id']))
                cond.append(tableVisit['deleted'].eq(0))
            payStatusFinanceCodeVisit = filter.get('payStatusFinanceCodeVisit', None)
            if payStatusFinanceCodeVisit:
                payStatusCodeVisit = filter.get('payStatusCodeVisit', 0)
                financeCode, financeId = self.getVisitFinanceByIndex(payStatusFinanceCodeVisit)
                mask  = getPayStatusMaskByCode(payStatusFinanceCodeVisit)
                value = getPayStatusValueByCode(payStatusCodeVisit, financeCode)
                cond.append('((%s & %d) = %d)' % (tableVisit['payStatus'].name(), mask, value))
                cond.append(tableVisit['finance_id'].eq(financeId))
        if 'jobTicketId' in filter:
            jobTicketId = filter['jobTicketId']
            tableAction = db.table('Action')
            tableActionProperty = db.table('ActionProperty')
            tableActionPropertyJobTicket = db.table('ActionProperty_Job_Ticket')
            subTableQuery = tableAction.leftJoin(tableActionProperty,
                                                 tableActionProperty['action_id'].eq(tableAction['id']))
            subTableQuery = subTableQuery.leftJoin(tableActionPropertyJobTicket,
                                                   tableActionPropertyJobTicket['id'].eq(tableActionProperty['id']))
            subCond = [tableAction['deleted'].eq(0),
                       tableActionProperty['deleted'].eq(0),
                       tableActionPropertyJobTicket['value'].eq(jobTicketId),
                       tableAction['event_id'].eq(table['id'])]
            cond.append(db.existsStmt(subTableQuery, subCond))
        payerId = filter.get('payerId', None)
        financeId = filter.get('financeId', None)
        if payerId or financeId:
            tableContract = db.table('Contract')
            queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(table['contract_id']))
        if payerId:
            cond.append(tableContract['payer_id'].eq(payerId))
        if financeId:
            cond.append(tableContract['finance_id'].eq(financeId))
        if 'contractId' in filter:
            cond.append(table['contract_id'].eq(filter['contractId']))
        if 'notExposedByOms' in filter and filter['notExposedByOms']:
            queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(table['contract_id']))
            cond.append("Contract.finance_id = 2 and NOT EXISTS(SELECT id FROM Account_Item WHERE event_id = Event.id limit 1)")
        if 'notExposed' in filter and filter['notExposed']:
            cond.append("Event.expose = 0")
        if 'begDate' and 'endDate' in filter:
            cond.append("Event.execDate >= '%s'" % filter['begDate'].toString('yyyy-MM-dd'))
            cond.append("Event.execDate < '%s'" % filter['endDate'].addDays(1).toString('yyyy-MM-dd'))
        if 'diseaseCharacter' in filter:
            cond.append('''EXISTS(SELECT Diagnosis.id
            FROM Diagnosis INNER JOIN Diagnostic ON Diagnostic.diagnosis_id=Diagnosis.id
            WHERE Diagnostic.event_id = Event.id AND Diagnosis.deleted = 0 AND Diagnostic.deleted = 0 AND Diagnostic.character_id = {})'''.format(filter['diseaseCharacter']))
        
        if 'eventActions' in filter:
            tableAction = db.table('Action')
            subCond = [tableAction['deleted'].eq(0),
                       tableAction['event_id'].eq(table['id']),
                       tableAction['actionType_id'].inlist(getActionTypeDescendants(filter['eventActions']))
                       ]
            if self.chkFilterEventActionsExclude.isChecked():
                cond.append(db.notExistsStmt(tableAction, subCond))
            else:
                cond.append(db.existsStmt(tableAction, subCond))

        
        visibleCond = []
        clientIds = filter.get('clientIds', None)
        hasRightOwnAreaOnly = self.hasRightOwnAreaOnly(clientIds)
        if QtGui.qApp.userHasRight(urRegVisibleOwnAreaEventsOnly) and hasRightOwnAreaOnly:
            cond.append(tableEventType['ignoreVisibleRights'].eq(1))
        elif QtGui.qApp.userHasRight(urRegVisibleOwnEventsParentOrgStructureOnly):
            orgStructureId = forceRef(db.translate('Person', 'id', QtGui.qApp.userId, 'orgStructure_id'))
            parentOrgStructure = getParentOrgStructureId(orgStructureId)
            orgStrinctureList = getOrgStructureDescendants(parentOrgStructure if parentOrgStructure else orgStructureId)
            cond.append(db.joinOr([tableExecPerson['orgStructure_id'].inlist(orgStrinctureList), tableEventType['ignoreVisibleRights'].eq(1)]))
        elif QtGui.qApp.userHasRight(urRegVisibleOwnEventsOrgStructureOnly):
            orgStructureId = forceRef(db.translate('Person', 'id', QtGui.qApp.userId, 'orgStructure_id'))
            orgStrinctureList = getOrgStructureDescendants(orgStructureId)
            cond.append(db.joinOr([tableExecPerson['orgStructure_id'].inlist(orgStrinctureList), tableEventType['ignoreVisibleRights'].eq(1)]))
        elif QtGui.qApp.userHasRight(urRegVisibleOwnEventsOnly):
            cond.append(db.joinOr([table['execPerson_id'].eq(QtGui.qApp.userId), tableEventType['ignoreVisibleRights'].eq(1)]))


        try:
            QtGui.QApplication.setOverrideCursor(QtGui.QCursor(Qt.WaitCursor))
            idList = db.getDistinctIdList(queryTable,
                                          table['id'].name(),
                                          cond,
                                          order)
            #                           ['execDate DESC', 'id'])
            self.tblEvents.setIdList(idList, posToId)
        finally:
            QtGui.QApplication.restoreOverrideCursor()

        hideClientInfo = 'clientIds' in filter and len(filter['clientIds']) == 1
        for i in xrange(4):
            #заменил setColumnHidden на showSection т.к. он устанавливал ширину столбца в 0
            #            self.tblEvents.setColumnHidden(i, hideClientInfo)
            header = self.tblEvents.horizontalHeader()
            if not hideClientInfo:
                header.showSection(i)
            else:
                header.hideSection(i)
        self.updateClientsListRequest = self.updateClientsListRequest or not hideClientInfo


    def getVisitFinanceByIndex(self, financeIndex):
        financeNames = [u'бюджет',  u'ОМС', u'ДМС', u'платн%', u'целев%']
        db = QtGui.qApp.db
        table = db.table('rbFinance')
        cond = [table['name'].like(financeNames[financeIndex-1])]
        record = db.getRecordEx(table, [table['code'], table['id']], cond)
        return forceInt(record.value('code')), forceInt(record.value('id'))


    def getEventFilterAsText(self):
        db = QtGui.qApp.db
        filter  = self.__eventFilter
        resList = []

        clientIds = filter.get('clientIds', None)
        if clientIds and len(clientIds) == 1:
            resList.append((u'пациент', getClientMiniInfo(clientIds[0])))
        elif clientIds is None:
            resList.append((u'список пациентов', u'полный'))
        else:
            resList.append((u'список пациентов', u'из вкладки'))

        tmpList = [
            ('begSetDateTime', u'Дата и время назначения с', forceString),
            ('endSetDateTime', u'Дата и время назначения по', forceString),
            ('begDate', u'Дата начала лечения с', forceString),
            ('endDate', u'Дата начала лечения по', forceString),
            ('orgStructureId', u'подразделение', getOrgStructureFullName),
            ('emptyExecDate', u'Пустая дата выполнения', lambda dummy: ''),
            ('begExecDateTime', u'Дата и время выполнения с', forceString),
            ('endExecDateTime', u'Дата и время выполнения по', forceString),
            ('begNextDate', u'Дата следующей явки с', forceString),
            ('endNextDate', u'Дата следующей явки по', forceString),
            ('eventTypeId', u'Тип обращения',
                lambda id: getEventName(id)),
            ('specialityId', u'Специальность',
                lambda id: forceString(db.translate('rbSpeciality', 'id', id, 'name'))),
            ('personId', u'Выполнил',
                lambda id: forceString(db.translate('vrbPersonWithSpeciality', 'id', id, 'name'))),
            ('dispanserObserved', u'Дисп.наблюдение', lambda dummy: ''),
            ('LPUId', u'ЛПУ', getOrganisationShortName),
            ('nonBase', u'Не базовое ЛПУ', lambda dummy: ''),
            ('eventResultId', u'Результат обращения',
                lambda id: forceString(db.translate('rbResult', 'id', id, 'name'))),
            ('errorInDiagnostic', u'Ошибки', lambda dummy: ''),
            ]
        for (key, title, ftm) in tmpList:
            convertFilterToTextItem(resList, filter, key, title, ftm)
        return '\n'.join([ ': '.join(item) for item in resList])


    def eventId(self, index):
        return self.tblEvents.itemId(index)


    def currentEventId(self):
        return self.tblEvents.currentItemId()

    def updateEventActions(self, eventId):
        orderBY = u'Action.id'
        for key, value in self.tblEventActions.model().headerSortingCol.items():
            if value:
                ASC = u'ASC'
            else:
                ASC = u'DESC'
            if key == 0:
                orderBY = u'directionDate %s' % ASC
            elif key == 1:
                orderBY = u'isUrgent %s' % ASC
            elif key == 2:
                orderBY = u'plannedEndDate %s' % ASC
            elif key == 3:
                orderBY = u'begDate %s' % ASC
            elif key == 4:
                orderBY = u'endDate %s' % ASC
            elif key == 5:
                orderBY = u'(select name from ActionType where id = actionType_id) %s' % ASC
            elif key == 6:
                orderBY = u'status %s' % ASC
            elif key == 7:
                orderBY = u'(select name from vrbPersonWithSpeciality where id = setPerson_id) %s' % ASC
            elif key == 8:
                orderBY = u'(select name from vrbPersonWithSpeciality where id = person_id) %s' % ASC
            elif key == 9:
                orderBY = u'Action.office %s' % ASC
            elif key == 10:
                orderBY = u'Action.note %s' % ASC
            elif key == 11:
                orderBY = u'Action.payStatus %s' % ASC
        db = QtGui.qApp.db
        tableAction = db.table('Action')
        tableActionType = db.table('ActionType')
        table = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
        idList = db.getIdList(table, 'Action.id', [tableAction['event_id'].eq(eventId),
                                                   tableAction['deleted'].eq(0),
                                                   tableActionType['deleted'].eq(0),
                                                   tableActionType['flatCode'].notlike(u'temperatureSheet')],
                              orderBY)
        self.tblEventActions.setIdList(idList)

    def updateEventVisits(self, eventId):
        orderBY = u'id'
        for key, value in self.tblEventVisits.model().headerSortingCol.items():
            if value:
                ASC = u'ASC'
            else:
                ASC = u'DESC'
            if key == 0:
                orderBY = u'(select name from rbScene where id = scene_id) %s' % ASC
            elif key == 1:
                orderBY = u'date %s' % ASC
            elif key == 2:
                orderBY = u'(select name from rbVisitType where id = visitType_id) %s' % ASC
            elif key == 3:
                orderBY = u'(select name from rbService where id = service_id) %s' % ASC
            elif key == 4:
                orderBY = u'(select name from vrbPersonWithSpecialityAndOrgStr where id = person_id) %s' % ASC
            elif key == 5:
                orderBY = u'isPrimary %s' % ASC
            elif key == 6:
                orderBY = u'payStatus %s' % ASC
        db = QtGui.qApp.db
        table = db.table('Visit')
        idList = db.getIdList(table, 'id', [table['event_id'].eq(eventId), table['deleted'].eq(0)], orderBY)
        self.tblEventVisits.setIdList(idList)

    def updateEventDiagnostics(self, eventId):
        db = QtGui.qApp.db

        tableDiagnostic = db.table('Diagnostic')
        tableRBDispanser = db.table('rbDispanser')
        table = tableDiagnostic.leftJoin(tableRBDispanser, tableRBDispanser['id'].eq(tableDiagnostic['dispanser_id']))
        cond = [
            table['event_id'].eq(eventId),
            table['deleted'].eq(0)]
        if self.chkFilterEventDispanser.isChecked() and self.cmbFilterEventDispanser.value():
            filterEventDispanser = self.cmbFilterEventDispanser.value()
            filterEvnDis = u'rbDispanser.ID IN ({0})'.format(filterEventDispanser)
            cond.append(filterEvnDis)

        orderBY = u'id'
        def inc():
            inc.counter += 1
            return inc.counter
        inc.counter = -1

        for key, value in self.tblEventDiagnostics.model().headerSortingCol.items():
            if value:
                ASC = u'ASC'
            else:
                ASC = u'DESC'
            if key == inc():
                orderBY = u'endDate %s' % ASC
            elif key == inc():
                orderBY = u'(select name from rbDiagnosisType where id = Diagnostic.diagnosisType_id) %s' % ASC
            elif key == inc():
                orderBY = u'(select name from rbHealthGroup where id = Diagnostic.healthGroup_id) %s' % ASC
            elif  key == inc():
                orderBY = u'(select concat_ws("+",MKB,MKBEx) from Diagnosis where id = Diagnostic.diagnosis_id) %s' % ASC
            elif QtGui.qApp.defaultMorphologyMKBIsVisible() and key == inc():
                orderBY = u'(select morphologyMKB from Diagnosis where id = Diagnostic.diagnosis_id) %s' % ASC
            elif key == inc():
                orderBY = u'(select name from rbDiseaseCharacter where id = Diagnostic.character_id) %s' % ASC
            elif key == inc():
                orderBY = u'(select name from rbDiseasePhases where id = Diagnostic.phase_id) %s' % ASC
            elif key == inc():
                orderBY = u'(select name from rbDiseaseStage where id = Diagnostic.stage_id) %s' % ASC
            elif key == inc():
                orderBY = u'(select name from rbDispanser where id = Diagnostic.dispanser_id) %s' % ASC
            elif key == inc():
                orderBY = u'hospital %s' % ASC
            elif key == inc():
                orderBY = u'(select name from rbTraumaType where id = Diagnostic.traumaType_id) %s' % ASC
            elif key == inc():
                orderBY = u'(select name from vrbPerson where id = Diagnostic.person_id) %s' % ASC
            elif key == inc():
                orderBY = u'(select name from rbSpeciality where id = Diagnostic.speciality_id) %s' % ASC
            elif key == inc():
                orderBY = u'(select name from rbDiagnosticResult where id = Diagnostic.result_id) %s' % ASC
            elif key == inc():
                orderBY = u'notes %s' % ASC
            elif key == inc():
                orderBY = u'freeInput %s' % ASC


        idList = db.getIdList(table, 'Diagnostic.id', cond, orderBY)
        self.tblEventDiagnostics.setIdList(idList)

    def updateEventInfo(self, eventId):
        db = QtGui.qApp.db
        record = db.getRecord('Event', ['createDatetime','createPerson_id', 'modifyDatetime', 'modifyPerson_id', 'eventType_id', 'externalId', 'client_id', 'payStatus', 'note', 'prevEvent_id', 'relegateOrg_id', 'srcDate', 'srcNumber'], eventId)
        if record:
            createDatetime = dateTimeToString(record.value('createDatetime').toDateTime())
            createPersonId = forceRef(record.value('createPerson_id'))
            modifyDatetime = dateTimeToString(record.value('modifyDatetime').toDateTime())
            modifyPersonId = forceRef(record.value('modifyPerson_id'))
            eventTypeId    = forceRef(record.value('eventType_id'))
            externalId     = forceString(record.value('externalId'))
            clientId       = forceRef(record.value('client_id'))
            note           = forceString(record.value('note'))
            payStatus      = forceInt(record.value('payStatus'))
            prevEventId    = forceRef(record.value('prevEvent_id'))
            relegateOrgId = forceRef(record.value('relegateOrg_id'))
            eventSrcDate = forceDate(record.value('srcDate')).toString('dd.MM.yyyy')
            eventSrcNumber = forceString(record.value('srcNumber'))
        else:
            createDatetime = ''
            createPersonId = None
            modifyDatetime = ''
            modifyPersonId = None
            externalId     = ''
            clientId       = None
            note           = ''
            payStatus      = 0
            prevEventId    = None
            relegateOrgId = None
            eventSrcDate = ''
            eventSrcNumber = ''

        if not clientId:
            clientId = self.selectedClientId()
        self.updateClientInfo(clientId)
        if clientId:
            self.actSurveillancePlanningClients.setEnabled(bool(isSurveillanceActive(clientId, {}, {'begDate': QDate.currentDate()})))
            if eventId:
                self.actSurveillancePlanningClientsByEvent.setEnabled(bool(isSurveillanceActive(clientId, {'event_id': eventId}, {'begDate': QDate.currentDate(), 'event_id': eventId})))
        self.actEventEditClient.setEnabled(bool(clientId))
        self.actEventOpenClientVaccinationCard.setEnabled(bool(clientId) and QtGui.qApp.userHasAnyRight([urCanReadClientVaccination, urCanEditClientVaccination]))
        self.actCheckClientAttach.setEnabled(bool(clientId))
        self.actPortal_Doctor.setEnabled(bool(clientId))
        self.actEventRelationsClient.setEnabled(bool(clientId))
        self.actStatusObservationClientBrowserByEvent.setEnabled(bool(clientId) and QtGui.qApp.userHasAnyRight([urAdmin, urEditStatusObservationClient]))
        self.actCreateRelatedAction.setEnabled(bool(clientId))
        QtGui.qApp.setCurrentClientId(clientId)

        if eventId:
            self.updateEventDiagnostics(eventId)
            self.updateEventActions(eventId)
            self.updateEventVisits(eventId)
            context = getEventContext(eventTypeId)
            additionalCustomizePrintButton(self, self.btnEventPrint, context)
        else:
            self.tblEventDiagnostics.setIdList([])
            self.tblEventActions.setIdList([])
            self.tblEventVisits.setIdList([])

        self.modelEventExportFile.loadData(eventId)
        self.lblEventIdValue.setText(str(eventId) if eventId else '')

        if prevEventId:
            tableEvent = db.table('Event')
            tableEventType = db.table('EventType')
            prevEventRecord = db.getRecordEx(tableEvent.innerJoin(tableEventType, tableEvent['eventType_id'].eq((tableEventType['id']))), [tableEventType['name'], tableEvent['setDate']], [tableEvent['deleted'].eq(0), tableEvent['id'].eq(prevEventId)])
            if prevEventRecord:
                self.lblPrevEventInfo.setText(u'Продолжение обращения: %s от %s.'%(forceString(prevEventRecord.value('name')), forceDate(prevEventRecord.value('setDate')).toString('dd.MM.yyyy')))
        else:
            self.lblPrevEventInfo.setText('')

        self.lblEventExternalIdValue.setText(externalId)
        self.lblEventCreateDateTimeValue.setText(createDatetime)
        self.lblEventCreatePersonValue.setText(self.getPersonText(createPersonId))
        self.lblEventModifyDateTimeValue.setText(modifyDatetime)
        self.lblEventModifyPersonValue.setText(self.getPersonText(modifyPersonId))
        self.lblEventNoteValue.setText(note)
        self.lblEventPayStatusValue.setText(payStatusText(payStatus))
        self.lblEventRelegateOrgValue.setText(getOrganisationShortName(relegateOrgId))
        self.lblEventSrcDateValue.setText(eventSrcDate)
        self.lblEventSrcNumberValue.setText(eventSrcNumber)


    def getPersonText(self, personId):
        if personId:
            index = self.personInfo.searchId(personId)
            if index:
                return u' | '.join([val for val in [forceString(self.personInfo.getCode(index)),
                                                    forceString(self.personInfo.getName(index))] if val])
            else:
                return '{'+str(personId)+'}'
        else:
            return ''

    def updateFilterEventResultTable(self):
        if self.chkFilterEventPurpose.isChecked():
            purposeId = self.cmbFilterEventPurpose.value()
        else:
            purposeId = None
        if purposeId is None:
            if self.chkFilterEventType.isChecked():
                eventTypeId = self.cmbFilterEventType.value()
            else:
                eventTypeId = None
            if eventTypeId:
                purposeId = getEventPurposeId(eventTypeId)
        filter = ('eventPurpose_id=\'%d\'' % purposeId) if purposeId else ''
        self.cmbFilterEventResult.setTable('rbResult', False, filter)


    def updateAmbCardInfo(self):
        clientId = self.currentClientId()
        if clientId:
            clientSex, clientAge = getClientSexAge(clientId)
            self.tabAmbCardContent.setClientId(clientId, clientSex, clientAge)
        self.actCheckClientAttach.setEnabled(bool(clientId))
        self.actPortal_Doctor.setEnabled(bool(clientId))
        self.actAmbCardEditClient.setEnabled(bool(clientId))
        self.actAmbCardOpenClientVaccinationCard.setEnabled(bool(clientId) and QtGui.qApp.userHasAnyRight([urCanReadClientVaccination, urCanEditClientVaccination]))
        self.actAmbCardRelationsClient.setEnabled(bool(clientId))
        QtGui.qApp.setCurrentClientId(clientId)


    def editAction(self, actionId):
        dialog = CActionEditDialog(self)
        try:
            dialog.load(actionId)
            if dialog.exec_():
                return dialog.itemId()
            else:
                self.updateActionInfo(actionId)
                self.updateClientsListRequest = True
            return None
        finally:
            dialog.deleteLater()


    def _setActionsOrderByColumn(self, column):
        table = self.getCurrentActionsTable()
        table.setOrder(column)
        self.updateActionsList(self.__actionFilter, table.currentItemId())


    def updateActionsList(self, filter, posToId=None):
#        """
#            в соответствии с фильтром обновляет список действий (мероприятий).
#        """
        self.__actionFilter = filter
        db = QtGui.qApp.db
        tableAction = db.table('Action')
        currentTable = self.getCurrentActionsTable()
        order = currentTable.order() if currentTable.order() else ['execDate DESC', tableAction['id'].name()]
        optionPropertyIdList = []
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        tableActionProperty = db.table('ActionProperty')
        tableActionPropertyType = db.table('ActionPropertyType')
        queryTable = tableAction.innerJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
        queryTable = queryTable.leftJoin(tableEventType, db.joinAnd([tableEventType['id'].eq(tableEvent['eventType_id']), tableEventType['context'].ne(u'flag'), tableEventType['code'].ne(u'flag')]))
        actionTypeIdListInsp = []
        actionTypeIdListInsp.extend(getActionTypeIdListByFlatCode(u'inspection_disability%'))
        # actionTypeIdListInsp.extend(getActionTypeIdListByFlatCode(u'inspection_mse%'))
        cond = [tableAction['deleted'].eq(0),
                tableEvent['deleted'].eq(0),
                tableAction['actionType_id'].notInlist(actionTypeIdListInsp)]
        self.addEqCond(cond, tableAction, 'id', filter, 'id')
        self.addEqCond(cond, tableAction, 'createPerson_id', filter, 'createPersonId')
        self.addDateCond(cond, tableAction, 'createDatetime', filter, 'begCreateDate', 'endCreateDate')
        self.addEqCond(cond, tableAction, 'modifyPerson_id', filter, 'modifyPersonId')
        self.addDateCond(cond, tableAction, 'modifyDatetime', filter, 'begModifyDate', 'endModifyDate')
        if 'actionTypeServiceType' in filter:
            actionTypeServiceType = filter.get('actionTypeServiceType')
            tableActionTypeST = db.table('ActionType').alias('ActionTypeST')
            queryTable = queryTable.innerJoin(tableActionTypeST, tableActionTypeST['id'].eq(tableAction['actionType_id']))
            cond.append(tableActionTypeST['deleted'].eq(0))
            cond.append(tableActionTypeST['serviceType'].eq(actionTypeServiceType))
        if 'clientIds' in filter:
            clientIds = filter.get('clientIds')
            cond.append(tableEvent['client_id'].inlist(clientIds))
        if 'eventIds' in filter:
            eventIds = filter.get('eventIds')
            cond.append(tableAction['event_id'].inlist(eventIds))
        if 'actionId' in filter:
            actionId = filter.get('actionId')
            cond.append(tableAction['id'].eq(actionId))
        if 'isUrgent' in filter:
            cond.append(tableAction['isUrgent'].ne(0))
        if 'actionMKB' in filter:
            if 'actionMKBFrom' in filter:
                actionMKBFrom = filter.get('actionMKBFrom', None)
            if 'actionMKBTo' in filter:
                actionMKBTo = filter.get('actionMKBTo', None)
            if actionMKBFrom or actionMKBTo:
                if actionMKBFrom and not actionMKBTo:
                   actionMKBTo = u'U'
                elif not actionMKBFrom and actionMKBTo:
                    actionMKBFrom = u'A'
                cond.append(tableAction['MKB'].ge(actionMKBFrom))
                cond.append(tableAction['MKB'].le(actionMKBTo))
        self.addDateCond(cond, tableAction, 'directionDate', filter, 'begSetDate', 'endSetDate')
        self.addDateCond(cond, tableAction, 'plannedEndDate', filter, 'begPlannedEndDate', 'endPlannedEndDate')
        self.addDateTimeCond(cond, tableAction, 'begDate', filter, 'begBegDateTime', 'endBegDateTime')
        self.addDateTimeCond(cond, tableAction, 'endDate', filter, 'begExecDateTime', 'endExecDateTime')
        actionClass = self.getActionClassByTabIndex()
        if 'actionTypeId' in filter:
            actionTypeIdList = getActionTypeDescendants(filter['actionTypeId'], actionClass)
            cond.append(tableAction['actionType_id'].inlist(actionTypeIdList))
        if actionClass is not None and 'actionId' not in filter:
            cond.append(tableAction['actionType_id'].name()+' IN (SELECT ActionType.id FROM ActionType WHERE ActionType.class=%d)' % actionClass)
# сделано без учета значений value в таблицах ActionProperty_Double, ActionProperty_Action и т.п., учитывается наличие записи в ActionProperty, т.к. считается, что при не заполнении не создается запись в ActionProperty.
        takenTissueJournal = filter.get('takenTissueJournal')
        if takenTissueJournal is not None:
            if takenTissueJournal:
                cond.append(tableAction['takenTissueJournal_id'].isNotNull())
            else:
                cond.append(tableAction['takenTissueJournal_id'].isNull())
        if self.chkTakeIntoAccountProperty.isChecked(): #по значению
            optionPropertyIdList, optionQueryTableList = self.getDataOptionPropertyChecked()
            if self.chkFilledProperty.isChecked() and not self.chkThresholdPenaltyGrade.isChecked():
                if filter.get('booleanFilledProperty'):
                    queryTable = queryTable.leftJoin(tableActionProperty, [tableActionProperty['action_id'].eq(tableAction['id']), tableActionProperty['deleted'].eq(0)])
                    joinCond = [tableActionPropertyType['deleted'].eq(0),
                                tableActionPropertyType['id'].eq(tableActionProperty['type_id'])]
                    if filter.get('listPropertyCond'):
                        existsCond = []
                        for optionPropertyId in optionPropertyIdList:
                            if filter.get('indexFilledProperty') != 0:
                                existsCond.append(u'''EXISTS(SELECT AP.id
                                                            FROM ActionPropertyType AS APT
                                                            INNER JOIN ActionProperty AS AP ON AP.type_id = APT.id
                                                            WHERE APT.actionType_id = Action.actionType_id
                                                            AND AP.action_id = Action.id
                                                            AND AP.deleted = 0
                                                            AND APT.deleted = 0
                                                            AND APT.id = %s
                                                            LIMIT 1)'''%(str(optionPropertyId)))
                            else:
                                existsCond.append(u'''NOT EXISTS(SELECT AP.id
                                                            FROM ActionPropertyType AS APT
                                                            INNER JOIN ActionProperty AS AP ON AP.type_id = APT.id
                                                            WHERE APT.actionType_id = Action.actionType_id
                                                            AND AP.action_id = Action.id
                                                            AND AP.deleted = 0
                                                            AND APT.deleted = 0
                                                            AND APT.id = %s
                                                            LIMIT 1)'''%(str(optionPropertyId)))
                        if filter.get('indexFilledProperty') == 2: #по значению
                            queryTable = queryTable.innerJoin(tableActionPropertyType, tuple(joinCond))
                            cond.append(tableActionProperty['id'].isNotNull())
                            cond.append(db.joinAnd(existsCond))
                            for optionQueryTable in optionQueryTableList:
                                queryTable = queryTable.leftJoin(optionQueryTable[0][1], [optionQueryTable[0][1]['action_id'].eq(tableAction['id']), optionQueryTable[0][1]['deleted'].eq(0), optionQueryTable[0][1]['type_id'].eq(optionQueryTable[0][2])])
                                queryTable = queryTable.innerJoin(optionQueryTable[0][0], optionQueryTable[1])
                        elif filter.get('indexFilledProperty') == 1: #Да
                            queryTable = queryTable.innerJoin(tableActionPropertyType, tuple(joinCond))
                            cond.append(tableActionProperty['id'].isNotNull())
                            cond.append(db.joinAnd(existsCond))
                        elif filter.get('indexFilledProperty') == 0: #Нет
                            queryTable = queryTable.leftJoin(tableActionPropertyType, tuple(joinCond))
                            cond.append(db.joinAnd(existsCond))
                    else:
                        if optionPropertyIdList:
                            joinCond.append(tableActionPropertyType['id'].inlist(optionPropertyIdList))
                        if filter.get('indexFilledProperty') == 2: #по значению
                            condOr = []
                            queryTable = queryTable.innerJoin(tableActionPropertyType, tuple(joinCond))
                            for optionQueryTable in optionQueryTableList:
                                queryTable = queryTable.leftJoin(optionQueryTable[0][1], [optionQueryTable[0][1]['action_id'].eq(tableAction['id']), optionQueryTable[0][1]['deleted'].eq(0), optionQueryTable[0][1]['type_id'].eq(optionQueryTable[0][2])])
                                queryTable = queryTable.leftJoin(optionQueryTable[0][0], optionQueryTable[1])
                                condOr.append(optionQueryTable[1][1])
                            cond.append(tableActionProperty['id'].isNotNull())
                            if condOr:
                                cond.append(db.joinOr(condOr))
                        elif filter.get('indexFilledProperty') == 1: #Да
                            queryTable = queryTable.innerJoin(tableActionPropertyType, tuple(joinCond))
                            for optionQueryTable in optionQueryTableList:
                                tablePropertyType = optionQueryTable[0][0]
                                queryTable = queryTable.leftJoin(tablePropertyType, [tablePropertyType['id'].eq(tableActionProperty['id']), tablePropertyType['value'].isNotNull()])
                            cond.append(tableActionProperty['id'].isNotNull())
                        elif filter.get('indexFilledProperty') == 0: #Нет
                            queryTable = queryTable.leftJoin(tableActionPropertyType, tuple(joinCond))
                            cond.append(db.joinOr([tableActionProperty['id'].isNull(),
                                        u'''NOT EXISTS(SELECT AP.id
                                        FROM ActionPropertyType AS APT
                                        INNER JOIN ActionProperty AS AP ON AP.type_id = APT.id
                                        WHERE APT.actionType_id = Action.actionType_id
                                        AND AP.action_id = Action.id
                                        AND AP.deleted = 0
                                        AND APT.deleted = 0
                                        AND APT.id IN (%s)
                                        LIMIT 1)'''%(u','.join(str(optionPropertyId) for optionPropertyId in optionPropertyIdList))]))
            elif not self.chkThresholdPenaltyGrade.isChecked():
                queryTable = queryTable.innerJoin(tableActionPropertyType, tableActionPropertyType['actionType_id'].eq(tableAction['actionType_id']))
                queryTable = queryTable.innerJoin(tableActionProperty, tableActionProperty['action_id'].eq(tableAction['id']))
                cond.append(tableActionProperty['deleted'].eq(0))
                cond.append(tableActionPropertyType['deleted'].eq(0))
            if self.chkThresholdPenaltyGrade.isChecked() and ('thresholdPenaltyGrade' in filter):
                filterPenaltyGrade = filter.get('thresholdPenaltyGrade')
                if filterPenaltyGrade:
                    whereOptionPropertyId = u''
                    if self.chkFilledProperty.isChecked():
                        if optionPropertyIdList != []:
                            strPropertyIdList = u''
                            col =len(optionPropertyIdList) - 1
                            for propertyId in optionPropertyIdList:
                                strPropertyIdList += forceString(propertyId)
                                col -= 1
                                if col > 0:
                                    strPropertyIdList +=  u', '
                            whereOptionPropertyId = u'(APT.id IN (%s)) AND ' % (strPropertyIdList)
                    cond.append(u'SELECT SUM(APT.penalty) >= %s FROM ActionPropertyType AS APT WHERE %s(APT.id NOT IN (SELECT AP.type_id FROM ActionProperty AS AP WHERE AP.action_id = Action.id AND AP.deleted = 0 GROUP BY AP.type_id) AND (APT.actionType_id = Action.actionType_id))' % (filterPenaltyGrade, whereOptionPropertyId))
        addTableSetPerson = False
        addTableExecPerson = False
        if 'setPersonId' in filter:
            if 'setPersonSNILS' in filter:
                if not addTableSetPerson:
                    addTableSetPerson = True
                    tablePerson = db.table('Person')
                    queryTable = queryTable.join(tablePerson, tablePerson['id'].eq(tableAction['setPerson_id']))
                rec = db.getRecordEx(tablePerson, [tablePerson['SNILS']], [tablePerson['id'].eq(filter['setPersonId'])])
                setPersonSNILS = forceString(rec.value('SNILS')) if rec else None
                cond.append(tablePerson['SNILS'].eq(setPersonSNILS))
            else:
                cond.append(tableAction['setPerson_id'].eq(filter['setPersonId']))
        else:
            if 'setSpecialityId' in filter:
                if not addTableSetPerson:
                    addTableSetPerson = True
                    tablePerson = db.table('Person')
                    queryTable = queryTable.join(tablePerson, tablePerson['id'].eq(tableAction['setPerson_id']))
                cond.append(tableAction['setPerson_id'].isNotNull())
                cond.append(tablePerson['speciality_id'].eq(filter['setSpecialityId']))
            if 'actionSetOrgStructureId' in filter:
                if not addTableSetPerson:
                    addTableSetPerson = True
                    tablePerson = db.table('Person')
                    queryTable = queryTable.join(tablePerson, tablePerson['id'].eq(tableAction['setPerson_id']))
                actionSetOrgStructureId = filter['actionSetOrgStructureId']
                actionSetOrgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', actionSetOrgStructureId) if actionSetOrgStructureId else []
                cond.append(tableAction['setPerson_id'].isNotNull())
                cond.append(tablePerson['orgStructure_id'].isNotNull())
                cond.append(tablePerson['orgStructure_id'].inlist(actionSetOrgStructureIdList))
        if 'execPersonId' in filter:
            execPersonId = filter['execPersonId']
            if execPersonId == -1:
                cond.append(tableAction['person_id'].isNull())
            else:
                if 'execPersonSNILS' in filter:
                    if not addTableExecPerson:
                        addTableExecPerson = True
                        tablePersonExec = db.table('Person').alias('PersonExec')
                        queryTable = queryTable.join(tablePersonExec,
                                                     tablePersonExec['id'].eq(tableAction['person_id']))
                    rec = db.getRecordEx(tablePersonExec, [tablePersonExec['SNILS']],
                                         [tablePersonExec['id'].eq(filter['execPersonId'])])
                    execPersonSNILS = forceString(rec.value('SNILS')) if rec else None
                    cond.append(tablePersonExec['SNILS'].eq(execPersonSNILS))
                else:
                    cond.append(tableAction['person_id'].eq(execPersonId))
        else:
            if 'execSetOrgStructureId' in filter:
                    if not addTableExecPerson:
                        addTableExecPerson = True
                        tablePersonExec = db.table('Person').alias('PersonExec')
                        queryTable = queryTable.join(tablePersonExec, tablePersonExec['id'].eq(tableAction['person_id']))
                    execSetOrgStructureId = filter['execSetOrgStructureId']
                    execSetOrgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', execSetOrgStructureId) if execSetOrgStructureId else []
                    cond.append(tableAction['person_id'].isNotNull())
                    cond.append(tablePersonExec['orgStructure_id'].isNotNull())
                    cond.append(tablePersonExec['orgStructure_id'].inlist(execSetOrgStructureIdList))
            if 'execSpecialityId' in filter:
                    if not addTableExecPerson:
                        addTableExecPerson = True
                        tablePersonExec = db.table('Person').alias('PersonExec')
                        queryTable = queryTable.join(tablePersonExec, tablePersonExec['id'].eq(tableAction['person_id']))
                    cond.append(tableAction['person_id'].isNotNull())
                    cond.append(tablePersonExec['speciality_id'].eq(filter['execSpecialityId']))
        if 'assistantId' in filter:
            assistantId = filter['assistantId']
            if assistantId == -1:
                cond.append(tableAction['assistant_id'].isNull())
            else:
                cond.append(tableAction['assistant_id'].eq(assistantId))

        if filter.get('uncoordinated'):
            tableActionType = db.table('ActionType')
            queryTable = queryTable.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
            cond.append(tableActionType['deleted'].eq(0))
            cond.append(tableActionType['isRequiredCoordination'].eq(1))
            cond.append(tableAction['coordDate'].isNull())
        self.addEqCond(cond, tableAction, 'status', filter, 'status')
        orgId = filter.get('orgId', None)
        if orgId:
            cond.append(tableAction['org_id'].eq(orgId))
        payStatusFinanceCode = filter.get('payStatusFinanceCode', None)
        if payStatusFinanceCode:
            payStatusCode = filter.get('payStatusCode', 0)
            mask  = getPayStatusMaskByCode(payStatusFinanceCode)
            value = getPayStatusValueByCode(payStatusCode, payStatusFinanceCode)
            cond.append('((%s & %d) = %d)' % (tableAction['payStatus'].name(), mask, value))
        if 'actionJobTicketId' in filter:
            jobTicketId = filter['actionJobTicketId']
            locTableActionProperty = db.table('ActionProperty').alias('SubActionProperty')
            tableActionPropertyJobTicket = db.table('ActionProperty_Job_Ticket')
            subTableQuery = locTableActionProperty.leftJoin(tableActionPropertyJobTicket,
                                                   tableActionPropertyJobTicket['id'].eq(locTableActionProperty['id']))
            subCond = [locTableActionProperty['deleted'].eq(0),
                       tableActionPropertyJobTicket['value'].eq(jobTicketId),
                       locTableActionProperty['action_id'].eq(tableAction['id'])]
            cond.append(db.existsStmt(subTableQuery, subCond))
        if 'financeId' in filter:
            financeId = filter['financeId']
            if financeId:
                cond.append(tableAction['finance_id'].eq(financeId))
            else:
                cond.append(tableAction['finance_id'].isNull())

        payerId = filter.get('payerId')
        if payerId:
            tableContract = db.table('Contract')
            queryTable = queryTable.leftJoin(tableContract,
                                             'IF(%s, %s, %s)' % (
                                                tableAction['contract_id'].isNotNull(),
                                                tableContract['id'].eq(tableAction['contract_id']),
                                                tableContract['id'].eq(tableEvent['contract_id']),
                                                                )

                                             )
            cond.append(tableContract['payer_id'].eq(payerId))

        if 'contractId' in filter:
            contractId = filter['contractId']
            if contractId:
                cond.append(tableAction['contract_id'].eq(contractId))
            else:
                cond.append(tableAction['contract_id'].isNull())

        if 'actionExportStatus' in filter:
            actionExportStatus = filter.get('actionExportStatus', None)
            actionExportSystem = filter.get('actionExportSystem', None)
            tableActionExport = db.table('Action_Export')
            actionExportCond = [ tableActionExport['master_id'].eq(tableAction['id']),
                                 tableActionExport['success'].eq(1),
                               ]
            if actionExportSystem:
                actionExportCond.append(tableActionExport['system_id'].eq(actionExportSystem))
            queryTable = queryTable.leftJoin(tableActionExport,
                                             actionExportCond
                                            )
            if actionExportStatus == 0:
                cond.append(tableActionExport['id'].isNotNull())
            else:
                    cond.append(tableActionExport['id'].isNull())
        
        if 'attachedFile' in filter:
            tableActionFileAttach = db.table('Action_FileAttach')
            queryTable = queryTable.leftJoin(tableActionFileAttach, (tableActionFileAttach['master_id'].eq(tableAction['id']), tableActionFileAttach['deleted'].eq(0)))

            if 'ActionFileAttach_id' in filter:
                attach_file_id = filter.get('ActionFileAttach_id',0)
                cond.append(tableActionFileAttach['id'].eq(attach_file_id))
            else:
                attachedFile = filter.get('attachedFile', None)
                cond.append('''Action_FileAttach.id IS {}NULL'''.format("" if attachedFile != 0 else "NOT "))

                if 'typeDoc' in filter:
                    typeDoc = filter.get('typeDoc', None)
                    if attachedFile == 0:
                        if typeDoc == u'Есть xml':
                            cond.append("Action_FileAttach.path LIKE '%.xml'")
                        elif typeDoc == u'Есть только pdf':
                            cond.append("Action_FileAttach.path LIKE '%.pdf'")
                            cond.append("NOT EXISTS(SELECT NULL FROM Action_FileAttach afa WHERE afa.master_id = Action.id and afa.deleted = 0 and afa.path like '%.xml')")

                if 'signed' in filter:
                    signedIndex = filter.get('signed', 0)
                    if signedIndex == 1:
                        cond.append(tableActionFileAttach['respSigner_id'].isNull())
                    elif signedIndex == 2:
                        cond.append(tableActionFileAttach['orgSigner_id'].isNull())
                    elif signedIndex == 3:
                        cond.append(tableActionFileAttach['orgSigner_id'].isNotNull())
                    elif signedIndex == 4:
                        cond.append(tableActionFileAttach['respSigner_id'].isNotNull())
                        cond.append(tableActionFileAttach['orgSigner_id'].isNull())
                    elif signedIndex == 5:
                        cond.append(db.joinOr([tableActionFileAttach['respSigner_id'].isNull(),
                                               tableActionFileAttach['orgSigner_id'].isNull()]))
                    elif signedIndex == 6:
                        cond.append(tableActionFileAttach['respSigner_id'].isNotNull())

                if 'exportSuitable' in filter:
                    tableActionTypeIT = db.table('ActionType').alias('ActionTypeIT')
                    tableActionTypeIdent = db.table('ActionType_Identification')
                    tableAccountingSystem = db.table('rbAccountingSystem')
                    queryTable = queryTable.innerJoin(tableActionTypeIT, tableActionTypeIT['id'].eq(tableAction['actionType_id']))
                    queryTable = queryTable.innerJoin(tableActionTypeIdent, tableActionTypeIdent['master_id'].eq(tableActionTypeIT['id']))
                    queryTable = queryTable.innerJoin(tableAccountingSystem, tableAccountingSystem['id'].eq(tableActionTypeIdent['system_id']))
                    cond.append(tableActionTypeIdent['deleted'].eq(0))
                    cond.append(tableAccountingSystem['code'].contain('n3.medDocumentType.'))

        if 'Client' in order:
            tableClient = db.table('Client')
            queryTable = queryTable.leftJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))

        if 'vrbSetPersonWithSpeciality.name' in order:
            tableSetPerson = db.table('vrbPersonWithSpeciality').alias('vrbSetPersonWithSpeciality')
            queryTable = queryTable.leftJoin(tableSetPerson, tableSetPerson['id'].eq(tableAction['setPerson_id']))

        if 'vrbPersonWithSpeciality.name' in order:
            tablePersonSP = db.table('vrbPersonWithSpeciality')
            queryTable = queryTable.leftJoin(tablePersonSP, tablePersonSP['id'].eq(tableAction['person_id']))

        if 'rbFinance.code' in order:
            tableFinance = db.table('rbFinance')
            queryTable = queryTable.leftJoin(tableFinance, tableFinance['id'].eq(tableAction['finance_id']))

        if 'vrbContract.code' in order:
            tableVRBContract = db.table('vrbContract')
            queryTable = queryTable.leftJoin(tableVRBContract, tableVRBContract['id'].eq(tableAction['contract_id']))


        # права на видимость мероприятий
        clientIds = filter.get('clientIds', None)
        hasRightOwnAreaOnly = self.hasRightOwnAreaOnly(clientIds)
        visibleCond = []
        if (QtGui.qApp.userHasAnyRight([urRegVisibleSetOwnActionsParentOrgStructureOnly, urRegVisibleSetOwnActionsOrgStructureOnly])
            or (QtGui.qApp.userHasRight(urRegVisibleOwnAreaActionsOnly) and hasRightOwnAreaOnly)) and not addTableSetPerson:
            tablePerson = db.table('Person')
            queryTable = queryTable.join(tablePerson, tablePerson['id'].eq(tableAction['setPerson_id']))
        if not (QtGui.qApp.userHasRight(urRegVisibleOwnAreaActionsOnly) and hasRightOwnAreaOnly):
            if QtGui.qApp.userHasRight(urRegVisibleSetOwnActionsParentOrgStructureOnly):
                orgStructureId = forceRef(db.translate('Person', 'id', QtGui.qApp.userId, 'orgStructure_id'))
                parentOrgStructure = getParentOrgStructureId(orgStructureId)
                orgStrinctureList = getOrgStructureDescendants(parentOrgStructure if parentOrgStructure else orgStructureId)
                visibleCond.append(tablePerson['orgStructure_id'].inlist(orgStrinctureList))
            elif QtGui.qApp.userHasRight(urRegVisibleSetOwnActionsOrgStructureOnly):
                orgStructureId = forceRef(db.translate('Person', 'id', QtGui.qApp.userId, 'orgStructure_id'))
                orgStrinctureList = getOrgStructureDescendants(orgStructureId)
                visibleCond.append(tablePerson['orgStructure_id'].inlist(orgStrinctureList))
            elif QtGui.qApp.userHasRight(urRegVisibleSetOwnActionsOnly):
                visibleCond.append(tableAction['setPerson_id'].eq(QtGui.qApp.userId))

        if (QtGui.qApp.userHasAnyRight([urRegVisibleExecOwnActionsParentOrgStructureOnly, urRegVisibleExecOwnActionsOrgStructureOnly])
            or (QtGui.qApp.userHasRight(urRegVisibleOwnAreaActionsOnly) and hasRightOwnAreaOnly)) and not addTableExecPerson:
            tablePersonExec = db.table('Person').alias('PersonExec')
            queryTable = queryTable.join(tablePersonExec, tablePersonExec['id'].eq(tableAction['person_id']))
        if not (QtGui.qApp.userHasRight(urRegVisibleOwnAreaActionsOnly) and hasRightOwnAreaOnly):
            if QtGui.qApp.userHasRight(urRegVisibleExecOwnActionsParentOrgStructureOnly):
                orgStructureId = forceRef(db.translate('Person', 'id', QtGui.qApp.userId, 'orgStructure_id'))
                parentOrgStructure = getParentOrgStructureId(orgStructureId)
                orgStrinctureList = getOrgStructureDescendants(parentOrgStructure if parentOrgStructure else orgStructureId)
                visibleCond.append(tablePersonExec['orgStructure_id'].inlist(orgStrinctureList))
            elif QtGui.qApp.userHasRight(urRegVisibleExecOwnActionsOrgStructureOnly):
                orgStructureId = forceRef(db.translate('Person', 'id', QtGui.qApp.userId, 'orgStructure_id'))
                orgStrinctureList = getOrgStructureDescendants(orgStructureId)
                visibleCond.append(tablePersonExec['orgStructure_id'].inlist(orgStrinctureList))
            elif QtGui.qApp.userHasRight(urRegVisibleExecOwnActionsOnly):
                visibleCond.append(tableAction['person_id'].eq(QtGui.qApp.userId))

        if visibleCond:
            # tableEventType = db.table('EventType')
            # queryTable = queryTable.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
            tableActionTypeIgnore = db.table('ActionType').alias('ATIgnore')
            queryTable = queryTable.innerJoin(tableActionTypeIgnore, tableActionTypeIgnore['id'].eq(tableAction['actionType_id']))
            visibleCond.append(tableActionTypeIgnore['ignoreVisibleRights'].eq(1))
            visibleCond.append(tableEventType['ignoreVisibleRights'].eq(1))
            cond.append(tableActionTypeIgnore['deleted'].eq(0))
            cond.append(db.joinOr(visibleCond))

        idList = []
        try:
            QtGui.QApplication.setOverrideCursor(QtGui.QCursor(Qt.WaitCursor))
            idList = db.getDistinctIdList(queryTable,
                           tableAction['id'].name(),
                           cond, order)
        finally:
            QtGui.QApplication.restoreOverrideCursor()

        if 'actionId' in filter and len(idList) > 0:
            # если фильтр по Action.id, то автоматический переход на вкладку класса действия
            query = db.query('SELECT ActionType.class'
                             ' FROM ActionType'
                             ' JOIN Action ON ActionType.id = Action.actionType_id'
                             ' WHERE Action.id = %d AND ActionType.deleted = 0' % idList[0])
            query.next()
            actionClass = forceInt(query.value(0))
            self.tabWidgetActionsClasses.setCurrentIndex(actionClass)
            table = self.getActionsTableByClass(actionClass)
        else:
            table = self.getCurrentActionsTable()

        tableMC = self.getCurrentExpertMedicalCommissionTable()
        table.setIdList(idList, posToId)
        hideClientInfo = 'clientIds' in filter and len(filter['clientIds']) == 1
        for i in range(3):
            table.setColumnHidden(i, hideClientInfo)
            tableMC.setColumnHidden(i, hideClientInfo)
        self.updateClientsListRequest = self.updateClientsListRequest or not hideClientInfo

    def hasRightOwnAreaOnly(self, clientIds):
        db = QtGui.qApp.db
        personId = QtGui.qApp.userId
        hasRight = False
        if clientIds:
            for clientId in clientIds:
                idList = []
                records = db.getRecordList('Person_Order', 'orgStructure_id', 'deleted = 0 AND master_id = {0} AND type = 6 AND validToDate IS NULL'.format(personId))
                personOrgStructureList = []
                for record in records:
                    if record:
                        orgStructureDescendants = getOrgStructureDescendants(forceInt(record.value('orgStructure_id')))
                        personOrgStructureList += orgStructureDescendants
                personOrgStructureSet = set(personOrgStructureList)
                if clientId:
                    tableClientAttach = db.table('ClientAttach')
                    stmt = u"""
                    SELECT MAX(ClientAttach.id)
                    FROM ClientAttach
                    INNER JOIN rbAttachType ON rbAttachType.id = ClientAttach.attachType_id
                    WHERE ClientAttach.client_id = {0}
                    AND ClientAttach.deleted = 0
                    AND ClientAttach.endDate IS NULL
                    AND NOT rbAttachType.TEMPORARY AND {1}
                    """.format(clientId, tableClientAttach['orgStructure_id'].inlist(personOrgStructureSet))
                    query = db.query(stmt)
                    if query.first():
                        attachRecord=query.record()
                        if forceBool(attachRecord.value('MAX(ClientAttach.id)')):
                            hasRight = True
                        else:
                            stmt2 = u"""
                            SELECT IF(ClientAttach.endDate IS NULL, 1, 0) AS notHasEnd
                            FROM ClientAttach
                            INNER JOIN rbAttachType ON rbAttachType.id = ClientAttach.attachType_id
                            WHERE ClientAttach.client_id = {0}
                            AND ClientAttach.deleted = 0
                            AND NOT rbAttachType.TEMPORARY
                            """.format(clientId)
                            query2 = db.query(stmt2)
                            if query2.size() == 0:
                                hasRight = True
                            else:
                                notHasEnd = False
                                if query2.next:
                                    attachRec = query.record()
                                    if forceInt(attachRec.value('notHasEnd')):
                                        notHasEnd = True
                                hasRight = not notHasEnd
                else:
                    hasRight = True
                return hasRight
        else:
            return hasRight

    def getActionFilterAsText(self):
        db = QtGui.qApp.db
        filter  = self.__actionFilter
        resList = []

        actionsFilterType = filter['actionsFilterType']
        if actionsFilterType in (0, 1):
            clientIds = filter.get('clientIds', None)
            if clientIds and len(clientIds) == 1:
                resList.append((u'пациент', getClientMiniInfo(clientIds[0])))
            elif clientIds and len(clientIds) > 1:
                resList.append((u'список пациентов', u'из вкладки'))
        elif actionsFilterType in (2, 3):
            clientIds = self.__eventFilter.get('clientIds', None)
            if clientIds and len(clientIds) == 1:
                resList.append((u'пациент', getClientMiniInfo(clientIds[0])))
            elif clientIds and len(clientIds) > 1:
                resList.append((u'список пациентов', u'по списку осмотров'))
        else:
            resList.append((u'список пациентов', u'полный'))

        tmpList = [
            ('begSetDate', u'Дата назначения с', forceString),
            ('endSetDate', u'Дата назначения по', forceString),
            ('actionTypeId', u'Тип мероприятия',
                lambda id: forceString(db.translate('ActionType', 'id', id, 'name'))),
            ('setSpecialityId', u'Специальность назначившего',
                lambda id: forceString(db.translate('rbSpeciality', 'id', id, 'name'))),
            ('personId', u'Назначил',
                lambda id: forceString(db.translate('vrbPersonWithSpeciality', 'id', id, 'name'))),
            ('isUrgent',   u'Срочно', lambda dummy: u'+'),
            ('begPlannedEndDate', u'Плановая дата выполнения с', forceString),
            ('endPlannedEndDate', u'Плановая дата окончания по', forceString),
            ('begExecDateTime', u'Дата и время выполнения с', forceString),
            ('endExecDateTime', u'Дата и время выполнения по', forceString),
            ]
        for (x, y, z) in tmpList:
            convertFilterToTextItem(resList, filter, x, y, z)
        return '\n'.join([ ': '.join(item) for item in resList])


    def getCurrentActionsTable(self):
        index = self.tabWidgetActionsClasses.currentIndex()
        if index == 4:
            # вкладка со всеми типами действия - не отдельный класс,
            # поэтому ей не место в getActionsTableByClass
            return self.tblActionsAll
        return self.getActionsTableByClass(index)


    def getActionClassByTabIndex(self):
        """Определяет класс типа действия по текущей вкладке в Обслуживании"""
        # type: () -> Optional[int]
        index = self.tabWidgetActionsClasses.currentIndex()
        if index == 4: # вкладке "все", не является классом
            return None
        return index


    def getActionsTableByClass(self, class_):
        return [self.tblActionsStatus, self.tblActionsDiagnostic, self.tblActionsCure, self.tblActionsMisc, ][class_]


    def getCurrentExpertMedicalCommissionTable(self):
        index = self.tabExpertMedicalCommissionWidget.currentIndex()
        return [self.tblExpertDirectionsMC, self.tblExpertProtocolsMC, self.tblExpertMedicalSocialInspection][index]


    def currentActionId(self):
        return self.getCurrentActionsTable().currentItemId()


    def setActionsIdList(self, idList, posToId):
        self.getCurrentActionsTable().setIdList(idList, posToId)


    def focusActions(self):
        self.getCurrentActionsTable().setFocus(Qt.TabFocusReason)


    def updateActionInfo(self, actionId):
        db = QtGui.qApp.db
        tableAction = db.table('Action')
        tableEvent = db.table('Event')
        table = tableAction.leftJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
        record = db.getRecord(table, ['Event.client_id',], actionId)
#                              ['Action.createDatetime','Action.createPerson_id', 'Action.modifyDatetime', 'Action.modifyPerson_id', 'Event.client_id', 'Action.payStatus', 'Action.note'], actionId)
        if record:
#            createDatetime = dateTimeToString(record.value('createDatetime').toDateTime())
#            createPersonId = forceRef(record.value('createPerson_id'))
#            modifyDatetime = dateTimeToString(record.value('modifyDatetime').toDateTime())
#            modifyPersonId = forceRef(record.value('modifyPerson_id'))
            clientId       = forceRef(record.value('client_id'))
#            note           = forceString(record.value('note'))
#            payStatus      = forceInt(record.value('payStatus'))
        else:
#            createDatetime = ''
#            createPersonId = None
#            modifyDatetime = ''
#            modifyPersonId = None
            clientId       = None
#            note           = ''
#            payStatus      = 0

        if not clientId:
            clientId = self.selectedClientId()
        self.updateClientInfo(clientId)
        self.actActionEditClient.setEnabled(bool(clientId))
        self.actActionOpenClientVaccinationCard.setEnabled(bool(clientId) and QtGui.qApp.userHasAnyRight([urCanReadClientVaccination, urCanEditClientVaccination]))
        self.actCheckClientAttach.setEnabled(bool(clientId))
        self.actPortal_Doctor.setEnabled(bool(clientId))
        self.actActionsRelationsClient.setEnabled(bool(clientId))
        QtGui.qApp.setCurrentClientId(clientId)
        clientSex, clientAge = getClientSexAge(clientId)
        self.tabAmbCardContent.setClientId(clientId, clientSex, clientAge)

#        table = db.table('Action')
#        idList = db.getIdList(table, 'id', table['event_id'].eq(eventId), ['id'])
#        self.tblEventActions.setIdList(idList)

#        self.lblEventIdValue.setText(str(eventId) if eventId else '')
#        self.lblEventExternalIdValue.setText(externalId)
#        self.lblEventCreateDateTimeValue.setText(createDatetime)
#        self.lblEventCreatePersonValue.setText(self.getPersonText(createPersonId))
#        self.lblEventModifyDateTimeValue.setText(modifyDatetime)
#        self.lblEventModifyPersonValue.setText(self.getPersonText(modifyPersonId))
#        self.lblEventNoteValue.setText(note)
#        self.lblEventPayStatusValue.setText(payStatusText(payStatus))


    def updateMedicalCommissionInfo(self, actionId):
        db = QtGui.qApp.db
        tableAction = db.table('Action')
        tableEvent = db.table('Event')
        table = tableAction.leftJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
        record = db.getRecord(table, ['Event.client_id',], actionId)
        if record:
            clientId = forceRef(record.value('client_id'))
        else:
            clientId = None
        if not clientId:
            clientId = self.selectedClientId()
        self.updateClientInfo(clientId)
        QtGui.qApp.setCurrentClientId(clientId)
        clientSex, clientAge = getClientSexAge(clientId)
        self.tabAmbCardContent.setClientId(clientId, clientSex, clientAge)


    def updateVisitInfo(self, visitId):
        clientId = None
        db = QtGui.qApp.db
        tableVisit = db.table('Visit')
        tableEvent = db.table('Event')
        table = tableVisit.innerJoin(tableEvent, tableEvent['id'].eq(tableVisit['event_id']))
        record = db.getRecord(table, ['Event.client_id',], visitId)
        if record:
            clientId       = forceRef(record.value('client_id'))
        else:
            clientId       = None
#        if not clientId:
#            clientId = self.selectedClientId()
        self.updateClientInfo(clientId)
        self.actCheckClientAttach.setEnabled(bool(clientId))
        self.actPortal_Doctor.setEnabled(bool(clientId))
        self.actActionEditClient.setEnabled(bool(clientId))
        self.actVisitRelationsClient.setEnabled(bool(clientId))
        QtGui.qApp.setCurrentClientId(clientId)

    def setClientSort(self, col):
        if col in (0, 1, 2, 3, 5):
            self.clientsSortingDest = 'ASC' if self.clientsSortingDest == 'DESC' else 'DESC'
            if col != self.clientsSortingCol:
                self.clientsSortingDest = 'ASC'
            self.clientsSortingCol = col
            self.updateClientsList(self.__filter)

    def setXXXSort(self, col):
        if col in (0, 1, 4, 5, 6, 7, 8, 9, 10):
            sortAscendingList = self.getSortAscendingList()
            sortAscending = not sortAscendingList.get(col, True)
            self.setXXXSortAscendingList(col, sortAscending)
            sortOrder = ' ASC' if sortAscending else ' DESC'
            if col == 0:
                order = u'Client.lastName%s, Client.firstName%s, Client.patrName%s' % (sortOrder, sortOrder, sortOrder)
            elif col == 1:
                order = u'Client.birthDate%s' % sortOrder
            if col in (4, 5, 7, 8, 9):
                nameField = self.modelExpertTempInvalid.cols()[col].fields()[0]
                table = self.modelExpertTempInvalid.table()
                order = table[str(nameField)].name() + sortOrder
            elif col == 6:
                order = u'rbTempInvalidReason.code%s, rbTempInvalidReason.name%s' % (sortOrder, sortOrder)
            elif col == 10:
                order = u'vrbPerson.code%s, vrbPerson.name' % sortOrder
            header = self.tblExpertTempInvalid.horizontalHeader()
            header.setSortIndicatorShown(True)
            header.setSortIndicator(col, Qt.AscendingOrder if sortAscending else Qt.DescendingOrder)
            self.renewXXXListAndSetTo(self.currentTempInvalidId(), [order])


    def renewXXXListAndSetTo(self, itemId=None, order=[]):
        self.updateTempInvalidList(self.__expertFilter, itemId, order)


    def setXXXSortAscendingList(self, col, check):
        self.sortAscendingList[col] = check


    def loadSortAscendingList(self):
        cols = self.modelExpertTempInvalid.cols()
        for col, field in enumerate(cols):
            self.setXXXSortAscendingList(col, True)


    def getSortAscendingList(self):
        return self.sortAscendingList


    def updateTempInvalidList(self, filter, posToId=None, order=[]):
        # в соответствии с фильтром обновляет список документов вр. нетрудоспособности.
        self.__expertFilter = filter
        db = QtGui.qApp.db
        if filter.get('linked', False):
            table = db.table('TempInvalid').alias('ti')
            mainTable = db.table('TempInvalid')
            queryTable = mainTable.join(table,
                                        db.joinAnd([mainTable['client_id'].eq(table['client_id']),
                                                    mainTable['caseBegDate'].eq(table['caseBegDate'])
                                                   ]))
        else:
            table = db.table('TempInvalid')
            mainTable = table
            queryTable = table
        tableDiagnosis = db.table('Diagnosis')
#        tableTempInvalidPeriod = db.table('TempInvalid_Period')
        tableTempInvalidDocument = db.table('TempInvalidDocument')
        queryTable = queryTable.leftJoin(tableDiagnosis, tableDiagnosis['id'].eq(table['diagnosis_id']))
        tempInvalidType = self.tabWidgetTempInvalidTypes.currentIndex()
        cond = [ mainTable['deleted'].eq(0),
                 mainTable['type'].eq(tempInvalidType)
               ]
        self.addEqCond(cond, table, 'id', filter, 'id')
        self.addEqCond(cond, table, 'doctype_id', filter, 'docTypeId')
        if filter.get('linked', False):
            cond.append(mainTable['prev_id'].isNull())
        if self.chkPrimaryOrDuble.isChecked() or self.chkFilterExpertSerial.isChecked() or self.chkFilterExpertNumber.isChecked():
            queryTable = queryTable.innerJoin(tableTempInvalidDocument, tableTempInvalidDocument['master_id'].eq(table['id']))
            cond.append(tableTempInvalidDocument['deleted'].eq(0))
        if self.chkPrimaryOrDuble.isChecked():
            cond.append(tableTempInvalidDocument['duplicate'].eq(filter.get('primaryOrDuble', 0)))
        if self.chkFilterTempInvalidDocType.isChecked():
            cond.append(u'''EXISTS(SELECT TID.id FROM TempInvalidDocument AS TID WHERE TID.deleted = 0
AND TID.master_id = TempInvalid.id AND TID.electronic = %d)''' % (filter.get('electronic', 0)))
        if self.chkFilterExpertSerial.isChecked():
            self.addLikeCond(cond, tableTempInvalidDocument, 'serial', filter, 'serial')
        if self.chkFilterExpertNumber.isChecked():
            self.addLikeCond(cond, tableTempInvalidDocument, 'number', filter, 'number')
        self.addEqCond(cond, table, 'tempInvalidReason_id', filter, 'reasonId')
        self.addEqCond(cond, table, 'result_id', filter, 'invalidResult')
        self.addDateCond(cond, table, 'begDate', filter, 'begBegDate', 'endBegDate')
        self.addDateCond(cond, table, 'endDate', filter, 'begEndDate', 'endEndDate')
        self.addEqCond(cond, table, 'person_id', filter, 'personId')
        self.addRangeCond(cond, tableDiagnosis, 'MKB', filter, 'begMKB', 'endMKB')
        self.addEqCond(cond, table, 'state', filter, 'state')
        if 'expertOrgStructureId' in filter or 'expertSpecialityId' in filter:
            tablePerson = db.table('Person')
            queryTable = queryTable.leftJoin(tablePerson, tablePerson['id'].eq(table['person_id']))
            cond.append(tablePerson['deleted'].eq(0))
            if 'expertOrgStructureId' in filter:
                expertOrgStructureId = filter.get('expertOrgStructureId', None)
                if expertOrgStructureId:
                    orgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', expertOrgStructureId)
                    if orgStructureIdList:
                        cond.append(tablePerson['orgStructure_id'].inlist(orgStructureIdList))
            if 'expertSpecialityId' in filter:
                expertSpecialityId = filter.get('expertSpecialityId', None)
                if expertSpecialityId:
                    cond.append(tablePerson['speciality_id'].eq(expertSpecialityId))
        if 'begDuration' in filter:
            cond.append(table['duration'].ge(filter['begDuration']))
        if 'endDuration' in filter:
            endDuration = filter['endDuration']
            if endDuration:
                cond.append(table['duration'].le(endDuration))
        self.addEqCond(cond, table, 'insuranceOfficeMark', filter, 'insuranceOfficeMark')
        self.addEqCond(cond, table, 'createPerson_id', filter, 'createPersonId')
        self.addDateCond(cond, table, 'createDatetime', filter, 'begCreateDate', 'endCreateDate')
        self.addEqCond(cond, table, 'modifyPerson_id', filter, 'modifyPersonId')
        self.addDateCond(cond, table, 'modifyDatetime', filter, 'begModifyDate', 'endModifyDate')
        if 'receiverIds' in filter:
            receiverIds = filter['receiverIds']
            cond.append(mainTable['client_id'].inlist(receiverIds))
        elif 'receiverEventIds' in filter:
            receiverEventIds = filter.get('receiverEventIds')
            tableEvent = db.table('Event')
            queryTable = queryTable.innerJoin(tableEvent, tableEvent['client_id'].eq(table['client_id']))
            cond.append(tableEvent['id'].inlist(receiverEventIds))
            cond.append(tableEvent['deleted'].eq(0))
        elif 'clientIds' in filter:
            clientIds = filter['clientIds']
            tableClient = db.table('Client').alias('Client')
            if not self.chkPrimaryOrDuble.isChecked():
                queryTable = queryTable.innerJoin(tableTempInvalidDocument, tableTempInvalidDocument['master_id'].eq(table['id']))
            queryTable = queryTable.innerJoin(tableClient, tableClient['id'].inlist(clientIds))
            cond.append(db.joinOr([tableClient['id'].eq(tableTempInvalidDocument['clientPrimum_id']), tableClient['id'].eq(tableTempInvalidDocument['clientSecond_id'])]))
            cond.append(tableTempInvalidDocument['deleted'].eq(0))
            cond.append(tableClient['deleted'].eq(0))
        elif 'eventIds' in filter:
            eventIds = filter.get('eventIds')
            tableEvent = db.table('Event')
            if not self.chkPrimaryOrDuble.isChecked() and not self.chkFilterExpertSerial.isChecked() and not self.chkFilterExpertNumber.isChecked():
                queryTable = queryTable.innerJoin(tableTempInvalidDocument, tableTempInvalidDocument['master_id'].eq(table['id']))
            queryTable = queryTable.innerJoin(tableEvent, tableEvent['id'].inlist(eventIds))
            cond.append(tableEvent['deleted'].eq(0))
            cond.append(tableTempInvalidDocument['deleted'].eq(0))
            cond.append(db.joinOr([tableEvent['client_id'].eq(tableTempInvalidDocument['clientPrimum_id']), tableEvent['client_id'].eq(tableTempInvalidDocument['clientSecond_id'])]))
            if order:
                tableClient = db.table('Client').alias('Client')
                cond.append(tableClient['deleted'].eq(0))
                queryTable = queryTable.innerJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
        if self.chkFilterExpertExternal.isChecked():
            isExternal = filter.get('isExternal', 0)
            if isExternal:
                stmtExternal = u'''EXISTS(SELECT TP.id FROM TempInvalid_Period AS TP
                WHERE TP.master_id = %s AND TP.isExternal = 1 AND TP.begDate = (SELECT TP2.begDate
                FROM TempInvalid_Period AS TP2 WHERE TP2.master_id = %s ORDER BY TP2.begDate ASC LIMIT 1)
                ORDER BY begDate ASC LIMIT 1)'''%(table.name() + '.id', table.name() + '.id')
                cond.append((u'NOT %s'%stmtExternal) if isExternal == 1 else stmtExternal)
        try:
            QtGui.QApplication.setOverrideCursor(QtGui.QCursor(Qt.WaitCursor))
            if table == mainTable and (not 'clientIds' in filter and not 'eventIds' in filter):
                getIdList = db.getIdList
            else:
                getIdList = db.getDistinctIdList
            if order:
                tableVRBPerson = db.table('vrbPerson')
                tableRBTempInvalidReason = db.table('rbTempInvalidReason')
                if not 'clientIds' in filter and not 'eventIds' in filter:
                    tableClient = db.table('Client')
                queryTable = queryTable.innerJoin(tableClient, tableClient['id'].eq(table['client_id']))
                queryTable = queryTable.leftJoin(tableVRBPerson, tableVRBPerson['id'].eq(table['person_id']))
                queryTable = queryTable.leftJoin(tableRBTempInvalidReason, tableRBTempInvalidReason['id'].eq(table['tempInvalidReason_id']))
                order.append(mainTable['endDate'].name()+' DESC')
            else:
                order.append(mainTable['endDate'].name()+' DESC')
                order.append(mainTable['id'].name())
            idList = getIdList(queryTable,
                           mainTable['id'].name(),
                           cond,
                           order)
            self.setExpertIdList(idList, posToId)
            documentIdList = []
            if idList:
                cond = [tableTempInvalidDocument['master_id'].inlist(idList),
                        tableTempInvalidDocument['deleted'].eq(0),
                        ]
                if self.chkPrimaryOrDuble.isChecked():
                    cond.append(tableTempInvalidDocument['duplicate'].eq(filter.get('primaryOrDuble', 0)))
                if self.chkFilterTempInvalidDocType.isChecked():
                    cond.append(tableTempInvalidDocument['electronic'].eq(filter.get('electronic', 0)))
                if self.chkFilterExpertSerial.isChecked():
                    self.addLikeCond(cond, tableTempInvalidDocument, 'serial', filter, 'serial')
                if self.chkFilterExpertNumber.isChecked():
                    self.addLikeCond(cond, tableTempInvalidDocument, 'number', filter, 'number')
                if filter.get('linked', False):
                    cond.append(tableTempInvalidDocument['prev_id'].isNull())
                if 'documentExportFSS' in filter:
                    documentExportFSS = filter['documentExportFSS']
                    if documentExportFSS >= 0:
                        if not (self.chkPrimaryOrDuble.isChecked() or self.chkFilterExpertSerial.isChecked() or self.chkFilterExpertNumber.isChecked()):
                            queryTable = queryTable.innerJoin(tableTempInvalidDocument, tableTempInvalidDocument['master_id'].eq(table['id']))
                        cond.append(tableTempInvalidDocument['electronic'].eq(1))
                        cond.append(tableTempInvalidDocument['deleted'].eq(0))
                        if documentExportFSS in (1, 2, 3):
                            tableTempInvalidDocumentFSS = db.table('TempInvalidDocument').alias('TempInvalidDocumentFSS')
                            tableDocumentExport = db.table('TempInvalidDocument_Export')
                            tableExternalSystem = db.table('rbExternalSystem')
                            queryTableExportFSS = tableTempInvalidDocumentFSS.innerJoin(tableDocumentExport, tableDocumentExport['master_id'].eq(tableTempInvalidDocumentFSS['id']))
                            queryTableExportFSS = queryTableExportFSS.innerJoin(tableExternalSystem, tableExternalSystem['id'].eq(tableDocumentExport['system_id']))
                            condExportFSS = [tableTempInvalidDocumentFSS['id'].eq(tableTempInvalidDocument['id']),
                                             tableExternalSystem['code'].eq(u'СФР'),
                                             tableTempInvalidDocumentFSS['electronic'].eq(1),
                                             tableTempInvalidDocumentFSS['deleted'].eq(0),
                                            ]
                            if documentExportFSS == 1:
                                cond.append(db.selectStmt(queryTableExportFSS, u'IF(TempInvalidDocument_Export.success = 1, 1, 0)', where=condExportFSS, order = u'TempInvalidDocument_Export.dateTime DESC', limit=1))
                            elif documentExportFSS == 2:
                                cond.append(db.selectStmt(queryTableExportFSS, u'IF(TempInvalidDocument_Export.success = 0, 1, 0)', where=condExportFSS, order = u'TempInvalidDocument_Export.dateTime DESC', limit=1))
                            elif documentExportFSS == 3:
                                cond.append('NOT EXISTS (%s)' % db.selectStmt(queryTableExportFSS, 'NULL', where=condExportFSS, order = u'TempInvalidDocument_Export.dateTime DESC', limit=1))
                documentIdList = db.getDistinctIdList(tableTempInvalidDocument,
                                              [tableTempInvalidDocument['id']],
                                              cond,
                                              u'TempInvalidDocument.idx ASC, TempInvalidDocument.issueDate DESC, TempInvalidDocument.master_id ASC')
            self.getCurrentExpertRelationDocumentsExTable().setIdList([])
            self.getCurrentTempDocumentsExTable().setIdList(documentIdList)
        finally:
            QtGui.QApplication.restoreOverrideCursor()
        expertFilterType = filter['expertFilterType']
        hideClientInfo = expertFilterType == 0 or expertFilterType == 1 and len(filter['receiverIds']) == 1
        table = self.getCurrentExpertTable()
        for i in range(3):
            table.setColumnHidden(i, hideClientInfo)
        self.getCurrentTempDocumentsTable().setColumnHidden(0, hideClientInfo)
        self.getCurrentTempDocumentsExTable().setColumnHidden(0, hideClientInfo)
        if filter.get('linked', False):
            self.getCurrentExpertRelationDocumentsExTable().setColumnHidden(0, hideClientInfo)
            for i in range(3):
                self.getCurrentExpertRelationTable().setColumnHidden(i, hideClientInfo)


    def updateCurrentTempPeriodTable(self, tempInvalidId):
        db = QtGui.qApp.db
        tblPeriods = self.getCurrentTempPeriodsTable()
        orderBY = u'id'
        for key, value in tblPeriods.model().headerSortingCol.items():
            if value:
                ASC = u'ASC'
            else:
                ASC = u'DESC'
            if key == 0:
                orderBY = u'(select name from vrbPerson where id = TempInvalid_Period.begPerson_id) %s' % ASC
            elif key == 1:
                orderBY = u'begDate %s' % ASC
            elif key == 2:
                orderBY = u'(select name from vrbPerson where id = TempInvalid_Period.endPerson_id) %s' % ASC
            elif key == 3:
                orderBY = u'endDate %s' % ASC
            elif key == 4:
                orderBY = u'isExternal %s' % ASC
            elif key == 5:
                orderBY = u'(select name from rbTempInvalidRegime where id = TempInvalid_Period.regime_id) %s' % ASC
            elif key == 6:
                orderBY = u'(select name from rbTempInvalidResult where id = TempInvalid_Period.result_id) %s' % ASC
            elif key == 7:
                orderBY = u'note %s' % ASC
        if tempInvalidId:
            table = db.table('TempInvalid_Period')
            idList = db.getIdList(table, 'id', table['master_id'].eq(tempInvalidId), orderBY)
        else:
            idList = []

        tblPeriods.setIdList(idList)


    # def updateTempInvalidDublicates(self, tempInvalidId):
    #     db = QtGui.qApp.db
    #     orderBY = u'id'
    #     for key, value in self.tblExpertTempInvalidDuplicates.model().headerSortingCol.items():
    #         if value:
    #             ASC = u'ASC'
    #         else:
    #             ASC = u'DESC'
    #         if key == 0:
    #             orderBY = u'insuranceOfficeMark %s' % ASC
    #         elif key == 1:
    #             orderBY = u'serial %s' % ASC
    #         elif key == 2:
    #             orderBY = u'number %s' % ASC
    #         elif key == 3:
    #             orderBY = u'date %s' % ASC
    #         elif key == 4:
    #             orderBY = u'(select name from vrbPerson where id = TempInvalidDuplicate.person_id) %s' % ASC
    #     if tempInvalidId:
    #         table = db.table('TempInvalidDuplicate')
    #         idList = db.getIdList(table, 'id', table['tempInvalid_id'].eq(tempInvalidId), orderBY)
    #     else:
    #         idList = []
    #     self.tblExpertTempInvalidDuplicates.setIdList(idList)

    def updateTempInvalidInfo(self, tempInvalidId, noPrev=False):
        isFilterExpertLinked = self.chkFilterExpertLinked.isChecked()
        db = QtGui.qApp.db
        tableTempInvalid = db.table('TempInvalid')
        tablePeriod = db.table('TempInvalid_Period')
        if isFilterExpertLinked:
            begDateMin = None
            endDateMax = None
            countDays = 0
            currentTable = self.getCurrentExpertRelationTable()
            if noPrev:
                tempInvalidRelationIdList = []
                if tempInvalidId:
                    id = tempInvalidId
                    while id:
                        record = db.getRecordEx(tableTempInvalid, ['id'],
                                                [tableTempInvalid['prev_id'].eq(id), tableTempInvalid['deleted'].eq(0)],
                                                tableTempInvalid['begDate'].name())
                        id = forceRef(record.value('id')) if record else None
                        if id and id not in tempInvalidRelationIdList:
                            tempInvalidRelationIdList.append(id)
                            recordPeriods = db.getRecordListGroupBy(tablePeriod, [
                                'MIN(begDate) AS begDate, MAX(endDate) AS endDate'], [tablePeriod['master_id'].eq(id)],
                                                                    'master_id', 'endDate')
                            for recordPeriod in recordPeriods:
                                begDate = forceDate(recordPeriod.value('begDate'))
                                begDateMin = min(begDateMin, begDate) if begDateMin else begDate
                                endDateMax = max(endDateMax, forceDate(recordPeriod.value('endDate')))
                currentTable.setIdList(tempInvalidRelationIdList)
            expertFilterType = self.cmbFilterExpert.currentIndex()
            hideClientInfo = expertFilterType == 0 or expertFilterType == 1 and len(self.modelClients.idList()) == 1
            for i in range(3):
                currentTable.setColumnHidden(i, hideClientInfo)
        self.setClientInfoBrowserExpert(tempInvalidId)
        idList = []
        if isFilterExpertLinked and noPrev:
            if tempInvalidId:
                recordPeriods = db.getRecordList(tablePeriod, ['id, begDate, endDate'],
                                                 [tablePeriod['master_id'].eq(tempInvalidId)], 'endDate')
                for recordPeriod in recordPeriods:
                    id = forceRef(recordPeriod.value('id'))
                    if id and id not in idList:
                        idList.append(id)
                        begDate = forceDate(recordPeriod.value('begDate'))
                        begDateMin = min(begDateMin, begDate) if begDateMin else begDate
                        endDateMax = max(endDateMax, forceDate(recordPeriod.value('endDate')))
            if begDateMin and endDateMax:
                countDays = begDateMin.daysTo(endDateMax) + 1
            index = self.tabWidgetTempInvalidTypes.currentIndex()
            textCount = u', ВУТ: ' + (begDateMin.toString('dd.MM.yyyy') if begDateMin else u'') + u' - ' + (
                endDateMax.toString('dd.MM.yyyy') if endDateMax else u'') + u', ' + formatDays(countDays)
            if index == self.tabWidgetTempInvalidTypes.indexOf(self.tabExpertTempInvalidDetalsWidget):
                self.lblExpertTempInvalidCount.setText(formatRecordsCount(
                    self.modelExpertTempInvalid.rowCount()) + textCount)
            elif index == self.tabWidgetTempInvalidTypes.indexOf(self.tabExpertDisabilityDetailsWidget):
                self.lblExpertDisabilityCount.setText(
                    formatRecordsCount(self.modelExpertDisability.rowCount()) + textCount)
            elif index == self.tabWidgetTempInvalidTypes.indexOf(self.tabExpertVitalRestrictionDetailsWidget):
                self.lblExpertVitalRestrictionCount.setText(
                    formatRecordsCount(self.modelExpertVitalRestriction.rowCount()) + textCount)
        else:
            if tempInvalidId:
                idList = db.getDistinctIdList(tablePeriod, 'id', tablePeriod['master_id'].eq(tempInvalidId),
                                              ['endDate'])
        self.getCurrentTempPeriodsTable().setIdList(idList)

        idList = []
        if tempInvalidId:
            table = db.table('TempInvalidDocument')
            cond = [table['master_id'].eq(tempInvalidId),
                    table['deleted'].eq(0)
                    ]
            idList = db.getDistinctIdList(table, 'id', cond, ['id'])
            additionalCustomizePrintButton(self, self.btnExpertPrint, getKerContext(), self.btnExpertPrint_actions)
        self.getCurrentTempDocumentsTable().setIdList(idList)


    def getExpertFilterAsText(self):
        db = QtGui.qApp.db
        filter  = self.__expertFilter
        resList = []

        expertFilterType = filter['expertFilterType']
        if expertFilterType in (0, 1):
            clientIds = filter.get('clientIds', None)
            if clientIds and len(clientIds) == 1:
                resList.append((u'Пациент', getClientMiniInfo(clientIds[0])))
            elif clientIds and len(clientIds) > 1:
                resList.append((u'Список пациентов', u'из вкладки'))
        else:
            resList.append((u'Список пациентов', u'полный'))

        tmpList = [
            ('id',         u'Идентифиатор записи', lambda id: '%d'%id),
            ('docTypeId',  u'Тип документа',       lambda id: forceString(db.translate('rbTempInvalidDocument', 'id', id, 'name'))),
            ('serial',     u'Серия',               forceString),
            ('number',     u'Номер',               forceString),
            ('reasonId',   u'Причина нетрудоспособности', lambda id: forceString(db.translate('rbTempInvalidReason', 'id', id, 'name'))),
            ('begBegDate', u'Дата начала с',       forceString),
            ('endBegDate', u'Дата начала по',      forceString),
            ('begEndDate', u'Дата окончания с',    forceString),
            ('endEndDate', u'Дата окончания по',   forceString),
            ('personId',   u'Врач',                lambda id: forceString(db.translate('vrbPersonWithSpeciality', 'id', id, 'name'))),
            ('begMKB',     u'Код МКБ с',           forceString),
            ('endMKB',     u'Код МКБ по',          forceString),
            ('state',      u'состояние',           CTempInvalidState.text),
            ('begDuration',u'длительность с',      lambda v: '%d'%v),
            ('endDuration',u'длительность по',     lambda v: '%d'%v),
            ('insuranceOfficeMark', u'отметка страхового стола', lambda i: [u'без отметки', u'с отметкой']),
            ('documentExportFSS', u'статус передачи в СФР', lambda i: [u'не задано', u'успешно', u'неуспешно', u'неотправленные']),
            ('createPerson_id', u'Автор записи',   lambda id: forceString(db.translate('vrbPersonWithSpeciality', 'id', id, 'name'))),
            ('begCreateDate', u'Дата создания с',  forceString),
            ('endCreateDate', u'Дата создания по', forceString),
            ('modifyPerson_id', u'Запись изменил', lambda id: forceString(db.translate('vrbPersonWithSpeciality', 'id', id, 'name'))),
            ('begModifyDate', u'Дата изменения с', forceString),
            ('endModifyDate', u'Дата изменения по',forceString),
            ]
        for (x, y, z) in tmpList:
            convertFilterToTextItem(resList, filter, x, y, z)
        return '\n'.join([ ': '.join(item) for item in resList])


    def getExpertMCFilterAsText(self):
        db = QtGui.qApp.db
        filter  = self.__expertMCFilter
        resList = []
        actionsFilterType = filter['actionsFilterType']
        if actionsFilterType in (0, 1):
            clientIds = filter.get('clientIds', None)
            if clientIds and len(clientIds) == 1:
                resList.append((u'Пациент', getClientMiniInfo(clientIds[0])))
            elif clientIds and len(clientIds) > 1:
                resList.append((u'Список пациентов', u'из вкладки'))
        else:
            resList.append((u'Список пациентов', u'полный'))
        tmpList = [
            ('id',                   u'Идентифиатор записи',  lambda id: '%d'%id),
            ('expertiseId',          u'Экспертиза',           lambda expertiseId: expertiseClass[expertiseId][1]),
            ('expertiseTypeId',      u'Тип экспертизы',       lambda expertiseTypeId: forceString(expertiseTypeId[1])),
            ('expertNumberExpertise',u'Номер'   ,             forceString),
            ('expertNumber',         u'Номер ЛН',             forceString),
            ('expertDirectionBegDate',u'Дата назначения с',    forceString),
            ('expertDirectionEndDate',u'Дата назначения по',   forceString),
            ('setPersonId',          u'Назначивший',          lambda id: forceString(db.translate('vrbPersonWithSpeciality', 'id', id, 'name'))),
            ('begDirectDate',        u'Направление на ВК с',  forceString),
            ('endDirectDate',        u'Направление на ВК по', forceString),
            ('expertOrgStructureId', u'Подразделение',        lambda id: forceString(db.translate('OrgStructure', 'id', id, 'name'))),
            ('expertSpecialityId',   u'Специальность',        lambda id: forceString(db.translate('rbSpeciality', 'id', id, 'name'))),
            ('begMKB',               u'Код МКБ с',            forceString),
            ('endMKB',               u'Код МКБ по',           forceString),
            ('actionStatus',         u'состояние',            lambda actionStatus: CActionStatus.names[actionStatus]),
            ('expertiseCharacterId', u'Характеристика экспертизы',lambda id: forceString(db.translate('rbMedicalBoardExpertiseCharacter', 'id', id, 'name'))),
            ('expertiseKindId',      u'Вид экспертизы',           lambda id: forceString(db.translate('rbMedicalBoardExpertiseKind', 'id', id, 'name'))),
            ('expertiseObjectId',    u'Предмет экспертизы',       lambda id: forceString(db.translate('rbMedicalBoardExpertiseObject', 'id', id, 'name'))),
            ('expertiseArgumentId',  u'Обоснование экспертизы',   lambda id: forceString(db.translate('rbMedicalBoardExpertiseArgument', 'id', id, 'name'))),
            ('begExecDate',          u'Экспертиза ВК с',      forceString),
            ('endExecDate',          u'Экспертиза ВК по',     forceString),
            ('expertId',             u'Эксперт',              lambda id: forceString(db.translate('vrbPersonWithSpeciality', 'id', id, 'name'))),
            ('expertExportedType',   u'Тип экспорта во внешние ИС', (lambda expertExportedType: [u'Да', u'Нет'][expertExportedType]) if self.chkFilterExpertExportedToExternalISMC.isChecked() else u''),
            ('expertIntegratedISId', u'Интегрированные внешние системы', (lambda expertIntegratedISId: forceString(db.translate('rbExternalSystem', 'id', expertIntegratedISId, 'name'))) if self.chkFilterExpertExportedToExternalISMC.isChecked() else None),
            ('createPerson_id',      u'Автор записи',         lambda id: forceString(db.translate('vrbPersonWithSpeciality', 'id', id, 'name'))),
            ('begCreateDate',        u'Дата создания с',      forceString),
            ('endCreateDate',        u'Дата создания по',     forceString),
            ('modifyPerson_id',      u'Запись изменил',       lambda id: forceString(db.translate('vrbPersonWithSpeciality', 'id', id, 'name'))),
            ('begModifyDate',        u'Дата изменения с',     forceString),
            ('endModifyDate',        u'Дата изменения по',    forceString),
            ]
        for (x, y, z) in tmpList:
            convertFilterToTextItem(resList, filter, x, y, z)
        return '\n'.join([ ': '.join(item) for item in resList])


    def getCurrentExpertTypesTabWidget(self):
        index = self.tabWidgetTempInvalidTypes.currentIndex()
        return [self.tabExpertTempInvalidDetalsWidget, self.tabExpertDisabilityDetailsWidget, self.tabExpertVitalRestrictionDetailsWidget, self.getCurrentExpertMedicalCommissionTable()][index]


    def getCurrentExpertTypesTabWidgetDetails(self):
        index = self.tabWidgetTempInvalidTypes.currentIndex()
        return [self.tabExpertTempInvalidDetals, self.tabExpertDisabilityDetails, self.tabExpertVitalRestrictionDetails, self.getCurrentExpertMedicalCommissionTable()][index]


#    def getCurrentExpertMedicalCommissionTable(self):
#        index = self.tabExpertMedicalCommissionWidget.currentIndex()
#        return [self.tblExpertDirectionsMC, self.tblExpertProtocolsMC, self.tblExpertMedicalSocialInspection][index]


    def getCurrentExpertTable(self):
        index = self.tabWidgetTempInvalidTypes.currentIndex()
        return [self.tblExpertTempInvalid, self.tblExpertDisability, self.tblExpertVitalRestriction, self.getCurrentExpertMedicalCommissionTable()][index]


    def getCurrentExpertLabelCount(self):
        index = self.tabWidgetTempInvalidTypes.currentIndex()
        return [self.lblExpertTempInvalidCount, self.lblExpertDisabilityCount, self.lblExpertVitalRestrictionCount, self.getCurrentExpertMedicalCommissionTable()][index]


    def getCurrentExpertRelationTable(self):
        index = self.tabWidgetTempInvalidTypes.currentIndex()
        return [self.tblExpertTempInvalidRelation, self.tblExpertDisabilityRelation, self.tblExpertVitalRestrictionRelation, self.getCurrentExpertMedicalCommissionTable()][index]


    def getCurrentExpertRelationDocumentsExTable(self):
        index = self.tabWidgetTempInvalidTypes.currentIndex()
        return [self.tblExpertTempInvalidRelationDocumentsEx, self.tblExpertDisabilityRelationDocumentsEx, self.tblExpertVitalRestrictionRelationDocumentsEx, self.getCurrentExpertMedicalCommissionTable()][index]


    def getCurrentTempPeriodsTable(self):
        index = self.tabWidgetTempInvalidTypes.currentIndex()
        return [self.tblExpertTempInvalidPeriods, self.tblExpertDisabilityPeriods, self.tblExpertVitalRestrictionPeriods, self.getCurrentExpertMedicalCommissionTable()][index]


    def getCurrentTempDocumentsTable(self):
        index = self.tabWidgetTempInvalidTypes.currentIndex()
        return [self.tblExpertTempInvalidDocuments, self.tblExpertDisabilityDocuments, self.tblExpertVitalRestrictionDocuments, self.getCurrentExpertMedicalCommissionTable()][index]


    def getCurrentTempDocumentsExTable(self):
        index = self.tabWidgetTempInvalidTypes.currentIndex()
        return [self.tblExpertTempInvalidDocumentsEx, self.tblExpertDisabilityDocumentsEx, self.tblExpertVitalRestrictionDocumentsEx, self.getCurrentExpertMedicalCommissionTable()][index]


    def getCurrentTempDocumentsExPeriodsTable(self):
        index = self.tabWidgetTempInvalidTypes.currentIndex()
        return [self.tblExpertTempInvalidPeriodsDocuments, self.tblExpertDisabilityPeriodsDocuments, self.tblExpertVitalRestrictionPeriodsDocuments, self.getCurrentExpertMedicalCommissionTable()][index]


    def currentTempInvalidId(self):
        return self.getCurrentExpertTable().currentItemId()


    def currentTempInvalidDocumentsId(self):
        return self.getCurrentTempDocumentsTable().currentItemId()


    def setExpertIdList(self, idList, posToId):
        self.getCurrentExpertTable().setIdList(idList, posToId)


    @pyqtSignature('bool')
    def on_chkFilterExpertExpertiseMC_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)
        self.initExpertiseMCComboBox()


    @pyqtSignature('int')
    def on_cmbFilterExpertExpertiseMC_currentIndexChanged(self, index):
        self.initExpertiseMCComboBox()
        self.cmbFilterExpertExpertiseCharacterMC.setTable('rbMedicalBoardExpertiseCharacter', False, filter='class = %s'%(index))


    @pyqtSignature('int')
    def on_cmbFilterExpertExpertiseCharacterMC_currentIndexChanged(self, index):
        self.cmbFilterExpertExpertiseKindMC.setTable('rbMedicalBoardExpertiseKind', False, filter='expertiseCharacter_id=%s'%(self.cmbFilterExpertExpertiseCharacterMC.value()))
        self.cmbFilterExpertExpertiseObjectMC.setTable('rbMedicalBoardExpertiseObject', False, filter='expertiseCharacter_id=%s'%(self.cmbFilterExpertExpertiseCharacterMC.value()))
        self.cmbFilterExpertExpertiseArgumentMC.setTable('rbMedicalBoardExpertiseArgument', False, filter='expertiseCharacter_id=%s'%(self.cmbFilterExpertExpertiseCharacterMC.value()))


    def initExpertiseMCComboBox(self):
        flatCode = u'inspection%'
        if self.chkFilterExpertExpertiseMC.isChecked():
            flatCode = expertiseClass[self.cmbFilterExpertExpertiseMC.currentIndex()][1]
        self.cmbFilterExpertExpertiseTypeMC.clearValue()
        self.cmbFilterExpertExpertiseTypeMC.clear()
        self.cmbFilterExpertExpertiseTypeMC.setTable('ActionType', False, filter='''flatCode LIKE '%s' '''%(flatCode))
#        self.getExpertiseProperty(self.cmbFilterExpertExpertiseCharacterMC, u'Характеристика экспертизы', flatCode)
#        self.getExpertiseProperty(self.cmbFilterExpertExpertiseKindMC, u'Вид экспертизы', flatCode)
#        self.getExpertiseProperty(self.cmbFilterExpertExpertiseObjectMC, u'Предмет экспертизы', flatCode)
#        self.getExpertiseProperty(self.cmbFilterExpertExpertiseArgumentMC, u'Обоснование экспертизы', flatCode)


    def getExpertiseProperty(self, comboBox, name, flatCode = u'inspection%'):
        comboBox._model.clear()
        domain = u'\'не определено\','
        record = self.getExpertiseDomain(flatCode, name)
        if record:
#            domainR = QString(forceString(record))
#            if u'*' in domainR:
#                index = domainR.indexOf(u'*', 0, Qt.CaseInsensitive)
#                if domainR[index - 1] != u',':
#                    domainR.replace(QString('*'), QString(','))
#                else:
#                    domainR.remove(QChar('*'), Qt.CaseInsensitive)
            domainR = forceString(record)
            index = domainR.find('*')
            if index>0 and domainR[index-1] != ',':
                domainR = domainR.replace('*', ',')
            else:
                domainR = domainR.replace('*', '')
            domain += domainR
        comboBox.setDomain(domain)


    def getExpertiseDomain(self, flatCode, name):
        db = QtGui.qApp.db
        tableAPT = db.table('ActionPropertyType')
        tableActionType = db.table('ActionType')
#        tableAction = db.table('Action')
        cond =[tableActionType['id'].inlist(getActionTypeIdListByFlatCode(flatCode)),
               tableAPT['name'].like(name),
               tableAPT['typeName'].like(u'String'),
               tableAPT['deleted'].eq(0)
               ]
        queryTable = tableActionType.innerJoin(tableAPT, tableActionType['id'].eq(tableAPT['actionType_id']))
        record = db.getRecordEx(queryTable, [tableAPT['valueDomain']], cond)
        if record:
            return record.value(0)
        return None


    def focusExpertMC(self):
        self.getCurrentExpertMedicalCommissionTable().setFocus(Qt.TabFocusReason)


    def focusExpert(self):
        self.getCurrentExpertTable().setFocus(Qt.TabFocusReason)


    def editTempInvalid(self, tempInvalidId):
        widgetIndex = self.tabWidgetTempInvalidTypes.currentIndex()
#        clientIdList = []
        db = QtGui.qApp.db
        clientCache = CTableRecordCache(db, db.forceTable('Client'), u'*', capacity=None)
        dialog = CTempInvalidEditDialog(self, clientCache)
        clientInfo = getClientMiniInfo(self.currentClientId())
        dialog.setWindowTitle(forceString(self.tabWidgetTempInvalidTypes.tabText(widgetIndex)) + u': ' + clientInfo)
        dialog.load(tempInvalidId)
        tempInvalidNewId = None
        try:
            if dialog.exec_():
                tempInvalidNewId = dialog.itemId()
            self.getCurrentExpertTable().model().updateColumnsCaches(tempInvalidId)
            self.updateTempInvalidList(self.__expertFilter, tempInvalidNewId if tempInvalidNewId else tempInvalidId)
            if self.tabWidgetTempInvalidTypes.currentIndex() == self.tabWidgetTempInvalidTypes.indexOf(self.tabExpertMedicalCommission):
                currentTableMSI = self.getCurrentExpertMedicalCommissionTable()
                actionId = currentTableMSI.currentItemId()
                if actionId:
                    currentTableMSI.model().updateColumnsCaches(actionId)
                else:
                    currentTableMSI.model().clearColumnsCaches()
                self.updateMedicalCommissionList(self.__expertMCFilter)
            # предполагаю что лок с записей в таблице здесь уже снят
            sendTempInvalidDocuments(dialog.transfer_tempId_list)
        finally:
            dialog.deleteLater()


    def editTempInvalidExpert(self):
        widgetIndex = self.tabWidgetTempInvalidTypes.currentIndex()
        clientId = self.currentClientId()
        if clientId:
            db = QtGui.qApp.db
            clientCache = CTableRecordCache(db, db.forceTable('Client'), u'*', capacity=None)
            dialog = CTempInvalidCreateDialog(self, clientId, clientCache)
            if self.tabWidgetTempInvalidTypes.currentIndex() == self.tabExpertTempInvalidDetals.indexOf(self.tabExpertTempInvalid):
                docCode = '1'
            else:
                docCode = ''
            dialog.setType(widgetIndex, docCode, True)
            clientInfo = getClientMiniInfo(self.currentClientId())
            dialog.setWindowTitle(forceString(self.tabWidgetTempInvalidTypes.tabText(widgetIndex)) + u': ' + clientInfo)
            dialog.createTempInvalidDocument(placeRegistry = True)
            tempInvalidId = None
            try:
                if dialog.exec_():
                    tempInvalidId = dialog.itemId()
                self.updateTempInvalidList(self.__expertFilter, tempInvalidId)
                sendTempInvalidDocuments(dialog.transfer_tempId_list)
            finally:
                dialog.deleteLater()


    def isEnabledExpertConcurrently(self, table):
        tempInvalidId = table.currentItemId()
        if tempInvalidId:
            model = table.model()
            currentItem = model.recordCache().get(tempInvalidId)
            if forceInt(currentItem.value('busyness')) == 1 and forceInt(currentItem.value('type')) == 0: 
                if forceInt(currentItem.value('state')) == 0 or QtGui.qApp.userHasRight(urCreateExpertConcurrentlyOnCloseVUT):
                    return True
        return False
        
                
    def getExpertPrevDocId(self, table):
        tempInvalidId = table.currentItemId()
        if tempInvalidId:
            model = table.model()
            currentItem = model.recordCache().get(tempInvalidId)
            return forceRef(currentItem.value('prev_id'))
        return None

    
    def getExpertState(self, table):
        tempInvalidId = table.currentItemId()
        if tempInvalidId:
            model = table.model()
            currentItem = model.recordCache().get(tempInvalidId)
            return forceInt(currentItem.value('state'))
        return None
    

    def getExpertNextDocId(self, table):
        tempInvalidId = table.currentItemId()
        if tempInvalidId:
            return forceRef(QtGui.qApp.db.translate('TempInvalid', 'prev_id', tempInvalidId, 'id'))
        return None


    def _setMedicalCommissionActionsOrderByColumn(self, column):
        table = self.getCurrentExpertMedicalCommissionTable()
        table.setOrder(column)
        self.updateMedicalCommissionList(self.__expertMCFilter, table.currentItemId())


    def expertiseForMSIPropertyValue(self, tableName, propertyName, value):
        return u'''EXISTS(SELECT APV.id
            FROM ActionProperty AS AP
            INNER JOIN ActionPropertyType AS APT ON AP.type_id = APT.id
            INNER JOIN Action AS A ON A.id = AP.action_id
            INNER JOIN %s AS APV ON APV.id = AP.id
            WHERE Action.prevAction_id IS NOT NULL AND APT.actionType_id = A.actionType_id
            AND  A.id IS NOT NULL AND A.id = Action.prevAction_id AND A.deleted = 0
            AND APT.deleted = 0 AND AP.deleted = 0 AND APT.name %s AND APV.value %s)'''%(tableName, updateLIKE(propertyName), updateLIKE(value))


    def expertiseTypeForMSI(self, expertiseTypeIdList):
        return u'''EXISTS(SELECT A.id
            FROM Action AS A
            WHERE Action.prevAction_id IS NOT NULL AND A.id = Action.prevAction_id AND A.id IS NOT NULL AND A.deleted = 0
            AND A.actionType_id IN (%s))'''%(u','.join(str(id) for id in expertiseTypeIdList if id))


    def updateMedicalCommissionList(self, filter, posToId = None, order = []):
        # в соответствии с фильтром обновляет список документов ВК.
        self.__expertMCFilter = filter
        currentTable = self.getCurrentExpertMedicalCommissionTable()
        db = QtGui.qApp.db
        table = db.table('Action')
        tableEvent = db.table('Event')
        queryTable = table.innerJoin(tableEvent, tableEvent['id'].eq(table['event_id']) )
        expertiseId = filter.get('expertiseId', None)
        cond = [table['deleted'].eq(0),
                tableEvent['deleted'].eq(0)
               ]
        order = currentTable.order() if currentTable.order() else [table['endDate'].name()+' DESC', table['id'].name()]
        actionTypeMSIIdList = getActionTypeIdListByFlatCode(u'inspection_mse%')
        if self.tabExpertMedicalCommissionWidget.currentIndex() == self.tabExpertMedicalCommissionWidget.indexOf(self.tabExpertDirectionsMC):
            cond.append(table['endDate'].isNull())
            if actionTypeMSIIdList:
                cond.append(table['actionType_id'].notInlist(actionTypeMSIIdList))
        elif self.tabExpertMedicalCommissionWidget.currentIndex() == self.tabExpertMedicalCommissionWidget.indexOf(self.tabExpertProtocolsMC):
            cond.append(table['endDate'].isNotNull())
            if actionTypeMSIIdList:
                cond.append(table['actionType_id'].notInlist(actionTypeMSIIdList))
        elif self.tabExpertMedicalCommissionWidget.currentIndex() == self.tabExpertMedicalCommissionWidget.indexOf(self.tabExpertMedicalSocialInspection):
            cond.append(table['actionType_id'].inlist(actionTypeMSIIdList))
        expertNumber = filter.get('expertNumber', None)
        if expertNumber:
            cond.append(getStringProperty(u'Номер ЛН', u'''APS.value %s'''%(updateLIKE(expertNumber))))
        expertNumberExpertise = filter.get('expertNumberExpertise', None)
        if expertNumberExpertise:
            cond.append(getStringProperty(u'Номер', u'''APS.value %s'''%(updateLIKE(expertNumberExpertise))))
        if self.chkFilterDirectDateOnMC.isChecked():
            begDirectDate = filter.get('begDirectDate', None)
            if begDirectDate:
                cond.append(table['begDate'].ge(begDirectDate))
            endDirectDate = filter.get('endDirectDate', None)
            if endDirectDate:
                cond.append(table['begDate'].lt(endDirectDate.addDays(1)))
        if self.chkFilterExecDateMC.isChecked():
            begExecDate = filter.get('begExecDate', None)
            if begExecDate:
                cond.append(table['endDate'].ge(begExecDate))
            endExecDate = filter.get('endExecDate', None)
            if endExecDate:
                cond.append(table['endDate'].lt(endExecDate.addDays(1)))
        self.addDateCond(cond, table, 'directionDate', filter, 'expertDirectionBegDate', 'expertDirectionEndDate')
        self.addEqCond(cond, table, 'setPerson_id', filter, 'setPersonId')
        self.addEqCond(cond, table, 'person_id', filter, 'expertId')
        if self.chkFilterExpertMKBMC.isChecked():
            actionMKBFrom = filter.get('begMKB', None)
            actionMKBTo = filter.get('endMKB', None)
            if actionMKBFrom or actionMKBTo:
                if actionMKBFrom and not actionMKBTo:
                   actionMKBTo = u'U'
                elif not actionMKBFrom and actionMKBTo:
                    actionMKBFrom = u'A'
                cond.append(table['MKB'].ge(actionMKBFrom))
                cond.append(table['MKB'].le(actionMKBTo))
        self.addEqCond(cond, table, 'status', filter, 'actionStatus')
        if 'expertOrgStructureId' in filter or 'expertSpecialityId' in filter:
            tablePerson = db.table('Person')
            queryTable = queryTable.leftJoin(tablePerson, tablePerson['id'].eq(table['setPerson_id']))
            cond.append(tablePerson['deleted'].eq(0))
            if 'expertOrgStructureId' in filter:
                expertOrgStructureId = filter.get('expertOrgStructureId', None)
                if expertOrgStructureId:
                    orgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', expertOrgStructureId)
                    if orgStructureIdList:
                        cond.append(tablePerson['orgStructure_id'].inlist(orgStructureIdList))
            if 'expertSpecialityId' in filter:
                expertSpecialityId = filter.get('expertSpecialityId', None)
                if expertSpecialityId:
                    cond.append(tablePerson['speciality_id'].eq(expertSpecialityId))
        self.addEqCond(cond, table, 'createPerson_id', filter, 'createPersonId')
        self.addDateCond(cond, table, 'createDatetime', filter, 'begCreateDate', 'endCreateDate')
        self.addEqCond(cond, table, 'modifyPerson_id', filter, 'modifyPersonId')
        self.addDateCond(cond, table, 'modifyDatetime', filter, 'begModifyDate', 'endModifyDate')

        expertiseId = filter.get('expertiseId', None)
        expertiseTypeId = filter.get('expertiseTypeId', None)
        expertiseCharacterId = filter.get('expertiseCharacterId', None)
        expertiseKindId = filter.get('expertiseKindId', None)
        expertiseObjectId = filter.get('expertiseObjectId', None)
        expertiseArgumentId = filter.get('expertiseArgumentId', None)
        expertiseIdList = []
        if expertiseId is not None:
            expertiseIdList = getActionTypeIdListByFlatCode(expertiseClass[expertiseId][1])
        else:
            if self.tabExpertMedicalCommissionWidget.currentIndex() != self.tabExpertMedicalCommissionWidget.indexOf(self.tabExpertMedicalSocialInspection):
                expertiseIdList = getActionTypeIdListByFlatCode(u'inspection_disability%')
                expertiseIdList.extend(getActionTypeIdListByFlatCode(u'inspection_case%'))
                cond.append(table['actionType_id'].inlist(expertiseIdList))
        if self.tabExpertMedicalCommissionWidget.currentIndex() == self.tabExpertMedicalCommissionWidget.indexOf(self.tabExpertMedicalSocialInspection):
            cond.append(table['actionType_id'].inlist(getActionTypeIdListByFlatCode(u'inspection_mse%')))
            if expertiseId is not None:
                cond.append(self.expertiseTypeForMSI(expertiseIdList))
            if bool(expertiseTypeId is not None and expertiseTypeId[0]):
                cond.append(self.expertiseTypeForMSI(expertiseTypeId[0]))
            if expertiseCharacterId:
                cond.append(self.expertiseForMSIPropertyValue(u'ActionProperty_rbMedicalBoardExpertiseCharacter', u'Характеристика экспертизы', expertiseCharacterId))
            if expertiseKindId:
                cond.append(self.expertiseForMSIPropertyValue(u'ActionProperty_rbMedicalBoardExpertiseKind', u'Вид экспертизы', expertiseKindId))
            if expertiseObjectId:
                cond.append(self.expertiseForMSIPropertyValue(u'ActionProperty_rbMedicalBoardExpertiseObject', u'Предмет экспертизы', expertiseObjectId))
            if expertiseArgumentId:
                cond.append(self.expertiseForMSIPropertyValue(u'ActionProperty_rbMedicalBoardExpertiseArgument', u'Обоснование экспертизы', expertiseArgumentId))
            if self.chkFilterExpertExportedToExternalISMC.isChecked():
                expertExportedType = filter.get('expertExportedType', 0)
                expertIntegratedISId = filter.get('expertIntegratedISId', None)
                tableActionExport = db.table('Action_Export')
                tableActionExportDetail = db.table('Action_Export_Detail')
                if expertExportedType == 1:
                    queryTable = queryTable.leftJoin(tableActionExport, tableActionExport['master_id'].eq(table['id']))
                    queryTable = queryTable.leftJoin(tableActionExportDetail, tableActionExportDetail['master_id'].eq(tableActionExport['id']))
                    cond.append(db.joinOr([tableActionExport['id'].isNull(), tableActionExportDetail['id'].isNull(), db.notExistsStmt(tableActionExportDetail, [tableActionExportDetail['value'].eq(u'ReferralMSE')])]))
                else:
                    queryTable = queryTable.innerJoin(tableActionExport, tableActionExport['master_id'].eq(table['id']))
                    queryTable = queryTable.innerJoin(tableActionExportDetail, tableActionExportDetail['master_id'].eq(tableActionExport['id']))
                    cond.append(tableActionExportDetail['value'].eq(u'ReferralMSE'))
                if expertIntegratedISId:
                    cond.append(tableActionExport['system_id'].eq(expertIntegratedISId))
        else:
            if expertiseId is not None:
                cond.append(table['actionType_id'].inlist(expertiseIdList))
            if bool(expertiseTypeId is not None and expertiseTypeId[0]):
                cond.append(table['actionType_id'].inlist(expertiseTypeId[0]))
            if expertiseCharacterId:
                cond.append(existsPropertyValue(u'ActionProperty_rbMedicalBoardExpertiseCharacter', u'Характеристика экспертизы', expertiseCharacterId))
            if expertiseKindId:
                cond.append(existsPropertyValue(u'ActionProperty_rbMedicalBoardExpertiseKind', u'Вид экспертизы', expertiseKindId))
            if expertiseObjectId:
                cond.append(existsPropertyValue(u'ActionProperty_rbMedicalBoardExpertiseObject', u'Предмет экспертизы', expertiseObjectId))
            if expertiseArgumentId:
                cond.append(existsPropertyValue(u'ActionProperty_rbMedicalBoardExpertiseArgument', u'Обоснование экспертизы', expertiseArgumentId))

        if 'clientIds' in filter:
            clientIds = filter.get('clientIds')
            cond.append(tableEvent['client_id'].inlist(clientIds))
        if 'eventIds' in filter:
            eventIds = filter.get('eventIds')
            cond.append(table['event_id'].inlist(eventIds))
        if 'Client' in order:
            tableClient = db.table('Client')
            queryTable = queryTable.leftJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
        if 'vrbSetPersonWithSpeciality.name' in order:
            tableSetPerson = db.table('vrbPersonWithSpeciality').alias('vrbSetPersonWithSpeciality')
            queryTable = queryTable.leftJoin(tableSetPerson, tableSetPerson['id'].eq(table['setPerson_id']))
        if 'vrbPersonWithSpeciality.name' in order:
            tablePersonSP = db.table('vrbPersonWithSpeciality')
            queryTable = queryTable.leftJoin(tablePersonSP, tablePersonSP['id'].eq(table['person_id']))
        if 'expertNumberMC' in order:
            cols = [table['id']]
            cols.append(self.getPropertyValueToOrder(u'Номер ЛН', u'expertNumberMC', u'ActionProperty_String'))
        if 'expertNumberExpertise' in order:
            cols = [table['id']]
            cols.append(self.getPropertyValueToOrder(u'Номер', u'expertNumberExpertise', u'ActionProperty_String'))
        if 'expertDecision' in order:
            cols = [table['id']]
            cols.append(self.getPropertyValueToOrder(u'Решение', u'expertDecision', u'ActionProperty_String'))
        if 'directionDateMSI' in order:
            cols = [table['id']]
            cols.append(self.getPrevActionFieldMSI(u'directionDate', u'directionDateMSI'))
        if 'plannedEndDateMSI' in order:
            cols = [table['id']]
            cols.append(self.getPrevActionFieldMSI(u'plannedEndDate', u'plannedEndDateMSI'))
        if 'endDateMSI' in order:
            cols = [table['id']]
            cols.append(self.getPrevActionFieldMSI(u'endDate', u'endDateMSI'))
        try:
            QtGui.QApplication.setOverrideCursor(QtGui.QCursor(Qt.WaitCursor))
            if 'expertNumberMC' in order or 'expertNumberExpertise' in order or 'expertDecision' in order or 'directionDateMSI' in order or 'plannedEndDateMSI' in order or 'endDateMSI' in order:
                records = db.getRecordList(queryTable,
                               cols,
                               cond,
                               order)
                idList = []
                if not 'clientIds' in filter and not 'eventIds' in filter:
                    for record in records:
                        actionId = forceRef(record.value('id'))
                        if actionId:
                            idList.append(actionId)
                else:
                    for record in records:
                        actionId = forceRef(record.value('id'))
                        if actionId and actionId not in idList:
                            idList.append(actionId)
            else:
                if not 'clientIds' in filter and not 'eventIds' in filter:
                    getIdList = db.getIdList
                else:
                    getIdList = db.getDistinctIdList
                idList = getIdList(queryTable,
                               table['id'].name(),
                               cond,
                               order)
            currentTable.setIdList(idList, posToId)
        finally:
            QtGui.QApplication.restoreOverrideCursor()
#        actionsFilterType = filter['actionsFilterType']
        hideClientInfo = 'clientIds' in filter and len(filter['clientIds']) == 1
        for i in range(3):
            currentTable.setColumnHidden(i, hideClientInfo)
        self.updateClientsListRequest = self.updateClientsListRequest or not hideClientInfo


    def getPrevActionFieldMSI(self, fieldName, aliasName):
        return u'''(SELECT ActionMSI.%s
                    FROM Action AS ActionMSI
                    WHERE ActionMSI.prevAction_id = Action.id AND ActionMSI.deleted = 0) AS %s'''%(fieldName, aliasName)


    def getPropertyValueToOrder(self, propertyName, aliasName, tableName):
        return u'''(SELECT APS.value
            FROM ActionProperty AS AP
            INNER JOIN ActionPropertyType AS APT ON AP.type_id = APT.id
            INNER JOIN %s AS APS ON APS.id = AP.id
            WHERE AP.action_id = Action.id AND APT.actionType_id = Action.actionType_id
            AND  Action.id IS NOT NULL
            AND APT.deleted = 0 AND AP.deleted = 0 AND APT.name %s) AS %s'''%(tableName, updateLIKE(propertyName), aliasName)


# ==================== Visit_Page ======================
    def updateVisitsList(self, filter, posToId=None):
#        """
#            в соответствии с фильтром обновляет список визитов.
#        """
        self.__visitFilter = filter
        db = QtGui.qApp.db
        tableVisit = db.table('Visit')
        tableEvent = db.table('Event')
        queryTable = tableVisit.leftJoin(tableEvent, tableEvent['id'].eq(tableVisit['event_id']) )
        cond = [tableVisit['deleted'].eq(0), tableEvent['deleted'].eq(0)]
        self.addEqCond(cond, tableVisit, 'id', filter, 'id')
        self.addEqCond(cond, tableVisit, 'createPerson_id', filter, 'createPersonId')
        self.addDateCond(cond, tableVisit, 'createDatetime', filter, 'begCreateDate', 'endCreateDate')
        self.addEqCond(cond, tableVisit, 'modifyPerson_id', filter, 'modifyPersonId')
        self.addDateCond(cond, tableVisit, 'modifyDatetime', filter, 'begModifyDate', 'endModifyDate')
        if 'clientIds' in filter:
            clientIds = filter.get('clientIds')
            cond.append(tableEvent['client_id'].inlist(clientIds))
        if 'eventIds' in filter:
            eventIds = filter.get('eventIds')
            cond.append(tableVisit['event_id'].inlist(eventIds))
        self.addDateTimeCond(cond, tableVisit, 'date', filter, 'begExecDateTime', 'endExecDateTime')
        if 'visitTypeId' in filter:
            cond.append(tableVisit['visitType_id'].eq(filter['visitTypeId']))
        if 'serviceId' in filter:
            cond.append(tableVisit['service_id'].eq(filter['serviceId']))
        if 'sceneId' in filter:
            cond.append(tableVisit['scene_id'].eq(filter['sceneId']))
        addTableExecPerson = False
        if 'personId' in filter:
            execPersonId = filter['personId']
            if execPersonId == -1:
                cond.append(tableVisit['person_id'].isNull())
            else:
                cond.append(tableVisit['person_id'].eq(execPersonId))
        else:
            if 'orgStructureId' in filter:
                    if not addTableExecPerson:
                        addTableExecPerson = True
                        tablePersonExec = db.table('Person').alias('PersonExec')
                        queryTable = queryTable.join(tablePersonExec, tablePersonExec['id'].eq(tableVisit['person_id']))
                    execSetOrgStructureId = filter['orgStructureId']
                    execSetOrgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', execSetOrgStructureId) if execSetOrgStructureId else []
                    cond.append(tableVisit['person_id'].isNotNull())
                    cond.append(tablePersonExec['orgStructure_id'].isNotNull())
                    cond.append(tablePersonExec['orgStructure_id'].inlist(execSetOrgStructureIdList))
            if 'specialityId' in filter:
                    if not addTableExecPerson:
                        addTableExecPerson = True
                        tablePersonExec = db.table('Person').alias('PersonExec')
                        queryTable = queryTable.join(tablePersonExec, tablePersonExec['id'].eq(tableVisit['person_id']))
                    cond.append(tableVisit['person_id'].isNotNull())
                    cond.append(tablePersonExec['speciality_id'].eq(filter['specialityId']))

        if 'assistantId' in filter:
            assistantId = filter['assistantId']
            if assistantId == -1:
                cond.append(tableVisit['assistant_id'].isNull())
            else:
                cond.append(tableVisit['assistant_id'].eq(assistantId))
        payStatusFinanceCode = filter.get('payStatusFinanceCode', None)
        if payStatusFinanceCode:
            payStatusCode = filter.get('payStatusCode', 0)
            mask  = getPayStatusMaskByCode(payStatusFinanceCode)
            value = getPayStatusValueByCode(payStatusCode, payStatusFinanceCode)
            cond.append('((%s & %d) = %d)' % (tableVisit['payStatus'].name(), mask, value))
        if 'financeId' in filter:
            financeId = filter['financeId']
            if financeId:
                cond.append(tableVisit['finance_id'].eq(financeId))
            else:
                cond.append(tableVisit['finance_id'].isNull())

        orderBY = u'date DESC, id'
        def ref(tbl, id):
            return u'(select name from %s where id = Visit.%s)' % (tbl, id) + u' %s'
        for key, value in self.tblVisits.model().headerSortingCol.items():
            if value:
                ASC = u'ASC'
            else:
                ASC = u'DESC'
            if key == 0:
                orderBY = u'(select concat(lastName,firstName,patrName) from Client where id = Event.client_id) %s' % ASC
            elif key == 1:
                orderBY = u'(select birthDate from Client where id = Event.client_id) %s' % ASC
            elif key == 2:
                orderBY = u'(select sex from Client where id = Event.client_id) %s' % ASC
            elif key == 3:
                orderBY = u'date %s' % ASC
            elif key == 4:
                orderBY = ref(u'rbVisitType', u'visitType_id') % ASC
            elif key == 5:
                orderBY = ref(u'vrbPersonWithSpecialityAndOrgStr', u'person_id') % ASC
            elif key == 6:
                orderBY = ref(u'rbScene', u'scene_id') % ASC
            elif key == 7:
                orderBY = u'Visit.isPrimary %s' % ASC
            elif key == 8:
                orderBY = ref(u'rbService', u'service_id') % ASC
            elif key == 9:
                orderBY = u'Visit.payStatus %s' % ASC
            elif key == 10:
                orderBY = ref(u'vrbPersonWithSpecialityAndOrgStr', u'assistant_id') % ASC
            elif key == 11:
                orderBY = u'(select externalId from Event where id = Visit.event_id) %s' % ASC
            elif key == 12:
                orderBY = ref(u'rbFinance', u'finance_id') % ASC
        try:
            QtGui.QApplication.setOverrideCursor(QtGui.QCursor(Qt.WaitCursor))
            idList = db.getDistinctIdList(queryTable,
                           tableVisit['id'].name(),
                           cond,
                           orderBY)
            self.tblVisits.setIdList(idList, posToId)
        finally:
            QtGui.QApplication.restoreOverrideCursor()
        visitsFilterType = self.cmbFilterVisit.currentIndex()
        if visitsFilterType == 0:
            filter['clientIds'] = [ self.selectedClientId() ]
        elif visitsFilterType == 1:
            filter['clientIds'] = self.modelClients.idList()
        elif visitsFilterType == 2:
            filter['eventIds'] = [ self.tblEvents.currentItemId() ]
        elif visitsFilterType == 3:
            filter['eventIds'] = self.modelEvents.idList()
        filter['visitsFilterType']=visitsFilterType
        hideClientInfo = 'clientIds' in filter and len(filter['clientIds']) == 1
        for i in xrange(3):
            self.tblVisits.setColumnHidden(i, hideClientInfo)
        self.updateClientsListRequest = self.updateClientsListRequest or not hideClientInfo

# ====== Visit_Page ===:)

#########################################################################
    def getEventListByDates(self, context, clientId, begDate, endDate):
        if not (begDate and endDate):
            return context.getInstance(CEventInfoList, [])
        if type(begDate) == CDateInfo:
            begDate = begDate.date
        if type(endDate) == CDateInfo:
            endDate = endDate.date
        db = QtGui.qApp.db
        table = db.table("Event")
        cond = [table['setDate'].dateLe(endDate),  table['setDate'].dateGe(begDate), table['client_id'].eq(clientId)]
        recordList = db.getRecordList(table, [table['id'].name()],  cond)
        idList = []
        for record in recordList:
            idList.append(forceRef(record.value(0)))
        return context.getInstance(CEventInfoList, idList)
        
        

    def getKerContextData(self):
        clientId = self.currentClientId()
        tempInvalidId = self.currentTempInvalidId()
        data = getClientContextData(clientId)
        context = data['client'].context
        tempInvalidInfo = context.getInstance(CTempInvalidInfo, tempInvalidId)
        if self.tabWidgetExpertTempInvalidDetails.currentIndex() == 0: #вкладка "Периоды"
            data['isDuplicate'] = False
            data['tempInvalid'] = tempInvalidInfo
            data['getEventList'] = lambda begDate, endDate: getEventListByDates(context, clientId, begDate, endDate)
            #tempInvalidPeriodId = self.currentTempInvalidPeriodId() ??????????
        # else: # self.tabWidgetExpertTempInvalidDetails.currentIndex() == 1: #вкладка "Дубликаты"
        #     tempInvalidDuplicateId = self.currentTempInvalidDuplicateId()
        #     tempInvalidInfo = context.getInstance(CTempInvalidDuplicateInfo, tempInvalidId, tempInvalidDuplicateId)
        #     data['isDuplicate'] = (tempInvalidDuplicateId > 0)
        #     data['tempInvalid'] = tempInvalidInfo
        #     data['getEventList'] = lambda begDate, endDate: getEventListByDates(context, clientId, begDate, endDate)
        return data


    def getKerListContextData(self):
        context = CInfoContext()
        idList = self.modelExpertTempInvalid.idList()
        tempInvalidId = self.currentTempInvalidId()
        tempInvalidListInfo = CTempInvalidAllInfoList(context, idList)
        clientId = self.currentClientId()
        tempInvalidInfo = context.getInstance(CTempInvalidInfo, tempInvalidId)
        begDate = endDate = None
        data = getClientContextData(clientId)
        context = data['client'].context
        if self.chkFilterExpertBegDate.isChecked():
            begDate = CDateInfo(self.edtFilterExpertBegBegDate.date())
            endDate = CDateInfo(self.edtFilterExpertEndBegDate.date())
        data['tempInvalidList'] = tempInvalidListInfo
        data['tempInvalid'] = tempInvalidInfo
        data['getEventList'] = lambda begDate, endDate: getEventListByDates(context, clientId, begDate, endDate)
        data['filter'] = {'begDate': begDate, 'endDate': endDate}
        return data

################################################################################


    @pyqtSignature('int')
    def on_tabMain_currentChanged(self, index):
        index = self.tabMain.originalIndex(self.tabMain.currentWidget())
        keyboardModifiers = QtGui.qApp.keyboardModifiers()
        if index == 0:  # реестр
            db = QtGui.qApp.db
            eventId = self.currentEventId()
            clientId = forceRef(db.translate('Event', 'id', eventId, 'client_id'))
            self.syncSplitters(self.splitterRegistry)
#            self.focusClients()
            if self.updateClientsListRequest:
                self.updateClientsList(self.__filter)
            if self.tabMainCurrentPage == 1:
                if keyboardModifiers & Qt.ControlModifier == Qt.ControlModifier:
                    self.tblClients.setCurrentItemId(clientId)
                if self.updateClientsListRequest:
                    self.updateClientsList(self.__filter)
            self.actSurveillancePlanningClients.setEnabled(bool(isSurveillanceActive(clientId, {}, {'begDate': QDate.currentDate()})))
            self.currentClientFromEvent = False
            self.currentClientFromAction = False
            self.currentClientFromExpert = False
        elif index == 1:  # осмотры
            self.syncSplitters(self.splitterEvents)
            if keyboardModifiers & Qt.AltModifier:
                clientsFilterType = 2
            elif keyboardModifiers & Qt.ControlModifier:
                clientsFilterType = 1
            elif keyboardModifiers & Qt.ShiftModifier:
                clientsFilterType = -1
            else:
                clientsFilterType = 0
            if clientsFilterType == 0 and self.currentClientFromEvent and not self.currentClientFromAction and not self.currentClientFromExpert:
                # возврат из мед. карты или подобного, на одного пациента
                self.updateEventInfo(self.currentEventId())
            else:
                self.updateEventInfo(None)
                if clientsFilterType != -1:
                    self.on_buttonBoxEvent_reset()
                    self.cmbFilterEventByClient.setCurrentIndex(clientsFilterType)
                self.on_buttonBoxEvent_apply()
            self.currentClientFromEvent = True
            self.currentClientFromAction = False
            self.currentClientFromExpert = False
        elif index == 2:  # мед.карта
            self.syncSplitters(self.splitterAmbCard)
            self.updateAmbCardInfo()
            self.tabAmbCardContent.resetWidgets()
        elif index == 3:  # Обслуживание
            self.syncSplitters(self.splitterActions)
            self.updateActionInfo(None)
            if self.currentClientFromEvent: # переход сквозь осмотры
                cmbFilterActionFlags = QVariant(int(Qt.ItemIsEnabled|Qt.ItemIsSelectable))
                cmbFilterActionDefault = 2
            else:
                cmbFilterActionFlags = QVariant(0)
                cmbFilterActionDefault = 0
            self.cmbFilterAction.setItemData(2, cmbFilterActionFlags, Qt.UserRole-1)
            self.cmbFilterAction.setItemData(3, cmbFilterActionFlags, Qt.UserRole-1)

            if keyboardModifiers & Qt.AltModifier == Qt.AltModifier:
                clientsFilterType = 5
            elif keyboardModifiers & Qt.ControlModifier == Qt.ControlModifier:
                clientsFilterType = cmbFilterActionDefault+1
            elif keyboardModifiers & Qt.ShiftModifier == Qt.ShiftModifier:
                clientsFilterType = -1
            else:
                clientsFilterType = cmbFilterActionDefault
            if clientsFilterType != -1:
                self.on_buttonBoxAction_reset()
                self.cmbFilterAction.setCurrentIndex(clientsFilterType)
            self.on_buttonBoxAction_apply()
            self.currentClientFromEvent = False
            self.currentClientFromAction = True
            self.currentClientFromExpert = False
        elif index == 4: # КЭР
            self.syncSplitters(self.splitterExpert)
            self.updateTempInvalidInfo(None, noPrev=True)
            self.updateDocumentsExInfo(None, noPrev=True)
            if self.currentClientFromEvent: # переход сквозь осмотры
                cmbFilterExpertFlags = QVariant(int(Qt.ItemIsEnabled|Qt.ItemIsSelectable))
                cmbFilterExpertDefault = 2
            else:
                cmbFilterExpertFlags = QVariant(0)
                cmbFilterExpertDefault = 0
            self.cmbFilterExpert.setItemData(2, cmbFilterExpertFlags, Qt.UserRole-1)
            self.cmbFilterExpert.setItemData(3, cmbFilterExpertFlags, Qt.UserRole-1)
            self.cmbFilterExpert.setItemData(6, cmbFilterExpertFlags, Qt.UserRole-1)
            self.cmbFilterExpert.setItemData(7, cmbFilterExpertFlags, Qt.UserRole-1)
            if keyboardModifiers & Qt.AltModifier == Qt.AltModifier:
                clientsFilterType = 5
            elif keyboardModifiers & Qt.ControlModifier == Qt.ControlModifier:
                clientsFilterType = cmbFilterExpertDefault + 1
            elif keyboardModifiers & Qt.ShiftModifier == Qt.ShiftModifier:
                clientsFilterType = -1
            else:
                clientsFilterType = cmbFilterExpertDefault
            if clientsFilterType != -1:
                self.on_buttonBoxExpert_reset()
                self.cmbFilterExpert.setCurrentIndex(clientsFilterType)
            self.on_tabWidgetTempInvalidTypes_currentChanged(self.tabWidgetTempInvalidTypes.currentIndex())
#            self.on_buttonBoxExpert_apply()
            self.currentClientFromEvent = False
            self.currentClientFromAction = False
            self.currentClientFromExpert = True
        elif index == 5: # Визиты
            self.syncSplitters(self.splitterVisits)
            if self.currentClientFromEvent: # переход сквозь осмотры
                cmbFilterVisitFlags = QVariant(int(Qt.ItemIsEnabled|Qt.ItemIsSelectable))
            else:
                cmbFilterVisitFlags = QVariant(0)
            self.cmbFilterVisit.setItemData(2, cmbFilterVisitFlags, Qt.UserRole-1)
            self.cmbFilterVisit.setItemData(3, cmbFilterVisitFlags, Qt.UserRole-1)
            self.on_buttonBoxVisit_apply()
            self.currentClientFromEvent = False
            self.currentClientFromAction = False
            self.currentClientFromExpert = False
            self.updateVisitInfo(self.tblVisits.currentItemId())
        self.tabMainCurrentPage = index


    def getFilterInfoBed(self):
        def getNameOrgStructure(orgStructureId):
            db = QtGui.qApp.db
            if orgStructureId:
                tableOS = db.table('OrgStructure')
                record = db.getRecordEx(tableOS, [tableOS['name']], [tableOS['deleted'].eq(0), tableOS['id'].eq(orgStructureId)])
                if record:
                    nameOrgStructure = forceString(record.value(0))
                else:
                    nameOrgStructure = forceString(None)
            else:
                tableO = db.table('Organisation')
                recordOrg = db.getRecordEx(tableO, [tableO['shortName']], [tableO['deleted'].eq(0), tableO['id'].eq(QtGui.qApp.currentOrgId())])
                if recordOrg:
                    nameOrgStructure = forceString(recordOrg.value(0))
                else:
                    nameOrgStructure = forceString(None)
            return nameOrgStructure
        infoBeds = u''
        if self.chkFilterBeds.isChecked():
            statusBeds = self.cmbFilterStatusBeds.currentText()
            orgStructureId = self.cmbFilterOrgStructureBeds.value()
            infoBeds = u'; по койкам: статус %s подразделение %s'%(statusBeds, getNameOrgStructure(orgStructureId))
        infoAddressOrgStructure = u''
        if self.chkFilterAddressOrgStructure.isChecked():
            orgStructureType = self.cmbFilterAddressOrgStructureType.currentText()
            orgStructureId = self.cmbFilterAddressOrgStructure.value()
            infoAddressOrgStructure = u'; по участкам: тип %s подразделение %s'%(orgStructureType, getNameOrgStructure(orgStructureId))
        return [infoBeds, infoAddressOrgStructure]


    def _updateFilterVaccinationType(self):
        vaccineIdList = self.modelFilterVaccine.getCheckedIdList()
        infectionIdList = self.modelFilterInfection.getCheckedIdList()
        vaccinationCalendarId = self.cmbFilterVaccinationCalendar.value()

        if bool(vaccinationCalendarId) and bool(infectionIdList) and not bool(vaccineIdList):
            filter = 'master_id = %d AND infection_id IN (%s)' % (vaccinationCalendarId, ','.join(map(str, infectionIdList)))
            self.cmbFilterVaccinationType.setTable('rbVaccinationCalendar_Infection', filter)
        else:
            if not vaccineIdList and infectionIdList:
                vaccineIdList = self.modelFilterVaccine.idList()
            filter = ''
            if vaccineIdList:
                filter = 'master_id IN (%s)' % ','.join(map(str, vaccineIdList))
            self.cmbFilterVaccinationType.setTable('rbVaccine_Schema', filter)


    def on_modelFilterInfection_itemCheckingChanged(self):
        infectionIdList = self.modelFilterInfection.getCheckedIdList()
        if infectionIdList:
            self.chkFilterId.setChecked(False)
            db = QtGui.qApp.db
            tableInfectionVaccine = db.table('rbInfection_rbVaccine')
            tableVaccine = db.table('rbVaccine')
            cond = tableInfectionVaccine['infection_id'].inlist(infectionIdList)
            idList = db.getIdList(tableInfectionVaccine, 'vaccine_id', cond)
            self.modelFilterVaccine.setFilter(tableVaccine['id'].inlist(idList))
        else:
            self.modelFilterVaccine.setFilter('')
        self._updateFilterVaccinationType()


    def on_modelFilterVaccine_itemCheckingChanged(self):
        self._updateFilterVaccinationType()


    @pyqtSignature('int')
    def on_cmbFilterVaccinationCalendar_currentIndexChanged(self, index):
        vaccinationCalendarId = self.cmbFilterVaccinationCalendar.value()
        if vaccinationCalendarId:
            db = QtGui.qApp.db
            idList = db.getIdList('rbVaccinationCalendar_Infection', 'infection_id', 'master_id=%d'%vaccinationCalendarId)
            tableInfection = db.table('rbInfection')
            self.modelFilterInfection.setFilter(tableInfection['id'].inlist(idList))
        else:
            self.modelFilterInfection.setFilter('')


    @pyqtSignature('int')
    def on_modelClients_itemsCountChanged(self, count):
        self.realItemCount = self.sender().getRealItemCount()
        batchRegLocatCardProcess = QtGui.qApp.batchRegLocatCardProcess
        if batchRegLocatCardProcess:
            self.lblClientsCount.setText(u'ВЫ НАХОДИТЕСЬ В РЕЖИМЕ ИЗМЕНЕНИЯ МЕСТА НАХОЖДЕНИЯ КАРТЫ!')
        else:
            self.lblClientsCount.setText(formatRecordsCount2(count, self.realItemCount))
        realCount = formatRecordsCount2(count, self.realItemCount)
        self.realCount(realCount)

    def realCount(self, realCount):
        self.realCount1 = realCount

    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelClients_currentRowChanged(self, current, previous):
        clientId = self.clientId(current)
        self.showClientInfo(clientId)
        self.tabMain.setTabEnabled(1, current.isValid())
        self.updateQueue()

        selectedRows = []
        rowCount = self.tblClients.model().rowCount()
        for index in self.tblClients.selectedIndexes():
            if index.row() < rowCount:
                row = index.row()
                if row not in selectedRows:
                    selectedRows.append(row)

        self.lblClientsCount.setText(self.realCount1 + u', из них выделено ' + forceString(len(selectedRows)))




    def updateQueue(self):
        clientId = self.currentClientId()
        self.modelSchedules.loadData(clientId)
        self.modelVisitsBySchedules.loadData(clientId)
        self.modelCanceledSchedules.loadData(clientId)
        self.modelExternalNotification.loadData(clientId)


    def updateCurrentClientInfo(self):
        self.updateClientInfo(QtGui.qApp.currentClientId())
        self.updateQueue()


    def updateClientInfo(self, clientId):
        # обновляем текст во всех шильдиках сразу,
        # чтобы при переключении между вкладками
        # текст был синхронизирован
        txtInfoList = [
            self.txtClientInfoBrowser,  # картотека
            self.txtClientInfoBrowserEvents,  # обращение
            self.txtClientInfoBrowserAmbCard,  # мед карта
            self.txtClientInfoBrowserActions,  # обслуживание
            self.txtClientInfoBrowserExpert,  # кэр
            self.txtClientInfoBrowserVisits,  # визиты
        ]
        bannerHtml = getClientBanner(clientId) if clientId else ''
        for txtInfo in txtInfoList:
            txtInfo.setHtml(bannerHtml)
        self.setUpdateF111Enabled(clientId)
    
    
    def setUpdateF111Enabled(self, clientId):
        clientSex, clientAge = getClientSexAge(clientId)
        self.actUpdateF111.setVisible(clientSex == 2)
        if self.actUpdateF111.isVisible():
            self.actUpdateF111.setEnabled(self.setIsUpdateF111Enable(clientId) and clientSex == 2)


    @pyqtSignature('QModelIndex')
    def on_tblClients_doubleClicked(self, index):
        self.editCurrentClient()
        self.focusClients()


    def showQueuePosition(self, scheduleItemId):
        if QtGui.qApp.mainWindow.dockResources:
            QtGui.qApp.mainWindow.dockResources.showQueueItem2(scheduleItemId)


    @pyqtSignature('QModelIndex')
    def on_tblSchedules_doubleClicked(self, index):
        if QtGui.qApp.doubleClickQueueClient() == 1:
            self.on_actAmbCreateEvent_triggered()
        elif QtGui.qApp.doubleClickQueueClient() == 2:
                self.on_actAmbChangeNotes_triggered()
        elif QtGui.qApp.doubleClickQueueClient() == 3:
               self.on_actAmbPrintOrder_clicked()
        elif QtGui.qApp.doubleClickQueueClient() == 4:
                self.on_actJumpQueuePosition_triggered()


    @pyqtSignature('')
    def on_actJumpQueuePosition_triggered(self):
        index = self.tblSchedules.currentIndex()
        if index.isValid():
            row = index.row()
            item = self.modelSchedules.items()[row]
            scheduleItemId = forceRef(item.value('id'))
            if scheduleItemId:
                QtGui.qApp.callWithWaitCursor(self, self.showQueuePosition, scheduleItemId)


    @pyqtSignature('QModelIndex')
    def on_tblVisitsBySchedules_doubleClicked(self, index):
        index = self.tblVisitsBySchedules.currentIndex()
        if index.isValid():
            row = index.row()
            eventId = self.modelVisitsBySchedules.getEventId(row)
            if eventId:
                editEvent(self, eventId)
                self.focusEvents()


    @pyqtSignature('')
    def on_actEditClient_triggered(self):
        self.editCurrentClient()
        self.focusClients()


    @pyqtSignature('')
    def on_actOpenClientDocumentTrackingHistory_triggered(self):
        self.openClientDocumentTrackingHistory()


    @pyqtSignature('')
    def on_actEditStatusObservationClient_triggered(self):
        self.updateStatusObservationClient()


    def openClientDocumentTrackingHistory(self):
        try:
            clientId = self.currentClientId()
            if clientId:
                if QtGui.qApp.userHasAnyRight([urRegTabReadLocationCard, urEditLocationCard]):
                    dialog = CClientDocumentTrackingList(self, clientId)
                    try:
                        dialog.exec_()
                        self.updateClientsList(self.__filter, clientId)
                    finally:
                        dialog.deleteLater()
        except:
            pass


    def updateStatusObservationClient(self):
        if QtGui.qApp.userHasAnyRight([urAdmin, urEditStatusObservationClient]):
            try:
                clientIdList = self.tblClients.selectedItemIdList()
                if clientIdList:
                    dialog = CStatusObservationClientEditor(self, clientIdList)
                    try:
                        if dialog.exec_():
                            clientId = clientIdList[0] if len(clientIdList) > 0 else None
                            self.updateClientsList(self.__filter, clientId)
                    finally:
                        dialog.deleteLater()
            except:
                pass


    @pyqtSignature('')
    def on_actCheckClientAttach_triggered(self):
        clientId = self.currentClientId()
        personInfo = getAttachmentPersonInfo(clientId)
        checkClientAttachService(personInfo)

    @pyqtSignature('')
    def on_actPortal_Doctor_triggered(self):
        clientId = self.currentClientId()
        templateId = None
        result = QtGui.qApp.db.getRecordEx('rbPrintTemplate', 'id', '`default` LIKE "%s" AND deleted = 0' % ('%/EMK_V3/indexV2.php%'))

        data = getClientContextData(clientId)

        if result:
            templateId = result.value('id').toString()
            if templateId:
                QtGui.qApp.call(self, applyTemplate, (self, templateId, data))
            else:
                QtGui.QMessageBox.information(self, u'Ошибка', u'Шаблон для перехода на портал врача не найден',
                                              QtGui.QMessageBox.Close, QtGui.QMessageBox.Close)
        else:
            QtGui.QMessageBox.information(self, u'Ошибка', u'Шаблон для перехода на портал врача не найден', QtGui.QMessageBox.Close, QtGui.QMessageBox.Close)



    @pyqtSignature('')
    def on_actShowContingentsClient_triggered(self):
        self.showContingentsClient()


    def showContingentsClient(self):
        try:
            clientId = self.currentClientId()
            if clientId:
                dialog = CShowContingentsClientDialog(self, clientId)
                try:
                    if dialog.exec_():
                        pass
                finally:
                    dialog.deleteLater()
        except:
            pass


    @pyqtSignature('')
    def on_btnEdit_clicked(self):
        self.editCurrentClient()
        self.focusClients()


    @pyqtSignature('')
    def on_btnNew_clicked(self):
        self.editNewClient()
        self.focusClients()


    @pyqtSignature('')
    def on_mnuPrint_aboutToShow(self):
        clientId = self.selectedClientId()
        if clientId:
            self.mnuPrint.setDefaultAction(self.actPrintClient)
            self.actPrintClient.setEnabled(True)
            self.actPrintClient.setVisible(True)
            self.actPrintClientPs.setEnabled(False)
            self.actPrintClientPs.setVisible(False)
            printer = QtGui.qApp.labelPrinter()
            self.actPrintClientLabel.setEnabled(self.clientLabelTemplate is not None and bool(printer))
        else:
            self.mnuPrint.setDefaultAction(self.actPrintClientPs)
            self.actPrintClientPs.setVisible(True)
            self.actPrintClientPs.setEnabled(True)
            self.actPrintClient.setEnabled(False)
            self.actPrintClient.setVisible(False)
            self.actPrintClientLabel.setEnabled(False)


    @pyqtSignature('int')
    def on_actPrintClient_printByTemplate(self, templateId):
        clientId = self.selectedClientId()
        if clientId:
            data = getClientContextData(clientId)
            context = data['client'].context
            data['clientsList'] = context.getInstance(CClientInfoListEx, tuple(self.tblClients.model().idList()))
            data['clientId'] = clientId
            QtGui.qApp.call(self, applyTemplate, (self, templateId, data))

    @pyqtSignature('int')
    def on_actPrintClientPs_printByTemplate(self, templateId):
        clientId = None
        data = getClientContextData(clientId)
        data['clientId'] = clientId
        QtGui.qApp.call(self, applyTemplate, (self, templateId, data))


    @pyqtSignature('')
    def on_actPrintClientLabel_triggered(self):
        clientId = self.selectedClientId()
        printer = QtGui.qApp.labelPrinter()
        if clientId and self.clientLabelTemplate and printer:
            clientInfo = getClientInfo2(clientId)
            QtGui.qApp.call(self, directPrintTemplate, (self.clientLabelTemplate.id, {'client':clientInfo}, printer))


    @pyqtSignature('')
    def on_actPrintClientList_triggered(self):
        self.tblClients.setReportHeader(u'Список пациентов')
        self.tblClients.setReportDescription(self.getClientFilterAsText())
        mask = [True]*(self.modelClients.columnCount())
        orientation = QtGui.QPrinter.Landscape
        self.tblClients.printContent(mask, orientation)
        self.focusClients()


    @pyqtSignature('')
    def on_actFilter_triggered(self):
        self.on_btnFilter_clicked()


    @pyqtSignature('')
    def on_btnFilter_clicked(self):
        for s in self.chkListOnClientsPage:
            chk = s[0]
            if chk.isChecked():
                self.activateFilterWdgets(s[1])
                return
        self.chkFilterBirthDay.setChecked(True)


    @pyqtSignature('')
    def on_actClientIdBarcodeScan_triggered(self):
        self.on_buttonBoxClient_reset()
        self.cmbFilterAccountingSystem.setValue(None)
        self.chkFilterId.setFocus(Qt.OtherFocusReason)
        self.chkFilterId.setChecked(True)


    @pyqtSignature('')
    def on_actShowPacsImages_triggered(self):
        explorer = CPacsExplorer(self.currentClientId())
        explorer.exec_()


    @pyqtSignature('')
    def on_actNotify_triggered(self):
        CNotifyDialog(self.tblClients.selectedItemIdList(),
                      CNotificationRule.ntRegistry).exec_()


    @pyqtSignature('')
    def on_actNotifyFromTabActions_triggered(self):
        try:
            currentTab = self.tabWidgetActionsClasses.currentWidget()
            db = QtGui.qApp.db
            systemId = forceRef(db.translate('rbExternalSystem', 'code', 'SamsonExtNotification', 'id'))
            tableAction = db.table('Action')
            tableEvent = db.table('Event')
            tableActionExport = db.table('Action_Export')
            table = tableAction.innerJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
            table = table.leftJoin(tableActionExport, db.joinAnd([tableActionExport['master_id'].eq(tableAction['id']),
                                                                  tableActionExport['system_id'].eq(systemId)
                                                                 ]
                                                                )
                                  )
            if currentTab == self.tabActionsStatus:  # Статус
                actionIdList = self.tblActionsStatus.selectedItemIdList()
            elif currentTab == self.tabActionsDiagnostic:  # Диагностика
                actionIdList = self.tblActionsDiagnostic.selectedItemIdList()
            elif currentTab == self.tabActionsCure:  # Лечение
                actionIdList = self.tblActionsCure.selectedItemIdList()
            elif currentTab == self.tabActionsMisc:  # Мероприятия
                actionIdList = self.tblActionsMisc.selectedItemIdList()
            elif currentTab == self.tabActionsAll:  # Все
                actionIdList = self.tblActionsAll.selectedItemIdList()
            else:
                raise Exception(u'Неизвестная таблица действий для оповещения')
            cond = [tableAction['id'].inlist(actionIdList), tableActionExport['id'].isNull(), tableAction['status'].eq(2)]
            cols = [tableAction['id'].alias('actionId'),
                    tableEvent['client_id'].alias('clientId'),
                    tableAction['actionType_id'].alias('actionTypeId')
                   ]
            recordList = db.getRecordList(table, cols, cond)
            if not recordList:
                raise Exception(u'По данным действиям уже было оповещение либо действия еще не закончены')
            clientIdList = []
            actionInfoList = []
            for record in recordList:
                clientId = forceRef(record.value('clientId'))
                clientIdList.append(clientId)
                actionInfoList.append([clientId, forceRef(record.value('actionId')), forceRef(record.value('actionTypeId'))])
            CNotifyDialog(clientIdList, actionInfoList).exec_()
        except Exception, e:
            QtGui.qApp.logCurrentException()
            QtGui.QMessageBox.critical( self,
                                        u'',
                                        exceptionToUnicode(e),
                                        QtGui.QMessageBox.Close)


    @pyqtSignature('')
    def on_actNotificationLog_triggered(self):
        CNotificationLogList(self, self.currentClientId()).exec_()


    @pyqtSignature('')
    def on_actActionGroupSign_triggered(self):
        currentTab = self.tabWidgetActionsClasses.currentWidget()
        actionIdList = []
        if currentTab == self.tabActionsStatus:  # Статус
            actionIdList = self.modelActionsStatus.idList()
        elif currentTab == self.tabActionsDiagnostic:  # Диагностика
            actionIdList = self.modelActionsDiagnostic.idList()
        elif currentTab == self.tabActionsCure:  # Лечение
            actionIdList = self.modelActionsCure.idList()
        elif currentTab == self.tabActionsMisc:  # Мероприятия
            actionIdList = self.modelActionsMisc.idList()
        elif currentTab == self.tabActionsAll:  # Все
            actionIdList = self.modelActionsAll.idList()
        else:
            QtGui.QMessageBox.critical(self, u'Ошибка', u'Выбрана неизвестная вкладка с Действиями')

        actionIdList = list(set(actionIdList))

        if QtGui.qApp.checkGlobalPreference(u'23:ActionGroupSignLockByRecord', u'да'):
            try:
                dialog = CActionGroupSignDialog(self, innerAppLock=True)
                dialog.setActionIdList(actionIdList)
                dialog.exec_()
            except:
                QtGui.qApp.logCurrentException()
        else:
            lockIdList = []
            excludedActionIdList = []
            alreadyLockedCount = 0
            lockErrorCount = 0
            for actionId in actionIdList:
                appLockId, message = self.tryLock('Action', actionId, shorted=1)
                if appLockId:
                    lockIdList.append(appLockId)
                else:
                    excludedActionIdList.append(actionId)
                    if message == u'Не удалось установить блокировку':
                        lockErrorCount += 1
                    if message.startswith(u'Данные'):
                        alreadyLockedCount += 1
            if len(excludedActionIdList) > 0:
                QtGui.QMessageBox.information(self, u'Внимание',
                    (u'Из списка были исключены Действия, заблокированные другими пользователями (%d шт)'
                    u' или блокировку на которые установить не удалось (%d шт)') % (alreadyLockedCount, lockErrorCount))

            actionIdList = list(set(actionIdList) - set(excludedActionIdList))
            try:
                dialog = CActionGroupSignDialog(self)
                dialog.setActionIdList(actionIdList)
                dialog.exec_()
            finally:
                for lockId in lockIdList:
                    self.releaseLock(lockId)
    
    @pyqtSignature('')
    def on_actSimplifiedClientSearch_triggered(self):
        if QtGui.qApp.defaultKLADR()[:2] == u'23':
            dlg = CFastSearchDialog(self)
            if dlg.exec_():
                fio, dd, mm, yy, withMask = dlg.getParsedQuery()
                if len(fio) == 0:
                    return
                filter = {}
                filter['lastName'] = fio[0] if withMask else addDotsBefore(fio[0])
                if len(fio) > 1:
                    filter['firstName'] = fio[1]
                if len(fio) > 2:
                    filter['patrName'] = fio[2]
                if dd:
                    if int(yy) < 100:
                        year = int(yy) + 2000  # 2000 + 09, 2000 + 15
                        if year > QDate.currentDate().year():  # 2000 + 88 - 100
                            year = year - 100
                        filter['birthDate'] = QDate(year, int(mm), int(dd))
                    if int(yy) > 100:
                        filter['birthDate'] = QDate(int(yy), int(mm), int(dd))
                filter['archive'] = self.cmbFilterArchive.currentIndex()
                self.updateClientsList(filter)
                self.focusClients()
        else:
            dialog = CSimplifiedClientSearch(self)
            if dialog.exec_():
                ok, nameParts, date = dialog.getParsedKey()
                chkAndWidgets = None
                if ok:
                    self.on_buttonBoxClient_reset()
                    chkAndWidgets = ((self.chkFilterLastName,  self.edtFilterLastName),
                                     (self.chkFilterFirstName, self.edtFilterFirstName),
                                     (self.chkFilterPatrName,  self.edtFilterPatrName),
                                    )
    
                    for part, (chk, edt) in zip(nameParts, chkAndWidgets):
                        chk.setChecked(True)
                        edt.setText(part)
                    if date:
                        self.chkFilterBirthDay.setChecked(True)
                        self.edtFilterBirthDay.setDate(date)
                self.identCard = None
                for part, (chk, edt) in zip(nameParts, chkAndWidgets):
                    chk.setChecked(True)
                    edt.setText(part)
                if date:
                    self.chkFilterBirthDay.setChecked(True)
                    self.edtFilterBirthDay.setDate(date)
                self.extendedPolicyInformation = {}
                self.on_buttonBoxClient_apply()

    @pyqtSignature('')
    def on_actcacheTemplate_triggered(self):
        try:
            if QtGui.qApp.cacheTemplate:
                if QtGui.qApp.cacheTemplate[0] == 'html':
                    reportView = CReportViewDialog(self)
                    reportView.setWindowTitle(u'Шаблон из кэша')
                    reportView.setText(QtGui.qApp.cacheTemplate[1])
                else:
                    try:
                        from Reports.ReportWEBView import CReportWEBViewDialog
                        reportView = CReportWEBViewDialog(self)
                        reportView.setWindowTitle(u'Шаблон из кэша')
                        reportView.btnSignAndAttach.setVisible(False)
                        reportView.btnEdit.setVisible(False)
                        reportView.setHtml(QtGui.qApp.cacheTemplate[1], QtGui.qApp.cacheTemplate[2])
                    except ImportError:
                        pass
                reportView.exec_()
                reportView.deleteLater()
        except:
            pass

    @pyqtSignature('')
    def on_actCreateEvent_triggered(self):
        self.requestNewEvent()


    @pyqtSignature('bool')
    def on_chkFilterExpertLinked_toggled(self, checked):
        self.tblExpertTempInvalidRelation.setVisible(checked)
        self.tblExpertTempInvalidRelationDocumentsEx.setVisible(checked)
        self.tblExpertDisabilityRelation.setVisible(checked)
        self.tblExpertDisabilityRelationDocumentsEx.setVisible(checked)
        self.tblExpertVitalRestrictionRelation.setVisible(checked)
        self.tblExpertVitalRestrictionRelationDocumentsEx.setVisible(checked)
        self.on_buttonBoxExpert_apply()


    @pyqtSignature('bool')
    def on_chkFilterVaccinationPeriod_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterVaccinationPeriod, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterVaccinationCalendar_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
            if not self.cmbFilterVaccinationCalendar.hasTable():
                self.cmbFilterVaccinationCalendar.setTable('rbVaccinationCalendar', addNone=True)
            self.on_cmbFilterVaccinationCalendar_currentIndexChanged(self.cmbFilterVaccinationCalendar.currentIndex())
        else:
            self.modelFilterInfection.setFilter('')
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterVaccinationCalendar, checked)
        self.onChkFilterToggled(self.sender(), checked)



    @pyqtSignature('bool')
    def on_chkFilterVaccinationSeria_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterVaccinationSeria, checked)
        self.onChkFilterToggled(self.sender(), checked)

    @pyqtSignature('bool')
    def on_chkFilterVaccinationType_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterVaccinationType, checked)
        self.onChkFilterToggled(self.sender(), checked)

    @pyqtSignature('bool')
    def on_chkFilterContingent_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterContingent, checked)
        self.onChkFilterToggled(self.sender(), checked)

    @pyqtSignature('bool')
    def on_chkFilterMedicalExemption_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterMedicalExemption, checked)
        self.onChkFilterToggled(self.sender(), checked)

    @pyqtSignature('bool')
    def on_chkFilterMedicalExemptionType_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
            if not self.cmbFilterMedicalExemptionType.hasTable():
                self.cmbFilterMedicalExemptionType.setTable('rbMedicalExemptionType', addNone=True)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterMedicalExemptionType, checked)
        self.onChkFilterToggled(self.sender(), checked)
    
    
    @pyqtSignature('bool')
    def on_chkFilterVaccinationPerson_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterVaccinationPerson, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterId_toggled(self, checked):
        self.onChkFilterToggled(self.chkFilterId, checked)
        if checked:
            if not self.cmbFilterAccountingSystem.hasTable():
                self.cmbFilterAccountingSystem.setTable('rbAccountingSystem', True, 'domain = \'client\'')
                self.cmbFilterAccountingSystem.setValue(
                    forceRef(QtGui.qApp.preferences.appPrefs.get('FilterAccountingSystem', 0)))
            for chk in (self.chkFilterLastName,
                        self.chkFilterFirstName,
                        self.chkFilterPatrName,
                        self.chkFilterBirthDay,
                        self.chkFilterEndBirthDay,
                        self.chkFilterSex,
                        self.chkFilterContact,
                        self.chkFilterSNILS,
                        self.chkFilterDocument,
                        self.chkFilterPolicy,
                        self.chkFilterRegionSMO,
                        self.chkFilterPolicyOnlyActual,
                        self.chkFilterAddress,
                        self.chkFilterAddressCorpus,
                        self.chkFilterWorkOrganisation,
                        self.chkSocStatuses,
                        self.chkFilterDocumentLocation,
                        self.chkFilterDocumentTypeForTracking,
                        self.chkFilterDocumentTypeForTrackingNumber,
                        self.chkFilterStatusObservationType,
                        self.chkFilterContingentType,
                        self.chkFilterCreatePerson,
                        self.chkFilterCreateDate,
                        self.chkFilterModifyPerson,
                        self.chkFilterModifyDate,
                        self.chkFilterEvent,
                        self.chkFilterEventOpen,
                        self.chkFilterAge,
                        self.chkFilterAddressOrgStructure,
                        self.chkFilterBeds,
                        self.chkFilterRegAddressIsEmpty,
                        self.chkFilterLocAddressIsEmpty,
                        self.chkFilterAttach,
                        self.chkFilterNotAttachOrganisation,
                        self.chkFilterToStatement,
                        self.chkFilterAttachType,
                        self.chkFilterExternalNotification,
                        self.chkFilterClientResearch,
                        self.chkFilterClientNoResearch,
                        self.chkFilterAttachNonBase,
                        self.chkFilterTempInvalid,
                        self.chkFilterTFUnconfirmed,
                        self.chkFilterTFConfirmed,
                        self.chkFilterClientConsent,
                        self.chkFilterVaccinationPeriod,
                        self.chkFilterVaccinationCalendar,
                        self.chkFilterVaccinationSeria,
                        self.chkFilterVaccinationType,
                        self.chkFilterContingent,
                        self.chkFilterMedicalExemption,
                        self.chkFilterMedicalExemptionType,
                        self.chkFilterVaccinationPerson,
                        self.chkFilterClientNote,
                        self.chkFilterIdentification,
                       ):
                chk.setChecked(False)
            self.tblFilterInfection.uncheckAll()
            self.tblFilterVaccine.uncheckAll()


    @pyqtSignature('int')
    def on_cmbFilterAccountingSystem_currentIndexChanged(self, index):
        self.edtFilterId.setValidator(None)
        if self.cmbFilterAccountingSystem.value():
            self.edtFilterId.setValidator(None)
        else:
            self.edtFilterId.setValidator(self.idValidator)


    @pyqtSignature('bool')
    def on_chkFilterLastName_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterOldLastName_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
        # self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterFirstName_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterOldFirstName_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
        # self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterPatrName_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterOldPatrName_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
        # self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterBirthDay_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
            self.chkFilterAge.setChecked(False)
            self.edtFilterEndBirthDay.setEnabled(self.chkFilterEndBirthDay.isChecked())
        else:
            self.edtFilterEndBirthDay.setEnabled(False)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterEndBirthDay_toggled(self, checked):
#        if checked:
#            self.chkFilterId.setChecked(False)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterSex_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterContact_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterSNILS_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterDocument_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
            if not self.cmbFilterDocumentType.hasTable():
                self.cmbFilterDocumentType.setTable('rbDocumentType', True,
                                                    'group_id IN (SELECT id FROM rbDocumentTypeGroup WHERE code=\'1\')')
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterDocument, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterPolicy_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
            self.chkInsurerDescendents.setEnabled(True)
            if not self.cmbFilterPolicyType.hasTable():
                self.cmbFilterPolicyType.setTable('rbPolicyType', True, specialValues=((-1, u'ОМС', u'ОМС'),))
            if not self.cmbFilterPolicyKind.hasTable():
                self.cmbFilterPolicyKind.setTable('rbPolicyKind', True)
        else:
            self.chkInsurerDescendents.setEnabled(False)
            self.chkInsurerDescendents.setChecked(False)
        self.onChkFilterToggled(self.sender(), checked)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterPolicy, checked)
        if self.chkFilterRegionSMO.isChecked():
            self.cmbFilterPolicyInsurer.setEnabled(False)
            self.chkInsurerDescendents.setChecked(False)
            self.chkInsurerDescendents.setEnabled(False)
            self.edtFilterPolicySerial.setEnabled(False)
            self.edtFilterPolicyNumber.setEnabled(False)


    @pyqtSignature('bool')
    def on_chkFilterRegionSMO_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
            self.chkInsurerDescendents.setChecked(False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterRegionSMO, checked)
        # self.cmbFilterPolicyInsurer.setEnabled(self.chkFilterPolicy.isChecked() and not checked)
        # self.chkInsurerDescendents.setEnabled(self.chkFilterPolicy.isChecked() and not checked)
        # self.edtFilterPolicySerial.setEnabled(self.chkFilterPolicy.isChecked() and not checked)
        # self.edtFilterPolicyNumber.setEnabled(self.chkFilterPolicy.isChecked() and not checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterPolicyOnlyActual_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('QString')
    def on_edtFilterPolicySerial_textEdited(self, text):
        self.cmbFilterPolicyInsurer.setSerialFilter(text)


    @pyqtSignature('bool')
    def on_chkFilterWorkOrganisation_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkSocStatuses_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
            if not self.cmbSocStatusesType.hasTable():
                self.cmbSocStatusesType.setTable('rbSocStatusType', True)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkSocStatuses, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterDocumentLocation_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
            if not self.cmbFilterDocumentLocation.hasTable():
                self.cmbFilterDocumentLocation.setTable('rbDocumentTypeLocation', True)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterDocumentLocation, checked)
        self.onChkFilterToggled(self.sender(), checked)

    @pyqtSignature('bool')
    def on_chkFilterDocumentTypeForTracking_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
            if not self.cmbFilterDocumentTypeForTracking.hasTable():
                self.cmbFilterDocumentTypeForTracking.setTable('rbDocumentTypeForTracking', True)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterDocumentTypeForTrackingNumber_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterStatusObservationType_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
            if not self.cmbFilterStatusObservationType.hasTable():
                self.cmbFilterStatusObservationType.setTable('rbStatusObservationClientType', True)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterContingentType_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
            if not self.cmbFilterContingentType.hasTable():
                self.cmbFilterContingentType.setTable('rbContingentType', addNone=True)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterContingentType, checked)
        self.onChkFilterToggled(self.sender(), checked)

    
    @pyqtSignature('bool')
    def on_chkFilterContingentSpeciality_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
            if not self.cmbFilterContingentSpeciality.hasTable():
                self.cmbFilterContingentSpeciality.setTable('rbSpeciality', True)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterContingentSpeciality, checked)
        self.onChkFilterToggled(self.sender(), checked)
        
        
    @pyqtSignature('bool')
    def on_chkFilterContingentMKB_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterContingentMKB, checked)
        self.onChkFilterToggled(self.sender(), checked)
    

    @pyqtSignature('bool')
    def on_chkFilterCreatePerson_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterCreatePerson, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterCreateDate_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterCreateDate, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterModifyPerson_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterModifyPerson, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterModifyDate_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterModifyDate, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterEvent_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
            self.chkFilterEventOpen.setChecked(False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterEvent, checked)
        self.onChkFilterToggled(self.sender(), checked)
    
    
    @pyqtSignature('bool')
    def on_chkFilterEventOpen_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
            self.chkFilterEvent.setChecked(False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterEventOpen, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterAge_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
            self.chkFilterBirthDay.setChecked(False)
            self.chkFilterEndBirthDay.setChecked(False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterAge, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('')
    def on_btnSelectWorkOrganisation_clicked(self):
        orgId = selectOrganisation(self, self.cmbWorkOrganisation.value(), False)
        self.cmbWorkOrganisation.updateModel()
        if orgId:
            self.cmbWorkOrganisation.setValue(orgId)


    @pyqtSignature('bool')
    def on_chkFilterAddress_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
            #self.chkFilterAddressOrgStructure.setChecked(False)            #ymd
            self.chkFilterRegAddressIsEmpty.setChecked(False)
            self.chkFilterLocAddressIsEmpty.setChecked(False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterAddress, checked)
        self.onChkFilterToggled(self.sender(), checked)
        self.edtFilterAddressCorpus.setEnabled(self.chkFilterAddressCorpus.isChecked() and checked)

    @pyqtSignature('bool')
    def on_chkResident_toggled(self, checked):
        self.cmbResident.setEnabled(self.chkResident.isChecked())

    @pyqtSignature('bool')
    def on_chkFilterAddressCorpus_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('int')
    def on_cmbFilterAddressCity_currentIndexChanged(self, index):
        code = self.cmbFilterAddressCity.code()
        self.cmbFilterAddressStreet.setCity(code)
        self.cmbFilterAddressOkato.setKladrCode(code)
        
        
    @pyqtSignature('int')
    def on_cmbFilterAddressRelation_currentIndexChanged(self, index):
        filters = [
            self.cmbFilterAddressOkato,
            self.cmbFilterAddressStreet,
            self.edtFilterAddressHouse,
            self.edtFilterAddressCorpus,
            self.edtFilterAddressFlat
            ]
        for filt in filters:
            filt.setDisabled(index)
            filt.clear()
        self.chkFilterAddressCorpus.setDisabled(index)
        self.chkFilterAddressCorpus.setChecked(0 if index else 1)
            


    @pyqtSignature('int')
    def on_cmbFilterAddressOkato_currentIndexChanged(self, index):
        okato = self.cmbFilterAddressOkato.value()
        self.cmbFilterAddressStreet.setOkato(okato)


    @pyqtSignature('int')
    def on_cmbSocStatusesClass_currentIndexChanged(self, index):
        socStatusClassId = self.cmbSocStatusesClass.value()
        if socStatusClassId:
            filter = (u'''rbSocStatusType.id IN (SELECT DISTINCT rbSocStatusClassTypeAssoc.type_id
            FROM  rbSocStatusClassTypeAssoc
            WHERE rbSocStatusClassTypeAssoc.class_id = %s)'''%(socStatusClassId))
        else:
            filter = u''
        self.cmbSocStatusesType.setFilter(filter)


    @pyqtSignature('bool')
    def on_chkFilterAddressOrgStructure_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
            #self.chkFilterAddress.setChecked(False)            #ymd
            self.chkFilterAddressCorpus.setChecked(False)
            self.chkFilterRegAddressIsEmpty.setChecked(False)
            self.chkFilterLocAddressIsEmpty.setChecked(False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterAddressOrgStructure, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterBeds_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterBeds, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterRegAddressIsEmpty_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
            self.chkFilterAddress.setChecked(False)
            self.chkFilterAddressCorpus.setChecked(False)
            self.chkFilterAddressOrgStructure.setChecked(False)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterLocAddressIsEmpty_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
            self.chkFilterAddress.setChecked(False)
            self.chkFilterAddressCorpus.setChecked(False)
            self.chkFilterAddressOrgStructure.setChecked(False)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterAttach_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
            self.chkFilterAttachNonBase.setChecked(False)
            if not self.cmbFilterAttachOrganisation.value():
                self.cmbFilterAttachOrganisation.setValue(QtGui.qApp.currentOrgId())
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterAttach, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterAttachType_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterAttachType, checked)
        for row in self.chkListOnClientsPage:
            if row[0] == self.chkFilterAttachType:
                for element in row[1]:
                    self.setChildElementsVisible(self.chkListOnClientsPage, element, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterExternalNotification_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterExternalNotification, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterClientResearch_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
            if not self.cmbFilterClientResearchKind.hasTable():
                self.cmbFilterClientResearchKind.setTable('rbClientResearchKind', addNone=True)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterClientResearch, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterToStatement_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterAttachNonBase_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
            self.chkFilterAttach.setChecked(False)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterTempInvalid_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterTempInvalid, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkClientMKB_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkClientMKB, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterTFUnconfirmed_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
            self.chkFilterTFConfirmed.setChecked(False)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterClientConsent_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
            if not self.cmbFilterClientConsentType.hasTable():
                self.cmbFilterClientConsentType.setTable('rbClientConsentType', addNone=True)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterClientConsent, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterTFConfirmed_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
            self.chkFilterTFUnconfirmed.setChecked(False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterTFConfirmed, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterClientNote_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterClientNote, checked)
        self.onChkFilterToggled(self.sender(), checked)
    
    @pyqtSignature('bool')
    def on_chkFilterIdentification_toggled(self, checked):
        if checked:
            self.chkFilterId.setChecked(False)
            if not self.cmbFilterIdentification.hasTable():
                self.cmbFilterIdentification.setTable('rbAccountingSystem', True, 'domain = \'client\'')
                self.cmbFilterIdentification.setValue(forceRef(QtGui.qApp.preferences.appPrefs.get('FilterAccountingSystemClient', 0)))
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('QAbstractButton*')
    def on_buttonBoxClient_clicked(self, button):
        buttonCode = self.buttonBoxClient.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.on_buttonBoxClient_apply()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_buttonBoxClient_reset()
            self.identCard = None

    @pyqtSignature('bool')
    def on_chkFilterActionFileAttachId_toggled(self, checked):
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionFileAttachId, checked)
        self.edtFilterActionFileAttachId.setEnabled(checked)
        self.cmbFilterActionAttachedFiles.setEnabled(not checked)
        self.cmbFilterActionTypeDoc.setEnabled(not checked)
        self.cmbFilterActionSigned.setEnabled(not checked)

        

#    @pyqtSignature('')
    def on_buttonBoxClient_apply(self):
        filter = {}
        if self.chkFilterId.isChecked():
            accountingSystemId = self.cmbFilterAccountingSystem.value()
            clientId = forceStringEx(self.edtFilterId.text())
            if not accountingSystemId:
                clientId = parseClientId(clientId)
            if clientId:
                filter['id'] = clientId
                filter['accountingSystemId'] = accountingSystemId

        if self.chkFilterLastName.isChecked():
            tmp = forceStringEx(self.edtFilterLastName.text())
            if tmp:
                if self.chkFilterOldLastName.isChecked():
                    filter['oldLastName'] = tmp
                else:
                    filter['lastName'] = tmp
        if self.chkFilterFirstName.isChecked():
            tmp = forceStringEx(self.edtFilterFirstName.text())
            if tmp:
                if self.chkFilterOldFirstName.isChecked():
                    filter['oldFirstName'] = tmp
                else:
                    filter['firstName'] = tmp
        if self.chkFilterPatrName.isChecked():
            tmp = forceStringEx(self.edtFilterPatrName.text())
            if tmp:
                if self.chkFilterOldPatrName.isChecked():
                    filter['oldPatrName'] = tmp
                else:
                    filter['patrName'] = tmp
        if self.chkFilterBirthDay.isChecked():
            filter['birthDate'] = self.edtFilterBirthDay.date()
            if self.chkFilterEndBirthDay.isChecked():
                filter['endBirthDate'] = self.edtFilterEndBirthDay.date()
        if self.chkFilterDead.isChecked():
            filter['dead'] = True
        if self.chkFilterDeathBegDate.isChecked():
            filter['begDeathDate'] = self.edtFilterDeathBegDate.date()
        if self.chkFilterDeathEndDate.isChecked():
            filter['endDeathDate'] = self.edtFilterDeathEndDate.date()
        if self.chkFilterSex.isChecked():
            filter['sex'] = self.cmbFilterSex.currentIndex()
        if self.chkFilterContact.isChecked():
            contact = forceStringEx(self.edtFilterContact.text())
            if contact:
                filter['contact'] = contact
        if self.chkFilterSNILS.isChecked():
            tmp = trim(forceString(self.edtFilterSNILS.text()).replace('-','').replace(' ',''))
            filter['SNILS'] = tmp
        if self.chkFilterDocument.isChecked():
            typeId = self.cmbFilterDocumentType.value()
            serial = forceStringEx(self.edtFilterDocumentSerial.text())
            number = forceStringEx(self.edtFilterDocumentNumber.text())
            filter['doc'] = (typeId, serial, number)
        if self.chkFilterPolicy.isChecked():
            onlyPolicyActual = self.chkFilterPolicyOnlyActual.isChecked()
            policyActualData = self.edtFilterPolicyActualData.date()
            policyType = self.cmbFilterPolicyType.value()
            policyKind = self.cmbFilterPolicyKind.value()
            insurerId = self.cmbFilterPolicyInsurer.value() if not self.chkFilterRegionSMO.isChecked() else None
            if insurerId:
                if self.chkInsurerDescendents.isChecked():
                    insurerIdList = getOrganisationDescendants(insurerId)
                else:
                    insurerIdList = [insurerId]
            else:
                insurerIdList = None
            serial = forceStringEx(self.edtFilterPolicySerial.text()) if not self.chkFilterRegionSMO.isChecked() else ''
            number = forceStringEx(self.edtFilterPolicyNumber.text()) if not self.chkFilterRegionSMO.isChecked() else ''
            filter['policy'] = (onlyPolicyActual, policyActualData, policyType, policyKind, insurerIdList, serial, number)
        if self.chkFilterRegionSMO.isChecked():
            filter['regionSMO'] = (self.cmbFilterRegionTypeSMO.currentIndex(), self.cmbFilterRegionSMO.code())
        if self.chkResident.isChecked():
            filter['resident'] = self.cmbResident.currentIndex()
        if self.chkFilterWorkOrganisation.isChecked():
            filter['orgId'] = self.cmbWorkOrganisation.value()
        filter['socStatuses'] = self.chkSocStatuses.isChecked()
        if self.chkSocStatuses.isChecked():
            filter['socStatusesCondition'] = self.chkSocStatusesCondition.isChecked()
            filter['socStatusesClass'] = self.cmbSocStatusesClass.value()
            filter['socStatusesType'] = self.cmbSocStatusesType.value()
            filter['socStatusesBegDate'] = self.edtFilterSocStatusesBegDate.date()
            filter['socStatusesEndDate'] = self.edtFilterSocStatusesEndDate.date()
        if self.chkFilterDocumentTypeForTracking.isChecked():
            filter['documentTypeForTracking'] = self.cmbFilterDocumentTypeForTracking.value()
        if self.chkFilterDocumentTypeForTrackingNumber.isChecked():
            filter['documentTypeForTrackingNumber'] = self.edtFilterDocumentTypeForTrackingNumber.text()
        if self.chkFilterDocumentLocation.isChecked():
            filter['documentLocation'] = self.cmbFilterDocumentLocation.value()
            filter['personDocumentLocation'] = self.cmbPersonDocumentLocation.value()
            filter['begDateFilterDocumentLocation'] = self.edtBegDateFilterDocumentLocation.date()
            filter['endDateFilterDocumentLocation'] = self.edtEndDateFilterDocumentLocation.date()
        if self.chkFilterStatusObservationType.isChecked():
            filter['statusObservationType'] = self.cmbFilterStatusObservationType.value()
        if self.chkFilterContingentType.isChecked():
            filter['contingentTypeId'] = self.cmbFilterContingentType.value()
            filter['contingentEventTypeStatus'] = self.cmbFilterContingentEventTypeStatus.currentIndex()
            filter['contingentActionTypeStatus'] = self.cmbFilterContingentActionType.currentIndex()
            if self.chkFilterContingentMKB.isChecked():
                contingentMKBFrom = forceString(self.edtContingentMKBFrom.text())
                contingentMKBTo = forceString(self.edtContingentMKBTo.text())
                filter['contingentMKBFrom'] = contingentMKBFrom if contingentMKBFrom else None
                filter['contingentMKBTo'] = contingentMKBTo if contingentMKBTo else None  
            if self.chkFilterContingentSpeciality.isChecked():
                filter['contingentSpeciality'] = self.cmbFilterContingentSpeciality.value()
        filter['archive'] = self.cmbFilterArchive.currentIndex()
        if self.chkFilterCreatePerson.isChecked():
            filter['createPersonIdEx'] = self.cmbFilterCreatePerson.value()
        if self.chkFilterCreateDate.isChecked():
            filter['begCreateDateEx'] = self.edtFilterBegCreateDate.date()
            filter['endCreateDateEx'] = self.edtFilterEndCreateDate.date()
        if self.chkFilterModifyPerson.isChecked():
            filter['modifyPersonIdEx'] = self.cmbFilterModifyPerson.value()
        if self.chkFilterModifyDate.isChecked():
            filter['begModifyDateEx'] = self.edtFilterBegModifyDate.date()
            filter['endModifyDateEx'] = self.edtFilterEndModifyDate.date()
        if self.chkFilterEvent.isChecked():
            filter['event'] = ( self.chkFilterFirstEvent.isChecked(),
                                self.edtFilterEventBegDate.date(),
                                self.edtFilterEventEndDate.date() )
        if self.chkFilterEventOpen.isChecked():
            filter['eventOpen'] = ( self.edtFilterEventBegDate.date(),
                                    self.edtFilterEventEndDate.date())
        if self.chkFilterAge.isChecked():
            filter['age'] = ((self.edtFilterBegAge.value(), self.cmbFilterBegAge.currentIndex()),
                             (self.edtFilterEndAge.value()+1, self.cmbFilterEndAge.currentIndex())
                            )
        if self.chkFilterAddress.isChecked():
            filter['address'] = (self.cmbFilterAddressType.currentIndex(),
                                 self.cmbFilterAddressRelation.currentIndex(),
                                 self.cmbFilterAddressCity.code(),
                                 self.cmbFilterAddressOkato.value(),
                                 self.cmbFilterAddressStreet.code(),
                                 self.cmbFilterAddressStreet.codeList(),
                                 forceString(self.edtFilterAddressHouse.text()),
                                 self.chkFilterAddressCorpus.isChecked(),
                                 forceString(self.edtFilterAddressCorpus.text()),
                                 forceString(self.edtFilterAddressFlat.text())
                                )
        #elif self.chkFilterAddressOrgStructure.isChecked():
        if self.chkFilterAddressOrgStructure.isChecked():
            filter['addressOrgStructure'] = (self.cmbFilterAddressOrgStructureType.currentIndex(),
                                             self.cmbFilterAddressOrgStructure.value()
                                            )
        else:
            if self.chkFilterRegAddressIsEmpty.isChecked():
                filter['regAddressIsEmpty'] = True
            if self.chkFilterLocAddressIsEmpty.isChecked():
                filter['locAddressIsEmpty'] = True
        if self.chkFilterBeds.isChecked():
            filter['beds'] = (self.cmbFilterStatusBeds.currentIndex(),
                              self.cmbFilterOrgStructureBeds.value()
                             )
        if self.chkFilterAttach.isChecked():
            filter['attachTo'] = self.cmbFilterAttachOrganisation.value()
            if self.chkFilterNotAttachOrganisation.isChecked():
                filter['isNotAttachOrganisation'] = True
        elif self.chkFilterAttachNonBase.isChecked():
            filter['attachToNonBase'] = True
        if self.chkFilterAttachType.isChecked():
            filter['attachType'] = (self.cmbFilterAttachCategory.currentIndex(),
                                    self.cmbFilterAttachType.value(),
                                    self.edtFilterAttachBegDate.date(),
                                    self.edtFilterAttachEndDate.date())
            if self.chkFilterToStatement.isChecked():
                filter['isStatement'] = self.cmbFilterToStatement.currentIndex()
        if self.chkFilterExternalNotification.isChecked():
            db = QtGui.qApp.db
            begDateEN = db.formatDate(self.edtExternalNotificationBegDate.dateTime())
            endDateEN = db.formatDate(self.edtExternalNotificationEndDate.dateTime())
            self.modelExternalNotification.setDate(begDateEN, endDateEN)
            filter['ENbegDate'] = begDateEN
            filter['ENendDate'] = endDateEN
        if self.chkFilterTempInvalid.isChecked():
            filter['tempInvalid'] = (self.edtFilterBegTempInvalid.date(),
                                     self.edtFilterEndTempInvalid.date()
                                    )
        if self.chkFilterTFUnconfirmed.isChecked():
            filter['TFUnconfirmed'] = True
        elif self.chkFilterTFConfirmed.isChecked():
            filter['TFConfirmed'] = (self.edtFilterBegTFConfirmed.date(),
                                     self.edtFilterEndTFConfirmed.date()
                                    )
        if self.chkFilterClientConsent.isChecked():
            filter['clientConsentValue'] = self.cmbFilterClientConsentValue.currentIndex()
            filter['clientConsentTypeId'] = self.cmbFilterClientConsentType.value()
            filter['clientConsentBegDate'] = self.edtFilterClientConsentBegDate.date()
            filter['clientConsentEndDate'] = self.edtFilterClientConsentEndDate.date()
            filter['clientConsentDate1'] = self.edtFilterClientConsentDate1.date()
            filter['clientConsentDate2'] = self.edtFilterClientConsentDate2.date()
            filter['clientPersonConsent'] = self.cmbFilterPersonConsent.value()
        filter['excludeDead'] = self.chkFilterExcludeDead.isChecked()
        if self.chkClientMKB.isChecked():
            clientMKBFrom = forceString(self.edtClientMKBFrom.text())
            clientMKBTo = forceString(self.edtClientMKBTo.text())
            filter['clientMKBFrom'] = clientMKBFrom if clientMKBFrom else None
            filter['clientMKBTo'] = clientMKBTo if clientMKBTo else None      
        if self.chkFilterClientNote.isChecked():
            tmp = forceStringEx(self.edtFilterClientNote.text())
            if tmp:
                filter['clientNote'] = tmp
        if self.chkFilterClientResearch.isChecked():
            filter['clientResearchKind'] = self.cmbFilterClientResearchKind.value()
            filter['clientResearchBegDate'] = self.edtFilterClientResearchBegDate.date()
            filter['clientResearchEndDate'] = self.edtFilterClientResearchEndDate.date()
        if self.chkFilterClientNoResearch.isChecked():
            filter['clientNoResearch'] = self.chkFilterClientNoResearch.isChecked()
        if self.chkFilterIdentification.isChecked():
            filter['identification'] = self.cmbFilterIdentification.value()

        vaccineIdList = self.modelFilterVaccine.getCheckedIdList()
        infectionIdList = self.modelFilterInfection.getCheckedIdList()
        vaccinationCalendarId = None
        if self.chkFilterVaccinationCalendar.isChecked():
            vaccinationCalendarId = self.cmbFilterVaccinationCalendar.value()
        if infectionIdList and not vaccinationCalendarId and not vaccineIdList:
            QtGui.QMessageBox.warning(self, u'Внимание', u'Выберите "План" и/или "Вакцины"')
            return
        
        filter.update(self.getVaccinationClientFilter())
        self.updateClientsList(filter)
        self.focusClients()


    def getVaccinationClientFilter(self):
        filter = {}

        if self.chkFilterVaccinationPeriod.isChecked():
            filter['vaccinationBegDate'] = self.edtFilterVaccinationBegDate.date()
            filter['vaccinationEndDate'] = self.edtFilterVaccinationEndDate.date()

        if self.chkFilterVaccinationCalendar.isChecked():
            filter['vaccinationCalendarId'] = self.cmbFilterVaccinationCalendar.value()

        infectionIdList = self.modelFilterInfection.getCheckedIdList()
        if infectionIdList:
            filter['infectionIdList'] = infectionIdList

        vaccineIdList = self.modelFilterVaccine.getCheckedIdList()
        if vaccineIdList:
            filter['vaccineIdList'] = vaccineIdList

        if self.chkFilterVaccinationSeria.isChecked():
            filter['vaccinationSeria'] = trim(self.edtFilterVaccinationSeria.text())

        if self.chkFilterVaccinationType.isChecked():
            filter['vaccinationType'] = trim(self.cmbFilterVaccinationType.text())

        if self.chkFilterContingent.isChecked():
            filter['vaccinationContingent'] = self.cmbFilterContingent.currentIndex()
        
        if self.chkFilterVaccinationPerson.isChecked():
            filter['vaccinationPerson'] = self.cmbFilterVaccinationPerson.value()
        
        if self.chkFilterMedicalExemption.isChecked():
            filter['medicalExemption'] = self.cmbFilterMedicalExemption.currentIndex()

        if self.chkFilterMedicalExemptionType.isChecked():
            filter['medicalExemptionTypeId'] = self.cmbFilterMedicalExemptionType.value()

        return filter



    @pyqtSignature('int')
    def on_cmbFilterAttachCategory_currentIndexChanged(self, index):
        self.setupCmbFilterAttachTypeCategory(index)


    @pyqtSignature('bool')
    def on_chkFilterExcludeDead_clicked(self, state):
        if state:
            self.chkFilterDead.setChecked(False)
    
    @pyqtSignature('bool')
    def on_chkFilterDead_toggled(self, state):
        self.chkFilterDeathBegDate.setEnabled(state)
        self.chkFilterDeathEndDate.setEnabled(state)
        if state:
            self.chkFilterExcludeDead.setChecked(False)
        else:
            self.chkFilterDeathBegDate.setChecked(False)
            self.chkFilterDeathEndDate.setChecked(False)
        self.setChildElementsVisible(self.chkListOnClientsPage, self.chkFilterDead, state)


#    @pyqtSignature('')
    def on_buttonBoxClient_reset(self):
        for s in self.chkListOnClientsPage:
            chk = s[0]
            if chk.isChecked():
                self.deactivateFilterWdgets(s[1])
                chk.setChecked(False)
        self.chkFilterSNILS.setChecked(QtGui.qApp.getOpeningSnilsCardindex())
        self.cmbFilterArchive.setCurrentIndex(0)
        self.tblFilterInfection.uncheckAll()
        self.tblFilterVaccine.uncheckAll()


    @pyqtSignature('')
    def on_btnScan_clicked(self):
        scaningData = QtGui.qApp.callWithWaitCursor(self, scanning)
        if scaningData:
            self.on_buttonBoxClient_reset()
            if scaningData['lastName']:
                self.chkFilterLastName.setChecked(True)
                self.edtFilterLastName.setText(scaningData['lastName'])
            if scaningData['firstName']:
                self.chkFilterFirstName.setChecked(True)
                self.edtFilterFirstName.setText(scaningData['firstName'])
            if scaningData['patrName']:
                self.chkFilterPatrName.setChecked(True)
                self.edtFilterPatrName.setText(scaningData['patrName'])
            if scaningData['birthDate']:
                self.chkFilterBirthDay.setChecked(True)
                self.edtFilterBirthDay.setDate(scaningData['birthDate'])
            self.on_buttonBoxClient_apply()


    #### Events page #################################

    @pyqtSignature('')
    def on_actEventEditClient_triggered(self):
        clientId = self.currentClientId()
        if not clientId:
            clientId = self.selectedClientId()
        if clientId:
            self.editClient(clientId)
            self.updateEventInfo(self.currentEventId())
            self.updateClientsListRequest = True


    @pyqtSignature('')
    def on_actSendEventFPUMP_triggered(self):
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableContract = db.table('Contract')
        tableFinance = db.table('rbFinance')
        table = tableEvent.leftJoin(tableContract, tableEvent['contract_id'].eq(tableContract['id']))
        table = table.leftJoin(tableFinance, tableContract['finance_id'].eq(tableFinance['id']))
        record = db.getRecordList(table, [tableEvent['execDate'], tableFinance['code']],
                                  tableEvent['id'].eq(self.currentEventId()))
        endDate = forceDate(record[0].value(0))
        financeCode = forceString(record[0].value(1))
        curDate = QDate.currentDate()
        monthAgoDate = QDate(curDate.year(), curDate.month() - 1, curDate.day())
        if financeCode != '2' or endDate is None:
            note = u''
            if financeCode != '2':
                note += u'Выгрузке подлежат только события по ОМС!'
            if endDate is None:
                if len(note):
                    note += u'\n'
                note += u'Выгрузке подлежат только завершённые события!'
            QtGui.QMessageBox.critical(self, u'Ошибка!', note, QtGui.QMessageBox.Ok)
        else:
            import urlparse
            url = forceString(QtGui.qApp.getGlobalPreference('23:servicesURL'))
            if url:
                url = url.replace('\\\\', '//')
                url = urlparse.urljoin(url, '/api/personalized_accounting')
                url += '/$export_specific_event?event_id={0}'.format(self.currentEventId())
            if not url:
                QtGui.QMessageBox.critical(self, u'Внимание!', u'Не указан IP адрес сервера сервиса!', QtGui.QMessageBox.Ok)
            else:
                import requests
                resp = requests.get(url=url)
                if resp:
                    result = json.loads(resp.content)
                    if result.get('success_events') and len(result.get('success_events')):
                        success_result = result['success_events'][0]
                        if success_result['type_action'] == u'update':
                            message_text = anyToUnicode(u'Обновление СЭФД на событие произведено успешно!')
                        else:
                            message_text = anyToUnicode(u'Создание СЭФД на событие произведено успешно!')
                        message_text += anyToUnicode(u'\nИдентификатор СЭФД в ФПУМП: ') + success_result['id_fpump']
                        message_text += anyToUnicode(u'.\nВерсия СЭФД в ФПУМП: ') + success_result['version_revision'] + u'.'
                        QtGui.QMessageBox.information(self, u'Внимание!', message_text, QtGui.QMessageBox.Ok)
                    else:
                        if result.get('errors'):
                            message_text = anyToUnicode(u'При выгрузке произошла ошибка:\n') + forceString(result['errors'][0]['error'])
                        elif result.get('error'):
                            message_text = forceString(result['error'])
                        else:
                            message_text = anyToUnicode(u'При выгрузке произошла ошибка!')
                        QtGui.QMessageBox.warning(self, u'Внимание!', message_text, QtGui.QMessageBox.Ok)
                else:
                    QtGui.QMessageBox.critical(self, u'Внимание!', u'Ошибка выгрузки события!', QtGui.QMessageBox.Ok)


    @pyqtSignature('')
    def on_actEventOpenClientVaccinationCard_triggered(self):
        clientId = self.currentClientId()
        if not clientId:
            clientId = self.selectedClientId()
        if clientId:
            openClientVaccinationCard(self, clientId)


    @pyqtSignature('')
    def on_actCreateRelatedAction_triggered(self):
        db = QtGui.qApp.db
        table = db.table('Client')
        tableAction = db.table('Action')
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        eventId = None

        clientId = self.currentClientId()
        if not clientId:
            clientId = self.selectedClientId()

        recordEventType = db.getRecordEx(tableEventType, [tableEventType['id']],
                                         [tableEventType['context'].like(u'relatedAction%'),
                                          tableEventType['deleted'].eq(0)], u'EventType.id')
        eventTypeId = forceRef(recordEventType.value('id')) if recordEventType else None
        if not eventTypeId:
            QtGui.QMessageBox.warning(self, u'Внимание!',
                                      u'Отсутствует тип события с контекстом "relatedAction"',
                                      QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
            return

        record = db.getRecord(table, '*', clientId)
        self.clientSex = forceInt(record.value('sex'))
        self.clientBirthDate = forceDate(record.value('birthDate'))
        self.clientAge = calcAgeTuple(self.clientBirthDate, QDate.currentDate())
        actionTypeIdList = selectActionTypes(self, self,
                                             [0, 1, 2, 3],
                                             orgStructureId=None,
                                             eventTypeId=None,
                                             contractId=None,
                                             mesId=None,
                                             eventDate=QDate.currentDate(),
                                             visibleTblSelected=False,
                                             preActionTypeIdList=[])
        if actionTypeIdList:
            prevEventId = self.currentEventId()
            recordEvent = tableEvent.newRecord()
            recordEvent.setValue('createDatetime', toVariant(QDateTime.currentDateTime()))
            recordEvent.setValue('createPerson_id', toVariant(QtGui.qApp.userId))
            recordEvent.setValue('modifyDatetime', toVariant(QDateTime.currentDateTime()))
            recordEvent.setValue('modifyPerson_id', toVariant(QtGui.qApp.userId))
            recordEvent.setValue('setDate', toVariant(QDateTime.currentDateTime()))
            recordEvent.setValue('eventType_id', toVariant(eventTypeId))
            recordEvent.setValue('client_id', toVariant(clientId))
            recordEvent.setValue('prevEvent_id', toVariant(prevEventId))
            eventId = db.insertRecord(tableEvent, recordEvent)

            if eventId:
                recordEvent.setValue('id', toVariant(eventId))

        for actionTypeId in actionTypeIdList:
            if actionTypeId:
                dialog = CActionCreateDialog(self)
                QtGui.qApp.setCounterController(CCounterController(self))
                QtGui.qApp.setJTR(self)
                try:
                    actionType = CActionTypeCache.getById(actionTypeId)
                    defaultStatus = actionType.defaultStatus
                    defaultExecPersonId = actionType.defaultExecPersonId
                    newRecord = tableAction.newRecord()

                    newRecord.setValue('createDatetime', toVariant(QDateTime.currentDateTime()))
                    newRecord.setValue('createPerson_id', toVariant(QtGui.qApp.userId))
                    newRecord.setValue('modifyDatetime', toVariant(QDateTime.currentDateTime()))
                    newRecord.setValue('modifyPerson_id', toVariant(QtGui.qApp.userId))
                    newRecord.setValue('actionType_id', toVariant(actionTypeId))
                    newRecord.setValue('status', toVariant(defaultStatus))
                    newRecord.setValue('begDate', toVariant(QDateTime.currentDateTime()))
                    newRecord.setValue('directionDate', toVariant(QDateTime.currentDateTime()))
                    newRecord.setValue('setPerson_id', toVariant(QtGui.qApp.userId))
                    newRecord.setValue('id', toVariant(None))
                    newRecord.setValue('event_id', toVariant(eventId))
                    newRecord.setValue('person_id', toVariant(defaultExecPersonId))

                    newAction = CAction(record=newRecord)
                    newAction.updatePresetValuesConditions({'clientId': clientId, 'eventTypeId': eventTypeId})
                    newAction.initPresetValues()

                    if not newAction:
                        return

                    dialog.load(newAction.getRecord(), newAction, clientId)
                    dialog.chkIsUrgent.setEnabled(True)
                    dialog.setReduced(True)
                    if dialog.exec_() and dialog.checkDataEntered(secondTry=True):
                        action = dialog.getAction()
                        if action:
                            action.save(idx=0, checkModifyDate=False)
                finally:
                    QtGui.qApp.unsetJTR(self)
                    QtGui.qApp.delAllCounterValueIdReservation()
                    QtGui.qApp.setCounterController(None)
                    dialog.deleteLater()

        if hasattr(self, 'clientSex'):
            delattr(self, 'clientSex')
        if hasattr(self, 'clientBirthDate'):
            delattr(self, 'clientBirthDate')
        if hasattr(self, 'clientAge'):
            delattr(self, 'clientAge')


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelEvents_currentRowChanged(self, current, previous):
        eventId = self.eventId(current)
        self.updateEventInfo(eventId)


    @pyqtSignature('int')
    def on_modelEvents_itemsCountChanged(self, count):
        if count:
            labelText = u'в списке %d %s' % (count, agreeNumberAndWord(count, (u'обращение', u'обращения', u'обращений')))
            # if count <= 10000:
            clientCount = self.modelEvents.getClientCount()
            labelText += ', %d %s' % (clientCount, agreeNumberAndWord(clientCount, (u'пациент', u'пациента', u'пациентов')))
        else:
            labelText = u'список пуст'
        self.lblEventsCount.setText(labelText)
        self.eventCount = formatRecordsCount(count)
        # self.realCount(realCount)


    @pyqtSignature('QModelIndex')
    def on_tblEvents_doubleClicked(self, index):
        if QtGui.qApp.userHasRight(urRegTabWriteEvents):
            self.on_btnEventEdit_clicked()


    def editF090ActionToEventId(self, actionId):
        newActionId = None
        dialog = CF090EditDialog(self)
        try:
            dialog.load(actionId)
            dialog.protectWidgetFromEdit(False)
            dialog.exec_()
            if dialog.isBtnSave:
                # self.updateActionsList(self.__actionFilter, dialog.itemId())
                QtGui.qApp.emitCurrentClientInfoChanged()
                newActionId = dialog.itemId()
            else:
                # self.updateActionInfo(actionId)
                self.updateClientsListRequest = True
        finally:
            dialog.deleteLater()
        return newActionId


    def createF090ActionToEventId(self, eventId):
        newActionId = None
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        recordEvent = db.getRecordEx(tableEvent, '*', [tableEvent['id'].eq(eventId), tableEvent['deleted'].eq(0)])
        resultF090, eventF090Id, newActionId = createF090(self, recordEvent=recordEvent)
        if resultF090:
            # self.updateActionsList(self.__actionFilter, newActionId)
            QtGui.qApp.emitCurrentClientInfoChanged()
        else:
            self.updateClientsListRequest = True
        return newActionId


    @pyqtSignature('')
    def on_btnEventEdit_clicked(self):
        eventId = self.currentEventId()
        if eventId:
            actionF111 = self.getEventTypeIdF111(eventId)
            if actionF111:
                dialog = CF111EditDialog(self)
                try:
                    dialog.load(actionF111)
                    if dialog.exec_():
                        pass
                finally:
                    dialog.deleteLater()
            elif self.getEventTypeIdF090(eventId):
                actionId = self.getF090ActionIdToEventId(eventId)
                if actionId and canChangePayStatusAdditional(self, 'Action', actionId) and canEditOtherpeopleAction(self, actionId):
                    if forceBool(self.getF090ActionTypeId(actionId)):
                        self.editF090ActionToEventId(actionId)
                    else:
                        self.createF090ActionToEventId(eventId)
            else:
                editEvent(self, eventId)
        else:
            eventId = self.requestNewEvent()
        if eventId:
            self.updateEventListAfterEdit(eventId)
        self.focusEvents()


    def getEventTypeIdF090(self, eventId):
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        queryTable = tableEventType.innerJoin(tableEvent, tableEvent['eventType_id'].eq(tableEventType['id']))
        cond = [tableEvent['id'].eq(eventId),
                tableEvent['deleted'].eq(0),
                tableEventType['deleted'].eq(0),
                tableEventType['form'].eq(u'090')
                ]
        record = db.getRecordEx(queryTable, [tableEvent['eventType_id'].alias('eventTypeId')], cond)
        return forceRef(record.value('eventTypeId')) if record else None

    
    def getEventTypeIdF111(self, eventId):
        actionId = None
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        queryTable = tableEvent.innerJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
        cond = [tableEventType['code'].like(u'KBiR%'),
                tableEvent['id'].eq(eventId),
                tableEvent['deleted'].eq(0),
                tableEventType['deleted'].eq(0),
                ]
        recordEvent = db.getRecordEx(queryTable, [tableEvent['id']], cond, u'Event.id DESC')
        eventId = forceRef(recordEvent.value('id')) if recordEvent else None
        if eventId:
            actionTypeIdListByKBiR = getActionTypeIdListByFlatCode(u'111/y-20')
            if actionTypeIdListByKBiR:
                tableAction = db.table('Action')
                cond = [tableAction['event_id'].eq(eventId),
                        tableAction['deleted'].eq(0),
                        tableAction['actionType_id'].inlist(actionTypeIdListByKBiR)
                        ]
                record = db.getRecordEx(tableAction, [tableAction['id']], cond, u'Action.begDate')
                actionId = forceRef(record.value('id')) if record else None
        return actionId

    def getF090ActionIdToEventId(self, eventId):
        if eventId:
            db = QtGui.qApp.db
            tableAction = db.table('Action')
            tableActionType = db.table('ActionType')
            queryTable = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
            cond = [tableAction['event_id'].eq(eventId),
                    tableAction['deleted'].eq(0),
                    tableActionType['deleted'].eq(0),
                    tableActionType['flatCode'].like(u'%medical_examination'),
                    ]
            record = db.getRecordEx(queryTable, [tableAction['id'].alias('actionId')], cond)
            return forceRef(record.value('actionId')) if record else None
        return None
    

    def on_btnEventEditTemplate_clicked(self, eventId):
        if eventId:
            eventId = editEvent(self, eventId)
        else:
            eventId = self.requestNewEvent()
        if eventId:
            self.updateEventListAfterEdit(eventId)
        self.focusEvents()


    @pyqtSignature('')
    def on_btnEventNew_clicked(self):
        eventId = self.requestNewEvent()
        if eventId:
            self.updateEventListAfterEdit(eventId)
        self.focusEvents()


    @pyqtSignature('')
    def on_actEventPrint_triggered(self):
        self.tblEvents.setReportHeader(u'Список обращений')
        self.tblEvents.setReportDescription(self.getEventFilterAsText())
#        if self.cmbFilterEventByClient.currentIndex() == 0:
#            mask = [False]*3 + [True]*(self.modelEvents.columnCount()-3)
#        else:
#            mask = [True]*(self.modelEvents.columnCount())
#        self.tblEvents.printContent(mask)
        pageFormat = CPageFormat(pageSize=CPageFormat.A4, orientation=CPageFormat.Landscape, leftMargin=1, topMargin=1, rightMargin=1,  bottomMargin=1)
        self.tblEvents.printContent(pageFormat = pageFormat)
        self.focusEvents()



    @pyqtSignature('')
    def on_actVisitPrint_triggered(self):
        self.tblVisits.setReportHeader(u'Список визитов')
        self.tblVisits.setReportDescription(self.getVisitFilterAsText())
        self.tblVisits.printContent()
        self.focusEvents()


    def getVisitFilterAsText(self):
        db = QtGui.qApp.db
        filter  = self.__visitFilter
        resList = []

        visitsFilterType = filter['visitsFilterType']
        if visitsFilterType in (0, 1):
            clientIds = filter.get('clientIds', None)
            if clientIds and len(clientIds) == 1:
                resList.append((u'пациент', getClientMiniInfo(clientIds[0])))
            elif clientIds and len(clientIds) > 1:
                resList.append((u'список пациентов', u'из вкладки'))
        elif visitsFilterType in (2, 3):
            clientIds = self.__eventFilter.get('clientIds', None)
            if clientIds and len(clientIds) == 1:
                resList.append((u'пациент', getClientMiniInfo(clientIds[0])))
            elif clientIds and len(clientIds) > 1:
                resList.append((u'список пациентов', u'по списку осмотров'))
        else:
            resList.append((u'список пациентов', u'полный'))

        tmpList = [
            ('begSetDate', u'Дата назначения с', forceString),
            ('endSetDate', u'Дата назначения по', forceString),
            ('visitTypeId', u'Тип визита',
                lambda id: forceString(db.translate('rbVisitType', 'id', id, 'name'))),
            ('setSpecialityId', u'Специальность назначившего',
                lambda id: forceString(db.translate('rbSpeciality', 'id', id, 'name'))),
            ('personId', u'Назначил',
                lambda id: forceString(db.translate('vrbPersonWithSpeciality', 'id', id, 'name'))),
            ('isPrimary',   u'Признак первичности', lambda dummy: u'+'),
            ('begPlannedEndDate', u'Плановая дата выполнения с', forceString),
            ('endPlannedEndDate', u'Плановая дата окончания по', forceString),
            ('begExecDateTime', u'Дата и время выполнения с', forceString),
            ('endExecDateTime', u'Дата и время выполнения по', forceString),
            ]
        for (x, y, z) in tmpList:
            convertFilterToTextItem(resList, filter, x, y, z)
        return '\n'.join([ ': '.join(item) for item in resList])


    @pyqtSignature('')
    def on_actReportClientServices_triggered(self):
        dialog = CReportClientServices(self, self.selectedClientId(), self.modelEvents.idList())
        dialog.exec_()


    def getEventInfo(self, context):
        eventId = self.currentEventId()
        return context.getInstance(CEmergencyTeethEventInfo, eventId)


    @pyqtSignature('int')
    def on_btnEventPrint_printByTemplate(self, templateId):
        data = self.getEventContextData(self)
        clientId = self.selectedClientId()
        data['clientId'] = clientId
        QtGui.qApp.call(self, applyTemplate, (self, templateId, data))


    def getEventContextData(self, editor):
        from Events.TempInvalidInfo import CTempInvalidInfo
        context = CInfoContext()
        eventInfoList = context.getInstance(CEmergencyEventInfoList, tuple(self.tblEvents.model().idList()))
        eventInfo = editor.getEventInfo(context)
        eventInfo._actions = eventInfo.actions
        if len(eventInfoList)>0:
            eventInfo.initActions()


        if hasattr(editor, 'getTempInvalidInfo'):
            tempInvalidInfo = editor.getTempInvalidInfo(context)
        else:
            tempInvalidInfo = context.getInstance(CTempInvalidInfo, None)
        eventType = context.getInstance(CEventTypeInfo, forceRef(self.cmbFilterEventType.value()))  if self.chkFilterEventType.isChecked() else None
        eventBegSetDate = CDateInfo(self.edtFilterEventBegSetDate.date()) if self.chkFilterEventSetDate.isChecked() else None
        eventEndSetDate = CDateInfo(self.edtFilterEventEndSetDate.date()) if self.chkFilterEventSetDate.isChecked() else None
        eventBegSetTime = CTimeInfo(self.edtFilterEventBegSetTime.time()) if self.chkFilterEventSetDate.isChecked() else None
        eventEndSetTime = CTimeInfo(self.edtFilterEventEndSetTime.time()) if self.chkFilterEventSetDate.isChecked() else None
        eventBegExecDate = CDateInfo(self.edtFilterEventBegExecDate.date()) if self.chkFilterEventExecDate.isChecked() else None
        eventEndExecDate = CDateInfo(self.edtFilterEventEndExecDate.date()) if self.chkFilterEventExecDate.isChecked() else None
        eventBegExecTime = CTimeInfo(self.edtFilterEventBegExecTime.time()) if self.chkFilterEventExecDate.isChecked() else None
        eventEndExecTime = CTimeInfo(self.edtFilterEventEndExecTime.time()) if self.chkFilterEventExecDate.isChecked() else None
        eventEmptyExecDate = self.chkFilterEventEmptyExecDate.isChecked()
        eventOrgStructure = context.getInstance(COrgStructureInfo, forceRef(self.cmbFilterEventOrgStructure.value())) if self.chkFilterEventOrgStructure.isChecked() else None
        eventSpeciality = context.getInstance(CSpecialityInfo, forceRef(self.cmbFilterEventSpeciality.value())) if self.chkFilterEventSpeciality.isChecked() else None
        eventPerson = context.getInstance(CPersonInfo, forceRef(self.cmbFilterEventPerson.value())) if self.chkFilterEventPerson.isChecked() else None
        eventCSGCode = forceStringEx(self.edtFilterEventCSG.text()) if self.chkFilterEventCSG.isChecked() else u''
        eventCSGBegDate = CDateInfo(self.edtFilterEventCSGBegDate.date()) if self.chkFilterEventCSGDate.isChecked() else None
        eventCSGEndDate = CDateInfo(self.edtFilterEventCSGEndDate.date()) if self.chkFilterEventCSGDate.isChecked() else None
        eventCSGMKBFrom = MKBwithoutSubclassification(unicode(self.edtCSGMKBFrom.text())) if self.chkFilterEventCSGMKB.isChecked() else None
        eventCSGMKBTo = MKBwithoutSubclassification(unicode(self.edtCSGMKBTo.text())) if self.chkFilterEventCSGMKB.isChecked() else None
        eventPayStatusCodeCSG = None
        eventPayStatusFinanceCodeCSG = None
        if self.chkFilterCSGPayStatus.isChecked():
            eventPayStatusCodeCSG = self.cmpFilterCSGPayStatusCode.currentIndex()
            index = self.cmbFilterCSGPayStatusFinance.currentIndex()
            if not 0 <= index < 5:
                index = 0
            eventPayStatusFinanceCodeCSG = 5 - index
        filter = {'eventType': eventType if eventType else None,
                    'eventBegSetDate' : eventBegSetDate,
                    'eventBegSetTime' : eventBegSetTime,
                    'eventEndSetDate' : eventEndSetDate,
                    'eventEndSetTime' : eventEndSetTime,
                    'eventBegExecDate' : eventBegExecDate,
                    'eventBegExecTime' : eventBegExecTime,
                    'eventEndExecDate' : eventEndExecDate,
                    'eventEndExecTime' : eventEndExecTime,
                    'eventOrgStructure' : eventOrgStructure if eventOrgStructure else None,
                    'eventSpeciality' : eventSpeciality if eventSpeciality else None,
                    'eventPerson' : eventPerson if eventPerson else None,
                    'eventCSGCode'    : eventCSGCode,
                    'eventCSGBegDate' : eventCSGBegDate,
                    'eventCSGEndDate' : eventCSGEndDate,
                    'eventCSGMKBFrom' : eventCSGMKBFrom,
                    'eventCSGMKBTo'   : eventCSGMKBTo,
                    'eventPayStatusCodeCSG' : eventPayStatusCodeCSG,
                    'eventPayStatusFinanceCodeCSG' : eventPayStatusFinanceCodeCSG,
                    'eventEmptyExecDate' :  eventEmptyExecDate
        }
        data = { 'event' : eventInfo,
                 'eventList' : eventInfoList,
                 'client': eventInfo.client,
                 'tempInvalid': tempInvalidInfo,
                 'filter' : filter
                }
        return data


    @pyqtSignature('')
    def on_btnEventFilter_clicked(self):
        for s in self.chkListOnEventsPage:
            chk = s[0]
            if chk.isChecked():
                self.activateFilterWdgets(s[1])
                return
        self.chkFilterEventType.setChecked(True)


    def onCheckEventToggled(self, checked):
        if checked:
            self.chkFilterEventId.setChecked(False)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterEventSetDate_toggled(self, checked):
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventSetDate, checked)
        self.onCheckEventToggled(checked)


    @pyqtSignature('bool')
    def on_chkFilterEventNextDate_toggled(self, checked):
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventNextDate, checked)
        self.onCheckEventToggled(checked)


    @pyqtSignature('bool')
    def on_chkFilterEventEmptyExecDate_toggled(self, checked):
        if checked:
            self.chkFilterEventId.setChecked(False)
            self.chkFilterEventExecDate.setChecked(False)


    @pyqtSignature('bool')
    def on_chkFilterEventExecDate_toggled(self, checked):
        if checked:
            self.chkFilterEventId.setChecked(False)
            self.chkFilterEventEmptyExecDate.setChecked(False)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventExecDate, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterEventPurpose_toggled(self, checked):
        if checked:
            if not self.cmbFilterEventPurpose.hasTable():
                self.cmbFilterEventPurpose.setTable('rbEventTypePurpose', False, filter='code != \'0\'')
            self.chkFilterEventId.setChecked(False)
            self.updateFilterEventResultTable()
            self.setCmbFilterEventTypeFilter(self.cmbFilterEventPurpose.value())
        else:
            self.setCmbFilterEventTypeFilter(None)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('int')
    def on_cmbFilterEventPurpose_currentIndexChanged(self, index):
        self.setCmbFilterEventTypeFilter(self.cmbFilterEventPurpose.value())
        self.updateFilterEventResultTable()


    @pyqtSignature('bool')
    def on_chkFilterEventType_toggled(self, checked):
        if checked:
            self.chkFilterEventId.setChecked(False)
        self.onChkFilterToggled(self.sender(), checked)
        if checked:
            self.updateFilterEventResultTable()


    @pyqtSignature('int')
    def on_cmbFilterEventType_currentIndexChanged(self, index):
        self.updateFilterEventResultTable()


    @pyqtSignature('bool')
    def on_chkFilterEventSpeciality_toggled(self, checked):
        if checked:
            self.chkFilterEventId.setChecked(False)
            if not self.cmbFilterEventSpeciality.hasTable():
                self.cmbFilterEventSpeciality.setTable('rbSpeciality', False)
        self.onChkFilterToggled(self.sender(), checked)
        if checked:
            self.cmbFilterEventPerson.setSpecialityId(self.cmbFilterEventSpeciality.value())
        else:
            self.cmbFilterEventPerson.setSpecialityId(None)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventSpeciality, checked)


    @pyqtSignature('bool')
    def on_chkFilterEventOrgStructure_toggled(self, checked):
        if checked:
            self.chkFilterEventId.setChecked(False)
        self.onChkFilterToggled(self.sender(), checked)
        if checked:
            self.cmbFilterEventPerson.setOrgStructureId(self.cmbFilterEventOrgStructure.value())
        else:
            self.cmbFilterEventPerson.setOrgStructureId(None)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventOrgStructure, checked)


    @pyqtSignature('int')
    def on_cmbFilterEventSpeciality_currentIndexChanged(self, index):
        self.cmbFilterEventPerson.setSpecialityId(self.cmbFilterEventSpeciality.value())


    @pyqtSignature('bool')
    def on_chkFilterEventPerson_toggled(self, checked):
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventPerson, checked)
        self.onCheckEventToggled(checked)


    @pyqtSignature('bool')
    def on_chkFilterEventDispanser_toggled(self, checked):
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventDispanser, checked)
        self.onCheckEventToggled(checked)


    @pyqtSignature('bool')
    def on_chkFilterEventIsPrimary_toggled(self, checked):
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventIsPrimary, checked)
        self.onCheckEventToggled(checked)


    @pyqtSignature('bool')
    def on_chkFilterEventOrder_toggled(self, checked):
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventOrder, checked)
        self.onCheckEventToggled(checked)


    @pyqtSignature('bool')
    def on_chkRelegateOrg_toggled(self, checked):
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkRelegateOrg, checked)
        self.onCheckEventToggled(checked)




    @pyqtSignature('bool')
    def on_chkFilterEventLPU_toggled(self, checked):
        if checked:
            self.chkFilterEventId.setChecked(False)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventLPU, checked)
        self.onChkFilterToggled(self.sender(), checked)
        if checked:
            db = QtGui.qApp.db
            orgId = forceRef(db.translate('Event', 'id', self.currentEventId(), 'org_id'))
            self.cmbFilterEventLPU.setValue(orgId)
            self.cmbFilterEventPerson.setOrgId(orgId)
            self.chkFilterEventNonBase.setChecked(False)
        else:
            self.cmbFilterEventLPU.setValue(None)
            self.cmbFilterEventPerson.setOrgId(None)



    @pyqtSignature('int')
    def on_cmbFilterEventLPU_currentIndexChanged(self, index):
        self.cmbFilterEventPerson.setOrgId(self.cmbFilterEventLPU.value())


    @pyqtSignature('bool')
    def on_chkFilterEventNonBase_toggled(self, checked):
        if checked:
            self.chkFilterEventId.setChecked(False)
            self.chkFilterEventLPU.setChecked(False)


    @pyqtSignature('bool')
    def on_chkFilterEventMes_toggled(self, checked):
        self.onCheckEventToggled(checked)


    @pyqtSignature('bool')
    def on_chkFilterEventCSG_toggled(self, checked):
        self.onCheckEventToggled(checked)


    @pyqtSignature('bool')
    def on_chkFilterEventCSGDate_toggled(self, checked):
        self.onCheckEventToggled(checked)


    @pyqtSignature('bool')
    def on_chkFilterEventCSGMKB_toggled(self, checked):
        self.onCheckEventToggled(checked)


    @pyqtSignature('bool')
    def on_chkFilterCSGPayStatus_toggled(self, checked):
        self.onCheckEventToggled(checked)


    @pyqtSignature('bool')
    def on_chkMKB_toggled(self, checked):
        self.onCheckEventToggled(checked)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkMKB, checked)


    @pyqtSignature('bool')
    def on_chkFilterActionMKB_toggled(self, checked):
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionMKB, checked)
        if checked:
            self.chkFilterActionId.setChecked(False)
            self.edtFilterActionId.setEnabled(False)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterEventResult_toggled(self, checked):
        if checked:
            self.chkFilterEventId.setChecked(False)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventResult, checked)
        self.onChkFilterToggled(self.sender(), checked)
        if checked:
            self.updateFilterEventResultTable()
            
    
    @pyqtSignature('bool')
    def on_chkFilterEventDisease_toggled(self, checked):
        if checked:
            self.chkFilterEventId.setChecked(False)
            if not self.cmbFilterEventDisease.hasTable():
                self.cmbFilterEventDisease.setTable('rbDiseaseCharacter', False)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventDisease, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterEventCreatePerson_toggled(self, checked):
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventCreatePerson, checked)
        self.onCheckEventToggled(checked)


    @pyqtSignature('bool')
    def on_chkFilterEventCreateDate_toggled(self, checked):
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventCreateDate, checked)
        self.onCheckEventToggled(checked)


    @pyqtSignature('bool')
    def on_chkFilterEventModifyPerson_toggled(self, checked):
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventModifyPerson, checked)
        self.onCheckEventToggled(checked)


    @pyqtSignature('bool')
    def on_chkFilterEventModifyDate_toggled(self, checked):
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventModifyDate, checked)
        self.onCheckEventToggled(checked)


    @pyqtSignature('bool')
    def on_chkFilterEventPayStatus_toggled(self, checked):
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventPayStatus, checked)
        self.onCheckEventToggled(checked)


    @pyqtSignature('bool')
    def on_chkFilterVisitPayStatus_toggled(self, checked):
        self.onCheckEventToggled(checked)

    @pyqtSignature('bool')
    def on_chkFilterPayStatus_toggled(self, checked):
        self.onCheckEventToggled(checked)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterPayStatus, checked)
        for row in self.chkListOnEventsPage:
            if row[0] == self.chkFilterPayStatus:
                for element in row[1]:
                    self.setChildElementsVisible(self.chkListOnEventsPage, element, checked)


    @pyqtSignature('bool')
    def on_chkFilterEventActions_toggled(self, checked):
        self.onCheckEventToggled(checked)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventActions, checked)
        for row in self.chkListOnEventsPage:
            if row[0] == self.chkFilterEventActions:
                for element in row[1]:
                    self.setChildElementsVisible(self.chkListOnEventsPage, element, checked)


    @pyqtSignature('bool')
    def on_chkErrorInDiagnostic_toggled(self, checked):
        if checked:
            self.chkFilterEventId.setChecked(False)


    @pyqtSignature('bool')
    def on_chkFilterJobTicketId_toggled(self, checked):
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterJobTicketId, checked)
        self.onCheckEventToggled(checked)


    @pyqtSignature('bool')
    def on_chkFilterVisits_toggled(self, checked):
        self.onCheckEventToggled(checked)
        if checked:
            if not self.cmbFilterVisitScene.hasTable():
                self.cmbFilterVisitScene.setTable('rbScene', True)
            if not self.cmbFilterVisitType.hasTable():
                self.cmbFilterVisitType.setTable('rbVisitType', True)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterVisits, checked)


    @pyqtSignature('bool')
    def on_chkFilterEventPayer_toggled(self, checked):
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventPayer, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('')
    def on_btnFilterEventSelectPayer_clicked(self):
        orgId = selectOrganisation(self, self.cmbFilterEventPayer.value(), False)
        self.cmbFilterEventPayer.updateModel()
        if orgId:
            self.cmbFilterEventPayer.setValue(orgId)


    @pyqtSignature('bool')
    def on_chkFilterEventContract_toggled(self, checked):
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventContract, checked)
        self.onCheckEventToggled(checked)
        if checked and self.chkFilterEventFinance.isChecked():
            self.chkFilterEventFinance.setChecked(not checked)


    @pyqtSignature('bool')
    def on_chkFilterEventFinance_toggled(self, checked):
        self.onCheckEventToggled(checked)
        if checked and self.chkFilterEventContract.isChecked():
            self.chkFilterEventContract.setChecked(not checked)
        if checked and not self.edtFilterEventFinance.hasTable():
            self.edtFilterEventFinance.setTable('rbFinance', True)


    @pyqtSignature('bool')
    def on_chkFilterEventExpertId_toggled(self, checked):
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventExpertId, checked)
        self.onCheckEventToggled(checked)


    @pyqtSignature('bool')
    def on_chkFilterEventExpertiseDate_toggled(self, checked):
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventExpertiseDate, checked)
        self.onCheckEventToggled(checked)


    @pyqtSignature('bool')
    def on_chkFilterEventExport_toggled(self, checked):
        if checked and not self.cmbFilterEventExportSystem.hasTable():
            self.cmbFilterEventExportSystem.setTable('rbExternalSystem', True)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventExport, checked)
        self.onCheckEventToggled(checked)


    @pyqtSignature('bool')
    def on_chkFilterEventInAccountItems_toggled(self, checked):
        self.onCheckEventToggled(checked)


    @pyqtSignature('')
    def on_btnFilterEventContract_clicked(self):
        currentDate = QDate.currentDate()
        self.filterEventContractParams = {}
        self.filterEventContractParams['financeId'] = forceRef(QtGui.qApp.preferences.appPrefs.get('Registry_filterEventContractParams_financeId', None))
        self.filterEventContractParams['groupingIndex'] = forceInt(QtGui.qApp.preferences.appPrefs.get('Registry_filterEventContractParams_groupingIndex', 0))
        self.filterEventContractParams['grouping'] = forceString(QtGui.qApp.preferences.appPrefs.get('Registry_filterEventContractParams_grouping', u''))
        self.filterEventContractParams['resolutionIndex'] = forceInt(QtGui.qApp.preferences.appPrefs.get('Registry_filterEventContractParams_resolutionIndex', 0))
        self.filterEventContractParams['resolution'] = forceString(QtGui.qApp.preferences.appPrefs.get('Registry_filterEventContractParams_resolution', u''))
        self.filterEventContractParams['priceList'] = forceInt(QtGui.qApp.preferences.appPrefs.get('Registry_filterEventContractParams_priceList', 0))
        self.filterEventContractParams['edtBegDate'] = forceDate(QtGui.qApp.preferences.appPrefs.get('Registry_filterEventContractParams_edtBegDate',QDate(currentDate.year(), 1, 1)))
        self.filterEventContractParams['edtEndDate'] = forceDate(QtGui.qApp.preferences.appPrefs.get('Registry_filterEventContractParams_edtEndDate', QDate(currentDate.year(), 12, 31)))
        self.filterEventContractParams['enableInAccounts'] = forceInt(QtGui.qApp.preferences.appPrefs.get('Registry_filterEventContractParams_enableInAccounts', 0))
        (contractId, contractDescr, filterEventContractParams)= selectContract(self, self.__filterEventContractId, self.filterEventContractParams)
        self.__filterEventContractId = contractId
        self.filterEventContractParams = filterEventContractParams
        self.edtFilterEventContract.setText(contractDescr)
        QtGui.qApp.preferences.appPrefs['Registry_filterEventContractParams_financeId'] = toVariant(self.filterEventContractParams.get('financeId', None))
        QtGui.qApp.preferences.appPrefs['Registry_filterEventContractParams_groupingIndex'] = toVariant(self.filterEventContractParams.get('groupingIndex', 0))
        QtGui.qApp.preferences.appPrefs['Registry_filterEventContractParams_grouping'] = toVariant(self.filterEventContractParams.get('grouping', u''))
        QtGui.qApp.preferences.appPrefs['Registry_filterEventContractParams_resolutionIndex'] = toVariant(self.filterEventContractParams.get('resolutionIndex', 0))
        QtGui.qApp.preferences.appPrefs['Registry_filterEventContractParams_resolution'] = toVariant(self.filterEventContractParams.get('resolution', u''))
        QtGui.qApp.preferences.appPrefs['Registry_filterEventContractParams_priceList'] = toVariant(self.filterEventContractParams.get('priceList', 0))
        QtGui.qApp.preferences.appPrefs['Registry_filterEventContractParams_edtBegDate'] = toVariant(self.filterEventContractParams.get('edtBegDate', QDate(currentDate.year(), 1, 1)))
        QtGui.qApp.preferences.appPrefs['Registry_filterEventContractParams_edtEndDate'] = toVariant(self.filterEventContractParams.get('edtEndDate', QDate(currentDate.year(), 12, 31)))
        QtGui.qApp.preferences.appPrefs['Registry_filterEventContractParams_enableInAccounts'] = toVariant(self.filterEventContractParams.get('enableInAccounts', 0))


    @pyqtSignature('')
    def on_actEventIdBarcodeScan_triggered(self):
        self.on_buttonBoxEvent_reset()
        self.tabEventFilter.setCurrentWidget(self.tabEventFindEx)
        self.chkFilterEventId.setFocus(Qt.OtherFocusReason)
        self.chkFilterEventId.setChecked(True)


    @pyqtSignature('')
    def on_actEventJobTicketIdBarcodeScan_triggered(self):
        self.on_buttonBoxEvent_reset()
        self.tabEventFilter.setCurrentWidget(self.tabEventFindEx)
        self.chkFilterJobTicketId.setFocus(Qt.OtherFocusReason)
        self.chkFilterJobTicketId.setChecked(True)


    @pyqtSignature('')
    def on_actEventExternalIdBarcodeScan_triggered(self):
        self.on_buttonBoxEvent_reset()
        self.tabEventFilter.setCurrentWidget(self.tabEventFindEx)
        self.chkFilterExternalId.setFocus(Qt.OtherFocusReason)
        self.chkFilterExternalId.setChecked(True)
        if not QtGui.qApp.getOpeningSnilsCardindex():
            self.cmbFilterEventByClient.setCurrentIndex(2)


    @pyqtSignature('bool')
    def on_chkFilterEventId_toggled(self, checked):
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterEventId, checked)
        self.onChkFilterToggled(self.sender(), checked)
        if checked:
            for chk in (self.chkFilterEventCreatePerson,
                        self.chkFilterEventCreateDate,
                        self.chkFilterEventModifyPerson,
                        self.chkFilterEventModifyDate,
                        self.chkErrorInDiagnostic,
                        self.chkFilterEventInAccountItems,
                        self.chkFilterEventPayStatus,
                        self.chkFilterVisitPayStatus,
                        self.chkFilterEventSetDate,
                        self.chkFilterEventEmptyExecDate,
                        self.chkFilterEventExecDate,
                        self.chkFilterEventNextDate,
                        self.chkFilterEventOrgStructure,
                        self.chkFilterEventSpeciality,
                        self.chkFilterEventPerson,
                        self.chkFilterEventDispanser,
                        self.chkRelegateOrg,
                        self.chkFilterEventLPU,
                        self.chkFilterEventNonBase,
                        self.chkFilterEventMes,
                        self.chkFilterEventCSG,
                        self.chkFilterEventCSGDate,
                        self.chkFilterEventCSGMKB,
                        self.chkFilterCSGPayStatus,
                        self.chkMKB,
                        self.chkFilterEventResult,
                        self.chkFilterEventDisease,
                        self.chkFilterExternalId,
                        self.chkFilterAccountSumLimit,
                        self.chkFilterVisits,
                        self.chkFilterEventPayer,
                        self.chkFilterEventFinance,
                        self.chkFilterEventContract,
                        self.chkFilterEventExpertId,
                        self.chkFilterEventExpertiseDate,
                        self.chkFilterEventExport,
                        self.chkFilterJobTicketId):
                chk.setChecked(False)
            if not QtGui.qApp.getOpeningSnilsCardindex():
                self.cmbFilterEventByClient.setCurrentIndex(2)


    @pyqtSignature('bool')
    def on_chkFilterExternalId_toggled(self, checked):
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterExternalId, checked)
        self.onCheckEventToggled(checked)


    @pyqtSignature('bool')
    def on_chkFilterAccountSumLimit_toggled(self, checked):
        if checked:
            self.chkFilterEventId.setChecked(False)
        self.setChildElementsVisible(self.chkListOnEventsPage, self.chkFilterAccountSumLimit, checked)
        self.onChkFilterToggled(self.sender(), checked)
        if self.cmbFilterAccountSumLimit.currentIndex() == 0:
            self.edtFilterSumLimitDelta.setValue(0)
            self.edtFilterSumLimitDelta.setEnabled(False)


    @pyqtSignature('int')
    def on_cmbFilterAccountSumLimit_currentIndexChanged(self, index):
        if index == 0:
            self.edtFilterSumLimitDelta.setValue(0)
            self.edtFilterSumLimitDelta.setEnabled(False)
        else:
            self.edtFilterSumLimitDelta.setEnabled(True)


    @pyqtSignature('QAbstractButton*')
    def on_buttonBoxEvent_clicked(self, button):
        buttonCode = self.buttonBoxEvent.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.on_buttonBoxEvent_apply()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_buttonBoxEvent_reset()


#    @pyqtSignature('')
    def on_buttonBoxEvent_reset(self):
        for s in self.chkListOnEventsPage:
            chk = s[0]
            if chk.isChecked():
                self.deactivateFilterWdgets(s[1])
                chk.setChecked(False)
        self.tblEvents.setOrder(None)
        self.cmbFilterEventByClient.setCurrentIndex(0)


#    @pyqtSignature('')
    def on_buttonBoxEvent_apply(self):
        filter = {}
        if self.chkFilterEventSetDate.isChecked():
            filter['begSetDateTime'] = QDateTime(self.edtFilterEventBegSetDate.date(),  self.edtFilterEventBegSetTime.time())
            filter['endSetDateTime'] = QDateTime(self.edtFilterEventEndSetDate.date(),  self.edtFilterEventEndSetTime.time())
        filter['emptyExecDate'] = self.chkFilterEventEmptyExecDate.isChecked()
        if self.chkFilterEventExecDate.isChecked():
            filter['begExecDateTime'] = QDateTime(self.edtFilterEventBegExecDate.date(), self.edtFilterEventBegExecTime.time())
            filter['endExecDateTime'] = QDateTime(self.edtFilterEventEndExecDate.date(), self.edtFilterEventEndExecTime.time())
        if self.chkFilterEventNextDate.isChecked():
            filter['begNextDate'] = self.edtFilterEventBegNextDate.date()
            filter['endNextDate'] = self.edtFilterEventEndNextDate.date()
        if self.chkFilterEventPurpose.isChecked():
            filter['eventPurposeId'] = self.cmbFilterEventPurpose.value()
        if self.chkFilterEventIsPrimary.isChecked():
            filter['isPrimary'] = self.cmbFilterEventIsPrimary.currentIndex() + 1
        if self.chkFilterEventOrder.isChecked():
            filter['order'] = self.cmbFilterEventOrder.currentIndex()+1
        if self.chkFilterEventType.isChecked():
            if self.cmbFilterEventType.value():
                filter['eventTypeId'] = self.cmbFilterEventType.value()
        if self.chkFilterEventOrgStructure.isChecked():
            filter['orgStructureId'] = self.cmbFilterEventOrgStructure.value()
        if self.chkFilterEventSpeciality.isChecked():
            filter['specialityId'] = self.cmbFilterEventSpeciality.value()
        if self.chkFilterEventPerson.isChecked():
            filter['personId'] = self.cmbFilterEventPerson.value()
        if self.chkFilterEventDispanser.isChecked():
            if self.cmbFilterEventDispanser.value():
                filter['dispanserId'] = self.cmbFilterEventDispanser.value()
        if self.chkRelegateOrg.isChecked():
            filter['relegateOrgId'] = self.cmbRelegateOrg.value()
        if self.chkEverythingExcept.isChecked():
            filter['everythingExcept'] = self.chkEverythingExcept.isChecked()
        if self.chkFilterEventLPU.isChecked():
            filter['LPUId'] = self.cmbFilterEventLPU.value()
        else:
            filter['nonBase'] = self.chkFilterEventNonBase.isChecked()
        filter['errorInDiagnostic'] = self.chkErrorInDiagnostic.isChecked()
        if self.chkFilterEventMes.isChecked():
            filter['mesCode'] = forceStringEx(self.edtFilterEventMes.text())
        if self.chkFilterEventCSG.isChecked():
            filter['csgCode'] = forceStringEx(self.edtFilterEventCSG.text())
        if self.chkFilterEventCSGDate.isChecked():
            filter['csgBegDate'] = self.edtFilterEventCSGBegDate.date()
            filter['csgEndDate'] = self.edtFilterEventCSGEndDate.date()
        if self.chkFilterEventCSGMKB.isChecked():
            filter['csgMKBFrom'] = MKBwithoutSubclassification(unicode(self.edtCSGMKBFrom.text()))
            filter['csgMKBTo'] = MKBwithoutSubclassification(unicode(self.edtCSGMKBTo.text()))
        if self.chkFilterCSGPayStatus.isChecked():
            filter['payStatusCodeCSG'] = self.cmpFilterCSGPayStatusCode.currentIndex()
            index = self.cmbFilterCSGPayStatusFinance.currentIndex()
            if not 0 <= index < 5:
                index = 0
            filter['payStatusFinanceCodeCSG'] = 5 - index
        if self.chkMKB.isChecked():
            filter['MKBFrom'] = MKBwithoutSubclassification(unicode(self.edtMKBFrom.text()))
            filter['MKBTo']   = MKBwithoutSubclassification(unicode(self.edtMKBTo.text()))
            filter['MKBisPreliminary'] = self.chkPreliminary.isChecked()
            filter['MKBisConcomitant'] = self.chkConcomitant.isChecked()
        if self.chkFilterEventResult.isChecked():
            filter['eventResultId'] = self.cmbFilterEventResult.value()
        if self.chkFilterEventDisease.isChecked():
            filter['diseaseCharacter'] = self.cmbFilterEventDisease.value()
#        if self.chkFilterEventTempInvalid.isChecked():
#            filter['begTempInvalidDate'] = self.edtFilterEventBegTempInvalid.date()
#            filter['endTempInvalidDate'] = self.edtFilterEventEndTempInvalid.date()
        if self.chkFilterEventCreatePerson.isChecked():
            filter['createPersonId'] = self.cmbFilterEventCreatePerson.value()
        if self.chkFilterEventCreateDate.isChecked():
            filter['begCreateDate'] = self.edtFilterEventBegCreateDate.date()
            filter['endCreateDate'] = self.edtFilterEventEndCreateDate.date()
        if self.chkFilterEventModifyPerson.isChecked():
            filter['modifyPersonId'] = self.cmbFilterEventModifyPerson.value()
        if self.chkFilterEventModifyDate.isChecked():
            filter['begModifyDate'] = self.edtFilterEventBegModifyDate.date()
            filter['endModifyDate'] = self.edtFilterEventEndModifyDate.date()
        if self.chkFilterEventInAccountItems.isChecked():
            filter['eventInAccountItems'] = self.cmbFilterEventInAccountItems.currentIndex()
        if self.chkFilterEventPayStatus.isChecked():
            filter['payStatusCode'] = self.cmpFilterEventPayStatusCode.currentIndex()
            index = self.cmbFilterEventPayStatusFinance.currentIndex()
            if not 0<=index<5:
                index = 0
            filter['payStatusFinanceCode'] = 5-index
        if self.chkFilterVisitPayStatus.isChecked():
            filter['payStatusCodeVisit'] = self.cmpFilterVisitPayStatusCode.currentIndex()
            index = self.cmbFilterVisitPayStatusFinance.currentIndex()
            if not 0<=index<5:
                index = 0
            filter['payStatusFinanceCodeVisit'] = 5-index
        if self.chkFilterEventPayer.isChecked():
            filter['payerId'] = self.cmbFilterEventPayer.value()
        if self.chkFilterEventFinance.isChecked():
            filter['financeId'] = self.edtFilterEventFinance.value()
        if self.chkFilterEventContract.isChecked() and self.__filterEventContractId:
            filter['contractId'] = self.__filterEventContractId
        if self.chkFilterEventExpertId.isChecked():
            filter['eventExpertId'] = self.cmbFilterEventExpertId.value()
        if self.chkFilterEventExpertiseDate.isChecked():
           filter['begExpertiseDate'] = self.edtFilterEventBegExpertiseDate.date()
           filter['endExpertiseDate'] = self.edtFilterEventEndExpertiseDate.date()
        if self.chkFilterEventExport.isChecked():
           filter['eventExportStatus'] = self.cmbFilterEventExportStatus.currentIndex()
           filter['eventExportSystem'] = self.cmbFilterEventExportSystem.value()
        if self.chkFilterEventId.isChecked():
            tmp = forceStringEx(self.edtFilterEventId.text())
            if tmp:
                filter['id'] = int(tmp)
        if self.chkFilterJobTicketId.isChecked():
            tmp = forceStringEx(self.edtFilterJobTicketId.text())
            if tmp:
                filter['jobTicketId'] = int(tmp)
        if self.chkFilterExternalId.isChecked():
            tmpExternalId = forceStringEx(self.edtFilterExternalId.text())
            if tmpExternalId:
                filter['externalId'] = tmpExternalId
        if self.chkFilterAccountSumLimit.isChecked():
            filter['accountSumLimit'] = forceInt(self.cmbFilterAccountSumLimit.currentIndex())
            filter['sumLimitFrom'] = forceInt(self.edtFilterSumLimitFrom.value())
            filter['sumLimitTo'] = forceInt(self.edtFilterSumLimitTo.value())
            filter['sumLimitDelta'] = forceInt(self.edtFilterSumLimitDelta.value())
        filter['filterVisits'] = self.chkFilterVisits.isChecked()
        if self.chkFilterVisits.isChecked():
            filter['visitScene'] = self.cmbFilterVisitScene.value()
            filter['visitType'] = self.cmbFilterVisitType.value()
            filter['visitProfile'] = self.cmbFilterVisitProfile.value()
        filterEventByClient = self.cmbFilterEventByClient.currentIndex()
        if filterEventByClient == 0:
            filter['clientIds'] = [ self.selectedClientId() ]
        elif filterEventByClient == 1:
            filter['clientIds'] = self.modelClients.idList()
        filter['filterEventByClient'] = filterEventByClient
        filter['notExposedByOms'] = self.chkNotExposedByOms.isChecked()
        filter['notExposed'] = self.chkNotExposed.isChecked()
        if self.chkFilterEventActions.isChecked():
            filter['eventActions'] = self.cmbFilterEventActions.value()
        self.updateEventsList(filter)
        self.focusEvents()

#### AmbCard page #################################

    @pyqtSignature('')
    def on_actAmbCardEditClient_triggered(self):
        clientId = self.currentClientId()
        if clientId:
            self.editClient(clientId)
            self.updateAmbCardInfo()
            self.updateClientsListRequest = True


    @pyqtSignature('')
    def on_actAmbCardOpenClientVaccinationCard_triggered(self):
        clientId = self.currentClientId()
        if clientId:
            openClientVaccinationCard(self, clientId)


### Actions page ##################################

    @pyqtSignature('')
    def on_actActionEditClient_triggered(self):
        clientId = self.currentClientId()
        if clientId:
            self.editClient(clientId)
            self.updateActionInfo(None)
            self.updateClientsListRequest = True


    @pyqtSignature('')
    def on_actActionOpenClientVaccinationCard_triggered(self):
        clientId = self.currentClientId()
        if clientId:
            openClientVaccinationCard(self, clientId)


    @pyqtSignature('int')
    def on_tabWidgetActionsClasses_currentChanged(self, index):
        actionClass = self.getActionClassByTabIndex()
        if actionClass is not None:
            self.cmbFilterActionType.setClassesPopup([actionClass])
            self.cmbFilterActionType.setClass(actionClass)
            self.cmbFilterActionType.setValue(self.__actionTypeIdListByClassPage[actionClass])
            self.cmbFilterActionType.setClassesPopupVisible(False)
        else:
            self.cmbFilterActionType.setClassesPopup(range(4))
            self.cmbFilterActionType.setClass(None)
            self.cmbFilterActionType.setClassesPopupVisible(True)
        self.on_buttonBoxAction_apply()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelVisits_currentRowChanged(self, current, previous):
        visitId = self.tblVisits.currentItemId()
        self.updateVisitInfo(visitId)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelActionsStatus_currentRowChanged(self, current, previous):
        actionId = self.tblActionsStatus.currentItemId()
        self.updateActionInfo(actionId)
        self.tabAmbCardContent.updateAmbCardPropertiesTable(current, self.tblActionsStatusProperties, previous)
        self.tabAmbCardContent.updateAmbCardAttachedFiles(current, self.tblActionsStatusAttachedDocuments, previous)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelActionsDiagnostic_currentRowChanged(self, current, previous):
        actionId = self.tblActionsDiagnostic.currentItemId()
        self.updateActionInfo(actionId)
        self.tabAmbCardContent.updateAmbCardPropertiesTable(current, self.tblActionsDiagnosticProperties, previous)
        self.tabAmbCardContent.updateAmbCardAttachedFiles(current, self.tblActionsDiagnosticAttachedDocuments, previous)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelActionsCure_currentRowChanged(self, current, previous):
        actionId = self.tblActionsCure.currentItemId()
        self.updateActionInfo(actionId)
        self.tabAmbCardContent.updateAmbCardPropertiesTable(current, self.tblActionsCureProperties, previous)
        self.tabAmbCardContent.updateAmbCardAttachedFiles(current, self.tblActionsCureAttachedDocuments, previous)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelActionsMisc_currentRowChanged(self, current, previous):
        actionId = self.tblActionsMisc.currentItemId()
        self.updateActionInfo(actionId)
        self.tabAmbCardContent.updateAmbCardPropertiesTable(current, self.tblActionsMiscProperties, previous)
        self.tabAmbCardContent.updateAmbCardAttachedFiles(current, self.tblActionsMiscAttachedDocuments, previous)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelActionsAll_currentRowChanged(self, current, previous):
        actionId = self.tblActionsAll.currentItemId()
        self.updateActionInfo(actionId)
        self.tabAmbCardContent.updateAmbCardPropertiesTable(current, self.tblActionsAllProperties, previous)
        self.tabAmbCardContent.updateAmbCardAttachedFiles(current, self.tblActionsAllAttachedDocuments, previous)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelExpertDirectionsMC_currentRowChanged(self, current, previous):
        actionId = self.tblExpertDirectionsMC.currentItemId()
        self.updateMedicalCommissionInfo(actionId)
        self.tabAmbCardContent.updateAmbCardPropertiesTable(current, self.tblExpertDirectionsPropertiesMC, previous)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelExpertProtocolsMC_currentRowChanged(self, current, previous):
        actionId = self.tblExpertProtocolsMC.currentItemId()
        self.updateMedicalCommissionInfo(actionId)
        self.tabAmbCardContent.updateAmbCardPropertiesTable(current, self.tblExpertProtocolsPropertiesMC, previous)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelExpertMedicalSocialInspection_currentRowChanged(self, current, previous):
        actionId = self.tblExpertMedicalSocialInspection.currentItemId()
        self.updateMedicalCommissionInfo(actionId)
        self.tabAmbCardContent.updateAmbCardPropertiesTable(current, self.tblExpertMSIProperties, previous)

    def getClientId(self, event_id):
        stmt = "SELECT c.id FROM Event e LEFT JOIN Client c ON c.id = e.client_id WHERE e.id = {0};".format(event_id)
        query = QtGui.qApp.db.query(stmt)
        if query.next():
            record = query.record()
            return record.value(0).toInt()[0]

    def getClientId(self, event_id):
        stmt = "SELECT c.id FROM Event e LEFT JOIN Client c ON c.id = e.client_id WHERE e.id = {0};".format(event_id)
        query = QtGui.qApp.db.query(stmt)
        if query.next():
            record = query.record()
            return record.value(0).toInt()[0]


    @pyqtSignature('int')
    def on_modelExpertDirectionsMC_itemsCountChanged(self, count):
        self.lblExpertDirectionsMCCount.setText(formatRecordsCount(count))


    @pyqtSignature('int')
    def on_modelExpertProtocolsMC_itemsCountChanged(self, count):
        self.lblExpertProtocolsMCCount.setText(formatRecordsCount(count))


    @pyqtSignature('int')
    def on_modelExpertMedicalSocialInspection_itemsCountChanged(self, count):
        self.lblExpertMedicalSocialInspectionCount.setText(formatRecordsCount(count))


    @pyqtSignature('int')
    def on_modelActionsStatus_itemsCountChanged(self, count):
        labelText = formatRecordsCount(count)
        
        actionsTotal = self.modelActionsStatus.getActionsTotal()
        clientCount = actionsTotal["clientsCount"]
        amount = actionsTotal["amount"]
        uet = actionsTotal["uet"]

        infoClients = ''
        if clientCount:
            infoClients = u', %d %s' % (clientCount, agreeNumberAndWord(clientCount, (u'пациент', u'пациента', u'пациентов')))
        labelText += infoClients
        
        self.lblActionsStatusCount.setText(labelText)
        self.actionsStatusCount = labelText
        self.lblActionsStatusAmountSum.setText(u'Количество: %.2f УЕТ: %.2f'% (amount, uet))


    @pyqtSignature('int')
    def on_modelVisits_itemsCountChanged(self, count):
        self.lblVisitCount.setText(formatRecordsCount(count))
        self.visitsCount = formatRecordsCount(count)


    @pyqtSignature('int')
    def on_modelActionsDiagnostic_itemsCountChanged(self, count):
        labelText = formatRecordsCount(count)
        
        actionsTotal = self.modelActionsDiagnostic.getActionsTotal()
        clientCount = actionsTotal["clientsCount"]
        amount = actionsTotal["amount"]
        uet = actionsTotal["uet"]

        infoClients = ''
        if clientCount:
            infoClients = u', %d %s' % (clientCount, agreeNumberAndWord(clientCount, (u'пациент', u'пациента', u'пациентов')))
        labelText += infoClients
        
        self.lblActionsDiagnosticCount.setText(labelText)
        self.actionsDiagnosticCount = labelText
        self.lblActionsDiagnosticAmountSum.setText(u'Количество: %.2f УЕТ: %.2f'% (amount, uet))


    @pyqtSignature('int')
    def on_modelActionsCure_itemsCountChanged(self, count):
        labelText = formatRecordsCount(count)
        
        actionsTotal = self.modelActionsCure.getActionsTotal()
        clientCount = actionsTotal["clientsCount"]
        amount = actionsTotal["amount"]
        uet = actionsTotal["uet"]

        infoClients = ''
        if clientCount:
            infoClients = u', %d %s' % (clientCount, agreeNumberAndWord(clientCount, (u'пациент', u'пациента', u'пациентов')))
        labelText += infoClients
        
        self.lblActionsCureCount.setText(labelText)
        self.actionsCureCount = labelText
        self.lblActionsCureAmountSum.setText(u'Количество: %.2f УЕТ: %.2f'% (amount, uet))


    @pyqtSignature('int')
    def on_modelActionsMisc_itemsCountChanged(self, count):
        labelText = formatRecordsCount(count)
        
        actionsTotal = self.modelActionsMisc.getActionsTotal()
        clientCount = actionsTotal["clientsCount"]
        amount = actionsTotal["amount"]
        uet = actionsTotal["uet"]

        infoClients = ''
        if clientCount:
            infoClients = u', %d %s' % (clientCount, agreeNumberAndWord(clientCount, (u'пациент', u'пациента', u'пациентов')))
        labelText += infoClients
        
        self.lblActionsMiscCount.setText(labelText)
        self.actionsMiscCount = labelText
        self.lblActionsMiscAmountSum.setText(u'Количество: %.2f УЕТ: %.2f'% (amount, uet))


    @pyqtSignature('int')
    def on_modelActionsAll_itemsCountChanged(self, count):
        labelText = formatRecordsCount(count)
        
        actionsTotal = self.modelActionsAll.getActionsTotal()
        clientCount = actionsTotal["clientsCount"]
        amount = actionsTotal["amount"]
        uet = actionsTotal["uet"]

        infoClients = ''
        if clientCount:
            infoClients = u', %d %s' % (clientCount, agreeNumberAndWord(clientCount, (u'пациент', u'пациента', u'пациентов')))
        labelText += infoClients
        
        self.lblActionsAllCount.setText(labelText)
        self.lblActionsAllAmountSum.setText(u'Количество: %.2f УЕТ: %.2f'% (amount, uet))


    @pyqtSignature('QModelIndex')
    def on_tblActionsStatus_doubleClicked(self, index):
        self.on_btnActionEdit_clicked()


    @pyqtSignature('QModelIndex')
    def on_tblActionsDiagnostic_doubleClicked(self, index):
        self.on_btnActionEdit_clicked()


    @pyqtSignature('QModelIndex')
    def on_tblActionsCure_doubleClicked(self, index):
        self.on_btnActionEdit_clicked()


    @pyqtSignature('QModelIndex')
    def on_tblActionsMisc_doubleClicked(self, index):
        self.on_btnActionEdit_clicked()


    @pyqtSignature('QModelIndex')
    def on_tblActionsAll_doubleClicked(self, index):
        self.on_btnActionEdit_clicked()


    @pyqtSignature('')
    def on_actOpenAccountingByEvent_triggered(self):
        eventId = self.tblEvents.currentItemId()
        self.showAccountingDialog(eventId)

    @pyqtSignature('')
    def on_actAddActionEvent_triggered(self):
        eventId = self.tblEvents.currentItemId()
        if eventId and canAddActionToExposedEvent(self, eventId):
            currentTable, currentRow, newActionIdList = addActionTabPresence(self, eventId, 0, self.tblEvents)
            #for actionId in newActionIdList:
            #    if actionId:
            #        self.editAction(actionId)
            #    currentTable.setCurrentRow(currentRow)
            self.updateEventListAfterEdit(eventId)
            self.focusEvents()


    @pyqtSignature('')
    def on_actJobTicketsEvent_triggered(self):
        eventId = self.tblEvents.currentItemId()
        if eventId:
            lockId = self.lock('Event', eventId, shorted = 1)
            if lockId:
                try:
                    getJobTicketsToEvent(self, eventId)
                finally:
                    self.releaseLock(lockId)
            self.updateEventListAfterEdit(eventId)
            self.focusEvents()


    @pyqtSignature('')
    def on_actGroupJobAppointment_triggered(self):
        self.openGroupJobAppointment()


    def getEventByActionIdList(self):
        eventIdListSelected = self.tblEvents.selectedItemIdList()
        eventIdList = {}
        for eventId in eventIdListSelected:
            actionId = None
            record = self.tblEvents.model().getRecordById(eventId)
            clientId = forceRef(record.value('client_id'))
            if eventId and (eventId not in eventIdList.keys()):
                eventIdList[eventId] = (clientId, actionId)
        return eventIdList


    def openGroupJobAppointment(self):
        currentRow = self.tblEvents.currentRow()
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
        self.tblEvents.setCurrentRow(currentRow)


    @pyqtSignature('')
    def on_actUpdateEventTypeByEvent_triggered(self):
        eventId = self.tblEvents.currentItemId()
        if eventId:
            if self.tblEvents.eventHasAccountItem(eventId):
                QtGui.QMessageBox.warning(self, u'Внимание!', u'По событию выставлен счёт, поэтому его тип не может быть изменён.', QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
            else:
                self.updateEventTypeByEvent(eventId)


    def updateEventTypeByEvent(self, eventId):
        if QtGui.qApp.userHasAnyRight([urAdmin, urUpdateEventTypeByEvent]):
            db = QtGui.qApp.db
            tableET = db.table('Event')
            record = db.getRecordEx(tableET, '*', [tableET['id'].eq(eventId), tableET['deleted'].eq(0)])
            eventTypeId = forceRef(record.value('eventType_id')) if record else None
            oldPrevEventId = forceRef(record.value('prevEvent_id')) if record else None
            clientId    = forceRef(record.value('client_id')) if record else None
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
                                eventTypeRecord = db.getRecordEx('EventType', 'changeExternalId', 'EventType.deleted=0 and EventType.id = {}'.format(newEventTypeId))
                                if eventTypeRecord:
                                    changeExternalId = forceBool(eventTypeRecord.value('changeExternalId'))
                                else:
                                    changeExternalId = False
                                if changeExternalId:
                                    counterId = getEventCounterId(newEventTypeId)
                                    if counterId:
                                        try:
                                            if not QtGui.qApp.counterController():
                                                QtGui.qApp.setCounterController(CCounterController(self))
                                            externalId = QtGui.qApp.getDocumentNumber(clientId, counterId)
                                            record.setValue('externalId', externalId)
                                        except Exception as e:
                                            QtGui.QMessageBox.critical(QtGui.qApp.mainWindow,
                                                                    u'Внимание!',
                                                                    u'Произошла ошибка при получении значения счетчика\n%s' % e,
                                                                    QtGui.QMessageBox.Ok)
                                            return False
                                    else:
                                        record.setValue('externalId', '')
                                record.setValue('eventType_id', toVariant(newEventTypeId))
                                if order > -1:
                                    record.setValue('order', toVariant(order+1))
                                if contractId:
                                    record.setValue('contract_id', toVariant(contractId))
                                idList = set([])
                                idListParents = set(db.getTheseAndParents(tableET, 'prevEvent_id', [eventId if eventId else self.prevEventId]))
                                idList ^= idListParents
                                idListDescendant = set(db.getDescendants(tableET, 'prevEvent_id', eventId if eventId else self.prevEventId))
                                idList ^= idListDescendant
                                if len(idList) < 2:
                                    prevEventTypeId = getEventPrevEventTypeId(newEventTypeId)
                                    prevEventId = getPrevEventIdByEventTypeId(prevEventTypeId, clientId) if prevEventTypeId else None
                                    if prevEventTypeId and oldPrevEventId != prevEventId:
                                        record.setValue('prevEvent_id', toVariant(prevEventId))
                            db.updateRecord(tableET, record)
                            self.updateEventListAfterEdit(eventId)
                            QtGui.qApp.delAllCounterValueIdReservation()
                    except Exception as e:
                        QtGui.qApp.logCurrentException()
                        QtGui.QMessageBox.critical(QtGui.qApp.mainWindow,
                                                    u'Произошла ошибка',
                                                    exceptionToUnicode(e),
                                                    QtGui.QMessageBox.Close)
                    finally:
                        dialog.deleteLater()


    @pyqtSignature('')
    def on_actUndoExpertise_triggered(self):
        eventId = self.tblEvents.currentItemId()
        if eventId:
            res = QtGui.QMessageBox.warning(self,
                            u'Внимание!',
                            u'Действительно отменить экспертизу?',
                            QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel,
                            QtGui.QMessageBox.Ok)
            if res == QtGui.QMessageBox.Ok:
                self.undoExpertise(eventId)


    def undoExpertise(self, eventId):
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        record = db.getRecordEx(tableEvent, '*', [tableEvent['id'].eq(eventId), tableEvent['deleted'].eq(0)])
        record.setNull('expertiseDate')
        record.setNull('expert_id')
        db.updateRecord(tableEvent, record)


    @pyqtSignature('')
    def on_actConcatEvents_triggered(self):
        eventId = self.tblEvents.currentItemId()
        self.concatEvents(eventId)


    @pyqtSignature('')
    def on_actMakePersonalAccount_triggered(self):
        eventId = self.tblEvents.currentItemId()
        self.makePersonalAccount(eventId)


    @pyqtSignature('')
    def on_actOpenAccountingByAction_triggered(self):
        actionId = self.tblEventActions.currentItemId()
        self.showAccountingDialog(None, actionId)


    @pyqtSignature('')
    def on_actOpenAccountingBySingleAction_triggered(self):
        actionId = self.getCurrentActionsTable().currentItemId()
        self.showAccountingDialog(None, actionId)


    @pyqtSignature('')
    def on_actOpenAccountingBySingleVisits_triggered(self):
        visitId = self.tblVisits.currentItemId()
        self.showAccountingDialog(None, None, visitId)


    @pyqtSignature('')
    def on_actOpenAccountingByVisit_triggered(self):
        visitId = self.tblEventVisits.currentItemId()
        self.showAccountingDialog(None, None, visitId)


    @pyqtSignature('')
    def on_actEditExpertMCEvent_triggered(self):
        currentTable = self.getCurrentExpertMedicalCommissionTable()
        actionId = currentTable.currentItemId()
        self.openEvent(actionId)
        currentTable.setFocus(Qt.TabFocusReason)


    @pyqtSignature('')
    def on_actEditActionEvent_triggered(self):
        self.on_btnActionEventEdit_clicked()


    @pyqtSignature('')
    def on_btnActionEventEdit_clicked(self):
        actionId = self.currentActionId()
        self.openEvent(actionId)
        self.focusActions()


    def openEvent(self, actionId):
        if actionId:
            eventId = forceRef(QtGui.qApp.db.translate('Action', 'id', actionId, 'event_id'))
            if eventId:
                if self.getEventTypeIdF090(eventId):
                    actionId = self.getF090ActionIdToEventId(eventId)
                    if actionId and canChangePayStatusAdditional(self, 'Action', actionId) and canEditOtherpeopleAction(self, actionId):
                        if forceBool(self.getF090ActionTypeId(actionId)):
                            if self.editF090ActionToEventId(actionId):
                                self.on_buttonBoxAction_apply()
                else:
                    if editEvent(self, eventId):
                        self.on_buttonBoxAction_apply()


    @pyqtSignature('')
    def on_actEditVisitEvent_triggered(self):
        visitId = self.tblVisits.currentItemId()
        if visitId:
            eventId = self.getEventIdForVisit(visitId)
            if eventId:
                if editEvent(self, eventId):
                   self.on_buttonBoxAction_apply()
        self.focusActions()


    @pyqtSignature('QModelIndex')
    def on_tblVisits_doubleClicked(self, index):
        self.on_actEditVisitEvent_triggered()


    @pyqtSignature('')
    def on_btnActionEdit_clicked(self):
        actionId = self.currentActionId()
        if actionId and canChangePayStatusAdditional(self, 'Action', actionId) and canEditOtherpeopleAction(self, actionId):
            if forceBool(self.getF090ActionTypeId(actionId)):
                self.editF090Action(actionId)
            else:
                self.editAction(actionId)
            self.updateActionsList(self.__actionFilter, actionId)
            QtGui.qApp.emitCurrentClientInfoChanged()
        self.focusActions()


    def getF090ActionTypeId(self, actionId):
        if actionId:
            db = QtGui.qApp.db
            tableAction = db.table('Action')
            tableActionType = db.table('ActionType')
            queryTable = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
            cond = [tableAction['id'].eq(actionId),
                    tableAction['deleted'].eq(0),
                    tableActionType['deleted'].eq(0),
                    tableActionType['flatCode'].like(u'%medical_examination'),
                    ]
            record = db.getRecordEx(queryTable, [tableActionType['id'].alias('actionTypeId')], cond)
            return forceRef(record.value('actionTypeId')) if record else None
        return None


    def editF090Action(self, actionId):
        newActionId = None
        dialog = CF090EditDialog(self)
        try:
            dialog.load(actionId)
            dialog.protectWidgetFromEdit(False)
            dialog.exec_()
            if dialog.isBtnSave:
                self.updateActionsList(self.__actionFilter, dialog.itemId())
                QtGui.qApp.emitCurrentClientInfoChanged()
                newActionId = dialog.itemId()
            else:
                self.updateActionInfo(actionId)
                self.updateClientsListRequest = True
        finally:
            dialog.deleteLater()
        return newActionId


    def expertMedicalCommissionActionEdit(self):
        currentTable = self.getCurrentExpertMedicalCommissionTable()
        actionId = currentTable.currentItemId()
        if actionId and canChangePayStatusAdditional(self, 'Action', actionId) and canEditOtherpeopleAction(self, actionId):
            if self.tabExpertMedicalCommissionWidget.currentIndex() == self.tabExpertMedicalCommissionWidget.indexOf(self.tabExpertMedicalSocialInspection):
                db = QtGui.qApp.db
                tableAction = db.table('Action')
                recordAction = db.getRecordEx(tableAction, [tableAction['createDatetime']],
                                              [tableAction['id'].eq(actionId), tableAction['deleted'].eq(0)])
                createDate = forceDate(recordAction.value('createDatetime')) if recordAction else None
                if createDate and createDate >= QDate(2022, 1, 1):
                    dialog = CF0882022EditDialog(self)
                else:
                    dialog = CF088EditDialog(self)
            else:
                dialog = CActionEditDialog(self)
            try:
                dialog.load(actionId)
                if dialog.exec_():
                    self.updateMedicalCommissionList(self.__expertMCFilter, dialog.itemId())
                    currentTable.model().updateColumnsCaches(actionId)
                    if self.tabExpertMedicalCommissionWidget.currentIndex() == self.tabExpertMedicalCommissionWidget.indexOf(self.tabExpertMedicalSocialInspection):
                        self.tblExpertProtocolsMC.model().updateColumnsCaches(actionId)
                    QtGui.qApp.emitCurrentClientInfoChanged()
                    return dialog.itemId()
                else:
                    self.updateMedicalCommissionInfo(actionId)
                    self.updateClientsListRequest = True
                return None
            finally:
                dialog.deleteLater()
        self.focusExpertMC()


    @pyqtSignature('')
    def on_btnVisitEdit_clicked(self):
        visitId = self.tblVisits.currentItemId()
        if visitId and canChangePayStatusAdditional(self, 'Visit', visitId):
            eventId = self.getEventIdForVisit(visitId)
            if eventId:
                eventId = editEvent(self, eventId)
        self.tblVisits.setFocus(Qt.TabFocusReason)


    def getEventIdForVisit(self, visitId):
        db = QtGui.qApp.db
        table = db.table('Visit')
        record = db.getRecordEx(table, [table['event_id']], [table['id'].eq(visitId)])
        if record:
            return forceRef(record.value('event_id'))
        return None


    @pyqtSignature('int')
    def on_btnActionPrint_printByTemplate(self, templateId):
        if templateId == -1:
            tblActions = self.getCurrentActionsTable()
            tblActions.setReportHeader(u'Список мероприятий')
            tblActions.setReportDescription(self.getActionFilterAsText())
    #        if self.cmbFilterAction.currentIndex() == 0:
    #            mask = [False]*3 + [True]*(model.columnCount()-3)
    #        else:
    #            mask = [True]*(model.columnCount())
    #        tblActions.printContent(mask)
            tblActions.printContent()
            self.focusActions()
        else:
            tblActions = self.getCurrentActionsTable()
            actionId = tblActions.currentItemId()
            idList = tblActions.model().idList()
            context = CInfoContext()
            action = context.getInstance(CActionInfo, actionId)
            if self.cmbFilterActionType.value():
                actionType = context.getInstance(CActionTypeInfo, (CActionTypeCache.getById(forceRef(self.cmbFilterActionType.value()))))
            else:
                actionType = None
            actionBegSetDate = CDateInfo(self.edtFilterActionBegSetDate.date()) if self.chkFilterActionSetDate.isChecked() else None
            actionEndSetDate = CDateInfo(self.edtFilterActionEndSetDate.date()) if self.chkFilterActionSetDate.isChecked() else None
            actionBegBegDate = CDateInfo(self.edtFilterActionBegBegDate.date()) if self.chkFilterActionBegDate.isChecked() else None
            actionEndBegDate = CDateInfo(self.edtFilterActionEndBegDate.date()) if self.chkFilterActionBegDate.isChecked() else None
            actionBegBegTime = CTimeInfo(self.edtFilterActionBegBegTime.time()) if self.chkFilterActionBegDate.isChecked() else None
            actionEndBegTime = CTimeInfo(self.edtFilterActionEndBegTime.time()) if self.chkFilterActionBegDate.isChecked() else None
            actionBegExecDate = CDateInfo(self.edtFilterActionBegExecDate.date()) if self.chkFilterActionExecDate.isChecked() else None
            actionEndExecDate = CDateInfo(self.edtFilterActionEndExecDate.date()) if self.chkFilterActionExecDate.isChecked() else None
            actionBegExecTime = CTimeInfo(self.edtFilterActionBegExecTime.time()) if self.chkFilterActionExecDate.isChecked() else None
            actionEndExecTime = CTimeInfo(self.edtFilterActionEndExecTime.time()) if self.chkFilterActionExecDate.isChecked() else None
            actionExecOrgStructure = context.getInstance(COrgStructureInfo, forceRef(self.cmbFilterActionExecSetOrgStructure.value()))
            actionExecSpeciality = context.getInstance(CSpecialityInfo, forceRef(self.cmbFilterActionExecSetSpeciality.value()))
            actionExecSetPerson = context.getInstance(CPersonInfo, forceRef(self.cmbFilterActionExecSetPerson.value()))
            actionExecSetAssistant = context.getInstance(CPersonInfo, forceRef(self.cmbFilterActionAssistant.value()))
            filter = {'actionType' : actionType,
                        'actionBegSetDate' : actionBegSetDate,
                        'actionEndSetDate' : actionEndSetDate,
                        'actionBegBegDate' : actionBegBegDate,
                        'actionEndBegDate' : actionEndBegDate,
                        'actionBegBegTime' : actionBegBegTime,
                        'actionEndBegTime' : actionEndBegTime,
                        'actionBegExecDate' : actionBegExecDate,
                        'actionEndExecDate' : actionEndExecDate,
                        'actionBegExecTime' : actionBegExecTime,
                        'actionEndExecTime' : actionEndExecTime,
                        'actionExecOrgStructure' : actionExecOrgStructure if actionExecOrgStructure else None,
                        'actionExecSpeciality' : actionExecSpeciality if actionExecSpeciality else None,
                        'actionExecSetPerson' : actionExecSetPerson if actionExecSetPerson else None,
                        'actionExecSetAssistant' : actionExecSetAssistant if actionExecSetAssistant else None
                        }
            data = { 'actions': CLocActionInfoList(context, idList),
                     'currentAction': action if action else None,
                            'filter':filter}
            QtGui.qApp.call(self, applyTemplate, (self, templateId, data))


    @pyqtSignature('int')
    def on_btnVisitPrint_printByTemplate(self, templateId):
        if templateId == -1:
            self.tblVisits.setReportHeader(u'Список визитов')
            self.tblVisits.setReportDescription(self.getVisitFilterAsText())
            self.tblVisits.printContent()
            self.focusEvents()
        else:
            context = CInfoContext()
            visitInfo = context.getInstance(CVisitInfo, self.tblVisits.currentItemId())
            visitInfoList = context.getInstance(CVisitInfoListEx, tuple(self.tblVisits.model().idList()))
            data = { 'visitList'    : visitInfoList,
                     'visit'        : visitInfo,
                     'filterVisitBegDate'   : CDateInfo(self.edtFilterVisitBegExecDate.date()) if self.chkFilterVisitExecDate.isChecked() else None,
                     'filterVisitBegTime'   : CTimeInfo(self.edtFilterVisitBegExecTime.time()) if self.chkFilterVisitExecDate.isChecked() else None,
                     'filterVisitEndDate'   : CDateInfo(self.edtFilterVisitEndExecDate.date()) if self.chkFilterVisitExecDate.isChecked() else None,
                     'filterVisitEndTime'   : CTimeInfo(self.edtFilterVisitEndExecTime.time()) if self.chkFilterVisitExecDate.isChecked() else None,
                     'filterVisitExecSetOrgStructure': context.getInstance(COrgStructureInfo, self.cmbFilterExecSetOrgStructureVisit.value() if self.chkFilterActionExecSetOrgStructure.isChecked() else None),
                     'filterVisitExecSetSpeciality'  : context.getInstance(CSpecialityInfo, self.cmbFilterExecSetSpecialityVisit.value() if self.chkFilterExecSetSpecialityVisit.isChecked() else None),
                     'filterVisitExecSetPerson'      : context.getInstance(CPersonInfo, self.cmbFilterExecSetPersonVisit.value() if self.chkFilterExecSetPersonVisit.isChecked() else None),
                     'filterVisitAssistant'          : context.getInstance(CPersonInfo, self.cmbFilterVisitAssistant.value() if self.chkFilterVisitAssistant.isChecked() else None),
                     'filterVisitFinance'            : context.getInstance(CFinanceInfo, self.cmbFilterVisitFinance.value() if self.chkFilterVisitFinance.isChecked() else None),
                     'filterVisitService'            : context.getInstance(CServiceInfo, self.cmbFilterServiceVisit.value() if self.chkFilterServiceVisit.isChecked() else None),
                     'filterVisitScene'              : context.getInstance(CSceneInfo, self.cmbFilterSceneVisit.value() if self.chkFilterSceneVisit.isChecked() else None),
                     'filterVisitCreatePersonEx'     : context.getInstance(CPersonInfo, self.cmbFilterVisitCreatePersonEx.value() if self.chkFilterVisitCreatePersonEx.isChecked() else None),
                     'filterVisitBegCreateDateEx'    : CDateInfo(self.edtFilterVisitBegCreateDateEx.date()) if self.chkFilterVisitCreateDateEx.isChecked() else None,
                     'filterVisitEndCreateDateEx'    : CDateInfo(self.edtFilterVisitEndCreateDateEx.date()) if self.chkFilterVisitCreateDateEx.isChecked() else None,
                     'filterVisitModifyPersonEx'     : context.getInstance(CPersonInfo, self.cmbFilterVisitModifyPersonEx.value() if self.chkFilterVisitModifyPersonEx.isChecked() else None),
                     'filterVisitBegModifyDateEx'    : CDateInfo(self.edtFilterVisitBegModifyDateEx.date()) if self.chkFilterVisitModifyDateEx.isChecked() else None,
                     'filterVisitEndModifyDateEx'    : CDateInfo(self.edtFilterVisitEndModifyDateEx.date()) if self.chkFilterVisitModifyDateEx.isChecked() else None,
                     'filterVisitPayStatusCodeEx'    : forceString(self.cmpFilterVisitPayStatusCodeEx.currentText()) if self.chkFilterVisitPayStatusEx.isChecked() else '',
                     'filterVisitPayStatusFinanceEx' : forceString(self.cmbFilterVisitPayStatusFinanceEx.currentText()) if self.chkFilterVisitPayStatusEx.isChecked() else ''
                     }
            QtGui.qApp.call(self, applyTemplate, (self, templateId, data))


    @pyqtSignature('int')
    def on_btnPrint_printByTemplate(self, templateId):
        context = CInfoContext()
        clientInfo = context.getInstance(CClientInfo, self.tblClients.currentItemId())
        clientInfoList = context.getInstance(CClientInfoListEx, tuple(self.tblClients.model().idList()))
        data = { 'clientsList': clientInfoList,
                 'client'    : clientInfo }
        clientId = self.selectedClientId()
        data['clientId'] = clientId
        QtGui.qApp.call(self, applyTemplate, (self, templateId, data))


    @pyqtSignature('')
    def on_btnActionFilter_clicked(self):
        for s in self.chkListOnActionsPage:
            chk = s[0]
            if chk.isChecked():
                self.activateFilterWdgets(s[1])
                return
        self.chkFilterActionType.setChecked(True)


    @pyqtSignature('')
    def on_btnVisitFilter_clicked(self):
        for s in self.chkListOnVisitsPage:
            chk = s[0]
            if chk.isChecked():
                self.activateFilterWdgets(s[1])
                return
        self.chkFilterVisitType.setChecked(True)


    @pyqtSignature('bool')
    def on_chkFilterActionType_toggled(self, checked):
        if checked:
            self.chkFilterActionId.setChecked(False)
            self.edtFilterActionId.setEnabled(False)
        self.onChkFilterToggled(self.sender(), checked)
        if not checked or not self.chkTakeIntoAccountProperty.isChecked() or not self.cmbFilterActionType.value():
            self.enabledOptionProperty(checked)
            self.chkFilledProperty.setEnabled(False)
            self.cmbFilledProperty.setEnabled(False)
            self.lblListProperty.setEnabled(False)
            self.cmbListPropertyCond.setEnabled(False)
            self.tblListOptionActionProperty.setEnabled(False)
        elif self.chkTakeIntoAccountProperty.isChecked():
            self.on_chkFilledProperty_toggled(checked and self.chkFilledProperty.isChecked())


    @pyqtSignature('bool')
    def on_chkFilterActionServiceType_toggled(self, checked):
        if checked:
            self.chkFilterActionId.setChecked(False)
            self.edtFilterActionId.setEnabled(False)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkThresholdPenaltyGrade_toggled(self, checked):
        # self.setChildElementsVisible(self.chkListOnActionsPage, self.chkListProperty, checked)
        self.onChkFilterToggled(self.sender(), checked)


#    @pyqtSignature('bool')
#    def on_chkListProperty_toggled(self, checked):
#        self.onChkFilterToggled(self.sender(), checked)
#        actionTypeId = forceRef(self.cmbFilterActionType.value())
#        self.enabledOptionProperty(checked, actionTypeId)


    def makePersonalAccount(self, eventId):
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableContract = db.table('Contract')
        tableFinance = db.table('rbFinance')
        table = tableEvent.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
        table = table.innerJoin(tableFinance, tableFinance['id'].eq(tableContract['finance_id']))
        cond = [tableEvent['id'].eq(eventId)]
        contractRecord = db.getRecordEx(table, 'Contract.*,rbFinance.name as financeName', cond)
        number = forceString(contractRecord.value('number'))
        finance = forceString(contractRecord.value('financeName'))
        mbResult = QtGui.QMessageBox.question(self,
            u'Внимание!', u'Договор номер %s, (%s)\nДействительно сформировать счет?'%(number, finance),
            QtGui.QMessageBox.Yes|QtGui.QMessageBox.No, QtGui.QMessageBox.No)
        if {QtGui.QMessageBox.Yes: True,
                QtGui.QMessageBox.No: False}.get(mbResult, None):
            try:
                from Accounting.InstantAccountDialog import createInstantAccount
                createInstantAccount(eventId, False)
            except:
                QtGui.qApp.logCurrentException()


    def concatEvents(self, eventId):
        mbResult = QtGui.QMessageBox().question(self, u'Внимание!',
                                                u'Действительно выполнить слияние событий?',
                                                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
        if {QtGui.QMessageBox.Yes: True, QtGui.QMessageBox.No: False}.get(mbResult, None):
            db = QtGui.qApp.db
            record = self.modelEvents.getRecordById(eventId)
            if record:
                prevId = forceRef(record.value('prevEvent_id'))
                if prevId:
                    prevRecord = self.modelEvents.getRecordById(prevId)
                    prevRecord.setValue('result_id', record.value('result_id'))
                    prevRecord.setValue('execDate', record.value('execDate'))
                    tableAction = db.table('Action')
                    actionList = db.getRecordList(tableAction, '*', tableAction['event_id'].eq(eventId))
                    for action in actionList:
                        action.setValue('event_id', prevId)
                        db.updateRecord(tableAction, action)
                    actionList = db.getRecordList(tableAction, '*', tableAction['event_id'].eq(prevId), 'begDate')
                    for i, action in enumerate(actionList):
                        action.setValue('idx', i)
                        db.updateRecord(tableAction, action)
                    db.updateRecord('Event', prevRecord)
                    self.tblEvents.removeCurrentRow(False)
                else:
                    QtGui.QMessageBox().information(self, u'Предупреждение!',
                                                    u'У данного обращения нет связанных событий!',
                                                    QtGui.QMessageBox.Ok,
                                                    QtGui.QMessageBox.Ok)


    def enabledOptionProperty(self, checked, actionTypeId = None):
        if actionTypeId and checked:
            self.cmbFilledProperty.setEnabled(True)
            self.cmbListPropertyCond.setEnabled(True)
            self.lblListProperty.setEnabled(True)
            self.tblListOptionActionProperty.setEnabled(True)
            self.on_cmbFilledProperty_currentIndexChanged(self.cmbFilledProperty.currentIndex())
            QtGui.qApp.callWithWaitCursor(self, self.updateDataOptiontPropertiesTable, actionTypeId)
        else:
            self.on_cmbFilledProperty_currentIndexChanged(self.cmbFilledProperty.currentIndex())
            self.tblListOptionActionProperty.model().setActionTypeProperty(None)
            self.cmbFilledProperty.setEnabled(False)
            self.cmbListPropertyCond.setEnabled(False)
            self.lblListProperty.setEnabled(False)
            self.tblListOptionActionProperty.setEnabled(False)


    def updateDataOptiontPropertiesTable(self, actionTypeId):
        if actionTypeId:
            db = QtGui.qApp.db
            actionTypeRecord = db.getRecord('ActionType', '*', actionTypeId)
            actionType = CActionType(actionTypeRecord)
            tableAction = db.table('Action')
            newRecord = tableAction.newRecord()
            newRecord.setValue('createDatetime',  toVariant(QDateTime.currentDateTime()))
            newRecord.setValue('createPerson_id', toVariant(QtGui.qApp.userId))
            newRecord.setValue('modifyDatetime',  toVariant(QDateTime.currentDateTime()))
            newRecord.setValue('modifyPerson_id', toVariant(QtGui.qApp.userId))
            newRecord.setValue('actionType_id',   toVariant(actionTypeId))
            newRecord.setValue('begDate',         toVariant(QDateTime.currentDateTime()))
            newRecord.setValue('directionDate',   toVariant(QDateTime.currentDateTime()))
            newRecord.setValue('setPerson_id',    toVariant(QtGui.qApp.userId))
            newRecord.setValue('plannedEndDate',   toVariant(QDateTime.currentDateTime()))
            newAction = CAction(actionType=actionType, record=newRecord)
            initActionProperties(newAction)
            self.tblListOptionActionProperty.model().setActionTypeProperty(newAction)
            self.tblListOptionActionProperty.resizeColumnsToContents()
#            self.tblListOptionActionProperty.resizeRowsToContents()
            self.tblListOptionActionProperty.horizontalHeader().setStretchLastSection(True)
        else:
            self.tblListOptionActionProperty.model().setActionTypeProperty(None)


    def getDataOptionPropertyChecked(self):
        from Events.ActionProperty import CActionPropertyValueTypeRegistry
        optionPropertyIdList = []
        optionQueryTableList = []
        model = self.tblListOptionActionProperty.model()
        if model and model.action:
            db = QtGui.qApp.db
            for row, propertyType in enumerate(model.propertyTypeList):
                include = model.includeRows.get(row, 0)
                if include == Qt.Checked:
                    optionPropertyId = propertyType.id
                    optionPropertyIdList.append(optionPropertyId)
                    typeName = propertyType.typeName
                    valueDomain = propertyType.valueDomain
                    propertyTypeRegistry = CActionPropertyValueTypeRegistry.get(typeName, valueDomain)
                    if propertyTypeRegistry:
                        tableName = propertyTypeRegistry.getTableName()
                        tablePropertyType = db.table(tableName).alias(tableName + str(row))
                        tableActionProperty = db.table('ActionProperty').alias('ActionProperty' + str(row))
                        property = model.action.getPropertyById(propertyType.id)
                        value = property.getValue()
                        if isinstance(value, basestring):
                            optionQueryTableList.append(((tablePropertyType, tableActionProperty, optionPropertyId), [tablePropertyType['id'].eq(tableActionProperty['id']), tablePropertyType['value'].like(value) if value else tablePropertyType['value'].isNull()]))
                        else:
                            optionQueryTableList.append(((tablePropertyType, tableActionProperty, optionPropertyId), [tablePropertyType['id'].eq(tableActionProperty['id']), tablePropertyType['value'].eq(value) if value else tablePropertyType['value'].isNull()]))
        return optionPropertyIdList, optionQueryTableList


    @pyqtSignature('int')
    def on_cmbFilledProperty_currentIndexChanged(self, index):
        if index == 2:
            self.tblListOptionActionProperty.setColumnHidden(self.tblListOptionActionProperty.model().ciValue, False)
        else:
            self.tblListOptionActionProperty.setColumnHidden(self.tblListOptionActionProperty.model().ciValue, True)


    @pyqtSignature('bool')
    def on_chkFilledProperty_toggled(self, checked):
        if checked:
            self.chkThresholdPenaltyGrade.setChecked(False)
            self.chkThresholdPenaltyGrade.setEnabled(False)
            self.edtThresholdPenaltyGrade.setEnabled(False)
            self.on_cmbFilledProperty_currentIndexChanged(self.cmbFilledProperty.currentIndex())
        elif self.chkTakeIntoAccountProperty.isChecked():
             self.chkThresholdPenaltyGrade.setEnabled(True)
        actionTypeId = forceRef(self.cmbFilterActionType.value())
        self.enabledOptionProperty(checked, actionTypeId)


    @pyqtSignature('bool')
    def on_chkTakeIntoAccountProperty_toggled(self, checked):
        if checked:
            self.chkFilterActionId.setChecked(False)
            self.edtFilterActionId.setEnabled(False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkTakeIntoAccountProperty, checked)
        self.onChkFilterToggled(self.sender(), checked)
        if not checked or not self.chkFilterActionType.isChecked() or not self.cmbFilterActionType.value():
            self.enabledOptionProperty(checked)
            self.chkFilledProperty.setChecked(False)
            self.chkFilledProperty.setEnabled(False)
            self.cmbFilledProperty.setEnabled(False)
            self.lblListProperty.setEnabled(False)
            self.cmbListPropertyCond.setEnabled(False)
            self.tblListOptionActionProperty.setEnabled(False)
        elif checked and self.chkFilterActionType.isChecked() and self.cmbFilterActionType.value() and self.chkFilledProperty.isChecked():
            self.chkFilledProperty.setEnabled(True)
            self.cmbFilledProperty.setEnabled(True)
            self.lblListProperty.setEnabled(True)
            self.cmbListPropertyCond.setEnabled(True)
            self.tblListOptionActionProperty.setEnabled(True)
        if not self.chkThresholdPenaltyGrade.isChecked():
            self.edtThresholdPenaltyGrade.setEnabled(False)


    @pyqtSignature('int')
    def on_cmbFilterActionType_currentIndexChanged(self, index):
        actionClass = self.getActionClassByTabIndex()
        if actionClass:
            self.__actionTypeIdListByClassPage[actionClass] = self.cmbFilterActionType.value()
        actionTypeId = forceRef(self.cmbFilterActionType.value())
        self.chkFilledProperty.setEnabled(bool(actionTypeId) and self.chkTakeIntoAccountProperty.isChecked())
        self.enabledOptionProperty((self.chkFilledProperty.isEnabled() and self.chkFilledProperty.isChecked()), actionTypeId)

    @pyqtSignature('bool')
    def on_chkFilterActionPayer_toggled(self, checked):
        if checked:
            self.chkFilterActionId.setChecked(False)
            self.edtFilterActionId.setEnabled(False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionPayer, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('')
    def on_btnFilterActionSelectPayer_clicked(self):
        orgId = selectOrganisation(self, self.cmbFilterActionPayer.value(), False)
        self.cmbFilterActionPayer.updateModel()
        if orgId:
            self.cmbFilterActionPayer.setValue(orgId)


    @pyqtSignature('bool')
    def on_chkFilterActionContract_toggled(self, checked):
        if checked:
            self.chkFilterActionId.setChecked(False)
            self.edtFilterActionId.setEnabled(False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionContract, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterActionExport_toggled(self, checked):
        if checked:
            if not self.cmbFilterActionExportSystem.hasTable():
                self.cmbFilterActionExportSystem.setTable('rbExternalSystem', True)
            self.chkFilterActionId.setChecked(False)
            self.edtFilterActionId.setEnabled(False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionExport, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterActionAttachedFiles_toggled(self, checked):
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionAttachedFiles, checked)
        self.cmbFilterActionAttachedFiles.setEnabled(checked)
        self.chkFilterActionFileAttachId.setEnabled(checked)
        self.chkFilterActionExportSuitable.setEnabled(checked)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionFileAttachId, checked & self.chkFilterActionFileAttachId.isChecked())
        if self.cmbFilterActionAttachedFiles.isEnabled():
            if self.cmbFilterActionAttachedFiles.currentIndex() == 0:
                self.cmbFilterActionTypeDoc.setEnabled(True)
                self.cmbFilterActionSigned.setEnabled(True)
                self.lblActionTypeDoc.setEnabled(True)
                self.lblActionSigned.setEnabled(True)
            else:
                self.cmbFilterActionTypeDoc.setEnabled(False)
                self.cmbFilterActionSigned.setEnabled(False)
                self.lblActionTypeDoc.setEnabled(False)
                self.lblActionSigned.setEnabled(False)
        else:
            self.cmbFilterActionTypeDoc.setEnabled(False)
            self.cmbFilterActionSigned.setEnabled(False)
            self.lblActionTypeDoc.setEnabled(False)
            self.lblActionSigned.setEnabled(False)

    @pyqtSignature('')
    def on_btnFilterActionContract_clicked(self):
        (contractId, contractDescr, filterActionContractParams)= selectContract(self, self.__filterActionContractId)
        self.__filterActionContractId = contractId
        self.edtFilterActionContract.setText(contractDescr)


    @pyqtSignature('bool')
    def on_chkFilterActionSetDate_toggled(self, checked):
        if checked:
            self.chkFilterActionId.setChecked(False)
            self.edtFilterActionId.setEnabled(False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionSetDate, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterActionSetSpeciality_toggled(self, checked):
        if checked:
            if not self.cmbFilterActionSetSpeciality.hasTable():
                self.cmbFilterActionSetSpeciality.setTable('rbSpeciality', False)
            self.chkFilterActionId.setChecked(False)
            self.edtFilterActionId.setEnabled(False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionSetSpeciality, checked)
        self.onChkFilterToggled(self.sender(), checked)
        if checked:
            self.chkFilterActionSetPerson.setChecked(False)
            self.cmbFilterActionSetPerson.setSpecialityId(self.cmbFilterActionSetSpeciality.value())
        else:
            self.cmbFilterActionSetPerson.setSpecialityId(None)


    @pyqtSignature('bool')
    def on_chkFilterActionSetOrgStructure_toggled(self, checked):
        if checked:
            self.chkFilterActionId.setChecked(False)
            self.edtFilterActionId.setEnabled(False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionSetOrgStructure, checked)
        self.onChkFilterToggled(self.sender(), checked)
        if checked:
            self.chkFilterActionSetPerson.setChecked(False)
            self.cmbFilterActionSetPerson.setOrgStructureId(self.cmbFilterActionSetOrgStructure.value())
        else:
            self.cmbFilterActionSetPerson.setOrgStructureId(None)


    @pyqtSignature('bool')
    def on_chkFilterActionExecSetOrgStructure_toggled(self, checked):
        if checked:
            self.chkFilterActionId.setChecked(False)
            self.edtFilterActionId.setEnabled(False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionExecSetOrgStructure, checked)
        self.onChkFilterToggled(self.sender(), checked)
        if checked:
            self.chkFilterActionExecSetPerson.setChecked(False)
            execSetOrgStructure = self.cmbFilterActionExecSetOrgStructure.value()
            if not execSetOrgStructure:
                execSetOrgStructure = QtGui.qApp.currentOrgStructureId()
                self.cmbFilterActionExecSetOrgStructure.setValue(execSetOrgStructure)
            self.cmbFilterActionSetPerson.setOrgStructureId(execSetOrgStructure)
        else:
            self.cmbFilterActionSetPerson.setOrgStructureId(None)


    @pyqtSignature('bool')
    def on_chkFilterActionExecSetSpeciality_toggled(self, checked):
        if checked:
            if not self.cmbFilterActionExecSetSpeciality.hasTable():
                self.cmbFilterActionExecSetSpeciality.setTable('rbSpeciality', False)
            self.chkFilterActionId.setChecked(False)
            self.edtFilterActionId.setEnabled(False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionExecSetSpeciality, checked)
        self.onChkFilterToggled(self.sender(), checked)
        if checked:
            self.chkFilterActionExecSetPerson.setChecked(False)
            self.cmbFilterActionExecSetPerson.setSpecialityId(self.cmbFilterActionExecSetSpeciality.value())
        else:
            self.cmbFilterActionExecSetPerson.setSpecialityId(None)


    @pyqtSignature('int')
    def on_cmbFilterActionSetSpeciality_currentIndexChanged(self, index):
        self.cmbFilterActionSetPerson.setSpecialityId(self.cmbFilterActionSetSpeciality.value())


    @pyqtSignature('int')
    def on_cmbFilterActionExecSetSpeciality_currentIndexChanged(self, index):
        self.cmbFilterActionExecSetPerson.setSpecialityId(self.cmbFilterActionExecSetSpeciality.value())
    
    
    @pyqtSignature('int')
    def on_cmbFilterActionAttachedFiles_currentIndexChanged(self, index):
        active = True if index == 0 else False
        self.cmbFilterActionTypeDoc.setEnabled(active)
        self.cmbFilterActionSigned.setEnabled(active)
        if not self.chkFilterActionExportSuitable.isEnabled():
            self.chkFilterActionExportSuitable.setChecked(False)
        self.setChildElementsVisible(self.chkListOnActionsPage , self.edtFilterActionFileAttachId, active)


    @pyqtSignature('bool')
    def on_chkFilterActionSetPerson_toggled(self, checked):
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionSetPerson, checked)
        self.cmbFilterActionSetPerson.setEnabled(checked)
        if self.cmbFilterActionSetPerson.currentIndex() == 0:
            self.chkFilterActionSNILSSetPerson.setEnabled(False)
        else:
            self.chkFilterActionSNILSSetPerson.setEnabled(True)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionSNILSSetPerson, checked & self.chkFilterActionSNILSSetPerson.isChecked())
        self.chkFilterActionSetOrgStructure.setChecked(False)
        self.chkFilterActionSetSpeciality.setChecked(False)

    @pyqtSignature('int')
    def on_cmbFilterActionSetPerson_currentIndexChanged(self):
        if self.cmbFilterActionSetPerson.currentIndex() == 0:
            self.chkFilterActionSNILSSetPerson.setEnabled(False)
        else:
            self.chkFilterActionSNILSSetPerson.setEnabled(True)
        if not self.chkFilterActionSNILSSetPerson.isEnabled():
            self.chkFilterActionSNILSSetPerson.setChecked(False)

    @pyqtSignature('bool')
    def on_chkFilterActionExecSetPerson_toggled(self, checked):
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionExecSetPerson, checked)
        self.cmbFilterActionExecSetPerson.setEnabled(checked)
        if self.cmbFilterActionExecSetPerson.currentIndex() == 0 or not self.cmbFilterActionExecSetPerson.value():
            self.chkFilterActionSNILSExecSetPerson.setEnabled(False)
        else:
            self.chkFilterActionSNILSExecSetPerson.setEnabled(True)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionSNILSExecSetPerson, checked & self.chkFilterActionSNILSExecSetPerson.isChecked())
        self.chkFilterActionSetOrgStructure.setChecked(False)
        self.chkFilterActionSetSpeciality.setChecked(False)

    @pyqtSignature('int')
    def on_cmbFilterActionExecSetPerson_currentIndexChanged(self):
        if self.cmbFilterActionExecSetPerson.currentIndex() == 0:
            self.chkFilterActionSNILSExecSetPerson.setEnabled(False)
        else:
            self.chkFilterActionSNILSExecSetPerson.setEnabled(True)
        if not self.chkFilterActionSNILSExecSetPerson.isEnabled():
            self.chkFilterActionSNILSExecSetPerson.setChecked(False)

    @pyqtSignature('bool')
    def on_chkFilterActionAssistant_toggled(self, checked):
        if checked:
            self.chkFilterActionId.setChecked(False)
            self.edtFilterActionId.setEnabled(False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionAssistant, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterActionFinance_toggled(self, checked):
        if checked:
            if not self.cmbFilterActionFinance.hasTable():
                self.cmbFilterActionFinance.setTable('rbFinance', addNone=True)
            self.chkFilterActionId.setChecked(False)
            self.edtFilterActionId.setEnabled(False)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterActionJobTicketId_toggled(self, checked):
        if checked:
            self.chkFilterActionId.setChecked(False)
            self.edtFilterActionId.setEnabled(False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionJobTicketId, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterActionPlannedEndDate_toggled(self, checked):
        if checked:
            self.chkFilterActionId.setChecked(False)
            self.edtFilterActionId.setEnabled(False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionPlannedEndDate, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterActionStatus_toggled(self, checked):
        if checked:
            self.chkFilterActionId.setChecked(False)
            self.edtFilterActionId.setEnabled(False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionStatus, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterActionOrg_toggled(self, checked):
        if checked:
            self.chkFilterActionId.setChecked(False)
            self.edtFilterActionId.setEnabled(False)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterActionBegDate_toggled(self, checked):
        if checked:
            self.chkFilterActionId.setChecked(False)
            self.edtFilterActionId.setEnabled(False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionBegDate, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterActionExecDate_toggled(self, checked):
        if checked:
            self.chkFilterActionId.setChecked(False)
            self.edtFilterActionId.setEnabled(False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionExecDate, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterActionCreatePerson_toggled(self, checked):
        if checked:
            self.chkFilterActionId.setChecked(False)
            self.edtFilterActionId.setEnabled(False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionCreatePerson, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterActionCreateDate_toggled(self, checked):
        if checked:
            self.chkFilterActionId.setChecked(False)
            self.edtFilterActionId.setEnabled(False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionCreateDate, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterActionModifyPerson_toggled(self, checked):
        if checked:
            self.chkFilterActionId.setChecked(False)
            self.edtFilterActionId.setEnabled(False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionModifyPerson, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterActionModifyDate_toggled(self, checked):
        if checked:
            self.chkFilterActionId.setChecked(False)
            self.edtFilterActionId.setEnabled(False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionModifyDate, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterActionPayStatus_toggled(self, checked):
        if checked:
            self.chkFilterActionId.setChecked(False)
            self.edtFilterActionId.setEnabled(False)
        self.setChildElementsVisible(self.chkListOnActionsPage, self.chkFilterActionPayStatus, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterActionTakenTissueJournal_toggled(self, checked):
        if checked:
            self.chkFilterActionId.setChecked(False)
            self.edtFilterActionId.setEnabled(False)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterActionId_toggled(self, checked):
        if checked:
            self.cmbFilterAction.setCurrentIndex(4)
            self.chkFilterActionType.setChecked(False)
            self.chkFilterActionServiceType.setChecked(False)
            self.chkFilterActionSetDate.setChecked(False)
            self.chkFilterActionSetOrgStructure.setChecked(False)
            self.chkFilterActionSetSpeciality.setChecked(False)
            self.chkFilterActionSetPerson.setChecked(False)
            self.chkFilterActionSNILSSetPerson.setChecked(False)
            self.chkFilterActionPlannedEndDate.setChecked(False)
            self.chkFilterActionStatus.setChecked(False)
            self.chkFilterActionOrg.setChecked(False)
            self.chkFilterActionExecDate.setChecked(False)
            self.chkFilterActionExecSetOrgStructure.setChecked(False)
            self.chkFilterActionExecSetSpeciality.setChecked(False)
            self.chkFilterActionExecSetPerson.setChecked(False)
            self.chkFilterActionSNILSExecSetPerson.setChecked(False)
            self.chkFilterActionAssistant.setChecked(False)
            self.chkFilterActionUncoordinated.setChecked(False)
            self.chkFilterActionJobTicketId.setChecked(False)
            self.chkFilterActionMKB.setChecked(False)
            self.chkFilterActionTakenTissueJournal.setChecked(False)
            self.chkFilterActionCreatePerson.setChecked(False)
            self.chkFilterActionCreateDate.setChecked(False)
            self.chkFilterActionModifyPerson.setChecked(False)
            self.chkFilterActionModifyDate.setChecked(False)
            self.chkTakeIntoAccountProperty.setChecked(False)
            self.chkFilledProperty.setChecked(False)
            self.chkThresholdPenaltyGrade.setChecked(False)
            self.chkFilterActionPayStatus.setChecked(False)
            self.chkFilterActionFinance.setChecked(False)
            self.chkFilterActionPayer.setChecked(False)
            self.chkFilterActionContract.setChecked(False)
            self.chkFilterActionExport.setChecked(False)
            self.chkFilterActionAttachedFiles.setChecked(False)
            self.chkFilterActionFileAttachId.setChecked(False)
            self.chkFilterActionExportSuitable.setChecked(False)
        self.onChkFilterToggled(self.chkFilterActionId, checked)


    @pyqtSignature('QAbstractButton*')
    def on_buttonBoxAction_clicked(self, button):
        buttonCode = self.buttonBoxAction.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.on_buttonBoxAction_apply()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_buttonBoxAction_reset()


#    @pyqtSignature('')
    def on_buttonBoxAction_reset(self):
        for s in self.chkListOnActionsPage:
            chk = s[0]
            if chk.isChecked():
                self.deactivateFilterWdgets(s[1])
                chk.setChecked(False)
        self.cmbFilterAction.setCurrentIndex(0)


#    @pyqtSignature('')
    def on_buttonBoxAction_apply(self):
        filter = {}
        if self.chkFilterActionType.isChecked():
            filter['actionTypeId'] = self.cmbFilterActionType.value()
        if self.chkFilterActionServiceType.isChecked():
            filter['actionTypeServiceType'] = self.cmbFilterActionServiceType.value()
        if self.chkFilterActionStatus.isChecked():
            filter['status'] = self.cmbFilterActionStatus.value()
        if self.chkFilterActionOrg.isChecked():
            filter['orgId'] = self.cmbFilterActionOrg.value()
        if self.chkFilterActionSetDate.isChecked():
            filter['begSetDate'] = self.edtFilterActionBegSetDate.date()
            filter['endSetDate'] = self.edtFilterActionEndSetDate.date()
        if self.chkFilterActionSetSpeciality.isChecked():
            filter['setSpecialityId'] = self.cmbFilterActionSetSpeciality.value()
        if self.chkFilterActionSetOrgStructure.isChecked():
            filter['actionSetOrgStructureId'] = self.cmbFilterActionSetOrgStructure.value()
        if self.chkFilterActionExecSetOrgStructure.isChecked():
            filter['execSetOrgStructureId'] = self.cmbFilterActionExecSetOrgStructure.value()
        if self.chkFilterActionSetPerson.isChecked():
            filter['setPersonId'] = self.cmbFilterActionSetPerson.value()
            if self.chkFilterActionSNILSSetPerson.isChecked() and self.chkFilterActionSNILSSetPerson.isEnabled():
                filter['setPersonSNILS'] = True
        if self.chkFilterActionExecSetSpeciality.isChecked():
            filter['execSpecialityId'] = self.cmbFilterActionExecSetSpeciality.value()
        if self.chkFilterActionExecSetPerson.isChecked():
            filter['execPersonId'] = self.cmbFilterActionExecSetPerson.value()
            if self.chkFilterActionSNILSExecSetPerson.isChecked() and self.chkFilterActionSNILSExecSetPerson.isEnabled():
                filter['execPersonSNILS'] = True
        if self.chkFilterActionAssistant.isChecked():
            filter['assistantId'] = self.cmbFilterActionAssistant.value()
        if self.chkFilterActionFinance.isChecked():
            filter['financeId'] = self.cmbFilterActionFinance.value()
        if self.chkFilterActionPayer.isChecked():
            filter['payerId'] = self.cmbFilterActionPayer.value()
        if self.chkFilterActionContract.isChecked():
            filter['contractId'] = self.__filterActionContractId
        if self.chkFilterActionExport.isChecked():
            filter['actionExportStatus'] = self.cmbFilterActionExportStatus.currentIndex()
            filter['actionExportSystem'] = self.cmbFilterActionExportSystem.value()

        if self.chkFilterActionUncoordinated.isChecked():
            filter['uncoordinated'] = self.chkFilterActionUncoordinated.isChecked()
        if self.chkFilterActionMKB.isChecked():
            filter['actionMKB'] = self.chkFilterActionMKB.isChecked()
            filter['actionMKBFrom'] = MKBwithoutSubclassification(unicode(self.edtFilterActionMKBFrom.text()))
            filter['actionMKBTo'] = MKBwithoutSubclassification(unicode(self.edtFilterActionMKBTo.text()))
        if self.chkFilterActionJobTicketId.isChecked():
            tmp = forceStringEx(self.edtFilterActionJobTicketId.text())
            if tmp:
                filter['actionJobTicketId'] = int(tmp)
        if self.chkFilterActionIsUrgent.isChecked():
            filter['isUrgent'] = True
        if self.chkFilterActionPlannedEndDate.isChecked():
            filter['begPlannedEndDate'] = self.edtFilterActionBegPlannedEndDate.date()
            filter['endPlannedEndDate'] = self.edtFilterActionEndPlannedEndDate.date()
        if self.chkFilterActionBegDate.isChecked():
            filter['begBegDateTime'] = QDateTime(self.edtFilterActionBegBegDate.date(), self.edtFilterActionBegBegTime.time())
            filter['endBegDateTime'] = QDateTime(self.edtFilterActionEndBegDate.date(), self.edtFilterActionEndBegTime.time())
        if self.chkFilterActionExecDate.isChecked():
            filter['begExecDateTime'] = QDateTime(self.edtFilterActionBegExecDate.date(), self.edtFilterActionBegExecTime.time())
            filter['endExecDateTime'] = QDateTime(self.edtFilterActionEndExecDate.date(), self.edtFilterActionEndExecTime.time())
        if self.chkFilterActionId.isChecked():
            tmp = forceStringEx(self.edtFilterActionId.text())
            if tmp:
                filter['actionId'] = int(tmp)
        if self.chkFilterActionCreatePerson.isChecked():
            filter['createPersonId'] = self.cmbFilterActionCreatePerson.value()
        if self.chkFilterActionCreateDate.isChecked():
            filter['begCreateDate'] = self.edtFilterActionBegCreateDate.date()
            filter['endCreateDate'] = self.edtFilterActionEndCreateDate.date()
        if self.chkFilterActionModifyPerson.isChecked():
            filter['modifyPersonId'] = self.cmbFilterActionModifyPerson.value()
        if self.chkFilterActionModifyDate.isChecked():
            filter['begModifyDate'] = self.edtFilterActionBegModifyDate.date()
            filter['endModifyDate'] = self.edtFilterActionEndModifyDate.date()
        if self.chkFilterActionPayStatus.isChecked():
            filter['payStatusCode'] = self.cmpFilterActionPayStatusCode.currentIndex()
            index = self.cmbFilterActionPayStatusFinance.currentIndex()
            if not 0<=index<5:
                index = 0
            filter['payStatusFinanceCode'] = 5-index
        if self.chkFilterActionTakenTissueJournal.isChecked():
            filter['takenTissueJournal'] = self.cmbFilterActionTakenTissueJournal.currentIndex() == 0
        actionsFilterType = self.cmbFilterAction.currentIndex()
        if actionsFilterType == 0:
            filter['clientIds'] = [ self.selectedClientId() ]
        elif actionsFilterType == 1:
            filter['clientIds'] = self.modelClients.idList()
        elif actionsFilterType == 2:
            filter['eventIds'] = [ self.tblEvents.currentItemId() ]
        elif actionsFilterType == 3:
            filter['eventIds'] = self.modelEvents.idList()
        filter['actionsFilterType']=actionsFilterType
        filter['booleanFilledProperty'] = self.chkFilledProperty.isChecked() #True = заполнено; False = не заполнено
        if self.chkFilledProperty.isChecked() and self.chkFilledProperty.isEnabled():
            filter['listPropertyCond'] = self.cmbListPropertyCond.currentIndex()
            filter['indexFilledProperty'] = self.cmbFilledProperty.currentIndex()
        if self.chkThresholdPenaltyGrade.isChecked():
            filter['thresholdPenaltyGrade'] = self.edtThresholdPenaltyGrade.text()
        if self.chkFilterActionAttachedFiles.isChecked():
            filter['attachedFile'] = self.cmbFilterActionAttachedFiles.currentIndex()
            if self.cmbFilterActionTypeDoc.isEnabled():
                filter['typeDoc'] = forceString(self.cmbFilterActionTypeDoc.currentText())
            if self.cmbFilterActionSigned.isEnabled():
                filter['signed'] = self.cmbFilterActionSigned.currentIndex()
            if self.chkFilterActionFileAttachId.isChecked():
                filter['ActionFileAttach_id'] = forceInt(self.edtFilterActionFileAttachId.text())
            if self.chkFilterActionExportSuitable.isChecked():
                filter['exportSuitable'] = True
        self.updateActionsList(filter)
        self.focusEvents()


### Expert page ##################################

    @pyqtSignature('')
    def on_actExpertEditClient_triggered(self):
        clientId = self.currentClientId()
        if clientId:
            self.editClient(clientId)
            if self.getCurrentExpertTypesTabWidgetDetails().currentIndex():
                self.updateDocumentsExInfo(self.getCurrentTempDocumentsExTable().currentItemId(), noPrev=True)
            else:
                self.updateTempInvalidInfo(self.getCurrentExpertTable().currentItemId(), noPrev=True)
            self.updateClientsListRequest = True


#    def setBtnExpertEditEnabled(self):
#        tableList = [self.tblExpertTempInvalid, self.tblExpertDisability, self.tblExpertVitalRestriction, self.getCurrentExpertMedicalCommissionTable()]
#        self.btnExpertEdit.setEnabled(getRightEditTempInvalid(tableList[self.tabWidgetTempInvalidTypes.currentIndex()].currentItemId()))


    @pyqtSignature('int')
    def on_tabExpertMedicalCommissionWidget_currentChanged(self, index):
        isExpertMedicalSocialInspection = self.tabExpertMedicalCommissionWidget.currentIndex() == self.tabExpertMedicalCommissionWidget.indexOf(self.tabExpertMedicalSocialInspection)
        self.chkFilterExpertExportedToExternalISMC.setEnabled(isExpertMedicalSocialInspection)
        self.cmbFilterExpertExportedTypeMC.setEnabled(isExpertMedicalSocialInspection and self.chkFilterExpertExportedToExternalISMC.isChecked())
        self.cmbFilterExpertIntegratedISMC.setEnabled(isExpertMedicalSocialInspection and self.chkFilterExpertExportedToExternalISMC.isChecked())
        self.on_buttonBoxExpertMC_apply()
        self.setBtnExpertEnabled()


    def setBtnExpertEnabled(self):
        rightEditExpertMC = QtGui.qApp.userHasRight(urRegTabEditExpertMC)
        enable = rightEditExpertMC and bool(len(self.getCurrentExpertMedicalCommissionTable().model().idList()) > 0)
        self.btnExpertEdit.setEnabled(enable)
        self.btnExpertPrint.setEnabled(enable)
        self.btnExpertFilter.setEnabled(enable)
        self.btnExpertNew.setEnabled(enable)


    def visibleFilterExpertExportFSS(self):
        visibleDocuments = self.tabWidgetTempInvalidTypes.currentIndex() in [self.tabWidgetTempInvalidTypes.indexOf(self.tabExpertTempInvalidDetalsWidget),
                                                                             self.tabWidgetTempInvalidTypes.indexOf(self.tabExpertDisabilityDetailsWidget),
                                                                             self.tabWidgetTempInvalidTypes.indexOf(self.tabExpertVitalRestrictionDetailsWidget)]
        if visibleDocuments:
            tabExpertTempInvalid = self.getCurrentExpertTypesTabWidgetDetails()
            visibleDocuments = tabExpertTempInvalid.currentIndex() in [tabExpertTempInvalid.indexOf(self.tabExpertTempInvalidDocuments),
                                                                       tabExpertTempInvalid.indexOf(self.tabExpertDisabilityDocumentsEx),
                                                                       tabExpertTempInvalid.indexOf(self.tabExpertVitalRestrictionDocumentsEx)]
        self.chkFilterExpertExportFSS.setVisible(visibleDocuments)
        self.cmbFilterExpertExportFSS.setVisible(visibleDocuments)


    @pyqtSignature('int')
    def on_tabExpertTempInvalidDetals_currentChanged(self, index):
        self.visibleFilterExpertExportFSS()


    @pyqtSignature('int')
    def on_tabExpertDisabilityDetails_currentChanged(self, index):
        self.visibleFilterExpertExportFSS()


    @pyqtSignature('int')
    def on_tabExpertVitalRestrictionDetails_currentChanged(self, index):
        self.visibleFilterExpertExportFSS()


    @pyqtSignature('int')
    def on_tabWidgetTempInvalidTypes_currentChanged(self, index):
        self.visibleFilterExpertExportFSS()
        if index == self.tabWidgetTempInvalidTypes.indexOf(self.tabExpertMedicalCommission):
            self.stwExpertFilter.setCurrentWidget(self.tabMedicalCommissionExpertFilter)
            if not self.cmbFilterExpertSpecialityMC.hasTable():
                self.cmbFilterExpertSpecialityMC.setTable('rbSpeciality', True)
            if not self.cmbFilterExpertIntegratedISMC.hasTable():
                self.cmbFilterExpertIntegratedISMC.setTable('rbExternalSystem', True)
            self.on_buttonBoxExpertMC_apply()
            self.setBtnExpertEnabled()
        else:
            self.stwExpertFilter.setCurrentWidget(self.tabTempInvalidExpertFilter)
            filter = 'type=%d'%index
            self.cmbFilterExpertDocType.setTable('rbTempInvalidDocument', False, filter)
            self.cmbFilterExpertReason.setTable('rbTempInvalidReason', False, filter)
            self.cmbFilterExpertResult.setTable('rbTempInvalidResult', False, filter)
            self.cmbFilterExpertSpeciality.setTable('rbSpeciality', True)
            self.cmbFilterExpertDocType.setValue(self.__tempInvalidDocTypeIdListByTypePage[index])
            self.on_buttonBoxExpert_apply()
            self.setBtnExpertEditEnabled()
            self.btnExpertPrint.setEnabled(True)
            self.btnExpertFilter.setEnabled(True)
            self.btnExpertNew.setEnabled(True)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelExpertTempInvalid_currentRowChanged(self, current, previous):
        tempInvalidId = self.tblExpertTempInvalid.currentItemId()
        self.updateTempInvalidInfo(tempInvalidId, noPrev=True)
        self.setBtnExpertEditEnabled()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelExpertTempInvalidRelation_currentRowChanged(self, current, previous):
        tempInvalidId = self.tblExpertTempInvalidRelation.currentItemId()
        self.updateTempInvalidInfo(tempInvalidId)
        self.setBtnExpertEditEnabled()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelExpertTempInvalidDocumentsEx_currentRowChanged(self, current, previous):
        self.updateDocumentsExInfo(self.tblExpertTempInvalidDocumentsEx.currentItemId(), noPrev=True)
        self.setBtnExpertEditEnabled()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelExpertDisabilityDocumentsEx_currentRowChanged(self, current, previous):
        self.updateDocumentsExInfo(self.tblExpertDisabilityDocumentsEx.currentItemId(), noPrev=True)
        self.setBtnExpertEditEnabled()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelExpertVitalRestrictionDocumentsEx_currentRowChanged(self, current, previous):
        self.updateDocumentsExInfo(self.tblExpertVitalRestrictionDocumentsEx.currentItemId(), noPrev=True)
        self.setBtnExpertEditEnabled()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelExpertTempInvalidRelationDocumentsEx_currentRowChanged(self, current, previous):
        self.updateDocumentsExInfo(self.tblExpertTempInvalidRelationDocumentsEx.currentItemId())
        self.setBtnExpertEditEnabled()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelExpertDisabilityRelationDocumentsEx_currentRowChanged(self, current, previous):
        self.updateDocumentsExInfo(self.tblExpertDisabilityRelationDocumentsEx.currentItemId())
        self.setBtnExpertEditEnabled()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelExpertVitalRestrictionRelationDocumentsEx_currentRowChanged(self, current, previous):
        self.updateDocumentsExInfo(self.tblExpertVitalRestrictionRelationDocumentsEx.currentItemId())
        self.setBtnExpertEditEnabled()


    def getCurrentDocumentsTempInvalid(self):
        index = self.tabWidgetTempInvalidTypes.currentIndex()
        if index < 3:
            return [self.edtExpertDocumentsTempInvalid, self.edtExpertDisabilityDocumentsTempInvalid, self.edtExpertVitalRestrictionDocumentsTempInvalid][index]
        else:
            return None


    def updateDocumentsExInfo(self, documentId, noPrev=False):
        currentTable = self.getCurrentDocumentsTempInvalid()
        if currentTable:
            isFilterExpertLinked = self.chkFilterExpertLinked.isChecked()
            if documentId:
                db = QtGui.qApp.db
                tableTempInvalidDocument = db.table('TempInvalidDocument')
                tablePeriod = db.table('TempInvalid_Period')
                record = db.getRecordEx(tableTempInvalidDocument, [tableTempInvalidDocument['master_id']],
                                        [tableTempInvalidDocument['id'].eq(documentId),
                                         tableTempInvalidDocument['deleted'].eq(0)],
                                        tableTempInvalidDocument['idx'].name())
                tempInvalidId = forceRef(record.value('master_id')) if record else None
                currentTable.loadData(tempInvalidId, documentId)
                self.setClientInfoBrowserExpert(tempInvalidId)
                if tempInvalidId:
                    idList = db.getDistinctIdList(tablePeriod, 'id', tablePeriod['master_id'].eq(tempInvalidId),
                                                  'endDate')
                else:
                    idList = []
                self.getCurrentTempDocumentsExPeriodsTable().setIdList(idList)
                if isFilterExpertLinked:
                    if noPrev:
                        prevIdList = [documentId]
                        prevIdSet = set([documentId])
                        while prevIdList:
                            childrenIdSet = set(db.getDistinctIdList(tableTempInvalidDocument, ['id'], [
                                tableTempInvalidDocument['prev_id'].inlist(prevIdList),
                                tableTempInvalidDocument['deleted'].eq(0)], tableTempInvalidDocument['idx'].name()))
                            newIdSet = childrenIdSet - prevIdSet
                            prevIdSet |= newIdSet
                            prevIdList = list(newIdSet)
                        documentRelationIdList = list(prevIdSet - set([documentId]))
                        self.getCurrentExpertRelationDocumentsExTable().setIdList(documentRelationIdList)
            else:
                self.getCurrentTempDocumentsExPeriodsTable().setIdList([])
                currentTable.loadData(None, None)
                if isFilterExpertLinked and noPrev:
                    self.getCurrentExpertRelationDocumentsExTable().setIdList([])


    def setClientInfoBrowserExpert(self, tempInvalidId):
        clientId = None
        if tempInvalidId:
            db = QtGui.qApp.db
            tableTempInvalid = db.table('TempInvalid')
            record = db.getRecordEx(tableTempInvalid, [tableTempInvalid['client_id']], [tableTempInvalid['id'].eq(tempInvalidId), tableTempInvalid['deleted'].eq(0)])
            clientId = forceRef(record.value('client_id')) if record else None
        if not clientId:
            clientId = self.selectedClientId()
        self.updateClientInfo(clientId)
        self.actCheckClientAttach.setEnabled(bool(clientId))
        self.actPortal_Doctor.setEnabled(bool(clientId))
        self.actExpertEditClient.setEnabled(bool(clientId))
        self.actExpertRelationsClient.setEnabled(bool(clientId))
        QtGui.qApp.setCurrentClientId(clientId)


    @pyqtSignature('')
    def on_tblExpertDirectionsMC_popupMenuAboutToShow(self):
        self.expertMC_popupMenuAboutToShow(self.tblExpertDirectionsMC)


    @pyqtSignature('')
    def on_tblExpertProtocolsMC_popupMenuAboutToShow(self):
        self.expertMC_popupMenuAboutToShow(self.tblExpertProtocolsMC)


    @pyqtSignature('')
    def on_ExpertMedicalSocialInspection_popupMenuAboutToShow(self):
        self.expertMC_popupMenuAboutToShow(self.ExpertMedicalSocialinspection)


    def expertMC_popupMenuAboutToShow(self, table):
        currentId = table.currentItemId()
        userRight = QtGui.qApp.userHasRight(urRegTabEditExpertMC)
        prevActionId = self.getPrevActionIdMSI(currentId)
        action = CAction.getActionById(currentId) if currentId else None
        actionType = action.getType() if action else None
        record = action.getRecord() if action else None
        numberDisabilityFill = True
        if actionType and u'Номер ЛН' in actionType._propertiesByName and action[u'Номер ЛН'] and u'#' in action[u'Номер ЛН']:
            numberDisabilityFill = False
        eventId = (forceRef(record.value('event_id')) if record else False)
        isTempInvalidId = (bool(self.getTempInvalidId(eventId)) if eventId else False)
        self.actExpertMedicalCommissionDelete.setEnabled(bool(currentId) and userRight and (not prevActionId))
        self.actExpertMedicalCommissionSelected.setEnabled(bool(currentId) and userRight)
        self.actExpertMedicalCommissionUpdateGroup.setEnabled(bool(currentId) and userRight and len(self.getCurrentExpertMedicalCommissionTable().selectedItemIdList()) > 1 and len(self.medicalCommissionSelectedRows) > 0)
        self.actExpertMedicalCommissionClear.setEnabled(bool(currentId) and userRight)
        self.actExpertMedicalCommissionUpdate.setEnabled(bool(currentId) and userRight)
        self.actExpertMCUpdateTempInvalid.setEnabled(bool(currentId) and userRight and isTempInvalidId)
        self.actExpertMedicalCommissionMSI.setEnabled(bool(currentId) and userRight and (not prevActionId) and numberDisabilityFill)
        self.actEditExpertMCEvent.setEnabled(bool(currentId) and QtGui.qApp.userHasRight(urRegTabWriteActions) and eventId and not isTempInvalidId)


    def getPrevActionIdMSI(self, currentId):
        prevActionId = None
        if currentId:
            db = QtGui.qApp.db
            tableAction = db.table('Action')
            record = db.getRecordEx(tableAction, [tableAction['id']], [tableAction['prevAction_id'].eq(currentId), tableAction['deleted'].eq(0)])
            prevActionId = forceRef(record.value('id')) if record else None
        return prevActionId


    def getTempInvalidId(self, eventId):
        if eventId:
            db = QtGui.qApp.db
            tableEvent = db.table('Event')
            record = db.getRecordEx(tableEvent, [tableEvent['tempInvalid_id']], [tableEvent['id'].eq(eventId), tableEvent['deleted'].eq(0)])
            return forceRef(record.value('tempInvalid_id')) if record else None
        return None


    @pyqtSignature('')
    def on_tblExpertTempInvalid_popupMenuAboutToShow(self):
#        tempInvalidId = self.tblExpertTempInvalid.currentItemId()
        prevId = self.getExpertPrevDocId(self.tblExpertTempInvalid)
        nextId = self.getExpertNextDocId(self.tblExpertTempInvalid)
        state = self.getExpertState(self.tblExpertTempInvalid)
        self.actExpertTempInvalidChangeToOpen.setEnabled(state == 2)
        self.actExpertTempInvalidNext.setEnabled(bool(nextId))
        self.actExpertTempInvalidPrev.setEnabled(bool(prevId))
        # self.actExpertTempInvalidConcurrently.setEnabled(self.isEnabledExpertConcurrently(self.tblExpertTempInvalid))


    @pyqtSignature('')
    def on_tblExpertDisability_popupMenuAboutToShow(self):
        tempInvalidId = self.tblExpertDisability.currentItemId()
        prevId = self.getExpertPrevDocId(self.tblExpertDisability)
        nextId = self.getExpertNextDocId(self.tblExpertDisability)
        self.actExpertDisabilityNext.setEnabled(bool(nextId))
        self.actExpertDisabilityPrev.setEnabled(bool(prevId))
#        app = QtGui.qApp
        self.actExpertDisabilityDelete.setEnabled(bool(tempInvalidId) and getRightEditTempInvalid(tempInvalidId))


    @pyqtSignature('')
    def on_tblExpertVitalRestriction_popupMenuAboutToShow(self):
        tempInvalidId = self.tblExpertVitalRestriction.currentItemId()
        prevId = self.getExpertPrevDocId(self.tblExpertVitalRestriction)
        nextId = self.getExpertNextDocId(self.tblExpertVitalRestriction)
        self.actExpertVitalRestrictionNext.setEnabled(bool(nextId))
        self.actExpertVitalRestrictionPrev.setEnabled(bool(prevId))
#        app = QtGui.qApp
        self.actExpertVitalRestrictionDelete.setEnabled(bool(tempInvalidId) and getRightEditTempInvalid(tempInvalidId))


    @pyqtSignature('')
    def on_actExpertTempInvalidChangeToOpen_triggered(self):
        tempInvalidId = self.tblExpertTempInvalid.currentItemId()
        if tempInvalidId:
            db = QtGui.qApp.db
            tableInvalidDocument = db.table('TempInvalidDocument')
            record = db.getRecordEx(tableInvalidDocument, 
                                    [tableInvalidDocument['last_id'], tableInvalidDocument['isExternal']], 
                                    [tableInvalidDocument['deleted'].eq(0), 
                                     tableInvalidDocument['master_id'].eq(tempInvalidId)], 
                                    'id desc')
            lastId = forceInt(record.value('last_id'))
            isExternal = forceBool(record.value('isExternal'))
            if lastId == 0 and not isExternal:
                res = QtGui.QMessageBox.warning(self,
                            u'Внимание!',
                            u'Изменить состояние с Продлен на Открыт?',
                            QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel,
                            QtGui.QMessageBox.Cancel)
                if res == QtGui.QMessageBox.Ok:
                    model = self.tblExpertTempInvalid.model()
                    currentItem = model.recordCache().get(tempInvalidId)
                    currentItem.setValue('state', 0)
                    tableInvalid = db.table('TempInvalid')
                    db.updateRecord(tableInvalid, currentItem)
            else:
                QtGui.QMessageBox().information(self, u'Предупреждение!',
                                                    u'Статус не может быть изменен, элн имеет продолжение.',
                                                    QtGui.QMessageBox.Ok,
                                                    QtGui.QMessageBox.Ok)
    
    
    @pyqtSignature('')
    def on_actExpertTempInvalidNext_triggered(self):
        self.onExpertDocNext(self.tblExpertTempInvalid)


    @pyqtSignature('')
    def on_actExpertDisabilityNext_triggered(self):
        self.onExpertDocNext(self.tblExpertDisability)


    @pyqtSignature('')
    def on_actExpertVitalRestrictionNext_triggered(self):
        self.onExpertDocNext(self.tblExpertVitalRestriction)


    def onExpertDocNext(self, table):
        nextId = self.getExpertNextDocId(table)
        if nextId:
            row = table.model().findItemIdIndex(nextId)
            if row>=0:
                table.setCurrentRow(row)
            else:
                QtGui.QMessageBox.information(self, u'Переход к следующему документу', u'Переход невозможен - необходимо изменить фильтр')


    @pyqtSignature('')
    def on_tblClients_popupMenuAboutToShow(self):
        QtGui.qApp = QtGui.qApp
        clientPresent = bool(self.currentClientId())
        self.actCreateEvent.setEnabled(clientPresent)
        self.actShowContingentsClient.setEnabled(clientPresent)
        self.actCheckClientAttach.setEnabled(clientPresent)
        self.actPortal_Doctor.setEnabled(clientPresent)
        self.actOpenClientVaccinationCard.setEnabled(clientPresent and QtGui.qApp.userHasAnyRight([urCanReadClientVaccination, urCanEditClientVaccination]))
        self.actListVisitsBySchedules.setEnabled(clientPresent)
        self.actBatchRegLocatCard.setEnabled(QtGui.qApp.userHasAnyRight([urBatchRegLocatCardProcess]))
        self.actaClients.setEnabled(clientPresent)
        self.actaddClients.setEnabled(clientPresent)
        self.actStatusObservationClient.setEnabled(clientPresent)
        self.actControlDoublesRecordClient.setEnabled(clientPresent and QtGui.qApp.userHasRight(urRegControlDoubles))
        self.actControlDoublesRecordClientList.setEnabled(clientPresent and QtGui.qApp.userHasRight(urRegControlDoubles) and len(self.modelClients.idList()) > 0)
        self.actReservedOrderQueueClient.setEnabled(bool(QtGui.qApp.mainWindow.dockFreeQueue and QtGui.qApp.mainWindow.dockFreeQueue.content and QtGui.qApp.mainWindow.dockFreeQueue.content.locked()))



    @pyqtSignature('')
    def on_tblSchedules_popupMenuAboutToShow(self):
        notEmpty = self.modelSchedules.rowCount() > 0
        self.actAmbCreateEvent.setEnabled(notEmpty and QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteEvents]))
        self.actAmbDeleteOrder.setEnabled(notEmpty)
        self.actAmbChangeNotes.setEnabled(notEmpty)
        index = self.tblSchedules.currentIndex()
        ambOrderPrint = 1
        if index.isValid():
            row = index.row()
            item = self.modelSchedules.items()[row]
            scheduleItemId = forceRef(item.value('id'))
            db = QtGui.qApp.db
            record = db.getRecord('vScheduleItem', '*', scheduleItemId)
            ambOrderPrint = forceInt(record.value('appointmentType')) 
        self.actAmbPrintOrder.setEnabled(notEmpty and ambOrderPrint != CSchedule.atHome)
        self.actAmbHomePrintOrder.setEnabled(notEmpty and ambOrderPrint == CSchedule.atHome)
        self.actPrintBeforeRecords.setEnabled(notEmpty)
        self.actShowPreRecordInfo.setEnabled(notEmpty)



    @pyqtSignature('')
    def on_tblVisitsBySchedules_popupMenuAboutToShow(self):
        notEmpty = self.modelVisitsBySchedules.rowCount() > 0
        self.actShowPreRecordInfoVisitBySchedule.setEnabled(notEmpty)



    @pyqtSignature('')
    def on_tblCanceledSchedules_popupMenuAboutToShow(self):
        notEmpty = self.modelCanceledSchedules.rowCount() > 0
        self.actShowPreRecordInfoCanceledSchedules.setEnabled(notEmpty)


    @pyqtSignature('')
    def on_tblEvents_popupMenuAboutToShow(self):
        self.actOpenAccountingByEvent.setEnabled(self.modelEvents.rowCount()>0)
        self.actGroupJobAppointment.setEnabled(self.modelEvents.rowCount()>0)
        eventId = self.tblEvents.currentItemId()
        self.actMakePersonalAccount.setEnabled(self.modelEvents.canMakePersonalAccount(eventId))
        self.actUpdateEventTypeByEvent.setEnabled(self.modelEvents.rowCount()>0 and QtGui.qApp.userHasAnyRight([urUpdateEventTypeByEvent]))
        self.actStatusObservationClientByEvent.setEnabled(self.modelEvents.rowCount()>0 and QtGui.qApp.userHasAnyRight([urAdmin, urEditStatusObservationClient]))
        self.actAddActionEvent.setEnabled(self.modelEvents.rowCount()>0)
        self.actJobTicketsEvent.setEnabled(self.modelEvents.rowCount()>0)
        self.actCreateRelatedAction.setEnabled(bool(self.currentClientId()))
        selected = self.tblEvents.selectionModel().selectedRows()
        clientId =  self.currentClientId()
        if not selected or len(selected) > 1:
            self.actSurveillancePlanningClientsByEvent.setEnabled(False)
        elif eventId:
                self.actSurveillancePlanningClientsByEvent.setEnabled(bool(isSurveillanceActive(clientId, {'event_id': eventId}, {'begDate': QDate.currentDate(), 'event_id': eventId})))
        # self.actSendEventFPUMP.setEnabled(forceString(QtGui.qApp.getGlobalPreference('useServiceGISOMS')) == u'да')


    @pyqtSignature('')
    def on_tblEventActions_popupMenuAboutToShow(self):
        self.actOpenAccountingByAction.setEnabled(self.modelEventActions.rowCount()>0)



    @pyqtSignature('')
    def on_tblEventVisits_popupMenuAboutToShow(self):
        self.actOpenAccountingByVisit.setEnabled(self.modelEventVisits.rowCount()>0)


    @pyqtSignature('')
    def on_actAmbCreateEvent_triggered(self):
        index = self.tblSchedules.currentIndex()
        if index.isValid():
            row = index.row()
            record = self.modelSchedules.items()[row]
            params = {}
            params['widget'] = self
            params['clientId'] = self.currentClientId()
            params['flagHospitalization'] = False
            params['actionTypeId'] = None
            params['valueProperties'] = []
            params['eventTypeFilterHospitalization'] = 0
            params['dateTime'] = forceDateTime(record.value('directionDate'))
            params['personId'] = forceRef(record.value('person_id'))
            requestNewEvent(params)


    @pyqtSignature('')
    def on_actAmbDeleteOrder_triggered(self):
        index = self.tblSchedules.currentIndex()
        if index.isValid():
            row = index.row()
            record = self.modelSchedules.items()[row]
            scheduleItemId = forceRef(record.value('id'))
            recordPersonId = forceRef(record.value('recordPerson_id'))
            clientId = self.currentClientId()
            confirmAndFreeScheduleItem(self, scheduleItemId, recordPersonId, clientId)
            self.updateQueue()
            if QtGui.qApp.mainWindow.dockResources:
                QtGui.qApp.mainWindow.dockResources.content.updateTimeTable()
            QtGui.qApp.emitCurrentClientInfoJLWDeleted(scheduleItemId)


    @pyqtSignature('')
    def on_actAmbChangeNotes_triggered(self):
        index = self.tblSchedules.currentIndex()
        if index.isValid():
            row = index.row()
            item = self.modelSchedules.items()[row]
            scheduleItemId = forceRef(item.value('id'))
            dlg = CComplaintsEditDialog(self)
            dlg.setComplaints(forceString(item.value('complaint')))
            if dlg.exec_():
                db = QtGui.qApp.db
                table = db.table('Schedule_Item')
                record = table.newRecord(['id', 'complaint'])
                record.setValue('id', toVariant(scheduleItemId))
                record.setValue('complaint', toVariant(dlg.getComplaints()))
                db.updateRecord(table, record)
#                self.modelSchedules.setValue(row, 'complaint', record.value('complaint'))
            self.updateQueue()
            if QtGui.qApp.mainWindow.dockResources:
                QtGui.qApp.mainWindow.dockResources.content.updateTimeTable()


    @pyqtSignature('')
    def on_actAmbPrintOrder_clicked(self, templateId = None):
        index = self.tblSchedules.currentIndex()
        if index.isValid():
            row = index.row()
            item = self.modelSchedules.items()[row]
            scheduleItemId = forceRef(item.value('id'))
            printOrderByScheduleItem(self, scheduleItemId, self.currentClientId(), templateId)
    
    @pyqtSignature('int')
    def on_actAmbPrintOrder_printByTemplate(self, templateId):
        self.on_actAmbPrintOrder_clicked(templateId)
    
    
    @pyqtSignature('int')
    def on_actAmbHomePrintOrder_printByTemplate(self, templateId):
        self.on_actAmbPrintOrder_clicked(templateId)


    @pyqtSignature('')
    def on_actPrintBeforeRecords_triggered(self):
        if self.modelSchedules.rowCount():
            self.tblSchedules.setReportHeader(u'Протокол предварительной записи пациента')
            self.tblSchedules.setReportDescription(self.txtClientInfoBrowser.toHtml())
            mask = [False]
            for i in range(1, self.tblSchedules.model().columnCount()): mask.append(True)
            self.tblSchedules.printContent(mask)


    @pyqtSignature('')
    def on_actShowPreRecordInfo_triggered(self):
        row = self.tblSchedules.currentRow()
        if 0<=row<self.modelSchedules.rowCount():
            scheduleItemId = self.modelSchedules.getScheduleItemId(row)
            showScheduleItemInfo(scheduleItemId, self)


    @pyqtSignature('')
    def on_actShowPreRecordInfoCanceledSchedules_triggered(self):
        row = self.tblCanceledSchedules.currentRow()
        if 0<=row<self.modelCanceledSchedules.rowCount():
            scheduleItemId = self.modelCanceledSchedules.getScheduleItemId(row)
            showScheduleItemInfo(scheduleItemId, self)


    @pyqtSignature('')
    def on_actShowPreRecordInfoVisitBySchedule_triggered(self):
        row = self.tblVisitsBySchedules.currentRow()
        if 0<=row<self.modelVisitsBySchedules.rowCount():
            scheduleItemId = self.modelVisitsBySchedules.getScheduleItemId(row)
            showScheduleItemInfo(scheduleItemId, self)


    @pyqtSignature('')
    def on_actControlDoublesRecordClient_triggered(self):
         clientId = self.currentClientId()
         if clientId:
            CRegistryControlDoubles(self, clientId).exec_()
            self.on_buttonBoxClient_apply()


    @pyqtSignature('')
    def on_actControlDoublesRecordClientList_triggered(self):
         clientIdList = self.modelClients.idList()
         if clientIdList:
            CRegistryClientListControlDoubles(self, clientIdList).exec_()
            self.on_buttonBoxClient_apply()


    @pyqtSignature('')
    def on_actReservedOrderQueueClient_triggered(self):
        dockFreeQueue = QtGui.qApp.mainWindow.dockFreeQueue
        if dockFreeQueue and dockFreeQueue.content and dockFreeQueue.content.locked():
            dockFreeQueue.content.on_actAmbCreateOrder_triggered()


    @pyqtSignature('')
    def on_actOpenClientVaccinationCard_triggered(self):
        clientId = self.currentClientId()
        openClientVaccinationCard(self, clientId)



    @pyqtSignature('')
    def on_actListVisitsBySchedules_triggered(self):
        if QtGui.qApp.mainWindow.dockResources.content:
            personId = QtGui.qApp.mainWindow.dockResources.content.getCurrentPersonId()
        else:
            personId = None

        if personId:
            orgStructureId, specialityId = None, None
        else:
            orgStructureId = QtGui.qApp.currentOrgStructureId
            specialityId = QtGui.qApp.userSpecialityId

        clientId = self.currentClientId()
        CVisitsBySchedulesDialog(self, clientId, orgStructureId, specialityId, personId).exec_()


    def batchRegLocatCardReset(self):
        prefs = getPref(QtGui.qApp.preferences.reportPrefs, 'BatchRegLocatCardParams', {})
        batchRegLocatCardProcess = getPrefBool(prefs, 'BatchRegLocatCardProcess', False)
        if batchRegLocatCardProcess:
            dialog = CSetParamsBatchRegistrationLocationCard(self)
            try:
                dialog.getFontInfoLabel()
                self.lblClientsCount.setText('')
                dialog.saveParams(not batchRegLocatCardProcess)
                self.on_buttonBoxClient_reset()
                self.on_buttonBoxClient_apply()
            finally:
                dialog.deleteLater()


    @pyqtSignature('')
    def on_actBatchRegLocatCard_triggered(self):
        try:
            if QtGui.qApp.userHasAnyRight([urBatchRegLocatCardProcess]):
                dialog = CSetParamsBatchRegistrationLocationCard(self)
                try:
                    if dialog.exec_():
                        pass
                finally:
                    prefs = getPref(QtGui.qApp.preferences.reportPrefs, self.preferences, {})
                    batchRegLocatCardProcess = getPrefBool(prefs, 'BatchRegLocatCardProcess', False)
                    if batchRegLocatCardProcess:
                        dialog.getFontInfoLabel()
                        self.lblClientsCount.setText('')
                        dialog.saveParams(not batchRegLocatCardProcess)
                        self.on_buttonBoxClient_reset()
                        self.on_buttonBoxClient_apply()
                    dialog.destroy()
                    dialog.deleteLater()
        except:
            pass


    @pyqtSignature('')
    def on_actStatusObservationClientByEvent_triggered(self):
        eventIdListSelected = self.tblEvents.selectedItemIdList()
        clientIdList = []
        for eventId in eventIdListSelected:
            if eventId:
                record = self.tblEvents.model().getRecordById(eventId)
                clientId = forceRef(record.value('client_id'))
                if clientId and clientId not in clientIdList:
                    clientIdList.append(clientId)
        if clientIdList and QtGui.qApp.userHasAnyRight([urAdmin, urEditStatusObservationClient]):
            try:
                dialog = CStatusObservationClientEditor(self, clientIdList)
                try:
                    if dialog.exec_():
                        self.updateEventInfo(self.currentEventId())
                finally:
                    dialog.deleteLater()
            except:
                pass


    @pyqtSignature('')
    def on_actStatusObservationClientBrowserByEvent_triggered(self):
        eventId = self.currentEventId()
        if eventId:
            record = self.tblEvents.model().getRecordById(eventId)
            clientId = forceRef(record.value('client_id'))
        if not clientId:
            clientId = self.selectedClientId()
        if clientId and QtGui.qApp.userHasAnyRight([urAdmin, urEditStatusObservationClient]):
            try:
                dialog = CStatusObservationClientEditor(self, [clientId])
                try:
                    if dialog.exec_():
                        self.updateEventInfo(eventId)
                finally:
                    dialog.deleteLater()
            except:
                pass
    
    
    @pyqtSignature('')
    def on_actJumpToRegistry_triggered(self):
        self.chkFilterId.setChecked(True)
        db = QtGui.qApp.db
        if self.tabMain.currentIndex() == 1:
            record = db.getRecord('Event', ['client_id'], self.currentEventId())  
            self.edtFilterId.setText(forceString(record.value('client_id')))
        elif self.tabMain.currentIndex() == 3:
            tableAction = db.table('Action')
            tableEvent = db.table('Event')
            table = tableAction.leftJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
            record = db.getRecord(table, ['Event.client_id',], self.currentActionId())
            self.edtFilterId.setText(forceString(record.value('client_id')))
        self.tabMain.setCurrentWidget(self.tabRegistry)
        self.on_buttonBoxClient_apply()
      

    @pyqtSignature('')
    def on_actaClients_triggered(self):

        db = QtGui.qApp.db

        stmt = u'''SELECT i,nam,birth,attach FROM tmp_days ORDER BY attach,nam
            '''

        try:
            myquery = db.query(stmt)

            doc = QtGui.QTextDocument()
            cursor = QtGui.QTextCursor(doc)
            cursor.setCharFormat(CReportBase.ReportTitle)
            cursor.insertText(u'Список пациентов\n')
            cursor.setCharFormat(CReportBase.ReportTitle)
            cursor.setBlockFormat(CReportBase.AlignCenter)
            cursor.insertBlock()
            cursor.insertBlock()
            tableColumns = [
                ('25%', [u'№ Амб. карты'], CReportBase.AlignLeft),
                ('25%', [u'Ф.И.О.'], CReportBase.AlignLeft),
                ('25%', [u'Дата рождения'], CReportBase.AlignLeft),
                ('25%', [u'Прикрепление'], CReportBase.AlignLeft)
            ]

            table = createTable(cursor, tableColumns)
            while myquery.next():
                record = myquery.record()
                cl = forceInt(record.value('i'))
                las = forceString(record.value('nam'))
                birth = forceString(record.value('birth'))
                attach = forceString(record.value('attach'))
                row = table.addRow()

                table.setText(row, 0, cl)
                table.setText(row, 1, las)
                table.setText(row, 2, birth)
                table.setText(row, 3, attach)

            html = doc.toHtml(QByteArray('utf-8'))
            view = CReportViewDialog(self)
            view.setText(html)
            view.exec_()
        except:
            doc = QtGui.QTextDocument()
            cursor = QtGui.QTextCursor(doc)
            cursor.setCharFormat(CReportBase.ReportTitle)
            cursor.insertText(u'Не выбрано ни 1 пациента\n')
            html = doc.toHtml(QByteArray('utf-8'))
            view = CReportViewDialog(self)
            view.setText(html)
            view.exec_()


    @pyqtSignature('')
    def on_actaddClients_triggered(self):

        db = QtGui.qApp.db
        lpuCode = forceString(QtGui.qApp.db.translate('Organisation', 'id', QtGui.qApp.currentOrgId(), 'infisCode'))
        if forceString(QtGui.qApp.preferences.appPrefs.get('provinceKLADR', '00'))[:2] == '23' and lpuCode == '07034':
            stmt = u'''CREATE TEMPORARY TABLE IF NOT EXISTS tmp_days(i int,nam varchar(30),birth date,attach varchar(100)) ; INSERT INTO tmp_days SELECT cdt.documentNumber,CONCAT(c.lastName,' ',c.firstName,' ', c.patrName), c.birthDate, if(os.id IS NULL,'нет прикрепления',os.name) FROM Client c LEFT JOIN Client_DocumentTracking cdt ON c.id = cdt.client_id  LEFT JOIN rbDocumentTypeForTracking dtft ON cdt.documentTypeForTracking_id = dtft.id LEFT JOIN ClientAttach ca ON c.id = ca.client_id AND getClientAttachId(c.id,0)=ca.id LEFT JOIN OrgStructure os ON ca.orgStructure_id = os.id where dtft.code=1 and c.id=%(condpersonId)s            ''' % {
                'condpersonId': QtGui.qApp.currentClientId()
                }
        else:
            stmt = u'''CREATE TEMPORARY TABLE IF NOT EXISTS tmp_days(i int,nam varchar(30),birth date,attach varchar(100)) ; INSERT INTO tmp_days SELECT c.id,CONCAT(c.lastName,' ',c.firstName,' ', c.patrName), c.birthDate, if(os.id IS NULL,'нет прикрепления',os.name) FROM Client c LEFT JOIN ClientAttach ca ON c.id = ca.client_id AND getClientAttachId(c.id,0)=ca.id LEFT JOIN OrgStructure os ON ca.orgStructure_id = os.id where c.id=%(condpersonId)s
                            ''' % {'condpersonId': QtGui.qApp.currentClientId()
                                   }
        return db.query(stmt)


    @pyqtSignature('')
    def on_actStatusObservationClient_triggered(self):
        self.updateStatusObservationClient()


    @pyqtSignature('')
    def on_actExpertMedicalCommissionDelete_triggered(self):
        table = self.getCurrentExpertMedicalCommissionTable()
        actionId = table.currentItemId()
        if actionId:
            if QtGui.QMessageBox.question(self,
                            u'Удаление документа', u'Вы действительно хотите удалить документ?',
                            QtGui.QMessageBox.Yes|QtGui.QMessageBox.No,
                            QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
                res1, res2 = QtGui.qApp.call(self, self.deleteExpertMedicalCommission, (actionId,))
                if res1 and res2:
                    table.model().removeRow(table.currentRow())
            self.focusExpertMC()


    def deleteExpertMedicalCommission(self, actionId):
        db = QtGui.qApp.db
        table = db.table('Action')
        db.markRecordsDeleted(table, table['id'].eq(actionId))
        return True


    @pyqtSignature('')
    def on_actExpertMedicalCommissionUpdate_triggered(self):
        self.expertMedicalCommissionActionEdit()


    @pyqtSignature('')
    def on_actExpertMCUpdateTempInvalid_triggered(self):
        QtGui.qApp.setWaitCursor()
        try:
            currentTable = self.getCurrentExpertMedicalCommissionTable()
            actionId = currentTable.currentItemId()
            if not actionId:
                return
            db = QtGui.qApp.db
            tableAction = db.table('Action')
            tableEvent = db.table('Event')
            table = tableAction.innerJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
            record = db.getRecordEx(table, [tableEvent['tempInvalid_id'], tableEvent['id']], [tableAction['id'].eq(actionId), tableAction['deleted'].eq(0), tableEvent['deleted'].eq(0)])
            tempInvalidId = forceRef(record.value('tempInvalid_id')) if record else None
            if not tempInvalidId:
                return
            record = db.getRecordEx(table, '*', [tableAction['id'].eq(actionId), tableAction['deleted'].eq(0)])
            action = CAction(record=record) if record else None
            if not action:
                return
        finally:
            QtGui.qApp.restoreOverrideCursor()
        if u'Номер ЛН' in action._actionType._propertiesByName and action[u'Номер ЛН'] and getRightEditTempInvalid(tempInvalidId):
            self.editTempInvalid(tempInvalidId)


    @pyqtSignature('')
    def on_actExpertMedicalCommissionSelected_triggered(self):
        self.medicalCommissionSelectedRows = []
        currentTable = self.getCurrentExpertMedicalCommissionTable()
        actionId = currentTable.currentItemId()
        currentTable.clearSelection()
        if not actionId:
            return
        db = QtGui.qApp.db
        table = db.table('Action')
        tableEvent = db.table('Event')
        queryTable = table.innerJoin(tableEvent, tableEvent['id'].eq(table['event_id']))
        cols = [table['actionType_id'],
                table['status'],
                table['directionDate'],
                table['setPerson_id'],
                tableEvent['tempInvalid_id']]
        cond = [table['deleted'].eq(0),
                tableEvent['deleted'].eq(0),
                table['id'].eq(actionId),
                ]
        record = db.getRecordEx(queryTable, cols, cond, u'Event.id DESC')
        tempInvalidId = forceRef(record.value('tempInvalid_id')) if record else None
        status = forceInt(record.value('status')) if record else None
        setPersonId = forceRef(record.value('setPerson_id')) if record else None
        actionTypeId = forceRef(record.value('actionType_id')) if record else None
        directionDate = forceDate(record.value('directionDate')) if record else None
        actionIdList = []
        if tempInvalidId:
            cond = [table['deleted'].eq(0),
                    tableEvent['deleted'].eq(0),
                    tableEvent['tempInvalid_id'].eq(tempInvalidId),
                    table['status'].eq(status),
                    table['setPerson_id'].eq(setPersonId),
                    table['actionType_id'].eq(actionTypeId),
                    table['directionDate'].dateEq(directionDate),
                    ]
            actionIdList = db.getDistinctIdList(queryTable, u'Action.id', cond, u'Action.id')
        if actionIdList:
            currentTable.setSelectedItemIdList(actionIdList)
            self.medicalCommissionSelectedRows = actionIdList


    @pyqtSignature('')
    def on_actExpertMedicalCommissionUpdateGroup_triggered(self):
        currentTable = self.getCurrentExpertMedicalCommissionTable()
        selectedActionIdList = currentTable.selectedItemIdList()
        if self.tabExpertMedicalCommissionWidget.currentIndex() != self.tabExpertMedicalCommissionWidget.indexOf(self.tabExpertMedicalSocialInspection) and len(selectedActionIdList) > 1 and len(self.medicalCommissionSelectedRows) > 0:
            actionId = currentTable.currentItemId()
            if actionId and canChangePayStatusAdditional(self, 'Action', actionId) and canEditOtherpeopleAction(self, actionId):
                dialog = CActionEditDialog(self)
                try:
                    dialog.load(actionId)
                    if dialog.exec_():
                        db = QtGui.qApp.db
                        tableEvent = db.table('Event')
                        action = CAction.getActionById(actionId)
                        selectedActionIdList = list(set(selectedActionIdList) - set([actionId]))
                        for selectedActionId in selectedActionIdList:
                            newAction = CAction.getActionById(selectedActionId)
                            newRecord = newAction.getRecord()
                            actionType = newAction.getType()
                            eventId = forceRef(newRecord.value('event_id'))
                            currentId = forceRef(newRecord.value('id'))
                            idx = forceInt(newRecord.value('idx'))
                            number = ''
                            if u'Номер ЛН' in actionType._propertiesByName:
                                number = trim(newAction[u'Номер ЛН'])
                            copyFields(newRecord, action.getRecord())
                            newAction.updateByAction(action)
                            if number and u'Номер ЛН' in actionType._propertiesByName:
                                newAction[u'Номер ЛН'] = number
                            newAction.getRecord().setValue('id', toVariant(currentId))
                            newAction.getRecord().setValue('event_id', toVariant(eventId))
                            newAction.getRecord().setValue('idx', toVariant(idx))
                            if eventId:
                                recordEvent = db.getRecordEx(tableEvent, '*', [tableEvent['id'].eq(eventId), tableEvent['deleted'].eq(0)])
                            self.saveMedicalCommissionAction(newAction, recordEvent, eventId)
                        self.updateMedicalCommissionList(self.__expertMCFilter, dialog.itemId())
                        currentTable.model().updateColumnsCaches(actionId)
                        for selectedActionId in selectedActionIdList:
                            currentTable.model().updateColumnsCaches(selectedActionId)
                        QtGui.qApp.emitCurrentClientInfoChanged()
                        return dialog.itemId()
                    else:
                        self.updateMedicalCommissionInfo(actionId)
                        self.updateClientsListRequest = True
                    return None
                finally:
                    dialog.deleteLater()


    @pyqtSignature('')
    def on_actExpertMedicalCommissionClear_triggered(self):
        self.medicalCommissionSelectedRows = []
        self.getCurrentExpertMedicalCommissionTable().clearSelection()


    @pyqtSignature('')
    def on_actExpertMedicalCommissionMSI_triggered(self):
        actionId = self.tblExpertProtocolsMC.currentItemId()
        if not actionId:
            return
        db = QtGui.qApp.db
        tableAction = db.table('Action')
        tableEvent = db.table('Event')
        table = tableAction.innerJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
        recordPrevEvent = db.getRecordEx(table, [tableEvent['client_id'], tableEvent['id']],
                                         [tableAction['id'].eq(actionId), tableAction['deleted'].eq(0),
                                          tableEvent['deleted'].eq(0)])
        if recordPrevEvent:
            clientId = forceRef(recordPrevEvent.value('client_id'))
            firstEventId = forceRef(recordPrevEvent.value('id'))
            record = db.getRecordEx(table, '*', [tableAction['id'].eq(actionId), tableAction['deleted'].eq(0)])
            prevMKB = forceStringEx(record.value('MKB'))
            prevAction = CAction(record=record) if record else None
        else:
            firstEventId = None
            clientId = None
            prevAction = None
            prevMKB = None
        if not clientId:
            return
        actionTypeIdList = getActionTypeIdListByFlatCode(u'inspection_mse%')
        if actionTypeIdList:
            actionTypeId = None
            if len(actionTypeIdList) > 1:
                try:
                    dialog = CActionTypeDialogTableModel(self, actionTypeIdList)
                    dialog.setWindowTitle(u'Выберите тип направления на МСЭ')
                    if dialog.exec_():
                        actionTypeId = dialog.currentItemId()
                finally:
                    dialog.deleteLater()
            else:
                actionTypeId = actionTypeIdList[0]
            if actionTypeId:
                action = None
                eventRecordMSI = None
                idxMSI = 0
                dialog = CF088CreateDialog(self)
                try:
                    actionType = CActionTypeCache.getById(actionTypeId)
                    defaultStatus = actionType.defaultStatus
                    defaultOrgId = actionType.defaultOrgId
                    defaultExecPersonId = actionType.defaultExecPersonId
                    newRecord = tableAction.newRecord()
                    newRecord.setValue('createDatetime', toVariant(QDateTime.currentDateTime()))
                    newRecord.setValue('createPerson_id', toVariant(QtGui.qApp.userId))
                    newRecord.setValue('modifyDatetime', toVariant(QDateTime.currentDateTime()))
                    newRecord.setValue('modifyPerson_id', toVariant(QtGui.qApp.userId))
                    newRecord.setValue('actionType_id', toVariant(actionTypeId))
                    newRecord.setValue('prevAction_id', toVariant(actionId))
                    newRecord.setValue('status', toVariant(defaultStatus))
                    newRecord.setValue('begDate', toVariant(QDateTime.currentDateTime()))
                    newRecord.setValue('directionDate', toVariant(QDateTime.currentDateTime()))
                    newRecord.setValue('org_id', toVariant(defaultOrgId if defaultOrgId else QtGui.qApp.currentOrgId()))
                    newRecord.setValue('setPerson_id', toVariant(QtGui.qApp.userId))
                    newRecord.setValue('person_id', toVariant(defaultExecPersonId))
                    newRecord.setValue('id', toVariant(None))
                    newRecord = preFillingActionRecordMSI(newRecord, actionTypeId)
                    if prevMKB:
                        newRecord.setValue('MKB', toVariant(prevMKB))
                    newAction = CAction(record=newRecord)
                    if prevAction:
                        newAction.updateByAction(prevAction)
                    if not newAction:
                        return
                    if u'Номер' in newAction.getType()._propertiesByName:
                        newAction[u'Номер'] = None
                    tableEventType = db.table('EventType')
                    eventId = None
                    if firstEventId:
                        queryTable = tableEvent.innerJoin(tableEventType,
                                                          tableEventType['id'].eq(tableEvent['eventType_id']))
                        cond = [tableEvent['id'].eq(firstEventId),
                                tableEventType['context'].like(u'inspection%'),
                                tableEvent['execDate'].isNull(),
                                tableEvent['client_id'].eq(clientId),
                                tableEvent['deleted'].eq(0),
                                tableEventType['deleted'].eq(0),
                                ]
                        recordFirstEvent = db.getRecordEx(queryTable, 'Event.*', cond, u'Event.id DESC')
                        eventId = forceRef(recordFirstEvent.value('id')) if recordFirstEvent else None
                    dialog.load(newAction.getRecord(), newAction, clientId, recordFirstEvent)
                    # dialog.btnPrint.setEnabled(False) #0011955
                    if dialog.exec_() and dialog.checkDataEntered(secondTry=True):
                        dialog.setTextEdits()
                        action = dialog.getAction()
                        eventRecordMSI = dialog.getEventRecord()
                        idxMSI = dialog.idx
                        # dialog.btnPrint.setEnabled(True) #0011955
                    newActionId = None
                    if action:
                        if eventId and eventRecordMSI:
                            newActionId = self.saveMedicalCommissionAction(action, eventRecordMSI, eventId, idx=idxMSI)
                        else:
                            eventTypeId = forceRef(eventRecordMSI.value('id')) if eventRecordMSI else None
                            if not eventTypeId:
                                recordEventType = db.getRecordEx(tableEventType, [tableEventType['id']],
                                                                 [tableEventType['context'].like(u'inspection%'),
                                                                  tableEventType['deleted'].eq(0)], u'EventType.id')
                                eventTypeId = forceRef(recordEventType.value('id')) if recordEventType else None
                            if eventTypeId:
                                recordEvent = tableEvent.newRecord()
                                if eventRecordMSI:
                                    for i in xrange(recordEvent.count()):
                                        recordEvent.setValue(i, eventRecordMSI.value(recordEvent.fieldName(i)))
                                    recordEvent.setValue('eventType_id', toVariant(eventTypeId))
                                    if clientId and not forceRef(recordEvent.value('client_id')):
                                        recordEvent.setValue('client_id', toVariant(clientId))
                                else:
                                    recordEvent.setValue('createDatetime', toVariant(QDateTime.currentDateTime()))
                                    recordEvent.setValue('createPerson_id', toVariant(QtGui.qApp.userId))
                                    recordEvent.setValue('modifyDatetime', toVariant(QDateTime.currentDateTime()))
                                    recordEvent.setValue('modifyPerson_id', toVariant(QtGui.qApp.userId))
                                    recordEvent.setValue('setDate', toVariant(QDateTime.currentDateTime()))
                                    recordEvent.setValue('eventType_id', toVariant(eventTypeId))
                                    recordEvent.setValue('client_id', toVariant(clientId))
                                    recordEvent.setValue('relegatePerson_id', toVariant(QtGui.qApp.userId))
                                    recordEvent.setValue('relegateOrg_id', toVariant(QtGui.qApp.currentOrgId()))
                                    # recordEvent.setValue('tempInvalid_id', toVariant(tempInvalidId))
                                eventId = db.insertRecord(tableEvent, recordEvent)
                                if eventId:
                                    recordEvent.setValue('id', toVariant(eventId))
                                    newActionId = self.saveMedicalCommissionAction(action, recordEvent, eventId,
                                                                                   idx=idxMSI)
                        if eventId and newActionId:
                            if hasattr(dialog, 'tabNotes') and hasattr(dialog.tabNotes, 'saveAttachedFiles'):
                                dialog.tabNotes.saveAttachedFiles(eventId)
                            if hasattr(dialog, 'modelDiagnosisDisease_30_2'):
                                dialog.saveDiagnostics(dialog.modelDiagnosisDisease_30_2, eventId)
                            if hasattr(dialog, 'modelDiagnosisDisease_30_3'):
                                dialog.saveDiagnostics(dialog.modelDiagnosisDisease_30_3, eventId)
                            if hasattr(dialog, 'modelDiagnosisDisease_30_5'):
                                dialog.saveDiagnostics(dialog.modelDiagnosisDisease_30_5, eventId)
                            if hasattr(dialog, 'modelDiagnosisDisease_30_6'):
                                dialog.saveDiagnostics(dialog.modelDiagnosisDisease_30_6, eventId)
                finally:
                    dialog.deleteLater()


    def saveMedicalCommissionAction(self, action, recordEvent = None, eventId = None, idx = 0):
        id = None
        try:
            try:
                db = QtGui.qApp.db
                db.transaction()
                id = action.save(eventId, idx = idx, checkModifyDate = False)
                if id:
                    action.getRecord().setValue('id', toVariant(id))
                    checkTissueJournalStatusByActions([(action.getRecord(), action)])
                    if action.getType().closeEvent and recordEvent:
                        eventExecDate = forceDate(recordEvent.value('execDate'))
                        actionEndDate = forceDateTime(action.getRecord().value('endDate'))
                        if not eventExecDate and actionEndDate:
                            recordEvent.setValue('execDate', QVariant(actionEndDate))
                            recordEvent.setValue('isClosed', QVariant(1))
                if recordEvent:
                    db.updateRecord('Event', recordEvent)
                db.commit()
            except:
                db.rollback()
                raise
        except Exception, e:
            QtGui.qApp.logCurrentException()
            QtGui.QMessageBox.critical( self,
                                        u'',
                                        exceptionToUnicode(e),
                                        QtGui.QMessageBox.Close)
        return id


    @pyqtSignature('')
    def on_actExpertTempInvalidDelete_triggered(self):
        self.onExpertDocDelete(self.tblExpertTempInvalid, self.modelExpertTempInvalid)


    @pyqtSignature('')
    def on_actExpertDisabilityDelete_triggered(self):
        self.onExpertDocDelete(self.tblExpertDisability, self.modelExpertDisability)


    @pyqtSignature('')
    def on_actExpertVitalRestrictionDelete_triggered(self):
        self.onExpertDocDelete(self.tblExpertVitalRestriction, self.modelExpertVitalRestriction)


    def onExpertDocDelete(self, table, model):
        tempInvalidId = table.currentItemId()
        if getRightEditTempInvalid(tempInvalidId):
            if QtGui.QMessageBox.question(self,
                        u'Удаление документа', u'Вы действительно хотите удалить документ?',
                        QtGui.QMessageBox.Yes|QtGui.QMessageBox.No,
                        QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
                self.getCurrentExpertTable().model().updateColumnsCaches(tempInvalidId)
                res1, res2 = QtGui.qApp.call(self, deleteTempInvalid, (self, tempInvalidId,))
                if res1 and res2:
                    model.removeRow(table.currentRow())
                self.updateTempInvalidList(self.__expertFilter)


    @pyqtSignature('')
    def on_actExpertTempInvalidPrev_triggered(self):
        self.onExpertDocPrev(self.tblExpertTempInvalid)


    @pyqtSignature('')
    def on_actExpertDisabilityPrev_triggered(self):
        self.onExpertDocPrev(self.tblExpertDisability)


    @pyqtSignature('')
    def on_actExpertVitalRestrictionPrev_triggered(self):
        self.onExpertDocPrev(self.tblExpertVitalRestriction)


    def onExpertDocPrev(self, table):
        prevId = self.getExpertPrevDocId(table)
        if prevId:
            row = table.model().findItemIdIndex(prevId)
            if row>=0:
                table.setCurrentRow(row)
            else:
                QtGui.QMessageBox.information(self, u'Переход к предыдущему документу', u'Переход невозможен - необходимо изменить фильтр')


    def onEditTempInvalid(self, tempInvalidId):
        if tempInvalidId:
            if getRightEditTempInvalid(tempInvalidId):
                self.editTempInvalid(tempInvalidId)
                self.focusExpert()
                QtGui.qApp.emitCurrentClientInfoChanged()
                
    
    @pyqtSignature('')
    def on_actExpertTempInvalidConcurrently_triggered(self):
        tempInvalidId = self.tblExpertTempInvalid.currentItemId()
        widgetIndex = self.tabWidgetTempInvalidTypes.currentIndex()
        clientId = self.currentClientId()
        if clientId:
            dialog = CTempInvalidCreateDialog(self, clientId, tempInvalidId)
            dialog.setWindowTitle(self.tabWidgetTempInvalidTypes.tabText(widgetIndex))
            try:
                if dialog.exec_():
                    self.updateTempInvalidList(self.__expertFilter, dialog.itemId())
            finally:
                dialog.deleteLater()
        self.focusExpert()
        QtGui.qApp.emitCurrentClientInfoChanged()


    @pyqtSignature('QModelIndex')
    def on_tblExpertTempInvalidDocumentsEx_doubleClicked(self, index):
        documentId = self.tblExpertTempInvalidDocumentsEx.currentItemId()
        tempInvalidId = self.modelExpertTempInvalidDocumentsEx.getCurrentTempInvalidId(documentId)
        self.onEditTempInvalid(tempInvalidId)


    @pyqtSignature('QModelIndex')
    def on_tblExpertTempInvalidRelationDocumentsEx_doubleClicked(self, index):
        documentId = self.tblExpertTempInvalidRelationDocumentsEx.currentItemId()
        tempInvalidId = self.modelExpertTempInvalidRelationDocumentsEx.getCurrentTempInvalidId(documentId)
        self.onEditTempInvalid(tempInvalidId)


    @pyqtSignature('QModelIndex')
    def on_tblExpertDisabilityDocumentsEx_doubleClicked(self, index):
        documentId = self.tblExpertDisabilityDocumentsEx.currentItemId()
        tempInvalidId = self.modelExpertDisabilityDocumentsEx.getCurrentTempInvalidId(documentId)
        self.onEditTempInvalid(tempInvalidId)


    @pyqtSignature('QModelIndex')
    def on_tblExpertDisabilityRelationDocumentsEx_doubleClicked(self, index):
        documentId = self.tblExpertDisabilityRelationDocumentsEx.currentItemId()
        tempInvalidId = self.modelExpertDisabilityRelationDocumentsEx.getCurrentTempInvalidId(documentId)
        self.onEditTempInvalid(tempInvalidId)


    @pyqtSignature('QModelIndex')
    def on_tblExpertVitalRestrictionDocumentsEx_doubleClicked(self, index):
        documentId = self.tblExpertVitalRestrictionDocumentsEx.currentItemId()
        tempInvalidId = self.modelExpertVitalRestrictionDocumentsEx.getCurrentTempInvalidId(documentId)
        self.onEditTempInvalid(tempInvalidId)


    @pyqtSignature('QModelIndex')
    def on_tblExpertVitalRestrictionRelationDocumentsEx_doubleClicked(self, index):
        documentId = self.tblExpertVitalRestrictionRelationDocumentsEx.currentItemId()
        tempInvalidId = self.modelExpertVitalRestrictionRelationDocumentsEx.getCurrentTempInvalidId(documentId)
        self.onEditTempInvalid(tempInvalidId)


    @pyqtSignature('QModelIndex')
    def on_tblExpertTempInvalidDocuments_doubleClicked(self, index):
        tempInvalidDocumentId = self.tblExpertTempInvalidDocuments.currentItemId()
        tempInvalidId = self.modelExpertTempInvalidDocuments.getCurrentTempInvalidId(tempInvalidDocumentId)
        self.onEditTempInvalid(tempInvalidId)


    @pyqtSignature('QModelIndex')
    def on_tblExpertDisabilityDocuments_doubleClicked(self, index):
        tempInvalidDocumentId = self.tblExpertDisabilityDocuments.currentItemId()
        tempInvalidId = self.modelExpertDisabilityDocuments.getCurrentTempInvalidId(tempInvalidDocumentId)
        self.onEditTempInvalid(tempInvalidId)


    @pyqtSignature('QModelIndex')
    def on_tblExpertVitalRestrictionDocuments_doubleClicked(self, index):
        tempInvalidDocumentId = self.tblExpertVitalRestrictionDocuments.currentItemId()
        tempInvalidId = self.modelExpertVitalRestrictionDocuments.getCurrentTempInvalidId(tempInvalidDocumentId)
        self.onEditTempInvalid(tempInvalidId)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelExpertDisability_currentRowChanged(self, current, previous):
        tempInvalidId = self.tblExpertDisability.currentItemId()
        self.updateTempInvalidInfo(tempInvalidId, noPrev=True)
        self.setBtnExpertEditEnabled()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelExpertDisabilityRelation_currentRowChanged(self, current, previous):
        tempInvalidId = self.tblExpertDisabilityRelation.currentItemId()
        self.updateTempInvalidInfo(tempInvalidId)
        self.setBtnExpertEditEnabled()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelExpertVitalRestriction_currentRowChanged(self, current, previous):
        tempInvalidId = self.tblExpertVitalRestriction.currentItemId()
        self.updateTempInvalidInfo(tempInvalidId, noPrev=True)
        self.setBtnExpertEditEnabled()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelExpertVitalRestrictionRelation_currentRowChanged(self, current, previous):
        tempInvalidId = self.tblExpertVitalRestrictionRelation.currentItemId()
        self.updateTempInvalidInfo(tempInvalidId)
        self.setBtnExpertEditEnabled()


    @pyqtSignature('int')
    def on_modelExpertTempInvalid_itemsCountChanged(self, count):
        self.lblExpertTempInvalidCount.setText(formatRecordsCount(count))
        self.expertTempInvalidCount = formatRecordsCount(count)


    @pyqtSignature('int')
    def on_modelExpertTempInvalidDocumentsEx_itemsCountChanged(self, count):
        self.lblExpertTempInvalidDocumentsExCount.setText(formatRecordsCount(count))


    @pyqtSignature('int')
    def on_modelExpertDisability_itemsCountChanged(self, count):
        self.lblExpertDisabilityCount.setText(formatRecordsCount(count))
        self.expertDisabilityCount = formatRecordsCount(count)


    @pyqtSignature('int')
    def on_modelExpertDisabilityDocumentsEx_itemsCountChanged(self, count):
        self.lblExpertDisabilityDocumentsExCount.setText(formatRecordsCount(count))


    @pyqtSignature('int')
    def on_modelExpertVitalRestriction_itemsCountChanged(self, count):
        self.lblExpertVitalRestrictionCount.setText(formatRecordsCount(count))
        self.expertVitalRestrictionCount = formatRecordsCount(count)


    @pyqtSignature('int')
    def on_modelExpertVitalRestrictionDocumentsEx_itemsCountChanged(self, count):
        self.lblExpertVitalRestrictionDocumentsExCount.setText(formatRecordsCount(count))


    @pyqtSignature('')
    def on_btnExpertRelationEdit_clicked(self):
        tempInvalidId = self.getCurrentExpertRelationTable().currentItemId()
        if tempInvalidId:
            self.editTempInvalid(tempInvalidId)
        self.focusExpert()
        QtGui.qApp.emitCurrentClientInfoChanged()


    @pyqtSignature('QModelIndex')
    def on_tblExpertTempInvalid_doubleClicked(self, index):
        tempInvalidId = self.tblExpertTempInvalid.currentItemId()
        if getRightEditTempInvalid(tempInvalidId):
            self.on_btnExpertEdit_clicked()


    @pyqtSignature('QModelIndex')
    def on_tblExpertTempInvalidRelation_doubleClicked(self, index):
        tempInvalidId = self.tblExpertTempInvalidRelation.currentItemId()
        if getRightEditTempInvalid(tempInvalidId):
            self.on_btnExpertRelationEdit_clicked()


    @pyqtSignature('QModelIndex')
    def on_tblExpertDisability_doubleClicked(self, index):
        tempInvalidId = self.tblExpertDisability.currentItemId()
        if getRightEditTempInvalid(tempInvalidId):
            self.on_btnExpertEdit_clicked()


    @pyqtSignature('QModelIndex')
    def on_tblExpertDisabilityRelation_doubleClicked(self, index):
        tempInvalidId = self.tblExpertDisabilityRelation.currentItemId()
        if getRightEditTempInvalid(tempInvalidId):
            self.on_btnExpertRelationEdit_clicked()


    @pyqtSignature('QModelIndex')
    def on_tblExpertVitalRestriction_doubleClicked(self, index):
        tempInvalidId = self.tblExpertVitalRestriction.currentItemId()
        if getRightEditTempInvalid(tempInvalidId):
            self.on_btnExpertEdit_clicked()


    @pyqtSignature('QModelIndex')
    def on_tblExpertVitalRestrictionRelation_doubleClicked(self, index):
        tempInvalidId = self.tblExpertVitalRestrictionRelation.currentItemId()
        if getRightEditTempInvalid(tempInvalidId):
            self.on_btnExpertRelationEdit_clicked()


    @pyqtSignature('QModelIndex')
    def on_tblExpertDirectionsMC_doubleClicked(self, index):
        if QtGui.qApp.userHasRight(urRegTabEditExpertMC):
            self.on_btnExpertEdit_clicked()


    @pyqtSignature('QModelIndex')
    def on_tblExpertProtocolsMC_doubleClicked(self, index):
        if QtGui.qApp.userHasRight(urRegTabEditExpertMC):
            self.on_btnExpertEdit_clicked()


    @pyqtSignature('QModelIndex')
    def on_tblExpertMedicalSocialInspection_doubleClicked(self, index):
        if QtGui.qApp.userHasRight(urRegTabEditExpertMC):
            self.on_btnExpertEdit_clicked()


    @pyqtSignature('')
    def on_btnExpertEdit_clicked(self):
        if self.tabWidgetTempInvalidTypes.currentIndex() == self.tabWidgetTempInvalidTypes.indexOf(self.tabExpertMedicalCommission):
            self.expertMedicalCommissionActionEdit()
        else:
            tempInvalidId = self.currentTempInvalidId()
            if tempInvalidId:
                self.editTempInvalid(tempInvalidId)
            self.focusExpert()
        QtGui.qApp.emitCurrentClientInfoChanged()


    @pyqtSignature('')
    def on_actExpertPrint_triggered(self):
        if self.tabWidgetTempInvalidTypes.currentIndex() == self.tabWidgetTempInvalidTypes.indexOf(self.tabExpertMedicalCommission):
            tblExpertMC = self.getCurrentExpertMedicalCommissionTable()
            expertiseType = self.tabWidgetTempInvalidTypes.currentIndex()
            tblExpertMC.setReportHeader(unicode(self.tabWidgetTempInvalidTypes.tabText(expertiseType)))
            tblExpertMC.setReportDescription(self.getExpertMCFilterAsText())
            tblExpertMC.printContent()
            self.focusExpertMC()
        else:
            tblExpert = self.getCurrentExpertTable()
            tempInvalidType = self.tabWidgetTempInvalidTypes.currentIndex()
            reportHeader = unicode(self.tabWidgetTempInvalidTypes.tabText(tempInvalidType))
            reportDescription = self.getExpertFilterAsText()
            CRegistryExpertPrintReport(self, tblExpert, reportHeader, reportDescription).exec_()
            self.focusExpert()


    @pyqtSignature('int')
    def on_btnExpertPrint_printByTemplate(self, templateId):
        context = forceString(QtGui.qApp.db.translate('rbPrintTemplate', 'id', templateId, 'context'))
        data = None
        if self.tabWidgetTempInvalidTypes.currentIndex() == self.tabWidgetTempInvalidTypes.indexOf(self.tabExpertMedicalCommission):
            if context == u'medicalCommission':
                currentTable = self.getCurrentExpertMedicalCommissionTable()
                if templateId == -1:
                    expertiseType = self.tabWidgetTempInvalidTypes.currentIndex()
                    currentTable.setReportHeader(unicode(self.tabWidgetTempInvalidTypes.tabText(expertiseType)))
                    currentTable.setReportDescription(self.getExpertMCFilterAsText())
                    currentTable.printContent()
                    self.focusExpertMC()
                else:
                    idList = currentTable.model().idList()
                    context = CInfoContext()
                    data = {'expertise': CLocActionInfoList(context, idList)}
                    QtGui.qApp.call(self, applyTemplate, (self, templateId, data))
        else:
            if context == u'tempInvalid':
                data = self.getKerContextData()
            else:
                data = self.getKerListContextData()
            QtGui.qApp.call(self, applyTemplate, (self, templateId, data))


    @pyqtSignature('')
    def on_btnExpertFilter_clicked(self):
        if self.tabWidgetTempInvalidTypes.currentIndex() == self.tabWidgetTempInvalidTypes.indexOf(self.tabExpertMedicalCommission):
            for s in self.chkListOnExpertMCPage:
                chk = s[0]
                if chk.isChecked():
                    self.activateFilterWdgets(s[1])
                    return
            self.chkFilterExpertExpertiseMC.setChecked(True)
        else:
            for s in self.chkListOnExpertPage:
                chk = s[0]
                if chk.isChecked():
                    self.activateFilterWdgets(s[1])
                    return
            self.chkFilterExpertDocType.setChecked(True)


    def on_actExpertNewMC(self):
        clientId = self.currentClientId()
        actionId = None
        if not clientId:
            return
        db = QtGui.qApp.db
        tableAction = db.table('Action')
        actionTypeIdList = []
        if self.tabExpertMedicalCommissionWidget.currentIndex() in [self.tabExpertMedicalCommissionWidget.indexOf(self.tabExpertDirectionsMC), self.tabExpertMedicalCommissionWidget.indexOf(self.tabExpertProtocolsMC)]:
            actionTypeIdList = getActionTypeIdListByFlatCode(u'inspection_disability%')
        elif self.tabExpertMedicalCommissionWidget.currentIndex() == self.tabExpertMedicalCommissionWidget.indexOf(self.tabExpertMedicalSocialInspection):
            actionTypeIdList = getActionTypeIdListByFlatCode(u'inspection_mse%')
        if actionTypeIdList:
            actionTypeId = None
            if len(actionTypeIdList) > 1:
                try:
                    dialog = CActionTypeDialogTableModel(self, actionTypeIdList)
                    if dialog.exec_():
                        actionTypeId = dialog.currentItemId()
                finally:
                    dialog.deleteLater()
            else:
                actionTypeId = actionTypeIdList[0]
            if actionTypeId:
                action = None
                eventRecordMSI = None
                idxMSI = 0
                if self.tabExpertMedicalCommissionWidget.currentIndex() == self.tabExpertMedicalCommissionWidget.indexOf(self.tabExpertMedicalSocialInspection):
                    dialog = CF088CreateDialog(self)
                else:
                    dialog = CTempInvalidActionCreateDialog(self)
                try:
                    actionType = CActionTypeCache.getById(actionTypeId)
#                    defaultStatus = actionType.defaultStatus
                    defaultOrgId = actionType.defaultOrgId
                    newRecord = tableAction.newRecord()
                    newRecord.setValue('createDatetime', toVariant(QDateTime().currentDateTime()))
                    newRecord.setValue('createPerson_id',toVariant(QtGui.qApp.userId))
                    newRecord.setValue('modifyDatetime', toVariant(QDateTime().currentDateTime()))
                    newRecord.setValue('modifyPerson_id',toVariant(QtGui.qApp.userId))
                    newRecord.setValue('actionType_id',  toVariant(actionTypeId))
                    newRecord.setValue('prevAction_id',  toVariant(None))
                    newRecord.setValue('org_id',         toVariant(defaultOrgId if defaultOrgId else QtGui.qApp.currentOrgId()))
                    newRecord.setValue('id',             toVariant(None))
                    dialog.setIsFillPersonValueUserId(False)
                    if self.tabExpertMedicalCommissionWidget.currentIndex() == self.tabExpertMedicalCommissionWidget.indexOf(self.tabExpertDirectionsMC):
                        newRecord.setValue('begDate',       toVariant(QDateTime().currentDateTime()))
                        newRecord.setValue('directionDate', toVariant(QDateTime().currentDateTime()))
                        newRecord.setValue('setPerson_id',  toVariant(QtGui.qApp.userId))
                        newRecord.setValue('status',        toVariant(CActionStatus.appointed))
                        newRecord.setValue('person_id',     toVariant(None))
                    if self.tabExpertMedicalCommissionWidget.currentIndex() == self.tabExpertMedicalCommissionWidget.indexOf(self.tabExpertProtocolsMC):
                        newRecord.setValue('begDate',       toVariant(QDateTime.currentDateTime()))
                        newRecord.setValue('endDate',       toVariant(QDateTime.currentDateTime()))
                        newRecord.setValue('directionDate', toVariant(QDateTime.currentDateTime()))
                        newRecord.setValue('person_id',     toVariant(QtGui.qApp.userId))
                        newRecord.setValue('status',        toVariant(CActionStatus.finished))
                    if self.tabExpertMedicalCommissionWidget.currentIndex() == self.tabExpertMedicalCommissionWidget.indexOf(self.tabExpertMedicalSocialInspection):
                        newRecord.setValue('begDate',       toVariant(QDateTime.currentDateTime()))
                        newRecord.setValue('directionDate', toVariant(QDateTime.currentDateTime()))
                        newRecord.setValue('setPerson_id',  toVariant(QtGui.qApp.userId))
                        newRecord.setValue('status',        toVariant(CActionStatus.appointed))
                        newRecord.setValue('person_id',     toVariant(None))
                        newRecord = preFillingActionRecordMSI(newRecord, actionTypeId)
                        dialog.setIsFillPersonValueFinished(True)
                    newAction = CAction(record=newRecord)
                    if not newAction:
                        return
                    if u'Номер' in newAction.getType()._propertiesByName:
                        newAction[u'Номер'] = None
                    dialog.load(newAction.getRecord(), newAction, clientId)
                    #dialog.btnPrint.setEnabled(False) #0011955
                    if dialog.exec_() and dialog.checkDataEntered(secondTry=True):
                        if self.tabExpertMedicalCommissionWidget.currentIndex() == self.tabExpertMedicalCommissionWidget.indexOf(self.tabExpertMedicalSocialInspection):
                            dialog.setTextEdits()
                            eventRecordMSI = dialog.getEventRecord()
                            idxMSI = dialog.idx
                        action = dialog.getAction()
                        #dialog.btnPrint.setEnabled(True) #0011955
                    if action:
                        tableEventType = db.table('EventType')
                        eventId = None
                        if self.tabExpertMedicalCommissionWidget.currentIndex() == self.tabExpertMedicalCommissionWidget.indexOf(self.tabExpertMedicalSocialInspection):
                            eventTypeId = forceRef(eventRecordMSI.value('id')) if eventRecordMSI else None
                            if not eventTypeId:
                                recordEventType = db.getRecordEx(tableEventType, [tableEventType['id']], [tableEventType['context'].like(u'inspection%'), tableEventType['deleted'].eq(0)], u'EventType.id')
                                eventTypeId = forceRef(recordEventType.value('id')) if recordEventType else None
                            if eventTypeId:
                                tableEvent = db.table('Event')
                                recordEvent = tableEvent.newRecord()
                                if eventRecordMSI:
                                    for i in xrange(recordEvent.count()):
                                        recordEvent.setValue(i, eventRecordMSI.value(recordEvent.fieldName(i)))
                                    recordEvent.setValue('eventType_id',   toVariant(eventTypeId))
                                    if clientId and not forceRef(recordEvent.value('client_id')):
                                        recordEvent.setValue('client_id', toVariant(clientId))
                                else:
                                    recordEvent.setValue('createDatetime', toVariant(QDateTime.currentDateTime()))
                                    recordEvent.setValue('createPerson_id',toVariant(QtGui.qApp.userId))
                                    recordEvent.setValue('modifyDatetime', toVariant(QDateTime.currentDateTime()))
                                    recordEvent.setValue('modifyPerson_id',toVariant(QtGui.qApp.userId))
                                    recordEvent.setValue('setDate',        toVariant(QDateTime.currentDateTime()))
                                    recordEvent.setValue('eventType_id',   toVariant(eventTypeId))
                                    recordEvent.setValue('client_id',      toVariant(clientId))
                                    recordEvent.setValue('relegatePerson_id', toVariant(QtGui.qApp.userId))
                                    recordEvent.setValue('relegateOrg_id', toVariant(QtGui.qApp.currentOrgId()))
                                eventId = db.insertRecord(tableEvent, recordEvent)
                                if eventId:
                                    recordEvent.setValue('id', toVariant(eventId))
                                    newActionId = self.saveMedicalCommissionAction(action, recordEvent, eventId, idx = idxMSI)
                                    if newActionId:
                                        if hasattr(dialog, 'tabNotes') and hasattr(dialog.tabNotes, 'saveAttachedFiles'):
                                            dialog.tabNotes.saveAttachedFiles(eventId)
                                        if hasattr(dialog, 'modelDiagnosisDisease_30_2'):
                                            dialog.saveDiagnostics(dialog.modelDiagnosisDisease_30_2, eventId)
                                        if hasattr(dialog, 'modelDiagnosisDisease_30_3'):
                                            dialog.saveDiagnostics(dialog.modelDiagnosisDisease_30_3, eventId)
                                        if hasattr(dialog, 'modelDiagnosisDisease_30_5'):
                                            dialog.saveDiagnostics(dialog.modelDiagnosisDisease_30_5, eventId)
                                        if hasattr(dialog, 'modelDiagnosisDisease_30_6'):
                                            dialog.saveDiagnostics(dialog.modelDiagnosisDisease_30_6, eventId)
                            else:
                                recordEventType = db.getRecordEx(tableEventType, [tableEventType['id']], [tableEventType['context'].like(u'inspection%'), tableEventType['deleted'].eq(0)], u'EventType.id')
                                eventTypeId = forceRef(recordEventType.value('id')) if recordEventType else None
                                if eventTypeId:
                                    tableEvent = db.table('Event')
                                    recordEvent = tableEvent.newRecord()
                                    recordEvent.setValue('createDatetime', toVariant(QDateTime.currentDateTime()))
                                    recordEvent.setValue('createPerson_id',toVariant(QtGui.qApp.userId))
                                    recordEvent.setValue('modifyDatetime', toVariant(QDateTime.currentDateTime()))
                                    recordEvent.setValue('modifyPerson_id',toVariant(QtGui.qApp.userId))
                                    recordEvent.setValue('setDate',        toVariant(QDateTime.currentDateTime()))
                                    recordEvent.setValue('eventType_id',   toVariant(eventTypeId))
                                    recordEvent.setValue('client_id', toVariant(clientId))
                                    recordEvent.setValue('relegatePerson_id', toVariant(QtGui.qApp.userId))
                                    recordEvent.setValue('relegateOrg_id', toVariant(QtGui.qApp.currentOrgId()))
                                    eventId = db.insertRecord(tableEvent, recordEvent)
                                    if eventId:
                                        recordEvent.setValue('id', toVariant(eventId))
                                        actionId = self.saveMedicalCommissionAction(action, recordEvent, eventId, idx = idxMSI)
                                        if actionId and hasattr(dialog, 'tabNotes') and hasattr(dialog.tabNotes, 'saveAttachedFiles'):
                                            dialog.tabNotes.saveAttachedFiles(eventId)
                finally:
                    dialog.deleteLater()
        return actionId


    @pyqtSignature('')
    def on_btnExpertNew_clicked(self):
        if self.tabWidgetTempInvalidTypes.currentIndex() == self.tabWidgetTempInvalidTypes.indexOf(self.tabExpertMedicalCommission):
            currentPersonId = QtGui.qApp.userId
            if currentPersonId:
                db = QtGui.qApp.db
                tablePerson = db.table('Person')
                tableRBPost = db.table('rbPost')
                queryTable = tablePerson.innerJoin(tableRBPost, tableRBPost['id'].eq(tablePerson['post_id']))
                cond = [tablePerson['id'].eq(currentPersonId),
                             tablePerson['deleted'].eq(0),
                             tableRBPost['code'].regexp(u'^[1-3]+')
                            ]
                record = db.getRecordEx(queryTable, [tablePerson['id']], cond)
                personId = forceRef(record.value('id')) if record else None
                if personId:
                    actionId = self.on_actExpertNewMC()
                    if actionId:
                        currentTable = self.getCurrentExpertMedicalCommissionTable()
                        self.updateMedicalCommissionList(self.__expertMCFilter, actionId)
                        currentTable.model().updateColumnsCaches(actionId)
                        if self.tabExpertMedicalCommissionWidget.currentIndex() == self.tabExpertMedicalCommissionWidget.indexOf(self.tabExpertMedicalSocialInspection):
                            self.tblExpertProtocolsMC.model().updateColumnsCaches(actionId)
                        QtGui.qApp.emitCurrentClientInfoChanged()
                    else:
                        self.updateMedicalCommissionInfo(actionId)
                        self.updateClientsListRequest = True
            self.focusExpertMC()
        else:
            tempInvalidId = getTempInvalidIdOpen(self.currentClientId(), self.tabWidgetTempInvalidTypes.currentIndex())
            if tempInvalidId:
                self.editTempInvalid(tempInvalidId)
            else:
                self.editTempInvalidExpert()
            self.focusExpert()
        QtGui.qApp.emitCurrentClientInfoChanged()


    @pyqtSignature('bool')
    def on_chkFilterExpertDocType_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterExpertSerial_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkPrimaryOrDuble_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterTempInvalidDocType_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterExpertNumber_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterExpertReason_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)
    
    
    @pyqtSignature('bool')
    def on_chkFilterExpertResult_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterExpertBegDate_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterDirectDateOnMC_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterExpertExternal_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkDateKAK_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkExpertIdKAK_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterExpertEndDate_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterExpertPerson_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterExpertOrgStruct_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterExpertSpeciality_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterExpertMKB_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterExpertState_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterExpertDuration_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterExpertInsuranceOfficeMark_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterExpertExportFSS_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterExpertCreatePerson_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterExpertModifyPerson_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)

    
    @pyqtSignature('bool')
    def on_chkFilterExpertModifyDate_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)
    

    @pyqtSignature('bool')
    def on_chkFilterExpertCreateDate_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)


#    @pyqtSignature('bool')
#    def on_chkFilterExpertExpertiseMC_toggled(self, checked):
#        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterExpertExpertiseTypeMC_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterExpertNumberMC_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterExpertNumberExpertise_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterExpertSetPersonMC_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterExpertDirectionDateMC_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterExpertExpertiseCharacterMC_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterExpertExpertiseKindMC_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_ghkFilterExpertExpertiseObjectMC_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterExpertExpertiseArgumentMC_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterExpertOrgStructMC_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterExpertSpecialityMC_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterExpertMKBMC_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterExpertClosedMC_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterExecDateMC_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkExpertIdMC_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterExpertExportedToExternalISMC_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterExpertCreatePersonMC_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterExpertCreateDateMC_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterExpertModifyPersonMC_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterExpertModifyDateMC_toggled(self, checked):
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('QAbstractButton*')
    def on_buttonBoxExpert_clicked(self, button):
        buttonCode = self.buttonBoxExpert.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.on_buttonBoxExpert_apply()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_buttonBoxExpert_reset()


#    @pyqtSignature('')
    def on_buttonBoxExpert_reset(self):
        for s in self.chkListOnExpertPage:
            chk = s[0]
            if chk.isChecked():
                self.deactivateFilterWdgets(s[1])
                chk.setChecked(False)
        self.cmbFilterExpert.setCurrentIndex(0)


    @pyqtSignature('QAbstractButton*')
    def on_buttonBoxExpertMC_clicked(self, button):
        buttonCode = self.buttonBoxExpertMC.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.on_buttonBoxExpertMC_apply()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_buttonBoxExpertMC_reset()


#    @pyqtSignature('')
    def on_buttonBoxExpertMC_reset(self):
        for s in self.chkListOnExpertMCPage:
            chk = s[0]
            if chk.isChecked():
                self.deactivateFilterWdgets(s[1])
                chk.setChecked(False)
        self.cmbFilterExpert.setCurrentIndex(0)


#    @pyqtSignature('')
    def on_buttonBoxExpert_apply(self):
        filter = {}
        if self.chkFilterExpertDocType.isChecked():
            filter['docTypeId'] = self.cmbFilterExpertDocType.value()
        if self.chkFilterExpertSerial.isChecked():
            filter['serial'] = forceStringEx(self.edtFilterExpertSerial.text())
        if self.chkFilterExpertNumber.isChecked():
            filter['number'] = forceStringEx(self.edtFilterExpertNumber.text())
        if self.chkPrimaryOrDuble.isChecked():
            filter['primaryOrDuble'] = forceInt(self.cmbPrimaryOrDuble.currentIndex())
        if self.chkFilterTempInvalidDocType.isChecked():
            filter['electronic'] = forceInt(self.cmbFilterTempInvalidDocType.currentIndex())
        if self.chkFilterExpertReason.isChecked():
            filter['reasonId'] = self.cmbFilterExpertReason.value()
        if self.chkFilterExpertResult.isChecked():
            filter['invalidResult'] = self.cmbFilterExpertResult.value()
        if self.chkFilterExpertBegDate.isChecked():
            filter['begBegDate'] = self.edtFilterExpertBegBegDate.date()
            filter['endBegDate'] = self.edtFilterExpertEndBegDate.date()
        if self.chkFilterExpertEndDate.isChecked():
            filter['begEndDate'] = self.edtFilterExpertBegEndDate.date()
            filter['endEndDate'] = self.edtFilterExpertEndEndDate.date()
        if self.chkFilterExpertPerson.isChecked():
            filter['personId'] = self.cmbFilterExpertPerson.value()
        if self.chkFilterExpertOrgStruct.isChecked():
            filter['expertOrgStructureId'] = self.cmbFilterExpertOrgStruct.value()
        if self.chkFilterExpertSpeciality.isChecked():
            filter['expertSpecialityId'] = self.cmbFilterExpertSpeciality.value()
        if self.chkFilterExpertMKB.isChecked():
            filter['begMKB'] = unicode(self.edtFilterExpertBegMKB.text())
            filter['endMKB'] = unicode(self.edtFilterExpertEndMKB.text())
        if self.chkFilterExpertState.isChecked():
            filter['state'] = self.cmbFilterExpertState.currentIndex()
        if self.chkFilterExpertDuration.isChecked():
            filter['begDuration'] = self.edtFilterExpertBegDuration.value()
            filter['endDuration'] = self.edtFilterExpertEndDuration.value()
        if self.chkFilterExpertInsuranceOfficeMark.isChecked():
            filter['insuranceOfficeMark'] = self.cmbFilterExpertInsuranceOfficeMark.currentIndex()
        if self.chkFilterExpertExportFSS.isChecked() and self.chkFilterExpertExportFSS.isVisible():
            filter['documentExportFSS'] = self.cmbFilterExpertExportFSS.currentIndex()
        filter['linked'] = self.chkFilterExpertLinked.isChecked()
        if self.chkFilterExpertExternal.isChecked():
            filter['isExternal'] = self.cmbFilterExpertExternal.currentIndex()
        if self.chkFilterExpertCreatePerson.isChecked():
            filter['createPersonId'] = self.cmbFilterExpertCreatePerson.value()
        if self.chkFilterExpertCreateDate.isChecked():
            filter['begCreateDate'] = self.edtFilterExpertBegCreateDate.date()
            filter['endCreateDate'] = self.edtFilterExpertEndCreateDate.date()
        if self.chkFilterExpertModifyPerson.isChecked():
            filter['modifyPersonId'] = self.cmbFilterExpertModifyPerson.value()
        if self.chkFilterExpertModifyDate.isChecked():
            filter['begModifyDate'] = self.edtFilterExpertBegModifyDate.date()
            filter['endModifyDate'] = self.edtFilterExpertEndModifyDate.date()
        expertFilterType = self.cmbFilterExpert.currentIndex()
        if expertFilterType == 0:
            filter['receiverIds'] = [ self.selectedClientId() ]
        elif expertFilterType == 1:
            filter['receiverIds'] = self.modelClients.idList()
        elif expertFilterType == 2:
            filter['receiverEventIds'] = [ self.tblEvents.currentItemId() ]
        elif expertFilterType == 3:
            filter['receiverEventIds'] = self.modelEvents.idList()
        elif expertFilterType == 4:
            filter['clientIds'] = [ self.selectedClientId() ]
        elif expertFilterType == 5:
            filter['clientIds'] = self.modelClients.idList()
        elif expertFilterType == 6:
            filter['eventIds'] = [ self.tblEvents.currentItemId() ]
        elif expertFilterType == 7:
            filter['eventIds'] = self.modelEvents.idList()
        filter['expertFilterType']=expertFilterType
        self.updateTempInvalidList(filter)
        self.focusExpert()


    def on_buttonBoxExpertMC_apply(self):
        filter = {}
        if self.chkFilterExpertExpertiseMC.isChecked():
            filter['expertiseId'] = self.cmbFilterExpertExpertiseMC.currentIndex()
        if self.chkFilterExpertExpertiseTypeMC.isChecked():
            expertiseTypeIdList = []
            expertiseTypeStr = self.cmbFilterExpertExpertiseTypeMC.value().split(',')
            for expertiseType in expertiseTypeStr:
                expertiseTypeId = trim(expertiseType)
                if expertiseTypeId and expertiseTypeId not in expertiseTypeIdList:
                    expertiseTypeIdList.append(expertiseTypeId)
            filter['expertiseTypeId'] = (expertiseTypeIdList, forceString(self.cmbFilterExpertExpertiseTypeMC.currentText()))
        if self.chkFilterExpertNumberMC.isChecked():
            filter['expertNumber'] = forceStringEx(self.edtFilterExpertNumberMC.text())
        if self.chkFilterExpertNumberExpertise.isChecked():
            filter['expertNumberExpertise'] = forceStringEx(self.edtFilterExpertNumberExpertise.text())
        if self.chkFilterExpertSetPersonMC.isChecked():
            filter['setPersonId'] = self.cmbFilterExpertSetPersonMC.value()
        if self.chkFilterExpertDirectionDateMC.isChecked():
            filter['expertDirectionBegDate'] = self.edtFilterExpertDirectionBegDateMC.date()
            filter['expertDirectionEndDate'] = self.edtFilterExpertDirectionEndDateMC.date()
        if self.chkFilterExpertOrgStructMC.isChecked():
            filter['expertOrgStructureId'] = self.cmbFilterExpertOrgStructMC.value()
        if self.chkFilterDirectDateOnMC.isChecked():
            filter['begDirectDate'] = self.edtFilterBegDirectDateOnMC.date()
            filter['endDirectDate'] = self.edtFilterEndDirectDateOnMC.date()
        if self.chkFilterExecDateMC.isChecked():
            filter['begExecDate'] = self.edtFilterBegExecDateMC.date()
            filter['endExecDate'] = self.edtFilterEndExecDateMC.date()
        if self.chkFilterExpertSpecialityMC.isChecked():
            filter['expertSpecialityId'] = self.cmbFilterExpertSpecialityMC.value()
        if self.chkFilterExpertMKBMC.isChecked():
            filter['begMKB'] = unicode(self.edtFilterExpertBegMKBMC.text())
            filter['endMKB'] = unicode(self.edtFilterExpertEndMKBMC.text())
        if self.chkFilterExpertClosedMC.isChecked():
            filter['actionStatus'] = self.cmbFilterExpertClosedMC.value()
        if self.chkFilterExpertExpertiseCharacterMC.isChecked():
            filter['expertiseCharacterId'] = unicode(self.cmbFilterExpertExpertiseCharacterMC.value())
        if self.chkFilterExpertExpertiseKindMC.isChecked():
            filter['expertiseKindId'] = unicode(self.cmbFilterExpertExpertiseKindMC.value())
        if self.ghkFilterExpertExpertiseObjectMC.isChecked():
            filter['expertiseObjectId'] = unicode(self.cmbFilterExpertExpertiseObjectMC.value())
        if self.chkFilterExpertExpertiseArgumentMC.isChecked():
            filter['expertiseArgumentId'] = unicode(self.cmbFilterExpertExpertiseArgumentMC.value())
        if self.chkExpertIdMC.isChecked():
            filter['expertId'] = self.cmbExpertIdMC.value()
        if self.chkFilterExpertExportedToExternalISMC.isChecked():
            filter['expertExportedType'] = self.cmbFilterExpertExportedTypeMC.currentIndex()
            filter['expertIntegratedISId'] = self.cmbFilterExpertIntegratedISMC.value()
        if self.chkFilterExpertCreateDateMC.isChecked():
            filter['begCreateDate'] = self.edtFilterExpertBegCreateDateMC.date()
            filter['endCreateDate'] = self.edtFilterExpertEndCreateDateMC.date()
        if self.chkFilterExpertCreatePersonMC.isChecked():
            filter['createPersonId'] = self.cmbFilterExpertCreatePersonMC.value()
        if self.chkFilterExpertModifyDateMC.isChecked():
            filter['begModifyDate'] = self.edtFilterExpertBegModifyDateMC.date()
            filter['endModifyDate'] = self.edtFilterExpertEndModifyDateMC.date()
        if self.chkFilterExpertModifyPersonMC.isChecked():
            filter['modifyPersonId'] = self.cmbFilterExpertModifyPersonMC.value()
        actionsFilterType = self.cmbFilterExpertMC.currentIndex()
        if actionsFilterType == 0:
            filter['clientIds'] = [ self.selectedClientId() ]
        elif actionsFilterType == 1:
            filter['clientIds'] = self.modelClients.idList()
        elif actionsFilterType == 2:
            filter['eventIds'] = [ self.tblEvents.currentItemId() ]
        elif actionsFilterType == 3:
            filter['eventIds'] = self.modelEvents.idList()
        filter['actionsFilterType']=actionsFilterType
        self.updateMedicalCommissionList(filter)
        self.setBtnExpertEnabled()
        self.focusExpertMC()

# ===== :)
# ============ Visit_Page ====================================================

    @pyqtSignature('bool')
    def on_chkFilterVisitType_toggled(self, checked):
        if checked and not self.cmbFilterVisitsType.hasTable():
            self.cmbFilterVisitsType.setTable('rbVisitType', False)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterVisitExecDate_toggled(self, checked):
        self.setChildElementsVisible(self.chkListOnVisitsPage, self.chkFilterVisitExecDate, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterExecSetOrgStructureVisit_toggled(self, checked):
        self.setChildElementsVisible(self.chkListOnVisitsPage, self.chkFilterExecSetOrgStructureVisit, checked)
        self.onChkFilterToggled(self.sender(), checked)
        if checked:
            self.chkFilterExecSetPersonVisit.setChecked(False)
            execSetOrgStructure = self.cmbFilterExecSetOrgStructureVisit.value()
            if not execSetOrgStructure:
                execSetOrgStructure = QtGui.qApp.currentOrgStructureId()
                self.cmbFilterExecSetOrgStructureVisit.setValue(execSetOrgStructure)
            self.cmbFilterExecSetPersonVisit.setOrgStructureId(execSetOrgStructure)
        else:
            self.cmbFilterExecSetPersonVisit.setOrgStructureId(None)


    @pyqtSignature('bool')
    def on_chkFilterExecSetSpecialityVisit_toggled(self, checked):
        self.setChildElementsVisible(self.chkListOnVisitsPage, self.chkFilterExecSetSpecialityVisit, checked)
        self.onChkFilterToggled(self.sender(), checked)
        if checked:
            if not self.cmbFilterExecSetSpecialityVisit.hasTable():
                self.cmbFilterExecSetSpecialityVisit.setTable('rbSpeciality', False)
            self.chkFilterExecSetPersonVisit.setChecked(False)
            self.cmbFilterExecSetPersonVisit.setSpecialityId(self.cmbFilterExecSetSpecialityVisit.value())
        else:
            self.cmbFilterExecSetPersonVisit.setSpecialityId(None)


    @pyqtSignature('int')
    def on_cmbFilterExecSetSpecialityVisit_currentIndexChanged(self, index):
        self.cmbFilterExecSetPersonVisit.setSpecialityId(self.cmbFilterExecSetSpecialityVisit.value())


    @pyqtSignature('bool')
    def on_chkFilterExecSetPersonVisit_toggled(self, checked):
        self.setChildElementsVisible(self.chkListOnVisitsPage, self.chkFilterExecSetPersonVisit, checked)
        self.onChkFilterToggled(self.sender(), checked)
        self.chkFilterExecSetOrgStructureVisit.setChecked(False)
        self.chkFilterExecSetSpecialityVisit.setChecked(False)


    @pyqtSignature('bool')
    def on_chkFilterVisitAssistant_toggled(self, checked):
        self.setChildElementsVisible(self.chkListOnVisitsPage, self.chkFilterVisitAssistant, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterServiceVisit_toggled(self, checked):
        self.setChildElementsVisible(self.chkListOnVisitsPage, self.chkFilterServiceVisit, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterSceneVisit_toggled(self, checked):
        if checked and not self.cmbFilterSceneVisit.hasTable():
            self.cmbFilterSceneVisit.setTable('rbScene', True)
        self.setChildElementsVisible(self.chkListOnVisitsPage, self.chkFilterSceneVisit, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterVisitFinance_toggled(self, checked):
        if checked and not self.cmbFilterVisitFinance.hasTable():
            self.cmbFilterVisitFinance.setTable('rbFinance', True)
        self.setChildElementsVisible(self.chkListOnVisitsPage, self.chkFilterVisitFinance, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterVisitCreatePersonEx_toggled(self, checked):
        self.setChildElementsVisible(self.chkListOnVisitsPage, self.chkFilterVisitCreatePersonEx, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterVisitCreateDateEx_toggled(self, checked):
        self.setChildElementsVisible(self.chkListOnVisitsPage, self.chkFilterVisitCreateDateEx, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterVisitModifyPersonEx_toggled(self, checked):
        self.setChildElementsVisible(self.chkListOnVisitsPage, self.chkFilterVisitModifyPersonEx, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterVisitModifyDateEx_toggled(self, checked):
        self.setChildElementsVisible(self.chkListOnVisitsPage, self.chkFilterVisitModifyDateEx, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('bool')
    def on_chkFilterVisitPayStatusEx_toggled(self, checked):
        self.setChildElementsVisible(self.chkListOnVisitsPage, self.chkFilterVisitPayStatusEx, checked)
        self.onChkFilterToggled(self.sender(), checked)


    @pyqtSignature('QAbstractButton*')
    def on_buttonBoxVisit_clicked(self, button):
        buttonCode = self.buttonBoxVisit.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.on_buttonBoxVisit_apply()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_buttonBoxVisit_reset()


    def on_buttonBoxVisit_reset(self):
        for s in self.chkListOnVisitsPage:
            chk = s[0]
            if chk.isChecked():
                self.deactivateFilterWdgets(s[1])
                chk.setChecked(False)
        self.cmbFilterVisit.setCurrentIndex(0)


    def on_buttonBoxVisit_apply(self):
        filter = {}
        if self.chkFilterVisitType.isChecked():
            filter['visitTypeId'] = self.cmbFilterVisitsType.value()
        if self.chkFilterVisitCreatePersonEx.isChecked():
            filter['createPersonId'] = self.cmbFilterVisitCreatePersonEx.value()
        if self.chkFilterVisitCreateDateEx.isChecked():
            filter['begCreateDate'] = self.edtFilterVisitBegCreateDateEx.date()
            filter['endCreateDate'] = self.edtFilterVisitEndCreateDateEx.date()
        if self.chkFilterVisitModifyPersonEx.isChecked():
            filter['modifyPersonId'] = self.cmbFilterVisitModifyPersonEx.value()
        if self.chkFilterVisitModifyDateEx.isChecked():
            filter['begModifyDate'] = self.edtFilterVisitBegModifyDateEx.date()
            filter['endModifyDate'] = self.edtFilterVisitEndModifyDateEx.date()
        if self.chkFilterVisitPayStatusEx.isChecked():
            filter['payStatusCode'] = self.cmpFilterVisitPayStatusCodeEx.currentIndex()
            index = self.cmbFilterVisitPayStatusFinanceEx.currentIndex()
            if not 0<=index<5:
                index = 0
            filter['payStatusFinanceCode'] = 5-index
        if self.chkFilterVisitExecDate.isChecked():
            filter['begExecDateTime'] = QDateTime(self.edtFilterVisitBegExecDate.date(), self.edtFilterVisitBegExecTime.time())
            filter['endExecDateTime'] = QDateTime(self.edtFilterVisitEndExecDate.date(), self.edtFilterVisitEndExecTime.time())
        if self.chkFilterExecSetOrgStructureVisit.isChecked():
            filter['orgStructureId'] = self.cmbFilterExecSetOrgStructureVisit.value()
        if self.chkFilterExecSetSpecialityVisit.isChecked():
            filter['specialityId'] = self.cmbFilterExecSetSpecialityVisit.value()
        if self.chkFilterExecSetPersonVisit.isChecked():
            filter['personId'] = self.cmbFilterExecSetPersonVisit.value()
        if self.chkFilterVisitAssistant.isChecked():
            filter['assistantId'] = self.cmbFilterVisitAssistant.value()
        if self.chkFilterVisitFinance.isChecked():
            filter['financeId'] = self.cmbFilterVisitFinance.value()
        if self.chkFilterServiceVisit.isChecked():
            filter['serviceId'] = self.cmbFilterServiceVisit.value()
        if self.chkFilterSceneVisit.isChecked():
            filter['sceneId'] = self.cmbFilterSceneVisit.value()
        visitFilterType = self.cmbFilterVisit.currentIndex()
        if visitFilterType == 0:
            filter['clientIds'] = [ self.selectedClientId() ]
        elif visitFilterType == 1:
            filter['clientIds'] = self.modelClients.idList()
        elif visitFilterType == 2:
            filter['eventIds'] = [ self.tblEvents.currentItemId() ]
        elif visitFilterType == 3:
            filter['eventIds'] = self.modelEvents.idList()
        filter['visitFilterType'] = visitFilterType
        self.updateVisitsList(filter)
        self.focusEvents()

# ===== Visit_Page ============ :)

def convertFilterToTextItem(resList, filter, prop, propTitle, format=None):
    val = filter.get(prop, None)
    if val:
        if format:
            resList.append((propTitle, format(val)))
        else:
            resList.append((propTitle, val))


class CIdValidator(QtGui.QRegExpValidator):
    def __init__(self, parent):
        QtGui.QRegExpValidator.__init__(self, QRegExp(r'(\d*)(\.\d*)?'), parent)


def dateTimeToString(value):
#   return value.toString(Qt.DefaultLocaleLongDate)
    return  value.toString('dd.MM.yyyy hh:mm:ss')


def parseClientId(clientIdEx):
    if '.' in clientIdEx:
        miacCode, clientId = clientIdEx.split('.')
    else:
        miacCode, clientId = '', clientIdEx
    if miacCode:
        if forceString(QtGui.qApp.db.translate('Organisation', 'id', QtGui.qApp.currentOrgId(), 'miacCode')) != miacCode.strip():
            return -1
    return clientId


class CSchedulesModel(CRecordListModel):
    def __init__(self,  parent):
        CRecordListModel.__init__(self, parent)
#        activityPref = QtGui.qApp.getGlobalPreference('23')
        self.addCol(CBoolInDocTableCol(u'Отметка',    'checked', 6))
        self.addCol(CEnumInDocTableCol(u'Тип', 'appointmentType', 6, CSchedule.atNames)).setReadOnly()
        self.addCol(CRBInDocTableCol(u'Назначение', 'appointmentPurpose_id', 20, 'rbAppointmentPurpose')).setReadOnly()
        self.addCol(CDateTimeInDocTableCol(u'Дата и время приема', 'time', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Каб',          'office', 6)).setReadOnly()
        self.addCol(CRBInDocTableCol(u'Специалист', 'person_id', 20, 'vrbPersonWithSpeciality')).setReadOnly()
        self.addCol(CRBInDocTableCol(u'Записал',    'recordPerson_id', 20, 'vrbPersonWithSpeciality')).setReadOnly()
        self.addCol(CInDocTableCol(u'Жалобы',       'complaint', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Примечания',   'note', 6)).setReadOnly()
        self.addCol(CRBInDocTableCol(u'Вид деятельности',  'activity_id',  10,  'rbActivity')).setToolTip(u'Вид деятельности')
        self.order = ''
        self._mapColumnToOrder = {'checked'               :'Schedule_Item.checked',
                                  'appointmentType'       :'Schedule.appointmentType',
                                  'appointmentPurpose_id' :'rbAppointmentPurpose.name',
                                  'time'                  :'Schedule_Item.time',
                                  'office'                :'Schedule.office',
                                  'person_id'             :'person',
                                  'recordPerson_id'       :'recordPerson',
                                  'complaint'             :'Schedule_Item.complaint',
                                  'note'                  :'Schedule_Item.note',
                                  'activity_id'           :'rbActivity.name',
                                  }


    def setOrder(self, order):
        self.order = order


    def getOrder(self, fieldName, column):
        if hasattr(self._cols[column], 'extraFields'):
            if len(self._cols[column].extraFields) > 0:
                fieldName = self._cols[column].extraFields[0]
        return self._mapColumnToOrder[fieldName]


    def loadData(self, clientId = None):
        if clientId:
            self.clientId = clientId
            currentDate = forceDateTime(QDate.currentDate())
            db = QtGui.qApp.db
            tableSchedule = db.table('Schedule')
            tableScheduleItem = db.table('Schedule_Item')
            cols = [tableScheduleItem['id'],
                    tableScheduleItem['checked'],
                    tableScheduleItem['time'],
                    tableSchedule['appointmentType'],
                    tableScheduleItem['appointmentPurpose_id'],
                    tableSchedule['office'],
                    tableSchedule['person_id'],
                    tableSchedule['activity_id'],
                    tableScheduleItem['recordPerson_id'],
                    tableScheduleItem['complaint'],
                    tableScheduleItem['note'],
                   ]
            cond = [tableScheduleItem['client_id'].eq(self.clientId),
                    tableSchedule['date'].ge(currentDate),
                    tableSchedule['deleted'].eq(0),
                    tableScheduleItem['deleted'].eq(0),
                   ]
            tableQuery = tableScheduleItem
            tableQuery = tableQuery.leftJoin(tableSchedule, tableSchedule['id'].eq(tableScheduleItem['master_id']))
            if self.order:
                if 'rbAppointmentPurpose.name' in self.order:
                    tableRBAppointmentPurpose = db.table('rbAppointmentPurpose')
                    tableQuery = tableQuery.leftJoin(tableRBAppointmentPurpose, tableRBAppointmentPurpose['id'].eq(tableScheduleItem['appointmentPurpose_id']))
                if 'person' in self.order:
                    tableVRBPersonWithSpeciality = db.table('vrbPersonWithSpeciality')
                    tableQuery = tableQuery.leftJoin(tableVRBPersonWithSpeciality, tableVRBPersonWithSpeciality['id'].eq(tableSchedule['person_id']))
                    cols.append('vrbPersonWithSpeciality.name AS person')
                if 'recordPerson' in self.order:
                    tableVRBPersonWithSpeciality = db.table('vrbPersonWithSpeciality')
                    tableQuery = tableQuery.leftJoin(tableVRBPersonWithSpeciality, tableVRBPersonWithSpeciality['id'].eq(tableScheduleItem['recordPerson_id']))
                    cols.append('vrbPersonWithSpeciality.name AS recordPerson')
                if 'rbActivity.name' in self.order:
                    tableRBActivity = db.table('rbActivity')
                    tableQuery = tableQuery.leftJoin(tableRBActivity, tableRBActivity['id'].eq(tableSchedule['activity_id']))
            else:
                self.order = u'Schedule_Item.time DESC'
            records = db.getRecordList(tableQuery, cols, cond, self.order)
            self.setItems(records)
        else:
            self.clearItems()


    def flags(self, index):
        result = Qt.ItemIsSelectable|Qt.ItemIsEnabled
        column = index.column()
        if column == 0:
            row = index.row()
            item = self.items()[row]
            if forceInt(item.value('appointmentType')) == CSchedule.atHome or QtGui.qApp.ambulanceUserCheckable():
                result = result | Qt.ItemIsUserCheckable
        return result


    def setData(self, index, value, role=Qt.EditRole):
        column = index.column()
        row = index.row()
        item = self.items()[row]
        if column == 0 and role == Qt.CheckStateRole:
            scheduleItemId = forceRef(item.value('id'))
            checked = forceBool(item.value('checked'))
            db = QtGui.qApp.db
            stmt = 'UPDATE Schedule_Item SET checked=%(newChecked)d ' \
                   'WHERE id=%(id)d AND client_id=%(clientId)d AND deleted=0' % dict(
                        id         = scheduleItemId,
                        clientId   = self.clientId,
                        newChecked = not checked,
                                                                                )
            r = db.query(stmt)
            item.setValue('checked', toVariant(not checked))
            if r.numRowsAffected()!=1:
                QtGui.qApp.emitCurrentClientInfoChanged()
            if QtGui.qApp.mainWindow.dockResources:
                QtGui.qApp.mainWindow.dockResources.content.updateTimeTable()
            self.emitCellChanged(row, column)
            return True
        return False


    def getScheduleItemId(self, row):
        item = self.items()[row]
        return forceRef(item.value('id'))


class CExternalNotificationModel(CRecordListModel):
    def __init__(self, parent):
        CRecordListModel.__init__(self, parent)
        self.begDate = None
        self.endDate = None
        self.addCol(CDateTimeInDocTableCol(u'Получено', 'last_sync_date', 30)).setReadOnly()
        self.addCol(CInDocTableCol(u'Где обслуживался', 'organisation_name', 30)).setReadOnly()
        self.addCol(CDateTimeInDocTableCol(u'Начало лечения', 'begDate', 30)).setReadOnly()
        self.addCol(CDateTimeInDocTableCol(u'Конец лечения', 'endDate', 30)).setReadOnly()
        self.addCol(CInDocTableCol(u'Тип обслуживания', 'category_display', 30)).setReadOnly()
        self.addCol(CInDocTableCol(u'Код МКБ', 'mkb', 30)).setReadOnly()
        self.addCol(CInDocTableCol(u'Диагноз', 'DiagName', 30)).setReadOnly()

    def setDate(self, begDate, endDate):
        self.begDate = begDate
        self.endDate = endDate

    def loadData(self, clientId=None):
        db = QtGui.qApp.db
        tableEN = db.table('ExternalNotification')
        tableOS = db.table('OrgStructure')
        tableClient = db.table('Client')
        tableMKB = db.table('MKB')
        cols = [tableEN['lastName'],
                tableEN['firstName'],
                tableEN['patrName'],
                tableEN['organisation_id'],
                tableEN['begDate'],
                tableEN['endDate'],
                tableEN['birthDate'],
                tableEN['last_sync_date'],
                tableEN['organisation_name'],
                tableClient['sex'],
                tableMKB['DiagName'],
                tableEN['mkb'],
                tableOS['name'],
                tableEN['category_display']
                ]
        cond = [tableEN['client_id'].eq(clientId), tableEN['client_id'].isNotNull()]
        tableQuery = tableEN
        tableQuery = tableQuery.leftJoin(tableOS, tableOS['id'].eq(tableEN['orgStructure_id']))
        tableQuery = tableQuery.leftJoin(tableClient, tableClient['id'].eq(tableEN['client_id']))
        tableQuery = tableQuery.leftJoin(tableMKB, tableMKB['DiagID'].eq(tableEN['mkb']))
        records = db.getRecordList(tableQuery, cols, cond, 'last_sync_date desc')
        self.setItems(records)


class CVisitsBySchedulesModel(CRecordListModel):
    def __init__(self,  parent):
        CRecordListModel.__init__(self, parent)
        self.addCol(CBoolInDocTableCol(u'Выполнено', 'event_id', 6)).setReadOnly()
        self.addCol(CEnumInDocTableCol(u'Тип',       'appointmentType', 6, CSchedule.atNames)).setReadOnly()
        self.addCol(CRBInDocTableCol(u'Назначение', 'appointmentPurpose_id', 20, 'rbAppointmentPurpose')).setReadOnly()
        self.addCol(CDateTimeInDocTableCol(u'Дата и время приема', 'date', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Каб',          'office', 6)).setReadOnly()
        self.addCol(CRBInDocTableCol(u'Специалист', 'person_id', 20, 'vrbPersonWithSpeciality')).setReadOnly()
        self.addCol(CRBInDocTableCol(u'Записал',    'recordPerson_id', 20, 'vrbPersonWithSpeciality')).setReadOnly()
        self.addCol(CInDocTableCol(u'Примечания',   'note', 6)).setReadOnly()
        self.addCol(CRBInDocTableCol(u'Вид деятельности',  'activity_id',  10,  'rbActivity')).setToolTip(u'Вид деятельности').setReadOnly()
        self.order = ''
        self._mapColumnToOrder = {'event_id'              :'vVisitExt.event_id',
                                  'appointmentType'       :'Schedule.appointmentType',
                                  'appointmentPurpose_id' :'rbAppointmentPurpose.name',
                                  'date'                  :'date',
                                  'office'                :'Schedule.office',
                                  'person_id'             :'person',
                                  'recordPerson_id'       :'recordPerson',
                                  'note'                  :'Schedule_Item.note',
                                  'activity_id'           :'rbActivity.name',
                                  }


    def setOrder(self, order):
        self.order = order


    def getOrder(self, fieldName, column):
        if hasattr(self._cols[column], 'extraFields'):
            if len(self._cols[column].extraFields) > 0:
                fieldName = self._cols[column].extraFields[0]
        return self._mapColumnToOrder[fieldName]


    def loadData(self, clientId):
        if clientId:
            db   = QtGui.qApp.db
            cols = []
            tableQuery = []
            if self.order:
                if 'rbAppointmentPurpose.name' in self.order:
                    tableQuery.append(u' LEFT JOIN rbAppointmentPurpose ON rbAppointmentPurpose.id = Schedule_Item.appointmentPurpose_id')
                if 'person' in self.order:
                    tableQuery.append(u' LEFT JOIN vrbPersonWithSpeciality ON vrbPersonWithSpeciality.id = Schedule.person_id')
                    cols.append('vrbPersonWithSpeciality.name AS person')
                if 'recordPerson' in self.order:
                    tableQuery.append(u' LEFT JOIN vrbPersonWithSpeciality ON vrbPersonWithSpeciality.id = Schedule_Item.recordPerson_id')
                    cols.append('vrbPersonWithSpeciality.name AS recordPerson')
                if 'rbActivity.name' in self.order:
                    tableQuery.append(u' LEFT JOIN rbActivity ON rbActivity.id = Schedule.activity_id')
            else:
                self.order = u'Schedule_Item.time DESC'
            stmt =  '''SELECT
                     Schedule_Item.id,
                     vVisitExt.event_id,
                     COALESCE(vVisitExt.date,      Schedule_Item.time) AS date,
                     COALESCE(vVisitExt.person_id, Schedule.person_id) AS person_id,
                     Schedule.appointmentType,
                     Schedule_Item.appointmentPurpose_id,
                     Schedule.office,
                     Schedule.activity_id,
                     Schedule_Item.recordPerson_id,
                     Schedule_Item.complaint %(cols)s
                    FROM
                     Schedule_Item
                     LEFT JOIN Schedule     ON Schedule.id      = Schedule_Item.master_id
                     LEFT JOIN Person       ON Person.id        = Schedule.person_id
                     LEFT JOIN vVisitExt    ON vVisitExt.client_id = Schedule_Item.client_id
                                               AND Person.speciality_id = vVisitExt.speciality_id
                                               AND DATE(vVisitExt.date) = Schedule.date
                     %(queryTable)s
                     WHERE Schedule_Item.client_id =%(clientId)d
                       AND Schedule_Item.deleted = 0
                       AND Schedule.deleted = 0
                       AND Schedule.date<=%(currentDate)s
                    ORDER BY %(order)s'''
            query = db.query(stmt%dict(cols        = (', %s'%(','.join(col for col in cols if col))) if cols else '',
                                       queryTable = (''.join(tq for tq in tableQuery if tq)) if tableQuery else '',
                                       clientId    = clientId,
                                       currentDate = db.formatDate(QDate.currentDate()),
                                       order       = self.order
                                      )
                            )
            items = []
            while query.next():
                items.append(query.record())
            self.setItems(items)
        else:
            self.clearItems()


    def getScheduleItemId(self, row):
        item = self.items()[row]
        return forceRef(item.value('id'))


    def getEventId(self, row):
        item = self.items()[row]
        return forceRef(item.value('event_id'))



class CCanceledSchedulesModel(CRecordListModel):
    def __init__(self,  parent):
        CRecordListModel.__init__(self, parent)
        self.addCol(CDateTimeInDocTableCol( u'Время',                   'time', 20)).setReadOnly()
        self.addCol(CEnumInDocTableCol(     u'Запись через',            'recordClass', 4, [u'-', u'инфомат', u'call-центр', u'интернет'])).setReadOnly()
        self.addCol(CDateTimeInDocTableCol( u'Дата и время записи',     'recordDatetime', 20)).setReadOnly()
        self.addCol(CRBInDocTableCol(       u'Записал',                 'recordPerson_id', 20, 'vrbPersonWithSpeciality')).setReadOnly()
        self.addCol(CDateTimeInDocTableCol( u'Дата и время изменения',  'modifyDatetime', 20)).setReadOnly()
        self.addCol(CRBInDocTableCol(       u'Изменил',                 'modifyPerson_id', 20, 'vrbPersonWithSpeciality')).setReadOnly()
        self.addCol(CRBInDocTableCol        (u'Врач',                'person_id', 20, 'vrbPersonWithSpeciality')).setReadOnly()
        self.addCol(CRBLikeEnumInDocTableCol(u'Тип', 'appointmentType',  20, CSchedule.atNames)).setReadOnly()
        self.addCol(CInDocTableCol(         u'Примечания',              'note', 6)).setReadOnly()
        self.order = u'Schedule_Item.time DESC'
        self.headerSortingCol = {}


    def loadData(self, clientId):
        if clientId:
            db   = QtGui.qApp.db
            cols = []
            tableQuery = []
            stmt =  '''SELECT
                     Schedule_Item.id,
                     Schedule_Item.time,
                     Schedule_Item.recordDatetime,
                     Schedule_Item.recordClass,
                     Schedule_Item.recordPerson_id,
                     Schedule_Item.modifyPerson_id,
                     Schedule_Item.modifyDatetime,
                     Schedule.appointmentType,
                     Schedule_Item.note,
                     Schedule.person_id
                    FROM
                     Schedule_Item
                     LEFT JOIN Schedule     ON Schedule.id      = Schedule_Item.master_id
                     WHERE Schedule_Item.client_id =%(clientId)d
                       AND Schedule_Item.deleted = 1
                       AND Schedule.deleted = 0
                       AND (Schedule.date <= %(currentDate)s OR Schedule_Item.modifyDatetime <= %(currentDate)s)
                    ORDER BY %(order)s'''
            query = db.query(stmt%dict(cols        = (', %s'%(','.join(col for col in cols if col))) if cols else '',
                                       queryTable = (''.join(tq for tq in tableQuery if tq)) if tableQuery else '',
                                       clientId    = clientId,
                                       currentDate = db.formatDate(QDate.currentDate().addDays(1)),
                                       order       = self.order
                                      )
                            )
            items = []
            while query.next():
                items.append(query.record())
            self.setItems(items)
        else:
            self.clearItems()


    def getScheduleItemId(self, row):
        item = self.items()[row]
        return forceRef(item.value('id'))
    
    
    def sort(self, col, order=Qt.AscendingOrder):
        self.headerSortingCol = {col: order}
        reverse = order == Qt.DescendingOrder
        if col in [0, 2, 4]:
            self.items().sort(key=lambda x: forceDateTime(x.value(self.cols()[col].fieldName())) if x else None, reverse=reverse)
        else:
            self.items().sort(key=lambda x: forceString(self.cols()[col].toString(x.value(self.cols()[col].fieldName()), x)) if x else None, reverse=reverse)
        self.reset()


class CRegistryExpertPrintReport(CReport):
    def __init__(self, parent, tblExpert, title, descr):
        CReport.__init__(self, parent)
        self.setTitle(title)
        self.__tblExpert = tblExpert
        self.__descr = descr


    def getSetupDialog(self, parent):
        result = CRegistryExpertPrintDialog(parent)
        result.setWindowTitle(u'Cписок документов ВУТ')
        return result


    def getClientId(self, tempInvalidId):
        query = QtGui.qApp.db.query('SELECT client_id FROM TempInvalid WHERE id = %d' % tempInvalidId)
        if query.next():
            return forceInt(query.value(0))


    def getTempInvalidDocumentNumber(self, tempInvalidId):
        db = QtGui.qApp.db
        table = db.table('TempInvalidDocument')
        record = db.getRecordEx(table, table['number'], [table['deleted'].eq(0), table['master_id'].eq(tempInvalidId)], 'id desc')
        if record:
            return forceString(record.value('number'))
    
    
    def getIssueDate(self, tempInvalidId):
        query = QtGui.qApp.db.query('SELECT issueDate FROM TempInvalidDocument WHERE master_id = %d' % tempInvalidId)
        if query.next():
            return forceString(query.value(0))


    def buildShowMask(self, params, colNames):
        showMask = [True] * (self.__tblExpert.model().columnCount() + 3)
        map = {
            'begDatePermit':       u'Дата начала путевки',
            'begDateStationary':   u'В стационаре "с"',
            'break':               u'Нарушение режима',
            'breakDate':           u'Дата нарушения режима',
            'disability':          u'Инвалидность',
            'endDatePermit':       u'Дата окончания путевки',
            'endDateStationary':   u'В стационаре "по"',
            'numberPermit':        u'Номер путевки',
            'result':              u'Результат',
            'resultDate':          u'Дата результата - Приступить к работе',
            'resultOtherwiseDate': u'Дата результата - Иное',
            'issueDate':           u'Дата выдачи документа'
            }
        for k in map.keys():
            if params[k] == False:
                showMask[colNames.index(map[k])] = False
        return showMask


    def build(self, params):
        model = self.__tblExpert.model()
        colNames = [u'Код пациента', u'Номер документа']
        colNames.extend([forceString(model.headerData(i, Qt.Horizontal)) for i in xrange(model.columnCount())])
        colNames.extend([u'Дата выдачи документа'])
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertText(self.__descr)
        cursor.insertBlock()
        cursor.insertBlock()

        table = cursor.insertTable(model.rowCount() + 1, model.columnCount() + 3)
        fmt = table.format()
        fmt.setWidth(QtGui.QTextLength(QtGui.QTextLength.PercentageLength, 100))
        fmt.setCellPadding(2)
        fmt.setCellSpacing(0)
        table.setFormat(fmt)

        for i, name in enumerate(colNames):
            cursor = table.cellAt(0, i).lastCursorPosition()
            cursor.setCharFormat(CReportBase.TableHeader)
            cursor.setBlockFormat(CReportBase.AlignCenter)
            cursor.insertText(name)

        for row in xrange(1, model.rowCount() + 1):
            cursor = table.cellAt(row, 0).lastCursorPosition()
            index = model.createIndex(row - 1, 0)
            cursor.insertText(str(self.getClientId(forceInt(self.__tblExpert.itemId(index)))))
            cursor = table.cellAt(row, 1).lastCursorPosition()
            cursor.insertText(self.getTempInvalidDocumentNumber(self.__tblExpert.itemId(index)))

            for col in xrange(model.columnCount()):
                cursor = table.cellAt(row, col + 2).lastCursorPosition()
                index = model.createIndex(row - 1, col)
                cursor.insertText(forceString(model.data(index)))
            
            cursor = table.cellAt(row, col + 3).lastCursorPosition()
            index = model.createIndex(row - 1, 0)
            cursor.insertText(self.getIssueDate(self.__tblExpert.itemId(index)))

        for i, show in reversed(list(enumerate(self.buildShowMask(params, colNames)))):
            if not show:
                table.removeColumns(i, 1)

        return doc




def contactToLikeMask(contact):
    m = '...'
    result = m+u''.join(contact.replace('-','').replace(' ','').replace('.','').replace('(','').replace(')','').replace('+',''))+m
    return result

#WTF?
def getKerContext():
    return ['tempInvalid', 'tempInvalidList']

#WTF?
def getActionContext():
    return ['actionsList']

#WTF?
def getVisitContext():
    return ['visitsList']

#WTF?
def getEventContextTemplate():
    return ['eventsList']


def getClientContext():
    return ['clientsList']


def getMedicalCommissionContext():
    return ['medicalCommission']
