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

from library.Utils      import forceInt, forceString, formatName
from Events.Utils       import getActionTypeDescendants
from Orgs.Utils         import getOrgStructureFullName
from Reports.Utils      import getStringPropertyValue, dateRangeAsStr
from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable
from Reports.ReportBIRADSSetupDialog import CReportBIRADSSetupDialog


def selectData(params):
    begDate = params.get('begDate', QDate.currentDate())
    endDate = params.get('endDate', QDate.currentDate())
    actionTypeId   = params.get('actionTypeId', None)
    organisationId = params.get('organisationId', None)
    orgStructureId = params.get('orgStructureId', None)
    personId       = params.get('personId', None)
    isClientDetail = params.get('isClientDetail', False)
    eventTypeId    = params.get('eventTypeId', None)

    db = QtGui.qApp.db
    tableEvent = db.table('Event')
    tableAction = db.table('Action')
    tableActionType = db.table('ActionType')
    tableVRBPerson = db.table('vrbPersonWithSpeciality')
    cond = []
    if eventTypeId:
        cond.append(tableEvent['eventType_id'].eq(eventTypeId))
    if begDate:
        cond.append(tableAction['endDate'].ge(begDate))
    if endDate:
        cond.append(tableAction['endDate'].lt(endDate.addDays(1)))
    if organisationId:
        cond.append(tableVRBPerson['org_id'].eq(organisationId))
    if orgStructureId:
        cond.append(tableVRBPerson['orgStructure_id'].eq(orgStructureId))
    if personId:
        cond.append(tableAction['person_id'].eq(personId))
    if actionTypeId:
        actionClass = forceInt(db.translate("ActionType", "id", actionTypeId, "class"))
        cond.append(tableActionType['id'].inlist(getActionTypeDescendants(actionTypeId, actionClass)))
    cond.append(u'''TRIM(%s) IN ('0-2','3','4-5','6')'''%getStringPropertyValue(u'BIRADS'))

    if isClientDetail:
        stmt = '''
    SELECT
        COUNT(*) AS cnt,
        TRIM(%s) AS propertyValue,
        ActionType.name AS actionTypeName,
        ActionType.id AS actionTypeId,
        vrbPersonWithSpeciality.name AS personName,
        vrbPersonWithSpeciality.id AS personId,
        Client.lastName, Client.firstName, Client.patrName, Client.id AS clientId
    FROM
        Event
        INNER JOIN Action ON Action.event_id = Event.id
        INNER JOIN Client ON Client.id = Event.client_id
        INNER JOIN ActionType on ActionType.id = Action.actionType_id
        LEFT JOIN vrbPersonWithSpeciality on vrbPersonWithSpeciality.id = Action.person_id
    WHERE Action.deleted = 0 AND Event.deleted = 0 AND %s
    GROUP BY actionTypeId, personId, clientId, propertyValue
    ORDER BY actionTypeName, actionTypeId, personName, personId, Client.lastName, Client.firstName, Client.patrName, clientId
        ''' % (getStringPropertyValue(u'BIRADS'), db.joinAnd(cond))
    else:
        joinEvent = u' INNER JOIN Event ON Action.event_id = Event.id' if eventTypeId else u''
        stmt = '''
    SELECT
        COUNT(*) AS cnt,
        TRIM(%s) AS propertyValue,
        ActionType.name AS actionTypeName,
        ActionType.id AS actionTypeId,
        vrbPersonWithSpeciality.name AS personName,
        vrbPersonWithSpeciality.id AS personId
    FROM
        Action
        INNER JOIN ActionType on ActionType.id = Action.actionType_id
        %s
        LEFT JOIN vrbPersonWithSpeciality on vrbPersonWithSpeciality.id = Action.person_id
    WHERE Action.deleted = 0 AND %s
    GROUP BY actionTypeId, personId, propertyValue
    ORDER BY actionTypeName, actionTypeId, personName, personId
        ''' % (getStringPropertyValue(u'BIRADS'), joinEvent, db.joinAnd(cond))

    return db.query(stmt)


class CReportBIRADS(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Сводка BIRADS')


    def getSetupDialog(self, parent):
        result = CReportBIRADSSetupDialog(parent)
        result.setTitle(self.title())
        return result


    def dumpParams(self, cursor, params):
        description = []
        db = QtGui.qApp.db
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        if begDate or endDate:
            description.append(dateRangeAsStr(u'за период', begDate, endDate))
        organisationId = params.get('organisationId', None)
        if organisationId:
            description.append(u'организация: %s'%forceString(db.translate('Organisation', 'id', organisationId, 'shortName')))
        orgStructureId = params.get('orgStructureId', None)
        if orgStructureId:
            description.append(u'подразделение: ' + getOrgStructureFullName(orgStructureId))
        else:
            description.append(u'подразделение: ЛПУ')
        personId = params.get('personId', None)
        if personId:
            description.append(u'врач: %s'%(forceString(db.translate('vrbPersonWithSpeciality', 'id', personId, 'name'))))
        actionTypeId = params.get('actionTypeId', None)
        if actionTypeId:
            actionTypeName=forceString(db.translate('ActionType', 'id', actionTypeId, 'name'))
            description.append(u'мероприятие: '+actionTypeName)
        description.append(u'отчёт составлен: '+forceString(QDateTime.currentDateTime()))
        columns = [ ('100%', [], CReportBase.AlignLeft) ]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()


    def build(self, params):
        isClientDetail = params.get('isClientDetail', False)
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        tableColumns = [
                        ('40%', [u'Действие', u''],    CReportBase.AlignLeft),
                        ('15%', [u'BIRADS',   u'0-2'], CReportBase.AlignRight),
                        ('15%', [u'',         u'3'],   CReportBase.AlignRight),
                        ('15%', [u'',         u'4-5'], CReportBase.AlignRight),
                        ('15%', [u'',         u'6'],   CReportBase.AlignRight)
                       ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 1, 4)
        query = selectData(params)
        reportData = {}
        while query.next():
            record = query.record()
            cnt = forceInt(record.value('cnt'))
            propertyValue = forceString(record.value('propertyValue'))
            actionTypeId = forceInt(record.value('actionTypeId'))
            actionTypeName = forceString(record.value('actionTypeName'))
            personId = forceInt(record.value('personId'))
            personName = forceString(record.value('personName'))
            keyActionTypeData = (actionTypeId, actionTypeName)
            keyPersonData = (personId, personName)
            if isClientDetail:
                clientId = forceInt(record.value('clientId'))
                clientName = formatName(record.value('lastName'), record.value('firstName'), record.value('patrName')) + u', ' + forceString(clientId)
                reportPersonLine = reportData.get(keyActionTypeData, {})
                reportLine = reportPersonLine.get(keyPersonData, ([0]*4, {}))
                clientIdList = reportLine[1]
                clientproPertyList = clientIdList.get((clientName, clientId), [0]*4)
                countList = reportLine[0]
                if propertyValue == u'0-2':
                    countList[0] += cnt
                    clientproPertyList[0] += cnt
                elif propertyValue == u'3':
                    countList[1] += cnt
                    clientproPertyList[1] += cnt
                elif propertyValue == u'4-5':
                    countList[2] += cnt
                    clientproPertyList[2] += cnt
                elif propertyValue == u'6':
                    countList[3] += cnt
                    clientproPertyList[3] += cnt
                clientIdList[(clientName, clientId)] = clientproPertyList
                reportPersonLine[keyPersonData] = (countList, clientIdList)
                reportData[keyActionTypeData] = reportPersonLine
            else:
                reportPersonLine = reportData.get(keyActionTypeData, {})
                reportLine = reportPersonLine.get(keyPersonData, [0]*4)
                if propertyValue == u'0-2':
                    reportLine[0] += cnt
                elif propertyValue == u'3':
                    reportLine[1] += cnt
                elif propertyValue == u'4-5':
                    reportLine[2] += cnt
                elif propertyValue == u'6':
                    reportLine[3] += cnt
                reportPersonLine[keyPersonData] = reportLine
                reportData[keyActionTypeData] = reportPersonLine

        keysActionTypeData = reportData.keys()
        keysActionTypeData.sort(key=lambda x: (x[1]))
        for (actionTypeId, actionTypeName) in keysActionTypeData:
            reportPersonLine = reportData.get((actionTypeId, actionTypeName), {})
            if reportPersonLine:
                i = table.addRow()
                table.setText(i, 0, actionTypeName, CReportBase.ReportSubTitle, CReportBase.AlignLeft)
                keysPersonData = reportPersonLine.keys()
                keysPersonData.sort(key=lambda x: (x[1]))
                for (personId, personName) in keysPersonData:
                    if isClientDetail:
                        reportLine = reportPersonLine.get((personId, personName), ([0]*4, []))
                        countList = reportLine[0]
                        clientIdList = reportLine[1]
                        if countList or clientIdList:
                            i = table.addRow()
                            table.setText(i, 0, personName, CReportBase.TableTotal)
                            for j, val in enumerate(countList):
                                table.setText(i, j+1, val)
                            clientKeys = clientIdList.keys()
                            clientKeys.sort(key=lambda x: x[0])
                            for clientKey in clientKeys:
                                (clientName, clientId) = clientKey
                                clientproPertyList = clientIdList.get(clientKey, [])
                                i = table.addRow()
                                table.setText(i, 0, clientName)
                                for j, val in enumerate(clientproPertyList):
                                    table.setText(i, j+1, val)
                    else:
                        reportLine = reportPersonLine.get((personId, personName), [0]*4)
                        if reportLine:
                            i = table.addRow()
                            table.setText(i, 0, personName, CReportBase.TableTotal)
                            for j, val in enumerate(reportLine):
                                table.setText(i, j+1, val)
        return doc
