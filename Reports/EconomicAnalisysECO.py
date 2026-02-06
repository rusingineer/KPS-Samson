# -*- coding: utf-8 -*-

from PyQt4 import QtGui

from Reports.Report import CReport, createTable
from Reports.ReportBase import CReportBase

from library.Utils import forceString, forceInt, forceDouble
from EconomicAnalisysSetupDialog import CEconomicAnalisysSetupDialog
from EconomicAnalisys import getStmt, colPerson, colStepECO, colKDPD, colAmount, colSUM


class CEconomicAnalisysECO(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Отчет по этапам ЭКО')

    def selectData(self, params):
        cols = [colPerson, colStepECO, colKDPD, colAmount, colSUM]
        colsStmt = u"""select colPerson as person,
        colStepECO as step,
        sum(colAmount) as amount,
        sum(colKD) as kd,
        round(sum(colSUM), 2) as sum
        """
        groupCols = u'colPerson, colStepECO'
        orderCols = u'colPerson, colStepECO'

        # этап ЭКО
        stepECO = params.get('stepECO', None)
        if stepECO:
            steps = {1: 'a', 2: 'b', 3: 'c', 4: 'd', 5: 'e'}
            having = " left(colStepECO, 1) = '%s'" % steps[stepECO]
        else:
            having = u"IFNULL(colStepECO, '') <> ''"

        stmt = getStmt(colsStmt, cols, groupCols, orderCols, params, queryList=['mes'], additionCond=u" and left(rbService.infis, 1) = 'G' and ct.id is not null", having=having)

        db = QtGui.qApp.db
        return db.query(stmt)

    def build(self, description, params):
        reportRowSize = 5
        colsShift = 2
        reportData = {}

        def processQuery(query):
            while query.next():
                record = query.record()
                person = forceString(record.value('person'))
                step = forceString(record.value('step'))
                amount = forceInt(record.value('amount'))
                kd = forceInt(record.value('kd'))
                sum = forceDouble(record.value('sum'))

                key = (person, step)
                reportLine = reportData.setdefault(key, [0] * reportRowSize)
                reportLine[0] += amount
                reportLine[1] += kd
                reportLine[2] += sum

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
            ('30%', [u'Врач'], CReportBase.AlignLeft),
            ('30%', [u'Этап ЭКО'], CReportBase.AlignLeft),
            ('6%', [u'Кол-во услуг'], CReportBase.AlignRight),
            ('10%', [u'Кол-во койко-дней (дней лечения)'], CReportBase.AlignRight),
            ('14%', [u'Сумма'], CReportBase.AlignRight)
        ]

        table = createTable(cursor, tableColumns)
        # table.mergeCells(0, 0, 1, 2)
        for col in xrange(reportRowSize):
            table.mergeCells(0, col, 2, 1)
        totalByReport = [0] * reportRowSize

        keys = reportData.keys()
        keys.sort()
        for key in keys:
            row = table.addRow()
            table.setText(row, 0, key[0])
            table.setText(row, 1, key[1])
            reportLine = reportData[key]
            for col in xrange(reportRowSize - colsShift):
                table.setText(row, col + colsShift, reportLine[col])
                totalByReport[col] = totalByReport[col] + reportLine[col]
        row = table.addRow()
        table.setText(row, 0, u'Итого')
        table.mergeCells(row, 0, 1, 2)
        for col in xrange(reportRowSize - colsShift):
            table.setText(row, col + colsShift, totalByReport[col])

        return doc


class CEconomicAnalisysECOEx(CEconomicAnalisysECO):
    def exec_(self, accountIdList=None):
        self.accountIdList = accountIdList
        CEconomicAnalisysECO.exec_(self)

    def getSetupDialog(self, parent):
        result = CEconomicAnalisysSetupDialog(parent)
        result.setTitle(self.title())
        result.setVisibleWidget('cmbStepECO', True)
        result.setVisibleWidget('lblStepECO', True)
        result.cmbStepECO.addItems([u'Все', u'a-проведение 1 этапа ЭКО(стимуляция суперовуляции)',
                                    u'b-полный цикл ЭКО с криоконсервацией эмбрионов',
                                    u'c-размораживание криоконсервированных эмбрионов с последующим переноссом',
                                    u'd-проведение I-III этапа ЭКО (стимуляция, получение, оплодотворение и культивирование) с последующей криоконсервацией эмбриона',
                                    u'e-полный цикл ЭКО без применения криоконсервации эмбрионов'])
        result.shrink()
        result.loadPrefs()
        return result

    def build(self, params):
        params['accountIdList'] = self.accountIdList
        return CEconomicAnalisysECO.build(self, '\n'.join(self.getDescription(params)), params)