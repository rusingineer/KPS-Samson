# -*- coding: utf-8 -*-

from PyQt4 import QtGui

from Reports.Report import CReport, createTable
from Reports.ReportBase import CReportBase

from library.Utils import forceString, forceInt, forceDouble
from EconomicAnalisysSetupDialog import CEconomicAnalisysSetupDialog
from EconomicAnalisys import (getStmt, colClient, colEvent, colOrgStructure, colMedicalType, colEventType, colFinance,
                              colPerson, colServiceInfis, colServiceName, colCSG, colPos, colObr, colSMP, colKD, colPD,
                              colUET, colAmount, colSUM, colSpecialityOKSOName, colExposedSum)


class CEconomicAnalisysE10(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Э-10 Сводка о выполненных медицинских услугах')
        self.detailList = [u'отделениям', u'услугам врачей', u'типам событий', u'условиям ОМП', u'специальности врача']
        self.detailId = None
        self.accountIdList = None

    def selectData(self, params):
        self.detailId = params.get('detailTo', 0)
        detailCol = []
        detailColName = ''
        if self.detailId == 0:
            detailCol = [colOrgStructure, colFinance]
            detailColName = u"colOrgStructure", u"colFinance"
        elif self.detailId == 1:
            detailCol = [colOrgStructure, colPerson]
            detailColName = u"colOrgStructure", u"colPerson"
        elif self.detailId == 2:
            detailCol = [colFinance, colEventType]
            detailColName = u"colFinance", u"colEventType"
        elif self.detailId == 3:
            detailCol = [colFinance, colMedicalType]
            detailColName = u"colFinance", u"colMedicalType"
        elif self.detailId == 4:
            detailCol = [colFinance, colSpecialityOKSOName]
            detailColName = u"colFinance", u"colSpecialityOKSOName"
        cols = [colClient, colEvent, colServiceInfis, colServiceName,
                colCSG, colPos, colObr, colSMP, colKD, colPD, colUET, colAmount, colSUM, colExposedSum]
        cols.extend(detailCol)
        
        colsStmt = u"""select %s as osname,
        %s as fin,
        colServiceInfis as infis,
        colServiceName as name,
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
        """ % detailColName
        
        groupCols = u'%s, %s, colServiceInfis, colServiceName' % detailColName
        orderCols = u'%s, %s, colServiceInfis, colServiceName' % detailColName
        
        stmt = getStmt(colsStmt, cols, groupCols, orderCols, params)

        return QtGui.qApp.db.query(stmt)

    def build(self, params):
        needExposedSum = params.get('dataType', None) == 3

        reportRowSize = 10 if needExposedSum else 9
        reportData = {}

        def processQuery(query):
            while query.next():
                record = query.record()
                osname = forceString(record.value('osname'))
                fin = forceString(record.value('fin'))
                infis = forceString(record.value('infis'))
                name = forceString(record.value('name'))
                amount = forceInt(record.value('usl'))
                mes = forceInt(record.value('mes'))
                kd = forceInt(record.value('kd'))
                pd = forceInt(record.value('pd'))
                uet = forceDouble(record.value('uet'))
                sums = forceDouble(record.value('sum'))
                exposedSum = forceDouble(record.value('exposedSum'))
                cnt = forceInt(record.value('cnt'))
                pos = forceInt(record.value('pos'))

                key = (osname, fin, infis, name)
                reportLine = reportData.setdefault(key, [0]*reportRowSize)
                reportLine[0] += amount
                reportLine[1] += mes
                reportLine[2] += kd
                reportLine[3] += pd
                reportLine[4] += pos
                reportLine[5] += uet
                reportLine[6] += sums
                reportLine[7] += cnt
                if needExposedSum:
                    reportLine[8] += exposedSum
        query = self.selectData(params)
        processQuery(query)
        # now text
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        description = '\n'.join(self.getDescription(params))
        cursor.insertText(u'по %s\n' % self.detailList[self.detailId])
        cursor.insertText(description)
        cursor.insertBlock()

        tableColumns = [
            ('10%', [u'Услуга', u'Код'], CReportBase.AlignLeft),
            ('30%', ['', u'Наименование'], CReportBase.AlignLeft),
            ('10%', [u'Кол-во услуг'], CReportBase.AlignRight),
            ('5%', [u'Кол-во КСГ'], CReportBase.AlignRight),
            ('10%', [u'Кол-во койко-дней'], CReportBase.AlignRight),
            ('10%', [u'Кол-во дней лечения'], CReportBase.AlignRight),
            ('5%', [u'Кол-во посещений'], CReportBase.AlignRight),
            ('10%', [u'Кол-во УЕТ'], CReportBase.AlignRight),
            ('5%', [u'Сумма'], CReportBase.AlignRight)
            ]
        if needExposedSum:
            tableColumns.append(('5%',  [u'Выставленная сумма'], CReportBase.AlignRight))
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 1, 2)
        for col in xrange(reportRowSize):
            table.mergeCells(0, col, 2, 1)

        totalByFin = [0]*reportRowSize
        totalByOs = [0]*reportRowSize
        totalByReport = [0]*reportRowSize
        colsShift = 2
        prevFin = None
        prevOs = None

        keys = reportData.keys()
        keys.sort()

        def drawTotal(table, total, text):
            row = table.addRow()
            table.setText(row, 1, text + u': кол-во законченных случаев - %s, количество посещений - %s'
                          % (total[7],  total[4]), CReportBase.TableHeader)
            table.mergeCells(row, 0, 1, 2)
            for col in xrange(reportRowSize):
                if col < 7:
                    table.setText(row, col + colsShift, total[col])

        for key in keys:
            osname = key[0]
            fin = key[1]
            infis = key[2]
            name = key[3]

            reportLine = reportData[key]
            if prevFin is not None and prevFin != fin:
                drawTotal(table,  totalByFin, u'%s итого' % prevFin)
                totalByFin = [0]*reportRowSize

            if prevOs is not None and prevOs != osname:
                drawTotal(table,  totalByOs, u'%s итого' % prevOs)
                totalByOs = [0]*reportRowSize

            if prevOs != osname:
                row = table.addRow()
                table.setText(row, 1, osname, CReportBase.TableHeader, CReportBase.AlignCenter)
                table.mergeCells(row, 0, 1, 9)

            if prevFin != fin:
                row = table.addRow()
                table.setText(row, 0, fin, CReportBase.TableHeader)
                table.mergeCells(row, 0, 1, 9)

            row = table.addRow()
            table.setText(row, 0, infis)
            table.setText(row, 1, name)
            for col in xrange(reportRowSize):
                if col < 7:
                    table.setText(row, col + colsShift, reportLine[col])
                totalByReport[col] = totalByReport[col] + reportLine[col]
                totalByFin[col] = totalByFin[col] + reportLine[col]
                totalByOs[col] = totalByOs[col] + reportLine[col]
            prevFin = fin
            prevOs = osname
        # total
        drawTotal(table, totalByFin, u'%s итого' % prevFin)
        drawTotal(table, totalByOs, u'%s итого' % prevOs)
        drawTotal(table, totalByReport, u'Итого')
        return doc


class CEconomicAnalisysE10Ex(CEconomicAnalisysE10):
    def exec_(self, accountIdList=None):
        self.accountIdList = accountIdList
        CEconomicAnalisysE10.exec_(self)

    def getSetupDialog(self, parent):
        result = CEconomicAnalisysSetupDialog(parent)
        result.setTitle(self.title())
        result.setVisibilityProfileBed(True)
        result.setDetailToVisible(True)
        result.setListDetailTo(self.detailList)
        result.shrink()
        result.loadPrefs()
        return result

    def build(self, params):
        params['accountIdList'] = self.accountIdList
        return CEconomicAnalisysE10.build(self, params)
