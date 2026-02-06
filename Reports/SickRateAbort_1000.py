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
        tableEvent['pregnancyWeek'].gt(0),
        tableEvent['pregnancyWeek'].lt(12)
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


class CSickRateAbort_1000(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Раздел II. Прерывание беременности в срок до 12 недель')


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
        reportLine1105 = [0]*5
        accountAccomp = params.get('accountAccomp', False)
        query = selectData(params)
        while query.next():
            record    = query.record()
            MKBRec    = normalizeMKB(forceString(record.value('MKB')))
            sickCount = forceInt(record.value('sickCount'))
            clientAge = forceInt(record.value('clientAge'))
            dopDiagnosisType = forceBool(record.value('dopDiagnosisType'))
            # т. 1000
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
            # т. 1105
            if dopDiagnosisType and MKBRec[:3] == 'O08':
                reportLine1105[0] += sickCount  # Осложнения, вызванные абортом (из стр. 1 гр. 4 табл. 1000): всего  1
                if MKBRec == 'O08.0':
                    reportLine1105[1] += sickCount  # из них инфекция половых путей и тазовых органов (О08.0)  2
                elif MKBRec == 'O08.1':
                    reportLine1105[2] += sickCount  # длительное или массивное кровотечение (О08.1)  3
                elif MKBRec == 'O08.2':
                    reportLine1105[3] += sickCount  # эмболия (О08.2)  4
                elif MKBRec == 'O08.3':
                    reportLine1105[4] += sickCount  # шок (О08.3)  5
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
        cursor.insertText(u'(1000)')
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
        cursor.insertText(u'(1100) Из стр. 4 гр. 4 табл. 1000 – медицинский аборт легальный: 1 __________, '\
            u'из них у женщин, проконсультированных в Центрах медико-социальной поддержки беременных женщин, '\
            u'оказавшихся в трудной жизненной ситуации, или в кабинетах медико-социальной помощи: 2 __________, '\
            u'из числа легальных абортов проведено медикаментозным методом: 3 __________, '\
            u'из числа легальных абортов проведено в возрастной группе: до 14 лет 4 __________, 15 – 17 лет 5 __________.'
        )
        cursor.insertBlock()
        cursor.insertBlock()
        cursor.insertText(u'(1101) Из стр. 4 гр. 4 табл. 1000 – медицинский аборт, проведенный по медицинским показаниям: 1 __________, '\
            u'из них медикаментозным методом  2 __________, из числа абортов по медицинским показаниям проведено в возрастной группе: '\
            u'до 14 лет 3 __________, 15 - 17 лет 4 __________.'
        )
        cursor.insertBlock()
        cursor.insertBlock()
        cursor.insertText(u'(1102) Из стр. 1 гр. 5 табл. 1000: из общего числа абортов, проведенных в возрастной группе до 14 лет: первобеременных 1 __________, ВИЧ-инфицированных 2 __________.')
        cursor.insertBlock()
        cursor.insertBlock()
        cursor.insertText(u'(1103) Из стр. 1 гр. 6 табл. 1000: из общего числа абортов, проведенных в возрастной группе 15 - 17 лет: первобеременных 1 __________, ВИЧ-инфицированных 2 __________.')
        cursor.insertBlock()
        cursor.insertBlock()
        cursor.insertText(u'(1104) Из стр. 9 гр. 4 табл. 1000: из числа неудачных попыток аборта (О07), проведено медикаментозным методом 1 __________.')
        cursor.insertBlock()
        cursor.insertBlock()
        cursor.insertText(u'(1105) Осложнения, вызванные абортом (из стр. 1 гр. 4 табл. 1000): всего 1 - %d, '\
            u'из них: инфекция половых путей и тазовых органов (O08.0) 2 - %d, '\
            u'длительное или массивное кровотечение (O08.1) 3 - %d, '\
            u'эмболия (O08.2) 4 - %d, '\
            u'шок (O08.3) 5 - %d.' % tuple(reportLine1105)
        )
        cursor.insertBlock()
        cursor.movePosition(QtGui.QTextCursor.End)
        return doc
