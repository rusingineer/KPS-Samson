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
import base64
import datetime
import json
import urlparse
import uuid


import requests
from PyQt4 import QtGui, QtSql
from PyQt4.QtCore                           import (
                                                    Qt,
                                                    pyqtSignature,
                                                    SIGNAL,
                                                    QDate,
                                                    QDateTime,
                                                    QModelIndex,
                                                    QObject,
                                                    QRegExp,
                                                    QTime,
                                                    QVariant,
                                                    QString,
                                                    pyqtSignal
                                                   )

from Events.Utils import checkDiagnosis
from Exchange.ExchangeScanPromobot import scanning
from KLADR.Utils import checkIsActualSTREET
from Orgs.OrgStructComboBoxes import COrgStructureTreePurpose
from library.Identification import getIdentification
from library.MKBExSubclassComboBox import CMKBExSubclassCol
from library.MSCAPI import MSCApi
from library.RBTreeComboBox import CRBTreeInDocTableCol
from library.SortFilterProxyTableModel import CSortFilterProxyTableModel
from library.crbcombobox                      import CRBModelDataCache, CRBComboBox
from library.database import CTableRecordCache, decorateString
from library.DbComboBox                       import CDbModel
from library.InDocTable import (CInDocTableModel, CDateInDocTableCol, CDateTimeInDocTableCol, CEnumInDocTableCol,
                                CFloatInDocTableCol, CInDocTableCol, CIntInDocTableCol, CRBInDocTableCol,
                                CRecordListModel, CBoolInDocTableCol, CSelectStrInDocTableCol,
                                CMKBListInDocTableModel, CLocItemDelegate)
from library.ICDInDocTableCol import CICDInDocTableCol, CICDExInDocTableCol
from library.interchange                      import setComboBoxValue, setLineEditValue, setSpinBoxValue, setTextEditValue
from library.ItemsListDialog                  import CItemEditorBaseDialog
from library.LineEditWithRegExpValidator      import CLineEditWithRegExpValidator
from library.SafeCleanupMixin import SafeCleanupMixin
from library.TableModel                     import (
                                                    CTableModel,
                                                    CCol,
                                                    CDateCol,
                                                    CDateTimeCol,
                                                    CNameCol,
                                                    CRefBookCol,
                                                    CTextCol,
                                                    CTimeCol,
                                                   )
from library.Utils import (calcAgeTuple, checkSNILS, exceptionToUnicode, fixSNILS, forceBool, forceDate, forceDateTime,
                           forceDouble, forceInt, forceRef, forceString, forceStringEx, forceTime, formatSex,
                           formatShortName, formatSNILS, isNameValid, nameCase, pyDate, smartDict, toVariant,
                           trim, unformatSNILS, formatDate, variantEq, checkDocCode, setPref, getPref)

from Accounting.Utils                         import CTariff # WTF!
from ClientHousesList                         import CClientHousesList
from ClientQuotaDiscussionEditor              import CQuotingEditorDialog
from KLADR.KLADRModel                         import getDistrictName, getOKATO
from Orgs.ContractFindComboBox                import CContractTreeFindComboBox
from Orgs.OrgComboBox import COrgComboBox, CInsurerInDocTableCol, CPolyclinicComboBox, CInsurerAreaInDocTableCol, COrgInDocTableCol, \
    COrgInDocTableColEx
from Orgs.Orgs                                import selectOrganisation
from Orgs.OrgStructureCol                     import COrgStructureInDocTableCol
import Exchange.AttachService as AttachService

from Orgs.Utils import advisePolicyType, findOrgStructuresByHouseAndFlat, getOKVEDName, getOrganisationInfo, \
    getOrganisationInfisAndShortName, getOrgStructureDescendants, getOrgStructureIdentification
from Quoting.QuotaTypeComboBox                import CQuotaTypeComboBox
from Registry.ClientRelationComboBox          import CClientRelationComboBox
from Registry.HurtModels                      import CWorkHurtFactorsModel, CWorkHurtsModel
from Registry.Utils import (CClientRelationComboBoxForConsents, CDbSearchWidget, clientIdToText, findHouseId,
                            findKLADRRegionRecordsInQuoting, findDistrictRecordsInQuoting, formatAddressInt, getAddress,
                            getAddressId, getClientAddress, getClientDocument, getClientWork,
                            uniqueIdentifierCheckingIsPassed, unitedPolicyIsVaid, CClientActiveDispensaryInfo,
                            CClientContingentKindInfo, CClientForcedTreatmentInfo, CClientSuicideInfo,
                            checkClientAttachService)
from Users.Rights import (
    urRegEditClientDeathDate, urRegEditClientHistory, urRegTabReadRegistry, urRegTabWriteRegistry,
    urRegDeleteAttachSync, urEnableTabPassport, urEnableSocStatus, urEnableClientAttach, urEnableTabWork,
    urEnableTabChangeJournalInfo, urEnableTabDocs, urEnableTabClientPolicy, urEnableTabClientAddress,
    urEnableTabFeature, urEnableTabResearch, urEnableTabDangerous, urEnableTabContingentKind, urEnableTabIdentification,
    urEnableTabRelations, urEnableTabContacts, urEnableTabQuoting, urEnableTabDeposit, urEnableTabConsent,
    urRegEditClientVisibleTabSocStatus, urRegEditClientVisibleTabAttach, urRegEditClientVisibleTabWork,
    urRegEditClientVisibleTabChangeJournalInfo, urRegEditClientVisibleTabFeature, urRegEditClientVisibleTabResearch,
    urRegEditClientVisibleTabDangerous, urRegEditClientVisibleTabContingentKind,
    urRegEditClientVisibleTabIdentification, urRegEditClientVisibleTabRelations, urRegEditClientVisibleTabContacts,
    urRegEditClientVisibleTabQuoting, urRegEditClientVisibleTabDeposit, urRegEditClientVisibleTabConsent,
    urRegEditClientVisibleTabDocs, urRegEditClientVisiblePolicy, urRegEditClientVisibleAddress,
    urRegEditClientVisibleHistory, urRegEditClientSnils, urRegEditClientInfo,
    urEnableTabClientMonitoring, urEnableTabClientEpidemic, urRegEditClientVisibleTabMonitoring,
    urRegEditClientVisibleTabEpidemic, urRegEditClientAttachEndDateOwnAreaOnly,
    urRegReadClientVisibleContingentKindOwnAreaOnly, urRegCreateClientContingentKindOwnAreaOnly,
    urRegEditClientContingentKindOpenOwnAreaOnly, urRegEditClientContingentKindClosedOwnAreaOnly,
    urRegCreateClientAttachOwnAreaOnly, urRegEditClientHospitalization,)
from RefBooks.DocumentType.Descr            import getDocumentTypeDescr
from RefBooks.ActionType.List               import CActionPropertyTemplateCol
from RefBooks.NomenclatureActiveSubstance.ActiveSubstanceComboBox import CActiveSubstanceComboBox
from RefBooks.ObservationSubgroup.ObservationSubgroupComboBox import CObservationSubgroupInDocTableCol
from Registry.Ui_ClientEditDialog             import Ui_Dialog
from datetime import date, timedelta

class CClientEditDialog(CItemEditorBaseDialog, Ui_Dialog, SafeCleanupMixin):
    prevAddress = None
    prevWork    = None

    socStatusChanged = pyqtSignal()

#    defaultKLADRCode = '7800000000000'

    def __init__(self, parent):
# ctor
        CItemEditorBaseDialog.__init__(self, parent, 'Client')
        self.__id = None
        self.__regAddressRecord = None
        self.__quotaRecord = None
        self.__regAddress = None
        self.__locAddressRecord = None
        self.__locAddress = None
        self.__documentRecord = None
        self.__workRecord = None
# create models
        self.contingentVisible = True
        self.rightOwnAreaOnly = False
        self.addModels('SocStatuses', CSocStatusesModel(self))
        self.addModels('SocStatusesSort', CSocStatusesModelSort(self, self.modelSocStatuses))
        self.modelSocStatuses = self.modelSocStatusesSort.model()
        self.addModels('Attaches',    CAttachesModel(self))
        self.addModels('DirectRelations', CDirectRelationsModel(self))
        self.addModels('BackwardRelations', CBackwardRelationsModel(self))
        self.addModels('WorkHurts',   CWorkHurtsModel(self))
        self.addModels('WorkHurtFactors', CWorkHurtFactorsModel(self))
        #self.modelWorkHurts.setFactorsModel(self.modelWorkHurtFactors)
        self.addModels('IdentificationDocs',  CIdentificationDocsModel(self))
        self.addModels('Policies',  CPoliciesModel(self))
        self.addModels('PersonalInfo',  CPersonalInfoModel(self))
        self.addModels('StatusObservation', CStatusObservationModel(self))
        self.addModels('PersonalInfo',  CPersonalInfoModel(self))
        self.addModels('Contacts',    CClientContactsModel(self))
        self.addModels('Allergy', CAllergyModel(self))
        self.addModels('IntoleranceMedicament', CIntoleranceMedicamentModel(self))
        self.addModels('NormalParameters', CNormalParametersModel(self))
        self.addModels('ClientIdentification', CClientIdentificationModel(self))
        self.addModels('ClientQuoting', CClientQuotingModel(self))
        self.addModels('ClientQuotingDiscussion', CClientQuotingDiscussionModel(self))
        self.addModels('Deposit', CDepositModel(self))
        self.addModels('ClientConsents', CClientConsentsInDocModel(self))
        self.addModels('Monitoring',     CMonitoringModel(self))
        self.addModels('ClientEpidCase', CClientEpidCaseModel(self))
        self.addModels('ClientAddressesReg', CAddressesTableModel(self, CAddressesTableModel.typeReg))
        self.addModels('ClientAddressesLoc', CAddressesTableModel(self, CAddressesTableModel.typeLoc))
        self.addModels('RiskFactors', CRiskFactorsModel(self))
        self.addModels('Research', CClientResearchModel(self))
        self.addModels('ActiveDispensary', CClientActiveDispensaryModel(self))
        self.addModels('Dangerous', CClientDangerousModel(self))
        self.addModels('ForcedTreatment', CClientForcedTreatmentModel(self))
        self.addModels('Suicide', CClientSuicideModel(self))
        self.addModels('ContingentKind', CClientContingentKindModel(self))
        self.addModels('Hospitalization', CClientHospitalizationModel(self))

# ui
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setObjectName('ClientEditDialog')
        self.edtBirthDate.setHighlightRedDate(False)
        self.edtWorkOrganisationINN.setBackgroundRole(QtGui.QPalette.Window)
        self.edtWorkOrganisationOGRN.setBackgroundRole(QtGui.QPalette.Window)
        self.edtOKVEDName.setBackgroundRole(QtGui.QPalette.Window)
        self.tabPassport.setFocusProxy(self.chkRegKLADR)
        self.tabSocStatus.setFocusProxy(self.tblSocStatuses)
        self.tabAttach.setFocusProxy(self.tblAttaches)
        self.tabRelations.setFocusProxy(self.tblDirectRelations)
        self.tabWork.setFocusProxy(self.btnSelectWorkOrganisation)
        self.tabPassport.setFocusProxy(self.tblContacts)
        self.tabFeature.setFocusProxy(self.tblAllergy)
        self.tabFeature.setFocusProxy(self.tblIntoleranceMedicament)
        self.tabFeature.setFocusProxy(self.tblNormalParameters)
        self.tabResearch.setFocusProxy(self.tblResearch)
        self.tabContingentKind.setFocusProxy(self.tblContingentKind)
        self.tabIdentification.setFocusProxy(self.tblClientIdentification)
        self.btnSearchPolicy.setEnabled(QtGui.qApp.identServiceEnabled())
        self.tabDeposit.setFocusProxy(self.tblDeposit)
        self.tabMonitoring.setFocusProxy(self.tblMonitoring)
        self.btnSearchClientAttach.setEnabled(QtGui.qApp.checkGlobalPreference(u'23:useAttachWS', u'да'))
        self.createApplyButton()
        if forceBool(QtGui.qApp.preferences.appPrefs.get('ScanPromobotEnable')):
            self.createScanButton()

        self.tabPassport.setEnabled(QtGui.qApp.userHasRight(urEnableTabPassport))  # Редактирование Паспортные данные
        self.tabSocStatus.setEnabled(QtGui.qApp.userHasRight(urEnableSocStatus))  # Редактирование Соц.статус
        self.tblAttaches.setEnabled(QtGui.qApp.userHasRight(urEnableClientAttach) or QtGui.qApp.userHasRight(urRegEditClientAttachEndDateOwnAreaOnly) or QtGui.qApp.userHasRight(urRegCreateClientAttachOwnAreaOnly))  # Редактирование Прикрепление
        self.tabWork.setEnabled(QtGui.qApp.userHasRight(urEnableTabWork))  # Редактирование Занятость

        self.tabChangeJournal.setEnabled(QtGui.qApp.userHasRight(urEnableTabChangeJournalInfo))  # Редактирование Журнала изменений
        self.tabDocsIdentification.setEnabled(QtGui.qApp.userHasRight(urEnableTabDocs))  # Редактирование Документы
        self.tabDocsPolicy.setEnabled(QtGui.qApp.userHasRight(urEnableTabClientPolicy))  # Редактирование Полисы
        self.tabAddresses.setEnabled(QtGui.qApp.userHasRight(urEnableTabClientAddress))  # Редактирование Адреса
        self.tabPersonalInfo.setEnabled(QtGui.qApp.userHasRight(urRegEditClientHistory))  # Редактирование Истории данных пациента(ФИО)

        self.tabFeature.setEnabled(QtGui.qApp.userHasRight(urEnableTabFeature))  # Редактирование Особенности
        self.tabResearch.setEnabled(QtGui.qApp.userHasRight(urEnableTabResearch))  # Редактирование Обследования
        self.tabDangerous.setEnabled(QtGui.qApp.userHasRight(urEnableTabDangerous))  # Редактирование Общ. опасность
        self.tabContingentKind.setEnabled(QtGui.qApp.userHasRight(urEnableTabContingentKind) or QtGui.qApp.userHasRight(urRegEditClientContingentKindOpenOwnAreaOnly) or QtGui.qApp.userHasRight(urRegEditClientContingentKindClosedOwnAreaOnly) or QtGui.qApp.userHasRight(urRegCreateClientContingentKindOwnAreaOnly))  # Редактирование Контингент
        self.tabIdentification.setEnabled(QtGui.qApp.userHasRight(urEnableTabIdentification))  # Редактирование Идентификаторы
        self.tabRelations.setEnabled(QtGui.qApp.userHasRight(urEnableTabRelations))  # Редактирование Связи
        self.tabContacts.setEnabled(QtGui.qApp.userHasRight(urEnableTabContacts))  # Редактирование Прочее
        self.tabQuoting.setEnabled(QtGui.qApp.userHasRight(urEnableTabQuoting))  # Редактирование Квоты
        self.tabDeposit.setEnabled(QtGui.qApp.userHasRight(urEnableTabDeposit))  # Редактирование Депозитная карта
        self.tabConsent.setEnabled(QtGui.qApp.userHasRight(urEnableTabConsent))  # Редактирование Согласия
        self.tabMonitoring.setEnabled(QtGui.qApp.userHasRight(urEnableTabClientMonitoring))  # Редактирование Мониторинг
        self.tabEpidCase.setEnabled(QtGui.qApp.userHasRight(urEnableTabClientEpidemic))  # Редактирование ЭпидНаблюдение
        self.tabHospitalization.setEnabled(QtGui.qApp.userHasRight(urRegEditClientHospitalization))  # имеет доступ к вкладке "Сведения о госпитализациях"

        self.userTabWidgetRights(self.tabSocStatus, urRegEditClientVisibleTabSocStatus)  # Видит вкладку Соц.статус
        self.userTabWidgetRights(self.tabAttach, urRegEditClientVisibleTabAttach)  # Видит вкладку Прикрепление
        self.userTabWidgetRights(self.tabWork, urRegEditClientVisibleTabWork)  # Видит вкладку Занятость
        self.userTabWidgetRights(self.tabChangeJournal, urRegEditClientVisibleTabChangeJournalInfo)  # Видит вкладку Журнал изменений
        self.userTabWidgetRights(self.tabFeature, urRegEditClientVisibleTabFeature)  # Видит вкладку Особенности
        self.userTabWidgetRights(self.tabResearch, urRegEditClientVisibleTabResearch)  # Видит вкладку Обследования
        self.userTabWidgetRights(self.tabDangerous, urRegEditClientVisibleTabDangerous)  # Видит вкладку Общ. опасность

        # Видит вкладку Контингент
        if QtGui.qApp.userHasRight(urRegEditClientVisibleTabContingentKind):
            self.userTabWidgetRights(self.tabContingentKind, urRegEditClientVisibleTabContingentKind)
        elif QtGui.qApp.userHasRight(urRegReadClientVisibleContingentKindOwnAreaOnly) and (self.rightOwnAreaOnly and self.contingentVisible):
            self.userTabWidgetRights(self.tabContingentKind, urRegReadClientVisibleContingentKindOwnAreaOnly)
        else:
            self.tabWidget.removeTab(self.tabWidget.indexOf(self.tabContingentKind))

        self.userTabWidgetRights(self.tabIdentification, urRegEditClientVisibleTabIdentification)  # Видит вкладку Идентификаторы
        self.userTabWidgetRights(self.tabRelations, urRegEditClientVisibleTabRelations)  # Видит вкладку Связи
        self.userTabWidgetRights(self.tabContacts, urRegEditClientVisibleTabContacts)  # Видит вкладку Прочее
        self.userTabWidgetRights(self.tabQuoting, urRegEditClientVisibleTabQuoting)  # Видит вкладку Квоты
        self.userTabWidgetRights(self.tabDeposit, urRegEditClientVisibleTabDeposit)  # Видит вкладку Депозитная карта
        self.userTabWidgetRights(self.tabConsent, urRegEditClientVisibleTabConsent)  # Видит вкладку Согласия
        self.userTabWidgetRights(self.tabMonitoring, urRegEditClientVisibleTabMonitoring)  # Видит вкладку Мониторинг
        self.userTabWidgetRights(self.tabEpidCase, urRegEditClientVisibleTabEpidemic)  # Видит вкладку ЭпидНаблюдение

        self.userTabHistoryWidgetRights(self.tabDocsIdentification, urRegEditClientVisibleTabDocs)
        self.userTabHistoryWidgetRights(self.tabDocsPolicy, urRegEditClientVisiblePolicy)
        self.userTabHistoryWidgetRights(self.tabAddresses, urRegEditClientVisibleAddress)
        self.userTabHistoryWidgetRights(self.tabPersonalInfo, urRegEditClientVisibleHistory)

# tables to rb and combo-boxes
        self.cmbDocType.setTable('rbDocumentType', True, 'group_id IN (SELECT id FROM rbDocumentTypeGroup WHERE code=\'1\')')
        self.cmbLivingArea.setTable('rbLivingArea', True)
        self.cmbDeathReason.setTable('rbDeathReason', True)
        self.cmbDeathPlaceType.setTable('rbDeathPlaceType', True)
        self.cmbCompulsoryPolisType.setTable('rbPolicyType', True, u'isCompulsory')
        self.cmbCompulsoryPolisKind.setTable('rbPolicyKind', True)
        self.cmbVoluntaryPolisType.setTable('rbPolicyType', True, u'NOT isCompulsory')
        self.cmbVoluntaryPolisKind.setTable('rbPolicyKind', True)
        self.cmbSocStatusDocType.setTable('rbDocumentType', True, 'group_id IN (SELECT id FROM rbDocumentTypeGroup WHERE code IN (\'2\', \'5\', \'7\'))')
        self.cmbBloodType.setTable('rbBloodType', True)
        self.edtBloodTypeDate.canBeEmpty(True)
        self.cmbWorkOKVED.setAddNone(True)
        self.btnAttachedFiles.setTable('Client_FileAttach')
        self.cmbWorkPost.setTable('rbClientWorkPost')

# assign models
        self.setModels(self.tblSocStatuses, self.modelSocStatusesSort, self.selectionModelSocStatusesSort)
        self.tblSocStatuses.horizontalHeader().setClickable(False)  # TT3856 убрал сортировку ибо ее и изначально не было
        self.tblSocStatuses.setItemDelegate(CSortFilterProxyLocItemDelegate(self.tblSocStatuses))
        self.setModels(self.tblAttaches, self.modelAttaches, self.selectionModelAttaches)
        self.setModels(self.tblDirectRelations, self.modelDirectRelations, self.selectionModelDirectRelations)
        self.setModels(self.tblBackwardRelations, self.modelBackwardRelations, self.selectionModelBackwardRelations)
        self.setModels(self.tblWorkHurts, self.modelWorkHurts, self.selectionModelWorkHurts)
        self.setModels(self.tblWorkHurtFactors, self.modelWorkHurtFactors, self.selectionModelWorkHurtFactors)
        self.setModels(self.tblIdentificationDocs, self.modelIdentificationDocs, self.selectionModelIdentificationDocs)
        self.setModels(self.tblPolicies, self.modelPolicies, self.selectionModelPolicies)
        self.setModels(self.tblStatusObservation, self.modelStatusObservation, self.selectionModelStatusObservation)
        self.setModels(self.tblPersonalInfo, self.modelPersonalInfo, self.selectionModelPersonalInfo)
        self.setModels(self.tblContacts, self.modelContacts, self.selectionModelContacts)
        self.setModels(self.tblAllergy, self.modelAllergy, self.selectionModelAllergy)
        self.setModels(self.tblIntoleranceMedicament, self.modelIntoleranceMedicament, self.selectionModelIntoleranceMedicament)
        self.setModels(self.tblNormalParameters, self.modelNormalParameters, self.selectionModelNormalParameters)
        self.setModels(self.tblRiskFactors, self.modelRiskFactors, self.selectionModelRiskFactors)
        self.setModels(self.tblClientIdentification,  self.modelClientIdentification,  self.selectionModelClientIdentification)
        self.setModels(self.tblClientQuoting, self.modelClientQuoting, self.selectionModelClientQuoting)
        self.setModels(self.tblClientQuotingDiscussion, self.modelClientQuotingDiscussion, self.selectionModelClientQuotingDiscussion)
        self.setModels(self.tblDeposit, self.modelDeposit, self.selectionModelDeposit)
        self.setModels(self.tblClientConsents, self.modelClientConsents, self.selectionModelClientConsents)
        self.setModels(self.tblMonitoring, self.modelMonitoring, self.selectionModelMonitoring)
        self.setModels(self.tblAddressesReg, self.modelClientAddressesReg, self.selectionModelClientAddressesReg)
        self.setModels(self.tblAddressesLoc, self.modelClientAddressesLoc, self.selectionModelClientAddressesLoc)
        self.setModels(self.tblEpidCase, self.modelClientEpidCase, self.selectionModelClientEpidCase)
        self.setModels(self.tblResearch, self.modelResearch, self.selectionModelResearch)
        self.setModels(self.tblActiveDispensary, self.modelActiveDispensary, self.selectionModelActiveDispensary)
        self.setModels(self.tblDangerous, self.modelDangerous, self.selectionModelDangerous)
        self.setModels(self.tblForcedTreatment, self.modelForcedTreatment, self.selectionModelForcedTreatment)
        self.setModels(self.tblSuicide, self.modelSuicide, self.selectionModelSuicide)
        self.setModels(self.tblContingentKind, self.modelContingentKind, self.selectionModelContingentKind)
        self.setModels(self.tblHospitalization, self.modelHospitalization, self.selectionModelHospitalization)

# popup menus
        self.tblSocStatuses.addPopupDelRow()
        self.tblSocStatuses.addPopupRecordProperies()
        self.tblSocStatuses.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        if QtGui.qApp.userHasRight(urEnableClientAttach):
            self.tblAttaches.addPopupDelRow()
        self.tblAttaches.addPopupRecordProperies()
        self.tblEpidCase.addPopupDelRow()
        self.tblEpidCase.addPopupRecordProperies()
        self.tblMonitoring.addPopupDelRow()
        self.tblMonitoring.addPopupRecordProperies()
        self.tblDirectRelations.addPopupDelRow()
        self.tblDirectRelations.addPopupRecordProperies()
        self.tblDirectRelations.addRelativeClientEdit()
        self.tblBackwardRelations.addPopupDelRow()
        self.tblBackwardRelations.addPopupRecordProperies()
        self.tblBackwardRelations.addRelativeClientEdit()
        self.tblWorkHurts.addPopupDelRow()
        self.tblWorkHurtFactors.addPopupDelRow()
        self.addPopupDelRowHistory()
        self.tblIdentificationDocs.addPopupRecordProperies()
        self.tblPolicies.addPopupRecordProperies()
       # self.tblSocStatuses.addPopupRecordProperies()
        self.tblStatusObservation.addPopupRecordProperies()
        self.tblPersonalInfo.addPopupRecordProperies()
        self.tblContacts.addPopupDelRow()
        self.tblContacts.addPopupRecordProperies()
        self.tblAllergy.addPopupDelRow()
        self.tblAllergy.addPopupRecordProperies()
        self.tblDeposit.addPopupDelRow()
        self.tblDeposit.addPopupRecordProperies()
        self.tblIntoleranceMedicament.addPopupDelRow()
        self.tblIntoleranceMedicament.addPopupRecordProperies()
        self.tblNormalParameters.addPopupDelRow()
        self.tblNormalParameters.addPopupRecordProperies()
        self.tblRiskFactors.addPopupDelRow()
        self.tblRiskFactors.addPopupRecordProperies()
        self.tblClientIdentification.addPopupDelRow()
        self.tblClientIdentification.addPopupRecordProperies()
        self.tblClientIdentification.setDelRowsChecker(self.modelClientIdentification.delRowsChecker)
        self.tblClientQuoting.addPopupSelectAllRow()
        self.tblClientQuoting.addPopupClearSelectionRow()
        self.actDelClientQuotingRows = QtGui.QAction(u'Удалить выделенное', self.tblClientQuoting)
        self.tblClientQuoting.popupMenu().addAction(self.actDelClientQuotingRows)
        self.tblClientConsents.addPopupDelRow()
        self.tblHospitalization.addPopupDelRow()
        self.connect(self.actDelClientQuotingRows, SIGNAL('triggered()'), self.deleteClientQuotingRows)
#        self.tblClientQuoting.addPopupDelRow()
        self.tblClientQuoting.addPopupRecordProperies()
        self.actNewMessage = QtGui.QAction(u'Добавить сообщение', self.tblClientQuotingDiscussion)
        self.connect(self.actNewMessage, SIGNAL('triggered()'), self.newQuotaDiscussionEditor)
        self.actEditMessage = QtGui.QAction(u'Редактировать сообщение', self.tblClientQuotingDiscussion)
        self.connect(self.actEditMessage, SIGNAL('triggered()'), self.editQuotaDiscussionEditor)
        self.actDelMessage = QtGui.QAction(u'Удалить сообщение', self.tblClientQuotingDiscussion)
        self.connect(self.actDelMessage, SIGNAL('triggered()'), self.deleteQuotaDiscussionMessage)
        self.connect(self.tblAddressesReg.horizontalHeader(), SIGNAL('sectionClicked(int)'), self._setAddressOrderByColumn)
        self.connect(self.tblAddressesLoc.horizontalHeader(), SIGNAL('sectionClicked(int)'), self._setAddressOrderByColumn)
        if QtGui.qApp.gis_oms_enable():
            self.actGetAttachMOData = QtGui.QAction(u'Прикрепление в ФЕРЗЛ', self.tblAttaches)
            self.connect(self.actGetAttachMOData, SIGNAL('triggered()'), self.getAttachMOData)
            self.tblAttaches.addPopupAction(self.actGetAttachMOData)
            self.connect(self.tblAttaches._popupMenu, SIGNAL('aboutToShow()'), self.on_tblAttachesPopupMenuAboutToShow)
            self.btn_FERZL.setEnabled(True)
            self.btn_FERZL.setVisible(True)
            self.hide_show_btn_findNR()
        self.tblClientQuotingDiscussion.addPopupAction(self.actNewMessage)
        self.tblClientQuotingDiscussion.addPopupAction(self.actEditMessage)
        self.tblClientQuotingDiscussion.addPopupAction(self.actDelMessage)
        self.tblAttaches.setDelRowsChecker(self.tblAttaches_delChecker)
        self.tblResearch.addPopupDelRow()
        self.tblResearch.addPopupRecordProperies()
        self.tblActiveDispensary.addPopupDelRow()
        self.tblActiveDispensary.addPopupRecordProperies()
        self.tblDangerous.addPopupDelRow()
        self.tblDangerous.addPopupRecordProperies()
        self.tblForcedTreatment.addPopupDelRow()
        self.tblForcedTreatment.addPopupRecordProperies()
        self.tblSuicide.addPopupDelRow()
        self.tblSuicide.addPopupRecordProperies()
        if QtGui.qApp.userHasRight(urEnableTabContingentKind):
            self.tblContingentKind.addPopupDelRow()
        self.tblContingentKind.addPopupRecordProperies()

# default values
        self.cmbRegCity.setCode(QtGui.qApp.defaultKLADR())
        self.cmbLocCity.setCode(QtGui.qApp.defaultKLADR())
        self.edtBirthDate.setDate(QDate())
        self.edtAddressDate.setDate(QDate())
        self.edtBegDate.setDate(QDate().currentDate())
        self.edtEndDate.setDate(QDate())
# etc
        if not QtGui.qApp.userHasRight(urRegEditClientDeathDate):
            self.chkDeathDate.setEnabled(False)
            self.edtDeathDate.setEnabled(False)
            self.edtDeathTime.setEnabled(False)
            self.lblDeathReason.setEnabled(False)
            self.cmbDeathReason.setEnabled(False)
            self.lblDeathPlaceType.setEnabled(False)
            self.cmbDeathPlaceType.setEnabled(False)

        self.btnCopyPrevAddress.setEnabled(bool(CClientEditDialog.prevAddress))
        self.btnCopyPrevWork.setEnabled(bool(CClientEditDialog.prevWork))
        self.setupDirtyCather()
        self.setIsDirty(False)
        self.edtLastName.setFocus(Qt.OtherFocusReason)
        self.lblInfo.setWordWrap(True)
        self.lblMKBText.setWordWrap(True)
        self.edtDocDate.setDate(QDate())
        self.edtDocDate.setDateRange(QDate(1900, 1, 1), QDate(2200, 12, 31))

        self.edtCompulsoryPolisBegDate.setDate(QDate())
        self.edtCompulsoryPolisBegDate.setDateRange(QDate(1993, 1, 1), QDate(2200, 12, 31))
        self.edtCompulsoryPolisEndDate.setDate(QDate())
        self.edtCompulsoryPolisEndDate.setDateRange(QDate(1993, 1, 1), QDate(2200, 12, 31))
        self.edtVoluntaryPolisBegDate.setDate(QDate())
        self.edtVoluntaryPolisBegDate.setDateRange(QDate(1993, 1, 1), QDate(2200, 12, 31))
        self.edtVoluntaryPolisEndDate.setDate(QDate())
        self.edtVoluntaryPolisEndDate.setDateRange(QDate(1993, 1, 1), QDate(2200, 12, 31))
        self.tblAddressesReg.setOrder(0)
        self.tblAddressesLoc.setOrder(0)
        self.regAddressInfo = {}
        self.locAddressInfo = {}
        self.defaultAddressInfo = None
        self.clientHousesListDialog = {}
        self.currentClientId = 0
        self.clientSex = 0
        self.clientBirthDate = QDate()
        self.clientWorkOrgId = None
        self.clientPolicyInfoList = []
        self.isHBDialog = False
        self.isHBEditClientInfo = False
        self.orgId = QtGui.qApp.currentOrgId()
        self.clientRegHousesList = CClientHousesList(parent)
        self.clientLocHousesList = CClientHousesList(parent)
        # Preferences
        self.widgetsVisible()
        self.chkShowOnlyActiveSocStatuses.stateChanged.connect(self.on_chkShowOnlyActiveSocStatuses_stateChanged)
        chkActSocStat = getPref(QtGui.qApp.preferences.appPrefs, 'clientEditDialogChkShowOnlyActiveSocStatuses', False )
        self.chkShowOnlyActiveSocStatuses.setChecked(forceBool(chkActSocStat))
        self.socStatusChanged.connect(self.addPlanProfOsmotrSocStatusRecord,Qt.QueuedConnection)


    def on_chkShowOnlyActiveSocStatuses_stateChanged(self):
        if self.chkShowOnlyActiveSocStatuses.isChecked():
            self.tblSocStatuses.model().setFilter('endDate', QDate.currentDate(), CSortFilterProxyTableModel.MatchGreaterEqualorEmpty)
            self.on_selectionModelSocStatusesSort_currentChanged(QModelIndex(),QModelIndex())
        else:
            self.tblSocStatuses.model().clearFilters()
        setPref(QtGui.qApp.preferences.appPrefs, 'clientEditDialogChkShowOnlyActiveSocStatuses', self.chkShowOnlyActiveSocStatuses.isChecked())
        
    def on_tblAttachesPopupMenuAboutToShow(self):
        model = self.tblAttaches.model()
        isReadOnly = model.getReadOnly()
        rowCount = model.realRowCount() if hasattr(model, 'realRowCount') else model.rowCount()
        row = self.tblAttaches.currentIndex().row()
        self.actGetAttachMOData.setEnabled(0 <= row < rowCount and not isReadOnly)
        self.tblAttaches.on_popupMenu_aboutToShow()


    def widgetsVisible(self):
        isVisible = False
        if not QtGui.qApp.showingClientCardDeathDate():
            self.DeathDateWidget.setVisible(isVisible)
        if not QtGui.qApp.showingClientCardBirthTime():
            self.edtBirthTime.setVisible(isVisible)
        if not QtGui.qApp.showingClientCardSNILS():
            self.lblSNILS.setVisible(isVisible)
            self.edtSNILS.setVisible(isVisible)
        if not QtGui.qApp.showingClientCardCompulsoryPolisName():
            self.lblCompulsoryPolisName.setVisible(isVisible)
            self.edtCompulsoryPolisName.setVisible(isVisible)
        if not QtGui.qApp.showingClientCardCompulsoryPolisNote():
            self.lblCompulsoryPolisNote.setVisible(isVisible)
            self.edtCompulsoryPolisNote.setVisible(isVisible)
        if not QtGui.qApp.showingClientCardDocOrigin():
            self.lblDocOrigin.setVisible(isVisible)
            self.edtDocOrigin.setVisible(isVisible)
            self.lblDocOriginCode.setVisible(isVisible)
            self.edtDocOriginCode.setVisible(isVisible)
        if not QtGui.qApp.showingClientCardVoluntaryPolicy():
            self.lblVoluntaryPolicy.setVisible(isVisible)
            self.VoluntaryPolisWidget.setVisible(isVisible)
            self.lblVoluntaryPolisCompany.setVisible(isVisible)
            self.cmbVoluntaryPolisCompany.setVisible(isVisible)
            self.cmbVoluntaryPolisType.setVisible(isVisible)
            self.cmbVoluntaryPolisKind.setVisible(isVisible)
            self.lblVoluntaryPolisName.setVisible(isVisible)
            self.edtVoluntaryPolisName.setVisible(isVisible)
            self.lblVoluntaryPolisNote.setVisible(isVisible)
            self.edtVoluntaryPolisNote.setVisible(isVisible)
        else:
            if not QtGui.qApp.showingClientCardVoluntaryPolicyName():
                self.lblVoluntaryPolisName.setVisible(isVisible)
                self.edtVoluntaryPolisName.setVisible(isVisible)
            if not QtGui.qApp.showingClientCardVoluntaryPolicyNote():
                self.lblVoluntaryPolisNote.setVisible(isVisible)
                self.edtVoluntaryPolisNote.setVisible(isVisible)
        if not QtGui.qApp.showingClientCardTabAttach():
            self.tabWidget.removeTab(self.tabWidget.indexOf(self.tabAttach))
        if not QtGui.qApp.showingClientCardTabWork():
            self.tabWidget.removeTab(self.tabWidget.indexOf(self.tabWork))
        if not QtGui.qApp.showingClientCardTabQuoting():
            self.tabWidget.removeTab(self.tabWidget.indexOf(self.tabQuoting))
        if not QtGui.qApp.showingClientCardTabDeposit():
            self.tabWidget.removeTab(self.tabWidget.indexOf(self.tabDeposit))
        if not QtGui.qApp.showingClientCardTabSocStatus():
            self.tabWidget.removeTab(self.tabWidget.indexOf(self.tabSocStatus))
        if not QtGui.qApp.showingClientCardTabChangeJournal():
            self.tabWidget.removeTab(self.tabWidget.indexOf(self.tabChangeJournal))
        if not QtGui.qApp.showingClientCardTabFeature():
            self.tabWidget.removeTab(self.tabWidget.indexOf(self.tabFeature))
        if not QtGui.qApp.showingClientCardTabResearch():
            self.tabWidget.removeTab(self.tabWidget.indexOf(self.tabResearch))
        if not QtGui.qApp.showingClientCardTabDangerous():
            self.tabWidget.removeTab(self.tabWidget.indexOf(self.tabDangerous))
        if not QtGui.qApp.showingClientCardTabContingentKind():
            self.tabWidget.removeTab(self.tabWidget.indexOf(self.tabContingentKind))
        if not QtGui.qApp.showingClientCardTabHospitalization():
            self.tabWidget.removeTab(self.tabWidget.indexOf(self.tabHospitalization))
        if not QtGui.qApp.showingClientCardTabIdentification():
            self.tabWidget.removeTab(self.tabWidget.indexOf(self.tabIdentification))
        if not QtGui.qApp.showingClientCardTabRelations():
            self.tabWidget.removeTab(self.tabWidget.indexOf(self.tabRelations))
        if not QtGui.qApp.showingClientCardTabContacts():
            self.tabWidget.removeTab(self.tabWidget.indexOf(self.tabContacts))
        if not QtGui.qApp.showingClientCardTabConsent():
            self.tabWidget.removeTab(self.tabWidget.indexOf(self.tabConsent))
        if not QtGui.qApp.showingClientCardTabMonitoring():
            self.tabWidget.removeTab(self.tabWidget.indexOf(self.tabMonitoring))
        if not QtGui.qApp.showingClientCardTabEpidCase():
            self.tabWidget.removeTab(self.tabWidget.indexOf(self.tabEpidCase))
        if not QtGui.qApp.gis_oms_enable():
            self.btn_FERZL.setEnabled(False)
            self.btn_FERZL.setVisible(False)
            self.btn_findNR.setEnabled(False)
            self.btn_findNR.setVisible(False)


    def addPopupDelRowHistory(self):
        if QtGui.qApp.userHasRight(urRegEditClientHistory):
            self.tblIdentificationDocs.addPopupDelRow()
            self.tblPolicies.addPopupDelRow()
            # self.tblSocStatusDocs.addPopupDelRow()
            self.tblStatusObservation.addPopupDelRow()
            self.tblPersonalInfo.addPopupDelRow()
            self.tblAddressesReg.addPopupDelRow()
            self.tblAddressesLoc.addPopupDelRow()



    def createApplyButton(self):
        self.addObject('btnApply', QtGui.QPushButton(u'Применить', self))
        self.buttonBox.addButton(self.btnApply, QtGui.QDialogButtonBox.ActionRole)
        self.connect(self.btnApply, SIGNAL('clicked()'), self.on_btnApply_clicked)


    def createScanButton(self):
        self.addObject('btnScan', QtGui.QPushButton(u'Сканировать', self))
        self.buttonBox.addButton(self.btnScan, QtGui.QDialogButtonBox.ActionRole)
        self.connect(self.btnScan, SIGNAL('clicked()'), self.on_btnScan_clicked)



    def getRightOwnAreaOnly(self):
        return self.rightOwnAreaOnly


    def hasRightOwnAreaOnly(self, clientId):
        db = QtGui.qApp.db
        personId = QtGui.qApp.userId
        hasRight = False
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
                        self.contingentVisible = False
        else:
            hasRight = True
        return hasRight
        # return True

    @pyqtSignature('')
    def on_btnApply_clicked(self):
        if self.saveData():
            self.lock(self._tableName, self._id)
            buttons = QtGui.QMessageBox.Ok
            messageBox = QtGui.QMessageBox()
            messageBox.setWindowFlags(messageBox.windowFlags() | Qt.WindowStaysOnTopHint)
            messageBox.setWindowTitle(u'Внимание!')
            messageBox.setText(u'Данные сохранены')
            messageBox.setStandardButtons(buttons)
            messageBox.setDefaultButton(QtGui.QMessageBox.Ok)
            return messageBox.exec_()


    @pyqtSignature('')
    def on_btnScan_clicked(self):
        newData = QtGui.qApp.callWithWaitCursor(self, scanning)
        if newData:
            message = u'Фамилия: %s\nИмя: %s\nОтчество: %s\nПол: %s\nДата рождения: %s\nМесто рождения: %s\nТип документа: %s\nСерия: %s\nНомер: %s\nДата выдачи: %s\nКем выдан: %s\nКод подразделения: %s\n' % (
                newData['lastName'], newData['firstName'], newData['patrName'], formatSex(newData['sex']),
                newData['birthDate'].toString('dd.MM.yyyy') if newData['birthDate'] else '',
                newData['birthPlace'], newData['docTypeTitle'],
                newData['serial'], newData['number'],
                newData['issueDate'].toString('dd.MM.yyyy') if newData['issueDate'] else '',
                newData['docOrigin'], newData['docOriginCode'])
            if QtGui.QMessageBox().question(self,
                                            u'Обновление данных пациента',
                                            message,
                                            QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel,
                                            QtGui.QMessageBox.Cancel) == QtGui.QMessageBox.Ok:
                self.edtLastName.setText(newData['lastName'])
                self.edtFirstName.setText(newData['firstName'])
                self.edtPatrName.setText(newData['patrName'])
                if newData.get('birthDate', None):
                    self.edtBirthDate.setDate(newData['birthDate'])
                if newData['doc_type'] in ['rus.snils.type1', 'rus.snils.type2']:
                    self.edtSNILS.setText(newData['number'])
                elif newData['doc_type'] in ['rus.birth_certificate.type1', 'rus.birth_certificate.type2',
                                             'rus.passport.national']:
                    self.cmbDocType.setValue(newData['docTypeId'])
                    self.edtDocSerialLeft.setText(newData['serialLeft'])
                    self.edtDocSerialRight.setText(newData['serialRight'])
                    self.edtDocNumber.setText(newData['number'])
                    self.edtDocDate.setDate(newData['issueDate'])
                    self.edtDocOrigin.setText(newData['docOrigin'])
                    self.edtDocOriginCode.setText(newData['docOriginCode'])
                    self.edtBirthPlace.setText(newData['birthPlace'])
                    self.cmbSex.setCurrentIndex(newData['sex'])


    def _setAddressOrderByColumn(self, column):
        type = self.tabWidgetAddresses.currentIndex()
        if type:
            table = self.tblAddressesLoc
        else:
            table = self.tblAddressesReg
        table.setOrder(column)
        order = table.order() if table.order() else ['ClientAddress.createDatetime ASC']
        db = QtGui.qApp.db
        tableCA = db.table('ClientAddress')
        tablePerson = db.table('vrbPerson')
        tableQuery = tableCA.leftJoin(tablePerson, tablePerson['id'].eq(tableCA['createPerson_id']))
        idList = db.getDistinctIdList(tableQuery, 'ClientAddress.id',
                                      [tableCA['deleted'].eq(0), tableCA['type'].eq(type),
                                       tableCA['client_id'].eq(self.itemId())], order)
        table.setIdList(idList)

    # WFT?
    def setHBEditClientInfoRight(self, isHBEditClientInfo, isHBDialog):
        self.isHBDialog = isHBDialog
        self.isHBEditClientInfo = isHBEditClientInfo

# WFT? у нас есть редактирование события из карточки пациента?
    def getHBUpdateEventRight(self):
        if self.isHBDialog:
            if not self.isHBEditClientInfo:
                QtGui.QMessageBox.warning( self,
                                         u'Внимание!',
                                         u'Нет права на редактирование события!',
                                         QtGui.QMessageBox.Ok,
                                         QtGui.QMessageBox.Ok)
                return False
        return True

    # Проверка на доступ к отображению вкладок
    def userTabWidgetRights(self, tab, right):
        if not QtGui.qApp.userHasRight(right):
            self.tabWidget.removeTab(self.tabWidget.indexOf(tab))

    # Проверка на доступ к отображению вкладок
    def userTabHistoryWidgetRights(self, tab, right):
        if not QtGui.qApp.userHasRight(right):
            self.tabChangeJournalInfo.removeTab(self.tabChangeJournalInfo.indexOf(tab))

    #Возвращает последний полис СМК
    def getPolicy(self,policy):
        hicId = self.cmbCompulsoryPolisCompany.value()
        if hicId:
            db = QtGui.qApp.db
            stmt="""select infisCode,smocode from Organisation
                    where Organisation.id='%s'"""%hicId
            query=db.query(stmt)
            while query.next():
                policy.smo_localcode=forceString(query.record().value('infisCode'))
                policy.smo_globalcode=forceString(query.record().value('smocode'))
                policy.policseria = forceString(self.edtCompulsoryPolisSerial.text())
                policy.policnum=forceString(self.edtCompulsoryPolisNumber.text())
                stmt="""select federalCode from rbPolicyKind where rbPolicyKind.id='%s'"""%forceString(self.cmbCompulsoryPolisKind.value())
                query=db.query(stmt)
                while query.next():
                    policy.polictype=forceString(query.record().value('federalCode'))
                policy.begindate=forceString(self.edtCompulsoryPolisBegDate.date().toString('yyyy-MM-dd'))
                policy.enddate=forceString(self.edtCompulsoryPolisEndDate.date().toString('yyyy-MM-dd'))


    #Устанавливает полис пациенту
    def setPolicy(self,globalcode,regionalcode,policyTypeId,policySerial,policyNumber,begindate,enddate):
        hicId=None
        #Ищем страховую компанию по коду ИНФИС
        db = QtGui.qApp.db
        if regionalcode:
            stmt="""select id from Organisation
                    where Organisation.`isInsurer`=1 and Organisation.`deleted`=0
                        and Organisation.`infisCode`='%s'"""%regionalcode
            query=db.query(stmt)
            if query.size()==1:
                while query.next():
                    hicId=query.record().value('id')
                    break
        #Если не нашли, то пробуем искать по коду СМО
        if globalcode and not hicId:
            stmt="""select id from Organisation
                    where Organisation.`isInsurer`=1 and Organisation.`deleted`=0
                        and Organisation.`smocode`='%s'"""%globalcode
            query=db.query(stmt)
            if query.size()==1:
                while query.next():
                    hicId=query.record().value('id')
                    break
        if hicId:
            self.cmbCompulsoryPolisCompany.setValue(hicId)
            if policySerial:
                self.edtCompulsoryPolisSerial.setText(policySerial)
            else:
                self.edtCompulsoryPolisSerial.clear()
            if policyNumber:
                self.edtCompulsoryPolisNumber.setText(policyNumber)
            else:
                self.edtCompulsoryPolisNumber.clear()
            self.cmbCompulsoryPolisType.setValue(0)
            stmt="""select id from rbPolicyKind where rbPolicyKind.`federalCode`='%s'"""%policyTypeId
            query=db.query(stmt)
            kindId=0
            while query.next():
                kindId=query.record().value('id')
                break
            self.cmbCompulsoryPolisKind.setValue(forceInt(kindId))
            self.syncPolicy(True)
            row = self.modelPolicies.getCurrentCompulsoryPolicyRow(policySerial, policyNumber)
            self.modelPolicies.setValue(row, 'begDate', toVariant(begindate))
            self.modelPolicies.setValue(row, 'endDate', toVariant(enddate))
            if not begindate:
                begindate = QDate()
            if not enddate:
                enddate = QDate()
            self.edtCompulsoryPolisBegDate.setDate(QDate(begindate))
            self.edtCompulsoryPolisEndDate.setDate(QDate(enddate))


    #Устанавливливает документ УЛ пациенту
    def setDoc(self,code,seria,number,passdate,enddate,docorg,note):
        documentType_id=0
        isnew=0
        db = QtGui.qApp.db
        stmt="""select rbDocumentType.id from rbDocumentType
                inner join rbDocumentTypeGroup on rbDocumentTypeGroup.id = rbDocumentType.group_id and rbDocumentTypeGroup.code='1'
                where rbDocumentType.regionalCode='%s'"""%code
        query=db.query(stmt)
        while query.next():
            documentType_id=forceInt(query.record().value('id'))
            break
        if documentType_id:
            for item in self.modelIdentificationDocs.items():
                if forceInt(item.value('documentType_id'))==documentType_id:
                    record=item
                    break
            else:
                record = self.modelIdentificationDocs.getEmptyRecord()
                isnew=1
            record.setValue('documentType_id', QVariant(documentType_id))
            if seria:
                record.setValue('serial', forceString(seria))
            else:
                record.setValue('serial', forceString(''))
            if number:
                record.setValue('number', forceString(number))
            else:
                record.setValue('number', forceString(''))
            if passdate:
                record.setValue('date', QVariant(QDate(passdate)))
            else:
                record.setValue('date', QVariant(QDate()))
            if docorg:
                record.setValue('origin', forceString(docorg))
            else:
                record.setValue('origin', forceString(''))
            if isnew:
                self.modelIdentificationDocs.items().append(record)
            self.modelIdentificationDocs.emit(SIGNAL("layoutChanged()"))
            self.setDocumentRecord(record)

    #Возвращает социальный статус
    def getSocStatus(self,classId):
        for item in self.modelSocStatuses.items():
            if (forceInt(item.value('socStatusClass_id'))==classId):
                db = QtGui.qApp.db
                stmt="""select socCode from rbSocStatusType  where id=%s"""%forceInt(item.value('socStatusType_id'))
                query=db.query(stmt)
                while query.next():
                    return query.record().value('socCode')
        return None

    #Устанавливает соц. статус
    def setSocStatus(self,classId,code,docname=None,docnum=None,docser=None,issuedate=None,enddate=None,note=None):
        typeId=0
        db = QtGui.qApp.db
        stmt="""select t.id from `rbSocStatusType` as t
                inner join `rbSocStatusClassTypeAssoc` as a on  a.`class_id`=%s and a.type_id=t.id
                where t.`socCode`='%s'"""%(classId,code)
        query=db.query(stmt)
        while query.next():
            typeId=query.record().value('id')
            break
        isnew=0
        for item in self.modelSocStatuses.items():
            if (forceInt(item.value('socStatusClass_id'))==classId and forceInt(item.value('socStatusType_id'))==typeId):
                record=item
                break
        else:
            record = self.modelSocStatuses.getEmptyRecord()
            isnew=1
        if typeId:
            record.setValue('socStatusClass_id', QVariant(classId))
            record.setValue('socStatusType_id', QVariant(typeId))
            #Для льгот
            if classId==1:
                if issuedate:
                    record.setValue('begDate', QVariant(QDate(issuedate)))
                else:
                    record.setValue('begDate', QVariant(QDate()))
                if enddate:
                    record.setValue('endDate', QVariant(QDate(enddate)))
                else:
                    record.setValue('endDate', QVariant(QDate()))
                if docnum:
                    record.setValue('number', forceString(docnum))
                else:
                    record.setValue('number', forceString(''))
                if docser:
                    record.setValue('serial', forceString(docser))
                else:
                     record.setValue('serial', forceString(''))
                if note:
                    record.setValue('origin', forceString(note))
                else:
                    record.setValue('origin', forceString(''))
                if docnum or  docser or note:
                    record.setValue('documentType_id', QVariant(230))
                    if issuedate:
                        record.setValue('date', QVariant(QDate(issuedate)))
            if isnew:
                self.modelSocStatuses.items().append(record)
            self.modelSocStatuses.emit(SIGNAL("layoutChanged()"))


    def destroy(self):
        pass


    def saveData(self):
        if QtGui.qApp.userHasRight(urRegTabReadRegistry) and not QtGui.qApp.userHasRight(urRegTabWriteRegistry):
            QtGui.QMessageBox.warning(self,
                            u'Внимание',
                            u'Право только на чтение!',
                            QtGui.QMessageBox.Ok,
                            QtGui.QMessageBox.Ok)
            return False
        if QtGui.qApp.userHasRight(urRegTabWriteRegistry):
            self.addCitizenshipSocStatusRecord()
            return self.checkDataEntered() and self.save()
        return False


    def save(self):
        try:
            db = QtGui.qApp.db
            db.transaction()
            try:
                record = self.getRecord()
                id = db.insertOrUpdate('Client', record)
                regAddressRecord, regAddress, regAddressRecordChanged = self.getAddressRecord(id, 0)
                if regAddressRecordChanged and regAddressRecord is not None:
                    db.insertOrUpdate('ClientAddress', regAddressRecord)
                locAddressRecord, locAddress, locAddressRecordChanged = self.getAddressRecord(id, 1)
                if locAddressRecordChanged and locAddressRecord is not None:
                    db.insertOrUpdate('ClientAddress', locAddressRecord)

                self.modelAttaches.saveItems(id)
                self.modelDirectRelations.saveItems(id)
                self.modelBackwardRelations.saveItems(id)
                self.modelAllergy.saveItems(id)
                self.modelDeposit.saveItems(id)
                self.modelClientConsents.saveItems(id)
                self.modelIntoleranceMedicament.saveItems(id)
                self.modelNormalParameters.saveItems(id)
                self.modelRiskFactors.saveItems(id)
                self.modelResearch.saveItems(id)
                self.modelActiveDispensary.saveItems(id)
                self.modelDangerous.saveItems(id)
                self.modelForcedTreatment.saveItems(id)
                self.modelSuicide.saveItems(id)
                self.modelContingentKind.saveItems(id)
                self.modelHospitalization.saveItems(id)
                workRecord, work, workRecordChanged = self.getWorkRecord(id)
                if workRecordChanged and workRecord is not None:
                    isWillInserted = workRecord.isNull('id')
                    workRecordId = db.insertOrUpdate('ClientWork', workRecord)
                    if isWillInserted:
                        db.query(('UPDATE `ClientWork`'
                                  ' SET deleted = 1 '
                                  ' WHERE client_id = %d AND id != %d') % (id, workRecordId))
                elif workRecord is not None:
                    workRecordId = forceRef(workRecord.value('id'))
                else:
                    workRecordId = None
                if workRecordId is not None:
                    self.modelWorkHurts.saveItems(workRecordId)
                    self.modelWorkHurtFactors.saveItems(workRecordId)
                self.modelIdentificationDocs.cleanUpEmptyItems()
                self.modelIdentificationDocs.saveItems(id)
                self.syncPolicies()
                self.modelPolicies.cleanUpEmptyItems()
                self.modelPolicies.saveItems(id)
                self.modelPersonalInfo.saveItems(id)
                self.modelStatusObservation.saveItems(id)
                self.modelPersonalInfo.saveItems(id)
                self.modelContacts.saveItems(id)
                self.modelMonitoring.saveItems(id)
                self.modelClientEpidCase.saveItems(id)

                if regAddress['useKLADR']:
                    self.modelClientQuoting.setNewRegCityCode(regAddress['KLADRCode'])
                    self.modelClientQuoting.setNewRegDistrictCode(
                        getOKATO(regAddress['KLADRCode'], regAddress['KLADRStreetCode'], regAddress['number']))
                self.modelClientQuoting.saveItems(id)
                self.modelSocStatuses.saveItems(id)
                self.modelClientIdentification.saveItems(id)
                self.btnAttachedFiles.saveItems(id)
                # saveSurveillanceRemoveDeath(self.edtDeathDate.date(), id)
                db.commit()
            except:
                db.rollback()
                QtGui.qApp.logCurrentException()
                raise
            self.setItemId(id)
            self.__regAddressRecord = regAddressRecord
            self.__regAddress = regAddress
            self.__locAddressRecord = locAddressRecord
            self.__locAddress = locAddress
            deAttachDeath = False
            deAttachDeathId = db.translate('rbDeAttachType', 'name', u'Смерть', 'id')
            recordAttach = self.modelAttaches.items()
            for record in recordAttach:
                if deAttachDeathId == forceString(record.value('deAttachType_id')):
                    deAttachDeath = True
            if QtGui.qApp.defaultKLADR()[:2] == u'23' and forceBool(QtGui.qApp.preferences.appPrefs.get('SyncAttachmentsAfterSave', False)) and not deAttachDeath:
                self.syncAttachments()

            self.setIsDirty(False)
            CClientEditDialog.prevAddress = (smartDict(**regAddress),
                                             forceStringEx(regAddressRecord.value('freeInput')),
                                             smartDict(**locAddress),
                                            )
            CClientEditDialog.prevWork    = work
            QtGui.qApp.emitCurrentClientInfoChanged()
            return id
        except Exception, e:
            QtGui.qApp.logCurrentException()
            QtGui.QMessageBox.critical( self,
                                        u'',
                                        exceptionToUnicode(e),
                                        QtGui.QMessageBox.Close)
            return None
    
    
    def addCitizenshipSocStatusRecord(self):
        documentTypeId = self.cmbDocType.value()
        documentTypeDescr = getDocumentTypeDescr(documentTypeId)
        if not documentTypeDescr.isCitizenship:
            # тип документа не требует добавления гражданства
            return

        db = QtGui.qApp.db
        socStatusClassId = forceInt(db.translate('rbSocStatusClass', 'code', '8', 'id'))
        socStatusTypeId = forceInt(db.translate('rbSocStatusType', 'code', u'м643', 'id'))
        for item in self.modelSocStatuses.items():
            typeId = forceInt(item.value('socStatusType_id'))
            classId = forceInt(item.value('socStatusClass_id'))
            if typeId == socStatusTypeId and classId == socStatusClassId:
                # гражданство установлено вручную
                return

        record = self.modelSocStatuses.getEmptyRecord()
        record.setValue('socStatusClass_id', socStatusClassId)
        record.setValue('socStatusType_id', socStatusTypeId)
        self.modelSocStatuses.addRecord(record)
             
    def addPlanProfOsmotrSocStatusRecord(self):
        db = QtGui.qApp.db
        socStatusClassId = forceInt(db.translate('rbSocStatusClass', 'code', 'profilac', 'id'))
        socStatusTypeId = forceInt(db.translate('rbSocStatusType', 'code', u'prof_d', 'id'))
        for item in self.modelSocStatuses.items():
            typeId = forceInt(item.value('socStatusType_id'))
            classId = forceInt(item.value('socStatusClass_id'))
            if typeId == socStatusTypeId and classId == socStatusClassId:
                return

        record = self.modelSocStatuses.getEmptyRecord()
        record.setValue('socStatusClass_id', socStatusClassId)
        record.setValue('socStatusType_id', socStatusTypeId)
        self.modelSocStatuses.addRecord(record)
             

    def getDefaultAddress(self):
        regAddressRecord, regAddress, regAddressRecordChanged = self.getAddressRecord(None, 0)
        locAddressRecord, locAddress, locAddressRecordChanged = self.getAddressRecord(None, 1)
        return (smartDict(**regAddress),
                forceStringEx(regAddressRecord.value('freeInput')),
                smartDict(**locAddress),
                )


    def setDefaultAddressInfo(self, defaultAddressInfo):
        self.defaultAddressInfo = defaultAddressInfo


    def checkDeadConfirmation(self, clientId):
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        tableEventTypePurpose = db.table('rbEventTypePurpose')
        table = tableEvent.leftJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
        table = table.leftJoin(tableEventTypePurpose, tableEventTypePurpose['id'].eq(tableEventType['purpose_id']))
        condDeath = [tableEvent['deleted'].eq(0),
                              tableEventType['deleted'].eq(0),
                              tableEvent['client_id'].eq(clientId),
                              tableEventTypePurpose['code'].eq(5)
                              ]
        recordDeath = db.getRecordEx(table, ['NULL'], condDeath)
        return True if recordDeath else False


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        id = self.itemId()
        self.rightOwnAreaOnly = self.hasRightOwnAreaOnly(id)
        self.setClientId(id)
        self.edtLastName.setText(forceString(record.value('lastName')))
        self.edtFirstName.setText(forceString(record.value('firstName')))
        self.edtPatrName.setText(forceString(record.value('patrName')))
        self.edtBirthPlace.setText(forceString(record.value('birthPlace')))
        self.edtBirthDate.setDate(forceDate(record.value('birthDate')))

        #если дата начала карты не заполнено, проставляем текущую
        if not forceDate(record.value('begDate')):
            self.edtBegDate.setDate(QDate().currentDate())
        else:
            self.edtBegDate.setDate(forceDate(record.value('begDate')))
        if not forceDate(record.value('endDate')):
            self.edtEndDate.setDate(QDate())
        else:
            self.edtEndDate.setDate(forceDate(record.value('endDate')))
            
        deathDateTime = forceDateTime(record.value('deathDate'))
        if deathDateTime:
            self.chkDeathDate.setChecked(True)
        self.edtDeathDate.setDate(deathDateTime.date())
        self.edtDeathTime.setTime(deathDateTime.time())
        self.cmbDeathReason.setValue(forceRef(record.value('deathReason_id')))
        self.cmbDeathPlaceType.setValue(forceRef(record.value('deathPlaceType_id')))
        
        self.edtBirthTime.setTime(forceTime(record.value('birthTime')))
        self.edtBirthHeight.setValue(forceInt(record.value('birthHeight')))
        self.edtBirthWeight.setValue(forceInt(record.value('birthWeight')))
        self.edtBirthNumber.setValue(forceInt(record.value('birthNumber')))
        self.edtBirthGestationalAge.setValue(forceInt(record.value('birthGestationalAge')))
        self.edtMenarhe.setValue(forceInt(record.value('menarhe')))
        self.edtMenoPausa.setValue(forceInt(record.value('menoPausa')))
        self.cmbSex.setCurrentIndex(forceInt(record.value('sex')))
        self.edtSNILS.setText(forceString(record.value('SNILS')))
        self.edtNotes.setPlainText(forceString(record.value('notes')))

        if id:
            if not QtGui.qApp.userHasRight(urRegEditClientInfo):
                self.edtLastName.setEnabled(False)
                self.edtFirstName.setEnabled(False)
                self.edtPatrName.setEnabled(False)
                self.cmbSex.setEnabled(False)
                self.edtBirthDate.setEnabled(False)
                self.edtBirthTime.setEnabled(False)
            if not QtGui.qApp.userHasRight(urRegEditClientSnils):
                self.edtSNILS.setEnabled(False)

        self.setRegAddressRecord(getClientAddress(id, 0))
        self.setLocAddressRecord(getClientAddress(id, 1))
        self.setDocumentRecord(getClientDocument(id))
        workRecord = getClientWork(id)
        self.setWorkRecord(workRecord)
        if workRecord:
            self.modelWorkHurts.loadItems(forceRef(workRecord.value('id')))
            self.modelWorkHurtFactors.loadItems(forceRef(workRecord.value('id')))
        else:
            self.modelWorkHurts.clearItems()
            self.modelWorkHurtFactors.clearItems()
        self.modelSocStatuses.loadItems(id)
        self.modelAttaches.loadItems(id)
        self.modelDirectRelations.loadItems(id)
        self.modelDirectRelations.setClientId(id)
        self.modelDirectRelations.setRegAddressInfo(self.getParamsRegAddress())
        self.modelDirectRelations.setLogAddressInfo(self.getParamsLocAddress())
        self.modelDirectRelations.setDirectRelationFilter(self.cmbSex.currentIndex())
        self.modelBackwardRelations.loadItems(id)
        self.modelBackwardRelations.setClientId(id)
        self.modelBackwardRelations.setRegAddressInfo(self.getParamsRegAddress())
        self.modelBackwardRelations.setLogAddressInfo(self.getParamsLocAddress())
        self.modelBackwardRelations.setBackwardRelationFilter(self.cmbSex.currentIndex())
        self.modelIdentificationDocs.loadItems(id)
        self.modelPolicies.loadItems(id)
#        self.modelPolicies.cleanUpEmptyItems()
        self.on_modelPolicies_policyChanged()
        self.modelPersonalInfo.loadItems(id)
        self.modelStatusObservation.loadItems(id)
        self.modelPersonalInfo.loadItems(id)
        self.modelContacts.loadItems(id)
        self.cmbBloodType.setValue(forceRef(record.value('bloodType_id')))
        self.edtBloodTypeDate.setDate(forceDate(record.value('bloodDate')))
        self.edtBloodTypeNotes.setText(forceString(record.value('bloodNotes')))
        self.modelAllergy.loadItems(id)
        self.modelDeposit.loadItems(id)
        self.modelClientConsents.setClientId(id)
        self.modelClientConsents.loadItems(id)
        self.modelIntoleranceMedicament.loadItems(id)
        self.modelNormalParameters.loadItems(id)
        self.modelClientIdentification.loadItems(id)
        self.modelClientQuoting.loadItems(id)
        self.modelMonitoring.loadItems(id)
        self.modelClientEpidCase.loadItems(id)
        self.modelRiskFactors.loadItems(id)
        self.modelResearch.loadItems(id)
        self.modelActiveDispensary.loadItems(id)
        self.modelDangerous.loadItems(id)
        forcedTreatmentBegDate = forceDate(record.value('forcedTreatmentBegDate'))
        if forcedTreatmentBegDate.isValid():
            self.chkForcedTreatmentBegDate.setChecked(True)
            self.edtForcedTreatmentBegDate.setEnabled(True)
        else:
            self.chkForcedTreatmentBegDate.setChecked(False)
            self.edtForcedTreatmentBegDate.setEnabled(False)
        self.edtForcedTreatmentBegDate.setDate(forcedTreatmentBegDate)
        self.modelForcedTreatment.loadItems(id)
        self.modelSuicide.loadItems(id)
        self.modelContingentKind.loadItems(id)
        self.modelHospitalization.loadItems(id)
        if self.__regAddress:
            self.modelClientQuoting.setRegCityCode(self.__regAddress['KLADRCode'])
            self.modelClientQuoting.setDistrictCode(
                getOKATO(self.__regAddress['KLADRCode'], self.__regAddress['KLADRStreetCode'],
                         self.__regAddress['number']))
        self.setSelectedQuota()
        self.setIsDirty(False)
        self.regAddressInfo = {}
        self.locAddressInfo = {}
        self.on_btnUpdateFactSum_clicked()
        self.btnAttachedFiles.loadItems(id)


    def setClientId(self, clientId):
        self.clientWorkOrgId = None
        self.currentClientId = clientId if clientId else 0
        if self.currentClientId:
            self.clientWorkOrgId = getClientWork(self.currentClientId)
        if clientId:
            self.setWindowTitle(unicode(self.windowTitle()) + u' (код: %d)' % clientId)


    def getClientId(self):
        return self.currentClientId


    @pyqtSignature('int')
    def on_cmbSex_currentIndexChanged(self, sex):
        self.modelDirectRelations.setDirectRelationFilter(sex)
        self.modelBackwardRelations.setBackwardRelationFilter(sex)
        self.clientSex = sex
        self.syncPersonalInfo()


    @pyqtSignature('QDate')
    def on_edtBirthDate_dateChanged(self, date):
        self.clientBirthDate = date
        self.syncPersonalInfo()
        if self.edtBirthDate.date():
            self.hide_show_btn_findNR()


    @pyqtSignature('QDate')
    def on_edtBegDate_dateChanged(self, date):
        self.clientBegDate = date


    @pyqtSignature('QDate')
    def on_edtDeathDate_dateChanged(self, date):
        deathDate = forceDate(date)
        db = QtGui.qApp.db
        table = db.table('rbDeathReason')
        cond = []
        cond.append(db.joinOr([table['begDate'].isNull(), table['begDate'].le(deathDate)]))
        cond.append(db.joinOr([table['endDate'].isNull(), table['endDate'].ge(deathDate)]))
        self.cmbDeathReason.setFilter(db.joinAnd(cond))
        self.syncPersonalInfo()

    @pyqtSignature('int')
    def on_cmbDeathReason_currentIndexChanged(self, value):
        self.syncPersonalInfo()

    @pyqtSignature('int')
    def on_cmbDeathPlaceType_currentIndexChanged(self, value):
        self.syncPersonalInfo()


    @pyqtSignature('')
    def on_btnUpdateFactSum_clicked(self):
        self.modelDeposit.factSum = []
        contractIdOfDateList = {}
        for row, record in enumerate(self.modelDeposit._items):
            contractId = forceRef(record.value('contract_id'))
            contractDate = forceDate(record.value('contractDate'))
            dateList = contractIdOfDateList.get(contractId, [])
            if contractDate and contractDate not in dateList:
                dateList.append(pyDate(contractDate))
                contractIdOfDateList[contractId] = dateList

        for row, record in enumerate(self.modelDeposit._items):
            contractId = forceRef(record.value('contract_id'))
            contractDate = forceDate(record.value('contractDate'))
            dateList = contractIdOfDateList.get(contractId, [])
            dateList.sort()
            lenDateList = len(dateList)
            if lenDateList > 1:
                begDateContract = QDate(dateList[0])
                endDateContract = QDate(dateList[lenDateList-1])
            else:
                begDateContract = contractDate
                endDateContract = 0

            sumAction = 0.0
            sumItem = 0.0
            currentDate = QDate.currentDate()
            clientAge = calcAgeTuple(self.clientBirthDate, currentDate)
            if contractId:
                db = QtGui.qApp.db
                tableAction = db.table('Action')
                tableEvent = db.table('Event')
                tableAccountItem = db.table('Account_Item')

            #  payStatus != 0
                cond = [tableAction['deleted'].eq(0),
                        tableEvent['deleted'].eq(0),
                        tableAccountItem['deleted'].eq(0),
                        tableAction['contract_id'].eq(contractId),
                        tableAction['payStatus'].ne(0),
                        tableAccountItem['refuseType_id'].isNull()
                        ]
                if begDateContract:
                    cond.append(tableAction['begDate'].dateGe(begDateContract))
                if endDateContract:
                    cond.append(tableAction['begDate'].dateLt(endDateContract))
                if self.currentClientId:
                    cond.append(tableEvent['client_id'].eq(self.currentClientId))
                table = tableEvent.innerJoin(tableAction, tableEvent['id'].eq(tableAction['event_id']))
                table = table.innerJoin(tableAccountItem, tableAction['id'].eq(tableAccountItem['action_id']))
                records = db.getRecordListGroupBy(table, u'SUM(Account_Item.sum) AS sumAction, Action.contract_id', cond, u'Action.contract_id')
                for newRecord in records:
                    contractId = forceRef(newRecord.value('contract_id'))
                    sumAction = forceDouble(newRecord.value('sumAction'))

            #  payStatus == 0
                tableActionType = db.table('ActionType')
                tableActionTypeService = db.table('ActionType_Service')
                tableRBService = db.table('rbService')
                tableContractTariff = db.table('Contract_Tariff')
                cols = u'''SUM(IF(Action.amount > Contract_Tariff.amount AND Contract_Tariff.amount != 0, Contract_Tariff.amount * Contract_Tariff.price,
                Action.amount * Contract_Tariff.price)) AS sumItem, Action.contract_id'''
                cond = [tableAction['deleted'].eq(0),
                        tableEvent['deleted'].eq(0),
                        tableActionType['deleted'].eq(0),
                        tableContractTariff['deleted'].eq(0),
                        tableAction['contract_id'].eq(contractId),
                        tableContractTariff['master_id'].eq(contractId),
                        tableAction['payStatus'].eq(0),
                        tableContractTariff['tariffType'].eq(CTariff.ttActionAmount),
                        tableActionType['id'].eq(tableActionTypeService['master_id'])
                        ]
                if begDateContract:
                    cond.append(tableAction['begDate'].dateGe(begDateContract))
                if endDateContract:
                    cond.append(tableAction['begDate'].dateLt(endDateContract))
                if clientAge:
                    cond.append(db.joinOr([tableContractTariff['age'].eq(''), tableContractTariff['age'].ge(clientAge[3])]))
                if self.currentClientId:
                    cond.append(tableEvent['client_id'].eq(self.currentClientId))
                cond.append(db.joinOr([tableContractTariff['sex'].eq(0), tableContractTariff['sex'].eq(self.clientSex)]))
                table = tableEvent.innerJoin(tableAction, tableEvent['id'].eq(tableAction['event_id']))
                table = table.innerJoin(tableActionType, tableAction['actionType_id'].eq(tableActionType['id']))
                table = table.innerJoin(tableActionTypeService, tableAction['finance_id'].eq(tableActionTypeService['finance_id']))
                table = table.innerJoin(tableRBService, tableActionTypeService['service_id'].eq(tableRBService['id']))
                table = table.innerJoin(tableContractTariff, tableRBService['id'].eq(tableContractTariff['service_id']))
                records = db.getRecordListGroupBy(table, cols, cond, u'Action.contract_id')
                for newRecord in records:
                    contractId = forceRef(newRecord.value('contract_id'))
                    sumItem = forceDouble(newRecord.value('sumItem'))
            self.modelDeposit.factSum.append(sumAction + sumItem)

        self.getFactSumList()
        self.modelDeposit.reset()

    @pyqtSignature('QItemSelection, QItemSelection')
    def on_selectionModelContingentKind_selectionChanged(self, selected, deselected):
        if selected.indexes():
            record = self.modelContingentKind.getRecordByRow(selected.indexes()[0].row())
            if record:
                self.modelContingentKind.setRemovalReasonFilter(record)


    def getFactSumList(self):
        lenItems = len(self.modelDeposit._items)
        lenFactSum = len(self.modelDeposit.factSum)
        diff = lenFactSum-lenItems
        if diff < 0:
            self.modelDeposit.factSum.extend([0]*(-diff))
        elif diff > 0:
            self.modelDeposit.factSum.extend([0]*diff)


    def setRegAddressRecord(self, record):
        self.__regAddressRecord = record
        if record:
            addressId = forceRef(record.value('address_id'))
#            self.chkRegKLADR.setChecked(addressId is not None)
            if addressId:
                self.__regAddress = getAddress(addressId)
            else:
                self.__regAddress = None
            self.setRegAddress(self.__regAddress, forceString(record.value('freeInput')), forceRef(record.value('livingArea')), forceDate(record.value('addressDate')))
        else:
            self.chkRegKLADR.setChecked(False)
            self.__regAddress = None
            self.setRegAddress(self.__regAddress, '')



    def setRegAddress(self, regAddress, freeInput, livingArea=None, addressDate=None):
        self.chkRegKLADR.setChecked(regAddress!=None)
        self.edtRegFreeInput.setText(freeInput)
        self.cmbLivingArea.setValue(livingArea)
        self.cmbCompulsoryPolisCompany._popup.setRegAdress(regAddress)
        if regAddress:
            self.cmbRegCity.setCode(regAddress.KLADRCode)
            self.cmbRegStreet.setCmbName('cmbRegStreet')
            self.cmbRegStreet.setCity(regAddress.KLADRCode)
            self.cmbRegStreet.setCode(regAddress.KLADRStreetCode)
            self.edtRegHouse.setText(regAddress.number)
            self.edtRegCorpus.setText(regAddress.corpus)
            self.edtRegFlat.setText(regAddress.flat)
            self.edtAddressDate.setDate(addressDate)
        else:
            self.cmbRegCity.setCode(QtGui.qApp.defaultKLADR())
            self.cmbRegStreet.setCity(QtGui.qApp.defaultKLADR())
            self.cmbRegStreet.setCode('')
            self.edtRegHouse.setText('')
            self.edtRegCorpus.setText('')
            self.edtRegFlat.setText('')
            self.edtAddressDate.setDate(QDate())


    def setRegAddressRelation(self, regAddress):
        if regAddress:
            self.edtRegFreeInput.setText(regAddress.get('regFreeInput', u''))
            self.cmbRegCity.setCode(regAddress.get('regCity', u''))
            self.cmbRegStreet.setCode(regAddress.get('regStreet', u''))
            self.edtRegHouse.setText(regAddress.get('regHouse', u''))
            self.edtRegCorpus.setText(regAddress.get('regCorpus', u''))
            self.edtRegFlat.setText(regAddress.get('regFlat', u''))
            self.edtAddressDate.setDate(regAddress.get('addressDate', QDate()))
            self.cmbResident.setCurrentIndex(regAddress.get('resident', 0))


    def setLocAddressRecord(self, record):
        self.__locAddressRecord = record
        if record:
            resident = record.value('resident')
            if resident.isNull():
                self.cmbResident.setCurrentIndex(0)
            else:
                if forceInt(resident) == 0:
                    self.cmbResident.setCurrentIndex(1)
                elif forceRef(resident) == 1:
                    self.cmbResident.setCurrentIndex(2)

            addressId = forceRef(record.value('address_id'))
            if addressId:
                self.__locAddress = getAddress(addressId)
            else:
                self.__locAddress = None
            self.setLocAddress(self.__locAddress, forceString(record.value('freeInput')))
        else:
            self.__locAddress = None
            self.chkLocKLADR.setChecked(False)
            self.setLocAddress(self.__locAddress, '')


    def setLocAddress(self, locAddress, freeInput):
        self.chkLocKLADR.setChecked(locAddress!=None)
        self.edtLocFreeInput.setText(freeInput)
        if locAddress:
            self.cmbLocCity.setCode(locAddress.KLADRCode)
            self.cmbLocStreet.setCmbName('cmbLocStreet')
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


    def setLocAddressRelation(self, locAddress):
        if locAddress:
            self.cmbLocCity.setCode(locAddress.get('regCity', u''))
            self.cmbLocStreet.setCode(locAddress.get('regStreet', u''))
            self.edtLocHouse.setText(locAddress.get('regHouse', u''))
            self.edtLocCorpus.setText(locAddress.get('regCorpus', u''))
            self.edtLocFlat.setText(locAddress.get('regFlat', u''))


    def setDocumentRecord(self, record):
        self.__documentRecord = record
        if record:
            documentTypeId = forceRef(record.value('documentType_id'))
            serial = forceString(record.value('serial'))
            number = forceString(record.value('number'))
            date   = forceDate(record.value('date'))
            origin = forceString(record.value('origin'))
            originCode = forceString(record.value('originCode'))
        else:
            documentTypeId = None
            serial = ''
            number = ''
            date   = QDate()
            origin = ''
            originCode = ''

        documentTypeDescr = getDocumentTypeDescr(documentTypeId)
        serialLeft, serialRight = documentTypeDescr.splitDocSerial(serial)

        bs = self.edtDocSerialLeft.blockSignals(True)
        try:
            self.edtDocSerialLeft.blockSignals(True)
            self.edtDocSerialRight.blockSignals(True)
            self.edtDocNumber.blockSignals(True)
            self.edtDocDate.blockSignals(True)
            self.edtDocOrigin.blockSignals(True)
            self.edtDocOriginCode.blockSignals(True)

            #            self.edtDocSerialLeft.setRegExp('')
            #            self.edtDocSerialRight.setRegExp('')
            self.edtDocSerialLeft.setText(serialLeft)
            self.edtDocSerialRight.setText(serialRight)
            #            self.edtDocNumber.setRegExp('')
            self.edtDocNumber.setText(number)
            self.edtDocDate.setDate(date)
            self.edtDocOrigin.setText(origin)
            self.edtDocOriginCode.setEditText(originCode)
            self.cmbDocType.setValue(documentTypeId)
        finally:
            self.edtDocSerialLeft.blockSignals(bs)
            self.edtDocSerialRight.blockSignals(bs)
            self.edtDocNumber.blockSignals(bs)
            self.edtDocDate.blockSignals(bs)
            self.edtDocOrigin.blockSignals(bs)
            self.edtDocOriginCode.blockSignals(bs)


    def setPolicyRecord(self, record, isCompulsory):
        if record:
            serial = forceString(record.value('serial'))
            number = forceString(record.value('number'))
            insurer = forceRef(record.value('insurer_id'))
            insurerArea = forceString(QtGui.qApp.db.translate('Organisation', 'id', insurer, 'area'))
            polisType = forceRef(record.value('policyType_id'))
            polisKind = forceRef(record.value('policyKind_id'))
            name = forceString(record.value('name'))
            note = forceString(record.value('note'))
            begDate = forceDate(record.value('begDate'))
            endDate = forceDate(record.value('endDate'))
        else:
            serial = ''
            number = ''
            insurer = None
            insurerArea = ''
            polisType = None
            polisKind = None
            name = ''
            note = ''
            begDate = QDate()
            endDate = QDate()
        if isCompulsory:
            self.edtCompulsoryPolisSerial.setText(serial)
            self.edtCompulsoryPolisNumber.setText(number)
            self.updateCompulsoryPolicyCompanyArea([insurerArea])
            self.cmbCompulsoryPolisCompany.setValue(insurer, isFirst=True)
            self.cmbCompulsoryPolisType.setValue(polisType)
            self.cmbCompulsoryPolisKind.setValue(polisKind)
            self.edtCompulsoryPolisName.setText(name)
            self.edtCompulsoryPolisNote.setText(note)
            self.edtCompulsoryPolisBegDate.setDate(begDate)
            self.edtCompulsoryPolisEndDate.setDate(endDate)
        else:
            self.edtVoluntaryPolisSerial.setText(serial)
            self.edtVoluntaryPolisNumber.setText(number)
            self.updateVoluntaryPolicyCompanyArea([insurerArea])
            self.cmbVoluntaryPolisCompany.setValue(insurer)
            self.cmbVoluntaryPolisType.setValue(polisType)
            self.cmbVoluntaryPolisKind.setValue(polisKind)
            self.edtVoluntaryPolisName.setText(name)
            self.edtVoluntaryPolisNote.setText(note)
            self.edtVoluntaryPolisBegDate.setDate(begDate)
            self.edtVoluntaryPolisEndDate.setDate(endDate)


    def setWorkRecord(self, record):
        self.__workRecord = record
        if record:
            self.cmbWorkOrganisation.setValue(forceRef(record.value('org_id')))
            self.updateWorkOrganisationInfo()
            self.edtWorkOrganisationFreeInput.setText(forceString(record.value('freeInput')))
            self.edtWorkPost.setText(forceString(record.value('post')))
            self.cmbWorkPost.setValue(forceRef(record.value('post_id')))
            self.cmbWorkOKVED.setText(forceString(record.value('OKVED')))
            self.edtWorkStage.setValue(forceInt(record.value('stage')))
        else:
            self.cmbWorkOrganisation.setValue(None)
            self.updateWorkOrganisationInfo()
            self.edtWorkOrganisationFreeInput.setText('')
            self.edtWorkPost.setText('')
            self.cmbWorkPost.setCurrentIndex(0)
            self.cmbWorkOKVED.setText('')
            self.edtWorkStage.setValue(0)


    def setWork(self, work):
        if work:
            self.cmbWorkOrganisation.setValue(work['organisationId'])
            self.updateWorkOrganisationInfo()
            self.edtWorkOrganisationFreeInput.setText(work['freeInput'])
            self.edtWorkPost.setText(work['post'])
            self.cmbWorkPost.setValue(work['post_id'])
            self.cmbWorkOKVED.setText(work['OKVED'])
            self.edtWorkStage.setValue(work['stage'])
        else:
            self.cmbWorkOrganisation.setValue(None)
            self.updateWorkOrganisationInfo()
            self.edtWorkOrganisationFreeInput.setText('')
            self.edtWorkPost.setText('')
            self.cmbWorkPost.setCurrentIndex(0)
            self.cmbWorkOKVED.setText('')
            self.edtWorkStage.setValue(0)


    def getParamsRegAddress(self):
        self.regAddressInfo = {}
        self.regAddressInfo['regFreeInput'] = self.edtRegFreeInput.text()
        self.regAddressInfo['addressType'] = 0
        self.regAddressInfo['regCity'] = self.cmbRegCity.code()
        self.regAddressInfo['regStreet'] = self.cmbRegStreet.code()
        self.regAddressInfo['regHouse'] = self.edtRegHouse.text()
        self.regAddressInfo['regCorpus'] = self.edtRegCorpus.text()
        self.regAddressInfo['regFlat'] = self.edtRegFlat.text()
        return self.regAddressInfo


    def setParamsRegAddress(self, regAddressInfo):
        self.regAddressInfo = regAddressInfo


    def getParamsLocAddress(self):
        self.locAddressInfo = {}
        self.locAddressInfo['addressType'] = 1
        self.locAddressInfo['regCity'] = self.cmbLocCity.code()
        self.locAddressInfo['regStreet'] = self.cmbLocStreet.code()
        self.locAddressInfo['regHouse'] = self.edtLocHouse.text()
        self.locAddressInfo['regCorpus'] = self.edtLocCorpus.text()
        self.locAddressInfo['regFlat'] = self.edtLocFlat.text()
        return self.locAddressInfo


    def setParamsLocAddress(self, locAddressInfo):
        self.locAddressInfo = locAddressInfo


    def setClientDialogInfo(self, info):
        if info:
            self.edtLastName.setText(info.get('lastName', ''))
            self.edtFirstName.setText(info.get('firstName', ''))
            self.edtPatrName.setText(info.get('patrName', ''))
            birthDate = info.get('birthDate', None)
            if birthDate:
                self.edtBirthDate.setDate(birthDate)
            self.cmbSex.setCurrentIndex(info.get('sex', 0))
            self.edtSNILS.setText(info.get('SNILS', ''))
            docTypeId = info.get('docType', None)
            if docTypeId:
                self.cmbDocType.setValue(docTypeId)
                self.edtDocSerialLeft.setText(forceString(info.get('serialLeft', '')))
                self.edtDocSerialRight.setText(forceString(info.get('serialRight', '')))
                self.edtDocNumber.setText(forceString(info.get('docNumber', '')))
                self.edtDocDate.setDate(forceDate(info.get('docIssueDate', None)))
                self.edtDocOrigin.setText(forceString(info.get('docOrigin', '')))
                self.edtDocOriginCode.setText(forceString(info.get('docOriginCode', '')))
            addressType = info.get('addressType', None)
            if addressType == 0:
                self.cmbRegCity.setCode(info.get('regCity', ''))
                self.cmbRegStreet.setCode(info.get('regStreet', ''))
                self.edtRegHouse.setText(info.get('regHouse', ''))
                self.edtRegCorpus.setText(info.get('regCorpus', ''))
                self.edtRegFlat.setText(info.get('regFlat', ''))
                self.cmbLivingArea.setCode(info.get('livingArea', ''))
            elif addressType == 1:
                self.cmbLocCity.setCode(info.get('regCity', ''))
                self.cmbLocStreet.setCode(info.get('regStreet', ''))
                self.edtLocHouse.setText(info.get('regHouse', ''))
                self.edtLocCorpus.setText(info.get('regCorpus', ''))
                self.edtLocFlat.setText(info.get('regFlat', ''))
            self.cmbResident.setCurrentIndex(info.get('resident', 0))
            regAddress = info.get('regAddress', None)
            if regAddress:
                self.edtRegFreeInput.setText(regAddress)
                self.chkRegKLADR.setChecked(False)
            locAddress = info.get('locAddress', None)
            if locAddress:
                self.edtLocFreeInput.setText(locAddress)
                self.chkLocKLADR.setChecked(False)
            identCard = info.get('identCard')
            polisSerial = info.get('polisSerial', '') or (identCard.policy.serial if identCard and identCard.policy else '')
            polisNumber = info.get('polisNumber', '') or (identCard.policy.number if identCard and identCard.policy else '')
            polisCompany = info.get('polisCompany', None) or (identCard.policy.number if identCard and identCard.policy and identCard.policy.insurerId else None)
            polisType = info.get('polisType', None)
            polisKind = info.get('polisKind', None)
            polisBegDate = info.get('polisBegDate', None)
            polisEndDate = info.get('polisEndDate', None)
            polisTypeName = forceString(info.get('polisTypeName', ''))
            if polisNumber:
                if u'ДМС' in polisTypeName:
                    self.edtVoluntaryPolisSerial.setText(polisSerial)
                    self.edtVoluntaryPolisNumber.setText(polisNumber)
                    self.cmbVoluntaryPolisCompany.setValue(polisCompany)
                    self.cmbVoluntaryPolisType.setValue(polisType)
                else:
                    self.edtCompulsoryPolisSerial.setText(polisSerial)
                    self.edtCompulsoryPolisNumber.setText(polisNumber)
                    self.cmbCompulsoryPolisCompany.setValue(polisCompany)
                    self.cmbCompulsoryPolisType.setValue(polisType)
                    self.cmbCompulsoryPolisKind.setValue(polisKind)
                    if identCard and identCard.policy and identCard.policy.begDate:
                        self.edtCompulsoryPolisBegDate.setDate(identCard.policy.begDate)
                    elif polisBegDate:
                        self.edtCompulsoryPolisBegDate.setDate(polisBegDate)
                    if identCard and identCard.policy and identCard.policy.endDate:
                        self.edtCompulsoryPolisEndDate.setDate(identCard.policy.endDate)
                    elif polisEndDate:
                        self.edtCompulsoryPolisEndDate.setDate(polisEndDate)
            if identCard and identCard.SNILS:
                self.edtSNILS.setText(identCard.SNILS)
            contactType = info.get('contactType', '')
            contact = info.get('contact', '')
            if contact:
                typeContactId = forceRef(QtGui.qApp.db.translate('rbContactType', 'code', contactType if contactType else '1', 'id'))
                self.modelContacts.setDialogContact(typeContactId, contact)
            birthPlace = info.get('birthPlace', '')
            if birthPlace:
                self.edtBirthPlace.setText(birthPlace)



    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        record.setValue('lastName',  toVariant(nameCase(forceStringEx(self.edtLastName.text()))))
        record.setValue('firstName', toVariant(nameCase(forceStringEx(self.edtFirstName.text()))))
        record.setValue('patrName',  toVariant(nameCase(forceStringEx(self.edtPatrName.text()))))
        record.setValue('birthPlace',  toVariant(nameCase(forceStringEx(self.edtBirthPlace.text()))))
        record.setValue('birthDate', toVariant(self.edtBirthDate.date()))
        record.setValue('birthTime', toVariant(self.edtBirthTime.time()))
        record.setValue('birthHeight',toVariant(self.edtBirthHeight.value()))
        record.setValue('birthWeight',toVariant(self.edtBirthWeight.value()))
        record.setValue('birthNumber', toVariant(self.edtBirthNumber.value()))
        record.setValue('birthGestationalAge', toVariant(self.edtBirthGestationalAge.value()))
        record.setValue('menarhe', toVariant(self.edtMenarhe.value()))
        record.setValue('menoPausa', toVariant(self.edtMenoPausa.value()))
        record.setValue('sex',       toVariant(self.cmbSex.currentIndex()))
        record.setValue('SNILS',     toVariant(forceStringEx(self.edtSNILS.text()).replace('-','').replace(' ','')))
        record.setValue('notes',     toVariant(forceStringEx(self.edtNotes.toPlainText())))
        record.setValue('bloodType_id', toVariant(self.cmbBloodType.value()))
        record.setValue('bloodDate', toVariant(self.edtBloodTypeDate.date()))
        record.setValue('bloodNotes', toVariant(forceStringEx(self.edtBloodTypeNotes.text())))
        record.setValue('deathDate', toVariant(QDateTime(self.edtDeathDate.date(), self.edtDeathTime.time()) if self.chkDeathDate.isChecked() else None))
        record.setValue('deathReason_id', toVariant(self.cmbDeathReason.value() if self.chkDeathDate.isChecked() else None))
        record.setValue('deathPlaceType_id', toVariant(self.cmbDeathPlaceType.value() if self.chkDeathDate.isChecked() else None))
        record.setValue('begDate', toVariant(self.edtBegDate.date()))
        record.setValue('endDate', toVariant(self.edtEndDate.date()))
        record.setValue('forcedTreatmentBegDate', toVariant(self.edtForcedTreatmentBegDate.date() if self.chkForcedTreatmentBegDate.isChecked() else None))
        return record


    def getAddress(self, addressType):
        if addressType == 0:
            return { 'useKLADR'         : self.chkRegKLADR.isChecked(),
                     'KLADRCode'        : self.cmbRegCity.code(),
                     'KLADRStreetCode'  : self.cmbRegStreet.code() if self.cmbRegStreet.code() else '', # без этого наростают адреса
                     'number'           : forceStringEx(self.edtRegHouse.text()),
                     'corpus'           : forceStringEx(self.edtRegCorpus.text()),
                     'flat'             : forceStringEx(self.edtRegFlat.text()),
                     'freeInput'        : forceStringEx(self.edtRegFreeInput.text()),
                     'livingArea'       : self.cmbLivingArea.value(),
                     'addressDate'      : forceDate(self.edtAddressDate.date()),
                     'resident'         : None}
        else:
            return { 'useKLADR'         : self.chkLocKLADR.isChecked(),
                     'KLADRCode'        : self.cmbLocCity.code(),
                     'KLADRStreetCode'  : self.cmbLocStreet.code() if self.cmbLocStreet.code() else '', # без этого наростают адреса
                     'number'           : forceStringEx(self.edtLocHouse.text()),
                     'corpus'           : forceStringEx(self.edtLocCorpus.text()),
                     'flat'             : forceStringEx(self.edtLocFlat.text()),
                     'freeInput'        : forceStringEx(self.edtLocFreeInput.text()),
                     'livingArea'       : None,
                     'addressDate'      : None,
                     'resident'         : self.cmbResident.currentIndex()}


    def getAddressRecord(self,  clientId, addressType):
        address = self.getAddress(addressType)
        if address['useKLADR']:
            addressId = getAddressId(address)
        else:
            addressId = None
        oldAddressRecord = self.__regAddressRecord if addressType == 0 else self.__locAddressRecord

        if oldAddressRecord is not None:

            def checkEditResident():
                resNum = None
                resident = oldAddressRecord.value('resident')
                if resident.isNull():
                    resNum = 0
                else:
                    if forceInt(resident) == 0:
                        resNum = 1
                    elif forceRef(resident) == 1:
                        resNum = 2

                if resident.isNull():
                    if resident.isNull() and address['resident'] != 0:
                        return True
                    else:
                        return False
                else:
                    if forceInt(address['resident']) != resNum:
                        return True
                    else:
                        return False

            if addressType == 1:
                recordChanged = (addressId != forceRef(oldAddressRecord.value('address_id')) or
                                 address['freeInput'] != forceString(oldAddressRecord.value('freeInput')) or
                                 address['livingArea'] != forceRef(oldAddressRecord.value('livingArea')) or
                                 forceDate(address['addressDate']) != forceDate(
                            oldAddressRecord.value('addressDate')) or
                                 checkEditResident())
            else:
                recordChanged = (addressId != forceRef(oldAddressRecord.value('address_id')) or
                             address['freeInput'] != forceString(oldAddressRecord.value('freeInput')) or
                             address['livingArea'] != forceRef(oldAddressRecord.value('livingArea')) or
                             forceDate(address['addressDate']) != forceDate(oldAddressRecord.value('addressDate')))
        else:
            recordChanged = True

        if recordChanged:
            record = QtGui.qApp.db.record('ClientAddress')
            record.setValue('client_id',  toVariant(clientId))
            record.setValue('type',       toVariant(addressType))
            record.setValue('address_id', toVariant(addressId))
            record.setValue('freeInput',  toVariant(address['freeInput']))
            record.setValue('livingArea', toVariant(address['livingArea']))
            record.setValue('addressDate', toVariant(address['addressDate']))
            if addressType == 1:
                if address['resident'] == 0:
                    record.setValue('resident', toVariant(None))
                elif address['resident'] == 1:
                    record.setValue('resident', toVariant(0))
                elif address['resident'] == 2:
                    record.setValue('resident', toVariant(1))
        else:
            record = oldAddressRecord

        return record, address, recordChanged


    def getWorkRecord(self, clientId):
        organisationId = self.cmbWorkOrganisation.value()
        freeInput = u'' if organisationId else forceStringEx(self.edtWorkOrganisationFreeInput.text())
        post  = forceStringEx(self.edtWorkPost.text())
        postId = self.cmbWorkPost.value()
        OKVED = forceStringEx(self.cmbWorkOKVED.text())
        stage = self.edtWorkStage.value()

        work = {'organisationId': organisationId,
                'freeInput'     : freeInput,
                'post'          : post,
                'post_id'       : postId,
                'OKVED'         : OKVED,
                'stage'         : stage}

        if self.__workRecord is not None:
            recordChanged = (
                organisationId  != forceRef(self.__workRecord.value('org_id')) or
                freeInput       != forceString(self.__workRecord.value('freeInput')) or
                post            != forceString(self.__workRecord.value('post')) or
                OKVED           != forceString(self.__workRecord.value('OKVED')) or
                stage           != forceInt(self.__workRecord.value('stage')) or
                postId          != forceRef(self.__workRecord.value('post_id'))
                )
        else:
            recordChanged = True

        if recordChanged:
            record = QtGui.qApp.db.record('ClientWork')
            record.setValue('client_id',    toVariant(clientId))
            record.setValue('org_id',       toVariant(organisationId))
            record.setValue('freeInput',    toVariant(freeInput))
            record.setValue('post',         toVariant(post))
            record.setValue('post_id',      toVariant(postId))
            record.setValue('OKVED',        toVariant(OKVED))
            record.setValue('stage',        toVariant(stage))
        else:
            record = self.__workRecord

        return record, work, recordChanged


#    def replacePatient(self, patientId):
#        db = QtGui.qApp.db
#        patientRecord = db.getRecord(tblPatients, '*', patientId)
#        self.setRecord(patientRecord)


    def checkDataEntered(self):
        self.syncPolicies()
        birthDate = self.edtBirthDate.date()
        lastName = forceStringEx(self.edtLastName.text())
        isAnonymous = lastName.startswith('*')
        tinyChild = birthDate and birthDate.addMonths(2)>=QDate.currentDate()
        result = True
        result = result and (lastName or self.checkInputMessage(u'фамилию', False, self.edtLastName))
        if not isAnonymous:
            result = result and (isNameValid(lastName, True) or self.checkInputMessage(u'допустимую фамилию', False, self.edtLastName))
            if tinyChild:
                result = result and (isNameValid(self.edtFirstName.text()) or self.checkInputMessage(u'допустимое имя', True, self.edtFirstName))
                result = result and (isNameValid(self.edtPatrName.text()) or self.checkInputMessage(u'допустимое отчество', True, self.edtPatrName))
            else:
                result = result and (forceStringEx(self.edtFirstName.text()) or self.checkInputMessage(u'имя', False, self.edtFirstName))
                result = result and (isNameValid(self.edtFirstName.text()) or self.checkInputMessage(u'допустимое имя', False, self.edtFirstName))
                result = result and (forceStringEx(self.edtPatrName.text())  or self.checkInputMessage(u'отчество', True, self.edtPatrName))
                result = result and (isNameValid(self.edtPatrName.text()) or self.checkInputMessage(u'допустимое отчество', False, self.edtPatrName))
        result = result and self.checkSexEntered()
        result = result and (birthDate or self.checkInputMessage(u'дату рождения', False, self.edtBirthDate))
        result = result and self.checkBirthDateEntered()
#        result = result and (self.cmbSex.currentIndex() or self.checkInputMessage(u'пол', False, self.cmbSex))
        if QtGui.qApp.showingClientCardSNILS():
            result = result and checkSNILSEntered(self)
        result = result and self.checkDocEntered()
        result = result and self.checkDocsEntered()
        result = result and self.checkDocNumber()
        result = result and self.checkPolicyEntered(True)
        result = result and self.checkPolicyAffiliationOMS()
        result = result and self.checkEpidCases()
        if QtGui.qApp.showingClientCardVoluntaryPolicy():
            result = result and self.checkPolicyEntered(False)
        if QtGui.qApp.showingClientCardTabContacts():
            result = result and self.checkContacts()
        if QtGui.qApp.showingClientCardTabSocStatus():
            result = result and self.checkSocStatuses()
        result = result and self.checkDup()
        #if QtGui.qApp.isCheckClientHouses():
        isControlAddress = QtGui.qApp.isStrictCheckControlAddress()
        if isControlAddress:
            result = result and self.checkRegAddress()
            result = result and self.checkLocAddress()
        result = result and self.checkHouses()
        if QtGui.qApp.showingClientCardTabAttach():
            result = result and self.checkAttachesDataEntered()
        if QtGui.qApp.showingClientCardTabRelations():
            result = result and self.checkClientRelations(self.cmbSex.currentIndex())
        if QtGui.qApp.showingClientCardTabDeposit():
            result = result and self.checkClientDeposit()
        if QtGui.qApp.showingClientCardTabWork():
            result = result and self.checkWorkHurts()
        if QtGui.qApp.showingClientCardTabConsent():
            result = result and self.checkClientConsents()
        result = result and self.checkResearch()
        result = result and self.checkDangerous()
        result = result and self.checkContingentKind()
        result = result and self.checkClientContingentKind()
        return result


    def checkRegAddress(self):
        result = True
        if trim(self.edtRegFreeInput.text()):
            return True
        boolCorpus = (trim(self.edtRegFlat.text()) or trim(self.edtRegHouse.text()) or trim(self.edtRegCorpus.text()))
        result = result and (self.cmbRegCity.code() or self.checkStreetHouseMessage(u'Адрес регистрации. Введите населённый пункт.', not boolCorpus, self.cmbRegCity))
        if self.cmbRegStreet.count() > 0:
            result = result and (self.cmbRegStreet.code() or self.checkStreetHouseMessage(u'Адрес регистрации. Введите название улицы.', not boolCorpus, self.cmbRegStreet))
        result = result and (trim(self.edtRegFlat.text()) or self.checkStreetHouseMessage(u'Адрес регистрации. Введите номер квартиры.', True, self.edtRegFlat))
        result = result and (trim(self.edtRegHouse.text()) or self.checkStreetHouseMessage(u'Адрес регистрации. Введите номер дома.', not(trim(self.edtRegFlat.text()) or trim(self.edtRegCorpus.text()) or self.cmbRegStreet.code()), self.edtRegHouse))
        boolCorpus = (trim(self.edtRegFlat.text()) or trim(self.edtRegHouse.text()))
        if boolCorpus:
            result = result and (trim(self.edtRegCorpus.text()) or self.checkStreetHouseMessage(u'Адрес регистрации. Введите корпус.', True, self.edtRegCorpus))
        isRegAddressDate = QtGui.qApp.getRegAddressDate()
        if isRegAddressDate:
            birthDate = self.edtBirthDate.date()
            regAddressDate = self.edtAddressDate.date()
            result = result and (regAddressDate.isValid() or self.checkInputMessage(u'дату регистрации', isRegAddressDate==1, self.edtAddressDate))
            if not regAddressDate.isNull():
                result = result and (regAddressDate >= birthDate or self.checkValueMessage(u'Дата регистрации не может быть меньше даты рождения', False, self.edtAddressDate))
                result = result and (regAddressDate <= QDate.currentDate() or self.checkValueMessage(u'Дата регистрации не может быть больше текущей даты', False, self.edtAddressDate))
        return result


    def checkLocAddress(self):
        result = True
        if trim(self.edtRegFreeInput.text()):
            return True
        boolCorpus = (trim(self.edtLocFlat.text()) or trim(self.edtLocHouse.text()) or trim(self.edtLocCorpus.text()))
        result = result and (self.cmbLocCity.code() or self.checkStreetHouseMessage(u'Адрес проживания. Введите населённый пункт.', not boolCorpus, self.cmbLocCity))
        if self.cmbLocStreet.count() > 0:
            result = result and (self.cmbLocStreet.code() or self.checkStreetHouseMessage(u'Адрес проживания. Введите название улицы.', not boolCorpus, self.cmbLocStreet))
        result = result and (trim(self.edtLocFlat.text()) or self.checkStreetHouseMessage(u'Адрес проживания. Введите номер квартиры.', True, self.edtLocFlat))
        result = result and (trim(self.edtLocHouse.text()) or self.checkStreetHouseMessage(u'Адрес проживания. Введите номер дома.', not(trim(self.edtLocFlat.text()) or trim(self.edtLocCorpus.text()) or self.cmbLocStreet.code()), self.edtLocHouse))
        boolCorpus = (trim(self.edtLocFlat.text()) or trim(self.edtLocHouse.text()))
        if boolCorpus:
            result = result and (trim(self.edtLocCorpus.text()) or self.checkStreetHouseMessage(u'Адрес проживания. Введите корпус.', True, self.edtLocCorpus))
        return result


    def checkWorkHurts(self):
        for row, item in enumerate(self.modelWorkHurts.items()):
            if not forceRef(item.value('hurtType_id')):
                return self.checkInputMessage(u'вредность', False, self.tblWorkHurts, row, 0)
        return True


    def checkClientConsents(self):
        for row, item in enumerate(self.modelClientConsents.items()):
            if not forceRef(item.value('representerClient_id')):
                return self.checkInputMessage(u'подписавшего', False, self.tblClientConsents, row, 5)
        return True


    def checkClientContingentKind(self):
        for row, item in enumerate(self.modelContingentKind.items()):
            if not forceDate(item.value('begDate')):
                return self.checkInputMessage(u'дату постановки', False, self.tblContingentKind, row, 3)
        return True


    def checkHouses(self):
        result = True
        regHouse = forceString(self.edtRegHouse.text())
        regStreetCode = False
        if regHouse:
            regStreetCode = self.cmbRegStreet.code()
            if not regStreetCode:
                cityCode = self.cmbRegCity.code()
                regStreetCode = cityCode + u'000000'
            if regStreetCode:
                res = self.checkHouseList(regStreetCode, 0)
                if res:
                    base = self.clientRegHousesList.getCheckResult()
                    widgetHouse = self.edtRegHouse
                    result = result and self.checkStreetHouseMessage(u'Данные о номере дома по адресу %s %s, %s, %s отсутствуют в %s.'%(u'регистрации',  self.cmbRegCity.currentText(), self.cmbRegStreet.currentText(), regHouse, base), res == 1, widgetHouse)
        locHouse = forceString(self.edtLocHouse.text())
        if locHouse:
            locStreetCode = self.cmbLocStreet.code()
            if not locStreetCode:
                cityCode = self.cmbLocCity.code()
                locStreetCode = cityCode + u'000000'
            if locStreetCode:
                res = self.checkHouseList(locStreetCode, 1)
                if res:
                    base = self.clientLocHousesList.getCheckResult()
                    widgetHouse = self.edtLocHouse
                    result = result and self.checkStreetHouseMessage(u'Данные о номере дома по адресу %s %s, %s, %s отсутствуют в %s.'%(u'проживания',  self.cmbRegCity.currentText(), self.cmbRegStreet.currentText(), locHouse, base), res == 1, widgetHouse)
        return result


    def checkStreetHouseMessage(self, message, ignore, widget, row=None, column=None, detailWdiget=None, setFocus=True):
        messageBox = QtGui.QMessageBox.Ok
        if ignore:
            messageBox |= QtGui.QMessageBox.Ignore
        res = QtGui.QMessageBox.warning( self,
                                         u'Внимание!',
                                         message,
                                         messageBox,
                                         QtGui.QMessageBox.Ok)
        if res == QtGui.QMessageBox.Ok:
            if setFocus:
                self.setFocusToWidget(widget, row, column)
                if detailWdiget:
                    self.setFocusToWidget(detailWdiget, row, column)
            return False
        return True


    def checkClientDeposit(self):
        contractDateList = {}
        for row, record in enumerate(self.modelDeposit._items):
            contractIdNew = forceRef(record.value('contract_id'))
            # Без заполненного договора ругается констреинт
            if not bool(contractIdNew or self.checkInputMessage(u'договор', False, self.tblDeposit, row, record.indexOf('contract_id'))):
                return False
            contractDate = forceDate(record.value('contractDate'))
            if contractDate in contractDateList.keys():
                contractIdList = contractDateList.get(contractDate, None)
                if contractIdNew and contractIdList and contractIdNew in contractIdList:
                    return self.checkValueMessage(u'Не должно быть двух одинаковых договоров на одну дату в таблице', False, self.tblDeposit, row, record.indexOf('contract_id'))
                elif contractIdNew and contractIdList:
                   contractIdList.append(contractIdNew)
                   contractDateList[contractDate] = contractIdList
                elif contractIdNew and contractIdList:
                    contractDateList[contractDate] = [contractIdNew]
            else:
                contractDateList[contractDate] = [contractIdNew]
        return True


    def checkDeposit(self):
        from Events.ClientDepositDialog import CClientDepositDialog
        currentDate = QDate.currentDate()
        self.btnExit = False
        self.clientAge = calcAgeTuple(self.clientBirthDate, currentDate)
        sumAction = 0
        sumItem = 0
        contractIdList = {}
        serviceBool = False
        for row, record in enumerate(self.modelDeposit._items):
            contractId = forceRef(record.value('contract_id'))
            #contractDate = forceDate(record.value('contractDate'))
            sumAction = 0.0
            sumItem = 0.0
            currentDate = QDate.currentDate()
            if contractId:
                contractSum = forceDouble(record.value('contractSum'))
                #contractSumList = contractIdList.get((contractId, contractDate), 0)
                contractSumList = contractIdList.get(contractId, 0)
                contractSumList += contractSum
                #contractIdList[(contractId, contractDate)] = contractSumList
                contractIdList[contractId] = contractSumList

        db = QtGui.qApp.db
        tableAction = db.table('Action')
        tableEvent = db.table('Event')
        tableContract = db.table('Contract')
        tableAccountItem = db.table('Account_Item')
        tableActionType = db.table('ActionType')
        tableActionTypeService = db.table('ActionType_Service')
        tableRBService = db.table('rbService')
        tableContractTariff = db.table('Contract_Tariff')

        for contractKey, contractSum in contractIdList.items():
            #contractId, contractDate = contractKey
            contractId = contractKey
            if contractId:
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
#                if contractDate:
#                    cond.append(tableAction['begDate'].dateGe(contractDate))
#                    cond.append(tableAction['endDate'].dateLe(contractDate))
                if self.currentClientId:
                    cond.append(tableEvent['client_id'].eq(self.currentClientId))
                table = tableEvent.innerJoin(tableAction, tableEvent['id'].eq(tableAction['event_id']))
                table = table.innerJoin(tableAccountItem, tableAction['id'].eq(tableAccountItem['action_id']))
                records = db.getRecordListGroupBy(table, u'SUM(Account_Item.sum) AS sumAction', cond, u'Action.contract_id')
                if records:
                    newRecord = records[0]
                    sumAction = forceDouble(newRecord.value('sumAction'))

            #  payStatus == 0
                cols = u'''SUM(IF(Action.amount > Contract_Tariff.amount AND Contract_Tariff.amount != 0, Contract_Tariff.amount * Contract_Tariff.price,
                Action.amount * Contract_Tariff.price)) AS sumItem, Action.contract_id'''
                cond = [tableAction['deleted'].eq(0),
                        tableEvent['deleted'].eq(0),
                        tableActionType['deleted'].eq(0),
                        tableContractTariff['deleted'].eq(0),
                        tableAction['contract_id'].eq(contractId),
                        tableContractTariff['master_id'].eq(contractId),
                        tableAction['payStatus'].eq(0),
                        tableContractTariff['tariffType'].eq(CTariff.ttActionAmount),
                        tableActionType['id'].eq(tableActionTypeService['master_id'])
                        ]
#                if contractDate:
#                    cond.append(tableAction['begDate'].dateGe(contractDate))
#                    cond.append(tableAction['endDate'].dateLe(contractDate))
                if self.clientAge:
                    cond.append(db.joinOr([tableContractTariff['age'].eq(''), tableContractTariff['age'].ge(self.clientAge[3])]))
                if self.currentClientId:
                    cond.append(tableEvent['client_id'].eq(self.currentClientId))
                cond.append(db.joinOr([tableContractTariff['sex'].eq(0), tableContractTariff['sex'].eq(self.clientSex)]))
                table = tableEvent.innerJoin(tableAction, tableEvent['id'].eq(tableAction['event_id']))
                table = table.innerJoin(tableActionType, tableAction['actionType_id'].eq(tableActionType['id']))
                table = table.innerJoin(tableActionTypeService, tableAction['finance_id'].eq(tableActionTypeService['finance_id']))
                table = table.innerJoin(tableRBService, tableActionTypeService['service_id'].eq(tableRBService['id']))
                table = table.innerJoin(tableContractTariff, tableRBService['id'].eq(tableContractTariff['service_id']))
                records = db.getRecordListGroupBy(table, cols, cond, u'Action.contract_id')
                for newRecord in records:
                    contractId = forceRef(newRecord.value('contract_id'))
                    sumItem = forceDouble(newRecord.value('sumItem'))

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
                buttonBoxIgnore = False
                if limitExceeding and sumDeposit > limitExceeding and sumDeposit < limitOfFinancing:
                    buttonBoxIgnore = True

                if limitExceeding or limitOfFinancing:
                    if ((sumAction + sumItem) > limitExceeding or limitSum < sumDeposit):
                        CClientDepositDialog(self, self.currentClientId, self.clientAge, self.clientSex, buttonBoxIgnore, title=u'Превышение общей стоимости услуг по договору').exec_()
                        if (sumAction + sumItem) > limitExceeding and self.btnExit:
                            if buttonBoxIgnore:
                                return True
                            else:
                                return False
                        else:
                            return False
                elif (sumAction + sumItem) > contractSum:
                    CClientDepositDialog(self, self.currentClientId, self.clientAge, self.clientSex, buttonBoxIgnore, title=u'Превышение общей стоимости услуг по договору').exec_()
                    if (sumAction + sumItem) > limitExceeding and self.btnExit:
                        return True
                    else:
                        return False
        if serviceBool:
            CClientDepositDialog(self, self.currentClientId, self.clientAge, self.clientSex, True, title=u'Предел стоимости услуг по договору').exec_()
            if self.btnExit:
                return True
            else:
                return False

        return True


    def checkDocNumber(self):
        for row, item in enumerate(self.modelSocStatuses.items()):
            if forceRef(item.value('documentType_id')):
                if not forceString(item.value('number')):
                    if QtGui.QMessageBox.question( self,
                                           u'Внимание!',
                                           u'Для типа соц.статуса не введен номер документа.',
                                           QtGui.QMessageBox.Ok|QtGui.QMessageBox.Ignore,
                                           QtGui.QMessageBox.Ok) == QtGui.QMessageBox.Ok:
                        self.setFocusToWidget(self.tblSocStatuses, row, 0)
                        self.edtSocStatusDocNumber.setFocus(Qt.ShortcutFocusReason)
                        return False
        return True


    def checkSexEntered(self):
        currentSex = self.cmbSex.currentIndex()
        firstName = forceStringEx(self.edtFirstName.text())
        firstNameSex = forceInt(QtGui.qApp.db.translate('rdFirstName', 'name', firstName, 'sex')) if firstName else 0
        patrName = forceStringEx(self.edtPatrName.text())
        patrNameSex = forceInt(QtGui.qApp.db.translate('rdPatrName', 'name', patrName, 'sex')) if patrName else 0
        if firstNameSex and patrNameSex:
            if firstNameSex == patrNameSex:
                detectedSex = firstNameSex
            else:
                res = QtGui.QMessageBox.question( self,
                                                  u'Внимание!',
                                                  u'Конфликт имени и отчества.\nХотите исправить?',
                                                  QtGui.QMessageBox.Yes|QtGui.QMessageBox.No,
                                                  QtGui.QMessageBox.Yes)
                if res == QtGui.QMessageBox.Yes:
                    if currentSex == firstNameSex:
                       self.edtPatrName.setFocus(Qt.ShortcutFocusReason)
                    else:
                       self.edtFirstName.setFocus(Qt.ShortcutFocusReason)
                    return False
                detectedSex = 0
        else:
            detectedSex = max(firstNameSex, patrNameSex)

        if currentSex:
            if detectedSex and currentSex != detectedSex:
                res = QtGui.QMessageBox.question( self,
                                                 u'Внимание!',
                                                 u'Конфликт при выборе пола.\nИсправить пол на %s?' % formatSex(detectedSex),
                                                 QtGui.QMessageBox.Yes|QtGui.QMessageBox.No,
                                                 QtGui.QMessageBox.Yes)
                if res == QtGui.QMessageBox.Yes:
                    self.cmbSex.setCurrentIndex(detectedSex)
        else:
            if detectedSex:
                self.cmbSex.setCurrentIndex(detectedSex)
            else:
                return self.checkInputMessage(u'пол', False, self.cmbSex)
        return True


    def checkBirthDateEntered(self):
        checkBirthDate = self.edtBirthDate.date()
        currentDate = QDate.currentDate()
        if checkBirthDate > currentDate:
            res = QtGui.QMessageBox.warning( self,
                                             u'Внимание!',
                                             u'Дата рождения не может быть больше текущей даты',
                                             QtGui.QMessageBox.Ok,
                                             QtGui.QMessageBox.Ok)
            if res == QtGui.QMessageBox.Ok:
                self.edtBirthDate.setFocus(Qt.ShortcutFocusReason)
                return False
        if currentDate.year() - checkBirthDate.year() > 135:
            res = QtGui.QMessageBox.question( self,
                                               u'Внимание!',
                                               u'Возраст превышает 135 лет.\nХотите исправить?',
                                               QtGui.QMessageBox.Yes|QtGui.QMessageBox.No,
                                               QtGui.QMessageBox.Yes)
            if res == QtGui.QMessageBox.Yes:
                self.edtBirthDate.setFocus(Qt.ShortcutFocusReason)
                return False
        return True


    def checkDocEntered(self):
        documentTypeId = self.cmbDocType.value()
        docCode = self.edtDocOriginCode.currentText()
        result = True
        if documentTypeId:
            if self.edtDocSerialLeft.isEnabled() and not self.edtDocSerialLeft.hasAcceptableInput():
                result = self.checkInputMessage(u'серию документа', False, self.edtDocSerialLeft)
            if result and self.edtDocSerialRight.isEnabled() and not self.edtDocSerialRight.hasAcceptableInput():
                result = self.checkInputMessage(u'серию документа', False, self.edtDocSerialRight)
            if result and self.edtDocNumber.isEnabled() and not self.edtDocNumber.hasAcceptableInput():
                result = self.checkInputMessage(u'номер документа', False, self.edtDocNumber)
            if documentTypeId == 1:
                if not checkDocCode(docCode):
                    result = self.checkValueMessageIgnore(u'Код подразделения не соответствует формату ххх-ххх!', False,
                                                        self.edtDocOriginCode)
                if len(docCode) == 0:
                    result = self.checkValueMessageIgnore(u'Требуется указать код подразделения', False, self.edtDocOriginCode)
#        if result and self.edtDocDate.isEnabled() and not self.edtDocDate.date():
#            result = self.checkInputMessage(u'дату выдачи документа', True, self.edtDocDate)
#        if result and self.edtDocOrigin.isEnabled() and not forceStringEx(self.edtDocOrigin.text()):
#            result = self.checkInputMessage(u'кем выдан документ', True, self.edtDocOrigin)

        checkClientDocumentIssueDate = QtGui.qApp.getGlobalPreference('checkClientDocumentIssueDate')
        if checkClientDocumentIssueDate and checkClientDocumentIssueDate != u'не выполнять':
            skipable = (checkClientDocumentIssueDate == u'мягкий')
            if result and self.edtDocDate.isEnabled() and not self.edtDocDate.date():
                result = self.checkInputMessage(u'дату выдачи документа', skipable, self.edtDocDate)
        return result
        
        
    def checkDocsEntered(self):
        result = True
        for row in xrange(self.modelIdentificationDocs.rowCount()-1):
            result = result and self.checkDocsItemEntered(row)
        return result


    def checkDocsItemEntered(self, row):
        result = True
        items = self.modelIdentificationDocs.items()
        item = items[row]

        documentTypeId = forceRef(item.value('documentType_id'))
        serial = forceString(item.value('serial'))
        number = forceString(item.value('number'))
        
        if documentTypeId or number or serial:
            if not documentTypeId:
                self.checkInputMessage(u'тип документа', False, self.tblIdentificationDocs, row, 0)
                return False
            serial = forceString(item.value('serial'))
            number = forceString(item.value('number'))
    #        date   = forceDate(item.value('date'))
    #        origin = forceStringEx(item.value('origin'))
    
            documentTypeDescr = getDocumentTypeDescr(documentTypeId)
            serialLeft, serialRight = documentTypeDescr.splitDocSerial(serial)
            if not documentTypeDescr.matchLeftPart(serialLeft):
                self.checkInputMessage(u'серию документа (левую часть)', False, self.tblIdentificationDocs, row, 1)
                return False
            if not documentTypeDescr.matchRightPart(serialRight):
                self.checkInputMessage(u'серию документа (правую часть)', False, self.tblIdentificationDocs, row, 1)
                return False
            if not documentTypeDescr.matchNumber(number):
                self.checkInputMessage(u'номер документа', False, self.tblIdentificationDocs, row, 2)
                return False
    # старые данные никто не восполнит, новые данные должны быть указаны на титульной странице.
    #        if result and not date:
    #            result = self.checkInputMessage(u'дату выдачи документа', True, self.tblIdentificationDocs, row, 3)
    #        if result and not origin:
    #            result = self.checkInputMessage(u'кем выдан документ', True, self.tblIdentificationDocs, row, 4)
        return result


    def checkPolicyEntered(self, isCompulsory):
        if isCompulsory:
            edtSerial = self.edtCompulsoryPolisSerial
            edtNumber = self.edtCompulsoryPolisNumber
            cmbPolisCompany = self.cmbCompulsoryPolisCompany
            cmbPolisKind = self.cmbCompulsoryPolisKind
            edtPolisName = self.edtCompulsoryPolisName
            edtPolisBegDate = self.edtCompulsoryPolisBegDate
            edtPolisEndDate = self.edtCompulsoryPolisEndDate
        else:
            edtSerial = self.edtVoluntaryPolisSerial
            edtNumber = self.edtVoluntaryPolisNumber
            cmbPolisCompany = self.cmbVoluntaryPolisCompany
            cmbPolisKind = self.cmbVoluntaryPolisKind
            edtPolisName = self.edtVoluntaryPolisName
            edtPolisBegDate = self.edtVoluntaryPolisBegDate
            edtPolisEndDate = self.edtVoluntaryPolisEndDate

        serial = forceStringEx(edtSerial.text())
        number = forceStringEx(edtNumber.text())
        insurerId = cmbPolisCompany.value()
        polisCompanyIsEmpty = not (insurerId and insurerId != cmbPolisCompany.invalidValue or not insurerId and forceStringEx(edtPolisName.text()))
        begDate = edtPolisBegDate.date()
        endDate = edtPolisEndDate.date()

        if not polisCompanyIsEmpty or serial or number or begDate or endDate:
            result = not polisCompanyIsEmpty or self.checkInputMessage(u'страховую компанию', True if insurerId and insurerId == cmbPolisCompany.invalidValue else False, cmbPolisCompany)
            if isCompulsory:
                policyKindId = cmbPolisKind.value()
                policyKindCode = forceString(cmbPolisKind.code())
                result = result and (policyKindId or self.checkInputMessage(u'вид полиса', False, cmbPolisKind))
                #проверка серии полиса только если полис старого образца
                result = result and (policyKindCode != '1' or serial or self.checkInputMessage(u'серию полиса', True, edtSerial))
                #проверка длины номера временного свидетельства
                result = result and (policyKindCode != '2' or len(number) == 9 or self.checkValueMessage(u"Номер временного свидетельства должен содержать строго 9 цифр!", False, edtNumber))
                #проверка ЕНП
                result = result and (policyKindCode not in ['3', '4', '5'] or unitedPolicyIsVaid(number) or self.checkInputMessage(u'правильный номер единого полиса', False, edtNumber))
                result = result and (policyKindCode not in ['3', '4', '5'] or not serial or self.checkValueMessage(u"Полис единого образца не должен иметь серию", False, edtNumber))

                if QtGui.qApp.isStrictPolicyCheckOnEventCreation() != 2:
                    result = result and ( begDate or self.checkInputMessage(u'начало действия полиса ОМС', bool(endDate), edtPolisBegDate))
                    #дата окончания - не обязательное поле
                    #result = result and ( (polisKind==3) or endDate or self.checkInputMessage(u'окончание действия полиса ОМС', True, edtPolisEndDate))
                result = result and self.checkDatePolicy(begDate, endDate, isCompulsory, serial, number)
            else:
                result = result and (serial or self.checkInputMessage(u'серию полиса', True, edtSerial))
                result = result and (number or self.checkInputMessage(u'номер полиса', False, edtNumber))
                if QtGui.qApp.isStrictPolicyCheckOnEventCreation() != 2:
                    result = result and (begDate or self.checkInputMessage(u'начало действия полиса ДМС', False, edtPolisBegDate))
                    result = result and ( endDate or self.checkInputMessage(u'окончание действия полиса ДМС', False, edtPolisEndDate))
                result = result and self.checkDatePolicy(begDate, endDate, isCompulsory, serial, number)
            return result
        return True


    def checkDatePolicy(self, policyBegDate, policyEndDate, isCompulsory, policySerial, policyNumber):
        result = True
        policyTypeIdList = []
        hasActivePolicy = False

        for row, record in enumerate(self.modelPolicies.items()):
            policyTypeIdList.append(forceRef(record.value('policyType_id')))
            if self.chkDeathDate.isChecked() and not forceDate(record.value('endDate')):
                hasActivePolicy = True

        # Закрываем полисы по дате смерти
        if hasActivePolicy and QtGui.QMessageBox().question(self,
                                                            u'Внимание!',
                                                            u'Обнаружен действующий полис.\nЗаполнить дату окончания полиса датой смерти?',
                                                            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                                            QtGui.QMessageBox.Yes) == QtGui.QMessageBox.Yes:
            for row, record in enumerate(self.modelPolicies.items()):
                if not forceDate(record.value('endDate')):
                    record.setValue('endDate', toVariant(QDate(self.edtDeathDate.date())))
            if any([self.edtCompulsoryPolisSerial.text(), self.edtCompulsoryPolisNumber.text(),
                    self.cmbCompulsoryPolisCompany.value()]) and not self.edtCompulsoryPolisEndDate.date():
                self.edtCompulsoryPolisEndDate.setDate(self.edtDeathDate.date())
            if any([self.edtVoluntaryPolisSerial.text(), self.edtVoluntaryPolisNumber.text(),
                    self.cmbVoluntaryPolisCompany.value()]) and not self.edtVoluntaryPolisEndDate.date():
                self.edtVoluntaryPolisEndDate.setDate(self.edtDeathDate.date())
        if policyTypeIdList:
            db = QtGui.qApp.db
            tableRBPolicyType = db.table('rbPolicyType')
            cond = [tableRBPolicyType['id'].inlist(policyTypeIdList),
                    tableRBPolicyType['isCompulsory'].eq(isCompulsory)]
            if not isCompulsory:
                cond.append(tableRBPolicyType['code'].eq(u'3'))
            idList = db.getDistinctIdList(tableRBPolicyType, [tableRBPolicyType['id']], cond)
            if idList:
                resultCorrectDatePolicy = False
                isCorrectDatePolicy = False
                for row, record in enumerate(self.modelPolicies.items()):
                    if isCorrectDatePolicy:
                        break
                    begDate = forceDate(record.value('begDate'))
                    endDate = forceDate(record.value('endDate'))
                    policyTypeId = forceRef(record.value('policyType_id'))
                    if policyTypeId and policyTypeId in idList:
                        serial = forceString(record.value('serial'))
                        number = forceString(record.value('number'))
                        periodBegDate = db.formatDate(begDate)
                        periodEndDate = db.formatDate(endDate)
                        result = result and (begDate or self.checkValueMessage(u'Укажите дату начала действия полиса серия %s номер %s период с %s по %s'%(serial, number, periodBegDate, periodEndDate), False, self.tblPolicies, row, record.indexOf('begDate')))
                        #result = result and (endDate or self.checkValueMessage(u'Укажите дату завершения действия полиса серия %s номер %s период с %s по %s'%(serial, number, periodBegDate, periodEndDate), True, self.tblPolicies, row, record.indexOf('endDate')))
                        for row2, record2 in enumerate(self.modelPolicies.items()):
                            if row != row2:
                                begDate2 = forceDate(record2.value('begDate'))
                                endDate2 = forceDate(record2.value('endDate'))
                                policyTypeId2 = forceRef(record2.value('policyType_id'))
                                if policyTypeId2 and policyTypeId2 in idList:
                                    if begDate:
                                        if ((not begDate2 or begDate2 <= begDate) and (not endDate2 or endDate2 >= begDate)):
                                            resultCorrectDatePolicy = (self.checkDatePolicyMessage(u'Пересечение действия полиса %s - %s с полисом %s - %s'%(forceString(begDate), forceString(endDate), forceString(begDate2), forceString(endDate2)), False, self.tblPolicies, row, record.indexOf('begDate'), idList=idList))
                                            result = result and resultCorrectDatePolicy
                                            isCorrectDatePolicy = True
                                            break
                                    if endDate:
                                        if ((not endDate2 or endDate2 >= endDate) and (not begDate2 or begDate2 <= endDate)):
                                            resultCorrectDatePolicy = (self.checkDatePolicyMessage(u'Пересечение действия полиса %s - %s с полисом %s - %s'%(forceString(begDate), forceString(endDate), forceString(begDate2), forceString(endDate2)), False, self.tblPolicies, row, record.indexOf('endDate'), idList=idList))
                                            result = result and resultCorrectDatePolicy
                                            isCorrectDatePolicy = True
                                            break
                result = result and self.checkIdenticalPolicy(idList, resultCorrectDatePolicy, isCompulsory)
        return result


    def checkPolicyAffiliationOMS(self):
        isCheckClientCardPolicyAffiliation = QtGui.qApp.checkClientCardPolicyAffiliation()
        if isCheckClientCardPolicyAffiliation > 0:
            buttons = QtGui.QMessageBox.Ok
            if isCheckClientCardPolicyAffiliation == 1:
                buttons = buttons | QtGui.QMessageBox.Ignore
            message = u'Необходимо выполнить проверку страховой принадлежности!'
            currentDate = QDate().currentDate()
            db = QtGui.qApp.db
            tableRBPolicyType = db.table('rbPolicyType')
            cond = [tableRBPolicyType['isCompulsory'].eq(1)]
            policyTypeIdList = db.getDistinctIdList(tableRBPolicyType, [tableRBPolicyType['id']], cond)
            if policyTypeIdList:
                for row, record in enumerate(self.modelPolicies.items()):
                    begDate = forceDate(record.value('begDate'))
                    endDate = forceDate(record.value('endDate'))
                    policyTypeId = forceRef(record.value('policyType_id'))
                    if policyTypeId and policyTypeId in policyTypeIdList:
                        if begDate <= currentDate and (currentDate <= endDate or endDate.isNull()):
                            checkDate = forceDate(record.value('checkDate'))
                            if not checkDate:
                                res = QtGui.QMessageBox().warning(self,
                                                                  u'Внимание!',
                                                                  message,
                                                                  buttons,
                                                                  QtGui.QMessageBox.Ok)
                                if res == QtGui.QMessageBox.Ok:
                                    if self.searchPolicy():
                                        self.modelPolicies.reset()
                                    return False
        return True


    def checkDatePolicyMessage(self, message, skipable, widget, row=None, column=None, detailWdiget=None, setFocus=True, idList=[]):
        buttons = QtGui.QMessageBox.Ok
        if skipable:
            buttons = buttons | QtGui.QMessageBox.Ignore
        messageBox = CCheckDatePolicyMessageBox(QtGui.QMessageBox.Warning,
                                                   u'Внимание!',
                                                   message,
                                                   buttons,
                                                   self
                                                )
        messageBox.setWindowFlags(messageBox.windowFlags() | Qt.WindowStaysOnTopHint)
        messageBox.setDefaultButton(QtGui.QMessageBox.Ok)
        messageBox.setEscapeButton(QtGui.QMessageBox.Ok)
        correctButton = QtGui.QPushButton(u'Исправить')
        messageBox.addButton(correctButton, QtGui.QMessageBox.AcceptRole)
        res = messageBox.exec_()
        clickedButton = messageBox.clickedButton()
        if res == QtGui.QMessageBox.Ok:
            if setFocus:
                self.setFocusToWidget(widget, row, column)
                if isinstance(detailWdiget, QtGui.QWidget):
                    self.setFocusToWidget(detailWdiget, row, column)
            return False
        elif clickedButton == correctButton:
            return QtGui.qApp.callWithWaitCursor(self, self.correctDatePolicy, idList)
        return False


    def correctDatePolicy(self, idList):
        #        db = QtGui.qApp.db
        items = []
        #        itemData = {}
        itemForDate = {}
        for row, record in enumerate(self.modelPolicies.items()):
            policyTypeId = forceRef(record.value('policyType_id'))
            if policyTypeId and policyTypeId in idList:
                serial = forceString(record.value('serial')).lower()
                number = forceString(record.value('number')).lower()
                insurerId = forceRef(record.value('insurer_id'))
                begDate = forceDate(record.value('begDate'))
                endDate = forceDate(record.value('endDate'))
                begDateDT = datetime.date(begDate.year(), begDate.month(), begDate.day())
                endDateDT = datetime.date(endDate.year(), endDate.month(), endDate.day()) if endDate else None
                newKey = (begDateDT, endDateDT, insurerId)
                itemForLine = itemForDate.get(newKey, {})
                itemForLine[(serial, number)] = (record, row, serial, number)
                itemForDate[newKey] = itemForLine
            else:
                items.append(record)
        for keyData, itemLine in itemForDate.items():
            if len(itemLine) > 1:
                QtGui.qApp.restoreOverrideCursor()
                return self.checkValueMessage(
                    u'Обнаружены полисы с одинаковым периодом и типом, но с разными номерами. Автоматическое исправление не возможно!',
                    False, self.tblPolicies, itemLine.values()[0][1], itemLine.values()[0][0].indexOf('begDate'))
        itemForDateKeys = itemForDate.keys()
        # itemForDateKeys.sort(key=lambda item:(item[0], item[1] if item[1] else datetime.date((QDate().currentDate().addYears(200)).year(), 12, 1)))
        itemForDateKeys.sort(key=lambda item: (item[0]))
        itemNewForDate = itemForDate.copy()
        rowFocus = None
        columnFocus = None
        for i, keyData in enumerate(itemForDateKeys):
            itemLine = itemForDate.get(keyData, {})
            if rowFocus is None and itemLine:
                rowFocus = 0
                columnFocus = itemLine.values()[0][0].indexOf('begDate')
            if i > 0:
                keyDataPrev = itemForDateKeys[i - 1]
                itemLinePrev = itemForDate.get(keyDataPrev, {})
                if not keyDataPrev[1] or keyDataPrev[1] >= keyData[0]:
                    if (not keyDataPrev[1] and keyData[1]) or (
                            keyDataPrev[1] and keyData[1] and keyDataPrev[1] >= keyData[1]):
                        if (keyDataPrev[2] != keyData[2]) or (
                                itemLinePrev.values()[0][2] != itemLine.values()[0][2]) or (
                                itemLinePrev.values()[0][3] != itemLine.values()[0][3]):
                            QtGui.qApp.restoreOverrideCursor()
                            return self.checkValueMessage(
                                u'Обнаружены полисы: один поглощает период другого. Автоматическое исправление не возможно!',
                                False, self.tblPolicies, itemLine.values()[0][1],
                                itemLine.values()[0][0].indexOf('begDate'))
                    if (keyDataPrev[2] == keyData[2]) and (
                            itemLinePrev.values()[0][2] == itemLine.values()[0][2]) and (
                            itemLinePrev.values()[0][3] == itemLine.values()[0][3]):
                        endDatePrev = forceDate(keyDataPrev[1])
                        endDateNext = forceDate(keyData[1])
                        if not endDatePrev or (endDateNext and endDatePrev > endDateNext):
                            endDate = endDatePrev.addDays(-1) if endDatePrev else QDate()
                        elif not endDateNext or (endDatePrev and endDatePrev < endDateNext):
                            endDate = endDateNext
                        else:
                            endDate = forceDate(keyData[0]).addDays(-1)
                        record = itemLinePrev.values()[0][0]
                        begDateUpd = forceDate(record.value('begDate'))
                        if endDate and begDateUpd > endDate:
                            QtGui.qApp.restoreOverrideCursor()
                            return self.checkValueMessage(
                                u'Обнаружен неразрешимый конфликт полисов. Автоматическое исправление не возможно!',
                                False, self.tblPolicies, itemLine.values()[0][1],
                                itemLine.values()[0][0].indexOf('begDate'))
                        if not endDatePrev or (endDateNext and endDatePrev > endDateNext):
                            itemNewForDate.pop(keyData, {})
                        elif not endDateNext or (endDatePrev and endDatePrev < endDateNext):
                            record.setValue('endDate', toVariant(endDate))
                            row = itemLinePrev.values()[0][1]
                            itemNewForDate.pop(keyDataPrev, {})
                            itemNewForDate.pop(keyData, {})
                            endDateNew = datetime.date(endDate.year(), endDate.month(),
                                                       endDate.day()) if endDate else None
                            itemNewForDate[(keyDataPrev[0], endDateNew, keyDataPrev[2])] = {
                                itemLinePrev.keys()[0]: (record, row)}
                        else:
                            record.setValue('endDate', toVariant(endDate))
                            row = itemLinePrev.values()[0][1]
                            itemNewForDate.pop(keyDataPrev, {})
                            endDateNew = datetime.date(endDate.year(), endDate.month(),
                                                       endDate.day()) if endDate else None
                            itemNewForDate[(keyDataPrev[0], endDateNew, keyDataPrev[2])] = {
                                itemLinePrev.keys()[0]: (record, row)}
                    else:
                        record = itemLinePrev.values()[0][0]
                        endDate = forceDate(keyData[0]).addDays(-1)
                        begDateUpd = forceDate(record.value('begDate'))
                        if begDateUpd > endDate:
                            QtGui.qApp.restoreOverrideCursor()
                            return self.checkValueMessage(
                                u'Обнаружен неразрешимый конфликт полисов. Автоматическое исправление не возможно!',
                                False, self.tblPolicies, itemLine.values()[0][1],
                                itemLine.values()[0][0].indexOf('begDate'))
                        record.setValue('endDate', toVariant(endDate))
                        row = itemLinePrev.values()[0][1]
                        itemNewForDate.pop(keyDataPrev, {})
                        endDateNew = datetime.date(endDate.year(), endDate.month(),
                                                   endDate.day()) if endDate else None
                        itemNewForDate[(keyDataPrev[0], endDateNew, keyDataPrev[2])] = {
                            itemLinePrev.keys()[0]: (record, row)}
        for itemNewForDateLine in itemNewForDate.values():
            items.append(itemNewForDateLine.values()[0][0])
        items, policyTypeList, result = self.mergeIdenticalPolicy(items, idList)
        items.sort(key=lambda item: (
        forceDate(item.value('begDate')), policyTypeList.get(forceRef(item.value('policyType_id')), False)),
                   reverse=False)
        self.modelPolicies.setItems(items)
        self.modelPolicies.reset()
        self.on_modelPolicies_policyChanged()
        self.syncPolicies()
        self.setFocusToWidget(self.tblPolicies, rowFocus, columnFocus)
        return True

    def checkIdenticalPolicy(self, idList, resultCorrectDatePolicy, isCompulsory):
        #        db = QtGui.qApp.db
        items = self.modelPolicies.items()
        items, policyTypeList, result = self.mergeIdenticalPolicy(items, idList)
        items.sort(key=lambda item: (
        forceDate(item.value('begDate')), policyTypeList.get(forceRef(item.value('policyType_id')), False)),
                   reverse=False)
        self.modelPolicies.setItems(items)
        self.modelPolicies.reset()
        self.on_modelPolicies_policyChanged()
        self.syncPolicies()
        # self.setFocusToWidget(self.tblPolicies, 0 if items else None, 0 if items else None)
        if result or resultCorrectDatePolicy:
            self.isCorrectDatePolicy(isCompulsory)
        return True

    def isCorrectDatePolicy(self, isCompulsory):
        QtGui.QMessageBox.warning(self,
                                  u'Внимание!',
                                  u'Произведено исправление пересечений полисов %s.' % (
                                      u'ОМС' if isCompulsory else u'ДМС'),
                                  QtGui.QMessageBox.Ok,
                                  QtGui.QMessageBox.Ok)
        return True

    def mergeIdenticalPolicy(self, items, idList):
        db = QtGui.qApp.db
        policyTypeList = {}
        result = False
        tableRBPolicyType = db.table('rbPolicyType')
        records = db.getRecordList(tableRBPolicyType,
                                   [tableRBPolicyType['id'], tableRBPolicyType['isCompulsory'],
                                    tableRBPolicyType['code']])
        for rec in records:
            id = forceRef(rec.value('id'))
            isCompulsory = forceBool(rec.value('isCompulsory'))
            policyTypeList[id] = isCompulsory
        items.sort(key=lambda item: (
        forceDate(item.value('begDate')), policyTypeList.get(forceRef(item.value('policyType_id')), False)),
                   reverse=True)
        # updateItems = []
        # updateRows = []
        # for row, item in enumerate(items):
        #     policyTypeId = forceRef(item.value('policyType_id'))
        #     if policyTypeId and policyTypeId in idList:
        #         updateItems.append(item)
        #         updateRows.append(row)
        # deletedRows = []
        # updateRow = None
        # itemNew = []
        # for row, item in enumerate(updateItems):
        #     if row > 0:
        #         itemPrev = updateItems[row - 1]
        #         serial = forceString(item.value('serial')).lower()
        #         number = forceString(item.value('number')).lower()
        #         insurerId = forceRef(item.value('insurer_id'))
        #         serialPrev = forceString(itemPrev.value('serial')).lower()
        #         numberPrev = forceString(itemPrev.value('number')).lower()
        #         insurerIdPrev = forceRef(itemPrev.value('insurer_id'))
        #         if serial == serialPrev and number == numberPrev and insurerId == insurerIdPrev:
        #             begDate = forceDate(item.value('begDate'))
        #             endDate = forceDate(item.value('endDate'))
        #             if not itemNew:
        #                 itemNew = itemPrev
        #                 updateRow = row - 1
        #             deletedRows.append(row)
        #             itemNew.setValue('begDate', toVariant(begDate))
        #             endDatePrev = forceDate(itemNew.value('endDate'))
        #             if endDatePrev and (not endDate or endDate > endDatePrev):
        #                 itemNew.setValue('endDate', toVariant(endDate))
        #             if itemNew and updateRow is not None:
        #                 updateItems[updateRow] = itemNew
        #             result = True
        #         else:
        #             itemNew = []
        #             updateRow = None
        # if updateItems:
        #     deletedRows.sort(reverse=True)
        #     for row in deletedRows:
        #         updateItems.pop(row)
        #     updateRows.sort(reverse=True)
        #     for row in updateRows:
        #         items.pop(row)
        #     items.extend(updateItems)
        items.sort(key=lambda item: (
        forceDate(item.value('begDate')), policyTypeList.get(forceRef(item.value('policyType_id')), False)),
                   reverse=True)
        return items, policyTypeList, result


    def checkContacts(self):
        table = self.tblContacts
        for row, record in enumerate(self.modelContacts.items()):
            contactTypeId = forceRef(record.value('contactType_id'))
            contact = forceString(record.value('contact'))
            if contactTypeId is None:
                return self.checkValueMessage(u'Не указан тип контакта', False, table, row, 0)
            if not contact and not self.checkValueMessage(u'Не указан контакт', True, table, row, 1):
                return False
        return True


    def checkEpidCases(self):
        table = self.tblEpidCase
        for row, record in enumerate(self.modelClientEpidCase.items()):
            regDate = forceDate(record.value('regDate'))
            if not regDate and not self.checkValueMessage(u'Не указана дата регистрации эпид. номера', False, table, row, 1):
                return False
        return True


    def checkSocStatuses(self):
        table = self.tblSocStatuses
        rowCount = self.modelSocStatuses.realRowCount()
        for row in xrange(rowCount):
            record = self.modelSocStatuses.getRecordByRow(row)
            socStatusTypeId = forceRef(record.value('socStatusType_id'))
            if socStatusTypeId is None:
                return self.checkValueMessage(u'Не указан тип соц.статуса', False, table, row, 1)
            begDate = forceDate(record.value('begDate'))
            endDate = forceDate(record.value('endDate'))
            if (endDate and begDate > endDate):
                return self.checkValueMessage(u'Требуется скорректировать даты соц статуса', False, table, row, 2)

            db = QtGui.qApp.db
            profSocStatusClassId = forceInt(db.translate('rbSocStatusClass', 'code', 'profilac', 'id'))
            profSocStatusTypeId = forceInt(db.translate('rbSocStatusType', 'code', u'prof_d', 'id'))
            if profSocStatusClassId == forceRef(record.value('socStatusClass_id')) and profSocStatusTypeId == socStatusTypeId  and (not begDate):
               return self.checkValueMessage(u'Требуется указать дату начала соц статуса', False, table, row, 2)
            if profSocStatusClassId == forceRef(record.value('socStatusClass_id')) and profSocStatusTypeId == socStatusTypeId  and (not endDate):
               return self.checkValueMessage(u'Требуется указать дату окончания соц статуса', False, table, row, 3)

        citizenshipGP = QtGui.qApp.isCitizenshipControl()
        if citizenshipGP:
            documentTypeId = self.cmbDocType.value()
            if documentTypeId:
                date = QDate.currentDate()
                db = QtGui.qApp.db
                tableType = db.table('rbSocStatusType')
                tableClass = db.table('rbSocStatusClass')
                isCitizenship = forceBool(db.translate('rbDocumentType', 'id', documentTypeId, 'isCitizenship'))
                isCitizenshipRF = False
                citizenshipClassId = forceRef(db.translate(tableClass, 'code', '8', 'id'))
                if citizenshipClassId:
                    for row, record in enumerate(self.modelSocStatuses.items()):
                        socStatusClassId = forceRef(record.value('socStatusClass_id'))
                        if socStatusClassId is None:
                            return self.checkValueMessage(u'Не указан соц.статус Класс', False, self.tblSocStatuses,
                                                          row, 0)
                        else:
                            begDate = forceDate(record.value('begDate'))
                            endDate = forceDate(record.value('endDate'))
                            if socStatusClassId != citizenshipClassId:
                                recordClass = db.getRecordEx(tableClass, [tableClass['code']],
                                                             [tableClass['id'].eq(socStatusClassId),
                                                              tableClass['group_id'].eq(citizenshipClassId)])
                                if recordClass:
                                    socStatusClassCode = forceString(recordClass.value('code'))
                                    if isCitizenship:
                                        if socStatusClassCode == '1' and (not begDate or begDate <= date) and (
                                                not endDate or endDate >= date):
                                            isCitizenshipRF = True
                                    elif socStatusClassCode in ['0', '1', '2'] and (
                                            not begDate or begDate <= date) and (not endDate or endDate >= date):
                                        isCitizenshipRF = True
                            else:
                                socStatusTypeId = forceRef(record.value('socStatusType_id'))
                                if socStatusTypeId:
                                    socStatusTypeCode = forceString(
                                        db.translate(tableType, 'id', socStatusTypeId, 'code'))
                                    if isCitizenship:
                                        if socStatusTypeCode == u'м643' and (not begDate or begDate <= date) and (
                                                not endDate or endDate >= date):
                                            isCitizenshipRF = True
                                    elif socStatusTypeCode and (not begDate or begDate <= date) and (
                                            not endDate or endDate >= date):
                                        isCitizenshipRF = True
                    if not isCitizenshipRF:
                        return self.checkValueMessage(u'Необходимо указать Гражданство',
                                                      True if citizenshipGP == 1 else False, self.tblSocStatuses,
                                                      len(self.modelSocStatuses.items()), 0)
        return True


    def checkClientRelations(self, clientSex):
        def checkClientRelationsInt(table, isDirect, otherFieldName, relationTypeCache, sexFieldName, otherSexFieldName):
            db = QtGui.qApp.db
            model = table.model()
            for row, record in enumerate(model.items()):
                relationTypeId = forceRef(record.value('relativeType_id'))
                otherId        = forceRef(record.value(otherFieldName))
                if relationTypeId:
                    relationTypeRecord = relationTypeCache.get(relationTypeId)
                    relationTypeCode = forceString(relationTypeRecord.value('regionalCode')) if relationTypeRecord else None
                    if otherId:
                        otherSex = forceInt(db.translate('Client', 'id', otherId, 'sex'))
                        if relationTypeRecord:
                            requiredSex = forceInt(relationTypeRecord.value(sexFieldName))
                            requiredOtherSex = forceInt(relationTypeRecord.value(otherSexFieldName))
                            if (   (requiredSex and requiredSex != clientSex)
                                or (requiredOtherSex and requiredOtherSex != otherSex)
                               ):
                                return self.checkValueMessage(u'Несоответствие полов в связи', False, table, row, 0)
                    elif not isDirect and relationTypeCode in ['4', '5']:
                        orgId = forceRef(record.value('org_id'))
                        if not orgId:
                            return self.checkValueMessage(u'Не выбрана связь', False, table, row, 1)
                    else:
                        return self.checkValueMessage(u'Не выбрана связь', False, table, row, 1)
                else:
                    return self.checkValueMessage(u'Не выбрана связь', False, table, row, 0)
            return True

        db = QtGui.qApp.db
        cache = CTableRecordCache(db, 'rbRelationType', ['regionalCode', 'leftSex', 'rightSex'])

        return (    checkClientRelationsInt(self.tblDirectRelations, True, 'relative_id', cache, 'leftSex', 'rightSex')
                and checkClientRelationsInt(self.tblBackwardRelations, False, 'client_id', cache, 'rightSex', 'leftSex')
               )


    def checkResearch(self):
        birthDate = self.edtBirthDate.date()
        for row, record in enumerate(self.modelResearch.items()):
            researchKindId = forceRef(record.value('researchKind_id'))
            if researchKindId is None:
                return self.checkInputMessage(u'вид обследования', False, self.tblResearch, row, record.indexOf('researchKind_id'))
            begDate = forceDate(record.value('begDate'))
            if not begDate.isValid():
                return self.checkInputMessage(u'дату проведения обследования', False, self.tblResearch, row, record.indexOf('begDate'))
            if begDate < birthDate:
                return self.checkValueMessage(u'Дата проведения не может быть меньше даты рождения', False, self.tblResearch, row, record.indexOf('begDate'))
            endDate = forceDate(record.value('endDate'))
            if endDate.isValid() and endDate < begDate:
                return self.checkValueMessage(u'Дата окончания срока действия не может быть меньше даты проведения', False, self.tblResearch, row, record.indexOf('endDate'))
        return True


    def checkDangerous(self):
        for row, record in enumerate(self.modelActiveDispensary.items()):
            begDate = forceDate(record.value('begDate'))
            if not begDate.isValid():
                return self.checkInputMessage(u'дату взятия на АДН', False, self.tblActiveDispensary, row, record.indexOf('begDate'))
            begReason = forceInt(record.value('begReason'))
            if begReason == 0:
                return self.checkInputMessage(u'причину взятия на АДН', False, self.tblActiveDispensary, row, record.indexOf('begReason'))
        for row, record in enumerate(self.modelDangerous.items()):
            date = forceDate(record.value('date'))
            if not date.isValid():
                return self.checkInputMessage(u'дату совершения общественно-опасного деяния', False, self.tblDangerous, row, record.indexOf('date'))
            description = forceString(record.value('description'))
            if not description:
                return self.checkInputMessage(u'описание общественно-опасного деяния', False, self.tblDangerous, row, record.indexOf('description'))
        for row, record in enumerate(self.modelForcedTreatment.items()):
            judgement = forceString(record.value('judgement'))
            if not judgement:
                return self.checkInputMessage(u'наименование суда', False, self.tblForcedTreatment, row, record.indexOf('judgement'))
            treatmentType = forceInt(record.value('treatmentType'))
            if treatmentType == 0:
                return self.checkInputMessage(u'тип принудительного лечения', False, self.tblForcedTreatment, row, record.indexOf('treatmentType'))
            begDate = forceDate(record.value('begDate'))
            if not begDate.isValid():
                return self.checkInputMessage(u'дату взятия на АПНЛ', False, self.tblForcedTreatment, row, record.indexOf('begDate'))
            endDate = forceDate(record.value('endDate'))
            if endDate.isValid() and endDate < begDate:
                return self.checkValueMessage(u'Дата снятия с АПНЛ не может быть меньше даты взятия', False, self.tblForcedTreatment, row, record.indexOf('endDate'))
            mcLastDate = forceDate(record.value('mcLastDate'))
            mcNextDate = forceDate(record.value('mcNextDate'))
            if mcLastDate.isValid() and mcNextDate.isValid() and mcNextDate < mcLastDate:
                return self.checkValueMessage(u'Дата следующей ВК не может быть меньше даты последней', False, self.tblForcedTreatment, row, record.indexOf('mcNextDate'))
            statBegDate = forceDate(record.value('statBegDate'))
            statEndDate = forceDate(record.value('statEndDate'))
            if statBegDate.isValid() and statEndDate.isValid() and statEndDate < statBegDate:
                return self.checkValueMessage(u'Дата снятия с принудительного лечения не может быть меньше даты перевода', False, self.tblForcedTreatment, row, record.indexOf('statEndDate'))
        for row, record in enumerate(self.modelSuicide.items()):
            date = forceDate(record.value('date'))
            if not date.isValid():
                return self.checkInputMessage(u'дату риска или совершенного акта', False, self.tblSuicide, row, record.indexOf('date'))
            statusType = forceInt(record.value('statusType'))
            if statusType == 0:
                return self.checkInputMessage(u'статус', False, self.tblSuicide, row, record.indexOf('statusType'))
            statusCondition = forceString(record.value('statusCondition'))
            if not statusCondition:
                return self.checkInputMessage(u'состояние', False, self.tblSuicide, row, record.indexOf('statusCondition'))
        return True


    def checkContingentKind(self):
        birthDate = self.edtBirthDate.date()
        for row, record in enumerate(self.modelContingentKind.items()):
            contingentKindId = forceRef(record.value('contingentKind_id'))
            if contingentKindId is None:
                return self.checkInputMessage(u'вид контингента', False, self.tblContingentKind, row, record.indexOf('contingentKind_id'))
            specialityId = forceRef(record.value('speciality_id'))
            if specialityId is None:
                return self.checkInputMessage(u'специальность', False, self.tblContingentKind, row, record.indexOf('speciality_id'))
            begDate = forceDate(record.value('begDate'))
            if not begDate.isValid():
                return self.checkInputMessage(u'дату постановки', False, self.tblContingentKind, row, record.indexOf('begDate'))
            if begDate < birthDate:
                return self.checkValueMessage(u'Дата постановки не может быть меньше даты рождения', False, self.tblContingentKind, row, record.indexOf('begDate'))
            endDate = forceDate(record.value('endDate'))
            if endDate.isValid() and endDate < begDate:
                return self.checkValueMessage(u'Дата снятия не может быть меньше даты постановки', False, self.tblContingentKind, row, record.indexOf('endDate'))
            reason = forceInt(record.value('contingentKindRemoval_id'))
            if reason > 0 and not endDate.isValid():
                return self.checkInputMessage(u'дату снятия', False, self.tblContingentKind, row, record.indexOf('endDate'))
            if endDate.isValid() and reason <= 0:
                return self.checkInputMessage(u'причину снятия', False, self.tblContingentKind, row, record.indexOf('contingentKindRemoval_id'))
            if forceBool(record.value('MKB')):
                mkb = forceString(record.value('MKB'))
                # specialityId = forceRef(record.value('speciality_id'))
                # if specialityId:
                #     result = QtGui.qApp.db.translate('rbSpeciality', 'id', specialityId, 'mkbFilter')
                #     if result:
                #         result = forceString(result)
                #     else:
                #         result = ''
                birthDate = forceDate(self.edtBirthDate.date())
                sex = forceInt(self.cmbSex.currentIndex())
                clientId = self.getClientId()
                clientAge = calcAgeTuple(self.clientBirthDate, QDate.currentDate())
                checkResut = checkDiagnosis(self, mkb, None, clientId, sex, clientAge)
                if not checkResut:
                    return self.checkValueMessage(u'Ошибка МКБ', False, self.tblContingentKind, row, record.indexOf('MKB'))
        return True


    def checkDup(self):
        dupCheckList = ((self.findDupByName, u'по имени и дате рождения'),
                        (self.findDupBySNILS, u'по СНИЛС'),
                        (self.findDupByDoc, u'по документу'),
                        (self.findDupByPolicy, u'по полису'),
                        )
        for method, title in dupCheckList:
            idList = method()
            if idList:
                buttons = QtGui.QMessageBox.No | QtGui.QMessageBox.Open
                message = u'Обнаружен "двойник" %s' % title
                if method == self.findDupByName and QtGui.qApp.checkGlobalPreference(u'23:IgnoreDoppelgangers', u'да', u'да') or method != self.findDupByName:
                    buttons = QtGui.QMessageBox.Yes | buttons
                    message += u'\nИгнорировать?'

                res = QtGui.QMessageBox().question(self, u'Внимание!', message, buttons, QtGui.QMessageBox.No)
                if res == QtGui.QMessageBox.No:
                    return False
                if res == QtGui.QMessageBox.Open:
                    self.load(idList[0])
                    db = QtGui.qApp.db
                    record = db.getRecord(db.table('Client'), '*', self._id)
                    self.setRecord(record)
                    return False
        return True


    def findDup(self, cond):
        db = QtGui.qApp.db
        table = db.table('Client')
        cond.append(table['deleted'].eq(0))
        id = self.itemId()
        if id:
            cond.append(table['id'].ne(id))
        return db.getIdList(table, where=cond, order='id')


    def findDupByName(self):
        db = QtGui.qApp.db
        table = db.table('Client')
        lastName  = forceStringEx(self.edtLastName.text())
        firstName = forceStringEx(self.edtFirstName.text())
        patrName  = forceStringEx(self.edtPatrName.text())
        birthDate = self.edtBirthDate.date()
        cond = [table['lastName'].eq(lastName),
                table['firstName'].eq(firstName),
                table['patrName'].eq(patrName),
                table['birthDate'].eq(birthDate)
               ]
        return self.findDup(cond)


    def findDupBySNILS(self):
        db = QtGui.qApp.db
        table = db.table('Client')
        SNILS = unformatSNILS(forceStringEx(self.edtSNILS.text()))
        if SNILS:
            cond = [table['SNILS'].eq(SNILS), table['deleted'].eq(0)]
            return self.findDup(cond)
        else:
            return []


    def findDupByDoc(self):
        docTypeId = self.cmbDocType.value()
        if docTypeId:
            serialLeft = forceStringEx(self.edtDocSerialLeft.text())
            serialRight = forceStringEx(self.edtDocSerialRight.text())
            serial = serialLeft + ' ' + serialRight
            number = forceStringEx(self.edtDocNumber.text())
            if not serialLeft and not serialRight and not number:
                return []
            db = QtGui.qApp.db
            table = db.table('ClientDocument')
            queryTable = table
            tableClient = db.table('Client')
            queryTable = table.leftJoin(tableClient, tableClient['id'].eq(table['client_id']))
            cond = [ table['documentType_id'].eq(docTypeId),
                     table['serial'].eq(serial),
                     table['number'].eq(number),
                     table['deleted'].eq(0),
                     table['id'].eqEx('(SELECT MAX(CD1.id) FROM ClientDocument AS CD1 WHERE CD1.client_id = ClientDocument.client_id)')
                   ]
            id = self.itemId()
            if id:
                cond.append(table['client_id'].ne(id))
            cond.append(tableClient['deleted'].eq(0))
            return db.getIdList(queryTable, 'client_id', cond, 'client_id')
        else:
            return []


    def findDupByPolicy(self):
        serial = forceStringEx(self.edtCompulsoryPolisSerial.text())
        number = forceStringEx(self.edtCompulsoryPolisNumber.text())
        if serial or number:
            db = QtGui.qApp.db
            table = db.table('ClientPolicy')
            queryTable = table
            tableClient = db.table('Client')
            queryTable = table.leftJoin(tableClient, tableClient['id'].eq(table['client_id']))
            cond = [ table['serial'].eq(serial),
                     table['number'].eq(number),
                     table['deleted'].eq(0),
                     table['id'].eqEx('(SELECT MAX(CP1.id) FROM ClientPolicy AS CP1 WHERE CP1.client_id = ClientPolicy.client_id)')
                   ]
            id = self.itemId()
            if id:
                cond.append(table['client_id'].ne(id))
            cond.append(tableClient['deleted'].eq(0))
            return db.getIdList(queryTable, 'client_id', cond, 'client_id')
        else:
            return []


    def checkAttachesDataEntered(self):
        result = True
        if QtGui.qApp.isStrictAttachCheckOnEventCreation() != 2:
            for i, item in enumerate(self.modelAttaches.items()):
                result = result and self.checkAttachDataEntered(i, item)
                if not result:
                    break

        return result


    def checkAttachDataEntered(self, row, item):
        result = ( forceRef(item.value('attachType_id')) or self.checkInputMessage(u'тип прикрепления',  False, self.tblAttaches, row, item.indexOf('attachType_id'))) \
             and ( forceRef(item.value('LPU_id'))        or self.checkInputMessage(u'ЛПУ',               False, self.tblAttaches, row, item.indexOf('LPU_id'))) \
             and ( forceDate(item.value('begDate'))      or self.checkInputMessage(u'дату прикрепления', False, self.tblAttaches, row, item.indexOf('begDate')))
        begDate = forceDate(item.value('begDate'))
        endDate = forceDate(item.value('endDate'))
        if result and endDate:
            result = (endDate >= begDate and endDate <= QDate.currentDate()) or self.checkValueMessage(u'ОШИБКА! Указана некорректная дата прикрепления или открепления', False, self.tblAttaches, row, item.indexOf('endDate'))
            # result = result and (forceRef(item.value('deAttachType_id')) or self.checkInputMessage(u'причину открепления', False, self.tblAttaches, row, item.indexOf('deAttachType_id')))
        return result


    def syncAttachments(self):
        db = QtGui.qApp.db
        lastRecord = None
        attachTypeCode = None
        actualRecordId = 0
        client_id = self.getClientId()
        for i, item in enumerate(self.modelAttaches.items()):
            id = forceRef(item.value('id'))
            attachTypeId = forceRef(item.value('attachType_id'))
            attachTypeCode = forceString(db.translate('rbAttachType', 'id', attachTypeId, 'code'))
            if id > actualRecordId and attachTypeCode in ['1', '2']:
                lastRecord = (i, item)
                actualRecordId = id
        
        if lastRecord == None or not forceDate(lastRecord[1].value('syncDate')).toPyDate():
            return
        row, actualRecord = lastRecord
        isAttached = actualRecord.isNull('endDate')
        if not actualRecord.isNull('deAttachType_id'):
            deAttachType = forceInt(db.translate('rbDeAttachType', 'id', actualRecord.value('deAttachType_id'), 'regionalCode'))  # код подразделения
        else:
            deAttachType = None
        if not isAttached and deAttachType is None:
            return
        orgStructureId = forceRef(actualRecord.value('orgStructure_id'))
        orgStructureInfisCode = forceString(db.translate('OrgStructure', 'id', orgStructureId, 'infisInternalCode'))  # код подразделения
        lpuInfisCode = forceString(db.translate('OrgStructure', 'id', orgStructureId, 'bookkeeperCode'))  # код участка
        
        # tmpDate = QDate().currentDate().addDays(-3)
        begDate = forceDate(actualRecord.value('begDate'))
        endDate = forceDate(actualRecord.value('endDate'))
        
        # # даты прикрепления/открепления проверяем на допустимый диапазон значений для сервиса
        # if begDate and begDate < tmpDate:
        #     begDate = tmpDate
        #
        # if endDate and endDate < tmpDate:
        #     endDate = tmpDate
        
               
        #ищем 5-ти значный омс код подразделения к которому прикреплен человек
        while len(lpuInfisCode) != 5 and orgStructureId:
            orgStructureId = forceRef(db.translate('OrgStructure', 'id', orgStructureId, 'parent_id'))
            lpuInfisCode = forceString(db.translate('OrgStructure', 'id', orgStructureId, 'bookkeeperCode'))
            
        personInfo = self.getAttachmentPersonInfo()

        def clientAttach(pr):
            attachInfo = {
                'date': forceString(begDate.toString('yyyy-MM-dd')),
                'area': orgStructureInfisCode,
                'type': forceInt(attachTypeCode),
                'mo':   lpuInfisCode, 
                'snils': None,
                'pr': pr
            }
            try:
                return AttachService.clientAttach(client_id, personInfo, attachInfo)
            except Exception as e:
                raise Exception(u'Не удалось прикрепить пациента: %s' % unicode(e))

        def clientDeAttach(date, type):
            deAttachInfo = {
                'date': date,
                'area': None, 
                'type': type,
                'mo':   lpuInfisCode
            }
            try:
                return AttachService.clientDeAttach(personInfo, deAttachInfo)
            except Exception, e:
                raise Exception(u'Не удалось открепить пациента: %s' % unicode(e))

        try:
            rawResponse = None
            searchResult = AttachService.searchClientAttach(personInfo)
            if not isAttached:  # в базе откреплен
                if 'attachlist' in searchResult:  # и в сервисе тоже прикреплен
                    attachInfo = searchResult['attachlist'][0]
                    serviceMo = str(attachInfo.get('mo', ''))
                    if serviceMo == lpuInfisCode:  # если совпадает МО, пробуем открепить на сервере
                        result = clientDeAttach(forceString(endDate.toString('yyyy-MM-dd')), deAttachType)
                        rawResponse = result['raw']
            else:  # в базе прикреплен
                if 'attachlist' not in searchResult or len(searchResult['attachlist']) == 0 or searchResult['attachlist'][0]['info'] is None:
                    # на сервере откреплен, пробуем прикрепить
                    result = clientAttach('1')
                    rawResponse = result['raw']
                else:  # на сервере тоже прикреплен, смотрим, совпадает ли МО и участок
                    attachInfo = searchResult['attachlist'][0]
                    serviceMo = str(attachInfo.get('mo', ''))
                    if serviceMo != lpuInfisCode:  # не совпадает МО
                        if not forceRef(db.translate('OrgStructure', 'bookkeeperCode', serviceMo, 'id')) and attachTypeCode == 1:  # не входит в состав юр лица
                            raise Exception(u'Пациент прикреплен к другой МО(юр. лицу)')
                    if 'info' in attachInfo and len(attachInfo['info']) > 0:
                        attachInfoInfo = attachInfo['info']
                        if 'area' in attachInfoInfo[0] and attachInfoInfo[0]['area'] != orgStructureInfisCode or serviceMo != lpuInfisCode:
                            # не совпадает участок, сначала открепляем от старого участка
                            # date = forceString(begDate.toString('yyyy-MM-dd'))
                            # if forceRef(db.translate('OrgStructure', 'bookkeeperCode', serviceMo, 'id')):
                            #     clientDeAttach(date, deAttachType)
                            if not forceRef(db.translate('OrgStructure', 'bookkeeperCode', serviceMo, 'id')):
                                result = clientAttach('1')
                            else:
                                result = clientAttach('4')
                            rawResponse = result['raw']
                        else:
                            # совпадает участок, значит уже синхронизировано
                            rawResponse = searchResult['raw']
                    else:  # на сервере нет сведений, пробуем прикрепить
                        result = clientAttach('1')
                        rawResponse = result['raw']
            query = db.preparedQueryCache.get(u"update ClientAttach set syncDate = now(), responceWS = ? where id = ?")
            query.bindValue(0, rawResponse)
            query.bindValue(1, actualRecordId)
            db.execPreparedQuery(query)
        except Exception, e:
            QtGui.QMessageBox.warning(self,
                                      u'Ошибка при синхронизации с сервисом прикреплений',
                                      unicode(e),
                                      QtGui.QMessageBox.Ok,
                                      QtGui.QMessageBox.Ok)


    def syncIdentificationDocs(self):
        #  синхронизация полей описания документа
        # (cmbDocType, edtDocSerialLeft, edtDocSerialRight, edtDocNumber)
        # в modelIdentificationDocs
        documentTypeId = self.cmbDocType.value()
        if documentTypeId is None:
            serial = ''
            number = ''
            date = QDate()
            origin = ''
            originCode = ''
        else:
            documentTypeDescr = getDocumentTypeDescr(documentTypeId)
            serialLeft = forceStringEx(self.edtDocSerialLeft.text())
            serialRight = forceStringEx(self.edtDocSerialRight.text())
            serial = documentTypeDescr.compoundDocSerial(serialLeft, serialRight)
            number = forceStringEx(self.edtDocNumber.text())
            date = forceDate(self.edtDocDate.date())
            origin = forceStringEx(self.edtDocOrigin.text())
            originCode = forceStringEx(self.edtDocOriginCode.currentText())

        if documentTypeId is not None or len(self.modelIdentificationDocs.items())!=0:
            row = self.modelIdentificationDocs.getCurrentDocRow(documentTypeId, serial, number)
            bs = self.modelIdentificationDocs.blockSignals(True)
            try:
                self.modelIdentificationDocs.setValue(row, 'documentType_id', documentTypeId)
                self.modelIdentificationDocs.setValue(row, 'serial', serial)
                self.modelIdentificationDocs.setValue(row, 'number', number)
                self.modelIdentificationDocs.setValue(row, 'date', date)
                self.modelIdentificationDocs.setValue(row, 'origin', origin)
                self.modelIdentificationDocs.setValue(row, 'originCode', originCode)
            finally:
                self.modelIdentificationDocs.blockSignals(bs)

    def syncPersonalInfo(self):
        lastName = forceStringEx(self.edtLastName.text())
        firstName = forceStringEx(self.edtFirstName.text())
        patrName = forceStringEx(self.edtPatrName.text())
        birthDate = forceDate(self.edtBirthDate.date())
        birthTime = forceTime(self.edtBirthTime.time())
        sex = forceInt(self.cmbSex.currentIndex())
        snils = unformatSNILS(forceStringEx(self.edtSNILS.text()))
        deathDate = QDateTime(self.edtDeathDate.date(), self.edtDeathTime.time()) if self.chkDeathDate.isChecked() else QDateTime()
        deathReasonId = forceRef(self.cmbDeathReason.value() if self.chkDeathDate.isChecked() else None)
        deathPlaceTypeId = forceRef(self.cmbDeathPlaceType.value() if self.chkDeathDate.isChecked() else None)
        row = self.modelPersonalInfo.getCurrentInfoRow(lastName, firstName, patrName, birthDate, birthTime, sex, deathDate, deathReasonId, deathPlaceTypeId, snils)
        bs = self.modelPersonalInfo.blockSignals(True)
        try:
            self.modelPersonalInfo.setValue(row, 'lastName', lastName)
            self.modelPersonalInfo.setValue(row, 'firstName', firstName)
            self.modelPersonalInfo.setValue(row, 'patrName', patrName)
            self.modelPersonalInfo.setValue(row, 'birthDate', birthDate)
            self.modelPersonalInfo.setValue(row, 'birthTime', birthTime)
            self.modelPersonalInfo.setValue(row, 'sex', sex)
            self.modelPersonalInfo.setValue(row, 'SNILS', snils)
            self.modelPersonalInfo.setValue(row, 'deathDate', deathDate)
            self.modelPersonalInfo.setValue(row, 'deathReason_id', deathReasonId)
            self.modelPersonalInfo.setValue(row, 'deathPlaceType_id', deathPlaceTypeId)
        finally:
            self.modelPersonalInfo.blockSignals(bs)
            self.modelPersonalInfo.reset()


    def updateCompulsoryPolicyType(self):
        serial = forceStringEx(self.edtCompulsoryPolisSerial.text())
        insurerId = self.cmbCompulsoryPolisCompany.value()
        if serial and insurerId and not self.cmbCompulsoryPolisType.value():
            policyTypeId = advisePolicyType(insurerId, serial)
            self.cmbCompulsoryPolisType.setValue(policyTypeId)


    def updateCompulsoryPolicyKind(self):
        serial = forceStringEx(self.edtCompulsoryPolisSerial.text())
        number = forceStringEx(self.edtCompulsoryPolisNumber.text())
        if serial.upper() in (u'ЕП', '') and len(number) == 16 and number.isdigit():
            code = '3'
        elif serial == '' and 9 <= len(number) <= 12 and number.isdigit():
            code = '2'
        elif serial != '' and number != '':
            code = '1'
        else:
            code = None
        if code:
            self.cmbCompulsoryPolisKind.setCode(code)


    def updateVoluntaryPolicyType(self):
        serial = forceStringEx(self.edtVoluntaryPolisSerial.text())
        insurerId = self.cmbVoluntaryPolisCompany.value()
        if serial and insurerId:
            policyTypeId = advisePolicyType(insurerId, serial)
            self.cmbVoluntaryPolisType.setValue(policyTypeId)


    def syncPolicies(self):
        self.syncPolicy(True)
        self.syncPolicy(False)


    def syncPolicy(self, isCompulsory):
        # возможные изменения в свойствах полиса
        # (edtCompulsoryPolisSerial, edtCompulsoryPolisNumber, cmbCompulsoryPolisCompany, cmbCompulsoryPolisType, edtCompulsoryPolisName, edtCompulsoryPolisNote)
        # необходимо отобразить в modelPolicies
        if isCompulsory:
            getRow = self.modelPolicies.getCurrentCompulsoryPolicyRow
            edtSerial = self.edtCompulsoryPolisSerial
            edtNumber = self.edtCompulsoryPolisNumber
            cmbPolisCompany = self.cmbCompulsoryPolisCompany
            cmbPolisType = self.cmbCompulsoryPolisType
            cmbPolisKind = self.cmbCompulsoryPolisKind
            edtPolisName = self.edtCompulsoryPolisName
            edtPolisNote = self.edtCompulsoryPolisNote
            polisBegDate = self.edtCompulsoryPolisBegDate
            polisEndDate = self.edtCompulsoryPolisEndDate
        else:
            getRow = self.modelPolicies.getCurrentVoluntaryPolicyRow
            edtSerial = self.edtVoluntaryPolisSerial
            edtNumber = self.edtVoluntaryPolisNumber
            cmbPolisCompany = self.cmbVoluntaryPolisCompany
            cmbPolisType = self.cmbVoluntaryPolisType
            cmbPolisKind = self.cmbVoluntaryPolisKind
            edtPolisName = self.edtVoluntaryPolisName
            edtPolisNote = self.edtVoluntaryPolisNote
            polisBegDate = self.edtVoluntaryPolisBegDate
            polisEndDate = self.edtVoluntaryPolisEndDate

        serial = forceStringEx(edtSerial.text())
        number = forceStringEx(edtNumber.text())
        insurerId = cmbPolisCompany.value()
        policyTypeId = cmbPolisType.value()
        if policyTypeId is None:
            cmbPolisType.setCurrentIndex(1)
            policyTypeId = cmbPolisType.value()
        policyKindId = cmbPolisKind.value()
        name = forceStringEx(edtPolisName.text())
        note = forceStringEx(edtPolisNote.text())
        begDate = polisBegDate.date()
        endDate = polisEndDate.date()

        if (number and begDate and (insurerId or name) and policyTypeId):
            previousRow = self.modelPolicies.getCurrentPolicyRowInt(isCompulsory)
            row = getRow(serial, number, insurerId, begDate)
            self.modelPolicies.setValue(row, 'serial', serial)
            self.modelPolicies.setValue(row, 'number', number)
            self.modelPolicies.setValue(row, 'insurer_id', insurerId)
            self.modelPolicies.setValue(row, 'policyType_id', policyTypeId)
            self.modelPolicies.setValue(row, 'policyKind_id', policyKindId)
            self.modelPolicies.setValue(row, 'name', name)
            self.modelPolicies.setValue(row, 'note', note)
            self.modelPolicies.setValue(row, 'begDate', begDate)
            self.modelPolicies.setValue(row, 'endDate', endDate)

            if isCompulsory and 0 <= previousRow < row and begDate:
                policies = self.modelPolicies.items()
                previousEndDate = forceDate(policies[previousRow].value('endDate'))
                previousBegDate = forceDate(policies[previousRow].value('begDate'))
                if previousEndDate.isNull() and previousBegDate <= begDate.addDays(-1):
                    self.modelPolicies.setValue(previousRow, 'endDate', toVariant(begDate.addDays(-1)))


    def evalSexByName(self, tableName, name):
        if not self.cmbSex.currentIndex():
            detectedSex = forceInt(QtGui.qApp.db.translate(tableName, 'name', name, 'sex'))
            self.cmbSex.setCurrentIndex(detectedSex)


    def updateSocStatus(self, fieldName, value):
        # изменено какое-то поле соц. статуса из числа доп.полей (сделанных отдельными widget-ами)
        row = self.tblSocStatuses.currentIndex().row()
        self.modelSocStatuses.setValue(row, fieldName, value)


    def updateSocStatuses(self, currStatuses):
        socStatusTypeIdSet = set()
        for socStatusTypeId, default in currStatuses:
            self.modelSocStatuses.establishStatus(socStatusTypeId)
            socStatusTypeIdSet.add(socStatusTypeId)
        self.modelSocStatuses.declineUnlisted(socStatusTypeIdSet)
        self.modelSocStatuses.reset()


    def updateWorkOrganisationInfo(self):
        id = self.cmbWorkOrganisation.value()
        self.clientWorkOrgId = id
        orgInfo = getOrganisationInfo(id)
        self.edtWorkOrganisationINN.setText(orgInfo.get('INN', ''))
        self.edtWorkOrganisationOGRN.setText(orgInfo.get('OGRN', ''))
        okved = orgInfo.get('OKVED', '')
        if self.cmbWorkOKVED.orgCode() != okved:
            self.edtOKVEDName.clear()
        self.cmbWorkOKVED.setOrgCode(okved)
        self.edtWorkOrganisationFreeInput.setEnabled(not id)


    def updateCompulsoryPolicyCompanyArea(self, forceAreaList=[]):
        areaList = [QtGui.qApp.defaultKLADR(),
                    self.cmbRegCity.code() if self.cmbRegCity.isEnabled() else '',
                    self.cmbLocCity.code(),
                    forceString(QtGui.qApp.db.translate('Organisation', 'id', self.cmbCompulsoryPolisCompany.value(), 'area'))
                   ]
        self.cmbCompulsoryPolisCompany.setAreaFilter(areaList+forceAreaList)
        self.updateCompulsoryPolicyType()


    def updateVoluntaryPolicyCompanyArea(self, forceAreaList=[]):
        areaList = [QtGui.qApp.defaultKLADR(),
                    self.cmbRegCity.code() if self.cmbRegCity.isEnabled() else '',
                    self.cmbLocCity.code(),
                    forceString(QtGui.qApp.db.translate('Organisation', 'id', self.cmbVoluntaryPolisCompany.value(), 'area'))
                   ]
        self.cmbVoluntaryPolisCompany.setAreaFilter(areaList+forceAreaList)
        self.updateVoluntaryPolicyType()


    def updatePolicyCompaniesArea(self, forceAreaList=[]):
        self.updateCompulsoryPolicyCompanyArea(forceAreaList)
        self.updateVoluntaryPolicyCompanyArea(forceAreaList)

    def blockQuotaWidgets(self, val):
        blockSignalList = self.grpQuotingDetails.children()
        for blockObj in blockSignalList:
            blockObj.blockSignals(val)

    def setQuotaWidgets(self, val):
        previousVal = self.edtQuotaIdentifier.isEnabled()
        if val != previousVal:
            self.setEnabledQuotaWidgets(val)
        if val:
            self.blockQuotaWidgets(True)
            record = self.__quotaRecord
            kladrCodeIndex = self.cmbQuotaKladr.getIndexByCode(forceString(record.value('regionCode')))
            if kladrCodeIndex:
                self.cmbQuotaKladr.setCurrentIndex(kladrCodeIndex)
            else:
                self.cmbQuotaKladr.setCurrentIndex(0)
            self.cmbQuotaDistrictKladr.setKladrCode(self.cmbQuotaKladr.itemData(self.cmbQuotaKladr.currentIndex()))
            self.cmbQuotaDistrictKladr.setValue(forceString(record.value('districtCode')))
            setLineEditValue(self.edtQuotaIdentifier, record, 'identifier')
            setSpinBoxValue(self.edtQuotaStage, record, 'stage')
            setLineEditValue(self.edtQuotaTicket, record, 'quotaTicket')
            setSpinBoxValue(self.edtQuotaAmount, record, 'amount')
            self.cmbQuotaMKB.setText(forceString(record.value('MKB')))
            setComboBoxValue(self.cmbQuotaRequest, record, 'request')

            directionDate = forceDate(record.value('directionDate'))
            if directionDate:
                self.edtQuotaDirectionDate.setDate(directionDate)
            else:
                self.edtQuotaDirectionDate.setDate(QDate())

            self.cmbQuotaLPU.setValue(forceInt(record.value('org_id')))
            setLineEditValue(self.edtQuotaLPUFreeInput, record, 'freeInput')

            dateRegistration = forceDate(record.value('dateRegistration'))
            if dateRegistration:
                self.edtQuotaDateRegistration.setDate(dateRegistration)
            else:
                self.edtQuotaDateRegistration.setDate(QDate())

            dateEnd = forceDate(record.value('dateEnd'))
            if dateEnd:
                self.edtQuotaDateEnd.setDate(dateEnd)
            else:
                self.edtQuotaDateEnd.setDate(QDate())

            orgStructureId = forceRef(record.value('orgStructure_id'))
            self.cmbQuotaOrgStructure.setValue(orgStructureId)
            setComboBoxValue(self.cmbQuotaStatus, record, 'status')
            setTextEditValue(self.edtQuotaStatment, record, 'statment')
            self.blockQuotaWidgets(False)


    def setEnabledQuotaWidgets(self, val):
        self.edtQuotaIdentifier.setEnabled(val)
        self.edtQuotaStage.setEnabled(val)
        self.edtQuotaTicket.setEnabled(val)
        self.edtQuotaAmount.setEnabled(val)
        self.cmbQuotaMKB.setEnabled(val)
        self.cmbQuotaRequest.setEnabled(val)
        self.edtQuotaDirectionDate.setEnabled(val)
        self.cmbQuotaLPU.setEnabled(val)
        self.edtQuotaLPUFreeInput.setEnabled(val)
        self.edtQuotaDateRegistration.setEnabled(val)
        self.edtQuotaDateEnd.setEnabled(val)
        self.cmbQuotaOrgStructure.setEnabled(val)
        self.cmbQuotaStatus.setEnabled(val)
        self.edtQuotaStatment.setEnabled(val)
        self.tblClientQuotingDiscussion.setEnabled(val)
        self.cmbQuotaKladr.setEnabled(val)
        self.cmbQuotaDistrictKladr.setEnabled(val)


    def setQuotingInfo(self):
        info = self.modelClientQuoting.info()
        limit     = info.get('limit', 0)
        used      = info.get('used', 0)
        confirmed = info.get('confirmed', 0)
        inQueue   = info.get('inQueue', 0)
        quotaTypeName = info.get('quotaTypeName', '')
        txt = u''
        txt += quotaTypeName+'\n'
        if limit:
            txt += u'Предел: %d\n' % limit
        if used:
            txt += u'Использовано: %d\n' % used
        if confirmed:
            txt += u'Подтверждено: %d\n' % confirmed
        if inQueue:
            txt += u'В очереди: %d\n' % inQueue
        self.lblInfo.setText(txt)

    def selectClientQuotingDiscussion(self, quotaId):
        db = QtGui.qApp.db
        table = self.modelClientQuotingDiscussion.table()
        cond = [table['master_id'].eq(quotaId)]
        return db.getIdList(table, 'id', cond, 'dateMessage')

    def showQuotaDiscussionEditor(self, editor):
        if editor.exec_():
            master_id = forceInt(self.__quotaRecord.value('id'))
            itemId = editor.itemId()
            if self.checkIsLastMessage(master_id, itemId):
                agreementTypeId = editor.cmbAgreementType.value()
                if agreementTypeId:
                    statusModifier = forceInt(QtGui.qApp.db.translate('rbAgreementType', 'id',
                                                         agreementTypeId, 'quotaStatusModifier'))
                    status = forceInt(self.__quotaRecord.value('status'))
                    if statusModifier and status != statusModifier-1:
                        quotaRow = self.selectionModelClientQuoting.selectedIndexes()[0].row()
                        self.__quotaRecord.setValue('status', QVariant(statusModifier-1))
                        self.cmbQuotaStatus.setCurrentIndex(statusModifier-1)
                        self.tblClientQuoting.model().emitRowChanged(quotaRow)
                        self.setSelectedQuota(quotaRow)
            idList = self.selectClientQuotingDiscussion(master_id)
            self.modelClientQuotingDiscussion.setIdList(idList, itemId)

    def newQuotaDiscussionEditor(self):
        editor = CQuotingEditorDialog(self)
        master_id = forceInt(self.__quotaRecord.value('id'))
        if not master_id:
            self.__quotaRecord.setValue('master_id', QVariant(self._id))
            row = self.tblClientQuoting.currentIndex().row()
            master_id = QtGui.qApp.db.insertRecord('Client_Quoting', self.__quotaRecord)
            quotingRecords = self.modelClientQuoting.getActualQuotingRecords(self.__quotaRecord)
            code = self.cmbRegCity.code()
            clientOKATOCode = getOKATO(code, self.cmbRegStreet.code(), self.edtRegHouse.text())
            if quotingRecords:
                for quotingRecord in quotingRecords:
                    status = forceInt(self.__quotaRecord.value('status'))
                    amount = forceInt(self.__quotaRecord.value('amount'))
                    self.modelClientQuoting.basicData[row] = [amount, status]
                    self.modelClientQuoting.changeData(quotingRecord, status, amount, amount.__add__)
                    if code:
                        self.modelClientQuoting.changeRegionData(status, amount, amount.__add__,
                                                                 code, quotingRecord)
                    if code and clientOKATOCode:
                        self.modelClientQuoting.changeDistrictData(status, amount, amount.__add__,
                                                                   (code, clientOKATOCode), quotingRecord)
        editor.setMaster_id(master_id)
        editor.cmbResponsiblePerson.setValue(QtGui.qApp.userId)
        self.showQuotaDiscussionEditor(editor)

    def editQuotaDiscussionEditor(self):
        isSelected = self.tblClientQuotingDiscussion.selectedIndexes()
        if isSelected:
            itemId = self.tblClientQuotingDiscussion.currentItemId()
            editor = CQuotingEditorDialog(self)
            editor.load(itemId)
            if editor.canBeEdit():
                self.showQuotaDiscussionEditor(editor)
            else:
                QtGui.QMessageBox.critical(self, u'Внимание!',
                                    u'Нет прав на редактирование записи',
                                    QtGui.QMessageBox.Ok,
                                    QtGui.QMessageBox.Ok
                                    )
        else:
            self.newQuotaDiscussionEditor()

    def deleteQuotaDiscussionMessage(self):
        isSelected = self.tblClientQuotingDiscussion.selectedIndexes()
        if isSelected:
            itemId = self.tblClientQuotingDiscussion.currentItemId()
            table = self.modelClientQuotingDiscussion.table()
            responsiblePersonId = forceInt(QtGui.qApp.db.translate(table,
                                                          'id', itemId, 'responsiblePerson_id'))
            if responsiblePersonId == QtGui.qApp.userId:
                if QtGui.QMessageBox.question(self, u'Подтверждение удаления',
                                    u'Вы уверены что хотите удалить сообщение?',
                                    QtGui.QMessageBox.Yes|QtGui.QMessageBox.No,
                                    QtGui.QMessageBox.No
                                    ) == QtGui.QMessageBox.Yes:
                    QtGui.qApp.db.deleteRecord(table, table['id'].eq(itemId))
                    idList = self.selectClientQuotingDiscussion(forceInt(self.__quotaRecord.value('id')))
                    self.modelClientQuotingDiscussion.setIdList(idList)

            else:
                QtGui.QMessageBox.critical(self, u'Внимание!',
                                    u'Нет прав на удаление записи',
                                    QtGui.QMessageBox.Ok,
                                    QtGui.QMessageBox.Ok
                                    )

    def deleteClientQuotingRows(self):
        rows = self.tblClientQuoting.getSelectedRows()
        rows.sort(reverse=True)
        self.checkClientAttachesForDeleting(rows)
        for row in rows:
            self.tblClientQuoting.model().removeRow(row)

    def checkClientAttachesForDeleting(self, rows):
        db = QtGui.qApp.db
        attachTypeId = db.translate('rbAttachType', 'code', '9', 'id')
        clientAttachRecords = self.modelAttaches.items()
        quotaItems = self.tblClientQuoting.model().items()
        attachQuotes = {}
        clientAttachRowsForDeleting = []
        for attachRow, clientAttchRecord in enumerate(clientAttachRecords):
            if clientAttchRecord.value('attachType_id') == attachTypeId:
                quotaList = attachQuotes.get(attachRow, [])
                attachBegDate = forceDate(clientAttchRecord.value('begDate'))
                attachEndDate = forceDate(clientAttchRecord.value('endDate'))
                for quotaRow, quotaItem in enumerate(quotaItems):
                    quotaBegDate = forceDate(quotaItem.value('dateRegistration'))
                    quotaEndDate = forceDate(clientAttchRecord.value('dateEnd'))
                    if attachEndDate:
                        if quotaBegDate <= attachEndDate:
                            if quotaEndDate:
                                if quotaEndDate >= attachBegDate:
                                    quotaList.append(quotaRow)
                                    attachQuotes[attachRow] = quotaList
                            else:
                                quotaList.append(quotaRow)
                                attachQuotes[attachRow] = quotaList
                    else:
                        if quotaEndDate:
                            if quotaEndDate >= attachBegDate:
                                quotaList.append(quotaRow)
                                attachQuotes[attachRow] = quotaList
                        else:
                            quotaList.append(quotaRow)
                            attachQuotes[attachRow] = quotaList
        for attachRow, clientAttchRecord in enumerate(clientAttachRecords):
            if clientAttchRecord.value('attachType_id') == attachTypeId:
                quotaList = attachQuotes.get(attachRow, [])
                for row in rows:
                    if row in quotaList:
                        quotaList.pop(quotaList.index(row))
                if len(quotaList) == 0:
                    clientAttachRowsForDeleting.append(attachRow)
        if clientAttachRowsForDeleting:
            if QtGui.QMessageBox.question(self,
                                       u'Внимание!',
                                       u'Удалить соответствующие прикрепления пациента?',
                                       QtGui.QMessageBox.Yes|QtGui.QMessageBox.No,
                                       QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
                clientAttachRowsForDeleting.sort(reverse=True)
                for attachRow in clientAttachRowsForDeleting:
                    self.tblAttaches.model().removeRow(attachRow)

    def checkIsLastMessage(self, quotingId, messageId):
        db = QtGui.qApp.db
        table = db.table('Client_QuotingDiscussion')
        cond = [ table['master_id'].eq(quotingId) ]
        stmt = db.selectStmt(table, 'MAX(id)', cond)
        query = db.query(stmt)
        if query.first():
            lastId = query.value(0).toInt()[0]
            if lastId == messageId:
                return True
        return False

    def setSelectedQuota(self, row=None):
        if row is None:
            items = self.modelClientQuoting.items()
            if items:
                row = 0
            else:
                return
        index = self.modelClientQuoting.index(row, 0)
        self.selectionModelClientQuoting.setCurrentIndex(index, QtGui.QItemSelectionModel.Rows)
        self.tblClientQuoting.setCurrentIndex(index)


    def setMKBTextInfo(self, text):
        if len(text)>1:
            if text[-1:] == '.':
                text = text[:-1]
            info = forceString(QtGui.qApp.db.translate('MKB', 'DiagID', text, 'DiagName'))
            self.lblMKBText.setText('<i>%s</i>'%info)
            if info:
                return True
            else:
                return False
        else:
            self.lblMKBText.clear()
            return False

    def getAttachmentPersonInfo(self):
        person = {}
        person['lastName'] = forceString(self.edtLastName.text())
        person['firstName'] = forceString(self.edtFirstName.text())
        person['patrName'] = forceString(self.edtPatrName.text())
        if self.cmbSex.currentIndex() != 0:
            person['sex'] = forceString(self.cmbSex.currentText())
        person['birthDate'] = forceString(self.edtBirthDate.date().toString('yyyy-MM-dd'))
        if unformatSNILS(self.edtSNILS.text()) != '':
            person['snils'] = forceString(self.edtSNILS.text())

        docTypeIsEmpty   = not self.cmbDocType.value()
        docNumberIsEmpty = not forceStringEx(self.edtDocNumber.text())
        if not (docTypeIsEmpty and docNumberIsEmpty):
            docTypeId = self.cmbDocType.value()
            documentTypeDescr = getDocumentTypeDescr(docTypeId)
            docTypeRegionalCode = forceInt(QtGui.qApp.db.translate('rbDocumentType', 'id', docTypeId, 'regionalCode'))
            if docTypeRegionalCode:
                person['docTypeId'] = docTypeRegionalCode
                person['docSerial'] = forceString(self.edtDocSerialLeft.text() + documentTypeDescr.partSeparator + self.edtDocSerialRight.text())
                person['docNumber'] = forceString(self.edtDocNumber.text())

        policyTypeIsEmpty   = not self.cmbCompulsoryPolisKind.value()
        policyNumberIsEmpty = not forceStringEx(self.edtCompulsoryPolisNumber.text())
        if not (policyTypeIsEmpty and policyNumberIsEmpty):
            policyTypeId = self.cmbCompulsoryPolisKind.value()
            policyTypeRegionalCode = forceInt(QtGui.qApp.db.translate('rbPolicyKind', 'id', policyTypeId, 'regionalCode'))
            if policyTypeRegionalCode:
                person['policyType'] = policyTypeRegionalCode
                person['policySerial'] = forceString(self.edtCompulsoryPolisSerial.text())
                person['policyNumber'] = forceString(self.edtCompulsoryPolisNumber.text())
                if policyTypeRegionalCode == '3':
                    person['enp'] = self.edtCompulsoryPolisNumber.text()

        insurerId = forceRef(self.cmbCompulsoryPolisCompany.value())
        infisCode = forceString(QtGui.qApp.db.translate('Organisation', 'id', insurerId, 'infisCode'))
        person['smoCode'] = infisCode
        OKATO = forceString(QtGui.qApp.db.translate('Organisation', 'id', insurerId, 'OKATO'))
        person['terrCode'] = OKATO
        return person

    @pyqtSignature('int')
    def on_tabWidget_currentChanged(self, index):
        widget = self.tabWidget.widget(index)
        if widget == self.tabRelations:
            self.modelDirectRelations.setRegAddressInfo(self.getParamsRegAddress())
            self.modelDirectRelations.setLogAddressInfo(self.getParamsLocAddress())
            self.modelDirectRelations.setDefaultAddressInfo(self.getDefaultAddress())
            self.modelBackwardRelations.setRegAddressInfo(self.getParamsRegAddress())
            self.modelBackwardRelations.setLogAddressInfo(self.getParamsLocAddress())
            self.modelBackwardRelations.setDefaultAddressInfo(self.getDefaultAddress())
        else:
            self.regAddressInfo = {}
            self.locAddressInfo = {}
            if widget == self.tabChangeJournal:
#                self.syncIdentificationDocs()
                self.syncPolicies()
                if self.tabChangeJournalInfo.currentWidget() == self.tabAddresses:
                    self.modelClientAddressesReg.setClientId(self.itemId())
                    self.modelClientAddressesLoc.setClientId(self.itemId())
        if widget:
            focusProxy = widget.focusProxy()
            if focusProxy:
                focusProxy.setFocus(Qt.OtherFocusReason)


    @pyqtSignature('int')
    def on_tabChangeJournalInfo_currentChanged(self, index):
        widget = self.tabChangeJournalInfo.widget(index)
        if widget == self.tabAddresses:
            self.modelClientAddressesReg.setClientId(self.itemId())
            self.modelClientAddressesLoc.setClientId(self.itemId())


    @pyqtSignature('')
    def on_edtFirstName_editingFinished(self):
        firstName = forceStringEx(self.edtFirstName.text())
        self.evalSexByName('rdFirstName', firstName)
        self.syncPersonalInfo()


    @pyqtSignature('')
    def on_edtPatrName_editingFinished(self):
        patrName = forceStringEx(self.edtPatrName.text())
        self.evalSexByName('rdPatrName', patrName)
        self.syncPersonalInfo()


    @pyqtSignature('')
    def on_btnCopyPrevAddress_clicked(self):
        if self.defaultAddressInfo:
            reg, freeInput, loc = self.defaultAddressInfo
            self.setRegAddress(reg, freeInput)
            self.setLocAddress(loc)
        elif CClientEditDialog.prevAddress:
            reg, freeInput, loc = CClientEditDialog.prevAddress
            self.setRegAddress(reg, freeInput)
            self.setLocAddress(loc)
        elif self.regAddressInfo or self.locAddressInfo:
            self.setRegAddressRelation(self.regAddressInfo)
            self.setLocAddressRelation(self.locAddressInfo)
        self.cmbDocType.setFocus(Qt.ShortcutFocusReason)


    @pyqtSignature('bool')
    def on_chkRegKLADR_toggled(self, checked):
        self.edtRegFreeInput.setEnabled(not checked)
        self.cmbRegCity.setEnabled(checked)
        self.cmbRegStreet.setEnabled(checked)
        self.edtRegHouse.setEnabled(checked)
        self.edtRegCorpus.setEnabled(checked)
        self.edtRegFlat.setEnabled(checked)


    @pyqtSignature('bool')
    def on_chkLocKLADR_toggled(self, checked):
        self.edtLocFreeInput.setEnabled(not checked)
        self.cmbLocCity.setEnabled(checked)
        self.cmbLocStreet.setEnabled(checked)
        self.edtLocHouse.setEnabled(checked)
        self.edtLocCorpus.setEnabled(checked)
        self.edtLocFlat.setEnabled(checked)


    @pyqtSignature('int')
    def on_cmbRegCity_currentIndexChanged(self,  val):
        code = self.cmbRegCity.code()
        strCode = self.cmbRegStreet.code()
        if strCode and not strCode.startswith(code[:-1]):
            self.cmbRegStreet.setCode('00')
        self.cmbRegStreet.setCity(code)
        self.updatePolicyCompaniesArea()   
    
    
    @pyqtSignature('int')
    def on_cmbRegStreet_currentIndexChanged(self,  val):
        code = self.cmbRegStreet.code()
        if code and checkIsActualSTREET(code) == False:
            self.cmbRegStreet.setStyleSheet('QComboBox { color: red; }')
        else:
            self.cmbRegStreet.setStyleSheet('')
        if code and code != self.cmbRegCity.code() and QtGui.qApp.getKladrResearch():
            self.cmbRegCity.setCode(code)
            self.updatePolicyCompaniesArea()


    @pyqtSignature('')
    def on_btnCopy_clicked(self):
        code = self.cmbRegCity.code()
        self.cmbLocCity.setCode(code)
        self.cmbLocStreet.setCity(code)
        self.cmbLocStreet.setCode(self.cmbRegStreet.code())
        self.edtLocHouse.setText(self.edtRegHouse.text())
        self.edtLocCorpus.setText(self.edtRegCorpus.text())
        self.edtLocFlat.setText(self.edtRegFlat.text())
        self.cmbDocType.setFocus(Qt.ShortcutFocusReason)


    @pyqtSignature('int')
    def on_cmbLocCity_currentIndexChanged(self, index):
        code = self.cmbLocCity.code()
        strCode = self.cmbLocStreet.code()
        if strCode and not strCode.startswith(code[:-1]):
            self.cmbLocStreet.setCode('00')
        self.cmbLocStreet.setCity(code)
        self.updatePolicyCompaniesArea()  
        
        
    @pyqtSignature('int')
    def on_cmbLocStreet_currentIndexChanged(self,  val):
        code = self.cmbLocStreet.code()
        if code and checkIsActualSTREET(code) == False:
            self.cmbLocStreet.setStyleSheet('QComboBox { color: red; }')
        else:
            self.cmbLocStreet.setStyleSheet('')
        if code and code != self.cmbLocCity.code() and QtGui.qApp.getKladrResearch():
            self.cmbLocCity.setCode(code)
            self.updatePolicyCompaniesArea()


    @pyqtSignature('int')
    def on_cmbDocType_currentIndexChanged(self, index):
        documentTypeId = self.cmbDocType.value()
        if documentTypeId:
            documentTypeDescr = getDocumentTypeDescr(documentTypeId)
            self.lblDocSerial.setEnabled(True)
            self.edtDocSerialLeft.setEnabled(True)
            self.edtDocSerialLeft.setRegExp(documentTypeDescr.leftPartRegExp)
            self.edtDocSerialRight.setEnabled(documentTypeDescr.hasRightPart)
            self.edtDocSerialRight.setRegExp(documentTypeDescr.rightPartRegExp)
            self.lblDocNumber.setEnabled(True)
            self.edtDocNumber.setEnabled(True)
            self.edtDocNumber.setRegExp(documentTypeDescr.numberRegExp)
            self.lblDocDate.setEnabled(True)
            self.edtDocDate.setEnabled(True)
            self.lblDocOrigin.setEnabled(True)
            self.edtDocOrigin.setEnabled(True)
            self.lblDocOriginCode.setEnabled(True)
            self.edtDocOriginCode.setEnabled(True)
        else:
            self.lblDocSerial.setEnabled(False)
            self.edtDocSerialLeft.setEnabled(False)
            self.edtDocSerialRight.setEnabled(False)
            self.lblDocNumber.setEnabled(False)
            self.edtDocNumber.setEnabled(False)
            self.lblDocDate.setEnabled(False)
            self.edtDocDate.setEnabled(False)
            self.lblDocOrigin.setEnabled(False)
            self.edtDocOrigin.setEnabled(False)
            self.lblDocOriginCode.setEnabled(False)
            self.edtDocOriginCode.setEnabled(False)
        self.syncIdentificationDocs()
        
        
    @pyqtSignature('QString')
    def on_edtDocSerialLeft_textChanged(self, text):
        self.syncIdentificationDocs()


    @pyqtSignature('QString')
    def on_edtDocSerialRight_textChanged(self, text):
        self.syncIdentificationDocs()


    @pyqtSignature('QString')
    def on_edtDocNumber_textChanged(self, text):
        self.syncIdentificationDocs()


    @pyqtSignature('QDate')
    def on_edtDocDate_dateChanged(self, date):
        self.syncIdentificationDocs()


    @pyqtSignature('QString')
    def on_edtDocOrigin_textChanged(self, text):
        self.syncIdentificationDocs()
      
        
    @pyqtSignature('QString')
    def on_edtDocOriginCode_editTextChanged(self, txt):
        textvalue = forceString(self.edtDocOriginCode.currentText())
        if textvalue:
            if len(textvalue) == 1:
                self.edtDocOriginCode.setTable()
            elif len(textvalue) > 8:
                DocCodeName = textvalue.split('| ')
                if DocCodeName and len(DocCodeName) > 1:
                    self.edtDocOrigin.setText(DocCodeName[1])
                    self.edtDocOriginCode.setEditText(DocCodeName[0])
        self.syncIdentificationDocs()


    @pyqtSignature('const QModelIndex&, const QModelIndex&')
    def on_modelIdentificationDocs_dataChanged(self, topLeft, bottomRight):
        items = self.modelIdentificationDocs.items()
        row = bottomRight.row()
        if row >=0 and row == len(items)-1:
            self.setDocumentRecord(items[-1])


    @pyqtSignature('const QModelIndex&, int, int')
    def on_modelIdentificationDocs_rowsRemoved(self, parent, start, end):
        items = self.modelIdentificationDocs.items()
        self.setDocumentRecord(items[-1] if items else None)


    @pyqtSignature('QString')
    def on_edtLastName_textChanged(self, text):
        self.syncPersonalInfo()

    @pyqtSignature('QString')
    def on_edtSNILS_textChanged(self, text):
        self.syncPersonalInfo()


    @pyqtSignature('const QModelIndex&, int, int')
    def on_modelPersonalInfo_rowsRemoved(self, parent, start, end):
        items = self.modelPersonalInfo.items()
        self.setPersonalInfoRecord(items[-1] if items else None)


    @pyqtSignature('QTime')
    def on_edtBirthTime_dateChanged(self, time):
        self.syncPersonalInfo()


    def setPersonalInfoRecord(self, record):
        if record:
            lastName = forceString(record.value('lastName'))
            firstName = forceString(record.value('firstName'))
            patrName = forceString(record.value('patrName'))
            birthDate = forceDate(record.value('birthDate'))
            birthTime = forceTime(record.value('birthTime'))
            sex = forceInt(record.value('sex'))
        else:
            lastName = ''
            firstName = ''
            patrName = ''
            birthDate = QDate()
            birthTime = QTime()
            sex = 0
        self.edtLastName.setText(lastName)
        self.edtFirstName.setText(firstName)
        self.edtPatrName.setText(patrName)
        self.edtBirthDate.setDate(birthDate)
        self.edtBirthTime.setTime(birthTime)
        self.cmbSex.setCurrentIndex(sex)


    @pyqtSignature('')
    def on_btnSearchPolicy_clicked(self):
        self.searchPolicy()


    def getAttachMOData(self):
        try:
            from Registry.Ferzl_service import Ferzl_service
            service = Ferzl_service()
            serviceUrl = service.url + u'/oms/services'
            model = self.tblAttaches.model()
            row = self.tblAttaches.currentIndex().row()
            recordRow = model.items()[row]
            itemId = forceRef(recordRow.value('id'))
            dateAttachB = forceDate(recordRow.value('begDate'))
            dateAttachE = forceDate(recordRow.value('endDate'))
            attachMethod = 2 if forceString(QtGui.qApp.db.translate('rbAttachType', 'id', forceRef(recordRow.value('attachType_id')), 'code')) == '2' else 1
            orgId = forceRef(recordRow.value('LPU_id'))
            orgStructureId = forceRef(recordRow.value('orgStructure_id'))
            moId = getIdentification('Organisation', orgId, 'urn:oid:1.2.643.5.1.13.13.11.1461', raiseIfNonFound=False)
            regKLADRCode = self.cmbRegStreet.code()
            locKLADRCode = self.cmbLocStreet.code()
            guid = str(uuid.uuid5(uuid.UUID(bytes='ClientAttach'.ljust(16, '\0')), repr(forceInt(itemId))))

            dataJson = {}
            dataJson['data'] = {}
            dataJson['data']['dateApplication'] = str(QDate.currentDate().toString('yyyy-MM-dd'))
            dataJson['data']['enp'] = ''
            if self.edtCompulsoryPolisNumber.text():
                dataJson['data']['enp'] = str(self.edtCompulsoryPolisNumber.text())
            dataJson['data']['dateAttachB'] = str(dateAttachB.toString('yyyy-MM-dd'))
            if not dateAttachE.isNull():
                dataJson['data']['dateAttachE'] = str(dateAttachE.toString('yyyy-MM-dd'))
            dataJson['data']['attachMethod'] = attachMethod
            dataJson['data']['areaType'] = 1
            dataJson['data']['moId'] = moId
            dataJson['data']['moCode'] = forceString(QtGui.qApp.db.translate('Organisation', 'id', orgId, 'smoCode'))
            dataJson['data']['moDepId'] = getOrgStructureIdentification(orgStructureId, 'urn:oid:1.2.643.5.1.13.13.99.2.114')
            dataJson['data']['addr'] = []
            dataJson['data']['applicationCont'] = []
            if regKLADRCode:
                address = {}
                address['okato'] = getOKATO(self.cmbRegCity.code(), regKLADRCode, self.edtRegHouse.text())[:5]
                address['oksm'] = 'RUS'
                query = QtGui.qApp.db.query("SELECT fias.GetObjectGuidByKladr(%s)" % decorateString(regKLADRCode[:15]))
                address['aoguid'] = ''
                if query.first():
                    address['aoguid'] = forceString(query.value(0))
                address['addressType'] = 1
                address['validFrom'] = str(self.edtAddressDate.date().toString('yyyy-MM-dd'))
                dataJson['data']['addr'].append(address)
            if locKLADRCode:
                address = {}
                address['okato'] = getOKATO(self.cmbLocCity.code(), locKLADRCode, self.edtLocHouse.text())[:5]
                address['oksm'] = 'RUS'
                query = QtGui.qApp.db.query("SELECT fias.GetObjectGuidByKladr(%s)" % decorateString(locKLADRCode[:15]))
                address['aoguid'] = ''
                if query.first():
                    address['aoguid'] = forceString(query.value(0))
                address['addressType'] = 2
                dataJson['data']['addr'].append(address)
            for row, record in enumerate(self.modelContacts.items()):
                contactTypeId = forceRef(record.value('contactType_id'))
                if contactTypeId is not None:
                    contactTypeCode = forceString(QtGui.qApp.db.translate('rbContactType', 'id', contactTypeId, 'code'))
                    contactType = {'1': 'TEL', '2': 'TEL', '3': 'MTEL'}.get(contactTypeCode)
                    if contactType:
                        contactText = forceString(record.value('contact'))
                        description = forceString(record.value('notes'))
                        dataJson['data']['applicationCont'].append({'contactType': contactType, 'contactText': contactText, 'description':description})
            
            content = requests.post(serviceUrl + '/AttachMoData', json=json.loads(json.dumps(dataJson)))
            if content.status_code != 200:
                message = u'Ошибка сервисов. Код ошибки: '+ forceString(content.status_code) + u' - ' + forceString(content.reason)+u'. AttachMoData'
                msgbx = service.showMessageBox(message, isError=True)
                if msgbx == QtGui.QMessageBox.Cancel:
                    return
            if content:
                api = MSCApi(QtGui.qApp.getCsp())
                certUser = QtGui.qApp.getUserCert(api)
                data = content.text.encode('utf-8').replace("<?xml version='1.0' encoding='utf8'?>\n", '')
                detachedSignatureBytesUser = certUser.createDetachedSignature(data)
                dictForJson = {
                                'guid': guid,
                               'sign': base64.b64encode(detachedSignatureBytesUser),
                               'certificate': base64.b64encode(detachedSignatureBytesUser),
                               'data': data}
                result = service.registerAttachMo(dictForJson)
                if result.get('result', None):
                    QtGui.QMessageBox().information(self,u'Прикрепление в ФЕРЗЛ',u'Прикрепление успешно отправлено в ФЕРЗЛ', QtGui.QMessageBox.Ok)


        except Exception, e:
            QtGui.QMessageBox().critical(self, u'Ошибка', u'Произошла ошибка: ' + unicode(e), QtGui.QMessageBox.Close)


    def searchPolicyInFederalService(self, servicesURL):
        servicesURL = urlparse.urljoin(servicesURL, '/api/IdentityPatient/fhir/')
        db = QtGui.qApp.db
        docTypeId = self.cmbDocType.value()
        policyKindId = self.cmbCompulsoryPolisKind.value()
        docTypeRegionalCode = forceInt(QtGui.qApp.db.translate('rbDocumentType', 'id', docTypeId, 'regionalCode'))
        SerialSeparator = '-' if docTypeRegionalCode in (3, 1) else ' '
        docSeria = forceStringEx(self.edtDocSerialLeft.text() + SerialSeparator + self.edtDocSerialRight.text())
        docNumber = forceStringEx(self.edtDocNumber.text())
        policyKindCode = forceInt(QtGui.qApp.db.translate('rbPolicyKind', 'id', policyKindId, 'regionalCode'))
        policySerial = forceStringEx(self.edtCompulsoryPolisSerial.text())
        policyNumber = forceStringEx(self.edtCompulsoryPolisNumber.text())

        messageBox = QtGui.QMessageBox()
        messageBox.setIcon(QtGui.QMessageBox.Information)
        messageBox.setWindowFlags(messageBox.windowFlags() | Qt.WindowStaysOnTopHint)
        messageBox.setWindowTitle(u'Обновление полисных данных')
        messageBox.setText(
            u'При поиске полисных данных\n в Web-сервисе«Проверка страховой принадлежности и прохождения диспансеризации (профилактических осмотров)\n полис не найден.\nЗапросить данные в сервисе «ИДЕНТИФИКАЦИЯ ГРАЖДАН В СФЕРЕ ОМС»?')
        btnSearchByDocument = QtGui.QPushButton()
        btnSearchByPolicy = QtGui.QPushButton()
        btnSearchByDocument.setText(u'По документу')
        btnSearchByPolicy.setText(u'По полисным данным')
        messageBox.addButton(btnSearchByDocument, QtGui.QMessageBox.ActionRole)
        messageBox.addButton(btnSearchByPolicy, QtGui.QMessageBox.ActionRole)
        messageBox.setDefaultButton(btnSearchByDocument)
        messageBox.addButton(QtGui.QMessageBox.Cancel)
        messageBox.exec_()
        if messageBox.clickedButton() in [btnSearchByDocument, btnSearchByPolicy]:
            try:
                lpu_guid = forceString(db.translate('Organisation', 'id', QtGui.qApp.currentOrgId(), 'usishCode'))
                params = {'registr_id': self.getClientId(), 'lpu_id': lpu_guid,
                          'patient_surname': forceString(self.edtLastName.text()),
                          'patient_name': forceString(self.edtFirstName.text()),
                          'patient_patronymic': forceString(self.edtPatrName.text()),
                          'birth_date': unicode(self.edtBirthDate.date().toString('yyyy-MM-dd')),
                          'doc_type': docTypeRegionalCode if messageBox.clickedButton() == btnSearchByDocument else policyKindCode,
                          'doc_seria': docSeria if messageBox.clickedButton() == btnSearchByDocument else policySerial,
                          'doc_number': docNumber if messageBox.clickedButton() == btnSearchByDocument else policyNumber,
                          'is_polis': 0 if messageBox.clickedButton() == btnSearchByDocument else 1,
                          'person_id': QtGui.qApp.userId}
                tableIdentityPatient = db.table('soc_IdentityPatient')
                cond = [tableIdentityPatient['client_id'].eq(self.getClientId()),
                        tableIdentityPatient['lastName'].eq(forceString(self.edtLastName.text())),
                        tableIdentityPatient['firstName'].eq(forceString(self.edtFirstName.text())),
                        tableIdentityPatient['patrName'].eq(forceString(self.edtPatrName.text())),
                        tableIdentityPatient['birthDate'].eq(self.edtBirthDate.date()), u" (errorMessageResponse IS NULL OR errorMessageResponse !='Отсутствуют данные по запросу') "]
                if messageBox.clickedButton() == btnSearchByDocument:
                    cond.extend([tableIdentityPatient['documentTypeCode'].eq(docTypeRegionalCode),
                                 tableIdentityPatient['serial'].eq(docSeria),
                                 tableIdentityPatient['number'].eq(docNumber), ])
                else:
                    cond.extend([tableIdentityPatient['policyKindCode'].eq(policyKindCode),
                                 tableIdentityPatient['policySerial'].eq(policySerial),
                                 tableIdentityPatient['policyNumber'].eq(policyNumber)])
                orderRecord = db.getRecordEx(tableIdentityPatient, '*', where=cond, order='createDatetime desc')
                if orderRecord:
                    responseDatetime = forceDate(orderRecord.value('responseDatetime'))
                    errorMessageResponse = forceString(orderRecord.value('errorMessageResponse'))
                    if not responseDatetime:
                        params = {'strah_ident_id': forceRef(orderRecord.value('id'))}
                        try:
                            response = requests.get(servicesURL + '$getIdentityPatient', params)
                            jsonData = response.json()
                            if jsonData.get('result', '') == "success":
                                db = QtGui.qApp.db
                                table = db.table('soc_IdentityPatient')
                                orderRecord = db.getRecord(table, '*', forceRef(orderRecord.value('id')))
                                if orderRecord:
                                    if forceDate(orderRecord.value('errorDateResponse')):
                                        if forceString(orderRecord.value('errorMessageResponse')) == '':
                                            message = u'Ошибка не указана!'
                                        else:
                                            message = forceString(orderRecord.value('errorMessageResponse'))
                                    else:
                                        message = u'Получен успешный ответ!'
                                    QtGui.QMessageBox().information(self, u'Информация', message)

                            else:
                                QtGui.QMessageBox().critical(self, u'Ошибка', u"Возвращен неверный формат ответа!",
                                                             QtGui.QMessageBox.Close)
                        except Exception, e:
                            QtGui.QMessageBox().critical(self, u'Ошибка', u'Произошла ошибка: ' + unicode(e),
                                                         QtGui.QMessageBox.Close)
                    elif responseDatetime and errorMessageResponse:
                        QtGui.QMessageBox().information(self, u'Ошибка', errorMessageResponse, QtGui.QMessageBox.Close)
                    elif responseDatetime:
                        # обновляем данные пациента
                        tableOrg = db.table('Organisation')
                        tablePolicyKind = db.table('rbPolicyKind')
                        tableClientPolicy = db.table('ClientPolicy')
                        newPolicyKindCode = forceString(orderRecord.value('respPolicyKindCode'))
                        newPolicyKindName = newPolicyKindCode
                        newPolicyKindId = None
                        pkRecord = db.getRecordEx(tablePolicyKind, 'id, name',
                                                  tablePolicyKind['regionalCode'].eq(newPolicyKindCode), 'id')
                        if pkRecord:
                            newPolicyKindId = forceRef(pkRecord.value('id'))
                            newPolicyKindName = forceString(pkRecord.value('name'))
                        newPolicySerial = forceString(orderRecord.value('respPolicySerial'))
                        newPolicyNumber = forceString(orderRecord.value('respPolicyNumber'))
                        newPolicyBegDate = forceDate(orderRecord.value('respPolicyBegDate'))
                        newPolicyEndDate = forceDate(orderRecord.value('respPolicyEndDate'))
                        newInsurerCode = forceString(orderRecord.value('respInsurerCode'))
                        newInsuranceArea = forceString(orderRecord.value('respInsuranceArea'))
                        checkDate = forceDate(orderRecord.value('responseDatetime'))
                        newInsurerId = None
                        newInsurerName = None
                        newInsurerArea = None

                        record = db.getRecordEx(tableOrg, 'id, shortName, area',
                                                [tableOrg['deleted'].eq(0), tableOrg['isActive'].eq(1),
                                                 tableOrg['OKATO'].eq(newInsuranceArea),
                                                 tableOrg['smoCode'].eq(newInsurerCode)], 'id')
                        if record:
                            newInsurerId = forceRef(record.value(0))
                            newInsurerName = forceString(record.value(1))
                            newInsurerArea = forceString(record.value(2))
                        else:
                            record = db.getRecordEx(tableOrg, 'id, shortName, area',
                                                    [tableOrg['deleted'].eq(0), tableOrg['isActive'].eq(1),
                                                     tableOrg['OKATO'].eq(newInsuranceArea)],
                                                    'id')
                            if record:
                                newInsurerId = forceRef(record.value(0))
                                newInsurerName = forceString(record.value(1))
                                newInsurerArea = forceString(record.value(2))
                            else:
                                newInsurerId = None
                                newInsurerName = u'{0} {1} ОКАТО {2}'.format(forceString(orderRecord.value('respInsurerCode')),
                                                                             forceString(orderRecord.value('respInsurerName')),
                                                                             forceString(orderRecord.value('respInsuranceArea')))
                        oldPolicyLabel = u'Текущий полис:\nСМО: %s\nсерия: %s\nномер: %s\nвид: %s\nдействителен с %s%s\n' % (
                            forceString(self.cmbCompulsoryPolisCompany.currentText()),
                            self.edtCompulsoryPolisSerial.text(), self.edtCompulsoryPolisNumber.text(),
                            self.cmbCompulsoryPolisKind.currentText(),
                            forceString(self.edtCompulsoryPolisBegDate.date()), u' по %s' % forceString(
                                self.edtCompulsoryPolisEndDate.date()) if self.edtCompulsoryPolisEndDate.date() else '')
                        messageBox = QtGui.QMessageBox()
                        messageBox.setIcon(QtGui.QMessageBox.Information)
                        messageBox.setWindowFlags(messageBox.windowFlags() | Qt.WindowStaysOnTopHint)
                        messageBox.setWindowTitle(u'Обновление полисных данных')
                        messageBox.setText(u'%s'
                                           u'Новый полис:\n'
                                           u'СМО: %s\n'
                                           u'серия: %s\n'
                                           u'номер: %s\n'
                                           u'вид: %s\n'
                                           u'действителен с %s%s\n'
                                           u'Обновить данные?\n' % (
                                               oldPolicyLabel, newInsurerName, newPolicySerial, newPolicyNumber,
                                               newPolicyKindName, forceString(newPolicyBegDate),
                                               u' по %s' % forceString(newPolicyEndDate) if newPolicyEndDate else ''))

                        btnUpdate = QtGui.QPushButton()
                        btnAdd = QtGui.QPushButton()
                        btnUpdate.setText(u'Обновить данные')
                        btnAdd.setText(u'Добавить новую запись')
                        messageBox.addButton(QtGui.QMessageBox.Cancel)
                        # если дата начала полиса отличаются, то показывать кнопку добавить
                        if newPolicyBegDate != self.edtCompulsoryPolisBegDate.date():
                            messageBox.addButton(btnAdd, QtGui.QMessageBox.ActionRole)
                            messageBox.setDefaultButton(btnAdd)
                        else:
                            messageBox.addButton(btnUpdate, QtGui.QMessageBox.ActionRole)
                            messageBox.setDefaultButton(btnUpdate)
                        messageBox.exec_()
                        if messageBox.clickedButton() == btnAdd:
                            # дата закрытия текущего полиса
                            row = self.modelPolicies.getCurrentPolicyRowInt(True)
                            if row > -1:
                                previousBegDate = forceDate(self.modelPolicies.items()[row].value('begDate'))
                                previousEndDate = forceDate(self.modelPolicies.items()[row].value('endDate'))
                                endDate = forceDate(
                                    newPolicyBegDate if newPolicyBegDate else QDate().currentDate()).addDays(-1)
                                if previousEndDate.isNull():
                                    if previousBegDate > endDate:
                                        endDate = previousBegDate
                                    self.modelPolicies.setValue(row, 'endDate', toVariant(endDate))

                            # добавление нового полиса
                            newRecord = self.modelPolicies.getEmptyRecord()
                            row = self.modelPolicies.rowCount()
                            newRecord.setValue('serial', toVariant(newPolicySerial))
                            newRecord.setValue('number', toVariant(newPolicyNumber))
                            newRecord.setValue('insurer_id', toVariant(newInsurerId))
                            if not newInsurerId:
                                newRecord.setValue('name', toVariant(newInsurerName))
                            newRecord.setValue('policyType_id',
                                               toVariant(db.translate('rbPolicyType', 'code', '1', 'id')))
                            newRecord.setValue('policyKind_id', toVariant(newPolicyKindId))
                            newRecord.setValue('begDate', toVariant(newPolicyBegDate))
                            newRecord.setValue('endDate', toVariant(newPolicyEndDate))
                            newRecord.setValue('checkDate', toVariant(checkDate))
                            self.modelPolicies.insertRecord(row, newRecord)
                            self.setPolicyRecord(newRecord, True)
                            self.setClientEnp(newPolicyKindCode, newPolicyNumber)
                        elif messageBox.clickedButton() == btnUpdate:
                            self.updateCompulsoryPolicyCompanyArea([newInsurerArea])
                            self.cmbCompulsoryPolisCompany.setValue(newInsurerId)
                            if newPolicySerial:
                                self.edtCompulsoryPolisSerial.setText(newPolicySerial)
                            else:
                                self.edtCompulsoryPolisSerial.clear()

                            self.edtCompulsoryPolisNumber.setText(newPolicyNumber)
                            self.cmbCompulsoryPolisType.setValue(db.translate('rbPolicyType', 'code', '1', 'id'))
                            self.cmbCompulsoryPolisKind.setValue(newPolicyKindId)
                            self.edtCompulsoryPolisBegDate.setDate(newPolicyBegDate)
                            self.edtCompulsoryPolisEndDate.setDate(newPolicyEndDate)
                            self.edtCompulsoryPolisName.setText('')
                            self.edtCompulsoryPolisNote.setText('')
                            self.syncPolicy(True)
                            row = self.modelPolicies.getCurrentCompulsoryPolicyRow(newPolicySerial, newPolicyNumber)
                            self.modelPolicies.setValue(row, 'checkDate', toVariant(checkDate))
                            self.setClientEnp(newPolicyKindCode, newPolicyNumber)
                        self.syncPolicy(True)
                else:
                    response = requests.get(servicesURL + '$sendIdentityPatient', params)
                    jsonData = response.json()

                    if jsonData.get('result', '') == 'success':
                        QtGui.QMessageBox().information(self, u'Заявка создана',
                                                        u'Идентификатор заявки: ' + jsonData.get('orderId', ''),
                                                        QtGui.QMessageBox.Close)
                    elif jsonData['detail'] == u"Свойство 'Серия и/или номер документа, удостоверяющего личность' не заполнено, 'docType' 'urn:oid:1.2.643.2.69.1.1.1.6.0' не найдено в сервисе терминологии 'urn:oid:1.2.643.2.69.1.1.1.6'":
                        QtGui.QMessageBox().critical(self, u'Ошибка',
                                                    u'Произошла ошибка:\n' + u'Необходимо указать документ',
                                                    QtGui.QMessageBox.Close)
                    elif jsonData['detail'] == u"Документ 'docNumber' указан в неверном формате":
                        QtGui.QMessageBox().critical(self, u'Ошибка', u'Произошла ошибка:\n' + u'Проверка страховой принадлежности в федеральном сегменте проводится только для единых полисов',
                                                     QtGui.QMessageBox.Close)
                    else:
                        QtGui.QMessageBox().critical(self, u'Ошибка', u'Произошла ошибка:\n' + jsonData['detail'],
                                                     QtGui.QMessageBox.Close)
            except Exception, e:
                QtGui.QMessageBox().critical(self, u'Ошибка', u'Произошла ошибка: ' + unicode(e),
                                             QtGui.QMessageBox.Close)

    def searchPolicy(self):
        db = QtGui.qApp.db
        docTypeId = self.cmbDocType.value()
        policyKindId = self.cmbCompulsoryPolisKind.value()
        docTypeRegionalCode = forceInt(QtGui.qApp.db.translate('rbDocumentType', 'id', docTypeId, 'regionalCode'))
        SerialSeparator = '-' if docTypeRegionalCode in (3, 1) else ' '
        docSeria = forceStringEx(self.edtDocSerialLeft.text() + SerialSeparator + self.edtDocSerialRight.text())
        docNumber = forceStringEx(self.edtDocNumber.text())
        policyKindCode = forceInt(QtGui.qApp.db.translate('rbPolicyKind', 'id', policyKindId, 'regionalCode'))
        policySerial = forceStringEx(self.edtCompulsoryPolisSerial.text())
        policyNumber = forceStringEx(self.edtCompulsoryPolisNumber.text())
        
        descr = QtGui.qApp.identService(forceStringEx(self.edtFirstName.text()),
                                       forceStringEx(self.edtLastName.text()),
                                       forceStringEx(self.edtPatrName.text()),
                                       self.cmbSex.currentIndex(),
                                       self.edtBirthDate.date(),
                                       forceStringEx(self.edtSNILS.text()).replace('-', '').replace(' ', ''),
                                       policyKindCode,
                                       policySerial,
                                       policyNumber,
                                       docTypeRegionalCode, 
                                       docSeria,
                                       docNumber)

        if descr and 'hicId' in descr and len(descr) > 3:
            if 'dd' in descr and descr.dd['VP']:
                ddMOCodeName = ' '.join([descr.dd['CODE_MO'], forceString(db.translate('Organisation', 'infisCode', descr.dd['CODE_MO'], 'shortName'))])
                ddVP = descr.dd['VP']
                if ddVP == '211':
                    ddVPstr = u'Проведена: диспансеризация взрослого населения'
                else:
                    ddVPstr = u'Проведен: профилактический осмотр'
                ddDATN = formatDate(QDate.fromString(descr.dd['DATN'], Qt.ISODate))
                ddDATO = formatDate(QDate.fromString(descr.dd['DATO'], Qt.ISODate))
                ddInfoStr = u'Найдена информация о проведенной ранее\n'\
                    u'диспансеризации/профилактическом осмотре:\n'\
                    u'%s\n'\
                    u'МО: %s\n'\
                    u'Период проведения с %s по %s' % (ddVPstr, ddMOCodeName, ddDATN, ddDATO)
            else:
                ddInfoStr = ''

            hicId = descr.hicId
            if hicId:
                hicName = forceString(db.translate('Organisation', 'id', hicId, 'shortName'))
            else:
                hicName = u'в справочнике не найдено: %s'%descr.hicName

            policyTypeCode = descr.typeCode
            policyTypeId = forceRef(db.translate('rbPolicyType', 'code', policyTypeCode, 'id'))
            if policyTypeId:
                policyTypeName = forceString(db.translate('rbPolicyType', 'id', policyTypeId, 'name'))
            else:
                policyTypeName = '-'

            policyKindCode = descr.kindCode
            policyKindId = forceRef(db.translate('rbPolicyKind', 'code', policyKindCode, 'id'))
            if policyKindId:
                policyKindName = forceString(db.translate('rbPolicyKind', 'id', policyKindId, 'name'))
            else:
                policyKindName = '-'

            covidSeverityTitle = ''
            if 'cv19Severity' in descr:
                covidSeverity = forceInt(descr.cv19Severity)
                if covidSeverity == 1:
                    covidSeverityTitle = u'Степень тяжести перенесенного COVID-19: легкое течение'
                elif covidSeverity == 2:
                    covidSeverityTitle = u'Степень тяжести перенесенного COVID-19: среднетяжелое течение'
                elif covidSeverity == 3:
                    covidSeverityTitle = u'Степень тяжести перенесенного COVID-19: тяжелое течение'
                elif covidSeverity == 4:
                    covidSeverityTitle = u'Степень тяжести перенесенного COVID-19: крайне тяжелое течение'

            socStatusCode = descr.SOC
            socStatus = u''
            if socStatusCode:
                socStatus = forceString(db.translate('rbSocStatusType', 'code', socStatusCode, 'name'))

            msgbox = QtGui.QMessageBox()
            msgbox.setIcon(QtGui.QMessageBox.Information)
            msgbox.setWindowFlags(msgbox.windowFlags() | Qt.WindowStaysOnTopHint)
            msgbox.setWindowTitle(u'Поиск полиса')
            msgbox.setText(u'Найден полис:\n'\
                u'Владелец:   %s %s %s, %s, %s\n'\
                u'СНИЛС:%s\n'\
                u'СМО:   %s\n'\
                u'серия: %s\n'\
                u'номер: %s\n'\
                u'тип:   %s\n'\
                u'вид:   %s\n'\
                u'действителен с %s по %s\n'\
                u'ЕНП: %s\n'\
                u'%s\n'\
                u'%s\n'\
                u'Обновить данные?\n\n%s' % (
                    nameCase(descr.lastName), nameCase(descr.firstName), nameCase(descr.patrName) if descr.patrName else '', [u'---', u'М', u'Ж'][descr.sex], forceString(descr.birthDate),
                    descr.snils,
                    hicName,
                    forceString(descr.policySerial),
                    descr.policyNumber,
                    policyTypeName,
                    policyKindName,
                    forceString(descr.begDate),
                    forceString(descr.endDate),
                    descr.ENP,
                    covidSeverityTitle,
                    socStatus,
                    ddInfoStr))

            btnUpdate = QtGui.QPushButton()
            btnAdd = QtGui.QPushButton()
            btnUpdate.setText(u'Обновить данные')
            btnAdd.setText(u'Добавить новую запись')

            msgbox.addButton(QtGui.QMessageBox.Cancel)

            # если дата начала полиса отличаются, то показывать кнопку добавить
            if forceDate(descr.begDate) != forceDate(self.edtCompulsoryPolisBegDate.date()):
                msgbox.addButton(btnAdd, QtGui.QMessageBox.ActionRole)
                msgbox.setDefaultButton(btnAdd)
            else:
                msgbox.addButton(btnUpdate, QtGui.QMessageBox.ActionRole)
                msgbox.setDefaultButton(btnUpdate)

            msgbox.exec_()
            if msgbox.clickedButton() in (btnAdd, btnUpdate):
                if descr.snils:
                    self.edtSNILS.setText(descr.snils)
                self.edtFirstName.setText(nameCase(descr.firstName))
                self.edtLastName.setText(nameCase(descr.lastName))
                self.edtPatrName.setText(nameCase(descr.patrName))
                self.edtBirthDate.setDate(descr.birthDate)
                self.cmbSex.setCurrentIndex(descr.sex)

                if msgbox.clickedButton() == btnAdd:
                    # дата закрытия текущего полиса
                    row = self.modelPolicies.getCurrentPolicyRowInt(True)
                    if row > -1:
                        previousBegDate = forceDate(self.modelPolicies.items()[row].value('begDate'))
                        previousEndDate = forceDate(self.modelPolicies.items()[row].value('endDate'))
                        endDate = forceDate(descr.begDate if descr.begDate else QDate().currentDate()).addDays(-1)
                        if previousEndDate.isNull():
                            if previousBegDate > endDate:
                                endDate = previousBegDate
                            self.modelPolicies.setValue(row, 'endDate', toVariant(endDate))

                    # добавление нового полиса
                    newRecord = self.modelPolicies.getEmptyRecord()
                    row = self.modelPolicies.rowCount()
                    newRecord.setValue('serial', toVariant(descr.policySerial))
                    newRecord.setValue('number', toVariant(descr.policyNumber))
                    newRecord.setValue('insurer_id', toVariant(hicId))
                    newRecord.setValue('policyType_id', toVariant(policyTypeId))
                    newRecord.setValue('policyKind_id', toVariant(policyKindId))
                    newRecord.setValue('begDate', toVariant(descr.begDate))
                    newRecord.setValue('endDate', toVariant(descr.endDate))
                    newRecord.setValue('checkDate', toVariant(QDateTime().currentDateTime()))
                    self.modelPolicies.insertRecord(row, newRecord)
                    self.setPolicyRecord(newRecord, True)
                    self.setClientEnp(descr.kindCode, descr.ENP)

                    if socStatusCode and socStatusCode != '000':
                        # tt4203 - не обнуляем данные соц статусов класса svo
                        self.setClientSocStatus(db, socStatusCode)

                elif msgbox.clickedButton() == btnUpdate:
                    self.cmbCompulsoryPolisCompany.setValue(hicId)
                    if descr.policySerial:
                        self.edtCompulsoryPolisSerial.setText(descr.policySerial)
                    else:
                        self.edtCompulsoryPolisSerial.clear()

                    self.edtCompulsoryPolisNumber.setText(descr.policyNumber)
                    self.cmbCompulsoryPolisType.setValue(policyTypeId)
                    self.cmbCompulsoryPolisKind.setValue(policyKindId)
                    self.edtCompulsoryPolisBegDate.setDate(descr.begDate)
                    self.edtCompulsoryPolisEndDate.setDate(descr.endDate)
                    self.edtCompulsoryPolisName.setText('')
                    self.edtCompulsoryPolisNote.setText('')
                    self.syncPolicy(True)
                    row = self.modelPolicies.getCurrentCompulsoryPolicyRow(descr.policySerial, descr.policyNumber)
                    self.modelPolicies.setValue(row, 'checkDate', toVariant(QDateTime().currentDateTime()))
                    self.setClientEnp(descr.kindCode, descr.ENP)

                    if socStatusCode and socStatusCode != '000':
                        # tt4203 - не обнуляем данные соц статусов класса svo
                        self.setClientSocStatus(db, socStatusCode)

                self.syncPolicy(True)
                return True
        else:
            servicesURL = forceString(QtGui.qApp.getGlobalPreference('23:servicesURL'))
            if not self.getClientId() or not servicesURL:
                messageBox = QtGui.QMessageBox(QtGui.QMessageBox.Information,
                                               u'Поиск полиса',
                                               u'Полис не найден',
                                               QtGui.QMessageBox.Ok)
                messageBox.setWindowFlags(messageBox.windowFlags() | Qt.WindowStaysOnTopHint)
                messageBox.exec_()
                return False
            self.searchPolicyInFederalService(servicesURL)

        return False


    def setClientSocStatus(self, db, socStatusCode):
        def checkSocStatusTypeClassAssoc(db, statusCode, svoClassId):
            # проверка, есть ли в rbSocStatusType тип соц статуса с кодом statusCode
            # с проставленной связью c классом svo
            tableAssoc = db.table('rbSocStatusClassTypeAssoc')
            tableType = db.table('rbSocStatusType')
            table = tableType.leftJoin(tableAssoc, tableType['id'].eq(tableAssoc['type_id']))
            record = db.getRecordEx(
                table, tableType['id'],
                [
                    tableType['code'].eq(statusCode),
                    tableAssoc['class_id'].eq(svoClassId)
                ]
            )
            if record:
                return True, forceInt(record.value('id'))
            else:
                return False, None

        socStatusSvoClassId = forceInt(db.translate('rbSocStatusClass', 'code', 'svo', 'id'))

        checkSocStatus, socStatusCodeId = checkSocStatusTypeClassAssoc(db, socStatusCode, socStatusSvoClassId)
        if not checkSocStatus:
            # если код соц статуса не занесён в rbSocStatusType,
            # то создаём с названием 'отсутствующая запись справочника "Социальная категория"'
            tableSocStatusType = db.table('rbSocStatusType')
            socStatusTypeRecord = tableSocStatusType.newRecord()
            socStatusTypeRecord.setValue('createDatetime', toVariant(QDateTime.currentDateTime()))
            socStatusTypeRecord.setValue('modifyDatetime', toVariant(QDateTime.currentDateTime()))
            socStatusTypeRecord.setValue('code', toVariant(socStatusCode))
            socStatusTypeRecord.setValue('name', toVariant(u'отсутствующая запись справочника "Социальная категория"'))
            socStatusTypeRecord.setValue('shortName', toVariant(''))
            socStatusTypeRecord.setValue('socCode', toVariant(''))
            socStatusTypeRecord.setValue('regionalCode', toVariant(socStatusCode))
            db.insertRecord(tableSocStatusType, socStatusTypeRecord)

            socStatusCodeId = forceInt(socStatusTypeRecord.value('id'))

            # и относим к классу соц статуса с кодом svo
            tableSocStatusClassTypeAssoc = db.table('rbSocStatusClassTypeAssoc')
            socStatusClassTypeAssocRecord = tableSocStatusClassTypeAssoc.newRecord()
            socStatusClassTypeAssocRecord.setValue('createDatetime', toVariant(QDateTime.currentDateTime()))
            socStatusClassTypeAssocRecord.setValue('modifyDatetime', toVariant(QDateTime.currentDateTime()))
            socStatusClassTypeAssocRecord.setValue('class_id', toVariant(socStatusSvoClassId))
            socStatusClassTypeAssocRecord.setValue('type_id', toVariant(socStatusCodeId))
            db.insertRecord(tableSocStatusClassTypeAssoc, socStatusClassTypeAssocRecord)

        socStatusExist = False
        tableAssoc = db.table('rbSocStatusClassTypeAssoc')
        socStatusTypeIds = db.getIdList(tableAssoc, idCol='type_id', where=tableAssoc['class_id'].eq(socStatusSvoClassId))

        for modelRow, item in enumerate(self.modelSocStatuses.items()):
            typeId = forceInt(item.value('socStatusType_id'))
            classId = forceInt(item.value('socStatusClass_id'))
            deleted = forceInt(item.value('deleted'))
            if (typeId in socStatusTypeIds and classId == socStatusSvoClassId) and socStatusCodeId != typeId and not deleted:
                # если уже существует не удалённый соц статус с другим кодом, то помечаем его удалённым
                # socStatusExist = True
                item.setValue('modifyDatetime', toVariant(QDateTime.currentDateTime()))
                item.setValue('deleted', QVariant(1))
                item.changed = True
            elif (typeId in socStatusTypeIds and classId == socStatusSvoClassId) and socStatusCodeId == typeId:
                socStatusExist = True
        if not socStatusExist and socStatusCodeId and socStatusSvoClassId:
            record = self.modelSocStatuses.getEmptyRecord()
            record.setValue('socStatusClass_id', QVariant(socStatusSvoClassId))
            record.setValue('socStatusType_id', QVariant(socStatusCodeId))
            record.changed = True
            self.modelSocStatuses.addRecord(record)


    def setClientEnp(self, policyKindCode, enp):
        if policyKindCode != '3' and forceString(enp):
            accountingSystemId = forceRef(QtGui.qApp.db.translate('rbAccountingSystem', 'code', 'ENP', 'id'))
            if accountingSystemId:
                exists = False
                for row, item in enumerate(self.modelClientIdentification.items()):
                    if forceInt(item.value('accountingSystem_id')) == forceInt(accountingSystemId):
                        exists = True
                        item.setValue('identifier', toVariant(forceString(enp)))
                        item.setValue('client_id', toVariant(forceRef(self.getClientId())))
                        self.modelClientIdentification.emitRowChanged(row)
                        break
                if not exists:
                    record = self.modelClientIdentification.getEmptyRecord()
                    record.setValue('accountingSystem_id', toVariant(forceRef(accountingSystemId)))
                    record.setValue('identifier', toVariant(forceString(enp)))
                    record.setValue('client_id', toVariant(forceRef(self.getClientId())))
                    self.modelClientIdentification.items().append(record)


    @pyqtSignature('QString')
    def on_edtCompulsoryPolisSerial_textEdited(self, text):
        self.cmbCompulsoryPolisCompany.setSerialFilter(text)
        self.updateCompulsoryPolicyType()
        self.updateCompulsoryPolicyKind()


    @pyqtSignature('QString')
    def on_edtCompulsoryPolisNumber_textEdited(self, text):
        if not self.cmbCompulsoryPolisType.value():
            self.cmbCompulsoryPolisType.setCurrentIndex(1)
        self.updateCompulsoryPolicyKind()


    @pyqtSignature('int')
    def on_cmbCompulsoryPolisCompany_currentIndexChanged(self, index):
        self.updateCompulsoryPolicyType()



    @pyqtSignature('QString')
    def on_edtVoluntaryPolisSerial_textEdited(self, text):
        self.cmbVoluntaryPolisCompany.setSerialFilter(text)
        self.updateVoluntaryPolicyType()


    @pyqtSignature('QString')
    def on_edtVoluntaryPolisNumber_textEdited(self, text):
        if not self.cmbVoluntaryPolisType.value():
            self.cmbVoluntaryPolisType.setCurrentIndex(1)


    @pyqtSignature('int')
    def on_cmbVoluntaryPolisCompany_currentIndexChanged(self, index):
        self.updateVoluntaryPolicyType()


    @pyqtSignature('')
    def on_modelPolicies_policyChanged(self):
        items = self.modelPolicies.items()
        self.clientPolicyInfoList = []
        for isCompulsory in (True, False):
            row = self.modelPolicies.getCurrentPolicyRowInt(isCompulsory)
            policyRecord = items[row] if 0<=row<len(items) else None
            self.setPolicyRecord(policyRecord, isCompulsory)
            if policyRecord:
                self.clientPolicyInfoList.append((forceRef(policyRecord.value('insurer_id')), forceRef(policyRecord.value('policyType_id'))))


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelSocStatusesSort_currentChanged(self, current, previous):
        dirty = self.isDirty()
        model = self.tblSocStatuses.model()
        row = current.row()
        if hasattr(model, 'mapToSource'):
            sourceIndex = model.mapToSource(current)
            row = sourceIndex.row()
#        column = current.column()
        if 0<=row<len(self.modelSocStatuses.items()):
            docTypeId, serial, number, date, origin = self.modelSocStatuses.getDocInfo(row)
            self.frmSocStatusDocument.setEnabled(True)
            if not docTypeId:
                docTypeId, serial, number, date, origin = None, '', '', QDate(), ''
                item = self.modelSocStatuses.items()[row]
#                documentId = forceRef(item.value('document_id'))
                socStatusTypeId = forceRef(item.value('socStatusType_id'))
                if socStatusTypeId:
                    db = QtGui.qApp.db
                    tableRBSocStatusType = db.table('rbSocStatusType')
                    record = db.getRecordEx(tableRBSocStatusType, [tableRBSocStatusType['documentType_id']], [tableRBSocStatusType['id'].eq(socStatusTypeId)])
                    if record:
                        docTypeId = forceRef(record.value('documentType_id'))
                        #self.edtSocStatusDocSerial.setFocus(Qt.ShortcutFocusReason)
        else:
            docTypeId, serial, number, date, origin = None, '', '', QDate(), ''
            self.cmbSocStatusDocType.setEnabled(False)
            self.frmSocStatusDocument.setEnabled(False)
        self.cmbSocStatusDocType.setValue(docTypeId)
        self.edtSocStatusDocSerial.setText(serial)
        self.edtSocStatusDocNumber.setText(number)
        self.edtSocStatusDocDate.setDate(date)
        self.edtSocStatusDocOrigin.setText(origin)
        if 0 <= row < len(self.modelSocStatuses.items()):
            isNeedFillOutDoc = QtGui.qApp.db.getRecord('rbSocStatusType', 'needFillOutDoc',
                                                       self.modelSocStatuses.items()[row].value(
                                                           'socStatusType_id').toString())
            showInDoc = forceInt(isNeedFillOutDoc.value(0)) if isNeedFillOutDoc and forceBool(self.modelSocStatuses.items()[row].value('socStatusClass_id')) else 0
            for elem in [self.cmbSocStatusDocType, self.edtSocStatusDocDate, self.edtSocStatusDocNumber,
                         self.edtSocStatusDocSerial, self.edtSocStatusDocOrigin]:
                elem.setEnabled(forceBool(showInDoc))
        self.setIsDirty(dirty)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelSocStatusesSort_dataChanged(self, current, bottomRight):
        dirty = self.isDirty()
        model = self.tblSocStatuses.model()
        row = current.row()
        column = current.column()
        if hasattr(model, 'mapToSource'):
            sourceIndex = model.mapToSource(current)
            row = sourceIndex.row()
            column = sourceIndex.column()

        if column in (0, 1):
            if 0 <= row < len(self.modelSocStatuses.items()):
                isNeedFillOutDoc = QtGui.qApp.db.getRecord('rbSocStatusType', 'needFillOutDoc',
                                                           self.modelSocStatuses.items()[row].value(
                                                               'socStatusType_id').toString())
                showInDoc = forceInt(isNeedFillOutDoc.value(0)) if isNeedFillOutDoc and forceBool(self.modelSocStatuses.items()[row].value('socStatusClass_id')) else 0
                for elem in [self.cmbSocStatusDocType, self.edtSocStatusDocDate, self.edtSocStatusDocNumber,
                             self.edtSocStatusDocSerial, self.edtSocStatusDocOrigin]:
                    elem.setEnabled(forceBool(showInDoc))
                if not forceBool(self.modelSocStatuses.items()[row].value(0)):
                    self.modelSocStatuses.items()[row].setValue('socStatusType_id', QVariant(None))

        self.setIsDirty(dirty)


    @pyqtSignature('int')
    def on_cmbSocStatusDocType_currentIndexChanged(self,  index):
        docTypeId = self.cmbSocStatusDocType.value()
        docTypeOk = bool(docTypeId)
        self.edtSocStatusDocSerial.setEnabled(docTypeOk)
        self.edtSocStatusDocSerial.setFocus(Qt.ShortcutFocusReason)
        self.edtSocStatusDocNumber.setEnabled(docTypeOk)
        self.edtSocStatusDocDate.setEnabled(docTypeOk)
        self.edtSocStatusDocOrigin.setEnabled(docTypeOk)
        self.updateSocStatus('documentType_id', docTypeId)


    @pyqtSignature('QString')
    def on_edtSocStatusDocSerial_textEdited(self, text):
        self.updateSocStatus('serial', text)


    @pyqtSignature('QString')
    def on_edtSocStatusDocNumber_textEdited(self, text):
        self.updateSocStatus('number', text)


    @pyqtSignature('QDate')
    def on_edtSocStatusDocDate_dateChanged(self, date):
        self.updateSocStatus('date', date)


    @pyqtSignature('QString')
    def on_edtSocStatusDocOrigin_textEdited(self, text):
        self.updateSocStatus('origin', text)


    @pyqtSignature('')
    def on_btnCopyPrevWork_clicked(self):
        if CClientEditDialog.prevWork:
            self.setWork(CClientEditDialog.prevWork)


    @pyqtSignature('int')
    def on_cmbWorkOrganisation_currentIndexChanged(self, index):
        self.updateWorkOrganisationInfo()


    @pyqtSignature('')
    def on_btnSelectWorkOrganisation_clicked(self):
        orgId = selectOrganisation(self, self.cmbWorkOrganisation.value(), False)
        self.cmbWorkOrganisation.updateModel()
        if orgId:
            self.setIsDirty()
            self.cmbWorkOrganisation.setValue(orgId)


    @pyqtSignature('')
    def on_btnRegHouseList_clicked(self):
        streetCode = forceString(self.cmbRegStreet.code())
        if not streetCode:
            cityCode = forceString(self.cmbRegCity.code())
            streetCode = cityCode + u'000000'
        self.getHouseList(streetCode, 0)


    @pyqtSignature('')
    def on_btnLocHouseList_clicked(self):
        streetCode = forceString(self.cmbLocStreet.code())
        if not streetCode:
            cityCode = forceString(self.cmbLocCity.code())
            streetCode = cityCode + u'000000'
        self.getHouseList(streetCode, 1)

    def checkHouseList(self, streetCode, typeAddress):
        result = True
        if streetCode:
            if not typeAddress:
                house = forceString(self.edtRegHouse.text())
                corp = forceString(self.edtRegCorpus.text())
                result = self.clientRegHousesList.checkHouse(house, corp)
            else:
                house = forceString(self.edtLocHouse.text())
                corp = forceString(self.edtLocCorpus.text())
                result = self.clientLocHousesList.checkHouse(house, corp)
        return result

    def getHouseListCheckResult(self, typeAddress):
        dialog = self.getHouseListDialog(typeAddress)
        return dialog.getHouseListCheckResult()


    def getHouseList(self, streetCode, typeAddress):
        if streetCode:
            #dialog = self.getHouseListDialog(typeAddress, streetCode)
            if not typeAddress:
                house = forceString(self.edtRegHouse.text())
                corp = forceString(self.edtRegCorpus.text())
                house, corp = self.clientRegHousesList.showHousesList(streetCode, house, corp)
                self.edtRegHouse.setText(house)
                self.edtRegCorpus.setText(corp)
            else:
                house = forceString(self.edtLocHouse.text())
                corp = forceString(self.edtLocCorpus.text())
                house, corp = self.clientLocHousesList.showHousesList(streetCode, house, corp)
                self.edtLocHouse.setText(house)
                self.edtLocCorpus.setText(corp)

    @pyqtSignature('int')
    def on_cmbWorkOKVED_currentIndexChanged(self,  index):
        self.edtOKVEDName.setText(getOKVEDName(self.cmbWorkOKVED.text()))
        self.edtOKVEDName.setCursorPosition(0)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelWorkHurts_currentChanged(self, current, previous):
        dirty = self.isDirty()
        # row = current.row()
        # factors = self.modelWorkHurts.factors(row)
        # self.modelWorkHurtFactors.setItems(factors)
        self.setIsDirty(dirty)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelClientQuoting_currentChanged(self, current, previous):
        row = current.row()
        modelItems = self.modelClientQuoting.items()
        if row < len(modelItems):
            self.__quotaRecord = modelItems[row]
            self.modelClientQuotingDiscussion.setIdList(
                    self.selectClientQuotingDiscussion(
                    forceInt(self.__quotaRecord.value('id'))))
            self.modelClientQuoting.loadItemsInfo(row)
            self.setQuotaWidgets(True)
        else:
            self.modelClientQuotingDiscussion.setIdList([])
            self.setEnabledQuotaWidgets(False)
            self.__quotaRecord = None
            self.modelClientQuoting.loadItemsInfo(None)
        self.setQuotingInfo()

    @pyqtSignature('QString')
    def on_edtQuotaIdentifier_textEdited(self, text):
        self.__quotaRecord.setValue('identifier', QVariant(text))


    @pyqtSignature('int')
    def on_edtQuotaStage_valueChanged(self, val):
        self.__quotaRecord.setValue('stage', QVariant(val))
        index = self.tblClientQuoting.currentIndex()
        if index.isValid():
            self.modelClientQuoting.emitRowChanged(index.row())


    @pyqtSignature('QString')
    def on_edtQuotaTicket_textEdited(self, text):
        self.__quotaRecord.setValue('quotaTicket', QVariant(text))


    @pyqtSignature('int')
    def on_edtQuotaAmount_valueChanged(self, val):
        self.__quotaRecord.setValue('amount', QVariant(val))


    @pyqtSignature('QString')
    def on_cmbQuotaMKB_textChanged(self, text):
        self.__quotaRecord.setValue('MKB', QVariant(text))
        if self.setMKBTextInfo(text):
            index = self.tblClientQuoting.currentIndex()
            if index.isValid():
                self.modelClientQuoting.emitRowChanged(index.row())

    @pyqtSignature('int')
    def on_cmbQuotaRequest_currentIndexChanged(self, index):
        self.__quotaRecord.setValue('request', QVariant(index))


    @pyqtSignature('QDate')
    def on_edtQuotaDirectionDate_dateChanged(self, date):
        self.__quotaRecord.setValue('directionDate', QVariant(date))


    @pyqtSignature('int')
    def on_cmbQuotaLPU_currentIndexChanged(self, index):
        val = self.cmbQuotaLPU.value()
        self.__quotaRecord.setValue('org_id', QVariant(val))


    @pyqtSignature('QString')
    def on_edtQuotaLPUFreeInput_textEdited(self, text):
        self.__quotaRecord.setValue('freeInput', QVariant(text))


    @pyqtSignature('QDate')
    def on_edtQuotaDateRegistration_dateChanged(self, date):
        self.__quotaRecord.setValue('dateRegistration', QVariant(date))


    @pyqtSignature('QDate')
    def on_edtQuotaDateEnd_dateChanged(self, date):
        self.__quotaRecord.setValue('dateEnd', QVariant(date))
#        self.modelClientQuoting.setIsActiveByDate(date)


    @pyqtSignature('int')
    def on_cmbQuotaOrgStructure_currentIndexChanged(self, index):
        val = self.cmbQuotaOrgStructure.value()
        self.__quotaRecord.setValue('orgStructure_id', QVariant(val))


    @pyqtSignature('int')
    def on_cmbQuotaStatus_currentIndexChanged(self, index):
        self.__quotaRecord.setValue('status', QVariant(index))
        tblIndex = self.tblClientQuoting.currentIndex()
        if tblIndex.isValid():
            self.modelClientQuoting.emitRowChanged(tblIndex.row())

    @pyqtSignature('')
    def on_edtQuotaStatment_textChanged(self):
        text = self.edtQuotaStatment.toPlainText()
        self.__quotaRecord.setValue('statment', QVariant(text))


    @pyqtSignature('int')
    def on_cmbQuotaKladr_currentIndexChanged(self, index):
        data = self.cmbQuotaKladr.itemData(index)
        self.__quotaRecord.setValue('regionCode', data)
        self.cmbQuotaDistrictKladr.setKladrCode(data)


    @pyqtSignature('int')
    def on_cmbQuotaDistrictKladr_currentIndexChanged(self, index):
        okato = self.cmbQuotaDistrictKladr.value()
        self.__quotaRecord.setValue('districtCode', toVariant(okato))


    @pyqtSignature('bool')
    def on_chkDeathDate_clicked(self, state):
        self.edtDeathDate.setEnabled(state)
        self.edtDeathTime.setEnabled(state)
        self.lblDeathReason.setEnabled(state)
        self.cmbDeathReason.setEnabled(state)
        self.lblDeathPlaceType.setEnabled(state)
        self.cmbDeathPlaceType.setEnabled(state)
        if state:
            self.edtDeathDate.setDate(QDate.currentDate())
        else:
            self.edtDeathDate.setDate(None)
            self.edtDeathTime.setTime(QTime(0, 0, 0, 0))
        self.syncPersonalInfo()


    @pyqtSignature('int')
    def on_cmbWorkPost_currentIndexChanged(self, index):
        self.edtWorkPost.setEnabled(index == 0)


    @pyqtSignature('bool')
    def on_chkForcedTreatmentBegDate_clicked(self, state):
        self.edtForcedTreatmentBegDate.setEnabled(state)
        if state:
            self.edtForcedTreatmentBegDate.setDate(QDate.currentDate())
        else:
            self.edtForcedTreatmentBegDate.setDate(None)


    @pyqtSignature('')
    def on_btnSearchClientAttach_clicked(self):
        personInfo = self.getAttachmentPersonInfo()
        checkClientAttachService(personInfo)


    def tblAttaches_delChecker(self, rows):
        canRemove = False
        for row in rows:
            syncDate = forceDate(self.tblAttaches.model().items()[row].value('syncDate'))
            canRemove = True if not syncDate or QtGui.qApp.userHasRight(urRegDeleteAttachSync) else False
            if not canRemove:
                break
        return canRemove


    @pyqtSignature('')
    def on_btn_FERZL_clicked(self):
        from Registry.Ferzl_service import Ferzl_service
        try:
            service = Ferzl_service()
            param_dict = {}
            if self.edtDocSerialLeft.text() != u'' or self.edtDocSerialRight.text() != u'' or self.edtDocNumber.text() != u"":
                docTypeId = self.cmbDocType.value()
                docTypeCode = None
                if docTypeId:
                    docTypeCode = forceString(QtGui.qApp.db.translate('rbDocumentType', 'id', docTypeId, 'regionalCode'))
                param_dict['dudlType'] = docTypeCode
            if param_dict.get('dudlType', None):
                if int(param_dict.get('dudlType')) == 14:
                    if self.edtDocSerialLeft.text() and self.edtDocSerialRight.text():
                        param_dict['dudlSer'] = (self.edtDocSerialLeft.text() + ' ' + self.edtDocSerialRight.text())
                        param_dict['dudlNum'] = self.edtDocNumber.text()
                    else:
                        if (not self.edtDocSerialLeft.text()) and self.edtDocSerialRight.text():
                            param_dict['dudlSer'] = self.edtDocSerialRight.text()
                            param_dict['dudlNum'] = self.edtDocNumber.text()
                        elif self.edtDocSerialLeft.text() and  not(self.edtDocSerialRight.text()):
                            param_dict['dudlSer'] = self.edtDocSerialLeft.text()
                            param_dict['dudlNum'] = self.edtDocNumber.text()

                elif int(param_dict.get('dudlType')) == 3:
                    if self.edtDocSerialLeft.text() and self.edtDocSerialRight.text():
                        param_dict['dudlSer'] = (self.edtDocSerialLeft.text() + '-' + self.edtDocSerialRight.text())
                        param_dict['dudlNum'] = self.edtDocNumber.text()

                    else:
                        if (not self.edtDocSerialLeft.text()) and self.edtDocSerialRight.text():
                            param_dict['dudlSer'] = self.edtDocSerialRight.text()
                            param_dict['dudlNum'] = self.edtDocNumber.text()
                        elif self.edtDocSerialLeft.text() and  not(self.edtDocSerialRight.text()):
                            param_dict['dudlSer'] = self.edtDocSerialLeft.text()
                            param_dict['dudlNum'] = self.edtDocNumber.text()
                else:
                    param_dict['dudlNum'] = self.edtDocNumber.text()

            enp = self.edtCompulsoryPolisNumber.text()
            param_dict['enp'] = enp
            param_dict['dt'] = forceString(date.today().strftime('%Y-%m-%d'))
            param_dict['show'] = u'ATTACH PERSON OMS_POLICY'
            external_id = str(uuid.uuid5(uuid.UUID(bytes='Client'.ljust(16, '\0')), repr(self.getClientId())))
            param_dict['external_id'] = external_id
            result_service = service.getInsuranceStatus(param_dict)
            
            if result_service:
                if result_service.get('result',None):
                    elements = result_service.get('elements', None)
                    if elements:
                        gender = elements.get('gender', None)
                        if gender:
                            if self.cmbSex.currentIndex() != forceInt(gender):
                                self.cmbSex.setCurrentIndex(forceInt(gender))
                        pcySer = elements.get('policySer', None)
                        pcyNum = elements.get('policyNumEnp', None)
                        polisDateB = elements.get('policyValidFrom', None)
                        pcyType = elements.get('policyType', None)
                        if pcyNum or pcySer:
                            if pcyNum:
                                self.edtCompulsoryPolisNumber.setText(pcyNum)
                                self.cmbCompulsoryPolisType.setValue(1)
                            if pcySer:
                                self.edtCompulsoryPolisSerial.setText(pcySer)
                                
                        if polisDateB:
                            polisDateB = QDate.fromString(polisDateB, "dd.MM.yyyy")
                            self.edtCompulsoryPolisBegDate.setDate(forceDate(polisDateB))
                        if pcyType:
                            pcyType_request = u"select id from rbPolicyKind where code = '/*CODE*/' "
                            if pcyType == u'П':
                                pcyType_request = pcyType_request.replace(u'/*CODE*/', u'3')
                                pcyType_query = QtGui.qApp.db.query(pcyType_request)
                                if pcyType_query.next():
                                    pcyType_id = pcyType_query.record().value('id')
                                    if pcyType_id:
                                        self.cmbCompulsoryPolisKind.setValue(forceInt(pcyType_id))
                            elif pcyType == u'С':
                                pcyType_request = pcyType_request.replace(u'/*CODE*/', u'1')
                                pcyType_query = QtGui.qApp.db.query(pcyType_request)
                                if pcyType_query.next():
                                    pcyType_id = pcyType_query.record().value('id')
                                    if pcyType_id:
                                        self.cmbCompulsoryPolisKind.setValue(forceInt(pcyType_id))
                            elif pcyType == u'В':
                                pcyType_request = pcyType_request.replace(u'/*CODE*/', u'2')
                                pcyType_query = QtGui.qApp.db.query(pcyType_request)
                                if pcyType_query.next():
                                    pcyType_id = pcyType_query.record().value('id')
                                    if pcyType_id:
                                        self.cmbCompulsoryPolisKind.setValue(forceInt(pcyType_id))
                            elif pcyType == u'Э':
                                pcyType_request = pcyType_request.replace(u'/*CODE*/', u'4')
                                pcyType_query = QtGui.qApp.db.query(pcyType_request)
                                if pcyType_query.next():
                                    pcyType_id = pcyType_query.record().value('id')
                                    if pcyType_id:
                                        self.cmbCompulsoryPolisKind.setValue(forceInt(pcyType_id))
                            elif pcyType == u'К':
                                pcyType_request = pcyType_request.replace(u'/*CODE*/', u'5')
                                pcyType_query = QtGui.qApp.db.query(pcyType_request)
                                if pcyType_query.next():
                                    pcyType_id = pcyType_query.record().value('id')
                                    if pcyType_id:
                                        self.cmbCompulsoryPolisKind.setValue(forceInt(pcyType_id))
# enp = polis.get('policyNumEnp', None) - передаётся в одно поле с номером описание "Номер полиса ОМС или ЕНП" как определять енп или номер полиса я хз,
# возможно если тип полиса "Х - Состояние на учёте без полиса ОМС" то это будет ЕНП, на текщий момент не знаю куда это прописать.
#                             elif pcyType == u'Х':
#                                 enp = polis.get('policyNumEnp', None)

                        insurfCode = elements.get('smo', None)
                        insurfOkato = elements.get('terr', None)
                        if insurfCode:
                            insurf_request = u"SELECT id from Organisation WHERE 1=1 and 2=2 and 3=3"
                            if insurfCode:
                                insurf_request = insurf_request.replace(u'1=1', u"smoCode = '" + forceString(insurfCode) + u"'")
                            if insurfOkato:
                                insurf_request = insurf_request.replace(u'2=2', u"OKATO = '" + forceString(insurfOkato) + u"'")
                            insurf_query = QtGui.qApp.db.query(insurf_request)
                            if insurf_query.next():
                                insurf_id = insurf_query.record().value('id')
                                if insurf_id:
                                    self.cmbCompulsoryPolisCompany.setValue(forceInt(insurf_id))
                        else:
                            insurf_string = u""
                            if insurfCode:
                                insurf_string = insurf_string + forceString(insurfCode)
                            self.edtCompulsoryPolisName.setText(insurf_string)
                        oip = elements.get('oip', None)
                        if oip:
                            request_identification = u"SELECT id FROM rbAccountingSystem  WHERE code = 'FERZL_patient'"
                            query_identification = QtGui.qApp.db.query(request_identification)
                            if query_identification.next():
                                accountingSystemId = query_identification.record().value('id')
                                exists = False
                                if accountingSystemId:
                                    for row, item in enumerate(self.modelClientIdentification.items()):
                                        if forceInt(item.value('accountingSystem_id')) == forceInt(accountingSystemId):
                                            exists = True
                                            item.setValue('identifier', toVariant(forceString(oip)))
                                            item.setValue('client_id', toVariant(forceRef(self.getClientId())))
                                            self.modelClientIdentification.emitRowChanged(row)
                                            break
                                    if not exists:
                                        record = self.modelClientIdentification.getEmptyRecord()
                                        record.setValue('accountingSystem_id', toVariant(forceRef(accountingSystemId)))
                                        record.setValue('identifier', toVariant(forceString(oip)))
                                        record.setValue('client_id', toVariant(forceRef(self.getClientId())))
                                        self.modelClientIdentification.items().append(record)

        except Exception as e:
            print(str(e))

    def hide_show_btn_findNR(self):
        if QtGui.qApp.gis_oms_enable():
            date_birth = self.edtBirthDate.date()
            current_date = date.today()
            # last_month = date(current_date.year, current_date.month-1, current_date.day)
            ninety_days_ago = current_date - timedelta(days=90)
            if ninety_days_ago <= date(date_birth.year(), date_birth.month(), date_birth.day()) <= current_date:
            # if last_month <= date(date_birth.year(), date_birth.month(), date_birth.day()) <= current_date:
                self.btn_findNR.setVisible(True)
            else:
                self.btn_findNR.setVisible(False)

    
    @pyqtSignature('')
    def on_btn_findNR_clicked(self):
        from Registry.Ferzl_service import Ferzl_service
        try:
            services = Ferzl_service()
            param_dict = {}
            if self.edtLastName.text():
                param_dict['surnameEstim'] = self.edtLastName.text()
            param_dict['gender'] = self.cmbSex.currentIndex() if self.cmbSex.currentIndex() != 0 else None
            if not self.edtBirthDate.date().isNull():
                date_birth = self.edtBirthDate.date()
                param_dict['birthdaySince'] = forceString((date(date_birth.year(),date_birth.month(),date_birth.day()) - timedelta(days=15)).strftime('%Y-%m-%d'))
                param_dict['birthdayTill'] = forceString((date(date_birth.year(),date_birth.month(),date_birth.day())+ timedelta(days=15)).strftime('%Y-%m-%d'))
            external_id = str(uuid.uuid5(uuid.UUID(bytes='Client'.ljust(16, '\0')), repr(self.getClientId())))
            param_dict['external_id'] = external_id

            found_nrs = services.findNRs(param_dict)

            if found_nrs and found_nrs != QtGui.QMessageBox.Cancel:
                elements = found_nrs.get('elements', None)
                if elements:
                    surname = elements.get('surnameEstim', None)
                    if surname:
                        self.edtLastName.setText(surname)
                    birthDate = elements.get('birthday', None)
                    if birthDate:
                        birthDate = datetime.datetime.strptime(birthDate, "%d.%m.%Y")
                        self.edtBirthDate.setDate(forceDate(birthDate))
                    deathDate = elements.get('deathday', None)
                    if deathDate:
                        deathDate = datetime.datetime.strptime(deathDate, "%d.%m.%Y")
                        self.chkDeathDate.setChecked(True)
                        self.edtDeathDate.setDate(forceDate(deathDate))
                    gender = elements.get('gender', None)
                    if gender:
                        self.cmbSex.setCurrentIndex(forceInt(gender))
                    seqTotal = elements.get('seqTotal', None)
                    if seqTotal:
                        if forceInt(seqTotal) > 1:
                            seqNum = elements.get('seqNum', None)
                            if seqNum:
                                self.edtBirthNumber.setValue(forceInt(seqNum))
                        else:
                            self.edtBirthNumber.setValue(0)
                    nbWeight = elements.get('nbWeight', None)
                    if nbWeight:
                        self.edtBirthWeight.setValue(forceInt(nbWeight))
                    nbHeight = elements.get('nbHeight', None)
                    if nbHeight:
                        self.edtBirthHeight.setValue(forceInt(nbHeight))
                    docs = elements.get('docs', None)
                    if docs and len(docs) > 0:
                        doc = docs[0]
                        type = doc.get('type', None)
                        if type:
                            if type == u'33':
                                docType_request = u"SELECT master_id FROM rbDocumentType_Identification where value = '249' "
                                docType_query = QtGui.qApp.db.query(docType_request)
                                if docType_query.next():
                                    docType_record = docType_query.record().value('master_id')
                                    if docType_record:
                                        self.cmbDocType.setValue(forceInt(docType_record))
                                        docSer = doc.get('docSer', None)
                                        if docSer:
                                            self.edtDocSerialLeft.setText(docSer)
                                        docNum = doc.get('docNum', None)
                                        if docNum:
                                            self.edtDocNumber.setText(docNum)
                    oip = elements.get('oip', None)
                    if oip:
                        request_identification = u"SELECT id FROM rbAccountingSystem  WHERE code = 'FERZL_patient'"
                        query_identification = QtGui.qApp.db.query(request_identification)
                        if query_identification.next():
                            needed_id = query_identification.record().value('id')
                            exists = False
                            if needed_id:
                                for row, item in enumerate(self.modelClientIdentification.items()):
                                    if forceInt(item.value('accountingSystem_id')) == forceInt(needed_id):
                                        exists = True
                                        item.setValue(u'identifier', toVariant(forceString(oip)))
                                        item.setValue(u'client_id', toVariant(forceRef(self.getClientId())))
                                        self.modelClientIdentification.emitRowChanged(row)
                                        break
                                if not exists:
                                    record_identification = self.tblClientIdentification.model().getEmptyRecord()
                                    record_identification.setValue(u'accountingSystem_id', toVariant(forceInt(needed_id)))
                                    record_identification.setValue(u'identifier', toVariant(oip))
                                    record_identification.setValue(u'note', toVariant(forceString(u"ГИС ОМС ФЕРЗЛ")))
                                    self.tblClientIdentification.model().addRecord(record_identification)


        except Exception as e:
            print(str(e))

def checkSNILSEntered(self):
    SNILS = unformatSNILS(forceStringEx(self.edtSNILS.text()))
    if SNILS:
        if len(SNILS) != 11 or any([str(i)*3 in SNILS[:-2] for i in range(10)]):
            return self.checkValueMessage(u'Сохранение невозможно\nВведен некорректный номер СНИЛС', False, self.edtSNILS)
        elif not checkSNILS(SNILS):
            fixedSNILS = formatSNILS(fixSNILS(SNILS))
            res = QtGui.QMessageBox.question(self,
                                             u'Внимание!',
                                             u'СНИЛС указан с ошибкой.\nПравильный СНИЛС %s\nИсправить?' % fixedSNILS,
                                             QtGui.QMessageBox.Yes|QtGui.QMessageBox.No,
                                             QtGui.QMessageBox.Yes)
            if res == QtGui.QMessageBox.Yes:
                self.edtSNILS.setText(fixedSNILS)
            else:
                self.edtSNILS.setFocus(Qt.ShortcutFocusReason)
                return False
    return True

#    @pyqtSignature('')
#    def on_btnPrint_clicked(self):
#        if not self.checkDataEntered():
#            return
#        db = QtGui.qApp.db
#        record = self.getRecord()
#
#        printer = QtGui.QPrinter(QtGui.QPrinter.HighResolution)
#
#        printer.setFullPage(True)
##        printer.setOrientation(QtGui.QPrinter.Landscape)
#        printer.setOrientation(QtGui.QPrinter.Portrait)
#        printer.setPageSize(QtGui.QPrinter.A5)
##
#        if QtGui.qApp.keyboardModifiers() & Qt.ControlModifier:
#            dlg = QtGui.QPrintDialog(printer, self)
#            dlg.setWindowTitle(u'Печать информации о пациенте')
#            if dlg.exec_() != QtGui.QDialog.Accepted:
#                return
#
#        patientId = db.insertOrUpdate(tblPatients, record)
#        record.setValue(patId, toVariant(patientId))
#        self.setIsDirty(False)
#
#        textDocument = QtGui.QTextDocument()
#        textDocument.setHtml(getPatientInfoAsHTMLEx2(record))
##        textDocument.setPageSize(QSizeF(210.0*2, 148.0*2))
##        textDocument.setPageSize(QSizeF(printer.width(), printer.height()))
##        body = QRectF(0, 0, p.device()->width(), p.device()->height());
#
##        textDocument.setDefaultFont(font)
#        textDocument.print_(printer)
#
#    @pyqtSignature('')
#    def on_btnPrintTalon_clicked(self):
#        if not self.checkDataEntered():
#            return
#        db = QtGui.qApp.db
#        record = self.getRecord()
#
#        printer = QtGui.QPrinter(QtGui.QPrinter.HighResolution)
#
#        printer.setFullPage(True)
##        printer.setOrientation(QtGui.QPrinter.Landscape)
#        printer.setOrientation(QtGui.QPrinter.Portrait)
#        printer.setPageSize(QtGui.QPrinter.A5)
##
#        if QtGui.qApp.keyboardModifiers() & Qt.ControlModifier:
#            dlg = QtGui.QPrintDialog(printer, self)
#            dlg.setWindowTitle(u'Печать заготовки стат.талона')
#            if dlg.exec_() != QtGui.QDialog.Accepted:
#                return
#
#        patientId = db.insertOrUpdate(tblPatients, record)
#        record.setValue(patId, toVariant(patientId))
#        self.setIsDirty(False)
#
#        textDocument = QtGui.QTextDocument()
#        textDocument.setHtml(getPatientInfoAsHTMLEx3(record))
##        textDocument.setPageSize(QSizeF(210.0*2, 148.0*2))
##        textDocument.setPageSize(QSizeF(printer.width(), printer.height()))
##        body = QRectF(0, 0, p.device()->width(), p.device()->height());
#
##        textDocument.setDefaultFont(font)
#        textDocument.print_(printer)


#class CPatientDupsListDialog(CDialogBase, Ui_PatientDupsListDialog):
#    def __init__(self, parent, idList):
#        CDialogBase.__init__(self, parent)
#        self.setupUi(self)
#        self.model = CPatientsTableModel(self)
#        self.model.setIdList(idList)
#        self.tblPatients.setModel(self.model)
#        if len(idList) > 0:
#            self.tblPatients.selectRow(0)
#        self.__patientId = None
#
#    def patientId(self):
#        return self.__patientId
#
#    @pyqtSignature('QModelIndex')
#    def on_tblPatients_doubleClicked(self, index):
#        self.on_btnSelect_clicked()
#
#    @pyqtSignature('')
#    def on_btnOk_clicked(self):
#        self.reject()
#
#    @pyqtSignature('')
#    def on_btnIgnore_clicked(self):
#        self.accept()
#
#    @pyqtSignature('')
#    def on_btnSelect_clicked(self):
#        row = self.tblPatients.currentIndex().row()
#        if 0<=row and row<len(self.model.idList()):
#            self.__patientId = self.model.idList()[row]
#        self.accept()

#
###########################################################################
#

class CSocStatusTypeInDocTableCol(CRBInDocTableCol):
    def setEditorData(self, editor, value, record):
        socStatusClassId = forceRef(record.value('socStatusClass_id'))
        filter = ('class_id = %d' % socStatusClassId) if socStatusClassId else 'class_id is NULL'
        editor.setFilter(filter)
        editor.setValue(forceInt(value))


class CSocStatusesModel(CInDocTableModel):
    documentFields = 'documentType_id,serial,number,date,origin'

    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'ClientSocStatus', 'id', 'client_id', parent)
        self.addCol(CRBTreeInDocTableCol(u'Класс', 'socStatusClass_id', 50, 'rbSocStatusClass', showFields=CRBComboBox.showNameAndCode,  order='code'))
        #self.addCol(CRBInDocTableCol(u'Класс', 'socStatusClass_id', 50, 'rbSocStatusClass', showFields = CRBComboBox.showNameAndCode))#, filter='group_id is NULL'))
        self.addCol(CSocStatusTypeInDocTableCol(u'Тип',   'socStatusType_id', 50, 'vrbSocStatusType', showFields = CRBComboBox.showNameAndCode))
        self.addCol(CDateInDocTableCol(u'Дата начала',     'begDate', 15, canBeEmpty=True))
        self.addCol(CDateInDocTableCol(u'Дата окончания',  'endDate', 15, canBeEmpty=True))
        self.addCol(CInDocTableCol(u'Примечание', 'note', 20))
        self.addHiddenCol('document_id')


    def getEmptyRecord(self):
        result = CInDocTableModel.getEmptyRecord(self)
        self._addExCols(result)
        return result


    def loadItems(self, id):
        u'''
        Загрузка соц. статусов из БД. Помимо загрузки самих соц. статусов из ClientSocStatus ещё добавляются внешние
        (exCols) колонки и загружается информация, является ли соц. статус закреплённым
        :param id: id клиента, для которого загружаются соц. статусы
        :type id: int
        '''
        db = QtGui.qApp.db
        CInDocTableModel.loadItems(self, id)
        for item in self.items():
            self._addExCols(item)
            self._loadDocInfo(item)
        # В спиок соц. статусов надо добавить закреплённые соц. статусы, при этом не дублируя записи, если они были
        # загружены. Также для загруженных нужно проставить признак socStatusIsHolded если он есть в справочнике.
        mapRowsToSocStatusId = dict((forceRef(item.value('socStatusClass_id')), self.items().index(item)) for item in self.items())
        table = db.forceTable('rbSocStatusClass')
        socStatusIdList = db.getIdList(table, where=table['isHolded'].eq(1))
        for id in socStatusIdList:
            if id not in mapRowsToSocStatusId:
                record = self.getEmptyRecord()
                record.setValue('socStatusClass_id', id)
                record.setValue('socStatusIsHolded', 1)
                self.addRecord(record)
            else:
                item = self.items()[mapRowsToSocStatusId.get(id)]
                item.setValue('socStatusIsHolded', 1)


    def saveItems(self, clientId):
        documentIdList = []
        for item in self.items():
            documentId = self._saveDocInfo(item, clientId)
            if documentId:
                documentIdList.append(documentId)
        items = self.items()
        savedItems = []
        for record in items:
            savedItems.append(QtSql.QSqlRecord(record))
            for n in self.documentFields.split(','):
                record.remove(record.indexOf(n))
            record.remove(record.indexOf('socStatusIsHolded'))
        self._saveItemsInternal(clientId)
        self.deleteDispPlanExport(clientId)
        for record, savedRecord in zip(items, savedItems):
            for n in self.documentFields.split(','):
                record.append(savedRecord.field(n))
            record.append(savedRecord.field('socStatusIsHolded'))

    def _saveItemsInternal(self, masterId):
        '''
        Копия CInDocTableModel.saveItems с возможностью пропускать строки, которые не требуют сохранения
        :param masterId:
        :return:
        '''
        if self._items is not None:
            db = QtGui.qApp.db
            table = self._table
            masterId = toVariant(masterId)
            masterIdFieldName = self._masterIdFieldName
            idFieldName = self._idFieldName
            idList = []
            for idx, record in enumerate(self._items):
                # Если во время сохранения встречаем пустой тип соц. статуса - просто пропускаем такую запись
                socStatusTypeId = forceRef(record.value('socStatusType_id'))
                if socStatusTypeId is None:
                    continue
                record.setValue(masterIdFieldName, masterId)
                if self._idxFieldName:
                    record.setValue(self._idxFieldName, toVariant(idx))
                if self._extColsPresent:
                    outRecord = self.removeExtCols(record)
                else:
                    outRecord = record
                id = db.insertOrUpdate(table, outRecord)
                record.setValue(idFieldName, toVariant(id))
                idList.append(id)
                self.saveDependence(idx, id)

            filter = [table[masterIdFieldName].eq(masterId),
                      'NOT ('+table[idFieldName].inlist(idList)+')']
            if self._filter:
                filter.append(self._filter)
            db.deleteRecord(table, filter)

    def indexOfStatus(self, socStatusTypeId):
        for i, item in enumerate(self.items()):
            if forceRef(item.value('socStatusType_id')) == socStatusTypeId:
                return i
        return -1


    def establishStatus(self, socStatusTypeId):
        i = self.indexOfStatus(socStatusTypeId)
        if i>=0:
            item = self.items()[i]
            item.setValue('endDate', toVariant(None))
        else:
            item = self.getEmptyRecord()
            item.setValue('socStatusType_id', toVariant(socStatusTypeId))
            item.setValue('begDate', toVariant(QDate.currentDate()))
            item.setValue('endDate', toVariant(None))
            self.items().append(item)


    def declineUnlisted(self, socStatusTypeIdList):
        yesterday = QDate.currentDate().addDays(-1)
        for item in self.items():
            if forceRef(item.value('socStatusType_id')) not in socStatusTypeIdList:
                endDate = forceDate(item.value('endDate'))
                if not endDate or yesterday<endDate:
                    item.setValue('endDate', toVariant(yesterday))


# todo: clean unused docs
    def getDocInfo(self, row):
        record = self.items()[row]
        return [ forceRef(record.value('documentType_id')),
                 forceString(record.value('serial')),
                 forceString(record.value('number')),
                 forceDate(record.value('date')),
                 forceString(record.value('origin'))
               ]


    def _addExCols(self, record):
        record.append(QtSql.QSqlField('documentType_id', QVariant.Int))
        record.append(QtSql.QSqlField('serial', QVariant.String))
        record.append(QtSql.QSqlField('number', QVariant.String))
        record.append(QtSql.QSqlField('date', QVariant.Date))
        record.append(QtSql.QSqlField('origin', QVariant.String))
        record.append(QtSql.QSqlField('socStatusIsHolded', QVariant.Int))
        record.setValue('socStatusIsHolded', 0)


    def _loadDocInfo(self, record):
        db = QtGui.qApp.db
        documentId = forceRef(record.value('document_id'))
        if documentId:
            documentRecord = db.getRecord('ClientDocument', self.documentFields, documentId)
            if documentRecord:
                for n in self.documentFields.split(','):
                    record.setValue(n, documentRecord.value(n))


    def _saveDocInfo(self, record, clientId):
        documentId = None
        documentRecord = None
        db = QtGui.qApp.db
        table = db.table('ClientDocument')
        if forceRef(record.value('documentType_id')):
            documentId = forceRef(record.value('document_id'))
            if documentId:
                documentRecord = db.getRecord(table, '*', documentId)
            if documentRecord is None:
                documentRecord = table.newRecord()
            for n in self.documentFields.split(','):
                documentRecord.setValue(n, record.value(n))
            documentRecord.setValue('client_id', toVariant(clientId))
            documentId = db.insertOrUpdate(table, documentRecord)
            record.setValue('document_id', toVariant(documentId))
        elif forceRef(record.value('document_id')):
            documentRecord = db.deleteRecord(table, 'id = {}'.format(forceRef(record.value('document_id'))))
            record.setValue('document_id', toVariant(documentId))
        return documentId
    
    def deleteDispPlanExport(self, clientId):
        db = QtGui.qApp.db
        tablePlanExport = db.table('disp_PlanExport')
        tablePlanExportErrors = db.table('disp_PlanExportErrors')
        tableCSS = db.table('ClientSocStatus')
        query = tablePlanExport.innerJoin(tableCSS, tableCSS['id'].eq(tablePlanExport['row_id']))
        where = [
            tablePlanExport['exportKind'].eq('ClientSocStatus'),
            tablePlanExport['client_id'].eq(clientId),
            tableCSS['deleted'].eq(1),
        ]
        planExportIdList = db.getDistinctIdList(query, idCol=tablePlanExport['id'], where=where)
        if planExportIdList:
            db.deleteRecord(tablePlanExportErrors, tablePlanExportErrors['planExport_id'].inlist(planExportIdList))
            db.deleteRecord(tablePlanExport, tablePlanExport['id'].inlist(planExportIdList))

class CPolyclinicInDocTableCol(CInDocTableCol):
    def __init__(self, title, fieldName, width):
        CInDocTableCol.__init__(self, title, fieldName, width)
        self.__model = None

    def initModel(self):
        self.__model = CDbModel(None)
        self.__model.setNameField(CPolyclinicComboBox.nameField)
        self.__model.setAddNone(True)
        self.__model.setFilter(CPolyclinicComboBox.filter)
        self.__model.setTable('Organisation')


    def toString(self, val, record):
        if not self.__model:
            self.initModel()
        text = self.__model.getNameById(forceRef(val))
        return toVariant(text)


    def createEditor(self, parent):
        if not self.__model:
            self.initModel()
        #editor = CDbComboBox(parent)
        #editor.setModel(self.__model)
        editor = CDbSearchWidget(parent)
        editor.setModel(self.__model)
        return editor


    def setEditorData(self, editor, value, record):
        editor.setValue(forceRef(value))


    def getEditorData(self, editor):
        return toVariant(editor.value())


class CSocStatusesModelSort(CSortFilterProxyTableModel):

    def rowCount(self, parent=QModelIndex()):
        if parent is None:
            parent = QModelIndex()
        return super(CSocStatusesModelSort, self).rowCount(parent)

    def filterAcceptsRow(self, sourceRow, sourceParent):
        if sourceRow >= len(self.sourceModel().items()):
            return True
        return super(CSocStatusesModelSort, self).filterAcceptsRow(sourceRow, sourceParent)

    def __getattr__(self, name):
        return getattr(self.sourceModel(), name)


class CSortFilterProxyLocItemDelegate(CLocItemDelegate):
    def setEditorData(self, editor, index):
        if editor is not None:
            model  = index.model()
            index = model.mapToSource(index)
            column = index.column()
            row = index.row()
            if row < len(model.items()):
                record = model.items()[row]
            else:
                record = model.getEmptyRecord()

            model.setEditorData(column, editor, model.sourceModel().data(index, Qt.EditRole), record)


class COrgStructureInDocTableColEx(COrgStructureInDocTableCol):
    def setEditorData(self, editor, value, record):
        editor.setOrgId(forceRef(record.value('LPU_id')))
        db = QtGui.qApp.db
        table = db.table('rbAttachType')
        if db.getRecordEx(table, 'id', db.joinAnd([table['id'].eq(forceRef(record.value('attachType_id'))),
                                                   table['code'].inlist(['1', '2']),
                                                   table['temporary'].eq(0),
                                                   table['outcome'].eq(0),
                                                   table['finance_id'].eq(2)])):
            editor.setPurpose(COrgStructureTreePurpose.areaSelector)
        editor.setValue(forceInt(value))


class CClientRelationInDocTableCol(CInDocTableCol):
    def __init__(self, title, fieldName, width, tableName, **params):
        CInDocTableCol.__init__(self, title, fieldName, width, **params)
        self.tableName  = tableName
        self.filter     = params.get('filter', '')
        self.preferredWidth = params.get('preferredWidth', None)
        self.clientId = None
        self.regAddressInfo = None
        self.logAddressInfo = None
        self.defaultAddressInfo = None


    def toString(self, val, record):
        return toVariant(clientIdToText(val))


    def createEditor(self, parent):
        editor = CClientRelationComboBox(parent, self.clientId, self.regAddressInfo, self.logAddressInfo, self.defaultAddressInfo)
        return editor


    def setEditorData(self, editor, value, record):
        editor.setValue(forceInt(value))


    def getEditorData(self, editor):
        return toVariant(editor.value())


    def setClientId(self, clientId):
        self.clientId = clientId


    def setRegAddressInfo(self, regAddressInfo):
        self.regAddressInfo = regAddressInfo


    def setLogAddressInfo(self, logAddressInfo):
        self.logAddressInfo = logAddressInfo


    def setDefaultAddressInfo(self, defaultAddressInfo):
        self.defaultAddressInfo = defaultAddressInfo


class CMonitoringModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Client_Monitoring', 'id', 'client_id', parent)
        self.addCol(CActionPropertyTemplateCol(u'Свойство',  'propertyTemplate_id', 40))


class CClientEpidCaseModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Client_EpidCase', 'id', 'master_id', parent)
        self.addCol(CInDocTableCol( u'Эпид.номер', 'number', 15))
        self.addCol(CDateInDocTableCol( u'Дата регистрации эпид.номера', 'regDate', 30, canBeEmpty=False))
        self.addCol(CRBInDocTableCol(u'Лицо, зарегистровавшее эпид.номер', 'regPerson_id', 30, 'vrbPerson'))
        self.addCol(CICDInDocTableCol(u'МКБ', 'MKB', 10))
        self.addCol(CDateInDocTableCol( u'Дата завершения эпид. расследования', 'endDate', 30, canBeEmpty=True))
        self.addCol(CInDocTableCol( u'Примечание', 'note', 15))
        self.clientEditDialog = parent


class CAttachesModel(CInDocTableModel):
    class CRBDeAttachTypeInDocTableCol(CRBInDocTableCol):
        def setEditorData(self, editor, value, record):
            actualDate = forceDate(record.value('endDate'))
            if not actualDate or not actualDate.isValid():
                actualDate = QDate().currentDate()
            db = QtGui.qApp.db
            rbDeAttachTypeTable = db.table('rbDeAttachType')
            cond = db.joinAnd([db.joinOr([rbDeAttachTypeTable['endDate'].ge(actualDate),
                                          rbDeAttachTypeTable['endDate'].isNull()]),
                               rbDeAttachTypeTable['begDate'].le(actualDate)])
            editor.setFilter(cond)
            editor.setValue(forceInt(value))


    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'ClientAttach', 'id', 'client_id', parent)
        rightOwnAreaOnly = parent.getRightOwnAreaOnly()
        self.parent = parent
        self.hasEditRight = (QtGui.qApp.userHasRight(urRegEditClientAttachEndDateOwnAreaOnly) and rightOwnAreaOnly)
        self.hasEmptyEditRight = QtGui.qApp.userHasRight(urRegCreateClientAttachOwnAreaOnly) and rightOwnAreaOnly
        self.addCol(CRBInDocTableCol(            u'Тип',               'attachType_id',    30, 'rbAttachType'))
        self.addCol(COrgInDocTableColEx(u'ЛПУ', 'LPU_id', 15))
        self.addCol(COrgStructureInDocTableColEx(u'Подразделение',     'orgStructure_id',  15))
        self.addCol(CDateInDocTableCol(          u'Дата прикрепления', 'begDate',          15, canBeEmpty=True))
        self.addCol(CDateInDocTableCol(          u'Дата открепления',  'endDate',          15, canBeEmpty=True))
        self.addCol(CEnumInDocTableCol(          u'По заявлению',      'isStatement',      15, [u'нет', u'да']))
        self.addCol(CAttachesModel.CRBDeAttachTypeInDocTableCol(u'Причина открепления', 'deAttachType_id', 30, 'rbDeAttachType'))
        self.addCol(CInDocTableCol(u'Примечание', 'notes', 30))
        self.addHiddenCol('syncDate')
        self.clientEditDialog = parent


    def getEmptyRecord(self):
        orgId = QtGui.qApp.currentOrgId()
        address = self.clientEditDialog.getAddress(1)
        houseId = findHouseId(address)
        if houseId:
            clientSex = self.clientEditDialog.cmbSex.currentIndex()
            clientAge = calcAgeTuple(self.clientEditDialog.clientBirthDate, QDate.currentDate())
            orgStructureIdList = findOrgStructuresByHouseAndFlat(houseId, address['flat'], orgId, QtGui.qApp.currentOrgStructureId(), clientSex, clientAge)
            orgStructureId = orgStructureIdList[0] if orgStructureIdList else None
        else:
            orgStructureId = None
        result = CInDocTableModel.getEmptyRecord(self)
        result.setValue('LPU_id',          toVariant(orgId))
        result.setValue('orgStructure_id', toVariant(orgStructureId))
        result.setValue('begDate',         toVariant(QDate.currentDate()))
        return result

    def setData(self, index, value, role=Qt.EditRole):
        result = None
        allAttachClosed = True
        for item in self._items:
            db = QtGui.qApp.db
            if forceBool(item.value('id')):
                recordAttach = db.getRecord('ClientAttach', 'endDate', forceInt(item.value('id')))
                if not forceBool(forceString(recordAttach.value('endDate'))):
                    allAttachClosed = False
                    break
        if QtGui.qApp.userHasRight(urEnableClientAttach):
            result = CInDocTableModel.setData(self, index, value, role)
        elif (len(self._items) == 0 or allAttachClosed) and self.hasEmptyEditRight:
            isAttachClose = False
            if 0 <= index.row() < len(self._items) and forceInt(self._items[index.row()].value('id')):
                row = self._items[index.row()]
                recordAttach = db.getRecord('ClientAttach', 'endDate', forceInt(row.value('id')))
                isAttachClose = forceBool(forceString(recordAttach.value('endDate')))
            if index.column() in [0, 1, 2, 3, 7] and not isAttachClose:
                if index.column() == 2:
                    row = self._items[index.row()]
                    selectedOrgStructre = forceInt(value)

                    db = QtGui.qApp.db
                    personId = QtGui.qApp.userId
                    records = db.getRecordList('Person_Order', 'orgStructure_id',
                                               'deleted = 0 AND master_id = {0} AND type = 6 AND validToDate IS NULL'.format(personId))
                    personOrgStructureList = []
                    for record in records:
                        if record:
                            orgStructureDescendants = getOrgStructureDescendants(forceInt(record.value('orgStructure_id')))
                            personOrgStructureList += orgStructureDescendants
                    personOrgStructureSet = set(personOrgStructureList)
                    if selectedOrgStructre in personOrgStructureSet:
                        result = CInDocTableModel.setData(self, index, value, role)
                    else:
                        QtGui.QMessageBox.information(self.parent,
                                                      u'Внимание!',
                                                      u'Вы можете выбрать только свое подразделение!',
                                                      QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
                else:
                    result = CInDocTableModel.setData(self, index, value, role)
            else:
                QtGui.QMessageBox.information(self.parent,
                                              u'Внимание!',
                                              u'Недостаточно прав для ввода данных!',
                                              QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
        elif self.hasEditRight:
            db = QtGui.qApp.db
            personId = QtGui.qApp.userId
            records = db.getRecordList('Person_Order', 'orgStructure_id',
                                       'deleted = 0 AND master_id = {0} AND type = 6 AND validToDate IS NULL'.format(
                                           personId))
            personOrgStructureList = []
            for record in records:
                if record:
                    orgStructureDescendants = getOrgStructureDescendants(forceInt(record.value('orgStructure_id')))
                    personOrgStructureList += orgStructureDescendants
            personOrgStructureSet = set(personOrgStructureList)

            if 0 <= index.row() < len(self._items):
                row = self._items[index.row()]
                recordAttach = db.getRecord('ClientAttach', 'endDate', forceInt(row.value('id')))
                isAttachClose = forceBool(forceString(recordAttach.value('endDate')))
                rec = self._items[index.row()]
                orgStructureId = forceInt(rec.value('orgStructure_id'))
                if index.column() in [4, 6, 7] and not isAttachClose and orgStructureId in personOrgStructureSet:
                    result = CInDocTableModel.setData(self, index, value, role)
                # elif index.column() not in [4, 6, 7]:
                #     result = CInDocTableModel.setData(self, index, value, role)
                else:
                    QtGui.QMessageBox.information(self.parent,
                                                  u'Внимание!',
                                                  u'Недостаточно прав для ввода данных!',
                                                  QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
            else:
                QtGui.QMessageBox.information(self.parent,
                                              u'Внимание!',
                                              u'Недостаточно прав для ввода данных!',
                                              QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
        else:
            QtGui.QMessageBox.information(self.parent,
                                        u'Внимание!',
                                        u'Недостаточно прав для ввода данных!',
                                        QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
        if result and index.column() == 0 and role == Qt.EditRole:
            db = QtGui.qApp.db
            outcome = forceInt(db.translate('rbAttachType', 'id', value, 'outcome'))
            if outcome and 0 <= index.row() < len(self._items):
                record = self._items[index.row()]
                record.setValue('endDate', record.value('begDate'))


class CDirectRelationsModel(CInDocTableModel):
    def __init__(self, parent):
        db = QtGui.qApp.db
        CInDocTableModel.__init__(self, 'ClientRelation', 'id', 'client_id', parent)
        self.addCol(CRBInDocTableCol(u'Прямая связь', 'relativeType_id', 30, 'vrbDirectClientRelation'))
        self.addCol(CClientRelationInDocTableCol(u'Связан с пациентом', 'relative_id', 30, 'ClientRelation'))
        self.clientEditDialog = parent
        self.clientId = None
        self.sex = None

    def setClientId(self, clientId):
        self.clientId = clientId
        self.cols()[1].setClientId(clientId)

    def setRegAddressInfo(self, regAddressInfo):
        self.cols()[1].setRegAddressInfo(regAddressInfo)

    def setLogAddressInfo(self, logAddressInfo):
        self.cols()[1].setLogAddressInfo(logAddressInfo)

    def setDefaultAddressInfo(self, defaultAddressInfo):
        self.cols()[1].setDefaultAddressInfo(defaultAddressInfo)


    def setDirectRelationFilter(self, sex):
        if sex:
            self.cols()[0].filter = 'id IN (SELECT rbRelationType.id FROM rbRelationType WHERE rbRelationType.leftSex = %d OR rbRelationType.leftSex = 0)'%(sex)
        else:
            self.cols()[0].filter = ''

    
    def setData(self, index, value, role=Qt.EditRole):
        if index.column() == 0:
            self.sex = forceInt(QtGui.qApp.db.translate('rbRelationType', 'id', forceInt(value), 'rightSex'))
        return CInDocTableModel.setData(self, index, value, role)

    def setEditorData(self, column, editor, value, record):
        self._cols[column].setEditorData(editor, value, record)
        if column == 1:
            editor.showPopup(self)


class CBackwardRelationsModel(CInDocTableModel):
    def __init__(self, parent):
        db = QtGui.qApp.db
        CInDocTableModel.__init__(self, 'ClientRelation', 'id', 'relative_id', parent)
        self.addCol(CRBInDocTableCol(u'Обратная связь', 'relativeType_id', 30, 'vrbBackwardClientRelation'))
        self.addCol(CClientRelationInDocTableCol(u'Связан с пациентом', 'client_id', 30, 'ClientRelation'))
        self.addCol(CAPLikeOrgInDocTableCol(u'Организация', 'org_id', 30))
        self.clientEditDialog = parent
        self.clientId = None
        self.allowOrgRelationTypeIds = set(db.getIdList('rbRelationType', where="regionalCode in ('4', '5')"))
        self.sex = None

    def setClientId(self, clientId):
        self.clientId = clientId
        self.cols()[1].setClientId(clientId)

    def setRegAddressInfo(self, regAddressInfo):
        self.cols()[1].setRegAddressInfo(regAddressInfo)

    def setLogAddressInfo(self, logAddressInfo):
        self.cols()[1].setLogAddressInfo(logAddressInfo)

    def setDefaultAddressInfo(self, defaultAddressInfo):
        self.cols()[1].setDefaultAddressInfo(defaultAddressInfo)


    def setBackwardRelationFilter(self, sex):
        if sex:
            self.cols()[0].filter = 'id IN (SELECT rbRelationType.id FROM rbRelationType WHERE rbRelationType.rightSex = %d OR rbRelationType.rightSex = 0)'%(sex)
        else:
            self.cols()[0].filter = ''
    
    def setData(self, index, value, role=Qt.EditRole):
        row = index.row()
        column = index.column()
        if column == self.getColIndex('relativeType_id'):
                self.sex = forceInt(QtGui.qApp.db.translate('rbRelationType', 'id', forceInt(value), 'leftSex'))
        if row < len(self._items):
            db = QtGui.qApp.db
            record = self._items[row]
            if column == self.getColIndex('relativeType_id'):
                relationTypeId = forceRef(value)
                if relationTypeId not in self.allowOrgRelationTypeIds:
                    record.setValue('org_id', QVariant())
                    self.emitCellChanged(row, self.getColIndex('org_id'))
            elif column == self.getColIndex('org_id'):
                orgId = forceRef(value)
                if orgId:
                    record.setValue('client_id', QVariant())
                    self.emitCellChanged(row, self.getColIndex('client_id'))
            elif column == self.getColIndex('client_id'):
                clientId = forceRef(value)
                if clientId:
                    record.setValue('org_id', QVariant())
                    self.emitCellChanged(row, self.getColIndex('client_id'))
        return CInDocTableModel.setData(self, index, value, role)

    def setEditorData(self, column, editor, value, record):
        self._cols[column].setEditorData(editor, value, record)
        if column == 1:
            editor.showPopup(self)


    def cellReadOnly(self, index):
        column = index.column()
        row = index.row()
        if column == self.getColIndex('org_id'):
            if row == len(self._items):
                return True
            record = self._items[row]
            relationTypeId = forceRef(record.value('relativeType_id'))
            if relationTypeId not in self.allowOrgRelationTypeIds:
                return True
        return False


def valIsMatched(old, new):
    return old == new or not old or not new


def valIsStrictlyEqual(old, new):
    return old == new


class CRegExpedInDocTableCol(CInDocTableCol):
    def __init__(self, title, fieldName, width, **params):
        CInDocTableCol.__init__(self, title, fieldName, width, **params)
        self.regExp = None


    def createEditor(self, parent):
        editor = CLineEditWithRegExpValidator(parent)
        return editor



class CDocSerialInDocTableCol(CRegExpedInDocTableCol):
    def setEditorData(self, editor, value, record):
        documentTypeId = record.value('documentType_id')
        if documentTypeId:
            documentTypeDescr = getDocumentTypeDescr(documentTypeId)
            if documentTypeDescr.hasRightPart:
                regExp = ( documentTypeDescr.leftPartRegExp
                           + documentTypeDescr.partSeparator
                           + documentTypeDescr.rightPartRegExp )
            else:
                regExp = documentTypeDescr.leftPartRegExp
        else:
            regExp = ''

        editor.setRegExp(regExp)
        editor.setText(forceStringEx(value))


class CDocNumberInDocTableCol(CRegExpedInDocTableCol):
    def setEditorData(self, editor, value, record):
        documentTypeId = record.value('documentType_id')
        if documentTypeId:
            documentTypeDescr = getDocumentTypeDescr(documentTypeId)
            regExp = documentTypeDescr.numberRegExp
        else:
            regExp = ''
        editor.setRegExp(regExp)
        editor.setText(forceStringEx(value))


class CIdentificationDocsModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'ClientDocument', 'id', 'client_id', parent)
        self.setFilter('documentType_id IN (SELECT rbDocumentType.id FROM rbDocumentType LEFT JOIN rbDocumentTypeGroup ON rbDocumentTypeGroup.id = rbDocumentType.group_id WHERE rbDocumentTypeGroup.code=\'1\')')
        self.addCol(CDateTimeInDocTableCol(u'Дата', u'createDatetime', 8, canBeEmpty=True)).setReadOnly(True)
        self.addCol(CRBInDocTableCol(u'Пользователь', u'createPerson_id', 15, u'vrbPerson')).setReadOnly(True)
        self.addCol(CRBInDocTableCol(u'Тип', 'documentType_id', 30, 'rbDocumentType', filter='group_id IN (SELECT id FROM rbDocumentTypeGroup WHERE code=\'1\')')).setReadOnly(True)
        self.addCol(CDocSerialInDocTableCol(u'Серия', 'serial', 8)).setReadOnly(True)
        self.addCol(CDocNumberInDocTableCol(u'Номер', 'number', 16)).setReadOnly(True)
        self.addCol(CDateInDocTableCol(u'Дата', 'date', 15, canBeEmpty=True)).setReadOnly(True)
        self.addCol(CInDocTableCol(u'Выдан', 'origin', 30)).setReadOnly(True)
        self.addCol(CInDocTableCol(u'Код', 'originCode', 30)).setReadOnly(True)


    # def setData(self, index, value, role=Qt.EditRole):
    #     CInDocTableModel.setData(self, index, value, role)


    def getCurrentDocRow(self, docTypeId, serial, number):
        items = self.items()
        if items:
            row = len(items)-1
            item = items[row]
            if ( item.isNull('id')
                 or ( valIsMatched(forceRef(item.value('documentType_id')), docTypeId)
                      and valIsMatched(forceStringEx(item.value('serial')), serial)
                      and valIsMatched(forceStringEx(item.value('number')), number)
                    )
               ):
                return row
        row = len(items)
        self.insertRecord(row, self.getEmptyRecord())
        return row
        
        
    def cleanUpEmptyItems(self):
        items = self.items()
        for i in reversed(xrange(len(items))):
            item = items[i]
            documentTypeId = forceRef(item.value('documentType_id'))
            serial = forceStringEx(item.value('serial'))
            number = forceStringEx(item.value('number'))
            if not (documentTypeId or number or serial):
                self.removeRows(i, 1)


class CPoliciesModel(CInDocTableModel):
    __pyqtSignals__ = ('policyChanged()',
                      )
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'ClientPolicy', 'id', 'client_id', parent)
        self.policyTypeColumn = CRBInDocTableCol(u'Тип', 'policyType_id', 30, 'rbPolicyType')
        self.policyKindColumn = CRBInDocTableCol(u'Вид', 'policyKind_id', 30, 'rbPolicyKind')
        self.addCol(CDateTimeInDocTableCol(u'Дата', u'createDatetime', 8, canBeEmpty=True)).setReadOnly(True)
        self.addCol(CRBInDocTableCol(u'Пользователь', u'createPerson_id', 15, u'vrbPerson')).setReadOnly(True)
        self.addCol(self.policyTypeColumn).setReadOnly(True)
        self.addCol(self.policyKindColumn).setReadOnly(True)
        self.addCol(CInDocTableCol(u'Серия', 'serial', 30)).setReadOnly(True)
        self.addCol(CInDocTableCol(u'Номер', 'number', 30)).setReadOnly(True)
        self.addCol(CDateInDocTableCol(u'Дата начала',    'begDate', 15, canBeEmpty=True))
        self.addCol(CDateInDocTableCol(u'Дата окончания', 'endDate', 15, canBeEmpty=True))
        self.addCol(CInsurerInDocTableCol(u'СМО', 'insurer_id', 50)).setReadOnly(True)
        self.addExtCol(CInsurerAreaInDocTableCol(u'Территория страхования', 'insurer_id', 50), QVariant.Int)
        self.addCol(CInDocTableCol(u'Наименование', 'name', 50)).setReadOnly(True)
        self.addCol(CInDocTableCol(u'Примечание',   'note', 50)).setReadOnly(True)
        self.addCol(CDateInDocTableCol(u'Дата проверки страховой принадлежности', 'checkDate', 15, canBeEmpty=True)).setReadOnly(True)


    def cellReadOnly(self, index):
        if index and index.isValid():
            column = index.column()
            col = self._cols[column]
            if QtGui.qApp.userHasRight(urRegEditClientHistory) and (col.fieldName() == 'begDate' or col.fieldName() == 'endDate'):
                return False
        return True


    def setData(self, index, value, role=Qt.EditRole):
        result = CInDocTableModel.setData(self, index, value, role)
        if result and role == Qt.EditRole:
            self.emit(SIGNAL('policyChanged()'))
            row = index.row()


    def removeRows(self, row, count, parentIndex=QModelIndex()):
        res = CRecordListModel.removeRows(self, row, count, parentIndex)
        if res:
            self.emit(SIGNAL('policyChanged()'))
        return res


    def getCurrentPolicyRowInt(self, isCompulsory, serial='', number='', insurerId=None, begDate=None):
        items = self.items()
        for row in reversed(xrange(len(items))):
            item = items[row]
            policyTypeId = forceRef(item.value('policyType_id'))
            if (policyTypeId is None and isCompulsory) or self.policyTypeIsCompulsory(policyTypeId, isCompulsory):
                if begDate:
                    if (valIsMatched(forceDate(item.value('begDate')), begDate)):
                        return row
                    elif isCompulsory:
                        return -1
                else:
                    if (item.isNull('id')
                            or (valIsMatched(forceStringEx(item.value('serial')), serial)
                                and valIsMatched(forceStringEx(item.value('number')), number))
                    ):
                        return row
                    elif isCompulsory:
                        return -1
        return -1

    def getCurrentPolicyRow(self, isCompulsory, serial, number, insurerId=None, begDate=None):
        row = self.getCurrentPolicyRowInt(isCompulsory, serial, number, insurerId, begDate)
        if row < 0:
            row = len(self.items())
#            self.insertRecord(row, self.getEmptyRecord())
            item = self.getEmptyRecord()
            self.insertRecord(row, item)
            item.setValue('policyType_id', toVariant(self.getFirstPolicyTypeId(isCompulsory)))
        return row


    def getCurrentCompulsoryPolicyRow(self, serial, number, insurerId=None, begDate=None):
        return self.getCurrentPolicyRow(True, serial, number, insurerId, begDate)


    def getCurrentVoluntaryPolicyRow(self, serial, number, insurerId=None, begDate=None):
        return self.getCurrentPolicyRow(False, serial, number, insurerId, begDate)


    def policyTypeIsCompulsory(self, policyTypeId, isCompulsory):
        if policyTypeId:
            cache = CRBModelDataCache.getData(self.policyTypeColumn.tableName, True)
            return self.policyTypeNameIsCompulsory(cache.getNameById(policyTypeId)) == isCompulsory
        return False


    def getFirstPolicyTypeId(self, isCompulsory):
        cache = CRBModelDataCache.getData(self.policyTypeColumn.tableName, True)
        for i in xrange(cache.getCount()):
            id = cache.getId(i)
            if id and self.policyTypeNameIsCompulsory(cache.getName(i)) == isCompulsory:
                return id
        return None


    def policyTypeNameIsCompulsory(self, name):
        return unicode(name)[:3].upper() == u'ОМС'


    def cleanUpEmptyItems(self):
        items = self.items()
        for i in reversed(xrange(len(items))):
            item = items[i]
            id = forceRef(item.value('id'))
            # serial = forceStringEx(item.value('serial'))
            number = forceStringEx(item.value('number'))
            insurerId = forceRef(item.value('insurer_id'))
            name = forceStringEx(item.value('name'))
            if not (id or number or insurerId or name):
                self.removeRows(i, 1)


    def loadItems(self, masterId):
        db = QtGui.qApp.db
        table = self._table
        tableRBPolicyType = db.table('rbPolicyType')
        cols = [table['createDatetime'],
                table['createPerson_id'],
                table['policyType_id'],
                table['policyKind_id'],
                table['serial'],
                table['number'],
                table['begDate'],
                table['endDate'],
                table['insurer_id'],
                table['name'],
                table['note'],
                table['id'],
                table['client_id'],
                table['checkDate'],
                ]
        for col in self._hiddenCols:
            cols.append(col)
        filter = [table[self._masterIdFieldName].eq(masterId)]
        if self._filter:
            filter.append(self._filter)
        if table.hasField('deleted'):
            filter.append(table['deleted'].eq(0))
        qeryTable = table.leftJoin(tableRBPolicyType, tableRBPolicyType['id'].eq(table['policyType_id']))
        order = [u'ClientPolicy.begDate', u'rbPolicyType.isCompulsory']
        self._items = db.getRecordList(qeryTable, cols, filter, order)
        if self._extColsPresent:
            extSqlFields = []
            for col in self._cols:
                if col.external():
                    fieldName = col.fieldName()
                    if fieldName not in cols:
                        extSqlFields.append(QtSql.QSqlField(fieldName, col.valueType()))
            if extSqlFields:
                for item in self._items:
                    for field in extSqlFields:
                        item.append(field)
        self.reset()


class CPersonalInfoModel(CInDocTableModel):

    class CSnilsInDocTableCol(CInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)

        def toString(self, val, record):
            return formatSNILS(forceString(val))


    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Client_History', 'id', 'master_id', parent)
        self.addCol(CDateTimeInDocTableCol(u'Дата', u'createDatetime', 8, canBeEmpty=True)).setReadOnly(True)
        self.addCol(CRBInDocTableCol(u'Пользователь', u'createPerson_id', 15, u'vrbPerson')).setReadOnly(True)
        self.addCol(CInDocTableCol(u'Фамилия', 'lastName', 8))
        self.addCol(CInDocTableCol(u'Имя', 'firstName', 8))
        self.addCol(CInDocTableCol(u'Отчество', 'patrName', 16))
        self.addCol(CDateInDocTableCol(u'Дата рождения', 'birthDate', 15, canBeEmpty=True))
        self.addCol(CEnumInDocTableCol(u'Пол', 'sex', 3, (u'', u'М', u'Ж')))
        self.addCol(CPersonalInfoModel.CSnilsInDocTableCol(u'СНИЛС', 'SNILS', 14)).setReadOnly(True)
        self.addCol(CDateTimeInDocTableCol(u'Дата смерти', 'deathDate', 15, canBeEmpty=True))
        self.addCol(CRBInDocTableCol(u'Причина смерти', u'deathReason_id', 15, u'rbDeathReason', canBeEmpty=True)).setReadOnly(True)
        self.addCol(CRBInDocTableCol(u'Место смерти', u'deathPlaceType_id', 15, u'rbDeathPlaceType', canBeEmpty=True)).setReadOnly(True)
        self.addHiddenCol('birthTime')


    def getCurrentInfoRow(self, lastName, firstName, patrName, birthDate, birthTime, sex, deathDate, deathReasonId, deathPlaceTypeId, snils):
        items = self.items()
        if items:
            row = len(items)-1
            item = items[row]
            if ( item.isNull('id')
                    or (valIsStrictlyEqual(forceStringEx(item.value('lastName')), lastName)
                        and valIsStrictlyEqual(forceStringEx(item.value('firstName')), firstName)
                        and valIsStrictlyEqual(forceStringEx(item.value('patrName')), patrName)
                        and valIsStrictlyEqual(forceDate(item.value('birthDate')), birthDate)
                        and valIsStrictlyEqual(forceTime(item.value('birthTime')), birthTime)
                        and valIsStrictlyEqual(forceInt(item.value('sex')), sex)
                        and valIsStrictlyEqual(forceStringEx(item.value('SNILS')), snils)
                        and valIsStrictlyEqual(forceDateTime(item.value('deathDate')), deathDate)
                        and valIsStrictlyEqual(forceRef(item.value('deathReason_id')), deathReasonId)
                        and valIsStrictlyEqual(forceRef(item.value('deathPlaceType_id')), deathPlaceTypeId)
                    )
                ):
                return row
        row = len(items)
        self.insertRecord(row, self.getEmptyRecord())
        return row


class CStatusObservationModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Client_StatusObservation', 'id', 'master_id', parent)
        self.addCol(CDateTimeInDocTableCol(u'Дата', u'createDatetime', 8, canBeEmpty=True)).setReadOnly(True)
        self.addCol(CRBInDocTableCol(u'Пользователь', u'createPerson_id', 15, u'vrbPersonWithSpeciality')).setReadOnly(True)
        self.addCol(CRBInDocTableCol(u'Статус наблюдения', 'statusObservationType_id', 30, 'rbStatusObservationClientType', showFields=CRBComboBox.showCodeAndName)).setReadOnly(True)


class CContactInDocTableCol(CInDocTableCol):
    def __init__(self, title, fieldName, width, **params):
        CInDocTableCol.__init__(self, title, fieldName, width, **params)
        self.recordContactTypeCache = params.get('contactTypeCaches', [])
        db = QtGui.qApp.db
        table = db.table('rbContactType')
        self._phoneNumberIdList = db.getDistinctIdList('rbContactType', 'id', [table['code'].inlist([1, 2, 3, 'max'])])
#        self._emailIdList = db.getDistinctIdList('rbContactType', 'id', [table['code'].inlist([4])])


    def setEditorData(self, editor, value, record):
        editor.setText(forceStringEx(value))
        contactTypeId = forceRef(record.value('contactType_id'))
        if contactTypeId and self.recordContactTypeCache:
            contactTypeRecord = self.recordContactTypeCache.get(contactTypeId) if contactTypeId else None
            if contactTypeRecord:
                regExpValidator = forceString(contactTypeRecord.value('regExpValidator'))
                if regExpValidator:
                    if contactTypeId in self._phoneNumberIdList:
                        editor.setInputMask(regExpValidator)
                    else:
                        editor.setValidator((QtGui.QRegExpValidator(QRegExp(regExpValidator), None)))


class CClientContactsModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'ClientContact', 'id', 'client_id', parent)
        db = QtGui.qApp.db
        contactTypeCaches = CTableRecordCache(db, db.forceTable('rbContactType'), u'*', capacity=None)
        self.addCol(CRBInDocTableCol(u'Тип', 'contactType_id', 30, 'rbContactType', addNone=False))
        self.addCol(CContactInDocTableCol(u'Номер', 'contact', 30, contactTypeCaches=contactTypeCaches))
        self.addCol(CInDocTableCol(u'Примечание', 'notes', 30))


    def setDialogContact(self, typeContactId, contact):
        if typeContactId:
            row = len(self.items())
            item = CInDocTableModel.getEmptyRecord(self)
            self.insertRecord(row, item)
            item.setValue('contactType_id', toVariant(typeContactId))
            item.setValue('contact', toVariant(contact))


class CAllergyModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'ClientAllergy', 'id', 'client_id', parent)
        self.addCol(CInDocTableCol(u'Наименование вещества', 'nameSubstance', 50))
        self.addCol(CRBInDocTableCol(u'Тип реакции', 'reactionType_id', 30, 'rbReactionType'))
        self.addCol(CRBInDocTableCol(u'Проявление реакции', 'reactionManifestation_id', 30, 'rbReactionManifestation'))
        self.addCol(CEnumInDocTableCol(u'Степень', 'power', 15, [u'0 - не известно', u'1 - малая', u'2 - средняя', u'3 - высокая', u'4 - строгая']))
        self.addCol(CDateInDocTableCol(u'Дата установления', 'createDate', 15, canBeEmpty=True))
        self.addCol(CInDocTableCol(u'Примечание', 'notes', 30))


class CRiskFactorsModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'ClientRiskFactor', 'id', 'client_id', parent)
        self.addCol(CRBInDocTableCol(u'Наименование', 'riskFactor_id', 50, 'rbRiskFactor'))
        self.addCol(CDateInDocTableCol(u'Дата начала', 'begDate', 15))
        self.addCol(CDateInDocTableCol(u'Дата окончания', 'endDate', 15, canBeEmpty=True))
        self.addCol(CInDocTableCol(u'Степень', 'power', 20))
        self.addCol(CICDExInDocTableCol(u'МКБ', 'MKB', 10))
        self.addCol(CInDocTableCol(u'Примечание', 'notes', 30))


class CDepositModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'ClientDeposit', 'id', 'client_id', parent)
        self.addCol(CDateInDocTableCol(u'Дата', 'contractDate', 15, canBeEmpty=True))
        self.addCol(CDepositModel.CContractInDocTableCol(self))
        self.addCol(CFloatInDocTableCol(u'Сумма депозита', 'contractSum', 8, precision=4))
        self.addExtCol(CFloatInDocTableCol( u'Сумма фактическая',   'factSum', 10), QVariant.Int).setReadOnly(True)
        self.columnFactSum = self.getColIndex('factSum')
        self.factSum = []


    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        if role == Qt.DisplayRole:
            if column == self.columnFactSum:
                row = index.row()
                if 0 <= row < len(self.items()) and len(self.factSum) <= len(self.items()):
                    return QVariant(self.factSum[row]) if len(self.factSum) > row else None
        return CInDocTableModel.data(self, index, role)


    class CContractInDocTableCol(CInDocTableCol):

        def __init__(self, model):
            CInDocTableCol.__init__(self, u'Договор', 'contract_id', 20)
            self.model = model


        def toString(self, val, record):
            contractId = forceRef(val)
            if contractId:
                names = ['number', 'date', 'resolution']
                record = QtGui.qApp.db.getRecord('Contract', names, contractId)
                str = ' '.join([forceString(record.value(name)) for name in names])
            else:
                str = u'не задано'
            return QVariant(str)


        def createEditor(self, parent):
            filter = {}
            editor = CContractTreeFindComboBox(parent, filter)
            return editor


        def getEditorData(self, editor):
            return QVariant(editor.value())


        def setEditorData(self, editor, value, record):
            date = forceDate(record.value('contractDate'))
            editor.setDate(date)


class CIntoleranceMedicamentModel(CInDocTableModel):
    class CCompositionInDocTableCol(CInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.caches = {}

        def toString(self, val, record):
            activeSubstanceId = forceRef(val)
            name = u''
            if activeSubstanceId:
                record = self.caches.get(activeSubstanceId, None)
                if not record:
                    db = QtGui.qApp.db
                    table = db.table('rbNomenclatureActiveSubstance')
                    record = db.getRecordEx(table, [table['name'], table['mnnLatin']], [table['id'].eq(activeSubstanceId)])
                if record:
                    name = forceStringEx(record.value('name'))
                    if not name:
                        name = forceStringEx(record.value('mnnLatin'))
                self.caches[activeSubstanceId] = record
            return toVariant(name)

        def createEditor(self, parent):
            editor = CActiveSubstanceComboBox(parent)
            return editor

        def setEditorData(self, editor, value, record):
            editor.setValue(forceRef(value))

        def getEditorData(self, editor):
            return toVariant(editor.value())

    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'ClientIntoleranceMedicament', 'id', 'client_id', parent)
        self.addCol(CIntoleranceMedicamentModel.CCompositionInDocTableCol(u'Название медикамента', 'activeSubstance_id', 20)) #0012159
        self.addCol(CRBInDocTableCol(u'Тип реакции', 'reactionType_id', 30, 'rbReactionType'))
        self.addCol(CRBInDocTableCol(u'Проявление реакции', 'reactionManifestation_id', 30, 'rbReactionManifestation'))
        self.addCol(CEnumInDocTableCol(u'Степень', 'power', 15, [u'0 - не известно', u'1 - малая', u'2 - средняя', u'3 - высокая', u'4 - строгая']))
        self.addCol(CDateInDocTableCol(u'Дата установления', 'createDate', 15, canBeEmpty=True))
        self.addCol(CInDocTableCol(u'Примечание', 'notes', 30))


class CNormalParametersModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Client_NormalParameters', 'id', 'client_id', parent)
        self.addCol(CActionPropertyTemplateCol(u'Шаблон',     'template_id', 40))
        self.addCol(CInDocTableCol(            u'Показатели', 'norm',        12).setToolTip(u'Вводить значения: Минимальное-Максимальное'))


class CClientIdentificationModel(CInDocTableModel):
    mapAccountingSystemIdToNeedUniqueValue = {}


    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'ClientIdentification', 'id', 'client_id', parent)
        self.__parent = parent
        self.addCol(CRBInDocTableCol(u'Внешняя учётная система', 'accountingSystem_id', 30, 'rbAccountingSystem', addNone=False, filter="domain='Client'"))
        self.addCol(CInDocTableCol(u'Идентификатор', 'identifier', 30))
        self.addCol(CDateInDocTableCol(u'Дата подтверждения',  'checkDate', 15, canBeEmpty=True))
        self.addCol(CInDocTableCol(u'Примечание',  'note', 15, maxLength=128))
        self.isEditable = {}
        self.isDeletable = {}
        flagsList = QtGui.qApp.db.getRecordList('rbAccountingSystem', 'id, isEditable, isDeletable', where="domain='Client'")
        if flagsList:
            for x in flagsList:
                self.isEditable[forceRef(x.value(0))] = forceBool(x.value(1))
                self.isDeletable[forceRef(x.value(0))] = forceBool(x.value(2))


    def flags(self, index = QModelIndex()):
        column = index.column()
        if column in (0, 2, 3):  # accountingSystem_id, checkDate, note
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
        if column == 1:  # identifier
            row = index.row()
            items = self.items()
            record = items[row] if 0 <= row < len(items) else None
            accountingSystemId = forceRef(record.value('accountingSystem_id')) if record else None
            nullId = (forceString(record.value('identifier')) == '') if record else True
            if accountingSystemId and (self.isEditable.get(accountingSystemId,  False) or nullId):
                return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return CInDocTableModel.flags(self, index)


    def getEmptyRecord(self):
        result = CInDocTableModel.getEmptyRecord(self)
        result.setValue('checkDate',         toVariant(QDate.currentDate()))
        return result


    def emitDataChanged(self, row, column):
        index = self.index(row, column)
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)


    def saveItems(self, client_id):
        return CInDocTableModel.saveItems(self, client_id)

    def setData(self, index, value, role=Qt.EditRole):
        items = self.items()
        col = index.column()
        if col == 0: # если меняем систему, проверим уникальность
            if not forceRef(value):
                return False

            for record in items:
                if forceRef(record.value('accountingSystem_id')) == forceRef(value):
#                    QtGui.QMessageBox.critical( self.__parent, u'Изменение типа учётной системы',
#                        u'Идентификатор в выбранной учётной системе уже задан.',
#                        QtGui.QMessageBox.Close)
                    #self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)
                    return False

        if col == 1: # меняем идентификатор. Проверяем необходимость проверки на уникальность и если нужно проверяем.
            newIdentifier = forceString(value)
            if newIdentifier == '':
                return False
            item = items[index.row()]
            currentItemId = forceRef(item.value('id'))
            accountingSystemId = forceRef(item.value('accountingSystem_id'))
            if self.needUniqueValue(accountingSystemId):
                if not uniqueIdentifierCheckingIsPassed(currentItemId, accountingSystemId, newIdentifier):
                    return False
        result = CInDocTableModel.setData(self, index, value, role)
        if result and role == Qt.EditRole:
            row = index.row()
            record = items[row] if 0<=row<len(items) else None
            if record:
                record.setValue('checkDate',         toVariant(QDate.currentDate()))
                self.emitDataChanged(row, 2) # колонка checkDate
        return result


    def delRowsChecker(self, rows):
        items = self.items()
        for row in rows:
            record = items[row]
            isNew = record.isNull('id')
            accountingSystemId = forceRef(record.value('accountingSystem_id'))
            if not isNew and accountingSystemId and not self.isDeletable.get(accountingSystemId, False):
                return False
        return True


    @classmethod
    def needUniqueValue(cls, accountingSystemId):
        isUnique = cls.mapAccountingSystemIdToNeedUniqueValue.get(accountingSystemId, None)
        if isUnique is None:
            isUnique = forceBool(QtGui.qApp.db.translate('rbAccountingSystem',
                                                         'id',
                                                          accountingSystemId,
                                                         'isUnique'))
            cls.mapAccountingSystemIdToNeedUniqueValue[accountingSystemId] = isUnique
        return isUnique


# ####################################################################


class CRBQuotaTypeInDocTableCol(CRBInDocTableCol):
    def createEditor(self, parent):
        editor = CQuotaTypeComboBox(parent)
        editor.setTable(self.tableName, addNone=self.addNone, filter=self.filter)
        editor.setShowFields(self.showFields)
        editor.setPreferredWidth(self.preferredWidth)
        return editor


class CClientQuotingModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Client_Quoting', 'id', 'master_id', parent)
        self.addCol(CRBQuotaTypeInDocTableCol(u'Квота', 'quotaType_id', 255, 'QuotaType', showFields=0))
        self.addCol(CIntInDocTableCol(u'Этап', 'stage', 2))
        self.addCol(CInDocTableCol(u'МКБ', 'MKB', 8))
        self.addCol(CEnumInDocTableCol(u'Статус', 'status', 2, [u'Отменено',
                                                                u'Ожидание',
                                                                u'Активный талон',
                                                                u'Талон для заполнения',
                                                                u'Заблокированный талон',
                                                                u'Отказано',
                                                                u'Необходимо согласовать дату обслуживания',
                                                                u'Дата обслуживания на согласовании',
                                                                u'Дата обслуживания согласована',
                                                                u'Пролечен',
                                                                u'Обслуживание отложено',
                                                                u'Отказ пациента',
                                                                u'Импортировано из ВТМП']))
        self.addHiddenCol('identifier')
        self.addHiddenCol('quotaTicket')
        self.addHiddenCol('directionDate')
        self.addHiddenCol('freeInput')
        self.addHiddenCol('org_id')
        self.addHiddenCol('amount')
        self.addHiddenCol('request')
        self.addHiddenCol('statment')
        self.addHiddenCol('dateRegistration')
        self.addHiddenCol('dateEnd')
        self.addHiddenCol('orgStructure_id')
        self.addHiddenCol('regionCode')
        self.addHiddenCol('districtCode')
        self._info = {}
        self.basicData = []
        self.basicDataCount = 0
        self.isActiveQuota = None
        self.currentRow = None
        self.isChangeingRow = None
        self.recordsForDeleting = []
        self.clientAttachForDeleting = []
        self.regCityCode = None
        self.newRegCityCode = None
        self.regDistrictCode = None
        self.newRegDistrictCode = None

    def addClientAttachForDeleting(self, attachRecord):
        self.clientAttachForDeleting.append(attachRecord)

    def setRegCityCode(self, regCityCode):
        self.regCityCode = regCityCode

    def setDistrictCode(self, regDistrictCode):
        self.regDistrictCode = regDistrictCode

    def setNewRegDistrictCode(self, regDistrictCode):
        self.newRegDistrictCode = regDistrictCode

    def setNewRegCityCode(self, regCityCode):
        self.newRegCityCode = regCityCode

    def flags(self, index):
        column = index.column()
        row    = index.row()
        if column == 0 and row == len(self.items()):
            return CInDocTableModel.flags(self, index)
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def getEmptyRecord(self):
        result = CInDocTableModel.getEmptyRecord(self)
        result.setValue('status', toVariant(1))
        currentDate = QDate.currentDate()
        result.setValue('dateRegistration', QVariant(currentDate))
        result.setValue('amount', QVariant(1))
        return result

    def setData(self, index, value, role=Qt.EditRole):
        resume = CInDocTableModel.setData(self, index, value, role)
        if resume:
            self.basicData.append([None, None, '', ''])
        return resume

    def info(self):
        return self._info

    def loadItems(self, masterId):
        CInDocTableModel.loadItems(self, masterId)
        self.saveBasicData()

    def saveBasicData(self):
        items = self.items()
        self.basicDataCount = len(items)
        for item in items:
            data = []
            data.append(forceInt(item.value('amount')))
            data.append(forceInt(item.value('status')))
            data.append(forceString(item.value('regionCode')))
            data.append(forceString(item.value('districtCode')))
            self.basicData.append(data)

    def saveItems(self, masterId):
#        for clientAttachRecord in self.clientAttachForDeleting:
#            clientAttachRecord.setValue('deleted', QVariant(1))
#            QtGui.qApp.db.updateRecord('ClientAttach', clientAttachRecord)
        items = self.items()
        basicData = self.basicData
        endedQuotes = 0
        minDate = None
        maxDate = None
        for idx, record in enumerate(items):
            currAmount = forceInt(record.value('amount'))
            currStatus = forceInt(record.value('status'))
            currRegionCode = forceString(record.value('regionCode'))
            currDistrictCode = forceString(record.value('districtCode'))
            baseAmount = basicData[idx][0]
            baseStatus = basicData[idx][1]
            baseRegionCode = basicData[idx][2]
            baseDistrictCode = basicData[idx][3]
            if currStatus in (5, 9, 11):
                endedQuotes += 1
                date = forceDate(record.value('dateEnd'))
                if not maxDate:
                    maxDate = date
                else:
                    if date > maxDate:
                        maxDate = date
            if not minDate:
                minDate = forceDate(record.value('dateRegistration'))
            else:
                date = forceDate(record.value('dateRegistration'))
                if date < minDate:
                    minDate = date
            if baseRegionCode:
                regCityCode = baseRegionCode
            else:
                regCityCode = self.regCityCode
            if currRegionCode:
                newRegCityCode = currRegionCode
            else:
                newRegCityCode = self.newRegCityCode
            if baseDistrictCode:
                regDistrictCode = baseDistrictCode
            else:
                regDistrictCode = self.regDistrictCode
            if currDistrictCode:
                newRegDistrictCode = currDistrictCode
            else:
                newRegDistrictCode = self.newRegDistrictCode
            if currStatus != baseStatus:
                quotingRecords = self.getActualQuotingRecords(record)
                if quotingRecords:
                    for quotingRecord in quotingRecords:
                        if baseAmount:
                            self.changeData(quotingRecord, baseStatus, baseAmount, baseAmount.__sub__)
                        self.changeData(quotingRecord, currStatus, currAmount, currAmount.__add__)
                        if regCityCode:
                            if baseAmount:
                                self.changeRegionData(baseStatus, baseAmount, baseAmount.__sub__,
                                                      regCityCode, quotingRecord)
                                self.changeDistrictData(baseStatus, baseAmount, baseAmount.__sub__,
                                                        (regCityCode, regDistrictCode), quotingRecord)
                        if newRegCityCode:
                            if regCityCode != newRegCityCode:
                                self.changeRegionData(currStatus, currAmount, currAmount.__add__,
                                                          newRegCityCode, quotingRecord)
                                if regDistrictCode != newRegDistrictCode:
                                    self.changeDistrictData(currStatus, currAmount, currAmount.__add__,
                                                            (newRegCityCode, newRegDistrictCode), quotingRecord)
                                else:
                                    self.changeDistrictData(currStatus, currAmount, currAmount.__add__,
                                                            (newRegCityCode, regDistrictCode), quotingRecord)
                            else:
                                self.changeRegionData(currStatus, currAmount, currAmount.__add__,
                                                      regCityCode, quotingRecord)
                                self.changeDistrictData(currStatus, currAmount, currAmount.__add__,
                                                        (regCityCode, regDistrictCode), quotingRecord)
            else:
                if currAmount != baseAmount:
                    quotingRecords = self.getActualQuotingRecords(record)
                    if quotingRecords:
                        for quotingRecord in quotingRecords:
                            dAmount = currAmount-baseAmount
                            self.changeData(quotingRecord, currStatus, dAmount, dAmount.__add__)
                            if regCityCode != newRegCityCode:
                                if regCityCode:
                                    self.changeRegionData(baseStatus, baseAmount, baseAmount.__sub__,
                                                          regCityCode, quotingRecord)
                                    self.changeDistrictData(baseStatus, baseAmount, baseAmount.__sub__,
                                                            (regCityCode, regDistrictCode), quotingRecord)
                                if newRegCityCode:
                                    self.changeRegionData(currStatus, currAmount, currAmount.__add__,
                                                          newRegCityCode, quotingRecord)
                                    self.changeDistrictData(currStatus, currAmount, currAmount.__add__,
                                                            (newRegCityCode, newRegDistrictCode), quotingRecord)
                            else:
                                if newRegCityCode:
                                    self.changeRegionData(currStatus, dAmount, dAmount.__add__,
                                                          newRegCityCode, quotingRecord)
                                    self.changeDistrictData(currStatus, dAmount, dAmount.__add__,
                                                            (newRegCityCode, newRegDistrictCode), quotingRecord)

        if len(items) > 0:
            self.setQuotingAttach(masterId, endedQuotes==len(items), minDate, maxDate, self.basicDataCount<len(items))
        CInDocTableModel.saveItems(self, masterId)
        if self.recordsForDeleting:
            self.changeQuotingDataForDeletedRecordList(self.recordsForDeleting)


    def setQuotingAttach(self, clientId, allAreEnded, minDate, maxDate, newQuotaAdded):
        db = QtGui.qApp.db
        table = db.table('ClientAttach')
        attachTypeId = db.translate('rbAttachType', 'code', '9', 'id')
        parent = QObject.parent(self)
        assert isinstance(parent, CClientEditDialog)
        attachItems = parent.tblAttaches.model().items()
        quotaAttachListEnded = []
        quotaAttachListNotEnded = []
        recordList = []
        if attachItems:
            quotaAttachList = [attach for attach in attachItems if attach.value('attachType_id') == attachTypeId]
            if quotaAttachList:
                for attach in quotaAttachList:
                    if forceDate(attach.value('endDate')).isValid():
                        quotaAttachListEnded.append(attach)
                    else:
                        quotaAttachListNotEnded.append(attach)
        if (not attachItems) or (not quotaAttachListNotEnded and newQuotaAdded):
            record = table.newRecord()
            record.setValue('client_id', QVariant(clientId))
            record.setValue('attachType_id', attachTypeId)
            record.setValue('LPU_id', QVariant(QtGui.qApp.currentOrgId()))
            record.setValue('begDate', QVariant(minDate))
            if allAreEnded:
                record.setValue('endDate', QVariant(maxDate))
            recordList.append(record)
        else:
            if quotaAttachListNotEnded:
                for attach in quotaAttachListNotEnded:
                    attach.setValue('begDate', QVariant(minDate))
                    if allAreEnded:
                        attach.setValue('endDate', QVariant(maxDate))
                    recordList.append(attach)
        clientQuotaAttachIdList = []
        for record in recordList:
            clientQuotaAttachIdList.append(db.insertOrUpdate('ClientAttach', record))
        return clientQuotaAttachIdList


    def changeRegionData(self, status, amount, action, code, quotingRecord):
        regionRecords = findKLADRRegionRecordsInQuoting(code, quotingRecord)
        for regionRecord in regionRecords:
            self.changeData(regionRecord, status, amount, action, 'Quoting_Region')


    def changeDistrictData(self, status, amount, action, codes, quotingRecord):
        regionRecords = findDistrictRecordsInQuoting(codes, quotingRecord)
        for regionRecord in regionRecords:
            self.changeData(regionRecord, status, amount, action, 'Quoting_District')


    def changeData(self, quotingRecord, status, amount, action, table='Quoting'):
        columnName = self.translateStatusToColumn(status)
        if columnName:
            columnValue = forceInt(quotingRecord.value(columnName))
            resumeValue = abs(action(columnValue))
            quotingRecord.setValue(columnName, QVariant(resumeValue))
            QtGui.qApp.db.updateRecord(table, quotingRecord)

    def translateStatusToColumn(self, status):
        if status == 9:
            return 'used'
        if status == 8:
            return 'confirmed'
        if status in (1, 2, 3, 4, 6, 7, 10, 12):
            return 'inQueue'
#        if status in (0, 5, 11):
        return None

    def getActualQuotingRecords(self, record):
        db = QtGui.qApp.db
        dateRegistration = forceDate(record.value('dateRegistration'))
        dateEnd          = forceDate(record.value('dateEnd'))
        quotaType_id     = forceInt(record.value('quotaType_id'))
        tableQuoting = db.table('Quoting')
        if not dateEnd:
            condDate = [tableQuoting['endDate'].ge(dateRegistration)]
        else:
            condDate = [db.joinOr([db.joinAnd([tableQuoting['beginDate'].le(dateRegistration),
                                   tableQuoting['endDate'].ge(dateRegistration)]),
                        db.joinAnd([tableQuoting['beginDate'].le(dateEnd),
                                   tableQuoting['endDate'].ge(dateEnd)])])]
        condDate.append(tableQuoting['deleted'].eq(0))
        record = db.getRecordEx(tableQuoting,'*',[tableQuoting['quotaType_id'].eq(quotaType_id)]+condDate)
        list = []
        if record:
            list.append(record)
#        else:
        code = forceString(db.translate('QuotaType', 'id', quotaType_id, 'code'))
        while code.find('.') > -1:
            record, code = self.checkParent(tableQuoting, condDate, quotaType_id)
            quotaType_id = forceRef(db.translate('QuotaType', 'code', code, 'id'))
            if record:
                list.append(record)
        return list

    def setNullInfo(self):
        self._info['limit'] = 0
        self._info['used'] = 0
        self._info['confirmed'] = 0
        self._info['inQueue'] = 0

    def loadItemsInfo(self, row):
        if row is None:
            self.setNullInfo()
            self._info['quotaTypeName'] = ''
            return
        db = QtGui.qApp.db
        tableQuoting = db.table('Quoting')
        record = self.items()[row]
        quotaType_id = forceInt(record.value('quotaType_id'))
        quotaTypeName = forceString(
                        QtGui.qApp.db.translate('QuotaType', 'id', quotaType_id, 'name'))
        condDate = []
        dateRegistration = forceDateTime(record.value('dateRegistration'))
        dateEnd          = forceDateTime(record.value('dateEnd'))
        if dateRegistration:
            condDate.append(db.joinAnd([tableQuoting['beginDate'].le(dateRegistration),
                                       tableQuoting['endDate'].ge(dateRegistration)]))
        if dateEnd:
            condDate.append(db.joinAnd([tableQuoting['beginDate'].le(dateEnd),
                                       tableQuoting['endDate'].ge(dateEnd)]))
        cond = [db.joinOr(condDate)] if condDate else []
        recordQuoting, brothersLimitIfNeedElseZero = self.getQuotingRecord(tableQuoting, cond, quotaType_id)
        self._info['quotaTypeName']    = quotaTypeName
        if recordQuoting:
            self._info['limit'] = forceInt(recordQuoting.value('limitation')) - brothersLimitIfNeedElseZero
            self._info['used'] = forceInt(recordQuoting.value('used'))
            self._info['confirmed'] = forceInt(recordQuoting.value('confirmed'))
            self._info['inQueue'] = forceInt(recordQuoting.value('inQueue'))
        else:
            self.setNullInfo()

    def getQuotingRecord(self, tableQuoting, cond, quotaType_id):
        db = QtGui.qApp.db
        condTmp = list(cond)
        condTmp.append(tableQuoting['quotaType_id'].eq(quotaType_id))
        record = db.getRecordEx('Quoting', '*', condTmp)
        if record:
            return record, 0
        else:
            val = 0
            record, parentCode = self.checkParent(tableQuoting, cond, quotaType_id)
            if record:
                val = self.checkBrothersLimit(tableQuoting, cond, parentCode)
            return record, val


    def checkParent(self, tableQuoting, cond, quotaType_id):
        db = QtGui.qApp.db
        parentCode = forceString(db.translate('QuotaType', 'id', quotaType_id, 'group_code'))
        if parentCode:
            parentId = forceInt(db.translate('QuotaType', 'code', parentCode, 'id'))
            record, val = self.getQuotingRecord(tableQuoting, cond, parentId)
            return record, parentCode
        else:
            return None, ''

    def checkBrothersLimit(self, tableQuoting, cond, parentCode):
        db = QtGui.qApp.db
        idList = db.getIdList('QuotaType', 'id', 'group_code=%s'%parentCode)
        condTmp = list(cond)
        condTmp.append(tableQuoting['quotaType_id'].inlist(idList))
        stmt = db.selectStmt(tableQuoting, 'SUM(`limitation`)', condTmp)
        query = db.query(stmt)
        if query.first():
            return forceInt(query.value(0))
        return 0

    def removeRows(self, row, count, parentIndex = QModelIndex()):
        tmpItems = list(self.items())
        resume = CInDocTableModel.removeRows(self, row, count, parentIndex)
        if resume:
            itemsForDeleting = tmpItems[row:row+count]
            for item in itemsForDeleting:
                self.recordsForDeleting.append(item)
            decreaseBD = row in range(len(self.basicData))
            del self.basicData[row:row+count]
            if decreaseBD:
                self.basicDataCount = len(self.basicData)
        return resume

    def changeQuotingDataForDeletedRecordList(self, recordList):
        for record in recordList:
            if record.value('id').isValid():
                quotingRecords = self.getActualQuotingRecords(record)
                if quotingRecords:
                    for quotingRecord in quotingRecords:
                        status = forceInt(record.value('status'))
                        amount = forceInt(record.value('amount'))
                        self.changeData(quotingRecord, status, amount, amount.__sub__)
                        regCityCode = self.regCityCode
                        if not regCityCode:
                            parent = QObject.parent(self)
                            assert isinstance(parent, CClientEditDialog)
                            regCityCode = parent.cmbRegCity.code()
                        self.changeRegionData(status, amount, amount.__sub__,
                                              regCityCode, quotingRecord)
                        regDistrictCode = self.regDistrictCode
                        if not regDistrictCode:
                            parent = QObject.parent(self)
                            assert isinstance(parent, CClientEditDialog)
                            regDistrictCode = getOKATO(regCityCode, parent.cmbRegStreet.code(),
                                                       parent.edtRegHouse.text())
                        self.changeDistrictData(status, amount, amount.__sub__,
                                                (regCityCode, regDistrictCode), quotingRecord)


class CClientQuotingDiscussionModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent,  [
            CDateCol(u'Дата', ['dateMessage'], 16),
            CTimeCol(u'Время', ['dateMessage'], 16),
            CRefBookCol(u'Тип согласования', ['agreementType_id'], 'rbAgreementType', 15),
            CRefBookCol(u'Ответственный ЛПУ', ['responsiblePerson_id'], 'vrbPersonWithSpeciality', 16, 1),
            CTextCol(u'Контрагент', ['cosignatory'], 25),
            CTextCol(u'Должность', ['cosignatoryPost'], 20),
            CNameCol(u'ФИО', ['cosignatoryName'], 50),
            CTextCol(u'Примечание', ['remark'], 128)
            ], 'Client_QuotingDiscussion')
# #############################################################################

class CClientConsentsInDocModel(CInDocTableModel):
    class CClientRelationInDocCol(CInDocTableCol):
        def __init__(self):
            CInDocTableCol.__init__(self, u'Подписавший', 'representerClient_id', 15)
            self._cache = {}
            self._clientId = None


        def setClientId(self, clientId):
            self._clientId = clientId


        def toString(self, val, record):
            representerClientId = forceRef(val)
            if representerClientId:
                result = self._cache.get(representerClientId, None)
                if result is not None:
                    return QVariant(result)

                db = QtGui.qApp.db
                tableC  = db.table('Client')
                if representerClientId == self._clientId:
                    clientRecord = db.getRecord(tableC, 'lastName, firstName, patrName, birthDate', representerClientId)
                    if clientRecord:
                        name = formatShortName(clientRecord.value('lastName'),
                                               clientRecord.value('firstName'),
                                               clientRecord.value('patrName'))
                        result = u', '.join([name, forceString(clientRecord.value('birthDate'))])
                    else:
                        result = u'Неправильные данные!'
                else:
                    tableCR = db.table('ClientRelation')
                    tableRT = db.table('rbRelationType')
                    queryTable = tableCR
                    queryTable = queryTable.leftJoin(tableRT, tableRT['id'].eq(tableCR['relativeType_id']))
                    queryTable = queryTable.leftJoin(tableC, tableC['id'].eq(tableCR['relative_id']))
                    cond = [tableCR['client_id'].eq(self._clientId),
                            tableCR['relative_id'].eq(representerClientId),
                            tableCR['deleted'].eq(0)]
                    fields = ['CONCAT_WS(\' | \', rbRelationType.`code`, CONCAT_WS(\'->\', rbRelationType.`leftName`, rbRelationType.`rightName`)) AS relationType',
                              tableC['lastName'].alias(), tableC['firstName'].name(),
                              tableC['patrName'].name(), tableC['birthDate'].name(),
                              tableC['id'].alias('relativeId')]
                    clientRelationRecord = db.getRecordEx(queryTable, fields, cond)
                    if clientRelationRecord:
                        name = formatShortName(clientRelationRecord.value('lastName'),
                                               clientRelationRecord.value('firstName'),
                                               clientRelationRecord.value('patrName'))
                        result = ', '.join([name,
                                            forceString(clientRelationRecord.value('birthDate')),
                                            forceString(clientRelationRecord.value('relationType'))])
                    else:
                        tableCR = db.table('ClientRelation')
                        tableRT = db.table('rbRelationType')
                        queryTable = tableCR
                        queryTable = queryTable.leftJoin(tableRT, tableRT['id'].eq(tableCR['relativeType_id']))
                        queryTable = queryTable.leftJoin(tableC, tableC['id'].eq(tableCR['client_id']))
                        cond = [tableCR['client_id'].eq(representerClientId),
                                tableCR['relative_id'].eq(self._clientId),
                                tableCR['deleted'].eq(0)]
                        fields = ['CONCAT_WS(\' | \', rbRelationType.`code`, CONCAT_WS(\'->\', rbRelationType.`rightName`, rbRelationType.`leftName`)) AS relationType',
                                  tableC['lastName'].alias(), tableC['firstName'].name(),
                                  tableC['patrName'].name(), tableC['birthDate'].name(),
                                  tableC['id'].alias('relativeId')]
                        clientRelationRecord = db.getRecordEx(queryTable, fields, cond)
                        if clientRelationRecord:
                            name = formatShortName(clientRelationRecord.value('lastName'),
                                                   clientRelationRecord.value('firstName'),
                                                   clientRelationRecord.value('patrName'))
                            result = ', '.join([name,
                                                forceString(clientRelationRecord.value('birthDate')),
                                                forceString(clientRelationRecord.value('relationType'))])
                        else:
                            result = u'Неправильные данные!'
                self._cache[representerClientId] = result
                return QVariant(result)
            return QVariant()


        def createEditor(self, parent):
            editor = CClientRelationComboBoxForConsents(parent)
            editor.setClientId(self._clientId)
            return editor


        def setEditorData(self, editor, value, record):
            editor.setValue(forceRef(value))


        def getEditorData(self, editor):
            return toVariant(editor.value())


    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'ClientConsent', 'id', 'client_id', parent)
        self.addCol(CRBInDocTableCol(u'Тип согласия', 'clientConsentType_id', 15, 'rbClientConsentType'))
        self.addCol(CDateInDocTableCol(u'Дата регистрации согласия', 'date', 15))
        self.addCol(CEnumInDocTableCol( u'Значение', 'value', 10, [u'Нет', u'Да']))
        self.addCol(CDateInDocTableCol(u'Дата окончания согласия', 'endDate', 15))
        self.addCol(CInDocTableCol(u'Примечания', 'note', 15))
        self._colClientRelation = CClientConsentsInDocModel.CClientRelationInDocCol()
        self.addCol(self._colClientRelation)
        self._clientId = None

    def currentClientId(self):
        return self._clientId

    def setClientId(self, clientId):
        self._clientId = clientId
        self._colClientRelation.setClientId(clientId)


# #############################

class CAddressesTableModel(CTableModel):
    typeReg = 0
    typeLoc = 1
    class CClientAddressCol(CCol):
        def __init__(self, title, fields, defaultWidth):
            CCol.__init__(self, title, fields, defaultWidth, u'l')
            self._cache = {}

        def format(self, values):
            clientAddressId = forceRef(values[0])
            result = self._cache.get(clientAddressId, None)
            if result is None:
                addressId = forceRef(values[1].value('address_id'))
                if addressId:
                    address = getAddress(addressId)
                    result = ', '.join([part for part in [formatAddressInt(address),
                                                          getDistrictName(address.KLADRCode,
                                                                          address.KLADRStreetCode,
                                                                          address.number)
                                                         ] if part])
                else:
                    result = values[1].value('freeInput')
                self._cache[clientAddressId] = result
            return result


    def __init__(self, parent, _type):
        CTableModel.__init__(self, parent)
        self._type = _type
        self.addColumn(CDateTimeCol(u'Дата', [u'createDatetime'], 8))
        self.addColumn(CRefBookCol(u'Пользователь', [u'createPerson_id'], u'vrbPerson', 15))
        self.addColumn(CAddressesTableModel.CClientAddressCol(u'Адрес', [u'id'], 16))
        if self._type == CAddressesTableModel.typeReg:
            self.addColumn(CDateTimeCol(u'Дата регистрации', [u'addressDate'], 8))
        self.loadField(u'freeInput')
        self.loadField(u'address_id')
        self.setTable(u'ClientAddress')
        self._clientId = None
        self._mapColumnToOrder = {u'createDatetime': u'ClientAddress.createDatetime',
                                 u'createPerson_id': u'vrbPerson.name',
                                 u'id': u'IF(ClientAddress.address_id IS NOT NULL, formatAddress(ClientAddress.address_id), ClientAddress.freeInput)',
                                 u'addressDate': u'ClientAddress.addressDate',
                                 }


    def getOrder(self, fieldName, column):
        if hasattr(self._cols[column], 'extraFields'):
            if len(self._cols[column].extraFields) > 0:
                fieldName = self._cols[column].extraFields[0]
        return self._mapColumnToOrder[fieldName]


    def setClientId(self, clientId):
        if self._clientId != clientId:
            order = ['ClientAddress.createDatetime ASC']
            self.setIdList(QtGui.qApp.db.getIdList(self._table, where=[self._table['client_id'].eq(clientId), self._table['type'].eq(self._type), self._table['deleted'].eq(0)], order=order))
            self._clientId = clientId


    def deleteRecord(self, table, itemId):
        QtGui.qApp.db.markRecordsDeleted(table, table[self.idFieldName].eq(itemId))


class CClientResearchModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'ClientResearch', 'id', 'client_id', parent)
        self.addCol(CRBInDocTableCol(  u'Вид обследования', 'researchKind_id', 30, 'rbClientResearchKind', showFields=CRBComboBox.showNameAndCode, order='code')).setSortable()
        self.addCol(CDateInDocTableCol(u'Дата проведения', 'begDate', 15)).setSortable()
        self.addCol(CInDocTableCol(    u'Результат', 'researchResult', 30))
        self.addCol(CDateInDocTableCol(u'Годен до', 'endDate', 15, canBeEmpty=True)).setSortable()
        self.addCol(CInDocTableCol(    u'Примечание', 'note', 30))

class CClientActiveDispensaryModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'ClientActiveDispensary', 'id', 'client_id', parent)
        self.addCol(CDateInDocTableCol(u'Дата взятия', 'begDate', 15))
        self.addCol(CEnumInDocTableCol(u'Причина взятия', 'begReason', 20, CClientActiveDispensaryInfo.begReasons))
        self.addCol(CDateInDocTableCol(u'Дата снятия', 'endDate', 15, canBeEmpty=True))
        self.addCol(CEnumInDocTableCol(u'Причина снятия', 'endReason', 20, CClientActiveDispensaryInfo.endReasons))
        self.addCol(CEnumInDocTableCol(u'Характер асоциальных проявлений', 'behaviorType', 20, CClientActiveDispensaryInfo.behaviorTypes))
        self.addCol(CInDocTableCol(u'Примечание', 'note', 30))

class CClientDangerousModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'ClientDangerous', 'id', 'client_id', parent)
        self.addCol(CDateInDocTableCol(u'Дата совершения', 'date', 15))
        self.addCol(CInDocTableCol(u'Описание', 'description', 30))
        self.addCol(CInDocTableCol(u'Постановление суда', 'judgement', 30))
        self.addCol(CInDocTableCol(u'Примечание', 'note', 30))

class CClientForcedTreatmentModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'ClientForcedTreatment', 'id', 'client_id', parent)
        self.addCol(CDateInDocTableCol(u'Дата взятия на АПНЛ (судом)', 'begDate', 15)).setToolTip(u'Дата взятия на АПНЛ (судом)')
        self.addCol(CInDocTableCol(u'Наименование суда', 'judgement', 30)).setToolTip(u'Наименование суда')
        self.addCol(CEnumInDocTableCol(u'Тип лечения', 'treatmentType', 20, CClientForcedTreatmentInfo.treatmentTypes)).setToolTip(u'Тип лечения')
        self.addCol(CDateInDocTableCol(u'Дата ГПД', 'dispDate', 15, canBeEmpty=True)).setToolTip(u'Дата ГПД')
        self.addCol(CDateInDocTableCol(u'Дата очередной ВК', 'mcNextDate', 15, canBeEmpty=True)).setToolTip(u'Дата очередной ВК')
        self.addCol(CDateInDocTableCol(u'Дата последней ВК', 'mcLastDate', 15, canBeEmpty=True)).setToolTip(u'Дата последней ВК')
        self.addCol(CDateInDocTableCol(u'Дата снятия с АПНЛ (судом)', 'endDate', 15, canBeEmpty=True)).setToolTip(u'Дата снятия с АПНЛ (судом)')
        self.addCol(CEnumInDocTableCol(u'Причина снятия', 'endReason', 20, CClientForcedTreatmentInfo.endReasons)).setToolTip(u'Причина снятия')
        self.addCol(CDateInDocTableCol(u'Снято в ГПД', 'dispEndDate', 15, canBeEmpty=True)).setToolTip(u'Снято в ГПД')
        self.addCol(CDateInDocTableCol(u'Дата продления АПНЛ', 'continueDate', 15, canBeEmpty=True)).setToolTip(u'Дата продления АПНЛ')
        self.addCol(CDateInDocTableCol(u'Дата перевода на стационарное принудительное лечение', 'statBegDate', 15, canBeEmpty=True)).setToolTip(u'Дата перевода на стационарное принудительное лечение')
        self.addCol(CDateInDocTableCol(u'Дата снятия с принудительного лечения', 'statEndDate', 15, canBeEmpty=True)).setToolTip(u'Дата снятия с принудительного лечения')

class CClientSuicideModel(CInDocTableModel):    
    class CStatusConditionCol(CInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.valuesByStatusType = [
                [],
                [u'низкий', u'средний', u'высокий'],
                [u'незавершенный', u'завершенный']
            ]
            self.statusType = 0
        
        def setIndex(self, index):
            model = index.model()
            row = index.row()
            self.statusType = forceInt(model.value(row, 'statusType'))

        def createEditor(self, parent):
            editor = QtGui.QComboBox(parent)
            if 0 <= self.statusType < len(self.valuesByStatusType):
                for val in self.valuesByStatusType[self.statusType]:
                    editor.addItem(val)
            return editor

        def setEditorData(self, editor, value, record):
            index = editor.findText(forceString(value))
            editor.setCurrentIndex(index)

        def getEditorData(self, editor):
            return toVariant(editor.currentText())

    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'ClientSuicide', 'id', 'client_id', parent)
        self.addCol(CDateInDocTableCol(u'Дата', 'date', 15))
        self.statusTypeCol = self.addCol(CEnumInDocTableCol(u'Статус', 'statusType', 20, CClientSuicideInfo.statusTypes))
        self.statusConditionCol = self.addCol(CClientSuicideModel.CStatusConditionCol(u'Состояние', 'statusCondition', 20))
        self.addCol(CInDocTableCol(u'Особенности', 'description', 30))
        self.addCol(CInDocTableCol(u'Примечание', 'note', 30))

    def setData(self, index, value, role=Qt.EditRole):
        row = index.row()
        changedCol = self._cols[index.column()]
        if row < len(self._items) and changedCol == self.statusTypeCol:
            record = self._items[row]
            oldStatusType = forceInt(record.value('statusType'))
            if oldStatusType != forceInt(value):
                record.setValue('statusCondition', '')
                self.emitCellChanged(row, self.getColIndex('statusCondition'))
        return CInDocTableModel.setData(self, index, value, role)


class CClientContingentKindModel(CMKBListInDocTableModel):
    reasons = (
        u'',
        u'1 - стойкая ремиссия/выздоровление',
        u'2 - смена места жительства',
        u'3 - неявка более 12 мес',
        u'4 - лишение свободы более 12 мес',
        u'5 - смена контингента',
        u'6 - смерть',
        u'7 - по заявлению',
    )
    def __init__(self, parent):
        CMKBListInDocTableModel.__init__(self, 'ClientContingentKind', 'id', 'client_id', parent)
        rightOwnAreaOnly = parent.getRightOwnAreaOnly()
        self.hasCreateRight = (QtGui.qApp.userHasRight(urRegCreateClientContingentKindOwnAreaOnly) and rightOwnAreaOnly)
        self.hasEditOpenRight = (QtGui.qApp.userHasRight(urRegEditClientContingentKindOpenOwnAreaOnly) and rightOwnAreaOnly)
        self.hasEditCloseRight = (QtGui.qApp.userHasRight(urRegEditClientContingentKindClosedOwnAreaOnly) and rightOwnAreaOnly)
        self.addCol(CRBInDocTableCol(u'Вид', 'contingentKind_id', 30, 'rbContingentKind', showFields=CRBComboBox.showNameAndCode, order='code')).setSortable()
        self.addCol(CRBInDocTableCol(u'Группа наблюдения', 'observationGroup_id', 30, 'rbObservationGroup', showFields=CRBComboBox.showCode))
        self.addCol(CObservationSubgroupInDocTableCol(u'Подгруппа наблюдения', u'observationSubgroups', 30))
        self.addCol(CDateInDocTableCol(u'Дата постановки', 'begDate', 15)).setSortable()
        self.addCol(CDateInDocTableCol(u'Дата снятия', 'endDate', 15, canBeEmpty=True)).setSortable()
        self.addCol(CRBInDocTableCol(u'Причина снятия', 'contingentKindRemoval_id', 20, 'rbContingentKindRemoval', showFields=CRBComboBox.showNameAndCode, order='code', filter='deleted=0'))
        self.addCol(CRBInDocTableCol(u'Специальность', 'speciality_id', 30, 'rbSpeciality', showFields=CRBComboBox.showNameAndCode, order='code'))
        self.addCol(CAPLikeOrgInDocTableCol(u'Организация', 'org_id', 30)).setFilter('deleted = 0')
        self.addCol(CICDExInDocTableCol(u'МКБ', 'MKB', 7))
        if QtGui.qApp.isExSubclassMKBVisible():
            self.addCol(CMKBExSubclassCol(u'РСК', 'exSubclassMKB', 10)).setToolTip(u'Расширенная субклассификация МКБ')
        self.addCol(CInDocTableCol(u'Примечание', 'note', 30))
        
        
    def setRemovalReasonFilter(self, record):
        db = QtGui.qApp.db
        filter = u'deleted=0'
        filter += u' AND (contingentKind_id is NULL {})'.format(
            "or contingentKind_id = {}".format(
                forceString(record.value('contingentKind_id'))
                ) if forceString(record.value('contingentKind_id')) else ''
            )
        if forceString(record.value('endDate')):
            filter+= u''' 
            AND ((begDate is NULL) or (begDate<={0}))
            AND ((endDate is NULL) or (endDate>={0}))
            '''.format(db.formatDate(forceDate(record.value('endDate'))))
        else:
            filter+= u''' 
            AND ((endDate is NULL) or (endDate>={}))
            '''.format(db.formatDate((QDate.currentDate())))
        self._cols[5].setFilter(filter)


    def flags(self, index=QModelIndex()):
        result = CInDocTableModel.flags(self, index)
        row = index.row()
        if row < len(self._items):
            column = index.column()
            if QtGui.qApp.isExSubclassMKBVisible() and index.isValid():
                if column == self.getColIndex('exSubclassMKB'):
                    mkb = forceString(self.items()[row].value('MKB'))
                    if len(mkb) != 6:
                        return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return result


    def setData(self, index, value, role=Qt.EditRole):
        isCreate = False
        isEditClose = False
        result = None
        hasOpen = False
        column = index.column()
        row = index.row()
        if row == len(self._items):
            if value.isNull():
                return False
            self._addEmptyItem()
        for item in self.items():
            if not item.isEmpty():
                if not forceString(item.value('endDate')) and forceBool(item.value('id')):
                    hasOpen = True
                    break
        if QtGui.qApp.userHasRight(urEnableTabContingentKind):
            return self.setDataResult(index, value, role, row, column)

        elif 0 <= row < len(self.items()):
            if forceBool(self.items()[row].value('id')):
                db = QtGui.qApp.db
                record = db.getRecord('ClientContingentKind', 'endDate, contingentKindRemoval_id', forceInt(self.items()[row].value('id')))
                isEditClose = forceBool(forceString(record.value('endDate'))) or forceBool(record.value('contingentKindRemoval_id'))

            if not forceBool(self.items()[row].value('id')):
                isCreate = True

            if self.hasCreateRight and isCreate and not hasOpen:
                return self.setDataResult(index, value, role, row, column)

            elif self.hasEditOpenRight and not isCreate and not isEditClose:
                return self.setDataResult(index, value, role, row, column)

            elif self.hasEditCloseRight and not isCreate and isEditClose:
                return self.setDataResult(index, value, role, row, column)
        elif row == len(self.items()):
            if self.hasCreateRight and not hasOpen:
                return self.setDataResult(index, value, role, row, column)

        if not result:
            QtGui.QMessageBox.information(self.parent,
                                        u'Внимание!',
                                        u'Недостаточно прав для ввода данных!',
                                        QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
            return True

    def setDataResult(self, index, value, role, row, column):
        if not variantEq(self.data(index, role), value):
            if column == 6:
                result = CInDocTableModel.setData(self, index, value, role)
                if result:
                    self.updateExSubclass(index, self.items()[row], forceString(value))
                    self.updateMKBToExSubclass(self.items()[row], forceString(value))
            if QtGui.qApp.isExSubclassMKBVisible() and 0 <= row < len(self.items()) and column == \
                    self.items()[row].indexOf('exSubclassMKB'):
                record = self.items()[row]
                self.updateMKBToExSubclass(record, forceStringEx(record.value('MKB')))
                return CInDocTableModel.setData(self, index, value, role)
            result = CInDocTableModel.setData(self, index, value, role)
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


class CClientHospitalizationModel(CInDocTableModel):
    purposes = (
        u'',
        u'лечение',
        u'принудительное лечение',
        u'трудовая экспертиза',
        u'военная экспертиза',
        u'судебная экспертиза',
        u'наркологическая экспертиза',
        u'другая экспертиза',
        u'прочие цели',
    )
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'ClientHospitalization', 'id', 'client_id', parent)
        self.addCol(CIntInDocTableCol(u'№', 'idx', 5, readOnly=True))
        self.addCol(CEnumInDocTableCol(u'Цель госпитализации', 'purpose', 20, CClientHospitalizationModel.purposes))
        self.addCol(CDateInDocTableCol(u'Дата поступления', 'begDate', 20))
        self.addCol(CDateInDocTableCol(u'Дата выбытия', 'endDate', 20))
        self.addCol(CICDExInDocTableCol(u'Диагноз поступления', 'receivedMKB', 20))
        self.addExtCol(CIntInDocTableCol(u'Дней госпитализации', 'bedDays', 20), QVariant.Int).setReadOnly(True)
        self.addCol(CSelectStrInDocTableCol(u'Кем направлен', 'whoDirected', 30, (u'', u'участковый врач', u'скорая помощь', u'неотложная помощь', u'полиция')))
        self.addCol(CBoolInDocTableCol(u'Первично', 'isPrimary', 5))
        self.addCol(CIntInDocTableCol(u'№ мед, свед.', 'medicalNumber', 20, high=2147483647))
        self.addCol(COrgInDocTableCol(u'Куда поступил', 'receivedOrg_id', 20))
        self.addCol(COrgInDocTableCol(u'Куда направлен', 'leavedOrg_id', 20))
        self.addCol(CICDExInDocTableCol(u'Диагноз выписки', 'leavedMKB', 20))
        self.addCol(CBoolInDocTableCol(u'Мед. сведения получены', 'infoTransmitted', 5))
        self.dataChanged.connect(self._updateIdxAndBedDays)
        self.rowsRemoved.connect(self._updateIdxAndBedDays)


    def _updateIdxAndBedDays(self, *args, **kwargs):
        for i, record in enumerate(self.items()):
            record.setValue('idx', i+1)
            begDate = forceDate(record.value('begDate'))
            endDate = forceDate(record.value('endDate'))
            if begDate and endDate:
                record.setValue('bedDays', begDate.daysTo(endDate))


    def loadItems(self, masterId):
        CInDocTableModel.loadItems(self, masterId)
        self._updateIdxAndBedDays()
    


class CAPLikeOrgInDocTableCol(CInDocTableCol):
    class CEditor(QtGui.QWidget):
        def __init__(self, parent, filter):
            QtGui.QWidget.__init__(self, parent)
            self.boxlayout = QtGui.QHBoxLayout(self)
            self.boxlayout.setMargin(0)
            self.boxlayout.setSpacing(0)
            self.boxlayout.setObjectName('boxlayout')
            self.cmbOrganisation = COrgComboBox(self)
            self.cmbOrganisation.setNameField("concat_ws(' | ', infisCode, shortName)")
            self.cmbOrganisation.setObjectName('cmbOrganisation')
            self.cmbOrganisation.setFilter(filter)
            self.boxlayout.addWidget(self.cmbOrganisation)
            self.btnSelect = QtGui.QPushButton(self)
            self.btnSelect.setObjectName('btnSelect')
            self.btnSelect.setText(u'...')
            self.btnSelect.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Ignored)
            self.btnSelect.setFixedWidth(20)
            self.boxlayout.addWidget(self.btnSelect)
            self.setFocusProxy(self.cmbOrganisation)
            self.connect(self.btnSelect, SIGNAL('clicked()'), self.on_btnSelect_clicked)

        def on_btnSelect_clicked(self):
            orgId = selectOrganisation(self, self.cmbOrganisation.value(), False, self.cmbOrganisation.filter(), None)
            self.cmbOrganisation.updateModel()
            if orgId:
                self.cmbOrganisation.setValue(orgId)

        def setValue(self, value):
            self.cmbOrganisation.setValue(value)

        def value(self):
            return self.cmbOrganisation.value()

    def __init__(self, title, fieldName, width):
        CInDocTableCol.__init__(self, title, fieldName, width)
        self.filter = None
    
    def setFilter(self, filter):
        self.filter = filter

    def toString(self, val, record):
        orgId = forceRef(val)
        text = getOrganisationInfisAndShortName(orgId)
        if text:
            return toVariant(text)
        return QVariant(u'не задано')

    def createEditor(self, parent):
        return CAPLikeOrgInDocTableCol.CEditor(parent, self.filter)

    def setEditorData(self, editor, value, record):
        editor.setValue(forceRef(value))

    def getEditorData(self, editor):
        return toVariant(editor.value())


class CCheckDatePolicyMessageBox(QtGui.QMessageBox):
    def __init__(self, icon, title, message, buttons, parent):
        QtGui.QMessageBox.__init__(self, icon, title, message, buttons, parent)


    def on_correct(self):
        self.done(2)

