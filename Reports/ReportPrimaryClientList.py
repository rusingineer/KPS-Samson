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
from PyQt4.QtCore import QDate, pyqtSignature

from library.Utils       import forceInt, forceString
from Reports.Report      import CReport
from Reports.ReportBase  import CReportBase, createTable
from library.DialogBase  import CDialogBase
from Events.EventTypeListEditorDialog import CEventTypePurposeListEditorDialog

from Ui_ReportPrimaryClientListSetupDialog import Ui_CReportPrimaryClientListSetupDialog


def getDistinctEventIdList(params):
    db = QtGui.qApp.db
    tableEvent = db.table('Event')
    tableClient = db.table('Client')
    tablePerson = db.table('Person')
    tableEventType = db.table('EventType')
    tableSpeciality = db.table('rbSpeciality')
    tableVisit = db.table('Visit')
    tableScene = db.table('rbScene')

    begDate = params.get('begDate')
    endDate = params.get('endDate')
    eventTypePurposeList = params.get('eventTypePurposeList')

    queryTable = tableEvent
    queryTable = queryTable.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
    queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
    queryTable = queryTable.innerJoin(tablePerson, tableEvent['execPerson_id'].eq(tablePerson['id']))
    queryTable = queryTable.innerJoin(tableSpeciality, tablePerson['speciality_id'].eq(tableSpeciality['id']))
    queryTable = queryTable.innerJoin(tableVisit, tableVisit['event_id'].eq(tableEvent['id']))
    queryTable = queryTable.innerJoin(tableScene, tableVisit['scene_id'].eq(tableScene['id']))

    cond = [ tableEvent['deleted'].eq(0),
             tableClient['deleted'].eq(0),
             tablePerson['deleted'].eq(0),
             tableEventType['deleted'].eq(0),
             tableVisit['deleted'].eq(0),
             tableScene['name'].like(u'поликлиника'),
           ]
    if begDate:
        cond.append(tableEvent['execDate'].ge(begDate))
    if endDate:
        cond.append(tableEvent['execDate'].lt(endDate.addDays(1)))
    if eventTypePurposeList:
        cond.append(tableEventType['purpose_id'].inlist(eventTypePurposeList))

    return db.getDistinctIdList(queryTable, tableEvent['id'], cond)


def getFirstClientEventId(idList):
    db = QtGui.qApp.db
    table = db.table('Event').alias('E')
    cond = [ 'E.client_id = Event.client_id', table['id'].inlist(idList) ]
    order = table['setDate'].name()
    return db.selectStmt(table, table['id'], cond, order, limit=1)


def selectData(params):
    db = QtGui.qApp.db
    tableEvent = db.table('Event')
    tablePerson = db.table('Person')
    tableSpeciality = db.table('rbSpeciality')

    eventIdList = getDistinctEventIdList(params)

    queryTable = tableEvent
    queryTable = queryTable.innerJoin(tablePerson, tableEvent['execPerson_id'].eq(tablePerson['id']))
    queryTable = queryTable.innerJoin(tableSpeciality, tablePerson['speciality_id'].eq(tableSpeciality['id']))

    cols = [ tableSpeciality['name'].alias('specialityName'),
             'COUNT(Event.id) AS `totalCount`',
             'SUM(Event.id = (%s)) AS `primaryCount`' % getFirstClientEventId(eventIdList),
           ]
    cond = [ tableEvent['id'].inlist(eventIdList)
           ]

    stmt = db.selectStmtGroupBy(queryTable, cols, cond, tableSpeciality['id'].name())
    query = db.query(stmt)
    while query.next():
        yield query.record()



class CReportPrimaryClientList(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Число лиц, обратившихся первично')


    def getSetupDialog(self, parent):
        result = CReportPrimaryClientListSetupDialog(parent)
        result.setWindowTitle(self.title())
        return result


    def getDescription(self, params):
        rows = CReport.getDescription(self, params)
        if params.get('eventTypePurposeList'):
            db = QtGui.qApp.db
            idList = params['eventTypePurposeList']
            table = db.table('rbEventTypePurpose')
            nameList = [forceString(db.translate(table, 'id', id, 'name')) for id in idList]
            rows.insert(-1, u'Назначение типов событий: ' + ', '.join(name for name in nameList if name))
        return rows


    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        tableColumns = [
            ('10%', [u'№ п/п'],           CReportBase.AlignCenter),
            ('30%', [u'Специальность'],   CReportBase.AlignLeft),
            ('20%', [u'Всего'],           CReportBase.AlignRight),
            ('20%', [u'Из них первично'], CReportBase.AlignRight),
            ('20%', [u'Из них повторно'], CReportBase.AlignRight),
        ]
        table = createTable(cursor, tableColumns)

        for i,rec in enumerate(selectData(params)):
            specialityName = forceString(rec.value('specialityName'))
            count = forceInt(rec.value('totalCount'))
            primaryCount = forceInt(rec.value('primaryCount'))

            row = table.addRow()
            table.setText(row, 0, i+1)
            table.setText(row, 1, specialityName)
            table.setText(row, 2, count)
            table.setText(row, 3, primaryCount)
            table.setText(row, 4, count - primaryCount)

        return doc



class CReportPrimaryClientListSetupDialog(CDialogBase, Ui_CReportPrimaryClientListSetupDialog):
    def __init__(self, parent=None):
        CDialogBase.__init__(self, parent)
        self.eventTypePurposeList = []
        self.setupUi(self)


    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['eventTypePurposeList'] = self.eventTypePurposeList
        return result


    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        self.eventTypePurposeList = params.get('eventTypePurposeList', [])


    @pyqtSignature('')
    def on_btnEventTypePurposeList_clicked(self):
        self.eventTypePurposeList = []
        self.lblEventTypePurposeList.setText(u'Не задано')
        dialog = CEventTypePurposeListEditorDialog(self, filter=None)
        if dialog.exec_():
            idList = dialog.values()
            if idList:
                db = QtGui.qApp.db
                table = db.table('rbEventTypePurpose')
                nameList = [forceString(db.translate(table, 'id', id, 'name')) for id in idList]
                text = ', '.join(name for name in nameList if name)
                self.lblEventTypePurposeList.setText(text)
                self.eventTypePurposeList = idList
