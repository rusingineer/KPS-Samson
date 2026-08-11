# -*- coding: utf-8 -*-

from PyQt4 import QtGui

from Reports.Report import CReport, createTable
from Reports.ReportBase import CReportBase

from library.Utils import forceString, forceInt, forceDouble
from EconomicAnalisysSetupDialog import CEconomicAnalisysSetupDialog
from EconomicAnalisys import getStmt, colOrgStructureInfisName, colParentOrgStructureInfisName, colClient, colEvent, \
    colKPK, colCSG, colKD, colPD, colAmount, colSUM, colExposedSum


class CEconomicAnalisysE24(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Э-24. Нагрузка на отделение в разрезе профилей коек')

    def selectData(self, params):
        cols = [colOrgStructureInfisName, colParentOrgStructureInfisName, colClient, colEvent, colKPK, colCSG, colKD,
                colPD, colAmount, colSUM, colExposedSum]
        colsStmt = u"""select colParentOrgStructureInfisName as podr_name,
        colOrgStructureInfisName as osname,
        colKPK as kpk,
        count(distinct colClient) as pac,
        count(distinct colEvent) as cnt,
        sum(colCSG) as mes,
        sum(colKD) as kd,
        sum(colPD) as pd,
        sum(colAmount) as usl,
        round(sum(colSUM), 2) as sum,
        round(sum(colExposedSUM), 2) as exposedSum
        """
        groupCols = u'colParentOrgStructureInfisName, colOrgStructureInfisName, colKPK'
        orderCols = u'colParentOrgStructureInfisName, colOrgStructureInfisName, colKPK'

        stmt = getStmt(colsStmt, cols, groupCols, orderCols, params, queryList=['action', 'mes', 'csg'], isOnlyMES=True)

        db = QtGui.qApp.db
        return db.query(stmt)

    def build(self, description, params):
        needExposedSum = params.get('dataType', None) == 3

        reportRowSize = 9 if needExposedSum else 8
        colsShift = 1
        reportData = {}

        def processQuery(query):
            while query.next():
                record = query.record()
                podr_name = forceString(record.value('podr_name'))
                osname = forceString(record.value('osname'))
                kpk = forceString(record.value('kpk'))
                pac = forceInt(record.value('pac'))
                cnt = forceInt(record.value('cnt'))
                mes = forceInt(record.value('mes'))
                kd = forceInt(record.value('kd'))
                pd = forceInt(record.value('pd'))
                usl = forceInt(record.value('usl'))
                sum = forceDouble(record.value('sum'))
                exposedSum = forceDouble(record.value('exposedSum'))

                if needExposedSum and not mes:
                    # форма по койкам. Убрать все, что не стационар
                    continue

                key = (podr_name, osname, kpk)
                reportLine = reportData.setdefault(key, [0]*reportRowSize)
                reportLine[0] += pac
                reportLine[1] += cnt
                reportLine[2] += mes
                reportLine[3] += kd
                reportLine[4] += pd
                reportLine[5] += usl
                reportLine[6] += sum
                if needExposedSum:
                    reportLine[7] += exposedSum
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
            ('43%',  [u'Подразделение/Отделение/Профиль койки'], CReportBase.AlignLeft),
            ('7%',  [u'Кол-во пациентов'], CReportBase.AlignRight),
            ('7%',  [u'Кол-во случаев'], CReportBase.AlignRight),
            ('7%',  [u'Кол-во КСГ'], CReportBase.AlignRight),
            ('7%',  [u'Кол-во койко-дней'], CReportBase.AlignRight),
            ('7%',  [u'Кол-во дней лечения'], CReportBase.AlignRight),
            ('7%',  [u'Кол-во простых услуг'], CReportBase.AlignRight),
            ('8%',  [u'Сумма'], CReportBase.AlignRight)
            ]
        if needExposedSum:
            tableColumns.append(('7%',  [u'Выставленная сумма'], CReportBase.AlignRight))
        table = createTable(cursor, tableColumns)
        totalByOrgStructure = [0]*reportRowSize
        totalByReport = [0]*reportRowSize

        prev_podr_name = None
        prevOsname = None
        podr_name = None
        osname = None
        prev_row = None

        keys = reportData.keys()
        keys.sort()
        for key in keys:
            podr_name = key[0]
            osname = key[1]
            kpk = key[2]

            if prev_podr_name != podr_name:
                row = table.addRow()
                table.setText(row, 0, podr_name,  CReportBase.TableHeader)
                prev_podr_name = podr_name
                table.mergeCells(row, 0, 1, reportRowSize)
                if prevOsname != osname:
                    if prevOsname is not None:
                        for col in xrange(reportRowSize-colsShift):
                            table.setText(prev_row, col + colsShift, totalByOrgStructure[col])
                            totalByReport[col] = totalByReport[col] + totalByOrgStructure[col]
                        totalByOrgStructure = [0]*reportRowSize
                    row = table.addRow()
                    prev_row = row
                    table.setText(row, 0, u'    ' + osname,  CReportBase.TableHeader)
                    prevOsname = osname

            if prevOsname != osname:
                if prevOsname is not None:
                    for col in xrange(reportRowSize-colsShift):
                        table.setText(prev_row, col + colsShift, totalByOrgStructure[col])
                        totalByReport[col] = totalByReport[col] + totalByOrgStructure[col]
                totalByOrgStructure = [0]*reportRowSize
                row = table.addRow()
                prev_row = row
                table.setText(row, 0, u'    ' + osname,  CReportBase.TableHeader)
                prevOsname = osname
            row = table.addRow()
            table.setText(row, 0, u'        ' + kpk)
            reportLine = reportData[key]
            for col in xrange(reportRowSize-colsShift):
                table.setText(row, col + colsShift, reportLine[col])
                totalByOrgStructure[col] = totalByOrgStructure[col] + reportLine[col]

        if osname is not None and prev_row is not None:
            for col in xrange(reportRowSize-colsShift):
                table.setText(prev_row, col + colsShift, totalByOrgStructure[col])
                totalByReport[col] = totalByReport[col] + totalByOrgStructure[col]
        row = table.addRow()
        table.setText(row, 0, u'Итого')
        for col in xrange(reportRowSize-colsShift):
            table.setText(row, col + colsShift, totalByReport[col])

        return doc


class CEconomicAnalisysE24Ex(CEconomicAnalisysE24):
    def exec_(self, accountIdList=None):
        self.accountIdList = accountIdList
        CEconomicAnalisysE24.exec_(self)

    def getSetupDialog(self, parent):
        result = CEconomicAnalisysSetupDialog(parent)
        result.setTitle(self.title())
        result.shrink()
        result.loadPrefs()
        return result

    def build(self, params):
        params['accountIdList'] = self.accountIdList
        return CEconomicAnalisysE24.build(self, '\n'.join(self.getDescription(params)), params)
