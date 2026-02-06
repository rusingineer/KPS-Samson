# -*- coding: utf-8 -*-

from PyQt4 import QtGui

from Reports.Report import CReport, createTable
from Reports.ReportBase import CReportBase

from library.Utils import forceString, forceInt, forceDouble
from EconomicAnalisysSetupDialog import CEconomicAnalisysSetupDialog
from EconomicAnalisys import getStmt, colClient, colEvent, colMKBCode, colMKBName, colCSG, colPos, colObr, colSMP, \
    colKD, colPD, colUET, colAmount, colSUM, colExposedSum


class CEconomicAnalisysE2(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Э-2. Выполненные объемы услуг в разрезе диагнозов')

    def selectData(self, params):
        cols = [colClient, colEvent, colMKBCode, colMKBName, colCSG, colPos, colObr, colSMP, colKD, colPD, colUET,
                colAmount, colSUM, colExposedSum]
        colsStmt = u"""select colMKBCode as code_mkb,
        colMKBName as name_mkb,
        count(distinct colEvent) as cnt,
        count(distinct colClient) as fl,
        sum(colCSG) as mes,
        sum(colPos) as pos,
        sum(colObr) as obr,
        round(sum(colUET), 2) as uet,
        sum(colKD) as kd,
        sum(colPD) as pd,
        sum(colSMP) as callambulance,
        sum(IF(colPos = 0 and colCSG = 0 and colSMP = 0 and colObr = 0, colAmount, 0)) as usl,
        round(sum(colSUM), 2) as sum,
        round(sum(colExposedSUM), 2) as exposedSum
        """
        groupCols = u'colMKBCode, colMKBName'
        orderCols = u'colMKBCode, colMKBName'
        
        stmt = getStmt(colsStmt, cols, groupCols, orderCols, params)

        return QtGui.qApp.db.query(stmt)

    def build(self, description, params):
        needExposedSum = params.get('dataType', None) == 3

        reportRowSize = 14 if needExposedSum else 13
        colsShift = 2
        reportData = {}

        def processQuery(query):
            while query.next():
                record = query.record()
                code_mkb = forceString(record.value('code_mkb'))
                name_mkb = forceString(record.value('name_mkb'))
                cnt = forceInt(record.value('cnt'))
                fl = forceInt(record.value('fl'))
                mes = forceInt(record.value('mes'))
                kd = forceInt(record.value('kd'))
                pd = forceInt(record.value('pd'))
                pos = forceInt(record.value('pos'))
                obr = forceInt(record.value('obr'))
                usl = forceInt(record.value('usl'))
                callambulance = forceInt(record.value('callambulance'))
                uet = forceDouble(record.value('uet'))
                sum = forceDouble(record.value('sum'))
                exposedSum = forceDouble(record.value('exposedSum'))

                key = (code_mkb, name_mkb)
                reportLine = reportData.setdefault(key, [0]*reportRowSize)
                reportLine[0] += cnt
                reportLine[1] += fl
                reportLine[2] += mes
                reportLine[3] += kd
                reportLine[4] += pd
                reportLine[5] += pos
                reportLine[6] += obr
                reportLine[7] += uet
                reportLine[8] += usl
                reportLine[9] += callambulance
                reportLine[10] += sum
                if needExposedSum:
                    reportLine[11] += exposedSum
        query = self.selectData(params)
        processQuery(query)

        # now text
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertText(description)
        cursor.insertBlock()

        tableColumns = [
            ('7%', [u'Диагноз', u'Код'], CReportBase.AlignLeft),
            ('43%', ['', u'Наименование'], CReportBase.AlignLeft),
            ('5%', [u'Кол-во случаев'], CReportBase.AlignRight),
            ('5%', [u'Кол-во пациентов'], CReportBase.AlignRight),
            ('5%', [u'Кол-во КСГ'], CReportBase.AlignRight),
            ('5%', [u'Кол-во койко-дней'], CReportBase.AlignRight),
            ('5%', [u'Кол-во дней лечения'], CReportBase.AlignRight),
            ('5%', [u'Кол-во посещений'], CReportBase.AlignRight),
            ('5%', [u'Кол-во обращений'], CReportBase.AlignRight),
            ('5%', [u'Кол-во УЕТ'], CReportBase.AlignRight),
            ('5%', [u'Кол-во простых услуг'], CReportBase.AlignRight),
            ('5%', [u'Кол-во вызовов СМП'], CReportBase.AlignRight),
            ('5%', [u'Сумма'], CReportBase.AlignRight)
            ]
        if needExposedSum:
            tableColumns.append(('5%',  [u'Выставленная сумма'], CReportBase.AlignRight))
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 1, 2)
        for col in xrange(reportRowSize):
            table.mergeCells(0, col, 2, 1)
        totalByReport = [0]*reportRowSize

        keys = reportData.keys()
        keys.sort()
        for key in keys:
            row = table.addRow()
            table.setText(row, 0, key[0])
            table.setText(row, 1, key[1])
            reportLine = reportData[key]
            for col in xrange(reportRowSize-colsShift):
                table.setText(row, col + colsShift, reportLine[col])
                totalByReport[col] = totalByReport[col] + reportLine[col]
        row = table.addRow()
        table.setText(row, 0, u'Итого')
        table.mergeCells(row, 0, 1, 2)
        for col in xrange(reportRowSize-colsShift):
            table.setText(row, col + colsShift, totalByReport[col])

        return doc


class CEconomicAnalisysE2Ex(CEconomicAnalisysE2):
    def exec_(self, accountIdList=None):
        self.accountIdList = accountIdList
        CEconomicAnalisysE2.exec_(self)

    def getSetupDialog(self, parent):
        result = CEconomicAnalisysSetupDialog(parent)
        result.setTitle(self.title())
        result.shrink()
        result.loadPrefs()
        return result

    def build(self, params):
        params['accountIdList'] = self.accountIdList
        return CEconomicAnalisysE2.build(self, '\n'.join(self.getDescription(params)), params)
