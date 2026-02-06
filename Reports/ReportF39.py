# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2025 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignature, QDate, QString

from library.database   import addDateInRange
from library.Utils      import forceBool, forceDate, forceInt, forceRef, forceString, pyDate

from Events.Utils       import getWorkEventTypeFilter
from Events.EventTypeListEditorDialog import CEventTypeListEditorDialog
from Orgs.Utils         import getOrgStructureDescendants
from Orgs.OrgStructComboBoxes import COrgStructureModel
from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable
from Reports.ReportView import CPageFormat
from Reports.Utils import getRetireeAges

# Комбобокс "Местность"
ADDRESS_TYPE_NOT_SET = 0
ADDRESS_TYPE_URBAN = 1
ADDRESS_TYPE_VILLAGER = 2

def selectData(params, scene):
    stmt="""
SELECT
    COUNT(*) AS cnt,
    %s AS rowKey,
    isAddressVillager(ClientAddress.address_id) AS clientRural,
    IF(rbScene.code = '2' OR rbScene.code = '3',0,1)  AS atAmbulance,
    rbEventTypePurpose.code AS purpose,
    age(Client.birthDate, Visit.date) as clientAge,
    Visit.finance_id AS finance_id,
    Client.sex as sex,
    IF(rbPost.code LIKE '1%%' OR rbPost.code LIKE '2%%' OR rbPost.code LIKE '3%%', 1, 0) AS postCode
FROM Visit
LEFT JOIN Event     ON Event.id = Visit.event_id
LEFT JOIN EventType ON EventType.id = Event.eventType_id
LEFT JOIN rbEventTypePurpose ON rbEventTypePurpose.id = EventType.purpose_id
LEFT JOIN rbMedicalAidType ON rbMedicalAidType.id = EventType.medicalAidType_id
LEFT JOIN Person    ON Person.id = Visit.person_id
LEFT JOIN rbPost    ON rbPost.id = Person.post_id
LEFT JOIN Client    ON Client.id = Event.client_id
LEFT JOIN ClientAddress ON ClientAddress.id =
          (SELECT MAX(CA.id)
           FROM ClientAddress AS CA
           WHERE CA.client_id = Event.client_id
             AND CA.deleted = 0
             AND CA.type=0
          )
LEFT JOIN rbScene   ON rbScene.id = Visit.scene_id
WHERE rbEventTypePurpose.code != \'0\'
AND Visit.deleted=0
AND Event.deleted=0
AND DATE(Event.setDate) <= DATE(Visit.date)
AND %s
GROUP BY
    rowKey,
    Visit.id,
    clientRural,
    atAmbulance,
    purpose,
    clientAge,
    finance_id,
    postCode
    """
    begDate = params.get('begDate', QDate())
    endDate = params.get('endDate', QDate())
    visitTypeId = params.get('visitTypeId', None)
    eventPurposeId = params.get('eventPurposeId', None)
    eventTypeList = params.get('eventTypeList', [])
    orgStructureId = params.get('orgStructureId', None)
    personId = params.get('personId', None)
    rowGrouping = params.get('rowGrouping', 0)
    visitPayStatus = params.get('visitPayStatus', 0)
    visitHospital = params.get('visitHospital', False)
    isEventClosed = params.get('isEventClosed', 0)
    sex = params.get('sex', 0)
    ageFrom = params.get('ageFrom', 0)
    ageTo = params.get('ageTo', 150)
    typeFinanceId = params.get('financeId', None)
    addressType = params.get('addressType', ADDRESS_TYPE_NOT_SET)

    db = QtGui.qApp.db
    tableVisit  = db.table('Visit')
    tableEvent  = db.table('Event')
    tableEventType = db.table('EventType')
    tablePerson = db.table('Person')
    tableClient = db.table('Client')
    cond = []
    addDateInRange(cond, tableVisit['date'], begDate, endDate)
    if visitTypeId:
        cond.append(tableVisit['visitType_id'].eq(visitTypeId))
    if eventTypeList:
        cond.append(tableEvent['eventType_id'].inlist(eventTypeList))
    elif eventPurposeId:
        tableEvent = db.table('Event')
        cond.append(tableEventType['purpose_id'].eq(eventPurposeId))
    if personId:
        cond.append(tableVisit['person_id'].eq(personId))
    elif orgStructureId:
        cond.append(tablePerson['orgStructure_id'].inlist(getOrgStructureDescendants(orgStructureId)))
    else:
        cond.append(tablePerson['org_id'].eq(QtGui.qApp.currentOrgId()))
    if rowGrouping == 5: # by post_id
        groupField = 'Person.post_id'
    elif rowGrouping == 4: # by speciality_id
        groupField = 'Person.speciality_id'
    elif rowGrouping == 3: # by orgStructureId
        groupField = 'Person.orgStructure_id'
    elif rowGrouping == 2: # by personId
        groupField = 'Visit.person_id'
    elif rowGrouping == 1: # by month
        groupField = '''CONCAT_WS('-', MONTH(Visit.date), YEAR(Visit.date))'''
    else: # by date
        groupField = 'DATE(Visit.date)'
    if typeFinanceId:
        cond.append(tableVisit['finance_id'].eq(typeFinanceId))
    visitPayStatus -= 1
    if visitPayStatus >= 0:
        cond.append(u'getPayCode(Visit.finance_id, Visit.payStatus) = %d'%(visitPayStatus))
    if not visitHospital:
        cond.append(u'''(EventType.medicalAidType_id IS NULL OR rbMedicalAidType.code != '7')''')
    if sex:
        cond.append(tableClient['sex'].eq(sex))
    if scene:
        cond.append('Visit.scene_id = %i' % scene)
    if ageFrom <= ageTo:
        cond.append('Visit.date >= ADDDATE(Client.birthDate, INTERVAL %d YEAR)'%ageFrom)
        cond.append('Visit.date < SUBDATE(ADDDATE(Client.birthDate, INTERVAL %d YEAR),1)'%(ageTo+1))
    if isEventClosed == 1:
        cond.append('Event.execDate is not NULL')
    elif isEventClosed == 2:
        cond.append('Event.execDate is NULL')

    if addressType == ADDRESS_TYPE_VILLAGER:
        cond.append('isAddressVillager(ClientAddress.address_id) = 1')
    if addressType == ADDRESS_TYPE_URBAN:
        cond.append('isAddressVillager(ClientAddress.address_id) = 0')

    wholeStmt = stmt % (groupField, db.joinAnd(cond))
    return db.query(wholeStmt)


class CReportF39(CReport):
    def __init__(self, parent, additionalFields = False):
        CReport.__init__(self, parent)
        self.setPayPeriodVisible(False)
        self.setTitle(u'Форма 39')
        self.pageFormat = CPageFormat(pageSize=CPageFormat.A4, orientation=CPageFormat.Landscape, leftMargin=5,
                                      topMargin=5, rightMargin=5, bottomMargin=5)
        self.additionalFields = additionalFields


    def dumpParamsMultiSelect(self, cursor, params):
        description = []
        eventTypeList = params.get('eventTypeList', None)
        if eventTypeList:
            db = QtGui.qApp.db
            tableET = db.table('EventType')
            records = db.getRecordList(tableET, [tableET['name']], [tableET['deleted'].eq(0), tableET['id'].inlist(eventTypeList)])
            nameList = []
            for record in records:
                nameList.append(forceString(record.value('name')))
            description.append(u'тип события:  %s'%(u','.join(name for name in nameList if name)))
        else:
            description.append(u'тип события:  не задано')
        columns = [ ('100%', [], CReportBase.AlignLeft) ]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)


    def getDescription(self, params):
        rows = CReport.getDescription(self, params)
        addressType = params.get('addressType', ADDRESS_TYPE_NOT_SET)
        if addressType != ADDRESS_TYPE_NOT_SET:
            rows.insert(-1, u'местность: ' + (u'сельские' if addressType == ADDRESS_TYPE_VILLAGER else u'городские'))
        return rows


    def getSetupDialog(self, parent):
        result = CReportF39SetupDialog(parent)
        result.setTitle(self.title())
        result.setAdditionalFieldsVisible(self.additionalFields)
        return result

    def calculateReportDataIfDetailaChildren(self, record, reportData, forceKeyVal, rowSize, financeIndexes, seniorAges):
        rowKey    = forceKeyVal(record.value('rowKey'))
        cnt       = forceInt(record.value('cnt'))
        atAmbulance = forceBool(record.value('atAmbulance'))
        purpose   = forceString(record.value('purpose'))
        age       = forceInt(record.value('clientAge'))
        sex       = forceInt(record.value('sex'))
        financeId = forceInt(record.value('finance_id'))
        clientRural = forceInt(record.value('clientRural'))
        postCode =  forceInt(record.value('postCode'))

        rowData = reportData.get(rowKey, None)
        if not rowData:
            rowData = {}
            row = [0]*(rowSize)
            rowData[postCode] = row
            reportData[rowKey] = rowData
        else:
            row = rowData.get(postCode, None)
        if not row:
            row = [0]*(rowSize)
            rowData[postCode] = row
            reportData[rowKey] = rowData

        cure = purpose == '1'
        prophylaxy = purpose == '2'
        if atAmbulance:
            row[0] += cnt
            if clientRural:
                row[1] += cnt
            if age<=1:
                row[2] += cnt
                row[4] += cnt
            elif age<=14:
                row[2] += cnt
            elif age>=15 and age<=17:
                row[3] += cnt
            elif (age >= seniorAges[0] and sex == 1) or (age >= seniorAges[1] and sex == 2):
                row[5] += cnt
            if cure:
                row[6] += cnt
                if age<=1:
                    row[7] += cnt
                    row[9] += cnt
                elif age<=14:
                    row[7] += cnt
                elif age>=15 and age<=17:
                    row[8] += cnt
                elif (age >= seniorAges[0] and sex == 1) or (age >= seniorAges[1] and sex == 2):
                    row[10] += cnt
            elif prophylaxy:
                row[11] += cnt
        else:
            row[12] += cnt
            if cure:
                row[13] += cnt
                if age<=1:
                    row[14] += cnt
                    row[16] += cnt
                elif age<=14:
                    row[14] += cnt
                elif age>=15 and age<=17:
                    row[15] += cnt
                elif (age >= seniorAges[0] and sex == 1) or (age >= seniorAges[1] and sex == 2):
                    row[17] += cnt
            elif prophylaxy:
                if age<=14:
                    row[18] += cnt
                    row[20] += cnt
                elif age>=15 and age<=17:
                    row[19] += cnt
                elif age<=1:
                    row[20] += cnt
        row[21+financeIndexes[financeId]] += cnt


    def calculateReportData(self, record, reportData, forceKeyVal, rowSize, financeIndexes, seniorAges):
        rowKey    = forceKeyVal(record.value('rowKey'))
        cnt       = forceInt(record.value('cnt'))
        atAmbulance = forceBool(record.value('atAmbulance'))
        purpose   = forceString(record.value('purpose'))
        age       = forceInt(record.value('clientAge'))
        sex       = forceInt(record.value('sex'))
        financeId = forceInt(record.value('finance_id'))
        clientRural = forceInt(record.value('clientRural'))
        postCode =  forceInt(record.value('postCode'))

        rowData = reportData.get(rowKey, None)
        if not rowData:
            rowData = {}
            row = [0]*(rowSize)
            rowData[postCode] = row
            reportData[rowKey] = rowData
        else:
            row = rowData.get(postCode, None)
        if not row:
            row = [0]*(rowSize)
            rowData[postCode] = row
            reportData[rowKey] = rowData

        cure = purpose == '1'
        prophylaxy = purpose == '2'
        if atAmbulance:
            row[0] += cnt
            if clientRural:
                row[1] += cnt
            if age<=1:
                row[2] += cnt
                row[3] += cnt
            elif age<=17:
                row[2] += cnt
            elif (age >= seniorAges[0] and sex == 1) or (age >= seniorAges[1] and sex == 2):
                row[4] += cnt
            if cure:
                row[5] += cnt
                if age<=1:
                    row[6] += cnt
                    row[7] += cnt
                elif age<=17:
                    row[6] += cnt
                elif (age >= seniorAges[0] and sex == 1) or (age >= seniorAges[1] and sex == 2):
                    row[8] += cnt
            elif prophylaxy:
                row[9] += cnt
        else:
            row[10] += cnt
            if cure:
                row[11] += cnt
                if age<=1:
                    row[12] += cnt
                    row[13] += cnt
                elif age<=17:
                    row[12] += cnt
                elif (age >= seniorAges[0] and sex == 1) or (age >= seniorAges[1] and sex == 2):
                    row[14] += cnt
            elif prophylaxy:
                if age<=17:
                    row[15] += cnt
                if age<=1:
                    row[16] += cnt
        row[17+financeIndexes[financeId]] += cnt


    def build(self, params):
        rowGrouping = params.get('rowGrouping', 0)
        visitPayStatus = params.get('visitPayStatus', 0)
        detailChildren = params.get('detailChildren', False)
        orgStructureId = params.get('orgStructureId', None)
        scene = params.get('sceneId',  None) if self.additionalFields else None
        visitPayStatus -= 1
        seniorAges = getRetireeAges(params.get('begDate', QDate()))
        if rowGrouping == 5: # by post_id
            forceKeyVal = forceRef
            keyValToString = lambda postId: forceString(QtGui.qApp.db.translate('rbPost', 'id', postId, 'name'))
            keyValToSort = keyValToString
            keyName = u'Должность'
        elif rowGrouping == 4: # by speciality_id
            forceKeyVal = forceRef
            keyValToString = lambda specialityId: forceString(QtGui.qApp.db.translate('rbSpeciality', 'id', specialityId, 'name'))
            keyValToSort = keyValToString
            keyName = u'Специальность'
        elif rowGrouping == 3: # by orgStructureId
            forceKeyVal = forceRef
            keyValToString = None
            keyValToSort = None
            keyName = u'Подразделение'
        elif rowGrouping == 2: # by personId
            forceKeyVal = forceRef
            keyValToString = lambda personId: forceString(QtGui.qApp.db.translate('vrbPersonWithSpeciality', 'id', personId, 'name'))
            keyValToSort = keyValToString
            keyName = u'Врач'
        elif rowGrouping == 1: # by month
            forceKeyVal = forceString
            keyValToString = lambda x: forceString(x)
            keyValToSort = lambda x: (forceInt(QString(x).split('-')[1]), forceInt(QString(x).split('-')[0]))
            keyName = u'Месяц'
        else: # by date
            forceKeyVal = lambda x: pyDate(forceDate(x))
            keyValToSort = None
            keyValToString = lambda x: forceString(QDate(x))
            keyName = u'Дата'

        db = QtGui.qApp.db
        financeNames   = []
        financeIndexes = {}
        for index, record in enumerate(db.getRecordList('rbFinance', 'id, name', '', 'code')):
            financeId = forceRef(record.value(0))
            financeName = forceString(record.value(1))
            financeIndexes[financeId] = index
            financeNames.append(financeName)
        if not(financeNames):
            financeNames.append(u'не определено')

        rowSize = (21 if detailChildren else 17)+len(financeNames)
        query = selectData(params, scene)
        reportData = {}
        calculate = self.calculateReportDataIfDetailaChildren if detailChildren else self.calculateReportData
        while query.next():
            record = query.record()
            calculate(record, reportData, forceKeyVal, rowSize, financeIndexes, seniorAges)

        # now text
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParamsMultiSelect(cursor, params)
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        tableColumns = [

            ( '10%', [keyName], CReportBase.AlignLeft),
            ( '5%', [u'Амбулаторно', u'все-\nго'         ], CReportBase.AlignRight),
            ( '5%', [u'',            u'с.ж.'             ], CReportBase.AlignRight),
            ( '5%', [u'',            u'', u'', u'0-1 год' ], CReportBase.AlignRight),
            ( '5%', [u'',            u'', u'', u'старше трудоспособно го возраста'], CReportBase.AlignRight),
            ( '5%', [u'',            u'по поводу заболеваний', u'все-\nго'], CReportBase.AlignRight),
            ( '5%', [u'',            u'', u'', u'0-1 год' ], CReportBase.AlignRight),
            ( '5%', [u'',            u'', u'', u'старше трудоспособно го возраста'], CReportBase.AlignRight),
            ( '5%', [u'',            u'про-\nфи-\nлак-\nти-\nчес-\nких'], CReportBase.AlignRight),
            ( '5%', [u'На дому',     u'все-\nго'         ], CReportBase.AlignRight),
            ( '5%', [u'',            u'по поводу заболеваний', u'все-\nго'], CReportBase.AlignRight),
            ( '5%', [u'',            u'', u'', u'0-1 год' ], CReportBase.AlignRight),
            ( '5%', [u'',            u'', u'', u'старше трудоспособно го возраста'], CReportBase.AlignRight),
            ( '5%', [u'',            u'', u'', u'0-1 год' ], CReportBase.AlignRight),
                   ]
#        if rowGrouping != 2:
        tableColumns.insert(0,  ( '5%', [u'№-\nСтроки'], CReportBase.AlignLeft))

        if detailChildren:
            tableColumns.insert(4,  ( '5%', [u'', u'в т.ч. в возрасте', u'',u'0-14 лет'], CReportBase.AlignRight))
            tableColumns.insert(5,  ( '5%', [u'', u'', u'', u'15-17 лет'], CReportBase.AlignRight))
            tableColumns.insert(9,  ( '5%', [u'', u'', u'', u'0-14 лет'], CReportBase.AlignRight))
            tableColumns.insert(10,  ( '5%', [u'', u'', u'', u'15-17 лет'], CReportBase.AlignRight))
            tableColumns.insert(16, ( '5%', [u'', u'', u'в т.ч. в возрасте',u'0-14 лет'], CReportBase.AlignRight))
            tableColumns.insert(17, ( '5%', [u'', u'', u'', u'15-17 лет'], CReportBase.AlignRight))
            tableColumns.insert(20, ( '5%', [u'', u'про-\nфи-\nлак-\nти-\nчес-\nких', u'', u'0-14 лет'], CReportBase.AlignRight))
            tableColumns.insert(21, ( '5%', [u'', u'', u'', u'15-17 лет'], CReportBase.AlignRight),)

        else:
            tableColumns.insert(4,  ( '5%', [u'', u'в т.ч. в возрасте', u'',u'0-17 лет'], CReportBase.AlignRight))
            tableColumns.insert(8,  ( '5%', [u'', u'', u'', u'0-17 лет'], CReportBase.AlignRight))
            tableColumns.insert(14, ( '5%', [u'', u'', u'в т.ч. в возрасте',u'0-17 лет'], CReportBase.AlignRight))
            tableColumns.insert(17, ( '5%', [u'', u'про-\nфи-\nлак-\nти-\nчес-\nких', u'', u'0-17 лет'], CReportBase.AlignRight))

        for financeName in financeNames:
            tableColumns.append(  ('4%', [financeName ], CReportBase.AlignRight) )

        table = createTable(cursor, tableColumns)

        if detailChildren:
            self.mergeCellsIfDetailChildren(table, financeNames)
        else:
            self.mergeCells(table, financeNames)


#        prevSpecName = None
#        total = None
#        grandTotal = [0]*rowSize

        if rowGrouping == 3: # by orgStructureId
            self.genOrgStructureReport(table, reportData, rowSize, orgStructureId)
        else:
            keys = reportData.keys()
            if keyValToSort:
                keys.sort(key=keyValToSort)
            else:
                keys.sort()
            total = [0]*rowSize
            grandTotalDoctor = [0]*rowSize
            grandTotalOtherPost = [0]*rowSize
            for key in keys:
                i = table.addRow()
                table.setText(i, 0, i-3)
                table.setText(i, 1, keyValToString(key))
                rowData = reportData[key]
                rowKeys = rowData.keys()
                rowTotal = [0]*rowSize
                for rowKey in rowKeys:
                    row = rowData[rowKey]
                    postCode = forceBool(rowKey)
                    for j in xrange(rowSize):
                        if postCode:
                            grandTotalDoctor[j] += row[j]
                        else:
                            grandTotalOtherPost[j] += row[j]
                        rowTotal[j] += row[j]
                for j in xrange(rowSize):
                    table.setText(i, j+2, rowTotal[j])
                    total[j] += rowTotal[j]
            i = table.addRow()
            table.setText(i, 1, u'всего', CReportBase.TableTotal)
            for j in xrange(rowSize):
                table.setText(i, j+2, total[j], CReportBase.TableTotal)
            self.produceTotalLine(table, u'в т.ч. врачи', grandTotalDoctor, rowSize)
            self.produceTotalLine(table, u'прочие', grandTotalOtherPost, rowSize)
        return doc


    def produceTotalLine(self, table, title, total, rowSize):
        i = table.addRow()
        table.setText(i, 1, title, CReportBase.TableTotal)
        for j in xrange(rowSize):
            table.setText(i, j+2, total[j], CReportBase.TableTotal)


    def mergeCellsIfDetailChildren(self, table, financeNames):
        table.mergeCells(0, 0, 4, 1) # строка
        table.mergeCells(0, 1, 4, 1) # key
        table.mergeCells(0, 2, 1, 12) # Амбулаторно
        table.mergeCells(1, 2, 3, 1) # всего
        table.mergeCells(1, 3, 3, 1) # с.ж.
        table.mergeCells(1, 4, 2, 4) # в возрасте
        table.mergeCells(1, 8, 1, 5) # по забол.
        table.mergeCells(2, 8, 2, 1) # всего
        table.mergeCells(1, 13, 3, 1)# профилактических
        table.mergeCells(2, 9, 2, 1) # 0-14
        table.mergeCells(2, 10, 2, 1) # 15-17
        table.mergeCells(2, 11, 2, 1) # <=1
        table.mergeCells(2, 12, 2, 1) # >=60
        table.mergeCells(2, 16, 1, 4)# в т.ч. в возрасте
        table.mergeCells(2, 15, 2, 1)# Всего
        table.mergeCells(1, 15, 1, 5)# по поводу заболеваний
        table.mergeCells(0, 14, 1, 9) # на дому
        table.mergeCells(1, 14, 3, 1) # Всего
        table.mergeCells(1, 20, 1, 3) #
        table.mergeCells(2, 20, 2, 1) #
        table.mergeCells(2, 21, 2, 1) #
        table.mergeCells(2, 22, 2, 1) #

        for i in xrange(len(financeNames)):
            table.mergeCells(0, 23+i, 4, 1)

    def mergeCells(self, table, financeNames):
        table.mergeCells(0, 0, 4, 1) #строка
        table.mergeCells(0, 1, 4, 1) #key
        table.mergeCells(0, 2, 1, 10) # Амбулаторно
        table.mergeCells(1, 2, 3, 1) # всего
        table.mergeCells(1, 4, 1, 3) # в возрасте
        table.mergeCells(1, 3, 3, 1) # с.ж.

        table.mergeCells(2, 4, 2, 1)
        table.mergeCells(2, 5, 2, 1)
        table.mergeCells(2, 6, 2, 1)

        table.mergeCells(1, 7, 1, 4)
        table.mergeCells(2, 7, 2, 1)
        table.mergeCells(2, 8, 2, 1)
        table.mergeCells(2, 9, 2, 1)
        table.mergeCells(2, 10, 2, 1)
        table.mergeCells(1, 11, 3, 1)

        table.mergeCells(0, 12, 1, 7) #на дому
        table.mergeCells(1, 12, 3, 1) #всего
        table.mergeCells(1, 13, 1, 4) #по поводу заболеваний
        table.mergeCells(2, 13, 2, 1) #всего
        table.mergeCells(2, 14, 1, 3) #
        table.mergeCells(1, 17, 1, 2)#профилактических
        table.mergeCells(2, 17, 2, 1)
        table.mergeCells(2, 18, 2, 1)

        for i in xrange(len(financeNames)):
            table.mergeCells(0,19+i, 4, 1)


    def genOrgStructureReport(self, table, reportData, rowSize, orgStructureId):
        model = COrgStructureModel(None, QtGui.qApp.currentOrgId())
        index = model.findItemId(orgStructureId)
        if index:
            item = index.internalPointer()
        else:
            item = model.getRootItem()
        self.genOrgStructureReportForItem(table, reportData, item, rowSize, {})


    def genOrgStructureReportForItem(self, table, reportData, item, rowSize, grandTotalAll = {}):
        def setParentTotal(curItem, rowData, rowSize, grandTotalAll):
            currentId = curItem.id()
            parentItem = curItem.parent()
            parentId = parentItem._id if parentItem else None
            while True:
                if currentId != parentId:
                    currentTotalAll = grandTotalAll.get(currentId, {})
                    curTotal = currentTotalAll.get('total', [0]*rowSize)
                    curTotalDoctor = currentTotalAll.get('grandTotalDoctor', [0]*rowSize)
                    curTotalOtherPost = currentTotalAll.get('grandTotalOtherPost', [0]*rowSize)
                    prevTotalAll = grandTotalAll.get(parentId, {})
                    prevTotal = prevTotalAll.get('total', [0]*rowSize)
                    prevTotalDoctor = prevTotalAll.get('grandTotalDoctor', [0]*rowSize)
                    prevTotalOtherPost = prevTotalAll.get('grandTotalOtherPost', [0]*rowSize)
                else:
                    prevTotalAll = grandTotalAll.get(parentId, {})
                    prevTotal = prevTotalAll.get('total', [0]*rowSize)
                    prevTotalDoctor = prevTotalAll.get('grandTotalDoctor', [0]*rowSize)
                    prevTotalOtherPost = prevTotalAll.get('grandTotalOtherPost', [0]*rowSize)
                for rowKey, valList  in rowData.items():
                    postCode = forceBool(rowKey)
                    for j in xrange(rowSize):
                        if postCode:
                            if currentId != parentId:
                                curTotalDoctor[j] += valList[j]
                                prevTotalDoctor[j] += valList[j]
                            else:
                                prevTotalDoctor[j] += valList[j]
                        else:
                            if currentId != parentId:
                                curTotalOtherPost[j] += valList[j]
                                prevTotalOtherPost[j] += valList[j]
                            else:
                                prevTotalOtherPost[j] += valList[j]
                        if currentId != parentId:
                            curTotal[j] += valList[j]
                            prevTotal[j] += valList[j]
                        else:
                            prevTotal[j] += valList[j]
                if currentId != parentId:
                    currentTotalAll = {'total':curTotal, 'grandTotalDoctor':curTotalDoctor, 'grandTotalOtherPost':curTotalOtherPost}
                    prevTotalAll = {'total':prevTotal, 'grandTotalDoctor':prevTotalDoctor, 'grandTotalOtherPost':prevTotalOtherPost}
                    grandTotalAll[currentId] = currentTotalAll
                    grandTotalAll[parentId] = prevTotalAll
                else:
                    prevTotalAll = {'total':prevTotal, 'grandTotalDoctor':prevTotalDoctor, 'grandTotalOtherPost':prevTotalOtherPost}
                    grandTotalAll[parentId] = prevTotalAll
                if not parentId:
                    break
                parentItem = parentItem.parent()
                parentId = parentItem._id if parentItem else None
                currentId = parentId
            return grandTotalAll

        i = table.addRow()
        table.setText(i, 0, i-3)
        if item.childCount() == 0:
            table.setText(i, 1, item.name())
            rowData = reportData.get(item.id(), None)
            if rowData:
                rowKeys = rowData.keys()
                rowTotal = [0]*rowSize
                for rowKey in rowKeys:
                    row = rowData[rowKey]
                    for j in xrange(rowSize):
                        rowTotal[j] += row[j]
                for j in xrange(rowSize):
                    table.setText(i, j+2, rowTotal[j])
                grandTotalAll = setParentTotal(item, rowData, rowSize, grandTotalAll)
            return grandTotalAll
        else:
            table.mergeCells(i,1, 1, rowSize+1)
            table.mergeCells(i,1, 1, rowSize+1)
            table.setText(i, 1, item.name(), CReportBase.TableHeader)
            rowData = reportData.get(item.id(), None)
            if rowData:
                rowKeys = rowData.keys()
                rowTotal = [0]*rowSize
                i = table.addRow()
                table.setText(i, 1, '-', CReportBase.TableHeader)
                for rowKey in rowKeys:
                    row = rowData[rowKey]
                    for j in xrange(rowSize):
                        rowTotal[j] += row[j]
                for j in xrange(rowSize):
                    table.setText(i, j+2, rowTotal[j])
                grandTotalAll = setParentTotal(item, rowData, rowSize, grandTotalAll)
            for subitem in item.items():
                grandTotalAll = self.genOrgStructureReportForItem(table, reportData, subitem, rowSize, grandTotalAll)

            currentTotalAll = grandTotalAll.get(item.id(), {})
            curTotal = currentTotalAll.get('total', [0]*rowSize)
            curTotalDoctor = currentTotalAll.get('grandTotalDoctor', [0]*rowSize)
            curTotalOtherPost = currentTotalAll.get('grandTotalOtherPost', [0]*rowSize)
            i = table.addRow()
            table.setText(i, 0, i-3)
            table.setText(i, 1, u'всего по '+item.name(), CReportBase.TableTotal)
            for j in xrange(rowSize):
                table.setText(i, j+2, curTotal[j], CReportBase.TableTotal)
            self.produceTotalLine(table, u'в т.ч. врачи', curTotalDoctor, rowSize)
            self.produceTotalLine(table, u'прочие', curTotalOtherPost, rowSize)

            return grandTotalAll


from Ui_ReportF39Setup import Ui_ReportF39SetupDialog


class CReportF39SetupDialog(QtGui.QDialog, Ui_ReportF39SetupDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cmbVisitType.setTable('rbVisitType', True)
        self.cmbEventPurpose.setTable('rbEventTypePurpose', True, filter='code != \'0\'')
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())
        self.cmbVisitPayStatus.setCurrentIndex(0)
        self.cmbScene.setTable('rbScene', True, None)
        self.cmbScene.setVisible(False)
        self.lblScene.setVisible(False)
        self.cmbFinance.setTable('rbFinance')
        self.flag = None
        self.eventTypeList = []


    def setAdditionalFieldsVisible(self, flag = True):
        self.cmbScene.setVisible(flag)
        self.lblScene.setVisible(flag)
        self.cmbOrgStructure.setVisible(not flag)
        self.lblOrgStructure.setVisible(not flag)
        self.flag = flag


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        self.cmbVisitType.setValue(params.get('visitTypeId', None))
        self.cmbEventPurpose.setValue(params.get('eventPurposeId', None))
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))
        self.cmbPerson.setValue(params.get('personId', None))
        self.cmbRowGrouping.setCurrentIndex(params.get('rowGrouping', 0))
        self.cmbVisitPayStatus.setCurrentIndex(params.get('visitPayStatus', 0))
        self.chkDetailChildren.setChecked(params.get('detailChildren', False))
        self.chkVisitHospital.setChecked(params.get('visitHospital', False))
        self.cmbSex.setCurrentIndex(params.get('sex', 0))
        self.edtAgeFrom.setValue(params.get('ageFrom', 0))
        self.edtAgeTo.setValue(params.get('ageTo', 150))
        self.cmbIsEventClosed.setCurrentIndex(params.get('isEventClosed', 0))
        self.cmbScene.setValue(params.get('sceneId', 0))
        self.cmbFinance.setValue(params.get('financeId', None))
        self.cmbAddressType.setCurrentIndex(params.get('addressType', ADDRESS_TYPE_NOT_SET))
        self.eventTypeList =  params.get('eventTypeList', [])
        if self.eventTypeList:
            db = QtGui.qApp.db
            tableET = db.table('EventType')
            records = db.getRecordList(tableET, [tableET['name']], [tableET['deleted'].eq(0), tableET['id'].inlist(self.eventTypeList)])
            nameList = []
            for record in records:
                nameList.append(forceString(record.value('name')))
            self.lblEventTypeList.setText(u','.join(name for name in nameList if name))
        else:
            self.lblEventTypeList.setText(u'не задано')


    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['visitTypeId'] = self.cmbVisitType.value()
        result['eventPurposeId'] = self.cmbEventPurpose.value()
        result['orgStructureId'] = QtGui.qApp.currentOrgStructureId() if self.flag else self.cmbOrgStructure.value()
        result['personId'] = self.cmbPerson.value()
        result['rowGrouping'] = self.cmbRowGrouping.currentIndex()
        result['visitPayStatus'] = self.cmbVisitPayStatus.currentIndex()
        result['detailChildren'] = self.chkDetailChildren.isChecked()
        result['visitHospital'] = self.chkVisitHospital.isChecked()
        result['sex'] = self.cmbSex.currentIndex()
        result['ageFrom'] = self.edtAgeFrom.value()
        result['ageTo'] = self.edtAgeTo.value()
        result['isEventClosed'] = self.cmbIsEventClosed.currentIndex()
        result['sceneId'] = self.cmbScene.value() if self.flag else None
        result['financeId'] = self.cmbFinance.value()
        result['eventTypeList'] = self.eventTypeList
        result['addressType'] = self.cmbAddressType.currentIndex()
        return result


    @pyqtSignature('QDate')
    def on_edtBegDate_dateChanged(self, date):
        self.cmbPerson.setBegDate(date)


    @pyqtSignature('QDate')
    def on_edtEndDate_dateChanged(self, date):
        self.cmbPerson.setEndDate(date)


    @pyqtSignature('int')
    def on_cmbEventPurpose_currentIndexChanged(self, index):
        self.eventTypeList = []
        self.lblEventTypeList.setText(u'не задано')


    @pyqtSignature('int')
    def on_cmbOrgStructure_currentIndexChanged(self, index):
        orgStructureId = self.cmbOrgStructure.value()
        self.cmbPerson.setOrgStructureId(orgStructureId)


    @pyqtSignature('')
    def on_btnEventTypeList_clicked(self):
        self.eventTypeList = []
        self.lblEventTypeList.setText(u'не задано')
        eventPurposeId = self.cmbEventPurpose.value()
        if eventPurposeId:
            filter = u'EventType.purpose_id =%d' % eventPurposeId
        else:
            filter = getWorkEventTypeFilter(isApplyActive=True)
        dialog = CEventTypeListEditorDialog(self, filter)
        if dialog.exec_():
            self.eventTypeList = dialog.values()
            if self.eventTypeList:
                db = QtGui.qApp.db
                tableET = db.table('EventType')
                records = db.getRecordList(tableET, [tableET['name']], [tableET['deleted'].eq(0), tableET['id'].inlist(self.eventTypeList)])
                nameList = []
                for record in records:
                    nameList.append(forceString(record.value('name')))
                self.lblEventTypeList.setText(u','.join(name for name in nameList if name))

