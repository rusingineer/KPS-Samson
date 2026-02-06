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
from PyQt4 import QtCore
from PyQt4.QtCore import QDate

from library.Utils      import forceString, forceInt
from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable
from Reports.Utils      import dateRangeAsStr
from Orgs.Utils         import getOrgStructureFullName, getOrgStructureDescendants
from library.Utils      import formatDate

from Reports.PlannedClientInvoiceNomenclaturesReport import CNomenclatureReportDialog


class CClientNomenclatureActionReport(CReport):
    def __init__(self, parent = None):
        CReport.__init__(self, parent)
        self.setTitle(u'Отчет о назначенных ЛСиИМН в рамках госпитализации')

    def getSetupDialog(self, parent):
        result = CNomenclatureReportDialog(parent)
        result.setDatePeriodVisible(True)
        result.setDatesVisible(True)
        result.setMonthVisible(False)
        result.setClientIdVisible(True)
        result.setOrgStructureVisible(True)
        result.setSignaVisible(False)
        result.setNomenclatureVisible(True)
        result.setSupplierVisible(False)
        result.setSupplierOrgVisible(False)
        result.setReceiverVisible(False)
        result.setReceiverPersonVisible(False)
        result.setFinanceVisible(False)
        result.setOnlyExists(False)
        result.edtBegTime.setVisible(False)
        result.edtEndTime.setVisible(False)
        return result

    def build(self, params):
        tableColumns = [
            ('5%', [u'№ п/п'], CReportBase.AlignRight),
            ('20%', [u'ФИО'], CReportBase.AlignLeft),
            ('10%', [u'Дата поступления'], CReportBase.AlignLeft),
            ('10%', [u'Дата выписки'], CReportBase.AlignLeft),
            ('15%', [u'ЛСиИМН'], CReportBase.AlignLeft),
            ('15%', [u'Дата начала приема'], CReportBase.AlignLeft),
            ('15%', [u'Дата окончания приема'], CReportBase.AlignLeft),
            ('10%', [u'Кол-во израсходованного ЛСиИМН (уч.ед)'], CReportBase.AlignRight),
        ]

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()

        table = createTable(cursor, tableColumns)

        query = self.getQuery(params)

        i=0
        row = 0
        rowNum=1
        prevClient = None
        prevSetDate = None
        while query.next():
            record = query.record()
            clientFullName = forceString(record.value('clientFullName'))
            setDate = formatDate(record.value('setDate'))
            execDate = formatDate(record.value('execDate'))
            nomenclatureName = forceString(record.value('nomenclatureName'))
            minStatus = forceInt(record.value('minStatus'))
            maxStatus = forceInt(record.value('maxStatus'))
            lastStatus = forceInt(record.value('lastStatus'))
            begDate = formatDate(record.value('begDate'))
            endDate = formatDate(record.value('endDate'))
            qnt = forceString(record.value('qnt'))

            if minStatus == 3 and maxStatus==3:
                pass
            else:
                row = table.addRow()
                table.setText(row, 4, nomenclatureName)
                table.setText(row, 5, begDate)
                table.setText(row, 6, endDate if (lastStatus==2 or (minStatus!=3 and maxStatus==3)) else u'')
                table.setText(row, 7, qnt)
                if (clientFullName==prevClient and setDate==prevSetDate):
                    i+=1
                else:
                    if i != 0:
                        table.mergeCells(row-i-1, 0, i+1, 1)
                        table.mergeCells(row-i-1, 1, i+1, 1)
                        table.mergeCells(row-i-1, 2, i+1, 1)
                        table.mergeCells(row-i-1, 3, i+1, 1)
                        i = 0

                    table.setText(row, 0, rowNum)
                    table.setText(row, 1, clientFullName)
                    table.setText(row, 2, setDate)
                    table.setText(row, 3, execDate)
                    rowNum += 1
                prevClient = clientFullName
                prevSetDate = setDate

        if i != 0:
            table.mergeCells(row-i, 0, i+1, 1)
            table.mergeCells(row-i, 1, i+1, 1)
            table.mergeCells(row-i, 2, i+1, 1)
            table.mergeCells(row-i, 3, i+1, 1)

        return doc

    def getQuery(self, params):
        datePeriod = params.get('datePeriod')
        begDate = params.get('begDate')
        endDate = params.get('endDate')
        nomenclatureId = params.get('nomenclatureId')
        orgStructureId = params.get('orgStructureId')
        clientId = params.get('clientId')

        db = QtGui.qApp.db
        tableStockMotion = db.table('StockMotion')
        tableStockMotionItem = db.table('StockMotion_Item')
        tableNomenclature = db.table('rbNomenclature')
        tableEvent = db.table('Event')
        tableClient = db.table('Client')
        tableAction = db.table('Action')
        tableOrgStructure = db.table('OrgStructure')
        tableActionType = db.table('ActionType')
        tableActionProperty = db.table('ActionProperty')
        tableActionPropertyType = db.table('ActionPropertyType')
        tableActionPropertyNomenclature = db.table('ActionProperty_rbNomenclature')

        cond = [
            tableActionType['isNomenclatureExpense'].eq('1'),
            tableNomenclature['name'].isNotNull(),
            tableEvent['execDate' if datePeriod else 'setDate'].dateGt(begDate),
            tableStockMotion['deleted'].eq(0), 
            db.joinOr([tableEvent['execDate' if datePeriod else 'setDate'].lt(endDate.addDays(1)), tableEvent['execDate' if datePeriod else 'setDate'].isNull()])
        ]

        groupAndOrder = u'Event.id, Action.actionType_id, Action.plannedEndDate, Action.directionDate, rbNomenclature.id ORDER BY Client.lastName , Event.setDate , rbNomenclature.name'

        queryTable = tableEvent
        queryTable = queryTable.leftJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
        queryTable = queryTable.leftJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
        queryTable = queryTable.leftJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
        queryTable = queryTable.leftJoin(tableActionProperty, tableActionProperty['action_id'].eq(tableAction['id']))
        queryTable = queryTable.leftJoin(tableActionPropertyType, tableActionPropertyType['id'].eq(tableActionProperty['type_id']))
        queryTable = queryTable.leftJoin(tableActionPropertyNomenclature, tableActionPropertyNomenclature['id'].eq(tableActionProperty['id']))
        queryTable = queryTable.leftJoin(tableStockMotion, tableStockMotion['id'].eq(tableAction['stockMotion_id']))
        queryTable = queryTable.leftJoin(tableStockMotionItem, tableStockMotionItem['master_id'].eq(tableStockMotion['id']))
        queryTable = queryTable.leftJoin(tableNomenclature, tableNomenclature['id'].eq(tableActionPropertyNomenclature['value']))
        queryTable = queryTable.leftJoin(tableOrgStructure, tableOrgStructure['id'].eq(tableStockMotion['supplier_id']))


        if nomenclatureId:
            cond.append(tableStockMotionItem['nomenclature_id'].eq(nomenclatureId))
        if orgStructureId:
            cond.append(db.joinOr([tableOrgStructure['id'].inlist(getOrgStructureDescendants(orgStructureId)), tableOrgStructure['id'].isNull()]))
        if clientId:
            cond.append(tableClient['id'].eq(clientId))

        cols = [
            'CONCAT_WS(" ", Client.lastName, Client.firstName, Client.patrName) as clientFullName',
           tableEvent['setDate'],
           tableEvent['execDate'],
           tableNomenclature['name'].alias('nomenclatureName'),
           tableAction['begDate'],
           'MIN(DATE(Action.begDate)) as begDate',
           'MAX(DATE(Action.endDate)) as endDate',
            '''(SELECT
                SUM((SELECT
                            value
                        FROM
                            ActionProperty_Double
                                LEFT JOIN
                            ActionProperty AS APP ON APP.id = ActionProperty_Double.id
                        WHERE
                            APP.action_id = AQ.id))
            FROM
                Action AS AQ
                    LEFT JOIN
                ActionProperty AS APQ ON APQ.action_id = AQ.id
                    LEFT JOIN
                ActionProperty_rbNomenclature AS APNQ ON APNQ.id = APQ.id
                    LEFT JOIN
                rbNomenclature AS RBNQ ON RBNQ.`id` = APNQ.`value`
            WHERE
                AQ.event_id = Event.id
                    AND RBNQ.name = rbNomenclature.name
                    AND DATE(AQ.plannedEndDate) = DATE(Action.plannedEndDate)
                    AND DATE(AQ.directionDate) = DATE(Action.directionDate)
                    AND AQ.status = 2) AS qnt''',
            'MIN(Action.status) as minStatus',
            'MAX(Action.status) as maxStatus',
            '''(SELECT
                ASt.status
            FROM
                Action AS ASt
                    LEFT JOIN
                ActionProperty AS APSt ON APSt.action_id = ASt.id
                    LEFT JOIN
                ActionProperty_rbNomenclature AS APNSt ON APNSt.id = APSt.id
                    LEFT JOIN
                rbNomenclature AS RBNSt ON RBNSt.`id` = APNSt.`value`
            WHERE
                DATE(ASt.plannedEndDate) = DATE(Action.plannedEndDate)
                    AND ASt.directionDate = Action.directionDate
                    AND RBNSt.name = rbNomenclature.name
            ORDER BY ASt.begDate DESC
            LIMIT 1) AS lastStatus'''
        ]

        stmt = db.selectStmtGroupBy(queryTable, cols, cond, groupAndOrder)
        query = db.query(stmt)
        return query

    def dumpParams(self, cursor, params):
        description = []
        db = QtGui.qApp.db
        datePeriod = params.get('datePeriod', 0)
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        nomenclatureId = params.get('nomenclatureId', None)
        orgStructureId = params.get('orgStructureId', None)
        clientId = params.get('clientId', None)

        description.append(u'Период по дате: %s' %(u'окончания госпитализации' if datePeriod else u'начала госпитализации'))
        if begDate and endDate:
            description.append(dateRangeAsStr(u'За период', begDate, endDate))
        if nomenclatureId:
            description.append(u'ЛСиИМН: %s'%(forceString(db.translate('rbNomenclature', 'id', nomenclatureId, 'name'))))
        if orgStructureId:
            description.append(u'Подразделение: ' + getOrgStructureFullName(orgStructureId))
        if clientId:
            description.append(u'Код пациента: %s' %clientId)

        description.append(u'Отчёт составлен: '+forceString(QtCore.QDateTime.currentDateTime()))
        columns = [ ('100%', [], CReportBase.AlignLeft) ]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
