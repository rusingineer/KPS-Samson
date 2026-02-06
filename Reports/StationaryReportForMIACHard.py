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
from PyQt4.QtCore import QDate, QDateTime, QTime

from library.Utils            import forceDate, forceInt, forceRef, forceString, getAgeRangeCond
from Events.Utils             import getActionTypeIdListByFlatCode
from Reports.ReportBase       import CReportBase, createTable
from Reports.ReportView       import CPageFormat
from Reports.StationaryF007   import CStationaryF007, getLeaved,getMovingTransfer, getReceived
from Reports.StationaryF007DS import getReceived as getReceivedDS, getLeaved as getLeavedDS, getMovingTransfer as getMovingTransferDS
from Reports.StationaryReportForMIAC import CStationaryReportForMIACSetupDialog, getOrgStructureTypeIdList
from Reports.Utils            import ( dateRangeAsStr,
                                       getAdultCount,
                                       getChildrenCount,
                                       getKladrClientDefaultCity,
                                       getMovingDays,
                                       getNoPropertyAPHBP,
                                       getOrgStructureProperty,
                                       getOrstructureHasHospitalBeds,
                                       getPropertyAPHBP,
                                       getSeniorsMovingDays,
                                       getStringProperty,
                                       getTheseAndChildrens,
                                     )


MainCodeAllKS = [ u'1',
                  u'2',
                  u'3',
                  u'4',
                  u'5',
                  u'6',
                  u'7',
                  u'8',
                  u'9',
                  u'10',
                  u'11',
                  u'12',
                  u'13',
                  u'14',
                  u'15',
                  u'16',
                  u'17',
                  u'18',
                  u'19',
                  u'20',
                  u'21',
                  u'22',
                  u'23',
                  u'24',
                  u'25',
                  u'26',
                  u'27',
                  u'28',
                  u'29',
                  u'30',
                  u'31',
                  u'32',
                  u'33',
                  u'34'
                  ]


MainCodePaymentAllKS = [ u'21',
                         u'22',
                         u'23',
                         u'24',
                         u'25',
                         u'26',
                         u'27',
                         u'28',
                         u'29',
                         u'30',
                         u'31',
                         u'32',
                         u'33',
                         u'34'
                        ]


MainCodeAllDS = [ u'34',
                  u'35',
                  u'36',
                  u'37',
                  u'38',
                  u'39',
                  u'40',
                  u'41',
                  u'42',
                  u'43',
                  u'44',
                  u'45',
                  u'46',
                  u'47',
                  u'48',
                  u'49',
                ]


MainCodePaymentAllDS = [ u'46',
                         u'47',
                         u'48',
                         u'49'
                        ]


MainCodeKS = [u'1',
              u'2',
              u'3',
              u'4',
              u'5',
              u'6',
              u'7',
              u'8',
              u'9',
              u'10',
              u'11',
              u'12',
              u'13',
              u'14',
              u'15',
              u'16',
              u'17',
              u'18',
              u'19',
              u'20',
              u'21',
              u'22',
              u'23',
              u'24',
              u'25',
              u'26',
              u'27',
              u'28',
              u'29',
              u'30',
              u'31',
              u'32',
              u'33',
              u'34'
              ]


MainCodePaymentKS = [u'21',
                     u'22',
                     u'23',
                     u'24',
                     u'25',
                     u'26',
                     u'27',
                     u'28',
                     u'29',
                     u'30',
                     u'31',
                     u'32',
                     u'33',
                     u'34'
                    ]


MainRowsALL = [
              ( u'ВСЕГО - круглосуточный стационар', 1, None, 1),
              ( u'Аллергологические для детей', 2, None, 1),
              ( u'Инфекционные для детей', 3, None, 1),
              ( u'Неврологические для детей', 4, None, 1),
              ( u'Оториноларингологические для детей', 5, None, 1),
              ( u'Офтальмологические для детей', 6, None, 1),
              ( u'Педиатрические соматические ', 7, None, 1),
              ( u'Пульмонологические для детей', 8, None, 1),
              ( u'Травматологические для детей', 9, None, 1),
              ( u'Ортопедические для детей', 10, None, 1),
              ( u'Урологические для детей', 11, None, 1),
              ( u'Уроандрологические для детей', 12, None, 1),
              ( u'Абдоминальная хирургия для взрослых', 13, None, 1),
              ( u'Хирургические для детей ', 14, None, 1),
              ( u'Нейрохирургические для детей', 15, None, 1),
              ( u'Торакальной хирургии для детей', 16, None, 1),
              ( u'Челюстно-лицевая хирургия для детей', 17, None, 1),
              ( u'Эндокринологические для детей', 18, None, 1),
              ( u'Реанимационные койки для детей (сверхсметные) ', 19, 4, 1),
              ( u'Из всех коек круглосуточного стационара - платные', 20, 4, 1),
              ( u'из платных для детей - аллергологические', 21, 4, 1),
              ( u'из платных для детей - инфекционные', 22, 4, 1),
              ( u'из платных для детей - неврологические', 23, 4, 1),
              ( u'из платных для детей - нейрохирургические', 24, 4, 1),
              ( u'из платных для детей - оториноларингологические', 25, 4, 1),
              ( u'из платных для детей - офтальмологические', 26, 4, 1),
              ( u'из платных для детей - педиатрические', 27, 4, 1),
              ( u'из платных для детей - пульмонологические', 28, 4, 1),
              ( u'из платных для детей - реанимационные (сверхсметные)', 29, 4, 1),
              ( u'из платных для детей - травматологические', 30, 4, 1),
              ( u'из платных для детей - хирургические', 31, 4, 1),
              ( u'из платных для детей - челюстно-лицевой хирургии', 32, 4, 1),
              ( u'из платных для детей - эндокринологические', 33, 4, 1),
              ( u'ВСЕГО - дневной стационар', 34, None, 0),
              ( u'койки дневного стационара для детей - неврологические Невр', 35, None, 0),
              ( u'койки дневного стационара для детей -офтальмологические Офт', 36, None, 0),
              ( u'койки дневного стационара для детей - педиатрические  Хозрасчетные и нехозрасчетн койки *Х/Педиа+Педиатр', 37, None, 0),
              ( u'койки дневного стационара для детей - хирургические Хозрасчетные и нехозрасчетн койки *Х/Хир+Хир', 38, None, 0),
              ( u'койки дневного стационара для детей - челюстно-лицевой хирургии ХирЧЛГ', 39, None, 0),
              ( u'койки дневного стационара для детей - эндокринологические Эндокр', 40, None, 0),
              ( u'койки дневного стационара для детей - реабилитационные соматические - всего', 41, None, 0),
              ( u'койки дневного стационара для детей - реабилитационные с заболеваниями ЦНС и органов чувств', 42, None, 0),
              ( u'койки дневного стационара для детей - реабилитационные с заболеваниями ОДА и ПНС', 43, None, 0),
              ( u'койки дневного стационара для детей - урологические - всего', 44, None, 0),
              ( u'койки дневного стационара для детей - уроандрологические', 45, None, 0),
              ( u'Из всех коек дневного стационара - платные хозрасчетные по всем отделениям *Х/Хир+*Х/Педиа', 46, 4, 0),
              ( u'Из коек дневного стационара - платные для детей Все профили коек с  типом финансирования Платно (rbFinance.id = 4)', 47, 4, 0),
              ( u'из коек дневного стационара для детей - платные хирургические  Хир тип финансирования Платно (rbFinance.id = 4)', 48, 4, 0),
              ( u'из коек дневного стационара для детей - платные педиатрические Педиатр+*Х/Педиа тип финансирования Платно (rbFinance.id = 4)', 49, 4, 0),
             ]


MainRowsKS = [
              ( u'ВСЕГО - круглосуточный стационар', 1, None, 1),
              ( u'Аллергологические для детей', 2, None, 1),
              ( u'Гинекологические для детей', 3, None, 1),
              ( u'Инфекционные для детей', 4, None, 1),
              ( u'Неврологические для детей', 5, None, 1),
              ( u'Онкологические для детей', 6, None, 1),
              ( u'Оториноларингологические для детей', 7, None, 1),
              ( u'Офтальмологические для детей', 8, None, 1),
              ( u'Педиатрические соматические ', 9, None, 1),
              ( u'Пульмонологические для детей', 10, None, 1),
              ( u'Токсикологические для детей', 11, None, 1),
              ( u'Травматологические для детей', 12, None, 1),
              ( u'Ортопедические для детей', 13, None, 1),
              ( u'Урологические для детей', 14, None, 1),
              ( u'Уроандрологические для детей', 15, None, 1),
              ( u'Абдоминальная хирургия для взрослых', 16, None, 1),
              ( u'Хирургические для детей ', 17, None, 1),
              ( u'Нейрохирургические для детей', 18, None, 1),
              ( u'Торакальной хирургии для детей', 19, None, 1),
              ( u'Челюстно-лицевая хирургия для детей', 20, None, 1),
              ( u'Эндокринологические для детей', 21, None, 1),
              ( u'Реанимационные койки для детей (сверхсметные) ', 22, 4, 1),
              ( u'Из всех коек круглосуточного стационара - платные', 23, 4, 1),
              ( u'из платных для детей - инфекционные', 24, 4, 1),
              ( u'из платных для детей - неврологические', 25, 4, 1),
              ( u'из платных для детей - нейрохирургические', 26, 4, 1),
              ( u'из платных для детей - оториноларингологические', 27, 4, 1),
              ( u'из платных для детей - офтальмологические', 28, 4, 1),
              ( u'из платных для детей - педиатрические', 29, 4, 1),
              ( u'из платных для детей - пульмонологические', 30, 4, 1),
              ( u'из платных для детей - реанимационные (сверхсметные)', 31, 4, 1),
              ( u'из платных для детей - травматологические', 32, 4, 1),
              ( u'из платных для детей - хирургические', 33, 4, 1),
              ( u'из платных для детей - челюстно-лицевой хирургии', 34, 4, 1),
             ]


MainCodeDS = [u'1',
              u'2',
              u'3',
              u'4',
              u'5',
              u'6',
              u'7',
              u'8',
              u'9',
              u'10',
              u'11',
              u'12',
              u'13',
              u'14',
              u'15',
              u'16',
              u'17',
              u'18',
              ]


MainCodePaymentDS = [u'13',
                     u'14',
                     u'15',
                     u'16',
                     u'17',
                     u'18'
                    ]


MainRowsDS = [
              ( u'ВСЕГО - дневной стационар', 1, None, 0),
              ( u'койки дневного стационара для детей - неврологические', 2, None, 0),
              ( u'койки дневного стационара для детей - офтальмологические', 3, None, 0),
              ( u'койки дневного стационара для детей - педиатрические', 4, None, 0),
              ( u'койки дневного стационара для детей - реабилитационные соматические - всего', 5, None, 0),
              ( u'койки дневного стационара для детей - реабилитационные с заболеваниями ЦНС и органов чувств', 6, None, 0),
              ( u'койки дневного стационара для детей - реабилитационные с заболеваниями ОДА и ПНС', 7, None, 0),
              ( u'койки дневного стационара для детей - урологические', 8, None, 0),
              ( u'койки дневного стационара для детей - уроандрологические', 9, None, 0),
              ( u'койки дневного стационара для детей - хирургические', 10, None, 0),
              ( u'койки дневного стационара для детей - челюстно-лицевой хирургии', 11, None, 0),
              ( u'койки дневного стационара для детей - эндокринологические', 12, None, 0),
              ( u'Из всех коек дневного стационара - платные (сумма строк 15-18)', 13, 4, 0),
              ( u'Из коек дневного стационара - платные для детей', 14, 4, 0),
              ( u'из коек дневного стационара для детей - платные неврологические', 15, 4, 0),
              ( u'из коек дневного стационара для детей - платные педиатрические', 16, 4, 0),
              ( u'из коек дневного стационара для детей - платные хирургические', 17, 4, 0),
              ( u'из коек дневного стационара для детей - платные реабилитационные с заболеваниями ЦНС и органов чувств', 18, 4, 0),
             ]


class CStationaryReportForMIACHard(CStationaryF007):
    def __init__(self, parent, currentOrgStructureId=None):
        CStationaryF007.__init__(self, parent)
        self.setTitle(u'Отчёт для МИАЦ')
        self.orientation = CPageFormat.Landscape
        self.currentOrgStructureId = currentOrgStructureId


    def getSetupDialog(self, parent):
        result = CStationaryReportForMIACSetupDialog(parent, self.currentOrgStructureId)
        result.setTitle(u'Отчёт для МИАЦ')
        result.setBegDateVisible(True)
        result.setForMIACHardVisible(False)
        self.stationaryF007SetupDialog = result
        self.stationaryF007SetupDialog.chkFinance.setVisible(True)
        self.stationaryF007SetupDialog.cmbFinance.setVisible(True)
        return result


    def averageDaysHospitalBed(self, orgStructureIdList, begDatePeriod, endDatePeriod, bedsSchedule, profile = None, isHospital = None, financeId=None, osType=None):
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
        if financeId:
           cond.append(tableOSHB['finance_id'].eq(financeId))
        if osType:
           cond.append(tableOS['type'].eq(osType))
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
        if profile:
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
        def createDictToRowIdx(capRow, hospitalBedProfileList, profileKS, profileDS, profilePayKS, profilePayDS, endDate, stationaryType):
            dictToRowIdx = {}
            financeId = forceRef(db.translate('rbFinance', 'code', 4, 'id'))
            tableIdent = tableRbAccountingSystem.innerJoin(tableRbHospitalBedProfileIdent, tableRbHospitalBedProfileIdent['system_id'].eq(tableRbAccountingSystem['id']))
            tableIdent = tableIdent.innerJoin(tableRbHospitalBedProfile, tableRbHospitalBedProfile['id'].eq(tableRbHospitalBedProfileIdent['master_id']))
            if stationaryType == 1:
                accountingSystemCode = u'miacReportDay'
            elif stationaryType == 2:
                accountingSystemCode = u'miacReportAlways'
            else:
                accountingSystemCode = u'miacReport'
            for row, codeList in enumerate(capRow):
                code = codeList[1]
                cond = [tableRbHospitalBedProfileIdent['deleted'].eq(0),
                        tableRbAccountingSystem['code'].eq(accountingSystemCode)
                        ]
                if endDate:
                    cond.append(db.joinOr([tableRbHospitalBedProfileIdent['checkDate'].isNull(), tableRbHospitalBedProfileIdent['checkDate'].le(endDate)]))
                if code > 1:
                    if stationaryType == 1 and code == 14:
                        cond.append(tableRbHospitalBedProfileIdent['value'].inlist(profilePayDS))
                    elif stationaryType == 2 and code == 21:
                        cond.append(tableRbHospitalBedProfileIdent['value'].inlist(profilePayKS))
                    elif stationaryType == 0 and code in [20, 34, 47]:
                        if code == 20:
                            cond.append(tableRbHospitalBedProfileIdent['value'].inlist(profilePayKS))
                        elif code == 34:
                            cond.append(tableRbHospitalBedProfileIdent['value'].inlist(profileDS))
                        elif code == 47:
                            cond.append(tableRbHospitalBedProfileIdent['value'].inlist(profilePayDS))
                    else:
                        cond.append(tableRbHospitalBedProfileIdent['value'].eq(code))
                else:
                    if codeList[3]:
                        cond.append(tableRbHospitalBedProfileIdent['value'].inlist(profileKS))
                    else:
                        cond.append(tableRbHospitalBedProfileIdent['value'].inlist(profileDS))
                if hospitalBedProfileList:
                    cond.append(tableRbHospitalBedProfile['id'].inlist(hospitalBedProfileList))
                profileList = db.getDistinctIdList(tableIdent, [tableRbHospitalBedProfile['id']], cond)
                dictTupleList = dictToRowIdx.get(code, [])
                dictTupleList.append((row, financeId if codeList[2] else None, codeList[3], profileList))
                dictToRowIdx[code] = dictTupleList
            return dictToRowIdx
        db = QtGui.qApp.db
        tableRbHospitalBedProfile = db.table('rbHospitalBedProfile')
        tableRbHospitalBedProfileIdent = db.table('rbHospitalBedProfile_Identification')
        tableRbAccountingSystem = db.table('rbAccountingSystem')
        endDate        = params.get('endDate', QDate())
        begDate        = params.get('begDate', QDate())
        stationaryType = params.get('stationaryType', 0)
        ageFor         = params.get('bedAgeFor', 0)
        ageTo          = params.get('bedAgeTo', 150)
        bedsSchedule   = params.get('bedsSchedule', 0)
        hospitalBedProfileList = params.get('hospitalBedProfileList', None)
        noProfileBed   = params.get('noProfileBed', True)
        isPermanentBed = params.get('isPermanentBed', False)
        noPrintCaption = params.get('noPrintCaption', False)
        noPrintParams  = params.get('noPrintFilterParameters', False)
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
            reportRowSize = 22
            if stationaryType == 1:
                MainRows = MainRowsDS
                profileKS = []
                profilePayKS = []
                profileDS = MainCodeDS
                profilePayDS = MainCodePaymentDS
            elif stationaryType == 2:
                MainRows = MainRowsKS
                profileKS = MainCodeKS
                profilePayKS = MainCodePaymentKS
                profileDS = []
                profilePayDS = []
            else:
                MainRows = MainRowsALL
                profileKS = MainCodeAllKS
                profilePayKS = MainCodePaymentAllKS
                profileDS = MainCodeAllDS
                profilePayDS = MainCodePaymentAllDS

            mapMainRows = createDictToRowIdx( [capRow for capRow in MainRows], hospitalBedProfileList, profileKS, profileDS, profilePayKS, profilePayDS, endDate, stationaryType )
            reportData = [ [0]*reportRowSize for row in xrange(len(MainRows)) ]

            def getDataReport(parOrgStructureIdList, profileIdList, osType = None):
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


                def averageYarHospitalBed(orgStructureIdList, begDate, endDate, profile = None, isHospital = None):
                    days = 0
                    daysMonths = 0
                    period = begDate.daysTo(endDate)
                    days = self.averageDaysHospitalBed(orgStructureIdList, begDate, endDate, bedsSchedule, profile, isHospital, financeId=financeId, osType=osType)
                    daysMonths += days / (period if period > 0 else 1)
                    return daysMonths

                def getBedForProfile(noProfileBed, profile = None, hospitalBedIdList = None):
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
                    countBeds = db.getCount(queryTable, countCol='rbHospitalBedProfile.id', where=cond)
                    return countBeds


                def unrolledHospitalBed34(profile = None):
                    tableVHospitalBedSchedule = tableVHospitalBed.innerJoin(tableOS,  tableVHospitalBed['master_id'].eq(tableOS['id']))
                    if QtGui.qApp.defaultHospitalBedProfileByMoving():
                        if bedsSchedule:
                            tableVHospitalBedSchedule = tableVHospitalBedSchedule.innerJoin(tableHBSchedule, tableVHospitalBed['schedule_id'].eq(tableHBSchedule['id']))
                        if self.hospitalBedIdList:
                            return getBedForProfile(noProfileBed, profile, self.hospitalBedIdList)
                    else:
                        cond = []
                        cond.append(tableOS['deleted'].eq(0))
                        if financeId:
                           cond.append(tableVHospitalBed['finance_id'].eq(financeId))
                        if osType:
                           cond.append(tableOS['type'].eq(osType))
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
                        elif bedsSchedule == 2:
                            cond.append(tableHBSchedule['code'].ne(1))
                        cond.append(db.joinOr([tableVHospitalBed['begDate'].isNull(), tableVHospitalBed['begDate'].lt(endDateTime)]))
                        cond.append(db.joinOr([tableVHospitalBed['endDate'].isNull(), tableVHospitalBed['endDate'].ge(begDateTime)]))
                        countBeds = db.getCount(tableVHospitalBedSchedule, countCol='vHospitalBed.id', where=cond)
                        return countBeds


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
                    stmt = db.selectStmt(queryTable, u'COUNT(Client.id) AS countDeath, SUM(%s) AS adultCount, SUM(%s) AS childrenCount'%(getAdultCount(), getChildrenCount()), where=cond)
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
                                                %(getAdultCount(), getChildrenCount()),
                                                where=cond)
                    query = db.query(stmt)
                    if query.first():
                        record = query.record()
                        return [forceInt(record.value('countDeath')), forceInt(record.value('adultCount')), forceInt(record.value('childrenCount'))]
                    else:
                        return [0, 0, 0]

                def getMovingPresent(orgStructureIdList, profile = None, flagCurrent = False, ageFor = False, ageTo = False):
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
                    cond.append(tableAPT['typeName'].like('HospitalBed'))
                    if financeId:
                       cond.append(tableOSHB['finance_id'].eq(financeId))
                    if osType:
                       cond.append(tableOS['type'].eq(osType))
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
                                                         u'SUM(%s) AS adultCount' %(getStringProperty(u'Патронаж%', u'(APS.value = \'Да\')'), getAdultCount()), where=cond)
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

                def presentBegDay(profile = None):
                    return getMovingPresent(orgStructureIdList, profile, False, ageFor, ageTo)

                # из других отделений
                def fromMovingTransfer(profile = None):
                    def getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile = None, transferIn = False, orgStructureIdList = [], boolFIO = False, ageFor = False, ageTo = False):
                        result = 0
                        if osType:
                            result = getMovingTransfer(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, transferIn, orgStructureIdList, boolFIO, ageFor = ageFor, ageTo = ageTo, transferType=1)
                        elif osType == 0:
                            result = getMovingTransferDS(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, transferIn, orgStructureIdList, boolFIO, ageFor = ageFor, ageTo = ageTo, transferType=1)
                        else:
                            if bedsSchedule != 2:
                                result = getMovingTransfer(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, transferIn, orgStructureIdList, boolFIO, ageFor = ageFor, ageTo = ageTo, transferType=1)
                            if bedsSchedule != 1:
                                result += getMovingTransferDS(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, transferIn, orgStructureIdList, boolFIO, ageFor = ageFor, ageTo = ageTo, transferType=1)
                        return result
                    return getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен из отделения', profile, False, orgStructureIdList, ageFor = ageFor, ageTo = ageTo)

                def receivedAll(profile = None):
                    def getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty = u'Переведен из отделения', profile = None, orgStructureIdList = [], boolFIO = False, noPropertyProfile = False, ageFor = False, ageTo = False):
                        result1 = result2 = [0, 0, 0, 0, 0, 0, 0]
                        if bedsSchedule != 2:
                            result1 = getReceived(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, orgStructureIdList, boolFIO, noPropertyProfile, ageFor = ageFor, ageTo = ageTo)
                        if bedsSchedule != 1:
                            result2 = getReceivedDS(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, orgStructureIdList, boolFIO, noPropertyProfile, ageFor = ageFor, ageTo = ageTo)
                        return list(map(lambda x, y: (x or 0) + (y or 0), result1, result2))
                    self.receivedBedsAll = 0
                    if osType:
                        getR = getReceived
                    elif osType == 0:
                        getR = getReceivedDS
                    else:
                        getR = getFunc
                    return getR(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен из отделения', profile, orgStructureIdList, ageFor = ageFor, ageTo = ageTo)

                def receivedForeignAll(profile = None):
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
                    return getR(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен из отделения', profile, orgStructureIdList, ageFor = ageFor, ageTo = ageTo)

                # в другие отделения
                def inMovingTransfer(profile = None):
                    def getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile = None, transferIn = False, orgStructureIdList = [], boolFIO = False, ageFor = False, ageTo = False):
                        result = 0
                        if osType:
                            result = getMovingTransfer(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, transferIn, orgStructureIdList, boolFIO, ageFor = ageFor, ageTo = ageTo,  transferType=0)
                        elif osType == 0:
                            result = getMovingTransferDS(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, transferIn, orgStructureIdList, boolFIO, ageFor = ageFor, ageTo = ageTo,  transferType=0)
                        else:
                            if bedsSchedule != 2:
                                result = getMovingTransfer(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, transferIn, orgStructureIdList, boolFIO, ageFor = ageFor, ageTo = ageTo,  transferType=0)
                            if bedsSchedule != 1:
                                result += getMovingTransferDS(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, transferIn, orgStructureIdList, boolFIO, ageFor = ageFor, ageTo = ageTo,  transferType=0)
                        return result
                    return getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен в отделение', profile, True, orgStructureIdList, ageFor = ageFor, ageTo = ageTo)

                def leavedAll(profile = None):
                    def getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty = u'Переведен в отделение', profile = None, orgStructureIdList = [], boolFIO = False, noPropertyProfile = False, ageFor = False, ageTo = False):
                        result1 = result2 = [0, 0, 0, 0, 0]
                        if osType == 0:
                            result2 = getLeavedDS(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, orgStructureIdList, boolFIO, noPropertyProfile, ageFor = ageFor, ageTo = ageTo)
                        elif osType:
                            result1 = getLeaved(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, orgStructureIdList, boolFIO, noPropertyProfile, ageFor = ageFor, ageTo = ageTo)
                        else:
                            if bedsSchedule != 2:
                                result1 = getLeaved(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, orgStructureIdList, boolFIO, noPropertyProfile, ageFor = ageFor, ageTo = ageTo)
                            if bedsSchedule != 1:
                                result2 = getLeavedDS(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, nameProperty, profile, orgStructureIdList, boolFIO, noPropertyProfile, ageFor = ageFor, ageTo = ageTo)
                        return list(map(lambda x, y: (x or 0) + (y or 0), result1, result2))
                    return getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен в отделение', profile, orgStructureIdList, ageFor = ageFor, ageTo = ageTo)

                def leavedAllDeath(profile = None):
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
                    return getFunc(isPermanentBed, noProfileBed, bedsSchedule, begDateTime, endDateTime, u'Переведен в отделение', profile, orgStructureIdList, ageFor = ageFor, ageTo = ageTo)

                def presentEndDay(profile = None):
                    return getMovingPresent(orgStructureIdList, profile, True, ageFor = ageFor, ageTo = ageTo)


                def involuteBedDays(profileIdList = None):
                    tableOSHBI = db.table('OrgStructure_HospitalBed_Involution').alias('OSHBI')
                    dbTable = tableOSHB.innerJoin(tableOSHBI, tableOSHBI['master_id'].eq(tableOSHB['id']))
                    cond = [
                        tableOSHB['profile_id'].inlist(profileIdList),
                        tableOSHB['master_id'].inlist(orgStructureIdList),
                        tableOSHBI['begDate'].lt(endDateTime.addDays(1)),
                        tableOSHBI['endDate'].ge(begDateTime)
                    ]
                    if financeId:
                       cond.append(tableOSHB['finance_id'].eq(financeId))
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
                    return days

                for dictTupleList in mapMainRows.values():
                    for row, financeId, osType, profileList in dictTupleList:
                        if row == -1:
                            if stationaryType in [1, 2]:
                                reportLine = reportData[0]
                                row = 0
                            else:
                                if osType:
                                    reportLine = reportData[0]
                                    row = 0
                                else:
                                    row = 30
                                    reportLine = reportData[30]
                        else:
                            reportLine = reportData[row]
                        for profileId in profileList:
                            reportLine[0] += unrolledHospitalBed34([profileId])
                            reportLine[1] += averageYarHospitalBed(orgStructureIdList, begDate, endDate, [profileId])
                            reportLine[2] += presentBegDay([profileId])
                            receivedInfo = receivedAll([profileId])  #receivedBedAll = receivedInfo[5]
                            reportLine[3] += receivedInfo[0]
                            reportLine[4] += receivedInfo[4]
                            reportLine[5] += receivedInfo[3]
                            reportLine[6] += receivedInfo[1]
                            reportLine[7] += receivedInfo[2]
                            reportLine[21] += receivedInfo[6]
                            reportLine[20] += receivedForeignAll([profileId])
                            reportLine[8] += fromMovingTransfer([profileId])
                            reportLine[9] += inMovingTransfer([profileId])
                            countLeavedAll, leavedDeath, leavedTransfer, countStationaryDay, leavedAdultCount = leavedAll([profileId])
                            reportLine[10] += countLeavedAll-leavedDeath
                            reportLine[11] += leavedAdultCount
                            reportLine[12] += countStationaryDay
                            leavedDeathCount, leavedAdultCount, leavedChildrenCount = leavedAllDeath([profileId])
                            reportLine[13] += leavedDeathCount
                            reportLine[14] += leavedChildrenCount
                            reportLine[15] += leavedAdultCount
                            presentAll, presentPatronag, clientRural, presentAdultCountEnd = presentEndDay([profileId])
                            reportLine[16] += presentAll
                            #reportLine[18] += presentAdultCountEnd
                            reportLine[18] += getSeniorsMovingDays(orgStructureIdList, begDateTime, endDateTime, profile = [profileId], isHospital = None, rural = None, additionalCond = None, bedsSchedule = bedsSchedule, typeOS = None)
                            reportLine[19] += involuteBedDays([profileId])
                            reportLine[17] += getMovingDays(orgStructureIdList, begDateTime, endDateTime, [profileId], bedsSchedule = bedsSchedule)
                        reportData[row] = reportLine
                return reportData
            boldChars = QtGui.QTextCharFormat()
            boldChars.setFontWeight(QtGui.QFont.Bold)
            reportData = getDataReport(begOrgStructureIdList, hospitalBedProfileList, osType = (stationaryType - 1) if stationaryType else None)

            for row, rowDescr in enumerate(MainRows):
                reportLine = reportData[row]
                i = table.addRow()
                table.setText(i, 0, rowDescr[0])
                for col in xrange(reportRowSize):
                    table.setText(i, 1+col, reportLine[col])

        return doc
