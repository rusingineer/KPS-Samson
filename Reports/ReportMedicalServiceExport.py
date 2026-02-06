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
from PyQt4.QtCore import QDate, QDateTime

from library.Utils      import forceDouble, forceInt, forceString
from library.DialogBase import CDialogBase
from Reports.Report     import CReport, getEventTypeName
from Reports.Utils      import dateRangeAsStr
from Reports.ReportBase import CReportBase, createTable

from Ui_ReportMedicalServiceExportSetup import Ui_ReportMedicalServiceExportSetup


def getSocStatusTypeIdList():
    db = QtGui.qApp.db
    tableSocStatusAssoc = db.table('rbSocStatusClassTypeAssoc')
    tableSocStatusType = db.table('rbSocStatusType')
    tableSocStatusClass = db.table('rbSocStatusClass')

    queryTable = tableSocStatusAssoc
    queryTable = queryTable.innerJoin(tableSocStatusClass, tableSocStatusAssoc['class_id'].eq(tableSocStatusClass['id']))
    queryTable = queryTable.innerJoin(tableSocStatusType, tableSocStatusAssoc['type_id'].eq(tableSocStatusType['id']))
    cond = [ tableSocStatusClass['name'].like(u'гражданство'),
             tableSocStatusType['name'].notlike(u'россия'),
           ]
    query = db.query(db.selectDistinctStmt(queryTable, [tableSocStatusType['id']], cond))
    idList = []
    while query.next():
        typeId = forceInt(query.value(0))
        idList.append(typeId)
    return idList


def selectActionsData(params, byProfile):
    db = QtGui.qApp.db
    begDate = params.get('begDate')
    endDate = params.get('endDate')
    eventTypePurposeId = params.get('eventTypePurposeId')
    eventTypeId = params.get('eventTypeId')
    financeId = params.get('financeId')

    tableEvent = db.table('Event')
    tableEventType = db.table('EventType')
    tableClient = db.table('Client')
    tableClientSocStatus = db.table('ClientSocStatus')
    tableSocStatusType = db.table('rbSocStatusType')
    tablePerson = db.table('Person')
    tableSpeciality = db.table('rbSpeciality')
    tableAction = db.table('Action')
    tableActionType = db.table('ActionType')
    tableAccountItem = db.table('Account_Item')

    queryTable = tableEvent
    queryTable = queryTable.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
    queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
    queryTable = queryTable.innerJoin(tableClientSocStatus, tableClientSocStatus['client_id'].eq(tableClient['id']))
    queryTable = queryTable.innerJoin(tableSocStatusType, tableClientSocStatus['socStatusType_id'].eq(tableSocStatusType['id']))
    queryTable = queryTable.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
    queryTable = queryTable.innerJoin(tableActionType, tableAction['actionType_id'].eq(tableActionType['id']))
    queryTable = queryTable.leftJoin (tablePerson, db.joinAnd([ tableAction['person_id'].eq(tablePerson['id']),
                                                                tablePerson['deleted'].eq(0) ]))
    queryTable = queryTable.leftJoin (tableSpeciality, tablePerson['speciality_id'].eq(tableSpeciality['id']))
    queryTable = queryTable.leftJoin (tableAccountItem, db.joinAnd([ tableAccountItem['action_id'].eq(tableAction['id']),
                                                                     tableAccountItem['deleted'].eq(0) ]))

    cond = [ tableEvent['deleted'].eq(0),
             tableEventType['deleted'].eq(0),
             tableClient['deleted'].eq(0),
             tableClientSocStatus['deleted'].eq(0),
             tableAction['deleted'].eq(0),
             tableActionType['deleted'].eq(0),
             tableSocStatusType['id'].inlist(getSocStatusTypeIdList()),
             tableActionType['serviceType'].eq(2),
           ]
    if begDate:
        cond.append(tableEvent['execDate'].ge(begDate))
    if endDate:
        cond.append(tableEvent['execDate'].lt(endDate.addDays(1)))
    if eventTypeId:
        cond.append(tableEventType['id'].eq(eventTypeId))
    if eventTypePurposeId:
        cond.append(tableEventType['purpose_id'].eq(eventTypePurposeId))
    if financeId:
        cond.append(tableAction['finance_id'].eq(financeId))

    cols = [ tableSpeciality['name'] if byProfile else tableSocStatusType['name'],
             'COUNT(DISTINCT %s) AS clientCount' % tableClient['id'],
             'COUNT(DISTINCT %s) AS serviceCount' % tableAction['id'],
             'SUM(%s) AS sumAccount' % tableAccountItem['sum'],
           ]
    stmt = db.selectStmtGroupBy(queryTable, cols, cond, group=cols[0].name(), order=cols[0].name())
    query = db.query(stmt)
    while query.next():
        yield query.record()



def selectVisitsData(params, byProfile):
    db = QtGui.qApp.db
    begDate = params.get('begDate')
    endDate = params.get('endDate')
    eventTypePurposeId = params.get('eventTypePurposeId')
    eventTypeId = params.get('eventTypeId')
    financeId = params.get('financeId')

    tableEvent = db.table('Event')
    tableEventType = db.table('EventType')
    tableVisit = db.table('Visit')
    tableClient = db.table('Client')
    tableClientSocStatus = db.table('ClientSocStatus')
    tableSocStatusType = db.table('rbSocStatusType')
    tablePerson = db.table('Person')
    tableSpeciality = db.table('rbSpeciality')
    tableAccountItem = db.table('Account_Item')

    queryTable = tableEvent
    queryTable = queryTable.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
    queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
    queryTable = queryTable.innerJoin(tableClientSocStatus, tableClientSocStatus['client_id'].eq(tableClient['id']))
    queryTable = queryTable.innerJoin(tableSocStatusType, tableClientSocStatus['socStatusType_id'].eq(tableSocStatusType['id']))
    queryTable = queryTable.innerJoin(tableVisit, tableVisit['event_id'].eq(tableEvent['id']))
    queryTable = queryTable.leftJoin (tablePerson, db.joinAnd([ tableVisit['person_id'].eq(tablePerson['id']),
                                                                tablePerson['deleted'].eq(0) ]))
    queryTable = queryTable.leftJoin (tableSpeciality, tablePerson['speciality_id'].eq(tableSpeciality['id']))
    queryTable = queryTable.leftJoin (tableAccountItem, db.joinAnd([ tableAccountItem['visit_id'].eq(tableVisit['id']),
                                                                     tableAccountItem['deleted'].eq(0) ]))

    cond = [ tableEvent['deleted'].eq(0),
             tableEventType['deleted'].eq(0),
             tableClient['deleted'].eq(0),
             tableClientSocStatus['deleted'].eq(0),
             tableVisit['deleted'].eq(0),
             tableVisit['service_id'].isNotNull(),
             tableSocStatusType['id'].inlist(getSocStatusTypeIdList()),
           ]
    if begDate:
        cond.append(tableEvent['execDate'].ge(begDate))
    if endDate:
        cond.append(tableEvent['execDate'].lt(endDate.addDays(1)))
    if eventTypeId:
        cond.append(tableEventType['id'].eq(eventTypeId))
    if eventTypePurposeId:
        cond.append(tableEventType['purpose_id'].eq(eventTypePurposeId))
    if financeId:
        cond.append(tableVisit['finance_id'].eq(financeId))

    cols = [ tableSpeciality['name'] if byProfile else tableSocStatusType['name'],
             'COUNT(DISTINCT %s) AS clientCount' % tableClient['id'],
             'COUNT(DISTINCT %s) AS serviceCount' % tableVisit['id'],
             'SUM(%s) AS sumAccount' % tableAccountItem['sum'],
           ]
    stmt = db.selectStmtGroupBy(queryTable, cols, cond, group=cols[0].name(), order=cols[0].name())
    query = db.query(stmt)
    while query.next():
        yield query.record()



class CReportMedicalServiceBase(CReport):
    def __init__(self, parent, title):
        CReport.__init__(self, parent)
        self.setTitle(title)


    def getSetupDialog(self, parent):
        result = CReportMedicalServiceExportSetup(parent)
        result.setTitle(self.title())
        return result


    def getDescription(self, params):
        db = QtGui.qApp.db
        rows = []
        byAction = params.get('byAction')
        begDate = params.get('begDate')
        endDate = params.get('endDate')
        eventPurposeId = params.get('eventTypePurposeId')
        eventTypeId = params.get('eventTypeId')
        financeId = params.get('financeId')

        if begDate or endDate:
            rows.append(dateRangeAsStr(u'за период', begDate, endDate))
        if financeId:
            rows.append(u'тип финансирования: '+ forceString(db.translate('rbFinance', 'id', financeId, 'name')))
        if eventPurposeId:
            rows.append(u'цель обращения: ' + forceString(db.translate('rbEventTypePurpose', 'id', eventPurposeId, 'name')))
        if eventTypeId:
            rows.append(u'тип обращения: ' + getEventTypeName(eventTypeId))
        rows.append(u'считать услуги' if byAction else u'Считать визиты')
        rows.append(u'отчёт составлен: ' + forceString(QDateTime.currentDateTime()))
        return rows


    def buildHeaders(self, params, firstColumnName):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        tableColumns = [
            ('25%', [firstColumnName, u'', u'1',], CReportBase.AlignCenter),
            ('25%', [u'Источник финансирования', u'Кол-во чел', u'2',], CReportBase.AlignRight),
            ('25%', [u'', u'Кол-во посещений', u'3'], CReportBase.AlignRight),
            ('25%', [u'', u'Сумма средств', u'4'], CReportBase.AlignRight),
        ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0,0, 2,1)
        table.mergeCells(0,1, 1,3)
        return doc, table



class CReportMedicalServiceExportByProfile(CReportMedicalServiceBase):
    def __init__(self, parent):
        CReportMedicalServiceBase.__init__(self, parent,
            u'Экспорт медицинских услуг (по профилю)')


    def build(self, params):
        doc, table = self.buildHeaders(params, u'Профиль')
        selectData = selectActionsData if params.get('byAction') else selectVisitsData
        for record in selectData(params, byProfile=True):
            row = table.addRow()
            table.setText(row, 0, forceString(record.value('name')))
            table.setText(row, 1, forceInt(record.value('clientCount')))
            table.setText(row, 2, forceInt(record.value('serviceCount')))
            table.setText(row, 3, '%.2f' % forceDouble(record.value('sumAccount')))
        return doc



class CReportMedicalServiceExportByCitizenship(CReportMedicalServiceBase):
    def __init__(self, parent):
        CReportMedicalServiceBase.__init__(self, parent,
            u'Экспорт медицинских услуг (по гражданству)')


    def build(self, params):
        doc, table = self.buildHeaders(params, u'Страна')
        selectData = selectActionsData if params.get('byAction') else selectVisitsData
        for record in selectData(params, byProfile=False):
            row = table.addRow()
            table.setText(row, 0, forceString(record.value('name')))
            table.setText(row, 1, forceInt(record.value('clientCount')))
            table.setText(row, 2, forceInt(record.value('serviceCount')))
            table.setText(row, 3, '%.2f' % forceDouble(record.value('sumAccount')))
        return doc



class CReportMedicalServiceExportSetup(CDialogBase, Ui_ReportMedicalServiceExportSetup):
    def __init__(self, parent=None):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.cmbEventPurpose.setTable('rbEventTypePurpose')
        self.cmbEventType.setTable('EventType')
        self.cmbFinance.setTable('rbFinance')


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        self.cmbEventPurpose.setValue(params.get('eventTypePurposeId'))
        self.cmbEventType.setValue(params.get('eventTypeId'))
        self.cmbFinance.setValue(params.get('financeId'))
        self.cmbConsider.setCurrentIndex(int(params.get('byAction', False)))


    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['eventTypePurposeId'] = self.cmbEventPurpose.value()
        result['eventTypeId'] = self.cmbEventType.value()
        result['financeId'] = self.cmbFinance.value()
        result['byAction'] = bool(self.cmbConsider.currentIndex())
        return result
