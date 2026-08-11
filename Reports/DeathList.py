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


from library.database   import addDateInRange
from library.Utils      import calcAge, forceBool, forceDate, forceInt, forceString, formatName
from Events.Action      import CActionTypeCache
from Events.Utils       import getActionTypeIdListByFlatCode
from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable
from Reports.Utils      import getExistsStringPropertyCurrEvent


def selectData(begDate, endDate, busyness, MKBFilter, MKBFrom, MKBTo, place, cause, foundBy, foundation, includeSelected, relegateOrgId, excludeSelected):
    stmt="""
SELECT
  Client.lastName,
  Client.firstName,
  Client.patrName,
  Client.birthDate,
  Client.sex,
  formatClientAddress(ClientAddress.id) AS address,
  IF(ClientWork.org_id IS NULL, ClientWork.freeInput, Organisation.shortName) AS workName,
  ClientWork.post AS workPost,
  Event.setDate AS date,
  Event.externalId AS number,
  (Event.isPrimary = 1) AS autopsy,
  PDiagnosis.MKB AS PMKB,
  PDiagnosis.MKBEx AS PMKBEx,
  FDiagnosis.MKB AS FMKB,
  FDiagnosis.MKBEx AS FMKBEx,
  rbResult.name AS result
FROM
  Event
  LEFT JOIN EventType ON EventType.id = Event.eventType_id
  LEFT JOIN Event_Death ed ON Event.id = ed.master_id
  LEFT JOIN Client ON Client.id = Event.client_id
  LEFT JOIN ClientAddress ON ClientAddress.client_id = Client.id
                             AND ClientAddress.id = (SELECT MAX(id) FROM ClientAddress AS CA WHERE CA.Type=0 AND CA.client_id = Client.id)
  LEFT JOIN ClientWork ON ClientWork.client_id = Client.id
                             AND ClientWork.id = (SELECT MAX(id) FROM ClientWork AS CW WHERE ClientWork.deleted=0 AND CW.client_id = Client.id)
  LEFT JOIN Organisation ON Organisation.id = ClientWork.org_id
  LEFT JOIN Diagnostic AS PDiagnostic ON (PDiagnostic.event_id = Event.id AND PDiagnostic.deleted = 0)
  LEFT JOIN rbDiagnosisType AS PDiagnosisType ON PDiagnosisType.id = PDiagnostic.diagnosisType_id
  LEFT JOIN Diagnosis  AS PDiagnosis ON PDiagnosis.id = PDiagnostic.diagnosis_id
  LEFT JOIN Diagnostic AS FDiagnostic ON (FDiagnostic.event_id = Event.id AND FDiagnostic.deleted = 0)
  LEFT JOIN rbDiagnosisType AS FDiagnosisType ON FDiagnosisType.id = FDiagnostic.diagnosisType_id
  LEFT JOIN Diagnosis  AS FDiagnosis ON FDiagnosis.id = FDiagnostic.diagnosis_id
  LEFT JOIN rbResult ON rbResult.id = Event.result_id

WHERE
  EventType.code = '15'
  AND PDiagnosisType.code = '8'
  AND FDiagnosisType.code = '4'
  AND %s
ORDER BY Client.lastName, Client.firstName, Client.patrName, Client.sex, Event.setDate, Event.id
    """
    db = QtGui.qApp.db
    tableEvent     = db.table('Event')
    tableWork      = db.table('ClientWork')
    tableDiagnosis = db.table('Diagnosis').alias('FDiagnosis')
    tableDeath     = db.table('Event_Death').alias('ed')
    cond = []
    cond.append(tableEvent['deleted'].eq(0))
    addDateInRange(cond, tableEvent['setDate'], begDate, endDate)
    if busyness == 1:
        cond.append(db.joinAnd([tableWork['id'].isNotNull(),db.joinOr([tableWork['org_id'].isNotNull(), "(ClientWork.freeInput IS NOT NULL AND TRIM(ClientWork.freeInput) > '') " ])]))
    elif busyness == 2:
        cond.append(db.joinOr([tableWork['id'].isNull(),db.joinAnd([tableWork['org_id'].isNull(),"(ClientWork.freeInput IS NULL OR TRIM(ClientWork.freeInput) = '') "])]))
    if MKBFilter == 1:
        cond.append(tableDiagnosis['MKB'].ge(MKBFrom))
        cond.append(tableDiagnosis['MKB'].le(MKBTo))
    if place:
        cond.append(tableDeath['deathPlaceType_id'].eq(place))
    if cause:
        cond.append(tableDeath['deathCauseType_id'].eq(cause))
    if foundBy:
        cond.append(tableDeath['employeeTypeDeterminedDeathCause_id'].eq(foundBy))
    if foundation:
        cond.append(tableDeath['groundsForDeathCause_id'].eq(foundation))
    if includeSelected:
        cond.append("(Event.relegateOrg_id IS NOT NULL)")
    if relegateOrgId > 0:
        if excludeSelected:
            cond.append(" (Event.relegateOrg_id NOT IN ({0}))".format(relegateOrgId))
        else:
            cond.append("Event.relegateOrg_id IN ({0})".format(relegateOrgId))
    return db.query(stmt % (db.joinAnd(cond)))


def addCondForDeathCurcumstance(cond, tableEvent, place, cause, foundBy, foundation):
    db = QtGui.qApp.db
    try:
        actionTypeIdList = getActionTypeIdListByFlatCode('deathCurcumstance')
    except:
        actionTypeIdList = None
    tableAction = db.table('Action')
    table = tableAction
    condActionProperties = []
    if place:
        condActionProperties = addCondActionProperties(condActionProperties, actionTypeIdList, u'Смерть последовала', place)
    if cause:
        condActionProperties = addCondActionProperties(condActionProperties, actionTypeIdList, u'Смерть произошла', cause)
    if foundBy:
        condActionProperties = addCondActionProperties(condActionProperties, actionTypeIdList, u'Причина установлена', foundBy)
    if foundation:
        condActionProperties = addCondActionProperties(condActionProperties, actionTypeIdList, u'Основание', foundation)
    if condActionProperties:
        condActionProperties.append(tableAction['event_id'].eq(tableEvent['id']))
        cond.append(db.existsStmt(table, condActionProperties))


def addCondActionProperties(cond, actionTypeIdList, propertyName, value):
    cond.append(getExistsStringPropertyCurrEvent(actionTypeIdList, propertyName, value))
    return cond


class CDeathList(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setPayPeriodVisible(False)
        self.setTitle(u'Журнал регистрации умерших')


    def getSetupDialog(self, parent):
        result = CDeathReportSetupDialog(parent)
        result.setBusynessEnabled(True)
        result.setMKBFilterEnabled(True)
        result.setTitle(self.title())
        return result


    def build(self, params):
        begDate   = params.get('begDate', QDate())
        endDate   = params.get('endDate', QDate())
        busyness  = params.get('busyness', 0)
        MKBFilter = params.get('MKBFilter', 0)
        MKBFrom   = params.get('MKBFrom', 'A00')
        MKBTo     = params.get('MKBTo', 'Z99.9')

        place = params.get('deathPlace', 0)
        cause = params.get('deathCause', 0)
        foundBy = params.get('deathFoundBy', 0)
        foundation = params.get('deathFoundation', 0)
        relegateOrgId = params.get('eventRelegateOrgId',0)
        includeSelectedOrg = params.get('includeSelectedOrg',False)
        excludeSelectedOrg = params.get('excludeSelectedOrg',False)

        tableColumns = [
            ('5%', [u'№'],       CReportBase.AlignRight),
            ('5%', [u'№ спр.'],  CReportBase.AlignRight),
            ('25%',[u'ФИО'],     CReportBase.AlignLeft),
            ('25%',[u'Адрес,\nЗанятость'],      CReportBase.AlignLeft),
            ('10%',[u'дата смерти и\nвозраст'], CReportBase.AlignLeft),
            ('15%',[u'предварительный\nи заключительный\nдиагноз'], CReportBase.AlignLeft),
            ('15%',[u'вскрытие,\nрезультат'],  CReportBase.AlignLeft),
            ]

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        table = createTable(cursor, tableColumns)

        n = 0
        query = selectData(begDate, endDate, busyness, MKBFilter, MKBFrom, MKBTo, place, cause, foundBy, foundation, includeSelectedOrg, relegateOrgId, excludeSelectedOrg)

        while query.next():
            n += 1
            i = table.addRow()
            record   = query.record()

            autopsy  = forceBool(record.value('autopsy'))
            table.setText(i, 0, n)
            table.setText(i, 1, forceString(record.value('number')))
            table.setText(i, 2, formatName(record.value('lastName'),
                                           record.value('firstName'),
                                           record.value('patrName')))
            work = ', '.join(filter(None, [forceString(record.value('workName')), forceString(record.value('workPost'))]))
            table.setText(i, 3, forceString(record.value('address'))+'\n'+work)
            birthDate = forceDate(record.value('birthDate'))
            date  = forceDate(record.value('date'))
            age   = calcAge(birthDate, date)
            table.setText(i, 4, u'%s\n%s' % (forceString(date), age))
            table.setText(i, 5, u'%s\n%s' % (forceString(record.value('PMKB')),
                                             forceString(record.value('FMKB'))))
            table.setText(i, 6, u'%s\n%s' % (u'проводилось' if autopsy else u'не проводилось',
                                             forceString(record.value('result'))))
        return doc


from Ui_DeathReportSetup import Ui_DeathReportSetupDialog


class CDeathReportSetupDialog(QtGui.QDialog, Ui_DeathReportSetupDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.setBusynessEnabled(False)
        self.setMKBFilterEnabled(False)
        self.cmbPlace.setTable('rbDeathPlaceType')
        self.cmbCause.setTable('rbDeathCauseType')
        self.cmbFoundBy.setTable('rbEmployeeTypeDeterminedDeathCause')
        self.cmbFoundation.setTable('rbGroundsForDeathCause')


    def setBusynessEnabled(self, mode=True):
        for widget in (self.lblBusyness, self.cmbBusyness):
            widget.setVisible(mode)
        self.busynessEnabled = mode


    def setMKBFilterEnabled(self, mode=True):
        for widget in (self.lblMKB, self.frmMKB):
            widget.setVisible(mode)
        self.MKBFilterEnabled = mode


    def preparePropertyComboBox(self, comboBox, actionType, propertyName):
        actionPropertyType = actionType.getPropertiesByName().get(propertyName, None) if actionType else None
        if actionPropertyType:
            comboBox.setDomain('\'\','+actionPropertyType.valueDomain)
            comboBox.setEnabled(True)
        else:
            comboBox.setEnabled(False)


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        if self.busynessEnabled:
            self.cmbBusyness.setCurrentIndex(forceInt(params.get('busyness', 0)))
        if self.MKBFilterEnabled:
            MKBFilter = params.get('MKBFilter', 0)
            self.cmbMKBFilter.setCurrentIndex(MKBFilter if MKBFilter else 0)
            self.edtMKBFrom.setText(params.get('MKBFrom', 'A00'))
            self.edtMKBTo.setText(params.get('MKBTo',   'Z99.9'))

        self.cmbPlace.setValue(params.get('deathPlace', None))
        self.cmbCause.setValue(params.get('deathCause', None))
        self.cmbFoundBy.setValue(params.get('deathFoundBy', None))
        self.cmbFoundation.setValue(params.get('deathFoundation', None))
        if params.get('includeSelectedOrg', False) == True:
            self.chkRelegateOrg.setChecked(True)
            self.cmbRelegateOrg.setValue(params.get('eventRelegateOrgId',None))
            if params.get('excludeSelectedOrg',False) == True:
                self.chkExcludeSelected.setChecked(True)


    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        if self.busynessEnabled:
            result['busyness'] = self.cmbBusyness.currentIndex()
        if self.MKBFilterEnabled:
            result['MKBFilter'] = self.cmbMKBFilter.currentIndex()
            result['MKBFrom']   = unicode(self.edtMKBFrom.text())
            result['MKBTo']     = unicode(self.edtMKBTo.text())
        result['deathPlace']      = self.cmbPlace.value()
        result['deathCause']      = self.cmbCause.value()
        result['deathFoundBy']    = self.cmbFoundBy.value()
        result['deathFoundation'] = self.cmbFoundation.value()
        if self.chkRelegateOrg.isChecked():
            result['eventRelegateOrgId'] = self.cmbRelegateOrg.value()
            result['excludeSelectedOrg'] = self.chkExcludeSelected.isChecked()
            result['includeSelectedOrg'] = self.chkRelegateOrg.isChecked()
        return result


    @pyqtSignature('int')
    def on_cmbMKBFilter_currentIndexChanged(self, index):
        self.edtMKBFrom.setEnabled(index == 1)
        self.edtMKBTo.setEnabled(index == 1)

    @pyqtSignature('bool')
    def on_chkRelegateOrg_toggled(self, checked):
        self.cmbRelegateOrg.setEnabled(checked)
        if not checked:
            self.cmbRelegateOrg.setCurrentIndex(0)
            self.chkExcludeSelected.setChecked(checked)

    @pyqtSignature('int')
    def on_cmbRelegateOrg_currentIndexChanged(self, index):
        self.chkExcludeSelected.setEnabled(index > 0)
        if index == 0:
            self.chkExcludeSelected.setChecked(False)
