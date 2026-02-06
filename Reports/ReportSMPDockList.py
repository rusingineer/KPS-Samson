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
from PyQt4.QtCore import QDate

from Reports.Report import CReport
from Reports.ReportBase import CReportBase, createTable
from Reports.ReportView import CPageFormat
from Reports.Ui_ReportSMPDockList import Ui_ReportSMPDockList
from datetime import datetime

from library.Utils import *


def selectData(params):
    begDate = params.get('begDate', None)
    endDate = params.get('endDate', None)
    orgStructureId = params.get('OrgStructureId', None)
    NMP = params.get('NMP', None)
    SMP = params.get('SMP', None)
    doctorCome = params.get('doctorCome', None)
    ageGroup = params.get('ageGroup', None)
    db = QtGui.qApp.db
    tableCallInfo = db.table('smp_callinfo').alias('callInfo')
    tableEventItem = db.table('smp_eventitem').alias('eventItem')
    tableEventType = db.table('smp_sprcalleventtype').alias('smp_eventType')
    tableOrgStructure = db.table('OrgStructure').alias('orgStruct')

    cond = [
        tableCallInfo['callDate'].le(endDate),
        tableCallInfo['callDate'].ge(begDate)
    ]

    if orgStructureId:
            setOrgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', orgStructureId)
            setBookkeeperCodeList = []
            records = db.getDistinctRecordList(tableOrgStructure, tableOrgStructure['bookkeeperCode'],
                                               tableOrgStructure['id'].inlist(setOrgStructureIdList))
            for record in records:
                bkCode = forceString(record.value('bookkeeperCode'))
                if bkCode:
                    setBookkeeperCodeList.append(bkCode)

            cond.append(tableCallInfo['OMS_CODE'].inlist(setBookkeeperCodeList))


    typeList = []
    if NMP:
        typeList.append(0)
    if SMP:
        typeList.append(1)
    if doctorCome:
        typeList.append(2)
    if typeList:
        cond.append(tableCallInfo['Type'].inlist(typeList))

    if ageGroup == 1:
        cond.append(tableCallInfo['ageYears'].lt(18))
    elif ageGroup == 2:
        cond.append(tableCallInfo['ageYears'].ge(18))


    queryTable = tableCallInfo
    queryTable = queryTable.leftJoin(tableEventItem, (tableEventItem['idCallNumber'].eq(tableCallInfo['idCallNumber'])))
    queryTable = queryTable.leftJoin(tableEventType,
                                     tableEventType['id'].eq(tableEventItem['idCallEventType']))


    cols = [
        tableCallInfo['callDate'],
        tableCallInfo['endReceivingCall'],
        tableCallInfo['lastName'],
        tableCallInfo['name'],
        tableCallInfo['patronymic'],
        tableCallInfo['sex'],
        tableCallInfo['ageYears'],
        tableCallInfo['ageMonths'],
        tableCallInfo['ageDays'],
        tableCallInfo['diseaseBasic'],
        tableCallInfo['callOccasion'],
        tableCallInfo['settlement'],
        tableCallInfo['street'],
        tableCallInfo['house'],
        tableCallInfo['houseFract'],
        tableCallInfo['building'],
        tableCallInfo['flat'],
        tableCallInfo['porch'],
        tableCallInfo['porchCode'],
        tableCallInfo['floor'],
        tableCallInfo['landmarks'],
        tableCallInfo['telephone'],
        tableCallInfo['active_visit_item_info'].alias('info'),
        tableEventType['Name'].alias('eventName'),
        tableCallInfo['Type'],
        tableCallInfo['idCallNumber'],
        tableCallInfo['OMS_CODE'],
        tableEventItem['transferUser']

    ]

    stmt = db.selectStmtGroupBy(queryTable, cols, cond, group='callInfo.idCallNumber',
                                order='callDate, endReceivingCall')
    return db.query(stmt)

class CReportSMPDockList(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Отчёт о количестве вызовов СМП/НМП')
        self.pageFormat = CPageFormat(pageSize=CPageFormat.A4, orientation=CPageFormat.Landscape, leftMargin=1,
                                      topMargin=1, rightMargin=1, bottomMargin=1)

    def getSetupDialog(self, parent):
        result = CReportSMPDockListDialog(parent)
        result.setTitle(self.title())

        return result

    def getDescription(self, params):
        db = QtGui.qApp.db

        begDate = params.get('begDate', None)
        endDate = params.get('endDate', None)
        setOrgStructureId = params.get('OrgStructureId', None)

        NMP = params.get('NMP', None)
        SMP = params.get('SMP', None)
        doctorCome = params.get('doctorCome', None)
        typeList = []
        if NMP:
            typeList.append(u'НМП')
        if SMP:
            typeList.append(u'03')
        if doctorCome:
            typeList.append(u'СМП (Актив.)')
        ageGroup = params.get('ageGroup', None)

        rows = []
        if begDate:
            rows.append(u'Начальная дата периода: %s' % forceString(begDate))
        if endDate:
            rows.append(u'Конечная дата периода: %s' % forceString(endDate))
        if ageGroup == 1:
            rows.append(u'Возраст: Дети (0-17)')
        elif ageGroup == 2:
            rows.append(u'Возраст: Взрослые (18 и старше)')
        if setOrgStructureId:
            rows.append(u'Подразделение: %s' % forceString(
                db.translate('OrgStructure', 'id', setOrgStructureId, 'CONCAT_WS(\' | \', code,name)')))
        if typeList:
            rows.append(u'Типы вызовов: %s' % ' ,'.join(typeList))
        return rows

    def formatAge(self, record):
        age = []
        ageParts = [
            ('ageYears', (u'год', u'года', u'лет')),
            ('ageMonths', (u'месяц', u'месяца', u'месяцев')),
            ('ageDays', (u'день', u'дня', u'дней'))
        ]
        for partName, words in ageParts:
            part = record.value(partName)
            if not part.isNull():
                part = forceInt(part)
                age.append(u'%d %s' % (part, agreeNumberAndWord(part, words)))
        if age:
            return ', '.join(age)
        return ''

    def formatAddress(self, record):
        settlement = forceString(record.value('settlement'))
        street = forceString(record.value('street'))
        house = forceString(record.value('house'))
        houseFract = forceString(record.value('houseFract'))
        building = forceString(record.value('building'))
        flat = forceString(record.value('flat'))
        porch = forceString(record.value('porch'))
        porchCode = forceString(record.value('porchCode'))
        floor = forceString(record.value('floor'))
        landmarks = forceString(record.value('landmarks'))

        addressParts = []

        if settlement:
            addressParts.append(settlement)
        if street:
            addressParts.append(u" {0}".format(street))
        if house and house != 0:
            addressParts.append(u"д. {0}".format(house))
        if houseFract and houseFract != 0:
            addressParts.append(houseFract)
        if building and building != 0:
            addressParts.append(u"корп. {0}".format(building))
        if flat and flat != 0:
            addressParts.append(u"кв. {0}".format(flat))
        if porch and porch != "0":
            addressParts.append(u"подъезд {0}".format(porch))
        if porchCode and porchCode != 0:
            addressParts.append(u"код домофона {0}".format(porchCode))
        if floor and floor != "0":
            addressParts.append(u"этаж {0}".format(floor))
        if landmarks:
            addressParts.append(u"ориентир: {0}".format(landmarks))

        return ", ".join(part for part in addressParts if part)


    def extractDiagnosis(self, text):
        pattern = u"<b>Основной диагноз:</b> ([^<]+)"
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
        return ''

    def extractComplaints(self, text):
        pattern = u"<b>Жалобы:</b> ([^<]+)"
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
        return ''

    def extractClientBirthDate(self, text):
        pattern = u"<b>Дата рождения:</b> ([^<]+)"
        match = re.search(pattern, text)
        if not match:
            return ''

        dateStr = match.group(1).strip()
        try:
            birthDate = datetime.datetime.strptime(dateStr, "%d.%m.%Y")
            return birthDate.strftime("%Y-%m-%d")
        except ValueError:
            return ''

    def findClientId(self, lastName, firstName, patrName, birthDate):
        db = QtGui.qApp.db
        table = db.table('Client')
        cond = [
            table['lastName'].eq(lastName),
            table['firstName'].eq(firstName),
            table['patrName'].eq(patrName),
            table['birthDate'].dateEq(birthDate),
            table['deleted'].eq(0)
        ]

        record = db.getRecordEx(table, 'id', cond)
        if record:
            return forceInt(record.value('id'))
        else:
            return ''

    def findClientAttach(self, clientId):
        db = QtGui.qApp.db
        tableClient = db.table('Client')
        tableClientAttach = db.table('ClientAttach')
        tableOrgStructure = db.table('OrgStructure')
        cond = [
            tableClient['id'].eq(clientId),
            tableClient['deleted'].eq(0),
            tableClientAttach['deleted'].eq(0),

        ]

        queryTable = tableClient.innerJoin(tableClientAttach, tableClientAttach['client_id'].eq(tableClient['id']))
        queryTable = queryTable.innerJoin(tableOrgStructure, tableOrgStructure['id'].eq(tableClientAttach['orgStructure_id']))

        record = db.getRecordEx(queryTable, tableOrgStructure['name'], cond)
        if record:
            return forceString(record.value('name'))
        else:
            return ''





    def build(self, params):
        showEventName = params.get('showEventName', False)
        showCallOccasion = params.get('showCallOccasion', False)
        showDiseaseBasic = params.get('showDiseaseBasic', False)
        showComplaints = params.get('showComplaints', False)
        query = selectData(params)
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportSubTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        tableColumns = [
            ('5%', [u'№'], CReportBase.AlignRight),
            ('5%', [u'Тип вызова'], CReportBase.AlignLeft),
            ('5%', [u'Дата вызова'], CReportBase.AlignLeft),
            ('5%', [u'Время приёма вызова'], CReportBase.AlignLeft),
            ('5%', [u'Код пациента'], CReportBase.AlignLeft),
            ('15%', [u'ФИО'], CReportBase.AlignLeft),
            ('2%', [u'Пол'], CReportBase.AlignLeft),
            ('5%', [u'Возраст'], CReportBase.AlignLeft),
            ('20%', [u'Адрес'], CReportBase.AlignLeft),
            ('10%', [u'Телефон'], CReportBase.AlignLeft),
            ('10%', [u'Код ОМС'], CReportBase.AlignLeft),
            ('10%', [u'Участок'], CReportBase.AlignLeft),
            ('10%', [u'ФИО передавшего вызов'], CReportBase.AlignLeft)
        ]

        index = 8
        if showDiseaseBasic:
            tableColumns.insert(index, ('15%', [u'Основной диагноз'], CReportBase.AlignLeft))
            index += 1
        if showComplaints:
            tableColumns.insert(index, ('10%', [u'Жалобы'], CReportBase.AlignLeft))
            index += 1
        if showCallOccasion:
            tableColumns.insert(index, ('15%', [u'Повод к вызову'], CReportBase.AlignLeft))
        if showEventName:
            tableColumns.append(('%10', [u'Статус вызова'], CReportBase.AlignLeft))


        table = createTable(cursor, tableColumns)
        n = 1
        while query.next():
            record = query.record()
            tableRow = table.addRow()
            type_rec = record.value('Type').toInt()[0]
            type_name = ''
            if type_rec == 0:
                type_name = u'НМП'
            elif type_rec == 1:
                type_name = u'03'
            elif type_rec == 2:
                type_name = u'СМП (Актив.)'
            birthDate = self.extractClientBirthDate(forceString(record.value('info')))
            clientId = self.findClientId(forceString(record.value('lastName')), forceString(record.value('name')),
                                                  forceString(record.value('patronymic')), birthDate)

            shift = 0
            table.setText(tableRow, 0, n)
            table.setText(tableRow, 1, type_name)
            table.setText(tableRow, 2, forceString(record.value('callDate')))
            table.setText(tableRow, 3, forceString(record.value('endReceivingCall')))
            table.setText(tableRow, 4, forceString(clientId))
            table.setText(tableRow, 5, formatName(forceString(record.value('lastName')),
                                                  forceString(record.value('name')),
                                                  forceString(record.value('patronymic'))))
            table.setText(tableRow, 6, forceString(record.value('sex')))
            table.setText(tableRow, 7, self.formatAge(record))

            if showDiseaseBasic:
                if forceString(record.value('diseaseBasic')) == '' and type_rec == 2:
                    table.setText(tableRow, 8, self.extractDiagnosis(forceString(record.value('info'))))
                else:
                    table.setText(tableRow, 8, forceString(record.value('diseaseBasic')))
                shift += 1
            if showComplaints:
                table.setText(tableRow, 8 + shift, self.extractComplaints(forceString(record.value('info'))))
                shift += 1
            if showCallOccasion:
                table.setText(tableRow, 8 + shift, forceString(record.value('callOccasion')))
                shift += 1
            table.setText(tableRow, 8 + shift, self.formatAddress(record))
            table.setText(tableRow, 9 + shift, forceString(record.value('telephone')))
            table.setText(tableRow, 10 + shift, forceString(record.value('OMS_CODE')))
            table.setText(tableRow, 11 + shift, self.findClientAttach(clientId))
            table.setText(tableRow, 12 + shift, forceString(record.value('transferUser')))
            if showEventName:
                table.setText(tableRow, 13 + shift, forceString(record.value('eventName')))

            n += 1

        return doc

class CReportSMPDockListDialog(QtGui.QDialog, Ui_ReportSMPDockList):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)

        self.setupUi(self)
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())
        self.chbNMP.setChecked(True)
        self.chb03.setChecked(True)
        self.chbDoctorCome.setChecked(True)
        self.chbShowEventName.setChecked(True)
        self.chbShowCallOccasion.setChecked(True)
        self.chbShowDiseaseBasic.setChecked(True)
        self.chbShowComplaints.setChecked(True)

    def setTitle(self, title):
        self.setWindowTitle(title)

    def setParams(self, params):
        date = QDate.currentDate()
        self.edtBegDate.setDate(params.get('begDate', date))
        self.edtEndDate.setDate(params.get('endDate', date))


    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['OrgStructureId'] = self.cmbOrgStructure.value()
        result['NMP'] = self.chbNMP.isChecked()
        result['SMP'] = self.chb03.isChecked()
        result['doctorCome'] = self.chbDoctorCome.isChecked()
        result['showEventName'] = self.chbShowEventName.isChecked()
        result['showCallOccasion'] = self.chbShowCallOccasion.isChecked()
        result['showDiseaseBasic'] = self.chbShowDiseaseBasic.isChecked()
        result['showComplaints'] = self.chbShowComplaints.isChecked()
        result['ageGroup'] = self.cmbAgeGroup.currentIndex()
        return result
