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
from PyQt4.QtCore import QDate

from library.Utils              import (forceInt, forceString, forceDouble,
                                        formatName, forceBool)
from Events.Utils               import getActionTypeIdListByFlatCode
from Orgs.Utils                 import getOrgStructurePersonIdList
from Reports.ReportBase         import CReportBase, createTable
from Reports.Report             import CReport, CReportEx
from Reports.Utils              import getStringPropertyCurrEvent

from Reports.ReportStomatF39_3  import CSetupReportStomatF39_3


def selectData(params):
    begDate = params.get('begDate', QDate())
    endDate = params.get('endDate', QDate())
    orgStructureId = params.get('orgStructureId', None)
    personId = params.get('personId', None)
    sex = params.get('sex', 0)
    ageFrom = params.get('ageFrom', None)
    ageTo = params.get('ageTo', None)

    db = QtGui.qApp.db
    tablePerson = db.table('Person')
    tableRBSpeciality = db.table('rbSpeciality')
    tableEvent = db.table('Event')
    tableClient = db.table('Client')
    tableRBMedicalAidType = db.table('rbMedicalAidType')
    tableEventType = db.table('EventType')

    queryTable = tableEvent.innerJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
    queryTable = queryTable.innerJoin(tablePerson, tablePerson['id'].eq(tableEvent['execPerson_id']))
    queryTable = queryTable.innerJoin(tableRBSpeciality, tableRBSpeciality['id'].eq(tablePerson['speciality_id']))
    queryTable = queryTable.innerJoin(tableRBMedicalAidType, tableRBMedicalAidType['id'].eq(tableEventType['medicalAidType_id']))
    queryTable = queryTable.innerJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))

    cond = [tableEvent['execDate'].ge(begDate),
            tableEvent['execDate'].lt(endDate.addDays(1)),
            tableRBMedicalAidType['code'].like(u'9'),
            tableRBSpeciality['federalCode'].like(u'140101'),
            tableEventType['deleted'].eq(0),
            tablePerson['deleted'].eq(0),
            tableEvent['deleted'].eq(0)
           ]

    cols = [tablePerson['id'].alias('personId'),
            tablePerson['firstName'].alias('personFirstName'),
            tablePerson['lastName'].alias('personLastName'),
            tablePerson['patrName'].alias('personPatrName'),
            tableEvent['isPrimary'],
           ]

    cols.append('age(Client.birthDate, DATE(Event.setDate)) AS clientAge')

    cols.append('''(SELECT COUNT(DISTINCT Visit.id)
                    FROM Visit
                    WHERE Visit.event_id = Event.id AND Visit.deleted = 0) AS visitCount''')

    cols.append('''(SELECT COUNT(Action.id)
                    FROM Action
                      JOIN ActionType ON Action.actionType_id = ActionType.id
                    WHERE Action.event_id = Event.id
                      AND Action.deleted = 0
                      AND ActionType.deleted = 0
                      AND ActionType.serviceType = 7
                    ) AS prophylaxisCount''')

    cols.append('(SELECT SUM(uet) FROM Action WHERE event_id = Event.id AND deleted = 0) AS uet')

    cols.append('''(SELECT SUM(TIME_TO_SEC(Schedule.doneTime)/60)
                    FROM Schedule
                    WHERE Schedule.person_id = Event.execPerson_id
                    AND DATE(Schedule.date) >= DATE(Event.setDate)
                    AND DATE(Schedule.date) <= DATE(Event.execDate)
                    AND Schedule.deleted = 0
                    ) AS countDoneMinutes''')

    actionTypeIdList = set(getActionTypeIdListByFlatCode(u'dentitionInspection')) | set(getActionTypeIdListByFlatCode(u'parodentInsp'))
    cols.append(getStringPropertyCurrEvent(actionTypeIdList, u'Аппарат') + u' AS apparatProp')
    cols.append(getStringPropertyCurrEvent(actionTypeIdList, u'Протезы') + u' AS protezesProp')
    cols.append(getStringPropertyCurrEvent(actionTypeIdList, u'Ортодонтическое лечение') + u' AS ortodontProp')

    if personId:
        cond.append(tableEvent['execPerson_id'].eq(personId))
    elif orgStructureId:
        personIdList = getOrgStructurePersonIdList(orgStructureId)
        if personIdList:
            cond.append(tableEvent['execPerson_id'].inlist(personIdList))
    if sex:
        cond.append(tableClient['sex'].eq(sex))
    if ageFrom is not None:
        cond.append('age(Client.`birthDate`, Event.`setDate`) >= %d' % ageFrom)
    if ageTo is not None:
        cond.append('age(Client.`birthDate`, Event.`setDate`) <= %d' % ageTo)

    stmt = db.selectStmt(queryTable, cols, cond)
    query = db.query(stmt)
    while query.next():
        yield query.record()



class CReportStomatSummary(CReportEx):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Сводная ведомость')


    def getSetupDialog(self, parent):
        result = CSetupReportStomatF39_3(parent)
        result.setTitle(self.title())
        return result


    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Сводная ведомость учета работы врачей-ортодонтов')
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        tableColumns = [
            ('4%', [u'', u'Таб. №', u'1'], CReportBase.AlignRight),
            ('4%', [u'', u'ФИО врача', u'2'], CReportBase.AlignLeft),
            ('4%', [u'', u'Кол-во рабочих часов', u'3'], CReportBase.AlignRight),
            ('4%', [u'', u'Посещений', u'4'], CReportBase.AlignRight),
            ('4%', [u'Принято первичных больных', u'Всего', u'5'], CReportBase.AlignRight),
            ('4%', [u'', u'в т.ч. детей', u'6'], CReportBase.AlignRight),
            ('4%', [u'Взято на лечение аномалий', u'Всего', u'7'], CReportBase.AlignRight),
            ('4%', [u'', u'зубов', u'8'], CReportBase.AlignRight),
            ('4%', [u'', u'рядов', u'9'], CReportBase.AlignRight),
            ('4%', [u'', u'прикуса', u'10'], CReportBase.AlignRight),
            ('4%', [u'', u'др. аномалий ЧЛО', u'11'], CReportBase.AlignRight),
            ('4%', [u'Сделано ортодонтических аппаратов', u'съемных', u'12'], CReportBase.AlignRight),
            ('4%', [u'', u'несъемных', u'13'], CReportBase.AlignRight),
            ('4%', [u'Сдано протезов', u'съемных', u'14'], CReportBase.AlignRight),
            ('4%', [u'', u'несъемных', u'15'], CReportBase.AlignRight),
            ('4%', [u'Закончило лечение', u'дошкольники', u'16'], CReportBase.AlignRight),
            ('4%', [u'', u'школьники', u'17'], CReportBase.AlignRight),
            ('4%', [u'', u'взрослые', u'18'], CReportBase.AlignRight),
            ('4%', [u'', u'всего', u'19'], CReportBase.AlignRight),
            ('4%', [u'', u'Профилактическая работа', u'20'], CReportBase.AlignRight),
            ('4%', [u'', u'Выполнено УЕТ', u'21'], CReportBase.AlignRight),
            ('4%', [u'Нагрузка на день', u'посещений', u'22'], CReportBase.AlignRight),
            ('4%', [u'', u'УЕТ', u'23'], CReportBase.AlignRight),
            ('4%', [u'', u'Закончило лечение, %', u'24'], CReportBase.AlignRight),
            ('4%', [u'', u'СПО', u'25'], CReportBase.AlignRight),
            ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0,0,  2,1)
        table.mergeCells(0,1,  2,1)
        table.mergeCells(0,2,  2,1)
        table.mergeCells(0,3,  2,1)
        table.mergeCells(0,19, 2,1)
        table.mergeCells(0,20, 2,1)

        table.mergeCells(0,4,  1,2)
        table.mergeCells(0,6,  1,5)
        table.mergeCells(0,11, 1,2)
        table.mergeCells(0,13, 1,2)
        table.mergeCells(0,15, 1,4)
        table.mergeCells(0,21, 1,4)

        reportData = {}
        for record in selectData(params):
            personId = forceInt(record.value('personId'))
            firstName = forceString(record.value('personFirstName'))
            lastName = forceString(record.value('personLastName'))
            patrName = forceString(record.value('personPatrName'))
            countDoneMinutes = forceInt(record.value('countDoneMinutes'))
            visitCount = forceInt(record.value('visitCount'))
            clientAge = forceInt(record.value('clientAge'))
            isPrimary = forceBool(record.value('isPrimary'))
            apparatProp = forceString(record.value('apparatProp')).lower()
            protezesProp = forceString(record.value('protezesProp')).lower()
            ortodontProp = forceString(record.value('ortodontProp')).lower()
            prophylaxisCount = forceInt(record.value('prophylaxisCount'))
            uet = forceDouble(record.value('uet'))

            data = reportData.setdefault(personId, {
                    'personName': formatName(lastName, firstName, patrName),
                    'countDoneMinutes': 0,
                    'visitCount': 0,
                    'primaryCount': 0,
                    'primaryChildrenCount': 0,
                    'anomalyTeeth': 0,
                    'anomalyTeethRow': 0,
                    'anomalyBite': 0,
                    'anomalyOthers': 0,
                    'apparatRemovableCount': 0,
                    'apparatNonRemovableCount': 0,
                    'protezesRemovableCount': 0,
                    'protezesNonRemovableCount': 0,
                    'finishedPreschoolers': 0,
                    'finishedSchoolers': 0,
                    'finishedAdults': 0,
                    'prophylaxisCount': 0,
                    'uet': 0.0,
                })

            if isPrimary:
                data['primaryCount'] += 1
                if clientAge <= 14:
                    data['primaryChildrenCount'] += 1

            data['countDoneMinutes'] += countDoneMinutes
            data['visitCount'] += visitCount
            data['prophylaxisCount'] += prophylaxisCount
            data['uet'] += uet

            if u'несъемн' in apparatProp:
                data['apparatNonRemovableCount'] += 1
            elif u'съемн' in apparatProp:
                data['apparatRemovableCount'] += 1

            if u'несъемн' in protezesProp:
                data['protezesRemovableCount'] += 1
            elif u'съемн' in protezesProp:
                data['protezesNonRemovableCount'] += 1

            if u'отдельных зубов' in ortodontProp:
                data['anomalyTeeth'] += 1
            elif u'зубных рядов' in ortodontProp:
                data['anomalyTeethRow'] += 1
            elif u'прикуса' in ortodontProp:
                data['anomalyBite'] += 1
            elif u'аномал' in ortodontProp:
                data['anomalyOthers'] += 1

            if u'закончено' in ortodontProp:
                if clientAge < 7:
                    data['finishedPreschoolers'] += 1
                elif 7 <= clientAge < 18:
                    data['finishedSchoolers'] += 1
                else:
                    data['finishedAdults'] += 1


        daysInPeriod = params['begDate'].daysTo(params['endDate'])
        for personId, data in reportData.items():
            visitCount = data['visitCount']
            anomalyTotal = data['anomalyTeeth']+data['anomalyTeethRow']+data['anomalyBite']+data['anomalyOthers']
            totalFinished = data['finishedPreschoolers']+data['finishedSchoolers']+data['finishedAdults']

            row = table.addRow()
            table.setText(row, 0,  personId)
            table.setText(row, 1,  data['personName'])
            table.setText(row, 2,  '%d:%d'%(data['countDoneMinutes']/60, data['countDoneMinutes']%60))
            table.setText(row, 3,  visitCount)
            table.setText(row, 4,  data['primaryCount'])
            table.setText(row, 5,  data['primaryChildrenCount'])

            table.setText(row, 6,  anomalyTotal)
            table.setText(row, 7,  data['anomalyTeeth'])
            table.setText(row, 8,  data['anomalyTeethRow'])
            table.setText(row, 9,  data['anomalyBite'])
            table.setText(row, 10, data['anomalyOthers'])

            table.setText(row, 11, data['apparatRemovableCount'])
            table.setText(row, 12, data['apparatNonRemovableCount'])
            table.setText(row, 13, data['protezesRemovableCount'])
            table.setText(row, 14, data['protezesNonRemovableCount'])

            table.setText(row, 15, data['finishedPreschoolers'])
            table.setText(row, 16, data['finishedSchoolers'])
            table.setText(row, 17, data['finishedAdults'])
            table.setText(row, 18, totalFinished)

            table.setText(row, 19, data['prophylaxisCount'])
            table.setText(row, 20, data['uet'])
            table.setText(row, 21, round(visitCount / float(daysInPeriod), 2))
            table.setText(row, 22, round(data['uet'] / float(daysInPeriod), 2))
            if visitCount != 0:
                table.setText(row, 23, (totalFinished / visitCount) * 100)
            else:
                table.setText(row, 23, 0)
            table.setText(row, 24, visitCount)

        return doc
