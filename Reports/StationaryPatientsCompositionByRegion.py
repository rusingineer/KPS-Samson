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

from library.Utils      import forceDate, forceString

from Reports.ReportBase import CReportBase, createTable
from Reports.Report     import CReport
from Reports.ReportView import CPageFormat

from Ui_StationaryPatientsCompositionByRegionSetupDialog import Ui_StationaryPatientsCompositionByRegionSetupDialog


class CStationaryPatientsCompositionByRegion(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Состав больных в стационаре, сроки и исходы лечения среди выбывших')
        self.orientation = CPageFormat.Landscape

    def getSetupDialog(self, parent):
        result = CStationaryPatientsCompositionByRegionSetup(parent)
        result.setTitle(self.title())
        return result

    def selectData(self, params):
        begDate   = params.get('begDate', QDate())
        endDate   = params.get('endDate', QDate())
        orgStructureIdList = params.get('orgStructureIdList', None)
        data = {}
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableOrgStructure = db.table('OrgStructure')
        cond = [tableEvent['execDate'].ge(begDate),
                    tableEvent['execDate'].lt(endDate.addDays(1))]
        orgStructureCond = u'is not NULL'
        if orgStructureIdList:
            orgStructureCond = u'in (%s)'%','.join(map(str, orgStructureIdList))
        stmt = u'''
            select
                kladr.getOKATOName(kladr.getOkato( AddressHouse.KLADRCode,
                                AddressHouse.KLADRStreetCode,
                                AddressHouse.number)) as 'region',
                getClientCitizenship(Client.id, Event.execDate) as 'citizenship',
                getTownName(AddressHouse.KLADRCode) as 'city',
                (
                    select OrgStructure.id
                        from ActionProperty as AP
                            left join ActionPropertyType AS APT on APT.id = AP.type_id
                            left join ActionProperty_OrgStructure AS APOS on APOS.id = AP.id
                            left join OrgStructure on OrgStructure.id = APOS.value
                        where
                            AP.action_id = Action.id
                            AND AP.deleted = 0
                            and APT.name = 'Отделение'
                            limit 1
                ) as 'orgStructure',
                Event.execDate as 'execDate',
                Event.setDate as 'setDate',
                CASE (
                    select APS.value
                        from ActionProperty as AP
                            left join ActionPropertyType AS APT on APT.id = AP.type_id
                            left join ActionProperty_String AS APS on APS.id = AP.id
                        where
                            AP.action_id = Action.id
                            and APT.name = 'Исход госпитализации'
                            AND AP.deleted = 0
                             limit 1
                )
                WHEN 'Переведен в другой стационар' THEN 'Transfered'
                WHEN 'Умер' THEN 'Dead'
                ELSE 'Leaved'
                END

                    as 'exitStatus',

                CASE rbDResult.name
                    WHEN 'Выздоровление' THEN 'feelFine'
                    WHEN 'Ухудшение' THEN 'youKilledMe'
                    WHEN 'Улучшение' THEN 'muchBetter'
                    ELSE 'whereAmI'
                END
                            as 'result'

            from Event
                left join Diagnostic on Diagnostic.event_id = Event.id
                left join Diagnosis on Diagnosis.id = Diagnostic.diagnosis_id
                left join rbDiagnosisType on rbDiagnosisType.id = Diagnostic.diagnosisType_id
                left join Client on Client.id = Event.client_id
                left join Action on Action.event_id = Event.id
                left join ActionType on ActionType.id = Action.actionType_id
                left join rbDiagnosticResult as rbDResult on rbDResult.id = Diagnostic.result_id
                LEFT JOIN ClientAddress ON ClientAddress.id = (SELECT MAX(id)
                                               FROM ClientAddress AS CA
                                               WHERE CA.type = 0
                                                 AND CA.deleted = 0
                                                 AND CA.client_id = Client.id)
                LEFT JOIN Address ON Address.id = ClientAddress.address_id
                LEFT JOIN AddressHouse ON AddressHouse.id = Address.house_id


            where rbDiagnosisType.code = 1
                and ActionType.flatCode = 'leaved'
                and %s

            having orgStructure %s
        ''' % (db.joinAnd(cond), orgStructureCond)

        query = db.query(stmt)
        while query.next():
            record = query.record()
            orgStructure = forceString(db.translate(tableOrgStructure, 'id', record.value('orgStructure'), 'name'))
            region = forceString(record.value('region'))
            citizenship = forceString(record.value('citizenship'))
            city = forceString(record.value('city'))
            fromDate = forceDate(record.value('setDate'))
            toDate = forceDate(record.value('execDate'))
            exitStatus = forceString(record.value('exitStatus'))
            result = forceString(record.value('result'))

            if fromDate < begDate:
                fromDate = begDate
            kdays = fromDate.daysTo(toDate)
            if not kdays:
                kdays = 1

            if citizenship and citizenship != u'м643':
                region = u'Иностранец'
            elif not region:
                region = city if city else u'Бомж'

            dataByDiag = data.setdefault(orgStructure, {})
            row = dataByDiag.setdefault(region, [0]*14)

            if exitStatus == 'Leaved':
                row[0] += 1
                row[1] += kdays
            elif exitStatus == 'Dead':
                row[3] += 1
                row[5] += kdays
            elif exitStatus == 'Transfered':
                row[7] += 1
                row[8] += kdays

            if result == 'feelFine':
                row[10] += 1
            elif result == 'muchBetter':
                row[11] += 1
            elif result == 'youKilledMe':
                row[12] += 1
            else:
                row[13] += 1

        return data

    def build(self, params):
        tableColumns = [
            #('22%', [u'Подразделение',  '',  '1'],  CReportBase.AlignLeft),
            ('16%', [u'Регион проживания', '',  '1'],     CReportBase.AlignLeft),
            ('6%', [u'Выписано',  u'Всего',  '2'],      CReportBase.AlignRight),
            ('6%', ['', u'Проведено койко-дней', '3'], CReportBase.AlignRight),
            ('6%', ['', u'Средний койко-день', '4'], CReportBase.AlignRight),
            ('6%', [u'Умерло',  u'Всего',  '5'],      CReportBase.AlignRight),
            ('6%', ['', u'Летальность', '6'], CReportBase.AlignRight),
            ('6%', ['', u'Проведено койко-дней', '7'], CReportBase.AlignRight),
            ('6%', ['', u'Средний койко-день', '8'], CReportBase.AlignRight),
            ('6%', [u'Переведено в др. стац.',  u'Всего',  '9'],      CReportBase.AlignRight),
            ('6%', ['', u'Проведено койко-дней', '10'], CReportBase.AlignRight),
            ('6%', ['', u'Средний койко-день', '11'], CReportBase.AlignRight),
            ('6%', [u'Выздоровление', '',  '12'],     CReportBase.AlignRight),
            ('6%', [u'Улучшение', '',  '13'],     CReportBase.AlignRight),
            ('6%', [u'Ухудшение', '',  '14'],     CReportBase.AlignRight),
            ('6%', [u'Прочее', '',  '15'],     CReportBase.AlignRight),
            ]

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        table = createTable(cursor, tableColumns)

        #table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 1, 3)
        table.mergeCells(0, 4, 1, 4)
        table.mergeCells(0, 8, 1, 3)
        table.mergeCells(0, 11, 2, 1)
        table.mergeCells(0, 12, 2, 1)
        table.mergeCells(0, 13, 2, 1)
        table.mergeCells(0, 14, 2, 1)

        fullSum = {}
        data = self.selectData(params)
        i = 0
        for orgStructure in data.keys():
            sum = [0]*14
            keyList = data[orgStructure].keys()
            keyList.sort()
            i = table.addRow()
            table.setText(i, 0, orgStructure, CReportBase.TableTotal, CReportBase.AlignRight)
            table.mergeCells(i, 0, 1, 15)
            for region in keyList:
                fullSumRow = fullSum.setdefault(region, [0]*14)
                row = data[orgStructure][region]
                row[2] = round(row[1]*1.0/row[0], 2) if row[0] else 0
                row[6] = round(row[5]*1.0/row[3], 2) if row[3] else 0
                row[9] = round(row[8]*1.0/row[7], 2) if row[7] else 0
                if row[3]:
                    row[4] = row[0]/row[3]
                i = table.addRow()
                for y, num in enumerate(row):
                    table.setText(i, y+1, num)
                    sum[y] += num
                    fullSumRow[y] += num
                table.setText(i, 0, region)
            i = table.addRow()
            #regionCount = len(data[orgStructure])
            sum[2] = round(sum[1]*1.0/sum[0], 2) if sum[0] else 0
            sum[6] = round(sum[5]*1.0/sum[3], 2) if sum[3] else 0
            sum[9] = round(sum[8]*1.0/sum[7], 2) if sum[7] else 0
            table.setText(i, 0, u'Итого', CReportBase.TableTotal, CReportBase.AlignRight)
            for y, num in enumerate(sum):
                table.setText(i, y+1, num, CReportBase.TableTotal)
        keyList = fullSum.keys()
        keyList.sort()
        i = table.addRow()
        table.setText(i, 0, u'Итого по стационару', CReportBase.TableTotal, CReportBase.AlignRight)
        table.mergeCells(i, 0, 1, 15)
        for region in keyList:
            fullSum[region][2] = round(fullSum[region][1]*1.0/fullSum[region][0], 2) if fullSum[region][0] else 0
            fullSum[region][6] = round(fullSum[region][5]*1.0/fullSum[region][3], 2) if fullSum[region][3] else 0
            fullSum[region][9] = round(fullSum[region][8]*1.0/fullSum[region][7], 2) if fullSum[region][7] else 0
            i = table.addRow()
            table.setText(i, 0, region, CReportBase.TableTotal)
            for y, num in enumerate(fullSum[region]):
                table.setText(i, y+1, num, CReportBase.TableTotal)
        #regionCount = len(fullSum.keys())
        return doc



class CStationaryPatientsCompositionByRegionSetup(QtGui.QDialog, Ui_StationaryPatientsCompositionByRegionSetupDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())

    def setTitle(self, title):
        self.setWindowTitle(title)

    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))

    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['orgStructureIdList'] = self.getOrgStructureIdList()

        return result

    def getOrgStructureIdList(self):
        treeIndex = self.cmbOrgStructure._model.index(self.cmbOrgStructure.currentIndex(), 0, self.cmbOrgStructure.rootModelIndex())
        treeItem = treeIndex.internalPointer() if treeIndex.isValid() else None
        return treeItem.getItemIdList() if treeItem else []
