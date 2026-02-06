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

from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignature, QDate, QDateTime

from library.Utils      import forceDate, forceInt, forceRef, forceString, formatName
from library.DialogBase import CDialogBase

from KLADR.Utils        import getLikeMaskForRegion
from Orgs.Utils         import getOrgStructureFullName

from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable

from Ui_StationaryAnalyticsSetup import Ui_StationaryAnalyticsSetupDialog


# форма 222,216

def selectData(params):
    begDate                 = params.get('begDate', None)
    endDate                 = params.get('endDate', None)
    medicalHistoryTypeIndex = params.get('medicalHistoryTypeIndex', 0)
    ambCardType             = params.get('ambCardType', None)
    diagType                = params.get('diagType', 0)
    financeId               = params.get('financeId', None)
    chkQuotaClass           = params.get('chkQuotaClass', False)
    quotaClass              = params.get('quotaClass', 0)
    quotaTypeId             = params.get('quotaTypeId', None)
    chkAdditionalOptions    = params.get('chkAdditionalOptions', False)
    filterSex               = params.get('filterSex', 0)
    filterToAge             = params.get('filterToAge', 0)
    filterFromAge           = params.get('filterFromAge', 150)
    eventTypePurposeId      = params.get('eventTypePurposeId', None)
    eventTypeId             = params.get('eventTypeId', None)

    db = QtGui.qApp.db
    tableClient                     = db.table('Client')
    tableEvent                      = db.table('Event')
    tableEventType                  = db.table('EventType')
    tableMedicalAidType             = db.table('rbMedicalAidType')
    tableContract                   = db.table('Contract')
    tableClientIdentification       = db.table('ClientIdentification')
    tableClientQuoting              = db.table('Client_Quoting')
    tableQuotaType                  = db.table('QuotaType')
    tableDiagnostic                 = db.table('Diagnostic')
    tableDiagnosis                  = db.table('Diagnosis')
    tableFinance                    = db.table('rbFinance')
    tableOrgStructure               = db.table('OrgStructure')
    tableActionType                 = db.table('ActionType')
    tableActionMoving               = db.table('Action').alias('ActionMoving')
    tableActionLeaved               = db.table('Action').alias('ActionLeaved')
    tableActionProperty             = db.table('ActionProperty')
    tableActionPropertyType         = db.table('ActionPropertyType')
    tableActionPropertyOrgStructure = db.table('ActionProperty_OrgStructure')
    tableClientAddress              = db.table('ClientAddress')
    tableAddress                    = db.table('Address')
    tableAddressHouse               = db.table('AddressHouse')

    tableActionReceivedForQuota          = db.table('Action').alias('ActionReceived')
    tableActionTypeReceivedForQuota      = db.table('ActionType').alias('ActionTypeReceived')
    tableActionPropertyForQuota          = db.table('ActionProperty').alias('ActionPropertyForQuota')
    tableActionPropertyTypeForQuota      = db.table('ActionPropertyType').alias('ActionPropertyTypeForQuota')
    tableActionPropertyClientQuoting = db.table('ActionProperty_Client_Quoting').alias('ActionPropertyClientQuoting')

    queryTable = tableClient.innerJoin(tableEvent, tableEvent['client_id'].eq(tableClient['id']))
    queryTable = queryTable.innerJoin( tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
    queryTable = queryTable.leftJoin(  tableMedicalAidType, tableMedicalAidType['id'].eq(tableEventType['medicalAidType_id']))
#    queryTable = queryTable.innerJoin( tableContract, tableContract['id'].eq(tableEvent['contract_id']))
#    queryTable = queryTable.innerJoin( tableFinance, tableFinance['id'].eq(tableContract['finance_id']))
    queryTable = queryTable.innerJoin( tableDiagnostic, tableDiagnostic['event_id'].eq(tableEvent['id']))

    if diagType == 0:
        diagTypeCode = '7'
        diagnosisJoinCond = [tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']),
                         tableDiagnostic['diagnosisType_id'].eq(forceRef(db.translate('rbDiagnosisType', 'code',
                                                                                     diagTypeCode, 'id')))]
        queryTable = queryTable.leftJoin(tableDiagnosis, db.joinAnd(diagnosisJoinCond))
    elif diagType == 1:
        diagTypeCode = '1'
        diagnosisJoinCond = [tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']),
                         tableDiagnostic['diagnosisType_id'].eq(forceRef(db.translate('rbDiagnosisType', 'code',
                                                                                     diagTypeCode, 'id')))]
        queryTable = queryTable.innerJoin(tableDiagnosis, db.joinAnd(diagnosisJoinCond))
    else:
        return None

    if ambCardType:
        clientIdenticationJoinCond = [tableClientIdentification['client_id'].eq(tableClient['id']),
                                      tableClientIdentification['accountingSystem_id'].eq(ambCardType)]
        queryTable = queryTable.leftJoin(tableClientIdentification, db.joinAnd(clientIdenticationJoinCond))

    if diagType == 0:
        tableAction = tableActionMoving
        orgStructurePropertyTypeName = u'Отделение пребывания'
        actionTypeIdList = db.getIdList('ActionType', 'id', 'flatCode LIKE \'moving%\' AND deleted=0')
        actionJoinDateCond = [tableAction['begDate'].lt(endDate.addDays(1)),
                              tableAction['begDate'].ge(begDate),
                              tableAction['deleted'].eq(0),
                              db.joinOr(
                                        [tableAction['endDate'].ge(endDate),
                                         tableAction['endDate'].isNull()
                                        ]
                                       )
                             ]
    elif diagType == 1:
        tableAction = tableActionLeaved
        orgStructurePropertyTypeName = u'Отделение'
        actionTypeIdList = db.getIdList('ActionType', 'id', 'flatCode LIKE \'leaved%\' AND deleted=0')
        actionJoinDateCond = [tableAction['begDate'].lt(endDate.addDays(1)),
                              tableAction['begDate'].ge(begDate),
                              tableAction['endDate'].lt(endDate.addDays(1)),
                              tableAction['endDate'].isNotNull(),
                              tableAction['deleted'].eq(0)
                             ]
    else:
        return None

    actionJoinCond = [tableAction['event_id'].eq(tableEvent['id']),
                      tableAction['actionType_id'].inlist(actionTypeIdList),
                     ]
    queryTable = queryTable.innerJoin(tableAction, db.joinAnd(actionJoinCond))
    queryTable = queryTable.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))

    actionPropertyTypeJoinCond = [tableActionPropertyType['actionType_id'].eq(tableActionType['id']),
                                  tableActionPropertyType['name'].eq(orgStructurePropertyTypeName)]
    queryTable = queryTable.leftJoin(tableActionPropertyType, db.joinAnd(actionPropertyTypeJoinCond))

    actionPropertyJoinCond = [tableActionProperty['action_id'].eq(tableAction['id']),
                              tableActionProperty['type_id'].eq(tableActionPropertyType['id'])]
    queryTable = queryTable.leftJoin(tableActionProperty, db.joinAnd(actionPropertyJoinCond))


    queryTable = queryTable.leftJoin(tableActionPropertyOrgStructure,
                                      tableActionPropertyOrgStructure['id'].eq(tableActionProperty['id']))

    queryTable = queryTable.leftJoin(tableOrgStructure, tableOrgStructure['id'].eq(tableActionPropertyOrgStructure['value']))

    if diagType == 0:
    # квота при поступлении
        actionTypeReceivedIdList = db.getIdList('ActionType', 'id', 'flatCode LIKE \'received%\' AND deleted=0')
        actionReceivedJoinCond = [tableActionReceivedForQuota['event_id'].eq(tableEvent['id']),
                                  tableActionReceivedForQuota['actionType_id'].inlist(actionTypeReceivedIdList),
                                 ]
        queryTable = queryTable.innerJoin(tableActionReceivedForQuota, db.joinAnd(actionReceivedJoinCond))
        queryTable = queryTable.innerJoin(tableActionTypeReceivedForQuota,
                                          tableActionTypeReceivedForQuota['id'].eq(tableActionReceivedForQuota['actionType_id']))
        tableActionForQuota = tableActionReceivedForQuota
        tableActionTypeForQuota = tableActionTypeReceivedForQuota

    # Квота при выписке
    elif diagType == 1:
        tableActionForQuota = tableAction
        tableActionTypeForQuota = tableActionType
    else:
        return None

    actionPropertyTypeForQuotaJoinCond = [tableActionPropertyTypeForQuota['actionType_id'].eq(tableActionTypeForQuota['id']),
                                          tableActionPropertyTypeForQuota['name'].eq(u'Квота')]
    queryTable = queryTable.leftJoin(tableActionPropertyTypeForQuota, db.joinAnd(actionPropertyTypeForQuotaJoinCond))

    actionPropertyForQuotaJoinCond = [tableActionPropertyForQuota['action_id'].eq(tableActionForQuota['id']),
                                      tableActionPropertyForQuota['type_id'].eq(tableActionPropertyTypeForQuota['id'])]
    queryTable = queryTable.leftJoin(tableActionPropertyForQuota, db.joinAnd(actionPropertyForQuotaJoinCond))

    queryTable = queryTable.leftJoin(tableActionPropertyClientQuoting,
                                     tableActionPropertyClientQuoting['id'].eq(tableActionPropertyForQuota['id']))

    queryTable = queryTable.leftJoin(tableClientQuoting,
                                     tableClientQuoting['id'].eq(tableActionPropertyClientQuoting['value']))

    queryTable = queryTable.leftJoin(tableQuotaType,
                                     tableQuotaType['id'].eq(tableClientQuoting['quotaType_id']))

    order = [tableClient['lastName'].name(),
             tableClient['firstName'].name(),
             tableClient['patrName'].name()]

    fields = order + ['getClientLocAddress(Client.`id`) AS clientAddress',
                      tableClient['id'].alias('clientId'),
                      tableEvent['id'].alias('eventId'),
                      tableEvent['externalId'],
                      tableDiagnosis['MKB'].name(),
                      #tableFinance['name'].alias('financeType'),
                      tableOrgStructure['name'].alias('orgStructureName'),
                      tableOrgStructure['id'].alias('orgStructureId'),
                      tableAddressHouse['KLADRCode'].name(),
                      tableEvent['setDate'].alias('eventSetDate'),
                      tableEvent['execDate'].alias('eventExecDate'),
                      tableMedicalAidType['code'].alias('medicalAidTypeCode'),
                      tableQuotaType['code'].alias('quotaTypeCode')]
    if chkAdditionalOptions:
        fields.append(tableClient['sex'].alias('clientSex'))
        fields.append(tableClient['birthDate'].alias('birthDate'))
        fields.append('age(Client.birthDate, IF(Event.execDate IS NOT NULL, DATE(Event.execDate), DATE(%s))) AS clientAge'%(db.formatDate(QDate.currentDate())))
    if ambCardType:
        fields.append(tableClientIdentification['identifier'].alias('ambCard'))
    else:
        fields.append(tableClient['id'].alias('ambCard'))

    # взависимости от типа диагноза tableActionForQuota будет либо действием "поступление"
    # либо дейтсвием "выписка"
    fields.append(tableActionForQuota['endDate'].alias('needDateForReport'))

    if medicalHistoryTypeIndex == 0:
        fields.append(tableEvent['id'].alias('codeCard'))
    else:
        fields.append(tableEvent['externalId'].alias('codeCard'))

    cond = list(actionJoinDateCond)
    cond.append(tableAction['deleted'].eq(0))
    cond.append(tableEvent['deleted'].eq(0))
    if eventTypePurposeId:
        cond.append(tableEventType['purpose_id'].eq(eventTypePurposeId))

    if eventTypeId:
        cond.append(tableEvent['eventType_id'].eq(eventTypeId))
    if chkAdditionalOptions:
        if filterSex:
            cond.append(tableClient['sex'].eq(filterSex))
        if filterToAge <= filterFromAge:
            cond.append('''age(Client.birthDate, IF(Event.execDate IS NOT NULL, DATE(Event.execDate), DATE(%s))) >= %d
                           AND age(Client.birthDate, IF(Event.execDate IS NOT NULL, DATE(Event.execDate), DATE(%s))) < %d''' % (db.formatDate(QDate.currentDate()), filterToAge, db.formatDate(QDate.currentDate()), filterFromAge+1))
    address = params.get('address', None)
    if address:
        addrType, KLADRCode, Okato, KLADRStreetCode, KLADRStreetCodeList, house, corpus, flat, isNoRegion = address
        tableClientAddress = db.table('ClientAddress')
        tableAddressHouse = db.table('AddressHouse')
        tableAddress = db.table('Address')
        queryTable = queryTable.leftJoin(tableClientAddress, tableClientAddress['client_id'].eq(tableClient['id']))
        queryTable = queryTable.leftJoin(tableAddress, tableAddress['id'].eq(tableClientAddress['address_id']))
        queryTable = queryTable.leftJoin(tableAddressHouse, tableAddressHouse['id'].eq(tableAddress['house_id']))
        cond.append('ClientAddress.id = (SELECT MAX(CA.id) FROM ClientAddress AS CA WHERE CA.deleted=0 AND CA.type=%d AND CA.client_id=Client.id)' % addrType)
        if isNoRegion:
            if KLADRStreetCode:
                cond.append(tableAddressHouse['KLADRStreetCode'].ne(KLADRStreetCode))
            elif Okato:
                cond.append(tableAddressHouse['KLADRStreetCode'].notInlist(KLADRStreetCodeList))
            elif KLADRCode:
                mask = getLikeMaskForRegion(KLADRCode)
                if mask == KLADRCode:
                    cond.append(tableAddressHouse['KLADRCode'].ne(KLADRCode))
                else:
                    cond.append(tableAddressHouse['KLADRCode'].notlike(mask))
        else:
            if KLADRStreetCode:
                cond.append(tableAddressHouse['KLADRStreetCode'].eq(KLADRStreetCode))
            elif Okato:
                cond.append(tableAddressHouse['KLADRStreetCode'].inlist(KLADRStreetCodeList))
            elif KLADRCode:
                mask = getLikeMaskForRegion(KLADRCode)
                if mask == KLADRCode:
                    cond.append(tableAddressHouse['KLADRCode'].eq(KLADRCode))
                else:
                    cond.append(tableAddressHouse['KLADRCode'].like(mask))
            if house:
                cond.append( tableAddressHouse['number'].eq(house) )
                cond.append( tableAddressHouse['corpus'].eq(corpus) )
            if flat:
                cond.append( tableAddress['flat'].eq(flat) )

    else:
        queryTable = queryTable.leftJoin(tableClientAddress, tableClientAddress['id'].name()+'=getClientLocAddressId(Client.`id`)')
        queryTable = queryTable.leftJoin(tableAddress, tableAddress['id'].eq(tableClientAddress['address_id']))
        queryTable = queryTable.leftJoin(tableAddressHouse, tableAddressHouse['id'].eq(tableAddress['house_id']))

    if diagType == 0:
        if QtGui.qApp.defaultHospitalBedFinanceByMoving() == 2:
            tableAction = tableActionMoving
            tableRBFinanceBC = db.table('rbFinance').alias('rbFinanceByContract')
            fields.append(u'IF(ActionMoving.finance_id IS NOT NULL AND ActionMoving.deleted=0, rbFinance.name, IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinanceByContract.name, NULL)) AS nameFinance')
            if financeId:
                cond.append('''((ActionMoving.finance_id IS NOT NULL AND ActionMoving.deleted=0 AND ActionMoving.finance_id = %s) OR (Contract.id IS NOT NULL AND Contract.deleted=0 AND Contract.finance_id = %s))'''%(str(financeId), str(financeId)))
                queryTable = queryTable.innerJoin(tableFinance, tableFinance['id'].eq(tableAction['finance_id']))
                queryTable = queryTable.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                queryTable = queryTable.innerJoin(tableRBFinanceBC, tableRBFinanceBC['id'].eq(tableContract['finance_id']))
            else:
                queryTable = queryTable.leftJoin(tableFinance, tableFinance['id'].eq(tableAction['finance_id']))
                queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                queryTable = queryTable.leftJoin(tableRBFinanceBC, tableRBFinanceBC['id'].eq(tableContract['finance_id']))
        elif QtGui.qApp.defaultHospitalBedFinanceByMoving() == 1:
            tableAction = tableActionMoving
            fields.append(tableFinance['name'].alias('financeType'))
            if financeId:
                cond.append('''(ActionMoving.finance_id IS NOT NULL AND ActionMoving.deleted=0 AND ActionMoving.finance_id = %s)'''%(str(financeId)))
                queryTable = queryTable.innerJoin(tableFinance, tableFinance['id'].eq(tableAction['finance_id']))
            else:
                queryTable = queryTable.leftJoin(tableFinance, tableFinance['id'].eq(tableAction['finance_id']))
        else:
            fields.append(tableFinance['name'].alias('financeType'))
            if financeId:
                queryTable = queryTable.innerJoin( tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                queryTable = queryTable.innerJoin( tableFinance, tableFinance['id'].eq(tableContract['finance_id']))
                cond.append(tableContract['deleted'].eq(0))
                cond.append(tableContract['finance_id'].eq(financeId))
            else:
                queryTable = queryTable.leftJoin( tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                queryTable = queryTable.leftJoin( tableFinance, tableFinance['id'].eq(tableContract['finance_id']))
    elif diagType == 1 and (QtGui.qApp.defaultHospitalBedFinanceByMoving() in (0, 2)):
        fields.append(tableFinance['name'].alias('financeType'))
        if financeId:
            queryTable = queryTable.innerJoin( tableContract, tableContract['id'].eq(tableEvent['contract_id']))
            queryTable = queryTable.innerJoin( tableFinance, tableFinance['id'].eq(tableContract['finance_id']))
            cond.append(tableContract['deleted'].eq(0))
            cond.append(tableContract['finance_id'].eq(financeId))
        else:
            queryTable = queryTable.leftJoin( tableContract, tableContract['id'].eq(tableEvent['contract_id']))
            queryTable = queryTable.leftJoin( tableFinance, tableFinance['id'].eq(tableContract['finance_id']))
    else:
        return None

    if chkQuotaClass and (quotaClass is not None):
        cond.append(tableQuotaType['class'].eq(quotaClass))
    if quotaTypeId:
        quotaTypeIdList = getChildrenIdList([quotaTypeId])
        cond.append(tableQuotaType['id'].inlist(quotaTypeIdList))

    stmt = db.selectStmt(queryTable, fields, cond, order)
    return db.query(stmt)


def getChildrenIdList(idList):
    db = QtGui.qApp.db
    table = db.table('QuotaType')
    result = idList
    while bool(idList):
        tmpResult = []
        for id in idList:
            code = forceString(db.translate(table, 'id', id, 'code'))
            cond = [table['group_code'].eq(code)]
            tmpResult.extend(db.getIdList(table, 'id', cond))
        result.extend(tmpResult)
        idList = tmpResult
    return result


class CAnalyticsReportHospitalizedClients(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Отчет по пациентам')
        self.resetHelpers()
        self.setOrientation(QtGui.QPrinter.Landscape)


    def resetHelpers(self):
        self._existEventClients = []
        self._mapOrgStructureToClientValues = {}
        self._orgStructureIdToFullName = {}
        self._mapClientIdToQuotingIdList = {}
        self._mapQuotingIdToQuotaTypeCode = {}


    def getSetupDialog(self, parent):
        result = CStationaryAnalyticsSetupDialog(parent)
        result.setHospitalizedWidgetsVisible(True)
        result.setQuotingWidgetsVisible(True)
        result.setDetailEventTypePurposeVisible(True)
        result.setDetailEventTypeVisible(True)
        result.setTitle(self.title())
        return result


    def dumpParamsAdditionalOptions(self, cursor, params):
        description = []
        description.append(u'Пол ' + [u'не определен', u'мужской', u'женский'][params.get('filterSex', 0)])
        description.append(u'Возраст с %s по %s'%(forceString(params.get('filterToAge', 0)), forceString(params.get('filterFromAge', 0))))
        columns = [ ('100%', [], CReportBase.AlignLeft) ]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)


    def build(self, params):
        self.resetHelpers()
        chkAdditionalOptions = params.get('chkAdditionalOptions', False)
        query = selectData(params)
        if query is not None:
            self.makeStruct(query, chkAdditionalOptions)
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        if chkAdditionalOptions:
            self.dumpParamsAdditionalOptions(cursor, params)
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        tableColumns = [('%3',  [u'№'],                            CReportBase.AlignRight),
                        ('%8',  [u'Карта амбулаторного больного'], CReportBase.AlignLeft),
                        ('%20', [u'Пациент'],                      CReportBase.AlignLeft),
                        ]
        if chkAdditionalOptions:
            tableColumns.append(('%2',  [u'Пол'],                   CReportBase.AlignLeft))
            tableColumns.append(('%4',  [u'Дата рождения'],         CReportBase.AlignLeft))
            tableColumns.append(('%2',  [u'Возраст'],               CReportBase.AlignLeft))
        tableColumns.append(('%8',      [u'Код карточки'],           CReportBase.AlignLeft))
        tableColumns.append(('%8',      [u'Номер документа'], CReportBase.AlignLeft))
        tableColumns.append(('%25'  if not chkAdditionalOptions else '%15', [u'Регион'],CReportBase.AlignLeft))
        tableColumns.append(('%7',  [u'DS'],                        CReportBase.AlignLeft))
        tableColumns.append(('%7',  [u'В/Т'],                       CReportBase.AlignLeft))
        tableColumns.append(('%7',  [u'Источник финансирования'],   CReportBase.AlignLeft))
        tableColumns.append(('%7',  [u'Количество койко-дней'],     CReportBase.AlignLeft))
        diagType = params.get('diagType', 0)
        if diagType == 0:
            tableColumns.append(('%8', [u'Дата госпитализации'], CReportBase.AlignLeft))
        else:
            tableColumns.append(('%8', [u'Дата выписки'], CReportBase.AlignLeft))

        table = createTable(cursor, tableColumns)

        boldChars = QtGui.QTextCharFormat()
        boldChars.setFontWeight(QtGui.QFont.Bold)

        keys = self._mapOrgStructureToClientValues.keys()
        iClient = 0
        daysCount = 0
        keys.sort(key=lambda item: item[0])
        keys.reverse()
        for key in keys:
            orgStructureId, orgStructureName = key
            valuesList = self._mapOrgStructureToClientValues[key]
            row = table.addRow()
            table.setText(row, 0, orgStructureName, charFormat=boldChars)
            table.mergeCells(row, 0, 1, 10)
            locClientCount = 0
            locDaysCount = 0
            for values in valuesList:
                locClientCount += 1
                iClient += 1
                row = table.addRow()
                table.setText(row, 0, iClient)
                for itemIdx, valuesItem in enumerate(values[1:]):
                    table.setText(row, itemIdx+1, valuesItem)
                locDaysCount += values[-2]
            row = table.addRow()
            table.setText(row, 0,
                          u'Итого по отделению: пациентов - %d, койко дней - %d'%(locClientCount, locDaysCount),
                          charFormat=boldChars)
            table.mergeCells(row, 0, 1, 10)
            daysCount += locDaysCount
        row = table.addRow()
        table.setText(row, 0,
                      u'Итого: пациентов - %d, койко дней - %d'%(iClient, daysCount),
                      charFormat=boldChars)
        table.mergeCells(row, 0, 1, 10)

        return doc

    def makeStruct(self, query, chkAdditionalOptions):
        while query.next():
            record = query.record()
            clientId         = forceRef(record.value('clientId'))
            fio              = formatName(
                                          record.value('lastName'),
                                          record.value('firstName'),
                                          record.value('patrName')
                                          )
            eventId            = forceRef(record.value('eventId'))
            numberDoc = forceRef(record.value('externalId'))
            clientAddress      = forceString(record.value('clientAddress'))
            KLADRCode          = forceString(record.value('KLADRCode'))
            mkb                = forceString(record.value('MKB'))
            financeType        = forceString(record.value('financeType'))
            orgStructureId     = forceRef(record.value('orgStructureId'))
            codeCard           = forceString(record.value('codeCard'))
            ambCard            = forceString(record.value('ambCard'))
            medicalAidTypeCode = forceString(record.value('medicalAidTypeCode'))
            eventSetDate       = forceDate(record.value('eventSetDate'))
            eventExecDate      = forceDate(record.value('eventExecDate'))
            quotaTypeCode      = forceString(record.value('quotaTypeCode'))
            needDateForReport  = forceString(record.value('needDateForReport'))
            clientSex          = [u'не определен', u'мужской', u'женский'][forceInt(record.value('clientSex'))]
            birthDate          = forceString(record.value('birthDate'))
            clientAge          = forceInt(record.value('clientAge'))

            if eventExecDate:
                topDate = min(eventExecDate, QDate.currentDate())
            else:
                topDate = QDate.currentDate()

            dCount = eventSetDate.daysTo(topDate)
            if medicalAidTypeCode in ('1', '2', '3'):
                if dCount == 0:
                    dCount = 1
            else:
                dCount += 1

            if (clientId, eventId) in self._existEventClients:
                continue
            self._existEventClients.append((clientId, eventId))
            fullOrgStructureName = self._orgStructureIdToFullName.get(orgStructureId, None)
            if not fullOrgStructureName:
                if not orgStructureId:
                    fullOrgStructureName = u'Подразделение не определено'
                else:
                    fullOrgStructureName = getOrgStructureFullName(orgStructureId)
                self._orgStructureIdToFullName[orgStructureId] = fullOrgStructureName
            key = (orgStructureId, fullOrgStructureName)
            orgStructureValueList = self._mapOrgStructureToClientValues.setdefault(key, [])
            if chkAdditionalOptions:
                orgStructureValue = [clientId, ambCard, fio, clientSex, birthDate, clientAge, codeCard, numberDoc,
                                     KLADRCode+', '+clientAddress, mkb, quotaTypeCode, financeType,
                                     dCount, needDateForReport]
            else:
                orgStructureValue = [clientId, ambCard, fio, codeCard, numberDoc,
                                     KLADRCode+', '+clientAddress, mkb, quotaTypeCode, financeType,
                                     dCount, needDateForReport]
            orgStructureValueList.append(orgStructureValue)


    def getDescription(self, params):
        begDate                 = params.get('begDate', None)
        endDate                 = params.get('endDate', None)
        diagType                = params.get('diagType', 0)
        financeId               = params.get('financeId', None)
        financeText             = params.get('financeText', None)
        chkQuotaClass           = params.get('chkQuotaClass', False)
        quotaClass              = params.get('quotaClass', None) if chkQuotaClass else None
        quotaTypeId             = params.get('quotaTypeId', False)
        eventTypePurposeId      = params.get('eventTypePurposeId', None)
        eventTypeId             = params.get('eventTypeId', None)
        rows = []
        if diagType == 0:
            rows.append(u'Предварительный диагноз')
        elif diagType == 1:
            rows.append(u'Заключительный диагноз')
        if financeId:
            rows.append(u'Тип финансирования: %s' % financeText)
        if begDate:
            rows.append(u'Начальная дата периода: %s'%forceString(begDate))
        if endDate:
            rows.append(u'Конечная дата периода: %s'%forceString(endDate))
        if eventTypePurposeId:
            rows.append(u'Назначение Типа события : %s'%forceString(QtGui.qApp.db.translate('rbEventTypePurpose', 'id',
                                                                eventTypePurposeId, 'CONCAT_WS(\' | \', code, name)')))
        if eventTypeId:
            rows.append(u'Тип События: %s'%forceString(QtGui.qApp.db.translate('EventType', 'id',
                                                                eventTypeId, 'CONCAT_WS(\' | \', code, name)')))
        if quotaClass is not None:
            rows.append(u'Класс квоты: %s'%[u'ВТМП', u'СМП'][quotaClass])
        if quotaTypeId:
            rows.append(u'Тип квоты: %s'%forceString(QtGui.qApp.db.translate('QuotaType', 'id',
                                                                            quotaTypeId, 'CONCAT_WS(\' | \', code, name)')))
        return rows


class CStationaryAnalyticsSetupDialog(CDialogBase, Ui_StationaryAnalyticsSetupDialog):
    def __init__(self, parent=None):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.cmbAmbCardType.setTable('rbAccountingSystem', addNone=False, specialValues=[(0, u'-', u'код пациента')])
        ambValue = forceRef(QtGui.qApp.db.translate('rbAccountingSystem', 'code', u'Амб', 'id'))
        self.cmbAmbCardType.setValue(ambValue)
        self.cmbFinance.setTable('rbFinance', addNone=True)
        self.cmbQuotaType.setTable('QuotaType', addNone=True)
        self.setHospitalizedWidgetsVisible(False)
        self.setContractWidgetsVisible(False)
        self.setQuotingWidgetsVisible(False)
        self.setDetailClientsVisible(False)
        self.setDetailFinanceVisible(False)
        self.setDetailHospitalBedProfileVisible(False)
        self.setDetailEventTypePurposeVisible(False)
        self.setDetailEventTypeVisible(False)
        self.cmbFilterAddressStreet.setAddNone(True)
        self.cmbFilterAddressCity.setAreaSelectable(True)
        self.cmbFilterAddressCity.setCode(QtGui.qApp.defaultKLADR())
        self.cmbEventTypePurpose.setTable('rbEventTypePurpose', addNone=True)
        self.cmbEventType.setTable('EventType', addNone=True)


    def setDetailEventTypePurposeVisible(self, value):
        self._detailEventTypePurposeVisible = value
        self.lblEventTypePurpose.setVisible(value)
        self.cmbEventTypePurpose.setVisible(value)


    def setDetailEventTypeVisible(self, value):
        self._detailEventTypeVisible = value
        self.lblEventType.setVisible(value)
        self.cmbEventType.setVisible(value)


    def setDetailClientsVisible(self, value):
        self._detailClientsVisible = value
        self.cmbEventType.setVisible(value)


    def setDetailFinanceVisible(self, value):
        self._detailFinanceVisible = value
        self.chkDetailFinance.setVisible(value)


    def setDetailHospitalBedProfileVisible(self, value):
        self._detailHospitalBedProfileVisible = value
        self.chkDetailHospitalBedProfile.setVisible(value)


    def setQuotingWidgetsVisible(self, value):
        self._quotingWidgetsVisible = value

        self.chkQuotaClass.setVisible(value)
        self.cmbQuotaClass.setVisible(value)

        self.lblQuotaType.setVisible(value)
        self.cmbQuotaType.setVisible(value)


    def setContractWidgetsVisible(self, value):
        self._contractWidgetsVisible = value

        self.lblContract.setVisible(value)
        self.cmbContract.setVisible(value)


    def setHospitalizedWidgetsVisible(self, value):
        self._hospitalizedWidgetsVisible = value

        self.lblAmbCardType.setVisible(value)
        self.cmbAmbCardType.setVisible(value)

        self.lblMedicalHistory.setVisible(value)
        self.cmbMedicalHistoryType.setVisible(value)

        self.lblDiagType.setVisible(value)
        self.cmbDiagType.setVisible(value)


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        self.cmbFinance.setValue(params.get('financeId', None))
        self.chkFilterAdditionalOptions.setChecked(params.get('chkAdditionalOptions', False))
        self.cmbFilterSex.setCurrentIndex(params.get('filterSex', 0))
        self.edtFilterToAge.setValue(params.get('filterToAge', 0))
        self.edtFilterFromAge.setValue(params.get('filterFromAge', 150))
        self.cmbFilterSex.setEnabled(self.chkFilterAdditionalOptions.isChecked())
        self.edtFilterToAge.setEnabled(self.chkFilterAdditionalOptions.isChecked())
        self.edtFilterFromAge.setEnabled(self.chkFilterAdditionalOptions.isChecked())
        if self._contractWidgetsVisible:
            self.cmbContract.setValue(params.get('contractId', None))
        if self._hospitalizedWidgetsVisible:
            self.cmbAmbCardType.setValue(params.get('ambCardType', None))
            self.cmbMedicalHistoryType.setCurrentIndex(params.get('medicalHistoryTypeIndex', 0))
            self.cmbDiagType.setCurrentIndex(params.get('diagType', 0))
        if self._quotingWidgetsVisible:
            chkQuotaClass = params.get('chkQuotaClass', False)
            self.chkQuotaClass.setChecked(chkQuotaClass)
            self.cmbQuotaClass.setCurrentIndex(params.get('quotaClass', 0))
            self.cmbQuotaType.setValue(params.get('quotaTypeId', None))
        if self._detailClientsVisible:
            self.chkDetailClients.setChecked(params.get('chkDetailClients', False))
        if self._detailFinanceVisible:
            self.chkDetailFinance.setChecked(params.get('chkDetailFinance', False))
        if self._detailHospitalBedProfileVisible:
            self.chkDetailHospitalBedProfile.setChecked(params.get('chkDetailHospitalBedProfile', False))
        self.chkFilterAddress.setChecked(params.get('isFilterAddress', False))
        if self.chkFilterAddress.isChecked():
            address = params.get('address', None)
            if address:
                addrType, KLADRCode, Okato, KLADRStreetCode, KLADRStreetCodeList, house, corpus, flat, isNoRegion = address
                self.cmbFilterAddressType.setCurrentIndex(addrType)
                self.cmbFilterAddressCity.setCode(KLADRCode)
                self.cmbFilterAddressOkato.setValue(Okato)
                self.cmbFilterAddressStreet.setCode(KLADRStreetCode)
                self.edtFilterAddressHouse.setText(house)
                self.edtFilterAddressCorpus.setText(corpus)
                self.edtFilterAddressFlat.setText(flat)
                self.chkFilterNoRegion.setChecked(isNoRegion)
        if self._detailEventTypePurposeVisible:
            self.cmbEventTypePurpose.setValue(params.get('eventTypePurposeId', None))
        if self._detailEventTypeVisible:
            self.cmbEventType.setValue(params.get('eventTypeId', None))


    def params(self):
        params = {}
        params['begDate']     = QDateTime(self.edtBegDate.date(), self.edtBegTime.time())
        params['endDate']     = QDateTime(self.edtEndDate.date(), self.edtEndTime.time())
        params['financeId']   = self.cmbFinance.value()
        params['financeText'] = self.cmbFinance.currentText()
        params['chkAdditionalOptions'] = self.chkFilterAdditionalOptions.isChecked()
        params['filterSex'] = self.cmbFilterSex.currentIndex()
        params['filterToAge'] = self.edtFilterToAge.value()
        params['filterFromAge'] = self.edtFilterFromAge.value()
        if self._contractWidgetsVisible:
            params['contractId'] = self.cmbContract.value()
            params['contractText'] = self.cmbContract.currentText()
        if self._hospitalizedWidgetsVisible:
            params['ambCardType'] = self.cmbAmbCardType.value()
            params['medicalHistoryTypeIndex'] = self.cmbMedicalHistoryType.currentIndex()
            params['medicalHistoryTypeText'] = self.cmbMedicalHistoryType.currentText()
            params['diagType'] = self.cmbDiagType.currentIndex()
        if self._quotingWidgetsVisible:
            params['chkQuotaClass'] = self.chkQuotaClass.isChecked()
            params['quotaClass']    = self.cmbQuotaClass.currentIndex()
            params['quotaTypeId']   = self.cmbQuotaType.value()
        if self._detailClientsVisible:
            params['chkDetailClients'] = self.chkDetailClients.isChecked()
        if self._detailFinanceVisible:
            params['chkDetailFinance'] = self.chkDetailFinance.isChecked()
        if self._detailHospitalBedProfileVisible:
            params['chkDetailHospitalBedProfile'] = self.chkDetailHospitalBedProfile.isChecked()
        if self.chkFilterAddress.isChecked():
            params['isFilterAddress'] = self.chkFilterAddress.isChecked()
            params['address'] = (self.cmbFilterAddressType.currentIndex(),
                                 self.cmbFilterAddressCity.code(),
                                 self.cmbFilterAddressOkato.value(),
                                 self.cmbFilterAddressStreet.code(),
                                 self.cmbFilterAddressStreet.codeList(),
                                 self.edtFilterAddressHouse.text(),
                                 self.edtFilterAddressCorpus.text(),
                                 self.edtFilterAddressFlat.text(),
                                 self.chkFilterNoRegion.isChecked()
                                )
        if self._detailEventTypePurposeVisible:
            params['eventTypePurposeId'] = self.cmbEventTypePurpose.value()
        if self._detailEventTypeVisible:
            params['eventTypeId'] = self.cmbEventType.value()
        return params


    @pyqtSignature('bool')
    def on_chkFilterAddress_toggled(self, checked):
        self.cmbFilterAddressType.setEnabled(checked)
        self.cmbFilterAddressCity.setEnabled(checked)
        self.cmbFilterAddressOkato.setEnabled(checked)
        self.cmbFilterAddressStreet.setEnabled(checked)
        self.cmbFilterAddressStreet.setEnabled(checked)
        self.lblFilterAddressHouse.setEnabled(checked)
        self.edtFilterAddressHouse.setEnabled(checked)
        self.lblFilterAddressCorpus.setEnabled(checked)
        self.edtFilterAddressCorpus.setEnabled(checked)
        self.lblFilterAddressFlat.setEnabled(checked)
        self.edtFilterAddressFlat.setEnabled(checked)
        self.chkFilterNoRegion.setEnabled(checked)


    @pyqtSignature('int')
    def on_cmbEventTypePurpose_currentIndexChanged(self, index):
        eventPurposeId = self.cmbEventTypePurpose.value()
        if eventPurposeId:
            filter = 'EventType.purpose_id =%d' % eventPurposeId
        else:
            filter = u''
        self.cmbEventType.setFilter(filter)


    @pyqtSignature('int')
    def on_cmbFilterAddressCity_currentIndexChanged(self, index):
        code = self.cmbFilterAddressCity.code()
        self.cmbFilterAddressStreet.setCity(code)
        self.cmbFilterAddressOkato.setKladrCode(code)


    @pyqtSignature('int')
    def on_cmbFilterAddressOkato_currentIndexChanged(self, index):
        okato = self.cmbFilterAddressOkato.value()
        self.cmbFilterAddressStreet.setOkato(okato)


    @pyqtSignature('bool')
    def on_chkQuotaClass_toggled(self, value):
        if value:
            index = self.cmbQuotaClass.currentIndex()
            self.cmbQuotaType.setFilter('class=%d'%index)
        else:
            self.cmbQuotaType.setFilter(None)


    @pyqtSignature('bool')
    def on_chkFilterAdditionalOptions_clicked(self, value):
        self.cmbFilterSex.setEnabled(value)
        self.edtFilterToAge.setEnabled(value)
        self.edtFilterFromAge.setEnabled(value)


    @pyqtSignature('bool')
    def on_chkDetailClients_clicked(self, value):
        if value:
            self.chkDetailClients.setEnabled(value)
            self.chkDetailHospitalBedProfile.setEnabled(not value)
            self.chkDetailFinance.setEnabled(not value)
            self.chkDetailHospitalBedProfile.setChecked(False)
            self.chkDetailFinance.setChecked(False)
        else:
            self.chkDetailHospitalBedProfile.setEnabled(not value)
            self.chkDetailFinance.setEnabled(not value)


    @pyqtSignature('bool')
    def on_chkDetailHospitalBedProfile_clicked(self, value):
        if value:
            self.chkDetailClients.setEnabled(not value)
            self.chkDetailFinance.setEnabled(value)
            self.chkDetailHospitalBedProfile.setEnabled(value)
            self.chkDetailClients.setChecked(False)
        elif self.chkDetailFinance.isChecked():
            self.chkDetailClients.setEnabled(value)
        else:
            self.chkDetailClients.setEnabled(not value)


    @pyqtSignature('bool')
    def on_chkDetailFinance_clicked(self, value):
        if value:
            self.chkDetailClients.setEnabled(not value)
            self.chkDetailFinance.setEnabled(value)
            self.chkDetailHospitalBedProfile.setEnabled(value)
            self.chkDetailClients.setChecked(False)
        elif self.chkDetailHospitalBedProfile.isChecked():
            self.chkDetailClients.setEnabled(value)
        else:
            self.chkDetailClients.setEnabled(not value)


    @pyqtSignature('int')
    def on_cmbQuotaClass_currentIndexChanged(self, index):
        if self.chkQuotaClass.isChecked():
            self.cmbQuotaType.setFilter('class=%d'%index)


    @pyqtSignature('int')
    def on_cmbFinance_currentIndexChanged(self, index):
        self.cmbContract.setFinanceId(self.cmbFinance.value())


    @pyqtSignature('QDate')
    def on_edtBegDate_dateChanged(self, date):
        self.cmbContract.setBegDate(date)


    @pyqtSignature('QDate')
    def on_edtEndDate_dateChanged(self, date):
        self.cmbContract.setEndDate(date)

