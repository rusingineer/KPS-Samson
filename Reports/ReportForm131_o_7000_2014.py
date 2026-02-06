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

from library.Utils             import forceDate, forceInt, forceRef, forceString, forceStringEx

from Reports.Report            import CReport
from Reports.ReportBase        import CReportBase, createTable
from Reports.ReportSetupDialog import CReportSetupDialog
from Orgs.Utils                import getOrgStructurePersonIdList


def selectData(params):
    begDate = params.get('begDate', QDate())
    endDate = params.get('endDate', QDate())
    onlyPayedEvents = params.get('onlyPayedEvents', False)
    begPayDate = params.get('begPayDate', QDate())
    endPayDate = params.get('endPayDate', QDate())
    orgStructureId = params.get('orgStructureId', None)
    db = QtGui.qApp.db

    tableEvent = db.table('Event')
    tableMES = db.table('mes.MES')
    tableMESGroup = db.table('mes.mrbMESGroup')
    tableClient = db.table('Client')
    tableClientWork = db.table('ClientWork')
    tableDiagnostic = db.table('Diagnostic')
    tableDiagnosticResult = db.table('rbDiagnosticResult')
    tableDiagnosis = db.table('Diagnosis')
    tableHealthGroup = db.table('rbHealthGroup')
    tableDispanser = db.table('rbDispanser')
    tableSecondEvent = db.table('Event').alias('SecondEvent')

    queryTable = tableEvent

    queryTable = queryTable.leftJoin(tableMES, tableMES['id'].eq(tableEvent['MES_id']))
    queryTable = queryTable.leftJoin(tableMESGroup, tableMESGroup['id'].eq(tableMES['group_id']))
    queryTable = queryTable.leftJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
    queryTable = queryTable.leftJoin(tableDiagnostic, tableDiagnostic['event_id'].eq(tableEvent['id']))
    queryTable = queryTable.leftJoin(tableDiagnosis, tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']))
    queryTable = queryTable.leftJoin(tableHealthGroup, tableHealthGroup['id'].eq(tableDiagnostic['healthGroup_id']))
    queryTable = queryTable.leftJoin(tableDiagnosticResult, tableDiagnosticResult['id'].eq(tableDiagnostic['result_id']))
    queryTable = queryTable.leftJoin(tableDispanser, tableDispanser['id'].eq(tableDiagnostic['dispanser_id']))
    queryTable = queryTable.leftJoin(tableClientWork, tableClientWork['client_id'].eq(tableClient['id']))
    queryTable = queryTable.leftJoin(tableSecondEvent, tableSecondEvent['prevEvent_id'].eq(tableEvent['id']))

    cond = [tableEvent['deleted'].eq(0),
            tableEvent['execDate'].ge(begDate),
            tableEvent['execDate'].lt(endDate.addDays(1)),
            tableMESGroup['code'].eq(u'ДиспанС'),
            tableDiagnostic['diagnosisType_id'].eq(forceRef(db.translate('rbDiagnosisType', 'code', '1', 'id'))),
            'ClientWork.`id`=(SELECT MAX(CW.`id`) FROM ClientWork AS CW WHERE CW.`client_id`=ClientWork.`client_id` AND CW.`deleted`=0) OR ClientWork.`id` IS NULL'
            ]
    if orgStructureId:
        cond.append(tableEvent['execPerson_id'].inlist(getOrgStructurePersonIdList(orgStructureId)))
    if onlyPayedEvents:
        tableAccount = db.table('Account')
        tableAccountItem = db.table('Account_Item')
        accountQueryTable = tableAccount.innerJoin(tableAccountItem, tableAccountItem['master_id'].eq(tableAccount['id']))
        onlyPayedEventsCond = [tableAccountItem['event_id'].eq(tableEvent['id'])]
        if begPayDate:
            onlyPayedEventsCond.append(tableAccount['date'].ge(begPayDate))
        if endPayDate:
            onlyPayedEventsCond.append(tableAccount['date'].le(endPayDate))
        cond.append(db.existsStmt(accountQueryTable, onlyPayedEventsCond))

    fields = [tableEvent['id'].alias('eventId'),
              'age(Client.`birthDate`, \'%s\') AS clientAge' % unicode(QDate(endDate.year(), 12, 31).toString('yyyy-MM-dd')),
              tableDiagnosis['MKB'].name(),
              tableClient['sex'].alias('clientSex'),
              tableClient['id'].alias('clientId'),
              tableHealthGroup['code'].alias('healthGroupCode'),
              tableDiagnosticResult['code'].alias('diagnosticResultCode'),
              tableDispanser['observed'].alias('dispanserObserved'),
              tableDiagnostic['sanatorium'].alias('diagnosticSanatorium'),
              tableDiagnostic['hospital'].alias('diagnosticHospital'),
              '(SELECT COUNT(Action.id) FROM Action WHERE Action.event_id=Event.id AND Action.deleted=0 AND Action.status=3) AS cancelActionCount',
              tableClientWork['post'].alias('clientPost'),
              tableClientWork['id'].alias('clientWorkId'),
              tableClientWork['org_id'].alias('clientWorkOrgId'),
              tableClientWork['freeInput'].alias('clientWorkFreeInput'),
              'isClientVillager(Client.id) AS isVillager',
              tableSecondEvent['id'].alias('secondEventId'),
              tableSecondEvent['execDate'].alias('secondEventExecDate')
              ]


    stmt = db.selectStmt(queryTable, fields, cond, tableEvent['id'].name())

#    print stmt

    return db.query(stmt)

class CReportForm131_o_7000_2014(CReport):
    mapHealthGroup2Report = {1:1,
                             2:2,
                             3:3,
                             4:3,
                             5:3,
                             6:2}
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Общие результаты диспансеризации определенных групп взрослого населения')
        self._additionalRows = None


    def getSetupDialog(self, parent):
        result = CReportSetupDialog(parent)
        result.setEventTypeVisible(False)
        result.setOnlyPermanentAttachVisible(False)
        result.setOrgStructureVisible(True)
        result.setPayPeriodVisible(True)
        result.setTitle(self.title())
        return result


    def _getRowsDefaults(self):
        rows  = { 1: [u'Определена I группа здоровья'],
                  2: [u'Определена II группа здоровья'],
                  3: [u'Определена III группа здоровья'],
                  4: [u'Установлено диспансерное наблюдение'],
                  5: [u'Назначено лечение'],
                  6: [u'Направлено на дополнительное диагностическое исследование, не входящее в объем диспансеризации'],
                  7: [u'Направлено для получения специализированной, в том числе высокотехнологичной, медицинской помощи'],
                  8: [u'Направлено на санаторно-курортное лечение'],
                  }

        for rowValueList in rows.values():
            for i in range(6):
                rowValueList.append(0)

        return rows


    def _getAdditionalRowsDefaults(self):
        if self._additionalRows is None:
            rows = { 1 : [u'7001 Общее число работающих граждан, прошедших диспансеризацию', u'человек'],
                     2 : [u'7002 Общее число неработающих граждан, прошедших диспансеризацию', u'человек'],
                     3 : [u'7003 Общее число прошедших диспансеризацию граждан, обучающихся в образовательных организациях по очной форме', u'человек'],
                     4 : [u'7004 Общее число прошедших диспансеризацию инвалидов Великой Отечественной войны, лиц, награжденных знаком «Жителю блокадного Ленинграда» и признанных инвалидами вследствие общего заболевания, трудового увечья и других причин (кроме лиц, инвалидность которых наступила вследствие их противоправных действий)', u'человек'],
                     5 : [u'7005 Общее число прошедших диспансеризацию граждан, принадлежащих к коренным малочисленным народам Севера, Сибири и Дальнего Востока Российской Федерации 1)', u'человек'],
                     6 : [u'7006 Общее число медицинских организаций, принимавших участие в проведении диспансеризации', u''],
                     7 : [u'7007 Общее число мобильных медицинских бригад, принимавших участие в проведении диспансеризации', u''],
                     8 : [u'7008 Общее число граждан, диспансеризация которых была проведена мобильными медицинскими бригадами', u'человек'],
                     9 : [u'7009 Число письменных отказов от прохождения отдельных осмотров (консультаций), исследований в рамках диспансеризации', u''],
                    10 : [u'7010 Число письменных отказов от прохождения диспансеризации в целом', u''],
                    11 : [u'7011 Число граждан, прошедших за отчетный период первый этап диспансеризации и не завершивших второй этап диспансеризации', u'человек'],
                    12 : [u'7012 Число граждан, проживающих в сельской местности, прошедших диспансеризацию в отчетном периоде', u'человек']}

            for rowValueList in rows.values():
                rowValueList.append(0)

            self._additionalRows = rows

        return self._additionalRows

    def getReportData(self, query):
        reportData = self._getRowsDefaults()

        additionalReportData = self._getAdditionalRowsDefaults()

        previous = None

        clientIdList = []
        secondEventIdList = []

        while query.next():

            record = query.record()

            eventId = forceRef(record.value('eventId'))
            mkb = forceStringEx(record.value('MKB'))

            if (eventId, mkb) == previous:
                continue
            previous = (eventId, mkb)

            clientAge = forceInt(record.value('clientAge'))
            clientSex = forceInt(record.value('clientSex'))
            clientId = forceRef(record.value('clientId'))
            healthGroupCode = forceInt(record.value('healthGroupCode'))
            diagnosticResultCode = forceString(record.value('diagnosticResultCode'))
            dispanserObserved = forceInt(record.value('dispanserObserved'))
            diagnosticSanatorium = forceInt(record.value('diagnosticSanatorium'))
            diagnosticHospital = forceInt(record.value('diagnosticHospital'))
            cancelActionCount = forceInt(record.value('cancelActionCount'))
            clientWorkOrgId = forceRef(record.value('clientWorkOrgId'))
            clientWorkFreeInput = forceStringEx(record.value('clientWorkFreeInput'))
            isVillager = forceInt(record.value('isVillager'))
            secondEventId = forceRef(record.value('secondEventId'))
            secondEventExecDate = forceDate(record.value('secondEventExecDate'))

            if not (clientWorkOrgId or clientWorkFreeInput):
                clientWorkId = None
            else:
                clientWorkId = forceRef(record.value('clientWorkId'))

            clientPost = forceString(record.value('clientPost')).upper()

            rowList = []

            try:
                reportHealthGroup = self.mapHealthGroup2Report.get(healthGroupCode, None)
                if reportHealthGroup:
                    rowList.append(reportHealthGroup)
            except:
                pass

            if dispanserObserved:
                rowList.append(4)

            if diagnosticResultCode == '32':
                rowList.append(5)

            if diagnosticHospital > 1 and healthGroupCode in (4, 5):
                rowList.append(7)

            if diagnosticSanatorium > 1:
                rowList.append(8)


            for row in rowList:
                data = reportData.get(row, None)
                if data and clientSex:

                    column = 1 if clientSex == 1 else 4

                    if 18 <= clientAge <= 36:
                        data[column] += 1


                    elif 39 <= clientAge <= 60:
                        data[column+1] += 1


                    elif 60 < clientAge:
                        data[column+2] += 1

            if clientId not in clientIdList:
                if clientWorkId and u'СТУДЕНТ' not in clientPost: # работающие
                    additionalReportData[1][2] += 1
                elif not clientWorkId: # не работающие
                    additionalReportData[2][2] += 1
                elif clientWorkId and u'СТУДЕНТ' in clientPost: # студенты
                    additionalReportData[3][2] += 1
                if isVillager:
                    additionalReportData[12][2] += 1
                clientIdList.append(clientId)
            if secondEventId and secondEventId not in secondEventIdList and not secondEventExecDate:
                additionalReportData[11][2] += 1
                secondEventIdList.append(secondEventId)

            additionalReportData[9][2] += cancelActionCount

        return reportData, additionalReportData


    def build(self, params):
        self._additionalRows = None
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        tableColumns = [
            ( '67%', [u'Результат диспансеризации определенных групп взрослого населения (далее – диспансеризация)', u''], CReportBase.AlignLeft),
            ( '3%',  [u'№ строки', u''], CReportBase.AlignRight),
            ( '5%',  [u'Мужчины', u'18 – 36 лет'], CReportBase.AlignRight),
            ( '5%',  [u'', u'39 – 60 лет'], CReportBase.AlignRight),
            ( '5%',  [u'', u'Старше 60 лет'], CReportBase.AlignRight),
            ( '5%',  [u'Женщины', u'18 – 36 лет'], CReportBase.AlignRight),
            ( '5%',  [u'', u'39 – 60 лет'], CReportBase.AlignRight),
            ( '5%',  [u'', u'Старше 60 лет'], CReportBase.AlignRight)
                      ]

        table = createTable(cursor, tableColumns)

        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 2, 1)
        table.mergeCells(0, 2, 1, 3)
        table.mergeCells(0, 5, 1, 3)


        query = selectData(params)

        reportData, additionalReportData = self.getReportData(query)

        reportDataKeyList = reportData.keys()
        reportDataKeyList.sort()
        for dataKey in reportDataKeyList:
            data = reportData[dataKey]

            i = table.addRow()
            table.setText(i, 0, data[0])
            table.setText(i, 1, dataKey)

            for idx, value in enumerate(data[1:]):
                table.setText(i, idx+2, value)

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertBlock()

        tableColumns = [
                        ( '90%', [u''], CReportBase.AlignLeft),
                        ( '5%',  [u''], CReportBase.AlignRight),
                        ( '5%',  [u''], CReportBase.AlignLeft)
                       ]


        table = createTable(cursor, tableColumns)

        additionalReportDataKeyList = additionalReportData.keys()
        additionalReportDataKeyList.sort()
        additionalRowsCount = len(additionalReportDataKeyList)
        for dataKeyIdx, dataKey in enumerate(additionalReportDataKeyList):
            data = additionalReportData[dataKey]

            row = table.rowCount()-1

            table.setText(row, 0, data[0])
            table.setText(row, 1, data[2])
            table.setText(row, 2, data[1])

            if dataKeyIdx < additionalRowsCount-1:
                table.addRow()

        return doc




