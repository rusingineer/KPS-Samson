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

from PyQt4        import QtGui

from library.Utils        import forceInt, forceString
from Reports.Report       import CReport
from Reports.ReportBase   import CReportBase, createTable
from Reports.Utils        import dateRangeAsStr
from Orgs.Utils           import getOrganisationInfo

from DeathReportByZones   import CDeathReportByZonesSetupDialog


def getAgeKey(ageValue):
    return {
        60 <= ageValue <= 64: '60-64',
        65 <= ageValue <= 69: '65-69',
        70 <= ageValue <= 74: '70-74',
        75 <= ageValue <= 79: '75-79',
        80 <= ageValue <= 84: '80-84',
              ageValue >= 85: '85+'
    }[True]



def selectData(params):
    reportData = {  '60-64': {'low':{'M':0, 'F': 0}, 'mid':{'M':0, 'F': 0}, 'high':{'M':0, 'F': 0}},
                    '65-69': {'low':{'M':0, 'F': 0}, 'mid':{'M':0, 'F': 0}, 'high':{'M':0, 'F': 0}},
                    '70-74': {'low':{'M':0, 'F': 0}, 'mid':{'M':0, 'F': 0}, 'high':{'M':0, 'F': 0}},
                    '75-79': {'low':{'M':0, 'F': 0}, 'mid':{'M':0, 'F': 0}, 'high':{'M':0, 'F': 0}},
                    '80-84': {'low':{'M':0, 'F': 0}, 'mid':{'M':0, 'F': 0}, 'high':{'M':0, 'F': 0}},
                    '85+':   {'low':{'M':0, 'F': 0}, 'mid':{'M':0, 'F': 0}, 'high':{'M':0, 'F': 0}},
                 }  # M - male, F - female
    sentForConsultation = {'60-64':0, '65-69':0, '70-74':0, '75-79':0, '80-84':0, '85+':0}
    sentToHospital = {'60-64':0, '65-69':0, '70-74':0, '75-79':0, '80-84':0, '85+':0}

    db = QtGui.qApp.db
    tableEvent       = db.table('Event')
    tableClient      = db.table('Client')
    tablePerson      = db.table('Person')
    tableAction      = db.table('Action')
    tableActionType  = db.table('ActionType')
    tableActionProperty  = db.table('ActionProperty')
    tablePropertyType    = db.table('ActionPropertyType')
    tablePropertyString  = db.table('ActionProperty_String')

    queryTable = tableEvent
    queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
    queryTable = queryTable.innerJoin(tablePerson, tableEvent['execPerson_id'].eq(tablePerson['id']))
    queryTable = queryTable.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
    queryTable = queryTable.innerJoin(tableActionType, tableAction['actionType_id'].eq(tableActionType['id']))
    queryTable = queryTable.innerJoin(tableActionProperty, tableActionProperty['action_id'].eq(tableAction['id']))
    queryTable = queryTable.innerJoin(tablePropertyType, tableActionProperty['type_id'].eq(tablePropertyType['id']))
    queryTable = queryTable.innerJoin(tablePropertyString, tableActionProperty['id'].eq(tablePropertyString['id']))

    cols = [ tablePropertyString['value'].alias('result'),
             tableClient['sex'],
             'age(Client.birthDate, Action.begDate) AS `age`',
           ]
    cond = [ tableEvent['deleted'].eq(0),
             tableClient['deleted'].eq(0),
             tablePerson['deleted'].eq(0),
             tableAction['deleted'].eq(0),
             tableActionType['deleted'].eq(0),
             tableActionProperty['deleted'].eq(0),
             tableAction['status'].eq(2),
             tableEvent['org_id'].eq(QtGui.qApp.currentOrgId()),
             tableActionType['flatCode'].eq('asthenia'),
             tableAction['endDate'].ge(params['begDate']),
             tableAction['endDate'].lt(params['endDate'].addDays(1)),
             tablePropertyType['name'].inlist([u'Заключение', u'Направление']),
             'age(Client.birthDate, Action.begDate) >= 60'
           ]

    # if params['orgStructureId'] != None:
        # cond.append(tablePerson['orgStructure_id'].inlist(params['orgStructureIdList']))

    stmt = db.selectStmt(queryTable, cols, cond)
    query = db.query(stmt)
    while query.next():
        record = query.record()
        result = forceString(record.value('result')).lower()
        clientAge = forceInt(record.value('age'))
        clientSex = 'M' if forceInt(record.value('sex')) == 1 else 'F'

        ageKey = getAgeKey(clientAge)

        if result.startswith(u'нет'):
            reportData[ageKey]['low'][clientSex] += 1

        elif u'преастения' in result:
            reportData[ageKey]['mid'][clientSex] += 1

        elif u'астения' in result:
            reportData[ageKey]['high'][clientSex] += 1

        elif result == u'направлен на консультацию ко врачу-гериатру(1)':
            sentForConsultation[ageKey] += 1

        elif result == u'направлен в гериатрический стационар(2)':
            sentToHospital[ageKey] += 1

    return reportData, sentForConsultation, sentToHospital



class CReportAstheniaResults(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Отчет о результатах проведения скрининга старческой астении')


    def getSetupDialog(self, parent):
        result = CDeathReportByZonesSetupDialog(parent)
        result.setTitle(self.title())
        return result


    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setBlockFormat(CReportBase.AlignCenter)
        cursor.setCharFormat(CReportBase.ReportBody)

        orgId = QtGui.qApp.currentOrgId()
        orgInfo = getOrganisationInfo(orgId)
        orgName = orgInfo.get('shortName', u'ЛПУ в настройках не указано!')

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Отчет\nо результатах проведения скрининга старческой астении при использовании опросника "Возраст не помеха"\n')
        cursor.insertBlock()
        cursor.insertText(u'Наименование ЛПУ: %s\n' % orgName)
        cursor.insertText(dateRangeAsStr(u'за период', params['begDate'], params['endDate']))
        cursor.insertBlock()
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)

        alignLeft = CReportBase.AlignLeft
        alignRight = CReportBase.AlignRight
        charBold = QtGui.QTextCharFormat()
        charBold.setFontWeight(QtGui.QFont.Bold)

        tableColumns = [ ('8%',  [u'Возраст', ''], alignLeft),
                         ('6%',  [u'нет астении\n(0-2 балла)', u'Всего'], alignLeft),
                         ('6%',  ['', u'Мужчин'], alignLeft),
                         ('6%',  ['', u'Женщин'], alignLeft),
                         ('6%',  [u'Преастения\n(3-4 балла)', u'Всего'], alignLeft),
                         ('6%',  ['', u'Мужчин'], alignLeft),
                         ('6%',  ['', u'Женщин'], alignLeft),
                         ('6%',  [u'Старческая астения\n(5 баллов и более)', u'Всего'], alignLeft),
                         ('6%',  ['', u'Мужчин'], alignLeft),
                         ('6%',  ['', u'Женщин'], alignLeft),
                         ('6%',  [u'ВСЕГО', u'Всего'], alignLeft),
                         ('6%',  ['', u'Мужчин'], alignLeft),
                         ('6%',  ['', u'Женщин'], alignLeft),
                         ('10%', [u'Направлено на консультацию к врачу-гериатру', ''], alignLeft),
                         ('10%', [u'Направлено в гериатрический стационар, в том числе для проведения комплексной гериатрической оценки', ''], alignLeft)
                       ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 1, 3)
        table.mergeCells(0, 4, 1, 3)
        table.mergeCells(0, 7, 1, 3)
        table.mergeCells(0, 10, 1, 3)
        table.mergeCells(0, 13, 2, 1)
        table.mergeCells(0, 14, 2, 1)


        reportData, sentForConsultation, sentToHospital = selectData(params)
        totalForAstheniaPoints = {'low':{'M':0, 'F': 0}, 'mid':{'M':0, 'F': 0}, 'high':{'M':0, 'F': 0}, 'all':{'M':0, 'F':0}}

        for ageKey in ('60-64', '65-69', '70-74', '75-79', '80-84', '85+'):
            row = table.addRow()
            totalForConcreteAges = {'M': 0, 'F': 0}
            table.setText(row, 0, ageKey if ageKey != '85+' else u'85 и старше')

            for i, astheniaKey in enumerate(('low', 'mid', 'high')):
                data = reportData[ageKey][astheniaKey]
                table.setText(row, 3*i+1, data['M'] + data['F'], blockFormat=alignRight)
                table.setText(row, 3*i+2, data['M'], blockFormat=alignRight)
                table.setText(row, 3*i+3, data['F'], blockFormat=alignRight)
                totalForConcreteAges['M'] += data['M']
                totalForConcreteAges['F'] += data['F']
                totalForAstheniaPoints[astheniaKey]['M'] += data['M']
                totalForAstheniaPoints[astheniaKey]['F'] += data['F']

            table.setText(row, 10, totalForConcreteAges['M'] + totalForConcreteAges['F'], blockFormat=alignRight)
            table.setText(row, 11, totalForConcreteAges['M'], blockFormat=alignRight)
            table.setText(row, 12, totalForConcreteAges['F'], blockFormat=alignRight)
            table.setText(row, 13, sentForConsultation[ageKey], blockFormat=alignRight)
            table.setText(row, 14, sentToHospital[ageKey], blockFormat=alignRight)
            totalForAstheniaPoints['all']['M'] += totalForConcreteAges['M']
            totalForAstheniaPoints['all']['F'] += totalForConcreteAges['F']

        row = table.addRow()
        table.setText(row, 0, u'ВСЕГО:')
        for i, astheniaKey in enumerate(('low', 'mid', 'high', 'all')):
            table.setText(row, 3*i+1, totalForAstheniaPoints[astheniaKey]['M'] + totalForAstheniaPoints[astheniaKey]['F'], blockFormat=alignRight)
            table.setText(row, 3*i+2, totalForAstheniaPoints[astheniaKey]['M'], blockFormat=alignRight)
            table.setText(row, 3*i+3, totalForAstheniaPoints[astheniaKey]['F'], blockFormat=alignRight)
        table.setText(row, 13, sum(sentForConsultation.values()), blockFormat=alignRight)
        table.setText(row, 14, sum(sentToHospital.values()), blockFormat=alignRight)

        return doc
