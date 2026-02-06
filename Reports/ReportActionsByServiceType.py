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

from library.Utils            import firstMonthDay, forceDouble, forceInt, forceRef, forceString, lastMonthDay
from Events.ActionServiceType import CActionServiceType

from Orgs.Utils               import getOrgStructureFullName
from Reports.Report           import CReport
from Reports.ReportBase       import CReportBase, createTable
from Reports.ReportView       import CPageFormat
from Timeline.Schedule        import CSchedule

from Ui_ReportActionsByServiceTypeSetupDialog import Ui_ReportActionsByServiceTypeSetupDialog


def selectData(params):
    begDate        = params.get('begDate', None)
    endDate        = params.get('endDate', None)
    eventTypeId    = params.get('eventTypeId', None)
    orgStructureId = params.get('orgStructureId', None)
    fiananceId     = params.get('fiananceId', None)
    confirmation        = params.get('confirmation', False)
    confirmationBegDate = params.get('confirmationBegDate', None)
    confirmationEndDate = params.get('confirmationEndDate', None)
    confirmationType    = params.get('confirmationType', 0)

    db = QtGui.qApp.db

    tableAction            = db.table('Action')
    tableActionTypeService = db.table('ActionType_Service')
    tableEvent             = db.table('Event')
    tablePerson            = db.table('vrbPerson')
    tableOrgStructure      = db.table('OrgStructure')
    tableActionType        = db.table('ActionType')
    tableAccountItem       = db.table('Account_Item')

    queryTable = tableAction

    queryTable = queryTable.leftJoin(tableEvent,        tableEvent['id'].eq(tableAction['event_id']))
    queryTable = queryTable.leftJoin(tableActionType,   tableActionType['id'].eq(tableAction['actionType_id']))
    queryTable = queryTable.leftJoin(tablePerson,       tablePerson['id'].eq(tableAction['person_id']))
    queryTable = queryTable.leftJoin(tableOrgStructure, tableOrgStructure['id'].eq(tablePerson['orgStructure_id']))

    existsCond = [tableActionTypeService['master_id'].eq(tableActionType['id'])]
    if fiananceId:
        existsCond.append(tableActionTypeService['finance_id'].eq(fiananceId))
    cond = [db.existsStmt(tableActionTypeService, existsCond),
            tableAction['deleted'].eq(0),
            tableEvent['deleted'].eq(0)]
    if begDate:
#        c = db.joinOr([tableAction['endDate'].dateGe(begDate), tableAction['endDate'].isNull()])
        cond.append(tableAction['endDate'].ge(begDate))
    if endDate:
#        c = db.joinOr([tableAction['begDate'].dateLe(endDate), tableAction['begDate'].isNull()])
        cond.append(tableAction['begDate'].lt(endDate.addDays(1)))
    if eventTypeId:
        cond.append(tableEvent['eventType_id'].eq(eventTypeId))
    if orgStructureId:
        cond.append(tableOrgStructure['id'].eq(orgStructureId))
#    if fiananceId:
#        cond.append(tableAction['finance_id'].eq(fiananceId))
    if confirmation:
        queryTable = queryTable.leftJoin(tableAccountItem, tableAccountItem['action_id'].eq(tableAction['id']))
        if confirmationType == 0:
            cond.append(tableAccountItem['id'].isNull())
        elif confirmationType == 1:
            cond.append(tableAccountItem['date'].isNotNull())
            cond.append(tableAccountItem['number'].ne(''))
        elif confirmationType == 2:
            cond.append(tableAccountItem['date'].isNotNull())
            cond.append(tableAccountItem['number'].ne(''))
            cond.append(tableAccountItem['refuseType_id'].isNull())
        elif confirmationType == 3:
            cond.append(tableAccountItem['date'].isNotNull())
            cond.append(tableAccountItem['number'].ne(''))
            cond.append(tableAccountItem['refuseType_id'].isNotNull())

        if confirmationBegDate:
            cond.append(tableAccountItem['date'].ge(confirmationBegDate))
        if confirmationEndDate:
            cond.append(tableAccountItem['date'].lt(confirmationEndDate.addDays(1)))

    fields = [
              tableAction['id'].alias('actionId'),
              tableOrgStructure['id'].alias('orgStructureId'),
              tableAction['amount'].name(),
              tableAction['office'].name(),
              tableActionType['serviceType'].name(),
              tablePerson['id'].alias('personId'),
              tablePerson['code'].alias('personCode'),
              tablePerson['name'].alias('personName'),
              tableEvent['client_id'].alias('clientId'),
              tableEvent['id'].alias('eventId')
             ]

    stmt = db.selectStmt(queryTable, fields, cond)
    return db.query(stmt)



class CReportActionsByServiceType(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Сводка об оказанных услугах')
        self._mapPersonPlan = {}
        self._mapOrgStructureToPersonDict = {}
        self._mapOrgStructureNameToId = {}
        self._mapPersonIdToEventIdList = {}
        self._mapPersonIdToInspectionCount = {}
        self._mapOrgStructureToNorm = {}
        self._totalNorm = 0
        self.resetHelpers()
        self._mapServiceTypeToCol = {
#                                        CActionServiceType.other             : 0,
                                        CActionServiceType.initialInspection : 1,
                                        CActionServiceType.reinspection      : 2,
                                        CActionServiceType.procedure         : 3,
                                        CActionServiceType.operation         : 4,
                                        CActionServiceType.research          : 5,
                                        CActionServiceType.healing           : 6,
#                                        CActionServiceType.prophylaxis       : 0,
#                                        CActionServiceType.anesthesia        : 0,
#                                        CActionServiceType.reanimation       : 0,
                                        CActionServiceType.labResearch       : 5,
                                    }
        self.orientation = CPageFormat.Landscape


    def resetHelpers(self):
        self._mapPersonPlan.clear()
        self._mapOrgStructureToPersonDict.clear()
        self._mapOrgStructureNameToId.clear()
        self._mapPersonIdToEventIdList.clear()
        self._mapPersonIdToInspectionCount.clear()
        self._mapOrgStructureToNorm.clear()
        self._totalNorm = 0


    def getSetupDialog(self, parent):
        result = CReportReportActionsByServiceTypeSetup(parent)
        result.setTitle(self.title())
        return result


    def getDescription(self, params):
        begDate                = params.get('begDate', None)
        endDate                = params.get('endDate', None)

        rows = []
        if begDate:
            rows.append(u'Начальная дата периода: %s'%forceString(begDate))
        if endDate:
            rows.append(u'Конечная дата периода: %s'%forceString(endDate))

        return rows


    def build(self, params):
        self.resetHelpers()
        query = selectData(params)
        self.structInfo(query, params)

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        tableColumns = [
                        ('=1',  [u'№', u'', u''], CReportBase.AlignRight),
                        ('3%',  [u'Код исполнителя', u'', u''], CReportBase.AlignLeft),
                        ('40%', [u'Имя исполнителя', u'', u''], CReportBase.AlignLeft),
                        ('3%',  [u'Обращения', u'', u''], CReportBase.AlignRight),
                        ('3%',  [u'Оказано услуг', u'В ЛПУ', u'Прочие'], CReportBase.AlignRight),
                        ('3%',  [u'', u'', u'Первичный осмотр'], CReportBase.AlignRight),
                        ('3%',  [u'', u'', u'Повторный осмотр'], CReportBase.AlignRight),
                        ('3%',  [u'', u'', u'Процедура'], CReportBase.AlignRight),
                        ('3%',  [u'', u'', u'Операция'], CReportBase.AlignRight),
                        ('3%',  [u'', u'', u'Исследование'], CReportBase.AlignRight),
                        ('3%',  [u'', u'', u'Лечение'], CReportBase.AlignRight),
                        ('3%',  [u'', u'На дому', u'Прочие'], CReportBase.AlignRight),
                        ('3%',  [u'', u'', u'Первичный осмотр'], CReportBase.AlignRight),
                        ('3%',  [u'', u'', u'Повторный осмотр'], CReportBase.AlignRight),
                        ('3%',  [u'', u'', u'Процедура'], CReportBase.AlignRight),
                        ('3%',  [u'', u'', u'Операция'], CReportBase.AlignRight),
                        ('3%',  [u'', u'', u'Исследование'], CReportBase.AlignRight),
                        ('3%',  [u'', u'', u'Лечение'], CReportBase.AlignRight),
                        ('3%',  [u'Норма', u'', u''], CReportBase.AlignRight),
                        ('3%',  [u'Норма исследований', u'', u''], CReportBase.AlignRight),
                        ('3%',  [u'% от нормы', u'', u''], CReportBase.AlignRight),
                       ]

        table = createTable(cursor, tableColumns)

        table.mergeCells(0, 0,  3, 1)
        table.mergeCells(0, 1,  3, 1)
        table.mergeCells(0, 2,  3, 1)
        table.mergeCells(0, 3,  3, 1)

        table.mergeCells(0, 4,  1, 14)
        table.mergeCells(1, 4,  1, 7)
        table.mergeCells(1, 11, 1, 7)
        table.mergeCells(0, 18, 3, 1)
        table.mergeCells(0, 19, 3, 1)
        table.mergeCells(0, 20, 3, 1)

        boldChars = QtGui.QTextCharFormat()
        boldChars.setFontWeight(QtGui.QFont.Bold)

        keyList = self._mapOrgStructureNameToId.keys()
        keyList.sort()
        rowShift = 2
        result = ['', '']+[0]*16+[u'', 0]
        resultLen = 0
        i = 1
        resultCount = 0
        lineLen = len(result)
        for key in keyList:
            orgStructureId = self._mapOrgStructureNameToId[key]
            i = table.addRow()
            table.setText(i, 1, key, charFormat=boldChars)
            table.mergeCells(i, 0, 1, 21)
            rowShift += 1
            personDict = self._mapOrgStructureToPersonDict[orgStructureId]
            orgStructureRezult = ['', '']+[0]*16+[u'', 0]
#            orgStructureRezultCount = 0
            orgStructureCount = 0
            for personId, personLine in personDict.items():
                personLine[2] = len(self._mapPersonIdToEventIdList[personId])
                count = self.printLine(personLine, table, rowShift, orgStructureRezult, personId, self._mapPersonIdToEventIdList)
                orgStructureCount += count
            resultCount += orgStructureCount
            self.printLine(orgStructureRezult, table, rowShift, result, orgStructureId, None, boldChars)
            resultLen = len(personDict.keys())
            table.mergeCells(i+resultLen+1, 0, 1, 3)
            self.setResultPercent(table,
                                  i+resultLen+1,
                                  lineLen,
                                  orgStructureCount,
                                  self._mapOrgStructureToNorm[orgStructureId][0],
                                  boldChars)
            rowShift += 1
        self.printLine(result, table, rowShift, None, None, None, boldChars)
        table.mergeCells(i+2+resultLen, 0, 1, 3)
        self.setResultPercent(table,
                              i+resultLen+2,
                              lineLen,
                              resultCount,
                              self._totalNorm,
                              boldChars)

        return doc


    def setResultPercent(self, table, row, column, count, norm, boldChars):
        percent = count*100/norm if norm else ''
        table.setText(row, column, percent, charFormat=boldChars)


    def printLine(self, values, table, rowShift, result, mapId, map, boldChars=None):
        i = table.addRow()
        if not boldChars:
            table.setText(i, 0, i-rowShift)
        for idx, value in enumerate(values):
            if not boldChars or idx > 1:
                if not boldChars or idx != 18:
                    table.setText(i, idx+1, value, charFormat=boldChars)
            if idx > 1 and result and idx != 18:
                result[idx] += value
        if not (map is None or boldChars):
            count = self._mapPersonIdToInspectionCount.get(mapId, 0)
            norm  = values[-3]
            percent = count*100/norm if norm else ''
            table.setText(i, len(values), percent, charFormat=boldChars)
            return count
        return 0


    def structInfo(self, query, params):
        while query.next():
            record = query.record()

#            actionId = forceRef(record.value('actionId'))
            orgStructureId = forceRef(record.value('orgStructureId'))
            amount = forceDouble(record.value('amount'))
            serviceType = forceInt(record.value('serviceType'))
            personId = forceRef(record.value('personId'))
            personCode = forceString(record.value('personCode'))
            personName = forceString(record.value('personName')) if personId else u' Врач не известен'
            office = forceString(record.value('office'))
#            clientId = forceRef(record.value('clientId'))
            eventId = forceRef(record.value('eventId'))

            personDict = self._mapOrgStructureToPersonDict.setdefault(orgStructureId, {})
            if not bool(personDict):
                orgStructureName = getOrgStructureFullName(orgStructureId) if orgStructureId else u' Не определено'
                self._mapOrgStructureNameToId[orgStructureName] = orgStructureId
            personLine = personDict.setdefault(personId, [personCode, personName]+[0]*16+[u'', 0])

            dataPoint = 3
            for c in (u'д', u'Д'):
                if c in office:
                    dataPoint = 10

            col = self._mapServiceTypeToCol.get(serviceType, 0)

            personLine[dataPoint+col] += amount
            if serviceType in (CActionServiceType.initialInspection,
                               CActionServiceType.reinspection):
                result = self._mapPersonIdToInspectionCount.get(personId, 0)
                self._mapPersonIdToInspectionCount[personId] = result+1

            self._setPersonPlan(personId, params, personLine)
            self._setEventId(eventId, personId)

            result = self._mapOrgStructureToNorm.setdefault(orgStructureId, [0, []])
            if personId not in result[1]:
                result[1].append(personId)
                result[0] += personLine[17]

                self._totalNorm += personLine[17]


    def _setEventId(self, eventId, personId):
        result = self._mapPersonIdToEventIdList.setdefault(personId, [eventId])
        if eventId not in result:
            result.append(eventId)


    def _setPersonPlan(self, personId, params, personLine):
        key = personId
        plan = self._mapPersonPlan.get(key, None)
        if plan is None:
            begDate        = params.get('begDate', None)
            endDate        = params.get('endDate', None)
            db = QtGui.qApp.db
            tableSchedule = db.table('Schedule')
            cond = [tableSchedule['deleted'].eq(0),
                    tableSchedule['appointmentType'].inlist([CSchedule.atAmbulance, CSchedule.atHome]),
                    tableSchedule['date'].ge(begDate),
                    tableSchedule['date'].le(endDate),
                    tableSchedule['person_id'].eq(personId),
                   ]
            plan = forceInt(db.getSum(tableSchedule, 'capacity', cond))
            self._mapPersonPlan[key] = plan
        personLine[17] = plan



class CReportReportActionsByServiceTypeSetup(QtGui.QDialog, Ui_ReportActionsByServiceTypeSetupDialog):
    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cmbEventType.setTable('EventType', addNone=True)
        self.cmbFinance.setTable('rbFinance', addNone=True)


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        date = QDate.currentDate().addDays(-3)
        self.edtBegDate.setDate(params.get('begDate', firstMonthDay(date)))
        self.edtEndDate.setDate(params.get('endDate', lastMonthDay(date)))
        self.cmbEventType.setValue(params.get('eventTypeId', None))
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))
        self.cmbFinance.setValue(params.get('fiananceId', None))
        self.chkConfirmation.setChecked(params.get('confirmation', False))
        self.edtConfirmationBegDate.setDate(params.get('confirmationBegDate', firstMonthDay(date)))
        self.edtConfirmationEndDate.setDate(params.get('confirmationEndDate', lastMonthDay(date)))
        self.cmbConfirmationType.setCurrentIndex(params.get('confirmationType', 0))


    def params(self):
        return dict(
                    begDate        = self.edtBegDate.date(),
                    endDate        = self.edtEndDate.date(),
                    eventTypeId    = self.cmbEventType.value(),
                    orgStructureId = self.cmbOrgStructure.value(),
                    fiananceId     = self.cmbFinance.value(),
                    confirmation        = self.chkConfirmation.isChecked(),
                    confirmationType    = self.cmbConfirmationType.currentIndex(),
                    confirmationBegDate = self.edtConfirmationBegDate.date(),
                    confirmationEndDate = self.edtConfirmationEndDate.date(),
                   )
