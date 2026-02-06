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
from PyQt4.QtCore       import pyqtSignature, QDate

from library.Utils      import (calcAge, forceDate, forceInt, forceRef, forceBool,
                                forceString, formatDate, formatName, formatSex, formatSNILS)
from library.database   import addDateInRange
from library.DialogBase import CDialogBase

from Orgs.Utils                import getOrgStructureDescendants
from RefBooks.TempInvalidState import CTempInvalidState
from Registry.Utils            import getClientInfo, getClientPhonesEx
from Reports.Report            import CReport
from Reports.ReportBase        import CReportBase, createTable

from Reports.Ui_TempInvalidSetup import Ui_TempInvalidSetupDialog


def selectData(params):
    begDate = params.get('begDate', QDate())
    endDate = params.get('endDate', QDate())
    byPeriod = params.get('byPeriod', False)
    doctype = params.get('doctype', 0)
    tempInvalidReasonIdList = params.get('tempInvalidReasonIdList', None)
    onlyClosed = params.get('onlyClosed', True)
    orgStructureId = params.get('orgStructureId', None)
    personId = params.get('personId', None)
    durationFrom = params.get('durationFrom', 0)
    durationTo = params.get('durationTo', 0)
    sex = params.get('sex', 0)
    ageFrom = params.get('ageFrom', 0)
    ageTo = params.get('ageTo', 150)
    socStatusClassId = params.get('socStatusClassId', None)
    socStatusTypeId = params.get('socStatusTypeId', None)
    MKBFilter = params.get('MKBFilter', 0)
    MKBFrom   = params.get('MKBFrom', '')
    MKBTo     = params.get('MKBTo', '')
    insuranceOfficeMark = params.get('insuranceOfficeMark', 0)
    hasBeginPerson = params.get('hasBeginPerson', True)
    hasEndPerson = params.get('hasEndPerson', True)
    placeWork = params.get('placeWork', True)
    electronic = params.get('electronic', True)
    clientAreaCheck = params.get('isClientArea', False)
    clientAreaValue = params.get('ClientAreaValue', None)
    orderByCheck = params.get('isOrderBy', False)
    orderByValue = params.get('OrderByValue', None)
    if electronic:
        electronicDict = {1: '1', 2: '0'}
        electronic = electronicDict[electronic]
    isExternal = params.get('isExternal', False)

    stmt="""
SELECT
   TempInvalid.client_id,
   TempInvalidDocument.`serial`,
   TempInvalidDocument.`number`,
   TempInvalidDocument.isExternal,
   IF(TempInvalidDocument.annulmentReason_id IS NOT NULL, 1, 0) AS isAnnulled,
  -- IF(TempInvalid.begDate > TempInvalidDocument.issueDate, TempInvalid.begDate, TempInvalidDocument.issueDate) AS begDate,
   TempInvalid.begDate AS begDate,
   IF(TempInvalidDocument.isExternal = 1,
    (SELECT MIN(TIP.endDate) FROM TempInvalid_Period TIP WHERE TIP.master_id = TempInvalid.id), TempInvalid.endDate) AS endDate,
   %s
   %s
   Diagnosis.MKB,
   rbTempInvalidReason.code AS reasonCode,
   rbTempInvalidReason.name AS reasonName,
   ClientWork.freeInput,
   TempInvalidDocument.placeWork AS clientWorkPlace,
   Organisation.shortName,
   TempInvalidDocument.duplicate AS isDuplicate,
   TempInvalid.caseBegDate,
   rbTempInvalidResult.name AS resultName,
   c_os.name as clientAttachName
   FROM TempInvalid
   INNER JOIN TempInvalidDocument ON TempInvalid.id = TempInvalidDocument.master_id
   LEFT JOIN Diagnosis ON Diagnosis.id = TempInvalid.diagnosis_id
   LEFT JOIN Person    ON Person.id = TempInvalid.person_id
   LEFT JOIN rbTempInvalidReason ON rbTempInvalidReason.id = TempInvalid.tempInvalidReason_id
   LEFT JOIN rbTempInvalidResult ON rbTempInvalidResult.id = TempInvalid.result_id
   LEFT JOIN Client    ON Client.id = TempInvalid.client_id
   LEFT JOIN ClientWork ON ClientWork.id = (SELECT MAX(CW.id) FROM ClientWork AS CW
   WHERE CW.client_id = TempInvalid.client_id AND CW.deleted = 0)
   LEFT JOIN Organisation ON Organisation.id = ClientWork.org_id
  LEFT JOIN ClientAttach on ClientAttach.client_id = Client.id and ClientAttach.deleted = 0 and ClientAttach.endDate IS NULL
  LEFT JOIN OrgStructure c_os on c_os.id = ClientAttach.orgStructure_id and c_os.deleted = 0
WHERE
   %s

    """
    defaultOrderBy = u"  ORDER BY number, Client.lastName, Client.firstName, Client.patrName, begDate  "

    if orderByCheck and orderByValue != None:
        if  orderByValue == 0:
            defaultOrderBy = u"  ORDER BY Client.lastName, Client.firstName, Client.patrName  "
        elif orderByValue == 1:
            defaultOrderBy = u"  ORDER BY begDate, Client.lastName, Client.firstName, Client.patrName  "

    stmt = stmt + defaultOrderBy
    db = QtGui.qApp.db
    tableTempInvalid = db.table('TempInvalid')
    tableTempInvalidDocument = db.table('TempInvalidDocument')
    tableClient = db.table('Client')
    cond = []
    if doctype:
        cond.append(tableTempInvalid['doctype_id'].eq(doctype))
    else:
        cond.append(tableTempInvalid['type'].eq(0))
    cond.append(tableTempInvalid['deleted'].eq(0))
    if tempInvalidReasonIdList:
        cond.append(tableTempInvalid['tempInvalidReason_id'].inlist(tempInvalidReasonIdList))
    if byPeriod:
        cond.append(tableTempInvalid['caseBegDate'].le(endDate))
        cond.append(tableTempInvalid['endDate'].ge(begDate))
    else:
        addDateInRange(cond, tableTempInvalid['endDate'], begDate, endDate)
    if onlyClosed:
        cond.append(tableTempInvalid['state'].eq(CTempInvalidState.closed))
    if orgStructureId:
        tablePerson = db.table('Person')
        cond.append(tablePerson['orgStructure_id'].inlist(getOrgStructureDescendants(orgStructureId)))
    if personId:
        cond.append(tableTempInvalid['person_id'].eq(personId))
    if durationTo:
        cond.append(tableTempInvalid['duration'].ge(durationFrom))
        cond.append(tableTempInvalid['duration'].le(durationTo))
    if sex:
        cond.append(tableClient['sex'].eq(sex))
    if ageFrom <= ageTo:
        cond.append('TempInvalid.begDate >= ADDDATE(Client.birthDate, INTERVAL %d YEAR)'%ageFrom)
        cond.append('TempInvalid.begDate < SUBDATE(ADDDATE(Client.birthDate, INTERVAL %d YEAR),1)'%(ageTo+1))
    if socStatusTypeId:
        subStmt = ('SELECT ClientSocStatus.id FROM ClientSocStatus WHERE '
                  +'ClientSocStatus.deleted=0 AND ClientSocStatus.client_id=Client.id AND '
                  +'ClientSocStatus.socStatusType_id=%d' % socStatusTypeId)
        cond.append('EXISTS('+subStmt+')')
    elif socStatusClassId:
        subStmt = ('SELECT ClientSocStatus.id FROM ClientSocStatus WHERE '
                  +'ClientSocStatus.deleted=0 AND ClientSocStatus.client_id=Client.id AND '
                  +'ClientSocStatus.socStatusClass_id=%d' % socStatusClassId)
        cond.append('EXISTS('+subStmt+')')
    if MKBFilter == 1:
        tableDiagnosis = db.table('Diagnosis')
        cond.append(tableDiagnosis['MKB'].ge(MKBFrom))
        cond.append(tableDiagnosis['MKB'].le(MKBTo))
    elif MKBFilter == 2:
        tableDiagnosis = db.table('Diagnosis')
        cond.append(db.joinOr([tableDiagnosis['MKB'].eq(''), tableDiagnosis['MKB'].isNull()]))
    if insuranceOfficeMark in (1, 2):
        cond.append(tableTempInvalid['insuranceOfficeMark'].eq(insuranceOfficeMark-1))
    if placeWork:
        cond.append(''' (TempInvalidDocument.placeWork IS NULL OR TempInvalidDocument.placeWork IS NOT NULL) ''')
    if params['electronic']:
        cond.append(tableTempInvalidDocument['electronic'].eq(electronic))
    if clientAreaCheck and clientAreaValue:
        cond.append(u' ClientAttach.orgStructure_id = ' + forceString(clientAreaValue))
    if not isExternal:
        cond.append(u' (TempInvalidDocument.isExternal = 0 ) ')
    return db.query(stmt % (u'''(SELECT vrbPersonWithSpeciality.name
    FROM vrbPersonWithSpeciality
    WHERE vrbPersonWithSpeciality.id = TempInvalidDocument.execPerson_id) AS endPersonName, ''' if hasEndPerson else u'',

    u'''(SELECT vrbPersonWithSpeciality.name
    FROM vrbPersonWithSpeciality
    WHERE vrbPersonWithSpeciality.id = TempInvalidDocument.person_id) AS begPersonName, ''' if hasBeginPerson else u'',

    db.joinAnd(cond)))


class CTempInvalidList(CReport):
    name = u'Список пациентов с ВУТ'

    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(self.name)


    def getSetupDialog(self, parent):
        result = CTempInvalidSetupDialog(parent)
        result.setElectronicVisible(True)
        result.setAnalysisMode(True)
        result.setClientAreaVisible(True)
        result.setOrderByVisible(True)
        result.setTitle(self.title())
        return result


    def build(self, params):
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
#        byPeriod = params.get('byPeriod', False)
#        doctype = params.get('doctype', 0)
#        tempInvalidReason = params.get('tempInvalidReason', None)
#        onlyClosed = params.get('onlyClosed', True)
#        orgStructureId = params.get('orgStructureId', None)
#        personId = params.get('personId', None)
#        durationFrom = params.get('durationFrom', 0)
#        durationTo = params.get('durationTo', 0)
#        sex = params.get('sex', 0)
#        ageFrom = params.get('ageFrom', 0)
#        ageTo = params.get('ageTo', 150)
#        socStatusClassId = params.get('socStatusClassId', None)
#        socStatusTypeId = params.get('socStatusTypeId', None)
#        MKBFilter = params.get('MKBFilter', 0)
#        MKBFrom   = params.get('MKBFrom', '')
#        MKBTo     = params.get('MKBTo', '')
#        insuranceOfficeMark = params.get('insuranceOfficeMark', 0)
        hasRegAddress = params.get('hasRegAddress', True)
        hasLocAddress = params.get('hasLocAddress', True)
        hasBeginPerson = params.get('hasBeginPerson', True)
        hasEndPerson = params.get('hasEndPerson', True)
        placeWork = params.get('placeWork', True)
        isClientArea = params.get('isClientArea', False)

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.name)
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        tableColumns = [
            ('3%',  [u'№' ],   CReportBase.AlignRight),
            ('3%',  [u'код' ], CReportBase.AlignLeft),
            ('8%', [u'ФИО,\nдата рождения (возраст),\nпол' ], CReportBase.AlignLeft),
            ('15%', [u'Адрес,\nтелефон'], CReportBase.AlignLeft),
            ('10%', [u'СНИЛС,\nполис'],   CReportBase.AlignLeft),
            ('5%',  [u'Шифр МКБ\nТип'],   CReportBase.AlignLeft),
            ('7%',  [u'Период'],          CReportBase.AlignLeft),
            ('4%',  [u'Дней'],            CReportBase.AlignRight),
            ('8%',  [u'Серия\nНомер'],    CReportBase.AlignLeft),
            ('6%',  [u'Дубликат'],        CReportBase.AlignLeft),
            ('7%',  [u'Дата выдачи'],     CReportBase.AlignLeft),
            ('7%',  [u'Результат закрытия листка'], CReportBase.AlignLeft),
            ]
        if hasBeginPerson:
           tableColumns.append(('6.5%' if (hasBeginPerson and hasEndPerson) else '8%', [u'Начавший БЛ'],    CReportBase.AlignLeft))
        if hasEndPerson:
           tableColumns.append(('6.5%' if (hasBeginPerson and hasEndPerson) else '8%', [u'Закончивший БЛ'], CReportBase.AlignLeft))
        if placeWork:
           tableColumns.append(('6.5%' if (hasBeginPerson and hasEndPerson) else '8%', [u'Место работы'], CReportBase.AlignLeft))
        if isClientArea:
            tableColumns.append(('7%', [u'Участок'], CReportBase.AlignLeft ))
        table = createTable(cursor, tableColumns)
        n = 0
        query = selectData(params)
        while query.next():
            n += 1
            record = query.record()
            clientId = forceRef(record.value('client_id'))
            serial = forceString(record.value('serial'))
            number = forceString(record.value('number'))
            isExternal = forceBool(record.value('isExternal'))
            isAnnulled = forceBool(record.value('isAnnulled'))
            begDate = forceDate(record.value('begDate'))
            endDate = forceDate(record.value('endDate'))
            duration = abs(endDate.toJulianDay() - begDate.toJulianDay()) + 1
            endPersonName = forceString(record.value('endPersonName'))
            begPersonName = forceString(record.value('begPersonName'))
            MKB  = forceString(record.value('MKB'))
            reasonCode  = forceString(record.value('reasonCode')) + u'-' + forceString(record.value('reasonName'))
            duplicate = forceInt(record.value('isDuplicate'))
            areaName = forceString( record.value('clientAttachName') )
            if duplicate:
                duplicate = u'Да'
            else:
                duplicate = u''

            info = getClientInfo(clientId, hasRegAddress, hasLocAddress)
            name = formatName(info['lastName'], info['firstName'], info['patrName'])
            nameBDateAndSex = '\n'.join([name, '%s (%s)'%(formatDate(info['birthDate']),calcAge(info['birthDate'], begDate)), formatSex(info['sexCode'])])
            caseBegDate = forceString(record.value('caseBegDate'))
            resultName  = forceString(record.value('resultName'))

            def getListWithoutEmptyAndWhitespaceStrings(lst):
                return filter(lambda x: x != '' and not x.isspace(), lst)

            addressAndPhoneList = []
            if hasRegAddress:
                addressAndPhoneList.append(info.get('regAddress', u'не указан'))
            if hasLocAddress:
                addressAndPhoneList.append(info.get('locAddress', u'не указан'))
            addressAndPhoneList.append(getClientPhonesEx(clientId))
            addressAndPhone = '\n'.join(getListWithoutEmptyAndWhitespaceStrings(addressAndPhoneList))
            SNILSAndPolicy = '\n'.join(getListWithoutEmptyAndWhitespaceStrings([formatSNILS(info['SNILS']), info.get('policy', u'нет')]))
            MKBandType = '\n'.join(getListWithoutEmptyAndWhitespaceStrings([MKB, reasonCode]))
            period = '\n'.join([forceString(begDate), forceString(endDate)])
            external = u'(внешний)' if isExternal else ''
            annulled = u'(аннулирован)' if isAnnulled else ''
            serialAndNumber = '\n'.join(getListWithoutEmptyAndWhitespaceStrings([serial, number, external, annulled]))
            i = table.addRow()
            table.setText(i, 0, n)
            table.setText(i, 1, clientId)
            table.setText(i, 2, nameBDateAndSex)
            table.setText(i, 3, addressAndPhone)
            table.setText(i, 4, SNILSAndPolicy)
            table.setText(i, 5, MKBandType)
            table.setText(i, 6, period)
            if begDate and endDate:
                table.setText(i, 7, duration, blockFormat=CReportBase.AlignLeft)
            table.setText(i, 8, serialAndNumber)
            table.setText(i, 9, duplicate)
            table.setText(i, 10, caseBegDate)
            table.setText(i, 11, resultName)
            if hasBeginPerson and hasEndPerson:
                table.setText(i, 12, begPersonName)
                table.setText(i, 13, endPersonName)
            elif hasBeginPerson:
                table.setText(i, 12, begPersonName)
            elif hasEndPerson:
                table.setText(i, 12, endPersonName)
            if placeWork:
                # tt3497 место работы должно выбираться не из ClientWork, а из tempInvalidDocument.workPlace
                # shortName = forceString(record.value('shortName'))
                # freeInput = forceString(record.value('freeInput'))
                clientPlaceWork = forceString(record.value('clientWorkPlace'))
                table.setText(i, len(tableColumns)-2 if isClientArea else len(tableColumns)-1, clientPlaceWork if clientPlaceWork else u'' ) # shortName if shortName else freeInput)
            if isClientArea:
                table.setText(i, len(tableColumns)-1, areaName)
        return doc


class CTempInvalidSetupDialog(CDialogBase, Ui_TempInvalidSetupDialog):
    def __init__(self, parent=None):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.setAnalysisMode(False)
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())
        filter = 'type=0'
        self.cmbDoctype.setTable('rbTempInvalidDocument', True, filter)
        self.cmbReason.setTable('rbTempInvalidReason', False, filter)
        self.cmbSocStatusType.setTable('vrbSocStatusType', True)
        self.setCntUserVisible(False)
        self.setTempInvalidReceiverVisible(False)
        self.setTempInvalidDuplicateVisible(False)
        self.setTempInvalidDuplicateWorkVisible(False)
        self.setClientNameSortVisible(False)
        self.setDateSortVisible(False)
        self.setTempInvalidCOVID19Visible(False)
        self.setElectronicVisible(False)
        self.setClientAreaVisible(False)
        self.setOrderByVisible(False)
        self.chkOrderBy.stateChanged.connect(self.setOrderByEnabled)
        self.chkClientArea.stateChanged.connect(self.setClientAreaEnabled)


    def setClientAreaEnabled(self):
        if self.chkClientArea.isChecked():
            self.cmbClientArea.setEnabled(True)
        else:
            self.cmbClientArea.setEnabled(False)


    def setOrderByEnabled(self):
        if self.chkOrderBy.isChecked():
            self.cmbOrderBy.setEnabled(True)
        else:
            self.cmbOrderBy.setEnabled(False)



    def setClientAreaVisible(self, value):
        self.isClientAreaVisible = value
        self.lblClientArea.setVisible(value)
        self.chkClientArea.setVisible(value)
        self.cmbClientArea.setVisible(value)


    def setOrderByVisible(self, value):
        self.isOrderByVisible = value
        self.lblOrderBy.setVisible(value)
        self.chkOrderBy.setVisible(value)
        self.cmbOrderBy.setVisible(value)


    def setCntUserVisible(self, value):
        self.isCntUserVisible = value
        self.lblCntUser.setVisible(value)
        self.edtCntUser.setVisible(value)


    def setTempInvalidReceiverVisible(self, value):
        self.isTempInvalidReceiverVisible = value
        self.chkTempInvalidReceiver.setVisible(value)


    def setTempInvalidCOVID19Visible(self, value):
        self.isTempInvalidCOVID19Visible = value
        self.chkTempInvalidCOVID19.setVisible(value)


    def setElectronicVisible(self, value):
        self.isElectronicVisible = value
        self.lblElectronic.setVisible(value)
        self.cmbElectronic.setVisible(value)


    def setTempInvalidDuplicateVisible(self, value):
        self.isTempInvalidDuplicateVisible = value
        self.chkTempInvalidDuplicate.setVisible(value)


    def setTempInvalidDuplicateWorkVisible(self, value):
        self.isTempInvalidDuplicateWorkVisible = value
        self.chkTempInvalidDuplicateWork.setVisible(value)


    def setClientNameSortVisible(self, value):
        self.clientNameSortVisible = value
        self.chkClientNameSort.setVisible(value)


    def setDateSortVisible(self, value):
        self.dateSortVisible = value
        self.lblDateSort.setVisible(value)
        self.cmbDateSort.setVisible(value)


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setAnalysisMode(self, mode=True):
        for widget in (self.lblDuration, self.frmDuration,
                       self.lblSex,      self.frmSex,
                       self.lblAge,      self.frmAge,
                       self.lblSocStatusClass, self.cmbSocStatusClass,
                       self.lblSocStatusType,  self.cmbSocStatusType,
                       self.lblMKB,      self.frmMKB,
                      ):
            widget.setVisible(mode)
        self.analysisMode = True


    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        self.chkByPeriod.setChecked(params.get('byPeriod', False))
        self.cmbDoctype.setValue(params.get('doctype', None))
        self.cmbReason.setValue(params.get('tempInvalidReasonIdList', None))
        self.chkOnlyClosed.setChecked(params.get('onlyClosed', True))
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))
        self.cmbPerson.setValue(params.get('personId', None))
        self.edtDurationFrom.setValue(params.get('durationFrom', 0))
        self.edtDurationTo.setValue(params.get('durationTo', 0))
        self.cmbSex.setCurrentIndex(params.get('sex', 0))
        self.edtAgeFrom.setValue(params.get('ageFrom', 0))
        self.edtAgeTo.setValue(params.get('ageTo', 150))
        self.cmbSocStatusClass.setValue(params.get('socStatusClassId', None))
        self.cmbSocStatusType.setValue(params.get('socStatusTypeId', None))
        MKBFilter = params.get('MKBFilter', 0)
        self.cmbMKBFilter.setCurrentIndex(MKBFilter if MKBFilter else 0)
        self.edtMKBFrom.setText(params.get('MKBFrom', 'A00'))
        self.edtMKBTo.setText(params.get('MKBTo',   'Z99.9'))
        self.cmbInsuranceOfficeMark.setCurrentIndex(params.get('insuranceOfficeMark', 0))
        self.chkAverageDuration.setChecked(params.get('averageDuration', False))
        self.chkResultsForGroups.setChecked(params.get('resultsForGroups', False))
        self.chkRegAddress.setChecked(params.get('hasRegAddress', True))
        self.chkLocAddress.setChecked(params.get('hasLocAddress', True))
        self.chkBeginPerson.setChecked(params.get('hasBeginPerson', True))
        self.chkEndPerson.setChecked(params.get('hasEndPerson', True))
        self.chkPlaceWork.setChecked(params.get('placeWork', True))
        self.chkIsExternal.setChecked(params.get('isExternal', True))
        if self.isCntUserVisible:
            self.edtCntUser.setValue(params.get('cntUser', 1))
        if self.isTempInvalidReceiverVisible:
            self.chkTempInvalidReceiver.setChecked(params.get('isTempInvalidReceiver', False))
        if self.isTempInvalidCOVID19Visible:
            self.chkTempInvalidCOVID19.setChecked(params.get('isTempInvalidCOVID19', False))
        if self.isTempInvalidDuplicateVisible:
            self.chkTempInvalidDuplicate.setChecked(params.get('isTempInvalidDuplicate', False))
        if self.isTempInvalidDuplicateWorkVisible:
            self.chkTempInvalidDuplicateWork.setChecked(params.get('isTempInvalidDuplicateWork', False))
        if self.clientNameSortVisible:
            self.chkClientNameSort.setChecked(params.get('isClientNameSort', False))
        if self.dateSortVisible:
            self.cmbDateSort.setCurrentIndex(params.get('dateSort', 0))
        if self.isOrderByVisible:
            self.chkOrderBy.setChecked(params.get('isOrderBy', False))
            self.cmbOrderBy.setCurrentIndex(params.get('OrderByValue', 0))
        if self.isClientAreaVisible:
            self.chkClientArea.setChecked(params.get('isClientArea', False))
            self.cmbClientArea.setValue(params.get('ClientAreaValue', 0))


    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['byPeriod'] = self.chkByPeriod.isChecked()
        result['doctype'] = self.cmbDoctype.value()
        if self.cmbReason.value():
            result['tempInvalidReasonIdList'] = self.cmbReason.value().split(u', ')
            result['tempInvalidReasonListText'] = self.cmbReason._translateValue2ShownValue(self.cmbReason.value())
        else:
            result['tempInvalidReasonIdList'] = None
            result['tempInvalidReasonListText'] = None
        result['onlyClosed'] = self.chkOnlyClosed.isChecked()
        result['orgStructureId'] = self.cmbOrgStructure.value()
        result['personId'] = self.cmbPerson.value()
        if self.analysisMode:
            result['durationFrom'] = self.edtDurationFrom.value()
            result['durationTo'] = self.edtDurationTo.value()
            result['sex'] = self.cmbSex.currentIndex()
            result['ageFrom'] = self.edtAgeFrom.value()
            result['ageTo'] = self.edtAgeTo.value()
            result['socStatusClassId'] = self.cmbSocStatusClass.value()
            result['socStatusTypeId'] = self.cmbSocStatusType.value()
            result['MKBFilter'] = self.cmbMKBFilter.currentIndex()
            result['MKBFrom']   = unicode(self.edtMKBFrom.text())
            result['MKBTo']     = unicode(self.edtMKBTo.text())
        result['insuranceOfficeMark'] = self.cmbInsuranceOfficeMark.currentIndex()
        result['averageDuration'] = self.chkAverageDuration.isChecked()
        result['resultsForGroups'] = self.chkResultsForGroups.isChecked()
        result['hasRegAddress'] = self.chkRegAddress.isChecked()
        result['hasLocAddress'] = self.chkLocAddress.isChecked()
        result['hasBeginPerson'] = self.chkBeginPerson.isChecked()
        result['hasEndPerson'] = self.chkEndPerson.isChecked()
        result['placeWork'] = self.chkPlaceWork.isChecked()
        if self.isElectronicVisible:
            result['electronic'] = self.cmbElectronic.currentIndex()
        if self.isCntUserVisible:
            result['cntUser'] = self.edtCntUser.value()
        if self.isTempInvalidReceiverVisible:
            result['isTempInvalidReceiver'] = self.chkTempInvalidReceiver.isChecked()
        if self.isTempInvalidCOVID19Visible:
            result['isTempInvalidCOVID19'] = self.chkTempInvalidCOVID19.isChecked()
        if self.isTempInvalidDuplicateVisible:
            result['isTempInvalidDuplicate'] = self.chkTempInvalidDuplicate.isChecked()
        if self.isTempInvalidDuplicateWorkVisible:
            result['isTempInvalidDuplicateWork'] = self.chkTempInvalidDuplicateWork.isChecked()
        if self.clientNameSortVisible:
            result['isClientNameSort'] = self.chkClientNameSort.isChecked()
        if self.dateSortVisible:
            result['dateSort'] = self.cmbDateSort.currentIndex()
        if self.isClientAreaVisible:
            result['isClientArea'] = self.chkClientArea.isChecked()
            result['ClientAreaValue'] = self.cmbClientArea.value()
        if self.isOrderByVisible:
            result['isOrderBy'] = self.chkOrderBy.isChecked()
            result['OrderByValue'] = self.cmbOrderBy.currentIndex()
        if self.chkIsExternal:
            result['isExternal'] = self.chkIsExternal.isChecked()
        return result


    @pyqtSignature('QDate')
    def on_edtBegDate_dateChanged(self, date):
        self.cmbPerson.setBegDate(date)


    @pyqtSignature('QDate')
    def on_edtEndDate_dateChanged(self, date):
        self.cmbPerson.setEndDate(date)


    @pyqtSignature('int')
    def on_cmbOrgStructure_currentIndexChanged(self, index):
        orgStructureId = self.cmbOrgStructure.value()
        self.cmbPerson.setOrgStructureId(orgStructureId)


    @pyqtSignature('int')
    def on_cmbSocStatusClass_currentIndexChanged(self, index):
        socStatusClassId = self.cmbSocStatusClass.value()
        filter = ('class_id=%d' % socStatusClassId) if socStatusClassId else ''
        self.cmbSocStatusType.setFilter(filter)


    @pyqtSignature('int')
    def on_cmbMKBFilter_currentIndexChanged(self, index):
        self.edtMKBFrom.setEnabled(index == 1)
        self.edtMKBTo.setEnabled(index == 1)

