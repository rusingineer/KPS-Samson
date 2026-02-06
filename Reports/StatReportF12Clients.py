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
from library.Utils      import forceInt, forceRef, forceString, formatName, formatSex

from Reports.Report     import CReport, normalizeMKB
from Reports.ReportBase import CReportBase, createTable
from Reports.ReportAcuteInfections import CReportAcuteInfectionsSetupDialog, addAttachCond, getFilterAddress
from Orgs.Utils         import getOrgStructureDescendants, getOrgStructureListDescendants, getOrgStructures


def selectData(params):
    registeredInPeriod = params.get('registeredInPeriod', False)
    begDate = params.get('begDate', QDate())
    endDate = params.get('endDate', QDate())
    eventPurposeId = params.get('eventPurposeId', None)
    eventTypeIdList = params.get('eventTypeList', None)
    orgStructureList = params.get('orgStructureList', None)
    personId = params.get('personId', None)
    sex = params.get('sex', 0)
    ageFrom = params.get('ageFrom', 18)
    ageTo = params.get('ageTo', 150)
    socStatusClassId = params.get('socStatusClassId', None)
    socStatusTypeId = params.get('socStatusTypeId', None)
    areaIdEnabled = params.get('areaIdEnabled', None)
    areaId = params.get('areaId', None)
    locality = params.get('locality', 0)
    excludeLeaved = params.get('excludeLeaved', False)
    specialityId = params.get('specialityId', None)
    MKBFilter = params.get('MKBFilter', 0)
    MKBFrom = params.get('MKBFrom', 'A00')
    MKBTo = params.get('MKBTo', 'Z99.9')
    MKBExFilter = params.get('MKBExFilter', 0)
    MKBExFrom = params.get('MKBExFrom', 'A00')
    MKBExTo = params.get('MKBExTo', 'Z99.9')
    filterAddressType = params.get('filterAddressType', 0)

    stmt="""
SELECT
   Client.id AS clientId,
   Client.lastName, Client.firstName, Client.patrName,
   Client.sex,
   Client.birthDate,
   formatClientAddress(ClientAddress.id) AS address,
   Diagnosis.MKB AS MKB,
   Diagnosis.MKBEx AS MKBEx,
   Diagnostic.endDate,
   Diagnostic.hospital,
   rbDispanser.name AS dispanser,
   vrbPerson.name AS person,
   rbSpeciality.name AS speciality

FROM Diagnosis
INNER JOIN Diagnostic ON Diagnostic.diagnosis_id = Diagnosis.id
INNER JOIN Client ON Client.id = Diagnosis.client_id
LEFT JOIN ClientAddress ON (ClientAddress.client_id = Diagnosis.client_id
        AND ClientAddress.deleted = 0
        AND ClientAddress.id = (SELECT MAX(id) FROM ClientAddress AS CA WHERE CA.Type=%d and CA.client_id = Client.id))
LEFT JOIN Address ON (Address.id = ClientAddress.address_id AND Address.deleted = 0)
%s
LEFT JOIN rbDiseaseCharacter ON rbDiseaseCharacter.id = Diagnostic.character_id
INNER JOIN rbDispanser ON rbDispanser.id = Diagnostic.dispanser_id
LEFT JOIN vrbPerson ON vrbPerson.id = Diagnosis.dispanserPerson_id
LEFT JOIN rbSpeciality ON rbSpeciality.id = vrbPerson.speciality_id

WHERE Diagnosis.diagnosisType_id NOT IN (SELECT RBDT.id FROM rbDiagnosisType AS RBDT WHERE RBDT.code = '7' OR RBDT.code = '11')
AND Diagnosis.deleted = 0
AND Client.deleted = 0
AND Diagnostic.deleted = 0
AND rbDispanser.observed = 1
AND Diagnostic.endDate = (SELECT MAX(D2.endDate)
                          FROM Diagnostic AS D2
                          WHERE D2.diagnosis_id = Diagnosis.id AND D2.dispanser_id IS NOT NULL AND  D2.endDate<%s)
AND %s
ORDER BY Client.lastName, Client.firstName, Client.patrName, Diagnosis.MKB, Diagnosis.MKB, Diagnostic.endDate
    """
    db = QtGui.qApp.db
    tableDiagnosis  = db.table('Diagnosis')
    tableDiseaseCharacter = db.table('rbDiseaseCharacter')
    tableClient = db.table('Client')
    tableDiagnosticPR = db.table('Diagnostic')
    tableDiagnostic = db.table('Diagnostic').alias('DC')
    tablePerson = db.table('Person')
    tableEvent = db.table('Event')
    tableOrgStructureAddress = db.table('OrgStructure_Address')
    tableAddress = db.table('Address')

    cond = []
    cond.append(tableDiagnosis['deleted'].eq(0))
    cond.append(tableDiagnosis['mod_id'].isNull())
    cond.append(db.joinOr([tableDiagnosis['setDate'].isNull(), db.joinAnd([tableDiagnosis['setDate'].le(endDate), tableDiagnosis['setDate'].ge(begDate)])]))
    cond.append(db.joinOr([tableDiagnosis['endDate'].ge(begDate), tableDiseaseCharacter['code'].eq('3')]))
    if MKBFilter == 1:
        cond.append(tableDiagnosis['MKB'].ge(MKBFrom))
        cond.append(tableDiagnosis['MKB'].le(MKBTo))
    if MKBExFilter == 1:
        cond.append(tableDiagnosis['MKBEx'].ge(MKBExFrom))
        cond.append(tableDiagnosis['MKBEx'].le(MKBExTo))

    diagnosticQuery = tableDiagnostic
    diagnosticCond = [ tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']),
                       tableDiagnostic['deleted'].eq(0),
                       tableDiagnostic['id'].eq(tableDiagnosticPR['id'])
                     ]

    if registeredInPeriod:
        addDateInRange(diagnosticCond, tableDiagnostic['setDate'], begDate, endDate)
    else:
        diagnosticCond.append(tableDiagnostic['setDate'].le(endDate))
        diagnosticCond.append(db.joinOr([tableDiagnostic['endDate'].ge(begDate), tableDiagnostic['endDate'].isNull()]))
    if specialityId:
        diagnosticQuery = diagnosticQuery.innerJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
        diagnosticCond.append(tablePerson['speciality_id'].eq(specialityId))
        diagnosticCond.append(tablePerson['deleted'].eq(0))
    isPersonPost = params.get('isPersonPost', 0)
    if isPersonPost:
        tableRBPost = db.table('rbPost')
        if not specialityId:
            diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
            diagnosticCond.append(tablePerson['deleted'].eq(0))
        diagnosticQuery = diagnosticQuery.leftJoin(tableRBPost, tableRBPost['id'].eq(tablePerson['post_id']))
        if isPersonPost == 1:
            diagnosticCond.append('''LEFT(rbPost.code, 1) IN ('1','2','3') ''')
        elif isPersonPost == 2:
            diagnosticCond.append('''LEFT(rbPost.code, 1) IN ('4','5','6','7','8','9')''')
    if personId:
        cond.append(tableDiagnosis['dispanserPerson_id'].eq(personId))
    elif orgStructureList:
        if not isPersonPost and not specialityId:
            diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
            diagnosticCond.append(tablePerson['deleted'].eq(0))
        diagnosticCond.append(tablePerson['orgStructure_id'].inlist(getOrgStructureListDescendants(orgStructureList)))
    else:
        if not isPersonPost and not specialityId:
            diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
            diagnosticCond.append(tablePerson['deleted'].eq(0))
        diagnosticCond.append(tablePerson['org_id'].eq(QtGui.qApp.currentOrgId()))
    if eventTypeIdList:
        diagnosticQuery = diagnosticQuery.leftJoin(tableEvent, tableEvent['id'].eq(tableDiagnostic['event_id']))
        diagnosticCond.append(tableEvent['eventType_id'].inlist(eventTypeIdList))
    elif eventPurposeId:
        tableEventType = db.table('EventType')
        diagnosticQuery = diagnosticQuery.leftJoin(tableEvent, tableEvent['id'].eq(tableDiagnostic['event_id']))
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
    if areaIdEnabled:
        if areaId:
            orgStructureIdListArea = getOrgStructureDescendants(areaId)
        else:
            orgStructureIdListArea = getOrgStructures(QtGui.qApp.currentOrgId())
        subCond = [ tableOrgStructureAddress['master_id'].inlist(orgStructureIdListArea),
                    tableOrgStructureAddress['house_id'].eq(tableAddress['house_id']),
                  ]
        cond.append(db.existsStmt(tableOrgStructureAddress, subCond))
    stmtAddress = u''''''
    if locality:
        # 1: горожане, isClientVillager == 0 или NULL
        # 2: сельские жители, isClientVillager == 1
        cond.append('IFNULL(isClientVillager(Client.id), 0) = %d' % (locality-1))
    filterAddress = params.get('isFilterAddress', False)
    if filterAddress:
        stmtAddress = u'''INNER JOIN AddressHouse ON AddressHouse.id = Address.house_id'''
        cond.append('ClientAddress.id IN (%s)'%(getFilterAddress(params)))
    if 'attachTo' in params:
        attachOrgId = params['attachTo']
        if attachOrgId:
            addAttachCond(cond, 'LPU_id=%d'%attachOrgId, *params.get('attachType', (0, None, QDate(), QDate())))
    elif 'attachToNonBase' in params:
        addAttachCond(cond, 'LPU_id!=%d'%QtGui.qApp.currentOrgId(), *params.get('attachType', (0, None, QDate(), QDate())))
    elif 'attachType' in params:
        addAttachCond(cond, '', *params['attachType'])
    excludeLeaved = params.get('excludeLeaved', False)
    if excludeLeaved:
        outerCond = ['ClientAttach.client_id = Client.id']
        innerCond = ['CA2.client_id = Client.id']
        cond.append('''EXISTS (SELECT ClientAttach.id
           FROM ClientAttach
           LEFT JOIN rbAttachType ON rbAttachType.id = ClientAttach.attachType_id
           WHERE ClientAttach.deleted=0
           AND %s
           AND ClientAttach.id in (SELECT MAX(CA2.id)
                       FROM ClientAttach AS CA2
                       LEFT JOIN rbAttachType AS rbAttachType2 ON rbAttachType2.id = CA2.attachType_id
                       WHERE CA2.deleted=0 AND %s))'''% (QtGui.qApp.db.joinAnd(outerCond), QtGui.qApp.db.joinAnd(innerCond)))
        cond.append(tableClient['deathDate'].isNull())
    if 'dead' in params:
        cond.append(tableClient['deathDate'].isNotNull())
        if 'begDeathDate' in params:
            begDeathDate = params['begDeathDate']
            if begDeathDate:
                cond.append(tableClient['deathDate'].ge(begDeathDate))
        if 'endDeathDate' in params:
            endDeathDate = params['endDeathDate']
            if endDeathDate:
                cond.append(tableClient['deathDate'].lt(endDeathDate.addDays(1)))
    return db.query(stmt % (filterAddressType,
                            stmtAddress,
                            tableDiagnostic['endDate'].formatValue(endDate.addDays(1)),
                            db.joinAnd(cond)))


class CStatReportF12Clients(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        title = u'Список пациентов по ф.12'
        self.setTitle(title, u'Список пациентов по ф.12')


    def getDefaultParams(self):
        result = CReport.getDefaultParams(self)
        result['ageFrom']     = 0
        result['ageTo']       = 150
        return result


    def getSetupDialog(self, parent):
        result = CReportAcuteInfectionsSetupDialog(parent)
        result.setAreaEnabled(True)
        result.setMKBFilterEnabled(True)
        result.setAllAddressSelectable(True)
        result.setEventTypeDDEnabled(True)
        result.setAllAttachSelectable(True)
        result.setEventTypeListListVisible(True)
        result.setOrgStructureListVisible(True)
        result.setSpecialityVisible(True)
        result.setCMBEventTypeVisible(False)
        result.setCMBOrgStructureVisible(False)
        result.setTitle(self.title())
        return result


    def dumpParamsMultiSelect(self, cursor, params):
        description = []
        eventTypeList = params.get('eventTypeList', None)
        if eventTypeList:
            db = QtGui.qApp.db
            tableET = db.table('EventType')
            records = db.getRecordList(tableET, [tableET['name']], [tableET['deleted'].eq(0), tableET['id'].inlist(eventTypeList)])
            nameList = []
            for record in records:
                nameList.append(forceString(record.value('name')))
            description.append(u'тип события:  %s'%(u','.join(name for name in nameList if name)))
        else:
            description.append(u'тип события:  не задано')
        orgStructureList = params.get('orgStructureList', None)
        if orgStructureList:
            if len(orgStructureList) == 1 and not orgStructureList[0]:
                description.append(u'подразделение: ЛПУ')
            else:
                db = QtGui.qApp.db
                table = db.table('OrgStructure')
                records = db.getRecordList(table, [table['name']], [table['id'].inlist(orgStructureList)])
                nameList = []
                for record in records:
                    nameList.append(forceString(record.value('name')))
                description.append(u'подразделение:  %s'%(u','.join(name for name in nameList if name)))
        else:
            description.append(u'подразделение: ЛПУ')
        columns = [ ('100%', [], CReportBase.AlignLeft) ]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)


    def build(self, params):
        chkFilterAttachType = params.get('chkFilterAttachType', False)
        dead = params.get('dead', False)
        chkFilterAttach = params.get('chkFilterAttach', False)
        attachToNonBase = params.get('attachToNonBase', False)
        excludeLeaved = params.get('excludeLeaved', False)
        reportData = {}
        query = selectData(params)
        while query.next():
            record         = query.record()
            clientId       = forceRef(record.value('clientId'))
            fio            = formatName(forceString(record.value('lastName')), forceString(record.value('firstName')), forceString(record.value('patrName')))
            MKB            = normalizeMKB(forceString(record.value('MKB')))
            MKBEx          = normalizeMKB(forceString(record.value('MKBEx')))
            address        = forceString(record.value('address'))
            sex            = forceInt(record.value('sex'))
            birthDate      = forceString(record.value('birthDate'))
            endDate        = forceString(record.value('endDate'))
            hospital       = forceInt(record.value('hospital'))
            formatHospital = [u'не нуждается', u'нуждается', u'направлен', u'пролечен'][hospital] if (hospital is not None) else u''
            dispanser      = forceString(record.value('dispanser'))
            person         = forceString(record.value('person'))
            speciality     = forceString(record.value('speciality'))

            keyClient = (clientId, fio, sex, birthDate, address)
            keyMKB = (MKB, MKBEx)
            reportLine = reportData.get(keyClient, {})
            reportItems = reportLine.get(keyMKB, [])
            reportItems.append((endDate, formatHospital, dispanser, person, speciality))
            reportLine[keyMKB] = reportItems
            reportData[keyClient] = reportLine

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        if chkFilterAttachType or dead or chkFilterAttach or attachToNonBase or excludeLeaved:
           self.dumpParamsAttach(cursor, params)
        if params.get('isFilterAddress', False):
            self.dumpParamsAdress(cursor, params)
        self.dumpParamsMultiSelect(cursor, params)
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        tableColumns = [
            ('5%',   [u'№'],                CReportBase.AlignLeft),
            ('10%',  [u'ФИО'],              CReportBase.AlignLeft),
            ('8.5%', [u'Пол'],              CReportBase.AlignLeft),
            ('8.5%', [u'д.р.'],             CReportBase.AlignLeft),
            ('8.5%', [u'Адрес проживания'], CReportBase.AlignLeft),
            ('8.5%', [u'Код по МКБ'],       CReportBase.AlignLeft),
            ('8.5%', [u'Доп.код'],          CReportBase.AlignLeft),
            ('8.5%', [u'Даты осмотров'],    CReportBase.AlignLeft),
            ('8.5%', [u'Госп.'],            CReportBase.AlignLeft),
            ('8.5%', [u'ДН'],               CReportBase.AlignLeft),
            ('8.5%', [u'Врач'],             CReportBase.AlignLeft),
            ('8.5%', [u'Специальность'],    CReportBase.AlignLeft),
            ]

        table = createTable(cursor, tableColumns)
        cnt = 1
        keysClient = reportData.keys()
        keysClient.sort(key=lambda item: item[1])
        for keyClient in keysClient:
            reportLine = reportData.get(keyClient, {})
            if reportLine:
                i = table.addRow()
                rowClients = i
                table.setText(i, 0, cnt)
                table.setText(i, 1, keyClient[1])
                table.setText(i, 2, formatSex(keyClient[2]))
                table.setText(i, 3, keyClient[3])
                table.setText(i, 4, keyClient[4])
                cnt += 1
                lenMKB = len(reportLine.keys())
                colMKB = 1
                for keyMKB, reportItems in reportLine.items():
                    rowMKB = i
                    table.setText(i, 5, keyMKB[0])
                    table.setText(i, 6, keyMKB[1])
                    lenItems = len(reportItems)
                    colItems = 1
                    reportItems.sort(key=lambda item: item[0])
                    for reportItem in reportItems:
                        for col, val in enumerate(reportItem):
                            table.setText(i, col+7, val)
                        if lenItems > colItems:
                            i = table.addRow()
                            colItems += 1
                    table.mergeCells(rowMKB, 5, i-rowMKB+1, 1)
                    table.mergeCells(rowMKB, 6, i-rowMKB+1, 1)
                    if lenMKB > colMKB:
                        i = table.addRow()
                        colMKB += 1
                table.mergeCells(rowClients, 0, i-rowClients+1, 1)
                table.mergeCells(rowClients, 1, i-rowClients+1, 1)
                table.mergeCells(rowClients, 2, i-rowClients+1, 1)
                table.mergeCells(rowClients, 3, i-rowClients+1, 1)
                table.mergeCells(rowClients, 4, i-rowClients+1, 1)
        return doc
