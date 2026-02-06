# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012 SAMSON Group. All rights reserved.
## Copyright (C) 2015 Oskin A.
## Copyright (C) 2016 Oskin A. and Arkhipov S.
## Copyright (C) 2021 Arkhipov S.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import *

from library.Utils import *
from Orgs.Utils import *
from library.database import *
from library.Utils import *
from Reports.Report import CReport
from Reports.ReportBase import *
from Reports.Ui_NoProfsChildSetupDialog import Ui_NoProfsChildSetupDialog


def selectData(params):

    stmt = u"""
SELECT distinct CONCAT_WS(' ', Client.lastName, Client.firstName, Client.patrName) as clientName, 
Client.birthDate, ClientAttach.orgStructure_id,
  ClientPolicy.number AS police, getClientContacts(Client.id) as contact, AttachOrgStructure.name as attachName,
  getClientLocAddress(Client.id) as address, Client.id, getOMSCode(AttachOrgStructure.id) as OrgStructureCode  ,
  ClientAttach.orgStructure_id,
  formatPersonName(Person.id) as personName, Person.id as personId
  
  FROM Client
  LEFT JOIN ClientPolicy ON ClientPolicy.id = getClientPolicyId(Client.id, 1)
  LEFT JOIN ClientAttach ON ClientAttach.id = getClientAttachIdForDate(Client.`id`, 0, NOW())
  left join OrgStructure as AttachOrgStructure on AttachOrgStructure.id = ClientAttach.orgStructure_id
  left join Person_Order as po ON po.id=(select id from Person_Order where Person_Order.orgStructure_id = AttachOrgStructure.id AND Person_Order.deleted=0 AND Person_Order.type = 6 AND ((Person_Order.validToDate IS NULL OR LENGTH(Person_Order.validToDate) = 0) or Person_Order.validToDate > NOW()) LIMIT 1)  
  left join Person on Person.id = po.master_id

WHERE
    %s

 ORDER BY %s
"""

    db = QtGui.qApp.db
    begDate = db.formatDate(params.get('begDate', QDate()))
    endDate = db.formatDate(params.get('endDate', QDate()))
    areaId = params.get('areaId', None)

    tableClientAttach = db.table('ClientAttach')
    tableClient = db.table('Client')
    cond = []
    cond.append(tableClient['deleted'].eq(0))
    cond.append(tableClient['endDate'].isNull())
    cond.append(tableClient['deathDate'].isNull())
    cond.append('getDispCountProfs(Client.id, 262, %s, %s) = 0' % (begDate, endDate))
    if (params.get('checkAge')):
        cond.append(
            'NOW() >= ADDDATE(Client.birthDate, INTERVAL {0:d} {1:s}) and NOW() < ADDDATE(Client.birthDate, INTERVAL {2:d} {3:s} )'.format(
            params.get('ageBegValue', 0),
            ['DAY', 'WEEK', 'MONTH', 'YEAR'][params.get('ageBegType', 3)],
            params.get('ageEndValue', 0) + 1,
            ['DAY', 'WEEK', 'MONTH', 'YEAR'][params.get('ageEndType', 3)]
            ))
    cond.append('NOW() < ADDDATE(Client.birthDate, INTERVAL 18 YEAR)')
    if areaId:
        orgStructureIdList = getOrgStructureDescendants(areaId)
        cond.append(tableClientAttach['orgStructure_id'].inlist(orgStructureIdList))
    order = 'AttachOrgStructure.name, AttachOrgStructure.id, clientName' if params.get('attach', False) else 'clientName'
    return db.query(stmt % (db.joinAnd(cond), order))


class CNoProfsChild(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Отчет по пациентам, не прошедшим профилактические мероприятия (0-17) ')

    def getSetupDialog(self, parent):
        result = CNoProfsChildSetupDialog(parent)
        result.setTitle(self.title())
        return result

    def build(self, params):
        attach = params.get('attach', False)

        # now text
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        self.dumpParams(cursor, params)
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportTitle)

        tableColumns = [
            ('2%', [u'№ п/п'], CReportBase.AlignCenter),
            ('10%', [u'ФИО пациента'], CReportBase.AlignLeft),
            ('10%', [u'Дата рождения'], CReportBase.AlignCenter),
            ('10%', [u'Полис'], CReportBase.AlignCenter),
            ('25%', [u'Адрес'],     CReportBase.AlignCenter),
            ('10%', [u'Контакты'],  CReportBase.AlignCenter),
            ('10%', [u'Подразделение'], CReportBase.AlignCenter),
            ('10%', [u'Участок'], CReportBase.AlignCenter),
        ]

        table = createTable(cursor, tableColumns)
        counter = 1
        query = selectData(params)
        orgStructureIdOld = -1
        while query.next():
            record = query.record()
            attachName = forceString(record.value('attachName'))
            if attach:
                orgStructureId = forceRef(record.value('orgStructure_id'))
                personName = forceString(record.value('personName'))
                if orgStructureId != orgStructureIdOld:
                    if personName:
                        personName = u'Участок: ' + attachName + u' Врач: ' + personName
                    elif orgStructureId > 0:
                        personName = u'Участок: ' + attachName + u' Врач: Не указан'
                    else:
                        personName = u'Участок не указан'

                    row = table.addRow()
                    table.setText(row, 1, personName, fontBold=True)
                    table.mergeCells(row, 1, 1, 6)
                    orgStructureIdOld = orgStructureId
            row = table.addRow()
            table.setText(row, 0, counter)

            table.setText(row, 1, forceString(record.value('clientName')))
            table.setText(row, 2, forceString(record.value('birthDate')))
            table.setText(row, 3, forceString(record.value('police')))

            table.setText(row, 4, forceString(record.value('address')))
            table.setText(row, 5, forceString(record.value('contact')))
            table.setText(row, 6, forceString(record.value('OrgStructureCode')))
            table.setText(row, 7, attachName)
            counter += 1
        return doc

    def dumpParams(self, cursor, params):
        description = self.getDescription(params)
        if params.get('checkAge'):
            idx = len(description) -1 if len(description) else 0
            description.insert(idx,
                               u'возраст ' + forceString(params.get('ageBegValue')) + [u'д', u'н', u'м', u'г'][
                                   params.get('ageBegType', 3)] + '-' + forceString(params.get('ageEndValue')) +
                               [u'д', u'н', u'м', u'г'][params.get('ageEndType', 3)])
        columns = [ ('100%', [], CReportBase.AlignLeft) ]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertHtml('<br/><br/>')

class CNoProfsChildSetupDialog(QtGui.QDialog, Ui_NoProfsChildSetupDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.edtBegDate.setDate(QDate(QDate.currentDate().year(), 1, 1))
        self.edtEndDate.setDate(QDate(QDate.currentDate().year(), 12, 31))
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())
        self.setAgeWidgetsEnabled(False)

    @pyqtSignature('bool')
    def on_chkAge_toggled(self, checked):
        self.setAgeWidgetsEnabled(checked)

    @pyqtSignature('int')
    def on_cmbAgeBegUnit_currentIndexChanged(self, index):
        maxVal = 17 if index == 3 else 6000 #до 18 лет хватит с запасом
        self.spnAgeBeg.setMaximum(maxVal)

    @pyqtSignature('int')
    def on_cmbAgeEndUnit_currentIndexChanged(self, index):
        maxVal = 17 if index == 3 else 6600
        self.spnAgeEnd.setMaximum(maxVal)

    def setAgeWidgetsEnabled(self, enabled):
        for wgt in (self.cmbAgeBegUnit, self.cmbAgeEndUnit, self.spnAgeBeg, self.spnAgeEnd):
            wgt.setEnabled(enabled)

    def setTitle(self, title):
        self.setWindowTitle(title)

    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate(QDate.currentDate().year(), 1, 1)))
        self.edtEndDate.setDate(params.get('endDate', QDate(QDate.currentDate().year(), 12, 31)))
        self.cmbOrgStructure.setValue(params.get('areaId', None))
        attach = bool(params.get('attach', False))
        self.chkGroupByAttach.setChecked(attach)

    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['areaId'] = self.cmbOrgStructure.value()
        result['attach'] = self.chkGroupByAttach.isChecked()

        result['checkAge'] = self.chkAge.isChecked()
        result['ageBegType'] = self.cmbAgeBegUnit.currentIndex()
        result['ageEndType'] = self.cmbAgeEndUnit.currentIndex()
        result['ageBegValue'] = self.spnAgeBeg.value()
        result['ageEndValue'] = self.spnAgeEnd.value()
        return result
