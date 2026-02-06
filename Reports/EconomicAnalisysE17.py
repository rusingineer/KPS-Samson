# -*- coding: utf-8 -*-

from PyQt4 import QtGui

from Reports.Report import CReport, createTable
from Reports.ReportBase import CReportBase

from library.Utils import forceString, forceInt, forceDouble
from EconomicAnalisysSetupDialog import CEconomicAnalisysSetupDialog
from EconomicAnalisys import getStmt, colClient, colEvent, colPerson, colServiceInfis, colServiceName, colCSG, colPos, \
    colObr, colSMP, colKD, colPD, colUET, colAmount, colSUM, colExposedSum


class CEconomicAnalisysE17(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Э-17. Выполненные объемы услуг по врачам')


    def selectData(self, params):
        cols = [colClient, colEvent, colPerson, colServiceInfis, colServiceName, colCSG, colPos, colObr, colSMP, colKD,
                colPD, colUET, colAmount, colSUM, colExposedSum]
        colsStmt = u"""select colPerson as person,
        colServiceInfis as infis,
        colServiceName as name,
        count(distinct colEvent) as cnt,
        count(distinct colClient) as fl,
        sum(colAmount) as amount,
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
        groupCols = u'colPerson, colServiceInfis, colServiceName'
        orderCols = u'colPerson, colServiceInfis, colServiceName'

        stmt = getStmt(colsStmt, cols, groupCols, orderCols, params)

        return QtGui.qApp.db.query(stmt)
        

    def build(self, description, params):
        needExposedSum = params.get('dataType', None) == 3

        reportRowSize = 21 if needExposedSum else 15
        reportData = {}

        def processQuery(query):
            while query.next():
                record = query.record()
                person = forceString(record.value('person'))
                infis = forceString(record.value('infis'))
                name = forceString(record.value('name'))
                amount = forceInt(record.value('amount'))
                kd = forceInt(record.value('kd'))
                pd = forceInt(record.value('pd'))
                uet = forceDouble(record.value('uet'))
                sum = forceDouble(record.value('sum'))
                exposedSum = forceDouble(record.value('exposedSum'))
                mes = forceInt(record.value('mes'))
                pos = forceInt(record.value('pos'))
                obr = forceInt(record.value('obr'))
                usl = forceInt(record.value('usl'))
                callambulance = forceInt(record.value('callambulance'))

                shiftExposedSum = 1 if needExposedSum else 0
                key = (person if person else u'Не задано', infis,   name)
                reportLine = reportData.setdefault(key, [0]*reportRowSize)
                reportLine[0] += amount
                reportLine[1] += kd
                reportLine[2] += pd
                reportLine[3] += uet
                reportLine[4] += sum
                if needExposedSum:
                    reportLine[5] += exposedSum
                reportLine[5+shiftExposedSum] += mes
                reportLine[6+shiftExposedSum] += pos
                reportLine[7+shiftExposedSum] += obr
                reportLine[8+shiftExposedSum] += usl
                reportLine[9+shiftExposedSum] += callambulance
                if mes > 0:
                    if needExposedSum:
                        reportLine[11] += sum
                        reportLine[12] += exposedSum
                    else:
                        reportLine[10] += sum
                if pos > 0:
                    if needExposedSum:
                        reportLine[13] += sum
                        reportLine[14] += exposedSum
                    else:
                        reportLine[11] += sum
                if obr > 0:
                    if needExposedSum:
                        reportLine[15] += sum
                        reportLine[16] += exposedSum
                    else:
                        reportLine[12] += sum
                if usl > 0:
                    if needExposedSum:
                        reportLine[17] += sum
                        reportLine[18] += exposedSum
                    else:
                        reportLine[13] += sum
                if callambulance > 0:
                    if needExposedSum:
                        reportLine[19] += sum
                        reportLine[20] += exposedSum
                    else:
                        reportLine[14] += sum

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
            ('40%',  ['', u'Наименование'], CReportBase.AlignLeft),
            ('10%',  [u'Кол-во услуг'], CReportBase.AlignRight),
            ('10%',  [u'Кол-во койко-дней'], CReportBase.AlignRight),
            ('10%',  [u'Кол-во дней лечения'], CReportBase.AlignRight),
            ('10%',  [u'Кол-во УЕТ'], CReportBase.AlignRight),
            ('5%',  [u'Сумма'], CReportBase.AlignRight),
            ]
        if needExposedSum:
            tableColumns.append(('5%',  [u'Выставленная сумма'], CReportBase.AlignRight))
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 1, 2)
        table.mergeCells(1, 2, 1, reportRowSize-5)
        totalByPerson = [0]*reportRowSize
        totalByReport = [0]*reportRowSize
        colsShift = 2
        prevPerson = None
        person = None

        keys = reportData.keys()
        keys.sort()

        # чтобы не повторять кусок кода, надо будет улучшить
        def drawTotal(table,  totalByPerson):
            shiftExposedSum = 1 if needExposedSum else 0
            row = table.addRow()

            table.setText(row, 1, u'кол-во КСГ', CReportBase.TableHeader,  CReportBase.AlignRight)
            table.setText(row, 2, totalByPerson[5+shiftExposedSum],  CReportBase.TableHeader,  CReportBase.AlignLeft)
            if needExposedSum:
                table.setText(row, 6, totalByPerson[11], CReportBase.TableHeader)
                table.setText(row, 7, totalByPerson[12], CReportBase.TableHeader)
            else:
                table.setText(row, 6, totalByPerson[10],  CReportBase.TableHeader)
            row = table.addRow()
            table.setText(row, 1, u'кол-во посещений', CReportBase.TableHeader,  CReportBase.AlignRight)
            table.setText(row, 2, totalByPerson[6+shiftExposedSum],  CReportBase.TableHeader,  CReportBase.AlignLeft)
            if needExposedSum:
                table.setText(row, 6, totalByPerson[13], CReportBase.TableHeader)
                table.setText(row, 7, totalByPerson[14], CReportBase.TableHeader)
            else:
                table.setText(row, 6, totalByPerson[11],  CReportBase.TableHeader)
            row = table.addRow()
            table.setText(row, 1, u'кол-во обращений', CReportBase.TableHeader,  CReportBase.AlignRight)
            table.setText(row, 2, totalByPerson[7+shiftExposedSum],  CReportBase.TableHeader,  CReportBase.AlignLeft)
            if needExposedSum:
                table.setText(row, 6, totalByPerson[15], CReportBase.TableHeader)
                table.setText(row, 7, totalByPerson[16], CReportBase.TableHeader)
            else:
                table.setText(row, 6, totalByPerson[12],  CReportBase.TableHeader)
            row = table.addRow()
            table.setText(row, 1, u'кол-во простых услуг', CReportBase.TableHeader,  CReportBase.AlignRight)
            table.setText(row, 2, totalByPerson[8+shiftExposedSum],  CReportBase.TableHeader,  CReportBase.AlignLeft)
            if needExposedSum:
                table.setText(row, 6, totalByPerson[17], CReportBase.TableHeader)
                table.setText(row, 7, totalByPerson[18], CReportBase.TableHeader)
            else:
                table.setText(row, 6, totalByPerson[13],  CReportBase.TableHeader)
            row = table.addRow()
            table.setText(row, 1, u'кол-во вызовов СМП', CReportBase.TableHeader,  CReportBase.AlignRight)
            table.setText(row, 2, totalByPerson[9+shiftExposedSum],  CReportBase.TableHeader,  CReportBase.AlignLeft)
            if needExposedSum:
                table.setText(row, 6, totalByPerson[19], CReportBase.TableHeader)
                table.setText(row, 7, totalByPerson[20], CReportBase.TableHeader)
            else:
                table.setText(row, 6, totalByPerson[14],  CReportBase.TableHeader)

        colLessThan = 6 if needExposedSum else 5
        for key in keys:
            person = key[0]
            uslugaKod = key[1]
            usluga = key[2]

            if prevPerson != person:
                if prevPerson is not None:
                    row = table.addRow()
                    table.setText(row, 0, u'Итого по врачу %s' % prevPerson)
                    for col in xrange(reportRowSize):
                        if col < colLessThan:
                            table.setText(row, col + colsShift, totalByPerson[col])
                        totalByReport[col] = totalByReport[col] + totalByPerson[col]
                    drawTotal(table,  totalByPerson)
                    totalByPerson = [0]*reportRowSize

                row = table.addRow()
                table.setText(row, 0, u'Врач: %s' % person,  CReportBase.TableHeader)
                table.mergeCells(row, 0, 1, 8 if needExposedSum else 7)
                prevPerson = person

            row = table.addRow()
            table.setText(row, 0, uslugaKod)
            table.setText(row, 1, usluga)
            reportLine = reportData[key]
            for col in xrange(reportRowSize):
                if col < colLessThan:
                    table.setText(row, col + colsShift, reportLine[col])
                totalByPerson[col] = totalByPerson[col] + reportLine[col]
        if prevPerson != person:
            if prevPerson is not None:
                row = table.addRow()
                table.setText(row, 0, u'Итого по врачу %s' % prevPerson)
                for col in xrange(reportRowSize):
                    if col < colLessThan:
                        table.setText(row, col + colsShift, totalByPerson[col])
                    totalByReport[col] = totalByReport[col] + totalByPerson[col]

        if prevPerson is not None:
            row = table.addRow()
            table.setText(row, 0, u'Итого по врачу %s' % prevPerson)
            for col in xrange(reportRowSize):
                if col < colLessThan:
                    table.setText(row, col + colsShift, totalByPerson[col])
                totalByReport[col] = totalByReport[col] + totalByPerson[col]
            drawTotal(table,  totalByPerson)
        row = table.addRow()
        table.setText(row, 0, u'Итого')
        for col in xrange(reportRowSize):
            if col < colLessThan:
                table.setText(row, col + colsShift, totalByReport[col])
        drawTotal(table, totalByReport)
        return doc


class CEconomicAnalisysE17Ex(CEconomicAnalisysE17):
    def exec_(self, accountIdList=None):
        self.accountIdList = accountIdList
        CEconomicAnalisysE17.exec_(self)

    def getSetupDialog(self, parent):
        result = CEconomicAnalisysSetupDialog(parent)
        result.setTitle(self.title())
        result.shrink()
        result.loadPrefs()
        return result

    def build(self, params):
        params['accountIdList'] = self.accountIdList
        return CEconomicAnalisysE17.build(self, '\n'.join(self.getDescription(params)), params)
