# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2023 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
##
## Модель и таблица расписания работ
##
#############################################################################

import pickle

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QByteArray, QDate, QMimeData, QModelIndex, QObject, QVariant, SIGNAL

from library.crbcombobox import CRBComboBox
from library.DialogBase  import CDialogBase
from library.InDocTable  import CRecordListModel, CInDocTableView, CRBInDocTableCol, CTimeInDocTableCol, CIntInDocTableCol
from library.Utils       import firstYearDay, forceRef, forceBool
from Timeline.Schedule   import getPeriodLength
from Resources.JobTypeComboBox import CJobTypeInDocTableCol
from Resources.JobSchedule     import CJob



class CJobsModel(CRecordListModel):
    def __init__(self, parent):
        CRecordListModel.__init__(self, parent)

        self.addCol(CJobTypeInDocTableCol(u'Тип', 'jobType_id', 20)).setToolTip(u'Тип работы').setSortable()
        self.addCol(CRBInDocTableCol(u'Назначение', 'jobPurpose_id', 10, 'rbJobPurpose', showFields=CRBComboBox.showCodeAndName)).setToolTip(u'Назначение работы').setSortable()
        self.addCol(CTimeInDocTableCol(u'Начало', 'begTime', 10)).setToolTip(u'Время начала работы').setSortable()
        self.addCol(CTimeInDocTableCol(u'Окончание', 'endTime', 10)).setToolTip(u'Время окончания работы').setSortable()
        self.addCol(CIntInDocTableCol(u'План', 'quantity', 5, low=0, high=999)).setToolTip(u'Плановое количество талонов').setSortable()
        self.addCol(CIntInDocTableCol(u'Ёмкость', 'capacity', 5, low=0, high=99)).setToolTip(u'Максимальный размер группы').setSortable()
        self.cntStdCols = 6

        self.orgStructureId = self.year = self.month = None
        self.daysInMonth = 0
        self.redDays = []


    def columnCount(self, index = None):
        return self.cntStdCols + 4


    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if section<self.cntStdCols:
                return CRecordListModel.headerData(self, section, orientation, role)
            else:
                return QVariant((u'Сверх плана', u'Назначено', u'Выполняется', u'Выполнено')[section-self.cntStdCols])

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
        job = self.getItem(index.row())
        if not job.isFreeToChange():
            return True
        return not column<self.cntStdCols


    def flags(self, index):
        column = index.column()
        if column<self.cntStdCols:
            return CRecordListModel.flags(self, index)
        else:
            return Qt.ItemIsSelectable
            ###|Qt.ItemIsEnabled|(Qt.ItemIsEditable if column <=1 else Qt.NoItemFlags)



    def data(self, index, role=Qt.EditRole):
        if role == Qt.FontRole:
            if self.cellReadOnly(index):
                result = QtGui.QFont()
                result.setItalic(True)
                return QVariant(result)
        if role == Qt.ToolTipRole:
            if self.cellReadOnly(index):
                return QVariant(u'Изменение запрещено')

        column = index.column()
        if column<self.cntStdCols:
            return CRecordListModel.data(self, index, role)
        else:
            if role == Qt.DisplayRole:
                job = self.getItem(index.row())
                customcolumn = column-self.cntStdCols
                if customcolumn == 0:
                    return QVariant(job.cntOutOfOrder)
                if customcolumn == 1:
                    return QVariant(job.cntReserved)
                if customcolumn == 2:
                    return QVariant(job.cntBusy)
                if customcolumn == 3:
                    return QVariant(job.cntExecuted)
#            if role == Qt.TextAlignmentRole:
#                return QVariant(Qt.AlignRight|Qt.AlignVCenter)
        return QVariant()


    def setData(self, index, value, role=Qt.EditRole):
        column = index.column()
        if 0 <= column < self.cntStdCols:
            row = index.row()
            job = self._items[row]
            if not job.isFreeToChange():
                return False
            job.cleanItems()
        return CRecordListModel.setData(self, index, value, role)


    def setOrgStructureAndMonth(self, orgStructureId, year, month, selectedDate = None):
        self.selectedDate = selectedDate
        if self.orgStructureId != orgStructureId or self.year != year or self.month != month:
            if self.orgStructureId:
                self.saveData()
            self.orgStructureId = orgStructureId
            self.year = year
            self.month = month
            begDate = QDate(self.year, self.month, 1)
            self.daysInMonth = begDate.daysInMonth()
            self.loadData()


    def loadData(self):
        self.redDays = []
        getDayOfWeek = QtGui.qApp.calendarInfo.getDayOfWeek
        for day in xrange(1, self.daysInMonth+1):
            date = QDate(self.year, self.month, day)
            if getDayOfWeek(date) in (Qt.Saturday, Qt.Sunday):
                self.redDays.append(day)

        db = QtGui.qApp.db
        table = db.table('Job')
        begDate = QDate(self.year, self.month, 1)
        records = db.getRecordList(table, '*', [table['deleted'].eq(0),
                                                table['orgStructure_id'].eq(self.orgStructureId),
                                                table['date'].ge(begDate),
                                                table['date'].lt(begDate.addMonths(1)),
                                               ],
                                        'date, begTime, id'
                                  )
        groupByDay = {}
        for record in records:
            item = CJob(record)
            day = item.date.day()
            groupByDay.setdefault(day, []).append(item)
        self._setGroupByDay(groupByDay)


    def getEmptyItem(self, date):
        result = CJob()
        result.date = date
        result.orgStructureId = self.orgStructureId
        return result


    def saveData(self):
        if self.orgStructureId and self.checkBegEndDate():
            idList = []
            for item in self.items():
                if item.jobTypeId:
                    item.save()
                    idList.append(item.id)

            db = QtGui.qApp.db
            table = db.table('Job')
            begDate = QDate(self.year, self.month, 1)
            db.markRecordsDeleted(table, [table['deleted'].eq(0),
                                          table['orgStructure_id'].eq(self.orgStructureId),
                                          table['date'].ge(begDate),
                                          table['date'].lt(begDate.addMonths(1)),
                                          'NOT '+table['id'].inlist(idList)
                                         ],
                                  )


    def checkBegEndDate(self):
        for row, item in enumerate(self.items()):
            if item.quantity > 0 and item.begTime > item.endTime:
                CDialogBase.checkValueMessage(QObject.parent(self), u'За дату %s: значение в ячейке "Окончание" %s меньше чем значение в ячейке "Начало" %s!'%(item.date.toString('dd.MM.yyyy'), item.endTime.toString('hh:mm'), item.begTime.toString('hh:mm')), False, QObject.parent(self).tblJobs, row, 3)
                return False
        return True


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
        self.beginInsertRows(QModelIndex(), row, row)
        items.insert(row, self.getEmptyItem(items[prototypeRow if len(items) > prototypeRow else -1].date))
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
            # установим свой orgStructureId_id:
            newItemData['orgStructure_id'] = self.orgStructureId
            # дату - скорректируем
            copyDate = newItemData['date']
            pasteDay = min(startDay-minDay+copyDate.day(), self.daysInMonth)
            pasteDate = QDate(self.year, self.month, pasteDay)
            dateShift = copyDate.daysTo(pasteDate)
            newItemData['date'] = pasteDate
            # job ticket-ы:
            #   во-первых - отфильтруем deleted и isExceedQuantity
            #   во-вторых - скопируем только datetime, а idx - подделаем


            copyJobTicketDicts = newItemData['items']
            pasteJobTicketDicts = []
            idx = 1
            for scheduleItemDict in copyJobTicketDicts:
                if not scheduleItemDict['isExceedQuantity'] and not scheduleItemDict['deleted']:
                    pasteJobTicketDicts.append({'datetime':scheduleItemDict['datetime'].addDays(dateShift),
                                                   'idx' : idx,
                                                  }
                                                 )
                    idx += 1
            newItemData['items'] = pasteJobTicketDicts
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


    def _filterOutJobs(self, jobs, removeExistingJobs):
        # removeExistingJobs: удалять незанятые элементы графика
        if removeExistingJobs:
            filterExpr = lambda job: not job.isFreeToChange()
        else:
            filterExpr = lambda job: job.jobTypeId
        return filter(filterExpr, jobs)


    def _addJobsFromTemplates(self, existingJobs, date, templates):
        result = existingJobs
        for template in templates:
            if template.jobTypeId:
                job = CJob()
                job.date = date
                job.orgStructureId = self.orgStructureId
                job.jobTypeId      = template.jobTypeId
                job.jobPurposeId   = template.jobPurposeId
                job.begTime        = template.begTime
                job.endTime        = template.endTime
                job.quantity       = template.quantity
                job.capacity       = template.capacity
                result.append(job)
        result.sort(key=lambda job: (job.begTime, job.jobTypeId))
        if not result:
            result.append(self.getEmptyItem(date))
        return result


    def setWorkPlan(self, (begDate, endDate), period, customLength, fillRedDays, jobTemplates, removeExistingJobs):
        groupByDay = self._getGroupByDay()

        templateByDay = {}
        for template in jobTemplates:
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
                groupByDay[day] = self._addJobsFromTemplates(self._filterOutJobs(groupByDay[day], removeExistingJobs), date, templates)
        elif period in (3, 4, 5, 6): # неделя, две, три или четыре
            # В соответствии с ISO 8601, недели начинаются с понедельника
            # и первый четверг года всегда находится в первой неделе этого года.
            firstDayOfYear = firstYearDay(begDate)
            firstMondayOfYear = firstDayOfYear.addDays((0, -1, -2, -3, 3, 2, 1)[firstDayOfYear.dayOfWeek()-1])
            for day in xrange(begDate.day(), endDate.day()+1):
                date = QDate(self.year, self.month, day)
                idx = firstMondayOfYear.daysTo(date) % periodLength
                if fillRedDays or day not in self.redDays:
                    templates = templateByDay[idx]
                else:
                    templates = []
                groupByDay[day] = self._addJobsFromTemplates(self._filterOutJobs(groupByDay[day], removeExistingJobs), date, templates)
        self._setGroupByDay(groupByDay)


    def setFlexWorkPlan(self, dates, jobTemplates, removeExistingJobs):
        groupByDay = self._getGroupByDay()
        for date in dates:
            day = date.day()
            groupByDay[day] = self._addJobsFromTemplates(self._filterOutJobs(groupByDay[day], removeExistingJobs), date, jobTemplates)
        self._setGroupByDay(groupByDay)


#    def fillTime(self):
#        for i, item in enumerate(self._items):
#            doneTime = QTime()
#            if item.jobTypeId:
#                begTime = item.begTime
#                endTime = item.endTime
#                doneTime = doneTime.addSecs(max(0, begTime.secsTo(endTime)))
#            if item.doneTime != doneTime:
#                item.doneTime = doneTime
#                self.emitRowChanged(i) # допустим, что мигания не будет
#
#
#    def setAbsence(self, begDate, endDate, fillRedDays, reasonOfAbsenceId):
#        begDay = begDate.day()
#        endDay = endDate.day()
#        for i, item in enumerate(self._items):
#            day = item.date.day()
#            if begDay<=day<=endDay and (fillRedDays or day not in self.redDays):
#                item.reasonOfAbsenceId = reasonOfAbsenceId
#                self.emitRowChanged(i) # допустим, что мигания не будет


class CJobsView(CInDocTableView):
    mimeType = 'application/x-s11/JobList'

    def __init__(self, parent):
        CInDocTableView.__init__(self, parent)
        self.verticalHeader().show()
        self.verticalHeader().setResizeMode(QtGui.QHeaderView.Fixed)
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)

        self.actInsertJob = QtGui.QAction(u'Добавить строку', self)
        self.actDeleleJob = QtGui.QAction(u'Удалить строку', self)

        self.actCopyJobs = QtGui.QAction(u'Копировать', self)
        self.actPasteJobs = QtGui.QAction(u'Вставить', self)
        self.actCopyJobs.setShortcut(QtGui.QKeySequence.Copy)
        self.actPasteJobs.setShortcut(QtGui.QKeySequence.Paste)

        menu = self.createPopupMenu()
        menu.addAction(self.actInsertJob)
        menu.addAction(self.actDeleleJob)
        menu.addSeparator()
        self.addPopupSelectAllRow()
        self.addPopupClearSelectionRow()
        menu.addSeparator()
        menu.addAction(self.actCopyJobs)
        menu.addAction(self.actPasteJobs)

        QObject.connect(self.actInsertJob, SIGNAL('triggered()'), self.on_actInsertJob_triggered)
        QObject.connect(self.actDeleleJob, SIGNAL('triggered()'), self.on_actDeleteShedule_triggered)
        QObject.connect(self.actCopyJobs,  SIGNAL('triggered()'), self.on_actCopyJobs_triggered)
        QObject.connect(self.actPasteJobs, SIGNAL('triggered()'), self.on_actPasteJobs_triggered)


    def keyPressEvent(self, event):
        if event.matches(QtGui.QKeySequence.Copy):
            self.on_actCopyJobs_triggered()
            event.accept()
        elif event.matches(QtGui.QKeySequence.Paste):
            self.on_actPasteJobs_triggered()
            event.accept()
        else:
            CInDocTableView.keyPressEvent(self, event)


    def on_popupMenu_aboutToShow(self):
        CInDocTableView.on_popupMenu_aboutToShow(self)
        row = self.currentIndex().row()
        rows = self.getSelectedRows()
        canDeleteRow = bool(rows)
        model = self.model()
        jobId = forceRef(model.value(row, u'id'))
        if jobId:
            db = QtGui.qApp.db
            table = db.table('Job_Ticket')
            record = db.getRecordEx(table, [table['id']],
            [table['master_id'].eq(jobId), table['resTimestamp'].isNotNull(), table['resConnectionId'].isNotNull(), table['deleted'].eq(0)])
            if (record and forceRef(record.value('id'))) or not model.getItem(row).isFreeToChange():
               canDeleteRow = False
        if len(rows) == 1 and rows[0] == row:
            self.actDeleleJob.setText(u'Удалить текущую строку')
        elif len(rows) == 1:
            self.actDeleleJob.setText(u'Удалить выделенную строку')
        else:
            self.actDeleleJob.setText(u'Удалить выделенные строки')
        self.actDeleleJob.setEnabled(canDeleteRow)
        self.actCopyJobs.setEnabled(bool(rows))
        mimeData = QtGui.qApp.clipboard().mimeData()
        self.actPasteJobs.setEnabled(mimeData.hasFormat(self.mimeType))


    def on_actInsertJob_triggered(self):
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
        db = QtGui.qApp.db
        tableJobTicket = db.table('Job_Ticket')
        tableAction = db.table('Action')
        tableActionProperty = db.table('ActionProperty')
        tableActionPropertyJobTicket = db.table('ActionProperty_Job_Ticket')
        tableActionPropertyType = db.table('ActionPropertyType')
        tableActionType = db.table('ActionType')
        queryRecord = tableJobTicket.innerJoin(tableActionPropertyJobTicket, tableActionPropertyJobTicket['value'].eq(tableJobTicket['id']))
        queryRecord = queryRecord.innerJoin(tableActionProperty, tableActionProperty['id'].eq(tableActionPropertyJobTicket['id']))
        queryRecord = queryRecord.innerJoin(tableAction, tableAction['id'].eq(tableActionProperty['action_id']))
        queryRecord = queryRecord.innerJoin(tableActionPropertyType, tableActionPropertyType['id'].eq(tableActionProperty['type_id']))
        queryRecord = queryRecord.innerJoin(tableActionType, tableActionType['id'].eq(tableActionPropertyType['actionType_id']))
        currentIndex = self.currentIndex()
        cnt = 0
        rows = self.getSelectedRows()
        rows.sort(reverse=True)
        for row in rows:
            job = self.model().getItem(row)
            if job and job.isFreeToChange():
                isUsed = False
                if job.id:
                    cond = [tableJobTicket['master_id'].eq(job.id),
                            tableAction['deleted'].eq(0),
                            tableActionProperty['deleted'].eq(0),
                            tableActionPropertyType['deleted'].eq(0),
                            tableActionType['deleted'].eq(0),
                            tableJobTicket['deleted'].eq(0),
                            ]
                    record = db.getRecordEx(queryRecord, [tableActionPropertyJobTicket['id']], cond)
                    isUsed = forceBool(record.value('id') if record else None)
                if not isUsed:
                    rowAfterDelete = self.model().delItem(row)
                    if row != rowAfterDelete:
                        cnt += 1
        self.clearSelection()
        self.setCurrentIndex(currentIndex.sibling(currentIndex.row()-cnt, 0))


    def on_actCopyJobs_triggered(self):
        mimeData = QMimeData()
        rows = self.getSelectedRows()
        rows.sort()
        v = pickle.dumps(self.model().getItemsForClipboard(rows))
        mimeData.setData(self.mimeType, QByteArray(v))
        QtGui.qApp.clipboard().setMimeData(mimeData)


    def on_actPasteJobs_triggered(self):
        mimeData = QtGui.qApp.clipboard().mimeData()
        if mimeData.hasFormat(self.mimeType):
            self.resetSorting()
            currentIndex = self.currentIndex()
            row = currentIndex.row()
            data = pickle.loads(mimeData.data(self.mimeType).data())
            self.model().insertFromClipboard(row, data)
            self.setCurrentIndex(currentIndex)

