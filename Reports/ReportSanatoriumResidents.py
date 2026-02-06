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
from PyQt4.QtCore import QDate, QDateTime

from library.Utils             import forceString, forceRef

from Reports.Report            import CReport
from Reports.ReportBase        import CReportBase, createTable
from Reports.ReportView        import CPageFormat

from Reports.ReportSanatoriumArrived import CReportSanatoriumSetupDialog

def selectData(params, relative=False):
    begDate = params.get('begDate', QDate())
    buildBy = params.get('buildBy', 0)

    db = QtGui.qApp.db
    tableAction           = db.table('Action')
    tableActionType       = db.table('ActionType')
    tableEvent            = db.table('Event')
    tableClient           = db.table('Client')
    tableRelative         = db.table('Client').alias('Relative')
    tableEventType        = db.table('EventType')
    tableRbMedicalAidType = db.table('rbMedicalAidType')
    tableOrgStructure     = db.table('OrgStructure')
    tableActionProperty   = db.table('ActionProperty')
    tableActionPropertyOrgStructure = db.table('ActionProperty_OrgStructure')

    if buildBy:
        cols = [ u'''CONCAT_WS(' ', Relative.lastName, Relative.firstName, Relative.patrName) AS clientName''',
                 tableRelative['birthDate'].alias('clientBirthDate'),
                 tableEvent['externalId'],
                 tableOrgStructure['name'].alias('orgStructure'),
                 tableEvent['id'].alias('eventId'),
                 tableRelative['id'].alias('relativeId')
               ]
    else:
        cols = [ u'''CONCAT_WS(' ', Client.lastName, Client.firstName, Client.patrName) AS clientName''',
                 tableClient['birthDate'].alias('clientBirthDate'),
                 tableEvent['externalId'],
                 tableOrgStructure['name'].alias('orgStructure'),
                 tableEvent['id'].alias('eventId')
               ]

    queryTable = tableAction
    queryTable = queryTable.leftJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
    queryTable = queryTable.leftJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
    if buildBy:
        queryTable = queryTable.leftJoin(tableRelative, tableRelative['id'].eq(tableEvent['relative_id']))
    else:
        queryTable = queryTable.leftJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
    queryTable = queryTable.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
    queryTable = queryTable.leftJoin(tableRbMedicalAidType, tableRbMedicalAidType['id'].eq(tableEventType['medicalAidType_id']))
    queryTable = queryTable.leftJoin(tableActionProperty, tableActionProperty['action_id'].eq(tableAction['id']))
    queryTable = queryTable.innerJoin(tableActionPropertyOrgStructure, tableActionPropertyOrgStructure['id'].eq(tableActionProperty['id']))
    queryTable = queryTable.leftJoin(tableOrgStructure, tableOrgStructure['id'].eq(tableActionPropertyOrgStructure['value']))

    cond = [ tableAction['deleted'].eq(0),
             tableActionType['deleted'].eq(0),
             tableActionType['flatCode'].eq('moving'),
             tableAction['begDate'].lt(begDate.addDays(1)),
             db.joinOr([tableAction['endDate'].ge(begDate), tableAction['endDate'].isNull()]),
             tableRbMedicalAidType['code'].eq(8)  #Санаторно-курортная
           ]
    if buildBy:
        cond.append(tableRelative['id'].isNotNull())
        cond.append(tableRelative['deleted'].eq(0))
    else:
        cond.append(tableClient['deleted'].eq(0))
    stmt = db.selectStmt(queryTable, cols, cond, order = u'orgStructure, clientName')
    query = db.query(stmt)
    return query


class CReportSanatoriumResidents(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Список проживающих')


    def getSetupDialog(self, parent):
        result = CReportSanatoriumSetupDialog(parent)
        result.setTitle(self.title())
        result.setObjectName(self.title())
        result.setShowAddressVisible(False)
        result.setPatronageVisible(False)
        result.setShowBirthDateVisible(True)
        result.showEndDateVisible(False)
        result.setBuildByVisible(True)
        result.lblBegDate.setText(u'Дата')
        return result


    def dumpParams(self, cursor, params):
        self.params = params
        begDate = params.get('begDate', QDate())
        description = []
        if begDate:
            description.append(u'на %s'%begDate.toString('dd.MM.yyyy'))
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertBlock(CReportBase.AlignCenter)
        cursor.movePosition(QtGui.QTextCursor.End)
        columns = [ ('100%', [], CReportBase.AlignCenter)]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        buildBy = params.get('buildBy', 0)
        description = []
        description.append(u'Формировать по: %s'%([u'пациентам', u'лицам по уходу'][buildBy]))
        description.append(u'отчёт составлен: '+forceString(QDateTime.currentDateTime()))
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertBlock(CReportBase.AlignLeft)
        cursor.movePosition(QtGui.QTextCursor.End)
        columns = [ ('100%', [], CReportBase.AlignLeft)]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)


    def build(self, params):
        showBirthDate = params.get('showBirthDate', 0)
        buildBy = params.get('buildBy', 0)
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.setBlockFormat(CReportBase.AlignCenter)
        cursor.insertText(self.title())
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        tableColumns = [
                        ('5%',  [u'№ п/п'],                CReportBase.AlignLeft),
                        ('40%', [u'Фамилия Имя Отчество'], CReportBase.AlignLeft),
                        ('15%', [u'№ истории болезни'],    CReportBase.AlignLeft),
                        ('35%' if showBirthDate else '40%', [u'Расположение'], CReportBase.AlignLeft),
                        ]
        if showBirthDate:
            tableColumns.insert(2, ('5%', [u'Дата рождения'],        CReportBase.AlignLeft))
        table = createTable(cursor, tableColumns)
        query = selectData(params)
        cnt = 0
        if query is None:
            return doc
        eventIdList = []
        reportData = {}
        if buildBy:
            while query.next():
                record = query.record()
                eventId = forceRef(record.value('eventId'))
                if eventId and eventId not in eventIdList:
                    eventIdList.append(eventId)
                    relativeId      = forceRef(record.value('relativeId'))
                    externalId      = forceString(record.value('externalId'))
                    clientName      = forceString(record.value('clientName'))
                    clientBirthDate = forceString(record.value('clientBirthDate'))
                    orgStructure    = forceString(record.value('orgStructure'))
                    reportLine = reportData.get((relativeId, clientName), [u'']*(3 if showBirthDate else 2))
                    prevExternalId = reportLine[0]
                    reportLine[0] += ((', ' + externalId) if prevExternalId else externalId) if externalId else u''
                    reportLine[1] = orgStructure
                    if showBirthDate:
                        reportLine[2] = clientBirthDate
                    reportData[(relativeId, clientName)] = reportLine
            reportKeys = reportData.keys()
            reportKeys.sort(key=lambda x: x[1])
            for reportKey in reportKeys:
                reportLine = reportData.get(reportKey, [u'']*(3 if showBirthDate else 2))
                cnt+=1
                i = table.addRow()
                table.setText(i, 0, cnt)
                table.setText(i, 1, reportKey[1])
                if showBirthDate:
                    table.setText(i, 1+showBirthDate, reportLine[2])
                table.setText(i, 2+showBirthDate, reportLine[0])
                table.setText(i, 3+showBirthDate, reportLine[1])
        else:
            while query.next():
                record = query.record()
                eventId = forceRef(record.value('eventId'))
                if eventId and eventId not in eventIdList:
                    eventIdList.append(eventId)
                    externalId        = forceString(record.value('externalId'))
                    clientName        = forceString(record.value('clientName'))
                    clientBirthDate   = forceString(record.value('clientBirthDate'))
                    orgStructure      = forceString(record.value('orgStructure'))
                    cnt+=1
                    i = table.addRow()
                    table.setText(i, 0, cnt)
                    table.setText(i, 1, clientName)
                    if showBirthDate:
                        table.setText(i, 1+showBirthDate, clientBirthDate)
                    table.setText(i, 2+showBirthDate, externalId)
                    table.setText(i, 3+showBirthDate, orgStructure)
        return doc

