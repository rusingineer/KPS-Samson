# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2023 SAMSON Group. All rights reserved.
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
from library.Utils      import forceBool, forceInt, forceRef, forceString

from Reports.Report     import normalizeMKB
from Reports.ReportBase import CReportBase, createTable
from Reports.ReportPersonSickList import addAddressCond, addAttachCond
from Reports.ReportAcuteInfections import getFilterAddress
from Orgs.Utils         import getOrgStructureListDescendants, getOrgStructureAddressIdList
from StatReportF12Adults_2020 import CStatReportF12Adults_2020, MainRows, CompRows, selectDataClient


def selectData(registeredInPeriod, begDate, endDate, eventPurposeId, eventTypeIdList, orgStructureIdList, personId, sex, ageFrom, ageTo, socStatusClassId, socStatusTypeId, isFilterAddressOrgStructure, addrType, addressOrgStructureId, locality, eventTypeDDId, params):
    stmt = u"""
SELECT
   Diagnosis.MKB AS MKB,
   COUNT(*) AS sickCount,
   rbDiseaseCharacter.code AS diseaseCharacter,
   rbDiagnosisType.code AS diagnosisType,

   EXISTS(SELECT rbResult.id
   FROM
   Diagnostic AS D1
   INNER JOIN Event ON Event.id = D1.event_id
   INNER JOIN rbResult ON rbResult.id = Event.result_id
   WHERE D1.diagnosis_id = Diagnosis.id AND rbResult.continued = 0
   ORDER BY Event.id
   LIMIT 1) AS closedEvent,

   (%s) AS firstInPeriod,

   %s
   (SELECT IF(rbDispanser.code IN (2,6,1), 1, 0)
    FROM
    Diagnostic AS D1
    LEFT JOIN rbDispanser ON rbDispanser.id = D1.dispanser_id
    WHERE
      D1.diagnosis_id = Diagnosis.id
      AND (rbDispanser.code IN (2,6,1))
    ORDER BY rbDispanser.code
    LIMIT 1) AS getObserved,

   IF((SELECT MAX(rbDispanser.observed)
FROM
Diagnostic AS D1
LEFT JOIN rbDispanser ON rbDispanser.id = D1.dispanser_id
WHERE
  D1.diagnosis_id = Diagnosis.id
  AND Diagnosis.diagnosisType_id NOT IN (SELECT RBDT.id FROM rbDiagnosisType AS RBDT WHERE RBDT.code IN ('7','11','51','52','53','54'))
  AND D1.endDate = (
    SELECT MAX(D2.endDate)
    FROM Diagnostic AS D2
    WHERE D2.diagnosis_id = Diagnosis.id
      AND D2.dispanser_id IS NOT NULL
      AND  D2.endDate<%s))
      = 1, 1, 0) AS observed,

   EXISTS(SELECT rbDispanser.id
    FROM
    Diagnostic AS D1
    LEFT JOIN rbDispanser ON rbDispanser.id = D1.dispanser_id
    WHERE
      D1.diagnosis_id = Diagnosis.id AND rbDispanser.code IN (3, 4, 5)
    ORDER BY rbDispanser.code) AS getRemovingObserved,

   EXISTS(SELECT mes.MES.id
    FROM
    Diagnostic AS D1
    INNER JOIN Event AS E ON E.id = D1.event_id
    INNER JOIN mes.MES ON mes.MES.id=E.MES_id
    INNER JOIN mes.mrbMESGroup ON mes.mrbMESGroup.id=mes.MES.group_id
    WHERE
      D1.diagnosis_id = Diagnosis.id AND E.deleted = 0
      AND D1.deleted = 0 AND (mes.mrbMESGroup.code='МедОсм')) AS getProfilactic,

   EXISTS(SELECT E.id
    FROM Diagnostic AS D1 INNER JOIN Event AS E ON E.id = D1.event_id
    WHERE D1.diagnosis_id = Diagnosis.id AND E.deleted = 0
    AND D1.deleted = 0 AND E.isPrimary = 2) AS isNotPrimary,

   EXISTS(SELECT mes.MES.id
    FROM
    Diagnostic AS D1
    INNER JOIN Event AS E ON E.id = D1.event_id
    INNER JOIN mes.MES ON mes.MES.id=E.MES_id
    INNER JOIN mes.mrbMESGroup ON mes.mrbMESGroup.id=mes.MES.group_id
    WHERE
      D1.diagnosis_id = Diagnosis.id AND E.deleted = 0
      AND D1.deleted = 0 AND (mes.mrbMESGroup.code='ДиспанС')) AS getAdultsDispans,

EXISTS(SELECT NULL
    FROM Event
    JOIN Diagnostic ON Diagnostic.event_id = Event.id
    JOIN mes.MES ON Event.MES_id = mes.MES.id
    JOIN mes.mrbMESGroup ON mes.MES.group_id = mes.mrbMESGroup.id
    WHERE Event.deleted = 0 AND mes.MES.deleted = 0 AND mes.mrbMESGroup.deleted = 0 AND Diagnostic.deleted = 0
    AND mes.mrbMESGroup.code = 'МедОсм' AND Diagnostic.diagnosis_id = Diagnosis.id
) AS hasMedOsm,

EXISTS(SELECT NULL
    FROM Event
    JOIN Diagnostic ON Diagnostic.event_id = Event.id
    JOIN EventType ON Event.eventType_id = EventType.id
    JOIN EventType_Identification AS ETI ON ETI.master_id = EventType.id
    WHERE Event.deleted = 0 AND EventType.deleted = 0 AND ETI.deleted = 0 AND Diagnostic.deleted = 0
    AND ETI.value = 'prof' AND Diagnostic.diagnosis_id = Diagnosis.id
) AS hasProf

FROM Diagnosis
LEFT JOIN Client ON Client.id = Diagnosis.client_id
%s
LEFT JOIN rbDiagnosisType    ON rbDiagnosisType.id = Diagnosis.diagnosisType_id
LEFT JOIN rbDiseaseCharacter ON rbDiseaseCharacter.id = Diagnosis.character_id
WHERE Diagnosis.diagnosisType_id NOT IN (SELECT RBDT.id FROM rbDiagnosisType AS RBDT WHERE RBDT.code IN ('7','11','51','52','53','54'))
AND %s
GROUP BY MKB, diseaseCharacter, firstInPeriod, getObserved, getRemovingObserved, getProfilactic, isNotPrimary, observed, closedEvent, getAdultsDispans, rbDiagnosisType.id
    """
    db = QtGui.qApp.db
    tableDiagnosis  = db.table('Diagnosis')
    tableClient = db.table('Client')
    tableDiagnostic = db.table('Diagnostic')
    tablePerson = db.table('Person')
    tableEvent = db.table('Event')
    specialityId = params.get('specialityId', None)
    extraAgesCond = params.get('extraAgesCond', None)

    cond = []
    cond.append(tableDiagnosis['deleted'].eq(0))
    cond.append(tableDiagnosis['mod_id'].isNull())
    if extraAgesCond:
        cond.append(extraAgesCond)
    diagnosticQuery = tableDiagnostic
    diagnosticCond = [ tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']),
                       tableDiagnostic['deleted'].eq(0)
                     ]

    if registeredInPeriod:
        addDateInRange(diagnosticCond, tableDiagnostic['setDate'], begDate, endDate)
    else:
        diagnosticCond.append(tableDiagnostic['setDate'].le(endDate))
        diagnosticCond.append(db.joinOr([tableDiagnostic['endDate'].ge(begDate), tableDiagnostic['endDate'].isNull()]))
    if specialityId:
        diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
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
            diagnosticCond.append("LEFT(rbPost.code, 1) IN ('1','2','3')")
        elif isPersonPost == 2:
            diagnosticCond.append("LEFT(rbPost.code, 1) IN ('4','5','6','7','8','9')")
    if personId:
        diagnosticCond.append(tableDiagnostic['person_id'].eq(personId))
    elif orgStructureIdList:
        if not isPersonPost and not specialityId:
            diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
            diagnosticCond.append(tablePerson['deleted'].eq(0))
        diagnosticCond.append(tablePerson['orgStructure_id'].inlist(getOrgStructureListDescendants(orgStructureIdList)))
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
    if eventTypeDDId:
        colsEventTypeDDId = u'''(SELECT E.id
        FROM Diagnostic
        INNER JOIN rbDiagnosisType ON Diagnostic.diagnosisType_id=rbDiagnosisType.id
        INNER JOIN Event AS E ON Diagnostic.event_id=E.id
        WHERE Diagnosis.deleted = 0 AND Diagnostic.deleted = 0 AND Diagnostic.diagnosis_id=Diagnosis.id
        AND E.eventType_id  = %d
        AND (rbDiagnosisType.code = '1'
        OR (rbDiagnosisType.code = '2' AND Diagnostic.person_id = E.execPerson_id
        AND (NOT EXISTS (SELECT DC.id FROM Diagnostic AS DC
        INNER JOIN rbDiagnosisType AS DT ON DT.id = DC.diagnosisType_id WHERE DT.code = '1'
        AND DC.diagnosis_id=Diagnosis.id
        LIMIT 1))))) AS eventId,  '''%(eventTypeDDId)
    else:
        colsEventTypeDDId = u''
    if sex:
        cond.append(tableClient['sex'].eq(sex))
    else:
        cond.append(tableClient['sex'].ne(0))
    # if ageFrom <= ageTo:
    #     cond.append('age(Client.birthDate, "%04d-12-31") BETWEEN %d AND %d' % (endDate.year(), ageFrom, ageTo))
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
    stmtAddress = u''
    if isFilterAddressOrgStructure:
        addrIdList = None
        cond2 = []
        if (addrType+1) & 1:
            addrIdList = getOrgStructureAddressIdList(addressOrgStructureId)
            cond2 = addAddressCond(db, cond2, 0, addrIdList)
        if (addrType+1) & 2:
            if addrIdList is None:
                addrIdList = getOrgStructureAddressIdList(addressOrgStructureId)
            cond2 = addAddressCond(db, cond2, 1, addrIdList)
        if ((addrType+1) & 4):
            if addressOrgStructureId:
                cond2 = addAttachCond(db, cond2, 'orgStructure_id = %d'%addressOrgStructureId, 1, None)
            else:
                cond2 = addAttachCond(db, cond2, 'LPU_id=%d'%QtGui.qApp.currentOrgId(), 1, None)
        if cond2:
            cond.append(db.joinOr(cond2))
    if locality:
        # 1: горожане, isClientVillager == 0 или NULL
        # 2: сельские жители, isClientVillager == 1
        cond.append('IFNULL(isClientVillager(Client.id), 0) = %d' % (locality-1))
    filterAddress = params.get('isFilterAddress', False)
    if filterAddress:
        if not stmtAddress:
            stmtAddress = u'''INNER JOIN ClientAddress ON ClientAddress.client_id = Client.id
                              INNER JOIN Address ON Address.id = ClientAddress.address_id
                              INNER JOIN AddressHouse ON AddressHouse.id = Address.house_id'''
        else:
            stmtAddress += u'INNER JOIN AddressHouse ON AddressHouse.id = Address.house_id'
        cond.append('ClientAddress.id IN (%s)'%(getFilterAddress(params)))
    if 'attachTo' in params:
        attachOrgId = params['attachTo']
        if attachOrgId:
            cond = addAttachCond(db, cond, 'LPU_id=%d'%attachOrgId, *params.get('attachType', (0, None, QDate(), QDate())))
    elif 'attachToNonBase' in params:
        cond = addAttachCond(db, cond, 'LPU_id!=%d'%QtGui.qApp.currentOrgId(), *params.get('attachType', (0, None, QDate(), QDate())))
    elif 'attachType' in params:
        cond = addAttachCond(db, cond, '', *params['attachType'])
    excludeLeaved = params.get('excludeLeaved', False)
    if excludeLeaved:
        outerCond = ['ClientAttach.client_id = Client.id']
        innerCond = ['CA2.client_id = Client.id']
        cond.append('''EXISTS (SELECT ClientAttach.id
           FROM ClientAttach
           LEFT JOIN rbAttachType ON rbAttachType.id = ClientAttach.attachType_id
           WHERE ClientAttach.deleted=0
           AND %s
           AND ClientAttach.id = (SELECT MAX(CA2.id)
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
    if params.get('MKBFrom'):
        cond.append(tableDiagnosis['MKB'].ge(params.get('MKBFrom')))
    if params.get('MKBTo'):
        cond.append(tableDiagnosis['MKB'].le(params.get('MKBTo')))
    return db.query(stmt % (db.joinAnd([tableDiagnosis['setDate'].le(endDate),
                                        tableDiagnosis['setDate'].ge(begDate)]),
                            colsEventTypeDDId,
                            tableDiagnosis['setDate'].formatValue(endDate.addDays(1)),
                            stmtAddress,
                            db.joinAnd(cond)))


def getClientCountFor3004(registeredInPeriod, begDate, endDate, eventPurposeId, eventTypeIdList, orgStructureIdList, personId, sex, ageFrom, ageTo, socStatusClassId, socStatusTypeId, isFilterAddressOrgStructure, addrType, addressOrgStructureId, locality, eventTypeDDId, params):
    clientsCount = 0
    clientsRemovingObserved = 0
    clientsDeadCount = 0
    clientsDeadCountI00_99 = 0

    query = selectData(registeredInPeriod, begDate, endDate, eventPurposeId, eventTypeIdList, orgStructureIdList, personId, sex, ageFrom, ageTo, socStatusClassId, socStatusTypeId, isFilterAddressOrgStructure, addrType, addressOrgStructureId, locality, eventTypeDDId, params)
    while query.next():
        record = query.record()
        sickCount = forceInt(record.value('sickCount'))
        getRemovingObserved = forceBool(record.value('getRemovingObserved'))
        clientsCount += sickCount
        if getRemovingObserved:
            clientsRemovingObserved += sickCount

    isDead = params.get('dead', False)
    params['dead'] = True
    query = selectData(registeredInPeriod, begDate, endDate, eventPurposeId, eventTypeIdList, orgStructureIdList, personId, sex, ageFrom, ageTo, socStatusClassId, socStatusTypeId, isFilterAddressOrgStructure, addrType, addressOrgStructureId, locality, eventTypeDDId, params)
    while query.next():
        record = query.record()
        sickCount = forceInt(record.value('sickCount'))
        getRemovingObserved = forceBool(record.value('getRemovingObserved'))
        MKB = forceString(record.value('MKB'))
        diagnosisType = forceString(record.value('diagnosisType'))

        if getRemovingObserved:
            clientsDeadCount += sickCount
            if MKB.startswith('I') and diagnosisType == '4':
                clientsDeadCountI00_99 += sickCount

    params['dead'] = isDead
    return (clientsCount, clientsRemovingObserved, clientsDeadCount, clientsDeadCountI00_99)


class CStatReportF12Adults_2021(CStatReportF12Adults_2020):
    def __init__(self, parent):
        CStatReportF12Adults_2020.__init__(self, parent)


    def getSetupDialog(self, parent):
        result = CStatReportF12Adults_2020.getSetupDialog(self, parent)
        result.chkFilterExcludeLeaved.setVisible(False)
        result.chkFilterExcludeLeaved.setChecked(False)
        result.chkRegisteredInPeriod.setChecked(True)
        return result


    def build(self, params, reportMainRows=MainRows, reportCompRows=CompRows):
        mapMainRows = createMapCodeToRowIdx( [row[2] for row in reportMainRows] )
        mapCompRows = createMapCodeToRowIdx( [row[2] for row in reportCompRows] )

        registeredInPeriod = params.get('registeredInPeriod', False)
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        eventPurposeId = params.get('eventPurposeId', None)
        eventTypeDDId = params.get('eventTypeDDId', None)
        eventTypeList = params.get('eventTypeList', None)
        orgStructureList = params.get('orgStructureList', None)
        personId = params.get('personId', None)
        sex = params.get('sex', 0)
        ageFrom = params.get('ageFrom', 18)
        ageTo = params.get('ageTo', 150)
        socStatusClassId = params.get('socStatusClassId', None)
        socStatusTypeId = params.get('socStatusTypeId', None)
        isFilterAddressOrgStructure = params.get('isFilterAddressOrgStructure', False)
        addrType = params.get('addressOrgStructureType', 0)
        addressOrgStructureId = params.get('addressOrgStructure', None)
        locality = params.get('locality', 0)
        reportLine = None
        chkFilterAttachType = params.get('chkFilterAttachType', False)
        dead = params.get('dead', False)
        chkFilterAttach = params.get('chkFilterAttach', False)
        attachToNonBase = params.get('attachToNonBase', False)
        excludeLeaved = params.get('excludeLeaved', False)
        detailMKB = params.get('detailMKB', False)
        rowSize = 8
        rowSizeComp = 4
        getObservedSum = 0
        eventTypeDDSum = 0
        eventIdList = []
        if detailMKB:
            reportMainData = {}  # { MKB: [reportLine] }
            reportCompData = {}  # { MKB: [reportLine] }
        else:
            reportMainData = [ [0]*rowSize for row in xrange(len(reportMainRows)) ]
            reportCompData = [ [0]*rowSizeComp for row in xrange(len(reportCompRows)) ]
        query = selectData(registeredInPeriod, begDate, endDate, eventPurposeId, eventTypeList, orgStructureList, personId, sex, ageFrom, ageTo, socStatusClassId, socStatusTypeId, isFilterAddressOrgStructure, addrType, addressOrgStructureId, locality, eventTypeDDId, params)
        while query.next():
            record    = query.record()
            clientId = forceRef(record.value('client_id'))
            MKB       = normalizeMKB(forceString(record.value('MKB')))
            sickCount = forceInt(record.value('sickCount'))
            diseaseCharacter = forceString(record.value('diseaseCharacter'))
            diagnosisType = forceString(record.value('diagnosisType'))
            firstInPeriod = forceBool(record.value('firstInPeriod'))
            closedEvent = forceBool(record.value('closedEvent'))
            observed = forceBool(record.value('observed'))
            hasMedOsm = forceBool(record.value('hasMedOsm'))
            hasProf = forceBool(record.value('hasProf'))
            getObserved = forceInt(record.value('getObserved'))
            getObservedSum += getObserved
            eventId = forceRef(record.value('eventId'))
            getRemovingObserved = forceBool(record.value('getRemovingObserved'))
            getProfilactic      = forceBool(record.value('getProfilactic'))
            getAdultsDispans    = forceBool(record.value('getAdultsDispans'))
            isNotPrimary        = forceBool(record.value('isNotPrimary'))
            if (eventId not in eventIdList) and (diseaseCharacter == 1 or diseaseCharacter == 2):
                eventTypeDDSum += 1
                eventIdList.append(eventId)
            cols = [0]
            if getObserved:
                cols.append(1)
            if getRemovingObserved:
                cols.append(6)
            if observed or hasMedOsm or hasProf:
                cols.append(7)
            if diseaseCharacter == u'1': # острое
                cols.append(2)
                if getObserved:
                    cols.append(3)
                if getProfilactic and not getAdultsDispans:
                    cols.append(4)
                if getAdultsDispans:
                    cols.append(5)
            elif firstInPeriod:
                cols.append(2)
                if getObserved:
                    cols.append(3)
                if getProfilactic and not getAdultsDispans:
                    cols.append(4)
                if getAdultsDispans:
                    cols.append(5)

            if detailMKB:
                reportLine = reportMainData.setdefault(MKB, [0]*rowSize)
                for col in cols:
                    reportLine[col] += sickCount
            else:
                for row in mapMainRows.get(MKB, []):
                    reportLine = reportMainData[row]
                    for col in cols:
                        reportLine[col] += sickCount

            if diagnosisType == u'98':
                if detailMKB:
                    reportLine = reportCompData.setdefault(MKB, [0]*rowSizeComp)
                    reportLine[0] += sickCount
                    if getProfilactic and isNotPrimary:
                        reportLine[1] += sickCount
                    if closedEvent:
                        reportLine[2] += sickCount
                else:
                    for row in mapCompRows.get(MKB, []):
                        reportLine = reportCompData[row]
                        reportLine[0] += sickCount
                        if getProfilactic and isNotPrimary:
                            reportLine[1] += sickCount
                        if closedEvent:
                            reportLine[2] += sickCount
        registeredAll = 0
        registeredFirst = 0
        consistsByEnd = [0, 0, 0]
        clientIdList = []
        clientIdFor3003List1 = {}
        clientIdFor3003List2 = {}
        queryClient = selectDataClient(registeredInPeriod, begDate, endDate, eventPurposeId, eventTypeList, orgStructureList, personId, sex, ageFrom, ageTo, socStatusClassId, socStatusTypeId, isFilterAddressOrgStructure, addrType, addressOrgStructureId, locality, params)
        while queryClient.next():
            record    = queryClient.record()
            clientId = forceRef(record.value('client_id'))
            diseaseCharacter = forceString(record.value('diseaseCharacter'))
            firstInPeriod = forceBool(record.value('firstInPeriod'))
            observed = forceBool(record.value('observed'))
            MKB = normalizeMKB(forceString(record.value('MKB')))
            if clientId and MKB in [u'B18', u'K74.6']:
                clientIdFor30031 = clientIdFor3003List1.setdefault(clientId, [])
                if MKB not in clientIdFor30031:
                    clientIdFor30031.append(MKB)
            if clientId and MKB in [u'B18', u'C22.0']:
                clientIdFor30032 = clientIdFor3003List2.setdefault(clientId, [])
                if MKB not in clientIdFor30032:
                    clientIdFor30032.append(MKB)

            if clientId and clientId not in clientIdList:
                clientIdList.append(clientId)
                registeredAll += 1
                if observed:
                    consistsByEnd[0] += 1
                if firstInPeriod:
                   registeredFirst += 1
        for clientIdFor30031 in clientIdFor3003List1.values():
            consistsByEnd[1] += (1 if len(clientIdFor30031) == 2 else 0)
        for clientIdFor30032 in clientIdFor3003List2.values():
            consistsByEnd[2] += (1 if len(clientIdFor30032) == 2 else 0)
        # now text
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
        cursor.insertText(u'(3000)')
        cursor.insertBlock()

        tableColumns = [
            ('15%', [u'Наименование классов и отдельных болезней',        u'',                                                                     u'',                                                                    u'1'], CReportBase.AlignLeft),
            ('5%',  [u'№ строки',                                         u'',                                                                     u'',                                                                    u'2'], CReportBase.AlignLeft),
            ('10%', [u'Код по МКБ-10 пересмотра',                         u'',                                                                     u'',                                                                    u'3'], CReportBase.AlignLeft),
            ('10%', [u'Зарегистрировано пациентов с данным заболеванием', u'Всего',                                                                u'',                                                                    u'4'], CReportBase.AlignRight),
            ('10%', [u'',                                                 u'из них(из гр. 4):',                                                    u'взято под диспансерное наблюдение',                                   u'5'], CReportBase.AlignRight),
            ('10%', [u'',                                                 u'',                                                                     u'с впервые в жизни установленным диагнозом',                           u'6'], CReportBase.AlignRight),
            ('10%', [u'',                                                 u'из заболеваний с впервые в жизни установленным диагнозом (из гр. 6):', u'взято под диспансерное наблюдение',                                   u'7'], CReportBase.AlignRight),
            ('10%', [u'',                                                 u'',                                                                     u'выявлено при профосмотре',                                            u'8'], CReportBase.AlignRight),
            ('10%', [u'',                                                 u'',                                                                     u'выявлено при диспансеризации определенных групп взрослого населения', u'9'], CReportBase.AlignRight),
            ('10%', [u'Снято с диспансерного наблюдения',                 u'',                                                                     u'',                                                                    u'10'], CReportBase.AlignRight),
            ('10%', [u'Состоит на д.н. на конец периода',                 u'',                                                                     u'',                                                                    u'11'], CReportBase.AlignRight)
            ]

        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 3, 1) # Наименование
        table.mergeCells(0, 1, 3, 1) # № стр.
        table.mergeCells(0, 2, 3, 1) # Код МКБ
        table.mergeCells(0, 3, 1, 6) # Всего
        table.mergeCells(1, 3, 2, 1)
        table.mergeCells(1, 4, 1, 2)
        table.mergeCells(1, 6, 1, 3)
        table.mergeCells(0, 9, 3, 1)
        table.mergeCells(0, 10, 3, 1)

        if detailMKB:
            for row, MKB in enumerate(sorted(reportMainData.keys())):
                reportLine = reportMainData[MKB]
                reportLine[7] = reportLine[1] - reportLine[6]
                if not MKB:
                    MKBDescr, MKB = u'', u'Не указано'
                else:
                    MKBDescr = forceString(QtGui.qApp.db.translate('MKB', 'DiagID', MKB, 'DiagName'))
                if MKB.endswith('.0') and not MKBDescr:
                    MKBDescr = forceString(QtGui.qApp.db.translate('MKB', 'DiagID', MKB[:-2], 'DiagName'))
                i = table.addRow()
                table.setText(i, 0, MKBDescr)
                table.setText(i, 1, row+1)
                table.setText(i, 2, MKB)
                for col in xrange(rowSize):
                    table.setText(i, 3+col, reportLine[col])
        else:
            for row, rowDescr in enumerate(reportMainRows):
                reportLine = reportMainData[row]
                reportLine[7] = reportLine[1] - reportLine[6]
                i = table.addRow()
                table.setText(i, 0, rowDescr[0])
                table.setText(i, 1, rowDescr[1])
                table.setText(i, 2, rowDescr[2] + (u' (часть)' if row == 59 else ''))
                for col in xrange(rowSize):
                    table.setText(i, 3+col, reportLine[col])

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertBlock()
        cursor.insertText(u'(3002) Число физических лиц зарегистрированных пациентов – всего %d , из них с диагнозом , установленным впервые в жизни %d , состоит под диспансерным наблюдением на конец отчетного года (из гр. 15, стр. 1.0) %d .'%(registeredAll, registeredFirst, consistsByEnd[0]))
        cursor.insertBlock()
        cursor.insertText(u'(3003) Из числа пациентов, состоящих на конец отчетного года под диспансерным наблюдением (гр. 11): состоит под диспансерным наблюдением лиц с хроническим вирусным гепатитом (B18) и циррозом печени (K74.6) одновременно %d чел.; с хроническим вирусным гепатитом (B18) и гепатоцеллюлярным раком (C22.0) одновременно %d чел.'%(consistsByEnd[1], consistsByEnd[2]))
        cursor.insertBlock()
        cursor.insertText(u'Число лиц с болезнями системы кровообращения,состоявших под диспансерном наблюдением (стр.10.0 гр.5) %d из них снято %d из них умерло (из графы 2) %d, из из них умерло от болезней системы кровообращения (из графы 3) %d' %
            getClientCountFor3004(registeredInPeriod, begDate, endDate, eventPurposeId, eventTypeList, orgStructureList, personId, sex, ageFrom, ageTo, socStatusClassId, socStatusTypeId, isFilterAddressOrgStructure, addrType, addressOrgStructureId, locality, eventTypeDDId, params))
        cursor.insertBlock()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertBlock()
        cursor.insertText(u'Взрослые 18 лет и старше.')
        cursor.insertBlock()
        cursor.insertText(u'ФАКТОРЫ, ВЛИЯЮЩИЕ НА СОСТОЯНИЕ ЗДОРОВЬЯ НАСЕЛЕНИЯ')
        cursor.insertBlock()
        cursor.insertText(u'И ОБРАЩЕНИЯ В МЕДИЦИНСКИЕ ОРГАНИЗАЦИИ (С ПРОФИЛАКТИЧЕСКОЙ ЦЕЛЬЮ)')
        cursor.insertBlock()
        cursor.insertText(u'(3100)')
        cursor.insertBlock()
        cursor.insertBlock()

        tableColumns = [
            ('30%', [u'Наименование', u'',                  u'1'], CReportBase.AlignLeft),
            ('10%', [u'№ строки',     u'',                  u'2'], CReportBase.AlignLeft),
            ('15%', [u'Код МКБ-10',   u'',                  u'3'], CReportBase.AlignLeft),
            ('15%', [u'Обращения',    u'всего',             u'4'], CReportBase.AlignRight),
            ('15%', [u'',             u'из них: повторные', u'5'], CReportBase.AlignRight),
            ('15%', [u'',             u'законченные случаи',u'6'], CReportBase.AlignRight),
            ]

        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 2, 1)
        table.mergeCells(0, 2, 2, 1)
        table.mergeCells(0, 3, 1, 3)

        if detailMKB:
            for row, MKB in enumerate(sorted(reportCompData.keys())):
                reportLine = reportCompData[MKB]
                if not MKB:
                    MKBDescr, MKB = u'', u'Не указано'
                else:
                    MKBDescr = forceString(QtGui.qApp.db.translate('MKB', 'DiagID', MKB, 'DiagName'))
                if MKB.endswith('.0') and not MKBDescr:
                    MKBDescr = forceString(QtGui.qApp.db.translate('MKB', 'DiagID', MKB[:-2], 'DiagName'))
                i = table.addRow()
                table.setText(i, 0, MKBDescr)
                table.setText(i, 1, row+1)
                table.setText(i, 2, MKB)
                table.setText(i, 3, reportLine[0])
                table.setText(i, 4, reportLine[1])
                table.setText(i, 5, reportLine[2])
        else:
            for row, rowDescr in enumerate(reportCompRows):
                reportLine = reportCompData[row]
                i = table.addRow()
                table.setText(i, 0, rowDescr[0])
                table.setText(i, 1, rowDescr[1])
                table.setText(i, 2, rowDescr[2])
                table.setText(i, 3, reportLine[0])
                table.setText(i, 4, reportLine[1])
                table.setText(i, 5, reportLine[2])
        return doc

