# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2021 SAMSON Group. All rights reserved.
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

from library.Utils       import (forceInt, forceDate, forceDateTime,
                                 forceString, formatName, formatDate, formatDateTime)
from library.DialogBase  import CDialogBase
from Reports.Report      import CReport
from Reports.ReportBase  import CReportBase, createTable
from Events.Utils        import getWorkEventTypeFilter
from Orgs.Utils          import getOrgStructureDescendants
from Reports.Ui_ReportEMDSetupDialog import Ui_ReportEMDSetupDialog


def selectData(params):
    db = QtGui.qApp.db
    tablePost = db.table('rbPost')
    tableEvent = db.table('Event')
    tableAction = db.table('Action')
    tablePerson = db.table('Person')
    tableClient = db.table('Client')
    tableOrgStr = db.table('OrgStructure')
    tableEventType = db.table('EventType')
    tableActionType = db.table('ActionType')
    tableActionExport = db.table('Action_Export')
    tableExternalSystem = db.table('rbExternalSystem')
    tableActionFileAttach = db.table('Action_FileAttach')
    tableFinance = db.table('rbFinance')

    begDate = params.get('begDate')
    endDate = params.get('endDate')
    eventTypeId = params.get('eventTypeId')
    financeId = params.get('financeId')
    orgStructureId = params.get('orgStructureId')
    personId = params.get('personId')
    status = params.get('status')
    onlyInspections = params.get('onlyInspections')
    onlyProtocols = params.get('onlyProtocols')
    detailClients = params.get('detailClients')

    queryTable = tableEvent
    queryTable = queryTable.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
    queryTable = queryTable.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
    queryTable = queryTable.innerJoin(tableActionType, tableAction['actionType_id'].eq(tableActionType['id']))
    queryTable = queryTable.innerJoin(tablePerson, tableAction['person_id'].eq(tablePerson['id']))
    queryTable = queryTable.innerJoin(tableOrgStr, tablePerson['orgStructure_id'].eq(tableOrgStr['id']))
    queryTable = queryTable.innerJoin(tablePost, tablePerson['post_id'].eq(tablePost['id']))
    queryTable = queryTable.leftJoin( tableActionExport, tableActionExport['master_id'].eq(tableAction['id']))
    queryTable = queryTable.leftJoin( tableExternalSystem, tableActionExport['system_id'].eq(tableExternalSystem['id']))
    queryTable = queryTable.leftJoin( tableFinance, tableAction['finance_id'].eq(tableFinance['id']))

    cols = [tableEvent['id'].alias('eventId'),
            tablePerson['firstName'],
            tablePerson['lastName'],
            tablePerson['patrName'],
            tablePerson['federalCode'].alias('personCode'),
            tableActionExport['dateTime'],
            tableEvent['setDate'],
            tableEvent['execDate'],
            tableAction['endDate'],
            tableEventType['name'].alias('eventTypeName'),
            tableOrgStr['name'].alias('orgName'),
            tablePost['name'].alias('postName'),
            tableActionType['name'].alias('actionTypeName'),
            tableFinance['name'].alias('financeName'),
           ]

    cond = [tableEvent['deleted'].eq(0),
            tableEventType['deleted'].eq(0),
            tableAction['deleted'].eq(0),
            tableActionType['deleted'].eq(0),
            tablePerson['deleted'].eq(0),
            tableOrgStr['deleted'].eq(0),
            db.joinOr([tableActionExport['success'].eq(1), tableActionExport['id'].isNull()]),
           ]

    if begDate:
        cond.append(tableAction['endDate'].ge(begDate))
    if endDate:
        cond.append(tableAction['endDate'].lt(endDate.addDays(1)))
    if financeId:
        cond.append(tableFinance['id'].eq(financeId))
    if eventTypeId:
        cond.append(tableEventType['id'].eq(eventTypeId))
    if orgStructureId:
        cond.append(tableOrgStr['id'].inlist(getOrgStructureDescendants(orgStructureId)))
    if personId:
        cond.append(tablePerson['id'].eq(personId))
    if onlyInspections:
        cond.append(db.joinOr([tableActionType['serviceType'].inlist([1, 2]),
                               tableActionType['flatCode'].inlist(['dischargeNote', 'inspection_mse'])]))
    if not onlyProtocols:
        cols.extend([ tableActionFileAttach['path'],
                      tableActionFileAttach['respSigningDatetime'],
                      tableActionFileAttach['orgSigningDatetime'],
                      tableActionFileAttach['createDatetime'].alias('fileAttachDatetime'),
                    ])
        queryTable = queryTable.leftJoin(tableActionFileAttach, tableActionFileAttach['master_id'].eq(tableAction['id']))

        if status == 1:  # подписан
            cond.append(db.joinOr([tableActionFileAttach['respSigningDatetime'].isNotNull(),
                                   tableActionFileAttach['orgSigningDatetime'].isNotNull()]))
        elif status == 2:  # не подписан
            cond.append(tableActionFileAttach['respSigningDatetime'].isNull())
            cond.append(tableActionFileAttach['orgSigningDatetime'].isNull())

    if detailClients:
        cols.extend([ tableClient['firstName'].alias('clientFirstName'),
                      tableClient['lastName'].alias('clientLastName'),
                      tableClient['patrName'].alias('clientPatrName'),
                      tableClient['birthDate'],
                    ])
        queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))

    stmt = db.selectStmt(queryTable, cols, cond)
    query = db.query(stmt)
    while query.next():
        record = query.record()
        reportData = {}
        reportData['eventId']  = forceInt(record.value('eventId'))
        reportData['setDate']  = formatDate(forceDate(record.value('setDate')))
        reportData['execDate'] = formatDate(forceDate(record.value('execDate')))
        reportData['endDate']  = formatDate(forceDate(record.value('endDate')))
        reportData['exportDatetime'] = formatDateTime(forceDateTime(record.value('dateTime')))
        reportData['eventTypeName']  = forceString(record.value('eventTypeName'))
        reportData['orgName']  = forceString(record.value('orgName'))
        reportData['postName'] = forceString(record.value('postName'))
        reportData['actionTypeName'] = forceString(record.value('actionTypeName'))
        reportData['financeName'] = forceString(record.value('financeName'))
        reportData['personCode'] = forceString(record.value('personCode'))

        firstName = forceString(record.value('firstName'))
        lastName = forceString(record.value('lastName'))
        patrName = forceString(record.value('patrName'))
        reportData['personName'] = formatName(lastName, firstName, patrName)

        if detailClients:
            firstName = forceString(record.value('clientFirstName'))
            lastName = forceString(record.value('clientLastName'))
            patrName = forceString(record.value('clientPatrName'))
            reportData['clientName'] = formatName(lastName, firstName, patrName)
            reportData['birthDate'] = formatDate(forceDate(record.value('birthDate')))

        if not onlyProtocols:
            reportData['fileAttachDatetime'] = formatDateTime(forceDateTime(record.value('fileAttachDatetime')))
            reportData['filePath'] = forceString(record.value('path'))

            respSigningDatetime = record.value('respSigningDatetime')
            if not respSigningDatetime.isNull():
                reportData['respSigningDatetime'] = formatDateTime(forceDateTime(respSigningDatetime))
            else:
                reportData['respSigningDatetime'] = u'Документ не подписан врачом'

            orgSigningDatetime = record.value('orgSigningDatetime')
            if not orgSigningDatetime.isNull():
                reportData['orgSigningDatetime'] = formatDateTime(forceDateTime(orgSigningDatetime))
            else:
                reportData['orgSigningDatetime'] = u'Документ не подписан организацией'

        yield reportData



class CReportEMD(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Отчет по ЭМД')


    def getSetupDialog(self, parent):
        result = CReportEMDSetupDialog(parent)
        result.setWindowTitle(self.title())
        return result


    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        onlyProtocols = params.get('onlyProtocols')
        detailClients = params.get('detailClients')

        tableColumns = []
        if detailClients:
            tableColumns.append(('', [u'ФИО пациента'],  CReportBase.AlignCenter))
            tableColumns.append(('', [u'Дата рождения'], CReportBase.AlignCenter))
        tableColumns.append(('', [u'Код обращения'],     CReportBase.AlignRight))
        tableColumns.append(('', [u'Врач исполнитель'],  CReportBase.AlignLeft))
        if not onlyProtocols:
            tableColumns.append(('', [u'Название файла'],          CReportBase.AlignLeft))
            tableColumns.append(('', [u'Дата подписи ЭЦП врачом'], CReportBase.AlignCenter))
            tableColumns.append(('', [u'Дата подписи ЭЦП МО'],     CReportBase.AlignCenter))
        tableColumns.append(('', [u'Дата экспорта действия'], CReportBase.AlignCenter))
        tableColumns.append(('', [u'Дата начала события'],    CReportBase.AlignCenter))
        tableColumns.append(('', [u'Дата закрытия события'],  CReportBase.AlignCenter))
        tableColumns.append(('', [u'Дата закрытия действия'], CReportBase.AlignCenter))
        tableColumns.append(('', [u'Тип действия'],           CReportBase.AlignLeft))
        tableColumns.append(('', [u'Наименование отделения'], CReportBase.AlignLeft))
        tableColumns.append(('', [u'Должность'],              CReportBase.AlignLeft))
        tableColumns.append(('', [u'Тип события'],            CReportBase.AlignLeft))
        if not onlyProtocols:
            tableColumns.append(('', [u'Дата прикрепления файла'], CReportBase.AlignCenter))
        tableColumns.append(('', [u'Тип финансирования'], CReportBase.AlignLeft))
        tableColumns.append(('', [u'Код сотрудника'], CReportBase.AlignLeft))

        table = createTable(cursor, tableColumns)
        for rowdata in selectData(params):
            row = table.addRow()
            col = 0

            if detailClients:
                table.setText(row, col+0, rowdata['clientName'])
                table.setText(row, col+1, rowdata['birthDate'])
                col += 2

            table.setText(row, col+0, rowdata['eventId'])
            table.setText(row, col+1, rowdata['personName'])
            col += 2

            if not onlyProtocols:
                table.setText(row,  col+0, rowdata['filePath'])
                table.setText(row,  col+1, rowdata['respSigningDatetime'])
                table.setText(row,  col+2, rowdata['orgSigningDatetime'])
                col += 3

            table.setText(row, col+0, rowdata['exportDatetime'])
            table.setText(row, col+1, rowdata['setDate'])
            table.setText(row, col+2, rowdata['execDate'])
            table.setText(row, col+3, rowdata['endDate'])
            table.setText(row, col+4, rowdata['actionTypeName'])
            table.setText(row, col+5, rowdata['orgName'])
            table.setText(row, col+6, rowdata['postName'])
            table.setText(row, col+7, rowdata['eventTypeName'])
            col += 8

            if not onlyProtocols:
                table.setText(row, col+0, rowdata['fileAttachDatetime'])
                col += 1

            table.setText(row, col+0, rowdata['financeName'])
            table.setText(row, col+1, rowdata['personCode'])

        return doc



class CReportEMDSetupDialog(CDialogBase, Ui_ReportEMDSetupDialog):
    def __init__(self, parent=None):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.cmbFinance.setTable('rbFinance')
        self.cmbEventType.setTable('EventType', True, filter=getWorkEventTypeFilter(isApplyActive=True))
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())


    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['financeId'] = self.cmbFinance.value()
        result['eventTypeId'] = self.cmbEventType.value()
        result['orgStructureId'] = self.cmbOrgStructure.value()
        result['onlyInspections'] = self.chkOnlyInspections.isChecked()
        result['onlyProtocols'] = self.chkOnlyProtocols.isChecked()
        result['detailClients'] = self.chkDetailClients.isChecked()
        result['personId'] = self.cmbPerson.value()
        result['status'] = self.cmbStatus.currentIndex()
        return result


    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate().addDays(1)))
        self.cmbFinance.setValue(params.get('financeId'))
        self.cmbEventType.setValue(params.get('eventTypeId'))
        self.cmbOrgStructure.setValue(params.get('orgStructureId'))
        self.chkOnlyInspections.setChecked(params.get('onlyInspections', False))
        self.chkOnlyProtocols.setChecked(params.get('onlyProtocols', False))
        self.chkDetailClients.setChecked(params.get('detailClients', False))
        self.cmbPerson.setValue(params.get('personId', None))
        self.cmbStatus.setCurrentIndex(params.get('status', 0))

