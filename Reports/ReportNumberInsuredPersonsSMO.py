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
from PyQt4.QtCore import QDate, QDateTime

from library.Utils      import forceInt, forceRef, forceString, agreeNumberAndWord, formatSex
from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable


def selectData(params):
    policyDate = params.get('policyDate', QDate())
    policyType = params.get('policyType', None)
    policyKind = params.get('policyKind', None)
    insurerId  = params.get('insurerId')
    sex        = params.get('sex', 0)
    ageFrom    = params.get('ageFrom', 0)
    ageTo      = params.get('ageTo', 150)

    stmt="""
SELECT
    COUNT(*) AS cnt,
    age(Client.birthDate, %s) AS clientAge,
    Client.sex AS clientSex,
    ClientPolicy.insurer_id,
    Organisation.shortName
FROM Client
INNER JOIN ClientPolicy  ON ClientPolicy.client_id = Client.id
        AND ClientPolicy.id = (SELECT MAX(CP.id) FROM ClientPolicy AS CP
                               WHERE CP.deleted = 0
                               AND   CP.insurer_id = ClientPolicy.insurer_id
                               AND   CP.client_id = Client.id
                               %s
                               %s
                              )
INNER JOIN rbPolicyType ON rbPolicyType.id = ClientPolicy.policyType_id
INNER JOIN Organisation ON Organisation.id = ClientPolicy.insurer_id
WHERE Client.deleted = 0 AND ClientPolicy.deleted = 0 AND Organisation.deleted = 0
  %s
GROUP BY clientAge, clientSex, shortName
    """
    db = QtGui.qApp.db
    tableClient = db.table('Client')
    tableClientPolicy = db.table('ClientPolicy')
    tableRBPolicyType = db.table('rbPolicyType')
    cond = []
    if insurerId:
        cond.append(tableClientPolicy['insurer_id'].eq(insurerId))
    if policyDate:
        cond.append(tableClientPolicy['begDate'].lt(policyDate.addDays(1)))
        cond.append(
                    db.joinOr(
                              [
                               tableClientPolicy['endDate'].ge(policyDate),
                               tableClientPolicy['endDate'].isNull()
                              ]
                             )
                   )
    stmtPolicyTypeId = u''
    stmtPolicyKindId = u''
    if policyType:
        if policyType == -1:
            cond.append(db.joinOr([tableRBPolicyType['code'].eq('1'), tableRBPolicyType['code'].eq('2')]))
        else:
            cond.append(tableClientPolicy['policyType_id'].eq(policyType))
        stmtPolicyTypeId = u'AND CP.policyType_id = ClientPolicy.policyType_id'
    if policyKind:
        cond.append(tableClientPolicy['policyKind_id'].eq(policyKind))
        stmtPolicyKindId = u'AND CP.policyKind_id = ClientPolicy.policyKind_id'
    if sex:
        cond.append(tableClient['sex'].eq(sex))
    if ageFrom <= ageTo:
        cond.append('age(Client.birthDate, %s) >= %d'%(tableClient['birthDate'].formatValue(policyDate), ageFrom))
        cond.append('age(Client.birthDate, %s) < %d'%(tableClient['birthDate'].formatValue(policyDate), ageTo+1))
    return db.query(stmt % (tableClient['birthDate'].formatValue(policyDate), stmtPolicyTypeId, stmtPolicyKindId, (u' AND %s'%(db.joinAnd(cond))) if cond else u''))


class CReportNumberInsuredPersonsSMO(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setPayPeriodVisible(False)
        self.setTitle(u'Сведения о численности застрахованных лиц по СМО')


    def getSetupDialog(self, parent):
        result = CNumberInsuredPersonsSMOSetupDialog(parent)
        result.setTitle(self.title())
        return result


    def dumpParams(self, cursor, params):
        db = QtGui.qApp.db
        description = []
        policyDate = params.get('policyDate', QDate())
        policyType = params.get('policyType', None)
        policyKind = params.get('policyKind', None)
        insurerId  = params.get('insurerId', None)
        sex        = params.get('sex', 0)
        ageFrom    = params.get('ageFrom', None)
        ageTo      = params.get('ageTo', None)
        description.append(u'на дату: ' + forceString(policyDate))
        if policyType:
            if policyType == -1:
                description.append(u'тип полиса: ОМС')
            else:
                description.append(u'тип полиса: ' + forceString(db.translate('rbPolicyType', 'id', policyType, 'name')))
        if policyKind:
            description.append(u'вид полиса: ' + forceString(db.translate('rbPolicyKind', 'id', policyKind, 'name')))
        if insurerId:
            description.append(u'СМО: ' + forceString(db.translate('Organisation', 'id', insurerId, 'shortName')))
        if sex:
            description.append(u'пол: ' + formatSex(sex))
        if ageFrom is not None and ageTo is not None and ageFrom <= ageTo:
            description.append(u'возраст: c %d по %d %s' % (ageFrom, ageTo, agreeNumberAndWord(ageTo, (u'год', u'года', u'лет'))))
        description.append(u'отчёт составлен: ' + forceString(QDateTime.currentDateTime()))
        columns = [ ('100%', [], CReportBase.AlignLeft) ]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()


    def build(self, params):
        reportRowSize = 9
        keyNameTotal = (u'Итого', None)
        reportShortName = {}
        reportShortNameTotal = {(keyNameTotal): [0] * reportRowSize}
        query = selectData(params)
        while query.next():
            record = query.record()
            cnt    = forceInt(record.value('cnt'))
            age    = forceInt(record.value('clientAge'))
            sex    = forceInt(record.value('clientSex'))
            shortName   = forceString(record.value('shortName'))
            insurerId   = forceRef(record.value('insurer_id'))
            keyName = (shortName, insurerId)
            reportData = reportShortName.get(keyName, [0] * reportRowSize)
            reportDataTotal = reportShortNameTotal.get(keyNameTotal, [0] * reportRowSize)
            if age < 5:
                colBase = 1
            elif age > 4 and age < 18:
                colBase = 3
            elif (sex==1 and age < 60) or (sex != 1 and age < 55):
                colBase = 5
            elif (sex==1 and age >= 60) or (sex != 1 and age >= 55):
                colBase = 7
            cols = [colBase+(0 if sex==1 else 1), 0]
            for col in cols:
                reportData[col] += cnt
                reportDataTotal[col] += cnt
            reportShortName[keyName] = reportData
            reportShortNameTotal[keyNameTotal] = reportDataTotal

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        tableColumns = [
            ( '8%', [u'№ стр.',                                    u'',                       u'',                u''],     CReportBase.AlignRight),
            ('20%', [u'Наименование страховой компании',           u'',                       u'',                u''],     CReportBase.AlignLeft),
            ( '8%', [u'Число застрахованных лиц',                  u'',                       u'',                u''],     CReportBase.AlignRight),
            ( '8%', [u'В том числе по группам застрахованных лиц', u'дети',                   u'0-4 года',        u'муж.'], CReportBase.AlignRight),
            ( '8%', [u'',                                          u'',                       u'',                u'жен.'], CReportBase.AlignRight),
            ( '8%', [u'',                                          u'',                       u'5-17 лет',        u'муж.'], CReportBase.AlignRight),
            ( '8%', [u'',                                          u'',                       u'',                u'жен.'], CReportBase.AlignRight),
            ( '8%', [u'',                                          u'трудоспособный возраст', u'18-59 лет',       u'муж.'], CReportBase.AlignRight),
            ( '8%', [u'',                                          u'',                       u'18-54 лет',       u'жен.'], CReportBase.AlignRight),
            ( '8%', [u'',                                          u'пенсионеры',             u'60 лет и старше', u'муж.'], CReportBase.AlignRight),
            ( '8%', [u'',                                          u'',                       u'55 лет и старше', u'жен.'], CReportBase.AlignRight),
            ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 4, 1) # № стр.
        table.mergeCells(0, 1, 4, 1) # Наименование СК
        table.mergeCells(0, 2, 4, 1) # Число застрахованных лиц
        table.mergeCells(0, 3, 1, 8) # В том числе по группам застрахованных лиц
        table.mergeCells(1, 3, 1, 4) # дети
        table.mergeCells(2, 3, 1, 2) # 0-4
        table.mergeCells(2, 5, 1, 2) # 15-17
        table.mergeCells(1, 7, 1, 2) # трудоспособный возраст
        table.mergeCells(1, 9, 1, 2) # пенсионеры

        keySortName = reportShortName.keys()
        keySortName.sort()
        for keyName in keySortName:
            reportData = reportShortName.get(keyName, [0] * reportRowSize)
            i = table.addRow()
            table.setText(i, 0, i-3)
            table.setText(i, 1, keyName[0])
            for j in xrange(len(reportData)):
                table.setText(i, 2+j, reportData[j])
        for reportDataTotal in reportShortNameTotal.values():
            i = table.addRow()
            table.setText(i, 0, i-3)
            table.setText(i, 1, keyNameTotal[0])
            for j in xrange(len(reportDataTotal)):
                table.setText(i, 2+j, reportDataTotal[j])
        return doc


from Ui_NumberInsuredPersonsSMOSetup import Ui_NumberInsuredPersonsSMOSetupDialog


class CNumberInsuredPersonsSMOSetupDialog(QtGui.QDialog, Ui_NumberInsuredPersonsSMOSetupDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cmbPolicyType.setTable('rbPolicyType', True, specialValues=((-1, u'ОМС', u'ОМС'), ))
        self.cmbPolicyKind.setTable('rbPolicyKind', True)


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        self.edtPolicyDate.setDate(params.get('policyDate', QDate.currentDate()))
        self.cmbPolicyType.setValue(params.get('policyType', None))
        self.cmbPolicyKind.setValue(params.get('policyKind', None))
        self.cmbInsurer.setValue(params.get('insurerId'))
        self.cmbSex.setCurrentIndex(params.get('sex', 0))
        self.edtAgeFrom.setValue(params.get('ageFrom', 0))
        self.edtAgeTo.setValue(params.get('ageTo', 150))


    def params(self):
        result = {}
        result['policyDate'] = self.edtPolicyDate.date()
        result['policyType'] = self.cmbPolicyType.value()
        result['policyKind'] = self.cmbPolicyKind.value()
        result['insurerId']  = self.cmbInsurer.value()
        result['sex']        = self.cmbSex.currentIndex()
        result['ageFrom']    = self.edtAgeFrom.value()
        result['ageTo']      = self.edtAgeTo.value()
        return result
