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

from library.Utils             import forceRef, forceString

from Reports.Report            import CReport
from Reports.ReportBase        import CReportBase, createTable
from Reports.ReportSetupDialog import CReportSetupDialog
from Orgs.Utils                import getOrgStructurePersonIdList


def selectData(params):
    begDate = params.get('begDate', QDate())
    endDate = params.get('endDate', QDate())
    orgStructureId = params.get('orgStructureId', None)
    if not endDate:
        return None

    db = QtGui.qApp.db

    tableMESVisit = db.table('mes.MES_visit')
    tableMES = db.table('mes.MES')
    tableMESGroup = db.table('mes.mrbMESGroup')
    tableEvent = db.table('Event')
    tableAction = db.table('Action')
    tableActionType = db.table('ActionType')
    tableService = db.table('rbService')
#    tablePerson = db.table('Person')

    queryTable = tableEvent
    queryTable = queryTable.leftJoin(tableMES, tableMES['id'].eq(tableEvent['MES_id']))
    queryTable = queryTable.leftJoin(tableMESVisit, tableMESVisit['master_id'].eq(tableMES['id']))
    queryTable = queryTable.leftJoin(tableMESGroup, tableMESGroup['id'].eq(tableMES['group_id']))
    queryTable = queryTable.leftJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
    queryTable = queryTable.leftJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
    queryTable = queryTable.leftJoin(tableService, tableService['id'].eq(tableActionType['nomenclativeService_id']))
#    queryTable = queryTable.leftJoin(tablePerson, tablePerson['id'].eq(tableAction['person_id']))

    cond = [db.joinOr([tableEvent['deleted'].eq(0), tableEvent['deleted'].isNull()]),
            tableEvent['prevEvent_id'].isNotNull(),
            db.joinOr([tableEvent['execDate'].ge(begDate), tableEvent['execDate'].isNull()]),
            db.joinOr([tableEvent['setDate'].lt(endDate.addDays(1)), db.joinAnd([tableEvent['setDate'].isNull(), tableEvent['id'].isNull()])]),
            tableMESGroup['code'].eq(u'ДиспанС'),
            db.joinOr([tableAction['endDate'].isNotNull(), tableAction['id'].isNull()]),
            db.joinOr([tableAction['deleted'].eq(0), tableAction['id'].isNull()]),
            db.joinOr([tableActionType['deleted'].eq(0), tableActionType['deleted'].isNull()]),
#            '(mes.MES_visit.`serviceCode` = SUBSTR(rbService.`code`,1, CHAR_LENGTH(mes.MES_visit.`serviceCode`)) OR Action.`id` IS NULL)'
            '(mes.MES_visit.`serviceCode` = SUBSTR(rbService.`code`,1, CHAR_LENGTH(mes.MES_visit.`serviceCode`))AND SUBSTR(rbService.`code`, CHAR_LENGTH(mes.MES_visit.`serviceCode`)+1) REGEXP \'^([*.]|$)\'  OR Action.`id` IS NULL)',
            ]
    if orgStructureId:
        cond.append(tableEvent['execPerson_id'].inlist(getOrgStructurePersonIdList(orgStructureId)))
    fields = [tableEvent['id'].alias('eventId'),
              tableEvent['client_id'].alias('clientId'),
              tableEvent['execDate'].alias('eventExecDate'),
              'CONCAT_WS(" | ", ActionType.`code`, ActionType.`name`) AS actionTypeName',
              tableService['name'].alias('serviceName'),
              tableAction['id'].alias('actionId'),
              tableAction['MKB'].alias('actionMkb'),
              tableMESVisit['additionalServiceCode'].alias('numMesVisitCode')]

    stmt = db.selectStmt(queryTable, fields, cond)
    return db.query(stmt)


class CReportForm131_o_3000_2014(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Сведения о втором этапе диспансеризации определенных групп взрослого населения')
        self.mapNumMesVisitCode2Row = {u'55' : [1],
                                       u'56' : [2],
                                       u'22' : [3],
                                       u'16' : [3],
                                       u'44' : [3],
                                       u'48' : [4],
                                       u'49' : [4],
                                       u'50' : [4],
                                       u'45' : [5],
                                       u'46' : [5],
                                       u'57' : [6],
                                       u'53' : [7],
                                       u'26' : [8],
                                       u'54' : [9],
                                       u'23' : [10],
                                       u'47' : [10],
                                       u'17' : [11],
                                       u'51' : [11],
                                       u'52' : [12, 13]
                                      }
        self.row2Name = {
                         1 : u'Дуплексное сканирование брахицефальных артерий',
                         2 : u'Эзофагогастродуоденоскопия ',
                         3 : u'Осмотр (консультация) врача-невролога',
                         4 : u'Осмотр (консультация) врача-хирурга/врача-уролога (для мужчин)',
                         5 : u'Осмотр (консультация) врача-хирурга/врача-колопроктолога',
                         6 : u'Колоноскопия (ректороманоскопия)',
                         7 : u'Определение липидного спектра крови ',
                         8 : u'Осмотр (консультация) врача-акушера-гинеколога (для женщин)',
                         9 : u'Определение концентрации гликированного гемоглобина в крови (тест на толерантность к глюкозе)',
                        10 : u'Осмотр (консультация) врача-офтальмолога ',
                        11 : u'Прием (осмотр) врача-терапевта (врача-терапевта участкового, врача-терапевта цехового врачебного участка, врача общей практики (семейного врача)',
                        12 : u'Углубленное профилактическое консультирование индивидуальное',
                        13 : u'Профилактическое консультирование групповое',
                        14 : u'Итого'
        }


    def getSetupDialog(self, parent):
        result = CReportSetupDialog(parent)
        result.setEventTypeVisible(False)
        result.setOnlyPermanentAttachVisible(False)
        result.setOrgStructureVisible(True)
        result.setTitle(self.title())
        return result


    def _getDefault(self):
        result = {}
        for key in self.row2Name:
            result[key] = [0, 0, 0]
        return result


    def getReportData(self, query):
        reportData = self._getDefault()

        uniqueSet = set()
        clientIdSet = set()
        clientIdWithMkbSet = set()

        while query.next():
            record = query.record()
            eventId = forceRef(record.value('eventId'))
            actionId = forceRef(record.value('actionId'))
            actionMkb = forceString(record.value('actionMkb'))
            serviceName = forceString(record.value('serviceName'))
            clientId = forceRef(record.value('clientId'))
            numMesVisitCode = forceString(record.value('numMesVisitCode'))

            if numMesVisitCode not in self.mapNumMesVisitCode2Row:
                continue

            key = eventId, numMesVisitCode, serviceName
            if key in uniqueSet:
                continue
            uniqueSet.add(key)

            rowList = self.mapNumMesVisitCode2Row[numMesVisitCode]
            for row in rowList:
                data = reportData.setdefault(row, [0, 0, 0])
                if eventId and actionId:
                    data[1] += 1
                if actionMkb and actionMkb[0].isalpha():
                    data[2] += 1
                    clientIdWithMkbSet.add(clientId)
            clientIdSet.add(clientId)

        return reportData, [0, len(clientIdSet), len(clientIdWithMkbSet)]

    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        tableColumns = [
            ( '45%', [u'Осмотр (консультация), исследование'], CReportBase.AlignLeft),
            ( '3%', [u'№'], CReportBase.AlignRight),
            ( '17%', [u'Выявлены показания по результатам первого этапа диспансеризации'], CReportBase.AlignRight),
            ( '17%', [u'Обследовано'], CReportBase.AlignRight),
            ( '17%', [u'Выявлены заболевания (подозрение на наличие заболевания)'], CReportBase.AlignRight),
        ]

        table = createTable(cursor, tableColumns)
        query = selectData(params)

        if query is None:
            return doc

        reportData, total = self.getReportData(query)

        dataKeyList = reportData.keys()
        dataKeyList.sort()

        for dataRow in dataKeyList:
            name = self.getName(dataRow)
            data = reportData[dataRow]
            i = table.addRow()
            table.setText(i, 0, name)
            table.setText(i, 1, dataRow)
            table.setText(i, 2, data[0])
            table.setText(i, 3, data[1])
            table.setText(i, 4, data[2])

        i = table.addRow()
        table.mergeCells(i, 0, 1, 2)
        table.setText(i, 1, u'Всего')
        table.setText(i, 2, total[0])
        table.setText(i, 3, total[1])
        table.setText(i, 4, total[2])

        return doc


    def getName(self, num):
        return self.row2Name.get(num, '')
