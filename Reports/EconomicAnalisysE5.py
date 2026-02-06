# -*- coding: utf-8 -*-

from PyQt4 import QtGui

from Reports.Report import CReport, createTable
from Reports.ReportBase import CReportBase

from library.Utils import forceString, forceInt, forceDouble
from EconomicAnalisysSetupDialog import CEconomicAnalisysSetupDialog
from EconomicAnalisys import getStmt, colClient, colEvent, colOrgStructure, colPayerTitle, colServiceInfis, \
    colServiceName, colCSG, colPos, colObr, colSMP, colKD, colPD, colUET, colAmount, colSUM, colExposedSum


class CEconomicAnalisysE5(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Э-5. Нагрузка на отделение в разрезе выполненных услуг')

    def selectData(self, params):
        cols = [colClient, colEvent, colOrgStructure, colPayerTitle, colServiceInfis, colServiceName, colCSG, colPos,
                colObr, colSMP, colKD, colPD, colUET, colAmount, colSUM, colExposedSum]
        colsStmt = u"""select colOrgStructure as osname,
        colPayerTitle as payer_title,
        colServiceInfis as code,
        colServiceName as usluga,
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
        groupCols = u'colOrgStructure, colPayerTitle, colServiceName, colServiceInfis'
        orderCols = u'colOrgStructure, colPayerTitle, colServiceName, colServiceInfis'
        
        stmt = getStmt(colsStmt, cols, groupCols, orderCols, params)
        db = QtGui.qApp.db
        return db.query(stmt)

    def build(self, description, params):
        needExposedSum = params.get('dataType', None) == 3

        reportRowSize = 15 if needExposedSum else 14
        colsShift = 3
        reportData = {}

        def processQuery(query):
            while query.next():
                record = query.record()
                osname = forceString(record.value('osname'))
                payer_title = forceString(record.value('payer_title'))
                usluga = forceString(record.value('usluga'))
                code = forceString(record.value('code'))
                cnt = forceInt(record.value('cnt'))
                fl = forceInt(record.value('fl'))
                csg = forceInt(record.value('csg'))
                pos = forceInt(record.value('pos'))
                obr = forceInt(record.value('obr'))
                kd = forceInt(record.value('kd'))
                pd = forceInt(record.value('pd'))
                usl = forceInt(record.value('usl'))
                callambulance = forceInt(record.value('callambulance'))
                uet = forceDouble(record.value('uet'))
                sum = forceDouble(record.value('sum'))
                exposedSum = forceDouble(record.value('exposedSum'))

                key = (osname if osname else u'Без подразделения', code,  payer_title, usluga)
                reportLine = reportData.setdefault(key, [0]*reportRowSize)
                
                reportLine[0] += cnt
                reportLine[1] += fl
                reportLine[2] += csg
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
            ('5%', [u'Услуга', u'Код'], CReportBase.AlignLeft),
            ('20%', ['', u'Наименование'], CReportBase.AlignLeft),
            ('15%', [u'Плательщик'], CReportBase.AlignLeft),
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
        for i in xrange(reportRowSize-colsShift+1):
            table.mergeCells(0, i+colsShift-1,  i+colsShift-1, 1)
        totalByFinance = [0]*reportRowSize
        totalByReport = [0]*reportRowSize

        prevOsname = None
        osname = None

        keys = reportData.keys()
        keys.sort()
        for key in keys:
            osname = key[0]
            code = key[1]
            payer_title = key[2]
            usluga = key[3]

            if prevOsname != osname:
                if prevOsname is not None:
                    row = table.addRow()
                    table.setText(row, 0, u'Итого по %s' % prevOsname)
                    table.mergeCells(row, 0, 1, 3)
                    for col in xrange(reportRowSize-colsShift):
                        table.setText(row, col + colsShift, totalByFinance[col])
                        totalByReport[col] = totalByReport[col] + totalByFinance[col]
                    totalByFinance = [0]*reportRowSize

                row = table.addRow()
                table.setText(row, 0, osname,  CReportBase.TableHeader)
                table.mergeCells(row, 0, 1, reportRowSize)
                prevOsname = osname

            row = table.addRow()
            table.setText(row, 0, code)
            table.setText(row, 1, usluga)
            if payer_title == '':
                table.setText(row, 2, u'Плательщик не определен (нет полиса)')
            else:
                table.setText(row, 2, payer_title)
            reportLine = reportData[key]
            for col in xrange(reportRowSize-colsShift):
                table.setText(row, col + colsShift, reportLine[col])
                totalByFinance[col] = totalByFinance[col] + reportLine[col]
        if osname is not None:
            row = table.addRow()
            table.setText(row, 0, u'Итого по %s' % osname)
            table.mergeCells(row, 0, 1, 3)
            for col in xrange(reportRowSize-colsShift):
                table.setText(row, col + colsShift, totalByFinance[col])
                totalByReport[col] = totalByReport[col] + totalByFinance[col]
        row = table.addRow()
        table.setText(row, 0, u'Итого')
        table.mergeCells(row, 0, 1, 3)
        for col in xrange(reportRowSize-colsShift):
            table.setText(row, col + colsShift, totalByReport[col])

        return doc


class CEconomicAnalisysE5Ex(CEconomicAnalisysE5):
    def exec_(self, accountIdList=None):
        self.accountIdList = accountIdList
        CEconomicAnalisysE5.exec_(self)

    def getSetupDialog(self, parent):
        result = CEconomicAnalisysSetupDialog(parent)
        result.setTitle(self.title())
        result.shrink()
        result.loadPrefs()
        return result

    def build(self, params):
        params['accountIdList'] = self.accountIdList
        return CEconomicAnalisysE5.build(self, '\n'.join(self.getDescription(params)), params)
