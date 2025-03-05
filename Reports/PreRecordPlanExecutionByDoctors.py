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
from PyQt4.QtCore import *

from Reports.Report     import *
from Reports.ReportBase import CReportBase, createTable
from Reports.Utils      import dateRangeAsStr
from Timeline.Schedule  import CSchedule
from library.DialogBase import CDialogBase
from library.Utils      import *
from Orgs.Utils import getOrgStructureDescendants

from Ui_PreRecordPlanExecutionByDoctorsDialog import Ui_PreRecordPlanExecutionByDoctorsDialog


def selectData(params):
    useRecordPeriod   = params.get('useRecordPeriod', True)
    begRecordDate     = params.get('begRecordDate', None)
    endRecordDate     = params.get('endRecordDate', None)
    useSchedulePeriod = params.get('useSchedulePeriod', False)
    begScheduleDate   = params.get('begScheduleDate', None)
    endScheduleDate   = params.get('endScheduleDate', None)
    orgStructureType  = params.get('orgStructureType', None)
    orgStructureId    = params.get('orgStructureId', None)
    specialityId      = params.get('specialityId', None)
    personId          = params.get('personId', None)
    isOvertime        = params.get('isOvertime', 0)

    appointmentType = params.get('appointmentType', CSchedule.atAmbulance)

    db = QtGui.qApp.db
    tablePerson = db.table('Person')
    tableOrgStructure = db.table('OrgStructure')
    tableSchedule = db.table('Schedule')
    tableScheduleItem = db.table('Schedule_Item')

    cond = [tableSchedule['deleted'].eq(0),
            tableSchedule['appointmentType'].eq(appointmentType),
            tableScheduleItem['deleted'].eq(0),
            tableScheduleItem['client_id'].isNotNull(),
            tableOrgStructure['type'].eq(orgStructureType)
            ]

    if useRecordPeriod:
        if begRecordDate:
            cond.append(tableScheduleItem['time'].ge(begRecordDate))
        if endRecordDate:
            cond.append(tableScheduleItem['time'].lt(endRecordDate.addDays(1)))
    if useSchedulePeriod:
        if begScheduleDate:
            cond.append(tableSchedule['date'].ge(begScheduleDate))
        if endScheduleDate:
            cond.append(tableSchedule['date'].le(endScheduleDate))
    if personId:
        cond.append(tableSchedule['person_id'].eq(personId))
    if specialityId:
        cond.append(tablePerson['speciality_id'].eq(specialityId))
    if orgStructureId:
        cond.append(tablePerson['orgStructure_id'].inlist(getOrgStructureDescendants(orgStructureId)))
    else:
        if not personId:
            cond.append(tablePerson['org_id'].eq(QtGui.qApp.currentOrgId()))

    if isOvertime:
        colsOvertime = u'Schedule_Item.overtime,'
        gruopBy = u'Schedule_Item.overtime,'
    else:
        colsOvertime = u''
        gruopBy = u''

    stmt =  '''SELECT
                 COUNT(1) AS cnt,
                %(colsOvertime)s
                 Schedule.person_id,
                 (Schedule.person_id <=> Schedule_Item.recordPerson_id) AS isSamePerson,
                 (Person.org_id <=> RP.org_id) AS isSameOrg,
                 (RP.speciality_id IS NOT NULL) AS recorderHasSpeciality,
                 IF(rbPost.code='6000', 2, Schedule_Item.recordClass) AS recordClassExt,
                 EXISTS(SELECT 1 FROM vVisitExt
                                       WHERE vVisitExt.client_id = Schedule_Item.client_id
                                         AND Person.speciality_id=vVisitExt.speciality_id
                                         AND DATE(vVisitExt.date) = Schedule.date
                       ) AS isVisited
               FROM
                 Schedule_Item
                 LEFT JOIN Schedule     ON Schedule.id = Schedule_Item.master_id
                 LEFT JOIN Person       ON Person.id = Schedule.person_id
                 LEFT JOIN OrgStructure ON OrgStructure.id = Person.orgStructure_id
                 LEFT JOIN Person AS RP ON RP.id = Schedule_Item.recordPerson_id
                 LEFT JOIN rbPost       ON rbPost.id = RP.post_id
                 WHERE %(whereCond)s
               GROUP BY %(groupBy)s person_id, appointmentType, isSamePerson, isSameOrg,
                          recorderHasSpeciality, recordClassExt, isVisited'''
    st=stmt % (dict(colsOvertime = colsOvertime,
                                   whereCond  = db.joinAnd(cond),
                                   groupBy    = gruopBy
                                   ))
    return db.query(st)


class CPreRecordPlanExecutionByDoctors(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Выполнение записи по подразделениям и врачам')


    def getSetupDialog(self, parent):
        result = CPreRecordDoctorsDialog(parent)
        result.setTitle(self.title())
        return result


    def dumpParams(self, cursor, params):
        db = QtGui.qApp.db
        useRecordPeriod     = params.get('useRecordPeriod', True)
        begRecordDate       = params.get('begRecordDate', None)
        endRecordDate       = params.get('endRecordDate', None)
        useSchedulePeriod   = params.get('useSchedulePeriod', False)
        begScheduleDate     = params.get('begScheduleDate', None)
        endScheduleDate     = params.get('endScheduleDate', None)
        orgStructureType    = params.get('orgStructureType', None)
        orgStructureId      = params.get('orgStructureId', None)
        specialityId        = params.get('specialityId', None)
        personId            = params.get('personId', None)
        groupByOrgStructure = params.get('groupByOrgStructure', None)
        hidePersons         = params.get('hidePersons', None)
        description = []

        if useRecordPeriod:
            if begRecordDate or endRecordDate:
                description.append(dateRangeAsStr(u'период постановки в очередь', begRecordDate, endRecordDate))
        if useSchedulePeriod:
            if begScheduleDate or endScheduleDate:
                description.append(dateRangeAsStr(u'период планируемого приёма', begScheduleDate, endScheduleDate))
        description.append(u'тип подразделения: ' + {0: u'Амбулатория', 1: u'Стационар', 2: u'Скорая помощь', 3: u'Мобильная станция', 4: u'Приемное отделение стационара'}.get(orgStructureType, ''))
        if orgStructureId:
            description.append(u'подразделение: ' + getOrgStructureFullName(orgStructureId))
        else:
            description.append(u'подразделение: ЛПУ')
        if specialityId:
            description.append(u'специальность: ' + forceString(db.translate('rbSpeciality', 'id', specialityId, 'name')))
        if personId:
            personInfo = getPersonInfo(personId)
            description.append(u'врач: ' + personInfo['shortName']+', '+personInfo['specialityName'])
        if groupByOrgStructure:
            description.append(u'группировать по подразделениям')
        if hidePersons:
            description.append(u'скрывать детализацию по врачам')

        description.append(u'отчёт составлен: '+forceString(QDateTime.currentDateTime()))
        columns = [ ('100%', [], CReportBase.AlignLeft) ]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()


    def build(self, params):
        #description = '\n'.join(self.getDescription(params))
        isOvertime = params.get('isOvertime', 0)
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()
        self.makeTable(cursor,
                       doc,
                       isOvertime,
                       params,
                       params.get('groupByOrgStructure', None),
                       params.get('hidePersons', None),
                       params.get('orgStructureId', None),
                       params.get('appointmentType', None)
                       )
        return doc


    def analyzeDataOvertime(self, query, params, reportResize):
        reportData = {}

        while query.next():
            record = query.record()
            personId        = forceRef(record.value('person_id'))
            isSamePerson    = forceBool(record.value('isSamePerson'))
            isSameOrg       = forceBool(record.value('isSameOrg'))
            recorderHasSpeciality = forceBool(record.value('recorderHasSpeciality'))
            recordClass     = forceInt(record.value('recordClassExt'))
            isVisited       = forceBool(record.value('isVisited'))
            cnt             = forceInt(record.value('cnt'))
            overtime        = forceBool(record.value('overtime'))

            personData = reportData.get(personId, None)
            if not personData:
                personData = [0]*reportResize
                reportData[personId] = personData
            personData[0] = 0 # план
            if overtime:
                personData[2] += cnt # записано
                if isVisited:
                    personData[4] += cnt # выполнено

                if recordClass == 1: # инфомат
                    personData[18] += cnt # инфомат
                    if isVisited:
                        personData[20] += cnt # инфомат
                elif recordClass == 2:
                    personData[22] += cnt # call-center
                    if isVisited:
                        personData[24] += cnt # call-center
                elif recordClass in (3, 5, 6, 7):
                    personData[26] += cnt # интернет
                    if isVisited:
                        personData[28] += cnt # интернет
                else: # samson
                    if isSamePerson:
                        personData[6] += cnt # актив
                        if isVisited:
                            personData[8] += cnt # актив
                    elif isSameOrg and recorderHasSpeciality:
                        personData[10] += cnt # консультация
                        if isVisited:
                            personData[12] += cnt # консультация
                    elif isSameOrg or personId is None:
                        personData[14] += cnt # сотр.ЛПУ
                        if isVisited:
                            personData[16] += cnt # сотр.ЛПУ
            else:
                personData[1] += cnt # записано
                if isVisited:
                    personData[3] += cnt # выполнено

                if recordClass == 1: # инфомат
                    personData[17] += cnt # инфомат
                    if isVisited:
                        personData[19] += cnt # инфомат
                elif recordClass == 2:
                    personData[21] += cnt # call-center
                    if isVisited:
                        personData[23] += cnt # call-center
                elif recordClass in (3, 5, 6, 7):
                    personData[25] += cnt # интернет
                    if isVisited:
                        personData[27] += cnt # интернет
                else: # samson
                    if isSamePerson:
                        personData[5] += cnt # актив
                        if isVisited:
                            personData[7] += cnt # актив
                    elif isSameOrg and recorderHasSpeciality:
                        personData[9] += cnt # консультация
                        if isVisited:
                            personData[11] += cnt # консультация
                    elif isSameOrg or personId is None:
                        personData[13] += cnt # сотр.ЛПУ
                        if isVisited:
                            personData[15] += cnt # сотр.ЛПУ

        begRecordDate     = params.get('begRecordDate', None)
        endRecordDate     = params.get('endRecordDate', None)
        useSchedulePeriod = params.get('useSchedulePeriod', False)
        begScheduleDate   = params.get('begScheduleDate', None)
        endScheduleDate   = params.get('endScheduleDate', None)

        if useSchedulePeriod:
            begDate = begScheduleDate
            endDate = endScheduleDate
        else:
            begDate = begRecordDate
            endDate = endRecordDate

        if reportData:
            appointmentType = params.get('appointmentType', CSchedule.atAmbulance)
            db = QtGui.qApp.db
            stmt = '''select person_id, SUM(capacity) from Schedule
                where person_id in (%s) and date between DATE(%s) and DATE(%s)
                    and appointmentType = %i and deleted = 0 group by person_id''' % (','.join([str(x) for x in reportData.keys()]),
                    db.formatDate(begDate), db.formatDate(endDate), appointmentType)

            query = db.query(stmt)
            while query.next():
                record = query.record()
                personId = forceInt(record.value(0))
                capacity = forceInt(record.value(1))
                reportData[personId][0] = capacity
        return reportData


    def analyzeData(self, query, params, reportResize):
        reportData = {}

        while query.next():
            record = query.record()
            personId        = forceRef(record.value('person_id'))
            isSamePerson    = forceBool(record.value('isSamePerson'))
            isSameOrg       = forceBool(record.value('isSameOrg'))
            recorderHasSpeciality = forceBool(record.value('recorderHasSpeciality'))
            recordClass     = forceInt(record.value('recordClassExt'))
            isVisited       = forceBool(record.value('isVisited'))
            cnt             = forceInt(record.value('cnt'))

            personData = reportData.get(personId, None)
            if not personData:
                personData = [0]*reportResize
                reportData[personId] = personData
            personData[0] = 0 # план
            personData[1] += cnt # записано
            if isVisited:
                personData[2] += cnt # выполнено

            if recordClass == 1: # инфомат
                personData[9] += cnt # инфомат
                if isVisited:
                    personData[10] += cnt # инфомат
            elif recordClass == 2:
                personData[11] += cnt # call-center
                if isVisited:
                    personData[12] += cnt # call-center
            elif recordClass in (3, 5, 6, 7):
                personData[13] += cnt # интернет
                if isVisited:
                    personData[14] += cnt # интернет
            else: # samson
                if isSamePerson:
                    personData[3] += cnt # актив
                    if isVisited:
                        personData[4] += cnt # актив
                elif isSameOrg and recorderHasSpeciality:
                    personData[5] += cnt # консультация
                    if isVisited:
                        personData[6] += cnt # консультация
                elif recordClass==0:
                    personData[7] += cnt # сотр.ЛПУ
                    if isVisited:
                        personData[8] += cnt # сотр.ЛПУ
                        

        begRecordDate     = params.get('begRecordDate', None)
        endRecordDate     = params.get('endRecordDate', None)
        useSchedulePeriod = params.get('useSchedulePeriod', False)
        begScheduleDate   = params.get('begScheduleDate', None)
        endScheduleDate   = params.get('endScheduleDate', None)

        if useSchedulePeriod:
            begDate = begScheduleDate
            endDate = endScheduleDate
        else:
            begDate = begRecordDate
            endDate = endRecordDate

        if reportData:
            appointmentType = params.get('appointmentType', CSchedule.atAmbulance)
            db = QtGui.qApp.db
            stmt = '''select person_id, SUM(capacity) from Schedule
                where person_id in (%s) and date between DATE(%s) and DATE(%s)
                    and appointmentType = %i and deleted = 0 group by person_id''' % (','.join([str(x) for x in reportData.keys()]),
                    db.formatDate(begDate), db.formatDate(endDate), appointmentType)

            query = db.query(stmt)
            while query.next():
                record = query.record()
                personId = forceInt(record.value(0))
                capacity = forceInt(record.value(1))
                reportData[personId][0] = capacity
        return reportData


    def getPersonSortedList(self, personIdList):
        result = []
        db = QtGui.qApp.db
        tablePerson = db.table('Person')
        for record in db.getRecordList(tablePerson, ['id','lastName', 'firstName', 'patrName'], tablePerson['id'].inlist(personIdList)):
            name = formatName(record.value('lastName'), record.value('firstName'), record.value('patrName'))
            personId = forceRef(record.value('id'))
            result.append(('', name, personId, None))
        result.sort()
        return result


    def getOrgStructureAndPersonSortedList(self, personIdList, topOrgStructureId):
        result = []
        db = QtGui.qApp.db

        mapOSIdtoSubTopOSId = {}

        def traceOrgStructureUp(orgStructureId):
            if orgStructureId in mapOSIdtoSubTopOSId:
                return mapOSIdtoSubTopOSId[orgStructureId]
            id = orgStructureId
            if id is None or id == topOrgStructureId:
                mapOSIdtoSubTopOSId[orgStructureId] = id
                return id
            while True:
                parentId = forceRef(db.translate('OrgStructure', 'id', id, 'parent_id'))
                if parentId is None or parentId == topOrgStructureId:
                    mapOSIdtoSubTopOSId[orgStructureId] = id
                    return id
                id = parentId

        tablePerson = db.table('Person')
        for record in db.getRecordList(tablePerson, ['id','lastName', 'firstName', 'patrName', 'orgStructure_id'], tablePerson['id'].inlist(personIdList)):
            name = formatName(record.value('lastName'), record.value('firstName'), record.value('patrName'))
            personId = forceRef(record.value('id'))
            orgStructureId = traceOrgStructureUp(forceRef(record.value('orgStructure_id')))
            result.append((getOrgStructureFullName(orgStructureId), name, personId, orgStructureId))
        result.sort()
        return result


    def makeTable(self, cursor, doc, isOvertime, params, groupByOrgStructure, hidePersons, topOrgStructureId, appointmentType):
        if isOvertime:
            type = u'На дому' if appointmentType == CSchedule.atHome else u'Амбулаторно'
            tableColumns = [('3%', [u'№',               u'',              u'',           u'',           u'',     u''],           CReportBase.AlignLeft),
                            ('8%', [u'Врачи',           u'',              u'',           u'',           u'',     u''],           CReportBase.AlignLeft),
                            ('3%', [type,               u'План',          u'',           u'',           u'',     u''],           CReportBase.AlignRight),
                            ('3%', [u'',                u'Запись',        u'',           u'',           u'',     u'планово'],    CReportBase.AlignRight),
                            ('3%', [u'',                u'',              u'',           u'',           u'',     u'сверхплана'], CReportBase.AlignRight),
                            ('3%', [u'',                u'Выполнено',     u'',           u'',           u'',     u'планово'],    CReportBase.AlignRight),
                            ('3%', [u'',                u'',              u'',           u'',           u'',     u'сверхплана'], CReportBase.AlignRight),
                            ('3%', [u'',                u'Актив',         u'',           u'',           u'зап.', u'планово'],    CReportBase.AlignRight),
                            ('3%', [u'',                u'',              u'',           u'',           u'',     u'сверхплана'], CReportBase.AlignRight),
                            ('3%', [u'',                u'',              u'',           u'',           u'вып.', u'планово'],    CReportBase.AlignRight),
                            ('3%', [u'',                u'',              u'',           u'',           u'',     u'сверхплана'], CReportBase.AlignRight),
                            ('3%', [u'',                u'Консультация',  u'',           u'',           u'зап.', u'планово'],    CReportBase.AlignRight),
                            ('3%', [u'',                u'',              u'',           u'',           u'',     u'сверхплана'], CReportBase.AlignRight),
                            ('3%', [u'',                u'',              u'',           u'',           u'вып.', u'планово'],    CReportBase.AlignRight),
                            ('3%', [u'',                u'',              u'',           u'',           u'',     u'сверхплана'], CReportBase.AlignRight),
                            ('3%', [u'',                u'Первично',      u'Сотр. ЛПУ',  u'',           u'зап.', u'планово'],    CReportBase.AlignRight),
                            ('3%', [u'',                u'',              u'',           u'',           u'',     u'сверхплана'], CReportBase.AlignRight),
                            ('3%', [u'',                u'',              u'',           u'',           u'вып.', u'планово'],    CReportBase.AlignRight),
                            ('3%', [u'',                u'',              u'',           u'',           u'',     u'сверхплана'], CReportBase.AlignRight),
                            ('3%', [u'',                u'',              u'Не свои',    u'Инфомат',    u'зап.', u'планово'],    CReportBase.AlignRight),
                            ('3%', [u'',                u'',              u'',           u'',           u'',     u'сверхплана'], CReportBase.AlignRight),
                            ('3%', [u'',                u'',              u'',           u'',           u'вып.', u'планово'],    CReportBase.AlignRight),
                            ('3%', [u'',                u'',              u'',           u'',           u'',     u'сверхплана'], CReportBase.AlignRight),
                            ('3%', [u'',                u'',              u'',           u'Call-центр', u'зап.', u'планово'],    CReportBase.AlignRight),
                            ('3%', [u'',                u'',              u'',           u'',           u'',     u'сверхплана'], CReportBase.AlignRight),
                            ('3%', [u'',                u'',              u'',           u'',           u'вып.', u'планово'],    CReportBase.AlignRight),
                            ('3%', [u'',                u'',              u'',           u'',           u'',     u'сверхплана'], CReportBase.AlignRight),
                            ('3%', [u'',                u'',              u'',           u'Интернет',   u'зап.', u'планово'],    CReportBase.AlignRight),
                            ('3%', [u'',                u'',              u'',           u'',           u'',     u'сверхплана'], CReportBase.AlignRight),
                            ('3%', [u'',                u'',              u'',           u'',           u'вып.', u'планово'],    CReportBase.AlignRight),
                            ('3%', [u'',                u'',              u'',           u'',           u'',     u'сверхплана'], CReportBase.AlignRight)
                           ]

            table = createTable(cursor, tableColumns)
            table.mergeCells(0, 0, 6, 1)
            table.mergeCells(0, 1, 6, 1)
            table.mergeCells(0, 2, 1, 29)
            table.mergeCells(1, 2, 5, 1)
            table.mergeCells(1, 3, 4, 2)
            table.mergeCells(2, 3, 4, 1)
            table.mergeCells(2, 4, 4, 1)
            table.mergeCells(1, 5, 4, 2)
            table.mergeCells(2, 5, 4, 1)
            table.mergeCells(2, 6, 4, 1)
            table.mergeCells(1, 7, 3, 4)
            table.mergeCells(4, 7, 1, 2)
            table.mergeCells(4, 9, 1, 2)
            table.mergeCells(1, 11, 3, 4)
            table.mergeCells(4, 11, 1, 2)
            table.mergeCells(4, 13, 1, 2)
            table.mergeCells(1, 15, 1, 16)
            table.mergeCells(2, 15, 2, 4)
            table.mergeCells(4, 15, 1, 2)
            table.mergeCells(4, 17, 1, 2)
            table.mergeCells(2, 19, 1, 12)
            table.mergeCells(3, 19, 1, 4)
            table.mergeCells(4, 19, 1, 2)
            table.mergeCells(4, 21, 1, 2)
            table.mergeCells(3, 23, 1, 4)
            table.mergeCells(4, 23, 1, 2)
            table.mergeCells(4, 25, 1, 2)
            table.mergeCells(3, 27, 1, 4)
            table.mergeCells(4, 27, 1, 2)
            table.mergeCells(4, 29, 1, 2)
        else:
            type = u'На дому' if appointmentType == CSchedule.atHome else u'Амбулаторно'
            tableColumns = [('5%', [u'№',                      u'',          u'',           u''],     CReportBase.AlignLeft),
                            ('15%',[u'Врачи',                  u'',          u'',           u''],     CReportBase.AlignLeft),
                            ('5%', [type,     u'План',         u'',          u'',           u''],     CReportBase.AlignRight),
                            ('5%', [u'',      u'Запись',       u'',          u'',           u''],     CReportBase.AlignRight),
                            ('5%', [u'',      u'Выполнено',    u'',          u'',           u''],     CReportBase.AlignRight),
                            ('5%', [u'',      u'Актив',        u'',          u'',           u'зап.'], CReportBase.AlignRight),
                            ('5%', [u'',      u'',             u'',          u'',           u'вып.'], CReportBase.AlignRight),
                            ('5%', [u'',      u'Консультация', u'',          u'',           u'зап.'], CReportBase.AlignRight),
                            ('5%', [u'',      u'',             u'',          u'',           u'вып.'], CReportBase.AlignRight),
                            ('5%', [u'',      u'Первично',     u'Сотр. ЛПУ', u'',           u'зап.'], CReportBase.AlignRight),
                            ('5%', [u'',      u'',             u'',          u'',           u'вып.'], CReportBase.AlignRight),
                            ('5%', [u'',      u'',             u'Не свои',   u'Инфомат',    u'зап.'], CReportBase.AlignRight),
                            ('5%', [u'',      u'',             u'',          u'',           u'вып.'], CReportBase.AlignRight),
                            ('5%', [u'',      u'',             u'',          u'Call-центр', u'зап.'], CReportBase.AlignRight),
                            ('5%', [u'',      u'',             u'',          u'',           u'вып.'], CReportBase.AlignRight),
                            ('5%', [u'',      u'',             u'',          u'Интернет',   u'зап.'], CReportBase.AlignRight),
                            ('5%', [u'',      u'',             u'',          u'',           u'вып.'], CReportBase.AlignRight)
                           ]

            table = createTable(cursor, tableColumns)
            table.mergeCells(0, 0, 5, 1)
            table.mergeCells(0, 1, 5, 1)
            table.mergeCells(0, 2, 1, 16)
            table.mergeCells(1, 2, 4, 1)
            table.mergeCells(1, 3, 4, 1)
            table.mergeCells(1, 4, 4, 1)
            table.mergeCells(1, 5, 3, 2)
            table.mergeCells(1, 7, 3, 2)
            table.mergeCells(1, 9, 1, 8)
            table.mergeCells(2, 9, 2, 2)
            table.mergeCells(1, 10, 1, 8)
            table.mergeCells(2, 11, 1, 6)
            table.mergeCells(3, 11, 1, 2)
            table.mergeCells(3, 13, 1, 2)
            table.mergeCells(3, 15, 1, 2)

        reportResize = len(tableColumns) - 2
        reportData = self.analyzeDataOvertime(selectData(params), params, reportResize) if isOvertime else self.analyzeData(selectData(params), params, reportResize)

        total = [0]*reportResize
        n = 1
        personIdList = reportData.keys()
        if groupByOrgStructure:
            keyList = self.getOrgStructureAndPersonSortedList(personIdList, topOrgStructureId)
        else:
            keyList = self.getPersonSortedList(personIdList)

        prevOrgStructureName = None
        prevOrgStructureId = None
        orgStructureTotal = [0]*reportResize
        for orgStructureName, name, personId, orgStructureId in keyList:
            if prevOrgStructureId != orgStructureId:
                if prevOrgStructureName is not None:
                    i = table.addRow()
                    table.setText(i, 0, n, CReportBase.TableTotal)
                    n += 1
                    table.setText(i, 1, u'Всего по '+prevOrgStructureName, CReportBase.TableTotal)
                    for column in xrange(reportResize):
                        table.setText(i, column+2, orgStructureTotal[column], CReportBase.TableTotal)
                prevOrgStructureName = orgStructureName
                prevOrgStructureId = orgStructureId
                orgStructureTotal = [0]*reportResize

            personData = reportData[personId]
            if not hidePersons:
                i = table.addRow()
                table.setText(i, 0, n)
                n += 1
                table.setText(i, 1, name)
                for column in xrange(reportResize):
                    table.setText(i, column+2, personData[column])
            for column in xrange(reportResize):
                orgStructureTotal[column] += personData[column]
                total[column] += personData[column]

        if prevOrgStructureName is not None:
            i = table.addRow()
            table.setText(i, 0, n, CReportBase.TableTotal)
            n += 1
            table.setText(i, 1, u'Всего по '+prevOrgStructureName, CReportBase.TableTotal)
            for column in xrange(reportResize):
                table.setText(i, column+2, orgStructureTotal[column], CReportBase.TableTotal)

        i  = table.addRow()
        table.setText(i, 0, n, CReportBase.TableTotal)
        table.setText(i, 1, u'ИТОГО', CReportBase.TableTotal)
        for column in xrange(reportResize):
            table.setText(i, column+2, total[column], CReportBase.TableTotal)

#def checkIsCallCenter(actionNote):
#    actionNote = actionNote.upper()
#    if 'CALL' in actionNote:
#        return True
#    elif 'MIACPROTOCOL' in actionNote:
#        value = trim(actionNote.lstrip('MIACPROTOCOL'))
#        if value:
#            if ':' in value:
#                operatorRole = value.split(':')[0]
#                return operatorRole == u'ОПЕРАТОР'
#    return False


#class CPreRecordDoctorsEx(CPreRecordDoctors):
#    def exec_(self):
#        CPreRecordDoctors.exec_(self)
#
#    def getSetupDialog(self, parent):
#        result = CPreRecordDoctorsDialog(parent)
#        result.setTitle(self.title())
#        return result
#
#    def build(self, params):
#        return CPreRecordDoctors.build(self, '\n'.join(self.getDescription(params)), params)


class CPreRecordDoctorsDialog(CDialogBase, Ui_PreRecordPlanExecutionByDoctorsDialog):
    def __init__(self, parent=None):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.cmbSpeciality.setTable('rbSpeciality', True)
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())
        self.cmbAppointmentType.clear()
        self.cmbAppointmentType.addItem(CSchedule.atNames[CSchedule.atAmbulance])
        self.cmbAppointmentType.addItem(CSchedule.atNames[CSchedule.atHome])


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        date = QDate.currentDate().addDays(-3)
        self.chkRecordPeriod.setChecked(params.get('useRecordPeriod', True))
        self.edtBegRecordDate.setDate(params.get('begRecordDate', firstMonthDay(date)))
        self.edtEndRecordDate.setDate(params.get('endRecordDate', lastMonthDay(date)))
        self.chkSchedulePeriod.setChecked(params.get('useSchedulePeriod', True))
        self.edtBegScheduleDate.setDate(params.get('begScheduleDate', QDate.currentDate()))
        self.edtEndScheduleDate.setDate(params.get('endScheduleDate', QDate.currentDate()))
        self.cmbOrgStructureType.setCurrentIndex(params.get('orgStructureType', 0))
        self.cmbOrgStructureType.setCurrentIndex(params.get('orgStructureType', 0))
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))
        self.cmbSpeciality.setValue(params.get('specialityId', None))
        self.cmbPerson.setValue(params.get('personId', None))
        self.chkGroupByOrgStructure.setChecked(bool(params.get('groupByOrgStructure', None)))
        self.chkHidePersons.setChecked(bool(params.get('hidePersons', None)))
        if params.get('appointmentType', CSchedule.atAmbulance) == CSchedule.atHome:
            self.cmbAppointmentType.setCurrentIndex(1)
        else:
            self.cmbAppointmentType.setCurrentIndex(0)
        self.chkOvertime.setChecked(params.get('isOvertime', False))


    def params(self):
        return dict(useRecordPeriod   = self.chkRecordPeriod.isChecked(),
                    begRecordDate     = self.edtBegRecordDate.date(),
                    endRecordDate     = self.edtEndRecordDate.date(),
                    useSchedulePeriod = self.chkSchedulePeriod.isChecked(),
                    begScheduleDate   = self.edtBegScheduleDate.date(),
                    endScheduleDate   = self.edtEndScheduleDate.date(),
                    orgStructureType  = self.cmbOrgStructureType.currentIndex(),
                    orgStructureId    = self.cmbOrgStructure.value(),
                    specialityId      = self.cmbSpeciality.value(),
                    personId          = self.cmbPerson.value(),
                    groupByOrgStructure = self.chkGroupByOrgStructure.isChecked(),
                    hidePersons       = self.chkHidePersons.isChecked(),
                    appointmentType   = CSchedule.atAmbulance if self.cmbAppointmentType.currentIndex() == 0 else CSchedule.atHome,
                    isOvertime        = self.chkOvertime.isChecked()
                   )


    @pyqtSignature('QDate')
    def on_edtBegRecordDate_dateChanged(self, date):
        self.cmbPerson.setBegDate(date)


    @pyqtSignature('QDate')
    def on_edtEndRecordDate_dateChanged(self, date):
        self.cmbPerson.setEndDate(date)


#    @pyqtSignature('bool')
#    def on_chkPeriodRecord_clicked(self, checked):
#        self.edtBegDate.setEnabled(checked)
#        self.edtEndDate.setEnabled(checked)
#        if checked:
#            self.edtBegDate.setFocus(Qt.OtherFocusReason)
#
#
#    @pyqtSignature('bool')
#    def on_chkPeriodBeforeRecord_clicked(self, checked):
#        self.edtBegDateRecord.setEnabled(checked)
#        self.edtEndDateRecord.setEnabled(checked)


    @pyqtSignature('QDate')
    def on_edtBegDate_dateChanged(self, date):
        self.cmbPerson.setBegDate(date)


    @pyqtSignature('QDate')
    def on_edtEndDate_dateChanged(self, date):
        self.cmbPerson.setEndDate(date)


    @pyqtSignature('int')
    def on_cmbOrgStructure_currentIndexChanged(self, index):
        orgStructureId = self.cmbOrgStructure.value()
        self.cmbPerson.setOrgStructureId(orgStructureId)


    @pyqtSignature('int')
    def on_cmbSpeciality_currentIndexChanged(self, index):
        specialityId = self.cmbSpeciality.value()
        self.cmbPerson.setSpecialityId(specialityId)
