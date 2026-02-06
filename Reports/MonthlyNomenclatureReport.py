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

from library.Utils      import (
    forceDate, forceRef, forceString, forceDouble
    )
from Orgs.Utils         import getOrgStructureName
from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable
from Reports.Utils            import dateRangeAsStr

from Reports.PlannedClientInvoiceNomenclaturesReport import CNomenclatureReportDialog


def _selectData(params):
    monthChecked = params['monthChecked']
    if monthChecked:
        date = params['monthOption']
        begDate = QDate(date.year(), date.month(), 1)
        endDate = QDate(date.year(), date.month(), date.daysInMonth())
    else:
        date = QDate(params['begDateOption'])
        begDate = QDate(params['begDateOption'])
        endDate = QDate(params['endDateOption'])

    orgStructureId = params.get('orgStructureId')
    financeId = params.get('financeId')

    db = QtGui.qApp.db
    table = db.table('StockTrans')

    debCond = [
        table['date'].lt(endDate.addDays(1))
    ]
    creCond = [
        table['date'].lt(endDate.addDays(1))
    ]

    if orgStructureId:
        debCond.append(table['debOrgStructure_id'].eq(orgStructureId))
        creCond.append(table['creOrgStructure_id'].eq(orgStructureId))

    if financeId:
        debCond.append(table['debFinance_id'].eq(financeId))
        creCond.append(table['creFinance_id'].eq(financeId))

    nomenclatureClassId = params.get('nomenclatureClassId')
    nomenclatureKindId = params.get('nomenclatureKindId')
    nomenclatureTypeId = params.get('nomenclatureTypeId')
    joinNomenclatureFilter = u''''''
    if nomenclatureClassId:
        joinNomenclatureFilter = u''' INNER JOIN rbNomenclatureType ON (rbNomenclature.type_id = rbNomenclatureType.id %s)
                                      INNER JOIN rbNomenclatureKind ON (rbNomenclatureType.kind_id = rbNomenclatureKind.id %s)
                                      INNER JOIN rbNomenclatureClass ON (rbNomenclatureKind.class_id = rbNomenclatureClass.id AND rbNomenclatureClass.id = %s)
        '''%((u'AND rbNomenclatureType.id = %s'%(nomenclatureTypeId)) if nomenclatureTypeId else u'',
             (u'AND rbNomenclatureKind.id = %s'%(nomenclatureKindId)) if nomenclatureKindId else u'',
              nomenclatureClassId)
    elif nomenclatureKindId:
        joinNomenclatureFilter = u''' INNER JOIN rbNomenclatureType ON (rbNomenclature.type_id = rbNomenclatureType.id %s)
                                      INNER JOIN rbNomenclatureKind ON (rbNomenclatureType.kind_id = rbNomenclatureKind.id AND rbNomenclatureKind.id = %s)
        '''%((u'AND rbNomenclatureType.id = %s'%(nomenclatureTypeId)) if nomenclatureTypeId else u'', nomenclatureKindId)
    elif nomenclatureTypeId:
        joinNomenclatureFilter = u''' INNER JOIN rbNomenclatureType ON (rbNomenclature.type_id = rbNomenclatureType.id AND rbNomenclatureType.id = %s)'''%(nomenclatureTypeId)

    stmt = """
    SELECT nomenclature_id, qnt, rbUnit.name AS unitName, month_date, rbNomenclature.name AS nomenclatureName
    FROM (
        SELECT
            debNomenclature_id AS nomenclature_id, sum(StockTrans.qnt) AS `qnt`,
            %(dateCond)s AS month_date
        FROM
            StockTrans
            LEFT JOIN StockMotion_Item ON StockMotion_Item.id = StockTrans.stockMotionItem_id
            WHERE {debCond} AND (StockMotion_Item.deleted=0)
        GROUP BY nomenclature_id, month_date
        UNION ALL
        SELECT
            creNomenclature_id AS nomenclature_id, -sum(StockTrans.qnt) AS `qnt`,
            %(dateCond)s AS month_date
        FROM
            StockTrans
            LEFT JOIN StockMotion_Item ON StockMotion_Item.id = StockTrans.stockMotionItem_id
            WHERE {creCond} AND (StockMotion_Item.deleted=0)
        GROUP BY nomenclature_id, month_date
    ) AS T
    INNER JOIN rbNomenclature ON rbNomenclature.id = T.nomenclature_id
    INNER JOIN rbUnit ON rbUnit.id = rbNomenclature.defaultStockUnit_id
    %(joinNomenclatureFilter)s
    """%{'dateCond' : 'date',
         'joinNomenclatureFilter' : joinNomenclatureFilter,
        }

    query = db.query(
        stmt.format(
            debCond=db.joinAnd(debCond), creCond=db.joinAnd(creCond)
        )
    )

    result = {}

    zero = 0

    while query.next():
        record = query.record()
        nomenclatureId = forceRef(record.value('nomenclature_id'))
        nomenclatureName = forceString(record.value('nomenclatureName'))
        unitName = forceString(record.value('unitName'))

        data = result.setdefault(
            (nomenclatureId, nomenclatureName), {
                'remainingBefore': 0,
                'in': 0,
                'out': 0,
                'remainingAfter': 0,
                'unitName': unitName
            }
        )

        qnt = forceDouble(record.value('qnt'))
        date = forceDate(record.value('month_date'))
        if monthChecked:
            if date < begDate:
                data['remainingBefore'] += qnt
            else:
                if qnt > zero:
                    data['in'] += qnt
                else:
                    # use sub to increase value
                    data['out'] -= qnt
                data['remainingAfter'] += qnt
        else:
            if date < begDate:
                data['remainingBefore'] += qnt
            elif date <= endDate:
                if qnt > zero:
                    data['in'] += qnt
                else:
                    # use sub to increase value
                    data['out'] -= qnt
                data['remainingAfter'] += qnt

    for key, value in result.items():
        value['remainingAfter'] += value['remainingBefore']

    return result


class CMonthlyNomenclatureReport(CReport):
    def __init__(self, parent = None):
        CReport.__init__(self, parent)
        self.setTitle(u'Форма 2-МЗ отчет о движении лекарственных средств, подлежащих предметно-количественному учету')

    def getSetupDialog(self, parent):
        result = CNomenclatureReportDialog(parent)
        result.setDatesVisible(False)
        result.setMonthVisible(False)
        result.chkMonth.setChecked(True)
        result.setDatesOptionVisible(True)
        result.setMonthOptionVisible(True)
        result.setClientIdVisible(False)
        result.setOrgStructureVisible(True)
        result.setSignaVisible(False)
        result.setNomenclatureVisible(False)
        result.setNomenclatureTypeVisible(True)
        result.setChkCountingTotalVisible(True)
        result.setSupplierVisible(False)
        result.setSupplierOrgVisible(False)
        result.setReceiverVisible(False)
        result.setReceiverPersonVisible(False)
        result.setFinanceVisible(True)
        result.setOnlyExists(False)
        result.edtBegTime.setVisible(False)
        result.edtEndTime.setVisible(False)
        return result


    def dumpParams(self, cursor, params):
        db = QtGui.qApp.db
        description = []
        financeId = params.get('financeId', None)
        if financeId:
            description.append(u'тип финансирования: %s'%(forceString(db.translate('rbFinance', 'id', financeId, 'name')) if financeId else u'не задано'))
        nomenclatureClassId = params.get('nomenclatureClassId')
        nomenclatureKindId = params.get('nomenclatureKindId')
        nomenclatureTypeId = params.get('nomenclatureTypeId')
        if nomenclatureClassId:
            description.append(u'Номенклатура Класс %s'%forceString(db.translate('rbNomenclatureClass', 'id', nomenclatureClassId, 'name')))
        if nomenclatureKindId:
            description.append(u'Номенклатура Вид %s'%forceString(db.translate('rbNomenclatureKind', 'id', nomenclatureKindId, 'name')))
        if nomenclatureTypeId:
            description.append(u'Номенклатура Тип %s'%forceString(db.translate('rbNomenclatureType', 'id', nomenclatureTypeId, 'name')))
        cursor.movePosition(QtGui.QTextCursor.End)
        columns = [ ('100%', [], CReportBase.AlignLeft) ]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)


    def getCaption(self, cursor, params):
        monthList = [u'', u'Январь', u'Февраль', u'Март', u'Апрель', u'Май', u'Июнь', u'Июль', u'Август', u'Сентябрь', u'Октябрь', u'Ноябрь', u'Декабрь']
        orgStructureId = params.get('orgStructureId', None)
        month = params.get('monthOption', None)
        begDate = params.get('begDateOption', QDate())
        endDate = params.get('endDateOption', QDate())
        monthChecked = params.get('monthChecked', False)
        orgStrName = u''
        if orgStructureId:
            orgStrName = forceString(getOrgStructureName(orgStructureId))
        else:
            orgStrName = u'ЛПУ'
        orgId = QtGui.qApp.currentOrgId()
        orgName = u''
        if orgId:
            record = QtGui.qApp.db.getRecordEx('Organisation', 'shortName, OKPO', 'id=%s AND deleted = 0'%(str(orgId)))
            if record:
                orgName = forceString(record.value('shortName'))

        columns = [('50%', [], CReportBase.AlignLeft), ('50%', [], CReportBase.AlignLeft)]
        table = createTable(cursor, columns, headerRowCount=5, border=0, cellPadding=2, cellSpacing=0)
        table.setText(0, 0, orgName)
        table.setText(0, 1, u'Форма 2-МЗ')
        table.setText(1, 0, u'Утверждаю')
        table.setText(1, 1, u'УТВЕРЖДЕНА')
        table.setText(2, 0, u'_________________________________')
        table.setText(2, 1, u'Приказом Министерства здравоохранения СССР')
        table.setText(3, 0, u'(подпись руководителя учреждения)')
        table.setText(3, 1, u' 2 июня 1987 г. № 747')
        table.setText(4, 0, u'"__" _________ 20___ г.')
        table.setText(4, 1, u'')

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        boldChars = QtGui.QTextCharFormat()
        boldChars.setFontWeight(QtGui.QFont.Bold)
        columns2 = [('100%', [], CReportBase.AlignCenter)]
        table2 = createTable(cursor, columns2, headerRowCount=2, border=0, cellPadding=2, cellSpacing=0)
        if monthChecked:
            table2.setText(0, 0, u'Отчет '+ orgStrName + u' за ' + monthList[month.month()] + u' '+ forceString(month.year()), charFormat=boldChars)
        else:
            table2.setText(0, 0, u'Отчет '+ orgStrName + u' '+ dateRangeAsStr(u'за период', begDate, endDate), charFormat=boldChars)
        cursor.movePosition(QtGui.QTextCursor.End)


    def build(self, params):
        monthChecked = params.get('monthChecked', False)
        chkCountingTotal = params.get('chkCountingTotal', False)
        reportTotal = [0]*4
        tableColumns = [
            ('5%', [u'№'], CReportBase.AlignRight),
            ('30%', [u'Наименование'], CReportBase.AlignLeft),
            ('13%', [u'Ед. Изм.'], CReportBase.AlignRight),
            ('6%', [u'Остаток на начало месяца' if monthChecked else u'Остаток на начало периода'], CReportBase.AlignRight),
            ('6%', [u'Приход'], CReportBase.AlignRight),
            ('6%', [u'Расход'], CReportBase.AlignRight),
            ('6%', [u'Остаток на конец месяца'  if monthChecked else u'Остаток на конец периода'], CReportBase.AlignRight),
            ('6%', [u'Цена'], CReportBase.AlignRight),
            ('6%', [u'Сумма'], CReportBase.AlignRight)
        ]

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        self.getCaption(cursor, params)
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        table = createTable(cursor, tableColumns)

        data = _selectData(params)

        for key in sorted(data.keys(), key=lambda k: k[1]):
            values = data[key]
            if round(values['remainingBefore'], 2) !=0 or round(values['in'], 2)!=0 or round(values['out'], 2)!=0 or round(values['remainingAfter'], 2)!=0:
                row = table.addRow()
                table.setText(row, 0, row)
                table.setText(row, 1, key[1])
                table.setText(row, 2, values['unitName'])
                table.setText(row, 3, "%.2f" %values['remainingBefore'] if "%.2f" %values['remainingBefore']!=u'-0.00' else u'0.00')
                table.setText(row, 4, "%.2f" %values['in'] if "%.2f" %values['in']!=u'-0.00' else u'0.00')
                table.setText(row, 5, "%.2f" %values['out'] if "%.2f" %values['out']!=u'-0.00' else u'0.00')
                table.setText(row, 6, "%.2f" %values['remainingAfter'] if "%.2f" %values['remainingAfter']!=u'-0.00' else u'0.00')
                if chkCountingTotal:
                    reportTotal[0] += forceDouble("%.2f" %values['remainingBefore'] if "%.2f" %values['remainingBefore']!=u'-0.00' else u'0.00')
                    reportTotal[1] += forceDouble("%.2f" %values['in'] if "%.2f" %values['in']!=u'-0.00' else u'0.00')
                    reportTotal[2] += forceDouble("%.2f" %values['out'] if "%.2f" %values['out']!=u'-0.00' else u'0.00')
                    reportTotal[3] += forceDouble("%.2f" %values['remainingAfter'] if "%.2f" %values['remainingAfter']!=u'-0.00' else u'0.00')
        if chkCountingTotal and reportTotal:
            i = table.addRow()
            table.setText(i, 0, u'ИТОГО', charFormat=CReportBase.ReportSubTitle, blockFormat=CReportBase.AlignLeft)
            table.mergeCells(i, 0, 1, 3)
            for col, val in enumerate(reportTotal):
                table.setText(i, col+3, val, charFormat=CReportBase.ReportSubTitle)

        db = QtGui.qApp.db
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertBlock()
        tablePerson = db.table('Person')
        tablePost = db.table('rbPost')
        currentPersonId = QtGui.qApp.userId
        stmt = db.selectStmt(tablePerson.leftJoin(tablePost, tablePost['id'].eq(tablePerson['post_id'])), tablePost['name'], tablePerson['id'].eq(currentPersonId))
        query = db.query(stmt)
        while query.next():
            record = query.record()
            postName = forceString(record.value('name'))
        currentPerson = forceString(db.translate('vrbPerson', 'id', currentPersonId, 'name'))

        columns = [('70%', [], CReportBase.AlignLeft), ('30%', [], CReportBase.AlignLeft)]
        tableBot = createTable(cursor, columns, headerRowCount=2, border=0, cellPadding=2, cellSpacing=0)
        tableBot.setText(0, 0, u'Отчет составил: ' + (postName if postName!='' else ' __________________ ') +  ' __________________ ' + ' %s' %currentPerson)
        tableBot.setText(0, 1, u'')
        tableBot.setText(1, 0, u'Отчет проверил: __________________  __________________  ______________')
        tableBot.setText(1, 1, u'')
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        return doc
