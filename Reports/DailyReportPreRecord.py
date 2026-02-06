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
import datetime

from PyQt4 import QtGui
from PyQt4.QtCore import QDate

from library.Utils      import forceDate, forceString, forceInt
from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable
from Orgs.Utils         import getOrgStructureDescendants

from Ui_DailyReportPreRecordSetupDialog import Ui_DailyReportPreRecordSetupDialog


def selectData(params):
    begDate              = params.get('begDate', None)
    endDate              = params.get('endDate', None)
    orgStructureId       = params.get('orgStructureId', None)
    db = QtGui.qApp.db
    tableSchedule = db.table('Schedule')
    tableScheduleItem = db.table('Schedule_Item')
    tableJobTicket = db.table('Job_Ticket').alias('JT')
    tableClient   = db.table('Client')
    tablePerson   = db.table('Person')
    cond = [tableSchedule['deleted'].eq(0),
            tableScheduleItem['deleted'].eq(0),
            tableSchedule['appointmentType'].inlist([1, 2]),
            tableClient['deleted'].eq(0),
            tablePerson['deleted'].eq(0)
           ]
    condJT = [tableJobTicket['datetime'].dateEq(tableScheduleItem['time'])]
    if begDate:
        cond.append(tableSchedule['date'].ge(begDate))
        condJT.append(tableJobTicket['datetime'].ge(begDate))
    if endDate:
        cond.append(tableSchedule['date'].le(endDate))
        condJT.append(tableJobTicket['datetime'].lt(endDate.addDays(1)))
    if orgStructureId:
        orgStructureIdList = getOrgStructureDescendants(orgStructureId)
        cond.append(tablePerson['orgStructure_id'].inlist(orgStructureIdList))
        condJT.append(tableJobTicket['orgStructure_id'].inlist(orgStructureIdList))
    stmt='''SELECT COUNT(Client.id) AS clientCount,
                    (SELECT COUNT(APJT.value)
                    FROM Action
                    INNER JOIN Event ON (Event.id = Action.event_id)
                    INNER JOIN ActionPropertyType AS APT ON APT.actionType_id = Action.actionType_id
                    INNER JOIN ActionProperty AS AP ON (AP.type_id = APT.id AND AP.action_id = Action.id)
                    INNER JOIN ActionProperty_Job_Ticket AS APJT ON APJT.id = AP.id
                    INNER JOIN Job_Ticket AS JT ON APJT.value = JT.id
                    WHERE Event.client_id = Client.id
                    AND APT.deleted=0
                    AND Event.deleted = 0
                    AND Action.deleted = 0
                    AND JT.deleted = 0
                    AND AP.deleted = 0
                    AND APT.typeName = 'JobTicket'
                    AND %s) AS jobTicketCount,
                    Schedule.appointmentType,
                    DATE(Schedule_Item.time) AS scheduleDate,
                    age(Client.birthDate, DATE(Schedule_Item.time)) AS clientAge
            FROM Schedule
            INNER JOIN Schedule_Item  ON Schedule.id = Schedule_Item.master_id
            INNER JOIN Client  ON Client.id = Schedule_Item.client_id
            INNER JOIN Person  ON Person.id = Schedule.person_id
            WHERE %s
            GROUP BY scheduleDate, appointmentType, clientAge
            ORDER BY scheduleDate, appointmentType'''
    return db.query(stmt % (db.joinAnd(condJT), db.joinAnd(cond)))


class CDailyReportPreRecordSetupDialog(QtGui.QDialog, Ui_DailyReportPreRecordSetupDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        date = QDate.currentDate()
        self.edtBegDate.setDate(params.get('begDate', date))
        self.edtEndDate.setDate(params.get('endDate', date))
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))


    def params(self):
        params = {}
        params['begDate'] = self.edtBegDate.date()
        params['endDate'] = self.edtEndDate.date()
        params['orgStructureId'] = self.cmbOrgStructure.value()
        return params


class CDailyReportPreRecord(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Ежедневный отчёт')


    def getSetupDialog(self, parent):
        result = CDailyReportPreRecordSetupDialog(parent)
        result.setTitle(self.title())
        return result


    def build(self, params):
        reportData = {}
        query = selectData(params)
        reportData = {}
        while query.next():
            record = query.record()
            scheduleDate    = forceDate(record.value('scheduleDate'))
            scheduleDate = datetime.date(scheduleDate.year(),scheduleDate.month(),scheduleDate.day())
            jobTicketCount  = forceInt(record.value('jobTicketCount'))
            appointmentType = forceInt(record.value('appointmentType'))
            clientAge       = forceInt(record.value('clientAge'))
            clientCount     = forceInt(record.value('clientCount'))
            reportLine = reportData.setdefault(scheduleDate, [0, 0, 0, 0, '', '', '', '', '', '', 0, ''])
            if clientAge < 18:
                if appointmentType == 2:
                    reportLine[0] += clientCount
                elif appointmentType == 1:
                    reportLine[1] += clientCount
            else:
                if appointmentType == 2:
                    reportLine[2] += clientCount
                elif appointmentType == 1:
                    reportLine[3] += clientCount
            reportLine[10] += jobTicketCount
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        cursor.movePosition(QtGui.QTextCursor.End)
        tableColumns = [('2.5%', [u'№',                   u''              ],  CReportBase.AlignLeft),
                        ('7.5%', [u'Дата',                u''              ],  CReportBase.AlignLeft),
                        ('7.5%', [u'Дети',                u'на дому'       ],  CReportBase.AlignLeft),
                        ('7.5%', [u'',                    u'в амбулатории' ],  CReportBase.AlignLeft),
                        ('7.5%', [u'Взрослые',            u'на дому'       ],  CReportBase.AlignLeft),
                        ('7.5%', [u'',                    u'в амбулатории' ],  CReportBase.AlignLeft),
                        ('7.5%', [u'Офтальмолог',         u'на дому'       ],  CReportBase.AlignLeft),
                        ('7.5%', [u'',                    u'в амбулатории' ],  CReportBase.AlignLeft),
                        ('7.5%', [u'Патронаж м/с',        u''              ],  CReportBase.AlignLeft),
                        ('7.5%', [u'Врачебный патронаж',  u''              ],  CReportBase.AlignLeft),
                        ('7.5%', [u'Медицинский кабинет', u'инъекции'      ],  CReportBase.AlignLeft),
                        ('7.5%', [u'',                    u'ЭКГ'           ],  CReportBase.AlignLeft),
                        ('7.5%', [u'',                    u'забор анализов'],  CReportBase.AlignLeft),
                        ('7.5%', [u'',                    u'перевязка'     ],  CReportBase.AlignLeft)
                        ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 2, 1)
        table.mergeCells(0, 2, 1, 2)
        table.mergeCells(0, 4, 1, 2)
        table.mergeCells(0, 6, 1, 2)
        table.mergeCells(0, 8, 2, 1)
        table.mergeCells(0, 9, 2, 1)
        table.mergeCells(0, 10, 1, 4)
        totalLine = [0, 0, 0, 0, '', '', '', '', '', '', 0, '']
        repKey = reportData.keys()
        repKey.sort()
        for row, scheduleDate in enumerate(repKey):
            reportLine = reportData.get(scheduleDate, [0, 0, 0, 0, '', '', '', '', '', '', 0, ''])
            i = table.addRow()
            table.setText(i, 0, row+1)
            table.setText(i, 1, forceString(scheduleDate))
            for col, val in enumerate(reportLine):
                table.setText(i, col+2, val)
                if col in [0, 1, 2, 3, 10]:
                    totalLine[col] += val
        i = table.addRow()
        table.setText(i, 0, u'ИТОГО')
        for col, val in enumerate(totalLine):
            table.setText(i, col+2, val)
        return doc

