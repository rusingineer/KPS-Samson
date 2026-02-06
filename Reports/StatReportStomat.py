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
from PyQt4.QtCore import Qt, QDate, QDateTime, QString

from library.PrintInfo          import CInfoContext
from library.Utils              import forceDate, forceDateTime, forceDouble, forceInt, forceRef, forceString

from Events.ActionServiceType   import CActionServiceType
from Events.TeethEventInfo      import CTeethEventInfo
from Orgs.Utils                 import getOrgStructurePersonIdList
from Reports.ReportMonthActions import CSetupReportMonthActions
from Reports.ReportSetupDialog  import CReportSetupDialog
from Reports.Report             import CReport, CReportEx, getOrgStructureFullName, selectMonthData
from Reports.ReportBase         import CReportBase, createTable
from Reports.Utils              import dateRangeAsStr


monthsInYear = 12

def selectData(db, begDate, endDate, orgStructureId, personId, sex, ageFrom, ageTo, locality, isMonth=False, reportType=0):
    stmt= u"""
        SELECT
            Event.id AS `eventId`,
            Event.client_id AS `clientId`,
            Event.execDate AS `date`,
            Event.isPrimary AS `isPrimary`,
            Action.id AS actionId,
            IF(ActionType.flatCode LIKE 'dentitionInspection%%', Action.id, NULL) AS `actionStomatId`,
            IF(ActionType.flatCode LIKE 'parodentInsp%%', Action.id, NULL) AS `actionParodentId`,
            Contract.finance_id AS `contractFinanceId`,
            IF(ActionType.flatCode LIKE 'dentitionInspection%%', Action.finance_id, NULL) AS `stomatActionFinanceId`,
            IF(ActionType.flatCode LIKE 'parodentInsp%%', Action.finance_id, NULL) AS `parodentActionFinanceId`
        FROM
            Event
            LEFT JOIN Client ON Client.id = Event.client_id
            LEFT JOIN Contract ON Contract.id = Event.contract_id
            LEFT JOIN EventType ON EventType.id = Event.eventType_id
            INNER JOIN Action ON Action.event_id = Event.id
            LEFT JOIN ActionType ON ActionType.id = Action.actionType_id
        WHERE
            Event.deleted = 0
            AND Action.endDate IS NOT NULL
            AND EventType.deleted = 0
            AND EventType.form = '043'
            AND Action.deleted = 0
            AND ActionType.deleted = 0
            AND EXISTS (SELECT DentAct.id
            FROM Action AS DentAct
            INNER JOIN ActionType AS DentActType ON DentActType.id=DentAct.actionType_id
            WHERE DentAct.event_id=Event.id AND (DentActType.flatCode LIKE 'dentitionInspection%%' OR DentActType.flatCode LIKE 'parodentInsp%%')
            AND DentAct.deleted=0 AND DentActType.deleted=0)
            AND %s
    """
#    tableEvent = db.table('Event')
    tableAction = db.table('Action')
    cond = []
#    if reportType:
    cond.append(db.joinAnd([tableAction['endDate'].dateGe(begDate),
                            tableAction['endDate'].dateLe(endDate)]))
#    else:
#        addDateInRange(cond, tableEvent['execDate'], begDate, endDate)
    if orgStructureId:
        persons = getOrgStructurePersonIdList(orgStructureId)
        cond.append(tableAction['person_id'].inlist(persons))
    if personId:
        cond.append(tableAction['person_id'].eq(personId))
    if sex:
        cond.append(db.table('Client')['sex'].eq(sex))
    if ageFrom:
        cond.append('age(Client.birthDate, Event.setDate) >= %d'%ageFrom)
    if ageTo is not None:
        cond.append('age(Client.birthDate, Event.setDate) <= %d'%ageTo)
    if locality:
        # 1: горожане, isClientVillager == 0 или NULL
        # 2: сельские жители, isClientVillager == 1
        cond.append('IFNULL(isClientVillager(Client.id), 0) = %d' % (locality-1))
    st = stmt % (db.joinAnd(cond))
    return db.query(st)


def selectDayDataStomat(date, orgStructureId, personId, locality, reportType=0):
    db = QtGui.qApp.db
    return selectData(db, date, date, orgStructureId, personId, None, None, None, locality=locality, reportType=reportType)

def selectMonthDataStomat(date, orgStructureId, personId, sex, ageFrom, ageTo, locality):
    return selectMonthData(selectData, date, orgStructureId, personId, sex, ageFrom, ageTo, locality)

# ###################
def getProp(info, name, where, number):
    propname = u'%s.%s.%d'%(unicode(name), (u'Верхний', u'Нижний')[where], number)
    return info.get(propname, u'')

def getStatus(info, where, number):
    strstatus = getProp(info, u'Статус', where, number)
    return int(strstatus) if len(strstatus) else -1

def getMobility(info, where, number):
    return getProp(info, u'Подвижность', where, number)

def getConditions(info, where, number):
    return getProp(info, u'Состояние', where, number).split(', ')

def hasCondition(info, where, number, name):
    return name in getConditions(info, where, number)

def hasConditions(info, where, number, names):
    resConditions = (hasCondition(info, where, number, name) for name in names)
    return True in resConditions

def hasAnyCondition(info, where, number, names):
    return any(hasCondition(info, where, number, name) for name in names)

def getNumber(info, where, number):
    number = getProp(info, (u'Верх', u'Низ')[where], where, number)
    return int(number) if len(number) else -1

def getSanitation(info):
    return info.get(u'Санация', u'')

def isSanitationNeed(info):
    return u'нуждается' in getSanitation(info)

def isSanitationPlanned(info):
    return u'запланирована' in getSanitation(info)

def isSanitationDone(info):
    return u'проведена' in getSanitation(info)

def selectData2(params):
    begDate = params.get('begDate', QDate())
    endDate = params.get('endDate', QDate())
    orgStructureId = params.get('orgStructureId', None)
    personId = params.get('personId', None)
    sex = params.get('sex', None)
    ageFrom = params.get('ageFrom', None)
    ageTo = params.get('ageTo', None)
    financeId = params.get('financeId', None)
    locality = params.get('locality', 0)
    chkMonthDetail = params.get('chkMonthDetail', False)

    db = QtGui.qApp.db

    tableAction = db.table('Action')
    tableActionType = db.table('ActionType')
    tableActionPropertyType = db.table('ActionPropertyType')
    tableActionProperty = db.table('ActionProperty')
    tableActionPropertyString = db.table('ActionProperty_String')
    tablePerson = db.table('vrbPersonWithSpeciality')
    tableEvent = db.table('Event')
    tableClient = db.table('Client')
    tableContract = db.table('Contract')
    tableContract_Tariff = db.table('Contract_Tariff')
    tablerbService = db.table('rbService')

    queryTable = tableAction
    queryTable = queryTable.leftJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
    queryTable = queryTable.leftJoin(tablePerson, tablePerson['id'].eq(tableAction['person_id']))
    queryTable = queryTable.leftJoin(tableActionProperty, tableActionProperty['action_id'].eq(tableAction['id']))
#    queryTable = queryTable.leftJoin(tableActionProperty, [tableActionProperty['action_id'].eq(tableAction['id']),
#                                                           tableActionType['flatCode'].like('dentitionInspection...')])
    queryTable = queryTable.leftJoin(tableActionPropertyType, [tableActionPropertyType['id'].eq(tableActionProperty['type_id']),
                                                               tableActionPropertyType['actionType_id'].eq(tableActionType['id'])])
    queryTable = queryTable.leftJoin(tableActionPropertyString, tableActionPropertyString['id'].eq(tableActionProperty['id']))
    queryTable = queryTable.leftJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
    queryTable = queryTable.leftJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
    queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
    queryTable = queryTable.leftJoin(tablerbService, tablerbService['id'].eq(tableActionType['nomenclativeService_id']))
    queryTable = queryTable.leftJoin(tableContract_Tariff, u'''(Contract_Tariff.master_id = Contract.id
    and Contract_Tariff.service_id = rbService.id and Contract_Tariff.deleted = 0
    and (Contract_Tariff.endDate is not null and DATE(Action.endDate) between Contract_Tariff.begDate and Contract_Tariff.endDate
    or DATE(Action.endDate) >= Contract_Tariff.begDate and Contract_Tariff.endDate is null) 
  and Contract_Tariff.tariffType in (2,5))''')

    cond = [tableEvent['execDate'].ge(begDate),
            tableEvent['execDate'].lt(endDate.addDays(1)),
            tableEvent['deleted'].eq(0),
            #tableEvent['execDate'].isNotNull(),
            tableAction['deleted'].eq(0),
            tableActionType['deleted'].eq(0),
            'EXISTS (SELECT DentAct.`id` FROM Action AS DentAct INNER JOIN ActionType AS DentActType ON DentActType.`id`=DentAct.`actionType_id` WHERE DentAct.`event_id`=Event.`id` AND DentActType.`flatCode` LIKE \'dentitionInspection%\' AND DentAct.`deleted`=0 AND DentActType.`deleted`=0)'
           ]

    if personId:
        cond.append(tableAction['person_id'].eq(personId))
    elif orgStructureId:
        persons = getOrgStructurePersonIdList(orgStructureId)
        cond.append(tableAction['person_id'].inlist(persons))
    if sex:
        cond.append(tableClient['sex'].eq(sex))
    if ageFrom:
        cond.append('age(Client.`birthDate`, Event.`setDate`) >= %d'%ageFrom)
    if ageTo is not None:
        cond.append('age(Client.`birthDate`, Event.`setDate`) <= %d'%ageTo)
    if financeId:
        cond.append('(Action.`finance_id`=%d) OR (Action.`finance_id` IS NULL AND Contract.`id`=%d)'%(financeId, financeId))
    if locality:
        # 1: горожане, isClientVillager == 0 или NULL
        # 2: сельские жители, isClientVillager == 1
        cond.append('IFNULL(isClientVillager(Client.id), 0) = %d' % (locality-1))
    cond.append(u'''((((ActionPropertyType.name LIKE 'Статус%' OR ActionPropertyType.name LIKE 'Подвижность%' OR ActionPropertyType.name LIKE 'Состояние%')
AND TRIM(ActionProperty_String.value) != '')
OR (ActionPropertyType.name NOT LIKE 'Статус%' AND ActionPropertyType.name NOT LIKE 'Подвижность%' AND ActionPropertyType.name NOT LIKE 'Состояние%'))
OR ActionProperty.type_id IS NULL)''')
    fields = [tableEvent['id'].alias('eventId'),
              tableEvent['client_id'].alias('clientId'),
              tableEvent['execDate'].alias('eventExecDate'),
              tableAction['endDate'],
              tableAction['id'].alias('actionId'),
              tableAction['finance_id'].alias('actionFinanceId'),
              u'''Action.amount * Contract_Tariff.uet as colUET''',
              tableAction['amount'].alias('actionAmount'),
              tableActionType['flatCode'].name(),
              tableActionType['serviceType'].name(),
              tableActionType['id'].alias('actionTypeId'),
              tableActionProperty['id'].alias('actionPropertyId'),
              tableActionPropertyType['name'].alias('propertyName'),
              tableActionPropertyString['value'].alias('propertyValue'),
              tableEvent['isPrimary'].name(),
              tableEvent['contract_id'].alias('contractId'),
              u'age(Client.`birthDate`, Event.`setDate`) AS clientAge',
              u'''(SELECT MIN(A.endDate)
                   FROM Action AS A
                   INNER JOIN ActionType AS AT ON AT.id = A.actionType_id
                   WHERE A.event_id = Event.id AND A.deleted = 0 AND A.endDate IS NOT NULL
                   AND AT.flatCode LIKE 'dentitionInspection%%' AND AT.deleted = 0) AS endDateMin''',
              tablePerson['id'].alias('personId'),
              tablePerson['name'].alias('personName'),
              tablePerson['orgStructure_id'].alias('personOS')]
    if chkMonthDetail:
        fields.append('''CONCAT_WS('-', MONTH(Action.endDate), YEAR(Action.endDate)) AS isMonth''')
    else:
        fields.append('''CONCAT_WS('-', DAY(Action.endDate), IF(LENGTH(MONTH(Action.endDate)) > 1, MONTH(Action.endDate), CONCAT_WS('', '0', MONTH(Action.endDate))), YEAR(Action.endDate)) AS isDay''')
    stmt = db.selectStmtGroupBy(queryTable, fields, cond,  order = u'Action.endDate ASC, Event.id')
    return db.query(stmt)


class CStomatReport(CReportEx):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Отчет о работе стоматолога (форма 039-2)', u'Отчет о работе стоматолога (форма 039-2)')
        self.table_columns = self.getTableColumns()
        self._mapActionTypeId2ServiceIdList = {}


    def getTableColumns(self, keyName=False):
        return [
            ('3%', [u'Месяц' if keyName else u'Дата', '', '', '', u'1'], CReportBase.AlignLeft),
            ('3%', [u'Принято больных (Всего)', '', '', '', u'2'], CReportBase.AlignRight),
            ('5%', [u'Принято первичных больных', '', u'Всего', '', u'3'], CReportBase.AlignRight),
            ('5%', [u'', '', u'Из них детей', '', u'4'], CReportBase.AlignRight),
            ('3%', [u'Запломбировано зубов', u'Всего', '', '', u'5'], CReportBase.AlignRight),
            ('5%', [u'', u'В том числе, по поводу', u'кариеса', u'постоянных', u'6'], CReportBase.AlignRight),
            ('5%', [u'', '', '', u'молочных зубов', u'7'], CReportBase.AlignRight),
            ('5%', [u'', '', u'его осложнений', u'постоянных', u'8'], CReportBase.AlignRight),
            ('5%', [u'', '', '', u'молочных зубов', u'9'], CReportBase.AlignRight),
            ('5%', [u'Вылечено зубов в одно посещение по поводу осложн. кариеса', '', '', '', u'10'], CReportBase.AlignRight),
            ('3%', [u'Кол.-во пломб из амальгамы', '', '', '', u'11'], CReportBase.AlignRight),
            ('5%', [u'Проведен курс лечения', u'Заболевание пародонта', u'Количество зубов', '', u'12'], CReportBase.AlignRight),
            ('5%', [u'', u'', u'Количество пациентов', '', u'13'], CReportBase.AlignRight),
            ('5%', [u'', u'Слизистой оболочки рта', u'', '', u'14'], CReportBase.AlignRight),
            ('3%', [u'Удалено зубов', u'Молочного прикуса (ВСЕГО)', '', '', u'15'], CReportBase.AlignRight),
            ('3%', [u'', u'В том числе по поводу заболеваний пародонта постоянного прикуса', '', '', u'16'], CReportBase.AlignRight),
            ('5%', [u'', u'Постоянного прикуса (ВСЕГО)', '', '', u'17'], CReportBase.AlignRight),
            ('3%', [u'Произведено операций', '', '', '', u'18'], CReportBase.AlignRight),
            ('4%', [u'Всего санировано в порядке плановой санации и по обращению', '', '', '', u'19'], CReportBase.AlignRight),
            ('4%', [u'Профилактическая работа', u'Осмотрено в порядке плановой санации', '', '', u'20'], CReportBase.AlignRight),
            ('4%', [u'', u'Из числа осмотренных нуждалось в санации', '', '', u'21'], CReportBase.AlignRight),
            ('4%', [u'', u'Санировано из числа выявленных при плановой санации', '', '', u'22'], CReportBase.AlignRight),
            ('4%', [u'', u'Проведен курс профилактических мероприятий', u'Количество мероприятий', '', u'23'], CReportBase.AlignRight),
            ('4%', [u'', u'', u'Количество пациентов', '', u'24'], CReportBase.AlignRight),
            ('4%', [u'', u'', u'Количество событий', '', u'25'], CReportBase.AlignRight),
            ('4%', [u'Выработано условных единиц трудоемкости (УЕТ)', '', '', '', u'26'], CReportBase.AlignRight),
            ]


    def getTableColumnsPersonOverall(self, keyName=False):
        cols = [
            ('5%', [u'ФИО врача', '', '', '',u'1'], CReportBase.AlignLeft),
            ('3%', [u'Принято больных (Всего)', '', '', '', u'3' if keyName else u'2'], CReportBase.AlignRight),
            ('5%', [u'Принято первичных больных', '', u'Всего', '', u'4' if keyName else u'3'], CReportBase.AlignRight),
            ('5%', [u'', '', u'Из них детей', '', u'5' if keyName else u'4'], CReportBase.AlignRight),
            ('3%', [u'Запломбировано зубов', u'Всего', '', '', u'6' if keyName else u'5'], CReportBase.AlignRight),
            ('5%', [u'', u'В том числе, по поводу', u'кариеса', u'постоянных', u'7' if keyName else u'6'], CReportBase.AlignRight),
            ('5%', [u'', '', '', u'молочных зубов', u'8' if keyName else u'7'], CReportBase.AlignRight),
            ('5%', [u'', '', u'его осложнений', u'постоянных', u'9' if keyName else u'8'], CReportBase.AlignRight),
            ('5%', [u'', '', '', u'молочных зубов', u'10' if keyName else u'9'], CReportBase.AlignRight),
            ('5%', [u'Вылечено зубов в одно посещение по поводу осложн. кариеса', '', '', '', u'11' if keyName else u'10'], CReportBase.AlignRight),
            ('3%', [u'Кол.-во пломб из амальгамы', '', '', '', u'12' if keyName else u'11'], CReportBase.AlignRight),
            ('5%', [u'Проведен курс лечения', u'Заболевание пародонта', u'Количество зубов', '', u'13' if keyName else u'12'], CReportBase.AlignRight),
            ('5%', [u'', u'', u'Количество пациентов', '', u'14' if keyName else u'13'], CReportBase.AlignRight),
            ('5%', [u'', u'Слизистой оболочки рта', u'', '', u'15' if keyName else u'14'], CReportBase.AlignRight),
            ('3%', [u'Удалено зубов', u'Молочного прикуса (ВСЕГО)', '', '', u'16' if keyName else u'15'], CReportBase.AlignRight),
            ('3%', [u'', u'В том числе по поводу заболеваний пародонта постоянного прикуса', '', '', u'17' if keyName else u'16'], CReportBase.AlignRight),
            ('4%', [u'', u'Постоянного прикуса (ВСЕГО)', '', '', u'18' if keyName else u'17'], CReportBase.AlignRight),
            ('4%', [u'Произведено операций', '', '', '', u'19' if keyName else u'16'], CReportBase.AlignRight),
            ('4%', [u'Всего санировано в порядке плановой санации и по обращению', '', '', '', u'20' if keyName else u'19'], CReportBase.AlignRight),
            ('4%', [u'Профилактическая работа', u'Осмотрено в порядке плановой санации', '', '', u'21' if keyName else u'20'], CReportBase.AlignRight),
            ('4%', [u'', u'Из числа осмотренных нуждалось в санации', '', '', u'22' if keyName else u'21'], CReportBase.AlignRight),
            ('4%', [u'', u'Санировано из числа выявленных при плановой санации', '', '', u'23' if keyName else u'22'], CReportBase.AlignRight),
            ('4%', [u'', u'Проведен курс профилактических мероприятий', u'Количество мероприятий', '', u'24' if keyName else u'23'], CReportBase.AlignRight),
            ('4%', [u'', u'', u'Количество пациентов', '', u'25' if keyName else u'23'], CReportBase.AlignRight),
            ('4%', [u'', u'', u'Количество событий', '', u'26' if keyName else u'23'], CReportBase.AlignRight),
            ('4%', [u'Выработано условных единиц трудоемкости (УЕТ)', '', '', '', u'27' if keyName else u'24'], CReportBase.AlignRight),
            ]
        if keyName:
            cols.insert(1, ('5%', [u'Месяц', '', '', '', u'2'], CReportBase.AlignLeft))
        return cols


    def getSetupDialog(self, parent):
        result = CSetupReportMonthActions(parent)
        result.setTitle(self.title())
        result.setActionTypeClassVisible(False)
        result.setActionTypeGroupVisible(False)
        result.setStatusVisible(False)
        result.setAssistantVisible(False)
        result.setTissueTypeVisible(False)
        result.setPersonDetailVisible(True)
        result.setPersonMonthDetailVisible(True)
        result.setLocalityVisible(True)
        return result


    def getPeriodName(self, params):
        begDate = params.get('begDate', QDate.currentDate())
        endDate = params.get('endDate', QDate.currentDate())
        return dateRangeAsStr(u' период', begDate, endDate)


    def _getNewPersonReportData(self, daysInMonthBeg, daysInMonthEnd):
        reportData = {}
        for dayIdx in xrange(daysInMonthBeg, daysInMonthEnd):
            reportData[dayIdx] = [dayIdx+1]+([0]*(len(self.table_columns)-1))
        return reportData


    def _getActionTypeServiceIdList(self, act):
        actionTypeId = act.typeId
        financeId = act._financeId
        if actionTypeId:
            result = self._mapActionTypeId2ServiceIdList.get((actionTypeId, financeId), None)
            if result is None:
                db = QtGui.qApp.db
                table = db.table('ActionType_Service')
                if financeId:
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
                self._mapActionTypeId2ServiceIdList[actionTypeId] = result
            return result
        return None


    def _getActionTypeServiceId(self, act):
        result = self._getActionTypeServiceIdList(act)
        return forceRef(result[0]) if result else None


    def _getUet(self, eventId, actionId = None):
        context = CInfoContext()
        event = context.getInstance(CTeethEventInfo, eventId)
#        action = event.stomatAction
        uetList = []
        actAmount = 0
        eventActAmountThroughCode = {}
        for act in event.actions:
            if actionId is None or actionId == act._id:
                serviceId = self._getActionTypeServiceId(act)
                endDate=act.endDate
                uet = 0
                db = QtGui.qApp.db
                tableContractTariff = db.table('Contract_Tariff')
                contractId = event.contract.id
                if serviceId and contractId:
                    record = db.getRecordEx(tableContractTariff, [tableContractTariff['uet']], [u'''(Contract_Tariff.master_id = %(contractId)s 
    and Contract_Tariff.service_id = %(serviceId)s  and Contract_Tariff.deleted = 0
    and (Contract_Tariff.endDate is not null and DATE(%(endDate)s) between Contract_Tariff.begDate and Contract_Tariff.endDate
    or DATE(%(endDate)s) >= Contract_Tariff.begDate and Contract_Tariff.endDate is null) 
  and Contract_Tariff.tariffType in (2,5))''' %{"contractId": contractId,"serviceId": serviceId,"endDate": db.formatDate(endDate)}])
                    if record:
                        uet = forceDouble(record.value('uet'))
                        if uet:
                            actAmount += act.amount
                            if serviceId and act.amount:
                                actAmountThroughCode = eventActAmountThroughCode.setdefault(act.typeId, [act.code, 0])
                                actAmountThroughCode[1] += act.amount
                uetList.append(act.amount*uet)
        return sum([amount_uet for amount_uet in uetList])


    def getReportData(self, query, params, daysInMonthBeg, daysInMonthEnd, chkPersonDetail, chkPersonOverall, chkPersonOSDetail, chkMonthDetail=False, forceKeyVal=None, keyValToString=None, keyValToSort=None):
        personReportData = {}
        personOSReportData = {}
        personOSList = {}
        person2Values = {}
        eventIdDict = {}
        actionIdDict = {}
        begDatePeriod = params.get('begDate', QDate())
        endDatePeriod = params.get('endDate', QDate())
        clientIdList = []
        tempPerson = None
        clientIdList14 = []
        clientIdList22 = []
        eventIdList23 = []
        while query.next():
            record = query.record()
            eventId = forceRef(record.value('eventId'))
            actionId = forceRef(record.value('actionId'))
            clientId = forceRef(record.value('clientId'))
            endDate = forceDate(record.value('endDate'))
            endDateMin = forceDate(record.value('endDateMin'))
            personId = forceRef(record.value('personId'))
            personName = forceString(record.value('personname'))
            flatCode = forceString(record.value('flatCode'))
            colUET = forceDouble(record.value('colUET'))
            if tempPerson != personId:
                tempPerson = personId
                clientIdList22 = []
            if chkPersonOSDetail:
                osKey = forceRef(record.value('personOS'))
                person2Values = personOSList.setdefault(osKey, {})
            if chkMonthDetail:
                day = forceKeyVal(record.value('isMonth'))
            else:
                day = forceKeyVal(record.value('isDay'))
            personKey = (personId, personName) if (chkPersonDetail or chkPersonOverall) else (None, u'')
            day2Values = person2Values.setdefault(personKey, {})
            eventIdList = eventIdDict.get(personKey, [])
            actionIdList = actionIdDict.get(personKey, [])
            dayValues = day2Values.setdefault(day, {'eventCount':0,
                                                    'isPrimary':0,
                                                    'teenagerIsPrimary':0,
                                                    'prophylaxis':0,
                                                    'prophylaxisClient':0,
                                                    'prophylaxisEvent':0,
                                                    'uet':0.0,
                                                    'operation':0.0})
            if u'dentitionInspection' in flatCode:
                propertyName = forceString(record.value('propertyName'))
                propertyValue = forceString(record.value('propertyValue'))
                actionValues = dayValues.setdefault((actionId, clientId), {})
                actionValues[propertyName] = propertyValue
            if eventId not in eventIdList:
                isPrimary = forceInt(record.value('isPrimary')) == 1
                clientAge = forceInt(record.value('clientAge'))
                if endDateMin == endDate:
                    dayValues['isPrimary'] += isPrimary
                    dayValues['teenagerIsPrimary'] += clientAge < 15 and isPrimary
                    eventIdList.append(eventId)
            if actionId not in actionIdList:
                if u'dentitionInspection' in flatCode:
                    dayValues['eventCount'] += 1
                serviceType = forceInt(record.value('serviceType'))
                actionAmount = forceDouble(record.value('actionAmount'))
                dayValues['prophylaxis'] += actionAmount if serviceType == CActionServiceType.prophylaxis else 0
                if eventId and eventId not in eventIdList23:
                    if serviceType == CActionServiceType.prophylaxis:
                        eventIdList23.append(eventId)
                    dayValues['prophylaxisEvent'] += serviceType == CActionServiceType.prophylaxis
                if clientId and clientId not in clientIdList22:
                    if serviceType == CActionServiceType.prophylaxis:
                        clientIdList22.append(clientId)
                    dayValues['prophylaxisClient'] += serviceType == CActionServiceType.prophylaxis
                if serviceType == CActionServiceType.operation:
                    dayValues['operation'] += actionAmount
                dayValues['uet'] += colUET
                actionIdList.append(actionId)
            eventIdDict[personKey] = eventIdList
            actionIdDict[personKey] = actionIdList

        def setDataList(personReportData):
            if chkMonthDetail:
                def getNewBuff(begDatePeriod, endDatePeriod):
                    endMonth = endDatePeriod.month()
                    endYear  = endDatePeriod.year()
                    endDate = QDate(endYear, endMonth, 1)
                    nextMonth = begDatePeriod.month()
                    nextYear  = begDatePeriod.year()
                    nextDate = QDate(nextYear, nextMonth, 1)
                    newBuff = {}
                    while nextDate <= endDate and nextYear <= endYear:
                        monthKey = forceString(nextMonth) + u'-' + forceString(nextYear)
                        newBuff[monthKey] = [0]*(len(self.table_columns))
                        newBuff[monthKey][0] = monthKey
                        if nextYear < endYear and nextMonth == 12:
                            nextYear += 1
                            nextMonth = 1
                        else:
                            nextMonth += 1
                        nextDate = nextDate.addMonths(1)
                    return newBuff
                for personKey, day2Values in person2Values.items():
                    reportData = personReportData.setdefault(personKey, getNewBuff(begDatePeriod, endDatePeriod))
                    for day, dayValues in day2Values.items():
                        if not dayValues:
                            continue
                        rl                = reportData.get(day, [])
                        if not rl:
                            continue
                        rl[1]             = dayValues.pop('eventCount')
                        rl[2]             = dayValues.pop('isPrimary')
                        rl[3]             = dayValues.pop('teenagerIsPrimary')
                        rl[17]            = dayValues.pop('operation')
                        rl[22]            = dayValues.pop('prophylaxis')
                        rl[23]            = dayValues.pop('prophylaxisClient')
                        rl[24]            = dayValues.pop('prophylaxisEvent')
                        rl[25]            = dayValues.pop('uet')
                        for (actionId, clientId), actionValues in dayValues.items():
                            rl[4]  += len([k for k in xrange(16) if getStatus(actionValues, 0, k+1) in (5, 6, 7)])
                            rl[4]  += len([k for k in xrange(16) if getStatus(actionValues, 1, k+1) in (5, 6, 7)])
                            rl[5]  += len([k for k in xrange(16) if getStatus(actionValues, 0, k+1) == 5
                                                                and hasAnyCondition(actionValues, 0, k+1, (u"П/С", u"C"))
                                                                and (getNumber(actionValues, 0, k+1) > 0
                                                                and getNumber(actionValues, 0, k+1) <= 48)])
                            rl[5]  += len([k for k in xrange(16) if getStatus(actionValues, 1, k+1) == 5
                                                                and hasAnyCondition(actionValues, 1, k+1, (u"П/С", u"C"))
                                                                and (getNumber(actionValues, 1, k+1) > 0
                                                                and getNumber(actionValues, 1, k+1) <= 48)])
                            rl[6]  += len([k for k in xrange(16) if getStatus(actionValues, 0, k+1) == 5
                                                                and hasAnyCondition(actionValues, 0, k+1, (u"П/С", u"C"))
                                                                and getNumber(actionValues, 0, k+1) >= 50])
                            rl[6]  += len([k for k in xrange(16) if getStatus(actionValues, 1, k+1) == 5
                                                                and hasAnyCondition(actionValues, 1, k+1, (u"П/С", u"C"))
                                                                and getNumber(actionValues, 1, k+1) >= 50])
                            rl[7]  += len([k for k in xrange(16) if getStatus(actionValues, 0, k+1) in (6, 7)
                                                                and hasAnyCondition(actionValues, 0, k+1, (u"П/С", u"C", u"P", u"Pt", u"R"))
                                                                and (getNumber(actionValues, 0, k+1) > 0
                                                                and getNumber(actionValues, 0, k+1) <= 48)])
                            rl[7]  += len([k for k in xrange(16) if getStatus(actionValues, 1, k+1) in (6, 7)
                                                                and hasAnyCondition(actionValues, 1, k+1, (u"П/С", u"C", u"P", u"Pt", u"R"))
                                                                and (getNumber(actionValues, 1, k+1) > 0
                                                                and getNumber(actionValues, 1, k+1) <= 48)])
                            rl[8]  += len([k for k in xrange(16) if getStatus(actionValues, 0, k+1) in (6, 7)
                                                                and hasAnyCondition(actionValues, 0, k+1, (u"П/С", u"C", u"P", u"Pt", u"R"))
                                                                and getNumber(actionValues, 0, k+1) >= 50])
                            rl[8]  += len([k for k in xrange(16) if getStatus(actionValues, 1, k+1) in (6, 7)
                                                                and hasAnyCondition(actionValues, 1, k+1, (u"П/С", u"C", u"P", u"Pt", u"R"))
                                                                and getNumber(actionValues, 1, k+1) >= 50])
                            rl[9]  += len([k for k in xrange(16) if getStatus(actionValues, 0, k+1) == 6
                                                                and hasAnyCondition(actionValues, 0, k+1, (u"П/С", u"C", u"P", u"Pt", u"R"))])
                            rl[9]  += len([k for k in xrange(16) if getStatus(actionValues, 1, k+1) == 6
                                                                and hasAnyCondition(actionValues, 1, k+1, (u"П/С", u"C", u"P", u"Pt", u"R"))])
                            rl[10] += len([k for k in xrange(16) if getStatus(actionValues, 0, k+1) in (5, 6, 7)
                                                                and hasCondition(actionValues, 0, k+1, u"Па")])
                            rl[10] += len([k for k in xrange(16) if getStatus(actionValues, 1, k+1) in (5, 6, 7)
                                                                and hasCondition(actionValues, 1, k+1, u"Па")])
                            rl[11] += len([k for k in xrange(16) if getStatus(actionValues, 0, k+1) == 4
                                                                and hasConditions(actionValues, 0, k+1, (u"A", u"G"))])
                            rl[11] += len([k for k in xrange(16) if getStatus(actionValues, 1, k+1) == 4
                                                                and hasConditions(actionValues, 1, k+1, (u"A", u"G"))])
                            for k in xrange(16):
                                if ((getStatus(actionValues, 0, k+1) == 4 and hasConditions(actionValues, 0, k+1, (u"A", u"G"))) or (getStatus(actionValues, 1, k+1) == 4
                                                                        and hasConditions(actionValues, 1, k+1, (u"A", u"G")))) and clientId and clientId not in clientIdList:
                                    clientIdList.append(clientId)
                                    rl[12] += 1
                            for k in xrange(16):
                                if ((getStatus(actionValues, 0, k+1) == 4 and not hasConditions(actionValues, 0, k+1, (u"A", u"G")))
                                or (getStatus(actionValues, 1, k+1) == 4 and not hasConditions(actionValues, 1, k+1, (u"A", u"G")))) and clientId and clientId not in clientIdList14:
                                    clientIdList14.append(clientId)
                                    rl[13] += 1
                            rl[14] += len([k for k in xrange(16) if getStatus(actionValues, 0, k+1) == 9
                                                                and getNumber(actionValues, 0, k+1) >= 50])
                            rl[14] += len([k for k in xrange(16) if getStatus(actionValues, 1, k+1) == 9
                                                                and getNumber(actionValues, 1, k+1) >= 50])
                            rl[15] += len([k for k in xrange(16) if getStatus(actionValues, 0, k+1) == 9
                                                                and hasCondition(actionValues, 0, k+1, u"A")
                                                                and (getNumber(actionValues, 0, k+1) > 0
                                                                and getNumber(actionValues, 0, k+1) <= 48)])
                            rl[15] += len([k for k in xrange(16) if getStatus(actionValues, 1, k+1) == 9
                                                                and hasCondition(actionValues, 1, k+1, u"A")
                                                                and (getNumber(actionValues, 1, k+1) > 0
                                                                and getNumber(actionValues, 1, k+1) <= 48)])
                            rl[16] += len([k for k in xrange(16) if getStatus(actionValues, 0, k+1) == 9
                                                                and (getNumber(actionValues, 0, k+1) > 0
                                                                and getNumber(actionValues, 0, k+1) <= 48)])
                            rl[16] += len([k for k in xrange(16) if getStatus(actionValues, 1, k+1) == 9
                                                                and (getNumber(actionValues, 1, k+1) > 0
                                                                and getNumber(actionValues, 1, k+1) <= 48)])
                            rl[18] += isSanitationDone(actionValues)
                            rl[19] += isSanitationPlanned(actionValues)
                            rl[20] += isSanitationNeed(actionValues)
                            rl[21] += isSanitationPlanned(actionValues) and isSanitationDone(actionValues)
            else:
                def getNewBuff(begDatePeriod, endDatePeriod):
                    endDay    = endDatePeriod.day()
                    endMonth  = endDatePeriod.month()
                    endYear   = endDatePeriod.year()
                    endDate   = QDate(endYear, endMonth, endDay)
                    nextDay   = begDatePeriod.day()
                    nextMonth = begDatePeriod.month()
                    nextYear  = begDatePeriod.year()
                    nextDate  = QDate(nextYear, nextMonth, nextDay)
                    newBuff = {}
                    while nextDate <= endDate and nextYear <= endYear:
                        nextMonthStr = forceString(nextMonth)
                        monthKey = forceString(nextDay) + u'-' + (nextMonthStr if len(nextMonthStr) > 1 else (U'0' + nextMonthStr)) + u'-' + forceString(nextYear)
                        newBuff[monthKey] = [0]*(len(self.table_columns))
                        newBuff[monthKey][0] = monthKey
                        if nextDay >= nextDate.daysInMonth() and nextYear < endYear and nextMonth == 12:
                            nextYear += 1
                            nextMonth = 1
                            nextDay = 1
                        elif nextDay >= nextDate.daysInMonth():
                            nextMonth += 1
                            nextDay = 1
                        else:
                            nextDay += 1
                        nextDate = nextDate.addDays(1)
                    return newBuff
                for personKey, day2Values in person2Values.items():
                    reportData = personReportData.setdefault(personKey, getNewBuff(begDatePeriod, endDatePeriod))
                    for day, dayValues in day2Values.items():
                        if not dayValues:
                            continue
                        rl                = reportData.get(day, [])
                        if not rl:
                            continue
                        rl[1]             = dayValues.pop('eventCount')
                        rl[2]             = dayValues.pop('isPrimary')
                        rl[3]             = dayValues.pop('teenagerIsPrimary')
                        rl[17]            = dayValues.pop('operation')
                        rl[22]            = dayValues.pop('prophylaxis')
                        rl[23]            = dayValues.pop('prophylaxisClient')
                        rl[24]            = dayValues.pop('prophylaxisEvent')
                        rl[25]            = dayValues.pop('uet')
                        for (actionId, clientId), actionValues in dayValues.items():
                            rl[4]  += len([k for k in xrange(16) if getStatus(actionValues, 0, k+1) in (5, 6, 7)])
                            rl[4]  += len([k for k in xrange(16) if getStatus(actionValues, 1, k+1) in (5, 6, 7)])
                            rl[5]  += len([k for k in xrange(16) if getStatus(actionValues, 0, k+1) == 5
                                                                and hasAnyCondition(actionValues, 0, k+1, (u"П/С", u"C"))
                                                                and (getNumber(actionValues, 0, k+1) > 0
                                                                and getNumber(actionValues, 0, k+1) <= 48)])
                            rl[5]  += len([k for k in xrange(16) if getStatus(actionValues, 1, k+1) == 5
                                                                and hasAnyCondition(actionValues, 1, k+1, (u"П/С", u"C"))
                                                                and (getNumber(actionValues, 1, k+1) > 0
                                                                and getNumber(actionValues, 1, k+1) <= 48)])
                            rl[6]  += len([k for k in xrange(16) if getStatus(actionValues, 0, k+1) == 5
                                                                and hasAnyCondition(actionValues, 0, k+1, (u"П/С", u"C"))
                                                                and getNumber(actionValues, 0, k+1) >= 50])
                            rl[6]  += len([k for k in xrange(16) if getStatus(actionValues, 1, k+1) == 5
                                                                and hasAnyCondition(actionValues, 1, k+1, (u"П/С", u"C"))
                                                                and getNumber(actionValues, 1, k+1) >= 50])
                            rl[7]  += len([k for k in xrange(16) if getStatus(actionValues, 0, k+1) in (6, 7)
                                                                and hasAnyCondition(actionValues, 0, k+1, (u"П/С", u"C", u"P", u"Pt", u"R"))
                                                                and (getNumber(actionValues, 0, k+1) > 0
                                                                and getNumber(actionValues, 0, k+1) <= 48)])
                            rl[7]  += len([k for k in xrange(16) if getStatus(actionValues, 1, k+1) in (6, 7)
                                                                and hasAnyCondition(actionValues, 1, k+1, (u"П/С", u"C", u"P", u"Pt", u"R"))
                                                                and (getNumber(actionValues, 1, k+1) > 0
                                                                and getNumber(actionValues, 1, k+1) <= 48)])
                            rl[8]  += len([k for k in xrange(16) if getStatus(actionValues, 0, k+1) in (6, 7)
                                                                and hasAnyCondition(actionValues, 0, k+1, (u"П/С", u"C", u"P", u"Pt", u"R"))
                                                                and getNumber(actionValues, 0, k+1) >= 50])
                            rl[8]  += len([k for k in xrange(16) if getStatus(actionValues, 1, k+1) in (6, 7)
                                                                and hasAnyCondition(actionValues, 1, k+1, (u"П/С", u"C", u"P", u"Pt", u"R"))
                                                                and getNumber(actionValues, 1, k+1) >= 50])
                            rl[9]  += len([k for k in xrange(16) if getStatus(actionValues, 0, k+1) == 6
                                                                and hasAnyCondition(actionValues, 0, k+1, (u"П/С", u"C", u"P", u"Pt", u"R"))])
                            rl[9]  += len([k for k in xrange(16) if getStatus(actionValues, 1, k+1) == 6
                                                                and hasAnyCondition(actionValues, 1, k+1, (u"П/С", u"C", u"P", u"Pt", u"R"))])
                            rl[10] += len([k for k in xrange(16) if getStatus(actionValues, 0, k+1) in (5, 6, 7)
                                                                and hasCondition(actionValues, 0, k+1, u"Па")])
                            rl[10] += len([k for k in xrange(16) if getStatus(actionValues, 1, k+1) in (5, 6, 7)
                                                                and hasCondition(actionValues, 1, k+1, u"Па")])
                            rl[11] += len([k for k in xrange(16) if getStatus(actionValues, 0, k+1) == 4
                                                                and hasConditions(actionValues, 0, k+1, (u"A", u"G"))])
                            rl[11] += len([k for k in xrange(16) if getStatus(actionValues, 1, k+1) == 4
                                                                and hasConditions(actionValues, 1, k+1, (u"A", u"G"))])
                            for k in xrange(16):
                                if ((getStatus(actionValues, 0, k+1) == 4 and hasConditions(actionValues, 0, k+1, (u"A", u"G"))) or (getStatus(actionValues, 1, k+1) == 4
                                                                        and hasConditions(actionValues, 1, k+1, (u"A", u"G")))) and clientId and clientId not in clientIdList:
                                    clientIdList.append(clientId)
                                    rl[12] += 1
                            for k in xrange(16):
                                if ((getStatus(actionValues, 0, k+1) == 4 and not hasConditions(actionValues, 0, k+1, (u"A", u"G")))
                                or (getStatus(actionValues, 1, k+1) == 4 and not hasConditions(actionValues, 1, k+1, (u"A", u"G")))) and clientId and clientId not in clientIdList14:
                                    clientIdList14.append(clientId)
                                    rl[13] += 1
                            rl[14] += len([k for k in xrange(16) if getStatus(actionValues, 0, k+1) == 9
                                                                and getNumber(actionValues, 0, k+1) >= 50])
                            rl[14] += len([k for k in xrange(16) if getStatus(actionValues, 1, k+1) == 9
                                                                and getNumber(actionValues, 1, k+1) >= 50])
                            rl[15] += len([k for k in xrange(16) if getStatus(actionValues, 0, k+1) == 9
                                                                and hasCondition(actionValues, 0, k+1, u"A")
                                                                and (getNumber(actionValues, 0, k+1) > 0
                                                                and getNumber(actionValues, 0, k+1) <= 48)])
                            rl[15] += len([k for k in xrange(16) if getStatus(actionValues, 1, k+1) == 9
                                                                and hasCondition(actionValues, 1, k+1, u"A")
                                                                and (getNumber(actionValues, 1, k+1) > 0
                                                                and getNumber(actionValues, 1, k+1) <= 48)])
                            rl[16] += len([k for k in xrange(16) if getStatus(actionValues, 0, k+1) == 9
                                                                and (getNumber(actionValues, 0, k+1) > 0
                                                                and getNumber(actionValues, 0, k+1) <= 48)])
                            rl[16] += len([k for k in xrange(16) if getStatus(actionValues, 1, k+1) == 9
                                                                and (getNumber(actionValues, 1, k+1) > 0
                                                                and getNumber(actionValues, 1, k+1) <= 48)])
                            rl[18] += isSanitationDone(actionValues)
                            rl[19] += isSanitationPlanned(actionValues)
                            rl[20] += isSanitationNeed(actionValues)
                            rl[21] += isSanitationPlanned(actionValues) and isSanitationDone(actionValues)
                            reportData[day] = rl
            return personReportData
        resultReportData = {}
        if chkPersonOSDetail:
            for personOSKey, person2Values in personOSList.items():
                personReportData = personOSReportData.setdefault(personOSKey, {})
                personReportData = setDataList(personReportData)
            resultReportData = personOSReportData
        else:
            resultReportData = setDataList(personReportData)
        return resultReportData


    def dumpParams(self, cursor, params):
        sexList = (u'не определено', u'мужской', u'женский')
        description = []
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        if begDate and endDate:
            description.append(dateRangeAsStr(u'за период', begDate, endDate))
        orgStructureId = params.get('orgStructureId', None)
        sexIndex = params.get('sex', 0)
        ageFor = params.get('ageFrom', 0)
        ageTo = params.get('ageTo', 150)
        personExecId = params.get('personId', None)
        if orgStructureId:
            description.append(u'подразделение: ' + getOrgStructureFullName(orgStructureId))
        else:
            description.append(u'подразделение: ЛПУ')
        financeId = params.get('financeId', None)
        description.append(u'тип финансирования: %s'%(forceString(QtGui.qApp.db.translate('rbFinance', 'id', financeId, 'name')) if financeId else u'не задано'))
        if sexIndex:
            description.append(u'пол ' + sexList[sexIndex])
        if ageFor or ageTo:
            description.append(u'возраст' + u' с '+forceString(ageFor) + u' по '+forceString(ageTo))
        locality = params.get('locality', 0)
        if locality:
            description.append(u'местность: %s жители' % ((u'городские', u'сельские')[locality-1]))
        if personExecId:
            personExecName = forceString(QtGui.qApp.db.translate('vrbPersonWithSpeciality', 'id', personExecId, 'name'))
            description.append(u'исполнитель ' + personExecName)
        if params.get('chkPersonOSDetail', False):
            description.append(u'Детализировать по подразделениям')
        if params.get('chkPersonOverall', False):
            description.append(u'Общий по врачам')
        if params.get('chkPersonDetail', False):
            description.append(u'Детализировать по врачам')
        if params.get('chkMonthDetail', False):
            description.append(u'Детализировать по месяцам')
        if params.get('chkPersonOverall', False):
            description.append(u'Детализировать по датам')
        description.append(u'отчёт составлен: '+forceString(QDateTime.currentDateTime()))
        columns = [ ('100%', [], CReportBase.AlignLeft) ]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()


    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        reportName = self.getReportName()
        if 'getPeriodName' in dir(self):
            reportName += u' за ' + self.getPeriodName(params)
        self.addParagraph(cursor, reportName)
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        old_table_columns = [self.table_columns[i] for i in xrange(len(self.table_columns))]
        self.buildInt(params, cursor)
        self.table_columns = old_table_columns
        cursor.movePosition(QtGui.QTextCursor.End)
        return doc


    def buildInt(self, params, cursor):
        query = selectData2(params)
        orgStructureNameList = {}
        orgStructureId = params.get('orgStructureId', None)
        chkPersonOSDetail = params.get('chkPersonOSDetail', False)
        chkPersonDetail = params.get('chkPersonDetail', False)
        chkPersonOverall = params.get('chkPersonOverall', False)
        chkPersonDateDetail = params.get('chkPersonDateDetail', False)
        begDate = params.get('begDate', QDate.currentDate())
        endDate = params.get('endDate', QDate.currentDate())
        daysInMonthBeg = begDate
        daysInMonthEnd = endDate
        chkMonthDetail = params.get('chkMonthDetail', False)
        keyValToSort = None
        if chkMonthDetail:
            forceKeyVal = forceString
            keyValToString = lambda x: forceString(x)
            keyValToSort = lambda x: (forceInt(QString(x).split('-')[1]), forceInt(QString(x).split('-')[0]))
            keyName = u'Месяц'
            personReportData = self.getReportData(query, params, daysInMonthBeg, daysInMonthEnd, chkPersonDetail, chkPersonOverall, chkPersonOSDetail, chkMonthDetail, forceKeyVal, keyValToString, keyValToSort)
        else:
            forceKeyVal = forceString
            keyValToString = lambda x: forceString(x)
            keyValToSort = lambda x: (forceInt(QString(x).split('-')[2]),forceInt(QString(x).split('-')[1]), forceInt(QString(x).split('-')[0]))
            keyName = None
            personReportData = self.getReportData(query, params,  daysInMonthBeg, daysInMonthEnd, chkPersonDetail, chkPersonOverall, chkPersonOSDetail, chkMonthDetail, forceKeyVal, keyValToString, keyValToSort)

        if chkPersonOverall and not chkPersonDateDetail:
            self.table_columns = self.getTableColumnsPersonOverall(keyName)
        elif chkPersonOverall and chkPersonDateDetail:
            self.table_columns = self.getTableColumns(keyName)
            self.table_columns.insert(0, ('5%', [u'ФИО', '', '', '', u''], CReportBase.AlignLeft))
        else:
            self.table_columns = self.getTableColumns(keyName)

        if chkPersonOSDetail:
            db = QtGui.qApp.db
            table = db.table('OrgStructure')
            if orgStructureId:
                orgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', orgStructureId)
            else:
                orgStructureIdList = []
            cond = [table['deleted'].eq(0)]
            if orgStructureIdList:
                cond.append(table['id'].inlist(orgStructureIdList))
            records = db.getRecordList(table, [table['id'], table['name']], cond)
            for record in records:
                id = forceRef(record.value('id'))
                name = forceString(record.value('name'))
                orgStructureNameList[id] = name
        detailPersonDate = (not chkPersonOverall and not chkPersonDetail) or ((chkPersonOverall or chkPersonDetail) and chkPersonDateDetail)
        if chkPersonOSDetail:
            self.setTableDataOrgStructure(cursor, personReportData, chkPersonOverall, chkPersonDetail, chkPersonDateDetail, chkMonthDetail, daysInMonthBeg, daysInMonthEnd, detailPersonDate, orgStructureNameList, keyValToSort=keyValToSort)
        else:
            self.setTableData(cursor, personReportData, chkPersonOverall, chkPersonDetail, chkPersonDateDetail, chkMonthDetail, daysInMonthBeg, daysInMonthEnd, detailPersonDate, keyValToSort=keyValToSort)


    def setTableDataOrgStructure(self, cursor, personReportData, chkPersonOverall, chkPersonDetail, chkPersonDateDetail, chkMonthDetail, daysInMonthBeg, daysInMonthEnd, detailPersonDate, orgStructureNameList, keyValToSort=None):
        firstPerson = True
        boldChars = QtGui.QTextCharFormat()
        boldChars.setFontWeight(QtGui.QFont.Bold)
        blockFormatCenter =QtGui.QTextBlockFormat()
        blockFormatCenter.setAlignment(Qt.AlignCenter)

        if chkPersonOverall and detailPersonDate:
            table = self._getPersonOverallTable(cursor, keyName=((chkMonthDetail or chkPersonDateDetail) and chkPersonOverall))
        else:
            table = self._getPersonTable(cursor, keyName=((chkMonthDetail or chkPersonDateDetail) and chkPersonOverall))
        lenColumns = len(self.table_columns)
        resultTotal = [0]*(lenColumns-1)
        for personKeyOS, reportDataOS in personReportData.items():
            firstPersonOS = True
            resultTotalOS = [0]*(lenColumns-1)
            for personKey, reportData in reportDataOS.items():
                if chkPersonDetail:
                    cursor.movePosition(QtGui.QTextCursor.End)
                    format = QtGui.QTextCharFormat()
                    font = QtGui.QFont()
                    font.setBold(True)
                    font.setPointSize(13)
                    format.setFont(font)
                    cursor.setCharFormat(format)
                    if firstPerson:
                        cursor.insertText(u'Врач: %s\n'%personKey[1])
                        firstPerson = False
                    else:
                        cursor.insertText(u'\n\nВрач: %s\n'%personKey[1])
                if chkPersonOverall:
                    firstPersonOverall = True
                elif chkPersonDetail:
                    table = self._getPersonTable(cursor, keyName=((chkMonthDetail or chkPersonDateDetail) and chkPersonOverall))
                if chkMonthDetail:
                    result = [0]*(lenColumns-1)
                    monthKeys = reportData.keys()
                    if keyValToSort:
                        monthKeys.sort(key=keyValToSort)
                    else:
                        monthKeys.sort()
                    for monthKey in monthKeys:
                        values = reportData.get(monthKey, [0]*len(self.table_columns))
                        row = table.addRow()
                        if firstPersonOS:
                            table.setText(row, 0, orgStructureNameList.get(personKeyOS, u''), charFormat=boldChars, blockFormat=blockFormatCenter)
                            firstPersonOS = False
                            table.mergeCells(row, 0, 1, lenColumns)
                            row = table.addRow()
                        for j, value in enumerate(values):
                            if chkPersonOverall:
                                if firstPersonOverall:
                                    table.setText(row, 0, personKey[1])
                                    mergeRow = row
                                    mergeCol = len(reportData.keys())
                                    firstPersonOverall = False
                                table.setText(row, j+1, value)
                            else:
                                table.setText(row, j, value)
                            if j:
                                result[j-1] += value
                                resultTotal[j-1] += value
                                resultTotalOS[j-1] += value
                    if chkPersonOverall or chkPersonDetail:
                        row = table.addRow()
                        if chkPersonOverall:
                            table.setText(row, 1, u'Итого:')
                        else:
                            if chkPersonDetail:
                                if firstPersonOS:
                                    table.setText(row, 0, orgStructureNameList.get(personKeyOS, u''), charFormat=boldChars, blockFormat=blockFormatCenter)
                                    firstPersonOS = False
                                    table.mergeCells(row, 0, 1, lenColumns)
                                    row = table.addRow()
                                table.setText(row, 0, u'Итого:')
                        if chkPersonOverall:
                            for j in xrange(len(result)-1 if (chkPersonOverall) else len(result)):
                                table.setText(row, j+2 if (chkPersonOverall) else j+1, result[j])
                    if chkPersonOverall:
                        table.mergeCells(mergeRow, 0, mergeCol, 1)
                        table.mergeCells(row, 0, 1, 2)
                else:
                    result = [0]*(lenColumns-1)
                    monthKeys = reportData.keys()
                    if keyValToSort:
                        monthKeys.sort(key=keyValToSort)
                    else:
                        monthKeys.sort()
                    for monthKey in monthKeys:
                        values = reportData.get(monthKey, [0]*len(self.table_columns))
                        if detailPersonDate:
                            row = table.addRow()
                            if firstPersonOS:
                                table.setText(row, 0, orgStructureNameList.get(personKeyOS, u''), charFormat=boldChars, blockFormat=blockFormatCenter)
                                firstPersonOS = False
                                table.mergeCells(row, 0, 1, lenColumns)
                                row = table.addRow()
                        for j, value in enumerate(values):
                            if detailPersonDate:
                                if chkPersonOverall:
                                    if firstPersonOverall:
                                        table.setText(row, 0, personKey[1])
                                        mergeRow = row
                                        firstPersonOverall = False
                                    table.setText(row, j+1, value)
                                else:
                                    table.setText(row, j, value)
                            if j:
                                result[j-1] += value
                                resultTotal[j-1] += value
                                resultTotalOS[j-1] += value
                    if chkPersonOverall or chkPersonDetail:
                        row = table.addRow()
                        if not detailPersonDate and chkPersonOverall:
                            if firstPersonOS:
                                table.setText(row, 0, orgStructureNameList.get(personKeyOS, u''), charFormat=boldChars, blockFormat=blockFormatCenter)
                                firstPersonOS = False
                                table.mergeCells(row, 0, 1, lenColumns)
                                row = table.addRow()
                            table.setText(row, 0, personKey[1])
                        elif detailPersonDate and chkPersonOverall:
                            table.setText(row, 1, u'Итого:')
                        else:
                            if chkPersonDetail:
                                if firstPersonOS:
                                    table.setText(row, 0, orgStructureNameList.get(personKeyOS, u''), charFormat=boldChars, blockFormat=blockFormatCenter)
                                    firstPersonOS = False
                                    table.mergeCells(row, 0, 1, lenColumns)
                                    row = table.addRow()
                                table.setText(row, 0, u'Итого:')
                        if chkPersonOverall:
                            for j in xrange(len(result)-1 if (chkPersonOverall and detailPersonDate) else len(result)):
                                table.setText(row, j+2 if (chkPersonOverall and detailPersonDate) else j+1, result[j])

                        if detailPersonDate and chkPersonOverall:
                            table.mergeCells(mergeRow, 0, daysInMonthEnd.day() + daysInMonthBeg.day() + 1, 1)

            row = table.addRow()
            table.setText(row, 0, u'Итого по подразделению:', charFormat=boldChars)
            if (detailPersonDate or chkMonthDetail) and chkPersonOverall:
                table.mergeCells(row, 0, 1, 2)
            elif chkPersonOverall:
                table.mergeCells(row, 0, 1, 1)
            for j in xrange(len(resultTotalOS)-1 if (chkPersonOverall and (detailPersonDate or chkMonthDetail)) else len(resultTotalOS)):
                table.setText(row, j+2 if (chkPersonOverall and (detailPersonDate or chkMonthDetail)) else j+1, resultTotalOS[j], charFormat=boldChars)

        row = table.addRow()
        table.setText(row, 0, u'Всего по подразделениям:', charFormat=boldChars)
        if (detailPersonDate or chkMonthDetail) and chkPersonOverall:
            table.mergeCells(row, 0, 1, 2)
        elif chkPersonOverall:
            table.mergeCells(row, 0, 1, 1)
        for j in xrange(len(resultTotal)-1 if (chkPersonOverall and (detailPersonDate or chkMonthDetail)) else len(resultTotal)):
            table.setText(row, j+2 if (chkPersonOverall and (detailPersonDate or chkMonthDetail)) else j+1, resultTotal[j], charFormat=boldChars)


    def setTableData(self, cursor, personReportData, chkPersonOverall, chkPersonDetail, chkPersonDateDetail, chkMonthDetail, daysInMonthBeg, daysInMonthEnd, detailPersonDate, keyValToSort=None):
        firstPerson = True
        if chkPersonOverall:
            table = self._getPersonOverallTable(cursor, keyName=(((chkMonthDetail or chkPersonDateDetail) or chkPersonDateDetail) and chkPersonOverall))
        resultTotal = [0]*(len(self.table_columns)-1)
        for personKey, reportData in personReportData.items():
            if chkPersonDetail:
                cursor.movePosition(QtGui.QTextCursor.End)
                format = QtGui.QTextCharFormat()
                font = QtGui.QFont()
                font.setBold(True)
                font.setPointSize(13)
                format.setFont(font)
                cursor.setCharFormat(format)
                if firstPerson:
                    cursor.insertText(u'Врач: %s\n'%personKey[1])
                    firstPerson = False
                else:
                    cursor.insertText(u'\n\nВрач: %s\n'%personKey[1])
            if chkPersonOverall:
                firstPersonOverall = True
            else:
                table = self._getPersonTable(cursor, keyName=((chkMonthDetail or chkPersonDateDetail) and chkPersonOverall))
            if chkMonthDetail:
                result = [0]*(len(self.table_columns)-1)
                monthKeys = reportData.keys()
                if keyValToSort:
                    monthKeys.sort(key=keyValToSort)
                else:
                    monthKeys.sort()
                for monthKey in monthKeys:
                    values = reportData.get(monthKey, [0]*len(self.table_columns))
                    row = table.addRow()
                    for j, value in enumerate(values):
                        if chkPersonOverall:
                            if firstPersonOverall:
                                table.setText(row, 0, personKey[1])
                                mergeRow = row
                                mergeCol = len(reportData.keys())
                                firstPersonOverall = False
                            table.setText(row, j+1, value)
                        else:
                            table.setText(row, j, value)
                        if j:
                            result[j-1] += value
                            resultTotal[j-1] += value
                row = table.addRow()
                table.setText(row, 0, u'Итого:')
                for j in xrange(len(result)-1 if chkPersonOverall else len(result)):
                    table.setText(row, j+2 if chkPersonOverall else j+1, result[j])
                if chkPersonOverall:
                    table.mergeCells(mergeRow, 0, mergeCol, 1)
                    table.mergeCells(row, 0, 1, 2)
            else:
                result = [0]*(len(self.table_columns)-1)
                monthKeys = reportData.keys()
                if keyValToSort:
                    monthKeys.sort(key=keyValToSort)
                else:
                    monthKeys.sort()
                for monthKey in monthKeys:
                    values = reportData.get(monthKey, [0]*len(self.table_columns))

                    if detailPersonDate:
                        row = table.addRow()
                    for j, value in enumerate(values):
                        if detailPersonDate:
                            if chkPersonOverall:
                                if firstPersonOverall:
                                    table.setText(row, 0, personKey[1])
                                    mergeRow = row
                                    firstPersonOverall = False
                                table.setText(row, j+1, value)
                            else:
                                table.setText(row, j, value)
                        if j:
                            result[j-1] += value
                            resultTotal[j-1] += value
                row = table.addRow()
                if not detailPersonDate and chkPersonOverall:
                    table.setText(row, 0, personKey[1])
                elif detailPersonDate and chkPersonOverall:
                    table.setText(row, 1, u'Итого:')
                else:
                    table.setText(row, 0, u'Итого:')
                for j in xrange(len(result)-1 if (chkPersonOverall and detailPersonDate) else len(result)):
                    table.setText(row, j+2 if (chkPersonOverall and detailPersonDate) else j+1, result[j])

                if detailPersonDate and chkPersonOverall:
                    table.mergeCells(mergeRow, 0, daysInMonthEnd.day() + daysInMonthBeg.day() + 1, 1)

        if chkPersonOverall:
            row = table.addRow()
            table.setText(row, 0, u'Итого:')
            if detailPersonDate or chkMonthDetail:
                table.mergeCells(row, 0, 1, 2)
            for j in xrange(len(resultTotal)-1 if (chkPersonOverall and (detailPersonDate or chkMonthDetail)) else len(resultTotal)):
                table.setText(row, j+2 if (chkPersonOverall and (detailPersonDate or chkMonthDetail)) else j+1, resultTotal[j])


    def _getPersonOverallTable(self, cursor, col=0, keyName=False):
        cursor.movePosition(QtGui.QTextCursor.End)
        table = self.createTable(cursor)
        table.mergeCells(0, 0, 4, 1)
        if keyName:
            table.mergeCells(0, 1, 4, 1)

        table.mergeCells(0, 2 if keyName else 1, 4, 1)

        table.mergeCells(0, 3 if keyName else 2, 2, 2)
        table.mergeCells(2, 3 if keyName else 2, 2, 1)
        table.mergeCells(2, 4 if keyName else 3, 2, 1)

        table.mergeCells(0, 5 if keyName else 4, 1, 5)
        table.mergeCells(1, 5 if keyName else 4, 3, 1)
        table.mergeCells(1, 6 if keyName else 5, 1, 4)
        table.mergeCells(2, 6 if keyName else 5, 1, 2)
        table.mergeCells(2, 8 if keyName else 7, 1, 2)

        table.mergeCells(0, 10 if keyName else 9, 4, 1)

        table.mergeCells(0, 11 if keyName else 10, 4, 1)

        table.mergeCells(0, 12 if keyName else 11, 1, 3)
        table.mergeCells(1, 12 if keyName else 11, 1, 2)
        table.mergeCells(2, 12 if keyName else 11, 2, 1)
        table.mergeCells(2, 13 if keyName else 12, 2, 1)
        table.mergeCells(1, 14 if keyName else 13, 3, 1)

        table.mergeCells(0, 15 if keyName else 14, 1, 3)
        table.mergeCells(1, 15 if keyName else 14, 3, 1)
        table.mergeCells(1, 16 if keyName else 15, 3, 1)
        table.mergeCells(1, 17 if keyName else 16, 3, 1)

        table.mergeCells(0, 18 if keyName else 17, 4, 1)

        table.mergeCells(0, 19 if keyName else 18, 4, 1)

        table.mergeCells(0, 20 if keyName else 19, 1, 6)
        table.mergeCells(1, 20 if keyName else 19, 3, 1)
        table.mergeCells(1, 21 if keyName else 20, 3, 1)
        table.mergeCells(1, 22 if keyName else 21, 3, 1)
        table.mergeCells(1, 23 if keyName else 22, 1, 3)

        table.mergeCells(2, 23 if keyName else 22, 2, 1)
        table.mergeCells(2, 24 if keyName else 23, 2, 1)
        table.mergeCells(2, 25 if keyName else 24, 2, 1)
        table.mergeCells(0, 26 if keyName else 25, 4, 1)

        return table


    def _getPersonTable(self, cursor, keyName=False):
        cursor.movePosition(QtGui.QTextCursor.End)

        table = self.createTable(cursor)
        table.mergeCells(0, 0, 4, 1)
        if keyName:
            table.mergeCells(0, 1, 4, 1)

        table.mergeCells(0, 2 if keyName else 1, 4, 1)

        table.mergeCells(0, 3 if keyName else 2, 2, 2)
        table.mergeCells(2, 3 if keyName else 2, 2, 1)
        table.mergeCells(2, 4 if keyName else 3, 2, 1)

        table.mergeCells(0, 5 if keyName else 4, 1, 5)
        table.mergeCells(1, 5 if keyName else 4, 3, 1)
        table.mergeCells(1, 6 if keyName else 5, 1, 4)
        table.mergeCells(2, 6 if keyName else 5, 1, 2)
        table.mergeCells(2, 8 if keyName else 7, 1, 2)

        table.mergeCells(0, 10 if keyName else 9, 4, 1)

        table.mergeCells(0, 11 if keyName else 10, 4, 1)

        table.mergeCells(0, 12 if keyName else 11, 1, 3)
        table.mergeCells(1, 12 if keyName else 11, 1, 2)
        table.mergeCells(2, 12 if keyName else 11, 2, 1)
        table.mergeCells(2, 13 if keyName else 12, 2, 1)
        table.mergeCells(1, 14 if keyName else 13, 3, 1)

        table.mergeCells(0, 15 if keyName else 14, 1, 3)
        table.mergeCells(1, 15 if keyName else 14, 3, 1)
        table.mergeCells(1, 16 if keyName else 15, 3, 1)
        table.mergeCells(1, 17 if keyName else 16, 3, 1)

        table.mergeCells(0, 18 if keyName else 17, 4, 1)

        table.mergeCells(0, 19 if keyName else 18, 4, 1)

        table.mergeCells(0, 20 if keyName else 19, 1, 6)
        table.mergeCells(1, 20 if keyName else 19, 3, 1)
        table.mergeCells(1, 21 if keyName else 20, 3, 1)
        table.mergeCells(1, 22 if keyName else 21, 3, 1)
        table.mergeCells(1, 23 if keyName else 22, 1, 3)

        table.mergeCells(2, 23 if keyName else 22, 2, 1)
        table.mergeCells(2, 24 if keyName else 23, 2, 1)
        table.mergeCells(2, 25 if keyName else 24, 2, 1)
        table.mergeCells(0, 26 if keyName else 25, 4, 1)

        return table


class CStomatDayReport(CReportEx):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self._mapActionTypeId2ServiceIdList = {}
        self.setTitle(u'Листок ежедневного учета работы врача-стоматолога (форма 037/у)', u'Листок ежедневного учета работы врача-стоматолога (форма 037/у)')
        self.table_columns = [
            ('8%', [u'№ п/п', u'1'], CReportBase.AlignRight),
            ('8%', [u'Время приема пациента',  u'2'], CReportBase.AlignLeft),
            ('8%', [u'ФИО пациента', u'3'], CReportBase.AlignLeft),
            ('8%', [u'Год рождения', u'4'], CReportBase.AlignLeft),
            ('8%', [u'Адрес', u'5'], CReportBase.AlignLeft),
            ('8%', [u'Первично принятые', u'6'], CReportBase.AlignRight),
            ('8%', [u'В том числе дети', u'7'], CReportBase.AlignRight),
            ('8%', [u'Диагноз', u'8'], CReportBase.AlignLeft),
            ('12%',[u'Фактически выполненный объем работы', u'9'], CReportBase.AlignLeft),
            ('8%', [u'Санированные', u'10'], CReportBase.AlignRight),
            ('8%', [u'В т.ч. в плановом порядке', u'11'], CReportBase.AlignRight),
            ('8%', [u'УЕТ', u'12'], CReportBase.AlignRight),
            ]

    def getSetupDialog(self, parent):
        result = CReportSetupDialog(parent)
        result.setTitle(self.title())
        result.setOrgStructureVisible(True)
        result.setPersonVisible(True)
        result.setFinanceVisible(False)
        result.setSpecialityVisible(False)
        result.setInsurerVisible(False)
        result.setStageVisible(False)
        result.setPayPeriodVisible(False)

        # заменяем подходящий комбобокс:
        result.setWorkTypeVisible(True)
        result.lblWorkType.setText(u'Адрес: ')
        result.cmbAddressType = result.cmbWorkType
        result.cmbAddressType.setMaxCount(0) # а как его еще очистить???
        result.cmbAddressType.setMaxCount(2)
        result.cmbAddressType.addItem(u'регистрации')
        result.cmbAddressType.addItem(u'проживания')
        result.params = lambda : dict(CReportSetupDialog.params(result).items() + [('addressType', result.cmbWorkType.currentIndex())])

        result.setOwnershipVisible(False)
        result.setWorkOrganisationVisible(False)
        result.setSexVisible(False)
        result.setAgeVisible(False)
        result.setActionTypeVisible(False)
        result.setMKBFilterVisible(False)
        result.setEventTypeVisible(False)
        result.lblBegDate.setText(u'Дата')
        result.lblEndDate.hide()
        result.edtEndDate.hide()
        result.lblEventType.hide()
        result.cmbEventType.hide()
        result.chkOnlyPermanentAttach.hide()
        result.chkDetailPerson.hide()
        return result


    def getPeriodName(self, params):
        date = params.get('begDate', QDate.currentDate())
        params['endDate'] = date
        return date.toString(u"dd.MM.yyyy")


    def getSelectFunction(self, params = None):
        return selectDayDataStomat


    def _getActionTypeServiceIdList(self, act):
        actionTypeId = act.typeId
        financeId = act._financeId
        if actionTypeId:
            result = self._mapActionTypeId2ServiceIdList.get((actionTypeId, financeId), None)
            if result is None:
                db = QtGui.qApp.db
                table = db.table('ActionType_Service')
                if financeId:
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
                self._mapActionTypeId2ServiceIdList[actionTypeId] = result
            return result
        return None


    def _getActionTypeServiceId(self, act):
        result = self._getActionTypeServiceIdList(act)
        return forceRef(result[0]) if result else None


    def getReportData(self, query, addressType):
        reportData = {}
        context = CInfoContext()
        i = 0
        eventIdList = []
        while query.next():
            record = query.record()
            date = forceDateTime(record.value('date'))
            eventId = forceRef(record.value('eventId'))
            actionId = forceRef(record.value('actionId'))
#            stomatId = forceRef(record.value('actionStomatId'))
            event = context.getInstance(CTeethEventInfo, eventId)
            action = event.stomatAction #context.getInstance(CStomatActionInfo, stomatId)
            reportLine = reportData.get((event.client.shortName, event.client.id), [0, '', '', '', '', 0, 0, '', 0, 0, 0, 0, '', ''])
            if (event.client.shortName, event.client.id) not in reportData.keys():
                i += 1
            reportLine[0] = i
            reportLine[1] = date.toString("hh:mm")
            reportLine[2] = event.client.shortName
            reportLine[3] = event.client.birthDate
            if eventId not in eventIdList:
                reportLine[5] += (1 if event.isPrimary else 0)
                reportLine[6] += (1 if (event.isPrimary and event.client.ageTuple[3] < 15) else 0)
                eventIdList.append(eventId)
            if len(event.diagnosises) > 0 and reportLine[7] != event.diagnosises[0].MKB.code:
                reportLine[7] += u'\n'.join([event.diagnosises[0].MKB.code])
            reportLine[9] += int(action.isSanitationDone())
            reportLine[10] += int(action.isSanitationDone() and event.order == 1)
            uetList = []
            actAmount = 0
            eventActAmountThroughCode = {}
            for act in event.actions:
                if actionId == act._id:
                    serviceId = self._getActionTypeServiceId(act)
                    if act.uet:
                        if serviceId and act.amount:
                            actAmountThroughCode = eventActAmountThroughCode.setdefault(act.typeId, [act.code, 0])
                            actAmountThroughCode[1] += act.amount
                        uetList.append(act.uet)
                        actAmount += act.amount
                    else:
                        uet = 0
                        db = QtGui.qApp.db
                        tableContractTariff = db.table('Contract_Tariff')
                        contractId = event.contract.id
                        if serviceId and contractId:
                            record = db.getRecordEx(tableContractTariff, [tableContractTariff['uet']], [tableContractTariff['deleted'].eq(0),
                                                                                                        tableContractTariff['master_id'].eq(contractId),
                                                                                                        tableContractTariff['service_id'].eq(serviceId)])
                            if record:
                                uet = forceDouble(record.value('uet'))
                                if uet:
                                    actAmount += act.amount
                                    if serviceId and act.amount:
                                        actAmountThroughCode = eventActAmountThroughCode.setdefault(act.typeId, [act.code, 0])
                                        actAmountThroughCode[1] += act.amount
                        uetList.append(act.amount*uet)
            reportLine[8] += actAmount
            reportLine[11] += round(sum([amount_uet for amount_uet in uetList]), 2)
            reportLine[12] = (event.client.regAddress, event.client.locAddress)
            value = u''
            for actValues in eventActAmountThroughCode.values():
                value = u'\n'.join([value, actValues[0]+': %.2f'%actValues[1]])
            reportLine[13] += value
            reportLine[4] = reportLine[12][addressType]
            reportData[(event.client.shortName, event.client.id)] = reportLine
        return reportData


    def buildInt(self, params, cursor):
        date = params.get('begDate', QDate.currentDate())
        orgStructureId = params.get('orgStructureId', None)
        personId = params.get('personId', None)
        locality = params.get('locality', 0)
        addressType = params.get('addressType', 0)
        selectFunction = self.getSelectFunction()
        query = selectFunction(date, orgStructureId, personId, locality=locality, reportType=1)
        reportData = self.getReportData(query, addressType)
        table = self.createTable(cursor)
        self.fillTable(table, reportData)
        return reportData


    def fillTable(self, table, reportData):
        total = [0]*14
        keysList = reportData.keys()
        keysList.sort()
        cnt = 1
        for key in keysList:
            reportLine = reportData[key]
            rows = len(reportLine)
            if rows > 0:
                cols = min(table.colCount(), len(reportLine))
                rowNum = table.addRow()
                table.setText(rowNum, 0, cnt)
                cnt += 1
                for j in xrange(1, cols):
                    if j == 8:
                        value = reportLine[13]
                    else:
                        value = unicode(reportLine[j])
                    table.setText(rowNum, j, value)
                    if j in [5, 6, 8, 9, 10, 11]:
                        total[j] += reportLine[j]
        tableRow = table.addRow()
        table.setText(tableRow, 0, u'Итого:')
        for col in [5, 6, 8, 9, 10, 11]:
            if col == 11 or col == 8:
                table.setText(tableRow, col, total[col])
            else:
                table.setText(tableRow, col, "%d"%total[col])

