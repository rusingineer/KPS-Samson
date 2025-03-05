# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2017 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

import pickle

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QByteArray, QLocale, QMimeData, QModelIndex, QObject, QTime, QVariant, SIGNAL

from Timeline.TimeTable import checkDurationAndCapacity
from library.crbcombobox import CRBComboBox
from library.InDocTable  import CRecordListModel, CInDocTableView, CInDocTableCol, CIntInDocTableCol, CRBLikeEnumInDocTableCol, CRBInDocTableCol, CNotCleanTimeInDocTableCol
from library.Utils import forceInt, forceTime, toVariant

from Timeline.Schedule import CSchedule, CScheduleTemplate, getPeriodLength


class CPersonTimeTableModel(CRecordListModel):
    def __init__(self, parent):
        CRecordListModel.__init__(self, parent)
        self.addCol(CRBLikeEnumInDocTableCol(u'Тип', 'appointmentType',  7, CSchedule.atNames, showFields=CRBComboBox.showName)).setToolTip(u'Тип приёма').setSortable()
        self.addCol(CRBInDocTableCol(u'Назначение', 'appointmentPurpose_id', 10, 'rbAppointmentPurpose', showFields=CRBComboBox.showCodeAndName)).setToolTip(u'Назначение приёма').setSortable()
        self.addCol(CInDocTableCol(u'Каб.', 'office', 5)).setToolTip(u'Кабинет').setSortable()
        self.addCol(CNotCleanTimeInDocTableCol(u'Начало', 'begTime', 10)).setToolTip(u'Время начала приёма').setSortable()
        self.addCol(CNotCleanTimeInDocTableCol(u'Окончание', 'endTime', 10)).setToolTip(u'Время окончания приёма').setSortable()
        self.addCol(CNotCleanTimeInDocTableCol(u'Длительность', 'duration', 10)).setToolTip(u'Длительность приёма одного пациента').setSortable()
        self.addCol(CIntInDocTableCol(u'План', 'capacity', 5, low=0, high=999)).setToolTip(u'Плановое количество пациентов').setSortable()
        self.addCol(CRBInDocTableCol(u'Вид деятельности',  'activity_id',  10,  'rbActivity')).setToolTip(u'Вид деятельности')
        self.setEnableAppendLine(True)
        self.period = None
        self.customLength = 0
        self._parent = parent


    def getDayName(self, day):
        if self.period == 0: # 0 == один день
            return u'Один день'
        elif self.period == 1: # 1 == нечет/чет
            return (u'Нечётный день', u'Чётный день')[day%2]
        elif self.period == 2:
            return u'%d день' % (day+1)
        elif self.period == 3: # 2 == неделя
            l = QLocale()
            return unicode(l.standaloneDayName(1+day%7, l.LongFormat)).title()
        elif self.period in (4, 5, 6): # 2,3,4 == недели
            l = QLocale()
            return u'Нед. %d, %s' % (day//7+1, unicode(l.standaloneDayName(1+day%7, l.LongFormat)).title())
        else:
            return u''


    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            return CRecordListModel.headerData(self, section, orientation, role)
        if orientation == Qt.Vertical:
            items = self._items
            if items:
                day = items[min(section,  len(items)-1)].day
                if role == Qt.DisplayRole:
                    prevDay = items[section-1].day if section>0 else None
                    return QVariant(self.getDayName(day) if day != prevDay else '-/-')
                if role == Qt.ForegroundRole:
                    if self.period >= 3 and (day % 7) in (5, 6):
                        return QVariant(QtGui.QBrush(Qt.red))
        return QVariant()


    def cellReadOnly(self, index):
        column = index.column()
        if column == 6: # план
            row = index.row()
            if 0<=row<len(self._items):
                item = self._items[row]
                return item.duration.secsTo(QTime()) != 0
            else:
                return False
        elif column == 5: # Длительность
            row = index.row()
            if 0<=row<len(self._items):
                item = self._items[row]
                return item.capacity != 0
            else:
                return False
        return False


    def sortData(self, column, ascending):
        col = self._cols[column]
        fieldName = col.fieldName()

        if ascending:
            keyExpr = lambda(item): (item.day, col.toSortString(item.value(fieldName), item))
            self._items.sort(key = keyExpr)
        else:
            keyExpr = lambda(item): (-item.day, col.toSortString(item.value(fieldName), item))
            self._items.sort(key = keyExpr, reverse=True)
        self.emitRowsChanged(0, len(self._items)-1)


    def loadItems(self, personId, period, customLength):
        self.period = period
        self.customLength = customLength

        db = QtGui.qApp.db
        table = db.table(CScheduleTemplate.tableName)
        records = db.getRecordList(table, '*', [table['master_id'].eq(personId),
                                               ],
                                        'day, begTime'
                                  )
        groupByDay = {}
        for record in records:
            item = CScheduleTemplate(record)
            dayItems = groupByDay.setdefault(item.day, [])
            dayItems.append(item)
        items = []
        for day in xrange(getPeriodLength(period, customLength)):
            dayItems = groupByDay.get(day)
            if dayItems is None:
                items.append(self.getEmptyItem(day))
            else:
                items.extend(dayItems)
        self.setItems(items)


    def getEmptyRecord(self):
        return self.getEmptyItem(self._items[-1].day)


    def getEmptyItem(self, day):
        result = CScheduleTemplate()
        result.day = day
        return result


    def saveItems(self, personId):
        idList = []
        for item in self.items():
            item.personId = personId
            item.save()
            idList.append(item.id)

        db = QtGui.qApp.db
        table = db.table(CScheduleTemplate.tableName)
        db.deleteRecord(table, [table['master_id'].eq(personId),
                                'NOT '+table['id'].inlist(idList)
                               ],
                       )


    def setPeriod(self, period, customLength):
        if self.period != period or self.customLength != customLength:
            currLen = getPeriodLength(self.period, self.customLength)
            newLen = getPeriodLength(period, customLength)
            if currLen and self._items:
                currItems = self._items
                groupByDay = {}
                for item in currItems:
                    dayItems = groupByDay.setdefault(item.day, [])
                    dayItems.append(item)
                newItems = []
                for day in xrange(newLen):
                    dayItems = groupByDay.get(day%currLen)
                    if dayItems is None:
                        newItems.append(self.getEmptyItem(day))
                    else:
                        if day<currLen:
                            for item in dayItems:
                                item.day = day
                                newItems.append(item)
                        else:
                            for item in dayItems:
                                clonedItem = item.clone()
                                clonedItem.day = day
                                newItems.append(clonedItem)
            else:
                newItems = []
                for day in xrange(newLen):
                    newItems.append(self.getEmptyItem(day))
            self.setItems(newItems)
            self.period = period
            self.customLength = customLength


    def insertItem(self, row, prototypeRow):
        items = self._items
        day = items[prototypeRow].day
        self.beginInsertRows(QModelIndex(), row,  row)
        items.insert(row, self.getEmptyItem(day))
        self.endInsertRows()



    def delItem(self, row):
        items = self._items
        day = items[row].day
        if row+1<len(items) and items[row+1].day == day:
            # ниже есть строки с той-же самой датой
            toRemove = True
            result = row
        elif 0<row and items[row-1].day == day:
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
            #old = items[row]
            items[row] = self.getEmptyItem(day)
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

        periodLen = getPeriodLength(self.period, self.customLength)
        items = self._items
        startDay = items[min(row, len(items)-1)].day

        groupByDay = {}
        for item in items[row:]:
            dayItems = groupByDay.setdefault(item.day, [])
            dayItems.append(item)

        pasteByDay = {}
        for newItemData in data:
            item = self.getEmptyItem(0)
            item.setDict(newItemData)
            item.id = None
            dayItems = pasteByDay.setdefault(item.day, [])
            dayItems.append(item)

        minDay = min(pasteByDay.iterkeys())
        for day, pasteItems in pasteByDay.iteritems():
            actualDay = day-minDay+startDay
            if actualDay<periodLen:
                for item in pasteItems:
                    item.day = actualDay
                groupByDay[actualDay] = mergeItems(groupByDay.get(actualDay, []), pasteItems)

        newItems = items[:row]
        for day in range(startDay, periodLen):
            newItems.extend(groupByDay[day])

        self.setItems(newItems)


    def setData(self, index, value, role=Qt.EditRole):
        column = index.column()
        if column in (3, 4, 5, 6): # время, период и план
            row = index.row()
            schedule = self._items[row]
            if column == 3:
                begTime = forceTime(value)
                if begTime != schedule.begTime:
                    if schedule.capacity != 0:
                        checkCapacity = checkDurationAndCapacity(schedule.capacity, self._parent, True, begTime, schedule.endTime)
                        if checkCapacity:
                            schedule.capacity = checkCapacity
            if column == 4:
                endTime = forceTime(value)
                if endTime != schedule.endTime:
                    if schedule.capacity != 0:
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
        return CRecordListModel.setData(self, index, value, role)


class CPersonTimeTableView(CInDocTableView):
    mimeType = 'application/x-s11/ScheduleTemplateList'

    def __init__(self, parent):
        CInDocTableView.__init__(self, parent)
        self.verticalHeader().show()
        self.verticalHeader().setResizeMode(QtGui.QHeaderView.Fixed)
#        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
#        self.setAlternatingRowColors(True)
#        self.horizontalHeader().setStretchLastSection(True)
#        self.setTabKeyNavigation(True)
#        self.setEditTriggers(QtGui.QAbstractItemView.AnyKeyPressed | QtGui.QAbstractItemView.EditKeyPressed | QtGui.QAbstractItemView.SelectedClicked | QtGui.QAbstractItemView.DoubleClicked)
#        self.setFocusPolicy(Qt.StrongFocus)

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
        self.actDeleleShedule.setEnabled(canDeleteRow)
        self.actCopyShedules.setEnabled(bool(rows))
        mimeData = QtGui.qApp.clipboard().mimeData()
        self.actPasteShedules.setEnabled(mimeData.hasFormat(self.mimeType))


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
            rowAfterDelete = self.model().delItem(row)
            if row != rowAfterDelete:
                cnt += 1
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

