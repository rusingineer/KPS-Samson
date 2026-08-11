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

# Редактор действия форма F090 #Электронная личная медицинская книжка #Electronic personal medical book  #ElectronicMedicalBook

import re

from PyQt4 import QtGui, QtSql

from PyQt4.QtGui import QCheckBox, QTextEdit
from PyQt4.QtCore import Qt, QDate, QDateTime, QVariant, pyqtSignature, QString, QChar, QEvent, QModelIndex, SIGNAL, QRegExp, QObject, QAbstractItemModel

from library.Attach.AttachAction     import getAttachAction
from library.Attach.AttachButton     import CAttachButton
from library.adjustPopup             import adjustPopupToWidget
from library.Calendar                import wpFiveDays, wpSixDays, wpSevenDays
from library.DateEdit                import CDateEdit
from library.DialogBase              import CDialogBase
from library.MultivalueTableDialog   import CRBRecordList
from library.Counter                 import CCounterController
from library.crbcombobox             import CRBComboBox
from library.InDocTable              import (CInDocTableModel,
                                             CInDocTableView,
                                             CMKBListInDocTableModel,
                                             CLocItemDelegate,
                                             CDateInDocTableCol,
                                             CInDocTableCol,
                                             CBoolInDocTableCol,
                                             CRBInDocTableCol,
                                             forcePyType,
                                             forceBool,
                                             #CRBLikeEnumInDocTableCol,
                                            )
from library.ICDInDocTableCol        import CICDExInDocTableCol
from library.ICDCodeEdit             import CICDCodeEditEx
from library.ICDUtils                import getMKBName, MKBwithoutSubclassification
from library.interchange             import (
                                              getDatetimeEditValue,
                                              getDoubleBoxValue,
                                              getLineEditValue,
                                              getRBComboBoxValue,
                                              getCheckBoxValue,
                                              setCheckBoxValue,
                                              setDatetimeEditValue,
                                              setDoubleBoxValue,
                                              setLineEditValue,
                                              setRBComboBoxValue,
                                            )

from library.ItemsListDialog         import CItemEditorBaseDialog
from library.PrintInfo               import CInfoContext
from library.PrintTemplates          import applyTemplate, customizePrintButton, getPrintButton
from library.StrComboBox             import CStrComboBox
from library.SortFilterProxyTableModel import CSortFilterProxyTableModel
from library.TableModel              import CTableModel, CTextCol, CEnumCol, CRefBookCol, CDateTimeCol
from library.TNMS.TNMSComboBox       import CTNMSCol
from library.MKBExSubclassComboBox   import CMKBExSubclassCol
from library.ICDMorphologyInDocTableCol import CMKBMorphologyCol
from library.Utils                   import (
                                              calcAgeTuple,
                                              forceDate,
                                              forceDateTime,
                                              forceInt,
                                              forceRef,
                                              forceDouble,
                                              forceString,
                                              forceStringEx,
                                              formatName,
                                              toDateTimeWithoutSeconds,
                                              trim,
                                              toVariant,
                                              exceptionToUnicode,
                                              variantEq,
                                              copyFields,
                                            )

from Events.Action                   import CAction, CActionType, CActionTypeCache
from Events.ActionEditDialog         import CActionEditDialog
from Events.ActionInfo               import CCookedActionInfo, CActionMEVaccinationInfoList, CActionMEExaminationsInfoList, CActionMEResearchesInfoList
from Events.ActionPropertiesTable    import CActionPropertiesTableModel
from Events.ActionStatus             import CActionStatus
from Events.ActionsModel             import CActionRecordItem
from Events.ActionTypeComboBox       import CActionTypeTableCol
from Events.ActionTemplateChoose     import CActionTemplateCache
from Events.DiagnosisType            import CDiagnosisTypeCol
from Events.Serialization            import storeUnsavedDataForEventDialog, loadUnsavedDataForEventDialog
from Events.EventInfo                import CEventInfo, CCookedEventInfo, CDiagnosticInfoProxyList #, CHospitalInfo
#from Events.MKBInfo                  import CMKBInfo
from Events.EventEditDialog          import CEventEditDialog, getToxicSubstancesIdListByMKB #, CDiseaseCharacter, CDiseaseStage, CDiseasePhases, CToxicSubstances
from Events.ContractTariffCache      import CContractTariffCache
from Events.EventVisitsModel         import CVisitServiceInDocTableCol
from Events.Utils                    import (
                                              checkAttachOnDate,
                                              checkPolicyOnDate,
                                              checkTissueJournalStatusByActions,
                                              getEventEnableActionsBeyondEvent,
                                              getEventDuration,
                                              getEventShowTime,
                                              getActionTypeIdListByFlatCode,
                                              getDeathDate,
                                              getEventPurposeId,
                                              specifyDiagnosis,
                                              checkSpecifyDiagnosis,
                                              setActionPropertiesColumnVisible,
                                              getEventMedicalAidKindId,
                                              getEventActionContract,
                                              getEventActionFinance,
                                              getEventPlannedInspections,
                                              getExactServiceId,
                                              getEventSceneId,
                                              CPayStatus,
                                              checkIsHandleDiagnosisIsChecked,
                                              getWorstPayStatus,
                                              getDiagnosisId2,
                                              recordAcceptable,
                                              checkDiagnosis,
                                              #getEventTypeForm,
                                              #getEventActionContract,
                                            )
from Orgs.Orgs                       import selectOrganisation
from Orgs.OrgComboBox                import CContractDbModel
from Orgs.PersonComboBoxEx           import CPersonFindInDocTableCol
from Registry.Utils                  import getClientInfo, getClientBanner
from Registry.ClientEditDialog       import CClientEditDialog
from RefBooks.Vaccine.List           import CVaccinationTypeDelegate
from F001.PreF001Dialog              import CPreF001Dialog
from Users.Rights                    import urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry, urEditClosedEvent, urEditAfterInvoicingEvent
from Events.ExportMIS                import iniExportEvent

from F090.Ui_F090 import Ui_F090Dialog


tabNotesFieldNames = ['relegateOrg_id',
                      'relegatePerson_id',
                      'srcNumber',
                      'srcDate',
                      'note',
                      'externalId',
                      'assistant_id',
                      'curator_id',
                      'patientModel_id',
                      'cureType_id',
                      'cureMethod_id',
                      'isClosed',
                      'relative_id',
                      'expertiseDate',
                      'expert_id',
                      'org_id',
                      'setDate',
                      'contract_id']

tabEventFieldNames = ['execPerson_id',
                      'setPerson_id',
                      'execDate',
                      'setDate',
                      'order',
                      'isPrimary',
                      'relegateOrg_id',
                      'relegatePerson_id',
                      'srcNumber',
                      'srcDate',
                      'note',
                      'externalId',
                      'assistant_id',
                      'curator_id',
                      'patientModel_id',
                      'cureType_id',
                      'cureMethod_id',
                      'isClosed',
                      'relative_id',
                      'expertiseDate',
                      'expert_id',
                      'org_id',
                      'setDate',
                      'contract_id']


rus = u'км.'
eng = u'rv/'
r2e = {}
e2r = {}
for i in range(len(rus)):
    r2e[ rus[i] ] = eng[i]
    e2r[ eng[i] ] = rus[i]


def propertyActionTypeDomainDefaultValue(propertyDescr, actionTypeId):
    db = QtGui.qApp.db
    tableAPT = db.table('ActionPropertyType')
    tableActionType = db.table('ActionType')
    cond =[tableActionType['id'].eq(actionTypeId),
           tableAPT['descr'].like(propertyDescr),
           tableActionType['deleted'].eq(0),
           tableAPT['deleted'].eq(0)
           ]
    queryTable = tableActionType.innerJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
    record = db.getRecordEx(queryTable, [tableAPT['valueDomain'], tableAPT['defaultValue']], cond)
    if record:
        return record.value('valueDomain'), record.value('defaultValue')
    return None, None


class CStrComboBoxItemDelegate(CLocItemDelegate):
    def __init__(self, parent, propertyDescr):
        CLocItemDelegate.__init__(self, parent)
        self.propertyDescr = propertyDescr


    def getPropertyDomain(self, propertyDescr, isNotDefined = True, actionId = None, actionTypeId = None):
        domain = u'\'не определено\',' if isNotDefined else u''
        record = None
        defaultValue = None
        if actionId:
            record, defaultValue = self.propertyActionDomain(propertyDescr, actionId)
        elif actionTypeId:
            record, defaultValue = propertyActionTypeDomainDefaultValue(propertyDescr, actionTypeId)
        if record:
            domainR = QString(forceString(record))
            if u'*' in domainR:
                index = domainR.indexOf(u'*', 0, Qt.CaseInsensitive)
                if domainR[index - 1] != u',':
                    domainR.replace(QString('*'), QString(','))
                else:
                    domainR.remove(QChar('*'), Qt.CaseInsensitive)
            domain += domainR
            if u'[mc]' in domain:
                domain = domain.remove(QString(u'[mc]'), Qt.CaseInsensitive)
        return domain, defaultValue


    def propertyActionDomain(self, propertyDescr, actionId):
        db = QtGui.qApp.db
        tableAction = db.table('Action')
        tableAPT = db.table('ActionPropertyType')
        tableActionType = db.table('ActionType')
        cond =[tableAction['id'].eq(actionId),
               tableAPT['descr'].like(propertyDescr),
               tableAction['deleted'].eq(0),
               tableActionType['deleted'].eq(0),
               tableAPT['deleted'].eq(0)
               ]
        queryTable = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
        queryTable = queryTable.innerJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
        record = db.getRecordEx(queryTable, [tableAPT['valueDomain'], tableAPT['defaultValue']], cond)
        if record:
            return record.value('valueDomain'), record.value('defaultValue')
        return None, None


    def createEditor(self, parent, option, index):
        self.row = index.row()
        model = index.model()
        col = model.cols()[model.Col_Result]
        items = model.items()
        actionId = model.actionId
        actionTypeId = model.actionTypeId
        domain = u''
        defaultValue = None
        if 0 <= self.row < len(items) and not actionId and not actionTypeId:
            record = items[self.row]
            actionId = forceRef(record.value('master_id')) if record else None
        if actionId:
            if col.actionIdDomainCache.has_key(actionId):
                domain, defaultValue = col.actionIdDomainCache[actionId]
            else:
                domain, defaultValue = self.getPropertyDomain(self.propertyDescr, isNotDefined = False, actionId = actionId, actionTypeId = None)
                model.cols()[model.Col_Result].actionIdDomainCache[actionId] = (domain, defaultValue)
        elif actionTypeId:
            if col.actionTypeIdDomainCache.has_key(actionTypeId):
                domain, defaultValue = col.actionTypeIdDomainCache[actionTypeId]
            else:
                domain, defaultValue = self.getPropertyDomain(self.propertyDescr, isNotDefined = False, actionId = None, actionTypeId = actionTypeId)
                model.cols()[model.Col_Result].actionTypeIdDomainCache[actionTypeId] = (domain, defaultValue)

        editor = CStrComboBox(parent)
        editor.setDomain(domain, isUpdateCurrIndex=False)
        self.connect(editor, SIGNAL('commit()'), self.emitCommitData)
        self.connect(editor, SIGNAL('editingFinished()'), self.commitAndCloseEditor)
        self.editor = editor
        self.rowcount = index.model().rowCount(None)
        self.column = index.column()
        return editor


class CF090EditDialog(CItemEditorBaseDialog, Ui_F090Dialog):
    cdSaveNoClose = 4 # сохранить не закрывая

    def __init__(self, parent, isCreate=False):
        CItemEditorBaseDialog.__init__(self, parent, 'Action')
        self.isCreate = isCreate
        self.action = None
        self.eventId     = None
        self._eventExecDate = None
        self.eventTypeId = None
        self.eventPurposeId = None
        self.eventSetDate = None
        self.eventDate = None
        self.eventSetDateTime = None
        self.clientId    = None
        self.forceClientId = None
        self.clientSex   = None
        self.clientAge   = None
        self.clientBirthDate = None
        self.clientDeathDate = None
        self.personId    = None
        self.personSNILS = u''
        self.showTypeTemplate = 0
        self.personSpecialityId = None
        self.recordEvent = None
        self.clientInfo = None
        self.actionTypeId = None
        self.nomenclatureSmnnUUIDCache = {}
        self.mapSpecialityIdToDiagFilter = {}
        self.actionTypeIdList = []
        self.labActionTypeIdList = []
        self.toolActionTypeIdList = []
        self.nomenclativeServiceIdList = []
        self.labNomenclativeServiceIdList = []
        self.toolNomenclativeServiceIdList = []
        self.labServiceIdList = []
        self.toolServiceIdList = []
        self.serviceMap = {}
        self.nomenclativeServiceMap = {}
        self.selectInfectionIdList = []
        self.personSSFCache = {}
        self.mapActionTypeIdToServiceIdList = {}
        self.preDiagnostics = []
        self.isProtected = False
        self.hurtTypeTableName = u'rbHurtType'
        self.hurtTypeCond = []
        self.postIdList = []
        self.infectionIdList = []
        self.preSpecialityIdList = []
        self.orgId = None
        self.idx = 0
        self.isRelationRepresentativeSetClientId = False
        self.clientWorkHurtCodeList = []
        self.clientWorkHurtFactorCodeList = []
        self.eventTypeForm = u'090'
        self.addModels('MembersMSIPerson', CMembersMSIPersonTableModel(self))
        self.addModels('InfectionDiseases', CInfectionDiseasesTableModel(self, diagnosisTypeCode=u'60'))
        self.addModels('ClientDiseases', CClientDiseasesTableModel(self))
        self.addModels('Vaccinations', CVaccinationsTableModel(self))
        self.addModels('ClientVaccinations', CClientVaccinationsTableModel(self))
        self.addModels('StatusActions', CStatusActionsTableModel(self))
        self.addModels('StatusActionProperties', CActionPropertiesTableModel(self))
        self.addModels('ClientStatusActions', CClientStatusActionsTableModel(self))
        self.addModels('ClientStatusActionProperties', CActionPropertiesTableModel(self))
        self.addModels('LabDiagnosticActions', CLabDiagnosticActionsTableModel(self))
        self.addModels('ToolDiagnosticActions', CToolDiagnosticActionsTableModel(self))
        self.addModels('DiagnosticActionProperties', CActionPropertiesTableModel(self))
        self.addModels('ClientDiagnosticActions', CClientDiagnosticActionsTableModel(self))
        self.addModels('ClientDiagnosticActionProperties', CActionPropertiesTableModel(self))
        self.addModels('Export', CEventExportTableModel(self))
        self.addModels('Export_FileAttach', CAdvancedExportTableModel(self))
        self.addModels('Export_VIMIS', CAdvancedExportTableModel(self))
        self.addModels('Diagnostics', CInspectionsResultModel(self))
        self.addObject('actInfectionDiseasesInsert',QtGui.QAction(u'Добавить в медицинское заключение', self))
        self.addObject('actInfectionDiseasesCheckedAllRow',QtGui.QAction(u'Выбрать все', self))
        self.addObject('actInfectionDiseasesClearCheckedAllRow',QtGui.QAction(u'Снять все отметки', self))
        self.addObject('actVaccinationsInsert',QtGui.QAction(u'Добавить в медицинское заключение', self))
        self.addObject('actClientVaccinationsCheckedAllRow',QtGui.QAction(u'Выбрать все', self))
        self.addObject('actClientVaccinationsClearCheckedAllRow',QtGui.QAction(u'Снять все отметки', self))
        self.addObject('actStatusActionsInsert',QtGui.QAction(u'Добавить в медицинское заключение', self))
        self.addObject('actClientStatusActionsCheckedAllRow',QtGui.QAction(u'Выбрать все', self))
        self.addObject('actClientStatusActionsClearCheckedAllRow',QtGui.QAction(u'Снять все отметки', self))
        self.addObject('actDiagnosticActionsInsert',QtGui.QAction(u'Добавить в медицинское заключение', self))
        self.addObject('actClientDiagnosticActionsCheckedAllRow',QtGui.QAction(u'Выбрать все', self))
        self.addObject('actClientDiagnosticActionsClearCheckedAllRow',QtGui.QAction(u'Снять все отметки', self))
        self.addObject('actShowAttachedToClientFiles', getAttachAction('Client_FileAttach',  self))
        self.addObject('actEditClient', QtGui.QAction(u'Открыть регистрационную карточку', self))
        self.addObject('btnPrint', getPrintButton(self, ''))
        self.addObject('btnAttachedFiles', CAttachButton(self, u'Прикреплённые файлы'))
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setWindowTitleEx(u'Медицинское заключение по результатам медицинского осмотра работника для предоставления в подсистему ЭЛМК')
        self.setWindowState(Qt.WindowMaximized)
        self.actionTypeIdListByELMK = self.getActionTypeIdListByELMK(flatCode = u'%medical_examination')
        self.initNewDate()
        self.edtDirectionDate.canBeEmpty(True)
        self.edtEndDate.canBeEmpty(True)
        self.edtBegDate.canBeEmpty(True)
        self.isActionSave = False
        self.isBtnSave = False
        self.buttonBox.addButton(self.btnPrint, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnAttachedFiles, QtGui.QDialogButtonBox.ActionRole)
        self.btnAttachedFiles.changed.connect(self.setIsDirty)
        self.setModels(self.tblMembersMSIPerson, self.modelMembersMSIPerson, self.selectionModelMembersMSIPerson)
        self.setModels(self.tblInfectionDiseases, self.modelInfectionDiseases, self.selectionModelInfectionDiseases)
        self.setModels(self.tblClientDiseases, self.modelClientDiseases, self.selectionModelClientDiseases)
        self.setModels(self.tblVaccinations, self.modelVaccinations, self.selectionModelVaccinations)
        self.setModels(self.tblClientVaccinations, self.modelClientVaccinations, self.selectionModelClientVaccinations)
        self.setModels(self.tblStatusActions, self.modelStatusActions, self.selectionModelStatusActions)
        self.setModels(self.tblStatusActionProperties, self.modelStatusActionProperties, self.selectionModelStatusActionProperties)
        self.setModels(self.tblClientStatusActions, self.modelClientStatusActions, self.selectionModelClientStatusActions)
        self.setModels(self.tblClientStatusActionProperties, self.modelClientStatusActionProperties, self.selectionModelClientStatusActionProperties)
        self.setModels(self.tblLabDiagnosticActions, self.modelLabDiagnosticActions, self.selectionModelLabDiagnosticActions)
        self.setModels(self.tblToolDiagnosticActions, self.modelToolDiagnosticActions, self.selectionModelToolDiagnosticActions)
        self.setModels(self.tblDiagnosticActionProperties, self.modelDiagnosticActionProperties, self.selectionModelDiagnosticActionProperties)
        self.setModels(self.tblClientDiagnosticActions, self.modelClientDiagnosticActions, self.selectionModelClientDiagnosticActions)
        self.setModels(self.tblClientDiagnosticActionProperties, self.modelClientDiagnosticActionProperties, self.selectionModelClientDiagnosticActionProperties)
        self.setModels(self.tblExport, self.modelExport, self.selectionModelExport)
        self.setModels(self.tblExport_FileAttach, self.modelExport_FileAttach, self.selectionModelExport_FileAttach)
        self.setModels(self.tblExport_VIMIS, self.modelExport_VIMIS, self.selectionModelExport_VIMIS)
        self.tblInspectionsResult.setModel(self.modelDiagnostics)
        self.tblClientDiseases.createPopupMenu([self.actInfectionDiseasesCheckedAllRow, self.actInfectionDiseasesClearCheckedAllRow, self.actInfectionDiseasesInsert])
        self.tblClientVaccinations.createPopupMenu([self.actClientVaccinationsCheckedAllRow, self.actClientVaccinationsClearCheckedAllRow, self.actVaccinationsInsert])
        self.tblClientStatusActions.createPopupMenu([self.actClientStatusActionsCheckedAllRow, self.actClientStatusActionsClearCheckedAllRow, self.actStatusActionsInsert])
        self.tblClientDiagnosticActions.createPopupMenu([self.actClientDiagnosticActionsCheckedAllRow, self.actClientDiagnosticActionsClearCheckedAllRow, self.actDiagnosticActionsInsert])
        self.txtClientInfoBrowser.actions.append(self.actShowAttachedToClientFiles)
        self.txtClientInfoBrowser.actions.append(self.actEditClient)
        self.tblVaccinations.setItemDelegateForColumn(self.modelVaccinations.Col_VaccinationType, CVaccinationTypeDelegate(self.tblVaccinations))
        self.tblClientVaccinations.setItemDelegateForColumn(self.modelClientVaccinations.Col_VaccinationType, CVaccinationTypeDelegate(self.tblClientVaccinations))
        self.tblStatusActions.setItemDelegateForColumn(self.modelStatusActions.Col_Result, CStrComboBoxItemDelegate(self.tblStatusActions, propertyDescr=u'ME:examination_result'))
        self.tblLabDiagnosticActions.setItemDelegateForColumn(self.modelLabDiagnosticActions.Col_Result, CStrComboBoxItemDelegate(self.tblLabDiagnosticActions, propertyDescr=u'ME:laboratory_result'))
        self.tblToolDiagnosticActions.setItemDelegateForColumn(self.modelToolDiagnosticActions.Col_Result, CStrComboBoxItemDelegate(self.tblToolDiagnosticActions, propertyDescr=u'ME:instrumental_result'))
        self.cmbHurtType.setTable('rbHurtType') #setTable('rbHurtType', filter='code > 182 AND code < 216')
        self.cmbMKBFromClientDiseasesFilter.connect(self.cmbMKBFromClientDiseasesFilter._lineEdit, SIGNAL('editingFinished()'), self.on_cmbMKBFromClientDiseasesFilter_editingFinished)
        self.cmbMKBToClientDiseasesFilter.connect(self.cmbMKBToClientDiseasesFilter._lineEdit, SIGNAL('editingFinished()'), self.on_cmbMKBToClientDiseasesFilter_editingFinished)
        self.setupDirtyCather()
        self.contractTariffCache = CContractTariffCache()
        self.setIsDirty(False)
        self.tblExport.enableColsHide()
        self.tblExport.enableColsMove()
        self.actionTemplateCache = CActionTemplateCache(self, self.cmbPerson)
        self.modelMembersMSIPerson.setEventEditor(self)
        self.tabNotes.setEventEditor(self)
        self.modelInfectionDiseases.setEventEditor(self)
        self.modelClientDiseases.setEventEditor(self)
        self.modelVaccinations.setEventEditor(self)
        self.modelClientVaccinations.setEventEditor(self)
        self.modelStatusActions.setEventEditor(self)
        self.modelStatusActionProperties.setReadOnly(True)
        self.modelClientStatusActions.setEventEditor(self)
        self.modelClientStatusActionProperties.setReadOnly(True)
        self.modelLabDiagnosticActions.setEventEditor(self)
        self.modelToolDiagnosticActions.setEventEditor(self)
        self.modelDiagnosticActionProperties.setReadOnly(True)
        self.modelClientDiagnosticActionProperties.setReadOnly(True)
        self.modelClientDiagnosticActions.setEventEditor(self)
        self.tblInspectionsResult.setDelRowsIsExposed(lambda rowsExp: not any(map(self.modelDiagnostics.isExposed, rowsExp)))
        self.tblMembersMSIPerson.addPopupDelRow()
        self.tblInfectionDiseases.addPopupDelRow()
        self.tblVaccinations.addPopupDelRow()
        self.tblStatusActions.addPopupDelRow()
        self.tblLabDiagnosticActions.addPopupDelRow()
        self.tblToolDiagnosticActions.addPopupDelRow()
        self.installEventFilter(self)
        self.edtElectronicMedicalBookNumber.installEventFilter(self)
        self.edtElectronicMedicalBookNumber.setCursorPosition(0)
        self.getDiagnosisTypeId()
        self.on_clientDiseasesFilter_reset()
        self.on_clientVaccinationsFilter_reset()
        self.on_clientStatusActionsFilter_reset()
        self.on_diagnosticActionsFilter_reset()
        self.setMKBClientDiseasesFilterReadOnly()
        diagnosisTypeIdColIndex = self.modelDiagnostics.getColIndex('diagnosisType_id', None)
        if diagnosisTypeIdColIndex >= 0:
            self.modelDiagnostics._cols[diagnosisTypeIdColIndex].setDefaultHidden(True)
            self.tblInspectionsResult.horizontalHeader().setSectionHidden(diagnosisTypeIdColIndex, True)
        serviceIdColIndex = self.modelDiagnostics.getColIndex('service_id', None)
        if serviceIdColIndex >= 0:
            self.modelDiagnostics._cols[serviceIdColIndex].setDefaultHidden(True)
            self.tblInspectionsResult.horizontalHeader().setSectionHidden(serviceIdColIndex, True)
#        healthGroupIdColIndex = self.modelDiagnostics.getColIndex('healthGroup_id', None)
#        if healthGroupIdColIndex >= 0:
#            self.modelDiagnostics._cols[healthGroupIdColIndex].setDefaultHidden(True)
#            self.tblInspectionsResult.horizontalHeader().setSectionHidden(healthGroupIdColIndex, True)
        exSubclassMKBColIndex = self.modelDiagnostics.getColIndex('exSubclassMKB', None)
        if exSubclassMKBColIndex >= 0:
            self.modelDiagnostics._cols[exSubclassMKBColIndex].setDefaultHidden(True)
            self.tblInspectionsResult.horizontalHeader().setSectionHidden(exSubclassMKBColIndex, True)
        TNMSColIndex = self.modelDiagnostics.getColIndex('TNMS', None)
        if TNMSColIndex >= 0:
            self.modelDiagnostics._cols[TNMSColIndex].setDefaultHidden(True)
            self.tblInspectionsResult.horizontalHeader().setSectionHidden(TNMSColIndex, True)
        morphologyMKBColIndex = self.modelDiagnostics.getColIndex('morphologyMKB', None)
        if morphologyMKBColIndex >= 0:
            self.modelDiagnostics._cols[morphologyMKBColIndex].setDefaultHidden(True)
            self.tblInspectionsResult.horizontalHeader().setSectionHidden(morphologyMKBColIndex, True)
        handleDiagnosisColIndex = self.modelDiagnostics.getColIndex('handleDiagnosis', None)
        if handleDiagnosisColIndex >= 0:
            self.modelDiagnostics._cols[handleDiagnosisColIndex].setDefaultHidden(True)
            self.tblInspectionsResult.horizontalHeader().setSectionHidden(handleDiagnosisColIndex, True)


    def getEventTypeId(self):
        return self.eventTypeId


    def getActionTypeServiceIdList(self, actionTypeId, financeId):
        key = (actionTypeId, financeId)
        result = self.mapActionTypeIdToServiceIdList.get(key, False)
        if result == False:
            db = QtGui.qApp.db
            table = db.table('ActionType_Service')
            result = db.getDistinctIdList(table,
                                          idCol='service_id',
                                          where=[table['master_id'].eq(actionTypeId),
                                                 table['finance_id'].eq(financeId),
                                                 table['service_id'].isNotNull()])
            if not result:
                result = db.getDistinctIdList(table,
                                          idCol='service_id',
                                          where=[table['master_id'].eq(actionTypeId),
                                                 table['finance_id'].isNull(),
                                                 table['service_id'].isNotNull()])
            self.mapActionTypeIdToServiceIdList[key] = result
        return result


    def getPersonTariffCategoryId(self, personId):
        return self.getPersonSSF(personId)[3]


    def getUet(self, actionTypeId, personId, financeId, contractId, eventSetDateTime):
        if not contractId:
            contractId = self.tabNotes.getContractId()
            financeId = self.tabNotes.eventFinanceId
        if contractId and actionTypeId:
            self.contractTariffCache = CContractTariffCache()
            serviceIdList = self.getActionTypeServiceIdList(actionTypeId, financeId)
            tariffCategoryId = self.getPersonTariffCategoryId(personId)
            tariffDescr = self.contractTariffCache.getTariffDate(contractId, self, eventSetDateTime, financeId)
            uet = CContractTariffCache.getUetToDate(tariffDescr.dateTariffMap, serviceIdList, tariffCategoryId, eventSetDateTime.date()) #, self.tabNotes.clientSex, self.tabNotes.clientAge)
            return uet
        return 0


    def getActionDefaultContractId(self, actionTypeId, financeId, begDate, endDate, contractId, eventTypeId):
        model = CContractDbModel(None)
        try:
            model.setOrgId(self.tabNotes.orgId)
            model.setEventTypeId(eventTypeId)
            model.setClientInfo(self.clientId,
                                self.tabNotes.clientSex,
                                self.tabNotes.clientAge,
                                self.tabNotes.clientWorkOrgId,
                                self.tabNotes.clientPolicyInfoList)
            model.setFinanceId(financeId)
            model.setActionTypeId(actionTypeId)
            model.setBegDate(begDate or QDate.currentDate())
            model.setEndDate(endDate or QDate.currentDate())
            model.initDbData()
            return contractId if contractId and model.searchId(contractId)>=0 else model.getId(0)
        finally:
            pass


    def updateInspectionsResultVisits(self, eventId):
        db = QtGui.qApp.db
        finishDiagnosisTypeId = self.modelDiagnostics.diagnosisTypeCol.ids[0]
        baseDiagnosisTypeId = self.modelDiagnostics.diagnosisTypeCol.ids[1]
        table = db.table('Visit')
        eventVisitFinance = False
        if self.eventTypeId:
            tableEventType = db.table('EventType')
            recordEventType = db.getRecordEx(tableEventType, [tableEventType['visitFinance'], tableEventType['finance_id']], [tableEventType['visitFinance'].eq(0), tableEventType['deleted'].eq(0), tableEventType['id'].eq(self.eventTypeId)])
            if recordEventType:
                eventVisitFinance = not forceBool(recordEventType.value('visitFinance'))
        diagnostics  = self.modelDiagnostics.items()
        visitIdList  = []
        for diagnostic in diagnostics:
            diagnosisTypeId = forceRef(diagnostic.value('diagnosisType_id'))
            if diagnosisTypeId == finishDiagnosisTypeId or diagnosisTypeId == baseDiagnosisTypeId:
                endDate = forceDate(diagnostic.value('endDate'))
                if not endDate:
                   endDate = forceDate(diagnostic.value('setDate'))
                sceneId      = forceRef(diagnostic.value('scene_id'))
                visitTypeId  = forceRef(diagnostic.value('visitType_id'))
                visitServiceId  = forceRef(diagnostic.value('service_id'))
                personId     = forceRef(diagnostic.value('person_id'))
                if endDate and personId and visitTypeId and sceneId:
                    financeId = None
                    if not eventVisitFinance:
                        financeId = forceRef(db.translate('Person', 'id', personId, 'finance_id'))
                    if not financeId:
                        financeId = forceRef(db.translate('Contract', 'id', self.tabNotes.cmbContract.value(), 'finance_id'))
                    visitId = forceRef(diagnostic.value('visit_id'))
                    if visitId:
                        record = db.getRecordEx(table, '*', [table['id'].eq(visitId), table['deleted'].eq(0)])
                    else:
                        record = table.newRecord()
                    record.setValue('event_id',     toVariant(eventId))
                    record.setValue('scene_id',     toVariant(sceneId))
                    record.setValue('date',         toVariant(endDate))
                    record.setValue('visitType_id', toVariant(visitTypeId))
                    record.setValue('person_id',    toVariant(personId))
                    record.setValue('isPrimary',    toVariant(0))
                    record.setValue('finance_id',   toVariant(financeId))
                    record.setValue('service_id',   toVariant(visitServiceId))
##                        record.setValue('payStatus',    toVariant(0))
                    visitId = db.insertOrUpdate(table, record)
                    visitIdList.append(visitId)
                    diagnostic.setValue('visit_id', toVariant(visitId))
        cond = [table['event_id'].eq(eventId)]
        if visitIdList:
            cond.append(table['id'].notInlist(visitIdList))
        tableAccountItem = db.table('Account_Item')
        cond.append(db.notExistsStmt(tableAccountItem, tableAccountItem['visit_id'].eq(table['id'])))
        db.deleteRecord(table, where=cond)


    def newDiagnosticRecord(self, template, boolSetRecord = True):
        finishDiagnosisTypeId, baseDiagnosisTypeId, accompDiagnosisTypeId = self.modelDiagnostics.diagnosisTypeCol.ids
        result = self.tblInspectionsResult.model().getEmptyRecord()
        result.setValue('speciality_id',  template.value('speciality_id'))
        result.setValue('post_id',  template.value('post_id'))
        if boolSetRecord:
            result.setValue('diagnosisType_id',  template.value('diagnosisType_id'))
        else:
            specialityId = forceRef(template.value('speciality_id'))
            mayEngageGP  = forceBool(template.value('mayEngageGP'))
            if (self.personSpecialityId == specialityId
                or mayEngageGP and self.personSpecialityId == QtGui.qApp.getGPSpecialityId()
               ):
                if any( forceInt(item.value('diagnosisType_id')) == finishDiagnosisTypeId
                        for item in self.modelDiagnostics.items()
                      ):
                    diagnosisTypeId = baseDiagnosisTypeId
                else:
                    diagnosisTypeId = finishDiagnosisTypeId
                result.setValue('person_id', QVariant(self.personId))
                result.setValue('diagnosisType_id', QVariant(diagnosisTypeId))
            else:
                result.setValue('diagnosisType_id', QVariant(baseDiagnosisTypeId))
                result.setValue('person_id', QVariant(template.value('person_id')))
        result.setValue('setDate',        QVariant(self.eventSetDateTime))
        if forceDate(template.value('endDate')):
            result.setValue('endDate', QVariant(template.value('endDate')))
        result.setValue('healthGroup_id', template.value('defaultHealthGroup_id'))
        result.setValue('dispanser_id',   template.value('defaultDispanser_id'))
        result.setValue('MKB',            template.value('defaultMKB'))
        result.setValue('defaultMKB',     template.value('defaultMKB'))
        result.setValue('actuality',      template.value('actuality'))
        result.setValue('visitType_id',   template.value('visitType_id'))
        if forceInt(template.value('scene_id')):
            sceneId = template.value('scene_id')
        else:
            sceneId = getEventSceneId(self.eventTypeId)
        result.setValue('scene_id',       toVariant(sceneId) if sceneId else QtGui.qApp.db.translate('rbScene', 'code',  '1', 'id'))
        result.setValue('service_id', template.value('service_id'))
        result.setValue('selectionGroup', template.value('selectionGroup'))
        result.setValue('payStatus',      CPayStatus.initial)
        return result


    def recordAcceptable(self, record):
        return recordAcceptable(self.clientSex, self.clientAge, record, forceDate(self.eventSetDateTime), self.clientBirthDate) and self.recordAcceptableByClientHurt(record)


    def recordAcceptableByClientHurt(self, record):
        resultWH  = True
        resultWHF = True
        listForChecking = self._getHurtListForChecking(record, 'hurtType')
        if listForChecking:
            if QtGui.qApp.checkGlobalPreference(u'workHurtsTypeVisible', u'да', u'нет'):
                resultWH  = False
                if self.clientWorkHurtCodeList:
                    resultWH = bool(set(self.clientWorkHurtCodeList) & set(listForChecking))
            else:
                resultWH = False
        elif QtGui.qApp.checkGlobalPreference(u'workHurtsTypeVisible', u'нет', u'нет'):
            resultWH = False
        listForChecking = self._getHurtListForChecking(record, 'hurtFactorType')
        if listForChecking:
            resultWHF = False
            if self.clientWorkHurtFactorCodeList:
                resultWHF = bool(set(self.clientWorkHurtFactorCodeList) & set(listForChecking))
        return resultWH or resultWHF


    def _getHurtListForChecking(self, record, fieldName):
        value = forceString(record.value(fieldName))
        result = [trim(val) for val in value.split(';') if val]
        return result


    def setClientWorkHurtCodeList(self, clientId):
        db = QtGui.qApp.db
        tableCW       = db.table('ClientWork')
        tableCWH      = db.table('ClientWork_Hurt')
        tableHurtType = db.table('rbHurtType')
        queryTable = tableCW.leftJoin(tableCWH, tableCWH['master_id'].eq(tableCW['id']))
        queryTable = queryTable.leftJoin(tableHurtType, tableHurtType['id'].eq(tableCWH['hurtType_id']))
        cond = [tableCW['client_id'].eq(clientId), tableCW['deleted'].eq(0)]
        fieldList = tableHurtType['code'].name()
        recordList = db.getRecordList(queryTable, fieldList, cond)
        for record in recordList:
            self.clientWorkHurtCodeList.append(forceString(record.value('code')))


    def setClientWorkHurtFactorCodeList(self, clientId, hurtIdList=[]):
        db = QtGui.qApp.db
        tableCW             = db.table('ClientWork')
        tableCWHF           = db.table('ClientWork_Hurt_Factor')
        tableHurtFactorType = db.table('rbHurtFactorType')
        if hurtIdList:
            queryTable = tableCWHF.leftJoin(tableHurtFactorType, tableHurtFactorType['id'].eq(tableCWHF['factorType_id']))
            cond = tableCWHF['master_id'].inlist(hurtIdList)
        else:
            queryTable = tableCW.leftJoin(tableCWHF, tableCWHF['master_id'].eq(tableCW['id']))
            queryTable = queryTable.leftJoin(tableHurtFactorType, tableHurtFactorType['id'].eq(tableCWHF['factorType_id']))
            cond = [tableCW['client_id'].eq(clientId), tableCW['deleted'].eq(0)]
        recordList = db.getRecordList(queryTable, tableHurtFactorType['code'].name(), cond)
        for record in recordList:
            self.clientWorkHurtFactorCodeList.append(forceString(record.value('code')))


    def createDiagnostics(self, eventId):
        if eventId:
            self.loadDiagnostics([], eventId)


    def prepareDiagnostics(self, diagnostics, addVisit = False):
        for record in diagnostics:
            if forceInt(record.value('include')) != 0 or addVisit:
                self.modelDiagnostics.items().append(self.newDiagnosticRecord(record, False))
        self.modelDiagnostics.reset()


    def loadDiagnostics(self, diagnostics, eventId):
        def selectionGroup(i):
            return forceInt(diagnostics[i].value('selectionGroup'))

        def getDiagnosisType(diagnosisTypeId):
            if diagnosisTypeId in self.modelDiagnostics.diagnosisTypeCol.ids:
                return self.modelDiagnostics.diagnosisTypeCol.ids.index(diagnosisTypeId)
            else:
                return 2

        db = QtGui.qApp.db
        table = db.table('Diagnostic')
        tableVisit  = db.table('Visit')
        tablePerson = db.table('Person')
        isDiagnosisManualSwitch = self.modelDiagnostics.manualSwitchDiagnosis()
        joinVisitPerson = tableVisit.leftJoin(tablePerson, tablePerson['id'].eq(tableVisit['person_id']))
        rawItems = db.getRecordList(table, '*', [table['deleted'].eq(0), table['event_id'].eq(eventId), table['diagnosisType_id'].ne(self.modelInfectionDiseases.diagnosisTypeId)], 'id')
        rawSorted = [[]]
        for record in rawItems:
            diagnosisTypeId = record.value('diagnosisType_id')
            diagnosisId     = record.value('diagnosis_id')
            MKB             = db.translate('Diagnosis', 'id', forceRef(diagnosisId), 'MKB')
            exSubclassMKB   = db.translate('Diagnosis', 'id', forceRef(diagnosisId), 'exSubclassMKB')
            morphologyMKB   = db.translate('Diagnosis', 'id', forceRef(diagnosisId), 'morphologyMKB')
            setDate         = forceDate(record.value('setDate'))
            newRecord = self.modelDiagnostics.getEmptyRecord()
            copyFields(newRecord, record)
            newRecord.setValue('diagnosisTypeId', diagnosisTypeId)
            if MKB:
                newRecord.setValue('MKB', MKB)
            if morphologyMKB:
                newRecord.setValue('morphologyMKB', morphologyMKB)
            newRecord.setValue('exSubclassMKB', exSubclassMKB)
            self.modelDiagnostics.updateMKBTNMS(newRecord, MKB)
            self.modelDiagnostics.updateMKBToExSubclass(newRecord, MKB)
            newRecord.setValue('defaultMKB', MKB)
            newRecord.setValue('actuality',  toVariant(1))
            newRecord.setValue('payStatus',  CPayStatus.initial)

            currentEventId = self.eventId
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

            rawSorted[0].append(newRecord)

        # восстанавливаем тип диагноза (если он утрачен), устанавливаем ссылки на визиты и статусы оплаты
        finishDiagnosisTypeId, baseDiagnosisTypeId, accompDiagnosisTypeId = self.modelDiagnostics.diagnosisTypeCol.ids
        visitIdListRecord = []
        dfSceneId = getEventSceneId(self.eventTypeId)
        for group in rawSorted:
            for i, record in enumerate(group):
                diagnosisTypeId = forceRef(record.value('diagnosisType_id'))
                if i == 0 and diagnosisTypeId == accompDiagnosisTypeId:
                    diagnosisTypeId = baseDiagnosisTypeId
                    record.setValue('diagnosisType_id', toVariant(diagnosisTypeId))
                if diagnosisTypeId in (finishDiagnosisTypeId, baseDiagnosisTypeId):
                    visitCond = [tableVisit['event_id'].eq(self.eventId),
                                       tableVisit['deleted'].eq(0),
                                 tableVisit['person_id'].eq(record.value('person_id'))
                                # tablePerson['speciality_id'].eq(record.value('speciality_id'))
                                 ]
                    if visitIdListRecord:
                        visitCond.append(tableVisit['id'].notInlist(visitIdListRecord))
                    visitIdList = db.getIdList(joinVisitPerson, tableVisit['id'].name(), where=visitCond, order=tableVisit['id'].name())
                    visitId = visitIdList[0] if visitIdList else None
                    if visitId and visitId not in visitIdListRecord:
                        visitIdListRecord.append(visitId)

                    endDate = forceDate(record.value('endDate'))
                    if visitId:
                        sceneId = forceRef(db.translate(tableVisit, 'id', visitId, 'scene_id'))
                        visitTypeId = forceRef(db.translate(tableVisit, 'id', visitId, 'visitType_id'))
                        visitServiceId = forceRef(db.translate(tableVisit, 'id', visitId, 'service_id'))
                        payStatus = getWorstPayStatus(forceInt(db.translate(tableVisit, 'id', visitId, 'payStatus')))

                        record.setValue('visit_id',      toVariant(visitId))
                        record.setValue('scene_id',      toVariant(sceneId))
                        record.setValue('visitType_id',  toVariant(visitTypeId))
                        record.setValue('service_id', toVariant(visitServiceId))
                        record.setValue('payStatus',     toVariant(payStatus))
                    if not endDate and not visitId and i < len(diagnostics):
                        sceneId = forceRef(diagnostics[i].value('scene_id'))
                        if not sceneId:
                            sceneId = dfSceneId if dfSceneId else forceRef(QtGui.qApp.db.translate('rbScene', 'code',  '1', 'id'))
                            record.setValue('scene_id', toVariant(sceneId))
                        visitTypeId = forceRef(diagnostics[i].value('visitType_id'))
                sceneId = forceRef(record.value('scene_id'))
                if not sceneId:
                    record.setValue('scene_id', toVariant(dfSceneId) if dfSceneId else QtGui.qApp.db.translate('rbScene', 'code',  '1', 'id'))

        # объединяем в один список
        items = []
        for group in rawSorted:
            for item in group:
                item._dirty = False
                items.append(item)
        # и устанавливаем в модель:
        self.modelDiagnostics.setItems(items)


    def getPersonSSF(self, personId):
        key = personId, self.tabNotes.clientType
        result = self.personSSFCache.get(key, None)
        if not result:
            record = QtGui.qApp.db.getRecord('Person LEFT JOIN rbSpeciality ON rbSpeciality.id = Person.speciality_id',
                                             'speciality_id, service_id, provinceService_id, otherService_id, finance_id, tariffCategory_id',
                                             personId
                                             )
            if record:
                specialityId = forceRef(record.value('speciality_id'))
                serviceId = forceRef(record.value('service_id'))
                provinceServiceId = forceRef(record.value('provinceService_id'))
                otherServiceId = forceRef(record.value('otherService_id'))
                financeId = forceRef(record.value('finance_id'))
                tariffCategoryId = forceRef(record.value('tariffCategory_id'))
                if self.tabNotes.clientType == CEventEditDialog.ctOther and otherServiceId:
                    serviceId = otherServiceId
                elif self.tabNotes.clientType == CEventEditDialog.ctProvince and provinceServiceId:
                    serviceId = provinceServiceId
                result = (specialityId, serviceId, financeId, tariffCategoryId)
            else:
                result = (None, None, None, None)
            self.personSSFCache[key] = result
        return result


    def getPersonFinanceId(self, personId):
        return self.getPersonSSF(personId)[2]


    def getActionFinanceId(self, actionRecord, eventTypeId):
        finance = getEventActionFinance(eventTypeId)
        if finance == 1:
            return self.tabNotes.eventFinanceId
        elif finance == 2:
            personId = forceRef(actionRecord.value('setPerson_id'))
            personSpecialityId, personServiceId, personFinanceId, personTariffCategoryId = self.getPersonSSF(personId)
            return self.getPersonFinanceId(personId) if personId else personFinanceId
        elif finance == 3:
            personId = forceRef(actionRecord.value('person_id'))
            personSpecialityId, personServiceId, personFinanceId, personTariffCategoryId = self.getPersonSSF(personId)
            return self.getPersonFinanceId(personId) if personId else personFinanceId
        else:
            return None


    def getActionDuration(self, eventTypeId, record, weekProfile):
        if record:
            startDate = forceDate(record.value('begDate'))
            stopDate  = forceDate(record.value('endDate'))
            if startDate and stopDate:
                return getEventDuration(startDate, stopDate, weekProfile, eventTypeId)
        return 0


    def getEventDuration(self, weekProfile, eventSetDateTime, eventDate, eventTypeId):
        startDate = eventSetDateTime.date() if eventSetDateTime else QDate.currentDate()
        stopDate = eventDate if eventDate else QDate.currentDate()
        return getEventDuration(startDate, stopDate, weekProfile, eventTypeId)


    def getVisitCount(self):
        return 1


    def getActionDefaultAmountEx(self, actionType, record, action, eventSetDateTime, eventDate, eventTypeId):
        result = actionType.amount
        if actionType.amountEvaluation == CActionType.eventVisitCount:
            result = result * self.getVisitCount()
        elif actionType.amountEvaluation == CActionType.eventDurationWithFiveDayWorking:
            result = result * self.getEventDuration(wpFiveDays, eventSetDateTime, eventDate, eventTypeId)
        elif actionType.amountEvaluation == CActionType.eventDurationWithSixDayWorking:
            result = result * self.getEventDuration(wpSixDays, eventSetDateTime, eventDate, eventTypeId)
        elif actionType.amountEvaluation == CActionType.eventDurationWithSevenDayWorking:
            result = result * self.getEventDuration(wpSevenDays, eventSetDateTime, eventDate, eventTypeId)
        elif actionType.amountEvaluation == CActionType.actionDurationWithFiveDayWorking:
            result = result * self.getActionDuration(eventTypeId, record, wpFiveDays)
        elif actionType.amountEvaluation == CActionType.actionDurationWithSixDayWorking:
            result = result * self.getActionDuration(eventTypeId, record, wpSixDays)
        elif actionType.amountEvaluation == CActionType.actionDurationWithSevenDayWorking:
            result = result * self.getActionDuration(eventTypeId, record, wpSevenDays)
        elif actionType.amountEvaluation == CActionType.actionFilledPropsCount:
            result = result * action.getFilledPropertiesCount() if action else 0
        elif actionType.amountEvaluation == CActionType.actionAssignedPropsCount:
            result = result * action.getAssignedPropertiesCount() if action else 0
        return result


    def preFillingActionRecord090(self, eventRecord, record, actionTypeId, amount, financeId, contractId, orgStructureId=None):
        orgStructureId = orgStructureId
        if actionTypeId:
            actionType = CActionTypeCache.getById(actionTypeId)
            defaultStatus = actionType.defaultStatus
            defaultDirectionDate = actionType.defaultDirectionDate
            defaultBegDate = actionType.defaultBegDate
            defaultEndDate = actionType.defaultEndDate
            defaultSetPerson = actionType.defaultSetPersonInEvent
            defaultExecPersonId = actionType.defaultExecPersonId
            defaultPerson = actionType.defaultPersonInEvent
            defaultMKB = actionType.defaultMKB
            defaultOrgId = actionType.defaultOrgId
            office = actionType.office
            record.setValue('actionType_id', toVariant(actionTypeId))
            if actionType.isNomenclatureExpense and not orgStructureId:
                orgStructureId = actionType.getNomenclatureOrgStructureId()
        else:
            defaultStatus = CActionStatus.finished  # Закончено
            defaultDirectionDate = CActionType.dddUndefined
            defaultBegDate = 0
            defaultEndDate = CActionType.dedEventExecDate  # Дата события
            defaultSetPerson = 0
            defaultExecPersonId = None
            defaultPerson = CActionType.dpEmpty
            defaultMKB = None
            defaultOrgId = None
            office = ''
        if not orgStructureId:
            orgStructureId = QtGui.qApp.currentOrgStructureId()

        eventId = forceRef(eventRecord.value('id'))
        eventTypeId = forceRef(eventRecord.value('eventType_id'))
        eventContractId = forceRef(eventRecord.value('contract_id'))
        eventSetDateTime = forceDateTime(eventRecord.value('setDate'))
        eventDate = forceDate(eventRecord.value('execDate'))
        execDateTime = forceDateTime(eventRecord.value('execDate'))
        personId = forceRef(eventRecord.value('execPerson_id'))

        if defaultEndDate == CActionType.dedEventExecDate:
            endDate = forceDateTime(eventDate)
        elif defaultEndDate == CActionType.dedEventSetDate:
            endDate = eventSetDateTime
        elif defaultEndDate == CActionType.dedCurrentDate:
            endDate = QDateTime.currentDateTime()
        else:
            if defaultStatus in (CActionStatus.finished, CActionStatus.withoutResult):
                endDate = QDateTime.currentDateTime()
            else:
                endDate = QDateTime()

        if defaultSetPerson == CActionType.dspUndefined:
            setPersonId = QtGui.qApp.userId if QtGui.qApp.userSpecialityId else personId
        elif defaultSetPerson == CActionType.dspEventExecPerson:
            setPersonId = personId
        elif defaultSetPerson == CActionType.dspExecPerson:
            setPersonId = None

        begDate = eventSetDateTime
        if defaultDirectionDate == CActionType.dddEventSetDate:
            directionDate = eventSetDateTime
        elif defaultDirectionDate == CActionType.dddCurrentDate:
            directionDate = QDateTime.currentDateTime()
        elif defaultDirectionDate == CActionType.dddActionExecDate:
            if endDate:
                if endDate < eventSetDateTime:
                    directionDate = eventSetDateTime
                    begDate = QDateTime()
                else:
                    directionDate = begDate = endDate
            else:
                directionDate = eventSetDateTime
        elif defaultDirectionDate == CActionType.dddSyncEventBegDate:
            directionDate = eventSetDateTime
        elif defaultDirectionDate == CActionType.dddSyncEventEndDate:
            directionDate = execDateTime
        else:
            directionDate = eventSetDateTime

        if defaultBegDate in [CActionType.dbdEventExecDate, CActionType.dbdSyncEventEndDate]:
            begDate = execDateTime
        elif defaultBegDate in [CActionType.dbdEventSetDate, CActionType.dbdSyncEventBegDate]:
            begDate = eventSetDateTime
        elif defaultBegDate == CActionType.dbdCurrentDate:
            begDate = QDateTime.currentDateTime()

        if defaultEndDate in [CActionType.dedActionBegDate, CActionType.dedSyncActionBegDate]:
            endDate = max(begDate, directionDate)
        if defaultEndDate == CActionType.dedSyncEventEndDate:
            endDate = execDateTime

        if defaultExecPersonId:
            personId = defaultExecPersonId
        else:
            if defaultPerson == CActionType.dpCurrentMedUser:
                if QtGui.qApp.userSpecialityId:
                    personId = QtGui.qApp.userId
                else:
                    personId = None
            elif defaultPerson == CActionType.dpCurrentUser:
                personId = QtGui.qApp.userId
            elif defaultPerson == CActionType.dpEventExecPerson:
                personId = personId
            elif defaultPerson == CActionType.dpSetPerson:
                personId = setPersonId
            else:
                personId = None

        if defaultSetPerson == CActionType.dspExecPerson:
            setPersonId = personId

        if defaultBegDate == CActionType.dbdActionEndDate:
            begDate = max(endDate, directionDate)

        record.setValue('orgStructure_id', toVariant(orgStructureId))
        record.setValue('directionDate', toVariant(directionDate))
        record.setValue('setPerson_id', toVariant(setPersonId))
        record.setValue('begDate', toVariant(max(begDate, directionDate)))
        record.setValue('endDate', toVariant(endDate))
        record.setValue('status', toVariant(defaultStatus))
        record.setValue('office', toVariant(office))
        record.setValue('person_id', toVariant(personId))
        record.setValue('MKB', toVariant(defaultMKB))
        record.setValue('org_id', toVariant(defaultOrgId))
        if actionTypeId:
            if not (amount and actionType.amountEvaluation == CActionType.userInput):
                amount = self.getActionDefaultAmountEx(actionType, record, None, eventSetDateTime, eventDate, eventTypeId)
        else:
            amount = 0
        record.setValue('amount', toVariant(amount))
        if not financeId:
            financeId = self.getActionFinanceId(record, eventTypeId)
        if getEventActionContract(eventTypeId):
            contractId = self.getActionDefaultContractId(actionTypeId, financeId, begDate, endDate, contractId or eventContractId, eventTypeId)
        else:
            contractId = None
        record.setValue('uet', toVariant(amount * self.getUet(actionTypeId, personId, financeId, contractId, eventSetDateTime)))
        record.setValue('finance_id', toVariant(financeId))
        record.setValue('contract_id', toVariant(contractId))
        if eventId:
            record.setValue('event_id', toVariant(eventId))
        eventMedicalAidKindId = getEventMedicalAidKindId(eventTypeId)
        record.setValue('medicalAidKind_id', toVariant(eventMedicalAidKindId))
        return record


    def setIsDirty(self, dirty=True):
        CItemEditorBaseDialog.setIsDirty(self, dirty)
        if self.recordEvent:
            self.recordEvent._dirty = dirty


    def protectWidgetFromEdit(self, isProtected):
        isClosed = self.tabNotes.isEventClosed()
        self.isProtected = isProtected if isProtected else (isClosed and not QtGui.qApp.userHasRight(urEditClosedEvent))
        isEditable = not self.isProtected
        self.cmbHurtType.setReadOnly(self.isProtected)
#        self.chkEpidemicIndications.setReadOnly(self.isProtected)
        self.edtElectronicMedicalBookNumber.setReadOnly(self.isProtected)
        self.modelInfectionDiseases.setReadOnly(self.isProtected)
        self.modelVaccinations.setReadOnly(self.isProtected)
        self.modelStatusActions.setReadOnly(self.isProtected)
        self.modelLabDiagnosticActions.setReadOnly(self.isProtected)
        self.modelToolDiagnosticActions.setReadOnly(self.isProtected)
        self.modelMembersMSIPerson.setReadOnly(self.isProtected)
        self.modelDiagnostics.setReadOnly(self.isProtected)
        self.cmbInfoResult.setReadOnly(self.isProtected)
        self.edtVisitDateNextResult.setReadOnly(self.isProtected)
        self.edtCommentResult.setReadOnly(self.isProtected)
        self.modelExport.setReadOnly(self.isProtected)
        self.tabNotes.protectFromEdit(self.isProtected)
        self.buttonBox.button(QtGui.QDialogButtonBox.Save).setEnabled(isEditable)
        self.btnSelectOrg.setEnabled(isEditable)
        #self.btnAttachedFiles.setEnabled(isEditable)


    @pyqtSignature('')
    def on_tblClientDiseases_popupMenuAboutToShow(self):
        notEmpty = self.modelClientDiseases.hasChecked() and not self.isProtected
        self.actInfectionDiseasesInsert.setEnabled(notEmpty)
        self.actInfectionDiseasesCheckedAllRow.setEnabled(self.modelClientDiseases.hasNotChecked() and not self.isProtected)
        self.actInfectionDiseasesClearCheckedAllRow.setEnabled(notEmpty)


    @pyqtSignature('')
    def on_actEditClient_triggered(self):
        self.editClient(self.clientId)


    def editClient(self, clientId):
        if QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]):
            dialog = CClientEditDialog(self)
            try:
                if clientId:
                    dialog.load(clientId)
                if dialog.exec_():
                    dialog.itemId()
            finally:
                dialog.deleteLater()


    @pyqtSignature('')
    def on_actInfectionDiseasesInsert_triggered(self):
        checkedItems = self.modelClientDiseases.getCheckedItems()
        for checkedItem in checkedItems:
            checkedId = forceRef(checkedItem.value('id'))
            if checkedId and checkedId not in self.modelInfectionDiseases.checkedIdList:
                self.modelInfectionDiseases.checkedIdList.append(checkedId)
            record = self.modelInfectionDiseases.getEmptyRecord()
            for i in xrange(record.count()):
                record.setValue(i, checkedItem.value(record.fieldName(i)))
            record.setValue('checked_id', toVariant(checkedId))
            record.setValue('id', toVariant(None))
            record.setValue('diagnosis_id', toVariant(None))
            record.setValue('event_id', toVariant(self.eventId))
            record.setValue('diagnosisType_id', toVariant(self.modelInfectionDiseases.diagnosisTypeId))
            self.modelInfectionDiseases.addRecord(record)
        self.updateClientDiseases()
        self.setIsDirty()


    @pyqtSignature('')
    def on_actInfectionDiseasesCheckedAllRow_triggered(self):
        self.modelClientDiseases.selectAll()


    @pyqtSignature('')
    def on_actInfectionDiseasesClearCheckedAllRow_triggered(self):
        self.modelClientDiseases.deselectAll()


    @pyqtSignature('')
    def on_tblClientVaccinations_popupMenuAboutToShow(self):
        notEmpty = self.modelClientVaccinations.hasChecked() and not self.isProtected
        self.actVaccinationsInsert.setEnabled(notEmpty)
        self.actClientVaccinationsCheckedAllRow.setEnabled(self.modelClientVaccinations.hasNotChecked() and not self.isProtected)
        self.actClientVaccinationsClearCheckedAllRow.setEnabled(notEmpty)


    @pyqtSignature('')
    def on_actVaccinationsInsert_triggered(self):
        checkedItems = self.modelClientVaccinations.getCheckedItems()
        for checkedItem in checkedItems:
            checkedId = forceRef(checkedItem.value('clientVaccination_id'))
            if checkedId and checkedId not in self.modelVaccinations.checkedIdList:
                self.modelVaccinations.checkedIdList.append(checkedId)
            record = self.modelVaccinations.getEmptyRecord()
            for i in xrange(record.count()):
                record.setValue(i, checkedItem.value(record.fieldName(i)))
            record.setValue('checked_id', toVariant(checkedId))
#            record.setValue('infection_id', checkedItem.value('infection_id'))
#            record.setValue('date', checkedItem.value('date'))
#            record.setValue('vaccinationType', checkedItem.value('vaccinationType'))
            record.setValue('id', toVariant(None))
            record.setValue('master_id', toVariant(self.itemId()))
            self.modelVaccinations.addRecord(record)
        self.updateClientVaccinations()
        self.setIsDirty()


    @pyqtSignature('')
    def on_actClientVaccinationsCheckedAllRow_triggered(self):
        self.modelClientVaccinations.selectAll()


    @pyqtSignature('')
    def on_actClientVaccinationsClearCheckedAllRow_triggered(self):
        self.modelClientVaccinations.deselectAll()


    @pyqtSignature('')
    def on_tblClientStatusActions_popupMenuAboutToShow(self):
        notEmpty = self.modelClientStatusActions.hasChecked() and not self.isProtected
        self.actStatusActionsInsert.setEnabled(notEmpty)
        self.actClientStatusActionsCheckedAllRow.setEnabled(self.modelClientStatusActions.hasNotChecked() and not self.isProtected)
        self.actClientStatusActionsClearCheckedAllRow.setEnabled(notEmpty)


    @pyqtSignature('')
    def on_actStatusActionsInsert_triggered(self):
        db = QtGui.qApp.db
        tablePerson = db.table('Person')
        checkedItems = self.modelClientStatusActions.getCheckedItems()
        for checkedItem in checkedItems:
            checkedId = forceRef(checkedItem.value('id'))
            if checkedId and checkedId not in self.modelStatusActions.checkedIdList:
                self.modelStatusActions.checkedIdList.append(checkedId)
            record = self.modelStatusActions.getEmptyRecord()
#            for i in xrange(record.count()):
#                record.setValue(i, checkedItem.value(record.fieldName(i)))
            postId = forceRef(checkedItem.value('post_id'))
            record.setValue('checked_id', toVariant(checkedId))
            record.setValue('post_id', toVariant(postId))
            record.setValue('examination_id', toVariant(checkedId))
            record.setValue('date', checkedItem.value('endDate'))
            record.setValue('id', toVariant(None))
            record.setValue('master_id', toVariant(self.itemId()))
            personId = forceRef(checkedItem.value('person_id'))
            if personId:
                personRecord = db.getRecordEx(tablePerson, '*', [tablePerson['id'].eq(personId), tablePerson['deleted'].eq(0)])
                if personRecord:
                    record.setValue('lastName', personRecord.value('lastName'))
                    record.setValue('firstName', personRecord.value('firstName'))
                    record.setValue('patrName', personRecord.value('patrName'))
            record.setValue('person_id', toVariant(personId))
            isComissioner = 0
            if personId and postId and len(self.modelMembersMSIPerson._items) < len(self.modelMembersMSIPerson.descrList) and personId not in self.modelMembersMSIPerson.getItemIdList():
                isComissioner = 1
                recordMembersMSIPerson = self.modelMembersMSIPerson.getEmptyRecord()
                recordMembersMSIPerson.setValue('id', toVariant(personId))
                self.modelMembersMSIPerson.addRecord(recordMembersMSIPerson)
            elif personId and postId and personId in self.modelMembersMSIPerson.getItemIdList():
                isComissioner = 1
            record.setValue('isComissioner', toVariant(isComissioner))
            self.modelStatusActions.addRecord(record)
        self.updateClientStatusActions()
        self.setIsDirty()


    @pyqtSignature('')
    def on_actClientStatusActionsCheckedAllRow_triggered(self):
        self.modelClientStatusActions.selectAll()


    @pyqtSignature('')
    def on_actClientStatusActionsClearCheckedAllRow_triggered(self):
        self.modelClientStatusActions.deselectAll()


    @pyqtSignature('')
    def on_tblClientDiagnosticActions_popupMenuAboutToShow(self):
        notEmpty = self.modelClientDiagnosticActions.hasChecked() and not self.isProtected
        self.actDiagnosticActionsInsert.setEnabled(notEmpty)
        self.actClientDiagnosticActionsCheckedAllRow.setEnabled(self.modelClientDiagnosticActions.hasNotChecked() and not self.isProtected)
        self.actClientDiagnosticActionsClearCheckedAllRow.setEnabled(notEmpty)


    @pyqtSignature('')
    def on_actDiagnosticActionsInsert_triggered(self):
        checkedItems = self.modelClientDiagnosticActions.getCheckedItems()
        for checkedItem in checkedItems:
            checkedId = forceRef(checkedItem.value('id'))
            researchType = forceInt(checkedItem.value('researchType'))
            if researchType == 2:
                model = self.modelToolDiagnosticActions
            else:
                model = self.modelLabDiagnosticActions
            if checkedId and checkedId not in model.checkedIdList:
                model.checkedIdList.append(checkedId)
            record = model.getEmptyRecord()
            for i in xrange(record.count()):
                if record.fieldName(i) != u'result':
                    record.setValue(i, checkedItem.value(record.fieldName(i)))

            serviceId = forceRef(checkedItem.value('nomenclativeService_id'))
            serviceIdent = self.nomenclativeServiceMap.get(serviceId)
            newServiceId = self.serviceMap.get(serviceIdent)
            record.setValue('checked_id', toVariant(checkedId))
            record.setValue('research_id', toVariant(checkedId))
            record.setValue('id', toVariant(None))
            record.setValue('date', toVariant(checkedItem.value('endDate')))
            record.setValue('service_id', toVariant(newServiceId))
            record.setValue('researchType', toVariant(researchType))
            record.setValue('master_id', toVariant(self.itemId()))
            model.addRecord(record)
        self.updateDiagnosticActions()
        self.setIsDirty()


    @pyqtSignature('')
    def on_actClientDiagnosticActionsCheckedAllRow_triggered(self):
        self.modelClientDiagnosticActions.selectAll()


    @pyqtSignature('')
    def on_actClientDiagnosticActionsClearCheckedAllRow_triggered(self):
        self.modelClientDiagnosticActions.deselectAll()


    def getActionTypeIdListByELMK(self, flatCode = u'%medical_examination'):
        return getActionTypeIdListByFlatCode(flatCode)


    def getHurtTypeSetTable(self, action):
        tableName = u'rbHurtType'
        self.hurtTypeTableName = tableName
        self.hurtTypeCond = []
        if action:
            for propertyTypeName, propertyType in action.getType()._propertiesByName.items():
                descr = trim(propertyType.descr)
                if descr == u'ME:work':
                    value = forceRef(action[propertyTypeName])
                    valueDomain = trim(propertyType.valueDomain)
                    cond = u''
                    if valueDomain:
                        valueDomainList = valueDomain.split(u';')
                        if len(valueDomainList) >= 1:
                            domain = trim(valueDomainList[0])
                            if ' WHERE ' in domain:
                                tableName, cond = domain.split(' WHERE ')[:2]
                            self.cmbHurtType.setTable(tableName.strip(), filter=cond)
                            self.cmbHurtType.setValue(value)
                            self.hurtTypeTableName = tableName.strip()
                            self.hurtTypeCond = cond
                            return
                    if ' WHERE ' in valueDomain:
                        tableName, cond = valueDomain.split(' WHERE ')[:2]
                        self.cmbHurtType.setTable(tableName.strip(), filter=cond)
                        self.cmbHurtType.setValue(value)
                        self.hurtTypeTableName = tableName.strip()
                        self.hurtTypeCond = cond
                        return
                    self.cmbHurtType.setTable(tableName.strip())
                    self.cmbHurtType.setValue(value)
                    return


    # tabMainInformation
    @pyqtSignature('int')
    def on_cmbHurtType_currentIndexChanged(self, value):
        hurtTypeId = self.cmbHurtType.value()
#        self.chkEpidemicIndications.setEnabled(bool(hurtTypeId))
        self.setProperty(QVariant(hurtTypeId), u'ME:work')
        self.getInfectionVaccinations()
        self.getPostIdList()
        self.getNomenclativeServiceIdList()


#    @pyqtSignature('bool')
#    def on_chkEpidemicIndications_toggled(self, checked):
#        self.setProperty(QVariant(self.chkEpidemicIndications.isChecked()), u'ME:epidemic_indications')
#        self.getInfectionVaccinations()
#        self.getPostIdList()
#        self.getNomenclativeServiceIdList()


    @pyqtSignature('QString')
    def on_edtElectronicMedicalBookNumber_textChanged(self, text):
        self.setProperty(QVariant(self.edtElectronicMedicalBookNumber.text()), u'ME:medical_book_number')


    # tabResult
    @pyqtSignature('int')
    def on_cmbInfoResult_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbInfoResult.value()), u'ME:conclusion')


    @pyqtSignature('QDate')
    def on_edtVisitDateNextResult_dateChanged(self, date):
        self.setProperty(QVariant(self.edtVisitDateNextResult.date()), u'ME:next_medical_examination_date')


    @pyqtSignature('QString')
    def on_edtCommentResult_textChanged(self, text):
        self.setProperty(QVariant(self.edtCommentResult.toPlainText()), u'ME:comment')


    def prepareActionTable(self, tbl, *actions):
        tbl.setEditTriggers(QtGui.QAbstractItemView.SelectedClicked | QtGui.QAbstractItemView.DoubleClicked)
        tbl.model().setReadOnly(True)
        tbl.addPopupCopyCell()
        tbl.addPopupSeparator()
        for action in actions:
            if action == '-':
                tbl.addPopupSeparator()
            else:
                tbl.addPopupAction(action)


    def initNewDate(self):
        if self.isCreate:
            self.edtVisitDateNextResult.setDate(QDate())


    def initNewData(self):
        if self.isCreate:
            self.on_cmbInfoResult_currentIndexChanged(0)


    def eventFilter(self, watched, event):
        if watched == self.edtElectronicMedicalBookNumber:
            if event.type() == QEvent.MouseButtonPress:
                event.accept()
                maskLen = len(trim(self.edtElectronicMedicalBookNumber.inputMask())) - 1
                curPos = self.edtElectronicMedicalBookNumber.cursorPositionAt(event.pos())
                pos = len(trim(self.edtElectronicMedicalBookNumber.text()))
                if not pos or curPos == maskLen:
                    self.edtElectronicMedicalBookNumber.setCursorPosition(0)
                    return True
                elif curPos > pos:
                    self.edtElectronicMedicalBookNumber.setCursorPosition(pos)
                    return True
        return CItemEditorBaseDialog.eventFilter(self, watched, event)


    def keyPressEvent(self, event):
        if self.isReadOnly():
            event.accept()
        elif event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Enter, Qt.Key_Return):
            if self.focusWidget() in [self.edtBegDateClientDiseasesFilter,
                                      self.edtEndDateClientDiseasesFilter,
                                      self.chkExecActionsClientDiseasesFilter,
                                      self.cmbMKBFromClientDiseasesFilter,
                                      self.cmbMKBToClientDiseasesFilter,
                                      self.chkPreliminaryClientDiseasesFilter,
                                      self.chkConcomitantClientDiseasesFilter
                                      ]:
                self.on_clientDiseasesFilter_apply()
                event.accept()
            elif self.focusWidget() in [self.edtBegDateClientVaccinationsFilter,
                                        self.edtEndDateClientVaccinationsFilter,
                                        self.chkExecActionsClientVaccinationsFilter,
                                        self.btnInfectionsClientVaccinationsFilter
                                        ]:
                self.on_clientVaccinationsFilter_apply()
                event.accept()
            elif self.focusWidget() in [self.edtBegDateClientStatusActionsFilter,
                                        self.edtEndDateClientStatusActionsFilter,
                                        self.chkExecActionsClientStatusActionsFilter,
                                        ]:
                self.on_clientStatusActionsFilter_apply()
                event.accept()
            elif self.focusWidget() in [self.edtBegDateDiagnosticActionsFilter,
                                        self.edtEndDateDiagnosticActionsFilter,
                                        self.chkExecActionsDiagnosticActionsFilter,
                                        ]:
                self.on_diagnosticActionsFilter_apply()
                event.accept()
            else:
                CItemEditorBaseDialog.keyPressEvent(self, event)
        else:
            CItemEditorBaseDialog.keyPressEvent(self, event)


    def saveDiagnostics(self, modelDiagnostics, eventId):
        items = modelDiagnostics.items()
        recordAction = self.action.getRecord() if self.action else None
        #begDate = forceDateTime(recordAction.value('begDate')) if recordAction else QDateTime()
        db = QtGui.qApp.db
        tableDiagnosis = db.table('Diagnosis')
        personId = None
        specialityId = None
        if QtGui.qApp.userId and QtGui.qApp.userSpecialityId:
            personId = QtGui.qApp.userId
            specialityId = QtGui.qApp.userSpecialityId
        elif recordAction:
            personId = forceRef(recordAction.value('setPerson_id'))
            if personId:
                tablePerson = db.table('Person')
                recordPerson = db.getRecordEx(tablePerson, [tablePerson['speciality_id']], [tablePerson['id'].eq(personId), tablePerson['deleted'].eq(0)])
                specialityId = forceRef(recordPerson.value('speciality_id')) if recordPerson else None
        for item in items:
            endDate = forceDateTime(item.value('endDate'))
            setDate = forceDateTime(item.value('setDate'))
#            if begDate and begDate.isValid():
#                if begDate <= endDate:
#                    item.setValue('setDate', toVariant(begDate))
#                    item.setValue('endDate', toVariant(begDate))
#                else:
#                    item.setValue('setDate', toVariant(endDate))
#                    item.setValue('endDate', toVariant(endDate))
#            else:
#                item.setValue('setDate', toVariant(endDate))
#                item.setValue('endDate', toVariant(endDate))
            if setDate and setDate.isValid():
                if setDate > endDate:
                    item.setValue('setDate', toVariant(endDate))
            else:
                item.setValue('setDate', toVariant(endDate))
            item.setValue('event_id', toVariant(eventId))
            item.setValue('speciality_id', toVariant(specialityId))
            item.setValue('person_id', toVariant(personId))
            record = None
            diagnosisId = forceRef(item.value('diagnosis_id'))
            if diagnosisId:
                record = db.getRecordEx(tableDiagnosis, '*', [tableDiagnosis['id'].eq(diagnosisId), tableDiagnosis['deleted'].eq(0)])
            if not record:
                record = tableDiagnosis.newRecord()
            record.setValue('MKB', toVariant(forceStringEx(item.value('MKB'))))
            record.setValue('morphologyMKB', toVariant(forceStringEx(item.value('morphologyMKB'))))
            record.setValue('diagnosisType_id', item.value('diagnosisType_id'))
            record.setValue('client_id', toVariant(self.clientId))
            record.setValue('person_id', item.value('person_id'))
            record.setValue('setDate', item.value('setDate'))
            record.setValue('endDate', item.value('endDate'))
            newDiagnosisId = db.insertOrUpdate(tableDiagnosis, record)
            record.setValue('id', toVariant(newDiagnosisId))
            item.setValue('diagnosis_id', toVariant(newDiagnosisId))
        modelDiagnostics.saveItems(eventId)


    def saveInspectionsResultDiagnostics(self, eventId):
        baseDiagnosisTypeId = self.modelDiagnostics.diagnosisTypeCol.ids[1]
        accompDiagnosisTypeId = self.modelDiagnostics.diagnosisTypeCol.ids[2]
        items = self.modelDiagnostics.items()
        isDiagnosisManualSwitch = self.modelDiagnostics.manualSwitchDiagnosis()
        begDate = self.edtBegDate.date()
        endDate = self.edtEndDate.date()
        date = endDate if endDate else begDate
        prevItem = None
        for idx in reversed(xrange(len(items))):
            item = items[idx]
            MKB  = forceStringEx(item.value('MKB'))
            diagnosisId = forceRef(item.value('diagnosis_id'))
            diagnosisTypeId = forceRef(item.value('diagnosisType_id'))
            if diagnosisTypeId is None:
                diagnosisTypeId = baseDiagnosisTypeId
                item.setValue('diagnosisType_id', toVariant(diagnosisTypeId))
            TNMS = forceStringEx(item.value('TNMS'))
            morphologyMKB = forceStringEx(item.value('morphologyMKB'))
            if not MKB:
                diagnosisId = None
                characterId = item.value('character_id')
            else:
                diagnosisId, characterId = getDiagnosisId2(
                    date,
                    forceRef(item.value('person_id')),
                    self.clientId,
                    diagnosisTypeId,
                    MKB,
                    '',
                    forceRef(item.value('character_id')),
                    forceRef(item.value('dispanser_id')),
                    None,
                    diagnosisId,
                    forceRef(item.value('id')),
                    isDiagnosisManualSwitch,
                    forceBool(item.value('handleDiagnosis')),
                    TNMS=TNMS,
                    morphologyMKB=morphologyMKB,
                    dispanserBegDate=forceDate(item.value('endDate')),
                    exSubclassMKB=forceStringEx(item.value('exSubclassMKB')))
            if diagnosisTypeId == accompDiagnosisTypeId and prevItem:
                for fieldName in ('speciality_id', 'person_id', 'setDate', 'endDate'):
                    item.setValue(fieldName, prevItem.value(fieldName))
            item.setValue('diagnosis_id', toVariant(diagnosisId))
            item.setValue('TNMS', toVariant(TNMS))
            item.setValue('character_id', toVariant(characterId))
            prevItem = item
        self.modelDiagnostics.saveItems(eventId)


    def on_actionAmountChanged(self, value):
        self.edtAmount.setValue(value)


    def setEventDate(self, date):
        eventRecord = self._getEventRecord()
        if eventRecord:
            execDate = forceDate(eventRecord.value('execDate'))
            if not execDate:
                self._eventExecDate = date
                self.eventDate = date


    def _getEventRecord(self):
        if not self.recordEvent and self.eventId:
            self.recordEvent = QtGui.qApp.db.getRecordEx('Event', 'id, execDate, isClosed', 'id=%d'%self.eventId)
        return self.recordEvent


    def setReduced(self, value):
        self.txtClientInfoBrowser.setVisible(not value)
        if self.clientInfo is None:
            self.clientInfo = getClientInfo(self.clientId, date=self.edtDirectionDate.date())
        name = formatName(self.clientInfo.lastName, self.clientInfo.firstName, self.clientInfo.patrName)
        self.setWindowTitle(self.windowTitle()+' : '+ name)


    @pyqtSignature('QAbstractButton*')
    def on_buttonBox_clicked(self, button):
        buttonCode = self.buttonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Save:
            self.save()
#        elif buttonCode == QtGui.QDialogButtonBox.Close:
#            self.close()


    def done(self, result):
        if self.isReadOnly():
            scd = self.cdDiscard
        if result == 1:   # кнопка Save: сохранить не закрывая
            scd = self.cdSaveNoClose
        else: #закрытие
            scd = self.askSaveDiscardContinueEdit()
        if scd == self.cdDiscard or (scd == self.cdSave and self.saveData()):
            self.saveDialogPreferences()
            if result < 0:
               result = 1 if scd == self.cdSave else 0
            QtGui.QDialog.done(self, result)


    def exec_(self):
        QtGui.qApp.setCounterController(CCounterController(self))
        QtGui.qApp.setJTR(self)
        try:
            if self.lock(self._tableName, self._id):
                try:
                    if self._id:
                        db = QtGui.qApp.db
                        record = db.getRecord(db.table(self._tableName), '*', self._id)
                        self.isActionSave = False
                        self.isBtnSave = False
                        self.setRecord(record)
                        self.setIsDirty(False)
                        if not self.checkDataBeforeOpen():
                            return QtGui.QDialog.Rejected
                    self.loadDialogPreferences()
                    rect = self.frameGeometry()
                    pos = self.pos()
                    if pos.x() < 0 or pos.y() < 0:
                        rect.moveCenter(QtGui.qApp.desktop().availableGeometry().center())
                        self.setGeometry(rect)
                    isLoaded = False
                    if not self._id: # если новая форма
                        try:
                            isLoaded = loadUnsavedDataForEventDialog(self)
                        except:
                            QtGui.qApp.logCurrentException()
                    # При открытии формы isDirty = False
                    # Если данные были восстановлены, то isDirty = True
                    self.setIsDirty(isLoaded)
                    result = QtGui.QDialog.exec_(self)
                    if self.isDirty():
                        try:
                            storeUnsavedDataForEventDialog(self)
                        except:
                            QtGui.qApp.logCurrentException()
                finally:
                    self.releaseLock()
            else:
                result = QtGui.QDialog.Rejected
                self.setResult(result)
        finally:
            QtGui.qApp.unsetJTR(self)
        if result:
            QtGui.qApp.delAllCounterValueIdReservation()
        else:
            QtGui.qApp.resetAllCounterValueIdReservation()
        QtGui.qApp.setCounterController(None)
        QtGui.qApp.disconnectClipboard()
        return result


    def setForceClientId(self, clientId):
        self.forceClientId = clientId


    def getCurrentTimeAction(self, actionDate):
        currentDateTime = QDateTime.currentDateTime()
        if currentDateTime == actionDate:
            currentTime = currentDateTime.time()
            return currentTime.addSecs(60)
        else:
            return currentDateTime.time()


    def getClientId(self, eventId):
        if self.forceClientId:
            return self.forceClientId
        return forceRef(QtGui.qApp.db.translate('Event', 'id', eventId, 'client_id'))


    def setComboBoxes(self):
        self.setPropertyDomainWidget(self.cmbInfoResult, u'ME:conclusion', isNotDefined = True)


    def setPropertyDomainWidget(self, widget, propertyDescr, isNotDefined = True):
        widget._model.clear()
        domain, defaultValue = self.getPropertyDomain(propertyDescr, isNotDefined)
        widget.setDomain(domain, isUpdateCurrIndex=False)
        if self.isCreate:
            if defaultValue:
                widget.setValue(defaultValue)
            else:
                widget.setCurrentIndex(0)


    def getPropertyDomain(self, propertyDescr, isNotDefined = True):
        domain = u'\'не определено\',' if isNotDefined else u''
        record, defaultValue = self.propertyDomain(propertyDescr)
        if record:
            domainR = QString(forceString(record))
            if u'*' in domainR:
                index = domainR.indexOf(u'*', 0, Qt.CaseInsensitive)
                if domainR[index - 1] != u',':
                    domainR.replace(QString('*'), QString(','))
                else:
                    domainR.remove(QChar('*'), Qt.CaseInsensitive)
            domain += domainR
            if u'[mc]' in domain:
                domain = domain.remove(QString(u'[mc]'), Qt.CaseInsensitive)
        return domain, defaultValue


    def propertyDomain(self, propertyDescr):
        if not self.actionTypeIdListByELMK:
            return None, None
        db = QtGui.qApp.db
        tableAPT = db.table('ActionPropertyType')
        tableActionType = db.table('ActionType')
        cond =[tableActionType['id'].inlist(self.actionTypeIdListByELMK),
               tableAPT['descr'].like(propertyDescr),
               tableActionType['deleted'].eq(0),
               tableAPT['deleted'].eq(0)
               ]
        if self.actionTypeId:
            cond.append(tableAPT['actionType_id'].eq(self.actionTypeId))
        queryTable = tableActionType.innerJoin(tableAPT, tableActionType['id'].eq(tableAPT['actionType_id']))
        record = db.getRecordEx(queryTable, [tableAPT['valueDomain'], tableAPT['defaultValue']], cond)
        if record:
            return record.value(0), record.value(1)
        return None, None


    @pyqtSignature('int')
    def on_tabWidget_currentChanged(self, index):
        widget = self.tabWidget.widget(index)
        if widget is not None:
            focusProxy = widget.focusProxy()
            if focusProxy:
                focusProxy.setFocus(Qt.OtherFocusReason)
        currentIndex = self.tabWidget.currentIndex()
        if currentIndex == self.tabWidget.indexOf(self.tabInfectionDiseases):
            self.on_clientDiseasesFilter_apply()
        elif currentIndex == self.tabWidget.indexOf(self.tabVaccinations):
            self.on_clientVaccinationsFilter_apply()
        elif currentIndex == self.tabWidget.indexOf(self.tabStatusActions):
            self.on_clientStatusActionsFilter_apply()
        elif currentIndex == self.tabWidget.indexOf(self.tabDiagnosticActions):
            self.on_diagnosticActionsFilter_apply()


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        self.eventId = forceRef(record.value('event_id'))
        self.eventTypeId = None
        self.eventPurposeId = None
        self.eventSetDate = None
        self.eventSetDateTime = None
        self.eventDate = None
        self.recordEvent = None
        db = QtGui.qApp.db
        if self.eventId:
            tableEvent = db.table('Event')
            self.recordEvent = db.getRecordEx(tableEvent, '*', [tableEvent['id'].eq(self.eventId), tableEvent['deleted'].eq(0)])
            if self.recordEvent:
                self.eventTypeId = forceRef(self.recordEvent.value('eventType_id'))
                self.eventSetDate = forceDate(self.recordEvent.value('setDate'))
                self.eventSetDateTime = forceDateTime(self.recordEvent.value('setDate'))
                self.eventDate = forceDate(self.recordEvent.value('execDate'))
        if not self.orgId:
            currentOrgId = forceRef(self.recordEvent.value('org_id')) if self.recordEvent else None
            if not currentOrgId:
                if QtGui.qApp.userId:
                    recordPerson = db.getRecord('Person', ['org_id'], QtGui.qApp.userId)
                    if recordPerson:
                        currentOrgId = forceRef(recordPerson.value('org_id'))
            if not currentOrgId:
                currentOrgId = QtGui.qApp.currentOrgId()
            self.orgId = currentOrgId
        if self.eventTypeId:
            self.eventPurposeId = getEventPurposeId(self.eventTypeId)
        if self.eventPurposeId:
            resultColIndex = self.modelDiagnostics.getColIndex('result_id', None)
            if resultColIndex >= 0:
                self.modelDiagnostics.cols()[resultColIndex].setFilter(u'''rbDiagnosticResult.eventPurpose_id=%d'''%(self.eventPurposeId))
        #self.getActionTypeToEventType()
        self.idx = forceInt(record.value('idx'))
        self.clientId = self.getClientId(self.eventId)
        self.action = CAction(record=record)
        self.getHurtTypeSetTable(self.action)
        actionType = self.action.getType()
        self.actionTypeId = actionType.id
        if not self.isActionSave:
            self.setComboBoxes()
        self.action.executionPlanManager.load()
        self.action.executionPlanManager.setCurrentItemIndex()
        showTime = actionType.showTime
        self.isRelationRepresentativeSetClientId = True
        self.tabNotes.cmbClientRelationConsents.clear()
        self.tabNotes.cmbClientRelationConsents.setClientId(self.clientId)
        self.tabNotes.cmbClientRelationConsents.setValue(forceRef(self.recordEvent.value('relative_id')))
        self.isRelationRepresentativeSetClientId = False
        self.edtDirectionTime.setVisible(showTime)
        self.edtPlannedEndTime.setVisible(showTime)
        self.edtBegTime.setVisible(showTime)
        self.edtEndTime.setVisible(showTime)
        self.lblAssistant.setVisible(actionType.hasAssistant)
        self.cmbAssistant.setVisible(actionType.hasAssistant)
        self.setWindowTitle(actionType.code + '|' + actionType.name)
        setCheckBoxValue(self.chkIsUrgent, record, 'isUrgent')
        #self.chkIsUrgent.setChecked(forceBool(record.value('isUrgent')))
        setDatetimeEditValue(self.edtDirectionDate,    self.edtDirectionTime,    record, 'directionDate')
        setDatetimeEditValue(self.edtPlannedEndDate,   self.edtPlannedEndTime,   record, 'plannedEndDate')
        setDatetimeEditValue(self.edtBegDate,          self.edtBegTime,          record, 'begDate')
        setDatetimeEditValue(self.edtEndDate,          self.edtEndTime,          record, 'endDate')
        setRBComboBoxValue(self.cmbStatus,      record, 'status')
        setDoubleBoxValue(self.edtAmount,       record, 'amount')
        setDoubleBoxValue(self.edtUet,          record, 'uet')
        setRBComboBoxValue(self.cmbPerson,      record, 'person_id')
        setRBComboBoxValue(self.cmbSetPerson,   record, 'setPerson_id')
        setLineEditValue(self.edtOffice,        record, 'office')
        setRBComboBoxValue(self.cmbAssistant,   record, 'assistant_id')
        setLineEditValue(self.edtNote,          record, 'note')
        self.cmbOrg.setValue(forceRef(record.value('org_id')))
        if (self.cmbPerson.value() is None
                and actionType.defaultPersonInEditor in (CActionType.dpUndefined, CActionType.dpCurrentUser, CActionType.dpCurrentMedUser)
                and QtGui.qApp.userSpecialityId):
            self.cmbPerson.setValue(QtGui.qApp.userId)
        self.setPersonId(self.cmbPerson.value())
        self.updateClientInfo()
        context = actionType.context if actionType else ''
        customizePrintButton(self.btnPrint, context)
        self.btnAttachedFiles.setAttachedFileItemList(self.action.getAttachedFileItemList())
        self.btnAttachedFiles.setAction(self.action)
        #self.btnAttachedFiles.setEnabled(not self.isProtected)
        canEdit = (not self.action.isLocked() if self.action else True) and not self.isProtected
        for widget in (self.edtPlannedEndDate, self.edtPlannedEndTime,
                       self.cmbStatus, self.edtBegDate, self.edtBegTime,
                       self.edtEndDate, self.edtEndTime,
                       self.cmbPerson, self.edtOffice, self.cmbSetPerson,
                       self.cmbAssistant,
                       self.edtUet,
                       self.edtNote, self.cmbOrg,
                       self.buttonBox.button(QtGui.QDialogButtonBox.Save)
                      ):
                widget.setEnabled(canEdit)
        self.edtAmount.setEnabled(actionType.amountEvaluation == 0 and canEdit)
        canEditPlannedEndDate = canEdit and actionType.defaultPlannedEndDate not in (CActionType.dpedBegDatePlusAmount,
                                                                                     CActionType.dpedBegDatePlusDuration)
        canEditIsExecutionPlan = not bool(self.action.getExecutionPlan() and self.action.executionPlanManager.hasItemsToDo())
        self.edtPlannedEndDate.setEnabled(canEditPlannedEndDate and canEditIsExecutionPlan)
        self.edtPlannedEndTime.setEnabled(canEditPlannedEndDate and bool(self.edtPlannedEndDate.date()) and canEditIsExecutionPlan)
        self.edtBegTime.setEnabled(bool(self.edtBegDate.date()) and canEdit)
        self.edtEndTime.setEnabled(bool(self.edtEndDate.date()) and canEdit)
        self.edtPlannedEndTime.setEnabled(bool(self.edtPlannedEndDate.date()) and canEdit)
        self.edtDirectionDate.setEnabled(not self.isProtected)
        self.edtDirectionTime.setEnabled(bool(self.edtDirectionDate.date()) and not self.isProtected)
        self.chkIsUrgent.setReadOnly(self.isProtected)
        self.initDateParamsFilter(self.edtEndDate.date())
        self.setProperties()
        self.tabNotes.setEventEditor(self)
        self.tabNotes.initContract()
        if self.recordEvent:
            self.tabNotes.setNotes(self.recordEvent)
        self.modelMembersMSIPerson.setAction(self.action)
        self.modelMembersMSIPerson.loadItems()
        self.modelInfectionDiseases.setAction(self.action)
        self.modelInfectionDiseases.loadItems(self.eventId)
        self.modelClientDiseases.setAction(self.action)
        self.updateClientDiseases()
        #self.modelClientDiseases.loadItems(self.eventId, self.clientId)
        self.modelVaccinations.setAction(self.action)
        self.modelVaccinations.loadItems(self.itemId())
        self.modelClientVaccinations.setAction(self.action)
        self.updateClientVaccinations()
        #self.modelClientVaccinations.loadItems(self.itemId(), self.clientId)
        self.modelStatusActions.setAction(self.action)
        self.modelStatusActions.loadItems(self.itemId())
        self.modelClientStatusActions.setAction(self.action)
        self.updateClientStatusActions()
        #self.modelClientStatusActions.loadItems(self.itemId(), self.clientId)
        self.modelLabDiagnosticActions.setAction(self.action)
        self.modelLabDiagnosticActions.loadItems(self.itemId())
        self.modelToolDiagnosticActions.setAction(self.action)
        self.modelToolDiagnosticActions.loadItems(self.itemId())
        self.modelClientDiagnosticActions.setAction(self.action)
        self.updateDiagnosticActions()
        #self.modelClientDiagnosticActions.loadItems(self.itemId(), self.clientId)
        actionId = self.itemId()
        # actionExportIdList = []
        # if actionId:
        #     tableActionExport = db.table('Action_Export')
        #     actionExportIdList = db.getDistinctIdList(tableActionExport, [tableActionExport['id']], [tableActionExport['master_id'].eq(actionId)])
        # self.modelExport.setIdList(actionExportIdList)
        iniExportEvent(self)
#        self.tblInfectionDiseases.setRowHidden(1, True)
        self.tblInfectionDiseases.resizeColumnToContents(2)
#        self.tblClientDiseases.setRowHidden(1, True)
        self.tblClientDiseases.resizeColumnToContents(4)
##        self.tblClientDiseases.resizeRowToContents(0)
#        form = getEventTypeForm(self.eventTypeId)
#        if form == u'090':
        dlg = CPreF001Dialog(self, self.contractTariffCache)
        try:
            dlg.setBegDateEvent(self.eventSetDateTime.date() if isinstance(self.eventSetDateTime, QDateTime) else self.eventSetDateTime)
            dlg.prepare(self.clientId, self.eventTypeId, self.eventSetDateTime.date(), self.personId, self.personSpecialityId, self.personTariffCategoryId)
            self.preSpecialityIdList = dlg.preSpecialityIdList
            self.modelDiagnostics.setPreSpecialityIdList(dlg.preSpecialityIdList)
            self.modelDiagnostics.isSelectionGroupOne = dlg.isSelectionGroupOne
            self.loadDiagnostics(dlg.modelDiagnostics.items(), self.eventId)
        finally:
            dlg.deleteLater()
        self.isActionSave = False
        self.getInfectionVaccinations()
        self.getPostIdList()
        self.getNomenclativeServiceIdList()


    def getDescrTextEdit(self):
        return [u'ME:comment']


    def setProperties(self, isCreate=False):
        items = {}
        if self.action:
            descrTextEditList = self.getDescrTextEdit()
            if isCreate:
                for propertyTypeName, propertyType in self.action.getType()._propertiesByName.items():
                    isDescrTextEdit = False
                    descr = trim(propertyType.descr)
                    value = self.action[propertyTypeName]
                    propertyValue = propertyType.convertQVariantToPyValue(value) if type(value) == QVariant else value
                    for descrTextEdit in descrTextEditList:
                        if descr == descrTextEdit:
                            isDescrTextEdit = True
                            break
                    if (isinstance(propertyValue, basestring) or type(propertyValue) == QString) and not isDescrTextEdit:
                        propertyValue = trim(propertyValue)
                    if propertyValue:
                        item = items.get(descr, [])
                        if propertyValue and (isinstance(propertyValue, basestring) or type(propertyValue) == QString) and len(propertyValue) > 1 and not isDescrTextEdit:
                            propertyValue = propertyValue.split(u',')
                            item.extend(propertyValue)
                        else:
                            item.append(propertyValue)
                        items[descr] = item
            else:
                for property in self.action._propertiesById.itervalues():
                    isDescrTextEdit = False
                    propertyType = property.type()
                    descr = trim(propertyType.descr)
                    value = property._value
                    propertyValue = propertyType.convertQVariantToPyValue(value) if type(value) == QVariant else value
                    for descrTextEdit in descrTextEditList:
                        if descr == descrTextEdit:
                            isDescrTextEdit = True
                            break
                    if (isinstance(propertyValue, basestring) or type(propertyValue) == QString) and not isDescrTextEdit:
                        propertyValue = trim(propertyValue)
                    if propertyValue:
                        item = items.get(descr, [])
                        if propertyValue and (isinstance(propertyValue, basestring) or type(propertyValue) == QString) and len(propertyValue) > 1 and not isDescrTextEdit:
                            propertyValue = propertyValue.split(u',')
                            item.extend(propertyValue)
                        else:
                            item.append(propertyValue)
                        items[descr] = item
            if items:
                # tabMainInformation
                self.cmbHurtType.setValue(self.getPropertyValue(items, u'ME:work', forceRef))
#                self.chkEpidemicIndications.setChecked(self.getPropertyValue(items, u'ME:epidemic_indications', QCheckBox))
                self.edtElectronicMedicalBookNumber.setText(self.getPropertyValue(items, u'ME:medical_book_number', QString))
                # tabInfectionDiseases
                # tabVaccinations
                # tabStatusActions
                # tabDiagnosticActions
                # tabCommission
                # tabResult
                self.cmbInfoResult.setValue(self.getPropertyValue(items, u'ME:conclusion', QString))
                self.edtVisitDateNextResult.setDate(self.getPropertyValue(items, u'ME:next_medical_examination_date', QDate))
                self.edtCommentResult.setPlainText(self.getPropertyValue(items, u'ME:comment', QTextEdit))
                # tabExport
                # tabNotes


    def getPropertyValue(self, items, descr, widgetType):
        item = items.get(descr, [])
        if widgetType == QString:
            return u','.join(val if (val and (isinstance(val, basestring) or type(val) == QString)) else str(val) for val in item if val)
        valueProperty = None
        if len(item) > 0:
            valueProperty = item[0]
        if widgetType == QTextEdit:
            return forceString(valueProperty)
        if widgetType == forceRef:
            return forceRef(valueProperty)
        if widgetType == QCheckBox:
            if valueProperty and (isinstance(valueProperty, basestring) or type(valueProperty) == QString):
                if valueProperty in [u'true', u'True']:
                    return True
            elif type(valueProperty) is int and valueProperty > 0:
                return True
            elif type(valueProperty) is bool:
                return valueProperty
            return False
        if widgetType == int:
            if valueProperty and (isinstance(valueProperty, basestring) or type(valueProperty) == QString):
                if valueProperty in [u'true', u'True']:
                    return 1
                else:
                    return int(valueProperty) if valueProperty else 0
            elif type(valueProperty) is bool:
                return int(valueProperty)
            return forceInt(valueProperty)
        if widgetType == QDate:
            if valueProperty and (isinstance(valueProperty, basestring) or type(valueProperty) == QString):
                return QDate().fromString(valueProperty,'dd.MM.yyyy')
            else:
                return forceDate(valueProperty)
        if widgetType == float:
            return forceDouble(QVariant(valueProperty))


    def setProperty(self, value, propertyDescr):
        if self.action:
            for propertyTypeName, propertyType in self.action.getType()._propertiesByName.items():
                if trim(propertyDescr) == trim(propertyType.descr):
                    if propertyTypeName and propertyTypeName in self.action._actionType._propertiesByName:
                        value = propertyType.convertQVariantToPyValue(value)
                        if type(value) == unicode:
                            value = value.replace('\0', '')
                        self.action[propertyTypeName] = QVariant(value)
                        break


    def getProperty(self, propertyDescr):
        if self.action:
            actionType = self.action.getType()
            for name, propertyType in actionType._propertiesByName.items():
                if trim(propertyType.descr) == trim(propertyDescr):
                    return toVariant(self.action[name])
        return QVariant()


    def getRecord(self):
        record = self.record()
        showTime = self.action.getType().showTime
        eventRecord = self._getEventRecord()
        if eventRecord:
            eventExecDate = forceDate(eventRecord.value('execDate'))
            if not eventExecDate:
                getDatetimeEditValue(self.edtDirectionDate, self.edtDirectionTime, record, 'directionDate', showTime)
        getCheckBoxValue(self.chkIsUrgent, record, 'isUrgent')
        getDatetimeEditValue(self.edtDirectionDate,  self.edtDirectionTime,  record, 'directionDate', showTime)
        getDatetimeEditValue(self.edtPlannedEndDate, self.edtPlannedEndTime, record, 'plannedEndDate', showTime)
        getDatetimeEditValue(self.edtBegDate, self.edtBegTime, record, 'begDate', showTime)
        getDatetimeEditValue(self.edtEndDate, self.edtEndTime, record, 'endDate', showTime)
        getRBComboBoxValue(self.cmbStatus,      record, 'status')
        getDoubleBoxValue(self.edtAmount,       record, 'amount')
        getDoubleBoxValue(self.edtUet,          record, 'uet')
        getRBComboBoxValue(self.cmbPerson,      record, 'person_id')
        getRBComboBoxValue(self.cmbSetPerson,   record, 'setPerson_id')
        getRBComboBoxValue(self.cmbAssistant,   record, 'assistant_id')
        getLineEditValue(self.edtOffice,        record, 'office')
        getLineEditValue(self.edtNote,          record, 'note')
        record.setValue('org_id', QVariant(self.cmbOrg.value()))
        result = type(record)(record) # copy record
        result.remove(result.indexOf('payStatus'))
        if self.recordEvent:
            self.tabNotes.getNotes(self.recordEvent, self.eventTypeId)
        self.modelMembersMSIPerson.saveItems()
        return result


    def getEventRecord(self):
        return self.recordEvent


    def setEventRecord(self, recordEvent):
        self.recordEvent = recordEvent


    def save(self):
        try:
            prevId = self.itemId()
            db = QtGui.qApp.db
            db.transaction()
            try:
                id = self.saveAction()
                db.commit()
            except:
                db.rollback()
                self.setItemId(prevId)
                QtGui.QMessageBox.critical( self,
                                            u'Внимание!',
                                            u'Информация не была сохранена.',
                                            QtGui.QMessageBox.Ok)
                raise
            if id:
                self.setItemId(id)
                self.afterSave()
                QtGui.QMessageBox.information( self,
                                               u'Внимание!',
                                               u'Информация была успешно сохранена.',
                                               QtGui.QMessageBox.Ok,
                                               QtGui.QMessageBox.Ok)
            return id
        except Exception as e:
            if self._isAssertNoMessage:
                return None
            QtGui.qApp.logCurrentException()
            QtGui.QMessageBox.critical( self,
                                        u'',
                                        exceptionToUnicode(e),
                                        QtGui.QMessageBox.Close)
            return None


    def afterSave(self):
        if self._id:
            db = QtGui.qApp.db
            record = db.getRecord(db.table(self._tableName), '*', self._id)
            self.isActionSave = True
            self.isBtnSave = True
            self.setRecord(record)
        self.setIsDirty(False)


    def getActionMKB(self): # ????????????????????
        MKB = ''
        items = self.modelInfectionDiseases.items() # ??????????????????????????
        for item in items:
            MKB = forceStringEx(item.value('MKB'))
            if MKB:
                break
        self.action.getRecord().setValue('MKB', toVariant(MKB))
        self.action.setChanged(True)
        return MKB


    def saveAction(self):
        newActionId = None
        if self.action and self.checkDataEntered(secondTry=True):
            self.getActionMKB()
            self.action._record = self.getRecord()
            self.setTextEdits()
            eventRecordMSI = self.getEventRecord()
            idxMSI = self.idx
            db = QtGui.qApp.db
            tableEvent = db.table('Event')
            tableEventType = db.table('EventType')
            recordAction = self.action.getRecord()
            eventRecordMSIId = forceRef(eventRecordMSI.value('id')) if eventRecordMSI else None
            eventId = forceRef(recordAction.value('event_id')) if recordAction else (eventRecordMSIId if eventRecordMSIId else None)
            eventTypeId = forceRef(eventRecordMSI.value('eventType_id')) if eventRecordMSI else None
            recordEventType = None
            if not eventTypeId:
                recordEventType = db.getRecordEx(tableEventType, [tableEventType['id'], tableEventType['order'], tableEventType['isPrimary']], [tableEventType['form'].like(u'090'), tableEventType['deleted'].eq(0)], u'EventType.id')
                eventTypeId = forceRef(recordEventType.value('id')) if recordEventType else None
            else:
                recordEventType = db.getRecordEx(tableEventType, [tableEventType['id'], tableEventType['order'], tableEventType['isPrimary']], [tableEventType['id'].eq(eventTypeId), tableEventType['deleted'].eq(0)])
            order = forceInt(recordEventType.value('order')) if recordEventType else 0
            isPrimary = forceInt(recordEventType.value('isPrimary')) if recordEventType else 0
            actionRecord = self.action.getRecord()
            if eventId and eventRecordMSI:
                eventRecordMSI.setValue('setDate', toVariant(forceDateTime(actionRecord.value('begDate')) if actionRecord else QDateTime.currentDateTime()))
                execDate = forceDateTime(actionRecord.value('endDate')) if actionRecord else None
                if execDate and execDate.isValid():
                    eventRecordMSI.setValue('isClosed', QVariant(1))
                eventRecordMSI.setValue('execDate', toVariant(execDate))
                eventRecordMSI.setValue('setPerson_id', toVariant(forceRef(actionRecord.value('setPerson_id')) if actionRecord else None))
                eventRecordMSI.setValue('execPerson_id', toVariant(forceRef(actionRecord.value('person_id')) if actionRecord else None))
                if isPrimary and not forceInt(eventRecordMSI.value('isPrimary')):
                    eventRecordMSI.setValue('isPrimary', toVariant(isPrimary))
                if order and not forceInt(eventRecordMSI.value('order')):
                    eventRecordMSI.setValue('order', toVariant(order))
                newActionId = self.saveMedicalCommissionAction(self.action, eventRecordMSI, eventId, idx = idxMSI)
            else:
                if eventTypeId:
                    tableEvent = db.table('Event')
                    recordEvent = tableEvent.newRecord()
                    if eventRecordMSI:
                        for i in xrange(recordEvent.count()):
                            fieldName = recordEvent.fieldName(i)
                            if fieldName in tabEventFieldNames:
                                recordEvent.setValue(fieldName, eventRecordMSI.value(fieldName))
                        recordEvent.setValue('eventType_id',   toVariant(eventTypeId))
                        if self.clientId and not forceRef(recordEvent.value('client_id')):
                            recordEvent.setValue('client_id', toVariant(self.clientId))
                    else:
                        currentOrgId = None
                        if QtGui.qApp.userId:
                            recordPerson = db.getRecord('Person', ['org_id'], QtGui.qApp.userId)
                            if recordPerson:
                                currentOrgId = forceRef(recordPerson.value('org_id'))
                        if not currentOrgId:
                            currentOrgId = QtGui.qApp.currentOrgId()
                        self.orgId = currentOrgId
                        recordEvent.setValue('id', toVariant(None))
                        recordEvent.setValue('createDatetime', toVariant(QDateTime.currentDateTime()))
                        recordEvent.setValue('createPerson_id',toVariant(QtGui.qApp.userId))
                        recordEvent.setValue('modifyDatetime', toVariant(QDateTime.currentDateTime()))
                        recordEvent.setValue('modifyPerson_id',toVariant(QtGui.qApp.userId))
                        recordEvent.setValue('setDate',        toVariant(forceDateTime(actionRecord.value('begDate')) if actionRecord else QDateTime.currentDateTime()))
                        execDate = forceDateTime(actionRecord.value('endDate')) if actionRecord else None
                        if execDate and execDate.isValid():
                            eventRecordMSI.setValue('isClosed', QVariant(1))
                        recordEvent.setValue('execDate',       toVariant(execDate))
                        recordEvent.setValue('setPerson_id',   toVariant(forceRef(actionRecord.value('setPerson_id')) if actionRecord else None))
                        recordEvent.setValue('execPerson_id',  toVariant(forceRef(actionRecord.value('person_id')) if actionRecord else None))
                        recordEvent.setValue('isPrimary',      toVariant(isPrimary))
                        recordEvent.setValue('order',          toVariant(order))
                        recordEvent.setValue('eventType_id',   toVariant(eventTypeId))
                        recordEvent.setValue('client_id', toVariant(self.clientId))
                        recordEvent.setValue('relegatePerson_id', toVariant(QtGui.qApp.userId))
                        recordEvent.setValue('relegateOrg_id', toVariant(QtGui.qApp.currentOrgId()))
                        recordEvent.setValue('org_id',         toVariant(currentOrgId))
                    eventId = db.insertRecord(tableEvent, recordEvent)
                    if eventId:
                        recordEvent.setValue('id', toVariant(eventId))
                        self.setEventRecord(recordEvent)
                        self.tabNotes.setNotes(self.recordEvent)
                        newActionId = self.saveMedicalCommissionAction(self.action, recordEvent, eventId, idx = idxMSI)
            if eventId and newActionId:
                if hasattr(self, 'tabNotes') and hasattr(self.tabNotes, 'saveAttachedFiles'):
                    self.tabNotes.saveAttachedFiles(eventId)
                if hasattr(self, 'modelInfectionDiseases'):
                    if hasattr(self, 'modelDiagnostics'):
                        self.modelInfectionDiseases.setInspectionsResultIdList(self.modelDiagnostics.getItemIdList())
                    self.saveDiagnostics(self.modelInfectionDiseases, eventId)
                    if hasattr(self, 'modelDiagnostics'):
                        self.modelDiagnostics.setInfectionDiseasesIdList(self.modelInfectionDiseases.getItemIdList())
                if hasattr(self, 'modelVaccinations'):
                    self.modelVaccinations.saveItems(newActionId)
                if hasattr(self, 'modelStatusActions'):
                    self.modelStatusActions.saveItems(newActionId)
                if hasattr(self, 'modelLabDiagnosticActions'):
                    self.modelLabDiagnosticActions.saveItems(newActionId)
                if hasattr(self, 'modelToolDiagnosticActions'):
                    self.modelToolDiagnosticActions.saveItems(newActionId)
                if hasattr(self, 'modelDiagnostics'):
                    self.saveInspectionsResultDiagnostics(eventId)
                    if hasattr(self, 'modelInfectionDiseases'):
                        self.modelInfectionDiseases.setInspectionsResultIdList(self.modelDiagnostics.getItemIdList())
                    self.updateInspectionsResultVisits(eventId)
        return newActionId


    def saveMedicalCommissionAction(self, action, recordEvent = None, eventId = None, idx = 0):
        id = None
        try:
            try:
                db = QtGui.qApp.db
                db.transaction()
                id = self.action.save(eventId, idx = idx, checkModifyDate = False)
                if id:
                    self.action.getRecord().setValue('id', toVariant(id))
                    self.action.getRecord().setValue('event_id', toVariant(eventId))
                    checkTissueJournalStatusByActions([(self.action.getRecord(), self.action)])
                    if self.action.getType().closeEvent and recordEvent:
                        eventExecDate = forceDate(recordEvent.value('execDate'))
                        actionEndDate = forceDateTime(self.action.getRecord().value('endDate'))
                        if not eventExecDate and actionEndDate:
                            recordEvent.setValue('execDate', QVariant(actionEndDate))
                            recordEvent.setValue('isClosed', QVariant(1))
                    self.eventId = eventId
                    self.tabNotes.lblEventIdValue.setText(forceString(self.action.getRecord().value('event_id')))
                if recordEvent:
                    self.eventId = db.updateRecord('Event', recordEvent)
                if id and self.eventId:
                    tableEvent = db.table('Event')
                    recordEvent = db.getRecordEx(tableEvent, '*', [tableEvent['id'].eq(self.eventId), tableEvent['deleted'].eq(0)])
                    self.setEventRecord(recordEvent)
                db.commit()
            except:
                db.rollback()
                raise
        except Exception as e:
            QtGui.qApp.logCurrentException()
            QtGui.QMessageBox.critical( self,
                                        u'',
                                        exceptionToUnicode(e),
                                        QtGui.QMessageBox.Close)
        return id


    def saveInternals(self, id):
        self.getActionMKB()
        if self.checkDataEntered(secondTry=True):
            self.setTextEdits()
            id = self.action.save(self.eventId, self.idx, checkModifyDate=False)
            checkTissueJournalStatusByActions([(self.action.getRecord(), self.action)])
            eventRecord = self._getEventRecord()
            if self.action.getType().closeEvent:
                if eventRecord:
                    eventExecDate = forceDate(eventRecord.value('execDate'))
                    if not eventExecDate and self._eventExecDate:
                        eventRecord.setValue('execDate', QVariant(self._eventExecDate))
                        eventRecord.setValue('isClosed', QVariant(1))
            if eventRecord:
                self.eventId = QtGui.qApp.db.updateRecord('Event', eventRecord)
            if id and self.eventId:
                db = QtGui.qApp.db
                tableEvent = db.table('Event')
                recordEvent = db.getRecordEx(tableEvent, '*', [tableEvent['id'].eq(self.eventId), tableEvent['deleted'].eq(0)])
                self.setEventRecord(recordEvent)
                if hasattr(self, 'modelVaccinations'):
                    self.modelVaccinations.saveItems(id)
                if hasattr(self, 'modelStatusActions'):
                    self.modelStatusActions.saveItems(id)
                if hasattr(self, 'modelLabDiagnosticActions'):
                    self.modelLabDiagnosticActions.saveItems(id)
                if hasattr(self, 'modelToolDiagnosticActions'):
                    self.modelToolDiagnosticActions.saveItems(id)
            self.tabNotes.saveAttachedFiles(self.eventId)
            self.modelInfectionDiseases.setInspectionsResultIdList(self.modelDiagnostics.getItemIdList())
            self.saveDiagnostics(self.modelInfectionDiseases, self.eventId)
            self.modelDiagnostics.setInfectionDiseasesIdList(self.modelInfectionDiseases.getItemIdList())
            self.saveInspectionsResultDiagnostics(self.eventId)
            self.modelInfectionDiseases.setInspectionsResultIdList(self.modelDiagnostics.getItemIdList())
            self.updateInspectionsResultVisits(self.eventId)
        return id


    def updateClientInfo(self):
        db = QtGui.qApp.db
        self.clientInfo = getClientInfo(self.clientId, date=self.edtDirectionDate.date())
        self.txtClientInfoBrowser.setHtml(getClientBanner(self.clientId, self.edtDirectionDate.date()))
        table  = db.table('Client')
        record = db.getRecord(table, '*', self.clientId)
        if record:
            directionDate = self.edtDirectionDate.date()
            self.clientSex       = forceInt(record.value('sex'))
            self.clientBirthDate = forceDate(record.value('birthDate'))
            self.clientAge       = calcAgeTuple(self.clientBirthDate, directionDate)
        self.actShowAttachedToClientFiles.setMasterId(self.clientId)
        self.clientDeathDate = getDeathDate(self.clientId)
        self.isRelationRepresentativeSetClientId = True
        self.tabNotes.cmbClientRelationConsents.clear()
        self.tabNotes.cmbClientRelationConsents.setClientId(self.clientId)
        self.tabNotes.cmbClientRelationConsents.setValue(forceRef(self.recordEvent.value('relative_id')))
        self.isRelationRepresentativeSetClientId = False


    def currentClientId(self):
        return self.clientId


    def currentClientSex(self):
        return self.clientSex


    def currentClientAge(self):
        return self.clientAge


    def updateAmount(self):
        def getActionDuration(weekProfile):
            startDate = self.edtBegDate.date()
            stopDate  = self.edtEndDate.date()
            if startDate and stopDate:
                return getEventDuration(startDate, stopDate, weekProfile, self.eventTypeId)
            else:
                return 0
        def setAmount(amount):
            self.edtAmount.setValue(amount)
        actionType = self.action.getType()
        if actionType.amountEvaluation == CActionType.actionPredefinedNumber:
            setAmount(actionType.amount)
        elif actionType.amountEvaluation == CActionType.actionDurationWithFiveDayWorking:
            setAmount(actionType.amount*getActionDuration(wpFiveDays))
        elif actionType.amountEvaluation == CActionType.actionDurationWithSixDayWorking:
            setAmount(actionType.amount*getActionDuration(wpSixDays))
        elif actionType.amountEvaluation == CActionType.actionDurationWithSevenDayWorking:
            setAmount(actionType.amount*getActionDuration(wpSevenDays))
        elif actionType.amountEvaluation == CActionType.actionFilledPropsCount:
            setAmount(actionType.amount*self.action.getFilledPropertiesCount())
        elif actionType.amountEvaluation == CActionType.actionAssignedPropsCount:
            setAmount(actionType.amount*self.action.getAssignedPropertiesCount())
        if actionType.defaultPlannedEndDate == CActionType.dpedBegDatePlusAmount:
            begDate = self.edtBegDate.date()
            amountValue = int(self.edtAmount.value())
            date = begDate.addDays(amountValue-1) if begDate and amountValue else QDate()
            self.edtPlannedEndDate.setDate(date)
        elif actionType.defaultPlannedEndDate == CActionType.dpedBegDatePlusDuration:
            begDate = self.edtBegDate.date()
            durationValue = self.edtDuration.value()
            date = begDate.addDays(durationValue) if begDate else QDate()
            self.edtPlannedEndDate.setDate(date)


    def checkDataEntered(self, secondTry=False):
        result = True
        begDate = self.edtBegDate.date()
        endDate = self.edtEndDate.date()
        result = result and (self.tabNotes.cmbContract.value() or self.checkInputMessage(u'договор', False, self.tabNotes.cmbContract))
        if endDate:
            if QtGui.qApp.isStrictCheckPolicyOnEndAction() in (0, 1):
                if not checkPolicyOnDate(self.clientId, endDate):
                    skippable = QtGui.qApp.isStrictCheckPolicyOnEndAction() == 0
                    result = result and self.checkInputMessage(u'время закрытия действия соответствующее полису',
                                                               skippable, self.edtEndDate)
            if QtGui.qApp.isStrictCheckAttachOnEndAction() in (0, 1):
                if not checkAttachOnDate(self.clientId, endDate):
                    skippable = QtGui.qApp.isStrictCheckAttachOnEndAction() == 0
                    result = result and self.checkInputMessage(u'время закрытия действия соответствующее прикреплению',
                                                               skippable, self.edtEndDate)
        showTime = self.action._actionType.showTime and getEventShowTime(self.eventTypeId)
        if showTime:
            begDate = toDateTimeWithoutSeconds(QDateTime(begDate, self.edtBegTime.time()))
            endDate = toDateTimeWithoutSeconds(QDateTime(endDate, self.edtEndTime.time()))
            result = result and (endDate >= begDate or self.checkValueMessage(u'Дата выполнения действия %s не должна быть раньше даты начала действия % s'%(forceString(endDate), forceString(begDate)), False, self.edtEndTime))
        if begDate and endDate:
            if showTime:
                result = result and (endDate >= begDate or self.checkValueMessage(u'Дата выполнения действия %s не должна быть раньше даты начала действия % s'%(forceString(endDate), forceString(begDate)), False, self.edtEndTime))
            else:
                result = result and (endDate >= begDate or self.checkValueMessage(u'Дата выполнения действия %s не должна быть раньше даты начала действия % s'%(forceString(endDate), forceString(begDate)), False, self.edtEndDate))
        if result and self.eventId:
            record = QtGui.qApp.db.getRecord('Event', '*',  self.eventId)
            if record:
                actionType = self.action.getType()
                #eventTypeId = forceRef(record.value('eventType_id'))
                #self.eventPurposeId = getEventPurposeId(eventTypeId)
                setDate = forceDateTime(record.value('setDate')) if showTime else forceDate(record.value('setDate'))
                execDate = forceDateTime(record.value('execDate')) if showTime else forceDate(record.value('execDate'))
                if execDate and setDate:
                    if actionType and u'received' in actionType.flatCode.lower():
                        isControlActionReceivedBegDate = QtGui.qApp.isControlActionReceivedBegDate()
                        if isControlActionReceivedBegDate:
                            eventBegDate = forceDateTime(record.value('setDate')) if showTime else forceDate(record.value('setDate'))
                            eventBegDate = toDateTimeWithoutSeconds(eventBegDate)
                            actionBegDate = begDate
                            if eventBegDate != actionBegDate:
                                if isControlActionReceivedBegDate == 1:
                                    message = u'Дата начала случая обслуживания %s не совпадает с датой начала действия Поступление %s. Исправить?'%(forceString(eventBegDate), forceString(actionBegDate))
                                    skippable = True
                                else:
                                    message = u'Дата начала случая обслуживания %s не совпадает с датой начала действия Поступление %s. Необходимо исправить.'%(forceString(eventBegDate), forceString(actionBegDate))
                                    skippable = False
                                result = result and self.checkValueMessage(message, skippable, self.edtBegDate)
                if setDate and endDate:
                    result = result and (endDate >= setDate or self.checkValueMessage(u'Дата выполнения действия %s не должна быть раньше даты начала события % s'%(forceString(endDate), forceString(setDate)), True, self.edtEndDate))
                actionsBeyondEvent = getEventEnableActionsBeyondEvent(self.eventTypeId)
                if execDate and endDate and actionsBeyondEvent:
                    result = result and (execDate >= endDate or self.checkValueMessage(u'Дата выполнения действия %s не должна быть позже даты выполнения события % s'%(forceString(endDate), forceString(execDate)), True if actionsBeyondEvent == 1 else False, self.edtEndDate))
                elif setDate and endDate:
                    currentDate = QDate.currentDate()
                    if currentDate and not secondTry:
                        endDateCur = endDate.date() if showTime else endDate
                        result = result and (currentDate >= endDateCur or self.checkValueMessage(
                            u'Дата выполнения действия %s не должна быть позже текущей даты % s'%(forceString(endDateCur), forceString(currentDate)), True, self.edtEndDate)
                        )
                actionRecord = self.action.getRecord()
                status = forceInt(actionRecord.value('status'))
                actionShowTime = self.action._actionType.showTime
                directionDate = QDateTime(self.edtDirectionDate.date(), self.edtDirectionTime.time()) if actionShowTime else self.edtDirectionDate.date()
                nameActionType = actionType.name
                eventEditDialog = CEventEditDialog(self)
                eventEditDialog.setClientBirthDate(self.clientBirthDate)
                eventEditDialog.setClientDeathDate(self.clientDeathDate)
                eventEditDialog.setEventPurposeId(self.eventPurposeId)
                eventEditDialog.setClientSex(self.clientSex)
                eventEditDialog.setClientAge(self.clientAge)
                eventEditDialog.setEventTypeIdToAction(self.eventTypeId)
                result = result and CEventEditDialog(self).checkActionDataEntered(directionDate, begDate, endDate, None, self.edtDirectionDate, self.edtBegDate, self.edtEndDate, None, 0)
                result = result and CEventEditDialog(self).checkEventActionDateEntered(setDate, execDate, status, directionDate, begDate, endDate, None, self.edtEndDate, self.edtBegDate, None, 0, nameActionType, actionShowTime=actionShowTime, enableActionsBeyondEvent=actionsBeyondEvent)
        result = result and (begDate or self.checkInputMessage(u'дату назначения', False, self.edtBegDate))
        if not secondTry:
            result = result and (endDate or self.checkInputMessage(u'дату выполнения', True, self.edtEndDate))
        result = result and self.checkPlannedEndDate()
        result = result and self.checkActionMorphology()
        result = result and self.checkInfectionDiseases()
        result = result and self.checkVaccinations()
        result = result and self.checkExaminations()
        result = result and self.checkResearches()
        result = result and self.checkInspectionsResult()
        return result


    def checkInfectionDiseases(self):
        result = True
        actionEndDate = self.edtEndDate.date()
        items = self.modelInfectionDiseases._items
        for row, item in enumerate(items):
            diagnosisId = forceRef(item.value('diagnosis_id'))
            MKB = forceString(item.value('MKB'))
            if not diagnosisId and not MKB:
                self.checkInputMessage(u'диагноз', False, self.tblInfectionDiseases, row, self.modelInfectionDiseases.Col_MKB)
                return False
            endDate = forceDate(item.value('endDate'))
            if not endDate and not endDate.isValid():
                self.checkInputMessage(u'дату установления диагноза', False, self.tblInfectionDiseases, row, self.modelInfectionDiseases.Col_EndDate)
                return False
            if actionEndDate and actionEndDate.isValid():
                if endDate > actionEndDate:
                    self.checkValueMessageCritical(u'Заболевание не может быть установлено позднее даты "Выполнено" текущего заключения', False, self.tblInfectionDiseases, row, self.modelInfectionDiseases.Col_EndDate)
                    return False
        return result


    def checkVaccinations(self):
        result = True
        actionEndDate = self.edtEndDate.date()
        items = self.modelVaccinations._items
        for row, item in enumerate(items):
            infectionId = forceRef(item.value('infection_id'))
            if not infectionId:
                self.checkInputMessage(u'инфекцию', False, self.tblVaccinations, row, self.modelVaccinations.Col_InfectionId)
                return False
            vaccinationType = forceStringEx(item.value('vaccinationType'))
            if not vaccinationType:
                self.checkInputMessage(u'тип прививки', False, self.tblVaccinations, row, self.modelVaccinations.Col_VaccinationType)
                return False
            date = forceDate(item.value('date'))
            if not date and not date.isValid():
                self.checkInputMessage(u'дату прививки', False, self.tblVaccinations, row, self.modelVaccinations.Col_Date)
                return False
            if actionEndDate and actionEndDate.isValid():
                if date > actionEndDate:
                    self.checkValueMessageCritical(u'Прививка не может быть сделана позднее даты "Выполнено" текущего заключения', False, self.tblVaccinations, row, self.modelVaccinations.Col_Date)
                    return False
        return result


    def checkExaminations(self):
        result = True
        actionEndDate = self.edtEndDate.date()
        items = self.modelStatusActions._items
        for row, item in enumerate(items):
            postId = forceRef(item.value('post_id'))
            if not postId:
                self.checkInputMessage(u'должность врача по осмотру', False, self.tblStatusActions, row, self.modelStatusActions.Col_PostId)
                return False
            lastName = forceStringEx(item.value('lastName'))
            if not lastName:
                self.checkInputMessage(u'фамилию врача по осмотру', False, self.tblStatusActions, row, self.modelStatusActions.Col_LastName)
                return False
            firstName = forceStringEx(item.value('firstName'))
            if not firstName:
                self.checkInputMessage(u'имя врача по осмотру', False, self.tblStatusActions, row, self.modelStatusActions.Col_FirstName)
                return False
            result = forceStringEx(item.value('result'))
            if not result:
                self.checkInputMessage(u'заключение по осмотру', False, self.tblStatusActions, row, self.modelStatusActions.Col_Result)
                return False
            date = forceDate(item.value('date'))
            if not date and not date.isValid():
                self.checkInputMessage(u'дату осмотра', False, self.tblStatusActions, row, self.modelStatusActions.Col_Date)
                return False
            if actionEndDate and actionEndDate.isValid():
                if date > actionEndDate:
                    self.checkValueMessageCritical(u'Осмотр не может быть проведен позднее даты "Выполнено" текущего заключения', False, self.tblStatusActions, row, self.modelStatusActions.Col_Date)
                    return False
        return result


    def checkResearches(self):
        result = True
        actionEndDate = self.edtEndDate.date()
        items = self.modelLabDiagnosticActions._items
        for row, item in enumerate(items):
            serviceId = forceRef(item.value('service_id'))
            if not serviceId:
                self.checkInputMessage(u'услугу по исследованию', False, self.tblLabDiagnosticActions, row, self.modelLabDiagnosticActions.Col_ServiceId)
                return False
            result = forceStringEx(item.value('result'))
            if not result:
                self.checkInputMessage(u'заключение по осмотру', False, self.tblLabDiagnosticActions, row, self.modelLabDiagnosticActions.Col_Result)
                return False
            date = forceDate(item.value('date'))
            if not date and not date.isValid():
                self.checkInputMessage(u'дату исследования', False, self.tblLabDiagnosticActions, row, self.modelLabDiagnosticActions.Col_Date)
                return False
            if actionEndDate and actionEndDate.isValid():
                if date > actionEndDate:
                    self.checkValueMessageCritical(u'Исследование не может быть проведено позднее даты "Выполнено" текущего заключения', False, self.tblLabDiagnosticActions, row, self.modelLabDiagnosticActions.Col_Date)
                    return False
        items = self.modelToolDiagnosticActions._items
        for row, item in enumerate(items):
            serviceId = forceRef(item.value('service_id'))
            if not serviceId:
                self.checkInputMessage(u'услугу по исследованию', False, self.tblToolDiagnosticActions, row, self.modelToolDiagnosticActions.Col_ServiceId)
                return False
            result = forceStringEx(item.value('result'))
            if not result:
                self.checkInputMessage(u'заключение по осмотру', False, self.tblToolDiagnosticActions, row, self.modelToolDiagnosticActions.Col_Result)
                return False
            date = forceDate(item.value('date'))
            if not date and not date.isValid():
                self.checkInputMessage(u'дату исследования', False, self.tblToolDiagnosticActions, row, self.modelToolDiagnosticActions.Col_Date)
                return False
            if actionEndDate and actionEndDate.isValid():
                if date > actionEndDate:
                    self.checkValueMessageCritical(u'Исследование не может быть проведено позднее даты "Выполнено" текущего заключения', False, self.tblToolDiagnosticActions, row, self.modelToolDiagnosticActions.Col_Date)
                    return False
        return result


    def checkInspectionsResult(self):
        result = True
        actionPersonId = self.cmbPerson.value()
        execPersonId = forceRef(self.recordEvent.value('execPerson_id'))
        personChif = []
        if actionPersonId:
            personChif.append(actionPersonId)
        if execPersonId:
            personChif.append(execPersonId)
        items = self.modelDiagnostics._items
        for row, item in enumerate(items):
            specialityId = forceRef(item.value('speciality_id'))
            if not specialityId:
                self.checkInputMessage(u'специальность', False, self.tblInspectionsResult, row, self.modelDiagnostics.getColIndex('speciality_id', None))
                return False
            personId = forceRef(item.value('person_id'))
            if not personId:
                self.checkInputMessage(u'врача', False, self.tblInspectionsResult, row, self.modelDiagnostics.getColIndex('person_id', None))
                return False
            sceneId = forceRef(item.value('scene_id'))
            if not sceneId:
                self.checkInputMessage(u'место визита', False, self.tblInspectionsResult, row, self.modelDiagnostics.getColIndex('scene_id', None))
                return False
            visitTypeId = forceRef(item.value('visitType_id'))
            if not visitTypeId:
                self.checkInputMessage(u'тип визита', False, self.tblInspectionsResult, row, self.modelDiagnostics.getColIndex('visitType_id', None))
                return False
#            healthGroupId = forceRef(item.value('healthGroup_id'))
#            if not healthGroupId:
#                self.checkInputMessage(u'ГрЗд', False, self.tblInspectionsResult, row, self.modelDiagnostics.getColIndex('healthGroup_id', None))
#                return False
            MKB = forceString(item.value('MKB'))
            if not MKB:
                self.checkInputMessage(u'диагноз', False, self.tblInspectionsResult, row, self.modelDiagnostics.getColIndex('MKB', None))
                return False
            resultId = forceRef(item.value('result_id'))
            if not resultId:
                self.checkInputMessage(u'результат', False, self.tblInspectionsResult, row, self.modelDiagnostics.getColIndex('result_id', None))
                return False
            if personChif:
                if personId not in personChif:
                    self.checkValueMessageCritical(u'Врач осмотра не соответствует Исполнителю текущего заключения!', False, self.tblInspectionsResult, row, self.modelDiagnostics.getColIndex('person_id', None))
                    return False
        return result


    def checkActionMorphology(self):
        actionStatus = self.cmbStatus.value()
        if QtGui.qApp.defaultMorphologyMKBIsVisible() \
           and actionStatus in (CActionStatus.finished, CActionStatus.withoutResult):
            action = self.action
            actionType = action.getType()
            defaultMKB = actionType.defaultMKB
            isMorphologyRequired = actionType.isMorphologyRequired
            items = self.modelInfectionDiseases.items()
            for item in items:
                morphologyMKB = forceStringEx(item.value('morphologyMKB'))
                if (not bool(re.match('M\d{4}/', forceStringEx(morphologyMKB)))) and defaultMKB > 0 and isMorphologyRequired > 0:
                    if actionStatus == CActionStatus.withoutResult and isMorphologyRequired == 2:
                        return True
                    skippable = True if isMorphologyRequired == 1 else False
                    message = u'Необходимо ввести корректную морфологию диагноза действия `%s`' % actionType.name
                    return self.checkValueMessage(message, skippable, self.cmbMorphologyMKB)
        return True


    def checkPlannedEndDate(self):
        action = self.action
        if action:
            actionType = action.getType()
            if actionType and actionType.isPlannedEndDateRequired in [CActionType.dpedControlMild, CActionType.dpedControlHard]:
                if not self.edtPlannedEndDate.date():
                    skippable = True if actionType.isPlannedEndDateRequired == CActionType.dpedControlMild else False
                    message = u'Необходимо указать Плановую дату выполнения у действия %s'%(actionType.name)
                    return self.checkValueMessage(message, skippable, self.edtPlannedEndDate)
        return True


    def setPersonId(self, personId):
        self.personId = personId
        record = QtGui.qApp.db.getRecord('Person', 'speciality_id, tariffCategory_id, SNILS, showTypeTemplate',  self.personId)
        if record:
            self.personSpecialityId     = forceRef(record.value('speciality_id'))
            self.personTariffCategoryId = forceRef(record.value('tariffCategory_id'))
            self.personSNILS            = forceStringEx(record.value('SNILS'))
            self.showTypeTemplate       = forceInt(record.value('showTypeTemplate'))
            self.actionTemplateCache.setPersonSNILS(self.personSNILS)
            self.actionTemplateCache.setShowTypeTemplate(self.showTypeTemplate)


    def getEventInfo(self, context):
        return None


    def setTextEdits(self):
        self.setProperty(QVariant(self.edtElectronicMedicalBookNumber.text()), u'ME:medical_book_number')
        self.setProperty(QVariant(self.edtCommentResult.toPlainText()), u'ME:comment')


    def updateDiagnosisDirectionMSI_Info(self, value, widgetInfo):
        if value[-1:] == '.':
            value = value[:-1]
        diagName = forceString(QtGui.qApp.db.translate('MKB', 'DiagID', value, 'DiagName'))
        if diagName:
            widgetInfo.setText(diagName)
        else:
            widgetInfo.clear()


    def editAction(self, actionId):
        dialog = CActionEditDialog(self)
        try:
            dialog.load(actionId)
            if dialog.exec_():
                return dialog.itemId()
            return None
        finally:
            dialog.deleteLater()


    def deleteAction(self, actionId):
        if QtGui.QMessageBox.question(self,
                u'Удаление Действия!', u'Вы действительно хотите удалить Действие?',
                QtGui.QMessageBox.Yes|QtGui.QMessageBox.No,
                QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
            db = QtGui.qApp.db
            table = db.table('Action')
            tableEvent = db.table('Event')
            record = db.getRecordEx(table, '*', [table['id'].eq(actionId), table['deleted'].eq(0)])
            payStatusAction = forceInt(record.value('payStatus')) if record else 0
            isPayStatus = forceBool(payStatusAction)
            payStatusEvent = False
            if self.eventId and not isPayStatus:
                recordEvent = db.getRecordEx(tableEvent, [tableEvent['payStatus'], tableEvent['id']], [tableEvent['id'].eq(self.eventId), tableEvent['deleted'].eq(0)])
                payStatusEvent = forceInt(recordEvent.value('payStatus')) if recordEvent else 0
            isPayStatus = isPayStatus and forceBool(payStatusEvent)
            if isPayStatus:
                message = u'%s включено в счёт\nи его данные не могут быть изменены!'%(u'Данное Действие' if payStatusAction else (u'Событие, содержащее данное Действие,' if payStatusEvent else u'Данное Действие'))
                QtGui.QMessageBox.critical(self, u'Внимание!', message)
                return
            createPersonId = forceRef(record.value('createPerson_id')) if record else None
            if actionId and createPersonId and QtGui.qApp.userId == createPersonId and not isPayStatus:
                tableActionProperty = db.table('ActionProperty')
                filter = [tableActionProperty['action_id'].eq(actionId), tableActionProperty['deleted'].eq(0)]
                db.deleteRecord(tableActionProperty, filter)

                tableActionExecutionPlan = db.table('Action_ExecutionPlan')
                filter = [tableActionExecutionPlan['master_id'].eq(actionId), tableActionExecutionPlan['deleted'].eq(0)]
                db.deleteRecord(tableActionExecutionPlan, filter)

                tableStockMotion = db.table('StockMotion')
                tableActionNR = db.table('Action_NomenclatureReservation')
                filter = [tableActionNR['action_id'].eq(actionId)]
                reservationIdList = db.getDistinctIdList(tableActionNR, [tableActionNR['reservation_id']], filter)
                if reservationIdList:
                    filter = [tableStockMotion['id'].inlist(reservationIdList), tableStockMotion['deleted'].eq(0)]
                    db.deleteRecord(tableStockMotion, filter)

                filter = [table['id'].eq(actionId), table['deleted'].eq(0)]
                stockMotionIdList = db.getDistinctIdList(table, [table['stockMotion_id']], filter)
                if stockMotionIdList:
                    tableStockMotionItem = db.table('StockMotion_Item')
                    filter = [tableStockMotionItem['master_id'].inlist(stockMotionIdList), tableStockMotionItem['deleted'].eq(0)]
                    db.deleteRecord(tableStockMotionItem, filter)
                    filter = [tableStockMotion['id'].inlist(stockMotionIdList), tableStockMotion['deleted'].eq(0)]
                    db.deleteRecord(tableStockMotion, filter)

                db.deleteRecord(table, [table['id'].eq(actionId)])
                return True
        return False


    def on_comboBoxChangedEx(self, index):
        if self.focusWidget() in [ self.cmbMKBFromClientDiseasesFilter,
                                   self.cmbMKBToClientDiseasesFilter
                                 ]:
            pass
            #self.setIsDirty()


    def on_checkBoxChangedEx(self, state):
        if self.focusWidget() in [ self.chkExecActionsClientDiseasesFilter,
                                   self.chkPreliminaryClientDiseasesFilter,
                                   self.chkConcomitantClientDiseasesFilter,
                                   self.chkExecActionsClientVaccinationsFilter,
                                   self.chkExecActionsClientStatusActionsFilter,
                                   self.chkExecActionsDiagnosticActionsFilter
                                 ]:
            pass
            #self.setIsDirty()


    def on_dateEditChangedEx(self, date):
        if self.focusWidget() in [ self.edtBegDateClientDiseasesFilter,
                                   self.edtEndDateClientDiseasesFilter,
                                   self.edtBegDateClientVaccinationsFilter,
                                   self.edtEndDateClientVaccinationsFilter,
                                   self.edtBegDateClientStatusActionsFilter,
                                   self.edtEndDateClientStatusActionsFilter,
                                   self.edtBegDateDiagnosticActionsFilter,
                                   self.edtEndDateDiagnosticActionsFilter
                                  ]:
            pass
            #self.setIsDirty()


    def on_dateEditChangedAction(self, date):
        if self.action:
            nameCols = {self.edtBegDate:u'begDate',
                        self.edtEndDate:u'endDate',
                        self.edtDirectionDate:u'directionDate',
                        self.edtPlannedEndDate:u'plannedEndDate'
                       }
            record = self.action.getRecord()
            if record and self.focusWidget() in nameCols.keys():
                name = nameCols.get(self.focusWidget(), '')
                if name and forceDate(record.value(name)) != date:
                    self.setIsDirty()


    def on_abstractdataModelDataChangedEx(self, topLeft,  bottomRight):
        if self.focusWidget() in [ self.tblDiagnosticActionProperties,
                                   self.tblClientDiagnosticActionProperties,
                                   self.tblClientDiagnosticActions,
                                   self.tblClientStatusActionProperties,
                                   self.tblStatusActionProperties,
                                   self.tblClientStatusActions,
                                   self.tblClientVaccinations,
                                   self.tblClientDiseases
                                 ]:
            pass
            #self.setIsDirty()


    def on_abstractdataModelDataChanged(self, topLeft,  bottomRight):
        self.setIsDirty()


    def on_doubleSpinBoxChanged(self, value):
        self.setIsDirty()


    def setupDirtyCatherForObject(self, obj, exclude):
        if obj in exclude:
            return
        for child in obj.children():
            if isinstance(child, QtGui.QLabel) or child in exclude:
                pass
            elif isinstance(child, CDateEdit):
                if child.objectName() in {u'edtBegDateClientDiseasesFilter':0,
                    u'edtEndDateClientDiseasesFilter':1,
                    u'edtBegDateClientVaccinationsFilter':2,
                    u'edtEndDateClientVaccinationsFilter':3,
                    u'edtBegDateClientStatusActionsFilter':4,
                    u'edtEndDateClientStatusActionsFilter':5,
                    u'edtBegDateDiagnosticActionsFilter':6,
                    u'edtEndDateDiagnosticActionsFilter':7}.keys():
                    self.connect(child, SIGNAL('dateChanged(QDate)'), self.on_dateEditChangedEx)
                elif child.objectName() in {u'edtBegDate':0,
                      u'edtEndDate':1,
                      u'edtDirectionDate':2,
                      u'edtPlannedEndDate':3}.keys():
                    self.connect(child, SIGNAL('dateChanged(QDate)'), self.on_dateEditChangedAction)
                else:
                    self.connect(child, SIGNAL('dateChanged(QDate)'), self.on_dateEditChanged)
            elif isinstance(child, QtGui.QLineEdit):
                self.connect(child, SIGNAL('textChanged(QString)'), self.on_lineEditChanged)
            elif isinstance(child, QtGui.QTextEdit):
                self.connect(child, SIGNAL('textChanged()'), self.on_textEditChanged)
            elif isinstance(child, QtGui.QDateEdit):
                if child.objectName() in {u'edtBegDateClientDiseasesFilter':0,
                    u'edtEndDateClientDiseasesFilter':1,
                    u'edtBegDateClientVaccinationsFilter':2,
                    u'edtEndDateClientVaccinationsFilter':3,
                    u'edtBegDateClientStatusActionsFilter':4,
                    u'edtEndDateClientStatusActionsFilter':5,
                    u'edtBegDateDiagnosticActionsFilter':6,
                    u'edtEndDateDiagnosticActionsFilter':7}.keys():
                    self.connect(child, SIGNAL('dateChanged(QDate)'), self.on_dateEditChangedEx)
                elif child.objectName() in {u'edtBegDate':0,
                      u'edtEndDate':1,
                      u'edtDirectionDate':2,
                      u'edtPlannedEndDate':3}.keys():
                    self.connect(child, SIGNAL('dateChanged(QDate)'), self.on_dateEditChangedAction)
                else:
                    self.connect(child, SIGNAL('dateChanged(QDate)'), self.on_dateEditChanged)
            elif isinstance(child, QtGui.QComboBox):
                if child.objectName() in {u'cmbMKBFromClientDiseasesFilter':0,
                    u'cmbMKBToClientDiseasesFilter':1}.keys():
                    self.connect(child, SIGNAL('currentIndexChanged(int)'), self.on_comboBoxChangedEx)
                else:
                    self.connect(child, SIGNAL('currentIndexChanged(int)'), self.on_comboBoxChanged)
            elif isinstance(child, QtGui.QCheckBox):
                if child.objectName() in {u'chkExecActionsClientDiseasesFilter':0,
                    u'chkPreliminaryClientDiseasesFilter':1,
                    u'chkConcomitantClientDiseasesFilter':2,
                    u'chkExecActionsClientVaccinationsFilter':3,
                    u'chkExecActionsClientStatusActionsFilter':4,
                    u'chkExecActionsDiagnosticActionsFilter':5}.keys():
                    self.connect(child, SIGNAL('stateChanged(int)'), self.on_checkBoxChangedEx)
                else:
                    self.connect(child, SIGNAL('stateChanged(int)'), self.on_checkBoxChanged)
            elif isinstance(child, QtGui.QSpinBox):
                self.connect(child, SIGNAL('valueChanged(int)'), self.on_spinBoxChanged)
            elif isinstance(child, QtGui.QDoubleSpinBox):
                self.connect(child, SIGNAL('valueChanged(double)'), self.on_doubleSpinBoxChanged)
            elif isinstance(child, QAbstractItemModel):
                if child.objectName() in {u'modelDiagnosticActionProperties':0,
                    u'modelClientDiagnosticActionProperties':1,
                    u'modelClientDiagnosticActions':2,
                    u'modelClientStatusActionProperties':3,
                    u'modelStatusActionProperties':4,
                    u'modelClientStatusActions':5,
                    u'modelClientVaccinations':6,
                    u'modelClientDiseases':7}.keys():
                    self.connect(child, SIGNAL('dataChanged(QModelIndex, QModelIndex)'), self.on_abstractdataModelDataChangedEx)
                else:
                    self.connect(child, SIGNAL('dataChanged(QModelIndex, QModelIndex)'), self.on_abstractdataModelDataChanged)
            else:
                self.setupDirtyCatherForObject(child, exclude)


    @pyqtSignature('QAbstractButton*')
    def on_btnButtonBoxClientDiseasesFilter_clicked(self, button):
        buttonCode = self.btnButtonBoxClientDiseasesFilter.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.on_clientDiseasesFilter_apply()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_clientDiseasesFilter_reset()


    def on_clientDiseasesFilter_reset(self):
        self.edtBegDateClientDiseasesFilter.setDate(QDate())
        self.edtEndDateClientDiseasesFilter.setDate(self.edtEndDate.date())
        self.chkExecActionsClientDiseasesFilter.setChecked(True)
        self.cmbMKBFromClientDiseasesFilter.setText(u'A00')
        self.cmbMKBToClientDiseasesFilter.setText(u'B99')
        self.cmbMKBFromClientDiseasesFilter.setFilter(u''' MKB.DiagID >= 'A00' AND MKB.DiagID <= 'B99' ''')
        self.cmbMKBFromClientDiseasesFilter.ICDTreePopup=None
        self.cmbMKBToClientDiseasesFilter.setFilter(u''' MKB.DiagID >= 'A00' AND MKB.DiagID <= 'B99' ''')
        self.cmbMKBToClientDiseasesFilter.ICDTreePopup=None
        self.chkPreliminaryClientDiseasesFilter.setChecked(False)
        self.chkConcomitantClientDiseasesFilter.setChecked(False)
        #self.getClientDiseasesFilter()


    def getClientDiseasesFilter(self):
        self.clientDiseasesFilter = {}
        self.clientDiseasesFilter['begDateClientDiseases'] = self.edtBegDateClientDiseasesFilter.date()
        self.clientDiseasesFilter['endDateClientDiseases'] = self.edtEndDateClientDiseasesFilter.date()
        self.clientDiseasesFilter['execActionsClientDiseases'] = self.chkExecActionsClientDiseasesFilter.isChecked()
        self.clientDiseasesFilter['MKBFromClientDiseases'] = MKBwithoutSubclassification(unicode(self.cmbMKBFromClientDiseasesFilter.text()))
        self.clientDiseasesFilter['MKBToClientDiseases'] = MKBwithoutSubclassification(unicode(self.cmbMKBToClientDiseasesFilter.text()))
        self.clientDiseasesFilter['MKBPreliminaryClientDiseases'] = self.chkPreliminaryClientDiseasesFilter.isChecked()
        self.clientDiseasesFilter['MKBConcomitantClientDiseases'] = self.chkConcomitantClientDiseasesFilter.isChecked()


    def on_clientDiseasesFilter_apply(self):
        self.updateClientDiseases()
        self.focusClientDiseases()


    def updateClientDiseases(self):
        self.getClientDiseasesFilter()
        self.loadClientDiseases(self.eventId, self.clientId)


    def focusClientDiseases(self):
        self.tblClientDiseases.setFocus(Qt.TabFocusReason)


    @pyqtSignature('bool')
    def on_chkExecActionsClientVaccinationsFilter_toggled(self, checked):
        self.btnInfectionsClientVaccinationsFilter.setEnabled(not self.chkExecActionsClientVaccinationsFilter.isChecked())


    @pyqtSignature('bool')
    def on_chkExecActionsClientDiseasesFilter_toggled(self, checked):
        self.setMKBClientDiseasesFilterReadOnly()


    def setMKBClientDiseasesFilterReadOnly(self):
        isChecked = self.chkExecActionsClientDiseasesFilter.isChecked()
        self.cmbMKBFromClientDiseasesFilter.setReadOnly(isChecked)
        self.cmbMKBToClientDiseasesFilter.setReadOnly(isChecked)


    def getDiagnosisTypeId(self):
        db = QtGui.qApp.db
        table = db.table('rbDiagnosisType')
        self.baseDiagnosisTypeIdList = db.getDistinctIdList(table, [table['id']], [table['code'].inlist([u'1', u'2', u'60'])])
        return self.baseDiagnosisTypeIdList


    def loadClientDiseases(self, masterId, clientId):
        currentIndex = self.tblClientDiseases.currentIndex()
        diagnosticCond = []
        db = QtGui.qApp.db
        cols = 'Diagnosis.id'
        table = self.modelClientDiseases._table
        tableEvent = db.table('Event')
        tableDiagnosis = db.table('Diagnosis')
        tableDiagnosisType = db.table('rbDiagnosisType')
        tableHurtTypeMKB = db.table('rbHurtType_MKB')
        queryTable = table.innerJoin(tableEvent, tableEvent['id'].eq(table['event_id']))
        queryTable = queryTable.innerJoin(tableDiagnosis, db.joinOr([tableDiagnosis['id'].eq(table['diagnosis_id']), tableDiagnosis['deleted'].eq(0)]))
        cond = [tableEvent['client_id'].eq(clientId),
                tableDiagnosis['client_id'].eq(clientId),
                table[self.modelClientDiseases._masterIdFieldName].ne(masterId),
                tableEvent['deleted'].eq(0),
                table['endDate'].isNotNull(),
                table['deleted'].eq(0)
                ]
        if self.modelInfectionDiseases.checkedIdList:
            cond.append(table['id'].notInlist(self.modelInfectionDiseases.checkedIdList))
        infectionDiseasesIdList = self.modelInfectionDiseases.getItemIdList()
        if infectionDiseasesIdList:
            cond.append(table['id'].notInlist(infectionDiseasesIdList))
#        if self.modelClientDiseases._filter:
#            cond.append(self.modelClientDiseases._filter)
        begDateClientDiseases = self.clientDiseasesFilter.get('begDateClientDiseases')
        endDateClientDiseases = self.clientDiseasesFilter.get('endDateClientDiseases')
        if begDateClientDiseases:
            cond.append(table['endDate'].dateGe(begDateClientDiseases))
        if endDateClientDiseases:
            cond.append(table['endDate'].dateLe(endDateClientDiseases))
        diagnosisTypeIdList = self.getDiagnosisTypeId()
        execActionsClientDiseases = self.clientDiseasesFilter.get('execActionsClientDiseases')
        if execActionsClientDiseases:
            hurtTypeMKBList = []
            hurtTypeId = self.cmbHurtType.value()
            if hurtTypeId:
                hurtTypeRecords = db.getDistinctRecordList(tableHurtTypeMKB, [tableHurtTypeMKB['MKB']], [tableHurtTypeMKB['master_id'].eq(hurtTypeId)], tableHurtTypeMKB['MKB'].name())
                for hurtTypeRecord in hurtTypeRecords:
                    hurtTypeMKB = forceStringEx(hurtTypeRecord.value('MKB'))
                    if hurtTypeMKB and hurtTypeMKB not in hurtTypeMKBList:
                        hurtTypeMKBList.append(hurtTypeMKB)
                if hurtTypeMKBList:
                    #queryTable = queryTable.innerJoin(tableHurtTypeMKB, tableHurtTypeMKB['MKB'].eq(tableDiagnosis['MKB']))
                    cond.append(tableDiagnosis['MKB'].inlist(hurtTypeMKBList))
        MKBFromClientDiseases = self.clientDiseasesFilter.get('MKBFromClientDiseases')
        MKBToClientDiseases = self.clientDiseasesFilter.get('MKBToClientDiseases')
        if not MKBToClientDiseases:
            MKBToClientDiseases = u'B99'
        if not MKBFromClientDiseases:
            MKBFromClientDiseases = u'A00'
        if MKBFromClientDiseases or MKBToClientDiseases:
            diagnosisTypeCodeList = []
            dopDiagnosisTypeIdList = []
            MKBPreliminaryClientDiseases = self.clientDiseasesFilter.get('MKBPreliminaryClientDiseases')
            MKBConcomitantClientDiseases = self.clientDiseasesFilter.get('MKBConcomitantClientDiseases')
            if MKBPreliminaryClientDiseases:
                diagnosisTypeCodeList.append(u'7')
            if MKBConcomitantClientDiseases:
                diagnosisTypeCodeList.append(u'9')
            if MKBConcomitantClientDiseases and MKBPreliminaryClientDiseases:
                diagnosisTypeCodeList.append(u'11')
            if diagnosisTypeCodeList:
                dopDiagnosisTypeIdList = db.getDistinctIdList(tableDiagnosisType, [tableDiagnosisType['id']], [tableDiagnosisType['code'].inlist(diagnosisTypeCodeList)])
            if dopDiagnosisTypeIdList:
                diagnosisTypeIdList.extend(dopDiagnosisTypeIdList)
            if MKBFromClientDiseases:
                cond.append(tableDiagnosis['MKB'].ge(MKBFromClientDiseases))
            if MKBToClientDiseases:
                cond.append(tableDiagnosis['MKB'].le(MKBToClientDiseases))
        if diagnosisTypeIdList:
            cond.append(table['diagnosisType_id'].inlist(diagnosisTypeIdList))
#        if self.modelClientDiseases._idxFieldName:
#            order = [table[self.modelClientDiseases._idxFieldName].name() + u'ASC', table['endDate'].name() + u'DESC']
#        else:
        order = [table['endDate'].name() + u'DESC']
        diagnosisIdList = db.getDistinctIdList(queryTable, cols, cond, order)
        diagnosticRecords = []
        if diagnosisIdList:
            queryTable = table.innerJoin(tableEvent, tableEvent['id'].eq(table['event_id']))
            diagnosticCond = [tableEvent['client_id'].eq(clientId),
                              table['diagnosis_id'].inlist(diagnosisIdList),
                              table[self.modelClientDiseases._masterIdFieldName].ne(masterId),
                              tableEvent['deleted'].eq(0),
                              table['endDate'].isNotNull(),
                              table['deleted'].eq(0)
                             ]
            if self.modelInfectionDiseases.checkedIdList:
                diagnosticCond.append(table['id'].notInlist(self.modelInfectionDiseases.checkedIdList))
            if infectionDiseasesIdList:
                diagnosticCond.append(table['id'].notInlist(infectionDiseasesIdList))
#            if self.modelClientDiseases._filter:
#                diagnosticCond.append(self.modelClientDiseases._filter)
            begDateClientDiseases = self.clientDiseasesFilter.get('begDateClientDiseases')
            endDateClientDiseases = self.clientDiseasesFilter.get('endDateClientDiseases')
            if begDateClientDiseases:
                diagnosticCond.append(table['endDate'].dateGe(begDateClientDiseases))
            if endDateClientDiseases:
                diagnosticCond.append(table['endDate'].dateLe(endDateClientDiseases))
            if diagnosisTypeIdList:
                diagnosticCond.append(table['diagnosisType_id'].inlist(diagnosisTypeIdList))
            diagnosticRecords = db.getDistinctRecordList(queryTable, u'Diagnostic.*, (SELECT Diagnosis.MKB FROM Diagnosis WHERE Diagnosis.id = Diagnostic.diagnosis_id AND Diagnosis.deleted = 0 LIMIT 1) AS MKB', diagnosticCond, order)
        diagnosticDiseasesItems = []
        for diagnosticRecord in diagnosticRecords:
            diagnosticEndDate = forceDate(diagnosticRecord.value('endDate'))
            diagnosticMKBId = forceRef(diagnosticRecord.value('diagnosis_id'))
            diagnosticMKB = forceStringEx(diagnosticRecord.value('MKB'))
            diagnosticTypeId = forceRef(diagnosticRecord.value('diagnosisType_id'))
            isDiagnosticDiseases = False
            for diagnosticDiseasesItem in diagnosticDiseasesItems:
                infectionDiseasesEndDate = forceDate(diagnosticDiseasesItem.value('endDate'))
                infectionDiseasesMKBId = forceRef(diagnosticDiseasesItem.value('diagnosis_id'))
                infectionDiseasesMKB = forceStringEx(diagnosticDiseasesItem.value('MKB'))
                infectionDiagnosisTypeId = forceRef(diagnosticDiseasesItem.value('diagnosisType_id'))
                if diagnosticTypeId == infectionDiagnosisTypeId and diagnosticEndDate == infectionDiseasesEndDate and (diagnosticMKBId == infectionDiseasesMKBId or diagnosticMKB == infectionDiseasesMKB):
                    isDiagnosticDiseases = True
                    continue
            if not isDiagnosticDiseases:
                diagnosticDiseasesItems.append(diagnosticRecord)
        clientDiseasesItems = []
        infectionDiseasesItems = self.modelInfectionDiseases.items()
        if infectionDiseasesItems:
            for diagnosticRecord in diagnosticDiseasesItems:
                diagnosticEndDate = forceDate(diagnosticRecord.value('endDate'))
                diagnosticMKBId = forceRef(diagnosticRecord.value('diagnosis_id'))
                diagnosticMKB = forceStringEx(diagnosticRecord.value('MKB'))
                isInfectionDiseasesItem = False
                for infectionDiseasesItem in infectionDiseasesItems:
                    infectionDiseasesEndDate = forceDate(infectionDiseasesItem.value('endDate'))
                    infectionDiseasesMKBId = forceRef(infectionDiseasesItem.value('diagnosis_id'))
                    infectionDiseasesMKB = forceStringEx(infectionDiseasesItem.value('MKB'))
                    if diagnosticEndDate == infectionDiseasesEndDate and (diagnosticMKBId == infectionDiseasesMKBId or diagnosticMKB == infectionDiseasesMKB):
                        isInfectionDiseasesItem = True
                        continue
                if not isInfectionDiseasesItem:
                    clientDiseasesItems.append(diagnosticRecord)
        else:
            clientDiseasesItems = diagnosticDiseasesItems
        self.modelClientDiseases._items = clientDiseasesItems
        if self.modelClientDiseases._extColsPresent:
            extSqlFields = []
            for col in self.modelClientDiseases._cols:
                if col.external():
                    fieldName = col.fieldName()
                    if fieldName not in cols:
                        extSqlFields.append(QtSql.QSqlField(fieldName, col.valueType()))
            if extSqlFields:
                for item in self.modelClientDiseases._items:
                    for field in extSqlFields:
                        item.append(field)
                        if field.name() == u'include':
                            item.setValue(field.name(), toVariant(False))
                        elif field.name() == u'MKB':
                            item.setValue(field.name(), toVariant(self.modelClientDiseases.getMKBToDiagnosis(forceRef(item.value('diagnosis_id')))))
        self.modelClientDiseases.reset()
        self.tblClientDiseases.setCurrentIndex(currentIndex)


    @pyqtSignature('QAbstractButton*')
    def on_btnButtonBoxClientVaccinationsFilter_clicked(self, button):
        buttonCode = self.btnButtonBoxClientVaccinationsFilter.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.on_clientVaccinationsFilter_apply()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_clientVaccinationsFilter_reset()


    def on_clientVaccinationsFilter_reset(self):
        self.edtBegDateClientVaccinationsFilter.setDate(QDate())
        self.edtEndDateClientVaccinationsFilter.setDate(self.edtEndDate.date())
        self.chkExecActionsClientVaccinationsFilter.setChecked(True)
        self.selectInfectionIdList = []
        self.lblInfectionList.setText(u'')


    def getClientVaccinationsFilter(self):
        self.clientVaccinationsFilter = {}
        self.clientVaccinationsFilter['begDateClientVaccinations'] = self.edtBegDateClientVaccinationsFilter.date()
        self.clientVaccinationsFilter['endDateClientVaccinations'] = self.edtEndDateClientVaccinationsFilter.date()
        self.clientVaccinationsFilter['execActionsClientVaccinations'] = self.chkExecActionsClientVaccinationsFilter.isChecked()


    def on_clientVaccinationsFilter_apply(self):
        self.updateClientVaccinations()
        self.focusClientVaccinations()


    def updateClientVaccinations(self):
        self.getClientVaccinationsFilter()
        self.loadClientVaccinations(self.itemId(), self.clientId)


    def focusClientVaccinations(self):
        self.tblClientVaccinations.setFocus(Qt.TabFocusReason)


    @pyqtSignature('')
    def on_btnInfectionsClientVaccinationsFilter_clicked(self):
        dialog = CRBInfectionTableDialog(self, 'rbInfection')
        dialog.setWindowTitle(u'Инфекции')
        dialog.setSelectedItemIdList(self.selectInfectionIdList)
        if dialog.exec_():
            self.selectInfectionIdList = dialog.selectedItemIdList()
            self.lblInfectionList.setText(dialog.formatSelectedItemIdList())


    def loadClientVaccinations(self, masterId, clientId):
        currentIndex = self.tblClientVaccinations.currentIndex()
        db = QtGui.qApp.db
        self.modelClientVaccinations._items = []
#        table = self.modelClientVaccinations._table
        tableAction = db.table('Action')
        tableEvent = db.table('Event')
        tableActionMEVaccination = db.table('Action_ME_Vaccination')
        tableHurtTypeInfection = db.table('rbHurtType_Infection')
        tableInfectionIdentification = db.table('rbInfection_Identification')
        tableAccountingSystem = db.table('rbAccountingSystem')
#        queryTable = table.innerJoin(tableAction, tableAction['id'].eq(table['master_id']))
#        queryTable = queryTable.innerJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
        begDateClientVaccinations = self.clientVaccinationsFilter.get('begDateClientVaccinations')
        endDateClientVaccinations = self.clientVaccinationsFilter.get('endDateClientVaccinations')
        execActionsClientVaccinations = self.clientVaccinationsFilter.get('execActionsClientVaccinations')
        # --
        tableClientVaccination = db.table('ClientVaccination')
        tableInfectionVaccine = db.table('rbInfection_rbVaccine')
        tableRBInfection = db.table('rbInfection')
        queryTable = tableClientVaccination.innerJoin(tableInfectionVaccine, tableInfectionVaccine['vaccine_id'].eq(tableClientVaccination['vaccine_id']))
        queryTable = queryTable.innerJoin(tableRBInfection, tableRBInfection['id'].eq(tableInfectionVaccine['infection_id']))
        queryTableME = tableActionMEVaccination.innerJoin(tableRBInfection, tableRBInfection['id'].eq(tableActionMEVaccination['infection_id']))
        queryTableME = queryTableME.innerJoin(tableAction, tableAction['id'].eq(tableActionMEVaccination['master_id']))
        queryTableME = queryTableME.innerJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
        condFilter = []
        condMEFilter = []
        if begDateClientVaccinations:
            condFilter.append(tableClientVaccination['datetime'].dateGe(begDateClientVaccinations))
            condMEFilter.append(tableActionMEVaccination['date'].dateGe(begDateClientVaccinations))
        if endDateClientVaccinations:
            condFilter.append(tableClientVaccination['datetime'].dateLe(endDateClientVaccinations))
            condMEFilter.append(tableActionMEVaccination['date'].dateLe(endDateClientVaccinations))
        condFilter.append(tableInfectionVaccine['infection_id'].isNotNull())
        condMEFilter.append(tableActionMEVaccination['infection_id'].isNotNull())
        if execActionsClientVaccinations:
            hurtTypeInfectionIdList = []
            hurtTypeId = self.cmbHurtType.value()
            if hurtTypeId:
                condHurtTypeInfection = [tableHurtTypeInfection['master_id'].eq(hurtTypeId)]
#                if self.chkEpidemicIndications.isChecked():
#                    condHurtTypeInfection.append(tableHurtTypeInfection['hasEpidIndications'].eq(1))
#                else:
#                    condHurtTypeInfection.append(tableHurtTypeInfection['hasEpidIndications'].eq(0))
                hurtTypeInfectionIdList = db.getDistinctIdList(tableHurtTypeInfection, [tableHurtTypeInfection['infection_id']], condHurtTypeInfection, tableHurtTypeInfection['infection_id'].name())
                if hurtTypeInfectionIdList:
                    condFilter.append(tableInfectionVaccine['infection_id'].inlist(hurtTypeInfectionIdList))
                    condMEFilter.append(tableActionMEVaccination['infection_id'].inlist(hurtTypeInfectionIdList))
            if not hurtTypeId or not hurtTypeInfectionIdList:
                queryTable = queryTable.innerJoin(tableInfectionIdentification, db.joinAnd([tableInfectionIdentification['master_id'].eq(tableRBInfection['id']),
                tableInfectionIdentification['deleted'].eq(0), tableInfectionIdentification['value'].ne('')]))
                queryTable = queryTable.innerJoin(tableAccountingSystem, db.joinAnd([tableAccountingSystem['id'].eq(tableInfectionIdentification['system_id']),
                tableAccountingSystem['urn'].eq(u'urn:oid:1.2.643.5.1.13.13.99.2.1111')]))
                queryTableME = queryTableME.innerJoin(tableInfectionIdentification, db.joinAnd([tableInfectionIdentification['master_id'].eq(tableRBInfection['id']),
                tableInfectionIdentification['deleted'].eq(0), tableInfectionIdentification['value'].ne('')]))
                queryTableME = queryTableME.innerJoin(tableAccountingSystem, db.joinAnd([tableAccountingSystem['id'].eq(tableInfectionIdentification['system_id']),
                tableAccountingSystem['urn'].eq(u'urn:oid:1.2.643.5.1.13.13.99.2.1111')]))
        else:
            queryTable = queryTable.innerJoin(tableInfectionIdentification, db.joinAnd([tableInfectionIdentification['master_id'].eq(tableRBInfection['id']),
            tableInfectionIdentification['deleted'].eq(0), tableInfectionIdentification['value'].ne('')]))
            queryTable = queryTable.innerJoin(tableAccountingSystem, db.joinAnd([tableAccountingSystem['id'].eq(tableInfectionIdentification['system_id']),
            tableAccountingSystem['urn'].eq(u'urn:oid:1.2.643.5.1.13.13.99.2.1111')]))
            queryTableME = queryTableME.innerJoin(tableInfectionIdentification, db.joinAnd([tableInfectionIdentification['master_id'].eq(tableRBInfection['id']),
            tableInfectionIdentification['deleted'].eq(0), tableInfectionIdentification['value'].ne('')]))
            queryTableME = queryTableME.innerJoin(tableAccountingSystem, db.joinAnd([tableAccountingSystem['id'].eq(tableInfectionIdentification['system_id']),
            tableAccountingSystem['urn'].eq(u'urn:oid:1.2.643.5.1.13.13.99.2.1111')]))
#            queryTableSystem = tableRBInfection.innerJoin(tableInfectionIdentification, db.joinAnd([tableInfectionIdentification['master_id'].eq(tableRBInfection['id']),
#            tableInfectionIdentification['deleted'].eq(0), tableInfectionIdentification['value'].ne('')]))
#            queryTableSystem = queryTableSystem.innerJoin(tableAccountingSystem, tableAccountingSystem['id'].eq(tableInfectionIdentification['system_id']))
#            systemInfectionIdList = db.getDistinctIdList(queryTableSystem, [tableRBInfection['id']], [tableAccountingSystem['urn'].eq(u'urn:oid:1.2.643.5.1.13.13.99.2.1111')], tableRBInfection['name'].name())
#            if systemInfectionIdList or self.selectInfectionIdList:
#                if self.selectInfectionIdList:
#                    systemInfectionIdList.extend(self.selectInfectionIdList)
#                condFilter.append(tableInfectionVaccine['infection_id'].inlist(systemInfectionIdList))
            if self.selectInfectionIdList:
                condFilter.append(tableInfectionVaccine['infection_id'].inlist(self.selectInfectionIdList))
                condMEFilter.append(tableActionMEVaccination['infection_id'].inlist(self.selectInfectionIdList))
        cols = [tableClientVaccination['id'].alias('clientVaccination_id'),
                tableClientVaccination['client_id'],
                tableClientVaccination['vaccine_id'],
                tableClientVaccination['datetime'].alias('date'),
                tableClientVaccination['vaccinationType'],
                tableInfectionVaccine['infection_id']
                ]
        cond = [tableClientVaccination['client_id'].eq(clientId),
                tableClientVaccination['deleted'].eq(0),
                #tableClientVaccination['datetime'].isNotNull()
               ]
        condME = [tableActionMEVaccination['clientVaccination_id'].isNull(),
                  tableEvent['client_id'].eq(clientId),
                  tableEvent['deleted'].eq(0),
                  tableAction['deleted'].eq(0),
                  tableActionMEVaccination['deleted'].eq(0),
                 ]
#        infectionDict = {}
        items = self.modelVaccinations._items
        for item in items:
            clientVaccinationId = forceRef(item.value('clientVaccination_id'))
            infectionId = forceRef(item.value('infection_id'))
            infectionDate = forceDate(item.value('date'))
            if clientVaccinationId:
                cond.append(db.if_(db.joinAnd([tableClientVaccination['id'].eq(clientVaccinationId), tableInfectionVaccine['infection_id'].eq(infectionId), tableClientVaccination['datetime'].dateEq(infectionDate)]), u'0', u'1'))
            elif infectionId:
                condME.append(db.if_(db.joinAnd([tableActionMEVaccination['infection_id'].eq(infectionId), tableActionMEVaccination['date'].dateEq(infectionDate)]), u'0', u'1'))
        if self.itemId():
            condME.append(tableActionMEVaccination['master_id'].ne(self.itemId()))
#        if self.modelVaccinations.checkedIdList:
#            cond.append(tableClientVaccination['id'].notInlist(self.modelVaccinations.checkedIdList))
        if condFilter:
            cond.extend(condFilter)
        if condMEFilter:
            condME.extend(condMEFilter)
        group = [tableClientVaccination['id'].name(),
                 tableClientVaccination['datetime'].name(),
                 tableInfectionVaccine['infection_id'].name(),
                 tableClientVaccination['vaccinationType'].name()
                 ]
        order = [tableClientVaccination['datetime'].name() + u'DESC']
        records = db.getRecordListGroupBy(queryTable, cols, cond, group, order)
        colsME = [tableActionMEVaccination['clientVaccination_id'].alias('clientVaccination_id'),
                  tableActionMEVaccination['date'],
                  tableActionMEVaccination['infection_id'],
                  tableActionMEVaccination['vaccinationType'],
                  ]
        groupME = [tableActionMEVaccination['clientVaccination_id'].name(),
                   tableActionMEVaccination['date'].name(),
                   tableActionMEVaccination['infection_id'].name(),
                   tableActionMEVaccination['vaccinationType'].name()
                  ]
        orderME = [tableActionMEVaccination['date'].name() + u'DESC']
        recordsME = db.getRecordListGroupBy(queryTableME, colsME, condME, groupME, orderME)
        if records and recordsME:
            records.extend(recordsME)
            records.sort(key=lambda x: forceDate(x.value('date')), reverse=True)
        elif recordsME and not records:
            records = recordsME
        for record in records:
            result = QtGui.qApp.db.table('Action_ME_Vaccination').newRecord()
            result.append(QtSql.QSqlField('include', QVariant.Bool))
            result.setValue('include', toVariant(False))
            result.setValue('master_id', toVariant(None))
            result.setValue('clientVaccination_id', record.value('clientVaccination_id'))
            result.setValue('date', record.value('date'))
            result.setValue('infection_id', record.value('infection_id'))
            result.setValue('vaccinationType', record.value('vaccinationType'))
            self.modelClientVaccinations._items.append(result)
        if self.modelClientVaccinations._extColsPresent:
            extSqlFields = []
            for col in self.modelClientVaccinations._cols:
                if col.external():
                    fieldName = col.fieldName()
                    if fieldName not in cols:
                        extSqlFields.append(QtSql.QSqlField(fieldName, col.valueType()))
            if extSqlFields:
                for item in self.modelClientVaccinations._items:
                    for field in extSqlFields:
                        item.append(field)
                        if field.name() == u'include':
                            item.setValue(field.name(), toVariant(False))
        #self.getInfectionVaccinations()
        self.modelClientVaccinations.reset()
        self.tblClientVaccinations.setCurrentIndex(currentIndex)


#    def getInfectionVaccinations(self):
#        self.infectionIdList = []
#        db = QtGui.qApp.db
#        tableHurtTypeInfection = db.table('rbHurtType_Infection')
#        tableInfectionIdentification = db.table('rbInfection_Identification')
#        tableAccountingSystem = db.table('rbAccountingSystem')
#        tableInfectionVaccine = db.table('rbInfection_rbVaccine')
#        tableRBInfection = db.table('rbInfection')
#        queryTable = tableInfectionVaccine.innerJoin(tableRBInfection, tableRBInfection['id'].eq(tableInfectionVaccine['infection_id']))
#        condFilter = []
#        condFilter.append(tableInfectionVaccine['infection_id'].isNotNull())
#        hurtTypeInfectionIdList = []
#        condHurtTypeInfection = []
#        hurtTypeId = self.cmbHurtType.value()
#        if hurtTypeId:
#            condHurtTypeInfection = [tableHurtTypeInfection['master_id'].eq(hurtTypeId)]
##            if self.chkEpidemicIndications.isChecked():
##                condHurtTypeInfection.append(tableHurtTypeInfection['hasEpidIndications'].eq(1))
##            else:
##                condHurtTypeInfection.append(tableHurtTypeInfection['hasEpidIndications'].eq(0))
#            hurtTypeInfectionIdList = db.getDistinctIdList(tableHurtTypeInfection, [tableHurtTypeInfection['infection_id']], condHurtTypeInfection, tableHurtTypeInfection['infection_id'].name())
#        if hurtTypeInfectionIdList:
#            condFilter.append(tableInfectionVaccine['infection_id'].inlist(hurtTypeInfectionIdList))
#        #if not hurtTypeId or not hurtTypeInfectionIdList:
#        queryTable = queryTable.innerJoin(tableInfectionIdentification, db.joinAnd([tableInfectionIdentification['master_id'].eq(tableRBInfection['id']),
#        tableInfectionIdentification['deleted'].eq(0), tableInfectionIdentification['value'].ne('')]))
#        queryTable = queryTable.innerJoin(tableAccountingSystem, db.joinAnd([tableAccountingSystem['id'].eq(tableInfectionIdentification['system_id']),
#        tableAccountingSystem['urn'].eq(u'urn:oid:1.2.643.5.1.13.13.99.2.1111')]))
#        cols = [tableInfectionVaccine['infection_id']]
#        cond = []
##        busyInfectionIdList = []
##        items = self.modelVaccinations._items
##        for item in items:
##            infectionIdList = forceRef(item.value('infection_id'))
##            if infectionId and infectionId not in busyInfectionIdList:
##                busyInfectionIdList.append(infectionId)
##        if busyInfectionIdList:
##            cond.append(tableInfectionVaccine['infection_id'].notInlist(busyInfectionIdList))
#        if condFilter:
#            cond.extend(condFilter)
#        order = [tableRBInfection['name'].name()]
#        self.infectionIdList = db.getDistinctIdList(queryTable, cols, cond, order)
#        self.modelVaccinations.setInfectionIdList(self.infectionIdList)


    def getInfectionVaccinations(self):
        self.infectionIdList = []
        db = QtGui.qApp.db
        tableHurtTypeInfection = db.table('rbHurtType_Infection')
        tableInfectionIdentification = db.table('rbInfection_Identification')
        tableAccountingSystem = db.table('rbAccountingSystem')
        tableRBInfection = db.table('rbInfection')
        condFilter = []
        hurtTypeInfectionIdList = []
        condHurtTypeInfection = []
        hurtTypeId = self.cmbHurtType.value()
        if hurtTypeId:
            condHurtTypeInfection = [tableHurtTypeInfection['master_id'].eq(hurtTypeId)]
            hurtTypeInfectionIdList = db.getDistinctIdList(tableHurtTypeInfection, [tableHurtTypeInfection['infection_id']], condHurtTypeInfection, tableHurtTypeInfection['infection_id'].name())
        if hurtTypeInfectionIdList:
            condFilter.append(tableRBInfection['id'].inlist(hurtTypeInfectionIdList))
        queryTable = tableRBInfection.innerJoin(tableInfectionIdentification, db.joinAnd([tableInfectionIdentification['master_id'].eq(tableRBInfection['id']),
        tableInfectionIdentification['deleted'].eq(0), tableInfectionIdentification['value'].ne('')]))
        queryTable = queryTable.innerJoin(tableAccountingSystem, db.joinAnd([tableAccountingSystem['id'].eq(tableInfectionIdentification['system_id']),
        tableAccountingSystem['urn'].eq(u'urn:oid:1.2.643.5.1.13.13.99.2.1111')]))
        cols = [tableRBInfection['id']]
        cond = []
        if condFilter:
            cond.extend(condFilter)
        order = [tableRBInfection['name'].name()]
        self.infectionIdList = db.getDistinctIdList(queryTable, cols, cond, order)
        self.modelVaccinations.setInfectionIdList(self.infectionIdList)


    @pyqtSignature('QAbstractButton*')
    def on_btnButtonBoxClientStatusActionsFilter_clicked(self, button):
        buttonCode = self.btnButtonBoxClientStatusActionsFilter.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.on_clientStatusActionsFilter_apply()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_clientStatusActionsFilter_reset()


    def on_clientStatusActionsFilter_reset(self):
        self.edtBegDateClientStatusActionsFilter.setDate(QDate())
        self.edtEndDateClientStatusActionsFilter.setDate(self.edtEndDate.date())
        self.chkExecActionsClientStatusActionsFilter.setChecked(True)


    def getClientStatusActionsFilter(self):
        self.clientStatusActionsFilter = {}
        self.clientStatusActionsFilter['begDateClientStatusActions'] = self.edtBegDateClientStatusActionsFilter.date()
        self.clientStatusActionsFilter['endDateClientStatusActions'] = self.edtEndDateClientStatusActionsFilter.date()
        self.clientStatusActionsFilter['execActionsClientStatusActions'] = self.chkExecActionsClientStatusActionsFilter.isChecked()


    def on_clientStatusActionsFilter_apply(self):
        self.updateClientStatusActions()
        self.focusClientStatusActions()


    def updateClientStatusActions(self):
        self.getClientStatusActionsFilter()
        self.loadClientStatusActions(self.eventId, self.clientId)


    def focusClientStatusActions(self):
        self.tblClientStatusActions.setFocus(Qt.TabFocusReason)


    def loadClientStatusActions(self, masterId, clientId):
        eventTypePostIdList = []
        eventTypeNotPostIdList = []
        currentIndex = self.tblClientStatusActions.currentIndex()
        db = QtGui.qApp.db
        cols = 'Action.*, Person.post_id'
        table = self.modelClientStatusActions._table
        tableEvent = db.table('Event')
        tableActionType = db.table('ActionType')
        tablePerson = db.table('Person')
        tablePost = db.table('rbPost')
        tablePostIdentification = db.table('rbPost_Identification')
        tableAccountingSystem = db.table('rbAccountingSystem')
        queryTable = table.innerJoin(tableEvent, tableEvent['id'].eq(table['event_id']))
        queryTable = queryTable.innerJoin(tableActionType, tableActionType['id'].eq(table['actionType_id']))
        queryTable = queryTable.innerJoin(tablePerson, db.joinAnd([tablePerson['id'].eq(table['person_id']), tablePerson['deleted'].eq(0)]))
        queryTable = queryTable.innerJoin(tablePost, tablePost['id'].eq(tablePerson['post_id']))
        queryTable = queryTable.innerJoin(tablePostIdentification, db.joinAnd([tablePostIdentification['master_id'].eq(tablePost['id']),
        tablePostIdentification['deleted'].eq(0), tablePostIdentification['value'].ne('')]))
        queryTable = queryTable.innerJoin(tableAccountingSystem, db.joinAnd([tableAccountingSystem['id'].eq(tablePostIdentification['system_id']),
        tableAccountingSystem['urn'].eq(u'urn:oid:1.2.643.5.1.13.13.11.1002')]))
        condFilter = []
        begDateClientStatusActions = self.clientStatusActionsFilter.get('begDateClientStatusActions')
        endDateClientStatusActions = self.clientStatusActionsFilter.get('endDateClientStatusActions')
        if begDateClientStatusActions:
            condFilter.append(table['endDate'].dateGe(begDateClientStatusActions))
        if endDateClientStatusActions:
            condFilter.append(table['endDate'].dateLe(endDateClientStatusActions))
        execActionsClientStatusActions = self.clientStatusActionsFilter.get('execActionsClientStatusActions')
        if execActionsClientStatusActions:
            hurtTypeCode = u''
            tableHurtType = db.table('rbHurtType')
            mainHurtTypeId = self.cmbHurtType.value()
            if mainHurtTypeId:
                recordHT = db.getRecordEx(tableHurtType, [tableHurtType['code']], [tableHurtType['id'].eq(mainHurtTypeId)])
                hurtTypeCode = forceStringEx(recordHT.value('code')) if recordHT else u''
            if self.eventTypeId:
                tableEventType = db.table('EventType')
                tableEventTypeDiagnostic = db.table('EventType_Diagnostic')
                recordETD = db.getRecordEx(tableEventTypeDiagnostic, [tableEventTypeDiagnostic['id']], [tableEventTypeDiagnostic['eventType_id'].eq(self.eventTypeId)])
                if recordETD and forceRef(recordETD.value('id')) and mainHurtTypeId:
                    condFilter.append(tablePerson['post_id'].isNotNull())
                    queryTableHT = tableEvent.innerJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
                    queryTableHT = queryTableHT.innerJoin(tableEventTypeDiagnostic, tableEventTypeDiagnostic['eventType_id'].eq(tableEventType['id']))
                    queryTableHT = queryTableHT.innerJoin(tablePost, tablePost['id'].eq(tableEventTypeDiagnostic['post_id']))
                    queryTableHT = queryTableHT.innerJoin(tablePostIdentification, db.joinAnd([tablePostIdentification['master_id'].eq(tablePost['id']),
                    tablePostIdentification['deleted'].eq(0), tablePostIdentification['value'].ne('')]))
                    queryTableHT = queryTableHT.innerJoin(tableAccountingSystem, db.joinAnd([tableAccountingSystem['id'].eq(tablePostIdentification['system_id']),
                    tableAccountingSystem['urn'].eq(u'urn:oid:1.2.643.5.1.13.13.11.1002')]))
                    colsHT = [tableEventTypeDiagnostic['eventType_id'],
                              tableEventTypeDiagnostic['post_id'],
                              tableEventTypeDiagnostic['hurtType'],
                              #tableAccountingSystem['urn']
                              ]
                    condHT = [tableEventType['id'].eq(self.eventTypeId),
                              tableEventTypeDiagnostic['post_id'].isNotNull(),
                              tableEventType['deleted'].eq(0),
                              tableEvent['deleted'].eq(0)
                              ]
                    records = db.getRecordList(queryTableHT, colsHT, condHT)
                    for record in records:
                        hurtType = forceStringEx(record.value('hurtType'))
                        postId = forceRef(record.value('post_id'))
                        if hurtTypeCode and ((not hurtType) or hurtTypeCode in hurtType.split(u';')):
                            if postId and postId not in eventTypePostIdList:
                               eventTypePostIdList.append(postId)
                        if hurtType and hurtTypeCode and hurtTypeCode not in hurtType.split(u';'):
                            if postId and postId not in eventTypeNotPostIdList:
                               eventTypeNotPostIdList.append(postId)
                if eventTypePostIdList:
                    condFilter.append(tablePerson['post_id'].inlist(eventTypePostIdList))
                if eventTypeNotPostIdList:
                    condFilter.append(tablePerson['post_id'].notInlist(eventTypeNotPostIdList))
        filter = [tableEvent['client_id'].eq(clientId),
                  table[self.modelClientStatusActions._masterIdFieldName].ne(masterId),
                  tableActionType['class'].eq(0),
                  table['status'].eq(CActionStatus.finished),
                  u'''(Action.endDate IS NOT NULL AND DATE(Action.endDate) != DATE(0))''',
                  tableEvent['deleted'].eq(0),
                  table['deleted'].eq(0),
                  tableActionType['deleted'].eq(0),
                  tableActionType['serviceType'].inlist([0, 1, 2])
                  ]
        if self.modelStatusActions.checkedIdList:
            filter.append(table['id'].notInlist(self.modelStatusActions.checkedIdList))
        examinationIdList = self.modelStatusActions.getExaminationIdList()
        if examinationIdList:
            filter.append(table['id'].notInlist(examinationIdList))
        if condFilter:
            filter.extend(condFilter)
#        if self.modelClientStatusActions._filter:
#            filter.append(self.modelClientStatusActions._filter)
#        if self.modelClientStatusActions._idxFieldName:
#            order = [table[self.modelClientStatusActions._idxFieldName].name() + u'ASC', table['endDate'].name() + u'DESC']
#        else:
        order = [table['endDate'].name() + u'DESC']
        self.modelClientStatusActions._items = db.getRecordList(queryTable, cols, filter, order)
        if self.modelClientStatusActions._extColsPresent:
            extSqlFields = []
            for col in self.modelClientStatusActions._cols:
                if col.external():
                    fieldName = col.fieldName()
                    if fieldName not in cols:
                        extSqlFields.append(QtSql.QSqlField(fieldName, col.valueType()))
            if extSqlFields:
                for item in self.modelClientStatusActions._items:
                    for field in extSqlFields:
                        item.append(field)
                        if field.name() == u'include':
                            item.setValue(field.name(), toVariant(False))
        #self.getPostIdList()
        self.modelClientStatusActions.reset()
        self.tblClientStatusActions.setCurrentIndex(currentIndex)


    def getPostIdList(self):
        self.postIdList = []
        eventTypePostIdList = []
        eventTypeNotPostIdList = []
        db = QtGui.qApp.db
        cols = 'rbPost.id'
        tablePost = db.table('rbPost')
        tablePostIdentification = db.table('rbPost_Identification')
        tableAccountingSystem = db.table('rbAccountingSystem')
        queryTable = tablePost.innerJoin(tablePostIdentification, db.joinAnd([tablePostIdentification['master_id'].eq(tablePost['id']),
        tablePostIdentification['deleted'].eq(0), tablePostIdentification['value'].ne('')]))
        queryTable = queryTable.innerJoin(tableAccountingSystem, db.joinAnd([tableAccountingSystem['id'].eq(tablePostIdentification['system_id']),
        tableAccountingSystem['urn'].eq(u'urn:oid:1.2.643.5.1.13.13.11.1002')]))
        condFilter = []
        hurtTypeCode = u''
        tableHurtType = db.table('rbHurtType')
        mainHurtTypeId = self.cmbHurtType.value()
        if mainHurtTypeId:
            recordHT = db.getRecordEx(tableHurtType, [tableHurtType['code']], [tableHurtType['id'].eq(mainHurtTypeId)])
            hurtTypeCode = forceStringEx(recordHT.value('code')) if recordHT else u''
        if self.eventTypeId:
            tableEventType = db.table('EventType')
            tableEventTypeDiagnostic = db.table('EventType_Diagnostic')
            recordETD = db.getRecordEx(tableEventTypeDiagnostic, [tableEventTypeDiagnostic['id']], [tableEventTypeDiagnostic['eventType_id'].eq(self.eventTypeId)])
            if recordETD and forceRef(recordETD.value('id')) and mainHurtTypeId:
                queryTableHT = tableEventType.innerJoin(tableEventTypeDiagnostic, tableEventTypeDiagnostic['eventType_id'].eq(tableEventType['id']))
                queryTableHT = queryTableHT.innerJoin(tablePost, tablePost['id'].eq(tableEventTypeDiagnostic['post_id']))
                queryTableHT = queryTableHT.innerJoin(tablePostIdentification, db.joinAnd([tablePostIdentification['master_id'].eq(tablePost['id']),
                tablePostIdentification['deleted'].eq(0), tablePostIdentification['value'].ne('')]))
                queryTableHT = queryTableHT.innerJoin(tableAccountingSystem, db.joinAnd([tableAccountingSystem['id'].eq(tablePostIdentification['system_id']),
                tableAccountingSystem['urn'].eq(u'urn:oid:1.2.643.5.1.13.13.11.1002')]))
                colsHT = [tableEventTypeDiagnostic['eventType_id'],
                          tableEventTypeDiagnostic['post_id'],
                          tableEventTypeDiagnostic['hurtType'],
                          #tableAccountingSystem['urn']
                          ]
                condHT = [tableEventType['id'].eq(self.eventTypeId),
                          tableEventTypeDiagnostic['post_id'].isNotNull(),
                          tableEventType['deleted'].eq(0)
                          ]
                records = db.getRecordList(queryTableHT, colsHT, condHT)
                for record in records:
                    hurtType = forceStringEx(record.value('hurtType'))
                    postId = forceRef(record.value('post_id'))
                    if hurtTypeCode and ((not hurtType) or hurtTypeCode in hurtType.split(u';')):
                        if postId and postId not in eventTypePostIdList:
                           eventTypePostIdList.append(postId)
                    if hurtType and hurtTypeCode and hurtTypeCode not in hurtType.split(u';'):
                        if postId and postId not in eventTypeNotPostIdList:
                           eventTypeNotPostIdList.append(postId)
            if eventTypePostIdList:
                condFilter.append(tablePost['id'].inlist(eventTypePostIdList))
            if eventTypeNotPostIdList:
                condFilter.append(tablePost['id'].notInlist(eventTypeNotPostIdList))
        filter = []
        if condFilter:
            filter.extend(condFilter)
        order = [tablePost['name'].name()]
        self.postIdList = db.getDistinctIdList(queryTable, cols, filter, order)
        self.modelStatusActions.setPostIdList(self.postIdList)


    @pyqtSignature('QAbstractButton*')
    def on_btnButtonBoxDiagnosticActionsFilter_clicked(self, button):
        buttonCode = self.btnButtonBoxDiagnosticActionsFilter.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.on_diagnosticActionsFilter_apply()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_diagnosticActionsFilter_reset()


    def on_diagnosticActionsFilter_reset(self):
        self.edtBegDateDiagnosticActionsFilter.setDate(QDate())
        self.edtEndDateDiagnosticActionsFilter.setDate(self.edtEndDate.date())
        self.chkExecActionsDiagnosticActionsFilter.setChecked(True)


    def getDiagnosticActionsFilter(self):
        self.diagnosticActionsFilter = {}
        self.diagnosticActionsFilter['begDateDiagnosticActions'] = self.edtBegDateDiagnosticActionsFilter.date()
        self.diagnosticActionsFilter['endDateDiagnosticActions'] = self.edtEndDateDiagnosticActionsFilter.date()
        self.diagnosticActionsFilter['execActionsDiagnosticActions'] = self.chkExecActionsDiagnosticActionsFilter.isChecked()


    def on_diagnosticActionsFilter_apply(self):
        self.updateDiagnosticActions()
        self.focusDiagnosticActions()


    def updateDiagnosticActions(self):
        self.getDiagnosticActionsFilter()
        self.loadDiagnosticActions(self.eventId, self.clientId)


    def focusDiagnosticActions(self):
        self.tblClientDiagnosticActions.setFocus(Qt.TabFocusReason)


    def loadDiagnosticActions(self, masterId, clientId):
        self.labNomenclativeServiceIdList = []
        self.toolNomenclativeServiceIdList = []
        nomenclativeServiceIdList = []
        actionTypeIdList = []
        currentIndex = self.tblClientDiagnosticActions.currentIndex()
        db = QtGui.qApp.db
        cols = '''Action.*, ActionType.nomenclativeService_id, IF(rbAccountingSystem.urn = 'urn:oid:1.2.643.5.1.13.13.11.1437', 1, IF(rbAccountingSystem.urn = 'urn:oid:1.2.643.5.1.13.13.11.1471', 2, 0)) AS researchType'''
        table = self.modelClientDiagnosticActions._table
        tableEvent = db.table('Event')
        tableActionType = db.table('ActionType')
        tableEventType = db.table('EventType')
        tableServiceIdentification = db.table('rbService_Identification')
        tableAccountingSystem = db.table('rbAccountingSystem')
        tableEventTypeAction = db.table('EventType_Action')
        queryTable = table.innerJoin(tableEvent, tableEvent['id'].eq(table['event_id']))
        queryTable = queryTable.innerJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
        queryTable = queryTable.innerJoin(tableActionType, tableActionType['id'].eq(table['actionType_id']))
        queryTable = queryTable.innerJoin(tableServiceIdentification, db.joinAnd([tableServiceIdentification['master_id'].eq(tableActionType['nomenclativeService_id']),
        tableServiceIdentification['deleted'].eq(0), tableServiceIdentification['value'].ne('')]))
        queryTable = queryTable.innerJoin(tableAccountingSystem, db.joinAnd([tableAccountingSystem['id'].eq(tableServiceIdentification['system_id']),
        db.joinOr([tableAccountingSystem['urn'].eq(u'urn:oid:1.2.643.5.1.13.13.11.1437'), tableAccountingSystem['urn'].eq(u'urn:oid:1.2.643.5.1.13.13.11.1471')])]))
        condFilter = []
        begDateDiagnosticActions = self.diagnosticActionsFilter.get('begDateDiagnosticActions')
        endDateDiagnosticActions = self.diagnosticActionsFilter.get('endDateDiagnosticActions')
        if begDateDiagnosticActions:
            condFilter.append(table['endDate'].dateGe(begDateDiagnosticActions))
        if endDateDiagnosticActions:
            condFilter.append(table['endDate'].dateLe(endDateDiagnosticActions))
        recordETA = db.getRecordEx(tableEventTypeAction, [tableEventTypeAction['id']], [tableEventTypeAction['eventType_id'].eq(self.eventTypeId)])
        execActionsDiagnosticActions = self.diagnosticActionsFilter.get('execActionsDiagnosticActions')
        if execActionsDiagnosticActions:
            condFilter.append(tableActionType['nomenclativeService_id'].isNotNull())
            if self.eventTypeId:
                hurtTypeCode = u''
                tableHurtType = db.table('rbHurtType')
                mainHurtTypeId = self.cmbHurtType.value()
                if mainHurtTypeId:
                    recordHT = db.getRecordEx(tableHurtType, [tableHurtType['code']], [tableHurtType['id'].eq(mainHurtTypeId)])
                    hurtTypeCode = forceStringEx(recordHT.value('code')) if recordHT else u''
                if recordETA and forceRef(recordETA.value('id')) and mainHurtTypeId:
                    queryTableHT = tableEventTypeAction.innerJoin(tableEventType, tableEventType['id'].eq(tableEventTypeAction['eventType_id']))
                    queryTableHT = queryTableHT.innerJoin(tableActionType, tableActionType['id'].eq(tableEventTypeAction['actionType_id']))
                    queryTableHT = queryTableHT.innerJoin(tableServiceIdentification, db.joinAnd([tableServiceIdentification['master_id'].eq(tableActionType['nomenclativeService_id']),
                    tableServiceIdentification['deleted'].eq(0), tableServiceIdentification['value'].ne('')]))
                    queryTableHT = queryTableHT.innerJoin(tableAccountingSystem, db.joinAnd([tableAccountingSystem['id'].eq(tableServiceIdentification['system_id']),
                    db.joinOr([tableAccountingSystem['urn'].eq(u'urn:oid:1.2.643.5.1.13.13.11.1437'), tableAccountingSystem['urn'].eq(u'urn:oid:1.2.643.5.1.13.13.11.1471')])]))
                    colsHT = [tableEventTypeAction['actionType_id'],
                              tableActionType['nomenclativeService_id'],
                              tableEventTypeAction['hurtType'],
                              tableAccountingSystem['urn']
                             ]
                    condHT = [tableEventType['id'].eq(self.eventTypeId),
                              tableActionType['nomenclativeService_id'].isNotNull(),
                              tableEventType['deleted'].eq(0),
                              tableActionType['deleted'].eq(0),
                             ]
                    recordsHT = db.getRecordList(queryTableHT, colsHT, condHT)
                else:
                    colsHT = [table['actionType_id'],
                              tableActionType['nomenclativeService_id'],
                              #tableEventTypeAction['hurtType'],
                              tableAccountingSystem['urn']
                             ]
                    condHT = [tableEventType['id'].eq(self.eventTypeId),
                              tableActionType['nomenclativeService_id'].isNotNull(),
                              table['deleted'].eq(0),
                              tableEvent['deleted'].eq(0),
                              tableEventType['deleted'].eq(0),
                              tableActionType['deleted'].eq(0),
                             ]
                    recordsHT = db.getRecordList(queryTable, colsHT, condHT)
                for record in recordsHT:
                    hurtType = forceStringEx(record.value('hurtType'))
                    if (not hurtType) or (not hurtTypeCode) or (not mainHurtTypeId) or (mainHurtTypeId and hurtTypeCode in hurtType.split(u';')):
                        urn = forceStringEx(record.value('urn'))
                        actionTypeId = forceRef(record.value('actionType_id'))
                        nomenclativeServiceId = forceRef(record.value('nomenclativeService_id'))
                        if urn == u'urn:oid:1.2.643.5.1.13.13.11.1437':
                            if actionTypeId and actionTypeId not in self.labActionTypeIdList:
                               self.labActionTypeIdList.append(actionTypeId)
                            if nomenclativeServiceId and nomenclativeServiceId not in self.labNomenclativeServiceIdList:
                               self.labNomenclativeServiceIdList.append(nomenclativeServiceId)
                        if urn == u'urn:oid:1.2.643.5.1.13.13.11.1471':
                            if actionTypeId and actionTypeId not in self.toolActionTypeIdList:
                               actionTypeIdList.append(actionTypeId)
                            if nomenclativeServiceId and nomenclativeServiceId not in self.toolNomenclativeServiceIdList:
                               self.toolNomenclativeServiceIdList.append(nomenclativeServiceId)
                        if nomenclativeServiceId and nomenclativeServiceId not in nomenclativeServiceIdList:
                           nomenclativeServiceIdList.append(nomenclativeServiceId)
                        if actionTypeId and actionTypeId not in actionTypeIdList:
                           actionTypeIdList.append(actionTypeId)
                if actionTypeIdList:
                    condFilter.append(tableActionType['id'].inlist(actionTypeIdList))
                if nomenclativeServiceIdList:
                    condFilter.append(tableActionType['nomenclativeService_id'].inlist(nomenclativeServiceIdList))
        filter = [tableEvent['client_id'].eq(clientId),
                  table[self.modelClientDiagnosticActions._masterIdFieldName].ne(masterId),
                  tableActionType['class'].eq(1),
                  table['status'].eq(CActionStatus.finished),
                  table['endDate'].isNotNull(),
                  tableEvent['deleted'].eq(0),
                  table['deleted'].eq(0),
                  tableActionType['deleted'].eq(0)
                  ]
        if self.modelLabDiagnosticActions.checkedIdList:
            filter.append(table['id'].notInlist(self.modelLabDiagnosticActions.checkedIdList))
        labResearchIdList = self.modelLabDiagnosticActions.getResearchIdList()
        if labResearchIdList:
            filter.append(table['id'].notInlist(labResearchIdList))
        if self.modelToolDiagnosticActions.checkedIdList:
            filter.append(table['id'].notInlist(self.modelToolDiagnosticActions.checkedIdList))
        toolResearchIdList = self.modelToolDiagnosticActions.getResearchIdList()
        if toolResearchIdList:
            filter.append(table['id'].notInlist(toolResearchIdList))
#        if self.modelClientDiagnosticActions._filter:
#            filter.append(self.modelClientDiagnosticActions._filter)
        if condFilter:
            filter.extend(condFilter)
#        if self.modelClientDiagnosticActions._idxFieldName:
#            order = [table[self.modelClientDiagnosticActions._idxFieldName].name() + u'ASC', table['endDate'].name() + u'DESC']
#        else:
        order = [table['endDate'].name() + u'DESC']
        self.modelClientDiagnosticActions._items = db.getRecordList(queryTable, cols, filter, order)
        items = self.modelClientDiagnosticActions._items
        for item in items:
            researchType = forceInt(item.value('researchType'))
            nomenclativeServiceId = forceRef(item.value('nomenclativeService_id'))
            if researchType == 1:
                if nomenclativeServiceId and nomenclativeServiceId not in self.labNomenclativeServiceIdList:
                   self.labNomenclativeServiceIdList.append(nomenclativeServiceId)
            if researchType == 2:
                if nomenclativeServiceId and nomenclativeServiceId not in self.toolNomenclativeServiceIdList:
                   self.toolNomenclativeServiceIdList.append(nomenclativeServiceId)
        if self.modelClientDiagnosticActions._extColsPresent:
            extSqlFields = []
            for col in self.modelClientDiagnosticActions._cols:
                if col.external():
                    fieldName = col.fieldName()
                    if fieldName not in cols:
                        extSqlFields.append(QtSql.QSqlField(fieldName, col.valueType()))
            if extSqlFields:
                for item in self.modelClientDiagnosticActions._items:
                    for field in extSqlFields:
                        item.append(field)
                        if field.name() == u'include':
                            item.setValue(field.name(), toVariant(False))
        #self.getNomenclativeServiceIdList()
        self.modelClientDiagnosticActions.reset()
        self.tblClientDiagnosticActions.setCurrentIndex(currentIndex)


    def getNomenclativeServiceIdList(self):
        self.labNomenclativeServiceIdList = []
        self.toolNomenclativeServiceIdList = []
        self.labServiceIdList = []
        self.toolServiceIdList = []
        self.serviceMap = {}
        self.nomenclativeServiceMap = {}
        nomenclativeServiceIdList = []
        actionTypeIdList = []
        db = QtGui.qApp.db
        cols = '''ActionType.nomenclativeService_id, IF(rbAccountingSystem.urn = 'urn:oid:1.2.643.5.1.13.13.11.1437', 1, IF(rbAccountingSystem.urn = 'urn:oid:1.2.643.5.1.13.13.11.1471', 2, 0)) AS researchType'''
        tableActionType = db.table('ActionType')
        tableService = db.table('rbService')
        tableServiceGroup = db.table('rbServiceGroup')
        tableServiceIdentification = db.table('rbService_Identification')
        tableAccountingSystem = db.table('rbAccountingSystem')
        tableEventTypeAction = db.table('EventType_Action')
        queryTable = tableActionType.leftJoin(tableService, tableService['id'].eq(tableActionType['nomenclativeService_id']))
        queryTable = queryTable.leftJoin(tableServiceGroup, tableServiceGroup['id'].eq(tableService['group_id']))
        queryTable = queryTable.innerJoin(tableServiceIdentification,
                                          db.joinAnd([tableServiceIdentification['master_id'].eq(tableService['id']),
                                                      tableServiceIdentification['deleted'].eq(0),
                                                      tableServiceIdentification['value'].ne('')]))
        queryTable = queryTable.innerJoin(tableAccountingSystem,
                                          db.joinAnd([tableAccountingSystem['id'].eq(tableServiceIdentification['system_id']),
                                                      db.joinOr([tableAccountingSystem['urn'].eq(u'urn:oid:1.2.643.5.1.13.13.11.1437'),
                                                                 tableAccountingSystem['urn'].eq(u'urn:oid:1.2.643.5.1.13.13.11.1471')])]))
        condFilter = []
        recordETA = db.getRecordEx(tableEventTypeAction, [tableEventTypeAction['id']], [tableEventTypeAction['eventType_id'].eq(self.eventTypeId)])
        condFilter.append(tableActionType['nomenclativeService_id'].isNotNull())
        if self.eventTypeId:
            hurtTypeCode = u''
            tableHurtType = db.table('rbHurtType')
            mainHurtTypeId = self.cmbHurtType.value()
            if mainHurtTypeId:
                recordHT = db.getRecordEx(tableHurtType, [tableHurtType['code']], [tableHurtType['id'].eq(mainHurtTypeId)])
                hurtTypeCode = forceStringEx(recordHT.value('code')) if recordHT else u''
            if recordETA and forceRef(recordETA.value('id')) and mainHurtTypeId:
                queryTableHT = tableActionType.innerJoin(tableEventTypeAction, tableEventTypeAction['actionType_id'].eq(tableActionType['id']))
                queryTableHT = queryTableHT.leftJoin(tableService, tableService['id'].eq(tableActionType['nomenclativeService_id']))
                queryTableHT = queryTableHT.leftJoin(tableServiceGroup, tableServiceGroup['id'].eq(tableService['group_id']))
                queryTableHT = queryTableHT.innerJoin(tableServiceIdentification,
                                                      db.joinAnd([tableServiceIdentification['master_id'].eq(tableService['id']),
                                                                  tableServiceIdentification['deleted'].eq(0),
                                                                  tableServiceIdentification['value'].ne('')]))
                queryTableHT = queryTableHT.innerJoin(tableAccountingSystem,
                                                      db.joinAnd([tableAccountingSystem['id'].eq(tableServiceIdentification['system_id']),
                                                                  db.joinOr([tableAccountingSystem['urn'].eq(u'urn:oid:1.2.643.5.1.13.13.11.1437'),
                                                                             tableAccountingSystem['urn'].eq(u'urn:oid:1.2.643.5.1.13.13.11.1471')])]))
                colsHT = [tableEventTypeAction['actionType_id'],
                          tableService['id'],
                          tableEventTypeAction['hurtType'],
                          tableAccountingSystem['urn'],
                          tableServiceGroup['code'],
                          tableServiceIdentification['value']
                          ]
                condHT = [tableEventTypeAction['eventType_id'].eq(self.eventTypeId),
                          tableActionType['nomenclativeService_id'].isNotNull(),
                          tableActionType['deleted'].eq(0),
                          ]
                recordsHT = db.getRecordList(queryTableHT, colsHT, condHT)
                for record in recordsHT:
                    hurtType = forceStringEx(record.value('hurtType'))
                    if (not hurtType) or (not hurtTypeCode) or (not mainHurtTypeId) or (mainHurtTypeId and hurtTypeCode in hurtType.split(u';')):
                        urn = forceStringEx(record.value('urn'))
                        actionTypeId = forceRef(record.value('actionType_id'))
                        nomenclativeServiceId = forceRef(record.value('id'))
                        serviceGroupCode = forceString(record.value('code'))
                        serviceIdent = forceString(record.value('value'))
                        if urn == u'urn:oid:1.2.643.5.1.13.13.11.1437':
                            if actionTypeId and actionTypeId not in self.labActionTypeIdList:
                                self.labActionTypeIdList.append(actionTypeId)
                            if nomenclativeServiceId and nomenclativeServiceId not in self.labNomenclativeServiceIdList:
                                self.labNomenclativeServiceIdList.append(nomenclativeServiceId)
                                self.nomenclativeServiceMap[nomenclativeServiceId] = serviceIdent
                            if serviceGroupCode == 'elmk' and nomenclativeServiceId and nomenclativeServiceId not in self.labServiceIdList:
                                self.labServiceIdList.append(nomenclativeServiceId)
                                self.serviceMap[serviceIdent] = nomenclativeServiceId
                        if urn == u'urn:oid:1.2.643.5.1.13.13.11.1471':
                            if actionTypeId and actionTypeId not in self.toolActionTypeIdList:
                                actionTypeIdList.append(actionTypeId)
                            if nomenclativeServiceId and nomenclativeServiceId not in self.toolNomenclativeServiceIdList:
                                self.toolNomenclativeServiceIdList.append(nomenclativeServiceId)
                                self.nomenclativeServiceMap[nomenclativeServiceId] = serviceIdent
                            if serviceGroupCode == 'elmk' and nomenclativeServiceId and nomenclativeServiceId not in self.toolServiceIdList:
                                self.toolServiceIdList.append(nomenclativeServiceId)
                                self.serviceMap[serviceIdent] = nomenclativeServiceId
                        if nomenclativeServiceId and nomenclativeServiceId not in nomenclativeServiceIdList:
                            nomenclativeServiceIdList.append(nomenclativeServiceId)
                        if actionTypeId and actionTypeId not in actionTypeIdList:
                            actionTypeIdList.append(actionTypeId)
            if actionTypeIdList:
                condFilter.append(tableActionType['id'].inlist(actionTypeIdList))
            if nomenclativeServiceIdList:
                condFilter.append(tableActionType['nomenclativeService_id'].inlist(nomenclativeServiceIdList))
        filter = [tableActionType['class'].eq(1),
                  tableActionType['nomenclativeService_id'].isNotNull(),
                  tableActionType['deleted'].eq(0),
                  ]
        if condFilter:
            filter.extend(condFilter)
        order = [tableActionType['name'].name()]
        items = db.getRecordList(queryTable, cols, filter, order)
        for item in items:
            researchType = forceInt(item.value('researchType'))
            nomenclativeServiceId = forceRef(item.value('nomenclativeService_id'))
            if researchType == 1:
                if nomenclativeServiceId and nomenclativeServiceId not in self.labNomenclativeServiceIdList:
                    self.labNomenclativeServiceIdList.append(nomenclativeServiceId)
            if researchType == 2:
                if nomenclativeServiceId and nomenclativeServiceId not in self.toolNomenclativeServiceIdList:
                    self.toolNomenclativeServiceIdList.append(nomenclativeServiceId)
        self.modelLabDiagnosticActions.setNomenclativeServiceIdList(self.labServiceIdList)
        self.modelToolDiagnosticActions.setNomenclativeServiceIdList(self.toolServiceIdList)


    def getActionTypeToEventType(self):
        self.actionTypeIdList = []
        self.labActionTypeIdList = []
        self.toolActionTypeIdList = []
        self.nomenclativeServiceIdList = []
        self.labNomenclativeServiceIdList = []
        self.toolNomenclativeServiceIdList = []
        self.labServiceIdList = []
        self.toolServiceIdList = []
        self.serviceMap = {}
        self.nomenclativeServiceMap = {}
        db = QtGui.qApp.db
        tableActionType = db.table('ActionType')
        if self.eventTypeId:
            tableAction = db.table('Action')
            tableEvent = db.table('Event')
            tableEventType = db.table('EventType')
            tableEventTypeAction = db.table('EventType_Action')
            tableService = db.table('rbService')
            tableServiceGroup = db.table('rbServiceGroup')
            tableServiceIdentification = db.table('rbService_Identification')
            tableAccountingSystem = db.table('rbAccountingSystem')
            mainHurtTypeId = self.cmbHurtType.value()
            hurtTypeCode = u''
            recordETA = db.getRecordEx(tableEventTypeAction, [tableEventTypeAction['id']], [tableEventTypeAction['eventType_id'].eq(self.eventTypeId)])
            if recordETA and forceRef(recordETA.value('id')) and mainHurtTypeId:
                tableHurtType = db.table('rbHurtType')
                if mainHurtTypeId:
                    recordHT = db.getRecordEx(tableHurtType, [tableHurtType['code']], [tableHurtType['id'].eq(mainHurtTypeId)])
                    hurtTypeCode = forceStringEx(recordHT.value('code')) if recordHT else u''
                queryTable = tableEvent.innerJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
                queryTable = queryTable.innerJoin(tableEventTypeAction, tableEventTypeAction['eventType_id'].eq(tableEventType['id']))
                queryTable = queryTable.innerJoin(tableActionType, tableActionType['id'].eq(tableEventTypeAction['actionType_id']))
                queryTable = queryTable.leftJoin(tableService, tableService['id'].eq(tableActionType['nomenclativeService_id']))
                queryTable = queryTable.leftJoin(tableServiceGroup, tableServiceGroup['id'].eq(tableService['group_id']))
                queryTable = queryTable.innerJoin(tableServiceIdentification,
                                                  db.joinAnd([tableServiceIdentification['master_id'].eq(tableService['id']),
                                                              tableServiceIdentification['deleted'].eq(0),
                                                              tableServiceIdentification['value'].ne('')]))
                queryTable = queryTable.innerJoin(tableAccountingSystem,
                                                  db.joinAnd([tableAccountingSystem['id'].eq(tableServiceIdentification['system_id']),
                                                             db.joinOr([tableAccountingSystem['urn'].eq(u'urn:oid:1.2.643.5.1.13.13.11.1437'),
                                                                        tableAccountingSystem['urn'].eq(u'urn:oid:1.2.643.5.1.13.13.11.1471')])]))
                cols = [tableEventTypeAction['actionType_id'],
                        tableService['id'],
                        tableEventTypeAction['hurtType'],
                        tableAccountingSystem['urn'],
                        tableServiceGroup['code'],
                        tableServiceIdentification['value']
                        ]
                cond = [tableEventType['id'].eq(self.eventTypeId),
                        tableService['id'].isNotNull(),
                        tableEventType['deleted'].eq(0),
                        tableEvent['deleted'].eq(0),
                        tableActionType['deleted'].eq(0),
                        ]
                records = db.getRecordList(queryTable, cols, cond)
            else:
                queryTable = tableEvent.innerJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
                queryTable = queryTable.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
                queryTable = queryTable.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
                queryTable = queryTable.leftJoin(tableService, tableService['id'].eq(tableActionType['nomenclativeService_id']))
                queryTable = queryTable.leftJoin(tableServiceGroup, tableServiceGroup['id'].eq(tableService['group_id']))
                queryTable = queryTable.innerJoin(tableServiceIdentification,
                                                  db.joinAnd([tableServiceIdentification['master_id'].eq(tableService['id']),
                                                              tableServiceIdentification['deleted'].eq(0),
                                                              tableServiceIdentification['value'].ne('')]))
                queryTable = queryTable.innerJoin(tableAccountingSystem,
                                                  db.joinAnd([tableAccountingSystem['id'].eq(tableServiceIdentification['system_id']),
                                                              db.joinOr([tableAccountingSystem['urn'].eq(u'urn:oid:1.2.643.5.1.13.13.11.1437'),
                                                                         tableAccountingSystem['urn'].eq(u'urn:oid:1.2.643.5.1.13.13.11.1471')])]))
                cols = [tableAction['actionType_id'],
                        tableService['id'],
                        tableAccountingSystem['urn'],
                        tableServiceGroup['code'],
                        tableServiceIdentification['value']
                        ]
                cond = [tableEventType['id'].eq(self.eventTypeId),
                        tableEvent['client_id'].eq(self.clientId),
                        tableService['id'].isNotNull(),
                        tableAction['deleted'].eq(0),
                        tableEventType['deleted'].eq(0),
                        tableEvent['deleted'].eq(0),
                        tableActionType['deleted'].eq(0),
                        ]
                records = db.getRecordList(queryTable, cols, cond)
            for record in records:
                hurtType = forceStringEx(record.value('hurtType'))
                if (not hurtType) or (not hurtTypeCode) or (not mainHurtTypeId) or (mainHurtTypeId and hurtTypeCode in hurtType.split(u';')):
                    urn = forceStringEx(record.value('urn'))
                    actionTypeId = forceRef(record.value('actionType_id'))
                    nomenclativeServiceId = forceRef(record.value('id'))
                    serviceGroupCode = forceString(record.value('code'))
                    serviceIdent = forceString(record.value('value'))
                    if urn == u'urn:oid:1.2.643.5.1.13.13.11.1437':
                        if actionTypeId and actionTypeId not in self.labActionTypeIdList:
                            self.labActionTypeIdList.append(actionTypeId)
                        if nomenclativeServiceId and nomenclativeServiceId not in self.labNomenclativeServiceIdList:
                            self.labNomenclativeServiceIdList.append(nomenclativeServiceId)
                            self.nomenclativeServiceMap[nomenclativeServiceId] = serviceIdent
                        if serviceGroupCode == 'elmk' and nomenclativeServiceId and nomenclativeServiceId not in self.labServiceIdList:
                            self.labServiceIdList.append(nomenclativeServiceId)
                            self.serviceMap[serviceIdent] = nomenclativeServiceId
                    if urn == u'urn:oid:1.2.643.5.1.13.13.11.1471':
                        if actionTypeId and actionTypeId not in self.toolActionTypeIdList:
                            self.actionTypeIdList.append(actionTypeId)
                        if nomenclativeServiceId and nomenclativeServiceId not in self.toolNomenclativeServiceIdList:
                            self.toolNomenclativeServiceIdList.append(nomenclativeServiceId)
                            self.nomenclativeServiceMap[nomenclativeServiceId] = serviceIdent
                        if serviceGroupCode == 'elmk' and nomenclativeServiceId and nomenclativeServiceId not in self.toolServiceIdList:
                            self.toolServiceIdList.append(nomenclativeServiceId)
                            self.serviceMap[serviceIdent] = nomenclativeServiceId
                    if nomenclativeServiceId and nomenclativeServiceId not in self.nomenclativeServiceIdList:
                        self.nomenclativeServiceIdList.append(nomenclativeServiceId)
                    if actionTypeId and actionTypeId not in self.actionTypeIdList:
                        self.actionTypeIdList.append(actionTypeId)
        condFilter = []
        condFilter.append(tableActionType['id'].inlist(self.actionTypeIdList))
        self.modelLabDiagnosticActions.setActionTypeIdList(self.labActionTypeIdList)
        self.modelToolDiagnosticActions.setActionTypeIdList(self.toolActionTypeIdList)
        condFilter.append(tableActionType['nomenclativeService_id'].inlist(self.nomenclativeServiceIdList))
        self.modelLabDiagnosticActions.setNomenclativeServiceIdList(self.labServiceIdList)
        self.modelToolDiagnosticActions.setNomenclativeServiceIdList(self.toolServiceIdList)
        if condFilter:
            if self.modelClientDiagnosticActions._filter:
                self.modelClientDiagnosticActions._filter += u' AND ' + db.joinAnd(condFilter)
            else:
                self.modelClientDiagnosticActions._filter = db.joinAnd(condFilter)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelStatusActions_currentRowChanged(self, current, previous):
        self.updateActionPropertiesTable(current, self.tblStatusActionProperties, u'examination_id', previous)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelClientStatusActions_currentRowChanged(self, current, previous):
        self.updateActionPropertiesTable(current, self.tblClientStatusActionProperties, u'id', previous)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelLabDiagnosticActions_currentRowChanged(self, current, previous):
        self.updateActionPropertiesTable(current, self.tblDiagnosticActionProperties, u'research_id', previous)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelToolDiagnosticActions_currentRowChanged(self, current, previous):
        self.updateActionPropertiesTable(current, self.tblDiagnosticActionProperties, u'research_id', previous)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelClientDiagnosticActions_currentRowChanged(self, current, previous):
        self.updateActionPropertiesTable(current, self.tblClientDiagnosticActionProperties, u'id', previous)


    def updateActionPropertiesTable(self, index, tbl, fieldActionId, previous=None):
        if previous:
            tbl.savePreferencesLoc(previous.row())
        row = index.row()
        record = None
        if row >= 0 and row < len(index.model()._items):
            record = index.model().getRecordByRow(row)
        actionId = forceRef(record.value(fieldActionId)) if record else None
        if record and actionId:
            clientId = self.clientId
            clientSex = self.clientSex
            clientAge = self.clientAge
            action = CAction.getActionById(actionId, isShort=True)
            tbl.model().setAction2(action, clientId, clientSex, clientAge, eventTypeId=self.eventTypeId)
            setActionPropertiesColumnVisible(action._actionType, tbl)
            tbl.resizeColumnsToContents()
            tbl.resizeRowsToContents()
            tbl.horizontalHeader().setStretchLastSection(True)
            tbl.loadPreferencesLoc(tbl.preferencesLocal, row)
        else:
            tbl.model().setAction2(None, None)


    @pyqtSignature('bool')
    def on_chkIsUrgent_toggled(self, checked):
        self.action.getRecord().setValue('isUrgent', toVariant(self.chkIsUrgent.isChecked()))


    @pyqtSignature('QDate')
    def on_edtBegDateClientDiseasesFilter_dateChanged(self, date):
        begDate = self.edtBegDateClientDiseasesFilter.date()
        if begDate:
            self.edtEndDateClientDiseasesFilter.setMinimumDate(begDate)
        else:
            self.edtEndDateClientDiseasesFilter.clearMinimumDate()


    @pyqtSignature('QDate')
    def on_edtEndDateClientDiseasesFilter_dateChanged(self, date):
        endDate = self.edtEndDateClientDiseasesFilter.date()
        if endDate:
            self.edtBegDateClientDiseasesFilter.setMaximumDate(endDate)
        else:
            self.edtBegDateClientDiseasesFilter.clearMaximumDate()


    @pyqtSignature('QDate')
    def on_edtBegDateClientVaccinationsFilter_dateChanged(self, date):
        begDate = self.edtBegDateClientVaccinationsFilter.date()
        if begDate:
            self.edtEndDateClientVaccinationsFilter.setMinimumDate(begDate)
        else:
            self.edtEndDateClientVaccinationsFilter.clearMinimumDate()


    @pyqtSignature('QDate')
    def on_edtEndDateClientVaccinationsFilter_dateChanged(self, date):
        endDate = self.edtEndDateClientVaccinationsFilter.date()
        if endDate:
            self.edtBegDateClientVaccinationsFilter.setMaximumDate(endDate)
        else:
            self.edtBegDateClientVaccinationsFilter.clearMaximumDate()


    @pyqtSignature('QDate')
    def on_edtBegDateClientStatusActionsFilter_dateChanged(self, date):
        begDate = self.edtBegDateClientStatusActionsFilter.date()
        if begDate:
            self.edtEndDateClientStatusActionsFilter.setMinimumDate(begDate)
        else:
            self.edtEndDateClientStatusActionsFilter.clearMinimumDate()


    @pyqtSignature('QDate')
    def on_edtEndDateClientStatusActionsFilter_dateChanged(self, date):
        endDate = self.edtEndDateClientStatusActionsFilter.date()
        if endDate:
            self.edtBegDateClientStatusActionsFilter.setMaximumDate(endDate)
        else:
            self.edtBegDateClientStatusActionsFilter.clearMaximumDate()


    @pyqtSignature('QDate')
    def on_edtBegDateDiagnosticActionsFilter_dateChanged(self, date):
        begDate = self.edtBegDateDiagnosticActionsFilter.date()
        if begDate:
            self.edtEndDateDiagnosticActionsFilter.setMinimumDate(begDate)
        else:
            self.edtEndDateDiagnosticActionsFilter.clearMinimumDate()


    @pyqtSignature('QDate')
    def on_edtEndDateDiagnosticActionsFilter_dateChanged(self, date):
        endDate = self.edtEndDateDiagnosticActionsFilter.date()
        if endDate:
            self.edtBegDateDiagnosticActionsFilter.setMaximumDate(endDate)
        else:
            self.edtBegDateDiagnosticActionsFilter.clearMaximumDate()


    def on_cmbMKBFromClientDiseasesFilter_editingFinished(self):
        if self.focusWidget() != self.cmbMKBFromClientDiseasesFilter:
            valueFrom = self.cmbMKBFromClientDiseasesFilter.text()
            if valueFrom == '':
                self.cmbMKBFromClientDiseasesFilter.setText(u'A00')
                valueFrom = self.cmbMKBFromClientDiseasesFilter.text()
            valueTo = self.cmbMKBToClientDiseasesFilter.text()
            if unicode(valueFrom) > unicode(valueTo) or unicode(valueFrom) < u'A00' or unicode(valueFrom) > u'B99':
                self.cmbMKBFromClientDiseasesFilter.setText(u'A00')
                valueFrom = self.cmbMKBFromClientDiseasesFilter.text()
            filterFrom = u''' MKB.DiagID >= 'A00' AND MKB.DiagID <= '%s' '''%(valueTo if valueTo else u'B99')
            self.cmbMKBFromClientDiseasesFilter.setFilter(filterFrom)
            self.cmbMKBFromClientDiseasesFilter.ICDTreePopup=None
            filterTo = u''' MKB.DiagID >= '%s' AND MKB.DiagID <= 'B99' '''%(valueFrom if valueFrom else u'A00')
            self.cmbMKBToClientDiseasesFilter.setFilter(filterTo)
            self.cmbMKBToClientDiseasesFilter.ICDTreePopup=None


    def on_cmbMKBToClientDiseasesFilter_editingFinished(self):
        if self.focusWidget() != self.cmbMKBToClientDiseasesFilter:
            valueFrom = self.cmbMKBFromClientDiseasesFilter.text()
            valueTo = self.cmbMKBToClientDiseasesFilter.text()
            if valueTo == '':
                self.cmbMKBToClientDiseasesFilter.setText(u'B99')
                valueTo = self.cmbMKBToClientDiseasesFilter.text()
            if unicode(valueFrom) > unicode(valueTo) or unicode(valueTo) > u'B99' or unicode(valueTo) < u'A00':
                self.cmbMKBToClientDiseasesFilter.setText(u'B99')
                valueTo = self.cmbMKBToClientDiseasesFilter.text()
            filterFrom = u''' MKB.DiagID >= 'A00' AND MKB.DiagID <= '%s' '''%(valueTo if valueTo else u'B99')
            self.cmbMKBFromClientDiseasesFilter.setFilter(filterFrom)
            self.cmbMKBFromClientDiseasesFilter.ICDTreePopup=None
            filterTo = u''' MKB.DiagID >= '%s' AND MKB.DiagID <= 'B99' '''%(valueFrom if valueFrom else u'A00')
            self.cmbMKBToClientDiseasesFilter.setFilter(filterTo)
            self.cmbMKBToClientDiseasesFilter.ICDTreePopup=None


    @pyqtSignature('double')
    def on_edtAmount_valueChanged(self, value):
        actionType = self.action.getType()
        if actionType.defaultPlannedEndDate == CActionType.dpedBegDatePlusAmount:
            begDate = self.edtBegDate.date()
            amountValue = int(value)
            date = begDate.addDays(amountValue-1) if begDate and amountValue else QDate()
            self.edtPlannedEndDate.setDate(date)


    @pyqtSignature('')
    def on_btnAttachedFiles_pressed(self):
        if self.btnAttachedFiles.getIsSaveModel():
            self.setIsDirty(True)


    @pyqtSignature('')
    def on_btnSelectOrg_clicked(self):
        orgId = selectOrganisation(self, self.cmbOrg.value(), False, self.cmbOrg.filter)
        self.cmbOrg.updateModel()
        if orgId:
            self.cmbOrg.setValue(orgId)


    @pyqtSignature('int')
    def on_cmbPerson_currentIndexChanged(self, value):
        personId = self.cmbPerson.value()
        self.setPersonId(personId)
        if personId and self.recordEvent and personId != forceRef(self.recordEvent.value('execPerson_id')):
            self.recordEvent.setValue('execPerson_id', toVariant(personId))


    def on_cmbSetPerson_currentIndexChanged(self, value):
        setPersonId = self.cmbSetPerson.value()
        if setPersonId and self.recordEvent and setPersonId != forceRef(self.recordEvent.value('setPerson_id')):
            self.recordEvent.setValue('setPerson_id', toVariant(setPersonId))


    @pyqtSignature('QDate')
    def on_edtDirectionDate_dateChanged(self, date):
        self.edtDirectionTime.setEnabled(bool(date))


    def getDateForContract(self):
        if self.eventDate:
            return self.eventDate
        elif self.eventSetDateTime:
            return self.eventSetDateTime.date()
        return QDate.currentDate()


    @pyqtSignature('QDate')
    def on_edtBegDate_dateChanged(self, date):
        oldDate = None
        if self.action:
            record = self.action.getRecord()
            if record:
                oldDate = forceDate(self.action.getRecord().value('begDate'))
        if oldDate != date:
            self.edtBegTime.setEnabled(bool(date))
            if date:
                if self.recordEvent and date != forceDate(self.recordEvent.value('setDate')):
                    self.recordEvent.setValue('setDate', toVariant(date))
                for item in self.modelDiagnostics.items():
                    if date != forceDate(item.value('setDate')):
                        item.setValue('setDate', toVariant(date))
                        item.setValue('endDate', toVariant(date))
            self.tabNotes.cmbContract.setDate(self.getDateForContract())
            self.updateAmount()


    @pyqtSignature('QDate')
    def on_edtEndDate_dateChanged(self, date):
        oldDate = None
        if self.action:
            record = self.action.getRecord()
            if record:
                oldDate = forceDate(self.action.getRecord().value('endDate'))
        if oldDate != date:
            self.edtEndTime.setEnabled(bool(date))
            if date and self.recordEvent and date != forceDate(self.recordEvent.value('execDate')):
                self.recordEvent.setValue('execDate', toVariant(date))
            self.tabNotes.cmbContract.setDate(self.getDateForContract())
            self.updateAmount()
            if self.action.getType().closeEvent:
                self.setEventDate(date)
            self.initDateParamsFilter(date)
            self.modelInfectionDiseases.setActionEndDate(date)
            self.modelVaccinations.setActionEndDate(date)
            self.modelStatusActions.setActionEndDate(date)
            self.modelLabDiagnosticActions.setActionEndDate(date)
            self.modelToolDiagnosticActions.setActionEndDate(date)


    def initDateParamsFilter(self, date):
        self.edtEndDateClientDiseasesFilter.setEndDateDefaultMax(date)
        self.edtEndDateClientDiseasesFilter.setEndDateAction(date)
        self.edtEndDateClientDiseasesFilter.setMaximumDate(date)
        self.edtEndDateClientDiseasesFilter.setDate(date)
        self.edtEndDateClientVaccinationsFilter.setEndDateDefaultMax(date)
        self.edtEndDateClientVaccinationsFilter.setEndDateAction(date)
        self.edtEndDateClientVaccinationsFilter.setMaximumDate(date)
        self.edtEndDateClientVaccinationsFilter.setDate(date)
        self.edtEndDateClientStatusActionsFilter.setEndDateDefaultMax(date)
        self.edtEndDateClientStatusActionsFilter.setEndDateAction(date)
        self.edtEndDateClientStatusActionsFilter.setMaximumDate(date)
        self.edtEndDateClientStatusActionsFilter.setDate(date)
        self.edtEndDateDiagnosticActionsFilter.setEndDateDefaultMax(date)
        self.edtEndDateDiagnosticActionsFilter.setEndDateAction(date)
        self.edtEndDateDiagnosticActionsFilter.setMaximumDate(date)
        self.edtEndDateDiagnosticActionsFilter.setDate(date)


    def setContractId(self, contractId):
        if forceRef(self.action.getRecord().value('contract_id')) != contractId:
            self.action.getRecord().setValue('contract_id', toVariant(contractId))
        financeId = self.tabNotes.eventFinanceId
        if forceRef(self.action.getRecord().value('finance_id')) != financeId:
            self.action.getRecord().setValue('finance_id', toVariant(financeId))


    @pyqtSignature('int')
    def on_cmbStatus_currentIndexChanged(self, index):
        actionStatus = self.cmbStatus.value()
        if actionStatus in (CActionStatus.finished, CActionStatus.canceled, CActionStatus.refused):
            if not self.edtEndDate.date():
                now = QDateTime.currentDateTime()
                self.edtEndDate.setDate(now.date())
                if self.edtEndTime.isVisible():
                    self.edtEndTime.setTime(now.time())
            if actionStatus in (CActionStatus.canceled, CActionStatus.refused) and not self.cmbSetPerson.value():
                if QtGui.qApp.userId and QtGui.qApp.userSpecialityId:
                    self.cmbPerson.setValue(QtGui.qApp.userId)
                else:
                    self.cmbPerson.setValue(self.cmbSetPerson.value())


    def freeJobTicket(self, endDate):
        if self.action:
            jobTicketIdList = []
            for property in self.action.getType()._propertiesById.itervalues():
                if property.isJobTicketValueType():
                    jobTicketId = self.action[property.name]
                    if jobTicketId and jobTicketId not in jobTicketIdList:
                        jobTicketIdList.append(jobTicketId)
                        db = QtGui.qApp.db
                        tableJobTicket = db.table('Job_Ticket')
                        cond = [tableJobTicket['id'].eq(jobTicketId),
                                tableJobTicket['deleted'].eq(0)
                                ]
                        if self.edtEndTime.isVisible():
                            cond.append(tableJobTicket['datetime'].ge(endDate))
                        else:
                            cond.append(tableJobTicket['datetime'].dateGe(endDate))
                        records = db.getRecordList(tableJobTicket, '*', cond)
                        for record in records:
                            datetime = forceDateTime(record.value('datetime')) if self.edtEndTime.isVisible() else forceDate(record.value('datetime'))
                            if datetime > endDate:
                                self.action[property.name] = None


    def checkPrintByTemplateAllowed(self, templateId):
        #Проверяет параметр шаблона печати "Требует идентификатор события" (rbPrintTemplate.needEventId), задача #0016238.
        if not self.eventId:
            db = QtGui.qApp.db
            printNotAllowed = forceBool(db.translate('rbPrintTemplate', 'id', templateId, 'needEventId'))
            if printNotAllowed:
                messageBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning, u'Внимание!',
                                               u'Требуется сохранить случай обслуживания до формирования печатной формы документа! Для сохранения без закрытия редактора нажмите кнопку "Сохранить".',
                                               QtGui.QMessageBox.Ok)
                messageBox.setWindowFlags(messageBox.windowFlags() | Qt.WindowStaysOnTopHint)
                messageBox.exec_()
                return False
        return True


    @pyqtSignature('int')
    def on_btnPrint_printByTemplate(self, templateId):
        if self.checkPrintByTemplateAllowed(templateId):
            context = CInfoContext()
            eventInfo = context.getInstance(CEventInfo, self.eventId)
            eventByRecord = CCookedEventInfo(context, self.eventId, self.recordEvent)
            eventActions = eventInfo.actions
            infectionDiseases = context.getInstance(CDiagnosticInfoProxyList, [self.modelInfectionDiseases])
            vaccinations = context.getInstance(CActionMEVaccinationInfoList, self.modelVaccinations.items())
            examinations = context.getInstance(CActionMEExaminationsInfoList, self.modelStatusActions.items())
            labResearches = context.getInstance(CActionMEResearchesInfoList, self.modelLabDiagnosticActions.items(), findResearchType=1)
            toolResearches = context.getInstance(CActionMEResearchesInfoList, self.modelToolDiagnosticActions.items(), findResearchType=2)
            self.modelMembersMSIPerson.saveItems()
            action = CCookedActionInfo(context, self.getRecord(), self.action)
            action._isDirty = self.isDirty()
            data = { 'event' : eventInfo,
                     'eventByRecord' : eventByRecord,
                     'infectionDiseases' : infectionDiseases,
                     'vaccinations' : vaccinations,
                     'examinations' : examinations,
                     'labResearches' : labResearches,
                     'toolResearches' : toolResearches,
                     'action': action,
                     'client': eventByRecord.client,
                     'actions':eventActions,
                     'currentAction': CActionRecordItem(self.getRecord(), self.action)
                   }
            signAndAttachResult = applyTemplate(self, templateId, data, signAndAttachHandler=self.btnAttachedFiles.getSignAndAttachHandler())
            if signAndAttachResult:
                self.setIsDirty(True)


    def getDiagFilter(self):
        result = ''
        personId = self.cmbPerson.value()
        if personId:
            db = QtGui.qApp.db
            tablePerson = db.table('Person')
            record = db.getRecordEx(tablePerson, [tablePerson['speciality_id']], [tablePerson['id'].eq(personId), tablePerson['deleted'].eq(0)])
            specialityId = forceRef(record.value('speciality_id')) if record else None
            result = self.mapSpecialityIdToDiagFilter.get(specialityId, None)
            if result is None:
                result = QtGui.qApp.db.translate('rbSpeciality', 'id', specialityId, 'mkbFilter')
                if result is None:
                    result = ''
                else:
                    result = forceString(result)
                self.mapSpecialityIdToDiagFilter[specialityId] = forceString(result)
        return result



    def getDiagFilterEx(self, specialityId=None):
        if not specialityId:
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


    def checkDiagnosis(self, MKB, specialityId=None):
        diagFilter = self.getDiagFilterEx(specialityId)
        return checkDiagnosis(self, MKB, diagFilter, self.clientId, self.clientSex, self.clientAge, self.edtBegDate.date())


    def checkSpecifyDiagnosis(self, MKB):
        diagFilter = self.getDiagFilter()
        date = min(d for d in (self.edtBegDate.date(), self.edtEndDate.date(), QDate.currentDate()) if d)
        acceptable, specifiedMKB, specifiedMKBEx, specifiedCharacterId, specifiedTraumaTypeId, modifiableDiagnosisId, specifiedDispanserId, specifiedRequiresFillingDispanser, specifiedProlongMKB = checkSpecifyDiagnosis(self, MKB, diagFilter, self.clientId, self.clientSex, self.clientAge, date)
        return acceptable, specifiedMKB, specifiedMKBEx, specifiedCharacterId, specifiedTraumaTypeId, specifiedDispanserId, specifiedRequiresFillingDispanser, specifiedProlongMKB


    def specifyDiagnosis(self, MKB):
        diagFilter = self.getDiagFilter()
        date = min(d for d in (self.edtBegDate.date(), self.edtEndDate.date(), QDate.currentDate()) if d)
        acceptable, specifiedMKB, specifiedMKBEx, specifiedCharacterId, specifiedTraumaTypeId, modifiableDiagnosisId, specifiedDispanserId, specifiedRequiresFillingDispanser, specifiedProlongMKB = specifyDiagnosis(self, MKB, diagFilter, self.clientId, self.clientSex, self.clientAge, date)
        return acceptable, specifiedMKB, specifiedMKBEx, specifiedCharacterId, specifiedTraumaTypeId, specifiedDispanserId, specifiedRequiresFillingDispanser, specifiedProlongMKB


class CMembersMSIPersonTableModel(CInDocTableModel):
    class CLocNumbeRowColumn(CInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)

        def toString(self, val, record, row):
            return toVariant(row + 1)

        def toSortString(self, val, record, row):
            return forcePyType(self.toString(val, record, row))

        def toStatusTip(self, val, record, row):
            return self.toString(val, record, row)

        def alignment(self):
            return QVariant(Qt.AlignLeft + Qt.AlignTop)

    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Person', 'id', 'id', parent)
        self.addExtCol(CMembersMSIPersonTableModel.CLocNumbeRowColumn(u'№', 'cnt', 5), QVariant.Int).setReadOnly()
        self.addCol(CPersonFindInDocTableCol(u'Члены врачебной комиссии', 'id',  20, 'vrbPersonWithSpecialityAndOrgStr', parent=parent))
        self.readOnly = False
        self.action = None
        self.eventEditor = None
        self._enableAppendLine = True
        self.descrList = []


    def rowCount(self, index=None):
        return len(self._items)+(1 if self._enableAppendLine else 0)


#    def rowCount(self, index=None):
#        itemsLen = len(self._items)
#        return itemsLen+(1 if (self._enableAppendLine and itemsLen < len(self.descrList)) else 0)


    def setEventEditor(self, eventEditor):
        self.eventEditor = eventEditor


    def setAction(self, action):
        self.action = action
        self.getDescrList()


    def setReadOnly(self, value=True):
        self.readOnly = value


    def flags(self, index):
        if self.readOnly:
           return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return CInDocTableModel.flags(self, index)


    def getEmptyRecord(self):
        result = CInDocTableModel.getEmptyRecord(self)
        result.append(QtSql.QSqlField('cnt', QVariant.Int))
        return result


    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if 0 <= row < len(self._items):
            if role == Qt.EditRole:
                col = self._cols[column]
                record = self._items[row]
                return record.value(col.fieldName())
            if role == Qt.DisplayRole:
                col = self._cols[column]
                record = self._items[row]
                if column == 0:
                    return col.toString(record.value(col.fieldName()), record, row)
                return col.toString(record.value(col.fieldName()), record)
            if role == Qt.StatusTipRole:
                col = self._cols[column]
                record = self._items[row]
                if column == 0:
                    return col.toStatusTip(record.value(col.fieldName()), record, row)
                return col.toStatusTip(record.value(col.fieldName()), record)
            if role == Qt.TextAlignmentRole:
                col = self._cols[column]
                return col.alignment()
            if role == Qt.ForegroundRole:
                col = self._cols[column]
                record = self._items[row]
                return col.getForegroundColor(record.value(col.fieldName()), record)
        return QVariant()


    def getDescrList(self):
        for propertyTypeName, propertyType in self.action.getType()._propertiesByName.items():
            descr = trim(propertyType.descr)
            if descr and u'ME:commissioner' in descr and descr not in self.descrList:
                self.descrList.append(descr)


    def getItemIdList(self):
        itemIdList = []
        items = self._items
        for item in items:
            id = forceRef(item.value('id'))
            if id and id not in itemIdList:
                itemIdList.append(id)
        return itemIdList


    def setData(self, index, value, role=Qt.EditRole):
        row = index.row()
        if row >= len(self.descrList):
            return False
        column = index.column()
        if role == Qt.EditRole:
            if row >= 0 and row < len(self._items):
                col = self._cols[column]
                record = self._items[row]
                if record.value(col.fieldName()) == value:
                    return False
                if column == 1:
                    newPersonId = forceRef(value)
                    oldPersonId = forceRef(record.value('id'))
                    result = CInDocTableModel.setData(self, index, value, role)
                    if result:
                        self.updateModelStatusActions(newPersonId, oldPersonId)
                    return result
        return CInDocTableModel.setData(self, index, value, role)


    def removeRows(self, row, count, parentIndex = QModelIndex()):
        if 0 <= row and row+count <= len(self._items):
            personId = forceRef(self._items[row].value('id'))
            self.beginRemoveRows(parentIndex, row, row+count-1)
            del self._items[row:row+count]
            self.endRemoveRows()
            self.saveItems()
            self.eventEditor.setIsDirty(True)
            self.reset()
            if personId:
                modelStatusActions = QObject.parent(self).modelStatusActions
                statusActionsItems = modelStatusActions._items
                for statusActionsRow, statusActionsItem in enumerate(statusActionsItems):
                    statusActionsPersonId = forceRef(statusActionsItem.value('person_id'))
                    if personId == statusActionsPersonId:
                        modelStatusActions._items[statusActionsRow].setValue('isComissioner', toVariant(0))
            return True
        else:
            return False


    def updateModelStatusActions(self, newPersonId, oldPersonId):
        modelStatusActions = QObject.parent(self).modelStatusActions
        statusActionsItems = modelStatusActions._items
        for statusActionsRow, statusActionsItem in enumerate(statusActionsItems):
            statusActionsPersonId = forceRef(statusActionsItem.value('person_id'))
            if newPersonId == statusActionsPersonId:
                modelStatusActions._items[statusActionsRow].setValue('isComissioner', toVariant(1))
            if oldPersonId == statusActionsPersonId:
                modelStatusActions._items[statusActionsRow].setValue('isComissioner', toVariant(0))


    def removeRow(self, row, parentIndex = QModelIndex()):
        return self.removeRows(row, 1, parentIndex)


    def loadItems(self, masterId = None):
        self._items = []
        if self.eventEditor and self.action:
            items = {}
            for property in self.action._propertiesById.itervalues():
                propertyType = property.type()
                descr = trim(propertyType.descr)
                if descr and u'ME:commissioner' in descr:
                    if descr not in self.descrList:
                        self.descrList.append(descr)
                    value = property._value
                    propertyValue = propertyType.convertQVariantToPyValue(value) if type(value) == QVariant else value
                    if isinstance(propertyValue, basestring) or type(propertyValue) == QString:
                        propertyValue = trim(propertyValue)
                    if propertyValue:
                        items[descr] = forceRef(propertyValue)
            itemsKeys = items.keys()
            itemsKeys.sort()
            for itemsKey in itemsKeys:
                val = items.get(itemsKey, None)
                if val:
                    record = self.getEmptyRecord()
                    record.setValue('id', toVariant(val))
                    self._items.append(record)
        self.reset()


    def saveItems(self, masterId = None):
        action = self.action if self.action else self.eventEditor.action
        if self.eventEditor and action:
            for idx, descr in enumerate(self.descrList):
                if descr:
                    for propertyTypeName, property in action._propertiesByName.items():
                        propertyType = property.type()
                        if trim(descr) == trim(propertyType.descr):
                            del self.eventEditor.action[propertyType.name]
            if self.eventEditor and self._items is not None and self.eventEditor.action:
                descrListLen = len(self.descrList)
                for idx, record in enumerate(self._items):
                    if idx < descrListLen:
                        descr = self.descrList[idx]
                        self.eventEditor.setProperty(QVariant(forceInt(record.value('id'))), descr)
                self.action = self.eventEditor.action


class CClientDiseasesTableModel(CInDocTableModel):
    class CLocMKBDiagNameColumn(CInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.cache = {}

        def toString(self, val, record):
            MKB = forceStringEx(record.value('MKB'))
            if self.cache.has_key(MKB):
                descr = self.cache[MKB]
            else:
                descr = getMKBName(MKB) if MKB else ''
                self.cache[MKB] = descr
            return QVariant((descr) if MKB else '')

        def invalidateRecordsCache(self):
            self.cache.invalidate()

    class CLocICDExInDocTableCol(CICDExInDocTableCol):
        def createEditor(self, parent):
            editor = CICDCodeEditEx(parent)
            #editor.setFilter(u''' MKB.DiagID >= 'A00' AND MKB.DiagID <= 'B99' ''')
            return editor


    def __init__(self, parent, diagnosisTypeCode=''):
        CInDocTableModel.__init__(self, 'Diagnostic', 'id', 'event_id', parent)
        self.addHiddenCol('diagnosis_id')
        self.addExtCol(CBoolInDocTableCol(u'Выбрать', 'include', 3 ), QVariant.Bool)
        self.addCol(CDateInDocTableCol(u'Установлен', 'endDate', 20, canBeEmpty=True)).setReadOnly(True)
        self.addCol(CRBInDocTableCol(u'Тип', 'diagnosisType_id', 10, 'rbDiagnosisType')).setReadOnly(True)
        self.addExtCol(self.CLocICDExInDocTableCol(u'Диагноз', 'MKB', 20), QVariant.String).setReadOnly(True)
        self.addCol(CClientDiseasesTableModel.CLocMKBDiagNameColumn(u'Диагноз расшифровка', 'id', 30), QVariant.String).setReadOnly(True)
        self.readOnly = False
        self.action = None
        self.eventEditor = None
        self.diagnosisTypeCode = diagnosisTypeCode
        self.diagnosisTypeId = self.getDiagnosisTypeId(self.diagnosisTypeCode)


    def getDiagnosisTypeId(self, diagnosisTypeCode):
        if diagnosisTypeCode:
            return forceRef(QtGui.qApp.db.translate('rbDiagnosisType', 'code', diagnosisTypeCode, 'id'))
        return None


    def setEventEditor(self, eventEditor):
        self.eventEditor = eventEditor


    def setAction(self, action):
        self.action = action


    def cellReadOnly(self, index):
        if QtGui.qApp.userId and QtGui.qApp.userSpecialityId:
            row = index.row()
            if 0 <= row < len(self._items):
                record = self._items[row]
                if record:
                    column = index.column()
                    MKB = forceStringEx(record.value('MKB'))
                    if MKB and column == 0:
                        return False
        return True


    def setReadOnly(self, value=True):
        self.readOnly = value


    def flags(self, index):
        if self.readOnly or index.column() != 0:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return CInDocTableModel.flags(self, index)


    def getEmptyRecord(self):
        result = QtGui.qApp.db.table('Diagnostic').newRecord()
        result.append(QtSql.QSqlField('include', QVariant.Bool))
        result.append(QtSql.QSqlField('MKB', QVariant.String))
        result.setValue('include', toVariant(False))
        result.setValue('MKB', toVariant(self.getMKBToDiagnosis(forceRef(result.value('diagnosis_id')))))
        return result


    def getMKBToDiagnosis(self, diagnosisId):
        MKB = u''
        if diagnosisId:
            db = QtGui.qApp.db
            table = db.table('Diagnosis')
            record = db.getRecordEx(table, 'MKB', [table['id'].eq(diagnosisId), table['deleted'].eq(0)])
            MKB = forceStringEx(record.value('MKB')) if record else u''
        return MKB


    def setMKBAction(self, fieldName, value):
        if self.eventEditor and self.eventEditor.action:
            self.eventEditor.action.getRecord().setValue(fieldName, toVariant(value))
        if self.action:
            self.action.getRecord().setValue(fieldName, toVariant(value))


    def removeRow(self, row, parentIndex = QModelIndex()):
        row = self.removeRows(row, 1, parentIndex)
        self.reset()
        return row


    def selectAll(self):
        for record in self._items:
            record.setValue('include', toVariant(True))
        self.reset()


    def deselectAll(self):
        for record in self._items:
            record.setValue('include', toVariant(False))
        self.reset()


    def hasChecked(self):
        for record in self._items:
            if forceBool(record.value('include')):
                return True
        return False


    def hasNotChecked(self):
        for record in self._items:
            if not forceBool(record.value('include')):
                return True
        return False


    def getCheckedItems(self):
        checkedItems = []
        for item in self._items:
            if forceBool(item.value('include')):
                checkedItems.append(item)
        return checkedItems


    def setData(self, index, value, role=Qt.EditRole):
        column = index.column()
        row = index.row()
        if row >= 0 and row < len(self._items):
            col = self._cols[column]
            record = self._items[row]
            if record.value(col.fieldName()) == value:
                return False
        if role == Qt.CheckStateRole and column == 0:
            return CInDocTableModel.setData(self, index, value, role)
        return False


    def loadItems(self, masterId, clientId):
        db = QtGui.qApp.db
        cols = '*'
        table = self._table
        tableEvent = db.table('Event')
        queryTable = table.innerJoin(tableEvent, tableEvent['id'].eq(table['event_id']))
        filter = [tableEvent['client_id'].eq(clientId),
                  table[self._masterIdFieldName].ne(masterId)
                  ]
        if self.diagnosisTypeId:
            filter.append(table['diagnosisType_id'].eq(self.diagnosisTypeId))
        if self._filter:
            filter.append(self._filter)
        if table.hasField('deleted'):
            filter.append(table['deleted'].eq(0))
        filter.append(tableEvent['deleted'].eq(0))
        filter.append(table['endDate'].isNotNull())
#        if self._idxFieldName:
#            order = [table[self._idxFieldName].name() + u'ASC', table['endDate'].name() + u'DESC']
#        else:
        order = [table['endDate'].name() + u'DESC']
        self._items = db.getRecordList(queryTable, cols, filter, order)
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
                        if field.name() == u'include':
                            item.setValue(field.name(), toVariant(False))
                        elif field.name() == u'MKB':
                            item.setValue(field.name(), toVariant(self.getMKBToDiagnosis(forceRef(item.value('diagnosis_id')))))
        self.reset()


    def saveItems(self, masterId):
        pass


class CInfectionDiseasesTableModel(CMKBListInDocTableModel):
    Col_EndDate = 0
    Col_MKB = 1
    class CLocMKBDiagNameColumn(CInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.cache = {}

        def toString(self, val, record):
            MKB = forceStringEx(record.value('MKB'))
            if self.cache.has_key(MKB):
                descr = self.cache[MKB]
            else:
                descr = getMKBName(MKB) if MKB else ''
                self.cache[MKB] = descr
            return QVariant(descr if MKB else '')

        def invalidateRecordsCache(self):
            self.cache.invalidate()

    class CLocICDExInDocTableCol(CICDExInDocTableCol):
        def createEditor(self, parent):
            editor = CICDCodeEditEx(parent)
            editor.setFilter(u''' MKB.DiagID >= 'A00' AND MKB.DiagID <= 'B99' ''')
            return editor

    class CDateExInDocTableCol(CDateInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CDateInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.highlightRedDate = params.get('highlightRedDate', True) and QtGui.qApp.highlightRedDate()
            self.canBeEmpty = params.get('canBeEmpty', False)
            self.actionEndDate = None

        def setActionEndDate(self, actionEndDate):
            self.actionEndDate = actionEndDate

        def createEditor(self, parent):
            editor = CDateEdit(parent)
            editor.setHighlightRedDate(self.highlightRedDate)
            editor.canBeEmpty(self.canBeEmpty)
            return editor


    def __init__(self, parent, diagnosisTypeCode):
        CMKBListInDocTableModel.__init__(self, 'Diagnostic', 'id', 'event_id', parent)
        self.addHiddenCol('diagnosis_id')
        self.addHiddenCol('diagnosisType_id')
        self.addCol(self.CDateExInDocTableCol(u'Установлен', 'endDate', 20, canBeEmpty=True))
        self.addExtCol(self.CLocICDExInDocTableCol(u'Диагноз', 'MKB', 20), QVariant.String)
        self.addCol(self.CLocMKBDiagNameColumn(u'Диагноз расшифровка', 'id', 30), QVariant.String).setReadOnly(True)
        self.readOnly = False
        self.setExtColsPresent(True)
        self.action = None
        self.eventEditor = None
        self.actionEndDate = None
        self.checkedIdList = []
        self.diagnosisTypeCode = diagnosisTypeCode
        self.diagnosisTypeId = self.getDiagnosisTypeId(self.diagnosisTypeCode)
        self.inspectionsResultIdList = []


    def setInspectionsResultIdList(self, inspectionsResultIdList):
        self.inspectionsResultIdList = inspectionsResultIdList


    def getDiagnosisTypeId(self, diagnosisTypeCode):
        if diagnosisTypeCode:
            return forceRef(QtGui.qApp.db.translate('rbDiagnosisType', 'code', diagnosisTypeCode, 'id'))
        return None


    def setEventEditor(self, eventEditor):
        self.eventEditor = eventEditor


    def setAction(self, action):
        self.action = action
        self.actionEndDate = forceDate(self.action.getRecord().value('endDate')) if self.action else None


    def setActionEndDate(self, actionEndDate):
        self.actionEndDate = actionEndDate


    def setReadOnly(self, value=True):
        self.readOnly = value


    def flags(self, index):
        if self.readOnly:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        row = index.row()
        if 0 <= row < len(self._items):
            record = self._items[row]
            if forceRef(record.value('checked_id')):
                return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return CMKBListInDocTableModel.flags(self, index)


    def getEmptyRecord(self):
        result = QtGui.qApp.db.table('Diagnostic').newRecord()
        result.append(QtSql.QSqlField('MKB', QVariant.String))
        result.append(QtSql.QSqlField('checked_id', QVariant.Int))
        result.setValue('checked_id', toVariant(None))
        result.setValue('MKB', toVariant(self.getMKBToDiagnosis(forceRef(result.value('diagnosis_id')))))
        result.setValue('diagnosisType_id', toVariant(self.diagnosisTypeId))
        return result


    def getMKBToDiagnosis(self, diagnosisId):
        MKB = u''
        if diagnosisId:
            db = QtGui.qApp.db
            table = db.table('Diagnosis')
            record = db.getRecordEx(table, 'MKB', [table['id'].eq(diagnosisId), table['deleted'].eq(0)])
            MKB = forceStringEx(record.value('MKB')) if record else u''
        return MKB


    def setMKBAction(self, fieldName, value):
        if self.eventEditor and self.eventEditor.action:
            self.eventEditor.action.getRecord().setValue(fieldName, toVariant(value))
        if self.action:
            self.action.getRecord().setValue(fieldName, toVariant(value))


    def getItemIdList(self):
        diagnosticIdList = []
        items = self._items
        for item in items:
            id = forceRef(item.value('id'))
            if id and id not in diagnosticIdList:
                diagnosticIdList.append(id)
        return diagnosticIdList


    def removeRow(self, row, parentIndex = QModelIndex()):
        checkedId = None
        if 0 <= row and row < len(self._items):
            item = self._items[row]
            checkedId = forceRef(item.value('checked_id'))
            row = self.removeRows(row, 1, parentIndex)
            if checkedId:
                self.checkedIdList.remove(checkedId)
            QObject.parent(self).updateClientDiseases()
            QObject.parent(self).setIsDirty(True)
            self.reset()
        return row


    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            row = index.row()
            column = index.column()
            if row >= 0 and row < len(self._items):
                col = self._cols[column]
                record = self._items[row]
                if record.value(col.fieldName()) == value:
                    return False
            if column == self.Col_EndDate:
                endDate = forceDate(value)
                if row >= 0 and row < len(self._items):
                    record = self._items[row]
                    endDateOld = forceDate(record.value('endDate')) if record else None
                    if endDateOld == endDate:
                        return False
                if endDate and endDate.isValid() and self.actionEndDate and self.actionEndDate.isValid() and endDate > self.actionEndDate:
                    value = toVariant(QDate())
                result = CMKBListInDocTableModel.setData(self, index, value, role)
                return result
            elif column == self.Col_MKB:
                newMKB = forceString(value)
                if newMKB < 'A00' or newMKB > 'B99':
                    return False
                if row >= 0 and row < len(self._items):
                    record = self._items[row]
                    oldMKB = forceString(record.value('MKB')) if record else None
                    if oldMKB == newMKB:
                        return False
                if not newMKB:
                    specifiedMKB = ''
                    specifiedMKBEx = ''
                    specifiedCharacterId = None
                    specifiedTraumaTypeId = None
                    specifiedDispanserId = None
                    specifiedRequiresFillingDispanser = 0
                    specifiedProlongMKB = False
                else:
                    (
                        acceptable,
                        specifiedMKB,
                        specifiedMKBEx,
                        specifiedCharacterId,
                        specifiedTraumaTypeId,
                        specifiedDispanserId,
                        specifiedRequiresFillingDispanser,
                        specifiedProlongMKB,
                    ) = self.eventEditor.checkSpecifyDiagnosis(newMKB)
                    if not acceptable:
                        return False
                value = toVariant(newMKB)
                specifiedCharacterId = forceRef(self.getColIndex('character_id')) if (0 <= row < len(self.items())) else None
                result = CMKBListInDocTableModel.setData(self, index, value, role)
                if result:
                    self.updateCharacterByMKB(row, newMKB, specifiedCharacterId)
                return result
        return CMKBListInDocTableModel.setData(self, index, value, role)


    def loadItems(self, masterId):
        self.checkedIdList = []
        db = QtGui.qApp.db
        cols = '*'
        table = self._table
        filter = [table[self._masterIdFieldName].eq(masterId),
                  table['diagnosisType_id'].eq(self.diagnosisTypeId)]
        if self._filter:
            filter.append(self._filter)
        if table.hasField('deleted'):
            filter.append(table['deleted'].eq(0))
        filter.append(table['endDate'].isNotNull())
#        if self._idxFieldName:
#            order = [self._idxFieldName + u'ASC', 'endDate DESC']
#        else:
        order = ['endDate DESC']
        self._items = db.getRecordList(table, cols, filter, order)
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
                        if field.name() == u'MKB':
                            item.setValue(field.name(), toVariant(self.getMKBToDiagnosis(forceRef(item.value('diagnosis_id')))))
        self.reset()


    def saveItems(self, masterId):
        if self._items is not None:
            db = QtGui.qApp.db
            table = self._table
            masterId = toVariant(masterId)
            masterIdFieldName = self._masterIdFieldName
            idFieldName = self._idFieldName
            idList = []
            for idx, record in enumerate(self._items):
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
            if self.inspectionsResultIdList:
                idList.extend(self.inspectionsResultIdList)
            filter = [table[masterIdFieldName].eq(masterId),
                      table['deleted'].eq(0),
                      table['diagnosisType_id'].eq(self.diagnosisTypeId),
                      'NOT ('+table[idFieldName].inlist(idList)+')']
            if self._filter:
                filter.append(self._filter)
            db.deleteRecord(table, filter)


class CVaccinationTypeCol(CInDocTableCol):
    class CLineEdit(QtGui.QLineEdit):
        def keyPressEvent(self, event):
            chr = unicode(event.text()).lower()
            if r2e.has_key(chr):
                if hasattr(event, 'isNew'):
                    engChr = r2e[chr].upper() if not event.isNew else ' '
                else:
                    engChr = r2e[chr].upper()
                myEvent = QtGui.QKeyEvent(event.type(), ord(engChr), event.modifiers(), engChr, event.isAutoRepeat(), event.count())
                QtGui.QLineEdit.keyPressEvent(self, myEvent)
            elif e2r.has_key(chr):
                if hasattr(event, 'isNew'):
                    engChr = chr.upper() if not event.isNew else ' '
                else:
                    engChr = chr.upper()
                myEvent = QtGui.QKeyEvent(event.type(), ord(engChr), event.modifiers(), engChr, event.isAutoRepeat(), event.count())
                QtGui.QLineEdit.keyPressEvent(self, myEvent)
            else:
                QtGui.QLineEdit.keyPressEvent(self, event)


    def createEditor(self, parent):
        editor = CVaccinationTypeCol.CLineEdit(parent)
        regExp = QRegExp(u'V\d{1,}/\d*|R\d{1,}/\d*|RV\d{1,}/\d*')
        editor.setValidator(QtGui.QRegExpValidator(regExp, None))
        return editor


    def setEditorData(self, editor, value, record):
        editor.setText(forceStringEx(record.value('vaccinationType')))


class CVaccinationsTableModel(CInDocTableModel):
    Col_Date = 0
    Col_InfectionId = 1
    Col_VaccinationType = 2

    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Action_ME_Vaccination', 'id', 'master_id', parent)
        filter = u'''rbInfection.id IN (SELECT rbInf.id
        FROM rbInfection AS rbInf
        INNER JOIN rbInfection_Identification AS rbII ON (rbII.master_id = rbInf.id AND rbII.deleted = 0)
        INNER JOIN rbAccountingSystem AS rbAS ON rbAS.id = rbII.system_id
        WHERE rbAS.urn = 'urn:oid:1.2.643.5.1.13.13.99.2.1111' AND rbII.value != '') '''
        self.addCol(CDateInDocTableCol(u'Дата прививки', 'date', 20, canBeEmpty=True)).setReadOnly(False)
        self.addCol(CRBInDocTableCol(u'Инфекция', 'infection_id', 10, 'rbInfection', filter=filter)).setReadOnly(False)
        self.addCol(CVaccinationTypeCol(u'Тип прививки', 'vaccinationType', 10, maxLength=7)).setReadOnly(False)
        self.addHiddenCol('clientVaccination_id')
        self.readOnly = False
        self.setExtColsPresent(True)
        self.action = None
        self.eventEditor = None
        self.actionEndDate = None
        self.checkedIdList = []
        self.filterInfectionIdList = []
        self.infectionIdList = []


    def setInfectionIdList(self, infectionIdList):
        self.infectionIdList = infectionIdList
        if self.infectionIdList:
            self.cols()[self.Col_InfectionId].setFilter('id IN (%s)'%(u','.join(str(id) for id in self.infectionIdList if id)))
        else:
            self.cols()[self.Col_InfectionId].setFilter('')


    def getItemIdList(self):
        itemIdList = []
        items = self._items
        for item in items:
            id = forceRef(item.value('id'))
            if id and id not in itemIdList:
                itemIdList.append(id)
        return itemIdList


    def setFilterInfectionIdList(self, infectionIdList):
        self.filterInfectionIdList = infectionIdList
        if self.filterInfectionIdList:
            self.cols()[self.Col_InfectionId].setFilter('id IN (%s)'%(u','.join(str(id) for id in self.filterInfectionIdList if id)))
        else:
            self.cols()[self.Col_InfectionId].setFilter('')


    def getEmptyRecord(self):
        result = QtGui.qApp.db.table('Action_ME_Vaccination').newRecord()
        result.append(QtSql.QSqlField('checked_id', QVariant.Int))
        result.setValue('checked_id', toVariant(None))
        return result


    def setEventEditor(self, eventEditor):
        self.eventEditor = eventEditor


    def setAction(self, action):
        self.action = action
        self.actionEndDate = forceDate(self.action.getRecord().value('endDate')) if self.action else None


    def setActionEndDate(self, actionEndDate):
        self.actionEndDate = actionEndDate


    def setReadOnly(self, value=True):
        self.readOnly = value


    def flags(self, index):
        if self.readOnly:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        row = index.row()
        if 0 <= row < len(self._items):
            record = self._items[row]
            clientVaccinationId = forceRef(record.value('clientVaccination_id')) if record else None
            if clientVaccinationId:
                return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return CInDocTableModel.flags(self, index)


    def removeRow(self, row, parentIndex = QModelIndex()):
        checkedId = None
        if 0 <= row and row < len(self._items):
            item = self._items[row]
            checkedId = forceRef(item.value('checked_id'))
            row = self.removeRows(row, 1, parentIndex)
            if checkedId:
                self.checkedIdList.remove(checkedId)
            QObject.parent(self).updateClientVaccinations()
            QObject.parent(self).setIsDirty(True)
            self.reset()
        return row


    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            row = index.row()
            column = index.column()
            if row >= 0 and row < len(self._items):
                col = self._cols[column]
                record = self._items[row]
                if record.value(col.fieldName()) == value:
                    return False
            if column == self.Col_Date:
                date = forceDate(value)
                if date and date.isValid() and self.actionEndDate and self.actionEndDate.isValid() and date > self.actionEndDate:
                    value = toVariant(QDate())
                return CInDocTableModel.setData(self, index, value, role)
        return CInDocTableModel.setData(self, index, value, role)


    def loadItems(self, masterId):
        self.checkedIdList = []
        db = QtGui.qApp.db
        cols = []
        for col in self._cols:
            if not col.external():
                cols.append(col.fieldName())
        cols.append(self._idFieldName)
        cols.append(self._masterIdFieldName)
        if self._idxFieldName:
            cols.append(self._idxFieldName)
        for col in self._hiddenCols:
            cols.append(col)
        table = self._table
        filter = [table[self._masterIdFieldName].eq(masterId)]
        if self._filter:
            filter.append(self._filter)
        if table.hasField('deleted'):
            filter.append(table['deleted'].eq(0))
        if self._idxFieldName:
            order = [self._idxFieldName.name() + u'ASC', u'Action_ME_Vaccination.date DESC']
        else:
            order = [u'Action_ME_Vaccination.date DESC']
        self._items = db.getRecordList(table, cols, filter, order)
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


class CClientVaccinationsTableModel(CInDocTableModel):
    Col_Include = 0
    Col_Date = 1
    Col_InfectionId = 2
    Col_VaccinationType = 3

    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Action_ME_Vaccination', 'id', 'master_id', parent)
        self.addExtCol(CBoolInDocTableCol(u'Выбрать', 'include', 3 ), QVariant.Bool).setReadOnly(False)
        self.addCol(CDateInDocTableCol(u'Дата прививки', 'date', 20, canBeEmpty=True)).setReadOnly(True)
        self.addCol(CRBInDocTableCol(u'Инфекция', 'infection_id', 10, 'rbInfection')).setReadOnly(True)
        self.addCol(CVaccinationTypeCol(u'Тип прививки', 'vaccinationType', 10, maxLength=7)).setReadOnly(True)
        self.addHiddenCol('clientVaccination_id')
        self.readOnly = False
        self.action = None
        self.eventEditor = None


    def setEventEditor(self, eventEditor):
        self.eventEditor = eventEditor


    def setAction(self, action):
        self.action = action


    def cellReadOnly(self, index):
        if QtGui.qApp.userId and QtGui.qApp.userSpecialityId:
            row = index.row()
            if 0 <= row < len(self._items):
                record = self._items[row]
                if record:
                    column = index.column()
                    infectionId = forceRef(record.value('infection_id'))
                    if infectionId and column == 0:
                        return False
        return True


    def setReadOnly(self, value=True):
        self.readOnly = value


    def flags(self, index):
        if self.readOnly or index.column() != 0:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return CInDocTableModel.flags(self, index)


    def getEmptyRecord(self):
        result = QtGui.qApp.db.table('Action_ME_Vaccination').newRecord()
        result.append(QtSql.QSqlField('include', QVariant.Bool))
        result.setValue('include', toVariant(False))
        return result


    def removeRow(self, row, parentIndex = QModelIndex()):
        row = self.removeRows(row, 1, parentIndex)
        self.reset()
        return row


    def selectAll(self):
        for record in self._items:
            record.setValue('include', toVariant(True))
        self.reset()


    def deselectAll(self):
        for record in self._items:
            record.setValue('include', toVariant(False))
        self.reset()


    def hasChecked(self):
        for record in self._items:
            if forceBool(record.value('include')):
                return True
        return False


    def hasNotChecked(self):
        for record in self._items:
            if not forceBool(record.value('include')):
                return True
        return False


    def getCheckedItems(self):
        checkedItems = []
        for item in self._items:
            if forceBool(item.value('include')):
                checkedItems.append(item)
        return checkedItems


    def setData(self, index, value, role=Qt.EditRole):
        row = index.row()
        column = index.column()
        if row >= 0 and row < len(self._items):
            col = self._cols[column]
            record = self._items[row]
            if record.value(col.fieldName()) == value:
                return False
        if role == Qt.CheckStateRole and column == 0:
            return CInDocTableModel.setData(self, index, value, role)
        return False


    def loadItems(self, masterId, clientId):
        self._items = []
        db = QtGui.qApp.db
        infectionDict = {}
        cols = '*'
        table = self._table
        tableAction = db.table('Action')
        tableEvent = db.table('Event')
        queryTable = table.innerJoin(tableAction, tableAction['id'].eq(table['master_id']))
        queryTable = queryTable.innerJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
        filter = [table[self._masterIdFieldName].ne(masterId),
                  tableEvent['client_id'].eq(clientId),
                  table['clientVaccination_id'].isNotNull(),
                  table['date'].isNotNull(),
                  table['deleted'].eq(0),
                  tableAction['deleted'].eq(0),
                  tableEvent['deleted'].eq(0),
                  ]
        if self._filter:
            filter.append(self._filter)
        if self._idxFieldName:
            order = [table[self._idxFieldName].name() + u'ASC', table['date'].name() + u'DESC']
        else:
            order = [table['date'].name() + u'DESC']
        group = [table['clientVaccination_id'].name(),
                 table['date'].name(),
                 table['infection_id'].name(),
                 table['vaccinationType'].name()
                 ]
        self._items = db.getRecordListGroupBy(queryTable, u'Action_ME_Vaccination.*', filter, group, order)
        for item in self._items:
            clientVaccinationId = forceRef(item.value('clientVaccination_id'))
            if clientVaccinationId:
                infectionId = forceRef(item.value('infection_id'))
                infectionLine = infectionDict.get(clientVaccinationId, [])
                if infectionId and infectionId not in infectionLine:
                    infectionLine.append(infectionId)
                    infectionDict[clientVaccinationId] = infectionLine
        # --
        filter = [table[self._masterIdFieldName].eq(masterId),
                  table['deleted'].eq(0),
                  table['clientVaccination_id'].isNotNull(),
                  ]
        if self._filter:
            filter.append(self._filter)
        if self._idxFieldName:
            order = [table[self._idxFieldName].name() + u'ASC', table['date'].name() + u'DESC']
        else:
            order = [table['date'].name() + u'DESC']
        clientVaccinationRecords = db.getRecordList(table, [table['clientVaccination_id'], table['infection_id']], filter, order)
        for clientVaccinationRecord in clientVaccinationRecords:
            clientVaccinationId = forceRef(clientVaccinationRecord.value('clientVaccination_id'))
            if clientVaccinationId:
                infectionId = forceRef(clientVaccinationRecord.value('infection_id'))
                infectionLine = infectionDict.get(clientVaccinationId, [])
                if infectionId and infectionId not in infectionLine:
                    infectionLine.append(infectionId)
                    infectionDict[clientVaccinationId] = infectionLine
        # --
        tableClientVaccination = db.table('ClientVaccination')
        tableInfectionVaccine = db.table('rbInfection_rbVaccine')
        tableRBInfection = db.table('rbInfection')
        queryTable = tableClientVaccination.innerJoin(tableInfectionVaccine, tableInfectionVaccine['vaccine_id'].eq(tableClientVaccination['vaccine_id']))
        queryTable = queryTable.innerJoin(tableRBInfection, tableRBInfection['id'].eq(tableInfectionVaccine['infection_id']))
        cols = [tableClientVaccination['id'].alias('clientVaccination_id'),
                tableClientVaccination['client_id'],
                tableClientVaccination['vaccine_id'],
                tableClientVaccination['datetime'].alias('date'),
                tableClientVaccination['vaccinationType'],
                tableInfectionVaccine['infection_id']
                ]
        cond = [tableClientVaccination['client_id'].eq(clientId),
                tableClientVaccination['deleted'].eq(0),
                #tableClientVaccination['datetime'].isNotNull()
               ]
        if infectionDict.keys():
            for clientVaccinationId, infectionLine in infectionDict.items():
                if infectionLine:
                    cond.append(db.joinOr([db.joinAnd([tableClientVaccination['id'].eq(clientVaccinationId), tableInfectionVaccine['infection_id'].notInlist(infectionLine)]),
                                tableClientVaccination['id'].ne(clientVaccinationId)]))
        group = [tableClientVaccination['id'].name(),
                 tableClientVaccination['datetime'].name(),
                 tableInfectionVaccine['infection_id'].name(),
                 tableClientVaccination['vaccinationType'].name()
                 ]
        order = [tableClientVaccination['datetime'].name() + u'DESC']
        records = db.getRecordListGroupBy(queryTable, cols, cond, group, order)
        for record in records:
            result = QtGui.qApp.db.table('Action_ME_Vaccination').newRecord()
            result.append(QtSql.QSqlField('include', QVariant.Bool))
            result.setValue('include', toVariant(False))
            result.setValue('master_id', toVariant(None))
            result.setValue('clientVaccination_id', record.value('clientVaccination_id'))
            result.setValue('date', record.value('date'))
            result.setValue('infection_id', record.value('infection_id'))
            result.setValue('vaccinationType', record.value('vaccinationType'))
            self._items.append(result)

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
                        if field.name() == u'include':
                            item.setValue(field.name(), toVariant(False))

        self.reset()


    def saveItems(self, masterId):
        pass


class CLocActionTypeInDocTableCol(CInDocTableCol):
    def __init__(self, title, fieldName, width, tableName, **params):
        CInDocTableCol.__init__(self, title, fieldName, width, **params)
        self.tableName  = tableName
        self.actionTypeCache = {}
        self.actionTypeIdList = []

    def setActionTypeIdList(self, actionTypeIdList):
        self.actionTypeIdList = actionTypeIdList

    def toString(self, val, record):
        actionId = forceRef(val)
        if actionId:
            actionTypeName = u''
            if self.actionTypeCache.has_key(actionId):
                actionTypeRecord = self.actionTypeCache[actionId]
            else:
                db = QtGui.qApp.db
                tableAction = db.table('Action')
                tableActionType = db.table(self.tableName)
                queryTable = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
                cond = [tableAction['id'].eq(actionId),
                        tableAction['deleted'].eq(0),
                        tableActionType['deleted'].eq(0)
                        ]
                actionTypeRecord = db.getRecordEx(queryTable, u'%s.*'%(self.tableName), cond)
                if actionTypeRecord:
                    self.actionTypeCache[actionId] = actionTypeRecord
            if actionTypeRecord:
                actionTypeName = forceString(actionTypeRecord.value('name'))
            return toVariant(actionTypeName)
        return QVariant()

    def invalidateRecordsCache(self):
        self.actionTypeCache.invalidate()


class CStatusActionsTableModel(CInDocTableModel):
    Col_Date = 0
    Col_ExaminationId = 1
    Col_PostId = 2
    Col_LastName = 3
    Col_FirstName = 4
    Col_PatrName = 5
    Col_IsComissioner = 6
    Col_Result = 7

    class CLocResultInDocTableCol(CInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.actionIdDomainCache = {}
            self.actionTypeIdDomainCache = {}

        def createEditor(self, parent):
            editor = CStrComboBox(parent)
            #editor.setDomain(domain, isUpdateCurrIndex=False)
            return editor

        def setEditorData(self, editor, value, record):
            editor.setValue(forceStringEx(value))

        def getEditorData(self, editor):
            text = trim(editor.text())
            if text:
                return toVariant(text)
            else:
                return QVariant()

        def invalidateRecordsCache(self):
            self.actionIdDomainCache.invalidate()
            self.actionTypeIdDomainCache.invalidate()

    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Action_ME_Examinations', 'id', 'master_id', parent)
        filter = u'''rbPost.id IN (SELECT rbP.id
        FROM rbPost AS rbP
        INNER JOIN rbPost_Identification AS rbPI ON (rbPI.master_id = rbP.id AND rbPI.deleted = 0)
        INNER JOIN rbAccountingSystem AS rbAS ON rbAS.id = rbPI.system_id
        WHERE rbAS.urn = 'urn:oid:1.2.643.5.1.13.13.11.1002' AND rbPI.value != '') '''
        self.addCol(CDateInDocTableCol(u'Дата осмотра', 'date', 20, canBeEmpty=True)).setReadOnly(False)
        self.addCol(CLocActionTypeInDocTableCol(u'Наименование осмотра', 'examination_id',  20, 'ActionType')).setReadOnly(True)
        self.addCol(CRBInDocTableCol(u'Должность врача', 'post_id', 10, 'rbPost', filter=filter)).setReadOnly(False)
        self.addCol(CInDocTableCol(u'Фамилия врача', 'lastName', 20)).setReadOnly(False)
        self.addCol(CInDocTableCol(u'Имя врача', 'firstName', 20)).setReadOnly(False)
        self.addCol(CInDocTableCol(u'Отчество врача', 'patrName', 20)).setReadOnly(False)
        self.addCol(CBoolInDocTableCol(u'Член ВК', 'isComissioner', 3)).setReadOnly(False)
        self.addCol(self.CLocResultInDocTableCol(u'Заключение', 'result', 30)).setReadOnly(False)
        self.readOnly = False
        self.setExtColsPresent(True)
        self.actionEndDate = None
        self.action = None
        self.actionId = None
        self.actionType = None
        self.actionTypeId = None
        self.eventEditor = None
        self.checkedIdList = []
        self.postIdList = []


    def setPostIdList(self, postIdList):
        self.postIdList = postIdList
        if self.postIdList:
            self.cols()[self.Col_PostId].setFilter('id IN (%s)'%(u','.join(str(id) for id in self.postIdList if id)))
        else:
            self.cols()[self.Col_PostId].setFilter('')


    def getEmptyRecord(self):
        result = QtGui.qApp.db.table('Action_ME_Examinations').newRecord()
        result.append(QtSql.QSqlField('checked_id', QVariant.Int))
        result.setValue('checked_id', toVariant(None))
        result.append(QtSql.QSqlField('person_id', QVariant.Int))
        result.setValue('person_id', toVariant(None))
        domain = u''
        defaultValue = toVariant(None)
        actionIdDomainCache = self.cols()[self.Col_Result].actionIdDomainCache
        if self.actionId and self.actionId in actionIdDomainCache.keys():
            domain, defaultValue = actionIdDomainCache[self.actionId]
        elif self.actionTypeId:
            actionTypeIdDomainResultCache = self.cols()[self.Col_Result].actionTypeIdDomainCache
            if self.actionTypeId in actionTypeIdDomainResultCache.keys():
                domain, defaultValue = actionTypeIdDomainResultCache[self.actionTypeId]
            else:
                domain, defaultValue = propertyActionTypeDomainDefaultValue(u'ME:examination_result', self.actionTypeId)
        result.setValue('result', defaultValue)
        return result


    def getItemIdList(self):
        itemIdList = []
        items = self._items
        for item in items:
            id = forceRef(item.value('id'))
            if id and id not in itemIdList:
                itemIdList.append(id)
        return itemIdList


    def getExaminationIdList(self):
        examinationIdList = []
        items = self._items
        for item in items:
            id = forceRef(item.value('examination_id'))
            if id and id not in examinationIdList:
                examinationIdList.append(id)
        return examinationIdList


    def setEventEditor(self, eventEditor):
        self.eventEditor = eventEditor


    def setAction(self, action):
        self.action = action
        self.actionId = forceRef(self.action.getRecord().value('id')) if self.action else None
        self.actionType = self.action.getType() if self.action else None
        self.actionTypeId = self.actionType.id if self.actionType else None
        self.actionEndDate = forceDate(self.action.getRecord().value('endDate')) if self.action else None


    def setActionEndDate(self, actionEndDate):
        self.actionEndDate = actionEndDate


    def setReadOnly(self, value=True):
        self.readOnly = value


    def flags(self, index):
        if self.readOnly:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        row = index.row()
        column = index.column()
        if 0 <= row < len(self._items):
            record = self._items[row]
            examinationId = forceRef(record.value('examination_id')) if record else None
            if column in (self.Col_ExaminationId, self.Col_Date):
                if examinationId:
                    return Qt.ItemIsSelectable | Qt.ItemIsEnabled
            elif column == self.Col_PostId:
                postId = forceRef(record.value('post_id')) if record else None
                if postId and examinationId:
                    return Qt.ItemIsSelectable | Qt.ItemIsEnabled
            elif column in (self.Col_LastName, self.Col_FirstName, self.Col_PatrName):
                personId = forceRef(record.value('person_id')) if record else None
                if personId and examinationId:
                    return Qt.ItemIsSelectable | Qt.ItemIsEnabled
            elif column == self.Col_IsComissioner:
                if record:
                    postId = forceRef(record.value('post_id'))
                    personId = forceRef(record.value('person_id'))
                    if not postId or not personId:
                        return Qt.ItemIsSelectable | Qt.ItemIsEnabled
                    isComissioner = forceBool(record.value('isComissioner'))
                    if (len(QObject.parent(self).modelMembersMSIPerson._items) >= len(QObject.parent(self).modelMembersMSIPerson.descrList) and personId not in QObject.parent(self).modelMembersMSIPerson.getItemIdList()) and not isComissioner:
                        return Qt.ItemIsSelectable | Qt.ItemIsEnabled
                else:
                    return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return CInDocTableModel.flags(self, index)


    def removeRow(self, row, parentIndex = QModelIndex()):
        checkedId = None
        personId = None
        if 0 <= row and row < len(self._items):
            item = self._items[row]
            checkedId = forceRef(item.value('checked_id'))
            personId = forceRef(item.value('person_id'))
            row = self.removeRows(row, 1, parentIndex)
            if checkedId:
                self.checkedIdList.remove(checkedId)
            self.removeModelMembersMSIPersonRow(personId)
            QObject.parent(self).updateClientStatusActions()
            QObject.parent(self).setIsDirty(True)
            self.reset()
        return row


    def removeModelMembersMSIPersonRow(self, personId):
        if personId:
            membersMSIPersonItems = QObject.parent(self).modelMembersMSIPerson._items
            for membersMSIPersonRow, membersMSIPersonItem in enumerate(membersMSIPersonItems):
                membersMSIPersonId = forceRef(membersMSIPersonItem.value('id'))
                if personId == membersMSIPersonId:
                    QObject.parent(self).modelMembersMSIPerson.removeRow(membersMSIPersonRow)


    def addModelMembersMSIPersonRow(self, personId, postId):
        isComissioner = 0
        modelMembersMSIPerson = QObject.parent(self).modelMembersMSIPerson
        if personId and postId and len(modelMembersMSIPerson._items) < len(modelMembersMSIPerson.descrList) and personId not in modelMembersMSIPerson.getItemIdList():
            recordMembersMSIPerson = modelMembersMSIPerson.getEmptyRecord()
            recordMembersMSIPerson.setValue('id', toVariant(personId))
            modelMembersMSIPerson.addRecord(recordMembersMSIPerson)
            isComissioner = 1
        return isComissioner


    def updateIsComissionerToPersonId(self, findPersonId, findPostId, isComissioner, column):
        for row, item in enumerate(self._items):
            personId = forceRef(item.value('person_id'))
            postId = forceRef(item.value('post_id'))
            if findPersonId == personId and findPostId == postId:
                item.setValue('isComissioner', QVariant(isComissioner))
                self.emitCellChanged(row, column)


    def setData(self, index, value, role=Qt.EditRole):
        row = index.row()
        column = index.column()
        if row >= 0 and row < len(self._items):
            col = self._cols[column]
            record = self._items[row]
            if record.value(col.fieldName()) == value:
                return False
        if role == Qt.CheckStateRole and column == self.Col_IsComissioner:
            if row >= 0 and row < len(self._items):
                record = self._items[row]
                state = value.toInt()[0]
                personId = forceRef(record.value('person_id'))
                postId = forceRef(record.value('post_id'))
                if forceBool(record.value('isComissioner')) and state == Qt.Unchecked:
                    self.updateIsComissionerToPersonId(personId, postId, 0, column)
                    self.removeModelMembersMSIPersonRow(forceRef(record.value('person_id')))
                    return True
                elif len(QObject.parent(self).modelMembersMSIPerson._items) < len(QObject.parent(self).modelMembersMSIPerson.descrList) or personId in QObject.parent(self).modelMembersMSIPerson.getItemIdList():
                    if postId and personId:
                        isComissioner = 0 if state == Qt.Unchecked else 1
                        self.updateIsComissionerToPersonId(personId, postId, isComissioner, column)
                        if isComissioner:
                            isComissioner = self.addModelMembersMSIPersonRow(personId, postId)
                        return True
            return False
        elif role == Qt.EditRole:
            if column == self.Col_Date:
                date = forceDate(value)
                if date and date.isValid() and self.actionEndDate and self.actionEndDate.isValid() and date > self.actionEndDate:
                    value = toVariant(QDate())
        return CInDocTableModel.setData(self, index, value, role)


    def loadItems(self, masterId):
        self.checkedIdList = []
        db = QtGui.qApp.db
        cols = []
        for col in self._cols:
            if not col.external():
                cols.append(col.fieldName())
        cols.append(self._idFieldName)
        cols.append(self._masterIdFieldName)
        if self._idxFieldName:
            cols.append(self._idxFieldName)
        for col in self._hiddenCols:
            cols.append(col)
        table = self._table
        cols.append(u'''IF(Action_ME_Examinations.examination_id IS NOT NULL, (SELECT Action.person_id FROM Action WHERE Action.id = Action_ME_Examinations.examination_id AND Action.deleted = 0 LIMIT 1), NULL) AS person_id''')
        filter = [table[self._masterIdFieldName].eq(masterId)]
        if self._filter:
            filter.append(self._filter)
        if table.hasField('deleted'):
            filter.append(table['deleted'].eq(0))
        if self._idxFieldName:
            order = [self._idxFieldName.name() + u'ASC', u'Action_ME_Examinations.date DESC']
        else:
            order = [u'Action_ME_Examinations.date DESC']
        self._items = db.getRecordList(table, cols, filter, order)
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


class CClientStatusActionsTableModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Action', 'id', 'event_id', parent)
        self.addExtCol(CBoolInDocTableCol(u'Выбрать', 'include', 3 ), QVariant.Bool).setReadOnly(False)
        self.addCol(CDateInDocTableCol(u'Дата осмотра', 'endDate', 20, canBeEmpty=True)).setReadOnly(True)
        self.addCol(CActionTypeTableCol(u'Наименование осмотра', 'actionType_id', 15, None, classesVisible=True)).setReadOnly(True)
        self.addExtCol(CRBInDocTableCol(u'Должность врача', 'post_id', 10, 'rbPost'), QVariant.Int).setReadOnly(True)
        self.addCol(CRBInDocTableCol(u'Врач', 'person_id', 20, 'vrbPersonWithSpeciality')).setReadOnly(True)
        self.readOnly = False
        self.action = None
        self.eventEditor = None


    def setEventEditor(self, eventEditor):
        self.eventEditor = eventEditor


    def setAction(self, action):
        self.action = action


    def cellReadOnly(self, index):
        if QtGui.qApp.userId and QtGui.qApp.userSpecialityId:
            row = index.row()
            if 0 <= row < len(self._items):
                record = self._items[row]
                if record:
                    column = index.column()
                    actionId = forceRef(record.value('id'))
                    if actionId and column == 0:
                        return False
        return True


    def setReadOnly(self, value=True):
        self.readOnly = value


    def flags(self, index):
        if self.readOnly or index.column() != 0:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return CInDocTableModel.flags(self, index)


    def getEmptyRecord(self):
        result = QtGui.qApp.db.table('Action').newRecord()
        result.append(QtSql.QSqlField('post_id', QVariant.Int))
        result.setValue('post_id', toVariant(None))
        result.append(QtSql.QSqlField('include', QVariant.Bool))
        result.setValue('include', toVariant(False))
        return result


    def removeRow(self, row, parentIndex = QModelIndex()):
        row = self.removeRows(row, 1, parentIndex)
        self.reset()
        return row


    def selectAll(self):
        for record in self._items:
            record.setValue('include', toVariant(True))
        self.reset()


    def deselectAll(self):
        for record in self._items:
            record.setValue('include', toVariant(False))
        self.reset()


    def hasChecked(self):
        for record in self._items:
            if forceBool(record.value('include')):
                return True
        return False


    def hasNotChecked(self):
        for record in self._items:
            if not forceBool(record.value('include')):
                return True
        return False


    def getCheckedItems(self):
        checkedItems = []
        for item in self._items:
            if forceBool(item.value('include')):
                checkedItems.append(item)
        return checkedItems


    def setData(self, index, value, role=Qt.EditRole):
        row = index.row()
        column = index.column()
        if row >= 0 and row < len(self._items):
            col = self._cols[column]
            record = self._items[row]
            if record.value(col.fieldName()) == value:
                return False
        if role == Qt.CheckStateRole and column == 0:
            return CInDocTableModel.setData(self, index, value, role)
        return False


    def loadItems(self, masterId, clientId):
        db = QtGui.qApp.db
        cols = '*'
        table = self._table
        tableEvent = db.table('Event')
        tableActionType = db.table('ActionType')
        tablePerson = db.table('Person')
        queryTable = table.innerJoin(tableEvent, tableEvent['id'].eq(table['event_id']))
        queryTable = queryTable.innerJoin(tableActionType, tableActionType['id'].eq(table['actionType_id']))
        queryTable = queryTable.leftJoin(tablePerson, db.joinAnd([tablePerson['id'].eq(table['person_id']), tablePerson['deleted'].eq(0)]))
        filter = [tableEvent['client_id'].eq(clientId),
                  table[self._masterIdFieldName].ne(masterId),
                  tableActionType['class'].eq(0),
                  table['status'].eq(CActionStatus.finished),
                  table['endDate'].isNotNull(),
                  tableEvent['deleted'].eq(0),
                  table['deleted'].eq(0),
                  tableActionType['deleted'].eq(0),
                  tableActionType['serviceType'].inlist([0, 1, 2])
                  ]
        if self._filter:
            filter.append(self._filter)
        if self._idxFieldName:
            order = [table[self._idxFieldName].name() + u'ASC', table['endDate'].name() + u'DESC']
        else:
            order = [table['endDate'].name() + u'DESC']
        self._items = db.getRecordList(queryTable, cols, filter, order)
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
                        if field.name() == u'include':
                            item.setValue(field.name(), toVariant(False))
        self.reset()


    def saveItems(self, masterId):
        pass


class CLabDiagnosticActionsTableModel(CInDocTableModel):
    Col_Date = 0
    Col_ResearchId = 1
    Col_ServiceId = 2
    Col_Titer = 3
    Col_Result = 4

    class CLocResultInDocTableCol(CInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.actionIdDomainCache = {}
            self.actionTypeIdDomainCache = {}

        def createEditor(self, parent):
            editor = CStrComboBox(parent)
            #editor.setDomain(domain, isUpdateCurrIndex=False)
            return editor

        def setEditorData(self, editor, value, record):
            editor.setValue(forceStringEx(value))

        def getEditorData(self, editor):
            text = trim(editor.text())
            if text:
                return toVariant(text)
            else:
                return QVariant()

        def invalidateRecordsCache(self):
            self.actionIdDomainCache.invalidate()
            self.actionTypeIdDomainCache.invalidate()

    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Action_ME_Researches', 'id', 'master_id', parent)
        self.addHiddenCol('researchType')
        self.addCol(CDateInDocTableCol(u'Дата исследования', 'date', 20, canBeEmpty=True)).setReadOnly(False)
        self.addCol(CLocActionTypeInDocTableCol(u'Наименование исследования', 'research_id',  20, 'ActionType')).setReadOnly(True)
        self.addCol(CRBInDocTableCol(u'Услуга', 'service_id', 10, 'rbService', showFields=CRBComboBox.showCodeAndName)).setReadOnly(False)
        self.addCol(CInDocTableCol(u'Титр', 'titer', 20)).setReadOnly(False)
        self.addCol(self.CLocResultInDocTableCol(u'Заключение', 'result', 30)).setReadOnly(False)
        self.readOnly = False
        self.setExtColsPresent(True)
        self.actionEndDate = None
        self.action = None
        self.actionId = None
        self.actionType = None
        self.actionTypeId = None
        self.eventEditor = None
        self.researchType = 1
        self.checkedIdList = []
        self.nomenclativeServiceIdList = []
        self.actionTypeIdList = []


    def getEmptyRecord(self):
        result = QtGui.qApp.db.table('Action_ME_Researches').newRecord()
        result.append(QtSql.QSqlField('checked_id', QVariant.Int))
        result.setValue('checked_id', toVariant(None))
        result.setValue('researchType', toVariant(self.researchType))
        result.append(QtSql.QSqlField('person_id', QVariant.Int))
        result.setValue('person_id', toVariant(None))
        domain = u''
        defaultValue = toVariant(None)
        actionIdDomainCache = self.cols()[self.Col_Result].actionIdDomainCache
        if self.actionId and self.actionId in actionIdDomainCache.keys():
            domain, defaultValue = actionIdDomainCache[self.actionId]
        elif self.actionTypeId:
            actionTypeIdDomainResultCache = self.cols()[self.Col_Result].actionTypeIdDomainCache
            if self.actionTypeId in actionTypeIdDomainResultCache.keys():
                domain, defaultValue = actionTypeIdDomainResultCache[self.actionTypeId]
            else:
                domain, defaultValue = propertyActionTypeDomainDefaultValue(u'ME:laboratory_result', self.actionTypeId)
        result.setValue('result', defaultValue)
        return result


    def getItemIdList(self):
        itemIdList = []
        items = self._items
        for item in items:
            id = forceRef(item.value('id'))
            if id and id not in itemIdList:
                itemIdList.append(id)
        return itemIdList


    def setNomenclativeServiceIdList(self, nomenclativeServiceIdList):
        self.nomenclativeServiceIdList = nomenclativeServiceIdList
        if self.nomenclativeServiceIdList:
            self.cols()[self.Col_ServiceId].setFilter('id IN (%s)'%(u','.join(str(id) for id in self.nomenclativeServiceIdList if id)))
        else:
            self.cols()[self.Col_ServiceId].setFilter('')


    def setActionTypeIdList(self, actionTypeIdList):
        self.actionTypeIdList = actionTypeIdList


    def setEventEditor(self, eventEditor):
        self.eventEditor = eventEditor


    def setAction(self, action):
        self.action = action
        self.actionId = forceRef(self.action.getRecord().value('id')) if self.action else None
        self.actionType = self.action.getType() if self.action else None
        self.actionTypeId = self.actionType.id if self.actionType else None
        self.actionEndDate = forceDate(self.action.getRecord().value('endDate')) if self.action else None


    def setActionEndDate(self, actionEndDate):
        self.actionEndDate = actionEndDate


    def setReadOnly(self, value=True):
        self.readOnly = value


    def flags(self, index):
        if self.readOnly:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        row = index.row()
        column = index.column()
        if 0 <= row < len(self._items):
            record = self._items[row]
            researchId = forceRef(record.value('research_id')) if record else None
            if column in (self.Col_ResearchId, self.Col_Date):
                if researchId:
                    return Qt.ItemIsSelectable | Qt.ItemIsEnabled
            elif column == self.Col_ServiceId:
                serviceId = forceRef(record.value('service_id')) if record else None
                if serviceId and researchId:
                    return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return CInDocTableModel.flags(self, index)


    def removeRow(self, row, parentIndex = QModelIndex()):
        checkedId = None
        if 0 <= row and row < len(self._items):
            item = self._items[row]
            checkedId = forceRef(item.value('checked_id'))
            row = self.removeRows(row, 1, parentIndex)
            if checkedId:
                self.checkedIdList.remove(checkedId)
            QObject.parent(self).updateDiagnosticActions()
            QObject.parent(self).setIsDirty(True)
            self.reset()
        return row


    def getResearchIdList(self):
        researchIdItems = []
        for item in self._items:
            researchId = forceRef(item.value('research_id'))
            if researchId:
                researchIdItems.append(researchId)
        return researchIdItems


    def loadItems(self, masterId):
        self.checkedIdList = []
        db = QtGui.qApp.db
        cols = []
        for col in self._cols:
            if not col.external():
                cols.append(col.fieldName())
        cols.append(self._idFieldName)
        cols.append(self._masterIdFieldName)
        if self._idxFieldName:
            cols.append(self._idxFieldName)
        for col in self._hiddenCols:
            cols.append(col)
        table = self._table
        filter = [table[self._masterIdFieldName].eq(masterId),
                  table['researchType'].eq(self.researchType)
                  ]
        if self._filter:
            filter.append(self._filter)
        if table.hasField('deleted'):
            filter.append(table['deleted'].eq(0))
        if self._idxFieldName:
            order = [self._idxFieldName.name() + u'ASC', u'Action_ME_Researches.date DESC']
        else:
            order = [u'Action_ME_Researches.date DESC']
        self._items = db.getRecordList(table, cols, filter, order)
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


    def saveItems(self, masterId):
        if self._items is not None:
            db = QtGui.qApp.db
            table = self._table
            masterId = toVariant(masterId)
            masterIdFieldName = self._masterIdFieldName
            idFieldName = self._idFieldName
            idList = []
            for idx, record in enumerate(self._items):
                record.setValue(masterIdFieldName, masterId)
                record.setValue('researchType', toVariant(self.researchType))
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
                      table['researchType'].eq(self.researchType),
                      'NOT ('+table[idFieldName].inlist(idList)+')']
            if self._filter:
                filter.append(self._filter)
            db.deleteRecord(table, filter)


    def setData(self, index, value, role=Qt.EditRole):
        row = index.row()
        column = index.column()
        if row >= 0 and row < len(self._items):
            col = self._cols[column]
            record = self._items[row]
            if record.value(col.fieldName()) == value:
                return False
        if role == Qt.EditRole:
            if column == self.Col_Date:
                date = forceDate(value)
                if date and date.isValid() and self.actionEndDate and self.actionEndDate.isValid() and date > self.actionEndDate:
                    value = toVariant(QDate())
        return CInDocTableModel.setData(self, index, value, role)


class CToolDiagnosticActionsTableModel(CInDocTableModel):
    Col_Date = 0
    Col_ResearchId = 1
    Col_ServiceId = 2
    Col_Result = 3

    class CLocResultInDocTableCol(CInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.actionIdDomainCache = {}
            self.actionTypeIdDomainCache = {}

        def createEditor(self, parent):
            editor = CStrComboBox(parent)
            #editor.setDomain(domain, isUpdateCurrIndex=False)
            return editor

        def setEditorData(self, editor, value, record):
            editor.setValue(forceStringEx(value))

        def getEditorData(self, editor):
            text = trim(editor.text())
            if text:
                return toVariant(text)
            else:
                return QVariant()

        def invalidateRecordsCache(self):
            self.actionIdDomainCache.invalidate()
            self.actionTypeIdDomainCache.invalidate()

    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Action_ME_Researches', 'id', 'master_id', parent)
        self.addHiddenCol('researchType')
        self.addCol(CDateInDocTableCol(u'Дата исследования', 'date', 20, canBeEmpty=True)).setReadOnly(False)
        self.addCol(CLocActionTypeInDocTableCol(u'Наименование исследования', 'research_id',  20, 'ActionType')).setReadOnly(True)
        self.addCol(CRBInDocTableCol(u'Услуга', 'service_id', 10, 'rbService', showFields=CRBComboBox.showCodeAndName)).setReadOnly(False)
        self.addCol(self.CLocResultInDocTableCol(u'Заключение', 'result', 30)).setReadOnly(False)
        self.readOnly = False
        self.setExtColsPresent(True)
        self.actionEndDate = None
        self.action = None
        self.actionId = None
        self.actionType = None
        self.actionTypeId = None
        self.eventEditor = None
        self.researchType = 2
        self.checkedIdList = []
        self.nomenclativeServiceIdList = []
        self.actionTypeIdList = []


    def getEmptyRecord(self):
        result = QtGui.qApp.db.table('Action_ME_Researches').newRecord()
        result.append(QtSql.QSqlField('checked_id', QVariant.Int))
        result.setValue('checked_id', toVariant(None))
        result.setValue('researchType', toVariant(self.researchType))
        result.append(QtSql.QSqlField('person_id', QVariant.Int))
        result.setValue('person_id', toVariant(None))
        domain = u''
        defaultValue = toVariant(None)
        actionIdDomainCache = self.cols()[self.Col_Result].actionIdDomainCache
        if self.actionId and self.actionId in actionIdDomainCache.keys():
            domain, defaultValue = actionIdDomainCache[self.actionId]
        elif self.actionTypeId:
            actionTypeIdDomainResultCache = self.cols()[self.Col_Result].actionTypeIdDomainCache
            if self.actionTypeId in actionTypeIdDomainResultCache.keys():
                domain, defaultValue = actionTypeIdDomainResultCache[self.actionTypeId]
            else:
                domain, defaultValue = propertyActionTypeDomainDefaultValue(u'ME:instrumental_result', self.actionTypeId)
        result.setValue('result', defaultValue)
        return result


    def getItemIdList(self):
        itemIdList = []
        items = self._items
        for item in items:
            id = forceRef(item.value('id'))
            if id and id not in itemIdList:
                itemIdList.append(id)
        return itemIdList


    def setNomenclativeServiceIdList(self, nomenclativeServiceIdList):
        self.nomenclativeServiceIdList = nomenclativeServiceIdList
        if self.nomenclativeServiceIdList:
            self.cols()[self.Col_ServiceId].setFilter('id IN (%s)'%(u','.join(str(id) for id in self.nomenclativeServiceIdList if id)))
        else:
            self.cols()[self.Col_ServiceId].setFilter('')


    def setActionTypeIdList(self, actionTypeIdList):
        self.actionTypeIdList = actionTypeIdList


    def setEventEditor(self, eventEditor):
        self.eventEditor = eventEditor


    def setAction(self, action):
        self.action = action
        self.actionId = forceRef(self.action.getRecord().value('id')) if self.action else None
        self.actionType = self.action.getType() if self.action else None
        self.actionTypeId = self.actionType.id if self.actionType else None
        self.actionEndDate = forceDate(self.action.getRecord().value('endDate')) if self.action else None


    def setActionEndDate(self, actionEndDate):
        self.actionEndDate = actionEndDate


    def setReadOnly(self, value=True):
        self.readOnly = value


    def flags(self, index):
        if self.readOnly:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        row = index.row()
        column = index.column()
        if 0 <= row < len(self._items):
            record = self._items[row]
            researchId = forceRef(record.value('research_id')) if record else None
            if column in (self.Col_ResearchId, self.Col_Date):
                if researchId:
                    return Qt.ItemIsSelectable | Qt.ItemIsEnabled
            elif column == self.Col_ServiceId:
                serviceId = forceRef(record.value('service_id')) if record else None
                if serviceId and researchId:
                    return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return CInDocTableModel.flags(self, index)


    def removeRow(self, row, parentIndex = QModelIndex()):
        checkedId = None
        if 0 <= row and row < len(self._items):
            item = self._items[row]
            checkedId = forceRef(item.value('checked_id'))
            row = self.removeRows(row, 1, parentIndex)
            if checkedId:
                self.checkedIdList.remove(checkedId)
            QObject.parent(self).updateDiagnosticActions()
            QObject.parent(self).setIsDirty(True)
            self.reset()
        return row


    def getResearchIdList(self):
        researchIdItems = []
        for item in self._items:
            researchId = forceRef(item.value('research_id'))
            if researchId:
                researchIdItems.append(researchId)
        return researchIdItems


    def loadItems(self, masterId):
        self.checkedIdList = []
        db = QtGui.qApp.db
        cols = []
        for col in self._cols:
            if not col.external():
                cols.append(col.fieldName())
        cols.append(self._idFieldName)
        cols.append(self._masterIdFieldName)
        if self._idxFieldName:
            cols.append(self._idxFieldName)
        for col in self._hiddenCols:
            cols.append(col)
        table = self._table
        filter = [table[self._masterIdFieldName].eq(masterId),
                  table['researchType'].eq(self.researchType)
                  ]
        if self._filter:
            filter.append(self._filter)
        if table.hasField('deleted'):
            filter.append(table['deleted'].eq(0))
        if self._idxFieldName:
            order = [self._idxFieldName.name() + u'ASC', u'Action_ME_Researches.date DESC']
        else:
            order = [u'Action_ME_Researches.date DESC']
        self._items = db.getRecordList(table, cols, filter, order)
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


    def saveItems(self, masterId):
        if self._items is not None:
            db = QtGui.qApp.db
            table = self._table
            masterId = toVariant(masterId)
            masterIdFieldName = self._masterIdFieldName
            idFieldName = self._idFieldName
            idList = []
            for idx, record in enumerate(self._items):
                record.setValue(masterIdFieldName, masterId)
                record.setValue('researchType', toVariant(self.researchType))
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
                      table['researchType'].eq(self.researchType),
                      'NOT ('+table[idFieldName].inlist(idList)+')']
            if self._filter:
                filter.append(self._filter)
            db.deleteRecord(table, filter)


    def setData(self, index, value, role=Qt.EditRole):
        row = index.row()
        column = index.column()
        if row >= 0 and row < len(self._items):
            col = self._cols[column]
            record = self._items[row]
            if record.value(col.fieldName()) == value:
                return False
        if role == Qt.EditRole:
            if column == self.Col_Date:
                date = forceDate(value)
                if date and date.isValid() and self.actionEndDate and self.actionEndDate.isValid() and date > self.actionEndDate:
                    value = toVariant(QDate())
        return CInDocTableModel.setData(self, index, value, role)


class CClientDiagnosticActionsTableModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Action', 'id', 'event_id', parent)
        self.addExtCol(CBoolInDocTableCol(u'Выбрать', 'include', 3 ), QVariant.Bool).setReadOnly(False)
        self.addCol(CDateInDocTableCol(u'Дата исследования', 'endDate', 20, canBeEmpty=True)).setReadOnly(True)
        self.addCol(CActionTypeTableCol(u'Наименование исследования', 'actionType_id', 15, None, classesVisible=True)).setReadOnly(True)
        self.addCol(CRBInDocTableCol(u'Услуга', 'nomenclativeService_id', 10, 'rbService')).setReadOnly(True)
        self.readOnly = False
        self.action = None
        self.eventEditor = None


    def setEventEditor(self, eventEditor):
        self.eventEditor = eventEditor


    def setAction(self, action):
        self.action = action


    def cellReadOnly(self, index):
        if QtGui.qApp.userId and QtGui.qApp.userSpecialityId:
            row = index.row()
            if 0 <= row < len(self._items):
                record = self._items[row]
                if record:
                    column = index.column()
                    actionId = forceRef(record.value('id'))
                    if actionId and column == 0:
                        return False
        return True


    def setReadOnly(self, value=True):
        self.readOnly = value


    def flags(self, index):
        if self.readOnly or index.column() != 0:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return CInDocTableModel.flags(self, index)


    def getEmptyRecord(self):
        result = QtGui.qApp.db.table('Action').newRecord()
        result.append(QtSql.QSqlField('include', QVariant.Bool))
        result.setValue('include', toVariant(False))
        return result


    def removeRow(self, row, parentIndex = QModelIndex()):
        row = self.removeRows(row, 1, parentIndex)
        self.reset()
        return row


    def selectAll(self):
        for record in self._items:
            record.setValue('include', toVariant(True))
        self.reset()


    def deselectAll(self):
        for record in self._items:
            record.setValue('include', toVariant(False))
        self.reset()


    def hasChecked(self):
        for record in self._items:
            if forceBool(record.value('include')):
                return True
        return False


    def hasNotChecked(self):
        for record in self._items:
            if not forceBool(record.value('include')):
                return True
        return False


    def getCheckedItems(self):
        checkedItems = []
        for item in self._items:
            if forceBool(item.value('include')):
                checkedItems.append(item)
        return checkedItems


    def setData(self, index, value, role=Qt.EditRole):
        row = index.row()
        column = index.column()
        if row >= 0 and row < len(self._items):
            col = self._cols[column]
            record = self._items[row]
            if record.value(col.fieldName()) == value:
                return False
        if role == Qt.CheckStateRole and column == 0:
            return CInDocTableModel.setData(self, index, value, role)
        return False


    def loadItems(self, masterId, clientId):
        db = QtGui.qApp.db
        cols = '''Action.*, ActionType.nomenclativeService_id, IF(rbAccountingSystem.urn = 'urn:oid:1.2.643.5.1.13.13.11.1437', 1, IF(rbAccountingSystem.urn = 'urn:oid:1.2.643.5.1.13.13.11.1471', 2, 0)) AS researchType'''
        table = self._table
        tableEvent = db.table('Event')
        tableActionType = db.table('ActionType')
        tableServiceIdentification = db.table('rbService_Identification')
        tableAccountingSystem = db.table('rbAccountingSystem')
        queryTable = table.innerJoin(tableEvent, tableEvent['id'].eq(table['event_id']))
        queryTable = queryTable.innerJoin(tableActionType, tableActionType['id'].eq(table['actionType_id']))
        queryTable = queryTable.innerJoin(tableServiceIdentification, db.joinAnd([tableServiceIdentification['master_id'].eq(tableActionType['nomenclativeService_id']),
        tableServiceIdentification['deleted'].eq(0), tableServiceIdentification['value'].ne('')]))
        queryTable = queryTable.innerJoin(tableAccountingSystem, db.joinAnd([tableAccountingSystem['id'].eq(tableServiceIdentification['system_id']),
        db.joinOr([tableAccountingSystem['urn'].eq(u'urn:oid:1.2.643.5.1.13.13.11.1437'), tableAccountingSystem['urn'].eq(u'urn:oid:1.2.643.5.1.13.13.11.1471')])]))
        filter = [tableEvent['client_id'].eq(clientId),
                  table[self._masterIdFieldName].ne(masterId),
                  tableActionType['class'].eq(1),
                  tableActionType['nomenclativeService_id'].isNotNull(),
                  table['status'].eq(CActionStatus.finished),
                  table['endDate'].isNotNull(),
                  tableEvent['deleted'].eq(0),
                  table['deleted'].eq(0),
                  tableActionType['deleted'].eq(0)
                  ]
        if self._filter:
            filter.append(self._filter)
#        if self._idxFieldName:
#            order = [table[self._idxFieldName].name() + u'ASC', table['endDate'].name() + u'DESC']
#        else:
        order = [table['endDate'].name() + u'DESC']
        self._items = db.getRecordList(queryTable, cols, filter, order)
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
                        if field.name() == u'include':
                            item.setValue(field.name(), toVariant(False))
        self.reset()


    def saveItems(self, masterId):
        pass


class CExportTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self.addColumn(CDateTimeCol(u'Дата и время экспорта', ['dateTime'], 15))
        self.addColumn(CRefBookCol(u'Внешняя система', ['system_id'], 'rbExternalSystem', 20))
        self.addColumn(CEnumCol(u'Состояние', ['success'], [u'не прошёл', u'прошёл'], 15))
        self.addColumn(CTextCol(u'Примечания',     ['note'],                                  6))
        self.setTable('Action_FileAttach_Export')


class CEventExportTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self._parent = parent
        self.firstExport = None
        self.addColumn(CDateTimeCol(u'Дата и время экспорта', ['dateTime'], 40))
        self.addColumn(CRefBookCol(u'Внешняя система', ['system_id'], 'rbExternalSystem', 50))
        self.addColumn(CEnumCol(u'отправка в Региональный РЭМД', ['success'], [u'ошибка', u'успех'], 15))
        self.addColumn(CTextCol(u'Идентификатор', ['externalId'], 6))
        self.addColumn(CTextCol(u'Примечания',     ['note'], 10))

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        column = index.column()
        row    = index.row()
        record = self.getRecordByRow(row)
        if forceInt(record.value('success')) == 1 and not self.firstExport:
            self.firstExport = record
        if role == Qt.DisplayRole: ### or role == Qt.EditRole:
            (col, values) = self.getRecordValues(column, row)
            return col.format(values)
        elif role == Qt.TextAlignmentRole:
            col = self._cols[column]
            return col.alignment()
        elif role == Qt.CheckStateRole:
            (col, values) = self.getRecordValues(column, row)
            return col.checked(values)
        elif role == Qt.ForegroundRole:
            (col, values) = self.getRecordValues(column, row)
            return col.getForegroundColor(values)
        elif role == Qt.DecorationRole:
            if column == 2 and forceInt(record.value('success')) == 1:
                return QVariant(QtGui.QColor('#9ACD32'))
            elif column == 2 and forceInt(record.value('success')) == 0:
                return QVariant(QtGui.QColor('#FF4500'))
            elif column == 0 and self.firstExport == record:
                execDate = forceDate(QtGui.qApp.db.translate('Event', 'id', forceInt(self._parent.itemId()), 'execDate'))
                if column == 0 and execDate.daysTo(forceDate(record.value('dateTime'))) > 2:
                    return QVariant(QtGui.QColor('#FFFF66'))
        elif role == Qt.ToolTipRole:
            if column == 2 and forceInt(record.value('success')) == 1:
                return QVariant(u'Выгружено в ИЭМК')
            elif column == 2 and forceInt(record.value('success')) == 0:
                return QVariant(u'Случай обслуживания не выгружен')
            elif column == 0 and self.firstExport == record:
                execDate = forceDate(QtGui.qApp.db.translate('Event', 'id', forceInt(self._parent.itemId()), 'execDate'))
                if column == 0 and execDate.daysTo(forceDate(record.value('dateTime'))) > 2:
                    return QVariant(u'Случай был выгружен с нарушением сроков')
        return QVariant()


class CAdvancedExportTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self._parent = parent

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        column = index.column()
        row    = index.row()
        record = self.getRecordByRow(row)
        if role == Qt.DisplayRole: ### or role == Qt.EditRole:
            (col, values) = self.getRecordValues(column, row)
            return col.format(values)
        elif role == Qt.TextAlignmentRole:
            col = self._cols[column]
            return col.alignment()
        elif role == Qt.CheckStateRole:
            (col, values) = self.getRecordValues(column, row)
            return col.checked(values)
        elif role == Qt.ForegroundRole:
            (col, values) = self.getRecordValues(column, row)
            return col.getForegroundColor(values)
        elif role == Qt.DecorationRole:
            if column == 5 and (forceInt(record.value('success')) == 1 or self.data(index) == u'успех'):
                return QVariant(QtGui.QColor('#9ACD32'))
            elif column == 5 and forceInt(record.value('success')) == 0:
                return QVariant(QtGui.QColor('#FF4500'))
            elif column == 3 and u'успеш' in forceString(record.value('Message')) and self.table().tableName == 'Information_Messages':
                return QVariant(QtGui.QColor('#9ACD32'))
            elif column == 3 and u'успеш' not in forceString(record.value('Message')) and self.table().tableName == 'Information_Messages':
                return QVariant(QtGui.QColor('#FF4500'))
        elif role == Qt.ToolTipRole:
            if column == 5 and (forceInt(record.value('success')) == 1 or self.data(index) == u'успех'):
                return QVariant(u'Выгружено в ИЭМК')
            elif column == 5 and forceInt(record.value('success')) == 0:
                return QVariant(u'Документ не выгружен')
        return QVariant()


class CRBInfectionTableDialog(CDialogBase):
    def __init__(self, parent=None, tableName='', filter=''):
        CDialogBase.__init__(self, parent)
        self.setObjectName('CRBInfectionTableDialog')
        self.tableName = tableName
        self.filter = filter
        self.edtName = QtGui.QLineEdit(self)
        self.tableView = CInDocTableView(self)
        buttonBox = QtGui.QDialogButtonBox(self)
        layout = QtGui.QGridLayout(self)

        self.edtName.textChanged.connect(self.setNameFilter)
        self.tableView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        self.sourceModel = CRBRecordList(self)
        self.model = CSortFilterProxyTableModel(self, self.sourceModel)
        self.model.setSortRole(Qt.UserRole)
        self.tableView.setModel(self.model)
        self.select()
        self.model.sort(0, Qt.DescendingOrder)

        layout.addWidget(QtGui.QLabel(u'Наименование'), 0, 0)
        layout.addWidget(self.edtName, 0, 1)
        layout.addWidget(self.tableView, 1, 0, 1, 2)
        layout.addWidget(buttonBox, 2, 1)


    def select(self):
        db = QtGui.qApp.db
        tableRBInfection = db.table('rbInfection')
        tableInfectionIdentification = db.table('rbInfection_Identification')
        tableAccountingSystem = db.table('rbAccountingSystem')
        queryTableSystem = tableRBInfection.innerJoin(tableInfectionIdentification, db.joinAnd([tableInfectionIdentification['master_id'].eq(tableRBInfection['id']),
        tableInfectionIdentification['deleted'].eq(0), tableInfectionIdentification['value'].ne('')]))
        queryTableSystem = queryTableSystem.innerJoin(tableAccountingSystem, tableAccountingSystem['id'].eq(tableInfectionIdentification['system_id']))
        systemInfectionList = db.getDistinctRecordList(queryTableSystem, 'rbInfection.id, rbInfection.code, rbInfection.name, 0 AS _chk', [tableAccountingSystem['urn'].eq(u'urn:oid:1.2.643.5.1.13.13.99.2.1111')], tableRBInfection['name'].name())
        self.sourceModel.setItems(systemInfectionList)


    def selectedItemIdList(self):
        idList = []
        for item in self.sourceModel.items():
            if forceBool(item.value('_chk')):
                idList.append(forceRef(item.value('id')))
        return idList


    def setSelectedItemIdList(self, idList):
        for item in self.sourceModel.items():
            if forceRef(item.value('id')) in idList:
                item.setValue('_chk', toVariant(True))
        self.sourceModel.emitColumnChanged(0)
        self.model.invalidate()


    def setCodeFilter(self, value):
        value = forceString(value)
        if value:
            self.model.setFilter('code', value, CSortFilterProxyTableModel.MatchContains)
        else:
            self.model.removeFilter('code')


    def setNameFilter(self, value):
        value = forceString(value)
        if value:
            self.model.setFilter('name', value, CSortFilterProxyTableModel.MatchContains)
        else:
            self.model.removeFilter('name')


    def uncheckAll(self):
        for item in self.sourceModel.items():
            item.setValue('_chk', toVariant(False))
        self.sourceModel.emitColumnChanged(0)
        self.model.invalidate()


    def formatSelectedItemIdList(self):
        return formatIdList(self.tableName, self.selectedItemIdList())


def formatIdList(table, idList, nameField='name'):
    items = []
    for id in idList:
        item = forceString(QtGui.qApp.db.translate(table, 'id', id, nameField))
        if item:
            items.append(item)
    return u', '.join(items) if items else u'Не задано'


class CDiagnosisPerson(CRBInDocTableCol):
    def __init__(self, title, fieldName, width, tableName, **params):
        CRBInDocTableCol.__init__(self, title, fieldName, width, tableName, **params)
        self.eventEditor = params['eventEditor']


    def setEditorData(self, editor, value, record):
        orgId = self.eventEditor.orgId
        specialityId = forceRef(record.value('speciality_id'))
        if self.mayEngageGP(self.eventEditor.eventTypeId, specialityId):
            gpSpecialityId = QtGui.qApp.getGPSpecialityId()
        else:
            gpSpecialityId = None
        if specialityId or gpSpecialityId:
            specialityIdSet = set([specialityId, gpSpecialityId])
            filter = '''speciality_id IN (%s) AND org_id=%d''' % (','.join(str(specialityId) for specialityId in specialityIdSet if specialityId), orgId)
        elif not specialityId:
            filter = '''speciality_id IS NULL AND org_id=%d''' % (orgId)
        else:
            filter = '''org_id=%d''' % (orgId)
        setDate = forceDate(record.value('setDate'))
        if setDate:
            filter += ''' AND (retireDate IS NULL OR DATE(retireDate) > DATE(%s))'''%(QtGui.qApp.db.formatDate(setDate))
        editor.setTable(self.tableName, self.addNone, filter, u'''name ASC''')
        editor.setShowFields(self.showFields)
        editor.setValue(forceInt(value))


    def mayEngageGP(self, eventTypeId, specialityId): # GP == General Practitioner
        records = getEventPlannedInspections(eventTypeId)
        for record in records:
            if (     forceRef(record.value('speciality_id')) == specialityId
                 and self.eventEditor.recordAcceptable(record)
               ):
                   if forceBool(record.value('mayEngageGP')):
                       return True
        return False


class CInspectionsResultModel(CMKBListInDocTableModel):
    __pyqtSignals__ = ('diagnosisChanged()',
                       'rowDeleted()'
                      )

    MKB_allowed_morphology = ['C', 'D']
    def __init__(self, parent):
        self._parent = parent
        CMKBListInDocTableModel.__init__(self, 'Diagnostic', 'id', 'event_id', parent)
        self.isManualSwitchDiagnosis = QtGui.qApp.defaultIsManualSwitchDiagnosis()
        self.isMKBMorphology = QtGui.qApp.defaultMorphologyMKBIsVisible()
        self.characterIdForHandleDiagnosis = None
        self.eventEditor = parent
        self.addCol(CRBInDocTableCol(    u'Специальность', 'speciality_id', 20, 'rbSpeciality')).setReadOnly(False)
        self.addCol(CDiagnosisPerson(    u'Врач',          'person_id',     20, 'vrbPerson', showFields=CRBComboBox.showName, preferredWidth=250, eventEditor=parent))
#        self.addCol(CDateInDocTableCol(  u'Назначен',      'setDate',     15)).setReadOnly()
#        self.addCol(CDateInDocTableCol(  u'Выполнен',      'endDate',     15, canBeEmpty=True))
        self.addExtCol(CRBInDocTableCol( u'Место визита',  'scene_id',    10, 'rbScene', addNone=False, preferredWidth=150), QVariant.Int)
        self.addExtCol(CRBInDocTableCol( u'Тип визита',    'visitType_id', 10, 'rbVisitType', addNone=False, showFields=CRBComboBox.showCodeAndName), QVariant.Int)
        self.addCol(CRBInDocTableCol(    u'ГрЗд',          'healthGroup_id',     4, 'rbHealthGroup', addNone=False, showFields=CRBComboBox.showCode, preferredWidth=150)).setToolTip(u'Группа здоровья')
        self.addExtCol(CICDExInDocTableCol(u'МКБ',           'MKB', 5), QVariant.String)
        self.addCol(CInDocTableCol(u'Описание',     'freeInput', 15))
        self.addCol(CRBInDocTableCol(    u'Результат',     'result_id',          4, 'rbDiagnosticResult', showFields=CRBComboBox.showNameAndCode, preferredWidth=350))
        self.addExtCol(CVisitServiceInDocTableCol(u'Услуга визита', 'service_id', 50, 'rbService', addNone=False, showFields=CRBComboBox.showCodeAndName, preferredWidth=150, eventEditor=parent), QVariant.Int)
        if QtGui.qApp.isExSubclassMKBVisible():
            self.addExtCol(CMKBExSubclassCol(u'РСК', 'exSubclassMKB',  20, defaultHidden=True), QVariant.String).setToolTip(u'Расширенная субклассификация МКБ')
        if QtGui.qApp.isTNMSVisible():
            self.addCol(CTNMSCol(u'TNM-Ст', 'TNMS',  10, defaultHidden=True))
        if self.isMKBMorphology:
            self.addExtCol(CMKBMorphologyCol(u'Морф.', 'morphologyMKB', 10, 'MKB_Morphology', filter='`group` IS NOT NULL', defaultHidden=True), QVariant.String)
#        self.addCol(CDiseaseCharacter(     u'Хар',         'character_id',   7, showFields=CRBComboBox.showCode, preferredWidth=150)).setToolTip(u'Характер')
        if self.isManualSwitchDiagnosis:
            self.addExtCol(CBoolInDocTableCol( u'П',   'handleDiagnosis', 10, defaultHidden=True), QVariant.Int)
            self.characterIdForHandleDiagnosis = forceRef(QtGui.qApp.db.translate('rbDiseaseCharacter', 'code', '1', 'id'))
        self.diagnosisTypeCol = self.addCol(CDiagnosisTypeCol(u'Тип', 'diagnosisType_id', 5, ['1', '2', '9'], defaultHidden=True))
#        self.addCol(CDiseasePhases(        u'Фаза',        'phase_id',       7, showFields=CRBComboBox.showCode, preferredWidth=150)).setToolTip(u'Фаза')
#        self.addCol(CDiseaseStage(         u'Ст',          'stage_id',       7, showFields=CRBComboBox.showCode, preferredWidth=150)).setToolTip(u'Стадия')
#        self.addCol(CRBInDocTableCol(    u'ДН',            'dispanser_id',       4, 'rbDispanser', showFields=CRBComboBox.showCode, preferredWidth=150)).setToolTip(u'Диспансерное наблюдение')
#        self.addCol(CRBLikeEnumInDocTableCol(u'СКЛ',       'sanatorium',         2, CHospitalInfo.names, showFields=CRBComboBox.showCode, preferredWidth=150)).setToolTip(u'Потребность в санаторно-курортном лечении')
#        self.addCol(CRBLikeEnumInDocTableCol(u'Госп',      'hospital',           2, CHospitalInfo.names, showFields=CRBComboBox.showCode, preferredWidth=150)).setToolTip(u'Потребность в госпитализации')
#        self.addCol(CToxicSubstances(u'ТоксВещ', 'toxicSubstances_id', 10, addNone=True, showFields=CRBComboBox.showName, preferredWidth=150)).setToolTip(u'Токсичное вещество')
        self.addHiddenCol(u'setDate')
        self.addHiddenCol(u'endDate')
#        if QtGui.qApp.isTNMSVisible():
#            self.addHiddenCol(u'TNMS')
        self.addHiddenCol(u'character_id')
        #self.addHiddenCol(u'handleDiagnosis')
        self.addHiddenCol(u'phase_id')
        self.addHiddenCol(u'stage_id')
        self.addHiddenCol(u'dispanser_id')
        self.addHiddenCol(u'sanatorium')
        self.addHiddenCol(u'hospital')
        self.addHiddenCol(u'toxicSubstances_id')
        self.columnHandleDiagnosis = self.getColIndex('handleDiagnosis', None)
        self.setEnableAppendLine(False)
        self.readOnly = False
        self.serviceIdUpdateList = []
        self.modelReset.connect(self.resetServiceIdUpdateList)
        self.rowsInserted.connect(self.resetServiceIdUpdateList)
        self.rowsMoved.connect(self.resetServiceIdUpdateList)
        self.rowsRemoved.connect(self.resetServiceIdUpdateList)
        self.prophylaxisPlanningId = None
        self.infectionDiseasesIdList = []
        self.preSpecialityIdList = []
        self.isSelectionGroupOne = False


    def setPreSpecialityIdList(self, preSpecialityIdList):
        self.preSpecialityIdList = preSpecialityIdList
        if self.preSpecialityIdList:
            filter = u'''rbSpeciality.id IN (%s)'''%(u','.join(str(specialityId) for specialityId in self.preSpecialityIdList if specialityId))
        else:
            filter = u''
        self.cols()[self.getColIndex('speciality_id')].setFilter(filter)



    def setInfectionDiseasesIdList(self, infectionDiseasesIdList):
        self.infectionDiseasesIdList = infectionDiseasesIdList


    def resetServiceIdUpdateList(self):
        self.serviceIdUpdateList = [False for x in range(len(self.items()))]


    def setReadOnly(self, value):
        self.readOnly = value


#    def rowCount(self, index=None):
#        return len(self._items) +(1 if len(self._items) == 0 else 0)


    def getCloseOrMainDiagnosisTypeIdList(self):
        return [self.diagnosisTypeCol.codeToId(code) for code in ('1', '2')]


    def manualSwitchDiagnosis(self):
        return self.isManualSwitchDiagnosis


    def getEmptyRecord(self):
        result = CMKBListInDocTableModel.getEmptyRecord(self)
        result.append(QtSql.QSqlField('diagnosis_id',     QVariant.Int))
        result.append(QtSql.QSqlField('defaultMKB',       QVariant.String))
#        if QtGui.qApp.isExSubclassMKBVisible():
#            result.append(QtSql.QSqlField('exSubclassMKB', QVariant.String))
#        if self.isMKBMorphology:
#            result.append(QtSql.QSqlField('morphologyMKB', QVariant.String))
        result.append(QtSql.QSqlField('actuality',        QVariant.Int))
        result.append(QtSql.QSqlField('selectionGroup',   QVariant.Int))
        result.append(QtSql.QSqlField('visit_id',         QVariant.Int))
        result.append(QtSql.QSqlField('scene_id',         QVariant.Int))
        result.append(QtSql.QSqlField('visitType_id',     QVariant.Int))
        #result.append(QtSql.QSqlField('service_id',       QVariant.Int))
        result.append(QtSql.QSqlField('payStatus',        QVariant.Int))
        result.append(QtSql.QSqlField('cTumor_id',        QVariant.Int))
        result.append(QtSql.QSqlField('cNodus_id',        QVariant.Int))
        result.append(QtSql.QSqlField('cMetastasis_id',   QVariant.Int))
        result.append(QtSql.QSqlField('cTNMphase_id',     QVariant.Int))
        result.append(QtSql.QSqlField('pTumor_id',        QVariant.Int))
        result.append(QtSql.QSqlField('pNodus_id',        QVariant.Int))
        result.append(QtSql.QSqlField('pMetastasis_id',   QVariant.Int))
        result.append(QtSql.QSqlField('pTNMphase_id',     QVariant.Int))
        return result


    def flags(self, index=QModelIndex()):
        if self.readOnly:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        result = CMKBListInDocTableModel.flags(self, index)
        row = index.row()
        if row < len(self._items):
            column = index.column()
            if column == self.getColIndex('speciality_id') and self.isSelectionGroupOne:
                return Qt.ItemIsSelectable | Qt.ItemIsEnabled
            if self.isManualSwitchDiagnosis and index.isValid():
                if column == self.columnHandleDiagnosis:
                    characterId = forceRef(self.items()[row].value('character_id'))
                    if characterId != self.characterIdForHandleDiagnosis:
                        result = (result & ~Qt.ItemIsUserCheckable)
#                        return result
            if self.isMKBMorphology and index.isValid():
                if column == self.getColIndex('morphologyMKB'):
                    mkb = forceString(self.items()[row].value('MKB'))
                    if not (bool(mkb) and mkb[0] in CInspectionsResultModel.MKB_allowed_morphology):
                        result = (result & ~Qt.ItemIsEditable)
            if QtGui.qApp.isExSubclassMKBVisible() and index.isValid():
                if column == self.getColIndex('exSubclassMKB'):
                    mkb = forceString(self.items()[row].value('MKB'))
                    if len(mkb) != 6:
                        return Qt.ItemIsSelectable | Qt.ItemIsEnabled
            if column == self.getColIndex('service_id'): # Обновляем состояние ячеек "Услуга визита"
                item = self.items()[row]
                person = forceRef(item.value('person_id'))
                endDate = forceDate(item.value('endDate'))
                curServiceId = forceRef(item.value('service_id'))
                specialityId = forceRef(item.value('speciality_id'))
                visitTypeId = forceRef(item.value('visitType_id'))
                sceneId = forceRef(item.value('scene_id'))
                if not person or endDate.isNull() or not sceneId or not visitTypeId:
                    self.setData(index, False, Qt.UserRole)
                    return Qt.NoItemFlags
                else:
                    if not curServiceId and not self.data(index, Qt.UserRole):
                        db = QtGui.qApp.db
                        personServiceId = forceRef(db.translate('rbSpeciality', 'id', specialityId, 'service_id'))
                        serviceId = getExactServiceId(None, None, personServiceId,
                                                      self._parent.eventTypeId, visitTypeId, sceneId, specialityId,
                                                      self._parent.clientSex, self._parent.clientAge,
                                                      forceDate(self._parent.eventSetDateTime),
                                                      self._parent.clientBirthDate)
                        item.setValue('service_id', QVariant(serviceId))
                        self.setData(index, True, Qt.UserRole)
                    return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
        return result


    def cellReadOnly(self, index):
        return False


    def isExposed(self, row):
        if 0 <= row < len(self.items()):
            return not self.canChangeDiagnostic(row)
        return False


    def canChangeDiagnostic(self, row):
        payStatus = self.payStatus(row)
        visitId = forceRef(self.items()[row].value('visit_id')) if 0 <= row < len(self.items()) else None
        eventId = forceRef(self.items()[row].value('event_id')) if 0 <= row < len(self.items()) else None
        if not payStatus and visitId and eventId:
            db = QtGui.qApp.db
            tableVisit = db.table('Visit')
            cond = [ tableVisit['event_id'].eq(eventId),
                     tableVisit['id'].eq(visitId),
                     tableVisit['payStatus'].ne(0),
                     tableVisit['deleted'].eq(0)
                   ]
            record = db.getRecordEx(tableVisit, [tableVisit['payStatus']], where=cond)
            payStatus = forceInt(record.value('payStatus')) if record else 0
        if payStatus and not QtGui.qApp.userHasRight(urEditAfterInvoicingEvent):
            return False
        return True


    def getItemIdList(self):
        diagnosticIdList = []
        items = self._items
        for item in items:
            id = forceRef(item.value('id'))
            if id and id not in diagnosticIdList:
                diagnosticIdList.append(id)
        return diagnosticIdList


    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if 0 <= row < len(self._items):
            if role == Qt.EditRole:
                if QtGui.qApp.isTNMSVisible() and 0 <= row < len(self.items()) and column == self.getColIndex('TNMS'):
                    col = self._cols[column]
                    record = self._items[row]
                    tnmsMap = {}
                    for keyName, fieldName in CEventEditDialog.TNMSFieldsDict.items():
                        tnmsMap[keyName] = forceRef(record.value(fieldName))
                    return QVariant([forceString(record.value(col.fieldName())), tnmsMap])
        if index.isValid() and 0 <= row < len(self._items):
            if role == Qt.DisplayRole:
                if column == self.getColIndex('setDate'):
                    record = self.items()[row]
                    setDate = record.value('setDate').toDate()
                    endDate = record.value('endDate').toDate()
                    if endDate and endDate < setDate:
                        return QVariant()
                elif column == self.getColIndex('service_id'):
                    item = self.items()[row]
                    person = forceRef(item.value('person_id'))
                    endDate = forceDate(item.value('endDate'))
                    visitTypeId = forceRef(item.value('visitType_id'))
                    sceneId = forceRef(item.value('scene_id'))
                    if not person or endDate.isNull() or not sceneId or not visitTypeId:
                        return QVariant('')
            elif role == Qt.UserRole:
                return self.serviceIdUpdateList[row].toBool()
        return CMKBListInDocTableModel.data(self, index, role)


    def setData(self, index, value, role=Qt.EditRole):
        row = index.row()
        column = index.column()
        if row >= 0 and row < len(self._items):
            col = self._cols[column]
            record = self._items[row]
            if record.value(col.fieldName()) == value:
                return False
        isRowExist = (0 <= row < len(self.items()))
        if role == Qt.EditRole:
            if not variantEq(self.data(index, role), value):
                if not self.canChangeDiagnostic(row):
                    return False
                if column == self.getColIndex('diagnosisType_id'): # тип, может быть изменён всегда
                    if forceInt(value) == self.diagnosisTypeCol.ids[0]:
                        for i, record in enumerate(self.items()):
                            if forceInt(record.value('diagnosisType_id')) == self.diagnosisTypeCol.ids[0]:
                                record.setValue('diagnosisType_id', toVariant(self.diagnosisTypeCol.ids[1]))
                                self.emitCellChanged(i, 0)
                                self.emit(SIGNAL('diagnosisChanged()'))
                elif column == self.getColIndex('speciality_id'):
                    if self.isSelectionGroupOne:
                        return False
                    else:
                        specialityId = forceRef(value)
                        personSpecialityId = None
                        record = self.items()[row] if isRowExist else None
                        record.setValue('speciality_id', toVariant(specialityId))
                        if specialityId:
                            personId = forceRef(record.value('person_id'))
                            if personId:
                                personRecord = QtGui.qApp.db.getRecord('Person', 'speciality_id', personId)
                                personSpecialityId = forceRef(personRecord.value('speciality_id')) if personRecord else None
                            if personSpecialityId != specialityId:
                                record.setValue('person_id', toVariant(None))
                        self.emitRowChanged(row)
                elif column == self.getColIndex('person_id'): # врач, изменяется всегда
                    personId = forceRef(value)
                    personRecord = QtGui.qApp.db.getRecord('Person', 'speciality_id', personId)
                    personSpecialityId = forceRef(personRecord.value('speciality_id')) if personRecord else None
                    record = self.items()[row] if isRowExist else None
                    if personId and record:
                        record.setValue('speciality_id', toVariant(personSpecialityId))
                    self.emitRowChanged(row)
                elif column == self.getColIndex('MKB'): # код МКБ
                    newMKB = forceString(value)
                    if not newMKB:
                        value = self.items()[row].value('defaultMKB') if isRowExist else u''
                        newMKB = forceString(value)
                    if newMKB:
                        if not QObject.parent(self).checkDiagnosis(newMKB, self.specialityId(row)):
                            return False
                    if isRowExist:
                        value = toVariant(newMKB)
                        specifiedCharacterId = forceRef(self.items()[row].value('character_id')) if isRowExist else None
                        self.updateCharacterByMKB(row, newMKB, specifiedCharacterId)
                        self.updateToxicSubstancesByMKB(row, newMKB)
                        self.updateTNMS(index, self.items()[row], newMKB)
                        self.updateMKBTNMS(self.items()[row], newMKB)
                        self.updateExSubclass(index, self.items()[row], newMKB)
                        self.updateMKBToExSubclass(self.items()[row], newMKB)
                        self.checkPrevTNMS(index, self.items()[row], newMKB)
                if isRowExist and column == self.getColIndex('dispanser_id'): # Диспансерное наблюдение
                    record = self.items()[row]
                    if QtGui.qApp.checkDispanserObservation():
                        dispanserId = forceInt(value)
                        if not self.eventEditor.checkNewDispanserObservationValue(dispanserId, record):
                            value = None
                    if not value.toString() and forceInt(record.value('dispanser_id')):
                        db = QtGui.qApp.db
                        tableVisit = db.table('Visit')
                        eventId = forceRef(record.value('event_id'))
                        visitId = None
                        if eventId:
                            recordPP = db.getRecordEx(tableVisit, [tableVisit['id']], [tableVisit['event_id'].eq(eventId), tableVisit['deleted'].eq(0)])
                            visitId = forceRef(recordPP.value('id')) if recordPP else None
                        if visitId:
                            tablePP = db.table('ProphylaxisPlanning')
                            cond = [
                                tablePP['visit_id'].eq(visitId),
                                tablePP['parent_id'].isNotNull(),
                            ]
                            recordPP = db.getRecordEx(tablePP, '*', cond)
                            if recordPP:
                                if QtGui.QMessageBox.warning(None,
                                                             u'Внимание!',
                                                             u'Снятие статуса ДН приведёт к удалению факта явки в ККДН.\n'
                                                             u'Продолжить?',
                                                             QtGui.QMessageBox.No | QtGui.QMessageBox.Yes,
                                                             QtGui.QMessageBox.Yes) == QtGui.QMessageBox.Yes:
                                    recordPP.setNull('visit_id')
                                    db.updateRecord(tablePP, recordPP)
                                    self.prophylaxisPlanningId = forceRef(recordPP.value('id'))
                                else:
                                    value = forceInt(record.value('dispanser_id'))
                elif QtGui.qApp.isTNMSVisible() and isRowExist and column == self.getColIndex('TNMS'):
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
                elif QtGui.qApp.isExSubclassMKBVisible() and isRowExist and column == self.getColIndex('exSubclassMKB'):
                    record = self.items()[row]
                    self.updateMKBToExSubclass(record, forceStringEx(record.value('MKB')))
                    return CMKBListInDocTableModel.setData(self, index, value, role)
                result = CMKBListInDocTableModel.setData(self, index, value, role)
                if result:
                    self.emit(SIGNAL('diagnosisChanged()'))
                return result
        elif role == Qt.UserRole:
            self.serviceIdUpdateList[row] = QVariant(value)
        else:
            return True


    def checkPrevTNMS(self, index, record, MKB):
        if QtGui.qApp.isTNMSVisible():
            newMKB = forceString(MKB)

            db = QtGui.qApp.db
            tableDiagnostic = db.table('Diagnostic')
            tableDiagnosis = db.table('Diagnosis')
            cols = [tableDiagnostic['TNMS']]
            cond = [
                tableDiagnosis['client_id'].eq(self._parent.clientId),
                tableDiagnosis['MKB'].eq(newMKB),
                tableDiagnosis['deleted'].eq(0),
                tableDiagnostic['deleted'].eq(0),
                tableDiagnostic['event_id'].ne(self._parent.itemId()),
                tableDiagnostic['TNMS'].ne(''),
            ]

            tableQuery = tableDiagnostic
            tableQuery = tableQuery.leftJoin(tableDiagnosis, tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']))

            prev_record = db.getRecordEx(tableQuery, cols=cols, where=cond, order=['Diagnostic.id DESC'])

            if prev_record and forceString(prev_record.value('TNMS')):
                TNMS = forceString(prev_record.value('TNMS'))

                answer = QtGui.QMessageBox.warning(self._parent,
                                               u'Внимание!',
                                               u'Ранее для диагноза %s было указано значение TNM-Cт - %s. Применить его?' %(newMKB, TNMS) ,
                                               QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel,
                                               QtGui.QMessageBox.Cancel)
                if answer == QtGui.QMessageBox.Ok:
                    # Обновление TNMS для текущего элемента
                    record.setValue('TNMS', toVariant(TNMS))
                    #row = index.row()
                    #item = self.items()[row]

                    from library.CustomComboBoxLike import CCustomComboBoxLike
                    from library.TNMS.TNMSComboBox import convertTNMSStringToId

                    idx = self.createIndex(index.row(), self.getColIndex('TNMS'))
                    editor = self.cols()[self.getColIndex('TNMS')].createEditor(self._parent)
                    ids = convertTNMSStringToId(TNMS, newMKB)
                    self.setData(idx, QVariant([TNMS, ids]))

                    editor.setValue(TNMS, ids)
                    editor._popup = editor.createPopup()
                    editor._popup.installEventFilter(editor)
                    adjustPopupToWidget(editor, editor._popup)
                    editor._popup.setEndDate(editor.endDate)
                    editor._popup.setTempValue(CCustomComboBoxLike.getValue(editor))
                    editor._popup.updateItemsComboBoxes(editor.MKB, editor.isTest)
                    editor.updateValueFromPopup()


    def updateMKBToExSubclass(self, record, MKB):
        if QtGui.qApp.isExSubclassMKBVisible():
            self.cols()[self.getColIndex('exSubclassMKB')].setMKB(forceString(MKB))


    def updateExSubclass(self, index, record, MKB):
        if QtGui.qApp.isExSubclassMKBVisible():
            newMKB = forceString(MKB)
            if self.cols()[self.getColIndex('exSubclassMKB')].MKB != newMKB:
                record.setValue('exSubclassMKB', toVariant(u''))
                self.emitRowChanged(index.row())


    def updateMKBTNMS(self, record, MKB):
        if QtGui.qApp.isTNMSVisible():
            self.cols()[self.getColIndex('TNMS')].setMKB(forceString(MKB))


    def updateTNMS(self, index, record, MKB):
        if QtGui.qApp.isTNMSVisible():
            newMKB = forceString(MKB)
            if self.cols()[self.getColIndex('TNMS')].MKB != newMKB:
                row = index.row()
                tnmsMap = {}
                for keyName, fieldName in CEventEditDialog.TNMSFieldsDict.items():
                    tnmsMap[keyName] = None
                    record.setValue(fieldName, toVariant(None))
                record.setValue('TNMS', toVariant(u''))
                self.emitRowChanged(row)


    def diagnosisTypeId(self, row):
        return forceRef(self.items()[row].value('diagnosisType_id')) if (row >= 0 and row < len(self.items())) else None


    def diagnosisType(self, row):
        diagnosisTypeId = self.diagnosisTypeId(row)
        if diagnosisTypeId in self.diagnosisTypeCol.ids:
            return self.diagnosisTypeCol.ids.index(diagnosisTypeId)
        else:
            return -1


    def specialityId(self, row):
        return forceInt(self.items()[row].value('speciality_id')) if (row >= 0 and row < len(self.items())) else None


    def visitTypeId(self, row):
        return forceInt(self.items()[row].value('visitType_id')) if (row >= 0 and row < len(self.items())) else None


    def payStatus(self, row):
        if 0 <= row < len(self.items()):
            return forceInt(self.items()[row].value('payStatus')) if (row >= 0 and row < len(self.items())) else None
        else:
            return 0


    def isAccompDiagnostic(self, row):
        diagnosisType = self.diagnosisType(row)
        return diagnosisType == 2


    def removeRowEx(self, row):
        diagnosisType = self.diagnosisType(row)
        if diagnosisType == 2:
            self.removeRows(row, 1)
            self._parent.updateActionsDiagnosisByDiagnostics()
        else:
            i = row+1
            while i<len(self.items()) and self.diagnosisType(i) == 2:
                i += 1
            self.removeRows(row, i-row)
            self._parent.updateActionsDiagnosisByDiagnostics()


    def setSetDate(self, row, date):
        self.items()[row].setValue('setDate',  QVariant(date))
        self.emitCellChanged(row, 3)


    def updateToxicSubstancesByMKB(self, row, MKB):
        toxicSubstanceIdList = getToxicSubstancesIdListByMKB(MKB)
        item = self.items()[row]
        toxicSubstanceId = forceRef(item.value('toxicSubstances_id'))
        if toxicSubstanceId and toxicSubstanceId in toxicSubstanceIdList:
            return
        item.setValue('toxicSubstances_id', toVariant(None))
        self.emitCellChanged(row, self.getColIndex('toxicSubstances_id'))


    def saveItems(self, masterId):
        if self._items is not None:
            db = QtGui.qApp.db
            table = self._table
            masterId = toVariant(masterId)
            masterIdFieldName = self._masterIdFieldName
            idFieldName = self._idFieldName
            idList = []
            for idx, record in enumerate(self._items):
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
            if self.infectionDiseasesIdList:
                idList.extend(self.infectionDiseasesIdList)
            filter = [table[masterIdFieldName].eq(masterId),
                      'NOT ('+table[idFieldName].inlist(idList)+')']
            if self._filter:
                filter.append(self._filter)
            db.deleteRecord(table, filter)

