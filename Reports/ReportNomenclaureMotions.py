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

from library.Utils      import forceString

from Orgs.Utils         import getOrgStructureFullName, getOrganisationShortName
from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable
from Reports.Utils import dateRangeAsStr
from Reports.PlannedClientInvoiceNomenclaturesReport import CNomenclatureReportDialog


class CReportNomenclaureMotions(CReport):
    def __init__(self, parent = None):
        CReport.__init__(self, parent)
        self.setTitle(u'Отчет о поступлении и передаче ЛС')

    def getSetupDialog(self, parent):
        result = CNomenclatureReportDialog(parent)
        result.setDatesVisible(True)
        result.setMonthVisible(False)
        result.setDatesOptionVisible(False)
        result.setMonthOptionVisible(False)
        result.setClientIdVisible(False)
        result.setOrgStructureVisible(False)
        result.setSignaVisible(False)
        result.setNomenclatureVisible(False)
        result.setSupplierVisible(True)
        result.setSupplierOrgVisible(True)
        result.setReceiverVisible(True)
        result.setReceiverPersonVisible(False)
        result.setFinanceVisible(True)
        result.setOnlyExists(True)
        result.edtBegTime.setVisible(False)
        result.edtEndTime.setVisible(False)
        return result

    def dumpParams(self, cursor, params):
        description = []
        db = QtGui.qApp.db
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        nomenclatureId = params.get('nomenclatureId', None)
        supplierId = params.get('supplierId', None)
        supplierOrgId = params.get('supplierOrgId', None)
        receiverId = params.get('receiverId', None)
        financeId = params.get('financeId', None)

        if begDate and endDate:
            description.append(dateRangeAsStr(u'За период', begDate, endDate))
        if nomenclatureId:
            description.append(u'ЛС: %s'%(forceString(db.translate('rbNomenclature', 'id', nomenclatureId, 'name'))))
        if supplierId:
            description.append(u'Поставщик: ' + getOrgStructureFullName(supplierId))
        if supplierOrgId:
            description.append(u'Внешний поставщик: ' + getOrganisationShortName(supplierOrgId))
        if receiverId:
            description.append(u'Получатель: ' + getOrgStructureFullName(receiverId))
        if financeId:
            description.append(u'Тип финансирования: %s'%(forceString(db.translate('rbFinance', 'id', financeId, 'name'))))

        description.append(u'отчёт составлен: '+forceString(QtCore.QDateTime.currentDateTime()))
        columns = [ ('100%', [], CReportBase.AlignLeft) ]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()


    def build(self, params):
        tableColumns = [
            ('20%', [u'Наименование ЛС'], CReportBase.AlignLeft),
            ('15%', [u'Ед. изм.'], CReportBase.AlignLeft),
            ('20%', [u'Поставщик'], CReportBase.AlignLeft),
            ('20%', [u'Получатель'], CReportBase.AlignLeft),
            ('15%', [u'Тип финансирования'], CReportBase.AlignLeft),
            ('10%', [u'Кол-во'], CReportBase.AlignRight),
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

        while query.next():
            record = query.record()
            nomenclatureName = forceString(record.value('nomenclatureName'))
            unit = forceString(record.value('unit'))
            supplier = forceString(record.value('supplier'))
            receiver = forceString(record.value('receiver'))
            finance = forceString(record.value('finance'))
            qnt = forceString(record.value('qnt'))

            row = table.addRow()
            table.setText(row, 0, nomenclatureName)
            table.setText(row, 1, unit)
            table.setText(row, 2, supplier)
            table.setText(row, 3, receiver)
            table.setText(row, 4, finance)
            table.setText(row, 5, qnt)

        return doc

    def getQuery(self, params):
        db = QtGui.qApp.db
        tableStockMotion = db.table('StockMotion')
        tableStockMotionItem = db.table('StockMotion_Item')
        tableRbUnit = db.table('rbUnit')
        tableRbFinance = db.table('rbFinance')
        tableSupplier = db.table('OrgStructure').alias('Supplier')
        tableReceiver = db.table('OrgStructure').alias('Receiver')
        tableOrganisation = db.table('Organisation')
        tableNomenclature = db.table('rbNomenclature')
        cond = [
            tableNomenclature['id'].isNotNull(),
            tableStockMotion['type'].eq(0)
        ]

        queryTable = tableStockMotion
        queryTable = queryTable.leftJoin(tableStockMotionItem, tableStockMotionItem['master_id'].eq(tableStockMotion['id']))
        queryTable = queryTable.leftJoin(tableNomenclature, tableNomenclature['id'].eq(tableStockMotionItem['nomenclature_id']))
        queryTable = queryTable.leftJoin(tableRbUnit, tableRbUnit['id'].eq(tableStockMotionItem['unit_id']))
        queryTable = queryTable.leftJoin(tableRbFinance, tableRbFinance['id'].eq(tableStockMotionItem['finance_id']))
        queryTable = queryTable.leftJoin(tableSupplier, tableSupplier['id'].eq(tableStockMotion['supplier_id']))
        queryTable = queryTable.leftJoin(tableReceiver, tableReceiver['id'].eq(tableStockMotion['receiver_id']))
        queryTable = queryTable.leftJoin(tableOrganisation, tableOrganisation['id'].eq(tableStockMotion['supplierOrg_id']))

        begDate = params.get('begDate')
        endDate = params.get('endDate')
        nomenclatureId = params.get('nomenclatureId')
        supplierId = params.get('supplierId')
        supplierOrgId = params.get('supplierOrgId')
        receiverId = params.get('receiverId')
        financeId = params.get('financeId')

        if begDate:
            cond.append(tableStockMotion['date'].ge(begDate))
        if endDate:
            cond.append(tableStockMotion['date'].lt(endDate.addDays(1)))
        if nomenclatureId:
            cond.append(tableStockMotionItem['nomenclature_id'].eq(nomenclatureId))
        if supplierId:
            cond.append(tableSupplier['id'].eq(supplierId))
        if receiverId:
            cond.append(tableReceiver['id'].eq(receiverId))
        if supplierOrgId:
            cond.append(tableOrganisation['id'].eq(supplierOrgId))
        if financeId:
            cond.append(tableStockMotionItem['finance_id'].eq(financeId))

        cols = [
            tableNomenclature['name'].alias('nomenclatureName'),
            tableRbUnit['name'].alias('unit'),
            '''    IF(Supplier.id IS NOT NULL,
                        Supplier.name,
                        Organisation.fullName) AS supplier''',
            tableReceiver['name'].alias('receiver'),
            tableRbFinance['name'].alias('finance'),
            '''SUM(StockMotion_Item.qnt) as qnt'''
        ]

        stmt = db.selectStmtGroupBy(queryTable, cols, cond, u'rbNomenclature.id, rbUnit.id, Supplier.id, Receiver.id, finance_id ORDER BY rbNomenclature.name')
        query = db.query(stmt)
        return query
