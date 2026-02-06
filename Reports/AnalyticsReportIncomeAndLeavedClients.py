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
from PyQt4.QtCore import QDate

from library.Utils      import forceDate, forceInt, forceRef, forceString, formatName

from Orgs.Utils         import getOrgStructureFullName
from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable
from Reports.AnalyticsReportHospitalizedClients import CStationaryAnalyticsSetupDialog, getChildrenIdList


def selectData(params):
    begDate         = params.get('begDate', None)
    endDate         = params.get('endDate', None)
    financeId       = params.get('financeId', None)
    contractId      = params.get('contractId', None)
    chkQuotaClass   = params.get('chkQuotaClass', False)
    quotaClass      = params.get('quotaClass', 0)
    quotaTypeId     = params.get('quotaTypeId', None)
    chkDetailClients = params.get('chkDetailClients', False)
    filterSex       = params.get('filterSex', 0)
    filterToAge     = params.get('filterToAge', 0)
    filterFromAge   = params.get('filterFromAge', 150)

    db = QtGui.qApp.db

    tableClient                     = db.table('Client')
    tableEvent                      = db.table('Event')
    tableContract                   = db.table('Contract')
    tableFinance                    = db.table('rbFinance')

    tableReceivedAction             = db.table('Action').alias('ActionReceived')
    tableMovingActionProperty       = db.table('ActionProperty').alias('ActionPropertyMoving')
    tableMovingActionPropertyType   = db.table('ActionPropertyType').alias('ActionPropertyTypeMoving')
    tableMovingActionPropertyOrgStructure   = db.table('ActionProperty_OrgStructure').alias('ActionPropertyOrgStructureMoving')
    tableMovingOrgStructure         = db.table('OrgStructure').alias('OrgStructureMoving')

    tableMovingInActionProperty = db.table('ActionProperty').alias('ActionPropertyMovingIn')
    tableMovingInActionPropertyType = db.table('ActionPropertyType').alias('ActionPropertyTypeMovingIn')
    tableMovingInActionPropertyOrgStructure = db.table('ActionProperty_OrgStructure').alias('ActionPropertyOrgStructureMovingIn')
    tableMovingInOrgStructure = db.table('OrgStructure').alias('OrgStructureMovingIn')

    tableActionMovingStaying                       = db.table('Action').alias('ActionMovingStaying')
    tableActionTypeMovingStaying                   = db.table('ActionType').alias('ActionTypeMovingStaying')
    tableMovingActionPropertyStaying               = db.table('ActionProperty').alias('ActionPropertyMovingStaying')
    tableMovingActionPropertyTypeStaying           = db.table('ActionPropertyType').alias('ActionPropertyTypeMovingStaying')
    tableMovingActionPropertyOrgStructureStaying   = db.table('ActionProperty_OrgStructure').alias(
                                                              'ActionPropertyOrgStructureMovingStaying')
    tableMovingStayingOrgStructure                 = db.table('OrgStructure').alias('OrgStructureMovingStaying')

    tableQuotaAction                  = db.table('Action').alias('ActionQuota')
    tableQuotaActionType              = db.table('ActionType').alias('ActionTypeQuota')
    tableQuotaActionProperty          = db.table('ActionProperty').alias('ActionPropertyQuota')
    tableQuotaActionPropertyType      = db.table('ActionPropertyType').alias('ActionPropertyTypeQuota')
    tableActionPropertyClientQuoting  = db.table('ActionProperty_Client_Quoting')
    tableClientQuoting                = db.table('Client_Quoting')
    tableQuotaType                    = db.table('QuotaType')

    queryTable = tableEvent.leftJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))

    # привязка к действию движение
    actionTypeMovingIdList = db.getIdList('ActionType', 'id', 'flatCode LIKE \'moving%\' AND deleted=0')

    ## Отделение пребывание
    actionMovingStayingJoinCond = [tableActionMovingStaying['event_id'].eq(tableEvent['id']),
                                   tableActionMovingStaying['actionType_id'].inlist(actionTypeMovingIdList),
                             ]
    queryTable = queryTable.leftJoin(tableActionMovingStaying, db.joinAnd(actionMovingStayingJoinCond))
    queryTable = queryTable.innerJoin(tableActionTypeMovingStaying,
                                      tableActionTypeMovingStaying['id'].eq(tableActionMovingStaying['actionType_id']))


    actionPropertyTypeMovingStayingJoinCond = [tableMovingActionPropertyTypeStaying['actionType_id'].eq(
                                               tableActionTypeMovingStaying['id']),
                                               tableMovingActionPropertyTypeStaying['name'].eq(u'Отделение пребывания')]
    queryTable = queryTable.innerJoin(tableMovingActionPropertyTypeStaying, db.joinAnd(actionPropertyTypeMovingStayingJoinCond))

    actionPropertyMovingStayingJoinCond = [tableMovingActionPropertyStaying['type_id'].eq(
                                                                    tableMovingActionPropertyTypeStaying['id']),
                                            tableMovingActionPropertyStaying['action_id'].eq(tableActionMovingStaying['id'])]
    queryTable = queryTable.leftJoin(tableMovingActionPropertyStaying,
                                     actionPropertyMovingStayingJoinCond)

    queryTable = queryTable.leftJoin(tableMovingActionPropertyOrgStructureStaying,
                                     tableMovingActionPropertyOrgStructureStaying['id'].eq(tableMovingActionPropertyStaying['id']))

    queryTable = queryTable.leftJoin(tableMovingStayingOrgStructure,
                                     tableMovingStayingOrgStructure['id'].eq(
                                     tableMovingActionPropertyOrgStructureStaying['value']))

    ## переведен в отделение
    actionPropertyTypeMovingJoinCond = [tableMovingActionPropertyType['actionType_id'].eq(
                                               tableActionTypeMovingStaying['id']),
                                               tableMovingActionPropertyType['name'].eq(u'Переведен в отделение')]
    queryTable = queryTable.innerJoin(tableMovingActionPropertyType, db.joinAnd(actionPropertyTypeMovingJoinCond))

    actionPropertyMovingJoinCond = [tableMovingActionProperty['type_id'].eq(tableMovingActionPropertyType['id']),
                                    tableMovingActionProperty['action_id'].eq(tableActionMovingStaying['id'])]
    queryTable = queryTable.leftJoin(tableMovingActionProperty,
                                     actionPropertyMovingJoinCond)

    queryTable = queryTable.leftJoin(tableMovingActionPropertyOrgStructure,
                                     tableMovingActionPropertyOrgStructure['id'].eq(tableMovingActionProperty['id']))

    queryTable = queryTable.leftJoin(tableMovingOrgStructure,
                                     tableMovingOrgStructure['id'].eq(tableMovingActionPropertyOrgStructure['value']))

    ## переведен из отделения
    actionPropertyTypeMovingInJoinCond = [
        tableMovingInActionPropertyType['actionType_id'].eq(tableActionTypeMovingStaying['id']),
        tableMovingInActionPropertyType['name'].eq(u'Переведен из отделения')]
    queryTable = queryTable.leftJoin(tableMovingInActionPropertyType, db.joinAnd(actionPropertyTypeMovingInJoinCond))

    actionPropertyMovingInJoinCond = [tableMovingInActionProperty['type_id'].eq(tableMovingInActionPropertyType['id']),
                                    tableMovingInActionProperty['action_id'].eq(tableActionMovingStaying['id'])]
    queryTable = queryTable.leftJoin(tableMovingInActionProperty, actionPropertyMovingInJoinCond)

    queryTable = queryTable.leftJoin(tableMovingInActionPropertyOrgStructure,
                                     tableMovingInActionPropertyOrgStructure['id'].eq(tableMovingInActionProperty['id']))

    queryTable = queryTable.leftJoin(tableMovingInOrgStructure,
                                     tableMovingInOrgStructure['id'].eq(tableMovingInActionPropertyOrgStructure['value']))

    ## получение начальной даты для первого действия движения из даты закрытия действия поступление
    actionTypeReceivedIdList = db.getIdList('ActionType', 'id', 'flatCode LIKE \'received%\' AND deleted=0')

    actionReceivedJoinCond = ['ActionReceived.id = getPrevActionId(Event.`id`, ActionMovingStaying.id, {typeId}, ActionMovingStaying.begDate)'.format(typeId=actionTypeReceivedIdList[-1]),
                              # tableReceivedAction['event_id'].eq(tableEvent['id']),
                              # tableReceivedAction['actionType_id'].inlist(actionTypeReceivedIdList)
                              tableReceivedAction['deleted'].eq(0),
                              tableReceivedAction['endDate'].isNotNull()
                             ]
    queryTable = queryTable.leftJoin(tableReceivedAction, actionReceivedJoinCond)
    ## Квота пациента
    queryTable = queryTable.innerJoin(tableQuotaActionType, tableQuotaActionType['id'].eq(tableActionMovingStaying['actionType_id']))
    queryTable = queryTable.leftJoin(tableQuotaAction, [tableQuotaAction['actionType_id'].eq(tableQuotaActionType['id']),
                                                        tableQuotaAction['event_id'].eq(tableEvent['id']),
                                                        tableQuotaAction['deleted'].eq(0)
                                                       ])
    actionPropertyTypeQuotaJoinCond = [tableQuotaActionPropertyType['actionType_id'].eq(tableQuotaActionType['id']),
                                       tableQuotaActionPropertyType['name'].eq(u'Квота')]
    queryTable = queryTable.innerJoin(tableQuotaActionPropertyType, db.joinAnd(actionPropertyTypeQuotaJoinCond))

    actionPropertyQuotaJoinCond = [tableQuotaActionProperty['type_id'].eq(tableQuotaActionPropertyType['id']),
                                   tableQuotaActionProperty['action_id'].eq(tableActionMovingStaying['id'])]
    queryTable = queryTable.leftJoin(tableQuotaActionProperty, actionPropertyQuotaJoinCond)
    queryTable = queryTable.leftJoin(tableActionPropertyClientQuoting, tableActionPropertyClientQuoting['id'].eq(tableQuotaActionProperty['id']))
    queryTable = queryTable.leftJoin(tableClientQuoting, tableClientQuoting['id'].eq(tableActionPropertyClientQuoting['value']))
    queryTable = queryTable.leftJoin(tableQuotaType, tableQuotaType['id'].eq(tableClientQuoting['quotaType_id']))

    recievedCond = db.joinAnd([
                               tableReceivedAction['endDate'].ge(begDate),
                               tableReceivedAction['endDate'].le(endDate),
                               tableMovingOrgStructure['id'].isNull()
                              ])

    leavedCond   = db.joinAnd([
                               tableActionMovingStaying['endDate'].le(endDate),
                               tableActionMovingStaying['endDate'].ge(begDate),
                               tableMovingOrgStructure['id'].isNull()
                              ])
    transferCond   = db.joinAnd([
                               tableActionMovingStaying['endDate'].le(endDate),
                               tableActionMovingStaying['endDate'].ge(begDate),
                               tableMovingOrgStructure['id'].isNotNull()
                              ])

    existsBottomCond = db.joinAnd([
                                   tableReceivedAction['endDate'].lt(begDate),
                                   db.joinOr([tableActionMovingStaying['endDate'].ge(begDate),
                                              tableActionMovingStaying['endDate'].isNull()]),
                                   tableMovingOrgStructure['id'].isNull()
                                  ])

    existsTopCond = db.joinAnd([
                                tableReceivedAction['endDate'].le(endDate),
                                db.joinOr([tableActionMovingStaying['endDate'].gt(endDate),
                                           tableActionMovingStaying['endDate'].isNull()]),
                                tableMovingOrgStructure['id'].isNull()
                               ])

    cond = [
            db.joinOr([existsBottomCond, recievedCond, transferCond, leavedCond, existsTopCond]),
            tableEvent['deleted'].eq(0),
            tableActionMovingStaying['deleted'].eq(0)
           ]
    if (chkQuotaClass and quotaClass is not None) or quotaTypeId:
        cond.append(tableActionMovingStaying['id'].eq(tableQuotaAction['id']))
    if contractId:
        cond.append(tableContract['id'].eq(contractId))

    if chkQuotaClass and (quotaClass is not None):
        cond.append(tableQuotaType['class'].eq(quotaClass))

    if quotaTypeId:
        quotaTypeIdList = getChildrenIdList([quotaTypeId])
        cond.append(tableQuotaType['id'].inlist(quotaTypeIdList))

    fields = [tableReceivedAction['endDate'].alias('receivedActionBegDate'),
              tableActionMovingStaying['begDate'].alias('movingActionBegDate'),
              tableActionMovingStaying['endDate'].alias('movingActionEndDate'),
              tableMovingOrgStructure['id'].alias('movingOrgStructureId'),
              tableMovingInOrgStructure['id'].alias('movingInOrgStructureId'),
              tableMovingStayingOrgStructure['id'].alias('stayingOrgStructureId'),
              tableMovingStayingOrgStructure['code'].alias('stayingOrgStructureCode'),
              tableEvent['id'].alias('eventId'), 
              u"""(SELECT 
            ActionProperty_rbHospitalBedProfile.value
        FROM
            ActionProperty_rbHospitalBedProfile
                LEFT JOIN
            ActionProperty AS APHB ON APHB.id = ActionProperty_rbHospitalBedProfile.id
                LEFT JOIN
            ActionPropertyType AS APTHB ON APHB.type_id = APTHB.id
                AND APTHB.typeName = 'HospitalBed'
        WHERE
            APHB.action_id = ActionMovingStaying.id
                AND ActionProperty_rbHospitalBedProfile.value IS NOT NULL
        LIMIT 1) as hospitalBedProfileId"""
              ]

    if chkDetailClients:
        fields.extend([tableClient['id'].alias('clientId'),
                       tableClient['lastName'].alias('clientLastName'),
                       tableClient['firstName'].alias('clientFirstName'),
                       tableClient['patrName'].alias('clientPatrName'),
                       'CONCAT_WS(\' \',grouping, number, DATE_FORMAT(date,\'%d:%m:%Y`\'), resolution) AS contractInfo',
                       tableQuotaType['class'].alias('quotaTypeClass'),
                       tableQuotaType['code'].alias('quotaTypeCode'),
                       tableClientQuoting['status'].alias('quotaStatus'),
                       tableClientQuoting['id'].alias('clientQuotingId'),
                       tableActionMovingStaying['id'].alias('actionMovingStayingId')])
    if filterSex > 0:
        cond.append(tableClient['sex'].eq(filterSex))
    if filterToAge <= filterFromAge:
        cond.append('''(Event.setDate >= ADDDATE(Client.birthDate, INTERVAL %d YEAR))
        AND (Event.setDate < ADDDATE(Client.birthDate, INTERVAL %d YEAR))''' % (filterToAge, filterFromAge+1))
    if QtGui.qApp.defaultHospitalBedFinanceByMoving() == 2:
        tableRBFinanceBC = db.table('rbFinance').alias('rbFinanceByContract')
        fields.append(u'IF(ActionMovingStaying.finance_id IS NOT NULL AND ActionMovingStaying.deleted=0, rbFinance.name, IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinanceByContract.name, NULL)) AS nameFinance')
        if financeId:
            cond.append('''((ActionMovingStaying.finance_id IS NOT NULL AND ActionMovingStaying.deleted=0 AND ActionMovingStaying.finance_id = %s) OR (Contract.id IS NOT NULL AND Contract.deleted=0 AND Contract.finance_id = %s))'''%(str(financeId), str(financeId)))
            queryTable = queryTable.innerJoin(tableFinance, tableFinance['id'].eq(tableActionMovingStaying['finance_id']))
            queryTable = queryTable.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
            queryTable = queryTable.innerJoin(tableRBFinanceBC, tableRBFinanceBC['id'].eq(tableContract['finance_id']))
        else:
            queryTable = queryTable.leftJoin(tableFinance, tableFinance['id'].eq(tableActionMovingStaying['finance_id']))
            queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
            queryTable = queryTable.leftJoin(tableRBFinanceBC, tableRBFinanceBC['id'].eq(tableContract['finance_id']))
    elif QtGui.qApp.defaultHospitalBedFinanceByMoving() == 1:
        fields.append(tableFinance['name'].alias('financeType'))
        if financeId:
            cond.append('''(ActionMovingStaying.finance_id IS NOT NULL AND ActionMovingStaying.deleted=0 AND ActionMovingStaying.finance_id = %s)'''%(str(financeId)))
            queryTable = queryTable.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
            queryTable = queryTable.innerJoin(tableFinance, tableFinance['id'].eq(tableActionMovingStaying['finance_id']))
        else:
            queryTable = queryTable.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
            queryTable = queryTable.leftJoin(tableFinance, tableFinance['id'].eq(tableActionMovingStaying['finance_id']))
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

    stmt = db.selectDistinctStmt(queryTable, fields, cond)
    return db.query(stmt)


def getOrgStructureHospitalBedProfileIdList():
    hospitalBedProfileIdByOrgStructureId = {}
    db = QtGui.qApp.db
    tableOrgStructureHospitalBed  = db.table('OrgStructure_HospitalBed')
    cond = [tableOrgStructureHospitalBed['master_id'].isNotNull()]
    recordList = db.getRecordListGroupBy(tableOrgStructureHospitalBed, '*', cond, u'master_id, profile_id')
    for record in recordList:
        orgStructureId = forceInt(record.value('master_id'))
        if orgStructureId not in hospitalBedProfileIdByOrgStructureId.keys():
            hospitalBedProfileIdByOrgStructureId[orgStructureId] = []
        hospitalBedProfileId = forceInt(record.value('profile_id'))
        hospitalBedProfileIdByOrgStructureId[orgStructureId].append(hospitalBedProfileId)
    return hospitalBedProfileIdByOrgStructureId


def getHospitalBedProfileNameList():
    mapHospitalBedIdToName = {}
    db = QtGui.qApp.db
    tableRbHospitalBedProfile  = db.table('rbHospitalBedProfile')
    recordList = db.getRecordList(tableRbHospitalBedProfile, '*')
    for record in recordList:
        hospitalBedProfileId = forceInt(record.value('id'))
        hospitalBedProfileName = forceString(record.value('name'))
        mapHospitalBedIdToName[hospitalBedProfileId] = hospitalBedProfileName
    return mapHospitalBedIdToName


class CAnalyticsReportIncomeAndLeavedClients(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Отчет по поступлению и выписке пациентов')
        self.resetHelpers()
        self.setOrientation(QtGui.QPrinter.Landscape)
        self.hospitalBedProfileIdByOrgStructureId = getOrgStructureHospitalBedProfileIdList()
        self.mapHospitalBedIdToName = getHospitalBedProfileNameList()


    def resetHelpers(self):
        self._existEvents = []
        self._orgStructureIdToFullName = {}
        self._mapOrgStructureToClientValues = {}
        self._rowsShift = 0
        self._clientInfo = {}
        self.boldChars = None


    def getSetupDialog(self, parent):
        result = CStationaryAnalyticsSetupDialog(parent)
        result.setContractWidgetsVisible(True)
        result.setQuotingWidgetsVisible(True)
        result.setDetailClientsVisible(True)
        result.setDetailFinanceVisible(True)
        result.setDetailHospitalBedProfileVisible(True)
        result.setTitle(self.title())
        return result

    def build(self, params):
        self.resetHelpers()
        query = selectData(params)
        self.makeStruct(query, params)
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        tableColumns = [('%5', [u'№'], CReportBase.AlignRight),
                        ('%25', [u'Подразделение'], CReportBase.AlignLeft),
                        ('%7', [u'Состояло'], CReportBase.AlignLeft),
                        ('%7', [u'Поступило'], CReportBase.AlignLeft),
                        ('%7', [u'Переведено в'], CReportBase.AlignLeft),
                        ('%7', [u'Переведено из'], CReportBase.AlignLeft),
                        ('%7', [u'Выписано'], CReportBase.AlignLeft),
                        ('%7', [u'Состоит'], CReportBase.AlignLeft)
                        ]

        chkDetailClients = params.get('chkDetailClients', False)
        chkDetailFinance = params.get('chkDetailFinance', False)
        financeId        = params.get('financeId', None)
        if financeId:
            chkDetailFinance = False
        chkDetailHospitalBedProfile = params.get('chkDetailHospitalBedProfile', False)
        if chkDetailClients:
            # подразделение будет выводится как заголовок
            del tableColumns[1]

            tableColumns.insert(1, ('%10', [u'Ф.И.О.'], CReportBase.AlignLeft))
            tableColumns.insert(2, ('%10', [u'Тип финансирования'], CReportBase.AlignLeft))
            tableColumns.insert(3, ('%10', [u'Контракт'], CReportBase.AlignLeft))
            tableColumns.insert(4, ('%10', [u'Класс квоты'], CReportBase.AlignLeft))
            tableColumns.insert(5, ('%10', [u'Состояние'], CReportBase.AlignLeft))
            tableColumns.insert(6, ('%10', [u'Вид квоты'], CReportBase.AlignLeft))

        table = createTable(cursor, tableColumns)
        self.boldChars = QtGui.QTextCharFormat()
        self.boldChars.setFontWeight(QtGui.QFont.Bold)

        result = [0, 0, 0, 0, 0, 0]
        financeResult = None
        keys = self._mapOrgStructureToClientValues.keys()
        keys.sort(key=lambda item: item[1])
        if (chkDetailHospitalBedProfile or chkDetailFinance) and not chkDetailClients:
            keys.sort(key=lambda item: (item[0], item[2]))
            orgStructuresList = []
            financeList = []
            for key in keys:
                orgStrKey = key[1] if chkDetailFinance else key[0]
                financeKey = key[0] if chkDetailFinance else None
                if chkDetailFinance:
                    if financeKey not in financeList:
                        if financeResult:
                            i = table.addRow()
                            table.setText(i, 1, u'Итого по типу финансирования %s'%financeList[-1], charFormat=self.boldChars)
                            table.mergeCells(i, 0, 1, 2)
                            columnShift = 2
                            for idx, value in enumerate(financeResult):
                                table.setText(i, idx+columnShift, value, charFormat=self.boldChars)
                                financeResult[idx] += value
                        financeList.append(key[0])
                        financeResult = [0, 0, 0, 0, 0, 0]
                        orgStructuresList = []
                        i = table.addRow()
                        table.setText(i, 1, key[0], charFormat=self.boldChars,  blockFormat = CReportBase.AlignCenter)
                        table.mergeCells(i, 0, 1, 8)
                if orgStrKey not in orgStructuresList:
                    orgStructuresList.append(orgStrKey)
                    subResult = self.printOrgStructureValues(key, self._mapOrgStructureToClientValues, table, financeKey=financeKey)
                    result = map(lambda x, y: x+y, subResult, result)
                    if chkDetailFinance:
                        financeResult = map(lambda x, y: x+y, subResult, financeResult)
                    if chkDetailHospitalBedProfile:
                        subResult = self.printProfileValues(key, self._mapOrgStructureToClientValues, table, financeKey=financeKey)
                else:
                    if chkDetailHospitalBedProfile:
                        subResult = self.printProfileValues(key, self._mapOrgStructureToClientValues, table, financeKey=financeKey)
            if chkDetailFinance:
                i = table.addRow()
                table.setText(i, 1, u'Итого по типу финансирования %s'%financeList[-1], charFormat=self.boldChars)
                table.mergeCells(i, 0, 1, 2)
                columnShift = 2
                for idx, value in enumerate(financeResult):
                    table.setText(i, idx+columnShift, value, charFormat=self.boldChars)
                    financeResult[idx] += value
            i = table.addRow()
            table.setText(i, 1, u'Итого', charFormat=self.boldChars)
            self.printResult(i, result, table, chkDetailClients)
        else:
            for key in keys:
                subResult = self.printValues(key, self._mapOrgStructureToClientValues, table)
                result = map(lambda x, y: x+y, subResult, result)
            i = table.addRow()
            table.setText(i, 1, u'Итого', charFormat=self.boldChars)
            self.printResult(i, result, table, chkDetailClients)
        return doc


    def printValues(self, key, valuesDict, table, depth=0):
        values = valuesDict.get(key, None)
        nameKey = key[1]
        i = table.addRow()
        charFormat = None if depth else self.boldChars

        if isinstance(values, list):
            table.setText(i, 0, i-self._rowsShift)
            table.setText(i, 1, nameKey, charFormat=charFormat)
            subResult = [0, 0, 0, 0, 0, 0]
            if depth:
                columnShift = 7
                clientValues = self._clientInfo.get(key, [])
                for idx, value in enumerate(clientValues):
                    table.setText(i, idx+2, value)
            else:
                 columnShift = 2
            for idx, value in enumerate(values):
                table.setText(i, idx+columnShift, value)
                subResult[idx] += value
            return subResult

        elif isinstance(values, dict):
            self._rowsShift += 1
            table.setText(i, 1, nameKey, charFormat=charFormat)
            result = [0, 0, 0, 0, 0, 0]
            table.mergeCells(i, 0, 1, 6)
            subKeys = values.keys()
            subKeys.sort(key=lambda item: item[1])
            for subKey in subKeys:
                subResult = self.printValues(subKey, values, table, depth+1)
                result = map(lambda x, y: x+y, subResult, result)
            self.printResult(i, result, table)
            return result


    def printProfileValues(self, key, valuesDict, table, depth=0, financeKey=False):
        values = valuesDict.get(key, None)
        profileKey = key[4] if financeKey else key[3]
        i = table.addRow()
        charFormat = None

        if isinstance(values, list):
            table.setText(i, 0, i-self._rowsShift)
            table.setText(i, 1, self.mapHospitalBedIdToName[profileKey] if profileKey in self.mapHospitalBedIdToName.keys() else u'Профиль не определен', 
                                charFormat=charFormat)
            subResult = [0, 0, 0, 0, 0, 0]
            if depth:
                columnShift = 7
                clientValues = self._clientInfo.get(key, [])
                for idx, value in enumerate(clientValues):
                    table.setText(i, idx+2, value)
            else:
                columnShift = 2
            for idx, value in enumerate(values):
                table.setText(i, idx+columnShift, value)
                subResult[idx] += value
            return subResult


    def printOrgStructureValues(self, key, valuesDict, table, depth=0, financeKey=False):
        values = [0, 0, 0, 0, 0, 0]
        orgStrKey = key[1] if financeKey else key[0]
        for dictKey in valuesDict.keys():
            dictOrgStrKey = dictKey[1] if financeKey else dictKey[0]
            if orgStrKey == dictOrgStrKey:
                if financeKey:
                    if financeKey == dictKey[0]:
                        value = valuesDict.get(dictKey, None)
                        for i in range(len(values)):
                            values[i] += value[i]
                else:
                    value = valuesDict.get(dictKey, None)
                    for i in range(len(values)):
                        values[i] += value[i]
        nameKey = key[2] if financeKey else key[1]
        i = table.addRow()
        charFormat = self.boldChars

        if isinstance(values, list):
            table.setText(i, 0, i-self._rowsShift)
            table.setText(i, 1, nameKey, charFormat=charFormat)
            subResult = [0, 0, 0, 0, 0, 0]
            if depth:
                columnShift = 7
                clientValues = self._clientInfo.get(key, [])
                for idx, value in enumerate(clientValues):
                    table.setText(i, idx+2, value)
            else:
                columnShift = 2
            for idx, value in enumerate(values):
                table.setText(i, idx+columnShift, value, charFormat=charFormat)
                subResult[idx] += value
            return subResult


    def printResult(self, row, values, table, chkDetailClients=True):
        columnShift = 7 if chkDetailClients else 2
        table.mergeCells(row, 0, 1, columnShift)
        for idx, value in enumerate(values):
            table.setText(row, idx+columnShift, value, charFormat=self.boldChars)


    def makeStruct(self, query, params):
        begDate          = params.get('begDate', QDate.currentDate())
        endDate          = params.get('endDate', QDate.currentDate())
        chkDetailClients = params.get('chkDetailClients', False)
        chkDetailFinance = params.get('chkDetailFinance', False)
        financeId        = params.get('financeId', None)
        if financeId:
            chkDetailFinance = False
        chkDetailHospitalBedProfile = params.get('chkDetailHospitalBedProfile', False)
        while query.next():
            record = query.record()

            stayingOrgStructureId   = forceRef(record.value('stayingOrgStructureId'))
            stayingOrgStructureCode = forceString(record.value('stayingOrgStructureCode'))
            actionMovingStayingId   = forceRef(record.value('actionMovingStayingId'))
            hospitalBedProfileId   = forceRef(record.value('hospitalBedProfileId'))
            financeType = forceString(record.value('financeType'))

            if chkDetailClients:
                clientId = forceRef(record.value('clientId'))
                clientName = formatName(record.value('clientLastName'),
                                        record.value('clientFirstName'),
                                        record.value('clientPatrName'))
            fullOrgStructureName = self._orgStructureIdToFullName.get(stayingOrgStructureId, None)
            if not fullOrgStructureName:
                if not stayingOrgStructureId:
                    fullOrgStructureName = u'Подразделение не определено'
                else:
                    fullOrgStructureName = getOrgStructureFullName(stayingOrgStructureId)
                self._orgStructureIdToFullName[stayingOrgStructureId] = fullOrgStructureName

            key = (stayingOrgStructureId, fullOrgStructureName, stayingOrgStructureCode)

            if chkDetailClients:
                clientDict = self._mapOrgStructureToClientValues.setdefault(key, {})
                clientKey = (clientId, clientName, actionMovingStayingId)
                self.makeClientInfo(clientKey, record)
                self.mapValues(clientDict, clientKey, record, begDate, endDate)
            elif chkDetailHospitalBedProfile and not chkDetailFinance:
                key = (stayingOrgStructureId, fullOrgStructureName, stayingOrgStructureCode, hospitalBedProfileId)
                self.mapValues(self._mapOrgStructureToClientValues, key, record, begDate, endDate)
            elif chkDetailFinance:
                key = (financeType, stayingOrgStructureId, fullOrgStructureName, stayingOrgStructureCode, hospitalBedProfileId)
                self.mapValues(self._mapOrgStructureToClientValues, key, record, begDate, endDate)
            else:
                self.mapValues(self._mapOrgStructureToClientValues, key, record, begDate, endDate)

    def mapValues(self, valuesDict, key, record, begDate, endDate):
        movingActionBegDate = forceDate(record.value('movingActionBegDate'))
        movingActionEndDate = forceDate(record.value('movingActionEndDate'))
        movingOrgStructureId = forceRef(record.value('movingOrgStructureId'))
        movingInOrgStructureId = forceRef(record.value('movingInOrgStructureId'))

        values = valuesDict.setdefault(key, [0, 0, 0, 0, 0, 0])

        if movingActionBegDate < begDate:
            values[0] += 1  # состояло
        if begDate <= movingActionBegDate and movingActionBegDate <= endDate:
            if not movingInOrgStructureId:
                values[1] += 1  # поступило
            else:
                values[2] += 1  # переведено в
        if begDate <= movingActionEndDate and movingActionEndDate <= endDate:
            if movingOrgStructureId:
                values[3] += 1  # переведено из
            else:
                values[4] += 1  # выписано
        if movingActionBegDate <= endDate and (not movingActionEndDate or endDate < movingActionEndDate):
            values[5] += 1 # осталось


    def makeClientInfo(self, key, record):
        if key not in self._clientInfo.keys():

            financeTypeName = forceString(record.value('financeTypeName'))
            contractInfo = forceString(record.value('contractInfo'))
            if forceRef(record.value('clientQuotingId')):
                quotaTypeClass = [u'ВТМП', u'СМП', u'Родовой сертификат'][forceInt(record.value('quotaTypeClass'))]
                quotaStatus = [u'Отменено',
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
                               u'Импортировано из ВТМП'][forceInt(record.value('quotaStatus'))]
                quotaTypeCode = forceString(record.value('quotaTypeCode'))
            else:
                quotaTypeClass = u''
                quotaStatus    = u''
                quotaTypeCode  = u''

            self._clientInfo[key] = [financeTypeName, contractInfo, quotaTypeClass, quotaStatus, quotaTypeCode]


    def getDescription(self, params):
        begDate = params.get('begDate', None)
        endDate = params.get('endDate', None)
        financeId = params.get('financeId', None)
        financeText = params.get('financeText', None)
        contractId = params.get('contractId', None)
        contractText = params.get('contractText', None)
        chkQuotaClass = params.get('chkQuotaClass', False)
        quotaClass = params.get('quotaClass', None) if chkQuotaClass else None
        quotaTypeId = params.get('quotaTypeId', False)

        rows = []
        if financeId:
            rows.append(u'Тип финансирования: %s' % financeText)
        if contractId:
            rows.append(u'Контракт: %s' % contractText)
        if begDate:
            rows.append(u'Начальная дата периода: %s'%forceString(begDate))
        if endDate:
            rows.append(u'Конечная дата периода: %s'%forceString(endDate))
        if quotaClass is not None:
            rows.append(u'Класс квоты: %s'%[u'ВТМП', u'СМП'][quotaClass])
        if quotaTypeId:
            rows.append(u'Тип квоты: %s'%forceString(QtGui.qApp.db.translate('QuotaType', 'id',
                                                                            quotaTypeId, 'CONCAT_WS(\' | \', code, name)')))
        return rows
