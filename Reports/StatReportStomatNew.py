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
from PyQt4.QtCore import Qt, QDate, QDateTime

from library.Utils      import forceString, forceRef, forceDate, forceDouble, forceInt, formatDate, forceDateTime, formatShortName

from Reports.Report               import createTable, CReportEx, getOrgStructureFullName
from Reports.ReportBase           import CReportBase
from Reports.SpecialityListDialog import formatSpecialityIdList
from Reports.ReportMonthActions   import CSetupReportMonthActions
from Reports.Utils                import dateRangeAsStr
from Orgs.Utils                   import getOrgStructurePersonIdList


class CStomatDayReport(CReportEx):
    def __init__(self, parent):
        CReportEx.__init__(self, parent)
        self._mapActionTypeId2ServiceIdList = {}
        self.setTitle(u'Листок ежедневного учета работы врача-стоматолога (форма 037/у)', u'Листок ежедневного учета работы врача-стоматолога (форма 037/у)')
        self.table_columns = [
            ('8%', [u'№ п/п', u'1'], CReportBase.AlignRight),
            ('8%', [u'Время приема пациента',  u'2'], CReportBase.AlignLeft),
            ('8%', [u'ФИО пациента', u'3'], CReportBase.AlignLeft),
            ('8%', [u'Год рождения', u'4'], CReportBase.AlignLeft),
            ('8%', [u'Адрес', u'5'], CReportBase.AlignLeft),
            ('8%', [u'Первично принятые', u'6'], CReportBase.AlignRight),
            ('8%', [u'В том числе дети', u'7'], CReportBase.AlignRight),
            ('8%', [u'Диагноз', u'8'], CReportBase.AlignLeft),
            ('12%',[u'Фактически выполненный объем работы', u'9'], CReportBase.AlignLeft),
            ('8%', [u'Санированные', u'10'], CReportBase.AlignRight),
            ('8%', [u'В т.ч. в плановом порядке', u'11'], CReportBase.AlignRight),
            ('8%', [u'УЕТ', u'12'], CReportBase.AlignRight),
            ]

    def getPeriodName(self, params):
        date = params.get('begDate', QDate.currentDate())
        params['endDate'] = date
        return date.toString(u"dd.MM.yyyy")

    def getSetupDialog(self, parent):
        result = CSetupReportMonthActions(parent)
        result.setTitle(self.title())
        result.setActionTypeClassVisible(False)
        result.setActionTypeGroupVisible(False)
        result.setStatusVisible(False)
        result.setAssistantVisible(False)
        result.setTissueTypeVisible(False)
        result.setPersonDetailVisible(False)
        result.setPersonMonthDetailVisible(False)
        result.setFinanceVisible(False)
        result.setSexVisible(False)
        result.chkPersonOSDetail.setVisible(False)
        result.label.setText(u'')
        result.edtEndDate.setVisible(False)
        result.setAgeVisible(False)
        result.setUETVisible(True)
        result.lblDate.setText(u'Дата ')
        result.chkPerson.setText(u'Врач ')
        #делаем вид, что это не QComboBox'ы, а обычные QLabel
        result.chkPerson.setStyleSheet('QCheckBox::indicator { width: 0px; height: 0px; }')
        result.chkPerson.setChecked(True)
        result.chkPerson.setCheckable(False)
        result.chkOrgStructure.setStyleSheet('QCheckBox::indicator { width: 0px; height: 0px; }')
        result.chkOrgStructure.setChecked(True)
        result.chkOrgStructure.setCheckable(False)
        result.chkLocality.setStyleSheet('QCheckBox::indicator { width: 0px; height: 0px; }')
        result.chkLocality.setChecked(True)
        result.chkLocality.setCheckable(False)


        # заменяем подходящий комбобокс:
        result.setLocalityVisible(True)
        result.chkLocality.setText(u'Адрес ')
        result.cmbLocality.setMaxCount(0)
        result.cmbLocality.setMaxCount(2)
        result.cmbLocality.addItem(u'регистрации')
        result.cmbLocality.addItem(u'проживания')
        result.params = lambda : dict(CSetupReportMonthActions.params(result).items() + [('addressType', result.cmbLocality.currentIndex())])
        result.params = lambda : dict(CSetupReportMonthActions.params(result).items() + [('orgStructureId', result.cmbOrgStructure.value())])
        result.params = lambda : dict(CSetupReportMonthActions.params(result).items() + [('personId', result.cmbPerson.value())])

        return result

    def key(self, key):
        return key[1]

    def build(self, params):
        doc = QtGui.QTextDocument()
        boldChars = QtGui.QTextCharFormat()
        boldChars.setFontWeight(QtGui.QFont.Bold)
        blockFormatCenter =QtGui.QTextBlockFormat()
        blockFormatCenter.setAlignment(Qt.AlignCenter)
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        reportName = self.getReportName()
        if 'getPeriodName' in dir(self):
            reportName += u' за ' + self.getPeriodName(params)
        self.addParagraph(cursor, reportName)
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        cursor.movePosition(QtGui.QTextCursor.End)
        data = self.getData(params)
        table = self.createTable(cursor)
        sumRow = [0]*12
        for i, key in enumerate(sorted(data.keys(), key=self.key)):
            dataRow = data[key]
            row = table.addRow()
            for j, val in enumerate(dataRow):
                if j == 11:
                    table.setText(row, j, round(val, 2))
                else:
                    table.setText(row, j, val)
                if j in [5, 6, 9, 10, 11]:
                    sumRow[j] += dataRow[j]
            table.setText(row, 0, i+1)
        tableRow = table.addRow()
        table.setText(tableRow, 0, u'Итого:')
        for col in [5, 6, 9, 10, 11]:
            if col == 11:
                table.setText(tableRow, col, round(sumRow[col],  2))
            else:
                table.setText(tableRow, col, sumRow[col])
        return doc

    def dumpParams(self, cursor, params):
        description = []
        begDate = params.get('begDate', QDate())
        if begDate:
            description.append(dateRangeAsStr(u'за период', begDate, begDate))
        orgStructureId = params.get('orgStructureId', None)
        personId = params.get('personId', None)
        if orgStructureId:
            description.append(u'подразделение: ' + getOrgStructureFullName(orgStructureId))
        else:
            description.append(u'подразделение: ЛПУ')
        addressType = params.get('addressType', 0)
        if addressType:
            description.append(u'Адрес: %s' % ((u'регистрации', u'проживания')[addressType-1]))
        if personId:
            personExecName = forceString(QtGui.qApp.db.translate('vrbPersonWithSpeciality', 'id', personId, 'name'))
            description.append(u'Врач: ' + personExecName)
        uetCond = params.get('uetCond', 0)
        if uetCond:
            description.append(u'Учитывать УЕТ по нормативу')
        else:
            description.append(u'Учитывать УЕТ по договору')
        description.append(u'отчёт составлен: '+forceString(QDateTime.currentDateTime()))
        columns = [ ('100%', [], CReportBase.AlignLeft) ]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()


    def getData(self, params):
        db = QtGui.qApp.db
        data = {}
        date = params.get('begDate', QDate.currentDate())
        orgStructureId = params.get('orgStructureId', None)
        uetCond = params.get('uetCond', 0)
        personId = params.get('personId', None)
        addressType = params.get('addressType', 0)
        tableAction = db.table('Action')
        tableEvent = db.table('Event')
        tableAT = db.table('ActionType')
        tableClient = db.table('Client')
        tableET = db.table('EventType')
        tableMKB = db.table('Diagnosis')
        tableVA = db.table('vActionStomOther')
        tableRBS = db.table('rbService')

        table = tableAction.leftJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
        table = table.leftJoin(tableET, tableET['id'].eq(tableEvent['eventType_id']))
        table = table.leftJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
        table = table.leftJoin(tableAT, tableAT['id'].eq(tableAction['actionType_id']))

        cols = [tableClient['id'].alias('client_id'),
                tableEvent['execDate'],
                tableClient['firstName'],
                tableClient['lastName'],
                tableClient['patrName'],
                tableEvent['isPrimary'],
                tableClient['birthDate'],
                tableMKB['MKB'],
                'age(Client.birthDate, Action.endDate) as age',
                tableAT['code'],
                tableEvent['id'].alias('event_id'),
                tableAction['uet'].alias('actionUet'),
                tableAction['amount'],
                tableVA['sanitation'],
                tableEvent['order']
            ]
        cond = [tableET['form'].eq('043'),
                tableAction['deleted'].eq(0),
                tableAction['endDate'].dateEq(date),
            ]

        if uetCond != 0:
            table = table.leftJoin(tableRBS, tableRBS['id'].eq(tableAT['nomenclativeService_id']))
            cols.append(u'IF(AGE(Client.birthDate, CURDATE()) > 18, rbService.`adultUetDoctor`, rbService.`childUetDoctor`) as `uet`')
            cond.append(db.joinOr([tableRBS['adultUetDoctor'].isNotNull(), tableRBS['childUetDoctor'].isNotNull()]))


        table = table.leftJoin(tableMKB, tableMKB['id'].eqEx('getEventDiagnosis(Event.id)'))
        table = table.leftJoin(tableVA, tableVA['action_id'].eq(tableAction['id']))
        cols.append('getClientRegAddress(Client.id) as address' if addressType else 'getClientLocAddress(Client.id) as address')
        if personId:
            cond.append(tableAction['person_id'].eq(personId))
        elif orgStructureId:
            persons = getOrgStructurePersonIdList(orgStructureId)
            cond.append(tableAction['person_id'].inlist(persons))
        recordList = db.getRecordListGroupBy(table, cols, cond, 'Action.id')
        eventIdList = []
        for record in recordList:
            clientId = forceRef(record.value('client_id'))
            #clientAddress = context.getInstance(CClientAddressInfo, clientId, addressType)
            clientAddress = forceString(record.value('address'))
            endDate = forceDateTime(record.value('execDate'))
            isPrimary = forceInt(record.value('isPrimary'))
            age = forceInt(record.value('age'))
            actionCode = forceString(record.value('code'))
            eventId = forceRef(record.value('event_id'))
            actionUet = forceDouble(record.value('actionUet'))
            tariffUet = forceDouble(record.value('uet'))
            uet = actionUet if actionUet else tariffUet
            actionAmount = forceInt(record.value('amount'))
            clientName = formatShortName(forceString(record.value('lastName')), forceString(record.value('firstName')), forceString(record.value('patrName')))
            sanitation = forceString(record.value('sanitation')).replace(' ', '').split(',')
            order = forceInt(record.value('order'))
            row = data.setdefault((clientId, clientName), [0, '', '', '', '', 0, 0, '', '', 0, 0, 0])
            row[1] = endDate.toString("hh:mm")
            row[2] = clientName
            row[3] = formatDate(forceDate(record.value('birthDate')))
            row[4] = unicode(clientAddress)
            if eventId not in eventIdList:
                row[5] += (1 if isPrimary==1 else 0)
                row[6] += (1 if (isPrimary==1 and age < 15) else 0)
                row[7] = forceString(record.value('MKB'))
                eventIdList.append(eventId)
            if uet and actionAmount:
                printCode = '%s: %i'%(actionCode, actionAmount)
                row[8] = '\n'.join([row[8], printCode]) if row[8] else printCode
            if uetCond==0:
                row[11] += actionUet
            else:
                row[11] += tariffUet*actionAmount
            if checkInList(sanitation, [u'проведена']):
                row[9] += 1
            if checkInList(sanitation, [u'проведена']) and order == 1:
                row[10] += 1
        return data


class CStomatReport1(CReportEx):
    def __init__(self, parent):
        CReportEx.__init__(self, parent)
        self.setTitle(u'Отчет о работе стоматолога (форма 039-2)', u'Отчет о работе стоматолога (форма 039-2)')
        self.table_columns = []
        self.colCount = len(self.table_columns)

    def getTableColumns(self, keyName=False, showVisits=0):
        cols =  [
            ('3%', [u'Месяц' if keyName else u'Дата', '', '', '', u'1'], CReportBase.AlignLeft),
            ('3%', [u'Принято больных (Всего)', '', '', '', u'2'], CReportBase.AlignRight),
            ('5%', [u'Принято первичных больных', '', u'Всего', '', u'%i'%(3+showVisits)], CReportBase.AlignRight),
            ('5%', [u'', '', u'Из них детей', '', u'%i'%(4+showVisits)], CReportBase.AlignRight),
            ('3%', [u'Запломбировано зубов', u'Всего', '', '',u'%i'%(5+showVisits)], CReportBase.AlignRight),
            ('5%', [u'', u'В том числе, по поводу', u'кариеса', u'постоянных', u'%i'%(6+showVisits)], CReportBase.AlignRight),
            ('4%', [u'', '', '', u'молочных зубов', u'%i'%(7+showVisits)], CReportBase.AlignRight),
            ('4%', [u'', '', u'его осложнений', u'постоянных', u'%i'%(8+showVisits)], CReportBase.AlignRight),
            ('4%', [u'', '', '', u'молочных зубов', u'%i'%(9+showVisits)], CReportBase.AlignRight),
            ('4%', [u'Вылечено зубов в одно посещение по поводу осложн. кариеса', '', '', '', u'%i'%(10+showVisits)], CReportBase.AlignRight),
            ('3%', [u'Кол.-во пломб из амальгамы', '', '', '', u'%i'%(11+showVisits)], CReportBase.AlignRight),
            ('4%', [u'Проведен курс лечения', u'Заболевание пародонта', u'Количество зубов', '', u'%i'%(12+showVisits)], CReportBase.AlignRight),
            ('4%', [u'', u'', u'Количество пациентов', '', u'%i'%(13+showVisits)], CReportBase.AlignRight),
            ('4%', [u'', u'Слизистой оболочки рта', u'', '', u'%i'%(14+showVisits)], CReportBase.AlignRight),
            ('3%', [u'Удалено зубов', u'Молочного прикуса (ВСЕГО)', '', '', u'%i'%(15+showVisits)], CReportBase.AlignRight),
            ('3%', [u'', u'В том числе по поводу заболеваний пародонта постоянного прикуса', '', '', u'%i'%(16+showVisits)], CReportBase.AlignRight),
            ('4%', [u'', u'Постоянного прикуса (ВСЕГО)', '', '', u'%i'%(17+showVisits)], CReportBase.AlignRight),
            ('3%', [u'Произведено операций', '', '', '', u'%i'%(18+showVisits)], CReportBase.AlignRight),
            ('4%', [u'Всего санировано в порядке плановой санации и по обращению', '', '', '', u'%i'%(19+showVisits)], CReportBase.AlignRight),
            ('4%', [u'Профилактическая работа', u'Осмотрено в порядке плановой санации', '', '', u'%i'%(20+showVisits)], CReportBase.AlignRight),
            ('4%', [u'', u'Из числа осмотренных нуждалось в санации', '', '', u'%i'%(21+showVisits)], CReportBase.AlignRight),
            ('4%', [u'', u'Санировано из числа выявленных при плановой санации', '', '', u'%i'%(22+showVisits)], CReportBase.AlignRight),
            ('4%', [u'', u'Проведен курс профилактических мероприятий', u'Количество мероприятий', '', u'%i'%(23+showVisits)], CReportBase.AlignRight),
            ('4%', [u'', u'', u'Количество пациентов', '', u'%i'%(24+showVisits)], CReportBase.AlignRight),
            ('4%', [u'', u'', u'Количество событий', '', u'%i'%(25+showVisits)], CReportBase.AlignRight),
            ('4%', [u'Выработано условных единиц трудоемкости (УЕТ)', '', '', '', u'%i'%(26+showVisits)], CReportBase.AlignRight),
            ]
        return cols

    def getSetupDialog(self, parent):
        result = CSetupReportMonthActions(parent)
        result.setTitle(self.title())
        result.setActionTypeClassVisible(False)
        result.setActionTypeGroupVisible(False)
        result.setStatusVisible(False)
        result.setAssistantVisible(False)
        result.setTissueTypeVisible(False)
        result.setPersonDetailVisible(True)
        result.setPersonMonthDetailVisible(True)
        result.setLocalityVisible(True)
        result.setUETVisible(True)
        result.setShowVisitsVisible(True)
        result.setSpecialityListVisible(True)
        result.setContractVisible(True)
        return result


    def dumpParams(self, cursor, params):
        sexList = (u'не определено', u'мужской', u'женский')
        description = []
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        if begDate and endDate:
            description.append(dateRangeAsStr(u'за период', begDate, endDate))
        orgStructureId = params.get('orgStructureId', None)
        sexIndex = params.get('sex', 0)
        ageFor = params.get('ageFrom', 0)
        ageTo = params.get('ageTo', 150)
        personExecId = params.get('personId', None)
        specialityList = params.get('specialityList', [])
        contractText = params.get('contractText', None)
        if orgStructureId:
            description.append(u'подразделение: ' + getOrgStructureFullName(orgStructureId))
        else:
            description.append(u'подразделение: ЛПУ')
        financeId = params.get('financeId', None)
        description.append(u'тип финансирования: %s'%(forceString(QtGui.qApp.db.translate('rbFinance', 'id', financeId, 'name')) if financeId else u'не задано'))
        if sexIndex:
            description.append(u'пол ' + sexList[sexIndex])
        if ageFor or ageTo:
            description.append(u'возраст' + u' с '+forceString(ageFor) + u' по '+forceString(ageTo))
        locality = params.get('locality', 0)
        if locality:
            description.append(u'местность: %s жители' % ((u'городские', u'сельские')[locality-1]))
        if personExecId:
            personExecName = forceString(QtGui.qApp.db.translate('vrbPersonWithSpeciality', 'id', personExecId, 'name'))
            description.append(u'исполнитель ' + personExecName)
        if specialityList:
            description.append(u'специальность: ' + formatSpecialityIdList(specialityList))
        if contractText:
            description.append(u'контракт: ' + contractText)
        if params.get('chkPersonOSDetail', False):
            description.append(u'Детализировать по подразделениям')
        if params.get('chkPersonOverall', False):
            description.append(u'Общий по врачам')
        if params.get('chkPersonDetail', False):
            description.append(u'Детализировать по врачам')
        if params.get('chkMonthDetail', False):
            description.append(u'Детализировать по месяцам')
        if params.get('chkPersonOverall', False):
            description.append(u'Детализировать по датам')
        uetCond = params.get('uetCond', 0)
        if uetCond:
            description.append(u'Учитывать УЕТ по нормативу')
        else:
            description.append(u'Учитывать УЕТ по договору')
        description.append(u'отчёт составлен: '+forceString(QDateTime.currentDateTime()))
        columns = [ ('100%', [], CReportBase.AlignLeft) ]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()


    def build(self, params):
        doc = QtGui.QTextDocument()
        boldChars = QtGui.QTextCharFormat()
        boldChars.setFontWeight(QtGui.QFont.Bold)
        blockFormatCenter =QtGui.QTextBlockFormat()
        blockFormatCenter.setAlignment(Qt.AlignCenter)
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        reportName = self.getReportName()
        if 'getPeriodName' in dir(self):
            reportName += u' за ' + self.getPeriodName(params)
        self.addParagraph(cursor, reportName)
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        cursor.movePosition(QtGui.QTextCursor.End)
        data = self.getData(params)
        chkPersonOSDetail = params.get('chkPersonOSDetail', False)
        chkPersonDetail = params.get('chkPersonDetail', False)
        chkPersonOverall = params.get('chkPersonOverall', False)
        chkPersonDateDetail = params.get('chkPersonDateDetail', False)
        chkMonthDetail = params.get('chkMonthDetail', False)
        chkShowVisits = params.get('chkShowVisits', False)
        self.table_columns = self.getTableColumns(showVisits=chkShowVisits)
        if chkShowVisits:
            self.table_columns.insert(2, ('3%', [u'Посещений (Всего)', '', '', '', u'3'], CReportBase.AlignRight),)
        colsCount = (25+chkShowVisits)
        resultRow = [0]*colsCount
        if chkPersonDetail:
            firstPerson = True
            for osName, osData in data.iteritems():
                for personName, personData in osData.iteritems():
                    cursor.movePosition(QtGui.QTextCursor.End)
                    format = QtGui.QTextCharFormat()
                    font = QtGui.QFont()
                    font.setBold(True)
                    font.setPointSize(13)
                    format.setFont(font)
                    cursor.setCharFormat(format)
                    if firstPerson:
                        cursor.insertText(u'Врач: %s\n'%personName)
                        firstPerson = False
                    else:
                        cursor.insertText(u'\n\nВрач: %s\n'%personName)
                    table = self.getTable(cursor, params=params)
                    resultRow = [0]*colsCount
                    for date in sorted(personData.keys(), key=dateKey):
                        dateRow = personData[date]
                        if chkPersonDateDetail:
                            row = table.addRow()
                            table.setText(row, 0, date)
                        for i, val in enumerate(dateRow):
                            if chkPersonDateDetail:
                                table.setText(row, i+1, val)
                            resultRow[i] += val
                    row = table.addRow()
                    table.setText(row, 0, u'Итого', charFormat=boldChars)
                    for i, val in enumerate(resultRow):
                        table.setText(row, i+1, val, charFormat=boldChars)
        elif chkPersonOverall:
            table = self.getTable(cursor, params=params)
            resultRow = [0]*colsCount
            for osName, osData in data.iteritems():
                for personName, personData in osData.iteritems():
                    personRow = [0]*colsCount
                    for date in sorted(personData.keys(), key=dateKey):
                        dateRow = personData[date]
                        for i, val in enumerate(dateRow):
                            personRow[i] += val
                            resultRow[i] += val
                    if sum(personRow) > 0:
                        row = table.addRow()
                        table.setText(row, 0, personName)
                        for i, val in enumerate(personRow):
                            table.setText(row, i+1, val)
            row = table.addRow()
            table.setText(row, 0, u'Итого', charFormat=boldChars)
            for i, val in enumerate(resultRow):
                table.setText(row, i+1, val, charFormat=boldChars)
        elif chkPersonOSDetail:
            table = self.getTable(cursor, params=params)
            for osName, osData in data.iteritems():
                resultRow = [0]*colsCount
                row = table.addRow()
                table.setText(row, 0, osName, charFormat=boldChars, blockFormat=blockFormatCenter)
                table.mergeCells(row, 0, 1, colsCount)
                dateResultRow = {}
                for personName, personData in osData.iteritems():
                    for date in sorted(personData.keys(), key=dateKey):
                        dateRow = personData[date]
                        if chkMonthDetail:
                            date = '.'.join(date.split('.')[1:])
                        resRow = dateResultRow.setdefault(date, [0]*colsCount)
                        for i, val in enumerate(dateRow):
                            resRow[i] += val
                            resultRow[i] += val
                if chkPersonDateDetail or chkMonthDetail:
                    for date in sorted(dateResultRow.keys(), key=dateKey):
                        row = table.addRow()
                        table.setText(row, 0, date)
                        for i, val in enumerate(dateResultRow.get(date, [0]*colsCount)):
                            table.setText(row, i+1, val)
                row = table.addRow()
                table.setText(row, 0, u'Итого', charFormat=boldChars)
                for i, val in enumerate(resultRow):
                    table.setText(row, i+1, val, charFormat=boldChars)
        else:
            table = self.getTable(cursor, params=params)
            dateResultRow = {}
            for osName, osData in data.iteritems():
                for personName, personData in osData.iteritems():
                    for date, dateRow in personData.iteritems():
                        if chkMonthDetail:
                            date = '.'.join(date.split('.')[1:])
                        resRow = dateResultRow.setdefault(date, [0]*colsCount)
                        for i, val in enumerate(dateRow):
                            resRow[i] += val
            for date in sorted(dateResultRow.keys(), key=dateKey):
                row = table.addRow()
                table.setText(row, 0, date)
                for i, val in enumerate(dateResultRow.get(date, [0]*colsCount)):
                    table.setText(row, i+1, val)
                    resultRow[i] += val
            row = table.addRow()
            table.setText(row, 0, u'Итого', charFormat=boldChars)
            for i, val in enumerate(resultRow):
                table.setText(row, i+1, val, charFormat=boldChars)
        return doc


    def getData(self, params):
        begDate = params.get('begDate', QDate.currentDate())
        endDate = params.get('endDate', QDate.currentDate())
        chkShowVisits = params.get('chkShowVisits', False)
        orgStructureId = params.get('orgStructureId', None)
        personId = params.get('personId', None)
        specialityList = params.get('specialityList', None)
        sex = params.get('sex', None)
        ageFrom = params.get('ageFrom', None)
        ageTo = params.get('ageTo', None)
        financeId = params.get('financeId', None)
        locality = params.get('locality', 0)
        uetCond = params.get('uetCond', 0)
        contractId = params.get('contractId', [])

        db = QtGui.qApp.db
        vActionUU = db.table('vActionStomUU')
        vActionLL = db.table('vActionStomLL')
        vActionSU = db.table('vActionStomSU')
        vActionSL = db.table('vActionStomSL')
        vActionCU = db.table('vActionStomCU')
        vActionCL = db.table('vActionStomCL')
        vActionOt = db.table('vActionStomOther')
        tableAction = db.table('Action')
        tableEvent = db.table('Event')
        tableAT = db.table('ActionType')
        tableClient = db.table('Client')
        tableATS = db.table('ActionType_Service')
        tableCT = db.table('Contract_Tariff')
        tableRBS = db.table('rbService')
        tablePerson = db.table('vrbPersonWithSpeciality')
        tableOS = db.table('OrgStructure')
        cond = [tableAction['endDate'].lt(endDate.addDays(1)),
            tableAction['endDate'].ge(begDate)]
        if personId:
            cond.append(tableAction['person_id'].eq(personId))
        elif orgStructureId:
            persons = getOrgStructurePersonIdList(orgStructureId)
            cond.append(tableAction['person_id'].inlist(persons))
        if specialityList:
            cond.append(tablePerson['speciality_id'].inlist(specialityList))
        if sex:
            cond.append(tableClient['sex'].eq(sex))
        if ageFrom:
            cond.append('age(Client.`birthDate`, Action.endDate) >= %d'%ageFrom)
        if ageTo is not None:
            cond.append('age(Client.`birthDate`, Action.endDate) <= %d'%ageTo)
        if financeId:
            cond.append('(Action.finance_id=%d)'%financeId)
        if locality:
            # 1: горожане, isClientVillager == 0 или NULL
            # 2: сельские жители, isClientVillager == 1
            cond.append('IFNULL(isClientVillager(Client.id), 0) = %d' % (locality-1))
        cols = [tableEvent['isPrimary'].alias('isPrimary'),
            tableAction['endDate'].alias('endDate'),
            tableAction['event_id'].alias('event_id'),
            tableAction['id'].alias('action_id'),
            'age(Client.birthDate, Action.endDate) as age',
            tableClient['id'].alias('client_id'),
            tableAT['serviceType'].alias('serviceType'),
            tablePerson['id'].alias('person_id'),
            tablePerson['name'].alias('person_name'),
            tableOS['name'].alias('orgStructure_name')
            ]
        if chkShowVisits:
            cols.append( u'''(SELECT COUNT(DISTINCT Visit.id)
                FROM Visit WHERE
                Visit.event_id = Action.event_id
                AND (Visit.date >= Action.begDate AND Visit.date <= Action.endDate)) as visitsCount''')
        table = tableAction.leftJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
        table = table.leftJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
        table = table.leftJoin(tableAT, tableAT['id'].eq(tableAction['actionType_id']))
        table = table.leftJoin(tablePerson, tablePerson['id'].eq(tableAction['person_id']))
        table = table.leftJoin(tableOS, tableOS['id'].eq(tablePerson['orgStructure_id']))

        recordList = db.getRecordList(table, cols, cond)
        data = {}
        eventListForDate = {}
        eventList = []
        actionIdList = []
        actionIdToEventId = {}
        actionIdToClientId = {}
        actionIdToServiceType = {}
        actionIdToPersonName = {}
        actionIdToOSName = {}
        actionIdToDate = {}
        for record in recordList:
            age = forceInt(record.value('age'))
            if ageFrom and age < ageFrom:
                continue
            if ageTo is not None and age > ageTo:
                continue
            date = formatDate(forceDate(record.value('endDate')))
            eventId = forceRef(record.value('event_id'))
            isPrimary = forceInt(record.value('isPrimary'))
            if chkShowVisits:
                visitsCount = forceInt(record.value('visitsCount'))
            action_id = forceRef(record.value('action_id'))
            client_id = forceRef(record.value('client_id'))
            serviceType = forceInt(record.value('serviceType'))
            osName = forceString(record.value('orgStructure_name'))
            personName = forceString(record.value('person_name'))
            actionIdList.append(action_id)
            actionIdToClientId[action_id] = client_id
            actionIdToServiceType[action_id] = serviceType
            actionIdToPersonName[action_id] = personName
            actionIdToOSName[action_id] = osName
            actionIdToDate[action_id] = date
            age = forceInt(record.value('age'))
            osdata = data.setdefault(osName, {})
            persondata = osdata.setdefault(personName, self.getEmptyDict(begDate, endDate, chkShowVisits))
            row = persondata.setdefault(date, [0]*(25+chkShowVisits))
            actionIdToEventId[action_id] = eventId

            # Устранять дубликаты только в пределах одной даты
            if not eventListForDate.has_key(date):
                eventListForDate[date] = []
            if eventId not in eventListForDate[date]:
                row[0] += 1
                if chkShowVisits:
                    row[1] += visitsCount
                eventListForDate[date].append(eventId)
                if isPrimary == 1:
                    row[1+chkShowVisits] += 1
                    if age < 15:
                        row[2+chkShowVisits] += 1
        eventList = []
        for i in eventListForDate.values():
            eventList.extend(i)

        toothData = {}
        otherParams = ['machine',
                       'objectivity',
                       'o_treatment',
                       'bite',
                       'note',
                       'prostheses',
                       'sanitation',
                       'mucous']
        otherParamsEmptyString = ["", "", "", "", "", "", "", ""]
        SURecordList = db.getRecordList(vActionSU, '*', [vActionSU['action_id'].inlist(actionIdList)])
        SLRecordList = db.getRecordList(vActionSL, '*', [vActionSL['action_id'].inlist(actionIdList)])
        UURecordList = db.getRecordList(vActionUU, '*', [vActionUU['action_id'].inlist(actionIdList)])
        #
        LLRecordList = db.getRecordList(vActionLL, '*', [vActionLL['action_id'].inlist(actionIdList)])

        CURecordList = db.getRecordList(vActionCU, '*', [vActionCU['action_id'].inlist(actionIdList)])
        CLRecordList = db.getRecordList(vActionCL, '*', [vActionCL['action_id'].inlist(actionIdList)])
        OtRecordList = db.getRecordList(vActionOt, '*', [vActionOt['action_id'].inlist(actionIdList)])
        for record in SURecordList:
            row = toothData.setdefault(forceRef(record.value('action_id')), {'status':[""]*32, 'condition': [""]*32, 'number': [""]*32,
                'other':dict(zip(otherParams, otherParamsEmptyString))})['status']
            for i in range(record.count()-1):
                row[i] = forceString(record.value(i+1))
        for record in SLRecordList:
            row = toothData.setdefault(forceRef(record.value('action_id')), {'status':[""]*32, 'condition': [""]*32, 'number': [""]*32,
                'other':dict(zip(otherParams, otherParamsEmptyString))})['status']
            for i in range(record.count()-1):
                row[i+16] = forceString(record.value(i+1))
        for record in UURecordList:
            row = toothData.setdefault(forceRef(record.value('action_id')), {'status':[""]*32, 'condition': [""]*32, 'number': [0]*32,
                'other':dict(zip(otherParams, otherParamsEmptyString))})['number']
            for i in range(record.count()-1):
                row[i] = forceInt(record.value(i+1))
        for record in LLRecordList:
            row = toothData.setdefault(forceRef(record.value('action_id')), {'status':[""]*32, 'condition': [""]*32, 'number': [0]*32,
                'other':dict(zip(otherParams, otherParamsEmptyString))})['number']
            for i in range(record.count()-1):
                row[i+16] = forceInt(record.value(i+1))
        for record in CURecordList:
            row = toothData.setdefault(forceRef(record.value('action_id')), {'status':[""]*32, 'condition': [""]*32, 'number': [""]*32,
                'other':dict(zip(otherParams, otherParamsEmptyString))})['condition']
            for i in range(record.count()-1):
                row[i] = forceString(record.value(i+1))
        for record in CLRecordList:
            row = toothData.setdefault(forceRef(record.value('action_id')), {'status':[""]*32, 'condition': [""]*32, 'number': [""]*32,
                'other':dict(zip(otherParams, otherParamsEmptyString))})['condition']
            for i in range(record.count()-1):
                row[i+16] = forceString(record.value(i+1))
        for record in OtRecordList:
            otherData = toothData.setdefault(forceRef(record.value('action_id')), {'status':[""]*32, 'condition': [""]*32, 'number': [""]*32,
                'other':dict(zip(otherParams, otherParamsEmptyString))})['other']
            for par in otherParams:
                otherData[par] = forceString(record.value(par))

        clientIdList = set()
        eventIdList = set()
        clientIdListForCols212223 = set()
        eventIdListForCols212223 = set()
        clientIdList13 = set()
        clientIdList14 = set()
        for (action_id, actionData) in toothData.iteritems():
            osdata = data.setdefault(actionIdToOSName[action_id], {})
            persondata = osdata.setdefault(actionIdToPersonName[action_id], {})
            row = persondata.setdefault(actionIdToDate[action_id], [0]*(25+chkShowVisits))
            sanation = actionData['other']['sanitation'].replace(' ', '').split(',')
            for i in range(32):
                conditions = actionData['condition'][i].replace(' ', '').split(',')
                if actionData['status'][i] in ('5', '6', '7'):
                    row[3+chkShowVisits] += 1
                if actionData['status'][i] == '5' and checkInList(conditions, [u"П/С", u"C"]) and actionData['number'][i] <= 48 and actionData['number'][i] > 0:
                    row[4+chkShowVisits] += 1
                if actionData['status'][i] == '5' and checkInList(conditions, [u"П/С", u"C"]) and actionData['number'][i] >= 50:
                    row[5+chkShowVisits] += 1
                if actionData['status'][i] in ('6',  '7') and checkInList(conditions, [u"П/С", u"C", u"P", u"Pt", u"R"]) and actionData['number'][i] <= 48 and actionData['number'][i] > 0:
                    row[6+chkShowVisits] += 1
                if actionData['status'][i] in ('6',  '7') and checkInList(conditions, [u"П/С", u"C", u"P", u"Pt", u"R"]) and actionData['number'][i] >= 50:
                    row[7+chkShowVisits] += 1
                if actionData['status'][i] == '6' and checkInList(conditions, [u"П/С", u"C", u"P", u"Pt", u"R"]):
                    row[8+chkShowVisits] += 1
                if actionData['status'][i] in ('5', '6', '7') and checkInList(conditions, [u"Па"]):
                    row[9+chkShowVisits] += 1
                if actionData['status'][i] == '4' and checkInList(conditions, [u"A", u"G"]):
                    row[10+chkShowVisits] += 1
                if actionData['status'][i] == '4' and not checkInList(conditions, [u"A", u"G"]) and actionIdToClientId[action_id] not in clientIdList13:
                    row[11+chkShowVisits] += 1
                    clientIdList13.add(actionIdToClientId[action_id])
                if actionData['status'][i] == '4' and not checkInList(conditions, [u"A", u"G"]) and actionIdToClientId[action_id] not in clientIdList14:
                    row[12+chkShowVisits] += 1
                    clientIdList14.add(actionIdToClientId[action_id])
                if actionData['status'][i] == '9' and actionData['number'][i] >= 50:
                    row[13+chkShowVisits] += 1
                if actionData['status'][i] == '9' and checkInList(conditions, [u"A"]) and actionData['number'][i] <= 48 and actionData['number'][i] > 0:
                    row[14+chkShowVisits] += 1
                if actionData['status'][i] == '9' and actionData['number'][i] <= 48 and actionData['number'][i] > 0:
                    row[15+chkShowVisits] += 1
            if checkInList(sanation, [u'проведена']):
                row[17+chkShowVisits] += 1
            if checkInList(sanation, [u'запланирована']):
                row[18+chkShowVisits] += 1
            if checkInList(sanation, [u'нуждается']):
                row[19+chkShowVisits] += 1
            if checkAllInList(sanation, [u'проведена', u'запланирована']):
                row[20+chkShowVisits] += 1
            clientIdList.add(actionIdToClientId[action_id])
            eventIdList.add(actionIdToEventId[action_id])
        for (action_id, actionData) in actionIdToServiceType.iteritems():
            osdata = data.setdefault(actionIdToOSName[action_id], {})
            persondata = osdata.setdefault(actionIdToPersonName[action_id], {})
            row = persondata.setdefault(actionIdToDate[action_id], [0]*(25+chkShowVisits))
            if actionIdToServiceType[action_id] == 4:
                row[16+chkShowVisits] += 1
            if actionIdToServiceType[action_id] == 7:
                row[21+chkShowVisits] += 1
            if actionIdToServiceType[action_id] == 7 and actionIdToClientId[action_id] not in clientIdListForCols212223:
                row[22+chkShowVisits] += 1
                clientIdListForCols212223.add(actionIdToClientId[action_id])
            if actionIdToServiceType[action_id] == 7 and actionIdToEventId[action_id] not in eventIdListForCols212223:
                row[23+chkShowVisits] += 1
                eventIdListForCols212223.add(actionIdToEventId[action_id])


        table = tableAction.leftJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
        table = table.leftJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
        table = table.leftJoin(tablePerson, tablePerson['id'].eq(tableAction['person_id']))
        table = table.leftJoin(tableAT, tableAT['id'].eq(tableAction['actionType_id']))
        table = table.leftJoin(tableOS, tableOS['id'].eq(tablePerson['orgStructure_id']))
        cols = [tableAction['id'],
                tableAction['endDate'],
                tableAction['uet'],
                tableAction['amount'],
                tablePerson['name'].alias('person_name'),
                tableOS['name'].alias('orgStructure_name')]

        #UET
        if uetCond == 0:
            table = table.leftJoin(tableATS, db.joinAnd([tableATS['master_id'].eq(tableAT['id']),
                                                                        db.joinOr([tableATS['finance_id'].isNull(), tableATS['finance_id'].eq(tableAction['finance_id'])])]))
            table = table.leftJoin(tableCT, [tableCT['service_id'].eq(tableATS['service_id']), tableCT['master_id'].eq(tableEvent['contract_id'])])
            cols.append(tableCT['uet'],)
            cond = ['isSexAndAgeSuitable(Client.sex, Client.birthDate, Contract_Tariff.sex, Contract_Tariff.age, Action.endDate)',
                tableCT['deleted'].eq(0),
                db.joinOr([tableCT['tariffCategory_id'].eq(tablePerson['tariffCategory_id']), tableCT['tariffCategory_id'].isNull()]),
                db.joinOr([tableCT['begDate'].lt(tableAction['endDate'].addDays(1)), tableCT['begDate'].isNull()]),
                db.joinOr([tableCT['endDate'].ge(tableAction['begDate']), tableCT['begDate'].isNull()]),
                tableAction['endDate'].lt(endDate.addDays(1)),
                tableAction['endDate'].ge(begDate)]
            if contractId:
                cond.append(tableCT['master_id'].eq(contractId))
        else:
            table = table.leftJoin(tableRBS, tableRBS['id'].eq(tableAT['nomenclativeService_id']))
            cols.append(u'IF(AGE(Client.birthDate, CURDATE()) > 18, rbService.`adultUetDoctor`, rbService.`childUetDoctor`) as `uet`')
            cond.append(db.joinOr([tableRBS['adultUetDoctor'].isNotNull(), tableRBS['childUetDoctor'].isNotNull()]))

        if len(eventList):
            cond.append(tableEvent['id'].inlist(eventList))

        if financeId:
            cond.append('(Action.finance_id=%d)'%financeId)

        recordList = db.getRecordList(table, cols, cond) # may be use group by for prevent multiple join of ActionType_Service?
        for record in recordList:
            action_id = forceRef(record.value(0))
            endDate = formatDate(forceDate(record.value(1)))
            auet = forceDouble(record.value(2))
            amount = forceInt(record.value(3))
            personName = forceString(record.value(4))
            osName = forceString(record.value(5))
            tuet = forceDouble(record.value(6))

            osdata = data.setdefault(osName, {})
            persondata = osdata.setdefault(personName, {})
            row = persondata.setdefault(endDate, [0]*(25+chkShowVisits))
            if uetCond==0:
                row[24+chkShowVisits] += auet
            else:
                row[24+chkShowVisits] += tuet*amount
        return data

    def getEmptyDict(self, begDate, endDate, chkShowVisits=0):
        result = {}
        for i in range(begDate.daysTo(endDate)+1):
            date = formatDate(begDate.addDays(i))
            result[date] = [0]*(25+chkShowVisits)
        return result

    def getTable(self, cursor, keyName=False, params=None):
        cursor.movePosition(QtGui.QTextCursor.End)
        if params:
            chkShowVisits = params.get('chkShowVisits', 0)
        else:
            chkShowVisits = 0

        shift = forceInt(chkShowVisits) + (1 if keyName else 0)

        table = self.createTable(cursor)
        table.mergeCells(0, 0, 4, 1)
        if keyName:
            table.mergeCells(0, 1+chkShowVisits, 4, 1)
        if chkShowVisits:
            table.mergeCells(0, 1, 4, 1)

        table.mergeCells(0, 1+shift, 4, 1)

        table.mergeCells(0, 2+shift, 2, 2)
        table.mergeCells(2, 2+shift, 2, 1)
        table.mergeCells(2, 3+shift, 2, 1)

        table.mergeCells(0, 4+shift, 1, 5)
        table.mergeCells(1, 4+shift, 3, 1)
        table.mergeCells(1, 5+shift, 1, 4)
        table.mergeCells(2, 5+shift, 1, 2)
        table.mergeCells(2, 7+shift, 1, 2)

        table.mergeCells(0, 9+shift, 4, 1)

        table.mergeCells(0, 10+shift, 4, 1)

        table.mergeCells(0, 11+shift, 1, 3)
        table.mergeCells(1, 11+shift, 1, 2)
        table.mergeCells(2, 11+shift, 2, 1)
        table.mergeCells(2, 12+shift, 2, 1)
        table.mergeCells(1, 13+shift, 3, 1)

        table.mergeCells(0, 14+shift, 1, 3)
        table.mergeCells(1, 14+shift, 3, 1)
        table.mergeCells(1, 15+shift, 3, 1)
        table.mergeCells(1, 16+shift, 3, 1)

        table.mergeCells(0, 17+shift, 4, 1)

        table.mergeCells(0, 18+shift, 4, 1)

        table.mergeCells(0, 19+shift, 1, 6)
        table.mergeCells(1, 19+shift, 3, 1)
        table.mergeCells(1, 20+shift, 3, 1)
        table.mergeCells(1, 21+shift, 3, 1)
        table.mergeCells(1, 22+shift, 1, 3)

        table.mergeCells(2, 22+shift, 2, 1)
        table.mergeCells(2, 23+shift, 2, 1)
        table.mergeCells(2, 24+shift, 2, 1)
        table.mergeCells(0, 25+shift, 4, 1)

        return table


def checkInList(list, vals):
    return any(val in list for val in vals)

def checkAllInList(list, vals):
    return all(val in list for val in vals)

def checkNotInList(list, vals):
    return all(val not in list for val in vals)

def dateKey(date):
    return '.'.join(reversed(date.split('.')))
