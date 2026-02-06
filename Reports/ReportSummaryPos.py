# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2015 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import QDate

from Reports.EconomicAnalisys import colPos, colObr, colEvent, colUET, colAmount, colSUM, getStmt, colPosType, \
    colMKBCode, colUslSpec, colServiceEndDate, colMedicalTypeCode
from Reports.EconomicAnalisysSetupDialog import CEconomicAnalisysSetupDialog
from Reports.Report import CReport
from Reports.ReportBase import CReportBase, createTable
from library.Utils import forceInt, forceString, forceDouble, forceDate, pyDate


class CReportSummaryPos(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Основные показатели по посещениям')

    def selectData(self, params):
        cols = [colPos, colObr, colPosType, colEvent, colMKBCode, colUslSpec, colUET, colAmount, colSUM, colServiceEndDate, colMedicalTypeCode]
        colsStmt = u"""select colPos, colObr, case when colPosType = 3 then 1 else 0 end isProf, colEvent, colUslSpec, colMKBCode, colUET, colAmount, colSUM, colServiceEndDate, colMedicalTypeCode
        """
        groupCols = ''
        orderCols = ''

        stmt = getStmt(colsStmt, cols, groupCols, orderCols, params)

        db = QtGui.qApp.db
        return db.query(stmt)

    def build(self, description, params):

        reportData = {'keys' : []}
        rowDict = {'singlePos': u'Разовое посещение по заболеванию', 'obr': u'Обращение по заболеванию (2 и более)',  'prof': u'Профилактический прием', 'otherPos': u'Посещения с иными целями', 'total': u'Итого'}

        def processQuery(query):
            defaultVals = {
                        'cnt' : 0, 
                        'uet' : 0, 
                        'sum' : 0, 
                        'cntAll' : 0, 
                    }
            reportData['keys'].append('singlePos')
            reportData['keys'].append('otherPos')
            reportData['keys'].append('obr')
            reportData['keys'].append('prof')
            reportData['keys'].append('total')

            obrDict = {}
            stomPosDict = {}
            
            for k in reportData['keys']:
                reportData.setdefault(k, defaultVals.copy())
                
            total = reportData['total']

            recordList = []

            while query.next():
                record = query.record()
                recordList.append(record)
                obr = forceInt(record.value('colObr'))
                if obr:
                    spec = forceString(record.value('colUslSpec'))
                    mkb = forceString(record.value('colMKBCode'))
                    eventId = forceString(record.value('colEvent'))
                    obrDict[(eventId, mkb, spec)] = 1

            for record in recordList:
                VP = forceString(record.value('colMedicalTypeCode'))
                endDate = forceDate(record.value('colServiceEndDate'))
                if VP in ['31', '32'] and endDate >= QDate(2018, 1, 1):
                    eventId = forceString(record.value('colEvent'))
                    uet = forceDouble(record.value('colUET'))
                    sum = forceDouble(record.value('colSUM'))
                    item = stomPosDict.setdefault((eventId, pyDate(endDate)), [0.0, 0.0])
                    item[0] += sum
                    item[1] += uet


            for record in recordList:
                pos = forceInt(record.value('colPos'))
                obr = forceInt(record.value('colObr'))
                prof = forceInt(record.value('isProf'))
                uet = round(forceDouble(record.value('colUET')), 2)
                sum = round(forceDouble(record.value('colSUM')), 2)
                spec = forceString(record.value('colUslSpec'))
                mkb = forceString(record.value('colMKBCode'))
                eventId = forceString(record.value('colEvent'))
                VP = forceString(record.value('colMedicalTypeCode'))
                endDate = forceDate(record.value('colServiceEndDate'))
                if pos and VP in ['31', '32'] and endDate >= QDate(2018, 1, 1):
                    sum, uet = stomPosDict[(eventId, pyDate(endDate))]
                if obr:
                    key = 'obr'
                    cnt = obr
                elif prof:
                    key = 'prof'
                    cnt = prof
                elif pos and obrDict.get((eventId, mkb, spec), None):
                    key = 'obr'
                    cnt = 0
                elif pos and not obrDict.get((eventId, mkb, spec), None) and mkb[:1] not in ['U', 'V', 'X', 'Y', 'Z']:
                    key = 'singlePos'
                    cnt = pos
                elif pos and not obrDict.get((eventId, mkb, spec), None) and mkb[:1] in ['U', 'V', 'X', 'Y', 'Z']:
                    key = 'otherPos'
                    cnt = pos
                else:
                    key = None
                    cnt = 0
                if key:
                    reportline = reportData[key]
                    reportline['cnt'] += cnt
                    reportline['uet'] += uet
                    reportline['sum'] += sum
                    reportline['cntAll'] += pos
                    total['cnt'] += cnt
                    total['uet'] += uet
                    total['sum'] += sum
                    total['cntAll'] += pos

        query = self.selectData(params)
        processQuery(query)

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertText(description)
        cursor.insertBlock()

        tableColumns = [
            ('30%', u'', CReportBase.AlignCenter),
            ('15%', u'Количество', CReportBase.AlignCenter),
            ('15%', u'УЕТ', CReportBase.AlignCenter),
            ('15%', u'Сумма (руб.)', CReportBase.AlignCenter),
            ('25%', u'Общее количество посещений (первичных и вторичных)', CReportBase.AlignCenter),
            ]

        table = createTable(cursor, tableColumns)
        for repRow in reportData['keys']:
            row = table.addRow()
            table.setText(row, 0, rowDict[repRow], blockFormat=CReportBase.AlignLeft)
            if repRow == 'total':                
                for i, key in enumerate(['uet', 'sum', 'cntAll']):
                    table.setText(row, i+2, round(reportData[repRow][key], 2) if key != 'cntAll' else reportData[repRow][key], blockFormat=CReportBase.AlignRight)
                table.mergeCells(row, 0, 1, 2)
            else:
                for i, key in enumerate(['cnt', 'uet', 'sum', 'cntAll']):
                    table.setText(row, i+1, round(reportData[repRow][key], 2) if key not in ['cnt', 'cntAll'] else reportData[repRow][key], blockFormat=CReportBase.AlignRight)
                
        return doc


class CReportSummaryPosEx(CReportSummaryPos):
    def exec_(self, accountIdList=None):
        self.accountIdList = accountIdList
        CReportSummaryPos.exec_(self)


    def getSetupDialog(self, parent):
        result = CEconomicAnalisysSetupDialog(parent)
        result.setTitle(self.title())
        result.loadPrefs()
        return result


    def build(self, params):
        params['accountIdList'] = self.accountIdList
        return CReportSummaryPos.build(self, '\n'.join(self.getDescription(params)), params)
