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
##
## Редактирование расписания работ
##
#############################################################################


from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QDate, pyqtSignature, QDateTime, SIGNAL

from Orgs.Utils import getOrgStructureFullName
from Reports.ReportBase import createTable
from library.DialogBase              import CDialogBase
from library.Utils                   import forceRef, forceString
from Reports.ReportBase              import CReportBase
from Reports.ReportView              import CReportViewDialog

from Orgs.OrgStructComboBoxes        import COrgStructureModel
from Resources.JobFlexTemplateDialog import CJobFlexTemplateDialog
from Resources.Jobs                  import CJobsModel
from Resources.JobTemplateDialog     import CJobTemplateDialog
from Resources.JobTicketsDialog      import CJobTicketsDialog

from Resources.Ui_JobPlannerDialog   import Ui_JobPlannerDialog
from library.Utils import forceInt


class CJobPlanner(CDialogBase, Ui_JobPlannerDialog):
    def __init__(self, parent, orgStructureId=None):
        CDialogBase.__init__(self, parent)
        self.addModels('OrgStructure', COrgStructureModel(self, QtGui.qApp.currentOrgId()))
        self.addModels('Jobs',         CJobsModel(self))


        # действия контекстного меню расписания
        self.addObject('actFillByTemplate',     QtGui.QAction(u'Заполнить по шаблону для текущего подразделения', self))
        self.addObject('actFillByFlexTemplate', QtGui.QAction(u'Заполнить по шаблону "скользящий график"', self))
        self.addObject('actEditJobTickets',     QtGui.QAction(u'Номерки', self))
        self.addObject('actJobInfo',            QtGui.QAction(u'Свойства записи', self))
#        self.addObject('actScheduleItemsHistory',QtGui.QAction(u'История', self))
        self.actFillByTemplate.setShortcut('F9')
        self.actFillByFlexTemplate.setShortcut('Alt+F9')

        # меню кнопки "заполнить"
        self.addObject('mnuFill', QtGui.QMenu(self))
        self.mnuFill.addAction(self.actFillByTemplate)
        self.mnuFill.addAction(self.actFillByFlexTemplate)

        self.setupUi(self)
#        self.btnPrint.setMenu(self.mnuPrint)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setModels(self.treeOrgStructure, self.modelOrgStructure, self.selectionModelOrgStructure)
        self.setModels(self.tblJobs, self.modelJobs, self.selectionModelJobs)

        self.btnFill.setMenu(self.mnuFill)
        self.tblJobs.addPopupActions([
                                       '-',
                                       self.actFillByTemplate,
                                       self.actFillByFlexTemplate,
                                       '-',
                                       self.actEditJobTickets,
                                       self.actJobInfo,
#                                       self.actScheduleItemsHistory,
                                     ])
        orgStructureId = orgStructureId or QtGui.qApp.currentOrgStructureId()
        orgStructureIndex = self.modelOrgStructure.findItemId(orgStructureId)
        if orgStructureIndex and orgStructureIndex.isValid():
            self.treeOrgStructure.setCurrentIndex(orgStructureIndex)
            self.treeOrgStructure.setExpanded(orgStructureIndex, True)

        date = QDate.currentDate()
        self.calendar.setSelectedDate(date)

    @pyqtSignature('')
    def on_btnPrint_clicked(self):
        rowSize = 10
        report = CReportBase()
        params = report.getDefaultParams()
        report.saveDefaultParams(params)
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Планирование работ')
        cursor.insertBlock()
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        orgStructName = getOrgStructureFullName(self.getCurrentOrgStructureId())
        date = self.calendar.selectedDate()
        lastDay = date.daysInMonth()
        dateMonthYear = date.toString("MM.yyyy")
        cursor.insertText(u'За период: с 01.{0} по {1}.{2}'.format(dateMonthYear, lastDay, dateMonthYear))
        cursor.insertBlock()
        cursor.insertText(u'Подразделение: {0}'.format(orgStructName))
        cursor.insertBlock()
        currentDate = QDateTime.currentDateTime()
        cursor.insertText(u'отчёт составлен: {0}'.format(currentDate.toString("dd.MM.yyyy")))
        cursor.insertHtml('<br/><br/>')
        table = createTable(cursor, [
            ('3%', [u''], CReportBase.AlignCenter),
            ('17%', [u'Тип'], CReportBase.AlignLeft),
            ('10%', [u'Назначение'], CReportBase.AlignLeft),
            ('10%', [u'Начало'], CReportBase.AlignRight),
            ('10%', [u'Окончание'], CReportBase.AlignRight),
            ('10%', [u'План'], CReportBase.AlignCenter),
            ('10%', [u'Сверх плана'], CReportBase.AlignCenter),
            ('10%', [u'Назначено'], CReportBase.AlignCenter),
            ('10%', [u'Выполняется'], CReportBase.AlignCenter),
            ('10%', [u'Выполнено'], CReportBase.AlignCenter),
        ]
                            )
        items = self.tblJobs.model().items()
        dateLast = None
        for item in items:
            itemForColsList = [u'', u'', u'', u'', u'', u'', u'', u'', u'', u'']
            date = forceString(item.date.toString('dd.MM'))
            if date != dateLast:
                itemForColsList[0] = date
                dateLast = date
            else:
                itemForColsList[0] = u' '
            jobTypeName = self.getJobTypeName(item.jobTypeId)
            if jobTypeName:
                itemForColsList[1] = forceString(jobTypeName.value('name'))
            else:
                itemForColsList[1] = u' '
            jobPurposeName = self.getJobPurposeName(item.jobPurposeId)
            if jobPurposeName:
                itemForColsList[2] = forceString(item.jobPurposeId) + u' | ' + forceString(jobPurposeName.value('name'))
            else:
                itemForColsList[2] = u'0 | Не задано'
            itemForColsList[3] = forceString(item.begTime)
            itemForColsList[4] = forceString(item.endTime)
            itemForColsList[5] = item.quantity

            itemForColsList[6] = item.cntOutOfOrder
            itemForColsList[7] = item.cntReserved
            itemForColsList[8] = item.cntBusy
            itemForColsList[9] = item.cntExecuted
            row = table.addRow()
            for col in xrange(rowSize):
                table.setText(row, col, itemForColsList[col])

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertHtml('<br/><br/>')

        reportView = CReportViewDialog(self)
        reportView.setWindowTitle(u'Планирование работ')
        reportView.setOrientation(QtGui.QPrinter.Portrait)
        reportView.setText(doc)
        reportView.exec_()

    def getJobTypeName(self, id):
        db = QtGui.qApp.db
        id = forceInt(id)
        name = db.getRecordEx('rbJobType', 'name', 'id = {0}'.format(id))
        return name

    def getJobPurposeName(self, id):
        db = QtGui.qApp.db
        id = forceInt(id)
        name = db.getRecordEx('rbJobPurpose', 'name', 'id = {0}'.format(id))
        return name

    def exec_(self):
        result = CDialogBase.exec_(self)
        return result

    def saveData(self):
        if not self.modelJobs.checkBegEndDate():
            return False
        QtGui.qApp.callWithWaitCursor(self, self.modelJobs.saveData)
        return True

    @pyqtSignature('')
    def on_btnApply_clicked(self):
        if self.saveData():
            buttons = QtGui.QMessageBox.Ok
            messageBox = QtGui.QMessageBox()
            messageBox.setWindowFlags(messageBox.windowFlags() | Qt.WindowStaysOnTopHint)
            messageBox.setWindowTitle(u'Внимание!')
            messageBox.setText(u'Данные сохранены')
            messageBox.setStandardButtons(buttons)
            messageBox.setDefaultButton(QtGui.QMessageBox.Ok)
            messageBox.exec_()


    def getBegDate(self):
        return QDate(self.calendar.yearShown(), self.calendar.monthShown(), 1)


    def getEndDate(self):
        return QDate(self.calendar.yearShown(), self.calendar.monthShown(), 1).addMonths(1).addDays(-1)


    def getCurrentOrgStructureId(self):
       treeIndex = self.treeOrgStructure.currentIndex()
       treeItem = treeIndex.internalPointer() if treeIndex.isValid() else None
       return treeItem.id() if treeItem else None


    def updateJobs(self, scrollToDate):
        prevOrgStructureId = self.modelJobs.orgStructureId
        prevYear       = self.modelJobs.year
        prevMonth      = self.modelJobs.month
        orgStructureId = self.getCurrentOrgStructureId()
        date           = self.calendar.selectedDate()

        QtGui.qApp.callWithWaitCursor(self, self.modelJobs.setOrgStructureAndMonth, orgStructureId, date.year(), date.month())
        row = self.modelJobs.getRowForDate(date)
        currentIndex = self.tblJobs.currentIndex()
        currentColumn = currentIndex.column() if currentIndex.isValid() else 0
        newIndex = self.modelJobs.index(row, currentColumn)
        self.tblJobs.setCurrentIndex(newIndex)
        if scrollToDate:
            self.tblJobs.scrollTo(newIndex, QtGui.QAbstractItemView.EnsureVisible)
        self.tblJobs.setEnabled( bool(orgStructureId) )
#        self.btnFill.setEnabled( bool(orgStructureId) )
        if prevOrgStructureId != self.modelJobs.orgStructureId or prevYear != self.modelJobs.year or prevMonth != self.modelJobs.month:
               pass
#            self.updateStatisctics()


    def fillByTemplate(self):
        currentOrgStructureId = self.getCurrentOrgStructureId()
        begDate = self.getBegDate()
        endDate = self.getEndDate()
        dialog = CJobTemplateDialog(self)
        try:
            dialog.setOrgStructureId(currentOrgStructureId)
            dialog.setDateRange(begDate, endDate)
            if dialog.exec_():
                QtGui.qApp.callWithWaitCursor(self,
                                              self.modelJobs.setWorkPlan,
                                              dialog.getDateRange(),
                                              dialog.getPeriod(),
                                              dialog.getCustomLength(),
                                              dialog.getFillRedDays(),
                                              dialog.getTemplates(),
                                              dialog.removeExistingJobs()
                                             )
        finally:
            dialog.deleteLater()


    def fillByFlexTemplate(self):
#        currentOrgStructureId = self.getCurrentOrgStructureId()
        begDate = self.getBegDate()
        endDate = self.getEndDate()
        dialog = CJobFlexTemplateDialog(self)
        try:
            dialog.setDateRange(begDate, endDate)
            dialog.setSelectedDate(self.calendar.selectedDate())
            if dialog.exec_():
                QtGui.qApp.callWithWaitCursor(self,
                                              self.modelJobs.setFlexWorkPlan,
                                              dialog.getSelectedDates(),
                                              dialog.getTemplates(),
                                              dialog.removeExistingJobs()
                                             )
        finally:
            dialog.deleteLater()



    # обработчики сигналов
    # календарь
    @pyqtSignature('int, int')
    def on_calendar_currentPageChanged(self, year, month):
        selectedDate = self.calendar.selectedDate()
        currYear = selectedDate.year()
        currMonth = selectedDate.month()
        newDate = selectedDate.addMonths((year-currYear)*12+(month-currMonth))
        self.calendar.setSelectedDate(newDate)


    @pyqtSignature('')
    def on_calendar_selectionChanged(self):
        self.updateJobs(True)


    # список подразделений
    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelOrgStructure_currentChanged(self, current, previous):
        self.updateJobs(False)


    @pyqtSignature('')
    def on_tblJobs_popupMenuAboutToShow(self):
        currentIndex = self.tblJobs.currentIndex()
        row = currentIndex.row()
        if 0<=row<self.modelJobs.rowCount():
           job = self.modelJobs.getItem(row)
#           isFreeToChange = job.isFreeToChange()
           isEmpty = job.isEmpty()
        else:
#           isFreeToChange = True
           isEmpty = True
        self.actEditJobTickets.setEnabled(not isEmpty)
        self.actJobInfo.setEnabled(not isEmpty)
#        self.actScheduleItemsHistory.setEnabled(True)


    @pyqtSignature('')
    def on_actFillByTemplate_triggered(self):
        self.fillByTemplate()


    @pyqtSignature('')
    def on_actFillByFlexTemplate_triggered(self):
        self.fillByFlexTemplate()


    @pyqtSignature('')
    def on_actJobInfo_triggered(self):
        jobId = self.tblJobs.currentItem().id
        if jobId:
            showJobInfo(jobId, self)


    @pyqtSignature('')
    def on_actEditJobTickets_triggered(self):
        currentIndex = self.tblJobs.currentIndex()
        row = currentIndex.row()
        if 0<=row<self.modelJobs.rowCount():
           job = self.modelJobs.getItem(row)
           job.reloadItems()
           isFreeToChange = job.isFreeToChange()
           isEmpty = job.isEmpty()

           if isFreeToChange and not isEmpty:
                job.calcTimePlanIfRequired()
                dialog = CJobTicketsDialog(self)
                try:
                    dialog.setJob(job)
                    if dialog.exec_():
                        pass
                finally:
                    dialog.deleteLater()



def showJobInfo(jobId, widget):
    db = QtGui.qApp.db
    jobRecord = db.getRecord('Job', '*', jobId)

    createDatetime = forceString(jobRecord.value('createDatetime'))
    createPersonId = forceRef(jobRecord.value('createPerson_id'))
    modifyDatetime = forceString(jobRecord.value('modifyDatetime'))
    modifyPersonId = forceRef(jobRecord.value('modifyPerson_id'))

    createPerson = forceString(db.translate('vrbPersonWithSpeciality', 'id', createPersonId, 'name'))
    modifyPerson = forceString(db.translate('vrbPersonWithSpeciality', 'id', modifyPersonId, 'name'))

    doc = QtGui.QTextDocument()
    cursor = QtGui.QTextCursor(doc)

    cursor.setCharFormat(CReportBase.ReportTitle)
    cursor.insertText(u'Свойства записи')
    cursor.insertBlock()
    cursor.setCharFormat(CReportBase.ReportBody)

    cursor.insertBlock()
    cursor.insertText(u'Создатель записи: %s\n' % createPerson)
    cursor.insertText(u'Дата создания записи: %s\n' % createDatetime)
    cursor.insertText(u'Редактор записи: %s\n' % modifyPerson)
    cursor.insertText(u'Дата редактирования записи: %s\n\n' % modifyDatetime)

    cursor.insertBlock()
    reportView = CReportViewDialog(widget)
    reportView.setWindowTitle(u'Свойства записи')
    reportView.setText(doc)
    reportView.exec_()


#
#
#    def getJobPlanNumbersDialog(self):
#        currentIndex = self.tblJobs.currentIndex()
#        row = currentIndex.row()
#        date = QDate(self.calendar.selectedDate())
#        orgStructureJobRecord = self.tblJobs.currentItem()
#        if orgStructureJobRecord:
#            orgStructureId = forceRef(orgStructureJobRecord.value('master_id'))
#            jobTypeId = forceRef(orgStructureJobRecord.value('jobType_id'))
#        else:
#            orgStructureId = None
#            jobTypeId = None
#        if orgStructureId and jobTypeId and date:
#            dialog = CJobPlanNumbersDialog(self, orgStructureId, jobTypeId, date, self.modelJobs.items[row])
#            try:
#                if dialog.exec_():
#                    pass
#            finally:
#                dialog.deleteLater()
#
#
#    def recountJobPlanNumbers(self):
#        currentIndex = self.tblJobs.currentIndex()
#        row = currentIndex.row()
#        planTime = self.modelJobs.items[row].timeRange
#        planCount = self.modelJobs.items[row].quantity
#        self.modelJobs.items[row].forceChange = planTime and planCount > 0
#
#
#
#
#    @pyqtSignature('')
#    def on_actPlanNumbers_triggered(self):
#        self.getJobPlanNumbersDialog()
#
#
#    @pyqtSignature('')
#    def on_actRecountNumbers_triggered(self):
#        self.recountJobPlanNumbers()
#
