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
from PyQt4.QtCore import Qt, QDate, QString, QVariant, pyqtSignature, SIGNAL
from Orgs.OrgComboBox import COrgInDocTableCol
from Orgs.Utils import getOrganisationInfo

from library.DateEdit           import CDateEdit
from library.interchange        import (
                                        getRBComboBoxValue,
                                        setRBComboBoxValue
                                       )
from library.ICDUtils           import MKBwithoutSubclassification
from library.InDocTable         import (
                                        CBoolInDocTableCol,
                                        CDateInDocTableCol,
                                        CInDocTableCol,
                                        CRBInDocTableCol,
                                        CInDocTableModel
                                       )
from library.ItemsListDialog    import CItemEditorBaseDialog
from library.PrintInfo import CInfoContext, CDateInfo
from library.PrintTemplates     import getPrintButton, applyTemplate

from library.Utils import (
    forceBool,
    forceDate,
    forceInt,
    forceRef,
    forceString,
    forceStringEx,
    formatDate,
    toVariant,
    calcAgeTuple,
    trim,
)

from Events.Action import CAction
from Events.EventInfo import CEventInfoList
from Events.MKBInfo             import CMKBInfo
from Events.TempInvalidInfo     import (
                                        CTempInvalidInfo,
                                        CTempInvalidDocTypeInfo,
                                        CTempInvalidDocumentItemInfoList,
                                       )

from Events.Utils               import (
                                        getAvailableCharacterIdByMKB,
                                        getDiagnosisId2
                                       )

from RefBooks.TempInvalidState  import CTempInvalidState
from Registry.Utils             import CClientInfo, getClientMiniInfo
from Registry.ClientRelationsEditDialog import CClientRelationsEditDialog

from Users.Rights import (urEditIssueDateTempInvalid)

from Events.Ui_TempDisabilityEditDialog import Ui_TempDisabilityEditDialog

class CTempDisabilityEditDialog(CItemEditorBaseDialog, Ui_TempDisabilityEditDialog):

    def __init__(self,  parent, clientCache):
        CItemEditorBaseDialog.__init__(self, parent, 'TempInvalid')
        self.addModels('Documents', CTempDisabilityDocumentsModel(self, clientCache))
        self.addObject('actProlong', QtGui.QAction(u'Продлить', self))
        self.addObject('actDuplicate', QtGui.QAction(u'Создать дубликат', self))
        self.addObject('actDelete', QtGui.QAction(u'Удалить', self))
        self.addObject('btnApply', QtGui.QPushButton(u'Применить', self))
        self.addObject('btnPrint', getPrintButton(self, 'tempInvalid', u'Печать'))
        
        self.setupUi(self)
        
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinMaxButtonsHint | Qt.WindowSystemMenuHint)
        self.setWindowTitleEx(u'Инвалидность')
        self.setWindowState(Qt.WindowMaximized)
        self.grpMainInfo.setStyleSheet('QGroupBox {font-weight: bold; color:red;}')
        self.grpTempDisabilityDocuments.setStyleSheet('QGroupBox {font-weight: bold;}')
        
        self.tblDocuments.setModel(self.modelDocuments)
        self.tblDocuments.addPopupAction(self.actProlong)
        self.tblDocuments.addPopupAction(self.actDuplicate)
        self.tblDocuments.addPopupSeparator()
        self.tblDocuments.addPopupAction(self.actDelete)
        
        self.clientCache = clientCache
        self.disabilityRecord = None
        
        self.buttonBox.addButton(self.btnApply, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnPrint, QtGui.QDialogButtonBox.ActionRole)
        #self.btnDuplicate.setEnabled(False)
        
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
        self.updateOtherwiseDate = False
        self.state = CTempInvalidState.opened
        
        self.setupDirtyCather()
        
        self.modifiableDiagnosisesMap = {}
        self.mapSpecialityIdToDiagFilter = {}
        self.blankParams = {}
        self.defaultBlankMovingId = None
        
        self.cmbDiseaseCharacter.setTable('rbDiseaseCharacter', order='code')
        #self.cmbDisability.setTable('rbTempInvalidRegime', filter='type = 1')
        
        self.placeRegistry = False
        self.isReasonPrimary = False
        self.documentsSignatures = {}
        self.documentsSignatureR = False
        self.documentsSignatureB = False
        self.documentsSignatureExternalR = False
        self.periodsSignaturesC = {}
        self.periodsSignaturesD = {}
        
        self.cmbReceiver.connect(self.cmbReceiver.lineEdit(), SIGNAL('textChanged(QString)'), self.on_cmbReceiver_textChanged)
        self.transfer_tempId_list = []
        self.edtReasonNote.setVisible(False)
        self.lblReasonNote.setVisible(False)
        self.edtCaseDateDueTo.setDate(QDate())
        self.edtCaseBegDate.setDate(QDate())
        self.edtSkipCaseEndDate.setDate(QDate())
        self.edtSkipCaseBegDate.setDate(QDate())
        self.edtChildCaseEndDate.setDate(QDate())
        self.edtChildCaseBegDate.setDate(QDate())
        self.edtNextCase.setDate(QDate())

    
    def setClient(self, client_id):
        self.clientId = client_id
        self.cmbReceiver.setValue(self.clientId)
        self.cmbReceiver.setClientId(self.clientId)

    def setRecord(self, record):
        self.isReasonPrimary = True
        CItemEditorBaseDialog.setRecord(self, record)
        self.state = forceInt(record.value('state'))
        self.clientId = forceRef(record.value('client_id'))
        self.diagnosisId = forceRef(record.value('diagnosis_id'))
        MKB, MKBEx, characterId = self.getMKBs()
        
        self.setType(forceInt(record.value('type')))
        
        setRBComboBoxValue(self.cmbGroup, record, 'doctype_id')
        setRBComboBoxValue(self.cmbReason,  record, 'tempInvalidReason_id')
        self.cmbReceiver.setValue(forceRef(record.value('client_id')))
        self.edtCaseBegDate.setDate(forceDate(record.value('caseBegDate')))
        self.edtNextCase.setDate(forceDate(record.value('nextCaseDate')))
        self.cmbReceiver.setClientId(self.clientId)
        self.edtDiagnosis.setText(MKB)
        self.cmbDiseaseCharacter.setValue(characterId)
        
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
        
        table = db.table('TempInvalid_Disability')
        cond = [
            table['deleted'].eq(0),
            table['master_id'].eq(record.value('id'))
        ]
        self.disabilityRecord = db.getRecordEx(table, '*', cond)
        if self.disabilityRecord:
            self.cmbSetType.setCurrentIndex(forceInt(self.disabilityRecord.value('setType')))
            self.edtCaseDateDueTo.setDate(forceDate(self.disabilityRecord.value('caseDateDueTo')))
            self.chkCaseDateIndef.setChecked(forceBool(self.disabilityRecord.value('caseDateDueToIndef')))
            self.cmbSkipCaseReason.setCurrentIndex(forceInt(self.disabilityRecord.value('skipCaseReason')))
            self.edtSkipCaseBegDate.setDate(forceDate(self.disabilityRecord.value('skipCaseBegDate')))
            self.edtSkipCaseEndDate.setDate(forceDate(self.disabilityRecord.value('skipCaseEndDate')))
            self.edtChildCaseBegDate.setDate(forceDate(self.disabilityRecord.value('childCaseBegDate')))
            self.edtChildCaseEndDate.setDate(forceDate(self.disabilityRecord.value('childCaseEndDate')))
            self.edtReasonNote.setText(forceString(self.disabilityRecord.value('reasonNote')))
            if self.disabilityRecord.value('childCaseBegDate') or self.disabilityRecord.value('childCaseEndDate'):
                self.chkChildCase.setChecked(True)
            else:
                self.chkChildCase.setChecked(False)
        else:
            self.disabilityRecord = table.newRecord()
            self.disabilityRecord.setValue('master_id', record.value('id'))
            db.insertRecord(table, self.disabilityRecord)
            self.disabilityRecord = db.getRecordEx(table, '*', cond)
            
        self.modelDocuments.loadItems(self.itemId())
        
        self.defaultBlankMovingId = None
        self.isReasonPrimary = False

        self.setDocumentsSignatures()
        self.tblDocuments.setCurrentRow(0)


    def setDocumentsSignaturesNoSave(self):
        self.documentsSignatures, self.documentsSignatureR, self.documentsSignatureB, self.documentsSignatureExternalR, self.periodsSignaturesC, self.periodsSignaturesD = self.getDocumentsSignaturesNoSave()
        self.modelDocuments.setDocumentsSignatures(self.documentsSignatures, self.documentsSignatureR, self.documentsSignatureExternalR)


    def setDocumentsSignatures(self):
        self.documentsSignatures, self.documentsSignatureR, self.documentsSignatureB, self.documentsSignatureExternalR, self.periodsSignaturesC, self.periodsSignaturesD = self.getDocumentsSignatures(self.modelDocuments.getTempInvalidDocumentIdList())


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
                    masterId = forceRef(record.value('master_id'))
                    subject = QString(forceStringEx(record.value('subject')))
                    if len(subject) > 0:
                        documentsSignaturesDict = documentsSignatures.get(masterId, {})
                        subject1 = subject.left(1)
                        if subject1 == u'R':
                            state = None
                            isExternal = forceBool(record.value('isExternal'))
                            tempInvalidId = forceRef(record.value('tempInvalidId'))
                            if tempInvalidId:
                                tableQuery = tableTI.innerJoin(tableTIR, tableTIR['id'].eq(tableTI['result_id']))
                                tempInvalidRecord = db.getRecordEx(tableQuery, [tableTI['result_id'], tableTIR['state']], [tableTI['id'].eq(tempInvalidId), tableTI['deleted'].eq(0)])
                                if tempInvalidRecord:
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


    def on_cmbReceiver_textChanged(self, text):
        if self.cmbReceiver.isVisible():
            receiverId = self.cmbReceiver.value()
            #self.modelDocuments.setTempInvalidClientId(receiverId)
            self.cmbReceiver.setClientId(receiverId)
            if receiverId:
                self.clientId = receiverId
            if not receiverId:
                self.cmbReceiver.setClientId(None)


    def getClientSexAge(self, clientId):
        sex = 0
        ageClient = 0
        clientAgeTuple = (0, 0, 0, 0)
        if clientId:
            db = QtGui.qApp.db
            table = db.table('Client')
            record = db.getRecordEx(table, [table['sex'], u'age(Client.birthDate, %s) AS ageClient, Client.birthDate' % (db.formatDate(QDate.currentDate()))], [table['id'].eq(clientId), table['deleted'].eq(0)])
            if record:
                sex = forceInt(record.value('sex'))
                ageClient = forceInt(record.value('ageClient'))
                birthDate = forceDate(record.value('ageClient'))
                clientAgeTuple = calcAgeTuple(birthDate, QDate.currentDate())
        return sex, ageClient, clientAgeTuple


    def setType(self, type_, docCode=None, isNotEvent=False):
        self.type_ = type_
        self.docCode = docCode
        self.docId = forceRef(QtGui.qApp.db.translate('rbTempInvalidDocument', 'code', self.docCode, 'id')) if self.docCode else None
        self.clientSex, self.clientAge, self.clientAgeTuple = self.getClientSexAge(self.clientId)
        
        filter = 'type=%d'%self.type_
        filterDoc = (filter+' AND code=\'%s\''%self.docCode) if (self.docCode and not isNotEvent) else filter
        
        self.cmbGroup.setTable('rbTempInvalidDocument', False, filterDoc)
        self.cmbReason.setTable('rbTempInvalidReason', False, filter + (u''' AND code NOT IN ('05', '020')''' if self.clientSex == 1 else u''))
        #self.cmbDocType.setTable('', False, filter)


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
        record.setValue('type', 1)
        getRBComboBoxValue(self.cmbGroup, record, 'doctype_id')
        getRBComboBoxValue(self.cmbReason,  record, 'tempInvalidReason_id')
        record.setValue('client_id', toVariant(self.cmbReceiver.value()))
        
        date = self.edtCaseBegDate.date()
        diagnosisTypeId = 1 #diagnosisType = закл
        diagnosis = getDiagnosisId2(date, None, self.clientId, diagnosisTypeId, unicode(self.edtDiagnosis.text()), u'', self.cmbDiseaseCharacter.value(), None, None)
        self.diagnosisId = diagnosis[0]
        record.setValue('diagnosis_id', toVariant(self.diagnosisId))
        record.setValue('prev_id', toVariant(self.prevId))
        record.setValue('caseBegDate', toVariant(self.edtCaseBegDate.date()))
        
        if self.disabilityRecord:
            self.disabilityRecord.setValue('skipCaseReason', toVariant(self.cmbSkipCaseReason.currentIndex()))
            self.disabilityRecord.setValue('setType', toVariant(self.cmbSetType.currentIndex()))
            self.disabilityRecord.setValue('nextCaseDate', toVariant(self.edtNextCase.date()))
            self.disabilityRecord.setValue('caseDateDueToIndef', toVariant(self.chkCaseDateIndef.isChecked()))
            if self.cmbSkipCaseReason.currentIndex() > 0:
                self.disabilityRecord.setValue('skipCaseBegDate', toVariant(self.edtSkipCaseBegDate.date()))
                self.disabilityRecord.setValue('skipCaseEndDate', toVariant(self.edtSkipCaseEndDate.date()))
            else:
                self.disabilityRecord.setValue('skipCaseBegDate', None)
                self.disabilityRecord.setValue('skipCaseEndDate', None)
            if self.chkChildCase.isChecked():
                self.disabilityRecord.setValue('childCaseBegDate', toVariant(self.edtChildCaseBegDate.date()))
                self.disabilityRecord.setValue('childCaseEndDate', toVariant(self.edtChildCaseEndDate.date()))
            else:
                self.disabilityRecord.setValue('childCaseBegDate', None)
                self.disabilityRecord.setValue('childCaseEndDate', None)
                
            if self.chkCaseDateIndef.isChecked():
                self.disabilityRecord.setValue('caseDateDueTo', None)
            else:
                self.disabilityRecord.setValue('caseDateDueTo', toVariant(self.edtCaseDateDueTo.date()))
            if self.edtReasonNote.isVisible():
                self.disabilityRecord.setValue('reasonNote', toVariant(self.edtReasonNote.text()))
            else:
                self.disabilityRecord.setValue('reasonNote', '')
        return record


    def checkDataEntered(self):
        
        def validateField(field, message, fieldObject):
            if not field:
                result = self.checkInputMessage(message, False, fieldObject)
                return False
            return True

        result = True

        fieldsToValidate = [
            (self.cmbReceiver.value(), u'получателя', self.cmbReceiver),
            (self.cmbSetType.currentIndex() >= 0, u'тип установления инвалидности', self.cmbSetType),
            (self.cmbGroup.value(), u'группу инвалидности', self.cmbGroup),
            (self.cmbReason.value(), u'причину', self.cmbReason),
            (self.edtCaseBegDate.date(), u'дату начала инвалидности', self.edtCaseBegDate),
            (self.edtDiagnosis.text(), u'диагноз', self.edtDiagnosis)
        ]

        for field, message, fieldObject in fieldsToValidate:
            if not validateField(field, message, fieldObject):
                return False
        if not self.checkActualMKB():
            return False   
        if self.edtNextCase.date() and self.edtNextCase.date() < QDate.currentDate():
            self.checkValueMessage(u'Дата очередного освидетельствования не может быть раньше текущей даты', False, self.edtNextCase)
            return False
        if self.cmbSkipCaseReason.currentIndex() > 0:
            if self.edtSkipCaseBegDate.date() and self.edtSkipCaseBegDate.date() >= QDate.currentDate():
                self.checkValueMessage(u'Дата начала периода пропуска срока освидетельствования не может быть текущей или позже текущей', False, self.edtSkipCaseBegDate)
                return False
            if self.edtSkipCaseEndDate.date() and self.edtSkipCaseEndDate.date() >= QDate.currentDate():
                self.checkValueMessage(u'Дата окончания периода пропуска срока освидетельствования не может быть текущей или позже текущей', False, self.edtSkipCaseEndDate)
                return False
            if self.edtSkipCaseBegDate.date() and self.edtSkipCaseEndDate.date() and self.edtSkipCaseBegDate.date() > self.edtSkipCaseEndDate.date():
                self.checkValueMessage(u'Дата начала периода пропуска срока освидетельствования не может быть больше даты окончания', False, self.edtSkipCaseBegDate)
                return False
        if self.chkChildCase.isChecked():
            if self.edtChildCaseBegDate.date() and self.edtChildCaseBegDate.date() >= QDate.currentDate():
                self.checkValueMessage(u'Дата начала установления инвалидности "ребенок-инвалид" не может быть текущей или позже текущей', False, self.edtChildCaseBegDate)
                return False
            if self.edtChildCaseEndDate.date() and self.edtChildCaseEndDate.date() >= QDate.currentDate():
                self.checkValueMessage(u'Дата окончания установления инвалидности "ребенок-инвалид" не может быть текущей или позже текущей', False, self.edtChildCaseEndDate)
                return False
            if self.edtChildCaseBegDate.date() and self.edtChildCaseBegDate.date() and self.edtChildCaseBegDate.date() > self.edtChildCaseBegDate.date():
                self.checkValueMessage(u'Дата начала установления инвалидности "ребенок-инвалид" не может быть больше даты окончания', False, self.edtChildCaseBegDate)
                return False
        result = self.checkDocuments()
        return result

    
    def checkDocuments(self):
        items = self.modelDocuments.items()
        for row, item in enumerate(items):
            res = True
            orgId = forceInt(item.value('org_id'))
            serial = forceStringEx(item.value('serial'))
            number = forceStringEx(item.value('number'))
            issueDate = forceDate(item.value('issueDate'))
            examNumber = forceString(item.value('examinationActNumber'))
            examDate = forceDate(item.value('examinationDate'))
            
            duplicate = forceBool(item.value('duplicate'))
            duplicateReason = forceInt(item.value('duplicateReason_id'))
            if not orgId:
                self.checkInputMessage(u'Орган выдачи', False, self.tblDocuments, row, item.indexOf('org_id'))
                return False
            if not number:
                self.checkInputMessage(u'Номер документа', False, self.tblDocuments, row, item.indexOf('number'))
                return False
            if not serial:
                self.checkInputMessage(u'Серия документа', False, self.tblDocuments, row, item.indexOf('serial'))
                return False
            if not issueDate:
                self.checkInputMessage(u'Дата выдачи документа', False, self.tblDocuments, row, item.indexOf('issueDate'))
                return False
            if not examNumber:
                self.checkInputMessage(u'Номер акта освидетельствования', False, self.tblDocuments, row, item.indexOf('examinationActNumber'))
                return False
            if not examDate:
                self.checkInputMessage(u'Дата акта освидетельствования', False, self.tblDocuments, row, item.indexOf('examinationDate'))
                return False
            elif self.edtCaseBegDate.date() and issueDate < self.edtCaseBegDate.date():
                res = res and self.checkValueMessage(u'Дата выдачи документа не может быть раньше даты начала инвалидности', False, self.tblDocuments, row, item.indexOf('issueDate'))
            if duplicate and not duplicateReason:
                res = res and self.checkInputMessage(u'Причина выдачи дубликата', False, self.tblDocuments, row, item.indexOf('duplicateReason'))
        return res
    

    def checkActualMKB(self):
        result = True
        MKB = unicode(self.edtDiagnosis.text())
        result = result and (MKB or self.checkInputMessage(u'диагноз', False, self.edtDiagnosis))
        if MKB:
            begDate = forceDate(self.edtCaseBegDate.date())
            db = QtGui.qApp.db
            tableMKB = db.table('MKB')
            cond = [tableMKB['DiagID'].eq(MKBwithoutSubclassification(MKB))]
            cond.append(db.joinOr([tableMKB['endDate'].isNull(), tableMKB['endDate'].dateGe(begDate)] ))
            recordMKB = db.getRecordEx(tableMKB, [tableMKB['DiagID']], cond)
            result = result and (forceString(recordMKB.value('DiagID')) == MKBwithoutSubclassification(MKB) if recordMKB else False) or self.checkValueMessage(u'Диагноз %s не доступен для применения'%MKB, False, self.edtDiagnosis)
        return result


    def getMKBs(self):
        if self.diagnosisId:
            db = QtGui.qApp.db
            record = db.getRecord('Diagnosis', '*', self.diagnosisId)
            if record:
               return forceString(record.value('MKB')), forceString(record.value('MKBEx')), forceRef(record.value('character_id'))
        return '', '', None


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
        result._doctype = context.getInstance(CTempInvalidDocTypeInfo,  self.cmbGroup.value())
        result._client = context.getInstance(CClientInfo, self.cmbReceiver.value())
        MKB, MKBEx, characterId = self.getMKBs()
        result._MKB = context.getInstance(CMKBInfo, MKB)
        result._MKBEx = context.getInstance(CMKBInfo, MKBEx)
        result._caseBegDate = CDateInfo(self.edtCaseBegDate.date())
        result._receiver = context.getInstance(CClientInfo, self.cmbReceiver.value())

        result._items = self.modelDocuments.getDocumentsInfo(context)
        if self.prevId:
            result._prev = context.getInstance(CTempInvalidInfo, self.prevId)
        else:
            result._prev = None
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


    @pyqtSignature('int')
    def on_cmbSetType_currentIndexChanged(self, index):
        pass


    @pyqtSignature('int')
    def on_cmbReason_currentIndexChanged(self, index):
        if self.cmbReason.code() in ['16', '17']:
            self.edtReasonNote.setVisible(True)
            self.lblReasonNote.setVisible(True)
        else:
            self.edtReasonNote.setVisible(False)
            self.lblReasonNote.setVisible(False)
            self.edtReasonNote.setText("")
    
    
    @pyqtSignature('int')
    def on_cmbSkipCaseReason_currentIndexChanged(self, index):
        self.edtSkipCaseBegDate.setEnabled(bool(index))
        self.edtSkipCaseEndDate.setEnabled(bool(index))
    

    def save(self):
        tempInvalidId = CItemEditorBaseDialog.save(self)
        if tempInvalidId:
            self.modelDocuments.saveItems(tempInvalidId)
        db = QtGui.qApp.db
        db.transaction()
        try:
            table = db.table('TempInvalid_Disability')
            if not self.disabilityRecord:
                self.disabilityRecord = table.newRecord()
                self.disabilityRecord.setValue('master_id', self.getRecord().value('id'))
            id = db.insertOrUpdate(table, self.disabilityRecord)
            db.commit()
        except:
            db.rollback()
            raise
        return tempInvalidId


    def createContinuation(self):
        document = self.tblDocuments.currentItem()
        if document:
            self.cmbSetType.setCurrentIndex(1) #повторно
            self.cmbGroup.setValue(None)
            self.cmbReason.setValue(None)
            self.edtReasonNote.setText('')
            self.edtReasonNote.setVisible(False)
            self.lblReasonNote.setVisible(False)
            self.edtCaseDateDueTo.setDate(QDate())
            self.chkCaseDateIndef.setChecked(False)
            self.edtNextCase.setDate(QDate())
            self.edtSkipCaseBegDate.setDate(QDate())
            self.edtSkipCaseEndDate.setDate(QDate())
            self.cmbSkipCaseReason.setCurrentIndex(0)
            
            continuation = self.modelDocuments.getEmptyRecord()
            continuation.setValue('org_id', forceInt(document.value('org_id')))
            continuation.setValue('serial', '')
            continuation.setValue('number', '')
            continuation.setValue('issueDate',  QDate())
            #continuation.setValue('busyness',   document.value('busyness'))
            #continuation.setValue('placeWork',  document.value('placeWork'))
            continuation.setValue('prevNumber', forceInt(document.value('number')))
            continuation.setValue('prev_id', forceInt(document.value('id')))
            self.modelDocuments.addRecord(continuation)
            if document.value('id') and forceString(document.value('id')) not in self.modelDocuments.prevIds:
                self.modelDocuments.prevIds.append(forceString(document.value('id')))


    @pyqtSignature('')
    def on_tblDocuments_popupMenuAboutToShow(self):
        document = self.tblDocuments.currentItem()
        if document:
            number = forceString(document.value('number'))
            annulmentReasonId = forceRef(document.value('annulmentReason_Id'))
        else:
            number = None
            annulmentReasonId = None
        self.actProlong.setEnabled(bool(number) and not annulmentReasonId and number not in self.modelDocuments.prevIds)
        self.actDuplicate.setEnabled(bool(number) and not annulmentReasonId)
        self.actDelete.setEnabled(number not in self.modelDocuments.prevIds)


    @pyqtSignature('')
    def on_actProlong_triggered(self):
        self.createContinuation()
    
    
    @pyqtSignature('')
    def on_actDelete_triggered(self):
        self.deleteDocument()


    @pyqtSignature('')
    def on_actDuplicate_triggered(self):
        self.createDuplicate()


    def createDuplicate(self):
        reasons = {u'Смена фамилии': 1, 
                   u'Утрата справки': 2, 
                   u'Порча справки': 3}
        duplicateReason, ok = QtGui.QInputDialog.getItem(self,
                                                u'Создать дубликат',
                                                u'Причина получения дубликата',
                                                reasons.keys(),
                                                0,
                                                False)
        document = self.tblDocuments.currentItem()
        if document and ok:
            self.cmbSetType.setCurrentIndex(1) #повторно
            self.cmbGroup.setValue(None)
            self.cmbReason.setValue(None)
            self.edtReasonNote.setText('')
            self.edtReasonNote.setVisible(False)
            self.lblReasonNote.setVisible(False)
            self.edtCaseDateDueTo.setDate(QDate())
            self.chkCaseDateIndef.setChecked(False)
            self.edtNextCase.setDate(QDate())
            self.edtSkipCaseBegDate.setDate(QDate())
            self.edtSkipCaseEndDate.setDate(QDate())
            self.cmbSkipCaseReason.setCurrentIndex(0)
            
            continuation = self.modelDocuments.getEmptyRecord()
            continuation.setValue('org_id', forceInt(document.value('org_id')))
            continuation.setValue('serial', document.value('serial'))
            continuation.setValue('number', document.value('number'))
            continuation.setValue('issueDate', document.value('issueDate'))
            #continuation.setValue('busyness',   document.value('busyness'))
            #continuation.setValue('placeWork',  document.value('placeWork'))
            continuation.setValue('duplicate', True)
            continuation.setValue('issueDate', document.value('issueDate'))
            continuation.setValue('prevNumber', document.value('number'))
            continuation.setValue('prev_id', document.value('id'))
            continuation.setValue('duplicateReason_id', reasons[forceString(duplicateReason)])
            self.modelDocuments.addRecord(continuation)
            if document.value('id') and forceString(document.value('id')) not in self.modelDocuments.prevIds:
                self.modelDocuments.prevIds.append(forceString(document.value('id')))


    def deleteDocument(self):
        documentRow = self.tblDocuments.getSelectedRows()
        document = self.tblDocuments.currentItem()
        if documentRow:
            if forceString(document.value('prev_id')) in self.modelDocuments.prevIds:
                self.modelDocuments.prevIds.remove(forceString(document.value('prev_id')))
            self.modelDocuments.removeRow(documentRow[-1])


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
        return


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelDocuments_currentRowChanged(self, current, previous):
        return


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


class CTempDisabilityDocumentsModel(CInDocTableModel):
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
                

    Col_Org = 0
    Col_Serial = 1
    Col_Number = 2
    Col_BegDate = 3
    Col_DocNumber = 4
    Col_DocBegDate = 5
    Col_Duplicate = 6
    Col_DuplicateReason = 7

    def __init__(self, parent, clientCache):
        CInDocTableModel.__init__(self, 'TempInvalidDocument', 'id', 'master_id', parent)
        self.addCol(COrgInDocTableCol(u'Орган выдачи', 'org_id', 30))
        self.addCol(CInDocTableCol(u'Серия', 'serial', 22))
        self.addCol(CInDocTableCol(u'Номер', 'number', 22,  maxLength=12, inputMask='999999999999;'))
        self.addCol(CTempDisabilityDocumentsModel.CIssueDateInDocTableCol( u'Дата выдачи', 'issueDate', 10))
        self.addCol(CInDocTableCol(u'№ акта освидетельствования', 'examinationActNumber', 15).setToolTip(u'№ акта освидетельствования'))
        self.addCol(CDateInDocTableCol(u'Дата освидетельствования', 'examinationDate', 50).setToolTip(u'Дата освидетельствования'))
        self.addCol(CBoolInDocTableCol(u'Д', 'duplicate', 3).setToolTip(u'Дубликат')).setReadOnly(True)
        self.addCol(CRBInDocTableCol(u'Причина выдачи дубликата', 'duplicateReason_id', 10, 'rbTempInvalidDuplicateReason')).setReadOnly(True)
        self.addHiddenCol('prevNumber')
        self.addHiddenCol('prev_id')
        self.prevIds = []


    def getEmptyRecord(self):
        result = CInDocTableModel.getEmptyRecord(self)
        result.append(QtSql.QSqlField('prevDuplicate_id', QVariant.Int))
        if QtGui.qApp.userSpecialityId:
            result.setValue('person_id', toVariant(QtGui.qApp.userId))
            if forceBool(result.value('duplicate')):
                result.setValue('execPerson_id', toVariant(QtGui.qApp.userId))
        return result


    def getTempInvalidDocumentIdList(self):
        idList = []
        for item in self._items:
            id = forceRef(item.value('id'))
            if id and id not in idList:
                idList.append(id)
        return idList


    def loadItems(self, tempInvalidId):
        CInDocTableModel.loadItems(self, tempInvalidId)
        for item in self._items:
            prevId = forceString(item.value('prev_id'))
            if prevId and prevId not in self.prevIds:
                self.prevIds.append(prevId)


    def saveItems(self, masterId):
        if self._items is not None:
            CInDocTableModel.saveItems(self, masterId)
            

    def getDocumentsInfo(self, context):
        result = context.getInstance(CTempInvalidDocumentItemInfoList, None)
        for i, item in enumerate(self.items()):
            id = forceRef(item.value('id'))
            result.addItem(id or -i-1, item)
        return result


