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

from library.Utils             import forceBool, forceDate, forceInt, forceRef, forceString, forceStringEx, lastYearDay
from Reports.Report            import CReport, normalizeMKB
from Reports.ReportBase        import CReportBase, createTable
from Reports.ReportSetupDialog import CReportSetupDialog
from Reports.Utils             import getAgeClass
from Reports.ReportView        import CPageFormat
from Orgs.Utils                import getOrgStructurePersonIdList


def selectData(params):
    begDate = params.get('begDate', QDate())
    endDate = params.get('endDate', QDate())
    orgStructureId = params.get('orgStructureId', None)
    onlyPayedEvents = params.get('onlyPayedEvents', False)
    begPayDate = params.get('begPayDate', QDate())
    endPayDate = params.get('endPayDate', QDate())
    db = QtGui.qApp.db
    tableEvent = db.table('Event')
    tableMES = db.table('mes.MES')
    tableMESGroup = db.table('mes.mrbMESGroup')
    tableClient = db.table('Client')
    tableClientWork = db.table('ClientWork')
    tableClientSocStatus = db.table('ClientSocStatus')
    tableClientSocStatusClass = db.table('rbSocStatusClass')
    tableClientSocStatusType = db.table('rbSocStatusType')
    tableClientConsent = db.table('ClientConsent')
    tableClientConsentType = db.table('rbClientConsentType')
    tableDiagnostic = db.table('Diagnostic')
    tableDiagnosticResult = db.table('rbDiagnosticResult')
    tableDiagnosis = db.table('Diagnosis')
    tableHealthGroup = db.table('rbHealthGroup')
    tableDispanser = db.table('rbDispanser')
    tableSecondEvent = db.table('Event').alias('SecondEvent')
    queryTable = tableEvent
    queryTable = queryTable.innerJoin(tableMES, tableMES['id'].eq(tableEvent['MES_id']))
    queryTable = queryTable.innerJoin(tableMESGroup, tableMESGroup['id'].eq(tableMES['group_id']))
    queryTable = queryTable.leftJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
    queryTable = queryTable.leftJoin(tableDiagnostic,
    db.joinAnd([tableDiagnostic['event_id'].eq(tableEvent['id']),
                '''(Diagnostic.`diagnosisType_id`= (SELECT rbDiagnosisType.id
                                     FROM rbDiagnosisType
                                     WHERE rbDiagnosisType.code = 1))'''
              ]))
    queryTable = queryTable.leftJoin(tableDiagnosis, tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']))
    queryTable = queryTable.leftJoin(tableHealthGroup, tableHealthGroup['id'].eq(tableDiagnostic['healthGroup_id']))
    queryTable = queryTable.leftJoin(tableDiagnosticResult, tableDiagnosticResult['id'].eq(tableDiagnostic['result_id']))
    queryTable = queryTable.leftJoin(tableDispanser, tableDispanser['id'].eq(tableDiagnostic['dispanser_id']))
    queryTable = queryTable.leftJoin(tableClientWork,
    db.joinAnd([tableClientWork['client_id'].eq(tableClient['id']),
                '''ClientWork.`id`=(SELECT MAX(CW.`id`) FROM ClientWork AS CW WHERE CW.`client_id`=ClientWork.`client_id` AND CW.`deleted`=0)'''
               ]))
    queryTable = queryTable.leftJoin(tableClientSocStatus, db.joinAnd([tableClientSocStatus['client_id'].eq(tableClient['id']),
                 tableClientSocStatus['deleted'].eq(0),
                 db.joinOr([db.joinAnd([tableClientSocStatus['begDate'].isNull(), tableClientSocStatus['endDate'].isNull()]),
                 db.joinAnd([
                 db.joinOr([tableClientSocStatus['endDate'].isNull(), tableClientSocStatus['endDate'].ge(begDate)]),
                 db.joinOr([tableClientSocStatus['begDate'].isNull(),
                            tableClientSocStatus['begDate'].lt(endDate.addDays(1))])
                 ])
                 ])]))
    queryTable = queryTable.leftJoin(tableClientSocStatusClass, tableClientSocStatusClass['id'].eq(tableClientSocStatus['socStatusClass_id']))
    queryTable = queryTable.leftJoin(tableClientSocStatusType, tableClientSocStatusType['id'].eq(tableClientSocStatus['socStatusType_id']))
    queryTable = queryTable.leftJoin(tableSecondEvent, tableSecondEvent['prevEvent_id'].eq(tableEvent['id']))
    queryTable = queryTable.leftJoin(tableClientConsent, db.joinAnd([tableClientConsent['client_id'].eq(tableClient['id']),
                 tableClientConsent['deleted'].eq(0),
                 db.joinOr([db.joinAnd([tableClientConsent['date'].isNull(), tableClientConsent['endDate'].isNull()]),
                 db.joinAnd([
                 db.joinOr([tableClientConsent['endDate'].isNull(), db.joinAnd([tableClientConsent['endDate'].ge(begDate),
                 tableClientConsent['endDate'].lt(endDate.addDays(1))])]),
                 db.joinOr([tableClientConsent['date'].isNull(),
                            tableClientConsent['date'].lt(endDate.addDays(1))])
                 ])
                 ])]))
    queryTable = queryTable.leftJoin(tableClientConsentType, tableClientConsentType['id'].eq(tableClientConsent['clientConsentType_id']))
    cond = [tableEvent['deleted'].eq(0),
            tableEvent['execDate'].ge(begDate),
            tableEvent['execDate'].lt(endDate.addDays(1)),
            tableMESGroup['code'].eq(u'ДиспанС'),
            db.joinOr([tableMES['endDate'].isNull(), tableMES['endDate'].ge(begDate)])
            ]
    if onlyPayedEvents:
        tableAccount = db.table('Account')
        tableAccountItem = db.table('Account_Item')
        accountQueryTable = tableAccount.innerJoin(tableAccountItem, tableAccountItem['master_id'].eq(tableAccount['id']))
        onlyPayedEventsCond = [tableAccountItem['event_id'].eq(tableEvent['id'])]
        if begPayDate:
            onlyPayedEventsCond.append(tableAccount['date'].ge(begPayDate))
        if endPayDate:
            onlyPayedEventsCond.append(tableAccount['date'].lt(endPayDate.addDays(1)))
        cond.append(db.existsStmt(accountQueryTable, onlyPayedEventsCond))
    mesDispansIdList = params.get('mesDispansIdList', [])
    if mesDispansIdList:
        cond.append(tableEvent['MES_id'].inlist(mesDispansIdList))
    if orgStructureId:
        cond.append(tableEvent['execPerson_id'].inlist(getOrgStructurePersonIdList(orgStructureId)))
    fields = [tableEvent['id'].alias('eventId'),
              'age(Client.`birthDate`, %s) AS clientAge' % db.formatDate(lastYearDay(endDate)),
              tableDiagnosis['MKB'].name(),
              tableClient['sex'].alias('clientSex'),
              tableClient['id'].alias('clientId'),
              tableHealthGroup['code'].alias('healthGroupCode'),
              tableDiagnosticResult['code'].alias('diagnosticResultCode'),
              tableDispanser['observed'].alias('dispanserObserved'),
              tableDiagnostic['hospital'].alias('diagnosticHospital'),
              tableDiagnostic['sanatorium'].alias('diagnosticSanatorium'),
              '(SELECT COUNT(Action.id) FROM Action WHERE Action.event_id=Event.id AND Action.deleted=0 AND Action.status=6) AS cancelActionCount',
              tableClientWork['post'].alias('clientPost'),
              tableClientWork['id'].alias('clientWorkId'),
              tableClientWork['org_id'].alias('clientWorkOrgId'),
              tableClientWork['freeInput'].alias('clientWorkFreeInput'),
              'isClientVillager(Client.id) AS isVillager',
              tableSecondEvent['id'].alias('secondEventId'),
              tableSecondEvent['execDate'].alias('secondEventExecDate'),
              'IF(rbSocStatusClass.code = \'1\', 1, 0) AS advantage',
              'CASE rbSocStatusType.code'
              ' WHEN \'01\'  THEN 1'
              ' WHEN \'010\' THEN 1'

              ' WHEN \'011\' THEN 2'
              ' WHEN \'012\' THEN 2'
              ' WHEN \'02\'  THEN 2'
              ' WHEN \'020\' THEN 2'

              ' WHEN \'03\'  THEN 3'
              ' WHEN \'030\' THEN 3'

              ' WHEN \'04\'  THEN 4'
              ' WHEN \'040\' THEN 4'

              ' WHEN \'05\'  THEN 5'
              ' WHEN \'050\' THEN 5'

              ' WHEN \'06\'  THEN 6'
              ' WHEN \'060\' THEN 6'

              ' WHEN \'120\' THEN 7'

              ' WHEN \'08\'  THEN 8'
              ' WHEN \'081\' THEN 8'
              ' WHEN \'082\' THEN 8'
              ' WHEN \'083\' THEN 8'
              ' ELSE NULL END AS socStatusType',

              'IF(ClientConsent.value = 0 AND rbClientConsentType.code = \'%s\', 1, 0) AS consentRefusal'%(u'Дисп'),

              'EXISTS(SELECT AT.id'
              ' FROM Action AS A'
              ' INNER JOIN ActionType AS AT ON A.actionType_id = AT.id'
              ' WHERE A.event_id = Event.id'
              ' AND A.deleted = 0'
              ' AND AT.deleted = 0'
              ' AND AT.class = 2'
              ' AND A.endDate IS NOT NULL'
              ') AS isActionClass2',

              'EXISTS(SELECT rbDiagnosticResult.id'
              ' FROM Diagnostic AS D'
              ' INNER JOIN rbDiagnosticResult ON rbDiagnosticResult.id = D.result_id'
              ' WHERE D.event_id = Event.id'
              ' AND D.deleted = 0'
              ' AND rbDiagnosticResult.code = \'07\''
              ') AS isResultAdditionDispans',

              'EXISTS(SELECT rbDiagnosticResult.id'
              ' FROM Diagnostic AS D'
              ' INNER JOIN rbDiagnosticResult ON rbDiagnosticResult.id = D.result_id'
              ' WHERE D.event_id = Event.id'
              ' AND D.deleted = 0'
              ' AND rbDiagnosticResult.code = \'10\''
              ') as isHighTech'
             ]
    fields.append('''EXISTS(SELECT DCR.id
                     FROM  Diagnostic AS DC
                     INNER JOIN rbDiagnosticResult AS DCR ON DCR.id = DC.result_id
                     WHERE DC.event_id = Event.id AND DC.deleted = 0
                     AND DCR.code = '11') AS isAppointCure''')
    stmt = db.selectStmt(queryTable, fields, cond, 'Event.id DESC')
    return db.query(stmt)


class CReportForm131_o_7000_2016(CReport):

    mapHealthGroupToReport = {u'1' :1,
                              u'2' :2,
                              u'3а':3,
                              u'3б':4,
                              u'6' :2
                             }

    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Общие результаты диспансеризации определенных групп взрослого населения (2016)')
        self.orientation = CPageFormat.Landscape


    def getSetupDialog(self, parent):
        result = CReportSetupDialog(parent)
        result.setEventTypeVisible(False)
        result.setMesDispansListVisible(True)
        result.setOnlyPermanentAttachVisible(False)
        result.setOrgStructureVisible(True)
        result.setPayPeriodVisible(True)
        result.setTitle(self.title())
        return result


    def _getRowsDefaults(self):
        rows  = { 1: [u'Определена I группа состояния здоровья'],
                  2: [u'Определена II группа состояния здоровья'],
                  3: [u'Определена IIIа группа состояния здоровья'],
                  4: [u'Определена IIIб группа состояния здоровья'],
                  5: [u'Назначено лечение'],
                  6: [u'Направлено на дополнительное обследование, не входящее в объем диспансеризации'],
                  7: [u'Направлено для получения специализированной, в том числе высокотехнологичной, медицинской помощи'],
                  8: [u'Направлено на санаторно-курортное лечение'],
                  }

        for rowValueList in rows.values():
            for i in range(6):
                rowValueList.append(0)

        return rows


    def _getAdditionalRowsDefaults(self):
        rows = { 1 : [u'7001 Общее число работающих граждан, прошедших диспансеризацию', u'человек'],
                 2 : [u'7002 Общее число неработающих граждан, прошедших диспансеризацию', u'человек'],
                 3 : [u'7003 Общее число прошедших диспансеризацию граждан, обучающихся в образовательных организациях по очной форме', u'человек'],
                 4 : [u'7004 Общее число прошедших диспансеризацию граждан, принадлежащих льготным категориям, в том числе', u'человек'],
                 (4, 1) : [u'7004.1 Инвалиды ВОВ', u'человек'],
                 (4, 2) : [u'7004.2 Участники ВОВ', u'человек'],
                 (4, 3) : [u'7004.3 Ветераны боевых действий из числа лиц, указанных в подпунктах1-4 пункта 1 статьи 3 ФЗ от 12.01.1995 № 5-ФЗ «О ветеранах»', u'человек'],
                 (4, 4) : [u'7004.4 Военнослужащих, проходивших военную службу в воинских частях, учреждениях, военно-учебных заведениях, не входивших в состав действующей армии, в период с 22 июня 1941 года по 3 сентября 1945 года не менее шести месяцев, военнослужащих, награжденных орденами или медалями СССР за службу в указанный период', u'человек'],
                 (4, 5) : [u'7004.5 Лицам, награжденным знаком «Жителю блокадного Ленинграда» и признанным инвалидами вследствие общего заболевания, трудового увечья и других причин (кроме лиц, инвалидность которых наступила вследствие их противоправных действий)', u'человек'],
                 (4, 6) : [u'7004.6 Лицам, работавшим в период Великой Отечественной войны на объектах противовоздушной обороны, местной противовоздушной обороны, строительстве оборонительных сооружений, военно-морских баз, аэродромов и других военных объектов в пределах тыловых границ действующих фронтов, операционных зон действующих флотов, на прифронтовых участках железных и автомобильных дорог, а так же  члены семей погибших работников госпиталей и больниц города Ленинграда', u'человек'],
                 (4, 7) : [u'7004.7 Интернированные', u'человек'],
                 (4, 8) : [u'7004.8 Инвалиды', u'человек'],
                 5 : [u'7005 Общее число прошедших диспансеризацию граждан, принадлежащих к коренным малочисленным народам Севера, Сибири и Дальнего Востока Российской Федерации 1)', u'человек'],
                 6 : [u'7006 Общее число медицинских организаций, принимавших участие в проведении диспансеризации', u''],
                 7 : [u'7007 Общее число мобильных медицинских бригад, принимавших участие в проведении диспансеризации', u''],
                 8 : [u'7008 Общее число граждан, диспансеризация которых была проведена мобильными медицинскими бригадами', u'человек'],
                 9 : [u'7009 Число письменных отказов от прохождения отдельных осмотров (консультаций), исследований в рамках диспансеризации', u''],
                10 : [u'7010 Число письменных отказов от прохождения диспансеризации в целом', u''],
                11 : [u'7011 Число граждан, прошедших за отчетный период первый этап диспансеризации и не завершивших второй этап диспансеризации', u'человек'],
                12 : [u'7012 Число граждан, проживающих в сельской местности, прошедших диспансеризацию в отчетном периоде', u'человек']}
        for rowValueList in rows.itervalues():
            rowValueList.append(0)
        return rows


    def getReportData(self, query, params):
        reportData = self._getRowsDefaults()
        additionalReportData = self._getAdditionalRowsDefaults()
        clientIdAndRowGroupSet = set()
        clientIdSet = set()
        clientIdAndSocStatusSet = set()
        secondEventIdSet = set()
        while query.next():
            record = query.record()
            clientAge            = forceInt(record.value('clientAge'))
            clientSex            = forceInt(record.value('clientSex'))
            clientId             = forceRef(record.value('clientId'))
            healthGroupCode      = forceString(record.value('healthGroupCode'))
            diagnosticSanatorium = forceInt(record.value('diagnosticSanatorium'))
            diagnosticHospital   = forceInt(record.value('diagnosticHospital'))
            cancelActionCount    = forceInt(record.value('cancelActionCount'))
            clientWorkOrgId      = forceRef(record.value('clientWorkOrgId'))
            clientWorkFreeInput  = forceStringEx(record.value('clientWorkFreeInput'))
            isVillager           = forceInt(record.value('isVillager'))
            isHighTech           = forceInt(record.value('isHighTech'))
            secondEventId        = forceRef(record.value('secondEventId'))
            secondEventExecDate  = forceDate(record.value('secondEventExecDate'))
            advantage            = forceBool(record.value('advantage'))
            socStatusType        = forceInt(record.value('socStatusType'))
            consentRefusal       = forceBool(record.value('consentRefusal'))
            isAppointCure        = forceBool(record.value('isAppointCure'))
            isResultAdditionDispans = forceBool(record.value('isResultAdditionDispans'))
            mkb                  = normalizeMKB(forceString(record.value('MKB')))
            if not (clientWorkOrgId or clientWorkFreeInput):
                clientWorkId = None
            else:
                clientWorkId = forceRef(record.value('clientWorkId'))
            clientPost = forceString(record.value('clientPost')).upper()

            ageColumn = getAgeClass(clientAge)
            if ageColumn is None:
                continue

            rowList = []
            reportHealthGroup = self.mapHealthGroupToReport.get(healthGroupCode, None)
            if reportHealthGroup is not None:
                rowList.append(reportHealthGroup)
            if isAppointCure:
                rowList.append(5)
            if isResultAdditionDispans and mkb:
                rowList.append(6)
            if (diagnosticHospital > 1 and healthGroupCode in (u'4', u'5')) or isHighTech:
                rowList.append(7)
            if diagnosticSanatorium > 1:
                rowList.append(8)

            for row in rowList:
                key = clientId, (row if row>4 else 1)
                if key not in clientIdAndRowGroupSet:
                    clientIdAndRowGroupSet.add(key)
                    reportRow = reportData[row]
                    if clientSex:
                        baseColumn = 1 if clientSex == 1 else 4
                        reportRow[baseColumn+ageColumn] += 1

            if clientId not in clientIdSet:
                clientIdSet.add(clientId)
                if clientWorkId and u'СТУДЕНТ' not in clientPost: # работающие
                    additionalReportData[1][2] += 1
                elif not clientWorkId: # не работающие
                    additionalReportData[2][2] += 1
                elif clientWorkId and u'СТУДЕНТ' in clientPost: # студенты
                    additionalReportData[3][2] += 1
                if advantage and socStatusType:
                    additionalReportData[4][2] += 1

                if consentRefusal:
                    additionalReportData[10][2] += 1
                if isVillager:
                    additionalReportData[12][2] += 1

            if advantage and socStatusType:
                key = (clientId, socStatusType)
                if key not in clientIdAndSocStatusSet:
                    clientIdAndSocStatusSet.add(key)
                    additionalReportData[(4, socStatusType)][2] += 1

            if secondEventId and secondEventId not in secondEventIdSet and not secondEventExecDate:
                secondEventIdSet.add(secondEventId)
                additionalReportData[11][2] += 1

            additionalReportData[9][2] += cancelActionCount

        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        db = QtGui.qApp.db
        table = db.table('ClientConsent')
        tableType = db.table('rbClientConsentType')
        cond = [table['deleted'].eq(0),
                table['value'].eq(0),
                tableType['code'].like(u'Дисп')
                ]
        if begDate:
            cond.append(db.joinOr([db.if_(u'ClientConsent.endDate IS NULL AND ClientConsent.date IS NOT NULL',
                                    u'DATE_ADD(ClientConsent.date, INTERVAL 12 MONTH) >= %s'%(db.formatDate(begDate)), u'0'),
                                    u'ClientConsent.endDate IS NULL AND ClientConsent.date IS NULL',
                                    table['endDate'].ge(begDate)]))
        if endDate:
            cond.append(db.joinOr([table['date'].isNull(), table['date'].le(endDate)]))
        queryTable = table.innerJoin(tableType, table['clientConsentType_id'].eq(tableType['id']))
        additionalReportData[10][2] = db.getDistinctCount(queryTable, 'ClientConsent.client_id', cond)
        return reportData, additionalReportData


    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        cursor.insertText(u'(7000)')
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        tableColumns = [
            ( '67%', [u'Результат диспансеризации определенных групп взрослого населения', u''], CReportBase.AlignLeft),
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
        reportData, additionalReportData = self.getReportData(query, params)
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
        additionalReportRows = additionalReportData.values()
        additionalReportRows.sort()
        for additionalReportRow in additionalReportRows:
            i = table.addRow()
            table.setText(i, 0, additionalReportRow[0])
            table.setText(i, 1, additionalReportRow[2])
            table.setText(i, 2, additionalReportRow[1])
        return doc

