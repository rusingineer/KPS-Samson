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
from PyQt4.QtCore import Qt, QDate, QDateTime, pyqtSignature, SIGNAL, QVariant

from library.RecordLock import CRecordLockMixin
from library.database             import CTableRecordCache
from library.DialogBase           import CDialogBase
from library.PrintInfo            import CInfoContext, CDateInfo
from library.PrintTemplates       import applyTemplate, getPrintAction
from library.TableModel           import CTableModel, CCol, CDateTimeCol, CEnumCol, CIntCol, CRefBookCol, CTextCol
from library.Utils                import agreeNumberAndWord, forceDate, forceDateTime, forceDouble, forceInt, forceRef, forceString, formatList, formatName, formatRecordsCount, formatSex, toVariant, trim, forceBool
from Events.Action                import CAction, CActionTypeCache
from Events.ActionStatus          import CActionStatus
from Events.AmbCardDialog         import CAmbCardDialog
from Events.EventInfo             import CEventInfo
from Events.ActionInfo            import CActionInfo
from Events.EventJobTicketsEditor import CEventJobTicketsListEditor
from Events.Utils                 import getActionTypeIdListByFlatCode
from Orgs.OrgStructComboBoxes     import COrgStructureModel
from Orgs.Utils                   import getOrgStructureFullName, getPersonInfo, COrgStructureInfo
from Registry.ClientEditDialog    import CClientEditDialog
from Registry.Utils               import getClientHospitalOrgStructureAndBedRecords
from Reports.ReportBase           import CReportBase, createTable
from Reports.ReportView           import CReportViewDialog
from Reports.Utils                import updateLIKE
from Resources.JobTicketActionsModel  import CJobTicketActionsModel
from Resources.JobTicketEditor        import CJobTicketEditor
from Resources.JobTicketInfo          import makeDependentActionIdList, CJobTicketsWithActionsInfoList, CJobTypeInfo
from Resources.JobTicketStatus        import CJobTicketStatus
from Resources.JobTypeActionsSelector import CFakeEventEditor
from Resources.CloseWorkForGroupDialog import CCloseWorkForGroupDialog
from Users.Rights import urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry, urUseGroupJobTicketsChanging, \
    urReadJobTicketMedKart
from Resources.Models.JobTicket import CJobTicket
from Orgs.PersonInfo              import CPersonInfo
from RefBooks.Speciality.Info     import CSpecialityInfo
from GroupJobTicketsManipulationsDialog import CGroupJobTicketsManipulationsDialog, CJobTicketJobTypeChangerDialog

from Ui_JobsOperatingDialog       import Ui_JobsOperatingDialog


def getClientOrgStructureId(clientId):
    [recordOrgStructure, recordBed] = getClientHospitalOrgStructureAndBedRecords(clientId)
    if recordOrgStructure:
        return forceRef(recordOrgStructure.value('orgStructureId'))
    else:
        return None


class CJobsOperatingDialog(CDialogBase, CRecordLockMixin, Ui_JobsOperatingDialog):
    def __init__(self, parent):
        self._jobTicketsListUpdatingAllowed = False

        CDialogBase.__init__(self, parent)
        CRecordLockMixin.__init__(self)
        self.jobTicketOrderColumn = None
        self.jobTypesOrderColumn = 0
        self.jobTicketOrderAscending = True
        self.jobTypesOrderAscending = forceBool(QtGui.qApp.preferences.appPrefs.get('jobTypesOrderAscending', True))

        self.addModels('OrgStructure', COrgStructureModel(self, QtGui.qApp.currentOrgId()))
        #self.addModels('OrgStructureWithBeds', COrgStructureModel(self, QtGui.qApp.currentOrgId(), filter='(SELECT getOrgStructureIsHasHospitalBeds(id))=1'))
        #self.addModels('OrgStructureWithBeds', COrgStructureModel(self, QtGui.qApp.currentOrgId(), purpose=COrgStructureTreePurpose.hospitalBedsSelector))
        self.addModels('JobTypes', CJobTypesModel(self))
        self.addModels('JobTickets', CJobTicketsModel(self))
        self.addModels('JobTicketActions', CJobTicketActionsModel(self, fromOperationDialog=True))

        self.addObject('actEditClient',     QtGui.QAction(u'Открыть регистрационную карточку', self))
        self.addObject('actAmbCardShow',    QtGui.QAction(u'Открыть медицинскую карту', self))
        self.addObject('actEnqueuePromptly', QtGui.QAction(u'Поставить в очередь первым', self)) # F2
        self.addObject('actEditJobTickets',    QtGui.QAction(u'Назначить другой номерок', self)) # F3
        self.addObject('actEditCurrentJobTicket', QtGui.QAction(u'Редактор', self)) # F4
        self.addObject('actEnqueue',   QtGui.QAction(u'Поставить в очередь', self)) # F5
        self.addObject('actSetWaiting',   QtGui.QAction(u'Убрать из очереди', self)) # F7
        self.addObject('actEditPassJobTicket', QtGui.QAction(u'Пропустить', self)) # F8
        self.addObject('actSetDoing', QtGui.QAction(u'Начать обслуживание', self)) # F10
        self.addObject('actJobTicketInfo', QtGui.QAction(u'Свойства записи', self))
        self.addObject('actGroupJobTicketsChanging', QtGui.QAction(u'Групповое изменение номерка', self))
        self.addObject('actJobTicketJobTypeChanging', QtGui.QAction(u'Изменение типа работы', self))
        self.addObject('actSchooseGroupJobTicket', QtGui.QAction(u'Выделить группу', self))
        self.addObject('actCloseWorkForGroup', QtGui.QAction(u'Закрыть работу для группы', self))

        self.addObject('actMainPrint',   QtGui.QAction(u'Основная печать списка (полная)', self))
        self.addObject('actMainPrint_v2',   QtGui.QAction(u'Основная печать списка', self))
        self.addObject('actJobTicketListPrint', getPrintAction(self, 'jobTicket_list', u'Печать списка', False))
        self.addObject('actActionPrint', getPrintAction(self, None, u'Печать мероприятия'))
        self.addObject('btnPrint', QtGui.QPushButton(u'Печать', self))
        self.addObject('mnuBtnPrint', QtGui.QMenu(self))
        self.addObject('actPrintClientNumberTicket', QtGui.QAction(u'Напечатать этикетку', self))
        printer = QtGui.qApp.labelPrinter()
        if bool(printer) and QtGui.qApp.db.getRecordEx(u'rbPrintTemplate', u'id', u"deleted = 0 and  context like 'barcodeProbe' "  ):
            self.mnuBtnPrint.addAction(self.actPrintClientNumberTicket)
            self.mnuBtnPrint.addSeparator()

        self.mnuBtnPrint.addAction(self.actMainPrint)
        self.mnuBtnPrint.addAction(self.actMainPrint_v2)
        self.mnuBtnPrint.addSeparator()
        self.mnuBtnPrint.addAction(self.actJobTicketListPrint)
        self.mnuBtnPrint.addSeparator()
        self.mnuBtnPrint.addAction(self.actActionPrint)
        self.btnPrint.setMenu(self.mnuBtnPrint)

        # сканирование штрих кода
        self.addBarcodeScanAction('actScanBarcode')
        self.addBarcodeScanAction('actScanBarcodeTissueType')
        self.addBarcodeScanAction('actScanBarcodeProbe')

        self.actEnqueuePromptly.setShortcut('F2')
        self.actEditJobTickets.setShortcut('F3')
        self.actEditCurrentJobTicket.setShortcut('F4')
        self.actEnqueue.setShortcut('F5')
        self.actEditPassJobTicket.setShortcut('F8')
        self.actSetWaiting.setShortcut('F7')
        self.actSetDoing.setShortcut('F10')

        self.setupUi(self)

        self.tblJobTickets.setSelectionMode(self.tblJobTickets.ExtendedSelection)
        self.tblJobTypes.setSelectionMode(self.tblJobTypes.ExtendedSelection)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint | Qt.WindowSystemMenuHint | Qt.Window)
        self.setModels(self.treeOrgStructure, self.modelOrgStructure, self.selectionModelOrgStructure)
        self.setModels(self.tblJobTypes, self.modelJobTypes, self.selectionModelJobTypes)
        self.setModels(self.tblJobTickets, self.modelJobTickets, self.selectionModelJobTickets)
        self.setModels(self.tblJobTicketActions, self.modelJobTicketActions, self.selectionModelJobTicketActions)

#        self.tblJobPlan.createPopupMenu([self.actFillByTemplate])
        self.cmbClientAccountingSystem.setTable('rbAccountingSystem', addNone=True)
        self.cmbSpeciality.setTable('rbSpeciality', True)
        self.cmbTissueType.setTable('rbTissueType', addNone=True, specialValues=[(-1, '-', u'любой биоматериал'), (-2, '-', u'без биоматериала')])
        self.cmbTakenTissueType.setTable('rbTissueType', addNone=True, specialValues=[(-1, '-', u'любой биоматериал'), (-2, '-', u'без биоматериала')])
        self.cmbJobPurpose.setTable('rbJobPurpose', addNone=True, specialValues=[(-1, '-', u'любое назначение'), (-2, '-', u'без назначения')])
        self.filter = {}
        self.resetFilter()
        orgStructureIndex = self.modelOrgStructure.findItemId(QtGui.qApp.currentOrgStructureId())
        if orgStructureIndex and orgStructureIndex.isValid():
            self.treeOrgStructure.setCurrentIndex(orgStructureIndex)
            self.treeOrgStructure.setExpanded(orgStructureIndex, True)

        self.connect(self.tblJobTypes.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.setSortJobTypesByColumn)
        self.setSortJobTypesByColumn(forceInt(QtGui.qApp.preferences.appPrefs.get('jobTypesOrderColumn', 0)))

        self.calendar.setSelectedDate(QDate.currentDate())
        self.connect(self.tblJobTickets.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.setSortJobTicketsByColumn)
        self.buttonBox.addButton(self.btnPrint, QtGui.QDialogButtonBox.ActionRole)

        self.tblJobTickets.addPopupAction(self.actEditClient)
        self.tblJobTickets.addPopupAction(self.actAmbCardShow)
        self.tblJobTickets.addPopupAction(self.actEnqueue)
        self.tblJobTickets.addPopupAction(self.actEnqueuePromptly)
        self.tblJobTickets.addPopupAction(self.actSetWaiting)
        self.tblJobTickets.addPopupAction(self.actEditPassJobTicket)
        self.tblJobTickets.addPopupAction(self.actSetDoing)
        self.tblJobTickets.addPopupAction(self.actEditJobTickets)
        self.tblJobTickets.addPopupAction(self.actEditCurrentJobTicket)
        self.tblJobTickets.addPopupAction(self.actJobTicketInfo)
        self.tblJobTickets.addPopupAction(self.actGroupJobTicketsChanging)
        self.tblJobTickets.addPopupAction(self.actJobTicketJobTypeChanging)
        self.tblJobTickets.addPopupAction(self.actSchooseGroupJobTicket)
        self.tblJobTickets.addPopupAction(self.actCloseWorkForGroup)

        self.tblJobTickets.enableColsHide()
        self.tblJobTickets.enableColsMove()

        self.tblJobTicketActions.addAction(self.actEnqueue)
        self.tblJobTicketActions.addAction(self.actEnqueuePromptly)
        self.tblJobTicketActions.addAction(self.actSetWaiting)
        self.tblJobTicketActions.addAction(self.actEditPassJobTicket)
        self.tblJobTicketActions.addAction(self.actSetDoing)
        self.tblJobTicketActions.addAction(self.actEditJobTickets)
        self.tblJobTicketActions.addAction(self.actEditCurrentJobTicket)

        appPrefs = QtGui.qApp.preferences.appPrefs
        onScanSelect = forceInt(appPrefs.get('onScanSelect',  QVariant(0)))
        self.cmbOnScanSelect.setCurrentIndex(onScanSelect) if self.cmbOnScanSelect.currentIndex() != onScanSelect else self.on_cmbOnScanSelect_currentIndexChanged(onScanSelect)
        self.cmbOnScan.setCurrentIndex(forceInt(appPrefs.get('actionOnScan',  QVariant(0))))
        jobOperationDialogFilterAwaiting = forceBool(appPrefs.get('jobOperationDialogFilterAwaiting',  True))
        self.chkAwaiting.setChecked(jobOperationDialogFilterAwaiting)
        jobOperationDialogFilterEnueued = forceBool(appPrefs.get('jobOperationDialogFilterEnueued',  False))
        self.chkEnueued.setChecked(jobOperationDialogFilterEnueued)
        jobOperationDialogFilterInProgress = forceBool(appPrefs.get('jobOperationDialogFilterInProgress',  False))
        self.chkInProgress.setChecked(jobOperationDialogFilterInProgress)
        jobOperationDialogFilterDone = forceBool(appPrefs.get('jobOperationDialogFilterDone',  False))
        self.chkDone.setChecked(jobOperationDialogFilterDone)
        jobOperationDialogFilterOnlyUrgent = forceBool(appPrefs.get('jobOperationDialogFilterOnlyUrgent',  False))
        self.chkOnlyUrgent.setChecked(jobOperationDialogFilterOnlyUrgent)
        jobOperationDialogFilterHideDoneActions = forceBool(appPrefs.get('jobOperationDialogFilterHideDoneActions',  True))
        self.chkHideDoneActions.setChecked(jobOperationDialogFilterHideDoneActions)
        jobOperationDialogFilterExpired = forceBool(appPrefs.get('jobOperationDialogFilterExpired',  False))
        self.chkExpired.setChecked(jobOperationDialogFilterExpired)
        self.cmbOrgStructureType.setCurrentIndex(forceInt(appPrefs.get('jobsOperatingDialogOrgStructureType',  1)))
        self.edtClientBirthDate.setDisplayFormat('dd.MM.yyyy')
        self.edtClientBirthDate.setDate(None)

        self.showNormal()
        self._jobTicketsListUpdatingAllowed = True
        self.updateJobTicketList()
        #self.showMaximized()


    def exec_(self):
        CDialogBase.exec_(self)
        QtGui.qApp.preferences.appPrefs['actionOnScan'] = self.cmbOnScan.currentIndex()
        QtGui.qApp.preferences.appPrefs['onScanSelect'] = self.cmbOnScanSelect.currentIndex()
        QtGui.qApp.preferences.appPrefs['jobOperationDialogFilterAwaiting'] = self.chkAwaiting.isChecked()
        QtGui.qApp.preferences.appPrefs['jobOperationDialogFilterEnueued'] = self.chkEnueued.isChecked()
        QtGui.qApp.preferences.appPrefs['jobOperationDialogFilterInProgress'] = self.chkInProgress.isChecked()
        QtGui.qApp.preferences.appPrefs['jobOperationDialogFilterDone'] = self.chkDone.isChecked()
        QtGui.qApp.preferences.appPrefs['jobOperationDialogFilterOnlyUrgent'] = self.chkOnlyUrgent.isChecked()
        QtGui.qApp.preferences.appPrefs['jobOperationDialogFilterHideDoneActions'] = self.chkHideDoneActions.isChecked()
        QtGui.qApp.preferences.appPrefs['jobOperationDialogFilterExpired'] = self.chkExpired.isChecked()
        QtGui.qApp.preferences.appPrefs['jobsOperatingDialogOrgStructureType'] = self.cmbOrgStructureType.currentIndex()


    def getPromptlyDateTime(self):
        filter = self.getFilter()
        queryTable, cond, order = self.prepareQueryParts(filter)
        db = QtGui.qApp.db
        tableJobTicket = db.table('Job_Ticket')
        cond.append(tableJobTicket['status'].eq(CJobTicketStatus.enqueued))
        record = db.getRecordEx(queryTable, 'Job_Ticket.begDateTime', cond, 'Job_Ticket.begDateTime')
        result = QDateTime.currentDateTime()
        if record:
            begDateTime = forceDateTime(record.value('begDateTime'))
            if begDateTime:
                result = begDateTime.addSecs(1)
        return result


    @pyqtSignature('')
    def on_tblJobTickets_popupMenuAboutToShow(self):
        currentIndex = self.tblJobTickets.currentIndex()
        curentIndexIsValid = currentIndex.isValid()
        status = self.modelJobTickets.getStatus(currentIndex.row())
        self.actEditClient.setEnabled(curentIndexIsValid and
                                      QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]))
        self.actAmbCardShow.setEnabled(curentIndexIsValid and QtGui.qApp.userHasRight(urReadJobTicketMedKart))
        self.actEditPassJobTicket.setEnabled((self.modelJobTickets.getPass(currentIndex.row()) < 9) if curentIndexIsValid else False)
        self.actEditCurrentJobTicket.setEnabled(curentIndexIsValid)
        rowActual = 0 <= currentIndex.row() < len(self.modelJobTickets.idList())
        self.actEnqueuePromptly.setEnabled(status in (CJobTicketStatus.wait, CJobTicketStatus.enqueued) and rowActual)
        self.actEnqueue.setEnabled(status in (CJobTicketStatus.wait, CJobTicketStatus.enqueued) and rowActual)
        self.actSetWaiting.setEnabled(status == CJobTicketStatus.enqueued and rowActual)
        self.actEditJobTickets.setEnabled(status in (CJobTicketStatus.wait, CJobTicketStatus.enqueued) and rowActual)
        self.actSetDoing.setEnabled(status != CJobTicketStatus.done and rowActual)
        self.actJobTicketInfo.setEnabled(rowActual)
        self.actGroupJobTicketsChanging.setEnabled(self._isActGroupJobTicketsChangingEnabled() and QtGui.qApp.userHasRight(urUseGroupJobTicketsChanging))
        self.actJobTicketJobTypeChanging.setEnabled(curentIndexIsValid and rowActual)
        isGroupEnable = curentIndexIsValid and rowActual and self._getJobCapacityFromJobTicket(self.modelJobTickets.getIdByRow(currentIndex.row())) > 1
        self.actSchooseGroupJobTicket.setEnabled(isGroupEnable)
        self.actCloseWorkForGroup.setEnabled(isGroupEnable and len(self.tblJobTickets.selectedRowList()) > 1)


    def _getJobCapacityFromJobTicket(self, jobTicketId):
        if not jobTicketId:
            return 0
        masterId = self.modelJobTickets.recordCache().get(jobTicketId).value('master_id')
        return forceInt(QtGui.qApp.db.translate('Job', 'id', masterId, 'capacity'))


    def _getJobTypeFromJobTicket(self, jobTicketId):
        masterId = self.modelJobTickets.recordCache().get(jobTicketId).value('master_id')
        return forceRef(QtGui.qApp.db.translate('Job', 'id', masterId, 'jobType_id'))


    def _isActGroupJobTicketsChangingEnabled(self):
        selectedItemIdList = self.tblJobTickets.selectedItemIdList()
        if len(selectedItemIdList) < 2:
            return False
        jobTypeId = self._getJobTypeFromJobTicket(selectedItemIdList[0])
        return all(self.modelJobTickets.recordCache().get(itemId).value('status') == 0 # Ожидание
                   and self._getJobTypeFromJobTicket(itemId) == jobTypeId
                   for itemId in selectedItemIdList if itemId
                  )


    @pyqtSignature('')
    def on_actGroupJobTicketsChanging_triggered(self):
        idList = self.tblJobTickets.selectedItemIdList()
        if idList:
            jobTypeId = self._getJobTypeFromJobTicket(idList[0])
            result = CGroupJobTicketsManipulationsDialog(idList, jobTypeId, self).exec_()
            if result == QtGui.QDialog.Accepted:
                self.updateJobTicketList()


    def getJobType(self, jobId):
        return forceRef(QtGui.qApp.db.translate('Job', 'id', jobId, 'jobType_id')) if jobId else None


    def getOrgStructure(self, jobId):
        return forceRef(QtGui.qApp.db.translate('Job', 'id', jobId, 'orgStructure_id')) if jobId else None


    @pyqtSignature('')
    def on_actSchooseGroupJobTicket_triggered(self):
        jobTicketId = self.tblJobTickets.currentItemId()
        if not jobTicketId:
            return
        capacity = self._getJobCapacityFromJobTicket(jobTicketId)
        if capacity > 1:
            record = self.modelJobTickets.recordCache().get(jobTicketId)
            firstDatetime = forceDateTime(record.value('datetime'))
            firstJobTypeId = self._getJobTypeFromJobTicket(jobTicketId)
            firstMasterId = forceRef(record.value('master_id'))
            jobTicketIdList = self.modelJobTickets.idList()
            model = self.tblJobTickets.model()
            selectionModel = self.tblJobTickets.selectionModel()
            for row, id in enumerate(jobTicketIdList):
                record = self.modelJobTickets.getRecordByRow(row)
                datetime = forceDateTime(record.value('datetime'))
                masterId = forceRef(record.value('master_id'))
                jobTypeId = self.getJobType(masterId)
                capacity = self._getJobCapacityFromJobTicket(id)
                if capacity > 1 and datetime == firstDatetime and masterId == firstMasterId and jobTypeId == firstJobTypeId:
                    index = model.index(row, 0)
                    selectionModel.select(index, QtGui.QItemSelectionModel.Select|QtGui.QItemSelectionModel.Rows)


    @pyqtSignature('')
    def on_actCloseWorkForGroup_triggered(self):
        jobTicketIdList = []
        selectedRowList = self.tblJobTickets.selectedRowList()
        for row in selectedRowList:
            jobTicketId = self.modelJobTickets.getIdByRow(row)
            if jobTicketId:
                capacity = self._getJobCapacityFromJobTicket(jobTicketId)
                if capacity > 1:
                    if jobTicketId not in jobTicketIdList:
                        jobTicketIdList.append(jobTicketId)
        if jobTicketIdList:
            actionTypeIdList, actionTypeDict = self.getActionsFromJobTicket(jobTicketIdList)
            if actionTypeIdList and actionTypeDict:
                db = QtGui.qApp.db
                record = self.modelJobTickets.recordCache().get(jobTicketIdList[0])
                jobId          = forceRef(record.value('master_id'))
                orgStructureId = self.getOrgStructure(jobId)
                jobTypeId      = self.getJobType(jobId)
                datetime       = forceDateTime(record.value('datetime'))
                jobTypeName    = forceString(db.translate('rbJobType', 'id', jobTypeId, 'name')) if jobTypeId else u''
                try:
                    title = u'Закрыть работу для группы %s %s'%(jobTypeName, datetime.toString(Qt.LocaleDate))
                    dialog = CCloseWorkForGroupDialog(self, title, orgStructureId, actionTypeIdList)
                    if dialog.exec_():
                        checkedIdList = dialog.getCheckedIdList()
                        if checkedIdList:
                            status = dialog.getStatus()
                            orgStructureId = dialog.getOrgStructure()
                            personId = dialog.getPerson()
                            execDateTime = dialog.getDateTime()
                            tableAction = db.table('Action')
                            tableJobTicket = db.table('Job_Ticket')
                            records = db.getRecordList(tableJobTicket, u'*', [tableJobTicket['id'].inlist(jobTicketIdList), tableJobTicket['deleted'].eq(0)])
                            for record in records:
                                record.setValue('status', toVariant(status))
                                if not forceDateTime(record.value('begDateTime')):
                                    record.setValue('begDateTime', toVariant(execDateTime))
                                if orgStructureId:
                                    record.setValue('orgStructure_id', toVariant(orgStructureId))
                                if status == CJobTicketStatus.done:
                                    record.setValue('endDateTime', toVariant(execDateTime))
                                else:
                                    record.setValue('endDateTime', toVariant(None))
                                db.updateRecord(tableJobTicket, record)
                            for actionTypetId in checkedIdList:
                                actionIdList = actionTypeDict.get(actionTypetId, [])
                                if actionIdList:
                                    records = db.getRecordList(tableAction, u'*', [tableAction['id'].inlist(actionIdList), tableAction['deleted'].eq(0)])
                                    for record in records:
                                        if not forceDateTime(record.value('begDate')):
                                            record.setValue('begDate', toVariant(execDateTime))
                                        if status == CJobTicketStatus.done:
                                            record.setValue('status', toVariant(CActionStatus.finished))
                                            record.setValue('person_id', toVariant(personId))
                                            record.setValue('endDate', toVariant(execDateTime))
                                        else:
                                            record.setValue('status', toVariant(CActionStatus.started))
                                            record.setValue('endDate', toVariant(None))
                                        db.updateRecord(tableAction, record)
                finally:
                    dialog.deleteLater()
        self.updateJobTicketList()


    def getActionsFromJobTicket(self, jobTicketIdList):
        actionTypeIdList = []
        actionTypeDict = {}
        if not jobTicketIdList:
            return actionTypeIdList, actionTypeDict
        db = QtGui.qApp.db
        tableJobTicket = db.table('Job_Ticket')
        tableAPJobTicket = db.table('ActionProperty_Job_Ticket')
        tableActionProperty = db.table('ActionProperty')
        tableAction = db.table('Action')
        tableActionType = db.table('ActionType')
        queryTable = tableJobTicket.innerJoin(tableAPJobTicket, tableAPJobTicket['value'].eq(tableJobTicket['id']))
        queryTable = queryTable.innerJoin(tableActionProperty, db.joinAnd([tableActionProperty['id'].eq(tableAPJobTicket['id']), tableActionProperty['deleted'].eq(0)]))
        queryTable = queryTable.innerJoin(tableAction, db.joinAnd([tableAction['id'].eq(tableActionProperty['action_id']), tableAction['deleted'].eq(0)]))
        queryTable = queryTable.innerJoin(tableActionType, db.joinAnd([tableActionType['id'].eq(tableAction['actionType_id']), tableActionType['deleted'].eq(0)]))
        cols = [tableActionType['name'],
                tableJobTicket['id'].alias('jobTicketId'),
                tableAction['id'].alias('actionId'),
                tableActionType['id'].alias('actionTypetId'),
                ]
        cond = [tableJobTicket['id'].inlist(jobTicketIdList),
                tableJobTicket['deleted'].eq(0),
                tableJobTicket['status'].eq(CJobTicketStatus.wait),
                tableAction['status'].inlist([CActionStatus.started, CActionStatus.appointed, CActionStatus.wait])
                ]
        records = db.getRecordList(queryTable, cols, cond, tableActionType['name'].name())
        for record in records:
            actionId = forceRef(record.value('actionId'))
            actionTypetId = forceRef(record.value('actionTypetId'))
            if actionTypetId and actionId:
                if actionTypetId not in actionTypeIdList:
                    actionTypeIdList.append(actionTypetId)
                actionIdList = actionTypeDict.get(actionTypetId, [])
                if actionId not in actionIdList:
                    actionIdList.append(actionId)
                    actionTypeDict[actionTypetId] = actionIdList
        return actionTypeIdList, actionTypeDict


    @pyqtSignature('')
    def on_actJobTicketJobTypeChanging_triggered(self):
        jobTicketId = self.tblJobTickets.currentItemId()
        datetime = forceDateTime(self.tblJobTickets.currentItem().value('datetime'))
        clientId = self.modelJobTickets.getClientId(jobTicketId)
        jobTypeId = self._getJobTypeFromJobTicket(jobTicketId)
        result = CJobTicketJobTypeChangerDialog(jobTicketId, jobTypeId, datetime, clientId, self).exec_()
        if result == QtGui.QDialog.Accepted:
            self.updateJobTicketList()


    @pyqtSignature('')
    def on_actEditClient_triggered(self):
        jobTicketId = self.tblJobTickets.currentItemId()
        clientId = self.modelJobTickets.getClientId(jobTicketId)
        if clientId and QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]):
            dialog = CClientEditDialog(self)
            try:
                dialog.load(clientId)
                if dialog.exec_():
                    self.modelJobTickets.invalidateRecordsCache()
            finally:
                dialog.deleteLater()


    @pyqtSignature('')
    def on_actAmbCardShow_triggered(self):
        jobTicketId = self.tblJobTickets.currentItemId()
        clientId = self.modelJobTickets.getClientId(jobTicketId)
        CAmbCardDialog(self, clientId).exec_()


    @pyqtSignature('')
    def on_actEditCurrentJobTicket_triggered(self):
        self.editCurrentJobTicket()


    @pyqtSignature('')
    def on_actEnqueue_triggered(self):
        jobTicketId = self.tblJobTickets.currentItemId()
        if jobTicketId:
            db    = QtGui.qApp.db
            tableJobTicket = db.table('Job_Ticket')
            record = db.getRecordEx(tableJobTicket,
                                    ('id', 'status', 'begDateTime', 'pass', 'registrationDateTime'),
                                    [tableJobTicket['id'].eq(jobTicketId),
                                     tableJobTicket['status'].eq(CJobTicketStatus.wait),
                                    ]
                                   )
            if record:
                record.setValue('status', toVariant(CJobTicketStatus.enqueued))
                record.setValue('begDateTime', toVariant(QDateTime.currentDateTime()))
                record.setValue('registrationDateTime', toVariant(QDateTime.currentDateTime()))
                record.setValue('pass',        toVariant(0))
                db.updateRecord(tableJobTicket, record)
                self.updateJobTicketList()


    @pyqtSignature('')
    def on_actEnqueuePromptly_triggered(self):
        jobTicketId = self.tblJobTickets.currentItemId()
        if jobTicketId:
            db    = QtGui.qApp.db
            tableJobTicket = db.table('Job_Ticket')
            record = db.getRecordEx(tableJobTicket,
                                    ('id', 'status', 'begDateTime', 'pass', 'registrationDateTime'),
                                    [tableJobTicket['id'].eq(jobTicketId),
                                     tableJobTicket['status'].inlist((CJobTicketStatus.wait, CJobTicketStatus.enqueued))
                                    ]
                                   )
            if record:
                begDateTimeNew = self.getPromptlyDateTime()
                if begDateTimeNew:
                    record.setValue('status', toVariant(CJobTicketStatus.enqueued))
                    record.setValue('begDateTime', toVariant(begDateTimeNew))
                    record.setValue('registrationDateTime', toVariant(begDateTimeNew))
                    record.setValue('pass',        toVariant(0))
                    db.updateRecord(tableJobTicket, record)
                    self.updateJobTicketList()


    @pyqtSignature('')
    def on_actSetWaiting_triggered(self):
        jobTicketId = self.tblJobTickets.currentItemId()
        if jobTicketId:
            db    = QtGui.qApp.db
            tableJobTicket = db.table('Job_Ticket')
            record = db.getRecordEx(tableJobTicket,
                                    ('id', 'status', 'begDateTime', 'pass', 'registrationDateTime'),
                                    [tableJobTicket['id'].eq(jobTicketId),
                                     tableJobTicket['status'].eq(CJobTicketStatus.enqueued),
                                    ]
                                   )
            if record:
                record.setValue('status', toVariant(CJobTicketStatus.wait))
                record.setValue('begDateTime', toVariant(QDateTime.currentDateTime()))
                record.setValue('registrationDateTime', toVariant(QDateTime.currentDateTime()))
                record.setValue('pass',        toVariant(0))
                db.updateRecord(tableJobTicket, record)
                self.updateJobTicketList()


    @pyqtSignature('')
    def on_actSetDoing_triggered(self):
        jobTicketId = self.tblJobTickets.currentItemId()
        if jobTicketId:
            db    = QtGui.qApp.db
            tableJobTicket = db.table('Job_Ticket')
            record = db.getRecordEx(tableJobTicket,
                                    ('id', 'status', 'begDateTime', 'pass', 'registrationDateTime'),
                                    [tableJobTicket['id'].eq(jobTicketId),
                                     tableJobTicket['status'].ne(CJobTicketStatus.done),
                                    ]
                                   )
            if record:
                record.setValue('status', toVariant(CJobTicketStatus.doing))
                record.setValue('begDateTime', toVariant(QDateTime.currentDateTime()))
                db.updateRecord(tableJobTicket, record)
                self.updateJobTicketList()


    @pyqtSignature('')
    def on_actEditPassJobTicket_triggered(self):
        jobTicketId = self.tblJobTickets.currentItemId()
        if jobTicketId:
            db    = QtGui.qApp.db
            tableJobTicket = db.table('Job_Ticket')
            record = db.getRecordEx(tableJobTicket,
                                    ('id', 'pass'),
                                    [tableJobTicket['id'].eq(jobTicketId)]
                                   )
            if record:
                passJobTicket = forceInt(record.value('pass'))
                if passJobTicket < 9:
                    record.setValue('pass', toVariant(passJobTicket + 1))
                    db.updateRecord(tableJobTicket, record)
                    self.updateJobTicketList()


    @pyqtSignature('')
    def on_actJobTicketInfo_triggered(self):
        jobTicketId = self.tblJobTickets.currentItemId()
        if jobTicketId:
            showJobTicketInfo(jobTicketId, self)


    @pyqtSignature('')
    def on_actEditJobTickets_triggered(self):
        db = QtGui.qApp.db

        currentIndex = self.tblJobTickets.currentIndex()
        row = currentIndex.row()
        if not (0 <= row < len(self.modelJobTickets.idList())):
            return

        if not self.modelJobTickets.getStatus(row) in (CJobTicketStatus.wait, CJobTicketStatus.enqueued):
            return

        ticketId = self.modelJobTickets.getIdByRow(row)

        tableAPJT  = db.table('ActionProperty_Job_Ticket')
        tableAP    = db.table('ActionProperty')
        tableA     = db.table('Action')
        queryTable = tableAPJT.innerJoin(tableAP, tableAPJT['id'].eq(tableAP['id']))
        queryTable = queryTable.innerJoin(tableA, tableA['id'].eq(tableAP['action_id']))
        eventCond  = [tableAPJT['value'].eq(ticketId),
                      tableA['deleted'].eq(0),
                      tableA['status'].inlist([CActionStatus.started,
                                               CActionStatus.appointed]),
                      tableAP['deleted'].eq(0)
                      ]
        actionRecordList = db.getRecordList(queryTable, 'Action.*', where=eventCond)
        if actionRecordList:
            actionsItemList = [(record, CAction(record=record)) for record in actionRecordList]
        else:
            actionsItemList = []

        currentActionId = self.modelJobTickets.getActionId(row)
        eventId = self.modelJobTickets.getActionEventId(currentActionId)
        eventEditor = CFakeEventEditor(self, eventId)
        QtGui.qApp.setJTR(eventEditor)
        try:
            dlg = CEventJobTicketsListEditor(self,
                                         [],
                                          actionsItemList,
                                         self.modelJobTickets.getClientIdByRow(row),
                                         eventEditor)
            dlg.setBtnCloseJobTicketsVisible(False)
            if eventEditor.lock('Event', eventId):
                try:
                    if dlg.exec_():
                        self.chkJobTicketId.setChecked(dlg.isJobTicketId)
                        self.cmbScanBarcode.setCurrentIndex(0)
                        self.edtJobTicketId.setText(dlg.edtJobTicketIdList)
                finally:
                    eventEditor.releaseLock()
        finally:
            QtGui.qApp.unsetJTR(eventEditor)
        self.updateJobTicketList()


    @pyqtSignature('')
    def on_actScanBarcode_triggered(self):
        self.chkJobTicketId.setChecked(True)
        self.cmbScanBarcode.setCurrentIndex(0) if self.cmbScanBarcode.currentIndex() != 0 else self.on_cmbScanBarcode_currentIndexChanged(0)


    @pyqtSignature('')
    def on_actScanBarcodeTissueType_triggered(self):
        self.chkJobTicketId.setChecked(True)
        self.cmbScanBarcode.setCurrentIndex(1) if self.cmbScanBarcode.currentIndex() != 1 else self.on_cmbScanBarcode_currentIndexChanged(1)


    @pyqtSignature('')
    def on_actScanBarcodeProbe_triggered(self):
        self.chkJobTicketId.setChecked(True)
        self.cmbScanBarcode.setCurrentIndex(2) if self.cmbScanBarcode.currentIndex() != 2 else self.on_cmbScanBarcode_currentIndexChanged(2)


    @pyqtSignature('bool')
    def on_chkJobTicketId_clicked(self, value):
        self.edtJobTicketId.clear()
        self.edtJobTicketId.setFocus(Qt.OtherFocusReason)
        if value:
            self.chkAwaiting.setChecked(False)
            self.chkEnueued.setChecked(False)
            self.chkInProgress.setChecked(False)
            self.chkDone.setChecked(False)
            self.cmbTissueType.setValue(None)
            self.cmbTakenTissueType.setValue(None)
            self.cmbJobPurpose.setValue(None)
            self.cmbOrgStructure.setValue(None)
            self.cmbSpeciality.setValue(None)
            self.cmbPerson.setValue(None)
            self.cmbSex.setCurrentIndex(0)
            self.edtAgeFrom.setValue(self.edtAgeFrom.minimum())
            self.edtAgeTo.setValue(self.edtAgeTo.maximum())


    @pyqtSignature('int')
    def on_cmbOnScanSelect_currentIndexChanged(self, index):
        if index == 0:
            if hasattr(self, 'actScanBarcode') and self.actScanBarcode not in self.actions():
                self.addAction(self.actScanBarcode)
            if hasattr(self, 'actScanBarcodeTissueType') and self.actScanBarcodeTissueType in self.actions():
                self.removeAction(self.actScanBarcodeTissueType)
            if hasattr(self, 'actScanBarcodeProbe') and self.actScanBarcodeProbe in self.actions():
                self.removeAction(self.actScanBarcodeProbe)
        elif index == 1:
            if hasattr(self, 'actScanBarcodeTissueType') and self.actScanBarcodeTissueType not in self.actions():
                self.addAction(self.actScanBarcodeTissueType)
            if hasattr(self, 'actScanBarcode') and self.actScanBarcode in self.actions():
                self.removeAction(self.actScanBarcode)
            if hasattr(self, 'actScanBarcodeProbe') and self.actScanBarcodeProbe in self.actions():
                self.removeAction(self.actScanBarcodeProbe)
        elif index == 2:
            if hasattr(self, 'actScanBarcodeProbe') and self.actScanBarcodeProbe not in self.actions():
                self.addAction(self.actScanBarcodeProbe)
            if hasattr(self, 'actScanBarcodeTissueType') and self.actScanBarcodeTissueType in self.actions():
                self.removeAction(self.actScanBarcodeTissueType)
            if hasattr(self, 'actScanBarcode') and self.actScanBarcode in self.actions():
                self.removeAction(self.actScanBarcode)


    @pyqtSignature('int')
    def on_cmbScanBarcode_currentIndexChanged(self, index):
        self.edtJobTicketId.clear()
        self.edtJobTicketId.setFocus(Qt.OtherFocusReason)


    @pyqtSignature('bool')
    def on_chkAwaiting_clicked(self, value):
        isList = self.edtJobTicketId.text()
        if value and (u',' not in isList):
            self.chkJobTicketId.setChecked(False)


    @pyqtSignature('bool')
    def on_chkEnueued_clicked(self, value):
        isList = self.edtJobTicketId.text()
        if value and (u',' not in isList):
            self.chkJobTicketId.setChecked(False)


    @pyqtSignature('bool')
    def on_chkInProgress_clicked(self, value):
        isList = self.edtJobTicketId.text()
        if value and (u',' not in isList):
            self.chkJobTicketId.setChecked(False)


    @pyqtSignature('bool')
    def on_chkDone_clicked(self, value):
        isList = self.edtJobTicketId.text()
        if value and (u',' not in isList):
            self.chkJobTicketId.setChecked(False)


    @pyqtSignature('int')
    def on_cmbOrgStructureType_currentIndexChanged(self, index):
        orgStructureIndex = self.modelOrgStructure.findItemId(QtGui.qApp.currentOrgStructureId())
        if orgStructureIndex and orgStructureIndex.isValid():
            self.treeOrgStructure.setCurrentIndex(orgStructureIndex)
            self.treeOrgStructure.setExpanded(orgStructureIndex, True)
        self.updateJobTypeList()
        self.updateJobTicketList()
#        orgStructureType = self.cmbOrgStructureType.currentIndex()
#        if orgStructureType in [0, 2]:
#            self.treeOrgStructure.setModel(None)
#            self.setModels(self.treeOrgStructure, self.modelOrgStructure, self.selectionModelOrgStructure)
#            orgStructureIndex = self.modelOrgStructure.findItemId(QtGui.qApp.currentOrgStructureId())
#            if orgStructureIndex and orgStructureIndex.isValid():
#                self.treeOrgStructure.setCurrentIndex(orgStructureIndex)
#                self.treeOrgStructure.setExpanded(orgStructureIndex, True)
#            self.updateJobTicketList()
#        else:
#            self.treeOrgStructure.setModel(None)
#            self.setModels(self.treeOrgStructure, self.modelOrgStructureWithBeds, self.selectionModelOrgStructureWithBeds)
#            rootItem = self.treeOrgStructure.model().getRootItem()
#            orgStructureIndex = self.treeOrgStructure.model().createIndex(rootItem.row(), 0, rootItem)
#            if orgStructureIndex and orgStructureIndex.isValid():
#                self.treeOrgStructure.setCurrentIndex(orgStructureIndex)
#                self.treeOrgStructure.setExpanded(orgStructureIndex, True)
#            self.updateJobTicketList()


    def getOrgStructIdList(self):
        treeIndex = self.treeOrgStructure.currentIndex()
        treeItem = treeIndex.internalPointer() if treeIndex.isValid() else None
        if treeItem:
            return treeItem.getItemIdList()
        return []


    def getJobTypeIdList(self, orgStructIdList, dateType, begDate, endDate):
        db = QtGui.qApp.db
        tableJob = db.table('Job')
        cond = [tableJob['deleted'].eq(0),
                tableJob['jobType_id'].isNotNull()
               ]
        tableJobType = db.table('rbJobType')
        table = tableJob.innerJoin(tableJobType, tableJobType['id'].eq(tableJob['jobType_id']))
        if orgStructIdList and self.cmbOrgStructureType.currentIndex() == 1:
            cond.append(tableJob['orgStructure_id'].inlist(orgStructIdList))

        if dateType in (1, 2):
            tableJobTicket = db.table('Job_Ticket')
            table = table.innerJoin(tableJobTicket,
                                    tableJobTicket['master_id'].eq(tableJob['id']))
            cond.append(tableJobTicket['deleted'].eq(0))
            if dateType == 1:
                cond.append(tableJobTicket['begDateTime'].dateBetween(begDate, endDate))
            else:
                cond.append(tableJobTicket['endDateTime'].dateBetween(begDate, endDate))
        else: # плановая дата
            cond.append(tableJob['date'].between(begDate, endDate))

        if self.jobTypesOrderColumn:
            orderBy = u'rbJobType.name ' + (u'DESC' if self.jobTypesOrderAscending else u'ASC')
        else:
            orderBy = u'rbJobType.code ' + (u'DESC' if self.jobTypesOrderAscending else u'ASC')

        return db.getDistinctIdList(table, idCol='Job.jobType_id', where=cond, order=orderBy)


    def getDateRange(self):
        if self.btnCalendarDate.isChecked():
            begDate = endDate = self.calendar.selectedDate()
        else:
            begDate = self.edtBegDate.date()
            endDate = self.edtEndDate.date()
        return begDate, endDate


    def updateJobTypeList(self):
        orgStructIdList = self.getOrgStructIdList()
        dateType = self.cmbDateType.currentIndex()
        begDate, endDate = self.getDateRange()
        jobTypeIdList = self.getJobTypeIdList(orgStructIdList, dateType, begDate, endDate)
        self.tblJobTypes.setIdList(jobTypeIdList)


    def resetFilter(self):
        self.chkAwaiting.setChecked(True)
        self.chkEnueued.setChecked(False)
        self.chkInProgress.setChecked(False)
        self.chkDone.setChecked(False)
        self.chkOnlyUrgent.setChecked(False)
        self.chkExpired.setChecked(False)
        self.cmbOrgStructure.setValue(None)
        self.cmbSpeciality.setValue(None)
        self.cmbPerson.setValue(None)
        self.cmbSex.setCurrentIndex(0)
        self.edtAgeFrom.setValue(self.edtAgeFrom.minimum())
        self.edtAgeTo.setValue(self.edtAgeTo.maximum())

        self.chkClientId.setChecked(False)
        self.cmbClientAccountingSystem.setValue(None)
        self.edtClientId.clear()

        self.chkClientLastName.setChecked(False)
        self.edtClientLastName.clear()

        self.chkClientFirstName.setChecked(False)
        self.edtClientFirstName.clear()

        self.chkClientPatrName.setChecked(False)
        self.edtClientPatrName.clear()

        self.chkClientBirthDate.setChecked(False)
        self.edtClientBirthDate.clear()

        self.chkExternalEventId.setChecked(False)
        self.edtExternalEventId.clear()

        self.cmbScanBarcode.setCurrentIndex(QtGui.qApp.jobsOperatingIdentifierScan())
        self.chkJobTicketId.setChecked(False)
        self.edtJobTicketId.clear()

        self.cmbDateType.setCurrentIndex(0)
        self.btnCalendarDate.setChecked(True)

        self.cmbTissueType.setValue(None)
        self.cmbTakenTissueType.setValue(None)
        self.cmbJobPurpose.setValue(None)


    def setSortJobTicketsByColumn(self, logicalIndex):
        if self.jobTicketOrderColumn == logicalIndex:
            self.jobTicketOrderAscending = not self.jobTicketOrderAscending
        else:
            self.jobTicketOrderColumn = logicalIndex
            self.jobTicketOrderAscending = True

        header = self.tblJobTickets.horizontalHeader()
        header.setSortIndicatorShown(True)
        header.setSortIndicator(self.jobTicketOrderColumn, Qt.AscendingOrder if self.jobTicketOrderAscending else Qt.DescendingOrder)
        self.updateJobTicketList()

    def setSortJobTypesByColumn(self, logicalIndex):
        if self.jobTypesOrderColumn == logicalIndex:
            self.jobTypesOrderAscending = not self.jobTypesOrderAscending
        else:
            self.jobTypesOrderColumn = logicalIndex
            self.jobTypesOrderAscending = True

        header = self.tblJobTypes.horizontalHeader()
        header.setSortIndicatorShown(True)
        header.setSortIndicator(self.jobTypesOrderColumn, Qt.AscendingOrder if self.jobTypesOrderAscending else Qt.DescendingOrder)
        self.updateJobTypeList()
        QtGui.qApp.preferences.appPrefs['jobTypesOrderAscending'] = toVariant(self.jobTypesOrderAscending)
        QtGui.qApp.preferences.appPrefs['jobTypesOrderColumn'] = toVariant(logicalIndex)

    def getFilter(self):
        begDate, endDate = self.getDateRange()

        return {
          'orgStructIdList': None if self.modelOrgStructure.isRootIndex(self.treeOrgStructure.currentIndex()) else self.getOrgStructIdList(),
          'dateType'       : self.cmbDateType.currentIndex(),
          'begDate'        : begDate,
          'endDate'        : endDate,
#          'jobTypeId'      : self.tblJobTypes.currentItemId(),
          'jobTypeIdList'  : self.tblJobTypes.selectedItemIdList(),
          'awaiting'       : self.chkAwaiting.isChecked(),
          'enqueued'       : self.chkEnueued.isChecked(),
          'inProgress'     : self.chkInProgress.isChecked(),
          'done'           : self.chkDone.isChecked(),
          'onlyUrgent'     : self.chkOnlyUrgent.isChecked(),
          'hideDoneActions': self.chkHideDoneActions.isChecked(),
          'isExpired'      : self.chkExpired.isChecked(),
          'orgStructureId' : self.cmbOrgStructure.value(),
          'specialityId'   : self.cmbSpeciality.value(),
          'setPersonId'    : self.cmbPerson.value(),
          'sex'            : self.cmbSex.currentIndex(),
          'ageFrom'        : self.edtAgeFrom.value(),
          'ageTo'          : self.edtAgeTo.value(),
          'tissueTypeId'   : self.cmbTissueType.value(),
          'takenTissueTypeId': self.cmbTakenTissueType.value(),
          'jobPurposeId'   : self.cmbJobPurpose.value(),
          'chkClientId'    : self.chkClientId.isChecked(),
          'clientAccountingSystemId': self.cmbClientAccountingSystem.value(),
          'clientId'       : trim(self.edtClientId.text()),
          'chkClientLastName': self.chkClientLastName.isChecked(),
          'clientLastName' : trim(self.edtClientLastName.text()),
          'chkClientFirstName': self.chkClientFirstName.isChecked(),
          'clientFirstName': trim(self.edtClientFirstName.text()),
          'chkClientPatrName': self.chkClientPatrName.isChecked(),
          'clientPatrName' : trim(self.edtClientPatrName.text()),
          'chkClientBirthDate': self.chkClientBirthDate.isChecked(),
          'clientBirthDate': trim(self.edtClientBirthDate.date()),
          'chkExternalEventId': self.chkExternalEventId.isChecked(),
          'externalEventId': trim(self.edtExternalEventId.text()),
          'chkJobTicketId' : self.chkJobTicketId.isChecked(),
          'scanBarcode'    : self.cmbScanBarcode.currentIndex(),
          'externalId'     : trim(self.edtJobTicketId.text()),
          }


    def prepareQueryPartsByJobTicketId(self, jobTicketId):
        db          = QtGui.qApp.db
        table       = db.table('Job_Ticket')
        tableAPJT   = db.table('ActionProperty_Job_Ticket')
        tableAP     = db.table('ActionProperty')
        tableAction = db.table('Action')

        queryTable  = table
        queryTable  = queryTable.innerJoin(tableAPJT, tableAPJT['value'].eq(table['id']))
        queryTable  = queryTable.leftJoin(tableAP,     tableAP['id'].eq(tableAPJT['id']))
        queryTable  = queryTable.leftJoin(tableAction, tableAction['id'].eq(tableAP['action_id']))
        order = self.getOrder()
        jobTicketIdList = jobTicketId.split(',')
        return queryTable, table['id'].inlist(jobTicketIdList), order


    def prepareQueryPartsByTakenTissueId(self, takenTissueId):
        db = QtGui.qApp.db
        table                   = db.table('Job_Ticket')
        tableAPJT               = db.table('ActionProperty_Job_Ticket')
        tableAP                 = db.table('ActionProperty')
        tableTakenTissueJournal = db.table('TakenTissueJournal')
        tableAction             = db.table('Action')
        queryTable  = table.innerJoin(tableAPJT, tableAPJT['value'].eq(table['id']))
        queryTable  = queryTable.leftJoin(tableAP,     tableAP['id'].eq(tableAPJT['id']))
        queryTable  = queryTable.leftJoin(tableAction, tableAction['id'].eq(tableAP['action_id']))
        queryTable  = queryTable.innerJoin(tableTakenTissueJournal, tableTakenTissueJournal['id'].eq(tableAction['takenTissueJournal_id']))
        order = self.getOrder()
        takenTissueIdList = takenTissueId.split(',')
        cond = [tableTakenTissueJournal['externalId'].inlist(takenTissueIdList),
                tableTakenTissueJournal['deleted'].eq(0),
                table['deleted'].eq(0),
                tableAP['deleted'].eq(0),
                tableAction['deleted'].eq(0)
                ]
        return queryTable, cond, order


    def prepareQueryPartsByProbeId(self, probeId):
        db = QtGui.qApp.db
        table                   = db.table('Job_Ticket')
        tableAPJT               = db.table('ActionProperty_Job_Ticket')
        tableAP                 = db.table('ActionProperty')
        tableProbe              = db.table('Probe')
        tableTakenTissueJournal = db.table('TakenTissueJournal')
        tableAction             = db.table('Action')
        queryTable  = table.innerJoin(tableAPJT, tableAPJT['value'].eq(table['id']))
        queryTable  = queryTable.leftJoin(tableAP,     tableAP['id'].eq(tableAPJT['id']))
        queryTable  = queryTable.leftJoin(tableAction, tableAction['id'].eq(tableAP['action_id']))
        queryTable  = queryTable.innerJoin(tableTakenTissueJournal, tableTakenTissueJournal['id'].eq(tableAction['takenTissueJournal_id']))
        queryTable  = queryTable.innerJoin(tableProbe, tableProbe['takenTissueJournal_id'].eq(tableTakenTissueJournal['id']))
        order = self.getOrder()
        probeIdList = probeId.split(',')
        cond = [tableProbe['externalId'].inlist(probeIdList),
                tableTakenTissueJournal['deleted'].eq(0),
                table['deleted'].eq(0),
                tableAP['deleted'].eq(0),
                tableAction['deleted'].eq(0)
                ]
        return queryTable, cond, order


    def prepareQueryParts(self, filter):
        isClientFilter  = self.tabDateClientFilter.widget(self.tabDateClientFilter.currentIndex()) == self.tabClientFilter
        orgStructIdList = filter['orgStructIdList']
        dateType        = filter['dateType']
        begDate         = filter['begDate']
        endDate         = filter['endDate']
#        jobTypeId       = filter['jobTypeId']
        jobTypeIdList   = filter['jobTypeIdList']
        awaiting        = filter['awaiting']
        enqueued        = filter['enqueued']
        inProgress      = filter['inProgress']
        done            = filter['done']
        onlyUrgent      = filter['onlyUrgent']
        isExpired       = filter['isExpired']
        orgStructureId  = filter['orgStructureId']
        specialityId    = filter['specialityId']
        setPersonId     = filter['setPersonId']
        sex             = filter['sex']
        ageFrom         = filter['ageFrom']
        ageTo           = filter['ageTo']
        tissueTypeId    = filter['tissueTypeId']
        takenTissueTypeId = filter['takenTissueTypeId']
        jobPurposeId    = filter['jobPurposeId']
        chkJobTicketId  = filter['chkJobTicketId']
        scanBarcode     = filter['scanBarcode']
        externalId      = filter['externalId']

        if chkJobTicketId:
            if scanBarcode == 0:
                return self.prepareQueryPartsByJobTicketId(externalId)
            elif scanBarcode == 1:
                return self.prepareQueryPartsByTakenTissueId(externalId)
            elif scanBarcode == 2:
                return self.prepareQueryPartsByProbeId(externalId)

        db = QtGui.qApp.db
        tableAPJT           = db.table('ActionProperty_Job_Ticket')
        tableAP             = db.table('ActionProperty')
        tableAction         = db.table('Action')
        tableActionType     = db.table('ActionType')
        tablePerson         = db.table('vrbPersonWithSpeciality')
        tableEvent          = db.table('Event')
        tablePerson_          = db.table('Person')
        tableClient         = db.table('Client')
        tableJob            = db.table('Job')
        tableJobTicket      = db.table('Job_Ticket')
        tableJobPurpose     = db.table('rbJobPurpose')
        tableIdentification = db.table('ClientIdentification')
        tableOrgStructure   = db.table('OrgStructure')
        tableTakenTissueJournal = db.table('TakenTissueJournal')

        queryTable = tableJobTicket
        queryTable = queryTable.leftJoin(tableJob,    tableJob['id'].eq(tableJobTicket['master_id']))
        queryTable = queryTable.leftJoin(tableAPJT,   tableAPJT['value'].eq(tableJobTicket['id']))
        queryTable = queryTable.leftJoin(tableAP,     tableAP['id'].eq(tableAPJT['id']))
        queryTable = queryTable.leftJoin(tableAction, tableAction['id'].eq(tableAP['action_id']))
        queryTable = queryTable.leftJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
        queryTable = queryTable.leftJoin(tablePerson, tablePerson['id'].eq(tableAction['setPerson_id']))
        queryTable = queryTable.leftJoin(tablePerson_, tablePerson_['id'].eq(tableAction['person_id']))
        queryTable = queryTable.leftJoin(tableEvent,  tableEvent['id'].eq(tableAction['event_id']))
        queryTable = queryTable.leftJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
        queryTable = queryTable.leftJoin(tableJobPurpose, tableJobPurpose['id'].eq(tableJob['jobPurpose_id']))
        queryTable = queryTable.leftJoin(tableOrgStructure, tableOrgStructure['id'].eq(tableJobTicket['orgStructure_id']))
        queryTable = queryTable.leftJoin(tableTakenTissueJournal, tableTakenTissueJournal['id'].eq(tableAction['takenTissueJournal_id']))

        orgStructureType = self.cmbOrgStructureType.currentIndex()
        cond = [tableJobTicket['deleted'].eq(0),
                tableJob['deleted'].eq(0),
#                tableJob['jobType_id'].eq(jobTypeId),
                tableJob['jobType_id'].inlist(jobTypeIdList),
                tableAction['deleted'].eq(0),
                tableAction['deleted'].eq(0),
                tableEvent['deleted'].eq(0),
                tableClient['deleted'].eq(0)]
#        if orgStructureType == 1:
#            # список пациентов, лежащих где надо, придётся формировать вручную
#            if self.treeOrgStructure.currentIndex() == self.treeOrgStructure.rootIndex():
#                cond = [] # для корня мы ничего не фильтруем!
#            else:
#                client_ids = QtGui.qApp.db.getIdList(queryTable, idCol='Client.id')
#                if orgStructIdList:
#                    client_ids2 = [c for c in client_ids if c != 0 and getClientOrgStructureId(c) in orgStructIdList]
#                else:
#                    client_ids2 = []
#                if client_ids2:
#                    cond.append(tableClient['id'].inlist(client_ids2))
#        if orgStructureType == 1:
#            if orgStructIdList:
#                cond.append(tableJob['orgStructure_id'].inlist(orgStructIdList))
        if orgStructIdList:
            if orgStructureType == 0:
                cond.append(tableJobTicket['orgStructure_id'].inlist(orgStructIdList))
            elif orgStructureType == 1:
                cond.append(tableJob['orgStructure_id'].inlist(orgStructIdList))
            elif orgStructureType == 2:
                actionTypeIdList = getActionTypeIdListByFlatCode(u'moving%')
                if actionTypeIdList:
                    db = QtGui.qApp.db
                    cond.append('''EXISTS(SELECT A.id
                    FROM Action AS A
                    INNER JOIN Event AS E ON E.id = A.event_id
                    INNER JOIN ActionPropertyType AS APT ON APT.actionType_id=A.actionType_id
                    INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id
                    INNER JOIN ActionProperty_OrgStructure AS APOS ON APOS.id=AP.id
                    WHERE A.actionType_id IN (%s)
                    AND E.client_id = Event.client_id
                    AND APOS.value IN (%s)
                    AND A.endDate IS NULL
                    AND AP.action_id=A.id AND A.deleted = 0 AND E.deleted = 0
                    AND APT.deleted=0 AND APT.name %s)'''%(','.join(forceString(actionTypeId) for actionTypeId in actionTypeIdList if actionTypeId),
                   ','.join(forceString(orgStructureId) for orgStructureId in orgStructIdList if orgStructureId) , updateLIKE(u'Отделение пребывания')))
        statuses = []
        if awaiting and enqueued and inProgress and done:
            pass
        else:
            if awaiting   : statuses.append(CJobTicketStatus.wait)
            if enqueued   : statuses.append(CJobTicketStatus.enqueued)
            if inProgress : statuses.append(CJobTicketStatus.doing)
            if done       : statuses.append(CJobTicketStatus.done)
        if isExpired and CJobTicketStatus.wait not in statuses:
            statuses.append(CJobTicketStatus.wait)
        if statuses:
            cond.append(tableJobTicket['status'].inlist(statuses))
        if tissueTypeId:
            if tissueTypeId == -1:
                cond.append('EXISTS (SELECT id FROM ActionType_TissueType WHERE master_id=ActionType.`id`)')
            elif tissueTypeId == -2:
                cond.append('NOT EXISTS (SELECT id FROM ActionType_TissueType WHERE master_id=ActionType.`id`)')
            else:
                cond.append('EXISTS (SELECT id FROM ActionType_TissueType WHERE master_id=ActionType.`id` AND tissueType_id=%d)'%tissueTypeId)
        if takenTissueTypeId:
            if takenTissueTypeId == -1:
                cond.append('EXISTS (SELECT id FROM TakenTissueJournal WHERE Action.`takenTissueJournal_id`=TakenTissueJournal.`id`)')
            elif takenTissueTypeId == -2:
                cond.append('NOT EXISTS (SELECT id FROM TakenTissueJournal WHERE Action.`takenTissueJournal_id`=TakenTissueJournal.`id`)')
            else:
                cond.append('EXISTS (SELECT id FROM TakenTissueJournal WHERE Action.`takenTissueJournal_id`=TakenTissueJournal.`id` and TakenTissueJournal.`tissueType_id`=%d)'%takenTissueTypeId)
        if jobPurposeId:
            if jobPurposeId == -2: # без назначения
                cond.append(tableJob['jobPurpose_id'].isNull())
            elif jobPurposeId == -1: # любое назначение
                cond.append(tableJob['jobPurpose_id'].isNotNull())
            else:
                cond.append(tableJob['jobPurpose_id'].eq(jobPurposeId))
        if onlyUrgent:
            cond.append(tableAction['isUrgent'].ne(0))
        if isExpired:
            tableJobType = db.table('rbJobType')
            queryTable = queryTable.innerJoin(tableJobType, tableJobType['id'].eq(tableJob['jobType_id']))
            cond.append(db.joinOr([db.joinAnd([tableJobType['ticketDuration'].gt(1),
                                               tableJobTicket['datetime'].name() + '< CURRENT_DATE()',
                                               tableJobTicket['datetime'].dateAddDay(tableJobType['ticketDuration']).name() + '< CURRENT_DATE()'
                                              ]),
                                   db.joinAnd([
                                              tableJobType['ticketDuration'].le(1),
                                              tableJobTicket['datetime'].name() + ' < CURRENT_DATE()'
                                              ]),
                                  ]))
        if orgStructureId:
            cond.append(tableJobTicket['orgStructure_id'].eq(orgStructureId))
        if specialityId:
            cond.append(tablePerson['speciality_id'].eq(specialityId))
        if setPersonId:
            cond.append(tableAction['setPerson_id'].eq(setPersonId))
        if sex:
            cond.append(tableClient['sex'].eq(sex))
        if ageFrom <= ageTo:
            cond.append('Job_Ticket.datetime >= ADDDATE(Client.birthDate, INTERVAL %d YEAR)'%ageFrom)
            cond.append('Job_Ticket.datetime < SUBDATE(ADDDATE(Client.birthDate, INTERVAL %d YEAR),1)'%(ageTo+1))
        if isClientFilter:
            chkClientId              = filter['chkClientId']
            clientAccountingSystemId = filter['clientAccountingSystemId']
            clientId                 = filter['clientId']
            chkClientLastName        = filter['chkClientLastName']
            clientLastName           = filter['clientLastName']
            chkClientFirstName       = filter['chkClientFirstName']
            clientFirstName          = filter['clientFirstName']
            chkClientPatrName        = filter['chkClientPatrName']
            clientPatrName           = filter['clientPatrName']
            chkClientBirthDate       = filter['chkClientBirthDate']
            clientBirthDate          = filter['clientBirthDate']
            chkExternalEventId       = filter['chkExternalEventId']
            externalEventId          = filter['externalEventId']

            if chkClientId:
                if bool(clientId):
                    if clientAccountingSystemId:
                        queryTable = queryTable.innerJoin(tableIdentification,
                                                          tableIdentification['client_id'].eq(tableClient['id']))
                        cond.extend(
                                    [tableIdentification['accountingSystem_id'].eq(clientAccountingSystemId),
                                     tableIdentification['identifier'].eq(clientId)])
                    else:
                        cond.append(tableClient['id'].eq(clientId))
            else:
                if chkClientLastName and clientLastName:
                    clientLastName = clientLastName + u'%'
                    cond.append(tableClient['lastName'].like(clientLastName))
                if chkClientFirstName and clientFirstName:
                    clientFirstName = clientFirstName + u'%'
                    cond.append(tableClient['firstName'].like(clientFirstName))
                if chkClientPatrName and clientPatrName:
                    clientPatrName = clientPatrName + u'%'
                    cond.append(tableClient['patrName'].like(clientPatrName))
                if chkClientBirthDate:
                    clientBirthDate = forceDate(self.edtClientBirthDate.date())
                    cond.append(tableClient['birthDate'].dateEq(clientBirthDate))
                if chkExternalEventId and externalEventId:
                    cond.append(tableEvent['externalId'].eq(externalEventId))
        else:
            if dateType == 1:
                cond.append(tableJobTicket['begDateTime'].dateBetween(begDate, endDate))
            elif dateType == 2:
                cond.append(tableJobTicket['endDateTime'].dateBetween(begDate, endDate))
            else:
                cond.append(tableJob['date'].between(begDate, endDate))
        order = self.getOrder()
        return queryTable, cond, order


    def getOrder(self):
        if self.jobTicketOrderColumn == 0:
            order = 'cast(TakenTissueJournal.externalId as signed), Job_Ticket.master_id'
        elif self.jobTicketOrderColumn == 1:
            order = 'rbJobPurpose.code, Job_Ticket.master_id'
        elif self.jobTicketOrderColumn == 2:
            order = 'ActionType.name, Job_Ticket.master_id'
        elif self.jobTicketOrderColumn == 3:
            order = 'Job_Ticket.isExceedQuantity, Job_Ticket.id'
        elif self.jobTicketOrderColumn == 4:
            order = 'Job_Ticket.pass, Job_Ticket.idx'
        elif self.jobTicketOrderColumn == 5:
            order = 'Job_Ticket.isExceedQuantity, Job_Ticket.idx'
        elif self.jobTicketOrderColumn == 6:
            order = 'Job_Ticket.status'
        elif self.jobTicketOrderColumn == 7:
            order = 'Job_Ticket.begDateTime'
        elif self.jobTicketOrderColumn == 8:
            order = 'Job_Ticket.isExceedQuantity, Job_Ticket.datetime'
        elif self.jobTicketOrderColumn == 9:
            order = 'Client.lastName, Client.firstName, Client.patrName, Job_Ticket.datetime'
        elif self.jobTicketOrderColumn == 10:
            order = 'Job_Ticket.isExceedQuantity, Client.sex, Job_Ticket.datetime'
        elif self.jobTicketOrderColumn == 11:
            order = 'Job_Ticket.isExceedQuantity, Client.birthDate, Job_Ticket.datetime'
        elif self.jobTicketOrderColumn == 12:
            order = 'Job_Ticket.isExceedQuantity, Job_Ticket.label, Job_Ticket.datetime'
        elif self.jobTicketOrderColumn == 13:
            order = 'OrgStructure.name'
        elif self.jobTicketOrderColumn == 14:
            order = 'Job_Ticket.isExceedQuantity, Job_Ticket.note, Job_Ticket.datetime'
        else:
            order = 'Job_Ticket.isExceedQuantity, Job_Ticket.id'
        if not self.jobTicketOrderAscending:
            order = ','.join([part + ' DESC' for part in order.split(',')])
        return order


    def getFilterDescription(self, filter):
        begDate        = filter['begDate']
        endDate        = filter['endDate']
        jobTypeIdList  = filter['jobTypeIdList']
        awaiting       = filter['awaiting']
        enqueued       = filter['enqueued']
        inProgress     = filter['inProgress']
        done           = filter['done']
        onlyUrgent     = filter['onlyUrgent']
        orgStructureId = filter['orgStructureId']
        specialityId   = filter['specialityId']
        setPersonId    = filter['setPersonId']
        sex            = filter['sex']
        ageFrom        = filter['ageFrom']
        ageTo          = filter['ageTo']

        db = QtGui.qApp.db
        description = [u'дата c ' + forceString(begDate) + u' по ' + forceString(endDate)]
        if len(jobTypeIdList) == 1 :
           jobTypeName = forceString(db.translate('rbJobType', 'id', jobTypeIdList[0], 'name'))
           description.append(u'работа: '+jobTypeName)
        elif len(jobTypeIdList) >1 :
           jobTypeNames = formatList([forceString(db.translate('rbJobType', 'id', jobTypeId, 'name'))
                                      for jobTypeId in jobTypeIdList
                                     ]
                                    )
           description.append(u'работы: '+jobTypeNames)
        if awaiting:
            description.append(u'ожидающие')
        if enqueued:
            description.append(u'в очереди')
        if inProgress:
            description.append(u'выполняемые')
        if done:
            description.append(u'законченные')
        if onlyUrgent:
            description.append(u'только срочные')
        if orgStructureId:
            description.append(u'подразделение: '+getOrgStructureFullName(orgStructureId))
        if specialityId:
            description.append(u'специальность: '+forceString(db.translate('rbSpeciality', 'id', specialityId, 'name')))
        if self.filter['setPersonId']:
            personInfo = getPersonInfo(setPersonId)
            description.append(u'врач: ' + personInfo['shortName']+', '+personInfo['specialityName'])
        if sex:
            description.append(u'пол: ' + formatSex(sex))
        if ageFrom <= ageTo:
            description.append(u'возраст: c %d по %d %s' % (ageFrom, ageTo, agreeNumberAndWord(ageTo, (u'год', u'года', u'лет'))))
        return '\n'.join(description)


    def updateJobTicketList(self):
        # Где-то есть зависимость от текущего состояния фиильтра. Не готов разгребать это,
        # по этому фильтр будем формировать в любом случае
        self.filter = self.getFilter()
        # При открытии нам нужно загружать один раз список, а не несколько как сейчас.
        if not self._jobTicketsListUpdatingAllowed:
            return

        queryTable, cond, order = self.prepareQueryParts(self.filter)
        db = QtGui.qApp.db
#        idList = db.getDistinctIdList(queryTable, 'Job_Ticket.id', cond, order)
        idList = []
        actionIdList = []
        isUrgentJTData = {}
        isUrgentJobTickets = 0
        isUrgentActions = 0
        amountCount = 0
        recordList = db.getRecordList(queryTable, 'Job_Ticket.id AS  jobTicketId, Action.id AS actionId, Action.amount AS actionAmount, Action.isUrgent', cond, order)
        for record in recordList:
            jobTicketId = forceRef(record.value('jobTicketId'))
            isUrgent = forceBool(record.value('isUrgent'))
            if jobTicketId not in idList:
                idList.append(jobTicketId)
            if isUrgent and not isUrgentJTData.get(jobTicketId, False):
                isUrgentJTData[jobTicketId] = isUrgent
                isUrgentJobTickets += 1
            actionId = forceRef(record.value('actionId'))
            if actionId not in actionIdList:
                actionIdList.append(actionId)
                actionAmount = forceDouble(record.value('actionAmount'))
                amountCount += actionAmount
                isUrgentActions += 1 if isUrgent else 0
        self.tblJobTickets.setIdList(idList)
        if self.filter['chkJobTicketId'] and self.filter['scanBarcode'] == 0 and idList:
            self.setValuesByJobTicketId(idList[0])
        bannerHTML = u'''<B><font color=black>%s</font></B><BR>'''%(formatRecordsCount(len(idList)))
        if isUrgentJobTickets:
            bannerHTML += u'''<B><font color=red>%s</font></B><BR>'''%(u'\nиз них %d срочных'%(isUrgentJobTickets))
        bannerHTML += u'''<B><font color=black>%s</font></B><BR>'''%(u'Всего мероприятий: %d'%len(actionIdList))
        if isUrgentActions:
            bannerHTML += u'''<B><font color=red>%s</font></B><BR>'''%(u'\nиз них %d срочных'%(isUrgentActions))
        bannerHTML += u'''<B><font color=black>%s</font></B>'''%(u'Кол-во услуг: %.2f'%amountCount)
        self.lblTicketsCount.setText("<html><head/><body><p><span>%s</span></p></body></html>"%(bannerHTML))


    def updateJobTicketActionsModel(self, jobTicketId):
        jtRecord = self.tblJobTickets.currentItem()
        if jtRecord:
            actionIdList = CJobTicket(jtRecord).getActionIdList(self.filter.get('hideDoneActions', False))
        else:
            actionIdList = []

        self.setActionIdList(actionIdList)


    def setActionIdList(self, actionIdList):
        self.tblJobTicketActions.setIdList(actionIdList)
        self.lblActionsCount.setText(formatRecordsCount(len(actionIdList)))


    def setValuesByJobTicketId(self, jobTicketId):
        db = QtGui.qApp.db
        record = db.getRecord('Job_Ticket', 'datetime, begDateTime, endDateTime, master_id', jobTicketId)
        if record:
            dataType = self.cmbDateType.currentIndex()
            if dataType == 1:
                date = forceDate(record.value('begDateTime'))
            elif dataType == 2:
                date = forceDate(record.value('endDateTime'))
            else:
                date = forceDate(record.value('datetime'))
            jobTypeId = forceRef(db.translate('Job', 'id', forceRef(record.value('master_id')), 'jobType_id'))
            if self.btnCalendarDate.isChecked():
                self.calendar.blockSignals(True)
                self.calendar.setSelectedDate(date)
                self.calendar.blockSignals(False)
            else:
                for edt in self.edtBegDate, self.edtEndDate:
                    edt.blockSignals(True)
                    edt.setDate(date)
                    edt.blockSignals(False)
            jobTypeIdList = self.modelJobTypes.idList()
            if jobTypeId in jobTypeIdList:
                row = jobTypeIdList.index(jobTypeId)
                self.tblJobTypes.setCurrentIndex(self.modelJobTypes.index(row, 0))


    def checkJobTicketIdDurationMessage(self, message, widget):
        buttons = QtGui.QMessageBox.Ok | QtGui.QMessageBox.No
        res = QtGui.QMessageBox.warning( self,
                                         u'Внимание!',
                                         message,
                                         buttons,
                                         QtGui.QMessageBox.Ok)
        if res == QtGui.QMessageBox.Ok:
            self.setFocusToWidget(widget)
            return False
        return True


    def editCurrentJobTicket(self, openProbes=False):
        jobTicketId = self.tblJobTickets.currentItemId()
        if jobTicketId:
            if self.modelJobTickets.getStatus(self.tblJobTickets.currentRow()) == CJobTicketStatus.wait:
                db = QtGui.qApp.db
                tableJob       = db.table('Job')
                tableJobTicket = db.table('Job_Ticket')
                tableJobType   = db.table('rbJobType')
                queryTable = tableJobTicket.leftJoin(tableJob, tableJob['id'].eq(tableJobTicket['master_id']))
                queryTable = queryTable.innerJoin(tableJobType, tableJobType['id'].eq(tableJob['jobType_id']))
                cond = [tableJobTicket['id'].eq(jobTicketId),
                        tableJob['deleted'].eq(0),
                        tableJobTicket['deleted'].eq(0)
                        ]
                cond.append(db.joinOr([db.joinAnd([tableJobType['ticketDuration'].gt(1),
                                                   db.joinOr([db.joinAnd([tableJobTicket['datetime'].name() + '< CURRENT_DATE()',
                                                                          tableJobTicket['datetime'].dateAddDay(tableJobType['ticketDuration']).name() + '>= CURRENT_DATE()'
                                                                          ]),
                                                              tableJobTicket['datetime'].name() + ' > CURRENT_DATE()'
                                                             ])
                                                   ]),
                                       tableJobTicket['datetime'].name() + ' >= CURRENT_DATE()'
                                      ]))
                record = db.getRecordEx(queryTable, [tableJobTicket['id']], cond)
                jobTicketIdDuration = forceRef(record.value('id')) if record else None
                if not jobTicketIdDuration and self.checkJobTicketIdDurationMessage(u'Срок действия направления истек, хотите продолжить?', self.tblJobTickets):
                        return
            checkedIdList = self.modelJobTicketActions.getCheckedActionIdList()
            actualActionIdList = checkedIdList if checkedIdList else self.modelJobTicketActions.idList()
            if QtGui.qApp.checkGlobalPreference(u'23:JobExecuteLock', u'да'):
                for id in actualActionIdList:
                    dialog = CJobTicketEditor(self, actualActionIdList)
                    lockId = None
                    try:
                        lockId = self.lock('Action', id)
                        if lockId:
                            dialog.load(jobTicketId)
                            if openProbes:
                                dialog.openProbesQueuedSignal.emit()
                            if dialog.exec_() or dialog.needUpdateAfterClose:
                                self.updateJobTicketList()
                    except Exception, e:
                        QtGui.qApp.logCurrentException()
                    finally:
                        dialog.deleteLater()
                        if lockId:
                            self.releaseLock(lockId)
            else:
                dialog = CJobTicketEditor(self, actualActionIdList)
                try:
                    dialog.load(jobTicketId)
                    if openProbes:
                        dialog.openProbesQueuedSignal.emit()
                    if dialog.exec_() or dialog.needUpdateAfterClose:
                        self.updateJobTicketList()
                finally:
                    dialog.deleteLater()


    def resetChkClientId(self):
        self.chkClientId.setChecked(False)


    @pyqtSignature('bool')
    def on_chkClientId_clicked(self, value):
        if value:
            self.chkClientLastName.setChecked(False)
            self.chkClientFirstName.setChecked(False)
            self.chkClientPatrName.setChecked(False)
            self.chkClientBirthDate.setChecked(False)


    @pyqtSignature('bool')
    def on_chkClientLastName_clicked(self, value):
        if value and self.chkClientId.isChecked():
            self.resetChkClientId()


    @pyqtSignature('bool')
    def on_chkClientFirstName_clicked(self, value):
        if value and self.chkClientId.isChecked():
            self.resetChkClientId()


    @pyqtSignature('bool')
    def on_chkClientPatrName_clicked(self, value):
        if value and self.chkClientId.isChecked():
            self.resetChkClientId()


    @pyqtSignature('bool')
    def on_chkClientBirthDate_clciked(self, value):
        if value and self.chkClientId.isChecked():
            self.resetChkClientId()


    @pyqtSignature('int')
    def on_tabDateClientFilter_currentChanged(self, tabIndex):
        ticketId = self.tblJobTickets.currentItemId()
        needCheck = bool(ticketId)
        self.chkClientId.setChecked(needCheck)
        if needCheck:
            clientId = self.modelJobTickets.getClientId(ticketId)
            if clientId:
                self.edtClientId.setText(unicode(clientId))
                self.updateJobTicketList()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelJobTicketActions_currentChanged(self, current, previous):
        if current.isValid():
            row = current.row()
            actionId = self.modelJobTicketActions.idList()[row]
            actionTypeId = self.modelJobTicketActions.getActionTypeId(actionId)
            actionType = CActionTypeCache.getById(actionTypeId) if actionTypeId else None
            context = actionType.context if actionType else None
            self.actActionPrint.setContext(context)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelJobTickets_currentChanged(self, current, previous):
        if current.isValid():
            row = current.row()
            jobTicketId = self.modelJobTickets.idList()[row]
            self.updateJobTicketActionsModel(jobTicketId)
        else:
            self.updateJobTicketActionsModel(None)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelOrgStructure_currentChanged(self, current, previous):
        self.updateJobTypeList()


    @pyqtSignature('int')
    def on_cmbDateType_currentIndexChanged(self, index):
        self.updateJobTypeList()


    @pyqtSignature('int, int')
    def on_calendar_currentPageChanged(self, year, month):
        selectedDate = self.calendar.selectedDate()
        currYear = selectedDate.year()
        currMonth = selectedDate.month()
        newDate = selectedDate.addMonths((year-currYear)*12+(month-currMonth))
        self.calendar.setSelectedDate(newDate)
#        self.updateJobTypeList()


    @pyqtSignature('')
    def on_calendar_selectionChanged(self):
        self.updateJobTypeList()


    @pyqtSignature('bool')
    def on_btnCalendarDate_clicked(self, value):
        self.updateJobTypeList()


    @pyqtSignature('bool')
    def on_btnDateRange_clicked(self, value):
        self.updateJobTypeList()


    @pyqtSignature('QDate')
    def on_edtBegDate_dateChanged(self, date):
        self.updateJobTypeList()


    @pyqtSignature('QDate')
    def on_edtEndDate_dateChanged(self, date):
        self.updateJobTypeList()


    @pyqtSignature('QItemSelection, QItemSelection')
    def on_selectionModelJobTypes_selectionChanged(self, selected, deselected):
        self.updateJobTicketList()
        jobTypeIdList = self.filter['jobTypeIdList']
        contextSet = set([forceString(QtGui.qApp.db.translate('rbJobType', 'id', jobTypeId, 'listContext'))
                          for jobTypeId in jobTypeIdList
                         ]
                        )
        contextSet.discard('jobTicket_list')
        contextList = ['jobTicket_list']
        if len(contextSet) == 1:
            context = list(contextSet)[0]
            if context:
                contextList.append(context)
        self.actJobTicketListPrint.setContext(contextList, False)


    @pyqtSignature('int')
    def on_cmbOrgStructure_currentIndexChanged(self, index):
        orgStructureId = self.cmbOrgStructure.value()
        self.cmbPerson.setOrgStructureId(orgStructureId)


    @pyqtSignature('int')
    def on_cmbSpeciality_currentIndexChanged(self, index):
        specialityId = self.cmbSpeciality.value()
        self.cmbPerson.setSpecialityId(specialityId)


    @pyqtSignature('int')
    def on_modelJobTickets_itemsCountChanged(self, count):
        self.lblTicketsCount.setText("<html><head/><body><p><span>%s</span></p></body></html>"%(formatRecordsCount(count)))


    @pyqtSignature('QAbstractButton*')
    def on_buttonBoxFilter_clicked(self, button):
        buttonCode = self.buttonBoxFilter.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.updateJobTicketList()
            self.tblJobTickets.setFocus()
            if self.chkJobTicketId.isChecked():
                if self.cmbOnScan.currentIndex() == 1:
                    self.editCurrentJobTicket()
                elif self.cmbOnScan.currentIndex() == 2:
                    self.editCurrentJobTicket(openProbes=True)

        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.resetFilter()
            self.updateJobTicketList()


    @pyqtSignature('QModelIndex')
    def on_tblJobTickets_doubleClicked(self, index):
        self.editCurrentJobTicket()


    @pyqtSignature('')
    def on_actPrintClientNumberTicket_triggered(self):

        index = self.tblJobTicketActions.currentIndex()
        if not index.isValid():
            return
        row = index.row()
        context = CInfoContext()
        actionId = self.modelJobTicketActions.idList()[row]
        actionInfo = context.getInstance(CActionInfo, actionId)
        data = {'action': actionInfo }
        templateRecord = QtGui.qApp.db.getRecordEx(u'rbPrintTemplate', u'id', u"deleted = 0 and  context like 'barcodeProbe' "  )
        templateId = forceInt(templateRecord.value('id')) if templateRecord else None
        if templateId:
            applyTemplate(self, templateId, data)



    @pyqtSignature('')
    def on_actMainPrint_triggered(self):
        if not self.filter:
            return
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Выполнение работ')
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertText(self.getFilterDescription(self.filter))
        cursor.insertBlock()

        tableColumns = [
            ('2%',  [u'№'],                 CReportBase.AlignRight),
            ('6%',  [u'Назначение'],        CReportBase.AlignLeft),
            ('5%',  [u'Номер'],             CReportBase.AlignLeft),
            ('3%',  [u'Проход'],            CReportBase.AlignLeft),
            ('4%',  [u'Очередь'],           CReportBase.AlignLeft),
            ('6%',  [u'Состояние'],         CReportBase.AlignLeft),
            ('6%',  [u'Дата и время'],      CReportBase.AlignLeft),
            ('14%', [u'Ф.И.О.'],            CReportBase.AlignLeft),
            ('2%',  [u'Пол'],               CReportBase.AlignLeft),
            ('5%',  [u'Дата рождения'],     CReportBase.AlignLeft),
            ('14%', [u'Тип действия'],      CReportBase.AlignLeft),
            ('8%',  [u'Отделение'],         CReportBase.AlignLeft),
            ('12%', [u'Назначил'],          CReportBase.AlignLeft),
            ('4%',  [u'Отметка'],           CReportBase.AlignLeft),
            ('10%', [u'Примечание'],        CReportBase.AlignLeft),
        ]

        table = createTable(cursor, tableColumns)
        queryTable, cond, order = self.prepareQueryParts(self.filter)
        db = QtGui.qApp.db
        records = db.getRecordList(queryTable,
                                   ['Job_Ticket.id', 'Job_Ticket.datetime', 'Job_Ticket.idx',
                                   'Job_Ticket.pass', 'Job_Ticket.status',
                                    'Client.lastName', 'Client.firstName', 'Client.patrName',
                                    'Client.sex', 'Client.birthDate',
                                    'ActionType.name AS actionTypeName',
                                    'vrbPersonWithSpeciality.name AS setPersonName',
                                    'Job_Ticket.label', 'Job_Ticket.note',
                                    'rbJobPurpose.code AS jobPurposeCode',
                                    'OrgStructure.name AS os_name', 'Action.endDate'
                                    ],
                                   cond, order)
        prevTicketId = False
        ticketStartRow = 0
        lineNo = 0
        for record in records:
            ticketId = forceRef(record.value('id'))
            ticketIdx = forceInt(record.value('idx')) + 1
            passInt = forceInt(record.value('pass'))
            status = forceInt(record.value('status'))
            datetime = forceString(record.value('datetime'))
            name = formatName(record.value('lastName'),
                              record.value('firstName'),
                              record.value('patrName'))
            sex = formatSex(forceInt(record.value('sex')))
            birthDate = forceString(record.value('birthDate'))
            endDate = forceString(record.value('endDate'))
            os_name = forceString(record.value('os_name'))
            actionTypeName = forceString(record.value('actionTypeName'))
            setPersonName = forceString(record.value('setPersonName'))
            label = forceString(record.value('label'))
            note = forceString(record.value('note'))
            jobPurposeCode = forceString(record.value('jobPurposeCode'))
            i = table.addRow()
            if prevTicketId == ticketId:
                table.mergeCells(ticketStartRow, 0, i - ticketStartRow + 1, 1)
                table.mergeCells(ticketStartRow, 1, i - ticketStartRow + 1, 1)
                table.mergeCells(ticketStartRow, 2, i - ticketStartRow + 1, 1)
                table.mergeCells(ticketStartRow, 3, i - ticketStartRow + 1, 1)
                table.mergeCells(ticketStartRow, 4, i - ticketStartRow + 1, 1)
                table.mergeCells(ticketStartRow, 5, i - ticketStartRow + 1, 1)
                table.mergeCells(ticketStartRow, 6, i - ticketStartRow + 1, 1)
                table.mergeCells(ticketStartRow, 7, i - ticketStartRow + 1, 1)
                table.setText(i, 10, actionTypeName)
                table.setText(i, 11, os_name)
                table.setText(i, 12, setPersonName)
                table.mergeCells(ticketStartRow, 8,  i-ticketStartRow+1, 1)
                table.mergeCells(ticketStartRow, 9, i-ticketStartRow+1, 1)
                table.mergeCells(ticketStartRow, 13, i - ticketStartRow + 1, 1)
            else:
                prevTicketId = ticketId
                ticketStartRow = i
                lineNo += 1
                table.setText(i, 0, lineNo)
                table.setText(i, 1, jobPurposeCode)
                table.setText(i, 2, ticketId)
                table.setText(i, 3, passInt)
                table.setText(i, 4, ticketIdx)
                table.setText(i, 5, CJobTicketStatus.names[status])
                table.setText(i, 6, datetime)
                table.setText(i, 7, name)
                table.setText(i, 8, sex)
                table.setText(i, 9, birthDate)
                table.setText(i, 10, actionTypeName)
                table.setText(i, 11, os_name)
                table.setText(i, 12, setPersonName)
                table.setText(i, 13,label)
                table.setText(i, 14,note)
        view = CReportViewDialog(self)
        view.setText(doc)
        view.exec_()


    @pyqtSignature('int')
    def on_actJobTicketListPrint_printByTemplate(self, templateId):
        jobTicketsIdList = self.modelJobTickets.idList()
        selectedJobTicketsIdList = self.tblJobTickets.selectedItemIdList()
        makeDependentActionIdList(jobTicketsIdList)
        context = CInfoContext()
        jobTicketsInfoList = context.getInstance(CJobTicketsWithActionsInfoList, tuple(jobTicketsIdList))
        selectedJobTicketsInfoList = context.getInstance(CJobTicketsWithActionsInfoList, tuple(selectedJobTicketsIdList))
        filter = {}
        filter['begDate'] = CDateInfo(self.filter['begDate'])
        filter['endDate'] = CDateInfo(self.filter['endDate'])
        filter['jobTypeList'] = [context.getInstance(CJobTypeInfo, id) for id in self.filter['jobTypeIdList']]
        for key in ('awaiting', 'enqueued', 'inProgress', 'done', 'onlyUrgent', 'ageFrom', 'ageTo'):
            filter[key] = self.filter[key]
        filter['orgStructure'] = context.getInstance(COrgStructureInfo, self.filter['orgStructureId'])
        filter['speciality'] = context.getInstance(CSpecialityInfo, self.filter['specialityId'])
        filter['person'] = context.getInstance(CPersonInfo, self.filter['setPersonId'])
        filter['sex'] = formatSex(self.filter['sex'])
        data = { 'jobTickets' : jobTicketsInfoList,
                 'selectedJobTickets' : selectedJobTicketsInfoList,
                 'filter': filter
               }
        applyTemplate(self, templateId, data)



    @pyqtSignature('int')
    def on_actActionPrint_printByTemplate(self, templateId):
        context = CInfoContext()
        index = self.tblJobTickets.currentIndex()
        if not index.isValid():
            return
        row = index.row()
        actionId = self.modelJobTickets.getActionId(row)
        QtGui.qApp.setWaitCursor()

        actionRecord = QtGui.qApp.db.getRecord('Action', '*', actionId)
        eventId = forceRef(actionRecord.value('event_id'))
        eventInfo = context.getInstance(CEventInfo, eventId)
        actionInfo = context.getInstance(CActionInfo, actionId)

        eventActions = eventInfo.actions
#        eventActions._idList = [actionId]
#        eventActions._items  = [CCookedActionInfo(context, actionRecord, CAction(record=actionRecord))]
#        eventActions._loaded = True

        action = eventInfo.actions[0]
        data = { 'event' : eventInfo,
                 'action': actionInfo,
                 'client': eventInfo.client,
                 'actions':eventActions,
                 'currentActionIndex': 0,
                 'tempInvalid': None
               }
        QtGui.qApp.restoreOverrideCursor()
        applyTemplate(self, templateId, data)


class CJobTypesModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent,  [
            CTextCol(u'Код',          ['code'],  6),
            CTextCol(u'Наименование', ['name'], 20),
            ], 'rbJobType' )
        self.parentWidget = parent


class CJobTicketsModel(CTableModel):

    class CLocNumberCol(CIntCol):
        def format(self, values):
#            record = values[1]
            return toVariant(forceInt(values[0])+1)

    class CLocJobPurposeColumn(CRefBookCol):
        def __init__(self, *args, **kwargs):
            CRefBookCol.__init__(self, *args, **kwargs)
            self._cache = {}

        def format(self, values):
            jobId = forceRef(values[0])
            if jobId:
                if jobId not in self._cache:

                    db = QtGui.qApp.db
                    tableJob = db.table('Job')
                    tableJobPurpose = db.table('rbJobPurpose')
                    queryTable = tableJob.innerJoin(tableJobPurpose, tableJobPurpose['id'].eq(tableJob['jobPurpose_id']))
                    record = db.getRecordEx(queryTable, [tableJobPurpose['code']], [tableJob['deleted'].eq(0), tableJob['id'].eq(jobId)])
                    if record:
                        result = toVariant(record.value('code'))
                    else:
                        result = CCol.invalid

                    self._cache[jobId] = result

                return self._cache[jobId]
            else:
                return CCol.invalid

        def clearCache(self):
            self._cache = {}

    class CEventExternalIdCol(CCol):
        def __init__(self):
            CCol.__init__(self, u'Номер документа', ['id'], 10, alignment='l', defaultHidden=True)
            self._cache = {}

        def format(self, values):
            record = values[1]
            jobTicket = CJobTicket(record)
            if not jobTicket.id in self._cache:
                eventExternalIdList = jobTicket.getEventExternalIdList()
                result = ', '.join(eventExternalIdList)
                self._cache[jobTicket.id] = toVariant(result)
            return self._cache[jobTicket.id]

        def clearCache(self):
            self._cache = {}

    def __init__(self, parent):
#        fieldList = ['event_id', 'visit_id', 'action_id', 'service_id']
        clientCol   = CLocClientColumn( u'Ф.И.О.',      ['id'], 20)
        self.clientCol = clientCol
        clientSexCol = CLocClientSexColumn(             u'Пол', ['id'],           3, clientCol)
        clientBirthDateCol = CLocClientBirthDateColumn( u'Дата рожд.', ['id'],   10, clientCol)
        self._jobPurposeCol = CJobTicketsModel.CLocJobPurposeColumn(u'Назначение',   ['master_id'], 'Job', 10)
        self._eventExternalIdCol = self.CEventExternalIdCol()
        self._takenTissueJournal = CLocTakenTissueJournalColumn(u'ИБМ', ['id'], 10)
        self.actionTypeCol = CLocActionTypeColumn(u'Тип действия', ['id'], 20, clientCol)
        CTableModel.__init__(self, parent, [
            self._takenTissueJournal,
            self._jobPurposeCol,
            self.actionTypeCol,
            CTextCol(u'Номер',                         ['id'],                                     10),
            CTextCol(u'Проход',                        ['pass'],                                   10),
            CJobTicketsModel.CLocNumberCol(u'Очередь', ['idx'],                                    10),
            CEnumCol(u'Состояние', ['status'],         [u'ожидание', u'выполнение', u'закончено', u'в очереди'], 5),
            CDateTimeCol(u'Начало работы',             ['begDateTime'],                            10),
            CDateTimeCol(u'Дата и время',              ['datetime'],                               10),
            clientCol,
            clientSexCol,
            clientBirthDateCol,
            CTextCol(u'Отметка',                       ['label'],                                  20),
            CRefBookCol(u'Подразделение',              ['orgStructure_id'], 'OrgStructure',        20),
            CTextCol(u'Примечание',                    ['note'],                                   20),
            self._eventExternalIdCol
            ])
        self.loadField('isExceedQuantity')
        self.setTable('Job_Ticket')


    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        if role == Qt.FontRole:
            row = index.row()
            actionId = self.getActionId(row)
            eventId = self.getActionEventId(actionId)
            if self.isClientInReanimation(eventId):
                result = QtGui.QFont()
                result.setBold(True)
                result.setItalic(True)
                return QVariant(result)
        else:
            return CTableModel.data(self, index, role)


    def setIdList(self, *args, **kwargs):
        self._jobPurposeCol.clearCache()
        self._eventExternalIdCol.clearCache()
        CTableModel.setIdList(self, *args, **kwargs)

    def getIdByRow(self, row):
        return self._idList[row] if row < len(self._idList) else None


    def getClientIdByRow(self, row):
        ticketId = self.getIdByRow(row)
        return self.getClientId(ticketId)


    def getClientId(self, ticketId):
        return self.clientCol.getClientId(ticketId)


    def isClientInReanimation(self, eventId):
        return self.clientCol.isClientInReanimation(eventId)


    def getActionId(self, row):
        ticketId = self.getIdByRow(row)
        return self.clientCol.getActionId(ticketId)


    def getActionEventId(self, actionId):
        return self.clientCol.getActionEventId(actionId)


    def getStatus(self, row):
        if row >= 0:
            ticketId = self.getIdByRow(row)
            if ticketId:
                record = self._recordsCache.get(ticketId)
                if record:
                    return forceInt(record.value('status'))
        return -1


    def getPass(self, row):
        ticketId = self.getIdByRow(row)
        if ticketId:
            record = self._recordsCache.get(ticketId)
            if record:
                return forceInt(record.value('pass'))
        return -1


class CLocClientColumn(CCol):
    def __init__(self, title, fields, defaultWidth):
        CCol.__init__(self, title, fields, defaultWidth, 'l')
        db = QtGui.qApp.db
        self.mapTicketIdToActionPropertyId = {}
        self.mapEventIdReanimation = {}
        self.APCache         = CTableRecordCache(db, 'ActionProperty', 'action_id')
        self.actionCache     = CTableRecordCache(db, 'Action', 'actionType_id, event_id, setPerson_id')
        self.actionTypeCache = CTableRecordCache(db, 'ActionType', 'name')
        self.eventCache      = CTableRecordCache(db, 'Event', 'client_id')
        self.personCache     = CTableRecordCache(db, 'vrbPersonWithSpeciality', 'name')
        self.clientCache     = CTableRecordCache(db, 'Client', 'firstName, lastName, patrName, birthDate, sex')


    def getActionRecord(self, ticketId):
        actionId = self.getActionId(ticketId)
        return self.actionCache.get(actionId) if actionId else None


    def getActionEventId(self, actionId):
        actionRecord = self.actionCache.get(actionId) if actionId else None
        if actionRecord:
            return forceRef(actionRecord.value('event_id')) if actionRecord else None
        return None


    def getActionId(self, ticketId):
        actionPropertyId = self.mapTicketIdToActionPropertyId.get(ticketId, -1)
        if actionPropertyId == -1:
            db = QtGui.qApp.db
            actionPropertyIdList = db.getDistinctIdList('ActionProperty_Job_Ticket', where='value=%d'%ticketId)
            for actionPropertyId in actionPropertyIdList:
                actionPropertyRecord = self.APCache.get(actionPropertyId) if actionPropertyId else None
                actionId = forceRef(actionPropertyRecord.value('action_id')) if actionPropertyRecord else None
                eventId = self.getActionEventId(actionId)
                if not eventId:
                    continue

                self.mapTicketIdToActionPropertyId[ticketId] = actionPropertyId
                break

        record = self.APCache.get(actionPropertyId) if actionPropertyId else None
        return forceRef(record.value('action_id')) if record else None


    def getClientRecord(self, ticketId):
        clientId = self.getClientId(ticketId)
        return self.clientCache.get(clientId) if clientId else None


    def getClientId(self, ticketId):
        record   = self.getActionRecord(ticketId)
        eventId  = forceRef(record.value('event_id')) if record else None
        record   = self.eventCache.get(eventId)
        clientId = forceRef(record.value('client_id')) if record else None
        return clientId


    def isClientInReanimation(self, eventId):
        result = self.mapEventIdReanimation.get(eventId, -1)
        if result == -1:
            stmt = u"""SELECT A.id
                      FROM Action AS A
                      INNER JOIN ActionType AS AT ON AT.id = A.actionType_id
                      WHERE A.event_id = {eventId} AND A.deleted = 0
                      AND AT.serviceType = 9 AND AT.deleted = 0
                      AND A.endDate IS NULL""".format(eventId=eventId)
            query = QtGui.qApp.db.query(stmt)
            result = query.size() > 0
            self.mapEventIdReanimation[eventId] = result
        return result


    def format(self, values):
        ticketId = forceRef(values[0])
        record = self.getClientRecord(ticketId)
        if record:
            name  = formatName(record.value('lastName'),
                               record.value('firstName'),
                               record.value('patrName'))
            return toVariant(name)
        else:
            return CCol.invalid


    def invalidateRecordsCache(self):
        self.mapTicketIdToActionPropertyId = {}
        self.APCache.invalidate()
        self.actionCache.invalidate()
        self.actionTypeCache.invalidate()
        self.eventCache.invalidate()
        self.personCache.invalidate()
        self.clientCache.invalidate()


class CLocTakenTissueJournalColumn(CCol):
    def __init__(self, title, fields, defaultWidth):
        CCol.__init__(self, title, fields, defaultWidth, 'l')
        db = QtGui.qApp.db
        self.mapTicketIdToActionPropertyId = {}
        self.APCache         = CTableRecordCache(db, 'ActionProperty', 'action_id')
        self.actionCache     = CTableRecordCache(db, 'Action', 'takenTissueJournal_id, actionType_id, event_id, setPerson_id')
        self.actionTypeCache = CTableRecordCache(db, 'ActionType', 'name')
        self.takenTissueJournalCache = CTableRecordCache(db, 'TakenTissueJournal', 'externalId')
        self.eventCache      = CTableRecordCache(db, 'Event', 'client_id')
        self.personCache     = CTableRecordCache(db, 'vrbPersonWithSpeciality', 'name')
        self.clientCache     = CTableRecordCache(db, 'Client', 'firstName, lastName, patrName, birthDate, sex')


    def getActionRecord(self, ticketId):
        actionId = self.getActionId(ticketId)
        return self.actionCache.get(actionId) if actionId else None


    def getActionEventId(self, actionId):
        actionRecord = self.actionCache.get(actionId) if actionId else None
        if actionRecord:
            return forceRef(actionRecord.value('event_id')) if actionRecord else None
        return None


    def getActionId(self, ticketId):
        actionPropertyId = self.mapTicketIdToActionPropertyId.get(ticketId, -1)
        if actionPropertyId == -1:
            db = QtGui.qApp.db
            actionPropertyIdList = db.getDistinctIdList('ActionProperty_Job_Ticket', where='value=%d'%ticketId)
            for actionPropertyId in actionPropertyIdList:
                actionPropertyRecord = self.APCache.get(actionPropertyId) if actionPropertyId else None
                actionId = forceRef(actionPropertyRecord.value('action_id')) if actionPropertyRecord else None
                eventId = self.getActionEventId(actionId)
                if not eventId:
                    continue

                self.mapTicketIdToActionPropertyId[ticketId] = actionPropertyId
                break

        record = self.APCache.get(actionPropertyId) if actionPropertyId else None
        return forceRef(record.value('action_id')) if record else None


    def getTakenTissueJournalRecord(self, ticketId):
        takenTissueJournalId = self.gettakenTissueJournalId(ticketId)
        return self.takenTissueJournalCache.get(takenTissueJournalId) if takenTissueJournalId else None


    def gettakenTissueJournalId(self, ticketId):
        record   = self.getActionRecord(ticketId)
        takenTissueJournalId = forceString(record.value('takenTissueJournal_id'))
        # eventId  = forceRef(record.value('event_id')) if record else None
        # record   = self.eventCache.get(eventId)
        # clientId = forceRef(record.value('client_id')) if record else None
        return takenTissueJournalId


    def format(self, values):
        ticketId = forceRef(values[0])
        record = self.getTakenTissueJournalRecord(ticketId)
        if record:
            externalId = forceString(record.value('externalId'))
            return toVariant(externalId)
        else:
            return CCol.invalid


    def invalidateRecordsCache(self):
        self.mapTicketIdToActionPropertyId = {}
        self.APCache.invalidate()
        self.actionCache.invalidate()
        self.actionTypeCache.invalidate()
        self.eventCache.invalidate()
        self.personCache.invalidate()
        self.clientCache.invalidate()

class CLocClientBirthDateColumn(CCol):
    def __init__(self, title, fields, defaultWidth, master):
        CCol.__init__(self, title, fields, defaultWidth, 'l')
        self.master = master


    def format(self, values):
        ticketId = forceRef(values[0])
        record = self.master.getClientRecord(ticketId)
        if record:
            return toVariant(forceString(record.value('birthDate')))
        else:
            return CCol.invalid


class CLocClientSexColumn(CCol):
    def __init__(self, title, fields, defaultWidth, master):
        CCol.__init__(self, title, fields, defaultWidth, 'l')
        self.master = master


    def format(self, values):
        ticketId = forceRef(values[0])
        record = self.master.getClientRecord(ticketId)
        if record:
            return toVariant(formatSex(record.value('sex')))
        else:
            return CCol.invalid


class CLocActionTypeColumn(CCol):
    def __init__(self, title, fields, defaultWidth, master):
        CCol.__init__(self, title, fields, defaultWidth, 'l')
        self.master = master


    def format(self, values):
        ticketId = forceRef(values[0])
        actionTypeId = self.getActionTypeId(ticketId)
        record = self.master.actionTypeCache.get(actionTypeId) if actionTypeId else None
        if record:
            return toVariant(forceString(record.value('name')))
        else:
            return CCol.invalid


    def getActionTypeId(self, ticketId):
        record = self.master.getActionRecord(ticketId) if ticketId else None
        return forceRef(record.value('actionType_id')) if record else None


class CLocPersonColumn(CCol):
    def __init__(self, title, fields, defaultWidth, master):
        CCol.__init__(self, title, fields, defaultWidth, 'l')
        self.master = master


    def format(self, values):
        ticketId = forceRef(values[0])
        record = self.master.getActionRecord(ticketId)
        setPersonId = forceRef(record.value('setPerson_id')) if record else None
        record = self.master.personCache.get(setPersonId) if setPersonId else None
        if record:
            return toVariant(forceString(record.value('name')))
        else:
            return CCol.invalid


def showJobTicketInfo(jobTicketId, widget):
    db = QtGui.qApp.db
    jobTicketRecord = db.getRecord('Job_Ticket', '*', jobTicketId)
    jobRecord = db.getRecord('Job', '*', jobTicketRecord.value('master_id'))

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

