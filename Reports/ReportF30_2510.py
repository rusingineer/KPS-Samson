# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2022 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4                  import QtGui
from library.Utils          import forceInt, forceRef, forceString
from Reports.ReportBase     import CReportBase, createTable
from Reports.ReportF30      import CReportF30Base, CReportF30SetupDialog
from ReportForm131_o_1000_2021 import appendClientToContingentTypeCond


MainRows = [
    (u'Дети в возрасте 0-14 лет включительно', u'1'),
    (u'из них  дети до 1 года', u'2'),
    (u'Дети в возрасте 15-17 лет включительно', u'3'),
    (u'Из общего числа детей 15-17 лет (стр.3) - юношей', u'4'),
    (u'Школьники (из суммы строк 1+3)', u'5'),
    (u'Контингенты взрослого населения (18 лет и старше), всего', u'6'),
    (u'из них старше трудоспособного возраста', u'6.1'),
    (u'диспансеризация определенных групп взрослого населения', u'6.2'),
    (u'из них старше трудоспособного возраста', u'6.2.1'),
    (u'углубленная диспансеризация граждан, переболевших новой короновирусной инфекцией COVID-19', u'6.2.2'),
    (u'Всего (сумма строк 1, 3, 6)', u'7'),
]


def isSeniorAge(begDate, clientAge, clientSex):
    year = begDate.year() if begDate else 0
    if year == 2021:
        if clientSex == 1 and clientAge >= 61:
            return True
        if clientSex == 2 and clientAge >= 56:
            return True
    elif year == 2022 or year == 2023:
        if clientSex == 1 and clientAge >= 62:
            return True
        if clientSex == 2 and clientAge >= 57:
            return True
    elif year >= 2024:
        if clientSex == 1 and clientAge >= 63:
            return True
        if clientSex == 2 and clientAge >= 58:
            return True
    else:
        if clientSex == 1 and clientAge >= 60:
            return True
        if clientSex == 2 and clientAge >= 55:
            return True
    return False



def getClientIdListStmt(params):
    db = QtGui.qApp.db
    sex     = params.get('sex', 0)
    ageFrom = params.get('ageFrom', 0)
    ageTo   = params.get('ageTo', 150)
    contingentTypeIdList = params.get('contingentTypeIdList', [])
    socStatusClassId = params.get('socStatusClassId', None)
    socStatusTypeId  = params.get('socStatusTypeId', None)

    tableClient = db.table('Client')
    tableCSS = db.table('ClientSocStatus')
    queryTable = tableClient.leftJoin(tableCSS, db.joinAnd([
            tableCSS['client_id'].eq(tableClient['id']),
            tableCSS['deleted'].eq(0),
        ]) )

    contingentTypeCond = []
    for contingentTypeId in contingentTypeIdList:
        contingentTypeCond.append(db.joinAnd(appendClientToContingentTypeCond(contingentTypeId)))
    if not contingentTypeCond:
        return 'NULL'

    cond = [
        db.joinOr(contingentTypeCond),
        tableClient['deleted'].eq(0),
        'age(Client.birthDate, CURDATE()) BETWEEN %d AND %d' % (ageFrom, ageTo),
    ]
    if sex:
        cond.append(tableClient['sex'].eq(sex))
    if socStatusTypeId:
        cond.append(tableCSS['socStatusType_id'].eq(socStatusTypeId))
    if socStatusClassId:
        cond.append(tableCSS['socStatusClass_id'].eq(socStatusClassId))

    return db.selectStmt(queryTable, 'DISTINCT Client.id', cond)


def selectData(params):
    db = QtGui.qApp.db
    begDate = params.get('begDate', None)
    endDate = params.get('endDate', None)
    stmt = u"""
        SELECT DISTINCT Client.id,
               isClientVillager(Client.id) AS isVillager,
               age(Client.birthDate, CURDATE()) AS clientAge,
               Client.sex AS clientSex,

               (SELECT rbHealthGroup.code
                FROM rbHealthGroup
                WHERE rbHealthGroup.id = (
                    SELECT MAX(Diagnostic.healthGroup_id)
                    FROM Diagnostic
                    JOIN Event ON Diagnostic.event_id = Event.id
                    WHERE Event.client_id = Client.id
                       AND Diagnostic.deleted = 0
                       AND Event.deleted = 0
                       AND Event.isClosed = 1
                       {eventBegDate}
                       {eventEndDate}
                )) AS healthGroupCode,

                EXISTS(SELECT id
                 FROM Event
                 WHERE Event.client_id = Client.id
                    AND Event.deleted = 0
                    AND Event.isClosed = 1
                    {eventBegDate}
                    {eventEndDate}
                 LIMIT 1) AS isVisited,

                EXISTS(SELECT ETI.value
                 FROM EventType_Identification ETI
                 JOIN rbAccountingSystem ON ETI.system_id = rbAccountingSystem.id
                 JOIN Event ON Event.eventType_id = ETI.master_id
                 WHERE ETI.master_id = Event.eventType_id
                    AND ETI.deleted = 0
                    AND rbAccountingSystem.urn = 'urn:oid:131o'
                    AND Event.client_id = Client.id
                    AND Event.deleted = 0
                    AND ETI.value IN ('disp', 'prof', 'udvn')
                    {eventBegDate}
                    {eventEndDate}
                 LIMIT 1) AS hasUrn131,

                EXISTS(SELECT ETI.value
                  FROM EventType_Identification ETI
                  JOIN rbAccountingSystem ON ETI.system_id = rbAccountingSystem.id
                  JOIN Event ON Event.eventType_id = ETI.master_id
                  WHERE ETI.master_id = Event.eventType_id
                    AND ETI.deleted = 0
                    AND ETI.value = 'udvn'
                    AND rbAccountingSystem.urn = 'urn:oid:F30.2510'
                    AND Event.client_id = Client.id
                    AND Event.deleted = 0
                    {eventBegDate}
                    {eventEndDate}
                 LIMIT 1) AS hasCovidDisp,

                ({contingentDogvn}) AS isDogvn
        FROM Client
        WHERE """

    contingentDogvn = []
    contingentTypeDogvnId = forceRef(db.translate('rbContingentType', 'code', u'ДОГВН', 'id'))
    if contingentTypeDogvnId:
        records = db.getRecordList('rbContingentType_SexAge', '*',
                                   'master_id = %d' % contingentTypeDogvnId)
        for record in records:
            ageSpec = forceString(record.value('age'))
            sexSpec = forceInt(record.value('sex'))
            contingentDogvn.append('isSexAndAgeSuitable(Client.sex, Client.birthDate,'
                                   ' %d, "%s", CURDATE())' % (sexSpec, ageSpec))

    tableEvent = db.table('Event')
    cond = [
        'Client.id IN (' + getClientIdListStmt(params) + ')',
    ]
    fmt = {
        'eventBegDate': ('AND ' + tableEvent['execDate'].ge(begDate)) if begDate else u'',
        'eventEndDate': ('AND ' + tableEvent['execDate'].lt(endDate.addDays(1))) if endDate else u'',
        'contingentDogvn': db.joinOr(contingentDogvn),
    }
    return db.query(stmt.format(**fmt) + db.joinAnd(cond))



class CReportF30_2510(CReportF30Base):
    def __init__(self, parent, additionalFields = False):
        CReportF30Base.__init__(self, parent, additionalFields)
        self.setPayPeriodVisible(False)
        self.setTitle(u'Профилактические осмотры и диспансеризация, проведенные медицинской организацией')


    def getSetupDialog(self, parent):
        result = CReportF30SetupDialog(parent)
        result.setTitle(self.title())
        result.setCMBEventTypeVisible(False)
        result.setEventTypeListListVisible(True)
        result.setSpecialityListVisible(False)
        result.setAdditionalFieldsVisible(False)
        result.setInputDateVisible(False)
        result.setContingentTypeVisible(True)
        result.lblEventPurpose.setVisible(False)
        result.cmbEventPurpose.setVisible(False)
        result.cmbOrgStructure.setVisible(False)
        result.lblOrgStructure.setVisible(False)
        result.cmbTypeFinance.setVisible(False)
        result.lblTypeFinance.setVisible(False)
        result.cmbTariff.setVisible(False)
        result.lblTariff.setVisible(False)
        result.cmbVisitPayStatus.setVisible(False)
        result.lblVisitPayStatus.setVisible(False)
        result.cmbGrouping.setVisible(False)
        result.lblGrouping.setVisible(False)
        result.chkDetailChildren.setVisible(False)
        result.chkVisitHospital.setVisible(False)
        result.chkAmbulator.setVisible(False)
        result.cmbIsEventClosed.setVisible(False)
        result.lblIsEventClosed.setVisible(False)
        result.cmbScene.setVisible(False)
        result.lblScene.setVisible(False)
        return result


    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)

        tableColumns = [
            ('20%', [u'Контингенты', '', '', '1'], CReportBase.AlignLeft),
            ('3%',  [u'№ стр', '', '', '2'], CReportBase.AlignRight),
            ('7%',  [u'Подлежало осмотрам', '', '', '3'], CReportBase.AlignRight),
            ('7%',  [u'из них сельских жителей', '', '', '4'], CReportBase.AlignRight),
            ('7%',  [u'Осмотрено', '', '', '5'], CReportBase.AlignRight),
            ('7%',  [u'из них сельских жителей', '', '', '6'], CReportBase.AlignRight),
            ('7%',  [u'из числа осмотренных (гр. 5):\nопределены группы здоровья', 'I', '', '7'], CReportBase.AlignRight),
            ('7%',  [u'', 'II', '', '8'], CReportBase.AlignRight),
            ('7%',  [u'', 'III', '', '9'], CReportBase.AlignRight),
            ('7%',  [u'', u'из них:', u'IIIа', '10'], CReportBase.AlignRight),
            ('7%',  [u'', u'из них:', u'IIIб', '11'], CReportBase.AlignRight),
            ('7%',  [u'', u'IV', '', '12'], CReportBase.AlignRight),
            ('7%',  [u'', u'V', '', '13'], CReportBase.AlignRight),
        ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0,0, 3,1)
        table.mergeCells(0,1, 3,1)
        table.mergeCells(0,2, 3,1)
        table.mergeCells(0,3, 3,1)
        table.mergeCells(0,4, 3,1)
        table.mergeCells(0,5, 3,1)
        table.mergeCells(0,6, 1,7)
        table.mergeCells(1,6, 2,1)
        table.mergeCells(1,7, 2,1)
        table.mergeCells(1,8, 2,1)
        table.mergeCells(1,11, 2,1)
        table.mergeCells(1,12, 2,1)

        begDate = params.get('begDate', None)
        reportData = [[0]*11 for _ in xrange(len(MainRows))]
        query = selectData(params)
        while query.next():
            record = query.record()
            clientAge = forceInt(record.value('clientAge'))
            clientSex = forceInt(record.value('clientSex'))
            isVillager = forceInt(record.value('isVillager'))
            healthGroupCode = forceString(record.value('healthGroupCode'))
            isVisited = forceInt(record.value('isVisited'))
            hasUrn131 = forceInt(record.value('hasUrn131'))
            hasCovidDisp = forceInt(record.value('hasCovidDisp'))
            isDogvn = forceInt(record.value('isDogvn'))

            childRows = []
            adultRows = []

            if clientAge <= 14:
                childRows.append(0)
                if clientAge <= 1:
                    childRows.append(1)
            if 15 <= clientAge <= 17:
                childRows.append(2)
                if clientSex == 1:
                    childRows.append(3)

            if clientAge >= 18:
                adultRows.append(5)
                if isSeniorAge(begDate, clientAge, clientSex):
                    adultRows.append(6)
                if isDogvn:
                    adultRows.append(7)
                    if isSeniorAge(begDate, clientAge, clientSex):
                        adultRows.append(8)
                if hasCovidDisp:
                    adultRows.append(9)

            for row in childRows:
                reportData[row][0] += 1
                reportData[row][1] += isVillager
                reportData[row][2] += isVisited
                reportData[row][3] += int(isVisited and isVillager)
                reportData[row][4] += int(isVisited and healthGroupCode == u'1')
                reportData[row][5] += int(isVisited and healthGroupCode == u'2')
                reportData[row][6] += int(isVisited and healthGroupCode == u'3')
                reportData[row][7] += int(isVisited and healthGroupCode == u'3а')
                reportData[row][8] += int(isVisited and healthGroupCode == u'3б')
                reportData[row][9] += int(isVisited and healthGroupCode == u'4')
                reportData[row][10] += int(isVisited and healthGroupCode == u'5')

            for row in adultRows:
                reportData[row][0] += 1
                reportData[row][1] += isVillager
                reportData[row][2] += hasUrn131
                reportData[row][3] += int(hasUrn131 and isVillager)
                reportData[row][4] += int(hasUrn131 and healthGroupCode == u'1')
                reportData[row][5] += int(hasUrn131 and healthGroupCode == u'2')
                reportData[row][6] += int(hasUrn131 and healthGroupCode == u'3')
                reportData[row][7] += int(hasUrn131 and healthGroupCode == u'3а')
                reportData[row][8] += int(hasUrn131 and healthGroupCode == u'3б')
                reportData[row][9] += int(hasUrn131 and healthGroupCode == u'4')
                reportData[row][10] += int(hasUrn131 and healthGroupCode == u'5')


        for i in xrange(11):
            reportData[4][i] = reportData[0][i] + reportData[2][i]
            reportData[10][i] = reportData[4][i] + reportData[5][i]

        for i, descr in enumerate(MainRows):
            row = table.addRow()
            table.setText(row, 0, descr[0])
            table.setText(row, 1, descr[1])
            for j, value in enumerate(reportData[i]):
                table.setText(row, 2+j, value)

        return doc
