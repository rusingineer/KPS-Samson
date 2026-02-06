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

from library.database   import addDateInRange
from library.MapCode    import createMapCodeToRowIdx
from library.Utils      import forceBool, forceInt, forceString
from Events.ActionServiceType import CActionServiceType
from Reports.Report     import CReport, normalizeMKB
from Reports.ReportBase import CReportBase, createTable
from Reports.ReportAcuteInfections import CReportAcuteInfectionsSetupDialog
from Orgs.Utils         import getOrgStructureDescendants


MainRows = [
    ( u'Число прерываний беременности в срок до 12 недель, всего ', u'1', u'O02-O06'),
    ( u'в том числе (из стр. 1): другие анормальные продукты зачатия', u'2', u'O02'),
    ( u'самопроизвольный аборт', u'3', u'O03'),
    ( u'медицинский аборт', u'4', u'O04'),
    ( u'другие виды аборта', u'5', u'O05'),
    ( u'аборт неуточненный', u'6', u'O06'),
    ( u'Кроме того: внематочная беременность', u'7', u'O00'),
    ( u'пузырный занос', u'8', u'O01'),
    ( u'неудачная попытка аборта', u'9', u'O07')
]


def selectData(params):
    begDate            = params.get('begDate', QDate())
    endDate            = params.get('endDate', QDate())
    eventPurposeId     = params.get('eventPurposeId', None)
    eventTypeId        = params.get('eventTypeId', None)
    orgStructureId     = params.get('orgStructureId', None)
    personId           = params.get('personId', None)
    sex                = params.get('sex', 0)
    ageFrom            = params.get('ageFrom', 0)
    ageTo              = params.get('ageTo', 150)
    socStatusClassId   = params.get('socStatusClassId', None)
    socStatusTypeId    = params.get('socStatusTypeId', None)
    MKBFilter          = params.get('MKBFilter', 0)
    MKBFrom            = params.get('MKBFrom', '')
    MKBTo              = params.get('MKBTo', '')
    MKBExFilter        = params.get('MKBExFilter', 0)
    MKBExFrom          = params.get('MKBExFrom', '')
    MKBExTo            = params.get('MKBExTo', '')
    accountAccomp      = params.get('accountAccomp', False)
    locality           = params.get('locality', 0)

    db = QtGui.qApp.db
    tableDiagnostic       = db.table('Diagnostic')
    tableDiagnosis        = db.table('Diagnosis')
    tableDiagnosisType    = db.table('rbDiagnosisType')
    tableClient           = db.table('Client')
    tablePerson           = db.table('Person')
    tableEvent            = db.table('Event')
    tableEventType        = db.table('EventType')
    tableClientAddress    = db.table('ClientAddress')
    tableAddress          = db.table('Address')
    tableAddressHouse     = db.table('AddressHouse')

    queryTable = tableDiagnostic.leftJoin(tableDiagnosis, tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']))
    queryTable = queryTable.leftJoin(tableDiagnosisType, tableDiagnosisType['id'].eq(tableDiagnostic['diagnosisType_id']))
    queryTable = queryTable.leftJoin(tableClient, tableClient['id'].eq(tableDiagnosis['client_id']))
    queryTable = queryTable.leftJoin(tableEvent, tableEvent['id'].eq(tableDiagnostic['event_id']))

    cond = [
        tableDiagnostic['deleted'].eq(0),
        tableDiagnosis['MKB'].ge(u'O00'),
        tableDiagnosis['MKB'].lt(u'O09'),
        tableEvent['deleted'].eq(0),
        tableEvent['pregnancyWeek'].ge(12),
        tableEvent['pregnancyWeek'].lt(22)
    ]
    cond.append(db.joinOr([tableDiagnosis['setDate'].isNull(), tableDiagnosis['setDate'].le(endDate)]))

    addDateInRange(cond, tableDiagnostic['setDate'], begDate, endDate)
    isPersonPost = params.get('isPersonPost', 0)
    if isPersonPost:
        tableRBPost = db.table('rbPost')
        queryTable = queryTable.innerJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
        queryTable = queryTable.innerJoin(tableRBPost, tableRBPost['id'].eq(tablePerson['post_id']))
        cond.append(tablePerson['deleted'].eq(0))
        if isPersonPost == 1:
            cond.append('''LEFT(rbPost.code, 1) IN ('1','2','3') ''')
        elif isPersonPost == 2:
            cond.append('''LEFT(rbPost.code, 1) IN ('4','5','6','7','8','9')''')
    if personId:
        cond.append(tableDiagnostic['person_id'].eq(personId))
    elif orgStructureId:
        if not isPersonPost:
            queryTable = queryTable.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
        cond.append(tablePerson['orgStructure_id'].inlist(getOrgStructureDescendants(orgStructureId)))
    else:
        if not isPersonPost:
            queryTable = queryTable.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
        cond.append(tablePerson['org_id'].eq(QtGui.qApp.currentOrgId()))
    if eventTypeId:
        cond.append(tableEvent['eventType_id'].eq(eventTypeId))
    if eventPurposeId:
        queryTable = queryTable.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
        cond.append(tableEventType['purpose_id'].eq(eventPurposeId))
    if sex:
        cond.append(tableClient['sex'].eq(sex))
    if ageFrom <= ageTo:
        cond.append('Diagnosis.endDate >= ADDDATE(Client.birthDate, INTERVAL %d YEAR)'%ageFrom)
        cond.append('Diagnosis.endDate < SUBDATE(ADDDATE(Client.birthDate, INTERVAL %d YEAR),1)'%(ageTo+1))
    if socStatusTypeId:
        subStmt = ('SELECT ClientSocStatus.id FROM ClientSocStatus WHERE '
                  +'ClientSocStatus.deleted=0 AND ClientSocStatus.client_id=Client.id AND '
                  +'ClientSocStatus.socStatusType_id=%d' % socStatusTypeId)
        cond.append('EXISTS('+subStmt+')')
    elif socStatusClassId:
        subStmt = ('SELECT ClientSocStatus.id FROM ClientSocStatus WHERE '
                  +'ClientSocStatus.deleted=0 AND ClientSocStatus.client_id=Client.id AND '
                  +'ClientSocStatus.socStatusClass_id=%d' % socStatusClassId)
        cond.append('EXISTS('+subStmt+')')
    if MKBFilter == 1:
        cond.append(tableDiagnosis['MKB'].ge(MKBFrom))
        cond.append(tableDiagnosis['MKB'].le(MKBTo))
    else:
        cond.append(tableDiagnosis['MKB'].lt('Z'))
    if MKBExFilter == 1:
        cond.append(tableDiagnosis['MKBEx'].ge(MKBExFrom))
        cond.append(tableDiagnosis['MKBEx'].le(MKBExTo))
    if not accountAccomp:
        cond.append(tableDiagnosisType['code'].inlist(['1', '2', '3', '4', '9']))
    if locality:
        # 1: горожане, isClientVillager == 0 или NULL
        # 2: сельские жители, isClientVillager == 1
        cond.append('IFNULL(isClientVillager(Client.id), 0) = %d' % (locality-1))
    filterAddress = params.get('isFilterAddress', False)
    if filterAddress:
        filterAddressType = params.get('filterAddressType', 0)
        filterAddressCity = params.get('filterAddressCity', None)
        filterAddressStreet = params.get('filterAddressStreet', None)
        filterAddressHouse = params.get('filterAddressHouse', u'')
        filterAddressCorpus = params.get('filterAddressCorpus', u'')
        filterAddressFlat = params.get('filterAddressFlat', u'')
        queryTable = queryTable.leftJoin(tableClientAddress, tableClient['id'].eq(tableClientAddress['client_id']))
        cond.append(tableClientAddress['type'].eq(filterAddressType))
        cond.append(db.joinOr([tableClientAddress['id'].isNull(), tableClientAddress['deleted'].eq(0)]))
        if filterAddressCity or filterAddressStreet or filterAddressHouse or filterAddressCorpus or filterAddressFlat:
            queryTable = queryTable.leftJoin(tableAddress, tableClientAddress['address_id'].eq(tableAddress['id']))
            queryTable = queryTable.leftJoin(tableAddressHouse, tableAddress['house_id'].eq(tableAddressHouse['id']))
            cond.append(db.joinOr([tableAddress['id'].isNull(), tableAddress['deleted'].eq(0)]))
            cond.append(db.joinOr([tableAddressHouse['id'].isNull(), tableAddressHouse['deleted'].eq(0)]))
        if filterAddressCity:
            cond.append(tableAddressHouse['KLADRCode'].like(filterAddressCity))
        if filterAddressStreet:
            cond.append(tableAddressHouse['KLADRStreetCode'].like(filterAddressStreet))
        if filterAddressHouse:
            cond.append(tableAddressHouse['number'].eq(filterAddressHouse))
        if filterAddressCorpus:
            cond.append(tableAddressHouse['corpus'].eq(filterAddressCorpus))
        if filterAddressFlat:
            cond.append(tableAddress['flat'].eq(filterAddressFlat))

    stmt="""
    SELECT
       Diagnosis.MKB AS MKB,
       COUNT(distinct Event.id) AS sickCount,
       age(Client.birthDate, coalesce(Diagnosis.setDate, Diagnosis.endDate, Event.setDate)) as clientAge,
       IF(rbDiagnosisType.code = '3', 1, 0) AS dopDiagnosisType
    FROM %s
    WHERE Diagnosis.deleted=0 AND Diagnosis.mod_id IS NULL AND %s
    GROUP BY MKB, clientAge, dopDiagnosisType
        """ % (db.getTableName(queryTable),
               db.joinAnd(cond))
    return db.query(stmt)


def selectData3000(params):
    begDate            = params.get('begDate', QDate())
    endDate            = params.get('endDate', QDate())
    eventPurposeId     = params.get('eventPurposeId', None)
    eventTypeId        = params.get('eventTypeId', None)
    orgStructureId     = params.get('orgStructureId', None)
    personId           = params.get('personId', None)
    sex                = params.get('sex', 0)
    ageFrom            = params.get('ageFrom', 0)
    ageTo              = params.get('ageTo', 150)
    socStatusClassId   = params.get('socStatusClassId', None)
    socStatusTypeId    = params.get('socStatusTypeId', None)
    MKBFilter          = params.get('MKBFilter', 0)
    MKBFrom            = params.get('MKBFrom', '')
    MKBTo              = params.get('MKBTo', '')
    MKBExFilter        = params.get('MKBExFilter', 0)
    MKBExFrom          = params.get('MKBExFrom', '')
    MKBExTo            = params.get('MKBExTo', '')
    accountAccomp      = params.get('accountAccomp', False)
    locality           = params.get('locality', 0)

    db = QtGui.qApp.db
    tableDiagnosis        = db.table('Diagnosis')
    tableDiagnosisType    = db.table('rbDiagnosisType')
    tableClient           = db.table('Client')
    tableDiagnostic       = db.table('Diagnostic')
    tablePerson           = db.table('Person')
    tableEvent            = db.table('Event')
    tableEventType        = db.table('EventType')
    tableClientAddress    = db.table('ClientAddress')
    tableAddress          = db.table('Address')
    tableAddressHouse     = db.table('AddressHouse')

    queryTable = tableDiagnosis.leftJoin(tableClient, tableDiagnosis['client_id'].eq(tableClient['id']))
    queryTable = queryTable.leftJoin(tableDiagnosisType, tableDiagnosis['diagnosisType_id'].eq(tableDiagnosisType['id']))

    cond = [tableDiagnosis['MKB'].ge(u'O02'),
            tableDiagnosis['MKB'].lt(u'O07')
            ]
    cond.append(db.joinOr([tableDiagnosis['setDate'].isNull(), tableDiagnosis['setDate'].le(endDate)]))

    diagnosticQuery = tableDiagnostic
    diagnosticQuery = diagnosticQuery.leftJoin(tableEvent, tableEvent['id'].eq(tableDiagnostic['event_id']))
    diagnosticCond = [ tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']),
                       tableDiagnostic['deleted'].eq(0)
                     ]
    addDateInRange(diagnosticCond, tableDiagnostic['setDate'], begDate, endDate)
    isPersonPost = params.get('isPersonPost', 0)
    if isPersonPost:
        tableRBPost = db.table('rbPost')
        diagnosticQuery = diagnosticQuery.innerJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
        diagnosticQuery = diagnosticQuery.innerJoin(tableRBPost, tableRBPost['id'].eq(tablePerson['post_id']))
        diagnosticCond.append(tablePerson['deleted'].eq(0))
        if isPersonPost == 1:
            diagnosticCond.append('''LEFT(rbPost.code, 1) IN ('1','2','3') ''')
        elif isPersonPost == 2:
            diagnosticCond.append('''LEFT(rbPost.code, 1) IN ('4','5','6','7','8','9')''')
    if personId:
        diagnosticCond.append(tableDiagnostic['person_id'].eq(personId))
    elif orgStructureId:
        if not isPersonPost:
            diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
        diagnosticCond.append(tablePerson['orgStructure_id'].inlist(getOrgStructureDescendants(orgStructureId)))
    else:
        if not isPersonPost:
            diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
        diagnosticCond.append(tablePerson['org_id'].eq(QtGui.qApp.currentOrgId()))
    if eventTypeId:
        diagnosticCond.append(tableEvent['eventType_id'].eq(eventTypeId))
    if eventPurposeId:
        diagnosticQuery = diagnosticQuery.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
        diagnosticCond.append(tableEventType['purpose_id'].eq(eventPurposeId))
    cond.append(db.existsStmt(diagnosticQuery, diagnosticCond))

    if sex:
        cond.append(tableClient['sex'].eq(sex))
    if ageFrom <= ageTo:
        cond.append('Diagnosis.endDate >= ADDDATE(Client.birthDate, INTERVAL %d YEAR)'%ageFrom)
        cond.append('Diagnosis.endDate < SUBDATE(ADDDATE(Client.birthDate, INTERVAL %d YEAR),1)'%(ageTo+1))
    if socStatusTypeId:
        subStmt = ('SELECT ClientSocStatus.id FROM ClientSocStatus WHERE '
                  +'ClientSocStatus.deleted=0 AND ClientSocStatus.client_id=Client.id AND '
                  +'ClientSocStatus.socStatusType_id=%d' % socStatusTypeId)
        cond.append('EXISTS('+subStmt+')')
    elif socStatusClassId:
        subStmt = ('SELECT ClientSocStatus.id FROM ClientSocStatus WHERE '
                  +'ClientSocStatus.deleted=0 AND ClientSocStatus.client_id=Client.id AND '
                  +'ClientSocStatus.socStatusClass_id=%d' % socStatusClassId)
        cond.append('EXISTS('+subStmt+')')
    if MKBFilter == 1:
        cond.append(tableDiagnosis['MKB'].ge(MKBFrom))
        cond.append(tableDiagnosis['MKB'].le(MKBTo))
    else:
        cond.append(tableDiagnosis['MKB'].lt('Z'))
    if MKBExFilter == 1:
        cond.append(tableDiagnosis['MKBEx'].ge(MKBExFrom))
        cond.append(tableDiagnosis['MKBEx'].le(MKBExTo))
    if not accountAccomp:
        cond.append(tableDiagnosisType['code'].inlist(['1', '2', '4']))
    if locality:
        # 1: горожане, isClientVillager == 0 или NULL
        # 2: сельские жители, isClientVillager == 1
        cond.append('IFNULL(isClientVillager(Client.id), 0) = %d' % (locality-1))
    filterAddress = params.get('isFilterAddress', False)
    if filterAddress:
        filterAddressType = params.get('filterAddressType', 0)
        filterAddressCity = params.get('filterAddressCity', None)
        filterAddressStreet = params.get('filterAddressStreet', None)
        filterAddressHouse = params.get('filterAddressHouse', u'')
        filterAddressCorpus = params.get('filterAddressCorpus', u'')
        filterAddressFlat = params.get('filterAddressFlat', u'')
        queryTable = queryTable.leftJoin(tableClientAddress, tableClient['id'].eq(tableClientAddress['client_id']))
        cond.append(tableClientAddress['type'].eq(filterAddressType))
        cond.append(db.joinOr([tableClientAddress['id'].isNull(), tableClientAddress['deleted'].eq(0)]))
        if filterAddressCity or filterAddressStreet or filterAddressHouse or filterAddressCorpus or filterAddressFlat:
            queryTable = queryTable.leftJoin(tableAddress, tableClientAddress['address_id'].eq(tableAddress['id']))
            queryTable = queryTable.leftJoin(tableAddressHouse, tableAddress['house_id'].eq(tableAddressHouse['id']))
            cond.append(db.joinOr([tableAddress['id'].isNull(), tableAddress['deleted'].eq(0)]))
            cond.append(db.joinOr([tableAddressHouse['id'].isNull(), tableAddressHouse['deleted'].eq(0)]))
        if filterAddressCity:
            cond.append(tableAddressHouse['KLADRCode'].like(filterAddressCity))
        if filterAddressStreet:
            cond.append(tableAddressHouse['KLADRStreetCode'].like(filterAddressStreet))
        if filterAddressHouse:
            cond.append(tableAddressHouse['number'].eq(filterAddressHouse))
        if filterAddressCorpus:
            cond.append(tableAddressHouse['corpus'].eq(filterAddressCorpus))
        if filterAddressFlat:
            cond.append(tableAddress['flat'].eq(filterAddressFlat))
    cond.append(u'''EXISTS(SELECT APS.id
        FROM Action
        INNER JOIN ActionProperty AS AP ON Action.id = AP.action_id
        INNER JOIN ActionType ON Action.actionType_id = ActionType.id
        INNER JOIN ActionPropertyType AS APT ON AP.type_id=APT.id
        INNER JOIN ActionProperty_String AS APS ON APS.id=AP.id
        WHERE APT.actionType_id=Action.actionType_id
        AND Action.deleted = 0
        AND ActionType.deleted = 0
        AND ActionType.serviceType = '%d'
        AND Action.event_id IN (SELECT Diagnostic.event_id
        FROM Diagnostic
        WHERE (Diagnostic.diagnosis_id=Diagnosis.id) AND (Diagnostic.deleted=0)
        GROUP BY Diagnostic.event_id)
        AND APT.deleted=0 AND AP.deleted=0 AND APT.name = 'Исход операции' AND (APS.value LIKE 'умер%%' OR APS.value LIKE 'смерть%%')
        )''' % CActionServiceType.operation)
    stmt="""
    SELECT
       Diagnosis.MKB AS MKB,
       COUNT(*) AS sickCount,
       age(Client.birthDate, IF(Diagnosis.setDate IS NOT NULL, DATE(Diagnosis.setDate),
       IF(Diagnosis.endDate IS NOT NULL, DATE(Diagnosis.endDate),
       (SELECT DATE(Event.setDate)
       FROM Diagnostic INNER JOIN Event ON Event.`id`=Diagnostic.`event_id`
       WHERE (Diagnostic.`diagnosis_id`=Diagnosis.`id`) AND (Diagnostic.`deleted`=0)
       LIMIT 1)))) AS clientAge,
       (EXISTS(SELECT Event.id
               FROM Diagnostic INNER JOIN Event ON Event.`id`=Diagnostic.`event_id`
               WHERE (Event.`deleted`=0) AND (Diagnostic.`diagnosis_id`=Diagnosis.`id`)
               AND (Diagnostic.`deleted`=0) AND (Event.`pregnancyWeek` >= 0) AND (Event.`pregnancyWeek` < 12) )) AS pregnancyWeek0to12,
       (EXISTS(SELECT Event.id
               FROM Diagnostic INNER JOIN Event ON Event.`id`=Diagnostic.`event_id`
               WHERE (Event.`deleted`=0) AND (Diagnostic.`diagnosis_id`=Diagnosis.`id`)
               AND (Diagnostic.`deleted`=0) AND (Event.`pregnancyWeek` >= 12) AND (Event.`pregnancyWeek` < 22) )) AS pregnancyWeek12to22
    FROM %s
    WHERE Diagnosis.deleted=0 AND Diagnosis.mod_id IS NULL AND %s
    GROUP BY MKB, clientAge, pregnancyWeek0to12, pregnancyWeek12to22
        """ % (db.getTableName(queryTable),
               db.joinAnd(cond))
    return db.query(stmt)


class CSickRateAbort_2000(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Раздел III. Прерывание беременности в срок с 12 до 22 недель')


    def getSetupDialog(self, parent):
        result = CReportAcuteInfectionsSetupDialog(parent)
        result.setAccountAccompEnabled(True)
        result.setRegisteredInPeriod(False)
        result.setUseInputDate(False)
        result.setTitle(self.title())
        return result


    def build(self, params):
        rowSize = 8
        mapMainRows = createMapCodeToRowIdx( [row[2] for row in MainRows] )
        reportMainData = [ [0]*rowSize for row in xrange(len(MainRows)) ]
        reportLine2105 = [0]*5
        accountAccomp = params.get('accountAccomp', False)
        query = selectData(params)
        while query.next():
            record    = query.record()
            MKBRec    = normalizeMKB(forceString(record.value('MKB')))
            sickCount = forceInt(record.value('sickCount'))
            clientAge = forceInt(record.value('clientAge'))
            dopDiagnosisType = forceBool(record.value('dopDiagnosisType'))
            # т. 2000
            for row in mapMainRows.get(MKBRec, []):
                if not dopDiagnosisType or accountAccomp:
                    reportLine = reportMainData[row]
                    reportLine[0] += sickCount  # Всего
                    if clientAge <= 14:
                        reportLine[1] += sickCount  # в том числе в возрасте (лет): 0 - 14
                    if clientAge >= 15 and clientAge <= 17:
                        reportLine[2] += sickCount  # 15 - 17
                    if clientAge >= 18 and clientAge <= 44:
                        reportLine[3] += sickCount  # 18 - 44
                    if clientAge >= 45 and clientAge <= 49:
                        reportLine[4] += sickCount  # 45 - 49
                    if clientAge >= 50:
                        reportLine[5] += sickCount  # 50 лет и старше
            # т. 2105
            if dopDiagnosisType and MKBRec[:3] == 'O08':
                reportLine2105[0] += sickCount  # Осложнения, вызванные абортом (из стр. 1 гр. 4 табл. 1000): всего 1
                if MKBRec == 'O08.0':
                    reportLine2105[1] += sickCount  # из них инфекция половых путей и тазовых органов (О08.0) 2
                elif MKBRec == 'O08.1':
                    reportLine2105[2] += sickCount  # длительное или массивное кровотечение (О08.1) 3
                elif MKBRec == 'O08.2':
                    reportLine2105[3] += sickCount  # эмболия (О08.2) 4
                elif MKBRec == 'O08.3':
                    reportLine2105[4] += sickCount  # шок (О08.3) 5
        # т. 3000
        reportLine3000 = [0]*3
        query = selectData3000(params)
        while query.next():
            record    = query.record()
            MKBRec    = normalizeMKB(forceString(record.value('MKB')))
            sickCount = forceInt(record.value('sickCount'))
            clientAge = forceInt(record.value('clientAge'))
            pregnancyWeek0to12 = forceBool(record.value('pregnancyWeek0to12'))
            pregnancyWeek12to22 = forceBool(record.value('pregnancyWeek12to22'))
            reportLine3000[0] += sickCount  # Число женщин, умерших от прерывания беременности (О02-О06) всего 1
            if pregnancyWeek0to12:
                reportLine3000[1] += sickCount  # из них в сроки: до 12 недель 2
            if pregnancyWeek12to22:
                reportLine3000[2] += sickCount  # с 12 до 22 недель 3
        # now text
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        if params.get('isFilterAddress', False):
            self.dumpParamsAdress(cursor, params)
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        cursor.insertText(u'(2000)')
        cursor.insertBlock()
        tableColumns = [
            ('25%', [u'Наименование',                  u'',                     u'1'], CReportBase.AlignLeft),
            ('5%',  [u'№ строки',                      u'',                     u'2'], CReportBase.AlignLeft),
            ('10%', [u'Код по МКБ-10',                 u'',                     u'3'], CReportBase.AlignLeft),
            ('7.5%',[u'Всего',                         u'',                     u'4'], CReportBase.AlignRight),
            ('7.5%',[u'в том числе в возрасте (лет):', u'0 - 14',               u'5'], CReportBase.AlignRight),
            ('7.5%',[u'',                              u'15 - 17',              u'6'], CReportBase.AlignRight),
            ('7.5%',[u'',                              u'18 - 44',              u'7'], CReportBase.AlignRight),
            ('7.5%',[u'',                              u'45 - 49',              u'8'], CReportBase.AlignRight),
            ('7.5%',[u'',                              u'50 лет и старше',      u'9'], CReportBase.AlignRight),
            ('7.5%',[u'из гр. 4:',                     u'у первобеременных',    u'10'], CReportBase.AlignRight),
            ('7.5%',[u'',                              u'у ВИЧ-инфицированных', u'11'], CReportBase.AlignRight)
            ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 3, 1) # Наименование
        table.mergeCells(0, 1, 3, 1) # №
        table.mergeCells(0, 2, 3, 1) # Код МКБ
        table.mergeCells(0, 3, 3, 1) # Всего
        table.mergeCells(0, 4, 1, 5) #
        table.mergeCells(0, 9, 1, 2) #

        for row, rowDescr in enumerate(MainRows):
            reportLine = reportMainData[row]
            i = table.addRow()
            table.setText(i, 0, rowDescr[0])
            table.setText(i, 1, rowDescr[1])
            table.setText(i, 2, rowDescr[2])
            for j, val in enumerate(reportLine):
                if j in [6, 7]:
                    val = u'-'
                table.setText(i, j+3, val)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertBlock()
        cursor.insertText(u'(2100) Из стр. 4 гр. 4 табл. 2000 – медицинский аборт, проведенный по социальным показаниям: 1 __________, '\
            u'из них медикаментозным методом  2 __________, из числа абортов по социальным показаниям проведено в возрастной группе: '\
            u'до 14 лет 3 __________, 15 - 17 лет 4 __________.'
        )
        cursor.insertBlock()
        cursor.insertBlock()
        cursor.insertText(u'(2101) Из стр. 4 гр. 4 табл. 2000 – медицинский аборт, проведенный медикаментозным методом: 1 __________.')
        cursor.insertBlock()
        cursor.insertBlock()
        cursor.insertText(u'(2102) Из стр. 1 гр. 5 табл. 2000: из общего числа абортов, проведенных в возрастной группе до 14 лет: первобеременных 1 __________, ВИЧ-инфицированных 2 __________.')
        cursor.insertBlock()
        cursor.insertBlock()
        cursor.insertText(u'(2103) Из стр. 1 гр. 6 табл. 2000: из общего числа абортов, проведенных в возрастной группе 15 - 17 лет: первобеременных 1 __________, ВИЧ-инфицированных 2 __________.')
        cursor.insertBlock()
        cursor.insertBlock()
        cursor.insertText(u'(2104) Из стр. 9 гр. 4 табл. 2000: из числа неудачных попыток аборта (О07), проведено медикаментозным методом 1 __________.')
        cursor.insertBlock()
        cursor.insertBlock()
        cursor.insertText(u'(2105) Осложнения, вызванные абортом (из стр. 1 гр. 4 табл. 2000): всего 1 - %d, '\
            u'из них: инфекция половых путей и тазовых органов (O08.0) 2 - %d, '\
            u'длительное или массивное кровотечение (O08.1) 3 - %d, '\
            u'эмболия (O08.2) 4 - %d, '\
            u'шок (O08.3) 5 - %d.' % tuple(reportLine2105)
        )
        cursor.insertBlock()
        cursor.insertBlock()
        cursor.insertText(u'(3000) Число женщин, умерших от  прерывания беременности  (О02-О06) всего 1 - %d, '\
            u'из них в сроки: до 12 недель 2 - %d, '\
            u'с 12 до 22 недель 3 - %d.' % tuple(reportLine3000)
        )
        cursor.insertBlock()
        cursor.movePosition(QtGui.QTextCursor.End)
        return doc
