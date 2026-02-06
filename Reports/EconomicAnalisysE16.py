# -*- coding: utf-8 -*-

from PyQt4 import QtGui

from Reports.Report import CReport, createTable
from Reports.ReportBase import CReportBase

from library.Utils import forceString, forceInt, forceDouble
from EconomicAnalisysSetupDialog import CEconomicAnalisysSetupDialog
from EconomicAnalisys import getStmt, colClient, colEvent, colPayerTitle, colPerson, colCSG, colPos, colObr, colSMP, \
    colKD, colPD, colUET, colAmount, colSUM, colExposedSum


class CEconomicAnalisysE16(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Э-16. Отчет о работе врачей в разрезе плательщиков')

    def selectData(self, params):
        cols = [colClient, colEvent, colPayerTitle, colPerson, colCSG, colPos, colObr, colSMP, colKD, colPD, colUET,
                colAmount, colSUM, colExposedSum]
        colsStmt = u"""select colPayerTitle as payer_name,
        colPerson as person,
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
        
        groupCols = u'colPayerTitle, colPerson'
        orderCols = u'colPayerTitle, colPerson'
        
        stmt = getStmt(colsStmt, cols, groupCols, orderCols, params)

        return QtGui.qApp.db.query(stmt)


    def build(self, description, params):
        needExposedSum = params.get('dataType', None) == 3

        reportRowSize = 13 if needExposedSum else 12
        colsShift = 1
        reportData = {}

        def processQuery(query):
            while query.next():
                record = query.record()
                payer_name = forceString(record.value('payer_name'))
                person = forceString(record.value('person'))
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

                key = (payer_name if payer_name else u'Не определен', person if person else u'Не выбран')
                reportLine = reportData.setdefault(key, [0]*reportRowSize)
                reportLine[0] += fl
                reportLine[1] += cnt
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
            ('35%',  [u'Плательщик / Врач'], CReportBase.AlignLeft),
            ('5%',  [u'Кол-во случаев'], CReportBase.AlignRight),
            ('5%',  [u'Кол-во пациентов'], CReportBase.AlignRight),
            ('5%',  [u'Кол-во КСГ'], CReportBase.AlignRight),
            ('5%',  [u'Кол-во койко-дней'], CReportBase.AlignRight),
            ('5%',  [u'Кол-во дней лечения'], CReportBase.AlignRight),
            ('5%',  [u'Кол-во посещений'], CReportBase.AlignRight),
            ('5%',  [u'Кол-во обращений'], CReportBase.AlignRight),
            ('5%',  [u'Кол-во УЕТ'], CReportBase.AlignRight),
            ('5%',  [u'Кол-во простых услуг'], CReportBase.AlignRight),
            ('5%',  [u'Кол-во вызовов СМП'], CReportBase.AlignRight),
            ('5%',  [u'Сумма'], CReportBase.AlignRight)
            ]
        if needExposedSum:
            tableColumns.append(('5%',  [u'Выставленная сумма'], CReportBase.AlignRight))
        table = createTable(cursor, tableColumns)
        totalByPayer = [0]*reportRowSize
        totalByReport = [0]*reportRowSize
        prevPayerName = None
        payerName = None

        keys = reportData.keys()
        keys.sort()
        for key in keys:
            payerName = key[0]
            person = key[1]

            if prevPayerName != payerName:
                if prevPayerName is not None:
                    row = table.addRow()
                    table.setText(row, 0, u'Итого по %s' % prevPayerName)
                    for col in xrange(reportRowSize-colsShift):
                        table.setText(row, col + colsShift, totalByPayer[col])
                        totalByReport[col] = totalByReport[col] + totalByPayer[col]
                    totalByPayer = [0]*reportRowSize

                row = table.addRow()
                table.setText(row, 0, u'Плательщик: %s' % payerName,  CReportBase.TableHeader)
                table.mergeCells(row, 0, 1, reportRowSize-1)
                prevPayerName = payerName

            row = table.addRow()
            table.setText(row, 0, u'    ' + person)

            reportLine = reportData[key]
            for col in xrange(reportRowSize-colsShift):
                table.setText(row, col + colsShift, reportLine[col])
                totalByPayer[col] = totalByPayer[col] + reportLine[col]

        if prevPayerName != payerName:
            if prevPayerName is not None:
                row = table.addRow()
                table.setText(row, 0, u'Итого по %s' % payerName)
                for col in xrange(reportRowSize-colsShift):
                    table.setText(row, col + colsShift, totalByPayer[col])
                    totalByReport[col] = totalByReport[col] + totalByPayer[col]

        if prevPayerName is not None:
            row = table.addRow()
            table.setText(row, 0, u'Итого по %s' % payerName)
            for col in xrange(reportRowSize-colsShift):
                table.setText(row, col + colsShift, totalByPayer[col])
                totalByReport[col] = totalByReport[col] + totalByPayer[col]

        row = table.addRow()
        table.setText(row, 0, u'Итого')
        for col in xrange(reportRowSize-colsShift):
            table.setText(row, col + colsShift, totalByReport[col])

        return doc


class CEconomicAnalisysE16Ex(CEconomicAnalisysE16):
    def exec_(self, accountIdList=None):
        self.accountIdList = accountIdList
        CEconomicAnalisysE16.exec_(self)

    def getSetupDialog(self, parent):
        result = CEconomicAnalisysSetupDialog(parent)
        result.setTitle(self.title())
        result.shrink()
        result.loadPrefs()
        return result

    def build(self, params):
        params['accountIdList'] = self.accountIdList
        return CEconomicAnalisysE16.build(self, '\n'.join(self.getDescription(params)), params)
