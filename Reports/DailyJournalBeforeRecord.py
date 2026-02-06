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
from PyQt4.QtCore import pyqtSignature, QDate

from library.Calendar   import monthName
from library.Utils      import calcAge, forceBool, forceDate, forceInt, forceRef, forceString, forceTime, formatName
from Orgs.Utils         import getPersonInfo, getOrgStructureFullName, getOrgStructureDescendants

from Orgs.Utils         import getPersonInfo, getOrgStructureDescendants
from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable
from Reports.ReportView import CPageFormat
from Registry.Utils     import formatAttachesAsHTML, getClientAttaches, getClientPhonesEx
from Timeline.Schedule  import CSchedule


from Reports.Ui_DailyJournalBeforeRecordSetup import Ui_DailyJournalBeforeRecordSetup


class CDailyJournalBeforeRecord(CReport):
    title_columns = [ ('25%', [], CReportBase.AlignLeft),
                      ('50%', [], CReportBase.AlignLeft),
                      ('25%', [], CReportBase.AlignLeft) ]

    def __init__(self, parent = None):
        CReport.__init__(self, parent)
        self.setTitle(u'Суточный журнал предварительной записи')
        self.rowInTable = 0
        self.rowOnPage = 0
        self.pageRowCount = 0
        self.tableRowCount = 0
        self.currentTable = None
        self.orientation = CPageFormat.Landscape
        self.table_columns = [
            ('3%', [u'№'], CReportBase.AlignRight),
            ('2%', [u'П'], CReportBase.AlignLeft),
            ('15%',[u'Идентификатор'], CReportBase.AlignLeft),
            ('5%', [u'Время'], CReportBase.AlignLeft),
            ('20%',[u'ФИО'], CReportBase.AlignLeft),
            ('8%', [u'Дата рождения'], CReportBase.AlignLeft),
            ('22%',[u'Прикрепление'], CReportBase.AlignLeft),
            ('25%',[u'Примечание'], CReportBase.AlignLeft),
               ]


    def getSetupDialog(self, parent):
        result = CDailyJournalBeforeRecordSetup(parent)
        return result


    def build(self, params):
        date = params.get('begDateDailyJournal', QDate())
        orgStructureId = params.get('orgStructureId', None)
        personId = params.get('personId', None)
        outputTablePerPage = forceBool(params.get('outputTablePerPage', 0))
        outputNotScheduled = forceBool(params.get('outputNotScheduled', 0))
        order       = params.get('order', None)
        isPrimary          = params.get('isPrimary', None)
        accountingSystemId = params.get('accountingSystemId', None)
        showEmptyItems     = forceBool(params.get('showEmptyItems', 0))
        self.pageRowCount  = params.get('rowCount', 0)
        isClientIdentifier = params.get('isClientIdentifier', 0)

        personIdList = self.getPersonIdList(date, orgStructureId, personId)

        doc = QtGui.QTextDocument()
        if date and personIdList:
            self.rowOnPage = 0
            cursor = QtGui.QTextCursor(doc)
            for i, personId in enumerate(personIdList):
                scheduleList = self.getScheduleList(date, personId)
                if scheduleList:
                    for schedule in scheduleList:
                        cursor = self.createTableForPerson(cursor, personId, date, schedule, order, accountingSystemId, isPrimary, showEmptyItems, isClientIdentifier)
                elif outputNotScheduled:
                    cursor = self.createTableForPerson(cursor, personId, date, None, order, accountingSystemId, isPrimary, showEmptyItems, isClientIdentifier)
                if outputTablePerPage and self.rowOnPage > 0 and i < len(personIdList) - 1:
                    self.insertPageBreak(cursor)
                    cursor.insertBlock()
                    cursor.insertBlock()
                    cursor.insertBlock()
                    cursor.insertBlock()
                    cursor.movePosition(QtGui.QTextCursor.End)
        return doc


    def getPersonIdList(self, date, orgStructureId, personId):
        db = QtGui.qApp.db
        tablePerson = db.table('Person')
        cond = [tablePerson['deleted'].eq(0)]
        if personId:
            cond.append(tablePerson['id'].eq(personId))
        if orgStructureId:
            cond.append(tablePerson['orgStructure_id'].inlist(getOrgStructureDescendants(orgStructureId)))
        else:
            cond.append(tablePerson['org_id'].eq(QtGui.qApp.currentOrgId()))
        cond.append(db.joinOr([tablePerson['retireDate'].isNull(),
                               tablePerson['retireDate'].gt(date)
                              ]
                             )
                   )
        return db.getIdList(tablePerson, where=cond, order='lastName, firstName, patrName')


    def getScheduleList(self, date, personId):
        db = QtGui.qApp.db
        tableSchedule = db.table('Schedule')
        cond = [tableSchedule['deleted'].eq(0),
                tableSchedule['person_id'].eq(personId),
                tableSchedule['date'].eq(date),
                tableSchedule['appointmentType'].eq(CSchedule.atAmbulance),
               ]
        recordList = db.getRecordList(tableSchedule, '*', cond, 'begTime')
        return recordList


    def getAccountingSystemName(self, accountingSystemId):
        if accountingSystemId == -2: # адрес проживания
            return u'Адрес проживания'
        elif accountingSystemId == -1: # адрес регистрации
            return u'Адрес регистрации'
        elif accountingSystemId is None: #
            return u'Идентификатор пациента в лечебном учреждении'
        else:
            return forceString(QtGui.qApp.db.translate('rbAccountingSystem', 'id', accountingSystemId, 'name'))


    def insertPageBreak(self, cursor):
        self.rowOnPage = 0
        # завершаем старую табличку
        cursor.movePosition(QtGui.QTextCursor.End)
        # готовимся к переводу страницы:
        page = QtGui.QTextBlockFormat()
        page.setPageBreakPolicy(QtGui.QTextFormat.PageBreak_AlwaysAfter)
        cursor.setBlockFormat(page)
        cursor.insertBlock()
        if self.rowInTable < self.tableRowCount:
            # начинаем новую табличку
            self.currentTable = createTable(cursor, self.table_columns)
        # сбрасываем перевод страницы:
        page = QtGui.QTextBlockFormat()
        page.setPageBreakPolicy(QtGui.QTextFormat.PageBreak_Auto)
        cursor.setBlockFormat(page)


    def getSheduleItemData(self, schedule, accountingSystemId, isPrimary, showEmptyItems, order, isClientIdentifier):
        db = QtGui.qApp.db

        if accountingSystemId == -2: # адрес проживания
            clientIdentifier = 'getClientLocAddress(Schedule_Item.client_id)'
        elif accountingSystemId == -1: # адрес регистрации
            clientIdentifier = 'getClientRegAddress(Schedule_Item.client_id)'
        elif accountingSystemId is None: #
            clientIdentifier = 'Schedule_Item.client_id'
        else:
            clientIdentifier = 'getClientIdentifier(Schedule_Item.client_id,%d)' % accountingSystemId
        tableScheduleItem = db.table('Schedule_Item')
        cond = [tableScheduleItem['deleted'].eq(0),
                tableScheduleItem['master_id'].eq(schedule.value('id')),
               ]
        joinIdentifier = u''
        if isClientIdentifier and accountingSystemId > 0:
            tableClientIdentification = db.table('ClientIdentification')
            joinIdentifier = u'''INNER JOIN ClientIdentification ON ClientIdentification.client_id = Client.id
            AND ClientIdentification.id = (SELECT MAX(CI.id)
                                     FROM ClientIdentification AS CI
                                     WHERE CI.client_id = Client.id
                                       AND CI.deleted = 0
                                       AND CI.accountingSystem_id = %s)'''%(accountingSystemId)
            cond.append(tableClientIdentification['accountingSystem_id'].eq(accountingSystemId))
        if not showEmptyItems or isPrimary:
            cond.append(tableScheduleItem['client_id'].isNotNull())
        if order == 0: # по идентификатору
            orderCols = 'clientIdentifier, Schedule_Item.time'
        elif order == 2: # по фио
            orderCols = 'Client.lastName, Client.firstName, Client.patrName, Schedule_Item.time'
        else: # order == 1: # по времени
            orderCols = 'Schedule_Item.time'

        if isPrimary:
            havingCond = 'isPrimary'
        else:
            havingCond = ''

        stmt = '''SELECT Schedule_Item.time,
                      Schedule_Item.client_id,
                      Schedule_Item.note,
                      Schedule_Item.complaint,
                      Schedule_Item.recordClass,
                      Schedule_Item.recordPerson_id,
               %(clientIdentifier)s AS clientIdentifier,
               NOT EXISTS(SELECT NULL
                        FROM Schedule_Item AS SI
                        JOIN Schedule AS S ON S.id = SI.master_id
                        WHERE SI.deleted=0
                          AND S.deleted=0
                          AND SI.client_id = Schedule_Item.client_id
                          AND S.date = Schedule.date
                          AND SI.time<Schedule_Item.time) AS isPrimary,
               Client.lastName, Client.firstName, Client.patrName,
               Client.birthDate
               FROM Schedule_Item
               LEFT JOIN Client   ON Client.id = Schedule_Item.client_id
               LEFT JOIN Schedule ON Schedule.id = Schedule_Item.master_id
               %(joinIdentifier)s
               WHERE %(cond)s
               %(havingKV)s%(havingCond)s
               ORDER BY %(order)s'''% dict(clientIdentifier = clientIdentifier,
                                           joinIdentifier   = joinIdentifier,
                                           cond             = db.joinAnd(cond),
                                           havingKV         = 'HAVING ' if havingCond else '',
                                           havingCond       = havingCond,
                                           order            = orderCols)
        return db.query(stmt)


    def createTableForPerson(self, cursor, personId, date, schedule, order, accountingSystemId, isPrimary, showEmptyItems, isClientIdentifier):
        isPrimaryList = (u'Нет', u'Да')
        boldChars = QtGui.QTextCharFormat()
        boldChars.setFontWeight(QtGui.QFont.Bold)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        personInfo = getPersonInfo(personId)
        personName     = personInfo['fullName']
        specialityName = personInfo['specialityName']
        postName = personInfo['postName']
        orgStructureName = personInfo['orgStructureName']
        if schedule:
            office    = forceString(schedule.value('office'))
            timeRange = '%s - %s' % (forceTime(schedule.value('begTime')).toString('hh:mm'),
                                     forceTime(schedule.value('endTime')).toString('hh:mm')
                                    )
        else:
            office    = '-'
            timeRange = u'нет приёма'

        table = createTable(cursor, CDailyJournalBeforeRecord.title_columns, headerRowCount=1, border=0, cellPadding=2, cellSpacing=0)

        table.setText(0, 0, forceString(date), charFormat=boldChars)
        table.setText(0, 1, monthName[date.month()], charFormat=boldChars)
        table.setText(0, 2, date.longDayName(date.dayOfWeek()), charFormat=boldChars)
        row = table.addRow()
        table.setText(row, 0, u'')
        table.setText(row, 1, u'Карточка предварительной записи пациентов', charFormat=boldChars)
        table.setText(row, 2, u'')
        row = table.addRow()
        table.setText(row, 0, u'к врачу:')
        table.setText(row, 1, u'%s(%s)'%(orgStructureName, postName))
        table.setText(row, 2, u'кабинет %s'%(office))
        row = table.addRow()
        table.setText(row, 1, '%s, %s' % (personName, specialityName))
        row = table.addRow()
        table.setText(row, 0, u'часы приема:')
        table.setText(row, 1, timeRange)
        table.setText(row, 2, u'')
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()

        if schedule:
            cursor.insertText(u'\nпервичные: %s\n'  % isPrimaryList[isPrimary])
            cursor.insertText(u'идентификатор: %s\n'% self.getAccountingSystemName(accountingSystemId))
            cursor.setCharFormat(CReportBase.ReportBody)
            cursor.insertBlock()

            self.currentTable = createTable(cursor, self.table_columns)
            self.rowInTable = 1

            query = self.getSheduleItemData(schedule, accountingSystemId, isPrimary, showEmptyItems, order, isClientIdentifier)
            while query.next():
                record = query.record()
                self.printDailyJournalRow(cursor, record, date)
        cursor.movePosition(QtGui.QTextCursor.End)
        return cursor


    def printDailyJournalRow(self, cursor, record, date):
        time = forceTime(record.value('time'))
        clientId = forceRef(record.value('client_id'))
        if clientId:
            primaryMark = u'П' if forceBool(record.value('isPrimary')) else ''
            clientIdentifier = forceString(record.value('clientIdentifier'))
            name = formatName(record.value('lastName'), record.value('firstName'), record.value('patrName'))
            birthDate = forceDate(record.value('birthDate'))
            age = calcAge(birthDate, date)
            birthDateAndAge = '%s (%s)'%(birthDate.toString('dd.MM.yyyy'), age)
            attaches =  formatAttachesAsHTML(getClientAttaches(clientId), clientId, date)
            recordClass = forceInt(record.value('recordClass'))
            if recordClass == 3:
                recordName = u'Самозапись через интернет'
            elif recordClass == 2:
                recordName = u'Запись через call-центр'
            elif recordClass == 1:
                recordName = u'Самозапись через инфомат'
            else:
                recordPersonId = forceRef(record.value('recordPerson_id'))
                recordName = u'Записал(a) ' + forceString(QtGui.qApp.db.translate('vrbPersonWithSpeciality', 'id', recordPersonId, 'name'))
            note = forceString(record.value('note'))
            complaint = forceString(record.value('complaint'))
        else:
            primaryMark = clientIdentifier = name = birthDateAndAge = attaches = note = complaint = recordName = ''
        row = self.currentTable.addRow()
        self.currentTable.setText(row, 0, self.rowInTable)
        self.currentTable.setText(row, 1, primaryMark)
        self.currentTable.setText(row, 2, clientIdentifier)
        self.currentTable.setText(row, 3, time.toString('hh:mm') if time else u'--:--')
        self.currentTable.setText(row, 4, name)
        self.currentTable.setText(row, 5, birthDateAndAge)
        self.currentTable.setHtml(row, 6, attaches)
        self.currentTable.setText(row, 7, '\n'.join([i for i in [recordName, note, complaint] if i]))
        self.calcRowAndInsertPageBreakIfRequired(cursor)


    def calcRowAndInsertPageBreakIfRequired(self, cursor):
        self.rowInTable += 1
        self.rowOnPage += 1
        if self.pageRowCount != 0 and self.rowOnPage >= self.pageRowCount:
            self.insertPageBreak(cursor)



class CDailyJournalBeforeRecord2(CDailyJournalBeforeRecord):
    def __init__(self, parent = None):
        CDailyJournalBeforeRecord.__init__(self, parent)
        self.setTitle(u'Суточный журнал предварительной записи - вариант 2')
        self.table_columns = [
            ('3%',  [u'№'], CReportBase.AlignRight),
            ('5%',  [u'Время'], CReportBase.AlignLeft),
            ('20%', [u'Пациент'], CReportBase.AlignLeft),
            ('20%', [u'Страховая компания'], CReportBase.AlignLeft),
            ('22%', [u'Адрес прописки'], CReportBase.AlignLeft),
            ('22%', [u'Адрес проживания'], CReportBase.AlignLeft),
            ('25%', [u'Телефон'], CReportBase.AlignLeft),
            ]

    def getSheduleItemData(self, schedule, accountingSystemId, isPrimary, showEmptyItems, order, isClientIdentifier):
        db = QtGui.qApp.db

        if accountingSystemId == -2: # адрес проживания
            clientIdentifier = 'getClientLocAddress(Schedule_Item.client_id)'
        elif accountingSystemId == -1: # адрес регистрации
            clientIdentifier = 'getClientRegAddress(Schedule_Item.client_id)'
        elif accountingSystemId is None: #
            clientIdentifier = 'Schedule_Item.client_id'
        else:
            clientIdentifier = 'getClientIdentifier(Schedule_Item.client_id,%d)' % accountingSystemId

        tableScheduleItem = db.table('Schedule_Item')
        cond = [tableScheduleItem['deleted'].eq(0),
                tableScheduleItem['master_id'].eq(schedule.value('id')),
               ]
        joinIdentifier = u''
        if isClientIdentifier and accountingSystemId > 0:
            tableClientIdentification = db.table('ClientIdentification')
            joinIdentifier = u'''INNER JOIN ClientIdentification ON ClientIdentification.client_id = Client.id
            AND ClientIdentification.id = (SELECT MAX(CI.id)
                                     FROM ClientIdentification AS CI
                                     WHERE CI.client_id = Client.id
                                       AND CI.deleted = 0
                                       AND CI.accountingSystem_id = %s)'''%(accountingSystemId)
            cond.append(tableClientIdentification['accountingSystem_id'].eq(accountingSystemId))
        if not showEmptyItems or isPrimary:
            cond.append(tableScheduleItem['client_id'].isNotNull())
        if order == 0: # по идентификатору
            orderCols = 'clientIdentifier, Schedule_Item.time'
        elif order == 2: # по фио
            orderCols = 'Client.lastName, Client.firstName, Client.patrName, Schedule_Item.time'
        else: # order == 1: # по времени
            orderCols = 'Schedule_Item.time'

        if isPrimary:
            havingCond = 'isPrimary'
        else:
            havingCond = ''

        stmt = 'SELECT Schedule_Item.time,'                                     \
                      ' Schedule_Item.client_id,'                               \
                      ' Schedule_Item.note,'                                    \
               ' %(clientIdentifier)s AS clientIdentifier,'                     \
               ' formatClientPolicyInsurer(getClientPolicyId(Schedule_Item.client_id, 1)) AS insurerName,'    \
               ' getClientLocAddress(Schedule_Item.client_id) AS locAddress,'   \
               ' getClientRegAddress(Schedule_Item.client_id) AS regAddress,'   \
               ' NOT EXISTS(SELECT NULL '                                       \
                        ' FROM Schedule_Item AS SI '                            \
                        ' JOIN Schedule AS S ON S.id = SI.master_id'            \
                        ' WHERE SI.deleted=0'                                   \
                          ' AND S.deleted=0'                                    \
                          ' AND SI.client_id = Schedule_Item.client_id'         \
                          ' AND S.date = Schedule.date'                         \
                          ' AND SI.time<Schedule_Item.time) AS isPrimary,'      \
               ' Client.lastName, Client.firstName, Client.patrName,'           \
               ' Client.birthDate'                                              \
               ' FROM Schedule_Item'                                            \
               ' LEFT JOIN Client   ON Client.id = Schedule_Item.client_id'     \
               ' LEFT JOIN Schedule ON Schedule.id = Schedule_Item.master_id'   \
               ' %(joinIdentifier)s'                                            \
               ' WHERE %(cond)s'                                                \
               ' %(havingKV)s%(havingCond)s '                                   \
               ' ORDER BY %(order)s'                                            \
               % dict(clientIdentifier = clientIdentifier,
                      joinIdentifier   = joinIdentifier,
                      cond             = db.joinAnd(cond),
                      havingKV         = 'HAVING ' if havingCond else '',
                      havingCond       = havingCond,
                      order            = orderCols)
        return db.query(stmt)


    def printDailyJournalRow(self, cursor, record, date):
        time = forceTime(record.value('time'))
        clientId = forceRef(record.value('client_id'))
        if clientId:
            name = formatName(record.value('lastName'), record.value('firstName'), record.value('patrName'))
            birthDate = forceDate(record.value('birthDate'))
            nameAndBirthDate = '%s (%s)'%(name, birthDate.toString('dd.MM.yyyy'))
            insurerName = forceString(record.value('insurerName'))
            regAddress  = forceString(record.value('regAddress'))
            locAddress  = forceString(record.value('locAddress'))
            phone = getClientPhonesEx(clientId)
        else:
            nameAndBirthDate = insurerName = regAddress = locAddress = phone = ''
        row = self.currentTable.addRow()
        self.currentTable.setText(row, 0, self.rowInTable)
        self.currentTable.setText(row, 1, time.toString('hh:mm') if time else u'--:--')
        self.currentTable.setText(row, 2, nameAndBirthDate)
        self.currentTable.setText(row, 3, insurerName)
        self.currentTable.setText(row, 4, regAddress)
        self.currentTable.setHtml(row, 5, locAddress)
        self.currentTable.setText(row, 6, phone)
        self.calcRowAndInsertPageBreakIfRequired(cursor)


class CDailyJournalBeforeRecordSetup(QtGui.QDialog, Ui_DailyJournalBeforeRecordSetup):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cmbAccountingSystem.setTable('rbAccountingSystem', addNone=True, filter='showInClientInfo = 1')
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.setFirstEntryPatientVisible(False)


    def setFirstEntryPatientVisible(self, value):
        self.isFirstEntryPatient = value
        self.chkFirstEntryPatient.setVisible(value)


    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDateDailyJournal', QDate.currentDate()))
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))
        self.cmbPerson.setValue(params.get('personId', None))
        self.cmbAccountingSystem.setValue(params.get('accountingSystemId', None))
        self.chkClientIdentifier.setChecked(params.get('isClientIdentifier', 0))
        self.cmbOrder.setCurrentIndex(params.get('order', 0))
        self.cmbIsPrimary.setCurrentIndex(params.get('isPrimary', 0))
        self.chkShowEmptyItems.setChecked(forceBool(params.get('showEmptyItems', 0)))
        self.chkTablePerPage.setChecked(forceBool(params.get('outputTablePerPage', 0)))
        self.chkOutputNotScheduled.setChecked(forceBool(params.get('outputNotScheduled', 0)))
        self.spnRowCount.setValue(params.get('rowCount', 0))
        if self.isFirstEntryPatient:
            self.chkFirstEntryPatient.setChecked(forceBool(params.get('isFirstEntryPatient', 0)))



    def params(self):
        return dict(begDateDailyJournal = self.edtBegDate.date(),
                    orgStructureId      = self.cmbOrgStructure.value(),
                    personId            = self.cmbPerson.value(),
                    accountingSystemId  = self.cmbAccountingSystem.value(),
                    isClientIdentifier  = self.chkClientIdentifier.isChecked(),
                    order               = self.cmbOrder.currentIndex(),
                    isPrimary           = self.cmbIsPrimary.currentIndex(),
                    showEmptyItems      = self.chkShowEmptyItems.isChecked(),
                    outputTablePerPage  = self.chkTablePerPage.isChecked(),
                    outputNotScheduled  = self.chkOutputNotScheduled.isChecked(),
                    rowCount            = self.spnRowCount.value(),
                    isFirstEntryPatient = self.chkFirstEntryPatient.isChecked() if self.isFirstEntryPatient else 0
                   )


    @pyqtSignature('int')
    def on_cmbOrgStructure_currentIndexChanged(self, index):
        orgStructureId = self.cmbOrgStructure.value()
        self.cmbPerson.setOrgStructureId(orgStructureId)


    @pyqtSignature('int')
    def on_cmbIsPrimary_currentIndexChanged(self, index):
        if not self.cmbIsPrimary.currentIndex():
            self.chkShowEmptyItems.setEnabled(True)
        else:
            self.chkShowEmptyItems.setChecked(False)
            self.chkShowEmptyItems.setEnabled(False)

