# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2021 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignature, SIGNAL, QDate, QVariant

from Reports.Utils import _getChiefName
from library.Utils              import calcAgeTuple, forceDate, forceDouble, forceInt, forceRef, forceString, forceStringEx, formatDate, formatName, nameCase, trim
from library.TableView          import CTableView
from library.DialogBase         import CConstructHelperMixin
from library.AmountToWords      import amountToWords

from KLADR.KLADRModel           import getMainRegionName
from Events.ContractTariffCache import CContractTariffCache
from Events.Utils               import recordAcceptable
from Events.MapActionTypeToServiceIdList import CMapActionTypeIdToServiceIdList
from Registry.Utils             import getClientInfoEx
from Registry.RegistryTable     import CClientsTableModel
from Reports.ReportBase         import CReportBase, createTable
from Reports.Report             import CReport
from Reports.ReportView         import CReportViewDialog

from Reports.Ui_ReportClientActionsSetup          import Ui_ReportClientActionsSetupDialog
from Reports.Ui_ReportClientSubsidiarySetupDialog import Ui_ReportClientSubsidiarySetupDialog


def getClientId(params):
    actionDateTypeValue    = params.get('actionDateTypeValue', 'begDate')
    begDate                = params.get('begDate', None)
    endDate                = params.get('endDate', None)
    chkClientCode          = params.get('chkClientCode', False)
    clientCode             = params.get('clientCode', None)
    accountingSystemId     = params.get('accountingSystemId', None)
    lastName               = params.get('lastName', None)
    firstName              = params.get('firstName', None)
    patrName               = params.get('patrName', None)
    birthDate              = params.get('birthDate', None)
    docType                = params.get('docType', None)
    leftSerial             = params.get('leftSerial', None)
    rightSerial            = params.get('rightSerial', None)
    number                 = params.get('number', None)
    policyType             = params.get('policyType', None)
    policySerial           = params.get('policySerial', None)
    policyNumber           = params.get('policyNumber', None)
    policyCompany          = params.get('policyCompany', None)
    contact                = params.get('contact', None)

    db = QtGui.qApp.db

    needJoinClientIdentification = bool(accountingSystemId)
    needJoinDocument             = (docType or (leftSerial and rightSerial) or number) and not chkClientCode
    needJoinPolicy               = (policyType or policySerial or policyNumber or policyCompany) and not chkClientCode
    needJoinContact              = bool(contact)

    tableClient               = db.table('Client')
    tableClientContact        = db.table('ClientContact')
    tableClientPolicy         = db.table('ClientPolicy')
    tableClientDocument       = db.table('ClientDocument')
    tableClientIdentification = db.table('ClientIdentification')

    tableAction               = db.table('Action')
    tableEvent                = db.table('Event')

    queryTable = tableClient.innerJoin(tableEvent, tableClient['id'].eq(tableEvent['client_id']))
#    queryTable = queryTable.innerJoin( tableEvent, tableEvent['id'].eq(tableAction['event_id']))

    if chkClientCode:
        if needJoinClientIdentification:
            queryTable = queryTable.innerJoin(tableClientIdentification,
                                              tableClientIdentification['client_id'].eq(tableClient['id']))
    else:
        if needJoinDocument:
            queryTable = queryTable.innerJoin(tableClientDocument,
                                              tableClientDocument['client_id'].eq(tableClient['id']))
        if needJoinPolicy:
            queryTable = queryTable.innerJoin(tableClientPolicy,
                                              tableClientPolicy['client_id'].eq(tableClient['id']))
        if needJoinContact:
            queryTable = queryTable.innerJoin(tableClientContact,
                                              tableClientContact['client_id'].eq(tableClient['id']))
    actionCond = '''
                    EXISTS (SELECT Action.`id` FROM Action WHERE %s AND %s AND %s AND Action.`event_id`=Event.`id`)
                 ''' %(tableAction[actionDateTypeValue].ge(begDate),
                       tableAction[actionDateTypeValue].lt(endDate.addDays(1)),
                       tableAction['deleted'].eq(0))

    cond = [actionCond, tableEvent['deleted'].eq(0)]

    if chkClientCode:
        if accountingSystemId:
            cond.append(tableClientIdentification['accountingSystem_id'].eq(accountingSystemId))
            if clientCode:
                cond.append(tableClientIdentification['identifier'].eq(clientCode))
        else:
            if clientCode:
                cond.append(tableClient['id'].eq(clientCode))
    else:
        if lastName:
            cond.append(tableClient['lastName'].eq(nameCase(lastName)))
        if firstName:
            cond.append(tableClient['firstName'].eq(nameCase(firstName)))
        if patrName:
            cond.append(tableClient['patrName'].eq(nameCase(patrName)))
        if birthDate:
            cond.append(tableClient['birthDate'].eq(birthDate))

        if docType:
            cond.append(tableClientDocument['documentType_id'].eq(docType))
        if leftSerial and rightSerial:
            serial = ' '.join([trim(leftSerial), trim(rightSerial)])
            cond.append(tableClientDocument['serial'].eq(serial))
        if number:
            cond.append(tableClientDocument['number'].eq(number))

        if policyType:
            cond.append(tableClientPolicy['policyType_id'].eq(policyType))
        if policySerial:
            cond.append(tableClientPolicy['serial'].eq(policySerial))
        if policyNumber:
            cond.append(tableClientPolicy['number'].eq(policyNumber))
        if policyCompany:
            cond.append(tableClientPolicy['insurer_id'].eq(policyCompany))

        if contact:
            cond.append(tableClientContact['contact'].eq(contact))

    idField =  tableClient['id'].alias('clientId')

    order =  [
              tableClient['lastName'].name(),
              tableClient['firstName'].name(),
              tableClient['patrName'].name()
             ]

    idList  = db.getDistinctIdList(queryTable, idField, cond, order)
    selectedClientId = None
    QtGui.qApp.restoreOverrideCursor()
    if idList:
        if len(idList) > 1:
            clientCheckerDialog = CClientCheckerDialog(idList)
            clientCheckerDialog.exec_()
            selectedClientId = clientCheckerDialog.selectedClientId()
        else:
            selectedClientId = idList[0]
    QtGui.qApp.setWaitCursor()
    return selectedClientId




# #############################################################################
#                                                                             #
#                              variant two                                    #
#                      price like in EventCachPage                            #
#                                                                             #
# #############################################################################


def selectData2(params, clientId = None):
    chkClientCode          = params.get('chkClientCode', False)
    clientCode             = params.get('clientCode', None)
    accountingSystemId     = params.get('accountingSystemId', None)
    lastName               = params.get('lastName', None)
    firstName              = params.get('firstName', None)
    patrName               = params.get('patrName', None)
    birthDate              = params.get('birthDate', None)
    docType                = params.get('docType', None)
    leftSerial             = params.get('leftSerial', None)
    rightSerial            = params.get('rightSerial', None)
    number                 = params.get('number', None)
    policyType             = params.get('policyType', None)
    policySerial           = params.get('policySerial', None)
    policyNumber           = params.get('policyNumber', None)
    policyCompany          = params.get('policyCompany', None)
    contact                = params.get('contact', None)
    actionDateTypeValue    = params.get('actionDateTypeValue', 'begDate')
    begDate                = params.get('begDate', None)
    endDate                = params.get('endDate', None)
    contractIdList         = params.get('contractIdList', None)
    financeId              = params.get('financeId', None)
    resultTypeIndex        = params.get('resultTypeIndex', 0)
    mkbDiagnosis           = params.get('mkbDiagnosis', '')
    payededOrg             = params.get('payededOrg', None)
    chkCoefficient         = params.get('chkCoefficient', False)

    needJoinClientIdentification = bool(accountingSystemId)
    needJoinDocument             = (docType or (leftSerial and rightSerial) or number) and not chkClientCode
    needJoinPolicy               = (policyType or policySerial or policyNumber or policyCompany) and not chkClientCode
    needJoinContact              = contact and not chkClientCode

    db = QtGui.qApp.db

    tableAction               = db.table('Action')
    tableActionType           = db.table('ActionType')
    tablePerson               = db.table('Person')
    tableEvent                = db.table('Event')
    tableContract             = db.table('Contract')
    tableFinance              = db.table('rbFinance')
    tableClient               = db.table('Client')
    tableClientContact        = db.table('ClientContact')
    tableClientPolicy         = db.table('ClientPolicy')
    tableClientDocument       = db.table('ClientDocument')
    tableClientIdentification = db.table('ClientIdentification')
    queryTable = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
    queryTable = queryTable.leftJoin(tablePerson, tablePerson['id'].eq(tableAction['person_id']))
    queryTable = queryTable.innerJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
    queryTable = queryTable.innerJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
    queryTable = queryTable.innerJoin(tableContract, 'Contract.`id`=IF(Action.`contract_id`, Action.`contract_id`, Event.`contract_id`)')
    queryTable = queryTable.innerJoin(tableFinance, tableFinance['id'].eq(tableContract['finance_id']))
    if chkClientCode:
        if needJoinClientIdentification:
            queryTable = queryTable.innerJoin(tableClientIdentification,
                                              tableClientIdentification['client_id'].eq(tableClient['id']))
    else:
        if needJoinDocument:
            queryTable = queryTable.innerJoin(tableClientDocument,
                                              tableClientDocument['client_id'].eq(tableClient['id']))
        if needJoinPolicy:
            queryTable = queryTable.innerJoin(tableClientPolicy,
                                              tableClientPolicy['client_id'].eq(tableClient['id']))
        if needJoinContact:
            queryTable = queryTable.innerJoin(tableClientContact,
                                              tableClientContact['client_id'].eq(tableClient['id']))
    cond = [tableAction[actionDateTypeValue].ge(begDate),
            tableAction[actionDateTypeValue].lt(endDate.addDays(1)),
            tableAction['deleted'].eq(0),
            tableEvent['deleted'].eq(0)
           ]
    if clientId or resultTypeIndex == 1:
        cond.append(tableClient['id'].eq(clientId))
    if contractIdList:
        cond.append(tableContract['id'].inlist(contractIdList))
    if financeId:
        cond.append(tableContract['finance_id'].eq(financeId))
    if mkbDiagnosis:
        cond.append('''EXISTS(SELECT Diagnosis.id
FROM Diagnosis INNER JOIN Diagnostic ON Diagnostic.diagnosis_id=Diagnosis.id
INNER JOIN rbDiagnosisType ON Diagnostic.diagnosisType_id=rbDiagnosisType.id
WHERE Diagnostic.event_id = Event.id AND Diagnosis.deleted = 0 AND Diagnosis.MKB LIKE '%s' AND Diagnostic.deleted = 0
AND (rbDiagnosisType.code = '1'
OR (rbDiagnosisType.code = '2' AND Diagnostic.person_id = Event.execPerson_id
AND (NOT EXISTS (SELECT DC.id FROM Diagnostic AS DC
INNER JOIN rbDiagnosisType AS DT ON DT.id = DC.diagnosisType_id WHERE DT.code = '1'
AND DC.event_id = Event.id
LIMIT 1)))))'''%(mkbDiagnosis))
    if payededOrg:
        tableEventLocalContract = db.table('Event_LocalContract')
        queryTable = queryTable.innerJoin(tableEventLocalContract, tableEventLocalContract['master_id'].eq(tableEvent['id']))
        cond.append(tableEventLocalContract['org_id'].eq(payededOrg))
        cond.append(tableEventLocalContract['deleted'].eq(0))
    if chkClientCode:
        if accountingSystemId:
            cond.append(tableClientIdentification['accountingSystem_id'].eq(accountingSystemId))
            if clientCode:
                cond.append(tableClientIdentification['identifier'].eq(clientCode))
        else:
            if clientCode:
                cond.append(tableClient['id'].eq(clientCode))
    else:
        if lastName:
            cond.append(tableClient['lastName'].eq(nameCase(lastName)))
        if firstName:
            cond.append(tableClient['firstName'].eq(nameCase(firstName)))
        if patrName:
            cond.append(tableClient['patrName'].eq(nameCase(patrName)))
        if birthDate:
            cond.append(tableClient['birthDate'].eq(birthDate))

        if docType:
            cond.append(tableClientDocument['documentType_id'].eq(docType))
        if leftSerial and rightSerial:
            serial = ' '.join([trim(leftSerial), trim(rightSerial)])
            cond.append(tableClientDocument['serial'].eq(serial))
        if number:
            cond.append(tableClientDocument['number'].eq(number))

        if policyType:
            cond.append(tableClientPolicy['policyType_id'].eq(policyType))
        if policySerial:
            cond.append(tableClientPolicy['serial'].eq(policySerial))
        if policyNumber:
            cond.append(tableClientPolicy['number'].eq(policyNumber))
        if policyCompany:
            cond.append(tableClientPolicy['insurer_id'].eq(policyCompany))

        if contact:
            cond.append(tableClientContact['contact'].eq(contact))

    fields =  [
              tableEvent['id'].alias('eventId'),
              tableEvent['execDate'].name(),
              tableEvent['setDate'].alias('setDate'),
              tableEvent['eventType_id'].alias('eventTypeId'),
              tableActionType['name'].alias('actionTypeName'),
              tableActionType['code'].alias('actionTypeCode'),
              tableActionType['id'].alias('actionTypeId'),
              tableAction['amount'].alias('actionAmount'),
              tableAction['id'].alias('actionId'),
              tableAction['endDate'].alias('actionEndDate'),
              'getClientRegAddress(Client.`id`) AS clientAddress',
              tableClient['id'].alias('clientId'),
              tableClient['lastName'].alias('clientLastName'),
              tableClient['firstName'].alias('clientFirstName'),
              tableClient['patrName'].alias('clientPatrName'),
              tableClient['sex'].alias('clientSex'),
              tableClient['birthDate'].alias('clientBirthDate'),
              tableContract['id'].alias('contractId'),
              tableFinance['name'].alias('financeTypeName'),
              tableFinance['id'].alias('financeId'),
              tableAction['person_id'].alias('personId'),
              tablePerson['tariffCategory_id'].alias('personTariffCategoryId'),
              tablePerson['code'].alias('personCode')
              ]

    order =  [
              tableClient['id'].name(),
              tableEvent['id'].name(),
              tableAction[actionDateTypeValue].name()
             ]

    if chkCoefficient:
        tableContractCoefficient = db.table('Contract_Coefficient')
        tableContractCoefficientType  = db.table('rbContractCoefficientType')
        queryTable = queryTable.leftJoin(tableContractCoefficient,
                                         (db.joinAnd([tableContractCoefficient['master_id'].eq(tableContract['id']),
                                                     tableContractCoefficient['deleted'].eq(0),
                                                     db.joinOr([tableContractCoefficient['begDate'].isNull(),
                                                                tableContractCoefficient['begDate'].le(endDate)])])))
        queryTable = queryTable.leftJoin(tableContractCoefficientType, tableContractCoefficientType['id'].eq(tableContractCoefficient['coefficientType_id']))
        fields.append(tableContractCoefficient['value'].alias('coefficientValue'))
        fields.append(tableContractCoefficientType['code'].alias('coefficientCode'))
        fields.append(tableContractCoefficientType['name'].alias('coefficientName'))
        fields.append(tableContractCoefficientType['id'].alias('coefficientTypeId'))
        order.append(tableActionType['code'].name())
        order.append(tableActionType['name'].name())

    stmt  = db.selectStmt(queryTable, fields, cond, order)
    query = db.query(stmt)
    return query


class CReportClientActions(CReport, CMapActionTypeIdToServiceIdList):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        CMapActionTypeIdToServiceIdList.__init__(self)
        self.parent = parent
        self.setTitle(u'Отчет работ по пациенту')
        self.contractTariffCache = CContractTariffCache()
        self.resetHelpers()

    def resetHelpers(self):
        self.mapClientIdToInfo = {}
        self.clientIdOrder = []
        self.contractNumberList = []
        self.clientActionKeysNeedFinanceTypeName = {}
        self.clientSex       = None
        self.clientAge       = None


    def reportLoop(self):
        params = self.getDefaultParams()
        while True:
            setupDialog = self.getSetupDialog(self.parent)
            setupDialog.setParams(params)
            if not setupDialog.exec_():
                break
            params = setupDialog.params()
            setupSubsidiaryDialog = self.getSubsidiarySetupDialog(self.parent)
            setupSubsidiaryDialog.setParams(params)
            if not setupSubsidiaryDialog.exec_():
                break
            paramsSubsidiary = setupSubsidiaryDialog.params()
            self.saveDefaultParams(paramsSubsidiary)
            try:
                QtGui.qApp.setWaitCursor()
                reportResult = self.build(paramsSubsidiary)
            finally:
                QtGui.qApp.restoreOverrideCursor()
            viewDialog = CReportViewDialog(self.parent)
            if self.viewerGeometry:
                viewDialog.restoreGeometry(self.viewerGeometry)
            viewDialog.setWindowTitle(self.title())
            viewDialog.setRepeatButtonVisible()
            viewDialog.setText(reportResult)
            done = not viewDialog.exec_()
            self.viewerGeometry = viewDialog.saveGeometry()
            if done:
                break


    def getSetupDialog(self, parent):
        result = CReportClientActionsSetupDialog(parent, self)
        result.setTitle(self.title())
        return result


    def getSubsidiarySetupDialog(self, parent):
        result = CReportClientSubsidiarySetupDialog(parent, self)
        result.setTitle(self.title())
        return result


    def build(self, params):
        self.resetHelpers()
        clientId = None
        resultTypeIndex = params.get('resultTypeIndex', 0)
        chkCoefficient = params.get('chkCoefficient', False)
        if resultTypeIndex == 1:
            clientId = getClientId(params)
        query = selectData2(params, clientId)
        detailDateAndPersonCode = params.get('detailDateAndPersonCode', False)
        self.structInfo(params, query, detailDateAndPersonCode)
        doc = QtGui.QTextDocument()
        if query is None:
            return doc
        cursor = QtGui.QTextCursor(doc)
        if resultTypeIndex == 1 and clientId:
            self.setReportHeaderForAct(cursor, clientId, params)
        else:
            cursor.setCharFormat(CReportBase.ReportTitle)
            cursor.insertText(self.title())
            cursor.insertBlock()
            self.dumpParams(cursor, params)
            cursor.insertBlock()
        tableColumns = [
                        ('%2',
                        [u'№'], CReportBase.AlignLeft),
                        ('%7',
                        [u'Код услуги'], CReportBase.AlignLeft),
                        ('%15',
                        [u'Наименование услуги'], CReportBase.AlignLeft),
                        ('%5',
                        [u'Количество'], CReportBase.AlignLeft),
                        ('%6',
                        [u'Стоимость.руб'], CReportBase.AlignLeft),
                        ('%6',
                        [u'Сумма.руб'], CReportBase.AlignLeft)
                       ]
        if chkCoefficient:
            tableColumns.append(('%5',[u'Наименование коэффициента'], CReportBase.AlignLeft))
            tableColumns.append(('%5',[u'Коэффициент'], CReportBase.AlignLeft))
            tableColumns.append(('%5',[u'Значение коэффициента'], CReportBase.AlignLeft))
            tableColumns.append(('%5',[u'Итого'], CReportBase.AlignLeft))
        if detailDateAndPersonCode:
            tableColumns.extend(
                                [('%8',
                                [u'Дата оказания услуги'], CReportBase.AlignLeft),
                                ('%8',
                                [u'Код врача'], CReportBase.AlignLeft)]
                               )
        mergeLength = len(tableColumns)
        table = createTable(cursor, tableColumns)
        boldChars = QtGui.QTextCharFormat()
        boldChars.setFontWeight(QtGui.QFont.Bold)
        result = [0, 0, 0, 0]
        actionIdx = 0
        rowKeySum = 1
        prevKeySum = ()
        for clientId in self.clientIdOrder:
            printClientInfo = False or (resultTypeIndex == 1)
            clientInfo = self.mapClientIdToInfo.get(clientId, None)
            if not clientInfo:
                continue
            if not printClientInfo:
                clientName, clientAddress = clientInfo['aboutClient']
                i = table.addRow()
                table.setText(i, 0, clientName+u', карта №: %d'%clientId, charFormat=boldChars)
                i = table.addRow()
                table.setText(i, 0, clientAddress, charFormat=boldChars)
                table.mergeCells(i-1, 0, 2, mergeLength)
            clientActions = clientInfo['clientActions']
            actionKeys = clientActions.keys()
            actionKeys.sort()
            clientResult = [0, 0, 0, 0]
            for key in actionKeys:
                actionIdx += 1
                i = table.addRow()
                table.setText(i, 0, actionIdx)
                actionInfo = clientActions[key]
                actionTypeCode  = key[1]
                actionTypeName  = key[0]
                financeTypeName = key[2]
                actionAmount    = actionInfo['actionAmount']
                price           = actionInfo['price']
                sum             = actionInfo['sum']
                if chkCoefficient:
                    table.setText(i, 6, actionInfo['coefficientName'])
                    table.setText(i, 7, actionInfo['coefficientValue'])
                    table.setText(i, 8, actionInfo['sumCoefficient'])
                    keySum = actionInfo['keySum']
                    if prevKeySum != keySum:
                        prevKeySum = keySum
                        priceSumCoefficient = self.sumCoefficientList.get(keySum, 0.0)
                        table.setText(i, 9, priceSumCoefficient)
                        clientResult[0] += actionAmount
                        clientResult[2] += sum
                        clientResult[3] += priceSumCoefficient
                        table.setText(i, 1, actionTypeCode)
                        financeTypeAdditionIfNeed = self.getFinanceTypeAdditionIfNeed(clientId,
                                                                                      actionTypeCode,
                                                                                      actionTypeName,
                                                                                      financeTypeName)
                        table.setText(i, 2, actionTypeName+financeTypeAdditionIfNeed)
                        table.setText(i, 3, actionAmount)
                        table.setText(i, 4, price)
                        table.setText(i, 5, sum)
                        if detailDateAndPersonCode:
                            table.setText(i, 10, actionInfo['actionEndDate'])
                            table.setText(i, 11, actionInfo['personCode'])
                        rowKeySum = i
                    table.mergeCells(rowKeySum, 1, i-rowKeySum+1, 1)
                    table.mergeCells(rowKeySum, 2, i-rowKeySum+1, 1)
                    table.mergeCells(rowKeySum, 3, i-rowKeySum+1, 1)
                    table.mergeCells(rowKeySum, 4, i-rowKeySum+1, 1)
                    table.mergeCells(rowKeySum, 5, i-rowKeySum+1, 1)
                    table.mergeCells(rowKeySum, 9, i-rowKeySum+1, 1)
                    if detailDateAndPersonCode:
                        table.mergeCells(rowKeySum, 10, i-rowKeySum+1, 1)
                        table.mergeCells(rowKeySum, 11, i-rowKeySum+1, 1)
                else:
                    table.setText(i, 1, actionTypeCode)
                    financeTypeAdditionIfNeed = self.getFinanceTypeAdditionIfNeed(clientId,
                                                                                  actionTypeCode,
                                                                                  actionTypeName,
                                                                                  financeTypeName)
                    table.setText(i, 2, actionTypeName+financeTypeAdditionIfNeed)
                    table.setText(i, 3, actionAmount)
                    table.setText(i, 4, price)
                    table.setText(i, 5, sum)
                    clientResult[0] += actionAmount
                    clientResult[2] += sum
                    if detailDateAndPersonCode:
                        table.setText(i, 6, actionInfo['actionEndDate'])
                        table.setText(i, 7, actionInfo['personCode'])

            if len(self.clientIdOrder) > 1:
                i = table.addRow()
                table.setText(i, 2, u'Итого', charFormat=boldChars)
                table.mergeCells(i, 0, 1, 3)
                table.setText(i, 3, clientResult[0], charFormat=boldChars)
                table.setText(i, 5, clientResult[2], charFormat=boldChars)
                if chkCoefficient:
                    table.setText(i, 9, clientResult[3], charFormat=boldChars)
            result[0] += clientResult[0]
            result[2] += clientResult[2]
            if chkCoefficient:
                result[3] += clientResult[3]
        i = table.addRow()
        table.setText(i, 2, u'Всего', charFormat=boldChars)
        table.mergeCells(i, 0, 1, 3)
        table.setText(i, 3, result[0], charFormat=boldChars)
        table.setText(i, 5, result[2], charFormat=boldChars)
        if chkCoefficient:
            table.setText(i, 9, result[3], charFormat=boldChars)
        cursor.movePosition(QtGui.QTextCursor.End)
        resultPriceText = amountToWords(result[2])
        cursor.insertBlock(CReportBase.AlignCenter)
        cursor.insertText(u'\n\n'+resultPriceText)
        if resultTypeIndex == 1:
            chiefPref = u'Директор'
            chief = _getChiefName(QtGui.qApp.currentOrgId())
            chiefLine = u'_'*(40-len(chief))
            if chief:
                chief = chiefPref+chiefLine+chief
            else:
                chief = chiefPref+chiefLine
            cursor.insertBlock(CReportBase.AlignLeft)
            cursor.insertText(u'\n\n'+chief)
            underLineChars = QtGui.QTextCharFormat()
            underLineChars.setUnderlineStyle(QtGui.QTextCharFormat.SingleUnderline)
            cursor.insertBlock(CReportBase.AlignCenter, underLineChars)
            cursor.insertText(u'\n\n'+forceString(QDate.currentDate()))
        return doc


    def getFinanceTypeAdditionIfNeed(self, clientId, actionTypeCode, actionTypeName, financeTypeName):
        actionKey = self.clientActionKeysNeedFinanceTypeName.get(clientId, {})
        financeTypeList = actionKey.get((actionTypeName, actionTypeCode), [])
        if len(financeTypeList) > 1:
            return '('+financeTypeName+')'
        return ''


    def structInfo(self, params, query, detailActions=False):
        chkCoefficient = params.get('chkCoefficient', False)
        existActionIdList = []
        contractIdList = []
        self.sumCoefficientList = {}
        while query.next():
            record = query.record()

            actionId       = forceRef(record.value('actionId'))
            if chkCoefficient:
                coefficientTypeId = forceRef(record.value('coefficientTypeId'))
                coefficientValue = forceDouble(record.value('coefficientValue'))
                coefficientName = forceString(record.value('coefficientName'))
                if (actionId, coefficientTypeId) in existActionIdList:
                    continue
                existActionIdList.append((actionId, coefficientTypeId))
            else:
                if actionId in existActionIdList:
                    continue
                existActionIdList.append(actionId)

            actionAmount    = forceDouble(record.value('actionAmount'))
            if not actionAmount:
                continue
            contractId      = forceRef(record.value('contractId'))
            actionTypeId    = forceRef(record.value('actionTypeId'))
            financeId       = forceRef(record.value('financeId'))
            actionTypeName  = forceString(record.value('actionTypeName'))
            actionTypeCode  = forceString(record.value('actionTypeCode'))
            clientId        = forceRef(record.value('clientId'))
            clientSex       = forceInt(record.value('clientSex'))
            clientBirthDate = forceDate(record.value('clientBirthDate'))
            financeTypeName = forceString(record.value('financeTypeName'))
            eventTypeId     = forceRef(record.value('eventTypeId'))
            eventSetDate    = forceDate(record.value('setDate'))
            eventExecDate   = forceDate(record.value('execDate'))
            tariffCategoryId = forceRef(record.value('personTariffCategoryId'))
            actionEndDate   = forceString(record.value('actionEndDate'))
            personCode      = forceString(record.value('personCode'))
            eventDate = eventExecDate if eventExecDate else eventSetDate
            if clientId not in self.clientIdOrder:
                self.clientIdOrder.append(clientId)
            clientName     = formatName(
                                        record.value('clientLastName'),
                                        record.value('clientFirstName'),
                                        record.value('clientPatrName')
                                       )
            clientAddress  = forceString(record.value('clientAddress'))
            self.setCurrentEventTypeId(eventTypeId)
            self.updateClientInfo(clientSex, clientBirthDate, eventDate)
            serviceIdList = self.getActionTypeServiceIdList(actionTypeId, financeId)
            price = CContractTariffCache.getPrice(self.getTariffMap(contractId), serviceIdList, tariffCategoryId)
            if not price:
                continue
            if contractId not in contractIdList:
                contractIdList.append(contractId)
            clientInfo = self.mapClientIdToInfo.setdefault(clientId, {})
            if not clientInfo:
                clientInfo['aboutClient'] = [clientName, clientAddress]
            clientActions = clientInfo.setdefault('clientActions', {})
            if chkCoefficient:
                keySum = (actionTypeName, actionTypeCode, financeTypeName)
                key = (actionTypeName, actionTypeCode, financeTypeName, coefficientTypeId)
            else:
                key = (actionTypeName, actionTypeCode, financeTypeName)
            if detailActions:
                key = key + (actionId, )
            if chkCoefficient:
                actionTypeValues = clientActions.setdefault(key, {'actionsCount':0,
                                                              'actionAmount':0,
                                                              'price':price,
                                                              'sum':0,
                                                              'coefficientTypeId':None,
                                                              'coefficientName':'',
                                                              'sumCoefficient':0.0,
                                                              'rezCoefficient':actionAmount*price})
            else:
                actionTypeValues = clientActions.setdefault(key, {'actionsCount':0,
                                                              'actionAmount':0,
                                                              'price':price,
                                                              'sum':0})
            actionTypeValues['actionsCount'] += 1
            actionTypeValues['actionAmount'] += actionAmount
            actionTypeValues['sum']          += actionAmount*price
            if detailActions:
                actionTypeValues['actionEndDate'] = actionEndDate
                actionTypeValues['personCode']    = personCode
            if chkCoefficient:
                sumCoefficient = (actionAmount*price)*coefficientValue/100.0
                actionTypeValues['coefficientTypeId'] = coefficientTypeId
                actionTypeValues['coefficientName'] = coefficientName
                actionTypeValues['coefficientValue'] = coefficientValue
                actionTypeValues['sumCoefficient'] += sumCoefficient
                actionTypeValues['keySum'] = keySum
                priceSumCoefficient = self.sumCoefficientList.get(keySum, actionAmount*price)
                actionTypeValues['rezCoefficient'] = priceSumCoefficient+sumCoefficient
                self.sumCoefficientList[keySum] = priceSumCoefficient + sumCoefficient
            actionKey = self.clientActionKeysNeedFinanceTypeName.setdefault(clientId, {(actionTypeName, actionTypeCode):[financeTypeName]})
            financeTypeNameList = actionKey.setdefault((actionTypeName, actionTypeCode), [])
            if financeTypeName not in financeTypeNameList:
                financeTypeNameList.append(financeTypeName)
        self.formatContractIdList(contractIdList)


    def formatContractIdList(self, contractIdList):
        db = QtGui.qApp.db
        table = db.table('Contract')
        recordList = db.getRecordList(table, 'number', table['id'].inlist(contractIdList))
        result = []
        for record in recordList:
            result.append(forceString(record.value('number')))
        self.contractNumberList = result


    def setReportHeaderForAct(self, cursor, clientId, params):
        boldChars = QtGui.QTextCharFormat()
        boldChars.setFontWeight(QtGui.QFont.Bold)

        clientInfo = getClientInfoEx(clientId)
        cursor.setCharFormat(CReportBase.ReportTitle)
        orgName = forceString(QtGui.qApp.db.translate('Organisation', 'id', QtGui.qApp.currentOrgId(), 'shortName'))
        cursor.insertText(orgName)

        cursor.insertBlock(CReportBase.AlignLeft)
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertText(u'Договор: '+', '.join(self.contractNumberList))

        cursor.insertBlock(CReportBase.AlignCenter)
        cursor.insertText('\n'+self.title())

        cursor.insertBlock()
        begDate = params.get('begDate', None)
        endDate = params.get('endDate', None)
        periodText = u'период: с %s по %s' %(forceString(begDate), forceString(endDate))
        cursor.insertText(periodText)

        cursor.insertBlock(CReportBase.AlignLeft)
        financeText = params.get('financeText', None)
        financeText = financeText if financeText else u'не уточнен'
        cursor.insertText(u'\nИсточник финансирования: %s'%financeText)

        cursor.insertBlock()
        cursor.insertText(u'Пациент: ')
        cursor.insertText(clientInfo.fullName, boldChars)

        cursor.insertBlock()
        cursor.insertText(u'Дата рождения: %s'%formatDate(clientInfo.birthDate), CReportBase.ReportBody)

        cursor.insertBlock()
        cursor.insertText(u'Карта, №: %d'%clientInfo.id)

        try:
            region = getMainRegionName(clientInfo.regAddressInfo.KLADRCode)
        except:
            region = u'не определен'
        cursor.insertBlock()
        cursor.insertText(u'Регион: %s'%region)

        cursor.insertBlock()
        address = clientInfo.regAddress
        cursor.insertText(u'Адрес: %s'%address)


    def getDescription(self, params):
        chkClientCode          = params.get('chkClientCode', False)
        clientCode             = params.get('clientCode', '')
        accountingSystemId     = params.get('accountingSystemId', None)
        lastName               = params.get('lastName', '')
        firstName              = params.get('firstName', '')
        patrName               = params.get('patrName', '')
        birthDate              = params.get('birthDate', None)
        docType                = params.get('docType', None)
        leftSerial             = params.get('leftSerial', '')
        rightSerial            = params.get('rightSerial', '')
        number                 = params.get('number', '')
        policyType              = params.get('policyType', None)
        policySerial            = params.get('policySerial', '')
        policyNumber            = params.get('policyNumber', '')
        policyCompany           = params.get('policyCompany', None)
        contact                = params.get('contact', '')
        actionDateTypeText     = params.get('actionDateTypeText', None)
        begDate                = params.get('begDate', None)
        endDate                = params.get('endDate', None)
        contractText           = params.get('contractText', None)
        financeText            = params.get('financeText', None)
        mkbDiagnosis           = params.get('mkbDiagnosis', '')
        payededOrg             = params.get('payededOrg', None)

        rows = []
        if actionDateTypeText:
            rows.append(u'Учитывается %s'%actionDateTypeText)
        if begDate:
            rows.append(u'Начальная дата периода: %s'%forceString(begDate))
        if endDate:
            rows.append(u'Конечная дата периода: %s'%forceString(endDate))
        if financeText:
            rows.append(u'Тип финансирования: %s' % financeText)
        if contractText:
            rows.append(u'Контракт: %s' % contractText)
        if payededOrg:
            rows.append(u'Плательщик: %s' % forceString(QtGui.qApp.db.translate('Organisation', 'id', payededOrg, 'shortName')))
        if mkbDiagnosis:
            rows.append(u'Диагноз: %s' % mkbDiagnosis)

        db = QtGui.qApp.db
        if chkClientCode:
            if accountingSystemId:
                accountingSysteName = forceString(db.translate('rbAccountingSystem', 'id', accountingSystemId, 'name'))
            if clientCode:
                if accountingSystemId:
                    rows.append(u'Код: %s %s'%(accountingSysteName, clientCode))
                else:
                    rows.append(u'Карта, №: %s'%clientCode)
        else:
            if lastName:
                rows.append(u'Фамилия: %s'%lastName)
            if firstName:
                rows.append(u'Имя: %s'%firstName)
            if patrName:
                rows.append(u'Отчество: %s'%patrName)
            if birthDate:
                rows.append(u'Дата рождения: %s'%forceString(birthDate))
            if docType:
                docTypeName = forceString(db.translate('rbDocumentType', 'id', docType, 'name'))
                rows.append(u'Тип документа: %s'%docTypeName)
            if leftSerial:
                rows.append(u'Левая часть серии документа: %s'%leftSerial)
            if rightSerial:
                rows.append(u'Правая часть серии документа: %s'%rightSerial)
            if number:
                rows.append(u'Номер документа: %s'%number)
            if policyType:
                policyTypeName = forceString(db.translate('rbPolicyType', 'id', policyType, 'name'))
                rows.append(u'Тип полиса: %s'%policyTypeName)
            if policySerial:
                rows.append(u'Серия полиса: %s'%policySerial)
            if policyNumber:
                rows.append(u'Номер полиса: %s'%policyNumber)
            if policyCompany:
                policyCompanyName = forceString(db.translate('Organisation', 'id', policyCompany, 'shortName'))
                rows.append(u'Страховая компания: %s'%policyCompanyName)
            if contact:
                rows.append(u'Контакт: %s'%contact)
        chkCoefficient = params.get('chkCoefficient', False)
        if chkCoefficient:
            rows.append(u'Учитывать коэффициенты')
        return rows


    def getTariffMap(self, contractId):
        tariffDescr = self.contractTariffCache.getTariffDescr(contractId, self)
        return tariffDescr.actionTariffMap


    def setCurrentEventTypeId(self, eventTypeId):
        self._currentEventTypeId = eventTypeId

    def getEventTypeId(self):
        return self._currentEventTypeId


    def updateClientInfo(self, clientSex, clientBirthDate, eventDate):
        self.clientSex       = clientSex
        self.clientAge       = calcAgeTuple(clientBirthDate, eventDate)


    def recordAcceptable(self, record):
        return recordAcceptable(self.clientSex, self.clientAge, record)


class CReportClientActionsSetupDialog(QtGui.QDialog, Ui_ReportClientActionsSetupDialog):
    def __init__(self, parent, report):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self._report = report
        self.contractIdListPayededOld = None
        self.actionDateValuePayededOld = ''
        self.financeIdPayededOld = None
        self.begDatePayededOld = QDate()
        self.endDatePayededOld = QDate()

        self.contractIdListMKBOld = None
        self.actionDateValueMKBOld = ''
        self.financeIdMKBOld = None
        self.begDateMKBOld = QDate.currentDate()
        self.endDateMKBOld = QDate.currentDate()

        self.cmbFinance.setTable('rbFinance', addNone=True)
        self.cmbAccountingSystem.setTable('rbAccountingSystem', True, filter='showInClientInfo = 1')
        self.cmbDocType.setTable('rbDocumentType', True, 'group_id IN (SELECT id FROM rbDocumentTypeGroup WHERE code=\'1\')')
        self.cmbPolicyType.setTable('rbPolicyType', True)
        self.valuesCmbActionDateType =  [
                                        (u'дата назначения', QVariant(u'directionDate')),
                                        (u'дата начала',     QVariant(u'begDate')),
                                        (u'дата выполнения', QVariant(u'endDate'))
                                        ]
        self.loadCmbActionDateType()


    def loadCmbActionDateType(self):
        self.cmbActionDateType.clear()
        for text, data in self.valuesCmbActionDateType:
            self.cmbActionDateType.addItem(text, data)


    def accept(self):
        if self.chkClientCode.isChecked():
            if not self.cmbAccountingSystem.value():
                try:
                    int(trim(self.edtClientCode.text()))
                except ValueError:
                    QtGui.QMessageBox.critical(QtGui.qApp.mainWindow,
                                               u'Внимание!',
                                               u'Идентификационный код пациента введен неверно!',
                                               QtGui.QMessageBox.Ok)
                    return None
        QtGui.QDialog.accept(self)


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        self.cmbResultType.setCurrentIndex(params.get('resultTypeIndex', 0))
        self.chkDetailDateAndPersonCode.setChecked(params.get('detailDateAndPersonCode', False))
        chkClientCode = params.get('chkClientCode', False)
        self.chkCoefficient.setChecked(params.get('chkCoefficient', False))
        self.chkClientCode.setChecked(chkClientCode)
        self.edtClientCode.setText(params.get('clientCode', ''))
        self.cmbAccountingSystem.setValue(params.get('accountingSystemId', None))
        self.edtLastName.setText(params.get('lastName', ''))
        self.edtFirstName.setText(params.get('firstName', ''))
        self.edtPatrName.setText(params.get('patrName', ''))
        self.edtBirthDate.setDate(params.get('birthDate', QDate()))
        self.cmbDocType.setValue(params.get('docType', None))
        self.edtLeftSerial.setText(params.get('leftSerial', ''))
        self.edtRightSerial.setText(params.get('rightSerial', ''))
        self.edtNumber.setText(params.get('number', ''))
        self.cmbPolicyType.setValue(params.get('policyType', None))
        self.edtPolicySerial.setText(params.get('policySerial', ''))
        self.edtPolicyNumber.setText(params.get('policyNumber', ''))
        self.cmbPolicyCompany.setValue(params.get('policyCompany', None))
        self.edtContact.setText(params.get('contact', ''))
        self.cmbActionDateType.setCurrentIndex(params.get('cmbActionDateTypeIndex', 0))
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        self.cmbContract.setPath(params.get('contractPath', None))
        self.cmbFinance.setValue(params.get('financeId', None))


    def params(self):
        params = {}
        params['resultTypeIndex']             = self.cmbResultType.currentIndex()
        params['detailDateAndPersonCode']     = self.chkDetailDateAndPersonCode.isChecked()
        params['chkClientCode']               = self.chkClientCode.isChecked()
        if params['chkClientCode']:
            params['clientCode']              = forceStringEx(self.edtClientCode.text())
            params['accountingSystemId']      = self.cmbAccountingSystem.value()
        else:
            params['lastName']                = forceStringEx(self.edtLastName.text())
            params['firstName']               = forceStringEx(self.edtFirstName.text())
            params['patrName']                = forceStringEx(self.edtPatrName.text())
            params['birthDate']               = self.edtBirthDate.date()
            params['docType']                 = self.cmbDocType.value()
            params['leftSerial']              = forceStringEx(self.edtLeftSerial.text())
            params['rightSerial']             = forceStringEx(self.edtRightSerial.text())
            params['number']                  = forceStringEx(self.edtNumber.text())
            params['policyType']               = self.cmbPolicyType.value()
            params['policySerial']             = forceStringEx(self.edtPolicySerial.text())
            params['policyNumber']             = forceStringEx(self.edtPolicyNumber.text())
            params['policyCompany']            = self.cmbPolicyCompany.value()
            params['contact']                 = forceStringEx(self.edtContact.text())

        params['contractPath'] = self.cmbContract.getPath()
        params['contractIdList'] = self.cmbContract.getIdList()
        params['contractText'] = forceString(self.cmbContract.currentText())
        params['financeId']  = self.cmbFinance.value()
        params['financeText'] = self.cmbFinance.currentText()
        params['chkCoefficient'] = self.chkCoefficient.isChecked()

        params['cmbActionDateTypeIndex'] = self.cmbActionDateType.currentIndex()
        params['actionDateTypeText']     = unicode(self.cmbActionDateType.currentText())
        params['actionDateTypeValue']  = forceString(self.cmbActionDateType.itemData(
                                                       params['cmbActionDateTypeIndex']))
        params['begDate'] = self.edtBegDate.date()
        params['endDate'] = self.edtEndDate.date()
        return params


    @pyqtSignature('int')
    def on_cmbResultType_currentIndexChanged(self, index):
        if index == 0:
            title = u'Отчет работ по пациенту'
        elif index == 1:
            title = u'Акт выполненных работ'

        self.setTitle(title)
        self._report.setTitle(title)


class CReportClientSubsidiarySetupDialog(QtGui.QDialog, Ui_ReportClientSubsidiarySetupDialog):
    def __init__(self, parent, report):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self._report = report
        self.paramsSubsidiary = {}


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        self.Subsidiary = params
        resultTypeIndex = self.Subsidiary.get('resultTypeIndex', 0)
        if resultTypeIndex == 0:
            title = u'Отчет работ по пациенту'
        elif resultTypeIndex == 1:
            title = u'Акт выполненных работ'
        self.setTitle(title)
        self.getFilterPayeded()
        self.getFilterMKB()


    def params(self):
        self.Subsidiary['payededOrg'] = self.cmbPayeded.value()
        self.Subsidiary['mkbDiagnosis'] = unicode(self.edtDiagnosis.text())
        return self.Subsidiary


    def getFilterPayeded(self):
        self.cmbPayeded.clear()
        actionDateTypeValue    = self.Subsidiary.get('actionDateTypeValue', 'begDate')
        begDate                = self.Subsidiary.get('begDate', None)
        endDate                = self.Subsidiary.get('endDate', None)
        contractIdList         = self.Subsidiary.get('contractIdList', None)
        financeId              = self.Subsidiary.get('financeId', None)
        if actionDateTypeValue:
            db = QtGui.qApp.db
            tableAction               = db.table('Action')
            tableActionType           = db.table('ActionType')
            tableEvent                = db.table('Event')
            tableContract             = db.table('Contract')
            tableFinance              = db.table('rbFinance')
            tableEventLocalContract   = db.table('Event_LocalContract')
            queryTable = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
            queryTable = queryTable.innerJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
            queryTable = queryTable.innerJoin(tableContract, 'Contract.`id`=IF(Action.`contract_id`, Action.`contract_id`, Event.`contract_id`)')
            queryTable = queryTable.innerJoin(tableFinance, tableFinance['id'].eq(tableContract['finance_id']))
            queryTable = queryTable.innerJoin(tableEventLocalContract, tableEventLocalContract['master_id'].eq(tableEvent['id']))
            actionCond = '''
                            EXISTS (SELECT Action.`id` FROM Action WHERE %s AND %s AND %s AND Action.`event_id`=Event.`id`)
                         ''' %(tableAction[actionDateTypeValue].ge(begDate),
                               tableAction[actionDateTypeValue].lt(endDate.addDays(1)),
                               tableAction['deleted'].eq(0))
            cond = [actionCond, tableEvent['deleted'].eq(0)]
            cond.append(tableEventLocalContract['org_id'].isNotNull())
            cond.append(tableEventLocalContract['deleted'].eq(0))
            cond.append(tableContract['id'].inlist(contractIdList))
            cond.append(tableContract['finance_id'].eq(financeId))
            orgIdList = db.getDistinctIdList(queryTable, [tableEventLocalContract['org_id']], cond)
            if orgIdList:
                filterCond = u'Organisation.id IN (%s)'%(','.join(str(orgId) for orgId in orgIdList if orgId))
                self.cmbPayeded.setFilter(filterCond)


    def getFilterMKB(self):
        self.edtDiagnosis.clear()
        actionDateTypeValue    = self.Subsidiary.get('actionDateTypeValue', 'begDate')
        begDate                = self.Subsidiary.get('begDate', None)
        endDate                = self.Subsidiary.get('endDate', None)
        contractIdList         = self.Subsidiary.get('contractIdList', None)
        financeId              = self.Subsidiary.get('financeId', None)
        if actionDateTypeValue:
            db = QtGui.qApp.db
            tableAction               = db.table('Action')
            tableActionType           = db.table('ActionType')
            tableEvent                = db.table('Event')
            tableContract             = db.table('Contract')
            tableFinance              = db.table('rbFinance')
            tableDiagnosis            = db.table('Diagnosis')
            tableDiagnostic           = db.table('Diagnostic')
            tableRBDiagnosisType      = db.table('rbDiagnosisType')
            queryTable = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
            queryTable = queryTable.innerJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
            queryTable = queryTable.innerJoin(tableDiagnostic, tableEvent['id'].eq(tableDiagnostic['event_id']))
            queryTable = queryTable.innerJoin(tableDiagnosis, tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']))
            queryTable = queryTable.innerJoin(tableRBDiagnosisType, tableDiagnostic['diagnosisType_id'].eq(tableRBDiagnosisType['id']))
            actionCond = '''EXISTS (SELECT Action.`id` FROM Action WHERE %s AND %s AND %s AND Action.`event_id`=Event.`id`)
                         ''' %(tableAction[actionDateTypeValue].ge(begDate),
                               tableAction[actionDateTypeValue].lt(endDate.addDays(1)),
                               tableAction['deleted'].eq(0))
            cond = [actionCond, tableEvent['deleted'].eq(0)]
            if contractIdList or financeId:
                queryTable = queryTable.innerJoin(tableContract, 'Contract.`id`=IF(Action.`contract_id`, Action.`contract_id`, Event.`contract_id`)')
                if financeId:
                    queryTable = queryTable.innerJoin(tableFinance, tableFinance['id'].eq(tableContract['finance_id']))
            if contractIdList:
                cond.append(tableContract['id'].inlist(contractIdList))
            if financeId:
                cond.append(tableContract['finance_id'].eq(financeId))
            cond.append('''Diagnostic.event_id = Event.id AND Diagnosis.deleted = 0 AND Diagnostic.deleted = 0
        AND (rbDiagnosisType.code = '1' OR (rbDiagnosisType.code = '2' AND Diagnostic.person_id = Event.execPerson_id
        AND (NOT EXISTS (SELECT DC.id FROM Diagnostic AS DC INNER JOIN rbDiagnosisType AS DT ON DT.id = DC.diagnosisType_id WHERE DT.code = '1' AND DC.event_id = Event.id LIMIT 1))))''')
            records = db.getRecordList(queryTable, [tableDiagnosis['MKB']], cond)
            for record in records:
                mkb = forceString(record.value('MKB'))
                if mkb and self.edtDiagnosis.findText(mkb) == -1:
                    self.edtDiagnosis.addItem(mkb)


#WFT?
class CClientCheckerDialog(QtGui.QDialog, CConstructHelperMixin):
    def __init__(self, clientIdList):
        QtGui.QDialog.__init__(self)
        self.setWindowTitle(u'Список подобранных пациентов')
        # gui
        self.addObject('tblClients', CTableView(self))
        self.addObject('buttonBox', QtGui.QDialogButtonBox(self))
        self.addObject('vLayout', QtGui.QVBoxLayout())
        self.vLayout.addWidget(self.tblClients)
        self.vLayout.addWidget(self.buttonBox)
        self.setLayout(self.vLayout)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Ok)

        self.addModels('Clients', CClientsTableModel(self))
        self.setModels(self.tblClients, self.modelClients)
        self.modelClients.setIdList(clientIdList)

        self.connect(self.buttonBox, SIGNAL('accepted()'), self.accept)
        self.connect(self.tblClients, SIGNAL('doubleClicked(QModelIndex)'), self.on_tblClients_doubleClicked)

        self._selectedClientId = None


    def on_tblClients_doubleClicked(self, index):
        self.accept(self.tblClients.currentItemId())


    def accept(self, selectedClientId=None):
        if not selectedClientId:
            selectedClientId = self.tblClients.currentItemId()
            if not selectedClientId:
                if len(self.modelClients.idList()) > 0:
                    selectedClientId = self.modelClients.idList()[0]
        self._selectedClientId = selectedClientId
        QtGui.QDialog.accept(self)


    def selectedClientId(self):
        return self._selectedClientId
