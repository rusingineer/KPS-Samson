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

from library.Utils      import forceString, forceInt,  forceDouble

from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable
from Orgs.Utils         import getOrgStructureFullName
from library.Utils import formatDate

from Reports.PlannedClientInvoiceNomenclaturesReport import CNomenclatureReportDialog


class CNomenclatureBook(CReport):
    def __init__(self, parent = None):
        CReport.__init__(self, parent)
        self.setTitle(u'Книга учета материальных ценностей')

    def getSetupDialog(self, parent):
        result = CNomenclatureReportDialog(parent)
        result.setDatesVisible(True)
        result.setMonthVisible(False)
        result.setClientIdVisible(False)
        result.setOrgStructureVisible(True)
        result.setSignaVisible(False)
        result.setNomenclatureVisible(True)
        result.setSupplierVisible(False)
        result.setSupplierOrgVisible(False)
        result.setReceiverVisible(False)
        result.setFinanceVisible(False)
        result.setOnlyExists(False)
        result.edtBegTime.setVisible(False)
        result.edtEndTime.setVisible(False)
        result.setReceiverPersonVisible(True)
        return result

    def build(self, params):
        tableColumns1 = [
            ('10%', [u'',u'Склад'], CReportBase.AlignLeft),
            ('5%', [u'',u'Стеллаж'], CReportBase.AlignLeft),
            ('5%', [u'',u'Ячейка'], CReportBase.AlignLeft),
            ('10%', [u'Единица измерения', u'Наименование'], CReportBase.AlignLeft),
            ('10%', [u'',u'Код'], CReportBase.AlignLeft),
            ('10%', [u'',u'Цена'], CReportBase.AlignLeft),
            ('10%', [u'',u'Марка'], CReportBase.AlignLeft),
            ('10%', [u'',u'Сорт'], CReportBase.AlignLeft),
            ('10%', [u'',u'Профиль'], CReportBase.AlignLeft),
            ('10%', [u'',u'Размер'], CReportBase.AlignLeft),
            ('10%', [u'',u'Норма запаса'], CReportBase.AlignLeft),
        ]

        tableColumns2 = [
            ('5%', [u'', u'№ п/п'], CReportBase.AlignLeft),
            ('10%', [u'', u'Дата записи'], CReportBase.AlignRight),
            ('10%', [u'Документ', u'Дата'], CReportBase.AlignRight),
            ('10%', [u'', u'Номер'], CReportBase.AlignLeft),
            ('20%', [u'', u'От кого получено (кому отпущено)'], CReportBase.AlignLeft),
            ('10%', [u'', u'Приход'], CReportBase.AlignRight),
            ('10%', [u'', u'Расход'], CReportBase.AlignRight),
            ('10%', [u'', u'Остаток'], CReportBase.AlignRight),
            ('15%', [u'', u'Контроль (подпись и дата)'], CReportBase.AlignLeft),
        ]

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        self.getCaption(cursor, params, self.title())
        cursor.insertBlock()

        cursor.setCharFormat(CReportBase.ReportBody)

        nomenclatureId = params.get('nomenclatureId')

        table = createTable(cursor, tableColumns1)

        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 2, 1)
        table.mergeCells(0, 2, 2, 1)
        table.mergeCells(0, 3, 1, 2)
        table.mergeCells(0, 4, 1, 1)
        table.mergeCells(0, 5, 2, 1)
        table.mergeCells(0, 6, 2, 1)
        table.mergeCells(0, 7, 2, 1)
        table.mergeCells(0, 8, 2, 1)
        table.mergeCells(0, 9, 2, 1)
        table.mergeCells(0, 10, 2, 1)

        defaultStockUnitId = QtGui.qApp.db.translate('rbNomenclature', 'id', nomenclatureId, 'defaultStockUnit_id')

        row = table.addRow()
        unitName = forceString(QtGui.qApp.db.translate('rbUnit', 'id', defaultStockUnitId, 'name'))
        unitCode = forceString(QtGui.qApp.db.translate('rbUnit', 'id', defaultStockUnitId, 'code'))
        table.setText(row, 3, unitName)
        table.setText(row, 4, unitCode)

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertBlock()

        cursor.insertText(u'Наименование материала: ' + forceString(QtGui.qApp.db.translate('rbNomenclature', 'id', nomenclatureId, 'name')))

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertBlock()

        table = createTable(cursor, tableColumns2)
        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 2, 1)
        table.mergeCells(0, 2, 1, 2)
        table.mergeCells(0, 3, 1, 1)
        table.mergeCells(0, 4, 2, 1)
        table.mergeCells(0, 5, 2, 1)
        table.mergeCells(0, 6, 2, 1)
        table.mergeCells(0, 7, 2, 1)
        table.mergeCells(0, 8, 2, 1)

        query = self.getQuery(params)

        i=0
        row = 0
        orgStructureId = params.get('orgStructureId')
        if not orgStructureId:
            orgStructureId =  QtGui.qApp.currentOrgStructureId()
        remainings = self.getRemainings(params)
        while query.next():
            record = query.record()
            date = formatDate(record.value('date'))
            number = forceString(record.value('number'))
            supplierOrg = forceString(record.value('supplierOrg'))
            supplier = forceString(record.value('supplier'))
            receiver = forceString(record.value('receiver'))
            supplierId = forceInt(record.value('supplier_id'))
            receiverId = forceInt(record.value('receiver_id'))
            qnt = forceDouble(record.value('qnt'))

            if qnt:
                row = table.addRow()
                i+=1
                table.setText(row, 0, i)
                table.setText(row, 1, date)
                table.setText(row, 2, date)
                table.setText(row, 3, number)
                table.setText(row, 4, supplierOrg + u' / ' + receiver if supplierOrg!=u'' and receiver !=u'' else  supplier + u' / ' + receiver)
                table.setText(row, 5, qnt if (receiverId==orgStructureId) else u'')
                table.setText(row, 6, qnt if (supplierId==orgStructureId) else u'')
                if supplierId==orgStructureId:
                    remainings = remainings - qnt
                elif receiverId==orgStructureId:
                    remainings = remainings + qnt
                table.setText(row, 7, remainings)

        return doc


    def getCaption(self, cursor, params, title, cols = 1):
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        orgStructureId = params.get('orgStructureId', None)
        receiverPersonId = params.get('receiverPersonId',  None)
        orgId = QtGui.qApp.currentOrgId()
        orgName = u''
        OKPO = u''

        boldChars = QtGui.QTextCharFormat()
        boldChars.setFontWeight(QtGui.QFont.Bold)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.setCharFormat(CReportBase.ReportBody)

        if orgId:
            record = QtGui.qApp.db.getRecordEx('Organisation', 'shortName, OKPO', 'id=%s AND deleted = 0'%(str(orgId)))
            if record:
                orgName = forceString(record.value('shortName'))
                OKPO = forceString(record.value('OKPO'))
        orgStructureId = params.get('orgStructureId', None)
        underCaptionList = []
        underCaptionList.append(u'Учреждение: ' + orgName)
        if orgStructureId:
            underCaptionList.append(u'Структурное подразделение: ' + forceString(getOrgStructureFullName(orgStructureId)))
        else:
            underCaptionList.append(u'Структурное подразделение: ЛПУ')
        if receiverPersonId:
            underCaptionList.append(u'Материально ответственное лицо: ' + forceString(forceString(QtGui.qApp.db.translate('vrbPerson', 'id', receiverPersonId, 'name'))))

        width = "%i%%"%(70-cols)
        columns = [(width, [], CReportBase.AlignLeft)]
        for i in range(cols-1):
            columns.append(('1%', [], CReportBase.AlignLeft))
        columns.append(('30%', [], CReportBase.AlignLeft))
        table = createTable(cursor, columns, headerRowCount=4, border=0, cellPadding=2, cellSpacing=0)
        table.mergeCells(0, 0, 1, cols)
        table.setText(0, 0, u'')
        table.setText(0, cols, u'Форма по ОКУД  0504042')
        table.mergeCells(1, 0, 1, cols)
        table.setText(1, 0, u'')
        table.setText(1, cols, u'Дата открытия  ' +  forceString(begDate))
        table.mergeCells(2, 0, 1, cols)
        table.setText(2, 0, u'')
        table.setText(2, cols, u'Дата закрытия  ' + forceString(endDate))
        table.mergeCells(3, 0, 1, cols)
        table.setText(3, 0, u'')
        table.setText(3, cols, u'по ОКПО  ' + OKPO)

        cursor.movePosition(QtGui.QTextCursor.End)

        table2 = createTable(cursor, columns, headerRowCount=len(underCaptionList), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(underCaptionList):
            table2.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()


    def getQuery(self, params):
        begDate = params.get('begDate')
        endDate = params.get('endDate')
        nomenclatureId = params.get('nomenclatureId')
        orgStructureId = params.get('orgStructureId')
        receiverPersonId = params.get('receiverPersonId')
        defaultOrgStructureId =  QtGui.qApp.currentOrgStructureId()

        db = QtGui.qApp.db
        tableStockMotion = db.table('StockMotion')
        tableStockMotionItem = db.table('StockMotion_Item')
        tablePerson = db.table('Person')
        tableOrgStructureS = db.table('OrgStructure').alias('OSS')
        tableOrgStructureR = db.table('OrgStructure').alias('OSR')
        tableOrg = db.table('Organisation')

        cond = [
            tableStockMotion['date'].ge(begDate),
            tableStockMotion['date'].lt(endDate.addDays(1)),
            tableStockMotion['type'].eq(0),
            tableStockMotion['deleted'].eq(0)
        ]

        queryTable = tableStockMotion
        queryTable = queryTable.leftJoin(tableStockMotionItem, db.joinAnd([tableStockMotionItem['master_id'].eq(tableStockMotion['id']), tableStockMotionItem['deleted'].eq(0)]))
        queryTable = queryTable.leftJoin(tableOrg, tableOrg['id'].eq(tableStockMotion['supplierOrg_id']))
        queryTable = queryTable.leftJoin(tableOrgStructureS, tableOrgStructureS['id'].eq(tableStockMotion['supplier_id']))
        queryTable = queryTable.leftJoin(tableOrgStructureR, tableOrgStructureR['id'].eq(tableStockMotion['receiver_id']))
        queryTable = queryTable.leftJoin(tablePerson, tablePerson['id'].eq(tableStockMotion['receiverPerson_id']))

        if nomenclatureId:
            cond.append(tableStockMotionItem['nomenclature_id'].eq(nomenclatureId))
        if orgStructureId:
            cond.append(db.joinOr([tableOrgStructureR['id'].eq(orgStructureId), tableOrgStructureS['id'].eq(orgStructureId)]))
        else:
            cond.append(db.joinOr([tableOrgStructureR['id'].eq(defaultOrgStructureId), tableOrgStructureS['id'].eq(defaultOrgStructureId)]))
        if receiverPersonId:
            cond.append(tablePerson['id'].eq(receiverPersonId))

        cols = [tableStockMotion['date'],
                    tableStockMotion['number'],
                    tableOrg['shortName'].alias('supplierOrg'),
                    tableOrgStructureS['name'].alias('supplier'),
                    tableStockMotion['supplier_id'],
                    tableOrgStructureR['name'].alias('receiver'),
                    tableStockMotion['receiver_id'],
                    tableStockMotionItem['qnt']
        ]

        stmt = db.selectStmt(queryTable, cols, cond)
        query = db.query(stmt)
        return query


    def getRemainings(self, params):
        begDate = params.get('begDate')
        nomenclatureId = params.get('nomenclatureId')
        orgStructureId = params.get('orgStructureId')
        defaultOrgStructureId =  QtGui.qApp.currentOrgStructureId()
        debCond = []
        creCond = []

        db = QtGui.qApp.db
        tableStockTrans = db.table('StockTrans')

        if nomenclatureId:
            debCond.append(tableStockTrans['debNomenclature_id'].eq(nomenclatureId))
            creCond.append(tableStockTrans['creNomenclature_id'].eq(nomenclatureId))
        if begDate:
            debCond.append(tableStockTrans['date'].lt(begDate.addDays(1)))
            creCond.append(tableStockTrans['date'].ge(begDate))
        if orgStructureId:
            debCond.append(tableStockTrans['debOrgStructure_id'].eq(orgStructureId))
            creCond.append(tableStockTrans['creOrgStructure_id'].eq(orgStructureId))
        else:
            debCond.append(tableStockTrans['debOrgStructure_id'].eq(defaultOrgStructureId))
            creCond.append(tableStockTrans['creOrgStructure_id'].eq(defaultOrgStructureId))

        stmt = u'''
                SELECT
                    IF(SUM(T.qnt), SUM(T.qnt), 0) AS `qnt`
                FROM
                (
                SELECT
                       sum(StockTrans.qnt)           AS `qnt`
                FROM StockTrans
                WHERE %(debCond)s
                UNION
                SELECT
                       -sum(StockTrans.qnt)          AS `qnt`
                FROM StockTrans
                WHERE %(creCond)s
                ) AS T

    ''' % {
        'debCond' : db.joinAnd(debCond),
        'creCond' : db.joinAnd(creCond)
        }

        query = db.query(stmt)
        if query.next():
            qnt = forceDouble(query.record().value('qnt'))
            return qnt
        return 0
