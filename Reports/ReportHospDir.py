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

from Orgs.Orgs import selectOrganisation
from library.Utils import *
from Orgs.Utils import *
from library.database import *
from library.Utils import *
from Reports.Report import CReport
from Reports.ReportBase import *
from Reports.Ui_HospDirReportSetupDialog import Ui_HospDirReportSetupDialog


def selectData(begDateParam, endDateParam, areaId, personId, OrganisationId, bedsScheduleText, orderText):

    db = QtGui.qApp.db
    begDate = db.formatDate(begDateParam)
    endDate = db.formatDate(endDateParam)
    stmt = u""" 
SELECT CONCAT_WS(" ",c.lastName,c.firstName,c.patrName) AS clientName,c.birthDate,
 d.MKB,

IFNULL(
(SELECT
apd2.value
FROM Action  a2
LEFT JOIN ActionType  AT2 ON AT2.id=a2.actionType_id
LEFT JOIN Event  e2 ON e2.id=a2.event_id
LEFT JOIN ActionProperty  ap2 ON ap2.action_id=a2.id
LEFT JOIN ActionPropertyType  apt2 ON apt2.actionType_id=AT2.id AND apt2.id=ap2.type_id
LEFT JOIN ActionProperty_Date  apd2 ON apd2.id=ap2.id
WHERE date(a2.begDate) BETWEEN {begDate} AND {endDate} AND AT2.flatcode IN ("hospitalDirection") AND apt2.name="Плановая дата госпитализации"
AND apt2.deleted=0 and a2.id=a.id),
(SELECT
apd2.value
FROM Action  a2
LEFT JOIN ActionType  AT2 ON AT2.id=a2.actionType_id
LEFT JOIN Event  e2 ON e2.id=a2.event_id
LEFT JOIN ActionProperty  ap2 ON ap2.action_id=a2.id
LEFT JOIN ActionPropertyType  apt2 ON apt2.actionType_id=AT2.id AND apt2.id=ap2.type_id
LEFT JOIN ActionProperty_Date  apd2 ON apd2.id=ap2.id
WHERE date(a2.begDate) BETWEEN {begDate} AND {endDate} AND AT2.flatcode IN ("planning") AND apt2.name="Плановая дата госпитализации поликлиники"
AND apt2.deleted=0 and a2.id=a.id)
) AS HospDirPlanDate,

IFNULL(
(SELECT
o.title
 FROM Action  a3
LEFT JOIN ActionType  AT3 ON AT3.id=a3.actionType_id
LEFT JOIN Event  e3 ON e3.id=a3.event_id
LEFT JOIN ActionProperty  ap3 ON ap3.action_id=a3.id
LEFT JOIN ActionPropertyType  apt3 ON apt3.actionType_id=AT3.id AND apt3.id=ap3.type_id
LEFT JOIN ActionProperty_Organisation  apo3 ON apo3.id=ap3.id
LEFT JOIN Organisation  o ON o.id=apo3.value
WHERE date(a3.begDate) BETWEEN {begDate} AND {endDate}  AND AT3.flatcode IN ("hospitalDirection") AND apt3.name="Куда направляется"
AND apt3.deleted=0 and a3.id=a.id {condOrganisation}),
(SELECT
concat(osp.name," > ",o3.name)
 FROM Action  a3
LEFT JOIN ActionType  AT3 ON AT3.id=a3.actionType_id
LEFT JOIN Event  e3 ON e3.id=a3.event_id
LEFT JOIN ActionProperty  ap3 ON ap3.action_id=a3.id
LEFT JOIN ActionPropertyType  apt3 ON apt3.actionType_id=AT3.id AND apt3.id=ap3.type_id
LEFT JOIN ActionProperty_OrgStructure  apo3 ON apo3.id=ap3.id
LEFT JOIN OrgStructure  o3 ON o3.id=apo3.value
LEFT JOIN OrgStructure osp ON osp.id=o3.parent_id
LEFT JOIN Organisation  o ON o.id=osp.organisation_id
WHERE date(a3.begDate) BETWEEN {begDate} AND {endDate}  AND AT3.flatcode IN ("planning") AND apt3.name="Подразделение"
AND apt3.deleted=0 and a3.id=a.id {condOrganisation})

) AS OrgDir,

(SELECT
hbp4.name
 FROM Action  a4
LEFT JOIN ActionType  AT4 ON AT4.id=a4.actionType_id
LEFT JOIN Event  e4 ON e4.id=a4.event_id
LEFT JOIN ActionProperty  ap4 ON ap4.action_id=a4.id
LEFT JOIN ActionPropertyType  apt4 ON apt4.actionType_id=AT4.id AND apt4.id=ap4.type_id
LEFT JOIN ActionProperty_rbHospitalBedProfile  aph4 ON aph4.id=ap4.id
LEFT JOIN rbHospitalBedProfile  hbp4 ON hbp4.id=aph4.value
WHERE date(a4.begDate) BETWEEN {begDate} AND {endDate} AND AT4.flatcode IN ("hospitalDirection","planning") AND apt4.name="Профиль койки"
AND apt4.deleted=0 and a4.id=a.id) AS bedProfile,

(SELECT
aps5.value
 FROM Action  a5
LEFT JOIN ActionType  AT5 ON AT5.id=a5.actionType_id
LEFT JOIN Event  e5 ON e5.id=a5.event_id
LEFT JOIN ActionProperty  ap5 ON ap5.action_id=a5.id
LEFT JOIN ActionPropertyType  apt5 ON apt5.actionType_id=AT5.id AND apt5.id=ap5.type_id
LEFT JOIN ActionProperty_String aps5 ON aps5.id=ap5.id
WHERE date(a5.begDate) BETWEEN {begDate} AND {endDate} AND AT5.flatcode IN ("hospitalDirection","planning") AND apt5.name="Тип стационара"
AND apt5.deleted=0 and a5.id=a.id {condbedsSchedule}) AS StationaryType,
date(a.begDate) AS HospDirDate,CONCAT_WS(" ",p.lastName,p.firstName,p.patrName) AS personName,
apsOrder.value as hospOrder

 FROM Action  a
LEFT JOIN ActionType  AT ON AT.id=a.actionType_id
LEFT JOIN Event  e ON e.id=a.event_id
LEFT JOIN Client  c ON c.id=e.client_id
LEFT JOIN Person  p ON p.id=a.person_id
LEFT JOIN Diagnostic dc on dc.event_id = e.id and dc.deleted = 0
LEFT JOIN Diagnosis d on d.id = dc.diagnosis_id and d.deleted = 0
LEFT JOIN ActionProperty_String apsOrder ON apsOrder.id = (
   SELECT apsOrdertmp.id FROM 
   ActionProperty  apOrder 
   inner JOIN ActionPropertyType  aptOrder ON  aptOrder.id=apOrder.type_id
   inner JOIN ActionProperty_String apsOrdertmp ON apsOrdertmp.id=apOrder.id
   WHERE apOrder.action_id=a.id and aptOrder.actionType_id=AT.id  and  aptOrder.name='Порядок направления' 
   AND apOrder.deleted=0
   LIMIT 1
)   
WHERE {cond}

ORDER BY a.id
"""

    cond = []
    tableAction = db.table('Action').alias('a')
    tableActionType = db.table('ActionType').alias('AT')
    tablePerson = db.table('Person').alias('p')
    tableDiagnosis = db.table('Diagnosis').alias('d')

    cond.append(tableActionType['flatCode'].inlist(["hospitalDirection", "planning"]))
    cond.append(u""" (dc.diagnosisType_id in (select id from rbDiagnosisType dt where dt.code in ('1'))) """)
    cond.append(tableDiagnosis['deleted'].eq(0))

    addDateInRange(cond, tableAction['begDate'], begDateParam, endDateParam)
    if areaId:
        orgStructureIdList = getOrgStructureDescendants(areaId)
        cond.append(tablePerson['orgStructure_id'].inlist(orgStructureIdList))
    if personId:
        cond.append(tablePerson['id'].eq(personId))
    if orderText:
        cond.append(u"apsOrder.value = '%s'" % orderText)

    condbedsSchedule = u''' AND aps5.value = '%s' ''' % bedsScheduleText if bedsScheduleText else ''
    condOrganisation = u''' AND o.id = %s''' % OrganisationId if OrganisationId else ''
    return db.query(
        stmt.format(begDate=begDate, endDate=endDate, condOrganisation=condOrganisation, condbedsSchedule=condbedsSchedule,
                    cond=db.joinAnd(cond)))


class CHospDir(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Отчет по созданным направлениям на госпитализацию')

    def getSetupDialog(self, parent):
        result = CHospDirSetupDialog(parent)
        result.setTitle(self.title())
        return result

    def build(self, params):

        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        areaId = params.get('areaId', None)
        personId = params.get('personId', None)
        OrganisationId = params.get('OrganisationId', None)
        bedsScheduleText = params.get('bedsScheduleText', '')
        orderText = params.get('orderText', '')

        # now text
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)

        tableColumns = [
            ('2%', [u'№ п/п'], CReportBase.AlignCenter),
            ('10%', [u'ФИО пациента'], CReportBase.AlignLeft),
            ('5%', [u'Дата рождения'], CReportBase.AlignCenter),
            ('5%', [u'Код диагноза по МКБ'], CReportBase.AlignCenter),
            ('5%', [u'Плановая дата госпитализации'], CReportBase.AlignCenter),
            ('25%', [u'Куда направляется'],     CReportBase.AlignCenter),
            ('10%', [u'Профиль койки'],  CReportBase.AlignCenter),
            ('10%', [u'Тип стационара,'], CReportBase.AlignCenter),
            ('5%', [u'Дата направления'], CReportBase.AlignCenter),
            ('10%', [u'Порядок направления'], CReportBase.AlignCenter),
            ('10%', [u'Направивший специалист'], CReportBase.AlignCenter),
        ]

        table = createTable(cursor, tableColumns)
        counter = 1
        query = selectData(begDate, endDate, areaId, personId, OrganisationId, bedsScheduleText, orderText)
        while query.next():
            record = query.record()
            OrgDir = forceString(record.value('OrgDir'))
            StationaryType = forceString(record.value('StationaryType'))
            if OrganisationId and not OrgDir:
                continue
            if bedsScheduleText and not StationaryType:
                continue
            row = table.addRow()
            table.setText(row, 0, counter)

            table.setText(row, 1, forceString(record.value('clientName')))
            table.setText(row, 2, forceString(record.value('birthDate')))
            table.setText(row, 3, forceString(record.value('MKB')))
            table.setText(row, 4, forceString(record.value('HospDirPlanDate')))

            table.setText(row, 5, OrgDir)
            table.setText(row, 6, forceString(record.value('bedProfile')))
            table.setText(row, 7, StationaryType)
            table.setText(row, 8, forceString(record.value('HospDirDate')))
            table.setText(row, 9, forceString(record.value('hospOrder')))
            table.setText(row, 10, forceString(record.value('personName')))
            counter += 1
        return doc


class CHospDirSetupDialog(QtGui.QDialog, Ui_HospDirReportSetupDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())
        if QtGui.qApp.userId:
            self.cmbPerson.setValue(QtGui.qApp.userId)

    def setTitle(self, title):
        self.setWindowTitle(title)

    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        self.cmbOrgStructure.setValue(params.get('areaId', None))
        self.cmbPerson.setValue(params.get('personId', None))
        self.cmbOrganisation.setValue(params.get('OrganisationId', None))
        self.cmbSchedule.setCurrentIndex(params.get('bedsSchedule', 0))

    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['areaId'] = self.cmbOrgStructure.value()
        result['personId'] = self.cmbPerson.value()
        result['OrganisationId'] = self.cmbOrganisation.value()
        result['bedsSchedule'] = self.cmbSchedule.currentIndex()
        result['bedsScheduleText'] = forceString(self.cmbSchedule.currentText()).lower() if result['bedsSchedule'] > 0 else ''
        result['orderText'] = self.cmbOrder.currentText()
        return result

    @pyqtSignature('')
    def on_btnSelectOrganisation_clicked(self):
        orgId = selectOrganisation(self, self.cmbOrganisation.value(), False)
        self.cmbOrganisation.updateModel()
        if orgId:
            self.cmbOrganisation.setValue(orgId)
