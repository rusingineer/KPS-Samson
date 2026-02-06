# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2025 SAMSON Group. All rights reserved.
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
from library.Utils      import forceBool, forceInt, forceRef, forceString, formatShortName
from Orgs.Utils         import getOrgStructureDescendants
from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable
from Reports.ReportF30  import CReportF30Base
from Reports.Utils import getRetireeAges


def getAgeGroupCond(begDate, today='Visit.date'):
    maleAge, femaleAge = getRetireeAges(begDate)

    return ('CASE WHEN age(Client.birthDate, {0}) < 15 THEN 0'
                ' WHEN age(Client.birthDate, {0}) BETWEEN 15 AND 17 THEN 1'
                ' WHEN age(Client.birthDate, {0}) >= IF(Client.sex = 1, {1}, {2}) THEN 3'
                ' ELSE 2 '
            'END').format(today, maleAge, femaleAge)


def selectData(begDate, endDate, useInputDate, begInputDate, endInputDate, eventPurposeId, eventTypeId, orgStructureId, socStatusClassId, socStatusTypeId, visitPayStatus, groupingRows, typeFinanceId, tariff, visitHospital, sex, ageFrom, ageTo, isEventClosed, scene):
    stmt = u"""
SELECT
   person_id,
   %(groupIdDef)s,
   %(groupNameDef)s,
   COUNT(person_id) AS cnt,
   SUM(clientRural) AS clientRuralSum,
   scene_id,
   illness,
   ageGroup,
   Person.lastName,
   Person.firstName,
   Person.patrName,
   IF(rbPost.code LIKE '1%%' OR rbPost.code LIKE '2%%' OR rbPost.code LIKE '3%%', 1, 0) AS postCode,
   EXISTS(SELECT PI.id
    FROM rbPost_Identification PI
    JOIN rbAccountingSystem rbAS ON PI.system_id = rbAS.id
    WHERE PI.deleted = 0
    AND rbAS.urn = 'urn:oid:1.2.643.5.1.13.13.11.1002'
    AND PI.value IN (3, 4, 5, 6)
    AND PI.master_id = Person.post_id
    ) AS isChief
   FROM (
SELECT
    Visit.person_id,
    Visit.scene_id,
    %(internalDefs)s
    rbEventTypePurpose.code = '1' as illness,
    %(ageGroupCond)s AS ageGroup,
    isAddressVillager(ClientAddress.address_id) AS clientRural
FROM Visit
LEFT JOIN Event     ON Event.id = Visit.event_id
LEFT JOIN EventType ON EventType.id = Event.eventType_id
LEFT JOIN rbEventTypePurpose ON rbEventTypePurpose.id = EventType.purpose_id
LEFT JOIN Client    ON Client.id = Event.client_id
LEFT JOIN ClientAddress ON ClientAddress.id =
          (SELECT MAX(CA.id)
           FROM ClientAddress AS CA
           WHERE CA.client_id = Event.client_id
             AND CA.deleted = 0
             AND CA.type=0
          )
LEFT JOIN Person    ON Person.id = Visit.person_id
%(internalJoins)s
WHERE Visit.deleted = 0
AND Event.deleted = 0
AND DATE(Event.setDate) <= Visit.date
AND %(cond)s
) AS T
LEFT JOIN Person ON Person.id = T.person_id
LEFT JOIN rbPost ON rbPost.id = Person.post_id
%(externalJoins)s
GROUP BY group_id, person_id, scene_id, illness, ageGroup, clientRural
ORDER BY groupName, Person.lastName, Person.firstName, Person.patrName
    """
    db = QtGui.qApp.db
    tableVisit  = db.table('Visit')
    tableEvent  = db.table('Event')
    tableEventType = db.table('EventType')
    tableClient = db.table('Client')
    tablePerson = db.table('Person')
    cond = []
    addDateInRange(cond, tableVisit['date'], begDate, endDate)
    if useInputDate:
        addDateInRange(cond, tableEvent['createDatetime'], begInputDate, endInputDate)
    if eventTypeId:
        cond.append(tableEvent['eventType_id'].eq(eventTypeId))
    elif eventPurposeId:
        tableEvent = db.table('Event')
        cond.append(tableEventType['purpose_id'].eq(eventPurposeId))
    cond.append(tablePerson['org_id'].eq(QtGui.qApp.currentOrgId()))
#    if eventTypeIdList:
#        cond.append(tableEvent['eventType_id'].inlist(eventTypeIdList))
    if orgStructureId:
        cond.append(tablePerson['orgStructure_id'].inlist(getOrgStructureDescendants(orgStructureId)))
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
    if visitPayStatus >= 0:
        cond.append(u'getPayCode(Visit.finance_id, Visit.payStatus) = %d'%(visitPayStatus))
    if typeFinanceId:
        cond.append(tableVisit['finance_id'].eq(typeFinanceId))
    if tariff == 2:
        cond.append(tableVisit['service_id'].isNull())
    elif tariff == 1:
        cond.append(tableVisit['service_id'].isNotNull())
    if scene:
        cond.append('Visit.scene_id = %i' % scene)
    if not visitHospital:
        cond.append(u'''EventType.medicalAidType_id IS NULL OR (EventType.medicalAidType_id NOT IN (SELECT rbMedicalAidType.id from rbMedicalAidType where rbMedicalAidType.code IN (\'7\')))''')
    if sex:
        cond.append(tableClient['sex'].eq(sex))
    cond.append(tableClient['sex'].ne(0))
    if ageFrom <= ageTo:
        cond.append('Visit.date >= ADDDATE(Client.birthDate, INTERVAL %d YEAR)'%ageFrom)
        cond.append('Visit.date < SUBDATE(ADDDATE(Client.birthDate, INTERVAL %d YEAR),1)'%(ageTo+1))
    if isEventClosed == 1:
        cond.append('Event.execDate is not NULL')
    elif isEventClosed == 2:
        cond.append('Event.execDate is NULL')
    if groupingRows == 1: # по должности
        groupIdDef    = 'Person.post_id AS group_id'
        groupNameDef  = 'rbPost.name AS groupName'
        internalDefs  = ''
        internalJoins = ''
        externalJoins = ''
    elif groupingRows == 2: # по профилю оплаты
        groupIdDef    = 'visitService_id  AS group_id'
        groupNameDef  = 'visitServiceName AS groupName'
        internalDefs  = 'Visit.service_id AS visitService_id, rbService.Code AS visitServiceName,'
        internalJoins = 'LEFT JOIN rbService ON rbService.id = Visit.service_id'
        externalJoins = ''
    else: # по специальности
        groupIdDef    = 'Person.speciality_id AS group_id'
        groupNameDef  = 'rbSpeciality.name AS groupName'
        internalDefs  = ''
        internalJoins = ''
        externalJoins = 'LEFT JOIN rbSpeciality ON rbSpeciality.id = Person.speciality_id'
    return db.query(stmt
                    % dict(groupIdDef    = groupIdDef,
                           groupNameDef  = groupNameDef,
                           internalDefs  = internalDefs,
                           internalJoins = internalJoins,
                           cond          = db.joinAnd(cond),
                           externalJoins = externalJoins,
                           ageGroupCond  = getAgeGroupCond(begDate),
                          )
                   )


class CReportF30_2100(CReportF30Base):
    def __init__(self, parent, additionalFields = False):
        CReportF30Base.__init__(self, parent, additionalFields)
        CReport.__init__(self, parent)
        self.setPayPeriodVisible(False)
        self.setTitle(u'Форма 30 (2100)', u'Форма 30 (2100)')


    def build(self, params):
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        useInputDate = bool(params.get('useInputDate', False))
        begInputDate = params.get('begInputDate', QDate())
        endInputDate = params.get('endInputDate', QDate())
        eventPurposeId = params.get('eventPurposeId', None)
        eventTypeId = params.get('eventTypeId', None)
        orgStructureId = params.get('orgStructureId', None)
        socStatusClassId = params.get('socStatusClassId', None)
        socStatusTypeId = params.get('socStatusTypeId', None)
        typeFinanceId = params.get('typeFinanceId', None)
        tariff = params.get('tariff', 0)
        visitPayStatus = params.get('visitPayStatus', 0)
        visitPayStatus -= 1
        groupingRows = params.get('groupingRows', 0)
        detailChildren = params.get('detailChildren', False)
        isEventClosed = params.get('isEventClosed', 0)
        scene = params.get('sceneId',  None) if self.additionalFields else None
        visitHospital = params.get('visitHospital', False)
        sex = params.get('sex', 0)
        ageFrom = params.get('ageFrom', 0)
        ageTo = params.get('ageTo', 150)
        onlyAmb = params.get('onlyAmbulator', True)
        db = QtGui.qApp.db
        basicSceneIdList = db.getDistinctIdList('rbScene', 'id', 'code = 2 OR code = 3')
        ambSceneId = self.getSceneId('1')
        reportRowSize = (15 if detailChildren else 11)
        #reportRowSize = reportRowSize if detailChildren else reportRowSize-1
        query = selectData(begDate, endDate, useInputDate, begInputDate, endInputDate, eventPurposeId, eventTypeId, orgStructureId, socStatusClassId, socStatusTypeId, visitPayStatus, groupingRows, typeFinanceId, tariff, visitHospital, sex, ageFrom, ageTo, isEventClosed, scene)

        reportData = {}
        personInfoList = []
        totalChildren = 0
        totalAdults = 0
        subRowVisitsAll = 0
        subRowVisitsChild = 0
        subRowVisitsRural = 0
        subRowVisitsChildRural = 0

        table2104VisitAll = 0
        table2104VisitAllRural = 0
        table2104VisitIllness = 0
        table2104VisitIllnessRural = 0
        table2104VisitHomeAll = 0
        table2104VisitHomeAllRural = 0
        table2104VisitHomeIllnes = 0
        table2104VisitHomeIllnesRural = 0

        while query.next():
            record    = query.record()
            groupId   = forceRef(record.value('group_id'))
            personId  = forceRef(record.value('person_id'))
            reportRow = reportData.get((groupId, personId), None)
            if not reportRow:
                reportRow = [0]*reportRowSize
                reportData[groupId, personId] = reportRow
                groupName = forceString(record.value('groupName'))
                lastName  = forceString(record.value('lastName'))
                firstName = forceString(record.value('firstName'))
                patrName = forceString(record.value('patrName'))
                postCode = forceInt(record.value('postCode'))
                isChief  = forceBool(record.value('isChief'))
                personName = formatShortName(lastName, firstName, patrName)
                personInfoList.append((groupName, personName, postCode, isChief, groupId, personId))
            cnt       = forceInt(record.value('cnt'))
            sceneId   = forceInt(record.value('scene_id'))
            illness   = forceBool(record.value('illness'))
            ageGroup  = forceInt(record.value('ageGroup'))
            clientRural = forceInt(record.value('clientRuralSum'))
            if (not onlyAmb) or (sceneId == ambSceneId):
                reportRow[0] += cnt
                reportRow[1] += clientRural
                if ageGroup in (0, 1):
                    reportRow[2] += cnt
                    if detailChildren and ageGroup == 1:
                        reportRow[3] += cnt
                if ageGroup == 3:
                    table2104VisitAll += cnt
                    table2104VisitAllRural += clientRural
                if illness:
                    subRowVisitsRural += clientRural
                    reportRow[4 if detailChildren else 3] += clientRural
                    if ageGroup in (0, 1):
                        subRowVisitsChild += cnt
                        subRowVisitsChildRural += clientRural
                        subRowVisitsAll += cnt
                        reportRow[6 if detailChildren else 5] += cnt
                        if detailChildren and ageGroup == 1:
                            reportRow[7] += cnt
                    else:
                        reportRow[5 if detailChildren else 4] += cnt
                        subRowVisitsAll += cnt
                    if ageGroup == 3:
                        table2104VisitIllness += cnt
                        table2104VisitIllnessRural += clientRural
            if sceneId in basicSceneIdList:
                reportRow[8 if detailChildren else 6] += cnt
                reportRow[9 if detailChildren else 7] += clientRural
                if ageGroup in (0, 1):
                    totalChildren += cnt
                else:
                    totalAdults += cnt
                if ageGroup == 3:
                    table2104VisitHomeAll += cnt
                    table2104VisitHomeAllRural += clientRural
                if illness:
                    reportRow[10 if detailChildren else 8] += cnt
                    if ageGroup == 3:
                        table2104VisitHomeIllnes += cnt
                        table2104VisitHomeIllnesRural += clientRural
                if ageGroup in (0, 1):
                    reportRow[11 if detailChildren else 9] += cnt
                    if illness:
                        reportRow[12 if detailChildren else 10] += cnt
                    if detailChildren and ageGroup == 0:
                        reportRow[13] += cnt
                        if illness:
                            reportRow[14] += cnt

        # now text
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        procentCol = '5%' if detailChildren else '7%'

        if detailChildren:
            tableColumns = [
                ('25%', [u'ФИО врача', u'', u'1'], CReportBase.AlignLeft),
                (procentCol, [u'№ строки', u'', u'2'], CReportBase.AlignLeft),
                (procentCol, [u'Число посещений', u'врачей, включая профилактические - всего', u'3'], CReportBase.AlignRight),
                (procentCol, [u'', u'в том числе сельскими жителями', u'4'], CReportBase.AlignRight),
                (procentCol, [u'', u'детьми 0 - 17 лет(из гр. 3)', u'5'], CReportBase.AlignRight),
                (procentCol, [u'', u'подр.', u'6'], CReportBase.AlignRight),
                (procentCol, [u'Из общего числа посещений сделано по поводу заболеваний', u'сельскими жителями', u'7'], CReportBase.AlignRight),
                (procentCol, [u'', u'взрослыми 18 лет и старше', u'8'], CReportBase.AlignRight),
                (procentCol, [u'', u'детьми 0 - 17 лет', u'9'], CReportBase.AlignRight),
                (procentCol, [u'', u'подр.', u'10'], CReportBase.AlignRight),
                (procentCol, [u'Число посещений врачами на дому', u'всего', u'11'], CReportBase.AlignRight),
                (procentCol, [u'', u'в том числе сельских жителей', u'12'], CReportBase.AlignRight),
                (procentCol, [u'', u'из них(гр. 8) по поводу заболеваний', u'13'], CReportBase.AlignRight),
                (procentCol, [u'', u'в том числе детей 0 - 17 лет включительно', u'14'], CReportBase.AlignRight),
                (procentCol, [u'', u'из них(гр. 10) по поводу заболеваний', u'15'], CReportBase.AlignRight),
                (procentCol, [u'', u'подр.', u'16'], CReportBase.AlignRight),
                (procentCol, [u'', u'из них(гр. 12) по поводу заболеваний', u'17'], CReportBase.AlignRight),
            ]
        else:
            tableColumns = [
                ('25%', [u'ФИО врача', u'', u'', u'1'], CReportBase.AlignLeft),
                (procentCol, [u'№ строки', u'', u'', u'2'], CReportBase.AlignLeft),
                (procentCol, [u'Число посещений', u'врачей, включая профилактические - всего', u'', u'3'], CReportBase.AlignRight),
                (procentCol, [u'', u'из них:', u'сельскими жителями', u'4'], CReportBase.AlignRight),
                (procentCol, [u'', u'', u'детьми 0 - 17 лет', u'5'], CReportBase.AlignRight),
                (procentCol, [u'Из общего числа посещений (из гр.3) сделано по поводу заболеваний', u'сельскими жителями', u'', u'6'], CReportBase.AlignRight),
                (procentCol, [u'', u'взрослыми 18 лет и старше', u'', u'7'], CReportBase.AlignRight),
                (procentCol, [u'', u'детьми 0 - 17 лет', u'', u'8'], CReportBase.AlignRight),
                (procentCol, [u'Число посещений врачами на дому', u'всего', u'', u'9'], CReportBase.AlignRight),
                (procentCol, [u'', u'из них сельских жителей', u'', u'10'], CReportBase.AlignRight),
                (procentCol, [u'', u'из гр.9', u'по поводу заболеваний', u'11'], CReportBase.AlignRight),
                (procentCol, [u'', u'', u'детей 0 - 17 лет', u'12'], CReportBase.AlignRight),
                (procentCol, [u'', u'из гр.12 по поводу заболеваний', u'', u'13'], CReportBase.AlignRight),
            ]


        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 1, 2, 1)
        if detailChildren:
            table.mergeCells(0, 1, 2, 1)
            table.mergeCells(0, 0, 2, 1)
            table.mergeCells(0, 2, 1, 4)
            table.mergeCells(0, 6, 1, 4)
            table.mergeCells(0, 10, 1, 10)
        else:
            table.mergeCells(0, 0, 3, 1)
            table.mergeCells(0, 1, 3, 1)
            table.mergeCells(0, 2, 1, 3)
            table.mergeCells(0, 5, 1, 3)
            table.mergeCells(0, 8, 1, 5)
            table.mergeCells(1, 2, 2, 1)
            table.mergeCells(1, 3, 1, 2)
            table.mergeCells(1, 5, 2, 1)
            table.mergeCells(1, 6, 2, 1)
            table.mergeCells(1, 7, 2, 1)
            table.mergeCells(1, 8, 2, 1)
            table.mergeCells(1, 9, 2, 1)
            table.mergeCells(1, 10, 1, 2)
            table.mergeCells(1, 12, 2, 1)

        prevGroupName = None
        total = None
        grandTotal = [0]*reportRowSize
        grandTotalChiefs = [0]*reportRowSize
        grandTotalDoctor = [0]*reportRowSize
        grandTotalOtherPost = [0]*reportRowSize
        for groupName, personName, postCode, isChief, groupId, personId in personInfoList:
            if prevGroupName != groupName:
                if total:
                    self.produceTotalLine(table, u'всего', total, 1)
                total = [0]*reportRowSize
                i = table.addRow()
                table.mergeCells(i, 2, 1, reportRowSize)
                table.setText(i, 0, groupName, CReportBase.TableHeader)
                table.setText(i, 1, i-1, CReportBase.TableHeader)
                prevGroupName = groupName
            row = reportData[groupId, personId]
            i = table.addRow()
            table.setText(i, 0, personName)
            table.setText(i, 1, i-1)
            for j in xrange(reportRowSize):
                table.setText(i, j+2, row[j])
                total[j] += row[j]
                grandTotal[j] += row[j]
                if isChief:
                    grandTotalChiefs[j] += row[j]
                if postCode:
                    grandTotalDoctor[j] += row[j]
                else:
                    grandTotalOtherPost[j] += row[j]
        if total:
            self.produceTotalLine(table, u'всего', total, 1)
        self.produceTotalLine(table, u'итого', grandTotal, 1)
        self.produceTotalLine(table, u'в т.ч. врачи', grandTotalDoctor, 1)
        self.produceTotalLine(table, u'в т.ч. специалисты: руководители организаций и их заместители', grandTotalChiefs, 1)
        self.produceTotalLine(table, u'прочие', grandTotalOtherPost, 1)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertBlock()
        cursor.insertText(u'(2102)Посещения врачами пунктов неотложной медицинской помощи на дому (из гр.9 таблицы 2100): взрослыми (18 лет и старше) __%s__, детьми (0-17 лет) __%s__.'%(totalAdults, totalChildren))
        cursor.insertBlock()
        cursor.insertBlock()
        cursor.insertText(u'(2104)')

        tableColumns = [
            ('65%', [u'Посещения лиц старше трудоспособного возраста', '1'], CReportBase.AlignLeft),
            ('5%' , [u'№ строки',                   '2'], CReportBase.AlignCenter),
            ('15%', [u'Число посещений',            '3'], CReportBase.AlignRight),
            ('15%', [u'из них: сельскими жителями', '4'], CReportBase.AlignRight),
            ]
        table = createTable(cursor, tableColumns)

        row = table.addRow()
        table.setText(row, 0, u'Из общего числа посещений сделано лицами старше трудоспособного возраста (из табл.2100,стр.1,гр.3)')
        table.setText(row, 1, 1)
        table.setText(row, 2, table2104VisitAll)
        table.setText(row, 3, table2104VisitAllRural)

        row = table.addRow()
        table.setText(row, 0, u'из них: по поводу заболеваний (из табл.2100, стр.1, гр.7)')
        table.setText(row, 1, 2)
        table.setText(row, 2, table2104VisitIllness)
        table.setText(row, 3, table2104VisitIllnessRural)

        row = table.addRow()
        table.setText(row, 0, u'посещений врачами на дому всего (из табл.2100, стр.1, гр.9)')
        table.setText(row, 1, 3)
        table.setText(row, 2, table2104VisitHomeAll)
        table.setText(row, 3, table2104VisitHomeAllRural)

        row = table.addRow()
        table.setText(row, 0, u'из них: по поводу заболеваний (из табл.2100, стр.1, гр.11)')
        table.setText(row, 1, 4)
        table.setText(row, 2, table2104VisitHomeIllnes)
        table.setText(row, 3, table2104VisitHomeIllnesRural)

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertBlock()
        cursor.insertText(u'(2106)Обращения по поводу заболеваний, всего __%s__, из них: сельских жителей __%s__, дети 0-17 лет (из стр.1) __%s__, из них: сельских жителей (из стр.3) __%s__.'%(subRowVisitsAll, subRowVisitsRural, subRowVisitsChild, subRowVisitsChildRural))
        cursor.insertBlock()
        return doc
