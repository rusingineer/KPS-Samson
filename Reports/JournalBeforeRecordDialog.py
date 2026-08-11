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
from PyQt4.QtCore import pyqtSignature, QDate, QDateTime, QTime

from library.DialogBase import CDialogBase
from library.Utils      import (firstMonthDay, forceInt, forceRef, forceString, forceDate, formatName,
                                formatDateTime, lastMonthDay, forceDateTime, formatNum, disassembleSeconds)
from Orgs.Utils         import getOrgStructureDescendants, getOrgStructureFullName, getPersonInfo
from Registry.Utils     import CSocStatusTypeCache
from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable
from Reports.Utils      import dateRangeAsStr
from Reports.ReportView import CPageFormat

from Timeline.Schedule  import CSchedule

from Reports.Ui_JournalBeforeRecordDialog  import Ui_JournalBeforeRecordDialog


def formatDisassembledSeconds(seconds):
    days, hours, minutes, seconds = disassembleSeconds(seconds)
    if seconds > 0:
        minutes += 1
        seconds = 0
    fmt = '%02d:%02d' % (hours, minutes)
    if days > 0:
        return fmt + ' ' + formatNum(days, (u'день', u'дня', u'дней'))
    return fmt


def getClientSocStatuses(clientIdList):
    db = QtGui.qApp.db
    table = db.table('ClientSocStatus')
    cond  = [ table['client_id'].inlist(clientIdList),
              table['deleted'].eq(0),
              db.joinOr([table['begDate'].isNull(), table['begDate'].le(QDate.currentDate())]),
              db.joinOr([table['endDate'].isNull(), table['endDate'].ge(QDate.currentDate())]),
            ]
    return db.getRecordList(table, 'DISTINCT socStatusType_id, client_id', where=cond, order='begDate')


def formatSocStatuses(socStatuses, sstIdList, asHtml=False):
    if socStatuses:
        if QtGui.qApp.showingInInfoBlockSocStatus() == 0:
            if asHtml:
                lines = [(('<B>' + CSocStatusTypeCache.getCode(socStatusTypeId) + u'</B>') if socStatusTypeId not in sstIdList
                                                            else CSocStatusTypeCache.getCode(socStatusTypeId)) for socStatusTypeId in socStatuses]
            else:
                lines = [CSocStatusTypeCache.getCode(socStatusTypeId) for socStatusTypeId in socStatuses]
        elif QtGui.qApp.showingInInfoBlockSocStatus() == 1:
            if asHtml:
                lines = [((u'<B>' + CSocStatusTypeCache.getName(socStatusTypeId) + u'</B>') if (socStatusTypeId in sstIdList and CSocStatusTypeCache.getCode(socStatusTypeId) != u'м643')
                                                            else CSocStatusTypeCache.getName(socStatusTypeId)) for socStatusTypeId in socStatuses]
            else:
                lines = [CSocStatusTypeCache.getName(socStatusTypeId) for socStatusTypeId in socStatuses]
        else:
            if asHtml:
                lines = [((('<B>' + CSocStatusTypeCache.getCode(socStatusTypeId) + u'</B>-') if socStatusTypeId not in sstIdList
                                                            else (CSocStatusTypeCache.getCode(socStatusTypeId) + '-'))
                                + ((u'<B>' + CSocStatusTypeCache.getName(socStatusTypeId) + u'</B>') if (socStatusTypeId in sstIdList and CSocStatusTypeCache.getCode(socStatusTypeId) != u'м643')
                                                            else CSocStatusTypeCache.getName(socStatusTypeId))) for socStatusTypeId in socStatuses]
            else:
                lines = [CSocStatusTypeCache.getCode(socStatusTypeId) + '-' + CSocStatusTypeCache.getName(socStatusTypeId) for socStatusTypeId in socStatuses]
        lines.sort()
        return ', '.join(lines)
    else:
        return u'нет'


def selectData(params, AV=False):
    useRecordPeriod   = params.get('useRecordPeriod', False)
    begRecordDate     = params.get('begRecordDate', None)
    begRecordTime     = params.get('begRecordTime', None)
    endRecordDate     = params.get('endRecordDate', None)
    endRecordTime     = params.get('endRecordTime', None)
    useSchedulePeriod = params.get('useSchedulePeriod', False)
    begScheduleDate   = params.get('begScheduleDate', None)
    begScheduleTime   = params.get('begScheduleTime', None)
    endScheduleDate   = params.get('endScheduleDate', None)
    endScheduleTime   = params.get('endScheduleTime', None)
    orgStructureId    = params.get('orgStructureId', None)
    specialityId      = params.get('specialityId', None)
    personId          = params.get('personId', None)
    activityId        = params.get('activityId', None)
    appointmentType   = params.get('appointmentType', None)
    recordPersonId    = params.get('recordPersonId', None)
    recordPersonProfileId  = params.get('recordPersonProfileId', None)
    detailSorted      = params.get('detailSorted', 0)
    userParams        = params.get('userParams', 0)
    appointmentPurposeId = params.get('appointmentPurposeId', None)
    socStatusClassId  = params.get('socStatusClassId', None)
    socStatusTypeId   = params.get('socStatusTypeId', None)
    isComplaint       = params.get('isComplaint', False)
    detailInternet    = params.get('detailInternet', False)
    isReason          = params.get('isReason', False)
    begRecordDateTime = QDateTime(begRecordDate, begRecordTime)
    endRecordDateTime = QDateTime(endRecordDate, endRecordTime)
    begScheduleDateTime = QDateTime(begScheduleDate, begScheduleTime)
    endScheduleDateTime = QDateTime(endScheduleDate, endScheduleTime)

    db = QtGui.qApp.db
    tablePerson = db.table('vrbPersonWithSpeciality').alias('P')
    tableSchedule = db.table('Schedule')
    tableScheduleItem = db.table('Schedule_Item')
    tableRecordPerson = db.table('vrbPersonWithSpeciality').alias('RP')

    cond = [ tableSchedule['deleted'].eq(0),
             tableSchedule['appointmentType'].eq(appointmentType),
             tableScheduleItem['deleted'].eq(0),
             tableScheduleItem['client_id'].isNotNull(),
           ]

    if useRecordPeriod:
        if begRecordDateTime:
            cond.append(tableScheduleItem['recordDatetime'].ge(begRecordDateTime))
        if endRecordDateTime:
            cond.append(tableScheduleItem['recordDatetime'].lt(endRecordDateTime.addDays(1)))
    if useSchedulePeriod:
        if begScheduleDateTime:
            cond.append(tableSchedule['date'].ge(begScheduleDateTime))
        if endScheduleDateTime:
            cond.append(tableSchedule['date'].le(endScheduleDateTime))
    if personId:
        cond.append(tableSchedule['person_id'].eq(personId))
    if specialityId:
        cond.append(tablePerson['speciality_id'].eq(specialityId))
    if orgStructureId:
        cond.append(tablePerson['orgStructure_id'].inlist(getOrgStructureDescendants(orgStructureId)))
    else:
        if not personId:
            cond.append(tablePerson['org_id'].eq(QtGui.qApp.currentOrgId()))
    if recordPersonId:
        cond.append(tableScheduleItem['recordPerson_id'].eq(recordPersonId))
    if recordPersonProfileId:
        cond.append(tableRecordPerson['userProfile_id'].eq(recordPersonProfileId))
    joinAP = u''
    if detailSorted == 3 or appointmentPurposeId:
        joinAP = u'''LEFT JOIN rbAppointmentPurpose ON rbAppointmentPurpose.id = Schedule.appointmentPurpose_id'''
    if appointmentPurposeId:
        cond.append(tableSchedule['appointmentPurpose_id'].eq(appointmentPurposeId))
    if detailSorted  == 1:
        sorted = ' ORDER BY Client.lastName, Client.firstName, Client.patrName'
    elif detailSorted  == 2:
        sorted = ' ORDER BY Client.birthDate'
    elif detailSorted  == 3:
        joinAP = u'''LEFT JOIN rbAppointmentPurpose ON rbAppointmentPurpose.id = Schedule.appointmentPurpose_id'''
        sorted = ' ORDER BY rbAppointmentPurpose.code, rbAppointmentPurpose.name'
    else:
        sorted = ' ORDER BY Schedule_Item.recordDatetime, P.name'
    if userParams == 1:
        cond.append(u'''((Schedule_Item.`recordClass`=2) OR rbPost.code='6000')''')
    elif userParams == 2:
        cond.append(tableScheduleItem['recordClass'].inlist([3,7]))
    if AV:
        isClientPhones = params.get('isClientPhones', False)
        isClientMail = params.get('isClientMail', False)
        if isClientPhones:
            stmtTelefone = u'''(SELECT GROUP_CONCAT( ClientContact.contact SEPARATOR ', ')
            FROM ClientContact
            LEFT JOIN rbContactType ON rbContactType.id = ClientContact.contactType_id
            WHERE ClientContact.client_id = Client.id AND ClientContact.deleted=0
             AND rbContactType.code IN ('1','2','3')
            ORDER BY ClientContact.id) AS clientPhones,'''
        else:
            stmtTelefone = u''
        if isClientMail:
            stmtMail = u'''(SELECT GROUP_CONCAT( ClientContact.contact SEPARATOR ', ')
            FROM ClientContact
            LEFT JOIN rbContactType ON rbContactType.id = ClientContact.contactType_id
            WHERE ClientContact.client_id = Client.id AND ClientContact.deleted=0
             AND rbContactType.code IN ('4')
            ORDER BY ClientContact.id) AS clientMail,'''
        else:
            stmtMail = u''
        if activityId:
            cond.append(tableSchedule['activity_id'].eq(activityId))
    else:
        stmtTelefone = u'''getClientContacts(Client.id) AS clientPhones,'''
        stmtMail = u''
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
    colsComplaint = u' Schedule_Item.complaint, ' if isComplaint or isReason else u''

    stmt =  u'''SELECT
             Schedule_Item.recordDatetime,
             IF(rbPost.code='6000', 2, Schedule_Item.recordClass) AS recordClass,
             Schedule_Item.recordPerson_id AS recordPerson_id, Schedule_Item.system_guid as systemGuid,
              Schedule_Item.appointmentPurpose_id as appointCode,
             IF(Schedule_Item.recordClass = 2, Schedule_Item.note, RP.name) AS recordPersonName,
             Client.lastName, Client.firstName, Client.patrName, Client.birthDate, Client.id AS clientId,
             %s
             %s
             %s
             getClientRegAddress(Client.id) AS clientAddress,
             rbPolicyType.name AS policyType, ClientPolicy.serial, ClientPolicy.number,
             Schedule_Item.time AS scheduleDatetime,
             P.name AS personName
            FROM
             Schedule_Item
             LEFT JOIN Schedule     ON Schedule.id = Schedule_Item.master_id
             LEFT JOIN vrbPersonWithSpeciality AS P  ON P.id = Schedule.person_id
             LEFT JOIN vrbPersonWithSpeciality AS RP ON RP.id = Schedule_Item.recordPerson_id
             LEFT JOIN Client       ON Client.id = Schedule_Item.client_id
             LEFT JOIN ClientPolicy ON ClientPolicy.id = getClientPolicyId(Client.id, 1)
             LEFT JOIN rbPolicyType ON rbPolicyType.id = ClientPolicy.policyType_id
             LEFT JOIN Person AS RPp ON RPp.id = Schedule_Item.recordPerson_id
                LEFT JOIN rbPost       ON rbPost.id = RPp.post_id
             %s
             WHERE %s
            %s''' % (stmtTelefone, stmtMail, colsComplaint, joinAP, db.joinAnd(cond),  sorted)
    return db.query(stmt)


class CJournalBeforeRecord(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Журнал предварительной записи')
        self.doctorsDict = {}
        self.callCentrDict = {}
        self.orientation = CPageFormat.Landscape


    def dumpParams(self, cursor, params):
        db = QtGui.qApp.db
        useRecordPeriod   = params.get('useRecordPeriod', False)
        begRecordDate     = params.get('begRecordDate', None)
        begRecordTime     = params.get('begRecordTime', None)
        endRecordDate     = params.get('endRecordDate', None)
        endRecordTime     = params.get('endRecordTime', None)
        useSchedulePeriod = params.get('useSchedulePeriod', False)
        begScheduleDate   = params.get('begScheduleDate', None)
        begScheduleTime   = params.get('begScheduleTime', None)
        endScheduleDate   = params.get('endScheduleDate', None)
        endScheduleTime   = params.get('endScheduleTime', None)
        orgStructureId    = params.get('orgStructureId', None)
        specialityId      = params.get('specialityId', None)
        activityId         = params.get('activityId', None)
        personId          = params.get('personId', None)
        appointmentType   = params.get('appointmentType', None)
        recordPersonId    = params.get('recordPersonId', None)
        recordPersonProfileId  = params.get('recordPersonProfileId', None)
        detailCallCenter  = params.get('detailCallCenter', False)
        appointmentPurposeId = params.get('appointmentPurposeId', None)
        socStatusClassId  = params.get('socStatusClassId', None)
        socStatusTypeId   = params.get('socStatusTypeId', None)
        isReason     = params.get('isReason', False)

        begRecordDateTime = QDateTime(begRecordDate, begRecordTime)
        endRecordDateTime = QDateTime(endRecordDate, endRecordTime)
        begScheduleDateTime = QDateTime(begScheduleDate, begScheduleTime)
        endScheduleDateTime = QDateTime(endScheduleDate, endScheduleTime)
        description = []
        if useRecordPeriod:
            if begRecordDateTime or endRecordDateTime:
                description.append(dateRangeAsStr(u'за период', begRecordDateTime, endRecordDateTime))
        if useSchedulePeriod:
            if begScheduleDateTime or endScheduleDateTime:
                description.append(dateRangeAsStr(u'период предварительной записи', begScheduleDateTime, endScheduleDateTime))
        if orgStructureId:
            description.append(u'подразделение: ' + getOrgStructureFullName(orgStructureId))
        else:
            description.append(u'подразделение: ЛПУ')
        if specialityId:
            description.append(u'специальность: ' + forceString(db.translate('rbSpeciality', 'id', specialityId, 'name')))
        if activityId:
            description.append(u'вид деятельности: ' + forceString(db.translate('rbActivity', 'id', activityId, 'name')))
        if personId:
            personInfo = getPersonInfo(personId)
            description.append(u'врач: ' + personInfo['shortName']+', '+personInfo['specialityName'])
        if appointmentPurposeId:
            description.append(u'назначение: ' + forceString(db.translate('rbAppointmentPurpose', 'id', appointmentPurposeId, 'name')))
        if appointmentType:
            description.append(u'тип приёма: '+CSchedule.atNames[appointmentType])
        if socStatusTypeId:
            description.append(u'Тип соц.статуса: ' + forceString(db.translate('vrbSocStatusType', 'id', socStatusTypeId, 'name')))
        if socStatusClassId:
            description.append(u'Класс соц.статуса: ' + forceString(db.translate('rbSocStatusClass', 'id', socStatusClassId, 'name')))
        if recordPersonId:
            personInfo = getPersonInfo(recordPersonId)
            description.append(u'пользователь: ' + personInfo['shortName'])
        if recordPersonProfileId:
            description.append(u'профиль прав пользователя: ' + forceString(db.translate('rbUserProfile', 'id', recordPersonProfileId, 'name')))
        if detailCallCenter:
            description.append(u'Детализировать сall-центр')
        if isReason:
            description.append(u'Отображать столбец "Причина"')

        description.append(u'отчёт составлен: '+forceString(QDateTime.currentDateTime()))
        columns = [ ('100%', [], CReportBase.AlignLeft) ]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()


    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()
        detailCallCenter = params.get('detailCallCenter', False)
        tableColumns = [( '2%', [u'№'],             CReportBase.AlignLeft),
                        ( '7%', [u'Дата записи'],   CReportBase.AlignLeft),
                        (' 9%', [u'Пользователь'],  CReportBase.AlignLeft),
                        (' 9%', [u'ФИО'],           CReportBase.AlignLeft),
                        ( '8%', [u'Д/р'],           CReportBase.AlignLeft),
                        ( '8%', [u'Полис'],         CReportBase.AlignLeft),
                        ( '8%', [u'Статус'],        CReportBase.AlignLeft),
                        ('14%', [u'Адрес'],         CReportBase.AlignLeft),
                        ( '7%', [u'Телефон'],       CReportBase.AlignLeft),
                        ( '8%', [u'Дата приема'],   CReportBase.AlignLeft),
                        ('10%', [u'Врач'],          CReportBase.AlignLeft),
                        ('10%', [u'Время ожидания записи в днях'], CReportBase.AlignLeft),
                        ]
        isReason = params.get('isReason', False)
        if isReason:
            tableColumns.append(('8%', [u'Причина'], CReportBase.AlignLeft))
        table = createTable(cursor, tableColumns)
        query = selectData(params)
        db = QtGui.qApp.db
        tableSSC = db.table('rbSocStatusClass')
        tableSSCT = db.table('rbSocStatusClassTypeAssoc')
        queryTable = tableSSC.innerJoin(tableSSCT, tableSSCT['class_id'].eq(tableSSC['id']))
        sstIdList = db.getDistinctIdList(queryTable, [tableSSCT['type_id']], [tableSSC['code'].eq('8')])
        detailInternet = params.get('detailInternet', False)
        n = 1
        appointCodeDB = None
        appointCodeDBRecord = QtGui.qApp.db.getRecordEx('rbAppointmentPurpose', 'id', where="code = 'Service_UO'")
        if appointCodeDBRecord is not None:
            appointCodeDB = forceInt(appointCodeDBRecord.value('id'))
            
        clientIdList = []
        reportLines = []
        while query.next():
            reportLine = [u'']*len(tableColumns)
            record = query.record()
            recordClass = forceInt(record.value('recordClass'))
            recordDateTime = forceDateTime(record.value('recordDatetime'))
            recordPersonName = forceString(record.value('recordPersonName'))
            recordPersonId = forceRef(record.value('recordPerson_id'))
            scheduleDatetime = forceDateTime(record.value('scheduleDatetime'))
            systemGuid       = forceString(record.value('systemGuid'))
            appointCode      = forceInt(record.value('appointCode'))
            reportLine[0] = formatDateTime(recordDateTime)
            if recordClass == 1: # Инфомат
                recordPersonName = u'Инфомат'
            elif recordClass == 2: # call-центр
                if detailCallCenter:
                    recordPersonName = u'Call-центр ' + recordPersonName
                else:
                    recordPersonName = u'Call-центр'
            elif recordClass in (3, 7): # интернет
                recordPersonName = u'Интернет'
                if detailInternet:
                    if systemGuid == u'075AEF71-C1C6-46B7-BE97-931037F03E2A':
                        recordPersonName  += u' (Мессенджер MAX)'
                    elif systemGuid == u'4001E5F6-E96D-4742-8561-C81C838E9064':
                        recordPersonName += u' (Портал госуслуг)'
                    elif systemGuid == u'D127D963-EB51-4624-8778-F0508CE67648':
                        recordPersonName += u' (Кубань-онлайн)'
                    elif appointCodeDB and appointCode == appointCodeDB:
                        recordPersonName += u' (Сервис УО)'
            else:
                if recordPersonId:
                    recordPersonName = recordPersonName
                else:
                    recordPersonName = 'demo'
            reportLine[1] = recordPersonName
            reportLine[2] =    formatName(record.value('lastName'),
                                          record.value('firstName'),
                                          record.value('patrName')
                                         )+ u', ' + forceString(record.value('clientId'))
            reportLine[3] = forceString(record.value('birthDate'))
            reportLine[4] = ' '.join(name for name in (forceString(record.value('policyType')),
                                                          forceString(record.value('serial')),
                                                          forceString(record.value('number'))
                                                         )
                                       )
            clientId = forceRef(record.value('clientId'))
            if clientId and clientId not in clientIdList:
                clientIdList.append(clientId)
            reportLine[5] = clientId
            reportLine[6] = forceString(record.value('clientAddress'))
            reportLine[7] = forceString(record.value('clientPhones'))
            reportLine[8] = formatDateTime(scheduleDatetime)
            reportLine[9] = forceString(record.value('personName'))
            reportLine[10] = formatDisassembledSeconds(max(0, recordDateTime.secsTo(scheduleDatetime)))
            if isReason:
                reportLine[11] = forceString(record.value('complaint'))
            reportLines.append(reportLine)
        clientSocStatuses = {}
        if clientIdList:
            records = getClientSocStatuses(clientIdList)
            for clientSocStatus in records:
                clientIdStatus = forceRef(clientSocStatus.value('client_id'))
                clientSocStatusLine = clientSocStatuses.get(clientIdStatus, [])
                socStatusTypeId = forceRef(clientSocStatus.value('socStatusType_id'))
                if socStatusTypeId and socStatusTypeId not in clientSocStatusLine:
                    clientSocStatusLine.append(socStatusTypeId)
                clientSocStatuses[clientIdStatus] = clientSocStatusLine
        for reportLine in reportLines:
            i = table.addRow()
            table.setText(i, 0, n)
            table.setText(i, 1, reportLine[0])
            table.setText(i, 2, reportLine[1])
            table.setText(i, 3, reportLine[2])
            table.setText(i, 4, reportLine[3])
            table.setText(i, 5, reportLine[4])
            table.setText(i, 6, formatSocStatuses(clientSocStatuses.get(reportLine[5]), sstIdList))
            table.setText(i, 7, reportLine[6])
            table.setText(i, 8, reportLine[7])
            table.setText(i, 9, reportLine[8])   #daysTo
            table.setText(i, 10, reportLine[9])
            table.setText(i, 11, reportLine[10])
            if isReason:
                table.setText(i, 12, reportLine[11])
            n += 1
        return doc


class CJournalBeforeRecordEx(CJournalBeforeRecord):
    def exec_(self):
        CJournalBeforeRecord.exec_(self)


    def getSetupDialog(self, parent):
        result = CJournalBeforeRecordDialog(parent)
        result.setDetailsInternetSource(True)
        result.setReasonVisible(True)
        return result


    def build(self, params):
        return CJournalBeforeRecord.build(self, params)


class CJournalBeforeRecordAV(CJournalBeforeRecord):
    def __init__(self, parent):
        CJournalBeforeRecord.__init__(self, parent)
        self.setTitle(u'Журнал предварительной записи (сокращённый вариант)')


    def exec_(self):
        CJournalBeforeRecord.exec_(self)


    def getSetupDialog(self, parent):
        result = CJournalBeforeRecordDialog(parent)
        result.setPersonInfoVisible(True)
        result.setActivityVisible(True)
        result.setClientIdVisible(True)
        result.setClientPhonesVisible(True)
        result.setClientMailVisible(True)
        result.setDumpParamsVisible(True)
        result.setComplaintVisible(True)
        return result


    def build(self, params):
        isPersonInfo = params.get('isPersonInfo', False)
        isDumpParams = params.get('isDumpParams', True)
        isComplaint  = params.get('isComplaint', False)
        isClientId = params.get('isClientId', False)
        isClientPhones = params.get('isClientPhones', False)
        isClientMail = params.get('isClientMail', False)
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        if isDumpParams:
            self.dumpParams(cursor, params)
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()
        tableColumns = [
                        ('20%', [u'ФИО'],                  CReportBase.AlignLeft),
                        ('10%', [u'Дата рождения'],     CReportBase.AlignLeft),
                        ]
        if isClientId:
            tableColumns.insert(len(tableColumns), ('10%', [u'Код'], CReportBase.AlignLeft))
        if isClientPhones:
            tableColumns.insert(len(tableColumns), ('10%' if isPersonInfo else '15%', [u'Телефон'], CReportBase.AlignLeft))
        if isClientMail:
            tableColumns.insert(len(tableColumns), ('10%' if isPersonInfo else '15%', [u'Электронная почта'], CReportBase.AlignLeft))
        tableColumns.insert(len(tableColumns), ('10%' if isPersonInfo else '15%', [u'Дата приема'], CReportBase.AlignLeft))
        if isPersonInfo:
            tableColumns.insert(len(tableColumns), ('15%', [u'Врач'],    CReportBase.AlignLeft))
        if isComplaint:
            tableColumns.insert(len(tableColumns), ('15%', [u'Жалобы'],    CReportBase.AlignLeft))
        table = createTable(cursor, tableColumns)
        query = selectData(params, AV = True)
        while query.next():
            record = query.record()
            i = table.addRow()
            clientName       = formatName(record.value('lastName'),
                                          record.value('firstName'),
                                          record.value('patrName')
                                         )# + u', ' + forceString(record.value('clientId'))
            clientPhones     = forceString(record.value('clientPhones'))
            clientMail       = forceString(record.value('clientMail'))
            birthDate        = forceDate(record.value('birthDate'))
            scheduleDatetime = forceString(record.value('scheduleDatetime'))
            table.setText(i, 0, clientName)
            table.setText(i, 1, birthDate.toString('dd.MM.yyyy') if birthDate else u'')
            col = 2
            if isClientId:
                table.setText(i, col, forceString(record.value('clientId')))
                col += 1
            if isClientPhones:
                table.setText(i, col, clientPhones)
                col += 1
            if isClientMail:
                table.setText(i, col, clientMail)
                col += 1
            table.setText(i, col, scheduleDatetime)
            col += 1
            if isPersonInfo:
                table.setText(i, col, forceString(record.value('personName')))
                col += 1
            if isComplaint:
                table.setText(i, col, forceString(record.value('complaint')))
        return doc


class CJournalBeforeRecordDialog(CDialogBase, Ui_JournalBeforeRecordDialog):
    def __init__(self, parent=None):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.cmbRecordPersonProfile.setTable('rbUserProfile')
        self.cmbSpeciality.setTable('rbSpeciality', True)
        self.cmbAppointmentPurpose.setTable('rbAppointmentPurpose', True)
        self.cmbActivity.setTable('rbActivity', True)
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())
        self.cmbRecordPerson.setSpecialityPresent(False)
        self.cmbSocStatusType.setTable('vrbSocStatusType', True)
        self.setPersonInfoVisible(False)
        self.setDumpParamsVisible(False)
        self.setComplaintVisible(False)
        self.setActivityVisible(False)
        self.setClientIdVisible(False)
        self.setClientPhonesVisible(False)
        self.setClientMailVisible(False)
        self.setDetailsInternetSource(False)
        self.setReasonVisible(False)


    def setDetailsInternetSource(self, value):
        self.chkDetailInternet.setVisible(value)
        self.chkDetailInternet.setChecked(value)


    def setClientIdVisible(self, value):
        self.clientIdVisible = value
        self.chkClientId.setVisible(value)


    def setClientPhonesVisible(self, value):
        self.clientPhonesVisible = value
        self.chkClientPhones.setVisible(value)


    def setClientMailVisible(self, value):
        self.clientMailVisible = value
        self.chkClientMail.setVisible(value)


    def setActivityVisible(self, value):
        self.activityVisible = value
        self.lblActivity.setVisible(value)
        self.cmbActivity.setVisible(value)


    def setPersonInfoVisible(self, value):
        self.personInfoVisible = value
        self.chkPersonInfo.setVisible(value)


    def setDumpParamsVisible(self, value):
        self.dumpParamsVisible = value
        self.chkDumpParams.setVisible(value)


    def setComplaintVisible(self, value):
        self.complaintVisible = value
        self.chkComplaint.setVisible(value)


    def setReasonVisible(self, value):
        self.reasonVisible = value
        self.chkReason.setVisible(value)


    def setParams(self, params):
        date = QDate.currentDate().addDays(-3)
        self.chkRecordPeriod.setChecked(params.get('useRecordPeriod', True))
        self.edtBegRecordDate.setDate(params.get('begRecordDate', firstMonthDay(date)))
        self.edtBegRecordTime.setTime(params.get('begRecordTime', QTime()))
        self.edtEndRecordDate.setDate(params.get('endRecordDate', lastMonthDay(date)))
        self.edtEndRecordTime.setTime(params.get('endRecordTime', QTime()))
        self.chkSchedulePeriod.setChecked(params.get('useSchedulePeriod', False))
        self.edtBegScheduleDate.setDate(params.get('begScheduleDate', firstMonthDay(date)))
        self.edtBegScheduleTime.setTime(params.get('begScheduleTime', QTime()))
        self.edtEndScheduleDate.setDate(params.get('endScheduleDate', lastMonthDay(date)))
        self.edtEndScheduleTime.setTime(params.get('endScheduleTime', QTime()))
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))
        self.cmbSpeciality.setValue(params.get('specialityId', None))
        self.cmbPerson.setValue(params.get('personId', None))
        if self.activityVisible:
            self.cmbActivity.setValue(params.get('activityId', None))
        self.cmbAppointmentType.setCurrentIndex(0 if params.get('appointmentType', CSchedule.atAmbulance)  == CSchedule.atAmbulance else 1)
        self.cmbRecordPerson.setValue(params.get('recordPersonId', None))
        self.cmbRecordPersonProfile.setValue(params.get('recordPersonProfileId', None))
        self.chkDetailCallCenter.setChecked(params.get('detailCallCenter', False))
        self.chkDetailInternet.setChecked(params.get('detailInternet', False))
        self.cmbSorted.setCurrentIndex(params.get('detailSorted', 0))
        self.cmbUserParams.setCurrentIndex(params.get('userParams', 0))
        self.cmbAppointmentPurpose.setValue(params.get('appointmentPurposeId', None))
        self.cmbSocStatusClass.setValue(params.get('socStatusClassId', None))
        self.cmbSocStatusType.setValue(params.get('socStatusTypeId', None))
        if self.personInfoVisible:
            self.chkPersonInfo.setChecked(params.get('isPersonInfo', False))
        if self.dumpParamsVisible:
            self.chkDumpParams.setChecked(params.get('isDumpParams', True))
        if self.complaintVisible:
            self.chkComplaint.setChecked(params.get('isComplaint', False))
        if self.clientIdVisible:
            self.chkClientId.setChecked(params.get('isClientId', True))
        if self.clientPhonesVisible:
            self.chkClientPhones.setChecked(params.get('isClientPhones', True))
        if self.clientMailVisible:
            self.chkClientMail.setChecked(params.get('isClientMail', True))
        if self.reasonVisible:
            self.chkReason.setChecked(params.get('isReason', False))


    def params(self):
        return dict(useRecordPeriod     = self.chkRecordPeriod.isChecked(),
                    begRecordDate       = self.edtBegRecordDate.date(),
                    begRecordTime       = self.edtBegRecordTime.time(),
                    endRecordDate       = self.edtEndRecordDate.date(),
                    endRecordTime       = self.edtEndRecordTime.time(),
                    useSchedulePeriod   = self.chkSchedulePeriod.isChecked(),
                    begScheduleDate     = self.edtBegScheduleDate.date(),
                    begScheduleTime     = self.edtBegScheduleTime.time(),
                    endScheduleDate     = self.edtEndScheduleDate.date(),
                    endScheduleTime     = self.edtEndScheduleTime.time(),
                    orgStructureId      = self.cmbOrgStructure.value(),
                    specialityId        = self.cmbSpeciality.value(),
                    personId            = self.cmbPerson.value(),
                    activityId          = self.cmbActivity.value() if self.activityVisible else None,
                    appointmentType     = (CSchedule.atAmbulance, CSchedule.atHome)[self.cmbAppointmentType.currentIndex()],
                    recordPersonId      = self.cmbRecordPerson.value(),
                    recordPersonProfile = self.cmbRecordPersonProfile.value(),
                    detailCallCenter    = self.chkDetailCallCenter.isChecked(),
                    detailSorted        = self.cmbSorted.currentIndex(),
                    userParams          = self.cmbUserParams.currentIndex(),
                    appointmentPurposeId = self.cmbAppointmentPurpose.value(),
                    socStatusClassId    = self.cmbSocStatusClass.value(),
                    socStatusTypeId     = self.cmbSocStatusType.value(),
                    isPersonInfo        = self.chkPersonInfo.isChecked() if self.personInfoVisible else False,
                    isDumpParams        = self.chkDumpParams.isChecked() if self.dumpParamsVisible else True,
                    isComplaint         = self.chkComplaint.isChecked() if self.complaintVisible else False,
                    isClientId          = self.chkClientId.isChecked() if self.clientIdVisible else False,
                    isClientPhones      = self.chkClientPhones.isChecked() if self.clientPhonesVisible else False,
                    isClientMail        = self.chkClientMail.isChecked() if self.chkClientMail else False,
                    detailInternet      = self.chkDetailInternet.isChecked(),
                    isReason            = self.chkReason.isChecked() if self.reasonVisible else False,
                   )


    @pyqtSignature('int')
    def on_cmbSocStatusClass_currentIndexChanged(self, index):
        socStatusClassId = self.cmbSocStatusClass.value()
        filter = ('class_id=%d' % socStatusClassId) if socStatusClassId else ''
        self.cmbSocStatusType.setFilter(filter)


    @pyqtSignature('QDate')
    def on_edtBegDate_dateChanged(self, date):
        self.cmbPerson.setBegDate(date)
        self.cmbRecordPerson.setBegDate(date)


    @pyqtSignature('QDate')
    def on_edtEndDate_dateChanged(self, date):
        self.cmbPerson.setEndDate(date)
        self.cmbRecordPerson.setEndDate(date)


    @pyqtSignature('int')
    def on_cmbOrgStructure_currentIndexChanged(self, index):
        orgStructureId = self.cmbOrgStructure.value()
        self.cmbPerson.setOrgStructureId(orgStructureId)


    @pyqtSignature('int')
    def on_cmbSpeciality_currentIndexChanged(self, index):
        specialityId = self.cmbSpeciality.value()
        self.cmbPerson.setSpecialityId(specialityId)

