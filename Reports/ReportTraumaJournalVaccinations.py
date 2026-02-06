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

from library.Utils      import forceString, forceInt, forceStringEx
from library.DialogBase import CDialogBase

from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable
from Reports.ReportView import CPageFormat
from Reports.Utils      import dateRangeAsStr

from Reports.Ui_ReportTraumaJVSetupDialog import Ui_ReportTraumaJVSetupDialog


def selectData(params):
    begDate = params.get('begDate', QDate())
    endDate = params.get('endDate', QDate())
    byPeriodIssueDate = params.get('byPeriodIssueDate', 0)
    db = QtGui.qApp.db
    tableAction        = db.table('Action')
    tableActionType    = db.table('ActionType')
    tableEvent        = db.table('Event')
    tableActionPropertyType = db.table('ActionPropertyType')
    tableClient = db.table('Client')
    tableActionPropertyBoolean = db.table('ActionProperty_Boolean')
    cond = [tableAction['deleted'].eq(0),
            tableEvent['deleted'].eq(0),
            tableClient['deleted'].eq(0),
            tableActionType['deleted'].eq(0),
            tableActionType['flatCode'].eq(u'trauma'),
            tableActionPropertyType['actionType_id'].eq(tableAction['actionType_id']),
            tableActionPropertyType['descr'].eq(u'Прививка'),
            tableActionPropertyBoolean['value'].eq(1)
            ]
    if byPeriodIssueDate and (begDate or endDate):
        cond.append(u'''(%s(SELECT APD.value FROM ActionProperty AS AP
                            INNER JOIN ActionPropertyType AS APT ON APT.id = AP.type_id
                            INNER JOIN ActionProperty_Date AS APD ON APD.id = AP.id
                            WHERE APT.actionType_id = Action.actionType_id AND APT.descr = 'Дата происшествия'
                            AND Action.id = AP.action_id AND APT.deleted = 0 AND AP.deleted = 0)%s)'''
                            %((u'DATE(%s) <= ' % db.formatDate(begDate)) if begDate else u'', (u' <= DATE(%s)'%db.formatDate(endDate) if endDate else u'')))
    elif not byPeriodIssueDate:
        if begDate:
            cond.append(tableAction['begDate'].ge(begDate))
        if endDate:
            cond.append(tableAction['begDate'].lt(endDate.addDays(1)))

    condSTR = db.joinAnd(cond)
    stmt = u"""
SELECT
    Client.id AS clientId,
    vrbPerson.name AS personName,
    CONCAT(Client.lastName, " ", Client.firstName, " ", Client.patrName) as clientName,
    Client.sex AS clientSex,
    Client.birthDate AS clientBirthDate,
    age(Client.birthDate, Action.endDate) AS clientAge,
    Action.endDate,
    getClientRegAddress(Client.id) AS regAddress,
    getClientLocAddress(Client.id) AS locAddress,
    (SELECT GROUP_CONCAT(ClientContact.contact)
     FROM ClientContact INNER JOIN rbContactType ON rbContactType.id = ClientContact.contactType_id
     WHERE ClientContact.client_id = Client.id AND rbContactType.name LIKE '%%телефон%%') AS phones,
    (SELECT APSMKB.value
     FROM ActionProperty AS APMKB
      INNER JOIN ActionPropertyType AS APTMKB ON APTMKB.id = APMKB.type_id
      INNER JOIN ActionProperty_String AS APSMKB ON APSMKB.id = APMKB.id
     WHERE APTMKB.actionType_id = Action.actionType_id AND APTMKB.descr = 'Диагноз происшествия' AND APMKB.action_id = Action.id
      AND APTMKB.deleted = 0 AND APMKB.deleted = 0
    LIMIT 1) AS MKB,
    (SELECT APSJV.value
     FROM ActionProperty AS APJV
      INNER JOIN ActionPropertyType AS APTJV ON APTJV.id = APJV.type_id
      INNER JOIN ActionProperty_String AS APSJV ON APSJV.id = APJV.id
     WHERE APTJV.actionType_id = Action.actionType_id AND APTJV.descr = 'Наименование вакцины' AND APJV.action_id = Action.id
      AND APTJV.deleted = 0 AND APJV.deleted = 0
    LIMIT 1) AS vaccinaName,
    (SELECT APSSR.value
     FROM ActionProperty AS APSR
      INNER JOIN ActionPropertyType AS APTSR ON APTSR.id = APSR.type_id
      INNER JOIN ActionProperty_String AS APSSR ON APSSR.id = APSR.id
     WHERE APTSR.actionType_id = Action.actionType_id AND APTSR.descr = 'Серия вакцины' AND APSR.action_id = Action.id
      AND APTSR.deleted = 0 AND APSR.deleted = 0
    LIMIT 1) AS  vaccinaSeria
FROM
    Action
    INNER JOIN ActionType ON ActionType.id = Action.actionType_id
    INNER JOIN Event ON Event.id = Action.event_id
    INNER JOIN vrbPerson ON vrbPerson.id = Action.person_id
    INNER JOIN Client ON Client.id = Event.client_id
    INNER JOIN ActionProperty ON ActionProperty.action_id = Action.id
    INNER JOIN ActionPropertyType ON ActionPropertyType.id = ActionProperty.type_id
    INNER JOIN ActionProperty_Boolean ON ActionProperty_Boolean.id = ActionProperty.id
WHERE %s
ORDER BY Client.lastName, Client.firstName, Client.patrName
    """%(condSTR)
    return db.query(stmt)


class CReportTraumaJournalVaccinations(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Журнал прививок')
        self.orientation = CPageFormat.Landscape


    def getSetupDialog(self, parent):
        result = CReportTraumaJVSetupDialog(parent)
        result.setTitle(self.title())
        return result


    def dumpParams(self, cursor, params):
        self.params = params
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        description = []
        if begDate and endDate:
            description.append(dateRangeAsStr(u'', begDate, endDate))
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertBlock(CReportBase.AlignCenter)
        cursor.movePosition(QtGui.QTextCursor.End)
        columns = [ ('100%', [], CReportBase.AlignCenter)]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)


    def build(self, params):
        cnt = params.get('cntUser', 1)
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.setBlockFormat(CReportBase.AlignCenter)
        cursor.insertText(self.title())
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        tableColumns = [
                        ('5%',  [u'№'],                          CReportBase.AlignLeft),
                        ('10%', [u'Номер медицинской карты'],    CReportBase.AlignLeft),
                        ('10%', [u'Дата и время обращения'],     CReportBase.AlignLeft),
                        ('10%', [u'Врач'],                       CReportBase.AlignLeft),
                        ('10%', [u'Ф.И.О. пострадавшего'],       CReportBase.AlignLeft),
                        ('10%', [u'Дата рождения (полных лет)'], CReportBase.AlignLeft),
                        ('5%',  [u'Пол' ],                       CReportBase.AlignLeft),
                        ('10%', [u'Адрес' ],                     CReportBase.AlignLeft),
                        ('10%', [u'Телефон' ],                   CReportBase.AlignLeft),
                        ('10%', [u'Диагноз' ],                   CReportBase.AlignLeft),
                        ('10%', [u'Прививка' ],                  CReportBase.AlignLeft),
                        ('10%', [u'Серия' ],                     CReportBase.AlignLeft),
                        ]
        table = createTable(cursor, tableColumns)
        query = selectData(params)
        if query is None:
            return doc
        while query.next():
            record = query.record()
            clientId         = forceInt(record.value('clientId'))
            endDate          = forceString(record.value('endDate'))
            personName       = forceString(record.value('personName'))
            clientName       = forceString(record.value('clientName'))
            clientBirthDate  = forceString(record.value('clientBirthDate'))
            clientAge        = forceString(record.value('clientAge'))
            clientSex        = forceInt(record.value('clientSex'))
            clientRegAddress = forceStringEx(record.value('regAddress'))
            clientLocAddress = forceStringEx(record.value('locAddress'))
            phones           = forceString(record.value('phones'))
            MKB              = forceString(record.value('MKB'))
            vaccinaName      = forceString(record.value('vaccinaName'))
            vaccinaSeria     = forceString(record.value('vaccinaSeria'))
            i = table.addRow()
            table.setText(i, 0, cnt)
            cnt += 1
            table.setText(i, 1, clientId)
            table.setText(i, 2, endDate)
            table.setText(i, 3, personName)
            table.setText(i, 4, clientName)
            table.setText(i, 5, u'%s (%s)'%(clientBirthDate, clientAge))
            table.setText(i, 6, [u'не задано', u'М', u'Ж'][clientSex])
            if clientRegAddress == clientLocAddress:
                table.setText(i, 7, clientRegAddress)
            else:
                table.setText(i, 7, u'Рег: %s \nФакт:%s'%(clientRegAddress, clientLocAddress))
            table.setText(i, 8, phones)
            table.setText(i, 9, MKB)
            table.setText(i, 10, vaccinaName)
            table.setText(i, 11, vaccinaSeria)
        return doc


class CReportTraumaJVSetupDialog(CDialogBase, Ui_ReportTraumaJVSetupDialog):
    def __init__(self, parent=None):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        self.cmbPeriodIssueDate.setCurrentIndex(params.get('byPeriodIssueDate', 0))
        self.edtCntUser.setValue(params.get('cntUser', 1))


    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['byPeriodIssueDate'] = self.cmbPeriodIssueDate.currentIndex()
        result['cntUser'] = self.edtCntUser.value()
        return result
