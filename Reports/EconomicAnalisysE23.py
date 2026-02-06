# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2020 SAMSON Group. All rights reserved.
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

from Reports.Report import CReport, createTable
from Reports.ReportBase import CReportBase

from library.Utils import forceString, forceInt, forceDouble, forceBool, forceDate, pyDate
from EconomicAnalisysSetupDialog import CEconomicAnalisysSetupDialog
from EconomicAnalisys import getStmt, colSpecialityOKSOName, colPosType, colIsAdult, colAmount, colSUM, colPos, \
    colServiceEndDate, colMedicalTypeCode, colUET, colEvent, colExposedSum


class CEconomicAnalisysE23(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Форма Э-23. Выполненные объемы посещений в разрезе специальностей')


    def selectData(self, params):
        cols = [colSpecialityOKSOName, colPosType, colEvent, colIsAdult, colAmount, colSUM, colExposedSum, colPos,
                colUET, colServiceEndDate, colMedicalTypeCode]
        colsStmt = u"""select colSpecialityOKSOName as spec,
        colEvent,
        colPosType as vtype,
        colIsAdult as adult,
        colAmount as cnt,
        round(colSUM, 2) as sum,
        round(colExposedSUM, 2) as exposedSum,
        round(colUET, 2) as uet,
        colServiceEndDate,
        colMedicalTypeCode
        """
        stmt = getStmt(colsStmt, cols, '', '', params, queryList=['action', 'visit'])

        db = QtGui.qApp.db
        return db.query(stmt)


    def build(self, description, params):
        needExposedSum = params.get('dataType', None) == 3

        reportData = {'keys': [], 'total': {
                                    'total': {'diag': [0, 0, 0], 'dn': [0, 0, 0], 'prof': [0, 0, 0], 'dom': [0, 0, 0]},
                                    'adult': {'diag': [0, 0, 0], 'dn': [0, 0, 0], 'prof': [0, 0, 0], 'dom': [0, 0, 0]},
                                    'child': {'diag': [0, 0, 0], 'dn': [0, 0, 0], 'prof': [0, 0, 0], 'dom': [0, 0, 0]}
                                }}

        def processQuery(query):
            stomPosDict = {}
            recordList = []
            while query.next():
                record = query.record()
                recordList.append(record)

            for record in recordList:
                VP = forceString(record.value('colMedicalTypeCode'))
                endDate = forceDate(record.value('colServiceEndDate'))
                if VP in ['31', '32'] and endDate >= QDate(2018, 1, 1):
                    eventId = forceString(record.value('colEvent'))
                    uet = forceDouble(record.value('uet'))
                    sum = forceDouble(record.value('sum'))
                    exposedSum = forceDouble(record.value('exposedSum'))
                    item = stomPosDict.setdefault((eventId, pyDate(endDate)), [0.0, 0.0, 0.0])
                    item[0] += sum
                    item[1] += uet
                    item[2] += exposedSum

            for record in recordList:
                spec = forceString(record.value('spec'))
                if not spec:
                    spec = u'Без специальности'
                vtype = forceString(record.value('vtype'))
                adult = forceBool(record.value('adult'))
                sum = forceDouble(record.value('sum'))
                exposedSum = forceDouble(record.value('exposedSum'))
                cnt = forceInt(record.value('cnt'))
                VP = forceString(record.value('colMedicalTypeCode'))
                endDate = forceDate(record.value('colServiceEndDate'))
                eventId = forceString(record.value('colEvent'))
                if vtype and VP in ['31', '32'] and endDate >= QDate(2018, 1, 1):
                    sum, uet, exposedSum = stomPosDict[(eventId, pyDate(endDate))]
                if spec not in reportData['keys']:
                    reportData['keys'].append(spec)

                reportline = reportData.setdefault(spec,  {
                                    'total': {'diag': [0, 0, 0], 'dn': [0, 0, 0], 'prof': [0, 0, 0], 'dom': [0, 0, 0]},
                                    'adult': {'diag': [0, 0, 0], 'dn': [0, 0, 0], 'prof': [0, 0, 0], 'dom': [0, 0, 0]},
                                    'child': {'diag': [0, 0, 0], 'dn': [0, 0, 0], 'prof': [0, 0, 0], 'dom': [0, 0, 0]}
                                })

                if vtype == '1':
                    vtype_key = 'diag'
                elif vtype == '2':
                    vtype_key = 'dn'
                elif vtype == '3':
                    vtype_key = 'prof'
                elif vtype == '4':
                    vtype_key = 'dom'
                else:
                    vtype_key = None

                if adult:
                    adult_key = 'adult'
                else:
                    adult_key = 'child'

                if vtype_key:
                    reportline[adult_key][vtype_key][0] += cnt
                    reportline[adult_key][vtype_key][1] += sum
                    reportline[adult_key][vtype_key][2] += exposedSum
                    reportline['total'][vtype_key][0] += cnt
                    reportline['total'][vtype_key][1] += sum
                    reportline['total'][vtype_key][2] += exposedSum
                    # total by report
                    reportData['total'][adult_key][vtype_key][0] += cnt
                    reportData['total'][adult_key][vtype_key][1] += sum
                    reportData['total'][adult_key][vtype_key][2] += exposedSum
                    reportData['total']['total'][vtype_key][0] += cnt
                    reportData['total']['total'][vtype_key][1] += sum
                    reportData['total']['total'][vtype_key][2] += exposedSum

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
            ('20%', [u'Специальность'], CReportBase.AlignCenter),
            ('6%', [''], CReportBase.AlignCenter),
            ('6%', [u'Всего', u'лечебно-диагностические'], CReportBase.AlignCenter),
            ('6%', ['', u'диспансерные'], CReportBase.AlignCenter),
            ('6%', ['', u'профилактические'], CReportBase.AlignCenter),
            ('6%', ['', u'на дому'], CReportBase.AlignCenter),
            ('6%', [u'Взрослые', u'лечебно-диагностические'], CReportBase.AlignCenter),
            ('6%', ['', u'диспансерные'], CReportBase.AlignCenter),
            ('6%', ['', u'профилактические'], CReportBase.AlignCenter),
            ('6%', ['', u'на дому'], CReportBase.AlignCenter),
            ('6%', [u'Дети', u'лечебно-диагностические'], CReportBase.AlignCenter),
            ('6%', ['', u'диспансерные'], CReportBase.AlignCenter),
            ('6%', ['', u'профилактические'], CReportBase.AlignCenter),
            ('6%', ['', u'на дому'], CReportBase.AlignCenter),
            ]

        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 2, 2)
        table.mergeCells(0, 2, 1, 4)
        table.mergeCells(0, 6, 1, 4)
        table.mergeCells(0, 10, 1, 4)
        reportData['keys'].append('total')
        for spec in reportData['keys']:
            rl = reportData[spec]
            row = table.addRow()
            if spec != 'total':
                table.setText(row, 0, spec,  blockFormat=CReportBase.AlignLeft)
            else:
                table.setText(row, 0, u'Итого', CReportBase.TableHeader, CReportBase.AlignLeft)
            table.addRow()
            col_n = 1
            table.setText(row, col_n, u'кол-во',  blockFormat=CReportBase.AlignLeft)
            table.setText(row + 1, col_n, u'сумма',  blockFormat=CReportBase.AlignLeft)
            if needExposedSum:
                table.addRow()
                table.setText(row + 2, col_n, u'выставленная сумма', blockFormat=CReportBase.AlignLeft)
            table.mergeCells(row, 0, 3 if needExposedSum else 2, 1)
            for col1 in ['total', 'adult', 'child']:
                for key in ['diag', 'dn', 'prof', 'dom']:
                    col_n += 1
                    table.setText(row, col_n, rl[col1][key][0],  blockFormat=CReportBase.AlignLeft)
                    table.setText(row+1, col_n, rl[col1][key][1],   blockFormat=CReportBase.AlignLeft)
                    if needExposedSum:
                        table.setText(row + 2, col_n, rl[col1][key][2], blockFormat=CReportBase.AlignLeft)

        return doc


class CEconomicAnalisysE23Ex(CEconomicAnalisysE23):
    def exec_(self, accountIdList=None):
        self.accountIdList = accountIdList
        CEconomicAnalisysE23.exec_(self)

    def getSetupDialog(self, parent):
        result = CEconomicAnalisysSetupDialog(parent)
        result.setTitle(self.title())
        result.shrink()
        result.loadPrefs()
        return result

    def build(self, params):
        params['accountIdList'] = self.accountIdList
        return CEconomicAnalisysE23.build(self, '\n'.join(self.getDescription(params)), params)
