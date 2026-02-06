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

import re

from PyQt4 import QtGui
from PyQt4.QtCore import QDate

from library.Utils             import forceInt, forceRef, forceString, lastYearDay

from Reports.Report            import CReport, normalizeMKB
from Reports.ReportBase        import CReportBase, createTable
from Reports.ReportSetupDialog import CReportSetupDialog
from Reports.Utils             import getAgeClass
from Orgs.Utils                import getOrgStructurePersonIdList


def getInterviewActionTypeIdList():
    db = QtGui.qApp.db
    table = db.table('rbService')
    cond = db.joinOr([table['code'].eq(u'A01.31.024*'),
                      table['code'].regexp(u'^A02.07.004([^0-9]|$)'),
                      table['code'].regexp(u'^A02.12.002([^0-9]|$)'),
                      table['code'].regexp(u'^A09.05.023([^0-9]|$)'),
                      table['code'].eq(u'A25.12.004*'),
                      table['code'].regexp(u'^В03.016.04([^0-9]|$)'),
                      ]
                     )
    return db.getIdList(table, 'id', cond)


def selectData(params):
    begDate = params.get('begDate', QDate())
    endDate = params.get('endDate', QDate())
    orgStructureId = params.get('orgStructureId', None)
    db = QtGui.qApp.db
    tableEvent = db.table('Event')
    tableEventType = db.table('EventType')
    tableRbEventProfile = db.table('rbEventProfile')
    tableAction = db.table('Action')
    tableActionType = db.table('ActionType')
    tableActionProperty = db.table('ActionProperty')
    tableActionPropertyType = db.table('ActionPropertyType')
    tableActionPropertyString = db.table('ActionProperty_String')
    tableActionPropertyInteger = db.table('ActionProperty_Integer')
    tableClient = db.table('Client')
    tableRBService = db.table('rbService')
    queryTable = tableEvent
    queryTable = queryTable.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
    queryTable = queryTable.leftJoin(tableRbEventProfile, tableRbEventProfile['id'].eq(tableEventType['eventProfile_id']))
    queryTable = queryTable.leftJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
    queryTable = queryTable.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
    queryTable = queryTable.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
    queryTable = queryTable.innerJoin(tableRBService, tableRBService['id'].eq(tableActionType['nomenclativeService_id']))
    queryTable = queryTable.leftJoin(tableActionProperty, tableActionProperty['action_id'].eq(tableAction['id']))
    queryTable = queryTable.leftJoin(tableActionPropertyType, tableActionPropertyType['id'].eq(tableActionProperty['type_id']))
    queryTable = queryTable.leftJoin(tableActionPropertyString, tableActionPropertyString['id'].eq(tableActionProperty['id']))
    queryTable = queryTable.leftJoin(tableActionPropertyInteger, tableActionPropertyInteger['id'].eq(tableActionProperty['id']))
    cond = [tableEvent['deleted'].eq(0),
            tableEvent['execDate'].ge(begDate),
            tableEvent['execDate'].lt(endDate.addDays(1)),
            tableActionType['deleted'].eq(0),
            tableRbEventProfile['regionalCode'].inlist(['8008', '8009']),
            tableAction['deleted'].eq(0),
            tableActionType['nomenclativeService_id'].inlist(getInterviewActionTypeIdList())
            ]
    if orgStructureId:
        cond.append(tableEvent['execPerson_id'].inlist(getOrgStructurePersonIdList(orgStructureId)))
    fields = [tableEvent['id'].alias('eventId'),
              'age(Client.`birthDate`, %s) AS clientAge' % db.formatDate(lastYearDay(endDate)),
              tableClient['sex'].alias('clientSex'),
              tableClient['id'].alias('clientId'),
              tableRBService['code'].alias('serviceCode'),
              tableActionPropertyType['name'].alias('propertyName'),
              tableActionPropertyType['descr'].alias('propertyDescr'),
              tableActionPropertyString['value'].alias('propertyValue'),
              tableActionPropertyInteger['value'].alias('integerPropertyValue'),
              tableActionProperty['evaluation'].alias('propertyEvaluation'),
              tableAction['MKB']
              ]
    stmt = db.selectStmt(queryTable, fields, cond, tableEvent['id'].name())
    return db.query(stmt)


class CReportForm131_o_4000_2015(CReport):

    rows = (
        # 0
        (u'Повышенный уровень артериального давления (Повышенное кровяное давление при отсутствии диагноза гипертензии) ',
            '01',
            'R03.0'),
        # 1
        (u'Гипергликемия неуточненная (Повышенное содержание глюкозы в крови) ',
            '02',
            'R73.9'),
        # 2
        (u'Избыточная масса тела (Анормальная прибавка массы тела)',
            '03',
            'R63.5'),
        # 3
        (u'Курение табака (Употребление табака)',
            '04',
            'Z72.0'),
        # 4
        (u'Риск пагубного потребления алкоголя (Употребление алкоголя)',
            '05',
            'Z72.1'),
        # 5
        (u'Риск потребления наркотических средств и психотропных веществ без назначения врача (Употребление наркотиков)',
            '06',
            'Z72.2'),
        # 6
        (u'Низкая физическая активность (Недостаток физической активности) ',
            '07',
            'Z72.3'),
        # 7
        (u'Нерациональное питание (Неприемлемая диета и вредные привычки питания)',
            '08',
            'Z72.4'),
        # 8
        (u'Отягощенная наследственность по злокачественным новообразованиям (в семейном анамнезе злокачественное новообразование)',
            '09.1',
            'Z80',
         ),
        # 9
        (u'Oтягощенная наследственность по сердечно-сосудистым заболеваниям (в семейном анамнезе инсульт)',
            '09.2',
            'Z82.3'),

        # 10
        (u'Oтягощенная наследственность по сердечно-сосудистым заболеваниям (в семейном анамнезе ишемическая болезнь сердца и другие болезни сердечно-сосудистой системы)',
            '09.3',
            'Z82.4'),
        # 11
        (u'Oтягощенная наследственность по хроническим болезням нижних дыхательных путей (в семейном анамнезе астма и другие хронические болезни нижних дыхательных путей)',
            '09.4',
            'Z82.5'),
        # 12
        (u'Oтягощенная наследственность по сахарному диабету (в семейном анамнезе сахарный диабет)',
            '09.5',
            'Z83.3'),
        # 13
        (u'Высокий абсолютный суммарный сердечно-сосудистый риск',
            '10',
            ''),
        # 14
        (u'Очень высокий абсолютный суммарный сердечно-сосудистый риск',
            '11',
            '')
        )

    mapInterviewQuestionToRow = {
        ('1.',  u'да'): 0,
        ('5.',  u'да'): 1,
        ('26.', u'да'): 3,
        ('27.', u'да'): 4,
        ('28.', u'да'): 4,
        ('29.', u'да'): 4,
        ('30.', u'да'): 4,
        ('39.', u'да'): 5,
        ('31.', u'до 30 мин'): 6,
        ('32.', u'нет'): 7,
        ('33.', u'нет'): 7,
        ('34.', u'да'):  7,
        ('35.', u'да'):  7,
        ('12.', u'да'):  8,
        ('11.', u'да'):  9,
        ('10.', u'да'): 10,
        ('11.1.', u'да'): 11,
        ('11.2.', u'да'): 12,
        }

    mapCardioRiskToRow = { (5.0,  10.0)   : 13,
                           (10.0, 1000.0) : 14,
                           u'ВЫСОКИЙ'     : 13,
                           u'ОЧЕНЬВЫСОКИЙ': 14,
                         }


    mapServiceCodeAndPropertyDescrToRow = {
        (u'A02.12.002', None): 0,
        (u'A09.05.023', None): 1,
        (u'A02.07.004', None): 2,
        (u'A02.07.004', u'имт'): 2,
        (u'B03.016.04', None): 1,
        }

    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Сведения о выявленных отдельных факторах риска развития хронических неинфекционных заболеваний, не являющихся заболеваниями,  в соответствии с кодами МКБ-10')

    def getSetupDialog(self, parent):
        result = CReportSetupDialog(parent)
        result.setEventTypeVisible(False)
        result.setOnlyPermanentAttachVisible(False)
        result.setOrgStructureVisible(True)
        result.setTitle(self.title())
        return result

    def dispathInterview(self, propertyName, propertyDescr, propertyValue):
        # propertyName - строки типа
        #  '1. Повышенное АД'
        #  '10.Инфаркт миокарда у родственников'
        #  '11.1 Отягощенная наследственность по ...'
        # выделяем номер вопроса
        m = re.match(r'^\s*([\d.]+)', propertyDescr)
        if m is None:
            m = re.match(r'^\s*([\d.]+)', propertyName)
        if m is not None:
            questionNumber = m.group()
            if not questionNumber.endswith('.'):  # и нормализуем
                questionNumber += '.'
            reportRowNumber = self.mapInterviewQuestionToRow.get((questionNumber, propertyValue.lower()))
        else:
            reportRowNumber = None
        return reportRowNumber

    def dispathCardioRisk(self, propertyDescr, propertyValue):
        if propertyDescr == '2':
            for val, reportRowNumber in self.mapCardioRiskToRow.iteritems():
                if ( val == propertyValue
                     or type(val) == tuple and val[0] <= propertyValue <= val[1]
                   ):
                    return reportRowNumber
        return None

    def dispathCustomActions(self, serviceCode, mkb, propertyDescr, evaluation):
        serviceCode = serviceCode[:10]
        reportRowNumber = self.mapServiceCodeAndPropertyDescrToRow.get((serviceCode, propertyDescr.lower()))
        if reportRowNumber is None:
            reportRowNumber = self.mapServiceCodeAndPropertyDescrToRow.get((serviceCode, None))
        if reportRowNumber is not None and (('A00' <= mkb < 'U00') or evaluation != 0):
            return reportRowNumber
        else:
            return None

    def getReportData(self, query):
        clientIdAndRowSet = set()
        reportData = [[0]*12 for row in xrange(len(self.rows))]
        commonColumn = 8

        while query.next():
            record = query.record()
            serviceCode = forceString(record.value('serviceCode'))
            propertyName = forceString(record.value('propertyName'))
            propertyDescr = forceString(record.value('propertyDescr'))
            propertyValue = forceString(record.value('propertyValue'))
            clientId = forceRef(record.value('clientId'))
            clientAge = forceInt(record.value('clientAge'))
            clientSex = forceInt(record.value('clientSex'))
            baseColumn = 0 if clientSex == 1 else 4

            # определить строки, в которые попадают данные этого action
            if serviceCode == u'A01.31.024*':
                # это - опрос
                targetRow = self.dispathInterview(propertyName, propertyDescr, propertyValue)
            elif serviceCode == u'A25.12.004*':
                propertyValue = (    forceInt(record.value('integerPropertyValue'))
                                  or propertyValue.replace(' ', '').upper()
                                )
                targetRow = self.dispathCardioRisk(propertyDescr, propertyValue)
            else:
                MKB = normalizeMKB(forceString(record.value('MKB')))
                propertyEvaluation = forceInt(record.value('propertyEvaluation'))
                targetRow = self.dispathCustomActions(serviceCode, MKB, propertyDescr, propertyEvaluation)

            if targetRow is not None:
                ageColumn = getAgeClass(clientAge)
                if ageColumn is not None:
                    key = (clientId, targetRow)
                    if key not in clientIdAndRowSet:
                        clientIdAndRowSet.add(key)
                        reportLine = reportData[targetRow]
                        reportLine[baseColumn + ageColumn] += 1
                        reportLine[baseColumn + 3] += 1
                        reportLine[commonColumn + ageColumn] += 1
                        reportLine[commonColumn + 3] += 1
        return reportData

    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        cursor.insertText(u'(4000)')
        cursor.insertBlock()
        tableColumns = [
            ('22%', [u'Фактора риска (наименование по МКБ-10)', u'', u'1'], CReportBase.AlignLeft),
            ('3%',  [u'№ строки', u'', u'2'], CReportBase.AlignRight),
            ('15%', [u'Код МКБ-10', u'', u'3'], CReportBase.AlignRight),
            ( '5%',  [u'Мужчины', u'18 – 36 лет', u'4'], CReportBase.AlignRight),
            ('5%',  [u'', u'39 – 60 лет', u'5'], CReportBase.AlignRight),
            ('5%',  [u'', u'Старше 60 лет', u'6'], CReportBase.AlignRight),
            ('5%',  [u'', u'Всего', u'7'], CReportBase.AlignRight),
            ( '5%',  [u'Женщины', u'18 – 36 лет', u'8'], CReportBase.AlignRight),
            ('5%',  [u'', u'39 – 60 лет', u'9'], CReportBase.AlignRight),
            ('5%',  [u'', u'Старше 60 лет', u'10'], CReportBase.AlignRight),
            ('5%',  [u'', u'Всего', u'11'], CReportBase.AlignRight),
            ( '5%',  [u'Всего', u'18 – 36 лет', u'12'], CReportBase.AlignRight),
            ('5%',  [u'', u'39 – 60 лет', u'13'], CReportBase.AlignRight),
            ('5%',  [u'', u'Старше 60 лет', u'14'], CReportBase.AlignRight),
            ('5%',  [u'', u'Всего', u'15'], CReportBase.AlignRight)
            ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 2, 1)
        table.mergeCells(0, 2, 2, 1)
        table.mergeCells(0, 3, 1, 4)
        table.mergeCells(0, 7, 1, 4)
        table.mergeCells(0, 11, 1, 4)
        query = selectData(params)
        reportData = self.getReportData(query)
        for row, reportLine in enumerate(reportData):
            i = table.addRow()
            table.setText(i, 0, self.rows[row][0])
            table.setText(i, 1, self.rows[row][1])
            table.setText(i, 2, self.rows[row][2])
            for idx, value in enumerate(reportLine):
                table.setText(i, idx+3, value)
        return doc
