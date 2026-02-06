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
from PyQt4.QtCore import QDate, QString

from library.Utils             import forceInt, forceRef, forceString, lastYearDay, trim
from Reports.Report            import CReport
from Reports.ReportBase        import CReportBase, createTable
from Reports.ReportSetupDialog import CReportSetupDialog
from Reports.Utils             import getAgeClass
from Orgs.Utils                import getOrgStructurePersonIdList

def getInterviewActionTypeIdList():
    db = QtGui.qApp.db
    table = db.table('rbService')
    cond = db.joinOr([table['code'].eq(u'FR'),
                      table['code'].eq(u'А25.12.004*'),
                     ]
                    )
    return db.getIdList(table, 'id', cond)


def selectData(params):
    begDate = params.get('begDate', QDate())
    endDate = params.get('endDate', QDate())
    orgStructureId = params.get('orgStructureId', None)
    db = QtGui.qApp.db
    tableEvent = db.table('Event')
    tableAction = db.table('Action')
    tableActionType = db.table('ActionType')
    tableActionProperty = db.table('ActionProperty')
    tableActionPropertyType = db.table('ActionPropertyType')
    tableActionPropertyString = db.table('ActionProperty_String')
    tableMES = db.table('mes.MES')
    tableMESGroup = db.table('mes.mrbMESGroup')
    tableClient = db.table('Client')
    tableRBService = db.table('rbService')
    queryTable = tableEvent
    queryTable = queryTable.innerJoin(tableMES, tableMES['id'].eq(tableEvent['MES_id']))
    queryTable = queryTable.innerJoin(tableMESGroup, tableMESGroup['id'].eq(tableMES['group_id']))
    queryTable = queryTable.innerJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
    queryTable = queryTable.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
    queryTable = queryTable.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
    queryTable = queryTable.leftJoin(tableRBService, db.joinAnd([tableRBService['id'].eq(tableActionType['nomenclativeService_id']),
                                                                  tableRBService['id'].inlist(getInterviewActionTypeIdList())]))
    queryTable = queryTable.innerJoin(tableActionProperty, tableActionProperty['action_id'].eq(tableAction['id']))
    queryTable = queryTable.innerJoin(tableActionPropertyType, tableActionPropertyType['id'].eq(tableActionProperty['type_id']))
    queryTable = queryTable.innerJoin(tableActionPropertyString, tableActionPropertyString['id'].eq(tableActionProperty['id']))
    cond = [tableEvent['deleted'].eq(0),
            tableEvent['execDate'].ge(begDate),
            tableEvent['execDate'].lt(endDate.addDays(1)),
            tableActionType['deleted'].eq(0),
            tableMESGroup['code'].eq(u'ДиспанС'),
            db.joinOr([tableMES['endDate'].isNull(), tableMES['endDate'].ge(begDate)]),
            tableAction['deleted'].eq(0),
            tableActionProperty['deleted'].eq(0),
            tableActionPropertyType['deleted'].eq(0)
            ]
    mesDispansIdList = params.get('mesDispansIdList', [])
    if mesDispansIdList:
        cond.append(tableEvent['MES_id'].inlist(mesDispansIdList))
    if orgStructureId:
        cond.append(tableEvent['execPerson_id'].inlist(getOrgStructurePersonIdList(orgStructureId)))
    cond.append(u'''rbService.id IS NOT NULL OR ActionType.code = 'FR' ''')
    fields = [tableEvent['id'].alias('eventId'),
              'age(Client.`birthDate`, %s) AS clientAge' % db.formatDate(lastYearDay(endDate)),
              'age(Client.birthDate, Action.endDate) AS ageClientProperty',
              tableClient['sex'].alias('clientSex'),
              tableClient['id'].alias('clientId'),
              tableActionPropertyType['name'].alias('propertyName'),
              tableActionPropertyType['descr'].alias('propertyDescr'),
              tableActionPropertyString['value'].alias('propertyValue')
             ]
    fields.append(u'''IF(rbService.id IS NOT NULL, rbService.code, ActionType.code) AS serviceCode''')
    stmt = db.selectStmt(queryTable, fields, cond, tableEvent['id'].name())
    return db.query(stmt)


class CReportForm131_o_4000_2016(CReport):

    rows = (
        # 0
        (u'Повышенный уровень артериального давления (Повышенное кровяное давление при отсутствии диагноза гипертензии).',
          '1',
          'R03.0'),
        # 1
        (u'Гипергликемия неуточненная (Повышенное содержание глюкозы в крови)',
          '2',
          'R73.9'),
        # 2
        (u'Избыточная масса тела (Анормальная прибавка массы тела)',
          '3',
          'R63.5'),
        # 3
        (u'Курение табака (Употребление табака)',
          '4',
          'Z72.0'),
        # 4
        (u'Риск пагубного потребления алкоголя (Употребление алкоголя)',
          '5',
          'Z72.1'),
        # 5
        (u'Риск потребления наркотических средств и психотропных веществ без назначения врача (Употребление наркотиков)',
          '6',
          'Z72.2'),
        # 6
        (u'Низкая физическая активность (Недостаток физической активности)',
          '7',
          'Z72.3'),
        # 7
        (u'Нерациональное питание (Неприемлемая диета и вредные привычки питания)',
          '8',
          'Z72.4'),
        # 8
        (u'Отягощенная наследственность по злокачественным новообразованиям (в семейном анамнезе злокачественное новообразование)Z80, Oтягощенная наследственность по сердечно-сосудистым заболеваниям (в семейном анамнезе инсульт)Z82.3, Oтягощенная наследственность по сердечно-сосудистым заболеваниям (в семейном анамнезе ишемическая болезнь сердца и другие болезни сердечно-сосудистой системы)Z82.4, Oтягощенная наследственность по хроническим болезням нижних дыхательных путей (в семейном анамнезе астма и другие хронические болезни нижних дыхательных путей)Z82.5, Oтягощенная наследственность по сахарному диабету (в семейном анамнезе сахарный диабет)Z83.3.',
          '9',
          'Z80, Z82.3, Z82.4, Z82.5, Z83.3',
        ),
        # 9
        (u'Высокий абсолютный суммарный сердечно-сосудистый риск',
          '10',
          ''),
        # 10
        (u'Очень высокий абсолютный суммарный сердечно-сосудистый риск',
          '11',
          '')
        )


    mapCardioRiskToRow = {
                           u'высокий'     : 9,
                           u'очень высокий': 10,
                         }


    mapRow9 = [u'9.1', u'9.1', u'9.2', u'9.3', u'9.4', u'9.5']


    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Сведения о выявленных отдельных факторах риска развития хронических неинфекционных заболеваний, не являющихся заболеваниями,  в соответствии с кодами МКБ-10 (2016)')


    def getSetupDialog(self, parent):
        result = CReportSetupDialog(parent)
        result.setEventTypeVisible(False)
        result.setMesDispansListVisible(True)
        result.setOnlyPermanentAttachVisible(False)
        result.setOrgStructureVisible(True)
        result.setTitle(self.title())
        return result


    def getReportData(self, query):
        clientIdAndRowSet = set()
        reportData = [ [0]*12
                       for row in xrange(len(self.rows))
                     ]
        commonColumn = 8
        while query.next():
            record = query.record()
            serviceCode = forceString(record.value('serviceCode'))
#            propertyName  = forceString(record.value('propertyName'))
            propertyDescr = forceString(record.value('propertyDescr'))
            propertyValue = forceString(record.value('propertyValue'))
            clientId  = forceRef(record.value('clientId'))
            clientAge = forceInt(record.value('clientAge'))
            clientSex = forceInt(record.value('clientSex'))
            ageClientProperty = forceInt(record.value('ageClientProperty'))
            baseColumn = 0 if clientSex == 1 else 4
            targetRow = None
            # определить строки, в которые попадают данные этого action
            if serviceCode == u'А25.12.004*':
                propertyDescrStr = trim(forceString(record.value('propertyDescr')))
                propertyDescr = int(propertyDescrStr) if propertyDescrStr else None
                if propertyDescr == 2 and ageClientProperty >= 40:
                    propertyValue = trim(forceString(record.value('propertyValue'))).lower()
                    targetRow = self.mapCardioRiskToRow.get(propertyValue, None)
            elif serviceCode == u'FR':
                propertyValue = trim(forceString(record.value('propertyValue'))).lower()
                propertyDescrStr = trim(forceString(record.value('propertyDescr')))
                if propertyDescrStr in self.mapRow9:
                    propertyDescr = 9
                else:
                    propertyDescr = int(QString(propertyDescrStr).toFloat()[0])
                targetRow = (propertyDescr - 1) if (propertyDescr and u'да' == propertyValue) else None
            if targetRow is not None or targetRow >= 0:
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
            ( '22%', [u'Факторы риска (наименование по МКБ-10)', u'', u'1'], CReportBase.AlignLeft),
            ( '3%',  [u'№ строки', u'', u'2'], CReportBase.AlignRight),
            ( '15%', [u'Код МКБ-10', u'', u'3'], CReportBase.AlignLeft),
            ( '5%',  [u'Мужчины', u'18 – 36 лет', u'4'], CReportBase.AlignRight),
            ( '5%',  [u'', u'39 – 60 лет', u'5'], CReportBase.AlignRight),
            ( '5%',  [u'', u'Старше 60 лет', u'6'], CReportBase.AlignRight),
            ( '5%',  [u'', u'Всего', u'7'], CReportBase.AlignRight),
            ( '5%',  [u'Женщины', u'18 – 36 лет', u'8'], CReportBase.AlignRight),
            ( '5%',  [u'', u'39 – 60 лет', u'9'], CReportBase.AlignRight),
            ( '5%',  [u'', u'Старше 60 лет', u'10'], CReportBase.AlignRight),
            ( '5%',  [u'', u'Всего', u'11'], CReportBase.AlignRight),
            ( '5%',  [u'Всего', u'18 – 36 лет', u'12'], CReportBase.AlignRight),
            ( '5%',  [u'', u'39 – 60 лет', u'13'], CReportBase.AlignRight),
            ( '5%',  [u'', u'Старше 60 лет', u'14'], CReportBase.AlignRight),
            ( '5%',  [u'', u'Всего', u'15'], CReportBase.AlignRight)
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

