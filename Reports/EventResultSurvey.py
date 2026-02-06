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
from PyQt4.QtCore import Qt, pyqtSignature, QDate

from library.Utils      import forceBool, forceInt, forceRef, forceString
from Events.Utils       import getWorkEventTypeFilter
from Orgs.Utils         import getOrgStructureDescendants, getOrgStructures
from Orgs.Orgs          import selectOrganisation
from Reports.ReportBase import CReportBase, createTable
from Reports.Report     import CReport
from library.DialogBase import CDialogBase
from Events.EventTypeListEditorDialog import CEventTypeListEditorDialog
from Reports.SpecialityListDialog import CSpecialityListDialog

from Ui_EventResultListSetup import Ui_EventResultSetupDialog

STRICT_ADDRESS = 0
NONRESIDENT_ADDRESS = 1
FOREIGN_ADDRESS = 2

def selectData(params):
    begDate                 = params.get('begDate', QDate())
    endDate                 = params.get('endDate', QDate())
    eventPurposeId          = params.get('eventPurposeId', None)
    eventTypeList           = params.get('eventTypeList', [])
    orgStructureId          = params.get('orgStructureId', None)
    specialityList          = params.get('specialityList', [])
    personId                = params.get('personId', None)
    workOrgId               = params.get('workOrgId', None)
    sex                     = params.get('sex', 0)
    ageFrom                 = params.get('ageFrom', 0)
    ageTo                   = params.get('ageTo', 150)
    socStatusTypeId         = params.get('socStatusTypeId', None)
    addressEnabled          = params.get('addressEnabled', False)
    areaEnabled             = params.get('areaEnabled', False)
    areaId                  = params.get('areaId', None)
    MKBFilter               = params.get('MKBFilter', 0)
    MKBFrom                 = params.get('MKBFrom', 'A00')
    MKBTo                   = params.get('MKBTo', 'Z99.9')
    MKBExFilter             = params.get('MKBExFilter', 0)
    MKBExFrom               = params.get('MKBExFrom', 'A00')
    MKBExTo                 = params.get('MKBExTo', 'Z99.9')
    chkPersonDetail         = params.get('chkPersonDetail', False)
    clientAddressEnabled    = params.get('clientAddressEnabled', False)
    addressType             = params.get('addressType', 0)
    clientAddressType       = params.get('clientAddressType', 0)
    clientAddressCityCode   = params.get('clientAddressCityCode', None)
    clientAddressCityCodeList = params.get('clientAddressCityCodeList', None)
    clientAddressStreetCode = params.get('clientAddressStreetCode', None)
    clientHouse             = params.get('clientHouse', '')
    clientCorpus            = params.get('clientCorpus', '')
    clientFlat              = params.get('clientFlat', '')

    stmt="""
SELECT
    COUNT(DISTINCT Event.id) AS `count`,
    Event.result_id AS result_id,
    rbResult.name   AS result,
    rbDiagnosticResult.id AS diagnosticResultId,
    rbDiagnosticResult.name AS diagnosticResult,
    Event.isPrimary AS isPrimary,
    Event.execDate IS NOT NULL AS isDone,
    Event.`order`   AS `order`,
    Event.execPerson_id,
    vrbPersonWithSpeciality.name AS personName
FROM
    Event
    JOIN EventType ON EventType.id = Event.eventType_id
    JOIN Diagnostic ON Diagnostic.event_id = Event.id AND
                            Diagnostic.id IN (
                    SELECT D1.id
                    FROM Diagnostic AS D1 JOIN rbDiagnosisType AS DT1 ON DT1.id = D1.diagnosisType_id
                    WHERE D1.event_id = Event.id AND
                    DT1.code = (SELECT MIN(DT2.code)
                              FROM Diagnostic AS D2 JOIN rbDiagnosisType AS DT2 ON DT2.id = D2.diagnosisType_id
                              WHERE D2.event_id = Event.id)
                    ) and Diagnostic.deleted = 0
    JOIN Client ON Client.id = Event.client_id
    LEFT JOIN ClientAddress ON ClientAddress.client_id = Event.client_id
                            AND ClientAddress.id = (SELECT MAX(id) FROM ClientAddress AS CA WHERE CA.Type=1 and CA.client_id = Event.client_id)
    LEFT JOIN Address ON Address.id = ClientAddress.address_id
    %s
    JOIN Diagnosis ON Diagnosis.id = Diagnostic.diagnosis_id
    JOIN vrbPersonWithSpeciality ON vrbPersonWithSpeciality.id = Event.execPerson_id
    JOIN rbResult ON rbResult.id = Event.result_id
    JOIN rbDiagnosticResult ON rbDiagnosticResult.id = Diagnostic.result_id
    %s
WHERE
    %s
GROUP BY
    result_id, diagnosticResultId, isPrimary, isDone, `order`, Event.execPerson_id
%s
"""
    db = QtGui.qApp.db
    tableEvent  = db.table('Event')
    tableDiagnosis  = db.table('Diagnosis')
    tableClient = db.table('Client')
    tableOrgStructureAddress = db.table('OrgStructure_Address')
    tableAddress = db.table('Address')
    tableAddressForClient = db.table('Address').alias('AddressForCLient')
    tableAddressHouse = db.table('AddressHouse')
    tablePerson = db.table('vrbPersonWithSpeciality')
    tableDiagnostic = db.table('Diagnostic')
    tableResult = db.table('rbResult')
    cond = []
    cond.append(tableEvent['deleted'].eq(0))
    cond.append(tableEvent['setDate'].dateLt(endDate.addDays(1)))
    cond.append(db.joinAnd([tableEvent['execDate'].dateGe(begDate),
                                       tableEvent['execDate'].dateLt(endDate.addDays(1))]))
    if eventTypeList:
        cond.append(tableEvent['eventType_id'].inlist(eventTypeList))
    elif eventPurposeId:
        cond.append(db.table('EventType')['purpose_id'].eq(eventPurposeId))
    if MKBFilter == 1:
        cond.append(tableDiagnosis['MKB'].ge(MKBFrom))
        cond.append(tableDiagnosis['MKB'].le(MKBTo))
    if MKBExFilter == 1:
        cond.append(tableDiagnosis['MKBEx'].ge(MKBExFrom))
        cond.append(tableDiagnosis['MKBEx'].le(MKBExTo))
    if personId:
        cond.append(tableDiagnostic['person_id'].eq(personId))
    elif orgStructureId:
        cond.append(tablePerson['orgStructure_id'].inlist(getOrgStructureDescendants(orgStructureId)))
    else:
        cond.append(tablePerson['org_id'].eq(QtGui.qApp.currentOrgId()))
    if specialityList:
        cond.append(tablePerson['speciality_id'].inlist(specialityList))
    if workOrgId:
        cond.append('EXISTS (SELECT * FROM ClientWork WHERE ClientWork.id = (SELECT MAX(id) FROM ClientWork AS CW WHERE CW.client_id = Client.id) and ClientWork.org_id=%d)' % (workOrgId))
    if sex:
        cond.append(tableClient['sex'].eq(sex))
    if ageFrom <= ageTo:
        date = str(QDate.currentDate().toString(Qt.ISODate))
        cond.append('IF(Diagnosis.endDate IS NOT NULL AND Diagnosis.endDate!=0, Diagnosis.endDate, DATE(\'%s\')) >= ADDDATE(Client.birthDate, INTERVAL %d YEAR)'%(date, ageFrom))
        cond.append('IF(Diagnosis.endDate IS NOT NULL AND Diagnosis.endDate!=0, Diagnosis.endDate, DATE(\'%s\')) <  SUBDATE(ADDDATE(Client.birthDate, INTERVAL %d YEAR),1)'%(date, ageTo+1))
    socStatusTypeJoin = ''
    if socStatusTypeId:
        tableClientSocStatus = db.table('ClientSocStatus')
        if begDate:
            cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['endDate'].isNotNull(),
                                               tableClientSocStatus['endDate'].ge(begDate)
                                              ]),
                                   tableClientSocStatus['endDate'].isNull()
                                  ]))
        if endDate:
            cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['begDate'].isNotNull(),
                                               tableClientSocStatus['begDate'].lt(endDate.addDays(1))
                                              ]),
                                   tableClientSocStatus['begDate'].isNull()
                                  ]))
        socStatusTypeJoin = u'''LEFT JOIN ClientSocStatus ON ClientSocStatus.client_id = Client.id'''
        cond.append(tableClientSocStatus['socStatusType_id'].eq(socStatusTypeId))
        cond.append(tableClientSocStatus['deleted'].eq(0))
    additionalJoin = ''
    if addressEnabled:
        if areaEnabled:
            if areaId:
                orgStructureIdList = getOrgStructureDescendants(areaId)
            else:
                orgStructureIdList = getOrgStructures(QtGui.qApp.currentOrgId())
            subCond = [ tableOrgStructureAddress['master_id'].inlist(orgStructureIdList),
                        tableOrgStructureAddress['house_id'].eq(tableAddress['house_id']),
                      ]
            cond.append(db.existsStmt(tableOrgStructureAddress, subCond))

        if clientAddressEnabled:
            if addressType in (STRICT_ADDRESS, NONRESIDENT_ADDRESS):
                clientAddressType = clientAddressType if addressType == STRICT_ADDRESS else 0
                additionalJoin = 'LEFT JOIN ClientAddress AS ClientAddressForClient ON ClientAddressForClient.client_id = Event.client_id AND ClientAddressForClient.id = (SELECT MAX(id) FROM ClientAddress AS CA2 WHERE CA2.Type=%d and CA2.client_id = Event.client_id) LEFT JOIN Address AS AddressForClient ON AddressForClient.id = ClientAddressForClient.address_id LEFT JOIN AddressHouse ON AddressHouse.id = AddressForClient.house_id'%clientAddressType
                if addressType == STRICT_ADDRESS:
                    if clientFlat:
                        cond.append(tableAddressForClient['flat'].eq(clientFlat))
                    if clientCorpus:
                        cond.append(tableAddressHouse['corpus'].eq(clientCorpus))
                    if clientHouse:
                        cond.append(tableAddressHouse['number'].eq(clientHouse))
                    if clientAddressStreetCode:
                        cond.append(tableAddressHouse['KLADRStreetCode'].eq(clientAddressStreetCode))
                    if clientAddressCityCodeList:
                        cond.append(tableAddressHouse['KLADRCode'].inlist(clientAddressCityCodeList))
                    else:
                        if clientAddressCityCode:
                            cond.append(tableAddressHouse['KLADRCode'].eq(clientAddressCityCode))
                else:
                    props = QtGui.qApp.preferences.appPrefs
                    kladrCodeList = [forceString(props.get('defaultKLADR', '')), forceString(props.get('provinceKLADR', ''))]
                    cond.append(tableAddressHouse['KLADRCode'].notInlist(kladrCodeList))
            else:
                foreignDocumentTypeId = forceInt(db.translate('rbDocumentType', 'code', '9', 'id'))
                documentCond = 'EXISTS(SELECT ClientDocument.`id` FROM ClientDocument WHERE ClientDocument.`documentType_id`=%d AND ClientDocument.`client_id`=Client.`id`)'%foreignDocumentTypeId
                cond.append(documentCond)
    stmt = stmt % (additionalJoin, socStatusTypeJoin, db.joinAnd(cond), 'ORDER BY vrbPersonWithSpeciality.name' if chkPersonDetail else '')
    return db.query(stmt)


class CEventResultSurvey(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setPayPeriodVisible(False)
        self.setTitle(u'Сводка по результату обращений')


    def getSetupDialog(self, parent):
        result = CEventResultSetupDialog(parent)
        result.setTitle(self.title())
        result.setVisibleVisitResult(True)
        result.setSocStatusTypeVisible(True)
        for i in xrange(result.gridLayout.count()):
            spacer=result.gridLayout.itemAt(i)
            if isinstance(spacer, QtGui.QSpacerItem):
                itemposition=result.gridLayout.getItemPosition(i)
                if itemposition!=(29, 0, 1, 1)and itemposition!=(8, 1, 1, 3):
                    result.gridLayout.removeItem(spacer)
        result.resize(400, 10)
        return result


    def build(self, params):
        query = selectData(params)
        chkPersonDetail = params.get('chkPersonDetail', False)
        chkVisitResultDetail = params.get('chkVisitResultDetail', False)
        reportData = {}
        personReportData = {}
        while query.next():
            record = query.record()
            count  = forceInt(record.value('count'))
            resultId  = forceRef(record.value('result_id'))
            if resultId:
                result = forceString(record.value('result'))
            else:
                result = None
            isDone    = forceBool(record.value('isDone'))
            isPrimary = forceInt(record.value('isPrimary'))
            order     = forceInt(record.value('order'))
            if chkPersonDetail:
                personId = forceRef(record.value('execPerson_id'))
                personName = forceString(record.value('personName'))
                reportData = personReportData.get((personName, personId), {})
            if chkVisitResultDetail:
                reportLineVisitResult = reportData.get(result, {})
                diagnosticResult = forceString(record.value('diagnosticResult'))
                reportLine = reportLineVisitResult.get(diagnosticResult, None)
            else:
                reportLine = reportData.get(result, None)
            if not reportLine:
                reportLine = [0]*7
                if chkVisitResultDetail:
                    reportLineVisitResult[diagnosticResult] = reportLine
                    reportData[result] = reportLineVisitResult
                else:
                    reportData[result] = reportLine
            reportLine[0] += count
            reportLine[1 if isDone else 2] += count
            if isPrimary == 1:
                reportLine[3] += count
            elif isPrimary == 2:
                reportLine[4] += count
            if order == 1:
                reportLine[5] += count
            elif order == 2:
                reportLine[6] += count
            if chkVisitResultDetail:
                reportLineVisitResult[diagnosticResult] = reportLine
                reportData[result] = reportLineVisitResult
            else:
                reportData[result] = reportLine
            if chkPersonDetail:
                personReportData[(personName, personId)] = reportData
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        if chkPersonDetail:
            tableColumns = [
            ('15', [u'Врач'],            CReportBase.AlignLeft),
            ('15%', [u'Результат обращений',    ], CReportBase.AlignLeft),
            ('10%', [u'Всего',        ], CReportBase.AlignRight),
            ('10%', [u'В том числе', u'Закончено',    ], CReportBase.AlignRight),
            ('10%', [u'',            u'Не закончено', ], CReportBase.AlignRight),
            ('10%', [u'',            u'Первичных',    ], CReportBase.AlignRight),
            ('10%', [u'',            u'Повторных',    ], CReportBase.AlignRight),
            ('10%', [u'',            u'Плановых',     ], CReportBase.AlignRight),
            ('10%', [u'',            u'Экстренных',   ], CReportBase.AlignRight),
            ]
        else:
            tableColumns = [
            ('5%',  [u'№' ], CReportBase.AlignRight),
            ('25%', [u'Результат обращений',    ], CReportBase.AlignLeft),
            ('10%', [u'Всего',        ], CReportBase.AlignRight),
            ('10%', [u'В том числе', u'Закончено',    ], CReportBase.AlignRight),
            ('10%', [u'',            u'Не закончено', ], CReportBase.AlignRight),
            ('10%', [u'',            u'Первичных',    ], CReportBase.AlignRight),
            ('10%', [u'',            u'Повторных',    ], CReportBase.AlignRight),
            ('10%', [u'',            u'Плановых',     ], CReportBase.AlignRight),
            ('10%', [u'',            u'Экстренных',   ], CReportBase.AlignRight),
            ]
        if chkVisitResultDetail:
            tableColumns.insert(2, ('25%', [u'Результат осмотра',    ], CReportBase.AlignLeft))
        table = createTable(cursor, tableColumns)
        if chkVisitResultDetail:
            table.mergeCells(0, 0, 2, 1)
            table.mergeCells(0, 1, 2, 1)
            table.mergeCells(0, 2, 2, 1)
            table.mergeCells(0, 3, 2, 1)
            table.mergeCells(0, 4, 1, 6)
        else:
            table.mergeCells(0, 0, 2, 1)
            table.mergeCells(0, 1, 2, 1)
            table.mergeCells(0, 2, 2, 1)
            table.mergeCells(0, 3, 1, 6)
        if chkPersonDetail:
            personKeys = personReportData.keys()
            personKeys.sort()
            totalAll = [0]*7
            for (personName, personId) in personKeys:
                reportData = personReportData.get((personName, personId), {})
                firstName = True
                results = reportData.keys()
                results.sort()
                total = [0]*7
                for result in results:
                    i = table.addRow()
                    if firstName:
                        table.setText(i, 0, personName)
                        firstName = False
                        oldRow = i
                    table.setText(i, 1, result if result is not None else u'-без указания-')
                    if chkVisitResultDetail:
                        reportLineVisitResult = reportData.get(result, [])
                        visitResultKeys = reportLineVisitResult.keys()
                        visitResultKeys.sort()
                        lenVisitResultKeys = len(visitResultKeys)
                        contRow = 1
                        oldVisitRow = i
                        for visitResult in visitResultKeys:
                            reportLine = reportLineVisitResult.get(visitResult, [])
                            table.setText(i, 2, visitResult if visitResult else u'-без указания-')
                            for j, v in enumerate(reportLine):
                                table.setText(i, 3+j, v)
                                total[j]+=v
                                totalAll[j]+=v
                            if lenVisitResultKeys > contRow:
                                contRow += 1
                                i = table.addRow()
                        table.mergeCells(oldVisitRow, 1, i-oldVisitRow + 1, 1)
                    else:
                        reportLine = reportData[result]
                        for j, v in enumerate(reportLine):
                            table.setText(i, 2+j, v)
                            total[j]+=v
                            totalAll[j]+=v
                i = table.addRow()
                table.setText(i, 1, u'итого', CReportBase.TableTotal)
                for j, v in enumerate(total):
                    table.setText(i, 3+j if chkVisitResultDetail else 2+j, v, CReportBase.TableTotal)
                    total[j]+=v
                table.mergeCells(oldRow, 0, i-oldRow + 1, 1)
            i = table.addRow()
            table.setText(i, 0, u'итого', CReportBase.TableTotal)
            for j, v in enumerate(totalAll):
                table.setText(i, 3+j if chkVisitResultDetail else 2+j, v, CReportBase.TableTotal)
        else:
            results = reportData.keys()
            results.sort()
            n = 0
            total = [0]*7
            for result in results:
                n += 1
                i = table.addRow()
                table.setText(i, 0, n)
                table.setText(i, 1, result if result is not None else u'-без указания-')
                if chkVisitResultDetail:
                    reportLineVisitResult = reportData.get(result, [])
                    visitResultKeys = reportLineVisitResult.keys()
                    visitResultKeys.sort()
                    lenVisitResultKeys = len(visitResultKeys)
                    contRow = 1
                    oldVisitRow = i
                    for visitResult in visitResultKeys:
                        reportLine = reportLineVisitResult.get(visitResult, [])
                        table.setText(i, 2, visitResult if visitResult else u'-без указания-')
                        for j, v in enumerate(reportLine):
                            table.setText(i, 3+j, v)
                            total[j]+=v
                        if lenVisitResultKeys > contRow:
                            contRow += 1
                            i = table.addRow()
                    table.mergeCells(oldVisitRow, 1, i-oldVisitRow + 1, 1)
                else:
                    reportLine = reportData[result]
                    for j, v in enumerate(reportLine):
                        table.setText(i, 2+j, v)
                        total[j]+=v
                if chkVisitResultDetail:
                    table.mergeCells(oldVisitRow, 0, i-oldVisitRow + 1, 1)
            i = table.addRow()
            table.setText(i, 1, u'итого', CReportBase.TableTotal)
            for j, v in enumerate(total):
                table.setText(i, 3+j if chkVisitResultDetail else 2+j, v, CReportBase.TableTotal)
                total[j]+=v
        return doc


class CEventResultSetupDialog(CDialogBase, Ui_EventResultSetupDialog):
    def __init__(self, parent=None):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.cmbEventPurpose.setTable('rbEventTypePurpose', True, filter='code != \'0\'')
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())
        self.cmbSocStatusClass.setTable('rbSocStatusClass', True)
        self.cmbSocStatusType.setTable('rbSocStatusType', True)
        self.cmbArea.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbArea.setValue(QtGui.qApp.currentOrgStructureId())

        self.cmbResult.setTable('rbResult', addNone=True)

        self._visibleResult = False
        self.setVisibleResult(self._visibleResult)

        self._visiblePrimary = False
        self.setVisiblePrimary(self._visiblePrimary)

        self._visibleOrder = False
        self.setVisibleOrder(self._visibleOrder)

        self._visibleVisitResult = False
        self.setVisibleVisitResult(self._visibleVisitResult)
        self.setSocStatusTypeVisible(False)
        self.setAdditionalGraphsVisible(False)


    def setAdditionalGraphsVisible(self, value):
        self._additionalGraphsVisible = value
        self.lblAdditionalGraphs.setVisible(value)
        self.chkSocStatus.setVisible(value)
        self.chkPolicy.setVisible(value)
        self.chkWork.setVisible(value)
        self.chkAddionalAddress.setVisible(value)
        self.chkDocument.setVisible(value)


    def setSocStatusTypeVisible(self, value):
        self._socStatusTypeVisible = value
        self.lblSocStatusClass.setVisible(value)
        self.cmbSocStatusClass.setVisible(value)
        self.lblSocStatusType.setVisible(value)
        self.cmbSocStatusType.setVisible(value)


    def setVisibleResult(self, value):
        self._visibleResult = value
        self.lblResult.setVisible(value)
        self.cmbResult.setVisible(value)


    def setVisibleVisitResult(self, value):
        self._visibleVisitResult = value
        self.chkVisitResult.setVisible(value)


    def setVisiblePrimary(self, value):
        self._visiblePrimary = value
        self.lblPrimary.setVisible(value)
        self.cmbPrimary.setVisible(value)


    def setVisibleOrder(self, value):
        self._visibleOrder = value
        self.lblOrder.setVisible(value)
        self.cmbOrder.setVisible(value)


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        self.cmbEventPurpose.setValue(params.get('eventPurposeId', None))
        self.eventTypeList = params.get('eventTypeList', [])
        if self.eventTypeList:
            db = QtGui.qApp.db
            tableET = db.table('EventType')
            records = db.getRecordList(tableET, [tableET['name']], [tableET['deleted'].eq(0), tableET['id'].inlist(self.eventTypeList)])
            nameList = []
            for record in records:
                nameList.append(forceString(record.value('name')))
            self.lblEventTypeList.setText(u', '.join(name for name in nameList if name))
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))
        self.specialityList = params.get('specialityList', [])
        if self.specialityList:
            db = QtGui.qApp.db
            table = db.table('rbSpeciality')
            records = db.getRecordList(table, [table['name']], [table['id'].inlist(self.specialityList)])
            self.lblSpecialityList.setText(u', '.join(forceString(record.value('name')) for record in records if forceString(record.value('name'))))
        self.cmbPerson.setValue(params.get('personId', None))
        self.cmbWorkOrganisation.setValue(params.get('workOrgId', None))
        self.cmbSex.setCurrentIndex(params.get('sex', 0))
        self.edtAgeFrom.setValue(params.get('ageFrom', 0))
        self.edtAgeTo.setValue(params.get('ageTo', 150))
        addressEnabled = params.get('addressEnabled', False)
        addressType = params.get('addressType', 0)
        self.cmbAddressType.setCurrentIndex(addressType)
        self.chkAddress.setChecked(addressEnabled)
        areaEnabled = params.get('areaEnabled', False)
        self.chkArea.setChecked(areaEnabled)
#        self.cmbArea.setEnabled(addressEnabled and areaEnabled)
        self.cmbArea.setValue(params.get('areaId', None))
#        self.setEnabledCmbAddressType(addressEnabled and addressEnabled)
#        self.setEnabledAddress(addressEnabled and addressEnabled and addressType==STRICT_ADDRESS)
        MKBFilter = params.get('MKBFilter', 0)
        self.cmbMKBFilter.setCurrentIndex(MKBFilter if MKBFilter else 0)
        self.edtMKBFrom.setText(params.get('MKBFrom', 'A00'))
        self.edtMKBTo.setText(params.get('MKBTo',   'Z99.9'))
        MKBExFilter = params.get('MKBExFilter', 0)
        self.cmbMKBExFilter.setCurrentIndex(MKBExFilter if MKBExFilter else 0)
        self.edtMKBExFrom.setText(params.get('MKBExFrom', 'A00'))
        self.edtMKBExTo.setText(params.get('MKBExTo',   'Z99.9'))
        self.chkClientAddress.setChecked(params.get('clientAddressEnabled', False) and addressEnabled)
        self.cmbClientAddressType.setCurrentIndex(params.get('clientAddressType', 0))
        self.cmbClientAddressCity.setCode(params.get('clientAddressCityCode', ''))
        self.cmbClientAddressStreet.setCode(params.get('clientAddressStreetCode', ''))
        self.edtAddressHouse.setText(params.get('clientHouse', ''))
        self.edtAddressCorpus.setText(params.get('clientCorpus', ''))
        self.edtAddressFlat.setText(params.get('clientFlat', ''))
        self.cmbOrder.setCurrentIndex(params.get('order', 0))
        self.cmbPrimary.setCurrentIndex(params.get('primary', 0))
        self.cmbResult.setValue(params.get('resultId', None))
        if self._socStatusTypeVisible:
            self.cmbSocStatusClass.setValue(params.get('socStatusClassId', None))
            self.cmbSocStatusType.setValue(params.get('socStatusTypeId', None))
        if self.cmbPerson.value():
            self.chkPersonDetail.setChecked(False)
        else:
            self.chkPersonDetail.setChecked(params.get('chkPersonDetail', False))
        self.chkVisitResult.setChecked(params.get('chkVisitResultDetail', False))
        if self._additionalGraphsVisible:
            self.chkSocStatus.setChecked(params.get('chkSocStatus', False))
            self.chkPolicy.setChecked(params.get('chkPolicy', False))
            self.chkWork.setChecked(params.get('chkWork', False))
            self.chkAddionalAddress.setChecked(params.get('chkAddionalAddress', False))
            self.chkDocument.setChecked(params.get('chkDocument', False))


    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['eventPurposeId'] = self.cmbEventPurpose.value()
        result['eventTypeList'] = self.eventTypeList
        result['orgStructureId'] = self.cmbOrgStructure.value()
        result['specialityList'] = self.specialityList
        result['personId'] = self.cmbPerson.value()
        result['workOrgId'] = self.cmbWorkOrganisation.value()
        result['sex'] = self.cmbSex.currentIndex()
        result['ageFrom'] = self.edtAgeFrom.value()
        result['ageTo'] = self.edtAgeTo.value()
        result['addressEnabled'] = self.chkAddress.isChecked()
        result['areaEnabled'] = self.chkArea.isChecked()
        result['areaId'] = self.cmbArea.value()
        result['MKBFilter'] = self.cmbMKBFilter.currentIndex()
        result['MKBFrom']   = unicode(self.edtMKBFrom.text())
        result['MKBTo']     = unicode(self.edtMKBTo.text())
        result['MKBExFilter'] = self.cmbMKBExFilter.currentIndex()
        result['MKBExFrom']   = unicode(self.edtMKBExFrom.text())
        result['MKBExTo']     = unicode(self.edtMKBExTo.text())
        if self.cmbPerson.value():
            result['chkPersonDetail'] = False
        else:
            result['chkPersonDetail'] = forceBool(self.chkPersonDetail.isChecked())
        result['clientAddressEnabled'] = self.chkClientAddress.isChecked()
        if self.chkClientAddress.isChecked():
            result['addressType'] = self.cmbAddressType.currentIndex()
            result['clientAddressType'] = self.cmbClientAddressType.currentIndex()
            result['clientAddressCityCode'] = self.cmbClientAddressCity.code()
            result['clientAddressCityCodeList'] = self.cmbClientAddressCity.getChildrenCodeList(result['clientAddressCityCode'])
            result['clientAddressStreetCode'] = self.cmbClientAddressStreet.code()
            result['clientHouse'] = self.edtAddressHouse.text()
            result['clientCorpus'] = self.edtAddressCorpus.text()
            result['clientFlat'] = self.edtAddressFlat.text()
        if self._socStatusTypeVisible:
            result['socStatusClassId'] = self.cmbSocStatusClass.value()
            result['socStatusTypeId'] = self.cmbSocStatusType.value()
        if self._visibleOrder:
            result['order'] = self.cmbOrder.currentIndex()
        if self._visiblePrimary:
            result['primary'] = self.cmbPrimary.currentIndex()
        if self._visibleResult:
            result['resultId'] = self.cmbResult.value()
        result['chkVisitResultDetail']  = self.chkVisitResult.isChecked()
        if self._additionalGraphsVisible:
            result['chkSocStatus']  = self.chkSocStatus.isChecked()
            result['chkPolicy']  = self.chkPolicy.isChecked()
            result['chkWork']  = self.chkWork.isChecked()
            result['chkAddionalAddress']  = self.chkAddionalAddress.isChecked()
            result['chkDocument']  = self.chkDocument.isChecked()
        return result


    def setEnabledAddress(self, value):
        self.cmbClientAddressType.setEnabled(value)
        self.cmbClientAddressCity.setEnabled(value)
        self.cmbClientAddressStreet.setEnabled(value)
        self.lblAddressHouse.setEnabled(value)
        self.edtAddressHouse.setEnabled(value)
        self.lblAddressCorpus.setEnabled(value)
        self.edtAddressCorpus.setEnabled(value)
        self.lblAddressFlat.setEnabled(value)
        self.edtAddressFlat.setEnabled(value)


    def setEnabledCmbAddressType(self, value):
        self.cmbAddressType.setEnabled(value)


    @pyqtSignature('bool')
    def on_chkAddress_toggled(self, value):
        self.chkArea.setEnabled(value)
        self.cmbArea.setEnabled(value and self.chkArea.isChecked())
        self.chkClientAddress.setEnabled(value)
        self.setEnabledCmbAddressType(value and self.chkClientAddress.isChecked())
        self.setEnabledAddress(value and self.chkClientAddress.isChecked() and self.cmbAddressType.currentIndex()==STRICT_ADDRESS)


    @pyqtSignature('bool')
    def on_chkClientAddress_toggled(self, value):
        self.setEnabledCmbAddressType(value and self.chkAddress.isChecked())
        self.setEnabledAddress(value and self.chkAddress.isChecked() and self.cmbAddressType.currentIndex()==STRICT_ADDRESS)


    @pyqtSignature('int')
    def on_cmbAddressType_currentIndexChanged(self, index):
        self.setEnabledAddress(self.chkClientAddress.isChecked() and self.chkAddress.isChecked() and index==STRICT_ADDRESS)


    @pyqtSignature('QDate')
    def on_edtBegDate_dateChanged(self, date):
        self.cmbPerson.setBegDate(date)


    @pyqtSignature('QDate')
    def on_edtEndDate_dateChanged(self, date):
        self.cmbPerson.setEndDate(date)


    @pyqtSignature('int')
    def on_cmbClientAddressCity_currentIndexChanged(self, index):
        self.cmbClientAddressStreet.setCity(self.cmbClientAddressCity.code())


    @pyqtSignature('int')
    def on_cmbEventPurpose_currentIndexChanged(self, index):
        eventPurposeId = self.cmbEventPurpose.value()
        if eventPurposeId:
            filter = 'EventType.purpose_id =%d' % eventPurposeId
            self.cmbResult.setFilter('eventPurpose_id=%d' % eventPurposeId)
        else:
            filter = getWorkEventTypeFilter(isApplyActive=True)
            self.cmbResult.setFilter(None)


    @pyqtSignature('int')
    def on_cmbOrgStructure_currentIndexChanged(self, index):
        orgStructureId = self.cmbOrgStructure.value()
        self.cmbPerson.setOrgStructureId(orgStructureId)


    @pyqtSignature('int')
    def on_cmbPerson_currentIndexChanged(self, index):
        personId = self.cmbPerson.value()
        if personId:
            self.chkPersonDetail.setChecked(not personId)
        self.chkPersonDetail.setEnabled(not personId)


    @pyqtSignature('')
    def on_btnSpecialityList_clicked(self):
        self.specialityList = []
        dialog = CSpecialityListDialog(self)
        if dialog.exec_():
            self.specialityList = dialog.values()
            if self.specialityList:
                db = QtGui.qApp.db
                tableSpeciality = db.table('rbSpeciality')
                records = db.getRecordList(tableSpeciality, [tableSpeciality['name']], [tableSpeciality['id'].inlist(self.specialityList)])
                nameList = []
                for record in records:
                    nameList.append(forceString(record.value('name')))
                self.lblSpecialityList.setText(u', '.join(name for name in nameList if name))
                self.cmbPerson.setFilter(db.table('vrbPersonWithSpecialityAndPost')['speciality_id'].inlist(self.specialityList))
            else:
                self.cmbPerson.setFilter('')
                self.lblSpecialityList.setText(u'не задано')


    @pyqtSignature('')
    def on_btnEventTypeList_clicked(self):
        self.eventTypeList = []
        eventPurposeId = self.cmbEventPurpose.value()
        if eventPurposeId:
            filter = u'EventType.purpose_id = %d' % eventPurposeId
        else:
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
                self.lblEventTypeList.setText(u', '.join(name for name in nameList if name))
            else:
                self.lblEventTypeList.setText(u'не задано')


    @pyqtSignature('')
    def on_btnSelectWorkOrganisation_clicked(self):
        orgId = selectOrganisation(self, self.cmbWorkOrganisation.value(), False)
        self.cmbWorkOrganisation.updateModel()
        if orgId:
            self.cmbWorkOrganisation.setValue(orgId)


    @pyqtSignature('int')
    def on_cmbMKBFilter_currentIndexChanged(self, index):
        self.edtMKBFrom.setEnabled(index == 1)
        self.edtMKBTo.setEnabled(index == 1)


    @pyqtSignature('int')
    def on_cmbMKBExFilter_currentIndexChanged(self, index):
        self.edtMKBExFrom.setEnabled(index == 1)
        self.edtMKBExTo.setEnabled(index == 1)
