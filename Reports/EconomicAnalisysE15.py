# -*- coding: utf-8 -*-

from PyQt4 import QtGui

from Reports.Report import CReport, createTable
from Reports.ReportBase import CReportBase

from library.Utils import forceString, forceInt, forceDouble
from EconomicAnalisysSetupDialog import CEconomicAnalisysSetupDialog
from EconomicAnalisys import getStmt, colClient, colEvent, colPayerTitle, colOrgStructure, colCSG, colPos, colObr, \
    colSMP, colKD, colPD, colUET, colAmount, colSUM, colExposedSum


class CEconomicAnalisysE15(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Форма Э-15. Отчет о работе отделений в разрезе плательщиков.')

    def selectData(self, params):
        cols = [colClient, colEvent, colPayerTitle, colOrgStructure, colCSG, colPos, colObr, colSMP, colKD, colPD,
                colUET, colAmount, colSUM, colExposedSum]
        colsStmt = u"""select colPayerTitle as osname,
        colOrgStructure as orgname,
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
        groupCols = u'colPayerTitle, colOrgStructure'
        orderCols = u'colPayerTitle, colOrgStructure'
        
        stmt = getStmt(colsStmt, cols, groupCols, orderCols, params)

        return QtGui.qApp.db.query(stmt)


    def build(self, description, params):
        needExposedSum = params.get('dataType', None) == 3

        reportRowSize = 12 if needExposedSum else 11
        reportData = {}

        def processQuery(query):
            while query.next():
                record = query.record()
                osname = forceString(record.value('osname'))
                orgname = forceString(record.value('orgname'))
                cnt = forceInt(record.value('cnt'))
                mes = forceInt(record.value('mes'))
                pos = forceInt(record.value('pos'))
                kd = forceInt(record.value('kd'))
                pd = forceInt(record.value('pd'))
                usl = forceInt(record.value('usl'))
                callambulance = forceInt(record.value('callambulance'))
                uet = forceDouble(record.value('uet'))
                sum = forceDouble(record.value('sum'))
                exposedSum = forceDouble(record.value('exposedSum'))

                key = (osname if osname else u'Не задан',  orgname if orgname else u'Не задан')
                reportLine = reportData.setdefault(key, [0]*reportRowSize)
                reportLine[0] += cnt
                reportLine[1] += mes
                reportLine[2] += kd
                reportLine[3] += pd
                reportLine[4] += pos
                reportLine[5] += uet
                reportLine[6] += usl
                reportLine[7] += callambulance
                reportLine[8] += sum
                if needExposedSum:
                    reportLine[9] += exposedSum
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
            ('35%',  [u'Плательщик/Отделение'], CReportBase.AlignLeft),
            ('5%',  [u'Кол-во случаев'], CReportBase.AlignRight),
            ('5%',  [u'Кол-во КСГ'], CReportBase.AlignRight),
            ('5%',  [u'Кол-во койко-дней'], CReportBase.AlignRight),
            ('5%',  [u'Кол-во дней лечения'], CReportBase.AlignRight),
            ('5%',  [u'Кол-во посещений'], CReportBase.AlignRight),
            ('5%',  [u'Кол-во УЕТ'], CReportBase.AlignRight),
            ('5%',  [u'Кол-во простых услуг'], CReportBase.AlignRight),
            ('5%',  [u'Кол-во вызовов СМП'], CReportBase.AlignRight),
            ('13%',  [u'Сумма'], CReportBase.AlignRight)
            ]
        if needExposedSum:
            tableColumns.append(('12%',  [u'Выставленная сумма'], CReportBase.AlignRight))
        table = createTable(cursor, tableColumns)
        totalByOS = [0]*reportRowSize
        totalByReport = [0]*reportRowSize
        colsShift = 1
        prevOs = None
        osname = None

        keys = reportData.keys()
        keys.sort()
        for key in keys:

            osname = key[0]
            orgname = key[1]
            if prevOs != osname:
                if prevOs is not None:
                    row = table.addRow()
                    table.setText(row, 0, u'Итого по %s' % prevOs)
                    for col in xrange(reportRowSize-2):
                        table.setText(row, col + colsShift, totalByOS[col])
                        totalByReport[col] = totalByReport[col] + totalByOS[col]
                    totalByOS = [0]*reportRowSize

                row = table.addRow()
                table.setText(row, 0, u'Плательщик: %s' % osname,  CReportBase.TableHeader)
                table.mergeCells(row, 0, 1, reportRowSize-1)
                prevOs = osname

            row = table.addRow()
            table.setText(row, 0, orgname)
            reportLine = reportData[key]
            for col in xrange(reportRowSize-2):
                table.setText(row, col + colsShift, reportLine[col])
                totalByOS[col] = totalByOS[col] + reportLine[col]
        if osname is not None:
            row = table.addRow()
            table.setText(row, 0, u'Итого по %s' % osname)
            for col in xrange(reportRowSize-2):
                table.setText(row, col + colsShift, totalByOS[col])
                totalByReport[col] = totalByReport[col] + totalByOS[col]
        row = table.addRow()
        table.setText(row, 0, u'Итого')
        for col in xrange(reportRowSize-2):
            table.setText(row, col + colsShift, totalByReport[col])

        return doc


class CEconomicAnalisysE15Ex(CEconomicAnalisysE15):
    def exec_(self, accountIdList=None):
        self.accountIdList = accountIdList
        CEconomicAnalisysE15.exec_(self)

    def getSetupDialog(self, parent):
        result = CEconomicAnalisysSetupDialog(parent)
        result.setTitle(self.title())
        result.shrink()
        result.loadPrefs()
        return result

    def build(self, params):
        params['accountIdList'] = self.accountIdList
        return CEconomicAnalisysE15.build(self, '\n'.join(self.getDescription(params)), params)
