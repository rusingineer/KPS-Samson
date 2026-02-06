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
from PyQt4.QtCore import pyqtSignature, QDate

from library.Utils      import forceInt, forceString

from Orgs.Utils         import getOrgStructureDescendants
from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable

from Reports.Ui_DiseasesAnalysisReportSetup import Ui_DiseasesAnalysisReportSetupDialog


class CDiseasesAnalysisReport(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Анализ заболеваний')
        self.setOrientation(QtGui.QPrinter.Landscape)

    def getSetupDialog(self, parent):
        result = CDiseasesAnalysisReportSetup(parent)
        result.setTitle(self.title())
        return result

    def selectData(self, begDate, endDate, orgStructureId, MKBFilter, MKBFrom, MKBTo):
        data = {}
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableDiagnosis = db.table('Diagnosis')
        cond = [tableEvent['deleted'].eq(0),
            tableEvent['execDate'].ge(begDate),
            tableEvent['execDate'].lt(endDate.addDays(1) if endDate else QDate.currentDate())
        ]
        if MKBFilter == 1:
            cond.append(tableDiagnosis['MKB'].ge(MKBFrom))
            cond.append(tableDiagnosis['MKB'].le(MKBTo))
        orgStructureCond = 'is not NULL'
        if orgStructureId:
            orgIds = getOrgStructureDescendants(orgStructureId)
            orgStructureCond = ' in (%s)'% ','.join(map(str, orgIds))
        stmt = u'''
            select COUNT(Event.id) as count,

            CASE (
                select APOS.value from ActionProperty as AP
                    left join ActionPropertyType on ActionPropertyType.id = AP.type_id
                    left join ActionProperty_String as APOS on APOS.id = AP.id
                where
                    AP.action_id = Action.id
                    AND AP.deleted = 0
                    and ActionPropertyType.name = 'Исход госпитализации' LIMIT 1
            )
            WHEN 'Умер' THEN 1 ELSE 0 END as 'dead',

            CASE (select APOS.value from Action as Act
                    left join ActionType as ActT on ActT.id = Act.actionType_id
                    left join ActionProperty as AP on AP.action_id = Act.id
                    left join ActionPropertyType on ActionPropertyType.id = AP.type_id
                    left join ActionProperty_String as APOS on APOS.id = AP.id
                where
                    ActT.flatCode = 'received'
                    and Act.event_id = Action.event_id
                    and Act.deleted = 0
                    and AP.deleted = 0
                    and ActionPropertyType.name = 'Доставлен')
            WHEN 'более 24 часов' THEN 2
            WHEN 'в первые 6 часов' THEN 1
            WHEN 'в течении 7-24 часов' THEN 1
            else 0
            END as 'deliveryTime',

            IF(TO_DAYS(Action.begDate) - TO_DAYS(Event.setDate) > 1, 1, 0 ) as 'moreThenDay',

            (
                select OrgStructure.id from ActionProperty as AP
                    left join ActionPropertyType on ActionPropertyType.id = AP.type_id
                    left join ActionProperty_OrgStructure as APOS on APOS.id = AP.id
                    left join OrgStructure on OrgStructure.id = APOS.value
                where
                    AP.action_id = Action.id
                    and ActionPropertyType.name = 'Отделение'
                    AND AP.deleted = 0
            ) as 'OrgStructureId'

            from Action
            left join ActionType on ActionType.id = Action.actionType_id
            left join Event on Event.id = Action.event_id
            left join Diagnostic on Diagnostic.event_id = Event.id
            left join rbDiagnosisType on rbDiagnosisType.id = Diagnostic.diagnosisType_id
            left join Diagnosis on Diagnostic.diagnosis_id = Diagnosis.id

        where ActionType.flatCode = 'leaved'
            and Action.deleted = 0
            and %s
            and rbDiagnosisType.code = 1

        group by OrgStructureId, dead, deliveryTime, moreThenDay
        having OrgStructureId %s
        '''% (db.joinAnd(cond), orgStructureCond)
        total = [0]*8
        query = db.query(stmt)
        while query.next():
            record = query.record()
            orgId = forceInt(record.value('OrgStructureId'))
            orgStructureName = forceString(db.translate('OrgStructure', 'id', orgId, 'name'))
            count = forceInt(record.value('count'))
            row = data.setdefault(orgStructureName, [0]*8)
            deliveryTime = forceInt(record.value('deliveryTime'))
            if deliveryTime == 1:
                row[1] += count
                total[1] += count
            elif deliveryTime == 2:
                row[2] += count
                total[2] += count
            else:
                row[3] += count
                total[3] += count
            dead = forceInt(record.value('dead'))
            if dead:
                row[4] += count
                total[4] += count
                moreThenDay = forceInt(record.value('moreThenDay'))
                if moreThenDay:
                    row[7] += count
                    total[7] += count
                else:
                    row[6] += count
                    total[6] += count
            row[0] += count
            total[0] += count
            if row[0]:
                row[5] = round(float(row[4])*100/float(row[0]), 2)
        if total[0]:
            total[5] = round(float(total[4])*100/float(total[0]), 2)
        return data, total


    def build(self, params):
        begDate   = params.get('begDate', QDate())
        endDate   = params.get('endDate', QDate())
        orgStructure = params.get('orgStructureId', None)
        MKBFilter = params.get('MKBFilter', 0)
        MKBFrom = params.get('MKBFrom', 'A00')
        MKBTo = params.get('MKBTo', 'Z99')

        tableColumns = [
            ('3%', [u'№', '',  '1'],       CReportBase.AlignRight),
            ('25%', [u'Подразделение',  '',  '2'],  CReportBase.AlignLeft),
            ('9%', [u'Количество больных', '',  '3'],     CReportBase.AlignRight),
            ('9%', [u'Доставлено от начала заболевания через',  u'До суток',  '4'],      CReportBase.AlignRight),
            ('9%', ['', u'Позднее суток', '5'], CReportBase.AlignRight),
            ('9%', ['', u'Без уточнения', '6'], CReportBase.AlignRight),
            ('9%', [u'Умерло (от момента поступления)', u'Всего', '7'],  CReportBase.AlignRight),
            ('9%', ['', u'Летальность %', '8'],  CReportBase.AlignRight),
            ('9%', ['', u'До суток', '9'],  CReportBase.AlignRight),
            ('9%', ['', u'Позднее суток', '10'],  CReportBase.AlignRight),
            ]

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        table = createTable(cursor, tableColumns)

        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 2, 1)
        table.mergeCells(0, 2, 2, 1)
        table.mergeCells(0, 3, 1, 3)
        table.mergeCells(0, 6, 1, 4)

        data, total = self.selectData(begDate, endDate, orgStructure, MKBFilter, MKBFrom, MKBTo)
        orgNames = data.keys()
        orgNames.sort()
        for orgName in orgNames:
            row = data[orgName]
            i = table.addRow()
            table.setText(i, 1, orgName)
            table.setText(i, 0, i-2)
            for j, item in enumerate(row):
                table.setText(i, j+2, item)
        if orgNames:
            i = table.addRow()
            table.setText(i, 0, u'ИТОГО')
            for j, item in enumerate(total):
                table.setText(i, j+2, item)
            table.mergeCells(i, 0, 1, 2)
        return doc


class CDiseasesAnalysisReportSetup(QtGui.QDialog, Ui_DiseasesAnalysisReportSetupDialog):
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
        self.edtMKBFrom.setText(params.get('MKBFrom', 'A00.0'))
        self.edtMKBTo.setText(params.get('MKBTo', 'Z99.9'))
        self.cmbMKBFilter.setCurrentIndex(params.get('MKBFilter', 0))

    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['orgStructureId'] = self.cmbOrgStructure.value()
        result['MKBFilter'] = self.cmbMKBFilter.currentIndex()
        result['MKBFrom']   = unicode(self.edtMKBFrom.text())
        result['MKBTo']     = unicode(self.edtMKBTo.text())
        return result

    @pyqtSignature('int')
    def on_cmbMKBFilter_currentIndexChanged(self, index):
        self.edtMKBFrom.setEnabled(index == 1)
        self.edtMKBTo.setEnabled(index == 1)
