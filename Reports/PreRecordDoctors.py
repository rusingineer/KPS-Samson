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
from PyQt4.QtCore       import pyqtSignature, QDate, QDateTime

from Orgs.Utils         import getOrgStructureDescendants, getOrgStructureFullName, getPersonInfo
from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable
from Reports.Utils      import dateRangeAsStr
from Timeline.Schedule  import CSchedule
from library.DialogBase import CDialogBase
from library.Utils import firstMonthDay, forceBool, forceInt, forceRef, forceString, formatName, lastMonthDay, getPersonIdList

from Ui_PreRecordDoctorsDialog import Ui_PreRecordDoctorsDialog


def selectData(params):
    useRecordPeriod   = params.get('useRecordPeriod', True)
    begRecordDate     = params.get('begRecordDate', None)
    endRecordDate     = params.get('endRecordDate', None)
    useSchedulePeriod = params.get('useSchedulePeriod', False)
    begScheduleDate   = params.get('begScheduleDate', None)
    endScheduleDate   = params.get('endScheduleDate', None)
    orgStructureId    = params.get('orgStructureId', None)
    specialityId      = params.get('specialityId', None)
    personId          = params.get('personId', None)
    isOvertime        = params.get('isOvertime', 0)
    showDeleted        = params.get('showDeleted', 0)
    joinPersonBySNILS = params.get('joinPersonBySNILS', None)

    db = QtGui.qApp.db
    tablePerson = db.table('Person')
    tableSchedule = db.table('Schedule')
    tableScheduleItem = db.table('Schedule_Item')

    cond = [ tableScheduleItem['client_id'].isNotNull(), 
           ]

    if not showDeleted:
        cond.append(tableSchedule['deleted'].eq(0))
        cond.append(tableScheduleItem['deleted'].eq(0))
    if useRecordPeriod:
        if begRecordDate:
            cond.append(tableScheduleItem['recordDatetime'].ge(begRecordDate))
        if endRecordDate:
            cond.append(tableScheduleItem['recordDatetime'].lt(endRecordDate.addDays(1)))
    if useSchedulePeriod:
        if begScheduleDate:
            cond.append(tableSchedule['date'].ge(begScheduleDate))
        if endScheduleDate:
            cond.append(tableSchedule['date'].le(endScheduleDate))
    if personId:
        duplicatePersons = []
        if joinPersonBySNILS:
            duplicates = getPersonIdList(personId)
            if duplicates:
                for duplicate in duplicates:
                    duplicatePersons.append(forceRef(duplicate.value('id')))
        if not duplicatePersons:
            duplicatePersons.append(personId)
        cond.append(tableSchedule['person_id'].inlist(duplicatePersons))
    if specialityId:
        cond.append(tablePerson['speciality_id'].eq(specialityId))
    if orgStructureId:
        cond.append(tablePerson['orgStructure_id'].inlist(getOrgStructureDescendants(orgStructureId)))
    else:
        if not personId:
            cond.append(tablePerson['org_id'].eq(QtGui.qApp.currentOrgId()))
    if isOvertime:
        colsOvertime = u'Schedule_Item.overtime, Schedule_Item.isUrgent,'
        groupBy = u'Schedule_Item.overtime, Schedule_Item.isUrgent,'
    else:
        colsOvertime = u''
        groupBy = u''
    stmt = '''
            SELECT
                COUNT(1) AS cnt,
                %(colsOvertime)s
                Schedule.person_id,
                Schedule.appointmentType,
                (Schedule.person_id <=> Schedule_Item.recordPerson_id) AS isSamePerson,
                (Person.org_id <=> RP.org_id) AS isSameOrg,
                (RP.speciality_id IS NOT NULL) AS recorderHasSpeciality,
                IF(rbPost.code='6000', 2, Schedule_Item.recordClass) AS recordClassExt,
                EXISTS(SELECT 1 FROM vVisitExt
                                WHERE vVisitExt.client_id = Schedule_Item.client_id
                                    AND Person.speciality_id=vVisitExt.speciality_id
                                    AND DATE(vVisitExt.date) = Schedule.date) AS isVisited,
                Schedule_Item.recordClass,
                Schedule_Item.recordPerson_id,
                IF(Schedule_Item.recordClass = 2, Schedule_Item.note,
              (SELECT vrbP.name FROM vrbPersonWithSpeciality AS vrbP WHERE vrbP.id = Schedule_Item.recordPerson_id)) AS recordPersonName,
                                    count((SELECT max(cp.id) AS cli FROM ClientPolicy cp
  LEFT JOIN Organisation o ON cp.insurer_id=o.id
  WHERE cp.client_id=Schedule_Item.client_id AND cp.deleted=0 AND o.deleted=0 AND o.area not LIKE '23%%')) AS inkray,Schedule_Item.note, Schedule_Item.system_guid
            FROM
                Schedule_Item
                LEFT JOIN Schedule     ON Schedule.id = Schedule_Item.master_id
                LEFT JOIN Person       ON Person.id = Schedule.person_id
                LEFT JOIN Person AS RP ON RP.id = Schedule_Item.recordPerson_id
                LEFT JOIN rbPost       ON rbPost.id = RP.post_id
            WHERE %(whereCond)s
            GROUP BY %(groupBy)s (SELECT vrbP.name FROM vrbPersonWithSpeciality AS vrbP WHERE vrbP.id = Person.id), appointmentType, isSamePerson, isSameOrg,
                      recorderHasSpeciality, recordClassExt, isVisited, recordPersonName, recordPerson_id, system_guid '''
    st = stmt % (dict(colsOvertime=colsOvertime,
                 whereCond=db.joinAnd(cond),
                 groupBy=groupBy
                 ))
    return db.query(st)


class CPreRecordDoctors(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Предварительная запись по подразделениям и врачам')


    def dumpParams(self, cursor, params):
        db = QtGui.qApp.db
        useRecordPeriod     = params.get('useRecordPeriod', True)
        begRecordDate       = params.get('begRecordDate', None)
        endRecordDate       = params.get('endRecordDate', None)
        useSchedulePeriod   = params.get('useSchedulePeriod', False)
        begScheduleDate     = params.get('begScheduleDate', None)
        endScheduleDate     = params.get('endScheduleDate', None)
        orgStructureId      = params.get('orgStructureId', None)
        specialityId        = params.get('specialityId', None)
        personId            = params.get('personId', None)
        groupByOrgStructure = params.get('groupByOrgStructure', None)
        hidePersons         = params.get('hidePersons', None)
        joinPersonBySNILS   = params.get('joinPersonBySNILS', None)
        showDeleted         = params.get('showDeleted', None)
        description = []

        if useRecordPeriod:
            if begRecordDate or endRecordDate:
                description.append(dateRangeAsStr(u'период постановки в очередь', begRecordDate, endRecordDate))
        if useSchedulePeriod:
            if begScheduleDate or endScheduleDate:
                description.append(dateRangeAsStr(u'период планируемого приёма', begScheduleDate, endScheduleDate))
        if orgStructureId:
            description.append(u'подразделение: ' + getOrgStructureFullName(orgStructureId))
        else:
            description.append(u'подразделение: ЛПУ')
        if specialityId:
            description.append(u'специальность: ' + forceString(db.translate('rbSpeciality', 'id', specialityId, 'name')))
        if personId:
            personInfo = getPersonInfo(personId)
            if joinPersonBySNILS:
                description.append(u'врач: ' + personInfo['shortName'])
            else:
                description.append(u'врач: ' + personInfo['shortName']+', '+personInfo['specialityName'])
        if groupByOrgStructure:
            description.append(u'группировать по подразделениям')
        if hidePersons:
            description.append(u'скрывать детализацию по врачам')
        if showDeleted:
            description.append(u'учитывать удаленные записи')

        description.append(u'отчёт составлен: '+forceString(QDateTime.currentDateTime()))
        columns = [ ('100%', [], CReportBase.AlignLeft) ]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()


    def build(self, description, params):
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
                       params.get('orgStructureId', None)
                       )
        return doc


    def analyzeData(self, query, detailCallCenter, reportRowSize):
        mapATtoCol = { CSchedule.atAmbulance:0, CSchedule.atHome:8 }
        reportData = {}
        while query.next():
            record = query.record()
            personId        = forceRef(record.value('person_id'))
            appointmentType = forceInt(record.value('appointmentType'))
            isSamePerson    = forceBool(record.value('isSamePerson'))
            isSameOrg       = forceBool(record.value('isSameOrg'))
            recorderHasSpeciality = forceBool(record.value('recorderHasSpeciality'))
            recordClass     = forceInt(record.value('recordClassExt'))
            recordNote     = forceString(record.value('note'))
            isVisited       = forceBool(record.value('isVisited'))
            cnt             = forceInt(record.value('cnt'))
            inkray             = forceInt(record.value('inkray'))
            sysGuid         = forceString(record.value('system_guid'))
            column = mapATtoCol.get(appointmentType, -1)
            if column>=0:
                personData = reportData.setdefault(personId, {})
                if recordClass == 1: # Инфомат
                    recordPersonName = u'Инфомат'
                elif recordClass == 2 or u'цто' in recordNote: # call-центр
                    if detailCallCenter:
                        recordPersonName = u'Call-центр ' + forceString(record.value('recordPersonName'))
                    else:
                        recordPersonName = u'Call-центр'
                elif recordClass  in (3, 5, 6, 7): # интернет
                    if sysGuid == u'075AEF71-C1C6-46B7-BE97-931037F03E2A':
                        recordPersonName = u'Мессенджер MAX'
                    elif sysGuid == u'4001E5F6-E96D-4742-8561-C81C838E9064':
                        recordPersonName = u'Портал госуслуг'
                    elif sysGuid == u'D127D963-EB51-4624-8778-F0508CE67648':
                        recordPersonName = u'Кубань-онлайн'
                    else:
                        recordPersonName = u'Интернет'
                else: #
                    if forceRef(record.value('recordPerson_id')):
                        recordPersonName = forceString(record.value('recordPersonName'))
                    else:
                        recordPersonName = 'demo'
                recordKey = (recordClass, recordPersonName)
                recordData = personData.get(recordKey, None)
                if recordData is None:
                    personData[recordKey] = recordData = [0]*reportRowSize
                recordData[column] += cnt # всего
                if appointmentType == 2:
                    recordData[column+8] += inkray # инкрай
                else:
                    recordData[column+16] += inkray # инкрай
                if isVisited:
                    recordData[column+1] += cnt # выполнено
                if recordClass == 1: # инфомат
                    recordData[column+5] += cnt # инфомат
                elif recordClass == 2:
                    recordData[column+6] += cnt # call-center
                elif recordClass  in (3, 5, 6, 7):
                    recordData[column+7] += cnt # интернет
                else: # samson
                    if isSamePerson:
                        recordData[column+2] += cnt # актив
                    elif isSameOrg and recorderHasSpeciality:
                        recordData[column+3] += cnt # консультация
                    elif isSameOrg or personId is None:
                        recordData[column+4] += cnt # сотр.ЛПУ
        return reportData


    def analyzeDataOvertime(self, query, detailCallCenter, reportRowSize):
        mapATtoCol = { CSchedule.atAmbulance:0, CSchedule.atHome:16 }
        reportData = {}
        while query.next():
            record = query.record()
            personId        = forceRef(record.value('person_id'))
            appointmentType = forceInt(record.value('appointmentType'))
            isSamePerson    = forceBool(record.value('isSamePerson'))
            isSameOrg       = forceBool(record.value('isSameOrg'))
            recorderHasSpeciality = forceBool(record.value('recorderHasSpeciality'))
            recordClass     = forceInt(record.value('recordClassExt'))
            isVisited       = forceBool(record.value('isVisited'))
            cnt             = forceInt(record.value('cnt'))
            inkray             = forceInt(record.value('inkray'))
            overtime        = forceBool(record.value('overtime'))
            #recordClass     = forceInt(record.value('recordClass'))
            recordNote = forceString(record.value('note'))
            isUrgent = forceBool(record.value('isUrgent'))
            sysGuid = forceString(record.value('system_guid'))
            column = mapATtoCol.get(appointmentType, -1)
            if column>=0:
                personData = reportData.setdefault(personId, {})
                if recordClass == 1: # Инфомат
                    recordPersonName = u'Инфомат'
                elif recordClass == 2 or u'цто' in recordNote: # call-центр
                    if detailCallCenter:
                        recordPersonName = u'Call-центр ' + forceString(record.value('recordPersonName'))
                    else:
                        recordPersonName = u'Call-центр'
                elif recordClass  in (3, 5, 6, 7): # интернет
                    if sysGuid == u'075AEF71-C1C6-46B7-BE97-931037F03E2A':
                        recordPersonName = u'Мессенджер MAX'
                    elif sysGuid == u'4001E5F6-E96D-4742-8561-C81C838E9064':
                        recordPersonName = u'Портал госуслуг'
                    elif sysGuid == u'D127D963-EB51-4624-8778-F0508CE67648':
                        recordPersonName = u'Кубань-онлайн'
                    else:
                        recordPersonName = u'Интернет'
                else: #
                    if forceRef(record.value('recordPerson_id')):
                        recordPersonName = forceString(record.value('recordPersonName'))
                    else:
                        recordPersonName = 'demo'
                recordKey = (recordClass, recordPersonName)
                recordData = personData.get(recordKey, None)
                if recordData is None:
                    personData[recordKey] = recordData = [0]*reportRowSize
                if overtime:
                    recordData[column+1] += cnt # всего
                    if appointmentType==2:
                        recordData[column+16] += inkray # инкрай
                        recordData[column+17] += cnt if isUrgent else 0 # сверхплана неотложно
                    else:
                        recordData[column+32] += inkray # инкрай
                        recordData[column+33] += cnt if isUrgent else 0 # сверхплана неотложно
                    if isVisited:
                        recordData[column+3] += cnt # выполнено
                    if recordClass == 1: # инфомат
                        recordData[column+11] += cnt # инфомат
                    elif recordClass == 2:
                        recordData[column+13] += cnt # call-center
                    elif recordClass in (3, 5, 6, 7):
                        recordData[column+15] += cnt # интернет
                    else: # samson
                        if isSamePerson:
                            recordData[column+5] += cnt # актив
                        elif isSameOrg and recorderHasSpeciality:
                            recordData[column+7] += cnt # консультация
                        elif isSameOrg or personId is None:
                            recordData[column+9] += cnt # сотр.ЛПУ
                else:
                    recordData[column] += cnt # всего
                    if appointmentType==2:
                        recordData[column+16] += inkray # инкрай
                        recordData[column+17] += cnt if isUrgent else 0 # сверхплана неотложно
                    else:
                        recordData[column+32] += inkray # инкрай
                        recordData[column+33] += cnt if isUrgent else 0 # сверхплана неотложно
                    if isVisited:
                        recordData[column+2] += cnt # выполнено
                    if recordClass == 1: # инфомат
                        recordData[column+10] += cnt # инфомат
                    elif recordClass == 2:
                        recordData[column+12] += cnt # call-center
                    elif recordClass in (3, 5, 6, 7):
                        recordData[column+14] += cnt # интернет
                    else: # samson
                        if isSamePerson:
                            recordData[column+4] += cnt # актив
                        elif isSameOrg and recorderHasSpeciality:
                            recordData[column+6] += cnt # консультация
                        elif isSameOrg or personId is None:
                            recordData[column+8] += cnt # сотр.ЛПУ
        return reportData


    def getPersonSortedList(self, personIdList):
        result = []
        db = QtGui.qApp.db
        tablePerson = db.table('vrbPersonWithSpecialityAndOrgStr')
        for record in db.getRecordList(tablePerson, ['id', 'name'], tablePerson['id'].inlist(personIdList)):
            #name = formatName(record.value('lastName'), record.value('firstName'), record.value('patrName'))
            name = forceString(record.value('name'))
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
        result.sort(key=lambda x: (x[0], x[3], x[2], x[1]))
        return result


    def makeTable(self, cursor, doc, isOvertime, params, groupByOrgStructure, hidePersons, topOrgStructureId):
        detailCallCenter= params.get('detailCallCenter', False)
        if isOvertime:
            tableColumns = [('4%',   [u'№',               u'',              u'',          u'',           u''],           CReportBase.AlignLeft),
                            ('8%',   [u'Записал',         u'',              u'',          u'',           u''],           CReportBase.AlignLeft),
                            ('2.5%', [u'Амбулаторно',     u'Всего',         u'',          u'',           u'планово'],    CReportBase.AlignRight),
                            ('2.5%', [u'',                u'',              u'',          u'',           u'сверхплана'], CReportBase.AlignRight),
                            ('2.5%', [u'',                u'Выполнено',     u'',          u'',           u'планово'],    CReportBase.AlignRight),
                            ('2.5%', [u'',                u'',              u'',          u'',           u'сверхплана'], CReportBase.AlignRight),
                            ('2.5%', [u'',                u'Актив',         u'',          u'',           u'планово'],    CReportBase.AlignRight),
                            ('2.5%', [u'',                u'',              u'',          u'',           u'сверхплана'], CReportBase.AlignRight),
                            ('2.5%', [u'',                u'Консультация',  u'',          u'',           u'планово'],    CReportBase.AlignRight),
                            ('2.5%', [u'',                u'',              u'',          u'',           u'сверхплана'], CReportBase.AlignRight),
                            ('2.5%', [u'',                u'Первично',      u'Сотр. ЛПУ', u'',           u'планово'],    CReportBase.AlignRight),
                            ('2.5%', [u'',                u'',              u'',          u'',           u'сверхплана'], CReportBase.AlignRight),
                            ('2.5%', [u'',                u'',              u'Не свои',   u'Инфомат',    u'планово'],    CReportBase.AlignRight),
                            ('2.5%', [u'',                u'',              u'',          u'',           u'сверхплана'], CReportBase.AlignRight),
                            ('2.5%', [u'',                u'',              u'',          u'Call-центр', u'планово'],    CReportBase.AlignRight),
                            ('2.5%', [u'',                u'',              u'',          u'',           u'сверхплана'], CReportBase.AlignRight),
                            ('2.5%', [u'',                u'',              u'',          u'Интернет',   u'планово'],    CReportBase.AlignRight),
                            ('2.5%', [u'',                u'',              u'',          u'',           u'сверхплана'], CReportBase.AlignRight),
                            ('2.5%', [u'На дому',         u'Всего',         u'',          u'',           u'планово'],    CReportBase.AlignRight),
                            ('2.5%', [u'',                u'',              u'',          u'',           u'сверхплана'], CReportBase.AlignRight),
                            ('2.5%', [u'',                u'Выполнено',     u'',          u'',           u'планово'],    CReportBase.AlignRight),
                            ('2.5%', [u'',                u'',              u'',          u'',           u'сверхплана'], CReportBase.AlignRight),
                            ('2.5%', [u'',                u'Актив',         u'',          u'',           u'планово'],    CReportBase.AlignRight),
                            ('2.5%', [u'',                u'',              u'',          u'',           u'сверхплана'], CReportBase.AlignRight),
                            ('2.5%', [u'',                u'Консультация',  u'',          u'',           u'планово'],    CReportBase.AlignRight),
                            ('2.5%', [u'',                u'',              u'',          u'',           u'сверхплана'], CReportBase.AlignRight),
                            ('2.5%', [u'',                u'Первично',      u'Сотр. ЛПУ', u'',           u'планово'],    CReportBase.AlignRight),
                            ('2.5%', [u'',                u'',              u'',          u'',           u'сверхплана'], CReportBase.AlignRight),
                            ('2.5%', [u'',                u'',              u'Не свои',   u'Инфомат',    u'планово'],    CReportBase.AlignRight),
                            ('2.5%', [u'',                u'',              u'',          u'',           u'сверхплана'], CReportBase.AlignRight),
                            ('2.5%', [u'',                u'',              u'',          u'Call-центр', u'планово'],    CReportBase.AlignRight),
                            ('2.5%', [u'',                u'',              u'',          u'',           u'сверхплана'], CReportBase.AlignRight),
                            ('2.5%', [u'',                u'',              u'',          u'Интернет',   u'планово'],    CReportBase.AlignRight),
                            ('2.5%', [u'',                u'',              u'',          u'',           u'сверхплана'], CReportBase.AlignRight),
                            ('4%', [u'Из всех инокраевых',                u'',              u'',          u'',           u''], CReportBase.AlignRight),
                            ('5%', [u'Сверх плана неотложно',                u'',              u'',          u'',           u''], CReportBase.AlignRight)
                           ]

            table = createTable(cursor, tableColumns)
            table.mergeCells(0, 0, 5, 1)
            table.mergeCells(0, 1, 5, 1)
            table.mergeCells(0, 2, 1, 16)
            table.mergeCells(1, 2, 3, 2)
            table.mergeCells(1, 4, 3, 2)
            table.mergeCells(1, 6, 3, 2)
            table.mergeCells(1, 8, 3, 2)
            table.mergeCells(1, 10, 1, 8)
            table.mergeCells(2, 10, 2, 2)
            table.mergeCells(2, 12, 1, 6)
            table.mergeCells(3, 12, 1, 2)
            table.mergeCells(3, 14, 1, 2)
            table.mergeCells(3, 16, 1, 2)
            table.mergeCells(0, 18, 1, 16)
            table.mergeCells(1, 18, 3, 2)
            table.mergeCells(1, 20, 3, 2)
            table.mergeCells(1, 22, 3, 2)
            table.mergeCells(1, 24, 3, 2)
            table.mergeCells(1, 26, 1, 8)
            table.mergeCells(2, 26, 2, 2)
            table.mergeCells(2, 28, 1, 6)
            table.mergeCells(3, 28, 1, 2)
            table.mergeCells(3, 30, 1, 2)
            table.mergeCells(3, 32, 1, 2)
            table.mergeCells(0, 34, 5, 1)
            table.mergeCells(0, 35, 5, 1)

        else:
            tableColumns = [('5%',  [u'№',              u'',              u'',          u''],           CReportBase.AlignLeft),
                            ('10%',[u'Записал',        u'',              u'',          u''],           CReportBase.AlignLeft),
                            ('5%',  [u'Амбулаторно',    u'Всего',         u'',          u''],           CReportBase.AlignRight),
                            ('5%',  [u'',               u'Выполнено',     u'',          u''],           CReportBase.AlignRight),
                            ('5%',  [u'',               u'Актив',         u'',          u''],           CReportBase.AlignRight),
                            ('5%',  [u'',               u'Консультация',  u'',          u''],           CReportBase.AlignRight),
                            ('5%',  [u'',               u'Первично',      u'Сотр. ЛПУ', u''],           CReportBase.AlignRight),
                            ('5%',  [u'',               u'',              u'Не свои',   u'Инфомат'],    CReportBase.AlignRight),
                            ('5%',  [u'',               u'',              u'',          u'Call-центр'], CReportBase.AlignRight),
                            ('5%',  [u'',               u'',              u'',          u'Интернет'],   CReportBase.AlignRight),
                            ('5%',  [u'На дому',        u'Всего',         u'',          u''],           CReportBase.AlignRight),
                            ('5%',  [u'',               u'Выполнено',     u'',          u''],           CReportBase.AlignRight),
                            ('5%',  [u'',               u'Актив',         u'',          u''],           CReportBase.AlignRight),
                            ('5%',  [u'',               u'Консультация',  u'',          u''],           CReportBase.AlignRight),
                            ('5%',  [u'',               u'Первично',      u'Сотр. ЛПУ', u''],           CReportBase.AlignRight),
                            ('5%',  [u'',               u'',              u'Не свои',   u'Инфомат'],    CReportBase.AlignRight),
                            ('5%',  [u'',               u'',              u'',          u'Call-центр'], CReportBase.AlignRight),
                            ('5%',  [u'',               u'',              u'',          u'Интернет'],   CReportBase.AlignRight), 
                            ('5%', [u'Из всех инокраевых',               '',              '',  ''],   CReportBase.AlignRight)
                           ]

            table = createTable(cursor, tableColumns)
            table.mergeCells(0, 0, 4, 1) # номер
            table.mergeCells(0, 1, 4, 1) # записал
            table.mergeCells(0, 2, 1, 8) # амбулаторно
            table.mergeCells(1, 2, 3, 1) # всего
            table.mergeCells(1, 3, 3, 1) # выполнено
            table.mergeCells(1, 4, 3, 1) # актив
            table.mergeCells(1, 5, 3, 1) # Консультация
            table.mergeCells(1, 6, 1, 4) # всего
            table.mergeCells(2, 6, 2, 1) # Инфомат
            table.mergeCells(2, 7, 1, 3) # не свои
            table.mergeCells(0, 10, 1, 8) #
            table.mergeCells(1, 10, 3, 1) #
            table.mergeCells(1, 11, 3, 1) #
            table.mergeCells(1, 12, 3, 1) #
            table.mergeCells(1, 13, 3, 1) #
            table.mergeCells(1, 14, 1, 4) #
            table.mergeCells(2, 14, 2, 1) #
            table.mergeCells(2, 15, 1, 3) #
            table.mergeCells(0, 18, 4, 1) #
        reportRowSize = len(tableColumns) - 2
        if isOvertime:
            reportData = self.analyzeDataOvertime(selectData(params), detailCallCenter, reportRowSize)
        else:
            reportData = self.analyzeData(selectData(params), detailCallCenter, reportRowSize)

        total = [0]*reportRowSize
        n = 1
        cn=0
        personIdList = reportData.keys()
        if groupByOrgStructure:
            keyList = self.getOrgStructureAndPersonSortedList(personIdList, topOrgStructureId)
        else:
            keyList = self.getPersonSortedList(personIdList)

        prevOrgStructureName = None
        prevOrgStructureId = None
        orgStructureTotal = [0]*reportRowSize
        for orgStructureName, name, personId, orgStructureId in keyList:
            if prevOrgStructureId != orgStructureId:
                if prevOrgStructureName is not None:
                    i = table.addRow()
                    table.setText(i, 0, n, CReportBase.TableTotal)
                    n += 1
                    table.setText(i, 1, u'Всего по '+prevOrgStructureName, CReportBase.TableTotal)
                    table.mergeCells(i, 0, 1, 2) #tt1421 соединял не те ячейки
                    for column in xrange(reportRowSize):
                        table.setText(i, column+2, orgStructureTotal[column], CReportBase.TableTotal)
                prevOrgStructureName = orgStructureName
                prevOrgStructureId = orgStructureId
                orgStructureTotal = [0]*reportRowSize

            personData = reportData[personId]
            if not hidePersons:
                recordKeys = personData.keys()
                recordKeys.sort()
                for row, recordKey in enumerate(recordKeys):
                    recordData = personData[recordKey]
                    recordClass, recordPersonName = recordKey
                    if row == 0:
                        cn+=n
                        n=1
                        row = table.addRow() 
                        table.setText(row, 1, name, CReportBase.TableTotal)
                        table.mergeCells(row, 0, 1, 21)
                    i = table.addRow()
                    table.setText(i, 0, n)
                    
                    n += 1
                    table.setText(i, 1, recordPersonName)
                    for column in xrange(reportRowSize):
                        table.setText(i, column+2, recordData[column])

            for recordData in personData.itervalues():
                for column in xrange(reportRowSize):
                    orgStructureTotal[column] += recordData[column]
                    total[column] += recordData[column]

        if prevOrgStructureName is not None:
            i = table.addRow()
            table.setText(i, 0, n, CReportBase.TableTotal)
            n += 1
            table.setText(i, 1, u'Всего по '+prevOrgStructureName, CReportBase.TableTotal)
            table.mergeCells(i, 0, 1, 2)
            for column in xrange(reportRowSize):
                table.setText(i, column+2, orgStructureTotal[column], CReportBase.TableTotal)

        i = table.addRow()
        table.setText(i, 0, u'ИТОГО ' + str(cn), CReportBase.TableTotal)
        table.mergeCells(i, 0, 1, 2)
        for column in xrange(reportRowSize):
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


class CPreRecordDoctorsEx(CPreRecordDoctors):
    def exec_(self):
        CPreRecordDoctors.exec_(self)

    def getSetupDialog(self, parent):
        result = CPreRecordDoctorsDialog(parent)
        result.setTitle(self.title())
        return result

    def build(self, params):
        return CPreRecordDoctors.build(self, '\n'.join(self.getDescription(params)), params)


class CPreRecordDoctorsDialog(CDialogBase, Ui_PreRecordDoctorsDialog):
    def __init__(self, parent=None):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.cmbSpeciality.setTable('rbSpeciality', True)
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        date = QDate.currentDate().addDays(-3)
        self.chkRecordPeriod.setChecked(params.get('useRecordPeriod', True))
        self.edtBegRecordDate.setDate(params.get('begRecordDate', firstMonthDay(date)))
        self.edtEndRecordDate.setDate(params.get('endRecordDate', lastMonthDay(date)))
        self.chkSchedulePeriod.setChecked(params.get('useSchedulePeriod', False))
        self.edtBegScheduleDate.setDate(params.get('begScheduleDate', firstMonthDay(date)))
        self.edtEndScheduleDate.setDate(params.get('endScheduleDate', lastMonthDay(date)))
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))
        self.cmbSpeciality.setValue(params.get('specialityId', None))
        self.cmbPerson.setValue(params.get('personId', None))
        self.chkGroupByOrgStructure.setChecked(bool(params.get('groupByOrgStructure', None)))
        self.chkHidePersons.setChecked(bool(params.get('hidePersons', None)))
        self.chkJoinPersonBySNILS.setChecked(bool(params.get('joinPersonBySNILS', None)))
        self.chkOvertime.setChecked(params.get('isOvertime', False))
        self.chkShowDeleted.setChecked(params.get('showDeleted', False))


    def params(self):
        return dict(useRecordPeriod   = self.chkRecordPeriod.isChecked(),
                    begRecordDate     = self.edtBegRecordDate.date(),
                    endRecordDate     = self.edtEndRecordDate.date(),
                    useSchedulePeriod = self.chkSchedulePeriod.isChecked(),
                    begScheduleDate   = self.edtBegScheduleDate.date(),
                    endScheduleDate   = self.edtEndScheduleDate.date(),
                    orgStructureId    = self.cmbOrgStructure.value(),
                    specialityId      = self.cmbSpeciality.value(),
                    personId          = self.cmbPerson.value(),
                    groupByOrgStructure = self.chkGroupByOrgStructure.isChecked(),
                    hidePersons       = self.chkHidePersons.isChecked(),
                    joinPersonBySNILS =self.chkJoinPersonBySNILS.isChecked(),
                    isOvertime        = self.chkOvertime.isChecked(), 
                    showDeleted        = self.chkShowDeleted.isChecked()
                   )


    @pyqtSignature('QDate')
    def on_edtBegRecordDate_dateChanged(self, date):
        self.cmbPerson.setBegDate(date)


    @pyqtSignature('QDate')
    def on_edtEndRecordDate_dateChanged(self, date):
        self.cmbPerson.setEndDate(date)


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
