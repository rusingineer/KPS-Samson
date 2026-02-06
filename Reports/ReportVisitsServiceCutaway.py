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

from library.database   import addDateInRange
from library.Utils      import forceDouble, forceInt, forceRef, forceString, formatName

from Orgs.Utils         import getOrgStructureFullName

from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable
from Reports.ReportSetupDialog import CReportSetupDialog
from Reports.StatReport1NPUtil import havePermanentAttach


def selectData(params):
    begDate             = params.get('begDate', QDate())
    endDate             = params.get('endDate', QDate())
    eventTypeId         = params.get('eventTypeId', None)
    sex                 = params.get('sex', 0)
    ageFrom             = params.get('ageFrom', 0)
    ageTo               = params.get('ageTo', 150)
    onlyPermanentAttach = params.get('onlyPermanentAttach', None)
    MKBFilter           = params.get('MKBFilter', 0)
    MKBFrom             = params.get('MKBFrom', '')
    MKBTo               = params.get('MKBTo', '')
    onlyPayedEvents     = params.get('onlyPayedEvents', False)
    begPayDate          = params.get('begPayDate', QDate())
    endPayDate          = params.get('endPayDate', QDate())
    detailPerson        = params.get('detailPerson', False)
    detailAssistant     = params.get('detailAssistant', False)
    personIdList            = params.get('personIdList', None)
    specialityId        = params.get('specialityId', None)
    orgStructureId      = params.get('orgStructureId', None)
    insurerId           = params.get('insurerId', None)
    socStatusTypeId     = params.get('socStatusTypeId', None)
    eventStatus         = params.get('eventStatus', 0)

    db = QtGui.qApp.db

    tableEvent        = db.table('Event')
    tableClient       = db.table('Client')
    tableVisit        = db.table('Visit')
    tablePerson       = db.table('Person')
    tableSpeciality   = db.table('rbSpeciality')
    tableService      = db.table('rbService')
    tableOrgStructure = db.table('OrgStructure')
    tableAccountItem  = db.table('Account_Item')

    table = tableVisit
    table = table.leftJoin(tableEvent,        tableEvent['id'].eq(tableVisit['event_id']))
    table = table.leftJoin(tableClient,       tableClient['id'].eq(tableEvent['client_id']))
    table = table.leftJoin(tableService,      tableService['id'].eq(tableVisit['service_id']))
    table = table.leftJoin(tablePerson,       tablePerson['id'].eq(tableVisit['person_id']))
    table = table.leftJoin(tableSpeciality,   tableSpeciality['id'].eq(tablePerson['speciality_id']))
    table = table.leftJoin(tableOrgStructure, tableOrgStructure['id'].eq(tablePerson['orgStructure_id']))

    fields = [tableVisit['person_id'],
              tableVisit['finance_id'],
              tableVisit['payStatus'].alias('visitPayStatus'),
              tablePerson['lastName'].alias('personLastName'),
              tablePerson['firstName'].alias('personFirstName'),
              tablePerson['patrName'].alias('personPatrName'),
              tableSpeciality['name'].alias('specialityName'),
              tableService['code'].alias('serviceCode'),
              tableOrgStructure['id'].alias('orgStructureId'),
              tableOrgStructure['code'].alias('orgStructureCode'),
              'IF(YEAR(FROM_DAYS(DATEDIFF(Visit.`date`, Client.`birthDate`))) < 18, rbService.`childUetDoctor`, rbService.`adultUetDoctor`) AS uetDoctor',
              'IF(YEAR(FROM_DAYS(DATEDIFF(Visit.`date`, Client.`birthDate`))) < 18, rbService.`childUetAverageMedWorker`, rbService.`adultUetAverageMedWorker`) AS uetAverageMedWorker']
    cond = [tableVisit['deleted'].eq(0),
            tableEvent['deleted'].eq(0),
            'DATE(Event.setDate) <= DATE(Visit.date)',
           ]
    if detailAssistant:
        tableAssistant = db.table('Person').alias('Assistant')
        tableSpecialityA   = db.table('rbSpeciality').alias('rbSpecialityA')
        table = table.leftJoin(tableAssistant, db.joinAnd([tableAssistant['id'].eq(tableVisit['assistant_id']), tableAssistant['deleted'].eq(0)]))
        table = table.leftJoin(tableSpecialityA, tableSpecialityA['id'].eq(tableAssistant['speciality_id']))
        fields.append(tableVisit['assistant_id'].alias('assistantId'))
        fields.append(tableAssistant['lastName'].alias('assistantLastName'))
        fields.append(tableAssistant['firstName'].alias('assistantFirstName'))
        fields.append(tableAssistant['patrName'].alias('assistantPatrName'))
        fields.append(tableSpecialityA['name'].alias('assistantSpecialityName'))
    if begDate:
        cond.append(tableVisit['date'].ge(begDate))
    if endDate:
        cond.append(tableVisit['date'].lt(endDate.addDays(1)))
    if eventTypeId:
        cond.append(tableEvent['eventType_id'].eq(eventTypeId))
    if sex:
        cond.append(tableClient['sex'].eq(sex))
    if socStatusTypeId:
        tableClientSocStatus = db.table('ClientSocStatus')
        if begDate:
            cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['endDate'].isNotNull(),
                                               tableClientSocStatus['endDate'].ge(begDate)
                                              ]),
                                   tableClientSocStatus['endDate'].isNull()
                                  ]))
        if endDate:
            cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['begDate'].isNotNull(),
                                               tableClientSocStatus['begDate'].lt(endDate.addDays(1))
                                              ]),
                                   tableClientSocStatus['begDate'].isNull()
                                  ]))
        table = table.leftJoin(tableClientSocStatus, tableClientSocStatus['client_id'].eq(tableClient['id']))
        cond.append(tableClientSocStatus['socStatusType_id'].eq(socStatusTypeId))
        cond.append(tableClientSocStatus['deleted'].eq(0))
    if eventStatus == 0:
        cond.append(tableEvent['execDate'].isNotNull())
    elif eventStatus == 1:
        cond.append(tableEvent['execDate'].isNull())
    if ageFrom <= ageTo and ageTo:
        if eventStatus == 0:
            cond.append('Event.execDate >= ADDDATE(Client.birthDate, INTERVAL %d YEAR)'%ageFrom)
            cond.append('Event.execDate < SUBDATE(ADDDATE(Client.birthDate, INTERVAL %d YEAR),1)'%(ageTo+1))
        elif eventStatus == 1:
            cond.append('Event.setDate >= ADDDATE(Client.birthDate, INTERVAL %d YEAR)'%ageFrom)
            cond.append('Event.setDate < SUBDATE(ADDDATE(Client.birthDate, INTERVAL %d YEAR),1)'%(ageTo+1))
        else:
            cond.append(db.joinOr([db.joinAnd([tableEvent['execDate'].isNotNull(), 'Event.execDate >= ADDDATE(Client.birthDate, INTERVAL %d YEAR)'%ageFrom]),
                                   db.joinAnd([tableEvent['execDate'].isNull(),    'Event.setDate >= ADDDATE(Client.birthDate, INTERVAL %d YEAR)'%ageFrom])]))
            cond.append(db.joinOr([db.joinAnd([tableEvent['execDate'].isNotNull(), 'Event.execDate < SUBDATE(ADDDATE(Client.birthDate, INTERVAL %d YEAR),1)'%(ageTo+1)]),
                                   db.joinAnd([tableEvent['execDate'].isNull(),    'Event.setDate < SUBDATE(ADDDATE(Client.birthDate, INTERVAL %d YEAR),1)'%(ageTo+1)])                                                                                                                          ]))
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
        accountItemJoinCond = 'Account_Item.id = (SELECT max(AI.id) FROM Account_Item AS AI WHERE AI.event_id = Event.id AND AI.deleted=0 AND AI.date IS NOT NULL AND AI.refuseType_id IS NULL AND AI.reexposeItem_id IS NULL AND AI.visit_id IS NULL AND AI.action_id IS NULL)'
        table = table.leftJoin(tableAccountItem, accountItemJoinCond)
        cond.append('isEventPayed(Event.id)')
        addDateInRange(cond, tableAccountItem['date'], begPayDate, endPayDate)

    if not detailPerson and personIdList:
        cond.append(tableVisit['person_id'].inlist(personIdList))

    if specialityId:
        cond.append(tablePerson['speciality_id'].eq(specialityId))

    if orgStructureId:
        orgStructureIdList = getTheseAndChildrens([orgStructureId])
        cond.append(tablePerson['orgStructure_id'].inlist(orgStructureIdList))

    if insurerId:
        cond.append('EXISTS (SELECT ClientPolicy.`client_id` FROM ClientPolicy WHERE ClientPolicy.`insurer_id`=%d AND ClientPolicy.`client_id`=Client.`id`)' % insurerId)
    order = [tableService['code'].name()]
    stmt = db.selectStmt(table, fields, cond, order)
    return db.query(stmt)


def getTheseAndChildrens(idlist):
    db = QtGui.qApp.db
    table = db.table('OrgStructure')
    result = []
    childrenIdList = db.getIdList(table, 'id', table['parent_id'].inlist(idlist))
    if childrenIdList:
        result = getTheseAndChildrens(childrenIdList)
    result += idlist
    return result


def payStatusCheck(payStatus, condFinanceCode):
    if condFinanceCode:
        payCode = (payStatus >> (2*condFinanceCode)) & 3
        if payCode:
            return True
    return False


class CReportVisitsServiceCutaway(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Отчет по УЕТ')
        self._mapOrgStructureToName = {}

        self.mainOrgStructureItems = None
        self.printedItemCount = 0
        self.headerCount = 0
        self.headerList  = []
        self.orgStructureResult = {}
        self._mapOrgStructureToFullName = {}
        self.result = []
        self.boldChars = None


    def dumpParams(self, cursor, params):
        description = self.getDescription(params)
        description.insert(len(description)-2, u'события %s'%([u'только закрытые', u'только открытые', u'все'][params.get('eventStatus', 0)]))
        columns = [ ('100%', [], CReportBase.AlignLeft) ]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()


    def getSetupDialog(self, parent):
        result = CReportSetupDialog(parent)
        result.setPayPeriodVisible(True)
        result.setWorkOrganisationVisible(True)
        result.setSexVisible(True)
        result.setAgeVisible(True)
        result.setMKBFilterVisible(True)
        result.setInsurerVisible(True)
        result.setOrgStructureVisible(True)
        result.setSpecialityVisible(True)
        result.setPersonVisible(False)
        result.setPersonListVisible(True)
        result.setFinanceVisible(True)
        result.setSocStatusTypeVisible(True)
        result.setEventStatusVisible(True)
        result.setDetailAssistantVisible(True)
        result.setTitle(self.title())
        self.mainOrgStructureItems = result.cmbOrgStructure.model().getRootItem().items()
#        print result.cmbOrgStructure.model().getRootItem()
        return result


    def build(self, params):
        detailPerson        = params.get('detailPerson', False)
        detailAssistant     = params.get('detailAssistant', False)
        orgStructureId      = params.get('orgStructureId', None)
        condFinanceId       = params.get('financeId', None)
        condFinanceCode     = params.get('financeCode', '0')

        query = selectData(params)

        reportData = {}
        self._mapOrgStructureToName.clear()
        self._mapOrgStructureToFullName.clear()

        while query.next():
            record = query.record()
            orgStructureId         = forceRef(record.value('orgStructureId'))
            orgStructureCode       = forceString(record.value('orgStructureCode'))
            financeId              = forceRef(record.value('finance_id'))
            visitPayStatus         = forceInt(record.value('visitPayStatus'))
            serviceCode            = forceString(record.value('serviceCode'))
            uetDoctor              = forceDouble(record.value('uetDoctor'))
            uetAverageMedWorker    = forceDouble(record.value('uetAverageMedWorker'))
            personName             = formatName(record.value('personLastName'),
                                                record.value('personFirstName'),
                                                record.value('personPatrName'))
            specialityName         = forceString(record.value('specialityName'))

            if condFinanceId:
                if financeId:
                    if condFinanceId != financeId:
                        continue
                else:
                    if not payStatusCheck(visitPayStatus, forceInt(condFinanceCode)):
                        continue
            if specialityName:
                personName = personName + ' | ' + specialityName
            if detailAssistant:
                assistantId = forceRef(record.value('assistantId'))
                assistantName = formatName(record.value('assistantLastName'),
                                            record.value('assistantFirstName'),
                                            record.value('assistantPatrName'))
                assistantSpecialityName = forceString(record.value('assistantSpecialityName'))
                if assistantSpecialityName:
                    assistantName = assistantName + ' | ' + assistantSpecialityName
                if not assistantName:
                    assistantName = forceString(assistantId) if assistantId else u'Ассистент не задан'

            self._mapOrgStructureToName.setdefault(orgStructureId, orgStructureCode)
            existsData = reportData.setdefault(orgStructureId, {})
            if detailPerson:
                if detailAssistant:
                    personData = existsData.setdefault(personName, {})
                    assistantData = personData.setdefault(assistantName, {})
                    existsValue = assistantData.setdefault(serviceCode, [0, 0.0, 0.0])
                    existsValue[0] += 1
                    existsValue[1] += uetDoctor
                    existsValue[2] += uetAverageMedWorker
                else:
                    personData = existsData.setdefault(personName, {})
                    existsValue = personData.setdefault(serviceCode, [0, 0.0, 0.0])
                    existsValue[0] += 1
                    existsValue[1] += uetDoctor
                    existsValue[2] += uetAverageMedWorker
            else:
                if detailAssistant:
                    assistantData = existsData.setdefault(assistantName, {})
                    existsValue = assistantData.setdefault(serviceCode, [0, 0.0, 0.0])
                    existsValue[0] += 1
                    existsValue[1] += uetDoctor
                    existsValue[2] += uetAverageMedWorker
                else:
                    existsValue = existsData.setdefault(serviceCode, [0, 0.0, 0.0])
                    existsValue[0] += 1
                    existsValue[1] += uetDoctor
                    existsValue[2] += uetAverageMedWorker

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        tableColumns = [
            ( '10%', [u'№ п/п'], CReportBase.AlignRight),
            ( '30%', [u'Код профиля'], CReportBase.AlignLeft),
            ( '15%', [u'Количество визитов'], CReportBase.AlignRight),
            ( '15%', [u'УЕТ врача'], CReportBase.AlignRight),
            ( '15%', [u'УЕТ ср.мед.персонала'], CReportBase.AlignRight)
        ]

        table = createTable(cursor, tableColumns)

        self.boldChars = QtGui.QTextCharFormat()
        self.boldChars.setFontWeight(QtGui.QFont.Bold)

        self.printedItemCount = 0
        self.orgStructureResult = {}
        self.result = [0, 0, 0]
        self.headerCount = 0
        self.headerList  = []

        result = self.printOrgStructureListValues(detailPerson, detailAssistant, self.mainOrgStructureItems, reportData, table)

        if None in reportData:
            orgStructureId = None
            orgStructureName = self.getOrgStructureFullName(orgStructureId)
            i = table.addRow()
            table.setText(i, 1, orgStructureName, charFormat=self.boldChars)
            self.headerList.append(i)
            self.headerCount += 1
            orgStructureResult = self.printOrgStructureValues(detailPerson, detailAssistant,
                                                              orgStructureId,
                                                              reportData,
                                                              table)
            result = map(lambda x, y: x+y, result, orgStructureResult)
            self.setResult(i, orgStructureResult, table)

        i = table.addRow()
        table.setText(i, 0, u'Итого', charFormat=self.boldChars)
        self.headerList.append(i)
        self.setResult(i, result, table)

        for headerRow in self.headerList:
            table.mergeCells(headerRow, 0, 1, 2)
        return doc


    def getOrgStructureFullName(self, orgStructureId):
        orgStructureFullName = self._mapOrgStructureToFullName.get(orgStructureId, None)
        if not orgStructureFullName:
            if orgStructureId is None:
                orgStructureFullName = u'Не задано'
            else:
                orgStructureFullName = getOrgStructureFullName(orgStructureId)
                self._mapOrgStructureToFullName[orgStructureId] = orgStructureFullName
        return orgStructureFullName


    def checkNeedPrint(self, checkOrgStructureIdList, existsOrgStructureIdList):
        return bool( set(checkOrgStructureIdList) & set(existsOrgStructureIdList) )


    def getAllReportOrgStructureIdList(self, reportOrgStructureIdKeyList, orgStructureItemList, result):
        added = False
        if orgStructureItemList:
            for orgStructureItem in orgStructureItemList:
                orgStructureId = orgStructureItem.id()
                if orgStructureId in reportOrgStructureIdKeyList:
                    result.append(orgStructureId)
                    added = True
                if self.getAllReportOrgStructureIdList(reportOrgStructureIdKeyList, orgStructureItem.items(), result):
                    if orgStructureId not in result:
                        result.append(orgStructureId)
                        added = True
        return added


    def printOrgStructureListValues(self, detailPerson, detailAssistant, orgStructureItemList,
                                    reportData, table, orgStructureNameShift=0):
        result = [0, 0, 0]
        localResult = [0, 0, 0]

        reportOrgStructureIdKeyList = reportData.keys()
        allReportOrgStructureIdList = []
        self.getAllReportOrgStructureIdList(reportOrgStructureIdKeyList, self.mainOrgStructureItems, allReportOrgStructureIdList)

        if bool(orgStructureItemList):
            for orgStructureItem in orgStructureItemList:
#                if self.checkNeedPrint( orgStructureItem.getItemIdList(), reportData.keys() ):
                orgStructureId = orgStructureItem.id()
                if orgStructureId in allReportOrgStructureIdList:
                    orgStructureName = self.getOrgStructureFullName(orgStructureId)
                    i = table.addRow()
                    table.setText(i, 1, (' '*orgStructureNameShift)+orgStructureName, charFormat=self.boldChars)
                    self.headerList.append(i)
                    self.headerCount += 1
                    orgStructureResult = self.printOrgStructureValues(detailPerson, detailAssistant,
                                                                      orgStructureId,
                                                                      reportData,
                                                                      table)

                    childrenResult = self.printOrgStructureListValues(detailPerson, detailAssistant,
                                                     orgStructureItem.items(),
                                                     reportData,
                                                     table,
                                                     orgStructureNameShift+8)

                    localResult = map(lambda x, y: x+y, childrenResult, orgStructureResult)
                    result = map(lambda x, y: x+y, result, localResult)

                    self.setResult(i, localResult, table)

        return result

    def printOrgStructureValues(self, detailPerson, detailAssistant, orgStructureId, reportData, table):
        orgStructureResult = [0, 0, 0]
        if detailPerson:
            if detailAssistant:
                persons = reportData.get(orgStructureId, {})
                personsKeys = persons.keys()
                personsKeys.sort()
                for personKey in personsKeys:
                    personResult = [0, 0, 0]
                    i = table.addRow()
                    table.setText(i, 0, personKey, charFormat=self.boldChars)
                    currentPersonRow = i
                    self.headerList.append(i)
                    self.headerCount += 1

                    assistants = persons.get(personKey, {})
                    assistantKeys = assistants.keys()
                    assistantKeys.sort()
                    for assistantKey in assistantKeys:
                        assistantResult = [0, 0, 0]
                        i = table.addRow()
                        table.setText(i, 0, assistantKey, charFormat=self.boldChars)
                        currentAssistantRow = i
                        self.headerList.append(i)
                        self.headerCount += 1

                        existsData = assistants.get(assistantKey, {})
                        existsDataKeys = existsData.keys()
                        existsDataKeys.sort()
                        for existsDataKey in existsDataKeys:
                            i = table.addRow()
                            table.setText(i, 0, i-self.headerCount)
                            column = 1
                            table.setText(i, column, existsDataKey)
                            column += 1
                            values = existsData.get(existsDataKey)
                            for value in values:
                                table.setText(i, column, value)
                                personResult[column-2] += value
                                assistantResult[column-2] += value
                                column += 1
                        self.setResult(currentAssistantRow, assistantResult, table)
                    orgStructureResult = map(lambda x, y: x+y, personResult, orgStructureResult)
                    self.setResult(currentPersonRow, personResult, table)
            else:
                persons = reportData.get(orgStructureId, {})
                personsKeys = persons.keys()
                personsKeys.sort()
                for personKey in personsKeys:
                    personResult = [0, 0, 0]
                    i = table.addRow()
                    table.setText(i, 0, personKey, charFormat=self.boldChars)
                    currentPersonRow = i
                    self.headerList.append(i)
                    self.headerCount += 1
                    existsData = persons.get(personKey, {})
                    existsDataKeys = existsData.keys()
                    existsDataKeys.sort()
                    for existsDataKey in existsDataKeys:
                        i = table.addRow()
                        table.setText(i, 0, i-self.headerCount)
                        column = 1
                        table.setText(i, column, existsDataKey)
                        column += 1
                        values = existsData.get(existsDataKey)
                        for value in values:
                            table.setText(i, column, value)
                            personResult[column-2] += value
                            column += 1
                    orgStructureResult = map(lambda x, y: x+y, personResult, orgStructureResult)
                    self.setResult(currentPersonRow, personResult, table)
        else:
            if detailAssistant:
                assistants = reportData.get(orgStructureId, {})
                assistantKeys = assistants.keys()
                assistantKeys.sort()
                for assistantKey in assistantKeys:
                    assistantResult = [0, 0, 0]
                    i = table.addRow()
                    table.setText(i, 0, assistantKey, charFormat=self.boldChars)
                    currentAssistantRow = i
                    self.headerList.append(i)
                    self.headerCount += 1
                    existsData = assistants.get(assistantKey, {})
                    existsDataKeys = existsData.keys()
                    existsDataKeys.sort()
                    for existsDataKey in existsDataKeys:
                        i = table.addRow()
                        table.setText(i, 0, i-self.headerCount)
                        column = 1
                        table.setText(i, column, existsDataKey)
                        column += 1
                        values = existsData.get(existsDataKey)
                        for value in values:
                            table.setText(i, column, value)
                            orgStructureResult[column-2] += value
                            assistantResult[column-2] += value
                            column += 1
                    self.setResult(currentAssistantRow, assistantResult, table)
            else:
                existsData = reportData.get(orgStructureId, {})
                existsDataKeys = existsData.keys()
                existsDataKeys.sort()
                for existsDataKey in existsDataKeys:
                    i = table.addRow()
                    table.setText(i, 0, i-self.headerCount)
                    column = 1
                    table.setText(i, column, existsDataKey)
                    column += 1
                    values = existsData.get(existsDataKey)
                    for value in values:
                        table.setText(i, column, value)
                        orgStructureResult[column-2] += value
                        column += 1

        return orgStructureResult


    def setResult(self, row, resultValues, table):
        for idx, value in enumerate(resultValues):
            table.setText(row, idx+2, value, charFormat=self.boldChars)
