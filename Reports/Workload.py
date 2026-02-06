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
from PyQt4.QtCore import *

from library.Utils      import *
from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable, autoMergeHeader
from Reports.EconomicAnalisysSetupDialog import CEconomicAnalisysSetupDialog
from Orgs.Utils         import *

def selectData(begDate, endDate, eventTypeId, personId, orgStructureId):
    db = QtGui.qApp.db
    between = 'between %s and %s' % (db.formatDate(begDate), db.formatDate(endDate))
    adds = ''
    cond = [u'EventModified.modifyDatetime %s' % between]
    if personId:
        cond.append(u'Person.id = %d' % personId)
    if eventTypeId:
        cond.append(u'EventModified.eventType_id = %d' % eventTypeId)
        adds = u' and eventType_id = %d' % eventTypeId
    if orgStructureId:
        cond.append('OrgStructure.id = {}'.format(orgStructureId))
    condStr = db.joinAnd(cond)
    stmt=u"""
select
    Person.code,
    concat_ws(' ', Person.lastName, Person.firstName, Person.patrName) as fio,
    rbPost.name as post,
    OrgStructure.name as org,
    (select count(distinct id) from Event where createPerson_id = Person.id and Event.deleted = 0 and Event.createDateTime %(between)s %(adds)s) as created,
    count(distinct EventModified.id) as edited,
    count(distinct case when EventModified.execDate is not null then EventModified.id else null end) AS closed
from Person
left join Event EventModified on EventModified.modifyPerson_id = Person.id and not EventModified.deleted
left join rbPost on rbPost.id = Person.post_id
left join OrgStructure on OrgStructure.id = Person.orgStructure_id
WHERE Person.deleted=0 AND %(cond)s
GROUP BY Person.id
ORDER BY Person.lastName, Person.firstName, Person.patrName
    """ % {'cond':condStr, 'between': between, 'adds': adds}
    #print stmt
    return db.query(stmt)


class CWorkload(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setPayPeriodVisible(False)
        self.setTitle(u'Выработка')

    def getSetupDialog(self, parent):
        result = CEconomicAnalisysSetupDialog(parent)
        result.setTitle(self.title())
        result.setVisibleWidgets('lblBegDate', 'edtBegDate', 'edtBegTime',
                                 'lblEndDate', 'edtEndDate', 'edtEndTime',
                                 'lblEventType', 'cmbEventType',
                                 'lblPerson', 'cmbPerson',
                                 'lblOrgStructure', 'cmbOrgStructure'
                                 )
        result.buttonBox.button(QtGui.QDialogButtonBox.Ok).setDefault(True)
        result.buttonBox.button(QtGui.QDialogButtonBox.Ok).setAutoDefault(True)
        minWidth = result.edtBegDate.fontMetrics().width('99.99.9999')
        result.edtBegDate.setMinimumSize(minWidth + 50, 0)
        result.loadPrefs()
        return result

    def build(self, params):
        begDate = params.get('begDate', None)
        endDate = params.get('endDate', None)
        begTime = params.get('begTime', QTime())
        endTime = params.get('endTime', QTime())
        begDateTime = QDateTime(begDate, begTime)
        endDateTime = QDateTime(endDate, endTime)
        eventTypeId = params.get('eventType', None)
        personId = params.get('personId', None)
        orgStructureId = params.get('orgStructureId', None)

        reportData = []

        query = selectData(begDateTime, endDateTime, eventTypeId, personId, orgStructureId)

        while query.next():
            record = query.record()
            code = forceString(record.value('code'))
            fio = forceString(record.value('fio'))
            post = forceString(record.value('post'))
            org = forceString(record.value('org'))
            created = forceInt(record.value('created'))
            edited = forceInt(record.value('edited'))
            closed = forceInt(record.value('closed'))
            reportData.append([code, fio, post, org, created, edited, closed])

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        tableColumns = [
            ('10%', [u'Код сотрудника'], CReportBase.AlignLeft),
            ('20%', [u'ФИО сотрудника'], CReportBase.AlignLeft),
            ('20%', [u'Должность'], CReportBase.AlignLeft),
            ('20%', [u'Подразделение'], CReportBase.AlignLeft),
            ('10%', [u'Создано событий'], CReportBase.AlignRight),
            ('10%', [u'Отредактировано событий', u'всего'], CReportBase.AlignRight),
            ('10%', [u'', u'в том числе закрытых'], CReportBase.AlignRight),
        ]

        table = createTable(cursor, tableColumns)
        autoMergeHeader(table, tableColumns)
        totalCnt = [0, 0, 0]

        for row in reportData:
            i = table.addRow()
            for j in xrange(len(row)):
                table.setText(i, j, row[j])
            totalCnt[0] += row[4]
            totalCnt[1] += row[5]
            totalCnt[2] += row[6]

        i = table.addRow()
        table.mergeCells(i, 0, 1, 4)
        table.setText(i, 0, u'всего', CReportBase.TableTotal)
        table.setText(i, 4, totalCnt[0], CReportBase.TableTotal)
        table.setText(i, 5, totalCnt[1], CReportBase.TableTotal)
        table.setText(i, 6, totalCnt[2], CReportBase.TableTotal)
        return doc
