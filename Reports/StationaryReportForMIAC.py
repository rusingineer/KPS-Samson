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
from PyQt4.QtCore import Qt, pyqtSignature, QDate, QDateTime, QTime

from library.Utils      import forceDate, forceDateTime, forceInt, forceRef, forceString, getAgeRangeCond
from Events.Utils       import getActionTypeIdListByFlatCode

from Reports.HospitalBedProfileListDialog import CHospitalBedProfileListDialog
from Reports.ReportBase import CReportBase, createTable
from Reports.ReportView import CPageFormat
from Reports.SelectOrgStructureListDialog import CSelectOrgStructureListDialog
from Reports.StationaryF007   import CStationaryF007, getMovingTransfer, getLeaved, getReceived
from Reports.StationaryF007DS import getLeaved as getLeavedDS, getReceived as getReceivedDS, getMovingTransfer as getMovingTransferDS
from Reports.Utils      import ( dateRangeAsStr,
                                 getChildrenCount,
                                 getAdultCount,
                                 getNoDeathAdultCount,
                                 getPropertyAPHBPName,
                                 getKladrClientRural,
                                 getKladrClientDefaultCity,
                                 countMovingDays,
                                 # getMovingDays,
                                 getNoPropertyAPHBP,
                                 getOrgStructureProperty,
                                 getOrstructureHasHospitalBeds,
                                 getPropertyAPHBP,
                                 # getSeniorsMovingDays,
                                 getStringProperty,
                                 getTheseAndChildrens,
                                 getTransferOrganisaionName,
                               )


from Reports.Ui_StationaryReportForMIACSetupDialog import Ui_StationaryReportForMIACSetupDialog


def getMovingDays(orgStructureIdList, begDatePeriod, endDatePeriod, profile=None, isHospital=None, rural=None, additionalCond=None, bedsSchedule=None, typeOS=None, financeTypeId=None):
    db = QtGui.qApp.db
    tableAPT = db.table('ActionPropertyType')
    tableAP = db.table('ActionProperty')
    tableActionType = db.table('ActionType')
    tableAction = db.table('Action')
    tableEvent = db.table('Event')
    tableClient = db.table('Client')
    tableOrg = db.table('Organisation')
    tableOS = db.table('OrgStructure')
    tableAPHB = db.table('ActionProperty_HospitalBed')
    tableOSHB = db.table('OrgStructure_HospitalBed')
    tableHPS = db.table('rbHospitalBedShedule')
    queryTable = tableActionType.innerJoin(tableAction, tableActionType['id'].eq(tableAction['actionType_id']))
    queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
    queryTable = queryTable.leftJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
    queryTable = queryTable.innerJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
    queryTable = queryTable.innerJoin(tableAP, tableAP['type_id'].eq(tableAPT['id']))
    queryTable = queryTable.innerJoin(tableAPHB, tableAPHB['id'].eq(tableAP['id']))
    queryTable = queryTable.innerJoin(tableOSHB, tableOSHB['id'].eq(tableAPHB['value']))
    queryTable = queryTable.innerJoin(tableOS, tableOS['id'].eq(tableOSHB['master_id']))
    queryTable = queryTable.innerJoin(tableOrg, tableOrg['id'].eq(tableOS['organisation_id']))
    queryTable = queryTable.innerJoin(tableHPS, tableHPS['id'].eq(tableOSHB['schedule_id']))
    cond = [tableActionType['flatCode'].like('moving%'),
            tableAction['deleted'].eq(0),
            tableEvent['deleted'].eq(0),
            tableAP['deleted'].eq(0),
            tableActionType['deleted'].eq(0),
            tableAPT['deleted'].eq(0),
            tableOS['deleted'].eq(0),
            tableClient['deleted'].eq(0),
            tableOrg['deleted'].eq(0),
            tableAPT['typeName'].like('HospitalBed'),
            tableAP['action_id'].eq(tableAction['id'])
           ]
    if financeTypeId:
        cond.append(tableOSHB['finance_id'].eq(financeTypeId))
    if typeOS == 0:
        cond.append(tableOS['type'].eq(0))
    elif typeOS > 0:
        cond.append(tableOS['type'].ne(0))
    if isHospital is not None:
       cond.append(tableOrg['isHospital'].eq(isHospital))
    if rural:
        cond.append(getKladrClientRural())
    if bedsSchedule:
        if bedsSchedule == 1:
            cond.append(tableHPS['code'].eq(1))
        elif bedsSchedule == 2:
            cond.append(tableHPS['code'].ne(1))
    if additionalCond:
        cond.append(additionalCond)
    if profile:
        cond.append(tableOSHB['profile_id'].inlist(profile))
    cond.append(tableOSHB['master_id'].inlist(orgStructureIdList))
    cond.append(db.joinOr([tableAction['endDate'].isNull(), tableAction['endDate'].ge(begDatePeriod)]))
    cond.append(db.joinOr([tableAction['endDate'].isNull(), tableAction['endDate'].le(endDatePeriod)]))
    stmt = db.selectStmt(queryTable, [tableAction['begDate'], tableAction['endDate']], cond)
    query = db.query(u'SELECT SUM(DATEDIFF(T.endDate, T.begDate)) FROM (%s) AS T' % stmt)
    if query.next():
        return forceInt(query.value(0))
    return 0


def getSeniorsMovingDays(orgStructureIdList, begDatePeriod, endDatePeriod, profile=None, isHospital=None, rural=None, additionalCond=None, bedsSchedule=None, typeOS=None, financeTypeId=None, financeTypeIdList=[]):
    db = QtGui.qApp.db
    tableAPT = db.table('ActionPropertyType')
    tableAP = db.table('ActionProperty')
    tableActionType = db.table('ActionType')
    tableAction = db.table('Action')
    tableEvent = db.table('Event')
    tableClient = db.table('Client')
    tableOrg = db.table('Organisation')
    tableOS = db.table('OrgStructure')
    tableAPHB = db.table('ActionProperty_HospitalBed')
    tableOSHB = db.table('OrgStructure_HospitalBed')
    tableHPS = db.table('rbHospitalBedShedule')
    queryTable = tableActionType.innerJoin(tableAction, tableActionType['id'].eq(tableAction['actionType_id']))
    queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
    queryTable = queryTable.leftJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
    queryTable = queryTable.innerJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
    queryTable = queryTable.innerJoin(tableAP, tableAP['type_id'].eq(tableAPT['id']))
    queryTable = queryTable.innerJoin(tableAPHB, tableAPHB['id'].eq(tableAP['id']))
    queryTable = queryTable.innerJoin(tableOSHB, tableOSHB['id'].eq(tableAPHB['value']))
    queryTable = queryTable.innerJoin(tableOS, tableOS['id'].eq(tableOSHB['master_id']))
    queryTable = queryTable.innerJoin(tableOrg, tableOrg['id'].eq(tableOS['organisation_id']))
    queryTable = queryTable.innerJoin(tableHPS, tableHPS['id'].eq(tableOSHB['schedule_id']))
    cond = [tableActionType['flatCode'].like('moving%'),
            tableAction['deleted'].eq(0),
            tableEvent['deleted'].eq(0),
            tableAP['deleted'].eq(0),
            tableActionType['deleted'].eq(0),
            tableAPT['deleted'].eq(0),
            tableOS['deleted'].eq(0),
            tableClient['deleted'].eq(0),
            tableOrg['deleted'].eq(0),
            tableAPT['typeName'].like('HospitalBed'),
            tableAP['action_id'].eq(tableAction['id'])
           ]
    if financeTypeIdList:
        cond.append(tableOSHB['finance_id'].inlist(financeTypeIdList))
    if financeTypeId:
        cond.append(tableOSHB['finance_id'].eq(financeTypeId))
    cond.append(u'(age(Client.birthDate, Action.begDate)) >= IF(Client.sex = 2, 56, IF(Client.sex = 1, 61, 56))')
    if typeOS == 0:
        cond.append(tableOS['type'].eq(0))
    elif typeOS > 0:
        cond.append(tableOS['type'].ne(0))
    if isHospital is not None:
       cond.append(tableOrg['isHospital'].eq(isHospital))
    if rural:
        cond.append(getKladrClientRural())
    if bedsSchedule:
        if bedsSchedule == 1:
            cond.append(tableHPS['code'].eq(1))
        elif bedsSchedule == 2:
            cond.append(tableHPS['code'].ne(1))
    if additionalCond:
        cond.append(additionalCond)
    cond.append(tableOSHB['profile_id'].inlist(profile))
    cond.append(tableOSHB['master_id'].inlist(orgStructureIdList))
    cond.append(db.joinOr([tableAction['endDate'].isNull(), tableAction['endDate'].ge(begDatePeriod)]))
    cond.append(db.joinOr([tableAction['endDate'].isNull(), tableAction['endDate'].le(endDatePeriod)]))
    stmt = db.selectStmt(queryTable, [tableAction['begDate'], tableAction['endDate']], cond)
    query = db.query(u'SELECT SUM(DATEDIFF(T.endDate, T.begDate)) FROM (%s) AS T' % stmt)
    if query.next():
        return forceInt(query.value(0))
    return 0



def getOrgStructureTypeIdList(orgStructureIdList=[], type=0):
    db = QtGui.qApp.db
    tableOS = db.table('OrgStructure')
    cond = [tableOS['deleted'].eq(0)]
    if orgStructureIdList:
        cond.append(tableOS['id'].inlist(orgStructureIdList))
    if type == 1:
        isTypeOS = u'(OrgStructure.type = 0 AND (SELECT getOrgStructureIsType(OrgStructure.id)) = 1)'
    elif type == 2:
        isTypeOS = u'OrgStructure.type != 0'
    else:
        isTypeOS = u'(OrgStructure.type != 0 OR (OrgStructure.type = 0 AND (SELECT getOrgStructureIsType(OrgStructure.id)) = 1))'
    cond.append(isTypeOS)
    return db.getDistinctIdList(tableOS, tableOS['id'].name(), cond)


class CStationaryReportForMIACSetupDialog(QtGui.QDialog, Ui_StationaryReportForMIACSetupDialog):
    def __init__(self, parent=None, currentOrgStructureId=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.currentOrgStructureId = currentOrgStructureId
        self.edtTimeEdit.setTime(QTime(9, 0, 0, 0))
        self._begDateVisible = False
        self.setBegDateVisible(self._begDateVisible)
        self.chkFinance.setVisible(False)
        self.cmbFinance.setVisible(False)
        self.orgStructureList = []
        self.hospitalBedProfileList = []


    def setForMIACHardVisible(self, value=True):
        if not value:
            self.chkNoProfileBed.setChecked(value)
            #self.chkIsPermanentBed.setChecked(value)
            self.chkIsGroupingOS.setChecked(value)
        self.chkNoProfileBed.setVisible(value)
        #self.chkIsPermanentBed.setVisible(value)
        self.chkIsGroupingOS.setVisible(value)


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setBegDateVisible(self, value):
        self._begDateVisible = value
        self.lblBegDate.setVisible(value)
        self.edtBegDate.setVisible(value)
        self.edtBegTime.setVisible(value)
        if value:
            self.lblEndDate.setText(u'Дата окончания')
        else:
            self.lblEndDate.setText(u'Текущий день')


    def setParams(self, params):
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        self.edtTimeEdit.setTime(params.get('endTime', QTime(9, 0, 0, 0)))
        self.orgStructureList = params.get('orgStructureList', [])
        if self.orgStructureList:
            if len(self.orgStructureList) == 1 and not self.orgStructureList[0]:
                self.lblOrgStructureList.setText(u'подразделение: ЛПУ')
            else:
                db = QtGui.qApp.db
                table = db.table('OrgStructure')
                records = db.getRecordList(table, [table['name']], [table['deleted'].eq(0), table['id'].inlist(self.orgStructureList)])
                nameList = []
                for record in records:
                    nameList.append(forceString(record.value('name')))
                self.lblOrgStructureList.setText(u', '.join(name for name in nameList if name))
        else:
            self.lblOrgStructureList.setText(u'подразделение: ЛПУ')
        self.cmbSchedule.setCurrentIndex(params.get('bedsSchedule', 0))
        self.hospitalBedProfileList = params.get('hospitalBedProfileList', [])
        if self.hospitalBedProfileList:
            db = QtGui.qApp.db
            table = db.table('rbHospitalBedProfile')
            records = db.getRecordList(table, [table['name']], [table['id'].inlist(self.hospitalBedProfileList)])
            nameList = []
            for record in records:
                nameList.append(forceString(record.value('name')))
            self.lblHospitalBedProfileList.setText(u', '.join(name for name in nameList if name))
        else:
            self.lblHospitalBedProfileList.setText(u'не задано')
        self.chkNoProfileBed.setChecked(params.get('noProfileBed', True))
        self.chkIsPermanentBed.setChecked(params.get('isPermanentBed', False))
        self.chkIsGroupingOS.setChecked(params.get('isGroupingOS', False))
        self.chkNoPrintCaption.setChecked(params.get('noPrintCaption', True))
        self.chkNoPrintFilterParameters.setChecked(params.get('chkNoPrintFilterParameters', False))
        if self._begDateVisible:
            self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
            self.edtBegTime.setTime(params.get('begTime', QTime(9, 0, 0, 0)))
        self.cmbStationaryType.setCurrentIndex(params.get('stationaryType', 0))
        self.edtBedAgeFor.setValue(params.get('bedAgeFor', 0))
        self.edtBedAgeTo.setValue(params.get('bedAgeTo', self.edtBedAgeTo.maximum()))


    def params(self):
        def getPureHMTime(time):
            return QTime(time.hour(), time.minute())
        result = {}
        result['endDate'] = self.edtEndDate.date()
        result['endTime'] = getPureHMTime(self.edtTimeEdit.time())
        if len(self.orgStructureList) == 1 and not self.orgStructureList[0]:
           result['orgStructureList'] = []
        else:
            result['orgStructureList'] = self.orgStructureList
        result['bedsSchedule'] = self.cmbSchedule.currentIndex()
        result['hospitalBedProfileList'] = self.hospitalBedProfileList
        result['noProfileBed'] = self.chkNoProfileBed.isChecked()
        result['isPermanentBed'] = self.chkIsPermanentBed.isChecked()
        result['isGroupingOS'] = self.chkIsGroupingOS.isChecked()
        result['noPrintCaption'] = self.chkNoPrintCaption.isChecked()
        result['noPrintFilterParameters'] = self.chkNoPrintFilterParameters.isChecked()
        if self._begDateVisible:
            result['begDate'] = self.edtBegDate.date()
            result['begTime'] = getPureHMTime(self.edtBegTime.time())
        result['financeList'] = []
        result['financeName'] = []
        if self.chkFinance.isChecked():
            itemList = self.cmbFinance.model().takeColumn(0)
            for item in itemList:
                if item.checkState() == Qt.Checked:
                    result['financeList'].append(item.financeId)
                    result['financeName'].append(item.text())
        result['stationaryType'] = self.cmbStationaryType.currentIndex()
        result['bedAgeFor'] = self.edtBedAgeFor.value()
        result['bedAgeTo'] = self.edtBedAgeTo.value()
        return result


    @pyqtSignature('bool')
    def on_chkFinance_toggled(self, checked):
        self.cmbFinance.setEnabled(checked)


    @pyqtSignature('QDate')
    def on_edtEndDate_dateChanged(self, date):
        endDate = date
        if endDate:
            begTime = self.edtTimeEdit.time()
            stringInfo = u'c %s до %s'%(forceString(QDateTime(endDate.addDays(-1), begTime)), forceString(QDateTime(endDate, begTime)))
        else:
            stringInfo = u'Введите дату'
        self.lblEndDate.setToolTip(stringInfo)


    @pyqtSignature('')
    def on_btnHospitalBedProfileList_clicked(self):
        self.hospitalBedProfileList = []
        self.lblHospitalBedProfileList.setText(u'не задано')
        dialog = CHospitalBedProfileListDialog(self)
        if dialog.exec_():
            self.hospitalBedProfileList = dialog.values()
            if self.hospitalBedProfileList:
                db = QtGui.qApp.db
                table = db.table('rbHospitalBedProfile')
                records = db.getRecordList(table, [table['name']], [table['id'].inlist(self.hospitalBedProfileList)])
                nameList = []
                for record in records:
                    nameList.append(forceString(record.value('name')))
                self.lblHospitalBedProfileList.setText(u', '.join(name for name in nameList if name))


    @pyqtSignature('')
    def on_btnOrgStructureList_clicked(self):
        self.orgStructureList = []
        self.lblOrgStructureList.setText(u'подразделение: ЛПУ')
        dialog = CSelectOrgStructureListDialog(self)
        if dialog.exec_():
            self.orgStructureList = dialog.values()
            if self.orgStructureList:
                if len(self.orgStructureList) == 1 and not self.orgStructureList[0]:
                    self.lblOrgStructureList.setText(u'подразделение: ЛПУ')
                else:
                    db = QtGui.qApp.db
                    table = db.table('OrgStructure')
                    records = db.getRecordList(table, [table['name']], [table['id'].inlist(self.orgStructureList)])
                    nameList = []
                    for record in records:
                        nameList.append(forceString(record.value('name')))
                    self.lblOrgStructureList.setText(u', '.join(name for name in nameList if name))


class CStationaryReportForMIAC(CStationaryF007):
    def __init__(self, parent, currentOrgStructureId=None):
        CStationaryF007.__init__(self, parent)
        self.setTitle(u'Отчёт для МИАЦ')
        self.orientation = CPageFormat.Landscape
        self.currentOrgStructureId = currentOrgStructureId


    def getSetupDialog(self, parent):
        result = CStationaryReportForMIACSetupDialog(parent, self.currentOrgStructureId)
        result.setTitle(u'Отчёт для МИАЦ')
        result.setBegDateVisible(True)
        self.stationaryF007SetupDialog = result
        self.stationaryF007SetupDialog.chkFinance.setVisible(True)
        self.stationaryF007SetupDialog.cmbFinance.setVisible(True)
        return result


    def averageDaysHospitalBed(self, orgStructureIdList, begDatePeriod, endDatePeriod, bedsSchedule, profile = None, isHospital = None, financeTypeId = None, financeTypeIdList=[]):
        days = 0
        db = QtGui.qApp.db
        tableOSHB = db.table('OrgStructure_HospitalBed')
        tableOrg = db.table('Organisation')
        tableOS = db.table('OrgStructure')
        tableHBSchedule = db.table('rbHospitalBedShedule')
        queryTable = tableOSHB.innerJoin(tableOS, tableOS['id'].eq(tableOSHB['master_id']))
        queryTable = queryTable.innerJoin(tableOrg, tableOrg['id'].eq(tableOS['organisation_id']))
        bedType = db.translate('rbHospitalBedType', 'name', u'профильная', 'id')
        cond = [tableOSHB['master_id'].inlist(orgStructureIdList),
                tableOrg['deleted'].eq(0),
                tableOS['deleted'].eq(0),
                tableOSHB['type_id'].eq(bedType),
                tableOSHB['isPermanent'].eq('1')
                ]
        if financeTypeIdList:
            cond.append(tableOSHB['finance_id'].inlist(financeTypeIdList))
        if financeTypeId:
            cond.append(tableOSHB['finance_id'].eq(financeTypeId))
        if bedsSchedule:
            queryTable = queryTable.innerJoin(tableHBSchedule, tableOSHB['schedule_id'].eq(tableHBSchedule['id']))
        if bedsSchedule == 1:
            cond.append(tableHBSchedule['code'].eq(1))
        elif bedsSchedule == 2:
            cond.append(tableHBSchedule['code'].ne(1))
        if isHospital is not None:
           cond.append(tableOrg['isHospital'].eq(isHospital))
        joinAnd = db.joinAnd([tableOSHB['endDate'].isNull(), db.joinOr([db.joinAnd([tableOSHB['begDate'].isNotNull(), tableOSHB['begDate'].lt(endDatePeriod)]), tableOSHB['begDate'].isNull()])])
        cond.append(db.joinOr([db.joinAnd([tableOSHB['endDate'].isNotNull(), tableOSHB['endDate'].gt(begDatePeriod), tableOSHB['begDate'].isNotNull(), tableOSHB['begDate'].lt(endDatePeriod)]), joinAnd]))
        #if profile:
        cond.append(tableOSHB['profile_id'].inlist(profile))
        stmt = db.selectStmt(queryTable, [tableOSHB['id'], tableOSHB['begDate'], tableOSHB['endDate']], where=cond)
        query = db.query(stmt)
        bedIdList = []
        while query.next():
            record = query.record()
            bedId = forceRef(record.value('id'))
            if bedId not in bedIdList:
                bedIdList.append(bedId)
                begDate = forceDate(record.value('begDate'))
                endDate = forceDate(record.value('endDate'))
                if not begDate or begDate < begDatePeriod:
                    begDate = begDatePeriod
                if not endDate or endDate > endDatePeriod:
                    endDate = endDatePeriod
                if begDate and endDate:
                    if begDate == endDate:
                        days += 1
                    else:
                        days += begDate.daysTo(endDate)
        return days


    def dumpParams(self, cursor, params, onlyDates):
        description = []
        endDate = params.get('endDate', QDate())
        begDate = params.get('begDate', QDate())
        if not endDate:
            endDate = QDate.currentDate()
        if endDate:
            endTime = params.get('endTime', QTime(9, 0, 0, 0))
            begTime = params.get('begTime', None)
            endDateTime = QDateTime(endDate, endTime)
            if not begDate:
                begTime = begTime if begTime else endTime
                begDateTime = QDateTime(endDate.addDays(-1), begTime)
                description.append(u'Текущий день: ' + forceString(QDateTime(endDate, endTime)))
            else:
                begTime = begTime if begTime else endTime
                begDateTime = QDateTime(begDate, begTime)
                if begDateTime.date() or endDateTime.date():
                    description.append(dateRangeAsStr(u'за период', begDateTime, endDateTime))
        stationaryType = params.get('stationaryType', 0)
        if stationaryType:
            description.append(u'тип стационара: %s'%([u'Дневной', u'Круглосуточный'][stationaryType-1]))
        if onlyDates:
            bedsSchedule = params.get('bedsSchedule', 0)
            noProfileBed = params.get('noProfileBed', True)
            isPermanentBed = params.get('isPermanentBed', False)
            orgStructureList = params.get('orgStructureList', None)
            if orgStructureList:
                if len(orgStructureList) == 1 and not orgStructureList[0]:
                    description.append(u'подразделение: ЛПУ')
                else:
                    db = QtGui.qApp.db
                    table = db.table('OrgStructure')
                    records = db.getRecordList(table, [table['name']], [table['id'].inlist(orgStructureList)])
                    nameList = []
                    for record in records:
                        nameList.append(forceString(record.value('name')))
                    description.append(u'подразделение:  %s'%(u','.join(name for name in nameList if name)))
            else:
                description.append(u'подразделение: ЛПУ')
            hospitalBedProfileList = params.get('hospitalBedProfileList', None)
            if hospitalBedProfileList:
                db = QtGui.qApp.db
                table = db.table('rbHospitalBedProfile')
                records = db.getRecordList(table, [table['name']], [table['id'].inlist(hospitalBedProfileList)])
                nameList = []
                for record in records:
                    nameList.append(forceString(record.value('name')))
                description.append(u'профиль койки:  %s'%(u','.join(name for name in nameList if name)))
            else:
                description.append(u'профиль койки:  не задано')
            description.append(u'режим койки: %s'%([u'Не учитывать', u'Круглосуточные', u'Не круглосуточные'][bedsSchedule]))
            if noProfileBed:
                description.append(u'учитывать койки с профилем и без профиля')
            else:
                description.append(u'учитывать койки с профилем')
            if isPermanentBed:
                description.append(u'учитывать внештатные койки')
            else:
                description.append(u'учитывать штатные койки')
        financeName = params.get('financeName', [])
        financeNameString = ''
        if len(financeName):
            for item in financeName:
                financeNameString += forceString(item) + ', '
            description.append(u'тип финансирования: %s' %financeNameString)
        ageForBed = params.get('bedAgeFor', 0)
        ageToBed  = params.get('bedAgeTo', 150)
        if ageForBed or ageToBed:
            description.append(u'возраст' + u' с '+forceString(ageForBed) + u' по '+forceString(ageToBed))
        description.append(u'отчёт составлен: '+forceString(QDateTime.currentDateTime()))
        columns = [ ('100%', [], CReportBase.AlignLeft) ]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()


    def getCaption(self, cursor, params, title):
        orgId = QtGui.qApp.currentOrgId()
        orgName = u''
        OKPO = u''
        if orgId:
            record = QtGui.qApp.db.getRecordEx('Organisation', 'shortName, OKPO', 'id=%s AND deleted = 0'%(str(orgId)))
            if record:
                orgName = forceString(record.value('shortName'))
                OKPO = forceString(record.value('OKPO'))
        underCaptionList = []
        orgStructureList = params.get('orgStructureList', None)
        if orgStructureList:
            if len(orgStructureList) == 1 and not orgStructureList[0]:
                underCaptionList.append(u'подразделение: ЛПУ')
            else:
                db = QtGui.qApp.db
                table = db.table('OrgStructure')
                records = db.getRecordList(table, [table['name']], [table['id'].inlist(orgStructureList)])
                nameList = []
                for record in records:
                    nameList.append(forceString(record.value('name')))
                underCaptionList.append(u'подразделение:  %s'%(u','.join(name for name in nameList if name)))
        else:
            underCaptionList.append(u'подразделение: ЛПУ')
        hospitalBedProfileList = params.get('hospitalBedProfileList', None)
        if hospitalBedProfileList:
            db = QtGui.qApp.db
            table = db.table('rbHospitalBedProfile')
            records = db.getRecordList(table, [table['name']], [table['id'].inlist(hospitalBedProfileList)])
            nameList = []
            for record in records:
                nameList.append(forceString(record.value('name')))
            underCaptionList.append(u'профиль койки:  %s'%(u','.join(name for name in nameList if name)))
        else:
            underCaptionList.append(u'профиль койки:  не задано')
        columns = [('50%', [], CReportBase.AlignLeft), ('50%', [], CReportBase.AlignLeft)]
        table = createTable(cursor, columns, headerRowCount=7, border=0, cellPadding=2, cellSpacing=0)
        table.setText(0, 0, u'')
        table.setText(0, 1, u'Код формы по ОКУД ___________')
        table.setText(1, 0, u'')
        table.setText(1, 1, u'Код учреждения по ОКПО  %s'%(OKPO))
        table.setText(2, 0, u'')
        table.setText(2, 1, u'')
        table.setText(3, 0, u'')
        table.setText(3, 1, u'Медицинская документация')
        table.setText(4, 0, u'')
        table.setText(4, 1, u'Форма № 007/у')
        table.setText(5, 0, u'')
        table.setText(5, 1, u'Утверждена Минздравом СССР')
        table.setText(6, 0, orgName)
        table.setText(6, 1, u'04.10.80 г. № 1030')
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        boldChars = QtGui.QTextCharFormat()
        boldChars.setFontWeight(QtGui.QFont.Bold)
        columns2 = [('100%', [], CReportBase.AlignCenter)]
        table2 = createTable(cursor, columns2, headerRowCount=2, border=0, cellPadding=2, cellSpacing=0)
        table2.setText(0, 0, title, charFormat=boldChars)
        table2.setText(1, 0, u', '.join(underCaption for underCaption in underCaptionList if underCaption))
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()


    def build(self, params):
        db = QtGui.qApp.db
        tableOS = db.table('OrgStructure')
        tableOSHB = db.table('OrgStructure_HospitalBed')
        tableHBSchedule = db.table('rbHospitalBedShedule')
        tableRbHospitalBedProfile = db.table('rbHospitalBedProfile')
        endDate        = params.get('endDate', QDate())
        begDate        = params.get('begDate', QDate())
        stationaryType = params.get('stationaryType', 0)
        ageFor         = params.get('bedAgeFor', 0)
        ageTo          = params.get('bedAgeTo', 150)
        bedsSchedule   = params.get('bedsSchedule', 0)
        #hospitalBedProfileList = params.get('hospitalBedProfileList', None)
        noProfileBed   = params.get('noProfileBed', True)
        isPermanentBed = params.get('isPermanentBed', False)
        noPrintCaption = params.get('noPrintCaption', False)
        isGroupingOS   = params.get('isGroupingOS', False)
        noPrintParams  = params.get('noPrintFilterParameters', False)
        financeTypeIdList= params.get('financeList', [])
        endTime = params.get('endTime', QTime(9, 0, 0, 0))
        begTime = params.get('begTime', None)
        endDateTime = QDateTime(endDate, endTime)
        if not begDate:
            begTime = begTime if begTime else endTime
            begDateTime = QDateTime(endDate.addDays(-1), begTime)
        else:
            begTime = begTime if begTime else endTime
            begDateTime = QDateTime(begDate, begTime)
        if not endDate:
            endDate = QDate.currentDate()
        endTime = params.get('endTime', QTime(9, 0, 0, 0))
        begTime = params.get('begTime', None)
        endDateTime = QDateTime(endDate, endTime)
        if not begDate:
            begTime = begTime if begTime else endTime
            begDateTime = QDateTime(endDate.addDays(-1), begTime)
        else:
            begTime = begTime if begTime else endTime
            begDateTime = QDateTime(begDate, begTime)
        begOrgStructureIdList  = getOrstructureHasHospitalBeds(getTheseAndChildrens(params.get('orgStructureList', [])))
        if stationaryType:
            begOrgStructureIdList  = getOrgStructureTypeIdList(getOrstructureHasHospitalBeds(getTheseAndChildrens(params.get('orgStructureList', []))), stationaryType)
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertBlock()
        if not noPrintCaption:
            self.getCaption(cursor, params, u'Отчёт для МИАЦ')
        else:
            cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params, not noPrintParams)
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()
        cols = [('12%',[u'Профиль',                                    u'',                                            u'1'], CReportBase.AlignLeft),
                ('4%', [u'Число коек',                                 u'На конец периода',                            u'2'], CReportBase.AlignRight),
                ('4%', [u'',                                           u'среднемесячных',                              u'3'], CReportBase.AlignRight),
                ('4%', [u'Состояло на конец предыдущего периода',      u'',                                            u'4'], CReportBase.AlignRight),
                ('4%', [u'Поступило больных всего',                    u'',                                            u'5'], CReportBase.AlignRight),
                ('4%', [u'в том числе',                                u'из дневного стационара',                      u'6'], CReportBase.AlignRight),
                ('4%', [u'',                                           u'Сельских жителей',                            u'7'], CReportBase.AlignRight),
                ('4%', [u'',                                           u'детей до 17 лет',                             u'8'], CReportBase.AlignRight),
                ('4%', [u'',                                           u'старше трудоспособного возраста',             u'9'], CReportBase.AlignRight),
                ('4%', [u'переведено',                                 u'из др. отделений',                            u'10'], CReportBase.AlignRight),
                ('4%', [u'',                                           u'в др. отделения',                             u'11'], CReportBase.AlignRight),
                ('4%', [u'Выписано больных',                           u'Всего',                                       u'12'], CReportBase.AlignRight),
                ('4%', [u'',                                           u'в том числе старше трудоспособного возраста', u'13'], CReportBase.AlignRight),
                ('4%', [u'',                                           u'из них в дневные стационары(всех типов)',     u'14'], CReportBase.AlignRight),
                ('4%', [u'Умерло',                                     u'',                                            u'15'], CReportBase.AlignRight),
                ('4%', [u'в том числе',                                u'детей до 17 лет',                             u'16'], CReportBase.AlignRight),
                ('4%', [u'',                                           u'старше трудоспособного возраста',             u'17'], CReportBase.AlignRight),
                ('4%', [u'Состоит на конец периода',                   u'',                                            u'18'], CReportBase.AlignRight),
                ('4%', [u'Проведено койко-дней',                       u'',                                            u'19'], CReportBase.AlignRight),
                ('4%', [u'в том числе старше трудоспособного возраста',u'',                                            u'20'], CReportBase.AlignRight),
                ('4%', [u'число койко-дней закрытия',                  u'',                                            u'21'], CReportBase.AlignRight),
                ('4%', [u'поступило иногородних больных',              u'',                                            u'22'], CReportBase.AlignRight),
                ('4%', [u'поступило экстренных больных',               u'',                                            u'23'], CReportBase.AlignRight)
               ]
        table = createTable(cursor, cols)
        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 1, 2)
        table.mergeCells(0, 3, 2, 1)
        table.mergeCells(0, 4, 2, 1)
        table.mergeCells(0, 5, 1, 4)
        table.mergeCells(0, 9, 1, 2)
        table.mergeCells(0, 11, 1, 3)
        table.mergeCells(0, 14, 2, 1)
        table.mergeCells(0, 15, 1, 2)
        table.mergeCells(0, 17, 2, 1)
        table.mergeCells(0, 18, 2, 1)
        table.mergeCells(0, 19, 2, 1)
        table.mergeCells(0, 20, 2, 1)
        table.mergeCells(0, 21, 2, 1)
        table.mergeCells(0, 22, 2, 1)
        if endDate and (not stationaryType or (stationaryType and begOrgStructureIdList)):
            self.countBedsRepairsAll = 0
            self.movingPresentAll = 0
            self.movingTransferAll = 0
            self.receivedBedsAllSUM = 0
            self.receivedInfo0 = 0
            self.receivedInfo6 = 0
            self.receivedInfo4 = 0
            self.receivedInfo3 = 0
            self.receivedInfo1 = 0
            self.receivedInfo2 = 0
            self.countBedsAll = 0
            self.inMovingTransferAll = 0
            self.leavedTransferSUM = 0
            self.countLeavedSUM = 0
            self.leavedAdultCountSUM = 0
            self.leavedAdultCountDeathSUM = 0
            self.leavedChildrenCountSUM = 0
            self.leavedDeathSUM = 0
            self.presentAdultCountEndSUM = 0
            self.seniorsMovingDaysSUM = 0
            self.countStationaryDaySUM = 0
            self.presentAllSUM = 0
            self.clientRuralSUM = 0
            self.presentPatronagSUM = 0
            self.bedsAllSUM = 0
            self.bedsMenSUM = 0
            self.bedsWomenSUM = 0
            self.monthBed = 0
            self.involuteBedsSUM = 0
            self.clientForeignSUM = 0

            def averageYarHospitalBed(orgStructureIdList, table, begDate, endDate, groupOS, profile = None, row = None, sumRowProfile = None, isHospital = None, financeTypeId = None, financeTypeIdList=[]):
                days = 0
                daysMonths = 0
                period = begDate.daysTo(endDate)
                days = self.averageDaysHospitalBed(orgStructureIdList, begDate, endDate, bedsSchedule, profile, isHospital, financeTypeId, financeTypeIdList)
                daysMonths += days / (period if period > 0 else 1)
                table.setText(row if row else sumRowProfile, 2, daysMonths)
                if groupOS:
                    self.monthBed += daysMonths

            def getHospitalBedProfile(orgStructureIdList, hbProfileIdList = [], financeTypeId = None):
                cond = []
                profileIdList = []
                self.hospitalBedIdList = []
                if orgStructureIdList:
                    cond.append(tableOSHB['master_id'].inlist(orgStructureIdList))
                if financeTypeId:
                    cond.append(tableOSHB['finance_id'].eq(financeTypeId))
                if hbProfileIdList:
                    cond.append(tableRbHospitalBedProfile['id'].inlist(hbProfileIdList))
                if QtGui.qApp.defaultHospitalBedProfileByMoving():
                    tableVHospitalBed = db.table('vHospitalBed')
                    condHB = []
                    tableVHospitalBedSchedule = tableVHospitalBed.innerJoin(tableOS,  tableVHospitalBed['master_id'].eq(tableOS['id']))
                    condHB.append(tableOS['deleted'].eq(0))
                    if orgStructureIdList:
                        condHB.append(tableVHospitalBed['master_id'].inlist(orgStructureIdList))
                    if bedsSchedule:
                        tableVHospitalBedSchedule = tableVHospitalBedSchedule.innerJoin(tableHBSchedule, tableVHospitalBed['schedule_id'].eq(tableHBSchedule['id']))
                    if bedsSchedule == 1:
                        condHB.append(tableHBSchedule['code'].eq(1))
                    elif bedsSchedule == 2:
                        condHB.append(tableHBSchedule['code'].ne(1))
                    if not isPermanentBed:
                        condHB.append(tableVHospitalBed['isPermanent'].eq(1))
                    if financeTypeIdList:
                        condHB.append(tableVHospitalBed['finance_id'].inlist(financeTypeIdList))
                    joinOr1 = db.joinAnd([tableVHospitalBed['begDate'].isNotNull(), tableVHospitalBed['endDate'].isNotNull(),
                    tableVHospitalBed['begDate'].lt(endDateTime), tableVHospitalBed['endDate'].gt(begDateTime)])
                    joinOr2 = db.joinOr([tableVHospitalBed['begDate'].isNull(), tableVHospitalBed['begDate'].lt(endDateTime)])
                    joinOr3 = db.joinOr([tableVHospitalBed['endDate'].isNull(), tableVHospitalBed['endDate'].le(begDateTime)])
                    condHB.append(db.joinOr([joinOr1, joinOr2, joinOr3]))
                    self.hospitalBedIdList = db.getDistinctIdList(tableVHospitalBedSchedule, [tableVHospitalBed['id']], condHB)
                    tableRbAPHBP = db.table('ActionProperty_rbHospitalBedProfile')
                    tableAP = db.table('ActionProperty')
                    tableAction = db.table('Action')
                    tableAPT = db.table('ActionPropertyType')
                    queryTable = tableRbAPHBP.innerJoin(tableAP, tableRbAPHBP['id'].eq(tableAP['id']))
                    queryTable = queryTable.innerJoin(tableRbHospitalBedProfile, tableRbHospitalBedProfile['id'].eq(tableRbAPHBP['value']))
                    queryTable = queryTable.innerJoin(tableAction, tableAction['id'].eq(tableAP['action_id']))
                    queryTable = queryTable.innerJoin(tableAPT, tableAPT['id'].eq(tableAP['type_id']))
                    cond = [tableAP['action_id'].isNotNull(),
                            tableAP['deleted'].eq(0),
                            tableAction['deleted'].eq(0),
                            tableAPT['deleted'].eq(0),
                            tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode('moving%')),
                            tableAPT['typeName'].like('rbHospitalBedProfile')
                            ]
                    if hbProfileIdList:
                        cond.append(tableRbHospitalBedProfile['id'].inlist(hbProfileIdList))
                    joinOr1 = db.joinAnd([tableAction['begDate'].isNull(), tableAction['endDate'].isNull()])
                    joinOr2 = db.joinAnd([tableAction['begDate'].isNotNull(), tableAction['begDate'].ge(begDateTime), tableAction['begDate'].lt(endDateTime)])
                    joinOr3 = db.joinAnd([tableAction['begDate'].isNull(), tableAction['endDate'].isNotNull(), tableAction['endDate'].gt(begDateTime)])
                    cond.append(db.joinOr([joinOr1, joinOr2, joinOr3]))
                    if financeTypeIdList:
                        cond.append(tableOSHB['finance_id'].inlist(financeTypeIdList))
                    cond.append(u'''EXISTS(SELECT APHB.value
    FROM ActionProperty AS AP
    INNER JOIN ActionProperty_HospitalBed AS APHB ON APHB.`id`=AP.`id`
    INNER JOIN Action AS A ON A.`id`=AP.`action_id`
    INNER JOIN ActionPropertyType AS APT ON APT.`id`=AP.`type_id`
    WHERE (AP.`action_id` IS NOT NULL AND AP.`action_id` = Action.id) AND (AP.`deleted`=0) AND (APT.`deleted`=0)
    AND (APT.`typeName` = 'HospitalBed') AND (APHB.`value` IN (%s)))'''%(u','.join(str(hospitalBedId) for hospitalBedId in self.hospitalBedIdList if hospitalBedId)))
                    records = db.getRecordList(queryTable, [tableRbHospitalBedProfile['id'], tableRbHospitalBedProfile['code'], tableRbHospitalBedProfile['name']], cond)
                    for record in records:
                        profileId = forceRef(record.value('id'))
                        if profileId not in profileIdList:
                            profileIdList.append(profileId)
                else:
                    if not noProfileBed:
                        cond.append('OrgStructure_HospitalBed.profile_id IS NOT NULL')
                    if financeTypeId:
                        cond.append(tableOSHB['finance_id'].eq(financeTypeId))
                    #if not isPermanentBed:
                    #    cond.append('OrgStructure_HospitalBed.isPermanent = 1')
                    queryTable = tableOSHB.innerJoin(tableRbHospitalBedProfile, tableOSHB['profile_id'].eq(tableRbHospitalBedProfile['id']))
                    queryTable = queryTable.innerJoin(tableOS,  tableOSHB['master_id'].eq(tableOS['id']))
                    cond.append(tableOS['deleted'].eq(0))
                    if financeTypeIdList:
                        cond.append(tableOSHB['finance_id'].inlist(financeTypeIdList))
                    if bedsSchedule:
                        queryTable = queryTable.innerJoin(tableHBSchedule, tableOSHB['schedule_id'].eq(tableHBSchedule['id']))
                        if bedsSchedule == 1:
                            cond.append(tableHBSchedule['code'].eq(1))
                        elif bedsSchedule == 2:
                            cond.append(tableHBSchedule['code'].ne(1))
                    cond.append(db.joinOr([tableOSHB['begDate'].isNull(), tableOSHB['begDate'].lt(endDateTime)]))
                    cond.append(db.joinOr([tableOSHB['endDate'].isNull(), tableOSHB['endDate'].ge(begDateTime)]))
                    profileIdList = db.getDistinctIdList(queryTable, [tableRbHospitalBedProfile['id']], cond)
                if not profileIdList:
                    return None
                if noProfileBed:
                    profileIdList.append(None)
                return profileIdList
            hospitalBedProfileList = getHospitalBedProfile(begOrgStructureIdList, hbProfileIdList = params.get('hospitalBedProfileList', None))

            def getDataReport(parOrgStructureIdList, rowProfile, table, sumRowProfile, groupOS, profileIdList, osType = None, financeTypeId = None, financeTypeIdList=[]):
                db = QtGui.qApp.db
                tableAPT = db.table('ActionPropertyType')
                tableAP = db.table('ActionProperty')
                tableActionType = db.table('ActionType')
                tableAction = db.table('Action')
                tableEvent = db.table('Event')
                tableClient = db.table('Client')
                tableOS = db.table('OrgStructure')
                tableAPHB = db.table('ActionProperty_HospitalBed')
                tableOSHB = db.table('OrgStructure_HospitalBed')
                tableVHospitalBed = db.table('vHospitalBed')
                tableHBSchedule = db.table('rbHospitalBedShedule')

                orgStructureIdList = parOrgStructureIdList
                self.receivedBedsAll = 0
                self.countBeds = 0
                self.presentAll = 0

                def getHospitalBedId():
                    cond = []
                    tableVHospitalBedSchedule = tableVHospitalBed.innerJoin(tableOS,  tableVHospitalBed['master_id'].eq(tableOS['id']))
                    cond.append(tableOS['deleted'].eq(0))
                    if orgStructureIdList:
                        cond.append(tableVHospitalBed['master_id'].inlist(orgStructureIdList))
                    if bedsSchedule:
                        tableVHospitalBedSchedule = tableVHospitalBedSchedule.innerJoin(tableHBSchedule, tableVHospitalBed['schedule_id'].eq(tableHBSchedule['id']))
                    if bedsSchedule == 1:
                        cond.append(tableHBSchedule['code'].eq(1))
                    elif bedsSchedule == 2:
                        cond.append(tableHBSchedule['code'].ne(1))
                    if not isPermanentBed:
                        cond.append(tableVHospitalBed['isPermanent'].eq(1))
                    if financeTypeIdList:
                        cond.append(tableVHospitalBed['finance_id'].inlist(financeTypeIdList))
                    joinOr1 = db.joinAnd([tableVHospitalBed['begDate'].isNotNull(), tableVHospitalBed['endDate'].isNotNull(),
                    tableVHospitalBed['begDate'].lt(endDateTime), tableVHospitalBed['endDate'].gt(begDateTime)])
                    joinOr2 = db.joinOr([tableVHospitalBed['begDate'].isNull(), tableVHospitalBed['begDate'].lt(endDateTime)])
                    joinOr3 = db.joinOr([tableVHospitalBed['endDate'].isNull(), tableVHospitalBed['endDate'].le(begDateTime)])
                    cond.append(db.joinOr([joinOr1, joinOr2, joinOr3]))
                    return db.getDistinctIdList(tableVHospitalBedSchedule, [tableVHospitalBed['id']], cond)

                def getBedForProfile(noProfileBed, profile = None, hospitalBedIdList = None, countSetText = True, row = None, column = None, groupOS = False):
                    tableRbAPHBP = db.table('ActionProperty_rbHospitalBedProfile')
                    tableAP = db.table('ActionProperty')
                    tableAction = db.table('Action')
                    tableAPT = db.table('ActionPropertyType')
                    tableRbHospitalBedProfile = db.table('rbHospitalBedProfile')
                    queryTable = tableRbAPHBP.innerJoin(tableAP, tableRbAPHBP['id'].eq(tableAP['id']))
                    queryTable = queryTable.innerJoin(tableRbHospitalBedProfile, tableRbHospitalBedProfile['id'].eq(tableRbAPHBP['value']))
                    queryTable = queryTable.innerJoin(tableAction, tableAction['id'].eq(tableAP['action_id']))
                    queryTable = queryTable.innerJoin(tableAPT, tableAPT['id'].eq(tableAP['type_id']))
                    cond = [tableAP['action_id'].isNotNull(),
                            tableAP['deleted'].eq(0),
                            tableAction['deleted'].eq(0),
                            tableAPT['deleted'].eq(0),
                            tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode('moving%')),
                            tableAPT['typeName'].like('rbHospitalBedProfile')
                            ]
                    if profile:
                        if noProfileBed and len(profile) > 1:
                            cond.append(db.joinOr([tableRbHospitalBedProfile['profile_id'].inlist(profile), tableRbHospitalBedProfile['profile_id'].isNull()]))
                        else:
                            cond.append(tableRbHospitalBedProfile['id'].inlist(profile))
                    else:
                        cond.append(tableRbHospitalBedProfile['id'].isNull())
                    joinOr1 = db.joinAnd([tableAction['begDate'].isNull(), tableAction['endDate'].isNull()])
                    joinOr2 = db.joinAnd([tableAction['begDate'].isNotNull(), tableAction['begDate'].ge(begDateTime), tableAction['begDate'].lt(endDateTime)])
                    joinOr3 = db.joinAnd([tableAction['begDate'].isNull(), tableAction['endDate'].isNotNull(), tableAction['endDate'].gt(begDateTime)])
                    cond.append(db.joinOr([joinOr1, joinOr2, joinOr3]))
                    cond.append(u'''EXISTS(SELECT APHB.value
    FROM ActionProperty AS AP
    INNER JOIN ActionProperty_HospitalBed AS APHB ON APHB.`id`=AP.`id`
    INNER JOIN Action AS A ON A.`id`=AP.`action_id`
    INNER JOIN ActionPropertyType AS APT ON APT.`id`=AP.`type_id`
    WHERE (AP.`action_id` IS NOT NULL AND AP.`action_id` = Action.id) AND (AP.`deleted`=0) AND (APT.`deleted`=0)
    AND (APT.`typeName` = 'HospitalBed') AND (APHB.`value` IN (%s)))'''%(u','.join(str(hospitalBedId) for hospitalBedId in hospitalBedIdList if hospitalBedId)))
                    if countSetText:
                        self.countBeds = db.getCount(queryTable, countCol='rbHospitalBedProfile.id', where=cond)
                        if row:
                           table.setText(row, column, self.countBeds)
                        else:
                            table.setText(sumRowProfile, column, self.countBeds)
                            if groupOS:
                                self.countBedsAll += self.countBeds
                                table.setText(rowProfile, column, self.countBedsAll)
                        return None
                    else:
                        return db.getDistinctIdList(queryTable, [tableRbHospitalBedProfile['id']], cond)

                def unrolledHospitalBed34(profile = None, row = None, groupOS = False, financeTypeId = None, financeTypeIdList=[]):
                    condRepairs = ['''OrgStructure_HospitalBed_Involution.involutionType != 0
                                           AND (OrgStructure_HospitalBed_Involution.begDate IS NULL
                                           OR OrgStructure_HospitalBed_Involution. endDate IS NULL
                                           OR (OrgStructure_HospitalBed_Involution.begDate >= '%s'
                                           AND OrgStructure_HospitalBed_Involution. endDate <= '%s'))'''%(begDateTime.toString(Qt.ISODate), begDateTime.toString(Qt.ISODate))]
                    tableInvolution = db.table('OrgStructure_HospitalBed_Involution')
                    tableVHospitalBedSchedule = tableVHospitalBed.innerJoin(tableOS,  tableVHospitalBed['master_id'].eq(tableOS['id']))
                    if not noProfileBed:
                        condRepairs.append('vHospitalBed.profile_id IS NOT NULL')
                    if not isPermanentBed:
                        condRepairs.append(tableVHospitalBed['isPermanent'].eq(1))
                    if QtGui.qApp.defaultHospitalBedProfileByMoving():
                        condRepairs.append(tableOS['deleted'].eq(0))
                        if bedsSchedule:
                            tableVHospitalBedSchedule = tableVHospitalBedSchedule.innerJoin(tableHBSchedule, tableVHospitalBed['schedule_id'].eq(tableHBSchedule['id']))
                        if bedsSchedule == 1:
                            condRepairs.append(tableHBSchedule['code'].eq(1))
                        elif bedsSchedule == 2:
                            condRepairs.append(tableHBSchedule['code'].ne(1))
                        if financeTypeIdList:
                            condRepairs.append(tableVHospitalBed['finance_id'].inlist(financeTypeIdList))
                        if financeTypeId:
                            condRepairs.append(tableVHospitalBed['finance_id'].eq(financeTypeId))
                        if orgStructureIdList:
                            condRepairs.append(tableVHospitalBed['master_id'].inlist(orgStructureIdList))
                        #bedRepairIdList = db.getDistinctIdList(tableVHospitalBedSchedule.innerJoin(tableInvolution, tableInvolution['master_id'].eq(tableVHospitalBed['id'])), [tableVHospitalBed['id']], condRepairs)
                        if self.hospitalBedIdList:
                            getBedForProfile(noProfileBed, profile, self.hospitalBedIdList, True, row, 1, groupOS)
                        else:
                            table.setText(row if row else sumRowProfile, 1, 0)
                            if groupOS:
                                table.setText(rowProfile, 1, 0)
                    else:
                        cond = []
                        cond.append(tableOS['deleted'].eq(0))
                        if orgStructureIdList:
                            cond.append(tableVHospitalBed['master_id'].inlist(orgStructureIdList))
                            condRepairs.append(tableVHospitalBed['master_id'].inlist(orgStructureIdList))
                        if not isPermanentBed:
                            cond.append(tableVHospitalBed['isPermanent'].eq(1))
                        if profile:
                            if noProfileBed and len(profile) > 1:
                                cond.append(db.joinOr([tableVHospitalBed['profile_id'].inlist(profile), tableVHospitalBed['profile_id'].isNull()]))
                                condRepairs.append(db.joinOr([tableVHospitalBed['profile_id'].inlist(profile), tableVHospitalBed['profile_id'].isNull()]))
                            else:
                                cond.append(tableVHospitalBed['profile_id'].inlist(profile))
                                condRepairs.append(tableVHospitalBed['profile_id'].inlist(profile))
                        else:
                            cond.append(tableVHospitalBed['profile_id'].isNull())
                            condRepairs.append(tableVHospitalBed['profile_id'].isNull())
                        if bedsSchedule:
                            tableVHospitalBedSchedule = tableVHospitalBedSchedule.innerJoin(tableHBSchedule, tableVHospitalBed['schedule_id'].eq(tableHBSchedule['id']))
                        if bedsSchedule == 1:
                            cond.append(tableHBSchedule['code'].eq(1))
                            condRepairs.append(tableHBSchedule['code'].eq(1))
                        elif bedsSchedule == 2:
                            cond.append(tableHBSchedule['code'].ne(1))
                            condRepairs.append(tableVHospitalBed['code'].ne(1))
                        if financeTypeIdList:
                            cond.append(tableVHospitalBed['finance_id'].inlist(financeTypeIdList))
                            condRepairs.append(tableVHospitalBed['finance_id'].inlist(financeTypeIdList))
                        if financeTypeId:
                            cond.append(tableVHospitalBed['finance_id'].eq(financeTypeId))
                            condRepairs.append(tableVHospitalBed['finance_id'].eq(financeTypeId))
                        cond.append(db.joinOr([tableVHospitalBed['begDate'].isNull(), tableVHospitalBed['begDate'].lt(endDateTime)]))
                        cond.append(db.joinOr([tableVHospitalBed['endDate'].isNull(), tableVHospitalBed['endDate'].ge(begDateTime)]))
                        self.countBeds = db.getCount(tableVHospitalBedSchedule, countCol='vHospitalBed.id', where=cond)
                        countBedsRepairs = db.getCount(tableVHospitalBedSchedule.innerJoin(tableInvolution, tableInvolution['master_id'].eq(tableVHospitalBed['id'])), countCol='vHospitalBed.id', where=condRepairs)
                        if row:
                           table.setText(row, 1, self.countBeds)
                        else:
                            table.setText(sumRowProfile, 1, self.countBeds)
                            if groupOS:
                                self.countBedsAll += self.countBeds
                                self.countBedsRepairsAll += countBedsRepairs

                def getReceivedForeign(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty = u'Переведен из отделения', profile = None, orgStructureIdList = [], noPropertyProfile = False, profileCode = False, ageFor = False, ageTo = False):
                    db = QtGui.qApp.db
                    tableActionType = db.table('ActionType')
                    tableAction = db.table('Action')
                    tableEvent = db.table('Event')
                    tableEventType = db.table('EventType')
                    tableClient = db.table('Client')
                    cond = [ tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode('received%')),
                             tableAction['deleted'].eq(0),
                             tableEvent['deleted'].eq(0),
                             tableActionType['deleted'].eq(0),
                             tableClient['deleted'].eq(0),
                             tableAction['endDate'].isNotNull()
                            ]
                    queryTable = tableActionType.innerJoin(tableAction, tableActionType['id'].eq(tableAction['actionType_id']))
                    queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
                    queryTable = queryTable.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
                    queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
                    cond.append('''%s'''%(getOrgStructureProperty(u'Направлен в отделение', orgStructureIdList)))
                    cond.append(u'''(EventType.medicalAidType_id IN (SELECT rbMedicalAidType.id from rbMedicalAidType where rbMedicalAidType.code IN (\'1\', \'2\', \'3\')))''')
                    if noPropertyProfile:
                        cond.append('''%s'''%(getNoPropertyAPHBP()))
                    else:
                        cond.append('''%s'''%(getPropertyAPHBP(profile, noProfileBed)))
                    if ageFor and ageTo and ageFor <= ageTo:
                        cond.append(getAgeRangeCond(ageFor, ageTo))
                    cond.append(tableAction['endDate'].isNotNull())
                    cond.append(tableAction['endDate'].ge(begDateTime))
                    cond.append(tableAction['endDate'].le(endDateTime))
                    cond.append(u'''NOT %s'''%(getKladrClientDefaultCity(QtGui.qApp.defaultKLADR())))
                    cols = u'''COUNT(Client.id) AS receivedForeignAll'''
                    stmt = db.selectStmt(queryTable, cols, where=cond)
                    query = db.query(stmt)
                    if query.first():
                        record = query.record()
                        return forceInt(record.value('receivedForeignAll'))
                    else:
                        return 0

                def getReceivedForeignDS(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty = u'Переведен из отделения', profile = None, orgStructureIdList = [], noPropertyProfile = False, profileCode = False, ageFor = False, ageTo = False):
                    db = QtGui.qApp.db
                    tableActionType = db.table('ActionType')
                    tableAction = db.table('Action')
                    tableEvent = db.table('Event')
                    tableEventType = db.table('EventType')
                    tableClient = db.table('Client')
                    cond = [ tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode('received%')),
                             tableAction['deleted'].eq(0),
                             tableEvent['deleted'].eq(0),
                             tableActionType['deleted'].eq(0),
                             tableClient['deleted'].eq(0),
                             tableAction['endDate'].isNotNull()
                            ]
                    queryTable = tableActionType.innerJoin(tableAction, tableActionType['id'].eq(tableAction['actionType_id']))
                    queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
                    queryTable = queryTable.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
                    queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
                    cond.append('''%s'''%(getOrgStructureProperty(u'Направлен в отделение', orgStructureIdList, u' = 0')))
                    cond.append(u'''(EventType.medicalAidType_id IN (SELECT rbMedicalAidType.id from rbMedicalAidType where rbMedicalAidType.code IN (\'7\')))''')
                    if noPropertyProfile:
                        cond.append('''%s'''%(getNoPropertyAPHBP()))
                    else:
                        cond.append('''%s'''%(getPropertyAPHBP(profile, noProfileBed)))
                    if ageFor and ageTo and ageFor <= ageTo:
                        cond.append(getAgeRangeCond(ageFor, ageTo))
                    cond.append(tableAction['endDate'].isNotNull())
                    cond.append(tableAction['endDate'].ge(begDateTime))
                    cond.append(tableAction['endDate'].le(endDateTime))
                    cond.append(u'''NOT %s'''%(getKladrClientDefaultCity(QtGui.qApp.defaultKLADR())))
                    cols = u'''COUNT(Client.id) AS receivedForeignAll'''
                    stmt = db.selectStmt(queryTable, cols, where=cond)
                    query = db.query(stmt)
                    if query.first():
                        record = query.record()
                        return forceInt(record.value('receivedForeignAll'))
                    else:
                        return 0

                def getLeavedDeath(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty = u'Переведен в отделение', profile = None, orgStructureIdList = [], noPropertyProfile = False, profileCode = False, additionalCond = None, ageFor = False, ageTo = False):
                    db = QtGui.qApp.db
                    tableActionType = db.table('ActionType')
                    tableAction = db.table('Action')
                    tableEvent = db.table('Event')
                    tableEventType = db.table('EventType')
                    tableClient = db.table('Client')
                    cond = [ tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode('leaved%')),
                             tableAction['deleted'].eq(0),
                             tableEvent['deleted'].eq(0),
                             tableActionType['deleted'].eq(0),
                             tableClient['deleted'].eq(0),
                             tableAction['begDate'].isNotNull(),
                             tableAction['endDate'].isNotNull()
                           ]
                    if additionalCond:
                        cond.append(additionalCond)
                    queryTable = tableActionType.innerJoin(tableAction, tableActionType['id'].eq(tableAction['actionType_id']))
                    queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
                    queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
                    queryTable = queryTable.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
                    cond.append('''%s'''%(getOrgStructureProperty(u'Отделение', orgStructureIdList)))
                    cond.append(u'''(EventType.medicalAidType_id IN (SELECT rbMedicalAidType.id from rbMedicalAidType where rbMedicalAidType.code IN (\'1\', \'2\', \'3\')))''')
                    if noPropertyProfile:
                        cond.append('''%s'''%(getNoPropertyAPHBP()))
                    else:
                        cond.append('''%s'''%(getPropertyAPHBP(profile, noProfileBed)))
                    cond.append(tableAction['begDate'].ge(begDateTime))
                    cond.append(tableAction['begDate'].le(endDateTime))
                    if ageFor and ageTo and ageFor <= ageTo:
                        cond.append(getAgeRangeCond(ageFor, ageTo))
                    cond.append(getStringProperty(u'Исход госпитализации', u'(APS.value LIKE \'умер%\' OR APS.value LIKE \'смерть%\')'))
                    stmt = db.selectStmt(queryTable, u'COUNT(Client.id) AS countDeath, SUM(%s) AS adultCount, SUM(%s) AS childrenCount'%(getAdultCount(56,61), getChildrenCount()), where=cond)
                    query = db.query(stmt)
                    if query.first():
                        record = query.record()
                        return [forceInt(record.value('countDeath')), forceInt(record.value('adultCount')), forceInt(record.value('childrenCount'))]
                    else:
                        return [0, 0, 0]

                def getLeavedDeathDS(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty = u'Переведен в отделение', profile = None, orgStructureIdList = [], noPropertyProfile = False, profileCode = False, additionalCond = None, ageFor = False, ageTo = False):
                    db = QtGui.qApp.db
                    tableActionType = db.table('ActionType')
                    tableAction = db.table('Action')
                    tableEvent = db.table('Event')
                    tableEventType = db.table('EventType')
                    tableClient = db.table('Client')
                    cond = [ tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode('leaved%')),
                             tableAction['deleted'].eq(0),
                             tableEvent['deleted'].eq(0),
                             tableActionType['deleted'].eq(0),
                             tableClient['deleted'].eq(0),
                             tableAction['begDate'].isNotNull(),
                             tableAction['endDate'].isNotNull()
                           ]
                    if additionalCond:
                        cond.append(additionalCond)
                    queryTable = tableActionType.innerJoin(tableAction, tableActionType['id'].eq(tableAction['actionType_id']))
                    queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
                    queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
                    queryTable = queryTable.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
                    cond.append('''%s'''%(getOrgStructureProperty(u'Отделение', orgStructureIdList, u' = 0')))
                    cond.append(u'''(EventType.medicalAidType_id IN (SELECT rbMedicalAidType.id from rbMedicalAidType where rbMedicalAidType.code IN (\'7\')))''')
                    if noPropertyProfile:
                        cond.append('''%s'''%(getNoPropertyAPHBP()))
                    else:
                        cond.append('''%s'''%(getPropertyAPHBP(profile, noProfileBed)))
                    cond.append(getStringProperty(u'Исход госпитализации', u'(APS.value LIKE \'умер%\' OR APS.value LIKE \'смерть%\')'))
                    cond.append(tableAction['begDate'].ge(begDateTime))
                    cond.append(tableAction['begDate'].le(endDateTime))
                    if ageFor and ageTo and ageFor <= ageTo:
                        cond.append(getAgeRangeCond(ageFor, ageTo))
                    stmt = db.selectDistinctStmt(queryTable, u'COUNT(Client.id) AS countDeath, SUM(%s) AS adultCount, SUM(%s) AS childrenCount'
                                                %(getAdultCount(56,61), getChildrenCount()),
                                                where=cond)
                    query = db.query(stmt)
                    if query.first():
                        record = query.record()
                        return [forceInt(record.value('countDeath')), forceInt(record.value('adultCount')), forceInt(record.value('childrenCount'))]
                    else:
                        return [0, 0, 0]

                def getMovingPresent(orgStructureIdList, profile = None, flagCurrent = False, ageFor = False, ageTo = False, financeTypeId = None, financeTypeIdList=[]):
                    cond = [ tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode('moving%')),
                             tableAction['deleted'].eq(0),
                             tableEvent['deleted'].eq(0),
                             tableAP['deleted'].eq(0),
                             tableActionType['deleted'].eq(0),
                             tableClient['deleted'].eq(0),
                             tableAP['action_id'].eq(tableAction['id'])
                           ]
                    queryTable = tableActionType.innerJoin(tableAction, tableActionType['id'].eq(tableAction['actionType_id']))
                    queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
                    queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
                    queryTable = queryTable.innerJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
                    queryTable = queryTable.innerJoin(tableAP, tableAP['type_id'].eq(tableAPT['id']))
                    queryTable = queryTable.innerJoin(tableAPHB, tableAPHB['id'].eq(tableAP['id']))
                    queryTable = queryTable.innerJoin(tableOSHB, tableOSHB['id'].eq(tableAPHB['value']))
                    queryTable = queryTable.innerJoin(tableOS, tableOS['id'].eq(tableOSHB['master_id']))
                    if financeTypeIdList:
                        cond.append(tableOSHB['finance_id'].inlist(financeTypeIdList))
                    if financeTypeId:
                        cond.append(tableOSHB['finance_id'].eq(financeTypeId))
                    cond.append(tableOS['deleted'].eq(0))
                    cond.append(tableAPT['typeName'].like('HospitalBed'))
                    if orgStructureIdList:
                        cond.append(tableOSHB['master_id'].inlist(orgStructureIdList))
#                    cond.append('''NOT %s'''%(getTransferPropertyInPeriod(u'Переведен из отделения', begDateTime, endDateTime)))
                    if not noProfileBed:
                        cond.append('OrgStructure_HospitalBed.profile_id IS NOT NULL')
#                    if not isPermanentBed:
#                        cond.append(tableOSHB['isPermanent'].eq(1))
                    if profile:
                        if QtGui.qApp.defaultHospitalBedProfileByMoving():
                            cond.append(getPropertyAPHBP(profile, noProfileBed))
                        else:
                            if noProfileBed and len(profile) > 1:
                                cond.append(db.joinOr([tableOSHB['profile_id'].inlist(profile), tableOSHB['profile_id'].isNull()]))
                            else:
                                cond.append(tableOSHB['profile_id'].inlist(profile))
                    else:
                        if QtGui.qApp.defaultHospitalBedProfileByMoving():
                            cond.append(getPropertyAPHBP([], noProfileBed))
                        else:
                            cond.append(tableOSHB['profile_id'].isNull())
                    if bedsSchedule:
                        queryTable = queryTable.innerJoin(tableHBSchedule, tableOSHB['schedule_id'].eq(tableHBSchedule['id']))
                    if bedsSchedule == 1:
                        cond.append(tableHBSchedule['code'].eq(1))
                    elif bedsSchedule == 2:
                        cond.append(tableHBSchedule['code'].ne(1))
                    if ageFor and ageTo and ageFor <= ageTo:
                        cond.append(getAgeRangeCond(ageFor, ageTo))
                    if flagCurrent:
                        cond.append(db.joinOr([tableAction['begDate'].isNull(), tableAction['begDate'].lt(endDateTime)]))
                        cond.append(db.joinOr([tableAction['endDate'].isNull(), tableAction['endDate'].ge(endDateTime)]))
                        stmt = db.selectStmt(queryTable, u'COUNT(Client.id) AS countAll, '
                                                         u'SUM(%s) AS countPatronage, '
                                                         u'SUM(isClientVillager(Client.id)) AS clientRural, '
                                                         u'SUM(%s) AS adultCount' %(getStringProperty(u'Патронаж%', u'(APS.value = \'Да\')'), getAdultCount(56,61)), where=cond)
                        query = db.query(stmt)
                        if query.first():
                            record = query.record()
                            return [forceInt(record.value('countAll')), forceInt(record.value('countPatronage')), forceInt(record.value('clientRural')), forceInt(record.value('adultCount'))]
                        else:
                            return [0, 0, 0, 0]
                    else:
                        cond.append(db.joinOr([tableAction['begDate'].isNull(), tableAction['begDate'].lt(begDateTime)]))
                        cond.append(db.joinOr([tableAction['endDate'].isNull(), tableAction['endDate'].ge(begDateTime)]))
                        return db.getCount(queryTable, countCol='Client.id', where=cond)

                def presentBegDay(profile = None, row = None, groupOS = False, financeTypeId = None, financeTypeIdList=[]):
                    movingPresent = getMovingPresent(orgStructureIdList, profile, False, ageFor, ageTo, financeTypeId, financeTypeIdList)
                    if row:
                        table.setText(row, 3, movingPresent)
                    else:
                        table.setText(sumRowProfile, 3, movingPresent)
                        if groupOS:
                            self.movingPresentAll += movingPresent

                # из других отделений
                def fromMovingTransfer(profile = None, row = None, groupOS = False, financeTypeId = None, financeTypeIdList=[]):
                    def getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile = None, transferIn = False, orgStructureIdList = [], boolFIO = False, ageFor = False, ageTo = False, financeTypeId = None, financeTypeIdList=[]):
                        result = 0
                        if osType:
                            result = getMovingTransfer(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, transferIn, orgStructureIdList, boolFIO, ageFor = ageFor, ageTo = ageTo, transferType=1, financeTypeId = financeTypeId, financeTypeIdList=financeTypeIdList)
                        elif osType == 0:
                            result = getMovingTransferDS(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, transferIn, orgStructureIdList, boolFIO, ageFor = ageFor, ageTo = ageTo, transferType=1, financeTypeId = financeTypeId, financeTypeIdList=financeTypeIdList)
                        else:
                            if bedsSchedule != 2:
                                result = getMovingTransfer(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, transferIn, orgStructureIdList, boolFIO, ageFor = ageFor, ageTo = ageTo, transferType=1, financeTypeId = financeTypeId, financeTypeIdList=financeTypeIdList)
                            if bedsSchedule != 1:
                                result += getMovingTransferDS(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, transferIn, orgStructureIdList, boolFIO, ageFor = ageFor, ageTo = ageTo, transferType=1, financeTypeId = financeTypeId, financeTypeIdList=financeTypeIdList)
                        return result
                    movingTransfer = getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен из отделения', profile, False, orgStructureIdList, ageFor = ageFor, ageTo = ageTo, financeTypeId = financeTypeId, financeTypeIdList=financeTypeIdList)
                    if row:
                        table.setText(row, 9, movingTransfer)
                    else:
                        table.setText(sumRowProfile, 9, movingTransfer)
                        if groupOS:
                            self.movingTransferAll += movingTransfer

                def receivedAll(profile = None, row = None, groupOS = False, financeTypeId = None, financeTypeIdList=[]):
                    def getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty = u'Переведен из отделения', profile = None, orgStructureIdList = [], boolFIO = False, noPropertyProfile = False, ageFor = False, ageTo = False, financeTypeId = None, financeTypeIdList=[], adultAgeFemale=56, adultAgeMale=61):
                        result1 = result2 = [0, 0, 0, 0, 0, 0, 0]
                        if bedsSchedule != 2:
                            result1 = getReceived(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, orgStructureIdList, boolFIO, noPropertyProfile, ageFor = ageFor, ageTo = ageTo, financeTypeId = financeTypeId, financeTypeIdList=financeTypeIdList, adultAgeFemale=adultAgeFemale, adultAgeMale=adultAgeMale)
                        if bedsSchedule != 1:
                            result2 = getReceivedDS(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, orgStructureIdList, boolFIO, noPropertyProfile, ageFor = ageFor, ageTo = ageTo, financeTypeId = financeTypeId, financeTypeIdList=financeTypeIdList, adultAgeFemale=adultAgeFemale, adultAgeMale=adultAgeMale)
                        return list(map(lambda x, y: (x or 0) + (y or 0), result1, result2))
                    self.receivedBedsAll = 0
                    if osType:
                        getR = getReceived
                    elif osType == 0:
                        getR = getReceivedDS
                    else:
                        getR = getFunc
                    # all, children, adultCount, clientRural, isStationaryDay, orderPlan, orderExtren
                    receivedInfo = getR(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен из отделения', profile, orgStructureIdList, ageFor = ageFor, ageTo = ageTo, financeTypeId = financeTypeId, financeTypeIdList=financeTypeIdList, adultAgeFemale=56, adultAgeMale=61)
                    if row:
                        receivedBedAll = receivedInfo[5]
                        childrenCount = receivedInfo[1]
                        adultCount = receivedInfo[2]
                        clientRural = receivedInfo[3]
                        isStationaryDay = receivedInfo[4]
                        orderExtren = receivedInfo[6]
                        countAll = receivedInfo[0]
                        if noProfileBed and not profile:
                            receivedInfoNoProfile = getR(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен из отделения', profile, orgStructureIdList, False, True, ageFor = ageFor, ageTo = ageTo, financeTypeId = financeTypeId, financeTypeIdList=financeTypeIdList, adultAgeFemale=56, adultAgeMale=61)
                            receivedBedAllNoProfile = receivedInfoNoProfile[5]
                            receivedBedAll += receivedBedAllNoProfile
                            childrenCountNoProfile = receivedInfoNoProfile[1]
                            childrenCount += childrenCountNoProfile
                            adultCountNoProfile = receivedInfoNoProfile[2]
                            adultCount += adultCountNoProfile
                            clientRuralNoProfile = receivedInfoNoProfile[3]
                            clientRural += clientRuralNoProfile
                            isStationaryDayNoProfile = receivedInfoNoProfile[4]
                            isStationaryDay += isStationaryDayNoProfile
                            orderExtrenNoProfile = receivedInfoNoProfile[6]
                            orderExtren += orderExtrenNoProfile
                            countAllNoProfile = receivedInfoNoProfile[0]
                            countAll += countAllNoProfile
                        self.receivedBedsAll = receivedBedAll
                        table.setText(row, 4,  countAll)
                        table.setText(row, 5,  isStationaryDay)
                        table.setText(row, 6,  clientRural)
                        table.setText(row, 7, childrenCount)
                        table.setText(row, 8, adultCount)
                        table.setText(row, 22, orderExtren)
                    else:
                        receivedBedAll = receivedInfo[5]
                        childrenCount = receivedInfo[1]
                        adultCount = receivedInfo[2]
                        clientRural = receivedInfo[3]
                        isStationaryDay = receivedInfo[4]
                        orderExtren = receivedInfo[6]
                        countAll = receivedInfo[0]
                        if noProfileBed:
                            receivedInfoNoProfile = getR(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен из отделения', profile, orgStructureIdList, False, True, ageFor = ageFor, ageTo = ageTo, financeTypeId = financeTypeId, financeTypeIdList=financeTypeIdList, adultAgeFemale=56, adultAgeMale=61)
                            receivedBedAllNoProfile = receivedInfoNoProfile[5]
                            receivedBedAll += receivedBedAllNoProfile
                            childrenCountNoProfile = receivedInfoNoProfile[1]
                            childrenCount += childrenCountNoProfile
                            adultCountNoProfile = receivedInfoNoProfile[2]
                            adultCount += adultCountNoProfile
                            clientRuralNoProfile = receivedInfoNoProfile[3]
                            clientRural += clientRuralNoProfile
                            isStationaryDayNoProfile = receivedInfoNoProfile[4]
                            isStationaryDay += isStationaryDayNoProfile
                            orderExtrenNoProfile = receivedInfoNoProfile[6]
                            orderExtren += orderExtrenNoProfile
                            countAllNoProfile = receivedInfoNoProfile[0]
                            countAll += countAllNoProfile
                        self.receivedBedsAll = receivedBedAll
                        table.setText(sumRowProfile, 4,  countAll)
                        table.setText(sumRowProfile, 5,  isStationaryDay)
                        table.setText(sumRowProfile, 6,  clientRural)
                        table.setText(sumRowProfile, 7, childrenCount)
                        table.setText(sumRowProfile, 8, adultCount)
                        table.setText(sumRowProfile, 22, orderExtren)
                        if groupOS:
                            self.receivedBedsAllSUM += self.receivedBedsAll
                            self.receivedInfo6 += orderExtren
                            self.receivedInfo0 += countAll
                            self.receivedInfo4 += isStationaryDay
                            self.receivedInfo3 += clientRural
                            self.receivedInfo1 += childrenCount
                            self.receivedInfo2 += adultCount

                def receivedForeignAll(profile = None, row = None, groupOS = False, financeTypeId = None):
                    def getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty = u'Переведен из отделения', profile = None, orgStructureIdList = [], noPropertyProfile = False, ageFor = False, ageTo = False):
                        result1 = result2 = 0
                        if bedsSchedule != 2:
                            result1 = getReceivedForeign(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, orgStructureIdList, noPropertyProfile, ageFor = ageFor, ageTo = ageTo)
                        if bedsSchedule != 1:
                            result2 = getReceivedForeignDS(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, orgStructureIdList, noPropertyProfile, ageFor = ageFor, ageTo = ageTo)
                        return result1 + result2
                    if osType:
                        getR = getReceivedForeign
                    elif osType == 0:
                        getR = getReceivedForeignDS
                    else:
                        getR = getFunc
                        #all, children, adultCount, clientRural, isStationaryDay, orderPlan, orderExtren
                        receivedForeign = getR(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен из отделения', profile, orgStructureIdList, ageFor = ageFor, ageTo = ageTo)
                    if row:
                        if noProfileBed and not profile:
                            receivedForeignNoProfile = getR(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен из отделения', profile, orgStructureIdList, True, ageFor = ageFor, ageTo = ageTo)
                            receivedForeign += receivedForeignNoProfile
                        table.setText(row, 21,  receivedForeign)
                    else:
                        if noProfileBed:
                            receivedForeignNoProfile = getR(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен из отделения', profile, orgStructureIdList, True, ageFor = ageFor, ageTo = ageTo)
                            receivedForeign += receivedForeignNoProfile
                        table.setText(sumRowProfile, 21,  receivedForeign)
                        if groupOS:
                            self.clientForeignSUM += receivedForeign

                # в другие отделения
                def inMovingTransfer(profile = None, row = None, groupOS = False, financeTypeId = None, financeTypeIdList=[]):
                    def getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile = None, transferIn = False, orgStructureIdList = [], boolFIO = False, ageFor = False, ageTo = False, financeTypeId = None, financeTypeIdList=[]):
                        result = 0
                        if osType:
                            result = getMovingTransfer(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, transferIn, orgStructureIdList, boolFIO, ageFor = ageFor, ageTo = ageTo, transferType=0, financeTypeId = financeTypeId, financeTypeIdList=financeTypeIdList)
                        elif osType == 0:
                            result = getMovingTransferDS(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, transferIn, orgStructureIdList, boolFIO, ageFor = ageFor, ageTo = ageTo, transferType=0, financeTypeId = financeTypeId, financeTypeIdList=financeTypeIdList)
                        else:
                            if bedsSchedule != 2:
                                result = getMovingTransfer(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, transferIn, orgStructureIdList, boolFIO, ageFor = ageFor, ageTo = ageTo, transferType=0, financeTypeId = financeTypeId, financeTypeIdList=financeTypeIdList)
                            if bedsSchedule != 1:
                                result += getMovingTransferDS(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, transferIn, orgStructureIdList, boolFIO, ageFor = ageFor, ageTo = ageTo, transferType=0, financeTypeId = financeTypeId, financeTypeIdList=financeTypeIdList)
                        return result
                    inMovingTransfer = getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен в отделение', profile, True, orgStructureIdList, ageFor = ageFor, ageTo = ageTo, financeTypeId = financeTypeId, financeTypeIdList=financeTypeIdList)
                    if row:
                        table.setText(row, 10, inMovingTransfer)
                    else:
                        table.setText(sumRowProfile, 10, inMovingTransfer)
                        if groupOS:
                            self.inMovingTransferAll += inMovingTransfer

                def leavedAll(profile = None, row = None, groupOS = False, financeTypeId = None):
                    def getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty = u'Переведен в отделение', profile = None, orgStructureIdList = [], boolFIO = False, noPropertyProfile = False, ageFor = False, ageTo = False, adultAgeMale=61, adultAgeFemale=56):
                        result1 = result2 = [0, 0, 0, 0, 0]
                        if osType == 0:
                            result2 = getLeavedDS(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, orgStructureIdList, boolFIO, noPropertyProfile, ageFor = ageFor, ageTo = ageTo, adultAgeMale=adultAgeMale, adultAgeFemale=adultAgeFemale)
                        elif osType:
                            result1 = getLeaved(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, orgStructureIdList, boolFIO, noPropertyProfile, ageFor = ageFor, ageTo = ageTo, adultAgeMale=adultAgeMale, adultAgeFemale=adultAgeFemale)
                        else:
                            if bedsSchedule != 2:
                                result1 = getLeaved(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, orgStructureIdList, boolFIO, noPropertyProfile, ageFor = ageFor, ageTo = ageTo, adultAgeMale=adultAgeMale, adultAgeFemale=adultAgeFemale)
                            if bedsSchedule != 1:
                                result2 = getLeavedDS(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, orgStructureIdList, boolFIO, noPropertyProfile, ageFor = ageFor, ageTo = ageTo, adultAgeMale=adultAgeMale, adultAgeFemale=adultAgeFemale)
                        return list(map(lambda x, y: (x or 0) + (y or 0), result1, result2))
                    countLeavedAll, leavedDeath, leavedTransfer, countStationaryDay, leavedAdultCount = getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен в отделение', profile, orgStructureIdList, ageFor = ageFor, ageTo = ageTo, adultAgeMale=61, adultAgeFemale=56)
                    if row:
                        countLeavedAll, leavedDeath, leavedTransfer, countStationaryDay, leavedAdultCount, leavedotkaz = getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен в отделение', profile, orgStructureIdList, ageFor = ageFor, ageTo = ageTo)
                        if noProfileBed and not profile:
                            countLeavedAllNoProfile, leavedDeathNoProfile, leavedTransferNoProfile, countStationaryDayNoProfile, leavedAdultCountNoProfile, leavedotkazNoProfile = getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен в отделение', profile, orgStructureIdList, False, True, ageFor = ageFor, ageTo = ageTo)
                            countLeavedAll   += countLeavedAllNoProfile-leavedotkaz-leavedotkazNoProfile
                            leavedDeath   += leavedDeathNoProfile
                            leavedAdultCount += leavedAdultCountNoProfile
                            countStationaryDay += countStationaryDayNoProfile
                        table.setText(row, 11, countLeavedAll-leavedDeath)
                        table.setText(row, 12, leavedAdultCount)
                        table.setText(row, 13, countStationaryDay)
                    else:
                        countLeavedAll, leavedDeath, leavedTransfer, countStationaryDay, leavedAdultCount, leavedotkaz = getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен в отделение', profile, orgStructureIdList, ageFor = ageFor, ageTo = ageTo)
                        if noProfileBed:
                            countLeavedAllNoProfile, leavedDeathNoProfile, leavedTransferNoProfile, countStationaryDayNoProfile, leavedAdultCountNoProfile, leavedotkazNoProfile = getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен в отделение', profile, orgStructureIdList, False, True, ageFor = ageFor, ageTo = ageTo)
                            countLeavedAll   += countLeavedAllNoProfile-leavedotkaz-leavedotkazNoProfile
                            leavedDeath      += leavedDeathNoProfile
                            leavedAdultCount += leavedAdultCountNoProfile
                            countStationaryDay += countStationaryDayNoProfile
                        table.setText(sumRowProfile, 11, countLeavedAll-leavedDeath)
                        table.setText(sumRowProfile, 12, leavedAdultCount)
                        table.setText(sumRowProfile, 13, countStationaryDay)
                        if groupOS:
                            self.countLeavedSUM += countLeavedAll-leavedDeath
                            self.leavedAdultCountSUM += leavedAdultCount
                            self.countStationaryDaySUM += countStationaryDay

                def leavedAllDeath(profile = None, row = None, groupOS = False, financeTypeId = None):
                    def getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty = u'Переведен в отделение', profile = None, orgStructureIdList = [], noPropertyProfile = False, ageFor = False, ageTo = False):
                        result1 = result2 = [0, 0, 0]
                        if osType == 0:
                            result2 = getLeavedDeathDS(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, orgStructureIdList, noPropertyProfile, ageFor = ageFor, ageTo = ageTo)
                        elif osType:
                            result1 = getLeavedDeath(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, orgStructureIdList, noPropertyProfile, ageFor = ageFor, ageTo = ageTo)
                        else:
                            if bedsSchedule != 2:
                                result1 = getLeavedDeath(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, orgStructureIdList, noPropertyProfile, ageFor = ageFor, ageTo = ageTo)
                            if bedsSchedule != 1:
                                result2 = getLeavedDeathDS(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, orgStructureIdList, noPropertyProfile, ageFor = ageFor, ageTo = ageTo)
                        return list(map(lambda x, y: (x or 0) + (y or 0), result1, result2))
                    leavedDeathCount, leavedAdultCount, leavedChildrenCount = getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен в отделение', profile, orgStructureIdList, ageFor = ageFor, ageTo = ageTo)
                    if row:
                        if noProfileBed and not profile:
                            leavedDeathNoProfile, adultCountDeathNoProfile, childrenCountDeathNoProfile = getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен в отделение', profile, orgStructureIdList, True, ageFor = ageFor, ageTo = ageTo)
                            leavedDeathCount    += leavedDeathNoProfile
                            leavedChildrenCount += childrenCountDeathNoProfile
                            leavedAdultCount    += adultCountDeathNoProfile
                        table.setText(row, 14, leavedDeathCount)
                        table.setText(row, 15, leavedChildrenCount)
                        table.setText(row, 16, leavedAdultCount)
                    else:
                        if noProfileBed:
                            leavedDeathNoProfile, adultCountDeathNoProfile, childrenCountDeathNoProfile = getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен в отделение', profile, orgStructureIdList, True, ageFor = ageFor, ageTo = ageTo)
                            leavedDeathCount    += leavedDeathNoProfile
                            leavedChildrenCount += childrenCountDeathNoProfile
                            leavedAdultCount    += adultCountDeathNoProfile
                        table.setText(sumRowProfile, 14, leavedDeathCount)
                        table.setText(sumRowProfile, 15, leavedChildrenCount)
                        table.setText(sumRowProfile, 16, leavedAdultCount)
                        if groupOS:
                            self.leavedChildrenCountSUM   += leavedChildrenCount
                            self.leavedAdultCountDeathSUM += leavedAdultCount
                            self.leavedDeathSUM           += leavedDeathCount

                def presentEndDay(profile = None, row = None, groupOS = False, financeTypeId = None, financeTypeIdList=[]):
                    self.presentAll, presentPatronag, clientRural, presentAdultCountEnd = getMovingPresent(orgStructureIdList, profile, True, ageFor = ageFor, ageTo = ageTo, financeTypeId = financeTypeId, financeTypeIdList=financeTypeIdList)
                    if row:
                        table.setText(row, 17, self.presentAll)
                        seniorsMovingDays = getSeniorsMovingDays(orgStructureIdList, begDateTime, endDateTime, profile = profile, isHospital = None, rural = None, additionalCond = None, bedsSchedule = bedsSchedule, typeOS = None, financeTypeId = financeTypeId, financeTypeIdList=financeTypeIdList)
                        #table.setText(row, 19, presentAdultCountEnd)
                        table.setText(row, 19, seniorsMovingDays)
                    else:
                        table.setText(sumRowProfile, 17, self.presentAll)
                        seniorsMovingDays = getSeniorsMovingDays(orgStructureIdList, begDateTime, endDateTime, profile = profile, isHospital = None, rural = None, additionalCond = None, bedsSchedule = bedsSchedule, typeOS = None, financeTypeId = financeTypeId, financeTypeIdList=financeTypeIdList)
                        #table.setText(sumRowProfile, 19, presentAdultCountEnd)
                        table.setText(sumRowProfile, 19, seniorsMovingDays)
                        if groupOS:
                            self.presentAllSUM += self.presentAll
                            self.presentAdultCountEndSUM += presentAdultCountEnd
                            self.seniorsMovingDaysSUM += seniorsMovingDays

                def involuteBedDays(profileIdList = None, row = None, groupOS = False, financeTypeId = None, financeTypeIdList = []):
                    tableOSHBI = db.table('OrgStructure_HospitalBed_Involution').alias('OSHBI')
                    dbTable = tableOSHB.innerJoin(tableOSHBI, tableOSHBI['master_id'].eq(tableOSHB['id']))
                    cond = [
                        tableOSHB['profile_id'].inlist(profileIdList),
                        tableOSHB['master_id'].inlist(orgStructureIdList),
                        tableOSHBI['begDate'].lt(endDateTime.addDays(1)),
                        tableOSHBI['endDate'].ge(begDateTime)
                    ]
                    if financeTypeIdList:
                        cond.append(tableOSHB['finance_id'].inlist(financeTypeIdList))
                    if financeTypeId:
                        cond.append(tableOSHB['finance_id'].eq(financeTypeId))
                    recordList = db.getRecordList(dbTable, 'OSHBI.begDate,OSHBI.endDate', cond)
                    days = 0
                    for record in recordList:
                        begDate = forceDate(record.value('begDate'))
                        endDate = forceDate(record.value('endDate'))
                        checkBegDate = begDateTime.date() if begDateTime.time().hour() >= 9 else begDateTime.date().addDays(-1)
                        checkEndDate = endDateTime.date() if endDateTime.time().hour() > 9 else endDateTime.date().addDays(-1)
                        if begDate < checkBegDate:
                            begDate = checkBegDate
                        if endDate > checkEndDate:
                            endDate = checkEndDate
                        days += begDate.daysTo(endDate) + 1
                    if row:
                        table.setText(row, 20, days)
                    else:
                        table.setText(sumRowProfile, 20, days)
                        self.involuteBedsSUM += days

                unrolledHospitalBed34(profileIdList, None, groupOS, financeTypeId = financeTypeId, financeTypeIdList=financeTypeIdList)
                presentBegDay(profileIdList, None, groupOS, financeTypeId = financeTypeId, financeTypeIdList=financeTypeIdList)
                receivedAll(profileIdList, None, groupOS, financeTypeId = financeTypeId, financeTypeIdList=financeTypeIdList)
                receivedForeignAll(profileIdList, None, groupOS, financeTypeId = financeTypeId)
                fromMovingTransfer(profileIdList, None, groupOS, financeTypeId = financeTypeId, financeTypeIdList=financeTypeIdList)
                inMovingTransfer(profileIdList, None, groupOS, financeTypeId = financeTypeId, financeTypeIdList=financeTypeIdList)
                leavedAll(profileIdList, None, groupOS, financeTypeId = financeTypeId)
                leavedAllDeath(profileIdList, None, groupOS, financeTypeId = financeTypeId)
                presentEndDay(profileIdList, None, groupOS, financeTypeId = financeTypeId)
                averageYarHospitalBed(orgStructureIdList, table, begDate, endDate, groupOS, profileIdList, None, sumRowProfile, financeTypeId = financeTypeId, financeTypeIdList=financeTypeIdList)
                table.setText(sumRowProfile, 18, getMovingDays(orgStructureIdList, begDateTime, endDateTime, profileIdList, bedsSchedule = bedsSchedule, financeTypeId=financeTypeId))
                involuteBedDays(profileIdList, None, groupOS, financeTypeId = financeTypeId, financeTypeIdList=financeTypeIdList)
                if noProfileBed and not financeTypeId:
                    table.setText(rowProfile, 0, u'профиль койки не определен')
                    unrolledHospitalBed34([], rowProfile, financeTypeId = financeTypeId, financeTypeIdList=financeTypeIdList)
                    presentBegDay([], rowProfile, financeTypeId = financeTypeId, financeTypeIdList=financeTypeIdList)
                    receivedAll([], rowProfile, financeTypeId = financeTypeId, financeTypeIdList=financeTypeIdList)
                    receivedForeignAll([], rowProfile, financeTypeId = financeTypeId)
                    fromMovingTransfer([], rowProfile, financeTypeId = financeTypeId, financeTypeIdList=financeTypeIdList)
                    inMovingTransfer([], rowProfile, financeTypeId = financeTypeId, financeTypeIdList=financeTypeIdList)
                    leavedAll([], rowProfile, financeTypeId = financeTypeId)
                    leavedAllDeath([], rowProfile, financeTypeId = financeTypeId)
                    presentEndDay([], rowProfile, financeTypeId = financeTypeId)
                    averageYarHospitalBed([], table, begDate, endDate, False, None, None, rowProfile, financeTypeId = financeTypeId, financeTypeIdList=financeTypeIdList)
                    table.setText(rowProfile, 18, getMovingDays([], begDateTime, endDateTime, None, bedsSchedule = bedsSchedule, financeTypeId=financeTypeId))
                    involuteBedDays([], rowProfile, financeTypeId = financeTypeId, financeTypeIdList=financeTypeIdList)
                cond = []
                queryTable = tableRbHospitalBedProfile
                if hospitalBedProfileList:
                    cond.append(tableRbHospitalBedProfile['id'].inlist(hospitalBedProfileList))
                else:
                    cond.append(tableRbHospitalBedProfile['id'].inlist(profileIdList))
                stmt = db.selectDistinctStmt(queryTable, [tableRbHospitalBedProfile['id'], tableRbHospitalBedProfile['code'], tableRbHospitalBedProfile['name']], cond, u'rbHospitalBedProfile.code')
                query = db.query(stmt)
                sizeQuery = query.size()
                if noProfileBed and not financeTypeId:
                    if sizeQuery > 0:
                        rowProfile = table.addRow()
                sizeQuery -= 1
                while query.next():
                    record = query.record()
                    profileId = forceRef(record.value('id'))
                    profileName = forceString(record.value('name'))
                    table.setText(rowProfile, 0, profileName)
                    unrolledHospitalBed34([profileId], rowProfile, financeTypeId = financeTypeId, financeTypeIdList=financeTypeIdList)
                    presentBegDay([profileId], rowProfile, financeTypeId = financeTypeId, financeTypeIdList=financeTypeIdList)
                    receivedAll([profileId], rowProfile, financeTypeId = financeTypeId, financeTypeIdList=financeTypeIdList)
                    receivedForeignAll([profileId], rowProfile, financeTypeId = financeTypeId)
                    fromMovingTransfer([profileId], rowProfile, financeTypeId = financeTypeId, financeTypeIdList=financeTypeIdList)
                    inMovingTransfer([profileId], rowProfile, financeTypeId = financeTypeId, financeTypeIdList=financeTypeIdList)
                    leavedAll([profileId], rowProfile, financeTypeId = financeTypeId)
                    leavedAllDeath([profileId], rowProfile, financeTypeId = financeTypeId)
                    presentEndDay([profileId], rowProfile, financeTypeId = financeTypeId)
                    averageYarHospitalBed(orgStructureIdList, table, begDate, endDate, False, [profileId], rowProfile, sumRowProfile, financeTypeId = financeTypeId, financeTypeIdList=financeTypeIdList)
                    table.setText(rowProfile, 18, getMovingDays(orgStructureIdList, begDateTime, endDateTime, [profileId], bedsSchedule = bedsSchedule, financeTypeId=financeTypeId))
                    involuteBedDays([profileId], rowProfile, financeTypeId = financeTypeId, financeTypeIdList=financeTypeIdList)
                    if sizeQuery > 0:
                        rowProfile = table.addRow()
                        sizeQuery -= 1
                return table.addRow() if sizeQuery > 0 else rowProfile

            boldChars = QtGui.QTextCharFormat()
            boldChars.setFontWeight(QtGui.QFont.Bold)
            def getOrgStructureParent(orgStructureIdList, rowProfile, table, financeTypeId = None):
                for parentOrgStructureId in orgStructureIdList:
                    tableQuery = tableOS.innerJoin(tableOSHB, tableOSHB['master_id'].eq(tableOS['id']))
                    cond = [tableOS['deleted'].eq(0),
                            tableOS['id'].eq(parentOrgStructureId)]
                    if financeTypeId:
                        cond.append(tableOSHB['finance_id'].eq(financeTypeId))
                    if hospitalBedProfileList:
                        cond.append(tableOSHB['profile_id'].inlist(hospitalBedProfileList))
                    recordEx = db.getRecordEx(tableQuery,
                                              [tableOS['name'], tableOS['id'], tableOS['type']], cond)
                    if recordEx:
                        name = forceString(recordEx.value('name'))
                        osType = forceInt(recordEx.value('type'))
                        rowProfile = table.addRow()
                        table.setText(rowProfile, 0, name, boldChars)
                        sumRowProfile = rowProfile
                        rowProfile = table.addRow()
                        profileIdList = getHospitalBedProfile([parentOrgStructureId], hbProfileIdList=hospitalBedProfileList, financeTypeId=financeTypeId)
                        rowProfile = getDataReport([parentOrgStructureId], rowProfile, table, sumRowProfile, True, profileIdList, osType, financeTypeId = financeTypeId, financeTypeIdList=financeTypeIdList)
                        cond =  [tableOS['deleted'].eq(0),
                                                    tableOS['parent_id'].eq(parentOrgStructureId)]
                        if hospitalBedProfileList:
                            cond.append(tableOSHB['profile_id'].inlist(hospitalBedProfileList))
                        records = db.getRecordList(tableQuery, [tableOS['id'], tableOS['name'], tableOS['type']], cond  )
                        for record in records:
                            name = forceString(record.value('name'))
                            orgStructureId = forceRef(record.value('id'))
                            osType = forceInt(record.value('type'))
                            table.setText(rowProfile, 0, name, boldChars)
                            sumRowProfile = rowProfile
                            rowProfile = table.addRow()
                            profileIdList = getHospitalBedProfile([orgStructureId], hbProfileIdList=hospitalBedProfileList, financeTypeId=financeTypeId)
                            rowProfile = getDataReport([orgStructureId], rowProfile, table, sumRowProfile, True, profileIdList, osType, financeTypeId = financeTypeId, financeTypeIdList=financeTypeIdList)
                            #getOrgStructureParent([orgStructureId], rowProfile)
            def getDateReportPay(financeTypeId):
                nextRow = table.addRow()
                if isGroupingOS:
                    getOrgStructureParent(begOrgStructureIdList, None, table, financeTypeId)
                    table.setText(nextRow, 0, u'Всего:\n\nв том числе по %sкойкам:'%(u'платным ' if financeTypeId else u''), boldChars)
                    table.setText(nextRow, 1, self.countBedsAll)
                    table.setText(nextRow, 2, self.monthBed)
                    table.setText(nextRow, 3, self.movingPresentAll)
                    table.setText(nextRow, 4, self.receivedInfo0)
                    table.setText(nextRow, 5, self.receivedInfo4)
                    table.setText(nextRow, 6, self.receivedInfo3)
                    table.setText(nextRow, 7, self.receivedInfo1)
                    table.setText(nextRow, 8, self.receivedInfo2)
                    table.setText(nextRow, 9, self.movingTransferAll)
                    table.setText(nextRow, 10, self.inMovingTransferAll)
                    table.setText(nextRow, 11, self.countLeavedSUM)
                    table.setText(nextRow, 12, self.leavedAdultCountSUM)
                    table.setText(nextRow, 13, self.countStationaryDaySUM)
                    table.setText(nextRow, 14, self.leavedDeathSUM)
                    table.setText(nextRow, 15, self.leavedChildrenCountSUM)
                    table.setText(nextRow, 16, self.leavedAdultCountDeathSUM)
                    table.setText(nextRow, 17, self.presentAllSUM)
                    profileIdList = getHospitalBedProfile(begOrgStructureIdList, hbProfileIdList=hospitalBedProfileList, financeTypeId=financeTypeId)
                    table.setText(nextRow, 18, getMovingDays(begOrgStructureIdList, begDateTime, endDateTime, profileIdList, bedsSchedule = bedsSchedule, financeTypeId=financeTypeId))
                    #table.setText(nextRow, 19, self.presentAdultCountEndSUM)
                    table.setText(nextRow, 19, self.seniorsMovingDaysSUM)
                    table.setText(nextRow, 20, self.involuteBedsSUM)
                    table.setText(nextRow, 21, self.clientForeignSUM)
                    table.setText(nextRow, 22, self.receivedInfo6)
                else:
                    profileIdList = getHospitalBedProfile(begOrgStructureIdList, hbProfileIdList=hospitalBedProfileList, financeTypeId=financeTypeId)
                    table.setText(nextRow, 0, u'Всего:\n\nв том числе по %sкойкам:'%(u'платным ' if financeTypeId else u''), boldChars)
                    if profileIdList or (not profileIdList and not financeTypeId):
                        getDataReport(begOrgStructureIdList, table.addRow(), table, nextRow, False, profileIdList, financeTypeId = financeTypeId, financeTypeIdList=financeTypeIdList)
                    elif not profileIdList and financeTypeId:
                        table.setText(nextRow, 1, self.countBedsAll)
                        table.setText(nextRow, 2, self.monthBed)
                        table.setText(nextRow, 3, self.movingPresentAll)
                        table.setText(nextRow, 4, self.receivedInfo0)
                        table.setText(nextRow, 5, self.receivedInfo4)
                        table.setText(nextRow, 6, self.receivedInfo3)
                        table.setText(nextRow, 7, self.receivedInfo1)
                        table.setText(nextRow, 8, self.receivedInfo2)
                        table.setText(nextRow, 9, self.movingTransferAll)
                        table.setText(nextRow, 10, self.inMovingTransferAll)
                        table.setText(nextRow, 11, self.countLeavedSUM)
                        table.setText(nextRow, 12, self.leavedAdultCountSUM)
                        table.setText(nextRow, 13, self.countStationaryDaySUM)
                        table.setText(nextRow, 14, self.leavedDeathSUM)
                        table.setText(nextRow, 15, self.leavedChildrenCountSUM)
                        table.setText(nextRow, 16, self.leavedAdultCountDeathSUM)
                        table.setText(nextRow, 17, self.presentAllSUM)
                        table.setText(nextRow, 18, 0)
                        table.setText(nextRow, 19, self.seniorsMovingDaysSUM)
                        table.setText(nextRow, 20, self.involuteBedsSUM)
                        table.setText(nextRow, 21, self.clientForeignSUM)
                        table.setText(nextRow, 22, self.receivedInfo6)
            tableRBFinance = db.table('rbFinance')
            financeTypeId = forceRef(db.translate(tableRBFinance, 'code', 4, 'id'))
            getDateReportPay(None)
            if financeTypeId:
                if isGroupingOS:
                    self.countBedsRepairsAll = 0
                    self.movingPresentAll = 0
                    self.movingTransferAll = 0
                    self.receivedBedsAllSUM = 0
                    self.receivedInfo0 = 0
                    self.receivedInfo6 = 0
                    self.receivedInfo4 = 0
                    self.receivedInfo3 = 0
                    self.receivedInfo1 = 0
                    self.receivedInfo2 = 0
                    self.countBedsAll = 0
                    self.inMovingTransferAll = 0
                    self.leavedTransferSUM = 0
                    self.countLeavedSUM = 0
                    self.leavedAdultCountSUM = 0
                    self.leavedAdultCountDeathSUM = 0
                    self.leavedChildrenCountSUM = 0
                    self.leavedDeathSUM = 0
                    self.presentAdultCountEndSUM = 0
                    self.seniorsMovingDaysSUM = 0
                    self.countStationaryDaySUM = 0
                    self.presentAllSUM = 0
                    self.clientRuralSUM = 0
                    self.presentPatronagSUM = 0
                    self.bedsAllSUM = 0
                    self.bedsMenSUM = 0
                    self.bedsWomenSUM = 0
                    self.monthBed = 0
                    self.involuteBedsSUM = 0
                    self.clientForeignSUM = 0
                getDateReportPay(financeTypeId)
        return doc

