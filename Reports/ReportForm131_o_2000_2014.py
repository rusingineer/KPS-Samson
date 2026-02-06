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

from library.Utils             import forceInt, forceRef, forceString
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
    tablePerson = db.table('Person')
    tableMESSpeciality = db.table('mes.mrbSpeciality')
    tableSpeciality = db.table('rbSpeciality')

    queryTable = tableEvent
    queryTable = queryTable.leftJoin(tableMES, tableMES['id'].eq(tableEvent['MES_id']))
    queryTable = queryTable.leftJoin(tableMESVisit, tableMESVisit['master_id'].eq(tableMES['id']))
    queryTable = queryTable.leftJoin(tableMESGroup, tableMESGroup['id'].eq(tableMES['group_id']))
    queryTable = queryTable.leftJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
    queryTable = queryTable.leftJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
    queryTable = queryTable.leftJoin(tableService, tableService['id'].eq(tableActionType['nomenclativeService_id']))
    queryTable = queryTable.leftJoin(tablePerson, tablePerson['id'].eq(tableAction['person_id']))
    queryTable = queryTable.leftJoin(tableSpeciality, tableSpeciality['id'].eq(tablePerson['speciality_id']))
    queryTable = queryTable.leftJoin(tableMESSpeciality, tableMESSpeciality['id'].eq(tableMESVisit['speciality_id']))

#    cond = [db.joinOr([tableEvent['deleted'].eq(0), tableEvent['deleted'].isNull()]),
#            tableEvent['prevEvent_id'].isNull(),
#            db.joinOr([tableEvent['execDate'].dateGe(begDate), tableEvent['execDate'].isNull()]),
#            db.joinOr([tableEvent['setDate'].dateLe(endDate), db.joinAnd([tableEvent['setDate'].isNull(), tableEvent['id'].isNull()])]),
#            tableMESGroup['code'].eq(u'ДиспанС'),
#            db.joinOr([tableAction['endDate'].isNotNull(), tableAction['id'].isNull()]),
#            db.joinOr([tableAction['deleted'].eq(0), tableAction['id'].isNull()]),
#            db.joinOr([tableActionType['deleted'].eq(0), tableActionType['deleted'].isNull()]),
#            '(mes.MES_visit.`serviceCode` = SUBSTR(rbService.`code`,1, CHAR_LENGTH(mes.MES_visit.`serviceCode`)) OR Action.`id` IS NULL)',
#            db.joinOr([tableSpeciality['OKSOCode'].eq(tableMESSpeciality['code']), 'mes.mrbSpeciality.`code`=SUBSTR(rbSpeciality.`federalCode`, 2)', tablePerson['id'].isNull()])
#            ]
#            # ОКСО код или федеральный(без первого знака)? Или просто оксокод не заполнен где нужно у нас?

    cond = [tableEvent['deleted'].eq(0),
            tableEvent['prevEvent_id'].isNull(),
            tableEvent['execDate'].ge(begDate),
            tableEvent['execDate'].lt(endDate.addDays(1)),
            tableMESGroup['code'].eq(u'ДиспанС'),
            tableAction['endDate'].isNotNull(),
            tableAction['deleted'].eq(0),
            tableActionType['deleted'].eq(0),
#            '(mes.MES_visit.`serviceCode` = SUBSTR(rbService.`code`,1, CHAR_LENGTH(mes.MES_visit.`serviceCode`)) OR Action.`id` IS NULL)',
            '(mes.MES_visit.`serviceCode` = SUBSTR(rbService.`code`,1, CHAR_LENGTH(mes.MES_visit.`serviceCode`))AND SUBSTR(rbService.`code`, CHAR_LENGTH(mes.MES_visit.`serviceCode`)+1) REGEXP \'^([*.]|$)\'  OR Action.`id` IS NULL)',
            ]
    if orgStructureId:
        cond.append(tableEvent['execPerson_id'].inlist(getOrgStructurePersonIdList(orgStructureId)))
    fields = [tableEvent['id'].alias('eventId'),
              tableEvent['client_id'].alias('clientId'),
              tableEvent['execDate'].alias('eventExecDate'),
              tableAction['actionType_id'].alias('actionTypeId'),
              'CONCAT_WS(" | ", ActionType.`code`, ActionType.`name`) AS actionTypeName',
              tableService['name'].alias('serviceName'),
              tableAction['id'].alias('actionId'),
              tableAction['MKB'].alias('actionMkb'),
              tableMESVisit['additionalServiceCode'].alias('numMesVisitCode')]

    stmt = db.selectDistinctStmt(queryTable, fields, cond, tableEvent['id'].name())
#    print stmt
    return db.query(stmt)


class CReportForm131_o_2000_2014(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Сведения о первом этапе диспансеризации определенных групп взрослого населения (далее - диспансеризация)')
        self.mapNumMesVisitCode2Name = {
                        1  : u'Опрос(анкетирование), направленный на выявление хронических неинфекционных заболеваний, факторов риска их развития, потребления наркотических средств и психотропных веществ без назначения врача',
                        2  : u'Измерение артериального давления',
                        3  : u'Антропометрия, расчет индекса масcы тела',
                        4  : u'Определение уровня общего холестерина в крови',
                        5  : u'Определение уровня глюкозы в крови',
                        6  : u'Oпределение суммарного сердечно-сосудистого риска',
                        7  : u'Измерение внутриглазного давления',
                        8  : u'Клинический анализ крови развернутый',
                        9  : u'Клинический анализ крови',
                        10 : u'Общий анализ мочи',
                        11 : u'Анализ крови биохимический общетерапевтический',
                        12 : u'Исследование кала на скрытую кровь',
                        13 : u'Ультразвуковое исследование органов брюшной полости',
                        14 : u'Флюорография легких',
                        15 : u'Электрокардиография в покое',
                        16 : u'Профилактический прием (осмотр, консультация) врача-невролога',
                        17 : u'прием (осмотр) врача-терапевта',
                        18 : u'Взятие мазка  с шейки матки на цитологическое исследование',
                        19 : u'Маммография',
                        20 : u'Определение уровня простат-специфического антигена в крови'
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
        for key in self.mapNumMesVisitCode2Name.keys():
            result[key] = [0, 0]
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
            clientId = forceRef(record.value('clientId'))
            serviceName = forceString(record.value('serviceName'))
            numMesVisitCode = forceInt(record.value('numMesVisitCode'))
            if numMesVisitCode not in self.mapNumMesVisitCode2Name:
                continue
            key = (eventId, numMesVisitCode, serviceName)
            if key in uniqueSet:
                continue
            uniqueSet.add(key)
            data = reportData.setdefault(numMesVisitCode, [0, 0])
            if eventId and actionId:
                data[0] += 1

            if actionMkb and actionMkb[0].isalpha() and actionMkb[0].upper() != 'Z':
                data[1] += 1
                clientIdWithMkbSet.add(clientId)

            clientIdSet.add(clientId)
        return reportData, [len(clientIdSet), len(clientIdWithMkbSet)]


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
            ( '15%', [u'Прошли первый этап диспансеризации, человек'], CReportBase.AlignRight),
            ( '15%', [u'Выявлены заболевания, случаев'], CReportBase.AlignRight),
        ]
        table = createTable(cursor, tableColumns)
        query = selectData(params)

        if query is None:
            return doc

        reportData, total = self.getReportData(query)

        dataKeyList = reportData.keys()
        dataKeyList.sort()

        for numMesVisitCode in dataKeyList:
            name = self.getName(numMesVisitCode)
            data = reportData[numMesVisitCode]
            i = table.addRow()
            table.setText(i, 0, name)
            table.setText(i, 1, numMesVisitCode)
            table.setText(i, 2, data[0])
            table.setText(i, 3, data[1])
        i = table.addRow()
        table.mergeCells(i, 0, 1, 2)
        table.setText(i, 1, u'Всего')
        table.setText(i, 2, total[0])
        table.setText(i, 3, total[1])
        return doc


    def getName(self, num):
        return self.mapNumMesVisitCode2Name.get(num, '')
