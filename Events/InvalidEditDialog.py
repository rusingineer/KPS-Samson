# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2023 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4                      import QtGui, QtSql
from PyQt4.QtCore               import Qt, QDate, QDateTime, QString, QVariant, pyqtSignature

from Orgs.PersonComboBoxEx import CPersonFindInDocTableCol
from RefBooks.TypeEducationalInstitution.Info import CTypeEducationalInstitutionInfo
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
from library.PrintTemplates     import applyTemplate
from library.ROComboBox         import CROEditableComboBox
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
from Registry.Utils             import CClientInfo, getClientWork, getClientMiniInfo
from Registry.ClientEditDialog  import CClientEditDialog
from Registry.ClientRelationsEditDialog import CClientRelationsEditDialog
from Orgs.Utils                 import getOrganisationInfo, getOrganisationShortName

from Orgs.Orgs                  import selectOrganisation
from Users.Rights               import (
                                        urAdmin,
                                        urRegWriteInsurOfficeMark,
                                        urRegTabWriteRegistry,
                                        urRegTabReadRegistry,
                                        urEditIssueDateTempInvalid)

from Events.Ui_InvalidEditDialog               import Ui_InvalidEditDialog


class CInvalidEditDialog(CItemEditorBaseDialog, Ui_InvalidEditDialog):

    def __init__(self,  parent, clientCache):
        CItemEditorBaseDialog.__init__(self, parent, 'TempInvalid')
        self.addModels('Documents', CInvalidDocumentsModel(self, clientCache))
        self.addObject('btnApply', QtGui.QPushButton(u'Применить', self))
        #self.addObject('btnTempInvalidProlong', QtGui.QPushButton(u'Продолжить', self))
        #self.addObject('btnPrint', getPrintButton(self, 'tempInvalid', u'Печать'))

        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinMaxButtonsHint | Qt.WindowSystemMenuHint)
        self.setWindowState(Qt.WindowMaximized)
        self.grpMainInfo.setStyleSheet('QGroupBox {font-weight: bold; color:red;}')
        self.grpDocuments.setStyleSheet('QGroupBox {font-weight: bold;}')
        self.tblDocuments.setModel(self.modelDocuments)
        self.tblDocuments.setSelectionModel(self.selectionModelDocuments)
        
        self.tblDocuments.addPopupDirectionMC()
        self.tblDocuments.addPopupDuplicateCurrentRow()
        self.tblDocuments.addPopupAction(self.actCreateContinuation)
        self.tblDocuments.addPopupSeparator()
        self.tblDocuments.addPopupDelRow()
        self.tblDocuments.addPopupDetermineContinued()
        self.tblDocuments.addPopupSeparator()
        self.tblDocuments.addPopupSeparator()
        self.tblDocuments.addPopupAction(self.actAnnulment)
        
        self.modelDocuments.setEventEditor(self)
        self.buttonBox.addButton(self.btnApply, QtGui.QDialogButtonBox.ActionRole)
        #self.buttonBox.addButton(self.btnPrint, QtGui.QDialogButtonBox.ActionRole)
        
        self.setupDirtyCather()
        self.clientCache = clientCache
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
        self.modifiableDiagnosisesMap = {}
        self.mapSpecialityIdToDiagFilter = {}
        self.blankParams = {}
        self.defaultBlankMovingId = None
        self.placeRegistry = False
        self.isReasonPrimary = False
        self.documentsSignatures = {}
        self.documentsSignatureR = False
        self.documentsSignatureB = False
        self.documentsSignatureExternalR = False
        self.periodsSignaturesC = {}
        self.periodsSignaturesD = {}

        self.cmbDiseaseCharacter.setTable('rbDiseaseCharacter', order='code')
        self.edtResultOtherwiseDate.setDate(QDate())


    @pyqtSignature('QString')
    def on_edtDiagnosis_textChanged(self, text):
        if len(forceString(text)) > 1:
            self.cmbEvent.setMKB(forceString(text[:3]) + '...')
        else:
            self.cmbEvent.setMKB(None)


    def setRecord(self, record):
        self.isReasonPrimary = True
        CItemEditorBaseDialog.setRecord(self, record)
        self.state = forceInt(record.value('state'))
        self.clientId = forceRef(record.value('client_id'))
        self.diagnosisId = forceRef(record.value('diagnosis_id'))
        MKB, MKBEx, characterId = self.getMKBs()
        self.edtDiagnosis.setText(MKB)
        self.cmbDiseaseCharacter.setValue(characterId)
        self.setType(forceInt(record.value('type')))
        setRBComboBoxValue(self.cmbDoctype, record, 'doctype_id')
        setRBComboBoxValue(self.cmbReason,  record, 'tempInvalidReason_id')

        setDateEditValue(self.edtResultOtherwiseDate, record, 'resultOtherwiseDate')
        self.edtCaseBegDate.setDate(forceDate(record.value('caseBegDate')))
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
        
        recordLast = db.getRecordEx(table, [table['id']], [table['prev_id'].eq(self.itemId()), table['deleted'].eq(0)], 'endDate')
        self.lastId = forceRef(recordLast.value('id')) if recordLast else None
        self.modelDocuments.loadItems(self.itemId(), forceRef(record.value('client_id')), self.prevId, self.lastId)
        self.prolonging = False
        self.defaultBlankMovingId = None
        self.isReasonPrimary = False
        self.newProlonging = False
        self.tblDocuments.setCurrentRow(0)
        

    def getIsNumberDisabilityFill(self):
        items = self.modelDocuments.items()
        for row, item in enumerate(items):
            number = forceStringEx(item.value('number'))
            if not number:
                return False
        return True


    def setType(self, type_, docCode=None, isNotEvent=False):
        self.type_ = type_
        self.docCode = docCode
        self.docId = forceRef(QtGui.qApp.db.translate('rbTempInvalidDocument', 'code', self.docCode, 'id')) if self.docCode else None
        filter = 'type=%d'%self.type_
        filierDoc = (filter+' AND code=\'%s\''%self.docCode) if (self.docCode and not isNotEvent) else filter
        self.cmbDoctype.setTable('rbTempInvalidDocument', False, filierDoc)
        self.cmbReason.setTable('rbTempInvalidReason', False, filter + (u''' AND code NOT IN ('05', '020')''' if self.clientSex == 1 else u''))
        self.modelDocuments.setType(self.type_)


    def setPrev(self, prevRecord):
        if prevRecord:
            self.prevId = forceRef(prevRecord.value('id'))
            self.prevState = forceInt(prevRecord.value('state'))
            self.edtCaseBegDate.setDate(forceDate(prevRecord.value('caseBegDate')))
        else:
            self.prevId = None
            self.prevState = None


    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        record.setValue('type', toVariant(self.type_))
        getRBComboBoxValue(self.cmbDoctype, record, 'doctype_id')
        getRBComboBoxValue(self.cmbReason,  record, 'tempInvalidReason_id')
        getRBComboBoxValue(self.cmbDisability,  record, 'disability_id')
        getDateEditValue(self.edtResultOtherwiseDate, record, 'resultOtherwiseDate')
        diagnosisTypeId = 1 #diagnosisType = закл
        #self.diagnosisId = diagnosis[0]
        record.setValue('diagnosis_id', toVariant(self.diagnosisId))
        state = self.getTempInvalidState()
        if (self.prolonging or self.state == CTempInvalidState.extended) and state != CTempInvalidState.annulled:
            state = CTempInvalidState.extended
        record.setValue('state',  state)
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
        result = True
        reasonId = self.cmbReason.value()
        result = result and (reasonId or self.checkInputMessage(u'причину', False, self.cmbReason))
        result = result and (len(self.modelDocuments.items()) or self.checkInputMessage(u'документ', False, self.tblDocuments, 0, 0))
        result = result and self.checkNumberTempInvalidDocument()
        result = result and self.checkSerialNumberTempInvalidDocument()
        result = result and self.checkReason()
        result = result and self.checkInvalidDisabilityDate()
        result = result and self.checkActualMKB()
        return result


    def checkReason(self):
        code = self.cmbReason.code()
        if not code:
            return False
        return True


    def checkInvalidDisabilityDate(self):
        begDate = self.edtCaseBegDate.date()
        endDate = self.edtCaseEndDate.date()
        indef = self.chkCaseEndDateIndef.isChecked()
        documentBegDate = self.modelDocuments.begDate()
        if not begDate:
            self.checkValueMessage(u'Дата Начала Установления инвалидности должна быть заполнена', False, self.edtCaseBegDate)
            return False
        if begDate > documentBegDate:
            self.checkValueMessage(u'Дата Начала Установления инвалидности не должна быть позже Даты выдачи справки', False, self.edtCaseBegDate)
            return False
        if begDate > QDate.currentDate():
            self.checkValueMessage(u'Дата Начала Установления инвалидности не должна быть позже текущей даты', False, self.edtCaseBegDate)
            return False
        if not indef and endDate:
            if begDate > endDate:
                self.checkValueMessage(u'Дата Начала Установления инвалидности не должна быть позже Дата Окончания Установления инвалидности.', False, self.self.edtCaseBegDate)
                return False
        return True


    def checkActualMKB(self):
        result = True
        MKB = unicode(self.edtDiagnosis.text())
        result = result and (MKB or self.checkInputMessage(u'диагноз', False, self.edtDiagnosis))
        return result


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


    def specifyDiagnosis(self, MKB):
        diagFilter = None
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


    # def getTempInvalidInfo(self, context):
    #     result = context.getInstance(CTempInvalidInfo, None)
    #     result._doctype = context.getInstance(CTempInvalidDocTypeInfo,  self.cmbDoctype.value())
    #     result._reason  = context.getInstance(CTempInvalidReasonInfo,  self.cmbReason.value())
    #     result._changedReason  = context.getInstance(CTempInvalidReasonInfo,  self.cmbChangedReason.value())
    #     result._extraReason  = context.getInstance(CTempInvalidExtraReasonInfo, forceRef(self.cmbExtraReason.value()))
    #     result._sex     = formatSex(self.cmbOtherSex.currentIndex())
    #     result._age     = self.edtOtherAge.value()
    #     result._client= context.getInstance(CClientInfo, self.cmbReceiver.value())
    #     result._duration, result._externalDuration = self.modelPeriods.calcLengths()
    #     result._begDate = CDateInfo(self.modelPeriods.begDate())
    #     result._endDate = CDateInfo(self.modelPeriods.endDate())
    #     result._accountPregnancyTo12Weeks = forceInt(self.cmbAccountPregnancyTo12Weeks.currentIndex())
    #     MKB, MKBEx, characterId = self.getMKBs()
    #     result._MKB = context.getInstance(CMKBInfo, MKB)
    #     result._MKBEx = context.getInstance(CMKBInfo, MKBEx)
    #     state = self.getTempInvalidState()
    #     result._state = state
    #     result._periods = self.modelPeriods.getPeriodsInfo(context)
    #     result._result = context.getInstance(CTempInvalidResultInfo, forceRef(self.cmbResult.value()))

    #     result._caseBegDate = CDateInfo(self.edtCaseBegDate.date())
    #     result._begDateStationary = CDateInfo(forceDate(self.edtBegDateStationary.date()))
    #     result._endDateStationary = CDateInfo(forceDate(self.edtEndDateStationary.date()))
    #     result._break = context.getInstance(CTempInvalidBreakInfo, self.cmbBreak.value())
    #     result._breakDate = CDateInfo(forceDate(self.edtBreakDate.date()))
    #     result._resultDate = CDateInfo(forceDate(self.edtResultDate.date()))
    #     result._resultOtherwiseDate = CDateInfo(forceDate(self.edtResultOtherwiseDate.date()))
    #     result._OGRN = self.edtOGRN.text()
    #     result._numberPermit = self.edtNumberPermit.text()
    #     result._begDatePermit = CDateInfo(self.edtBegDatePermit.date())
    #     result._endDatePermit = CDateInfo(self.edtEndDatePermit.date())
    #     result._receiver = context.getInstance(CClientInfo, self.cmbReceiver.value())
    #     result._eventId = self.cmbEvent.value()
    #     result._institution = context.getInstance(CTypeEducationalInstitutionInfo, self.cmbTypeEducationalInstitution.value())
    #     result._inf_contact = self.edtInfContact.text()
    #     present = False
    #     for document in self.modelDocuments.items():
    #         if document.signatures.present(document.signatures.resultSubject()):
    #             present = True
    #             break
    #     result._isSigned = (result._state == 1 and present)

    #     result._items = self.modelDocuments.getDocumentsInfo(context)
    #     if self.prevId:
    #         result._prev = context.getInstance(CTempInvalidInfo, self.prevId)
    #     else:
    #         result._prev = None

    #     for item in result._items:
    #         item._cares = self.modelCare.getCaresInfo(context, item.id)

    #     result._ok = True
    #     return result


    # @pyqtSignature('int')
    # def on_cmbDoctype_currentIndexChanged(self, index):
    #     self.modelDocuments.setDocCode(self.cmbDoctype.code())

    def getDuplicateAndParent(self):
        pass
#        items = []


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


    def createContinuation(self):
        document = self.tblDocuments.currentItem()
        if document:
            isExternal   = forceBool(document.value('isExternal'))
            isElectronic = forceBool(document.value('electronic'))
            number       = forceString(document.value('number'))
            annulmentReasonId = forceRef(document.value('annulmentReason_Id'))
            if isExternal and number and not annulmentReasonId:
                if isElectronic:
#                    continuationNumber = '12345'
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
        self.actAnnulment.setEnabled(isElectronic and bool(number) and not annulmentReasonId)


    @pyqtSignature('')
    def on_actCreateContinuation_triggered(self):
        self.createContinuation()


    @pyqtSignature('')
    def on_actAnnulment_triggered(self):
        QtGui.qApp.call(self, self.annulment)


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
                self.modelDocuments.setAnnulledDublicate(True)
                self.setDocumentsSignatures()
                self.tblDocuments.setCurrentRow(0)
                if not forceRef(prevRecord.value('prev_id')) and forceInt(prevRecord.value('state')) == CTempInvalidState.annulled:
                    self.edtCaseBegDate.setDate(self.modelPeriods.begDate())


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
        # newItems = []
        # duplicatePresent = any(forceBool(item.value('duplicate'))
        #                        for item in items
        #                       )
        # if duplicatePresent:
        #     resItems = []
        #     dialog = CTempInvalidDocumentProlongDialog(self, self.clientCache, items)
        #     try:
        #         if dialog.exec_():
        #             resItems = dialog.getItems()
        #     finally:
        #         dialog.deleteLater()
        #     includeItems = []
        #     for includeItem in resItems:
        #         if forceBool(includeItem.value('include')):
        #             includeItems.append(includeItem)
        #     if not includeItems:
        #         if self.itemId():
        #             try:
        #                 db = QtGui.qApp.db
        #                 db.transaction()
        #                 table = db.table('TempInvalid')
        #                 state = self.prevState if (self.prevState is not None) else CTempInvalidState.opened
        #                 db.updateRecords(table, table['state'].eq(state), [table['deleted'].eq(0), table['id'].eq(self.itemId())])
        #                 db.commit()
        #             except:
        #                 db.rollback()
        #                 raise
        #         return
        #     newItems = self.newTempInvalidDocuments(includeItems)
        # else:
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
        self.cmbResult.setValue(None)
        self.edtResultDate.setDate(QDate())
        self.edtResultOtherwiseDate.setDate(QDate())
        self.tblPeriods.setFocus(Qt.OtherFocusReason)
        self.tblPeriods.setCurrentIndex(self.modelPeriods.index(0, 1))
        self.newProlonging = not self.itemId()
        self.setDocumentsSignatures()
        self.tblDocuments.setCurrentRow(0)


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


    # @pyqtSignature('int')
    # def on_btnPrint_printByTemplate(self, templateId):
    #     context = CInfoContext()
    #     tempInvalidInfo = self.getTempInvalidInfo(context)
    #     eventInfo = None
    #     data = { 'event' : eventInfo,
    #              'client': context.getInstance(CClientInfo, self.clientId, QDate.currentDate()),
    #              'tempInvalid': tempInvalidInfo,
    #              'getEventList': lambda begDate, endDate: getEventListByDates(context, self.clientId, begDate, endDate)
    #            }
    #     applyTemplate(self, templateId, data)


class CInvalidCreateDialog(CInvalidEditDialog):
    def __init__(self,  parent, clientId = None, clientCache = None, MKB = u''):
        CInvalidEditDialog.__init__(self, parent, clientCache)
        self.lblDiagnosis.setVisible(True)
        self.edtDiagnosis.setVisible(True)
        self.cmbDiseaseCharacter.setVisible(True)
        self.clientId = clientId
        self.MKB = MKB
        self.cmbDiseaseCharacter.setTable('rbDiseaseCharacter', order='code')


    def createTempInvalidDocument(self, MKB=u'', placeRegistry=False, type=0, execDate=None, execPersonId=None, begDateStationary=None, endDateStationary=None):
        self.modelDocuments.setClientId(self.clientId)
        newRecord = self.modelDocuments.getEmptyRecord()
        newRecord.setValue('issueDate', toVariant(execDate) if execDate else toVariant(QDate.currentDate()))
        self.modelDocuments.addRecord(newRecord)
        if MKB:
            acceptable, specifiedMKB, specifiedMKBEx, specifiedCharacterId, specifiedTraumaTypeId, specifiedDispanserId, specifiedRequiresFillingDispanser, specifiedProlongMKB = self.specifyDiagnosis(MKB)
            self.MKB = specifiedMKB
            self.edtDiagnosis.setText(self.MKB)
            self.updateCharacterByMKB(specifiedMKB, specifiedCharacterId)
        if len(self.modelDocuments.items()) > 0:
            self.tblDocuments.setCurrentRow(0)


    def getRecord(self): 
        record = CItemEditorBaseDialog.getRecord(self)
        record.setValue('type', toVariant(self.type_))
        getRBComboBoxValue(self.cmbDoctype, record, 'doctype_id')
        getRBComboBoxValue(self.cmbReason,  record, 'tempInvalidReason_id')
        getDateEditValue(self.edtResultOtherwiseDate, record, 'resultOtherwiseDate')
        #diagnosisTypeId = 1 #diagnosisType = закл
        #diagnosis = getDiagnosisId2(date, self.modelPeriods.lastPerson(), self.clientId, diagnosisTypeId, unicode(self.edtDiagnosis.text()), u'', self.cmbDiseaseCharacter.value(), None, None)
        #record.setValue('diagnosis_id', toVariant(diagnosis[0]))
        if self.prolonging or self.state == CTempInvalidState.extended:
            state = CTempInvalidState.extended
        else:
            state = self.getTempInvalidState()
        record.setValue('state',  state)
        record.setValue('prev_id', toVariant(self.prevId))
        record.setValue('caseBegDate', toVariant(self.edtCaseBegDate.date()))
        self.saveProlonging = False
        return record


    def getMKBs(self):
        return unicode(self.edtDiagnosis.text()), '', self.cmbDiseaseCharacter.value()


class CInvalidDocumentsModel(CInDocTableModel):
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
    Col_ChairPersonId   = 13
    Col_LastId          = 14
    Col_Note            = 15
    Col_AnnulmentReason = 16

    def __init__(self, parent, clientCache):
        CInDocTableModel.__init__(self, 'TempInvalidDocument', 'id', 'master_id', parent)
        self.addCol(CRBInDocTableCol(       u'Орган выдачи справки',                '',                22,   'rb'))
        self.addCol(CInDocTableCol(         u'Серия',                               'serial',          22                                                 ))
        self.addCol(CInDocTableCol(         u'Номер',                               'number',          22,  maxLength=12, inputMask='999999999999;'       ))
        self.addCol(CInvalidDocumentsModel.CIssueDateInDocTableCol(     u'Дата выдачи',            'issueDate', 10))
        self.addCol(CInDocTableCol(         u'№ акта освидетельствования',          '',          22                                                 ))
        self.addCol(CInDocTableCol(         u'Дата акта освидетельствования',          '',          10))
        self.addCol(CBoolInDocTableCol(     u'Д',                                   'duplicate',       3                                                  ).setToolTip(u'Дубликат')).setReadOnly(True)
        self.addCol(CRBInDocTableCol(       u'Причина выдачи дубликата',            'duplicateReason_id',  10, 'rbTempInvalidDuplicateReason'             ))

        self.eventEditor = None
        self.readOnly = False
        self.clientId = None
        self.tempInvalidPrevId = None
        self.tempInvalidLastId = None
        self.blankIdList = []
        self.numberBlankList = {}
        self.isEnabledPatient = True
        self.type = None
        self.docCode = None
        self.clientCache = clientCache
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


    def getEmptyRecord(self):
        result = CInDocTableModel.getEmptyRecord(self)
        result.append(QtSql.QSqlField('prevDuplicate_id', QVariant.Int))
        if QtGui.qApp.userSpecialityId:
            result.setValue('person_id', toVariant(QtGui.qApp.userId))
            if forceBool(result.value('duplicate')):
                result.setValue('execPerson_id', toVariant(QtGui.qApp.userId))
        return result


    def setType(self, type_):
        self.cols()[CInvalidDocumentsModel.Col_Number].setInputMask('9'*64)
        self.cols()[CInvalidDocumentsModel.Col_Number].setMaxLength(64)
        self.cols()[CInvalidDocumentsModel.Col_PrevNumber].setInputMask('999999999999;')


    def setEnabledPatient(self, otherPersonEnabled, rightRegWriteInsurOfficeMark, checkedInsuranceOfficeMark, isReasonPrimary):
        enable = rightRegWriteInsurOfficeMark if checkedInsuranceOfficeMark else True
        self.isEnabledPatient = bool(otherPersonEnabled and enable)
        if not otherPersonEnabled and enable and not isReasonPrimary:
#            for record in self._items:
#                record.setValue('clientPrimum_id', toVariant(None))
#                record.setValue('clientSecond_id', toVariant(None))
            pass


    def setReadOnly(self, value):
        self.readOnly = value


    def cellReadOnly(self, index):
        column = index.column()
        row = index.row()
        if 0 <= row < len(self._items):
            record = self._items[row]
            isExternal = forceBool(record.value('isExternal'))
            if isExternal:
                if column in (CInvalidDocumentsModel.Col_Duplicate,
                              CInvalidDocumentsModel.Col_DuplicateReason
                             ):
                    return True
                if forceBool(record.value('duplicate')):
                    if column in ( CInvalidDocumentsModel.Col_Duplicate):
                        return True
        elif column not in ( CInvalidDocumentsModel.Col_IssueDate,
                             CInvalidDocumentsModel.Col_Serial,
                             CInvalidDocumentsModel.Col_Number):
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
        self.chairPersonCol.setEventEditor(eventEditor)
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


class CTempInvalidDocumentsProlongModel(CInvalidDocumentsModel):

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
#    Col_ClientPrimumId = 14
#    Col_ClientSecondId = 15
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
#                clientPrimumId = forceRef(item.value('clientPrimum_id'))
#                clientSecondId = forceRef(item.value('clientSecond_id'))
                for i in range(row+1, rows):
                    if placeWork == forceStringEx(includeItems[i].value('placeWork')):
                        # if clientPrimumId == forceRef(includeItems[i].value('clientPrimum_id')) and clientSecondId == forceRef(includeItems[i].value('clientSecond_id')):
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


# def acquireElectronicTempInvalidNumber():
#     db = QtGui.qApp.db
#     userId = QtGui.qApp.userId
#     orgId = QtGui.qApp.currentOrgId()
#     for i in xrange(10):
#         db.query('CALL acquireElectronicTempInvalidNumber(%s, %s, @resErrorCode, @resNumber)' % (str(userId) if userId else 'NULL', str(orgId) if orgId else 'NULL'))
#         query = db.query('SELECT @resErrorCode, @resNumber')
#         if query.next():
#             record = query.record()
#             code   = forceInt(record.value(0))
#             number = forceString(record.value(1))
#             if code == 0: # всё хорошо
#                 return number
#             if code == 1: # нет доступных номерков
#                 raise Exception(u'Нет доступных номеров ЭЛН')
#     raise Exception(u'Что-то идёт не так, невозможно получить номер ЭЛН')


# def releaseElectronicTempInvalidNumber(number):
#     db = QtGui.qApp.db
#     userId = QtGui.qApp.userId
#     db.query('CALL releaseElectronicTempInvalidNumber(%s, %s)'
#               %  ( (str(userId) if userId else 'NULL'),
#                    decorateString(number)
#                  )
#             )

