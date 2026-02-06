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

from library.Utils             import forceInt, forceRef, forceString

from Events.Utils              import getActionTypeDescendants
from Reports.Report            import CReport
from Reports.ReportBase        import CReportBase, createTable
from Reports.ReportView        import CPageFormat
from Reports.ReportSetupDialog import CReportSetupDialog
from Reports.StatReport1NPUtil import havePermanentAttach


def selectData(params):
    begDate = params.get('begDate', QDate())
    endDate = params.get('endDate', QDate())
    eventTypeId = params.get('eventTypeId', None)
    sex = params.get('sex', 0)
    ageFrom = params.get('ageFrom', 0)
    ageTo = params.get('ageTo', 150)
    actionTypeClass = params.get('actionTypeClass', None)
    actionTypeId = params.get('actionTypeId', None)
    onlyPermanentAttach = params.get('onlyPermanentAttach', None)
    MKBFilter = params.get('MKBFilter', 0)
    MKBFrom   = params.get('MKBFrom', '')
    MKBTo     = params.get('MKBTo', '')
    orgStructureId = params.get('orgStructureId', None)
    personId  = params.get('personId', None)
    specialityId = params.get('specialityId', None)

    db = QtGui.qApp.db
    tableEvent      = db.table('Event')
    tableClient     = db.table('Client')
    tableActionType = db.table('ActionType')
    tableAction     = db.table('Action')
    tablePerson     = db.table('Person')
    cond = []
    if begDate:
        cond.append(db.joinOr([
            tableAction['directionDate'].ge(begDate), tableAction['directionDate'].isNull()]))
    if endDate:
        cond.append(tableAction['directionDate'].lt(endDate.addDays(1)))
    if eventTypeId:
        cond.append(tableEvent['eventType_id'].eq(eventTypeId))
    if sex:
        cond.append(tableClient['sex'].eq(sex))
    if ageFrom <= ageTo:
        cond.append('Action.directionDate >= ADDDATE(Client.birthDate, INTERVAL %d YEAR)'%ageFrom)
        cond.append('Action.directionDate < SUBDATE(ADDDATE(Client.birthDate, INTERVAL %d YEAR),1)'%(ageTo+1))
    if actionTypeId:
        cond.append(tableActionType['id'].inlist(getActionTypeDescendants(actionTypeId, actionTypeClass)))
    elif actionTypeClass is not None:
        cond.append(tableActionType['class'].eq(actionTypeClass))
    if onlyPermanentAttach:
        cond.append(havePermanentAttach(endDate))
    if orgStructureId:
        orgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', orgStructureId)
        if orgStructureIdList:
            cond.append(tablePerson['orgStructure_id'].inlist(orgStructureIdList))
    if personId:
        cond.append(tableAction['setPerson_id'].eq(personId))
    if specialityId:
        cond.append(tablePerson['speciality_id'].eq(specialityId))
    if MKBFilter:
        tableDiagnostic = db.table('Diagnostic')
        tableDiagnosis = db.table('Diagnosis')
        subQueryTable = tableDiagnosis.leftJoin(tableDiagnostic, tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']))
        subCond = [ tableDiagnostic['event_id'].eq(tableEvent['id']),
                    tableDiagnosis['MKB'].between(MKBFrom, MKBTo)
                  ]
        cond.append(db.existsStmt(subQueryTable, subCond))
    AIJoin = ''
    condStr = db.joinAnd(cond)
    stmt = """
SELECT
    SUM(Action.amount) AS amount,
    COUNT(Client.id) AS cnt,
    ActionType.code,
    ActionType.name,
    ActionType.id AS actionTypeId,
    Client.id AS clientId
FROM
    Action
    LEFT JOIN Event on Action.event_id=Event.id
    LEFT JOIN Client on Client.id=Event.client_id
    LEFT JOIN ActionType on ActionType.id=Action.actionType_id
    LEFT JOIN Person ON Person.id = Action.setPerson_id
    %s
WHERE Action.deleted=0 AND Event.deleted=0 AND %s
GROUP BY ActionType.class, ActionType.group_id, ActionType.id, Client.id
ORDER BY ActionType.code
    """ % (AIJoin, condStr)
    return db.query(stmt)


class CReportDirectionActions(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Сводка о назначениях')
        self.orientation = CPageFormat.Landscape


    def getSetupDialog(self, parent):
        result = CReportSetupDialog(parent)
        result.setPayPeriodVisible(False)
        result.setWorkOrganisationVisible(False)
        result.setSexVisible(True)
        result.setAgeVisible(True)
        result.setOrgStructureVisible(True)
        result.setSpecialityVisible(True)
        result.setActionTypeVisible(True)
        result.setPersonVisible(True)
        result.chkDetailPerson.setVisible(False)
        result.setMKBFilterVisible(True)
        result.setTitle(self.title())
        return result


    def build(self, params):
        query = selectData(params)
        reportData = {}
        totalData = [0]*2
        while query.next():
            record = query.record()
            actionTypeId = forceRef(record.value('actionTypeId'))
            code = forceString(record.value('code'))
            name = forceString(record.value('name'))
            reportLine = reportData.get(code, {})
            if not reportLine:
                reportLine[actionTypeId] = [0]*4
            repData = reportLine.get(actionTypeId, [0]*4)
            amount = forceInt(record.value('amount'))
            repData[0] = code
            repData[1] = name
            repData[2] += amount
            repData[3] += 1
            totalData[0] += amount
            totalData[1] += 1
            reportLine[actionTypeId] = repData
            reportData[code] = reportLine
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        tableColumns = [
            ( '8%', [u'№ п/п'], CReportBase.AlignRight),
            ( '30%', [u'Код назначения'], CReportBase.AlignLeft),
            ( '30%', [u'Наименование назначения'], CReportBase.AlignLeft),
            ( '16%', [u'Количество назначений'], CReportBase.AlignRight),
            ( '16%', [u'Количество пациентов'], CReportBase.AlignRight),
        ]
        table = createTable(cursor, tableColumns)
        repKeys = reportData.keys()
        repKeys.sort()
        for key in repKeys:
            reportLine = reportData.get(key, {})
            for row in reportLine.values():
                i = table.addRow()
                table.setText(i, 0, i)
                for j in xrange(len(row)):
                    table.setText(i, j+1, row[j])
        if reportData:
            i = table.addRow()
            table.setText(i, 1, u'Итого')
            for j in xrange(len(totalData)):
                table.setText(i, j+3, totalData[j])
            table.mergeCells(i, 0, 1, 3)
        return doc
