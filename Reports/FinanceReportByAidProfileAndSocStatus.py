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
from PyQt4.QtCore import QDate, pyqtSignature

from library.Utils      import forceInt, forceString, forceDate, formatSex

from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable
from library.DialogBase import CDialogBase

from Events.Utils                     import getWorkEventTypeFilter
from Events.EventTypeListEditorDialog import CEventTypeListEditorDialog

from Ui_FinanceReportByAidProfileAndSocStatusSetupDialog import Ui_FinanceReportByAidProfileAndSocStatusSetupDialog


def selectData(params):
    db = QtGui.qApp.db

    tableEvent = db.table('Event')
    tableAction = db.table('Action')
    tableClient = db.table('Client')
    tableClientSocStatus = db.table('ClientSocStatus')
    tableClientDocument = db.table('ClientDocument')
    tableDocumentType = db.table('rbDocumentType')
    tableService = db.table('rbService')
    tableSocStatusType = db.table('rbSocStatusType')
    tableServiceProfile = db.table('rbService_Profile')
    tableMedicalAidProfile = db.table('rbMedicalAidProfile')
    tableAccountItem = db.table('Account_Item')

    queryTable = tableEvent
    queryTable = queryTable.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
    queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
    queryTable = queryTable.innerJoin(tableClientSocStatus, tableClientSocStatus['client_id'].eq(tableClient['id']))
    queryTable = queryTable.innerJoin(tableSocStatusType, tableClientSocStatus['socStatusType_id'].eq(tableSocStatusType['id']))
    queryTable = queryTable.innerJoin(tableClientDocument, tableClientDocument['client_id'].eq(tableClient['id']))
    queryTable = queryTable.innerJoin(tableDocumentType, tableClientDocument['documentType_id'].eq(tableDocumentType['id']))
    queryTable = queryTable.innerJoin(tableAccountItem, tableAccountItem['event_id'].eq(tableEvent['id']))
    queryTable = queryTable.innerJoin(tableService, tableAccountItem['service_id'].eq(tableService['id']))
    queryTable = queryTable.innerJoin(tableServiceProfile, tableServiceProfile['master_id'].eq(tableService['id']))
    queryTable = queryTable.innerJoin(tableMedicalAidProfile, tableServiceProfile['medicalAidProfile_id'].eq(tableMedicalAidProfile['id']))

    cols = [ "CONCAT_WS(' ', Client.lastName, Client.firstName, Client.patrName) AS `clientName`",
             'age(Client.birthDate, CURDATE()) AS `clientAge`',  # ТЗ: "Возраст" расчитываем по дате рождения с учетом текущего дня.
             'COUNT(Account_Item.id) AS `accountItems`',
             'SUM(Account_Item.`sum`) AS `accountItemsSum`',
             tableSocStatusType['name'].alias('socStatusName'),
             tableMedicalAidProfile['name'].alias('aidProfileName'),
             tableDocumentType['name'].alias('documentTypeName'),
             tableClient['sex'].alias('clientSex'),
             tableClientDocument['number'],
             tableClientDocument['serial'],
             tableClientDocument['date'],
             tableClientDocument['origin'],
           ]

    cond = [ 'age(Client.birthDate, Action.begDate) BETWEEN %d AND %d' % (params['ageFrom'], params['ageTo']),
             tableEvent['deleted'].eq(0),
             tableAction['deleted'].eq(0),
             tableClient['deleted'].eq(0),
             tableClientDocument['deleted'].eq(0),
             tableClientSocStatus['deleted'].eq(0),
             tableAccountItem['deleted'].eq(0),
           ]
    if params['begDate']:
        cond.append(tableAction['endDate'].ge(params['begDate']))
    if params['endDate']:
        cond.append(tableAction['endDate'].lt(params['endDate'].addDays(1)))
    if params['eventTypeList']:
        cond.append(tableEvent['eventType_id'].inlist(params['eventTypeList']))
    if params['socStatusClassId']:
        cond.append(tableClientSocStatus['socStatusClass_id'].eq(params['socStatusClassId']))
    if params['socStatusTypeId']:
        cond.append(tableClientSocStatus['socStatusType_id'].eq(params['socStatusTypeId']))
    if params['sex']:
        cond.append(tableClient['sex'].eq(params['sex']))

    group = [ tableMedicalAidProfile['id'].name() ]
    if params['detailByClient']:
        group.append(tableClient['id'].name())

    stmt = db.selectStmtGroupBy(queryTable, cols, cond, group, order='NULL')
    query = db.query(stmt)
    while query.next():
        record = query.record()
        data = {}
        data['clientName'] = forceString(record.value('clientName'))
        data['clientAge'] = forceInt(record.value('clientAge'))
        data['clientSex'] = forceInt(record.value('clientSex'))
        data['accountItems'] = forceInt(record.value('accountItems'))
        data['accountItemsSum'] = forceInt(record.value('accountItemsSum'))
        data['socStatusName'] = forceString(record.value('socStatusName'))
        data['aidProfileName'] = forceString(record.value('aidProfileName'))
        data['documentTypeName'] = forceString(record.value('documentTypeName'))
        data['documentSerial'] = forceString(record.value('serial'))
        data['documentNumber'] = forceString(record.value('number'))
        data['documentDate'] = forceDate(record.value('date'))
        data['documentOrigin'] = forceString(record.value('origin'))
        yield data




class CFinanceReportByAidProfileAndSocStatus(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        title = u'Финансовый отчет по профилям мед. помощи и соц. статусу'
        self.setTitle(title, u'Финансовый отчет по профилям мед. помощи и соц. статусу')


    def getSetupDialog(self, parent):
        result = CFinanceReportByAidProfileAndSocStatusSetupDialog(parent)
        result.setTitle(self.title())
        return result


    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        cursor.insertBlock()

        if params['detailByClient']:
            tableColumns = [
                ('5%',  [u'№'], CReportBase.AlignRight),
                ('20%', [u'Ф.И.О'], CReportBase.AlignLeft),
                ('5%',  [u'Пол'], CReportBase.AlignCenter),
                ('5%',  [u'Возраст'], CReportBase.AlignRight),
                ('13%', [u'Соц. статус'], CReportBase.AlignLeft),
                ('13%', [u'Документ УДЛ'], CReportBase.AlignLeft),
                ('13%', [u'Профиль мед. пом.'], CReportBase.AlignLeft),
                ('13%', [u'Кол-во услуг'], CReportBase.AlignLeft),
                ('13%', [u'Сумма по услугам'], CReportBase.AlignLeft),
                ]
        else:
            tableColumns = [
                ('4%',  [u'№'], CReportBase.AlignRight),
                ('24%', [u'Соц. статус'], CReportBase.AlignLeft),
                ('24%', [u'Профиль мед. пом.'], CReportBase.AlignLeft),
                ('24%', [u'Кол-во услуг'], CReportBase.AlignLeft),
                ('24%', [u'Сумма по услугам'], CReportBase.AlignLeft),
                ]

        table = createTable(cursor, tableColumns)
        for reportData in selectData(params):
            row = table.addRow()
            table.setText(row, 0, str(row))
            if params['detailByClient']:
                table.setText(row, 1, reportData['clientName'])
                table.setText(row, 2, formatSex(reportData['clientSex']))
                table.setText(row, 3, reportData['clientAge'])
                table.setText(row, 4, reportData['socStatusName'])
                table.setText(row, 5, reportData['documentTypeName'] + u', '.join([
                    unicode(reportData['documentNumber']),
                    unicode(reportData['documentSerial']),
                    unicode(reportData['documentDate'].toString('yyyy-MM-dd')),
                    unicode(reportData['documentOrigin'])
                    ]))
                table.setText(row, 6, reportData['aidProfileName'])
                table.setText(row, 7, reportData['accountItems'])
                table.setText(row, 8, reportData['accountItemsSum'])
            else:
                table.setText(row, 1, reportData['socStatusName'])
                table.setText(row, 2, reportData['aidProfileName'])
                table.setText(row, 3, reportData['accountItems'])
                table.setText(row, 4, reportData['accountItemsSum'])

        return doc




class CFinanceReportByAidProfileAndSocStatusSetupDialog(CDialogBase, Ui_FinanceReportByAidProfileAndSocStatusSetupDialog):
    def __init__(self, parent=None):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.eventTypeList = []
        self.cmbSocStatusClass.setTable('rbSocStatusClass')
        self.cmbSocStatusType.setTable('rbSocStatusType')
        self.cmbDocumentType.setTable('rbDocumentType')


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate(QDate.currentDate().year(), 1, 1)))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        self.cmbSocStatusClass.setValue(params.get('socStatusClassId', 0))
        self.cmbSocStatusType.setValue(params.get('socStatusTypeId', 0))
        self.cmbDocumentType.setValue(params.get('documentTypeId', 0))
        self.cmbSex.setCurrentIndex(params.get('sex', 0))
        self.edtAgeFrom.setValue(params.get('ageFrom', 0))
        self.edtAgeTo.setValue(params.get('ageTo', 150))
        self.chkDetailByClient.setChecked(params.get('detailByClient', False))
        self.eventTypeList = params.get('eventTypeList', [])
        if self.eventTypeList:
            db = QtGui.qApp.db
            tableET = db.table('EventType')
            records = db.getRecordList(tableET, [tableET['name']], [tableET['deleted'].eq(0), tableET['id'].inlist(self.eventTypeList)])
            nameList = []
            for record in records:
                nameList.append(forceString(record.value('name')))
            self.lblEventTypeList.setText(u','.join(name for name in nameList if name))
        else:
            self.lblEventTypeList.setText(u'не задано')


    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['eventTypeList'] = self.eventTypeList
        result['socStatusClassId'] = self.cmbSocStatusClass.value()
        result['socStatusTypeId'] = self.cmbSocStatusType.value()
        result['documentTypeId'] = self.cmbDocumentType.value()
        result['sex'] = self.cmbSex.currentIndex()
        result['ageFrom'] = self.edtAgeFrom.value()
        result['ageTo'] = self.edtAgeTo.value()
        result['detailByClient'] = self.chkDetailByClient.isChecked()
        return result


    @pyqtSignature('')
    def on_btnEventTypeList_clicked(self):
        self.eventTypeList = []
        self.lblEventTypeList.setText(u'не задано')
        filter = getWorkEventTypeFilter(isApplyActive=True)
        dialog = CEventTypeListEditorDialog(self, filter)
        if dialog.exec_():
            self.eventTypeList = dialog.values()
            if self.eventTypeList:
                db = QtGui.qApp.db
                tableET = db.table('EventType')
                records = db.getRecordList(tableET, [tableET['name']], [tableET['deleted'].eq(0), tableET['id'].inlist(self.eventTypeList)])
                nameList = []
                for record in records:
                    nameList.append(forceString(record.value('name')))
                self.lblEventTypeList.setText(u','.join(name for name in nameList if name))
