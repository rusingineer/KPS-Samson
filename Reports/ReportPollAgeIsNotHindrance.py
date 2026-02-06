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

from PyQt4        import QtGui
from PyQt4.QtCore import QDate

from library.Utils        import forceInt, forceString, forceDate, formatSex, formatDate
from Reports.Report       import CReport
from Reports.ReportBase   import CReportBase, createTable
from Reports.ReportView   import CPageFormat
from Reports.Utils        import dateRangeAsStr
from Orgs.Utils           import getOrganisationInfo

from library.DialogBase   import CDialogBase
from library.DateEdit     import CDateEdit


def selectData(params):
    begDate = params.get('begDate', QDate())
    endDate = params.get('endDate', QDate())

    db = QtGui.qApp.db
    tableEvent       = db.table('Event')
    tableAction      = db.table('Action')
    tableActionType  = db.table('ActionType')
    tableClient      = db.table('Client')
    tablePerson      = db.table('vrbPerson')
    tableActionProp  = db.table('ActionProperty')
    tablePropInteger = db.table('ActionProperty_Integer')

    queryTable = tableEvent
    queryTable = queryTable.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
    queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
    queryTable = queryTable.innerJoin(tablePerson, tableEvent['execPerson_id'].eq(tablePerson['id']))
    queryTable = queryTable.innerJoin(tableActionType, tableAction['actionType_id'].eq(tableActionType['id']))
    queryTable = queryTable.innerJoin(tableActionProp, tableActionProp['action_id'].eq(tableAction['id']))
    queryTable = queryTable.innerJoin(tablePropInteger, tableActionProp['id'].eq(tablePropInteger['id']))

    cols = [ tableClient['sex'],
             tableClient['birthDate'],
             tableAction['createDatetime'].alias('pollDate'),
             tablePerson['name'].alias('doctorName'),
             "CONCAT(Client.lastName, ' ', LEFT(Client.firstName, 1), '. ', LEFT(Client.patrName, 1), '.') AS `clientName`",
             'getClientLocAddress(Client.id) AS `clientAddress`'
           ]
    cond = [ tableEvent['deleted'].eq(0),
             tableAction['deleted'].eq(0),
             tableActionType['deleted'].eq(0),
             tableClient['deleted'].eq(0),
             tableAction['status'].eq(2),
             tableActionType['flatCode'].eq('asthenia'),
             tablePropInteger['value'].ge(params['resultFrom']),
             tablePropInteger['value'].le(params['resultTo'])
           ]
    if begDate:
        cond.append(tableAction['createDatetime'].ge(begDate))
    if endDate:
        cond.append(tableAction['createDatetime'].lt(endDate.addDays(1)))

    stmt = db.selectStmt(queryTable, cols, cond)
    query = db.query(stmt)
    while query.next():
        record = query.record()
        clientSex = forceInt(record.value('sex'))
        clientBirthDate = forceDate(record.value('birthDate'))
        pollDate = forceDate(record.value('pollDate'))
        clientName = forceString(record.value('clientName'))
        doctorName = forceString(record.value('doctorName'))
        clientAddress = forceString(record.value('clientAddress'))
        yield { 'name':      clientName,
                'birthDate': formatDate(clientBirthDate),
                'sex':       formatSex(clientSex),
                'address':   clientAddress,
                'doctor':    doctorName,
                'date':      formatDate(pollDate)
              }




class CReportPollAgeIsNotHindrance(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Список пациентов, прошедших опрос «Возраст не помеха»')


    def getSetupDialog(self, parent):
        result = CReportPollAgeIsNotHindranceSetupDialog(parent)
        result.setTitle(self.title())
        return result


    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setBlockFormat(CReportBase.AlignCenter)
        cursor.setCharFormat(CReportBase.ReportBody)

        orgId = QtGui.qApp.currentOrgId()
        orgInfo = getOrganisationInfo(orgId)
        orgName = orgInfo.get('shortName', u'ЛПУ в настройках не указано!')

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(orgName + '\n')
        cursor.insertBlock()
        cursor.insertText(u'Список пациентов, прошедших опрос "Возраст не помеха"\n')
        cursor.insertText(dateRangeAsStr(u'за период', params['begDate'], params['endDate']))
        cursor.insertBlock()
        cursor.insertBlock()

        alignLeft, alignRight, alignCenter = CReportBase.AlignLeft, CReportBase.AlignRight, CReportBase.AlignCenter
        charBold = QtGui.QTextCharFormat()
        charBold.setFontWeight(QtGui.QFont.Bold)

        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.setBlockFormat(alignLeft)
        cursor.insertText(u'Количество баллов: от %s до %s' % (params['resultFrom'], params['resultTo']), charBold)
        cursor.insertBlock()

        tableColumns = [ ('5%',  [u'№'], alignLeft),
                         ('15%', [u'Ф.И.О.'], alignLeft),
                         ('10%', [u'Дата рожд.'], alignLeft),
                         ('5%',  [u'Пол'], alignLeft),
                         ('35%', [u'Адрес проживания'], alignLeft),
                         ('15%', [u'Ф.И.О. врача'], alignLeft),
                         ('15%', [u'Дата опроса'], alignLeft),
                       ]
        table = createTable(cursor, tableColumns)
        for data in selectData(params):
            row = table.addRow()
            table.setText(row, 0, str(row), blockFormat=alignRight)
            table.setText(row, 1, data['name'], blockFormat=alignCenter)
            table.setText(row, 2, data['birthDate'], blockFormat=alignCenter)
            table.setText(row, 3, data['sex'], blockFormat=alignCenter)
            table.setText(row, 4, data['address'])
            table.setText(row, 5, data['doctor'], blockFormat=alignCenter)
            table.setText(row, 6, data['date'], blockFormat=alignCenter)

        return doc


class CReportPollAgeIsNotHindranceSetupDialog(CDialogBase):
    def __init__(self, parent=None):
        CDialogBase.__init__(self, parent)
        self.edtBegDate = CDateEdit()
        self.edtEndDate = CDateEdit()
        self.edtResultFrom = QtGui.QSpinBox()
        self.edtResultTo = QtGui.QSpinBox()

        self.edtResultFrom.setRange(0, 150)
        self.edtResultTo.setRange(0, 150)
        self.edtResultTo.setValue(150)

        buttonBox = QtGui.QDialogButtonBox(self)
        buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout = QtGui.QGridLayout(self)
        layout.addWidget(QtGui.QLabel(u'Дата начала периода'), 0, 0)
        layout.addWidget(self.edtBegDate, 0, 1, 1, 4)
        layout.addWidget(QtGui.QLabel(u'Дата окончания периода'), 1, 0)
        layout.addWidget(self.edtEndDate, 1, 1, 1, 4)
        layout.addWidget(QtGui.QLabel(u'Результат от'), 2, 0)
        layout.addWidget(self.edtResultFrom, 2, 1)
        layout.addWidget(QtGui.QLabel(u'до'), 2, 2)
        layout.addWidget(self.edtResultTo, 2, 3)
        layout.addWidget(QtGui.QLabel(u'баллов'), 2, 4)
        layout.addItem(QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding), 3, 0)
        layout.addItem(QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum), 3, 5)
        layout.addWidget(buttonBox, 4, 0, 1, 6)


    def setTitle(self, title):
        self.setWindowTitle(title)
        self.setObjectName(title)


    def setParams(self, params):
        currentDate = QDate.currentDate()
        self.edtBegDate.setDate(params.get('begDate', QDate(currentDate.year(), 1, 1)))
        self.edtEndDate.setDate(params.get('endDate', currentDate))
        self.edtResultFrom.setValue(params.get('resultFrom', 0))
        self.edtResultTo.setValue(params.get('resultTo', 150))


    def params(self):
        return {
            'begDate':    self.edtBegDate.date(),
            'endDate':    self.edtEndDate.date(),
            'resultFrom':    self.edtResultFrom.value(),
            'resultTo':      self.edtResultTo.value()
        }

