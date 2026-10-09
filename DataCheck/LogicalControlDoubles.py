# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2023 SAMSON Group. All rights reserved.
##  #chkNameClient
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, pyqtSignature, SIGNAL, QDateTime

from library.DialogBase        import CConstructHelperMixin, CDialogBase
from library.Utils             import forceDate, forceDateTime, forceInt, forceRef, forceString, forceTime

from Registry.ClientEditDialog import CClientEditDialog
from Registry.Utils            import getClientCompulsoryPolicy, getClientDocument, getClientVoluntaryPolicy
from Reports.ReportBase        import createTable, CReportBase
from Reports.ReportView        import CReportViewDialog
from Users.Rights              import urAdmin, urRegTabReadRegistry, urRegTabWriteRegistry
from DataCheck.ClientsRelationsInfo import CClientsRelationsInfo

from DataCheck.Ui_LogicalControlDoubles       import Ui_LogicalControlDoubles
from DataCheck.Ui_WarningControlDublesDialog  import Ui_WarningControlDublesDialog
from DataCheck.Ui_CorrectsControlDublesDialog import Ui_CorrectsControlDublesDialog
from DataCheck.Ui_CorrectBaseLineDialog       import Ui_CorrectBaseLineDialog


class CControlDoubles(QtGui.QDialog, CConstructHelperMixin, Ui_LogicalControlDoubles):
    def __init__(self, parent, clientId = None, clientIdList = []):
        QtGui.QDialog.__init__(self, parent)
        self.addObject('actFirstRecordTake', QtGui.QAction(u'Удаление дублей, базовая - первая запись', self))
        self.addObject('actLastRecordTake', QtGui.QAction(u'Удаление дублей, базовая - последняя запись', self))
        self.addObject('actOpenDocumentCorrect', QtGui.QAction(u'Открыть документ', self))
        self.addObject('actClientsInfo', QtGui.QAction(u'Информация о пациентах', self))
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.prbControlDoubles.setFormat('%v')
        self.prbControlDoubles.setValue(0)
        self.registryClientId = clientId
        self.registryClientIdList = clientIdList
        self.abortProcess = False
        self.checkRun = False
        self.lastRowTake = False
        self.booleanNewTuning = True
        self.bufferRecords = []
        self.bufferCorrectClientIds = []
        self.bufferCorrectDocumentIds = []
        self.bufferCorrectPolicyIds = []
        self.recordsCorrectClient = []
        self.bufferCorrectRowList = []
        self.tempPrintList = []
        self.basicFont = None
        self.findLikeStings = None
        self.booleanNameClient = False
        self.booleanBirthDateClient = False
        self.booleanSexClient = False
        self.booleanSNILSClient = False
        self.booleanDocumentsClient = False
        self.booleanPolicyClient = False
        self.btnNewTuning.setEnabled(False)
        self.btnPrint.setEnabled(False)
        self.rows = 0
        self.errorStr = u''
        self.tblDoubleClients.createPopupMenu([self.actFirstRecordTake, self.actLastRecordTake, self.actOpenDocumentCorrect, u'-', self.actClientsInfo])
        self.connect(self.tblDoubleClients._popupMenu, SIGNAL('aboutToShow()'), self.popupMenuAboutToShow)
        

    def rel(self, a, b):
        stmt = """SELECT cr.relative_id FROM ClientRelation cr
  inner JOIN (SELECT cr.relative_id,cr.client_id FROM ClientRelation cr
  WHERE cr.deleted=0 and (cr.client_id=%(a)s  OR cr.relative_id=%(a)s)) AS q ON cr.relative_id=q.relative_id OR cr.client_id=q.client_id
  WHERE cr.deleted=0 and (cr.client_id=%(b)s  OR cr.relative_id=%(b)s)
                  """
        st=stmt %{"a": a,"b": b}
        query = QtGui.qApp.db.query(st)
        record = None
        if query and query.first():
            record = query.record()
        return record


    def changeDataClientsId(self):
        if self.bufferCorrectClientIds != [] and self.bufferCorrectRowList != []:
            self.recordsCorrectClient = []
            bufferCorrectItemsList = []
            rowList = 0
            fontString = QtGui.QFont()
            fontString.setWeight(75)
            self.controlDoubleClients(self.bufferCorrectClientIds, self.bufferCorrectDocumentIds, self.bufferCorrectPolicyIds)
            for row in self.bufferCorrectRowList:
                bufferCorrectItemsList.append(self.tblDoubleClients.item(row))
            for itemList in bufferCorrectItemsList:
                rowList = self.tblDoubleClients.row(itemList)
                clientId = forceRef(self.bufferRecords[rowList].value('clientId'))
                if clientId in self.bufferCorrectClientIds:
                    if len(self.bufferRecords) > rowList:
                        self.tblDoubleClients.takeItem(rowList)
                        self.bufferRecords.pop(rowList)
            for bufferCorrectClient in self.recordsCorrectClient:
                resultStr = u''
                resultStr = self.aggregateString(bufferCorrectClient)
                itemRec = None
                if len(self.bufferRecords) > rowList:
                    self.tblDoubleClients.insertItem(rowList, resultStr)
                    itemRec = self.tblDoubleClients.item(rowList)
                    itemRec.setFont(fontString)
                    self.findLikeStings.append(itemRec)
                    self.bufferRecords.insert(rowList, bufferCorrectClient)
                else:
                    self.tblDoubleClients.addItem(resultStr)
                    findLikeSting = self.tblDoubleClients.findItems(resultStr, Qt.MatchContains)
                    for likeString in findLikeSting:
                        likeString.setFont(fontString)
                        self.findLikeStings.append(likeString)
                    self.bufferRecords.append(bufferCorrectClient)
            self.rows = self.tblDoubleClients.count()
            self.tblDoubleClients.reset()
#            self.tblDoubleClients.model().reset()
            self.lblCountRecords.setText(forceString(self.rows))


    @pyqtSignature('')
    def on_btnPrint_clicked(self):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Контроль двойников')
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertText(u'Фильтр по: ')
        if self.chkLastNameClient.isChecked():
            cursor.insertText(u' %s,'%(self.chkLastNameClient.text()))
        if self.chkFirstNameClient.isChecked():
            cursor.insertText(u' %s,'%(self.chkFirstNameClient.text()))
        if self.chkPatrNameClient.isChecked():
            cursor.insertText(u' %s,'%(self.chkPatrNameClient.text()))
        if self.chkSexClient.isChecked():
            cursor.insertText(u' %s,'%(self.chkSexClient.text()))
        if self.chkBirthDateClient.isChecked():
            cursor.insertText(u' %s,'%(self.chkBirthDateClient.text()))
        if self.chkDocumentsClient.isChecked():
            cursor.insertText(u' %s,'%(self.chkDocumentsClient.text()))
        if self.chkPolicyClient.isChecked():
            cursor.insertText(u' %s,'%(self.chkPolicyClient.text()))
        if self.chkSNILSClient.isChecked():
            cursor.insertText(u' %s,'%(self.chkSNILSClient.text()))
        cursor.insertText(u'\nОтчёт составлен: ' + forceString(QDateTime.currentDateTime()))
        cursor.insertBlock()
        tableColumns = [('5%', [u'Номер'], CReportBase.AlignLeft),
                        ('10%', [u'Фамилия'], CReportBase.AlignLeft),
                        ('10%', [u'Имя'], CReportBase.AlignLeft),
                        ('10%', [u'Отчество'], CReportBase.AlignLeft),
                        ('5%',  [u'Пол'], CReportBase.AlignLeft),
                        ('5%',  [u'Дата рождения'], CReportBase.AlignLeft),
                        ('10%', [u'Документы'], CReportBase.AlignLeft),
                        ('20%', [u'Полис'], CReportBase.AlignLeft),
                        ('5%',  [u'СНИЛС'], CReportBase.AlignLeft), 
                        ('5%',  [u'Автор записи'], CReportBase.AlignLeft), 
                        ('3%',  [u'Дата создания'], CReportBase.AlignLeft),
                        ('2%',  [u'Время создания'], CReportBase.AlignLeft),
                        ('5%',  [u'Автор изменения'], CReportBase.AlignLeft), 
                        ('3%',  [u'Дата изменения'], CReportBase.AlignLeft),
                        ('2%',  [u'Время изменения'], CReportBase.AlignLeft)
                        ]
        table = createTable(cursor, tableColumns)
        for tempPrint in self.tempPrintList:
            iTableRow = table.addRow()
            for i, val in enumerate(tempPrint):
                table.setText(iTableRow, i, val)
        html = doc.toHtml('utf-8')
        view = CReportViewDialog(self)
        view.setText(html)
        view.exec_()


    @pyqtSignature('')
    def on_actFirstRecordTake_triggered(self):
        if not self.booleanNewTuning:
            self.lastRowTake = False
            self.firstRecordTake()
        else:
            QtGui.QMessageBox.warning(self,
                                      u'Внимание!',
                                      u'Вы изменили условие выбора. Обновите данные.',
                                      QtGui.QMessageBox.Ok,
                                      QtGui.QMessageBox.Ok)


    @pyqtSignature('')
    def on_actLastRecordTake_triggered(self):
        if not self.booleanNewTuning:
            self.lastRowTake = True
            self.firstRecordTake()
        else:
            QtGui.QMessageBox.warning(self,
                                      u'Внимание!',
                                      u'Вы изменили условие выбора. Обновите данные.',
                                      QtGui.QMessageBox.Ok,
                                      QtGui.QMessageBox.Ok)


    def isLockedAnyEvent(self, bufferRecordsDoubleLines, messageDouble):
        db = QtGui.qApp.db
        for recordDoubleLine in bufferRecordsDoubleLines:
            clientId = forceRef(recordDoubleLine.value('clientId'))
            tableAppLock_Detail = db.table('AppLock_Detail')
            tableEvent          = db.table('Event')
            tableAppLock        = db.table('AppLock')
            tableAppLock_Detail = tableAppLock_Detail.leftJoin(tableEvent , tableEvent['id'].eq(tableAppLock_Detail['recordId']))
            tableAppLock_Detail = tableAppLock_Detail.leftJoin(tableAppLock, tableAppLock['id'].eq(tableAppLock_Detail['master_id']))
            cond = [tableAppLock_Detail['tableName'].eq('Event'),
                    tableEvent['client_id'].eq(clientId)]
            recordList = db.getRecordList(tableAppLock_Detail, 'AppLock_Detail.*', where=cond)
            for record in recordList:
                appLockId = forceRef(record.value('master_id'))
                recordId  = forceRef(record.value('recordId'))
                lockRecord = db.getRecord('AppLock', ['lockTime', 'retTime', 'person_id', 'addr'], appLockId)
                if lockRecord:
                    retTime  = forceDateTime(lockRecord.value('retTime'))
                    if retTime.secsTo(QDateTime.currentDateTime()) < 300:
                        lockTime = forceDateTime(lockRecord.value('lockTime'))
                        personId = forceRef(lockRecord.value('person_id'))
                        personName = forceString(
                            db.translate('vrbPersonWithSpeciality', 'id', personId, 'name')) if personId else u'аноним'
                        addr = forceString(lockRecord.value('addr'))
                        lockInfo = lockTime, personName, addr
                        message = u'У удаляемого дубля пациента {}\n{} заблокировано событие(id записи: {}) \nпользователем {}\nс компьютера {}'.format(
                            messageDouble.split(')')[0]+')',
                            forceString(lockInfo[0]),
                            recordId,
                            lockInfo[1],
                            lockInfo[2])

                        QtGui.QMessageBox.critical(QtGui.qApp.mainWindow,
                                                u'Ограничение совместного доступа к данным',
                                                message,
                                                QtGui.QMessageBox.Cancel,
                                                QtGui.QMessageBox.Cancel
                                                )
                        return False
        return True
    
    
    def firstRecordTake(self, rowBaseLine = None):
        self.bufferCorrectClientIds = []
        self.bufferCorrectDocumentIds = []
        self.bufferCorrectPolicyIds = []
        self.bufferCorrectRowList = []
        self.recordsCorrectClient = []
        listItemsSelectControl = self.tblDoubleClients.selectedItems()
        itemsSelect = []
        rowList = -1
        rowLine = 1
        recordsRowList = []
        for itemsSelect in listItemsSelectControl:
            rowList = self.tblDoubleClients.row(itemsSelect)
            recordsRowList.append(rowList)
        recordsRowList.sort(reverse = True if self.lastRowTake else False)
        if rowBaseLine is not None:
            if rowBaseLine in recordsRowList:
                rowIndex = recordsRowList.index(rowBaseLine)
                recordsRowList.pop(rowIndex)
                recordsRowList.insert(0, rowBaseLine)
        self.bufferCorrectRowList = recordsRowList
        messageDouble = u''
        messageBaseLine = u''
        listMessageDouble = []
        bufferRecordsBaseLines = []
        bufferRecordsDoubleLines = []
        selectBaseLineItems = []
        selectBaseLine = []
        baseLineClientId = None
        baseLineDocumentId = None
        baseLinePolicyId = None
        if len(listItemsSelectControl) > 1:
            QtGui.qApp.setWaitCursor()
            try:
                for row in recordsRowList:
                    if rowLine > 1:
                        doubleClientId = forceRef(self.bufferRecords[row].value('clientId'))
                        if doubleClientId:
                            itemDuble = self.tblDoubleClients.item(row)
                            dubleLine = itemDuble.text()
                            messageDouble += dubleLine + u'\n'
                            listMessageDouble.append(dubleLine)
                            selectBaseLineItems.append(dubleLine)
                            selectBaseLine.append(row)
                            doubleDocumentId = forceRef(self.bufferRecords[row].value('documentId'))
                            doublePolicyId = forceRef(self.bufferRecords[row].value('policyId'))
                            if doubleDocumentId and doubleDocumentId not in self.bufferCorrectDocumentIds:
                                self.bufferCorrectDocumentIds.append(doubleDocumentId)
                            if doublePolicyId and doublePolicyId not in self.bufferCorrectPolicyIds:
                                self.bufferCorrectPolicyIds.append(doublePolicyId)
                            if doubleClientId and doubleClientId not in self.bufferCorrectClientIds:
                                self.bufferCorrectClientIds.append(doubleClientId)
                            bufferRecordsDoubleLines.append(self.bufferRecords[row])
                    else:
                        baseLineClientId = forceRef(self.bufferRecords[row].value('clientId'))
                        if baseLineClientId:
                            item = self.tblDoubleClients.item(row)
                            baseLine = item.text()
                            messageBaseLine = baseLine + u'\n'
                            selectBaseLineItems.append(baseLine)
                            selectBaseLine.append(row)
                            baseLineDocumentId = forceRef(self.bufferRecords[row].value('documentId'))
                            baseLinePolicyId = forceRef(self.bufferRecords[row].value('policyId'))
                            if baseLineDocumentId and baseLineDocumentId not in self.bufferCorrectDocumentIds:
                                self.bufferCorrectDocumentIds.append(baseLineDocumentId)
                            if baseLinePolicyId and baseLinePolicyId not in self.bufferCorrectPolicyIds:
                                self.bufferCorrectPolicyIds.append(baseLinePolicyId)
                            if baseLineClientId and baseLineClientId not in self.bufferCorrectClientIds:
                                self.bufferCorrectClientIds.append(baseLineClientId)
                            bufferRecordsBaseLines.append(self.bufferRecords[row])
                    rowLine += 1
            finally:
                QtGui.qApp.restoreOverrideCursor()
            if messageBaseLine != u'' and messageDouble != u'':
                warningDublesDialog = CWarningControlDublesDialog(self, messageBaseLine, messageDouble, selectBaseLineItems, selectBaseLine)
                if warningDublesDialog.exec_():
                    if messageBaseLine != u'' and listMessageDouble != []:
                        resCorrects = CCorrectsControlDublesDialog(self, messageBaseLine, listMessageDouble, bufferRecordsBaseLines, bufferRecordsDoubleLines).exec_()
                        if resCorrects == 1:
                            QtGui.qApp.setWaitCursor()
                            try:
                                self.recordsCorrectClient = []
                                resultStrBaseLine = u''
                                resultStrDoubleLine = u''
                                bufferRecordsBaseLines = []
                                bufferRecordsDoubleLines = []
                                self.controlDoubleClients(self.bufferCorrectClientIds, self.bufferCorrectDocumentIds, self.bufferCorrectPolicyIds, baseLineClientId, baseLineDocumentId, baseLinePolicyId)
                                booleanBaseLineCorrect = False
                                recordsCorrectClientDouble = []
                                for recordCorrectClient in self.recordsCorrectClient:
                                    if baseLineClientId and forceRef(recordCorrectClient.value('clientId')) == baseLineClientId and not booleanBaseLineCorrect:
                                        booleanBaseLineCorrect = True
                                        resultStrBaseLine = self.aggregateString(recordCorrectClient) + u'\n'
                                        bufferRecordsBaseLines = recordCorrectClient
                                    else:
                                        recordsCorrectClientDouble.append(recordCorrectClient)
                                if booleanBaseLineCorrect:
                                    for recordCorrectClientDouble in recordsCorrectClientDouble:
                                        clientIdDouble = forceRef(recordCorrectClientDouble.value('clientId'))
                                        if clientIdDouble:
                                            resultStrDoubleLine += self.aggregateString(recordCorrectClientDouble) + u'\n'
                                            bufferRecordsDoubleLines.append(recordCorrectClientDouble)
                            finally:
                                QtGui.qApp.restoreOverrideCursor()
                            if resultStrBaseLine != u'' and resultStrDoubleLine != u'':
                                warningNextDialog = CWarningControlDublesDialog(self, resultStrBaseLine, resultStrDoubleLine)
                                warningNextDialog.btnSelectBaseLine.setVisible(False)
                                if warningNextDialog.exec_():
                                    QtGui.qApp.setWaitCursor()
                                    try:
                                        db = QtGui.qApp.db
                                        tableClient = db.table('Client')
                                        tableClientDocument = db.table('ClientDocument')
                                        tableClientPolicy = db.table('ClientPolicy')
                                        tableClientAddress = db.table('ClientAddress')
                                        tableClientAttach = db.table('ClientAttach')
                                        tableClientAllergy = db.table('ClientAllergy')
                                        tableClientAttach = db.table('ClientAttach')
                                        tableClientContact = db.table('ClientContact')
                                        tableClientIdentification = db.table('ClientIdentification')
                                        tableClientIntoleranceMedicament = db.table('ClientIntoleranceMedicament')
                                        tableClientSocStatus = db.table('ClientSocStatus')
                                        tableClientWork = db.table('ClientWork')
                                        tableClientFileAttach = db.table('Client_FileAttach')
                                        tableEvent = db.table('Event')
                                        tableClientDT = db.table('Client_DocumentTracking')
                                        tableDiagnosis = db.table('Diagnosis')
                                        tableTempInvalid = db.table('TempInvalid')
                                        tableClientRelation = db.table('ClientRelation')
                                        tableScheduleItem = db.table('Schedule_Item')
                                        tableExternalNotification = db.table('ExternalNotification')
                                        tableClientContingentKind = db.table('ClientContingentKind')
                                        tableClientActiveDispensary = db.table('ClientActiveDispensary')
                                        tableClientDangerous = db.table('ClientDangerous')
                                        tableClientForcedTreatment = db.table('ClientForcedTreatment')
                                        tableClientResearch = db.table('ClientResearch')
                                        tableClientSuicide = db.table('ClientSuicide')
                                        tableClientVaccination = db.table('ClientVaccination')
                                        tableClientVaccinationProbe = db.table('ClientVaccinationProbe')
                                        booleanBaseLine = False
                                        if not booleanBaseLine:
                                            if bufferRecordsBaseLines:
                                                baseClientId = forceRef(bufferRecordsBaseLines.value('clientId'))
                                                baseDocumentId = forceRef(bufferRecordsBaseLines.value('documentId'))
                                                basePolicyId = forceRef(bufferRecordsBaseLines.value('policyId'))
                                                baseAddressRegId = forceRef(bufferRecordsBaseLines.value('addressRegId'))
                                                baseAddressLocId = forceRef(bufferRecordsBaseLines.value('addressLocId'))
                                                booleanBaseLine = True
                                        if booleanBaseLine:
                                            if self.isLockedAnyEvent(bufferRecordsDoubleLines, dubleLine):
                                                for recordDoubleLine in bufferRecordsDoubleLines:
                                                    clientId = forceRef(recordDoubleLine.value('clientId'))
                                                    documentId = forceRef(recordDoubleLine.value('documentId'))
                                                    policyId = forceRef(recordDoubleLine.value('policyId'))
                                                    addressRegId = forceRef(recordDoubleLine.value('addressRegId'))
                                                    addressLocId = forceRef(recordDoubleLine.value('addressLocId'))
                                                    if (clientId and baseClientId) and (clientId != baseClientId):
                                                        db.updateRecords(tableEvent.name(), tableEvent['client_id'].eq(baseClientId), tableEvent['client_id'].eq(clientId))
                                                        db.updateRecords(tableClientFileAttach.name(), tableClientFileAttach['master_id'].eq(baseClientId), tableClientFileAttach['master_id'].eq(clientId))
                                                        db.updateRecords(tableDiagnosis.name(), tableDiagnosis['client_id'].eq(baseClientId), tableDiagnosis['client_id'].eq(clientId))
                                                        db.updateRecords(tableTempInvalid.name(), tableTempInvalid['client_id'].eq(baseClientId), tableTempInvalid['client_id'].eq(clientId))
                                                        relInfo = self.rel(baseClientId, clientId)
                                                        if not relInfo:
                                                            db.updateRecords(tableClientRelation.name(), tableClientRelation['client_id'].eq(baseClientId), tableClientRelation['client_id'].eq(clientId))
                                                            db.updateRecords(tableClientRelation.name(), tableClientRelation['relative_id'].eq(baseClientId), tableClientRelation['relative_id'].eq(clientId))
                                                        tableClientRelation1 = db.table('ClientRelation').alias('CR1')
                                                        tableClientRelation2 = db.table('ClientRelation').alias('CR2')
                                                        queryTable = tableClientRelation1.innerJoin(tableClientRelation2, tableClientRelation2['relativeType_id'].eq(tableClientRelation1['relativeType_id']))
                                                        condCR = [tableClientRelation1['client_id'].eq(baseClientId),
                                                                tableClientRelation1['client_id'].eq(tableClientRelation2['client_id']),
                                                                tableClientRelation1['relative_id'].eq(tableClientRelation2['relative_id']),
                                                                tableClientRelation1['id'].ne(tableClientRelation2['id']),
                                                                tableClientRelation1['deleted'].eq(0),
                                                                tableClientRelation2['deleted'].eq(0)
                                                                ]
                                                        idListCR = db.getDistinctIdList(queryTable, [tableClientRelation1['id']], condCR, u'CR1.id DESC')
                                                        condRC = [tableClientRelation1['relative_id'].eq(baseClientId),
                                                                tableClientRelation1['relative_id'].eq(tableClientRelation2['relative_id']),
                                                                tableClientRelation1['client_id'].eq(tableClientRelation2['client_id']),
                                                                tableClientRelation1['id'].ne(tableClientRelation2['id']),
                                                                tableClientRelation1['deleted'].eq(0),
                                                                tableClientRelation2['deleted'].eq(0)
                                                                ]
                                                        idListRC = db.getDistinctIdList(queryTable, [tableClientRelation1['id']], condRC, u'CR1.id DESC')
                                                        idListResRC = list(set(idListCR) | set(idListRC))
                                                        idListResRC.sort(reverse=False)
                                                        for rowId, CRId in enumerate(idListResRC):
                                                            if CRId and rowId:
                                                                db.deleteRecord(tableClientRelation, tableClientRelation['id'].eq(CRId))
                                                        db.updateRecords(tableScheduleItem.name(), tableScheduleItem['client_id'].eq(baseClientId), tableScheduleItem['client_id'].eq(clientId))
                                                        db.updateRecords(tableClientDT.name(), tableClientDT['client_id'].eq(baseClientId), tableClientDT['client_id'].eq(clientId))
                                                        db.updateRecords(tableClientContact.name(), tableClientContact['client_id'].eq(baseClientId), tableClientContact['client_id'].eq(clientId))
                                                        db.updateRecords(tableExternalNotification.name(), tableExternalNotification['client_id'].eq(baseClientId), tableExternalNotification['client_id'].eq(clientId))
                                                        db.updateRecords(tableClientContingentKind.name(), tableClientContingentKind['client_id'].eq(baseClientId), tableClientContingentKind['client_id'].eq(clientId))
                                                        db.updateRecords(tableClientActiveDispensary.name(), tableClientActiveDispensary['client_id'].eq(baseClientId), tableClientActiveDispensary['client_id'].eq(clientId))
                                                        db.updateRecords(tableClientDangerous.name(), tableClientDangerous['client_id'].eq(baseClientId), tableClientDangerous['client_id'].eq(clientId))
                                                        db.updateRecords(tableClientForcedTreatment.name(), tableClientForcedTreatment['client_id'].eq(baseClientId), tableClientForcedTreatment['client_id'].eq(clientId))
                                                        db.updateRecords(tableClientResearch.name(), tableClientResearch['client_id'].eq(baseClientId), tableClientResearch['client_id'].eq(clientId))
                                                        db.updateRecords(tableClientSuicide.name(), tableClientSuicide['client_id'].eq(baseClientId),tableClientSuicide['client_id'].eq(clientId))
                                                        db.updateRecords(tableClientAttach.name(),  tableClientAttach['client_id'].eq(baseClientId), tableClientAttach['client_id'].eq(clientId))
                                                        db.updateRecords(tableClientVaccination.name(), tableClientVaccination['client_id'].eq(baseClientId), tableClientVaccination['client_id'].eq(clientId))
                                                        db.updateRecords(tableClientVaccinationProbe.name(),  tableClientVaccinationProbe['client_id'].eq(baseClientId), tableClientVaccinationProbe['client_id'].eq(clientId))
                                                        db.deleteRecord(tableClientDocument, tableClientDocument['client_id'].eq(clientId))
                                                        db.deleteRecord(tableClientPolicy, tableClientPolicy['client_id'].eq(clientId))
                                                        db.deleteRecord(tableClientAddress, tableClientAddress['client_id'].eq(clientId))
                                                        db.deleteRecord(tableClientAllergy, tableClientAllergy['client_id'].eq(clientId))
                                                        db.deleteRecord(tableClientContact, tableClientContact['client_id'].eq(clientId))
                                                        db.deleteRecord(tableClientIdentification, tableClientIdentification['client_id'].eq(clientId))
                                                        db.deleteRecord(tableClientIntoleranceMedicament, tableClientIntoleranceMedicament['client_id'].eq(clientId))
                                                        db.deleteRecord(tableClientSocStatus, tableClientSocStatus['client_id'].eq(clientId))
                                                        db.deleteRecord(tableClientWork, tableClientWork['client_id'].eq(clientId))
                                                        db.deleteRecord(tableClient, tableClient['id'].eq(clientId))
                                                    else:
                                                        if (clientId and baseClientId):
                                                            if (baseDocumentId and documentId) and (baseDocumentId != documentId):
                                                                db.deleteRecord(tableClientDocument, tableClientDocument['id'].eq(documentId))
                                                            if (basePolicyId and policyId) and (basePolicyId != policyId):
                                                                db.deleteRecord(tableClientPolicy, tableClientPolicy['id'].eq(policyId))
                                                            if (baseAddressRegId and addressRegId) and (baseAddressRegId != addressRegId):
                                                                db.deleteRecord(tableClientAddress, tableClientAddress['id'].eq(addressRegId))
                                                            if (baseAddressLocId and addressLocId) and (baseAddressLocId != addressLocId):
                                                                db.deleteRecord(tableClientAddress, tableClientAddress['id'].eq(addressLocId))
                                            else:
                                                QtGui.QMessageBox.warning(self,
                                                          u'Внимание!',
                                                          u"Дубль пациента не был удалён",
                                                          QtGui.QMessageBox.Cancel,
                                                          QtGui.QMessageBox.Cancel)
                                    finally:
                                        QtGui.qApp.restoreOverrideCursor()
                            else:
                                messageAdd = u''
                                if resultStrBaseLine == u'':
                                   messageAdd = u'Отсутствует основная строка.'
                                elif resultStrDoubleLine == u'':
                                    messageAdd = u'Отсутствуют дубли.'
                                QtGui.QMessageBox.warning(self,
                                                          u'Внимание!',
                                                          messageAdd,
                                                          QtGui.QMessageBox.Cancel,
                                                          QtGui.QMessageBox.Cancel)
                        self.changeDataClientsId()
                elif warningDublesDialog.rowBaseLine is not None:
                    self.firstRecordTake(warningDublesDialog.rowBaseLine)
                    warningDublesDialog = None


    @pyqtSignature('')
    def on_actOpenDocumentCorrect_triggered(self):
        if not self.booleanNewTuning:
            QtGui.qApp.callWithWaitCursor(self, self.openDocumentCorrectTriggered)
        else:
            QtGui.QMessageBox.warning(self,
                                      u'Внимание!',
                                      u'Вы изменили условие выбора. Обновите данные.',
                                      QtGui.QMessageBox.Ok,
                                      QtGui.QMessageBox.Ok)


    @pyqtSignature('')
    def on_actClientsInfo_triggered(self):
        clientIdList = []
        listSelectControl = self.tblDoubleClients.selectedItems()
        for itemsSelect in listSelectControl:
            row = self.tblDoubleClients.row(itemsSelect)
            if row > -1:
                record = self.bufferRecords[row]
                clientId = forceRef(record.value('clientId')) if record else None
                if clientId and clientId not in clientIdList:
                    clientIdList.append(clientId)
        if clientIdList:
            dialog = CClientsRelationsInfo(self)
            try:
                #clientIdList = [364247] #
                dialog.loadData(clientIdList)
                dialog.exec_()
            finally:
                dialog.deleteLater()
        else:
            QtGui.QMessageBox.warning(self,
                          u'Внимание!',
                          u'Необходимо выбрать строки.',
                          QtGui.QMessageBox.Ok,
                          QtGui.QMessageBox.Ok)


    def openDocumentCorrectTriggered(self):
        listSelectControl = self.tblDoubleClients.selectedItems()
        itemsSelect = []
        self.bufferCorrectClientIds = []
        self.bufferCorrectDocumentIds = []
        self.bufferCorrectPolicyIds = []
        self.bufferCorrectRowList = []
        rowList = None
        for itemsSelect in listSelectControl:
            rowList = self.tblDoubleClients.row(itemsSelect)
            self.openDocumentClient(rowList)
        self.changeDataClientsId()


    def popupMenuAboutToShow(self):
        if self.actFirstRecordTake:
            self.actFirstRecordTake.setEnabled(True)
        if self.actLastRecordTake:
            self.actLastRecordTake.setEnabled(True)
        if self.actOpenDocumentCorrect:
            self.actOpenDocumentCorrect.setEnabled(True)


    @pyqtSignature('')
    def on_btnEndCheck_clicked(self):
        if self.checkRun:
            self.abortProcess = True
        else:
            self.close()
            QtGui.qApp.emitCurrentClientInfoChanged()


    @pyqtSignature('')
    def on_btnNewTuning_clicked(self):
        self.tempPrintList = []
        self.tblDoubleClients.selectAll()
        self.tblDoubleClients.clear()
        self.booleanNewTuning = True
        self.chkLastNameClient.setEnabled(True)
        self.chkFirstNameClient.setEnabled(True)
        self.chkPatrNameClient.setEnabled(True)
        self.chkSexClient.setEnabled(True)
        self.chkBirthDateClient.setEnabled(True)
        self.chkDocumentsClient.setEnabled(True)
        self.chkPolicyClient.setEnabled(True)
        self.chkSNILSClient.setEnabled(True)
        self.chkBirthDateFilter.setEnabled(True)
        self.edtBirthDateFilterFrom.setEnabled(self.chkBirthDateFilter.isChecked())
        self.edtBirthDateFilterTo.setEnabled(self.chkBirthDateFilter.isChecked())
        self.chkLastNameFilter.setEnabled(True)
        self.edtLastNameFilterFrom.setEnabled(self.chkLastNameFilter.isChecked())
        self.edtLastNameFilterTo.setEnabled(self.chkLastNameFilter.isChecked())
        self.chkLimitFilter.setEnabled(True)
        self.edtLimitFilter.setEnabled(self.chkLimitFilter.isChecked())
        self.btnPrint.setEnabled(False)


    @pyqtSignature('')
    def on_btnBeginCheck_clicked(self):
        if self.checkBirthDateFilter() and self.checkLastNameFilter() and self.checkLimitFilter():
            self.tblDoubleClients.selectAll()
            self.tblDoubleClients.clear()
            self.btnPrint.setEnabled(False)
            self.booleanNameClient = False
            self.booleanBirthDateClient = False
            self.booleanSexClient = False
            self.booleanSNILSClient = False
            self.booleanDocumentsClient = False
            self.booleanPolicyClient = False
            self.basicFont = None
            self.rows = 0
            self.errorStr = u''
            self.duration = 0
            self.bufferRecords = []
            self.bufferCorrectClientIds = []
            self.bufferCorrectDocumentIds = []
            self.bufferCorrectPolicyIds = []
            self.bufferCorrectRowList = []
            self.findLikeStings = None
            self.lblCountRecords.setText(u'0')
            self.chkLastNameClient.setEnabled(False)
            self.chkFirstNameClient.setEnabled(False)
            self.chkPatrNameClient.setEnabled(False)
            self.chkSexClient.setEnabled(False)
            self.chkBirthDateClient.setEnabled(False)
            self.chkDocumentsClient.setEnabled(False)
            self.chkHaveDocumentsClient.setEnabled(False)
            self.chkPolicyClient.setEnabled(False)
            self.chkHavePolicyClient.setEnabled(False)
            self.chkSNILSClient.setEnabled(False)
            self.chkHaveSNILSClient.setEnabled(False)
            self.chkLastNameFilter.setEnabled(False)
            self.edtLastNameFilterFrom.setEnabled(False)
            self.edtLastNameFilterTo.setEnabled(False)
            self.chkBirthDateFilter.setEnabled(False)
            self.edtBirthDateFilterFrom.setEnabled(False)
            self.edtBirthDateFilterTo.setEnabled(False)
            self.chkLimitFilter.setEnabled(False)
            self.edtLimitFilter.setEnabled(False)
            QtGui.qApp._timeoutLogout.stop()
            self.loadDataDiagnosis()
            self.booleanNewTuning = False
            QtGui.qApp._timeoutLogout.setup(QtGui.qApp.getConnectionTimeout() * 60000, timeoutFunc=QtGui.qApp.mainWindow.logoutAndLogin)

    
    @pyqtSignature('bool')
    def on_chkLastNameFilter_toggled(self, checked):
        self.edtLastNameFilterFrom.setFocus()
        
    
    @pyqtSignature('bool')
    def on_chkBirthDateFilter_toggled(self, checked):
        self.edtBirthDateFilterFrom.setFocus()
        
    
    @pyqtSignature('bool')
    def on_chkLimitFilter_toggled(self, checked):
        self.edtLimitFilter.setFocus()
    

    @pyqtSignature('QModelIndex')
    def on_tblDoubleClients_doubleClicked (self, index):
        self.openDocumentClient(index.row())
        self.bufferCorrectClientIds = []
        self.bufferCorrectDocumentIds = []
        self.bufferCorrectPolicyIds = []
        self.bufferCorrectRowList = []


    def openDocumentClient(self, row = -1):
        booleanCorrected = False
        if row > -1:
            row = self.tblDoubleClients.currentRow()
        record = self.bufferRecords[row]
        documentId = forceRef(record.value('documentId'))
        policyId = forceRef(record.value('policyId'))
        if documentId and documentId not in self.bufferCorrectDocumentIds:
            self.bufferCorrectDocumentIds.append(documentId)
        if policyId and policyId not in self.bufferCorrectPolicyIds:
            self.bufferCorrectPolicyIds.append(policyId)
        clientId = forceRef(record.value('clientId'))
        self.bufferCorrectRowList.append(row)
        if clientId and clientId not in self.bufferCorrectClientIds:
            self.bufferCorrectClientIds.append(clientId)
        if clientId and QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]):
            dialog = CClientEditDialog(self)
            if dialog:
                try:
                    dialog.load(clientId)
                    booleanCorrected = dialog.exec_()
                finally:
                    dialog.deleteLater()
        if booleanCorrected:
            listWidgetItem = self.tblDoubleClients.item(row)
            if listWidgetItem:
                listWidgetItem.setFlags(Qt.NoItemFlags)


    @pyqtSignature('QModelIndex')
    def on_tblDoubleClients_clicked (self, index):
        if self.basicFont:
            if self.findLikeStings:
               for likeStrings in self.findLikeStings:
                likeStrings.setFont(self.basicFont)

            listItemsSelectControl = self.tblDoubleClients.selectedItems()
            correctSelect = []
            itemsSelect = []
            rowList = -1
            if len(listItemsSelectControl) == 1:
                for itemsSelect in listItemsSelectControl:
                    rowList = self.tblDoubleClients.row(itemsSelect)
                    correctSelect.append([self.bufferRecords[rowList], rowList])
                for resSelect, row in correctSelect:
                    resultStr = u''
                    resultStrList = []

                    if self.booleanNameClient:
                        lastName = forceString(resSelect.value('lastName'))
                        firstName = forceString(resSelect.value('firstName'))
                        patrName = forceString(resSelect.value('patrName'))
                        resultStrList.append(lastName + u' ' + firstName + u' ' + patrName)

                    if self.booleanBirthDateClient:
                        birthDate = forceString(resSelect.value('birthDate'))
                        resultStrList.append(birthDate)

                    if self.booleanSexClient:
                        sexInt = forceInt(resSelect.value('sex'))
                        if sexInt == 1:
                            sex = u'мужской'
                        elif sexInt == 2:
                              sex = u'женский'
                        else:
                            sex = u'неопределено'
                        resultStrList.append(u' пол: ' + sex)

                    if self.booleanSNILSClient:
                        SNILS = forceString(resSelect.value('SNILS'))
                        if SNILS:
                            resultStr = u'  СНИЛС: ' + SNILS
                            resultStrList.append(resultStr)

                    if self.booleanDocumentsClient:
                        documentId = forceString(resSelect.value('documentId'))
                        nameDocument = forceString(resSelect.value('nameDocument'))
                        serialDocument = forceString(resSelect.value('serialDocument'))
                        numberDocument = forceString(resSelect.value('numberDocument'))
                        if documentId:
                            resultStr = u'  Документ: '
                            if nameDocument:
                                resultStr = nameDocument
                            if serialDocument:
                                resultStr = u' серия: ' + serialDocument
                            if numberDocument:
                                resultStr = u' номер: ' + numberDocument
                            resultStrList.append(resultStr)

                    if self.booleanPolicyClient and not self.booleanDocumentsClient:
                        policyId = forceString(resSelect.value('policyId'))
                        serialPolicy = forceString(resSelect.value('serialPolicy'))
                        numberPolicy = forceString(resSelect.value('numberPolicy'))
                        shortName = forceString(resSelect.value('shortName'))
                        nameTypePolicy = forceString(resSelect.value('nameTypePolicy'))
                        if policyId:
                            resultStr = u'  Полис: '
                            if shortName:
                                resultStr = u' короткое название: ' + shortName
                            if nameTypePolicy:
                                resultStr = u' тип: ' + nameTypePolicy
                            if serialPolicy:
                                resultStr = u' серия: ' + serialPolicy
                            if numberPolicy:
                                resultStr = u' номер: ' + numberPolicy
                            resultStrList.append(resultStr)
                    fontString = QtGui.QFont()
                    fontString.setWeight(75)
                    likeStingsList = []
                    findLikeRowFirstList = {}
                    findLikeRowList = {}
                    self.findLikeStings = []
                    for resultStr in resultStrList:
                        if resultStr != u'':
                            likeStingsList = self.tblDoubleClients.findItems(resultStr, Qt.MatchContains)
                            for likeStings in likeStingsList:
                                findLikeRow = self.tblDoubleClients.row(likeStings)
                                if findLikeRow not in findLikeRowFirstList.keys():
                                    findLikeRowFirstList[findLikeRow] = likeStings
                            break

                    for resultStr in resultStrList:
                        if resultStr != u'':
                            likeStingsList = self.tblDoubleClients.findItems(resultStr, Qt.MatchContains)
                            for likeStings in likeStingsList:
                                findLikeRow = self.tblDoubleClients.row(likeStings)
                                if findLikeRow not in findLikeRowList.keys():
                                    findLikeRowList[findLikeRow] = likeStings
                    resRow = set(findLikeRowFirstList) & set(findLikeRowList)
                    resRowList = list(resRow)
                    for row in resRowList:
                        likeStrings = findLikeRowList.get(row, None)
                        if likeStrings:
                            likeStrings.setFont(fontString)
                            self.findLikeStings.append(likeStrings)

    
    def checkLastNameFilter(self):
        if self.chkLastNameFilter.isChecked():
            if forceString(self.edtLastNameFilterFrom.text()) == '' or forceString(self.edtLastNameFilterTo.text()) == '':
                QtGui.QMessageBox().warning(self, u'Предупреждение',
                                                            u'Для фильтра по фамилиям должны быть заполнены оба поля')
                return False
        return True

    def checkBirthDateFilter(self):
        if self.chkBirthDateFilter.isChecked():
            if not (self.edtBirthDateFilterFrom.date().isValid() and self.edtBirthDateFilterTo.date().isValid()):
                QtGui.QMessageBox().warning(self, u'Предупреждение',
                                                            u'Для фильтра по дате рождения должны быть заполнены оба поля')
                return False
        return True
    
    def checkLimitFilter(self):
        if self.chkLimitFilter.isChecked():
            if forceInt(self.edtLimitFilter.text()) < 1:
                QtGui.QMessageBox().warning(self, u'Предупреждение',
                                                            u'Фильтр по количеству записей должен быть больше нуля')
                return False
        return True

    def controlRegistryDoubleClients(self, listCorrectsClientId = [], listCorrectsDocumentsId = [], listCorrectsPolicysId = [], baseLineClientId = None, baseLineDocumentId = None, baseLinePolicyId = None):
        db = QtGui.qApp.db
        table  = db.table('Client')
        record = db.getRecordEx(table, '*', [table['id'].eq(self.registryClientId), table['deleted'].eq(0)])
        lastName = forceString(record.value('lastName'))
        firstName = forceString(record.value('firstName'))
        patrName  = forceString(record.value('patrName'))
        sexCode   = forceInt(record.value('sex'))
        birthDate = forceDate(record.value('birthDate'))
        SNILS = forceString(record.value('SNILS'))
        documentRecord = getClientDocument(self.registryClientId)
        if documentRecord:
#            documentId = forceRef(documentRecord.value('id'))
            documentTypeId = forceRef(documentRecord.value('documentType_id'))
            serial = forceString(documentRecord.value('serial'))
            number = forceString(documentRecord.value('number'))
#            document = formatDocument(documentTypeId, serial, number)
        policyRecord = getClientCompulsoryPolicy(self.registryClientId)
        if policyRecord:
#            compulsoryPolicyId = forceRef(policyRecord.value('id'))
            compulsoryPolicyTypeId = forceRef(policyRecord.value('policyType_id'))
            compulsoryPolicySerial = forceString(policyRecord.value('serial'))
            compulsoryPolicyNumber = forceString(policyRecord.value('number'))
#            compulsoryPolicy = formatPolicy(     policyRecord.value('insurer_id'),
#                                                 compulsoryPolicySerial,
#                                                 compulsoryPolicyNumber,
#                                                 policyRecord.value('begDate'),
#                                                 policyRecord.value('endDate'),
#                                                 policyRecord.value('name'),
#                                                 policyRecord.value('note')
#                                                 )
        voluntaryPolicyRecord = getClientVoluntaryPolicy(self.registryClientId)
        if voluntaryPolicyRecord:
#            voluntaryPolicyId = forceRef(voluntaryPolicyRecord.value('id'))
            voluntaryPolicyTypeId = forceRef(voluntaryPolicyRecord.value('policyType_id'))
            voluntaryPolicySerial = forceString(voluntaryPolicyRecord.value('serial'))
            voluntaryPolicyNumber = forceString(voluntaryPolicyRecord.value('number'))
#            voluntaryPolicy = formatPolicy(      voluntaryPolicyRecord.value('insurer_id'),
#                                                 voluntaryPolicySerial,
#                                                 voluntaryPolicyNumber,
#                                                 voluntaryPolicyRecord.value('begDate'),
#                                                 voluntaryPolicyRecord.value('endDate'),
#                                                 voluntaryPolicyRecord.value('name'),
#                                                 voluntaryPolicyRecord.value('note')
#                                                 )
        self.recordsCorrectClient = []
        self.booleanNameClient = False
        self.booleanBirthDateClient = False
        self.booleanSexClient = False
        self.booleanSNILSClient = False
        self.booleanDocumentsClient = False
        self.booleanPolicyClient = False
        db = QtGui.qApp.db
        tableClient = db.table('Client').alias('C1')
        tableClientDocument = db.table('ClientDocument').alias('CD1')
        tableClientPolicy = db.table('ClientPolicy').alias('CP1')
        tableDocumentType = db.table('rbDocumentType')
        tableOrganisation = db.table('Organisation')
        tablePolicyType   = db.table('rbPolicyType')
        tableClientAddress = db.table('ClientAddress')
        tableClientAttach = db.table('ClientAttach')

        cols = [tableClient['id'].alias('clientId'),
               tableClient['lastName'],
               tableClient['firstName'],
               tableClient['patrName'],
               tableClient['birthDate'],
               tableClient['sex'],
               tableClient['SNILS'], 
               tableClient['createPerson_id'], 
               tableClient['createDatetime'].alias('createDate'),
               tableClient['createDatetime'].alias('createTime'),
               tableClient['modifyPerson_id'], 
               tableClient['modifyDatetime'].alias('modifyDate'),
               tableClient['modifyDatetime'].alias('modifyTime')
               ]
        cols.append('''(IF(CD1.id IS NOT NULL AND CD1.deleted = 0, CD1.id, NULL)) AS documentId''')
        cols.append('''(IF(CD1.id IS NOT NULL AND CD1.deleted = 0, rbDocumentType.name, '')) AS nameDocument''')
        cols.append('''(IF(CD1.id IS NOT NULL AND CD1.deleted = 0, CD1.serial, '')) AS serialDocument''')
        cols.append('''(IF(CD1.id IS NOT NULL AND CD1.deleted = 0, CD1.number, '')) AS numberDocument''')
        cols.append('''(IF(CD1.id IS NOT NULL AND CD1.deleted = 0, CD1.date, NULL)) AS date''')
        cols.append('''(IF(CD1.id IS NOT NULL AND CD1.deleted = 0, CD1.origin, '')) AS origin''')
        cols.append('''(IF(CP1.id IS NOT NULL AND CP1.deleted = 0, CP1.id, NULL)) AS policyId''')
        cols.append('''(IF(CP1.id IS NOT NULL AND CP1.deleted = 0, rbPolicyType.name, '')) AS nameTypePolicy''')
        cols.append('''(IF(CP1.id IS NOT NULL AND CP1.deleted = 0, CP1.serial, '')) AS serialPolicy''')
        cols.append('''(IF(CP1.id IS NOT NULL AND CP1.deleted = 0, CP1.number, '')) AS numberPolicy''')
        cols.append('''(IF(CP1.id IS NOT NULL AND CP1.deleted = 0, CP1.begDate, NULL)) AS begDate''')
        cols.append('''(IF(CP1.id IS NOT NULL AND CP1.deleted = 0, CP1.endDate, NULL)) AS endDate''')
        cols.append('''(IF(CP1.id IS NOT NULL AND CP1.deleted = 0, CP1.name, '')) AS namePolicy''')
        cols.append('''(IF(Organisation.id IS NOT NULL AND Organisation.deleted = 0, Organisation.shortName, '')) AS shortName''')
        cols.append('(SELECT MAX(CA.id) FROM ClientAddress AS CA WHERE CA.type=0 AND CA.client_id = C1.id AND CA.deleted = 0) AS addressRegId')
        cols.append('(SELECT MAX(CA2.id) FROM ClientAddress AS CA2 WHERE CA2.type=1 AND CA2.client_id = C1.id AND CA2.deleted=0) AS addressLocId')
        cols.append('(SELECT MAX(CAt.id) FROM ClientAttach AS CAt WHERE CAt.deleted=0 AND CAt.client_id = C1.id) AS clientAttachId')

        condClients = []
        group = u'C1.id'
        order = u''
        self.checkRun = True
        emptilySNILS = True
        booleanEmptyDocumentPolicy = True
        condClients.append(tableClient['deleted'].eq(0))
        if (self.chkDocumentsClient.isChecked() and documentRecord):
            if self.chkHaveDocumentsClient.isChecked():
                condClients.append('CD1.id IS NOT NULL AND CD1.deleted = 0')
            else:
                condClients.append('CD1.id IS NULL OR CD1.deleted = 0')
        if (self.chkPolicyClient.isChecked() and (policyRecord or voluntaryPolicyRecord)):
            if self.chkHavePolicyClient.isChecked():
                condClients.append('CP1.id IS NOT NULL AND CP1.deleted = 0')
            else:
                condClients.append('CP1.id IS NULL OR CP1.deleted = 0')
        if self.chkLastNameClient.isChecked():
            condClients.append(tableClient['lastName'].eq(lastName))
        if self.chkFirstNameClient.isChecked():
            condClients.append(tableClient['firstName'].eq(firstName))
        if self.chkPatrNameClient.isChecked():
            condClients.append(tableClient['patrName'].eq(patrName))
        if self.chkLastNameClient.isChecked() or self.chkFirstNameClient.isChecked() or self.chkPatrNameClient.isChecked():
            self.booleanNameClient = True
            emptilySNILS = False
        if self.chkBirthDateClient.isChecked():
            condClients.append(tableClient['birthDate'].eq(birthDate))
            self.booleanBirthDateClient = True
            emptilySNILS = False
        if self.chkSexClient.isChecked():
            condClients.append(tableClient['sex'].eq(sexCode))
            self.booleanSexClient = True
            emptilySNILS = False
        if self.chkSNILSClient.isChecked() and SNILS != u'':
            if emptilySNILS:
                condClients.append(tableClient['SNILS'].ne(u''))
                if group != u'':
                    group += u', SNILS'
                else:
                    group = u'SNILS'
            if self.chkHaveSNILSClient.isChecked() and not emptilySNILS:
                condClients.append(tableClient['SNILS'].ne(u''))
            condClients.append(tableClient['SNILS'].eq(SNILS))
            self.booleanSNILSClient = True
        if self.chkLastNameFilter.isChecked():
            condClients.append(tableClient['lastName'].textBetween(forceString(self.edtLastNameFilterFrom.text()).lower(), forceString(self.edtLastNameFilterTo.text()).lower()))
        if self.chkBirthDateFilter.isChecked():
            condClients.append(tableClient['birthDate'].dateBetween(forceDate(self.edtBirthDateFilterFrom.date()), forceDate(self.edtBirthDateFilterTo.date())))
        tableDocJoinCond = [tableClient['id'].eq(tableClientDocument['client_id'])]
        tableDocJoinCond.append(u'''(CD1.id IS NOT NULL AND CD1.deleted = 0 AND CD1.id = (SELECT MAX(CD.id) FROM ClientDocument AS CD
WHERE CD.`client_id`=C1.`id` AND CD.`deleted`=0 LIMIT 1)) ''')
        if self.chkLastNameClient.isChecked() or self.chkFirstNameClient.isChecked() or self.chkPatrNameClient.isChecked() or self.chkBirthDateClient.isChecked() or self.chkSexClient.isChecked() or (self.chkSNILSClient.isChecked() and SNILS != u''):
            condClients.append(tableClient['id'].isNotNull())
            table = tableClient.leftJoin(tableClientDocument, tableDocJoinCond)
            if emptilySNILS:
                if group != u'':
                    group += u', SNILS'
                else:
                    group = u'SNILS'
            booleanEmptyDocumentPolicy = False
        elif listCorrectsClientId != []:
            table = table.leftJoin(tableClientDocument, tableDocJoinCond)
        else:
            table = tableClient.leftJoin(tableClientDocument, tableDocJoinCond)
        table = table.leftJoin(tableClientAddress, tableClientAddress['client_id'].eq(tableClient['id']))
        table = table.leftJoin(tableClientAttach, tableClientAttach['client_id'].eq(tableClient['id']))
        table = table.leftJoin(tableDocumentType, tableDocumentType['id'].eq(tableClientDocument['documentType_id']))
        tablePolicyJoinCond = [tableClient['id'].eq(tableClientPolicy['client_id'])]
        tablePolicyJoinCond.append(u'''(CP1.id IS NOT NULL AND CP1.deleted = 0 AND CP1.id = (SELECT MAX(CP3.id) FROM ClientPolicy AS CP3
        WHERE CP3.`client_id`=C1.`id` AND CP3.`deleted`=0 LIMIT 1)) ''')
        table = table.leftJoin(tableClientPolicy, tablePolicyJoinCond)
        table = table.leftJoin(tableOrganisation, tableOrganisation['id'].eq(tableClientPolicy['insurer_id']))
        table = table.leftJoin(tablePolicyType, tablePolicyType['id'].eq(tableClientPolicy['policyType_id']))
        if self.chkDocumentsClient.isChecked() and documentRecord:
            if listCorrectsDocumentsId != []:
                condClients.append(tableClientDocument['id'].inlist(listCorrectsDocumentsId))
                if baseLineDocumentId:
                    condClients.append(tableClientDocument['id'].eq(baseLineDocumentId))
                else:
                    condClients.append(tableClientDocument['id'].inlist(listCorrectsDocumentsId))
            if self.chkLastNameClient.isChecked() or self.chkFirstNameClient.isChecked() or self.chkPatrNameClient.isChecked():
                condClients.append(tableClient['id'].eq(tableClientDocument['client_id']))
            condClients.append(tableClientDocument['id'].isNotNull())
            condClients.append(tableClientDocument['documentType_id'].eq(documentTypeId))
            if booleanEmptyDocumentPolicy:
                condClients.append(tableClientDocument['serial'].ne(u''))
                condClients.append(tableClientDocument['number'].ne(u''))
            condClients.append(tableClientDocument['serial'].eq(serial))
            condClients.append(tableClientDocument['number'].eq(number))
            self.booleanDocumentsClient = True
            emptilySNILS = False
            booleanEmptyDocumentPolicy = False

        if self.chkPolicyClient.isChecked() and (policyRecord or voluntaryPolicyRecord):
            if listCorrectsPolicysId != []:
                condClients.append(tableClientPolicy['id'].inlist(listCorrectsPolicysId))
                if baseLinePolicyId:
                    condClients.append(tableClientPolicy['id'].eq(baseLinePolicyId))
                else:
                    condClients.append(tableClientPolicy['id'].inlist(listCorrectsPolicysId))
            if self.chkLastNameClient.isChecked() or self.chkFirstNameClient.isChecked() or self.chkPatrNameClient.isChecked():
                condClients.append(tableClient['id'].eq(tableClientPolicy['client_id']))
            condClients.append(tableClientPolicy['id'].isNotNull())
            if booleanEmptyDocumentPolicy:
                condClients.append(tableClientPolicy['serial'].ne(u''))
                condClients.append(tableClientPolicy['number'].ne(u''))
                condClients.append(tableClientPolicy['policyType_id'].isNotNull())
            joinAnd1 = None
            joinAnd2 = None
            if policyRecord:
                joinAnd1 = db.joinAnd([tableClientPolicy['policyType_id'].eq(compulsoryPolicyTypeId), tableClientPolicy['serial'].eq(compulsoryPolicySerial), tableClientPolicy['number'].eq(compulsoryPolicyNumber)])
            if voluntaryPolicyRecord:
                joinAnd2 = db.joinAnd([tableClientPolicy['policyType_id'].eq(voluntaryPolicyTypeId), tableClientPolicy['serial'].eq(voluntaryPolicySerial), tableClientPolicy['number'].eq(voluntaryPolicyNumber)])
            if joinAnd1 and joinAnd2:
                condClients.append(db.joinOr([joinAnd1, joinAnd2]))
            elif joinAnd1:
                condClients.append(joinAnd1)
            elif joinAnd2:
                condClients.append(joinAnd2)
            self.booleanPolicyClient = True
            emptilySNILS = False
            booleanEmptyDocumentPolicy = False
        if listCorrectsClientId != []:
            condClients.append(tableClient['id'].inlist(listCorrectsClientId))
            if baseLineClientId:
                condClients.append(tableClient['id'].eq(baseLineClientId))
            else:
                condClients.append(tableClient['id'].inlist(listCorrectsClientId))
        if condClients != []:
            order = u'C1.id != %d'%(self.registryClientId)
            records = db.getRecordListGroupBy(table, cols, condClients, group, order, forceInt(self.edtLimitFilter.text()) if self.chkLimitFilter.isChecked() else None)
            if listCorrectsClientId != []:
                for record in records:
                    self.recordsCorrectClient.append(record)
                self.checkRun = False
                self.abortProcess = False
            elif listCorrectsClientId == [] and not baseLineClientId:
                self.createRecordsTblDoubleClients(records)


    def controlDoubleClients(self, listCorrectsClientId = [], listCorrectsDocumentsId = [], listCorrectsPolicysId = [], baseLineClientId = None, baseLineDocumentId = None, baseLinePolicyId = None):
        self.recordsCorrectClient = []
        self.booleanNameClient = False
        self.booleanBirthDateClient = False
        self.booleanSexClient = False
        self.booleanSNILSClient = False
        self.booleanDocumentsClient = False
        self.booleanPolicyClient = False
        db = QtGui.qApp.db
        tableClient = db.table('Client').alias('C1')
        tableClient2 = db.table('Client').alias('C2')
        tableClientDocument = db.table('ClientDocument').alias('CD1')
        tableClientDocument2 = db.table('ClientDocument').alias('CD2')
        tableClientPolicy = db.table('ClientPolicy').alias('CP1')
        tableClientPolicy2 = db.table('ClientPolicy').alias('CP2')
        tableDocumentType = db.table('rbDocumentType')
        tableOrganisation = db.table('Organisation')
        tablePolicyType = db.table('rbPolicyType')
        tableClientAddress = db.table('ClientAddress')
        tableClientAttach = db.table('ClientAttach')

        cols = [tableClient['id'].alias('clientId'),
               tableClient['lastName'],
               tableClient['firstName'],
               tableClient['patrName'],
               tableClient['birthDate'],
               tableClient['sex'],
               tableClient['SNILS'], 
               tableClient['createPerson_id'], 
               tableClient['createDatetime'].alias('createDate'),
               tableClient['createDatetime'].alias('createTime'),
               tableClient['modifyPerson_id'], 
               tableClient['modifyDatetime'].alias('modifyDate'),
               tableClient['modifyDatetime'].alias('modifyTime')
               ]
        cols.append('''(IF(CD1.id IS NOT NULL AND CD1.deleted = 0, CD1.id, NULL)) AS documentId''')
        cols.append('''(IF(CD1.id IS NOT NULL AND CD1.deleted = 0, rbDocumentType.name, '')) AS nameDocument''')
        cols.append('''(IF(CD1.id IS NOT NULL AND CD1.deleted = 0, CD1.serial, '')) AS serialDocument''')
        cols.append('''(IF(CD1.id IS NOT NULL AND CD1.deleted = 0, CD1.number, '')) AS numberDocument''')
        cols.append('''(IF(CD1.id IS NOT NULL AND CD1.deleted = 0, CD1.date, NULL)) AS date''')
        cols.append('''(IF(CD1.id IS NOT NULL AND CD1.deleted = 0, CD1.origin, '')) AS origin''')
        cols.append('''(IF(CP1.id IS NOT NULL AND CP1.deleted = 0, CP1.id, NULL)) AS policyId''')
        cols.append('''(IF(CP1.id IS NOT NULL AND CP1.deleted = 0, rbPolicyType.name, '')) AS nameTypePolicy''')
        cols.append('''(IF(CP1.id IS NOT NULL AND CP1.deleted = 0, CP1.serial, '')) AS serialPolicy''')
        cols.append('''(IF(CP1.id IS NOT NULL AND CP1.deleted = 0, CP1.number, '')) AS numberPolicy''')
        cols.append('''(IF(CP1.id IS NOT NULL AND CP1.deleted = 0, CP1.begDate, NULL)) AS begDate''')
        cols.append('''(IF(CP1.id IS NOT NULL AND CP1.deleted = 0, CP1.endDate, NULL)) AS endDate''')
        cols.append('''(IF(CP1.id IS NOT NULL AND CP1.deleted = 0, CP1.name, '')) AS namePolicy''')
        cols.append('''(IF(Organisation.id IS NOT NULL AND Organisation.deleted = 0, Organisation.shortName, '')) AS shortName''')
        cols.append('(SELECT MAX(CA.id) FROM ClientAddress AS CA WHERE CA.type=0 AND CA.client_id = C1.id AND CA.deleted = 0) AS addressRegId')
        cols.append('(SELECT MAX(CA2.id) FROM ClientAddress AS CA2 WHERE CA2.type=1 AND CA2.client_id = C1.id AND CA2.deleted=0) AS addressLocId')
        cols.append('(SELECT MAX(CAt.id) FROM ClientAttach AS CAt WHERE CAt.deleted=0 AND CAt.client_id = C1.id) AS clientAttachId')

        condClients = []
        group = u'C1.id'
        order = u''
        self.checkRun = True
        emptilySNILS = True
        booleanEmptyDocumentPolicy = True
        condClients.append(tableClient['deleted'].eq(0))
        if self.registryClientIdList:
            condClients.append(db.joinOr([tableClient['id'].inlist(self.registryClientIdList), tableClient2['id'].inlist(self.registryClientIdList)]))
        # if (self.chkDocumentsClient.isChecked()):
        #     condClients.append('CD1.id IS NULL OR CD1.deleted = 0')
        # if (self.chkPolicyClient.isChecked()):
        #     condClients.append('CP1.id IS NULL OR CP1.deleted = 0')
        if self.chkLastNameClient.isChecked():
            condClients.append(tableClient['lastName'].eq(tableClient2['lastName']))
        if self.chkFirstNameClient.isChecked():
            condClients.append(tableClient['firstName'].eq(tableClient2['firstName']))
        if self.chkPatrNameClient.isChecked():
            condClients.append(tableClient['patrName'].eq(tableClient2['patrName']))
            self.booleanNameClient = True
            emptilySNILS = False
        if self.chkBirthDateClient.isChecked():
            condClients.append(tableClient['birthDate'].eq(tableClient2['birthDate']))
            self.booleanBirthDateClient = True
            emptilySNILS = False
        if self.chkSexClient.isChecked():
            condClients.append(tableClient['sex'].eq(tableClient2['sex']))
            self.booleanSexClient = True
            emptilySNILS = False
        if self.chkSNILSClient.isChecked():
            if emptilySNILS:
                condClients.append(tableClient['SNILS'].ne(u''))
                if group != u'':
                    group += u', SNILS'
                else:
                    group = u'SNILS'
            else:
                condClients.append(db.joinOr([tableClient['SNILS'].ne(u''), tableClient['SNILS'].eq(u'')]))
            if self.chkHaveSNILSClient.isChecked() and not emptilySNILS:
                condClients.append(tableClient['SNILS'].ne(u''))
            condClients.append(tableClient['SNILS'].eq(tableClient2['SNILS']))
            self.booleanSNILSClient = True
        if self.chkLastNameFilter.isChecked():
            condClients.append(tableClient['lastName'].textBetween(forceString(self.edtLastNameFilterFrom.text()).lower(), forceString(self.edtLastNameFilterTo.text()).lower()))
        if self.chkBirthDateFilter.isChecked():
            condClients.append(tableClient['birthDate'].dateBetween(forceDate(self.edtBirthDateFilterFrom.date()), forceDate(self.edtBirthDateFilterTo.date())))
        tableDocJoinCond = [tableClient['id'].eq(tableClientDocument['client_id'])]
        tableDocJoinCond.append(u'''(CD1.id IS NOT NULL AND CD1.deleted = 0 AND CD1.id = (SELECT MAX(CD.id) FROM ClientDocument AS CD
WHERE CD.`client_id`=C1.`id` AND CD.`deleted`=0 LIMIT 1))''')
        tableDocJoinCond2 = [tableClient2['id'].eq(tableClientDocument2['client_id'])]
        tableDocJoinCond2.append(u'''(CD2.id IS NOT NULL AND CD2.deleted = 0 AND CD2.id = (SELECT MAX(CD.id) FROM ClientDocument AS CD
WHERE CD.`client_id`=C2.`id` AND CD.`deleted`=0 LIMIT 1))''')
        if self.chkLastNameClient.isChecked() or self.chkFirstNameClient.isChecked() or self.chkPatrNameClient.isChecked() or self.chkBirthDateClient.isChecked() or self.chkSexClient.isChecked() or self.chkSNILSClient.isChecked():
            if listCorrectsClientId != [] and baseLineClientId:
                table = tableClient2.join(tableClient, 1)
            else:
                table = tableClient2.innerJoin(tableClient, tableClient['id'].ne(tableClient2['id']))
                condClients.append(tableClient['id'].ne(tableClient2['id']))
            condClients.append(tableClient2['deleted'].eq(0))
            condClients.append(tableClient['id'].isNotNull())
            condClients.append(tableClient2['id'].isNotNull())
            table = table.leftJoin(tableClientDocument, tableDocJoinCond)
            if emptilySNILS:
                order = u'SNILS'
                if group != u'':
                    group += u', SNILS'
                else:
                    group = u'SNILS'
            else:
                order = u'C1.lastName, C1.firstName, C1.patrName, C1.birthDate, C1.id'
            booleanEmptyDocumentPolicy = False
        elif listCorrectsClientId != []:
            table = tableClient2.join(tableClient, 1)
            table = table.leftJoin(tableClientDocument, tableDocJoinCond)
        else:
            table = tableClient.leftJoin(tableClientDocument, tableDocJoinCond)
        table = table.leftJoin(tableClientAddress, tableClientAddress['client_id'].eq(tableClient['id']))
        table = table.leftJoin(tableClientAttach, tableClientAttach['client_id'].eq(tableClient['id']))
        table = table.leftJoin(tableDocumentType, tableDocumentType['id'].eq(tableClientDocument['documentType_id']))
        tablePolicyJoinCond = [tableClient['id'].eq(tableClientPolicy['client_id'])]
        tablePolicyJoinCond.append(u'''(CP1.id IS NOT NULL AND CP1.deleted = 0 AND CP1.id = (SELECT MAX(CP3.id) FROM ClientPolicy AS CP3
        WHERE CP3.`client_id`=C1.`id` AND CP3.`deleted`=0 LIMIT 1)) ''')
        table = table.leftJoin(tableClientPolicy, tablePolicyJoinCond)
        table = table.leftJoin(tableOrganisation, tableOrganisation['id'].eq(tableClientPolicy['insurer_id']))
        table = table.leftJoin(tablePolicyType, tablePolicyType['id'].eq(tableClientPolicy['policyType_id']))
        if self.chkDocumentsClient.isChecked():

            table = table.leftJoin(tableClientDocument2, tableDocJoinCond2)
            
            if self.chkHaveDocumentsClient.isChecked():
                condClients.append(tableClientDocument['id'].isNotNull())
                condClients.append(tableClientDocument2['id'].isNotNull())
                
            if listCorrectsDocumentsId != []:
                condClients.append(tableClientDocument['id'].inlist(listCorrectsDocumentsId))
                condClients.append(tableClientDocument2['id'].inlist(listCorrectsDocumentsId))
                if booleanEmptyDocumentPolicy:
                    condClients.append(tableClientDocument['serial'].ne(u''))
                    condClients.append(tableClientDocument['number'].ne(u''))
            condClients.append(db.joinOr([db.joinAnd([tableClientDocument['id'].isNull(), tableClientDocument2['id'].isNull()]),
                                          db.joinAnd([tableClientDocument['documentType_id'].eq(tableClientDocument2['documentType_id']),
                                                      tableClientDocument['serial'].eq(tableClientDocument2['serial']),
                                                      tableClientDocument['number'].eq(tableClientDocument2['number'])])]))
            if order != u'':
                order += u', '
            order += u'CD1.documentType_id, CD1.serial, CD1.number'
            self.booleanDocumentsClient = True
            emptilySNILS = False
            booleanEmptyDocumentPolicy = False

        if self.chkPolicyClient.isChecked():
            tablePolicyJoinCond2 = [tableClientPolicy2['client_id'].eq(tableClient2['id'])]
            tablePolicyJoinCond2.append(u'''(CP2.id IS NOT NULL AND CP2.deleted = 0 AND CP2.id = (SELECT MAX(CP3.id) FROM ClientPolicy AS CP3
            WHERE CP3.`client_id`=C2.`id` AND CP3.`deleted`=0 LIMIT 1)) ''')

            table = table.leftJoin(tableClientPolicy2, tablePolicyJoinCond2)
            
            if self.chkHavePolicyClient.isChecked() and listCorrectsPolicysId == []:
                condClients.append(tableClientPolicy['id'].isNotNull())
                condClients.append(tableClientPolicy2['id'].isNotNull())
                
            if listCorrectsPolicysId == []:
                if (not self.chkLastNameClient.isChecked() and not self.chkFirstNameClient.isChecked() and not self.chkPatrNameClient.isChecked()) and not self.chkBirthDateClient.isChecked() and not self.chkSexClient.isChecked() and not self.chkSNILSClient.isChecked():
                    condClients.append('(CP1.id IS NOT NULL AND CP2.id IS NOT NULL AND CP1.deleted = 0 AND CP2.deleted = 0 AND CP1.id!=CP2.id)')
                else:
                    condClients.append('''(CP1.id IS NULL AND CP2.id IS NULL)
                                           OR (CP1.deleted = 0 AND CP2.deleted = 0 AND CP1.id!=CP2.id)''')
            else:
                condClients.append(tableClientPolicy['id'].ne(tableClientPolicy2['id']))
            if listCorrectsPolicysId != []:
                condClients.append(tableClientPolicy['id'].inlist(listCorrectsPolicysId))
                condClients.append(tableClientPolicy2['id'].inlist(listCorrectsPolicysId))
                if self.chkLastNameClient.isChecked() or self.chkFirstNameClient.isChecked() or self.chkPatrNameClient.isChecked():
                    condClients.append(tableClient['id'].eq(tableClientPolicy['client_id']))
                    condClients.append(tableClient2['id'].eq(tableClientPolicy2['client_id']))
                condClients.append(tableClientPolicy['id'].isNotNull())
                condClients.append(tableClientPolicy2['id'].isNotNull())
                condClients.append(tableClientPolicy2['deleted'].eq(0))
                if booleanEmptyDocumentPolicy:
                    condClients.append(tableClientPolicy['serial'].ne(u''))
                    condClients.append(tableClientPolicy['number'].ne(u''))
                    condClients.append(tableClientPolicy['policyType_id'].isNotNull())
            condClients.append(
                db.joinOr([db.joinAnd([tableClientPolicy['id'].isNull(), tableClientPolicy2['id'].isNull()]),
                           db.joinAnd([tableClientPolicy['policyType_id'].eq(tableClientPolicy2['policyType_id']),
                                       tableClientPolicy['serial'].eq(tableClientPolicy2['serial']),
                                       tableClientPolicy['number'].eq(tableClientPolicy2['number'])])]))
            if order != u'':
                order += u', '
            order += u'CP1.policyType_id, CP1.serial, CP1.number, CP1.name'
            self.booleanPolicyClient = True
            emptilySNILS = False
            booleanEmptyDocumentPolicy = False
        if listCorrectsClientId != []:
            condClients.append(tableClient['id'].inlist(listCorrectsClientId))
            if baseLineClientId:
                pass
                # condClients.append(tableClient2['id'].eq(baseLineClientId))
            else:
                condClients.append(tableClient2['id'].inlist(listCorrectsClientId))
        if condClients != []:
            records = db.getRecordListGroupBy(table, cols, condClients, group, order, forceInt(self.edtLimitFilter.text()) if self.chkLimitFilter.isChecked() else None)
            if listCorrectsClientId != []:
                for record in records:
                    self.recordsCorrectClient.append(record)
                self.checkRun = False
                self.abortProcess = False
            elif listCorrectsClientId == [] and not baseLineClientId:
                self.createRecordsTblDoubleClients(records)


    def createRecordsTblDoubleClients(self, records = None):
        prbControlPercent = 0
        lenStr = len(records)
        if lenStr > 1:
            self.prbControlDoubles.setMaximum(lenStr - 1)
            i = 0
            self.lblCountRecords.setText(forceString(len(records)))
            for record in records:
                self.bufferRecords.append(record)
                QtGui.qApp.processEvents()
                if self.abortProcess:
                    self.checkRun = False
                    break
                resultStr = u''
                self.prbControlDoubles.setValue(prbControlPercent)
                prbControlPercent += 1
                resultStr = self.aggregateString(record)
                i += 1
                self.printDataDoubles(resultStr)
        if lenStr > 0:
            listWidgetItemClient = self.tblDoubleClients.item(0)
            if listWidgetItemClient:
                self.basicFont = listWidgetItemClient.font()


    def aggregateString(self, record = None):
        resultStr = u''
        if record:
            db = QtGui.qApp.db
            lastName = forceString(record.value('lastName'))
            firstName = forceString(record.value('firstName'))
            patrName = forceString(record.value('patrName'))
            birthDate = forceString(record.value('birthDate'))
            clientId = forceString(record.value('clientId'))
            documentId = forceString(record.value('documentId'))
            policyId = forceString(record.value('policyId'))
            sexInt = forceInt(record.value('sex'))
            if sexInt == 1:
                sex = u'мужской'
            elif sexInt == 2:
                  sex = u'женский'
            else:
                sex = u'неопределено'
            addressRegId = forceRef(record.value('addressRegId'))
            addressLocId = forceRef(record.value('addressLocId'))
            clientAttachId = forceRef(record.value('clientAttachId'))
            addressReg = u''
            addressLoc = u''
            attachInfo = u''
            if addressRegId:
                queryAddressReg = db.query('''SELECT formatClientAddress(%d) AS addressReg'''%(addressRegId))
                while queryAddressReg.next():
                    recordAddressReg = queryAddressReg.record()
                    addressReg = forceString(recordAddressReg.value('addressReg'))
            if addressLocId:
                queryAddressLoc = db.query('''SELECT formatClientAddress(%d) AS addressLoc'''%(addressLocId))
                while queryAddressLoc.next():
                    recordAddressLoc = queryAddressLoc.record()
                    addressLoc = forceString(recordAddressLoc.value('addressLoc'))
            if clientAttachId:
                queryAttach = db.query('''SELECT formatClientAttach(%d) AS attachInfo'''%(clientAttachId))
                while queryAttach.next():
                    recordAttach = queryAttach.record()
                    attachInfo = forceString((recordAttach.value('attachInfo')))
            SNILS = forceString(record.value('SNILS'))
            nameDocument = forceString(record.value('nameDocument'))
            serialDocument = forceString(record.value('serialDocument'))
            numberDocument = forceString(record.value('numberDocument'))
            date = forceString(forceDate(record.value('date')))
            origin = forceString(record.value('origin'))
            serialPolicy = forceString(record.value('serialPolicy'))
            numberPolicy = forceString(record.value('numberPolicy'))
            begDate = forceString(forceDate(record.value('begDate')))
            endDate = forceString(forceDate(record.value('endDate')))
#            namePolicy = forceString(record.value('namePolicy'))
            shortName = forceString(record.value('shortName'))
            nameTypePolicy = forceString(record.value('nameTypePolicy'))
            createPerson = forceRef(record.value('createPerson_id'))
            createDate = forceString(forceDate(record.value('createDate')))
            createTime = forceString(forceTime(record.value('createTime')))
            modifyPerson= forceRef(record.value('modifyPerson_id'))
            modifyDate = forceString(forceDate(record.value('modifyDate')))
            modifyTime = forceString(forceTime(record.value('modifyTime')))
            resultStr = u'Пациент: '
            if clientId:
                resultStr += clientId
            resultStr +=u'(' + lastName + u' ' + firstName + u' ' + patrName + u' ' + birthDate + u')' +  u' пол: ' + sex
            if SNILS:
                resultStr += u'  СНИЛС: ' + SNILS
            resultDoc = u''
            if documentId:
                resultDoc += u'  Документ: '
                if nameDocument:
                    resultDoc += nameDocument
                if serialDocument:
                    resultDoc += u' серия: ' + serialDocument
                if numberDocument:
                    resultDoc += u' номер: ' + numberDocument
                if date:
                    resultDoc += u' дата: ' + date
                if origin:
                    resultDoc += u' организация: ' + origin
                resultStr += resultDoc
#                resultStr += u'  Документ: '
#                if nameDocument:
#                    resultStr += nameDocument
#                if serialDocument:
#                    resultStr += u' серия: ' + serialDocument
#                if numberDocument:
#                    resultStr += u' номер: ' + numberDocument
#                if date:
#                    resultStr += u' дата: ' + date
#                if origin:
#                    resultStr += u' организация: ' + origin
            resultPolicy = u''
            if policyId:
                resultPolicy += u'  Полис: '
                if shortName:
                    resultPolicy += u' короткое название: ' + shortName
                if nameTypePolicy:
                    resultPolicy += u' тип: ' + nameTypePolicy
                if serialPolicy:
                    resultPolicy += u' серия: ' + serialPolicy
                if numberPolicy:
                    resultPolicy += u' номер: ' + numberPolicy
                if begDate:
                    resultPolicy += u' дата выдачи: ' + begDate
                if endDate:
                    resultPolicy += u' дата окончания: ' + endDate
                if addressReg:
                    resultPolicy += u'  Адрес регистрации: ' + addressReg
                elif addressLoc:
                    resultPolicy += u'  Адрес проживания: ' + addressLoc
                resultStr += resultPolicy
#                resultStr += u'  Полис: '
#                if shortName:
#                    resultStr += u' короткое название: ' + shortName
#                if nameTypePolicy:
#                    resultStr += u' тип: ' + nameTypePolicy
#                if serialPolicy:
#                    resultStr += u' серия: ' + serialPolicy
#                if numberPolicy:
#                    resultStr += u' номер: ' + numberPolicy
#                if begDate:
#                    resultStr += u' дата выдачи: ' + begDate
#                if endDate:
#                    resultStr += u' дата окончания: ' + endDate
#                if addressReg:
#                    resultStr += u'  Адрес регистрации: ' + addressReg
#                elif addressLoc:
#                    resultStr += u'  Адрес проживания: ' + addressLoc
            resultAttach = u''
            if attachInfo:
                resultAttach += u' Прикрепление: ' + attachInfo
            resultStr += resultAttach
            resultProps=u''
            if clientId:
                if createPerson:
                    resultProps += u' Автор записи: ' + forceString(QtGui.qApp.db.translate('vrbPerson', 'id', createPerson, 'name'))
                if createDate:
                    resultProps += u' Дата создания записи: ' + createDate
                if createTime:
                    resultProps += u' Время создания записи: ' + createTime
                if modifyPerson:
                    resultProps += u' Автор последнего изменения записи: ' + forceString(QtGui.qApp.db.translate('vrbPerson', 'id', modifyPerson, 'name'))
                if modifyDate:
                    resultProps += u' Дата последнего изменения записи: ' + modifyDate
                if modifyTime:
                    resultProps += u' Время последнего изменения записи: ' + modifyTime
            resultStr += resultProps
            tempPrintList = [clientId,
                             lastName,
                             firstName,
                             patrName,
                             sex,
                             birthDate,
                             resultDoc,
                             resultPolicy,
                             SNILS, 
                             forceString(QtGui.qApp.db.translate('vrbPerson', 'id', createPerson, 'name')),
                             createDate,
                             createTime,
                             forceString(QtGui.qApp.db.translate('vrbPerson', 'id', modifyPerson, 'name')), 
                             modifyDate,
                             modifyTime
                            ]
            self.tempPrintList.append(tempPrintList)
        return resultStr


    def printDataDoubles(self, valStr):
        self.tblDoubleClients.addItem(self.errorStr + valStr)
        item = self.tblDoubleClients.item(self.rows)
        self.tblDoubleClients.scrollToItem(item)
        self.rows += 1


    def loadDataDiagnosis(self):
        self.tempPrintList = []
        self.rows = 0
        self.prbControlDoubles.setFormat('%v')
        self.prbControlDoubles.setValue(0)
        self.btnEndCheck.setText(u'прервать')
        self.btnBeginCheck.setEnabled(False)
        self.btnNewTuning.setEnabled(False)
        self.lblCountRecords.setText(u'0')
        try:
            if self.registryClientId:
                QtGui.qApp.callWithWaitCursor(self, self.controlRegistryDoubleClients)
            else:
                QtGui.qApp.callWithWaitCursor(self, self.controlDoubleClients)
#        except Exception, e:
        except Exception:
            self.abortProcess = True
        self.prbControlDoubles.setText(u'прервано' if self.abortProcess else u'готово')
        self.btnEndCheck.setText(u'закрыть')
        self.btnNewTuning.setEnabled(True)
        self.btnBeginCheck.setEnabled(True)
        self.btnPrint.setEnabled(True)
        self.checkRun = False
        self.abortProcess = False


class CWarningControlDublesDialog(CDialogBase, Ui_WarningControlDublesDialog):
    def __init__(self, parent = None, messageBaseLine = u'', messageDouble = u'', selectBaseLineItems = None, selectBaseLine = None):
        CDialogBase.__init__(self, parent = None)
        self.setupUi(self)
        self.lblInformationTextBaseLine.setText(messageBaseLine)
        self.lblInformationTextDoubleLine.setText(messageDouble)
        self.btnOkCancel.button(QtGui.QDialogButtonBox.Cancel).setDefault(True)
        self.selectBaseLineItems = selectBaseLineItems
        self.selectBaseLine = selectBaseLine
        self.rowBaseLine = None


    @pyqtSignature('')
    def on_btnSelectBaseLine_clicked(self):
        if CCorrectBaseLineDialog(self).exec_():
            if self.rowBaseLine is not None:
                self.close()
        else:
            self.rowBaseLine = None


class CCorrectsControlDublesDialog(CDialogBase, Ui_CorrectsControlDublesDialog):
    def __init__(self, parent = None, messageBaseLine = u'', messageDouble = u'', bufferRecordsBaseLines = None, bufferRecordsDoubleLines = None):
        CDialogBase.__init__(self, parent = None)
        self.setupUi(self)
        self.tblCorrectBaseLine.addItem(messageBaseLine)
        self.tblCorrectDoubleLine.addItems(messageDouble)
        self.btnOkCancel.button(QtGui.QDialogButtonBox.Cancel).setDefault(True)
        self.bufferRecordsBaseLines = bufferRecordsBaseLines
        self.bufferRecordsDoubleLines = bufferRecordsDoubleLines


    @pyqtSignature('QModelIndex')
    def on_tblCorrectBaseLine_doubleClicked (self, index):
        self.openDocumentClientCorrects(self.tblCorrectBaseLine, self.bufferRecordsBaseLines)


    @pyqtSignature('QModelIndex')
    def on_tblCorrectDoubleLine_doubleClicked (self, index):
        self.openDocumentClientCorrects(self.tblCorrectDoubleLine, self.bufferRecordsDoubleLines)


    def openDocumentClientCorrects(self, widget = None, records = None):
        if widget and records:
            booleanCorrected = False
            row = widget.currentRow()
            record = records[row]
            clientId = forceRef(record.value('clientId'))
            if clientId and QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]):
                dialog = CClientEditDialog(self)
                if dialog:
                    try:
                        dialog.load(clientId)
                        booleanCorrected = dialog.exec_()
                    finally:
                        dialog.deleteLater()
            if booleanCorrected and widget:
                listWidgetItem = widget.item(row)
                if listWidgetItem:
                    listWidgetItem.setFlags(Qt.NoItemFlags)


class CCorrectBaseLineDialog(CDialogBase, Ui_CorrectBaseLineDialog):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.currentRow = None
        self.tblSelectBaseLine.addItems(parent.selectBaseLineItems)


    @pyqtSignature('QModelIndex')
    def on_tblSelectBaseLine_clicked (self, index):
        currentRow = self.tblSelectBaseLine.currentRow()
        self.parent().rowBaseLine = self.parent().selectBaseLine[currentRow]
