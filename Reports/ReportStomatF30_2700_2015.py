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

from PyQt4 import QtGui
from PyQt4.QtCore import QDate

from library.database   import addDateInRange
#from library.PrintInfo  import CInfoContext
from library.Utils      import forceBool, forceDouble, forceInt, forceRef, forceString

from Events.ActionServiceType   import CActionServiceType

from Orgs.Utils                 import getOrgStructurePersonIdList
from Reports.Report             import CReport, CReportEx, selectMonthData

from Reports.ReportBase         import CReportBase
from Reports.ReportMonthActions import CSetupReportMonthActions
from Reports.Utils              import dateRangeAsStr, getKladrClientRural

monthsInYear = 12

MainRows = [(u'Всего',                                  u'1'),
            (u'в том числе: стоматологами',             u'2'),
            (u'зубными врачами',                        u'3'),
            (u'гигиенистами стоматологическими',        u'4'),
            (u'из них дети:  до 14 лет (включительно)', u'5'),
            (u'15-17 лет (включительно)',               u'6'),
            (u'Сельские жители',                        u'7'),
            (u'В передвижных стоматологических кабинетах',u'8')
           ]


def selectData(db, begDate, endDate, orgStructureId, personId, sex, ageFrom, ageTo):
    stmt= u"""
        SELECT
            Event.id as `eventId`,
            Event.execDate as `date`,
            Event.isPrimary as `isPrimary`,
            StomatAction.id as `actionStomatId`,
            ParodentAction.id as `actionParodentId`,
            Contract.finance_id as `contractFinanceId`,
            StomatAction.finance_id as `stomatActionFinanceId`,
            ParodentAction.finance_id as `parodentActionFinanceId`

        FROM
            Event
            LEFT JOIN Client ON Client.id = Event.client_id
            LEFT JOIN Contract ON Contract.id = Event.contract_id
            LEFT JOIN EventType ON EventType.id = Event.eventType_id,
            Action AS StomatAction
            LEFT JOIN ActionType AS StomatActionType ON StomatAction.actionType_id = StomatActionType.id,
            Action AS ParodentAction
            LEFT JOIN ActionType AS ParodentActionType ON ParodentAction.actionType_id = ParodentActionType.id
        WHERE
            Event.deleted = 0
            AND EventType.form = '043'
            AND StomatAction.deleted = 0
            AND ParodentAction.deleted = 0
            AND StomatAction.event_id = Event.id
            AND ParodentAction.event_id = Event.id
            AND StomatActionType.flatCode = 'dentitionInspection'
            AND ParodentActionType.flatCode = 'parodentInsp'
            AND %s
    """
    tableEvent = db.table('Event')
    tableActionStomat = db.table('Action').alias('StomatAction')
    cond = []
    addDateInRange(cond, tableEvent['execDate'], begDate, endDate)
    if orgStructureId:
        persons = getOrgStructurePersonIdList(orgStructureId)
        cond.append(tableActionStomat['person_id'].inlist(persons))
    if personId:
        cond.append(tableActionStomat['person_id'].eq(personId))
    if sex:
        cond.append(db.table('Client')['sex'].eq(sex))
    if ageFrom:
        cond.append('age(Client.birthDate, Event.setDate) >= %d'%ageFrom)
    if ageTo is not None:
        cond.append('age(Client.birthDate, Event.setDate) <= %d'%ageTo)
    return db.query(stmt % (db.joinAnd(cond)))


def selectDayDataStomat(date, orgStructureId, personId):
    db = QtGui.qApp.db
    return selectData(db, date, date, orgStructureId, personId, None, None, None)

def selectMonthDataStomat(date, orgStructureId, personId, sex, ageFrom, ageTo):
    return selectMonthData(selectData, date, orgStructureId, personId, sex, ageFrom, ageTo)

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

def hasAnyCondition(info, where, number, names):
    return any(hasCondition(info, where, number, name) for name in names)

def getNumber(info, where, number):
    return int(getProp(info, (u'Верх', u'Низ')[where], where, number))

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

    queryTable = tableAction
    queryTable = queryTable.leftJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
    queryTable = queryTable.leftJoin(tablePerson, tablePerson['id'].eq(tableAction['person_id']))
    queryTable = queryTable.leftJoin(tableActionProperty, [tableActionProperty['action_id'].eq(tableAction['id']),
                                                           tableActionType['flatCode'].like('dentitionInspection...')])
    queryTable = queryTable.leftJoin(tableActionPropertyType, [tableActionPropertyType['id'].eq(tableActionProperty['type_id']),
                                                               tableActionPropertyType['actionType_id'].eq(tableActionType['id'])])
    queryTable = queryTable.leftJoin(tableActionPropertyString, tableActionPropertyString['id'].eq(tableActionProperty['id']))
    queryTable = queryTable.leftJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
    queryTable = queryTable.leftJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
    queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))

    cond = [tableEvent['execDate'].ge(begDate),
            tableEvent['execDate'].lt(endDate.addDays(1)),
            tableEvent['deleted'].eq(0),
            tableAction['deleted'].eq(0),
            tableActionType['deleted'].eq(0),
            'EXISTS (SELECT DentAct.`id` FROM Action AS DentAct LEFT JOIN ActionType AS DentActType ON DentActType.`id`=DentAct.`actionType_id` WHERE DentAct.`event_id`=Event.`id` AND DentActType.`flatCode` LIKE \'dentitionInspection%\' AND DentAct.`deleted`=0 AND DentActType.`deleted`=0)'
           ]

    if personId:
        cond.append(tableAction['person_id'].eq(personId))
    elif orgStructureId:
        persons = getOrgStructurePersonIdList(orgStructureId)
        cond.append(tableAction['person_id'].inlist(persons))
    if sex is not None:
        cond.append(tableClient['sex'].eq(sex+1))
    if ageFrom:
        cond.append('age(Client.`birthDate`, Event.`setDate`) >= %d'%ageFrom)
    if ageTo is not None:
        cond.append('age(Client.`birthDate`, Event.`setDate`) <= %d'%ageTo)
    if financeId:
        cond.append('(Action.`finance_id`=%d) OR (Action.`finance_id` IS NULL AND Contract.`id`=%d)'%(financeId, financeId))

    fields = [tableEvent['id'].alias('eventId'),
              tableEvent['execDate'].alias('eventExecDate'),
              tableAction['id'].alias('actionId'),
              tableAction['finance_id'].alias('actionFinanceId'),
              tableAction['uet'].alias('actionUet'),
              tableAction['amount'].alias('actionAmount'),
              tableActionType['flatCode'].name(),
              tableActionType['serviceType'].name(),
              tableActionType['id'].alias('actionTypeId'),
              tableActionProperty['id'].alias('actionPropertyId'),
              tableActionPropertyType['name'].alias('propertyName'),
              tableActionPropertyString['value'].alias('propertyValue'),
              tableEvent['isPrimary'].name(),
              tableEvent['contract_id'].alias('contractId'),
              'age(Client.`birthDate`, Event.`setDate`) AS clientAge',
              tablePerson['id'].alias('personId'),
              tablePerson['name'].alias('personName')]
    fields.append(u'%s AS clientRural'%(getKladrClientRural()))
    fields.append(u'''EXISTS(SELECT rbSpeciality.id FROM rbSpeciality INNER JOIN Person ON Person.speciality_id = rbSpeciality.id WHERE rbSpeciality.name LIKE '%стоматолог%' AND Person.deleted = 0 AND Person.id = vrbPersonWithSpeciality.id) AS stomatSpeciality''')
    fields.append(u'''EXISTS(SELECT rbPost.id FROM rbPost INNER JOIN Person ON Person.post_id = rbPost.id WHERE rbPost.code LIKE '1%' OR rbPost.code LIKE '2%' OR rbPost.code LIKE '3%' AND Person.deleted = 0 AND Person.id = vrbPersonWithSpeciality.id) AS stomatPost''')
    fields.append(u'''EXISTS(SELECT rbSpeciality.id FROM rbSpeciality INNER JOIN Person ON Person.speciality_id = rbSpeciality.id WHERE rbSpeciality.name LIKE '%гигиенист стоматолог%' AND Person.deleted = 0 AND Person.id = vrbPersonWithSpeciality.id) AS stomatSpecialityGigienist''')
    fields.append(u'''EXISTS(SELECT Visit.id FROM Visit INNER JOIN rbScene ON rbScene.id = Visit.scene_id WHERE Visit.event_id = Event.id AND Visit.deleted = 0 AND rbScene.code = 4) AS codeScene''')
    stmt = db.selectStmt(queryTable, fields, cond)
    return db.query(stmt)


class CReportStomatF30_2700_2015(CReportEx):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Ф.30(2700). 6. Работа стоматологического (зубоврачебного) кабинета', u'Ф.30(2700). 6. Работа стоматологического (зубоврачебного) кабинета')
        self.table_columns = self.getTableColumns()
        self._mapActionUet = {}


    def getTableColumns(self):
        return [
            ('22%', [u'Контингенты', '', u'1'], CReportBase.AlignLeft),
            ('3%', [u'№ строки', '', u'2'], CReportBase.AlignRight),
            ('5%', [u'Число посещений стоматологов и зубных врачей', u'Всего', u'3'], CReportBase.AlignRight),
            ('5%', [u'', u'в том числе первичных', u'4'], CReportBase.AlignRight),
            ('5%', [u'Вылечено зубов', u'', u'5'], CReportBase.AlignRight),
            ('5%', [u'из них постоянных', u'', u'6'], CReportBase.AlignRight),
            ('5%', [u'по поводу осложнен-ного кариеса(из гр.5)', u'', u'7'], CReportBase.AlignRight),
            ('5%', [u'Удалено зубов', u'', u'8'], CReportBase.AlignRight),
            ('5%', [u'из них постоянных', u'', u'9'], CReportBase.AlignRight),
            ('5%', [u'Всего санировано', u'', u'10'], CReportBase.AlignRight),
            ('5%', [u'Профилактическая работа', u'осмотрено в порядке плановой санации', u'11'], CReportBase.AlignRight),
            ('5%', [u'', u'из числа осмотренных нуждались в санации', u'12'], CReportBase.AlignRight),
            ('5%', [u'', u'санировано из числа нуждавшихся в санации', u'13'], CReportBase.AlignRight),
            ('5%', [u'Проведен курс профилактики', u'', u'14'], CReportBase.AlignRight),
            ('5%', [u'Из общего числа (гр. 3) – посещений по ОМС', u'', u'15'], CReportBase.AlignRight),
            ('5%', [u'Выполнен объем работы в УЕТ(тыс.)(из гр.3)', u'', u'16'], CReportBase.AlignRight),
            ('5%', [u'Выполнен объем работы в УЕТ (тыс.) по ОМС (из гр.15)', u'', u'17'], CReportBase.AlignRight),
            ]


    def getSetupDialog(self, parent):
        result = CSetupReportMonthActions(parent)
        result.setTitle(self.title())
        result.setActionTypeClassVisible(False)
        result.setActionTypeGroupVisible(False)
        result.setStatusVisible(False)
        result.setAssistantVisible(False)
        result.setTissueTypeVisible(False)
        result.setPersonDetailVisible(False)
        return result


    def getPeriodName(self, params):
        begDate = params.get('begDate', QDate.currentDate())
        endDate = params.get('endDate', QDate.currentDate())
        return dateRangeAsStr(u' период', begDate, endDate)


    def getSelectFunction(self, params = None):
        return selectMonthDataStomat


    def _getNewPersonReportData(self, daysInMonth):
        return [[dayIdx+1]+([0]*(len(self.table_columns)-1)) for dayIdx in xrange(daysInMonth)]


    def getReportData(self, query, daysInMonth):
        personReportData = {}
        eventIdList = []
        actionIdList = []
        day2Values = {}

        db = QtGui.qApp.db
        tableRBFinance = db.table('rbFinance')
        omsFinanceId = forceRef(db.translate(tableRBFinance, 'code', 2, 'id', ))

        for cnt in xrange(8):
            day2Values[cnt] = {'eventCount':0,
                               'isPrimary':0,
                               'eventCountOMS':0,
                               'prophylaxis':0,
                               'uet':0.0,
                               'uetOMS':0.0}
        while query.next():
            record = query.record()
            eventId = forceRef(record.value('eventId'))
            actionId = forceRef(record.value('actionId'))
            actionFinanceId = forceRef(record.value('actionFinanceId'))
            clientAge = forceInt(record.value('clientAge'))
            stomatSpeciality = forceBool(record.value('stomatSpeciality'))
            stomatPost = forceBool(record.value('stomatPost'))
            stomatSpecialityGigienist = forceBool(record.value('stomatSpecialityGigienist'))
            codeScene = forceBool(record.value('codeScene'))
            clientRural = forceBool(record.value('clientRural'))
            propertyName = forceString(record.value('propertyName'))
            propertyValue = forceString(record.value('propertyValue'))
            isPrimary = forceInt(record.value('isPrimary')) == 1
            serviceType = forceInt(record.value('serviceType'))
            actionUet = forceDouble(record.value('actionUet'))
            cntList = []
            if stomatSpeciality and stomatPost:
                cntList.append(1)
            if stomatSpeciality and not stomatPost:
                cntList.append(2)
            if stomatSpecialityGigienist:
                cntList.append(3)
            if clientAge <= 14:
                cntList.append(4)
            if clientAge > 14 and clientAge <= 17:
                cntList.append(5)
            if clientRural:
                cntList.append(6)
            if codeScene:
                cntList.append(7)
            for cnt in cntList:
                dayValues = day2Values.setdefault(cnt, {'eventCount':0,
                                                        'isPrimary':0,
                                                        'eventCountOMS':0,
                                                        'prophylaxis':0,
                                                        'uet':0.0,
                                                        'uetOMS':0.0})
                if u'dentitionInspection' in forceString(record.value('flatCode')):
                    actionValues = dayValues.setdefault(actionId, {})
                    actionValues[propertyName] = propertyValue

                if eventId not in eventIdList:
                    dayValues['eventCount'] += 1
                    dayValues['eventCountOMS'] += omsFinanceId == actionFinanceId
                    dayValues['isPrimary'] += isPrimary

                if actionId not in actionIdList:
                    dayValues['prophylaxis'] += serviceType == CActionServiceType.prophylaxis
                    dayValues['uet'] += actionUet
                    dayValues['uetOMS'] += actionUet if omsFinanceId == actionFinanceId else 0

            dayTotalValues = day2Values.setdefault(0, {'eventCount':0,
                                                    'isPrimary':0,
                                                    'eventCountOMS':0,
                                                    'prophylaxis':0,
                                                    'uet':0.0,
                                                    'uetOMS':0.0})
            if u'dentitionInspection' in forceString(record.value('flatCode')):
                actionValues = dayTotalValues.setdefault(actionId, {})
                actionValues[propertyName] = propertyValue

            if eventId not in eventIdList:
                dayTotalValues['eventCount'] += 1
                dayTotalValues['eventCountOMS'] += omsFinanceId == actionFinanceId
                dayTotalValues['isPrimary'] += isPrimary
                eventIdList.append(eventId)

            if actionId not in actionIdList:
                dayTotalValues['prophylaxis'] += serviceType == CActionServiceType.prophylaxis
                dayTotalValues['uet'] += actionUet
                dayTotalValues['uetOMS'] += actionUet if omsFinanceId == actionFinanceId else 0
                actionIdList.append(actionId)

        for personKey, dayValues in day2Values.items():
            reportData = personReportData.setdefault(personKey, [0]*16)
            if not dayValues:
                continue

            rl                = reportData
            rl[1]             = dayValues.pop('eventCount')
            rl[2]             = dayValues.pop('isPrimary')
            rl[12]            = dayValues.pop('prophylaxis')
            rl[13]            = dayValues.pop('eventCountOMS')
            rl[14]            = dayValues.pop('uet')
            rl[15]            = dayValues.pop('uetOMS')

            for actionValues in dayValues.values():
                rl[3]  += len([k for k in xrange(16) if getStatus(actionValues, 0, k+1) in (5, 6, 7)])
                rl[3]  += len([k for k in xrange(16) if getStatus(actionValues, 1, k+1) in (5, 6, 7)])
                rl[4]  += len([k for k in xrange(16) if getStatus(actionValues, 0, k+1) == 5
                                                    and hasCondition(actionValues, 0, k+1, u"П/С")
                                                    and getNumber(actionValues, 0, k+1) <= 48])
                rl[4]  += len([k for k in xrange(16) if getStatus(actionValues, 1, k+1) == 5
                                                    and hasCondition(actionValues, 1, k+1, u"П/С")
                                                    and getNumber(actionValues, 1, k+1) <= 48])
                rl[4]  += len([k for k in xrange(16) if getStatus(actionValues, 0, k+1) in (6, 7)
                                                    and hasAnyCondition(actionValues, 0, k+1, (u"П/С", u"C", u"P", u"Pt", u"R"))
                                                    and getNumber(actionValues, 0, k+1) <= 48])
                rl[4]  += len([k for k in xrange(16) if getStatus(actionValues, 1, k+1) in (6, 7)
                                                    and hasAnyCondition(actionValues, 1, k+1, (u"П/С", u"C", u"P", u"Pt", u"R"))
                                                    and getNumber(actionValues, 1, k+1) <= 48])
                rl[5]  += len([k for k in xrange(16) if getStatus(actionValues, 0, k+1) == 6
                                                    and hasAnyCondition(actionValues, 0, k+1, (u"П/С", u"C", u"P", u"Pt", u"R"))])
                rl[5]  += len([k for k in xrange(16) if getStatus(actionValues, 1, k+1) == 6
                                                    and hasAnyCondition(actionValues, 1, k+1, (u"П/С", u"C", u"P", u"Pt", u"R"))])
                rl[6] += len([k for k in xrange(16) if getStatus(actionValues, 0, k+1) == 9
                                                    and getNumber(actionValues, 0, k+1) >= 50])
                rl[6] += len([k for k in xrange(16) if getStatus(actionValues, 1, k+1) == 9
                                                    and getNumber(actionValues, 1, k+1) >= 50])
                rl[6] += len([k for k in xrange(16) if getStatus(actionValues, 0, k+1) == 9
                                                    and hasCondition(actionValues, 0, k+1, u"A")
                                                    and getNumber(actionValues, 0, k+1) <= 48])
                rl[6] += len([k for k in xrange(16) if getStatus(actionValues, 1, k+1) == 9
                                                    and hasCondition(actionValues, 1, k+1, u"A")
                                                    and getNumber(actionValues, 1, k+1) <= 48])
                rl[6] += len([k for k in xrange(16) if getStatus(actionValues, 0, k+1) == 9
                                                    and getNumber(actionValues, 0, k+1) <= 48])
                rl[6] += len([k for k in xrange(16) if getStatus(actionValues, 1, k+1) == 9
                                                    and getNumber(actionValues, 1, k+1) <= 48])
                rl[7] += len([k for k in xrange(16) if getStatus(actionValues, 0, k+1) == 9
                                                    and getNumber(actionValues, 0, k+1) <= 48])
                rl[7] += len([k for k in xrange(16) if getStatus(actionValues, 1, k+1) == 9
                                                    and getNumber(actionValues, 1, k+1) <= 48])
                rl[8] += isSanitationDone(actionValues)
                rl[9] += isSanitationPlanned(actionValues)
                rl[10] += isSanitationNeed(actionValues)
                rl[11] += isSanitationPlanned(actionValues) and isSanitationDone(actionValues)

        return personReportData


    def buildInt(self, params, cursor):
        query = selectData2(params)
        daysInMonth = 4
        personReportData = self.getReportData(query, daysInMonth)

        table = self._getPersonTable(cursor)
        for personKey, reportData in personReportData.items():
            i = table.addRow()
            table.setText(i, 0, MainRows[personKey][0])
            table.setText(i, 1, MainRows[personKey][1])
            for j in xrange(len(reportData)-1):
                table.setText(i, j+2, reportData[j+1])


    def _getPersonTable(self, cursor):
        cursor.movePosition(QtGui.QTextCursor.End)
        table = self.createTable(cursor)
        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 2, 1)
        table.mergeCells(0, 2, 1, 2)
        table.mergeCells(0, 4, 2, 1)
        table.mergeCells(0, 5, 2, 1)
        table.mergeCells(0, 6, 2, 1)
        table.mergeCells(0, 7, 2, 1)
        table.mergeCells(0, 8, 2, 1)
        table.mergeCells(0, 9, 2, 1)
        table.mergeCells(0, 10, 1, 3)
        table.mergeCells(0, 13, 2, 1)
        table.mergeCells(0, 14, 2, 1)
        table.mergeCells(0, 15, 2, 1)
        table.mergeCells(0, 16, 2, 1)
        return table

