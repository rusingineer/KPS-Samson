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

from library.Utils import forceInt, forceString, forceBool
from Reports.Report            import CReport
from Reports.ReportBase        import CReportBase, createTable
from Orgs.Utils                import getOrgStructurePersonIdList

from Reports.ReportForm131_o_2000_2021 import CReportForm131SetupDialog2021



MainRows = [
    (u'Определена I группа здоровья',    u'1'),
    (u'Определена II группа здоровья',   u'2'),
    (u'Определена IIIА группа здоровья', u'3'),
    (u'Определена IIIБ группа здоровья', u'4'),
    (u'Направлены при наличии медицинских показаний на дополнительное обследование, не входящее в объем диспансеризации, в том числе направлены на осмотр (консультацию) врачом-онкологом при подозрении на онкологическое заболевание', u'5'),
    (u'Установлено диспансерное наблюдение, всего', u'6'),
    (u'врачом (фельдшером) отделения (кабинета) медицинской профилактики или центра здоровья', u'6.1'),
    (u'врачом-терапевтом',   u'6.2'),
    (u'врачом-специалистом', u'6.3'),
    (u'фельдшером фельдшерского здравпункта или фельдшерско-акушерского пункта', u'6.4'),
    (u'Направлены для получения специализированной, в том числе высокотехнологичной, медицинской помощи', u'7'),
    (u'Направлены на санаторно-курортное лечение', u'8'),
]

def selectData(params):
    begDate = params.get('begDate', QDate())
    endDate = params.get('endDate', QDate())
    orgStructureId = params.get('orgStructureId', None)
    onlyPayedEvents = params.get('onlyPayedEvents', False)
    begPayDate = params.get('begPayDate', QDate())
    endPayDate = params.get('endPayDate', QDate())
    dispType = params.get('dispType', 0)

    if dispType == 0:
        dispTypeList = ['8011', '8008', '8009', '8014', '8015']
    elif dispType == 1:
        dispTypeList = ['8008', '8009', '8014', '8015']
    else:
        dispTypeList = ['8011']

    db = QtGui.qApp.db
    tableEvent = db.table('Event')
    # tableMES = db.table('mes.MES')
    # tableMESGroup = db.table('mes.mrbMESGroup')
    tableClient = db.table('Client')
    tableClientWork = db.table('ClientWork')
    tableClientSocStatus = db.table('ClientSocStatus')
    tableClientSocStatusClass = db.table('rbSocStatusClass')
    tableClientSocStatusType = db.table('rbSocStatusType')
    tableClientConsent = db.table('ClientConsent')
    tableClientConsentType = db.table('rbClientConsentType')
    tableDiagnostic = db.table('Diagnostic')
    tableResult = db.table('rbResult')
    tableDiagnosticResult = db.table('rbDiagnosticResult')
    tableDiagnosis = db.table('Diagnosis')
    tableHealthGroup = db.table('rbHealthGroup')
    tableDispanser = db.table('rbDispanser')
    tableEventType = db.table('EventType')
    tableEventProfile = db.table('rbEventProfile')
    tableAction = db.table('Action')
    tableActionType = db.table('ActionType')
    tableService = db.table('rbService')
    tableServiceIdentification = db.table('rbService_Identification')
    # tableEventIdentification = db.table('EventType_Identification')
    tablePerson = db.table('Person')
    tableSpeciality = db.table('rbSpeciality')
    tablePost = db.table('rbPost')
    tableAccountingSystem = db.table('rbAccountingSystem')

    eventTypeIdList = []

    queryTable = tableEvent
    queryTable = queryTable.innerJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
    queryTable = queryTable.innerJoin(tableEventProfile, tableEventProfile['id'].eq(tableEventType['eventProfile_id']))
    queryTable = queryTable.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
    queryTable = queryTable.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
    queryTable = queryTable.innerJoin(tableService, tableService['id'].eq(tableActionType['nomenclativeService_id']))
    queryTable = queryTable.innerJoin(tableServiceIdentification, tableServiceIdentification['master_id'].eq(tableService['id']))
    queryTable = queryTable.innerJoin(tableAccountingSystem, tableAccountingSystem['id'].eq(tableServiceIdentification['system_id']))

    # queryTable = queryTable.innerJoin(tableEventIdentification, tableEventType['id'].eq(tableEventIdentification['master_id']))
    # queryTable = queryTable.innerJoin(tableAccountingSystem, tableEventIdentification['system_id'].eq(tableAccountingSystem['id']))
    cond = [ tableEventType['deleted'].eq(0),
             tableServiceIdentification['deleted'].eq(0),
             tableEventProfile['code'].inlist(dispTypeList),
             tableAccountingSystem['code'].eq('131o'),
           ]
    stmt = db.selectDistinctStmt(queryTable, tableEventType['id'], cond)
    query = db.query(stmt)
    while query.next():
        eventTypeIdList.append(forceInt(query.value(0)))

    queryTable = tableEvent
    queryTable = queryTable.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
    # queryTable = queryTable.innerJoin(tableMES, tableMES['id'].eq(tableEvent['MES_id']))
    # queryTable = queryTable.innerJoin(tableMESGroup, tableMESGroup['id'].eq(tableMES['group_id']))
    queryTable = queryTable.leftJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
    queryTable = queryTable.leftJoin(tableDiagnostic,
    db.joinAnd([tableDiagnostic['event_id'].eq(tableEvent['id']),
                '''(Diagnostic.`diagnosisType_id` IN (SELECT rbDiagnosisType.id
                                     FROM rbDiagnosisType
                                     WHERE rbDiagnosisType.code = 1))'''
              ]))
    queryTable = queryTable.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
    queryTable = queryTable.leftJoin(tableSpeciality, tableSpeciality['id'].eq(tablePerson['speciality_id']))
    queryTable = queryTable.leftJoin(tablePost, tablePost['id'].eq(tablePerson['post_id']))
    queryTable = queryTable.leftJoin(tableResult, tableResult['id'].eq(tableEvent['result_id']))
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
            tableEventType['id'].inlist(eventTypeIdList),
            # tableMESGroup['code'].eq(u'ДиспанС'),
            # db.joinOr([tableMES['endDate'].isNull(), tableMES['endDate'].dateGe(begDate)]),
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
              'age(Client.`birthDate`, Event.execDate) AS clientAge',
              tableDiagnosis['MKB'],
              u"""
                  EXISTS(SELECT AP.id FROM Action A
                     LEFT JOIN ActionType AType ON A.actionType_id = AType.id
                     LEFT JOIN ActionProperty AP ON AP.action_id = A.id
                     LEFT JOIN ActionProperty AP2 ON AP2.action_id = A.id
                     LEFT JOIN ActionProperty_String APS ON AP.id = APS.id
                     LEFT JOIN ActionPropertyType APType ON APType.id = AP.type_id
                      LEFT JOIN ActionPropertyType APType2 ON APType2.id = AP2.type_id    
                     LEFT JOIN ActionProperty_rbSpeciality APSpec ON AP2.id = APSpec.id
                     LEFT JOIN rbSpeciality rbSpec ON APSpec.value = rbSpec.id
                     WHERE AP.deleted = 0 AND AType.deleted = 0
                        AND A.event_id = Event.id 
                        AND AType.flatCode = 'appointments'
                        AND APType.name = 'Назначения: направлен на'
                        AND APType2.name = 'Специальность'
                        AND (APS.value LIKE '%%обследование%%'
                        OR (APS.value LIKE '%%консультацию%%'
                        AND rbSpec.name LIKE '%%онколог%%'))
                     LIMIT 1
                    ) AS personSpeciality
              """,
              tableClient['sex'].alias('clientSex'),
              tableClient['id'].alias('clientId'),
              tableResult['regionalCode'].alias('healthGroupCode'),
              tableDiagnosticResult['code'].alias('diagnosticResultCode'),
              "IF(rbDispanser.code IN ('2', '6'), 1, 0) AS isObserved",
              tableDiagnostic['hospital'],
              tableDiagnostic['sanatorium'],
              '(SELECT COUNT(Action.id) FROM Action WHERE Action.event_id=Event.id AND Action.deleted=0 AND Action.status=6) AS cancelActionCount',
              u"EXISTS(SELECT cs.id FROM Client cs LEFT JOIN ClientSocStatus css ON cs.id = css.client_id LEFT JOIN rbSocStatusType rbSST ON rbSST.`id` = css.`socStatusType_id` LEFT JOIN ClientWork cw ON cw.client_id = cs.id WHERE ((rbSST.code in ('c04', 'с04')  AND css.deleted = 0) OR (ClientWork.post LIKE 'студент%' AND ClientWork.id = (SELECT MAX(id) FROM ClientWork AS CW  WHERE CW.client_id = Client.id AND CW.deleted = 0) )) AND Client.id = cs.id) AS isStudent",
              "IF(ClientWork.id IS NOT NULL AND (ClientWork.org_id IS NOT NULL OR ClientWork.freeInput != ''), 1, 0) AS hasWork",
              '(SELECT ah.KLADRCode FROM ClientAddress cads LEFT JOIN Address ads ON cads.address_id = ads.id LEFT JOIN AddressHouse ah ON ads.house_id = ah.id WHERE cads.id = getClientRegAddressId(Client.id)) AS regAddress',
              '(SELECT ah2.KLADRCode FROM ClientAddress cads2 LEFT JOIN Address ads2 ON cads2.address_id = ads2.id LEFT JOIN AddressHouse ah2 ON ads2.house_id = ah2.id WHERE cads2.id = getClientLocAddressId(Client.id)) AS locAddress',
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

              'EXISTS(SELECT rbDiagnosticResult.id'
              ' FROM Diagnostic AS D'
              ' INNER JOIN rbDiagnosticResult ON rbDiagnosticResult.id = D.result_id'
              ' WHERE D.event_id = Event.id'
              ' AND D.deleted = 0'
              ' AND rbDiagnosticResult.code = \'07\''
              ') AS isResultAdditionDispans',

              'IF(ClientConsent.value = 0 AND rbClientConsentType.code = \'%s\', 1, 0) AS consentRefusal'%(u'Дисп'),

              tablePost['name'].alias('postName'),
              tableSpeciality['name'].alias('specialityName'),
             ]
    stmt = db.selectStmt(queryTable, fields, cond, 'Event.id DESC')
    return db.query(stmt)



class CReportForm131_o_6000_2021(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Общие результаты профилактического медицинского осмотра, диспансеризации (2021)')


    def getSetupDialog(self, parent):
        result = CReportForm131SetupDialog2021(parent)
        result.setTitle(self.title())
        return result


    def getReportData(self, query):
        uniqueClients = set()
        uniqueClientsSanatorium = set()
        uniqueClientsF = set()
        uniqueClientsT = set()
        uniqueClientsS = set()
        uniqueClientsO = set()
        uniqueClientsSocStatus = set()
        clients600 = [ set() for i in xrange(11) ]
        clients = [ set(), set(), set() ]
        reportData = [ [0]*3 for row in MainRows ]
        if not query:
            return reportData, [0]*10

        def isInWorkingAge(clientAge, clientSex):
            if clientSex == 1: # М
                return 16 <= clientAge <= 60
            if clientSex == 2: # Ж
                return 16 <= clientAge <= 55
            return False

        def isOlderWorkingAge(clientAge, clientSex):
            if clientSex == 1: # М
                return clientAge > 60
            if clientSex == 2: # Ж
                return clientAge > 55
            return False

        while query.next():
            record = query.record()
            clientId = forceInt(record.value('clientId'))
            clientAge = forceInt(record.value('clientAge'))
            clientSex = forceInt(record.value('clientSex'))
            isObserved = forceInt(record.value('isObserved'))
            cancelActionCount = forceInt(record.value('cancelActionCount'))
            consentRefusal = forceInt(record.value('consentRefusal'))
            MKB = forceInt(record.value('MKB'))
            healthGroupCode = forceString(record.value('healthGroupCode'))
            hasWork = forceInt(record.value('hasWork'))
            isStudent = forceInt(record.value('isStudent'))
            # specialityCode = forceString(record.value('specialityCode'))
            personSpeciality = forceInt(record.value('personSpeciality'))
            specialityName = forceString(record.value('specialityName'))
            postName = forceString(record.value('postName'))
            diagnosticResultCode = forceString(record.value('diagnosticResultCode'))
            sanatorium = forceInt(record.value('sanatorium'))
            hospital = forceInt(record.value('hospital'))
            socStatusType = forceInt(record.value('socStatusType'))
            isResultAdditionDispans = forceInt(record.value('isResultAdditionDispans'))
            regAddress = forceString(record.value('regAddress'))
            locAddress = forceString(record.value('locAddress'))
            reportLine = None

            rows = []
            if healthGroupCode in ('343', '317'):
                if clientId not in uniqueClients:
                    rows.append(0)
                    uniqueClients.add(clientId)
            if healthGroupCode in ('344', '318', '353'):
                if clientId not in uniqueClients:
                    rows.append(1)
                    uniqueClients.add(clientId)
            if healthGroupCode in ('373', '355', '357'):
                if clientId not in uniqueClients:
                    rows.append(2)
                    uniqueClients.add(clientId)
            if healthGroupCode in ('374', '356', '358'):
                if clientId not in uniqueClients:
                    rows.append(3)
                    uniqueClients.add(clientId)

            if personSpeciality:
                if clientId not in uniqueClientsO:
                    rows.append(4)
                    uniqueClientsO.add(clientId)

            if isObserved:
                if (specialityName.find(u'Терап') != -1 or specialityName.find(u'терап') != -1) and (postName.find(u'фельдшер') == -1 and postName.find(u'Фельдшер') == -1):
                    if clientId not in uniqueClientsT:
                        uniqueClientsT.add(clientId)
                        rows.append(7)
                if (specialityName.find(u'Терап') == -1 and specialityName.find(u'терап') == -1) and (postName.find(u'фельдшер') == -1 and postName.find(u'Фельдшер') == -1):
                    if clientId not in uniqueClientsS:
                        uniqueClientsS.add(clientId)
                        rows.append(8)
                if postName.find(u'фельдшер') != -1 or postName.find(u'Фельдшер') != -1:
                    if clientId not in uniqueClientsF:
                        uniqueClientsF.add(clientId)
                        rows.append(9)
            if (hospital > 1 and healthGroupCode in ('4', '5')) or diagnosticResultCode == '10':
                rows.append(10)
            # if sanatorium > 1:
            if sanatorium > 1 or diagnosticResultCode == '11':
                if clientId not in uniqueClientsSanatorium:
                    uniqueClientsSanatorium.add(clientId)
                    rows.append(11)

            for row in rows:
                reportLine = reportData[row]
                reportLine[0] += 1
                if isInWorkingAge(clientAge, clientSex):
                    reportLine[1] += 1
                if isOlderWorkingAge(clientAge, clientSex):
                    reportLine[2] += 1

            # if MKB or isResultAdditionDispans:
            #     clients[0].add(clientId)
            #     if isInWorkingAge(clientAge, clientSex):
            #         clients[1].add(clientId)
            #     if isOlderWorkingAge(clientAge, clientSex):
            #         clients[2].add(clientId)

            if clientId not in uniqueClientsSocStatus:
                if hasWork and not isStudent:
                    clients600[1].add(clientId)
                    uniqueClientsSocStatus.add(clientId)
                if not hasWork and not isStudent:
                    clients600[2].add(clientId)
                    uniqueClientsSocStatus.add(clientId)
                if isStudent:
                    clients600[3].add(clientId)
                    uniqueClientsSocStatus.add(clientId)
            if socStatusType in (1,10,11,12,2,20,3,30,4,40,5,50,60,61,8,81,82,83):
                clients600[4].add(clientId)
            if cancelActionCount > 0:
                clients600[8].add(clientId)
            # if consentRefusal:
            #     clients600[9].add(clientId)
            if forceBool(locAddress) and locAddress[8:11] != '000':
                clients600[10].add(clientId)
            elif forceBool(regAddress) and regAddress[8:11] != '000':
                clients600[10].add(clientId)

        # for col in xrange(len(clients)):
        #     reportData[4][col] = len(clients[col])

        reportLine = reportData[5]
        for col in xrange(len(reportLine)):  # сумма строк 6.1 - 6.4
            reportLine[col] += reportData[6][col]
            reportLine[col] += reportData[7][col]
            reportLine[col] += reportData[8][col]
            reportLine[col] += reportData[9][col]

        return reportData, [len(i) for i in clients600]



    def build(self, params):
        query = selectData(params)
        reportData, clients600 = self.getReportData(query)

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        cursor.insertText('(6000)')
        cursor.insertBlock()
        tableColumns = [
            ('35%',  [u'Общие результаты', u'', u'', u'1'], CReportBase.AlignLeft),
            ('5%',   [u'№ строки', u'', u'', u'2'], CReportBase.AlignLeft),
            ('20%',  [u'Число лиц взрослого населения:', u'всего', u'', u'3'], CReportBase.AlignRight),
            ('20%',  [u'', u'в том числе:', u'В трудоспособном возрасте', u'4'], CReportBase.AlignRight),
            ('20%',  [u'', u'', u'В возрасте старше трудоспособного', u'5'], CReportBase.AlignRight),
        ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0,0, 3,1)
        table.mergeCells(0,1, 3,1)
        table.mergeCells(0,2, 1,3)
        table.mergeCells(1,2, 2,1)
        table.mergeCells(1,3, 1,2)

        for row, rowDescr in enumerate(MainRows):
            reportLine = reportData[row]
            i = table.addRow()
            table.setText(i, 0, rowDescr[0])
            table.setText(i, 1, rowDescr[1])
            for col, value in enumerate(reportLine):
                table.setText(i, 2+col, value)

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()

        def writeInfoCode(code):
            table = createTable(cursor, [('50%', [''], CReportBase.AlignLeft), ('50%', [''], CReportBase.AlignLeft)])
            fmt = table.table.format()
            fmt.setBorder(0)
            table.table.setFormat(fmt)
            table.setText(0, 0, code)
            table.setText(0, 1, u'Код по ОКЕИ: человек - 792')
            cursor.movePosition(QtGui.QTextCursor.End)

        writeInfoCode(u'(6001)')
        cursor.insertBlock()
        cursor.insertText(u'Общее число работающих лиц, прошедших профилактический медицинский осмотр, диспансеризацию ')
        cursor.insertText(str(clients600[1]))

        writeInfoCode(u'(6002)')
        cursor.insertBlock()
        cursor.insertText(u'Общее число неработающих лиц, прошедших профилактический медицинский осмотр, диспансеризацию ')
        cursor.insertText(str(clients600[2]))

        writeInfoCode(u'(6003)')
        cursor.insertBlock()
        cursor.insertText(u'Общее число лиц, обучающихся в образовательных организациях по очной форме, прошедших профилактический медицинский осмотр, диспансеризацию ')
        cursor.insertText(str(clients600[3]))

        writeInfoCode(u'(6004)')
        cursor.insertBlock()
        cursor.insertText(u'Общее число лиц, имеющих право на получение государственной социальной помощи в виде набора социальных услуг, прошедших профилактический медицинский осмотр, диспансеризацию ')
        cursor.insertText(str(clients600[4]))

        writeInfoCode(u'(6005)')
        cursor.insertBlock()
        cursor.insertText(u'Общее число лиц, принадлежащих к коренным малочисленным народам Севера, Сибири и Дальнего Востока Российской Федерации, прошедших профилактический медицинский осмотр, диспансеризацию _______')

        writeInfoCode(u'(6006)')
        cursor.insertBlock()
        cursor.insertText(u'Общее число мобильных медицинских бригад, принимавших участие в проведении профилактического медицинского осмотра, диспансеризации _______')

        writeInfoCode(u'(6007)')
        cursor.insertBlock()
        cursor.insertText(u'Общее число лиц, профилактический медицинский осмотр или первый этап диспансеризация которых были проведены мобильными медицинскими бригадами _______')

        writeInfoCode(u'(6008)')
        cursor.insertBlock()
        cursor.insertText(u'Число лиц с отказами от прохождения отдельных медицинских мероприятий в рамках профилактического медицинского осмотра, диспансеризации ')
        cursor.insertText(str(clients600[8]))

        writeInfoCode(u'(6009)')
        cursor.insertBlock()
        cursor.insertText(u'Число лиц с отказами от прохождения профилактического медицинского осмотра в целом, от диспансеризации в целом ')
        cursor.insertText(str(clients600[9]))

        writeInfoCode(u'(6010)')
        cursor.insertBlock()
        cursor.insertText(u'Число лиц, проживающих в сельской местности, прошедших профилактический медицинский осмотр, диспансеризацию ')
        cursor.insertText(str(clients600[10]))

        return doc

