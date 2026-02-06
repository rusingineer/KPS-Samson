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
from PyQt4.QtCore import Qt, pyqtSignature, QDate

from library.database   import CTableRecordCache
from library.TableModel import CTableModel, CTextCol
from library.Utils      import forceInt, forceRef, forceString

from Events.Utils       import getWorkEventTypeFilter
from Orgs.Utils         import getOrgStructureDescendants
from Reports.ReportBase import CReportBase, createTable
from Reports.Report     import CReport

from Reports.Ui_ReportUniversalEventListSetupDialog import Ui_ReportUniversalEventListSetupDialog


def selectData(params):
    begDate = params.get('begDate', QDate())
    endDate = params.get('endDate', QDate())
    eventPurposeId = params.get('eventPurposeId', None)
    eventTypeIdList = params.get('eventTypeIdList', None)
    orgStructureId = params.get('orgStructureId', None)
    specialityId = params.get('specialityId', None)
    personId = params.get('personId', None)
    typeFinanceId = params.get('typeFinanceId', None)
    visitPayStatus = params.get('visitPayStatus', 0)

    stmt="""
SELECT
    SUM(IF(Event.execDate IS NULL, 1, 0)) AS countETNoEnd,
    SUM(IF(Event.execDate IS NOT NULL, 1, 0)) AS countETEnd,
    Event.execPerson_id,
    EventType.id AS eventTypeId,
    EventType.code AS codeEventType,
    EventType.name AS nameEventType,
    vrbPersonWithSpeciality.name AS personName,
    EXISTS(SELECT Account_Item.id
    FROM Account_Item
    WHERE Account_Item.event_id = Event.id
    AND Account_Item.deleted = 0
    AND Account_Item.number = '%s') AS paymentConfirmation
FROM Event
INNER JOIN EventType ON EventType.id = Event.eventType_id
INNER JOIN Contract ON Contract.id = Event.contract_id
LEFT JOIN vrbPersonWithSpeciality ON vrbPersonWithSpeciality.id = Event.execPerson_id
WHERE
    %s
GROUP BY eventTypeId, execPerson_id, paymentConfirmation, personName
ORDER BY EventType.code, EventType.name, personName, eventTypeId, execPerson_id, paymentConfirmation
"""
    db = QtGui.qApp.db
    tablePerson = db.table('vrbPersonWithSpeciality')
    tableContract = db.table('Contract')
    tableEvent  = db.table('Event')
    tableEventType = db.table('EventType')
    cond = [tableEvent['deleted'].eq(0),
            tableEventType['deleted'].eq(0),
            tableContract['deleted'].eq(0)
            ]
    if endDate:
        cond.append(tableEvent['setDate'].lt(endDate.addDays(1)))
    if begDate:
        cond.append(tableEvent['setDate'].ge(begDate))
    if eventTypeIdList:
        cond.append(tableEvent['eventType_id'].inlist(eventTypeIdList))
    elif eventPurposeId:
        cond.append(tableEventType['purpose_id'].eq(eventPurposeId))
    if personId:
        cond.append(tableEvent['execPerson_id'].eq(personId))
    elif orgStructureId:
        cond.append(tablePerson['orgStructure_id'].inlist(getOrgStructureDescendants(orgStructureId)))
    else:
        cond.append(tablePerson['org_id'].eq(QtGui.qApp.currentOrgId()))
    if specialityId:
        cond.append(tablePerson['speciality_id'].eq(specialityId))
    if typeFinanceId:
        cond.append(tableContract['finance_id'].eq(typeFinanceId))
    visitPayStatus -= 1
    if visitPayStatus >= 0:
        cond.append(u'getPayCode(Contract.finance_id, Event.payStatus) = %d'%(visitPayStatus))
    return db.query(stmt % (u'Принято ЕИС', db.joinAnd(cond)))


class CReportUniversalEventList(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setPayPeriodVisible(False)
        self.setTitle(u'Универсальный отчет по событиям')


    def getSetupDialog(self, parent):
        result = CReportUniversalEventListSetupDialog(parent)
        return result


    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParamsEventTypeList(cursor, params)
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        tempMergeColums = {}
        tempColums = {}
        reportLine = {}
        reportTotalPerson = {}
        reportTotalEvent = {}
        tableColumns = [('10%', [u'ФИО, Специальность врача', u''], CReportBase.AlignLeft)]
        mergeCol = 1
        query = selectData(params)
        while query.next():
            record = query.record()
            eventTypeId = forceRef(record.value('eventTypeId'))
            codeEventType = forceString(record.value('codeEventType'))
            nameEventType = forceString(record.value('nameEventType'))
            execPersonId = forceRef(record.value('execPerson_id'))
            personName = forceString(record.value('personName'))
            paymentConfirmation = forceInt(record.value('paymentConfirmation'))
            countETNoEnd = forceInt(record.value('countETNoEnd'))
            countETEnd = forceInt(record.value('countETEnd'))
            if eventTypeId and eventTypeId not in tempMergeColums.keys():
                tempMergeColums[eventTypeId] = mergeCol
                tempColums[mergeCol] = [codeEventType, nameEventType]
                mergeCol += 3
            lineTotalEvent = reportTotalEvent.get(eventTypeId, [0]*3)
            lineTotalPerson = reportTotalPerson.get((personName, execPersonId), [0]*3)
            reportPersonLine = reportLine.get((personName, execPersonId), {})
            reportCountLine = reportPersonLine.get(eventTypeId, [0]*3)
            reportCountLine[0] += countETNoEnd
            lineTotalPerson[0] += countETNoEnd
            lineTotalEvent[0] += countETNoEnd
            reportCountLine[1] += countETEnd
            lineTotalPerson[1] += countETEnd
            lineTotalEvent[1] += countETEnd
            if paymentConfirmation:
                reportCountLine[2] += countETEnd
                lineTotalPerson[2] += countETEnd
                lineTotalEvent[2] += countETEnd
            reportPersonLine[eventTypeId] = reportCountLine
            reportLine[(personName, execPersonId)] = reportPersonLine
            reportTotalPerson[(personName, execPersonId)] = lineTotalPerson
            reportTotalEvent[eventTypeId] = lineTotalEvent
            lineTotalEvent = reportTotalEvent.get(None, [0]*3)
            lineTotalEvent[0] += countETNoEnd
            lineTotalEvent[1] += countETEnd
            if paymentConfirmation:
                lineTotalEvent[2] += countETEnd
            reportTotalEvent[None] = lineTotalEvent
        countEventType = len(tempColums)
        if countEventType:
            tempColumsKeys = tempColums.keys()
            tempColumsKeys.sort()
            for col in tempColumsKeys:
                val = tempColums.get(col, [u'', u''])
                tableColumns.insert(col, ('%2.2f'%(90.0/((countEventType+1)*3))+'%', [u'%s'%(val[0]+u' '+val[1]), u'Всего открытых событий'], CReportBase.AlignLeft))
                tableColumns.insert(col+1, ('%2.2f'%(90.0/((countEventType+1)*3))+'%', [u'', u'Всего закрытых событий'], CReportBase.AlignLeft))
                tableColumns.insert(col+2, ('%2.2f'%(90.0/((countEventType+1)*3))+'%', [u'', u'Всего закрытых событий, принятых на оплату'], CReportBase.AlignLeft))
            tableColumns.append(('%2.2f'%(90.0/((countEventType+1)*3))+'%', [u'Итог по всем событиям', u'Всего открытых событий'], CReportBase.AlignLeft))
            tableColumns.append(('%2.2f'%(90.0/((countEventType+1)*3))+'%', [u'', u'Всего закрытых событий'], CReportBase.AlignLeft))
            tableColumns.append(('%2.2f'%(90.0/((countEventType+1)*3))+'%', [u'', u'Всего закрытых событий, принятых на оплату'], CReportBase.AlignLeft))
            table = createTable(cursor, tableColumns)
            table.mergeCells(0, 0, 2, 1)
            for col in tempColumsKeys:
                table.mergeCells(0, col, 1, 3)
            table.mergeCells(0, len(tableColumns)-3, 1, 3)
            tempMergeColums[None] = len(tableColumns)-3
            keysPerson = reportLine.keys()
            keysPerson.sort()
            rowColList = {}
            for keyPerson in keysPerson:
                reportPersonLine = reportLine.get(keyPerson, {})
                if reportPersonLine:
                    i = table.addRow()
                    table.setText(i, 0, keyPerson[0])
                    colList = rowColList.get(i, [])
                    for keyVal, reportCountLine in reportPersonLine.items():
                        col = tempMergeColums.get(keyVal, None)
                        if col:
                            table.setText(i, col, reportCountLine[0])
                            table.setText(i, col+1, reportCountLine[1])
                            table.setText(i, col+2, reportCountLine[2])
                            colList.append(col)
                            colList.append(col+1)
                            colList.append(col+2)
                    rowColList[i] = colList
                lineTotalPerson = reportTotalPerson.get(keyPerson, [0]*3)
                table.setText(i, len(tableColumns)-3, lineTotalPerson[0], CReportBase.TableTotal)
                table.setText(i, len(tableColumns)-2, lineTotalPerson[1], CReportBase.TableTotal)
                table.setText(i, len(tableColumns)-1, lineTotalPerson[2], CReportBase.TableTotal)
            for row, colList in rowColList.items():
                for col in range(countEventType*3+1):
                    if col and col not in colList:
                       table.setText(row, col, 0)
            if reportLine:
                i = table.addRow()
                table.setText(i, 0, u'Итого (сумма события по врачам):', CReportBase.TableTotal)
                for keyET, valET in tempMergeColums.items():
                    lineTotalEvent = reportTotalEvent.get(keyET, [0]*3)
                    table.setText(i, valET, lineTotalEvent[0], CReportBase.TableTotal)
                    table.setText(i, valET+1, lineTotalEvent[1], CReportBase.TableTotal)
                    table.setText(i, valET+2, lineTotalEvent[2], CReportBase.TableTotal)
        return doc


class CReportUniversalEventListSetupDialog(QtGui.QDialog, Ui_ReportUniversalEventListSetupDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.patientRequired = False
        self.tableModel = CEventTypeTableModel(self)
        self.tableSelectionModel = QtGui.QItemSelectionModel(self.tableModel, self)
        self.tableSelectionModel.setObjectName('tableSelectionModel')
        self.setupUi(self)
        self.cmbEventPurpose.setTable('rbEventTypePurpose', True, filter='code != \'0\'')
        self.cmbSpeciality.setTable('rbSpeciality', True)
        self.cmbFinance.setTable('rbFinance')
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())
        self.filter = []
        self.tblEventType.setModel(self.tableModel)
        self.tblEventType.setSelectionModel(self.tableSelectionModel)
        self.tblEventType.installEventFilter(self)
        self.tblEventType.model().setIdList(self.setEventTypeIdList())
        self.setTitle(u'Универсальный отчет по событиям')
        self.cmbVisitPayStatus.setCurrentIndex(0)


    def getSelectEventTypeList(self):
        return self.tblEventType.selectedItemIdList()


    def setSelectEventTypeList(self, eventTypeList):
        self.tblEventType.clearSelection()
        if eventTypeList:
            self.tblEventType.setSelectedItemIdList(eventTypeList)


    def setEventTypeIdList(self):
        db = QtGui.qApp.db
        tableEventType = db.table('EventType')
        cond = [tableEventType['deleted'].eq(0)]
        if self.filter:
            cond.append(self.filter)
        return db.getDistinctIdList(tableEventType, tableEventType['id'].name(),
                              where=cond,
                              order=u'EventType.code ASC, EventType.name ASC')


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        self.cmbEventPurpose.setValue(params.get('eventPurposeId', None))
        self.setSelectEventTypeList(params.get('eventTypeIdList', None))
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))
        self.cmbSpeciality.setValue(params.get('specialityId', None))
        self.cmbPerson.setValue(params.get('personId', None))
        self.cmbVisitPayStatus.setCurrentIndex(params.get('visitPayStatus', 0))
        self.cmbFinance.setValue(params.get('typeFinanceId', None))


    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['eventPurposeId'] = self.cmbEventPurpose.value()
        result['eventTypeIdList'] = self.getSelectEventTypeList()
        result['orgStructureId'] = self.cmbOrgStructure.value()
        result['specialityId'] = self.cmbSpeciality.value()
        result['personId'] = self.cmbPerson.value()
        result['visitPayStatus'] = self.cmbVisitPayStatus.currentIndex()
        result['typeFinanceId'] = self.cmbFinance.value()
        return result


    @pyqtSignature('QDate')
    def on_edtBegDate_dateChanged(self, date):
        self.cmbPerson.setBegDate(date)


    @pyqtSignature('QDate')
    def on_edtEndDate_dateChanged(self, date):
        self.cmbPerson.setEndDate(date)


    @pyqtSignature('int')
    def on_cmbEventPurpose_currentIndexChanged(self, index):
        eventPurposeId = self.cmbEventPurpose.value()
        if eventPurposeId:
            self.filter = 'EventType.purpose_id =%d' % eventPurposeId
        else:
            self.filter = getWorkEventTypeFilter(isApplyActive=True)
        self.tblEventType.model().setIdList(self.setEventTypeIdList())


    @pyqtSignature('int')
    def on_cmbOrgStructure_currentIndexChanged(self, index):
        self.cmbPerson.setOrgStructureId(self.cmbOrgStructure.value())


    @pyqtSignature('int')
    def on_cmbSpeciality_currentIndexChanged(self, index):
        self.cmbPerson.setSpecialityId(self.cmbSpeciality.value())


class CEventTypeTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self._parent = parent
        self._specialValues = []
        self.addColumn(CTextCol(u'Код', ['code'], 5))
        self.addColumn(CTextCol(   u'Наименование',     ['name'], 40))
        self._fieldNames = ['EventType.id', 'EventType.code', 'EventType.name']
        self.setTable('EventType')


    def flags(self, index):
        return Qt.ItemIsEnabled|Qt.ItemIsSelectable


    def setTable(self, tableName):
        db = QtGui.qApp.db
        tableEventType = db.table('EventType')
        loadFields = []
        loadFields.append(u'DISTINCT '+ u', '.join(self._fieldNames))
        self._table = tableEventType
        self._recordsCache = CTableRecordCache(db, self._table, loadFields, fakeValues=self._specialValues)

