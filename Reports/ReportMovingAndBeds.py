# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2021 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################


from PyQt4 import QtGui
from PyQt4.QtCore import Qt,pyqtSignature, QDate, QDateTime, QTime

from library.TreeModel  import forceInt, forceRef, forceString
from library.Utils      import forceDate, forceDateTime

from Events.Utils       import getActionTypeIdListByFlatCode
from Reports.HospitalBedProfileListDialog import CHospitalBedProfileListDialog
from Reports.ReportView import CPageFormat
from Reports.ReportBase import CReportBase, createTable
from Reports.SelectOrgStructureListDialog import CSelectOrgStructureListDialog
from Reports.StationaryF007 import CStationaryF007, getLeaved, getMovingTransfer, getReceived
from Reports.StationaryF007DS import getReceived as getReceivedDS, getLeaved as getLeavedDS, getMovingTransfer as getMovingTransferDS
from Reports.Utils      import countMovingDays, dateRangeAsStr, getMovingDays, getOrstructureHasHospitalBeds, getPropertyAPHBP, getStringProperty, getTheseAndChildrens



from Ui_ReportMovingAndBedsSetupDialog import Ui_ReportMovingAndBedsSetupDialog


class CReportMovingAndBedsSetupDialog(QtGui.QDialog, Ui_ReportMovingAndBedsSetupDialog):
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
        self.orgStructureSelectedItems = params.get('orgStructureSelectedItems', [])
        if self.orgStructureList:
            if len(self.orgStructureList) == 1 and not self.orgStructureList[0]:
                self.lblOrgStructureList.setText(u'подразделение: ЛПУ')
            else:
                self.lblOrgStructureList.setText(u', '.join(self.orgStructureSelectedItems))
        else:
            self.lblOrgStructureList.setText(u'подразделение: ЛПУ')
        self.cmbSchedule.setCurrentIndex(params.get('bedsSchedule', 0))
        self.hospitalBedProfileList = params.get('hospitalBedProfileList', [])
        if self.hospitalBedProfileList:
            db = QtGui.qApp.db
            table = db.table('rbHospitalBedProfile')
            records = db.getRecordList(table, [table['name']], [table['id'].inlist(self.hospitalBedProfileList)])
            self.lblHospitalBedProfileList.setText(u', '.join(forceString(record.value('name')) for record in records if forceString(record.value('name'))))
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
        self.chkTableHeaderOnlyFirstPage.setChecked(params.get('tableHeaderOnlyFirstPage', False))


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
        result['orgStructureSelectedItems'] = self.orgStructureSelectedItems
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
        result['tableHeaderOnlyFirstPage'] = self.chkTableHeaderOnlyFirstPage.isChecked()
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
        self.orgStructureSelectedItems = []
        self.lblOrgStructureList.setText(u'подразделение: ЛПУ')
        dialog = CSelectOrgStructureListDialog(self)
        if dialog.exec_():
            self.orgStructureList = dialog.values()
            for index in dialog.tblSelectOrgStructureList.selectedIndexes():
                itemText = forceString(index.data(Qt.DisplayRole))
                self.orgStructureSelectedItems.append(itemText)
            if self.orgStructureList:
                if len(self.orgStructureList) == 1 and not self.orgStructureList[0]:
                    self.lblOrgStructureList.setText(u'подразделение: ЛПУ')
                else:
                    self.lblOrgStructureList.setText(u', '.join(self.orgStructureSelectedItems))


class CReportMovingAndBeds(CStationaryF007):
    def __init__(self, parent, currentOrgStructureId=None):
        CStationaryF007.__init__(self, parent)
        self.setTitle(u'Анализ движения и использования коечного фонда')
        self.orientation = CPageFormat.Landscape
        self.currentOrgStructureId = currentOrgStructureId


    def getSetupDialog(self, parent):
        result = CReportMovingAndBedsSetupDialog(parent, self.currentOrgStructureId)
        result.setTitle(u'Анализ движения и использования коечного фонда')
        result.setBegDateVisible(True)
        self.stationaryF007SetupDialog = result
        self.stationaryF007SetupDialog.chkFinance.setVisible(True)
        self.stationaryF007SetupDialog.cmbFinance.setVisible(True)
        return result


#    def getCountPatronageList(self, orgStructureIdList, begDateTime, endDateTime, noProfileBed, profile = None, bedsSchedule = False):
#        countPatronage = 0
#        if begDateTime <= endDateTime:
#            newBegDateTime = begDateTime.addDays(1)
#            if newBegDateTime >= endDateTime:
#                newBegDateTime = endDateTime
#            while newBegDateTime <= endDateTime:
#                countPatronage += self.getCountPatronage(orgStructureIdList, newBegDateTime, noProfileBed, profile, bedsSchedule)
#                newBegDateTime = newBegDateTime.addDays(1)
#        return countPatronage


#    def getCountPatronage(self, orgStructureIdList, endDateTime, noProfileBed, profile = None, bedsSchedule = False):
#        countPatronage = 0
#        db = QtGui.qApp.db
#        tableAPT = db.table('ActionPropertyType')
#        tableAP = db.table('ActionProperty')
#        tableActionType = db.table('ActionType')
#        tableAction = db.table('Action')
#        tableEvent = db.table('Event')
#        tableClient = db.table('Client')
#        tableOS = db.table('OrgStructure')
#        tableAPHB = db.table('ActionProperty_HospitalBed')
#        tableOSHB = db.table('OrgStructure_HospitalBed')
#        tableHBSchedule = db.table('rbHospitalBedShedule')
#        cond = [ tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode('moving%')),
#                 tableAction['deleted'].eq(0),
#                 tableEvent['deleted'].eq(0),
#                 tableAP['deleted'].eq(0),
#                 tableActionType['deleted'].eq(0),
#                 tableClient['deleted'].eq(0),
#                 tableAP['action_id'].eq(tableAction['id'])
#               ]
#        queryTable = tableActionType.innerJoin(tableAction, tableActionType['id'].eq(tableAction['actionType_id']))
#        queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
#        queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
#        queryTable = queryTable.innerJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
#        queryTable = queryTable.innerJoin(tableAP, tableAP['type_id'].eq(tableAPT['id']))
#        queryTable = queryTable.innerJoin(tableAPHB, tableAPHB['id'].eq(tableAP['id']))
#        queryTable = queryTable.innerJoin(tableOSHB, tableOSHB['id'].eq(tableAPHB['value']))
#        queryTable = queryTable.innerJoin(tableOS, tableOS['id'].eq(tableOSHB['master_id']))
#        cond.append(tableAPT['typeName'].like('HospitalBed'))
#        if orgStructureIdList:
#            cond.append(tableOS['deleted'].eq(0))
#            cond.append(tableOS['id'].inlist(orgStructureIdList))
#            #cond.append(tableOS['type'].ne(0))
#        if not noProfileBed:
#            cond.append('OrgStructure_HospitalBed.profile_id IS NOT NULL')
#        if profile:
#            if QtGui.qApp.defaultHospitalBedProfileByMoving():
#                cond.append(getPropertyAPHBP(profile, noProfileBed))
#            else:
#                if noProfileBed and len(profile) > 1:
#                    cond.append(db.joinOr([tableOSHB['profile_id'].inlist(profile), tableOSHB['profile_id'].isNull()]))
#                else:
#                    cond.append(tableOSHB['profile_id'].inlist(profile))
#        else:
#            if QtGui.qApp.defaultHospitalBedProfileByMoving():
#                cond.append(getPropertyAPHBP([], noProfileBed))
#            else:
#                cond.append(tableOSHB['profile_id'].isNull())
#        if bedsSchedule:
#            queryTable = queryTable.innerJoin(tableHBSchedule, tableOSHB['schedule_id'].eq(tableHBSchedule['id']))
#        if bedsSchedule == 1:
#            cond.append(tableHBSchedule['code'].eq(1))
#        elif bedsSchedule == 2:
#            cond.append(tableHBSchedule['code'].ne(1))
#        cond.append(db.joinOr([tableAction['begDate'].isNull(), tableAction['begDate'].lt(endDateTime)]))
#        cond.append(db.joinOr([tableAction['endDate'].isNull(), tableAction['endDate'].ge(endDateTime)]))
#        cond.append(getStringProperty(u'''Патронаж%''', u'''(APS.value = 'Да')'''))
#        stmt = db.selectStmt(queryTable, u'COUNT(Action.id) AS countPatronage', where=cond)
#        query = db.query(stmt)
#        while query.next():
#            record = query.record()
#            countPatronage += forceInt(record.value('countPatronage'))
#        return countPatronage


    def getCountPatronageList(self, orgStructureIdList, begDateTime, endDateTime, noProfileBed, profile = None, bedsSchedule = False):
        countPatronage = 0
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
        tableHBSchedule = db.table('rbHospitalBedShedule')
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
        cond.append(tableAPT['typeName'].like('HospitalBed'))
        if orgStructureIdList:
            cond.append(tableOS['deleted'].eq(0))
            cond.append(tableOS['id'].inlist(orgStructureIdList))
            #cond.append(tableOS['type'].ne(0))
        if not noProfileBed:
            cond.append('OrgStructure_HospitalBed.profile_id IS NOT NULL')
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
        else:
            queryTable = queryTable.leftJoin(tableHBSchedule, tableOSHB['schedule_id'].eq(tableHBSchedule['id']))
        if bedsSchedule == 1:
            cond.append(tableHBSchedule['code'].eq(1))
        elif bedsSchedule == 2:
            cond.append(tableHBSchedule['code'].ne(1))
        cond.append(db.joinOr([tableAction['begDate'].isNull(), tableAction['begDate'].le(endDateTime)]))
        cond.append(db.joinOr([tableAction['endDate'].isNull(), tableAction['endDate'].ge(begDateTime)]))
        cond.append(getStringProperty(u'''Патронаж%''', u'''(APS.value = 'Да')'''))
        cols = [tableAction['id'].alias('actionId'),
                tableAction['begDate'],
                tableAction['endDate'],
                tableHBSchedule['code'].alias('scheduleCode')
                ]
        stmt = db.selectStmt(queryTable, cols, where=cond)
        query = db.query(stmt)
        actionIdList = []
        while query.next():
            record = query.record()
            actionId = forceRef(record.value('actionId'))
            if actionId not in actionIdList:
                actionIdList.append(actionId)
                begDate = forceDateTime(record.value('begDate'))
                endDate = forceDateTime(record.value('endDate'))
                schedule = forceInt(record.value('scheduleCode'))
                countPatronage += countMovingDays(begDate, endDate, begDateTime, endDateTime, schedule)
        return countPatronage


    def averageDaysHospitalBed(self, orgStructureIdList, begDatePeriod, endDatePeriod, bedsSchedule, profile = None, isHospital = None, financeTypeIdList=[]):
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
                #tableOS['type'].ne(0),
                tableOSHB['type_id'].eq(bedType),
                tableOSHB['isPermanent'].eq('1')
                ]
        if financeTypeIdList:
            cond.append(tableOSHB['finance_id'].inlist(financeTypeIdList))
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
        if onlyDates:
            bedsSchedule = params.get('bedsSchedule', 0)
            noProfileBed = params.get('noProfileBed', True)
            isPermanentBed = params.get('isPermanentBed', False)
            orgStructureList = params.get('orgStructureList', None)
            orgStructureSelectedItems = params.get('orgStructureSelectedItems', None)
            if orgStructureList:
                if len(orgStructureList) == 1 and not orgStructureList[0]:
                    description.append(u'подразделение: ЛПУ')
                else:
                    description.append(u'подразделение: ' + u','.join(orgStructureSelectedItems))
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
        orgStructureSelectedItems = params.get('orgStructureSelectedItems', None)
        if orgStructureList:
            if len(orgStructureList) == 1 and not orgStructureList[0]:
                underCaptionList.append(u'подразделение: ЛПУ')
            else:
                underCaptionList.append(u'подразделение: ' + u','.join(orgStructureSelectedItems))
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
        columns = [('70%', [], CReportBase.AlignLeft), ('30%', [], CReportBase.AlignLeft)]
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
            else:
                begTime = begTime if begTime else endTime
                begDateTime = QDateTime(begDate, begTime)
            bedsSchedule = params.get('bedsSchedule', 0)
            paramsHospitalBedProfileList = params.get('hospitalBedProfileList', None)
            begOrgStructureIdList = getOrstructureHasHospitalBeds(getTheseAndChildrens(params.get('orgStructureList', [])))
            noProfileBed = params.get('noProfileBed', True)
            isPermanentBed = params.get('isPermanentBed', False)
            noPrintCaption = params.get('noPrintCaption', False)
            isGroupingOS = params.get('isGroupingOS', False)
            noPrintParams = params.get('noPrintFilterParameters', False)
            financeTypeIdList = params.get('financeList', [])

            def getHospitalBedProfile(orgStructureIdList, hbProfileIdList = [], isFirst = False):
                cond = []
                profileIdList = []
                self.hospitalBedIdList = []
#                if not isFirst and not hbProfileIdList:
#                    return None
                if orgStructureIdList:
                    cond.append(tableOSHB['master_id'].inlist(orgStructureIdList))
                if hbProfileIdList:
                    cond.append(tableRbHospitalBedProfile['id'].inlist(hbProfileIdList))
                if QtGui.qApp.defaultHospitalBedProfileByMoving():
                    tableVHospitalBed = db.table('vHospitalBed')
                    condHB = []
                    tableVHospitalBedSchedule = tableVHospitalBed.innerJoin(tableOS,  tableVHospitalBed['master_id'].eq(tableOS['id']))
                    #condHB.append(tableOS['type'].ne(0))
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
                    condHB.append(db.joinOr([tableVHospitalBed['begDate'].isNull(), tableVHospitalBed['begDate'].lt(endDateTime)]))
                    condHB.append(db.joinOr([tableVHospitalBed['endDate'].isNull(), tableVHospitalBed['endDate'].ge(begDateTime)]))
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
    #                    if not isPermanentBed:
    #                        cond.append(tableOSHB['isPermanent'].eq(1))
                    queryTable = tableOSHB.innerJoin(tableRbHospitalBedProfile, tableOSHB['profile_id'].eq(tableRbHospitalBedProfile['id']))
                    queryTable = queryTable.innerJoin(tableOS,  tableOSHB['master_id'].eq(tableOS['id']))
                    #cond.append(tableOS['type'].ne(0))
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

            hospitalBedProfileList = getHospitalBedProfile(begOrgStructureIdList, hbProfileIdList = paramsHospitalBedProfileList, isFirst = True)
            doc = QtGui.QTextDocument()
            cursor = QtGui.QTextCursor(doc)
            cursor.setCharFormat(CReportBase.ReportTitle)
            cursor.insertBlock()
            if not noPrintCaption:
                self.getCaption(cursor, params, u'СВОДНАЯ ВЕДОМОСТЬ учета движения больных и коечного фонда по стационару, отделению или профилю коек за период')
            else:
                cursor.insertText(self.title())
            cursor.insertBlock()
            self.dumpParams(cursor, params, not noPrintParams)
            cursor.setCharFormat(CReportBase.ReportBody)
            cursor.insertBlock()
            cols = [('10%',  [u'', u'', u'', u'', u'1'], CReportBase.AlignLeft),
                    ('4.5%', [u'Число коек', u'На конец', u'', u'', u'2'], CReportBase.AlignRight),
                    ('4.5%', [u'', u'Среднемесячных', u'', u'', u'3'], CReportBase.AlignRight),
                    ('4.5%', [u'Движение больных за истекшие сутки', u'Состояло больных на начало истекших суток', u'',u'', u'4'], CReportBase.AlignRight),
                    ('4.5%', [u'', u'Поступило больных(без переведенных внутри больницы)', u'Плановых', u'', '5'], CReportBase.AlignRight),
                    ('4.5%', [u'', u'', u'Экстренных', u'', '6'], CReportBase.AlignRight),
                    ('4.5%', [u'', u'', u'Всего', u'', '7'], CReportBase.AlignRight),
                    ('4.5%', [u'', u'', u'в т.ч. из дневн. стац.', u'', '8'], CReportBase.AlignRight),
                    ('4.5%', [u'', u'', u'Из них', u'Сельских жителей', u'9'], CReportBase.AlignRight),
                    ('4.5%', [u'', u'', u'', u'0 - 17 лет', u'10'], CReportBase.AlignRight),
                    ('4.5%', [u'', u'', u'', u'60 лет и старше', u'11'], CReportBase.AlignRight),
                    ('4.5%', [u'', u'Переведено больных внутри больницы', u'Из других отделений', u'', u'12'], CReportBase.AlignRight),
                    ('4.5%', [u'', u'', u'В другие отделения', u'', u'13'], CReportBase.AlignRight),
                    ('4.5%', [u'', u'Выписано больных', u'Всего', u'', u'14'], CReportBase.AlignRight),
                    ('4.5%', [u'', u'', u'В т.ч. переведенных в др. стац.', u'', u'15'], CReportBase.AlignRight),
                    ('4.5%', [u'', u'', u'В дневной стационар', u'', u'16'], CReportBase.AlignRight),
                    ('4.5%', [u'', u'Умерло', u'', u'', u'17'], CReportBase.AlignRight),
                    ('4.5%', [u'Состоит на конец периода', u'', u'', u'', u'18'], CReportBase.AlignRight),
                    ('4.5%', [u'проведено койко-дней', u'', u'', u'', u'19'], CReportBase.AlignRight),
                    ('4.5%', [u'число койко-дней закрытия', u'', u'', u'', u'20'], CReportBase.AlignRight),
                    ('4.5%',   [u'Состоит матерей при больных детях', u'', u'', u'', u'21'], CReportBase.AlignRight)
                   ]
            table = createTable(cursor, cols, duplicateHeaderOnNewPage = not params.get('tableHeaderOnlyFirstPage', False))
            table.mergeCells(0, 0, 4, 1) # 1
            table.mergeCells(0, 1, 1, 2) # код
            table.mergeCells(1, 1, 3, 1) # код
            table.mergeCells(1, 2, 3, 1) # код
            table.mergeCells(0, 3, 1, 13) # Движение больных за истекшие сутки
            table.mergeCells(1, 3, 3, 1) # Состояло больных на начало истекших суток
            table.mergeCells(1, 4, 1, 7) # Поступило больных
            table.mergeCells(2, 4, 2, 1) # - Плановых
            table.mergeCells(2, 5, 2, 1) # - Экстренных
            table.mergeCells(2, 6, 2, 1) # - Всего
            table.mergeCells(2, 7, 2, 1) # Поступило больных - Из них-
            table.mergeCells(2, 8, 2, 1) #
            table.mergeCells(2, 9, 2, 1) #
            table.mergeCells(2, 10, 2, 1) #

            table.mergeCells(1, 11, 1, 2) # Переведено больных внутри больницы
            table.mergeCells(2, 11, 2, 1) # -Из других отделений
            table.mergeCells(2, 12, 2, 1) # Переведено больных внутри больницы-В другие отделения
            table.mergeCells(1, 13, 1, 3) # Выписано больных
            table.mergeCells(2, 13, 2, 1) # -Всего
            table.mergeCells(2, 14, 2, 1) # Выписано больных-В т.ч. переведенных в другие стационары
            table.mergeCells(2, 15, 2, 1) # Выписано больных-В т.ч. в дневной стационар
            table.mergeCells(0, 16, 4, 1) # Умерло
            table.mergeCells(0, 17, 4, 1)
            table.mergeCells(0, 18, 4, 1)
            table.mergeCells(0, 19, 4, 1)
            table.mergeCells(0, 20, 4, 1)

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
            self.leavedDeathSUM = 0
            self.countStationaryDaySUM = 0
            self.presentAllSUM = 0
            self.clientRuralSUM = 0
            self.presentPatronagSUM = 0
            self.monthBed = 0
            self.involuteBedsSUM = 0
            self.countPatronage = 0
            self.rowsWithoutBeds = []

            def averageYarHospitalBed(orgStructureIdList, table, begDate, endDate, groupOS, profile = None, row = None, sumRowProfile = None, isHospital = None, financeTypeIdList=[]):
                days = 0
                daysMonths = 0
                period = begDate.daysTo(endDate)
                days = self.averageDaysHospitalBed(orgStructureIdList, begDate, endDate, bedsSchedule, profile, isHospital, financeTypeIdList=financeTypeIdList)
                daysMonths += days / (period if period > 0 else 1)
                table.setText(row if row else sumRowProfile, 2, daysMonths)
                if groupOS:
                    self.monthBed += daysMonths

            def getDataReport(parOrgStructureIdList, rowProfile, table, sumRowProfile, groupOS, profileIdList, osType = None, financeTypeIdList=[]):
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
#                    joinOr1 = db.joinAnd([tableAction['begDate'].isNull(), tableAction['endDate'].isNull()])
#                    joinOr2 = db.joinAnd([tableAction['begDate'].isNotNull(), tableAction['begDate'].ge(begDateTime), tableAction['begDate'].lt(endDateTime)])
#                    joinOr3 = db.joinAnd([tableAction['begDate'].isNull(), tableAction['endDate'].isNotNull(), tableAction['endDate'].gt(begDateTime)])
#                    cond.append(db.joinOr([joinOr1, joinOr2, joinOr3]))
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

                def unrolledHospitalBed34(profile = None, row = None, groupOS = False, financeTypeIdList=[]):
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
                        #condRepairs.append(tableOS['type'].ne(0))
                        condRepairs.append(tableOS['deleted'].eq(0))
                        if bedsSchedule:
                            tableVHospitalBedSchedule = tableVHospitalBedSchedule.innerJoin(tableHBSchedule, tableVHospitalBed['schedule_id'].eq(tableHBSchedule['id']))
                        if bedsSchedule == 1:
                            condRepairs.append(tableHBSchedule['code'].eq(1))
                        elif bedsSchedule == 2:
                            condRepairs.append(tableHBSchedule['code'].ne(1))
                        if financeTypeIdList:
                            condRepairs.append(tableVHospitalBed['finance_id'].inlist(financeTypeIdList))
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
                        #cond.append(tableOS['type'].ne(0))
                        cond.append(tableOS['deleted'].eq(0))
                        if orgStructureIdList:
                            cond.append(tableVHospitalBed['master_id'].inlist(orgStructureIdList))
                        if not isPermanentBed:
                            cond.append(tableVHospitalBed['isPermanent'].eq(1))
                        if profile:
                            if noProfileBed and len(profile) > 1:
                                cond.append(db.joinOr([tableVHospitalBed['profile_id'].inlist(profile), tableVHospitalBed['profile_id'].isNull()]))
                            else:
                                cond.append(tableVHospitalBed['profile_id'].inlist(profile))
                        else:
                            cond.append(tableVHospitalBed['profile_id'].isNull())
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
                        cond.append(db.joinOr([tableVHospitalBed['begDate'].isNull(), tableVHospitalBed['begDate'].lt(endDateTime)]))
                        cond.append(db.joinOr([tableVHospitalBed['endDate'].isNull(), tableVHospitalBed['endDate'].ge(begDateTime)]))
                        #condRepairs.append(tableOS['type'].ne(0))

                        if orgStructureIdList:
                            condRepairs.append(tableVHospitalBed['master_id'].inlist(orgStructureIdList))
                        if profile:
                            if noProfileBed and len(profile) > 1:
                                condRepairs.append(db.joinOr([tableVHospitalBed['profile_id'].inlist(profile), tableVHospitalBed['profile_id'].isNull()]))
                            else:
                                condRepairs.append(tableVHospitalBed['profile_id'].inlist(profile))
                        else:
                            condRepairs.append(tableVHospitalBed['profile_id'].isNull())
                        self.countBeds = db.getCount(tableVHospitalBedSchedule, countCol='vHospitalBed.id', where=cond)
                        countBedsRepairs = db.getCount(tableVHospitalBedSchedule.innerJoin(tableInvolution, tableInvolution['master_id'].eq(tableVHospitalBed['id'])), countCol='vHospitalBed.id', where=condRepairs)
                        if row:
                           table.setText(row, 1, self.countBeds)
                           if self.countBeds == 0:
                               self.rowsWithoutBeds.append(row)
                        else:
                            table.setText(sumRowProfile, 1, self.countBeds)
                            if groupOS:
                                self.countBedsAll += self.countBeds
                                self.countBedsRepairsAll += countBedsRepairs

                def getMovingPresent(profile = None, flagCurrent = False, financeTypeIdList=[]):
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
                    cond.append(tableOS['deleted'].eq(0))
                    #cond.append(tableOS['type'].ne(0))
                    cond.append(tableAPT['typeName'].like('HospitalBed'))
                    if financeTypeIdList:
                        cond.append(tableOSHB['finance_id'].inlist(financeTypeIdList))
                    if orgStructureIdList:
                        cond.append(tableOSHB['master_id'].inlist(orgStructureIdList))
                    #cond.append('''NOT %s'''%(getTransferPropertyInPeriod(u'Переведен из отделения', begDateTime, endDateTime)))
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
                    if flagCurrent:
                        cond.append(db.joinOr([tableAction['begDate'].isNull(), tableAction['begDate'].lt(endDateTime)]))
                        cond.append(db.joinOr([tableAction['endDate'].isNull(), tableAction['endDate'].ge(endDateTime)]))
                        stmt = db.selectStmt(queryTable, u'COUNT(Client.id) AS countAll, '
                                                         u'SUM(%s) AS countPatronage, '
                                                         u'SUM(isClientVillager(Client.id)) AS clientRural' %(getStringProperty(u'Патронаж%', u'(APS.value = \'Да\')')), where=cond)
                        query = db.query(stmt)
                        if query.first():
                            record = query.record()
                            return [forceInt(record.value('countAll')), forceInt(record.value('countPatronage')), forceInt(record.value('clientRural'))]
                        else:
                            return [0, 0, 0]
                    else:
                        cond.append(db.joinOr([tableAction['begDate'].isNull(), tableAction['begDate'].lt(begDateTime)]))
                        cond.append(db.joinOr([tableAction['endDate'].isNull(), tableAction['endDate'].ge(begDateTime)]))
                        return db.getCount(queryTable, countCol='Client.id', where=cond)

                def presentBegDay(profile = None, row = None, groupOS = False, financeTypeIdList=[]):
                    if row:
                        table.setText(row, 3, getMovingPresent(profile, financeTypeIdList=financeTypeIdList))
                    else:
                        movingPresent = getMovingPresent(profile, financeTypeIdList=financeTypeIdList)
                        table.setText(sumRowProfile, 3, movingPresent)
                        if groupOS:
                            self.movingPresentAll += movingPresent
                # из других отделений
                def fromMovingTransfer(profile = None, row = None, groupOS = False, financeTypeIdList=[]):
                    def getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile = None, transferIn = False, orgStructureIdList = [], boolFIO = False, financeTypeIdList=[]):
                        result = 0
                        if osType:
                            result = getMovingTransfer(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, transferIn, orgStructureIdList, boolFIO, transferType=1, financeTypeIdList=financeTypeIdList)
                        elif osType == 0:
                            result = getMovingTransferDS(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, transferIn, orgStructureIdList, boolFIO, transferType=1, financeTypeIdList=financeTypeIdList)
                        else:
                            if bedsSchedule != 2:
                                result = getMovingTransfer(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, transferIn, orgStructureIdList, boolFIO, transferType=1, financeTypeIdList=financeTypeIdList)
                            if bedsSchedule != 1:
                                result += getMovingTransferDS(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, transferIn, orgStructureIdList, boolFIO, transferType=1, financeTypeIdList=financeTypeIdList)
                        return result
                    if row:
                        table.setText(row, 11, getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен из отделения', profile, False, orgStructureIdList, financeTypeIdList=financeTypeIdList))
                    else:
                        movingTransfer = getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен из отделения', profile, False, orgStructureIdList, financeTypeIdList=financeTypeIdList)
                        table.setText(sumRowProfile, 11, movingTransfer)
                        if groupOS:
                            self.movingTransferAll += movingTransfer

                def receivedAll(profile = None, row = None, groupOS = False, financeTypeIdList=[]):
                    def getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty = u'Переведен из отделения', profile = None, orgStructureIdList = [], boolFIO = False, noPropertyProfile = False, financeTypeIdList=[]):
                        result1 = result2 = [0, 0, 0, 0, 0, 0, 0]
                        if bedsSchedule != 2:
                            result1 = getReceived(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, orgStructureIdList, boolFIO, noPropertyProfile, financeTypeIdList=financeTypeIdList)
                        if bedsSchedule != 1:
                            result2 = getReceivedDS(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, orgStructureIdList, boolFIO, noPropertyProfile, financeTypeIdList=financeTypeIdList)
                        return list(map(lambda x, y: (x or 0) + (y or 0), result1, result2))
                    self.receivedBedsAll = 0
                    if osType:
                        getR = getReceived
                    elif osType == 0:
                        getR = getReceivedDS
                    else:
                        getR = getFunc
                    if row:
                        #all, children, adultCount, clientRural, isStationaryDay, orderPlan, orderExtren
                        receivedInfo = getR(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен из отделения', profile, orgStructureIdList, financeTypeIdList=financeTypeIdList)
                        receivedBedAll = receivedInfo[5]
                        childrenCount = receivedInfo[1]
                        adultCount = receivedInfo[2]
                        clientRural = receivedInfo[3]
                        isStationaryDay = receivedInfo[4]
                        orderExtren = receivedInfo[6]
                        countAll = receivedInfo[0]
                        if noProfileBed and not profile:
                            receivedInfoNoProfile = getR(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен из отделения', profile, orgStructureIdList, False, True, financeTypeIdList=financeTypeIdList)
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
                        table.setText(row, 4,  self.receivedBedsAll)
                        table.setText(row, 5,  orderExtren)
                        table.setText(row, 6,  countAll)
                        table.setText(row, 7,  isStationaryDay)
                        table.setText(row, 8,  clientRural)
                        table.setText(row, 9, childrenCount)
                        table.setText(row, 10, adultCount)
                    else:
                        #all, children, adultCount, clientRural, isStationaryDay, orderPlan, orderExtren
                        receivedInfo = getR(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен из отделения', profile, orgStructureIdList, financeTypeIdList=financeTypeIdList)
                        receivedBedAll = receivedInfo[5]
                        childrenCount = receivedInfo[1]
                        adultCount = receivedInfo[2]
                        clientRural = receivedInfo[3]
                        isStationaryDay = receivedInfo[4]
                        orderExtren = receivedInfo[6]
                        countAll = receivedInfo[0]
                        if noProfileBed:
                            receivedInfoNoProfile = getR(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен из отделения', profile, orgStructureIdList, False, True, financeTypeIdList=financeTypeIdList)
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
                        table.setText(sumRowProfile, 4,  self.receivedBedsAll)
                        table.setText(sumRowProfile, 5,  orderExtren)
                        table.setText(sumRowProfile, 6,  countAll)
                        table.setText(sumRowProfile, 7,  isStationaryDay)
                        table.setText(sumRowProfile, 8,  clientRural)
                        table.setText(sumRowProfile, 9, childrenCount)
                        table.setText(sumRowProfile, 10, adultCount)
                        if groupOS:
                            self.receivedBedsAllSUM += self.receivedBedsAll
                            self.receivedInfo6 += orderExtren
                            self.receivedInfo0 += countAll
                            self.receivedInfo4 += isStationaryDay
                            self.receivedInfo3 += clientRural
                            self.receivedInfo1 += childrenCount
                            self.receivedInfo2 += adultCount

                # в другие отделения
                def inMovingTransfer(profile = None, row = None, groupOS = False, financeTypeIdList=[]):
                    def getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile = None, transferIn = False, orgStructureIdList = [], boolFIO = False, financeTypeIdList=[]):
                        result = 0
                        if osType:
                            result = getMovingTransfer(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, transferIn, orgStructureIdList, boolFIO, transferType=0, financeTypeIdList=financeTypeIdList)
                        elif osType == 0:
                            result = getMovingTransferDS(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, transferIn, orgStructureIdList, boolFIO, transferType=0, financeTypeIdList=financeTypeIdList)
                        else:
                            if bedsSchedule != 2:
                                result = getMovingTransfer(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, transferIn, orgStructureIdList, boolFIO, transferType=0, financeTypeIdList=financeTypeIdList)
                            if bedsSchedule != 1:
                                result += getMovingTransferDS(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, transferIn, orgStructureIdList, boolFIO, transferType=0, financeTypeIdList=financeTypeIdList)
                        return result
                    if row:
                        table.setText(row, 12, getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен в отделение', profile, True, orgStructureIdList, financeTypeIdList=financeTypeIdList))
                    else:
                        inMovingTransfer = getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен в отделение', profile, True, orgStructureIdList, financeTypeIdList=financeTypeIdList)
                        table.setText(sumRowProfile, 12, inMovingTransfer)
                        if groupOS:
                            self.inMovingTransferAll += inMovingTransfer

                def leavedAll(profile = None, row = None, groupOS = False):
                    def getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty = u'Переведен в отделение', profile = None, orgStructureIdList = [], boolFIO = False, noPropertyProfile = False):
                        result1 = result2 = [0, 0, 0, 0, 0, 0]
                        if osType == 0:
                            result2 = getLeavedDS(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, orgStructureIdList, boolFIO, noPropertyProfile)
                        elif osType:
                            result1 = getLeaved(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, orgStructureIdList, boolFIO, noPropertyProfile)
                        else:
                            if bedsSchedule != 2:
                                result1 = getLeaved(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, orgStructureIdList, boolFIO, noPropertyProfile)
                            if bedsSchedule != 1:
                                result2 = getLeavedDS(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, orgStructureIdList, boolFIO, noPropertyProfile)
                        return list(map(lambda x, y: (x or 0) + (y or 0), result1, result2))
                    if row:
                        countLeavedAll, leavedDeath, leavedTransfer, countStationaryDay, leavedAdultCount, leavedotkaz = getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен в отделение', profile, orgStructureIdList)
                        if noProfileBed and not profile:
                            countLeavedAllNoProfile, leavedDeathNoProfile, leavedTransferNoProfile, countStationaryDayNoProfile, leavedAdultCountNoProfile, leavedotkazNoProfile = getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен в отделение', profile, orgStructureIdList, False, True)
                            countLeavedAll += countLeavedAllNoProfile
                            leavedDeath += leavedDeathNoProfile
                            leavedTransfer += leavedTransferNoProfile
                            countStationaryDay += countStationaryDayNoProfile
                        table.setText(row, 13, countLeavedAll-leavedDeath)
                        table.setText(row, 14, leavedTransfer)
                        table.setText(row, 15, countStationaryDay)
                        table.setText(row, 16, leavedDeath)
                    else:
                        countLeavedAll, leavedDeath, leavedTransfer, countStationaryDay, leavedAdultCount, leavedotkaz = getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен в отделение', profile, orgStructureIdList)
                        if noProfileBed:
                            countLeavedAllNoProfile, leavedDeathNoProfile, leavedTransferNoProfile, countStationaryDayNoProfile, leavedAdultCountNoProfile, leavedotkazNoProfile = getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен в отделение', profile, orgStructureIdList, False, True)
                            countLeavedAll += countLeavedAllNoProfile
                            leavedDeath += leavedDeathNoProfile
                            leavedTransfer += leavedTransferNoProfile
                            countStationaryDay += countStationaryDayNoProfile
                        table.setText(sumRowProfile, 13, countLeavedAll-leavedDeath)
                        table.setText(sumRowProfile, 14, leavedTransfer)
                        table.setText(sumRowProfile, 15, countStationaryDay)
                        table.setText(sumRowProfile, 16, leavedDeath)
                        if groupOS:
                            self.countLeavedSUM += countLeavedAll-leavedDeath
                            self.leavedTransferSUM += leavedTransfer
                            self.leavedDeathSUM += leavedDeath
                            self.countStationaryDaySUM += countStationaryDay

                def presentEndDay(profile = None, row = None, groupOS = False, financeTypeIdList=[]):
                    self.presentAll = 0
                    if row:
                        self.presentAll, presentPatronag, clientRural = getMovingPresent(profile, True, financeTypeIdList=financeTypeIdList)
                        table.setText(row, 17, self.presentAll)
                    else:
                        self.presentAll, presentPatronag, clientRural = getMovingPresent(profile, True, financeTypeIdList=financeTypeIdList)
                        table.setText(sumRowProfile, 17, self.presentAll)
                        if groupOS:
                            self.presentAllSUM += self.presentAll
                            self.clientRuralSUM += clientRural
                            self.presentPatronagSUM += presentPatronag

                def involuteBedDays(profileIdList = None, row = None, groupOS = False, financeTypeIdList = []):
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
                        table.setText(row, 19, days)
                    else:
                        table.setText(sumRowProfile, 19, days)
                        self.involuteBedsSUM += days

                unrolledHospitalBed34(profileIdList, None, groupOS, financeTypeIdList=financeTypeIdList)
                presentBegDay(profileIdList, None, groupOS, financeTypeIdList=financeTypeIdList)
                receivedAll(profileIdList, None, groupOS, financeTypeIdList=financeTypeIdList)
                fromMovingTransfer(profileIdList, None, groupOS, financeTypeIdList=financeTypeIdList)
                inMovingTransfer(profileIdList, None, groupOS, financeTypeIdList=financeTypeIdList)
                leavedAll(profileIdList, None, groupOS)
                presentEndDay(profileIdList, None, groupOS, financeTypeIdList=financeTypeIdList)
                averageYarHospitalBed(orgStructureIdList, table, begDate, endDate, groupOS, profileIdList, None, sumRowProfile, financeTypeIdList=financeTypeIdList)
                table.setText(sumRowProfile, 18, getMovingDays(orgStructureIdList, begDateTime, endDateTime, profileIdList, bedsSchedule = bedsSchedule) if hospitalBedProfileList else 0)
                involuteBedDays(profileIdList, None, groupOS, financeTypeIdList=financeTypeIdList)
                countPatronage = self.getCountPatronageList(orgStructureIdList, begDateTime, endDateTime, noProfileBed, profileIdList, bedsSchedule = bedsSchedule)
                table.setText(sumRowProfile, 20, countPatronage)
                if groupOS:
                    self.countPatronage += countPatronage
                if noProfileBed:
                    table.setText(rowProfile, 0, u'профиль койки не определен')
                    unrolledHospitalBed34([], rowProfile, financeTypeIdList=financeTypeIdList)
                    presentBegDay([], rowProfile, financeTypeIdList=financeTypeIdList)
                    receivedAll([], rowProfile, financeTypeIdList=financeTypeIdList)
                    fromMovingTransfer([], rowProfile, financeTypeIdList=financeTypeIdList)
                    inMovingTransfer([], rowProfile, financeTypeIdList=financeTypeIdList)
                    leavedAll([], rowProfile)
                    presentEndDay([], rowProfile, financeTypeIdList=financeTypeIdList)
                    averageYarHospitalBed(orgStructureIdList, table, begDate, endDate, False, None, None, rowProfile, financeTypeIdList=financeTypeIdList)
                    table.setText(rowProfile, 18, getMovingDays(orgStructureIdList, begDateTime, endDateTime, None, bedsSchedule = bedsSchedule) if hospitalBedProfileList else 0)
                    involuteBedDays([], rowProfile, financeTypeIdList=financeTypeIdList)
                    table.setText(rowProfile, 20, self.getCountPatronageList(orgStructureIdList, begDateTime, endDateTime, noProfileBed, [], bedsSchedule = bedsSchedule))
                cond = []
                queryTable = tableRbHospitalBedProfile
                if hospitalBedProfileList and profileIdList:
                    cond.append(tableRbHospitalBedProfile['id'].inlist(profileIdList))
                    stmt = db.selectDistinctStmt(queryTable, [tableRbHospitalBedProfile['id'], tableRbHospitalBedProfile['code'], tableRbHospitalBedProfile['name']], cond, u'rbHospitalBedProfile.code')
                    query = db.query(stmt)
                    sizeQuery = query.size()
                    if noProfileBed:
                        if sizeQuery > 0:
                            rowProfile = table.addRow()
                    sizeQuery -= 1
                    while query.next():
                        record = query.record()
                        profileId = forceRef(record.value('id'))
                        profileName = forceString(record.value('name'))
                        table.setText(rowProfile, 0, profileName)
                        unrolledHospitalBed34([profileId], rowProfile, financeTypeIdList=financeTypeIdList)
                        presentBegDay([profileId], rowProfile, financeTypeIdList=financeTypeIdList)
                        receivedAll([profileId], rowProfile, financeTypeIdList=financeTypeIdList)
                        fromMovingTransfer([profileId], rowProfile, financeTypeIdList=financeTypeIdList)
                        inMovingTransfer([profileId], rowProfile, financeTypeIdList=financeTypeIdList)
                        leavedAll([profileId], rowProfile)
                        presentEndDay([profileId], rowProfile, financeTypeIdList=financeTypeIdList)
                        averageYarHospitalBed(orgStructureIdList, table, begDate, endDate, False, [profileId], rowProfile, sumRowProfile, financeTypeIdList=financeTypeIdList)
                        table.setText(rowProfile, 18, getMovingDays(orgStructureIdList, begDateTime, endDateTime, [profileId], bedsSchedule = bedsSchedule) if hospitalBedProfileList else 0)
                        involuteBedDays([profileId], rowProfile, financeTypeIdList=financeTypeIdList)
                        table.setText(rowProfile, 20, self.getCountPatronageList(orgStructureIdList, begDateTime, endDateTime, noProfileBed, [profileId], bedsSchedule = bedsSchedule))
                        if sizeQuery > 0:
                            rowProfile = table.addRow()
                            sizeQuery -= 1
                    return table.addRow() if sizeQuery > 0 else rowProfile
                else:
                    return rowProfile

            boldChars = QtGui.QTextCharFormat()
            boldChars.setFontWeight(QtGui.QFont.Bold)
            def getOrgStructureParent(orgStructureIdList, rowProfile, table):
                testList=[]
                for parentOrgStructureId in orgStructureIdList:
                    tableQuery = tableOS.innerJoin(tableOSHB, tableOSHB['master_id'].eq(tableOS['id']))
                    cond = [tableOS['deleted'].eq(0),
                                               tableOS['id'].eq(parentOrgStructureId)]
                    if testList:
                        cond.append(tableOS['id'].notInlist(testList))
                    if hospitalBedProfileList:
                        cond.append(tableOSHB['profile_id'].inlist(hospitalBedProfileList))
                    recordEx = db.getRecordEx(tableQuery,
                                              [tableOS['name'], tableOS['id'], tableOS['type'], tableOS['parent_id']], cond)
                    if recordEx:
                        name = forceString(recordEx.value('name'))
                        osType = forceInt(recordEx.value('type'))
                        ID = forceInt(recordEx.value('id'))
                        parent = forceInt(recordEx.value('parent_id'))
                        testList.append(ID)
                        if parent not in testList:
                            testList.append(parent)
                        rowProfile = table.addRow()
                        table.setText(rowProfile, 0, name, boldChars)
                        sumRowProfile = rowProfile
                        rowProfile = table.addRow() if (hospitalBedProfileList or noProfileBed) else rowProfile
                        profileIdList = getHospitalBedProfile([parentOrgStructureId], hbProfileIdList=hospitalBedProfileList)
                        rowProfile = getDataReport([parentOrgStructureId], rowProfile, table, sumRowProfile, True, profileIdList, osType, financeTypeIdList=financeTypeIdList)
                        cond =  [tableOS['deleted'].eq(0),
                                                    tableOS['parent_id'].eq(parentOrgStructureId)]
                        if hospitalBedProfileList:
                            cond.append(tableOSHB['profile_id'].inlist(hospitalBedProfileList))
                        cond.append(tableOS['id'].notInlist(testList))
                        group = 'OrgStructure.`name`'
                        records = db.getRecordListGroupBy(tableQuery, [tableOS['id'], tableOS['name'], tableOS['type']], cond, group)
                        for record in records:
                            name = forceString(record.value('name'))
                            orgStructureId = forceRef(record.value('id'))
                            osType = forceInt(record.value('type'))
                            table.setText(rowProfile, 0, name, boldChars)
                            sumRowProfile = rowProfile
                            rowProfile = table.addRow()
                            profileIdList = getHospitalBedProfile([orgStructureId], hbProfileIdList=hospitalBedProfileList)
                            rowProfile = getDataReport([orgStructureId], rowProfile, table, sumRowProfile, True, profileIdList, osType, financeTypeIdList=financeTypeIdList)
                            #getOrgStructureParent([orgStructureId], rowProfile)
            #if hospitalBedProfileList or not paramsHospitalBedProfileList:
            nextRow = table.addRow()
            if isGroupingOS:
                getOrgStructureParent(begOrgStructureIdList, None, table)
                table.setText(nextRow, 0, u'Всего:\n\nв том числе по койкам:', boldChars)
                table.setText(nextRow, 1, self.countBedsAll)
                table.setText(nextRow, 2, self.monthBed)
                table.setText(nextRow, 3, self.movingPresentAll)
                table.setText(nextRow, 4, self.receivedBedsAllSUM)
                table.setText(nextRow, 5, self.receivedInfo6)
                table.setText(nextRow, 6, self.receivedInfo0)
                table.setText(nextRow, 7, self.receivedInfo4)
                table.setText(nextRow, 8, self.receivedInfo3)
                table.setText(nextRow, 9, self.receivedInfo1)
                table.setText(nextRow, 10, self.receivedInfo2)
                table.setText(nextRow, 11, self.movingTransferAll)
                table.setText(nextRow, 12, self.inMovingTransferAll)
                table.setText(nextRow, 13, self.countLeavedSUM)
                table.setText(nextRow, 14, self.leavedTransferSUM)
                table.setText(nextRow, 15, self.countStationaryDaySUM)
                table.setText(nextRow, 16, self.leavedDeathSUM)
                table.setText(nextRow, 17, self.presentAllSUM)
                profileIdList = getHospitalBedProfile(begOrgStructureIdList, hbProfileIdList=hospitalBedProfileList)
                table.setText(nextRow, 18, getMovingDays(begOrgStructureIdList, begDateTime, endDateTime, profileIdList, bedsSchedule = bedsSchedule) if hospitalBedProfileList else 0)
                table.setText(nextRow, 19, self.involuteBedsSUM)
                table.setText(nextRow, 20, self.countPatronage)
#                table.setText(nextRow, 19, self.clientRuralSUM)
#                table.setText(nextRow, 20, self.presentPatronagSUM)
            else:
                profileIdList = getHospitalBedProfile(begOrgStructureIdList, hbProfileIdList=hospitalBedProfileList)
                table.setText(nextRow, 0, u'Всего:\n\nв том числе по койкам:', boldChars)
                getDataReport(begOrgStructureIdList, table.addRow() if (hospitalBedProfileList or noProfileBed) else nextRow, table, nextRow, False, profileIdList, financeTypeIdList=financeTypeIdList)

        # удалить строки, где нет коек
        for row in sorted(self.rowsWithoutBeds, reverse=True):
            table.delRow(row, 1)
        return doc

