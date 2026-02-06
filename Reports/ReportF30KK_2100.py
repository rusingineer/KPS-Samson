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
from library.Utils      import forceBool, forceInt, forceString
from Orgs.Utils         import getOrgStructureDescendants
from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable
from Reports.ReportF30  import CReportF30Base
from Reports.Utils import getRetireeAges

def getAgeGroupCond(begDate, today='Action.begDate'):
    maleAge, femaleAge = getRetireeAges(begDate)

    return ('CASE WHEN age(Client.birthDate, {0}) < 15 THEN 0'
                ' WHEN age(Client.birthDate, {0}) BETWEEN 15 AND 17 THEN 1'
                ' WHEN age(Client.birthDate, {0}) >= IF(Client.sex = 1, {1}, {2}) THEN 3'
                ' ELSE 2 '
            'END').format(today, maleAge, femaleAge)


def getQueryCond(begDate, endDate, useInputDate, begInputDate, endInputDate, eventPurposeId, eventTypeId, orgStructureId, socStatusClassId, socStatusTypeId, visitHospital, sex, ageFrom, ageTo, isEventClosed):
    db = QtGui.qApp.db
    tableAction  = db.table('Action')
    tableEvent  = db.table('Event')
    tableEventType = db.table('EventType')
    tableClient = db.table('Client')
    tablePerson = db.table('Person')
    cond = []
    addDateInRange(cond, tableAction['begDate'], begDate, endDate)
    if useInputDate:
        addDateInRange(cond, tableEvent['createDatetime'], begInputDate, endInputDate)
    if eventTypeId:
        cond.append(tableEvent['eventType_id'].eq(eventTypeId))
    elif eventPurposeId:
        cond.append(tableEventType['purpose_id'].eq(eventPurposeId))
    cond.append(tablePerson['org_id'].eq(QtGui.qApp.currentOrgId()))
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
        cond.append('EXISTS(' + subStmt + ')')
    if not visitHospital:
        cond.append(u'''EventType.medicalAidType_id IS NULL OR (EventType.medicalAidType_id NOT IN (SELECT rbMedicalAidType.id from rbMedicalAidType where rbMedicalAidType.code IN (\'7\')))''')
    if sex:
        cond.append(tableClient['sex'].eq(sex))
    cond.append(tableClient['sex'].ne(0))
    if ageFrom <= ageTo:
        cond.append('Action.begDate >= ADDDATE(Client.birthDate, INTERVAL %d YEAR)' % ageFrom)
        cond.append('Action.begDate < SUBDATE(ADDDATE(Client.birthDate, INTERVAL %d YEAR),1)' % (ageTo + 1))
    if isEventClosed == 1:
        cond.append('Event.execDate is not NULL')
    elif isEventClosed == 2:
        cond.append('Event.execDate is NULL')
    return cond


def selectData2100(begDate, endDate, useInputDate, begInputDate, endInputDate, eventPurposeId, eventTypeId, orgStructureId, socStatusClassId, socStatusTypeId, visitHospital, sex, ageFrom, ageTo, isEventClosed):
    stmt = u"""
SELECT
    ReportLine.title,
    ReportLine.descrb,
    (CASE
        WHEN ReportUslCol.reportLine_id = 1443 THEN 0
        WHEN ReportUslCol.reportLine_id = 1444 THEN 1
        WHEN ReportUslCol.reportLine_id = 1445 THEN 2
        WHEN ReportUslCol.reportLine_id = 1446 THEN 3
    END) AS columnGroup,
    ReportData.isRural,
    ReportData.ageGroup,
    SUM(ReportData.cnt) AS cnt
FROM soc_Report AS Report
    LEFT JOIN soc_ReportLine AS ReportLine ON ReportLine.report_id = Report.id
    LEFT JOIN soc_ReportUsl AS ReportUsl ON ReportUsl.reportLine_id = ReportLine.id
    LEFT JOIN soc_ReportUsl AS ReportUslCol ON ReportUslCol.kusl = ReportUsl.kusl AND ReportUslCol.reportLine_id BETWEEN 1443 AND 1446
    LEFT JOIN (
        SELECT rbService.code AS serviceCode,
            isAddressVillager(ClientAddress.address_id) AS isRural,
            %(ageGroupCond)s AS ageGroup,
            count(Action.id) AS cnt
        FROM Action
            INNER JOIN ActionType ON ActionType.id = Action.actionType_id
            INNER JOIN rbService ON rbService.id = ActionType.nomenclativeService_id
            INNER JOIN Person ON Person.id = Action.person_id
            INNER JOIN Event ON Event.id = Action.event_id
            INNER JOIN EventType ON EventType.id = Event.eventType_id
            LEFT JOIN Client ON Client.id = Event.client_id
            LEFT JOIN ClientAddress ON ClientAddress.id = (
                SELECT MAX(CA.id)
                FROM ClientAddress AS CA
                WHERE CA.client_id = Event.client_id
                    AND CA.deleted = 0
                    AND CA.type=0
            )
        WHERE Action.deleted = 0
            AND Event.deleted = 0
            AND %(cond)s
        GROUP BY rbService.code, isRural, ageGroup
    ) AS ReportData ON ReportData.serviceCode = ReportUslCol.kusl
WHERE Report.code = '30.2.1.2100'
    AND ReportLine.descrb is not null   
GROUP BY ReportLine.title, ReportLine.descrb, ReportLine.seqNum, columnGroup, ReportData.isRural, ReportData.ageGroup
ORDER BY ReportLine.seqNum, columnGroup
    """
    db = QtGui.qApp.db
    cond = getQueryCond(begDate, endDate, useInputDate, begInputDate, endInputDate, eventPurposeId, eventTypeId, orgStructureId, socStatusClassId, socStatusTypeId, visitHospital, sex, ageFrom, ageTo, isEventClosed)
    return db.query(stmt % {
        'cond': db.joinAnd(cond),
        'ageGroupCond': getAgeGroupCond(begDate),
    })


def selectData2101(begDate, endDate, useInputDate, begInputDate, endInputDate, eventPurposeId, eventTypeId, orgStructureId, socStatusClassId, socStatusTypeId, visitHospital, sex, ageFrom, ageTo, isEventClosed):
    stmt = u"""
SELECT
    ReportLine.title,
    ReportLine.descrb,
    ReportData.isRural,
    SUM(ReportData.cnt) AS cnt
FROM soc_Report AS Report
    LEFT JOIN soc_ReportLine AS ReportLine ON ReportLine.report_id = Report.id
    LEFT JOIN soc_ReportUsl AS ReportUsl ON ReportUsl.reportLine_id = ReportLine.id
    LEFT JOIN (
        SELECT rbService.code AS serviceCode,
            isAddressVillager(ClientAddress.address_id) AS isRural,
            count(Action.id) AS cnt
        FROM Action
            INNER JOIN ActionType ON ActionType.id = Action.actionType_id
            INNER JOIN rbService ON rbService.id = ActionType.nomenclativeService_id
            INNER JOIN Person ON Person.id = Action.person_id
            INNER JOIN Event ON Event.id = Action.event_id
            INNER JOIN EventType ON EventType.id = Event.eventType_id
            LEFT JOIN Client ON Client.id = Event.client_id
            LEFT JOIN ClientAddress ON ClientAddress.id = (
                SELECT MAX(CA.id)
                FROM ClientAddress AS CA
                WHERE CA.client_id = Event.client_id
                    AND CA.deleted = 0
                    AND CA.type=0
            )
        WHERE Action.deleted = 0
            AND Event.deleted = 0
            AND %(cond)s
        GROUP BY rbService.code, isRural
    ) AS ReportData ON ReportData.serviceCode = ReportUsl.kusl
WHERE Report.code = '30.2.1.2101'
GROUP BY ReportLine.title, ReportLine.descrb, ReportLine.seqNum, ReportData.isRural
ORDER BY ReportLine.seqNum
    """
    db = QtGui.qApp.db
    cond = getQueryCond(begDate, endDate, useInputDate, begInputDate, endInputDate, eventPurposeId, eventTypeId, orgStructureId, socStatusClassId, socStatusTypeId, visitHospital, sex, ageFrom, ageTo, isEventClosed)
    return db.query(stmt % {
        'cond': db.joinAnd(cond),
    })


def selectData2105(begDate, endDate, useInputDate, begInputDate, endInputDate, eventPurposeId, eventTypeId, orgStructureId, socStatusClassId, socStatusTypeId, visitHospital, sex, ageFrom, ageTo, isEventClosed):
    stmt = u"""
SELECT
    ReportLine.title,
    ReportLine.descrb,
    ReportData.isRural,
    ReportData.ageGroup,
    SUM(ReportData.cnt) AS cnt
FROM soc_Report AS Report
    LEFT JOIN soc_ReportLine AS ReportLine ON ReportLine.report_id = Report.id
    LEFT JOIN soc_ReportUsl AS ReportUsl ON ReportUsl.reportLine_id = ReportLine.id
    LEFT JOIN (
        SELECT rbService.code AS serviceCode,
            isAddressVillager(ClientAddress.address_id) AS isRural,
            %(ageGroupCond)s AS ageGroup,
            count(Action.id) AS cnt
        FROM Action
            INNER JOIN ActionType ON ActionType.id = Action.actionType_id
            INNER JOIN rbService ON rbService.id = ActionType.nomenclativeService_id
            INNER JOIN Person ON Person.id = Action.person_id
            INNER JOIN Event ON Event.id = Action.event_id
            INNER JOIN EventType ON EventType.id = Event.eventType_id
            LEFT JOIN Client ON Client.id = Event.client_id
            LEFT JOIN ClientAddress ON ClientAddress.id = (
                SELECT MAX(CA.id)
                FROM ClientAddress AS CA
                WHERE CA.client_id = Event.client_id
                    AND CA.deleted = 0
                    AND CA.type=0
            )
        WHERE Action.deleted = 0
            AND Event.deleted = 0
            AND %(cond)s
        GROUP BY rbService.code, isRural, ageGroup
    ) AS ReportData ON ReportData.serviceCode = ReportUsl.kusl
WHERE Report.code = '30.2.1.2105'
GROUP BY ReportLine.title, ReportLine.descrb, ReportLine.seqNum, ReportData.isRural, ReportData.ageGroup
ORDER BY ReportLine.seqNum
    """
    db = QtGui.qApp.db
    cond = getQueryCond(begDate, endDate, useInputDate, begInputDate, endInputDate, eventPurposeId, eventTypeId, orgStructureId, socStatusClassId, socStatusTypeId, visitHospital, sex, ageFrom, ageTo, isEventClosed)
    return db.query(stmt % {
        'cond': db.joinAnd(cond),
        'ageGroupCond': getAgeGroupCond(begDate),
    })


class CReportF30KK_2100(CReportF30Base):
    def __init__(self, parent):
        CReportF30Base.__init__(self, parent)
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
        detailChildren = params.get('detailChildren', False)
        isEventClosed = params.get('isEventClosed', 0)
        visitHospital = params.get('visitHospital', False)
        sex = params.get('sex', 0)
        ageFrom = params.get('ageFrom', 0)
        ageTo = params.get('ageTo', 150)
        db = QtGui.qApp.db
        # запросы
        # т. 2100, 2102, 2104, 2106
        query = selectData2100(begDate, endDate, useInputDate, begInputDate, endInputDate, eventPurposeId, eventTypeId, orgStructureId, socStatusClassId, socStatusTypeId, visitHospital, sex, ageFrom, ageTo, isEventClosed)
        reportRowSize2100 = 17 if detailChildren else 13
        reportDataSize2100 = reportRowSize2100 - 2
        cntHomeAdults = 0
        cntHomeChildren = 0
        cntRetired = 0
        cntRetiredRural = 0
        cntIllnessRetired = 0
        cntIllnessRetiredRural = 0
        cntHomeRetired = 0
        cntHomeRetiredRural = 0
        cntHomeIllnessRetired = 0
        cntHomeIllnessRetiredRural = 0
        cntIllness = 0
        cntIllnessRural = 0
        cntIllnessChildren = 0
        cntIllnessChildrenRural = 0
        tableRows2100 = []
        prevDescrb = None
        currentRow = None
        while query.next():
            record = query.record()
            descrb = forceString(record.value('descrb'))
            if descrb != prevDescrb:
                title = forceString(record.value('title'))
                currentRow = [title, descrb] + ([0] * reportDataSize2100)
                tableRows2100.append(currentRow)
                prevDescrb = descrb
            cnt = forceInt(record.value('cnt'))
            if not cnt:
                continue
            columnGroup = forceInt(record.value('columnGroup'))
            isRural = forceBool(record.value('isRural'))
            ageGroup = forceInt(record.value('ageGroup'))
            if columnGroup == 0:
                # Число посещений
                # 3. врачей, включая профилактические - всего
                currentRow[2] += cnt
                if isRural:
                    # 4. из них: сельскими жителями
                    currentRow[3] += cnt
                if ageGroup in (0, 1):
                    # 5. детьми 0 - 17 лет
                    currentRow[4] += cnt
                if detailChildren and ageGroup == 1:
                    # 6. подр.
                    currentRow[5] += cnt
            elif columnGroup == 1:
                # Из общего числа посещений (из гр. 3) сделано по поводу заболеваний
                if isRural:
                    # 6/7. сельскими жителями
                    currentRow[6 if detailChildren else 5] += cnt
                if ageGroup in (2, 3):
                    # 7/8. взрослыми 18 лет и старше
                    currentRow[7 if detailChildren else 6] += cnt
                if ageGroup in (0, 1):
                    # 8/9. детьми 0 - 17 лет
                    currentRow[8 if detailChildren else 7] += cnt
                if detailChildren and ageGroup == 1:
                    # 10. подр.
                    currentRow[9] += cnt
            elif columnGroup in (2, 3):
                # Число посещений врачами на дому
                if columnGroup == 2:
                    # 9/11. всего
                    currentRow[10 if detailChildren else 8] += cnt
                if columnGroup == 2 and isRural:
                    # 10/12. из них сельских жителей
                    currentRow[11 if detailChildren else 9] += cnt
                if columnGroup == 3:
                    # 11/13. из гр. 9/11 по поводу заболеваний
                    currentRow[12 if detailChildren else 10] += cnt
                if columnGroup == 2 and ageGroup in (0, 1):
                    # 12/14. детей 0 - 17 лет
                    currentRow[13 if detailChildren else 11] += cnt
                if columnGroup == 3 and ageGroup in (0, 1):
                    # 13/15. из гр. 12/14 по поводу заболеваний
                    currentRow[14 if detailChildren else 12] += cnt
                if detailChildren and columnGroup == 2 and ageGroup == 1:
                    # 16. подр.
                    currentRow[15] += cnt
                if detailChildren and columnGroup == 3 and ageGroup == 1:
                    # 17. из гр. 16 по поводу заболеваний
                    currentRow[16] += cnt
            if descrb == '1':
                if columnGroup == 2:
                    # (2102) Посещения врачами пунктов неотложной медицинской помощи на дому (из гр.9 таблицы 2100)
                    if ageGroup in (2, 3):
                        # взрослыми (18 лет и старше)
                        cntHomeAdults += cnt
                    else:
                        # детьми (0-17 лет)
                        cntHomeChildren += cnt
                if ageGroup == 3:
                    # (2104) Из общего числа посещений сделано лицами старше трудоспособного возраста
                    if columnGroup == 0:
                        # всего
                        cntRetired += cnt
                        if isRural:
                            cntRetiredRural += cnt
                    elif columnGroup == 1:
                        # из них: по поводу заболеваний
                        cntIllnessRetired += cnt
                        if isRural:
                            cntIllnessRetiredRural += cnt
                    elif columnGroup == 2:
                        # посещений врачами на дому всего
                        cntHomeRetired += cnt
                        if isRural:
                            cntHomeRetiredRural += cnt
                    elif columnGroup == 3:
                        # из них: по поводу заболеваний
                        cntHomeIllnessRetired += cnt
                        if isRural:
                            cntHomeIllnessRetiredRural += cnt
                if columnGroup == 1:
                    # (2106) Обращения по поводу заболеваний
                    # всего
                    cntIllness += cnt
                    if isRural:
                        # из них: сельских жителей
                        cntIllnessRural += cnt
                    if ageGroup in (0, 1):
                        # дети 0-17 лет (из стр.1)
                        cntIllnessChildren += cnt
                    if ageGroup in (0, 1) and isRural:
                        # из них: сельских жителей (из стр.3)
                        cntIllnessChildrenRural += cnt
        # т. 2101
        query = selectData2101(begDate, endDate, useInputDate, begInputDate, endInputDate, eventPurposeId, eventTypeId, orgStructureId, socStatusClassId, socStatusTypeId, visitHospital, sex, ageFrom, ageTo, isEventClosed)
        reportRowSize2101 = 4
        reportDataSize2101 = reportRowSize2101 - 2
        tableRows2101 = []
        prevDescrb = None
        currentRow = None
        while query.next():
            record = query.record()
            descrb = forceString(record.value('descrb'))
            if descrb != prevDescrb:
                title = forceString(record.value('title'))
                currentRow = [title, descrb] + ([0] * reportDataSize2101)
                tableRows2101.append(currentRow)
                prevDescrb = descrb
            cnt = forceInt(record.value('cnt'))
            if not cnt:
                continue
            isRural = forceBool(record.value('isRural'))
            # Посещения среднего медицинского персонала
            # 3. Всего, ед
            currentRow[2] += cnt
            if isRural == 0:
                # 4. из них сельскими жителями
                currentRow[3] += cnt
        # т. 2105
        query = selectData2105(begDate, endDate, useInputDate, begInputDate, endInputDate, eventPurposeId, eventTypeId, orgStructureId, socStatusClassId, socStatusTypeId, visitHospital, sex, ageFrom, ageTo, isEventClosed)
        reportRowSize2105 = 6
        reportDataSize2105 = reportRowSize2105 - 2
        tableRows2105 = []
        prevDescrb = None
        currentRow = None
        while query.next():
            record = query.record()
            descrb = forceString(record.value('descrb'))
            if descrb != prevDescrb:
                title = forceString(record.value('title'))
                currentRow = [title, descrb] + ([0] * reportDataSize2105)
                tableRows2105.append(currentRow)
                prevDescrb = descrb
            cnt = forceInt(record.value('cnt'))
            if not cnt:
                continue
            isRural = forceBool(record.value('isRural'))
            ageGroup = forceInt(record.value('ageGroup'))
            # Из общего числа посещений (табл. 2100, стр. 1) сделано посещений всего
            # 3. Всего, ед
            currentRow[2] += cnt
            if isRural:
                # 4. из них сельскими жителями
                currentRow[3] += cnt
            if ageGroup in (0, 1):
                # 5. детьми 0-17 лет
                currentRow[4] += cnt
                if isRural:
                    # 6. из них сельскими жителями (из гр. 5)
                    currentRow[5] += cnt
        # документ
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        # т. 2100
        procentCol = '5%' if detailChildren else '7%'
        if detailChildren:
            tableColumns = [
                ('25%', [u'Наименование', u'', u'1'], CReportBase.AlignLeft),
                (procentCol, [u'№ строки', u'', u'2'], CReportBase.AlignLeft),
                (procentCol, [u'Число посещений', u'врачей, включая профилактические - всего', u'3'], CReportBase.AlignRight),
                (procentCol, [u'', u'из них: сельскими жителями', u'4'], CReportBase.AlignRight),
                (procentCol, [u'', u'детьми 0 - 17 лет', u'5'], CReportBase.AlignRight),
                (procentCol, [u'', u'подр.', u'6'], CReportBase.AlignRight),
                (procentCol, [u'Из общего числа посещений (из гр. 3) сделано по поводу заболеваний', u'сельскими жителями', u'7'], CReportBase.AlignRight),
                (procentCol, [u'', u'взрослыми 18 лет и старше', u'8'], CReportBase.AlignRight),
                (procentCol, [u'', u'детьми 0 - 17 лет', u'9'], CReportBase.AlignRight),
                (procentCol, [u'', u'подр.', u'10'], CReportBase.AlignRight),
                (procentCol, [u'Число посещений врачами на дому', u'всего',  u'11'], CReportBase.AlignRight),
                (procentCol, [u'', u'из них сельских жителей', u'12'], CReportBase.AlignRight),
                (procentCol, [u'', u'из гр. 11 по поводу заболеваний', u'13'], CReportBase.AlignRight),
                (procentCol, [u'', u'детей 0 - 17 лет', u'14'], CReportBase.AlignRight),
                (procentCol, [u'', u'из гр. 14 по поводу заболеваний', u'15'], CReportBase.AlignRight),
                (procentCol, [u'', u'подр.', u'16'], CReportBase.AlignRight),
                (procentCol, [u'', u'из гр. 16 по поводу заболеваний', u'17'], CReportBase.AlignRight),
            ]
        else:
            tableColumns = [
                ('25%', [u'Наименование', u'', u'1'], CReportBase.AlignLeft),
                (procentCol, [u'№ строки', u'', u'2'], CReportBase.AlignLeft),
                (procentCol, [u'Число посещений', u'врачей, включая профилактические - всего', u'3'], CReportBase.AlignRight),
                (procentCol, [u'', u'из них: сельскими жителями', u'4'], CReportBase.AlignRight),
                (procentCol, [u'', u'детьми 0 - 17 лет', u'5'], CReportBase.AlignRight),
                (procentCol, [u'Из общего числа посещений (из гр.3) сделано по поводу заболеваний', u'сельскими жителями', u'6'], CReportBase.AlignRight),
                (procentCol, [u'', u'взрослыми 18 лет и старше', u'7'], CReportBase.AlignRight),
                (procentCol, [u'', u'детьми 0 - 17 лет', u'8'], CReportBase.AlignRight),
                (procentCol, [u'Число посещений врачами на дому', u'всего', u'9'], CReportBase.AlignRight),
                (procentCol, [u'', u'из них сельских жителей', u'10'], CReportBase.AlignRight),
                (procentCol, [u'', u'из гр.9 по поводу заболеваний', u'11'], CReportBase.AlignRight),
                (procentCol, [u'', u'детей 0 - 17 лет', u'12'], CReportBase.AlignRight),
                (procentCol, [u'', u'из гр.12 по поводу заболеваний', u'13'], CReportBase.AlignRight),
            ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 2, 1)
        if detailChildren:
            table.mergeCells(0, 2, 1, 4)
            table.mergeCells(0, 6, 1, 4)
            table.mergeCells(0, 10, 1, 7)
        else:
            table.mergeCells(0, 2, 1, 3)
            table.mergeCells(0, 5, 1, 3)
            table.mergeCells(0, 8, 1, 5)
        for row in tableRows2100:
            r = table.addRow()
            for c in xrange(reportRowSize2100):
                table.setText(r, c, row[c])
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        # т. 2101
        cursor.insertBlock()
        cursor.insertText(u'(2101)')
        tableColumns = [
            ('65%', [u'Посещения среднего медицинского персонала', '1'], CReportBase.AlignLeft),
            ('5%' , [u'№ строки', '2'], CReportBase.AlignCenter),
            ('15%', [u'Всего, ед', '3'], CReportBase.AlignRight),
            ('15%', [u'из них: сельскими жителями', '4'], CReportBase.AlignRight),
            ]
        table = createTable(cursor, tableColumns)
        for row in tableRows2101:
            r = table.addRow()
            for c in xrange(reportRowSize2101):
                table.setText(r, c, row[c])
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        # т. 2102
        cursor.insertBlock()
        cursor.insertText(u'(2102) Посещения врачами пунктов неотложной медицинской помощи на дому (из гр.9 таблицы 2100): взрослыми (18 лет и старше) __%s__, детьми (0-17 лет) __%s__.' % (cntHomeAdults, cntHomeChildren))
        cursor.insertBlock()
        # т. 2104
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
        table.setText(row, 2, cntRetired)
        table.setText(row, 3, cntRetiredRural)
        row = table.addRow()
        table.setText(row, 0, u'из них: по поводу заболеваний (из табл.2100, стр.1, гр.7)')
        table.setText(row, 1, 2)
        table.setText(row, 2, cntIllnessRetired)
        table.setText(row, 3, cntIllnessRetiredRural)
        row = table.addRow()
        table.setText(row, 0, u'посещений врачами на дому всего (из табл.2100, стр.1, гр.9)')
        table.setText(row, 1, 3)
        table.setText(row, 2, cntHomeRetired)
        table.setText(row, 3, cntHomeRetiredRural)
        row = table.addRow()
        table.setText(row, 0, u'из них: по поводу заболеваний (из табл.2100, стр.1, гр.11)')
        table.setText(row, 1, 4)
        table.setText(row, 2, cntHomeIllnessRetired)
        table.setText(row, 3, cntHomeIllnessRetiredRural)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        # т. 2105
        cursor.insertBlock()
        cursor.insertText(u'(2105)')
        tableColumns = [
            ('55%', [u'Из общего числа посещений (табл. 2100, стр. 1) сделано посещений всего', u'' '1'], CReportBase.AlignLeft),
            ('5%' , [u'№ строки', u'', '2'], CReportBase.AlignCenter),
            ('10%', [u'Всего, ед', u'', '3'], CReportBase.AlignRight),
            ('10%', [u'из них', u'сельскими жителями', '4'], CReportBase.AlignRight),
            ('10%', [u'', u'детьми 0-17 лет', '5'], CReportBase.AlignRight),
            ('10%', [u'', u'из них: сельскими жителями (из гр. 5)', '6'], CReportBase.AlignRight),
            ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 2, 1)
        table.mergeCells(0, 2, 2, 1)
        table.mergeCells(0, 3, 1, 3)
        for row in tableRows2105:
            r = table.addRow()
            for c in xrange(reportRowSize2105):
                table.setText(r, c, row[c])
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        # т. 2106
        cursor.insertBlock()
        cursor.insertText(u'(2106) Обращения по поводу заболеваний, всего __%s__, из них: сельских жителей __%s__, дети 0-17 лет (из стр.1) __%s__, из них: сельских жителей (из стр.3) __%s__.'%(cntIllness, cntIllnessRural, cntIllnessChildren, cntIllnessChildrenRural))
        cursor.insertBlock()
        return doc
