# -*- coding: utf-8 -*-

from PyQt4 import QtGui

from Reports.Report import CReport, createTable
from Reports.ReportBase import CReportBase

from library.Utils import forceString, forceInt, forceDouble
from EconomicAnalisysSetupDialog import CEconomicAnalisysSetupDialog
from EconomicAnalisys import getStmt, colServiceInfis, colServiceName, colKDPD, colUET, colAmount, colSUM, colExposedSum


class CEconomicAnalisysE1(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Э-1. Нагрузка на врача')

    def selectData(self, params):
        cols = [colServiceInfis, colServiceName, colKDPD, colUET, colAmount, colSUM, colExposedSum]
        colsStmt = u"""select colServiceInfis as code_usl,
        colServiceName as name_usl,
        sum(colAmount) as amount,
        round(sum(colUET), 2) as uet,
        sum(colKD) as kd,
        round(sum(colSUM), 2) as sum,
        round(sum(colExposedSUM), 2) as exposedSum
        """
        groupCols = u'colServiceInfis, colServiceName'
        orderCols = u'colServiceInfis, colServiceName'
        
        stmt = getStmt(colsStmt, cols, groupCols, orderCols, params)

        db = QtGui.qApp.db
        return db.query(stmt)

    def build(self, description, params):
        needExposedSum = params.get('dataType', None) == 3

        reportRowSize = 7 if needExposedSum else 6
        colsShift = 2
        reportData = {}

        def processQuery(query):
            while query.next():
                record = query.record()
                code_usl = forceString(record.value('code_usl'))
                name_usl = forceString(record.value('name_usl'))
                amount = forceInt(record.value('amount'))
                kd = forceInt(record.value('kd'))
                pd = forceInt(record.value('pd'))
                uet = forceDouble(record.value('uet'))
                sum = forceDouble(record.value('sum'))
                exposedSum = forceDouble(record.value('exposedSum'))

                key = (code_usl, name_usl)
                reportLine = reportData.setdefault(key, [0]*reportRowSize)
                reportLine[0] += amount
                reportLine[1] += kd + pd
                reportLine[2] += uet
                reportLine[3] += sum
                if needExposedSum:
                    reportLine[4] += exposedSum

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
            ('10%',  [u'Услуга', u'Код'], CReportBase.AlignLeft),
            ('50%',  ['', u'Наименование'], CReportBase.AlignLeft),
            ('6%',  [u'Кол-во услуг'], CReportBase.AlignRight),
            ('10%',  [u'Кол-во койко-дней (дней лечения)'], CReportBase.AlignRight),
            ('10%',  [u'Кол-во УЕТ'], CReportBase.AlignRight),
            ('7%',  [u'Сумма'], CReportBase.AlignRight)
            ]
        if needExposedSum:
            tableColumns.append(('7%',  [u'Выставленная сумма'], CReportBase.AlignRight))
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


class CEconomicAnalisysE1Ex(CEconomicAnalisysE1):
    def exec_(self, accountIdList=None):
        self.accountIdList = accountIdList
        CEconomicAnalisysE1.exec_(self)

    def getSetupDialog(self, parent):
        result = CEconomicAnalisysSetupDialog(parent)
        result.setTitle(self.title())
        result.shrink()
        result.loadPrefs()
        return result

    def build(self, params):
        params['accountIdList'] = self.accountIdList
        return CEconomicAnalisysE1.build(self, '\n'.join(self.getDescription(params)), params)
