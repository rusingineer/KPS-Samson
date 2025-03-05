# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2022 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

import pickle
from math import ceil

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QByteArray, QDate, QMimeData, QModelIndex, QObject, QTime, QVariant, SIGNAL
from Orgs.PersonSubstitution import CPeriodDialog

from library.crbcombobox import CRBComboBox
from library.InDocTable  import CRecordListModel, CInDocTableView, CInDocTableCol, CRBLikeEnumInDocTableCol, CRBInDocTableCol, CNotCleanTimeInDocTableCol, CIntInDocTableCol
from library.Utils import firstYearDay, forceString, forceRef, forceInt, forceTime, toVariant
from Users.Rights        import urAccessEditTimeLine
from Timeline.Schedule   import CSchedule, getPeriodLength
from Users.Rights import (urAdmin, urCanChangePersonSubstitution)

def formatTimeRange(range): # должно переехать. куда-нибуть
    if range:
        start, finish = range
        return u'%s - %s' % (start.toString('HH:mm'), finish.toString('HH:mm'))
    else:
        return ''


def checkDurationAndCapacity(value, parent, checkCapacity=False, begTime=None, endTime=None):
    if not checkCapacity:
        time = forceTime(value)
        zeroDuration = QTime.fromString('00:00', 'hh:mm')
        if time != zeroDuration:
            minTime = QTime.fromString('00:05', 'hh:mm')
            maxTime = QTime.fromString('00:50', 'hh:mm')
            if not (minTime <= time <= maxTime):
                allowedTime = max(minTime if (minTime > time) else 0, maxTime if (time > maxTime) else 0)
                if QtGui.QMessageBox.question(parent, u'Внимание!',
                                              u'Длительность одного талона не может быть {0} {1} минут.\n'
                                              u'Установить длительность {1} минут?'.format(
                                                  u'менее' if allowedTime.minute() == 5 else u'более',
                                                  allowedTime.minute()),
                                              QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                              QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
                    return toVariant(allowedTime)
                else:
                    return toVariant(zeroDuration)
        else:
            return False
    else:
        capacity = forceInt(value)
        if capacity:
            workPeriodDuration = max(0, begTime.secsTo(endTime))
            duration = workPeriodDuration // capacity
            if duration != 0:
                if not (300 <= duration <= 3000):
                    if duration < 300:
                        allowedCapacity = int(ceil(float(workPeriodDuration) / 300.0))
                        formMassage = u'не более'
                        formMassage1 = u'менее 5 минут'
                    else:
                        formMassage = u'не менее'
                        formMassage1 = u'более 50 минут'
                        allowedCapacity = int(ceil(float(workPeriodDuration) / 3000.0))
                    if QtGui.QMessageBox.question(parent, u'Внимание!',
                                                  u'Длительность одного талона не может быть {2}.\n'
                                                  u'Согласно требованиям доступно {0} {1} талона(ов), создать?'.format(
                                                      formMassage, allowedCapacity, formMassage1),
                                                  QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                                  QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
                        return toVariant(allowedCapacity)
                    else:
                        return toVariant(0)
            else:
                return toVariant(0)
        else:
            return False


class CTimeTableModel(CRecordListModel):
    def __init__(self, parent):
        CRecordListModel.__init__(self, parent)
        self.addCol(CRBLikeEnumInDocTableCol(u'Тип', 'appointmentType',  7, CSchedule.atNames, showFields=CRBComboBox.showName)).setToolTip(u'Тип приёма')
        self.addCol(CRBInDocTableCol(u'Назначение', 'appointmentPurpose_id', 10, 'rbAppointmentPurpose', showFields=CRBComboBox.showCodeAndName)).setToolTip(u'Назначение приёма')
        self.addCol(CInDocTableCol(u'Каб.', 'office', 5)).setToolTip(u'Кабинет')
        self.addCol(CNotCleanTimeInDocTableCol(u'Начало', 'begTime', 10)).setToolTip(u'Время начала приёма')
        self.addCol(CNotCleanTimeInDocTableCol(u'Окончание', 'endTime', 10)).setToolTip(u'Время окончания приёма')
        self.addCol(CNotCleanTimeInDocTableCol(u'Длительность', 'duration', 10)).setToolTip(u'Длительность приёма одного пациента')
        self.addCol(CIntInDocTableCol(u'План', 'capacity', 5, low=0, high=999)).setToolTip(u'Плановое количество пациентов')
        self.addCol(CIntInDocTableCol(u'Факт', 'done', 5, low=0, high=999)).setToolTip(u'Фактическое количестово пациентов')
        self.addCol(CNotCleanTimeInDocTableCol(u'Факт.время', 'doneTime', 10)).setToolTip(u'Фактическая длительность приёма')
        self.addCol(CRBInDocTableCol(u'Причина отсутствия', 'reasonOfAbsence_id', 10, 'rbReasonOfAbsence', showFields=CRBComboBox.showCodeAndName))
        self.addCol(CRBInDocTableCol(u'Вид деятельности',  'activity_id',  10,  'rbActivity')).setToolTip(u'Вид деятельности')

        self.personId = self.year = self.month = self.begDate = None
        self.daysInMonth = 0
        self.redDays = []

        # статистика:
        self.numDays =  self.numAbsenceDays = self.numServDays = \
        self.numAmbDays  = self.numAmbFact  = self.numAmbPlan  = self.numAmbTime = \
        self.numHomeDays = self.numHomeFact = self.numHomePlan = self.numHomeTime = \
        self.numExpDays  = self.numExpFact  = self.numExpPlan  = self.numExpTime = 0
        self.readOnly = False
        self._parent = parent


    def setReadOnly(self, value):
        self.readOnly = value


    def flags(self, index):
        if self.readOnly:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return CRecordListModel.flags(self, index)


    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            return CRecordListModel.headerData(self, section, orientation, role)

        if orientation == Qt.Vertical and self.daysInMonth:
            if role == Qt.DisplayRole:
                items = self.items()
                if section==0 or items[section].date != items[section-1].date:
                    return QVariant(items[section].date.day())
                else:
                    return QVariant()
            if role == Qt.ToolTipRole:
                    return QVariant(self.items()[section].date)
            if role == Qt.ForegroundRole:
                if self.items()[section].date.day() in self.redDays:
                    return QVariant(QtGui.QBrush(Qt.red))
        return QVariant()


    def cellReadOnly(self, index):
        column = index.column()
        schedule = self.getItem(index.row())
        if not schedule.isFreeToChange():
            return (not column == 1 and column<=6) or column == 10 # 6 - это capacity
        if column == 6:
            return schedule.duration.secsTo(QTime()) != 0
        return False


    def data(self, index, role=Qt.EditRole):
        if role == Qt.FontRole:
            if self.cellReadOnly(index):
                result = QtGui.QFont()
                result.setItalic(True)
                return QVariant(result)
        if role == Qt.ToolTipRole:
            if self.cellReadOnly(index):
                return QVariant(u'Изменение запрещено, так как в очереди уже есть пациенты')
        return CRecordListModel.data(self, index, role)


    def setData(self, index, value, role=Qt.EditRole):
        column = index.column()
        if column in (3, 4, 5, 6): # время, период и план
            row = index.row()
            schedule = self._items[row]
            if not schedule.isFreeToChange():
                return False
            if column == 3:
                begTime = forceTime(value)
                if begTime != schedule.begTime:
                    if schedule.capacity != 0 and schedule.duration == QTime.fromString('00:00', 'hh:mm'):
                        checkCapacity = checkDurationAndCapacity(schedule.capacity, self._parent, True, begTime, schedule.endTime)
                        if checkCapacity:
                            schedule.capacity = checkCapacity
            if column == 4:
                endTime = forceTime(value)
                if endTime != schedule.endTime:
                    if schedule.capacity != 0 and schedule.duration == QTime.fromString('00:00', 'hh:mm'):
                        checkCapacity = checkDurationAndCapacity(schedule.capacity, self._parent, True, schedule.begTime, endTime)
                        if checkCapacity:
                            schedule.capacity = checkCapacity
            if column == 5:
                checkValue = checkDurationAndCapacity(value, self._parent)
                if checkValue:
                    value = checkValue
            if column == 6:
                checkValue = checkDurationAndCapacity(value, self._parent, True, schedule.begTime, schedule.endTime)
                if checkValue:
                    value = checkValue
            schedule.cleanItems()
        if column == 1: # назначение приема
            row = index.row()
            schedule = self._items[row]
            if value != schedule.appointmentPurposeId and schedule.items:
                if forceRef(value):
                    appointment = forceString(QtGui.qApp.db.translate('rbAppointmentPurpose', 'id', value, 'name'))
                    message = u'Применить назначение приёма "{0}" для номерков с НЕ заполненным назначением?'.format(appointment)
                else:
                    message = u'Удалить назначение приема из всех номерков в периоде?'

                if QtGui.QMessageBox.question(QtGui.qApp.mainWindow,
                                              u'Внимание!',
                                              message,
                                              QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                              QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
                    for item in schedule.items:
                        if (item.appointmentPurposeId is None or forceRef(value) is None) and item.clientId is None:
                            item.appointmentPurposeId = value
                            
                if forceRef(value):
                    message = u'Применить назначение приёма "{0}" для номерков с заполненным назначением?'.format(appointment)
                    if QtGui.QMessageBox.question(QtGui.qApp.mainWindow,
                                                    u'Внимание!',
                                                    message,
                                                    QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                                    QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
                        for item in schedule.items:
                            if item.clientId is None and item.appointmentPurposeId:
                                item.appointmentPurposeId = value
                        return CRecordListModel.setData(self, index, value, role)
        if column == 9 and (QtGui.qApp.userHasRight(urAdmin) or QtGui.qApp.userHasRight(urCanChangePersonSubstitution)) and forceInt(value) != 0:
            #print(forceInt(value))# Причина отсутствия
            row = index.row()
            item = self._items[row]
            if QtGui.QMessageBox.question(QtGui.qApp.mainWindow,
                                                    u'Внимание!',
                                                    u'Заполнить период замещения отсутствующего сотрудника?',
                                                    QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                                    QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
                dialog = CPeriodDialog()
                data = {
                    'begDate': item.date,
                    'endDate': item.date,
                    'person_id': None,
                    'record': None,
                    'absencePerson': item.personId,
                }
                dialog.loadData(data)
                dialog.exec_()
        return CRecordListModel.setData(self, index, value, role)


    def setPersonAndMonth(self, personId, year, month, selectedDate = None, isCanSaveData = True):
        self.selectedDate = selectedDate
        if self.personId != personId or self.year != year or self.month != month:
            if self.personId and isCanSaveData:
                self.saveData()
            self.personId = personId
            self.year = year
            self.month = month
            self.begDate = QDate(year, month, 1)
            self.personId = personId
            self.daysInMonth = self.begDate.daysInMonth()
            self.loadData()

    def loadData(self):
        self.redDays = []
        getDayOfWeek = QtGui.qApp.calendarInfo.getDayOfWeek
        for day in xrange(1, self.daysInMonth+1):
            date = QDate(self.year, self.month, day)
            if getDayOfWeek(date) in (Qt.Saturday, Qt.Sunday):
                self.redDays.append(day)

        db = QtGui.qApp.db
        table = db.table('Schedule')
        records = db.getRecordList(table, '*', [table['deleted'].eq(0),
                                                table['person_id'].eq(self.personId),
                                                table['date'].ge(self.begDate),
                                                table['date'].lt(self.begDate.addMonths(1)),
                                               ],
                                        'date, begTime, id'
                                  )
        groupByDay = {}
        for record in records:
            item = CSchedule(record)
            day = item.date.day()
            groupByDay.setdefault(day, []).append(item)
        self._setGroupByDay(groupByDay)


    def getEmptyItem(self, date):
        result = CSchedule()
        result.date = date
        result.personId = self.personId
        return result


    def saveData(self):
        if self.personId:
            idList = []
            for item in self.items():
                item.save()
                idList.append(item.id)

            db = QtGui.qApp.db
            table = db.table('Schedule')
            db.markRecordsDeleted(table, [table['deleted'].eq(0),
                                          table['person_id'].eq(self.personId),
                                          table['date'].ge(self.begDate),
                                          table['date'].lt(self.begDate.addMonths(1)),
                                          'NOT '+table['id'].inlist(idList)
                                         ],
                                  )


    def updateStatistics(self):
        self.numDays =  self.numAbsenceDays = self.numServDays = \
        self.numAmbDays  = self.numAmbFact  = self.numAmbPlan  = self.numAmbTime = \
        self.numHomeDays = self.numHomeFact = self.numHomePlan = self.numHomeTime = \
        self.numExpDays  = self.numExpFact  = self.numExpPlan  = self.numExpTime = 0

        ambDaysSet  = set()
        homeDaysSet = set()
        expDaysSet  = set()
        absenceDaysSet = set()

        for item in self.items():
            day = item.date.day()
            if item.reasonOfAbsenceId:
                self.numAbsenceDays += 1
                absenceDaysSet.add(day)
            appointmentType = item.appointmentType
            workPeriodDuraion = max(0, item.begTime.secsTo(item.endTime))
            duration = QTime().secsTo(item.duration)
            capacity = workPeriodDuraion//duration if duration else item.capacity
            if appointmentType == CSchedule.atAmbulance:
                ambDaysSet.add(day)
                self.numAmbDays += 1
                self.numAmbPlan += capacity
                self.numAmbFact += item.done
                self.numAmbTime += workPeriodDuraion
            elif appointmentType == CSchedule.atHome:
                homeDaysSet.add(day)
                self.numHomeDays += 1
                self.numHomePlan += capacity
                self.numHomeFact += item.done
                self.numHomeTime += workPeriodDuraion
            elif appointmentType == CSchedule.atExp:
                expDaysSet.add(day)
                self.numExpDays += 1
                self.numExpPlan += capacity
                self.numExpFact += item.done
                self.numExpTime += workPeriodDuraion

        workDaysSet = ambDaysSet | homeDaysSet | expDaysSet
        self.numDays = len(workDaysSet)
        self.numAbsenceDays = len(workDaysSet & absenceDaysSet)
        self.numServDays = len((ambDaysSet | homeDaysSet)-absenceDaysSet)


    def getDate(self, row):
        return self.getItem(row).date


    def getItem(self, row):
        return self.items()[row]


    def getRowForDate(self, date):
        for row, item in enumerate(self.items()):
            if item.date == date:
                return row
        return -1


    def insertItem(self, row, prototypeRow):
        items = self.items()
        proto = items[prototypeRow]
        self.beginInsertRows(QModelIndex(), row,  row)
        items.insert(row, self.getEmptyItem(proto.date))
        self.endInsertRows()


    def delItem(self, row):
        items = self.items()
        date = items[row].date
        if row<len(items)-1 and items[row+1].date == date:
            # ниже есть строки с той-же самой датой
            toRemove = True
            result = row
        elif 0<row and items[row-1].date == date:
            # выше есть строка стой-же самой датой
            toRemove = True
            result = row-1
        else:
            # заменяем строку на строку без приёма
            toRemove = False
            result = row
        if toRemove:
            self.beginRemoveRows(QModelIndex(), row, row)
            del items[row]
            self.endRemoveRows()
        else:
            old = items[row]
            items[row] = self.getEmptyItem(old.date)
            self.emitRowChanged(row)
        return result


    def getItemsForClipboard(self, rows):
        items = self._items
        return [items[row].asDict() for row in rows]


    def insertFromClipboard(self, row, data):
        def mergeItems(curr, new):
            iCurr = 0
            iNew = 0
            while iCurr<len(curr) and iNew<len(new):
                if curr[iCurr].isEmpty():
                    curr[iCurr] = new[iNew]
                    iCurr += 1
                    iNew += 1
                else:
                    iCurr += 1
            curr.extend(new[iNew:])
            return curr

        items = self._items
        startDay = items[min(row, len(items)-1)].date.day()

        groupByDay = {}
        for item in items[row:]:
            dayItems = groupByDay.setdefault(item.date.day(), [])
            dayItems.append(item)

        pasteByDay = {}

        minDay = 99
        for newItemData in data:
            minDay = min(minDay, newItemData['date'].day())

        for newItemData in data:
            # id - не нужно
            del newItemData['id']
            # и ещё кое что ненужное
            del newItemData['createDatetime']
            del newItemData['createPerson_id']
            del newItemData['modifyDatetime']
            del newItemData['modifyPerson_id']
            # установим свой person_id:
            newItemData['person_id'] = self.personId
            # дату - скорректируем
            copyDate = newItemData['date']
            pasteDay = min(startDay-minDay+copyDate.day(), self.daysInMonth)
            pasteDate = QDate(self.year, self.month, pasteDay)
            dateShift = copyDate.daysTo(pasteDate)
            newItemData['date'] = pasteDate
            # schedule item-ы:
            #   во-первых - отфильтруем overtime
            #   во-вторых - скопируем только time, а idx - подделаем
            copyScheduleItemDicts = newItemData['items']
            pasteScheduleItemDicts = []
            idx = 0
            for scheduleItemDict in copyScheduleItemDicts:
                if not scheduleItemDict['overtime']:
                    pasteScheduleItemDicts.append({'time':scheduleItemDict['time'].addDays(dateShift),
                                                   'appointmentPurpose_id': scheduleItemDict['appointmentPurpose_id'],
                                                   'idx' : idx,
                                                  }
                                                 )
                    idx += 1
            newItemData['items'] = pasteScheduleItemDicts
            item = self.getEmptyItem(None)
            item.setDict(newItemData)
            dayItems = pasteByDay.setdefault(item.date.day(), [])
            dayItems.append(item)

        for day, pasteItems in pasteByDay.iteritems():
            groupByDay[day] = mergeItems(groupByDay.get(day, []), pasteItems)

        newItems = items[:row]
        for day in range(startDay, self.daysInMonth+1):
            newItems.extend(groupByDay[day])

        self.setItems(newItems)


    def _getGroupByDay(self):
        groupByDay = {}
        for item in self._items:
            day = item.date.day()
            groupByDay.setdefault(day, []).append(item)
        return groupByDay


    def _setGroupByDay(self, groupByDay):
        items = []
        for day in xrange(1, self.daysInMonth+1):
            dayItems = groupByDay.get(day)
            if dayItems:
                items.extend(dayItems)
            else:
                items.append(self.getEmptyItem(QDate(self.year, self.month, day)))
        self.setItems(items)


    def _filterOutSchedules(self, schedules, removeExistingSchedules):
        # removeExistingSchedules: удалять незанятые элементы графика
        if removeExistingSchedules:
            filterExpr = lambda schedule: not schedule.isFreeToChange_Custom()
        else:
            filterExpr = lambda schedule: schedule.appointmentType
        return filter(filterExpr, schedules)


    def _addSchedulesFromTemplates(self, existingSchedules, date, templates):
        result = existingSchedules
        for template in templates:
            if template.appointmentType:
                schedule = CSchedule()
                schedule.date = date
                schedule.personId = self.personId
                schedule.appointmentType = template.appointmentType
                schedule.appointmentPurposeId = template.appointmentPurposeId
                schedule.office = template.office
                schedule.begTime = template.begTime
                schedule.endTime = template.endTime
                schedule.duration = template.duration
                schedule.capacity = template.capacity
                schedule.activityId = template.activityId
                result.append(schedule)
        result.sort(key=lambda schedule: (schedule.begTime, schedule.appointmentType))
        if not result:
            result.append(self.getEmptyItem(date))
        return result


    def setWorkPlan(self, (begDate, endDate), period, customLength, fillRedDays, sheduleTemplates, removeExistingSchedules):
        groupByDay = self._getGroupByDay()

        templateByDay = {}
        for template in sheduleTemplates:
            day = template.day
            templateByDay.setdefault(day, []).append(template)

        periodLength = getPeriodLength(period, customLength)
        if period in (0, 1, 2): # 1 день, 2 дня или "произвольный":
            for day in xrange(begDate.day(), endDate.day()+1):
                date = QDate(self.year, self.month, day)
                if fillRedDays or day not in self.redDays:
                    templates = templateByDay[(day-1)%periodLength]
                else:
                    templates = []
                groupByDay[day] = self._addSchedulesFromTemplates(self._filterOutSchedules(groupByDay[day], removeExistingSchedules), date, templates)
        elif period in (3, 4, 5, 6): # неделя, две, три или четыре
            # В соответствии с ISO 8601, недели начинаются с понедельника
            # и первый четверг года всегда находится в первой неделе этого года.
            firstDayOfMonth = QDate(begDate.year(), begDate.month(), 1)
            firstMondayOfMonth = firstDayOfMonth.addDays((0, -1, -2, -3, 3, 2, 1)[firstDayOfMonth.dayOfWeek()-1])
            for day in xrange(begDate.day(), endDate.day()+1):
                date = QDate(self.year, self.month, day)
                idx = firstMondayOfMonth.daysTo(date) % periodLength
                if fillRedDays or day not in self.redDays:
                    templates = templateByDay[idx]
                else:
                    templates = []
                groupByDay[day] = self._addSchedulesFromTemplates(self._filterOutSchedules(groupByDay[day], removeExistingSchedules), date, templates)
        self._setGroupByDay(groupByDay)


    def setFlexWorkPlan(self, dates, sheduleTemplates, removeExistingSchedules):
        groupByDay = self._getGroupByDay()
        for date in dates:
            day = date.day()
            groupByDay[day] = self._addSchedulesFromTemplates(self._filterOutSchedules(groupByDay[day], removeExistingSchedules), date, sheduleTemplates)
        self._setGroupByDay(groupByDay)


    def fillTime(self):
        for i, item in enumerate(self._items):
            doneTime = QTime()
            if item.appointmentType:
                begTime = item.begTime
                endTime = item.endTime
                d = begTime.secsTo(endTime)
                if d < 0:
                    d += 86400
                doneTime = doneTime.addSecs(d)
            if item.doneTime != doneTime:
                item.doneTime = doneTime
                self.emitRowChanged(i) # допустим, что мигания не будет


    def setAbsence(self, begDate, endDate, fillRedDays, reasonOfAbsenceId):
        begDay = begDate.day()
        endDay = endDate.day()
        for i, item in enumerate(self._items):
            day = item.date.day()
            if begDay<=day<=endDay and (fillRedDays or day not in self.redDays):
                item.reasonOfAbsenceId = reasonOfAbsenceId
                self.emitRowChanged(i) # допустим, что мигания не будет


class CTimeTableView(CInDocTableView):
    mimeType = 'application/x-s11/ScheduleList'

    def __init__(self, parent):
        CInDocTableView.__init__(self, parent)
        self.verticalHeader().show()
        self.verticalHeader().setResizeMode(QtGui.QHeaderView.Fixed)
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)

        self.actInsertShedule = QtGui.QAction(u'Добавить строку', self)
        self.actDeleleShedule = QtGui.QAction(u'Удалить строку', self)

        self.actCopyShedules = QtGui.QAction(u'Копировать', self)
        self.actPasteShedules = QtGui.QAction(u'Вставить', self)
        self.actCopyShedules.setShortcut(QtGui.QKeySequence.Copy)
        self.actPasteShedules.setShortcut(QtGui.QKeySequence.Paste)

        menu = self.createPopupMenu()
        menu.addAction(self.actInsertShedule)
        menu.addAction(self.actDeleleShedule)
        menu.addSeparator()
        self.addPopupSelectAllRow()
        self.addPopupClearSelectionRow()
        menu.addSeparator()
        menu.addAction(self.actCopyShedules)
        menu.addAction(self.actPasteShedules)

        QObject.connect(self.actInsertShedule, SIGNAL('triggered()'), self.on_actInsertShedule_triggered)
        QObject.connect(self.actDeleleShedule, SIGNAL('triggered()'), self.on_actDeleteShedule_triggered)
        QObject.connect(self.actCopyShedules,  SIGNAL('triggered()'), self.on_actCopyShedules_triggered)
        QObject.connect(self.actPasteShedules, SIGNAL('triggered()'), self.on_actPasteShedules_triggered)


    def keyPressEvent(self, event):
        if event.matches(QtGui.QKeySequence.Copy):
            self.on_actCopyShedules_triggered()
            event.accept()
        elif event.matches(QtGui.QKeySequence.Paste):
            self.on_actPasteShedules_triggered()
            event.accept()
        else:
            CInDocTableView.keyPressEvent(self, event)


    def on_popupMenu_aboutToShow(self):
        CInDocTableView.on_popupMenu_aboutToShow(self)
        row = self.currentIndex().row()
        rows = self.getSelectedRows()
        canDeleteRow = bool(rows)
        if len(rows) == 1 and rows[0] == row:
            self.actDeleleShedule.setText(u'Удалить текущую строку')
        elif len(rows) == 1:
            self.actDeleleShedule.setText(u'Удалить выделенную строку')
        else:
            self.actDeleleShedule.setText(u'Удалить выделенные строки')
        rightEditTimeLine = QtGui.qApp.userHasRight(urAccessEditTimeLine)
        self.actDeleleShedule.setEnabled(canDeleteRow and rightEditTimeLine)
        self.actCopyShedules.setEnabled(bool(rows) and rightEditTimeLine)
        mimeData = QtGui.qApp.clipboard().mimeData()
        self.actPasteShedules.setEnabled(mimeData.hasFormat(self.mimeType) and rightEditTimeLine)
        self.actInsertShedule.setEnabled(self.actInsertShedule.isEnabled() and rightEditTimeLine)


    def on_actInsertShedule_triggered(self):
        currentIndex = self.currentIndex()
        if currentIndex.isValid():
            self.resetSorting()
            keyboardModifiers = QtGui.qApp.keyboardModifiers()
            if keyboardModifiers & Qt.ShiftModifier:
                row = currentIndex.row()
                self.model().insertItem(row, row)
            else:
                row = currentIndex.row()+1
                self.model().insertItem(row, row-1)
            self.setCurrentIndex(currentIndex.sibling(row, 0))
            self.clearSelection()


    def on_actDeleteShedule_triggered(self):
        currentIndex = self.currentIndex()
        cnt = 0
        rows = self.getSelectedRows()
        rows.sort(reverse=True)
        for row in rows:
            if self.model().getItem(row).isFreeToChange_Custom():
                rowAfterDelete = self.model().delItem(row)
                if row != rowAfterDelete:
                    cnt += 1
            else:
                QtGui.QMessageBox.information(self,
                                              u'Удаление строки',
                                              u'Невозможно удалить расписание, обнаружен записанный пациент.',
                                              QtGui.QMessageBox.Ok,
                                              QtGui.QMessageBox.Ok
                                              )
        self.clearSelection()
        self.setCurrentIndex(currentIndex.sibling(currentIndex.row()-cnt, 0))


    def on_actCopyShedules_triggered(self):
        mimeData = QMimeData()
        rows = self.getSelectedRows()
        rows.sort()
        v = pickle.dumps(self.model().getItemsForClipboard(rows))
        mimeData.setData(self.mimeType, QByteArray(v))
        QtGui.qApp.clipboard().setMimeData(mimeData)


    def on_actPasteShedules_triggered(self):
        mimeData = QtGui.qApp.clipboard().mimeData()
        if mimeData.hasFormat(self.mimeType):
            self.resetSorting()
            currentIndex = self.currentIndex()
            row = currentIndex.row()
            data = pickle.loads(mimeData.data(self.mimeType).data())
            self.model().insertFromClipboard(row, data)
            self.setCurrentIndex(currentIndex)

