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
from PyQt4.QtCore import pyqtSignature, QDate, QDateTime

from library.abstract   import abstract
from library.Utils      import calcAge, forceBool, forceDate, forceRef, forceString, formatBool, formatName

from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable
from Reports.Utils      import dateRangeAsStr

from Orgs.Utils         import getOrgStructureDescendants, getOrgStructureFullName


from Reports.Ui_ReportVisitByQueueDialog import Ui_ReportVisitByQueueDialog


class CReportVisitByQueue(CReport):
    def __init__(self, parent, reportType):
        CReport.__init__(self, parent)
        self.setTitle(u'Выполнение предварительной записи')
        self.setOrientation(QtGui.QPrinter.Landscape)
        self.reportType = reportType


    def getSetupDialog(self, parent):
        result = CReportVisitByQueueDialog(self.reportType, parent)
        result.setTitle(self.title())
        return result


    @abstract
    def getData(self, params):
        pass


    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()
        isNoteVisibled = params.get('isNoteVisibled', False)
        isPersonVisibled = params.get('isPersonVisibled', False)
        if isNoteVisibled and isPersonVisibled:
            colsSize = '12%'
        elif isNoteVisibled or isPersonVisibled:
            colsSize = '15%'
        else:
            colsSize = '18%'
        cols = [( '5%', [u'№ п/п'], CReportBase.AlignLeft),
                (colsSize, [u'Идентификатор пациента'], CReportBase.AlignLeft),
                (colsSize, [u'ФИО'], CReportBase.AlignLeft),
                (colsSize, [u'Д/р и возраст'], CReportBase.AlignLeft),
                (colsSize, [u'Дата'], CReportBase.AlignLeft),
                ( '5%', [u'Явка'], CReportBase.AlignLeft),
                (colsSize, [u'Телефон'], CReportBase.AlignLeft)
               ]
        if isNoteVisibled:
            cols.append(('15%', [u'Примечания'], CReportBase.AlignLeft))
        if isPersonVisibled:
            cols.append(('15%', [u'Врач'], CReportBase.AlignLeft))
        table = createTable(cursor, cols)
        query = self.getData(params)
        cnt = 1

        while query.next():
            record = query.record()
            clientId  = forceRef(record.value('client_id'))
            date      = forceDate(record.value('date'))
            if clientId:
                name      = formatName(record.value('lastName'), record.value('firstName'), record.value('patrName'))
                birthDate = forceDate(record.value('birthDate'))
                age       = calcAge(birthDate, date)
                birthDateAndAge = '%s (%s)' % ( forceString(birthDate), age)
                visited   = formatBool(forceBool(record.value('visited')))
                phones    = forceString(record.value('clientPhones'))
            else:
                name = birthDateAndAge = phones = ''
            i = table.addRow()
            table.setText(i, 0, cnt)
            table.setText(i, 1, clientId)
            table.setText(i, 2, name)
            table.setText(i, 3, birthDateAndAge)
            table.setText(i, 4, forceString(date))
            table.setText(i, 5, visited)
            table.setText(i, 6, phones)
            if isNoteVisibled:
                table.setText(i, 7, forceString(record.value('notes')) if clientId else u'')
            if isPersonVisibled:
                table.setText(i, 8 if isNoteVisibled else 7, forceString(record.value('personName')))
            cnt += 1
        return doc


    def dumpParams(self, cursor, params):
        description = []
        begScheduleDate = params.get('begScheduleDate', QDate())
        endScheduleDate = params.get('endScheduleDate', QDate())
        orgStructureId = params.get('orgStructureId', None)
        specialityId = params.get('specialityId', None)
        personId = params.get('personId', None)
        nextVisit = params.get('nextVisit', False)
        listOnlyWithoutVisit = params.get('listOnlyWithoutVisit', False)
        takeAccountVisitToOtherDoctor = params.get('takeAccountVisitToOtherDoctor', False)
        order = params.get('order', 0)
        if begScheduleDate or endScheduleDate:
            description.append(dateRangeAsStr(u'за период', begScheduleDate, endScheduleDate))
        if orgStructureId:
            description.append(u'подразделение: ' + getOrgStructureFullName(orgStructureId))
        else:
            description.append(u'подразделение: ЛПУ')
        if specialityId:
            specialityName = forceString(QtGui.qApp.db.translate('rbSpeciality', 'id', specialityId, 'name'))
            description.append(u'Специальность ' + specialityName)
        if personId:
            personName = forceString(QtGui.qApp.db.translate('vrbPersonWithSpeciality', 'id', personId, 'name'))
            description.append(u'Врач ' + personName)
        if nextVisit:
           description.append(u'Учитывать назначение следующей явки')
        if listOnlyWithoutVisit:
           description.append(u'Учитывать только не явившихся на прием')
        if takeAccountVisitToOtherDoctor:
           description.append(u'Учитывать явившихся к другому врачу данной специальности')
        else:
           description.append(u'Не учитывать явившихся к другому врачу данной специальности')

        description.append(u'Сортировка ' + [u'по дате', u'по ФИО пациента', u'по идентификатору пациента'][order])

        description.append(u'отчёт составлен: '+forceString(QDateTime.currentDateTime()))
        columns = [ ('100%', [], CReportBase.AlignLeft) ]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()


class CReportVisitBySchedule(CReportVisitByQueue):
    def __init__(self, parent):
        CReportVisitByQueue.__init__(self, parent, 0)
        self.setTitle(u'Отчет о выполнении предварительной записи к врачу')


    def getSetupDialog(self, parent):
        result = CReportVisitByQueueDialog(self.reportType, parent)
        result.setTitle(self.title())
        result.setChkNoteVisibled(True)
        result.setChkPersonVisibled(True)
        return result


    def getData(self, params):
        begScheduleDate = params.get('begScheduleDate', QDate())
        endScheduleDate = params.get('endScheduleDate', QDate())
        orgStructureId  = params.get('orgStructureId', QDate())
        specialityId    = params.get('specialityId', None)
        personId        = params.get('personId', None)
        isNoteVisibled  = params.get('isNoteVisibled', False)
        isPersonVisibled = params.get('isPersonVisibled', False)

        listOnlyWithoutVisit = params.get('listOnlyWithoutVisit', False)
        takeAccountVisitToOtherDoctor = params.get('takeAccountVisitToOtherDoctor', False)
        order = params.get('order', 0)

        db = QtGui.qApp.db
        tablePerson = db.table('Person')
        tableSchedule = db.table('Schedule')
        tableScheduleItem = db.table('Schedule_Item')

        cond = [ tableSchedule['deleted'].eq(0),
                 tableScheduleItem['deleted'].eq(0),
                 tableScheduleItem['client_id'].isNotNull(),
               ]

        if begScheduleDate:
            cond.append(tableSchedule['date'].ge(begScheduleDate))
        if endScheduleDate:
            cond.append(tableSchedule['date'].le(endScheduleDate))
        if personId:
            cond.append(tableSchedule['person_id'].eq(personId))
        if specialityId:
            cond.append(tablePerson['speciality_id'].eq(specialityId))
        if orgStructureId:
            cond.append(tablePerson['orgStructure_id'].inlist(getOrgStructureDescendants(orgStructureId)))
        else:
            if not personId:
                cond.append(tablePerson['org_id'].eq(QtGui.qApp.currentOrgId()))
        if listOnlyWithoutVisit:
            cond.append('vVisitExt.id IS NULL')
        if takeAccountVisitToOtherDoctor:
            visitCond = 'Person.speciality_id=vVisitExt.speciality_id'
        else:
            visitCond = 'vVisitExt.person_id = Schedule.person_id'
        if order == 0:
            orderExpr = 'Schedule.date'
        elif order == 1:
            orderExpr = 'Client.lastName, Client.firstName, Client.patrName'
        else:
            orderExpr = 'Schedule_Item.client_id'
        if isNoteVisibled:
            noteVisibled = u'Schedule_Item.note,'
        else:
            noteVisibled = u''
        if isPersonVisibled:
            personVisibled = u'formatPersonName(Person.id) as personName,'
        else:
            personVisibled = u''
        stmt = 'SELECT DISTINCT'                                                               \
               ' Schedule_Item.client_id,'                                                     \
               ' Schedule.date,'                                                               \
               ' Client.lastName, Client.firstName, Client.patrName, Client.birthDate,'        \
               ' getClientContacts(Client.id) AS clientPhones,'                                \
               ' %(noteVisibled)s'                                                             \
               ' %(personVisibled)s'                                                           \
               ' vVisitExt.id IS NOT NULL AS visited'                                          \
               ' FROM'                                                                         \
               ' Schedule_Item'                                                                \
               ' LEFT JOIN Schedule     ON Schedule.id = Schedule_Item.master_id'              \
               ' LEFT JOIN Person       ON Person.id = Schedule.person_id'                     \
               ' LEFT JOIN Client       ON Client.id = Schedule_Item.client_id'                \
               ' LEFT JOIN vVisitExt    ON vVisitExt.client_id = Schedule_Item.client_id'      \
                                         ' AND %(visitCond)s'                                  \
                                         ' AND DATE(vVisitExt.date) = Schedule.date'           \
               ' WHERE %(cond)s'                                                               \
               ' ORDER BY %(order)s' % dict( visitCond = visitCond,
                                             cond = db.joinAnd(cond),
                                             order = orderExpr,
                                             noteVisibled = noteVisibled,
                                             personVisibled = personVisibled,
                                           )
        return db.query(stmt)



class CReportVisitByNextEventDate(CReportVisitByQueue):
    def __init__(self, parent):
        CReportVisitByQueue.__init__(self, parent, 1)
        self.setTitle(u'Отчет об исполнении назначения следующей явки')


    def getData(self, params):
        begScheduleDate = params.get('begScheduleDate', QDate())
        endScheduleDate = params.get('endScheduleDate', QDate())
        orgStructureId  = params.get('orgStructureId', QDate())
        specialityId    = params.get('specialityId', None)
        personId        = params.get('personId', None)

        listOnlyWithoutVisit = params.get('listOnlyWithoutVisit', False)
        takeAccountVisitToOtherDoctor = params.get('takeAccountVisitToOtherDoctor', False)
        order = params.get('order', 0)

        db = QtGui.qApp.db
        tablePerson = db.table('Person')
        tableEvent  = db.table('Event')

        cond = [ tableEvent['deleted'].eq(0),
                 tableEvent['nextEventDate'].isNotNull(),
               ]

        if begScheduleDate:
            cond.append(tableEvent['nextEventDate'].ge(begScheduleDate))
        if endScheduleDate:
            cond.append(tableEvent['nextEventDate'].lt(endScheduleDate.addDays(1)))
        if personId:
            cond.append(tableEvent['execPerson_id'].eq(personId))
        if specialityId:
            cond.append(tablePerson['speciality_id'].eq(specialityId))
        if orgStructureId:
            cond.append(tablePerson['orgStructure_id'].inlist(getOrgStructureDescendants(orgStructureId)))
        else:
            if not personId:
                cond.append(tablePerson['org_id'].eq(QtGui.qApp.currentOrgId()))
        if listOnlyWithoutVisit:
            cond.append('vVisitExt.id IS NULL')
        if takeAccountVisitToOtherDoctor:
            visitCond = 'vVisitExt.person_id = Person.id'
        else:
            visitCond = 'Person.speciality_id=vVisitExt.speciality_id'
        if order == 0:
            orderExpr = 'Event.nextEventDate'
        elif order == 1:
            orderExpr = 'Client.lastName, Client.firstName, Client.patrName'
        else:
            orderExpr = 'Event.client_id'
        stmt = 'SELECT DISTINCT'                                                               \
               ' DATE(Event.nextEventDate) AS date,'                                           \
               ' Event.client_id,'                                                             \
               ' Client.lastName, Client.firstName, Client.patrName, Client.birthDate,'        \
               ' getClientContacts(Client.id) AS clientPhones,'                                \
               ' vVisitExt.id IS NOT NULL AS visited'                                          \
               ' FROM Event'                                                                   \
               ' LEFT JOIN Client on Client.id = Event.client_id'                              \
               ' LEFT JOIN Person ON Person.id = Event.execPerson_id'                          \
               ' LEFT JOIN vVisitExt    ON vVisitExt.client_id = Event.client_id'              \
                                         ' AND %(visitCond)s'                                  \
                                         ' AND vVisitExt.date >= DATE(Event.nextEventDate)'    \
               ' WHERE %(cond)s'                                                               \
               ' ORDER BY %(order)s' % dict( visitCond = visitCond,
                                             cond = db.joinAnd(cond),
                                             order = orderExpr,
                                           )
        return db.query(stmt)


class CReportVisitByQueueDialog(QtGui.QDialog, Ui_ReportVisitByQueueDialog):
    def __init__(self, reportType, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())
        self.cmbSpeciality.setTable('rbSpeciality', order='name')
        self.setChkNoteVisibled(False)
        self.setChkPersonVisibled(False)
#        if reportType:
#            self.chkListOnlyWithoutVisit.setVisible(False)
#            self.chkTakeAccountVisitToOtherDoctor.setVisible(False)
#        else:
#            self.chkListOnlyWithoutVisit.setVisible(True)
#            self.chkTakeAccountVisitToOtherDoctor.setVisible(True)


    def setTitle(self, title):
        self.setWindowTitle(title)

    def setChkNoteVisibled(self, value):
        self.isNoteVisibled = value
        self.chkNoteVisibled.setVisible(value)

    def setChkPersonVisibled(self, value):
        self.isPersonVisibled = value
        self.chkPersonVisibled.setVisible(value)

    def setParams(self, params):
        self.edtBegScheduleDate.setDate(params.get('begScheduleDate', QDate.currentDate()))
        self.edtEndScheduleDate.setDate(params.get('endScheduleDate', QDate.currentDate()))
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))
        self.cmbSpeciality.setValue(params.get('specialityId', None))
        self.cmbPerson.setValue(params.get('personId', None))
        self.chkListOnlyWithoutVisit.setChecked(params.get('listOnlyWithoutVisit', False))
        self.chkTakeAccountVisitToOtherDoctor.setChecked(params.get('takeAccountVisitToOtherDoctor', True))
        self.cmbOrder.setCurrentIndex(params.get('order', 0))
        if self.isNoteVisibled:
            self.chkNoteVisibled.setChecked(params.get('isNoteVisibled', False))
        if self.isPersonVisibled:
            self.chkPersonVisibled.setChecked(params.get('isPersonVisibled', False))


    def params(self):
        return dict(begScheduleDate = self.edtBegScheduleDate.date(),
                    endScheduleDate = self.edtEndScheduleDate.date(),
                    orgStructureId  = self.cmbOrgStructure.value(),
                    specialityId    = self.cmbSpeciality.value(), #tt1435
                    personId        = self.cmbPerson.value(),
                    listOnlyWithoutVisit          = self.chkListOnlyWithoutVisit.isChecked(),
                    takeAccountVisitToOtherDoctor = self.chkTakeAccountVisitToOtherDoctor.isChecked(),
                    order           = self.cmbOrder.currentIndex(),
                    isNoteVisibled  = self.chkNoteVisibled.isChecked() if self.isNoteVisibled else False,
                    isPersonVisibled= self.chkPersonVisibled.isChecked() if self.isPersonVisibled else False,
                   )


    @pyqtSignature('int')
    def on_cmbOrgStructure_currentIndexChanged(self, index):
        orgStructureId = self.cmbOrgStructure.value()
        self.cmbPerson.setOrgStructureId(orgStructureId)


    @pyqtSignature('int')
    def on_cmbSpeciality_currentIndexChanged(self, index):
        specialityId = self.cmbSpeciality.value()
        self.cmbPerson.setSpecialityId(specialityId)

