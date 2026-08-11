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

from PyQt4                      import QtGui, QtSql
from PyQt4.QtCore import Qt, QDate, QDateTime, QString, QVariant, pyqtSignature, SIGNAL

from appendix.fsselnv2.app.selectReadyTempInvalidDocumentIds import selectReadyTempInvalidDocumentById

from library.DialogBase         import CDialogBase
from library.RecordLock         import CRecordLockMixin
from library.database           import CTableRecordCache, decorateString
from library.DateEdit           import CDateEdit
from library.crbcombobox        import CRBComboBox
from library.interchange        import (
                                        getCheckBoxValue,
                                        getComboBoxValue,
                                        getLineEditValue,
                                        getRBComboBoxValue,
                                        getSpinBoxValue,
                                        setDateEditValue,
                                        getDateEditValue,
                                        setCheckBoxValue,
                                        setComboBoxValue,
                                        setLineEditValue,
                                        setRBComboBoxValue,
                                        setSpinBoxValue
                                       )
from library.ICDUtils           import MKBwithoutSubclassification
from library.InDocTable         import (
                                        CBoolInDocTableCol,
                                        CDateInDocTableCol,
                                        CDateTimeInDocTableCol,
                                        CEnumInDocTableCol,
                                        CInDocTableCol,
                                        CIntInDocTableCol,
                                        CRBInDocTableCol,
                                        CSelectStrInDocTableCol,
                                        CInDocTableModel,
                                        CRecordListModel
                                       )
from library.ICDInDocTableCol   import CICDExInDocTableCol
from library.ItemsListDialog    import CItemEditorBaseDialog
from library.MSCAPI             import MSCApi
from library.PrintInfo import CInfoContext, CDateInfo
from library.PrintTemplates     import getPrintButton, applyTemplate
from library.ROComboBox         import CROEditableComboBox
from library.TableModel import CTableModel, CTextCol, CDateCol, CDesignationCol

from library.Utils import (
    copyFields,
    forceBool,
    forceDate,
    forceDateTime,
    forceInt,
    forceRef,
    forceString,
    forceStringEx,
    formatDate,
    formatSex,
    toVariant,
    formatName,
    trim,
    calcAgeTuple,
    withWaitCursor,
    exceptionToUnicode
)

from Events.Action              import CAction
from Events.ActionStatus        import CActionStatus
from Events.ActionTypeComboBox  import CActionTypeTableCol
from Events.EventEditDialog     import CEventEditDialog
from Events.EventInfo import CEventInfoList
from Events.MKBInfo             import CMKBInfo
from Events.TempInvalidInfo     import (
                                        CTempInvalidInfo,
                                        CTempInvalidReasonInfo,
                                        CTempInvalidExtraReasonInfo,
                                        CTempInvalidDocTypeInfo,
                                        CTempInvalidPeriodInfoList,
                                        CTempInvalidDocumentItemInfoList,
                                        CTempInvalidResultInfo,
                                        CTempInvalidBreakInfo,
                                        CTempInvalidDocumentCareInfoList
                                       )
from Events.TempInvalidRequestsToFss import annulment, searchCase, showDocumentInfo
from Events.TempInvalidRequestFSSByNumber import CTempInvalidRequestFSSByNumber

from Events.Utils               import (
                                        getAvailableCharacterIdByMKB,
                                        getDiagnosisId2,
                                        specifyDiagnosis,
                                        getActionTypeIdListByFlatCode
                                       )

from Exchange.FSSv2.generated.FileOperationsLnService_types import ns2 as fssMo, ns3 as fssEln
from Exchange.FSSv2.generated.fssns import fssNsDict
from Exchange.FSSv2.FssSignInfo import CFssSignInfo
from Exchange.FSSv2.zsiUtils    import (
                                        createPyObject,
                                        convertQDateToTuple,
                                        fixu,
                                        serializeToXmlAndSignIt,
                                        restoreFromXml
                                       )

from RefBooks.TempInvalidState  import CTempInvalidState
from RefBooks.TypeEducationalInstitution.Info import CTypeEducationalInstitutionInfo
from Registry.Utils             import CClientInfo, getClientWork, getClientMiniInfo
from Registry.ClientEditDialog  import CClientEditDialog
from Registry.ClientRelationsEditDialog import CClientRelationsEditDialog


from Orgs.Orgs                  import selectOrganisation
from Orgs.PersonComboBoxEx import CPersonFindInDocTableCol
from Orgs.Utils                 import getOrganisationInfo, getOrganisationShortName

from Users.Rights               import (
                                        urAdmin,
                                        urRegWriteInsurOfficeMark,
                                        urRegTabWriteRegistry,
                                        urRegTabReadRegistry,
                                        urEditIssueDateTempInvalid,
                                        urRegTabExpertChangeSignVUT)

from Events.Ui_TempInvalidEditDialog               import Ui_TempInvalidEditDialog
from Events.Ui_TempInvalidSignatureSubjectSelector import Ui_TempInvalidSignatureSubjectSelector
from Events.Ui_TempInvalidTransferSubjectSelector  import Ui_TempInvalidTransferSubjectSelector


titleList = (u'ВУТ', u'Инвалидность', u'Ограничения жизнедеятельности')


class CTempInvalidEditDialog(CItemEditorBaseDialog, Ui_TempInvalidEditDialog):
    TempInvalid      = 0
    Disability       = 1
    VitalRestriction = 2
    MSI              = 3

    InabilitySheet     = '1'
    MedicalCertificate = '2'

    def __init__(self,  parent, clientCache):
        CItemEditorBaseDialog.__init__(self, parent, 'TempInvalid')
        self.addModels('Documents', CTempInvalidDocumentsModel(self, clientCache))
        self.addObject('modelPeriods', CTempInvalidPeriodModel(self))
        self.addObject('modelCare', CTempInvalidDocumentCareModel(self, clientCache))
        self.addObject('modelMedicalCommission', CMedicalCommissionModel(self))
        self.addObject('modelMedicalCommissionMSI', CMedicalCommissionMSIModel(self))
        self.addObject('actCreateContinuation', QtGui.QAction(u'Создать продолжение внешнего документа', self))
        self.addObject('actRequestFSSForDocument', QtGui.QAction(u'Запросить состояние ЛН в СФР', self))
        self.addObject('actRequestFSSForPrevDocument', QtGui.QAction(u'Запросить состояние предыдущего ЛН в СФР', self))
        self.addObject('actRequestFSSByNumber', QtGui.QAction(u'Запросить данные ЭЛН по номеру', self))
        self.addObject('actAnnulment', QtGui.QAction(u'Запросить аннулирование ЛН в СФР', self))
        self.addObject('btnSelectToTransfer', QtGui.QPushButton(u'Передать в СФР', self))
        self.addObject('btnApply', QtGui.QPushButton(u'Применить', self))
        self.addObject('btnDuplicate', QtGui.QPushButton(u'Создать Дубликат ЭЛН', self))
        self.addObject('btnRequestFss', QtGui.QPushButton(u'Запросить СФР', self))
        self.addObject('btnSignTempInvalidParts', QtGui.QPushButton(u'Подписать', self))
        self.addObject('btnRevokeTempInvalidSignature', QtGui.QPushButton(u'Снять подпись', self))
        self.addObject('btnTempInvalidProlong', QtGui.QPushButton(u'Продолжить', self))
        self.addObject('btnPrint', getPrintButton(self, 'tempInvalid', u'Печать'))

        self.setupUi(self)
        self.setWindowFlags(Qt.Window)
        self.setWindowTitleEx(u'Документ временной нетрудоспособности')
        self.setWindowState(Qt.WindowMaximized)
        self.grpMainInfo.setStyleSheet('QGroupBox {font-weight: bold; color:red;}')
        self.grpTempInvalidPeriods.setStyleSheet('QGroupBox {font-weight: bold;}')
        self.grpTempInvalidDocuments.setStyleSheet('QGroupBox {font-weight: bold;}')
        self.grbTempInvalidDocumentCare.setStyleSheet('QGroupBox {font-weight: bold;}')
        self.grpMedicalCommission.setStyleSheet('QGroupBox {font-weight: bold;}')
        self.grpMedicalCommissionMSI.setStyleSheet('QGroupBox {font-weight: bold;}')
        self.tblPeriods.setModel(self.modelPeriods)
        self.tblDocuments.setModel(self.modelDocuments)
        self.tblDocuments.setSelectionModel(self.selectionModelDocuments)
        self.tblPeriods.addPopupDelRow()
        self.tblDocuments.addPopupDirectionMC()
        self.tblDocuments.addPopupDuplicateCurrentRow()
        self.tblDocuments.addPopupAction(self.actCreateContinuation)
        self.tblDocuments.addPopupSeparator()
        self.tblDocuments.addPopupDelRow()
        self.tblDocuments.addPopupDetermineContinued()
        self.tblDocuments.addPopupSeparator()
        self.tblDocuments.addPopupAction(self.actRequestFSSForDocument)
        self.tblDocuments.addPopupAction(self.actRequestFSSForPrevDocument)
        self.tblDocuments.addPopupAction(self.actRequestFSSByNumber)
        self.tblDocuments.addPopupSeparator()
        self.tblDocuments.addPopupAction(self.actAnnulment)

        self.tblCare.setModel(self.modelCare)
        self.tblCare.addPopupDelRow()
        self.tblMedicalCommission.setModel(self.modelMedicalCommission)
        self.tblMedicalCommission.addPopupEditDirectionMC()
        self.tblMedicalCommission.addPopupDelRow()
        self.tblMedicalCommissionMSI.setModel(self.modelMedicalCommissionMSI)
        self.tblMedicalCommissionMSI.addPopupEditDirectionMC()
        self.tblMedicalCommissionMSI.addPopupDelRow()
        self.clientCache = clientCache
        self.modelPeriods.setEventEditor(self)
        self.modelDocuments.setEventEditor(self)
        self.modelCare.setEventEditor(self)
        self.modelMedicalCommission.setEventEditor(self)
        self.modelMedicalCommissionMSI.setEventEditor(self)
        self.buttonBox.addButton(self.btnSelectToTransfer, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnApply, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnDuplicate, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnRequestFss, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnSignTempInvalidParts, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnRevokeTempInvalidSignature, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnTempInvalidProlong, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnPrint, QtGui.QDialogButtonBox.ActionRole)
        self.btnDuplicate.setEnabled(False)
        self.clientId = None
        self.clientSex = None
        self.clientAge = None
        self.diagnosisId = None
        self.prevId = None
        self.lastId = None
        self.prevState = None
        self.orgId = QtGui.qApp.currentOrgId()
        self.personId = None
        self.docCode = None
        self.docId = None
        self.prolonging = False
        self.newProlonging = False
        self.saveProlonging = False
        self.updateOtherwiseDate = False
        self.isUpdatePlaceWork = False
        self.state = CTempInvalidState.opened
        self.setupDirtyCather()
        self.lblDiagnosis.setVisible(False)
        self.edtDiagnosis.setVisible(False)
        self.cmbDiseaseCharacter.setVisible(False)
        self.edtCaseBegDate.setDate(None)
        self.edtCaseBegDate.setEnabled(False)
        self.chkInsuranceOfficeMark.setEnabled(QtGui.qApp.userHasRight(urRegWriteInsurOfficeMark))
        self.modifiableDiagnosisesMap = {}
        self.mapSpecialityIdToDiagFilter = {}
        self.blankParams = {}
        self.defaultBlankMovingId = None
        self.cmbDiseaseCharacter.setTable('rbDiseaseCharacter', order='code')
        self.edtNumberPermit.setText(u'')
        self.edtBegDatePermit.setDate(QDate())
        self.edtEndDatePermit.setDate(QDate())
        self.cmbBreak.setTable('rbTempInvalidBreak')
        self.edtBreakDate.setDate(QDate())
        self.edtBegDateStationary.setDate(QDate())
        self.edtEndDateStationary.setDate(QDate())
        self.cmbDisability.setTable('rbTempInvalidRegime', filter='type = 1')
        self.cmbResult.setTable('rbTempInvalidResult')
        self.edtResultDate.setDate(QDate())
        self.edtResultOtherwiseDate.setDate(QDate())
        self.placeRegistry = False
        self.isReasonPrimary = False
        self.documentsSignatures = {}
        self.documentsSignatureR = False
        self.documentsSignatureB = False
        self.documentsSignatureExternalR = False
        self.periodsSignaturesC = {}
        self.periodsSignaturesD = {}
        self.edtMseDate.setDate(QDate())
        self.onOpenEventId = None
        self.cmbReceiver.setNeedSNILS(True)
        self.cmbReceiver.connect(self.cmbReceiver.lineEdit(), SIGNAL('textChanged(QString)'), self.on_cmbReceiver_textChanged)
        self.transfer_tempId_list = []
        self.chkUserCert.setEnabled(False)
        self.connect(self.cmbEvent.lineEdit(), SIGNAL('textChanged(QString)'), self.on_cmbEvent_textChanged)
        if forceBool(QtGui.qApp.preferences.appPrefs.get('csp', '')):
            self.setCsp()


    @pyqtSignature('QString')
    def on_cmbEvent_textChanged(self):
        if not self.edtMseDate.date():
            event_id = self.cmbEvent.value()
            if event_id:
                if self.onOpenEventId == event_id:
                    self.onOpenEventId = -1
                    return
                db = QtGui.qApp.db
                tableAction = db.table('Action')
                tableEvent = db.table('Event')
                tableActionType = db.table('ActionType')
                cond = [tableEvent['deleted'].eq(0),
                         tableAction['deleted'].eq(0),
                         tableActionType['deleted'].eq(0),
                         tableActionType['flatCode'].eq('inspection_mse'),
                         tableEvent['id'].eq(event_id)]
                table = tableAction.leftJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
                table = table.leftJoin(tableActionType, tableAction['actionType_id'].eq(tableActionType['id']))
                record = db.getRecordEx(table, tableAction['endDate'], cond)
                if record:
                    self.edtMseDate.setDate(forceDate(record.value('endDate')))

    @pyqtSignature('QString')
    def on_edtDiagnosis_textChanged(self, text):
        if len(forceString(text)) > 1:
            self.cmbEvent.setMKB(forceString(text[:3]) + '...')
        else:
            self.cmbEvent.setMKB(None)


    def setRecord(self, record):
        self.isReasonPrimary = True
        CItemEditorBaseDialog.setRecord(self, record)
        setCheckBoxValue(self.chkInsuranceOfficeMark, record, 'insuranceOfficeMark')
        self.state = forceInt(record.value('state'))
        self.clientId = forceRef(record.value('client_id'))
        self.cmbReceiver.setClientId(self.clientId)
        self.cmbEvent.setClientId(self.clientId)
        self.diagnosisId = forceRef(record.value('diagnosis_id'))
        MKB, MKBEx, characterId = self.getMKBs()
        self.edtDiagnosis.setText(MKB)
        self.cmbDiseaseCharacter.setValue(characterId)
        self.setType(forceInt(record.value('type')))
        setRBComboBoxValue(self.cmbDoctype, record, 'doctype_id')
        setRBComboBoxValue(self.cmbReason,  record, 'tempInvalidReason_id')
        setRBComboBoxValue(self.cmbChangedReason,  record, 'tempInvalidChangedReason_id')
        if requiredDiagnosis(self.cmbReason.value()):
            self.lblDiagnosis.setVisible(True)
            self.edtDiagnosis.setVisible(True)
            self.cmbDiseaseCharacter.setVisible(True)
        setRBComboBoxValue(self.cmbExtraReason,  record, 'tempInvalidExtraReason_id')
        setLineEditValue(self.edtNumberPermit, record, 'numberPermit')
        setDateEditValue(self.edtBegDatePermit, record, 'begDatePermit')
        setDateEditValue(self.edtEndDatePermit, record, 'endDatePermit')
        setRBComboBoxValue(self.cmbBreak,  record, 'break_id')
        setDateEditValue(self.edtBreakDate, record, 'breakDate')
        setDateEditValue(self.edtBegDateStationary, record, 'begDateStationary')
        setDateEditValue(self.edtEndDateStationary, record, 'endDateStationary')
        setRBComboBoxValue(self.cmbDisability,  record, 'disability_id')
        setRBComboBoxValue(self.cmbResult,  record, 'result_id')
        setDateEditValue(self.edtResultDate, record, 'resultDate')
        setDateEditValue(self.edtResultOtherwiseDate, record, 'resultOtherwiseDate')
        setLineEditValue(self.edtOGRN, record, 'OGRN')
        setRBComboBoxValue(self.cmbTypeEducationalInstitution, record, 'institution_id')
        setLineEditValue(self.edtInfContact, record, 'inf_contact')
        self.on_edtOGRN_textEdited(self.edtOGRN.text())
        self.clientSex, self.clientAge, self.clientAgeTuple = self.getClientSexAge(self.clientId)
        setComboBoxValue(self.cmbOtherSex,  record, 'sex')
        setSpinBoxValue(self.edtOtherAge,   record, 'age')
        self.cmbReceiver.setValue(forceRef(record.value('client_id')))
        setDateEditValue(self.edtMseDate, record, 'mseDate')
        self.onOpenEventId = forceRef(record.value('event_id'))
        self.cmbEvent.setValue(forceRef(record.value('event_id')))
        self.edtCaseBegDate.setDate(forceDate(record.value('caseBegDate')))
        self.cmbAccountPregnancyTo12Weeks.setCurrentIndex(forceInt(record.value('accountPregnancyTo12Weeks')))
        self.setEnabledWidget(self.chkInsuranceOfficeMark.isChecked(), [self.cmbDoctype, self.cmbReason, self.cmbExtraReason, self.edtDiagnosis, self.cmbDiseaseCharacter, self.chkInsuranceOfficeMark, self.tblPeriods])
        db = QtGui.qApp.db
        table = db.table('TempInvalid')
        condDeleted = table['deleted'].eq(0)
        condClient = table['client_id'].eq(self.clientId)
        prevId = forceRef(record.value('prev_id'))
        prevAnnulled = False
        if prevId and self.state != CTempInvalidState.annulled:
            prevCond = [condDeleted, condClient,
                        table['id'].eq(prevId),
                        table['state'].eq(CTempInvalidState.annulled)
                        ]
            prevRecord = db.getRecordEx(table, '*', prevCond, 'endDate DESC')
            if prevRecord:
                self.setPrev(prevRecord)
            prevAnnulled = bool(prevRecord)
        if not prevId or not prevAnnulled:
            prevCond = [condDeleted, condClient,
                        table['state'].eq(CTempInvalidState.extended),
                        table['endDate'].eq(forceDate(record.value('begDate')).addDays(-1))
                        ]
            prevRecord = db.getRecordEx(table, '*', prevCond, 'endDate DESC')
            self.setPrev(prevRecord)
        self.modelPeriods.loadItems(self.itemId())
        self.on_modelPeriods_dataChanged(0, 0)
        recordLast = db.getRecordEx(table, [table['id']], [table['prev_id'].eq(self.itemId()), table['deleted'].eq(0)], 'endDate')
        self.lastId = forceRef(recordLast.value('id')) if recordLast else None
        self.modelDocuments.loadItems(self.itemId(), forceRef(record.value('client_id')), self.prevId, self.lastId)
        self.modelCare.setTempInvalidId(self.itemId())
        self.modelCare.setTempInvalidClientId(forceRef(record.value('client_id')))
        self.modelMedicalCommission.loadItems(self.itemId())
        self.medicalCommissionMSILoadItems()
        self.updateLength()
        fullLength, externalLength = self.modelPeriods.calcLengths()
        self.btnTempInvalidProlong.setEnabled(self.state == CTempInvalidState.opened and fullLength and self.getIsNumberDisabilityFill())
        self.prolonging = False
        self.defaultBlankMovingId = None
        self.isReasonPrimary = False
        self.newProlonging = False
        state = self.getTempInvalidState()
        self.cmbReceiver.setReadOnly(not (state == CTempInvalidState.opened  and self.getDocumentsSignature(self.modelDocuments.getTempInvalidDocumentIdList())))
        self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(not (state == CTempInvalidState.annulled and self.itemId() and self.lastId))
        self.btnApply.setEnabled(not (state == CTempInvalidState.annulled and self.itemId() and self.lastId))
        self.setDocumentsSignatures()
        self.tblDocuments.setCurrentRow(0)


    def getFssStatusToReason(self):
        documents = self.modelDocuments.items()
        db = QtGui.qApp.db
        tableDocumentExport = db.table('TempInvalidDocument_Export')
        for document in documents:
            isExternal = forceBool(document.value('isExternal'))
            fssStatus = forceStringEx(document.value('fssStatus'))
            if fssStatus == u'P0' and not isExternal:
                documentId = forceRef(document.value('id'))
                if documentId:
                    cond = [tableDocumentExport['master_id'].eq(documentId),
                            tableDocumentExport['success'].eq(1)
                            ]
                    record = db.getRecordEx(tableDocumentExport, [tableDocumentExport['id']], cond)
                    documentExportId = forceRef(record.value('id')) if record else None
                    if documentExportId:
                        return True
        return False


    def setDocumentsSignaturesNoSave(self):
        self.documentsSignatures, self.documentsSignatureR, self.documentsSignatureB, self.documentsSignatureExternalR, self.periodsSignaturesC, self.periodsSignaturesD = self.getDocumentsSignaturesNoSave()
        self.modelPeriods.setDocumentsSignatures(self.documentsSignatures, self.documentsSignatureR, self.documentsSignatureExternalR, self.periodsSignaturesC, self.periodsSignaturesD)
        self.modelDocuments.setDocumentsSignatures(self.documentsSignatures, self.documentsSignatureR, self.documentsSignatureExternalR)
        self.protectClosedSignatures()


    def setDocumentsSignatures(self):
        self.documentsSignatures, self.documentsSignatureR, self.documentsSignatureB, self.documentsSignatureExternalR, self.periodsSignaturesC, self.periodsSignaturesD = self.getDocumentsSignatures(self.modelDocuments.getTempInvalidDocumentIdList())
        self.modelPeriods.setDocumentsSignatures(self.documentsSignatures, self.documentsSignatureR, self.documentsSignatureExternalR, self.periodsSignaturesC, self.periodsSignaturesD)
        self.modelDocuments.setDocumentsSignatures(self.documentsSignatures, self.documentsSignatureR, self.documentsSignatureExternalR)
        self.protectClosedSignatures()


    def protectClosedSignatures(self):
        isProtected = False
        isBreakProtected = False
        isReasonProtected = self.getFssStatusToReason() # False
        if self.documentsSignatureR:
            isProtected = True
            isBreakProtected = True
        else:
            if self.documentsSignatureB:
                isBreakProtected = True
        isEditable = isProtected
        if hasattr(self, 'modelPeriods'):
            self.modelPeriods.setReadOnly(isProtected)
        if hasattr(self, 'modelDocuments'):
            self.modelDocuments.setReadOnly(isProtected)
        if hasattr(self, 'modelCare'):
            isReadOnlyCare = self.modelCare.isReadOnly()
            self.modelCare.setReadOnly(isReadOnlyCare if isReadOnlyCare else isProtected)
        if hasattr(self, 'modelMedicalCommission'):
            self.modelMedicalCommission.setReadOnly(isProtected)
        if hasattr(self, 'modelMedicalCommissionMSI'):
            self.modelMedicalCommissionMSI.setReadOnly(isProtected)
        if hasattr(self, 'cmbDoctype'):
            self.cmbDoctype.setReadOnly(isEditable)
        if hasattr(self, 'cmbReason'):
            self.cmbReason.setReadOnly(isReasonProtected)
        if hasattr(self, 'cmbChangedReason'):
            self.cmbChangedReason.setReadOnly(isEditable)
        if hasattr(self, 'cmbExtraReason'):
            self.cmbExtraReason.setReadOnly(isEditable)
        if hasattr(self, 'cmbReceiver'):
            self.cmbReceiver.setReadOnly(isEditable)
        if hasattr(self, 'btnClientRelations'):
            self.btnClientRelations.setEnabled(not isEditable)
        if hasattr(self, 'cmbOtherSex'):
            self.cmbOtherSex.setReadOnly(isEditable)
        if hasattr(self, 'edtOtherAge'):
            self.edtOtherAge.setReadOnly(isEditable)
        if hasattr(self, 'edtDiagnosis'):
            self.edtDiagnosis.setReadOnly(isEditable)
        if hasattr(self, 'cmbDiseaseCharacter'):
            self.cmbDiseaseCharacter.setReadOnly(isEditable)
        if hasattr(self, 'edtCaseBegDate'):
            self.edtCaseBegDate.setReadOnly(isEditable)
        if hasattr(self, 'edtBegDatePermit'):
            self.edtBegDatePermit.setReadOnly(isEditable)
        if hasattr(self, 'edtEndDatePermit'):
            self.edtEndDatePermit.setReadOnly(isEditable)
        if hasattr(self, 'edtNumberPermit'):
            self.edtNumberPermit.setReadOnly(isEditable)
        if hasattr(self, 'edtOGRN'):
            self.edtOGRN.setReadOnly(isEditable)
        if hasattr(self, 'btnSelectHeadOrganisation'):
            self.btnSelectHeadOrganisation.setEnabled(not isEditable)
        if hasattr(self, 'cmbAccountPregnancyTo12Weeks'):
            self.cmbAccountPregnancyTo12Weeks.setReadOnly(isEditable)
        # if hasattr(self, 'edtBreakDate'):
        #     self.edtBreakDate.setReadOnly(isBreakProtected)
        # if hasattr(self, 'cmbBreak'):
        #     self.cmbBreak.setReadOnly(isBreakProtected)
        if hasattr(self, 'edtBegDateStationary'):
            self.edtBegDateStationary.setReadOnly(isEditable)
        if hasattr(self, 'edtEndDateStationary'):
            self.edtEndDateStationary.setReadOnly(isEditable)
        if hasattr(self, 'cmbDisability'):
            self.cmbDisability.setReadOnly(isEditable)
        if hasattr(self, 'chkInsuranceOfficeMark'):
            self.chkInsuranceOfficeMark.setEnabled(not isEditable)
        if hasattr(self, 'edtResultDate'):
            self.edtResultDate.setReadOnly(isEditable)
        if hasattr(self, 'edtResultOtherwiseDate'):
            self.edtResultOtherwiseDate.setReadOnly(isEditable)


    def getDocumentsSignatures(self, tempInvalidDocumentIdList):
        documentsSignatures = {}
        periodsSignaturesC = {}
        periodsSignaturesD = {}
        documentsSignatureR = False
        documentsSignatureB = False
        documentsSignatureExternalR = False
        if tempInvalidDocumentIdList:
            db = QtGui.qApp.db
            tableTI = db.table('TempInvalid')
            tableTIR = db.table('rbTempInvalidResult')
            tableTD = db.table('TempInvalidDocument')
            electronicRecord = db.getRecordEx(tableTD, 'id', [tableTD['id'].inlist(tempInvalidDocumentIdList), tableTD['electronic'].ne(0), tableTD['deleted'].eq(0)])
            if bool(electronicRecord):
                tableTDS = db.table('TempInvalidDocument_Signature')
                cols = [tableTDS['id'],
                        tableTDS['master_id'],
                        tableTDS['subject'],
                        tableTDS['signPerson_id'],
                        tableTDS['status'],
                        tableTDS['begDate'],
                        tableTDS['endDate'],
                        tableTD['isExternal'],
                        tableTD['master_id'].alias('tempInvalidId')
                        ]
                queryTable = tableTD.innerJoin(tableTDS, tableTDS['master_id'].eq(tableTD['id']))
                records = db.getRecordList(queryTable, cols, [tableTDS['master_id'].inlist(tempInvalidDocumentIdList)])
                for record in records:
                    #signatureId = forceRef(record.value('id'))
                    masterId = forceRef(record.value('master_id'))
                    #signPersonId = forceRef(record.value('signPerson_id'))
                    subject = QString(forceStringEx(record.value('subject')))
                    if len(subject) > 0:
                        documentsSignaturesDict = documentsSignatures.get(masterId, {})
                        subject1 = subject.left(1)
                        if subject1 == u'R':
                            #resultId = None
                            state = None
                            isExternal = forceBool(record.value('isExternal'))
                            tempInvalidId = forceRef(record.value('tempInvalidId'))
                            if tempInvalidId:
                                tableQuery = tableTI.innerJoin(tableTIR, tableTIR['id'].eq(tableTI['result_id']))
                                tempInvalidRecord = db.getRecordEx(tableQuery, [tableTI['result_id'], tableTIR['state']], [tableTI['id'].eq(tempInvalidId), tableTI['deleted'].eq(0)])
                                if tempInvalidRecord:
                                    #resultId = forceRef(tempInvalidRecord.value('result_id'))
                                    state = forceInt(tempInvalidRecord.value('state'))
                            if state is not None and state == CTempInvalidState.closed:
                                documentsSignatureR = True
                                documentsSignaturesDict[u'R'] = True
                            elif state is not None and state != CTempInvalidState.closed and isExternal:
                                documentsSignatureExternalR = True
                                documentsSignaturesDict[u'REx'] = True
                            documentsSignatures[masterId] = documentsSignaturesDict
                        elif subject1 == u'B':
                            documentsSignatureB = True
                            documentsSignaturesDict[u'B'] = True
                            documentsSignatures[masterId] = documentsSignaturesDict
                        elif subject1 == u'C':
                            subjectN = subject.right(len(subject)-1)
                            if subjectN:
                                subjectNRow = forceInt(subjectN)
                                documentsSignaturesLine = documentsSignaturesDict.get(u'C', [])
                                if subjectNRow not in documentsSignaturesLine:
                                    documentsSignaturesLine.append(subjectNRow)
                                    documentsSignaturesDict[u'C'] = documentsSignaturesLine
                                    documentsSignatures[masterId] = documentsSignaturesDict
                                    periodsSignaturesC[subjectNRow] = True
                        elif subject1 == u'D':
                            subjectN = subject.right(len(subject)-1)
                            if subjectN:
                                subjectNRow = forceInt(subjectN)
                                begDate = forceDate(record.value('begDate'))
                                endDate = forceDate(record.value('endDate'))
                                if begDate and endDate:
                                    for periodRow, periodRecord in enumerate(self.modelPeriods.items()):
                                        begDatePeriod = forceDate(periodRecord.value('begDate'))
                                        endDatePeriod = forceDate(periodRecord.value('endDate'))
                                        if begDatePeriod and endDatePeriod:
                                            if begDate == begDatePeriod and endDate == endDatePeriod:
                                                subjectNRow = periodRow
                                                break
                                documentsSignaturesLine = documentsSignaturesDict.get(u'D', [])
                                if subjectNRow not in documentsSignaturesLine:
                                    documentsSignaturesLine.append(subjectNRow)
                                    documentsSignaturesDict[u'D'] = documentsSignaturesLine
                                    documentsSignatures[masterId] = documentsSignaturesDict
                                    periodsSignaturesD[subjectNRow] = True
        return documentsSignatures, documentsSignatureR, documentsSignatureB, documentsSignatureExternalR, periodsSignaturesC, periodsSignaturesD


    def getDocumentsSignaturesNoSave(self):
        documentsSignatures = {}
        periodsSignaturesC = {}
        periodsSignaturesD = {}
        documentsSignatureR = False
        documentsSignatureB = False
        documentsSignatureExternalR = False
        db = QtGui.qApp.db
        tableTI = db.table('TempInvalid')
        tableTIR = db.table('rbTempInvalidResult')
        for document in self.modelDocuments.items():
            if forceBool(document.value('electronic')):
                for record in document.signatures.records():
                    #signatureId = forceRef(record.value('id'))
                    masterId = forceRef(record.value('master_id'))
                    #signPersonId = forceRef(record.value('signPerson_id'))
                    subject = QString(forceStringEx(record.value('subject')))
                    if len(subject) > 0:
                        documentsSignaturesDict = documentsSignatures.get(masterId, {})
                        subject1 = subject.left(1)
                        if subject1 == u'R':
                            #resultId = None
                            state = None
                            isExternal = forceBool(document.value('isExternal'))
                            tempInvalidId = forceRef(document.value('master_id'))
                            if tempInvalidId:
                                tableQuery = tableTI.innerJoin(tableTIR, tableTIR['id'].eq(tableTI['result_id']))
                                tempInvalidRecord = db.getRecordEx(tableQuery, [tableTI['result_id'], tableTIR['state']], [tableTI['id'].eq(tempInvalidId), tableTI['deleted'].eq(0)])
                                if tempInvalidRecord:
                                    #resultId = forceRef(tempInvalidRecord.value('result_id'))
                                    state = forceInt(tempInvalidRecord.value('state'))
                            if state is not None and state == CTempInvalidState.closed:
                                documentsSignatureR = True
                                documentsSignaturesDict[u'R'] = True
                            elif state is not None and state != CTempInvalidState.closed and isExternal:
                                documentsSignatureExternalR = True
                                documentsSignaturesDict[u'REx'] = True
                            documentsSignatures[masterId] = documentsSignaturesDict
                        elif subject1 == u'B':
                            documentsSignatureB = True
                            documentsSignaturesDict[u'B'] = True
                            documentsSignatures[masterId] = documentsSignaturesDict
                        elif subject1 == u'C':
                            subjectN = subject.right(len(subject)-1)
                            if subjectN:
                                subjectNRow = forceInt(subjectN)
                                documentsSignaturesLine = documentsSignaturesDict.get(u'C', [])
                                if subjectNRow not in documentsSignaturesLine:
                                    documentsSignaturesLine.append(subjectNRow)
                                    documentsSignaturesDict[u'C'] = documentsSignaturesLine
                                    documentsSignatures[masterId] = documentsSignaturesDict
                                    periodsSignaturesC[subjectNRow] = True
                        elif subject1 == u'D':
                            subjectN = subject.right(len(subject)-1)
                            if subjectN:
                                subjectNRow = forceInt(subjectN)
                                begDate = forceDate(record.value('begDate'))
                                endDate = forceDate(record.value('endDate'))
                                if begDate and endDate:
                                    for periodRow, periodRecord in enumerate(self.modelPeriods.items()):
                                        begDatePeriod = forceDate(periodRecord.value('begDate'))
                                        endDatePeriod = forceDate(periodRecord.value('endDate'))
                                        if begDatePeriod and endDatePeriod:
                                            if begDate == begDatePeriod and endDate == endDatePeriod:
                                                subjectNRow = periodRow
                                                break
                                documentsSignaturesLine = documentsSignaturesDict.get(u'D', [])
                                if subjectNRow not in documentsSignaturesLine:
                                    documentsSignaturesLine.append(subjectNRow)
                                    documentsSignaturesDict[u'D'] = documentsSignaturesLine
                                    documentsSignatures[masterId] = documentsSignaturesDict
                                    periodsSignaturesD[subjectNRow] = True
        return documentsSignatures, documentsSignatureR, documentsSignatureB, documentsSignatureExternalR, periodsSignaturesC, periodsSignaturesD


    def medicalCommissionLoadItems(self):
        self.modelMedicalCommission.loadItems(self.itemId())


    def medicalCommissionMSILoadItems(self):
        self.modelMedicalCommissionMSI.setTempInvalidId(self.itemId())
        self.modelMedicalCommissionMSI.loadItems(self.modelMedicalCommission.getActionIdList())


    def getIsNumberDisabilityFill(self):
        items = self.modelDocuments.items()
        for row, item in enumerate(items):
            number = forceStringEx(item.value('number'))
            if not number:
                return False
        return True


    def getDocumentsSignature(self, tempInvalidDocumentIdList):
        if tempInvalidDocumentIdList:
            db = QtGui.qApp.db
            tableTD = db.table('TempInvalidDocument')
            electronicRecord = db.getRecordEx(tableTD, 'id', [tableTD['id'].inlist(tempInvalidDocumentIdList), tableTD['electronic'].ne(0), tableTD['deleted'].eq(0)])
            if bool(electronicRecord):
                tableTDS = db.table('TempInvalidDocument_Signature')
                record = db.getRecordEx(tableTDS, 'id', [tableTDS['master_id'].inlist(tempInvalidDocumentIdList)])
                return not bool(record)
        return True


    def setEnabledWidget(self, checked, listWidget = []):
        if not self.isReasonPrimary:
            isReadOnlyReceiver = self.getTempInvalidState() == CTempInvalidState.opened and self.getDocumentsSignature(self.modelDocuments.getTempInvalidDocumentIdList())
            self.cmbReceiver.setReadOnly(not isReadOnlyReceiver)
        enabled = QtGui.qApp.userHasRight(urRegWriteInsurOfficeMark)
        otherPersonEnabled = requiredOtherPerson(self.cmbReason.value()) if self.type_ != CTempInvalidEditDialog.Disability else True
        if not otherPersonEnabled or self.placeRegistry:
            if self.cmbReceiver.isReadOnly():
                self.cmbReceiver.setValue(self.clientId)
        pregnancyAndBirthEnabled = requiredPregnancyAndBirth(self.cmbReason.value())
        diagnosisEnabled = requiredDiagnosis(self.cmbReason.value())
        self.lblDiagnosis.setVisible(diagnosisEnabled)
        self.edtDiagnosis.setVisible(diagnosisEnabled)
        self.cmbDiseaseCharacter.setVisible(diagnosisEnabled)
        receiverId = self.cmbReceiver.value()
        sex, ageClient, clientAgeTuple = self.getClientSexAge(receiverId)
        otherAge = self.edtOtherAge.value()
        if otherPersonEnabled and ageClient >= 15 or not otherAge or otherAge < 15:
            self.cmbOtherSex.setCurrentIndex(sex)
            self.edtOtherAge.setValue(ageClient)
        if checked:
            for widget in listWidget:
                widget.setEnabled(enabled)
            self.cmbReceiver.setEnabled(enabled)
            self.cmbOtherSex.setEnabled(otherPersonEnabled and enabled and not self.cmbReceiver.value())
            self.edtOtherAge.setEnabled(otherPersonEnabled and enabled and not self.cmbReceiver.value())
            self.cmbAccountPregnancyTo12Weeks.setEnabled(pregnancyAndBirthEnabled and enabled)
            if self.btnTempInvalidProlong.isEnabled():
                fullLength, externalLength = self.modelPeriods.calcLengths()
                state = self.getTempInvalidState()
                self.btnTempInvalidProlong.setEnabled(enabled and state == CTempInvalidState.opened and fullLength and self.getIsNumberDisabilityFill())
            self.modelDocuments.setEnabledPatient(otherPersonEnabled, enabled, checked, self.isReasonPrimary)
            self.modelCare.setReadOnly(not bool(otherPersonEnabled and (enabled if checked else True)))
        else:
            self.cmbOtherSex.setEnabled(otherPersonEnabled and not self.cmbReceiver.value())
            self.edtOtherAge.setEnabled(otherPersonEnabled and not self.cmbReceiver.value())
            self.chkInsuranceOfficeMark.setEnabled(enabled)
            self.cmbAccountPregnancyTo12Weeks.setEnabled(pregnancyAndBirthEnabled)
            self.modelDocuments.setEnabledPatient(otherPersonEnabled, enabled, False, self.isReasonPrimary)
            self.modelCare.setReadOnly(not bool(otherPersonEnabled and (enabled if checked else True)))
        self.modelPeriods.setReason(self.cmbReason.value())


#    @pyqtSignature('QString')
    def on_cmbReceiver_textChanged(self, text):
        if self.cmbReceiver.isVisible():
            otherPersonEnabled = requiredOtherPerson(self.cmbReason.value()) if self.type_ != CTempInvalidEditDialog.Disability else True
            receiverId = self.cmbReceiver.value()
            sex, ageClient, clientAgeTuple = self.getClientSexAge(receiverId)
            otherAge = self.edtOtherAge.value()
            if otherPersonEnabled and ageClient >= 15 or not otherAge or otherAge < 15:
                self.cmbOtherSex.setCurrentIndex(sex)
                self.edtOtherAge.setValue(ageClient)
            if self.chkInsuranceOfficeMark.isChecked():
                enabled = QtGui.qApp.userHasRight(urRegWriteInsurOfficeMark)
                self.cmbOtherSex.setEnabled(otherPersonEnabled and enabled and not receiverId)
                self.edtOtherAge.setEnabled(otherPersonEnabled and enabled and not receiverId)
            else:
                self.cmbOtherSex.setEnabled(otherPersonEnabled and not receiverId)
                self.edtOtherAge.setEnabled(otherPersonEnabled and not receiverId)
            self.modelDocuments.setTempInvalidClientId(receiverId)
            self.cmbReceiver.setClientId(receiverId)
            self.modelCare.setTempInvalidClientId(receiverId)
            if receiverId:
                self.clientId = receiverId
            if otherPersonEnabled:
                self.isUpdatePlaceWork = True
                if not receiverId:
                    self.cmbReceiver.setClientId(None)
                self.updatePlaceWork(receiverId)
            elif self.isUpdatePlaceWork:
                self.isUpdatePlaceWork = False
                self.updatePlaceWork(self.clientId)


    def updatePlaceWork(self, receiverId):
        self.getPlaceWorkValues(receiverId)
        values = self.modelDocuments.cols()[CTempInvalidDocumentsModel.Col_PlaceWork].values
        if values and len(values) > 0:
            work = values[0]
        else:
            work = formatWorkTempInvalid(getClientWork(receiverId)) if receiverId else u''
        work = trim(work) if work else None
        for item in self.modelDocuments.items():
            item.setValue('placeWork', toVariant(work if work else None))
        self.modelDocuments.reset()


    def getClientSexAge(self, clientId):
        sex = 0
        ageClient = 0
        clientAgeTuple = (0, 0, 0, 0)
        if clientId:
            db = QtGui.qApp.db
            table = db.table('Client')
            begDate = self.modelPeriods.begDate()
            record = db.getRecordEx(table, [table['sex'], u'age(Client.birthDate, %s) AS ageClient, Client.birthDate' % (db.formatDate(begDate if begDate else QDate.currentDate()))], [table['id'].eq(clientId), table['deleted'].eq(0)])
            if record:
                sex = forceInt(record.value('sex'))
                ageClient = forceInt(record.value('ageClient'))
                birthDate = forceDate(record.value('ageClient'))
                clientAgeTuple = calcAgeTuple(birthDate, begDate if begDate else QDate.currentDate())
        return sex, ageClient, clientAgeTuple


    def setType(self, type_, docCode=None, isNotEvent=False):
        self.type_ = type_
        self.docCode = docCode
        self.docId = forceRef(QtGui.qApp.db.translate('rbTempInvalidDocument', 'code', self.docCode, 'id')) if self.docCode else None
        filter = 'type=%d'%self.type_
        filterDoc = (filter+' AND code=\'%s\''%self.docCode) if (self.docCode and not isNotEvent) else filter
        self.cmbDoctype.setTable('rbTempInvalidDocument', False, filterDoc)
        self.clientSex, self.clientAge, self.clientAgeTuple = self.getClientSexAge(self.clientId)
        self.cmbReason.setTable('rbTempInvalidReason', False, filter + (u''' AND code NOT IN ('05', '020')''' if self.clientSex == 1 else u''))
        self.cmbChangedReason.setTable('rbTempInvalidReason', True, filter + (u''' AND code NOT IN ('05', '020')''' if self.clientSex == 1 else u''))
        self.cmbExtraReason.setTable('rbTempInvalidExtraReason', True, filter)
        self.cmbResult.setTable('rbTempInvalidResult', True, filter)
        self.cmbTypeEducationalInstitution.setTable('rbTypeEducationalInstitution', True)
        self.modelPeriods.setType(self.type_)
        self.modelDocuments.setType(self.type_)
        for widget in (self.lblOtherSex, self.cmbOtherSex,
                       self.lblOtherAge, self.edtOtherAge,
                       self.lblAccountPregnancyTo12Weeks,
                       self.cmbAccountPregnancyTo12Weeks,):
            widget.setVisible(self.type_==0)
        if self.type_ == 0:
            self.cmbDoctype.setCode(QtGui.qApp.tempInvalidDoctype())
            self.cmbReason.setCode(QtGui.qApp.tempInvalidReason())
            # self.cmbChangedReason.setCode(QtGui.qApp.tempInvalidReason())
            if self.docCode:
                self.cmbDoctype.setEnabled(isNotEvent)
                self.cmbDoctype.setValue(self.docId)
        if self.type_ == CTempInvalidEditDialog.Disability:
            self.lblCaseBegDate.setText(u'Дата начала Инв.')
            self.lblPermit.setText(u'Установлена')
            self.lblResultDate.setText(u'Дата снятия')
            self.lblResultOtherwiseDate.setText(u'Дата ОС')
            self.edtNumberPermit.setVisible(False)
            self.lblAccountPregnancyTo12Weeks.setVisible(False)
            self.cmbAccountPregnancyTo12Weeks.setVisible(False)
            self.lblOGRN.setVisible(False)
            self.edtOGRN.setVisible(False)
            self.btnSelectHeadOrganisation.setVisible(False)
            self.lblOrganisation.setVisible(False)
            self.lblOrganisationOGRN.setVisible(False)
        self.getPlaceWorkValues(self.clientId)


    def setPrev(self, prevRecord):
        if prevRecord:
            self.prevId = forceRef(prevRecord.value('id'))
            self.prevState = forceInt(prevRecord.value('state'))
            self.edtCaseBegDate.setDate(forceDate(prevRecord.value('caseBegDate')))
        else:
            self.prevId = None
            self.prevState = None


    def begDateLastPeriod(self):
        return self.modelPeriods.begDateLast()


    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        record.setValue('type', toVariant(self.type_))
        getRBComboBoxValue(self.cmbDoctype, record, 'doctype_id')
        getRBComboBoxValue(self.cmbReason,  record, 'tempInvalidReason_id')
        getRBComboBoxValue(self.cmbChangedReason,  record, 'tempInvalidChangedReason_id')
        getRBComboBoxValue(self.cmbExtraReason,  record, 'tempInvalidExtraReason_id')
        getLineEditValue(self.edtNumberPermit, record, 'numberPermit')
        getDateEditValue(self.edtBegDatePermit, record, 'begDatePermit')
        getDateEditValue(self.edtEndDatePermit, record, 'endDatePermit')
        getRBComboBoxValue(self.cmbBreak,  record, 'break_id')
        getDateEditValue(self.edtBreakDate, record, 'breakDate')
        getDateEditValue(self.edtBegDateStationary, record, 'begDateStationary')
        getDateEditValue(self.edtEndDateStationary, record, 'endDateStationary')
        getRBComboBoxValue(self.cmbDisability,  record, 'disability_id')
        getRBComboBoxValue(self.cmbResult,  record, 'result_id')
        getDateEditValue(self.edtResultDate, record, 'resultDate')
        getDateEditValue(self.edtResultOtherwiseDate, record, 'resultOtherwiseDate')
        record.setValue('client_id', toVariant(self.cmbReceiver.value()))
        getDateEditValue(self.edtMseDate, record, 'mseDate')
        record.setValue('event_id', toVariant(self.cmbEvent.value()))
        getComboBoxValue(self.cmbOtherSex,  record, 'sex')
        getSpinBoxValue(self.edtOtherAge,   record, 'age')
        getCheckBoxValue(self.chkInsuranceOfficeMark,  record, 'insuranceOfficeMark')
        getLineEditValue(self.edtOGRN, record, 'OGRN')
        getRBComboBoxValue(self.cmbTypeEducationalInstitution, record, 'institution_id')
        getLineEditValue(self.edtInfContact, record, 'inf_contact')
        fullLength, externalLength = self.modelPeriods.calcLengths()
        record.setValue('begDate',  toVariant(self.modelPeriods.begDate()))
        record.setValue('endDate',  toVariant(self.modelPeriods.endDate()))
        record.setValue('duration', toVariant(fullLength))
        date = self.modelPeriods.endDate()
        if not date:
            date = self.modelPeriods.begDate()
        diagnosisTypeId = 1 #diagnosisType = закл
        diagnosis = getDiagnosisId2(date, self.modelPeriods.lastPerson(), self.clientId, diagnosisTypeId, unicode(self.edtDiagnosis.text()), u'', self.cmbDiseaseCharacter.value(), None, None)
        self.diagnosisId = diagnosis[0]
        record.setValue('diagnosis_id', toVariant(self.diagnosisId))
        state = self.getTempInvalidState()
        if (self.prolonging or self.state == CTempInvalidState.extended) and state != CTempInvalidState.annulled:
            state = CTempInvalidState.extended
        record.setValue('state',  state)
        if requiredDiagnosis(self.cmbReason.value()):
            if self.diagnosisId:
                record.setValue('diagnosis_id', toVariant(self.diagnosisId))
        else:
            record.setValue('diagnosis_id', QVariant())
        record.setValue('person_id', toVariant(self.modelPeriods.lastPerson()))
        record.setValue('prev_id', toVariant(self.prevId))
        if not self.edtCaseBegDate.date():
            self.edtCaseBegDate.setDate(self.modelPeriods.begDate())
        record.setValue('caseBegDate', toVariant(self.edtCaseBegDate.date()))
        record.setValue('accountPregnancyTo12Weeks', toVariant(self.cmbAccountPregnancyTo12Weeks.currentIndex()))
        self.saveProlonging = False
        return record


    def exec_(self):
        result = CItemEditorBaseDialog.exec_(self)
        if not result:
            if self.saveProlonging and self.prevId and self.prevState is not None:
                self.prolonging = False
                self.saveProlonging = False
                self.updateOtherwiseDate = False
                self.newProlonging = False
                try:
                    db = QtGui.qApp.db
                    db.transaction()
                    table = db.table('TempInvalid')
                    tableTD = db.table('TempInvalidDocument')
                    db.updateRecords(table, [table['state'].eq(self.state)], [table['deleted'].eq(0), table['id'].eq(self.prevId)])
                    records = db.getRecordList(tableTD, u'*', [tableTD['deleted'].eq(0), tableTD['master_id'].eq(self.prevId), tableTD['modifyDatetime'].dateEq(QDate.currentDate())])
                    for row, record in enumerate(records):
                        record.setValue('execPerson_id', toVariant(None))
                        db.updateRecord(tableTD, record)
                    db.commit()
                except:
                    db.rollback()
                    raise
        return result


    def checkDataEntered(self):
        if forceString(self.cmbResult.code()) == '99':
            return True
        result = True
        reasonId = self.cmbReason.value()
        result = result and (reasonId or self.checkInputMessage(u'причину', False, self.cmbReason))
        result = result and (self.cmbReceiver.value() or self.checkInputMessage(u'получателя', False, self.cmbReceiver))
        result = result and (self.cmbResult.value() or self.checkInputMessage(u'результат', False, self.cmbResult))
        if self.getTempInvalidState():  # ???????
            if self.mustHaveResultDate():
                result = result and (self.edtResultDate.date() or self.checkInputMessage(u'дату "Приступить к работе"', False, self.edtResultDate))
                endDateStationary = self.edtEndDateStationary.date()
                result = result and ((not endDateStationary or endDateStationary < self.edtResultDate.date()) or self.checkValueMessage(u'Дата "Приступить к работе" должна быть позднее даты окончания нахождения в стационаре.', False, self.edtResultDate))
            elif self.mustHaveOtherDate():
                result = result and (self.edtResultOtherwiseDate.date() or self.checkInputMessage(u'дату "Иное"', True, self.edtResultOtherwiseDate))
        if requiredOtherPerson(reasonId) and self.type_ != CTempInvalidEditDialog.Disability:
            clientSex, ageClient, clientAgeTuple = self.getClientSexAge(self.cmbReceiver.value())
            result = result and (ageClient >= 15 or self.checkValueMessage(u'Возраст Лица по уходу меньше 15 лет!', True, self.cmbReceiver))
            result = result and (self.cmbOtherSex.currentIndex() or self.checkInputMessage(u'пол', False, self.cmbOtherSex))
            result = result and (self.edtOtherAge.value() or self.checkInputMessage(u'возраст', False, self.edtOtherAge))
        items = self.modelPeriods.items()
        countPeriods = len(items)
        result = result and (countPeriods or self.checkInputMessage(u'период', False, self.tblPeriods, 0, 0))
        isExternalDocument = False
        isElectronicDocument = False
        hasInternalDocument = False
        for docItem in self.modelDocuments.items():
            if forceBool(docItem.value('isExternal')):
                isExternalDocument = True
            else:
                hasInternalDocument = True
            if forceBool(docItem.value('electronic')):
                isElectronicDocument = True
        breakId = self.cmbBreak.value()
        breakDate = self.edtBreakDate.date()
        if self.type_ == CTempInvalidEditDialog.TempInvalid and countPeriods == 1 and forceBool(items[0].value('isExternal')):
            endDatePeriod = self.modelPeriods.endDate()
            resultOtherwiseDate = self.edtResultOtherwiseDate.date()
            if self.getTempInvalidAbleStatus() and self.cmbResult.code() == u'36' and resultOtherwiseDate and breakDate and breakId and breakDate == endDatePeriod and resultOtherwiseDate > breakDate:
                pass
        elif self.type_ == CTempInvalidEditDialog.TempInvalid:
            if countPeriods == 1 and forceBool(items[0].value('isExternal')):
                if not (isExternalDocument and self.getTempInvalidState() and self.mustHaveResultDate() and self.edtResultDate.date() == self.modelPeriods.endDate().addDays(1)):
                    result = result and self.checkInputMessage(u'внутренний период', False, self.tblPeriods, 1, 0)
        else:
            if countPeriods == 1 and forceBool(items[0].value('isExternal')):
                result = result and self.checkInputMessage(u'внутренний период', False, self.tblPeriods, 1, 0)
        if not result:
            return False
        date = None
        for row, record in enumerate(items):
            date, recordOk = self.checkPeriodDataEntered(date, isElectronicDocument, row, record)
            if not recordOk:
                return False
        result = result and (self.modelPeriods.lastPerson() or not hasInternalDocument or self.checkInputMessage(u'Врача последнего периода', True, self.tblPeriods, len(items)-1 if items else None, items[-1].indexOf('endPerson_id') if items else None))
        # проверка отсутствия пересекающихся периодов нетрудоспособности
        begDate = self.modelPeriods.begDate()
        endDate = self.modelPeriods.endDate()
        begDateExternal, endDateExternal = self.modelPeriods.begDateEndDateFirstExternal()
        db = QtGui.qApp.db
        table = db.table('TempInvalid')
        tableTIResult = db.table('rbTempInvalidResult')
        cond = [table['begDate'].between(begDate, endDate),
                table['endDate'].between(begDate, endDate),
                db.joinAnd([table['begDate'].le(begDate), table['endDate'].ge(begDate)]),
                db.joinAnd([table['begDate'].le(endDate), table['endDate'].ge(endDate)]),  # а на бумажке рисую - вроде-бы и не нужно...
               ]
        cond = [db.joinOr(cond)]
        if begDateExternal and endDateExternal:
            cond.append(table['state'].ne(CTempInvalidState.transferred))
            cond.append(u'''(TempInvalid.state != %d
                                         OR NOT EXISTS(SELECT TI.id
                                                   FROM TempInvalid AS TI
                                                   WHERE TI.id = getLastTransferredStateTempInvalidId(TempInvalid.id)
                                                   AND TI.deleted = 0)
                                                   )''' % (CTempInvalidState.extended))
        cond.append(table['id'].ne(self.itemId()))
        cond.append(table['client_id'].eq(self.clientId))
        cond.append(table['deleted'].eq(0))
        cond.append(table['doctype_id'].eq(self.cmbDoctype.value()))
        cond.append(db.joinOr([tableTIResult['id'].isNull(), tableTIResult['state'].ne(CTempInvalidState.annulled)]))
        queryTable = table.leftJoin(tableTIResult, tableTIResult['id'].eq(table['result_id']))
        stmt = 'SELECT ' + db.existsStmt(queryTable, cond) + ' AS X'
        query = db.query(stmt)
        if query.first():
            present = forceBool(query.record().value(0))
            if present:
                result = self.checkValueMessage(u'Период нетрудоспособности пересекается с существующим.', False, self.tblPeriods, 0, 0)
                return False
        # result = result and self.checkTempInvalidPeriodsDateKAKEntered(reasonId)
        result = result and (len(self.modelDocuments.items()) or self.checkInputMessage(u'документ', False, self.tblDocuments, 0, 0))
        result = result and self.checkNumberOfDisabilityDocuments()
        result = result and self.checkValidContinuation()
        result = result and self.checkNumberTempInvalidDocument()
        result = result and self.checkSerialNumberTempInvalidDocument()
        result = result and self.checkReason()
        result = result and self.checkBreak()
        result = result and self.checkTempInvalidDocumentIssueDate()
        result = result and self.checkTempInvalidDisabilityDate()
        result = result and self.checkDataOther()
        result = result and self.checkTempInvalidDocumentClients()
        result = result and self.checkTempInvalidDocumentClientsItems()
        result = result and self.checkActualMKB()
        result = result and self.checkDocumentsSNILS()
        result = result and self.checkPersonDocuments()
        result = result and self.checkAbleStatusDocuments()
        result = result and self.checkReasonDiagnosis()
        return result


    def checkPersonDocuments(self):
        items = self.modelDocuments.items()
        for row, item in enumerate(items):
            if not forceRef(item.value('person_id')) and not forceBool(item.value('isExternal')):
                number = forceStringEx(item.value('number'))
                if not self.checkInputMessage(u'Врача выдавшего документ номер %s!'%(number), False, self.tblDocuments, row, item.indexOf('person_id')):
                    return False
        return True


    def checkAbleStatusDocuments(self):
        if self.cmbResult.code() not in (u'31',) or self.getTempInvalidAbleStatus():
            items = self.modelDocuments.items()
            for row, item in enumerate(items):
                if not forceRef(item.value('execPerson_id')):
                    number = forceStringEx(item.value('number'))
                    if not self.checkExecPersonValueMessage(u'Необходимо указать врача закрывшего документ номер %s! Заполнить его текущим пользователем?'%(number), self.tblDocuments, row, item.indexOf('execPerson_id')):
                        return False
        return True


    def checkReasonDiagnosis(self):
        reasonCode = self.cmbReason.code()
        diagnosisCode = self.edtDiagnosis.text()
        msg = u''

        if reasonCode == '01' and (str(diagnosisCode).startswith("S") or str(diagnosisCode).startswith("T")):
            msg = u"\nПричина не заболевание, а возможно травма"
        elif reasonCode == "02" and (str(diagnosisCode).startswith("S") == False and str(diagnosisCode).startswith("T") == False):
            msg = u"\nВозможно причина Заболевание?"

        if msg != '':
            messageBox = QtGui.QMessageBox()
            messageBox.setWindowFlags(messageBox.windowFlags() | Qt.WindowStaysOnTopHint)
            messageBox.setWindowTitle(u'Внимание!')
            messageBox.setText(msg)
            messageBox.addButton(QtGui.QPushButton(u'ОК'), QtGui.QMessageBox.ActionRole)
            messageBox.addButton(QtGui.QPushButton(u'Пропустить'), QtGui.QMessageBox.ActionRole)

            res = messageBox.exec_()
            if res == 0:
                return False
            elif res == 1:
                return True
        else:
            pass

        return True



    def checkExecPersonValueMessage(self, message, widget, row=None, column=None, detailWdiget=None, setFocus=True):
        buttons = QtGui.QMessageBox.Yes | QtGui.QMessageBox.No
        res = QtGui.QMessageBox.warning( self,
                                         u'Внимание!',
                                         message,
                                         buttons,
                                         QtGui.QMessageBox.Yes)
        if res == QtGui.QMessageBox.Yes:
            self.modelDocuments.items()[row].setValue('execPerson_id', toVariant(QtGui.qApp.userId))
            return True
        elif res == QtGui.QMessageBox.No:
            if setFocus:
                self.setFocusToWidget(widget, row, column)
                if isinstance(detailWdiget, QtGui.QWidget):
                    self.setFocusToWidget(detailWdiget, row, column)
            return False
        return True


    def checkReason(self):
        docTypeCode = forceInt(self.cmbDoctype.code())
        code = self.cmbReason.code()
        name = self.cmbReason.name()
        if docTypeCode <= forceInt(CTempInvalidEditDialog.InabilitySheet):
            if (code in [u'08', u'017', u'018', u'019'] or (code == u'05' and u'после' not in name)) and not self.edtBegDatePermit.date():
                self.checkInputMessage(u'дату начала путёвки', False, self.edtBegDatePermit)
                return False
        if (code in [u'08', u'017', u'018', u'019'] or (code == u'05' and u'после' not in name and u'родам (до)' not in name and u'родам(до)' not in name)) and not self.edtEndDatePermit.date():
            self.checkInputMessage(u'дату окончания путёвки', False, self.edtEndDatePermit)
            return False
        if (code in [u'08', u'017', u'018', u'019'] or (code == u'05' and u'после' not in name and u'родам (до)' not in name and u'родам(до)' not in name)) and not trim(self.edtNumberPermit.text()):
            self.checkInputMessage(u'номер путёвки', False, self.edtNumberPermit)
            return False
        begDatePermit = self.edtBegDatePermit.date()
        endDatePermit = self.edtEndDatePermit.date()
        if begDatePermit and endDatePermit and begDatePermit > endDatePermit:
            self.checkValueMessage(u'Дата начала путёвки не может быть позже даты окончания.', False, self.edtEndDatePermit)
            return False
        if not begDatePermit and endDatePermit:
            self.checkValueMessage(u'Дата окончания путёвки введена должна быть и дата начала путёвки.', False, self.edtBegDatePermit)
            return False
        if code in [u'08', u'017', u'018', u'019'] and not trim(self.edtOGRN.text()):
            self.checkInputMessage(u'ОГРН', False, self.edtOGRN)
            return False
        if self.cmbExtraReason.code() in [u'018'] and code not in [u'02', u'04']:
            self.checkValueMessage(u'Несовместимые значения причины и доп.причины нетрудоспособности.', False, self.cmbReason)
            return False
        if trim(self.edtNumberPermit.text()):
            if not self.edtBegDatePermit.date():
                self.checkInputMessage(u'дату начала путёвки', False, self.edtBegDatePermit)
                return False
            if not self.edtEndDatePermit.date():
                self.checkInputMessage(u'дату окончания путёвки', False, self.edtEndDatePermit)
                return False
        if trim(self.edtOGRN.text()):
            if not trim(self.edtNumberPermit.text()):
                self.checkInputMessage(u'номер путёвки', False, self.edtNumberPermit)
                return False
            if not self.edtBegDatePermit.date():
                self.checkInputMessage(u'дату начала путёвки', False, self.edtBegDatePermit)
                return False
            if not self.edtEndDatePermit.date():
                self.checkInputMessage(u'дату окончания путёвки', False, self.edtEndDatePermit)
                return False
        return True


    def checkBreak(self):
        breakId = self.cmbBreak.value()
        if breakId:
            if not self.edtBreakDate.date():
                self.checkInputMessage(u'дату нарушения режима', False, self.edtBreakDate)
                return False
            if not (self.edtBreakDate.date() >= self.modelPeriods.begDate() and self.edtBreakDate.date() <= self.modelPeriods.endDate()):
                self.checkValueMessage(u'Дата нарушения режима не попадает в период временной нетрудоспособности.', False, self.edtBreakDate)
                return False
        if self.edtBreakDate.date() and not self.cmbBreak.value():
            self.checkInputMessage(u'значение Нарушения режима', False, self.cmbBreak)
            return False
        return True


    def checkDataOther(self):
        begDateStationary = self.edtBegDateStationary.date()
        endDateStationary = self.edtEndDateStationary.date()
        if begDateStationary and endDateStationary and begDateStationary > endDateStationary:
            self.checkValueMessage(u'Дата начала нахождения в стационаре не может быть позже даты окончания.', False, self.edtEndDateStationary)
            return False
        if not begDateStationary and endDateStationary:
            self.checkValueMessage(u'Дата окончания нахождения в стационаре введена должна быть и дата начала нахождения в стационаре.', False, self.edtBegDateStationary)
            return False
        return True


    def checkTempInvalidDocumentIssueDate(self):
        if self.type_ != CTempInvalidEditDialog.Disability:
            begDatePermit = self.edtBegDatePermit.date()
            resultOtherwiseDate = self.edtResultOtherwiseDate.date()
            isDead = self.cmbResult.code() == '34'
            items = self.modelDocuments.items()
            for row, item in enumerate(items):
                issueDate = forceDate(item.value('issueDate'))
                duplicate = forceBool(item.value('duplicate'))
                if not duplicate and issueDate and begDatePermit and issueDate > begDatePermit and self.cmbReason.code() != '05':
                    self.checkValueMessage(u'Дата выдачи ЛН не должна быть позже Даты начала путёвки.', False, self.tblDocuments, row, item.indexOf('issueDate'))
                    return False
                if not duplicate and issueDate and resultOtherwiseDate and not isDead and issueDate > resultOtherwiseDate:
                    self.checkValueMessage(u'Дата выдачи ЛН не должна быть позже Даты Иное.', False, self.tblDocuments, row, item.indexOf('issueDate'))
                    return False
        return True


    def checkTempInvalidDisabilityDate(self):
        if self.type_ == CTempInvalidEditDialog.Disability:
            begDatePermit = self.edtBegDatePermit.date()
            endDatePermit = self.edtEndDatePermit.date()
            endDate = self.modelPeriods.endDate()
            if begDatePermit > endDatePermit:
                self.checkValueMessage(u'Дата Начала Установления инвалидности не должна быть позже Дата Окончания Установления инвалидности.', False, self.edtBegDatePermit)
                return False
            if endDate:
                if begDatePermit > endDate:
                    self.checkValueMessage(u'Дата Начала Установления инвалидности не должна быть позже последней дате последнего периода.', False, self.edtBegDatePermit)
                    return False
                if endDatePermit > endDate:
                    self.checkValueMessage(u'Дата Окончания Установления инвалидности не должна быть позже последней дате последнего периода.', False, self.edtEndDatePermit)
                    return False
        return True


    def getTempInvalidNextId(self, itemId):
        tempInvalidNextId = None
        if itemId:
            db = QtGui.qApp.db
            table = db.table('TempInvalid')
            lastRecord = db.getRecordEx(table, [table['id']], [table['prev_id'].eq(itemId), table['deleted'].eq(0), table['client_id'].eq(self.clientId), table['type'].eq(self.type_)], 'endDate ASC')
            tempInvalidNextId = forceRef(lastRecord.value('id')) if lastRecord else None
        return tempInvalidNextId

    
    def checkNumberOfDisabilityDocuments(self):
        if self.cmbDoctype.value() == CTempInvalidEditDialog.Disability:
            items = self.modelDocuments.items()
            internalCount = 0
            externalCount = 0
            for row, item in enumerate(items):
                isExternal = forceInt(item.value('isExternal'))
                if isExternal == 0:
                    internalCount += 1
                elif isExternal == 1:
                    externalCount += 1
                if internalCount > 1:
                    self.checkValueMessage(u'В эпизоде ВУТ может быть только 1 внутренний документ. Проверьте внесенные данные', False, self.tblDocuments, row, item.indexOf('isExternal')) 
                    return False
                if externalCount > 1:
                    self.checkValueMessage(u'В эпизоде ВУТ может быть только 1 внешний документ. Проверьте внесенные данные', False, self.tblDocuments, row, item.indexOf('isExternal'))
                    return False
        return True
    
    
    def checkValidContinuation(self):
        if self.cmbDoctype.value() == CTempInvalidEditDialog.Disability:
            items = self.modelDocuments.items()
            idxZero = None
            idxOne = None
            for row, item in enumerate(items):
                if forceInt(item.value('idx')) == 0 and not idxZero:
                    idxZero = item
                elif forceInt(item.value('idx')) == 1:
                    idxOne = item
                    checkRow = row
                if idxOne and idxZero:
                    if not forceInt(idxOne.value('prevNumber')) and forceInt(idxOne.value('prevNumber')) != forceInt(idxZero.value('number')):
                        self.checkValueMessage(u'В эпизоде ВУТ внутренний документ не является продолжением внешнего! Удалите внутренний документ и создайте его как продолжение внешнего', False, self.tblDocuments, checkRow, idxOne.indexOf('isExternal'))
                        return False    
        return True


    def checkNumberTempInvalidDocument(self):
        isNumberDisabilityFill = QtGui.qApp.controlNumberDisabilityFill()
        if isNumberDisabilityFill == 2:
            return True
        items = self.modelDocuments.items()
        for row, item in enumerate(items):
            electronic = forceBool(item.value('electronic'))
            number = forceStringEx(item.value('number'))
            skipable = bool(not electronic and not forceRef(item.value('last_id')) and not self.getTempInvalidNextId(self.itemId())) if isNumberDisabilityFill else False
            if not number:
                res = self.checkInputMessage(u'Номер в ЛВН', skipable, self.tblDocuments, row, item.indexOf('number'))
                if not res:
                    return False
            elif (     self.type_ != CTempInvalidEditDialog.Disability
                   and len(number) != 12
                   and self.cmbDoctype.code() != CTempInvalidEditDialog.MedicalCertificate
                 ):
                self.checkValueMessage(u'Номер ЛВН %s должен содержать 12 символов. Введите корректный номер.'%(number), False, self.tblDocuments, row, item.indexOf('number'))
                return False
            busyness = forceInt(item.value('busyness'))
            if not busyness and not electronic:
                self.checkInputMessage(u'Занятость в ЛВН', False, self.tblDocuments, row, item.indexOf('busyness'))
                return False
            placeWork = forceStringEx(item.value('placeWork'))
            if not placeWork and busyness != 3 and not electronic:
                self.checkInputMessage(u'Место работы в ЛВН', False, self.tblDocuments, row, item.indexOf('placeWork'))
                return False
        return True


    def checkTempInvalidDocumentClients(self):
        if self.type_ != CTempInvalidEditDialog.Disability:
            otherPersonEnabled = requiredOtherPerson(self.cmbReason.value())
            if not otherPersonEnabled:
                return True
            if self.cmbReason.code() == u'08':
                return True
            isClientFill = False
            clientPrimumItems = self.modelCare.items()
            clientSecondItems = self.modelCare.items()
            for rowPrimum, clientPrimumItem in enumerate(clientPrimumItems):
                clientPrimumId = forceRef(clientPrimumItem.value('client_id'))
                if clientPrimumId:
                    isClientFill = True
                for rowSecond, clientSecondItem in enumerate(clientSecondItems):
                    if rowPrimum != rowSecond:
                        clientSecondId = forceRef(clientSecondItem.value('client_id'))
                        if (clientPrimumId or clientSecondId) and clientPrimumId == clientSecondId:
                            self.checkValueMessage(u'Пациент в таблице "Лица по уходу" введён дважды.', False, self.tblCare, rowSecond, clientSecondItem.indexOf('client_id'))
                            return False
            if self.cmbReason.code() != u'03' and not isClientFill:
                self.checkValueMessage(u'Так как причина ВУТ связана с уходом - заполните, пожалуйста, таблицу "Лица по уходу".', False, self.tblCare, 0, 0)
                return False
        return True


    def checkTempInvalidDocumentClientsItems(self):
        clientItems = self.modelCare.items()
        for row, clientItem in enumerate(clientItems):
            clientId = forceRef(clientItem.value('client_id'))
            if clientId:
                column = None
                message = u""
                if not forceRef(clientItem.value('tempInvalidRegime_id')):
                    column = clientItem.indexOf('tempInvalidRegime_id')
                    message = u"введён режим"
                elif not forceString(clientItem.value('MKB')):
                    column = clientItem.indexOf('MKB')
                    message = u"введён диагноз"
                elif not forceRef(clientItem.value('tempInvalidReason_id')):
                    column = clientItem.indexOf('tempInvalidReason_id')
                    message = u"введена причина"
                if column and message:
                    self.checkValueMessage(u'У пациента в таблице "Лица по уходу" не {}'.format(message),
                                            False, 
                                            self.tblCare, 
                                            row, 
                                            column)
                    return False
        return True


    def checkSerialNumberTempInvalidDocument(self):
        isNumberDisabilityFill = QtGui.qApp.controlNumberDisabilityFill()
        tempInvalidNextId = self.getTempInvalidNextId(self.itemId()) if isNumberDisabilityFill else None
        items = self.modelDocuments.items()
        for row, item in enumerate(items):
            serial = forceString(item.value('serial'))
            number = forceString(item.value('number'))
            if isNumberDisabilityFill != 2 or (isNumberDisabilityFill == 2 and number):
                duplicate = forceBool(item.value('duplicate'))
                if not duplicate:
                    for row2, item2 in enumerate(items):
                        if row != row2:
                            serial2 = forceString(item2.value('serial'))
                            number2 = forceString(item2.value('number'))
                            duplicate2 = forceBool(item2.value('duplicate'))
                            skipable = bool(not forceBool(item.value('electronic')) and not forceRef(item.value('last_id')) and not forceBool(item2.value('electronic')) and not forceRef(item2.value('last_id')) and not tempInvalidNextId) if isNumberDisabilityFill else False
                            if serial == serial2 and number == number2 and not duplicate2:
                                if not self.checkValueMessage(u'ЛВН с указанными серией %s и номером %s уже существуют. Укажите корректные данные.'%(serial2, number2), skipable, self.tblDocuments, row2, item2.indexOf('serial')):
                                    return False
        db = QtGui.qApp.db
        table = db.table('TempInvalidDocument')
        tableTempInvalid = db.table('TempInvalid')
        table = table.leftJoin(tableTempInvalid, tableTempInvalid['id'].eq(table['master_id']))
        for row, item in enumerate(items):
            documentId = forceRef(item.value('id'))
            serial = forceString(item.value('serial'))
            number = forceString(item.value('number'))
            if isNumberDisabilityFill != 2 or (isNumberDisabilityFill == 2 and number):
                duplicate = forceBool(item.value('duplicate'))
                if not duplicate:
                    cond = [table['deleted'].eq(0),
                            table['serial'].like(serial),
                            table['number'].like(number),
                            table['duplicate'].eq(0),
                            tableTempInvalid['state'].ne(4)
                            ]
                    if documentId:
                        cond.append(table['id'].ne(documentId))
                    record = db.getRecordEx(table, [table['id']], cond)
                    if record:
                        skipable = bool(not forceBool(record.value('electronic')) and not forceRef(record.value('last_id')) and not tempInvalidNextId) if isNumberDisabilityFill else False
                        if not self.checkValueMessage(u'ЛВН с указанными серией %s и номером %s уже существуют. Укажите корректные данные.'%(serial, number), skipable, self.tblDocuments, row, item.indexOf('serial')):
                            return False
        return True


    def checkValueMessageUpdateSNILS(self, clientId, widget, row, column):
        result = False
        isSNILSTempInvalid = QtGui.qApp.controlSNILSTempInvalid()
        messageBox = QtGui.QMessageBox()
        messageBox.setWindowFlags(messageBox.windowFlags() | Qt.WindowStaysOnTopHint)
        messageBox.setWindowTitle(u'Внимание!')
        messageBox.setText(u'Для оформления электронного больничного листа необходим СНИЛС получателя.')
        messageBox.addButton(QtGui.QPushButton(u'ОК'), QtGui.QMessageBox.ActionRole)
        messageBox.addButton(QtGui.QPushButton(u'Добавить СНИЛС'), QtGui.QMessageBox.ActionRole)
        if isSNILSTempInvalid == 0:
            messageBox.addButton(QtGui.QPushButton(u'Пропустить'), QtGui.QMessageBox.ActionRole)
        res = messageBox.exec_()
        if res == 0:
            self.setFocusToWidget(widget, row, column)
            result = False
        elif res == 1:
            QtGui.qApp.callWithWaitCursor(self, self.editClient, clientId)
            self.setFocusToWidget(widget, row, column)
            result = False
        elif isSNILSTempInvalid == 0 and res == 2:
            result = True
        return result


    def getClientSNILS(self):
        db = QtGui.qApp.db
        clientId = self.cmbReceiver.value()
        SNILS = forceString(db.translate('Client', 'id', clientId, 'SNILS'))
        return SNILS


    def editClient(self, clientId):
        if QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]):
            dialog = CClientEditDialog(self)
            try:
                dialog.load(clientId)
                QtGui.qApp.restoreOverrideCursor()
                dialog.setFocusToWidget(dialog.edtSNILS)
                if dialog.exec_():
                    pass
            finally:
                dialog.deleteLater()


    def checkDocumentsSNILS(self):
        items = self.modelDocuments.items()
        for row, item in enumerate(items):
            if forceBool(item.value('electronic')):
                SNILS = self.getClientSNILS()
                if SNILS:
                    return True
                else:
                    return self.checkValueMessageUpdateSNILS(self.cmbReceiver.value(),
                                                             self.tblDocuments,
                                                             row,
                                                             item.indexOf('electronic')
                                                            )
        return True


    def checkActualMKB(self):
        result = True
        reasonTypeId = self.cmbReason.value()
        if reasonTypeId:
            db = QtGui.qApp.db
            table = db.table('rbTempInvalidReason')
            if forceBool(db.translate(table, 'id', reasonTypeId, 'requiredDiagnosis')):
                MKB = unicode(self.edtDiagnosis.text())
                items = self.modelPeriods.items()
                result = result and (MKB or self.checkInputMessage(u'диагноз', False, self.edtDiagnosis))
                if len(items) > 0 and MKB:
                    begDate = forceDate(items[0].value('begDate'))
                    db = QtGui.qApp.db
                    tableMKB = db.table('MKB')
                    cond = [tableMKB['DiagID'].eq(MKBwithoutSubclassification(MKB))]
                    cond.append(db.joinOr([tableMKB['endDate'].isNull(), tableMKB['endDate'].dateGe(begDate)] ))
                    recordMKB = db.getRecordEx(tableMKB, [tableMKB['DiagID']], cond)
                    result = result and (forceString(recordMKB.value('DiagID')) == MKBwithoutSubclassification(MKB) if recordMKB else False) or self.checkValueMessage(u'Диагноз %s не доступен для применения'%MKB, False, self.edtDiagnosis)
        return result


    def checkTempInvalidPeriodsDateKAKEntered(self, tempInvalidReasonId):
        db = QtGui.qApp.db
        table = db.table('rbTempInvalidReason')
        tableTempInvalid = db.table('TempInvalid')
        tableTempInvalidPeriod = db.table('TempInvalid_Period')
        recordReason = db.getRecordEx(table, [table['restriction']], [table['id'].eq(tempInvalidReasonId)])
        restriction = forceInt(recordReason.value('restriction')) if recordReason else 0
        if restriction:
            itemsPrev = []
            if self.prevId:
                prevId = self.prevId
                tempInvalidIdList = []
                while prevId:
                    cond = [tableTempInvalid['prev_id'].isNotNull(),
                            tableTempInvalid['id'].eq(prevId),
                            tableTempInvalid['deleted'].eq(0),
                            tableTempInvalid['doctype_id'].eq(self.cmbDoctype.value())
                            ]
                    if self.clientId:
                        cond.append(tableTempInvalid['client_id'].eq(self.clientId))
                    cond.append('TempInvalid.state IN(%d,%d)' % (CTempInvalidState.extended, CTempInvalidState.opened))
                    stmt = db.selectDistinctStmt(tableTempInvalid, [tableTempInvalid['prev_id']], cond, '', None)
                    query = db.query(stmt)
                    prevId = None
                    while query.next():
                        prevId = query.value(0).toInt()[0]
                        if prevId and prevId not in tempInvalidIdList:
                            tempInvalidIdList.append(prevId)
                if self.prevId not in tempInvalidIdList:
                    tempInvalidIdList.append(self.prevId)
                if tempInvalidIdList:
                    prevRecords = db.getRecordListGroupBy(tableTempInvalidPeriod, u'TempInvalid_Period.*', [tableTempInvalidPeriod['master_id'].inlist(tempInvalidIdList)], u'TempInvalid_Period.id', u'TempInvalid_Period.begDate')
                    for recordPrev in prevRecords:
                        itemsPrev.append(recordPrev)
            items = self.modelPeriods.items()
            if itemsPrev:
                for item in items:
                    itemsPrev.append(item)
            else:
                itemsPrev = items
            durationSum = 0
            begDate = None
            for row, record in enumerate(itemsPrev):
                begDateDur = forceDate(record.value('begDate'))
                endDateDur = forceDate(record.value('endDate'))
                duration = begDateDur.daysTo(endDateDur)+1 if begDateDur and endDateDur and begDateDur <= endDateDur else 0
                directDateOnKAK = forceDate(record.value('directDateOnKAK'))
                isExternal = forceBool(record.value('isExternal'))
                directDateOnKAKIndex = record.indexOf('directDateOnKAK')
                resultId = forceRef(record.value('result_id'))
                able = forceBool(db.translate('rbTempInvalidResult', 'id', resultId, 'able'))
                if able or directDateOnKAK or isExternal:
                    durationSum = 0
                    begDate = None
                else:
                    durationSum += duration
                    if not begDate:
                        begDate = forceDate(record.value('begDate'))
            if durationSum and restriction < durationSum:
                if begDate:
                    newDirectDateOnKAK = begDate.addDays(restriction - 1)
                result = CEventEditDialog(self).checkValueMessage(u'Необходимо направить на КЭК%s'%((u', предположительная дата напрвления на КЭК %s'%(newDirectDateOnKAK.toString('dd.MM.yyyy'))) if newDirectDateOnKAK else u''), False, self.tblPeriods, len(items)-1, directDateOnKAKIndex)
                if newDirectDateOnKAK:
                    record.setValue('directDateOnKAK', toVariant(newDirectDateOnKAK))
                return result
        return True


    def checkPeriodDataEntered(self, prevPerionEndDate, isElectronicDocument, row, record):
        begDateIndex = record.indexOf('begDate')
        endDateIndex = record.indexOf('endDate')
        begDate = forceDate(record.value(begDateIndex))
        endDate = forceDate(record.value(endDateIndex))
        result = True
        if result and not begDate:
            result = self.checkValueMessage(u'Не заполнена дата начала периода', False, self.tblPeriods, row, begDateIndex)
        if result and (prevPerionEndDate and prevPerionEndDate.daysTo(begDate) != 1):
            result = self.checkValueMessage(u'Недопустимая дата начала периода', False, self.tblPeriods, row, begDateIndex)
        if result and not endDate and not ((self.cmbResult.code() == u'issued' or self.getTempInvalidState() == CTempInvalidState.opened) and not isElectronicDocument):
            result = self.checkValueMessage(u'Не заполнена дата окончания периода', False, self.tblPeriods, row, endDateIndex)
            if result and endDate and (begDate.daysTo(endDate) < 0):
                result = self.checkValueMessage(u'Недопустимая дата окончания периода', False, self.tblPeriods, row, endDateIndex)
        return endDate, result


    def getTempInvalidState(self):
        resultId = self.cmbResult.value()
        if resultId:
            return forceInt(QtGui.qApp.db.translate('rbTempInvalidResult', 'id', resultId, 'state'))
        return CTempInvalidState.opened


    def getTempInvalidAbleStatus(self):
        resultId = self.cmbResult.value()
        if resultId:
            return forceInt(QtGui.qApp.db.translate('rbTempInvalidResult', 'id', resultId, 'able'))
        return 0


    # is date must be used?
    def mustHaveResultDate(self):
        code = self.cmbResult.code()
        #        return code == '30'
        return not ('31' <= code <= '37') and self.getTempInvalidAbleStatus()


    def mustHaveOtherDate(self):
        code = self.cmbResult.code()
        return code in ('32', '33', '34', '36')


    def mustHaveContinuation(self):
        code = self.cmbResult.code()
        return code in ('31', '37')


    def updateLength(self):
        fullLength, externalLength = self.modelPeriods.calcLengths()
        self.lblLengthValue.setText(str(fullLength))
        self.lblExternalLengthValue.setText(str(externalLength))
        caseBegDate = self.edtCaseBegDate.date()
        if caseBegDate:
            caseLength = caseBegDate.daysTo(self.modelPeriods.begDate())+fullLength
        else:
            caseLength = fullLength
        self.lblCaseLengthValue.setText(str(caseLength))
        state = self.getTempInvalidState()
        self.btnTempInvalidProlong.setEnabled(state == CTempInvalidState.opened and self.state != CTempInvalidState.extended and caseLength and self.getIsNumberDisabilityFill())


    def newTempInvalid(self, begDate):
        self.tempInvalidId = None
        self.insuranceOfficeMark = None
        self.state = CTempInvalidState.opened
        fullLength, externalLength = self.modelPeriods.calcLengths()
        self.btnTempInvalidProlong.setEnabled((not self.prolonging) and fullLength and self.getIsNumberDisabilityFill())
        self.prolonging = False
        self.modelPeriods.clearItems()
        self.modelPeriods.addStart(begDate)
        self.chkInsuranceOfficeMark.setChecked(False)
        self.updateLength()
        self.setItemId(None)
        self.edtResultOtherwiseDate.setDate(QDate())
        self.modelCare.clearItems()
        self.modelMedicalCommission.clearItems()
        self.modelMedicalCommissionMSI.clearItems()


    def getMKBs(self):
        if self.diagnosisId:
            db = QtGui.qApp.db
            record = db.getRecord('Diagnosis', '*', self.diagnosisId)
            if record:
               return forceString(record.value('MKB')), forceString(record.value('MKBEx')), forceRef(record.value('character_id'))
        return '', '', None


    def getDiagFilter(self):
        db =QtGui.qApp.db
        specialityId = forceRef(db.translate('Person', 'id', self.modelPeriods.lastPerson(), 'speciality_id'))
        result = self.mapSpecialityIdToDiagFilter.get(specialityId, None)
        if result is None:
            result = db.translate('rbSpeciality', 'id', specialityId, 'mkbFilter')
            if result is None:
                result = ''
            else:
                result = forceString(result)
            self.mapSpecialityIdToDiagFilter[specialityId] = forceString(result)
        return result


    def specifyDiagnosis(self, MKB):
        diagFilter = self.getDiagFilter()
        date = self.modelPeriods.begDate()
        if not date:
            date = QDate.currentDate()
        acceptable, specifiedMKB, specifiedMKBEx, specifiedCharacterId, specifiedTraumaTypeId, modifiableDiagnosisId, specifiedDispanserId, specifiedRequiresFillingDispanser, specifiedProlongMKB = specifyDiagnosis(self, MKB, diagFilter, self.clientId, self.clientSex, self.clientAgeTuple, date)
        self.modifiableDiagnosisesMap[specifiedMKB] = modifiableDiagnosisId
        return acceptable, specifiedMKB, specifiedMKBEx, specifiedCharacterId, specifiedTraumaTypeId, specifiedDispanserId, specifiedRequiresFillingDispanser, specifiedProlongMKB


    def setEditorDataTI(self):
        db = QtGui.qApp.db
        MKB  = unicode(self.edtDiagnosis.text())
        codeIdList = getAvailableCharacterIdByMKB(MKB)
        table = db.table('rbDiseaseCharacter')
        self.cmbDiseaseCharacter.setTable(table.name(), not bool(codeIdList), filter=table['id'].inlist(codeIdList))


    def updateCharacterByMKB(self, MKB, specifiedCharacterId):
        characterIdList = getAvailableCharacterIdByMKB(MKB)
        if specifiedCharacterId in characterIdList:
            characterId = specifiedCharacterId
        else:
            characterId = forceRef(self.cmbDiseaseCharacter.value())
            if (characterId in characterIdList) or (characterId is None and not characterIdList):
                return
            if characterIdList:
                characterId = characterIdList[0]
            else:
                characterId = None
        self.cmbDiseaseCharacter.setValue(characterId)


    def getTempInvalidInfo(self, context):
        result = context.getInstance(CTempInvalidInfo, None)
        result._doctype = context.getInstance(CTempInvalidDocTypeInfo,  self.cmbDoctype.value())
        result._reason  = context.getInstance(CTempInvalidReasonInfo,  self.cmbReason.value())
        result._changedReason  = context.getInstance(CTempInvalidReasonInfo,  self.cmbChangedReason.value())
        result._extraReason  = context.getInstance(CTempInvalidExtraReasonInfo, forceRef(self.cmbExtraReason.value()))
        result._sex     = formatSex(self.cmbOtherSex.currentIndex())
        result._age     = self.edtOtherAge.value()
        result._client= context.getInstance(CClientInfo, self.cmbReceiver.value())
        result._duration, result._externalDuration = self.modelPeriods.calcLengths()
        result._begDate = CDateInfo(self.modelPeriods.begDate())
        result._endDate = CDateInfo(self.modelPeriods.endDate())
        result._accountPregnancyTo12Weeks = forceInt(self.cmbAccountPregnancyTo12Weeks.currentIndex())
        MKB, MKBEx, characterId = self.getMKBs()
        result._MKB = context.getInstance(CMKBInfo, MKB)
        result._MKBEx = context.getInstance(CMKBInfo, MKBEx)
        state = self.getTempInvalidState()
        result._state = state
        result._periods = self.modelPeriods.getPeriodsInfo(context)
        result._result = context.getInstance(CTempInvalidResultInfo, forceRef(self.cmbResult.value()))

        result._caseBegDate = CDateInfo(self.edtCaseBegDate.date())
        result._begDateStationary = CDateInfo(forceDate(self.edtBegDateStationary.date()))
        result._endDateStationary = CDateInfo(forceDate(self.edtEndDateStationary.date()))
        result._break = context.getInstance(CTempInvalidBreakInfo, self.cmbBreak.value())
        result._breakDate = CDateInfo(forceDate(self.edtBreakDate.date()))
        result._resultDate = CDateInfo(forceDate(self.edtResultDate.date()))
        result._resultOtherwiseDate = CDateInfo(forceDate(self.edtResultOtherwiseDate.date()))
        result._OGRN = self.edtOGRN.text()
        result._numberPermit = self.edtNumberPermit.text()
        result._begDatePermit = CDateInfo(self.edtBegDatePermit.date())
        result._endDatePermit = CDateInfo(self.edtEndDatePermit.date())
        result._receiver = context.getInstance(CClientInfo, self.cmbReceiver.value())
        result._eventId = self.cmbEvent.value()
        result._institution = context.getInstance(CTypeEducationalInstitutionInfo, self.cmbTypeEducationalInstitution.value())
        result._inf_contact = self.edtInfContact.text()
        present = False
        for document in self.modelDocuments.items():
            if document.signatures.present(document.signatures.resultSubject()):
                present = True
                break
        result._isSigned = (result._state == 1 and present)

        result._items = self.modelDocuments.getDocumentsInfo(context)
        if self.prevId:
            result._prev = context.getInstance(CTempInvalidInfo, self.prevId)
        else:
            result._prev = None

        for item in result._items:
            item._cares = self.modelCare.getCaresInfo(context, item.id)

        result._ok = True
        return result


    @pyqtSignature('')
    def on_btnClientRelations_clicked(self):
        dialog = CClientRelationsEditDialog(self)
        clientInfo = getClientMiniInfo(self.clientId)
        dialog.setWindowTitle(u'Связи: ' + clientInfo)
        dialog.load(self.clientId)
        try:
            if dialog.exec_():
                pass
        finally:
            dialog.deleteLater()


    @pyqtSignature('')
    def on_btnSelectHeadOrganisation_clicked(self):
        OGRN = u''
        shortName = u''
        orgId = selectOrganisation(self, None, False)
        if orgId:
            db = QtGui.qApp.db
            table = db.table('Organisation')
            record = db.getRecordEx(table, [table['OGRN'], table['shortName']], [table['id'].eq(orgId), table['deleted'].eq(0)], 'shortName, INN, OGRN')
            if record:
                OGRN = forceString(record.value('OGRN'))
                shortName = forceString(record.value('shortName'))
        self.edtOGRN.setText(OGRN)
        charCount = 32
        if len(shortName) > charCount:
            shortNameLeft = QString(shortName).left(charCount) + u'...'
        else:
            shortNameLeft = shortName
        self.lblOrganisationOGRN.setText(shortNameLeft)
        self.lblOrganisationOGRN.setToolTip(shortName)


    @pyqtSignature('QString')
    def on_edtOGRN_textEdited(self, OGRN):
        shortName = u''
        if OGRN:
            db = QtGui.qApp.db
            table = db.table('Organisation')
            record = db.getRecordEx(table, [table['shortName']], [table['OGRN'].eq(OGRN), table['deleted'].eq(0)], 'shortName, INN, OGRN')
            if record:
                shortName = forceString(record.value('shortName'))
        charCount = 32
        if len(shortName) > charCount:
            shortNameLeft = QString(shortName).left(charCount) + u'...'
        else:
            shortNameLeft = shortName
        self.lblOrganisationOGRN.setText(shortNameLeft)
        self.lblOrganisationOGRN.setToolTip(shortName)


    @pyqtSignature('int')
    def on_cmbResult_currentIndexChanged(self, index):
        resultId = self.cmbResult.value()
        if resultId:
            if self.mustHaveResultDate():
                self.edtResultDate.setEnabled(True)
                endDate = self.modelPeriods.endDate()
                self.edtResultDate.setDate(endDate.addDays(1) if endDate else QDate())
                self.edtResultOtherwiseDate.setEnabled(False)
                self.edtResultOtherwiseDate.setDate(QDate())
            else:
                self.edtResultDate.setEnabled(False)
                self.edtResultDate.setDate(QDate())
                self.edtResultOtherwiseDate.setEnabled(self.mustHaveOtherDate())
            self.ableStatusDocuments()
        else:
            self.edtResultDate.setEnabled(False)
            self.edtResultDate.setDate(QDate())
            self.edtResultOtherwiseDate.setEnabled(False)
            self.edtResultOtherwiseDate.setDate(QDate())
        state = self.getTempInvalidState()
        fullLength, externalLength = self.modelPeriods.calcLengths()
        self.btnTempInvalidProlong.setEnabled(state == CTempInvalidState.opened and self.state != CTempInvalidState.extended and fullLength and self.getIsNumberDisabilityFill())
        self.btnDuplicate.setEnabled(bool(state == CTempInvalidState.annulled and self.itemId()))


    def ableStatusDocuments(self):
        if self.getTempInvalidAbleStatus():
            items = self.modelDocuments.items()
            for row, item in enumerate(items):
                if not forceRef(item.value('execPerson_id')):
                    self.modelDocuments.items()[row].setValue('execPerson_id', toVariant(QtGui.qApp.userId))
            self.modelDocuments.reset()


    @pyqtSignature('int')
    def on_cmbDoctype_currentIndexChanged(self, index):
        self.modelDocuments.setDocCode(self.cmbDoctype.code())
        isForm095 = self.cmbDoctype.code() == '2'
        self.lblTypeEducationalInstitution.setVisible(isForm095)
        self.cmbTypeEducationalInstitution.setVisible(isForm095)
        self.lblInfContact.setVisible(isForm095)
        self.edtInfContact.setVisible(isForm095)
        self.lblPermit.setVisible(not isForm095)
        self.edtBegDatePermit.setVisible(not isForm095)
        self.edtEndDatePermit.setVisible(not isForm095)
        self.edtNumberPermit.setVisible(not isForm095)
        self.lblOGRN.setVisible(not isForm095)
        self.edtOGRN.setVisible(not isForm095)
        self.btnSelectHeadOrganisation.setVisible(not isForm095)
        self.lblOrganisation.setVisible(not isForm095)
        self.lblOrganisationOGRN.setVisible(not isForm095)
        self.lblDisability.setVisible(not isForm095)
        self.cmbDisability.setVisible(not isForm095)


    @pyqtSignature('int')
    def on_cmbReason_currentIndexChanged(self, index):
        if not self.isReasonPrimary:
            self.setEnabledWidget(self.chkInsuranceOfficeMark.isChecked(), [self.cmbDoctype, self.cmbReason, self.cmbExtraReason, self.edtDiagnosis, self.cmbDiseaseCharacter, self.chkInsuranceOfficeMark, self.tblPeriods])
        if self.type_ != CTempInvalidEditDialog.Disability:
            self.btnClientRelations.setEnabled(requiredOtherPerson(self.cmbReason.value()))


    def getDuplicateAndParent(self):
        pass


    def newTempInvalidDocuments(self, items):
        newItems = []
        db = QtGui.qApp.db
        for item in items:
            prevNumber = item.value('number')
            prevExecPersonId = forceRef(item.value('execPerson_id'))
            newItem = self.modelDocuments.getEmptyRecord()
            copyFields(newItem, item)
            newItem.setValue('id',                 toVariant(None))
            newItem.setValue('master_id',          toVariant(None))
            newItem.setValue('issueDate',          QDate.currentDate())
            newItem.setValue('serial',             '')
            newItem.setValue('number',             '')
            if forceBool(item.value('electronic')):
                ok, number = QtGui.qApp.call(None, acquireElectronicTempInvalidNumber)
                if ok:
                    newItem.setValue('number',     number)
                else:
                    newItem.setValue('electronic', False)
            newItem.setValue('duplicate',          0)
            newItem.setValue('duplicateReason_id', None)
            newItem.setValue('prevDuplicate_id',   None)
            newItem.setValue('prevNumber',         prevNumber)
            newItem.setValue('prev_id',            item.value('id'))
            newItem.setValue('last_id',            None)
            newItem.setValue('person_id',          prevExecPersonId if prevExecPersonId else QtGui.qApp.userId)
            newItem.setValue('execPerson_id',      None)
            newItem.setValue('note',               '')
            newItem.setValue('fssStatus',          '')
            newCareRecords = []
            careItems = item.tempInvalidCare.getItems()
            for careItem in careItems:
                newCareRecord = db.table('TempInvalidDocument_Care').newRecord()
                copyFields(newCareRecord, careItem)
                newCareRecord.setValue('id', toVariant(None))
                newCareRecord.setValue('begDate', toVariant(forceDate(self.modelPeriods.endDate().addDays(1))))
                newCareRecord.setValue('endDate', toVariant(None))
                newCareRecords.append(newCareRecord)
            newItem.tempInvalidCare.setItems(newCareRecords)
            newItems.append(newItem)
        return newItems


    def save(self):
        tempInvalidId = CItemEditorBaseDialog.save(self)
        if tempInvalidId:
            self.modelPeriods.saveItems(tempInvalidId)
            self.modelDocuments.saveItems(tempInvalidId, self.newProlonging)
            if self.updateOtherwiseDate and self.prevId:
                items = self.modelDocuments.items()
                if items:
                        db = QtGui.qApp.db
                        db.transaction()
                        try:
                            table = db.table('TempInvalid')
                            if len(items) > 1:
                                items.sort(key=lambda item: forceDate(item.value('issueDate')))
                            issueDate = forceDate(items[0].value('issueDate'))
                            record = db.getRecordEx(table, [table['resultOtherwiseDate'], table['result_id']], [table['id'].eq(self.prevId), table['deleted'].eq(0)])
                            tableTIR = db.table('rbTempInvalidResult')
                            resultIdExtend = db.getDistinctIdList(tableTIR, [tableTIR['id']], [tableTIR['state'].eq(CTempInvalidState.extended)], [tableTIR['id'].name()])
                            resultOtherwiseDate = forceDate(record.value('resultOtherwiseDate')) if record else None
                            resultId = forceRef(record.value('result_id')) if record else None
                            cols = []
                            if not resultId or (resultIdExtend and resultId not in resultIdExtend):
                                cols.append(table['result_id'].eq(resultIdExtend[0]))
                                resultId = resultIdExtend[0]
                            resultCode = ''
                            if resultId:
                                resultCode = forceString(db.translate(tableTIR, 'id', resultId, 'code'))
                            if (not resultOtherwiseDate or issueDate != resultOtherwiseDate) and resultId and resultCode in ['32', '33', '34', '36']:
                                cols.append(table['resultOtherwiseDate'].eq(issueDate))
                            if cols:
                                db.updateRecords(table, cols, [table['deleted'].eq(0), table['id'].eq(self.prevId)])
                            db.commit()
                        except:
                            db.rollback()
                            raise
            if self.modelDocuments.items():
                db = QtGui.qApp.db
                db.transaction()
                try:
                    table = db.table('TempInvalid')
                    resultIdAnnulment = self.getAnnulmentDocumentsResult()
                    if resultIdAnnulment:
                        tableTIR = db.table('rbTempInvalidResult')
                        resultIdListAnnulment = db.getDistinctIdList(tableTIR, [tableTIR['id']], [tableTIR['type'].eq(self.type_), tableTIR['state'].eq(CTempInvalidState.annulled)])
                        record = db.getRecordEx(table, [table['result_id']], [table['id'].eq(tempInvalidId), table['deleted'].eq(0)])
                        resultId = forceRef(record.value('result_id')) if record else None
                        if resultId != resultIdAnnulment and resultId not in resultIdListAnnulment:
                            cols = [table['result_id'].eq(resultIdAnnulment),
                                    table['state'].eq(CTempInvalidState.annulled)]
                            db.updateRecords(table, cols, [table['deleted'].eq(0), table['id'].eq(tempInvalidId)])
                    db.commit()
                except:
                    db.rollback()
                    raise
        self.updateOtherwiseDate = False
        return tempInvalidId


    def getAnnulmentDocumentsResult(self):
        resultId = None
        annulmentReasonId = None
        items = self.modelDocuments.items()
        for item in items:
            annulmentReasonId = forceRef(item.value('annulmentReason_id'))
            if annulmentReasonId is None:
                break
        if annulmentReasonId is not None:
            db = QtGui.qApp.db
            table = db.table('rbTempInvalidResult')
            record = db.getRecordEx(table, [table['id']], [table['type'].eq(self.type_), table['state'].eq(CTempInvalidState.annulled)], table['id'].name())
            resultId = forceRef(record.value('id')) if record else None
        return resultId


    def requestFssForDocument(self):
        snils = self.getClientSNILS()
        row = self.tblDocuments.currentIndex().row()
        number = forceString(self.modelDocuments.value(row, 'number'))
        if snils and number:
            showDocumentInfo(self, snils, number)


    def requestFssForPrevDocument(self):
        snils = self.getClientSNILS()
        row = self.tblDocuments.currentIndex().row()
        number = forceString(self.modelDocuments.value(row, 'prevNumber'))
        if snils and number:
            showDocumentInfo(self, snils, number)


    def requestFssByNumber(self):
        dlg = CTempInvalidRequestFSSByNumber(self)
        if dlg.exec_():
            number = unicode(dlg.edtQuery.text())
            snils = self.getClientSNILS()
            if snils and number:
                showDocumentInfo(self, snils, number)


    def createContinuation(self):
        document = self.tblDocuments.currentItem()
        if document:
            isExternal   = forceBool(document.value('isExternal'))
            isElectronic = forceBool(document.value('electronic'))
            number       = forceString(document.value('number'))
            annulmentReasonId = forceRef(document.value('annulmentReason_Id'))
            if isExternal and number and not annulmentReasonId:
                if isElectronic:
                    ok, continuationNumber = QtGui.qApp.call(None, acquireElectronicTempInvalidNumber)
                else:
                    continuationNumber = ''
                continuation = self.modelDocuments.getEmptyRecord()
                continuation.setValue('electronic', isElectronic)
                continuation.setValue('issueDate',  QDate.currentDate())
                continuation.setValue('number',     continuationNumber)
                continuation.setValue('busyness',   document.value('busyness'))
                continuation.setValue('placeWork',  document.value('placeWork'))
                continuation.setValue('prevNumber', number)
                newCareRecords = []
                db = QtGui.qApp.db
                careItems = document.tempInvalidCare.getItems()
                for careItem in careItems:
                    newCareRecord = db.table('TempInvalidDocument_Care').newRecord()
                    copyFields(newCareRecord, careItem)
                    newCareRecord.setValue('id', toVariant(None))
                    newCareRecords.append(newCareRecord)
                continuation.tempInvalidCare.setItems(newCareRecords)
                self.modelDocuments.addRecord(continuation)


    def annulment(self):
        snils = self.getClientSNILS()
        row = self.tblDocuments.currentIndex().row()
        number = forceString(self.modelDocuments.value(row, 'number'))
        if snils and number:
            annulmentReasonId = annulment(self, snils, number)
            if annulmentReasonId:
                self.modelDocuments.setValue(row, 'annulmentReason_id', annulmentReasonId)
                if self.checkDataEntered():
                    self.save()
                    self.modelDocuments.reset()


    def requestFss(self):
        snils = self.getClientSNILS()
        currExternalPeriods = [row
                               for (row, item) in enumerate(self.modelPeriods.items())
                               if forceBool(item.value('isExternal'))
                              ]
        numbers = set()
        prevNumbers = set()
        for documentRecord in self.modelDocuments.items():
            number = forceString(documentRecord.value('number'))
            if number:
                numbers.add(number)
            prevNumber = forceString(documentRecord.value('prevNumber'))
            if prevNumber:
                prevNumbers.add(prevNumber)

        isPeriodsSignature = bool(self.modelPeriods.periodsSignaturesC or self.modelPeriods.periodsSignaturesD)
        predecessors, externalPeriod = searchCase(self, snils, bool(currExternalPeriods), numbers, prevNumbers, isPeriodsSignature=isPeriodsSignature)
        toImport = None
        if predecessors:
            predecessor = predecessors[0]
            self.cmbReason.setCode(predecessor['reason'])
            # self.cmbReason.setEnabled(False)
            self.cmbExtraReason.setCode(predecessor['extraReason'])
            if predecessor['diagnosis']:
                self.edtDiagnosis.setText(predecessor['diagnosis'])
            if (     all( item.value('id').isNull() for item in self.modelPeriods.items() )
                 and all( documentRecord.value('id').isNull() for documentRecord in self.modelDocuments.items() )
               ):
                orgId = QtGui.qApp.currentOrgId()
                orgInfo = getOrganisationInfo(orgId)
                ogrn = orgInfo['OGRN']
                if predecessors[0]['issueOrgOgrn'] == ogrn and predecessors[0]['state'] in ('010', '020'):
                    toImport = predecessors[0]
                    self.modelPeriods.clearItems()
                    self.modelDocuments.clearItems()

            for predecessor in predecessors:
                document = self.modelDocuments.getEmptyRecord()
                document.setValue('electronic', True)
                document.setValue('issueDate',  predecessor['issueDate'])
                document.setValue('number',     predecessor['number'])
                if toImport == predecessor:
                    document.setValue('isExternal', False)
                    document.setValue('fssStatus', 'P%d' % (len(predecessor['period'])-1))
                else:
                    document.setValue('isExternal', True)
                if not self.itemId():
                    self.modelDocuments.clearItems()
                if not self.itemId():
                    self.modelDocuments.clearItems()
                self.modelDocuments.addRecord(document)
        if externalPeriod:
            if not self.itemId():
                self.modelPeriods.clearItems()
            elif currExternalPeriods:
                for row in reversed(currExternalPeriods):
                    self.modelPeriods.removeRow(row)
            periodRecord = self.modelPeriods.getEmptyRecord()
            periodRecord.setValue('isExternal', True)
            periodRecord.setValue('begDate', externalPeriod[0])
            periodRecord.setValue('endDate', externalPeriod[1])
            periodRecord.setValue('duration', externalPeriod[0].daysTo(externalPeriod[1])+1)
            self.modelPeriods.insertRecord(0, periodRecord)
            self.edtCaseBegDate.setDate(externalPeriod[0])

        if toImport:
            for period in toImport['period']:
                periodRecord = self.modelPeriods.getEmptyRecord()
                periodRecord.setValue('isExternal', False)
                periodRecord.setValue('begDate', period['begDate'])
                periodRecord.setValue('endDate', period['endDate'])
                periodRecord.setValue('duration', period['begDate'].daysTo(period['endDate'])+1)
                periodRecord.setValue('endPerson_id', self.tryGuessPerson(period['doctorName'], period['doctorPost']))
                if period['chairmanName']:
                    periodRecord.setValue('chairPerson_id', self.tryGuessPerson(period['chairmanName']))
                self.modelPeriods.addRecord(periodRecord)
            self.edtCaseBegDate.setDate(toImport['period'][0]['begDate'])
        self.setDocumentsSignaturesNoSave()


    def tryGuessPerson(self, name, post=''):
        db = QtGui.qApp.db

        if post:
            tablePost = db.table('rbPost')
            postIds = db.getIdList(tablePost, 'id', tablePost['name'].like('%' + post.replace(' ','%') + '%'))
        else:
            postIds = []

        tablePerson = db.table('Person')
        name = name.replace('_', ' ')
        parts = name.split(None, 1)
        lastName = parts[0]
        initials = parts[1] if len(parts) > 1 else ''
        firstNameInitial = patrNameInitial = ''
        if initials:
            if ' ' in initials:
                firstNameInitial, patrNameInitial = initials.split(None, 1)
                firstNameInitial = firstNameInitial.split('.', 1)[0]
                patrNameInitial  = patrNameInitial.split('.', 1)[0]
            elif '.' in initials:
                firstNameInitial, patrNameInitial = initials.split('.', 1)
                patrNameInitial = patrNameInitial.rstrip('.')
                if '.' in patrNameInitial:
                    patrNameInitial = ''
            elif len(initials) == 2:
                firstNameInitial, patrNameInitial = initials[0], initials[1]
        personCondParts = [ tablePerson['deleted'].eq(0),
                            tablePerson['retired'].eq(0),
                            tablePerson['org_id'].eq(QtGui.qApp.currentOrgId()),
                            tablePerson['lastName'].eq(lastName),
                            tablePerson['firstName'].like(firstNameInitial + '%'),
                            tablePerson['patrName'].like(patrNameInitial + '%'),
                          ]
        if postIds:
            personIdList = db.getIdList(tablePerson, 'id', personCondParts + [tablePerson['post_id'].inlist(postIds)])
            if personIdList:
                return personIdList[0]
        personIdList = db.getIdList(tablePerson, 'id', personCondParts)
        if personIdList:
            return personIdList[0]
        return None


    def somethingCanBeSigned(self):
        return any( self.documentCanBeSigned(document)
                    for document in self.modelDocuments.items()
                  )


    def convertInvalidPeriodsToSignaturePeriods(self, issueDate, invalidPeriods, duplicate=False):
        tmpDate = None
        result = []
        for invalidPeriod in invalidPeriods:
            if forceBool(invalidPeriod.value('isExternal')):
                continue
            begDate       = forceDate(invalidPeriod.value('begDate'))
            endDate       = forceDate(invalidPeriod.value('endDate'))
            personId      = forceRef(invalidPeriod.value('endPerson_id'))
            chairPersonId = forceRef(invalidPeriod.value('chairPerson_id'))

            if tmpDate is None or tmpDate < begDate:
                tmpDate = begDate

            #if issueDate <= endDate or duplicate or (issueDate > endDate and ((len(invalidPeriods) == 1 and forceBool(invalidPeriod.value('isExternal')) == 0) or busyness == 2)):
            if issueDate and endDate:
                result.append( CSignaturePeriod(len(result), tmpDate, endDate, personId, chairPersonId) )
        return result


    def documentCanBeSigned(self, document):
        if not forceBool(document.value('electronic')):
            return False
        fssStatus = forceString(document.value('fssStatus'))
        if fssStatus == 'R':
            return False
        if forceBool(document.value('isExternal')):
            return self.externalDocumentResultCanBeSigned(document)
        else:
            number = forceString(document.value('number'))
            issueDate = forceDate(document.value('issueDate'))
            if not issueDate or not number:
                return False
            if forceRef(document.value('annulmentReason_id')):
                return False
            if forceBool(document.value('duplicate')):
                return False
            for period in self.convertInvalidPeriodsToSignaturePeriods(issueDate, self.modelPeriods.items()):
                if self.documentPeriodCanBeSigned(document, period):
                    return True
                if self.documentFullPeriodCanBeSigned(document, period):
                    return True
            if self.documentBreachCanBeSigned(document):
                return True
            if self.documentResultCanBeSigned(document):
                return True
        return False


    def documentPeriodCanBeSigned(self, document, period):
        periodSubject = document.signatures.periodSubject(period.idx)
        fssStatus = forceString(document.value('fssStatus'))
        begDate  = period.begDate
        endDate  = period.endDate
        personId = period.personId
        return (     begDate
                 and endDate
                 and personId
                 and not document.signatures.present(periodSubject)
                 and (    period.idx == 0 and fssStatus == ''
                       or period.idx > 0  and fssStatus == 'P%d' % (period.idx-1)
                     )
               )


    def documentPeriodSignatureCanBeRevoked(self, document, period):
        periodSubject = document.signatures.periodSubject(period.idx)
        fssStatus = forceString(document.value('fssStatus'))
        return ( document.signatures.present(periodSubject)
                 and (   (     period.idx == 0
                           and fssStatus == ''
                         )
                      or (     period.idx > 0
                           and fssStatus == 'P%d' % (period.idx-1)
                         )
                     )
               )


    def documentFullPeriodCanBeSigned(self, document, period):
        periodSubject = document.signatures.periodSubject(period.idx)
        fullPeriodSubject = document.signatures.fullPeriodSubject(period.idx)
        fssStatus = forceString(document.value('fssStatus'))
        chairmanId = period.chairPersonId
        return (     chairmanId
                 and document.signatures.present(periodSubject)
                 and not document.signatures.present(fullPeriodSubject)
                 and (    period.idx == 0 and fssStatus == ''
                       or period.idx > 0  and fssStatus == 'P%d' % (period.idx-1)
                     )
               )


    def documentFullPeriodSignatureCanBeRevoked(self, document, period):
        fullPeriodSubject = document.signatures.fullPeriodSubject(period.idx)
        fssStatus = forceString(document.value('fssStatus'))
        return ( document.signatures.present(fullPeriodSubject)
                 and (   (     period.idx == 0
                           and fssStatus == ''
                         )
                      or (     period.idx > 0
                           and fssStatus == 'P%d' % (period.idx-1)
                         )
                     )
               )


    def documentBreachCanBeSigned(self, document):
        breachId   = self.cmbBreak.value()
        breachDate = self.edtBreakDate.date()
        isExternal = forceBool(document.value('isExternal'))
        fssStatus = forceString(document.value('fssStatus'))
        return (     breachId
                 and breachDate
                 and not document.signatures.present(document.signatures.breachSubject())
                 and ( isExternal and fssStatus == '' or fssStatus.startswith('P')
                     )
               )


    def documentBreachSignatureCanBeRevoked(self, document):
        subject = document.signatures.breachSubject()
        isExternal = forceBool(document.value('isExternal'))
        fssStatus = forceString(document.value('fssStatus'))
        return (     document.signatures.present(subject)
                 and (isExternal and fssStatus == '' or fssStatus.startswith('P')
                     )
               )


    def documentResultCanBeSigned(self, document):
        number = forceString(document.value('number'))
        if not number:
            return False

        if self.mustHaveResultDate():
            if not self.edtResultDate.date():
                return False
        if self.mustHaveOtherDate():
            if not self.edtResultOtherwiseDate.date():
                return False
        if self.mustHaveContinuation():
            if not self.modelDocuments.findNextDocumentNumber(number):
                return False
        return not document.signatures.present(document.signatures.resultSubject())


    def documentResultSignatureCanBeRevoked(self, document):
        return (     document.signatures.present(document.signatures.resultSubject())
                and not forceString(document.value('fssStatus')).startswith(('R'))
               )


    def externalDocumentResultCanBeSigned(self, document):
        number = forceString(document.value('number'))
        if not number:
            return False

        if self.mustHaveResultDate():
            resultDate = self.edtResultDate.date()
            if not resultDate:
                return False
            maxEndDate = None
            for period in self.modelPeriods.items():
                # if not forceBool(period.value('isExternal')):
                #     return False
                endDate = forceDate(period.value('endDate'))
                maxEndDate = max(maxEndDate, endDate) if maxEndDate else endDate
            if not maxEndDate:
                return False
            if maxEndDate.addDays(1) != resultDate:
                return False
        if self.mustHaveOtherDate():
            if not self.edtResultOtherwiseDate.date():
                return False
        if self.mustHaveContinuation():
            if not self.modelDocuments.findNextDocumentNumber(number):
                return False
        return not document.signatures.present(document.signatures.resultSubject())


    def oldDocumentResultSignatureRequired(self, tempInvalidDocumentId):
        db = QtGui.qApp.db
        electronic = forceBool(db.translate('TempInvalidDocument', 'id', tempInvalidDocumentId, 'electronic'))
        if electronic:
            table = db.table('TempInvalidDocument_Signature')
            record = db.getRecordEx(table,
                                    'id',
                                    [ table['master_id'].eq(tempInvalidDocumentId),
                                      table['subject'].eq(CSignatureRegistry.resultSubject())
                                    ]
                                   )
            return not bool(record)
        else:
            return False


    def getPersonNameAndPost(self, personId):
        db = QtGui.qApp.db
        personName = forceStringEx(db.translate('vrbPerson', 'id', personId, 'name')).upper().replace('.', '')
        postId   = db.translate('Person', 'id', personId, 'post_id')
        postName = forceStringEx(db.translate('rbPost', 'id', postId, 'name')).upper()
        return personName, postName


    def signDocumentPeriod(self, api, cert, document, period):
        number   = forceString(document.value('number'))
        begDate  = period.begDate
        endDate  = period.endDate
        personId = period.personId
        personName, post = self.getPersonNameAndPost(personId)
        periodElementId, periodActorUri = CFssSignInfo.getTreatPeriodElementIdAndActorUri(number, period.idx)

        tp = createPyObject(fssEln.treatPeriod_Dec)
        tp.TreatDt1 = convertQDateToTuple(begDate)
        tp.TreatDt2 = convertQDateToTuple(endDate)
        tp.TreatDoctor     = personName
        tp.TreatDoctorRole = post
        tp.set_attribute_Id(periodElementId)

        tpDataXml, tpSecurityXml = serializeToXmlAndSignIt(api, cert, tp, periodElementId, periodActorUri, fssNsDict)
        subject = document.signatures.periodSubject(period.idx)
        certName = cert.surName() + ' ' + cert.givenName() + ', ' + cert.snils()
        document.signatures.append(subject, tpDataXml, tpSecurityXml, begDate, endDate, certName)


    def signDocumentFullPeriod(self, api, cert, document, period):
        number   = forceString(document.value('number'))
        begDate  = period.begDate
        endDate  = period.endDate
        personId = period.personId
        chairmanId = period.chairPersonId

        personName, post = self.getPersonNameAndPost(personId)
        chairmanName, chairmanPost = self.getPersonNameAndPost(chairmanId)

        fullPeriodElementId, fullPeriodActorUri = CFssSignInfo.getTreatFullPeriodElementIdAndActorUri(number, period.idx)
        tfp = createPyObject(fssMo.treatFullPeriod_Dec)
        periodSubject = document.signatures.periodSubject(period.idx)
        tp = restoreFromXml(tfp.new_treatPeriod(), document.signatures.getDataXml(periodSubject))
        tfp.TreatPeriod = tp

        assert tp.TreatDt1 == convertQDateToTuple(begDate)
        assert tp.TreatDt2 == convertQDateToTuple(endDate)
        assert fixu(tp.TreatDoctor)  == personName
        assert fixu(tp.TreatDoctorRole) == post

        tfp.TreatChairman = chairmanName
        tfp.TreatChairmanRole = u'ПРЕД ВК'

        tfpDataXml, tfpSecurityXml = serializeToXmlAndSignIt(api, cert, tfp, fullPeriodElementId, fullPeriodActorUri, fssNsDict)
        subject = document.signatures.fullPeriodSubject(period.idx)
        certName = cert.surName() + ' ' + cert.givenName() + ', ' + cert.snils()
        document.signatures.append(subject, tfpDataXml, tfpSecurityXml, begDate, endDate, certName)


    def signDocumentBreach(self, api, cert, document, subject):
        number = forceString(document.value('number'))
        breachCode = self.cmbBreak.code()
        breachDate = self.edtBreakDate.date()

        hbElementId, hbActorUri = CFssSignInfo.getHospitalBreachElementIdAndActorUri(number)

        hb = createPyObject(fssMo.hospitalBreach_Dec)
        hb.HospitalBreachCode = breachCode
        hb.HospitalBreachDt  = convertQDateToTuple(breachDate)
        hbDataXml, hbSecurityXml = serializeToXmlAndSignIt(api, cert, hb, hbElementId, hbActorUri, fssNsDict)
        certName = cert.surName() + ' ' + cert.givenName() + ', ' + cert.snils()
        document.signatures.append(subject, hbDataXml, hbSecurityXml, breachDate, breachDate, certName)


    def signDocumentResult(self, api, cert, document, subject):
        db = QtGui.qApp.db
        number = forceString(document.value('number'))
        code = self.cmbResult.code()
        resultDate = None
        otherStateCode = None if code in ['1', '30'] else code
        otherStateDate = None
        nextNumber = None
        if self.mustHaveResultDate():
            resultDate = self.edtResultDate.date()
        if self.mustHaveOtherDate():
            otherStateDate = self.edtResultOtherwiseDate.date()
        if self.mustHaveContinuation():
            lastId = forceRef(document.value('last_id'))
            if lastId:
                nextNumber = forceString(db.translate('TempInvalidDocument', 'id', lastId, 'number')) or None
            if nextNumber is None:
                nextNumber = self.modelDocuments.findNextDocumentNumber(number)
        lnrElementId, lnrActorUri = CFssSignInfo.getLnResultElementIdAndActorUri(number)
        lnr = createPyObject(fssMo.lnResult_Dec)
        lnr.ReturnDateLpu = convertQDateToTuple(resultDate) if resultDate else None
        lnr.MseResult = otherStateCode
        lnr.OtherStateDt = convertQDateToTuple(otherStateDate) if otherStateDate else None
        lnr.NextLnCode = nextNumber
        lnrDataXml, lnrSecurityXml = serializeToXmlAndSignIt(api, cert, lnr, lnrElementId, lnrActorUri, fssNsDict)
        date = resultDate or otherStateDate
        certName = cert.surName() + ' ' + cert.givenName() + ', ' + cert.snils()
        document.signatures.append(subject, lnrDataXml, lnrSecurityXml, date, date, certName)


    def signOldDocumentResult(self, api, cert, document, nextNumber):
        db = QtGui.qApp.db
        number     = forceString(document.value('number'))
        tempInvalid = db.getRecord('TempInvalid',  '*', document.value('master_id'))
        resultId = forceRef(tempInvalid.value('result_id'))
        code = forceString(db.translate('rbTempInvalidResult', 'id', resultId, 'code'))

        if '31' <= code <= '37' or nextNumber:
            resultDate     = None
            otherStateCode = code or '31'
            otherStateDate = forceDate(tempInvalid.value('otherStateDate'))
        else:
            resultDate = forceDate(tempInvalid.value('resultDate'))
            otherStateCode = None
            otherStateDate = None
        lnrElementId, lnrActorUri = CFssSignInfo.getLnResultElementIdAndActorUri(number)
        lnr = createPyObject(fssMo.lnResult_Dec)
        lnr.ReturndateLpu = convertQDateToTuple(resultDate) if resultDate else None
        lnr.MseResult = otherStateCode
        lnr.OtherStateDt = convertQDateToTuple(otherStateDate) if otherStateDate else None
        lnr.NextLnCode = nextNumber
        lnrDataXml, lnrSecurityXml = serializeToXmlAndSignIt(api, cert, lnr, lnrElementId, lnrActorUri, fssNsDict)
        date = resultDate or otherStateDate
        certName = cert.surName() + ' ' + cert.givenName() + ', ' + cert.snils()
        signatureRecord = CSignatureRegistry.newRecord(CSignatureRegistry.resultSubject(),
                                                       lnrDataXml,
                                                       lnrSecurityXml,
                                                       date,
                                                       date,
                                                       certName
                                                      )
        signatureRecord.setValue('master_id',  document.value('id'))
        db.insertRecord('TempInvalidDocument_Signature', signatureRecord)


    def signExternalDocumentResult(self, api, cert, document, subject):
        number = forceString(document.value('number'))
        lastId = forceRef(document.value('last_id'))
        code = self.cmbResult.code()
        resultDate = None
        otherStateCode = None if code in ['1', '30'] else code
        otherStateDate = None
        nextNumber = None
        db = QtGui.qApp.db
        tableTempInvalidDocument = db.table('TempInvalidDocument')
        if lastId:
            recordTD = db.getRecordEx(tableTempInvalidDocument, [tableTempInvalidDocument['number']], [tableTempInvalidDocument['id'].eq(lastId), tableTempInvalidDocument['deleted'].eq(0)])
            nextNumber = forceString(recordTD.value('number')) if recordTD else None
        if nextNumber is None:
            nextNumber = self.modelDocuments.findNextDocumentNumber(number)
        if self.mustHaveResultDate():
            resultDate = self.edtResultDate.date()
            maxEndDate = None
            for period in self.modelPeriods.items():
                if forceBool(period.value('isExternal')):
                    endDate = forceDate(period.value('endDate'))
                    maxEndDate = max(maxEndDate, endDate) if maxEndDate else endDate
            if not self.mustHaveContinuation():
                if maxEndDate and maxEndDate.addDays(1) != resultDate and (lastId or nextNumber is not None):
                    resultDate = None
                    otherStateCode = '31'
        if self.mustHaveOtherDate():
            otherStateDate = self.edtResultOtherwiseDate.date()
        if self.mustHaveContinuation():
            # nextNumber = self.modelDocuments.findNextDocumentNumber(number)
            assert nextNumber
            resultDate = None
            otherStateCode = '31'

        lnrElementId, lnrActorUri = CFssSignInfo.getLnResultElementIdAndActorUri(number)
        lnr = createPyObject(fssMo.lnResult_Dec)
        lnr.ReturnDateLpu = convertQDateToTuple(resultDate) if resultDate else None
        lnr.MseResult = otherStateCode
        lnr.OtherStateDt = convertQDateToTuple(otherStateDate) if otherStateDate else None
        lnr.NextLnCode = nextNumber
        lnrDataXml, lnrSecurityXml = serializeToXmlAndSignIt(api, cert, lnr, lnrElementId, lnrActorUri, fssNsDict)
        date = resultDate or QDate().currentDate()
        certName = cert.surName() + ' ' + cert.givenName() + ', ' + cert.snils()
        document.signatures.append(subject, lnrDataXml, lnrSecurityXml, date, date, certName)


    def signElements(self):
        db = QtGui.qApp.db

        if not self.checkDataEntered():
            return

        dlg = CTempInvalidSignatureSubjectSelector(self)
        for document in self.modelDocuments.items():
            isElectronic = forceBool(document.value('electronic'))
            if forceRef(document.value('annulmentReason_id')):
                continue
            issueDate = forceDate(document.value('issueDate'))
            number    = forceString( document.value('number') )
            placeWork = forceString( document.value('placeWork') )
            duplicate = forceBool(document.value('duplicate'))

            if forceBool(document.value('isExternal')):
                if isElectronic:
                    partName = u'Отметки о нарушение режима внешнего ЭЛН'
                    subject = document.signatures.breachSubject()
                    if document.signatures.present(subject):
                        dlg.addDocumentPart(number,
                                            placeWork,
                                            partName,
                                            document.signatures.getSignPersonId(subject),
                                            document.signatures.getSignOwner(subject),
                                            document.signatures.getSignDatetime(subject),
                                            None
                                           )
                    elif self.documentBreachCanBeSigned(document):
                        dlg.addDocumentPart(number,
                                            placeWork,
                                            partName,
                                            None,
                                            None,
                                            None,
                                            lambda api, cert, document=document, subject=subject: self.signDocumentBreach(api, cert, document, subject)
                                           )
                    partName = u'Результат внешнего ЭЛН'
                    subject = document.signatures.resultSubject()
                    if document.signatures.present(subject):
                        dlg.addDocumentPart(number,
                                            placeWork,
                                            partName,
                                            document.signatures.getSignPersonId(subject),
                                            document.signatures.getSignOwner(subject),
                                            document.signatures.getSignDatetime(subject),
                                            None
                                           )
                    elif self.externalDocumentResultCanBeSigned(document):
                        dlg.addDocumentPart(number,
                                            placeWork,
                                            partName,
                                            None,
                                            None,
                                            None,
                                            lambda api, cert, document=document, subject=subject: self.signExternalDocumentResult(api, cert, document, subject)
                                           )
            else:
                prevDocumentId = forceRef(document.value('prev_id'))
                if prevDocumentId and self.oldDocumentResultSignatureRequired(prevDocumentId):
                    prevDocument = db.getRecord('TempInvalidDocument', ['id, number, placeWork, master_id'], prevDocumentId)
                    if not forceString(prevDocument.value('number')) in map(lambda x: forceString(x.value('number')), dlg.modelSingnatureSubjectSelector._items):
                        dlg.addDocumentPart(forceString(prevDocument.value('number')),
                                            forceString(prevDocument.value('placeWork')).upper(),
                                            u'Результат внешнего ЭЛН',
                                            None,
                                            None,
                                            None,
                                            lambda api, cert, prevDocument=prevDocument, number=number: self.signOldDocumentResult(api, cert, prevDocument, number)
                                            )
                if isElectronic:
                    for period in self.convertInvalidPeriodsToSignaturePeriods(issueDate, self.modelPeriods.items(), duplicate):
                        partName = u'Врач за период №%d, с %s по %s' % ( period.idx+1,  forceString(period.begDate),  forceString(period.endDate))
                        subject = document.signatures.periodSubject(period.idx)
                        if document.signatures.present(subject):
                            dlg.addDocumentPart(number,
                                                placeWork,
                                                partName,
                                                document.signatures.getSignPersonId(subject),
                                                document.signatures.getSignOwner(subject),
                                                document.signatures.getSignDatetime(subject),
                                                None
                                               )
                        elif self.documentPeriodCanBeSigned(document, period):
                            dlg.addDocumentPart(number,
                                                placeWork,
                                                partName,
                                                None,
                                                None,
                                                None,
                                                lambda api, cert, document=document, period=period: self.signDocumentPeriod(api, cert, document, period)
                                               )
                        partName = u'Пред.ВК за период №%d, с %s по %s' % ( period.idx+1,  forceString(period.begDate),  forceString(period.endDate))
                        subject = document.signatures.fullPeriodSubject(period.idx)
                        if document.signatures.present(subject):
                            dlg.addDocumentPart(number,
                                                placeWork,
                                                partName,
                                                document.signatures.getSignPersonId(subject),
                                                document.signatures.getSignOwner(subject),
                                                document.signatures.getSignDatetime(subject),
                                                None
                                               )
                        elif self.documentFullPeriodCanBeSigned(document, period):
                            dlg.addDocumentPart(number,
                                                placeWork,
                                                partName,
                                                None,
                                                None,
                                                None,
                                                lambda api, cert, document=document, period=period: self.signDocumentFullPeriod(api, cert, document, period)
                                               )
                    partName = u'Отметки о нарушение режима'
                    subject = document.signatures.breachSubject()
                    if document.signatures.present(subject):
                        dlg.addDocumentPart(number,
                                            placeWork,
                                            partName,
                                            document.signatures.getSignPersonId(subject),
                                            document.signatures.getSignOwner(subject),
                                            document.signatures.getSignDatetime(subject),
                                            None
                                           )
                    elif self.documentBreachCanBeSigned(document):
                        dlg.addDocumentPart(number,
                                            placeWork,
                                            partName,
                                            None,
                                            None,
                                            None,
                                            lambda api, cert, document=document, subject=subject: self.signDocumentBreach(api, cert, document, subject)
                                           )
                    partName = u'Результат'
                    subject = document.signatures.resultSubject()
                    if document.signatures.present(subject):
                        dlg.addDocumentPart(number,
                                            placeWork,
                                            partName,
                                            document.signatures.getSignPersonId(subject),
                                            document.signatures.getSignOwner(subject),
                                            document.signatures.getSignDatetime(subject),
                                            None
                                           )
                    elif self.documentResultCanBeSigned(document):
                        dlg.addDocumentPart(number,
                                            placeWork,
                                            partName,
                                            None,
                                            None,
                                            None,
                                            lambda api, cert, document=document, subject=subject: self.signDocumentResult(api, cert, document, subject)
                                           )
        if dlg.exec_():
            api = MSCApi(QtGui.qApp.getCsp())
            if self.chkUserCert.isChecked():
                userCertSha1 = self.cmbUserCert.value()
                cert = api.findCertInStores(api.SNS_OWN_CERTIFICATES, sha1hex=userCertSha1)
            else:
                cert = QtGui.qApp.getUserCert(api)
            with cert.provider() as master:  # для исключения массового запроса пароля
                assert master  # silence pyflakes
                for signFunc in dlg.getSignFuncsOfCheckedRecords():
                    signFunc(api, cert)
                    document._dirty = True  # Документ теперь подписан, а значит изменился
        return


    def setCsp(self):
        csp = QtGui.qApp.getCsp()
        if csp:
            try:
                api = MSCApi(csp)
            except Exception, e:
                QtGui.QMessageBox.critical( self,
                                            u'Произошла ошибка подключения к криптопровайдеру',
                                            exceptionToUnicode(e),
                                            QtGui.QMessageBox.Close)
                api = None
        else:
            api = None
        self.cmbUserCert.setApi(api)
        if api is None:
            self.chkUserCert.setEnabled(False)
        else:
            self.cmbUserCert.setStores(api.SNS_OWN_CERTIFICATES)
            self.chkUserCert.setEnabled(QtGui.qApp.userHasRight(urRegTabExpertChangeSignVUT))


    def revokeSignatures(self):

        if not self.checkDataEntered():
            return

        dlg = CTempInvalidRevokeSignatureSubjectSelector(self)
        for document in self.modelDocuments.items():
            if not forceBool(document.value('electronic')) or forceRef(document.value('annulmentReason_id')):
                continue

            issueDate = forceDate(document.value('issueDate'))
            number    = forceString( document.value('number') )
            placeWork = forceString( document.value('placeWork') )
            duplicate = forceBool(document.value('duplicate'))

            for period in self.convertInvalidPeriodsToSignaturePeriods(issueDate, self.modelPeriods.items(), duplicate):
                partName = u'Врач за период №%d, с %s по %s' % ( period.idx+1,  forceString(period.begDate),  forceString(period.endDate))
                subject = document.signatures.periodSubject(period.idx)
                if self.documentPeriodSignatureCanBeRevoked(document, period):
                    dlg.addDocumentPart(number,
                                        placeWork,
                                        partName,
                                        document.signatures.getSignPersonId(subject),
                                        document.signatures.getSignOwner(subject),
                                        document.signatures.getSignDatetime(subject),
                                        lambda document=document, subject=subject: document.signatures.remove(subject)
                                       )
                partName = u'Пред.ВК за период №%d, с %s по %s' % ( period.idx+1,  forceString(period.begDate),  forceString(period.endDate))
                subject = document.signatures.fullPeriodSubject(period.idx)
                if self.documentFullPeriodSignatureCanBeRevoked(document, period):
                    dlg.addDocumentPart(number,
                                        placeWork,
                                        partName,
                                        document.signatures.getSignPersonId(subject),
                                        document.signatures.getSignOwner(subject),
                                        document.signatures.getSignDatetime(subject),
                                        lambda document=document, subject=subject: document.signatures.remove(subject)
                                       )
            partName = u'Отметки о нарушение режима'
            subject = document.signatures.breachSubject()
            if self.documentBreachSignatureCanBeRevoked(document):
                dlg.addDocumentPart(number,
                                    placeWork,
                                    partName,
                                    document.signatures.getSignPersonId(subject),
                                    document.signatures.getSignOwner(subject),
                                    document.signatures.getSignDatetime(subject),
                                    lambda document=document, subject=subject: document.signatures.remove(subject)
                                   )
            partName = u'Результат'
            subject = document.signatures.resultSubject()
            if self.documentResultSignatureCanBeRevoked(document):
                dlg.addDocumentPart(number,
                                    placeWork,
                                    partName,
                                    document.signatures.getSignPersonId(subject),
                                    document.signatures.getSignOwner(subject),
                                    document.signatures.getSignDatetime(subject),
                                    lambda document=document, subject=subject: document.signatures.remove(subject)
                                   )
        if dlg.exec_():
            for revokeFunc in dlg.getRevokeFuncsOfCheckedRecords():
                revokeFunc()
        return


    @pyqtSignature('')
    def on_tblDocuments_popupMenuAboutToShow(self):
        document = self.tblDocuments.currentItem()
        if document:
            isExternal   = forceBool(document.value('isExternal'))
            isElectronic = forceBool(document.value('electronic'))
            number       = forceString(document.value('number'))
            prevNumber   = forceString(document.value('prevNumber'))
            annulmentReasonId = forceRef(document.value('annulmentReason_Id'))
        else:
            isExternal   = False
            isElectronic = False
            number       = None
            prevNumber   = None
            annulmentReasonId = None
        self.actCreateContinuation.setEnabled(isExternal and bool(number) and not annulmentReasonId)
        self.actRequestFSSForDocument.setEnabled(isElectronic and bool(number))
        self.actRequestFSSForPrevDocument.setEnabled(isElectronic and bool(prevNumber))
        self.actRequestFSSByNumber.setEnabled(True)
        self.actAnnulment.setEnabled(isElectronic and bool(number) and not annulmentReasonId)


    @pyqtSignature('')
    def on_actCreateContinuation_triggered(self):
        self.createContinuation()


    @pyqtSignature('bool')
    def on_chkUserCert_toggled(self, value):
        self.cmbUserCert.setEnabled(value)


    @pyqtSignature('')
    def on_actRequestFSSForDocument_triggered(self):
        QtGui.qApp.call(self, self.requestFssForDocument)


    @pyqtSignature('')
    def on_actRequestFSSForPrevDocument_triggered(self):
        QtGui.qApp.call(self, self.requestFssForPrevDocument)


    @pyqtSignature('')
    def on_actRequestFSSByNumber_triggered(self):
        QtGui.qApp.call(self, self.requestFssByNumber)


    @pyqtSignature('')
    def on_actAnnulment_triggered(self):
        QtGui.qApp.call(self, self.annulment)


    @pyqtSignature('')
    def on_btnRequestFss_clicked(self):
        QtGui.qApp.call(self, self.requestFss)


    @pyqtSignature('')
    def on_btnDuplicate_clicked(self):
        QtGui.qApp.call(self, self.createDuplicate)


    def createDuplicate(self):
        itemId = self.itemId()
        if itemId:
            if not self.checkDataEntered():
                return
            if not self.save():
                return
            db = QtGui.qApp.db
            tableTempInvalid = db.table('TempInvalid')
            prevRecord = db.getRecordEx(tableTempInvalid, '*', [tableTempInvalid['id'].eq(itemId), tableTempInvalid['deleted'].eq(0)])
            if prevRecord:
                documentItems = self.modelDocuments.items()
                periodsItems = self.modelPeriods.items()
                self.newDuplicateTempInvalid(prevRecord)
                addDocumentsItems = []
                for documentItem in documentItems:
                    if forceBool(documentItem.value('electronic')) and not forceBool(documentItem.value('duplicate')):
                        addDocumentsItems.append(documentItem)
                newDocumentsItems = self.newDuplicateTempInvalidDocuments(addDocumentsItems)
                self.modelDocuments.clearItems()
                for row, newItem in enumerate(newDocumentsItems):
                    self.modelDocuments.insertRecord(row, newItem)
                self.modelDocuments.reset()
                externalPeriodsItems = []
                internalPeriodsItems = []
                newPeriodsItems = []
                begDatePeriod = None
                endDatePeriod = None
                for periodItem in periodsItems:
                    if forceBool(periodItem.value('isExternal')):
                        externalPeriodsItems.append(periodItem)
                    if not forceBool(periodItem.value('isExternal')):
                        internalPeriodsItems.append(periodItem)
                if internalPeriodsItems:
                    internalPeriodsItems.sort(key=lambda x: forceDateTime(x.value('begDate')))
                    begDatePeriod = forceDate(internalPeriodsItems[0].value('begDate'))
                    internalPeriodsItems.sort(key=lambda x: forceDateTime(x.value('endDate')), reverse=True)
                    endDatePeriod = forceDate(internalPeriodsItems[0].value('endDate'))
                newExternalPeriodsItems = self.newDuplicateTempInvalidPeriods(externalPeriodsItems)
                if newExternalPeriodsItems:
                    newPeriodsItems.extend(newExternalPeriodsItems)
                if internalPeriodsItems and begDatePeriod and endDatePeriod:
                    internalPeriodsItem = internalPeriodsItems[0]
                    newInternalPeriodsItems = self.newDuplicateTempInvalidPeriods([internalPeriodsItem])
                    if newInternalPeriodsItems:
                        newInternalPeriodsItem = newInternalPeriodsItems[0]
                        newInternalPeriodsItem.setValue('begDate', toVariant(begDatePeriod))
                        newInternalPeriodsItem.setValue('duration', toVariant(self.modelPeriods._calcDuration(begDatePeriod, forceDate(newInternalPeriodsItem.value('endDate')))))
                        newPeriodsItems.extend([newInternalPeriodsItem])
                self.modelPeriods.clearItems()
                for row, newItem in enumerate(newPeriodsItems):
                    self.modelPeriods.insertRecord(row, newItem)
                self.modelPeriods.reset()
                self.tblPeriods.setFocus(Qt.OtherFocusReason)
                self.tblPeriods.setCurrentIndex(self.modelPeriods.index(0, 1))
                if self.modelPeriods.items():
                    self.updateLength()
                self.modelDocuments.setAnnulledDublicate(True)
                self.setDocumentsSignatures()
                self.tblDocuments.setCurrentRow(0)
                if not forceRef(prevRecord.value('prev_id')) and forceInt(prevRecord.value('state')) == CTempInvalidState.annulled:
                    self.edtCaseBegDate.setDate(self.modelPeriods.begDate())


    def newDuplicateTempInvalidPeriods(self, items):
        newItems = []
        for item in items:
            newRecord = self.modelPeriods.getEmptyRecord()
            copyFields(newRecord, item)
            newRecord.setValue('id', toVariant(None))
            newRecord.setValue('master_id', toVariant(None))
            newItems.append(newRecord)
        return newItems


    def newDuplicateTempInvalidDocuments(self, items):
        newItems = []
        db = QtGui.qApp.db
        for item in items:
            annulmentReasonId = forceRef(item.value('annulmentReason_id'))
            if annulmentReasonId:
                prevId = forceRef(item.value('id'))
                newItem = self.modelDocuments.getEmptyRecord()
                copyFields(newItem, item)
                newItem.setValue('id',                 toVariant(None))
                newItem.setValue('master_id',          toVariant(None))
                newItem.setValue('annulmentReason_id', toVariant(None))
                newItem.setValue('issueDate',          toVariant(QDate.currentDate()))
                newItem.setValue('serial',             '')
                newItem.setValue('number',             '')
                if forceBool(item.value('electronic')):
                    ok, number = QtGui.qApp.call(None, acquireElectronicTempInvalidNumber)
                    if ok:
                        newItem.setValue('number',     number)
                    else:
                        newItem.setValue('electronic', False)
                newItem.setValue('duplicate',          toVariant(1))
                newItem.setValue('duplicateReason_id', item.value('duplicateReason_id'))
                newItem.setValue('prevDuplicate_id',   toVariant(prevId))
                newItem.setValue('prevNumber',         item.value('prevNumber'))
                newItem.setValue('prev_id',            toVariant(None))
                newItem.setValue('last_id',            toVariant(None))
                newItem.setValue('person_id',          item.value('person_id'))
                newItem.setValue('execPerson_id',      item.value('execPerson_id'))
                newItem.setValue('note',               '')
                newItem.setValue('fssStatus',          '')
                newCareRecords = []
                careItems = item.tempInvalidCare.getItems()
                for careItem in careItems:
                    newCareRecord = db.table('TempInvalidDocument_Care').newRecord()
                    copyFields(newCareRecord, careItem)
                    newCareRecord.setValue('id', toVariant(None))
                    newCareRecords.append(newCareRecord)
                newItem.tempInvalidCare.setItems(newCareRecords)
                newItems.append(newItem)
        return newItems


    def newDuplicateTempInvalid(self, record):
        self.isReasonPrimary = True
        CItemEditorBaseDialog.setRecord(self, record)
        self.prevId = forceRef(record.value('id'))
        self.prevState = forceInt(record.value('state'))
        self.edtCaseBegDate.setDate(forceDate(record.value('caseBegDate')))
        self.setItemId(None)
        record.setValue('prev_id', toVariant(self.prevId))
        setCheckBoxValue(self.chkInsuranceOfficeMark, record, 'insuranceOfficeMark')
        self.state = CTempInvalidState.opened
        self.clientId = forceRef(record.value('client_id'))
        self.cmbReceiver.setClientId(self.clientId)
        self.cmbEvent.setClientId(self.clientId)
        self.diagnosisId = forceRef(record.value('diagnosis_id'))
        MKB, MKBEx, characterId = self.getMKBs()
        self.edtDiagnosis.setText(MKB)
        self.cmbDiseaseCharacter.setValue(characterId)
        self.setType(forceInt(record.value('type')))
        setRBComboBoxValue(self.cmbDoctype, record, 'doctype_id')
        setRBComboBoxValue(self.cmbReason,  record, 'tempInvalidReason_id')
        setRBComboBoxValue(self.cmbChangedReason,  record, 'tempInvalidChangedReason_id')
        if requiredDiagnosis(self.cmbReason.value()):
            self.lblDiagnosis.setVisible(True)
            self.edtDiagnosis.setVisible(True)
            self.cmbDiseaseCharacter.setVisible(True)
        setRBComboBoxValue(self.cmbExtraReason,  record, 'tempInvalidExtraReason_id')
        setLineEditValue(self.edtNumberPermit, record, 'numberPermit')
        setDateEditValue(self.edtBegDatePermit, record, 'begDatePermit')
        setDateEditValue(self.edtEndDatePermit, record, 'endDatePermit')
        setRBComboBoxValue(self.cmbBreak,  record, 'break_id')
        setDateEditValue(self.edtBreakDate, record, 'breakDate')
        setDateEditValue(self.edtBegDateStationary, record, 'begDateStationary')
        setDateEditValue(self.edtEndDateStationary, record, 'endDateStationary')
        setRBComboBoxValue(self.cmbDisability,  record, 'disability_id')
        setRBComboBoxValue(self.cmbResult,  record, 'result_id')
        setDateEditValue(self.edtResultDate, record, 'resultDate')
        setDateEditValue(self.edtResultOtherwiseDate, record, 'resultOtherwiseDate')
        setLineEditValue(self.edtOGRN, record, 'OGRN')
        setRBComboBoxValue(self.cmbTypeEducationalInstitution, record, 'institution_id')
        setLineEditValue(self.edtInfContact, record, 'inf_contact')
        self.on_edtOGRN_textEdited(self.edtOGRN.text())
        self.clientSex, self.clientAge, self.clientAgeTuple = self.getClientSexAge(self.clientId)
        record.setValue('sex', self.clientSex)
        setComboBoxValue(self.cmbOtherSex,  record, 'sex')
        setSpinBoxValue(self.edtOtherAge,   record, 'age')
        self.cmbReceiver.setValue(forceRef(record.value('client_id')))
        self.cmbEvent.setValue(forceRef(record.value('event_id')))
        self.edtCaseBegDate.setDate(forceDate(record.value('caseBegDate')))
        self.cmbAccountPregnancyTo12Weeks.setCurrentIndex(forceInt(record.value('accountPregnancyTo12Weeks')))
        self.setEnabledWidget(self.chkInsuranceOfficeMark.isChecked(), [self.cmbDoctype, self.cmbReason, self.cmbExtraReason, self.edtDiagnosis, self.cmbDiseaseCharacter, self.chkInsuranceOfficeMark, self.tblPeriods])
        self.lastId = None
        self.btnTempInvalidProlong.setEnabled(False)
        self.prolonging = False
        self.defaultBlankMovingId = None
        self.isReasonPrimary = False
        self.newProlonging = False
        self.cmbReceiver.setReadOnly(not (self.getTempInvalidState() == CTempInvalidState.opened  and self.getDocumentsSignature(self.modelDocuments.getTempInvalidDocumentIdList())))
        self.tempInvalidId = None
        record.setValue('result_id', toVariant(None))
        setRBComboBoxValue(self.cmbResult,  record, 'result_id')
        self.modelPeriods.clearItems()
        self.modelCare.clearItems()
        self.modelMedicalCommission.clearItems()
        self.modelMedicalCommissionMSI.clearItems()
        self.documentsSignatures = {}
        self.documentsSignatureR = False
        self.documentsSignatureB = False
        self.documentsSignatureExternalR = False
        self.periodsSignaturesC = {}
        self.periodsSignaturesD  = {}


    @pyqtSignature('')
    def on_btnSignTempInvalidParts_clicked(self):
        QtGui.qApp.call(self, self.signElements)
        self.cmbReceiver.setReadOnly(not (self.getTempInvalidState() == CTempInvalidState.opened and self.getDocumentsSignature(self.modelDocuments.getTempInvalidDocumentIdList())))
        self.setDocumentsSignaturesNoSave()


    @pyqtSignature('')
    def on_btnRevokeTempInvalidSignature_clicked(self):
        QtGui.qApp.call(self, self.revokeSignatures)
        self.cmbReceiver.setReadOnly(not (self.getTempInvalidState() == CTempInvalidState.opened and self.getDocumentsSignature(self.modelDocuments.getTempInvalidDocumentIdList())))
        self.setDocumentsSignaturesNoSave()


    @pyqtSignature('')
    def on_btnTempInvalidProlong_clicked(self):
        items = self.modelDocuments.items()
        for row, item in enumerate(items):
            if forceBool(item.value('duplicate')):
                personId = forceRef(item.value('person_id'))
                if personId:
                    self.modelDocuments.setValue(row, 'execPerson_id', personId)
                else:
                    self.modelDocuments.setValue(row, 'person_id', QtGui.qApp.userId)
                    self.modelDocuments.setValue(row, 'execPerson_id', QtGui.qApp.userId)
            else:
                if not forceRef(item.value('execPerson_id')):
                    self.modelDocuments.setValue(row, 'execPerson_id', toVariant(QtGui.qApp.userId))
        if not self.checkDataEntered():
            return
        self.prolonging = True
        if not self.save():
            self.prolonging = False
            self.saveProlonging = False
            self.updateOtherwiseDate = False
            self.newProlonging = False
            return
        items = []
        documentItems = self.modelDocuments.items()
        for documentItem in documentItems:
            if not forceBool(documentItem.value('isExternal')) and not forceRef(documentItem.value('annulmentReason_id')):
                items.append(documentItem)
        newItems = self.newTempInvalidDocuments(items)
        self.saveProlonging = True
        itemId = self.itemId()
        if itemId:
            db = QtGui.qApp.db
            table = db.table('TempInvalid')
            prevRecord = db.getRecordEx(table,
                                        '*',
                                        [ table['id'].eq(itemId),
                                          table['deleted'].eq(0),
                                          table['client_id'].eq(self.clientId),
                                          table['type'].eq(self.type_),
                                          table['state'].eq(CTempInvalidState.extended)
                                        ],
                                        'endDate DESC')
            self.setPrev(prevRecord)
        self.newTempInvalid(forceDate(self.modelPeriods.endDate().addDays(1)))
        self.modelDocuments.clearItems()
        for row, newItem in enumerate(newItems):
            self.modelDocuments.insertRecord(row, newItem)
        self.updateOtherwiseDate = True
        self.modelDocuments.reset()
        self.edtNumberPermit.setText(u'')
        self.edtBegDatePermit.setDate(QDate())
        self.edtEndDatePermit.setDate(QDate())
        self.cmbBreak.setValue(None)
        self.edtBreakDate.setDate(QDate())
        self.edtBegDateStationary.setDate(QDate())
        self.edtEndDateStationary.setDate(QDate())
        self.cmbDisability.setValue(None)
        self.edtMseDate.setDate(QDate())
        self.cmbResult.setValue(None)
        self.edtResultDate.setDate(QDate())
        self.edtResultOtherwiseDate.setDate(QDate())
        self.tblPeriods.setFocus(Qt.OtherFocusReason)
        self.tblPeriods.setCurrentIndex(self.modelPeriods.index(0, 1))
        self.newProlonging = not self.itemId()
        self.setDocumentsSignatures()
        self.tblDocuments.setCurrentRow(0)


    @pyqtSignature('')
    def on_btnSelectToTransfer_clicked(self):
        tempInvalidId = self.saveData()
        if tempInvalidId:
            if not self.checkDataEntered():
                return
            dlg = CTempInvalidTransferSubjectSelector(self, tempInvalidId)
            dlg.exec_()
            del dlg


    @pyqtSignature('')
    def on_btnApply_clicked(self):
        if self.applyChanges():
            buttons = QtGui.QMessageBox.Ok
            messageBox = QtGui.QMessageBox()
            messageBox.setWindowFlags(messageBox.windowFlags() | Qt.WindowStaysOnTopHint)
            messageBox.setWindowTitle(u'Внимание!')
            messageBox.setText(u'Данные сохранены')
            messageBox.setStandardButtons(buttons)
            messageBox.setDefaultButton(QtGui.QMessageBox.Ok)
            return messageBox.exec_()


    def applyChanges(self):
        if self.saveData():
            QtGui.qApp.delAllCounterValueIdReservation()
            self.lock(self._tableName, self._id)
            return True
        else:
            return False


    def preCreateDirectionMC(self):
        itemId = self.itemId()
        if not itemId:
            if not self.checkDataEntered():
                return False
            tempInvalidId = self.save()
            if tempInvalidId:
                self.setItemId(tempInvalidId)
                db = QtGui.qApp.db
                table = db.table('TempInvalid')
                prevRecord = db.getRecordEx(table,
                                            '*',
                                            [ table['id'].eq(itemId),
                                              table['deleted'].eq(0),
                                              table['client_id'].eq(self.clientId),
                                              table['type'].eq(self.type_),
                                              table['state'].eq(CTempInvalidState.extended)
                                            ],
                                            'endDate DESC')
                self.setPrev(prevRecord)
                self.modelDocuments.setClientId(self.clientId)
                self.modelDocuments.setTempInvalidId(tempInvalidId)
                self.modelDocuments.setTempInvalidPrevId(self.prevId)
                self.modelCare.setTempInvalidId(self.itemId())
                self.modelCare.setTempInvalidClientId(self.clientId)
                return True
            return False
        else:
            return True


    @pyqtSignature('int')
    def on_btnPrint_printByTemplate(self, templateId):
        context = CInfoContext()
        tempInvalidInfo = self.getTempInvalidInfo(context)
        eventInfo = None
        data = { 'event' : eventInfo,
                 'client': context.getInstance(CClientInfo, self.clientId, QDate.currentDate()),
                 'tempInvalid': tempInvalidInfo,
                 'getEventList': lambda begDate, endDate: getEventListByDates(context, self.clientId, begDate, endDate)
               }
        applyTemplate(self, templateId, data)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelDocuments_dataChanged(self, topLeft, bottomRight):
        self.updateLength()
        index = self.tblDocuments.currentIndex()
        if index.isValid():
            row = index.row()
            if bottomRight.column() == CTempInvalidDocumentsModel.Col_Electronic:
                items = self.modelDocuments.items()
                if 0 <= row < len(items):
                    self.modelCare.setIsElectronic(forceBool(items[row].value('electronic')))


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelDocuments_currentRowChanged(self, current, previous):
        index = self.tblDocuments.currentIndex()
        if index.isValid():
            row = index.row()
            items = self.modelDocuments.items()
            if 0 <= row < len(items):
                self.modelCare.setIsElectronic(forceBool(items[row].value('electronic')))
                self.modelCare.setItems(items[row].tempInvalidCare.getItems())
            else:
                self.modelCare.clearItems()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelCare_dataChanged(self, topLeft, bottomRight):
        index = self.tblDocuments.currentIndex()
        if index.isValid():
            row = index.row()
            items = self.modelDocuments.items()
            if 0 <= row < len(items):
                self.modelDocuments.items()[row].tempInvalidCare.setItems(self.modelCare.items())
            else:
                self.modelCare.clearItems()
        else:
            self.modelCare.clearItems()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelPeriods_dataChanged(self, topLeft, bottomRight):
        self.updateLength()
        db = QtGui.qApp.db
        state = self.getTempInvalidState()
        fullLength, externalLength = self.modelPeriods.calcLengths()
        self.btnTempInvalidProlong.setEnabled(state == CTempInvalidState.opened and self.state != CTempInvalidState.extended and fullLength and self.getIsNumberDisabilityFill())
        items = self.modelPeriods.items()
        if len(items) > 0:
            begDate = forceDate(items[0].value('begDate'))
            receiverId = self.cmbReceiver.value()
            if receiverId and requiredOtherPerson(self.cmbReason.value()) and self.type_ != CTempInvalidEditDialog.Disability:
                clientSex, ageClient, clientAgeTuple = self.getClientSexAge(receiverId)
                otherAge = self.edtOtherAge.value()
                if ageClient >= 15 or not otherAge or otherAge < 15:
                    self.edtOtherAge.setValue(ageClient)
                    self.cmbOtherSex.setCurrentIndex(clientSex)
            self.edtDiagnosis.setFilter('''IF(MKB.endDate IS NOT NULL, MKB.endDate >= %s, 1)''' % (db.formatDate(begDate)))
        if not self.prevId:
            self.edtCaseBegDate.setDate(self.modelPeriods.begDate())
        else:
            tableTempInvalid = db.table('TempInvalid')
            prevRecord = db.getRecordEx(tableTempInvalid, '*', [tableTempInvalid['id'].eq(self.prevId), tableTempInvalid['deleted'].eq(0)])
            if prevRecord and not forceRef(prevRecord.value('prev_id')) and forceInt(prevRecord.value('state')) == CTempInvalidState.annulled:
                self.edtCaseBegDate.setDate(self.modelPeriods.begDate())

        begDate = self.modelPeriods.begDate()
        if begDate:
            begDate = begDate.addDays(-7)
        self.cmbEvent.setBegDate(begDate)
        endDate = self.modelPeriods.endDate()
        if endDate:
            endDate = endDate.addDays(7)
        self.cmbEvent.setEndDate(endDate)


    def getPlaceWorkValues(self, clientId):
        placeWorkValues = []
        if clientId:
            db = QtGui.qApp.db
            table = db.table('TempInvalid')
            tableTD = db.table('TempInvalidDocument')
            cond = [table['client_id'].eq(clientId),
                    table['deleted'].eq(0),
                    tableTD['deleted'].eq(0),
                    tableTD['busyness'].ne(0)
                    ]
            group = u'TempInvalidDocument.busyness, TempInvalidDocument.placeWork'
            tableQuery = table.innerJoin(tableTD, tableTD['master_id'].eq(table['id']))
            records = db.getRecordListGroupBy(tableQuery, u'DISTINCT TempInvalidDocument.busyness, TempInvalidDocument.placeWork', cond, group, u'TempInvalidDocument.issueDate DESC')
            for record in records:
                busyness = forceInt(record.value('busyness'))
                if busyness and busyness != 3:
                    placeWork = forceStringEx(record.value('placeWork'))
                    if placeWork and placeWork not in placeWorkValues:
                        placeWorkValues.append(placeWork)
            work = trim(formatWorkTempInvalid(getClientWork(clientId)))
            if work and work not in placeWorkValues:
                placeWorkValues.append(work)
        self.modelDocuments.setPlaceWorkValues(placeWorkValues)


    def getLastPlaceWork(self, clientId):
        placeWorkValues = []
        if clientId:
            db = QtGui.qApp.db
            table = db.table('TempInvalid')
            tableTD = db.table('TempInvalidDocument')
            tableQuery = table.innerJoin(tableTD, tableTD['master_id'].eq(table['id']))
            cond = [table['client_id'].eq(clientId),
                    table['deleted'].eq(0),
                    tableTD['deleted'].eq(0),
                    tableTD['issueDate'].dateLe(QDate.currentDate())
                   ]
            record = db.getRecordEx(tableQuery, [table['id']], cond, 'TempInvalidDocument.issueDate DESC')
            tempInvalidId = forceRef(record.value('id')) if record else None
            if tempInvalidId:
                cols = [tableTD['busyness'],
                        tableTD['placeWork']
                        ]
                cond = [tableTD['master_id'].eq(tempInvalidId),
                        tableTD['deleted'].eq(0)
                        ]
                records = db.getRecordList(tableQuery, cols, cond, u'TempInvalidDocument.issueDate DESC')
                for record in records:
                    busyness = forceInt(record.value('busyness'))
                    if busyness and busyness != 3:
                        placeWork = forceStringEx(record.value('placeWork'))
                        if placeWork and placeWork not in placeWorkValues:
                            placeWorkValues.append((busyness, placeWork))
        return placeWorkValues


class CTempInvalidCreateDialog(CTempInvalidEditDialog):
    def __init__(self,  parent, clientId = None, clientCache = None, MKB = u'', eventId = None):
        CTempInvalidEditDialog.__init__(self, parent, clientCache)
        self.lblDiagnosis.setVisible(True)
        self.edtDiagnosis.setVisible(True)
        self.cmbDiseaseCharacter.setVisible(True)
        self.clientId = clientId
        self.eventId = eventId
        self.MKB = MKB
        self.begDateStationary = None
        self.endDateStationary = None
        self.clientSex = None
        self.clientAge = None
        self.modifiableDiagnosisesMap = {}
        self.mapSpecialityIdToDiagFilter = {}
        self.cmbDiseaseCharacter.setTable('rbDiseaseCharacter', order='code')
        self.cmbReceiver.setClientId(self.clientId)
        self.cmbEvent.setClientId(self.clientId)
        self.cmbEvent.setValue(self.eventId)
        self.on_modelPeriods_dataChanged(0, 0)
        self.placeRegistry = False


    def createTempInvalidDocument(self, MKB=u'', placeRegistry=False, type=0, execDate=None, execPersonId=None, begDateStationary=None, endDateStationary=None):
        self.placeRegistry = placeRegistry
        self.modelDocuments.setClientId(self.clientId)
        self.modelCare.setTempInvalidClientId(self.clientId)
        otherPersonEnabled = requiredOtherPerson(self.cmbReason.value()) if self.type_ != CTempInvalidEditDialog.Disability else True
        self.getPlaceWorkValues(self.clientId)
        placeWorkValues = self.getLastPlaceWork(self.clientId)
        if not placeWorkValues:
            newRecord = self.modelDocuments.getEmptyRecord()
            if not otherPersonEnabled or self.placeRegistry:
                self.cmbReceiver.setValue(self.clientId)
            else:
                self.modelCare.setTempInvalidClientId(self.clientId)
            newRecord.setValue('issueDate', toVariant(execDate) if execDate else toVariant(QDate.currentDate()))
            newRecord.setValue('busyness', toVariant(1))
            newRecord.setValue('placeWork', toVariant(trim(formatWorkTempInvalid(getClientWork(self.clientId)))))
            if execPersonId:
                newRecord.setValue('person_id', toVariant(execPersonId))
            self.modelDocuments.addRecord(newRecord)
        else:
            for (busyness, placeWork) in placeWorkValues:
                newRecord = self.modelDocuments.getEmptyRecord()
                if not otherPersonEnabled or self.placeRegistry:
                    self.cmbReceiver.setValue(self.clientId)
                else:
                    self.modelCare.setTempInvalidClientId(self.clientId)
                newRecord.setValue('issueDate', toVariant(execDate) if execDate else toVariant(QDate.currentDate()))
                newRecord.setValue('busyness', toVariant(busyness))
                newRecord.setValue('placeWork', toVariant(placeWork))
                if execPersonId:
                    newRecord.setValue('person_id', toVariant(execPersonId))
                self.modelDocuments.addRecord(newRecord)
        receiverId = self.cmbReceiver.value()
        sex, ageClient, clientAgeTuple = self.getClientSexAge(receiverId)
        otherAge = self.edtOtherAge.value()
        if otherPersonEnabled and ageClient >= 15 or not otherAge or otherAge < 15:
            self.cmbOtherSex.setCurrentIndex(sex)
            self.edtOtherAge.setValue(ageClient)
        newRecordPeriods = self.modelPeriods.getEmptyRecord()
        self.modelPeriods.addRecord(newRecordPeriods)
        if begDateStationary:
            self.edtBegDateStationary.setDate(begDateStationary)
        if endDateStationary:
            self.edtEndDateStationary.setDate(endDateStationary)
        if MKB:
            acceptable, specifiedMKB, specifiedMKBEx, specifiedCharacterId, specifiedTraumaTypeId, specifiedDispanserId, specifiedRequiresFillingDispanser, specifiedProlongMKB = self.specifyDiagnosis(MKB)
            self.MKB = specifiedMKB
            self.edtDiagnosis.setText(self.MKB)
            self.updateCharacterByMKB(specifiedMKB, specifiedCharacterId)
        itemsPeriods = self.modelPeriods.items()
        if len(itemsPeriods) == 1:
            record = itemsPeriods[0]
            record.setValue('id', toVariant(None))
            record.setValue('begDate', toVariant(execDate) if execDate else toVariant(QDate.currentDate()))
            if execPersonId:
                record.setValue('endPerson_id', toVariant(execPersonId))
            self.modelPeriods.items()[0] = record
        if not self.edtCaseBegDate.date():
            self.edtCaseBegDate.setDate(self.modelPeriods.begDate())
        self.on_modelPeriods_dataChanged(0, 0)
        db = QtGui.qApp.db
        tableResult = db.table('rbTempInvalidResult')
        record = db.getRecordEx(tableResult, [tableResult['id']], [tableResult['state'].eq(CTempInvalidState.opened)], tableResult['id'].name())
        resultId = forceRef(record.value('id')) if record else None
        self.cmbResult.setValue(resultId)
        if not placeRegistry:
            if type:
                tableReason = db.table('rbTempInvalidReason')
                record = db.getRecordEx(tableReason, [tableReason['id']], [tableReason['code'].eq('09'), tableReason['grouping'].eq(1)], tableReason['id'].name())
                reasonId = forceRef(record.value('id')) if record else None
                self.cmbReason.setValue(reasonId)
        if len(self.modelDocuments.items()) > 0:
            self.tblDocuments.setCurrentRow(0)
        if self.docCode != '2' and QtGui.qApp.tempInvalidRequestFss() and QtGui.qApp.isCspDefined() and QtGui.qApp.getCurrentOrgOgrn():
            self.on_btnRequestFss_clicked()


    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        record.setValue('type', toVariant(self.type_))
        getRBComboBoxValue(self.cmbDoctype, record, 'doctype_id')
        getRBComboBoxValue(self.cmbReason,  record, 'tempInvalidReason_id')
        getRBComboBoxValue(self.cmbChangedReason,  record, 'tempInvalidChangedReason_id')
        getRBComboBoxValue(self.cmbExtraReason,  record, 'tempInvalidExtraReason_id')
        getLineEditValue(self.edtNumberPermit, record, 'numberPermit')
        getDateEditValue(self.edtBegDatePermit, record, 'begDatePermit')
        getDateEditValue(self.edtEndDatePermit, record, 'endDatePermit')
        getRBComboBoxValue(self.cmbBreak,  record, 'break_id')
        getDateEditValue(self.edtBreakDate, record, 'breakDate')
        getDateEditValue(self.edtBegDateStationary, record, 'begDateStationary')
        getDateEditValue(self.edtEndDateStationary, record, 'endDateStationary')
        getRBComboBoxValue(self.cmbDisability,  record, 'disability_id')
        getRBComboBoxValue(self.cmbResult,  record, 'result_id')
        getDateEditValue(self.edtResultDate, record, 'resultDate')
        getDateEditValue(self.edtResultOtherwiseDate, record, 'resultOtherwiseDate')
        getComboBoxValue(self.cmbOtherSex,  record, 'sex')
        getSpinBoxValue(self.edtOtherAge,   record, 'age')
        getCheckBoxValue(self.chkInsuranceOfficeMark,  record, 'insuranceOfficeMark')
        getLineEditValue(self.edtOGRN, record, 'OGRN')
        getRBComboBoxValue(self.cmbTypeEducationalInstitution, record, 'institution_id')
        getLineEditValue(self.edtInfContact, record, 'inf_contact')
        fullLength, externalLength = self.modelPeriods.calcLengths()
        record.setValue('begDate',  toVariant(self.modelPeriods.begDate()))
        record.setValue('endDate',  toVariant(self.modelPeriods.endDate()))
        record.setValue('duration', toVariant(fullLength))
        record.setValue('client_id', toVariant(self.cmbReceiver.value()))
        date = self.modelPeriods.endDate()
        if not date:
            date = self.modelPeriods.begDate()
        diagnosisTypeId = 1 #diagnosisType = закл
        diagnosis = getDiagnosisId2(date, self.modelPeriods.lastPerson(), self.clientId, diagnosisTypeId, unicode(self.edtDiagnosis.text()), u'', self.cmbDiseaseCharacter.value(), None, None)
        record.setValue('diagnosis_id', toVariant(diagnosis[0]))
        if self.prolonging or self.state == CTempInvalidState.extended:
            state = CTempInvalidState.extended
        else:
            state = self.getTempInvalidState()
        record.setValue('state',  state)
        record.setValue('prev_id', toVariant(self.prevId))
        record.setValue('event_id', toVariant(self.cmbEvent.value()))
        record.setValue('mseDate', toVariant(self.edtMseDate.date()))
        record.setValue('person_id', toVariant(self.modelPeriods.lastPerson()))
        if not self.edtCaseBegDate.date():
            self.edtCaseBegDate.setDate(self.modelPeriods.begDate())
        record.setValue('caseBegDate', toVariant(self.edtCaseBegDate.date()))
        record.setValue('accountPregnancyTo12Weeks', toVariant(self.cmbAccountPregnancyTo12Weeks.currentIndex()))
        self.saveProlonging = False
        return record


    def getMKBs(self):
        return unicode(self.edtDiagnosis.text()), '', self.cmbDiseaseCharacter.value()
    
    
    def newPatronageRecord(self, data):
        self.modelCare.newRecord(data)


def getEventListByDates(context, clientId, begDate, endDate):
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


class CTempInvalidCareRegistry:
    def __init__(self):
        self.items = []


    def load(self, tempInvalidDocumentId):
        db = QtGui.qApp.db
        table = db.table('TempInvalidDocument_Care')
        self.items = db.getRecordList(table,'*',table['master_id'].eq(tempInvalidDocumentId))


    def save(self, tempInvalidDocumentId):
        db = QtGui.qApp.db
        table = db.table('TempInvalidDocument_Care')
        idList = []
        for idx, record in enumerate(self.items):
            record.setValue('idx', toVariant(idx))
            record.setValue('master_id', toVariant(tempInvalidDocumentId))
            id = db.insertOrUpdate(table, record)
            idList.append(id)
        oldIdList = db.getDistinctIdList(table,[table['id']], [table['master_id'].eq(tempInvalidDocumentId)])
        db.deleteRecord(table, db.joinAnd([ table['master_id'].eq(tempInvalidDocumentId), table['id'].notInlist(idList), table['id'].inlist(oldIdList)]))


    def getItems(self):
        return self.items


    def setItems(self, items):
        self.items = items


class CSignatureRegistry:
    def __init__(self):
        self._mapSubjectToSignature = {}


    def __nonzero__(self):
        return bool(self._mapSubjectToSignature)

    @staticmethod
    def periodSubject(periodIndex):
        return 'D%d' % periodIndex


    @staticmethod
    def fullPeriodSubject(periodIndex):
        return 'C%d' % periodIndex


    @staticmethod
    def breachSubject():
        return 'B'


    @staticmethod
    def resultSubject():
        return 'R'


    def present(self, subject):
        return subject in self._mapSubjectToSignature


    def appendRecord(self, record):
        subject = forceString(record.value('subject'))
        self._mapSubjectToSignature[subject] = record


    @staticmethod
    def newRecord(subject, dataXml, securityXml, begDate, endDate, certName):
        db = QtGui.qApp.db
        table = db.table('TempInvalidDocument_Signature')
        record = table.newRecord()
        record.setValue('subject', subject)
        record.setValue('dataXml', dataXml)
        record.setValue('securityXml', securityXml)
        record.setValue('begDate', begDate)
        record.setValue('endDate', endDate)
        record.setValue('signDatetime',  QDateTime.currentDateTime())
        record.setValue('signPerson_id', QtGui.qApp.userId)
        record.setValue('signOwner', certName)
        return record


    def records(self):
        return self._mapSubjectToSignature.values()


    def append(self, subject, dataXml, securityXml, begDate, endDate, certName):
        self._mapSubjectToSignature[subject] = self.newRecord(subject, dataXml, securityXml, begDate, endDate, certName)


    def remove(self, subject):
        if subject in self._mapSubjectToSignature:
            del self._mapSubjectToSignature[subject]


    def getDataXml(self, subject):
        record = self._mapSubjectToSignature.get(subject)
        if record:
            return forceString(record.value('dataXml'))
        return None


    def getSignDatetime(self, subject):
        record = self._mapSubjectToSignature.get(subject)
        if record:
            return forceDateTime(record.value('signDatetime')) or None
        return None


    def getSignPersonId(self, subject):
        record = self._mapSubjectToSignature.get(subject)
        if record:
            return forceRef(record.value('signPerson_id'))
        return None

    def getSignOwner(self, subject):
        record = self._mapSubjectToSignature.get(subject)
        if record:
            return forceString(record.value('signOwner'))
        return None


    def load(self, tempInvalidDocumentId):
        db = QtGui.qApp.db
        table = db.table('TempInvalidDocument_Signature')
        for record in db.getRecordList(table,
                                       '*',
                                       table['master_id'].eq(tempInvalidDocumentId)
                                      ):
            self.appendRecord(record)


    def save(self, tempInvalidDocumentId):
        db = QtGui.qApp.db
        table = db.table('TempInvalidDocument_Signature')
        idList = []
        for record in self._mapSubjectToSignature.itervalues():
            record.setValue('master_id',  tempInvalidDocumentId)
            id = db.insertOrUpdate(table, record)
            idList.append(id)
        db.deleteRecord(table, db.joinAnd([ table['master_id'].eq(tempInvalidDocumentId),
                                            table['id'].notInlist(idList)
                                          ]
                                         )
                       )


class CTempInvalidDocumentsModel(CInDocTableModel):
    class CLocDocumentColumn(CInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.recordCache = params.get('documentCaches', [])

        def toString(self, val, record):
            documentId  = forceRef(val)
            if documentId and self.recordCache:
                documentRecord = self.recordCache.get(documentId) if documentId else None
                if documentRecord:
                    if not forceInt(documentRecord.value('deleted')):
                        issueDate = forceString(documentRecord.value('issueDate'))
                        name = forceString(documentRecord.value('serial')) + u'-' + forceString(documentRecord.value('number')) + u', ' + forceString(documentRecord.value('placeWork')) + u', ' + issueDate
                        return toVariant(name)
            return QVariant()


    class CPlaceWorkInDocTableCol(CSelectStrInDocTableCol):
        def __init__(self, title, fieldName, width, values, **params):
            CSelectStrInDocTableCol.__init__(self, title, fieldName, width, values, **params)
            self.values = values

        def toString(self, val, record):
            str = forceStringEx(val).lower()
            for item in self.values:
                if trim(item.lower()) == str:
                    return toVariant(item)
            if str:
                self.values.append(forceString(val))
            return toVariant(val)

        def createEditor(self, parent):
            editor = CROEditableComboBox(parent)
            for val in self.values:
                editor.addItem(val)
            return editor

        def setValues(self, values):
            self.values = values

    class CIssueDateInDocTableCol(CDateInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CDateInDocTableCol.__init__(self, title, fieldName, width, **params)

        def createEditor(self, parent):
            editor = CDateEdit(parent)
            editor.setHighlightRedDate(self.highlightRedDate)
            editor.canBeEmpty(self.canBeEmpty)
            if not QtGui.qApp.userHasRight(urEditIssueDateTempInvalid):
                currentDate = QDate.currentDate()
                editor.setMinimumDate(currentDate.addDays(-1))
            return editor

        def getEditorData(self, editor):
            d = QDate.fromString(editor.text(), 'dd.MM.yyyy')
            if d.isValid() and not QtGui.qApp.userHasRight(urEditIssueDateTempInvalid):
                currentDate = QDate.currentDate()
                if d < currentDate.addDays(-1):
                    res = QtGui.QMessageBox.warning(None,
                                                    u'Внимание!',
                                                    u'Отсутствует право редактировать дату выдачи документа ВУТ более чем на 1 день!',
                                                    QtGui.QMessageBox.Ok,
                                                    QtGui.QMessageBox.Ok)
            value = editor.date()
            if value.isValid():
                return toVariant(value)
            elif self.canBeEmpty:
                return QVariant()
            else:
                return QVariant(QDate.currentDate())

    Col_IsExternal      = 0
    Col_Electronic      = 1
    Col_IssueDate       = 2
    Col_Serial          = 3
    Col_Number          = 4
    Col_Duplicate       = 5
    Col_DuplicateReason = 6
    Col_Busyness        = 7
    Col_PlaceWork       = 8
    Col_PrevNumber      = 9
    Col_PrevId          = 10
    Col_IssuePersonId   = 11
    Col_ExecPersonId    = 12
    Col_LastId          = 13
    Col_Note            = 14
    Col_AnnulmentReason = 15

    def __init__(self, parent, clientCache):
        CInDocTableModel.__init__(self, 'TempInvalidDocument', 'id', 'master_id', parent)
        self.issuePersonCol = CActionPersonFind(u'Выдал',                               'person_id',       20, 'vrbPersonWithSpecialityAndOrgStr')
        self.execPersonCol  = CActionPersonFind(u'Закрыл',                              'execPerson_id',   20, 'vrbPersonWithSpecialityAndOrgStr')
        db = QtGui.qApp.db
        documentCaches = CTableRecordCache(db, db.forceTable('TempInvalidDocument'), u'*', capacity=None)
        self.addCol(CBoolInDocTableCol(     u'Внешний',                             'isExternal',      3                                                  ))
        self.addCol(CBoolInDocTableCol(     u'Э',                                   'electronic',      3                                                  ).setToolTip(u'Электронный'))
        self.addCol(CTempInvalidDocumentsModel.CIssueDateInDocTableCol(     u'Дата выдачи',            'issueDate', 10))
        self.addCol(CInDocTableCol(         u'Серия',                               'serial',          22                                                 ))
        self.addCol(CInDocTableCol(         u'Номер',                               'number',          22,  maxLength=12, inputMask='999999999999;'       ))
        self.addCol(CBoolInDocTableCol(     u'Д',                                   'duplicate',       3                                                  ).setToolTip(u'Дубликат')).setReadOnly(True)
        self.addCol(CRBInDocTableCol(       u'Причина выдачи дубликата',            'duplicateReason_id',  10, 'rbTempInvalidDuplicateReason'             ))
        self.addCol(CEnumInDocTableCol(     u'Занятость',                           'busyness',        4,  [u'', u'основное', u'совместитель', u'на учете']))
        self.addCol(CTempInvalidDocumentsModel.CPlaceWorkInDocTableCol(u'Место работы','placeWork',    10, []                                             ))
        self.addCol(CInDocTableCol(         u'ПДН',                                 'prevNumber',      10                                                 ).setToolTip(u'Продолжение документа с номером'))
        self.addCol(CTempInvalidDocumentsModel.CLocDocumentColumn(u'ИПД',           'prev_id',         10, documentCaches=documentCaches).setToolTip(u'Идентификатор продолжения документа')).setReadOnly(True)
        self.addCol(self.issuePersonCol)
        self.addCol(self.execPersonCol)
        self.addCol(CTempInvalidDocumentsModel.CLocDocumentColumn(u'ИВД',           'last_id', 10, documentCaches=documentCaches).setToolTip(u'Идентификатор выданного документа')).setReadOnly(True)
        self.addCol(CInDocTableCol(         u'Примечание',                          'note',            10                                                 ))
        self.addCol(CRBInDocTableCol(       u'Причина аннулирования',               'annulmentReason_id',  10, 'rbTempInvalidAnnulmentReason'             ))
        self.addHiddenCol('fssStatus')

        self.eventEditor = None
        self.readOnly = False
        self.tempInvalidId = None
        self.clientId = None
        self.tempInvalidPrevId = None
        self.tempInvalidLastId = None
        self.blankIdList = []
        self.numberBlankList = {}
        self.isEnabledPatient = True
        userId = QtGui.qApp.userId
        self.chairUser = forceBool(db.translate('Person', 'id', userId, 'chairPerson')) if userId else False
        self.type = None
        self.docCode = None
        self.clientCache = clientCache
        self.documentsSignatures = {}
        self.documentsSignatureR = False
        self.documentsSignatureExternalR = False
        self.isAnnulledDublicate = False


    def initAnnulledDublicate(self):
        if not self.isAnnulledDublicate and self.tempInvalidId:
            db = QtGui.qApp.db
            tableTempInvalid = db.table('TempInvalid')
            record = db.getRecordEx(tableTempInvalid, [tableTempInvalid['prev_id']], [tableTempInvalid['id'].eq(self.tempInvalidId), tableTempInvalid['deleted'].eq(0)])
            prevTempInvalidId = forceRef(record.value('prev_id')) if record else None
            if prevTempInvalidId:
                tableTIR = db.table('rbTempInvalidResult')
                queryTable = tableTempInvalid.innerJoin(tableTIR, tableTIR['id'].eq(tableTempInvalid['result_id']))
                cols = [tableTempInvalid['state']]
                cond = [tableTempInvalid['deleted'].eq(0),
                        tableTempInvalid['id'].eq(prevTempInvalidId)
                        ]
                record = db.getRecordEx(queryTable, cols, cond)
                self.isAnnulledDublicate = (forceInt(record.value('state')) == CTempInvalidState.annulled) if record else False


    def setAnnulledDublicate(self, isAnnulledDublicate):
        self.isAnnulledDublicate = isAnnulledDublicate


    def setDocumentsSignatures(self, documentsSignatures, documentsSignatureR, documentsSignatureExternalR):
        self.documentsSignatures = documentsSignatures
        self.documentsSignatureR = documentsSignatureR
        self.documentsSignatureExternalR = documentsSignatureExternalR


    def getEmptyRecord(self):
        result = CInDocTableModel.getEmptyRecord(self)
        result.append(QtSql.QSqlField('prevDuplicate_id', QVariant.Int))
        if QtGui.qApp.userSpecialityId:
            result.setValue('person_id', toVariant(QtGui.qApp.userId))
            if forceBool(result.value('duplicate')):
                result.setValue('execPerson_id', toVariant(QtGui.qApp.userId))
        result.signatures = CSignatureRegistry()
        result.tempInvalidCare = CTempInvalidCareRegistry()
        return result


    def setType(self, type_):
        self.type = type_
        if self.type == CTempInvalidEditDialog.Disability:
            self.cols()[CTempInvalidDocumentsModel.Col_Number].setInputMask('9'*64)
            self.cols()[CTempInvalidDocumentsModel.Col_Number].setMaxLength(64)
        else:
            if self.docCode == CTempInvalidEditDialog.InabilitySheet:
                self.cols()[CTempInvalidDocumentsModel.Col_Number].setInputMask('999999999999;')
            elif self.docCode == CTempInvalidEditDialog.MedicalCertificate:
                self.cols()[CTempInvalidDocumentsModel.Col_Number].setInputMask('')
        self.cols()[CTempInvalidDocumentsModel.Col_PrevNumber].setInputMask('999999999999;')


    def setPlaceWorkValues(self, values):
        self.cols()[CTempInvalidDocumentsModel.Col_PlaceWork].setValues(values)


    def setDocCode(self, docCode):
        self.docCode = docCode
        if self.type == CTempInvalidEditDialog.TempInvalid and self.docCode == CTempInvalidEditDialog.InabilitySheet:
            self.eventEditor.tblDocuments.enableColHide(CTempInvalidDocumentsModel.Col_Serial)
        else:
            self.eventEditor.tblDocuments.showColHide(CTempInvalidDocumentsModel.Col_Serial)
        self.setType(self.type)


    def setEnabledPatient(self, otherPersonEnabled, rightRegWriteInsurOfficeMark, checkedInsuranceOfficeMark, isReasonPrimary):
        enable = rightRegWriteInsurOfficeMark if checkedInsuranceOfficeMark else True
        self.isEnabledPatient = bool(otherPersonEnabled and enable)
        if not otherPersonEnabled and enable and not isReasonPrimary:
            pass


    def setReadOnly(self, value):
        self.readOnly = value


    def cellReadOnly(self, index):
        column = index.column()
        row = index.row()
        if self.documentsSignatureR:
            return True
        if self.documentsSignatureExternalR:
            if 0 <= row < len(self._items):
                record = self._items[row]
                documentId = forceRef(record.value('id'))
                documentsSignature = self.documentsSignatures.get(documentId, {})
                if documentsSignature.get(u'REx', False) or documentsSignature.get(u'R', False):
                    return True
        if self.documentsSignatures:
            if 0 <= row < len(self._items):
                record = self._items[row]
                documentId = forceRef(record.value('id'))
                documentsSignaturesDict = self.documentsSignatures.get(documentId, {})
                documentsSignaturesLineC = documentsSignaturesDict.get(u'C', [])
                if documentsSignaturesLineC and 0 in documentsSignaturesLineC and column != CTempInvalidDocumentsModel.Col_ExecPersonId:
                    return True
                else:
                    documentsSignaturesLineD = documentsSignaturesDict.get(u'D', [])
                    if documentsSignaturesLineD and 0 in documentsSignaturesLineD and column != CTempInvalidDocumentsModel.Col_ExecPersonId:
                        return True
        if 0 <= row < len(self._items):
            record = self._items[row]
            isExternal = forceBool(record.value('isExternal'))
            if isExternal:
                if column in (CTempInvalidDocumentsModel.Col_Duplicate,
                              CTempInvalidDocumentsModel.Col_DuplicateReason,
                              CTempInvalidDocumentsModel.Col_AnnulmentReason
                             ):
                    return True
            else:
                if forceBool(record.value('electronic')):
                    if column == CTempInvalidDocumentsModel.Col_AnnulmentReason:
                        return True
                    if not (self.eventEditor and self.eventEditor.getTempInvalidState() == CTempInvalidState.closed
                    and not self.eventEditor.itemId() and not self.eventEditor.prevId) and column in (CTempInvalidDocumentsModel.Col_Serial,
                                                                                                      CTempInvalidDocumentsModel.Col_Number):
                        return True
                if forceBool(record.value('duplicate')):
                    if not self.isAnnulledDublicate and column in (CTempInvalidDocumentsModel.Col_Electronic,
                                                                   CTempInvalidDocumentsModel.Col_Duplicate,
                                                                   CTempInvalidDocumentsModel.Col_Busyness,
                                                                   CTempInvalidDocumentsModel.Col_PlaceWork,
                                                                   CTempInvalidDocumentsModel.Col_PrevNumber,
                                                                   CTempInvalidDocumentsModel.Col_PrevId,
                                                                   CTempInvalidDocumentsModel.Col_LastId,
                                                                   CTempInvalidDocumentsModel.Col_Note):
                        return True
                    elif self.isAnnulledDublicate and column in (CTempInvalidDocumentsModel.Col_Electronic,
                                                                 CTempInvalidDocumentsModel.Col_Duplicate,
                                                                 CTempInvalidDocumentsModel.Col_PrevNumber,
                                                                 CTempInvalidDocumentsModel.Col_PrevId,
                                                                 CTempInvalidDocumentsModel.Col_LastId,
                                                                 CTempInvalidDocumentsModel.Col_Note):
                        return True
                if forceRef(record.value('annulmentReason_id')):
                   return True
                if record.signatures and column in ( CTempInvalidDocumentsModel.Col_Electronic,
                                                     CTempInvalidDocumentsModel.Col_IssueDate,
                                                     CTempInvalidDocumentsModel.Col_Serial,
                                                     CTempInvalidDocumentsModel.Col_Number):
                    return True
                if column == CTempInvalidDocumentsModel.Col_PlaceWork and forceInt(self._items[row].value('busyness')) == 3:
                    return True
                if column == CTempInvalidDocumentsModel.Col_PrevNumber and forceRef(self._items[row].value('prev_id')):
                    return True
                if column == CTempInvalidDocumentsModel.Col_Electronic and forceBool(record.value('electronic')):
                    idxZero = None
                    idxOne = None
                    for rowS, item in enumerate(self._items):
                        if forceInt(item.value('idx')) == 0 and not idxZero:
                            idxZero = item
                        idxOne = record
                        if idxOne and idxZero:
                            if not forceInt(idxOne.value('prevNumber')) and forceInt(idxOne.value('prevNumber')) != forceInt(idxZero.value('number')):
                                return False  
                            else:
                                return True
        elif column not in ( CTempInvalidDocumentsModel.Col_IsExternal,
                             CTempInvalidDocumentsModel.Col_Electronic,
                             CTempInvalidDocumentsModel.Col_IssueDate,
                             CTempInvalidDocumentsModel.Col_Serial,
                             CTempInvalidDocumentsModel.Col_Number):
                return True
        return False


    def flags(self, index):
        if self.readOnly:
           return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return CInDocTableModel.flags(self, index)


    def setClientId(self, clientId):
        self.clientId = clientId


    def setTempInvalidId(self, tempInvalidId):
        self.tempInvalidId = tempInvalidId


    def getTempInvalidId(self):
        return self.tempInvalidId


    def setTempInvalidPrevId(self, tempInvalidPrevId):
        self.tempInvalidPrevId = tempInvalidPrevId


    def getTempInvalidPrevId(self):
        return self.tempInvalidPrevId


    def setTempInvalidLastId(self, tempInvalidLastId):
        self.tempInvalidLastId = tempInvalidLastId


    def getTempInvalidLastId(self):
        return self.tempInvalidLastId


    def getTempInvalidDocumentIdList(self):
        idList = []
        for item in self._items:
            id = forceRef(item.value('id'))
            if id and id not in idList:
                idList.append(id)
        return idList


    def data(self, index, role=Qt.DisplayRole):
        result = CInDocTableModel.data(self, index, role)
        if role == Qt.FontRole:
            row = index.row()
            if 0 <= row < len(self._items):
                annulmentReasonId = forceRef(self._items[row].value('annulmentReason_id'))
                if annulmentReasonId:
                    font = QtGui.QFont(result) if result and result.type() == QVariant.Font else QtGui.QFont()
                    font.setStrikeOut(True)
                    result = QVariant(font)
        return result


    def setData(self, index, value, role=Qt.EditRole):
        row = index.row()
        column = index.column()
        if self.type == CTempInvalidEditDialog.Disability:
            if row >= 1:
                return False

        if ( column in ( CTempInvalidDocumentsModel.Col_Electronic,
                         CTempInvalidDocumentsModel.Col_Serial,
                         CTempInvalidDocumentsModel.Col_Number)
              and 0<=row<len(self._items)
              and self._items[row].signatures
           ):
            return False

        result = CInDocTableModel.setData(self, index, value, role)
        if result:
            self.setValue(row, 'idx', row)
            isExternal = forceBool(self.value(row, 'isExternal'))
            if not isExternal:
                if column == CTempInvalidDocumentsModel.Col_Electronic:
                    electronic = forceBool(value)
                    if not (self.eventEditor and self.eventEditor.getTempInvalidState() == CTempInvalidState.closed and not self.eventEditor.itemId() and not self.eventEditor.prevId):
                        if electronic:
                                ok, number = QtGui.qApp.call(None, acquireElectronicTempInvalidNumber)
                                if ok:
                                    self.setValue(row, 'serial', '')
                                    self.setValue(row, 'number', number)
                                else:
                                    self.setValue(row, 'electronic', 'False')
                        else:
                            number = forceStringEx(self.value(row, 'number'))
                            self.setValue(row, 'serial', '')
                            self.setValue(row, 'number', '')
                            if number:
                                releaseElectronicTempInvalidNumber(number)
                    elif not electronic:
                        self.setValue(row, 'serial', '')
                        self.setValue(row, 'number', '')

            if column == CTempInvalidDocumentsModel.Col_Busyness: # Занятость
                busyness = forceInt(value)
                placeWork = forceStringEx(self.value(row, 'placeWork'))
                if busyness == 3:
                    self.setValue(row, 'placeWork', None)
                if self.clientId and not placeWork and (busyness == 0 or busyness == 1):
                    work = formatWorkTempInvalid(getClientWork(self.clientId))
                    if work:
                        self.setValue(row, 'placeWork', toVariant(trim(work)))
                        self.updatePlaceWork(row, toVariant(work))
                        self.setValue(row, 'busyness', toVariant(1))
                    else:
                        self.setValue(row, 'busyness', value)
                else:
                    self.setValue(row, 'busyness', value)
            elif column == CTempInvalidDocumentsModel.Col_PlaceWork: # Место работы
                val = forceStringEx(value)
                self.setValue(row, 'placeWork', toVariant(val))
                self.updatePlaceWork(row, val)
        return result


    def updatePlaceWork(self, row, value):
        newRow = row + 1
        duplicate = True
        while duplicate:
            if newRow >= 0 and newRow < len(self._items):
                duplicate = forceBool(self._items[newRow].value('duplicate'))
                if duplicate:
                    self._items[newRow].setValue('placeWork', QVariant(value))
            else:
                duplicate = False
            newRow += 1


    def loadItems(self, tempInvalidId, clientId, tempInvalidPrevId, tempInvalidLastId):
        self.tempInvalidId = tempInvalidId
        self.clientId = clientId
        self.tempInvalidPrevId = tempInvalidPrevId
        self.tempInvalidLastId = tempInvalidLastId
        CInDocTableModel.loadItems(self, tempInvalidId)
        self.initAnnulledDublicate()
        for item in self._items:
            item.signatures = CSignatureRegistry()
            item.signatures.load(forceRef(item.value('id')))
            item.tempInvalidCare = CTempInvalidCareRegistry()
            item.tempInvalidCare.load(forceRef(item.value('id')))


    def saveItems(self, masterId, newProlonging = False):
        if self._items is not None:
            for item in self._items:
                item._dirty = True
            CInDocTableModel.saveItems(self, masterId)
            db = QtGui.qApp.db
            table = self._table
            for idx, item in enumerate(self._items):
                id = forceRef(item.value('id'))
                lastId = forceRef(item.value('last_id'))
                prevId = forceRef(item.value('prev_id'))
                duplicate = forceBool(item.value('duplicate'))
                isExternal = forceBool(item.value('isExternal'))
                number = forceString(item.value('number'))
                if isExternal and number:
                    db.updateRecords(table, table['prev_id'].eq(id), [table['prevNumber'].eq(number), table['deleted'].eq(0)])
                if prevId and id: #and not duplicate:
                    db.updateRecords(table, table['last_id'].eq(id), [table['id'].eq(prevId), table['deleted'].eq(0)])
                    if newProlonging:
                        personId = forceRef(item.value('person_id'))
                        if personId:
                            db.updateRecords(table, table['execPerson_id'].eq(personId), [table['id'].eq(prevId), table['deleted'].eq(0), table['execPerson_id'].ne(personId)])
                if duplicate:
                    prevIdx = idx-1
                    if prevIdx >= 0 and prevIdx < len(self._items):
                        prevDuplicateId = forceRef(self._items[prevIdx].value('id'))
                        db.updateRecords(table, table['prevDuplicate_id'].eq(toVariant(prevDuplicateId)), [table['id'].eq(id), table['deleted'].eq(0)])
                if lastId:
                    record = db.getRecordEx(table, '*', [table['id'].eq(lastId), table['deleted'].eq(0), db.joinOr([table['prev_id'].isNull(), table['prev_id'].ne(id)])])
                    if record:
                        if forceRef(record.value('prev_id')) != id:
                            record.setValue('prev_id', toVariant(id))
                            record.setValue('prevNumber', item.value('number'))
                            db.updateRecord(table, record)
                item.signatures.save(forceRef(item.value('id')))
                item.tempInvalidCare.save(forceRef(item.value('id')))


    def setEventEditor(self, eventEditor):
        # self.issuePersonCol.setEventEditor(eventEditor)
        # self.execPersonCol.setEventEditor(eventEditor)
        self.eventEditor = eventEditor


    def setTempInvalidClientId(self, clientId):
        self.clientId = clientId


    def getTempInvalidClientId(self):
        return self.clientId


    def findNextDocumentNumber(self, number):
        for document in self._items:
            if (    not forceRef(document.value('annulmentReason_id'))
                and forceString(document.value('prevNumber')) == number
               ):
                return forceString(document.value('number'))


    def getDocumentsInfo(self, context):
        result = context.getInstance(CTempInvalidDocumentItemInfoList, None)
        for i, item in enumerate(self.items()):
            id = forceRef(item.value('id'))
            result.addItem(id or -i-1, item)
        return result


class CTempInvalidPeriodModel(CInDocTableModel):
    Col_BegDate       = 0
    Col_EndDate       = 1
    Col_Duration      = 2
    Col_ChairPersonId = 4

    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'TempInvalid_Period', 'id', 'master_id', parent)
        self.parent = parent
        self.endPersonCol = CActionPersonFind(              u'Врач',             'endPerson_id',    20, 'vrbPersonWithSpecialityAndOrgStr')
        self.chairPersonCol = CActionPerson(            u'Председатель ВК',  'chairPerson_id',  20, 'vrbPersonWithSpecialityAndOrgStr', filter=u'chairPerson = 1')
        self.addCol(CDateInDocTableCol(                 u'Начало',           'begDate',         10                                          ))
        self.addCol(CDateInDocTableCol(                 u'Окончание',        'endDate',         10                                          ))
        self.addExtCol(CIntInDocTableCol(               u'Дни',              'duration',        10, high=999), QVariant.Int).setReadOnly(not QtGui.qApp.userSpecialityId)
        self.addCol(self.endPersonCol)
        self.chairPersonCol.setFilterAddSpeciality(False)
        self.addCol(self.chairPersonCol)
        self.colRegime = self.addCol(CRBInDocTableCol(  u'Режим',            'regime_id',       10, 'rbTempInvalidRegime', preferredWidth=150))
        self.addCol(CInDocTableCol(                     u'Примечание',       'note',            10                                           ))
        self.addCol(CBoolInDocTableCol(                 u'Внешний',          'isExternal',      3                                            ))
        self.eventEditor = None
        self.readOnly = False
        self.isExternal = False
        self.primary = 0
        self.prolongate = 0
        self.restriction = 0
        self.currentRow = -1
        self.currentDegDate = None
        self.currentEndDate = None
        self.chairPersonCol.setFilter(filter=u'chairPerson = 1')
        userId = QtGui.qApp.userId
        self.chairUser = forceBool(QtGui.qApp.db.translate('Person', 'id', userId, 'chairPerson')) if userId else False
        self.type = None
        self.documentsSignatures = {}
        self.documentsSignatureR = False
        self.documentsSignatureExternalR = False
        self.periodsSignaturesC = {}
        self.periodsSignaturesD = {}


    def setDocumentsSignatures(self, documentsSignatures, documentsSignatureR, documentsSignatureExternalR, periodsSignaturesC, periodsSignaturesD):
        self.documentsSignatures = documentsSignatures
        self.documentsSignatureR = documentsSignatureR
        self.documentsSignatureExternalR = documentsSignatureExternalR
        self.periodsSignaturesC = periodsSignaturesC
        self.periodsSignaturesD = periodsSignaturesD


    def cellReadOnly(self, index):
        column = index.column()
        if self.documentsSignatureR and not (column == CTempInvalidPeriodModel.Col_ChairPersonId and self.chairUser):
            return True
        row = index.row()
        if self.documentsSignatureExternalR:
            if 0 <= row < len(self._items):
                record = self._items[row]
                if forceBool(record.value('isExternal')):
                    return True
                if self.chairUser and column == self.Col_ChairPersonId:
                    return False
        if self.periodsSignaturesC:
            if 0 <= row < len(self._items):
                if self.periodsSignaturesC.get(row, False):
                    return True
                else:
                    record = self._items[row]
                    isExternal = forceBool(record.value('isExternal'))
                    if isExternal:
                        for periodsSignatureC in self.periodsSignaturesC.values():
                            if periodsSignatureC:
                                return True
        if self.periodsSignaturesD:
            if 0 <= row < len(self._items):
                if self.periodsSignaturesD.get(row, False) and column != CTempInvalidPeriodModel.Col_ChairPersonId:
                    return True
                else:
                    record = self._items[row]
                    isExternal = forceBool(record.value('isExternal'))
                    if isExternal:
                        for periodsSignatureD in self.periodsSignaturesD.values():
                            if periodsSignatureD:
                                return True
        if 0 <= row < len(self._items):
            record = self._items[row]
            if record:
                if column == CTempInvalidPeriodModel.Col_ChairPersonId:
                    if self.chairUser:
                        return False
                    return True
            elif column == CTempInvalidPeriodModel.Col_ChairPersonId:
                return True
        elif column == CTempInvalidPeriodModel.Col_ChairPersonId:
            return True
        return False


    def setReadOnly(self, value):
        self.readOnly = value


    def flags(self, index):
        column = index.column()
        if self.readOnly and not (column == CTempInvalidPeriodModel.Col_ChairPersonId and self.chairUser):
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if self.cellReadOnly(index):
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        elif column == CTempInvalidPeriodModel.Col_ChairPersonId and self.chairUser:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
        row = index.row()
        if self.type != CTempInvalidEditDialog.Disability:
            if self.isExternal:
                if row >= 4:
                    return Qt.ItemIsSelectable | Qt.ItemIsEnabled
            elif row >= 3:
                return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        elif row >= 1 and not forceBool(self._items[row-1].value('isExternal')):
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return CInDocTableModel.flags(self, index)


    def setData(self, index, value, role=Qt.EditRole):
        row = index.row()
        column = index.column()
        if self.type != CTempInvalidEditDialog.Disability:
            if self.isExternal:
                if row >= 4:
                    return False
            elif row >= 3:
                return False
        else:
            if row >= 1 and not forceBool(self._items[row-1].value('isExternal')):
                return False
        result = CInDocTableModel.setData(self, index, value, role)
        if result and role == Qt.EditRole:
            if column == 0 or column == 1: # начало или окончание
                begDate = forceDate(self.value(row, 'begDate'))
                endDate = forceDate(self.value(row, 'endDate'))
                duration = self._calcDuration(begDate, endDate, row, column)
                self.setValue(row, 'duration', duration)
            elif column == 2: # длительность
                duration = forceInt(self.value(row, 'duration'))
                if duration > 0:
                    begDate = forceDate(self.value(row, 'begDate'))
                    endDate = forceDate(self.value(row, 'endDate'))
                    if begDate:
                        endDate = begDate.addDays(duration-1)
                        self.setValue(row, 'endDate',  endDate)
                    elif endDate:
                        begDate = endDate.addDays(1-duration)
                        self.setValue(row, 'begDate',  begDate)
                    self._calcDuration(begDate, endDate, row, column)
        if role == Qt.CheckStateRole:
            if column == self.getColIndex('isExternal'): # Внешний = isExternal
                if self.type != CTempInvalidEditDialog.Disability and row >= 1 and forceBool(value):
                    value = toVariant(Qt.Unchecked)
                    self.setValue(row, 'isExternal', value)
                if forceBool(value):
                    self.setValue(row, 'endPerson_id', toVariant(None))
                self.getIsExternal()
        return result


    def getIsExternal(self):
        self.isExternal = False
        for item in self._items:
            self.isExternal = forceBool(item.value('isExternal'))
            if self.isExternal:
                break


    def loadItems(self, masterId):
        CInDocTableModel.loadItems(self, masterId)
        for item in self.items():
            begDate = forceDate(item.value('begDate'))
            endDate = forceDate(item.value('endDate'))
            duration = self._calcDuration(begDate, endDate)
            item.setValue('duration', toVariant(duration))
        self.getIsExternal()


    def setEventEditor(self, eventEditor):
        # self.endPersonCol.setEventEditor(eventEditor)
        self.chairPersonCol.setEventEditor(eventEditor)
        self.eventEditor = eventEditor


    def setReason(self, reasonId):
        if reasonId:
            db = QtGui.qApp.db
            table = db.table('rbTempInvalidReason')
            record = db.getRecordEx(table, [table['primary'], table['prolongate'], table['restriction']], [table['id'].eq(reasonId)])
            if record:
                self.primary = forceInt(record.value('primary'))
                self.prolongate = forceInt(record.value('prolongate'))
                self.restriction = forceInt(record.value('restriction'))


    def setType(self, type_):
        self.type = type_
        filter = 'type=%d' % (type_ if type_ != CTempInvalidEditDialog.Disability else 2)
        self.colRegime.filter = filter


    def getEmptyRecord(self):
        result = CInDocTableModel.getEmptyRecord(self)
        if QtGui.qApp.userSpecialityId:
            result.setValue('endPerson_id', QtGui.qApp.userId)
            # result.setValue('chairPerson_id', QtGui.qApp.userId)
        result.setValue('regime_id', QtGui.qApp.tempInvalidRegime())
        return result


    def _calcDuration(self, begDate, endDate, row = -1, column = -1):
        duration = begDate.daysTo(endDate)+1 if begDate and endDate and begDate <= endDate else 0
        if duration > 0 and row >= 0 and column >= 0:
            items = self.items()
            primary = True
            durationItems = 0
            if self.currentRow != row or self.currentDegDate != begDate or self.currentEndDate != endDate:
                self.currentRow = row
                self.currentDegDate = begDate
                self.currentEndDate = endDate
                for i, item in enumerate(items):
                    if not forceBool(item.value('isExternal')):
                        begDateItem = forceDate(item.value('begDate'))
                        endDateItem = forceDate(item.value('endDate'))
                        durationItems += begDateItem.daysTo(endDateItem)+1 if begDateItem and endDateItem and begDateItem <= endDateItem else 0
                        if row == i:
                            if primary:
                                primary = False
                                if self.primary and duration > self.primary:
                                    self.eventEditor.checkValueMessage(u'Превышена максимальная длительность первичного периода ВУТ в днях (%s).'%(self.primary), True, self.eventEditor.tblPeriods, row, column)
                            else:
                                if self.prolongate and duration > self.prolongate:
                                    self.eventEditor.checkValueMessage(u'Превышена максимальная длительность продления ВУТ в днях (%s).'%(self.prolongate), True, self.eventEditor.tblPeriods, row, column)
                        else:
                            primary = False
                        if self.restriction and durationItems > self.restriction:
                            self.eventEditor.checkValueMessage(u'Превышена максимальная длительность ВУТ, после которого требуется Направление на ВК (%s).'%(self.restriction), True, self.eventEditor.tblPeriods, i, column)
        return duration


    def calcLengths(self):
        internalLength = 0
        externalLength = 0
        for record in self.items():
            isExternal = forceBool(record.value('isExternal'))
            begDate = forceDate(record.value('begDate'))
            endDate = forceDate(record.value('endDate'))
            length = self._calcDuration(begDate, endDate)
            if isExternal:
                externalLength += length
            else:
                internalLength += length
        return internalLength+externalLength, externalLength


    def begDate(self):
        items = self.items()
        if items:
            firstRecord = items[0]
            return forceDate(firstRecord.value('begDate'))
        else:
            return None


    def endDate(self):
        items = self.items()
        if items:
            lastRecord = items[-1]
            return forceDate(lastRecord.value('endDate'))
        else:
            return None


    def lastPerson(self):
        result = None
        items = self.items()
        if items:
            lastRecord = items[-1]
            result = forceRef(lastRecord.value('endPerson_id'))
        return result


    def begDateEndDateFirstExternal(self):
        items = self.items()
        for item in items:
            if forceBool(item.value('isExternal')):
                return forceDate(item.value('begDate')), forceDate(item.value('endDate'))
        else:
            return None, None


    def begDateAfterExternal(self):
        self.isExternal = self.getIsExternal()
        if self.isExternal:
            items = self.items()
            for item in items:
                if not forceBool(item.value('isExternal')):
                    return forceDate(item.value('begDate'))
        else:
            return None


    def endDateAfterExternal(self):
        items = self.items()
        if items:
            lastRecord = items[-1]
            isExternal = forceBool(lastRecord.value('isExternal'))
            return forceDate(lastRecord.value('endDate')) if not isExternal else None
        else:
            return None


    def begDateLast(self):
        items = self.items()
        if items:
            lastRecord = items[-1]
            if not forceBool(lastRecord.value('isExternal')):
                return forceDate(lastRecord.value('begDate'))
        else:
            return None


    def addStart(self, begDate):
        item = self.getEmptyRecord()
        item.setValue('begDate', toVariant(begDate))
        self.items().append(item)
        self.reset()


    def getPeriodsInfo(self, context):
        result = context.getInstance(CTempInvalidPeriodInfoList, None)
        for i, item in enumerate(self.items()):
            itemCopy = QtSql.QSqlRecord(item)
            isSigned = QtSql.QSqlField('isSigned', QVariant.Bool)
            signDatetime = QtSql.QSqlField('signDatetime', QVariant.DateTime)
            signPersonId = QtSql.QSqlField('signPerson_id', QVariant.Int)

            for document in self.parent.modelDocuments.items():
                for record in document.signatures.records():
                    begDate = forceDate(record.value('begDate'))
                    endDate = forceDate(record.value('endDate'))
                    if begDate == forceDate(item.value('begDate')) and endDate == forceDate(item.value('endDate')):
                        isSigned.setValue(True)
                        signDatetime.setValue(forceDateTime(record.value('signDatetime')))
                        signPersonId.setValue(forceRef(record.value('signPerson_id')))

            itemCopy.append(isSigned)
            itemCopy.append(signDatetime)
            itemCopy.append(signPersonId)

            id = forceRef(itemCopy.value('id'))
            result.addItem(id or -i-1, itemCopy)
        return result


class CActionPerson(CRBInDocTableCol):
    def __init__(self, title, fieldName, width, tableName, **params):
        CRBInDocTableCol.__init__(self, title, fieldName, width, tableName, **params)
        self.eventEditor = None
        self.filterLoc = u''
        self.isFilterAddSpeciality = True


    def setFilterAddSpeciality(self, value):
        self.isFilterAddSpeciality = value


    def setFilter(self, filter):
        self.filterLoc = filter


    def setEventEditor(self, eventEditor):
        self.eventEditor = eventEditor


    def setEditorData(self, editor, value, record):
        filterRetired = u''
        if self.eventEditor is not None:
            orgId = self.eventEditor.orgId
            begDate = forceDate(record.value('begDate'))
            endDate = forceDate(record.value('endDate'))
            filterDate = None
            if endDate:
                filterDate = u'DATE(retireDate) > DATE(%s)'%QtGui.qApp.db.formatDate(endDate)
            elif begDate:
                filterDate = u'DATE(retireDate) > DATE(%s)'%QtGui.qApp.db.formatDate(begDate)
            filterRetired = u' AND (retireDate IS NULL %s)'%((u' OR (%s)'%filterDate) if filterDate else u'')
        else:
            orgId = QtGui.qApp.currentOrgId()
        if self.isFilterAddSpeciality:
            filter = 'speciality_id IS NOT NULL AND org_id=\'%s\' %s' % (orgId, filterRetired)
        else:
            filter = 'org_id=\'%s\' %s' % (orgId, filterRetired)
        if self.filterLoc:
            filter += u' AND ' + self.filterLoc
        editor.setTable(self.tableName, self.addNone, filter,'name')
        editor.setShowFields(self.showFields)
        editor.setValue(forceInt(value))


class CActionPersonFind(CPersonFindInDocTableCol):
    def __init__(self, title, fieldName, width, tableName, **params):
        CPersonFindInDocTableCol.__init__(self, title, fieldName, width, tableName, **params)

    def setEditorData(self, editor, value, record):
        begDate = forceDate(record.value('begDate'))
        issueDate = forceDate(record.value('issueDate'))
        if begDate:
            editor.setBegDate(begDate)
        else:
            editor.setBegDate(issueDate)
        editor.setValue(forceInt(value))


def requiredOtherPerson(tempInvalidReasonId):
    grouping = forceInt(QtGui.qApp.db.translate('rbTempInvalidReason', 'id', tempInvalidReasonId, 'grouping'))
    return grouping == 1


def requiredPregnancyAndBirth(tempInvalidReasonId):
    grouping = forceInt(QtGui.qApp.db.translate('rbTempInvalidReason', 'id', tempInvalidReasonId, 'grouping'))
    return grouping == 2


def requiredDiagnosis(tempInvalidReasonId):
    return forceBool(QtGui.qApp.db.translate('rbTempInvalidReason', 'id', tempInvalidReasonId, 'requiredDiagnosis'))


def formatWorkTempInvalid(workRecord):
    if workRecord:
        orgId = forceRef(workRecord.value('org_id'))
        if orgId:
            orgShortName = getOrganisationShortName(orgId)
        else:
            orgShortName = forceString(workRecord.value('freeInput'))
    else:
        orgShortName = ''
    return orgShortName


from Events.Ui_TempInvalidDocumentProlongDialog import Ui_TempInvalidDocumentProlongDialog


class CTempInvalidDocumentProlongDialog(CDialogBase, CRecordLockMixin, Ui_TempInvalidDocumentProlongDialog):
    def __init__(self,  parent, clientCache, items):
        CDialogBase.__init__(self, parent)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        CRecordLockMixin.__init__(self)
        self.addObject('modelDocuments', CTempInvalidDocumentsProlongModel(self, clientCache))
        self.setupUi(self)
        self.setWindowTitleEx(u'Продлить документы временной нетрудоспособности')
        self.setWindowState(Qt.WindowMaximized)
        self.tblDocuments.setModel(self.modelDocuments)
        self.clientCache = clientCache
        self.modelDocuments.setEventEditor(self)
        self.setupDirtyCather()
        self.modelDocuments.setIncludeItems(items)
        self.tblDocuments.enableColHide(CTempInvalidDocumentsProlongModel.Col_Serial)


    def getItems(self):
        return self.modelDocuments.items()


class CTempInvalidDocumentsProlongModel(CTempInvalidDocumentsModel):

    Col_Include        = 0
    Col_Electronic     = 1
    Col_IssueDate      = 2
    Col_Serial         = 3
    Col_Number         = 4
    Col_Duplicate      = 5
    Col_DuplicateReason= 6
    Col_Busyness       = 7
    Col_PlaceWork      = 8
    Col_PrevNumber     = 9
    Col_PrevId         = 10
    Col_IssuePersonId  = 11
    Col_ExecPersonId   = 12
    Col_ChairPersonId  = 13
    Col_LastId         = 14
    Col_Note           = 15

    def __init__(self, parent, clientCache):
        CTempInvalidDocumentsModel.__init__(self, parent, clientCache)
        self.addExtCol(CBoolInDocTableCol(u'Включить', 'include', 10), QVariant.Int, idx=0)


    def cellReadOnly(self, index):
        if index.column() == CTempInvalidDocumentsProlongModel.Col_Include:
            return False
        return True


    def flags(self, index):
        if self.readOnly:
           return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if index.column() == CTempInvalidDocumentsProlongModel.Col_Include:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsUserCheckable
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled


    def getEmptyRecord(self):
        result = CTempInvalidDocumentsModel.getEmptyRecord(self)
        result.append(QtSql.QSqlField('include', QVariant.Int))
        result.tempInvalidCare = CTempInvalidCareRegistry()
        return result


    def setData(self, index, value, role=Qt.EditRole):
        row = index.row()
        column = index.column()
        if self.type == CTempInvalidEditDialog.Disability:
            if row >= 1:
                return False
        if ( column in ( CTempInvalidDocumentsModel.Col_Electronic,
                         CTempInvalidDocumentsModel.Col_Serial,
                         CTempInvalidDocumentsModel.Col_Number)
              and 0<=row<len(self._items)
              and self._items[row].signatures
           ):
            return False
        if role == Qt.CheckStateRole:
            if column == self.getColIndex('include'):
                if row >= 0 and row < len(self.items()):
                    self.setValue(row, 'include', QVariant(forceBool(value)))
                    self.emitCellChanged(row, column)
                    placeWork = forceStringEx(self.items()[row].value('placeWork'))
                    self.updatePlaceWork(row, column, forceBool(self.value(row, 'include')), placeWork)
                    return True
        return False


    def updatePlaceWork(self, row, column, value, placeWork):
        for i, item in enumerate(self._items):
            if placeWork == forceStringEx(item.value('placeWork')):
                if i != row:
                   self.setValue(i, 'include', QVariant(0))
                   self.emitCellChanged(i, column)


    def setIncludeItems(self, items):
        includeItems = []
        db = QtGui.qApp.db
        for item in items:
            newRecord = self.getEmptyRecord()
            copyFields(newRecord, item)
            if not forceBool(newRecord.value('duplicate')):
                newRecord.setValue('include', QVariant(1))
            newCareRecords = []
            careItems = item.tempInvalidCare.getItems()
            for careItem in careItems:
                newCareRecord = db.table('TempInvalidDocument_Care').newRecord()
                copyFields(newCareRecord, careItem)
                newCareRecord.setValue('id', toVariant(None))
                newCareRecords.append(newCareRecord)
            newRecord.tempInvalidCare.setItems(newCareRecords)
            includeItems.append(newRecord)
        rows = len(includeItems)
        for row, item in enumerate(includeItems):
            if not forceBool(item.value('duplicate')):
                placeWork = forceStringEx(item.value('placeWork'))
                for i in range(row+1, rows):
                    if placeWork == forceStringEx(includeItems[i].value('placeWork')):
                        includeItems[i].setValue('include', QVariant(0))
        self.setItems(includeItems)
        self.reset()


def getTempInvalidIdOpen(clientId, type, docCode = None):
    if clientId:
        db = QtGui.qApp.db
        tableTempInvalid = db.table('TempInvalid')
        tableRBTempInvalidResult = db.table('rbTempInvalidResult')
        cond = [tableTempInvalid['deleted'].eq(0),
                tableTempInvalid['client_id'].eq(clientId),
                tableTempInvalid['state'].eq(CTempInvalidState.opened),
                tableRBTempInvalidResult['state'].eq(CTempInvalidState.opened),
                tableTempInvalid['type'].eq(type),
                tableRBTempInvalidResult['able'].ne(1)
                ]
        if docCode:
            tableRBTempInvalidDocument = db.table('rbTempInvalidDocument')
            cond.append(tableRBTempInvalidDocument['code'].eq(docCode))
            table = tableTempInvalid.leftJoin(tableRBTempInvalidDocument, tableTempInvalid['doctype_id'].eq(tableRBTempInvalidDocument['id']))
        else:
            table = tableTempInvalid
        table = table.leftJoin(tableRBTempInvalidResult, tableRBTempInvalidResult['id'].eq(tableTempInvalid['result_id']))
        record = db.getRecordEx(table, 'TempInvalid.*', cond, 'TempInvalid.begDate DESC')
        tempInvalidId = forceRef(record.value('id')) if record else None
        return tempInvalidId
    return None


class CTempInvalidDocumentCareModel(CInDocTableModel):
    class CLocClientColumn(CInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.clientCaches = params.get('clientCaches', [])

        def toString(self, val, record):
            clientId  = forceRef(val)
            if clientId and self.clientCaches:
                clientRecord = self.clientCaches.get(clientId) if clientId else None
                if clientRecord:
                    birthDate = forceString(clientRecord.value('birthDate'))
                    name = formatName(forceString(clientRecord.value('lastName')),
                           forceString(clientRecord.value('firstName')),
                           forceString(clientRecord.value('patrName'))) + u', ' + birthDate
                    return toVariant(name)
            return QVariant()

        def setEditorData(self, editor, value, record):
            editor.setValue(forceRef(value))

        def getEditorData(self, editor):
            return toVariant(editor.value())

        def alignment(self):
            return QVariant(Qt.AlignLeft + Qt.AlignTop)

    def __init__(self, parent, clientCache):
        CInDocTableModel.__init__(self, 'TempInvalidDocument_Care', 'id', 'master_id', parent)
        self.addCol(CTempInvalidDocumentCareModel.CLocClientColumn(u'Пациент', 'client_id', 30, clientCaches=clientCache))
        self.addCol(CDateInDocTableCol( u'Начало',   'begDate',              10, canBeEmpty=True))
        self.addCol(CDateInDocTableCol( u'Окончание','endDate',              10, canBeEmpty=True))
        self.addCol(CRBInDocTableCol(   u'Режим',    'tempInvalidRegime_id', 10, 'rbTempInvalidRegime', filter=u'type = 0'))
        self.addCol(CICDExInDocTableCol(u'Диагноз',  'MKB',                  10))
        self.addCol(CRBInDocTableCol(   u'Причина',  'tempInvalidReason_id', 10, 'rbTempInvalidReason', filter=u'''code IN ('03', '09', '12', '13', '14', '15')'''))
        self.clientCache = clientCache
        self.clientId = None
        self.eventEditor = None
        self.readOnly = False
        self.tempInvalidId = None
        self.isElectronic = False


    def setTempInvalidClientId(self, clientId):
        self.clientId = clientId


    def setIsElectronic(self, value):
        self.isElectronic = value


    def getTempInvalidClientId(self):
        return self.clientId


    def setReadOnly(self, value):
        self.readOnly = value


    def isReadOnly(self):
        return self.readOnly


    def setTempInvalidId(self, tempInvalidId):
        self.tempInvalidId = tempInvalidId


    def getTempInvalidId(self):
        return self.tempInvalidId


    def setEventEditor(self, eventEditor):
        self.eventEditor = eventEditor


    def flags(self, index):
        if self.readOnly:
           return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        row = index.row()
        if not self.isElectronic and row >= 2:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable


    def setData(self, index, value, role=Qt.EditRole):
        row = index.row()
        if not self.isElectronic and row >= 2:
            return False
        return CInDocTableModel.setData(self, index, value, role)
    
    
    def newRecord(self, data):
        record = self.getEmptyRecord()
        record.setValue('client_Id', data['clientId'])
        db = QtGui.qApp.db
        tempInvalidRegimeId = forceInt(db.getRecordEx(db.table('rbTempInvalidRegime'), 'id', u'code={} and name="{}"'.format(data['tempInvalidRegime_code'][0], data['tempInvalidRegime_code'][1])).value(0))
        record.setValue('tempInvalidRegime_id', tempInvalidRegimeId)
        if 'begDate' in data.keys():    
            record.setValue('begDate', data['begDate'])
            record.setValue('endDate', data['endDate'])
        items = self.items()
        items.append(record)
        self.setItems(items)


    def getCaresInfo(self, context, masterId):
        count = 0
        result = context.getInstance(CTempInvalidDocumentCareInfoList, None)
        for item in self.items():
            if forceRef(item.value('master_id')) == masterId or masterId == -1 and not forceRef(item.value('master_id')):
                result.addItem(forceRef(item.value('id')), item)
                count += 1
        if count == 0:
            result = context.getInstance(CTempInvalidDocumentCareInfoList, masterId)
            result.load()
        return result


class CMedicalCommissionModel(CInDocTableModel):
    class CLocActionPropertiColumn(CInDocTableCol):
        def __init__(self, title, fieldName, propertiName, width, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.actionCaches = {}
            self.propertiName = propertiName

        def updateActionCaches(self, id):
            if id in self.actionCaches.keys():
                self.actionCaches.pop(id, None)

        def clearActionCaches(self):
            self.actionCaches.clear()

        def toString(self, val, record):
            actionId = forceRef(val)
            if actionId:
                action = self.actionCaches.get(actionId, None)
                if not action:
                    action = CAction(record=record)
                    if action:
                        self.actionCaches[actionId] = action
                if action and self.propertiName in action._actionType._propertiesByName:
                    return QVariant(action[self.propertiName])
            return val

    Col_Number = 1
    Col_NumberMC = 2
    Col_Decision = 11

    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Action', 'id', 'event_id', parent)
        self.setPersonCol = CActionPerson(u'Назначил',  'setPerson_id',   20, 'vrbPersonWithSpeciality')
        self.endPersonCol = CActionPerson(u'Выполнил',  'person_id',      20, 'vrbPersonWithSpeciality')
        self.addCol(CActionTypeTableCol(u'Тип',          'actionType_id',  15, None, classesVisible=True, showFields=CRBComboBox.showName))
        self.addCol(CMedicalCommissionModel.CLocActionPropertiColumn(u'Номер',    'id', u'Номер',    15))
        self.addCol(CMedicalCommissionModel.CLocActionPropertiColumn(u'Номер ЛН', 'id', u'Номер ЛН', 15))
        self.addCol(CEnumInDocTableCol(    u'Состояние', 'status',         10, CActionStatus.names))
        self.addCol(CDateTimeInDocTableCol(u'Назначено', 'directionDate',  10))
        self.addCol(CDateTimeInDocTableCol(u'План',      'plannedEndDate', 10))
        self.addCol(CDateTimeInDocTableCol(u'Начато',    'begDate',        10))
        self.addCol(CDateTimeInDocTableCol(u'Окончено',  'endDate',        10))
        self.addCol(CICDExInDocTableCol(   u'МКБ',       'MKB',            10))
        self.addCol(self.setPersonCol)
        self.addCol(self.endPersonCol)
        self.addCol(CMedicalCommissionModel.CLocActionPropertiColumn(u'Решение', 'id', u'Решение', 50))
        self.addCol(CInDocTableCol(        u'Примечание','note',           10))
        self.eventEditor = None
        self.readOnly = False
        self.tempInvalidId = None


    def setReadOnly(self, value):
        self.readOnly = value


    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled


    def setTempInvalidId(self, tempInvalidId):
        self.tempInvalidId = tempInvalidId


    def getTempInvalidId(self):
        return self.tempInvalidId


    def updateItems(self):
        self.loadItems(self.tempInvalidId)


    def data(self, index, role=Qt.DisplayRole):
        result = CInDocTableModel.data(self, index, role)
        row = index.row()
        if 0 <= row < len(self._items):
            if role == Qt.ToolTipRole:
                column = index.column()
                if column == CMedicalCommissionModel.Col_Decision:
                    col = self._cols[column]
                    record = self._items[row]
                    return col.toString(record.value(col.fieldName()), record)
        return result


    def loadItems(self, masterId):
        self._items = []
        self.clearColumnsCaches()
        self.setTempInvalidId(masterId)
        if masterId:
            actionTypeIdList = getActionTypeIdListByFlatCode(u'inspection_disability%')
            if actionTypeIdList:
                db = QtGui.qApp.db
                tableEvent = db.table('Event')
                eventIdList = db.getDistinctIdList(tableEvent, [tableEvent['id']], [tableEvent['tempInvalid_id'].eq(masterId), tableEvent['deleted'].eq(0)])
                if eventIdList:
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
                    filter = [table[self._masterIdFieldName].inlist(eventIdList)]
                    if self._filter:
                        filter.append(self._filter)
                    filter.append(table['deleted'].eq(0))
                    filter.append(table['actionType_id'].inlist(actionTypeIdList))
                    order = [u'Action.directionDate DESC']
                    self._items = db.getRecordList(table, cols, filter, order)
        self.reset()


    def getActionIdList(self):
        actionIdList = []
        for item in self._items:
            actionId = forceRef(item.value('id'))
            if actionId and actionId not in actionIdList:
                actionIdList.append(actionId)
        return actionIdList


    def setEventEditor(self, eventEditor):
        self.setPersonCol.setEventEditor(eventEditor)
        self.endPersonCol.setEventEditor(eventEditor)
        self.eventEditor = eventEditor


    def updateColumnsCaches(self, id):
        self._cols[CMedicalCommissionModel.Col_Number].updateActionCaches(id)
        self._cols[CMedicalCommissionModel.Col_NumberMC].updateActionCaches(id)
        self._cols[CMedicalCommissionModel.Col_Decision].updateActionCaches(id)


    def clearColumnsCaches(self):
        self._cols[CMedicalCommissionModel.Col_Number].clearActionCaches()
        self._cols[CMedicalCommissionModel.Col_NumberMC].clearActionCaches()
        self._cols[CMedicalCommissionModel.Col_Decision].clearActionCaches()


class CMedicalCommissionMSIModel(CMedicalCommissionModel):
    class CLocDateActionPropertiColumn(CDateInDocTableCol):
        def __init__(self, title, fieldName, propertiName, width, **params):
            CDateInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.actionCaches = {}
            self.propertiName = propertiName

        def updateActionCaches(self, id):
            if id in self.actionCaches.keys():
                self.actionCaches.pop(id, None)

        def clearActionCaches(self):
            self.actionCaches.clear()

        def toString(self, val, record):
            actionId = forceRef(val)
            if actionId:
                action = self.actionCaches.get(actionId, None)
                if not action:
                    action = CAction(record=record)
                    if action:
                        self.actionCaches[actionId] = action
                if action and self.propertiName in action._actionType._propertiesByName:
                    properti = action[self.propertiName]
                    if properti:
                        return QVariant(formatDate(properti))
            return QVariant()

    Col_Decision = 13
    Col_DisabilityGroup = 14

    def __init__(self, parent):
        CMedicalCommissionModel.__init__(self, parent)
        self._cols = []
        self.setPersonCol = CActionPerson(u'Назначил',  'setPerson_id',   20, 'vrbPersonWithSpeciality')
        self.endPersonCol = CActionPerson(u'Выполнил',  'person_id',      20, 'vrbPersonWithSpeciality')
        self.addCol(CActionTypeTableCol(u'Тип',          'actionType_id',  15, None, classesVisible=True, showFields=CRBComboBox.showName))
        self.addCol(CMedicalCommissionModel.CLocActionPropertiColumn(u'Номер',    'id', u'Номер',    15))
        self.addCol(CMedicalCommissionModel.CLocActionPropertiColumn(u'Номер ЛН', 'id', u'Номер ЛН', 15))
        self.addCol(CEnumInDocTableCol(    u'Состояние', 'status',         10, CActionStatus.names))
        self.addCol(CDateTimeInDocTableCol(u'Назначено', 'directionDate',  10))
        self.addCol(CDateTimeInDocTableCol(u'План',      'plannedEndDate', 10))
        self.addCol(CDateTimeInDocTableCol(u'Начато',    'begDate',        10))
        self.addCol(CDateTimeInDocTableCol(u'Окончено',  'endDate',        10))
        self.addCol(CICDExInDocTableCol(   u'МКБ',       'MKB',            10))
        self.addCol(self.setPersonCol)
        self.addCol(self.endPersonCol)
        self.addCol(CMedicalCommissionMSIModel.CLocDateActionPropertiColumn(u'Рег-ция', 'id', u'Дата регистрации МСЭ',         50).setToolTip(u'Дата регистрации документов в бюро МСЭ'))
        self.addCol(CMedicalCommissionMSIModel.CLocDateActionPropertiColumn(u'МСЭ',     'id', u'Дата освидетельствования МСЭ', 50).setToolTip(u'Дата освидетельствования в бюро МСЭ'))
        self.addCol(CMedicalCommissionModel.CLocActionPropertiColumn(u'Результат', 'id', u'Результат', 50))
        self.addCol(CMedicalCommissionModel.CLocActionPropertiColumn(u'Группа',    'id', u'Группа инвалидности', 50))
        self.addCol(CInDocTableCol(        u'Примечание','note',           10))


    def data(self, index, role=Qt.DisplayRole):
        result = CInDocTableModel.data(self, index, role)
        row = index.row()
        if 0 <= row < len(self._items):
            if role == Qt.ToolTipRole:
                column = index.column()
                if column in [CMedicalCommissionMSIModel.Col_Decision, CMedicalCommissionMSIModel.Col_DisabilityGroup]:
                    col = self._cols[column]
                    record = self._items[row]
                    return col.toString(record.value(col.fieldName()), record)
        return result


    def updateItems(self):
        if self.tempInvalidId:
            actionTypeIdList = getActionTypeIdListByFlatCode(u'inspection_disability%')
            if actionTypeIdList:
                db = QtGui.qApp.db
                tableAction = db.table('Action')
                tableEvent = db.table('Event')
                eventIdList = db.getDistinctIdList(tableEvent, [tableEvent['id']], [tableEvent['tempInvalid_id'].eq(self.tempInvalidId), tableEvent['deleted'].eq(0)])
                if eventIdList:
                    prevActionIdList = db.getDistinctIdList(tableAction, [tableAction['id']], [tableAction['event_id'].inlist(eventIdList), tableAction['actionType_id'].inlist(actionTypeIdList), tableAction['deleted'].eq(0)])
                    self.loadItems(prevActionIdList)


    def loadItems(self, prevActionIdList):
        self._items = []
        self.clearColumnsCaches()
        if prevActionIdList:
            actionTypeIdList = getActionTypeIdListByFlatCode(u'inspection_mse%')
            if actionTypeIdList:
                db = QtGui.qApp.db
                table = self._table
                cols = [self._idFieldName,
                        self._masterIdFieldName,
                        table['prevAction_id']]
                for col in self._cols:
                    if not col.external():
                        cols.append(col.fieldName())
                if self._idxFieldName:
                    cols.append(self._idxFieldName)
                for col in self._hiddenCols:
                    cols.append(col)
                filter = [table['prevAction_id'].inlist(prevActionIdList)]
                if self._filter:
                    filter.append(self._filter)
                filter.append(table['deleted'].eq(0))
                filter.append(table['actionType_id'].inlist(actionTypeIdList))
                order = [u'Action.directionDate DESC']
                self._items = db.getRecordList(table, cols, filter, order)
        self.reset()


class CSignaturePeriod:
    def __init__(self, idx, begDate,  endDate,  personId,  chairPersonId):
        self.idx     = idx
        self.begDate = begDate
        self.endDate = endDate
        self.personId = personId
        self.chairPersonId = chairPersonId


class CTempInvalidTransferSubjectSelector(Ui_TempInvalidTransferSubjectSelector, CDialogBase):
    def __init__(self, parent, tempInvalidId):
        CDialogBase.__init__(self, parent)
        self.tempId = tempInvalidId
        self.addModels('ReadyTempInvalidDocuments', CTransferSubjectSelectorModel(self))
        self.setupUi(self)
        self.setWindowTitle(u'Перечень элементов ЭЛН, подлежащих передаче в СФР')
        self.tblReadyTempInvalidDocuments.setModel(self.modelReadyTempInvalidDocuments)

        self.tblReadyTempInvalidDocuments.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tblReadyTempInvalidDocuments.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)

        self.updateReadyTempInvalidDocuments()


    @withWaitCursor
    def updateReadyTempInvalidDocuments(self):
        temp_invalid_id = self.tempId
        temp_invalid_ids_chain = self.get_chain_tempInvalid_ids(temp_invalid_id)
        fss_system_id = getFssSystemId()

        elem_to_transfer_list = []
        for temp_invalid in temp_invalid_ids_chain:
            idList = selectReadyTempInvalidDocumentById(temp_invalid, fss_system_id)
            elem_to_transfer_list += idList
        if elem_to_transfer_list:
            elem_to_transfer_list.sort()
            self.modelReadyTempInvalidDocuments.setIdList(elem_to_transfer_list)
            self.btnTransfer.setEnabled(True)
            self.tblReadyTempInvalidDocuments.selectAll()


    def get_chain_tempInvalid_ids(self, temp_invalid_id):
        db = QtGui.qApp.db
        chain = []
        while temp_invalid_id:
            chain.append(temp_invalid_id)
            tableTempInvalid = db.table('TempInvalid')
            cond = [
                tableTempInvalid['id'].eq(temp_invalid_id),
                tableTempInvalid['deleted'].eq(0),
            ]
            record = db.getRecordEx(tableTempInvalid, cols='prev_id', where=cond)
            if record:
                if forceInt(record.value('prev_id')):
                    temp_invalid_id = forceInt(record.value('prev_id'))
                else:
                    temp_invalid_id = None
            else:
                temp_invalid_id = None
        return chain


    @pyqtSignature('')
    def on_btnTransfer_clicked(self):
        idList = self.tblReadyTempInvalidDocuments.selectedItemIdList()
        if idList:
            if self.check_prevDocumentExported(idList):
                self.parent().transfer_tempId_list = idList

                self.close()
                self.parent().accept()
        else:
            messageBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning, u'Внимание!',
                                           u'Не выбраны документы для передачи',
                                           QtGui.QMessageBox.Ok)
            messageBox.exec_()


    def check_prevDocumentExported(self, id_list):
        # функция проверки у всех ли элементов передан в СФР предыдущий документ при его наличии
        result = True
        model = self.tblReadyTempInvalidDocuments.model()
        db = QtGui.qApp.db
        tableTempInvalidDocument = db.table('TempInvalidDocument')
        cols = ['id', 'fssStatus']
        for id in id_list:
            prevNumber = model.getRecordValueByIdCol(4, id)
            if prevNumber:
                cond = [tableTempInvalidDocument['number'].eq(prevNumber),
                        tableTempInvalidDocument['electronic'].eq(1),
                        tableTempInvalidDocument['deleted'].eq(0)]
                record = db.getRecordEx(tableTempInvalidDocument, cols, where=cond)
                ok = record.value('fssStatus').toString() == 'R' or record.value('id').toInt()[0] in id_list
                if result:
                    result = ok
        if not result:
            # Не у всех продолжений передан результат базового ЭЛН, выберете его для передачи или передайте отдельно
            messageBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning, u'Внимание!',
                                           u'Невозможно отправить выбранный документ, '
                                           u'так как не передан результат предыдущего ЭЛН.',
                                           QtGui.QMessageBox.Ok)
            messageBox.exec_()
        return result


def getFssSystemId():
    db = QtGui.qApp.db
    tableExternalSystem = db.table('rbExternalSystem')
    systemId = forceRef(db.translate(tableExternalSystem, 'code', u'СФР', 'id'))
    if systemId is None:
        record = tableExternalSystem.newRecord()
        record.setValue('code', u'СФР')
        record.setValue('name', u'СФР')
        systemId = db.insertRecord(tableExternalSystem, record)
    return systemId


class CTempInvalidSignatureSubjectSelector(Ui_TempInvalidSignatureSubjectSelector, CDialogBase):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.addModels('SingnatureSubjectSelector', CSingnatureSubjectSelectorModel(self))
        self.setupUi(self)
        self.setWindowTitle(u'Перечень элементов ЭЛН, подлежащих подписыванию')
        self.tblDocumentSubjects.setModel(self.modelSingnatureSubjectSelector)


    def addDocumentPart(self, number, placeWork, part, signPersonId, signOwner, signDatetime, signFunc):
        record = self.modelSingnatureSubjectSelector.getEmptyRecord()
        record.setValue('number',        number)
        record.setValue('placeWork',     placeWork)
        record.setValue('part',          part)
        record.setValue('signPerson_id', signPersonId)
        record.setValue('signOwner',     signOwner)
        record.setValue('signDatetime',  signDatetime)
        if signDatetime is None:
            record.setValue('toSign',        True)
        record.signFunc = signFunc
        self.modelSingnatureSubjectSelector.addRecord(record)


    def getSignFuncsOfCheckedRecords(self):
        return [ record.signFunc
                 for record in self.modelSingnatureSubjectSelector.items()
                 if forceBool(record.value('toSign'))
               ]


class CBaseSingnatureSubjectSelectorModel(CRecordListModel):
    def __init__(self,  parent):
        CRecordListModel.__init__(self, parent)
        self.addCol(CInDocTableCol(u'Номер',                 'number',        12)).setReadOnly()
        self.addCol(CInDocTableCol(u'Место работы',          'placeWork',     30)).setReadOnly()
        self.addCol(CInDocTableCol(u'Подписываемый элемент', 'part',          12)).setReadOnly()
        self.addCol(CActionPerson(u'Подписал',               'signPerson_id', 20, 'vrbPersonWithSpeciality')).setReadOnly()
        self.addCol(CInDocTableCol(u'ЭЦП',                   'signOwner',     12)).setReadOnly()
        self.addCol(CDateTimeInDocTableCol(u'Подписано',     'signDatetime',  10)).setReadOnly()


    def cellReadOnly(self, index):
        return self.data(index, Qt.EditRole).isNull()


    def getEmptyRecord(self):
        result = QtSql.QSqlRecord()
        result.append(QtSql.QSqlField('number',        QVariant.String))
        result.append(QtSql.QSqlField('placeWork',     QVariant.String))
        result.append(QtSql.QSqlField('part',          QVariant.String))
        result.append(QtSql.QSqlField('signPerson_id', QVariant.Int))
        result.append(QtSql.QSqlField('signOwner',     QVariant.String))
        result.append(QtSql.QSqlField('signDatetime',  QVariant.DateTime))
        return result


class CSingnatureSubjectSelectorModel(CBaseSingnatureSubjectSelectorModel):
    def __init__(self,  parent):
        CBaseSingnatureSubjectSelectorModel.__init__(self, parent)
        self.addCol(CBoolInDocTableCol(u'Подписать',         'toSign',    3))


    def getEmptyRecord(self):
        result = CBaseSingnatureSubjectSelectorModel.getEmptyRecord(self)
        result.append(QtSql.QSqlField('toSign',        QVariant.Bool))
        return result


class CTransferSubjectSelectorModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent, [
            CTextCol(u'Номер',              ['number'], 20),
            CDateCol(u'Дата изменения',     ['modifyDatetime'],    10),
            CDesignationCol(u'Врач',        ['master_id'],  [('TempInvalid', 'person_id'), ('vrbPersonWithSpeciality', 'name')], 20),
            CDesignationCol(u'Получатель',  ['master_id'], [('TempInvalid', 'client_id'), ('Client', 'CONCAT(lastName, " ", firstName, " ", patrName)')], 40),
            CTextCol(u'Номер базового ЭЛН', ['prevNumber'], 20)],
                'TempInvalidDocument')


class CTempInvalidRevokeSignatureSubjectSelector(Ui_TempInvalidSignatureSubjectSelector, CDialogBase):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.addModels('SingnatureSubjectSelector', CRevokeSingnatureSubjectSelectorModel(self))
        self.setupUi(self)
        self.setWindowTitle(u'Перечень подписанных элементов ЭЛН, подпись которых может быть отменена')
        self.tblDocumentSubjects.setModel(self.modelSingnatureSubjectSelector)


    def addDocumentPart(self, number, placeWork, part, signPersonId, signOwner, signDatetime, revokeFunc):
        record = self.modelSingnatureSubjectSelector.getEmptyRecord()
        record.setValue('number',        number)
        record.setValue('placeWork',     placeWork)
        record.setValue('part',          part)
        record.setValue('signPerson_id', signPersonId)
        record.setValue('signOwner',     signOwner)
        record.setValue('signDatetime',  signDatetime)
        record.setValue('toRevoke',      False)

        record.revokeFunc = revokeFunc
        self.modelSingnatureSubjectSelector.addRecord(record)


    def getRevokeFuncsOfCheckedRecords(self):
        return [ record.revokeFunc
                 for record in self.modelSingnatureSubjectSelector.items()
                 if forceBool(record.value('toRevoke'))
               ]


class CRevokeSingnatureSubjectSelectorModel(CBaseSingnatureSubjectSelectorModel):
    def __init__(self,  parent):
        CBaseSingnatureSubjectSelectorModel.__init__(self, parent)
        self.addCol(CBoolInDocTableCol(u'Отменить',         'toRevoke',    3))


    def getEmptyRecord(self):
        result = CBaseSingnatureSubjectSelectorModel.getEmptyRecord(self)
        result.append(QtSql.QSqlField('toRevoke',        QVariant.Bool))
        return result


# Это не слишком удовлетворительный вариант выбора номера ЛН.
# Он должен работать если "всё хорошо",
# и терять номера в случае прерывания работы САМСОН-а.
def acquireElectronicTempInvalidNumber():
    db = QtGui.qApp.db
    userId = QtGui.qApp.userId
    orgId = QtGui.qApp.currentOrgId()
    for i in xrange(10):
        db.query('CALL acquireElectronicTempInvalidNumber(%s, %s, @resErrorCode, @resNumber)' % (str(userId) if userId else 'NULL', str(orgId) if orgId else 'NULL'))
        query = db.query('SELECT @resErrorCode, @resNumber')
        if query.next():
            record = query.record()
            code   = forceInt(record.value(0))
            number = forceString(record.value(1))
            if code == 0: # всё хорошо
                return number
            if code == 1: # нет доступных номерков
                raise Exception(u'Нет доступных номеров ЭЛН')
    raise Exception(u'Что-то идёт не так, невозможно получить номер ЭЛН')


def releaseElectronicTempInvalidNumber(number):
    db = QtGui.qApp.db
    userId = QtGui.qApp.userId
    db.query('CALL releaseElectronicTempInvalidNumber(%s, %s)'
              %  ( (str(userId) if userId else 'NULL'),
                   decorateString(number)
                 )
            )

