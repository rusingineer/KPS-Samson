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

from library.Utils             import forceInt, forceString, formatName

from Reports.Report            import CReport
from Reports.ReportBase        import CReportBase, createTable

from Reports.Ui_ReportLaboratoryProbeExportImportSetupDialog import Ui_ReportLaboratoryProbeExportImportSetupDialog


def selectData(params):
    begDate = params.get('begDate', QDate())
    endDate = params.get('endDate', QDate())
    type    = params.get('type', 0)

    db = QtGui.qApp.db

    tableProbe = db.table('Probe')
    tableTTJ = db.table('TakenTissueJournal')
    tableClient = db.table('Client')
    tableTest = db.table('rbTest')
    tableEquipment = db.table('rbEquipment')
    tableEquipmentTest = db.table('rbEquipment_Test')

    queryTable = tableProbe
    queryTable = queryTable.leftJoin(tableTTJ, tableTTJ['id'].eq(tableProbe['takenTissueJournal_id']))
    queryTable = queryTable.leftJoin(tableClient, tableClient['id'].eq(tableTTJ['client_id']))
    queryTable = queryTable.leftJoin(tableTest, tableTest['id'].eq(tableProbe['workTest_id']))
    queryTable = queryTable.leftJoin(tableEquipment, tableEquipment['id'].eq(tableProbe['equipment_id']))
    queryTable = queryTable.leftJoin(tableEquipmentTest, db.joinAnd([
                                                    tableEquipmentTest['equipment_id'].eq(tableEquipment['id']),
                                                    tableEquipmentTest['test_id'].eq(tableTest['id']),
                                                    tableEquipmentTest['specimenType_id'].eq(tableProbe['specimenType_id'])]))

    prefix = 'import' if type else 'export'

    cond = [tableProbe[prefix+'Datetime'].ge(begDate),
            tableProbe[prefix+'Datetime'].lt(endDate.addDays(1))]

    fields = [tableTest['code'].alias('testCode'),
              tableTest['name'].alias('testName'),
              tableEquipment['code'].alias('equipmentCode'),
              tableEquipmentTest['hardwareTestCode'].name(),
              tableProbe[prefix+'Name'].alias('fileName'),
              tableProbe['externalId'].alias('probeExternalId'),
              tableClient['id'].alias('clientId'),
              tableClient['lastName'].name(),
              tableClient['firstName'].name(),
              tableClient['patrName'].name()]

    if type:
        fields.extend([tableProbe['result1'].name(),
                       tableProbe['result2'].name(),
                       tableProbe['result3'].name(),
                       tableProbe['resultIndex'].name(),
                       tableProbe['norm'].name(),
                       tableProbe['externalNorm'].name()])


    stmt = db.selectStmt(queryTable, fields, cond)
#    print stmt
    return db.query(stmt)



class CReportLaboratoryProbeExportImport(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Отчет о выполнении экспорта/импорта лабораторных проб')

    def getSetupDialog(self, parent):
        result = CLocSetupDialog(parent)
        result.setTitle(self.title())
        return result


    def getReportData(self, query, type, group):
        reportData = {}

        while query.next():
            record = query.record()

            testCode = forceString(record.value('testCode'))
            testName = forceString(record.value('testName'))
            equipmentCode = forceString(record.value('equipmentCode'))
            hardwareTestCode = forceString(record.value('hardwareTestCode'))
            fileName = forceString(record.value('fileName'))

            valueList = (testCode, testName, equipmentCode, hardwareTestCode, fileName)

            if type:
                result1 = forceString(record.value('result1'))
                result2 = forceString(record.value('result2'))
                result3 = forceString(record.value('result3'))
                resultIndex = forceInt(record.value('resultIndex'))
                norm = forceString(record.value('norm'))
                externalNorm = forceString(record.value('externalNorm'))

                result = (u'', result1, result2, result3)[resultIndex] if resultIndex < 4 else u''
                norm = norm or externalNorm

                valueList += (result, norm)

            if group:
                groupField = forceString(record.value('probeExternalId'))
            else:
                clientId = forceString(record.value('clientId'))
                lastName = forceString(record.value('lastName'))
                firstName = forceString(record.value('firstName'))
                patrName = forceString(record.value('patrName'))
                groupField = formatName(lastName, firstName, patrName) + ' - ' + clientId

            reportData.setdefault(groupField, []).append(valueList)

        return reportData





    def build(self, params):
        def _formatTitle(params):
            return u'Отчет о выполнении %s лабораторных проб\nГруппировка по %s'%({0:u'экспорта', 1:u'импорта'}[params['type']], {0:u'по пациенту', 1:u'заказу'}[params['group']])

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(_formatTitle(params))
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        tableColumns = [
            ( '25%', [u'Группа'], CReportBase.AlignLeft),
            ( '3%',  [u'№ пп'], CReportBase.AlignRight),
            ( '10%', [u'Код пробы'], CReportBase.AlignLeft),
            ( '10%', [u'Наименование пробы'], CReportBase.AlignLeft),
            ( '10%', [u'Код оборудования'], CReportBase.AlignLeft),
            ( '10%', [u'Аппаратный код теста'], CReportBase.AlignLeft),
            ( '10%', [u'Имя'], CReportBase.AlignRight)
                       ]
        if params['type']:
            tableColumns.extend([( '10%',  [u'Результат'], CReportBase.AlignRight), ( '10%',  [u'Норма'], CReportBase.AlignRight)])

        table = createTable(cursor, tableColumns)

        query = selectData(params)

        reportData = self.getReportData(query, params['type'], params['group'])

        keys = reportData.keys()
        keys.sort()

        mergeLenghtList = []

        for key in keys:
            i = table.addRow()
            table.setText(i, 0, key)
            keyReportData = reportData[key]
            valueListCount = len(keyReportData)

            mergeLenght = (i, )

            for i_valueList, valueList in enumerate(keyReportData):
                table.setText(i, 1, i)
                for idx, value in enumerate(valueList):
                    table.setText(i, 2+idx, value)
                if i_valueList != valueListCount-1:
                    i = table.addRow()
                else:
                    mergeLenght += (i-mergeLenght[0]+1, )
                    mergeLenghtList.append(mergeLenght)

        for mergeLenght in mergeLenghtList:
            table.mergeCells(mergeLenght[0], 0, mergeLenght[1], 1)

        return doc




class CLocSetupDialog(Ui_ReportLaboratoryProbeExportImportSetupDialog, QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)

    def setTitle(self, title):
        self.setWindowTitle(title)

    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        self.cmbType.setCurrentIndex(params.get('type', 0))
        self.cmbGroup.setCurrentIndex(params.get('group', 0))

    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['type'] = self.cmbType.currentIndex()
        result['group'] = self.cmbGroup.currentIndex()
        return result





