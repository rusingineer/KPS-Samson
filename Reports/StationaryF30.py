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

from Events.Utils       import getActionTypeIdListByFlatCode
from Orgs.Utils         import getOrgStructureFullName
from library.Utils      import forceDate, forceInt, forceRef, forceString, isMKB, forceDateTime

from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable
from Reports.ReportView import CPageFormat
from Reports.StationaryF007 import getHospitalBedIdList, getLeaved, getMovingTransfer, getReceived
from Reports.StationaryF007DS import getReceived as getReceivedDS, getLeaved as getLeavedDS, getMovingTransfer as getMovingTransferDS
from Reports.Utils      import dateRangeAsStr, getMovingDays, getPropertyAPHBP, getStringProperty, updateLIKE



from Ui_StationaryF30Setup import Ui_StationaryF30SetupDialog


MainRows = [
          ( u'1', u'Из числа выписанных (гр. 9) переведено в другие стационары'),
          ( u'2', u'обследовано серологически *) с целью выявления больных сифилисом'),
          ( u'3', u'Число выбывших больных (гр.9 +11) по ОМС'),
          ( u'4', u'по платным услугам включая ДМС'),
          ( u'5', u'из них по ДМС'),
          ( u'6', u'Проведено выбывшими больными койко-дней:  по ОМС'),
          ( u'7', u'по платным услугам  включая ДМС'),
          ( u'8', u'из них по ДМС'),
          ( u'9', u'Посещений к  врачам стационара на платной основе')
          ]


class CStationaryF30SetupDialog(QtGui.QDialog, Ui_StationaryF30SetupDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())
        self.cmbHospitalBedProfile.setTable('rbHospitalBedProfile', True)
        self.cmbFinance.setTable('rbFinance', True)
        self.cmbSocStatusType.setTable('vrbSocStatusType', True)


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtBegTime.setTime(params.get('begTime', QTime(9, 0, 0, 0)))
        self.edtTimeEdit.setTime(params.get('endTime', QTime(9, 0, 0, 0)))
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))
        self.cmbHospitalBedProfile.setValue(params.get('hospitalBedProfileId', None))
        self.cmbFinance.setValue(params.get('financeId', None))
        self.cmbSocStatusClass.setValue(params.get('socStatusClassId', None))
        self.cmbSocStatusType.setValue(params.get('socStatusTypeId', None))
        self.cmbSchedule.setCurrentIndex(params.get('bedsSchedule', 0))


    def params(self):
        def getPureHMTime(time):
            return QTime(time.hour(), time.minute())
        return dict(endDate              = self.edtEndDate.date(),
                    endTime              = getPureHMTime(self.edtTimeEdit.time()),
                    begDate              = self.edtBegDate.date(),
                    begTime              = getPureHMTime(self.edtBegTime.time()),
                    orgStructureId       = self.cmbOrgStructure.value(),
                    hospitalBedProfileId = self.cmbHospitalBedProfile.value(),
                    financeId = self.cmbFinance.value(),
                    socStatusClassId     = self.cmbSocStatusClass.value(),
                    socStatusTypeId      = self.cmbSocStatusType.value(),
                    bedsSchedule      = self.cmbSchedule.currentIndex()
                   )


    @pyqtSignature('int')
    def on_cmbSocStatusClass_currentIndexChanged(self, index):
        socStatusClassId = self.cmbSocStatusClass.value()
        filter = ('class_id=%d' % socStatusClassId) if socStatusClassId else ''
        self.cmbSocStatusType.setFilter(filter)


class CStationaryF30(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Листок учета движения больных и коечного фонда стационара')
        self.orientation = CPageFormat.Landscape
        self.stationaryF30SetupDialog = None
        self.clientDeath = 8


    def getSetupDialog(self, parent):
        result = CStationaryF30SetupDialog(parent)
        self.stationaryF30SetupDialog = result
        return result


    def getOrgStructureIdList(self, treeIndex):
        treeItem = treeIndex.internalPointer() if treeIndex.isValid() else None
        return treeItem.getItemIdList() if treeItem else []


    def dumpParams(self, cursor, params):
        description = []
        #eventOrder = params.get('eventOrder', 0)
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

        orgStructureId = params.get('orgStructureId', None)
        hospitalBedProfileId = params.get('hospitalBedProfileId', None)
        if orgStructureId:
            description.append(u'подразделение: ' + getOrgStructureFullName(orgStructureId))
        else:
            description.append(u'подразделение: ЛПУ')
        if hospitalBedProfileId:
            description.append(u'профиль койки: %s'%(forceString(QtGui.qApp.db.translate('rbHospitalBedProfile', 'id', hospitalBedProfileId, 'name'))))
        description.append(u'отчёт составлен: '+forceString(QDateTime.currentDateTime()))
        columns = [ ('100%', [], CReportBase.AlignLeft) ]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()


    def getCaption(self, cursor, params, title):
        orgStructureId = params.get('orgStructureId', None)
        underCaptionList = []
        if orgStructureId:
            underCaptionList.append(u'подразделение: ' + forceString(getOrgStructureFullName(orgStructureId)))
        else:
            underCaptionList.append(u'подразделение: ЛПУ')
        hospitalBedProfileId = params.get('hospitalBedProfileId', None)
        if hospitalBedProfileId:
            underCaptionList.append(u'профиль койки: %s'%(forceString(QtGui.qApp.db.translate('rbHospitalBedProfile', 'id', hospitalBedProfileId, 'name'))))
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        boldChars = QtGui.QTextCharFormat()
        boldChars.setFontWeight(QtGui.QFont.Bold)
        columns2 = [('100%', [], CReportBase.AlignCenter)]
        table2 = createTable(cursor, columns2, headerRowCount=3, border=0, cellPadding=2, cellSpacing=0)
        table2.setText(0, 0, u'Раздел III. ДЕЯТЕЛЬНОСТЬ СТАЦИОНАРА', charFormat=boldChars)
        table2.setText(1, 0, title, charFormat=boldChars)
        table2.setText(2, 0, u', '.join(underCaption for underCaption in underCaptionList if underCaption))
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()


class CStationaryF30Moving(CStationaryF30):
    def __init__(self, parent):
        CStationaryF30.__init__(self, parent)
        self.setTitle(u'1. Коечный фонд и его использование(3100)')


    def averageDaysHospitalBed(self, orgStructureIdList, begDatePeriod, endDatePeriod, bedsSchedule, profile = None, isHospital = None):
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
        if bedsSchedule:
            queryTable = queryTable.innerJoin(tableHBSchedule, tableOSHB['schedule_id'].eq(tableHBSchedule['id']))
        if bedsSchedule == 1:
            cond.append(tableHBSchedule['code'].eq(1))
        elif bedsSchedule == 2:
            cond.append(tableHBSchedule['code'].ne(1))
        if isHospital is not None:
           cond.append(tableOrg['isHospital'].eq(isHospital))
        joinAnd = db.joinAnd([tableOSHB['endDate'].isNull(), db.joinOr([db.joinAnd([tableOSHB['begDate'].isNotNull(), tableOSHB['begDate'].le(endDatePeriod)]), tableOSHB['begDate'].isNull()])])
        cond.append(db.joinOr([db.joinAnd([tableOSHB['endDate'].isNotNull(), tableOSHB['endDate'].ge(begDatePeriod), tableOSHB['begDate'].isNotNull(), tableOSHB['begDate'].le(endDatePeriod)]), joinAnd]))
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


    def build(self, params):
        db = QtGui.qApp.db
        tableOS = db.table('OrgStructure')
        tableOSHB = db.table('OrgStructure_HospitalBed')
        tableHBSchedule = db.table('rbHospitalBedShedule')
        tableRbHospitalBedProfile = db.table('rbHospitalBedProfile')
        tableContract = db.table('Contract')
        tablerbFinance = db.table('rbFinance')
        endDate = params.get('endDate', QDate())
        begDate = params.get('begDate', QDate())
        financeId = params.get('financeId', None)
        if not endDate:
            endDate = QDate.currentDate()
        if endDate:
            endTime = params.get('endTime', QTime(9, 0, 0, 0))
            begTime = params.get('begTime', None)
            endDateTime = QDateTime(endDate, endTime)
            self.MKBRange = None  # (MKBFrom, MKBTo)
            if not begDate:
                begTime = begTime if begTime else endTime
                begDateTime = QDateTime(endDate.addDays(-1), begTime)
            else:
                begTime = begTime if begTime else endTime
                begDateTime = QDateTime(begDate, begTime)
                
            self.ageCond = u'IF(Client.sex = 1, age(Client.birthDate, IF(Action.endDate IS NOT NULL, Action.endDate, %s))>=60, IF(Client.sex = 2, age(Client.birthDate, IF(Action.endDate IS NOT NULL, Action.endDate, %s))>=55, 0))'%(db.formatDate(endDateTime), db.formatDate(endDateTime))
            bedsSchedule = params.get('bedsSchedule', 0)
            hospitalBedProfileId = params.get('hospitalBedProfileId', None)
            noProfileBed = params.get('noProfileBed', True)
            isPermanentBed = params.get('isPermanentBed', False)
            noPrintCaption = params.get('noPrintCaption', False)
            isGroupingOS = params.get('isGroupingOS', False)
            orgStructureIndex = self.stationaryF30SetupDialog.cmbOrgStructure._model.index(self.stationaryF30SetupDialog.cmbOrgStructure.currentIndex(), 0, self.stationaryF30SetupDialog.cmbOrgStructure.rootModelIndex())
            begOrgStructureIdList = self.getOrgStructureIdList(orgStructureIndex)

            doc = QtGui.QTextDocument()
            cursor = QtGui.QTextCursor(doc)
            cursor.setCharFormat(CReportBase.ReportTitle)
            cursor.insertBlock()
            if not noPrintCaption:
                self.getCaption(cursor, params, u'СВОДНАЯ ВЕДОМОСТЬ учета движения больных и коечного фонда по стационару, отделению или профилю коек за период')
            else:
                cursor.insertText(self.title())
            cursor.insertBlock()
            self.dumpParams(cursor, params)
            cursor.setCharFormat(CReportBase.ReportBody)
            cursor.insertBlock()
            cols = [('6%', [u'№ строки', u'', u'', u'', u'1'], CReportBase.AlignLeft),
                    ('10%', [u'Профиль коек', u'', u'', u'', u'2'], CReportBase.AlignLeft),
                    ('6%', [u'Число коек, фактически развернутых и свернутых на ремонт', u'на конец отчетного года', u'', u'', u'3'], CReportBase.AlignLeft),
                    ('6%', [u'', u'расположенных в сельской местности', u'', u'', u'4'], CReportBase.AlignLeft),
                    ('6%', [u'', u'среднегодовых', u'', u'', u'5'], CReportBase.AlignLeft),
                    ('6%', [u'В отчетном году', u'поступило больных - всего', u'', u'', u'6'], CReportBase.AlignLeft),
                    ('6%', [u'', u'из них сельских жителей', u'', u'', u'7'], CReportBase.AlignLeft),
                    ('6%', [u'', u'из общего числа поступивших (из гр.5)', u'0–17 лет (включительно)', u'', u'8'], CReportBase.AlignLeft),
                    ('6%', [u'', u'', u'старше трудоспособного возраста', u'', u'9'], CReportBase.AlignLeft),
                    ('6%', [u'', u'выписано больных', u'всего', u'', u'10'], CReportBase.AlignLeft),
                    ('6%', [u'', u'', u'в том числе старше  трудоспособного возраста', u'', u'11'], CReportBase.AlignLeft),
                    ('6%', [u'', u'из них в дневные стационары(всех типов)', u'', u'', u'12'], CReportBase.AlignLeft),
                    ('6%', [u'', u'Умерло', u'всего', u'', u'13'], CReportBase.AlignLeft),
                    ('6%', [u'', u'', u'в том числе старше трудоспособного возраста', u'', u'14'], CReportBase.AlignLeft),
                    ('6%', [u'Проведено больными койко-дней', u'всего', u'', u'', u'15'], CReportBase.AlignLeft),
                    ('6%', [u'', u'в том числе старше трудоспособного возраста', u'', u'', u'16'], CReportBase.AlignLeft),
                    ('6%', [u'Койко-дни закрытия на ремонт', u'', u'', u'', u'17'], CReportBase.AlignLeft)
                   ]
            table = createTable(cursor, cols)
            table.mergeCells(0, 0, 4, 1)
            table.mergeCells(0, 1, 4, 1)
            table.mergeCells(0, 2, 1, 3)
            table.mergeCells(1, 2, 3, 1)
            table.mergeCells(1, 3, 3, 1)#вставка
            table.mergeCells(1, 4, 3, 1)#среднегод

            table.mergeCells(0, 5, 1, 9)#15в отчетном году
            table.mergeCells(0, 14, 1, 2)#15проведено
            table.mergeCells(1, 5, 3, 1)#5поступило
            table.mergeCells(1, 6, 3, 1)#7из них сельск
            table.mergeCells(0, 16, 4, 1)#15койкодни
            table.mergeCells(1, 7, 1, 2)#7из общего числа
            table.mergeCells(2, 7, 2, 1)#0-17
            table.mergeCells(2, 8, 2, 1)#старше
            table.mergeCells(1, 9, 1, 2)#9выписано
            table.mergeCells(2, 9, 2, 1)#всего
            table.mergeCells(2, 10, 2, 1)#10 в том числе
            table.mergeCells(1, 11, 3, 1)#11 из них
            table.mergeCells(1, 12, 1, 2)#12 умерло
            table.mergeCells(2, 12, 2, 1)
            table.mergeCells(2, 13, 2, 1)
            table.mergeCells(1, 14, 3, 1)#15всего
            table.mergeCells(1, 15, 3, 1)

            self.countselhoz = 0
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
            self.countLeavedSUM1 = 0
            self.leavedDeathSUM1 = 0
            self.countStationaryDaySUM = 0
            self.presentAllSUM = 0
            self.clientRuralSUM = 0
            self.presentPatronagSUM = 0
            self.bedsAllSUM = 0
            self.bedsMenSUM = 0
            self.bedsWomenSUM = 0
            self.monthBed = 0
            self.involuteBedsSUM = 0

            def getHospitalBedId(orgStructureIdList):
                tableVHospitalBed = db.table('vHospitalBed')
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
                joinOr1 = db.joinAnd([tableVHospitalBed['begDate'].isNotNull(), tableVHospitalBed['endDate'].isNotNull(),
                tableVHospitalBed['begDate'].lt(endDateTime), tableVHospitalBed['endDate'].gt(begDateTime)])
                joinOr2 = db.joinOr([tableVHospitalBed['begDate'].isNull(), tableVHospitalBed['begDate'].lt(endDateTime)])
                joinOr3 = db.joinOr([tableVHospitalBed['endDate'].isNull(), tableVHospitalBed['endDate'].le(begDateTime)])
                cond.append(db.joinOr([joinOr1, joinOr2, joinOr3]))
                return db.getDistinctIdList(tableVHospitalBedSchedule, [tableVHospitalBed['id']], cond)

            def averageYarHospitalBed(orgStructureIdList, table, begDate, endDate, groupOS, profile = None, row = None, sumRowProfile = None, isHospital = None):
                days = 0
                daysMonths = 0
                period = begDate.daysTo(endDate)
                days = self.averageDaysHospitalBed(orgStructureIdList, begDate, endDate, bedsSchedule, profile, isHospital)
                daysMonths += days / (period if period > 0 else 1)
                table.setText(row if row else sumRowProfile, 4, daysMonths)
                if groupOS:
                    self.monthBed += daysMonths

            def getHospitalBedProfile(orgStructureIdList):
                cond = []
                profileIdList = []
                self.hospitalBedIdList = []
                if orgStructureIdList:
                    cond.append(tableOSHB['master_id'].inlist(orgStructureIdList))
                if QtGui.qApp.defaultHospitalBedProfileByMoving():
                    self.hospitalBedIdList = getHospitalBedId(orgStructureIdList)
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
    AND (APT.`typeName` = 'HospitalBed') AND (APHB.`value` IN (%s)))'''%(u','.join(str(hospitalBedId) for hospitalBedId in self.hospitalBedIdList if hospitalBedId)))
                    records = db.getRecordList(queryTable, [tableRbHospitalBedProfile['id'], tableRbHospitalBedProfile['code'], tableRbHospitalBedProfile['name']], cond)
                    for record in records:
                        profileId = forceRef(record.value('id'))
                        if profileId not in profileIdList:
                            profileIdList.append(profileId)
                else:
                    if not noProfileBed:
                        cond.append('OrgStructure_HospitalBed.profile_id IS NOT NULL')
                    queryTable = tableOSHB.innerJoin(tableRbHospitalBedProfile, tableOSHB['profile_id'].eq(tableRbHospitalBedProfile['id']))
                    queryTable = queryTable.innerJoin(tableOS,  tableOSHB['master_id'].eq(tableOS['id']))
                    cond.append(tableOS['deleted'].eq(0))
                    if bedsSchedule:
                        queryTable = queryTable.innerJoin(tableHBSchedule, tableOSHB['schedule_id'].eq(tableHBSchedule['id']))
                        if bedsSchedule == 1:
                            cond.append(tableHBSchedule['code'].eq(1))
                        elif bedsSchedule == 2:
                            cond.append(tableHBSchedule['code'].ne(1))
                    if hospitalBedProfileId:
                        cond.append(tableRbHospitalBedProfile['id'].eq(hospitalBedProfileId))
                    profileIdList = db.getDistinctIdList(queryTable, [tableRbHospitalBedProfile['id']], cond)
                if not profileIdList:
                    return None
                if noProfileBed:
                    profileIdList.append(None)
                return profileIdList

            def getDataReport(parOrgStructureIdList, rowProfile, table, sumRowProfile, groupOS, profileIdList, osType = None):
                db = QtGui.qApp.db
                tableAPT = db.table('ActionPropertyType')
                tableAP = db.table('ActionProperty')
                tableActionType = db.table('ActionType')
                tableAction = db.table('Action')
                tableEvent = db.table('Event')
                tableContract = db.table('Contract')
                tablerbFinance = db.table('rbFinance')
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

                def unrolledHospitalBed34(profile = None, row = None, groupOS = False):
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
                        if orgStructureIdList:
                            condRepairs.append(tableVHospitalBed['master_id'].inlist(orgStructureIdList))
                        if self.hospitalBedIdList:
                            getBedForProfile(noProfileBed, profile, self.hospitalBedIdList, True, row, 1, groupOS)
                        else:
                            table.setText(row if row else sumRowProfile, 2, 0)
                            if groupOS:
                                table.setText(rowProfile, 2, 0)
                    else:
                        cond = []
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
                        joinOr1 = db.joinAnd([tableVHospitalBed['begDate'].isNotNull(), tableVHospitalBed['endDate'].isNotNull(),
                        tableVHospitalBed['begDate'].le(endDateTime), db.joinAnd([tableVHospitalBed['endDate'].ge(begDateTime), db.joinOr([tableVHospitalBed['endDate'].ge(endDateTime), tableVHospitalBed['endDate'].eq(endDateTime)])])])
                        joinOr2 = db.joinOr([tableVHospitalBed['begDate'].isNull(), tableVHospitalBed['begDate'].le(endDateTime)])
                        joinOr3 = db.joinOr([tableVHospitalBed['endDate'].isNull(), db.joinAnd([tableVHospitalBed['endDate'].ge(begDateTime), db.joinOr([tableVHospitalBed['endDate'].ge(endDateTime), tableVHospitalBed['endDate'].eq(endDateTime)])])])
                        cond.append(db.joinOr([joinOr1, db.joinAnd([joinOr2, joinOr3])]))
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
                           table.setText(row, 2, self.countBeds)
                        else:
                            table.setText(sumRowProfile, 2, self.countBeds)
                            if groupOS:
                                self.countBedsAll += self.countBeds
                                self.countBedsRepairsAll += countBedsRepairs

                def getMovingPresent(profile = None, flagCurrent = False):
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
                    queryTable = queryTable.innerJoin(tableContract, tableEvent['contract_id'].eq(tableContract['id']))
                    queryTable = queryTable.innerJoin(tablerbFinance, tablerbFinance['id'].eq(tableContract['finance_id']))
                    queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
                    queryTable = queryTable.innerJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
                    queryTable = queryTable.innerJoin(tableAP, tableAP['type_id'].eq(tableAPT['id']))
                    queryTable = queryTable.innerJoin(tableAPHB, tableAPHB['id'].eq(tableAP['id']))
                    queryTable = queryTable.innerJoin(tableOSHB, tableOSHB['id'].eq(tableAPHB['value']))
                    queryTable = queryTable.innerJoin(tableOS, tableOS['id'].eq(tableOSHB['master_id']))
                    cond.append(tableOS['deleted'].eq(0))
                    cond.append(tableAPT['typeName'].like('HospitalBed'))
                    if self.MKBRange:
                        cond.append(isMKB(self.MKBRange[0], self.MKBRange[1]))
                    if orgStructureIdList:
                        cond.append(tableOSHB['master_id'].inlist(orgStructureIdList))
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

                def presentBegDay(profile = None, row = None, groupOS = False):
                    if row:
                        table.setText(row, 5, getMovingPresent(profile))
                    else:
                        movingPresent = getMovingPresent(profile)
                        table.setText(sumRowProfile, 5, movingPresent)
                        if groupOS:
                            self.movingPresentAll += movingPresent
                # из других отделений
                def fromMovingTransfer(profile = None, row = None, groupOS = False):
                    def getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile = None, transferIn = False, orgStructureIdList = [], boolFIO = False):
                        result = 0
                        if osType:
                            result = getMovingTransfer(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, transferIn, orgStructureIdList, boolFIO)
                        elif osType == 0:
                            result = getMovingTransferDS(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, transferIn, orgStructureIdList, boolFIO)
                        else:
                            if bedsSchedule != 2:
                                result = getMovingTransfer(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, transferIn, orgStructureIdList, boolFIO)
                            if bedsSchedule != 1:
                                result += getMovingTransferDS(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, transferIn, orgStructureIdList, boolFIO)
                        return result
                    if row:
                        table.setText(row, 13, getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен из отделения', profile, False, orgStructureIdList))
                    else:
                        movingTransfer = getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен из отделения', profile, False, orgStructureIdList)
                        table.setText(sumRowProfile, 13, movingTransfer)
                        if groupOS:
                            self.movingTransferAll += movingTransfer

                def receivedAll(profile = None, row = None, groupOS = False):
                    def getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty = u'Переведен из отделения', profile = None, orgStructureIdList = [], boolFIO = False, noPropertyProfile = False, additionalCond = None):
                        result1 = result2 = [0, 0, 0, 0, 0, 0, 0]
                        if bedsSchedule != 2:
                            result1 = getReceived(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, orgStructureIdList, boolFIO, noPropertyProfile, additionalCond=additionalCond)
                        if bedsSchedule != 1:
                            result2 = getReceivedDS(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, orgStructureIdList, boolFIO, noPropertyProfile, additionalCond=additionalCond)
                        return list(map(lambda x, y: (x or 0) + (y or 0), result1, result2))
                    extraCond = (isMKB(self.MKBRange[0], self.MKBRange[1]) if self.MKBRange else None)
                    self.receivedBedsAll = 0
                    if osType:
                        getR = getReceived
                    elif osType == 0:
                        getR = getReceivedDS
                    else:
                        getR = getFunc
                    if row:
                        receivedInfo = getR(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен из отделения', profile, orgStructureIdList, additionalCond=extraCond)
                        receivedBedAll = receivedInfo[5]
                        childrenCount = receivedInfo[1]
                        adultCount = receivedInfo[2]
                        clientRural = receivedInfo[3]
                        isStationaryDay = receivedInfo[4]
                        orderExtren = receivedInfo[6]
                        countAll = receivedInfo[0]
                        if noProfileBed and not profile:
                            receivedInfoNoProfile = getR(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен из отделения', profile, orgStructureIdList, False, True, additionalCond=extraCond)
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
                        table.setText(row, 5,  countAll)
                        table.setText(row, 6,  clientRural)
                        table.setText(row, 7, childrenCount)
                        table.setText(row, 8, adultCount)
                    else:
                        receivedInfo = getR(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен из отделения', profile, orgStructureIdList, additionalCond=extraCond)
                        receivedBedAll = receivedInfo[5]
                        childrenCount = receivedInfo[1]
                        adultCount = receivedInfo[2]
                        clientRural = receivedInfo[3]
                        isStationaryDay = receivedInfo[4]
                        orderExtren = receivedInfo[6]
                        countAll = receivedInfo[0]
                        if noProfileBed:
                            receivedInfoNoProfile = getR(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен из отделения', profile, orgStructureIdList, False, True, additionalCond=extraCond)
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
                        table.setText(sumRowProfile, 5,  countAll)
                        table.setText(sumRowProfile, 6,  clientRural)
                        table.setText(sumRowProfile, 7, childrenCount)
                        table.setText(sumRowProfile, 8, adultCount)
                        if groupOS:
                            self.receivedBedsAllSUM += self.receivedBedsAll
                            self.receivedInfo6 += orderExtren
                            self.receivedInfo0 += countAll
                            self.receivedInfo4 += isStationaryDay
                            self.receivedInfo3 += clientRural
                            self.receivedInfo1 += childrenCount
                            self.receivedInfo2 += adultCount

                # в другие отделения
                def inMovingTransfer(profile = None, row = None, groupOS = False):
                    def getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile = None, transferIn = False, orgStructureIdList = [], boolFIO = False, additionalCond = None):
                        result = 0
                        if osType:
                            result = getMovingTransfer(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, transferIn, orgStructureIdList, boolFIO, additionalCond=additionalCond)
                        elif osType == 0:
                            result = getMovingTransferDS(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, transferIn, orgStructureIdList, boolFIO, additionalCond=additionalCond)
                        else:
                            if bedsSchedule != 2:
                                result = getMovingTransfer(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, transferIn, orgStructureIdList, boolFIO, additionalCond=additionalCond)
                            if bedsSchedule != 1:
                                result += getMovingTransferDS(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, transferIn, orgStructureIdList, boolFIO, additionalCond=additionalCond)
                        return result

                    extraCond = (isMKB(self.MKBRange[0], self.MKBRange[1]) if self.MKBRange else None)
                    if row:
                        table.setText(row, 13, getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен в отделение', profile, True, orgStructureIdList))
                    else:
                        inMovingTransfer = getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен в отделение', profile, True, orgStructureIdList, additionalCond=extraCond)
                        table.setText(sumRowProfile, 13, inMovingTransfer)
                        if groupOS:
                            self.inMovingTransferAll += inMovingTransfer

                def leavedAll(profile = None, row = None, groupOS = False):
                    def getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty = u'Переведен в отделение', profile = None, orgStructureIdList = [], boolFIO = False, noPropertyProfile = False, profileCode = False, additionalCond = None):
                        result1 = result2 = [0, 0, 0, 0, 0]
                        type = u' in (0,1)'
                        ageFor = False
                        ageTo = False
                        if osType:
                            result1 = getLeaved(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, orgStructureIdList, boolFIO, noPropertyProfile, profileCode, additionalCond, ageFor, ageTo, type, financeId)
                        else:
                            result1 = getLeaved(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, orgStructureIdList, boolFIO, noPropertyProfile, profileCode, additionalCond, ageFor, ageTo, type, financeId)
                        return list(map(lambda x, y: (x or 0) + (y or 0), result1, result2))
                    extraCond = self.ageCond
                    onlyMKBCond = None
                    if self.MKBRange:
                        onlyMKBCond = isMKB(self.MKBRange[0], self.MKBRange[1])
                        extraCond += ' AND ' + onlyMKBCond
                    if row:
                        countLeavedAll, leavedDeath, leavedTransfer, countStationaryDay, leavedAdultCount, leavedotkaz = getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен в отделение', profile, orgStructureIdList)
                        countLeavedAll1, leavedDeath1, leavedTransfer1, countStationaryDay1, leavedAdultCount, leavedotkaz1 = getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен в отделение', profile, orgStructureIdList, additionalCond = self.ageCond)
                        if noProfileBed and not profile:
                            countLeavedAllNoProfile, leavedDeathNoProfile, leavedTransferNoProfile, countStationaryDayNoProfile, leavedAdultCountNoProfile, leavedotkazNoProfile = getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен в отделение', profile, orgStructureIdList, False, True)
                            countLeavedAllNoProfile1, leavedDeathNoProfile1, leavedTransferNoProfile1, countStationaryDayNoProfile1, leavedAdultCountNoProfile1, leavedotkazNoProfile1 = getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен в отделение', profile, orgStructureIdList, False, True, additionalCond = self.ageCond)
                            leavedDeath += leavedDeathNoProfile
                            leavedTransfer += leavedTransferNoProfile
                            countStationaryDay += countStationaryDayNoProfile
                            leavedDeath1 += leavedDeathNoProfile1
                            leavedTransfer1 += leavedTransferNoProfile1
                            countStationaryDay1 += countStationaryDayNoProfile1
                            countLeavedAll += countLeavedAllNoProfile-leavedDeath-leavedotkaz-leavedotkazNoProfile
                            countLeavedAll1 += countLeavedAllNoProfile1-leavedDeath1-leavedotkaz1-leavedotkazNoProfile1
                        table.setText(row, 9, countLeavedAll)
                        table.setText(row, 10, countLeavedAll1)
                        table.setText(row, 11, countStationaryDay)
                        table.setText(row, 12, leavedDeath)
                        table.setText(row, 13, leavedDeath1)
                    else:
                        countLeavedAll, leavedDeath, leavedTransfer, countStationaryDay, leavedAdultCount, leavedotkaz = getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен в отделение', profile, orgStructureIdList)
                        countLeavedAll1, leavedDeath1, leavedTransfer1, countStationaryDay1, leavedAdultCount, leavedotkaz1 = getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен в отделение', profile, orgStructureIdList, additionalCond = self.ageCond)
                        if noProfileBed and not profile:
                            countLeavedAllNoProfile, leavedDeathNoProfile, leavedTransferNoProfile, countStationaryDayNoProfile, leavedAdultCountNoProfile, leavedotkazNoProfile = getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен в отделение', profile, orgStructureIdList, False, True)
                            countLeavedAllNoProfile1, leavedDeathNoProfile1, leavedTransferNoProfile1, countStationaryDayNoProfile1, leavedAdultCountNoProfile1, leavedotkazNoProfile1 = getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен в отделение', profile, orgStructureIdList, False, True, additionalCond = self.ageCond)
                            leavedDeath += leavedDeathNoProfile
                            leavedTransfer += leavedTransferNoProfile
                            countStationaryDay += countStationaryDayNoProfile
                            leavedDeath1 += leavedDeathNoProfile1
                            leavedTransfer1 += leavedTransferNoProfile1
                            countStationaryDay1 += countStationaryDayNoProfile1
                            countLeavedAll += countLeavedAllNoProfile - leavedDeath - leavedotkaz - leavedotkazNoProfile
                            countLeavedAll1 += countLeavedAllNoProfile1 - leavedDeath1 - leavedotkaz1 - leavedotkazNoProfile1
                        table.setText(sumRowProfile, 9, countLeavedAll)
                        table.setText(sumRowProfile, 10, countLeavedAll1)
                        table.setText(sumRowProfile, 11, countStationaryDay)
                        table.setText(sumRowProfile, 12, leavedDeath)
                        table.setText(sumRowProfile, 13, leavedDeath1)
                        if groupOS:
                            self.countLeavedSUM += countLeavedAll-leavedDeath
                            self.countLeavedSUM1 += countLeavedAll1-leavedDeath1
                            self.leavedDeathSUM += leavedDeath
                            self.leavedDeathSUM1 += leavedDeath1
                            self.countStationaryDaySUM += countStationaryDay

                def presentEndDay(profile = None, row = None, groupOS = False):
                    self.presentAll = 0
                    if row:
                        self.presentAll, presentPatronag, clientRural = getMovingPresent(profile, True)
                        table.setText(row, 17, self.presentAll)
                    else:
                        self.presentAll, presentPatronag, clientRural = getMovingPresent(profile, True)
                        table.setText(sumRowProfile, 17, self.presentAll)
                        if groupOS:
                            self.presentAllSUM += self.presentAll
                            self.clientRuralSUM += clientRural
                            self.presentPatronagSUM += presentPatronag

                #Всего коек пустых
                def freelyHospitalBedAll(profile = None, row = None, groupOS = False):
                    bedIdList = getHospitalBedIdList(isPermanentBed, begDateTime, endDateTime, orgStructureIdList)
                    tableVHospitalBedSchedule = tableVHospitalBed.innerJoin(tableOS,  tableVHospitalBed['master_id'].eq(tableOS['id']))
                    cond = []
                    cond.append(tableOS['deleted'].eq(0))
                    if bedIdList:
                        cond.append(tableVHospitalBed['id'].notInlist(bedIdList))
                    if orgStructureIdList:
                        cond.append(tableVHospitalBed['master_id'].inlist(orgStructureIdList))
                    if not noProfileBed:
                        cond.append('vHospitalBed.profile_id IS NOT NULL')
                    if profile:
                        if QtGui.qApp.defaultHospitalBedProfileByMoving():
                            profileIdListNoBusi = getBedForProfile(noProfileBed, profile, self.hospitalBedIdList, False, None, None, groupOS)
                            cond.append(tableVHospitalBed['profile_id'].inlist(profileIdListNoBusi))
                        else:
                            if noProfileBed and len(profile) > 1:
                                cond.append(db.joinOr([tableVHospitalBed['profile_id'].inlist(profile), tableVHospitalBed['profile_id'].isNull()]))
                            else:
                                cond.append(tableVHospitalBed['profile_id'].inlist(profile))
                    else:
                        if QtGui.qApp.defaultHospitalBedProfileByMoving():
                            profileIdListNoBusi = getBedForProfile(noProfileBed, [], self.hospitalBedIdList, False, None, None, groupOS)
                            cond.append(tableVHospitalBed['profile_id'].inlist(profileIdListNoBusi))
                        else:
                            cond.append(tableVHospitalBed['profile_id'].isNull())
                    if bedsSchedule:
                        tableVHospitalBedSchedule = tableVHospitalBedSchedule.innerJoin(tableHBSchedule, tableVHospitalBed['schedule_id'].eq(tableHBSchedule['id']))
                    if bedsSchedule == 1:
                        cond.append(tableHBSchedule['code'].eq(1))
                    elif bedsSchedule == 2:
                        cond.append(tableHBSchedule['code'].ne(1))
                    stmt = db.selectStmt(tableVHospitalBedSchedule, u'COUNT(vHospitalBed.id) AS bedsAll, SUM(IF(vHospitalBed.sex = 1, 1, 0)) AS bedsMen, SUM(IF(vHospitalBed.sex = 2, 1, 0)) AS bedsWomen', where=cond)
                    query = db.query(stmt)
                    if query.first():
                        record = query.record()
                        bedsAll = self.countBeds - self.presentAll
                        bedsMen = forceInt(record.value('bedsMen'))
                        bedsWomen = forceInt(record.value('bedsWomen'))
                    else:
                        bedsAll = 0 - self.presentAll
                        bedsMen = 0
                        bedsWomen = 0
                    if row:
                        table.setText(row, 20, bedsAll)
                        table.setText(row, 21, bedsMen)
                        table.setText(row, 22, bedsWomen)
                    else:
                        table.setText(sumRowProfile, 20, bedsAll)
                        table.setText(sumRowProfile, 21, bedsMen)
                        table.setText(sumRowProfile, 22, bedsWomen)
                        if groupOS:
                            self.bedsAllSUM += bedsAll
                            self.bedsMenSUM += bedsMen
                            self.bedsWomenSUM += bedsWomen

                def involuteBedDays(profileIdList = None, row = None, groupOS = False):
                    tableOSHBI = db.table('OrgStructure_HospitalBed_Involution').alias('OSHBI')
                    dbTable = tableOSHB.innerJoin(tableOSHBI, tableOSHBI['master_id'].eq(tableOSHB['id']))
                    cond = [
                        tableOSHB['profile_id'].inlist(profileIdList),
                        tableOSHB['master_id'].inlist(orgStructureIdList),
                        tableOSHBI['begDate'].lt(endDateTime.addDays(1)),
                        tableOSHBI['endDate'].ge(begDateTime)
                    ]
                    recordList = db.getRecordList(dbTable, 'OSHBI.begDate,OSHBI.endDate', cond)
                    days = 0
                    for record in recordList:
                        begDate = forceDate(record.value('begDate'))
                        endDate = forceDate(record.value('endDate'))
                        if begDate < begDateTime.date():
                            begDate = begDateTime.date()
                        if endDate > endDateTime.date():
                            endDate = endDateTime.date()
                        days += begDate.daysTo(endDate) + 1
                    if row:
                        table.setText(row, 16, days)
                    else:
                        table.setText(sumRowProfile, 16, days)
                        self.involuteBedsSUM += days

                extraCond = self.ageCond
                onlyMKBCond = None
                if self.MKBRange:
                    onlyMKBCond = isMKB(self.MKBRange[0], self.MKBRange[1])
                    extraCond += ' AND ' + onlyMKBCond

                numRow = 1
                table.setText(sumRowProfile, 0, numRow)
                numRow += 1
                unrolledHospitalBed34(profileIdList, None, groupOS)
                receivedAll(profileIdList, None, groupOS)
                leavedAll(profileIdList, None, groupOS)
                averageYarHospitalBed(orgStructureIdList, table, begDate, endDate, groupOS, profileIdList, None, sumRowProfile)
                table.setText(sumRowProfile, 14, getMovingDays(orgStructureIdList, begDateTime, endDateTime, profileIdList, bedsSchedule = bedsSchedule, financeEventId=financeId))
                table.setText(sumRowProfile, 15, getMovingDays(orgStructureIdList, begDateTime, endDateTime, profileIdList, bedsSchedule = bedsSchedule, additionalCond=self.ageCond, financeEventId=financeId))
                involuteBedDays(profileIdList, None, groupOS)
                if noProfileBed:
                    table.setText(rowProfile, 0, numRow)
                    numRow += 1
                    table.setText(rowProfile, 1, u'профиль койки не определен')
                    unrolledHospitalBed34([], rowProfile)
                    receivedAll([], rowProfile)
                    leavedAll([], rowProfile)
                    averageYarHospitalBed(orgStructureIdList, table, begDate, endDate, False, None, None, rowProfile)
                    table.setText(rowProfile, 14, getMovingDays(orgStructureIdList, begDateTime, endDateTime, None, bedsSchedule = bedsSchedule, financeEventId=financeId))
                    table.setText(rowProfile, 15, getMovingDays(orgStructureIdList, begDateTime, endDateTime, None, bedsSchedule = bedsSchedule, additionalCond=self.ageCond, financeEventId=financeId))
                    involuteBedDays([], rowProfile)
                cond = []
                queryTable = tableRbHospitalBedProfile
                if QtGui.qApp.defaultHospitalBedProfileByMoving():
                    if hospitalBedProfileId and (hospitalBedProfileId in profileIdList):
                        cond.append(tableRbHospitalBedProfile['id'].eq(hospitalBedProfileId))
                    elif not hospitalBedProfileId and profileIdList:
                        cond.append(tableRbHospitalBedProfile['id'].inlist(profileIdList))
                elif hospitalBedProfileId:
                    cond.append(tableRbHospitalBedProfile['id'].eq(hospitalBedProfileId))
                else:
                    cond.append(tableRbHospitalBedProfile['id'].inlist(profileIdList))
                stmt = db.selectDistinctStmt(queryTable, [tableRbHospitalBedProfile['id'], tableRbHospitalBedProfile['code'], tableRbHospitalBedProfile['name']], cond, u'rbHospitalBedProfile.code')
                query = db.query(stmt)
                sizeQuery = query.size()
                if noProfileBed:
                    if sizeQuery > 0:
                        rowProfile = table.addRow()
                sizeQuery -= 1
                while query.next():
                    numRow += 1
                    record = query.record()
                    profileId = forceRef(record.value('id'))
                    profileName = forceString(record.value('name'))
                    table.setText(rowProfile, 0, numRow)
                    table.setText(rowProfile, 1, profileName)
                    unrolledHospitalBed34([profileId], rowProfile)
                    receivedAll([profileId], rowProfile)
                    leavedAll([profileId], rowProfile)
                    averageYarHospitalBed(orgStructureIdList, table, begDate, endDate, False, [profileId], rowProfile, sumRowProfile)
                    table.setText(rowProfile, 14, getMovingDays(orgStructureIdList, begDateTime, endDateTime, [profileId], bedsSchedule = bedsSchedule, financeEventId=financeId))
                    table.setText(rowProfile, 15, getMovingDays(orgStructureIdList, begDateTime, endDateTime, [profileId], bedsSchedule = bedsSchedule, additionalCond=self.ageCond, financeEventId=financeId))
                    involuteBedDays([profileId], rowProfile)
                    if profileName == u'Инфекционные':
                        rowProfile = table.addRow()
                        table.setText(rowProfile, 0, '%d.1' % numRow)
                        table.setText(rowProfile, 1, u'из них для COVID-19')
                        self.MKBRange = ('U07.1', 'U07.2')
                        unrolledHospitalBed34([profileId], rowProfile)
                        receivedAll([profileId], rowProfile)
                        leavedAll([profileId], rowProfile)
                        averageYarHospitalBed(orgStructureIdList, table, begDate, endDate, False, [profileId], rowProfile, sumRowProfile)
                        table.setText(rowProfile, 13, getMovingDays(orgStructureIdList, begDateTime, endDateTime, [profileId], bedsSchedule = bedsSchedule, additionalCond=onlyMKBCond))
                        table.setText(rowProfile, 14, getMovingDays(orgStructureIdList, begDateTime, endDateTime, [profileId], bedsSchedule = bedsSchedule, additionalCond=extraCond))
                        involuteBedDays([profileId], rowProfile)
                        self.MKBRange = None
                    if sizeQuery > 0:
                        rowProfile = table.addRow()
                        sizeQuery -= 1
                return table.addRow() if sizeQuery > 0 else rowProfile

            boldChars = QtGui.QTextCharFormat()
            boldChars.setFontWeight(QtGui.QFont.Bold)
            def getOrgStructureParent(orgStructureIdList, rowProfile, table):
                for parentOrgStructureId in orgStructureIdList:
                    tableQuery = tableOS.innerJoin(tableOSHB, tableOSHB['master_id'].eq(tableOS['id']))
                    cond = [tableOS['deleted'].eq(0),
                                               tableOS['id'].eq(parentOrgStructureId)]
                    if hospitalBedProfileId:
                        cond.append(tableOSHB['profile_id'].eq(hospitalBedProfileId))
                    recordEx = db.getRecordEx(tableQuery,
                                              [tableOS['name'], tableOS['id'], tableOS['type']], cond)
                    if recordEx:
                        name = forceString(recordEx.value('name'))
                        osType = forceInt(recordEx.value('type'))
                        rowProfile = table.addRow()
                        table.setText(rowProfile, 0, name, boldChars)
                        sumRowProfile = rowProfile
                        rowProfile = table.addRow()
                        profileIdList = getHospitalBedProfile([parentOrgStructureId])
                        rowProfile = getDataReport([parentOrgStructureId], rowProfile, table, sumRowProfile, True, profileIdList, osType)
                        cond =  [tableOS['deleted'].eq(0),
                                                    tableOS['parent_id'].eq(parentOrgStructureId)]
                        if hospitalBedProfileId:
                            cond.append(tableOSHB['profile_id'].eq(hospitalBedProfileId))
                        records = db.getRecordList(tableQuery, [tableOS['id'], tableOS['name'], tableOS['type']], cond  )
                        for record in records:
                            name = forceString(record.value('name'))
                            orgStructureId = forceRef(record.value('id'))
                            osType = forceInt(record.value('type'))
                            table.setText(rowProfile, 0, name, boldChars)
                            sumRowProfile = rowProfile
                            rowProfile = table.addRow()
                            profileIdList = getHospitalBedProfile([orgStructureId])
                            rowProfile = getDataReport([orgStructureId], rowProfile, table, sumRowProfile, True, profileIdList, osType)
            nextRow = table.addRow()
            if isGroupingOS:
                getOrgStructureParent(begOrgStructureIdList, None, table)
                table.setText(nextRow, 1, u'Всего:\n', boldChars)
                table.setText(nextRow, 2, self.countBedsAll)
                #self.averageYarHospitalBed(begOrgStructureIdList, table, begDate, endDate, profile, nextRow)
                #table.setText(nextRow, 4, self.countBedsRepairsAll)
#                table.setText(nextRow, 2, self.monthBed)
#                table.setText(nextRow, 4, self.movingPresentAll)
                #table.setText(nextRow, 4, self.receivedBedsAllSUM)
                #сюда
                table.setText(nextRow, 4, self.monthBed)
                table.setText(nextRow, 5, self.receivedInfo0)
                table.setText(nextRow, 6, self.receivedInfo3)
                table.setText(nextRow, 7, self.receivedInfo1)
                table.setText(nextRow, 8, self.receivedInfo2)
                table.setText(nextRow, 9, self.countLeavedSUM)
                table.setText(nextRow, 10, self.countLeavedSUM1)
                table.setText(nextRow, 11, self.countStationaryDaySUM)
                table.setText(nextRow, 12, self.leavedDeathSUM)
                table.setText(nextRow, 13, self.leavedDeathSUM1)
                profileIdList = getHospitalBedProfile(begOrgStructureIdList)
                table.setText(nextRow, 14, getMovingDays(begOrgStructureIdList, begDateTime, endDateTime, profileIdList, bedsSchedule = bedsSchedule, financeEventId=financeId))
                table.setText(nextRow, 15, getMovingDays(begOrgStructureIdList, begDateTime, endDateTime, profileIdList, bedsSchedule = bedsSchedule, additionalCond=self.ageCond, financeEventId=financeId))
                table.setText(nextRow, 16, self.involuteBedsSUM)
            else:
                profileIdList = getHospitalBedProfile(begOrgStructureIdList)
                table.setText(nextRow, 1, u'Всего:\n', boldChars)
                getDataReport(begOrgStructureIdList, table.addRow(), table, nextRow, False, profileIdList)
        return doc


class CStationaryF30_3101(CStationaryF30):
    def __init__(self, parent):
        CStationaryF30.__init__(self, parent)
        self.setTitle(u'1. Коечный фонд и его использование(3101)')


    def getLeaved_3101(self, begDateTime, endDateTime, orgStructureIdList, nameProperty = u'Переведен в отделение', profile = None, socStatusClassId = None, socStatusTypeId = None):
        db = QtGui.qApp.db
        tableAPT = db.table('ActionPropertyType')
        tableAP = db.table('ActionProperty')
        tableActionType = db.table('ActionType')
        tableAction = db.table('Action')
        tableEvent = db.table('Event')
        tableClient = db.table('Client')
        tableContract = db.table('Contract')
        cond = [ tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode('leaved%')),
                 tableAction['deleted'].eq(0),
                 tableEvent['deleted'].eq(0),
                 tableAP['deleted'].eq(0),
                 tableActionType['deleted'].eq(0),
                 tableContract['deleted'].eq(0),
                 tableClient['deleted'].eq(0),
                 tableAP['action_id'].eq(tableAction['id']),
                 tableAction['begDate'].isNotNull()
               ]
        queryTable = tableActionType.innerJoin(tableAction, tableActionType['id'].eq(tableAction['actionType_id']))
        queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
        queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
        queryTable = queryTable.innerJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
        queryTable = queryTable.innerJoin(tableAP, tableAP['type_id'].eq(tableAPT['id']))
        queryTable = queryTable.innerJoin(tableContract, tableEvent['contract_id'].eq(tableContract['id']))
        cond.append('''%s'''%(getDataAPHBnoPropertyForLeaved(False, nameProperty, False, profile if profile else [], u' AND A.endDate IS NOT NULL', u'Отделение', orgStructureIdList)))
        cond.append(db.joinAnd([tableAction['begDate'].ge(begDateTime), tableAction['begDate'].le(endDateTime)]))
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
        financeStmt = '''(IF(Action.finance_id IS NOT NULL, (SELECT rbFinance.code FROM rbFinance WHERE rbFinance.id = Action.finance_id), NULL)) AS codeActionFinance,
        (IF(Contract.finance_id IS NOT NULL, (SELECT rbFinance.code FROM rbFinance WHERE rbFinance.id = Contract.finance_id), NULL)) AS codeContractFinance'''

        stmt = db.selectStmt(queryTable, u'distinct Event.id AS eventId, %s AS transfer, %s'
                             %(getStringProperty(u'Исход госпитализации', u'(APS.value LIKE \'%%переведен%%\')'),
                               financeStmt), where=cond)
        query = db.query(stmt)
        transferCount = 0
        codeFinanceOMCCount = 0
        codeFinanceDMCCount = 0
        codeFinancePayMentCount = 0
        eventIdList = []
        while query.next():
            record = query.record()
            transferCount += forceInt(record.value('transfer'))
            eventId = forceRef(record.value('eventId'))
            if eventId and eventId not in eventIdList:
                eventIdList.append(eventId)
            codeActionFinance = forceString(record.value('codeActionFinance'))
            if codeActionFinance:
                codeFinanceOMCCount += 1 if codeActionFinance == '2' else 0
                codeFinanceDMCCount += 1 if codeActionFinance == '3' else 0
                codeFinancePayMentCount += 1 if codeActionFinance == '4' else 0
            else:
                codeContractFinance = forceString(record.value('codeContractFinance'))
                if codeContractFinance:
                    codeFinanceOMCCount += 1 if codeContractFinance == '2' else 0
                    codeFinanceDMCCount += 1 if codeContractFinance == '3' else 0
                    codeFinancePayMentCount += 1 if codeContractFinance == '4' else 0
        return [transferCount, codeFinanceOMCCount, codeFinanceDMCCount, codeFinancePayMentCount, eventIdList]


    def dataMovingDays_3101(self, orgStructureIdList, begDatePeriod, endDatePeriod, eventIdList, profile = None, socStatusClassId = None, socStatusTypeId = None):
        codeFinanceOMCDays = 0
        codeFinanceDMCDays = 0
        codeFinancePayMentDays = 0
        if eventIdList:
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
            tableContract = db.table('Contract')
            queryTable = tableActionType.innerJoin(tableAction, tableActionType['id'].eq(tableAction['actionType_id']))
            queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.leftJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
            queryTable = queryTable.innerJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
            queryTable = queryTable.innerJoin(tableAP, tableAP['type_id'].eq(tableAPT['id']))
            queryTable = queryTable.innerJoin(tableAPHB, tableAPHB['id'].eq(tableAP['id']))
            queryTable = queryTable.innerJoin(tableOSHB, tableOSHB['id'].eq(tableAPHB['value']))
            queryTable = queryTable.innerJoin(tableOS, tableOS['id'].eq(tableOSHB['master_id']))
            queryTable = queryTable.innerJoin(tableOrg, tableOrg['id'].eq(tableOS['organisation_id']))
            queryTable = queryTable.innerJoin(tableContract, tableEvent['contract_id'].eq(tableContract['id']))
            cond = [tableAction['event_id'].inlist(eventIdList),
                    tableActionType['flatCode'].like('moving%'),
                    tableAction['deleted'].eq(0),
                    tableEvent['deleted'].eq(0),
                    tableAP['deleted'].eq(0),
                    tableActionType['deleted'].eq(0),
                    tableAPT['deleted'].eq(0),
                    tableOS['deleted'].eq(0),
                    tableOS['type'].ne(0),
                    tableClient['deleted'].eq(0),
                    tableOrg['deleted'].eq(0),
                    tableContract['deleted'].eq(0),
                    tableAPT['typeName'].like('HospitalBed'),
                    tableAP['action_id'].eq(tableAction['id'])
                   ]
            if profile:
               cond.append(tableOSHB['profile_id'].inlist(profile))
            cond.append(tableOSHB['master_id'].inlist(orgStructureIdList))
            joinAnd = db.joinAnd([tableAction['endDate'].isNull(), tableAction['begDate'].isNotNull(), tableAction['begDate'].lt(endDatePeriod)])
            cond.append(db.joinOr([db.joinAnd([tableAction['endDate'].isNotNull(), tableAction['endDate'].gt(begDatePeriod), tableAction['begDate'].isNotNull(), tableAction['begDate'].lt(endDatePeriod)]), joinAnd]))
            cols = [tableEvent['id'].alias('eventId'),
                    tableAction['id'].alias('actionId'),
                    tableAction['begDate'],
                    tableAction['endDate']
                    ]
            cols.append('''(IF(Action.finance_id IS NOT NULL, (SELECT rbFinance.code FROM rbFinance WHERE rbFinance.id = Action.finance_id), NULL)) AS codeActionFinance,
        (IF(Contract.finance_id IS NOT NULL, (SELECT rbFinance.code FROM rbFinance WHERE rbFinance.id = Contract.finance_id), NULL)) AS codeContractFinance'''
        )
            stmt = db.selectStmt(queryTable, cols, cond)
            query = db.query(stmt)
            actionIdList = []
            while query.next():
                record = query.record()
                actionId = forceRef(record.value('actionId'))
                codeActionFinance = forceString(record.value('codeActionFinance'))
                codeContractFinance = forceString(record.value('codeContractFinance'))
                if actionId not in actionIdList:
                    actionIdList.append(actionId)
                    begDate = forceDateTime(record.value('begDate'))
                    endDate = forceDateTime(record.value('endDate'))
                    if begDate < begDatePeriod:
                        begDate = begDatePeriod
                    if not endDate or endDate > endDatePeriod:
                        endDate = endDatePeriod
                    if begDate and endDate:
                        if codeActionFinance:
                            if codeActionFinance == '2':
                                if begDate == endDate:
                                    codeFinanceOMCDays += 1
                                else:
                                    codeFinanceOMCDays += begDate.daysTo(endDate)
                            elif codeActionFinance == '3':
                                if begDate == endDate:
                                    codeFinanceDMCDays += 1
                                else:
                                    codeFinanceDMCDays += begDate.daysTo(endDate)
                            elif codeActionFinance == '4':
                                if begDate == endDate:
                                    codeFinancePayMentDays += 1
                                else:
                                    codeFinancePayMentDays += begDate.daysTo(endDate)
                        else:
                            if codeContractFinance:
                                if codeContractFinance == '2':
                                    if begDate == endDate:
                                        codeFinanceOMCDays += 1
                                    else:
                                        codeFinanceOMCDays += begDate.daysTo(endDate)
                                elif codeContractFinance == '3':
                                    if begDate == endDate:
                                        codeFinanceDMCDays += 1
                                    else:
                                        codeFinanceDMCDays += begDate.daysTo(endDate)
                                elif codeContractFinance == '4':
                                    if begDate == endDate:
                                        codeFinancePayMentDays += 1
                                    else:
                                        codeFinancePayMentDays += begDate.daysTo(endDate)
        return codeFinanceOMCDays, codeFinanceDMCDays, codeFinancePayMentDays


    def getVisitStationary(self, orgStructureIdList, begDatePeriod, endDatePeriod, eventIdList, profile = None, socStatusClassId = None, socStatusTypeId = None):
        db = QtGui.qApp.db
        tableEventType = db.table('EventType')
        tableEvent = db.table('Event')
        tableClient = db.table('Client')
        tableAPT = db.table('ActionPropertyType')
        tableAP = db.table('ActionProperty')
        tableActionType = db.table('ActionType')
        tableAction = db.table('Action')
        tableOS = db.table('OrgStructure')
        tableAPHB = db.table('ActionProperty_HospitalBed')
        tableOSHB = db.table('OrgStructure_HospitalBed')
        tableVisit = db.table('Visit')
        tableRBFinance = db.table('rbFinance')

        queryTable = tableActionType.innerJoin(tableAction, tableActionType['id'].eq(tableAction['actionType_id']))
        queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
        queryTable = queryTable.leftJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
        queryTable = queryTable.innerJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
        queryTable = queryTable.innerJoin(tableAP, tableAP['type_id'].eq(tableAPT['id']))
        queryTable = queryTable.innerJoin(tableAPHB, tableAPHB['id'].eq(tableAP['id']))
        queryTable = queryTable.innerJoin(tableOSHB, tableOSHB['id'].eq(tableAPHB['value']))
        queryTable = queryTable.innerJoin(tableOS, tableOS['id'].eq(tableOSHB['master_id']))
        queryTable = queryTable.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
        queryTable = queryTable.innerJoin(tableVisit, tableVisit['event_id'].eq(tableEvent['id']))
        queryTable = queryTable.innerJoin(tableRBFinance, tableRBFinance['id'].eq(tableVisit['finance_id']))
        cond = [tableActionType['flatCode'].like('moving%'),
                tableAction['deleted'].eq(0),
                tableEvent['deleted'].eq(0),
                tableAP['deleted'].eq(0),
                tableActionType['deleted'].eq(0),
                tableAPT['deleted'].eq(0),
                tableOS['deleted'].eq(0),
                tableOS['type'].ne(0),
                tableClient['deleted'].eq(0),
                tableVisit['deleted'].eq(0),
                'DATE(Event.setDate) <= DATE(Visit.date)',
                tableAPT['typeName'].like('HospitalBed'),
                tableAP['action_id'].eq(tableAction['id']),
                tableRBFinance['code'].like(u'4')
               ]
        cond.append(u'''(EventType.medicalAidType_id IN (SELECT rbMedicalAidType.id from rbMedicalAidType where rbMedicalAidType.code IN (\'1\', \'2\', \'3\', \'7\')))''')
        if profile:
           cond.append(tableOSHB['profile_id'].inlist(profile))
        cond.append(tableOSHB['master_id'].inlist(orgStructureIdList))
        joinAnd = db.joinAnd([tableAction['endDate'].isNull(), tableAction['begDate'].isNotNull(), tableAction['begDate'].lt(endDatePeriod)])
        cond.append(db.joinOr([db.joinAnd([tableAction['endDate'].isNotNull(), tableAction['endDate'].gt(begDatePeriod), tableAction['begDate'].isNotNull(), tableAction['begDate'].lt(endDatePeriod)]), joinAnd]))
        stmt = db.selectStmt(queryTable, u'COUNT(Visit.id) AS visitCount', cond)
        query = db.query(stmt)
        if query.first():
            record = query.record()
            return forceInt(record.value('visitCount'))
        return 0


    def build(self, params):
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
                
            hospitalBedProfileId = params.get('hospitalBedProfileId', None)
            socStatusClassId = params.get('socStatusClassId', None)
            socStatusTypeId = params.get('socStatusTypeId', None)
            orgStructureIndex = self.stationaryF30SetupDialog.cmbOrgStructure._model.index(self.stationaryF30SetupDialog.cmbOrgStructure.currentIndex(), 0, self.stationaryF30SetupDialog.cmbOrgStructure.rootModelIndex())
            orgStructureIdList = self.getOrgStructureIdList(orgStructureIndex)
            doc = QtGui.QTextDocument()
            cursor = QtGui.QTextCursor(doc)
            cursor.setCharFormat(CReportBase.ReportTitle)
            cursor.insertBlock()
            self.getCaption(cursor, params, u'1. Коечный фонд и его использование(3101)')
            cursor.insertBlock()
            self.dumpParams(cursor, params)
            cursor.setCharFormat(CReportBase.ReportBody)
            cursor.insertBlock()
            cols = [('10%',[u'№ графы'], CReportBase.AlignLeft),
                    ('70%', [u'Строка'], CReportBase.AlignLeft),
                    ('20%', [u''], CReportBase.AlignLeft)
                   ]
            table = createTable(cursor, cols)
            leavedTransfer, codeFinanceOMCCount, codeFinanceDMCCount, codeFinancePayMentCount, eventIdList = self.getLeaved_3101(begDateTime, endDateTime, orgStructureIdList,u'Переведен в отделение', [hospitalBedProfileId] if hospitalBedProfileId else [], socStatusClassId, socStatusTypeId)
            codeFinanceOMCDays, codeFinanceDMCDays, codeFinancePayMentDays = self.dataMovingDays_3101(orgStructureIdList, begDateTime, endDateTime, eventIdList, [hospitalBedProfileId] if hospitalBedProfileId else [], socStatusClassId, socStatusTypeId)
            visitCount = self.getVisitStationary(orgStructureIdList, begDateTime, endDateTime, eventIdList, [hospitalBedProfileId] if hospitalBedProfileId else [], socStatusClassId, socStatusTypeId)
            for rows in MainRows:
                rowProfile = table.addRow()
                table.setText(rowProfile, 0, rows[0])
                table.setText(rowProfile, 1, rows[1])
            table.setText(1, 2, leavedTransfer)
            table.setText(2, 2, u'-')
            table.setText(3, 2, codeFinanceOMCCount)
            table.setText(4, 2, codeFinanceDMCCount + codeFinancePayMentCount)
            table.setText(5, 2, codeFinanceDMCCount)
            table.setText(6, 2, codeFinanceOMCDays)
            table.setText(7, 2, codeFinanceDMCDays + codeFinancePayMentDays)
            table.setText(8, 2, codeFinancePayMentDays)
            table.setText(9, 2, visitCount)
            cursor.movePosition(QtGui.QTextCursor.End)
            cursor.insertBlock()
            cursor.insertText(u'*) Исключая больных, выбывших с дермато-венерологических коек.')
            cursor.insertBlock()
        return doc


def getDataAPHBnoPropertyForLeaved(isPermanentBed, nameProperty, noProfileBed, profileList=[], endDate=u'', namePropertyStay=u'Отделение', orgStructureIdList=[], isMedical = None, bedsSchedule = None):
    strIsMedical = u''''''
    strIsMedicalJoin = u''''''
    strIsScheduleJoin = u''''''
    if isMedical is not None:
        strIsMedicalJoin += u''' INNER JOIN OrgStructure AS OS ON OSHB.master_id = OS.id INNER JOIN Organisation AS ORG ON OS.organisation_id = ORG.id'''
        strIsMedical += u''' AND OS.type != 0 AND ORG.isMedical = %d'''%(isMedical)
    strFilter = u''''''
    if profileList and not noProfileBed:
        if QtGui.qApp.defaultHospitalBedProfileByMoving():
            strFilter += u''' AND (''' + getPropertyAPHBP(profileList, noProfileBed) + u''')'''
        else:
            strFilter += u''' AND (OSHB.profile_id IN (%s)%s)'''%((','.join(forceString(profile) for profile in profileList if profile)), u' OR OSHB.profile_id IS NULL' if noProfileBed and len(profileList) > 1 else u'')
    elif noProfileBed:
        if QtGui.qApp.defaultHospitalBedProfileByMoving():
            strFilter += u''' AND EXISTS(''' + getPropertyAPHBPNoProfileF30() + u''')'''
        else:
            strFilter += u''' AND OSHB.profile_id IS NULL'''
    if bedsSchedule:
        strIsScheduleJoin += u''' INNER JOIN rbHospitalBedShedule AS HBS ON OSHB.schedule_id = HBS.id'''
    if bedsSchedule == 1:
        strFilter += u''' AND HBS.code = 1'''
    elif bedsSchedule == 2:
        strFilter += u''' AND HBS.code != 1'''

    return '''EXISTS(SELECT APHB.value
FROM ActionType AS AT
INNER JOIN Action AS A ON AT.id=A.actionType_id
INNER JOIN ActionPropertyType AS APT ON APT.actionType_id=AT.id
INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id
INNER JOIN ActionProperty_HospitalBed AS APHB ON APHB.id=AP.id
INNER JOIN OrgStructure_HospitalBed AS OSHB ON OSHB.id=APHB.value%s%s
WHERE A.event_id=Event.id%s%s AND A.deleted=0 AND APT.actionType_id=A.actionType_id
AND AP.action_id=A.id AND AP.deleted=0 AND APT.deleted=0
AND APT.typeName = 'HospitalBed'%s %s)'''%(strIsMedicalJoin, strIsScheduleJoin, strIsMedical, endDate, strFilter,
(u' AND %s'%getDataOrgStructureStayForLeaved(namePropertyStay, orgStructureIdList)) if orgStructureIdList else u'')


def getPropertyAPHBPNoProfileF30():
    return '''SELECT APHBP.value
FROM ActionPropertyType AS APT_Profile
LEFT JOIN ActionProperty AS AP_Profile ON AP_Profile.type_id=APT_Profile.id
LEFT JOIN ActionProperty_rbHospitalBedProfile AS APHBP ON APHBP.id=AP_Profile.id
LEFT JOIN rbHospitalBedProfile AS RBHBP ON RBHBP.id=APHBP.value
WHERE APT_Profile.actionType_id = Action.actionType_id
AND AP_Profile.action_id = Action.id
AND AP_Profile.deleted = 0
AND APT_Profile.deleted = 0
AND APT_Profile.typeName = 'rbHospitalBedProfile'
AND APHBP.value IS NULL'''


def getDataOrgStructureStayForLeaved(nameProperty, orgStructureIdList):
    orgStructureList = [u'NULL']
    for orgStructureId in orgStructureIdList:
        orgStructureList.append(forceString(orgStructureId))
    return '''EXISTS(SELECT APOS2.value
    FROM ActionPropertyType AS APT2
    INNER JOIN ActionProperty AS AP2 ON AP2.type_id=APT2.id
    INNER JOIN ActionProperty_OrgStructure AS APOS2 ON APOS2.id=AP2.id
    INNER JOIN OrgStructure AS OS2 ON OS2.id=APOS2.value
    WHERE APT2.actionType_id=Action.actionType_id AND AP2.action_id=Action.id AND APT2.deleted=0
    AND APT2.name %s AND OS2.type != 0 AND OS2.deleted=0
    AND APOS2.value %s)'''%(updateLIKE(nameProperty), u' IN ('+(','.join(orgStructureList))+')')

