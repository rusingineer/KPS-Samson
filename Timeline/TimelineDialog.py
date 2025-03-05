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
##
## Диалог редактирования расписания
##
#############################################################################


from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QDate, QObject, QTime, QVariant, pyqtSignature, SIGNAL

from library.Calendar                    import monthName, monthNameGC
from library.DialogBase                  import CDialogBase
from library.RecordLock                  import CRecordLockMixin
from library.SimpleProgressDialog        import CSimpleProgressDialog
from library.TableModel                  import CTableModel, CBoolCol, CDateCol, CDesignationCol, CNameCol, CRefBookCol, CTextCol
from library.Utils                       import agreeNumberAndWord, forceInt, forceString, sorry, withWaitCursor, forceDate, forceTime

from Orgs.OrgStructComboBoxes            import COrgStructureModel
from Orgs.Utils import getPersonInfo, getOrgStructureFullName
from RefBooks.Person.List                import CPersonEditor
from Registry.ResourcesDock              import CActivityModel, CActivityTreeItem
from Reports.ReportBase                  import CReportBase, createTable
from Reports.ReportView                  import CReportViewDialog
from Timeline.FlexTemplateDialog         import CFlexTemplateDialog
from Timeline.Schedule                   import CSchedule
from Timeline.ScheduleItemsDialog        import CScheduleItemsDialog
from Timeline.ScheduleItemsHistoryDialog import CScheduleItemsHistoryDialog
from Timeline.TemplateDialog             import CTemplateDialog
from Timeline.TimeTable                  import CTimeTableModel
from Users.Rights                        import urAccessRefPerson, urAccessRefPersonPersonal, urAdmin, urAccessEditTimeLine, urCanChangePersonSubstitution

from .Ui_TimelineDialog                  import Ui_TimelineDialog
from .Ui_CalcDialog                      import Ui_CalcDialog
from .Ui_AbsenceDialog                   import Ui_AbsenceDialog
from .Ui_ParamsForExternalDialog         import Ui_ParamsForExternalDialog


def calcSecondsInTime(time):
    return QTime().secsTo(time) if time else 0


class CTimelineDialog(CDialogBase, CRecordLockMixin, Ui_TimelineDialog):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        CRecordLockMixin.__init__(self)
        self.lastAttachResult = True
        self.lastPerson = None
        preferenceFilter = None
        if QtGui.qApp.preferences.appPrefs.get('TimetableOrgStructureCheckedNames'):
            preferenceFilter = [forceInt(checkedId) for checkedId in QtGui.qApp.preferences.appPrefs.get('TimetableOrgStructureCheckedNames').toList()]
        if preferenceFilter:
            orgStructureFilter = 'OrgStructure.id NOT IN ({0})'.format(','.join(map(str, preferenceFilter)))
        else:
            orgStructureFilter = None
        self.getPersonsWithoutAttach()
        self.addModels('OrgStructure', COrgStructureModel(self, QtGui.qApp.currentOrgId(), filter=orgStructureFilter))
        self.addModels('Activity',     CActivityModel(self))
        self.modelActivity.setRootItem(CActivityRootTreeItem())
        self.addModels('Personnel',    CPersonnelModel(self))
        self.addModels('TimeTable',    CTimeTableModel(self))
        # действия контекстного меню списка врачей
        self.addObject('actSelectAllRow', QtGui.QAction(u'Выделить все строки', self))
        self.addObject('actClearSelection', QtGui.QAction(u'Снять выделение', self))
        self.addObject('actChangeTimelineAccessibility', QtGui.QAction(u'Изменить параметры доступа к расписанию', self))
        self.addObject('actSetAvailableForExternal', QtGui.QAction(u'Сделать доступным для внешней системы', self))
        self.addObject('actUnsetAvailableForExternal', QtGui.QAction(u'Сделать недоступным для внешней системы', self))
#        self.addObject('actFillPerson', QtGui.QAction(u'Заполнить по персональному графику', self))

        # действия контекстного меню расписания
        self.addObject('actFillByTemplate',     QtGui.QAction(u'Заполнить по шаблону для текущего врача', self))
        self.addObject('actFillByFlexTemplate', QtGui.QAction(u'Заполнить по шаблону "скользящий график"', self))
        self.addObject('actEditScheduleItems',  QtGui.QAction(u'Номерки', self))
        self.addObject('actScheduleItemsHistory',QtGui.QAction(u'История', self))
        self.actFillByTemplate.setShortcut('F9')
        self.actFillByFlexTemplate.setShortcut('Alt+F9')

        # меню кнопки "заполнить"
        self.addObject('mnuFill', QtGui.QMenu(self))
        self.mnuFill.addAction(self.actFillByTemplate)
        self.mnuFill.addAction(self.actFillByFlexTemplate)

        # меню кнопки печать
        self.addObject('mnuPrint', QtGui.QMenu(self))
        self.addObject('actPrintPerson', QtGui.QAction(u'Индивидуальный табель', self))
        self.addObject('actPrintPersons', QtGui.QAction(u'Общий табель', self))
        self.addObject('actPrintPersonF12', QtGui.QAction(u'Табель Т-12', self))
        self.addObject('actPrintTimelineForPerson', QtGui.QAction(u'Расписание приёма врача', self))
        self.addObject('actPrintTimelineForOffices', QtGui.QAction(u'Расписание кабинетов', self))
        self.mnuPrint.addAction(self.actPrintPerson)
        self.mnuPrint.addAction(self.actPrintPersons)
        self.mnuPrint.addAction(self.actPrintPersonF12)
        self.mnuPrint.addSeparator()
        self.mnuPrint.addAction(self.actPrintTimelineForPerson)
        self.mnuPrint.addAction(self.actPrintTimelineForOffices)

        self.setupUi(self)

        self.btnFill.setMenu(self.mnuFill)
        self.btnPrint.setMenu(self.mnuPrint)

        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.activityListIsShown = False

        self.setModels(self.treeOrgStructure, self.modelOrgStructure, self.selectionModelOrgStructure)
        self.headerTreeOS = self.treeOrgStructure.header()
        self.headerTreeOS.setClickable(True)
        QObject.connect(self.headerTreeOS, SIGNAL('sectionClicked(int)'), self.onHeaderTreeOSClicked)

        self.setModels(self.tblPersonnel, self.modelPersonnel, self.selectionModelPersonnel)
        self.tblPersonnel.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tblPersonnel.createPopupMenu([self.actSelectAllRow, self.actClearSelection, self.actChangeTimelineAccessibility, self.actSetAvailableForExternal, self.actUnsetAvailableForExternal])
        self.connect(self.tblPersonnel.popupMenu(), SIGNAL('aboutToShow()'), self.onPersonnelPopupMenuAboutToShow)
        self.connect(self.tblPersonnel.horizontalHeader(), SIGNAL('sectionClicked(int)'), self._setPersonnelOrderByColumn)

        self.setModels(self.tblTimeTable, self.modelTimeTable, self.selectionModelTimeTable)
        self.tblTimeTable.horizontalHeader().moveSection(10, 1)
        self.tblTimeTable.addPopupActions([
                                           '-',
                                           self.actFillByTemplate,
                                           self.actFillByFlexTemplate,
                                           '-',
                                           self.actEditScheduleItems,
                                           self.actScheduleItemsHistory,
                                          ])
        self.connect(self.tblTimeTable.popupMenu(), SIGNAL('aboutToShow()'), self.on_tblTimeTablePopupMenu_aboutToShow)

        orgStructureIndex = self.modelOrgStructure.findItemId(QtGui.qApp.currentOrgStructureId())
        if orgStructureIndex and orgStructureIndex.isValid():
            self.treeOrgStructure.setCurrentIndex(orgStructureIndex)
            self.treeOrgStructure.setExpanded(orgStructureIndex, True)

        self.calendar.setSelectedDate(QDate.currentDate())
        self.setEnabledToEditRight()
#        self.on_calendar_selectionChanged()


    def setEnabledToEditRight(self):
        rightEditTimeLine = QtGui.qApp.userHasRight(urAccessEditTimeLine)
        self.btnFill.setEnabled(rightEditTimeLine)
        self.btnFillVisitsCount.setEnabled(rightEditTimeLine)
        self.btnFillTime.setEnabled(rightEditTimeLine)
        self.btnAbsence.setEnabled(rightEditTimeLine)
        self.modelTimeTable.setReadOnly(not rightEditTimeLine)


    def _setPersonnelOrderByColumn(self, column):
        self.tblPersonnel.setOrder(column)
        if self.activityListIsShown:
            self.updatePersonListForActivity(self.tblPersonnel.currentItemId())
        else:
            self.updatePersonListForOrgStructure(self.tblPersonnel.currentItemId())


    def exec_(self):
        self.updateTimeTable(True)
        result = CDialogBase.exec_(self)
        if QtGui.qApp.userHasRight(urAccessEditTimeLine):
            QtGui.qApp.callWithWaitCursor(self, self.modelTimeTable.saveData)
        return result

    # геттеры

    def getBegDate(self):
        return QDate(self.calendar.yearShown(), self.calendar.monthShown(), 1)


    def getEndDate(self):
        return QDate(self.calendar.yearShown(), self.calendar.monthShown(), 1).addMonths(1).addDays(-1)


    def getActivityId(self):
        if self.activityListIsShown:
            treeIndex = self.treeOrgStructure.currentIndex()
            treeItem = treeIndex.internalPointer() if treeIndex.isValid() else None
            return treeItem.id() if treeItem else None
        else:
            return None


    def getActivityIdList(self):
        # only selected - descendants is not provided
        if self.activityListIsShown:
            treeIndex = self.treeOrgStructure.currentIndex()
            itemIP = treeIndex.internalPointer()
            if itemIP:
                itemName =itemIP.name()
                if itemName == u'Не определен':
                    return []
            return self.modelActivity.getItemIdList(treeIndex)
        return None


    def getOrgStructureId(self):
        # only selected
        if self.activityListIsShown:
            return None
        else:
            treeIndex = self.treeOrgStructure.currentIndex()
            treeItem = treeIndex.internalPointer() if treeIndex.isValid() else None
            return treeItem.id() if treeItem else None


    def getOrgStructureIdList(self):
        # selected and descendants
        if self.activityListIsShown:
            return None
        else:
            treeIndex = self.treeOrgStructure.currentIndex()
            treeItem = treeIndex.internalPointer() if treeIndex.isValid() else None
            return treeItem.getItemIdList() if treeItem else []


    def getCurrentPersonId(self):
        return self.tblPersonnel.currentItemId()


    def getSelectedPersonIdList(self):
        return self.tblPersonnel.selectedItemIdList()

    # утилиты

    def getPersonIdListForActivity(self, date, activityIdList):
        if activityIdList is not None:
            db = QtGui.qApp.db
            table = db.table('Person')
            tablePersonActivity = db.table('Person_Activity')
            queryTable = table.leftJoin(tablePersonActivity,
                                        [ tablePersonActivity['master_id'].eq(table['id']),
                                          tablePersonActivity['deleted'].eq(0)
                                        ]
                                       )
            cond = [ table['deleted'].eq(0),
                     db.joinOr([table['retireDate'].isNull(), table['retireDate'].gt(date)]),
                     table['retired'].eq(0),
                     table['speciality_id'].isNotNull(),
                     table['isHideSchedule'].eq(0)
                   ]
            withoutActivity = activityIdList == []
            if withoutActivity:
                cond.append(tablePersonActivity['activity_id'].isNull())
            else:
                cond.append(tablePersonActivity['activity_id'].inlist(activityIdList))
            curOrder = self.tblPersonnel.order()
            if not curOrder:
                curOrder='lastName, firstName, patrName'
            else:
                if u'OrgStructure.name' in curOrder:
                    tableOS = db.table('OrgStructure')
                    queryTable = queryTable.leftJoin(tableOS, db.joinAnd([tableOS['id'].eq(table['orgStructure_id']), tableOS['deleted'].eq(0)]))
                if u'rbPost.name' in curOrder:
                    tableRBPost = db.table('rbPost')
                    queryTable = queryTable.leftJoin(tableRBPost, tableRBPost['id'].eq(table['post_id']))
                if u'rbSpeciality.name' in curOrder:
                    tableRBSpeciality = db.table('rbSpeciality')
                    queryTable = queryTable.leftJoin(tableRBSpeciality, tableRBSpeciality['id'].eq(table['speciality_id']))
            activityPersonIdList = db.getDistinctIdList(queryTable, idCol='Person.id', where=cond, order=curOrder)
            return activityPersonIdList
        return []


    def getPersonIdListForOrgStructure(self, date, orgStructureIdList):
        if orgStructureIdList:
            db = QtGui.qApp.db
            table = db.table('Person')
            queryTable = table
            cond = [ table['deleted'].eq(0),
                     db.joinOr([table['retireDate'].isNull(), table['retireDate'].gt(date)]),
                     table['retired'].eq(0),
                     table['speciality_id'].isNotNull(),
                     table['orgStructure_id'].inlist(orgStructureIdList),
                     table['isHideSchedule'].eq(0)
                   ]
            curOrder = self.tblPersonnel.order()
            if not curOrder:
                curOrder='lastName, firstName, patrName'
            else:
                if u'OrgStructure.name' in curOrder:
                    tableOS = db.table('OrgStructure')
                    queryTable = queryTable.leftJoin(tableOS, db.joinAnd([tableOS['id'].eq(table['orgStructure_id']), tableOS['deleted'].eq(0)]))
                if u'rbPost.name' in curOrder:
                    tableRBPost = db.table('rbPost')
                    queryTable = queryTable.leftJoin(tableRBPost, tableRBPost['id'].eq(table['post_id']))
                if u'rbSpeciality.name' in curOrder:
                    tableRBSpeciality = db.table('rbSpeciality')
                    queryTable = queryTable.leftJoin(tableRBSpeciality, tableRBSpeciality['id'].eq(table['speciality_id']))
            return db.getIdList(queryTable, idCol='Person.id', where=cond, order=curOrder)
        return []


    def updatePersonListForActivity(self, posToId=None):
        date = self.getBegDate()
        activityIdList = self.getActivityIdList()
        personIdList = self.getPersonIdListForActivity(date, activityIdList)
        self.tblPersonnel.setIdList(personIdList, posToId)


    def updatePersonListForOrgStructure(self, posToId=None):
        date = self.getBegDate()
        orgStructureIdList = self.getOrgStructureIdList()
        personIdList = self.getPersonIdListForOrgStructure(date, orgStructureIdList)
        self.tblPersonnel.setIdList(personIdList, posToId)


    def invalidatePersonTable(self):
        self.modelPersonnel.invalidateRecordsCache()
        self.modelPersonnel.emitDataChanged()


    def changeTimelineAccessibility(self):
        personIdList = self.getSelectedPersonIdList()
        if personIdList:
            dialog = CParamsForExternalDialog(self)
            try:
                if dialog.exec_():
                    db = QtGui.qApp.db
                    table = db.table('Person')
                    if dialog.chkLastAccessibleTimelineDate.isChecked() and dialog.chkTimelineAccessibilityDays.isChecked():
                        record = table.newRecord(['lastAccessibleTimelineDate', 'timelineAccessibleDays'])
                    elif dialog.chkLastAccessibleTimelineDate.isChecked():
                        record = table.newRecord(['lastAccessibleTimelineDate'])
                    elif dialog.chkTimelineAccessibilityDays.isChecked():
                        record = table.newRecord(['timelineAccessibleDays'])
                    if dialog.chkLastAccessibleTimelineDate.isChecked():
                        date = dialog.edtLastAccessibleTimelineDate.date()
                        record.setValue('lastAccessibleTimelineDate', QVariant(date) if date else QVariant())
                    if dialog.chkTimelineAccessibilityDays.isChecked():
                        days = dialog.edtTimelineAccessibilityDays.value()
                        record.setValue('timelineAccessibleDays', QVariant(days))
                    if dialog.chkLastAccessibleTimelineDate.isChecked() or dialog.chkTimelineAccessibilityDays.isChecked():
                        QtGui.qApp.callWithWaitCursor(self, db.updateRecords, table, record, table['id'].inlist(personIdList))
                        self.invalidatePersonTable()
            finally:
                dialog.deleteLater()


    def setAvailableForExternal(self, value):
        personIdList = self.getSelectedPersonIdList()
        db = QtGui.qApp.db
        table = db.table('Person')
        db.updateRecords(table,
                         table['availableForExternal'].eq(value),
                         table['id'].inlist(personIdList))
        self.invalidatePersonTable()


    def updateTimeTable(self, scrollToDate):
        prevPersonId   = self.modelTimeTable.personId
        prevYear       = self.modelTimeTable.year
        prevMonth      = self.modelTimeTable.month
        personId       = self.getCurrentPersonId()
        date           = self.calendar.selectedDate()

        if prevPersonId and self.isPersonAttach(prevPersonId):
            QtGui.qApp.callWithWaitCursor(self, self.modelTimeTable.setPersonAndMonth, personId, date.year(),
                                          date.month())
        else:
            QtGui.qApp.callWithWaitCursor(self, self.modelTimeTable.setPersonAndMonth, personId, date.year(),
                                          date.month(), isCanSaveData=False)

        row = self.modelTimeTable.getRowForDate(date)
        currentIndex = self.tblTimeTable.currentIndex()
        currentColumn = currentIndex.column() if currentIndex.isValid() else 0
        newIndex = self.modelTimeTable.index(row, currentColumn)
        self.tblTimeTable.setCurrentIndex(newIndex)
        if scrollToDate:
            self.tblTimeTable.scrollTo(newIndex, QtGui.QAbstractItemView.EnsureVisible)
        if bool(personId) and self.isPersonAttach(personId):
            self.tblTimeTable.setEnabled(True)
            self.btnFill.setEnabled(True)
            self.btnFillTime.setEnabled(True)
        else:
            self.tblTimeTable.setEnabled(False)
            self.btnFill.setEnabled(False)
            self.btnFillTime.setEnabled(False)
        if prevPersonId != self.modelTimeTable.personId or prevYear != self.modelTimeTable.year or prevMonth != self.modelTimeTable.month:
            self.updateStatisctics()


    def updateStatisctics(self):
        self.modelTimeTable.updateStatistics()

        model = self.modelTimeTable
        self.lblNumDaysValue.setText(str(model.numDays))
        self.lblAbsenceDaysValue.setText(str(model.numAbsenceDays))
        self.lblAmbDaysValue.setText(str(model.numAmbDays))
        self.lblAmbPlanValue.setText(str(model.numAmbPlan))
        self.lblHomeDaysValue.setText(str(model.numHomeDays))
        self.lblHomePlanValue.setText(str(model.numHomePlan))
        self.lblExpDaysValue.setText(str(model.numExpDays))
        self.lblExpPlanValue.setText(str(model.numExpPlan))

        self.lblHourLoadValue.setText(divIfPosible(3600*(model.numAmbFact+model.numHomeFact+model.numExpFact), model.numAmbTime+model.numHomeTime+model.numExpTime))
        self.lblServHourLoadValue.setText(divIfPosible(3600*(model.numAmbFact+model.numHomeFact), model.numAmbTime+model.numHomeTime))
        self.lblAmbHourLoadValue.setText(divIfPosible(3600*model.numAmbFact, model.numAmbTime))
        self.lblHomeHourLoadValue.setText(divIfPosible(3600*model.numHomeFact, model.numHomeTime))
        self.lblExpHourLoadValue.setText(divIfPosible(3600*model.numExpFact, model.numExpTime))

        self.lblLoadValue.setText(divIfPosible(model.numAmbFact+model.numHomeFact+model.numExpFact, model.numDays))
        self.lblServLoadValue.setText(divIfPosible(model.numAmbFact+model.numHomeFact, model.numServDays))
        self.lblAmbLoadValue.setText(divIfPosible(model.numAmbFact, model.numAmbDays))
        self.lblHomeLoadValue.setText(divIfPosible(model.numHomeFact, model.numHomeDays))
        self.lblExpLoadValue.setText(divIfPosible(model.numExpFact, model.numExpDays))

        self.lblExecValue.setText(divIfPosible(100*(model.numAmbFact+model.numHomeFact+model.numExpFact), model.numAmbPlan+model.numHomePlan+model.numExpPlan))
        self.lblServExecValue.setText(divIfPosible(100*(model.numAmbFact+model.numHomeFact), model.numAmbPlan+model.numHomePlan))
        self.lblAmbExecValue.setText(divIfPosible(100*(model.numAmbFact), model.numAmbPlan))
        self.lblHomeExecValue.setText(divIfPosible(100*(model.numHomeFact), model.numHomePlan))
        self.lblExpExecValue.setText(divIfPosible(100*(model.numExpFact), model.numExpPlan))


    def fillByTemplateForCurrentPerson(self):
        currentPersonId = self.getCurrentPersonId()
        begDate = self.getBegDate()
        endDate = self.getEndDate()
        dialog = CTemplateDialog(self)
        try:
            dialog.setPersonId(currentPersonId)
            dialog.setDateRange(begDate, endDate)
            if dialog.exec_():
                QtGui.qApp.callWithWaitCursor(self,
                                              self.modelTimeTable.setWorkPlan,
                                              dialog.getDateRange(),
                                              dialog.getPeriod(),
                                              dialog.getCustomLength(),
                                              dialog.getFillRedDays(),
                                              dialog.getTemplates(),
                                              dialog.removeExistingSchedules()
                                             )
        finally:
            dialog.deleteLater()


    def fillByFlexTemplateForCurrentPerson(self):
        begDate = self.getBegDate()
        endDate = self.getEndDate()
        dialog = CFlexTemplateDialog(self)
        try:
            dialog.setDateRange(begDate, endDate)
            dialog.setSelectedDate(self.calendar.selectedDate())

            if dialog.exec_():
                QtGui.qApp.callWithWaitCursor(self,
                                              self.modelTimeTable.setFlexWorkPlan,
                                              dialog.getSelectedDates(),
                                              dialog.getTemplates(),
                                              dialog.removeExistingSchedules()
                                              )
        finally:
            dialog.deleteLater()


    def editScheduleItems(self):
        # мы собираемся изменять времена талончиков или переносить время приёма
        # с переносом есть особенности:
        # - возможен перенос внутри периода
        # - возможен перенос между периодами одного месяца (эти периоды открыты в этом диалоге
        # - возможен перенос в "посторонние" периоды (другой врач, другой период)
        # поэтому выглядит правильным сохранить все данные
        currentIndex = self.tblTimeTable.currentIndex()
        row = currentIndex.row()
        schedule = self.modelTimeTable.items()[row]
        if schedule.appointmentType != CSchedule.atNone:
            QtGui.qApp.callWithWaitCursor(self, self.modelTimeTable.saveData)
            lockId = self.lock('Schedule', schedule.id)
            if lockId:
                try:
                    dialog = CScheduleItemsDialog(self, schedule, self.modelTimeTable.items())
                    try:
                        dialog.exec_()
                    finally:
                        dialog.deleteLater()
                finally:
                    self.releaseLock(lockId)


    def showScheduleItemsHistory(self):
        currentIndex = self.tblTimeTable.currentIndex()
        row = currentIndex.row()
        schedule = self.modelTimeTable.items()[row]
        dialog = CScheduleItemsHistoryDialog(self)
        try:
            dialog.setPersonAndDate(schedule.personId, schedule.date)
            dialog.exec_()
        finally:
            dialog.deleteLater()


    def fillVisitsCount(self, personId, appointmentTypeList, financeIdList, fillAll):
        model = self.modelTimeTable
        mapAppointmentPurposeIdToFinanceId = {}
        db = QtGui.qApp.db
        tableVisit = db.table('Visit')
        tableEvent = db.table('Event')
        tableClient = db.table('Client')
        tableSchedule = db.table('Schedule')
        tableScheduleItem = db.table('Schedule_Item')
        tableScene = db.table('rbScene')
        table = tableVisit.leftJoin(tableEvent, tableEvent['id'].eq(tableVisit['event_id']))
        table = table.leftJoin(tableScene, tableScene['id'].eq(tableVisit['scene_id']))
        table = table.innerJoin(tableSchedule, tableSchedule['person_id'].eq(tableVisit['person_id']))
        table = table.innerJoin(tableScheduleItem, tableScheduleItem['master_id'].eq(tableSchedule['id']))
        table = table.innerJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))

        for row, item in enumerate(model.items()):
            appointmentType = item.appointmentType
            if appointmentType not in appointmentTypeList:
                continue

            if item.done and not fillAll:
                continue

            appointmentPurposeId = item.appointmentPurposeId
            if appointmentPurposeId in mapAppointmentPurposeIdToFinanceId:
                financeId = mapAppointmentPurposeIdToFinanceId[appointmentPurposeId]
            else:
#                financeId = forceRef(db.translate('rbAppointmentPurpose', 'id', appointmentPurposeId, 'finance_id'))
                financeId = None
                mapAppointmentPurposeIdToFinanceId[appointmentPurposeId] = financeId

            if financeId and financeId not in financeIdList:
                continue

            cond  = [tableVisit['deleted'].eq(0),
                     tableVisit['person_id'].eq(personId),
                     tableVisit['date'].eq(item.date),
                     tableScene['appointmentType'].inlist((appointmentType, 0)),
                     tableEvent['deleted'].eq(0),
                     tableSchedule['deleted'].eq(0),
                     tableScheduleItem['deleted'].eq(0),
                     tableClient['deleted'].eq(0),
                     tableSchedule['date'].dateEq(tableVisit['date']),
                     tableScheduleItem['client_id'].eq(tableClient['id']),
                     tableScheduleItem['time'].dateEq(item.date),
                     '''TIME(Schedule_Item.time) >= TIME(%s)'''%(db.formatDate(item.begTime)),
                     '''TIME(Schedule_Item.time) <= TIME(%s)'''%(db.formatDate(item.endTime))
                    ]
            if financeId:
                cond.append(tableVisit['finance_id'].eq(financeId))
            else:
                cond.append(tableVisit['finance_id'].inlist(financeIdList))

            item.done = db.getDistinctCount(table, 'Event.client_id', where=cond)
            model.emitRowChanged(row)
        self.updateTimeTable(True)
        self.updateStatisctics()


    @withWaitCursor
    def setAbsence(self, begDate, endDate, fillRedDays, reasonOfAbsenceId):
        self.modelTimeTable.setAbsence(begDate, endDate, fillRedDays, reasonOfAbsenceId)


    @withWaitCursor
    def setAbsenceOffTable(self, personId, begDate, endDate, fillRedDays, reasonOfAbsenceId):
        db = QtGui.qApp.db
        stmt = 'UPDATE Schedule SET reasonOfAbsence_id=%(reasonOfAbsenceId)s ' \
               'WHERE deleted=0'\
               ' AND person_id=%(personId)d' \
               ' AND date>=%(begDate)s' \
               ' AND date<=%(endDate)s' % dict(
                        reasonOfAbsenceId = reasonOfAbsenceId if reasonOfAbsenceId else 'NULL',
                        personId          = personId,
                        begDate           = db.formatDate(begDate),
                        endDate           = db.formatDate(endDate),
                                              )
        db.transaction()
        try:
            db.query(stmt)
            db.commit()
        except:
            db.rollback()
            QtGui.qApp.logCurrentException()
            raise


    def fillAbsence(self, personIdList, begDate, endDate, fillRedDays, reasonOfAbsenceId):
        def stepIterator(progressDialog):
            currentPersonId = self.tblPersonnel.currentItemId()
            for personId in personIdList:
                if personId == currentPersonId:
                    self.setAbsence(begDate, endDate, fillRedDays, reasonOfAbsenceId)
                else:
                    self.setAbsenceOffTable(personId, begDate, endDate, fillRedDays, reasonOfAbsenceId)

                yield 1

        pd = CSimpleProgressDialog(self)
        pd.setWindowTitle(u'Массовое заполнение причин отсутствия')
        pd.setStepCount(len(personIdList))
        pd.setAutoStart(True)
        pd.setAutoClose(False)
        pd.setStepIterator(stepIterator)
        pd.exec_()


    def printWorkTable(self):
        db = QtGui.qApp.db
        personId = self.tblPersonnel.currentItemId()
        if not personId:
            return
        model = self.modelTimeTable
        daysInMonth = model.daysInMonth

        begDate = model.begDate

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        model = self.modelTimeTable
        begDate = model.begDate
        cursor.insertText(u'Табель на %s %d г.' % (monthName[begDate.month()], begDate.year()))
        cursor.insertBlock()

        cursor.setCharFormat(CReportBase.ReportBody)
        personInfo = getPersonInfo(personId)
        cursor.insertText(u'врач: %s, %s\n' % (personInfo['fullName'], personInfo['specialityName']))
        cursor.insertText(u'подразделение: %s, %s\n' % (personInfo['orgStructureName'], personInfo['postName']))
        if personInfo['tariffCategoryName']:
            cursor.insertText(u'тарифная категория: %s\n' % (personInfo['tariffCategoryName'], ))
        cursor.insertText(u'дата формирования: %s\n' % QDate.currentDate().toString('dd.MM.yyyy'))
        cursor.insertBlock()

        tableColumns = [
            ('3%',  [ u'Число'], CReportBase.AlignRight),        # 0
            ('10%', [ u'Амбулаторно'], CReportBase.AlignRight),  # 1
            ('3%',  [ u'Кабинет'], CReportBase.AlignRight),      # 2
            ('3%',  [ u'План'], CReportBase.AlignRight),         # 3
            ('5%',  [ u'ФЧасы'], CReportBase.AlignRight),        # 4
            ('5%',  [ u'Принято'], CReportBase.AlignRight),      # 5
            ('10%', [ u'На дому'], CReportBase.AlignRight),      # 6
            ('3%',  [ u'План'], CReportBase.AlignRight),         # 7
            ('5%',  [ u'ФЧасы'], CReportBase.AlignRight),        # 8
            ('5%',  [ u'Принято'], CReportBase.AlignRight),      # 9
            ('10%', [ u'КЭР'], CReportBase.AlignRight),          # 10
            ('3%',  [ u'Кабинет'], CReportBase.AlignRight),      # 11
            ('3%',  [ u'План'], CReportBase.AlignRight),         # 12
            ('5%',  [ u'ФЧасы'], CReportBase.AlignRight),        # 13
            ('5%',  [ u'Принято'], CReportBase.AlignRight),      # 14
            ('5%',  [ u'Прочее'], CReportBase.AlignRight),       # 15
            ('5%',  [ u'Табель'], CReportBase.AlignRight),       # 16
            ('10%', [ u'Причина отсутствия'], CReportBase.AlignLeft), # 17
                       ]
        table = createTable(cursor, tableColumns)

        data  = {}
#        total = [ u'Всего'
#                ]
        for item in model.items():
            appointmentType = item.appointmentType
            if appointmentType == CSchedule.atNone:
                continue
            day = item.date.day()
            timeRange = unicode(item.begTime.toString('HH:mm')+' - '+item.endTime.toString('HH:mm'))
#            workTime  = item.begTime.secsTo(item.endTime)
            office    = item.office
            capacity  = item.capacity
            doneTime  = QTime().secsTo(item.doneTime)
            done      = item.done
            reasonOfAbsenceId = item.reasonOfAbsenceId
            row = data.get(day)
            if row is None:
                row = [ day,
                        [], [],  0,  QTime(), 0, # амбулаторно
                        [],      0,  QTime(), 0, # на дому
                        [], [],  0,  QTime(), 0, # экспертиза
                        QTime(),                 # прочее время
                        '',                      # табель
                        []                       # причины отсутствия
                      ]
                data[day] = row
            if appointmentType == CSchedule.atAmbulance:
                row[1].append(timeRange)
                row[2].append(office)
                row[3] += capacity
                row[4] = row[4].addSecs(doneTime)
                row[5] += done
                if reasonOfAbsenceId:
                    row[17].append(reasonOfAbsenceId)
#                row[100] = row.get(100, 0) + workTime
            elif appointmentType == CSchedule.atHome:
                row[6].append(timeRange)
                row[7] += capacity
                row[8] = row[8].addSecs(doneTime)
                row[9] += done
                if reasonOfAbsenceId:
                    row[17].append(reasonOfAbsenceId)
#                row[100] = row.get(100, 0) + workTime
            elif appointmentType == CSchedule.atExp:
                row[10].append(timeRange)
                row[11].append(office)
                row[12] += capacity
                row[13] = row[13].addSecs(doneTime)
                row[14] += done
                if reasonOfAbsenceId:
                    row[17].append(reasonOfAbsenceId)
#                row[100] = row.get(100, 0) + workTime

#        for day in xrange(1, daysInMonth+1):
#            row = data.get(day)
#            row[0] = day
#            if 1 in row:
#                row[1] = ', '.join(row[1])
#            if 2 in row:
#                row[1] = ', '.join(row[1])


        for day in xrange(1, daysInMonth+1):
            i = table.addRow()
            table.setText(i, 0, day)
            row = data.get(day)
            if row:
                table.setText(i, 1, ', '.join(row[1]))
                table.setText(i, 2, ', '.join(row[2]))
                table.setText(i, 3, row[3])
                table.setText(i, 4, row[4].toString('HH:mm'))
                table.setText(i, 5, row[5])
                table.setText(i, 6, ', '.join(row[6]))
                table.setText(i, 7, row[3])
                table.setText(i, 8, row[4].toString('HH:mm'))
                table.setText(i, 9, row[5])

                table.setText(i, 10, ', '.join(row[10]))
                table.setText(i, 11, ', '.join(row[11]))
                table.setText(i, 12, row[12])
                table.setText(i, 13, row[13].toString('HH:mm'))
                table.setText(i, 14, row[14])
                if row[17]:
                    table.setText(i, 17, forceString(db.translate('rbReasonOfAbsence', 'id', row[17][0], 'name')))


        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()

#        rows = []
#        for i in range(5):
#            rows.append([None]*4)
#
#        rows[0][0]=u'Количество дней: '+(self.lblShowNumDays.text())
#        rows[1][0]=u'Дней с отсутствием: '+self.lblShowAbsenceDays.text()
#        rows[2][0]=u'Дней на приёме: '+self.lblShowAmbDays.text()
#        rows[3][0]=u'Дней на вызовах: '+self.lblShowHomeDays.text()
#        rows[4][0]=u'Дней на КЭР: '+self.lblShowExpDays.text()
#        rows[0][1]=u'Среднечасовая нагрузка: '+self.lblShowHourLoad.text()
#        rows[1][1]=u'на обслуживании '+self.lblShowServHourLoad.text()
#        rows[2][1]=u'СН на приёме: '+self.lblShowAmbHourLoad.text()
#        rows[3][1]=u'СН на вызовах: '+self.lblShowHomeHourLoad.text()
#        rows[4][1]=u'СН на КЭР: '+self.lblShowExpHourLoad.text()
#        rows[0][2]=u'Средняя подушевая нагрузка: '+self.lblShowLoad.text()
#        rows[1][2]=u'на обслуживании '+self.lblShowServLoad.text()
#        rows[2][2]=u'СПН на приёме: '+self.lblShowAmbLoad.text()
#        rows[3][2]=u'СПН на вызовах: '+self.lblShowHomeLoad.text()
#        rows[4][2]=u'СПН на КЭР: '+self.lblShowExpLoad.text()
#        rows[0][3]=u'Выполнение плана: '+self.lblShowExec.text()
#        rows[1][3]=u'на обслуживании '+self.lblShowServExec.text()
#        rows[2][3]=u'ВП на приёме: '+self.lblShowAmbExec.text()
#        rows[3][3]=u'ВП на вызовах: '+self.lblShowHomeExec.text()
#        rows[4][3]=u'ВП на КЭР: '+self.lblShowExpExec.text()
#
#        columnDescrs = [('25%', [], CReportBase.AlignLeft)]*4
#        table1 = createTable (
#            cursor, columnDescrs, headerRowCount=len(rows), border=0, cellPadding=2, cellSpacing=0)
#        for i, row in enumerate(rows):
#            for j in range(4):
#                table1.setText(i, j, row[j])
#        cursor.movePosition(QtGui.QTextCursor.End)
#        cursor.insertBlock()

#        html = doc.toHtml('utf-8')
        view = CReportViewDialog(self)
        view.setWindowTitle(u'Табель')
        view.setText(doc)
        view.exec_()

    def printWorkTableF12(self):
        db = QtGui.qApp.db
        selectedDate = self.calendar.selectedDate()
        daysInMonth = selectedDate.daysInMonth()
        currMonth = selectedDate.month()
        currYear = selectedDate.year()

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.insertHtml(u'''
            <p align="right"><small>Утв. приказом Минфина России\nот 30 марта 2015 г. №52н</small></p>
            <table width="100%" border="0">
                <tr>
                    <td width="75%">
                        <h3 align="center">Табель № ___________</h3>
                        <h3 align="center">учета использования рабочего времени</h3>
                        <p align="center">за период с 1 по {lastMonthDay} {monthNameGC} {year} г.</p>
                        <p>Учреждение: {org}</p>
                        <p>Структурное подразделение: {orgStr}</p>
                        <p>Вид табеля: _________________</p>
                    </td>
                    <td width="25%" align="right">
                        <table border="1" cellspacing="0">
                            <tr>
                                <td></td>
                                <td>Коды</td>
                            </tr>
                            <tr>
                                <td>Форма по ОКУД</td>
                                <td>0504421</td>
                            </tr>
                            <tr>
                                <td>Дата</td>
                                <td></td>
                            </tr>
                            <tr>
                                <td>по ОКПО</td>
                                <td></td>
                            </tr>
                            <tr>
                                <td>Номер корректировки</td>
                                <td></td>
                            </tr>
                            <tr>
                                <td>Дата формирования документа</td>
                                <td></td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        '''.format(lastMonthDay=daysInMonth, monthNameGC=monthNameGC[currMonth], year=currYear,
            org=forceString(db.translate('Organisation', 'id', QtGui.qApp.currentOrgId(), 'fullName')),
            orgStr=getOrgStructureFullName(self.getOrgStructureId())))

        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertText('\n')
        tableColumns = [('8%', [u'Фамилия, имя, отчество', u'', u'1'], CReportBase.AlignLeft),
            ('4%', [u'Табельный номер', u'', u'2'], CReportBase.AlignLeft),
            ('6%', [u'Должность', u'', u'3'], CReportBase.AlignLeft),
            ('2%', [u'Числа месяца', u'1', u'4'], CReportBase.AlignRight),
            ('2%', [u'', u'2', u'5'], CReportBase.AlignRight), ('2%', [u'', u'3', u'6'], CReportBase.AlignRight),
            ('2%', [u'', u'4', u'7'], CReportBase.AlignRight), ('2%', [u'', u'5', u'8'], CReportBase.AlignRight),
            ('2%', [u'', u'6', u'9'], CReportBase.AlignRight), ('2%', [u'', u'7', u'10'], CReportBase.AlignRight),
            ('2%', [u'', u'8', u'11'], CReportBase.AlignRight), ('2%', [u'', u'9', u'12'], CReportBase.AlignRight),
            ('2%', [u'', u'10', u'13'], CReportBase.AlignRight), ('2%', [u'', u'11', u'14'], CReportBase.AlignRight),
            ('2%', [u'', u'12', u'15'], CReportBase.AlignRight), ('2%', [u'', u'13', u'16'], CReportBase.AlignRight),
            ('2%', [u'', u'14', u'17'], CReportBase.AlignRight), ('2%', [u'', u'15', u'18'], CReportBase.AlignRight),
            ('4%', [u'', u'Итого часов (дней) с 1 по 15 число месяца', u'19'], CReportBase.AlignRight),
            ('2%', [u'', u'16', u'20'], CReportBase.AlignRight), ('2%', [u'', u'17', u'21'], CReportBase.AlignRight),
            ('2%', [u'', u'18', u'22'], CReportBase.AlignRight), ('2%', [u'', u'19', u'23'], CReportBase.AlignRight),
            ('2%', [u'', u'20', u'24'], CReportBase.AlignRight), ('2%', [u'', u'21', u'25'], CReportBase.AlignRight),
            ('2%', [u'', u'22', u'26'], CReportBase.AlignRight), ('2%', [u'', u'23', u'27'], CReportBase.AlignRight),
            ('2%', [u'', u'24', u'28'], CReportBase.AlignRight), ('2%', [u'', u'25', u'29'], CReportBase.AlignRight),
            ('2%', [u'', u'26', u'30'], CReportBase.AlignRight), ('2%', [u'', u'27', u'31'], CReportBase.AlignRight),
            ('2%', [u'', u'28', u'32'], CReportBase.AlignRight), ('2%', [u'', u'29', u'33'], CReportBase.AlignRight),
            ('2%', [u'', u'30', u'34'], CReportBase.AlignRight), ('2%', [u'', u'31', u'35'], CReportBase.AlignRight),
            ('4%', [u'', u'Всего часов (дней) за месяц', u'36'], CReportBase.AlignRight),
            ('4%', [u'', u'Норма часов (дней)', u'37'], CReportBase.AlignRight),
            ('4%', [u'', u'Выходные и праздничные (часы)', u'38'], CReportBase.AlignRight),
            ('4%', [u'', u'Оплачиваемый выходной (часы) ОВ', u'39'], CReportBase.AlignRight), ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 2, 1)
        table.mergeCells(0, 2, 2, 1)
        table.mergeCells(0, 3, 1, 37)

        def selectData(month, orgStructureIdList):
            db = QtGui.qApp.db
            tableSchedule = db.table('Schedule')
            tablePerson = db.table('Person')
            cols = [tableSchedule['doneTime'], tableSchedule['begTime'], tableSchedule['date'],
                tableSchedule['reasonOfAbsence_id'], tableSchedule['person_id'], tablePerson['firstName'],
                tablePerson['lastName'], tablePerson['patrName'], tablePerson['post_id'],
                ('(SELECT PI.value FROM Person_Identification PI'
                 ' JOIN rbAccountingSystem ON PI.system_id = rbAccountingSystem.id'
                 ' WHERE rbAccountingSystem.urn = "urn:oid:0504421"'
                 ' AND PI.deleted = 0 AND PI.master_id = Person.id'
                 ' LIMIT 1) AS personCode'), ]
            cond = ['MONTH(Schedule.date) = %d' % month, tableSchedule['deleted'].eq(0), tablePerson['deleted'].eq(0),
                tablePerson['orgStructure_id'].inlist(orgStructureIdList), ]
            table = tableSchedule.join(tablePerson, tableSchedule['person_id'].eq(tablePerson['id']))
            return db.getRecordList(table, cols, cond)

        def formatSeconds(seconds):
            minutes, seconds = divmod(seconds, 60)
            hours, minutes = divmod(minutes, 60)
            return '%02d:%02d' % (hours, minutes)

        def writeSeconds(table, row, rowSub, col, data, isWeekdays=False):
            timeText = u''
            timeTypeText = u''
            if len(data) == 3 and data[2]:  # причины отсутствия
                timeText += ', '.join(data[2])
            elif data[0] and data[1]:  # дневные и ночные
                timeText += formatSeconds(data[0]) + '\n' + formatSeconds(data[1])
                timeTypeText = u'Я/Н'
            elif data[0]:  # дневные
                timeText += formatSeconds(data[0])
                timeTypeText = u'Я'
            elif data[1]:  # ночные
                timeText += formatSeconds(data[1])
                timeTypeText = u'Н'
            else:
                if not isWeekdays:
                    timeTypeText = u'В'
            table.setText(row, col, timeText)
            table.setText(rowSub, col, timeTypeText)

        reportData = {}
        for record in selectData(currMonth, self.getOrgStructureIdList()):
            personId = forceInt(record.value('person_id'))
            doneTime = forceTime(record.value('doneTime'))
            begTime = forceTime(record.value('begTime'))
            date = forceDate(record.value('date'))
            reasonOfAbsenceId = forceInt(record.value('reasonOfAbsence_id'))
            if personId not in reportData:
                personName = ' '.join((forceString(record.value('lastName')), forceString(record.value('firstName')),
                                       forceString(record.value('patrName'))))
                personCode = forceString(record.value('personCode'))
                postId = forceInt(record.value('post_id'))
                postName = db.translate('rbPost', 'id', postId, 'name')
                reportLine = {}
                reportLine['name'] = personName
                reportLine['code'] = personCode
                reportLine['post'] = forceString(postName)
                reportLine['weekdays'] = [0, 0]  # дневные, ночные
                for i in xrange(1, 32):
                    reportLine[i] = [0, 0, []]  # дневные, ночные, причины отсутствия
                reportData[personId] = reportLine
            else:
                reportLine = reportData[personId]

            doneTimeSecs = QTime().secsTo(doneTime)
            isNightHours = int(begTime.hour() >= 22 or begTime.hour() <= 6)
            day = date.day()
            reportLine[day][isNightHours] += doneTimeSecs
            if date.dayOfWeek() in (6, 7):
                reportLine['weekdays'][isNightHours] += doneTimeSecs
            if reasonOfAbsenceId:
                code = forceString(db.translate('rbReasonOfAbsence', 'id', reasonOfAbsenceId, 'code'))
                reportLine[day][2].append(code)

        for reportLine in reportData.values():
            row = table.addRow()
            rowSub = table.addRow()
            table.setText(row, 0, reportLine['name'])
            table.setText(row, 1, reportLine['code'])
            table.setText(row, 2, reportLine['post'])
            total = [0, 0]  # дневные, ночные
            for i in xrange(1, 16):
                data = reportLine[i]
                total[0] += data[0]
                total[1] += data[1]
                writeSeconds(table, row, rowSub, 2 + i, data)
            writeSeconds(table, row, rowSub, 18, total)
            for i in xrange(16, 32):
                data = reportLine[i]
                total[0] += data[0]
                total[1] += data[1]
                writeSeconds(table, row, rowSub, 2 + i + 1, data)
            table.setText(row, 35, formatSeconds(total[0]) + '\n' + formatSeconds(total[1]))
            table.setText(rowSub, 35, u'Я/Н')
            writeSeconds(table, row, rowSub, 37, reportLine['weekdays'], isWeekdays=True)
            table.mergeCells(row, 0, 2, 1)
            table.mergeCells(row, 1, 2, 1)
            table.mergeCells(row, 2, 2, 1)

        view = CReportViewDialog(self)
        view.setWindowTitle(u'Табель Т-12')
        view.setText(doc)
        view.exec_()


    # обработчики сигналов
    # календарь
    @pyqtSignature('int, int')
    def on_calendar_currentPageChanged(self, year, month):
        selectedDate = self.calendar.selectedDate()
        currYear = selectedDate.year()
        currMonth = selectedDate.month()
        newDate = selectedDate.addMonths((year-currYear)*12+(month-currMonth))
        self.calendar.setSelectedDate(newDate)
        if self.activityListIsShown:
            self.updatePersonListForActivity()
        else:
            self.updatePersonListForOrgStructure()


    @pyqtSignature('')
    def on_calendar_selectionChanged(self):
        self.updateTimeTable(True)


    # список подразделений и activity
    def onHeaderTreeOSClicked(self, col):
        if self.activityListIsShown:
            self.treeOrgStructure.setModel(None)
            self.activityListIsShown = False
            self.setModels(self.treeOrgStructure, self.modelOrgStructure, self.selectionModelOrgStructure)
            orgStructureIndex = self.modelOrgStructure.findItemId(QtGui.qApp.currentOrgStructureId())
            if orgStructureIndex and orgStructureIndex.isValid():
                self.treeOrgStructure.setCurrentIndex(orgStructureIndex)
                self.treeOrgStructure.setExpanded(orgStructureIndex, True)
            self.updatePersonListForOrgStructure()
        else:
            self.treeOrgStructure.setModel(None)
            self.activityListIsShown = True
            self.setModels(self.treeOrgStructure, self.modelActivity, self.selectionModelActivity)
            activityIndex = self.modelActivity.findItemId(1)
            if activityIndex and activityIndex.isValid():
                self.treeOrgStructure.setCurrentIndex(activityIndex)
            self.treeOrgStructure.expandAll()
            self.updatePersonListForActivity()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelOrgStructure_currentChanged(self, current, previous):
        self.updatePersonListForOrgStructure()
        self.updateTimeTable(True)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelActivity_currentChanged(self, current, previous):
        self.updatePersonListForActivity()
        self.updateTimeTable(True)

    # список врачей

    @pyqtSignature('QModelIndex')
    def on_tblPersonnel_doubleClicked(self, current):
        if QtGui.qApp.userHasAnyRight([urAdmin, urAccessRefPerson, urAccessRefPersonPersonal]):
            personId = self.tblPersonnel.currentItemId()
            if personId:
                dialog = CPersonEditor(self)
                dialog.load(personId)
                dialog.exec_()
                self.getPersonsWithoutAttach()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelPersonnel_currentChanged(self, current, previous):
        self.updateTimeTable(True)


    def onPersonnelPopupMenuAboutToShow(self):
        anyPersonSelected  = bool(self.getSelectedPersonIdList())
        anyPersonExists    = self.modelPersonnel.rowCount()>0

        self.actSelectAllRow.setEnabled(anyPersonExists)
        self.actClearSelection.setEnabled(anyPersonSelected)
        rightEditTimeLine = QtGui.qApp.userHasRight(urAccessEditTimeLine)
        self.actChangeTimelineAccessibility.setEnabled(anyPersonSelected and rightEditTimeLine)
        self.actSetAvailableForExternal.setEnabled(anyPersonSelected and rightEditTimeLine)
        self.actUnsetAvailableForExternal.setEnabled(anyPersonSelected and rightEditTimeLine)


    @pyqtSignature('')
    def on_actSelectAllRow_triggered(self):
        self.tblPersonnel.selectAll()


    @pyqtSignature('')
    def on_actClearSelection_triggered(self):
        #self.tblPersonnel.clearSelection()
        self.tblPersonnel.setCurrentIndex(self.tblPersonnel.currentIndex())


    @pyqtSignature('')
    def on_actChangeTimelineAccessibility_triggered(self):
        self.changeTimelineAccessibility()


    @pyqtSignature('')
    def on_actSetAvailableForExternal_triggered(self):
        QtGui.qApp.callWithWaitCursor(self, self.setAvailableForExternal, True)


    @pyqtSignature('')
    def on_actUnsetAvailableForExternal_triggered(self):
        QtGui.qApp.callWithWaitCursor(self, self.setAvailableForExternal, False)


    # расписание
    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelTimeTable_dataChanged(self, topLeft, bottomRight):
        self.updateStatisctics()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelTimeTable_currentChanged(self, current, previous):
        if current.isValid():
            date = self.modelTimeTable.getDate(current.row())
            block = self.calendar.blockSignals(True)
            try:
                self.calendar.setSelectedDate(date)
            finally:
                self.calendar.blockSignals(block)


    def on_tblTimeTablePopupMenu_aboutToShow(self):
        currentIndex = self.tblTimeTable.currentIndex()
        row = currentIndex.row()
        if 0<=row<self.modelTimeTable.rowCount():
            schedule = self.modelTimeTable.items()[row]
            scheduleActive = schedule.appointmentType != CSchedule.atNone
        else:
            scheduleActive = False
        self.actEditScheduleItems.setEnabled(scheduleActive)
        self.actScheduleItemsHistory.setEnabled(True)
        self.on_mnuFill_aboutToShow()


    @pyqtSignature('')
    def on_actFillByTemplate_triggered(self):
        self.fillByTemplateForCurrentPerson()
        self.updateStatisctics()


    @pyqtSignature('')
    def on_actFillByFlexTemplate_triggered(self):
        self.fillByFlexTemplateForCurrentPerson()
        self.updateStatisctics()


    @pyqtSignature('')
    def on_actEditScheduleItems_triggered(self):
        self.editScheduleItems()
        self.updateStatisctics()


    @pyqtSignature('')
    def on_actScheduleItemsHistory_triggered(self):
        self.showScheduleItemsHistory()


    # кнопки

    @pyqtSignature('')
    def on_mnuFill_aboutToShow(self):
        resonPresent = self.tblPersonnel.currentItemId() is not None
        rightEditTimeLine = QtGui.qApp.userHasRight(urAccessEditTimeLine)
        self.actFillByTemplate.setEnabled(resonPresent and rightEditTimeLine)
        self.actFillByFlexTemplate.setEnabled(resonPresent and rightEditTimeLine)


    def on_mnuPrint_aboutToShow(self):
        resonPresent = self.tblPersonnel.currentItemId() is not None
        self.actPrintPerson.setEnabled(resonPresent)
        self.actPrintPersons.setEnabled(False)
#        self.mnuPrint.addSeparator()
        self.actPrintTimelineForPerson.setEnabled(resonPresent)
        self.actPrintTimelineForOffices.setEnabled(True)


    @pyqtSignature('')
    def on_actPrintTimelineForPerson_triggered(self):
        from Reports.TimelineForPerson import CTimelineForPerson
        personId = self.tblPersonnel.currentItemId()
        if not personId:
            return
        QtGui.qApp.callWithWaitCursor(self, self.modelTimeTable.saveData)
        begDate = self.modelTimeTable.begDate
        endDate = begDate.addDays(self.modelTimeTable.daysInMonth-1)
        report = CTimelineForPerson(self)
        params = {'begDate':begDate,
                  'endDate':endDate,
                  'personId':personId,
                 }

        view = CReportViewDialog(self)
        view.setWindowTitle(report.title())
        view.setText(report.build('', params))
        view.exec_()


    @pyqtSignature('')
    def on_actPrintTimelineForOffices_triggered(self):
        from Reports.TimelineForOffices import CTimelineForOffices
        QtGui.qApp.callWithWaitCursor(self, self.modelTimeTable.saveData)
        begDate = self.modelTimeTable.begDate
        endDate = begDate.addDays(self.modelTimeTable.daysInMonth-1)
        report = CTimelineForOffices(self)
        params = {'begDate':begDate,
                  'endDate': endDate,
                  'orgStructureId': self.getOrgStructureId(),
                  'activityId': self.getActivityId(),
                 }
        view = CReportViewDialog(self)
        view.setWindowTitle(report.title())
        view.setText(report.build('', params))
        view.exec_()


    @pyqtSignature('')
    def on_btnFillVisitsCount_clicked(self):
        personId = self.tblPersonnel.currentItemId()
        if not personId:
            return
        if QtGui.QMessageBox.question(self, u'Внимание!', u'Вы действительно хотите заполнить фактическое количество посещений?', QtGui.QMessageBox.Yes|QtGui.QMessageBox.No, QtGui.QMessageBox.No) != QtGui.QMessageBox.Yes:
            return
        dialog = CCalcDialog(self)
        try:
            if dialog.exec_():
                self.fillVisitsCount(personId, dialog.getAppointmentTypeList(), dialog.getFinanceIdList(), dialog.getFillAll())
        finally:
            dialog.deleteLater()


    @pyqtSignature('')
    def on_btnFillTime_clicked(self):
        if not self.tblPersonnel.currentItemId():
            return
        if QtGui.QMessageBox.question(self, u'Внимание!', u'Вы действительно хотите заполнить фактическое время на все дни месяца?', QtGui.QMessageBox.Yes|QtGui.QMessageBox.No, QtGui.QMessageBox.No) != QtGui.QMessageBox.Yes:
            return
        self.modelTimeTable.fillTime()
        self.updateStatisctics()


    @pyqtSignature('')
    def on_btnAbsence_clicked(self):
        currentPersonId = self.tblPersonnel.currentItemId()
        personIdList = self.tblPersonnel.selectedItemIdList()
        if not personIdList:
            return
        dialog = CAbsenceDialog(self)
        try:
            dialog.setDateRange(self.getBegDate(), self.getEndDate())
            if dialog.exec_():
                begDate, endDate = dialog.getDateRange()
                fillRedDays = dialog.getFillRedDays()
                reasonOfAbsenceId = dialog.getReasonOfAbsenceId()
                dialog.saveSubstitute(currentPersonId)

                if len(personIdList)>1 or currentPersonId not in personIdList:
                    self.fillAbsence(personIdList, begDate, endDate, fillRedDays, reasonOfAbsenceId)
                else:
                    self.setAbsence(begDate, endDate, fillRedDays, reasonOfAbsenceId)
        finally:
            dialog.deleteLater()

    def getPersonsWithoutAttach(self):
        db = QtGui.qApp.db
        stmt = u'''
        SELECT DISTINCT Person.id AS result
        FROM Person
        LEFT JOIN (select id, master_id, validToDate, type, deleted, orgStructure_id from Person_Order 
        where  ((validToDate IS NULL) OR (LENGTH(validToDate) = 0) OR validToDate >= now()) and type = 6 AND deleted=0  ) po_max on po_max.master_id=Person.id 
        left join Person_Order po on po.id=po_max.id LEFT JOIN rbPost rp ON Person.post_id = rp.id left join rbPost_Identification as PostIdent on rp.id = PostIdent.master_id
        LEFT JOIN rbAccountingSystem as1 ON PostIdent.system_id = as1.id
        WHERE (`Person`.`speciality_id` IS NOT NULL)
        AND (`Person`.`orgStructure_id` IS NOT NULL) 
        AND (`PostIdent`.`id` IS NOT NULL) AND (`Person`.deleted=0) AND (((po.type = 6) AND (po.documentType_id IS NULL) AND (po.deleted = 0)
        AND ((po.validToDate IS NOT NULL) OR (LENGTH(po.validToDate) != 0) OR (po.validToDate <= now()))) OR (po.id IS null)) AND (`Person`.`retired` = 0)
        AND ((`Person`.`retireDate` IS NULL) OR (`Person`.`retireDate` > ADDDATE(CURRENT_DATE(), INTERVAL 3 DAY))) 
        AND PostIdent.value IN (110,59,49) 
        AND as1.urn = 'urn:oid:1.2.643.5.1.13.13.11.1002'
        '''
        query = db.query(stmt)
        self.personsWithoutAttach = []
        while query.next():
            record = query.record()
            self.personsWithoutAttach.append(forceInt(record.value('result')))


    def isPersonAttach(self, personId=None):
        if personId != self.lastPerson:
            if not personId:
                personId = self.getCurrentPersonId()
            if personId not in self.personsWithoutAttach:
                self.lastAttachResult = True
                return True
            else:
                self.lastAttachResult = False
                return False
        else:
            return self.lastAttachResult


############################################################################################
# ниже - нужно разбираться что и для чего нужно


    def enabledButtonsForSelected(self, enabled = True):
        if self.btnCalc.isEnabled() == (not enabled):
            self.btnCalc.setEnabled(enabled)
            self.btnPrint.setEnabled(enabled)
            self.btnFillTime.setEnabled(enabled)


    @pyqtSignature('')
    def on_actPrintPerson_triggered(self):
        self.printWorkTable()


    @pyqtSignature('')
    def on_actPrintPersonF12_triggered(self):
        self.printWorkTableF12()


    @pyqtSignature('')
    def on_actPrintPersons_triggered(self):
        sorry()



#        db = QtGui.qApp.db
#        personIdList=self.modelPersonnel.idList()
#        model = self.modelTimeTable
#        begDate = model.begDate
#        daysInMonth = model.daysInMonth
#        doc = QtGui.QTextDocument()
#        cursor = QtGui.QTextCursor(doc)
#
#        cursor.setCharFormat(CReportBase.ReportTitle)
#        model = self.modelTimeTable
#        begDate = model.begDate
#        cursor.insertText(u'Табель на %s %d г.' % (monthName[begDate.month()], begDate.year()))
#        cursor.insertBlock()

#        cursor.setCharFormat(CReportBase.ReportBody)
#        treeIndex = self.treeOrgStructure.currentIndex()
#        if treeIndex.isValid():
#            treeItem = treeIndex.internalPointer()
#            def getOrgNames(orgStructure_id):
#                if not orgStructure_id:
#                    return []
#                orgStructureName = forceString(db.translate('OrgStructure', 'id', orgStructure_id, 'name'))
#                parent_id=forceInt(db.translate('OrgStructure', 'id', orgStructure_id, 'parent_id'))
#                return getOrgNames(parent_id)+[orgStructureName]
#            orgNames=getOrgNames(treeItem.id())
#            if orgNames:
#                cursor.insertText(u'подразделение: '+u', '.join(orgNames)+u'\n')
#        cursor.insertText(u'дата формирования: %s\n' % QDate.currentDate().toString('dd.MM.yyyy'))
#        cursor.insertBlock()
#
#        reasonOfAbsenceList=db.getRecordList('rbReasonOfAbsence', 'code, name', '1', 'id')
#        reasonOfAbsenceNum=len(reasonOfAbsenceList)
#        reasonOfAbsenceCodeList=[forceString(x.value('code')) for x in reasonOfAbsenceList]
#        reasonOfAbsenceNameList=[forceString(x.value('name')) for x in reasonOfAbsenceList]
#        reasonOfAbsenceCodeList.append(u'Д')
#        reasonOfAbsenceNameList.append(u'Другие причины')
#
#        f = QtGui.QTextCharFormat()
#        f.setProperty(QtGui.QTextFormat.FontSizeIncrement, QVariant(-6));
##        cursor.setCharFormat(f)
#        tableColumns = [('7%', [ u'врач'], CReportBase.AlignRight)]
#        for d in range(daysInMonth):
#            tableColumns.append(('2.4%', [str(d+1)], CReportBase.AlignRight))
#        tableColumns.append(('3%', [u'всего часы'], CReportBase.AlignRight))
#        tableColumns.append(('2%', [u'факт. дни'], CReportBase.AlignRight))
##        tableColumns.append(('2%', [u'дни неявки'], CReportBase.AlignRight))
#        for reasonOfAbsenceCode in reasonOfAbsenceCodeList:
#            tableColumns.append(('1%', [reasonOfAbsenceCode], CReportBase.AlignRight))
#        table = createTable(cursor, tableColumns)
##        cursor.setCharFormat(f)
#
#        def sec2str(sec):
#            minuts = sec//60
#            if minuts<600:
#                return '%02d:%02d'%(minuts//60, minuts%60)
#            else:
#                return '%d:%02d'%(minuts//60, minuts%60)
#
#        days_fact_all = 0
##        days_n_all = 0
#        days_n_all = [0]*(reasonOfAbsenceNum+1)
#        timesum_day = [0]*daysInMonth
#        timesum_all = 0
#        for personId in personIdList:
##            break
#            i = table.addRow()
#            table.setText(i, 0, getPersonInfo(personId)['fullName'], charFormat=f)
#            timesum=0
#            days_fact = 0
##            days_n = 0
#            days_n = [0]*(reasonOfAbsenceNum+1)
#            for d in range(daysInMonth):
#                day=begDate.addDays(d)
#                event = getEvent(etcTimeTable, day, personId)
#                eventId = forceRef(event.value('id'))
#                if not eventId:
#                    continue
#                actionAmbulance = CAction.getAction(eventId, atcAmbulance)
#                actionHome = CAction.getAction(eventId, atcHome)
#                actionExp = CAction.getAction(eventId, atcExp)
#                if not (actionAmbulance['begTime'] or actionAmbulance['endTime'] or actionHome['begTime'] or actionHome['endTime'] or actionExp['begTime'] or actionExp['endTime']):
#                    continue
#                action = CAction.getAction(eventId, atcTimeLine)
#                factTime = action['factTime']
#                if not factTime:
#                    reasonOfAbsenceId = action['reasonOfAbsence']
#                    if reasonOfAbsenceId:
#                        days_n[reasonOfAbsenceId-1]+=1
#                        days_n_all[reasonOfAbsenceId-1]+=1
#                    else:
#                        days_n[reasonOfAbsenceNum]+=1
#                        days_n_all[reasonOfAbsenceNum]+=1
##                    days_n+=1
##                    days_n_all+=1
#                    continue
#                factTimeSec = calcSecondsInTime(factTime)
#                timesum += factTimeSec
#                timesum_day[d] += factTimeSec
#                timesum_all += factTimeSec
#                days_fact+=1
#                days_fact_all+=1
#                table.setText(i, d+1, factTime.toString('HH:mm'), charFormat=f)
#            table.setText(i, daysInMonth+1, sec2str(timesum), charFormat=f)
#            table.setText(i, daysInMonth+2, days_fact, charFormat=f)
#            table.setText(i, daysInMonth+3, days_n, charFormat=f)
#            for x in range(reasonOfAbsenceNum+1):
#                table.setText(i, daysInMonth+3+x, days_n[x], charFormat=f)
#        i = table.addRow()
#        table.setText(i, 0, u'всего')
#        for d in range(daysInMonth):
#            table.setText(i, d+1, sec2str(timesum_day[d]), charFormat=f)
#        table.setText(i, daysInMonth+1, sec2str(timesum_all), charFormat=f)
#        table.setText(i, daysInMonth+2, days_fact_all, charFormat=f)
##        table.setText(i, daysInMonth+3, days_n_all, charFormat=f)
#        for x in range(reasonOfAbsenceNum+1):
#            table.setText(i, daysInMonth+3+x, days_n_all[x], charFormat=f)
#
#        cursor.movePosition(QtGui.QTextCursor.End)
#        cursor.insertBlock()
#
#        cursor.setCharFormat(CReportBase.ReportBody)
#        cursor.insertText(u'Причины отсутствия:\n')
#        for i in range(reasonOfAbsenceNum+1):
#            cursor.insertText(reasonOfAbsenceCodeList[i]+' - '+reasonOfAbsenceNameList[i]+'\n')
#
#        html = doc.toHtml('utf-8')
#        view = CReportViewDialog(self)
#        view.setWindowTitle(u'Табель')
#        view.setText(html)
#        view.exec_()



def divIfPosible(nom, denom):
    if denom != 0:
        return "%.2f"%(float(nom)/denom)
    else:
        return '-'


class CPersonnelModel(CTableModel):
    def __init__(self, parent):
        self.parent = parent
        cols = [CTextCol(u'Код', ['code'], 6),
                CBoolCol(u'Доступ для ВС', ['availableForExternal'], 15),
                CBoolCol(u'Доступ для стенда', ['availableForStand'], 15),
                CDateCol(u'Расписание видимо до', ['lastAccessibleTimelineDate'], 10),
                CTextCol(u'Расписание видимо дней', ['timelineAccessibleDays'], 6),
                CTextCol(u'Фамилия', ['lastName'], 20),
                CNameCol(u'Имя', ['firstName'], 20),
                CNameCol(u'Отчество', ['patrName'], 20),
                CDesignationCol(u'Подразделение', ['orgStructure_id'], ('OrgStructure', 'name'), 5),
                CRefBookCol(u'Должность', ['post_id'], 'rbPost', 10),
                CRefBookCol(u'Специальность', ['speciality_id'], 'rbSpeciality', 10)
                ]
        if QtGui.qApp.defaultKLADR()[:2] == u'23':
            cols.pop(2)  # Доступ для стенда
        CTableModel.__init__(self, parent, cols, 'Person')
        self.parentWidget = parent
        self._mapColumnToOrder = {u'code': u'Person.code',
                                  u'availableForExternal': u'Person.availableForExternal',
                                  u'lastAccessibleTimelineDate': u'Person.lastAccessibleTimelineDate',
                                  u'timelineAccessibleDays': u'Person.timelineAccessibleDays',
                                  u'lastName': u'Person.lastName',
                                  u'firstName': u'Person.firstName',
                                  u'patrName': u'Person.patrName',
                                  u'orgStructure_id': u'OrgStructure.name',
                                  u'post_id': u'rbPost.name',
                                  u'speciality_id': u'rbSpeciality.name'
                                  }


    def getOrder(self, fieldName, column):
        if hasattr(self._cols[column], 'extraFields'):
            if len(self._cols[column].extraFields) > 0:
                fieldName = self._cols[column].extraFields[0]
        return self._mapColumnToOrder[fieldName]


    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        row = index.row()
        personId = self.getIdByRow(row)
        isAttach = self.parent.isPersonAttach(personId)
        if role == Qt.ToolTipRole:
            if isAttach:
                self.parent.tblPersonnel.setToolTip(u'')
            else:
                self.parent.tblPersonnel.setToolTip(u'Отсутствует прикрепление к участку в кадровых перемещениях')
        if role == Qt.BackgroundRole:
            if not isAttach:
                return QtGui.QColor(Qt.yellow)
        return CTableModel.data(self, index, role)


    def getIdByRow(self, row):
        if 0 <= row < self.parent.modelPersonnel.rowCount():
            return self.parent.modelPersonnel.idList()[row]
        return None


class CActivityAllTreeItem(CActivityTreeItem):
    def __init__(self):
        CActivityTreeItem.__init__(self, None, u'Любой', None)

    def loadChildren(self):
        items = []
        db = QtGui.qApp.db
        tableRBActivity = db.table('rbActivity')
        query = db.query(db.selectStmt(tableRBActivity, [tableRBActivity['id'], tableRBActivity['name'] ]))
        while query.next():
            record = query.record()
            id   = forceInt(record.value('id'))
            name = forceString(record.value('name'))
            items.append(CActivityTreeItem(self, name, id))
        return items



class CActivityNoneTreeItem(CActivityTreeItem):
    def __init__(self):
        CActivityTreeItem.__init__(self, None, u'Не определен', None)


    def loadChildren(self):
        return []



class CActivityRootTreeItem(CActivityTreeItem):
    def __init__(self):
        CActivityTreeItem.__init__(self, None, u'-', None)

    def loadChildren(self):
        items = []
        items.append(CActivityNoneTreeItem())
        items.append(CActivityAllTreeItem())
        return items



class CCalcDialog(CDialogBase, Ui_CalcDialog):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)


    def getFinanceIdList(self):
        from Events.Utils import CFinanceType
        result = []
        for checkBox, financeCode in ( (self.chkBudget,   CFinanceType.budget ),
                                       (self.chkCMI,      CFinanceType.CMI ),
                                       (self.chkVMI,      CFinanceType.VMI ),
                                       (self.chkCach,     CFinanceType.cash ),
                                       (self.chkTargeted, CFinanceType.targeted ),
                                     ):
            if checkBox.isChecked():
                result.append(CFinanceType.getId(financeCode))
        return result


    def getAppointmentTypeList(self):
        result = []
        if self.chkAmbulance.isChecked():
            result.append(CSchedule.atAmbulance)
        if self.chkHome.isChecked():
            result.append(CSchedule.atHome)
        if self.chkExp.isChecked():
            result.append(CSchedule.atExp)
        return result


    def getFillAll(self):
        return self.rbFillAll.isChecked()



class CAbsenceDialog(CDialogBase, Ui_AbsenceDialog):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.cmbReasonOfAbsence.setTable('rbReasonOfAbsence')
        QObject.connect(self.buttonBox, SIGNAL("accepted()"), self.apply)
        if not (QtGui.qApp.userHasRight(urAdmin) or QtGui.qApp.userHasRight(urCanChangePersonSubstitution)):
            self.lblSubstitutePerson.setEnabled(False)
            self.cmbSubstitutePerson.setEnabled(False)


    def setDateRange(self, begDate, endDate):
        self.edtBegDate.setDateRange(begDate, endDate)
        self.edtEndDate.setDateRange(begDate, endDate)
        self.edtBegDate.setDate(begDate)
        self.edtEndDate.setDate(endDate)


    def getDateRange(self):
        return self.edtBegDate.date(), self.edtEndDate.date()


    def getFillRedDays(self):
        return self.chkFillRedDays.isChecked()


    def getReasonOfAbsenceId(self):
        return self.cmbReasonOfAbsence.value()
    
    
    def saveSubstitute(self, absencesPerson_id):
        if self.cmbSubstitutePerson.value() and (QtGui.qApp.userHasRight(urAdmin) or QtGui.qApp.userHasRight(urCanChangePersonSubstitution)):
            db = QtGui.qApp.db
            table = db.table(u'soc_PersonSubstitution')
            self.record = table.newRecord()
            self.record.setValue('createDatetime', QDate.currentDate())
            self.record.setValue('createPerson_id',  QtGui.qApp.userId)
            self.record.setValue('modifyDatetime', QDate.currentDate())
            self.record.setValue('modifyPerson_id', QtGui.qApp.userId)
            self.record.setValue('absencesPerson_id', forceString(absencesPerson_id))
            self.record.setValue('begDate', forceDate(self.edtBegDate.date()))
            self.record.setValue('endDate', forceDate(self.edtEndDate.date()))
            self.record.setValue('substitutionPerson_Id', forceString(self.cmbSubstitutePerson.value()))
            db.insertOrUpdate(table, self.record)

    
    def checkDates(self):
        if self.edtBegDate.date() > self.edtEndDate.date():
            QtGui.QMessageBox.warning(self, u'Ошибка при сохранении',
                        u'Дата начала периода замещения не может быть больше даты окончания периода')
            return False
        db = QtGui.qApp.db
        table = db.table(u'soc_PersonSubstitution')
        cond = """absencesPerson_id = {2} AND
            deleted = 0 AND
            (({0} <= begDate and {1} <= begDate) 
            or ({0} >= endDate and {1} >= endDate))""".format(db.formatDate(self.edtBegDate.date()), 
                                                               db.formatDate(self.edtBegDate.date()), 
                                                               self.tblPersonnel.currentItemId())
        record = db.getRecordEx(table, cols="*", where=cond)
        if record:
            QtGui.QMessageBox.warning(self, u'Ошибка при сохранении',
                        u'Новый период замещения пересекается с существующим периодом с {} по {}'.format(forceString(record.value('begDate')), forceString(record.value('endDate'))))
            return False
        return True
    
    def apply(self):
        if self.checkDates() and self.cmbSubstitutePerson.value():
            self.accept()



class CParamsForExternalDialog(CDialogBase, Ui_ParamsForExternalDialog):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.edtLastAccessibleTimelineDate.setDate(QDate())


    @pyqtSignature('int')
    def on_edtTimelineAccessibilityDays_valueChanged(self, value):
        self.lblTimelineAccessibilityDaysSuffix.setText(agreeNumberAndWord(value, (u'день', u'дня', u'дней')))

