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

from library.Utils      import forceInt, forceString

from Orgs.Utils         import getOrgStructureDescendants
from Reports.ReportBase import CReportBase, createTable
from Reports.Report     import CReport

from Reports.Ui_LengthOfStayReportSetupDialog import Ui_CLengthOfStayReportSetup


class CLengthOfStayReport(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Сроки пребывания больных по отделениям')
        self.setOrientation(QtGui.QPrinter.Landscape)

    def getSetupDialog(self, parent):
        result = CLengthOfStayReportSetup(parent)
        result.setTitle(self.title())
        return result

    def selectData(self, begDate, endDate, orgStructureId, clientMovings):
        data = {}
        db = QtGui.qApp.db
        tableAction = db.table('Action')
        if clientMovings:
            cond = [
                tableAction['endDate'].ge(begDate),
                tableAction['endDate'].lt(endDate.addDays(1) if endDate else QDate.currentDate())
            ]
        else:
            cond = [
                tableAction['begDate'].ge(begDate),
                tableAction['begDate'].lt(endDate.addDays(1) if endDate else QDate.currentDate())
            ]
        orgStructureCond = 'is not NULL'
        if orgStructureId:
            orgIds = getOrgStructureDescendants(orgStructureId)
            orgStructureCond = ' in (%s)'% ','.join(map(str, orgIds))
        flatCode = 'moving' if clientMovings else 'leaved'
        apTypeName = u'Отделение пребывания' if clientMovings else u'Отделение'
        stmt = u'''
            select count(Action.id) as count,
            (
                select OrgStructure.id from ActionProperty as AP
                    left join ActionPropertyType on ActionPropertyType.id = AP.type_id
                    left join ActionProperty_OrgStructure as APOS on APOS.id = AP.id
                    left join OrgStructure on OrgStructure.id = APOS.value
                where
                    AP.action_id = Action.id
                    and OrgStructure.type != 4
                    and ActionPropertyType.name = '%s'

            ) as 'OrgStructureId',

            (
                select rbHospitalBedProfile.name from ActionProperty as AP
                    left join ActionPropertyType on ActionPropertyType.id = AP.type_id
                    left join ActionProperty_rbHospitalBedProfile as APOS on APOS.id = AP.id
                    left join rbHospitalBedProfile on rbHospitalBedProfile.id = APOS.value
                where
                    AP.action_id = Action.id
                    and ActionPropertyType.name = 'Профиль'

            ) as 'Profile',

            SUM(IF(TO_DAYS(Action.endDate) - TO_DAYS(Event.setDate)+1 <= 5, 1, 0 )) as 'less5',
            SUM(IF(TO_DAYS(Action.endDate) - TO_DAYS(Event.setDate)+1 > 5 && TO_DAYS(Action.endDate) - TO_DAYS(Event.setDate)+1 <= 10, 1, 0 )) as 'b6-10',
            SUM(IF(TO_DAYS(Action.endDate) - TO_DAYS(Event.setDate)+1 > 10 && TO_DAYS(Action.endDate) - TO_DAYS(Event.setDate)+1 <= 15, 1, 0 )) as 'b11-15',
            SUM(IF(TO_DAYS(Action.endDate) - TO_DAYS(Event.setDate)+1 > 15 && TO_DAYS(Action.endDate) - TO_DAYS(Event.setDate)+1 <= 20, 1, 0 )) as 'b16-20',
            SUM(IF(TO_DAYS(Action.endDate) - TO_DAYS(Event.setDate)+1 > 20 && TO_DAYS(Action.endDate) - TO_DAYS(Event.setDate)+1 <= 25, 1, 0 )) as 'b21-25',
            SUM(IF(TO_DAYS(Action.endDate) - TO_DAYS(Event.setDate)+1 > 25 && TO_DAYS(Action.endDate) - TO_DAYS(Event.setDate)+1 <= 30, 1, 0 )) as 'b26-30',
            SUM(IF(TO_DAYS(Action.endDate) - TO_DAYS(Event.setDate)+1 > 30 && TO_DAYS(Action.endDate) - TO_DAYS(Event.setDate)+1 <= 35, 1, 0 )) as 'b31-35',
            SUM(IF(TO_DAYS(Action.endDate) - TO_DAYS(Event.setDate)+1 > 35 && TO_DAYS(Action.endDate) - TO_DAYS(Event.setDate)+1 <= 40, 1, 0 )) as 'b36-40',
            SUM(IF(TO_DAYS(Action.endDate) - TO_DAYS(Event.setDate)+1 > 40 && TO_DAYS(Action.endDate) - TO_DAYS(Event.setDate)+1 <= 45, 1, 0 )) as 'b41-45',
            SUM(IF(TO_DAYS(Action.endDate) - TO_DAYS(Event.setDate)+1 > 45, 1, 0 )) as 'more45'


            from Action
            left join ActionType on ActionType.id = Action.actionType_id
            left join Event on Event.id = Action.event_id

        where ActionType.flatCode = '%s'
            and Action.endDate is not NULL
            and %s

        group by OrgStructureId, Profile

        having OrgStructureId %s

        '''% (apTypeName, flatCode, db.joinAnd(cond), orgStructureCond)

        query = db.query(stmt)
        while query.next():
            record = query.record()
            orgId = forceInt(record.value('OrgStructureId'))
            orgStructureName = forceString(db.translate('OrgStructure', 'id', orgId, 'name'))
            profile = forceString(record.value('Profile'))
            if not profile:
                profile = u'Не указан'
            profileRow = data.setdefault(orgStructureName, {})
            row = profileRow.setdefault(profile, [0]*11)
            row[0] = forceInt(record.value('less5'))
            row[1] = forceInt(record.value('b6-10'))
            row[2] = forceInt(record.value('b11-15'))
            row[3] = forceInt(record.value('b16-20'))
            row[4] = forceInt(record.value('b21-25'))
            row[5] = forceInt(record.value('b26-30'))
            row[6] = forceInt(record.value('b31-35'))
            row[7] = forceInt(record.value('b36-40'))
            row[8] = forceInt(record.value('b41-45'))
            row[9] = forceInt(record.value('more45'))
            row[10] = forceInt(record.value('count'))

        return data

    def build(self, params):
        begDate   = params.get('begDate', QDate())
        endDate   = params.get('endDate', QDate())
        orgStructureId = params.get('orgStructureId', None)
        clientMovings = params.get('clientMovings', False)

        tableColumns = [
            ('17%', [u'Подразделение',  '',  '1'],  CReportBase.AlignRight),
            ('17%', [u'Профиль', '',  '2'],     CReportBase.AlignLeft),
            ('6%', [u'Сроки пребывания (суток)',  u'До 5',  '3'],      CReportBase.AlignLeft),
            ('6%', ['', u'6-10', '4'], CReportBase.AlignLeft),
            ('6%', ['', u'11-15', '5'], CReportBase.AlignLeft),
            ('6%', ['', u'16-20', '6'], CReportBase.AlignLeft),
            ('6%', ['', u'21-25', '7'], CReportBase.AlignLeft),
            ('6%', ['', u'26-30', '8'], CReportBase.AlignLeft),
            ('6%', ['', u'31-35', '9'], CReportBase.AlignLeft),
            ('6%', ['', u'36-40', '10'], CReportBase.AlignLeft),
            ('6%', ['', u'41-45', '11'], CReportBase.AlignLeft),
            ('6%', ['', u'Свыше', '12'], CReportBase.AlignLeft),
            ('6%', ['', u'Всего', '13'], CReportBase.AlignLeft)
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
        table.mergeCells(0, 2, 1, 11)

        data = self.selectData(begDate, endDate, orgStructureId, clientMovings)
        orgNames = data.keys()
        orgNames.sort()
        allSum = [0]*11
        for orgStructureName in orgNames:
            profileRow = data[orgStructureName]
            sum = [0]*11
            for profile in profileRow:
                i = table.addRow()
                table.setText(i, 1, profile)
                row = profileRow[profile]
                for j, item in enumerate(row):
                    table.setText(i, j+2, item)
                    sum[j] += item
                    allSum[j] += item
            i = table.addRow()
            table.setText(i, 1, u'Итого', CReportBase.TableTotal)
            for j, item in enumerate(sum):
                table.setText(i, j+2, item, CReportBase.TableTotal)
            profileLen = len(profileRow)
            table.setText(i-profileLen, 0, orgStructureName)
            table.mergeCells(i-profileLen, 0, profileLen+1, 1)
        i = table.addRow()
        for j, item in enumerate(allSum):
            table.setText(i, j+2, item, CReportBase.TableTotal)
        table.setText(i, 0, u'Итого по стационару', CReportBase.TableTotal)
        return doc


class CLengthOfStayReportSetup(QtGui.QDialog, Ui_CLengthOfStayReportSetup):
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
        self.chkClientMoving.setChecked(params.get('clientMovings', False))

    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['orgStructureId'] = self.cmbOrgStructure.value()
        result['clientMovings'] = True if self.chkClientMoving.isChecked() else False
        return result
