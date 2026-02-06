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

from Events.Utils import getActionTypeIdListByFlatCode
from Reports.Report import CReport
from Reports.ReportBase import CReportBase, createTable
from Reports.ReportView import CPageFormat
from Reports.Ui_ReportActivityMO import Ui_ReportActivityMO

from library.Utils import *


def selectDataNMP(params):
    date = params.get('date', None)


    db = QtGui.qApp.db
    tableCallInfo = db.table('smp_callinfo').alias('callInfo')

    cond = [
        tableCallInfo['callDate'].eq(date),
        tableCallInfo['Type'].inlist([0, 2])

    ]

    cols = 'COUNT(DISTINCT idCallNumber) as callCount'

    stmt = db.selectStmt(tableCallInfo, cols, cond)
    return db.query(stmt)


def selectDataSuspended():
    db = QtGui.qApp.db

    tableSuspended = db.table('SuspendedAppointment').alias('suspended')
    tableClient = db.table('Client')
    queryTable = tableSuspended.innerJoin(tableClient, tableClient['id'].eq(tableSuspended['client_id']))

    cond = [
        tableSuspended['deleted'].eq(0),
        tableClient['deleted'].eq(0)

    ]


    cols = [
        'COUNT(*) as totalCount',
        'SUM(suspended.processed = 0) AS pendingCount',
        'SUM(suspended.processed = 1) AS processedCount',
    ]

    stmt = db.selectStmt(queryTable, cols, cond)
    return db.query(stmt)

def selectDataEmergency(params):
    date = params.get('date', None)


    db = QtGui.qApp.db
    tableEvent = db.table('Event').alias('event')
    tableEventType = db.table('EventType')
    tableMedAidType = db.table('rbMedicalAidType').alias('medicalAid')

    cond = [
        tableEvent['execDate'].dateEq(date),
        tableEvent['deleted'].eq(0),
        tableMedAidType['regionalCode'].inlist(('111','112'))

    ]


    queryTable = tableEvent.innerJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
    queryTable = queryTable.innerJoin(tableMedAidType, tableMedAidType['id'].eq(tableEventType['medicalAidType_id']))


    cols = [
        'COUNT(event.id) as totalCount',
        'SUM(medicalAid.regionalCode = "111") as adultCount',
        'SUM(medicalAid.regionalCode = "112") as childCount'
        ]

    stmt = db.selectStmt(queryTable, cols, cond)
    return db.query(stmt)

def selectDataHospital(params):
    date = params.get('date', None)

    db = QtGui.qApp.db
    tableAPHB = db.table('ActionProperty_HospitalBed')
    tableOSHB = db.table('OrgStructure_HospitalBed').alias('orgStructBed')
    tableAP = db.table('ActionProperty')
    tableAction = db.table('Action')
    tableAPT = db.table('ActionPropertyType')
    tableEvent = db.table('Event').alias('event')
    tableClient = db.table('Client').alias('client')


    queryTable = tableAPHB.innerJoin(tableAP, tableAPHB['id'].eq(tableAP['id']))
    queryTable = queryTable.innerJoin(tableOSHB,
                                      tableOSHB['id'].eq(tableAPHB['value']))
    queryTable = queryTable.innerJoin(tableAction, tableAction['id'].eq(tableAP['action_id']))
    queryTable = queryTable.innerJoin(tableAPT, tableAPT['id'].eq(tableAP['type_id']))
    queryTable = queryTable.innerJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
    queryTable = queryTable.innerJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))

    cond = [
        tableAP['action_id'].isNotNull(),
        tableAP['deleted'].eq(0),
        tableAction['deleted'].eq(0),
        tableAPT['deleted'].eq(0),
        tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode('moving%')),
        tableAPT['typeName'].like('HospitalBed'),
        tableAction['begDate'].dateEq(date),
        u"""NOT EXISTS(
	SELECT 1 FROM ActionProperty AS ap_transfer 
	INNER JOIN ActionPropertyType AS apt_transfer ON apt_transfer.`id` = ap_transfer.`type_id` 
	AND apt_transfer.`name` LIKE '%Переведен из отделения%' 
	INNER JOIN ActionProperty_OrgStructure AS apo_transfer ON apo_transfer.`id` = ap_transfer.`id`
	WHERE ap_transfer.`action_id` = Action.`id`
)"""
    ]


    cols = [
        'COUNT(CASE WHEN orgStructBed.schedule_id = 1 AND TIMESTAMPDIFF(YEAR, client.birthDate, CURDATE()) >= 18 THEN 1 END) AS adult24h',
        'COUNT(CASE WHEN orgStructBed.schedule_id = 1 AND TIMESTAMPDIFF(YEAR, client.birthDate, CURDATE()) >= 18 AND event.`order` = 2 THEN 1 END) AS adult24hEmerg',
        'COUNT(CASE WHEN orgStructBed.schedule_id = 1 AND TIMESTAMPDIFF(YEAR, client.birthDate, CURDATE()) >= 18 AND event.`order` = 1 THEN 1 END) AS adult24hPlan',
        'COUNT(CASE WHEN orgStructBed.schedule_id = 2 AND TIMESTAMPDIFF(YEAR, client.birthDate, CURDATE()) >= 18 THEN 1 END) AS adultDay',
        'COUNT(CASE WHEN orgStructBed.schedule_id = 1 AND TIMESTAMPDIFF(YEAR, client.birthDate, CURDATE()) < 18 THEN 1 END) AS child24h',
        'COUNT(CASE WHEN orgStructBed.schedule_id = 1 AND TIMESTAMPDIFF(YEAR, client.birthDate, CURDATE()) < 18 AND event.`order` = 2 THEN 1 END) AS child24hEmerg',
        'COUNT(CASE WHEN orgStructBed.schedule_id = 1 AND TIMESTAMPDIFF(YEAR, client.birthDate, CURDATE()) < 18 AND event.`order` = 1 THEN 1 END) AS child24hPlan',
        'COUNT(CASE WHEN orgStructBed.schedule_id = 2 AND TIMESTAMPDIFF(YEAR, client.birthDate, CURDATE()) < 18 THEN 1 END) AS childDay'
        ]

    stmt = db.selectStmt(queryTable, cols, cond)
    return db.query(stmt)

class CReportActivityMO(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Деятельность МО (оперативный отчет)')
        self.pageFormat = CPageFormat(pageSize=CPageFormat.A4, orientation=CPageFormat.Portrait, leftMargin=1,
                                      topMargin=1, rightMargin=1, bottomMargin=1)

    def getSetupDialog(self, parent):
        result = CReportActivityMODialog(parent)
        result.setTitle(self.title())

        return result

    def getDescription(self, params):

        date = params.get('date', None)


        rows = []
        if date:
            rows.append(u'Отчёт на дату: %s' % forceString(date))
        return rows

    def build(self, params):

        queryNMP = selectDataNMP(params)
        querySuspended = selectDataSuspended()
        queryEmergency = selectDataEmergency(params)
        queryHospital = selectDataHospital(params)

        callCount = None
        totalSuspended = None
        pendingSuspended = None
        processedSuspended = None
        totalEmergency = None
        adultEmergency = None
        childEmergency = None
        adult24h = None
        adult24hEmerg = None
        adult24hPlan = None
        adultDay = None
        child24h = None
        child24hEmerg = None
        child24hPlan = None
        childDay = None

        while queryNMP.next():
            record = queryNMP.record()
            callCount = forceString(record.value('callCount'))

        while querySuspended.next():
            record = querySuspended.record()
            totalSuspended = forceString(record.value('totalCount'))
            pendingSuspended = forceString(record.value('pendingCount'))
            processedSuspended = forceString(record.value('processedCount'))

        while queryEmergency.next():
            record = queryEmergency.record()
            totalEmergency = forceString(record.value('totalCount'))
            adultEmergency = forceString(record.value('adultCount'))
            childEmergency = forceString(record.value('childCount'))

        while queryHospital.next():
            record = queryHospital.record()
            adult24h = forceString(record.value('adult24h'))
            adult24hEmerg = forceString(record.value('adult24hEmerg'))
            adult24hPlan = forceString(record.value('adult24hPlan'))
            adultDay = forceString(record.value('adultDay'))
            child24h = forceString(record.value('child24h'))
            child24hEmerg = forceString(record.value('child24hEmerg'))
            child24hPlan = forceString(record.value('child24hPlan'))
            childDay = forceString(record.value('childDay'))

        totalHospital = str(sum(int(x or 0) for x in [
            adult24h, adultDay,
            child24h, childDay
        ]))


        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportSubTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.setBlockFormat(CReportBase.AlignCenter)
        cursor.insertText(u'Поликлиника')
        cursor.insertBlock()
        cursor.insertBlock()

        tableColumns = [
            ('50%', [u'Вызовы на дом'], CReportBase.AlignLeft),
            ('50%', [u'Количество'], CReportBase.AlignLeft)
        ]

        table = createTable(cursor, tableColumns)
        tableRow = table.addRow()
        table.setText(tableRow, 0, u'Итого')
        table.setText(tableRow, 1,  callCount)

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertBlock()

        tableColumns = [
            ('50%', [u'Журнал отложенной записи'], CReportBase.AlignLeft),
            ('50%', [u'Количество'], CReportBase.AlignLeft)
        ]

        table = createTable(cursor, tableColumns)

        tableRow = table.addRow()
        table.setText(tableRow, 0, u'Всего (на текущий момент)')
        table.setText(tableRow, 1, totalSuspended)
        tableRow = table.addRow()
        table.setText(tableRow, 0, u'из них записанных')
        table.setText(tableRow, 1, processedSuspended)
        tableRow = table.addRow()
        table.setText(tableRow, 0, u'из них в ожидании')
        table.setText(tableRow, 1, pendingSuspended)

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertBlock()
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.setBlockFormat(CReportBase.AlignCenter)
        cursor.insertText(u'Стационар')
        cursor.insertBlock()
        cursor.insertBlock()

        tableColumns = [
            ('50%', [u'Приёмное отделение (амбулаторные)'], CReportBase.AlignLeft),
            ('50%', [u'Количество'], CReportBase.AlignLeft)
        ]

        table = createTable(cursor, tableColumns)

        tableRow = table.addRow()
        table.setText(tableRow, 0, u'Взрослые')
        table.setText(tableRow, 1, adultEmergency)
        tableRow = table.addRow()
        table.setText(tableRow, 0, u'Дети')
        table.setText(tableRow, 1, childEmergency)
        tableRow = table.addRow()
        table.setText(tableRow, 0, u'Всего', fontBold=True)
        table.setText(tableRow, 1, totalEmergency)

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertBlock()
        cursor.insertBlock()

        tableColumns = [
            ('50%', [u'Госпитализация'], CReportBase.AlignLeft),
            ('50%', [u'Количество'], CReportBase.AlignLeft)
        ]

        table = createTable(cursor, tableColumns)

        tableRow = table.addRow()
        table.setText(tableRow, 0, u'Взрослые - круглосуточный стационар')
        table.setText(tableRow, 1, adult24h)
        tableRow = table.addRow()
        table.setText(tableRow, 0, u'из них экстренно')
        table.setText(tableRow, 1, adult24hEmerg)
        tableRow = table.addRow()
        table.setText(tableRow, 0, u'из них планово')
        table.setText(tableRow, 1, adult24hPlan)
        tableRow = table.addRow()
        table.setText(tableRow, 0, u'Взрослые - дневной стационар')
        table.setText(tableRow, 1, adultDay)
        tableRow = table.addRow()
        table.setText(tableRow, 0, u'Дети - круглосуточный стационар')
        table.setText(tableRow, 1, child24h)
        tableRow = table.addRow()
        table.setText(tableRow, 0, u'из них экстренно')
        table.setText(tableRow, 1, child24hEmerg)
        tableRow = table.addRow()
        table.setText(tableRow, 0, u'из них планово')
        table.setText(tableRow, 1, child24hPlan)
        tableRow = table.addRow()
        table.setText(tableRow, 0, u'Дети - дневной стационар')
        table.setText(tableRow, 1, childDay)
        tableRow = table.addRow()
        table.setText(tableRow, 0, u'Всего', fontBold=True)
        table.setText(tableRow, 1, totalHospital)

        return doc

class CReportActivityMODialog(QtGui.QDialog, Ui_ReportActivityMO):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)

        self.setupUi(self)


    def setTitle(self, title):
        self.setWindowTitle(title)

    def setParams(self, params):
        date = QDate.currentDate()
        self.edtDate.setDate(params.get('date', date))



    def params(self):
        result = {}
        result['date'] = self.edtDate.date()
        return result