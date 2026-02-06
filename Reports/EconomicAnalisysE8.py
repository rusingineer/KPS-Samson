# -*- coding: utf-8 -*-

from PyQt4 import QtGui

from Reports.Report import CReport, createTable
from Reports.ReportBase import CReportBase

from library.Utils import forceString, forceInt, forceDouble
from EconomicAnalisysSetupDialog import CEconomicAnalisysSetupDialog
from EconomicAnalisys import getStmt, colClient, colEvent, colFinance, colOrgStructure, colCSG, colPos, colObr, colSMP, \
    colKD, colPD, colUET, colAmount, colSUM, colExposedSum


class CEconomicAnalisysE8(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Э-8. Анализ нагрузки на подразделения по видам финансирования')

    def selectData(self, params):
        cols = [colClient, colEvent, colFinance, colOrgStructure, colCSG, colPos, colObr, colSMP, colKD, colPD, colUET,
                colAmount, colSUM, colExposedSum]
        colsStmt = u"""select colFinance as fin,
        colOrgStructure as osname,
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
        groupCols = u'colFinance, colOrgStructure'
        orderCols = u'colFinance, colOrgStructure'
        
        stmt = getStmt(colsStmt, cols, groupCols, orderCols, params)

        db = QtGui.qApp.db
        return db.query(stmt)

    def build(self, description, params):
        needExposedSum = params.get('dataType', None) == 3

        reportRowSize = 14 if needExposedSum else 13
        reportData = {}

        def processQuery(query):
            while query.next():
                record = query.record()
                fin = forceString(record.value('fin'))
                osname = forceString(record.value('osname'))
                cnt = forceInt(record.value('cnt'))
                fl = forceInt(record.value('fl'))
                mes = forceInt(record.value('mes'))
                pos = forceInt(record.value('pos'))
                obr = forceInt(record.value('obr'))
                kd = forceInt(record.value('kd'))
                pd = forceInt(record.value('pd'))
                usl = forceInt(record.value('usl'))
                callambulance = forceInt(record.value('callambulance'))
                uet = forceDouble(record.value('uet'))
                sum = forceDouble(record.value('sum'))
                exposedSum = forceDouble(record.value('exposedSum'))
                osname = osname if osname else '---'
                key = (fin if fin else u'Вид финансирования не указан', osname)
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
            ('35%', [u'Отделение'], CReportBase.AlignLeft),
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
            ('8%', [u'Сумма'], CReportBase.AlignRight)
            ]
        if needExposedSum:
            tableColumns.append(('7%',  [u'Выставленная сумма'], CReportBase.AlignRight))
        table = createTable(cursor, tableColumns)
        totalByReport = [0]*reportRowSize
        colsShift = 1
        keys = reportData.keys()
        keys.sort()
        dFinances = {}

        for key in keys:
            fin = key[0]
            if fin not in dFinances:
                dFinances[fin] = []
            dFinances[fin].append([key[1], reportData[key]])

        for fin in dFinances.keys():
            totalByFin = [0]*reportRowSize
            table.setText(table.addRow(), 0, fin, CReportBase.TableHeader)

            for osname, reportLine in dFinances[fin]:
                row = table.addRow()
                table.setText(row,  0,  osname)
                for col in xrange(reportRowSize-2):
                    table.setText(row, col + colsShift, reportLine[col])
                    totalByFin[col] = totalByFin[col] + reportLine[col]
                    totalByReport[col] = totalByReport[col] + reportLine[col]

            row = table.addRow()
            table.setText(row, 0, u'Итого %s' % fin)
            for col in xrange(reportRowSize-2):
                table.setText(row, col + colsShift, totalByFin[col])
        row = table.addRow()
        table.setText(row, 0, u'Итого')
        for col in xrange(reportRowSize-2):
            table.setText(row, col + colsShift, totalByReport[col])

        return doc


class CEconomicAnalisysE8Ex(CEconomicAnalisysE8):
    def exec_(self, accountIdList=None):
        self.accountIdList = accountIdList
        CEconomicAnalisysE8.exec_(self)

    def getSetupDialog(self, parent):
        result = CEconomicAnalisysSetupDialog(parent)
        result.setTitle(self.title())
        result.shrink()
        result.loadPrefs()
        return result

    def build(self, params):
        params['accountIdList'] = self.accountIdList
        return CEconomicAnalisysE8.build(self, '\n'.join(self.getDescription(params)), params)
