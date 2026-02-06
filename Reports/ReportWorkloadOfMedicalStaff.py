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

from library.Utils      import forceString, forceInt
from Orgs.Utils         import getOrgStructureFullName, getOrgStructureDescendants
from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable
from Reports.Utils            import dateRangeAsStr

from Reports.ReportPersonSickList import CReportPersonSickListSetupDialog


def _selectData(params):
    db = QtGui.qApp.db
    begDate = params.get('begDate', QDate())
    endDate = params.get('endDate', QDate())
    orgStructureId = params.get('orgStructureId', None)
    specialityId      = params.get('specialityId', None)
    personId = params.get('personId', None)

    tableOrgStructure = db.table('OrgStructure')
    tableSchedule = db.table('Schedule')
    tablePerson = db.table('Person')
    tableRbSpeciality = db.table('rbSpeciality')
    tableVisit = db.table('Visit')


    cols = [tableOrgStructure['name'].alias('orgStrName'),
                tableRbSpeciality['name'].alias('specName'),
                'CONCAT_WS(" ", Person.lastName, Person.firstName, Person.patrName) as personName',
                'MONTH(Schedule.date) AS month',
                'COUNT(DISTINCT Schedule.date) as dates',
                'COUNT(Visit.id) as visits'
    ]
    cond = [tableSchedule['appointmentType'].inlist([1, 2, 3])]
    if begDate and endDate:
        cond.append(tableSchedule['date'].ge(begDate))
        cond.append(tableSchedule['date'].lt(endDate.addDays(1)))
    if orgStructureId:
        cond.append(tablePerson['orgStructure_id'].inlist(getOrgStructureDescendants(params['orgStructureId'])))
    if specialityId:
        cond.append(tablePerson['speciality_id'].eq(specialityId))
    if personId:
        cond.append(tablePerson['id'].eq(personId))

    queryTable = tableSchedule
    queryTable = queryTable.leftJoin(tablePerson, tablePerson['id'].eq(tableSchedule['person_id']))
    queryTable = queryTable.leftJoin(tableOrgStructure, tableOrgStructure['id'].eq(tablePerson['orgStructure_id']))
    queryTable = queryTable.leftJoin(tableRbSpeciality, tableRbSpeciality['id'].eq(tablePerson['speciality_id']))
    queryTable = queryTable.leftJoin(tableVisit, db.joinAnd([tableVisit['person_id'].eq(tablePerson['id']), tableVisit['date'].eq(tableSchedule['date'])]))

    groupBy = u'OrgStructure.id , rbSpeciality.id , Person.id , LEFT(Schedule.date, 7) ORDER BY rbSpeciality.id , Person.id , MONTH(Schedule.date)'

    stmt = db.selectStmtGroupBy(queryTable, cols, cond, groupBy)
    query = db.query(stmt)

    return query


class CReportWorkloadOfMedicalStaff(CReport):
    def __init__(self, parent = None):
        CReport.__init__(self, parent)
        self.setTitle(u'Распределение нагрузки на врачебный персонал')

    def getSetupDialog(self, parent):
        result = CReportPersonSickListSetupDialog(parent)
        result.setSortByExecDateVisible(False)
        result.setAccountPreliminaryVisible(False)
        result.setEventPurposeVisible(False)
        result.setEventTypeVisible(False)
        result.setWorkOrganisationVisible(False)
        result.setSexVisible(False)
        result.setAgeVisible(False)
        result.setMKBFilterVisible(False)
        result.setLocalityVisible(False)
        result.setFilterAttachOrganisationVisible(False)
        result.setFilterAddressOrgStructureVisible(False)
        result.setTitle(self.title())
        return result


    def dumpParams(self, cursor, params):
        description = []
        db = QtGui.qApp.db
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        if begDate and endDate:
            description.append(dateRangeAsStr(u'За период', begDate, endDate))
        orgStructureId = params.get('orgStructureId', None)
        if orgStructureId:
            description.append(u'Подразделение: ' + getOrgStructureFullName(orgStructureId))
        else:
            description.append(u'Подразделение: ЛПУ')
        specialityId      = params.get('specialityId', None)
        if specialityId:
            description.append(u'Специальность: ' + forceString(db.translate('rbSpeciality', 'id', specialityId, 'name')))
        personId = params.get('personId', None)
        if personId:
            description.append(u'Врач: %s'%(forceString(db.translate('vrbPersonWithSpeciality', 'id', personId, 'name'))))
        cursor.movePosition(QtGui.QTextCursor.End)

        columns = [ ('100%', [], CReportBase.AlignLeft) ]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)


    def build(self, params):
        monthList = [u'Январь', u'Февраль', u'Март', u'Апрель', u'Май', u'Июнь', u'Июль', u'Август', u'Сентябрь', u'Октябрь', u'Ноябрь', u'Декабрь']
        monthColumns = []
        for month in monthList:
            monthColumns.append(('2.5%', [month, u'Отработано дней'], CReportBase.AlignRight))
            monthColumns.append(('2.5%', [u'', u'Количество посещений'], CReportBase.AlignRight))
        tableColumns = [
            ('8%', [u'Подразделение', u''], CReportBase.AlignLeft),
            ('8%', [u'Специальность',  u''], CReportBase.AlignLeft),
            ('16%', [u'Врач', u''], CReportBase.AlignLeft),
        ]
        tableColumns = tableColumns + monthColumns
        tableColumns.append(('3.8%', [u'Итого', u'Отработано дней'], CReportBase.AlignRight))
        tableColumns.append(('3.8%', [u'', u'Количество посещений'], CReportBase.AlignRight))

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 2, 1)
        table.mergeCells(0, 2, 2, 1)
        for i, col in enumerate(tableColumns):
            table.mergeCells(0, i+3, 1, 2)
            table.mergeCells(0, i+4, 1, 1)

        query = _selectData(params)

        row = None
        prevPerson = u''
        prevSpec = u''
        totalDatesByPerson = 0
        totalVisitsByPerson = 0
        totalDatesBySpec =  {1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0, 8:0, 9:0, 10:0, 11:0, 12:0, 13:0}
        totalVisitsBySpec =  {1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0, 8:0, 9:0, 10:0, 11:0, 12:0, 13:0}
        totalDatesByMonths = {1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0, 8:0, 9:0, 10:0, 11:0, 12:0, 13:0}
        totalVisitsByMonths = {1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0, 8:0, 9:0, 10:0, 11:0, 12:0, 13:0}
        mapMonthColumn = {1:3, 2:5, 3:7, 4:9, 5:11, 6:13, 7:15, 8:17, 9:19, 10:21, 11:23, 12:25, 13:27}
        while query.next():
            record = query.record()
            orgStrName = forceString(record.value('orgStrName'))
            specName = forceString(record.value('specName'))
            personName = forceString(record.value('personName'))
            month = forceInt(record.value('month'))
            dates = forceInt(record.value('dates'))
            visits = forceInt(record.value('visits'))
            # if prevPerson != personName:
            #     if prevPerson != u'':
            #         table.setText(row, 27, totalDatesByPerson)
            #         table.setText(row, 28, totalVisitsByPerson)
            #         totalDatesByPerson = 0
            #         totalVisitsByPerson = 0
            if prevSpec != specName and prevSpec != u'':
                row = table.addRow()
                table.setText(row, 0, u'Итого по профилю')
                table.mergeCells(row, 0, 1, 3)
                for index, m in enumerate(monthList):
                    table.setText(row,  mapMonthColumn[index+1],  totalDatesBySpec[index+1] if totalDatesBySpec[index+1]!=0 else u'')
                    table.setText(row,  mapMonthColumn[index+1]+1,  totalVisitsBySpec[index+1] if totalVisitsBySpec[index+1]!=0 else u'')
                table.setText(row,  mapMonthColumn[13],  totalDatesBySpec[13] if totalDatesBySpec[13]!=0 else u'')
                table.setText(row,  mapMonthColumn[13]+1,  totalVisitsBySpec[13] if totalVisitsBySpec[13]!=0 else u'')

                totalDatesBySpec =  {1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0, 8:0, 9:0, 10:0, 11:0, 12:0, 13:0}
                totalVisitsBySpec =  {1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0, 8:0, 9:0, 10:0, 11:0, 12:0, 13:0}
            if prevPerson != personName:
                if prevPerson != u'':
                    if totalDatesByPerson:
                        table.setText(row, 27, totalDatesByPerson)
                    if totalVisitsByPerson:
                        table.setText(row, 28, totalVisitsByPerson)
                    totalDatesByPerson = 0
                    totalVisitsByPerson = 0

                row = table.addRow()
                table.setText(row, 0, orgStrName)
                table.setText(row, 1, specName)
                table.setText(row, 2, personName)
            table.setText(row, mapMonthColumn[month], dates)
            totalDatesByMonths[month] += dates
            totalDatesBySpec[month] += dates
            totalDatesByMonths[13] += dates
            totalDatesBySpec[13] += dates
            totalDatesByPerson += dates
            table.setText(row, mapMonthColumn[month]+1, visits)
            totalVisitsByMonths[month] += visits
            totalVisitsBySpec[month] += visits
            totalVisitsByMonths[13] += visits
            totalVisitsBySpec[13] += visits
            totalVisitsByPerson += visits

            prevPerson = personName
            prevSpec = specName

        if totalDatesByPerson and totalVisitsByPerson:
            table.setText(row, 27, totalDatesByPerson)
            table.setText(row, 28, totalVisitsByPerson)
        row = table.addRow()
        table.setText(row, 0, u'Итого по профилю')
        table.mergeCells(row, 0, 1, 3)
        for index, m in enumerate(monthList):
            table.setText(row,  mapMonthColumn[index+1],  totalDatesBySpec[index+1] if totalDatesBySpec[index+1]!=0 else u'')
            table.setText(row,  mapMonthColumn[index+1]+1,  totalVisitsBySpec[index+1] if totalVisitsBySpec[index+1]!=0 else u'')
        table.setText(row,  mapMonthColumn[13],  totalDatesBySpec[13] if totalDatesBySpec[13]!=0 else u'')
        table.setText(row,  mapMonthColumn[13]+1,  totalVisitsBySpec[13] if totalVisitsBySpec[13]!=0 else u'')
        row = table.addRow()
        table.setText(row,  0,  u'Итого')
        table.mergeCells(row, 0, 1, 3)
        for index, month in enumerate(monthList):
            table.setText(row,  mapMonthColumn[index+1],  totalDatesByMonths[index+1] if totalDatesByMonths[index+1]!=0 else u'')
            table.setText(row,  mapMonthColumn[index+1]+1,  totalVisitsByMonths[index+1] if totalVisitsByMonths[index+1]!=0 else u'')
        table.setText(row,  mapMonthColumn[13],  totalDatesByMonths[13] if totalDatesByMonths[13] !=0 else u'')
        table.setText(row,  mapMonthColumn[13]+1,  totalVisitsByMonths[13] if totalVisitsByMonths[13]!=0 else u'')

        return doc
