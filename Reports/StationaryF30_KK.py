# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2019 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
import re

from PyQt4 import QtGui
from PyQt4.QtCore import QDate, QDateTime, QTime

from Events.Utils import getActionTypeIdListByFlatCode, CFinanceType
from Orgs.Utils import getOrgStructureFullName
from library.Utils import forceDate, forceInt, forceString, forceDateTime, forceBool, forceRef

from Reports.Report import CReport
from Reports.ReportBase import CReportBase, createTable
from Reports.ReportView import CPageFormat
from Reports.Utils import dateRangeAsStr


from Ui_StationaryF30KKSetup import Ui_StationaryF30KKSetupDialog

MainRows3100 = [
    # отступ | наименование | № строки | профили коек
    (0, u'Всего', '1', ''),
    (1, u'в том числе:\nаллергологические для взрослых', '2', '07'),
    (1, u'аллергологические для детей', '3', '08'),
    (1, u'для беременных и рожениц', '4', '38;98'),
    (1, u'для патологии беременности', '5', '39;1A'),
    (1, u'гинекологические для взрослых', '6', '97>=18;40;1B;41'),
    (2, u'из них гинекологические для вспомогательных репродуктивных технологий', '6.1', '1B'),
    (1, u'гинекологические для детей', '7', '97<18;96'),
    (1, u'гастроэнтерологические для взрослых', '8', '05'),
    (1, u'гастроэнтерологические для детей', '9', '06'),
    (1, u'гематологические для взрослых', '10', '15'),
    (1, u'гематологические для детей', '11', '16'),
    (1, u'геронтологические', '12', '70'),
    (1, u'дерматологические для взрослых', '13', '1C'),
    (1, u'дерматологические для детей', '14', '1D'),
    (1, u'венерологические для взрослых', '15', '1E>=18'),
    (1, u'венерологические для детей', '16', '1E<18'),
    (1, u'инфекционные для взрослых', '17', '1G>=18;13;1GCOVID>=18;13COVID'),
    (2, u'из них лепрозные', '17.1', '1G>=18'),
    (5, u'Для COVID-19', '17.2', '1GCOVID>=18;13COVID'),
    (1, u'инфекционные для детей', '18', '1G<18;14;1GCOVID<18;14COVID'),
    (2, u'из них лепрозные', '18.1', '1G<18'),
    (5, u'Для COVID-19', '18.2', '1GCOVID<18;14COVID'),
    (1, u'кардиологические для взрослых', '19', '03;1U;94'),
    (2, u'из них:\nкардиологические интенсивной терапии', '19.1', '1U'),
    (2, u'кардиологические для больных с острым инфарктом миокарда', '19.2', '94'),
    (1, u'кардиологические для детей', '20', '77'),
    (1, u'наркологические', '21', '53'),
    (2, u'из них для детей', '21.1', ''),
    (1, u'неврологические для взрослых', '22', '47;92;1V'),
    (2, u'из них:\nневрологические для больных с острыми нарушениями мозгового кровообращения', '22.1', '92'),
    (2, u'неврологические интенсивной терапии', '22.2', '1V'),
    (1, u'неврологические для детей', '23', '1O<18;48'),
    (2, u'из них психоневрологические для детей', '23.1', '1O<18'),
    (1, u'нефрологические для взрослых', '24', '17'),
    (1, u'нефрологические для детей', '25', '18'),
    (1, u'онкологические для взрослых', '26', '2D-2J>=18;36'),
    (2, u'из них:\nонкологические торакальные', '26.1', '2D>=18'),
    (2, u'онкологические абдоминальные', '26.2', '2E>=18'),
    (2, u'онкоурологические ', '26.3', '2F>=18'),
    (2, u'онкогинекологические', '26.4', '2G>=18'),
    (2, u'онкологические опухолей головы и шеи', '26.5', '2H>=18'),
    (2, u'онкологические опухолей костей, кожи и мягких тканей', '26.6', '2I>=18'),
    (2, u'онкологические паллиативные', '26.7', '2J>=18'),
    (1, u'онкологические для детей', '27', '2D-2J>=18;37'),
    (1, u'оториноларингологические для взрослых', '28', '1H>=18;55'),
    (2, u'из них оториноларингологические для кохлеарной имплантации', '28.1', '1H>=18'),
    (1, u'оториноларингологические для детей', '29', '1H<18;56'),
    (2, u' из них оториноларингологические для детей для кохлеарной имплантации', '29.1', ''),
    (1, u'офтальмологические для взрослых', '30', '53'),
    (1, u'офтальмологические для детей', '31', '54'),
    (1, u'ожоговые', '32', '29-99'),
    (1, u'паллиативные для взрослых', '33', '74>=18'),
    (1, u'паллиативные для детей', '34', '74<18'),
    (1, u'педиатрические соматические', '35', '61;62;60;91;1W'),
    (2, u'из них\nпатологии новорожденных и недоношенных детей', '35.1', '91'),
    (2, u'койки для новорожденных', '35.2', '1W'),
    (1, u'проктологические', '36', '63'),
    (1, u'психиатрические для взрослых', '37', '1O>=18;1R;49;51;1P'),
    (2, u'из них:\nпсихосоматические', '37.1', '51'),
    (2, u'соматопсихиатрические', '37.2', '1P'),
    (2, u'психиатрические для судебно-психиатрической экспертизы', '37.3', '1R'),
    (1, u'психиатрические для детей', '38', '50'),
    (1, u'профпатологические', '39', '71'),
    (1, u'пульмонологические для взрослых', '40', '68'),
    (1, u'пульмонологические для детей', '41', '69'),
    (1, u'радиологические', '42', '59'),
    (1, u'реабилитационные для взрослых', '43', '1X;1Z;2B;2K'),
    (2, u'из них:\nреабилитационные для больных с заболеваниями центральной нервной системы и органов чувств', '43.1', '1Z'),
    (2, u'реабилитационные для больных с заболеваниями опорно-двигательного аппарата и периферической нервной системы', '43.2', '2B'),
    (2, u'реабилитационные наркологические для взрослых', '43.3', '2K'),
    (2, u'реабилитационные соматические', '43.4', '1X'),
    (1, u'реабилитационные для детей', '44', '1Y;2A;2C'),
    (2, u'в том числе: \nреабилитационные для детей с  заболеваниями центральной нервной системы и органов чувств', '44.1', '2A'),
    (2, u'реабилитационные для детей с заболеваниями опорно-двигательного аппарата и периферической нервной системы', '44.2', '2C'),
    (2, u'реабилитационные соматические', '44.3', '1Y'),
    (2, u'реабилитационные для детей с наркологическими расстройствами', '44.4', ''),
    (1, u'реанимационные ', '45', '1I;1J;1S;1T;1ICOVID'),
    (2, u'из них:\nреанимационные для новорожденных', '45.1', '1J'),
    (2, u'интенсивной терапии', '45.2', '1S'),
    (2, u'интенсивной терапии для новорожденных', '45.3', '1T'),
    (5, u'для COVID-19', '45.4', '1ICOVID'),
    (1, u'ревматологические для взрослых', '46', '64'),
    (1, u'ревматологические для детей', '47', '65'),
    (1, u'сестринского ухода', '48', '73'),
    (1, u'скорой медицинской помощи краткосрочного пребывания', '49', '1K;1L'),
    (1, u'скорой медицинской помощи суточного пребывания', '50', '1M;1N'),
    (1, u'терапевтические', '51', '02'),
    (1, u'токсикологические', '52', '72'),
    (1, u'травматологические для взрослых', '53', '27'),
    (1, u'травматологические для детей', '54', '28'),
    (1, u'ортопедические для взрослых', '55', '30'),
    (1, u'ортопедические для детей', '56', '31'),
    (1, u'туберкулезные для взрослых', '57', '42'),
    (1, u'туберкулезные для детей', '58', '45'),
    (1, u'урологические для взрослых', '59', '32'),
    (1, u'урологические для детей', '60', '33;1F'),
    (2, u'из них уроандрологические для детей', '60.1', '1F'),
    (1, u'хирургические для взрослых', '61', '19'),
    (1, u'абдоминальной хирургии', '62', '87;88'),
    (1, u'хирургические для детей', '63', '20'),
    (1, u'нейрохирургические для взрослых', '64', '21'),
    (1, u'нейрохирургические для детей', '65', '22'),
    (1, u'торакальной хирургии для взрослых', '66', '23'),
    (1, u'торакальной хирургии для детей', '67', '24'),
    (1, u'кардиохирургические', '68', '25;78'),
    (1, u'сосудистой хирургии', '69', '26'),
    (1, u'хирургические гнойные для взрослых', '70', '66'),
    (1, u'хирургические гнойные для детей ', '71', '67'),
    (1, u'челюстно-лицевой хирургии для взрослых', '72', '84'),
    (1, u'челюстно-лицевой хирургии для детей', '73', '85'),
    (1, u'эндокринологические для взрослых', '74', '11'),
    (1, u'эндокринологические для детей', '75', '12'),
    (1, u'прочие койки для взрослых', '76', '2N;2O;80:79'),
    (1, u'прочие койки для детей', '77', '35'),
    (1, u'Кроме того, «движение» больных новорожденных', '78', None),
    (1, u'Из общего числа (стр. 1) - платных коек', '79', 'cash'),
    (1, u'Кроме того – дополнительно развернутые койки для лечения пациентов с COVID-19', '80', ''),
    (1, u'Реанимационные (с учетом внутрибольничных переводов)', '81', '1I;1ICOVID;1IORIT'),
    (1, u'Профиль неопределен', '82', 'NOPROFILE')
]


class CStationaryF30KKSetupDialog(QtGui.QDialog, Ui_StationaryF30KKSetupDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())
        self.cmbFinance.setTable('rbFinance', True)


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtBegTime.setTime(params.get('begTime', QTime(9, 0, 0, 0)))
        self.edtTimeEdit.setTime(params.get('endTime', QTime(9, 0, 0, 0)))
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))
        self.cmbStacType.setCurrentIndex(params.get('stacType', 0))
        self.cmbSchedule.setCurrentIndex(params.get('bedsSchedule', 0))
        self.cmbFinance.setValue(params.get('financeId', None))
        self.cmbAddressType.setCurrentIndex(params.get('addressType', 0))
        self.chkPermanentBed.setChecked(params.get('permanentBed', False))
        self.chkEventExpose.setChecked(params.get('eventExpose', False))


    def params(self):
        def getPureHMTime(time):
            return QTime(time.hour(), time.minute())
        return dict(endDate=self.edtEndDate.date(),
                    endTime=getPureHMTime(self.edtTimeEdit.time()),
                    begDate=self.edtBegDate.date(),
                    begTime=getPureHMTime(self.edtBegTime.time()),
                    orgStructureId=self.cmbOrgStructure.value(),
                    stacType=self.cmbStacType.currentIndex(),
                    bedsSchedule=self.cmbSchedule.currentIndex(),
                    financeId=self.cmbFinance.value(),
                    addressType=self.cmbAddressType.currentIndex(),
                    permanentBed=self.chkPermanentBed.isChecked(),
                    eventExpose=self.chkEventExpose.isChecked()
                   )


class CStationaryF30_KK(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Листок учета движения больных и коечного фонда стационара')
        self.pageFormat = CPageFormat(pageSize=CPageFormat.A4, orientation=CPageFormat.Landscape, leftMargin=1, topMargin=1, rightMargin=1,  bottomMargin=1)
        self.stationaryF30KKSetupDialog = None
        self.clientDeath = 8


    def getSetupDialog(self, parent):
        result = CStationaryF30KKSetupDialog(parent)
        self.stationaryF30KKSetupDialog = result
        return result


    def getOrgStructureIdList(self, treeIndex):
        treeItem = treeIndex.internalPointer() if treeIndex.isValid() else None
        return treeItem.getItemIdList() if treeItem else []


    def dumpParams(self, cursor, params):
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

        orgStructureId = params.get('orgStructureId', None)
        stacType = params.get('stacType', 0)
        bedsSchedule = params.get('bedsSchedule', 0)
        financeId = params.get('financeId', None)
        addressType = params.get('addressType', 0)
        permanentBed = params.get('permanentBed', False)
        eventExpose = params.get('eventExpose', False)

        if orgStructureId:
            description.append(u'подразделение: ' + getOrgStructureFullName(orgStructureId))
        else:
            description.append(u'подразделение: ЛПУ')

        if stacType:
            description.append(u'тип стационара: ' + (u'круглосуточный' if stacType == 1 else u'дневной'))

        if bedsSchedule:
            description.append(u'режим койки: ' + (u'круглосуточные' if bedsSchedule == 1 else u'не круглосуточные'))

        if financeId:
            description.append(u'тип финансирования: %s' % forceString(QtGui.qApp.db.translate('rbFinance', 'id', financeId, 'name')))

        description.append(u'адрес: ' + (u'по проживанию' if addressType else u'по регистрации'))

        if permanentBed:
            description.append(u'учитывая внештатные койки')

        if eventExpose:
            description.append(u'учитывая флаг "Выставлять в счет"')

        description.append(u'отчёт составлен: '+forceString(QDateTime.currentDateTime()))
        columns = [ ('100%', [], CReportBase.AlignLeft) ]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()


    def getCaption(self, cursor, params, title):
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        boldChars = QtGui.QTextCharFormat()
        boldChars.setFontWeight(QtGui.QFont.Bold)
        columns2 = [('100%', [], CReportBase.AlignCenter)]
        table2 = createTable(cursor, columns2, headerRowCount=3, border=0, cellPadding=2, cellSpacing=0)
        table2.setText(0, 0, u'''Раздел IV. ДЕЯТЕЛЬНОСТЬ МЕДИЦИНСКОЙ ОРГАНИЗАЦИИ ПО ОКАЗАНИЮ
МЕДИЦИНСКОЙ ПОМОЩИ В СТАЦИОНАРНЫХ УСЛОВИЯХ''', charFormat=boldChars)
        table2.setText(1, 0, title, charFormat=boldChars)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()


class CStationaryF30Moving_KK(CStationaryF30_KK):
    def __init__(self, parent):
        CStationaryF30_KK.__init__(self, parent)
        self.setTitle(u'1. Коечный фонд и его использование(3100)')

    def build(self, params):

        db = QtGui.qApp.db
        tableOS = db.table('OrgStructure')
        tableOSHB = db.table('OrgStructure_HospitalBed')
        tableOSHBI = db.table('OrgStructure_HospitalBed_Involution').alias('OSHBI')
        tableHBSchedule = db.table('rbHospitalBedShedule')
        tableRbHospitalBedProfile = db.table('rbHospitalBedProfile')

        tableEvent = db.table('Event')
        tableContract = db.table('Contract')
        tableEventType = db.table('EventType')
        tableMAT = db.table('rbMedicalAidType')
        tableClient = db.table('Client')
        tableAction = db.table('Action')
        tableMovingAction = db.table('Action').alias('MovingAction')
        tableAPTHB = db.table('ActionPropertyType').alias('apt_bed')
        tableAPHB = db.table('ActionProperty').alias('ap_bed')
        tableAPVHB = db.table('ActionProperty_HospitalBed').alias('apv_bed')

        tableAPT = db.table('ActionPropertyType')
        tableAP = db.table('ActionProperty')
        tableAPS = db.table('ActionProperty_String')
        
        tableDiagnosis = db.table('Diagnosis')
        tableDiagnostic = db.table('Diagnostic')

        reanimProfiles = ['1I', '1J', '1S', '1T']

        # количество коек по профилям (столбец 3)
        def getPermamentHospitalBeds(orgStructureList, bedsSchedule, begDate, endDate, permamentBed):
            cols = [tableRbHospitalBedProfile['regionalCode'],
                    'count(OrgStructure_HospitalBed.id) as cnt',
                    u'''IF(cast(case when OrgStructure_HospitalBed.age like '%-%г' then substring_index(OrgStructure_HospitalBed.age, '-', -1)
                  when OrgStructure_HospitalBed.age like '%-%м' then FLOOR(substring_index(OrgStructure_HospitalBed.age, '-', -1)/12)
                  when OrgStructure_HospitalBed.age like '%-%д' then FLOOR(substring_index(OrgStructure_HospitalBed.age, '-', -1)/365)
                  else 150 end as unsigned integer) < 18, 1, 0) as isChild'''
                    ]
            cond = [tableOS['deleted'].eq(0),
                    tableOSHB['deleted'].eq(0),
                    db.joinOr([tableOSHB['begDate'].isNull(),
                               db.joinAnd([tableOSHB['begDate'].isNotNull(), tableOSHB['begDate'].le(begDate)])]),
                    db.joinOr([tableOSHB['endDate'].isNull(),
                               db.joinAnd([tableOSHB['endDate'].isNotNull(), tableOSHB['endDate'].ge(endDate)])])
                    ]
            if not permamentBed:
                cond.append(tableOSHB['isPermanent'].eq(1))
            queryTable = tableOS.leftJoin(tableOSHB, tableOSHB['master_id'].eq(tableOS['id']))
            queryTable = queryTable.leftJoin(tableRbHospitalBedProfile, tableRbHospitalBedProfile['id'].eq(tableOSHB['profile_id']))
            if orgStructureList:
                cond.append(tableOS['id'].inlist(orgStructureList))
            if bedsSchedule:
                queryTable = queryTable.leftJoin(tableHBSchedule, tableHBSchedule['id'].eq(tableOSHB['schedule_id']))
                if bedsSchedule == 1:
                    cond.append(tableHBSchedule['code'].eq('1'))
                else:
                    cond.append(tableHBSchedule['code'].ne('1'))
            records = db.getRecordListGroupBy(queryTable, cols=cols, where=db.joinAnd(cond), group=[tableRbHospitalBedProfile['regionalCode'].name(), 'isChild'])
            return records


        # среднегодовые койки
        def averageDaysHospitalBed(orgStructureIdList, bedsSchedule, begDatePeriod, endDatePeriod, permamentBed):
            days = 0
            cols = [tableRbHospitalBedProfile['regionalCode'], tableOSHB['begDate'], tableOSHB['endDate'],
                    u'''IF(cast(case when OrgStructure_HospitalBed.age like '%-%г' then substring_index(OrgStructure_HospitalBed.age, '-', -1)
                                     when OrgStructure_HospitalBed.age like '%-%м' then FLOOR(substring_index(OrgStructure_HospitalBed.age, '-', -1)/12)
                                     when OrgStructure_HospitalBed.age like '%-%д' then FLOOR(substring_index(OrgStructure_HospitalBed.age, '-', -1)/365)
                                     else 150 end as unsigned integer) < 18, 1, 0) as isChild'''
                    ]
            queryTable = tableOS.leftJoin(tableOSHB, tableOSHB['master_id'].eq(tableOS['id']))
            queryTable = queryTable.leftJoin(tableRbHospitalBedProfile, tableRbHospitalBedProfile['id'].eq(tableOSHB['profile_id']))
            cond = [tableOS['deleted'].eq(0),
                    tableOSHB['deleted'].eq(0),
                    db.joinOr([tableOSHB['begDate'].isNull(),
                               db.joinAnd([tableOSHB['begDate'].isNotNull(), tableOSHB['begDate'].le(begDatePeriod)])]),
                    db.joinOr([tableOSHB['endDate'].isNull(),
                               db.joinAnd([tableOSHB['endDate'].isNotNull(), tableOSHB['endDate'].ge(endDatePeriod)])])
                    ]
            if not permamentBed:
                cond.append(tableOSHB['isPermanent'].eq(1))
            if orgStructureIdList:
                cond.append(tableOSHB['master_id'].inlist(orgStructureIdList))
            if bedsSchedule:
                queryTable = queryTable.innerJoin(tableHBSchedule, tableOSHB['schedule_id'].eq(tableHBSchedule['id']))
                if bedsSchedule == 1:
                    cond.append(tableHBSchedule['code'].eq(1))
                elif bedsSchedule == 2:
                    cond.append(tableHBSchedule['code'].ne(1))

            stmt = db.selectStmt(queryTable, cols, where=cond)
            query = db.query(stmt)
            mapProfileDays = {}
            while query.next():
                record = query.record()
                ageCond = ''
                profile = forceString(record.value('regionalCode'))
                isChild = forceBool(record.value('isChild'))
                begDate = forceDate(record.value('begDate'))
                endDate = forceDate(record.value('endDate'))

                if profile in profileWithAgeList:
                    ageCond = '<18' if isChild else '>=18'

                days = mapProfileDays.setdefault((profile, ageCond), 0)
                if not begDate or begDate < begDatePeriod:
                    begDate = begDatePeriod
                if not endDate or endDate > endDatePeriod:
                    endDate = endDatePeriod
                if begDate and endDate:
                    if begDate == endDate:
                        days += 1
                    else:
                        days += begDate.daysTo(endDate)
                mapProfileDays[(profile, ageCond)] = days
            return mapProfileDays


        # поступившие (столбцы 6-9)
        def getReceived(orgStructureIdList, bedsSchedule, begDateTime, endDateTime, stacType, financeId, addressType, permamentBed, eventExpose):
            cond = [tableEvent['deleted'].eq(0),
                    tableOSHB['deleted'].eq(0),
                    db.joinOr(
                        [tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode('received%')),
                         db.joinAnd([tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode('moving%')),
                                     tableRbHospitalBedProfile['regionalCode'].eq('1I'),
                                     tableAction['id'].ne(tableMovingAction['id'])])]),
                    tableAction['deleted'].eq(0),
                    tableClient['deleted'].eq(0),
                    tableEvent['setDate'].ge(begDateTime),
                    tableEvent['setDate'].le(endDateTime),
                    tableEventType['context'].notInlist(['relatedAction', 'inspection']),
                    tableEventType['code'].notInlist(['hospDir', 'egpuDisp', 'plng'])
                    ]
            actionTypeMovingList = getActionTypeIdListByFlatCode('moving%')
            queryTable = tableEvent.leftJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
            queryTable = queryTable.leftJoin(tableMAT, tableMAT['id'].eq(tableEventType['medicalAidType_id']))
            queryTable = queryTable.leftJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
            queryTable = queryTable.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.innerJoin(tableMovingAction, "MovingAction.id = (SELECT min(Action.id) FROM Action WHERE Action.event_id = Event.id AND Action.deleted = 0 AND Action.actionType_id IN ({0}))".format(
                                                  ','.join([ str(id) for id in actionTypeMovingList]) if actionTypeMovingList else 0))
            queryTable = queryTable.leftJoin(tableAPTHB, db.joinAnd([tableAPTHB['actionType_id'].eq(tableMovingAction['actionType_id']),
                                                                      tableAPTHB['name'].eq(u'койка'),
                                                                      tableAPTHB['deleted'].eq(0)]))
            queryTable = queryTable.leftJoin(tableAPHB, db.joinAnd(
                [tableAPHB['type_id'].eq(tableAPTHB['id']),
                 tableAPHB['action_id'].eq(tableMovingAction['id']),
                 tableAPHB['deleted'].eq(0)]))
            queryTable = queryTable.leftJoin(tableAPVHB, tableAPVHB['id'].eq(tableAPHB['id']))
            queryTable = queryTable.leftJoin(tableOSHB, tableOSHB['id'].eq(tableAPVHB['value']))
            queryTable = queryTable.leftJoin(tableRbHospitalBedProfile, tableRbHospitalBedProfile['id'].eq(tableOSHB['profile_id']))
            queryTable = queryTable.leftJoin(tableContract, tableEvent['contract_id'].eq(tableContract['id']))
            queryTable = queryTable.leftJoin(tableDiagnostic,db.joinAnd( 
                                             [tableEvent['id'].eq(tableDiagnostic['event_id']),
                                              tableDiagnostic['diagnosisType_id'].eq(1),
                                              tableDiagnostic['deleted'].eq(0)]))
            queryTable = queryTable.leftJoin(tableDiagnosis, tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']))
            if orgStructureIdList:
                cond.append(tableOSHB['master_id'].inlist(orgStructureIdList))
            if bedsSchedule:
                queryTable = queryTable.innerJoin(tableHBSchedule, tableOSHB['schedule_id'].eq(tableHBSchedule['id']))
                if bedsSchedule == 1:
                    cond.append(tableHBSchedule['code'].eq(1))
                elif bedsSchedule == 2:
                    cond.append(tableHBSchedule['code'].ne(1))

            if stacType == 0:
                cond.append(tableMAT['code'].inlist(['1', '2', '3', '7'])),
                cond.append(tableMAT['regionalCode'].notInlist(['111', '112'])),
            elif stacType == 1:
                cond.append(tableMAT['code'].inlist(['1', '2', '3']))
                cond.append(tableMAT['regionalCode'].notInlist(['111', '112'])),
            elif stacType == 2:
                cond.append(tableMAT['code'].eq('7'))

            if financeId:
                cond.append(tableContract['finance_id'].eq(financeId))

            if not permamentBed:
                cond.append(tableOSHB['isPermanent'].eq(1))

            if eventExpose:
                cond.append(tableEvent['expose'].eq(1))

            addressFunc = 'getClientLocAddressId' if addressType == 1 else 'getClientRegAddressId'

            cols = u'''
            CASE 
                WHEN rbHospitalBedProfile.regionalCode = '1I' and Action.actionType_id in ({0}) THEN CONCAT(rbHospitalBedProfile.regionalCode,'ORIT')
                WHEN rbHospitalBedProfile.regionalCode in ('1G','1I','13') and (Diagnosis.mkb='U07.1' or Diagnosis.mkb='U07.2') and Action.actionType_id not in ({0}) THEN CONCAT(rbHospitalBedProfile.regionalCode,'COVID')
                WHEN Action.actionType_id not in ({0}) THEN rbHospitalBedProfile.regionalCode 
            END as profile,
            Contract.finance_id,
            COUNT(Event.id) AS countAll, 
            SUM(isAddressVillager((SELECT address_id   FROM ClientAddress  WHERE id = {1}(Client.id)))) as countVillager,
            IF(Client.birthDate > Event.setDate - interval 18 year, 1, 0) isChild,
            SUM(IF(Client.birthDate > Event.setDate - interval 18 year, 1, 0)) as countChild,
            CASE 
                WHEN Event.setDate<'2022-01-01T00:00:00' THEN SUM(IF(Client.sex = 1 and Client.birthDate <= Event.setDate - interval 60 year OR Client.sex = 2 and Client.birthDate <= Event.setDate - interval 55 year, 1, 0))
                WHEN Event.setDate between '2022-01-01T00:00:00' and '2023-12-31T23:59:59' THEN SUM(IF(Client.sex = 1 and Client.birthDate <= Event.setDate - interval 61 year OR Client.sex = 2 and Client.birthDate <= Event.setDate - interval 56 year, 1, 0)) 
                WHEN Event.setDate>='2024-01-01T00:00:00' THEN SUM(IF(Client.sex = 1 and Client.birthDate <= Event.setDate - interval 62 year OR Client.sex = 2 and Client.birthDate <= Event.setDate - interval 57 year, 1, 0)) 
            END as countSenior'''.format(','.join([ str(id) for id in actionTypeMovingList]) if actionTypeMovingList else 0, addressFunc)

            records = db.getRecordListGroupBy(queryTable, cols=cols, where=db.joinAnd(cond), group=['profile', 'Contract.finance_id', 'IF(Client.birthDate > Event.setDate - interval 18 year, 1, 0)'])
            return records


        # выписаные (столбцы 10-14)
        def getLeaved(orgStructureIdList, bedsSchedule, begDateTime, endDateTime, stacType, financeId, permanentBed, eventExpose):

            cond = [tableEvent['deleted'].eq(0),
                    tableOSHB['deleted'].eq(0),
                    db.joinOr(
                        [tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode('leaved%')),
                         db.joinAnd([tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode('moving%')),
                                     tableRbHospitalBedProfile['regionalCode'].eq('1I'),
                                     tableOS['id'].isNotNull()])]),tableAction['deleted'].eq(0),
                    tableClient['deleted'].eq(0),
                    tableEvent['execDate'].ge(begDateTime),
                    tableEvent['execDate'].le(endDateTime),
                    tableEventType['context'].notInlist(['relatedAction', 'inspection']),
                    tableEventType['code'].notInlist(['hospDir', 'egpuDisp', 'plng'])
                    ]
            actionTypeMovingList = getActionTypeIdListByFlatCode('moving%')
            queryTable = tableEvent.leftJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
            queryTable = queryTable.leftJoin(tableMAT, tableMAT['id'].eq(tableEventType['medicalAidType_id']))
            queryTable = queryTable.leftJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
            queryTable = queryTable.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.innerJoin(tableMovingAction,
                                              "MovingAction.id = (SELECT max(Action.id) FROM Action WHERE Action.event_id = Event.id AND Action.deleted = 0 AND Action.actionType_id IN ({0}))".format(
                                                  ','.join([ str(id) for id in actionTypeMovingList]) if actionTypeMovingList else 0))
            queryTable = queryTable.leftJoin(tableAPTHB, db.joinAnd(
                [tableAPTHB['actionType_id'].eq(tableMovingAction['actionType_id']),
                 tableAPTHB['name'].eq(u'койка'),
                 tableAPTHB['deleted'].eq(0)]))
            queryTable = queryTable.leftJoin(tableAPHB, db.joinAnd(
                [tableAPHB['type_id'].eq(tableAPTHB['id']),
                 tableAPHB['action_id'].eq(tableMovingAction['id']),
                 tableAPHB['deleted'].eq(0)]))
            queryTable = queryTable.leftJoin(tableAPVHB, tableAPVHB['id'].eq(tableAPHB['id']))
            queryTable = queryTable.leftJoin(tableOSHB, tableOSHB['id'].eq(tableAPVHB['value']))
            queryTable = queryTable.leftJoin(tableRbHospitalBedProfile,
                                             tableRbHospitalBedProfile['id'].eq(tableOSHB['profile_id']))

            queryTable = queryTable.leftJoin(tableAPT, db.joinAnd(
                [tableAPT['actionType_id'].eq(tableAction['actionType_id']),
                 tableAPT['name'].eq(u'Исход госпитализации'),
                 tableAPT['deleted'].eq(0)]))
            queryTable = queryTable.leftJoin(tableAP, db.joinAnd(
                [tableAP['type_id'].eq(tableAPT['id']),
                 tableAP['action_id'].eq(tableAction['id']),
                 tableAP['deleted'].eq(0)]))
            queryTable = queryTable.leftJoin(tableAPS, tableAPS['id'].eq(tableAP['id']))
            queryTable = queryTable.leftJoin(tableContract, tableEvent['contract_id'].eq(tableContract['id']))
            queryTable = queryTable.leftJoin(tableDiagnostic,db.joinAnd( 
                                             [tableEvent['id'].eq(tableDiagnostic['event_id']),
                                              tableDiagnostic['diagnosisType_id'].eq(1),
                                              tableDiagnostic['deleted'].eq(0)]))
            queryTable = queryTable.leftJoin(tableDiagnosis, tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']))
            
            tableAPTOS = db.table('ActionPropertyType').alias('apt_orit')
            tableAPOS = db.table('ActionProperty').alias('ap_orit')
            tableAPVOS = db.table('ActionProperty_OrgStructure').alias('apv_orit')
            queryTable = queryTable.leftJoin(tableAPTOS, db.joinAnd(
                [tableAPTOS['actionType_id'].eq(tableMovingAction['actionType_id']),
                 tableAPTOS['name'].eq(u'Переведен из отделения'),
                 tableAPTOS['deleted'].eq(0)]))
            queryTable = queryTable.leftJoin(tableAPOS, db.joinAnd(
                [tableAPOS['type_id'].eq(tableAPTOS['id']),
                 tableAPOS['action_id'].eq(tableMovingAction['id']),
                 tableAPOS['deleted'].eq(0)]))
            queryTable = queryTable.leftJoin(tableAPVOS, tableAPVOS['id'].eq(tableAPOS['id']))
            queryTable = queryTable.leftJoin(tableOS, db.joinAnd(
                [tableOS['id'].eq(tableAPVOS['value']),
                 tableOS['code'].like(u'%ОРИТ%')]))
            
            if orgStructureIdList:
                cond.append(tableOSHB['master_id'].inlist(orgStructureIdList))
            if bedsSchedule:
                queryTable = queryTable.innerJoin(tableHBSchedule,
                                                  tableOSHB['schedule_id'].eq(tableHBSchedule['id']))
                if bedsSchedule == 1:
                    cond.append(tableHBSchedule['code'].eq(1))
                elif bedsSchedule == 2:
                    cond.append(tableHBSchedule['code'].ne(1))

            if stacType == 0:
                cond.append(tableMAT['code'].inlist(['1', '2', '3', '7'])),
                cond.append(tableMAT['regionalCode'].notInlist(['111', '112'])),
            elif stacType == 1:
                cond.append(tableMAT['code'].inlist(['1', '2', '3']))
                cond.append(tableMAT['regionalCode'].notInlist(['111', '112'])),
            elif stacType == 2:
                cond.append(tableMAT['code'].eq('7'))

            if financeId:
                cond.append(tableContract['finance_id'].eq(financeId))

            if not permanentBed:
                cond.append(tableOSHB['isPermanent'].eq(1))

            if eventExpose:
                cond.append(tableEvent['expose'].eq(1))

            cols = u"""
            CASE 
                WHEN rbHospitalBedProfile.regionalCode = '1I' and OrgStructure.id is not NULL and Action.actionType_id in ({0}) THEN CONCAT(rbHospitalBedProfile.regionalCode,'ORIT')
                WHEN rbHospitalBedProfile.regionalCode in ('1G','1I','13') and (Diagnosis.mkb='U07.1' or Diagnosis.mkb='U07.2') and Action.actionType_id not in ({0}) THEN CONCAT(rbHospitalBedProfile.regionalCode,'COVID')
                WHEN Action.actionType_id not in ({0}) THEN rbHospitalBedProfile.regionalCode 
            END as profile,
            Contract.finance_id,
            IF(Client.birthDate > Event.setDate - interval 18 year, 1, 0) isChild,
                SUM(IF(ActionProperty_String.value not like 'умер%' or ActionProperty_String.value is null, 1, 0)) AS countAll, 
                CASE 
                    WHEN Event.setDate<'2022-01-01T00:00:00' THEN SUM(IF((ActionProperty_String.value not like 'умер%' or ActionProperty_String.value is null)
                        and (Client.sex = 1 and Client.birthDate <= Event.setDate - interval 60 year OR Client.sex = 2 and Client.birthDate <= Event.setDate - interval 55 year), 1, 0))
                    WHEN Event.setDate between '2022-01-01T00:00:00' and '2023-12-31T23:59:59' THEN SUM(IF((ActionProperty_String.value not like 'умер%' or ActionProperty_String.value is null)
                        and (Client.sex = 1 and Client.birthDate <= Event.setDate - interval 61 year OR Client.sex = 2 and Client.birthDate <= Event.setDate - interval 56 year), 1, 0))
                    WHEN Event.setDate>='2024-01-01T00:00:00' THEN SUM(IF((ActionProperty_String.value not like 'умер%' or ActionProperty_String.value is null)
                        and (Client.sex = 1 and Client.birthDate <= Event.setDate - interval 62 year OR Client.sex = 2 and Client.birthDate <= Event.setDate - interval 57 year), 1, 0)) 
                END as countSenior,
                SUM(IF(ActionProperty_String.value like 'переведен в дневной стационар%', 1, 0)) AS countTransfer,
                SUM(IF(ActionProperty_String.value like '%другой стационар%', 1, 0)) AS countOtherTransfer,
                SUM(IF(ActionProperty_String.value like 'умер%', 1, 0)) AS countDeath, 
                CASE 
                    WHEN Event.setDate<'2022-01-01T00:00:00' THEN SUM(IF((ActionProperty_String.value like 'умер%')
                        and (Client.sex = 1 and Client.birthDate <= Event.setDate - interval 60 year OR Client.sex = 2 and Client.birthDate <= Event.setDate - interval 55 year), 1, 0))
                    WHEN Event.setDate between '2022-01-01T00:00:00' and '2023-12-31T23:59:59' THEN SUM(IF((ActionProperty_String.value like 'умер%')
                        and (Client.sex = 1 and Client.birthDate <= Event.setDate - interval 61 year OR Client.sex = 2 and Client.birthDate <= Event.setDate - interval 56 year), 1, 0)) 
                    WHEN Event.setDate>='2024-01-01T00:00:00' THEN SUM(IF((ActionProperty_String.value like 'умер%')
                        and (Client.sex = 1 and Client.birthDate <= Event.setDate - interval 62 year OR Client.sex = 2 and Client.birthDate <= Event.setDate - interval 57 year), 1, 0)) 
                END as countDeathSenior""".format(','.join([ str(id) for id in actionTypeMovingList]) if actionTypeMovingList else 0)

            records = db.getRecordListGroupBy(queryTable, cols=cols, where=db.joinAnd(cond),
                                              group=['profile', 'Contract.finance_id', 'IF(Client.birthDate > Event.setDate - interval 18 year, 1, 0)'])
            return records

        # койко-дни (столбцы 15-16)
        def countBedDays(orgStructureIdList, bedsSchedule, begDateTime, endDateTime, stacType, financeId, permamentBed, eventExpose):
            cond = [tableEvent['deleted'].eq(0),
                    tableClient['deleted'].eq(0),
                    tableEvent['setDate'].le(endDateTime),
                    db.joinOr([tableEvent['execDate'].isNull(), tableEvent['execDate'].ge(begDateTime)]),
                    tableEventType['context'].notInlist(['relatedAction', 'inspection']),
                    tableEventType['code'].notInlist(['hospDir', 'egpuDisp', 'plng']),
                    tableOSHB['deleted'].eq(0)
                    ]
            actionTypeMovingList = getActionTypeIdListByFlatCode('moving%')
            queryTable = tableEvent.leftJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
            queryTable = queryTable.leftJoin(tableMAT, tableMAT['id'].eq(tableEventType['medicalAidType_id']))
            queryTable = queryTable.leftJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
            queryTable = queryTable.innerJoin(tableMovingAction,
                                              "MovingAction.id = (SELECT max(Action.id) FROM Action WHERE Action.event_id = Event.id AND Action.deleted = 0 AND Action.actionType_id IN ({0}))".format(
                                                  ','.join([ str(id) for id in actionTypeMovingList]) if actionTypeMovingList else 0))
            queryTable = queryTable.leftJoin(tableAPTHB, db.joinAnd(
                [tableAPTHB['actionType_id'].eq(tableMovingAction['actionType_id']),
                 tableAPTHB['name'].eq(u'койка'),
                 tableAPTHB['deleted'].eq(0)]))
            queryTable = queryTable.leftJoin(tableAPHB, db.joinAnd(
                [tableAPHB['type_id'].eq(tableAPTHB['id']),
                 tableAPHB['action_id'].eq(tableMovingAction['id']),
                 tableAPHB['deleted'].eq(0)]))
            queryTable = queryTable.leftJoin(tableAPVHB, tableAPVHB['id'].eq(tableAPHB['id']))
            queryTable = queryTable.leftJoin(tableOSHB, tableOSHB['id'].eq(tableAPVHB['value']))
            queryTable = queryTable.leftJoin(tableRbHospitalBedProfile, tableRbHospitalBedProfile['id'].eq(tableOSHB['profile_id']))
            queryTable = queryTable.leftJoin(tableContract, tableEvent['contract_id'].eq(tableContract['id']))
            queryTable = queryTable.leftJoin(tableDiagnostic,db.joinAnd( 
                                             [tableEvent['id'].eq(tableDiagnostic['event_id']),
                                              tableDiagnostic['diagnosisType_id'].eq(1),
                                              tableDiagnostic['deleted'].eq(0)]))
            queryTable = queryTable.leftJoin(tableDiagnosis, tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']))
            if orgStructureIdList:
                cond.append(tableOSHB['master_id'].inlist(orgStructureIdList))
            if bedsSchedule:
                queryTable = queryTable.innerJoin(tableHBSchedule, tableOSHB['schedule_id'].eq(tableHBSchedule['id']))
                if bedsSchedule == 1:
                    cond.append(tableHBSchedule['code'].eq(1))
                elif bedsSchedule == 2:
                    cond.append(tableHBSchedule['code'].ne(1))

            if stacType == 0:
                cond.append(tableMAT['code'].inlist(['1', '2', '3', '7'])),
                cond.append(tableMAT['regionalCode'].notInlist(['111', '112'])),
            elif stacType == 1:
                cond.append(tableMAT['code'].inlist(['1', '2', '3']))
                cond.append(tableMAT['regionalCode'].notInlist(['111', '112'])),
            elif stacType == 2:
                cond.append(tableMAT['code'].eq('7'))

            if financeId:
                cond.append(tableContract['finance_id'].eq(financeId))

            if not permamentBed:
                cond.append(tableOSHB['isPermanent'].eq(1))

            if eventExpose:
                cond.append(tableEvent['expose'].eq(1))

            cols = u'''
                        IF((Diagnosis.mkb='U07.1' or Diagnosis.mkb='U07.2') and rbHospitalBedProfile.regionalCode in ('1G','1I','13'), CONCAT(rbHospitalBedProfile.regionalCode,'COVID'), rbHospitalBedProfile.regionalCode) as profile,
                        Contract.finance_id,
                        IF(Client.birthDate > Event.setDate - interval 18 year, 1, 0) as isChild,
                        WorkDays(IF(Event.setDate < {begDate}, {begDate}, Event.setDate), IF(IFNULL(Event.execDate, {endDate}) >= {endDate}, {endDate}, Event.execDate), EventType.weekProfileCode, rbMedicalAidType.regionalCode) AS dayCount,
                        CASE 
                            WHEN Event.setDate<'2022-01-01T00:00:00' THEN IF(Client.sex = 1 and Client.birthDate <= Event.setDate - interval 60 year OR Client.sex = 2 and Client.birthDate <= Event.setDate - interval 55 year, 1, 0) 
                            WHEN Event.setDate between '2022-01-01T00:00:00' and '2023-12-31T23:59:59' THEN IF(Client.sex = 1 and Client.birthDate <= Event.setDate - interval 61 year OR Client.sex = 2 and Client.birthDate <= Event.setDate - interval 56 year, 1, 0) 
                            WHEN Event.setDate>='2024-01-01T00:00:00' THEN IF(Client.sex = 1 and Client.birthDate <= Event.setDate - interval 62 year OR Client.sex = 2 and Client.birthDate <= Event.setDate - interval 57 year, 1, 0) 
                        END as isSenior '''.format(
                begDate=db.formatDate(forceDateTime(begDateTime)),
                endDate=db.formatDate(forceDateTime(endDateTime)))

            stmt = db.selectStmt(queryTable, cols, where=cond)
            query = db.query(stmt)
            mapProfileCountDays = {}
            while query.next():
                record = query.record()
                ageCond = ''
                profile = forceString(record.value('profile'))
                isChild = forceBool(record.value('isChild'))
                dayCount = forceInt(record.value('dayCount'))
                _financeId = forceRef(record.value('finance_id'))
                if profile in profileWithAgeList:
                    ageCond = '<18' if isChild else '>=18'
                if not profile:
                    profile = 'NOPROFILE'
                keys = [(profile, ageCond)]
                if _financeId == CFinanceType.cash:
                    keys.append(('CASH', ''))
                for key in keys:
                    days = mapProfileCountDays.setdefault(key, [0,0])
                    mapProfileCountDays[key][0] = days[0] + dayCount
                    if forceBool(record.value('isSenior')):
                        mapProfileCountDays[key][1] = days[1] + dayCount
            return mapProfileCountDays


        # реанимационные койко-дни (столбцы 15-16)
        def countReanimBedDays(orgStructureIdList, bedsSchedule, begDateTime, endDateTime, stacType, financeId, permamentBed, eventExpose):
            cond = [tableEvent['deleted'].eq(0),
                    tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode('moving%')),
                    tableClient['deleted'].eq(0),
                    tableAction['deleted'].eq(0),
                    tableAction['begDate'].le(endDateTime),
                    db.joinOr([tableAction['endDate'].isNull(), tableAction['endDate'].ge(begDateTime)]),
                    tableRbHospitalBedProfile['regionalCode'].inlist(reanimProfiles),
                    tableEventType['context'].notInlist(['relatedAction', 'inspection']),
                    tableEventType['code'].notInlist(['hospDir', 'egpuDisp', 'plng']),
                    tableOSHB['deleted'].eq(0),
                    ]
            queryTable = tableEvent.leftJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
            queryTable = queryTable.leftJoin(tableMAT, tableMAT['id'].eq(tableEventType['medicalAidType_id']))
            queryTable = queryTable.leftJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
            queryTable = queryTable.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.leftJoin(tableAPTHB, db.joinAnd(
                [tableAPTHB['actionType_id'].eq(tableAction['actionType_id']),
                 tableAPTHB['name'].eq(u'койка'),
                 tableAPTHB['deleted'].eq(0)]))
            queryTable = queryTable.leftJoin(tableAPHB, db.joinAnd(
                [tableAPHB['type_id'].eq(tableAPTHB['id']),
                 tableAPHB['action_id'].eq(tableAction['id']),
                 tableAPHB['deleted'].eq(0)]))
            queryTable = queryTable.leftJoin(tableAPVHB, tableAPVHB['id'].eq(tableAPHB['id']))
            queryTable = queryTable.leftJoin(tableOSHB, tableOSHB['id'].eq(tableAPVHB['value']))
            queryTable = queryTable.leftJoin(tableRbHospitalBedProfile,
                                             tableRbHospitalBedProfile['id'].eq(tableOSHB['profile_id']))
            queryTable = queryTable.leftJoin(tableDiagnostic,db.joinAnd( 
                                             [tableEvent['id'].eq(tableDiagnostic['event_id']),
                                              tableDiagnostic['diagnosisType_id'].eq(1),
                                              tableDiagnostic['deleted'].eq(0)]))
            queryTable = queryTable.leftJoin(tableDiagnosis, tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']))
            if orgStructureIdList:
                cond.append(tableOSHB['master_id'].inlist(orgStructureIdList))
            if bedsSchedule:
                queryTable = queryTable.innerJoin(tableHBSchedule,
                                                  tableOSHB['schedule_id'].eq(tableHBSchedule['id']))
                if bedsSchedule == 1:
                    cond.append(tableHBSchedule['code'].eq(1))
                elif bedsSchedule == 2:
                    cond.append(tableHBSchedule['code'].ne(1))

            if stacType == 0:
                tableMAT['code'].inlist(['1', '2', '3', '7']),
                tableMAT['regionalCode'].notInlist(['111', '112']),
            elif stacType == 1:
                cond.append(tableMAT['code'].inlist(['1', '2', '3']))
                tableMAT['regionalCode'].notInlist(['111', '112']),
            elif stacType == 2:
                cond.append(tableMAT['code'].eq('7'))

            if financeId:
                queryTable = queryTable.innerJoin(tableContract, tableEvent['contract_id'].eq(tableContract['id']))
                cond.append(tableContract['finance_id'].eq(financeId))

            if not permamentBed:
                cond.append(tableOSHB['isPermanent'].eq(1))

            if eventExpose:
                cond.append(tableEvent['expose'].eq(1))

            cols = u'''     
                            IF((Diagnosis.mkb='U07.1' or Diagnosis.mkb='U07.2') and rbHospitalBedProfile.regionalCode in ('1G','1I','13'), CONCAT(rbHospitalBedProfile.regionalCode,'COVID'), rbHospitalBedProfile.regionalCode) as profile,
                            WorkDays(IF(Action.begDate < {begDate}, {begDate}, Action.begDate), IF(IFNULL(Action.endDate, {endDate}) >= {endDate}, {endDate}, Action.endDate), EventType.weekProfileCode, rbMedicalAidType.regionalCode)  AS dayCount,
                            CASE 
                                WHEN Event.setDate<'2022-01-01T00:00:00' THEN IF(Client.sex = 1 and Client.birthDate <= Event.setDate - interval 60 year OR Client.sex = 2 and Client.birthDate <= Event.setDate - interval 55 year, 1, 0) 
                                WHEN Event.setDate between '2022-01-01T00:00:00' and '2023-12-31T23:59:59' THEN IF(Client.sex = 1 and Client.birthDate <= Event.setDate - interval 61 year OR Client.sex = 2 and Client.birthDate <= Event.setDate - interval 56 year, 1, 0) 
                                WHEN Event.setDate>='2024-01-01T00:00:00' THEN IF(Client.sex = 1 and Client.birthDate <= Event.setDate - interval 62 year OR Client.sex = 2 and Client.birthDate <= Event.setDate - interval 57 year, 1, 0) 
                            END as isSenior '''.format(
                begDate=db.formatDate(forceDateTime(begDateTime)),
                endDate=db.formatDate(forceDateTime(endDateTime)))

            stmt = db.selectStmt(queryTable, cols, where=cond)
            query = db.query(stmt)
            mapProfileCountDays = {}
            while query.next():
                record = query.record()
                profile = forceString(record.value('profile'))
                dayCount = forceInt(record.value('dayCount'))
                days = mapProfileCountDays.setdefault((profile, ''), [0, 0])
                mapProfileCountDays[(profile, '')][0] = days[0] + dayCount
                if forceBool(record.value('isSenior')):
                    mapProfileCountDays[(profile, '')][1] = days[1] + dayCount
            return mapProfileCountDays


        # койко-дни закрытия на ремонт (столбец 17)
        def involuteBedDays(orgStructureIdList, bedsSchedule, begDatePeriod, endDatePeriod, permamentBed):
            cols = [tableRbHospitalBedProfile['regionalCode'], tableOSHBI['begDate'], tableOSHBI['endDate'],
                    u'''IF(cast(case when OrgStructure_HospitalBed.age like '%-%г' then substring_index(OrgStructure_HospitalBed.age, '-', -1)
                                                         when OrgStructure_HospitalBed.age like '%-%м' then FLOOR(substring_index(OrgStructure_HospitalBed.age, '-', -1)/12)
                                                         when OrgStructure_HospitalBed.age like '%-%д' then FLOOR(substring_index(OrgStructure_HospitalBed.age, '-', -1)/365)
                                                         else 150 end as unsigned integer) < 18, 1, 0) as isChild'''
                    ]
            queryTable = tableOS.leftJoin(tableOSHB, tableOSHB['master_id'].eq(tableOS['id']))
            queryTable = queryTable.leftJoin(tableRbHospitalBedProfile, tableRbHospitalBedProfile['id'].eq(tableOSHB['profile_id']))
            queryTable = queryTable.leftJoin(tableOSHBI, tableOSHBI['master_id'].eq(tableOSHB['id']))
            cond = [tableOS['deleted'].eq(0),
                    tableOSHB['deleted'].eq(0),
                    tableOSHBI['involutionType'].eq(1),
                    db.joinOr([tableOSHB['begDate'].isNull(),
                               db.joinAnd([tableOSHB['begDate'].isNotNull(), tableOSHB['begDate'].le(begDatePeriod)])]),
                    db.joinOr([tableOSHB['endDate'].isNull(),
                               db.joinAnd([tableOSHB['endDate'].isNotNull(), tableOSHB['endDate'].ge(endDatePeriod)])]),
                    tableOSHBI['begDate'].le(endDatePeriod),
                    db.joinOr([tableOSHBI['endDate'].isNull(),
                               db.joinAnd([tableOSHBI['endDate'].isNotNull(), tableOSHBI['endDate'].ge(begDatePeriod)])])
                    ]
            if not permamentBed:
                cond.append(tableOSHB['isPermanent'].eq(1))
            if orgStructureIdList:
                cond.append(tableOSHB['master_id'].inlist(orgStructureIdList))
            if bedsSchedule:
                queryTable = queryTable.innerJoin(tableHBSchedule, tableOSHB['schedule_id'].eq(tableHBSchedule['id']))
                if bedsSchedule == 1:
                    cond.append(tableHBSchedule['code'].eq(1))
                elif bedsSchedule == 2:
                    cond.append(tableHBSchedule['code'].ne(1))

            stmt = db.selectStmt(queryTable, cols, where=cond)
            query = db.query(stmt)
            mapProfileInvoluteDays = {}

            while query.next():
                record = query.record()
                ageCond = ''
                profile = forceString(record.value('regionalCode'))
                isChild = forceBool(record.value('isChild'))
                begDate = forceDate(record.value('begDate'))
                endDate = forceDate(record.value('endDate'))
                if begDate < begDateTime.date():
                    begDate = begDateTime.date()
                if endDate > endDateTime.date():
                    endDate = endDateTime.date()

                if profile in profileWithAgeList:
                    ageCond = '<18' if isChild else '>=18'
                if not profile:
                    profile = 'NOPROFILE'
                days = mapProfileInvoluteDays.setdefault((profile, ageCond), 0)
                days += begDate.daysTo(endDate) + 1
                mapProfileInvoluteDays[(profile, ageCond)] = days
            return mapProfileInvoluteDays


        mapMainRows = createMapCodeToRowIdx([row[3] for row in MainRows3100])
        profileWithAgeList = [key[0] for key in mapMainRows.keys() if key[1]]
        rowSize = 15
        reportMainData = [[0] * rowSize for row in xrange(len(MainRows3100))]

        endDate = params.get('endDate', QDate())
        begDate = params.get('begDate', QDate())
        financeId = params.get('financeId', None)
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
        isPermanentBed = params.get('permanentBed', False)
        if params.get('orgStructureId', None):
            orgStructureIndex = self.stationaryF30KKSetupDialog.cmbOrgStructure._model.index(self.stationaryF30KKSetupDialog.cmbOrgStructure.currentIndex(), 0, self.stationaryF30KKSetupDialog.cmbOrgStructure.rootModelIndex())
            begOrgStructureIdList = self.getOrgStructureIdList(orgStructureIndex)
        else:
            begOrgStructureIdList = None
        stacType = params.get('stacType', 0)
        addressType = params.get('addressType', 0)
        eventExpose = params.get('eventExpose', False)

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertBlock()
        self.getCaption(cursor, params, u'1. Коечный фонд и его использование')
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        cursor.insertBlock()
        splitTitle(cursor, u'(3100)', u'Коды по ОКЕИ: койка - 911; койко-день - 9111; человек - 792')
        cursor.setCharFormat(CReportBase.ReportBody)
        cols = [('10%', [u'Профиль коек', u'', u'', u'', u'1'], CReportBase.AlignLeft),
                ('2%', [u'№ строки', u'', u'', u'', u'2'], CReportBase.AlignCenter),
                ('6%', [u'Число коек, фактически развернутых и свернутых на ремонт', u'на конец отчетного года', u'', u'', u'3'], CReportBase.AlignRight),
                ('6%', [u'', u'из них: расположенных в сельской местности', u'', u'', u'4'], CReportBase.AlignRight),
                ('6%', [u'', u'среднегодовых', u'', u'', u'5'], CReportBase.AlignRight),
                ('6%', [u'В отчетном году', u'поступило больных - всего, чел.', u'', u'', u'6'], CReportBase.AlignRight),
                ('6%', [u'', u'из них сельских жителей', u'', u'', u'7'], CReportBase.AlignRight),
                ('6%', [u'', u'из общего числа поступивших (из гр.6)', u'0–17 лет (включительно)', u'', u'8'], CReportBase.AlignRight),
                ('6%', [u'', u'', u'старше трудоспособного возраста', u'', u'9'], CReportBase.AlignRight),
                ('6%', [u'', u'выписано пациентов, чел.', u'всего', u'', u'10'], CReportBase.AlignRight),
                ('6%', [u'', u'', u'в том числе старше трудоспособного возраста', u'', u'11'], CReportBase.AlignRight),
                ('6%', [u'', u'из них в дневные стационары (всех типов)', u'', u'', u'12'], CReportBase.AlignRight),
                ('6%', [u'', u'умерло, чел.', u'всего', u'', u'13'], CReportBase.AlignRight),
                ('6%', [u'', u'', u'в том числе старше трудоспособного возраста', u'', u'14'], CReportBase.AlignRight),
                ('6%', [u'Проведено пациентами койко-дней', u'всего', u'', u'', u'15'], CReportBase.AlignRight),
                ('6%', [u'', u'в том числе старше трудоспособного возраста', u'', u'', u'16'], CReportBase.AlignRight),
                ('6%', [u'Койко-дни закрытия на ремонт', u'', u'', u'', u'17'], CReportBase.AlignRight)
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

        # вычисление столбца 3
        records = getPermamentHospitalBeds(begOrgStructureIdList, bedsSchedule, begDate, endDate, isPermanentBed)
        for record in records:
            ageCond = ''
            profile = forceString(record.value('regionalCode'))
            isChild = forceBool(record.value('isChild'))
            cnt = forceInt(record.value('cnt'))

            if profile in profileWithAgeList:
                ageCond = '<18' if isChild else '>=18'
            if not profile:
                profile = 'NOPROFILE'
            rows = mapMainRows.get((profile, ageCond), [])[:]
            rows.append(0)
            for row in rows:
                reportLine = reportMainData[row]
                reportLine[0] += cnt

        # вычисление столбца 5
        mapProfileDays = averageDaysHospitalBed(begOrgStructureIdList, bedsSchedule, begDate, endDate, isPermanentBed)
        period = begDate.daysTo(endDate)
        for key in mapProfileDays.keys():
            rows = mapMainRows.get(key, [])[:]
            daysMonths = mapProfileDays[key] / (period if period > 0 else 1)
            rows.append(0)
            for row in rows:
                reportLine = reportMainData[row]
                reportLine[1] += daysMonths

        # вычисление стобцов 6-9
        records = getReceived(begOrgStructureIdList, bedsSchedule, begDateTime, endDateTime, stacType, financeId, addressType, isPermanentBed, eventExpose)
        for record in records:
            ageCond = ''
            profile = forceString(record.value('profile'))
            isChild = forceBool(record.value('isChild'))
            countAll = forceInt(record.value('countAll'))
            countVillager = forceInt(record.value('countVillager'))
            countChild = forceInt(record.value('countChild'))
            countSenior = forceInt(record.value('countSenior'))
            _financeId = forceRef(record.value('finance_id'))

            if profile in profileWithAgeList:
                ageCond = '<18' if isChild else '>=18'
            if not profile:
                profile = 'NOPROFILE'
            rows = mapMainRows.get((profile, ageCond), [])[:]
            if not profile == '1IORIT':
                rows.append(0)
            if _financeId == CFinanceType.cash:
                rows.extend(mapMainRows.get(('CASH', ''), [])[:])
            for row in rows:
                reportLine = reportMainData[row]
                reportLine[2] += countAll
                reportLine[3] += countVillager
                reportLine[4] += countChild
                reportLine[5] += countSenior

        # вычисление стобцов 10-14
        records = getLeaved(begOrgStructureIdList, bedsSchedule, begDateTime, endDateTime, stacType, financeId, isPermanentBed, eventExpose)
        countTransfer3101 = 0
        for record in records:
            ageCond = ''
            profile = forceString(record.value('profile'))
            isChild = forceBool(record.value('isChild'))
            _financeId = forceRef(record.value('finance_id'))
            countAll = forceInt(record.value('countAll'))
            countSenior = forceInt(record.value('countSenior'))
            countTransfer = forceInt(record.value('countTransfer'))
            countOtherTransfer = forceInt(record.value('countOtherTransfer'))
            countDeath = forceInt(record.value('countDeath'))
            countDeathSenior = forceInt(record.value('countDeathSenior'))
            countTransfer3101 += countOtherTransfer
            if profile in profileWithAgeList:
                ageCond = '<18' if isChild else '>=18'
            if not profile:
                profile = 'NOPROFILE'
            rows = mapMainRows.get((profile, ageCond), [])[:]
            if not profile == '1IORIT':
                rows.append(0)
            if _financeId == CFinanceType.cash:
                rows.extend(mapMainRows.get(('CASH', ''), [])[:])
            for row in rows:
                reportLine = reportMainData[row]
                reportLine[6] += countAll
                reportLine[7] += countSenior
                reportLine[8] += countTransfer
                reportLine[9] += countDeath
                reportLine[10] += countDeathSenior

        # вычисление столбцов 15-16
        mapProfileCountDays = countBedDays(begOrgStructureIdList, bedsSchedule, begDateTime, endDateTime, stacType, financeId, isPermanentBed, eventExpose)
        for key in mapProfileCountDays.keys():
            if key[0] in reanimProfiles:
                continue
            rows = mapMainRows.get(key, [])[:]
            days = mapProfileCountDays[key]
            if key[0] != 'CASH':
                rows.append(0)
            for row in rows:
                reportLine = reportMainData[row]
                reportLine[11] += days[0]
                reportLine[12] += days[1]

        mapProfileCountDays = countReanimBedDays(begOrgStructureIdList, bedsSchedule, begDateTime, endDateTime, stacType, financeId, isPermanentBed, eventExpose)
        for key in mapProfileCountDays.keys():
            rows = mapMainRows.get(key, [])[:]
            days = mapProfileCountDays[key]
            for row in rows:
                reportLine = reportMainData[row]
                reportLine[11] += days[0]
                reportLine[12] += days[1]

        # вычисление столбца 17
        mapProfileInvoluteDays = involuteBedDays(begOrgStructureIdList, bedsSchedule, begDateTime, endDateTime, isPermanentBed)
        for key in mapProfileInvoluteDays.keys():
            rows = mapMainRows.get(key, [])[:]
            days = mapProfileInvoluteDays[key]
            rows.append(0)
            for row in rows:
                reportLine = reportMainData[row]
                reportLine[13] += days

        t = QtGui.QTextBlockFormat()
        for row, rowDescr in enumerate(MainRows3100):
            i = table.addRow()
            t.setLeftMargin(rowDescr[0] * 10)
            table.setText(i, 0, rowDescr[1], blockFormat=t)
            table.setText(i, 1, rowDescr[2])
            if rowDescr[2] in ['78']:
                continue
            reportLine = reportMainData[row]
            table.setText(i, 2, reportLine[0])
            table.setText(i, 4, reportLine[1])
            table.setText(i, 5, reportLine[2])
            table.setText(i, 6, reportLine[3])
            table.setText(i, 7, reportLine[4])
            table.setText(i, 8, reportLine[5])
            table.setText(i, 9, reportLine[6])
            table.setText(i, 10, reportLine[7])
            table.setText(i, 11, reportLine[8])
            table.setText(i, 12, reportLine[9])
            table.setText(i, 13, reportLine[10])
            table.setText(i, 14, reportLine[11])
            table.setText(i, 15, reportLine[12])
            table.setText(i, 16, reportLine[13])

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertBlock()
        splitTitle(cursor, u'(3101)', u'Код по ОКЕИ: человек - 792')
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertText(u"Из числа выписанных (гр. 10, стр. 1 табл. 3100) переведено в другие стационары: {0}".format(countTransfer3101))
        return doc


def createMapCodeToRowIdx(codesList):
    mapCodeToRowIdx = {}
    for rowIdx, code in enumerate(codesList):
        if code:
            parseRowCodes(rowIdx, str(code), mapCodeToRowIdx)
    return mapCodeToRowIdx


def parseRowCodes(rowIdx, codes, mapCodesToRowIdx):
    profileRanges = codes.split(';')
    for profileRange in profileRanges:
        profileLimit = profileRange.split('-')
        n = len(profileLimit)
        if n == 1 and profileLimit[0]:
            code, postfix = normalizeCode(profileLimit[0])
            mapCodesToRowIdx.setdefault((code, postfix), []).append(rowIdx)
        elif n == 2:
            lowCode, postfix = normalizeCode(profileLimit[0])
            highCode, postfix = normalizeCode(profileLimit[1])
            if lowCode[0] == highCode[0]:
                for i in xrange(ord(lowCode[1]), ord(highCode[1]) + 1):
                    code = lowCode[0] + chr(i)
                    mapCodesToRowIdx.setdefault((code, postfix), []).append(rowIdx)
        else:
            assert False, 'Wrong codes range "'+profileRange+'"';

def normalizeCode(code):
    code = code.strip().upper()
    postfix = ''
    if re.match('\w{2,2}<18$', code) is not None:
        code = code[:-3]
        postfix = '<18'
    elif re.match('\w{2,2}>=18$', code) is not None:
        code = code[:-4]
        postfix = '>=18'
    return code, postfix

def splitTitle(cursor, t1, t2):
    cursor.movePosition(QtGui.QTextCursor.End)
    cursor.insertBlock()
    html = u'''
<table width="100%%">
<tr>
    <td align="left"><h5>%s</h5></td>
    <td align="right"><h5>%s</h5></td>
</tr>
</table>
    ''' % (t1,t2)
    cursor.insertHtml(html)
    cursor.insertBlock()