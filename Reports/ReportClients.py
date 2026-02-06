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

from library.Utils      import calcAge, forceDate, forceInt, forceString, formatName, formatSNILS
from library.database   import addDateInRange
from Events.Utils       import getActionTypeDescendants
from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable
from Reports.ReportSetupDialog import CReportSetupDialog
from Reports.StatReport1NPUtil import havePermanentAttach


def selectData(begDate, endDate, eventTypeId, sex, ageFrom, ageTo, actionTypeClass, actionTypeId, onlyPermanentAttach, MKBFilter, MKBFrom, MKBTo, onlyPayedEvents, begPayDate, endPayDate, insurerId, personId, currentWorkOrganisation, workOrgId, eventStatus):
    db = QtGui.qApp.db
    tableEvent = db.table('Event')
    tableClient = db.table('Client')
    tableAction = db.table('Action')
    tableActionType = db.table('ActionType')
    cond = []
    if eventStatus == 0:
        cond.append(tableEvent['execDate'].isNotNull())
    elif eventStatus == 1:
        cond.append(tableEvent['execDate'].isNull())
    if begDate:
        cond.append(tableAction['endDate'].ge(begDate))
    if endDate:
        cond.append(tableAction['endDate'].le(endDate))
    if eventTypeId:
        cond.append(tableEvent['eventType_id'].eq(eventTypeId))
    if personId:
        cond.append(tableEvent['execPerson_id'].eq(personId))
    if sex:
        cond.append(tableClient['sex'].eq(sex))
    if ageFrom <= ageTo:
        if eventStatus:
            cond.append('Event.setDate >= ADDDATE(Client.birthDate, INTERVAL %d YEAR)'%ageFrom)
            cond.append('Event.setDate < SUBDATE(ADDDATE(Client.birthDate, INTERVAL %d YEAR),1)'%(ageTo+1))
        else:
            cond.append('Event.execDate >= ADDDATE(Client.birthDate, INTERVAL %d YEAR)'%ageFrom)
            cond.append('Event.execDate < SUBDATE(ADDDATE(Client.birthDate, INTERVAL %d YEAR),1)'%(ageTo+1))
    if eventStatus == 1:
        cond.append(tableEvent['execDate'].isNull())
    if actionTypeId:
        cond.append(tableActionType['id'].inlist(getActionTypeDescendants(actionTypeId, actionTypeClass)))
    elif actionTypeClass is not None:
        cond.append(tableActionType['class'].eq(actionTypeClass))
    if onlyPermanentAttach:
        cond.append(havePermanentAttach(endDate))
    if MKBFilter:
        tableDiagnostic = db.table('Diagnostic')
        tableDiagnosis = db.table('Diagnosis')
        subQueryTable = tableDiagnosis.leftJoin(tableDiagnostic, tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']))
        subCond = [ tableDiagnostic['event_id'].eq(tableEvent['id']),
                    tableDiagnosis['MKB'].between(MKBFrom, MKBTo)
                  ]
        cond.append(db.existsStmt(subQueryTable, subCond))
    if onlyPayedEvents:
        cond.append('isEventPayed(Event.id)')
        tableAccountItem = db.table('Account_Item')
        addDateInRange(cond, tableAccountItem['date'], begPayDate, endPayDate)
    if currentWorkOrganisation:
        cond.append('EXISTS (SELECT * FROM ClientWork WHERE ClientWork.id = (SELECT MAX(id) FROM ClientWork AS CW WHERE CW.client_id = Client.id))')
    if workOrgId:
        if currentWorkOrganisation:
            cond.append('EXISTS (SELECT * FROM ClientWork WHERE ClientWork.id = (SELECT MAX(id) FROM ClientWork AS CW WHERE CW.client_id = Client.id) AND ClientWork.org_id=%d)' % (workOrgId))
        else:
            cond.append('EXISTS (SELECT * FROM ClientWork WHERE ClientWork.org_id=%d)' % (workOrgId))

    if insurerId:
        tableCP = db.table('ClientPolicy').alias('CP')

        condCP = [tableCP['begDate'].lt(tableEvent['execDate'].addDays(1)),
                  db.joinOr([tableCP['endDate'].ge(tableEvent['execDate']), tableCP['endDate'].isNull()]),
                  tableCP['insurer_id'].eq(insurerId),
                  tableCP['client_id'].eq(tableClient['id'])]

        cond.append(db.existsStmt(tableCP, condCP))
    condStr = db.joinAnd(cond)
    stmt = """
SELECT
    Client.lastName, Client.firstName, Client.patrName,
    Client.birthDate, Client.sex,
    formatClientAddress(ClientAddress.id) AS address,
    ClientPolicy.serial AS policySerial, ClientPolicy.number AS policyNumber,
    ClientDocument.serial AS documentSerial, ClientDocument.number AS documentNumber,
    Client.SNILS,
    Event.setDate AS date,
    Action.office, Action.note,
    Action.actionType_id,
    ActionType.name AS actionTypeName
FROM
    Event
    INNER JOIN Action ON Action.event_id=Event.id
    INNER JOIN Client ON Client.id=Event.client_id
    LEFT JOIN ActionType on ActionType.id=Action.actionType_id
    LEFT JOIN ClientAddress ON
        ClientAddress.client_id = Client.id AND
        ClientAddress.id = (SELECT MAX(id) FROM ClientAddress AS CA WHERE CA.Type=0 AND CA.client_id = Client.id)
    LEFT JOIN ClientPolicy  ON
        ClientPolicy.client_id = Client.id AND
        ClientPolicy.id = (SELECT MAX(CP.id) FROM ClientPolicy AS CP WHERE  CP.client_id = Client.id)
    LEFT JOIN ClientDocument ON
        ClientDocument.client_id = Client.id AND
        ClientDocument.id = (
            SELECT MAX(CD.id)
            FROM
                ClientDocument AS CD
                LEFT JOIN rbDocumentType AS rbDT ON rbDT.id = CD.documentType_id
                LEFT JOIN rbDocumentTypeGroup AS rbDTG ON rbDTG.id = rbDT.group_id
            WHERE rbDTG.code = '1' AND CD.client_id = Client.id)
    LEFT  JOIN Account_Item      ON ( Account_Item.id = (SELECT max(AI.id) FROM Account_Item AS AI WHERE AI.event_id = Event.id AND AI.deleted=0 AND AI.date IS NOT NULL AND AI.refuseType_id IS NULL AND AI.reexposeItem_id IS NULL AND AI.visit_id IS NULL AND AI.action_id IS NULL)
                                    )
WHERE (Action.deleted=0 OR Action.deleted IS NULL) AND Event.deleted=0 AND %s
order BY ActionType.class, ActionType.group_id, ActionType.name, ActionType.id, Client.lastName, Client.firstName, Client.patrName
    """ % (condStr)
    return db.query(stmt)


class CReportClients(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Список обслуженных пациентов')


    def getSetupDialog(self, parent):
        result = CReportSetupDialog(parent)
        result.setPayPeriodVisible(True)
        result.setWorkOrganisationVisible(True)
        result.setPersonVisible(True)
        result.chkDetailPerson.setVisible(False)
        result.setSexVisible(True)
        result.setAgeVisible(True)
        result.setActionTypeVisible(True)
        result.setMKBFilterVisible(True)
        result.setCurrentWorkOrganisationVisible(True)
        result.setInsurerVisible(True)
        result.setEventStatusVisible(True)
        result.setTitle(self.title())
        return result


    def build(self, params):
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        eventTypeId = params.get('eventTypeId', None)
        personId = params.get('personId', None)
        sex = params.get('sex', 0)
        ageFrom = params.get('ageFrom', 0)
        ageTo = params.get('ageTo', 150)
        actionTypeClass = params.get('actionTypeClass', None)
        actionTypeId = params.get('actionTypeId', None)
        onlyPermanentAttach = params.get('onlyPermanentAttach', None)
        MKBFilter = params.get('MKBFilter', 0)
        MKBFrom   = params.get('MKBFrom', '')
        MKBTo     = params.get('MKBTo', '')
        workOrgId = params.get('workOrgId', None)
        currentWorkOrganisation = params.get('currentWorkOrganisation', False)
        onlyPayedEvents = params.get('onlyPayedEvents', False)
        begPayDate = params.get('begPayDate', QDate())
        endPayDate = params.get('endPayDate', QDate())
        insurerId = params.get('insurerId', None)
        eventStatus = params.get('eventStatus', 0)

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        tableColumns = [
            ( '5%', [u'№ п/п'], CReportBase.AlignRight),
            ('15%', [u'ФИО'], CReportBase.AlignLeft),
            ( '5%', [u'д/р'], CReportBase.AlignLeft),
            ( '5%', [u'возраст'], CReportBase.AlignLeft),
            ('25%', [u'Адрес'],CReportBase.AlignLeft),
            ( '7%', [ u'Полис'], CReportBase.AlignCenter),
            ( '9%', [ u'паспорт'], CReportBase.AlignCenter),
            ('10%', [ u'СНИЛС' ], CReportBase.AlignLeft ),
            ( '5%', [u'кабинет'],CReportBase.AlignLeft),
            ('15%', [u'примечение'],CReportBase.AlignLeft),
        ]
        table = createTable(cursor, tableColumns)
        query = selectData(begDate, endDate, eventTypeId, sex, ageFrom, ageTo, actionTypeClass, actionTypeId, onlyPermanentAttach, MKBFilter, MKBFrom, MKBTo, onlyPayedEvents, begPayDate, endPayDate, insurerId, personId, currentWorkOrganisation, workOrgId, eventStatus)
        num = 0
        prevActionTypeId = None

        while query.next():
            record = query.record()
            fio = formatName(record.value('lastName'), record.value('firstName'), record.value('patrName'))
            birthDate = forceDate(record.value('birthDate'))
            date = forceDate(record.value('date'))
            age = calcAge(birthDate, date)
            address = forceString(record.value('address'))
            policy = ' '.join([forceString(record.value('policySerial')), forceString(record.value('policyNumber'))])
            document= ' '.join([forceString(record.value('documentSerial')), forceString(record.value('documentNumber'))])
            SNILS = formatSNILS(record.value('SNILS'))
            office = forceString(record.value('office'))
            note = forceString(record.value('note'))
            row = [fio, birthDate.toString('dd.MM.yyyy'), age, address, policy, document, SNILS, office, note]
            actionTypeId = forceInt(record.value('actionType_id'))
            actionTypeName = forceString(record.value('actionTypeName'))
            if actionTypeId!=prevActionTypeId:
                num = 0
                i = table.addRow()
                prevActionTypeId=actionTypeId
                table.mergeCells(i, 0, 1, 10)
                table.setText(i, 0, actionTypeName, CReportBase.ReportSubTitle, CReportBase.AlignLeft)
            i = table.addRow()
            num+=1
            table.setText(i, 0, num)
            for j, val in enumerate(row):
                table.setText(i, j+1, val)
        return doc
