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
from PyQt4.QtCore import QDate, pyqtSignature

from library.Utils      import forceInt, forceDate, forceString, formatName, formatSex, getMKB, isMKB
from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable
from Orgs.Utils         import getPersonInfo

from library.DialogBase            import CDialogBase
from Ui_ReportEventListSetupDialog import Ui_CReportEventListSetupDialog


EVENT_STATUS_ALL        = 0
EVENT_STATUS_ONLY_OPEN  = 1
EVENT_STATUS_ONLY_CLOSE = 2


def selectData(params):
    db = QtGui.qApp.db
    tableEvent     = db.table('Event')
    tableEventType = db.table('EventType')
    tableClient    = db.table('Client')
    tableContract  = db.table('Contract')
    tablePerson    = db.table('vrbPersonWithSpecialityAndOrgStr')

    orgStructureList = params['orgStructureList']
    detailByVisits = params['detailByVisits']
    specialityId = params['specialityId']
    eventTypeId  = params['eventTypeId']
    MKBFilter    = params['MKBFilter']
    personId     = params['personId']
    begDate      = params['begDate']
    endDate      = params['endDate']
    eventStatus  = params['eventStatus']

    queryTable = tableEvent
    queryTable = queryTable.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
    queryTable = queryTable.innerJoin(tableContract, tableEvent['contract_id'].eq(tableContract['id']))
    queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
    queryTable = queryTable.innerJoin(tablePerson, tableEvent['execPerson_id'].eq(tablePerson['id']))

    cols = [ tableEvent['setDate'],
             tableEvent['execDate'],
             tableContract['number'].alias('contractNumber'),
             tableEventType['name'].alias('eventTypeName'),
             getMKB(),
             tablePerson['name'].alias('personName'),
             tableEvent['externalId'].alias('documentNumber'),
             tableClient['lastName'].alias('clientLastName'),
             tableClient['firstName'].alias('clientFirstName'),
             tableClient['patrName'].alias('clientPatrName'),
             tableClient['birthDate'].alias('clientBirthDate'),
             tableClient['sex'].alias('clientSex'),
           ]
    cond = [ tableEvent['deleted'].eq(0),
             tableClient['deleted'].eq(0),
             tableEventType['deleted'].eq(0),
             tableContract['deleted'].eq(0),
           ]
    order = [ tableClient['lastName'].name(),
              tableClient['firstName'].name(),
              tableClient['patrName'].name(),
            ]
    group = tableEvent['id'].name()

    if begDate:
        cond.append(tableEvent['setDate'].ge(begDate))
    if endDate:
        cond.append(tableEvent['setDate'].lt(endDate.addDays(1)))
    if MKBFilter:
        cond.append(isMKB(params['MKBFrom'], params['MKBTo']))
    if eventTypeId:
        cond.append(tableEventType['id'].eq(eventTypeId))
    if specialityId:
        cond.append(tablePerson['speciality_id'].eq(specialityId))
    if personId:
        cond.append(tablePerson['id'].eq(personId))
    if orgStructureList:
        cond.append(tablePerson['orgStructure_id'].inlist(orgStructureList))

    if eventStatus != EVENT_STATUS_ALL:
        if eventStatus == EVENT_STATUS_ONLY_OPEN:
            cond.append(tableEvent['execDate'].isNull())
        if eventStatus == EVENT_STATUS_ONLY_CLOSE:
            cond.append(tableEvent['execDate'].isNotNull())

    if detailByVisits:
        cols.append(tableEvent['id'].alias('eventId'))

    stmt = db.selectStmtGroupBy(queryTable, cols, cond, group, order)
    query = db.query(stmt)
    while query.next():
        record = query.record()
        data = {}
        data['MKB'] = forceString(record.value('MKB'))
        data['setDate']  = forceDate(record.value('setDate'))
        data['execDate'] = forceDate(record.value('execDate'))
        data['eventTypeName'] = forceString(record.value('eventTypeName'))
        data['personName']    = forceString(record.value('personName'))
        data['contractNumber']= forceString(record.value('contractNumber'))
        data['documentNumber']= forceString(record.value('documentNumber'))
        data['clientName'] = formatName(lastName =forceString(record.value('clientLastName')),
                                        firstName=forceString(record.value('clientFirstName')),
                                        patrName =forceString(record.value('clientPatrName')))
        data['clientSex'] = formatSex(forceInt(record.value('clientSex')))
        data['clientBirthDate'] = forceDate(record.value('clientBirthDate'))
        if detailByVisits:
            data['eventId'] = forceInt(record.value('eventId'))
        yield data



def selectVisitsData(eventId, params):
    db = QtGui.qApp.db
    tablePerson = db.table('vrbPersonWithSpecialityAndOrgStr')
    tableVisit  = db.table('Visit')

    visitTypeId   = params['visitTypeId']
    visitPersonId = params['visitPersonId']

    queryTable = tableVisit
    queryTable = queryTable.leftJoin(tablePerson, tableVisit['person_id'].eq(tablePerson['id']))

    cols = [ tablePerson['name'].alias('visitPersonName'),
             tableVisit['date'].alias('visitDate'),
           ]
    cond = [ tableVisit['deleted'].eq(0),
             tableVisit['event_id'].eq(eventId),
           ]
    if visitTypeId:
        cond.append(tableVisit['visitType_id'].eq(visitTypeId))
    if visitPersonId:
        cond.append(tableVisit['person_id'].eq(visitPersonId))

    visits = []
    stmt = db.selectStmt(queryTable, cols, cond)
    query = db.query(stmt)
    while query.next():
        record = query.record()
        data = {}
        data['personName'] = forceString(record.value('visitPersonName'))
        data['date'] = forceDate(record.value('visitDate'))
        yield data



class CReportEventList(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Список посещений')


    def getSetupDialog(self, parent):
        result = CReportEventListSetupDialog(parent)
        result.setWindowTitle(self.title())
        return result


    def getDescription(self, params):
        rows = CReport.getDescription(self, params)
        eventStatus = params.get('eventStatus', EVENT_STATUS_ALL)
        visitPersonId = params.get('visitPersonId')

        if eventStatus == EVENT_STATUS_ONLY_OPEN:
            rows.insert(-1, u'только открытые')
        if eventStatus == EVENT_STATUS_ONLY_CLOSE:
            rows.insert(-1, u'только закрытые')
        if visitPersonId:
            personInfo = getPersonInfo(visitPersonId)
            rows.insert(-1, u'врач визита: '+personInfo['shortName']+', '+personInfo['specialityName'])

        return rows


    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        detailByVisits = params['detailByVisits']

        if detailByVisits:
            tableColumns = [
                ( '5%', [u'№'],         CReportBase.AlignRight),
                ('15%', [u'Пациент'],   CReportBase.AlignLeft),
                ( '5%', [u'Назначен'],  CReportBase.AlignLeft),
                ( '5%', [u'Выполнен'],  CReportBase.AlignLeft),
                ('10%', [u'Договор'],   CReportBase.AlignLeft),
                ('10%', [u'Тип'],       CReportBase.AlignLeft),
                ( '5%', [u'МКБ'],       CReportBase.AlignLeft),
                ('15%', [u'Врач'],      CReportBase.AlignLeft),
                ('10%', [u'Номер документа'], CReportBase.AlignLeft),
                ( '5%', [u'Дата визита'],     CReportBase.AlignLeft),
                ('15%', [u'Врач визита'],     CReportBase.AlignLeft),
            ]
        else:
            tableColumns = [
                ( '5%', [u'№'],         CReportBase.AlignRight),
                ('20%', [u'Пациент'],   CReportBase.AlignLeft),
                ('10%', [u'Назначен'],  CReportBase.AlignLeft),
                ('10%', [u'Выполнен'],  CReportBase.AlignLeft),
                ('10%', [u'Договор'],   CReportBase.AlignLeft),
                ('10%', [u'Тип'],       CReportBase.AlignLeft),
                ('5%',  [u'МКБ'],       CReportBase.AlignLeft),
                ('20%', [u'Врач'],      CReportBase.AlignLeft),
                ('10%', [u'Номер документа'], CReportBase.AlignLeft),
            ]
        table = createTable(cursor, tableColumns)

        for i,data in enumerate(selectData(params)):
            visitRow = row = table.addRow()
            birthDate = data['clientBirthDate'].toString('dd.MM.yyyy')
            table.setText(row, 0, i+1)
            table.setText(row, 1, '%s, %s (%s)' % (data['clientName'], birthDate, data['clientSex']))
            table.setText(row, 2, data['setDate'].toString('dd.MM.yyyy'))
            table.setText(row, 3, data['execDate'].toString('dd.MM.yyyy'))
            table.setText(row, 4, data['contractNumber'])
            table.setText(row, 5, data['eventTypeName'])
            table.setText(row, 6, data['MKB'])
            table.setText(row, 7, data['personName'])
            table.setText(row, 8, data['documentNumber'])
            if detailByVisits:
                visitsCount = 0
                for i,visitData in enumerate(selectVisitsData(data['eventId'], params)):
                    if i != 0:
                        table.addRow()
                    table.setText(row+i,  9, visitData['date'].toString('dd.MM.yyyy'))
                    table.setText(row+i, 10, visitData['personName'])
                    visitsCount += 1
                for i in xrange(9):
                    table.mergeCells(row,i, visitsCount,1)
        return doc



class CReportEventListSetupDialog(CDialogBase, Ui_CReportEventListSetupDialog):
    def __init__(self, parent=None):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.cmbSpeciality.setTable('rbSpeciality')
        self.cmbEventType.setTable('EventType')
        self.cmbVisitType.setTable('rbVisitType')
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())


    @pyqtSignature('int')
    def on_cmbMKBFilter_currentIndexChanged(self, index):
        self.edtMKBFrom.setEnabled(bool(index))
        self.edtMKBTo.setEnabled(bool(index))


    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['eventTypeId'] = self.cmbEventType.value()
        result['specialityId'] = self.cmbSpeciality.value()
        result['personId'] = self.cmbPerson.value()
        result['MKBFilter'] = bool(self.cmbMKBFilter.currentIndex())
        result['MKBFrom'] = self.edtMKBFrom.text()
        result['MKBTo'] = self.edtMKBTo.text()
        result['orgStructureId'] = self.cmbOrgStructure.value()
        result['orgStructureList'] = self.cmbOrgStructure.getItemIdList() if result['orgStructureId'] else None
        result['detailByVisits'] = self.chkDetailByVisits.isChecked()
        result['visitTypeId'] = self.cmbVisitType.value() if result['detailByVisits'] else None
        result['visitPersonId'] = self.cmbVisitPerson.value() if result['detailByVisits'] else None
        result['eventStatus'] = self.cmbEventStatus.currentIndex()
        return result


    def setParams(self, params):
        currentDate = QDate.currentDate()
        self.edtBegDate.setDate(params.get('begDate', currentDate))
        self.edtEndDate.setDate(params.get('endDate', currentDate.addDays(1)))
        self.cmbEventType.setValue(params.get('eventTypeId', None))
        self.cmbSpeciality.setValue(params.get('specialityId', None))
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))
        self.cmbPerson.setValue(params.get('personId', None))
        self.edtMKBFrom.setText(params.get('MKBFrom', 'A'))
        self.edtMKBTo.setText(params.get('MKBTo', 'Z99.9'))
        self.cmbMKBFilter.setCurrentIndex(int(params.get('MKBFilter', 0)))
        self.chkDetailByVisits.setChecked(False)
        self.cmbVisitType.setValue(params.get('visitTypeId', None))
        self.cmbVisitPerson.setValue(params.get('visitPersonId', None))
        self.cmbEventStatus.setCurrentIndex(params.get('eventStatus', EVENT_STATUS_ALL))

