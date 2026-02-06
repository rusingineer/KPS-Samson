# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2020 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignature, QDate, QDateTime, QLocale

from library.Utils       import firstMonthDay, forceBool, forceDouble, forceRef, forceString, lastMonthDay
from Events.ActionStatus import CActionStatus
from Events.FinanceTypeListEditorDialog import CFinanceTypeListEditorDialog
from Reports.Report      import CReport
from Reports.ReportBase  import CReportBase, createTable

from Reports.Ui_ExternalIncomePaidServicesDialog import Ui_ExternalIncomePaidServicesDialog


class CExternalIncomePaidServicesDialog(QtGui.QDialog, Ui_ExternalIncomePaidServicesDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.patientRequired                = False
        self.setupByOrgStructureVisible     = False
        self.strongOrgStructureVisible      = False
        self.clientAgeCategoryVisible       = False
        self.onlyClientAsPersonInLPUVisible = False
        self.personVisible                  = False
        self.detailServiceVisible           = False
        self.eventIdentifierTypeVisible     = False
        self.dateTypeVisible                = False
        self.eventStatusVisible             = False
        self.setStrongOrgStructureVisible(      self.strongOrgStructureVisible      )
        self.setSetupByOrgStructureVisible(     self.setupByOrgStructureVisible     )
        self.setClientAgeCategoryVisible(       self.clientAgeCategoryVisible       )
        self.setOnlyClientAsPersonInLPUVisible( self.onlyClientAsPersonInLPUVisible )
        self.setPersonVisible(                  self.personVisible                  )
        self.setEventIdentifierTypeVisible(     self.eventIdentifierTypeVisible     )
        self.setDateTypeVisible(                self.dateTypeVisible                )
        self.setEventStatusVisible(             self.eventStatusVisible             )
        self.cmbActionTypeGroup.setClass(None)
        self.cmbActionTypeGroup.model().setLeavesVisible(False)
        self.cmbAccountingSystem.setTable('rbAccountingSystem', addNone=False, filter = u'''domain = 'EventType' ''')
        self.cmbAccountingSystem.setValue(forceRef(QtGui.qApp.preferences.appPrefs.get('FilterAccountingSystem', 0))
                                         )
        self.cmbMedicalAidUnit.setTable('rbMedicalAidUnit', addNone=True)
        self.financeTypeList = []


    def setDateTypeVisible(self, value):
        self.dateTypeVisible = value
        self.cmbDateType.setVisible(value)
        self.lblDateType.setVisible(value)


    def setEventIdentifierTypeVisible(self, value):
        self.eventIdentifierTypeVisible = value
        self.lblEventIdentifierType.setVisible(value)
        self.cmbEventIdentifierType.setVisible(value)


    def setPersonVisible(self, value):
        self.personVisible = value
        self.chkPerson.setVisible(value)
        self.cmbPerson.setVisible(value)


    def setStrongOrgStructureVisible(self, value):
        self.strongOrgStructureVisible = value
        self.chkOrgStructure.setVisible(value)
        self.cmbOrgStructure.setVisible(value)


    def setSetupByOrgStructureVisible(self, value):
        self.setupByOrgStructureVisible = value
        self.lblReportType.setVisible(value)
        self.cmbReportType.setVisible(value)
        self.chkAllOrgStructure.setVisible(value)


    def setClientAgeCategoryVisible(self, value):
        self.clientAgeCategoryVisible = value
        self.chkClientAgeCategory.setVisible(value)
        self.cmbClientAgeCategory.setVisible(value)


    def setOnlyClientAsPersonInLPUVisible(self, value):
        self.onlyClientAsPersonInLPUVisible = value
        self.chkOnlyClientAsPersonInLPU.setVisible(value)


    def setEventStatusVisible(self, value):
        self.eventStatusVisible = value
        self.chkEventStatus.setVisible(value)
        self.cmbEventStatus.setVisible(value)


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        if self.dateTypeVisible:
            self.cmbDateType.setCurrentIndex(params.get('dateType', 0))
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        chkClass = params.get('chkClass', False)
        self.chkClass.setChecked(chkClass)
        self.cmbClass.setCurrentIndex(params.get('class', 0))
        chkActionTypeGroup = params.get('chkActionTypeGroup', False)
        self.chkActionTypeGroup.setChecked(chkActionTypeGroup)
        self.cmbActionTypeGroup.setValue(params.get('actionTypeGroupId', None))
        chkStatus = params.get('chkStatus', False)
        self.chkStatus.setChecked(chkStatus)
        self.cmbStatus.setValue(params.get('status', CActionStatus.started))
        self.cmbReportType.setCurrentIndex(params.get('reportType', 0))
        self.chkAllOrgStructure.setChecked(params.get('chkAllOrgStructure', False))
#        self.cmbContract.setValue(params.get('contractId', None))
        self.cmbContract.setPath(params.get('contractPath', None))
        self.financeTypeList =  params.get('financeTypeList', [])
        if self.financeTypeList:
            db = QtGui.qApp.db
            table = db.table('rbFinance')
            records = db.getRecordList(table, [table['name']], [table['id'].inlist(self.financeTypeList)])
            nameList = []
            for record in records:
                nameList.append(forceString(record.value('name')))
            self.lblFinanceTypeList.setText(u','.join(name for name in nameList if name))
        else:
            self.lblFinanceTypeList.setText(u'не задано')
        self.chkConfirmation.setChecked(params.get('confirmation', False))
        date = QDate.currentDate()
        self.edtConfirmationBegDate.setDate(params.get('confirmationBegDate', firstMonthDay(date)))
        self.edtConfirmationEndDate.setDate(params.get('confirmationEndDate', lastMonthDay(date)))
        self.cmbConfirmationType.setCurrentIndex(params.get('confirmationType', 0))
        self.cmbConfirmationPeriodType.setCurrentIndex(params.get('confirmationPeriodType', 0))
        if self.eventIdentifierTypeVisible:
            self.cmbEventIdentifierType.setCurrentIndex(params.get('eventIdentifierType', 0))
        if self.strongOrgStructureVisible:
            chkOrgStructure = params.get('chkOrgStructure', False)
            self.chkOrgStructure.setChecked(chkOrgStructure)
            self.cmbOrgStructure.setValue(params.get('orgStructureId', None))
        if self.clientAgeCategoryVisible:
            chkClientAgeCategory = params.get('chkClientAgeCategory', False)
            self.chkClientAgeCategory.setChecked(chkClientAgeCategory)
            self.cmbClientAgeCategory.setCurrentIndex(params.get('clientAgeCategory', 0))
            self.cmbClientAgeCategory.setEnabled(chkClientAgeCategory)
        if self.onlyClientAsPersonInLPUVisible:
            self.chkOnlyClientAsPersonInLPU.setChecked(params.get('chkOnlyClientAsPersonInLPU', False))
        if self.personVisible:
            chkPerson = params.get('chkPerson', False)
            self.chkPerson.setChecked(chkPerson)
            self.cmbPerson.setValue(params.get('personId', None))
        if self.eventStatusVisible:
            chkEventStatus = params.get('chkEventStatus', False)
            self.chkEventStatus.setChecked(chkEventStatus)
            self.cmbEventStatus.setCurrentIndex(params.get('eventStatus',  0))
        self.cmbAccountingSystem.setValue(params.get('accountingSystemId', forceRef(QtGui.qApp.preferences.appPrefs.get('FilterAccountingSystem', 0))))
        self.cmbMedicalAidUnit.setValue(params.get('unitId', None))
        self.chkVAT.setChecked(params.get('isVAT', False))


    def params(self):
        params = {}
        if self.dateTypeVisible:
            params['dateType']            = self.cmbDateType.currentIndex()
        params['begDate']                 = self.edtBegDate.date()
        params['endDate']                 = self.edtEndDate.date()
        params['chkClass']                = self.chkClass.isChecked()
        if params['chkClass']:
            params['class']               = self.cmbClass.currentIndex()
        params['chkActionTypeGroup']      = self.chkActionTypeGroup.isChecked()
        if params['chkActionTypeGroup']:
            params['actionTypeGroupId']   = self.cmbActionTypeGroup.value()
        params['chkStatus']               = self.chkStatus.isChecked()
        params['status']                  = self.cmbStatus.value()
        params['contractPath']            = self.cmbContract.getPath()
        params['contractIdList']          = self.cmbContract.getIdList()
        params['contractText']            = forceString(self.cmbContract.currentText())
        params['financeTypeList']         = self.financeTypeList
        params['financeText']             = self.lblFinanceTypeList.text()
        params['confirmation']            = self.chkConfirmation.isChecked()
        params['confirmationType']        = self.cmbConfirmationType.currentIndex()
        params['confirmationPeriodType']  = self.cmbConfirmationPeriodType.currentIndex()
        params['confirmationBegDate']     = self.edtConfirmationBegDate.date()
        params['confirmationEndDate']     = self.edtConfirmationEndDate.date()
        if self.eventIdentifierTypeVisible:
            params['eventIdentifierType'] = self.cmbEventIdentifierType.currentIndex()
        if self.strongOrgStructureVisible:
            params['chkOrgStructure']     = self.chkOrgStructure.isChecked()
            params['orgStructureId']      = self.cmbOrgStructure.value()
            params['orgStructureIdList']  = self.getOrgStructureIdList()
        if self.setupByOrgStructureVisible:
            params['reportType']          = self.cmbReportType.currentIndex()
            if self.chkAllOrgStructure.isEnabled():
                params['chkAllOrgStructure'] = self.chkAllOrgStructure.isChecked()
            else:
                params['chkAllOrgStructure'] = False
        if self.clientAgeCategoryVisible:
            params['chkClientAgeCategory']   = self.chkClientAgeCategory.isChecked()
            params['clientAgeCategory']      = self.cmbClientAgeCategory.currentIndex()
        if self.onlyClientAsPersonInLPUVisible:
            params['chkOnlyClientAsPersonInLPU'] = self.chkOnlyClientAsPersonInLPU.isChecked()
        if self.personVisible:
            params['chkPerson']                  = self.chkPerson.isChecked()
            params['personId']                   = self.cmbPerson.value()
        if self.eventStatusVisible:
            params['chkEventStatus']             = self.chkEventStatus.isChecked()
            params['eventStatus']                = self.cmbEventStatus.currentIndex()
        params['accountingSystemId']             = self.cmbAccountingSystem.value()
        params['unitId']                         = self.cmbMedicalAidUnit.value()
        params['isVAT']                          = self.chkVAT.isChecked()
        return params


    def getOrgStructureModel(self):
        return self.cmbOrgStructure.model()


    def getOrgStructureIdList(self):
        treeIndex = self.cmbOrgStructure._model.index(self.cmbOrgStructure.currentIndex(), 0, self.cmbOrgStructure.rootModelIndex())
        treeItem = treeIndex.internalPointer() if treeIndex.isValid() else None
        return treeItem.getItemIdList() if treeItem else []


    @pyqtSignature('int')
    def on_cmbReportType_currentIndexChanged(self, index):
        self.chkAllOrgStructure.setEnabled(index==1)


    @pyqtSignature('bool')
    def on_chkClass_clicked(self, bValue):
        if bValue:
            class_ = self.cmbClass.currentIndex()
        else:
            class_ = None
        self.cmbActionTypeGroup.setClass(class_)


    @pyqtSignature('int')
    def on_cmbClass_currentIndexChanged(self, index):
        self.cmbActionTypeGroup.setClass(index)


    @pyqtSignature('')
    def on_btnFinanceTypeList_clicked(self):
        self.financeTypeList = []
        self.lblFinanceTypeList.setText(u'не задано')
        dialog = CFinanceTypeListEditorDialog(self)
        if dialog.exec_():
            self.financeTypeList = dialog.values()
            if self.financeTypeList:
                db = QtGui.qApp.db
                table = db.table('rbFinance')
                records = db.getRecordList(table, [table['name']], [table['id'].inlist(self.financeTypeList)])
                nameList = []
                for record in records:
                    nameList.append(forceString(record.value('name')))
                self.lblFinanceTypeList.setText(u','.join(name for name in nameList if name))


def selectData(params):
    dateType          = params.get('dateType', 0)
    begDate           = params.get('begDate', None)
    endDate           = params.get('endDate', None)
    class_            = params.get('class', None)
    db = QtGui.qApp.db
    actionTypeGroupId = params.get('actionTypeGroupId', None)
    if actionTypeGroupId:
        actionTypeGroupIdList = db.getDescendants('ActionType', 'group_id', actionTypeGroupId)
    else:
        actionTypeGroupIdList = None
    chkStatus                  = params.get('chkStatus', False)
    status                     = params.get('status', None)
    contractIdList             = params.get('contractIdList', None)
    financeTypeList            = params.get('financeTypeList', None)
    confirmation               = params.get('confirmation', False)
    confirmationBegDate        = params.get('confirmationBegDate', None)
    confirmationEndDate        = params.get('confirmationEndDate', None)
    confirmationType           = params.get('confirmationType', 0)
    confirmationPeriodType     = params.get('confirmationPeriodType', 0)
    chkClientAgeCategory       = params.get('chkClientAgeCategory', False)
    clientAgeCategory          = params.get('clientAgeCategory', None)
    chkOnlyClientAsPersonInLPU = params.get('chkOnlyClientAsPersonInLPU', False)
    chkOrgStructure            = params.get('chkOrgStructure', False)
    orgStructureIdList         = params.get('orgStructureIdList', None)
    chkPerson                  = params.get('chkPerson', False)
    personId                   = params.get('personId', None)
    chkEventStatus             = params.get('chkEventStatus',  False)
    eventStatus                = params.get('eventStatus',  0)
    accountingSystemId         = params.get('accountingSystemId', None)
    unitId                     = params.get('unitId', None)

    tableAction            = db.table('Action')
    tableActionType        = db.table('ActionType')
    tableContract          = db.table('Contract')
    tablePriceList         = db.table('Contract').alias('ContractPriceList')
    tableAccountItem       = db.table('Account_Item')
    tableAccount           = db.table('Account')
    tableClient            = db.table('Client')
    tableClientWork        = db.table('ClientWork')
    tableEvent             = db.table('Event')
    tableEventType         = db.table('EventType')
    tableEventTypeIdentification = db.table('EventType_Identification')
    tablePerson            = db.table('vrbPersonWithSpeciality')
    tableOgrStructure      = db.table('OrgStructure')

    queryTable = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
    queryTable = queryTable.innerJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
    queryTable = queryTable.innerJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
    queryTable = queryTable.innerJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
    queryTable = queryTable.leftJoin(tableEventTypeIdentification, db.joinAnd([tableEventTypeIdentification['master_id'].eq(tableEventType['id']), tableEventTypeIdentification['deleted'].eq(0)]))
    queryTable = queryTable.innerJoin(tableContract, 'Contract.`id`=IF(Action.`contract_id`, Action.`contract_id`, Event.`contract_id`)')
    queryTable = queryTable.leftJoin(tablePriceList, tableContract['priceListExternal_id'].eq(tablePriceList['id']))
    queryTable = queryTable.innerJoin(tableAccountItem, tableAccountItem['event_id'].eq(tableEvent['id']))
    queryTable = queryTable.innerJoin(tableAccount, tableAccount['id'].eq(tableAccountItem['master_id']))
    queryTable = queryTable.leftJoin(tablePerson, tablePerson['id'].eq(tableAction['person_id']))
    queryTable = queryTable.leftJoin(tableOgrStructure, tableOgrStructure['id'].eq(tablePerson['orgStructure_id']))
    cond = [tableAction['deleted'].eq(0),
            tableActionType['deleted'].eq(0),
            tableEvent['deleted'].eq(0),
            tableAccountItem['deleted'].eq(0),
            tableAccount['deleted'].eq(0)
            ]
    if dateType:
        cond.append(tableEvent['setDate'].ge(begDate))
        cond.append(tableEvent['setDate'].lt(endDate.addDays(1)))
    else:
        cond.append(tableAction['endDate'].isNotNull())
        cond.append(tableAction['endDate'].ge(begDate))
        cond.append(tableAction['begDate'].lt(endDate.addDays(1)))
    if contractIdList:
        cond.append(tableContract['id'].inlist(contractIdList))
    if financeTypeList:
        cond.append(tableContract['finance_id'].inlist(financeTypeList))
    if confirmation:
        cond.append(tableAccountItem['master_id'].eq(tableAccount['id']))
        if confirmationType == 0:
            cond.append(tableAccountItem['id'].isNull())
        elif confirmationType == 1:
            cond.append(tableAccountItem['date'].isNotNull())
            cond.append(tableAccountItem['number'].ne(''))
        elif confirmationType == 2:
            cond.append(tableAccountItem['date'].isNotNull())
            cond.append(tableAccountItem['number'].ne(''))
            cond.append(tableAccountItem['refuseType_id'].isNull())
        elif confirmationType == 3:
            cond.append(tableAccountItem['date'].isNotNull())
            cond.append(tableAccountItem['number'].ne(''))
            cond.append(tableAccountItem['refuseType_id'].isNotNull())
        if confirmationPeriodType:
            if confirmationBegDate:
                cond.append(tableAccountItem['date'].ge(confirmationBegDate))
            if confirmationEndDate:
                cond.append(tableAccountItem['date'].lt(confirmationEndDate.addDays(1)))
        else:
            if confirmationBegDate:
                cond.append(tableAccount['date'].ge(confirmationBegDate))
            if confirmationEndDate:
                cond.append(tableAccount['date'].lt(confirmationEndDate.addDays(1)))
    if class_ is not None:
        cond.append(tableActionType['class'].eq(class_))
    if actionTypeGroupIdList:
        cond.append(tableActionType['group_id'].inlist(actionTypeGroupIdList))
    if chkStatus and status is not None:
        cond.append(tableAction['status'].eq(status))
    if chkClientAgeCategory and clientAgeCategory is not None:
        ageCond = '< 18' if clientAgeCategory == 0 else '>= 18'
        cond.append('age(Client.`birthDate`,CURRENT_DATE) %s'%ageCond)
    if chkOnlyClientAsPersonInLPU:
        clientWorkJoinCond = [tableClient['id'].eq(tableClientWork['client_id']),
                              'ClientWork.`id`=(SELECT MAX(CW.`id`) FROM ClientWork AS CW WHERE CW.`client_id`=Client.`id`)']
        queryTable = queryTable.innerJoin(tableClientWork, clientWorkJoinCond)
        cond.append(tableClientWork['org_id'].eq(QtGui.qApp.currentOrgId()))
    if chkOrgStructure and orgStructureIdList:
        cond.append(tablePerson['orgStructure_id'].inlist(orgStructureIdList))
    if chkPerson and personId:
        cond.append(tablePerson['id'].eq(personId))
    if chkEventStatus:
        cond.append(tableEvent['execDate'].isNull() if eventStatus else tableEvent['execDate'].isNotNull())
    cond.append('''Account_Item.visit_id IS NULL AND IF(Account_Item.action_id IS NOT NULL, Account_Item.action_id = Action.id, 1)''')

    cols = [tableOgrStructure['id'].alias('orgStructureId'),
            tableOgrStructure['name'].alias('orgStructureName'),
            tableAccountItem['sum'].alias('accountSum'),
            tableAccountItem['VAT'],
            tableAccountItem['price'],
            tableAccountItem['amount'],
            tableEventTypeIdentification['value'].alias('valueETI'),
            u'''EXISTS(SELECT rbFinance.id
                    FROM rbFinance
                    WHERE Contract.finance_id IS NOT NULL AND rbFinance.id = Contract.finance_id
                    AND rbFinance.code = 3) AS isDms''',
            u'''EXISTS(SELECT rbFinance.id
                    FROM rbFinance
                    WHERE Contract.finance_id IS NOT NULL AND rbFinance.id = Contract.finance_id
                    AND rbFinance.code = 4) AS isPaid''',
           ]
    if accountingSystemId:
        cond.append(tableEventTypeIdentification['system_id'].eq(accountingSystemId))
    if unitId:
        cond.append(tableAccountItem['unit_id'].eq(unitId))
    cond.append(tableEventType['deleted'].eq(0))
    stmt = db.selectStmt(queryTable, cols, cond)
    query = db.query(stmt)
    return query


class CExternalIncomePaidServices(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Внешний доход от платных медицинских услуг')


    def getSetupDialog(self, parent):
        result = CExternalIncomePaidServicesDialog(parent)
        result.setDateTypeVisible(True)
        result.setClientAgeCategoryVisible(True)
        result.setOnlyClientAsPersonInLPUVisible(True)
        result.setStrongOrgStructureVisible(True)
        result.setPersonVisible(True)
        result.setEventIdentifierTypeVisible(True)
        result.setEventStatusVisible(True)
        result.setTitle(self.title())
        return result


    def build(self, params):
        query = selectData(params)
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        tableColumns = [
                        ('10%', [u'Отделение', u''], CReportBase.AlignLeft),
                        ('5%',  [u'Итого',     u''], CReportBase.AlignRight),
                        ('5%',  [u'Итого',     u''], CReportBase.AlignRight),
                        ('5%',  [u'ИТОГО',     u''], CReportBase.AlignRight)
                        ]
        cnt = 0
        orgStructureIdList = params.get('orgStructureIdList', None)
        accountingSystemId = params.get('accountingSystemId', None)
        recordsETIList = []
        ETIList = {}
        db = QtGui.qApp.db
        if accountingSystemId:
            tableEventTypeIdentification = db.table('EventType_Identification')
            recordsETI = db.getRecordList(tableEventTypeIdentification,
                            u'''DISTINCT EventType_Identification.value''',
                            [tableEventTypeIdentification['deleted'].eq(0),
                             tableEventTypeIdentification['system_id'].eq(accountingSystemId)],
                             order = tableEventTypeIdentification['value'].name())
            for recordETI in recordsETI:
                recordsETIList.append(forceString(recordETI.value('value')))
            cnt = len(recordsETIList)
            procent = '%.2f'%(75.0/(cnt*2+4))
            for row, nameETI in enumerate(recordsETIList):
                ETILine = ETIList.setdefault(nameETI, [[], []])
                ETILine[0].append(row+1)
                if row == 0:
                    tableColumns.insert(row+1, (procent+'%', [u'Платно', nameETI], CReportBase.AlignRight))
                else:
                    tableColumns.insert(row+1, (procent+'%', [u'',       nameETI], CReportBase.AlignRight))
            for row, nameETI in enumerate(recordsETIList):
                ETILine = ETIList.setdefault(nameETI, [[], []])
                ETILine[1].append(row+cnt+2)
                if row == 0:
                    tableColumns.insert(row+cnt+2, (procent+'%', [u'ДМС', nameETI], CReportBase.AlignRight))
                else:
                    tableColumns.insert(row+cnt+2, (procent+'%', [u'',    nameETI], CReportBase.AlignRight))
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 1, cnt)
        table.mergeCells(0, cnt+1, 2, 1)
        table.mergeCells(0, cnt+2, 1, cnt)
        table.mergeCells(0, cnt+cnt+2, 2, 1)
        table.mergeCells(0, cnt+cnt+3, 2, 1)
        locale = QLocale()
        isVAT = params.get('isVAT', False)
        reportData = {}
        tableOrg = db.table('OrgStructure')
        condOrg = [tableOrg['deleted'].eq(0)]
        if orgStructureIdList:
            condOrg.append(tableOrg['id'].inlist(orgStructureIdList))
        orgRecords = db.getRecordList(tableOrg, [tableOrg['id'], tableOrg['name']], condOrg)
        for orgRecord in orgRecords:
            reportData[(forceRef(orgRecord.value('id')), forceString(orgRecord.value('name')))] = [[0]*(cnt+1), [0]*(cnt+1), 0]
        while query.next():
            record = query.record()
            orgStructureId   = forceRef(record.value('orgStructureId'))
            orgStructureName = forceString(record.value('orgStructureName'))
            accountSum       = forceDouble(record.value('accountSum'))
            valueETI         = forceString(record.value('valueETI'))
            isDms            = forceBool(record.value('isDms'))
            isPaid           = forceBool(record.value('isPaid'))
            if isVAT:
                VAT          = forceDouble(record.value('VAT'))
                amount       = forceDouble(record.value('amount'))
                price        = forceDouble(record.value('price'))
                sumIsVat     = accountSum - (((price*VAT)/(100+VAT))*amount)
            else:
                sumIsVat     = accountSum
            reportLine = reportData.get((orgStructureId, orgStructureName), [[0]*(cnt+1), [0]*(cnt+1), 0])
            reportTotal = reportLine[2]
            ETILine = ETIList.get(valueETI, None)
            if ETILine:
                ETIPaid = ETILine[0]
                ETIDms = ETILine[1]
                if isPaid:
                    reportPaid = reportLine[0]
                    for col in ETIPaid:
                        reportPaid[col-1] += sumIsVat
                    reportPaid[cnt] += sumIsVat
                    reportTotal += sumIsVat
                elif isDms:
                    reportDms = reportLine[1]
                    for col in ETIDms:
                        reportDms[col-len(reportDms)-1] += sumIsVat
                    reportDms[len(reportDms)-1] += sumIsVat
                    reportTotal += sumIsVat
            reportLine[2] = reportTotal
            reportData[(orgStructureId, orgStructureName)] = reportLine
        keysOrg = reportData.keys()
        keysOrg.sort(key=lambda x: x[1].lower())
        total = [0]*(cnt*2+3)
        for keyOrg in keysOrg:
            reportLine = reportData.get(keyOrg, [[0]*(cnt+1), [0]*(cnt+1), 0])
            i = table.addRow()
            table.setText(i, 0, keyOrg[1])
            for numb, values in enumerate(reportLine):
                if numb == 0:
                    reportPaid = values
                    for col, val in enumerate(reportPaid):
                        table.setText(i, col+1, locale.toString(float(val), 'f', 2))
                        total[col] += val
                elif numb == 1:
                    reportDms = values
                    for col, val in enumerate(reportDms):
                        table.setText(i, col+cnt+2, locale.toString(float(val), 'f', 2))
                        total[col+len(reportPaid)] += val
                elif numb == 2:
                    table.setText(i, len(tableColumns)-1, locale.toString(float(values), 'f', 2))
                    total[cnt*2+2] += values
        if reportData:
            i = table.addRow()
            table.setText(i, 0, u'ИТОГО', CReportBase.TableTotal)
            for col, val in enumerate(total):
                table.setText(i, col+1, locale.toString(float(val), 'f', 2), CReportBase.TableTotal)
        return doc


    def getDescription(self, params):
        dateType          = params.get('dateType', None)
        begDate           = params.get('begDate', None)
        endDate           = params.get('endDate', None)
        class_            = params.get('class', None)
        actionTypeGroupId = params.get('actionTypeGroupId', None)
        chkStatus         = params.get('chkStatus', False)
        status            = params.get('status', None)
        chkGroupByPatient = params.get('chkGroupByPatient', None)
        contractText      = params.get('contractText', None)
        financeText       = params.get('financeText', None)
        confirmation      = params.get('confirmation', False)
        confirmationBegDate = params.get('confirmationBegDate', None)
        confirmationEndDate = params.get('confirmationEndDate', None)
        confirmationType    = params.get('confirmationType', 0)
        confirmationPeriodType = params.get('confirmationPeriodType', 0)
        unitId                 = params.get('unitId', None)
        accountingSystemId     = params.get('accountingSystemId', None)
        isVAT                  = params.get('isVAT', False)
        rows = []
        if dateType is not None:
            rows.append(u'Тип дат: %s'%[u'Даты оказания услуги', u'Даты события'][dateType])
        if begDate:
            rows.append(u'Начальная дата периода: %s'%forceString(begDate))
        if endDate:
            rows.append(u'Конечная дата периода: %s'%forceString(endDate))
        if unitId:
            rows.append(u'Единица измерения: %s'%forceString(QtGui.qApp.db.translate('rbMedicalAidUnit', 'id', unitId, 'CONCAT(code, \' | \', name)')))
        if accountingSystemId:
            rows.append(u'Внешняя учетная система: %s'%forceString(QtGui.qApp.db.translate('rbAccountingSystem', 'id', accountingSystemId, 'CONCAT(code, \' | \', name)')))
        if class_ is not None:
            rows.append(u'Класс типов действия: %s'%[u'статус', u'диагностика', u'лечение', u'прочие мероприятия'][class_])
        if actionTypeGroupId:
            rows.append(u'Группа типов действий: %s'%forceString(QtGui.qApp.db.translate('ActionType', 'id', actionTypeGroupId, 'CONCAT(code, \' | \', name)')))
        if chkStatus and status is not None:
            rows.append(u'Статус: %s'%CActionStatus.text(status))
        if params.get('chkDetailPerson', False):
            rows.append(u'Группировка по исполнителям')
        if chkGroupByPatient:
            rows.append(u'Группировка по пациентам')
        if financeText:
            rows.append(u'Тип финансирования: %s' % financeText)
        if contractText:
            rows.append(u'Контракт: %s' % contractText)
        chkCoefficient = params.get('chkCoefficient', False)
        if chkCoefficient:
            rows.append(u'Учитывать коэффициенты')
        if confirmation:
            rows.append(u'Тип подтверждения: %s'%{0: u'не выставлено',
                                                  1: u'выставлено',
                                                  2: u'оплачено',
                                                  3: u'отказано'}.get(confirmationType, u'не выставлено'))
            rows.append(u'Период подтверждения: %s'%{0: u'по дате формирования счета',
                                                     1: u'по дате подтверждения оплаты'}.get(confirmationPeriodType, u'по дате формирования счета'))
            if confirmationBegDate:
                rows.append(u'Начало периода подтверждения: %s'%forceString(confirmationBegDate))
            if confirmationEndDate:
                rows.append(u'Окончание периода подтверждения: %s'%forceString(confirmationEndDate))
        if isVAT:
            rows.append(u'Без учёта НДС')
        rows.append(u'отчёт составлен: '+forceString(QDateTime.currentDateTime()))
        return rows

