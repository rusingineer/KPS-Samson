# -*- coding: utf-8 -*-

from PyQt4 import QtGui

from Reports.Report import CReport, createTable
from Reports.ReportBase import CReportBase

from library.Utils import forceString, forceInt, forceDouble, forceBool
from EconomicAnalisysSetupDialog import CEconomicAnalisysSetupDialog
from EconomicAnalisys import getStmt, colInsurerCodeName, colEvent, colUET, colSUM, colIsWorking, colExposedSum


class CEconomicAnalisysE14(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Форма Э-14. Отчет о пролеченных больных, застрахованных на территории Краснодарского края, в разрезе страховщиков.')

    def selectData(self, params):
        cols = [colInsurerCodeName, colEvent, colUET, colSUM, colExposedSum, colIsWorking]
        colsStmt = u"""select colInsurerCodeName as insurer,
        count(distinct colEvent) as cnt,
        round(sum(colSUM), 2) as sum,
        round(sum(colExposedSUM), 2) as exposedSum,
        colIsWorking as isWorking
        """
        groupCols = u'colInsurerCodeName, colIsWorking'
        orderCols = u'colInsurerCodeName, colIsWorking'

        stmt = getStmt(colsStmt, cols, groupCols, orderCols, params, additionCond=u"and substr(Insurer.area, 1, 2) = '%(defaultRegion)s' and ct.id is not null")

        db = QtGui.qApp.db
        return db.query(stmt)

    def build(self, description, params):
        needExposedSum = params.get('dataType', None) == 3

        reportData = {'keys': []}

        def processQuery(query):
            while query.next():
                record = query.record()
                insurer = forceString(record.value('insurer'))
                if not insurer:
                    insurer = u'Без страховщика'
                cnt = forceInt(record.value('cnt'))
                uet = forceDouble(record.value('uet'))
                sum = forceDouble(record.value('sum'))
                exposedSum = forceDouble(record.value('exposedSum'))
                isWorking = forceBool(record.value('isWorking'))
                if insurer not in reportData['keys']:
                    reportData['keys'].append(insurer)
                defaultVals = {
                    'cntAll': 0,
                    'sumAll': 0,
                    'exposedSumAll': 0,
                    'uetAll': 0,
                    'cntW': 0,
                    'sumW': 0,
                    'exposedSumW': 0,
                    'uetW': 0,
                    'cntNW': 0,
                    'sumNW': 0,
                    'exposedSumNW': 0,
                    'uetNW': 0,
                    }
                reportline = reportData.setdefault(insurer, defaultVals.copy())
                total = reportData.setdefault('total',  defaultVals.copy())
                reportline['cntAll'] += cnt
                reportline['sumAll'] += sum
                reportline['exposedSumAll'] += exposedSum
                reportline['uetAll'] += uet
                total['cntAll'] += cnt
                total['sumAll'] += sum
                total['exposedSumAll'] += exposedSum
                total['uetAll'] += uet
                if isWorking:
                    reportline['cntW'] += cnt
                    reportline['sumW'] += sum
                    reportline['exposedSumW'] += exposedSum
                    reportline['uetW'] += uet
                    total['cntW'] += cnt
                    total['sumW'] += sum
                    total['exposedSumW'] += exposedSum
                    total['uetW'] += uet
                else:
                    reportline['cntNW'] += cnt
                    reportline['sumNW'] += sum
                    reportline['exposedSumNW'] += exposedSum
                    reportline['uetNW'] += uet
                    total['cntNW'] += cnt
                    total['sumNW'] += sum
                    total['exposedSumNW'] += exposedSum
                    total['uetNW'] += uet

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

        if needExposedSum:
            tableColumns = [
                ('33%', [u'Страховщик'], CReportBase.AlignCenter),
                ('7%', [u'Всего', u'Кол-во cлучаев'], CReportBase.AlignCenter),
                ('7%', ['', u'Сумма по ОМС, руб'], CReportBase.AlignCenter),
                ('7%', ['', u'Выставленная сумма по ОМС, руб'], CReportBase.AlignCenter),
                ('7%', [u'по неработающим', u'Кол-во cлучаев'], CReportBase.AlignCenter),
                ('7%', ['', u'Кол-во УЕТ'], CReportBase.AlignCenter),
                ('7%', ['', u'Сумма по ОМС, руб'], CReportBase.AlignCenter),
                ('7%', ['', u'Выставленная сумма по ОМС, руб'], CReportBase.AlignCenter),
                ('7%', [u'по работающим', u'Кол-во cлучаев'], CReportBase.AlignCenter),
                ('7%', ['', u'Кол-во УЕТ'], CReportBase.AlignCenter),
                ('7%', ['', u'Сумма по ОМС, руб'], CReportBase.AlignCenter),
                ('7%', ['', u'Выставленная сумма по ОМС, руб'], CReportBase.AlignCenter),
                ]
        else:
            tableColumns = [
                ('36%', [u'Страховщик'], CReportBase.AlignCenter),
                ('8%', [u'Всего', u'Кол-во cлучаев'], CReportBase.AlignCenter),
                ('8%', ['', u'Сумма по ОМС, руб'], CReportBase.AlignCenter),
                ('8%', [u'по неработающим', u'Кол-во cлучаев'], CReportBase.AlignCenter),
                ('8%', ['', u'Кол-во УЕТ'], CReportBase.AlignCenter),
                ('8%', ['', u'Сумма по ОМС, руб'], CReportBase.AlignCenter),
                ('8%', [u'по работающим', u'Кол-во cлучаев'], CReportBase.AlignCenter),
                ('8%', ['', u'Кол-во УЕТ'], CReportBase.AlignCenter),
                ('8%', ['', u'Сумма по ОМС, руб'], CReportBase.AlignCenter)
                ]

        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 2, 1)
        if needExposedSum:
            table.mergeCells(0, 1, 1, 3)
            table.mergeCells(0, 4, 1, 4)
            table.mergeCells(0, 8, 1, 4)
        else:
            table.mergeCells(0, 1, 1, 2)
            table.mergeCells(0, 3, 1, 3)
            table.mergeCells(0, 6, 1, 3)
        reportData['keys'].append('total')
        if needExposedSum:
            keys = ['cntAll', 'sumAll', 'exposedSumAll', 'cntNW', 'uetNW', 'sumNW', 'exposedSumNW', 'cntW', 'uetW',
                    'sumW', 'exposedSumW']
        else:
            keys = ['cntAll', 'sumAll',  'cntNW',  'uetNW',  'sumNW', 'cntW',  'uetW',  'sumW']
        for insurer in reportData['keys']:
            row = table.addRow()
            table.setText(row, 0, insurer if insurer != 'total' else u'Итого',  blockFormat=CReportBase.AlignLeft)
            for i, key in enumerate(keys):
                table.setText(row, i+1, reportData[insurer][key])

        return doc


class CEconomicAnalisysE14Ex(CEconomicAnalisysE14):
    def exec_(self, accountIdList=None):
        self.accountIdList = accountIdList
        CEconomicAnalisysE14.exec_(self)

    def getSetupDialog(self, parent):
        result = CEconomicAnalisysSetupDialog(parent)
        result.setTitle(self.title())
        result.shrink()
        result.loadPrefs()
        return result

    def build(self, params):
        params['accountIdList'] = self.accountIdList
        return CEconomicAnalisysE14.build(self, '\n'.join(self.getDescription(params)), params)
