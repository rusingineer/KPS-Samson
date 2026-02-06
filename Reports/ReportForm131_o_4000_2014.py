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
from PyQt4.QtCore import QDate

from library.Utils             import forceInt, forceRef, forceString, trim

from Reports.Report            import CReport
from Reports.ReportBase        import CReportBase, createTable
from Reports.ReportSetupDialog import CReportSetupDialog
from Orgs.Utils                import getOrgStructurePersonIdList


def getInterviewActionTypeIdList():
    db = QtGui.qApp.db
    table = db.table('ActionType')
    cond = [table['code'].eq(u'А01.31.024*'), table['deleted'].eq(0)]
    fields = table['id'].name()
    return [forceRef(record.value('id')) for record in db.getRecordList(table, fields, cond)]

def selectData(params):
    begDate = params.get('begDate', QDate())
    endDate = params.get('endDate', QDate())
    orgStructureId = params.get('orgStructureId', None)
    db = QtGui.qApp.db

    tableEvent = db.table('Event')
    tableAction = db.table('Action')
    tableActionProperty = db.table('ActionProperty')
    tableActionPropertyType = db.table('ActionPropertyType')
    tableActionPropertyString = db.table('ActionProperty_String')
    tableMES = db.table('mes.MES')
    tableMESGroup = db.table('mes.mrbMESGroup')
    tableClient = db.table('Client')

    queryTable = tableEvent

    queryTable = queryTable.leftJoin(tableMES, tableMES['id'].eq(tableEvent['MES_id']))
    queryTable = queryTable.leftJoin(tableMESGroup, tableMESGroup['id'].eq(tableMES['group_id']))
    queryTable = queryTable.leftJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
    queryTable = queryTable.leftJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
    queryTable = queryTable.leftJoin(tableActionProperty, tableActionProperty['action_id'].eq(tableAction['id']))
    queryTable = queryTable.leftJoin(tableActionPropertyType, tableActionPropertyType['id'].eq(tableActionProperty['type_id']))
    queryTable = queryTable.leftJoin(tableActionPropertyString, tableActionPropertyString['id'].eq(tableActionProperty['id']))

    cond = [tableEvent['deleted'].eq(0),
            tableEvent['execDate'].ge(begDate),
            tableEvent['execDate'].lt(endDate.addDays(1)),
            tableMESGroup['code'].eq(u'ДиспанС'),
            tableAction['deleted'].eq(0),
            tableAction['actionType_id'].inlist(getInterviewActionTypeIdList())
            ]
    if orgStructureId:
        cond.append(tableEvent['execPerson_id'].inlist(getOrgStructurePersonIdList(orgStructureId)))
    fields = [tableEvent['id'].alias('eventId'),
              'age(Client.`birthDate`, \'%s\') AS clientAge' % unicode(QDate(endDate.year(), 12, 31).toString('yyyy-MM-dd')),
              tableClient['sex'].alias('clientSex'),
              tableClient['id'].alias('clientId'),
              tableActionPropertyType['shortName'].alias('propertyShortName'),
              tableActionPropertyString['value'].alias('propertyValue')
              ]


    stmt = db.selectStmt(queryTable, fields, cond, tableEvent['id'].name())

#    print stmt

    return db.query(stmt)

class CReportForm131_o_4000_2014(CReport):
    ## Report form 131/o - table 4000
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Сведения о распространенности факторов риска развития хронических неинфекционных заболеваний, являющихся основной причиной инвалидности и преждевременной смертности населения Российской Федерации (человек)')


    def getSetupDialog(self, parent):
        result = CReportSetupDialog(parent)
        result.setEventTypeVisible(False)
        result.setOnlyPermanentAttachVisible(False)
        result.setOrgStructureVisible(True)
        result.setTitle(self.title())
        return result


    def _getRowsDefaults(self):
        ## init and return default values
        rows  = {
                  1: [u'Повышенный уровень артериального давления'],
                  2: [u'Дислипидемия'],
                  3: [u'Повышенный уровень глюкозы в крови'],
                  4: [u'Курение табака'],
                  5: [u'Риск пагубного потребления алкоголя'],
                  6: [u'Риск потребления наркотических средств и психотропных веществ без назначения врача'],
                  7: [u'Нерациональное питание'],
                  8: [u'Низкая физическая активность'],
                  9: [u'Избыточная масса тела (ожирение)'],
                 10: [u'Отягощенная наследственность по хроническим неинфекционным заболеваниям'],
                 11: [u'Высокий уровень стресса'],
                 12: [u'Умеренный суммарный сердечно-сосудистый риск'],
                 13: [u'Высокий суммарный сердечно-сосудистый риск'],
                 14: [u'Очень высокий суммарный сердечно-сосудистый риск'],
                }

        for rowValueList in rows.values():
            for i in range(9):
                rowValueList.append(0)

        return rows

    def getReportData(self, query):
        ##  data processing

        def _checkValue(row, value):
            if row == 8:
                return value == u'до 30 мин'
            else:
                return value == u'да'

        reportData = self._getRowsDefaults()

        commonColumn = 7

        clientIdAndRowList = [] # list of distinct cuple values (clientId, propertyShortName)
        while query.next():

            record = query.record()

            clientId = forceRef(record.value('clientId'))
            propertyShortNameList = forceString(record.value('propertyShortName')).split(',')

            if not all([trim(propertyShortName).isdigit() for propertyShortName in propertyShortNameList]):
                continue

            for propertyShortName in propertyShortNameList:
                row = int(propertyShortName)
                if row in reportData and (clientId, row) not in clientIdAndRowList:
                    clientIdAndRowList.append((clientId, row))
                else:
                    continue

                propertyValue = forceString(record.value('propertyValue'))
                if not _checkValue(row, propertyValue):
                    continue

                clientAge = forceInt(record.value('clientAge'))
                clientSex = forceInt(record.value('clientSex'))


                column = 1 if clientSex == 1 else 4

                if 18 <= clientAge <= 36:
                    reportData[row][column] += 1
                    reportData[row][commonColumn] += 1

                elif 39 <= clientAge <= 60:
                    reportData[row][column+1] += 1
                    reportData[row][commonColumn+1] += 1

                elif 60 < clientAge:
                    reportData[row][column+2] += 1
                    reportData[row][commonColumn+2] += 1


        return reportData


    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        tableColumns = [
            ( '47%', [u'Фактор риска развития заболеваний', u''], CReportBase.AlignLeft),
            ( '3%',  [u'№', u''], CReportBase.AlignRight),
            ( '5%',  [u'Мужчины', u'18 – 36 лет'], CReportBase.AlignRight),
            ( '5%',  [u'', u'39 – 60 лет'], CReportBase.AlignRight),
            ( '5%',  [u'', u'Старше 60 лет'], CReportBase.AlignRight),
            ( '5%',  [u'Женщины', u'18 – 36 лет'], CReportBase.AlignRight),
            ( '5%',  [u'', u'39 – 60 лет'], CReportBase.AlignRight),
            ( '5%',  [u'', u'Старше 60 лет'], CReportBase.AlignRight),
            ( '5%',  [u'Всего', u'18 – 36 лет'], CReportBase.AlignRight),
            ( '5%',  [u'', u'39 – 60 лет'], CReportBase.AlignRight),
            ( '5%',  [u'', u'Старше 60 лет'], CReportBase.AlignRight)
                      ]

        table = createTable(cursor, tableColumns)

        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 2, 1)
        table.mergeCells(0, 2, 1, 3)
        table.mergeCells(0, 5, 1, 3)
        table.mergeCells(0, 8, 1, 3)

        query = selectData(params)

        reportData = self.getReportData(query)

        reportDataKeyList = reportData.keys()
        reportDataKeyList.sort()
        for dataKey in reportDataKeyList:
            data = reportData[dataKey]

            i = table.addRow()
            table.setText(i, 0, data[0])
            table.setText(i, 1, dataKey)

            for idx, value in enumerate(data[1:]):
                table.setText(i, idx+2, value)

        return doc



