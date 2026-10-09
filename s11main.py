#!/usr/bin/env python
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
from ctypes.util import find_library
import library.patches

assert library.patches  # затыкаем pyflakes

import codecs
import gc
import locale
import logging
import os.path
import re
import serial
import sip
import sys
import time
from optparse import OptionParser

psutilFlag = False

try:
    import psutil
    psutilFlag = True
except ImportError:
    pass

def lockFile(fileName, pid):
    try:
        lockedFile = open(fileName, 'w')
        lockedFile.write(str(pid))
        lockedFile.close()
    except Exception as e:
        print e
        return -1
    return 0


def fileExists(fileName):
    return os.path.exists(fileName)


def getPidList():
    if not psutilFlag:
        return []

    procName = 'samson.exe'
    fileName = 's11main.py'
    pids = []
    for proc in psutil.process_iter():
        try:
            pinfo = proc.as_dict(attrs=['pid', 'name', 'cmdline'])
        except psutil.NoSuchProcess:
            pass
        else:
            if str(pinfo['name']).find(procName) > -1 or str(pinfo['cmdline']).find(fileName) > -1:
                pids.append(pinfo['pid'])

    return pids


def createLock():
    if not psutilFlag:
        print("Psutil not available, blocking of multi-processes is not possible")
        return
    dirPath = os.path.join(os.path.expanduser('~'), '.samson-vista')
    lockFileName = '.s11main.lock'
    fileName = os.path.join(dirPath, lockFileName)
    if not os.path.isdir(dirPath):
        os.mkdir(dirPath)
    myPid = os.getpid()
    if fileExists(fileName):
        try:
            lockedFile = open(fileName, 'r')
            PID = lockedFile.readline()
            for pid in getPidList():
                if str(pid) == str(PID):
                    lockedFile.close()
                    print("Exit, too many running applications")
                    sys.exit(1)
            lockedFile.close()
            lockFile(fileName, myPid)
        except Exception as e:
            print e
    else:
        lockFile(fileName, myPid)

# Перенес проверку запущенного приложения повыше, что бы быстрее отрбатывала, без лишней инициализации всего проекта
if "--oneprocess" in sys.argv[1:]:
    createLock()

from PyQt4 import QtGui
from PyQt4.QtCore import (
    Qt,
    pyqtSignature,
    SIGNAL,
    QByteArray,
    QDateTime,
    QEvent,
    QEventLoop,
    QObject,
    QProcess,
    QThread,
    QTime,
    QTimer,
    QTranslator,
    QVariant, QDate,
)

from library                                            import database
from library.Attach.WebDAVInterface                     import CWebDAVInterface
from library.BaseApp                                    import CBaseApp
from library.DbfViewDialog                              import viewDbf
from library.DialogBase                                 import CConstructHelperMixin
from library.downloadProgress                           import DownloadProgress, LoadSizeFormat
from library.GS1CodeParser                              import CGS1CodeParser
from library.ItemsListDialog                            import CItemsListDialog
from library.MSCAPI.certErrors                          import ECertNotFound

from library.PrintTemplates import CPrintAction, getPrintTemplates, applyTemplate, getFirstPrintTemplate
from library.SendMailDialog                             import sendMail
from library.SerialSettings                             import CSerialSettings

try:
    from library.SmartCard.SmartCardWatcher             import CSmartCardWatcher
    gSmartCardAvailable = True
except:
    gSmartCardAvailable = False
from library.symbologyIdentification                    import (
                                                                hasSymbologyId,
                                                                getSymbologyIdLen,
                                                                isEan13,
                                                                isGS1,
                                                                isPdf417,
                                                                isPdf417WithDoubleBackslash,
                                                                isQrCode,
                                                                stripSymbologyId,
                                                               )
from library.TableModel                                 import CTextCol, CIntCol, CDateTimeCol
from library.Utils import (
    anyToUnicode,
    exceptionToUnicode,
    forceBool,
    forceDouble,
    forceTime,
    forceInt,
    forceRef,
    forceDate,
    forceString,
    forceStringEx,
    formatSNILS,
    getPref,
    quote,
    setPref,
    toVariant,
    withWaitCursor, formatDays,
)

from KLADR.Utils                                        import getProvinceKLADRCode

from preferences.CalendarExceptionList                  import CCalendarExceptionList
from preferences.connection                             import CConnectionDialog
from preferences.decor                                  import CDecorDialog
from preferences.EventPage                              import DefaultAverageDuration
from preferences.VoucherPage                            import DefaultVoucherDuration
from preferences.PreferencesDialog                      import CPreferencesDialog

from Accounting.AccountingDialog                        import CAccountingDialog
from Accounting.CashBookDialog                          import CCashBookDialog

from Blank.BlanksDialog                                 import CBlanksDialog

from CentralizedAccounting.CentralizedAccountingDialog import CCentralizedAccountingDialog

from DataCheck.CheckClients                             import ClientsCheck
from DataCheck.CheckEvents                              import CEventsCheck
from DataCheck.CheckTempInvalidEditDialog               import CCheckTempInvalidEditDialog
from DataCheck.CheckTempInvalid                         import TempInvalidCheck
from DataCheck.LogicalControlDiagnosis                  import CControlDiagnosis
from DataCheck.LogicalControlDoubles                    import CControlDoubles
from DataCheck.LogicalControlMes                        import CLogicalControlMes

from Events.PreCreateEventDialog                        import CPreCreateEventDialog

from Exchange.AriadnaDialog.DialogOdli                  import DialogOdli
from Exchange.Export131                                 import Export131
from Exchange.ExportActionResult                        import ExportActionResult
from Exchange.ExportActions                             import ExportActionType
from Exchange.ExportAttachDoctorSectionInfoDialog       import CExportAttachDoctorSectionInfoDialog
from Exchange.ExportActionTemplate                      import ExportActionTemplate
from Exchange.ExportEvents                              import ExportEventType
from Exchange.ExportFeedDataCsv                         import exportFeedDataCsv
from Exchange.ExportVMPCases                            import ExportVMPCases
from Exchange.ExportHL7v2_5                             import ExportHL7v2_5
from Exchange.ExportPrimaryDocInXml                     import ExportPrimaryDocInXml
from Exchange.ExportRbComplain                          import ExportRbComplain
from Exchange.ExportRbDiagnosticResult                  import ExportRbDiagnosticResult
from Exchange.ExportRbResult                            import ExportRbResult
from Exchange.ExportRbService                           import ExportRbService
from Exchange.ExportRbPrintTemplate                     import ExportRbPrintTemplate
from Exchange.ExportRbThesaurus                         import ExportRbThesaurus
from Exchange.ExportRbUnit                              import ExportRbUnit
from Exchange.ExportSanAviacInfoDialog                  import CExportSanAviacInfoDialog
from Exchange.ExportXmlEmc                              import ExportXmlEmc
from Exchange.ImportRbPrintTemplate                     import ImportRbPrintTemplate
from Exchange.ImportSPR import ImportSPR
from Exchange.Import131Errors                           import Import131Errors
from Exchange.ImportCSVClient                           import  ImportCSVClient
from Exchange.ImportVMPCases                            import ImportVMPCases
from Exchange.Import131                                 import Import131
from Exchange.Import131XML                              import Import131XML
from Exchange.ImportActions                             import ImportActionType
from Exchange.ImportActionTemplate                      import ImportActionTemplate
from Exchange.ImportDD                                  import ImportDD
from Exchange.ImportEISOMS_Clients                      import importClientsFromEisOms
from Exchange.ImportEISOMS_LPU                          import ImportEISOMS_LPU
from Exchange.ImportEISOMS_SMO                          import ImportEISOMS_SMO
from Exchange.ImportEvents                              import ImportEventType
from Exchange.ImportFromSail                            import ImportFromSail
from Exchange.ImportFromSailXML                         import ImportFromSailXML
from Exchange.ImportLgot                                import ImportLgot
from Exchange.ImportOrgsINFIS                           import ImportOrgsINFIS
from Exchange.ImportPolicySerialDBF                     import ImportPolicySerialDBF
from Exchange.ImportPrimaryDocFromXml                   import ImportPrimaryDocFromXml
from Exchange.ImportProfiles                            import ImportProfiles
from Exchange.ImportProfilesINFIS                       import ImportProfilesINFIS
from Exchange.ImportQuotaFromVTMP                       import ImportQuotaFromVTMP
from Exchange.ImportRbComplain                          import ImportRbComplain
from Exchange.ImportRbDiagnosticResult                  import ImportRbDiagnosticResult
from Exchange.ImportRbResult                            import ImportRbResult
from Exchange.ImportRbService                           import ImportRbService
from Exchange.ImportRbThesaurus                         import ImportRbThesaurus
from Exchange.ImportRbUnit                              import ImportRbUnit
from Exchange.ImportServiceMes                          import CImportServiceMes
from Exchange.ImportServiceNomen                        import CImportServiceNomen
from Exchange.ImportRbCure                              import CImportRbCureType, CImportRbCureMethod
from Exchange.ImportRbPatientModel                      import CImportRbPatientModel
from Exchange.ReAttach                                  import CReAttach
from Exchange.Svod.SvodReportListDialog                 import CSvodReportListDialog
from Exchange.TFUnifiedIdent.Service                    import CTFUnifiedIdentService

from HealthResort.HealthResortDialog                    import CHealthResortDialog

from HospitalBeds.HospitalBedsDialog                    import CHospitalBedsDialog

from Notifications.NotificationLog                      import CNotificationLogList
from Notifications.NotificationRule                     import CNotificationRuleList

from Orgs.ActionFileAttachDialog                        import CActionFileAttach
from Orgs.Banks                                         import CBanksList
from Orgs.Contracts                                     import CContractsList
from Orgs.CreateAttachClientsForArea                    import CCreateAttachClientsForAreaDialog
from Orgs.Orgs                                          import COrgsList
from Orgs.OrgstructurePlanningHospitalBedsProfile       import CPlanningHospitalBedProfileDialog
from Orgs.PersonSubstitution                            import CPersonSubstitutionDialog
from Orgs.Utils                                         import getOrganisationInfo

from Quoting.QuotingDialog                              import CQuotingDialog

from RefBooks.AccountExportFormat.List                  import CRBAccountExportFormatList
from RefBooks.AccountingSystem.List                     import CRBAccountingSystemList
from RefBooks.AccountType.List                          import CRBAccountTypeList
from RefBooks.ActionPropertyTemplate.List               import CActionPropertyTemplateList
from RefBooks.ActionShedule.List                        import CRBActionSheduleList
from RefBooks.ActionSpecification.List                  import CRBActionSpecificationList
from RefBooks.ActionTemplate.List                       import CActionTemplateList
from RefBooks.ActionTypeGroup.List                      import CRBActionTypeGroupAppointment
from RefBooks.ActionType.List                           import CActionTypeList
from RefBooks.Activity.List                             import CRBActivityList
from RefBooks.AgreementType.List                        import CRBAgreementTypeList
from RefBooks.AnatomicalLocalizations.List              import CRBAnatomicalLocalizationsList
from RefBooks.AppointmentPurpose.List                   import CRBAppointmentPurposeList
from RefBooks.AttachType.List                           import CRBAttachTypeList
from RefBooks.BlankType.List                            import CBlankTypeList
from RefBooks.BloodType.List                            import CRBBloodTypeList
from RefBooks.CashOperation.List                        import CRBCashOperationList
from RefBooks.ClientConsentType.List                    import CRBClientConsentTypeList
from RefBooks.ClientWorkPost.List                       import CRBClientWorkPostList
from RefBooks.Complain.List                             import CRBComplainList
from RefBooks.ContactType.List                          import CRBContactTypeList
from RefBooks.ContainerType.List                        import CRBContainerTypeList
from RefBooks.ContingentKind.List                       import CRBContingentKindList
from RefBooks.ContingentKindRemoval.List                import CRBContingentKindRemovalList
from RefBooks.ContingentType.List                       import CRBContingentTypeList
from RefBooks.ContractAttributeType.List                import CRBContractAttributeTypeList
from RefBooks.ContractCoefficientType.List              import CRBContractCoefficientTypeList
from RefBooks.Counter.List                              import CRBCounterList
from RefBooks.CureMethod.List                           import CRBCureMethod
from RefBooks.CureType.List                             import CRBCureType
from RefBooks.DeathReason.List                          import CRBDeathReasonList
from RefBooks.DiagnosisType.List                        import CRBDiagnosisTypeList
from RefBooks.DiagnosticResult.List                     import CRBDiagnosticResultList
from RefBooks.DiagnosticService.List                    import CRBDiagnosticServiceList
from RefBooks.Diet.List                                 import CRBDiet
from RefBooks.DiseaseCharacter.List                     import CRBDiseaseCharacterList
from RefBooks.DiseasePhase.List                         import CRBDiseasePhaseList
from RefBooks.DiseaseStage.List                         import CRBDiseaseStageList
from RefBooks.Dispanser.List                            import CRBDispanserList
from RefBooks.DocumentTypeForTracking.List              import CRBDocumentTypeForTrackingList
from RefBooks.DocumentTypeGroup.List                    import CRBDocumentTypeGroupList
from RefBooks.DocumentType.List                         import CRBDocumentTypeList
from RefBooks.EmergencyAccident.List                    import CRBEmergencyAccidentList
from RefBooks.EmergencyBrigade.List                     import CRBEmergencyBrigadeList
from RefBooks.EmergencyCauseCall.List                   import CRBEmergencyCauseCallList
from RefBooks.EmergencyDeath.List                       import CRBEmergencyDeathList
from RefBooks.EmergencyDiseased.List                    import CRBEmergencyDiseasedList
from RefBooks.EmergencyEbriety.List                     import CRBEmergencyEbrietyList
from RefBooks.EmergencyMethodTransportation.List        import CRBEmergencyMethodTransportationList
from RefBooks.EmergencyPlaceCall.List                   import CRBEmergencyPlaceCallList
from RefBooks.EmergencyPlaceReceptionCall.List          import CRBEmergencyPlaceReceptionCallList
from RefBooks.EmergencyReasondDelays.List               import CRBEmergencyReasondDelaysList
from RefBooks.EmergencyReceivedCall.List                import CRBEmergencyReceivedCallList
from RefBooks.EmergencyResult.List                      import CRBEmergencyResultList
from RefBooks.EmergencyTransferredTransportation.List   import CRBEmergencyTransferredTransportationList
from RefBooks.EmergencyTypeAsset.List                   import CRBEmergencyTypeAssetList
from RefBooks.EquipmentClass.List                       import CRBEquipmentClassList
from RefBooks.Equipment.List                            import CRBEquipmentList
from RefBooks.EquipmentType.List                        import CRBEquipmentTypeList
from RefBooks.EventProfile.List                         import CRBEventProfileList
from RefBooks.EventType.List                            import CEventTypeList
from RefBooks.EventTypePurpose.List                     import CRBEventTypePurposeList
from RefBooks.ExpenseServiceItem.List                   import CRBExpenseServiceItemList
from RefBooks.ExtraDataDef.List                         import CExtraDataDefList
from RefBooks.Finance.List                              import CRBFinanceList
from RefBooks.FinanceSource.List                        import CRBFinanceSourceList
from RefBooks.HealthGroup.List                          import CRBHealthGroupList
from RefBooks.HospitalBedProfile.List                   import CRBHospitalBedProfileList
from RefBooks.HurtFactorType.List                       import CRBHurtFactorTypeList
from RefBooks.HurtType.List                             import CRBHurtTypeList
from RefBooks.ImageMap.List                             import CRBImageMapList
from RefBooks.Infection.List                            import CRBInfectionList
from RefBooks.Ingredient.List                           import CRBIngredientList
from RefBooks.JobPurpose.List                           import CRBJobPurposeList
from RefBooks.JobType.List                              import CRBJobTypeList
from RefBooks.KLADRMilitaryUnit.List                    import CKLADRMilitaryUnitList
from RefBooks.Laboratory.List                           import CRBLaboratoryList
from RefBooks.LfForm.List                               import CRBLfFormList
from RefBooks.LivingArea.List                           import CRBLivingAreaList
from RefBooks.LocationCardType.List                     import CRBLocationCardTypeList
from RefBooks.Login.List                                import CLoginListDialog
from RefBooks.MealTime.List                             import CRBMealTime
from RefBooks.MedicalAidKind.List                       import CRBMedicalAidKindList
from RefBooks.MedicalAidProfile.List                    import CRBMedicalAidProfileList
from RefBooks.MedicalAidType.List                       import CRBMedicalAidTypeList
from RefBooks.MedicalAidUnit.List                       import CRBMedicalAidUnitList
from RefBooks.MedicalBoardExpertiseArgument.List        import CRBMedicalBoardExpertiseArgument
from RefBooks.MedicalBoardExpertiseCharacter.List       import CRBMedicalBoardExpertiseCharacter
from RefBooks.MedicalBoardExpertiseKind.List            import CRBMedicalBoardExpertiseKind
from RefBooks.MedicalBoardExpertiseObject.List          import CRBMedicalBoardExpertiseObject
from RefBooks.MedicalExemptionType.List                 import CRBMedicalExemptionTypeList
from RefBooks.MedicalExemptionReason.List               import CRBMedicalExemptionReasonList
from RefBooks.Menu.List                                 import CRBMenu
from RefBooks.MesSpecification.List                     import CRBMesSpecificationList
from RefBooks.Metastasis.List                           import CRBMetastasisList
from RefBooks.MKBExSubclass.List                        import CMKBExSubclass
from RefBooks.MKB.List                                  import CMKBList
from RefBooks.MKBMorphology.List                        import CRBMKBMorphologyList
from RefBooks.MKBSubclass.List                          import CMKBSubclass
from RefBooks.Net.List                                  import CRBNetList
from RefBooks.Nodus.List                                import CRBNodusList
from RefBooks.NomenclatureClass.List                    import CRBNomenclatureClassList
from RefBooks.NomenclatureKind.List                     import CRBNomenclatureKindList
from RefBooks.Nomenclature.List                         import CRBNomenclatureList
from RefBooks.NomenclatureUsingType.List                import CRBNomenclatureUsingTypeList
from RefBooks.DisposalMethod.List                       import CRBDisposalMethod
from RefBooks.NomenclatureType.List                     import CRBNomenclatureTypeList
from RefBooks.NomenclatureActiveSubstance.List          import CRBNomenclatureActiveSubstanceList
from RefBooks.NomenclatureActiveSubstanceGroups.List    import CRBNomenclatureActiveSubstanceGroupsList
from RefBooks.NotificationKind.List                     import CRBNotificationKindList
from RefBooks.OKFS.List                                 import CRBOKFSList
from RefBooks.OKPF.List                                 import CRBOKPFList
from RefBooks.OrgStructure.List                         import COrgStructureList
from RefBooks.PatientModel.List                         import CRBPatientModel
from RefBooks.PayRefuseType.List                        import CRBPayRefuseTypeList
from RefBooks.Person.List                               import CPersonList
from RefBooks.PlanningHealthResortActivity.List         import CRBPlanningHealthResortActivity
from RefBooks.PlanningHospitalActivity.List             import CRBPlanningHospitalActivityList
from RefBooks.PolicyKind.List                           import CRBPolicyKindList
from RefBooks.PolicyType.List                           import CRBPolicyTypeList
from RefBooks.Post.List                                 import CRBPostList
from RefBooks.PostOnAppointment.List                    import CPostOnAppointmentList
from RefBooks.PrikCoefType.List                         import CRBPrikCoefTypeList
from RefBooks.PrintTemplate.List                        import CRBPrintTemplate
from RefBooks.ProphylaxisPlanningType.List              import CRBProphylaxisPlanningType
from RefBooks.QuotaType.List                            import CQuotaTypeList
from RefBooks.RBFmsUnit                                 import CRBFmsUnitList
from RefBooks.Reaction.List                             import CRBReactionList
from RefBooks.ReactionType.List                         import CRBReactionTypeList
from RefBooks.ReactionManifestation.List                import CRBReactionManifestationList
from RefBooks.ReasonOfAbsence.List                      import CRBReasonOfAbsenceList
from RefBooks.Relative.List                             import CRBRelativeList
from RefBooks.ResearchArea.List                         import CRBResearchAreaList
from RefBooks.ResearchKind.List                         import CRBResearchKindList
from RefBooks.Result.List                               import CRBResultList
from RefBooks.RiskFactor.List                           import CRBRiskFactor
from RefBooks.Scene.List                                import CRBSceneList
from RefBooks.ServiceGroup.List                         import CRBServiceGroupList
from RefBooks.Service.List                              import CRBServiceList
from RefBooks.ServiceType.List                          import CRBServiceTypeList
from RefBooks.SocStatusClass.List                       import CRBSocStatusClassList
from RefBooks.SocStatusType.List                        import CRBSocStatusTypeList
from RefBooks.Speciality.List                           import CRBSpecialityList
from RefBooks.SpecimenType.List                         import CRBSpecimenTypeList
from RefBooks.SRSUser.List                              import CSRSUserList
from RefBooks.StatusObservationClientType.List          import CRBStatusObservationClientTypeList
from RefBooks.StockMotionItemReason.List                import getStockMotionItemReasonDialog
from RefBooks.StockMotionNumber.List                    import CRBStockMotionNumberList
from RefBooks.StockRecipe.List                          import CRBStockRecipeList
from RefBooks.SuiteReagent.List                         import CRBSuiteReagentList
from RefBooks.SurveillanceRemoveReason.List             import CRBSurveillanceRemoveReasonList
from RefBooks.ObservationGroup.List                     import CRBObservationGroupList
from RefBooks.ObservationSubgroup.List                  import CRBObservationSubgroupList
from RefBooks.TariffCategory.List                       import CRBTariffCategoryList
from RefBooks.TempInvalidAnnulmentReason.List           import CRBTempInvalidAnnulmentReasonList
from RefBooks.TempInvalidBreak.List                     import CRBTempInvalidBreakList
from RefBooks.TempInvalidDocument.List                  import CRBTempInvalidDocumentList
from RefBooks.TempInvalidDuplicateReason.List           import CRBTempInvalidDuplicateReasonList
from RefBooks.TempInvalidExtraReason.List               import CRBTempInvalidExtraReasonList
from RefBooks.TempInvalidReason.List                    import CRBTempInvalidReasonList
from RefBooks.TempInvalidRegime.List                    import CRBTempInvalidRegimeList
from RefBooks.TempInvalidResult.List                    import CRBTempInvalidResultList
from RefBooks.TestGroup.List                            import CRBTestGroupList
from RefBooks.Test.List                                 import CRBTestList
from RefBooks.Thesaurus.List                            import CRBThesaurus
from RefBooks.TissueType.List                           import CRBTissueTypeList
from RefBooks.TNMPhase.List                             import CRBTNMPhaseList
from RefBooks.TraumaType.List                           import CRBTraumaTypeList
from RefBooks.ToxicSubstances.List                      import CRBToxicSubstancesList
from RefBooks.TreatmentType.List                        import CTreatmentTypeList
from RefBooks.Tumor.List                                import CRBTumorList
from RefBooks.Unit.List                                 import CRBUnitList
from RefBooks.VaccinationCalendar.List                  import CRBVaccinationCalendarList
from RefBooks.VaccinationProbe.List                     import CRBVaccinationProbeList
from RefBooks.VaccinationResult.List                    import CRBVaccinationResultList
from RefBooks.Vaccine.List                              import CRBVaccineList
from RefBooks.VaccineSchemaTransitionType.List          import CRBVaccineSchemaTransitionTypeList
from RefBooks.VisitType.List                            import CRBVisitTypeList
from RefBooks.DeathPlaceType.List                       import CRBDeathPlaceTypeList
from RefBooks.DeathCauseType.List                       import CRBDeathCauseTypeList
from RefBooks.EmployeeTypeDeterminedDeathCause.List     import CRBEmployeeTypeDeterminedDeathCauseList
from RefBooks.GroundsForDeathCause.List                 import CRBGroundsForDeathCauseList

from Registry.DemogrCertificates                        import CDemogrCertificatesDialog
from Registry.DiagnosisDock                             import CDiagnosisDockWidget
from Registry.DispExchange                              import CDispExchangeWindow
from Registry.DistantMonitoringWindow                   import CDistantMonitoringWindow
from Registry.FreeQueueDock                             import CFreeQueueDockWidget
from Registry.HomeCallRequestsWindow                    import CHomeCallRequestsWindow
from Registry.IdentCard.EkpBarCode                      import tryCardIdAsEkpIdentCard
from Registry.IdentCard.PolicyBarCode                   import policyBarCodeAsIdentCard
from Registry.IdentCard.smartCardAsIdentCard            import smartCardAsIdentCard
from Registry.ProphylaxisPlanning                       import CProphylaxisPlanningWindow
from Registry.RegistryWindow                            import CRegistryWindow
from Registry.ResourcesDock                             import CResourcesDockWidget
from Registry.SMPDock                                   import CSMPDockWidget
from Registry.SuspendedAppointment                      import CSuspenedAppointmentWindow
from Registry.UnlockAppLockDialog                       import CUnlockAppLockDialog
from Registry.IdentityPatientService                    import CIdentityPatientServiceDialog
from Registry.AttachOnlineService                       import CAttachOnlineServiceDialog
from Registry.CorrectorOutdatedStreets                  import CCorrectorOutdatedStreets

from Reports.ActDeattachCheckReport                     import CActDeattachCheckReport
from Reports.ActionPropertiesTestsReport                import CActionPropertiesTestsReport
from Reports.ActReconciliationMutualSettlements         import CActReconciliationMutualSettlements
from Reports.ActReportPatientSchoolJournal              import CactReportPatientSchoolJournal
from Reports.ActReportMonthlySchoolJournal              import CactReportMonthlySchoolJournal
from Reports.Analitic_referralMSE                       import CAnalitic_referralMSE
from Reports.AnaliticReportsAdditionalSurgery           import CAnaliticReportsAdditionalSurgery
from Reports.AnaliticReportsChildrenLeaved              import CAnaliticReportsChildrenLeaved
from Reports.AnaliticReportsDeathStationary             import CAnaliticReportsDeathStationary
from Reports.AnaliticReportsGeneralInfoSurgery          import CAnaliticReportsGeneralInfoSurgery
from Reports.AnaliticReportsStationary                  import CAnaliticReportsStationary
from Reports.AnaliticReportsSurgery                     import CAnaliticReportsSurgery
from Reports.AnaliticReportsSurgeryStationary           import CAnaliticReportsSurgeryStationary
from Reports.AnalyticsExecutionMes                      import showCheckMesDescription
from Reports.AnalyticsReportHospitalizedClients         import CAnalyticsReportHospitalizedClients
from Reports.AnalyticsReportIncomeAndLeavedClients      import CAnalyticsReportIncomeAndLeavedClients
from Reports.Attach_IEMK_EGISZ                          import CAttach_IEMK_EGISZ
from Reports.Attach_SEMD_IEMK                           import CAttach_SEMD_IEMK
from Reports.AttachedContingent                         import CAttachedContingent
from Reports.AttachmentList                             import CAttachmentListReport
from Reports.AttachmentBySmo                            import CAttachmentBySmoReport
from Reports.BySMOContingent                            import CBySMOContingent
from Reports.ClientNomenclatureActionReport             import CClientNomenclatureActionReport
from Reports.ClientNomenclatureInvoiceReport            import CClientNomenclatureInvoiceReport
from Reports.CountByOms                                 import CCountByOms
from Reports.DailyJournalBeforeRecord                   import CDailyJournalBeforeRecord, CDailyJournalBeforeRecord2
from Reports.DailyReportPreRecord                       import CDailyReportPreRecord
from Reports.DeathList                                  import CDeathList
from Reports.DeathReportByZones                         import CDeathReportByZones, CDetailedDeathReportByZones
from Reports.DeathReport                                import CDeathReport
from Reports.DeathSurvey                                import CDeathSurvey
from Reports.DeAttachmentList                           import CDeAttachmentListReport
from Reports.DiagnosisDispansPlanedList                 import CDiagnosisDispansPlanedListReport, CDiagnosisDispansNoVisitReport
from Reports.DiagnosticYearReport                       import CDiagnosticYearReport
from Reports.DispansList import CDispansListReport
from Reports.DispObservationList                        import CDispObservationList
from Reports.DispObservationPriorityListReport import CDispObservationPriorityListReport
from Reports.DispObservationSurvey                      import CDispObservationSurvey
from Reports.DispReport                                 import CDispReport
from Reports.EconomicAnalisysE1                         import CEconomicAnalisysE1Ex
from Reports.EconomicAnalisysE2                         import CEconomicAnalisysE2Ex
from Reports.EconomicAnalisysE3                         import CEconomicAnalisysE3Ex
from Reports.EconomicAnalisysE4                         import CEconomicAnalisysE4Ex
from Reports.EconomicAnalisysE5                         import CEconomicAnalisysE5Ex
from Reports.EconomicAnalisysE6                         import CEconomicAnalisysE6Ex
from Reports.EconomicAnalisysE7                         import CEconomicAnalisysE7Ex
from Reports.EconomicAnalisysE8                         import CEconomicAnalisysE8Ex
from Reports.EconomicAnalisysE9                         import CEconomicAnalisysE9Ex
from Reports.EconomicAnalisysE10                        import CEconomicAnalisysE10Ex
from Reports.EconomicAnalisysE11                        import CEconomicAnalisysE11Ex
from Reports.EconomicAnalisysE12                        import CEconomicAnalisysE12Ex
from Reports.EconomicAnalisysE13                        import CEconomicAnalisysE13Ex
from Reports.EconomicAnalisysE14                        import CEconomicAnalisysE14Ex
from Reports.EconomicAnalisysE15                        import CEconomicAnalisysE15Ex
from Reports.EconomicAnalisysE16                        import CEconomicAnalisysE16Ex
from Reports.EconomicAnalisysE17                        import CEconomicAnalisysE17Ex
from Reports.EconomicAnalisysE19                        import CEconomicAnalisysE19Ex
from Reports.EconomicAnalisysE23                        import CEconomicAnalisysE23Ex
from Reports.EconomicAnalisysE24                        import CEconomicAnalisysE24Ex
from Reports.EconomicAnalisysE26                        import CEconomicAnalisysE26Ex
from Reports.EconomicAnalisysECO                        import CEconomicAnalisysECOEx
from Reports.EconomicAnalisysFinOtd                     import CEconomicAnalisysFinOtdEx
from Reports.EconomicAnalisysForeignCitizens            import CEconomicAnalisysForeignCitizensEx
from Reports.EconomicAnalisysP10                        import CEconomicAnalisysP10Ex
from Reports.EconomicAnalisysP11                        import CEconomicAnalisysP11Ex
from Reports.EmergencySurgicalCare7Nosologies           import CEmergencySurgicalCare7Nosologies
from Reports.EventResultList                            import CReportEventResultList
from Reports.EventResultSurvey                          import CEventResultSurvey
from Reports.FactorRateSurvey                           import CFactorRateSurvey
from Reports.FinanceSumByServicesExpenses               import CFinanceSumByServicesExpensesEx
from Reports.FinanceSummaryByDoctors                    import CFinanceSummaryByDoctorsEx
from Reports.FinanceSummaryByDoctorsOld                 import CFinanceSummaryByDoctorsExOld
from Reports.FinanceSummaryByOrgStructures              import CFinanceSummaryByOrgStructuresEx
from Reports.FinanceSummaryByRejections                 import CFinanceSummaryByRejectionsEx
from Reports.FinanceSummaryByServices                   import CFinanceSummaryByServicesEx
from Reports.FinanceReportByAidProfileAndSocStatus      import CFinanceReportByAidProfileAndSocStatus
from Reports.ReportPaidServices                         import CReportPaidServices
from Reports.FinOtch                                    import CFinOtchEx
from Reports.FinReestr                                  import CFinReestr
from Reports.Form10                                     import CForm10_2000, CForm10_3000
from Reports.Form11                                     import CForm11_1000, CForm11_2000, CForm11_4000
from Reports.Form12                                     import CForm12_1000_1100, CForm12_1500_1900, CForm12_2000_2100, CForm12_3000_3100, CForm12_4000_4100
from Reports.Form19                                     import CStatReportF19_1000, CStatReportF19_2000, CStatReportF19_1000_Psychiatry, CStatReportF19_2000_Psychiatry
from Reports.Form36_2100_2190                           import CForm36_2100_2190
from Reports.Form36_2200_2210                           import CForm36_2200_2210
from Reports.Form36_2300_2340                           import CForm36_2300_2340
from Reports.Form36_2400                                import CForm36_2400
from Reports.Form36_2500                                import CForm36_2500
from Reports.Form36_2600                                import CForm36_2600
from Reports.Form36_2800                                import CForm36_2800
from Reports.Form36_2900                                import CForm36_2900
from Reports.Form36PL_2100_2190                         import CForm36PL_2100_2190
from Reports.Form36PL_2200_2240                         import CForm36PL_2200_2240
from Reports.Form37                                     import CForm37_2100_2170
from Reports.Form37_2200_2210                           import CForm37_2200_2210
from Reports.Form37_2300_2330                           import CForm37_2300_2330
from Reports.FormOS6                                    import CFormOS6
from Reports.JournalBeforeRecordDialog                  import CJournalBeforeRecordEx, CJournalBeforeRecordAV
from Reports.LgotRecipe                                 import CLgotRecip
from Reports.MonthlyNomenclatureReport                  import CMonthlyNomenclatureReport
from Reports.MUOMSOFCity                                import CMUOMSOFCity
from Reports.MUOMSOFForeign                             import CMUOMSOFForeign
from Reports.MUOMSOFTable1                              import CMUOMSOFTable1
from Reports.MUOMSOFTable3                              import CMUOMSOFTable3
from Reports.NomenclatureBook                           import CNomenclatureBook
from Reports.ReportNoProfsChild                         import CNoProfsChild
from Reports.OutgoingDirectionsReport                   import COutgoingDirectionsReport
from Reports.PaidServices                               import CPaidServices
from Reports.PersonVisits                               import CPersonVisits
from Reports.PersonParusCheck                           import CPersonParusCheckReport
from Reports.PlannedClientInvoiceNomenclaturesReport    import CPlannedClientInvoiceNomenclaturesReport
from Reports.PopulationStructure                        import CPopulationStructure
from Reports.PreRecordClientsCard                       import CPreRecordClientsCard
from Reports.PreRecordDoctors                           import CPreRecordDoctorsEx
from Reports.PreRecordPlanExecutionByDoctors            import CPreRecordPlanExecutionByDoctors
from Reports.PreRecordSpeciality                        import CPreRecordSpecialityEx
from Reports.PreRecordUsers                             import CPreRecordUsersEx
from Reports.ProfileYearReport                          import CProfileYearReport
from Reports.RepKarta                                   import CKarta_Expert
from Reports.RepHospital                                import CHospital
from Reports.RepNaprGospital                            import CNaprGosp
from Reports.RepNullHospital                            import CNullHospital
from Reports.RepODLI                                    import CODLI
from Reports.Report060Y                                 import CRep060Y
from Reports.ReportEMD                                  import CReportEMD
from Reports.ReportEventCasesVerification               import CReportEventCasesVerification
from Reports.ReportAccountDoneActions                   import CReportAccountDoneActions
from Reports.ReportActionsByOrgStructure                import CReportActionsByOrgStructure
from Reports.ReportActionsByServiceType                 import CReportActionsByServiceType
from Reports.ReportActions                              import CReportActions
from Reports.ReportActionsServiceCutaway                import CReportActionsServiceCutaway
from Reports.ReportAcuteInfections                      import CReportAcuteInfections
from Reports.ReportAddressFound                         import CAddressFound
from Reports.ReportAstheniaResults                      import CReportAstheniaResults
from Reports.ReportAttachingMotion                      import CReportAttachingMotion
from Reports.ReportBIRADS                               import CReportBIRADS
from Reports.ReportBreachSA                             import CReportBreachSA
from Reports.ReportClientActions                        import CReportClientActions
from Reports.ReportClientNomenclaturePlan               import CReportClientNomenclaturePlan
from Reports.ReportClients                              import CReportClients
from Reports.ReportClientSummary                        import CReportClientSummary
from Reports.ReportClientTreatmentsStructure            import CClientTreatmentsStructureReport
from Reports.ReportCost                                 import CReportCost
from Reports.ReportDailyAcuteInfections                 import CReportDailyAcuteInfections, CReportDailyAcuteInfectionsHospital
from Reports.ReportDailyCash                            import CReportDailyCash
from Reports.ReportDirectionActions                     import CReportDirectionActions
from Reports.ReportDiseasesResult                       import CReportDiseasesResult
from Reports.ReportDispansMO_1_1                        import CReportDispansMO_1_1
from Reports.ReportDoctor                               import CReportDoctor
from Reports.ReportDoctorPreCalc                        import CReportDoctorPreCalc
from Reports.ReportDoctorSummary                        import CReportDoctorSummary
from Reports.ReportDoneActions                          import CReportApproxDoneActions
from Reports.ReportEmergencyCallList                    import CReportEmergencyCallList
from Reports.ReportSMPDockList                          import CReportSMPDockList
from Reports.ReportEmergencyF30                         import CReportEmergencyF302350
from Reports.ReportEmergencyF40                         import CReportEmergencyAdditionally, CReportEmergencyF402000, CReportEmergencyF302120, CReportEmergencyF402001, CReportEmergencyF402100, CReportEmergencyF402500, CReportEmergencyF40TimeIndicators, CReportEmergencyTalonSignal
from Reports.ReportEmergencySize                        import CEmergencySizeReport
from Reports.ReportExternalDirections                   import CExternalOutgoingDirectionsReport
from Reports.ReportExternalIncomePaidServices           import CExternalIncomePaidServices
from Reports.ReportF035                                 import CForm035
from Reports.ReportF14App3ksg                           import CReportF14App3ksg
from Reports.ReportF1children                           import CReportF1_1000, CReportF1_2000
from Reports.ReportF1RB                                 import CReportF1RB_2000, CReportF1RB_AmbulatoryCare, CReportF1RB_DentalTreatment, CReportF1RB_AmbulanceCall
from Reports.ReportF30_1050                             import CReportF30_1050
from Reports.ReportF30_2100                             import CReportF30_2100
from Reports.ReportF30_2110                             import CReportF30_2110
from Reports.ReportF30_2510                             import CReportF30_2510
from Reports.ReportF30                                  import CReportF30
from Reports.ReportF30_SMP                              import CReportF30_SMP
from Reports.ReportF30KK_2100                           import CReportF30KK_2100
from Reports.ReportF39                                  import CReportF39
from Reports.ReportF62_4000                             import CReportF62_4000
#from Reports.ReportF62_7000                             import CReportF62_7000
from Reports.ReportForm131_o_1000_2014                  import CReportForm131_o_1000_2014
from Reports.ReportForm131_o_1000_2015                  import CReportForm131_o_1000_2015
from Reports.ReportForm131_o_1000_2015_16               import CReportForm131_o_1000_2015_16
from Reports.ReportForm131_o_1000_2016                  import CReportForm131_o_1000_2016
from Reports.ReportForm131_o_1000_2021                  import CReportForm131_o_1000_2021
from Reports.ReportForm131_o_2000_2014                  import CReportForm131_o_2000_2014
from Reports.ReportForm131_o_2000_2015                  import CReportForm131_o_2000_2015
from Reports.ReportForm131_o_2000_2016                  import CReportForm131_o_2000_2016
from Reports.ReportForm131_o_2000_2019                  import CReportForm131_o_2000_2019
from Reports.ReportForm131_o_2000_2021                  import CReportForm131_o_2000_2021
from Reports.ReportForm131_o_3000_2014                  import CReportForm131_o_3000_2014
from Reports.ReportForm131_o_3000_2015                  import CReportForm131_o_3000_2015
from Reports.ReportForm131_o_3000_2016                  import CReportForm131_o_3000_2016
from Reports.ReportForm131_o_3000_2019                  import CReportForm131_o_3000_2019
from Reports.ReportForm131_o_3000_2021                  import CReportForm131_o_3000_2021
from Reports.ReportForm131_o_4000_2014                  import CReportForm131_o_4000_2014
from Reports.ReportForm131_o_4000_2015                  import CReportForm131_o_4000_2015
from Reports.ReportForm131_o_4000_2016                  import CReportForm131_o_4000_2016
from Reports.ReportForm131_o_4000_2021                  import CReportForm131_o_4000_2021
from Reports.ReportForm131_o_5000_2014                  import CReportForm131_o_5000_2014, CReportForm131_o_6000_2014
from Reports.ReportForm131_o_5000_2015                  import CReportForm131_o_5000_2015, CReportForm131_o_5001_2015, CReportForm131_o_6000_2015
from Reports.ReportForm131_o_5000_2016                  import CReportForm131_o_5000_2016, CReportForm131_o_5001_2016, CReportForm131_o_6000_2016
from Reports.ReportForm131_o_5000_2021                  import CReportForm131_o_5000_2021
from Reports.ReportForm131_o_6000_2021                  import CReportForm131_o_6000_2021
from Reports.ReportForm131_o_7000_2014                  import CReportForm131_o_7000_2014
from Reports.ReportForm131_o_7000_2015                  import CReportForm131_o_7000_2015
from Reports.ReportForm131_o_7000_2016                  import CReportForm131_o_7000_2016
from Reports.ReportForm30                               import CRepForm30
from Reports.ReportHealthResortAnalysisUsePlacesRegions import CReportHealthResortAnalysisUsePlacesRegions
from Reports.ReportHepatitis                            import CReportHepatitis
from Reports.ReportHospDir                              import CHospDir
from Reports.ReportImunoprophylaxisForm5                import CReportImunoprophylaxisForm5
from Reports.ReportIncomingExternalDirections           import CExternalIncomingDirectionsReport
from Reports.ReportInfoPrik                             import CInfoPrik
from Reports.ReportInsuredMedicalCare                   import CReportInsuredMedicalCare
from Reports.ReportInternalDirections                   import CReportInternalDirections
from Reports.ReportInvalidGroupMovement                 import CReportInvalidGroupMovement
from Reports.ReportKolRecipe                            import CRepKolRecipe
from Reports.ReportLaboratoryActionsByMedicalType       import CReportLaboratoryActionsByMedicalType
from Reports.ReportLaboratoryAntibodiesHIV              import CReportLaboratoryAntibodiesHIV
from Reports.ReportLaboratoryProbeExportImport          import CReportLaboratoryProbeExportImport
from Reports.ReportLengthOfStayInHospital               import CReportLengthOfStayInHospital
from Reports.ReportLgot030P                             import CLgot030
from Reports.ReportLgotL30                              import CReportLgotL30
from Reports.ReportLgotRecipe                           import CRepLgotRecipe
from Reports.ReportMonitoringReabilityInvalid           import CReportMonitoringReabilityInvalid
from Reports.ReportMonthActions                         import CReportMonthActions
from Reports.ReportMovingAndBeds                        import CReportMovingAndBeds
from Reports.ReportNomenclaureMotions                   import CReportNomenclaureMotions
from Reports.ReportNumberInsuredPersonsSMO              import CReportNumberInsuredPersonsSMO
from Reports.ReportNumberResidentsAddress               import CReportNumberResidentsAddress
from Reports.ReportOnPerson                             import CReportOnPerson
from Reports.ReportOnServiceType                        import CReportOnServiceType
from Reports.ReportOperationalMonitoring                import CReportOperationalMonitoring
from Reports.ReportAFT_002                              import CReportAFT_002
from Reports.ReportAFT_Forecast12month                  import CReportAFT_Forecast12month
from Reports.ReportStomPersonSalary                     import CReportStomPersonSalaryEx
from Reports.ReportOrgStructureSummary                  import CReportOrgStructureSummary
from Reports.ReportPayers                               import CReportPayers
from Reports.ReportPayersWithFinance                    import CReportPayersWithFinance
from Reports.ReportPeopleOfCancer import CPeopleOfCancer
from Reports.ReportPeopleWithDiseasesCirculatorySystem import CPeopleWithDiseasesCirculatorySystem
from Reports.ReportPersonSickList                       import CReportPersonSickList
from Reports.ReportPersonSickListStationary             import CReportPersonSickListStationary
from Reports.ReportPGG                                  import CReportPGG
from Reports.ReportPollAgeIsNotHindrance                import CReportPollAgeIsNotHindrance
from Reports.ReportPolyclinicsOthersPersonList          import CReportPolyclinicsOthersPersonList
from Reports.ReportPos                                  import CRepPos
from Reports.ReportPlatUsl                              import CRepPlatUsl
from Reports.ReportProtozoa                             import CReportProtozoa
from Reports.ReportRoadMap                              import CReportRoadMap
from Reports.ReportSanatoriumArrivalDiary               import CReportSanatoriumArrivalDiary
from Reports.ReportSanatoriumArrived                    import CReportSanatoriumArrived
from Reports.ReportSanatoriumResidents                  import CReportSanatoriumResidents
from Reports.ReportScheduleRegisteredCount              import CReportScheduleRegisteredCount
from Reports.ReportsBeingInStationary                   import CReportsBeingInStationary
from Reports.ReportServicesMonitoredContingent          import CReportServicesMonitoredContingent
from Reports.ReportSMOClients                           import CReportSMOClients
# from Reports.ReportStacKoyka                            import CReportStacKoyka
from Reports.ReportStomatF30_2700_2015                  import CReportStomatF30_2700_2015
from Reports.ReportStomatF30_2700                       import CReportStomatF30_2700, CReportStomatF30_2710
from Reports.ReportStomatF39_3                          import CReportStomatF39_3
from Reports.ReportStomatSummary                        import CReportStomatSummary
from Reports.ReportSummaryClientNotApply import CReportSummaryClientNotApply
from Reports.ReportSummaryOnAccounts                    import CReportSummaryOnAccounts
from Reports.ReportSummaryOnServices                    import CReportSummaryOnServices
from Reports.ReportSummaryPos                           import CReportSummaryPosEx
from Reports.ReportSurgeryPlanDay                       import CReportSurgeryPlanDay
from Reports.ReportTraumaAnimalBites                    import CReportTraumaAnimalBites
from Reports.ReportTraumaGypsum                         import CReportTraumaGypsum
from Reports.ReportTraumaHospitalization                import CReportTraumaHospitalization
from Reports.ReportTraumaIce                            import CReportTraumaIce
from Reports.ReportTraumaJournalVaccinations            import CReportTraumaJournalVaccinations
from Reports.ReportTraumaMiteBites                      import CReportTraumaMiteBites
from Reports.ReportTraumaOperations                     import CReportTraumaOperations
from Reports.ReportTraumaTelephoneMessage               import CReportTraumaTelephoneMessage
from Reports.ReportTraumaWorkInjury                     import CReportTraumaWorkInjury
from Reports.ReportTreatedPatientsForComorbidities      import CReportTreatedPatientsForComorbidities
from Reports.ReportTreatedPatientsForMajorDiseases      import CReportTreatedPatientsForMajorDiseases
from Reports.ReportTreatments                           import CReportTreatments
from Reports.ReportUETActions                           import CReportUETActionByActions, CReportUETActionByPersons
from Reports.ReportUniversalEventList                   import CReportUniversalEventList
from Reports.ReportActivityMO                           import CReportActivityMO
from Reports.ReportUseContainers                        import CReportUseContainers
from Reports.ReportVaccineJournal                       import CReportVaccineJournal
from Reports.ReportVaccineTuberculin                    import CReportVaccineAndTuberculinTestJournal
from Reports.ReportVisitByPurposeEvents                 import CReportVisitByPurposeEvents
from Reports.ReportVisitByQueue                         import CReportVisitBySchedule, CReportVisitByNextEventDate
from Reports.ReportVisitsServiceCutaway                 import CReportVisitsServiceCutaway
from Reports.ReportWorkloadOfMedicalStaff               import CReportWorkloadOfMedicalStaff
from Reports.ReportEventList                            import CReportEventList
from Reports.ReportPrimaryClientList                    import CReportPrimaryClientList
from Reports.ReportYearActions                          import CReportYearActions
from Reports.RepJournalNapr                             import CRepJournalNapr
from Reports.RepOpSpecSlujb                             import CSpec_Journal
from Reports.RepReestrUsl                               import CRepReestrUslEx
from Reports.RepSanAviacExport                          import CSanAviacExport
from Reports.RepService                                 import CRepService
from Reports.RepServiceAttach                           import CRepServiceAttach
from Reports.Repsoclab                                  import CSOClab
from Reports.ServiceAverageDurationAcuteDisease         import CAverageDurationAcuteDiseaseBase
from Reports.SickRateAbort                              import CSickRateAbort
from Reports.SickRateAbort_1000                         import CSickRateAbort_1000
from Reports.SickRateAbort_2000                         import CSickRateAbort_2000
from Reports.SickRateSurvey                             import CSickRateSurvey
from Reports.SocStatus                                  import CSocStatus
from Reports.SpendingToClients                          import CSpendingToClients
from Reports.SvedVipis                                  import CSvedVipis
from Reports.ReportForm7_2000                           import CReportForm7_2000
from Reports.ReportPassportT1200                        import CReportPassportT1200
from Reports.ReportPassportT1000                        import CReportPassportT1000
from Reports.ReportPassportT1100                        import CReportPassportT1100
from Reports.StationaryDeliveryChannels                 import CDeliveryChannelsReport
from Reports.StationaryDiseasesAnalysis                 import CDiseasesAnalysisReport
from Reports.StationaryF007DS                           import CStationaryF007DSClientList, CStationaryF007DSMoving
from Reports.StationaryF007                             import CStationaryF007ClientList, CStationaryF007Moving
from Reports.StationaryF007_530                         import CStationaryF007_530ClientList, CStationaryF007_530Moving
from Reports.StationaryF014                             import CStationaryF14_4300_4301_4302, CStationaryAdultF142000, CStationaryAdultNoSeniorF142000, CStationaryChildrenF142000, CStationaryF142100, CStationaryF143000, CStationaryF144000, CStationaryF144001, CStationaryF144001A, CStationaryF144002, CStationaryF144100, CStationaryF144200, CStationaryF144201, CStationaryF144202, CStationaryF144400, CStationarySeniorF142000
from Reports.StationaryF014_2021                        import CStationaryF0144000_2021, CStationaryF144001_2021, CStationaryF144001A_2021, CStationaryF144002_2021, CStationaryF144100_2021, CStationaryF144110_2021, CStationaryF144200_2021, CStationaryF144201_2021, CStationaryF14_4300_4301_4302_2021, CStationaryF144400_2021
from Reports.StationaryF014_2022                        import CStationaryF144201_2022, CStationaryF014_2910_2022
from Reports.StationaryF14KK                            import CStationaryF14KK2000Adult, CStationaryF14KK2000Senior, CStationaryF14KK2000Children, CStationaryF14KK4000, CStationaryF14KK4001, CStationaryF14KK4100
from Reports.StationaryF016_02                          import CStationaryF016_02
from Reports.StationaryF016_02_530                      import CStationaryF016_02_530n
from Reports.StationaryF016ForPeriod                    import CStationaryF016ForPeriod
from Reports.StationaryF016                             import CStationaryF016
from Reports.StationaryF14DC                            import CStationaryOne_2015F14DC, CStationaryOneF14DC, CStationaryOneHospitalF14DC, CStationaryOneHouseF14DC, CStationaryOnePolyclinicF14DC, CStationaryTwoAdult_2015F14DC, CStationaryTwoAdultF14DC, CStationaryTwoAdultHospitalF14DC, CStationaryTwoAdultHouseF14DC, CStationaryTwoAdultPoliclinicF14DC, CStationaryTwoChildren_2015F14DC, CStationaryTwoChildrenF14DC, CStationaryTwoChildrenHospitalF14DC, CStationaryTwoChildrenHouseF14DC, CStationaryTwoChildrenPoliclinicF14DC, CStationaryTypePaymentF14DC
from Reports.Ds14kk1000                                 import CReportDs14kk1000
from Reports.Ds14kk2000                                 import CReportDs14kk2000
from Reports.Ds14kk3000                                 import CReportDs14kk3000
from Reports.Ds14kk4000                                 import CReportDs14kk4000
from Reports.StationaryF30                              import CStationaryF30_3101, CStationaryF30Moving
from Reports.StationaryF30_KK                           import CStationaryF30Moving_KK
from Reports.StationaryF036_2300                        import CStationaryF036_2300
from Reports.StationaryF36_PL                           import CStationaryF36_PL
from Reports.StationaryLengthOfStay                     import CLengthOfStayReport
from Reports.StationaryMESOneF14DC                      import CStationaryMESHospitalF14DC, CStationaryMESHouseF14DC, CStationaryMESOneF14DC, CStationaryMESPolyclinicF14DC
from Reports.StationaryPatientsCompositionByRegion      import CStationaryPatientsCompositionByRegion
from Reports.StationaryPatientsComposition              import CStationaryPatientsComposition
from Reports.StationaryPlanning                         import CStationaryPlanMoving
from Reports.StationaryReportForMIACHard                import CStationaryReportForMIACHard
from Reports.StationaryReportForMIAC                    import CStationaryReportForMIAC
from Reports.StationaryTallySheetMoving                 import CStationaryTallySheetMoving
from Reports.StationaryYearReport                       import CStationaryYearReport
from Reports.StatReport1DD1000                          import CStatReport1DD1000
from Reports.StatReport1DD2000                          import CStatReport1DD2000
from Reports.StatReport1DD3000                          import CStatReport1DD3000
from Reports.StatReport1DDAll                           import CStatReport1DDAll
from Reports.StatReport1NP2000                          import CStatReport1NP2000
from Reports.StatReport1NP3000                          import CStatReport1NP3000
from Reports.StatReport1NP4000                          import CStatReport1NP4000
from Reports.StatReport1NP5000                          import CStatReport1NP5000
from Reports.StatReport1NP7000                          import CStatReport1NP7000
from Reports.StatReportDiseaseInPermille                import CStatReportDiseaseInPermille
from Reports.StatReportEED                              import CStatReportEEDMonth, CStatReportEEDMonthSummary, CStatReportEEDPeriod, CStatReportEEDPeriodSummary, CStatReportEEDYear, CStatReportEEDYearSummary
from Reports.StatReportF12Able_2022                     import CStatReportF12Able_2022
from Reports.StatReportF12Able                          import CStatReportF12Able
from Reports.StatReportF12Adults_2022                   import CStatReportF12Adults_2022
from Reports.StatReportF12Adults                        import CStatReportF12Adults
from Reports.StatReportF12Children_2022                 import CStatReportF12Children0_14_2022, CStatReportF12Children0_1_2022
from Reports.StatReportF12Children                      import CStatReportF12Children
from Reports.StatReportF12Clients                       import CStatReportF12Clients
from Reports.StatReportF12_D_1_07                       import CStatReportF12_D_1_07
from Reports.StatReportF12_D_1_08                       import CStatReportF12_D_1_08
from Reports.StatReportF12_D_1_10                       import CStatReportF12_D_1_10
from Reports.StatReportF12_D_2_07                       import CStatReportF12_D_2_07
from Reports.StatReportF12_D_2_10                       import CStatReportF12_D_2_10
from Reports.StatReportF12_D_3_M                        import CStatReportF12_D_3_M
from Reports.StatReportF12Inset2008                     import CStatReportF12Inset2008
from Reports.StatReportF12Seniors_2022                  import CStatReportF12Seniors_2022
from Reports.StatReportF12Seniors                       import CStatReportF12Seniors
from Reports.StatReportF12Teenagers_2022                import CStatReportF12Teenagers_2022
from Reports.StatReportF12Teenagers                     import CStatReportF12Teenagers
from Reports.StatReportF12Students_2025                 import CStatReportF12Students_2025
from Reports.StatReportF131ByDD                         import CStatReportF131ByDD
from Reports.StatReportF131ByDoctors                    import CStatReportF131ByDoctors
from Reports.StatReportF131ByEmployer                   import CStatReportF131ByEmployer
from Reports.StatReportF131ByRaion                      import CStatReportF131ByRaion
from Reports.StatReportF131Raion                        import CStatReportF131Raion
from Reports.StatReportF4_D_For_Teenager                import CStatReportF4_D_For_Teenager
from Reports.StatReportF57                              import CStatReportF57, CStatReportF57_1000, CStatReportF57_2000, CStatReportF57_3000, CStatReportF57_3500
from Reports.StatReportF5_D_For_Teenager                import CStatReportF5_D_For_Teenager
from Reports.StatReportF63                              import CStatReportF63
from Reports.StatReportF065                             import CStatReportF065_1000, CStatReportF065_2000
from Reports.StatReportF71                              import CStatReportF71
from Reports.StatReportF9_2000                          import CStatReportF9_2000
from Reports.StatReportF9_2001                          import CStatReportF9_2001
from Reports.StatReportF9_2003                          import CStatReportF9_2003
from Reports.StatReportF9_2005                          import CStatReportF9_2005
from Reports.StatReportF9_2006                          import CStatReportF9_2006
from Reports.StatReportStomat                           import CStomatReport, CStomatDayReport
from Reports.StatReportStomatCompositeList              import CStomatReportCompositeList, CStomatReportToSpecialityList
from Reports.StatReportStomatDay_2015                   import CStomatDayReport_2015
from Reports.StatReportStomatNew                        import CStomatDayReport  # okdesk 1628 вернул старую форму
from Reports.SummaryOnServiceType                       import CSummaryOnServiceType
from Reports.TempInvalidBookF036                        import CTempInvalidBookF036
from Reports.TempInvalidBookF035                        import CTempInvalidBookF035
from Reports.TempInvalidExpert                          import CTempInvalidExpert
from Reports.TempInvalidF16                             import CTempInvalidF16
from Reports.TempInvalidF16_2022                        import CTempInvalidF16_2022
from Reports.TempInvalidList                            import CTempInvalidList
from Reports.TempInvalidSurvey                          import CTempInvalidSurvey
from Reports.TimelineForOffices                         import CTimelineForOfficesEx
from Reports.TimelineForPerson                          import CTimelineForPersonEx
from Reports.UnfinishedEventsByDoctor                   import CUnfinishedEventsByDoctor
from Reports.UnfinishedEventsByMes                      import CUnfinishedEventsByMes
from Reports.VolumeServices                             import CVolumeServices
from Reports.Workload                                   import CWorkload
from Reports.ReportMedicalServiceExport                 import CReportMedicalServiceExportByProfile, CReportMedicalServiceExportByCitizenship
from Reports.ReportRegistryCardFullness                 import CReportRegistryCardFullness
from Reports.TMKReports                                 import CTMKReports
from Reports.Form13dChildPopulation                     import CForm13dChildPopulation
from Reports.Form25dNumberChildrenByAgeAndSocStatus     import CForm25dNumberChildrenByAgeAndSocStatus
from Reports.ReportFerlzAttachments                     import CReportFerlzAttachments
from Reports.ReportPreventiveMinors                     import CReportPreventiveMinors
from Reports.Report030dco13                             import CReport030dco13
from Reports.ReportDrugAtitumorCure                     import CReportDrugAtitumorCure
from Reports.ReportOnkoByStages                         import CReportOnkoByStages
from Reports.HealthCenterForm68                         import CHealthCenterForm68
from Reports.HealthCenterAnaliz                         import CHealthCenterAnaliz

from Resources.JobPlanner                               import CJobPlanner
from Resources.JobsOperatingDialog                      import CJobsOperatingDialog
from Resources.JobTicketReserve                         import CJobTicketReserveHolder
from Resources.TreatmentControlDialog                   import CTreatmentControlDialog
from Resources.TreatmentScheduleDialog                  import CTreatmentScheduleDialog
from Resources.TreatmentSchemeDialog                    import CTreatmentSchemeDialog

from Stock.StockDialog                                  import CStockDialog
from Stock.StockModel                                   import CStockMotionType

from SurgeryJournal.SurgeryJournalDialog                import CSurgeryJournalDialog

from Surveillance.SurveillanceDialog                    import CSurveillanceDialog

from Timeline.TimelineDialog                            import CTimelineDialog

from TissueJournal                                      import ExportLocalLabResultsToUsish
from TissueJournal.TissueJournalDialog                  import CTissueJournalDialog

from Users.Informer                                     import CInformerList, showInformer
from Users.Login                                        import CLoginDialog, CPersonSelectDialog, getLoginPersonList
from Users.RightList                                    import CUserRightListDialog,  CUserRightProfileListDialog
from Users.Rights import (urAccessAccountInfo,
                          urAccessAccounting,
                          urAccessAccountingBudget,
                          urAccessAccountingCash,
                          urAccessAccountingCMI,
                          urAccessAccountingTargeted,
                          urAccessAccountingVMI,
                          urAccessAnalysis,
                          urAccessAnalysisAnaliticReports,
                          urAccessAnalysisOrgStruct,
                          urAccessAnalysisPersonal,
                          urAccessAnalysisTimeline,
                          urAccessAnalysisTimelinePreRecord,
                          urAccessAttachClientsForArea,
                          urAccessBlanks,
                          urAccessCalendar,
                          urAccessCashBook,
                          urAccessCentralizedAccounting,
                          urAccessContract,
                          urAccessEditTimeLine,
                          urAccessEquipment,
                          urAccessEquipmentMaintenanceJournal,
                          urAccessExchange,
                          urAccessGraph,
                          urAccessHospitalBeds,
                          urAccessHealthResort,
                          urAccessTreatmentScheme,
                          urAccessTreatmentSchedule,
                          urAccessTreatmentControl,
                          urAccessSurgeryJournal,
                          urAccessImunoprophylaxis,
                          urAccessJobsOperating,
                          urAccessJobsPlanning,
                          urAccessLaboratory,
                          urAccessLogicalControl,
                          urAccessLogicalControlDiagnosis,
                          urAccessLogicalControlDoubles,
                          urAccessLogicalControlMES,
                          urAccessLUD,
                          urAccessNomenclature,
                          urAccessNotificationKind,
                          urAccessNotificationLog,
                          urAccessNotificationRule,
                          urAccessNotifications,
                          urAccessQuoting,
                          urAccessQuotingWatch,
                          urAccessReadTimeLine,
                          urAccessRefAccount,
                          urAccessRefAccountActionPropertyTemplate,
                          urAccessRefAccountActionTemplate,
                          urAccessRefAccountActionType,
                          urAccessRefAccountBlankType,
                          urAccessRefAccountEventType,
                          urAccessRefAccountJobPurpose,
                          urAccessRefAccountQuotaType,
                          urAccessRefAccountRBActionShedule,
                          urAccessRefAccountRBAttachType,
                          urAccessRefAccountRBEventProfile,
                          urAccessRefAccountRBEventTypePurpose,
                          urAccessRefAccountRBHospitalBedProfile,
                          urAccessRefAccountRBMedicalAidUnit,
                          urAccessRefAccountRBReasonOfAbsence,
                          urAccessRefAccountRBScene,
                          urAccessRefAccountRBVisitType,
                          urAccessRefAddress,
                          urAccessRefAddressAreas,
                          urAccessRefAddressKLADR,
                          urAccessRefAgreementType,
                          urAccessRefBooks,
                          urAccessRefClassificators,
                          urAccessRefClHurtFactorType,
                          urAccessRefClHurtType,
                          urAccessRefClOKFS,
                          urAccessRefClOKPF,
                          urAccessRefClUnit,
                          urAccessRefEditCardType,
                          urAccessRefEditLocationCard,
                          urAccessRefEmergency,
                          urAccessRefFeed,
                          urAccessRefFinancial,
                          urAccessRefFinRBCashOperation,
                          urAccessRefFinRBFinance,
                          urAccessRefFinRBPayRefuseType,
                          urAccessRefFinRBService,
                          urAccessRefFinRBTariffCategory,
                          urAccessRefMedBloodType,
                          urAccessRefMedComplain,
                          urAccessRefMedDiagnosisType,
                          urAccessRefMedDiseaseCharacter,
                          urAccessRefMedDiseasePhase,
                          urAccessRefMedDiseaseStage,
                          urAccessRefMedDispanser,
                          urAccessRefMedHealthGroup,
                          urAccessRefMedical,
                          urAccessRefMedMKB,
                          urAccessRefMedMKBSubClass,
                          urAccessRefMedResult,
                          urAccessRefMedTempInvalidAnnulmentReason,
                          urAccessRefMedTempInvalidBreak,
                          urAccessRefMedTempInvalidDocument,
                          urAccessRefMedTempInvalidReason,
                          urAccessRefMedTempInvalidRegime,
                          urAccessRefMedTempInvalidResult,
                          urAccessRefMedThesaurus,
                          urAccessRefMedTraumaType,
                          urAccessRefOrganization,
                          urAccessRefOrgBank,
                          urAccessRefOrgOrganisation,
                          urAccessRefOrgRBNet,
                          urAccessRefPersnftnContactType,
                          urAccessRefPersnftnDocumentType,
                          urAccessRefPersnftnDocumentTypeGroup,
                          urAccessRefPersnftnPolicyKind,
                          urAccessRefPersnftnPolicyType,
                          urAccessRefPerson,
                          urAccessRefPersonfication,
                          urAccessRefPersonOrgStructure,
                          urAccessRefPersonPersonal,
                          urAccessRefPersonRBActivity,
                          urAccessRefPersonRBAppointmentPurpose,
                          urAccessRefPersonRBPost,
                          urAccessRefPersonRBSpeciality,
                          urAccessRefSocialStatus,
                          urAccessRefSocialStatusClass,
                          urAccessRefSocialStatusType,
                          urAccessRegistry,
                          urAccessSetupAccountSystems,
                          urAccessSetupCounter,
                          urAccessSetupDefault,
                          urAccessSetupExport,
                          urAccessSetupProfilesUserRights,
                          urAccessSetupTemplate,
                          urAccessSetupUserRights,
                          urAccessStockControl,
                          urAccessStockRecipe,
                          urAccessSurveillance,
                          urAccessSuspenedAppointment,
                          urAccessTissueJournal,
                          urAdmin,
                          urAccessStatReports,
                          urAccessGenRep,
                          urAccessReportsChief,
                          urAccessReportsByVisits,
                          urAccessReportsBuMorbidity,
                          urAccessDispObservation,
                          urAccessAnalysisService,
                          urAccessTempInvalid,
                          urAccessDeath,
                          urAccessContingent,
                          urAccessWorkload,
                          urAccessStationary,
                          urAccessAccountingAnalysis,
                          urAccessEmergencyCall,
                          urAccessReportImunoprophylaxis,
                          urAccessReportLaboratory,
                          urAccessReportTrauma,
                          urAccessReportSanstorium,
                          urAccessRefPersnftnResearchKind,
                          urAccessAdministrator,
                          urAccessClientAttachExport,
                          urUnlockData,
                          urAccesslogicCntlOMSAccounts,
                          urCanSignOrgCert,
                          canRightForCreateAccounts,
                          urAccessDispService,
                          urDemography,
                          urHomeCallJournal,
                          urMedStatic,
                          urDoctorSectionExport,
                          urSetupInformer,
                          urAccessRefPersnftnContingentKind,
                          urPlanningHospitalBedProfile, urAdminServiceTMK, urServiceTMKdirectionList,
                          urEditLoginPasswordProfileUser, urAccessLethality, urAccessClientAttachFederalService,
                          urPersonSubstitution, urAccessEconomicAnalysis, urAccessCashBookOnlyJournal,
                          urStreetCorrect
                          )
from Users.Tables import demoUserName, tblUser, usrLogin, usrRetired, tblLogin
from Users.tryKerberosAuth                              import tryKerberosAuth
from Users.UserInfo                                     import CUserInfo, CDemoUserInfo
from library.PrintDebug.Utils                           import DebugPrintData

from Ui_s11main                                         import Ui_MainWindow
from library.TimeoutLogout               import CTimeoutLogout
from Exchange.UO.MedServiceProfilesDialog import CMedServiceProfilesDialog


class CS11mainApp(CBaseApp):
    __pyqtSignals__ = ('dbConnectionChanged(bool)',
                       'currentOrgIdChanged()',
                       'currentOrgStructureIdChanged()',
                       'currentClientIdChanged()',
                       'currentClientInfoChanged()',
                       'currentUserIdChanged()',
                       'identCardReceived(PyQt_PyObject)',
                       'gtinReceived(QString)',  # для МДЛП: один только gtin из EAN-13 или др. GS1
                       'sgtinReceived(QString)', # для МДЛП: gtin + серийный номер из GS1
                       'ssccReceived(QString)',  # для МДЛП: sscc из GS1

                      )

    iniFileName = 'S11App.ini'
    logFileName = 'error.log'

    inputCalculatorMimeDataType  = 'samson/inputLaboratoryCalculator'
    outputCalculatorMimeDataType = 'samson/outputLaboratoryCalculator'

    def __init__(self, args, demoModeRequest, iniFileName, disableLock, logSql, appLogMark, rkey):
        self.eventLogFile = None
        self.eventLogTime = 0

        CBaseApp.__init__(self, args, iniFileName or CS11mainApp.iniFileName)
        self.traceActive = True
        self.demoMode = False
        self.loginId = None
        self.demoModeRequested = demoModeRequest
        self.disableLockRequested = disableLock
        self.disableLock = disableLock
        self.batchRegLocatCardProcess = False
        self.dbInside = None
        self.isBusyReconnect = 0
        self.EIS_db = None
        self.clearPreferencesCache()
        self._currentClientId = None
        self.userInfo = None
        self.maxLifeDuration = 130
        self._counterController = None
        self._globalPreferences = {}
        self._oldClipboardSlot = None
        self.accountingSystem = None
        self._gpSpecialityId = None   # специальность врача общей практики
        self.morphologyMKBIsVisible = None
        self.isManualSwitchDiagnosis = None
        self.isHospitalBedProfileByMoving = None
        self.isHospitalBedFinanceByMoving = None
        self.isNeedPreCreateEventPerson = None
        self._isGlobalAppLog = None
        self.scanner = None
        self.scannerTimer = None
        self.smartCardWatcher = None
        self.smartCardTimer = None
        self.logSql = logSql
        self.rkey = rkey
        self.appLogMark = appLogMark
        self.webDAVInterface = CWebDAVInterface()
        self.__checkCertExpiration = {}
        self._session = {}
        self._timeoutLogout = CTimeoutLogout(self)


    def writeAppLog(self, log, mark=u''):
        try:
            self.db.query('CALL writeAppLog(\'%s\',\'%s\')'%(log, mark or self.appLogMark))
        except:
            pass


    def connectClipboard(self, slotFunction):
        self.disconnectClipboard()
        self._oldClipboardSlot = slotFunction
        self.connect(self.clipboard(), SIGNAL('dataChanged()'), slotFunction)


    def disconnectClipboard(self):
        if self._oldClipboardSlot:
            self.disconnect(self.clipboard(), SIGNAL('dataChanged()'), self._oldClipboardSlot)
            self._oldClipboardSlot = None


    def registerDocumentTables(self):
        database.registerDocumentTable('Account')
        database.registerDocumentTable('Action')
        database.registerDocumentTable('Action_FileAttach')
        # database.registerDocumentTable('Action_FileAttach_Signature')
        database.registerDocumentTable('Action_ExecutionPlan')
        database.registerDocumentTable('Action_ActionProperty')
        database.registerDocumentTable('Action_ESKLP_Smnn')
        database.registerDocumentTable('ActionExecutionPlan')
        database.registerDocumentTable('ActionProperty')
        database.registerDocumentTable('ActionPropertyTemplate')
        database.registerDocumentTable('ActionTemplate')
        database.registerDocumentTable('ActionType')
        database.registerDocumentTable('Address')
        database.registerDocumentTable('AddressHouse')
        database.registerDocumentTable('Bank')
        database.registerDocumentTable('BlankActions_Moving')
        database.registerDocumentTable('BlankActions_Party')
        database.registerDocumentTable('BlankTempInvalid_Moving')
        database.registerDocumentTable('BlankTempInvalid_Party')
        database.registerDocumentTable('CalendarException')
        database.registerDocumentTable('Client')
        database.registerDocumentTable('Client_FileAttach')
        database.registerDocumentTable('ClientAddress')
        database.registerDocumentTable('ClientAllergy')
        database.registerDocumentTable('ClientAttach')
        database.registerDocumentTable('ClientConsent')
        database.registerDocumentTable('ClientContact')
        database.registerDocumentTable('ClientDeposit')
        database.registerDocumentTable('ClientDocument')
        database.registerDocumentTable('ClientIdentification')
        database.registerDocumentTable('ClientIntoleranceMedicament')
        database.registerDocumentTable('ClientPolicy')
        database.registerDocumentTable('Client_Quoting')
        database.registerDocumentTable('ClientRelation')
        database.registerDocumentTable('ClientResearch')
        database.registerDocumentTable('ClientActiveDispensary')
        database.registerDocumentTable('ClientDangerous')
        database.registerDocumentTable('ClientForcedTreatment')
        database.registerDocumentTable('ClientSuicide')
        database.registerDocumentTable('ClientContingentKind')
        database.registerDocumentTable('ClientSocStatus')
        database.registerDocumentTable('ClientHospitalization')
        database.registerDocumentTable('ClientWork')
        database.registerDocumentTable('Client_StatusObservation')
        database.registerDocumentTable('Contract')
        database.registerDocumentTable('Diagnosis')
        database.registerDocumentTable('DiagnosisDispansPlaned')
        database.registerDocumentTable('Diagnostic')
        database.registerDocumentTable('EmergencyCall')
        database.registerDocumentTable('Event')
        database.registerDocumentTable('Event_Feed')
        database.registerDocumentTable('Event_FileAttach')
        database.registerDocumentTable('Event_JournalOfPerson')
        database.registerDocumentTable('Event_LocalContract')
        database.registerDocumentTable('Event_Payment')
        database.registerDocumentTable('EventType')
        database.registerDocumentTable('InformerMessage')
        database.registerDocumentTable('Job')
        database.registerDocumentTable('Licence')
        database.registerDocumentTable(tblLogin)
        database.registerDocumentTable('Notification_Rule')
        database.registerDocumentTable('Organisation')
        database.registerDocumentTable('OrgStructure')
        database.registerDocumentTable('OrgStructure_HospitalBed')
        database.registerDocumentTable('OrgStructure_HospitalBed_Involution')
        database.registerDocumentTable('OrgStructure_PlanningHospitalBedProfile')
        database.registerDocumentTable('Person')
        database.registerDocumentTable('Person_Activity')
        database.registerDocumentTable('Person_Contact')
        database.registerDocumentTable('Person_Education')
        database.registerDocumentTable('Person_Order')
        database.registerDocumentTable('Person_TimeTemplate')
        database.registerDocumentTable('Probe')
        database.registerDocumentTable('ProphylaxisPlanning')
        database.registerDocumentTable('ProphylaxisPlanning_FileAttach')
        database.registerDocumentTable('QuotaType')
        database.registerDocumentTable('Quoting')
        database.registerDocumentTable('Quoting_Region')
        database.registerDocumentTable('Schedule')
        database.registerDocumentTable('Schedule_Item')
        database.registerDocumentTable('StockMotion')
        database.registerDocumentTable('StockPurchaseContract')
        database.registerDocumentTable('SuspendedAppointment')
        database.registerDocumentTable('TakenTissueJournal')
        database.registerDocumentTable('TempInvalid')
        database.registerDocumentTable('TempInvalidDocument')
        database.registerDocumentTable('Visit')
        database.registerDocumentTable('Event_CardLocation')
        database.registerDocumentTable('rbUserProfile') # это против правил :(
        database.registerDocumentTable('Client_DocumentTracking')
        database.registerDocumentTable('Client_DocumentTrackingItem')
        database.registerDocumentTable('rbService')
        database.registerDocumentTable('ActionTypeGroup')
        database.registerDocumentTable('ActionTypeGroup_Item')
        database.registerDocumentTable('Person_ActionProperty')
        database.registerDocumentTable('rbStockMotionItemReason')
        database.registerDocumentTable('rbTumor')
        database.registerDocumentTable('rbTumor_Identification')
        database.registerDocumentTable('rbNodus')
        database.registerDocumentTable('rbNodus_Identification')
        database.registerDocumentTable('rbMetastasis')
        database.registerDocumentTable('rbMetastasis_Identification')
        database.registerDocumentTable('rbTNMphase')
        database.registerDocumentTable('rbTNMphase_Identification')
        database.registerDocumentTable('ActionType_Expansion')
        database.registerDocumentTable('rbEquipmentType')
        database.registerDocumentTable('rbEquipmentClass')
        database.registerDocumentTable('Client_History')
        database.registerDocumentTable('rbNomenclature_Identification')
        database.registerDocumentTable('Event_Voucher')
        database.registerDocumentTable('rbMKBExSubclass')
        database.registerDocumentTable('MKB_ExSubclass')
        database.registerDocumentTable('TreatmentType')
        database.registerDocumentTable('TreatmentScheme')
        database.registerDocumentTable('TreatmentScheme_Source')
        database.registerDocumentTable('TreatmentSchedule')
        database.registerDocumentTable('Client_Monitoring')
        database.registerDocumentTable('rbNomenclatureActiveSubstance')
        database.registerDocumentTable('rbNomenclatureActiveSubstance_Identification')
        database.registerDocumentTable('rbNomenclatureActiveSubstanceGroups')
        database.registerDocumentTable('rbNomenclatureActiveSubstance_Groups')
        database.registerDocumentTable('ClientVaccinationProbe')
        database.registerDocumentTable('rbReactionType_Identification')
        database.registerDocumentTable('rbReactionManifestation_Identification')
        database.registerDocumentTable('rbNomenclatureUsingType')
        database.registerDocumentTable('rbNomenclatureUsingType_Identification')
        database.registerDocumentTable('soc_prikCoefType')
        database.registerDocumentTable('soc_prikCoefItem')

    def isAdmin(self):
        return self.userHasRight(urAdmin)


    def getPathToDictionary(self):
        result = QtGui.qApp.pathToPersonalDict()
        if not os.path.isfile(result):
            result = self.getDefaultPathToDictionary()
            if not os.path.isfile(result):
                try:
                    f = open(result, 'w')
                    f.close()
                except:
                    return None
        return result


    def getDefaultPathToDictionary(self):
        return os.path.join(self.logDir, 'Dicts', 'PersonalDictionary.txt')


    def openDatabaseReConnect(self):        #ymd
        self.db = None
        self.db = database.connectDataBase(self.preferences.dbDriverName,
                                     self.preferences.dbServerName,
                                     self.preferences.dbServerPort,
                                     self.preferences.dbDatabaseName,
                                     self.preferences.dbUserName,
                                     self.preferences.dbPassword,
                                     compressData = self.preferences.dbCompressData,
                                     logger = logging.getLogger('DB') if self.logSql else None)
#ymd st

        try:
            self.db.parentGl = self.mainWindow
        except:
            pass

# ymd end

    def openDatabase(self):
        self.db = None
        self.db = database.connectDataBase(self.preferences.dbDriverName,
                                     self.preferences.dbServerName,
                                     self.preferences.dbServerPort,
                                     self.preferences.dbDatabaseName,
                                     self.preferences.dbUserName,
                                     self.preferences.dbPassword,
                                     compressData = self.preferences.dbCompressData,
                                     logger = logging.getLogger('DB') if self.logSql else None
                                     )

        self.loadGlobalPreferences()
        self.setCurrentClientId(None)


    def loadCalendarInfo(self):
        self.emit(SIGNAL('dbConnectionChanged(bool)'), True)
        self.calendarInfo.load()
        self.disableLock = self.disableLockRequested or self.db.db.record('AppLock').count() == 0
        if not self.disableLock:
            try:
                if self.db.name == 'postgres':
                    self.db.query('select getAppLock_prepare()')
                else:
                    self.db.query('CALL getAppLock_prepare()')
            except:
                self.disableLock = True

        self.webDAVInterface.setWebDAVUrl(self.getWebDAVUrl())


    def closeDatabase(self):
        if self.db:
            # Подчистка блокировок при выходе из приложения
            if not self.disableLock:
                try:
                    if self.db.name == 'postgres':
                        self.db.query('select cleanup_locks()')
                    else:
                        self.db.query('CALL CleanupLocks()')
                except:
                    pass
            self.db.close()
            self.setCurrentClientId(None)
            self.db = None
            self.emit(SIGNAL('dbConnectionChanged(bool)'), False)
            self.calendarInfo.clear()
            self._globalPreferences.clear()
            self.accountingSystem = None
            self._gpSpecialityId = None
            self.batchRegLocatCardProcess = False


#    def closeNewDBConnection(self, name):
#        if hasattr(self, name):
#            db = getattr(self, name)
#            db.close()
#            self.__delattr__(name)


    def loadGlobalPreferences(self):
        if self.db:
            try:
                recordList = self.db.getRecordList('GlobalPreferences')
            except:
                recordList = []
            for record in recordList:
                code  = forceString(record.value('code'))
                value = forceString(record.value('value'))
                self._globalPreferences[code] = value


    def checkGlobalPreference(self, code, chkValue, default=None):
        value = self._globalPreferences.get(code, default)
        if value:
            return unicode(value).lower() == unicode(chkValue).lower()
        return False


    def isGlobalAppLog(self):
        if self._isGlobalAppLog is None:
            self._isGlobalAppLog = self.checkGlobalPreference(u'appLog', u'да')
        return self._isGlobalAppLog


    def getWebDAVUrl(self):
        url = forceStringEx(self.preferences.appPrefs.get('WebDAVUrl', ''))
        if not url:
            url = forceStringEx(self._globalPreferences.get('WebDAV', None))
        if url:
            url = url.replace('${dbServerName}', self.preferences.dbServerName)
        else:
            url = None
        return url


    def getMqHelperUrl(self):
        url = self._globalPreferences.get('MqHelperUrl', None)
        if not url:
            url = 'http://${dbServerName}/queueManagement/api'
        url = url.replace('${dbServerName}', self.preferences.dbServerName)
        return url


    def getGlobalPreference(self, code):
        value = self._globalPreferences.get(code, None)
        return unicode(value).lower() if value else None


    def tryOpenScanner(self):
        if self.scannerEnabled():
            self.scanner = None
            try:
                settings = self.scannerPortSettings()
                self.scanner = serial.Serial(settings.port,
                                             baudrate=settings.baudrate,
                                             bytesize=8,
                                             parity=settings.parity,
                                             stopbits=settings.stopbits,
                                             xonxoff=settings.xonxoff,
                                             rtscts=settings.rtscts,
                                             timeout=0.1)
#            except IOError, e:
            except UnicodeError, e:
                if self.scannerConnectionReport():
                    try:
                        QtGui.QMessageBox.information(self.mainWindow, u'Ошибка подключения к сканеру', anyToUnicode(e.object), QtGui.QMessageBox.Close, QtGui.QMessageBox.Close)
                    except:
                        pass
                #self.logCurrentException()
                return
            except Exception, e:
                if self.scannerConnectionReport():
                    try:
                        QtGui.QMessageBox.information(self.mainWindow, u'Ошибка подключения к сканеру', anyToUnicode(str(e)), QtGui.QMessageBox.Close, QtGui.QMessageBox.Close)
                    except:
                        pass
                #self.logCurrentException()
                return
            if self.scannerTimer is None:
                self.scannerTimer = QTimer(self)
                self.connect(self.scannerTimer, SIGNAL('timeout()'), self.checkScanner)
            self.scannerTimer.start(250)


    def checkScanner(self):
        def processPdf417(data, backshashesAreDoubled):
            if ( backshashesAreDoubled
                 or (     backshashesAreDoubled is None
                      and self.scannerCorrectBackslashes() and data.count('\\') == data.count('\\\\')*2
                    )
               ):
                data = data.replace('\\\\',  '\\')
            identCard = policyBarCodeAsIdentCard(QtGui.qApp.focusWidget(), data)
            if identCard:
                self.emit(SIGNAL('identCardReceived(PyQt_PyObject)'), identCard)


        def processEkp(data):
            if self.getIdentCardServiceUrl() and self.ekpBarCodeEnabled():
                identCard = tryCardIdAsEkpIdentCard(data)
                if identCard:
                    self.emit(SIGNAL('identCardReceived(PyQt_PyObject)'), identCard)
                    return True
            return False


        def processGS1(data):
            try:
                data = stripSymbologyId(data)
                assocList = CGS1CodeParser.parseCode(data)
                gs1 = dict(assocList)
                if '00' in gs1:
                    self.emit(SIGNAL('ssccReceived(QString)'), gs1['00'])
                elif '01' in gs1 and '21' in gs1:
                    self.emit(SIGNAL('sgtinReceived(QString)'), gs1['01'] + gs1['21'])
                elif '01' in gs1:
                    self.emit(SIGNAL('gtinReceived(QString)'), gs1['01'])
                self.emit(SIGNAL('Gs1BarcodeReceived(QByteArray, PyQt_PyObject)'),  data, assocList)
            except:
                self.logCurrentException()
                self.beep()

        def processEan13(data):
            data = stripSymbologyId(data)
            self.emit(SIGNAL('gtinReceived(QString)'), data.rjust(14, '0'))
            #self.emulateKeyboardInput('gtin:' + data.rjust(14, '0'))

        if self.scanner is not None:
            data = None
            try:
                if self.scanner.inWaiting():
                    data = self.scanner.readall()
#            except IOError, e:
            except UnicodeError as e:
                if self.scannerConnectionReport():
                    QtGui.QMessageBox.information(self.mainWindow, u'Ошибка считывания со сканера',  anyToUnicode(e.object), QtGui.QMessageBox.Close, QtGui.QMessageBox.Close)
                    self.scannerTimer.stop()
            except Exception as e:
                if self.scannerConnectionReport():
                    QtGui.QMessageBox.information(self.mainWindow, u'Ошибка считывания со сканера',  exceptionToUnicode(e), QtGui.QMessageBox.Close, QtGui.QMessageBox.Close)
                    self.scannerTimer.stop()
                #self.logCurrentException()
                return
            if data is not None:
                if hasSymbologyId(data):
                    if isGS1(data):
                        processGS1(data)
                    elif isEan13(data):
                        processEan13(data)
                    elif isPdf417(data):
                        processPdf417(stripSymbologyId(data), isPdf417WithDoubleBackslash(data))
                    elif isQrCode(data):
                        processEkp(stripSymbologyId(data))
                    else:
                        data = stripSymbologyId(data)
                        simpleBarCode = re.match('^\x02?([ 0-9]+)[\n\r\t\x00]*$', data)
                        if simpleBarCode:
                            simpleBarCodeData = simpleBarCode.group(1)
                            self.emulateKeyboardInput('\x02'+simpleBarCodeData+'\n')
                else:
                    simpleBarCode = re.match('^\x02?([ 0-9]+)[\n\r\t\x00]*$', data)
                    if simpleBarCode:
                        simpleBarCodeData = simpleBarCode.group(1)
                        if not processEkp(simpleBarCodeData):
                            self.emulateKeyboardInput('\x02'+simpleBarCodeData+'\n')
                    else:
                        processPdf417(data, None)


    def emulateKeyboardInput(self, data):
        specialKeys = { '\r'  : (Qt.Key_Return, Qt.NoModifier),
                        '\n'  : (Qt.Key_Enter,  Qt.NoModifier),
                        '\t'  : (Qt.Key_Tab,    Qt.NoModifier),
                        '\x02': (Qt.Key_B,      Qt.ControlModifier)
                      }
        for c in data:
            key = specialKeys.get(c)
            if key is None:
                key = ord(c.upper()), Qt.ShiftModifier if c.isupper() else Qt.NoModifier
            keyEvent = QtGui.QKeyEvent(QtGui.QKeyEvent.KeyPress, key[0], key[1],  c)
            if self.focusWidget():
                self.sendEvent(self.focusWidget(), keyEvent)
            keyEvent = QtGui.QKeyEvent(QtGui.QKeyEvent.KeyRelease, key[0],  key[1],  c)
            if self.focusWidget():
                self.sendEvent(self.focusWidget(), keyEvent)


    def closeScanner(self):
        if self.scannerTimer is not None:
            self.scannerTimer.stop()
        if self.scanner is not None:
            self.scanner.close()
            self.scanner = None


    def tryOpenSmartCardReader(self):
        global gSmartCardAvailable
        if gSmartCardAvailable:
            try:
                self.smartCardWatcher = CSmartCardWatcher()
            except:
                # если у нас будет настройка "использовать смарт-карты",
                # то нужно будет выдавать явное сообщение о проблеме
                gSmartCardAvailable = False
                #self.logCurrentException()
                return
            self.smartCardWatcher.addSubscriber(self)
            if self.smartCardTimer is None:
                self.smartCardTimer = QTimer(self)
                self.connect(self.smartCardTimer, SIGNAL('timeout()'), self.checkSmartCard)
            self.smartCardTimer.start(250)


    def checkSmartCard(self):
        if self.activeWindow(): # and self.focusWidget()
            self.smartCardWatcher.watch()


    def addSmartCardNotice(self, connection):
        try:
            identCard = smartCardAsIdentCard(connection)
            if identCard:
                self.emit(SIGNAL('identCardReceived(PyQt_PyObject)'), identCard)
            return True
        except:
            pass


    def closeSmartCardReader(self):
        if self.smartCardTimer is not None:
            self.smartCardTimer.stop()
        self.smartCardWatcher = None


    def getUserCertForAdmin(self, api, personId):
        now = QDateTime.currentDateTime().toPyDateTime()
        # if self.getUseOwnPk():
            # snils = self.getUserSnils()
        snils = forceString(self.db.translate('Person', 'id', personId, 'SNILS'))
        if not snils:
            raise ECertNotFound(u'Для текущего пользователя (Person.id=%r) не определён СНИЛС' % personId)
        result = api.findCertInStores(api.SNS_OWN_CERTIFICATES, snils=snils, datetime=now)
        if not result:
            raise ECertNotFound(u'Не удалось найти действующий сертификат пользователя по СНИЛС «%s»' % formatSNILS(snils))
        # else:
        #     userCertSha1 = self.getUserCertSha1()
        #     result = api.findCertInStores(api.SNS_OWN_CERTIFICATES, sha1hex=userCertSha1)
        #     if not result:
        #         raise Exception(u'Не удалось найти сертификат пользователя с отпечатком sha1 %s' % userCertSha1)
        #     if not result.notBefore() <= now <= result.notAfter():
        #         raise Exception(u'Сертификат пользователя с отпечатком sha1 %s найден, но сейчас не действителен' %  userCertSha1)
        return result


    def getUserCert(self, api):
        now = QDateTime.currentDateTime().toPyDateTime()
        if self.getUseOwnPk():
            snils = forceString(self.db.translate('Person', 'id', self.userId, 'SNILS'))
            if not snils:
                raise ECertNotFound(u'Для текущего пользователя (Person.id=%s) не определён СНИЛС' % self.userId)
            ogrn  = self.getCurrentOrgOgrn()
            result = api.findCertInStores(api.SNS_OWN_CERTIFICATES,
                                          snils=snils,
                                          datetime=now,
                                          weakOgrn=ogrn
                                          )
            if not result:
                raise ECertNotFound(u'Не удалось найти действующий сертификат пользователя по СНИЛС «%s»' % formatSNILS(snils))
#            if not result.notBefore() <= now <= result.notAfter():
#                raise ECertNotFound(u'Сертификат пользователя со СНИЛС «%s», но сейчас не действителен' % formatSNILS(snils))
        else:
            userCertSha1 = self.getUserCertSha1()
            result = api.findCertInStores(api.SNS_OWN_CERTIFICATES, sha1hex=userCertSha1)
            if not result:
                raise ECertNotFound(u'Не удалось найти сертификат пользователя с отпечатком sha1 %s' % userCertSha1)
            if not result.notBefore() <= now <= result.notAfter():
                raise ECertNotFound(u'Сертификат пользователя с отпечатком sha1 %s найден, но сейчас не действителен' %  userCertSha1)
        self.checkCertExpirationPeriod(result)
        return result


    def getOrgCertOptionalOgrn(self, api):
        # в СФР теперь ОГРН в сертификате не обязателен, но если есть, все еще проверяем соответствие
        ogrn = self.getCurrentOrgOgrn()
        if not ogrn:
            raise ECertNotFound(u'Мы не сможем подобрать сертификат медицинской организации, так как для текущей организации не определён ОГРН')

        now = QDateTime.currentDateTime().toPyDateTime()
        orgCertSha1 = self.getOrgCertSha1()
        if orgCertSha1:
            result = api.findCertInStores(api.SNS_OWN_CERTIFICATES, sha1hex=orgCertSha1)
            if not result:
                raise ECertNotFound(u'Не удалось найти сертификат медицинской организации с отпечатком sha1 %s' % orgCertSha1)
            if result.ogrn() and result.ogrn() != ogrn:
                raise ECertNotFound(u'Сертификат медицинской организации с отпечатком sha1 %s найден, но указанный в нём ОГРН не равен «%s»' % (orgCertSha1, ogrn))
            if not result.notBefore() <= now <= result.notAfter():
                raise ECertNotFound(u'Сертификат медицинской организации с отпечатком sha1 %s найден, но сейчас не действителен' % orgCertSha1)
            self.checkCertExpirationPeriod(result)
        else:
            result = self.getUserCert(api)
            if result.ogrn() and result.ogrn() != ogrn:
                raise ECertNotFound(u'В настройках не определён сертификат медицинской организации, сертификат пользователя не подошёл')
        return result


    def getOrgCert(self, api):
        result = self.getOrgCertOptionalOgrn(api)
        orgCertSha1 = self.getOrgCertSha1()
        if orgCertSha1:
            if not result.ogrn():
                raise ECertNotFound(u'Сертификат медицинской организации с отпечатком sha1 %s найден, но в нём не указан ОГРН' % orgCertSha1)
        else:
            if not result.ogrn():
                raise ECertNotFound(u'В настройках не определён сертификат медицинской организации, сертификат пользователя не подошёл')
        return result


    def checkCertExpirationPeriod(self, cert):
        if self.getWarnAboutCertExpiration():
            days = QDateTime.currentDateTime().daysTo(cert.notAfter())
            sha1 = cert.sha1().encode('hex').lower()
            if days <= self.getCertExpirationWarnPeriod() and self.__checkCertExpiration.get(sha1) != days:
                commonName      = cert.commonName()
                surName         = cert.surName()
                givenName       = cert.givenName()
                issuerName      = cert.issuerName()
                serialNumber    = cert.serialNumber()
                notAfter        = forceString(QDateTime(cert.notAfter()))
                if surName and givenName:
                    name = u'%s %s' % (surName, givenName)
                else:
                    name = commonName or ''
                message = u'До окончания срока действия сертификата ЭЦП\n' \
                          u'(имя субьекта: %s,\n' \
                          u' имя издателя: %s,\n' \
                          u' серийный номер: %s,\n' \
                          u' срок действия: %s,\n'\
                          u' хэш SHA1: %s)\n' \
                          u'осталось %s' % (name,
                                            issuerName,
                                            serialNumber,
                                            notAfter,
                                            sha1,
                                            formatDays(days)
                                           )
                QtGui.QMessageBox.warning(None,
                                          u'Внимание!',
                                          message,
                                          QtGui.QMessageBox.Close)
                self.__checkCertExpiration[sha1] = days


    def getFssCert(self, api):
        fssCertSha1 = self.getFssCertSha1()
        result = api.findCertInStores([api.SNS_OTHER_CERTIFICATES, api.SNS_OWN_CERTIFICATES], sha1hex=fssCertSha1)
        if not result:
            raise ECertNotFound(u'Не удалось найти сертификат СФР с отпечатком sha1 %s' % fssCertSha1)
        today = QDateTime.currentDateTime().toPyDateTime()
        if not result.notBefore() <= today <= result.notAfter():
            raise ECertNotFound(u'Сертификат СФР с отпечатком sha1 %s найден, но сейчас не действителен' %  fssCertSha1)
        return result


    def getMdlpPrefs(self):
        prefs = self.preferences.appPrefs
        if 'mdlpEnabled' not in prefs or forceBool(prefs.get('mdlpEnabled', True)):
            mdlpUrl          = forceString(prefs.get('mdlpUrl', ''))
            clientId         = forceString(prefs.get('mdlpClientId', ''))
            secret           = forceString(prefs.get('mdlpClientSecret', ''))
            useStunnel       = forceBool(prefs.get('mdlpUseStunnel', False))
            stunnelUrl       = forceString(prefs.get('mdlpStunnelUrl', ''))
            notificationMode = forceBool(prefs.get('mdlpNotificationMode', False))
        else:
            mdlpUrl          = ''
            clientId         = ''
            secret           = ''
            useStunnel       = False
            stunnelUrl       = ''
            notificationMode = False
        return mdlpUrl, clientId, secret, useStunnel, stunnelUrl, notificationMode


    def isMdlpEnabled(self):
        prefs = self.preferences.appPrefs
        if 'mdlpEnabled' in prefs:
            return forceBool(prefs.get('mdlpEnabled', True))
        mdlpUrl, clientId, secret, useStunnel, stunnelUrl, notificationMode = self.getMdlpPrefs()
        return mdlpUrl and clientId and secret and(not useStunnel or stunnelUrl)

    
    def getMdlpRetRegPres(self):
        prefs = self.preferences.appPrefs
        if 'mdlpEnabled' not in prefs or forceBool(prefs.get('mdlpEnabled', True)):
            url      = forceString(prefs.get('mdlpRetRegUrl', ''))
            user     = forceString(prefs.get('mdlpRetRegUser', ''))
            password = forceString(prefs.get('mdlpRetRegPassword', ''))
        else:
            url = user = password = ''
        return url, user, password
        

    def isMdlpRetRegEnabled(self):
        url, user, password = self.getMdlpRetRegPres()
        return bool(url and user and password)


    def recordEvent(self, receiver, event):
        def getPath(obj):
            names = []
            while obj:
                parent = obj.parent()
                name = obj.objectName()
                if parent:
                    children = parent.findChildren(QObject, name)
                    if not children:
                        self.eventLogFile.write('Warning child %s type %s not found\n' %(
                            repr(unicode(name)),
                            repr(obj.metaObject().className()),
                            ))
                    elif len(children)>1:
                        try:
                            idx = children.index(obj)
                        except:
                            idx = -1
                        name = name + ':' + str(idx)
                names.append(unicode(name))
                obj = obj.parent()
            names.append('')
            return '/'.join(names[::-1])

        def recordKeyEvent(typeName):
            t0, self.eventLogTime = self.eventLogTime, time.time()
            self.eventLogFile.write('Time %f\n' % (self.eventLogTime-t0))
            self.eventLogFile.write('%s %s %X %X %s\n' % (typeName,
                                                     getPath(receiver),
                                                     event.key(),
                                                     int(event.modifiers()),
                                                     repr(unicode(event.text()))
                                      ))

        def recordMouseEvent(typeName):
            t0, self.eventLogTime = self.eventLogTime, time.time()
            self.eventLogFile.write('Time %f\n' % (self.eventLogTime-t0))
            self.eventLogFile.write('%s %s %X %X %X %d %d\n' % (typeName,
                                                     getPath(receiver),
                                                     int(event.button()),
                                                     int(event.buttons()),
                                                     int(event.modifiers()),
                                                     event.x(),
                                                     event.y()
                                      ))

        t = event.type()
        if t == QEvent.KeyPress:
            recordKeyEvent('KeyPress')
        elif t == QEvent.KeyRelease:
            recordKeyEvent('KeyRelease')
        elif t == QEvent.MouseButtonPress:
            recordMouseEvent('MouseButtonPress')
        elif t == QEvent.MouseButtonRelease:
            recordMouseEvent('MouseButtonRelease')
        elif t == QEvent.MouseButtonDblClick:
            recordMouseEvent('MouseButtonDblClick')
        elif t == QEvent.MouseMove:
            recordMouseEvent('MouseMove')


    def notify(self, receiver, event):
        try:
            if self.eventLogFile and isinstance(event, QtGui.QInputEvent):
                self.recordEvent(receiver, event)
#            report = ['notify:: receiver.type=',unicode(type(receiver)),' receiver.name=', unicode(receiver.objectName()),' event.type=',unicode(type(event)), 'event.type()=', unicode(event.type())]
#            logging.getLogger('notify').info( ("".join(report)) )
#            if receiver.objectName()=='txtClientInfoBrowser':
#                logging.getLogger('notify').info( receiver.toHtml() )

            return QtGui.QApplication.notify(self, receiver, event)
        except Exception, e:
            if self.traceActive:
                self.logCurrentException()
                widget = self.activeModalWidget()
                if widget is None:
                    widget = self.mainWindow
                QtGui.QMessageBox.critical( widget,
                                            u'Произошла ошибка',
                                            exceptionToUnicode(e),
                                            QtGui.QMessageBox.Close)
            return False
        except:
            return False


    def call(self, widget, func, params = ()):
        try:
            return True, func(*params)
        except IOError, e:
            self.logCurrentException()
            # msg=''
            if getattr(e, 'filename', None):
                msg = u'%s:\n[Errno %s] %s' % (e.filename, e.errno, anyToUnicode(e.strerror))
            elif getattr(e, 'strerror', None):
                msg = u'[Errno %s] %s' % (e.errno, anyToUnicode(e.strerror))
            # эти хлопоты с вложенными exception связаны со своеобразной обработкой
            # ошибок в requests
#            elif isinstance(e.message, Exception):
#                if len(e.message.args) >= 2 and isinstance(e.message.args[1], IOError):
#                    msg = u'%s: [Errno %s] %s' % ( e.message.args[0], e.message.args[1].errno, anyToUnicode(e.message.args[1].strerror))
#                else:
#                    msg = unicode(e.message)
            else:
                msg = exceptionToUnicode(e)
            QtGui.QMessageBox.critical(widget,
                u'Произошла ошибка ввода-вывода', msg, QtGui.QMessageBox.Close)
        except Exception, e:
            self.logCurrentException()
            widget = widget or self.activeModalWidget() or self.mainWindow
            QtGui.QMessageBox.critical( widget,
                                        u'Произошла ошибка',
                                        exceptionToUnicode(e),
                                        QtGui.QMessageBox.Close)
        return False, None


    def setWaitCursor(self):
        self.setOverrideCursor(QtGui.QCursor(Qt.WaitCursor))


    def callWithWaitCursor(self, widget, func, *params, **kwparams):
        self.setWaitCursor()
        try:
            return func(*params, **kwparams)
        finally:
            self.restoreOverrideCursor()


    def execProgram(self, cmd, args=None, waitForFinished=True):
        self.setWaitCursor()
        try:
            process = None
            outArgs = [arg if isinstance(arg, basestring) else unicode(arg) for arg in args] if args is not None else None
            t = QTime()
            t.start()
            stepTimeOut = 200 # ms

            if waitForFinished:
                process = QProcess()
                if outArgs is None:
                    process.start(cmd)
                else:
                    process.start(cmd, outArgs)
                for i in xrange(100):
                    started=process.waitForStarted(stepTimeOut)
                    self.processEvents(QEventLoop.ExcludeUserInputEvents)
                    if started:
                        break

                while process.state() == QProcess.Running and not process.waitForFinished(stepTimeOut):
                    self.processEvents(QEventLoop.ExcludeUserInputEvents)
            else:
                if outArgs is None:
                    started = QProcess.startDetached(cmd)
                else:
                    started = QProcess.startDetached(cmd, outArgs)
            if started:
                # Обнаружено, что некоторые программы (winword.exe, например)
                # сообщают об успешном выполнении до того, как реально начнут работать
                # Возможно это связано с тем, что второй экремпляр программы
                # просто передаёт первому имя файла и завершается.
                # Из-за этого мы успеваем удалить исходные файлы раньше, чем
                # программа их прочитает.
                # дадим 3 секунды на раскачку.
                while 0<=t.elapsed()<=3000:
                    QThread.msleep(stepTimeOut)
                    self.processEvents(QEventLoop.ExcludeUserInputEvents)
            return started, process.error() if process else None, process.exitCode() if process else None

        finally:
            self.restoreOverrideCursor()


    def editDocument(self,  textDocument):
        tmpDir = QtGui.qApp.getTmpDir('edit')
        try:
            fileName = os.path.join(tmpDir, 'document.html')
            txt = textDocument.toHtml(QByteArray('utf-8'))
            file = codecs.open(unicode(fileName), mode='w', encoding='utf-8')
            file.write(unicode(txt))
            file.close()
            started, error, exitCode = self.execProgram(self.documentEditor(), [fileName])
            if started:
                for enc in ('utf-8', 'cp1251'):
                    try:
                        file = codecs.open(fileName, mode='r', encoding=enc)
                        txt = file.read()
                        file.close()
                        textDocument.setHtml(txt)
                        return True
                    except:
                        pass
                QtGui.QMessageBox.critical(None,
                                       u'Внимание!',
                                       u'Не удалось загрузить "%s" после' % fileName,
                                       QtGui.QMessageBox.Close)
            else:
                QtGui.QMessageBox.critical(None,
                                       u'Внимание!',
                                       u'Не удалось запустить "%s"' % self.documentEditor(),
                                       QtGui.QMessageBox.Close)
        finally:
            QtGui.qApp.removeTmpDir(tmpDir)
        return False


    def startProgressBar(self, steps, format=u'%v из %m'):
        progressBar = self.mainWindow.getProgressBar()
        progressBar.setFormat(format)
        progressBar.setMinimum(0)
        progressBar.setMaximum(steps)
        progressBar.setValue(0)


    def stepProgressBar(self, step=1):
        progressBar = self.mainWindow.getProgressBar()
        progressBar.setValue(progressBar.value()+step)


    def stopProgressBar(self):
        self.mainWindow.hideProgressBar()


    def kerberosAuthEnabled(self):
        return True


    def passwordAuthEnabled(self):
        return True


    def demoModePosible(self):
        try:
            tableUser = self.db.table(tblUser)
            record = self.db.getRecordEx(tableUser,
                                         ['password = \'\' AS passwordIsEmpty',
                                          usrRetired
                                         ],
                                         [tableUser[usrLogin].eq(demoUserName),
                                          tableUser['deleted'].eq(0)
                                         ]
                                        )
            return record is None or (forceBool(record.value('passwordIsEmpty')) and not forceBool(record.value(usrRetired)))
        except:
            pass
        return False


    def setUserId(self, userId, demoMode=False, loginId=None):
        assert(userId or demoMode)

        self.demoMode = demoMode
        self.userId = userId
        self.loginId = loginId
        self.userSpecialityId = None
        self.userPostId = None
        self.userOrgStructureId = None

        db = self.db
        if db.isProcedureExists('registerUserLoginEx'):
            db.query(u'CALL registerUserLoginEx(%s, %s, %s)' % (str(userId) if userId else 'NULL',
                                                                quote(self.hostName),
                                                                quote(QtGui.qApp.getLatVersion()),
                                                              )
                    )
        elif db.isProcedureExists('registerUserLogin'):
            db.query(u'CALL registerUserLogin(%s, %s)' % (str(userId) if userId else 'NULL',
                                                          quote(self.hostName))
                                                         )

        if userId:
            record = db.getRecord('Person', ['speciality_id', 'orgStructure_id', 'post_id'], userId)
            if record:
                self.userSpecialityId = forceRef(record.value('speciality_id'))
                self.userOrgStructureId = forceRef(record.value('orgStructure_id'))
                self.userPostId = forceRef(record.value('post_id'))
        if demoMode:
            self.userInfo = CDemoUserInfo(userId)
        else:
            self.userInfo = CUserInfo(userId, loginId)
        self.emit(SIGNAL('currentUserIdChanged()'))


    def clearUserId(self, emitUserIdChanged=True):
        self.demoMode = False
        self.userId = None
        self.loginId = None
        self.userSpecialityId = None
        self.userOrgStructureId = None
        self.userInfo = None

        db = self.db
        if db.isProcedureExists('registerUserLogout'):
            db.query('CALL registerUserLogout()')
        if emitUserIdChanged:
            self.emit(SIGNAL('currentUserIdChanged()'))
        CPreCreateEventDialog.onCurrentUserIdChanged()


    def isUserAvailableJobTypeId(self, jobTypeId):
        return self.userInfo.isAvailableJobTypeId(jobTypeId)


    def isUserAvailableJobType(self, jobTypeCode):
        return self.userInfo.isAvailableJobType(jobTypeCode)


    def userAvailableJobTypeIdList(self):
        return self.userInfo.availableJobTypeIdList()


    def userName(self):
        if self.userInfo:
            orgId = self.currentOrgId()
            orgInfo = getOrganisationInfo(orgId)
            if not orgInfo:
                QtGui.qApp.preferences.appPrefs['orgId'] = QVariant()
            shortName = orgInfo.get('shortName', u'ЛПУ в настройках не указано!')
            return u'%s (%s) %s' % (self.userInfo.name(), self.userInfo.login(), shortName)
        else:
            return u''


    def userHasRight(self, right):
        return self.userInfo is not None and self.userInfo.hasRight(right)


    def userHasAnyRight(self, rights):
        return self.userInfo is not None and self.userInfo.hasAnyRight(rights)


    def currentOrgId(self):
        return forceRef(self.preferences.appPrefs.get('orgId', QVariant()))


    def getCurrentOrgOgrn(self):
        orgId = self.getCurrentOrgId()
        if orgId:
            return forceString( self.db.translate('Organisation', 'id', orgId, 'OGRN')
                              )
        else:
            return ''


#    def currentOrgStructureId(self):
#        return forceRef(QtGui.qApp.preferences.appPrefs.get('orgStructureId', QVariant()))
    def server(self):
        return forceString(QtGui.qApp.preferences.appPrefs.get('orgId', QVariant()))

    def currentOrgStructureId(self):
        return forceRef(QtGui.qApp.preferences.appPrefs.get('orgStructureId', QVariant())) or self.userOrgStructureId


    def filterPaymentByOrgStructure(self):
        return forceBool(QtGui.qApp.preferences.appPrefs.get('filterPaymentByOrgStructure', QVariant()))


    def useNativeFileDialog(self):
        return forceBool(QtGui.qApp.preferences.appPrefs.get('useNativeFileDialog', QVariant()))


    def emitCurrentClientInfoJLWChanged(self, scheduleItemId):
        # люди добрые, что такое JLW?
        self.emit(SIGNAL('currentClientInfoJLWChanged(int)'), scheduleItemId)


    def emitCurrentClientInfoSAChanged(self, scheduleItemId):
        # люди добрые, что такое SA?
        self.emit(SIGNAL('currentClientInfoSAChanged(int)'), scheduleItemId)


    def emitCurrentClientInfoJLWDeleted(self, scheduleItemId):
        self.emit(SIGNAL('currentClientInfoJLWDeleted(int)'), scheduleItemId)


    def setCurrentClientId(self, id):
        if self._currentClientId != id:
            self._currentClientId = id
            self.emit(SIGNAL('currentClientIdChanged()'))


    def emitCurrentClientInfoChanged(self):
        self.emit(SIGNAL('currentClientInfoChanged()'))


    def currentClientId(self):
        return self._currentClientId


    def canFindClient(self):
        return bool(self.mainWindow.registry)


    def findClient(self, clientId):
        if self.mainWindow.registry:
            self.mainWindow.registry.findClient(clientId)


    def identServiceEnabled(self):
        if self._identService is None:
            return forceBool(self.preferences.appPrefs.get('TFCheckPolicy', False))
        else:
            return True


    def identService(self, firstName, lastName, patrName, sex, birthDate, snils='', policyKind=0,  policySerial='', policyNumber='', docType=0, docSerial='', docNumber=''):
        if self._identService is None:
            url = forceString(self.preferences.appPrefs.get('TFCPUrl', ''))
            login    = forceString(self.preferences.appPrefs.get('TFCPLogin', ''))
            password = forceString(self.preferences.appPrefs.get('TFCPPassword', ''))
            self._identService = CTFUnifiedIdentService(url, login, password)
        try:
            if not self._identService.url:
                return None, None, u'Не указан адрес сервера'
            return self.callWithWaitCursor(self, self._identService.getPolicyAndAttach, firstName, lastName, patrName, sex, birthDate, snils, policyKind, policySerial, policyNumber, docType,  docSerial, docNumber)
        except Exception as e:
            self.logCurrentException()
            msg = u'Неизвестная ошибка'
            try:
                msg = unicode(e)
            except UnicodeDecodeError:
                msg = str(e)
            if anyToUnicode(msg) == u'timed out':
                msg = u'Сервис не отвечает, попробуйте воспользоваться им позже!'
            QtGui.QMessageBox.critical(None, u'Поиск полиса',
                                       u'Произошла ошибка при обращении к серверу проверки БД застрахованных:\n%s'
                                       % anyToUnicode(msg))
            return None, None, anyToUnicode(e.message)


    def TFAccountingSystemId(self):
        return forceRef(self.preferences.appPrefs.get('TFAccountingSystemId', None))


    def scannerEnabled(self):
        return forceBool(self.preferences.appPrefs.get('ScannerEnable', False))


    def scannerPortSettings(self):
        return CSerialSettings(forceString(self.preferences.appPrefs.get('ScannerPortSettings', '')))


    def scannerCorrectBackslashes(self):
        return forceBool(self.preferences.appPrefs.get('ScannerCorrectBackslashes', False))


    def scannerConnectionReport(self):
        return forceBool(self.preferences.appPrefs.get('ScannerConnectionReport', True))


    def scannerParseReport(self):
        return forceBool(self.preferences.appPrefs.get('ScannerParseReport', True))


    def getUserSnils(self):
        result = forceString(self.db.translate('Person', 'id', self.userId, 'SNILS'))
        if not result:
            raise Exception(u'Для текущего пользователя (Person.id=%s) не определён СНИЛС' % self.userId)
        return result


    def isCspDefined(self):
        return forceString(self.preferences.appPrefs.get('csp', '')) != ''


    def getCsp(self):
        result = forceString(self.preferences.appPrefs.get('csp', ''))
        if not result:
            # QtGui.QMessageBox.information(None, u'Внимание', u'В настройках не определён криптопровайдер')
            raise Exception(u'В настройках не определён криптопровайдер')
        return result


    def getUseOwnPk(self):
        return forceBool(self.preferences.appPrefs.get('useOwnPk', True))


    def getUserCertSha1(self):
        result = forceString(self.preferences.appPrefs.get('userCertSha1', ''))
        if not result:
            raise ECertNotFound(u'В настройках не определён сертификат пользователя')
        return result


    def getOrgCertSha1(self):
        result = forceString(self.preferences.appPrefs.get('orgCertSha1', ''))
#        if not result:
#            raise ECertNotFound(u'В настройках не определён сертификат медицинской организации')
        return result


    def getWarnAboutCertExpiration(self):
        return forceBool(self.preferences.appPrefs.get('warnAboutCertExpiration', False))


    def getCertExpirationWarnPeriod(self):
        return forceInt(self.preferences.appPrefs.get('certExpirationWarnPeriod', 7))

    
    def getAllowUnsignedAttachments(self):
        # разрешить прикрепление документов без ЭЦП
        return forceBool(self.preferences.appPrefs.get('allowUnsignedAttachments', False))

    def getAllowUnsignedAttachments(self):
        # разрешить прикрепление документов без ЭЦП
        return forceBool(self.preferences.appPrefs.get('allowUnsignedAttachments', True))


    def getFssServiceUrl(self):
        result = forceString(self.preferences.appPrefs.get('fssServiceUrl', ''))
        if not result:
            db = QtGui.qApp.db
            tableGP = db.table('GlobalPreferences')
            recordUrlELN = db.getRecordList(tableGP, 'value', [tableGP['note'].eq('ELN')], 'code')
            result = [forceString(item.value('value')) for item in recordUrlELN if recordUrlELN]
        if not result:
            raise Exception(u'В настройках не определён URL сервиса ЭЛН СФР')
        return result


    def getFssServiceERSUrl(self):
        result = forceString(self.preferences.appPrefs.get('fssServiceERSUrl', ''))
        if not result:
            db = QtGui.qApp.db
            tableGP = db.table('GlobalPreferences')
            recordUrlERS = db.getRecordList(tableGP, 'value', [tableGP['note'].eq('ERS')], 'code')
            result = [forceString(item.value('value')) for item in recordUrlERS]
        if not result:
            raise Exception(u'В настройках не определён URL сервиса ЭРС СФР')
        return result


    def getFssUseEncryption(self):
        return forceBool(self.preferences.appPrefs.get('fssUseEncryption', False))


    def getFssCertSha1(self):
        result = forceString(self.preferences.appPrefs.get('fssCertSha1', ''))
        if not result:
            raise Exception(u'В настройках не определён сертификат СФР')
        return result


    def getFssProxyPreferences(self):
        props = self.preferences.appPrefs
        useProxy = forceBool(props.get('fssUseProxy', False))

        proxyAddress  = None
        proxyPort     = None
        proxyLogin    = None
        proxyPassword = None

        if useProxy:
            proxyAddress = forceString(props.get('fssProxyAddress', ''))
            proxyPort    = forceInt(props.get('fssProxyPort', 0))
            proxyUseAuth = forceBool(props.get('fssProxyUseAuth', False))
            if proxyUseAuth:
                proxyLogin    = forceString(props.get('fssProxyLogin', ''))
                proxyPassword = forceString(props.get('fssProxyPassword', ''))

        return { 'address' : proxyAddress,
                 'port'    : proxyPort,
                 'login'   : proxyLogin,
                 'password': proxyPassword,
               }


    def getGPSpecialityId(self):
        if self._gpSpecialityId is None:
            self._gpSpecialityId = ( forceRef(self.db.translate('rbSpeciality', 'federalCode', '2019', 'id'))
                                     or forceRef(self.db.translate('rbSpeciality', 'OKSOCode',    '040819', 'id'))
                                   )
        return self._gpSpecialityId


    def getIdentCardServiceUrl(self):
        url = forceStringEx(self.preferences.appPrefs.get('identCardServiceUrl', ''))
        if not url:
            url = self._globalPreferences.get('identCardServiceUrl', None)
        if url:
            url = url.replace('${dbServerName}', self.preferences.dbServerName)
        else:
            url = None
        return url


    def ekpBarCodeEnabled(self):
        return (     self.defaultKLADR().startswith('78')
                 and forceBool(self.preferences.appPrefs.get('ekpBarCodeEnabled', True))
               )


    def ekpContactlessEnabled(self):
        return (     self.defaultKLADR().startswith('78')
                 and forceBool(self.preferences.appPrefs.get('ekpContactlessEnabled', True))
               )


    def ekpContactlessCheckATR(self):
        return forceBool(self.preferences.appPrefs.get('ekpContactlessCheckATR', True))


    def ekpContactlessReaders(self):
        return forceString(self.preferences.appPrefs.get('ekpContactlessReaders', ''))


    def ekpContactEnabled(self):
        return (     self.defaultKLADR().startswith('78')
                 and forceBool(self.preferences.appPrefs.get('ekpContactEnabled', True))
               )


    def ekpContactCheckATR(self):
        return forceBool(self.preferences.appPrefs.get('ekpContactCheckATR', True))


    def ekpContactReaders(self):
        return forceString(self.preferences.appPrefs.get('ekpContactReaders', ''))


    def ekpContactLib(self):
        return forceString(self.preferences.appPrefs.get('ekpContactLib', ''))


    def isDockDiagnosisAnalyzeSurveillance(self):
        return forceBool(self.preferences.appPrefs.get('dockDiagnosisAnalyzeSurveillance', False))


    def requestNewEvent(self, clientId, typeQueue=-1):
        if self.mainWindow.registry:
            self.mainWindow.registry.findClient(clientId)
            self.mainWindow.registry.requestNewEventQueue(typeQueue)


    def canFindEvent(self):
        return bool(self.mainWindow.registry)


    def findEvent(self, id):
        if self.mainWindow.registry:
            self.mainWindow.registry.findEvent(id)


    def setEventList(self, idList):
        if self.mainWindow.registry:
            self.mainWindow.registry.setEventList(idList)


    def addMruEvent(self, eventId, descr):
        self.mainWindow.addMruEvent(eventId, descr)


    def clearPreferencesCache(self):
        self._defaultKLADR = None
        self._provinceKLADR = None
        self._averageDuration = None
        self._voucherDuration = None
        self._highlightRedDate = None
        self._highlightInvalidDate = None
        self._identService = None
        self.accountingSystem = None
        self.loadGlobalPreferences()


    def defaultKLADR(self):
        # код КЛАДР по умолчанию
        if self._defaultKLADR is None:
            self._defaultKLADR = forceString(self.preferences.appPrefs.get('defaultKLADR', ''))
            if not self._defaultKLADR:
                self._defaultKLADR = '7800000000000'
        return self._defaultKLADR


    def provinceKLADR(self):
        # областной код КЛАДР по умолчанию
        if self._provinceKLADR is None:
            self._provinceKLADR = forceString(self.preferences.appPrefs.get('provinceKLADR', ''))
            if not self._provinceKLADR:
                self._provinceKLADR = getProvinceKLADRCode(self.defaultKLADR())
        return self._provinceKLADR


    def averageDuration(self):
        # средняя длительность заболевания
        if self._averageDuration is None:
            self._averageDuration = forceInt(self.preferences.appPrefs.get('averageDuration', DefaultAverageDuration))
        return self._averageDuration


    def voucherDuration(self):
        # длительность путевки по умолчанию
        if self._voucherDuration is None:
            self._voucherDuration = forceInt(self.preferences.appPrefs.get('voucherDuration', DefaultVoucherDuration))
        return self._voucherDuration


    def tempInvalidDoctype(self):
        # возвращает код документа временной нетрудоспособности
        return forceString(self.preferences.appPrefs.get('tempInvalidDoctype', ''))


    def tempInvalidReason(self):
        # возвращает код причины временной нетрудоспособности
        return forceString(self.preferences.appPrefs.get('tempInvalidReason', ''))


    def tempInvalidRegime(self):
        # возвращает код режима временной нетрудоспособности
        return forceRef(self.preferences.appPrefs.get('tempInvalidRegime', None))


    def tempInvalidRequestFss(self):
        # Запрашивать СФР на наличие открытых ЭЛН при создании нового эпизода ВУТ
        return forceBool(self.preferences.appPrefs.get('tempInvalidRequestFss', False))


    def enableFastPrint(self):
        return forceBool(self.preferences.appPrefs.get('enableFastPrint', False))


    def enablePreview(self):
        # отображение предварительного просмотра при печати
        return forceBool(self.preferences.appPrefs.get('enablePreview', False))


    def printFullPage(self):
        # отключить границы печати по настройкам принтера
        return forceBool(self.preferences.appPrefs.get('printFullPage', False))


    def showPageSetup(self):
        # отображение окна настроек параметров страницы при печати
        return forceBool(self.preferences.appPrefs.get('showPageSetup', False))


    def labelPrinter(self):
        printerName = forceString(self.preferences.appPrefs.get('labelPrinter', ''))
        if 'QPrinterInfo' in QtGui.__dict__: # work-around for current version of pyqt in ubuntu 8.04
            printerInfoList = [ pi for pi in  QtGui.QPrinterInfo.availablePrinters() if pi.printerName() == printerName ]
        else:
            printerInfoList = []
        if printerInfoList:
            return QtGui.QPrinter(printerInfoList[0], QtGui.QPrinter.HighResolution)
        else:
            return None


    def surgeryPageRestrictFormation(self):
        # Ограничить формирование журнала операций.
        return forceInt(self.preferences.appPrefs.get('surgeryPageRestrictFormation', 0))


    def surgeryPageOrgStructureId(self):
        # Ограничить формирование журнала операций, параметр "Подразделение".
        return forceRef(self.preferences.appPrefs.get('surgeryPageOrgStructureId', 0))


    def showingFormTempInvalid(self):
        # отображение вкладки "Трудоспособность" в форие ввода:
        return forceBool(self.preferences.appPrefs.get('showingFormTempInvalid', True))


    def showingClientCardVoluntaryPolicyNote(self):
        # отображение в Регистрационная карта пациента Поле "Примечание" полиса ДМС:
        return forceBool(self.preferences.appPrefs.get('showingClientCardVoluntaryPolicyNote', True))


    def showingClientCardVoluntaryPolicyName(self):
        # отображение в Регистрационная карта пациента Поле "Название" полиса ДМС:
        return forceBool(self.preferences.appPrefs.get('showingClientCardVoluntaryPolicyName', True))


    def showingClientCardCompulsoryPolisNote(self):
        # отображение в Регистрационная карта пациента Поле "Примечание" полиса ОМС:
        return forceBool(self.preferences.appPrefs.get('showingClientCardCompulsoryPolisNote', True))


    def showingClientCardCompulsoryPolisName(self):
        # отображение в Регистрационная карта пациента Поле "Название" полиса ОМС:
        return forceBool(self.preferences.appPrefs.get('showingClientCardCompulsoryPolisName', True))


    def showingClientCardDocOrigin(self):
        # отображение в Регистрационная карта пациента Поле "Кем выдан" документа, удостоверяющего личность:
        return forceBool(self.preferences.appPrefs.get('showingClientCardDocOrigin', True))


    def checkClientCardPolicyAffiliation(self):
        # Контроль проверки страховой принадлежности в Регистрационная карта пациента: 1)Не выполнять, 2)Мягко, 3)Строго.
        return forceInt(self.preferences.appPrefs.get('checkClientCardPolicyAffiliation', 0))


    def showingClientCardDeathDate(self):
        # отображение в Регистрационная карта пациента даты смерти:
        return forceBool(self.preferences.appPrefs.get('showingClientCardDeathDate', True))


    def showingClientCardBirthTime(self):
        # отображение в Регистрационная карта пациента времени рождения:
        return forceBool(self.preferences.appPrefs.get('showingClientCardBirthTime', True))


    def showingClientCardSNILS(self):
        # отображение в Регистрационная карта пациента СНИЛС:
        return forceBool(self.preferences.appPrefs.get('showingClientCardSNILS', True))


    def showingClientCardVoluntaryPolicy(self):
        # отображение в Регистрационная карта пациента данных полиса ДМС:
        return forceBool(self.preferences.appPrefs.get('showingClientCardVoluntaryPolicy', True))


    def showingClientCardTabAttach(self):
        # отображение в Регистрационная карта пациента вкладки Прикрепление:
        return forceBool(self.preferences.appPrefs.get('showingClientCardTabAttach', True))


    def showingClientCardTabWork(self):
        # отображение в Регистрационная карта пациента вкладки Занятость:
        return forceBool(self.preferences.appPrefs.get('showingClientCardTabWork', True))


    def showingClientCardTabQuoting(self):
        # отображение в Регистрационная карта пациента вкладки Квоты:
        return forceBool(self.preferences.appPrefs.get('showingClientCardTabQuoting', True))


    def showingClientCardTabDeposit(self):
        # отображение в Регистрационная карта пациента вкладки Депозитная карта:
        return forceBool(self.preferences.appPrefs.get('showingClientCardTabDeposit', True))


    def showingClientCardTabSocStatus(self):
        # отображение в Регистрационная карта пациента вкладки Соц.статус:
        return forceBool(self.preferences.appPrefs.get('showingClientCardTabSocStatus', True))


    def showingClientCardTabChangeJournal(self):
        # отображение в Регистрационная карта пациента вкладки Журнал изменений:
        return forceBool(self.preferences.appPrefs.get('showingClientCardTabChangeJournal', True))


    def showingClientCardTabFeature(self):
        # отображение в Регистрационная карта пациента вкладки Особенности:
        return forceBool(self.preferences.appPrefs.get('showingClientCardTabFeature', True))


    def showingClientCardTabResearch(self):
        # отображение в Регистрационная карта пациента вкладки Обследования:
        return forceBool(self.preferences.appPrefs.get('showingClientCardTabResearch', True))


    def showingClientCardTabDangerous(self):
        # отображение в Регистрационная карта пациента вкладки Общ. опасность:
        return forceBool(self.preferences.appPrefs.get('showingClientCardTabDangerous', True))


    def showingClientCardTabContingentKind(self):
        # отображение в Регистрационная карта пациента вкладки контингент:
        return forceBool(self.preferences.appPrefs.get('showingClientCardTabContingentKind', True))

    def showingClientCardTabHospitalization(self):
        # отображение в Регистрационная карта пациента вкладки Сведения о госпитализациях:
        return forceBool(self.preferences.appPrefs.get('showingClientCardTabHospitalization', True))

    def showingClientCardTabIdentification(self):
        # отображение в Регистрационная карта пациента вкладки Идентификация:
        return forceBool(self.preferences.appPrefs.get('showingClientCardTabIdentification', True))


    def showingClientCardTabRelations(self):
        # отображение в Регистрационная карта пациента вкладки Связи:
        return forceBool(self.preferences.appPrefs.get('showingClientCardTabRelations', True))


    def showingClientCardTabContacts(self):
        # отображение в Регистрационная карта пациента вкладки Прочее:
        return forceBool(self.preferences.appPrefs.get('showingClientCardTabContacts', True))


    def showingClientCardTabConsent(self):
        # отображение в Регистрационная карта пациента вкладки Согласия:
        return forceBool(self.preferences.appPrefs.get('showingClientCardTabConsent', True))


    def showingClientCardTabMonitoring(self):
        # отображение в Регистрационная карта пациента вкладки Мониторинг:
        return forceBool(self.preferences.appPrefs.get('showingClientCardTabMonitoring', True))


    def showingClientCardTabEpidCase(self):
        # отображение в Регистрационная карта пациента вкладки ЭпидНаблюдение:
        return forceBool(self.preferences.appPrefs.get('showingClientCardTabEpidCase', True))

    
    def showingHospitalBedsTabDeath(self):
        # отображение в Стационарный монитор вкладки Умерло:
        return forceBool(self.preferences.appPrefs.get('showingHospitalBedsTabDeath', True))
    
    
    def showingHospitalBedsTabEmergency(self):
        # отображение в Стационарный монитор пациента вкладки СМП:
        return forceBool(self.preferences.appPrefs.get('showingHospitalBedsTabEmergency', True))
    
    
    def showingHospitalBedsTabFund(self):
        # отображение в Стационарный монитор пациента вкладки Коечный фонд:
        return forceBool(self.preferences.appPrefs.get('showingHospitalBedsTabFund', True))
    
    
    def showingHospitalBedsTabLeaved(self):
        # отображение в Стационарный монитор пациента вкладки Выбыли:
        return forceBool(self.preferences.appPrefs.get('showingHospitalBedsTabLeaved', True))
    
    
    def showingHospitalBedsTabPresence(self):
        # отображение в Стационарный монитор пациента вкладки Присутствуют:
        return forceBool(self.preferences.appPrefs.get('showingHospitalBedsTabPresence', True))
    
    
    def showingHospitalBedsTabQueue(self):
        # отображение в Стационарный монитор пациента вкладки В очереди:
        return forceBool(self.preferences.appPrefs.get('showingHospitalBedsTabQueue', True))
    
    
    def showingHospitalBedsTabReadyToLeave(self):
        # отображение в Стационарный монитор пациента вкладки Готовы к выбытию:
        return forceBool(self.preferences.appPrefs.get('showingHospitalBedsTabReadyToLeave', True))
    
    
    def showingHospitalBedsTabReanimation(self):
        # отображение в Стационарный монитор пациента вкладки Реанимация:
        return forceBool(self.preferences.appPrefs.get('showingHospitalBedsTabReanimation', False))
    
    
    def showingHospitalBedsTabReceived(self):
        # отображение в Стационарный монитор пациента вкладки Поступили:
        return forceBool(self.preferences.appPrefs.get('showingHospitalBedsTabReceived', True))
    
    
    def showingHospitalBedsTabRenunciation(self):
        # отображение в Стационарный монитор пациента вкладки Отказ от госпитализации:
        return forceBool(self.preferences.appPrefs.get('showingHospitalBedsTabRenunciation', True))
    
    
    def showingHospitalBedsTabTransfer(self):
        # отображение в Стационарный монитор пациента вкладки Переведены (в отделение):
        return forceBool(self.preferences.appPrefs.get('showingHospitalBedsTabTransfer', True))


    def showingSpellCheckHighlight(self):
        # отображение Проверки правописания:
        return forceBool(self.preferences.appPrefs.get('showingSpellCheckHighlight', True))


    def pathToPersonalDict(self):
        # выбор пути до персонального словаря
        return forceString(QtGui.qApp.preferences.appPrefs.get('edtPathToPersonalDict', ''))


    def lloServiceUrl(self):
        # адрес сервиса льготно-лекарственного обеспечения
        return forceString(QtGui.qApp.preferences.appPrefs.get('edtlloUrl', ''))


    def lloRecipientCode(self):
        # код получателя в сервисе льготно-лекарственного обеспечения
        return forceString(QtGui.qApp.preferences.appPrefs.get('edtRecipientCode', ''))


    def lloRecipientName(self):
        # наименование получателя в сервисе льготно-лекарственного обеспечения
        return forceString(QtGui.qApp.preferences.appPrefs.get('edtRecipientName', ''))


    def lloTestMode(self):
        # Включение/отключение тестового режима для сервиса ЛЛО:
        return forceBool(self.preferences.appPrefs.get('chkRecipeTestIsOn', True))


    def lloLogin(self):
        # Логин сервиса льготно-лекарственного обеспечения
        return forceString(QtGui.qApp.preferences.appPrefs.get('edtlloLogin', ''))


    def lloPassword(self):
        # Пароль сервиса льготно-лекарственного обеспечения
        return forceString(QtGui.qApp.preferences.appPrefs.get('edtlloPassword', ''))


    def informerShowPersonSNILS(self):
        # Информатор: фильтровать уведомления по СНИЛСу пользователя:
        return forceBool(self.preferences.appPrefs.get('informerShowPersonSNILS', False))


    def informerShowNoSNILS(self):
        # Информатор: показывать уведомления без СНИЛС:
        return forceBool(self.preferences.appPrefs.get('informerShowNoSNILS', False))


    def informerShowByUserArea(self):
        # Информатор: фильтровать уведомления по участку пользователя:
        return forceBool(self.preferences.appPrefs.get('informerShowByUserArea', False))


    def informerShowByUserNotArea(self):
        # Информатор: фильтровать уведомления по пациентам без участка:
        return forceBool(self.preferences.appPrefs.get('informerShowByUserNotArea', False))


    def disableCheckDB(self):
        return forceBool(self.preferences.appPrefs.get('disableCheckDB', False))


    def showingInInfoBlockSocStatus(self):
        # отображение в информационном блоке данных по Соц.статусу в возможных вариантах:
        # 0: код
        # 1: наименование
        # 2: код и наименование
        return forceInt(self.preferences.appPrefs.get('showingInInfoBlockSocStatus', 0))

    
    def showingAttach(self):
        # отображение закрытого прикрепления в шильдике
        return forceBool(self.preferences.appPrefs.get('showingAttach', False))
    

    def doubleClickQueuePerson(self):
        # изменение двойного щелчка в листе предварительной записи врача
        # 0: изменить жалобы/примечания
        # 1: перейти в картотеку
        # 2: новое обращение
        return forceInt(self.preferences.appPrefs.get('doubleClickQueuePerson', 0))


    def doubleClickQueueClient(self):
        # реакция на двойной щелчок в листе предварительной записи пациента
        # 0: Нет действия
        # 1: новое обращение
        # 2: изменить жалобы/примечания
        # 3: напечатать приглашение
        # 4: перейти в график
        return forceInt(self.preferences.appPrefs.get('doubleClickQueueClient', 0))


    def onSingleClientInSearchResult(self):
        # действие в случае, если поиск пациента закончился единственным пациентом
        # 0: Нет действия
        # 1: новое обращение
        # 2: открыть прививочную карту
        return forceInt(self.preferences.appPrefs.get('onSingleClientInSearchResult', 0))



    def doubleClickQueueFreeOrder(self):
        # изменение двойного щелчка в списке свободных номерков
        # 0: Нет действия
        # 1: Поставить в очередь
        # 2: Выполнить бронирование
        return forceInt(self.preferences.appPrefs.get('doubleClickQueueFreeOrder', 0))


    def diagnosisTypeAfterFinalForm043(self):
        # Предпочитаемый тип диагноза в форме ввода 043 после закл:
        # 0: Сопутствующий
        # 1: Основной
        return forceInt(self.preferences.appPrefs.get('diagnosisTypeAfterFinalForm043', 0))


    def jobsOperatingIdentifierScan(self):
        # выполнение работ - выбор идентификатора
        # 0: Идентификатор направления
        # 1: Идентификатор биоматериала
        # 2: Идентификатор пробы
        return forceInt(self.preferences.appPrefs.get('jobsOperatingIdentifierScan', 0))


    def ambulanceUserCheckable(self):
        return forceBool(QtGui.qApp.preferences.appPrefs.get('ambulanceUserCheckable', False))


    def syncCheckableAndInvitiation(self):
        return forceBool(QtGui.qApp.preferences.appPrefs.get('syncCheckableAndInvitiation', False))


    def combineTimetable(self):
        # Управление объединением расписания на сутки в панели "номерки"
        # 0 - не объединять расписание
        # 1 - объединять по назначению приёма
        # 2 - объединять расписание независимо от назначения приёма
        return forceInt(QtGui.qApp.preferences.appPrefs.get('combineTimetable', 0))


    def highlightRedDate(self):
        if self._highlightRedDate is None:
            self._highlightRedDate = forceBool(QtGui.qApp.preferences.appPrefs.get('highlightRedDate', False))
        return self._highlightRedDate


    def highlightInvalidDate(self):
        if self._highlightInvalidDate is None:
            self._highlightInvalidDate = forceBool(QtGui.qApp.preferences.appPrefs.get('highlightInvalidDate', False))
        return self._highlightInvalidDate


    def documentEditor(self):
        return forceString(QtGui.qApp.preferences.appPrefs.get('documentEditor', ''))


    def cashBox(self):
        # номер кассы
        return forceString(self.preferences.appPrefs.get('cashBox', ''))


    def directoryExportDocuments(self):
        # путь к каталогу для выгрузки прикреплённых документов
        return forceString(self.preferences.appPrefs.get('directoryExportDocuments', ''))


    def defaultAccountingSystem(self):
        if self.accountingSystem is None:
            id = None
            name = None
            code = self.getGlobalPreference('3')
            if code is not None:
                table = self.db.table('rbAccountingSystem')
                record = self.db.getRecordEx(table, ['id', 'name'], table['code'].eq(code))
                if record:
                    id = forceRef(record.value('id'))
                    name = forceString(record.value('name'))
            self.accountingSystem = id, name
        return self.accountingSystem


    def defaultAccountingSystemId(self):
        return self.defaultAccountingSystem()[0]


    def defaultAccountingSystemName(self):
        return self.defaultAccountingSystem()[1]


    def defaultMorphologyMKBIsVisible(self):
        if self.morphologyMKBIsVisible is None:
            self.morphologyMKBIsVisible = self.checkGlobalPreference('2', u'да')
        return self.morphologyMKBIsVisible


    def gis_oms_enable(self):
        return self.checkGlobalPreference('useServiceGISOMS', u'да')


    def defaultHospitalBedProfileByMoving(self):
        # ЭТА ГЛОБАЛЬНАЯ НАСТРОЙКА ВРЕМЕННО ЗАМОРОЖЕНА.
#        # Учитывать профиль койки по движению:
#        # нет: по койке
#        # да:  по движению
#        #if self.isHospitalBedProfileByMoving is None:
#        #self.isHospitalBedProfileByMoving = self.checkGlobalPreference('5', u'да')
        self.isHospitalBedProfileByMoving = False
        return self.isHospitalBedProfileByMoving


    def defaultNeedPreCreateEventPerson(self):
        # необходимость контроля ответственного врача в диалоге 'новое обращение'
        if self.isNeedPreCreateEventPerson is None:
            self.isNeedPreCreateEventPerson = self.checkGlobalPreference('6', u'да')
        return self.isNeedPreCreateEventPerson


    def defaultIsManualSwitchDiagnosis(self):
        # Механизм учёта острых заболеваний:
        # по средней длительности
        # в ручную
        if self.isManualSwitchDiagnosis is None:
            self.isManualSwitchDiagnosis = self.checkGlobalPreference('1', u'в ручную')
        return self.isManualSwitchDiagnosis



    def isExSubclassMKBVisible(self):
        return self.checkGlobalPreference('exSubclassMKB', u'да')


    def refundRegistrationEnabled(self):
        return self.checkGlobalPreference('refundRegistration', u'да')


    def isClinicalGroupDiagnosticVisible(self):
        return self.checkGlobalPreference('showClinicalGroupDiagnostic', u'да')


    def isTNMSVisible(self):
        return self.checkGlobalPreference('7', u'да')
#        checkGlobalPreferenceList = {u'не выполнять':0, u'мягкий':1, u'жёсткий':2}
#        value = self._globalPreferences.get(u'7', None)
#        if value:
#            return checkGlobalPreferenceList.get(unicode(value).lower(), None)
#        return None


#    def getLevelFromGlobalPreference(self, preferenceCode):
#        checkGlobalPreferenceList = {u'нет':0, u'да':1, u'не выполнять':2}
#        value = self._globalPreferences.get(code, None)
#        return checkGlobalPreferenceList.get(unicode(value), None)


    def isStrictPolicyCheckOnEventCreation(self):
        return self.isStrictCheckOn('4')


    def isStrictAttachCheckOnEventCreation(self):
        return self.isStrictCheckOn('8')


    def isStrictCheckPolicyOnEndAction(self):
        return self.isStrictCheckOn('16')


    def isStrictCheckAttachOnEndAction(self):
        return self.isStrictCheckOn('17')


    def isStrictCheckOn(self, code):
        checkGlobalPreferenceList = {u'нет':0, u'да':1, u'не выполнять':2}
        value = self._globalPreferences.get(code, None)
        return checkGlobalPreferenceList.get(unicode(value), None)


    def isStrictCheckControlAddress(self):
        return self.isCheckOnControlAddress('25')


    def isCheckOnControlAddress(self, code):
        checkGlobalPreferenceList = {u'не выполнять':0, u'выполнять':1}
        value = self._globalPreferences.get(code, None)
        return checkGlobalPreferenceList.get(unicode(value), None)


    def getStrictCheckMKBreceivedOMS(self):
        checkGlobalPreferenceList = {u'не выполнять':0, u'мягкий':1, u'строгий':2}
        value = self._globalPreferences.get(u'23:checkMKBreceivedOMS', None)
        return checkGlobalPreferenceList.get(unicode(value), None)

    
    def getEventTimeout(self):
        value = forceInt(self._globalPreferences.get('23:EventTimeout', 0))
        if value>120 or value<2: value=0
        return value


    def getConnectionTimeout(self):
        value = forceInt(self._globalPreferences.get('23:ConnectionTimeout', 0))
        if value > 120 or value < 2:
            value = 0
        return value


    def getScheduleFIOAppointment(self):
        return self.checkGlobalPreference('23:ScheduleFIOAppointment', u'да')
    
    
    def getKladrResearch(self):
        return self.checkGlobalPreference('23:KladrResearch', u'да')
    
    
    def getOpeningSnilsCardindex(self):
        return self.checkGlobalPreference('23:OpeningSnilsCardindex', u'да')
    

    def getStrictCheckReceivedControlSMP(self):
        checkGlobalPreferenceList = {u'не выполнять': 0, u'мягкий': 1, u'жесткий': 2, u'жёсткий': 2}
        value = self._globalPreferences.get(u'23:receivedControlSMP', None)
        return checkGlobalPreferenceList.get(unicode(value), None)


    def getRegAddressDate(self):
        checkGlobalPreferenceList = {u'не выполнять':0, u'мягкий':1, u'жесткий':2}
        value = self._globalPreferences.get(u'RegAddressDate', None)
        return checkGlobalPreferenceList.get(unicode(value).lower(), None)


    def getStrictCheckSocStatus(self):
        checkGlobalPreferenceList = {u'нет':0, u'мягко':1, u'жестко':2}
        value = self._globalPreferences.get('27', '')
        value = value.replace(u';', u';')
        value = value.replace(u',', u',')
        value = value.replace(u':', u':')
        resList = value.split(u';')
        if len(resList) > 1:
            checkVal = resList[0]
            socStatusVal = resList[1]
        else:
            return 0, []
        isCheckSocStatus = checkGlobalPreferenceList.get(checkVal, None)
        socStatusRes = []
        if isCheckSocStatus:
            socStatusList = socStatusVal.split(u',')
            db = QtGui.qApp.db
            table = db.table('rbSocStatusClass')
            for socStatus in socStatusList:
                socStatusCodeList = socStatus.split(u':')
                if len(socStatusCodeList) > 1:
                    groupCode = socStatusCodeList[0]
                    code = socStatusCodeList[1]
                    cond = [table['code'].eq(code),
                            table['group_id'].isNotNull()
                            ]
                    cond.append(u'''rbSocStatusClass.group_id IN (SELECT SSC.id
                    FROM rbSocStatusClass AS SSC
                    WHERE SSC.code = %s AND SSC.id != rbSocStatusClass.id)'''%(groupCode))
                    record = db.getRecordEx(table, [table['id']], cond)
                    if record:
                        socStatusRes.append(forceRef(record.value('id')))
                else:
                    code = socStatusCodeList[0]
                    cond = [table['code'].eq(code),
                            table['group_id'].isNull()
                            ]
                    record = db.getRecordEx(table, [table['id']], cond)
                    if record:
                        socStatusRes.append(forceRef(record.value('id')))
        return isCheckSocStatus, socStatusRes


    def defaultHospitalBedFinanceByMoving(self):
        # Глобальная настройка для определения правила учета источника финансирования в стац. мониторе:
        # по событию
        # по движению
        # по движению или событию
        if self.isHospitalBedFinanceByMoving is None:
            self.isHospitalBedFinanceByMoving = self.checkGlobalPreferenceHospitalBedFinance('9')
        return self.isHospitalBedFinanceByMoving


    def checkGlobalPreferenceHospitalBedFinance(self, code):
        checkGlobalPreferenceList = {u'по событию':0, u'по движению':1, u'по движению или событию':2}
        value = self._globalPreferences.get(code, None)
        if value:
            return checkGlobalPreferenceList.get(unicode(value).lower(), None)
        return None


    def isRestrictedEventCreationByContractPresence(self):
        return self.checkGlobalPreference('10', u'да')


    def isNextEventCreationFromAction(self):
        checkGlobalPreferenceList = {u'никогда':0, u'иногда':1, u'всегда':2}
        value = self._globalPreferences.get('11', None)
        if value:
            return checkGlobalPreferenceList.get(unicode(value).lower(), None)
        return None


    def isTimelineAccessibilityDays(self):
        code = '12'
        checkGlobalPreferenceList = {u'Внешняя ИС':0, u'Вся ИС':1}
        value = self._globalPreferences.get(code, None)
        if value:
            return checkGlobalPreferenceList.get(unicode(value), None)
        return None


    def isCheckedEventForPersonOrSpeciality(self):
        return self.checkGlobalPreference('13', u'по врачу')


    def isDisabledEventForPersonOrSpeciality(self):
        return self.checkGlobalPreference('13', u'не выполнять')


    def isExistsActionControlledInAddActionF9(self):
        return self.explainGlobalPreference('14', {u'не выполнять':0, u'мягкий':1, u'строгий':2})


    def isGetPersonStationary(self):
        return self.checkGlobalPreference('15', u'да')


    def isReStagingInQueue(self):
        # Повторная постановка в очередь(да, нет)
        # Когда пациент уже записан к врачу этой специальности, может возникнуть необходимость подтвердить повторную запись.
        return self.checkGlobalPreference('18', u'да')


    def isCheckClientHouses(self):
        # Выполнять контроль номера дома по КЛАДР, по умолчанию - нет
        return self.checkGlobalPreference('21', u'да')


    def isCheckEventJournalOfPerson(self):
        # Использовать Журнал назначения лечащего врача, по умолчанию - нет
        return self.checkGlobalPreference('26', u'да')

    def needSaveTissueOnSaveJT(self):
        # Необходимость сохранения забора биоматериала при нажатии кнопки ОК в редакторе работы
        return self.checkGlobalPreference('saveTissueOnSaveJT', u'да', default=u'да')

    def getStockMotionNumberGlobalCounterCode(self):
        return self.getGlobalPreference('SMCounterCode')

    def askCloseJTAfterIBMBarCodeScanning(self):
        return self.checkGlobalPreference('askCloseJTAfterIBMBarCodeScanning', u'да')

    def explainGlobalPreference(self, code, checkGlobalPreferenceList):
        value = self.getGlobalPreference(code)
        if value:
            return checkGlobalPreferenceList.get(unicode(value).lower(), None)
        return None


    def isUniqueNumberCardCall(self):
        checkGlobalPreferenceList = {u'не выполнять':0, u'мягкий':1, u'жёсткий':2}
        value = self._globalPreferences.get(u'uniqueNumberCard', None)
        if value:
            return checkGlobalPreferenceList.get(unicode(value).lower(), None)
        return None


    def controlHBPatronChanges(self):
        checkGlobalPreferenceList = {u'мягкий':0, u'жёсткий':1}
        value = self._globalPreferences.get(u'patronChanges', None)
        if value:
            return checkGlobalPreferenceList.get(unicode(value).lower(), None)
        return None


    def controlSMFinance(self):
        #контроль типа финансирования ЛСиИМН при назначении и списании в соответствии с типом финансирования события
        checkGlobalPreferenceList = {u'не выполнять':0, u'мягкий':1, u'жёсткий':2}
        value = self._globalPreferences.get(u'SMFinanceControl', None)
        if value:
            return checkGlobalPreferenceList.get(unicode(value).lower(), None)
        return None


    def controlNomenclatureExpense(self):
        #Контроль наличия ЛСиИМН после добавления действия с настроенным "Учетом ТМЦ" в событие в момент создания документа на списание ЛСиИМН на пациента (обычно момент сохранения/закрытия события).
        #Окно можно только пропустить, после чего событие окончательно сохраняется/закрывается. Задача №0011017.
        checkGlobalPreferenceList = {u'не выполнять':0, u'выполнять':1}
        value = self._globalPreferences.get(u'nomenclatureExpense', None)
        if value:
            return checkGlobalPreferenceList.get(unicode(value).lower(), None)
        return None


    def controlExecutionWriteOffNomenclatureExpense(self):
        # Контроль выполнения списаний ЛСиИМН.
        # Задача #0011442: Учет ЛСиИМН. Проверка наличия ЛС при списании.
        checkGlobalPreferenceList = {u'не выполнять': 0, u'мягкий': 1, u'жесткий': 2}
        value = self._globalPreferences.get(u'controlExecutionWriteOffNE', None)
        if value:
            return checkGlobalPreferenceList.get(unicode(value).lower(), None)
        return None


    def controlFillingFieldsNomenclatureExpense(self):
        #ЛСиИМН проверка заполнения полей при назначении ЛС. Задача 0011741.
        checkGlobalPreferenceList = {u'не выполнять':0, u'выполнять':1}
        value = self._globalPreferences.get(u'controlFillingFieldsNomenclatureExpense', None)
        if value:
            return checkGlobalPreferenceList.get(unicode(value).lower(), None)
        return None


    def admissibilityNomenclatureExpensePostDates(self):
        #Допустимость списания ЛСиИМН за прошедшие даты
        checkGlobalPreferenceList = {u'не учитывать':0, u'прошедший день':1, u'текущий месяц':2}
        value = self._globalPreferences.get(u'admissibilityNEPostDates', None)
        if value:
            return checkGlobalPreferenceList.get(unicode(value).lower(), None)
        return None


    def controlSNILSTempInvalid(self):
        checkGlobalPreferenceList = {u'мягкий':0, u'жёсткий':1}
        value = self._globalPreferences.get(u'checkSNILSTI', None)
        if value:
            return checkGlobalPreferenceList.get(unicode(value).lower(), None)
        return None


    def controlDiagnosticsBlock(self):
        #контроль ввода кодов МКБ в рамках одного блока одним врачом
        checkGlobalPreferenceList = {u'не выполнять':0, u'мягкий':1, u'жёсткий':2}
        value = self._globalPreferences.get(u'diagnosticsBlockControl', None)
        if value:
            return checkGlobalPreferenceList.get(unicode(value).lower(), None)
        return None

    def controlOnkoTNMS(self):
        #контроль ввода кодов ТНМ-Ст для онко диагнозов
        checkGlobalPreferenceList = {u'не выполнять':0, u'мягкий':1, u'жёсткий':2}
        value = self._globalPreferences.get(u'23:onkoTNMSControl', None)
        if value:
            return checkGlobalPreferenceList.get(unicode(value).lower(), None)
        return None

    def isLockUpdateEventHospitalBeds(self):
        # Блокировать возможность перевода и выписки в Стационарном мониторе при открытии формы ввода, по умолчанию - нет
        return self.checkGlobalPreference('lockUpdEventHB', u'да')


    def isCheckDoubleVisitsEnteredByService(self):
        #Контроль регистрации визита по услуге
        checkGlobalPreferenceList = {u'не выполнять':0, u'мягкий':1, u'жёсткий':2}
        value = self._globalPreferences.get(u'28', None)
        if value:
            return checkGlobalPreferenceList.get(unicode(value).lower(), None)
        return None


    def isCheckDoubleVisitsEnteredBySpeciality(self):
        #Контроль регистрации визита по специальности
        checkGlobalPreferenceList = {u'не выполнять':0, u'мягкий':1, u'жёсткий':2}
        value = self._globalPreferences.get(u'29', None)
        if value:
            return checkGlobalPreferenceList.get(unicode(value).lower(), None)
        return None


    def isControlVoucherNumber(self):
        #Контроль уникальности путевки
        checkGlobalPreferenceList = {u'нет':0, u'мягкий':1, u'жёсткий':2}
        value = self._globalPreferences.get(u'controlVoucherNumber', None)
        if value:
            return checkGlobalPreferenceList.get(unicode(value).lower(), None)
        return None


    def isControlActionReceivedBegDate(self):
        #Контроль даты начала события и даты начала действия Поступление
        checkGlobalPreferenceList = {u'нет':0, u'мягкий':1, u'жёсткий':2}
        value = self._globalPreferences.get(u'actionReceivedBegDateControl', None)
        if value:
            return checkGlobalPreferenceList.get(unicode(value).lower(), None)
        return None


    def isControlActionBegDate(self):
        #Контроль даты начала действия
        checkGlobalPreferenceList = {u'нет':0, u'мягкий':1, u'жёсткий':2}
        value = self._globalPreferences.get(u'actionBegDateControl', None)
        if value:
            return checkGlobalPreferenceList.get(unicode(value).lower(), None)
        return None


    def isControlEventMesPeriodicity(self):
        #Контроль периодичности МЭС
        checkGlobalPreferenceList = {u'мягкий':0, u'жёсткий':1}
        value = self._globalPreferences.get(u'eventMesPeriodicityControl', None)
        if value:
            return checkGlobalPreferenceList.get(unicode(value).lower(), None)
        return None


    def medicalDayBegTime(self):
        # Время начала медицинских суток
        value = self._globalPreferences.get(u'medicalDayBegTime', None)
        if value:
            return forceTime(QTime.fromString(value, 'hh:mm'))
        return QTime()


    def numberDecimalPlacesQnt(self):
        #Количество знаков после запятой в количестве для ЛС
        value = self._globalPreferences.get(u'numberDecimalPlacesQnt', None)
        if value:
            return forceInt(value)
        return 0


    def minQntConsumableUnitsStock(self):
        #Минимальное количество ЛСиИМН в расходных единицах
        value = self._globalPreferences.get(u'minQntConsumableUnitsStock', None)
        if value:
            return forceDouble(value)
        return 0


    def createStockResidualQuantityAuto(self):
        #Создание документа в автоматическом режиме "Списание остаточных количеств ЛСиИМН"
        value = self._globalPreferences.get(u'createStockResidualQuantityAuto', '')
        if value:
            return forceStringEx(value)
        return ''


    def isDurationTakingIntoMedicalDays(self):
        # Использовать "Расчет длительности с учётом медицинских суток", по умолчанию - нет
        return self.checkGlobalPreference('takingIntoMedicalDays', u'да')


    def isPortraitOrientationThermalSheet(self):
        # Книжная ориентация температурного листа, по умолчанию - да
        return self.checkGlobalPreference('portraitOrientationThermalSheet', u'да')


    def controlMKBExForTraumaType(self):
        #Контроль заполнения столбца "Доп.МКБ" для учета травм
        checkGlobalPreferenceList = {u'мягкий':0, u'жёсткий':1}
        value = self._globalPreferences.get(u'30', None)
        if value:
            return checkGlobalPreferenceList.get(unicode(value).lower(), None)
        return None


    def controlTraumaType(self):
        #Контроль ввода травмы
        checkGlobalPreferenceList = {u'мягкий':0, u'жёсткий':1}
        value = self._globalPreferences.get(u'31', None)
        if value:
            return checkGlobalPreferenceList.get(unicode(value).lower(), None)
        return None


    def isCitizenshipControl(self):
        #Контроль Гражданства пациента
        checkGlobalPreferenceList = {u'не выполнять':0, u'мягкий':1, u'жёсткий':2}
        value = self._globalPreferences.get(u'Citizenship', None)
        if value:
            return checkGlobalPreferenceList.get(unicode(value).lower(), None)
        return None


    def isSMNomenclatureColFilter(self):
        #0010305: Складской учет. Требования. Выбор подразделения
        checkGlobalPreferenceList = {u'не выполнять':0, u'выполнять':1}
        value = self._globalPreferences.get(u'SMNomenclatureColFilter', None)
        if value:
            return checkGlobalPreferenceList.get(unicode(value).lower(), None)
        return None


    def controlNumberDisabilityFill(self):
        checkGlobalPreferenceList = {u'жёсткий':0, u'мягкий':1, u'не контролировать':2}
        value = self._globalPreferences.get(u'numberDisability', None)
        if value:
            return checkGlobalPreferenceList.get(unicode(value).lower(), None)
        return None


    def isGenerateNomenclatureReservation(self):
        #0010360: Складской учет. Настройка для резервирования ЛС
        checkGlobalPreferenceList = {u'всегда':0, u'иногда':1, u'никогда':2}
        value = self._globalPreferences.get(u'generateNomenclatureReservation', None)
        if value:
            return checkGlobalPreferenceList.get(unicode(value).lower(), None)
        return None


    ######
    def setCounterController(self, counterController):
        if counterController and self._counterController:
            self._counterController.resetAllCounterValueIdReservation()
        self._counterController = counterController


    def getDocumentNumber(self, clientId, counteId, date = None):
        if self._counterController:
            return self._counterController.getDocumentNumber(clientId, counteId, date)


    def delAllCounterValueIdReservation(self):
        if self._counterController:
            self._counterController.delAllCounterValueIdReservation()


    def resetAllCounterValueIdReservation(self):
        if self._counterController:
            self._counterController.resetAllCounterValueIdReservation()


    def resetCounterValueIdReservation(self, reservationId):
        if self._counterController:
            self._counterController.resetCounterValueCacheReservation(reservationId)


    def counterController(self):
        return self._counterController

    ######

    def setJTR(self, jtr):
        self.jobTicketReserveHolder.addLevel(jtr)

    def unsetJTR(self, jtr):
        self.jobTicketReserveHolder.delLevel(jtr)

#    def addJobTicketReservation(self, jobTicketId, chainLength=1):
    def addJobTicketReservation(self, jobTicketId):
        return self.jobTicketReserveHolder.addJobTicketReservation(jobTicketId)


    def getReservedJobTickets(self):
        return self.jobTicketReserveHolder.getReservedJobTickets()


#    def makeJobTicketIdQueue(self, jobTicketId):
#        if self.currentJTR:
#            self.currentJTR.makeJobTicketIdQueue(jobTicketId)


#    def delAllJobTicketReservationsWithExcluding(self, excludingJTIdList):
#        if self.currentJTR:
#            self.currentJTR.delAllJobTicketReservationsWithExcluding(excludingJTIdList)

    def setupDocFreeQueue(self, appointmentType, orgStructureId, specialityId, personId, begDate):
        if self.userHasRight(urAccessGraph):
            dockFreeQueue = self.mainWindow.dockFreeQueue
            if not dockFreeQueue.isVisible():
                dockFreeQueue.show()
            dockFreeQueue.raise_()
            dockFreeQueue.setFilter(appointmentType, orgStructureId, specialityId, personId, begDate)


    def setupResourcesDock(self, orgStructureId, specialityId, personId, begDate, appointmentType = None):
        if self.userHasRight(urAccessEditTimeLine):
            dockResources = self.mainWindow.dockResources
            if not dockResources.isVisible():
                dockResources.show()
            dockResources.raise_()
            dockResources.setFilter(orgStructureId, specialityId, personId, begDate, appointmentType)


    def session(self, *args):
        if len(args) == 1:
            return self._session.get(args[0], None)
        elif len(args) == 2:
            self._session[args[0]] = args[1]



# #############################################################

class CS11MainWindow(QtGui.QMainWindow, Ui_MainWindow, CConstructHelperMixin):
    __pyqtSignals__ = (
        'dockWidgetCreated(QWidget*)',
    )

    def __init__(self, bgParams=None, parent = None):
        QtGui.QMainWindow.__init__(self, parent)
        QtGui.qApp.mainWindow = self
        QtGui.qApp.visibleMyDoctorArea = False
        QtGui.qApp.visibleNotifications = False
        self.initDockResources()
        self.initDockFreeQueue()
        self.initDockDiagnosis()
        if QtGui.qApp.defaultKLADR()[:2] == u'23':
            self.initDockSMP()
        self.addObject('actMyArea', QtGui.QAction(u'Мой участок', self, checkable=True))
        self.addObject('actNotifications', QtGui.QAction(u'Уведомления', self, checkable=True))
        self.setupUi(self)
        self.setCentralWidget(self.centralWidget)
        self.setCorner(Qt.TopLeftCorner,    Qt.LeftDockWidgetArea)
        self.setCorner(Qt.BottomLeftCorner, Qt.LeftDockWidgetArea)
        self.setCorner(Qt.TopRightCorner, Qt.RightDockWidgetArea)
        self.setCorner(Qt.BottomRightCorner, Qt.RightDockWidgetArea)
        for dock in (self.dockResources, self.dockFreeQueue, self.dockDiagnosis):
            self.menuPreferences.addAction(dock.toggleViewAction())
        if QtGui.qApp.defaultKLADR()[:2] == u'23':
            self.menuPreferences.addAction(self.dockSMP.toggleViewAction())
        if bgParams:
            self.centralWidget.setBackground(bgParams)
        self.menuPreferences.addAction(self.actMyArea)
        self.menuPreferences.addAction(self.actNotifications)
        self.prepareStatusBar()
        self.registry = None
        self.homeCallRequests = None
        self.suspendedAppointment = None
        self.prophylaxisPlanning = None
        self.dispExchange = None
        self.distantMonitoring = None
        self.updateActionsState()
        self.setUserName('')
        self.mruEventList = []
        self.mruEventListChanged = False
        self.loadPreferences()
        # self.centralWidget.subWindowActivated.connect(self.centralWidgetSubWindowActivated)
        self.actMyArea.setChecked(QtGui.qApp.visibleMyDoctorArea)
        self.actNotifications.setChecked(QtGui.qApp.visibleNotifications)
        # self.actSetAdmittingStart.setVisible(False)
        # self.actSetAdmittingEnd.setVisible(False)
        # self.actSetDutyStart.setVisible(False)
        # self.actSetDutyEnd.setVisible(False)
        self.menu_036.menuAction().setVisible(False)
        self.menu_36PL.menuAction().setVisible(False)
        self.actStationaryYearReport.setVisible(False)
        self.actProfileYearReport.setVisible(False)
        # self.actProphylaxisPlanning.setVisible(False)
        # self.actSurgeryJournal.setVisible(False)
        # self.actHealthResort.setVisible(False)
        self.actTreatmentScheme.setVisible(False)
        self.actTreatmentSchedule.setVisible(False)
        self.actTreatmentControl.setVisible(False)


    def fillByTemplate(self, templateId):
        QtGui.qApp.call(self, applyTemplate, (self, templateId, {}))


    def on_actMyArea_toggled(self, checked):
        QtGui.qApp.visibleMyDoctorArea = checked
        if self.registry:
            self.registry.tabMain.setTabVisible(self.registry.tabMyDoctorArea, checked)


    def on_actNotifications_toggled(self, checked):
        QtGui.qApp.visibleNotifications = checked
        if self.registry:
            self.registry.tabMain.setTabVisible(self.registry.tabNotifications, checked)


    @pyqtSignature('QMdiSubWindow*')
    def centralWidgetSubWindowActivated(self, subwindow):
        if subwindow:
            subwindow.widget().update()


    def initDockResources(self):
        self.dockResources = CResourcesDockWidget(self)
        self.dockResources.setObjectName('dockResources')
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dockResources)
        self.emit(SIGNAL('dockWidgetCreated(QDockWidget*)'), self.dockResources)


    def initDockFreeQueue(self):
        self.dockFreeQueue = CFreeQueueDockWidget(self)
        self.dockFreeQueue.setObjectName('dockFreeQueue')
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dockFreeQueue)
        self.emit(SIGNAL('dockWidgetCreated(QDockWidget*)'), self.dockFreeQueue)


    def initDockDiagnosis(self):
        self.dockDiagnosis = CDiagnosisDockWidget(self)
        self.dockDiagnosis.setObjectName('dockDiagnosis')
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dockDiagnosis)
        self.emit(SIGNAL('dockWidgetCreated(QDockWidget*)'), self.dockDiagnosis)


    def initDockSMP(self):
        self.dockSMP = CSMPDockWidget(self)
        self.dockSMP.setObjectName('dockSMP')
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dockSMP)
        self.emit(SIGNAL('dockWidgetCreated(QDockWidget*)'), self.dockSMP)


    def prepareStatusBar(self):
        self.progressBar = QtGui.QProgressBar()
        self.progressBar.setMaximumWidth(200)
        self.progressBar.setMaximumHeight(self.statusBar.height()/2)
        self.progressBarVisible = False


    def closeEvent(self, event):
        self.dockResources.saveDialogPreferences()
        self.dockFreeQueue.saveDialogPreferences()
        self.dockDiagnosis.saveDialogPreferences()
        if QtGui.qApp.defaultKLADR()[:2] == u'23' and hasattr(self, 'dockSMP'):
            self.dockSMP.saveDialogPreferences()
        self.savePreferences()
        self.centralWidget.closeAllSubWindows()
        QtGui.QMainWindow.closeEvent(self, event)


    def loadPreferences(self):
        preferences = getPref(QtGui.qApp.preferences.windowPrefs, self.objectName(), {})
        geometry = getPref(preferences, 'geometry', None)
        if type(geometry) == QVariant and geometry.type() == QVariant.ByteArray and not geometry.isNull():
            self.restoreGeometry(geometry.toByteArray())
        state = getPref(preferences, 'state', None)
        if type(state) == QVariant and state.type() == QVariant.ByteArray and not geometry.isNull():
            self.restoreState(state.toByteArray())
        QtGui.qApp.visibleMyDoctorArea = forceBool(getPref(preferences, 'visibleMyDoctorArea', False))
        QtGui.qApp.visibleNotifications = forceBool(getPref(preferences, 'visibleNotifications', False))


    def savePreferences(self):
        preferences = {}
        setPref(preferences, 'geometry', QVariant(self.saveGeometry()))
        setPref(preferences, 'state', QVariant(self.saveState()))
        setPref(preferences, 'visibleMyDoctorArea', QVariant(QtGui.qApp.visibleMyDoctorArea))
        setPref(preferences, 'visibleNotifications', QVariant(QtGui.qApp.visibleNotifications))
        setPref(QtGui.qApp.preferences.windowPrefs, self.objectName(), preferences)


    def updateActionsState(self):
#        notImplemented = False
        app = QtGui.qApp
        loggedIn = bool(app.db) and (app.demoMode or app.userId is not None)
        orgIdSet = loggedIn and bool(app.currentOrgId())
        isMedical = loggedIn and bool(app.currentOrgId()) and forceInt(app.db.translate('Organisation', 'id', app.currentOrgId(), 'isMedical'))
#        orgStructureIdSet = loggedIn and bool(app.currentOrgStructureId())
        isAdmin      = loggedIn and app.userHasRight(urAdmin)
        isAccountant = orgIdSet and (app.userHasRight(urAccessAccountInfo) or isAdmin)
        isTimekeeper = orgIdSet and app.userHasAnyRight([urAccessReadTimeLine, urAccessEditTimeLine, isAdmin])
        isBlankskeeper = orgIdSet and (app.userHasRight(urAccessBlanks) or isAdmin)
        isRefAdmin   = loggedIn and (app.userHasRight(urAccessRefBooks) or isAdmin)
        isEmergencyRefAdmin = loggedIn and (isRefAdmin or app.userHasRight(urAccessRefEmergency))
        isFeedRefAdmin = loggedIn and (isRefAdmin or app.userHasRight(urAccessRefFeed))
        isMedicalRefAdmin = loggedIn and (isRefAdmin or app.userHasRight(urAccessRefMedical))
        isClassificatorRefAdmin = loggedIn and (isRefAdmin or app.userHasRight(urAccessRefClassificators))
        exchangeEnabled = orgIdSet and (app.userHasRight(urAccessExchange) or isAdmin)

        fullAnalysisEnabled = orgIdSet and (app.userHasRight(urAccessAnalysis) or isAdmin)
        personalAnalysisEnabled = orgIdSet and (app.userHasRight(urAccessAnalysisPersonal)
                                                            or app.userHasRight(urAccessAnalysis) or isAdmin)
        orgStructAnalysisEnabled = orgIdSet and (app.userHasRight(urAccessAnalysisOrgStruct)
                                                            or app.userHasRight(urAccessAnalysis) or isAdmin)
        analysisTimelineEnabled = orgIdSet and (app.userHasRight(urAccessAnalysisTimeline)
                                                            or app.userHasRight(urAccessAnalysis) or isAdmin)
        analysisTimelinePreRecordEnabled = orgIdSet and (app.userHasRight(urAccessAnalysisTimelinePreRecord)
                                                            or app.userHasRight(urAccessAnalysis) or isAdmin)
        analysisAnaliticReportsEnabled = orgIdSet and (app.userHasRight(urAccessAnalysisAnaliticReports)
                                                            or app.userHasRight(urAccessAnalysis) or isAdmin)

        # Меню Сессия
        self.actLogin.setEnabled(not loggedIn)
        self.actLogout.setEnabled(loggedIn)
        self.actChangeCurrentPerson.setEnabled(loggedIn and len(getLoginPersonList(QtGui.qApp.loginId)) > 1)
        self.actSetAdmittingStart.setEnabled(loggedIn)
        self.actSetDutyStart.setEnabled(loggedIn)
        self.actSetAdmittingEnd.setEnabled(False)
        self.actSetDutyEnd.setEnabled(False)
        self.actQuit.setEnabled(True)

        # Меню Работа
        self.actRegistry.setEnabled(orgIdSet and (app.userHasRight(urAccessRegistry) or isAdmin))
        self.actSuspenedAppointment.setEnabled(app.userHasRight(urAccessSuspenedAppointment))
        self.actSurgeryJournal.setEnabled(app.userHasRight(urAccessSurgeryJournal))
        self.actHomeCallRequests.setEnabled(loggedIn)
        self.actProphylaxisPlanning.setEnabled(loggedIn)
        self.actTimeline.setEnabled(isTimekeeper)
        self.actFormRegistration.setEnabled(isBlankskeeper)
        self.actHospitalBeds.setEnabled(orgIdSet and (app.userHasRight(urAccessHospitalBeds) or isAdmin))
        self.actHealthResort.setEnabled(orgIdSet and (app.userHasRight(urAccessHealthResort) or isAdmin))
        self.actHealthResort.setVisible(isMedical == 5)
        self.actTreatmentScheme.setEnabled(app.userHasRight(urAccessTreatmentScheme))
        self.actTreatmentSchedule.setEnabled(app.userHasRight(urAccessTreatmentSchedule))
        self.actTreatmentControl.setEnabled(app.userHasRight(urAccessTreatmentControl))
        self.actProphylaxisPlanning.setEnabled(orgIdSet)
        self.actSurveillance.setEnabled(orgIdSet and (app.userHasRight(urAccessSurveillance) or isAdmin))
        self.actJobsPlanning.setEnabled(orgIdSet and (app.userHasRight(urAccessJobsPlanning) or isAdmin))
        self.actJobsOperating.setEnabled(orgIdSet and (app.userHasRight(urAccessJobsOperating) or isAdmin))
        self.actQuoting.setEnabled(app.userHasRight(urAccessQuoting) or
                                   app.userHasRight(urAccessQuotingWatch) or
                                   isAdmin)
        self.actTissueJournal.setEnabled(app.userHasRight(urAccessTissueJournal))
        self.actStockControl.setEnabled(orgIdSet and (app.userHasRight(urAccessStockControl) or isAdmin))
        self.actDispExchange.setEnabled(app.userHasRight(urAccessDispService))
        self.actDemogrCertificates.setEnabled(app.userHasRight(urDemography) or isAdmin)
        self.actHomeCallRequests.setEnabled(app.userHasRight(urHomeCallJournal) or isAdmin)
        self.actSvodService.setEnabled(app.userHasRight(urMedStatic) or isAdmin)
        self.actExportAttachDoctorSectionInfo.setEnabled(app.userHasRight(urDoctorSectionExport) or isAdmin)
        self.actInformerMessages.setEnabled(app.userHasRight(urSetupInformer) or isAdmin)
        # Меню Расчет
        self.mnuAccounting.setEnabled(orgIdSet and (   isAccountant
                                                    or app.userHasAnyRight((urAccessAccounting,
                                                                            urAccessAccountingBudget,
                                                                            urAccessAccountingCMI,
                                                                            urAccessAccountingVMI,
                                                                            urAccessAccountingCash,
                                                                            urAccessAccountingTargeted,
                                                                            urAccessContract,
                                                                            urAccessCashBook,
                                                                            urAccessCashBookOnlyJournal
                                                                           )
                                                                          )
                                                   )
                                     )
        self.actAccounting.setEnabled(orgIdSet and (   isAccountant
                                                    or app.userHasAnyRight((urAccessAccounting,
                                                                            urAccessAccountingBudget,
                                                                            urAccessAccountingCMI,
                                                                            urAccessAccountingVMI,
                                                                            urAccessAccountingCash,
                                                                            urAccessAccountingTargeted
                                                                           )
                                                                          )
                                                   )
                                     )
        self.actContract.setEnabled(orgIdSet and (isAccountant or app.userHasRight(urAccessContract)))
        self.actCashBook.setEnabled(orgIdSet and (isAccountant or app.userHasAnyRight((urAccessCashBook, urAccessCashBookOnlyJournal))))

        # Меню Обмен
        self.mnuExchange.setEnabled(exchangeEnabled)

        # обособленные отчеты для КК
        self.mnuReportImunoprophylaxis.removeAction(self.actReportImunoprophylaxisForm6)
        if bool(app.db):
            lpuCode = forceString(app.db.translate('Organisation', 'id', app.currentOrgId(), 'infisCode'))
            if lpuCode in ['07096', '07034']:
                if not hasattr(self, 'mnuPaidServices'):
                    menu = QtGui.QMenu(self.mnuReports)
                    self.__setattr__('mnuPaidServices', menu)
                    menu.setObjectName('mnuPaidServices')
                    self.mnuPaidServices.setTitle(u"Платные услуги")
                    self.mnuReports.addMenu(menu)
                    self.actPaidServices = QtGui.QAction(self)
                    self.actPaidServices.setObjectName("actPaidServices")
                    self.actPaidServices.setText(u"Анализ платных услуг")
                    self.actVolumeServices = QtGui.QAction(self)
                    self.actVolumeServices.setObjectName("actPaidServices")
                    self.actVolumeServices.setText(u"Объем выполненных услуг")
                    self.mnuPaidServices.addAction(self.actPaidServices)
                    self.mnuPaidServices.addAction(self.actVolumeServices)
                    self.actPaidServices.triggered.connect(self.on_actPaidServices_triggered)
                    self.actVolumeServices.triggered.connect(self.on_actVolumeServices_triggered)
            if lpuCode != '07541':
                self.mnuReportEconomicAnalisys.removeAction(self.actECO)

        # Меню Анализ
        self.mnuStatReports.setEnabled(app.userHasRight(urAccessStatReports) or orgStructAnalysisEnabled)
        self.mnuAdministrator.menuAction().setVisible(app.userHasRight(urAccessAdministrator))
        self.mnuReportF131.setEnabled(orgStructAnalysisEnabled)
        self.actSpendingToClients.setEnabled(personalAnalysisEnabled)
        mnuReportsChiefEnabled = loggedIn and app.userHasRight(urAccessReportsChief)
        self.mnuReportsChief.setEnabled(mnuReportsChiefEnabled)
        if mnuReportsChiefEnabled:
            self.loadReportsChiefActions()
        if loggedIn:
            self.setSelectedReportsVisible(False)
        self.actGenRep.setEnabled(app.userHasRight(urAccessGenRep) or orgStructAnalysisEnabled)
        self.mnuReportsByVisits.setEnabled(app.userHasRight(urAccessReportsByVisits) or personalAnalysisEnabled)
        if loggedIn:
            self.mnuUserTemplate.setEnabled(True)
            self.resultUserTemplate = CPrintAction(u'None', None, None, self)
            self.resultUserTemplate._menu = self.mnuUserTemplate
            self.resultUserTemplate.setContext("reportsList", True)
            QObject.connect(self.resultUserTemplate, SIGNAL('printByTemplate(int)'), self.fillByTemplate)
        else:
            self.mnuUserTemplate.setEnabled(False)
        self.mnuReportsBuMorbidity.setEnabled(app.userHasRight(urAccessReportsBuMorbidity) or personalAnalysisEnabled)
        self.mnuDispObservation.setEnabled(app.userHasRight(urAccessDispObservation) or personalAnalysisEnabled)
        self.mnuTempInvalid.setEnabled(app.userHasRight(urAccessTempInvalid) or personalAnalysisEnabled)
        self.mnuDeath.setEnabled(app.userHasRight(urAccessDeath) or personalAnalysisEnabled)
        self.mnuContingent.setEnabled(app.userHasRight(urAccessContingent) or personalAnalysisEnabled)
        self.mnuStationary.setEnabled(app.userHasRight(urAccessStationary) or personalAnalysisEnabled)
        self.mnuTimelineReports.setEnabled(analysisTimelineEnabled)
        self.mnuPreRecord.setEnabled(analysisTimelinePreRecordEnabled)
        self.mnuAnaliticReports.setEnabled(analysisAnaliticReportsEnabled)
        self.mnuDD2007.setEnabled(fullAnalysisEnabled)
        self.mnuAnalysisService.setEnabled(app.userHasRight(urAccessAnalysisService) or fullAnalysisEnabled)
        self.actWorkload.setEnabled(app.userHasRight(urAccessWorkload) or fullAnalysisEnabled)
        self.mnuReportEconomicAnalisys.setEnabled(loggedIn and (app.userHasRight(urAccessEconomicAnalysis) or isAdmin))
        self.mnuAccountingAnalysis.setEnabled(app.userHasRight(urAccessAccountingAnalysis) or fullAnalysisEnabled)
        self.mnuEmergencyCall.setEnabled(app.userHasRight(urAccessEmergencyCall) or fullAnalysisEnabled)
        self.mnuReportImunoprophylaxis.setEnabled(app.userHasRight(urAccessReportImunoprophylaxis) or fullAnalysisEnabled)
        self.mnuReportLaboratory.setEnabled(app.userHasRight(urAccessReportLaboratory) or fullAnalysisEnabled)
        self.mnuReportTrauma.setEnabled(app.userHasRight(urAccessReportTrauma) or fullAnalysisEnabled)
        self.mnuReportSanstorium.setEnabled(app.userHasRight(urAccessReportSanstorium) or fullAnalysisEnabled)
        if bool(app.db):
            lpuCode = forceString(app.db.translate('Organisation', 'id', app.currentOrgId(), 'infisCode'))
            if lpuCode != '45014':
                self.mnuAccountingAnalysis.removeAction(self.actReportPaidServices)
            self.actReportAFT_002.setVisible(lpuCode == '48001')
            self.actReportAFT_Forecast12month.setVisible(lpuCode == '48001')
        self.actRepServiceAttach.setVisible(QtGui.qApp.defaultKLADR()[:2] != u'23')
        self.mnuHealthCenter.setEnabled(True)

        # Меню Справочники
        # Подменю Адреса
#        self.menu.setEnabled(notImplemented)
        self.menu.setEnabled(isRefAdmin or
            app.userHasAnyRight([urAccessRefAddress,
                                 urAccessRefAddressKLADR,
                                 urAccessRefAddressAreas
                                ]))
        self.actMilitaryUnits.setEnabled(isRefAdmin or app.userHasAnyRight([urAccessRefAddressKLADR]))
#        self.actKLADR.setEnabled(isRefAdmin or app.userHasAnyRight([urAccessRefAddress, urAccessRefAddressKLADR]))
#        self.actAreas.setEnabled(isRefAdmin or app.userHasAnyRight([urAccessRefAddress, urAccessRefAddressAreas]))
#        self.actKLADR.setEnabled(notImplemented)
#        self.actAreas.setEnabled(notImplemented)

        # Подменю Персонал
        self.menu_2.setEnabled(isRefAdmin or
            app.userHasAnyRight([urAccessRefPerson,
                                 urAccessRefPersonOrgStructure,
                                 urAccessRefPersonRBSpeciality,
                                 urAccessRefPersonRBPost,
                                 urAccessRefPersonRBActivity,
                                 urAccessRefPersonRBAppointmentPurpose,
                                 urAccessRefPersonPersonal
                                ]))
        self.actOrgStructure.setEnabled(isRefAdmin or
            app.userHasAnyRight([urAccessRefPerson, urAccessRefPersonOrgStructure]))
        self.actRBSpeciality.setEnabled(isRefAdmin or
            app.userHasAnyRight([urAccessRefPerson, urAccessRefPersonRBSpeciality]))
        self.actRBPost.setEnabled(isRefAdmin or
            app.userHasAnyRight([urAccessRefPerson, urAccessRefPersonRBPost]))
        self.actRBActivity.setEnabled(isRefAdmin or
            app.userHasAnyRight([urAccessRefPerson, urAccessRefPersonRBActivity]))
        self.actRBAppointmentPurpose.setEnabled(isRefAdmin or
            app.userHasAnyRight([urAccessRefPerson, urAccessRefPersonRBAppointmentPurpose]))
        self.actPersonal.setEnabled(isRefAdmin or
            app.userHasAnyRight([urAccessRefPerson, urAccessRefPersonPersonal]))
        self.actRBLogin.setEnabled(QtGui.qApp.userHasRight(urEditLoginPasswordProfileUser))

        # Подменю Скорая помощь
        self.menu_9.setEnabled(isEmergencyRefAdmin or
            app.userHasAnyRight([urAccessRefEmergency]))

        # Подменю Питание
        self.menu_16.setEnabled(isFeedRefAdmin or
            app.userHasAnyRight([urAccessRefFeed]))

        # Подменю Медицинские
        self.menu_3.setEnabled(isMedicalRefAdmin or
            app.userHasAnyRight([urAccessRefMedical,
                                 urAccessRefMedMKB,
                                 urAccessRefMedMKBSubClass,
                                 urAccessRefMedDiseaseCharacter,
                                 urAccessRefMedDiseaseStage,
                                 urAccessRefMedDiseasePhase,
                                 urAccessRefMedDiagnosisType,
                                 urAccessRefMedTraumaType,
                                 urAccessRefMedHealthGroup,
                                 urAccessRefMedDispanser,
                                 urAccessRefMedResult,
                                 urAccessRefMedTempInvalidAnnulmentReason,
                                 urAccessRefMedTempInvalidDocument,
                                 urAccessRefMedTempInvalidBreak,
                                 urAccessRefMedTempInvalidReason,
                                 urAccessRefMedTempInvalidRegime,
                                 urAccessRefMedTempInvalidResult,
                                 urAccessRefMedComplain,
                                 urAccessRefMedThesaurus,
                                 urAccessRefMedBloodType
                                ]))
        self.actMKB.setEnabled(isMedicalRefAdmin or
            app.userHasAnyRight([urAccessRefMedical, urAccessRefMedMKB]))
        self.actMKBSubclass.setEnabled(isMedicalRefAdmin or
            app.userHasAnyRight([urAccessRefMedical, urAccessRefMedMKBSubClass]))
        self.actMKBMorphology.setEnabled(isMedicalRefAdmin or
            app.userHasAnyRight([urAccessRefMedical]))
        self.actRBDiseaseCharacter.setEnabled(isMedicalRefAdmin or
            app.userHasAnyRight([urAccessRefMedical, urAccessRefMedDiseaseCharacter]))
        self.actRBDiseaseStage.setEnabled(isMedicalRefAdmin or
            app.userHasAnyRight([urAccessRefMedical, urAccessRefMedDiseaseStage]))
        self.actRBDiseasePhase.setEnabled(isMedicalRefAdmin or
            app.userHasAnyRight([urAccessRefMedical, urAccessRefMedDiseasePhase]))
        self.actRBDiagnosisType.setEnabled(isMedicalRefAdmin or
            app.userHasAnyRight([urAccessRefMedical, urAccessRefMedDiagnosisType]))
        self.actRBTraumaType.setEnabled(isMedicalRefAdmin or
            app.userHasAnyRight([urAccessRefMedical, urAccessRefMedTraumaType]))
        self.actRBHealthGroup.setEnabled(isMedicalRefAdmin or
            app.userHasAnyRight([urAccessRefMedical, urAccessRefMedHealthGroup]))
        self.actRBDispanser.setEnabled(isMedicalRefAdmin or app.userHasAnyRight([urAccessRefMedical, urAccessRefMedDispanser]))
        self.actRBResult.setEnabled(isMedicalRefAdmin or app.userHasAnyRight([urAccessRefMedical, urAccessRefMedResult]))
        self.actRBTempInvalidAnnulmentReason.setEnabled(isMedicalRefAdmin or app.userHasAnyRight([urAccessRefMedical, urAccessRefMedTempInvalidAnnulmentReason]))
        self.actRBTempInvalidAnnulmentReason.setEnabled(isMedicalRefAdmin or
            app.userHasAnyRight([urAccessRefMedical, urAccessRefMedTempInvalidAnnulmentReason]))
        self.actRBResult.setEnabled(isMedicalRefAdmin or
            app.userHasAnyRight([urAccessRefMedical, urAccessRefMedResult]))
        self.actRBTempInvalidReason.setEnabled(isMedicalRefAdmin or
            app.userHasAnyRight([urAccessRefMedical, urAccessRefMedTempInvalidReason]))
        self.actRBTempInvalidDocument.setEnabled(isMedicalRefAdmin or
            app.userHasAnyRight([urAccessRefMedical, urAccessRefMedTempInvalidDocument]))
        self.actRBTempInvalidBreak.setEnabled(isMedicalRefAdmin or
            app.userHasAnyRight([urAccessRefMedical, urAccessRefMedTempInvalidBreak]))
        self.actRBTempInvalidRegime.setEnabled(isMedicalRefAdmin or
            app.userHasAnyRight([urAccessRefMedical, urAccessRefMedTempInvalidRegime]))
        self.actRBTempInvalidResult.setEnabled(isMedicalRefAdmin or
            app.userHasAnyRight([urAccessRefMedical, urAccessRefMedTempInvalidResult]))
        self.actRBTempInvalidDuplicateReason.setEnabled(isMedicalRefAdmin or
            app.userHasAnyRight([urAccessRefMedical, urAccessRefMedTempInvalidResult]))

        self.actRBComplain.setEnabled(isMedicalRefAdmin or
            app.userHasAnyRight([urAccessRefMedical, urAccessRefMedComplain]))
        self.actRBThesaurus.setEnabled(isMedicalRefAdmin or
            app.userHasAnyRight([urAccessRefMedical, urAccessRefMedThesaurus]))
        self.actRBBloodType.setEnabled(isMedicalRefAdmin or
            app.userHasAnyRight([urAccessRefMedical, urAccessRefMedBloodType]))
        self.actRBImageMap.setEnabled(isMedicalRefAdmin or app.userHasAnyRight([urAccessRefMedical,]))

        # Подменю Классификаторы
        self.menu_4.setEnabled(isClassificatorRefAdmin
            or app.userHasAnyRight([urAccessRefClOKPF,
                                    urAccessRefClOKFS,
                                    urAccessRefClHurtType,
                                    urAccessRefClHurtFactorType,
                                    urAccessRefClUnit,
                                   ]))
        self.actRBOKPF.setEnabled(isClassificatorRefAdmin or app.userHasRight(urAccessRefClOKPF))
        self.actRBOKFS.setEnabled(isClassificatorRefAdmin or app.userHasRight(urAccessRefClOKFS))
        self.actRBHurtType.setEnabled(isClassificatorRefAdmin or app.userHasRight(urAccessRefClHurtType))
        self.actRBHurtFactorType.setEnabled(isClassificatorRefAdmin or app.userHasRight(urAccessRefClHurtFactorType))
        self.actRBUnit.setEnabled(isClassificatorRefAdmin or app.userHasRight(urAccessRefClUnit))
        self.actRBResearchArea.setEnabled(isClassificatorRefAdmin)

        # Подменю Учет
        self.menu_6.setEnabled(isRefAdmin or
           app.userHasAnyRight([urAccessRefAccount,
                                urAccessRefAccountRBVisitType,
                                urAccessRefAccountEventType,
                                urAccessRefAccountRBEventTypePurpose,
                                urAccessRefAccountRBScene,
                                urAccessRefAccountRBAttachType,
                                urAccessRefAccountRBMedicalAidUnit,
                                urAccessRefAccountActionPropertyTemplate,
                                urAccessRefAccountActionType,
                                urAccessRefAccountActionTemplate,
                                urAccessRefAccountRBReasonOfAbsence,
                                urAccessRefAccountRBHospitalBedProfile,
                               ]))
        self.actRBVisitType.setEnabled(isRefAdmin or
            app.userHasAnyRight([urAccessRefAccount, urAccessRefAccountRBVisitType]))
        self.actRBTest.setEnabled(isRefAdmin or app.userHasAnyRight([urAccessRefAccount]))
        self.actRBTestGroup.setEnabled(isRefAdmin or app.userHasAnyRight([urAccessRefAccount]))
        self.actRBLaboratory.setEnabled(isRefAdmin or app.userHasAnyRight([urAccessRefAccount]))
        self.actRBSuiteReagent.setEnabled(isRefAdmin or app.userHasAnyRight([urAccessRefAccount]))
        self.actEventType.setEnabled(isRefAdmin or
            app.userHasAnyRight([urAccessRefAccount, urAccessRefAccountEventType]))
        self.actRBEventTypePurpose.setEnabled(isRefAdmin or
            app.userHasAnyRight([urAccessRefAccount, urAccessRefAccountRBEventTypePurpose]))
        self.actRBEventProfile.setEnabled(isRefAdmin or
            app.userHasAnyRight([urAccessRefAccount, urAccessRefAccountRBEventProfile]))
        self.actRBScene.setEnabled(isRefAdmin or
            app.userHasAnyRight([urAccessRefAccount, urAccessRefAccountRBScene]))
        self.actRBAttachType.setEnabled(isRefAdmin or
            app.userHasAnyRight([urAccessRefAccount, urAccessRefAccountRBAttachType]))
        self.actRBMedicalAidUnit.setEnabled(isRefAdmin or
            app.userHasAnyRight([urAccessRefAccount, urAccessRefAccountRBMedicalAidUnit]))
        self.actRBMedicalAidKind.setEnabled(isRefAdmin or app.userHasRight(urAccessRefAccount))
        self.actRBMedicalAidType.setEnabled(isRefAdmin or app.userHasRight(urAccessRefAccount))
        self.actRBMedicalAidProfile.setEnabled(isRefAdmin or app.userHasRight(urAccessRefAccount))
        self.actRBMesSpecification.setEnabled(isRefAdmin or app.userHasRight(urAccessRefAccount))

        self.actActionPropertyTemplate.setEnabled(isRefAdmin or
            app.userHasAnyRight([urAccessRefAccount, urAccessRefAccountActionPropertyTemplate]))
        self.actRBActionShedule.setEnabled(isRefAdmin or
            app.userHasAnyRight([urAccessRefAccount, urAccessRefAccountRBActionShedule]))
        self.actActionType.setEnabled(isRefAdmin or
            app.userHasAnyRight([urAccessRefAccount, urAccessRefAccountActionType]))
        self.actActionTemplate.setEnabled(isRefAdmin or
            app.userHasAnyRight([urAccessRefAccount, urAccessRefAccountActionTemplate]))
        self.actRBReasonOfAbsence.setEnabled(isRefAdmin or
            app.userHasAnyRight([urAccessRefAccount, urAccessRefAccountRBReasonOfAbsence]))
        self.actRBHospitalBedProfile.setEnabled(isRefAdmin or
            app.userHasAnyRight([urAccessRefAccount, urAccessRefAccountRBHospitalBedProfile]))
        self.actRBJobType.setEnabled(isRefAdmin or app.userHasAnyRight([urAccessRefAccount]))
        self.actRBJobPurpose.setEnabled(isRefAdmin or app.userHasAnyRight([urAccessRefAccountJobPurpose]))
        self.actBlankType.setEnabled(isRefAdmin or app.userHasAnyRight([urAccessRefAccountBlankType]))
        self.actRBAgreementType.setEnabled(isRefAdmin or app.userHasAnyRight([urAccessRefAgreementType]))
        self.actQuotaType.setEnabled(isRefAdmin or app.userHasAnyRight([urAccessRefAccountQuotaType]))

        # Подменю Организации
        self.menu_11.setEnabled(isRefAdmin or
            app.userHasAnyRight([urAccessRefOrganization, urAccessRefOrgRBNet, urAccessRefOrgBank, urAccessRefOrgOrganisation]))
        self.actRBNet.setEnabled(isRefAdmin or \
            app.userHasAnyRight([urAccessRefOrganization, urAccessRefOrgRBNet]))
        self.actBank.setEnabled(isRefAdmin or \
            app.userHasAnyRight([urAccessRefOrganization, urAccessRefOrgBank]))
        self.actOrganisation.setEnabled(isRefAdmin or \
            app.userHasAnyRight([urAccessRefOrganization, urAccessRefOrgOrganisation]))

        # Подменю Финансовые
        self.menu_5.setEnabled(isRefAdmin or
            app.userHasAnyRight([urAccessRefFinancial, urAccessRefFinRBFinance,
                                 urAccessRefFinRBService, urAccessRefFinRBTariffCategory,
                                 urAccessRefFinRBPayRefuseType, urAccessRefFinRBCashOperation]))
        self.actRBFinance.setEnabled(isRefAdmin or \
            app.userHasAnyRight([urAccessRefFinancial, urAccessRefFinRBFinance]))
        self.actRBServiceGroup.setEnabled(isRefAdmin or \
            app.userHasAnyRight([urAccessRefFinancial, urAccessRefFinRBService]))
        self.actRBService.setEnabled(isRefAdmin or \
            app.userHasAnyRight([urAccessRefFinancial, urAccessRefFinRBService]))
        self.actRBTariffCategory.setEnabled(isRefAdmin or \
            app.userHasAnyRight([urAccessRefFinancial, urAccessRefFinRBTariffCategory]))
        self.actRBPayRefuseType.setEnabled(isRefAdmin or \
            app.userHasAnyRight([urAccessRefFinancial, urAccessRefFinRBPayRefuseType]))
        self.actRBCashOperation.setEnabled(isRefAdmin or \
            app.userHasAnyRight([urAccessRefFinancial, urAccessRefFinRBCashOperation]))
        self.actPrikCoef.setVisible(QtGui.qApp.defaultKLADR()[:2] == u'23')
        self.actPrikCoef.setEnabled(app.userHasRight(canRightForCreateAccounts))

        # Подменю Социальный Статус
        self.menu_12.setEnabled(isRefAdmin or
            app.userHasAnyRight([urAccessRefSocialStatus, urAccessRefSocialStatusType, urAccessRefSocialStatusClass]))
        self.actRBSocStatusType.setEnabled(isRefAdmin or \
            app.userHasAnyRight([urAccessRefSocialStatus, urAccessRefSocialStatusType]))
        self.actRBSocStatusClass.setEnabled(isRefAdmin or
            app.userHasAnyRight([urAccessRefSocialStatus, urAccessRefSocialStatusClass]))

        # Подменю Персонификация
        self.menu_13.setEnabled(isRefAdmin or
            app.userHasAnyRight([urAccessRefPersonfication,
                                 urAccessRefPersnftnPolicyKind,
                                 urAccessRefPersnftnPolicyType,
                                 urAccessRefPersnftnDocumentTypeGroup,
                                 urAccessRefPersnftnDocumentType,
                                 urAccessRefPersnftnContactType
                                ]))
        self.actRBPolicyType.setEnabled(isRefAdmin or
            app.userHasAnyRight([urAccessRefPersonfication, urAccessRefPersnftnPolicyType]))
        self.actRBPolicyKind.setEnabled(isRefAdmin or
            app.userHasAnyRight([urAccessRefPersonfication, urAccessRefPersnftnPolicyKind]))
        self.actRBDocumentTypeGroup.setEnabled(isRefAdmin or
            app.userHasAnyRight([urAccessRefPersonfication, urAccessRefPersnftnDocumentTypeGroup]))
        self.actRBDocumentType.setEnabled(isRefAdmin or
            app.userHasAnyRight([urAccessRefPersonfication, urAccessRefPersnftnDocumentType]))
        self.actRBContactType.setEnabled(isRefAdmin or
            app.userHasAnyRight([urAccessRefPersonfication, urAccessRefPersnftnContactType]))
        self.actRBLocationCardType.setEnabled(isRefAdmin or
            app.userHasAnyRight([urAccessRefEditLocationCard]))
        self.actRBDocumentTypeForTracking.setEnabled(isRefAdmin or
            app.userHasAnyRight([urAccessRefEditCardType]))
        self.actRBResearchKind.setEnabled(isRefAdmin or
            app.userHasAnyRight([urAccessRefPersnftnResearchKind]))
        self.actRBContingentKind.setEnabled(isRefAdmin or
            app.userHasAnyRight([urAccessRefPersnftnContingentKind]))
        self.actRBFmsUnit.setEnabled(isRefAdmin or
            app.userHasAnyRight([urAccessRefPersonfication, urAccessRefPersnftnDocumentType]))

        # Подменю Номенклатура
        self.mnuNomenclature.setEnabled(isRefAdmin
                                        or app.userHasRight(urAccessNomenclature)
                                        or app.userHasRight(urAccessStockRecipe)
                                       )
        self.actRBNomenclatureClass.setEnabled(isRefAdmin or app.userHasRight(urAccessNomenclature))
        self.actRBNomenclatureKind.setEnabled(isRefAdmin or app.userHasRight(urAccessNomenclature))
        self.actRBNomenclatureType.setEnabled(isRefAdmin or app.userHasRight(urAccessNomenclature))
        self.actRBNomenclatureActiveSubstance.setEnabled(isRefAdmin or app.userHasRight(urAccessNomenclature))
        self.actRBLfForm.setEnabled(isRefAdmin or app.userHasRight(urAccessNomenclature))
        self.actRBIngredient.setEnabled(isRefAdmin or app.userHasRight(urAccessNomenclature))
        self.actRBNomenclature.setEnabled(isRefAdmin or app.userHasRight(urAccessNomenclature))
        self.actRBStockRecipe.setEnabled(isRefAdmin or app.userHasRight(urAccessStockRecipe))
        self.actRBStockMotionItemUtilizationReason.setEnabled(isRefAdmin or app.userHasRight(urAccessNomenclature))

        # Подменю Лаборатория
        self.mnuLaboratory.setEnabled(isRefAdmin or app.userHasRight(urAccessLaboratory))

        # Подменю Оборудование
        self.mnuEquipment.setEnabled(isRefAdmin or app.userHasRight(urAccessEquipment))

        # Подменю Иммунопрофилактика
        self.mnuImunoprophylaxis.setEnabled(isRefAdmin or app.userHasRight(urAccessImunoprophylaxis))

        # Подменю Летальность
        self.mnuLethality.setEnabled(isRefAdmin or app.userHasRight(urAccessLethality))

        # Меню Сервис
        self.actCreateAttachClientsForArea.setEnabled(isAdmin or app.userHasRight(urAccessAttachClientsForArea))
        self.actTestSendMail.setEnabled(loggedIn)
        self.actTestMKB.setEnabled(loggedIn)
        self.actAverageDurationAcuteDisease.setEnabled(loggedIn)
        self.actTestRLS.setEnabled(loggedIn)
        self.actTestMES.setEnabled(loggedIn)
        self.menu_27.menuAction().setVisible(app.userHasRight(urAdminServiceTMK) or app.userHasRight(urServiceTMKdirectionList))
        self.actTMKAdmin.setVisible(app.userHasRight(urAdminServiceTMK))
        self.actTMKListDirections.setVisible(app.userHasRight(urAdminServiceTMK) or app.userHasRight(urServiceTMKdirectionList))
        self.actAttach_SEMD_IEMK.setEnabled(loggedIn)
        self.actTestCSG.setEnabled(loggedIn)
        self.actSignOrgSert.setEnabled(loggedIn)
        self.actExportSanAviacInfo.setEnabled(loggedIn)
        self.action_WSAttach.setEnabled(app.userHasRight(urAccessClientAttachExport))
        self.mnuUnlockDialog.setEnabled(app.userHasRight(urAdmin) or app.userHasRight(urUnlockData))
        self.actPlanningOrgStructureHospitalBedProfile.setEnabled(app.userHasRight(urPlanningHospitalBedProfile))
        self.actPersonSubstitutionService.setEnabled(app.userHasRight(urAdmin) or app.userHasRight(urPersonSubstitution))
        # Подменю Логический контроль
        self.mnuCheck.setEnabled(isAdmin or app.userHasRight(urAccessLogicalControl))
        self.actControlDiagnosis.setEnabled(isAdmin or app.userHasRight(urAccessLogicalControlDiagnosis))
        self.actControlDoubles.setEnabled(isAdmin or app.userHasRight(urAccessLogicalControlDoubles))
        self.actControlMes.setEnabled(isAdmin or app.userHasRight(urAccessLogicalControlMES))
        self.actEventsOMSCheck.setEnabled(isAdmin or app.userHasRight(urAccesslogicCntlOMSAccounts))
        # Подменю оповещения
        self.mnuNotifications.setEnabled(isAdmin or app.userHasRight(urAccessNotifications))
        self.actNotificationLog.setEnabled(isAdmin or app.userHasRight(urAccessNotificationLog))
        self.actRBNotificationKind.setEnabled(isAdmin or app.userHasRight(urAccessNotificationKind))
        self.actNotificationRules.setEnabled(isAdmin or app.userHasRight(urAccessNotificationRule))
        # Неприкаянный экспорт, который непонятно даже как назвать
        self.actExportLocalLabResultsToUSISH.setEnabled(exchangeEnabled)
        self.actSignOrgSert.setEnabled(app.userHasRight(urCanSignOrgCert))

        servicesDN = forceString(QtGui.qApp.getGlobalPreference('23:servicesDN')) if loggedIn else None
        if servicesDN and servicesDN == u'да':
            self.actDistantMonitoring.setVisible(True)
        else:
            self.actDistantMonitoring.setVisible(False)

        servicesURL = forceString(QtGui.qApp.getGlobalPreference('23:servicesURL')) if loggedIn else None
        self.actIdentityPatientService.setVisible(bool(servicesURL))
        self.actAttachOnlineService.setVisible(bool(servicesURL))
        self.actAttachOnlineService.setEnabled(isAdmin or app.userHasRight(urAccessClientAttachFederalService))
        self.actStreetCorrect.setEnabled(app.userHasRight(urStreetCorrect))

        # Меню Настройки
        # self.actConnection.setEnabled(isAdmin or app.userHasRight(urAccessSetupDB))
        self.actAppPreferences.setEnabled(isAdmin or app.userHasRight(urAccessSetupDefault))

        self.actRBPrintTemplate.setEnabled(isAdmin or app.userHasRight(urAccessSetupTemplate))
        self.actRBAccountExportFormat.setEnabled(isAdmin or app.userHasRight(urAccessSetupAccountSystems))
        self.actRBAccountingSystem.setEnabled(isAdmin or app.userHasRight(urAccessSetupExport))

        self.actUserRight.setEnabled(isAdmin or app.userHasRight(urAccessSetupUserRights))
        self.actUserRightProfile.setEnabled(isAdmin or app.userHasRight(urAccessSetupProfilesUserRights))
        self.actCalendar.setEnabled(isAdmin or app.userHasRight(urAccessCalendar))
        self.actRBCounter.setEnabled(isAdmin or app.userHasRight(urAccessSetupCounter))
        self.actN3QmExtraDataDef.setEnabled(isAdmin)
        self.actN3SRSUser.setEnabled(isAdmin)

        for dock, right in ((self.dockResources, urAccessGraph),
                            (self.dockFreeQueue, urAccessGraph),
                            (self.dockDiagnosis, urAccessLUD)):
            action = dock.toggleViewAction()

            if loggedIn and app.userHasRight(right):
                action.setEnabled(True)
                dock.loadDialogPreferences()  # ради загрузки видимости и пр.
            else:
                dock.setVisible(False)
                action.setEnabled(False)
        if QtGui.qApp.defaultKLADR()[:2] == u'23' and hasattr(self, 'dockSMP'):
            if loggedIn:
                self.dockSMP.toggleViewAction().setEnabled(True)
                self.dockSMP.loadDialogPreferences()
            else:
                self.dockSMP.setVisible(False)
                self.dockSMP.toggleViewAction().setEnabled(False)

        self.actMyArea.setEnabled(loggedIn)

        # Меню помощь
        self.actAbout.setEnabled(True)
        self.actAboutQt.setEnabled(True)

        # Скрываем неиспользуемые пункты меню Обмен
        if QtGui.qApp.defaultKLADR()[:2] == u'23':
            self.actImportEisOmsClients.setVisible(False)
            self.actImportDD.setVisible(False)
            self.actImport131DBF.setVisible(False)
            self.actImport131XML.setVisible(False)
            self.actImport131Errors.setVisible(False)
            self.menu_132.menuAction().setVisible(False)
            self.menuImportProfiles.menuAction().setVisible(False)
            self.actImportLgot.setVisible(False)
            self.actImportQuotaFromVTMP.setVisible(False)
            self.actImpotrFromSail.setVisible(False)
            self.actImportFromSailXML.setVisible(False)
            self.actImportPrimaryDocFromXml.setVisible(False)
            self.actExport131.setVisible(False)
            self.actExportRD2.setVisible(False)
            self.actExportHL7v2_5.setVisible(False)
            self.actExportPrimaryDocInXml.setVisible(False)
            self.actExportXmlEmc.setVisible(False)
            self.menu_8.menuAction().setVisible(False)
            self.actExportActionResult.setVisible(False)
            self.actExportFeedDataCsv.setVisible(False)

            self.actImportEisOmsLpu.setVisible(False)
            self.actImportOrgsINFIS.setVisible(False)
            self.actImportEisOmsSmo.setVisible(False)
            self.actImportSPR.setVisible(True)
        else:
            self.actImportSPR.setVisible(False)

        self.actImportCSVClient.setVisible(False)
        if bool(app.db):
            orgId = app.getCurrentOrgId()
            if orgId:
                if forceString(app.db.translate('Organisation', 'id', orgId, 'OGRN')) == u"1022302832078":
                    self.actImportCSVClient.setVisible(True)



    def setAdmittingEnabled(self, admitting, isAdmitting=False, isDuty=False):
        self.actSetAdmittingStart.setEnabled(not admitting)
        self.actSetDutyStart.setEnabled(not admitting)
        self.actSetAdmittingEnd.setEnabled(admitting and isAdmitting)
        self.actSetDutyEnd.setEnabled(admitting and isDuty)


    def getProgressBar(self):
        if not self.progressBarVisible:
            self.progressBarVisible = True
            self.statusBar.addWidget(self.progressBar)
            self.progressBar.show()
        return self.progressBar


    def hideProgressBar(self):
        self.statusBar.removeWidget(self.progressBar)
        self.progressBarVisible = False


    def setUserName(self, userName):
        if userName:
            orgStructureName = u''
            orgStructureId = QtGui.qApp.currentOrgStructureId()
            if orgStructureId:
                db = QtGui.qApp.db
                table = db.table('OrgStructure')
                record = db.getRecordEx(table, [table['name']],
                                        [table['id'].eq(orgStructureId), table['deleted'].eq(0)])
                orgStructureName = forceStringEx(record.value('name')) if record else u''
            self.setWindowTitle(u'%s: %s%s' % (QtGui.qApp.title, userName, (u': %s'%(orgStructureName)) if orgStructureName else u''))
        else:
            self.setWindowTitle(QtGui.qApp.title)


    def findSubwindow(self, widget):
        for subwindow in self.centralWidget.subWindowList():
            if subwindow.widget() == widget:
                return subwindow
        return None
    

    @withWaitCursor
    def createSubwindow(self, widgetClass):
        widget = widgetClass(self)
        subwindow = self.centralWidget.addSubWindow(widget, Qt.SubWindow)
        return widget
    

    def openSubwindow(self, widget):
        subwindow = self.findSubwindow(widget)
        if subwindow:
            subwindow.showMaximized()
    

    def closeSubwindow(self, widget):
        subwindow = self.findSubwindow(widget)
        if subwindow:
            subwindow.close()
            self.centralWidget.activatePreviousSubWindow()


    def closeAllSubwindows(self):
        for subwindow in self.centralWidget.subWindowList():
            subwindow.close()


    def closeSubwindowsExcept(self, *widgets):
        for subwindow in self.centralWidget.subWindowList():
            if subwindow.widget() not in widgets:
                subwindow.close()


    def getMenuTree(self, menu):
        ''' получить список действий из меню в виде словаря
            {(text, objectName): {...}} если это подменю
            {(text, objectName): None} если это действие '''

        assert isinstance(menu, QtGui.QMenu)
        from collections import OrderedDict

        items = OrderedDict()
        for action in menu.actions():
            if action.isSeparator():
                continue
            elif action.menu():
                key = (unicode(action.text()), unicode(action.menu().objectName()))
                items[key] = self.getMenuTree(action.menu())
            else:
                key = (unicode(action.text()), unicode(action.objectName()))
                items[key] = None
        return items


    def loadReportsChiefActions(self):
        def loadReportsChiefActionsGroup(self, records, menu, groupId):
            for record in records:
                itemId = forceRef(record.value('id'))
                parentId = forceRef(record.value('parent_id'))
                title = forceString(record.value('title'))
                objectName = forceString(record.value('objectName'))
                if parentId != groupId:
                    continue
                if objectName:
                        slot = getattr(self, 'on_' + objectName + '_triggered', None)
                        if slot:
                            act = menu.addAction(title)
                            act.triggered.connect(slot)
                else:
                    loadReportsChiefActionsGroup(self, records, menu.addMenu(title), itemId)

        self.mnuReportsChief.clear()
        records = QtGui.qApp.db.getRecordList('ReportsChiefActions')
        loadReportsChiefActionsGroup(self, records, self.mnuReportsChief, None)


    def setSelectedReportsVisible(self, isVisible):
        records = QtGui.qApp.db.getRecordList('ReportsToHide')
        for record in records:
            objectName = forceString(record.value('objectName'))
            obj = getattr(self, objectName, None)
            if obj:
                if isinstance(obj, QtGui.QMenu):
                    obj.menuAction().setVisible(isVisible)
                else:
                    obj.setVisible(isVisible)


    def findDockTab(self, dockWidget):
        # найти QTabBar и индекс для док-виджета, если несколько док-виджетов сгруппированы по вкладкам
        # у док-виждетов Qt хранит указатели в QTabBar::tabData(), ищем по ним
        dockWidgetPtr = sip.unwrapinstance(dockWidget)
        tabBars = self.findChildren(QtGui.QTabBar)
        for tabBar in tabBars:
            if tabBar.parent() != self:
                continue
            for tabIndex in xrange(0, tabBar.count()):
                ptr, ok = tabBar.tabData(tabIndex).toULongLong()
                if ok and ptr == dockWidgetPtr:
                    return (tabBar, tabIndex)
        return (None, None)


    def addMruItem(self, mruList, id, descr):
        mruList = filter(lambda item: item[0] != id, mruList)
        mruList.insert(0, (id, descr))
        return mruList[:20]


    def prepareMruMenu(self, menu, clearAction, mruList, method):
        for action in menu.actions():
            if action.isSeparator():
                break
            menu.removeAction(action)
            action.deleteLater()
        actions = menu.actions()
        topAction = actions[0] if actions else None
        actions = []
        for id, descr in mruList:
            action = QtGui.QAction(descr, self)
            action.setData(toVariant(id))
            self.connect(action, SIGNAL('triggered()'), method)
            actions.append(action)
        menu.insertActions(topAction, actions)
        clearAction.setEnabled(bool(actions))


    def addMruEvent(self, eventId, descr):
        newList = self.addMruItem(self.mruEventList, eventId, descr)
        self.mruEventListChanged = newList != self.mruEventList
        self.mruEventList = newList


    def setAdmitting(self, isDuty=False):
        try:
            db = QtGui.qApp.db
            currentSessionId = None
            currentSessionQuery = db.query('SELECT @currentSessionId')
            if currentSessionQuery.next():
                currentSessionId = forceRef(currentSessionQuery.record().value(0))
            if currentSessionId:
                tableAppSession = db.table('AppSession')
                cols = [ fieldName
                         for fieldName in ('id', 'isAdmitting', 'isAppointment', 'isDuty')
                         if tableAppSession.hasField(fieldName)
                       ]
                record = db.getRecord(tableAppSession, cols, currentSessionId)
                if record:
                    admitting = None
                    if tableAppSession.hasField('isAdmitting'):
                        admitting = forceBool(record.value('isAdmitting'))
                    elif tableAppSession.hasField('isAppointment'):
                        admitting = forceBool(record.value('isAppointment'))
                    if tableAppSession.hasField('isDuty') and isDuty:
                        admitting = forceBool(record.value('isDuty'))

                    if admitting is not None:
                        admitting = not admitting
                        if isDuty:
                            record.setValue('isDuty',   admitting)
                        else:
                            record.setValue('isAdmitting',   admitting)
                            record.setValue('isAppointment', admitting)
                        QtGui.qApp.db.updateRecord(tableAppSession, record)
                        if isDuty:
                            QtGui.QMessageBox.information(self, u'Статус приема', u'Дежурство %s'%(u'завершено', u'начато')[admitting], QtGui.QMessageBox.Close, QtGui.QMessageBox.Close)
                        else:
                            QtGui.QMessageBox.information(self, u'Статус приема', u'Прием %s'%(u'завершен', u'начат')[admitting], QtGui.QMessageBox.Close, QtGui.QMessageBox.Close)
                        return admitting
        except:
            QtGui.qApp.logCurrentException()
            QtGui.QMessageBox.critical(self, u'Cтатус приема', u'Не удалось установить статус приема', QtGui.QMessageBox.Close)
        return False


    @pyqtSignature('')
    def on_actSanAviac_triggered(self):
        CSanAviacExport(self).exec_()

    # sanaviac
    @pyqtSignature('')
    def on_actExportSanAviacInfo_triggered(self):
        CExportSanAviacInfoDialog(self).exec_()

    @pyqtSignature('')
    def on_actUnlockRegKart_triggered(self):
        if QtGui.qApp.userHasRight(urUnlockData) or QtGui.qApp.userHasRight(urAdmin):
            dialog = CUnlockAppLockDialog(self, 'Client')
            dialog.setWindowTitle(u'Разблокировать регистрационную карту')
            #dialog.lblInfo.setText(u'Введите код пациента')


    @pyqtSignature('')
    def on_actUnlockEvent_triggered(self):
        if QtGui.qApp.userHasRight(urUnlockData) or QtGui.qApp.userHasRight(urAdmin):
            dialog = CUnlockAppLockDialog(self, 'Event')
            dialog.setWindowTitle(u'Разблокировать обращение (событие)')
            dialog.lblInfo.setText(u'Введите код карточки (вкладка "Примечание", поле "Код карточки")')

    @pyqtSignature('')
    def on_actUnlockTempInvalid_triggered(self):
        if QtGui.qApp.userHasRight(urUnlockData) or QtGui.qApp.userHasRight(urAdmin):
            dialog = CUnlockAppLockDialog(self, 'TempInvalid')
            dialog.setWindowTitle(u'Разблокировать эпизод ВУТ')
            dialog.lblInfo.setText(u'Введите код эпизода')

    @pyqtSignature('')
    def on_actUnlockMSE_triggered(self):
        if QtGui.qApp.userHasRight(urUnlockData) or QtGui.qApp.userHasRight(urAdmin):
            dialog = CUnlockAppLockDialog(self, 'Action', u'inspection_mse')
            dialog.setWindowTitle(u'Разблокировать направление на МСЭ')
            dialog.lblInfo.setText(u'Введите код эпизода')

    @pyqtSignature('')
    def on_actUnlockProphylaxisPlanning_triggered(self):
        if QtGui.qApp.userHasRight(urUnlockData) or QtGui.qApp.userHasRight(urAdmin):
            dialog = CUnlockAppLockDialog(self, 'ProphylaxisPlanning')
            dialog.setWindowTitle(u'Разблокировать ККДН')
            dialog.lblInfo.setText(u'Введите Id записи')

    @pyqtSignature('')
    def on_actUnlockKBIR_triggered(self):
        if QtGui.qApp.userHasRight(urUnlockData) or QtGui.qApp.userHasRight(urAdmin):
            dialog = CUnlockAppLockDialog(self, 'Action', u'111/y-20')
            dialog.setWindowTitle(u'Разблокировать карту беременной и родильницы')
            dialog.lblInfo.setText(u'Введите код эпизода')

    @pyqtSignature('')
    def on_actLogin_triggered(self):
        try:
            personId = userId = loginId = demoMode = login = None
            if not QtGui.qApp.db:
                QtGui.qApp.openDatabase()
            if QtGui.qApp.demoModePosible() and QtGui.qApp.demoModeRequested:
                ok, loginId, personId, demoMode, login = True, None, None, True, 'demo'
            else:
                ok = False
                if QtGui.qApp.kerberosAuthEnabled():
                    userId = tryKerberosAuth()
                    if userId:
                        ok, demoMode = True, False
                        login = forceString(QtGui.qApp.db.translate('Person', 'id', userId, 'login'))
                if not ok and QtGui.qApp.passwordAuthEnabled():
                    dialog = CLoginDialog(self)
                    dialog.setLoginName(QtGui.qApp.preferences.appUserName)
                    if dialog.exec_():
                        ok, loginId, personId, demoMode, login = True, dialog.loginId(), dialog.personId(), dialog.demoMode(), dialog.loginName()
                    else:
                        ok, loginId, personId, demoMode, login = False, None, None, False, ''
            if ok:
                QtGui.qApp.setUserId(personId, demoMode, loginId)
                QtGui.qApp.preferences.appUserName = login
                QtGui.qApp.loadCalendarInfo()
                self.setUserName(QtGui.qApp.userName())
                self.updateActionsState()
                QtGui.qApp._timeoutLogout.setup(QtGui.qApp.getConnectionTimeout() * 60000, timeoutFunc=self.logoutAndLogin)
                try:
                    showInformer(QtGui.qApp.mainWindow, True)
                except:
                    pass
                return
        except database.CDatabaseException, e:
            QtGui.QMessageBox.critical(self, u'Ошибка открытия базы данных', exceptionToUnicode(e), QtGui.QMessageBox.Close)
        except Exception, e:
            QtGui.QMessageBox.critical(self, u'Ошибка открытия базы данных',
                u'Невозможно установить соедиенение с базой данных\n' + exceptionToUnicode(e), QtGui.QMessageBox.Close)
            QtGui.qApp.logCurrentException()
        QtGui.qApp.closeDatabase()


    @pyqtSignature('')
    def on_actChangeCurrentPerson_triggered(self):
        loginId = QtGui.qApp.loginId
        personList = getLoginPersonList(loginId)
        dialogSelectPerson = CPersonSelectDialog(self, personList=personList)
        if dialogSelectPerson.exec_():
            self.dockResources.saveDialogPreferences()
            self.dockFreeQueue.saveDialogPreferences()
            self.dockDiagnosis.saveDialogPreferences()
            if QtGui.qApp.defaultKLADR()[:2] == u'23':
                self.dockSMP.saveDialogPreferences()
            self.closeAllSubwindows()
            personId = dialogSelectPerson.getPersonId()
            QtGui.qApp.clearUserId(True)
            QtGui.qApp.setUserId(personId, False, loginId)
            self.setUserName(QtGui.qApp.userName())
            self.updateActionsState()
            if QtGui.qApp.mainWindow.registry and QtGui.qApp.visibleMyDoctorArea:
                QtGui.qApp.mainWindow.registry.tabMyDoctorAreaContent.changeUserId()



    @pyqtSignature('')
    def on_actLogout_triggered(self):
        QtGui.qApp._timeoutLogout.stop()
        self.dockResources.saveDialogPreferences()
        self.dockFreeQueue.saveDialogPreferences()
        self.dockDiagnosis.saveDialogPreferences()
        if QtGui.qApp.defaultKLADR()[:2] == u'23':
            self.dockSMP.saveDialogPreferences()
        self.closeAllSubwindows()
        if QtGui.qApp.db:
            QtGui.qApp.clearUserId(True)
            QtGui.qApp.closeDatabase()
        self.updateActionsState()
        self.setUserName('')
        self.mruEventListChanged = True
        self.mruEventList = []


    # при отключении по таймеру
    def logoutAndLogin(self):
        self.on_actLogout_triggered()
        self.on_actLogin_triggered()


    @pyqtSignature('')
    def on_mnuMruEvents_aboutToShow(self):
        if self.mruEventListChanged:
            self.prepareMruMenu(self.mnuMruEvents, self.actClearMruEvents, self.mruEventList, self.onEventEdit)
            self.mruEventListChanged = False


    def onEventEdit(self):
        from Events.CreateEvent import editEvent
        eventId = forceRef(self.sender().data())
        if eventId:
            if not forceBool(QtGui.qApp.db.translate('Event', 'id', eventId, 'deleted')):
                editEvent(self, eventId)
            else:
                QtGui.QMessageBox.critical(self,
                                       u'Внимание!',
                                       u'Эту запись нельзя редактировать так как она удалена',
                                       QtGui.QMessageBox.Close)


    @pyqtSignature('')
    def on_actClearMruEvents_triggered(self):
        self.mruEventList = []
        self.mruEventListChanged = True


    @pyqtSignature('')
    def on_actQuit_triggered(self):
        self.close()


    @pyqtSignature('')
    def on_actRegistry_triggered(self):
        if self.registry is None:
            self.registry = self.createSubwindow(CRegistryWindow)
        self.openSubwindow(self.registry)
        self.closeSubwindowsExcept(self.registry)
        self.registry.switchMainTabToSpecifiedTabByIndex(self.registry.tabMain.indexOf(self.registry.tabRegistry))
        self.registry.batchRegLocatCardReset()


    @pyqtSignature('')
    def on_actSuspenedAppointment_triggered(self):
        if self.suspendedAppointment is None:
            self.suspendedAppointment = self.createSubwindow(CSuspenedAppointmentWindow)
        self.openSubwindow(self.suspendedAppointment)
        self.closeSubwindowsExcept(self.suspendedAppointment)


    @pyqtSignature('')
    def on_actDispExchange_triggered(self):
        if self.dispExchange is None:
            self.dispExchange = self.createSubwindow(CDispExchangeWindow)
        self.openSubwindow(self.dispExchange)
        self.closeSubwindowsExcept(self.dispExchange)


    @pyqtSignature('')
    def on_actDistantMonitoring_triggered(self):
        if self.distantMonitoring is None:
            self.distantMonitoring = self.createSubwindow(CDistantMonitoringWindow)
        self.openSubwindow(self.distantMonitoring)
        self.closeSubwindowsExcept(self.distantMonitoring)


    def on_actHomeCallRequests_triggered(self):
        if self.homeCallRequests is None:
            self.homeCallRequests = self.createSubwindow(CHomeCallRequestsWindow)
        self.openSubwindow(self.homeCallRequests)
        self.closeSubwindowsExcept(self.homeCallRequests)


    @pyqtSignature('')
    def on_actProphylaxisPlanning_triggered(self):
        if self.prophylaxisPlanning is None:
            self.prophylaxisPlanning = self.createSubwindow(CProphylaxisPlanningWindow)
        self.openSubwindow(self.prophylaxisPlanning)
        self.closeSubwindowsExcept(self.prophylaxisPlanning)


    @pyqtSignature('')
    def on_actTMKAdmin_triggered(self):
        template = getFirstPrintTemplate('adminTMK')
        if template:
            data = {'filter': {}}
            applyTemplate(self, template.id, data)

    @pyqtSignature('')
    def on_actTMKListDirections_triggered(self):
        template = getFirstPrintTemplate('listTMK')
        if template:
            data = {'filter': {}}
            applyTemplate(self, template.id, data)

    @pyqtSignature('')
    def on_actTMKReports_triggered(self):
        CTMKReports(self).exec_()

    @pyqtSignature('')
    def on_actTimeline_triggered(self):
        CTimelineDialog(self).exec_()


    @pyqtSignature('')
    def on_actFormRegistration_triggered(self):
        QtGui.qApp.setWaitCursor()
        try:
            blanksDialog = CBlanksDialog(self)
        finally:
            QtGui.qApp.restoreOverrideCursor()
        if blanksDialog:
            blanksDialog.exec_()


    @pyqtSignature('')
    def on_actDemogrCertificates_triggered(self):
        CDemogrCertificatesDialog(self).exec_()


    @pyqtSignature('')
    def on_actSvodService_triggered(self):
        CSvodReportListDialog(self).exec_()


    @pyqtSignature('')
    def on_actQuoting_triggered(self):
        dialog = CQuotingDialog(self)
        if not (QtGui.qApp.userHasRight(urAccessQuoting) or QtGui.qApp.userHasRight(urAdmin)):
            dialog.setEditable(False)
        dialog.exec_()


    @pyqtSignature('')
    def on_actTissueJournal_triggered(self):
        CTissueJournalDialog(self).exec_()


    @pyqtSignature('')
    def on_actTreatmentScheme_triggered(self):
        CTreatmentSchemeDialog(self).exec_()


    @pyqtSignature('')
    def on_actTreatmentSchedule_triggered(self):
        CTreatmentScheduleDialog(self).exec_()


    @pyqtSignature('')
    def on_actTreatmentControl_triggered(self):
        CTreatmentControlDialog(self).exec_()


    @pyqtSignature('')
    def on_actHospitalBeds_triggered(self):
        QtGui.qApp.setWaitCursor()
        try:
            hospitalBedsDialog = CHospitalBedsDialog(self)
        finally:
            QtGui.qApp.restoreOverrideCursor()
        if hospitalBedsDialog:
            hospitalBedsDialog.exec_()

    @pyqtSignature('')
    def on_actPaidServices_triggered(self):
        CPaidServices(self).exec_()


    @pyqtSignature('')
    def on_actVolumeServices_triggered(self):
        CVolumeServices(self).exec_()


    @pyqtSignature('')
    def on_actHealthResort_triggered(self):
        QtGui.qApp.setWaitCursor()
        try:
            healthResortDialog = CHealthResortDialog(self)
        finally:
            QtGui.qApp.restoreOverrideCursor()
        if healthResortDialog:
            healthResortDialog.exec_()

    
    @pyqtSignature('')
    def on_actCentralizedAccounting_triggered(self):
        QtGui.qApp.setWaitCursor()
        try:
            centralizedAccountingDialog = CCentralizedAccountingDialog(self)
        finally:
            QtGui.qApp.restoreOverrideCursor()
        if centralizedAccountingDialog:
            centralizedAccountingDialog.exec_()
    

    @pyqtSignature('')
    def on_actSurgeryJournal_triggered(self):
        QtGui.qApp.setWaitCursor()
        try:
            surgeryJournalDialog = CSurgeryJournalDialog(self)
        finally:
            QtGui.qApp.restoreOverrideCursor()
        if surgeryJournalDialog:
            surgeryJournalDialog.exec_()


    @pyqtSignature('')
    def on_actSurveillance_triggered(self):
        QtGui.qApp.setWaitCursor()
        try:
            surveillanceDialog = CSurveillanceDialog(self)
        finally:
            QtGui.qApp.restoreOverrideCursor()
        if surveillanceDialog:
            surveillanceDialog.exec_()


    @pyqtSignature('')
    def on_actJobsPlanning_triggered(self):
        CJobPlanner(self).exec_()


    @pyqtSignature('')
    def on_actJobsOperating_triggered(self):
        CJobsOperatingDialog(self).exec_()


    @pyqtSignature('')
    def on_actStockControl_triggered(self):
        CStockDialog(self).exec_()


    @pyqtSignature('')
    def on_actAccounting_triggered(self):
        CAccountingDialog(self).exec_()


    @pyqtSignature('')
    def on_actCashBook_triggered(self):
        CCashBookDialog(self).exec_()


    @pyqtSignature('')
    def on_actImportActionType_triggered(self):
        ImportActionType()


    @pyqtSignature('')
    def on_actImportEventType_triggered(self):
        ImportEventType()


    @pyqtSignature('')
    def on_actImportActionTemplate_triggered(self):
        ImportActionTemplate()


    @pyqtSignature('')
    def on_actImportDD_triggered(self):
        ImportDD()


    @pyqtSignature('')
    def on_actImport131DBF_triggered(self):
        Import131(self)


    @pyqtSignature('')
    def on_actImport131XML_triggered(self):
        Import131XML(self)


    @pyqtSignature('')
    def on_actImport131Errors_triggered(self):
        Import131Errors(self)


    @pyqtSignature('')
    def on_actImportLgot_triggered(self):
        ImportLgot(self)


    @pyqtSignature('')
    def on_actImportQuotaFromVTMP_triggered(self):
        ImportQuotaFromVTMP(self)


    @pyqtSignature('')
    def on_actImportProfilesEIS_triggered(self):
        ImportProfiles(self)


    @pyqtSignature('')
    def on_actImportProfilesINFIS_triggered(self):
        ImportProfilesINFIS(self)


    @pyqtSignature('')
    def on_actImportEisOmsClients_triggered(self):
        importClientsFromEisOms(self)


    @pyqtSignature('')
    def on_actImportEisOmsLpu_triggered(self):
        ImportEISOMS_LPU(self)


    @pyqtSignature('')
    def on_actImportEisOmsSmo_triggered(self):
        ImportEISOMS_SMO(self)


    @pyqtSignature('')
    def on_actImportServiceNomen_triggered(self):
        CImportServiceNomen(self).exec_()

    def on_actImportServiceNomen2_triggered(self):
        CImportServiceNomen(self, 2).exec_()


    @pyqtSignature('')
    def on_actImportRbCureType_triggered(self):
        CImportRbCureType(self).exec_()


    @pyqtSignature('')
    def on_actImportRbCureMethod_triggered(self):
        CImportRbCureMethod(self).exec_()


    @pyqtSignature('')
    def on_actImportRbPatientModel_triggered(self):
        CImportRbPatientModel(self).exec_()


    @pyqtSignature('')
    def on_actImportServiceMes_triggered(self):
        CImportServiceMes(self).exec_()


    @pyqtSignature('')
    def on_actImportRbResult_triggered(self):
        ImportRbResult(self)


    @pyqtSignature('')
    def on_actImportRbDiagnosticResult_triggered(self):
        ImportRbDiagnosticResult(self)


    @pyqtSignature('')
    def on_actImportRbUnit_triggered(self):
        ImportRbUnit(self)


    @pyqtSignature('')
    def on_actImportRbThesaurus_triggered(self):
        ImportRbThesaurus(self)


    @pyqtSignature('')
    def on_actImportRbService_triggered(self):
        ImportRbService(self)


    @pyqtSignature('')
    def on_actImportRbComplain_triggered(self):
        ImportRbComplain(self)


    @pyqtSignature('')
    def on_actImportPolicySerialDBF_triggered(self):
        ImportPolicySerialDBF(self)


    @pyqtSignature('')
    def on_actImportOrgsINFIS_triggered(self):
        ImportOrgsINFIS(self)


    @pyqtSignature('')
    def on_actImpotrFromSail_triggered(self):
        ImportFromSail()


    @pyqtSignature('')
    def on_actImportFromSailXML_triggered(self):
        ImportFromSailXML()


    @pyqtSignature('')
    def on_actImportPrimaryDocFromXml_triggered(self):
        ImportPrimaryDocFromXml(self)


    @pyqtSignature('')
    def on_actImportCSVClient_triggered(self):
        ImportCSVClient(self).exec_()


    @pyqtSignature('')
    def on_actImportVMPCases_triggered(self):
        ImportVMPCases(self).exec_()


    @pyqtSignature('')
    def on_actExport131_triggered(self):
        Export131(self).exec_()


    @pyqtSignature('')
    def on_actExportActionType_triggered(self):
        ExportActionType()


    @pyqtSignature('')
    def on_actExportEventType_triggered(self):
        ExportEventType()


    @pyqtSignature('')
    def on_actExportActionTemplate_triggered(self):
        ExportActionTemplate()


    @pyqtSignature('')
    def on_actExportPrimaryDocInXml_triggered(self):
        ExportPrimaryDocInXml(self)


    @pyqtSignature('')
    def on_actExportXmlEmc_triggered(self):
        ExportXmlEmc(self)


    @pyqtSignature('')
    def on_actExportActionResult_triggered(self):
        ExportActionResult(self)

    @pyqtSignature('')
    def on_actExportFeedDataCsv_triggered(self):
        exportFeedDataCsv(self)


    @pyqtSignature('')
    def on_actExportVMPCases_triggered(self):
        ExportVMPCases(self).exec_()

    @pyqtSignature('')
    def on_actExportRbResult_triggered(self):
        ExportRbResult(self)


    @pyqtSignature('')
    def on_actExportRbDiagnosticResult_triggered(self):
        ExportRbDiagnosticResult(self)


    @pyqtSignature('')
    def on_actExportRbUnit_triggered(self):
        ExportRbUnit(self)


    @pyqtSignature('')
    def on_actExportRbThesaurus_triggered(self):
        ExportRbThesaurus(self)


    @pyqtSignature('')
    def on_actExportRbComplain_triggered(self):
        ExportRbComplain(self)


    @pyqtSignature('')
    def on_actExportRbService_triggered(self):
        ExportRbService(self)
    
    
    @pyqtSignature('')
    def on_actExportRbPrintTemplate_triggered(self):
        ExportRbPrintTemplate()

    
    @pyqtSignature('')
    def on_actImportRbPrintTemplate_triggered(self):
        ImportRbPrintTemplate()
    
    
    @pyqtSignature('')
    def on_actImportSPR_triggered(self):
        ImportSPR()
    

    @pyqtSignature('')
    def on_actExportHL7v2_5_triggered(self):
        ExportHL7v2_5(self)


    @pyqtSignature('')
    def on_actStatReportF12_D_1_07_triggered(self):
        CStatReportF12_D_1_07(self).exec_()


    @pyqtSignature('')
    def on_actStatReportF12_D_2_07_triggered(self):
        CStatReportF12_D_2_07(self, mode='07').exec_()


    @pyqtSignature('')
    def on_actStatReportF12_D_1_08_triggered(self):
        CStatReportF12_D_1_08(self).exec_()


    @pyqtSignature('')
    def on_actStatReportF12_D_2_08_triggered(self):
        CStatReportF12_D_2_07(self, mode='08').exec_()


    @pyqtSignature('')
    def on_actStatReportF12_D_3_M_triggered(self):
        CStatReportF12_D_3_M(self).exec_()


    @pyqtSignature('')
    def on_actStatReportF12_D_2_09_triggered(self):
        CStatReportF12_D_2_07(self, mode='09').exec_()


    @pyqtSignature('')
    def on_actStatReportF12_D_1_10_triggered(self):
        CStatReportF12_D_1_10(self).exec_()


    @pyqtSignature('')
    def on_actStatReportF12_D_2_10_triggered(self):
        CStatReportF12_D_2_10(self).exec_()


    @pyqtSignature('')
    def on_actStatReport1NP2000_triggered(self):
        CStatReport1NP2000(self).exec_()


    @pyqtSignature('')
    def on_actStatReportF5_D_For_Teenager_triggered(self):
        CStatReportF5_D_For_Teenager(self).exec_()


    @pyqtSignature('')
    def on_actStatReportF4_D_For_Teenager_triggered(self):
        CStatReportF4_D_For_Teenager(self).exec_()


    @pyqtSignature('')
    def on_actStatReport1NP3000_triggered(self):
        CStatReport1NP3000(self).exec_()


    @pyqtSignature('')
    def on_actStatReport1NP4000_triggered(self):
        CStatReport1NP4000(self).exec_()


    @pyqtSignature('')
    def on_actStatReport1NP5000_triggered(self):
        CStatReport1NP5000(self).exec_()


    @pyqtSignature('')
    def on_actStatReport1NP7000_triggered(self):
        CStatReport1NP7000(self).exec_()


    @pyqtSignature('')
    def on_actStatReport1DD1000_triggered(self):
        CStatReport1DD1000(self).exec_()


    @pyqtSignature('')
    def on_actStatReport1DD2000_triggered(self):
        CStatReport1DD2000(self).exec_()


    @pyqtSignature('')
    def on_actStatReport1DD3000_triggered(self):
        CStatReport1DD3000(self).exec_()


    @pyqtSignature('')
    def on_actMUOMSOFTable1_triggered(self):
        CMUOMSOFTable1(self).exec_()


    @pyqtSignature('')
    def on_actMUOMSOFTable3_triggered(self):
        CMUOMSOFTable3(self).exec_()


    @pyqtSignature('')
    def on_actMUOMSOFCity_triggered(self):
        CMUOMSOFCity(self).exec_()


    @pyqtSignature('')
    def on_actMUOMSOFForeign_triggered(self):
        CMUOMSOFForeign(self).exec_()


    @pyqtSignature('')
    def on_actReportF14App3ksg_triggered(self):
        CReportF14App3ksg(self).exec_()


    @pyqtSignature('')
    def on_actStatReport1DDAll_triggered(self):
        CStatReport1DDAll(self).exec_()


    @pyqtSignature('')
    def on_actStatReportF131ByDoctors_triggered(self):
        CStatReportF131ByDoctors(self).exec_()


    @pyqtSignature('')
    def on_actStatReportF131ByEmployer_triggered(self):
        CStatReportF131ByEmployer(self).exec_()


    @pyqtSignature('')
    def on_actStatReportF131ByRaion_triggered(self):
        CStatReportF131ByRaion(self).exec_()


    @pyqtSignature('')
    def on_actStatReportF131Raion_triggered(self):
        CStatReportF131Raion(self).exec_()


    @pyqtSignature('')
    def on_actStatReportF131ByDD_triggered(self):
        CStatReportF131ByDD(self).exec_()


    @pyqtSignature('')
    def on_actStomatReport039_triggered(self):
        CStomatReport(self).exec_()


    @pyqtSignature('')
    def on_actStomatReportDay_triggered(self):
        CStomatDayReport(self).exec_()


    @pyqtSignature('')
    def on_actFinanceStomatReportDay_2015_triggered(self):
        CStomatDayReport_2015(self).exec_()


    @pyqtSignature('')
    def on_actFinanceStomatReportCompositeList_triggered(self):
        CStomatReportCompositeList(self).exec_()


    @pyqtSignature('')
    def on_actFinanceStomatReportToSpecialityList_triggered(self):
        CStomatReportToSpecialityList(self).exec_()


    @pyqtSignature('')
    def on_actTimelineForPerson_triggered(self):
        CTimelineForPersonEx(self).exec_()


    @pyqtSignature('')
    def on_actReportVisitBySchedule_triggered(self):
        CReportVisitBySchedule(self).exec_()


    @pyqtSignature('')
    def on_actReportVisitByNextEventDate_triggered(self):
        CReportVisitByNextEventDate(self).exec_()


    @pyqtSignature('')
    def on_actReportScheduleRegisteredCount_triggered(self):
        CReportScheduleRegisteredCount(self).exec_()


    @pyqtSignature('')
    def on_actReportOutgoingDirections_triggered(self):
        CExternalOutgoingDirectionsReport(self).exec_()


    @pyqtSignature('')
    def on_actOutgoingDirectionsReport_triggered(self):
        COutgoingDirectionsReport(self).exec_()


    @pyqtSignature('')
    def on_actReportInternalDirections_triggered(self):
        CReportInternalDirections(self).exec_()


    @pyqtSignature('')
    def on_actReportIncomingDirections_triggered(self):
        CExternalIncomingDirectionsReport(self).exec_()


    @pyqtSignature('')
    def on_actTimelineForOffices_triggered(self):
        CTimelineForOfficesEx(self).exec_()


    @pyqtSignature('')
    def on_actDailyReportPreRecord_triggered(self):
        CDailyReportPreRecord(self).exec_()


    @pyqtSignature('')
    def on_actPreRecordDoctors_triggered(self):
        CPreRecordDoctorsEx(self).exec_()


    @pyqtSignature('')
    def on_actPreRecordPlanExecutionByDoctors_triggered(self):
        CPreRecordPlanExecutionByDoctors(self).exec_()


    @pyqtSignature('')
    def on_actPreRecordUsers_triggered(self):
        CPreRecordUsersEx(self).exec_()


    @pyqtSignature('')
    def on_actPreRecordSpeciality_triggered(self):
        CPreRecordSpecialityEx(self).exec_()


    @pyqtSignature('')
    def on_actJournalBeforeRecord_triggered(self):
        CJournalBeforeRecordEx(self).exec_()


    @pyqtSignature('')
    def on_actJournalBeforeRecordAV_triggered(self):
        CJournalBeforeRecordAV(self).exec_()


    @pyqtSignature('')
    def on_actDailyJournalBeforeRecord_triggered(self):
        CDailyJournalBeforeRecord(self).exec_()

    @pyqtSignature('')
    def on_actActionPropertiesTestsReport_triggered(self):
        CActionPropertiesTestsReport(self).exec_()

    @pyqtSignature('')
    def on_actNomenclatureReportForm2M3_triggered(self):
        CMonthlyNomenclatureReport(self).exec_()

    @pyqtSignature('')
    def on_actPlannedClientInvoiceNomenclaturesReport_triggered(self):
        CPlannedClientInvoiceNomenclaturesReport(self).exec_()

    @pyqtSignature('')
    def on_actClientNomenclatureInvoiceReport_triggered(self):
        CClientNomenclatureInvoiceReport(self).exec_()

    @pyqtSignature('')
    def on_actReportNomenclaureMotions_triggered(self):
        CReportNomenclaureMotions(self).exec_()

    @pyqtSignature('')
    def on_actClientNomenclatureActionReport_triggered(self):
        CClientNomenclatureActionReport(self).exec_()


    @pyqtSignature('')
    def on_actNomenclatureBook_triggered(self):
        CNomenclatureBook(self).exec_()


    @pyqtSignature('')
    def on_actReportForm131_o_1000_2014_triggered(self):
        CReportForm131_o_1000_2014(self).exec_()


    @pyqtSignature('')
    def on_actReportForm131_o_2000_2014_triggered(self):
        CReportForm131_o_2000_2014(self).exec_()


    @pyqtSignature('')
    def on_actReportForm131_o_3000_2014_triggered(self):
        CReportForm131_o_3000_2014(self).exec_()


    @pyqtSignature('')
    def on_actReportForm131_o_4000_2014_triggered(self):
        CReportForm131_o_4000_2014(self).exec_()


    @pyqtSignature('')
    def on_actReportForm131_o_5000_2014_triggered(self):
        CReportForm131_o_5000_2014(self).exec_()


    @pyqtSignature('')
    def on_actReportForm1_1000_triggered(self):
        CReportF1_1000(self).exec_()


    @pyqtSignature('')
    def on_actReportForm1_2000_triggered(self):
        CReportF1_2000(self).exec_()


    @pyqtSignature('')
    def on_actForm10_3000_triggered(self):
        CForm10_3000(self).exec_()


    @pyqtSignature('')
    def on_actReportForm1RB_2000_triggered(self):
        CReportF1RB_2000(self).exec_()

    @pyqtSignature('')
    def on_actForm10_2000_triggered(self):
        CForm10_2000(self).exec_()

    @pyqtSignature('')
    def on_actForm12_1000_1100_triggered(self):
        CForm12_1000_1100(self).exec_()

    @pyqtSignature('')
    def on_actForm12_1500_1900_triggered(self):
        CForm12_1500_1900(self).exec_()

    @pyqtSignature('')
    def on_actForm12_2000_2100_triggered(self):
        CForm12_2000_2100(self).exec_()

    @pyqtSignature('')
    def on_actForm12_3000_3100_triggered(self):
        CForm12_3000_3100(self).exec_()

    @pyqtSignature('')
    def on_actForm12_4000_4100_triggered(self):
        CForm12_4000_4100(self).exec_()

    @pyqtSignature('')
    def on_actForm19_1000_triggered(self):
        CStatReportF19_1000(self).exec_()

    @pyqtSignature('')
    def on_actForm19_2000_triggered(self):
        CStatReportF19_2000(self).exec_()

    @pyqtSignature('')
    def on_actForm19_1000_Psychistry_triggered(self):
        CStatReportF19_1000_Psychiatry(self).exec_()

    @pyqtSignature('')
    def on_actForm19_2000_Psychistry_triggered(self):
        CStatReportF19_2000_Psychiatry(self).exec_()

    @pyqtSignature('')
    def on_actForm030po17_triggered(self):
        CReportPreventiveMinors(self).exec_()

    @pyqtSignature('')
    def on_actForm030dco13_triggered(self):
        CReport030dco13(self).exec_()

    @pyqtSignature('')
    def on_actForm36_2100_2190_triggered(self):
        CForm36_2100_2190(self).exec_()

    @pyqtSignature('')
    def on_actForm36_2200_2210_triggered(self):
        CForm36_2200_2210(self).exec_()

    @pyqtSignature('')
    def on_actForm36_2300_2340_triggered(self):
        CForm36_2300_2340(self).exec_()

    @pyqtSignature('')
    def on_actForm36_2400_triggered(self):
        CForm36_2400(self).exec_()

    @pyqtSignature('')
    def on_actForm36_2500_triggered(self):
        CForm36_2500(self).exec_()

    @pyqtSignature('')
    def on_actForm36_2600_triggered(self):
        CForm36_2600(self).exec_()

    @pyqtSignature('')
    def on_actForm36_2800_triggered(self):
        CForm36_2800(self).exec_()

    @pyqtSignature('')
    def on_actForm36_2900_triggered(self):
        CForm36_2900(self).exec_()

    @pyqtSignature('')
    def on_actForm36PL_2100_2190_triggered(self):
        CForm36PL_2100_2190(self).exec_()

    @pyqtSignature('')
    def on_actForm36PL_2200_2240_triggered(self):
        CForm36PL_2200_2240(self).exec_()

    @pyqtSignature('')
    def on_actForm11_1000_triggered(self):
        CForm11_1000(self).exec_()


    @pyqtSignature('')
    def on_actForm11_2000_triggered(self):
        CForm11_2000(self).exec_()


    @pyqtSignature('')
    def on_actForm11_4000_triggered(self):
        CForm11_4000(self).exec_()


    @pyqtSignature('')
    def on_actForm37_2100_2170_triggered(self):
        CForm37_2100_2170(self).exec_()


    @pyqtSignature('')
    def on_actForm37_2200_2210_triggered(self):
        CForm37_2200_2210(self).exec_()


    @pyqtSignature('')
    def on_actForm37_2300_2330_triggered(self):
        CForm37_2300_2330(self).exec_()


    @pyqtSignature('')
    def on_actReportInvalidGroupMovement_triggered(self):
        CReportInvalidGroupMovement(self).exec_()


    @pyqtSignature('')
    def on_actReportMonitoringReabilityInvalid_triggered(self):
        CReportMonitoringReabilityInvalid(self).exec_()


    @pyqtSignature('')
    def on_actKarta_Expert_triggered(self):
        CKarta_Expert(self).exec_()


    @pyqtSignature('')
    def on_actForm035_triggered(self):
        CForm035(self).exec_()


    @pyqtSignature('')
    def on_actReportF1RB_AmbulatoryCare_triggered(self):
        CReportF1RB_AmbulatoryCare(self).exec_()


    @pyqtSignature('')
    def on_actReportF1RB_DentalTreatment_triggered(self):
        CReportF1RB_DentalTreatment(self).exec_()


    @pyqtSignature('')
    def on_actReportF1RB_AmbulanceCall_triggered(self):
        CReportF1RB_AmbulanceCall(self).exec_()


    @pyqtSignature('')
    def on_actReportUniversalEventList_triggered(self):
        CReportUniversalEventList(self).exec_()

    @pyqtSignature('')
    def on_actReportActivityMO_triggered(self):
        CReportActivityMO(self).exec_()

    @pyqtSignature('')
    def on_actRepService_triggered(self):
        CRepService(self).exec_()

    @pyqtSignature('')
    def on_actAttach_IEMK_EGISZ_triggered(self):
        CAttach_IEMK_EGISZ(self).exec_()

    @pyqtSignature('')
    def on_actAttach_SEMD_IEMK_triggered(self):
        CAttach_SEMD_IEMK(self).exec_()

    @pyqtSignature('')
    def on_actRepServiceAttach_triggered(self):
        CRepServiceAttach(self).exec_()

    @pyqtSignature('')
    def on_actRepJournalNapr_triggered(self):
        CRepJournalNapr(self).exec_()

    @pyqtSignature('')
    def on_actReportLgotL30_triggered(self):
        CReportLgotL30(self).exec_()

    @pyqtSignature('')
    def on_actRepKolRecipe_triggered(self):
        CRepKolRecipe(self).exec_()

    @pyqtSignature('')
    def on_actRepLgotRecipe_triggered(self):
        CRepLgotRecipe(self).exec_()

    @pyqtSignature('')
    def on_actLgotRecip_triggered(self):
        CLgotRecip(self).exec_()

    @pyqtSignature('')
    def on_actLgot030_triggered(self):
        CLgot030(self).exec_()

    @pyqtSignature('')
    def on_actSoclab_triggered(self):
        CSOClab(self).exec_()


    @pyqtSignature('')
    def on_actODLI_triggered(self):
        CODLI(self).exec_()

    @pyqtSignature('')
    def on_actNaprGosp_triggered(self):
        CNaprGosp(self).exec_()

    @pyqtSignature('')
    def on_actNullHospital_triggered(self):
        CNullHospital(self).exec_()

    @pyqtSignature('')
    def on_actHospital_triggered(self):
        CHospital(self).exec_()

    @pyqtSignature('')
    def on_actReportForm131_o_6000_2014_triggered(self):
        CReportForm131_o_6000_2014(self).exec_()


    @pyqtSignature('')
    def on_actReportForm131_o_7000_2014_triggered(self):
        CReportForm131_o_7000_2014(self).exec_()


    @pyqtSignature('')
    def on_actReportForm131_o_1000_2015_triggered(self):
        CReportForm131_o_1000_2015(self).exec_()


    @pyqtSignature('')
    def on_actReportForm131_o_1000_2015_2016_triggered(self):
        CReportForm131_o_1000_2015_16(self).exec_()

    @pyqtSignature('')
    def on_actReportForm131_o_2000_2015_triggered(self):
        CReportForm131_o_2000_2015(self).exec_()


    @pyqtSignature('')
    def on_actReportForm131_o_3000_2015_triggered(self):
        CReportForm131_o_3000_2015(self).exec_()


    @pyqtSignature('')
    def on_actReportForm131_o_4000_2015_triggered(self):
        CReportForm131_o_4000_2015(self).exec_()


    @pyqtSignature('')
    def on_actReportForm131_o_5000_2015_triggered(self):
        CReportForm131_o_5000_2015(self).exec_()


    @pyqtSignature('')
    def on_actReportForm131_o_5001_2015_triggered(self):
        CReportForm131_o_5001_2015(self).exec_()


    @pyqtSignature('')
    def on_actReportForm131_o_6000_2015_triggered(self):
        CReportForm131_o_6000_2015(self).exec_()


    @pyqtSignature('')
    def on_actReportForm131_o_7000_2015_triggered(self):
        CReportForm131_o_7000_2015(self).exec_()


# ############################################################################
    @pyqtSignature('')
    def on_actReportForm131_o_1000_2016_triggered(self):
        CReportForm131_o_1000_2016(self).exec_()


    @pyqtSignature('')
    def on_actReportForm131_o_2000_2016_triggered(self):
        CReportForm131_o_2000_2016(self).exec_()


    @pyqtSignature('')
    def on_actReportForm131_o_3000_2016_triggered(self):
        CReportForm131_o_3000_2016(self).exec_()


    @pyqtSignature('')
    def on_actReportForm131_o_4000_2016_triggered(self):
        CReportForm131_o_4000_2016(self).exec_()


    @pyqtSignature('')
    def on_actReportForm131_o_5000_2016_triggered(self):
        CReportForm131_o_5000_2016(self).exec_()


    @pyqtSignature('')
    def on_actReportForm131_o_5001_2016_triggered(self):
        CReportForm131_o_5001_2016(self).exec_()


    @pyqtSignature('')
    def on_actReportForm131_o_6000_2016_triggered(self):
        CReportForm131_o_6000_2016(self).exec_()


    @pyqtSignature('')
    def on_actReportForm131_o_7000_2016_triggered(self):
        CReportForm131_o_7000_2016(self).exec_()


    @pyqtSignature('')
    def on_actReportForm131_o_1000_2021_triggered(self):
        CReportForm131_o_1000_2021(self).exec_()


    @pyqtSignature('')
    def on_actReportForm131_o_2000_2021_triggered(self):
        CReportForm131_o_2000_2021(self).exec_()


    @pyqtSignature('')
    def on_actReportForm131_o_3000_2021_triggered(self):
        CReportForm131_o_3000_2021(self).exec_()


    @pyqtSignature('')
    def on_actReportForm131_o_4000_2021_triggered(self):
        CReportForm131_o_4000_2021(self).exec_()


    @pyqtSignature('')
    def on_actReportForm131_o_5000_2021_triggered(self):
        CReportForm131_o_5000_2021(self).exec_()


    @pyqtSignature('')
    def on_actReportForm131_o_6000_2021_triggered(self):
        CReportForm131_o_6000_2021(self).exec_()
# ############################################################################


    @pyqtSignature('')
    def on_actReportForm131_o_1000_2021_triggered(self):
        CReportForm131_o_1000_2021(self).exec_()


    @pyqtSignature('')
    def on_actReportForm131_o_2000_2021_triggered(self):
        CReportForm131_o_2000_2021(self).exec_()


    @pyqtSignature('')
    def on_actReportForm131_o_3000_2021_triggered(self):
        CReportForm131_o_3000_2021(self).exec_()


    @pyqtSignature('')
    def on_actReportForm131_o_4000_2021_triggered(self):
        CReportForm131_o_4000_2021(self).exec_()


    @pyqtSignature('')
    def on_actReportForm131_o_5000_2021_triggered(self):
        CReportForm131_o_5000_2021(self).exec_()


    @pyqtSignature('')
    def on_actReportForm131_o_6000_2021_triggered(self):
        CReportForm131_o_6000_2021(self).exec_()


    @pyqtSignature('')
    def on_actReportImunoprophylaxisForm5_triggered(self):
        CReportImunoprophylaxisForm5(self).exec_()


    @pyqtSignature('')
    def on_actReportLaboratoryProbeExportImport_triggered(self):
        CReportLaboratoryProbeExportImport(self).exec_()


    @pyqtSignature('')
    def on_actReportUseContainers_triggered(self):
        CReportUseContainers(self).exec_()
    
    
    @pyqtSignature('')
    def on_actReportVaccineJournal_triggered(self):
        CReportVaccineJournal(self).exec_()


    @pyqtSignature('')
    def on_actReportPreventiveVaccinatiomsAndTuberculinTests_triggered(self):
        CReportVaccineAndTuberculinTestJournal(self).exec_()


    @pyqtSignature('')
    def on_actReportProtozoa_triggered(self):
        CReportProtozoa(self).exec_()


    @pyqtSignature('')
    def on_actReportHepatitis_triggered(self):
        CReportHepatitis(self).exec_()


    @pyqtSignature('')
    def on_actReportLaboratoryActionsByMedicalType_triggered(self):
        CReportLaboratoryActionsByMedicalType(self).exec_()


    @pyqtSignature('')
    def on_actReportLaboratoryAntibodiesHIV_triggered(self):
        CReportLaboratoryAntibodiesHIV(self).exec_()


    @pyqtSignature('')
    def on_actReportTraumaMiteBites_triggered(self):
        CReportTraumaMiteBites(self).exec_()


    @pyqtSignature('')
    def on_actReportTraumaAnimalBites_triggered(self):
        CReportTraumaAnimalBites(self).exec_()


    @pyqtSignature('')
    def on_actReportTraumaIce_triggered(self):
        CReportTraumaIce(self).exec_()


    @pyqtSignature('')
    def on_actReportTraumaHospitalization_triggered(self):
        CReportTraumaHospitalization(self).exec_()


    @pyqtSignature('')
    def on_actReportTraumaWorkInjury_triggered(self):
        CReportTraumaWorkInjury(self).exec_()


    @pyqtSignature('')
    def on_actReportTraumaTelephoneMessage_triggered(self):
        CReportTraumaTelephoneMessage(self).exec_()


    @pyqtSignature('')
    def on_actReportTraumaGypsum_triggered(self):
        CReportTraumaGypsum(self).exec_()


    @pyqtSignature('')
    def on_actReportTraumaOperations_triggered(self):
        CReportTraumaOperations(self).exec_()


    @pyqtSignature('')
    def on_actReportTraumaJournalVaccinations_triggered(self):
        CReportTraumaJournalVaccinations(self).exec_()


    @pyqtSignature('')
    def on_actReportSanatoriumArrived_triggered(self):
        CReportSanatoriumArrived(self).exec_()


    @pyqtSignature('')
    def on_actReportSanatoriumResidents_triggered(self):
        CReportSanatoriumResidents(self).exec_()


    @pyqtSignature('')
    def on_actReportSanatoriumArrivalDiary_triggered(self):
        CReportSanatoriumArrivalDiary(self).exec_()


    @pyqtSignature('')
    def on_actReportHRAnalysisUsePlacesRegions_triggered(self):
        CReportHealthResortAnalysisUsePlacesRegions(self).exec_()


    @pyqtSignature('')
    def on_actReportMedicalServiceExportByProfile_triggered(self):
        CReportMedicalServiceExportByProfile(self).exec_()


    @pyqtSignature('')
    def on_actReportMedicalServiceExportByCitizenship_triggered(self):
        CReportMedicalServiceExportByCitizenship(self).exec_()


    @pyqtSignature('')
    def on_actReportRegistryCardFullness_triggered(self):
        CReportRegistryCardFullness(self).exec_()


    @pyqtSignature('')
    def on_actReportDispansMO_1_1_triggered(self):
        CReportDispansMO_1_1(self).exec_()


    @pyqtSignature('')
    def on_actDailyJournalBeforeRecord2_triggered(self):
        CDailyJournalBeforeRecord2(self).exec_()


    @pyqtSignature('')
    def on_actUnfinishedEventsByDoctor_triggered(self):
        CUnfinishedEventsByDoctor(self).exec_()


    @pyqtSignature('')
    def on_actPreRecordClientsCard_triggered(self):
        CPreRecordClientsCard(self).exec_()


    @pyqtSignature('')
    def on_actClientTreatmentsStructureReport_triggered(self):
        CClientTreatmentsStructureReport(self).exec_()


    @pyqtSignature('')
    def on_actNumberResidentsAddress_triggered(self):
        CReportNumberResidentsAddress(self).exec_()


    @pyqtSignature('')
    def on_actPatientsCompositionReport_triggered(self):
        CStationaryPatientsComposition(self).exec_()


    @pyqtSignature('')
    def on_actPatientsCompositionByRegionReport_triggered(self):
        CStationaryPatientsCompositionByRegion(self).exec_()


    @pyqtSignature('')
    def on_actUnfinishedEventsByMes_triggered(self):
        CUnfinishedEventsByMes(self).exec_()


    @pyqtSignature('')
    def on_actExecutionMes_triggered(self):
        showCheckMesDescription(self)


    @pyqtSignature('')
    def on_actAnalyticsReportHospitalizedClients_triggered(self):
        CAnalyticsReportHospitalizedClients(self).exec_()


    @pyqtSignature('')
    def on_actAnaliticReportsPerson_triggered(self):
        CAnaliticReportsStationary(self).exec_()


    @pyqtSignature('')
    def on_actAnaliticReportsDeathStationary_triggered(self):
        CAnaliticReportsDeathStationary(self).exec_()


    @pyqtSignature('')
    def on_actAnaliticReportsAdditionalSurgery_triggered(self):
        CAnaliticReportsAdditionalSurgery(self).exec_()


    @pyqtSignature('')
    def on_actAnaliticReportsGeneralInfoSurgery_triggered(self):
        CAnaliticReportsGeneralInfoSurgery(self).exec_()


    @pyqtSignature('')
    def on_actAnaliticReportsSurgeryStationary_triggered(self):
        CAnaliticReportsSurgeryStationary(self).exec_()


    @pyqtSignature('')
    def on_actAnaliticReportsSurgery_triggered(self):
        CAnaliticReportsSurgery(self).exec_()


    @pyqtSignature('')
    def on_actSummaryOnServiceType_triggered(self):
        CSummaryOnServiceType(self).exec_()


    @pyqtSignature('')
    def on_actReportOnServiceType_triggered(self):
        CReportOnServiceType(self).exec_()


    @pyqtSignature('')
    def on_actAnalyticsReportIncomeAndLeavedClients_triggered(self):
        CAnalyticsReportIncomeAndLeavedClients(self).exec_()


    @pyqtSignature('')
    def on_actAnaliticReportsChildrenLeaved_triggered(self):
        CAnaliticReportsChildrenLeaved(self).exec_()


    @pyqtSignature('')
    def on_actStationaryTallySheetMoving_triggered(self):
        CStationaryTallySheetMoving(self).exec_()


    @pyqtSignature('')
    def on_actAnalyticsReporStationaryPlanning_triggered(self):
        CStationaryPlanMoving(self).exec_()


    @pyqtSignature('')
    def on_actReportF30_OLD_triggered(self):
        CReportF30(self).exec_()


    @pyqtSignature('')
    def on_actReportF30_SMP_triggered(self):
        CReportF30_SMP(self).exec_()


    @pyqtSignature('')
    def on_actReportF30_2100_triggered(self):
        CReportF30_2100(self).exec_()


    @pyqtSignature('')
    def on_actReportF30KK_2100_triggered(self):
        CReportF30KK_2100(self).exec_()


    @pyqtSignature('')
    def on_actReportF30_2110_triggered(self):
        CReportF30_2110(self).exec_()
    
    
    @pyqtSignature('')
    def on_actReportF30_2510_triggered(self):
        CReportF30_2510(self).exec_()
    

    @pyqtSignature('')
    def on_actReportF30_1050_triggered(self):
        CReportF30_1050(self).exec_()


    @pyqtSignature('')
    def on_actStationaryYearReport_triggered(self):
        CStationaryYearReport(self).exec_()


    @pyqtSignature('')
    def on_actDiagnosticYearReport_triggered(self):
        CDiagnosticYearReport(self).exec_()


    @pyqtSignature('')
    def on_actProfileYearReport_triggered(self):
        CProfileYearReport(self).exec_()


    @pyqtSignature('')
    def on_actReportEMD_triggered(self):
        CReportEMD(self).exec_()


    @pyqtSignature('')
    def on_actReportEventCasesVerification_triggered(self):
        CReportEventCasesVerification(self).exec_()


    @pyqtSignature('')
    def on_actReportPollAgeIsNotHindrance_triggered(self):
        CReportPollAgeIsNotHindrance(self).exec_()


    @pyqtSignature('')
    def on_actReportTreatedPatientsForComorbidities_triggered(self):
        CReportTreatedPatientsForComorbidities(self).exec_()


    @pyqtSignature('')
    def on_actReportTreatedPatientsForMajorDiseases_triggered(self):
        CReportTreatedPatientsForMajorDiseases(self).exec_()


    @pyqtSignature('')
    def on_actReportDiseasesResult_triggered(self):
        CReportDiseasesResult(self).exec_()


    @pyqtSignature('')
    def on_actReportAstheniaResults_triggered(self):
        CReportAstheniaResults(self).exec_()


    @pyqtSignature('')
    def on_actReportStomatF30_2700_triggered(self):
        CReportStomatF30_2700(self).exec_()


    @pyqtSignature('')
    def on_actReportStomatF30_2710_triggered(self):
        CReportStomatF30_2710(self).exec_()


    @pyqtSignature('')
    def on_actReportStomatF30_2700_2015_triggered(self):
        CReportStomatF30_2700_2015(self).exec_()


    @pyqtSignature('')
    def on_actReportF30M_triggered(self):
        CReportF30(self, True).exec_()


    @pyqtSignature('')
    def on_actReportF30M_2100_triggered(self):
        CReportF30_2100(self, True).exec_()


    @pyqtSignature('')
    def on_actReportF30M_2110_triggered(self):
        CReportF30_2110(self, True).exec_()


    @pyqtSignature('')
    def on_actReportF39_triggered(self):
        CReportF39(self).exec_()

    @pyqtSignature('')
    def on_actRepPos_triggered(self):
        CRepPos(self).exec_()

    @pyqtSignature('')
    def on_actRepPlatUsl_triggered(self):
        CRepPlatUsl(self).exec_()

    @pyqtSignature('')
    def on_actReportF39_3y_triggered(self):
        CReportStomatF39_3(self).exec_()


    @pyqtSignature('')
    def on_actReportStomatSummary_triggered(self):
        CReportStomatSummary(self).exec_()


    @pyqtSignature('')
    def on_actReportF39M_triggered(self):
        CReportF39(self, True).exec_()


    @pyqtSignature('')
    def on_actReportPGG_Ambulance_triggered(self):
        CReportPGG(self, type=1).exec_()


    @pyqtSignature('')
    def on_actReportPGG_Stomotology_triggered(self):
        CReportPGG(self, type=2).exec_()


    @pyqtSignature('')
    def on_actReportPGG_DHospital_triggered(self):
        CReportPGG(self, type=3).exec_()


    @pyqtSignature('')
    def on_actReportPGG_Hospital_triggered(self):
        CReportPGG(self, type=4).exec_()


    @pyqtSignature('')
    def on_actReportPGG_Emergency_triggered(self):
        CReportPGG(self, type=5).exec_()


    @pyqtSignature('')
    def on_actPersonVisits_triggered(self):
        CPersonVisits(self).exec_()


    @pyqtSignature('')
    def on_actReportPersonSickList_triggered(self):
        CReportPersonSickList(self).exec_()


    @pyqtSignature('')
    def on_actReportPolyclinicsOthersPersonList_triggered(self):
        CReportPolyclinicsOthersPersonList(self).exec_()


    @pyqtSignature('')
    def on_actReportBreachSA_triggered(self):
        CReportBreachSA(self).exec_()


    @pyqtSignature('')
    def on_actReportWorkloadOfMedicalStaff_triggered(self):
        CReportWorkloadOfMedicalStaff(self).exec_()


    @pyqtSignature('')
    def on_actReportEventList_triggered(self):
        CReportEventList(self).exec_()


    @pyqtSignature('')
    def on_actPrimaryClientList_triggered(self):
        CReportPrimaryClientList(self).exec_()


    @pyqtSignature('')
    def on_actStatReportDiseaseInPermille_triggered(self):
        CStatReportDiseaseInPermille(self).exec_()


    @pyqtSignature('')
    def on_actReportPersonSickListStationary_triggered(self):
        CReportPersonSickListStationary(self).exec_()


    @pyqtSignature('')
    def on_actReportSurgeryPlanDay_triggered(self):
        CReportSurgeryPlanDay(self).exec_()


    @pyqtSignature('')
    def on_actReportAcuteInfections_triggered(self):
        CReportAcuteInfections(self).exec_()


    @pyqtSignature('')
    def on_actReportDailyAcuteInfections_triggered(self):
        CReportDailyAcuteInfections(self).exec_()


    @pyqtSignature('')
    def on_actReportDailyAcuteInfectionsHospital_triggered(self):
        CReportDailyAcuteInfectionsHospital(self).exec_()


    @pyqtSignature('')
    def on_actReportMonthActions_triggered(self):
        CReportMonthActions(self).exec_()


    @pyqtSignature('')
    def on_actReportToYearActions_triggered(self):
        CReportYearActions(self).exec_()


    @pyqtSignature('')
    def on_actReportDirectionActions_triggered(self):
        CReportDirectionActions(self).exec_()


    @pyqtSignature('')
    def on_actReportBIRADS_triggered(self):
        CReportBIRADS(self).exec_()


    @pyqtSignature('')
    def on_actReportRoadMap_triggered(self):
        CReportRoadMap(self).exec_()


    @pyqtSignature('')
    def on_actUETActionsByActions_triggered(self):
        CReportUETActionByActions(self).exec_()


    @pyqtSignature('')
    def on_actUETActionsByPersons_triggered(self):
        CReportUETActionByPersons(self).exec_()


    @pyqtSignature('')
    def on_actReportActionsByOrgStructure_triggered(self):
        CReportActionsByOrgStructure(self).exec_()


    @pyqtSignature('')
    def on_actReportActionsByServiceType_triggered(self):
        CReportActionsByServiceType(self).exec_()


    @pyqtSignature('')
    def on_actReportClientSummary_triggered(self):
        CReportClientSummary(self).exec_()


    @pyqtSignature('')
    def on_actReportDoctorSummary_triggered(self):
        CReportDoctorSummary(self).exec_()


    @pyqtSignature('')
    def on_actReportDoctor_triggered(self):
        CReportDoctor(self).exec_()


    def on_actReportDoctorPreCalc_triggered(self):
        CReportDoctorPreCalc(self).exec_()


    def on_actReportMonitoredContingent_triggered(self):
        CReportServicesMonitoredContingent(self).exec_()


    @pyqtSignature('')
    def on_actReportOrgStructureSummary_triggered(self):
        CReportOrgStructureSummary(self).exec_()


    @pyqtSignature('')
    def on_actReportApproxDoneActions_triggered(self):
        CReportApproxDoneActions(self).exec_()


    @pyqtSignature('')
    def on_actReportAccountDoneActions_triggered(self):
        CReportAccountDoneActions(self).exec_()


    @pyqtSignature('')
    def on_actExternalIncomePaidServices_triggered(self):
        CExternalIncomePaidServices(self).exec_()


    @pyqtSignature('')
    def on_actReportSummaryOnAccounts_triggered(self):
        CReportSummaryOnAccounts(self).exec_()


    @pyqtSignature('')
    def on_actReportSummaryOnServices_triggered(self):
        CReportSummaryOnServices(self).exec_()


    @pyqtSignature('')
    def on_actReportPayers_triggered(self):
        CReportPayers(self).exec_()


    @pyqtSignature('')
    def on_actReportPayersWithFinance_triggered(self):
        CReportPayersWithFinance(self).exec_()


    @pyqtSignature('')
    def on_actReportClientActions_triggered(self):
        CReportClientActions(self).exec_()

    @pyqtSignature('')
    def on_actReportCost_triggered(self):
        CReportCost(self).exec_()

    @pyqtSignature('')
    def on_actReportF62_4000_triggered(self):
        CReportF62_4000(self).exec_()


#    @pyqtSignature('')
#    def on_actReportF62_7000_triggered(self):
#        CReportF62_7000(self).exec_()

    @pyqtSignature('')
    def on_actStatReportF65_1000_triggered(self):
        CStatReportF065_1000(self).exec_()


    @pyqtSignature('')
    def on_actStatReportF65_2000_triggered(self):
        CStatReportF065_2000(self).exec_()


    @pyqtSignature('')
    def on_actReportActions_triggered(self):
        CReportActions(self).exec_()


    @pyqtSignature('')
    def on_actUETService_triggered(self):
        CReportActionsServiceCutaway(self).exec_()


    @pyqtSignature('')
    def on_actReportOnPerson_triggered(self):
        CReportOnPerson(self).exec_()

    @pyqtSignature('')
    def on_actE1_triggered(self):
        CEconomicAnalisysE1Ex(self).exec_()

    @pyqtSignature('')
    def on_actE2_triggered(self):
        CEconomicAnalisysE2Ex(self).exec_()

    @pyqtSignature('')
    def on_actE4_triggered(self):
        CEconomicAnalisysE4Ex(self).exec_()

    @pyqtSignature('')
    def on_actVisitsServiceUET_triggered(self):
        CReportVisitsServiceCutaway(self).exec_()

    @pyqtSignature('')
    def on_actE6_triggered(self):
        CEconomicAnalisysE6Ex(self).exec_()

    @pyqtSignature('')
    def on_actE7_triggered(self):
        CEconomicAnalisysE7Ex(self).exec_()

    @pyqtSignature('')
    def on_actE8_triggered(self):
        CEconomicAnalisysE8Ex(self).exec_()

    @pyqtSignature('')
    def on_actE3_triggered(self):
        CEconomicAnalisysE3Ex(self).exec_()

    @pyqtSignature('')
    def on_actE5_triggered(self):
        CEconomicAnalisysE5Ex(self).exec_()

    @pyqtSignature('')
    def on_actFinanceSummaryByDoctorsOld_triggered(self):
        CFinanceSummaryByDoctorsExOld(self).exec_()

    @pyqtSignature('')
    def on_actE9_triggered(self):
        CEconomicAnalisysE9Ex(self).exec_()

    @pyqtSignature('')
    def on_actE11_triggered(self):
        CEconomicAnalisysE11Ex(self).exec_()

    @pyqtSignature('')
    def on_actE12_triggered(self):
        CEconomicAnalisysE12Ex(self).exec_()

    @pyqtSignature('')
    def on_actE13_triggered(self):
        CEconomicAnalisysE13Ex(self).exec_()

    @pyqtSignature('')
    def on_actE14_triggered(self):
        CEconomicAnalisysE14Ex(self).exec_()

    @pyqtSignature('')
    def on_actE15_triggered(self):
        CEconomicAnalisysE15Ex(self).exec_()

    @pyqtSignature('')
    def on_actE16_triggered(self):
        CEconomicAnalisysE16Ex(self).exec_()

    @pyqtSignature('')
    def on_actE17_triggered(self):
        CEconomicAnalisysE17Ex(self).exec_()

    @pyqtSignature('')
    def on_actForeignCitizens_triggered(self):
        CEconomicAnalisysForeignCitizensEx(self).exec_()

    @pyqtSignature('')
    def on_actOperationalMonitoring_triggered(self):
        CReportOperationalMonitoring(self).exec_()

    @pyqtSignature('')
    def on_actReportAFT_002_triggered(self):
        CReportAFT_002(self).exec_()

    @pyqtSignature('')
    def on_actReportAFT_Forecast12month_triggered(self):
        CReportAFT_Forecast12month(self).exec_()

    @pyqtSignature('')
    def on_actReportStomPersonSalary_triggered(self):
        CReportStomPersonSalaryEx(self).exec_()

    @pyqtSignature('')
    def on_actE19_triggered(self):
        CEconomicAnalisysE19Ex(self).exec_()

    @pyqtSignature('')
    def on_actE10_triggered(self):
        CEconomicAnalisysE10Ex(self).exec_()

    @pyqtSignature('')
    def on_actFinOtch_triggered(self):
        CFinOtchEx(self).exec_()

    @pyqtSignature('')
    def on_actFinReestr_triggered(self):
        CFinReestr(self).exec_()

    @pyqtSignature('')
    def on_actE23_triggered(self):
        CEconomicAnalisysE23Ex(self).exec_()

    @pyqtSignature('')
    def on_actE24_triggered(self):
        CEconomicAnalisysE24Ex(self).exec_()

    @pyqtSignature('')
    def on_actE26_triggered(self):
        CEconomicAnalisysE26Ex(self).exec_()

    @pyqtSignature('')
    def on_actECO_triggered(self):
        CEconomicAnalisysECOEx(self).exec_()

    @pyqtSignature('')
    def on_actP10_triggered(self):
        CEconomicAnalisysP10Ex(self).exec_()

    @pyqtSignature('')
    def on_actP11_triggered(self):
        CEconomicAnalisysP11Ex(self).exec_()

    @pyqtSignature('')
    def on_actFinOtd_triggered(self):
        CEconomicAnalisysFinOtdEx(self).exec_()

    @pyqtSignature('')
    def on_actRepReestrUsl_triggered(self):
        CRepReestrUslEx(self).exec_()

    @pyqtSignature('')
    def on_actFrmOS6_triggered(self):
        CFormOS6(self).exec_()

    @pyqtSignature('')
    def on_actInfoPrik_triggered(self):
        CInfoPrik(self).exec_()
    
    @pyqtSignature('')
    def on_actAddressFound_triggered(self):
        CAddressFound(self).exec_()

    @pyqtSignature('')
    def on_actAttachmentList_triggered(self):
        CAttachmentListReport(self).exec_()

    @pyqtSignature('')
    def on_actPersonParusCheck_triggered(self):
        CPersonParusCheckReport(self).exec_()

    @pyqtSignature('')
    def on_actDeattachCheck_triggered(self):
        CActDeattachCheckReport(self).exec_()

    @pyqtSignature('')
    def on_actAttachmentBySmo_triggered(self):
        CAttachmentBySmoReport(self).exec_()


    @pyqtSignature('')
    def on_actDeAttachmentList_triggered(self):
        CDeAttachmentListReport(self).exec_()

    @pyqtSignature('')
    def on_actRepForm30_triggered(self):
        CRepForm30(self).exec_()

    @pyqtSignature('')
    def on_actReportSummaryPos_triggered(self):
        CReportSummaryPosEx(self).exec_()

    @pyqtSignature('')
    def on_actFinanceSummaryByDoctors_triggered(self):
        CFinanceSummaryByDoctorsEx(self).exec_()


    @pyqtSignature('')
    def on_actVisitByPurposeEvents_triggered(self):
        CReportVisitByPurposeEvents(self).exec_()


    @pyqtSignature('')
    def on_actReconciliationMutualSettlements_triggered(self):
        CActReconciliationMutualSettlements(self).exec_()


    @pyqtSignature('')
    def on_actFinanceSummaryByServices_triggered(self):
        CFinanceSummaryByServicesEx(self).exec_()


    @pyqtSignature('')
    def on_actFinanceReportByAidProfileAndSocStatus_triggered(self):
        CFinanceReportByAidProfileAndSocStatus(self).exec_()

    @pyqtSignature('')
    def on_actReportPaidServices_triggered(self):
        CReportPaidServices(self).exec_()

    @pyqtSignature('')
    def on_actFinanceSummaryByOrgStructures_triggered(self):
        CFinanceSummaryByOrgStructuresEx(self).exec_()


    @pyqtSignature('')
    def on_actReportPaidServices_triggered(self):
        CReportPaidServices(self).exec_()


    @pyqtSignature('')
    def on_actFinanceSumByServicesExpenses_triggered(self):
        CFinanceSumByServicesExpensesEx(self).exec_()


    @pyqtSignature('')
    def on_actFinanceSummaryByRejections_triggered(self):
        CFinanceSummaryByRejectionsEx(self).exec_()


    @pyqtSignature('')
    def on_actReportDailyCash_triggered(self):
        CReportDailyCash(self).exec_()


    @pyqtSignature('')
    def on_actReportInsuredMedicalCare_triggered(self):
        CReportInsuredMedicalCare(self).exec_()


    @pyqtSignature('')
    def on_actReportClients_triggered(self):
        CReportClients(self).exec_()


    @pyqtSignature('')
    def on_actReportTreatments_triggered(self):
        CReportTreatments(self).exec_()


    @pyqtSignature('')
    def on_actEventResultSurvey_triggered(self):
        CEventResultSurvey(self).exec_()


    @pyqtSignature('')
    def on_actEventResultList_triggered(self):
        CReportEventResultList(self).exec_()


    @pyqtSignature('')
    def on_actReportSocStatus_triggered(self):
        CSocStatus(self).exec_()

    @pyqtSignature('')
    def on_actSickRateSurvey_triggered(self):
        CSickRateSurvey(self).exec_()


    @pyqtSignature('')
    def on_actSickRateAbort_triggered(self):
        CSickRateAbort(self).exec_()


    @pyqtSignature('')
    def on_actSickRateAbort_1000_triggered(self):
        CSickRateAbort_1000(self).exec_()


    @pyqtSignature('')
    def on_actSickRateAbort_2000_triggered(self):
        CSickRateAbort_2000(self).exec_()


    @pyqtSignature('')
    def on_actFactorRateSurvey_triggered(self):
        CFactorRateSurvey(self).exec_()


    @pyqtSignature('')
    def on_actStatReportF12Children_triggered(self):
        CStatReportF12Children(self).exec_()


    @pyqtSignature('')
    def on_actStatReportF12Children0_14_2022_triggered(self):
        CStatReportF12Children0_14_2022(self).exec_()


    @pyqtSignature('')
    def on_actStatReportF12Children0_1_2022_triggered(self):
        CStatReportF12Children0_1_2022(self).exec_()


    @pyqtSignature('')
    def on_actStatReportF12Teenagers_triggered(self):
        CStatReportF12Teenagers(self).exec_()


    @pyqtSignature('')
    def on_actStatReportF12Teenagers_2022_triggered(self):
        CStatReportF12Teenagers_2022(self).exec_()


    @pyqtSignature('')
    def on_actStatReportF12Adults_triggered(self):
        CStatReportF12Adults(self).exec_()


    @pyqtSignature('')
    def on_actStatReportF12Adults_2022_triggered(self):
        CStatReportF12Adults_2022(self).exec_()


    @pyqtSignature('')
    def on_actStatReportF12Seniors_triggered(self):
        CStatReportF12Seniors(self).exec_()


    @pyqtSignature('')
    def on_actStatReportF12Seniors_2022_triggered(self):
        CStatReportF12Seniors_2022(self).exec_()


    @pyqtSignature('')
    def on_actStatReportF12Able_triggered(self):
        CStatReportF12Able(self).exec_()


    @pyqtSignature('')
    def on_actStatReportF12Able_2022_triggered(self):
        CStatReportF12Able_2022(self).exec_()



    @pyqtSignature('')
    def on_actStatReportF12Inset2008_triggered(self):
        CStatReportF12Inset2008(self).exec_()


    @pyqtSignature('')
    def on_actStatReportF12Students_2025_triggered(self):
        CStatReportF12Students_2025(self).exec_()


    @pyqtSignature('')
    def on_actStatReport_F57_triggered(self):
        CStatReportF57(self).exec_()


    @pyqtSignature('')
    def on_actStatReport_F57_1000_triggered(self):
        CStatReportF57_1000(self).exec_()


    @pyqtSignature('')
    def on_actStatReport_F57_2000_triggered(self):
        CStatReportF57_2000(self).exec_()


    @pyqtSignature('')
    def on_actStatReport_F57_3000_triggered(self):
        CStatReportF57_3000(self).exec_()


    @pyqtSignature('')
    def on_actStatReport_F57_3500_triggered(self):
        CStatReportF57_3500(self).exec_()


    @pyqtSignature('')
    def on_actStatReportF63_triggered(self):
        CStatReportF63(self).exec_()

    @pyqtSignature('')
    def on_actRep060Y_triggered(self):
        CRep060Y(self).exec_()

    @pyqtSignature('')
    def on_actStatReportF71_triggered(self):
        CStatReportF71(self).exec_()


    @pyqtSignature('')
    def on_actStatReportF9_2000_triggered(self):
        CStatReportF9_2000(self).exec_()


    @pyqtSignature('')
    def on_actStatReportF9_2001_triggered(self):
        CStatReportF9_2001(self).exec_()


    @pyqtSignature('')
    def on_actStatReportF9_2003_triggered(self):
        CStatReportF9_2003(self).exec_()


    @pyqtSignature('')
    def on_actStatReportF9_2005_triggered(self):
        CStatReportF9_2005(self).exec_()


    @pyqtSignature('')
    def on_actStatReportF9_2006_triggered(self):
        CStatReportF9_2006(self).exec_()


    @pyqtSignature('')
    def on_actDispObservationList_triggered(self):
        CDispObservationList(self).exec_()


    @pyqtSignature('')
    def on_actDispObservationSurvey_triggered(self):
        CDispObservationSurvey(self).exec_()


    @pyqtSignature('')
    def on_actStatReportF12Clients_triggered(self):
        CStatReportF12Clients(self).exec_()


    @pyqtSignature('')
    def on_actDiagnosisDispansPlanedList_triggered(self):
        CDiagnosisDispansPlanedListReport(self).exec_()


    @pyqtSignature('')
    def on_actDiagnosisDispansNoVisit_triggered(self):
        CDiagnosisDispansNoVisitReport(self).exec_()


    @pyqtSignature('')
    def on_actDispansList_triggered(self):
        CDispansListReport(self).exec_()


    @pyqtSignature('')
    def on_actDispObservationPriorityListReport_triggered(self):
        CDispObservationPriorityListReport(self).exec_()


    @pyqtSignature('')
    def on_actDispReport_triggered(self):
        CDispReport(self).exec_()

    @pyqtSignature('')
    def on_actReportSummaryClientNotApply_triggered(self):
        CReportSummaryClientNotApply(self).exec_()


    @pyqtSignature('')
    def on_actOdliServ_triggered(self):
        DialogOdli(self).exec_()


    @pyqtSignature('')
    def on_actPeopleOfCancer_triggered(self):
        CPeopleOfCancer(self).exec_()

    @pyqtSignature('')
    def on_actPeopleWithDiseasesCirculatorySystem_triggered(self):
        CPeopleWithDiseasesCirculatorySystem(self).exec_()

    @pyqtSignature('')
    def on_actRepNoProfsChild_triggered(self):
        CNoProfsChild(self).exec_()

    @pyqtSignature('')
    def on_actReportHospDir_triggered(self):
        CHospDir(self).exec_()

    @pyqtSignature('')
    def on_actTempInvalidList_triggered(self):
        CTempInvalidList(self).exec_()


    @pyqtSignature('')
    def on_actTempInvalidSurvey_triggered(self):
        CTempInvalidSurvey(self).exec_()


    @pyqtSignature('')
    def on_actTempInvalidF16_triggered(self):
        CTempInvalidF16(self).exec_()


    @pyqtSignature('')
    def on_actTempInvalidF16_2022_triggered(self):
        CTempInvalidF16_2022(self).exec_()


    @pyqtSignature('')
    def on_actTempInvalidBookF036_triggered(self):
        CTempInvalidBookF036(self).exec_()


    @pyqtSignature('')
    def on_actTempInvalidBookF035_triggered(self):
        CTempInvalidBookF035(self).exec_()


    @pyqtSignature('')
    def on_actTempInvalidExpert_triggered(self):
        CTempInvalidExpert(self).exec_()


    @pyqtSignature('')
    def on_actDeathList_triggered(self):
        CDeathList(self).exec_()


    @pyqtSignature('')
    def on_actDeathReport_triggered(self):
        CDeathReport(self).exec_()


    @pyqtSignature('')
    def on_actDeathReportByZones_triggered(self):
        CDeathReportByZones(self).exec_()


    @pyqtSignature('')
    def on_actDetailedDeathReportByZones_triggered(self):
        CDetailedDeathReportByZones(self).exec_()


    @pyqtSignature('')
    def on_actDeathSurvey_triggered(self):
        CDeathSurvey(self).exec_()


    @pyqtSignature('')
    def on_actWorkload_triggered(self):
        CWorkload(self).exec_()


    @pyqtSignature('')
    def on_actAttachedContingent_triggered(self):
        CAttachedContingent(self).exec_()

    @pyqtSignature('')
    def on_actForm13dChildPopulation_triggered(self):
        CForm13dChildPopulation(self).exec_()

    @pyqtSignature('')
    def on_actForm25dNumberChildrenByAgeAndSocStatus_triggered(self):
        CForm25dNumberChildrenByAgeAndSocStatus(self).exec_()

    @pyqtSignature('')
    def on_actFerzlAttach_triggered(self):
        CReportFerlzAttachments(self).exec_()

    @pyqtSignature('')
    def on_actReportOnkoByStages_triggered(self):
        CReportOnkoByStages(self).exec_()


    @pyqtSignature('')
    def on_actReportDrugAtitumorCure_triggered(self):
        CReportDrugAtitumorCure(self).exec_()

        
    @pyqtSignature('')
    def on_actBySMOContingent_triggered(self):
        CBySMOContingent(self).exec_()

    @pyqtSignature('')
    def on_actCountByOms_triggered(self):
        CCountByOms(self).exec_()

    @pyqtSignature('')
    def on_actAttachingMotion_triggered(self):
        CReportAttachingMotion(self).exec_()


    @pyqtSignature('')
    def on_actReportSMOClients_triggered(self):
        CReportSMOClients(self).exec_()


    @pyqtSignature('')
    def on_actNumberInsuredPersonsSMO_triggered(self):
        CReportNumberInsuredPersonsSMO(self).exec_()


    @pyqtSignature('')
    def on_actForma007Moving_triggered(self):
        CStationaryF007Moving(self).exec_()
    
    
    @pyqtSignature('')
    def on_actForma007_530Moving_triggered(self):
        CStationaryF007_530Moving(self).exec_()


    @pyqtSignature('')
    def on_actForm7_2000_triggered(self):
        CReportForm7_2000(self).exec_()


    @pyqtSignature('')
    def on_actMovingAndBedsReport_triggered(self):
        CReportMovingAndBeds(self).exec_()


    @pyqtSignature('')
    def on_actStationaryReportForMIAC_triggered(self):
        CStationaryReportForMIAC(self).exec_()

    @pyqtSignature('')
    def on_actSpec_Journal_triggered(self):
        CSpec_Journal(self).exec_()

    @pyqtSignature('')
    def on_actStationaryReportForMIACInHard_triggered(self):
        CStationaryReportForMIACHard(self).exec_()


    @pyqtSignature('')
    def on_actReportsBeingInStationary_triggered(self):
        CReportsBeingInStationary(self).exec_()


    @pyqtSignature('')
    def on_actReportLengthOfStayInHospital_triggered(self):
        CReportLengthOfStayInHospital(self).exec_()


    @pyqtSignature('')
    def on_actDeliveryChannelsReport_triggered(self):
        CDeliveryChannelsReport(self).exec_()


    @pyqtSignature('')
    def on_actDiseasesAnalysisReport_triggered(self):
        CDiseasesAnalysisReport(self).exec_()


    @pyqtSignature('')
    def on_actLengthOfStayReport_triggered(self):
        CLengthOfStayReport(self).exec_()


    @pyqtSignature('')
    def on_actForma007ClientList_triggered(self):
        CStationaryF007ClientList(self).exec_()
    
    
    @pyqtSignature('')
    def on_actForma007_530ClientList_triggered(self):
        CStationaryF007_530ClientList(self).exec_()


    @pyqtSignature('')
    def on_actForma007DSMoving_triggered(self):
        CStationaryF007DSMoving(self).exec_()


    @pyqtSignature('')
    def on_actForma007DSClientList_triggered(self):
        CStationaryF007DSClientList(self).exec_()


    @pyqtSignature('')
    def on_actFormaF016_02_triggered(self):
        CStationaryF016_02(self).exec_()


    @pyqtSignature('')
    def on_actForma016_530n_triggered(self):
        CStationaryF016_02_530n(self).exec_()


    # @pyqtSignature('')
    # def on_actRepStacKoy_triggered(self):
    #     CReportStacKoyka(self).exec_()


    @pyqtSignature('')
    def on_actSvedVipis_triggered(self):
        CSvedVipis(self).exec_()

    @pyqtSignature('')
    def on_actFormaF016_triggered(self):
        CStationaryF016(self).exec_()

    @pyqtSignature('')
    def on_report_analitic_referrslMSE_triggered(self):
        CAnalitic_referralMSE(self).exec_()

    @pyqtSignature('')
    def on_actFormaF016ForPeriod_triggered(self):
        CStationaryF016ForPeriod(self).exec_()


    @pyqtSignature('')
    def on_actStationaryF30Moving_triggered(self):
        CStationaryF30Moving(self).exec_()


    @pyqtSignature('')
    def on_actStationaryF30_3101_triggered(self):
        CStationaryF30_3101(self).exec_()


    @pyqtSignature('')
    def on_actStationaryF30Moving_KK_triggered(self):
        CStationaryF30Moving_KK(self).exec_()


    @pyqtSignature('')
    def on_actStationaryF036_2300_triggered(self):
        CStationaryF036_2300(self).exec_()


    @pyqtSignature('')
    def on_actStationaryF36_PL_triggered(self):
        CStationaryF36_PL(self).exec_()


    @pyqtSignature('')
    def on_actEmergencySurgicalCare7Nosologies_triggered(self):
        CEmergencySurgicalCare7Nosologies(self).exec_()


    @pyqtSignature('')
    def on_actFormaAdultF142000_triggered(self):
        CStationaryAdultF142000(self).exec_()


    @pyqtSignature('')
    def on_actFormaAdultNoSeniorF142000_triggered(self):
        CStationaryAdultNoSeniorF142000(self).exec_()


    @pyqtSignature('')
    def on_actFormaChildrenF142000_triggered(self):
        CStationaryChildrenF142000(self).exec_()


    @pyqtSignature('')
    def on_actFormaSeniorF142000_triggered(self):
        CStationarySeniorF142000(self).exec_()


    @pyqtSignature('')
    def on_actStationaryF142100_triggered(self):
        CStationaryF142100(self).exec_()


    @pyqtSignature('')
    def on_actStationaryF14_4300_4301_4302_triggered(self):
        CStationaryF14_4300_4301_4302(self).exec_()


    @pyqtSignature('')
    def on_actFormaF0143000_triggered(self):
        CStationaryF143000(self).exec_()


    @pyqtSignature('')
    def on_actFormaF0144000_triggered(self):
        CStationaryF144000(self).exec_()


    @pyqtSignature('')
    def on_actFormaF0144001_triggered(self):
        CStationaryF144001(self).exec_()


    @pyqtSignature('')
    def on_actFormaF0144001A_triggered(self):
        CStationaryF144001A(self).exec_()


    @pyqtSignature('')
    def on_actFormaF0144002_triggered(self):
        CStationaryF144002(self).exec_()


    @pyqtSignature('')
    def on_actFormaF0144100_triggered(self):
        CStationaryF144100(self).exec_()


    @pyqtSignature('')
    def on_actFormaF0144200_triggered(self):
        CStationaryF144200(self).exec_()


    @pyqtSignature('')
    def on_actFormaF0144201_triggered(self):
        CStationaryF144201(self).exec_()


    @pyqtSignature('')
    def on_actFormaF0144202_triggered(self):
        CStationaryF144202(self).exec_()


    @pyqtSignature('')
    def on_actFormaF0144400_triggered(self):
        CStationaryF144400(self).exec_()


    @pyqtSignature('')
    def on_actFormaF0144000_2021_triggered(self):
        CStationaryF0144000_2021(self).exec_()


    @pyqtSignature('')
    def on_actFormaF0144001_2021_triggered(self):
        CStationaryF144001_2021(self).exec_()


    @pyqtSignature('')
    def on_actFormaF0144001A_2021_triggered(self):
        CStationaryF144001A_2021(self).exec_()


    @pyqtSignature('')
    def on_actFormaF0144002_2021_triggered(self):
        CStationaryF144002_2021(self).exec_()


    @pyqtSignature('')
    def on_actFormaF0144100_2021_triggered(self):
        CStationaryF144100_2021(self).exec_()


    @pyqtSignature('')
    def on_actFormaF0144110_2021_triggered(self):
        CStationaryF144110_2021(self).exec_()

    @pyqtSignature('')
    def on_actFormaF0144200_2021_triggered(self):
        CStationaryF144200_2021(self).exec_()


    @pyqtSignature('')
    def on_actFormaF0144201_2021_triggered(self):
        CStationaryF144201_2021(self).exec_()


    @pyqtSignature('')
    def on_actFormaF0144201_2022_triggered(self):
        CStationaryF144201_2022(self).exec_()


    @pyqtSignature('')
    def on_actFormaF014_2910_2022_triggered(self):
        CStationaryF014_2910_2022(self).exec_()


    @pyqtSignature('')
    def on_actStationaryF14_4300_4301_4302_2021_triggered(self):
        CStationaryF14_4300_4301_4302_2021(self).exec_()


    @pyqtSignature('')
    def on_actFormaF0144400_2021_triggered(self):
        CStationaryF144400_2021(self).exec_()

    @pyqtSignature('')
    def on_actReportPatientSchoolJournal_triggered(self):
        CactReportPatientSchoolJournal(self).exec_()

    @pyqtSignature('')
    def on_actReportMonthlySchoolJournal_triggered(self):
        CactReportMonthlySchoolJournal(self).exec_()


    @pyqtSignature('')
    def on_actStationaryF14KK2000Adult_triggered(self):
        CStationaryF14KK2000Adult(self).exec_()


    @pyqtSignature('')
    def on_actStationaryF14KK2000Senior_triggered(self):
        CStationaryF14KK2000Senior(self).exec_()


    @pyqtSignature('')
    def on_actStationaryF14KK2000Children_triggered(self):
        CStationaryF14KK2000Children(self).exec_()


    @pyqtSignature('')
    def on_actStationaryF14KK4000_triggered(self):
        CStationaryF14KK4000(self).exec_()


    @pyqtSignature('')
    def on_actStationaryF14KK4001_triggered(self):
        CStationaryF14KK4001(self).exec_()


    @pyqtSignature('')
    def on_actStationaryF14KK4100_triggered(self):
        CStationaryF14KK4100(self).exec_()


    @pyqtSignature('')
    def on_actOne2015Forma14DC_triggered(self):
        CStationaryOne_2015F14DC(self).exec_()


    @pyqtSignature('')
    def on_actTwoAdult_2015Forma14DC_triggered(self):
        CStationaryTwoAdult_2015F14DC(self).exec_()


    @pyqtSignature('')
    def on_actTwoChildren_2015Forma14DC_triggered(self):
        CStationaryTwoChildren_2015F14DC(self).exec_()


    @pyqtSignature('')
    def on_act14dskk1000_triggered(self):
        CReportDs14kk1000(self).exec_()


    @pyqtSignature('')
    def on_act14dskk2000_triggered(self):
        CReportDs14kk2000(self).exec_()


    @pyqtSignature('')
    def on_act14dskk3000_triggered(self):
        CReportDs14kk3000(self).exec_()


    @pyqtSignature('')
    def on_act14dskk4000_triggered(self):
        CReportDs14kk4000(self).exec_()


    @pyqtSignature('')
    def on_actOneForma14DC_triggered(self):
        CStationaryOneF14DC(self).exec_()


    @pyqtSignature('')
    def on_actOneHospitalF14DC_triggered(self):
        CStationaryOneHospitalF14DC(self).exec_()


    @pyqtSignature('')
    def on_actMESHospitalF14DC_triggered(self):
        CStationaryMESHospitalF14DC(self).exec_()


    @pyqtSignature('')
    def on_actMESHouseF14DC_triggered(self):
        CStationaryMESHouseF14DC(self).exec_()


    @pyqtSignature('')
    def on_actMESPolyclinicF14DC_triggered(self):
        CStationaryMESPolyclinicF14DC(self).exec_()


    @pyqtSignature('')
    def on_actMESOneF14DC_triggered(self):
        CStationaryMESOneF14DC(self).exec_()


    @pyqtSignature('')
    def on_actOnePolyclinicF14DC_triggered(self):
        CStationaryOnePolyclinicF14DC(self).exec_()


    @pyqtSignature('')
    def on_actOneHouseF14DC_triggered(self):
        CStationaryOneHouseF14DC(self).exec_()


    @pyqtSignature('')
    def on_actEmergency2000_triggered(self):
        CReportEmergencyF402000(self).exec_()


    @pyqtSignature('')
    def on_actEmergency2120_triggered(self):
        CReportEmergencyF302120(self).exec_()


    @pyqtSignature('')
    def on_actEmergency2001_triggered(self):
        CReportEmergencyF402001(self).exec_()


    @pyqtSignature('')
    def on_actEmergency2350_triggered(self):
        CReportEmergencyF302350(self).exec_()


    @pyqtSignature('')
    def on_actEmergency2100_triggered(self):
        CReportEmergencyF402100(self).exec_()


    @pyqtSignature('')
    def on_actEmergency2500_triggered(self):
        CReportEmergencyF402500(self).exec_()


    @pyqtSignature('')
    def on_actEmergencyF40TimeIndicators_triggered(self):
        CReportEmergencyF40TimeIndicators(self).exec_()


    @pyqtSignature('')
    def on_actEmergencyAdditionally_triggered(self):
        CReportEmergencyAdditionally(self).exec_()


    @pyqtSignature('')
    def on_actEmergencyTalonSignal_triggered(self):
        CReportEmergencyTalonSignal(self).exec_()


    @pyqtSignature('')
    def on_actEmergencySize_triggered(self):
        CEmergencySizeReport(self).exec_()


    @pyqtSignature('')
    def on_actReportEmergencyCallList_triggered(self):
        CReportEmergencyCallList(self).exec_()

    @pyqtSignature('')
    def on_actReportSMPDockList_triggered(self):
        CReportSMPDockList(self).exec_()


    @pyqtSignature('')
    def on_actTwoAdultForma14DC_triggered(self):
        CStationaryTwoAdultF14DC(self).exec_()


    @pyqtSignature('')
    def on_actTwoAdultHospitalF14DC_triggered(self):
        CStationaryTwoAdultHospitalF14DC(self).exec_()


    @pyqtSignature('')
    def on_actTwoAdultPoliclinicF14DC_triggered(self):
        CStationaryTwoAdultPoliclinicF14DC(self).exec_()


    @pyqtSignature('')
    def on_actTwoAdultHouseF14DC_triggered(self):
        CStationaryTwoAdultHouseF14DC(self).exec_()


    @pyqtSignature('')
    def on_actTwoChildrenForma14DC_triggered(self):
        CStationaryTwoChildrenF14DC(self).exec_()


    @pyqtSignature('')
    def on_actTwoChildrenHospitalF14DC_triggered(self):
        CStationaryTwoChildrenHospitalF14DC(self).exec_()


    @pyqtSignature('')
    def on_actTwoChildrenPoliclinicF14DC_triggered(self):
        CStationaryTwoChildrenPoliclinicF14DC(self).exec_()


    @pyqtSignature('')
    def on_actTwoChildrenHouseF14DC_triggered(self):
        CStationaryTwoChildrenHouseF14DC(self).exec_()


    @pyqtSignature('')
    def on_actStationaryTypePaymentF14DC_triggered(self):
        CStationaryTypePaymentF14DC(self).exec_()


    @pyqtSignature('')
    def on_actPopulationStructure_triggered(self):
        CPopulationStructure(self).exec_()


    @pyqtSignature('')
    def on_actSpendingToClients_triggered(self):
        CSpendingToClients(self).exec_()


    @pyqtSignature('')
    def on_actReportClientNomenclaturePlan_triggered(self):
        CReportClientNomenclaturePlan(self).exec_()


    @pyqtSignature('')
    def on_actReportPassportT1000_triggered(self):
        CReportPassportT1000(self).exec_()


    @pyqtSignature('')
    def on_actReportPassportT1100_triggered(self):
        CReportPassportT1100(self).exec_()


    @pyqtSignature('')
    def on_actReportPassportT1200_triggered(self):
        CReportPassportT1200(self).exec_()

    @pyqtSignature('')
    def on_actHealthCenterForm68_triggered(self):
        CHealthCenterForm68(self).exec_()

    @pyqtSignature('')
    def on_actHealthCenterAnaliz_triggered(self):
        CHealthCenterAnaliz(self).exec_()


    @pyqtSignature('')
    def on_actGenRep_triggered(self):
        genRep = forceString(QtGui.qApp.preferences.appPrefs['extGenRep'])
        if genRep:
            prg=QtGui.qApp.execProgram(genRep)
            if not prg[0]:
                QtGui.QMessageBox.critical(self,
                                       u'Внимание!',
                                       u'Не удалось запустить "%s"' % genRep,
                                       QtGui.QMessageBox.Close)
            if prg[2]:
                QtGui.QMessageBox.critical(self,
                                       u'Внимание!',
                                       u'Ошибка при выполнении "%s"' % genRep,
                                       QtGui.QMessageBox.Close)
        else:
            QtGui.QMessageBox.critical(self,
                                    u'Ошибка!',
                                    u'Не указан исполнимый файл генератора отчетов\n'+
                                    u'Смотрите пункт меню "Настройки.Умолчания", закладка "Прочие настройки",\n'+
                                    u'строка "Внешний генератор отчетов".',
                                    QtGui.QMessageBox.Close)


    @pyqtSignature('')
    def on_actAreas_triggered(self):
        pass


    @pyqtSignature('')
    def on_actKLADR_triggered(self):
        pass


    @pyqtSignature('')
    def on_actMKB_triggered(self):
        CMKBList(self).exec_()


    @pyqtSignature('')
    def on_actMKBSubclass_triggered(self):
        CMKBSubclass(self).exec_()


    @pyqtSignature('')
    def on_actMKBExSubclass_triggered(self):
        CMKBExSubclass(self).exec_()


    @pyqtSignature('')
    def on_actMKBMorphology_triggered(self):
        CRBMKBMorphologyList(self).exec_()


    @pyqtSignature('')
    def on_actTumor_triggered(self):
        CRBTumorList(self).exec_()


    @pyqtSignature('')
    def on_actTNMphase_triggered(self):
        CRBTNMPhaseList(self).exec_()


    @pyqtSignature('')
    def on_actNodus_triggered(self):
        CRBNodusList(self).exec_()


    @pyqtSignature('')
    def on_actMetastasis_triggered(self):
        CRBMetastasisList(self).exec_()


    @pyqtSignature('')
    def on_actBank_triggered(self):
        CBanksList(self).exec_()


    @pyqtSignature('')
    def on_actContract_triggered(self):
        CContractsList(self).exec_()


    @pyqtSignature('')
    def on_actOrganisation_triggered(self):
        COrgsList(self).exec_()


    @pyqtSignature('')
    def on_actActionPropertyTemplate_triggered(self):
        CActionPropertyTemplateList(self).exec_()


    @pyqtSignature('')
    def on_actRBActionShedule_triggered(self):
        CRBActionSheduleList(self).exec_()


    @pyqtSignature('')
    def on_actActionType_triggered(self):
        CActionTypeList(self).exec_()


    @pyqtSignature('')
    def on_actQuotaType_triggered(self):
        CQuotaTypeList(self).exec_()


    @pyqtSignature('')
    def on_actRBAgreementType_triggered(self):
        CRBAgreementTypeList(self).exec_()


    @pyqtSignature('')
    def on_actBlankType_triggered(self):
        CBlankTypeList(self).exec_()


    @pyqtSignature('')
    def on_actRBMedicalBoardExpertiseCharacter_triggered(self):
        CRBMedicalBoardExpertiseCharacter(self).exec_()


    @pyqtSignature('')
    def on_actRBMedicalBoardExpertiseKind_triggered(self):
        CRBMedicalBoardExpertiseKind(self).exec_()


    @pyqtSignature('')
    def on_actRBMedicalBoardExpertiseObject_triggered(self):
        CRBMedicalBoardExpertiseObject(self).exec_()


    @pyqtSignature('')
    def on_actRBMedicalBoardExpertiseArgument_triggered(self):
        CRBMedicalBoardExpertiseArgument(self).exec_()


    @pyqtSignature('')
    def on_actCureMethod_triggered(self):
        CRBCureMethod(self).exec_()


    @pyqtSignature('')
    def on_actCureType_triggered(self):
        CRBCureType(self).exec_()


    @pyqtSignature('')
    def on_actPatientModel_triggered(self):
        CRBPatientModel(self).exec_()


    @pyqtSignature('')
    def on_actActionTemplate_triggered(self):
        CActionTemplateList(self).exec_()


    @pyqtSignature('')
    def on_actEventType_triggered(self):
        CEventTypeList(self).exec_()


    @pyqtSignature('')
    def on_actN3QmExtraDataDef_triggered(self):
        CExtraDataDefList(self).exec_()


    @pyqtSignature('')
    def on_actN3SRSUser_triggered(self):
        CSRSUserList(self).exec_()


    @pyqtSignature('')
    def on_actPersonal_triggered(self):
        CPersonList(self).exec_()


    @pyqtSignature('')
    def on_actSignOrgSert_triggered(self):
        CActionFileAttach(self).exec_()


    @pyqtSignature('')
    def on_actIdentityPatientService_triggered(self):
        CIdentityPatientServiceDialog(self).exec_()


    @pyqtSignature('')
    def on_actAttachOnlineService_triggered(self):
        CAttachOnlineServiceDialog(self).exec_()

    @pyqtSignature('')
    def on_actStreetCorrect_triggered(self):
        CCorrectorOutdatedStreets(self).exec_()

    @pyqtSignature('')
    def on_actUO_triggered(self):
        dlg = CMedServiceProfilesDialog(self)
        dlg.exec_()
    
    @pyqtSignature('')
    def on_actPersonSubstitutionService_triggered(self):
        CPersonSubstitutionDialog(self).exec_()


    @pyqtSignature('')
    def on_actPlanningHospitalActivity_triggered(self):
        CRBPlanningHospitalActivityList(self).exec_()


    @pyqtSignature('')
    def on_actPlanningOrgStructureHospitalBedProfile_triggered(self):
        CPlanningHospitalBedProfileDialog(self).exec_()


    @pyqtSignature('')
    def on_actPlanningHealthResortActivity_triggered(self):
        CRBPlanningHealthResortActivity(self).exec_()


    @pyqtSignature('')
    def on_actPostOnAppointment_triggered(self):
        CPostOnAppointmentList(self).exec_()


    @pyqtSignature('')
    def on_actOrgStructure_triggered(self):
        COrgStructureList(self).exec_()


    @pyqtSignature('')
    def on_actRBAccountExportFormat_triggered(self):
        CRBAccountExportFormatList(self).exec_()


    @pyqtSignature('')
    def on_actRBAccountingSystem_triggered(self):
        CRBAccountingSystemList(self).exec_()


    @pyqtSignature('')
    def on_actRBCounter_triggered(self):
        CRBCounterList(self).exec_()


    @pyqtSignature('')
    def on_actRBAttachType_triggered(self):
        CRBAttachTypeList(self).exec_()


    @pyqtSignature('')
    def on_actRBContactType_triggered(self):
        CRBContactTypeList(self).exec_()


    @pyqtSignature('')
    def on_actRBContractAttributeType_triggered(self):
        CRBContractAttributeTypeList(self).exec_()


    @pyqtSignature('')
    def on_actRBClientWorkPost_triggered(self):
        CRBClientWorkPostList(self).exec_()


    @pyqtSignature('')
    def on_actRBRiskFactor_triggered(self):
        CRBRiskFactor(self).exec_()


    @pyqtSignature('')
    def on_actRBContractCoefficientType_triggered(self):
        CRBContractCoefficientTypeList(self).exec_()


    @pyqtSignature('')
    def on_actRBDiagnosisType_triggered(self):
        CRBDiagnosisTypeList(self).exec_()


    @pyqtSignature('')
    def on_actRBDiseaseCharacter_triggered(self):
        CRBDiseaseCharacterList(self).exec_()


    @pyqtSignature('')
    def on_actRBEmergencyBrigade_triggered(self):
        CRBEmergencyBrigadeList(self).exec_()


    @pyqtSignature('')
    def on_actRBEmergencyCauseCall_triggered(self):
        CRBEmergencyCauseCallList(self).exec_()


    @pyqtSignature('')
    def on_actRBEmergencyTransferredTransportation_triggered(self):
        CRBEmergencyTransferredTransportationList(self).exec_()


    @pyqtSignature('')
    def on_actRBEmergencyPlaceReceptionCall_triggered(self):
        CRBEmergencyPlaceReceptionCallList(self).exec_()


    @pyqtSignature('')
    def on_actRBEmergencyReceivedCall_triggered(self):
        CRBEmergencyReceivedCallList(self).exec_()


    @pyqtSignature('')
    def on_actRBEmergencyReasondDelays_triggered(self):
        CRBEmergencyReasondDelaysList(self).exec_()


    @pyqtSignature('')
    def on_actRBEmergencyResult_triggered(self):
        CRBEmergencyResultList(self).exec_()


    @pyqtSignature('')
    def on_actRBEmergencyAccident_triggered(self):
        CRBEmergencyAccidentList(self).exec_()


    @pyqtSignature('')
    def on_actRBEmergencyDeath_triggered(self):
        CRBEmergencyDeathList(self).exec_()


    @pyqtSignature('')
    def on_actRBEmergencyEbriety_triggered(self):
        CRBEmergencyEbrietyList(self).exec_()


    @pyqtSignature('')
    def on_actRBEmergencyDiseased_triggered(self):
        CRBEmergencyDiseasedList(self).exec_()


    @pyqtSignature('')
    def on_actRBEmergencyPlaceCall_triggered(self):
        CRBEmergencyPlaceCallList(self).exec_()


    @pyqtSignature('')
    def on_actRBEmergencyMethodTransportation_triggered(self):
        CRBEmergencyMethodTransportationList(self).exec_()


    @pyqtSignature('')
    def on_actRBEmergencyTypeAsset_triggered(self):
        CRBEmergencyTypeAssetList(self).exec_()


    @pyqtSignature('')
    def on_actRBMealTime_triggered(self):
        CRBMealTime(self).exec_()


    @pyqtSignature('')
    def on_actRBDiet_triggered(self):
        CRBDiet(self).exec_()


    @pyqtSignature('')
    def on_actRBMenu_triggered(self):
        CRBMenu(self).exec_()


    @pyqtSignature('')
    def on_actRecativeClient_triggered(self):
        CRBRelativeList(self).exec_()


    @pyqtSignature('')
    def on_actRBDiseaseStage_triggered(self):
        CRBDiseaseStageList(self).exec_()


    @pyqtSignature('')
    def on_actRBDiseasePhase_triggered(self):
        CRBDiseasePhaseList(self).exec_()


    @pyqtSignature('')
    def on_actRBDispanser_triggered(self):
        CRBDispanserList(self).exec_()


    @pyqtSignature('')
    def on_actRBDocumentType_triggered(self):
        CRBDocumentTypeList(self).exec_()


    @pyqtSignature('')
    def on_actRBDocumentTypeGroup_triggered(self):
        CRBDocumentTypeGroupList(self).exec_()


    @pyqtSignature('')
    def on_actRBEventTypePurpose_triggered(self):
        CRBEventTypePurposeList(self).exec_()


    @pyqtSignature('')
    def on_actRBEventProfile_triggered(self):
        CRBEventProfileList(self).exec_()


    @pyqtSignature('')
    def on_actRBFinance_triggered(self):
        CRBFinanceList(self).exec_()


    @pyqtSignature('')
    def on_actRBFinanceSource_triggered(self):
        CRBFinanceSourceList(self).exec_()


    @pyqtSignature('')
    def on_actRBExpenseServiceItem_triggered(self):
        CRBExpenseServiceItemList(self).exec_()


    @pyqtSignature('')
    def on_actRBHealthGroup_triggered(self):
        CRBHealthGroupList(self).exec_()


    @pyqtSignature('')
    def on_actRBHurtFactorType_triggered(self):
        CRBHurtFactorTypeList(self).exec_()


    @pyqtSignature('')
    def on_actRBHurtType_triggered(self):
        CRBHurtTypeList(self).exec_()


    @pyqtSignature('')
    def on_actRBMedicalAidKind_triggered(self):
        CRBMedicalAidKindList(self).exec_()


    @pyqtSignature('')
    def on_actRBMedicalAidType_triggered(self):
        CRBMedicalAidTypeList(self).exec_()


    @pyqtSignature('')
    def on_actRBMedicalAidProfile_triggered(self):
        CRBMedicalAidProfileList(self).exec_()


    @pyqtSignature('')
    def on_actRBMesSpecification_triggered(self):
        CRBMesSpecificationList(self).exec_()


    @pyqtSignature('')
    def on_actRBActionSpecification_triggered(self):
        CRBActionSpecificationList(self).exec_()


    @pyqtSignature('')
    def on_actRBMedicalAidUnit_triggered(self):
        CRBMedicalAidUnitList(self).exec_()


    @pyqtSignature('')
    def on_actRBNet_triggered(self):
        CRBNetList(self).exec_()


    @pyqtSignature('')
    def on_actRBNomenclatureClass_triggered(self):
        CRBNomenclatureClassList(self).exec_()


    @pyqtSignature('')
    def on_actRBNomenclatureKind_triggered(self):
        CRBNomenclatureKindList(self).exec_()


    @pyqtSignature('')
    def on_actRBNomenclatureType_triggered(self):
        CRBNomenclatureTypeList(self).exec_()


    @pyqtSignature('')
    def on_actRBNomenclatureActiveSubstance_triggered(self):
        CRBNomenclatureActiveSubstanceList(self).exec_()


    @pyqtSignature('')
    def on_actRBNomenclatureActiveSubstanceGroups_triggered(self):
        CRBNomenclatureActiveSubstanceGroupsList(self).exec_()


    @pyqtSignature('')
    def on_actRBLfForm_triggered(self):
        CRBLfFormList(self).exec_()


    @pyqtSignature('')
    def on_actRBIngredient_triggered(self):
        CRBIngredientList(self).exec_()


    @pyqtSignature('')
    def on_actRBNomenclature_triggered(self):
        CRBNomenclatureList(self).exec_()


    @pyqtSignature('')
    def on_actRBNomenclatureUsingType_triggered(self):
        CRBNomenclatureUsingTypeList(self).exec_()


    @pyqtSignature('')
    def on_actRBDisposalMethod_triggered(self):
        CRBDisposalMethod(self).exec_()


    @pyqtSignature('')
    def on_actRBStockRecipe_triggered(self):
        CRBStockRecipeList(self).exec_()

    @pyqtSignature('')
    def on_actRBStockMotionItemUtilizationReason_triggered(self):
        getStockMotionItemReasonDialog(CStockMotionType.utilization, self).exec_()


    @pyqtSignature('')
    def on_actRBStockMotionNumber_triggered(self):
        CRBStockMotionNumberList(self).exec_()


    @pyqtSignature('')
    def on_actRBTissueType_triggered(self):
        CRBTissueTypeList(self).exec_()


    @pyqtSignature('')
    def on_actRBOKFS_triggered(self):
        CRBOKFSList(self).exec_()


    @pyqtSignature('')
    def on_actRBOKPF_triggered(self):
        CRBOKPFList(self).exec_()


    @pyqtSignature('')
    def on_actRBPayRefuseType_triggered(self):
        CRBPayRefuseTypeList(self).exec_()


    @pyqtSignature('')
    def on_actRBCashOperation_triggered(self):
        CRBCashOperationList(self).exec_()


    @pyqtSignature('')
    def on_actRBPolicyKind_triggered(self):
        CRBPolicyKindList(self).exec_()


    @pyqtSignature('')
    def on_actRBPolicyType_triggered(self):
        CRBPolicyTypeList(self).exec_()


    @pyqtSignature('')
    def on_actRBPost_triggered(self):
        CRBPostList(self).exec_()


    @pyqtSignature('')
    def on_actRBActivity_triggered(self):
        CRBActivityList(self).exec_()


    @pyqtSignature('')
    def on_actRBAppointmentPurpose_triggered(self):
        CRBAppointmentPurposeList(self).exec_()


    @pyqtSignature('')
    def on_actRBPrintTemplate_triggered(self):
        CRBPrintTemplate(self).exec_()

    @pyqtSignature('')
    def on_actAdminTemplate_triggered(self):
        from library.PrintTemplates import applyTemplate, getFirstPrintTemplate
        from Registry.Utils import getClientInfo2
        clientId = QtGui.qApp._currentClientId
        clientInfo = getClientInfo2(clientId)
        templateId = getFirstPrintTemplate('admin')
        data = {'client': clientInfo}
        data['clientId'] = clientId
        QtGui.qApp.call(self, applyTemplate, (self, templateId[1], data, None))

    @pyqtSignature('')
    def on_actAdminTemplate_YEARS_triggered(self):
        from library.PrintTemplates import applyTemplate, getFirstPrintTemplate
        from Registry.Utils import getClientInfo2
        clientId = QtGui.qApp._currentClientId
        clientInfo = getClientInfo2(clientId)
        templateId = getFirstPrintTemplate('admin_years')
        data = {'client': clientInfo}
        data['clientId'] = clientId
        QtGui.qApp.call(self, applyTemplate, (self, templateId[1], data, None))

    @pyqtSignature('')
    def on_actRBReasonOfAbsence_triggered(self):
        CRBReasonOfAbsenceList(self).exec_()


    @pyqtSignature('')
    def on_actRBHospitalBedProfile_triggered(self):
        CRBHospitalBedProfileList(self).exec_()


    @pyqtSignature('')
    def on_actRBJobType_triggered(self):
        CRBJobTypeList(self).exec_()


    @pyqtSignature('')
    def on_actRBJobPurpose_triggered(self):
        CRBJobPurposeList(self).exec_()

    @pyqtSignature('')
    def on_actRBLivingArea_triggered(self):
        CRBLivingAreaList(self).exec_()


    @pyqtSignature('')
    def on_actTreatmentType_triggered(self):
        CTreatmentTypeList(self).exec_()


    @pyqtSignature('')
    def on_actRBResult_triggered(self):
        CRBResultList(self).exec_()


    @pyqtSignature('')
    def on_actRBDiagnosticResult_triggered(self):
        CRBDiagnosticResultList(self).exec_()


    @pyqtSignature('')
    def on_actRBScene_triggered(self):
        CRBSceneList(self).exec_()


    @pyqtSignature('')
    def on_actRBService_triggered(self):
        CRBServiceList(self).exec_()


    @pyqtSignature('')
    def on_actRBServiceGroup_triggered(self):
        CRBServiceGroupList(self).exec_()


    @pyqtSignature('')
    def on_actRBServiceType_triggered(self):
        CRBServiceTypeList(self).exec_()


    @pyqtSignature('')
    def on_actMilitaryUnits_triggered(self):
        CKLADRMilitaryUnitList(self).exec_()


    @pyqtSignature('')
    def on_actRBSocStatusClass_triggered(self):
        CRBSocStatusClassList(self).exec_()


    @pyqtSignature('')
    def on_actRBSocStatusType_triggered(self):
        CRBSocStatusTypeList(self).exec_()


    @pyqtSignature('')
    def on_actRBSpeciality_triggered(self):
        CRBSpecialityList(self).exec_()


    @pyqtSignature('')
    def on_actRBTariffCategory_triggered(self):
        CRBTariffCategoryList(self).exec_()


    @pyqtSignature('')
    def on_actRBTempInvalidAnnulmentReason_triggered(self):
        CRBTempInvalidAnnulmentReasonList(self).exec_()

    @pyqtSignature('')
    def on_actRBTempInvalidDocument_triggered(self):
        CRBTempInvalidDocumentList(self).exec_()


    @pyqtSignature('')
    def on_actRBTempInvalidBreak_triggered(self):
        CRBTempInvalidBreakList(self).exec_()


    @pyqtSignature('')
    def on_actRBBloodType_triggered(self):
        CRBBloodTypeList(self).exec_()


    @pyqtSignature('')
    def on_actRBReactionType_triggered(self):
        CRBReactionTypeList(self).exec_()


    @pyqtSignature('')
    def on_actRBReactionManifestation_triggered(self):
        CRBReactionManifestationList(self).exec_()


    @pyqtSignature('')
    def on_actRBImageMap_triggered(self):
        CRBImageMapList(self).exec_()


    @pyqtSignature('')
    def on_actRBTempInvalidReason_triggered(self):
        CRBTempInvalidReasonList(self).exec_()


    @pyqtSignature('')
    def on_actRBTempInvalidExtraReason_triggered(self):
        CRBTempInvalidExtraReasonList(self).exec_()


    @pyqtSignature('')
    def on_actRBTempInvalidRegime_triggered(self):
        CRBTempInvalidRegimeList(self).exec_()


    @pyqtSignature('')
    def on_actRBTempInvalidResult_triggered(self):
        CRBTempInvalidResultList(self).exec_()


    @pyqtSignature('')
    def on_actRBTempInvalidDuplicateReason_triggered(self):
        CRBTempInvalidDuplicateReasonList(self).exec_()


    @pyqtSignature('')
    def on_actRBComplain_triggered(self):
        CRBComplainList(self).exec_()


    @pyqtSignature('')
    def on_actRBThesaurus_triggered(self):
        CRBThesaurus(self).exec_()


    @pyqtSignature('')
    def on_actRBTraumaType_triggered(self):
        CRBTraumaTypeList(self).exec_()


    @pyqtSignature('')
    def on_actRBToxicSubstances_triggered(self):
        CRBToxicSubstancesList(self).exec_()


    @pyqtSignature('')
    def on_actRBUnit_triggered(self):
        CRBUnitList(self).exec_()


    @pyqtSignature('')
    def on_actRBDiagnosticService_triggered(self):
        CRBDiagnosticServiceList(self).exec_()


    def on_actRBResearchArea_triggered(self):
        CRBResearchAreaList(self).exec_()


    @pyqtSignature('')
    def on_actRBResearchArea_triggered(self):
        CRBResearchAreaList(self).exec_()


    @pyqtSignature('')
    def on_actRBVisitType_triggered(self):
        CRBVisitTypeList(self).exec_()


    @pyqtSignature('')
    def on_actProphylaxisPlanningType_triggered(self):
        CRBProphylaxisPlanningType(self).exec_()


    @pyqtSignature('')
    def on_actRBActionTypeAppointment_triggered(self):
        CRBActionTypeGroupAppointment(self).exec_()

    @pyqtSignature('')
    def on_actRBActionTypeAppointment_triggered(self):
        CRBActionTypeGroupAppointment(self).exec_()


    @pyqtSignature('')
    def on_actRBInfection_triggered(self):
        CRBInfectionList(self).exec_()


    @pyqtSignature('')
    def on_actRBVaccine_triggered(self):
        CRBVaccineList(self).exec_()


    @pyqtSignature('')
    def on_actRBVaccineSchemaTransitionType_triggered(self):
        CRBVaccineSchemaTransitionTypeList(self).exec_()


    @pyqtSignature('')
    def on_actRBVaccinationCalendar_triggered(self):
        CRBVaccinationCalendarList(self).exec_()


    @pyqtSignature('')
    def on_actRBVaccinationProbe_triggered(self):
        CRBVaccinationProbeList(self).exec_()


    @pyqtSignature('')
    def on_actRBVaccinationResult_triggered(self):
        CRBVaccinationResultList(self).exec_()


    @pyqtSignature('')
    def on_actRBReaction_triggered(self):
        CRBReactionList(self).exec_()


    @pyqtSignature('')
    def on_actRBMedicalExemptionType_triggered(self):
        CRBMedicalExemptionTypeList(self).exec_()


    @pyqtSignature('')
    def on_actRBMedicalExemptionReason_triggered(self):
        CRBMedicalExemptionReasonList(self).exec_()


    @pyqtSignature('')
    def on_actRBTest_triggered(self):
        CRBTestList(self).exec_()


    @pyqtSignature('')
    def on_actRBTestGroup_triggered(self):
        CRBTestGroupList(self).exec_()


    @pyqtSignature('')
    def on_actRBLaboratory_triggered(self):
        CRBLaboratoryList(self).exec_()


    @pyqtSignature('')
    def on_actRBSuiteReagent_triggered(self):
        CRBSuiteReagentList(self).exec_()


    @pyqtSignature('')
    def on_actSurveillanceRemoveReason_triggered(self):
        CRBSurveillanceRemoveReasonList(self).exec_()


    @pyqtSignature('')
    def on_actRBObservationGroup_triggered(self):
        CRBObservationGroupList(self).exec_()


    @pyqtSignature('')
    def on_actRBObservationSubgroup_triggered(self):
        CRBObservationSubgroupList(self).exec_()


    @pyqtSignature('')
    def on_actRBSpecimenType_triggered(self):
        CRBSpecimenTypeList(self).exec_()


    @pyqtSignature('')
    def on_actRBEquipmentClass_triggered(self):
        CRBEquipmentClassList(self).exec_()


    @pyqtSignature('')
    def on_actRBEquipmentType_triggered(self):
        CRBEquipmentTypeList(self).exec_()


    @pyqtSignature('')
    def on_actRBEquipment_triggered(self):
        dlg = CRBEquipmentList(self)
        dlg.setEditableJournal(QtGui.qApp.userHasAnyRight([urAccessEquipmentMaintenanceJournal, urAccessRefBooks]))
        dlg.exec_()


    @pyqtSignature('')
    def on_actRBContainerType_triggered(self):
        CRBContainerTypeList(self).exec_()


    @pyqtSignature('')
    def on_actRBLocationCardType_triggered(self):
        CRBLocationCardTypeList(self).exec_()

    @pyqtSignature('')
    def on_actRBDocumentTypeForTracking_triggered(self):
        CRBDocumentTypeForTrackingList(self).exec_()


    @pyqtSignature('')
    def on_actRBStatusObservationClientType_triggered(self):
        CRBStatusObservationClientTypeList(self).exec_()


    @pyqtSignature('')
    def on_actRBClientConsentType_triggered(self):
        CRBClientConsentTypeList(self).exec_()


    @pyqtSignature('')
    def on_actRBDeathReason_triggered(self):
        CRBDeathReasonList(self).exec_()


    @pyqtSignature('')
    def on_actRBContingentType_triggered(self):
        CRBContingentTypeList(self).exec_()


    @pyqtSignature('')
    def on_actRBDeathPlaceType_triggered(self):
        CRBDeathPlaceTypeList(self).exec_()


    @pyqtSignature('')
    def on_actRBDeathCauseType_triggered(self):
        CRBDeathCauseTypeList(self).exec_()


    @pyqtSignature('')
    def on_actRBEmployeeTypeDeterminedDeathCause_triggered(self):
        CRBEmployeeTypeDeterminedDeathCauseList(self).exec_()


    @pyqtSignature('')
    def on_actRBGroundsForDeathCause_triggered(self):
        CRBGroundsForDeathCauseList(self).exec_()


    @pyqtSignature('')
    def on_actEventsCheck_triggered(self):
        CEventsCheck(self).exec_()


    @pyqtSignature('')
    def on_actEventsOMSCheck_triggered(self):
        from Accounting.AccountCheckDialog import CAccountCheckDialog
        dialog = CAccountCheckDialog(self, None)
        try:
            dialog.exec_()
        finally:
            dialog.deleteLater()


    @pyqtSignature('')
    def on_actRBAnatomicalLocalizations_triggered(self):
        CRBAnatomicalLocalizationsList(self).exec_()


    @pyqtSignature('')
    def on_actControlDiagnosis_triggered(self):
        CControlDiagnosis(self).exec_()


    @pyqtSignature('')
    def on_actControlDoubles_triggered(self):
        CControlDoubles(self).exec_()


    @pyqtSignature('')
    def on_actControlMes_triggered(self):
        CLogicalControlMes(self).exec_()


    @pyqtSignature('')
    def on_actClientsCheck_triggered(self):
        ClientsCheck(self).exec_()


    @pyqtSignature('')
    def on_actTempInvalidCheck_triggered(self):
        TempInvalidCheck(self).exec_()


    @pyqtSignature('')
    def on_actUpdateTempInvalid_triggered(self):
        CCheckTempInvalidEditDialog(self).exec_()


    @pyqtSignature('')
    def on_actCreateAttachClientsForArea_triggered(self):
        dlg = CCreateAttachClientsForAreaDialog(self)
        dlg.exec_()
        dlg.stop()

    @pyqtSignature('')
    def on_action_WSAttach_triggered(self):
        if self.registry:
            reattachlist = self.registry.modelClients._idList[:]
            dlg = CReAttach(self)
            dlg.setClientIdList(reattachlist)
            dlg.exec_()



    @pyqtSignature('')
    def on_actDbfView_triggered(self):
        viewDbf(self)


    @pyqtSignature('')
    def on_actTestSendMail_triggered(self):
        sendMail(self, '', u'проверка связи', u'проверка связи\n1\n2\n3', [])


    @pyqtSignature('')
    def on_actSetAdmittingStart_triggered(self):
        admitting = self.setAdmitting()
        self.setAdmittingEnabled(admitting, isAdmitting=True)


    @pyqtSignature('')
    def on_actSetDutyStart_triggered(self):
        duty = self.setAdmitting(isDuty=True)
        self.setAdmittingEnabled(duty, isDuty=True)


    @pyqtSignature('')
    def on_actSetAdmittingEnd_triggered(self):
        admitting = self.setAdmitting()
        self.setAdmittingEnabled(admitting, isAdmitting=True)

    @pyqtSignature('')
    def on_actSetDutyEnd_triggered(self):
        duty = self.setAdmitting(isDuty=True)
        self.setAdmittingEnabled(duty, isDuty=True)


    @pyqtSignature('')
    def on_actTestMKB_triggered(self):
        from library.ICDTreeTest import testICDTree
        testICDTree()


    @pyqtSignature('')
    def on_actAverageDurationAcuteDisease_triggered(self):
        CAverageDurationAcuteDiseaseBase(self).exec_()


    @pyqtSignature('')
    def on_actTestRLS_triggered(self):
        from library.RLS.RLSComboBoxTest import testRLSComboBox
        testRLSComboBox()


    @pyqtSignature('')
    def on_actTestMES_triggered(self):
        from library.MES.MESComboBoxTest import testMESComboBox
        testMESComboBox()


    @pyqtSignature('')
    def on_actTestCSG_triggered(self):
        from library.CSG.CSGComboBoxTest import testCSGComboBox
        testCSGComboBox()


    @pyqtSignature('')
    def on_actTestTNMS_triggered(self):
        from library.TNMS.TNMSComboBoxTest import testTNMSComboBox
        testTNMSComboBox()


    @pyqtSignature('')
    def on_actNotificationLog_triggered(self):
        CNotificationLogList(self).exec_()


    @pyqtSignature('')
    def on_actNotificationRules_triggered(self):
        CNotificationRuleList(self).exec_()


    @pyqtSignature('')
    def on_actRBNotificationKind_triggered(self):
        CRBNotificationKindList(self).exec_()


    @pyqtSignature('')
    def on_actRBAccountType_triggered(self):
        CRBAccountTypeList(self).exec_()

    @pyqtSignature('')
    def on_actPrikCoef_triggered(self):
        CRBPrikCoefTypeList(self).exec_()

    @pyqtSignature('')
    def on_actRBResearchKind_triggered(self):
        CRBResearchKindList(self).exec_()

    @pyqtSignature('')
    def on_actRBContingentKind_triggered(self):
        CRBContingentKindList(self).exec_()
        
    @pyqtSignature('')
    def on_actRBContingentKindRemoval_triggered(self):
        CRBContingentKindRemovalList(self).exec_()

    @pyqtSignature('')
    def on_actRBFmsUnit_triggered(self):
        CRBFmsUnitList(self).exec_()

    @pyqtSignature('')
    def on_actExportLocalLabResultsToUSISH_triggered(self):
        try:
            ExportLocalLabResultsToUsish.exportLocalLabResultsToUsish()
        except:
            QtGui.qApp.logCurrentException()

    @pyqtSignature('')
    def on_actExportAttachDoctorSectionInfo_triggered(self):
        CExportAttachDoctorSectionInfoDialog(self).exec_()

    @pyqtSignature('')
    def on_actAppPreferences_triggered(self):
        application = QtGui.qApp
        try:
            application.closeScanner()
            application.closeSmartCardReader()
            dialog = CPreferencesDialog(self)
            dialog.setProps(application.preferences.appPrefs)
            if dialog.exec_():
                prevOrgId = application.currentOrgId()
                prevOrgStructureId = application.currentOrgStructureId()
                prevOrgStructureVisible = None
                prevShowComplaintColumn = forceBool(QtGui.qApp.preferences.appPrefs.get('showComplaintColumn', False))
                if QtGui.qApp.preferences.appPrefs.get('TimetableOrgStructureCheckedNames'):
                    prevOrgStructureVisible = [forceInt(checkedId) for checkedId in QtGui.qApp.preferences.appPrefs.get('TimetableOrgStructureCheckedNames').toList()]
                application.preferences.appPrefs.update(dialog.getProps())
                application.preferences.save()
                orgId = application.currentOrgId()
                OrgStructureVisible = [forceInt(checkedId) for checkedId in QtGui.qApp.preferences.appPrefs.get('TimetableOrgStructureCheckedNames').toList()]
                ShowComplaintColumn = forceBool(QtGui.qApp.preferences.appPrefs.get('showComplaintColumn', False))
                if not orgId:
                    self.closeAllSubwindows()
                self.setUserName(application.userName())
                if orgId != prevOrgId:
                    application.emit(SIGNAL('currentOrgIdChanged()'))
                if QtGui.qApp.currentOrgStructureId() != prevOrgStructureId:
                    application.emit(SIGNAL('currentOrgStructureIdChanged()'))
                if OrgStructureVisible != prevOrgStructureVisible:
                    QtGui.qApp.mainWindow.dockResources.onConnectionChanged(True)
                    QtGui.qApp.mainWindow.dockFreeQueue.onConnectionChanged(True)
                elif ShowComplaintColumn != prevShowComplaintColumn:
                    QtGui.qApp.mainWindow.dockResources.onConnectionChanged(True)
                QtGui.qApp.emitCurrentClientInfoChanged()
                application.clearPreferencesCache()
                self.updateActionsState()
                application.webDAVInterface.setWebDAVUrl(application.getWebDAVUrl())
        finally:
            QtGui.qApp._timeoutLogout.setup(QtGui.qApp.getConnectionTimeout() * 60000, timeoutFunc=self.logoutAndLogin)
            application.tryOpenScanner()
            application.tryOpenSmartCardReader()


    @pyqtSignature('')
    def on_actConnection_triggered(self):
        dlg   = CConnectionDialog(self)
        preferences = QtGui.qApp.preferences
        dlg.setDriverName(preferences.dbDriverName)
        dlg.setServerName(preferences.dbServerName)
        dlg.setServerPort(preferences.dbServerPort)
        dlg.setDatabaseName(preferences.dbDatabaseName)
        dlg.setCompressData(preferences.dbCompressData)
        dlg.setUserName(preferences.dbUserName)
        dlg.setPassword(preferences.dbPassword)
        if dlg.exec_():
            preferences.dbDriverName = dlg.driverName()
            preferences.dbServerName = dlg.serverName()
            preferences.dbServerPort = dlg.serverPort()
            preferences.dbDatabaseName = dlg.databaseName()
            preferences.dbCompressData = dlg.compressData()
            preferences.dbUserName = dlg.userName()
            preferences.dbPassword = dlg.password()
            preferences.save()


    @pyqtSignature('')
    def on_actDecor_triggered(self):
        dlg = CDecorDialog(self)
        preferences = QtGui.qApp.preferences
        dlg.setStyle(preferences.decorStyle)
        dlg.setStandardPalette(preferences.decorStandardPalette)
        dlg.setMaximizeMainWindow(preferences.decorMaximizeMainWindow)
        dlg.setFullScreenMainWindow(preferences.decorFullScreenMainWindow)
        dlg.setUseCustomFont(preferences.useCustomFont)
        dlg.setFont(preferences.font)
        dlg.setPropertyColor(preferences.propertyColor)
        dlg.setPropertyColorTest(preferences.propertyColorTest)
        if dlg.exec_():
            preferences.decorStyle = dlg.style()
            preferences.decorStandardPalette = dlg.standardPalette()
            preferences.decorMaximizeMainWindow = dlg.maximizeMainWindow()
            preferences.decorFullScreenMainWindow = dlg.fullScreenMainWindow()
            preferences.useCustomFont = dlg.useCustomFont()
            preferences.font = dlg.font()
            preferences.propertyColor = dlg.propertyColor()
            preferences.propertyColorTest = dlg.propertyColorTest()
            preferences.save()
            QtGui.qApp.applyDecorPreferences()


    @pyqtSignature('')
    def on_actCalendar_triggered(self):
        CCalendarExceptionList(self).exec_()
        calendarInfo = QtGui.qApp.calendarInfo
        calendarInfo.clear()
        calendarInfo.load()


    @pyqtSignature('')
    def on_actInformerMessages_triggered(self):
        CInformerList(self).exec_()


    @pyqtSignature('')
    def on_actInformer_triggered(self):
        showInformer(self, False)


    @pyqtSignature('')
    def on_actUserRight_triggered(self):
        CUserRightListDialog(self).exec_()


    @pyqtSignature('')
    def on_actRBLogin_triggered(self):
        CLoginListDialog(self).exec_()


    @pyqtSignature('')
    def on_actUserRightProfile_triggered(self):
        CUserRightProfileListDialog(self).exec_()


    @pyqtSignature('')
    def on_actAbout_triggered(self):
        dlg = QtGui.QDialog()
        dlg.setWindowTitle(u'О программе')
        def aboutModernisation():
            dialog = CModernisationVersionList(None)
            dialog.exec_()
        dlg.setWindowIcon(QtGui.QIcon(':/new/prefix1/icons/znak_32x32.png'))
        dlg.setWindowFlags(dlg.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        layout = QtGui.QVBoxLayout()
        layout.setAlignment(Qt.AlignHCenter)
        logo = QtGui.QLabel()
        logo.setPixmap(QtGui.QPixmap(':/new/prefix1/icons/logo_130x42.png'))
        layout.addWidget(logo)
        label = QtGui.QLabel()
        label.setText(QtGui.qApp.getAbout())
        label.setTextFormat(Qt.RichText)
        label.linkActivated.connect(aboutModernisation)
        layout.addWidget(label)
        hbox = QtGui.QHBoxLayout()
        hbox.setAlignment(Qt.AlignCenter)
        button = QtGui.QPushButton("OK")
        button.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        button.setMaximumWidth(75)
        button.clicked.connect(dlg.close)
        hbox.addWidget(button)
        layout.addLayout(hbox)
        dlg.setLayout(layout)
        dlg.exec_()


    @pyqtSignature('')
    def on_actAboutQt_triggered(self):
        QtGui.QMessageBox.aboutQt(self, u'О Qt')


    @pyqtSignature('QWidget*')
    def on_centralWidget_mdiSubwindowClose(self, widget):
        if widget == self.registry:
            self.registry = None
        elif widget == self.suspendedAppointment:
            self.suspendedAppointment = None
        elif widget == self.dispExchange:
            self.dispExchange = None
        elif widget == self.homeCallRequests:
            self.homeCallRequests = None
        elif widget == self.prophylaxisPlanning:
            self.prophylaxisPlanning = None
        elif widget == self.distantMonitoring:
            self.distantMonitoring = None


class CModernisationVersionList(CItemsListDialog):
    def __init__(self, parent):
        CItemsListDialog.__init__(self, parent, [
            CIntCol(u'Версия', ['version'], 20),
            CDateTimeCol(u'Дата обновления', ['dateUpdate'], 40),
            CTextCol(u'Описание', ['description'], 100),
        ], 'VersionControlMod', ['dateUpdate', 'version'])
        self.setWindowTitleEx(u'Установленные версии модернизации')
        self.btnNew.setVisible(False)
        self.btnNew.setEnabled(False)
        self.btnEdit.setVisible(False)
        self.btnEdit.setEnabled(False)
        self.tblItems.doubleClicked.disconnect()


    def select(self, props={}):
        table = self.model.table()
        cond = CItemsListDialog.generateFilterByProps(self, props)
        cond.append(table['name'].eq('Update'))
        cond.append(table['description'].isNotNull())
        return QtGui.qApp.db.getIdList(table.name(), self.idFieldName, cond, self.order)


def parseGCDebug(val):
    result = 0
    for char in val.upper():
        if char == 'S':
            result |= gc.DEBUG_STATS
        elif char == 'C':
            result |= gc.DEBUG_COLLECTABLE
        elif char == 'U':
            result |= gc.DEBUG_UNCOLLECTABLE
        elif char == 'I':
            result |= gc.DEBUG_INSTANCES
        elif char == 'O':
            result |= gc.DEBUG_OBJECTS
    return result

def parseGCThreshold(val):
    result = []
    if val:
        for s in val.split(','):
            try:
                v = int(s)
            except:
                v = 0
            result.append(v)
        l = len(result)
        if l > 3:
            result = result[0:3]
    return result


def parseBgParams(image, size, position):
    bgParams = None
    if image:
        bgParams = {'image': os.path.expanduser(image)}
        if size:
            bgParams['size'] = size
        if position:
            bgParams['position'] = position
    return bgParams

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
##    gc.set_threshold(*[10*k for k in gc.get_threshold()])
    parser = OptionParser(usage='usage: %prog [options]')
    parser.add_option('-c', '--config',
                      dest='iniFile',
                      help='custom .ini file name',
                      metavar='iniFile',
                      default=CS11mainApp.iniFileName
                     )
    parser.add_option('-d', '--demo',
                      dest='demo',
                      help='Login as demo',
                      action='store_true',
                      default=False
                     )
    parser.add_option('--SQL',
                      dest='logSql',
                      help='log sql queries',
                      action='store_true',
                      default=False
                     )
    parser.add_option('--applog',
                      dest='appLogMark',
                      help='set main app log mark',
                      metavar='appLogMark',
                      default='')
    parser.add_option('-r', '--record',
                      dest='recordEventLogFile',
                      help='file name for record events',
                      metavar='eventLogFile',
                      default=None,
                     )
    parser.add_option('-p', '--play',
                      dest='playEventLogFile',
                      help='file name for playback events',
                      metavar='eventLogFile',
                      default=None
                     )
    parser.add_option('-l', '--nolock',
                      dest='nolock',
                      help='Disable record lock',
                      action='store_true',
                      default=False
                     )
    parser.add_option('--gc-debug',
                      dest='gcDebug',
                      help='gc debug flags, chars S(stat), C(collectable), U(uncollectable), I(instances), O(objects), for details see gc.set_debug',
                      metavar='[S][C][U][I][O]',
                      default=''
                     )
    parser.add_option('--gc-threshold',
                      dest='gcThreshold',
                      help='gc thresholds list, see gc.set_threshold ',
                      metavar='threshold0[,threshold1[,threshold2]]',
                      default=''
                     )
    parser.add_option('--bgImage',
                      dest='bgImage',
                      help='set backgroung image',
                      metavar='path to image',
                      default=None)
    parser.add_option('--bgSize',
                      dest='bgSize',
                      help='set backgroung Size. x for percent scaling or x,y for scaling to x.y size or x,y,1 for keeping aspect ratio scale',
                      metavar = '200,200,1',
                      default=None)
    parser.add_option('--bgPos',
                      dest='bgPosition',
                      help='set backgroung position. center, topRight, bottomRight, bottomLeft',
                      metavar = 'center',
                      default=None)
    parser.add_option('--version',
                      dest='version',
                      help='print version and exit',
                      action='store_true',
                      default=False
                     )
    parser.add_option('--restart',
                      dest='restart',
                      help='restart app',
                      action='store_true',
                      default=False
                     )
    parser.add_option('--rkey',
                      dest='rkey',
                      help='debug rkey',
                      default=''
                     )
    parser.add_option('--template_debug',
                      dest='isPrintDebugEnabled',
                      help='run in debug mode',
                      action='store_true',
                      default=False
                     )
    parser.add_option('--faulthandler',
                      dest='enableFaulthandler',
                      help='display the Python backtrace on SIGSEGV, SIGFPE, SIGABRT, SIGBUS and SIGILL signals',
                      action='store_true',
                      default=True
                      )
    parser.add_option('--oneprocess',
                      dest='oneprocess',
                      help='forbid start more than one copy of application',
                      action='store_true',
                      default=False
                      )
#    parser.add_option("-q", "--quiet",   action="store_false", dest="verbose", default=True,  help="don't print status messages to stdout")
    (options, args) = parser.parse_args()
    parser.destroy()

    if options.version:
#        print '%s, v.2.5' % titleLat
        print CS11mainApp.getLatVersion()
        return

    gcDebug = parseGCDebug(options.gcDebug)
    gcThreshold = parseGCThreshold(options.gcThreshold)
    
    if gcDebug:
        gc.set_debug(gcDebug)
        print 'debug set to ', gcDebug
    if gcThreshold:
        gc.set_threshold(*gcThreshold)
        print 'threshold set to ', gcThreshold

    bgParams = parseBgParams(options.bgImage, options.bgSize, options.bgPosition)

    app = CS11mainApp(sys.argv, options.demo, options.iniFile, options.nolock, options.logSql, options.appLogMark, options.rkey)
    if options.recordEventLogFile:
        app.eventLogFile = open(options.recordEventLogFile, 'w+', 0)
        app.eventLogTime = time.time()
    stdTtranslator = QTranslator()
    stdTtranslator.load(os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'i18n', 'std_ru.qm'))
    app.installTranslator(stdTtranslator)
    #Перевод стандартных диалогов Qt
    stdTtranslatorLib = QTranslator()
    stdTtranslatorLib.load(os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'i18n', 'qt_ru_lib.qm'))
    app.installTranslator(stdTtranslatorLib)
    stdTtranslatorLib = QTranslator()
    stdTtranslatorLib.load(os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'i18n', 'qt_ru.qm'))
    app.installTranslator(stdTtranslatorLib)
    app.isPrintDebugEnabled = options.isPrintDebugEnabled
    app.debugPrintData = DebugPrintData()

    if options.enableFaulthandler:
        try:
            import faulthandler
            fileName = app.getFaultHandlerLogFilePath()
            f = open(fileName, 'a')
            f.write(u'\nstart logging: ' + QDateTime.currentDateTime().toString(Qt.ISODate) + '\n')
            faulthandler.enable(file=f)
        except ImportError as e:
            pass
            # app.logCurrentException()
        except IOError as e:
            pass
            # app.logCurrentException()

    QtGui.qApp = app
    try:
        import platform
        if platform.system() == 'Windows' and not options.restart:
            if winAutoUpdate(app, platform.system()):
                res = 0
                sys.exit(0)
        else:
            if winAutoUpdate(app, platform.system()):
                res = 0
                sys.exit(0)
    except Exception as e:
        pass
    res = 0
    if QtGui.qApp:
        QtGui.qApp.jobTicketReserveHolder = CJobTicketReserveHolder(app)
        app.applyDecorPreferences() # надеюсь, что это поможет немного сэкономить при создании гл.окна
        MainWindow = CS11MainWindow(bgParams)
        app.mainWindow = MainWindow
#ymd st
        try:
            app.db.parentGl = MainWindow
        except:
            pass
# ymd end
        app.applyDecorPreferences() # применение максимизации/полноэкранного режима к главному окну
        MainWindow.show()
        app.tryOpenScanner()
        app.tryOpenSmartCardReader()
        if app.preferences.dbAutoLogin:
            MainWindow.actLogin.activate(QtGui.QAction.Trigger)
        app._timeoutLogout.setup(app.getConnectionTimeout() * 60000, u'подключение', MainWindow.logoutAndLogin)
        res = app.exec_()
        app.preferences.save()
        if app.db:
            app.clearUserId(False)
            app.closeDatabase()
        app.doneTrace()
        QtGui.qApp = None
    return res
    
def errorUpdateMis():
    QtGui.QMessageBox().critical(None, u'Ошибка', u'Версия МИС устарела, запуск невозможен.', QtGui.QMessageBox.Ok)

def winAutoUpdate(app, platformName):
    res = False
    dontStart = False
    app.openDatabase()
    # if not app.db or not app.checkGlobalPreference(u'23:winAutoUpd', u'да'):
    #     if app.db:
    #         app.closeDatabase()
    #     return res
    record = app.db.getRecordEx('VersionControl', 'version, dateUpdate, DATEDIFF(CURDATE(), dateUpdate) AS day', "name='ClientVersion'")
    dbVersion = [forceInt(item) for item in forceString(record.value('version')).split('.')]
    clientVer = [forceInt(item) for item in app.socRev.split('.')[:-1]]
    dbVersionDate = forceDate(record.value('dateUpdate'))
    recordNew = app.db.getRecordEx('VersionControl', 'version, dateUpdate', "name='NewVersion'")
    day = forceInt(record.value('day'))
    check = False
    if recordNew:
        dbNewVersion = [forceInt(item) for item in forceString(recordNew.value('version')).split('.')]
        dbNewVersionDate = forceDate(recordNew.value('dateUpdate'))
        if dbNewVersion and dbNewVersionDate and dbVersion < dbNewVersion:
            check = True
            if day > 3:
                errorUpdateMis()
                dontStart = True
            else:
                if day == 0:
                    message = u'Обнаружена новая версия, обновите МИС в течение 3х дней'
                elif day == 1:
                    message = u'Обнаружена новая версия, обновите МИС в течение 2х дней'
                elif day == 2:
                    message = u'Обнаружена новая версия, обновите МИС в течение суток'
                else:
                    message = u'Обнаружена новая версия, обновите МИС, иначе завтра запуск станет невозможен'
                QtGui.QMessageBox().information(None,
                                            u'Внимание!',
                                            message,
                                            QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)

    if not check and clientVer < dbVersion:
        if dbVersion and dbVersionDate and clientVer < dbVersion:
            check = True
            if day > 3:
                errorUpdateMis()
                dontStart = True
            else:
                if day == 0:
                    message = u'Обнаружена новая версия, обновите МИС в течение 3х дней'
                elif day == 1:
                    message = u'Обнаружена новая версия, обновите МИС в течение 2х дней'
                elif day == 2:
                    message = u'Обнаружена новая версия, обновите МИС в течение суток'
                else:
                    message = u'Обнаружена новая версия, обновите МИС, иначе завтра запуск станет невозможен'
                QtGui.QMessageBox().information(None,
                                                u'Внимание!',
                                                message,
                                                QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)

    if platformName == 'Windows':
        ftpURL = forceString(app.preferences.appPrefs.get('FTPUrl', ''))
        if not ftpURL:
            ftpURL = app.getGlobalPreference(u'23:ftpURL')
        if clientVer > dbVersion:
            QtGui.QMessageBox().information(None,
                                    u'Внимание!',
                                    u'Вы используете тестовую сборку клиента',
                                    QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
        if clientVer < dbVersion:
            app.closeDatabase()
            if not ftpURL:
                if not check:
                    errorUpdateMis()
                    return True
                QtGui.QMessageBox().information(None,
                                                u'Внимание!',
                                                u'Не укзан адрес Адрес FTP-сервера автообновления win-клиента',
                                                QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
                return dontStart
            fileName = 'Samson_Install_Win_{0}.exe'.format(dbVersion[-2])
            from ftplib import FTP
            import tempfile
            batFileName = 'Samson_update.bat'
            try:
                appFileName = os.path.abspath(__file__)
            except NameError:  # We are the main py2exe script, not a module
                import sys as s1
                appFileName = os.path.abspath(s1.argv[0])
            if appFileName.endswith('s11main.py'):
                appFileName = appFileName[:-10] + 'samson.exe'
            tmpdir = tempfile.gettempdir()
            newpathfile = os.path.join(tmpdir, fileName)
            batPathFile = os.path.join(tmpdir, batFileName)
            try:
                if ftpURL.startswith('ftp://'):
                    ftpURL = ftpURL.replace('ftp://', '')
                ftpURL = ftpURL.split('/')
                ftp = FTP(ftpURL[0], timeout=30)
                ftp.login()
                for pth in ftpURL[1:]:
                    if pth:
                        ftp.cwd(pth)
                lsFtp = ftp.nlst(fileName)
                if lsFtp.count(fileName) != 0:
                    QtGui.QMessageBox().information(None,
                                                    u'Внимание!',
                                                    u'Версия клиента отличается от версии БД.\nБудет произведено автообновление!\nНажмите "ОК" и дождитесь запуска программы после автоматического обновления',
                                                    QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
                    ftp.voidcmd('TYPE I')
                    fileSize = ftp.size(fileName)
                    downloadProgress = DownloadProgress()
                    downloadProgress.labelFile.setText(fileName)
                    downloadProgress.labelFileSize.setText(LoadSizeFormat(0, fileSize))

                    downloadProgress.progressBarFile.setValue(0)
                    downloadProgress.progressBarFile.setMaximum(fileSize)
                    with open(newpathfile, 'wb') as fileUpdate:
                        def callback(data):
                            fileUpdate.write(data)
                            downloadProgress.progressBarFile.setValue(downloadProgress.progressBarFile.value() + len(data))
                            downloadProgress.labelFileSize.setText(
                                LoadSizeFormat(downloadProgress.progressBarFile.value(), fileSize))
                            QtGui.qApp.processEvents()

                        ftp.retrbinary('RETR {0:s}'.format(fileName), callback)
                        ftp.quit()
                    batFile = open(batPathFile, 'wb')
                    batFile.writelines(u"""
::@echo off
::Команды DOS
::http://detc.usu.ru/Assets/aCOMP0041/lectures/DOS-commands/DOS.html

::pause - пауза 3 секунды
::ping 127.0.0.1 -n 3 >nulprint(subprocess.__file__

:run app
start /wait "" "{newpathfile:s}" /silent /nocancel

::AHTUNG - удаляем SETUP.ЕХЕ
:try
del "{newpathfile:s}"
if exist "{newpathfile:s}" goto try

start "" "{appFileName:s}" --restart

::Удаляем bat - он уже не нужен
del "{batPathFile:s}"
del "{newpathfile:s}"
            """.format(newpathfile=newpathfile, batPathFile=batPathFile, appFileName=appFileName).encode('cp866'))
                    batFile.close()
                    if app.db:
                        app.clearUserId(False)
                        app.closeDatabase()
                    app.doneTrace()
                    QtGui.qApp = None
                    import subprocess
                    SW_HIDE = 0
                    info = subprocess.STARTUPINFO()
                    try:
                        info.dwFlags = subprocess.STARTF_USESHOWWINDOW
                        info.wShowWindow = SW_HIDE
                    except:
                        info.dwFlags = subprocess._subprocess.STARTF_USESHOWWINDOW
                        info.wShowWindow = subprocess._subprocess.SW_HIDE
                    subprocess.Popen(batPathFile, startupinfo=info)
                    res = True
                else:
                    if not check:
                        errorUpdateMis()
                        return True
                    else:
                        return dontStart
            except:
                app.logCurrentException()
                QtGui.QMessageBox().critical(None, u'Ошибка', u'Проблема с доступом к серверу обновлений', QtGui.QMessageBox.Ok)
                return dontStart
            return res
    else:
        return dontStart


if __name__ == '__main__':
    locale.setlocale(locale.LC_ALL, '')
    sys.stdout = codecs.getwriter(locale.getpreferredencoding())(sys.stdout)
    sys.stderr = codecs.getwriter(locale.getpreferredencoding())(sys.stderr)
    main()
#    sys.exit(res)
