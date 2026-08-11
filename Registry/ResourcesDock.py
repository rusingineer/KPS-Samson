# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2025 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

import math
from PyQt4 import QtGui
from PyQt4.QtCore import (
                          Qt,
                          pyqtSignature,
                          SIGNAL,
                          QAbstractTableModel,
                          QDate,
                          QDateTime,
                          QModelIndex,
                          QSize,
                          QTimer,
                          QVariant,
                          QSettings,
                         )

from Registry.ElQueueNumberDialog import CElQueueNumberDialog
from library.crbcombobox                  import CRBModelDataCache, CRBComboBox
from library.DialogBase                   import CConstructHelperMixin
from library.DockWidget       import CDockWidget
from library.PreferencesMixin             import CContainerPreferencesMixin, CPreferencesMixin
from library.PrintInfo                    import (
                                                  CDateInfo,
                                                  CInfo,
                                                  CInfoContext,
                                                  CTimeInfo,
                                                  CDateTimeInfo
                                                 )
from library.PrintTemplates   import getPrintAction, applyTemplate
from library.RecordLock       import CRecordLockMixin
from library.TreeModel                    import CTreeItemWithId, CTreeModel
from library.Utils                        import (
                                                  calcAgeTuple,
                                                  forceBool,
                                                  forceDate,
                                                  forceDouble,
                                                  forceInt,
                                                  forceRef,
                                                  forceString,
                                                  formatList,
                                                  formatTime,
                                                  getPref,
                                                  setPref,
                                                  toVariant,
                                                  forceDateTime
                                                 )

from Events.CreateEvent                   import requestNewEvent
from Events.Utils                         import getDeathDate
from Notifications.NotifyDialog import CNotifyDialog
from Notifications.NotificationRule import CNotificationRule
from Orgs.OrgPersonnel                    import COrgPersonnelModel, CFlatOrgPersonnelModel
from Orgs.OrgStructComboBoxes import COrgStructureModel
from Orgs.PersonInfo          import CPersonInfo
from Orgs.Utils                           import findOrgStructuresByAddress, getPersonInfo
from Registry.BeforeRecordClient          import CQueue, printOrderByScheduleItem
from Registry.ComplaintsEditDialog        import CComplaintsEditDialog
from Registry.ReferralEditDialog          import inputReferral, CReferral, CReferralEditDialog
from Registry.RegistrySuspenedAppointment import setRegistrySuspenedAppointment
from Registry.RegistryProphylaxisPlanning import setRegistryProphylaxisPlanningList
from Registry.ShowScheduleItemInfo import showScheduleItemInfo
from Registry.Utils                       import (
                                                  CAppointmentPurposeCache,
                                                  CCheckNetMixin,
                                                  CClientInfo,
                                                  getClientAddressEx,
                                                  getClientInfoEx,
                                                  getClientMiniInfo,
                                                  getClientInfo2,
                                                  getClientAttachEx,
                                                  createRelatedActionTMK
                                                 )
from Reports.ReportBase       import CReportBase, createTable
from Reports.ReportBeforeRecord           import CReportBeforeRecord
from Reports.ReportView       import CReportViewDialog
from RefBooks.AppointmentPurpose.Info     import CAppointmentPurposeInfo
from Timeline.Schedule import (
    CSchedule,
    CScheduleItem,
    confirmAndFreeScheduleItem,
    getScheduleItemIdListForClient, getScheduleItemIdFinance, getScheduleItemIdListForClient_OMS, getExceptionSpecialty
)
from Timeline.TimeTable                   import formatTimeRange
from Users.Rights import (
    urAdmin,
    urQueueCancelMaxDateLimit,
    urQueueCancelMinDateLimit,
    urQueueOverTime,
    urQueueToSelfOverTime,
    urRegTabWriteEvents,
    urSendInternalAmbNotifications,
    urQueueModifyCheck, urQueueingOutreaching
)

from Registry.Ui_ResourcesDockContent     import Ui_Form
from preferences.decor import CDecorDialog

# примечание 1:
#   при уменьшении количества строк в таблице при некоторых случаях
#   verticalHeader().updatesEnabled() остаётся False
#   эта ошибка наблюдается в Alt linux 6, причём в PyQt она есть, а в Qt - нет.
#   когда эта ошибка будет исправлена можно будет удалить строки с этой пометкой

class CResourcesDockWidget(CDockWidget):
    def __init__(self, parent):
        CDockWidget.__init__(self, parent)
        self.setWindowTitle(u'График')
        self.setFeatures(QtGui.QDockWidget.AllDockWidgetFeatures)
        self.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
        self.content = None
        self.contentPreferences = {}
        self.connect(QtGui.qApp, SIGNAL('dbConnectionChanged(bool)'), self.onConnectionChanged)


    def loadPreferences(self, preferences):
        self.contentPreferences = getPref(preferences, 'content', {})
        CDockWidget.loadPreferences(self, preferences)
        if isinstance(self.content, CPreferencesMixin):
            self.content.loadPreferences(self.contentPreferences)


    def savePreferences(self):
        result = CDockWidget.savePreferences(self)
        self.updateContentPreferences()
        setPref(result,'content',self.contentPreferences)
        return result


    def updateContentPreferences(self):
        if isinstance(self.content, CPreferencesMixin):
            self.contentPreferences = self.content.savePreferences()


    def onConnectionChanged(self, value):
        if value:
            self.onDBConnected()
        else:
            self.onDBDisconnected()


    def onDBConnected(self):
        self.setWidget(None)
        if self.content:
            self.content.setParent(None)
            self.content.deleteLater()
        self.content = CResourcesDockContent(self)
        self.content.loadPreferences(self.contentPreferences)
        self.setWidget(self.content)
        self.emit(SIGNAL('contentCreated(QDockWidget*)'), self)


    def onDBDisconnected(self):
        self.setWidget(None)
        if self.content:
            self.updateContentPreferences()
            self.content.setParent(None)
            self.content.deleteLater()
        self.content = QtGui.QLabel(u'необходимо\nподключение\nк базе данных', self)
        self.content.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.content.setDisabled(True)
        self.setWidget(self.content)
        self.emit(SIGNAL('contentDestroyed(QDockWidget*)'), self)


    def showQueueItem2(self, scheduleItemId):
        if isinstance(self.content, CResourcesDockContent):
            self.content.showQueueItem2(scheduleItemId)


    def setFilter(self, orgStructureId, specialityId, personId, begDate, appointmentType = None):
        if isinstance(self.content, CResourcesDockContent):
            self.content.showQueueItem(orgStructureId, specialityId, None, personId, begDate, None, appointmentType)


class CResourcesDockContent(QtGui.QWidget,
                            Ui_Form,
                            CConstructHelperMixin,
                            CContainerPreferencesMixin,
                            CCheckNetMixin,
                            CRecordLockMixin):

    ClearAndSelectRows = (  QtGui.QItemSelectionModel.ClearAndSelect
                          | QtGui.QItemSelectionModel.Rows
                         )

    __pyqtSignals__ = (
        'appointmentTypeChanged(int)',
    )

    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)
        CCheckNetMixin.__init__(self)
        CRecordLockMixin.__init__(self)

        application = QtGui.qApp
        self.groupingSpeciality  = forceBool(application.preferences.appPrefs.get('groupingSpeciality', True))
        self.activityListIsShown = forceBool(application.preferences.appPrefs.get('activityListIsShown', False))
        orgStructureFilter = None
        if QtGui.qApp.preferences.appPrefs.get('TimetableOrgStructureCheckedNames'):
            preferenceFilter = [forceInt(checkedId) for checkedId in QtGui.qApp.preferences.appPrefs.get('TimetableOrgStructureCheckedNames').toList()]
            if preferenceFilter:
                orgStructureFilter = 'OrgStructure.id NOT IN ({0})'.format(','.join(map(str, preferenceFilter)))

        self.addModels('OrgStructure',  COrgStructureModel(self, application.currentOrgId(), filter=orgStructureFilter))
        self.addModels('Activity',      CActivityModel(self))
        self.addModels('AmbTimeTable',  CTimeTableModel(self, CSchedule.atAmbulance))
        self.addModels('AmbQueue',      CQueueModel(self, CSchedule.atAmbulance))
        self.addModels('HomeTimeTable', CTimeTableModel(self, CSchedule.atHome))
        self.addModels('HomeQueue',     CQueueModel(self, CSchedule.atHome))

        self.addObject('actFindArea',       QtGui.QAction(u'Найти участок', self))
        self.addObject('actAmbCreateOrder', QtGui.QAction(u'Поставить в очередь', self))
        self.addObject('actAmbCreateOrderUrgent', QtGui.QAction(u'Поставить в очередь неотложно', self))
        self.addObject('actAmbCreateOrderTMK', QtGui.QAction(u'Поставить в очередь на ТМК', self))
        self.addObject('actAmbDeleteOrder', QtGui.QAction(u'Удалить из очереди', self))
        self.addObject('actAmbChangeComplaint', QtGui.QAction(u'Изменить жалобы', self))
        self.addObject('actAmbChangeReferral',  QtGui.QAction(u'Изменить данные направления', self))
        self.addObject('actAmbPrintOrder',  QtGui.QAction(u'Напечатать направление', self))
        self.addObject('actAmbPrintOrderByTemplate', getPrintAction(self, 'ambOrder', u'Напечатать направление по шаблону', False))
        self.addObject('actAmbPrintQueue',  QtGui.QAction(u'Напечатать полный список', self))
        self.addObject('actAmbPrintConfirmedQueue',  QtGui.QAction(u'Напечатать список подтвержденных записей', self))
        self.addObject('actAmbPrintUnconfirmedQueue',  QtGui.QAction(u'Напечатать список неподтвержденных записей', self))
        self.addObject('actAmbPrintPreRecordQueue',  QtGui.QAction(u'Напечатать список предварительной записи', self))
        self.addObject('actAmbPrintQueueByTemplate', getPrintAction(self, 'ambQueue', u'Напечатать список по шаблону', False))
        self.addObject('actAmbFindClient',  QtGui.QAction(u'Перейти в картотеку', self))
        self.addObject('actAmbFindClientEvents',  QtGui.QAction(u'Перейти на вкладку "Обращение"', self))
        self.addObject('actAmbCreateEvent', QtGui.QAction(u'Новое обращение', self))
        self.addObject('actAmbInviteClient', QtGui.QAction(u'Пригласить', self))
        self.addObject('actAmbCancelInvitation', QtGui.QAction(u'Отменить приглашение', self))
        self.addObject('actAmbNotification', QtGui.QAction(u'Сообщение по списку', self))
        self.addObject('actAmbInfo', QtGui.QAction(u'Свойства записи', self))

        self.addObject('actHomeCreateOrder',QtGui.QAction(u'Поставить в очередь', self))
        self.addObject('actHomeCreateOrderUrgent', QtGui.QAction(u'Поставить в очередь неотложно', self))
        self.addObject('actHomeDeleteOrder',QtGui.QAction(u'Удалить из очереди', self))
        self.addObject('actHomeChangeComplaint',QtGui.QAction(u'Изменить жалобы', self))
        self.addObject('actHomeChangeReferral', QtGui.QAction(u'Изменить данные направления', self))
        self.addObject('actHomePrintOrder', QtGui.QAction(u'Напечатать направление', self))
        self.addObject('actHomePrintOrderByTemplate', getPrintAction(self, 'homeOrder', u'Напечатать направление по шаблону', False))
        self.addObject('actHomePrintQueue', QtGui.QAction(u'Напечатать полный список', self))
        self.addObject('actHomePrintConfirmedQueue', QtGui.QAction(u'Напечатать список переданных врачу', self))
        self.addObject('actHomePrintUnconfirmedQueue', QtGui.QAction(u'Напечатать список непереданных врачу', self))
        self.addObject('actHomePrintQueueByTemplate', getPrintAction(self, 'homeQueue', u'Напечатать список по шаблону', False))
        self.addObject('actHomeFindClient', QtGui.QAction(u'Перейти в картотеку', self))
        self.addObject('actHomeFindClientEvents', QtGui.QAction(u'Перейти на вкладку "Обращение"', self))
        self.addObject('actHomeCreateEvent', QtGui.QAction(u'Новое обращение', self))
        self.addObject('actServiceReport', QtGui.QAction(u'Сводка об обслуживании', self))
        self.addObject('actHomeInfo', QtGui.QAction(u'Свойства записи', self))
        self.addObject('actRegistrySuspenedAppointment', QtGui.QAction(u'Зарегистрировать пациента в Журнале отложной записи', self))
        self.addObject('actRegistryProphylaxisPlanning', QtGui.QAction(u'Зарегистрировать пациента в Журнале планирования профилактического наблюдения', self))

        self.enableQueueing = False
        self.isNeededUpdateSchedulesForSelectedDate = False

        self.timer = QTimer(self)
        self.timer.setObjectName('timer')
        self.timer.setInterval(60*1000) # раз в минуту
        self.activityPref = application.getGlobalPreference('23')

        self.setupUi(self)
        for treeWidget in (self.treeOrgStructure, self.treeOrgPersonnel):
            treeWidget.setIndentation(12)
            treeWidget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        for tableWidget in (self.tblAmbTimeTable, self.tblAmbQueue, self.tblHomeTimeTable, self.tblHomeQueue):
            verticalHeader = tableWidget.verticalHeader()
            verticalHeader.show()
            verticalHeader.setResizeMode(QtGui.QHeaderView.Interactive)
        
        self.tblAmbTimeTable.setSelectionMode(self.tblAmbTimeTable.ExtendedSelection)
        self.tblHomeTimeTable.setSelectionMode(self.tblHomeTimeTable.ExtendedSelection)

        self.setModels(self.treeOrgStructure, self.modelOrgStructure, self.selectionModelOrgStructure)
        self.setModels(self.tblAmbTimeTable,  self.modelAmbTimeTable, self.selectionModelAmbTimeTable)
        self.setModels(self.tblAmbQueue,      self.modelAmbQueue,     self.selectionModelAmbQueue)
        self.setModels(self.tblHomeTimeTable, self.modelHomeTimeTable,self.selectionModelHomeTimeTable)
        self.setModels(self.tblHomeQueue,     self.modelHomeQueue,    self.selectionModelHomeQueue)

        # self.onTreePersonnelSectionClicked(0, False)

        self.tblHomeTimeTable.setColumnHidden(2, True)  # кабинет в вызовах на дом

        self.treeOrgStructure.createPopupMenu([self.actFindArea])
        self.treeOrgPersonnel.createPopupMenu([self.actRegistrySuspenedAppointment,
                                               self.actRegistryProphylaxisPlanning
                                              ]
                                             )
        self.tblAmbQueue.createPopupMenu([self.actAmbCreateOrder,
                                          self.actAmbCreateOrderUrgent,
                                          self.actAmbCreateOrderTMK,
                                          self.actAmbDeleteOrder,
                                          '-',
                                          self.actAmbChangeComplaint,
                                          self.actAmbChangeReferral,
                                          '-',
                                          self.actAmbPrintOrder,
                                          self.actAmbPrintOrderByTemplate,
                                          '-',
                                          self.actAmbPrintQueue,
                                          self.actAmbPrintConfirmedQueue,
                                          self.actAmbPrintUnconfirmedQueue,
                                          self.actAmbPrintPreRecordQueue,
                                          self.actAmbPrintQueueByTemplate,
                                          '-',
                                          self.actAmbFindClient,
                                          self.actAmbFindClientEvents, 
                                          self.actAmbCreateEvent,
                                          '-',
                                          self.actServiceReport,
                                          self.actAmbInfo,
                                          #self.actRegistrySuspenedAppointment,
                                          '-',
                                          self.actAmbInviteClient,
                                          self.actAmbCancelInvitation,
                                          '-',
                                          self.actAmbNotification])
        self.tblHomeQueue.createPopupMenu([self.actHomeCreateOrder,
                                          self.actHomeCreateOrderUrgent,
                                          self.actHomeDeleteOrder,
                                          '-',
                                          self.actHomeChangeComplaint,
                                          self.actHomeChangeReferral,
                                          '-',
                                          self.actHomePrintOrder,
                                          self.actHomePrintOrderByTemplate, 
                                          '-',
                                          self.actHomePrintQueue,
                                          self.actHomePrintConfirmedQueue,
                                          self.actHomePrintUnconfirmedQueue,
                                          self.actHomePrintQueueByTemplate,
                                          '-',
                                          self.actHomeFindClient,
                                          self.actHomeFindClientEvents,
                                          self.actHomeCreateEvent,
                                          '-',
                                          self.actServiceReport,
                                          self.actHomeInfo,
                                          #self.actRegistrySuspenedAppointment
                                          ]
                                          )

        self.connect(application, SIGNAL('currentOrgIdChanged()'), self.onCurrentOrgIdChanged)
        self.connect(application, SIGNAL('currentUserIdChanged()'), self.onCurrentUserIdChanged)
        # qApp.currentOrgIdChanged.connect(self.onCurrentOrgIdChanged)
        # qApp.currentUserIdChanged.connect(self.onCurrentUserIdChanged)

        self.treeOrgStructure.popupMenu().aboutToShow.connect(self.onTreeOrgStructurePopupMenuAboutToShow)

        self.selectionModelAmbTimeTable.currentRowChanged.connect( self.onSelectionModelAmbTimeTableCurrentRowChanged,
                                                                   type=Qt.QueuedConnection
                                                                 )

        self.selectionModelHomeTimeTable.currentRowChanged.connect( self.onSelectionModelHomeTimeTableCurrentRowChanged,
                                                                    type=Qt.QueuedConnection
                                                                  )

        treeOrgStructureHeader = self.treeOrgStructure.header()
        treeOrgStructureHeader.setClickable(True)
        treeOrgStructureHeader.sectionClicked.connect(self.onTreeOrgStructureHeaderClicked)

        self.treeOrgPersonnel.popupMenu().aboutToShow.connect(self.onTreeOrgPersonnelPopupMenuAboutToShow)
        treeOrgPersonnelHeader = self.treeOrgPersonnel.header()
        treeOrgPersonnelHeader.setClickable(True)
        treeOrgPersonnelHeader.sectionClicked.connect(self.onTreeOrgPersonnelHeaderClicked)

        self.prevClientId = None
        self.prevComplaint = ''

        self.onTreeOrgPersonnelHeaderClicked(0, False) # там создаются модели :(
        self.onTreeOrgStructureHeaderClicked(0, False)
        self.onCurrentUserIdChanged()

        self.tblHomeTimeTable.setColumnHidden(1,True) # кабинет в вызовах на дом

        self.postForMainLogicRecord = []
        self.postForInterofficeRecord = []

        self.timer.start()
        self.updateTimeTable()
        self.appointmentType = CSchedule.atAmbulance if self.tabPlace.currentIndex() == 0 else CSchedule.atHome
        for tableWidget in (self.tblAmbQueue, self.tblHomeQueue):
            self.loadSizeState(tableWidget)
        

    ######### утилиты

    def loadSizeState(self, tableWidget):
        tableSizeSettings = QSettings(QSettings.IniFormat, QSettings.UserScope, 'ResourcesDock')
        tableSize = tableSizeSettings.value("sizeOfHorizontal"+tableWidget.objectName(), "").toByteArray()
        tableWidget.horizontalHeader().restoreState(tableSize)
        tableSize = tableSizeSettings.value("sizeOfVertical"+tableWidget.objectName(), "").toByteArray()
        tableWidget.verticalHeader().restoreState(tableSize)    
    
    
    def closeEvent(self, event):
        for tableWidget in (self.tblAmbQueue, self.tblHomeQueue):
            tableSizeSettings = QSettings(QSettings.IniFormat, QSettings.UserScope, 'ResourcesDock')
            tableSize = tableWidget.horizontalHeader().saveState()
            tableSizeSettings.value("sizeOfHorizontal"+tableWidget.objectName(), tableSize)
            tableSize = tableWidget.verticalHeader().saveState()
            tableSizeSettings.setValue("sizeOfVertical"+tableWidget.objectName(), tableSize)
        event.accept()
        

    def sizeHint(self):
        return QSize(10, 10)


    def showQueueItem2(self, scheduleItemId):
        if scheduleItemId:
            db = QtGui.qApp.db
            record = db.getRecord('vScheduleItem', 'date, person_id, activity_id', scheduleItemId)
            if record:
                date = forceDate(record.value('date'))
                personId = forceRef(record.value('person_id'))
                if self.activityPref == u'да':
                    activityId = forceRef(record.value('activity_id'))
                    personRecord = db.getRecord('Person', 'orgStructure_id, speciality_id', personId)
                else:
                    tablePersonActivity = db.table('Person_Activity')
                    tablePerson = db.table('Person')
                    table = tablePerson.leftJoin(tablePersonActivity, tablePerson['id'].eq(tablePersonActivity['master_id']))
                    personRecord = db.getRecord(table, 'orgStructure_id, speciality_id, activity_id', personId)
                if personRecord:
                    orgStructureId = forceRef(personRecord.value('orgStructure_id'))
                    specialityId = forceRef(personRecord.value('speciality_id'))
                    if self.activityPref != u'да':
                        activityId = forceRef(personRecord.value('activity_id'))
                    self.showQueueItem(orgStructureId, specialityId, activityId, personId, date, scheduleItemId)


    def showQueueItem(self,
                      orgStructureId,
                      specialityId,
                      activityId,
                      personId,
                      date,
                      scheduleItemId,
                      appointmentType=None):
        self.setPersonEtc(orgStructureId, specialityId, activityId, personId)
        if date >= QDate.currentDate():
            self.calendarWidget.setSelectedDate(date)
        if scheduleItemId:
            self.selectScheduleItem(scheduleItemId)

        if appointmentType is not None:
            if appointmentType == CSchedule.atAmbulance:
                self.tabPlace.setCurrentIndex(0)
            elif appointmentType == CSchedule.atHome:
                self.tabPlace.setCurrentIndex(1)


    def setPersonEtc(self, orgStructureId, specialityId, activityId, personId):
        index = None
        if self.activityListIsShown and activityId:
            index = self.modelActivity.findItemId(activityId)
        else:
            if orgStructureId:
                index = self.modelOrgStructure.findItemId(orgStructureId)
        if index and index.isValid():
            self.treeOrgStructure.setCurrentIndex(index)
        if specialityId and personId:
            index = self.modelPersonnel.findPersonId(personId)
            if index and index.isValid():
                self.treeOrgPersonnel.setCurrentIndex(index)


    def selectScheduleItem(self, scheduleItemId):
        db = QtGui.qApp.db
        record = db.getRecord('vScheduleItem', 'appointmentType, master_id, idx', scheduleItemId)
        if record:
            appointmentType = forceInt(record.value('appointmentType'))
            scheduleId = forceRef(record.value('master_id'))

            if appointmentType == CSchedule.atAmbulance:
                self.tabPlace.setCurrentIndex(0)
            elif appointmentType == CSchedule.atHome:
                self.tabPlace.setCurrentIndex(1)

            self.updateTimeTable()
            place = self.tabPlace.currentIndex()
            if place == 0:
                tblTimeTable, tblQueue = self.tblAmbTimeTable, self.tblAmbQueue
            else:
                tblTimeTable, tblQueue = self.tblHomeTimeTable, self.tblHomeQueue

            scheduleRow = tblTimeTable.model().findRowForScheduleId(scheduleId)
            if scheduleRow>=0:
                tblTimeTable.selectRow(scheduleRow)
                tblQueue.selectRow(tblQueue.model().findScheduleItemRow(scheduleItemId))
                tblQueue.setFocus(Qt.OtherFocusReason)


    def filterStructureId(self, idList, topOrgStructureId):
        index = self.modelOrgStructure.findItemId(topOrgStructureId)
        childrenIdList = self.modelOrgStructure.getItemIdList(index)
        filteredList = list(set(childrenIdList).intersection(set(idList)))
        if filteredList:
            filteredList.sort()
            return filteredList[0]
        else:
            return None


    def getActivityId(self):
        if self.activityListIsShown and self.activityPref == u'да':
            treeIndex = self.treeOrgStructure.currentIndex()
            activityIdList = self.modelActivity.getItemIdList(treeIndex)
            return activityIdList[0] if activityIdList else None
        else:
            return None


    def getCurrentPersonId(self):
        treeIndex = self.treeOrgPersonnel.currentIndex()
        personIdList = self.modelPersonnel.getItemIdList(treeIndex)
        if personIdList and len(personIdList) == 1:
            return personIdList[0]
        else:
            return None
    
    
    def getCurrentSpecialityId(self):
        treeIndex = self.treeOrgPersonnel.currentIndex()
        personIdList = self.modelPersonnel.getItemIdList(treeIndex)
        if personIdList:
            personId = personIdList[0]
            if personId:
                return self.getPersonSpecialityId(personId)
        return None


    def getSpecialityExpandedStatus(self):
        def getStatusInternal(model, parent=QModelIndex(), prefix=''):
            for column in xrange(model.columnCount(parent)):
                for row in xrange(model.rowCount(parent)):
                    index = model.index(row, column,  parent)
                    if index.isValid():
                        prefix += index.internalPointer().name() + '_'
                        isExpanded = self.treeOrgPersonnel.isExpanded(index)
                        self.expandedItemsStatus[prefix] = isExpanded
                        if isExpanded:
                            getStatusInternal(model, index, prefix)
        self.expandedItemsStatus = {}
        getStatusInternal(self.modelPersonnel)


    def setSpecialityExpandedStatus(self):
        def setStatusInternal(model, parent=QModelIndex(), prefix=''):
            for column in xrange(model.columnCount(parent)):
                for row in xrange(model.rowCount(parent)):
                    index = model.index(row, column,  parent)
                    if index.isValid():
                        prefix += index.internalPointer().name() + '_'
                        isExpanded = self.expandedItemsStatus.get(prefix, False)
                        if isExpanded:
                            self.treeOrgPersonnel.setExpanded(index, isExpanded)
                            setStatusInternal(model, index, prefix)
        setStatusInternal(self.modelPersonnel)
        self.expandedItemsStatus.clear()


    def updatePersonnelByOrgStructure(self):
        self.getSpecialityExpandedStatus()
        personId = self.getCurrentPersonId()
        if self.groupingSpeciality and not personId:
            specialityId = self.getCurrentSpecialityId()
        treeIndex = self.treeOrgStructure.currentIndex()
        orgStructureIdList = self.modelOrgStructure.getItemIdList(treeIndex)
        date = self.getCurrentDate()
        self.modelPersonnel.setOrgStructureIdList(self.modelOrgStructure.orgId, orgStructureIdList, date)
        if self.modelOrgStructure.isLeaf(treeIndex):
            self.treeOrgPersonnel.expandAll()
            self.treeOrgPersonnel.setCurrentIndex(self.modelPersonnel.getFirstLeafIndex())
        index = self.modelPersonnel.findPersonId(personId)
        if index and index.isValid():
            self.treeOrgPersonnel.setCurrentIndex(index)
        if self.groupingSpeciality and not personId:
            index = self.modelPersonnel.findSpecialityId(specialityId)
            if index and index.isValid():
                self.treeOrgPersonnel.setCurrentIndex(index)
        self.updateTimeTable()
        self.setSpecialityExpandedStatus()
        if index and index.isValid():
            self.treeOrgPersonnel.scrollTo(index)


    def updatePersonnelByActivity(self):
        self.getSpecialityExpandedStatus()
        personId = self.getCurrentPersonId()
        if self.groupingSpeciality and not personId:
            specialityId = self.getCurrentSpecialityId()
        treeIndex = self.treeOrgStructure.currentIndex()
        activityIdList = self.modelActivity.getItemIdList(treeIndex)
        date = self.getCurrentDate()
        self.modelPersonnel.setActivityIdList(self.modelOrgStructure.orgId, activityIdList, date)
        if self.modelActivity.isLeaf(treeIndex):
            self.treeOrgPersonnel.expandAll()
            self.treeOrgPersonnel.setCurrentIndex(self.modelPersonnel.getFirstLeafIndex())
        index = self.modelPersonnel.findPersonId(personId)
        if index and index.isValid():
            self.treeOrgPersonnel.setCurrentIndex(index)
        if self.groupingSpeciality and not personId:
            index = self.modelPersonnel.findSpecialityId(specialityId)
            if index and index.isValid():
                self.treeOrgPersonnel.setCurrentIndex(index)
        self.updateTimeTable()
        self.setSpecialityExpandedStatus()
        if index and index.isValid():
            self.treeOrgPersonnel.scrollTo(index)


    def setCalendarDataRange(self):
        application = QtGui.qApp
        today = QDate.currentDate()
        if application.userHasRight(urQueueCancelMinDateLimit):
            minDate = today.addYears(-10)
        else:
            minDate = today.addDays(-7)
        queueCancelMaxDateLimit = application.userHasRight(urQueueCancelMaxDateLimit)
        if queueCancelMaxDateLimit:
            maxDate = today.addYears(10)
        else:
            maxDate = today.addMonths(2)
# это скверная мысль "рулить" датами в зависимости от врача -
# в зависимости от свойств врача это может сбивать дату в календаре.
# но к сожалению требуют - задача №0007142: Право пользователей queueCancelMaxDateLimit
#        personId = self.getCurrentPersonId()
#        if personId and QtGui.qApp.isTimelineAccessibilityDays() == 1:
#            db = QtGui.qApp.db
#            table = db.table('Person')
#            record = db.getRecordEx(table, [table['lastAccessibleTimelineDate'], table['timelineAccessibleDays']], [table['deleted'].eq(0), table['id'].eq(personId)])
#            if record:
#                lastAccessibleTimelineDate = forceDate(record.value('lastAccessibleTimelineDate'))
#                timelineAccessibleDays = forceInt(record.value('timelineAccessibleDays'))
#                if lastAccessibleTimelineDate:
#                    maxDate = lastAccessibleTimelineDate
#                if timelineAccessibleDays and not queueCancelMaxDateLimit:
#                    accessibleDays = today.addDays(timelineAccessibleDays-1)
#                    if lastAccessibleTimelineDate:
#                        maxDate = min(maxDate, accessibleDays)
#                    else:
#                        maxDate = accessibleDays
        self.calendarWidget.setDateRange(minDate, maxDate)


    def getCurrentDate(self):
        return self.calendarWidget.selectedDate()


    def updateTimeTable(self):
        self.timer.stop()
        try:
            self.setCalendarDataRange()

            place = self.tabPlace.currentIndex()
            if place == 0: # амбулаторно
                self.updateTimeTableEx(self.tblAmbTimeTable,
                                       self.modelAmbTimeTable,
                                       self.selectionModelAmbTimeTable,
                                       self.tblAmbQueue,
                                       self.modelAmbQueue
                                      )
            else: # place == 1: # на дому
                self.updateTimeTableEx(self.tblHomeTimeTable,
                                       self.modelHomeTimeTable,
                                       self.selectionModelHomeTimeTable,
                                       self.tblHomeQueue,
                                       self.modelHomeQueue
                                      )
        finally:
            self.timer.start()


    def updateTimeTableEx(self,
                          tblTimeTable,
                          modelTimeTable,
                          selectionModelTimeTable,
                          tblQueue,
                          modelQueue):
        personId = self.getCurrentPersonId()
        activityId = self.getActivityId()
        currentDate = self.getCurrentDate()
        minDate = self.calendarWidget.minimumDate()
        maxDate = self.calendarWidget.maximumDate()

        currentRow = tblTimeTable.currentIndex().row()
        modelTimeTable.setPersonActivityAndDate(personId, activityId, currentDate, minDate, maxDate)
        newCurrentRow = modelTimeTable.getRowForDate(currentDate, currentRow)
        if newCurrentRow>=0:
            self.updateTimeTableSelection(tblTimeTable,
                                          modelTimeTable,
                                          selectionModelTimeTable,
                                          tblQueue,
                                          modelQueue,
                                          newCurrentRow,
                                          currentRow
                                         )
            newCurrentIndex = modelTimeTable.index(newCurrentRow, 0)
            tblTimeTable.scrollTo(newCurrentIndex)
            selectionModelTimeTable.setCurrentIndex(newCurrentIndex,
                                                    selectionModelTimeTable.NoUpdate)
        else:
            self.clearTimeTableSelection(tblTimeTable,
                                         modelTimeTable,
                                         selectionModelTimeTable,
                                         tblQueue,
                                         modelQueue
                                        )
            invalidIndex = modelTimeTable.index(-1, 0)
            selectionModelTimeTable.setCurrentIndex(invalidIndex,
                                                    selectionModelTimeTable.NoUpdate)



#        tblTimeTable.setCurrentIndex(currentIndex)
#            self.selectInTimeTable(tblTimeTable, modelTimeTable, selectionModelTimeTable)
#            tblTimeTable.update()
#            tblTimeTable.scrollTo(currentIndex)
#        finally:
#            selectionModelTimeTable.blockSignals(bs)
#        self.updateQueueEx(tblTimeTable,
#                           modelTimeTable,
#                           selectionModelTimeTable,
#                           tblQueue,
#                           modelQueue)


    def updateTimeTableSelection(self,
                                tblTimeTable,
                                modelTimeTable,
                                selectionModelTimeTable,
                                tblQueue,
                                modelQueue,
                                currentRow,
                                previousRow):
            currentDate = modelTimeTable.getDate(currentRow)
            previousDate = modelTimeTable.getDate(previousRow)
            if currentDate != previousDate:
                rows = self.getCombinableRowsInTimeTable(modelTimeTable, currentRow)
                self.selectRowsInTimeTable(selectionModelTimeTable, rows)
                prevBlock = self.calendarWidget.blockSignals(True)
                try:
                    self.calendarWidget.setSelectedDate(currentDate)
                finally:
                    self.calendarWidget.blockSignals(prevBlock)
            self.updateQueueEx(tblTimeTable,
                               modelTimeTable,
                               selectionModelTimeTable,
                               tblQueue,
                               modelQueue
                              )


    def clearTimeTableSelection(self,
                                tblTimeTable,
                                modelTimeTable,
                                selectionModelTimeTable,
                                tblQueue,
                                modelQueue):
        self.selectRowsInTimeTable(selectionModelTimeTable, [])
        self.updateQueueEx(tblTimeTable,
                           modelTimeTable,
                           selectionModelTimeTable,
                           tblQueue,
                           tblQueue.model()
                          )


    def updateQueueEx(self,
                      tblTimeTable,
                      modelTimeTable,
                      selectionModelTimeTable,
                      tblQueue,
                      modelQueue
                     ):
        rows = self.getSelectedRowsInTimeTable(selectionModelTimeTable)
        personId = self.getCurrentPersonId()
        if self.isRightMaxDateLimit(personId):
            schedules = [ modelTimeTable.schedules[row] for row in rows ]
        else:
            schedules = []
        modelQueue.setSchedules(schedules)
        self.enableQueueing = False
        if personId:
            for schedule in schedules:
                if (    schedule.reasonOfAbsenceId is None
                    and isAppointmentEnabled(schedule.appointmentPurposeId, personId)
                   ):
                    self.enableQueueing = True
                    break
                elif schedule.reasonOfAbsenceId is None:
                    for scheduleItem in schedule.items:
                        if not self.enableQueueing and scheduleItem.enableQueueing:
                            self.enableQueueing = True
                            break
        tblQueue.setEnabled(modelQueue.rowCount()>0)


    def isRightMaxDateLimit(self, personId): # Переименовать
        if personId and QtGui.qApp.isTimelineAccessibilityDays() == 1: # Переименовать
            date = self.getCurrentDate()
            today = QDate.currentDate()
            queueCancelMaxDateLimit = QtGui.qApp.userHasRight(urQueueCancelMaxDateLimit)
            if queueCancelMaxDateLimit:
                maxDate = today.addYears(10)
            else:
                maxDate = today.addDays(7)
            db = QtGui.qApp.db
            table = db.table('Person')
            record = db.getRecordEx(table,
                                    [ table['lastAccessibleTimelineDate'],
                                      table['timelineAccessibleDays']
                                    ],
                                    [table['deleted'].eq(0),
                                     table['id'].eq(personId)
                                    ])
            if record:
                lastAccessibleTimelineDate = forceDate(record.value('lastAccessibleTimelineDate'))
                timelineAccessibleDays = forceInt(record.value('timelineAccessibleDays'))
                if lastAccessibleTimelineDate:
                    maxDate = lastAccessibleTimelineDate
                if timelineAccessibleDays and not queueCancelMaxDateLimit:
                    accessibleDays = today.addDays(timelineAccessibleDays-1)
                    if lastAccessibleTimelineDate:
                        maxDate = min(maxDate, accessibleDays)
                    else:
                        maxDate = accessibleDays
            return maxDate >= date
        return True


    def getSelectedRowsInTimeTable(self, selectionModelTimeTable):
        return sorted([index.row()
                       for index in selectionModelTimeTable.selectedRows()
                      ]
                     )


    def getCombinableRowsInTimeTable(self, modelTimeTable, row):
        timeTableCombinationRule = QtGui.qApp.combineTimetable() # плохое название getTimeTableCombinationRule?
        if timeTableCombinationRule == 0:
            return [row]
        else:
            return modelTimeTable.getCombinableRows(row, timeTableCombinationRule==1)


    def selectRowsInTimeTable(self, selectionModelTimeTable, rows):
        model = selectionModelTimeTable.model()
        indexes = QtGui.QItemSelection()
        for row in rows:
            indexes.append(QtGui.QItemSelectionRange(model.index(row, 0)))
        selectionModelTimeTable.select(QtGui.QItemSelection(indexes), self.ClearAndSelectRows)


    def popupMenuAboutToShow(self,
                             tblQueue,
                             actCreateOrder,
                             actCreateOrderUrgent,
                             actCreateOrderTMK,
                             actDeleteOrder,
                             actChangeComplaint,
                             actChangeReferral,
                             actPrintOrder,
                             actPrintOrderByTemplate,
                             actPrintQueue,
                             actPrintConfirmedQueue,
                             actPrintUnconfirmedQueue,
                             actPrintQueueByTemplate,
                             actFindClient,
                             actFindClientEvents,
                             actCreateEvent,
                             actServiceReport,
                             actInfo,
                             actAmbInviteClient = None,
                             actAmbCancelInvitation = None
                             ):
        modelQueue = tblQueue.model()
        currentRow = tblQueue.currentIndex().row()
        itemPresent = 0<=currentRow<modelQueue.rowCount()
        orderPresent = bool(modelQueue.getClientId(currentRow))
        anyOrderPresent = bool(modelQueue.getQueuedClientsCount()) # плохо

        canFindClient  = QtGui.qApp.canFindClient()
        currentClientId = QtGui.qApp.currentClientId()
        deathDate = getDeathDate(currentClientId)

        variantPrintQueue = QtGui.qApp.ambulanceUserCheckable()
        clientIsInvited = modelQueue.getInvitation(currentRow)

        overlapItem = False

        if 0<=currentRow<len(modelQueue.scheduleItems):
            isEnableQueueingForItem = modelQueue.scheduleItems[currentRow].enableQueueing
        else:
            isEnableQueueingForItem = self.enableQueueing
            overlapItem = True

        actCreateOrder.setEnabled(bool(currentClientId)
                                  and itemPresent
                                  and not orderPresent
                                  and (self.enableQueueing and isEnableQueueingForItem)
                                  and not deathDate)
        actCreateOrderUrgent.setEnabled(bool(currentClientId)
                                  and itemPresent
                                  and not orderPresent
                                  and (self.enableQueueing and isEnableQueueingForItem)
                                  and not deathDate)
        actCreateOrderTMK.setEnabled(bool(currentClientId)
                                  and itemPresent
                                  and not orderPresent
                                  and (self.enableQueueing and isEnableQueueingForItem)
                                  and not deathDate
                                  and canFindClient and bool(currentClientId)
                                  and not overlapItem)
        actDeleteOrder.setEnabled(orderPresent)
        actChangeComplaint.setEnabled(orderPresent)
        actChangeReferral.setEnabled(orderPresent)
        actPrintOrder.setEnabled(orderPresent)
        if actPrintOrderByTemplate:
            actPrintOrderByTemplate.setEnabled(orderPresent)
        actPrintQueue.setEnabled(anyOrderPresent)
        if tblQueue == self.tblAmbQueue:
            actPrintConfirmedQueue.setEnabled(anyOrderPresent and variantPrintQueue)
            actPrintUnconfirmedQueue.setEnabled(anyOrderPresent and variantPrintQueue)
        else:
            actPrintConfirmedQueue.setEnabled(anyOrderPresent)
            actPrintUnconfirmedQueue.setEnabled(anyOrderPresent)
        actPrintQueueByTemplate.setEnabled(anyOrderPresent)
        actFindClient.setEnabled(canFindClient and bool(currentClientId))
        actCreateEvent.setEnabled(itemPresent
                                  and orderPresent
                                  and bool(currentClientId)
                                  and QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteEvents]))
        actServiceReport.setEnabled(anyOrderPresent)
        actInfo.setEnabled(itemPresent and orderPresent)
        if actAmbInviteClient:
            actAmbInviteClient.setEnabled(orderPresent and not clientIsInvited)
        if actAmbCancelInvitation:
            actAmbCancelInvitation.setEnabled(orderPresent and clientIsInvited)


    def getQueuedClientsCount(self, tblQueue):
        return tblQueue.model().getQueuedClientsCount()


    def queueingEnabled(self, date, orgStructureId, specialityId, activityId, personId, schedule, tblQueue, row, clientId, appointmentPurposeId, scheduleItem=None):
        modelQueue = tblQueue.model()
        if modelQueue.getClientId(row):
            return False  # кто-то уже записан
        deathDate = getDeathDate(clientId)
        if deathDate:
            QtGui.QMessageBox.warning(self, u'Внимание!', u'Этот пациент не может быть записан к врачу, потому что есть отметка что он уже умер %s' % forceString(deathDate))
            return False

        # appointmentPurposeId = modelQueue.schedule.appointmentPurposeId
        if not isAppointmentEnabledForClient(appointmentPurposeId, personId, date, clientId):
            QtGui.QMessageBox.warning(self, u'Внимание!', u'Назначение приёма препятствует записи пациента')
            return False

        if scheduleItem and not QtGui.qApp.isReStagingInQueue() and not isAppointmentEnabledForDate(scheduleItem, personId):
            personInfo = getPersonInfo(personId)
            if QtGui.qApp.userId == personId:
                QtGui.QMessageBox.warning(self, u'Не удалось выполнить запись.',
                                          u'Запись на КТ разрешена только на 14 дней')
            else:
                QtGui.QMessageBox.warning(self, u'Не удалось выполнить запись.',
                                          u'Запись на ' + scheduleItem.time.toString(
                                              'dd.MM.yyyy HH:mm') + u' разрешена только для врача ' + personInfo[
                                              'shortName'])
            return False

        if not checkInterofficeRecord(self, personId, scheduleItem):
            return False

        scheduleItemIdList = getScheduleItemIdListForClient(clientId, specialityId, date, modelQueue.appointmentType)
        if scheduleItemIdList:
            scheduleItemIdList_OMS = getScheduleItemIdListForClient_OMS(scheduleItemIdList)
            exceptionSpecialty = getExceptionSpecialty(specialityId)
            checkFinance = None
            if scheduleItem and scheduleItem.appointmentPurposeId:
                recordFinance = getScheduleItemIdFinance(scheduleItem)
                if recordFinance:
                    checkFinance = forceString(recordFinance.value('code'))
                else:
                    checkFinance = None
            if QtGui.qApp.isReStagingInQueue() or (checkFinance and checkFinance != '2') or not scheduleItemIdList_OMS or exceptionSpecialty == 1 or modelQueue.appointmentType == 2:  # Повторная постановка в очередь(да, нет)
                textMessage = u'Этот пациент уже записан к врачу этой специальности\nПодтвердите повторную запись'
            else:
                textMessage = u'Этот пациент уже записан к врачу этой специальности'
            messageBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning, u'Внимание!', textMessage)
            messageBox.setWindowFlags(messageBox.windowFlags() | Qt.WindowStaysOnTopHint)
            messageBox.addButton(u'Отмена', QtGui.QMessageBox.NoRole)
            messageBox.setDefaultButton(messageBox.addButton(u'Просмотр', QtGui.QMessageBox.ActionRole))
            if QtGui.qApp.isReStagingInQueue() or (checkFinance and checkFinance != '2') or not scheduleItemIdList_OMS or exceptionSpecialty == 1 or modelQueue.appointmentType == 2:
                messageBox.addButton(u'Ок', QtGui.QMessageBox.YesRole)
            confirmation = messageBox.exec_()
            if not QtGui.qApp.isReStagingInQueue() or not checkFinance or checkFinance == '2':  # Повторная постановка в очередь(да, нет)
                confirmation += 1
            if confirmation == 1:
                return False
            if confirmation == 2:  # просмотр
                place = self.tabPlace.currentIndex()
                result = CQueue(self, clientId, scheduleItemIdList, QtGui.qApp.isReStagingInQueue()).exec_()
                if not result:
                    return False
                self.tabPlace.setCurrentIndex(place)
                self.showQueueItem(orgStructureId, specialityId, activityId, personId, date, None)  # при некоторых условиях это не будет работать
                tblQueue.selectRow(row)

        if not (modelQueue.overtimeEnabled and modelQueue.getTime(row).isNull()):
            capacity = schedule.getCapacityAppointmentPurpose(appointmentPurposeId, personId)
            quota = getQuota(personId, capacity)
            queued = modelQueue.getQueuedCount(row)
            if quota <= queued:
                message = u'Квота на запись исчерпана!'
                if QtGui.qApp.userHasRight(urQueueingOutreaching):
                    message += u'\nВсё равно продолжить?'
                    buttons = QtGui.QMessageBox.Yes | QtGui.QMessageBox.No
                else:
                    buttons = QtGui.QMessageBox.Ok
                if QtGui.QMessageBox.critical(self,
                                                  u'Внимание!',
                                                  message,
                                                  buttons) != QtGui.QMessageBox.Yes:
                    return False
        return True


    def createOrder(self, tblTimeTable, tblQueue, clientId, isUrgent=0, recordType=None, idx=None):
        def fillScheduleItem(scheduleItem, clientId, complaint, referral, isUrgent=0, recordType=None, idx=None):
            scheduleItem.clientId = clientId
            scheduleItem.recordDatetime = QDateTime.currentDateTime()
            scheduleItem.recordPersonId = QtGui.qApp.userId
            scheduleItem.complaint = complaint
            scheduleItem.checked = False
            scheduleItem.isUrgent = isUrgent
            if recordType:
                scheduleItem.recordType = recordType
            if referral:
                scheduleItem.srcOrgId        = referral.srcOrgId
                scheduleItem.srcPerson       = referral.srcPerson
                scheduleItem.srcSpecialityId = referral.srcSpecialityId
                scheduleItem.srcNumber       = referral.srcNumber
                scheduleItem.srcDate         = referral.srcDate
            if idx:
                scheduleItem.idx = idx

        date = self.getCurrentDate()
        if self.checkApplicable(clientId, date):
            db = QtGui.qApp.db
            personId = self.getCurrentPersonId()
            specialityId = self.getPersonSpecialityId(personId)
            activityId = None
            orgStructureId = self.getPersonOrgStructureId(personId)
            modelQueue = tblQueue.model()
            modelQueue.updateData()
            row = tblQueue.currentIndex().row()
            if row == len(modelQueue.scheduleItems): # это плохо
                if len(modelQueue.schedules) == 1:
                    schedule = modelQueue.schedules[0]
                else:
                    schedule = self.selectSchedule(modelQueue.schedules)
                    if not schedule:
                        return False
                scheduleItem = modelQueue.createOvertimeScheduleItem(schedule)
            else:
                schedule = modelQueue.getSchedule(row)
                scheduleItem = modelQueue.getScheduleItem(row)
            # исправить запись по назначению сверхплана!!!
            if scheduleItem.overtime:
                appointmentPurposeId = schedule.appointmentPurposeId
            else:
                appointmentPurposeId = scheduleItem.appointmentPurposeId

            if (scheduleItem.enableQueueing
                and personId
                and specialityId
                and orgStructureId
                and clientId
                and schedule
                and scheduleItem
                and self.queueingEnabled(date, orgStructureId, specialityId, activityId, personId, schedule, tblQueue, row, clientId, appointmentPurposeId, scheduleItem)):

                appointmentPurposeId = schedule.appointmentPurposeId
                appointmentType = modelQueue.appointmentType
                if isReferralRequired(appointmentPurposeId):
                    referral = inputReferral(self)
                    if not referral:
                        return False
                else:
                    referral = None

                if QtGui.qApp.mainWindow.homeCallRequests:
                    self.prevComplaint = forceString(QtGui.qApp.mainWindow.homeCallRequests.tblHomeCallRequests.currentItem().value('reason'))
                else:
                    self.prevComplaint = ''

                if modelQueue.complaintRequired():
                    dlg = CComplaintsEditDialog(self)
                    if self.prevClientId == clientId or QtGui.qApp.mainWindow.homeCallRequests:
                        dlg.setComplaints(self.prevComplaint)
                    dlg.disableCancel()
                    dlg.exec_()
                    complaint = dlg.getComplaints()
                    self.prevClientId = clientId
                    self.prevComplaint = complaint
                else:
                    complaint = ''

                if scheduleItem.id is None:
                    if self.lock('Schedule', scheduleItem.scheduleId):
                        db.transaction()
                        try:
                            schedule.reloadItems()
                            #row = len(schedule.items)
                            scheduleItem.idx = schedule.items[-1].idx+1 if schedule.items else 0
                            fillScheduleItem(scheduleItem, clientId, complaint, referral, isUrgent, recordType)
                            scheduleItemId = scheduleItem.save()
                            if recordType and recordType == 4 and scheduleItemId:
                                if not createRelatedActionTMK(self, clientId, personId, scheduleItem.time, scheduleItemId):
                                    db.rollback()
                                    return False
                            if appointmentType == CSchedule.atHome:
                                QtGui.qApp.emitCurrentClientInfoJLWChanged(scheduleItemId)
                            else:
                                QtGui.qApp.emitCurrentClientInfoSAChanged(scheduleItemId)
                            db.commit()
                            # self.updateTimeTableRow(tblTimeTable)
                            # modelQueue.emitDataChanged(row)
                            # modelQueue.updateData()
                        except:
                            db.rollback()
                            raise
                        finally:
                            self.updateTimeTableRow(tblTimeTable)
                            modelQueue.emitDataChanged(row)
                            modelQueue.updateData()
                            self.releaseLock()
                    tblQueue.setCurrentIndex(modelQueue.index(row, 0))
                    return True
                else:
                    if self.lock('Schedule_Item', scheduleItem.id):
                        try:
                            modelQueue.updateData()
                            scheduleItem = modelQueue.getScheduleItem(row)
                            if scheduleItem.clientId or forceBool(scheduleItem.value('deleted')):
                                messageBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning,
                                                               u'Внимание!',
                                                               u'Запись на это время невозможна, так как оно уже занято',
                                                               QtGui.QMessageBox.Ok)
                                messageBox.setWindowFlags(messageBox.windowFlags() | Qt.WindowStaysOnTopHint)
                                messageBox.exec_()
                                return False

                            db.transaction()
                            try:
                                fillScheduleItem(scheduleItem, clientId, complaint, referral, isUrgent, recordType, idx)
                                scheduleItemId = scheduleItem.save()
                                if recordType and recordType == 4 and scheduleItemId:
                                    if not createRelatedActionTMK(self, clientId, personId, scheduleItem.time, scheduleItemId):
                                        db.rollback()
                                        return False
                                if appointmentType == CSchedule.atHome:
                                    QtGui.qApp.emitCurrentClientInfoJLWChanged(scheduleItemId)
                                else:
                                    QtGui.qApp.emitCurrentClientInfoSAChanged(scheduleItemId)
                                db.commit()
                                # self.updateTimeTableRow(tblTimeTable)
                                # modelQueue.emitDataChanged(row)
                                return True
                            except:
                                db.rollback()
                                raise
                            finally:
                                self.updateTimeTableRow(tblTimeTable)
                                modelQueue.emitDataChanged(row)
                                modelQueue.updateData()
                        finally:
                            self.releaseLock()
        return False


    def selectSchedule(self, schedules):
#        menu = QtGui.QMenu(self)
        menu = QtGui.QMenu()
        header = QtGui.QWidgetAction(menu)
        header.setDefaultWidget(QtGui.QLabel(u'Выберите период приёма', menu))
        menu.addAction(header)
        firstAction = None
        for i, schedule in enumerate(schedules):
            timeRange = formatTimeRange((schedule.begTime, schedule.endTime))
            appointmentPurpose = CAppointmentPurposeCache.getName(schedule.appointmentPurposeId)
            menuItemText = u'%s\t%s\t%s' % (timeRange, schedule.office, appointmentPurpose)
            if i<=10:
                menuItemText = '&%d %s' % ((i+1)%10, menuItemText)
            action = QtGui.QAction(menuItemText, menu)
            action.setData(i)
            menu.addAction(action)
            if firstAction is None:
                firstAction = action
        selectedAction = menu.exec_(QtGui.QCursor.pos(), firstAction)
        if selectedAction:
            row = forceInt(selectedAction.data())
            return schedules[row]
        else:
            return None


    def updateTimeTableRow(self, tblTimeTable):
        tblTimeTable.model().updateAvail(tblTimeTable.currentIndex().row())


    def checkApplicable(self, clientId, date):
        db = QtGui.qApp.db
        personId = self.getCurrentPersonId()
        clientIsNotAlive = forceDateTime(db.translate('Client', 'id', clientId, 'deathDate'))
        return (     self.checkClientAttach(personId, clientId, date, True)
                 and (    self.checkClientAttendance(personId, clientId)
                       or self.confirmClientAttendance(self, personId, clientId)
                     )
                 and self.confirmClientPolicyConstraint(self, clientId)
                 and not clientIsNotAlive
               )


    def printOrder(self, tblQueue):
        row = tblQueue.currentIndex().row()
        scheduleItem = tblQueue.model().getScheduleItem(row)
        if scheduleItem:
            printOrderByScheduleItem(self, scheduleItem.id)


    def deleteOrder(self, tblTimeTable, tblQueue):
        modelQueue = tblQueue.model()
        row = tblQueue.currentIndex().row()
        scheduleItem = modelQueue.getScheduleItem(row)
        if scheduleItem:
            confirmAndFreeScheduleItem(self, scheduleItem.id, scheduleItem.recordPersonId, scheduleItem.clientId)
            modelQueue.updateData()
            QtGui.qApp.emitCurrentClientInfoJLWDeleted(scheduleItem.id)


    def changeComplaint(self, tblQueue):
        modelQueue = tblQueue.model()
        modelQueue.updateData()

        row = tblQueue.currentIndex().row()
        complaint = modelQueue.getComplaint(row)
        if complaint is not None:
            dlg = CComplaintsEditDialog(self)
            dlg.setComplaints(complaint)
            if dlg.exec_():
                modelQueue.setComplaint(row, dlg.getComplaints())


    def changeReferral(self, tblQueue):
        modelQueue = tblQueue.model()
        modelQueue.updateData()
        row = tblQueue.currentIndex().row()
        referral = modelQueue.getReferral(row)
        dlg = CReferralEditDialog(self)
        dlg.setReferral(referral)
        if dlg.exec_():
            modelQueue.setReferral(row, dlg.getReferral())


    def printOrderByTemplate(self, tblQueue, templateId):
        queueTableRow = tblQueue.currentIndex().row()
        modelQueue = tblQueue.model()

        schedule = modelQueue.getSchedule(queueTableRow)
        scheduleItem = modelQueue.getScheduleItem(queueTableRow)
        if schedule and scheduleItem:
            clientId = scheduleItem.clientId
            if clientId:
                visit = {'timeRange'      : formatTimeRange((schedule.begTime, schedule.endTime)),
                         'purpose'        : CAppointmentPurposeInfo(self, schedule.appointmentPurposeId),
                         'office'         : schedule.office,
                         'date'           : CDateInfo(schedule.date),
                         'time'           : CTimeInfo(scheduleItem.time),
                         'num'            : scheduleItem.idx+1,
                         'overtime'       : scheduleItem.overtime,
                         'complaints'     : scheduleItem.complaint,
                         'recordDatetime' : CDateTimeInfo(scheduleItem.recordDatetime),
                         }
                clientInfo = getClientInfo2(clientId)
                personInfo = clientInfo.getInstance(CPersonInfo, schedule.personId)
                data = { 'client':clientInfo,
                         'person':personInfo,
                         'visit': visit
                       }
                applyTemplate(self, templateId, data)


    def printQueue(self, tblQueue, variantPrint, nameMenuPrintQueue = u''):
        def _formatNote(note):
            target = u'Логин записавшего администратора'
            if target in note:
                return target + note[note.find(target)+len(target):]
            return note

        def _formatPerson(recordClass, recordPersonId, note):
            if recordClass:
                return {CScheduleItem.rcInfomat:u'Инфомат',
                        CScheduleItem.rcCallCenter:u'Call-центр; %s'%_formatNote(note),
                        CScheduleItem.rcInternet   : u'Интернет'
                       }.get(recordClass, u'')
            else:
                return forceString(QtGui.qApp.db.translate('vrbPersonWithSpeciality', 'id', recordPersonId, 'name'))

        def Visit_ExecPerson(sheduleItemId):
            db = QtGui.qApp.db
            stmt = u'''SELECT IFNULL(vVisitExt.person_id, Schedule.person_id) AS person_id
                                  FROM Schedule_Item 
                                    LEFT JOIN Schedule     ON Schedule.id      = Schedule_Item.master_id 
                                      LEFT JOIN Person       ON Person.id        = Schedule.person_id 
                                        LEFT JOIN vVisitExt    ON vVisitExt.client_id = Schedule_Item.client_id  AND Person.speciality_id=vVisitExt.speciality_id AND DATE(vVisitExt.date) = Schedule.date 
                                          WHERE Schedule_Item.id = %(sheduleItemId)s 
                                            AND Schedule_Item.deleted = 0 AND Schedule.deleted = 0
                                              ORDER BY Schedule_Item.time DESC
            ''' % {'sheduleItemId': sheduleItemId}
            query = db.query(stmt)
            if query.first():
                record = query.record()
                result = forceInt(record.value(0))
                return result



        # receptionInfo = self.getReceptionInfo(timeTableWidget)
        # personId = receptionInfo['personId']
        modelQueue = tblQueue.model()
        if len(modelQueue.schedules) == 1:
            schedule = modelQueue.schedules[0]
            office = schedule.office
            timeRange = formatTimeRange((schedule.begTime, schedule.endTime))
        else:
            offices = []
            for schedule in modelQueue.schedules:
                timeRange = formatTimeRange((schedule.begTime, schedule.endTime))
                offices.append(u'%s (%s)' % (schedule.office, timeRange))
            office = formatList(offices)
            timeRange = formatTimeRange((min(schedule.begTime for schedule in modelQueue.schedules),
                                         max(schedule.endTime for schedule in modelQueue.schedules)
                                        )
                                       )
        date = modelQueue.schedules[0].date
        personId = modelQueue.schedules[0].personId
        personInfo = self.getPersonInfo(personId)


        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportSubTitle)
        if tblQueue == self.tblAmbQueue:
            cursor.insertText(u'запись на амбулаторный приём' + nameMenuPrintQueue)
        else:
            cursor.insertText(u'вызовы на дом' + nameMenuPrintQueue)
            office = ''
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(personInfo['fullName'])
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportSubTitle)
        cursor.insertText(personInfo['specialityName'])
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportSubTitle)
        cursor.insertText(forceString(date) +' '+timeRange+' '+office)
        cols = [('5%',  [u'№'],       CReportBase.AlignRight),
                ('5%',  [u'время'],   CReportBase.AlignRight),
                ('50%', [u'пациент'], CReportBase.AlignLeft),
                ('20%', [u'жалобы'],  CReportBase.AlignLeft),
                ('10%', [u'записал'],  CReportBase.AlignLeft),
                ('10%', [u'выполнил'],  CReportBase.AlignLeft),
               ]
        table = createTable(cursor, cols)
        cnt = 0
        for row in xrange(modelQueue.realRowCount()):
            scheduleItem = modelQueue.getScheduleItem(row)
            VisitPerson = Visit_ExecPerson(scheduleItem.id)
            if not scheduleItem:
                continue
            clientId = scheduleItem.clientId
            if clientId:
                if scheduleItem.overtime:
                    time = QDateTime()
                else:
                    time = scheduleItem.time

                recordClass = scheduleItem.recordClass
                recordPersonId = scheduleItem.recordPersonId
                note = scheduleItem.note
                if (((variantPrint == 0 or variantPrint == 1) and tblQueue == self.tblHomeQueue) or
                    ((variantPrint == 0 or variantPrint == 1) and (tblQueue == self.tblAmbQueue and
                      QtGui.qApp.ambulanceUserCheckable()))):
                    checked = scheduleItem.checked
                    if checked == variantPrint:
                        recordPerson = _formatPerson(recordClass, recordPersonId, note)
                        recordVisitPerson = _formatPerson(None, VisitPerson, note)
                        clientInfo = getClientInfoEx(clientId, self.getCurrentDate())
                        clientText = u'%(fullName)s, %(birthDateStr)s (%(age)s), %(sex)s, код: %(id)s, СНИЛС: %(SNILS)s\n' \
                                     u'документ %(document)s, полис %(policy)s\n' \
                                     u'адр.рег. %(regAddress)s\n' \
                                     u'адр.прож. %(locAddress)s\n' \
                                     u'занятость %(work)s\n' \
                                     u'%(phones)s' % clientInfo
                        i = table.addRow()
                        cnt+=1
                        table.setText(i, 0, cnt)
                        table.setText(i, 1, locFormatTime(time))
                        table.setText(i, 2, clientText)
                        table.setText(i, 3, scheduleItem.complaint)
                        table.setText(i, 4, recordPerson)
                        table.setText(i, 5, recordVisitPerson)
                else:
                    if variantPrint == 2:
                        recordPerson = _formatPerson(recordClass, recordPersonId, note)
                        recordVisitPerson = _formatPerson(None, VisitPerson, note)
                        clientInfo = getClientInfoEx(clientId, self.getCurrentDate())
                        clientText = u'%(fullName)s, %(birthDateStr)s (%(age)s), %(sex)s, код: %(id)s, СНИЛС: %(SNILS)s\n' \
                                     u'документ %(document)s, полис %(policy)s\n' \
                                     u'адр.рег. %(regAddress)s\n' \
                                     u'адр.прож. %(locAddress)s\n' \
                                     u'прикрепление %(attaches)s\n' \
                                     u'занятость %(work)s\n' \
                                     u'%(phones)s' % clientInfo
                        i = table.addRow()
                        cnt+=1
                        table.setText(i, 0, cnt)
                        table.setText(i, 1, locFormatTime(time))
                        table.setText(i, 2, clientText)
                        table.setText(i, 3, scheduleItem.complaint)
                        table.setText(i, 4, recordPerson)
                        table.setText(i, 5, recordVisitPerson)
        reportView = CReportViewDialog(self)
        reportView.setWindowTitle(u'Очередь')
        reportView.setText(doc)
        reportView.exec_()


    def printQueueByTemplate(self, tblQueue, templateId):
        modelQueue = tblQueue.model()
        if len(modelQueue.schedules) == 1:
            schedule = modelQueue.schedules[0]
            office = schedule.office
            timeRange = formatTimeRange((schedule.begTime, schedule.endTime))
        else:
            offices = []
            for schedule in modelQueue.schedules:
                timeRange = formatTimeRange((schedule.begTime, schedule.endTime))
                offices.append(u'%s (%s)' % (schedule.office, timeRange))
            office = formatList(offices)
            timeRange = formatTimeRange((min(schedule.begTime for schedule in modelQueue.schedules),
                                         max(schedule.endTime for schedule in modelQueue.schedules)
                                        )
                                       )
        schedule = modelQueue.schedules[0]
        date = schedule.date
        personId = schedule.personId

        context = CInfoContext()
        queue = []
        for item in modelQueue.scheduleItems: # плохо!
                time       = item.time
                overtime = item.overtime
                clientId   = item.clientId
                if clientId:
                    checked        = item.checked
                    complaint      = item.complaint
                    recordPersonId = item.recordPersonId
                    recordDatetime = item.recordDatetime
                else:
                    checked        = False
                    complaint      = ''
                    recordPersonId = None
                    recordDatetime = None
                queue.append(CQueueItemInfo(context, time, clientId, checked, complaint, recordPersonId, recordDatetime, overtime))

        data = {'date'     : CDateInfo(date),
                'office'   : office,
                'person'   : context.getInstance(CPersonInfo, personId),
                'timeRange': timeRange,
                'queue'   : queue,
               }
        applyTemplate(self, templateId, data)


    def showInfo(self, tblQueue):
        modelQueue = tblQueue.model()
        row = tblQueue.currentIndex().row()
        scheduleItem = modelQueue.getScheduleItem(row)
        if scheduleItem:
            showScheduleItemInfo(scheduleItem.id, self)


    def inviteClient(self, tblQueue):
        modelQueue = tblQueue.model()
        modelQueue.updateData()
        row = tblQueue.currentIndex().row()
        modelQueue.setInvitation(row, True)
        modelQueue.reset()


    def cancelInvitation(self, tblQueue):
        modelQueue = tblQueue.model()
        modelQueue.updateData()
        row = tblQueue.currentIndex().row()
        modelQueue.setInvitation(row, False)
        modelQueue.reset()


    def getCurrentQueuedClientId(self, tblQueue):
        row = tblQueue.currentIndex().row()
        if row>=0:
            return tblQueue.model().getClientId(row)
        else:
            return None


    def getPersonInfo(self, personId):
        return getPersonInfo(personId)


    # этот метод не нужен этому классу.
    def getCurrentOrgSrtuctureId(self):
        treeIndex = self.treeOrgStructure.currentIndex()
        return self.modelOrgStructure.itemId(treeIndex)


    # этот метод не нужен этому классу.
    def getCurrentPersonIdList(self):
        treeIndex = self.treeOrgPersonnel.currentIndex()
        return self.modelPersonnel.getItemIdList(treeIndex)



    ######### слоты

    def onCurrentOrgIdChanged(self):
        application = QtGui.qApp
        self.modelOrgStructure.setOrgId(application.currentOrgId())
        self.updatePersonnelByOrgStructure()
        self.updateTimeTable()


    def onCurrentUserIdChanged(self):
        application = QtGui.qApp
        if application.userOrgStructureId:
            index = self.modelOrgStructure.findItemId(application.userOrgStructureId)
            if index and index.isValid():
                self.treeOrgStructure.setCurrentIndex(index)
        if application.userSpecialityId:
            index = self.modelPersonnel.findPersonId(application.userId)
            if index and index.isValid():
                self.treeOrgPersonnel.setCurrentIndex(index)
        self.setCalendarDataRange()
        self.actAmbNotification.setEnabled(application.userHasAnyRight([
                        urAdmin, urSendInternalAmbNotifications]))
        hasRightmodifyCheck = QtGui.qApp.userHasRight(urQueueModifyCheck)
        ambCheckable = QtGui.qApp.ambulanceUserCheckable()
        self.modelAmbQueue.setItemsAreCheckable(hasRightmodifyCheck and ambCheckable)
        self.modelHomeQueue.setItemsAreCheckable(hasRightmodifyCheck)


    @pyqtSignature('')
    def on_timer_timeout(self):
        def update(tblTimeTable, tblQueue):
            if tblTimeTable.isEnabled():
                modelTimeTable = tblTimeTable.model()
                selectionModelTimeTable = tblTimeTable.selectionModel()
                currentRow = tblTimeTable.currentIndex().row()
                schedule = modelTimeTable.getSchedule(currentRow)
                if schedule:
                    currentDate = schedule.date
                    currentScheduleId = schedule.id
                else:
                    currentDate = self.getCurrentDate()
                    currentScheduleId = None
                selectedRows = self.getSelectedRowsInTimeTable(selectionModelTimeTable)
                selectedScheduleId = [ modelTimeTable.getSchedule(row).id
                                       for row in selectedRows
                                     ]
                modelQueue = tblQueue.model()
                currentQueueRow = tblQueue.currentIndex().row()
                modelTimeTable.updateData()
                newSelectedRows = [ modelTimeTable.findRowForScheduleId(scheduleId)
                                    for scheduleId in selectedScheduleId
                                  ]
                rowForCurrentScheduleId = modelTimeTable.findRowForScheduleId(currentScheduleId)
                newCurrentRow = modelTimeTable.getRowForDate(currentDate, rowForCurrentScheduleId if rowForCurrentScheduleId>=0 else currentRow)
                self.selectRowsInTimeTable(selectionModelTimeTable, newSelectedRows)
                selectionModelTimeTable.setCurrentIndex(modelTimeTable.index(newCurrentRow, 0),
                                                        selectionModelTimeTable.NoUpdate)
                self.updateQueueEx(tblTimeTable,
                                   modelTimeTable,
                                   selectionModelTimeTable,
                                   tblQueue,
                                   modelQueue
                                  )
                tblQueue.setCurrentIndex(modelQueue.index(currentQueueRow, 0))
        self.timer.stop()
        try:
            self.setCalendarDataRange()
            place = self.tabPlace.currentIndex()
            queuetbl = self.tblAmbQueue if place == 0 else self.tblHomeQueue
            timetbl = self.tblAmbTimeTable if place == 0 else self.tblHomeTimeTable
            selectedRows = queuetbl.selectedRowList()
            update(timetbl, queuetbl)
            queuetbl.setSelectedRowList(selectedRows)
        finally:
            self.timer.start()


    def onTreeOrgStructureHeaderClicked(self, col, reverse=True):
        application = QtGui.qApp
        if reverse:
            self.activityListIsShown = not self.activityListIsShown

        if not self.activityListIsShown:
            self.treeOrgStructure.setModel(None)
            self.setModels(self.treeOrgStructure, self.modelOrgStructure, self.selectionModelOrgStructure)
            orgStructureIndex = self.modelOrgStructure.findItemId(application.currentOrgStructureId())
            if orgStructureIndex and orgStructureIndex.isValid():
                self.treeOrgStructure.setCurrentIndex(orgStructureIndex)
                self.treeOrgStructure.setExpanded(orgStructureIndex, True)
            self.updatePersonnelByOrgStructure()
        else:
             self.treeOrgStructure.setModel(None)
             self.setModels(self.treeOrgStructure, self.modelActivity, self.selectionModelActivity)
             self.updatePersonnelByActivity()
        application.preferences.appPrefs['activityListIsShown'] = self.activityListIsShown


    def onTreeOrgPersonnelHeaderClicked(self, col, reverse=True):
        if reverse:
            self.groupingSpeciality = not self.groupingSpeciality

        if hasattr(self, 'selectionModelPersonnel'):
            self.disconnect(self.selectionModelPersonnel,
                            SIGNAL('currentChanged(QModelIndex, QModelIndex)'),
                            self.on_selectionModelPersonnel_currentChanged)
            del self.selectionModelPersonnel

        self.treeOrgPersonnel.setModel(None)
        if self.groupingSpeciality:
            self.addModels('Personnel', CResourcesPersonnelModel([], self))
        else:
            self.addModels('Personnel', CFlatResourcesPersonnelModel([], self))

        self.setModels(self.treeOrgPersonnel, self.modelPersonnel, self.selectionModelPersonnel)
        self.connect(self.selectionModelPersonnel,
                     SIGNAL('currentChanged(QModelIndex, QModelIndex)'),
                     self.on_selectionModelPersonnel_currentChanged)

        QtGui.qApp.preferences.appPrefs['groupingSpeciality'] = self.groupingSpeciality

        if self.activityListIsShown:
            self.updatePersonnelByActivity()
        else:
            self.updatePersonnelByOrgStructure()

    def isSwitchToUserSchedule(self):
        """
        Функция проверяет локальную настройку "Переходить в свой график при записи не к себе"

            0 или None - Запись работает как обычно
            1 - Отменяет запись на талон и переключает расписание выбранного врача на расписание врача под которым залогинен пользователь
            2 - При записи спросит необходимо ли переключение на расписание залогиненого врача

        True - В случае если необходимо переключение на расписание залогиненого врача
        False - В случае если переключение ненужно
        """
        switchingToUserSchedule = QtGui.qApp.preferences.appPrefs.get('switchingToUserSchedule')
        if not switchingToUserSchedule:
            return False
        userPersonId = QtGui.qApp.userId
        personIndex = self.treeOrgPersonnel.currentIndex()
        personId = self.modelPersonnel.getItemIdList(personIndex)
        userPersonIndex = self.modelPersonnel.findPersonId(userPersonId)
        userPersonOrgStructureIndex = self.modelOrgStructure.findItemId(QtGui.qApp.userOrgStructureId)

        if (userPersonId in personId) or not(userPersonIndex and userPersonIndex.isValid()):
            return False

        if switchingToUserSchedule == 1:
            if userPersonOrgStructureIndex and userPersonOrgStructureIndex.isValid():
                self.treeOrgStructure.setCurrentIndex(userPersonOrgStructureIndex)
            self.treeOrgPersonnel.setCurrentIndex(userPersonIndex)
            return True
        elif switchingToUserSchedule == 2:
            if QtGui.QMessageBox().question(self,
                                            u'Внимание!',
                                            u'Перейти на повторный прием?',
                                            QtGui.QMessageBox.No | QtGui.QMessageBox.Yes,
                                            QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
                if userPersonOrgStructureIndex and userPersonOrgStructureIndex.isValid():
                    self.treeOrgStructure.setCurrentIndex(userPersonOrgStructureIndex)
                self.treeOrgPersonnel.setCurrentIndex(userPersonIndex)
                return True
            else:
                return False
        else:
            return False

    @pyqtSignature('int')
    def on_tabPlace_currentChanged(self, index):
        self.isNeededUpdateSchedulesForSelectedDate = True
        newAppointmentType = CSchedule.atAmbulance if index == 0 else CSchedule.atHome
        if self.appointmentType != newAppointmentType:
            self.appointmentType = newAppointmentType
            self.emit(SIGNAL('appointmentTypeChanged(int)'), self.appointmentType)
        self.updateTimeTable()
        self.isNeededUpdateSchedulesForSelectedDate = False


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelOrgStructure_currentChanged(self, current, previous):
        self.updatePersonnelByOrgStructure()


    def onTreeOrgStructurePopupMenuAboutToShow(self):
        currentClientId = QtGui.qApp.currentClientId()
        self.actFindArea.setEnabled(bool(currentClientId))


    @pyqtSignature('')
    def on_actFindArea_triggered(self):
        addressId = None
        currentClientId = QtGui.qApp.currentClientId()
        if currentClientId:
            attachRecord = getClientAttachEx(currentClientId, 0)
            if attachRecord and attachRecord['orgStructure_id']:
                id = attachRecord['orgStructure_id']
            else:
                r = getClientAddressEx(currentClientId)
                addressId = forceRef(r.value('address_id')) if r else None
                age = calcAgeTuple(forceDate(QtGui.qApp.db.translate('Client', 'id', currentClientId,'birthDate')), QDate.currentDate())
                idList = findOrgStructuresByAddress(addressId, QtGui.qApp.currentOrgId(), clientAge=age)
                id = self.filterStructureId(idList, QtGui.qApp.currentOrgStructureId())
            if id:
                index = self.modelOrgStructure.findItemId(id)
                self.treeOrgStructure.setCurrentIndex(index)
            else:
                msg = u'Адрес пациента не соответствует никакому участку' if addressId else u'Адрес пациента пуст'
                QtGui.QMessageBox.warning( self.parent(),
                                           u'Поиск участка',
                                           msg,
                                           QtGui.QMessageBox.Ok,
                                           QtGui.QMessageBox.Ok)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelActivity_currentChanged(self, current, previous):
        self.updatePersonnelByActivity()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelPersonnel_currentChanged(self, current, previous):
        self.updateTimeTable()


    def onTreeOrgPersonnelPopupMenuAboutToShow(self):
        currentClientId = QtGui.qApp.currentClientId()
        self.actRegistrySuspenedAppointment.setEnabled(bool(currentClientId))
        self.actRegistryProphylaxisPlanning.setEnabled(bool(currentClientId))


    @pyqtSignature('')
    def on_actRegistrySuspenedAppointment_triggered(self):
        setRegistrySuspenedAppointment(self, QtGui.qApp.currentClientId())


    @pyqtSignature('')
    def on_actRegistryProphylaxisPlanning_triggered(self): #???
        registry = QtGui.qApp.mainWindow.registry
        if registry:
            clientIdList = registry.tblClients.selectedItemIdList() # currentClientId?
            if clientIdList:
                setRegistryProphylaxisPlanningList(self, clientIdList)


    @pyqtSignature('')
    def on_calendarWidget_selectionChanged(self):
        if self.activityListIsShown:
            self.updatePersonnelByActivity()
        else:
            self.updatePersonnelByOrgStructure()


    @pyqtSignature('int')
    def on_tabPlace_currentChanged(self, index):
        self.updateTimeTable()


    # автоматическое связывание не годится :(
    # @pyqtSignature('QModelIndex, QModelIndex')
    def onSelectionModelAmbTimeTableCurrentRowChanged(self, current, previous):
        currentRow = current.row()
        previousRow = previous.row()
        if 0<=currentRow<self.modelAmbTimeTable.rowCount():
            self.updateTimeTableSelection(self.tblAmbTimeTable,
                                          self.modelAmbTimeTable,
                                          self.selectionModelAmbTimeTable,
                                          self.tblAmbQueue,
                                          self.modelAmbQueue,
                                          currentRow,
                                          previousRow)


    # автоматическое связывание не годится :(
    # @pyqtSignature('QModelIndex, QModelIndex')
    def onSelectionModelHomeTimeTableCurrentRowChanged(self, current, previous):
        currentRow = current.row()
        previousRow = previous.row()
        if 0<=currentRow<self.modelHomeTimeTable.rowCount():
            self.updateTimeTableSelection(self.tblHomeTimeTable,
                                          self.modelHomeTimeTable,
                                          self.selectionModelHomeTimeTable,
                                          self.tblHomeQueue,
                                          self.modelHomeQueue,
                                          currentRow,
                                          previousRow)


    @pyqtSignature('')                                     # см. примечание 1
    def on_modelAmbTimeTable_rowCountChanged(self):               # см. примечание 1
        self.tblAmbTimeTable.verticalHeader().setUpdatesEnabled(True) # см. примечание 1


    @pyqtSignature('')                                     # см. примечание 1
    def on_modelHomeTimeTable_rowCountChanged(self):                  # см. примечание 1
        self.tblHomeTimeTable.verticalHeader().setUpdatesEnabled(True)# см. примечание 1


    @pyqtSignature('QModelIndex')
    def on_tblAmbQueue_doubleClicked(self, index):
        clientId = self.getCurrentQueuedClientId(self.tblAmbQueue)
        queueModel = self.tblAmbQueue.model()
        if 0<=index.row()<len(queueModel.scheduleItems):
            isEnableQueueingForItem = queueModel.scheduleItems[index.row()].enableQueueing
        else:
            isEnableQueueingForItem = self.enableQueueing
        if clientId:
            if QtGui.qApp.doubleClickQueuePerson() == 0:
                self.on_actAmbChangeComplaint_triggered()
            elif QtGui.qApp.doubleClickQueuePerson() == 1:
                    self.on_actAmbFindClient_triggered()
            elif QtGui.qApp.doubleClickQueuePerson() == 2:
                   self.on_actAmbCreateEvent_triggered()
        elif self.enableQueueing and isEnableQueueingForItem:
            self.on_actAmbCreateOrder_triggered()


    @pyqtSignature('QModelIndex')
    def on_tblHomeQueue_doubleClicked(self, index):
        clientId = self.getCurrentQueuedClientId(self.tblHomeQueue)
        if clientId:
            if QtGui.qApp.doubleClickQueuePerson() == 0:
                self.on_actHomeChangeComplaint_triggered()
            elif QtGui.qApp.doubleClickQueuePerson() == 1:
                    self.on_actHomeFindClient_triggered()
            elif QtGui.qApp.doubleClickQueuePerson() == 2:
                   self.on_actHomeCreateEvent_triggered()
        elif self.enableQueueing:
            self.on_actHomeCreateOrder_triggered()


    @pyqtSignature('')
    def on_tblAmbQueue_popupMenuAboutToShow(self):
        self.popupMenuAboutToShow(self.tblAmbQueue,
                                  self.actAmbCreateOrder,
                                  self.actAmbCreateOrderUrgent,
                                  self.actAmbCreateOrderTMK,
                                  self.actAmbDeleteOrder,
                                  self.actAmbChangeComplaint,
                                  self.actAmbChangeReferral,
                                  self.actAmbPrintOrder,
                                  self.actAmbPrintOrderByTemplate,
                                  self.actAmbPrintQueue,
                                  self.actAmbPrintConfirmedQueue,
                                  self.actAmbPrintUnconfirmedQueue,
                                  self.actAmbPrintQueueByTemplate,
                                  self.actAmbFindClient,
                                  self.actAmbFindClientEvents,
                                  self.actAmbCreateEvent,
                                  self.actServiceReport,
                                  self.actAmbInfo,
                                  self.actAmbInviteClient,
                                  self.actAmbCancelInvitation)


    @pyqtSignature('')
    def on_tblHomeQueue_popupMenuAboutToShow(self):
        self.popupMenuAboutToShow(self.tblHomeQueue,
                                  self.actHomeCreateOrder,
                                  self.actHomeCreateOrderUrgent,
                                  self.actHomeDeleteOrder,
                                  self.actHomeChangeComplaint,
                                  self.actHomeChangeReferral,
                                  self.actHomePrintOrder,
                                  self.actHomePrintOrderByTemplate,
                                  self.actHomePrintQueue,
                                  self.actHomePrintConfirmedQueue,
                                  self.actHomePrintUnconfirmedQueue,
                                  self.actHomePrintQueueByTemplate,
                                  self.actHomeFindClient,
                                  self.actHomeFindClientEvents,
                                  self.actHomeCreateEvent,
                                  self.actServiceReport,
                                  self.actHomeInfo)


    @pyqtSignature('')                                            # см. примечание 1
    def on_modelAmbQueue_rowCountChanged(self):                   # см. примечание 1
        self.tblAmbQueue.verticalHeader().setUpdatesEnabled(True) # см. примечание 1
        self.tblAmbQueue.verticalHeader().setMinimumWidth(self.tblAmbQueue.verticalHeader().defaultSectionSize() + self.font().pointSize()*3.7)


    @pyqtSignature('')                                            # см. примечание 1
    def on_modelHomeQueue_rowCountChanged(self):                  # см. примечание 1
        self.tblHomeQueue.verticalHeader().setUpdatesEnabled(True)# см. примечание 1
        self.tblHomeQueue.verticalHeader().setMinimumWidth(self.tblHomeQueue.verticalHeader().defaultSectionSize() + self.font().pointSize()*3.7)


    @pyqtSignature('')
    def on_actAmbCreateOrder_triggered(self):

        # Для Сириуса делаем сохранение номера талончика электронной очереди в Schedule_Item.idx
        idx = None
        lpuCode = forceString(QtGui.qApp.db.translate('Organisation', 'id', QtGui.qApp.currentOrgId(), 'infisCode'))
        if lpuCode == "48001" and self.getCurrentDate() == QDate.currentDate(): # у Сириуса ОМС = 48001, тестирую на 10.2.94.42 20011
            dialog = CElQueueNumberDialog(self)
            if dialog.exec_():
                if dialog.queue_number > 0:
                    idx = dialog.queue_number
            else:
                return

        if self.createOrder(self.tblAmbTimeTable, self.tblAmbQueue, QtGui.qApp.currentClientId(), idx=idx):
            self.printOrder(self.tblAmbQueue)
        QtGui.qApp.emitCurrentClientInfoChanged()
    
    
    @pyqtSignature('')
    def on_actAmbCreateOrderUrgent_triggered(self):
        if self.createOrder(self.tblAmbTimeTable, self.tblAmbQueue, QtGui.qApp.currentClientId(), isUrgent = 1):
            self.printOrder(self.tblAmbQueue)
        QtGui.qApp.emitCurrentClientInfoChanged()


    @pyqtSignature('')
    def on_actAmbCreateOrderTMK_triggered(self):
        if self.isSwitchToUserSchedule():
            return
        if self.createOrder(self.tblAmbTimeTable, self.tblAmbQueue, QtGui.qApp.currentClientId(), recordType = 4):
            self.printOrder(self.tblAmbQueue)
        QtGui.qApp.emitCurrentClientInfoChanged()


    @pyqtSignature('')
    def on_actAmbDeleteOrder_triggered(self):
        self.deleteOrder(self.tblAmbTimeTable, self.tblAmbQueue)
        QtGui.qApp.emitCurrentClientInfoChanged()


    @pyqtSignature('')
    def on_actAmbChangeComplaint_triggered(self):
        self.changeComplaint(self.tblAmbQueue)
        QtGui.qApp.emitCurrentClientInfoChanged()


    @pyqtSignature('')
    def on_actAmbChangeReferral_triggered(self):
        self.changeReferral(self.tblAmbQueue)
        QtGui.qApp.emitCurrentClientInfoChanged()


    @pyqtSignature('')
    def on_actAmbPrintOrder_triggered(self):
        self.printOrder(self.tblAmbQueue)


    @pyqtSignature('int')
    def on_actAmbPrintOrderByTemplate_printByTemplate(self, templateId):
        self.printOrderByTemplate(self.tblAmbQueue, templateId)


    @pyqtSignature('')
    def on_actAmbPrintQueue_triggered(self):
        self.printQueue(self.tblAmbQueue, 2)


    @pyqtSignature('')
    def on_actAmbPrintConfirmedQueue_triggered(self):
        nameMenuPrintQueue = u', список подтвержденных записей'
        self.printQueue(self.tblAmbQueue, 1, nameMenuPrintQueue)


    @pyqtSignature('')
    def on_actHomePrintUnconfirmedQueue_triggered(self):
        nameMenuPrintQueue = u', список непереданных врачу'
        self.printQueue(self.tblHomeQueue, 0, nameMenuPrintQueue)


    @pyqtSignature('')
    def on_actAmbPrintUnconfirmedQueue_triggered(self):
        nameMenuPrintQueue = u', список неподтвержденных записей'
        self.printQueue(self.tblAmbQueue, 0, nameMenuPrintQueue)


    @pyqtSignature('')
    def on_actHomePrintConfirmedQueue_triggered(self):
        nameMenuPrintQueue = u', список переданных врачу'
        self.printQueue(self.tblHomeQueue, 1, nameMenuPrintQueue)


    @pyqtSignature('')
    def on_actAmbPrintPreRecordQueue_triggered(self):
        currentRow = self.tblAmbTimeTable.currentIndex().row()
        currentSchedule = self.modelAmbTimeTable.getSchedule(currentRow)
        if currentSchedule:
            scheduleList = [self.modelAmbTimeTable.getSchedule(row) for row in self.modelAmbTimeTable.getRowListForDate(currentSchedule.date)]
            CReportBeforeRecord(currentSchedule, scheduleList).exec_()


    @pyqtSignature('int')
    def on_actAmbPrintQueueByTemplate_printByTemplate(self, templateId):
        self.printQueueByTemplate(self.tblAmbQueue, templateId)


    @pyqtSignature('')
    def on_actAmbCreateEvent_triggered(self):
        row = self.tblAmbQueue.currentIndex().row()
        modelQueue = self.tblAmbQueue.model()
        scheduleItem = modelQueue.getScheduleItem(row)
        schedule = modelQueue.getSchedule(row)
        if not scheduleItem:
            return

        personId = schedule.personId
        # specialityId = self.getPersonSpecialityId(personId)
        time = scheduleItem.time
        date = schedule.date
        params = {'widget'             : self,
                  'clientId'           : scheduleItem.clientId,
                  'flagHospitalization':False,
                  'actionTypeId'       : None,
                  'valueProperties'    : [],
                  'eventTypeFilterHospitalization': 0,
                  'dateTime'           : time if time else QDateTime(date),
                  'personId'           : personId,
                  'typeQueue'          : 0,
                  'srcOrgId'           : scheduleItem.srcOrgId,
                  'srcPerson'          : scheduleItem.srcPerson,
                  'srcSpeciality'      : scheduleItem.srcSpecialityId,
                  'srcNumber'          : scheduleItem.srcNumber,
                  'srcDate'            : scheduleItem.srcDate,
                 }
        requestNewEvent(params)
        # else: когда у врача нет специальности?!
        #     QtGui.qApp.requestNewEvent(scheduleItem.clientId, 0)


    @pyqtSignature('')
    def on_actHomeCreateEvent_triggered(self):
        row = self.tblHomeQueue.currentIndex().row()
        modelQueue = self.tblHomeQueue.model()
        scheduleItem = modelQueue.getScheduleItem(row)
        schedule = modelQueue.getSchedule(row)
        if not scheduleItem:
            return
        time = scheduleItem.time
        date = schedule.date
        params = {'widget'             : self,
                  'clientId'           : scheduleItem.clientId,
                  'flagHospitalization':False,
                  'actionTypeId'       : None,
                  'valueProperties'    : [],
                  'eventTypeFilterHospitalization': 0,
                  'dateTime'           : time if time else QDateTime(date),
                  'personId'           : schedule.personId,
                  'typeQueue'          : 1
                 }
        requestNewEvent(params)
#        else: когда у врача нет специальности?!
#            QtGui.qApp.requestNewEvent(clientId, 1)


    # мне не нравится построение отчёта прямо здесь...
    @pyqtSignature('')
    def on_actAmbFindClient_triggered(self):
        clientId = self.getCurrentQueuedClientId(self.tblAmbQueue)
        QtGui.qApp.findClient(clientId)


    @pyqtSignature('')
    def on_actAmbFindClientEvents_triggered(self):
        clientId = self.getCurrentQueuedClientId(self.tblAmbQueue)
        if not QtGui.qApp.mainWindow.registry:
            QtGui.qApp.mainWindow.on_actRegistry_triggered()
        QtGui.qApp.findClient(clientId)
        QtGui.qApp.mainWindow.registry.tabMain.setCurrentIndex(1)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelHomeTimeTable_currentChanged(self, current, previous):
        row = current.row()
        if row != previous.row() and 0<=row<self.modelHomeTimeTable.rowCount():
            date = self.modelHomeTimeTable.getDate(row)
            prevBlock = self.calendarWidget.blockSignals(True)
            try:
                self.calendarWidget.setSelectedDate(date)
            finally:
                self.calendarWidget.blockSignals(prevBlock)
            self.updateQueueEx(self.tblHomeTimeTable,
                               self.modelHomeTimeTable,
                               self.selectionModelHomeTimeTable,
                               self.tblHomeQueue,
                               self.modelHomeQueue)


    @pyqtSignature('')
    def on_actHomeCreateOrder_triggered(self):
        self.createOrder(self.tblHomeTimeTable, self.tblHomeQueue, QtGui.qApp.currentClientId())
    
    
    @pyqtSignature('')
    def on_actHomeCreateOrderUrgent_triggered(self):
        self.createOrder(self.tblHomeTimeTable, self.tblHomeQueue, QtGui.qApp.currentClientId(), isUrgent = 1)


    @pyqtSignature('')
    def on_actHomeDeleteOrder_triggered(self):
        self.deleteOrder(self.tblHomeTimeTable, self.tblHomeQueue)


    @pyqtSignature('')
    def on_actHomeChangeComplaint_triggered(self):
        self.changeComplaint(self.tblHomeQueue)
        QtGui.qApp.emitCurrentClientInfoChanged()


    @pyqtSignature('')
    def on_actHomeChangeReferral_triggered(self):
        self.changeReferral(self.tblHomeQueue)
        QtGui.qApp.emitCurrentClientInfoChanged()


    @pyqtSignature('')
    def on_actHomePrintOrder_triggered(self):
        self.printOrder(self.tblHomeQueue)


    @pyqtSignature('int')
    def on_actHomePrintOrderByTemplate_printByTemplate(self, templateId):
        self.printOrderByTemplate(self.tblHomeQueue, templateId)


    @pyqtSignature('')
    def on_actHomePrintQueue_triggered(self):
        self.printQueue(self.tblHomeQueue, 2)


    @pyqtSignature('')
    def on_actHomePrintQueuePass_triggered(self):
        nameMenuPrintQueue = u', список переданных врачу'
        self.printQueue(self.tblHomeQueue, 0, nameMenuPrintQueue)


    @pyqtSignature('')
    def on_actHomePrintQueueNoPass_triggered(self):
        nameMenuPrintQueue = u', список непереданных врачу'
        self.printQueue(self.tblHomeQueue, 1, nameMenuPrintQueue)


    @pyqtSignature('int')
    def on_actHomePrintQueueByTemplate_printByTemplate(self, templateId):
        self.printQueueByTemplate(self.tblHomeQueue, templateId)


    @pyqtSignature('')
    def on_actHomeFindClient_triggered(self):
        clientId = self.getCurrentQueuedClientId(self.tblHomeQueue)
        QtGui.qApp.findClient(clientId)


    @pyqtSignature('')
    def on_actHomeFindClientEvents_triggered(self):
        clientId = self.getCurrentQueuedClientId(self.tblHomeQueue)
        QtGui.qApp.findClient(clientId)
        QtGui.qApp.mainWindow.registry.tabMain.setCurrentIndex(1)


# какое редкостное Г..., нужно вынести построение отчёта из этого модуля
    @pyqtSignature('')
    def on_actServiceReport_triggered(self):
        db = QtGui.qApp.db
        currentDate = self.getCurrentDate()
        personId = self.getCurrentPersonId()
        specialityId = self.getPersonSpecialityId(personId)

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Сводка об обслуживании на '+forceString(currentDate)+'\n')
        cursor.insertBlock()

        cursor.setCharFormat(CReportBase.ReportBody)
        personInfo = self.getPersonInfo(personId)
        specialityId=personInfo['specialityId']

        cursor.insertText(u'врач: %s, %s\n' % (personInfo['fullName'], personInfo['specialityName']))
        cursor.insertText(u'подразделение: %s, %s\n' % (personInfo['orgStructureName'], personInfo['postName']))
        cursor.insertText(u'дата формирования: %s\n' % forceString(QDate.currentDate()))
        cursor.insertBlock()

        cols = [
            ('2%',  [u'№'], CReportBase.AlignRight),
            ('4%',  [u'Время записи'], CReportBase.AlignLeft),
            ('10%', [u'ФИО'], CReportBase.AlignLeft),
            ('4%',  [u'Д/р'], CReportBase.AlignLeft),
            ('3%',  [u'Возраст'], CReportBase.AlignLeft),
            ('1%',  [u'Пол'], CReportBase.AlignLeft),
            ('10%', [u'Адрес'], CReportBase.AlignLeft),
            ('10%', [u'Полис'], CReportBase.AlignLeft),
            ('10%', [u'Паспорт'], CReportBase.AlignLeft),
            ('10%', [u'СНИЛС'], CReportBase.AlignLeft),
            ('10%', [u'Врач'], CReportBase.AlignLeft),
            ('4%',  [u'Время обслуживания'], CReportBase.AlignLeft),
            ('7%',  [u'Тип'], CReportBase.AlignLeft),
            ('5%',  [u'Диагноз'], CReportBase.AlignLeft),
            ('10%', [u'Результат'], CReportBase.AlignLeft),
           ]
        table = createTable(cursor, cols)
        cnt = 0

        isAmb = (self.tabPlace.currentIndex() == 0)  # амбулаторно - 0, на дому - 1
        modelQueue = (self.modelAmbQueue if isAmb else self.modelHomeQueue)
        clients = []
        for scheduleItem in modelQueue.scheduleItems:
            clientId = scheduleItem.clientId
            if clientId:
                clients.append((clientId, scheduleItem.time))

        numSame = 0
        numOther = 0
        numWithoutVisit = 0
        for (clientId, time) in clients:
            i = table.addRow()
            cnt += 1
            table.setText(i, 0, i)
            clientInfo = getClientInfoEx(clientId, currentDate)
            table.setText(i, 2, clientInfo['fullName'])
            table.setText(i, 3, clientInfo['birthDateStr'])
            table.setText(i, 4, clientInfo['age'])
            table.setText(i, 5, clientInfo['sex'])
            table.setText(i, 6, clientInfo['regAddress'])
            table.setText(i, 7, clientInfo['policy'])
            table.setText(i, 8, clientInfo['document'])
            table.setText(i, 9, clientInfo['SNILS'])
            stmt = """
SELECT
    Person.id AS person_id,
    Diagnosis.MKB,
    Visit.date,
    Event.result_id,
    rbDiagnosticResult.name AS result,
    rbScene.name AS scene,
    Visit.createDatetime,
    Person.speciality_id
FROM
    Visit
    JOIN Event ON Event.id=Visit.event_id
    JOIN Person ON Person.id=Visit.person_id
    LEFT JOIN Diagnosis on Diagnosis.id=getEventPersonDiagnosis(Event.id, Person.id)
    LEFT JOIN Diagnostic ON Diagnosis.id = Diagnostic.diagnosis_id and Diagnostic.event_id = Event.id
    LEFT JOIN rbDiagnosticResult ON rbDiagnosticResult.id=Diagnostic.result_id
    LEFT JOIN rbScene ON rbScene.id = Visit.scene_id
WHERE
    Visit.deleted = 0
AND Event.deleted = 0
AND (Person.id=%(personId)d OR Person.speciality_id=%(specialityId)d)
AND DATE(Visit.date) = %(visitDate)s
AND Event.client_id=%(clientId)d
ORDER BY (Person.id=%(personId)d), Event.id desc, Visit.id desc
limit 0,1""" % {'personId'    : personId,
              'specialityId': specialityId,
              'visitDate'   : db.formatDate(currentDate),
              'clientId'    : clientId,
             }
            query = db.query(stmt)
            withoutVisit = True
            table.setText(i, 1, formatTime(time) if time else '--:--')
            if query.first():
                record = query.record()
                visitPersonId = forceRef(record.value('person_id'))
                if visitPersonId:
                    visitPersonInfo = self.getPersonInfo(visitPersonId)
                    if visitPersonInfo:
                        table.setText(i, 10, visitPersonInfo['fullName'])
                    table.setText(i, 11, formatTime(record.value('createDatetime').toTime()))
                    table.setText(i, 12, forceString(record.value('scene')))
                    table.setText(i, 13, forceString(record.value('MKB')))
                    table.setText(i, 14, forceString(record.value('result')))
                    if personId == visitPersonId:
                        numSame += 1
                    elif forceRef(record.value('speciality_id')) == specialityId:
                        numOther += 1
                    withoutVisit = False
            if withoutVisit:
                numWithoutVisit += 1
                table.setText(i, 10, '-')
                table.setText(i, 11, '-')
                table.setText(i, 12, '-')
                table.setText(i, 13, '-')
                table.setText(i, 14, '-')

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertText(u'обслужено врачом к которому была запись: %d; обслужено коллегами: %d; не было обслужено: %d\n' % (numSame, numOther, numWithoutVisit))
        reportView = CReportViewDialog(self)
        reportView.setWindowTitle(u'Сводка об обслуживании')
        reportView.setText(doc)
        reportView.exec_()


    @pyqtSignature('')
    def on_actAmbInfo_triggered(self):
        self.showInfo(self.tblAmbQueue)


    @pyqtSignature('')
    def on_actHomeInfo_triggered(self):
        self.showInfo(self.tblHomeQueue)


    @pyqtSignature('')
    def on_actAmbInviteClient_triggered(self):
        self.inviteClient(self.tblAmbQueue)
        QtGui.qApp.emitCurrentClientInfoChanged()


    @pyqtSignature('')
    def on_actAmbCancelInvitation_triggered(self):
        self.cancelInvitation(self.tblAmbQueue)
        QtGui.qApp.emitCurrentClientInfoChanged()


    @pyqtSignature('')
    def on_actAmbNotification_triggered(self):
        modelQueue = self.modelAmbQueue
        info = [ (scheduleItem.clientId,
                  scheduleItem,
                  modelQueue.getSchedule(row)
                 )
                 for row, scheduleItem in enumerate(modelQueue.scheduleItems)
                 if scheduleItem.clientId
               ]
        CNotifyDialog(info,
                      type = CNotificationRule.ntSchedule,
                     ).exec_()


    @pyqtSignature('bool')
    def on_chkShowSchedulesForSelectedDate_toggled(self, checked):
        self.isNeededUpdateSchedulesForSelectedDate = True
        self.updateTimeTable()
        self.isNeededUpdateSchedulesForSelectedDate = False


################################################################################


class CTimeTableModel(QAbstractTableModel):
    __pyqtSignals__ = ( 'rowCountChanged()',) # см. примечание 1

    headerText = ( u'Назначение', u'Время', u'Каб', u'План', u'Свободно' )

    def __init__(self, parent, appointmentType):
        QAbstractTableModel.__init__(self, parent)
        self.appointmentType = appointmentType
        self.personId = None
        self.begDate  = None
        self.endDate  = None
        self.activityId = None
        self.schedules = []
        self.redBrush = QtGui.QBrush(Qt.red)
        self.parent = parent


    def columnCount(self, index = None):
        return 5


    def rowCount(self, index = None):
        return len(self.schedules)


    def flags(self, index):
        return Qt.ItemIsSelectable|Qt.ItemIsEnabled


    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return QVariant(self.headerText[section])
        if orientation == Qt.Vertical:
            date = self.schedules[section].date
            if role == Qt.DisplayRole:
                return QVariant(QDate.shortDayName(date.dayOfWeek()))
            elif role == Qt.ToolTipRole:
                if self.begDate:
                    return QVariant(date)
            elif role == Qt.ForegroundRole:
                if date.dayOfWeek()>=6:
                    return QVariant(self.redBrush)
        return QVariant()


    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if role == Qt.DisplayRole:
            schedule = self.schedules[row]
            if column == 0: # Назначение
                appointmentPurposeId = schedule.appointmentPurposeId
                if appointmentPurposeId:
                    return toVariant(self.getAppointmentPurposeName(appointmentPurposeId))
                else:
                    return QVariant()
            if column == 1: # Время
                timeRange = schedule.begTime, schedule.endTime
                reasonOfAbsenceId = schedule.reasonOfAbsenceId
                if reasonOfAbsenceId:
                    return toVariant(formatTimeRange(timeRange)+', '+self.getReasonOfAbsenceCode(reasonOfAbsenceId))
                else:
                    return toVariant(formatTimeRange(timeRange))
            elif column == 2: # Каб
                return toVariant(schedule.office)
            elif column == 3: # План
                return toVariant(schedule.capacity)
            elif column == 4: # Свободно
                return toVariant(schedule.capacity-schedule.getQueuedClientsCount())
        elif role == Qt.FontRole:
            schedule = self.schedules[row]
            if schedule.reasonOfAbsenceId:
                result = QtGui.QFont()
                result.setBold(True)
                result.setStrikeOut(True)
                return QVariant(result)
        return QVariant()


    def setPersonActivityAndDate(self, personId, activityId, date, minDate, maxDate):
        if (self.personId == personId and activityId == self.activityId and self.begDate <= date <= self.endDate) and (not self.parent.isNeededUpdateSchedulesForSelectedDate):
            self.updateData()
        else:
            # self.beginResetModel()
            try:
                self.personId = personId
                self.activityId = activityId
                if self.parent.chkShowSchedulesForSelectedDate.isChecked():
                    self.begDate, self.endDate = date, date
                else:
                    self.begDate = max(date.addDays(1-date.dayOfWeek()), minDate)
                    self.endDate = min(self.begDate.addDays(6), maxDate)
                self.loadData()
            finally:
                #self.endResetModel()
                self.reset()


    def getAppointmentPurposeName(self, appointmentPurposeId):
        return CAppointmentPurposeCache.getName(appointmentPurposeId)


    def getAppointmentPurposeCodeAndName(self, appointmentPurposeId):
        cache = CRBModelDataCache.getData('rbAppointmentPurpose', False)
        text = cache.getStringById(appointmentPurposeId, CRBComboBox.showCodeAndName)
        return text


    def getReasonOfAbsenceCode(self, reasonOfAbsenceId):
        cache = CRBModelDataCache.getData('rbReasonOfAbsence', True)
        text = cache.getStringById(reasonOfAbsenceId, CRBComboBox.showCode)
        return text


    def getRowForDate(self, date, prevRow=-1):
        if 0<=prevRow<len(self.schedules):
            if self.schedules[prevRow].date == date:
                return prevRow
        for row, schedule in enumerate(self.schedules):
            if schedule.date == date:
                return row
        return -1


    def getRowListForDate(self, date):
        result = []
        for row, schedule in enumerate(self.schedules):
            if schedule.date == date:
                result.append(row)
        return result


    def loadSchedules(self, begDate, endDate, personId, activityId):
        if begDate and endDate and personId and QtGui.qApp.db:
            db = QtGui.qApp.db
            tableSchedule = db.table('Schedule')
            tablePerson   = db.table('Person')
            table = tableSchedule.leftJoin(tablePerson, tablePerson['id'].eq(tableSchedule['person_id']))
            cond = [tableSchedule['deleted'].eq(0),
                    tableSchedule['appointmentType'].eq(self.appointmentType),
                    tableSchedule['date'].between(begDate, endDate),
                    tableSchedule['person_id'].eq(personId)
                   ]
            activityPref = QtGui.qApp.getGlobalPreference('23')
            if activityPref == u'да' and activityId:
                cond.append(db.joinOr([tableSchedule['activity_id'].eq(activityId),
                                       tableSchedule['activity_id'].isNull()
                                      ]
                                     )
                           )
            cond.append( '`Person`.`lastAccessibleTimelineDate` IS NULL OR `Person`.`lastAccessibleTimelineDate`=0 OR `Schedule`.`date`<=`Person`.`lastAccessibleTimelineDate`')
            if QtGui.qApp.isTimelineAccessibilityDays() == 1:
                cond.append( '`Person`.`timelineAccessibleDays` <= 0 OR `Schedule`.`date`<=%s'%db.dateAdd('current_date', 'day', 'Person.timelineAccessibleDays'))

            return [CSchedule(record) for record in db.getRecordList(table,
                                                                     'Schedule.*',
                                                                     cond,
                                                                     'Schedule.date, Schedule.begTime, Schedule.id'
                                                                    )
                   ]
        else:
            return []


    def loadDataInt(self):
        return self.loadSchedules(self.begDate, self.endDate, self.personId, self.activityId)


    def loadData(self):
        self.schedules = self.loadDataInt()


    def updateData(self):
        oldList = self.schedules
        self.schedules = self.loadDataInt()
        oldLen = len(oldList)
        newLen = len(self.schedules)
        if oldLen<newLen:
            # добавилось
            self.beginInsertRows(QModelIndex(), oldLen, newLen-1)
            self.endInsertRows()
        elif oldLen>newLen:
            # удалилось
            self.beginRemoveRows(QModelIndex(), newLen, oldLen-1)
            self.endRemoveRows()
        for row in xrange(min(oldLen, newLen)):
            oldSchedule = oldList[row]
            newSchedule = self.schedules[row]
            if oldSchedule != newSchedule:
                self.emitDataChanged(row)


    def updateAvail(self, row):
        index = self.index(row, 4)
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)


    def getDate(self, row):
        if 0<=row<len(self.schedules):
            schedule = self.schedules[row]
            return schedule.date
        else:
            return None


    def getTimeRange(self, row):
        schedule = self.schedules[row]
        return schedule.begTime, schedule.endTime


    def getOffice(self, row):
        schedule = self.schedules[row]
        return schedule.office


    def getSchedule(self, row):
        if 0<=row<len(self.schedules):
            return self.schedules[row]
        else:
            return None


    def findRowForScheduleId(self, scheduleId):
        for row, schedule in enumerate(self.schedules):
            if schedule.id == scheduleId:
                return row
        return -1


    def getCombinableRows(self, row, groupByAppointmentPurposeId):
        if 0 <= row < len(self.schedules):
            schedule = self.schedules[row]
            date = schedule.date
            if groupByAppointmentPurposeId:
                appointmentPurposeId = schedule.appointmentPurposeId
                return [row_
                        for row_, schedule_ in enumerate(self.schedules)
                        if schedule_.date == date and schedule_.appointmentPurposeId == appointmentPurposeId
                       ]
            else:
                return [row_
                        for row_, schedule_ in enumerate(self.schedules)
                        if schedule_.date == date
                       ]
        return []


    def reset(self):                                # см. примечание 1
        QAbstractTableModel.reset(self)             # см. примечание 1
        self.emitRowCountChanged()                  # см. примечание 1


    def endInsertRows(self):                        # см. примечание 1
        QAbstractTableModel.endInsertRows(self)     # см. примечание 1
        self.emitRowCountChanged()                  # см. примечание 1


    def endRemoveRows(self):                        # см. примечание 1
        QAbstractTableModel.endRemoveRows(self)     # см. примечание 1
        self.emitRowCountChanged()                  # см. примечание 1


    def emitRowCountChanged(self):                      # см. примечание 1
        self.emit(SIGNAL('rowCountChanged()'))   # см. примечание 1


    def emitDataChanged(self, row):
        index = self.index(row, 0)
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)


class CQueueModel(QAbstractTableModel):
    __pyqtSignals__ = ('rowCountChanged()',)  # см. примечание 1

    def __init__(self, parent, appointmentType):
        QAbstractTableModel.__init__(self, parent)
        self.appointmentType = appointmentType
        # FIXME: реализовать другой механизм подбора и кеширования специальности
        self.personId = None
        self.personSpecialityId = None
        self.appointmentPurposeId = None
        self.schedules = []
        self.scheduleItems = []
        self.overtimeEnabled = False
        self.mapClientIdToName = {}
        self.getPersonSpecialityId = parent.getPersonSpecialityId
        self.itemsAreCheckable = False
        self.mapClientIdToString = {}
        self.parent = parent


    def setItemsAreCheckable(self, value):
        self.itemsAreCheckable = bool(value)


    def complaintRequired(self):
        return self.appointmentType == CSchedule.atHome


    def columnCount(self, index=None, *args, **kwargs):
        return 2


    def rowCount(self, index=None, *args, **kwargs):
        if self.scheduleItems:
            return len(self.scheduleItems)+(1 if self.overtimeEnabled else 0)
        else:
            return 0


    def realRowCount(self):
        return len(self.scheduleItems)


    def flags(self, index):
        result = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if self.itemsAreCheckable:
            row = index.row()
            if 0 <= row < len(self.scheduleItems):
                item = self.scheduleItems[row]
                if item.clientId:
                    result = result | Qt.ItemIsUserCheckable
        return result


    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                if section == 0:
                    return QVariant(u'ФИО')
                else:
                    return QVariant(u'Назначение')
        if orientation == Qt.Vertical:
            if role == Qt.DisplayRole:
                if 0 <= section < len(self.scheduleItems):
                    item = self.scheduleItems[section]
                    time = None if item.overtime else item.time
                else:
                    time = None
                return QVariant(locFormatTime(time))
            if role == Qt.TextAlignmentRole:
                return QVariant(Qt.AlignRight)
            if role == Qt.ForegroundRole:
                if 0 <= section < len(self.scheduleItems):
                    item = self.scheduleItems[section]
                    if not item.enableQueueing or not self.parent.enableQueueing:
                        return QVariant(QtGui.QBrush(Qt.darkGray))
        return QVariant()


    def getTextForClientId(self, clientId):
        if clientId:
            result = self.mapClientIdToString.get(clientId, False)
            if not result:
                result = getClientMiniInfo(clientId)
                self.mapClientIdToString[clientId] = result
            return result
        return None


    def data(self, index, role=Qt.DisplayRole):
        row = index.row()
        column = index.column()
        item = self.scheduleItems[row] if 0 <= row < len(self.scheduleItems) else None

        if role == Qt.DisplayRole:
            if item:
                if column == 0 and item.clientId:
                    if item.invitation:
                        return toVariant(u'> ' + self.getTextForClientId(item.clientId))
                    else:
                        return toVariant(self.getTextForClientId(item.clientId))
                elif column == 1 or QtGui.qApp.getScheduleFIOAppointment():
                    if item.appointmentPurposeId:
                        cache = CRBModelDataCache.getData('rbAppointmentPurpose', True)
                        text = cache.getStringById(item.appointmentPurposeId, CRBComboBox.showCodeAndName)
                        return QVariant(text)
                    else:
                        return QVariant()
        elif role == Qt.ForegroundRole:
            if (item and not item.enableQueueing) or not self.parent.enableQueueing:
                return QVariant(QtGui.QBrush(Qt.darkGray))

        elif role == Qt.CheckStateRole and column == 0 and self.itemsAreCheckable:
            if item and item.clientId:
                return toVariant(Qt.Checked if item.checked else Qt.Unchecked)
        elif role == Qt.ToolTipRole:
            if item and item.clientId:
                cache = CRBModelDataCache.getData('vrbPersonWithSpeciality', True)
                additionalToolTip = u''
                if item.isUrgent == 1:
                    additionalToolTip = u' неотложно'
                elif item.recordType == 4:
                    additionalToolTip = u' (ТМК (MAX))'
                text = u'Записал: '+cache.getStringById(item.recordPersonId, CRBComboBox.showName) + additionalToolTip
                if item.complaint:
                    text += u'\nЖалобы: '+item.complaint
                if item.note:
                    text += u'\nПримечание: '+item.note
                return toVariant(text)
        elif role == Qt.FontRole:
            if item and item.clientId and item.recordClass == item.rcSamson:
                recordPersonId = item.recordPersonId
                result = QtGui.QFont()
                if self.personId == recordPersonId:
                    result.setBold(True)
                else:
                    recordPersonSpecialityId = self.getPersonSpecialityId(recordPersonId)
                    if recordPersonSpecialityId:
                        result.setItalic(True)
                        if self.personSpecialityId == recordPersonSpecialityId:
                            result.setBold(True)
                return QVariant(result)
        elif role == Qt.DecorationRole:
            if item and item.clientId and column == 0:
                if item.isUrgent:
                    return QVariant(QtGui.QIcon(':/new/prefix1/icons/blueBullet.png'))
                elif item.recordType == 4:
                    return QVariant(QtGui.QIcon(':/new/prefix1/icons/orangeBullet.png'))
                else:
                    if item.recordClass == item.rcSamson:
                        if item.inWaitingArea:
                            return QVariant(QtGui.QIcon(':/new/prefix1/icons/greenBullet.png'))
                        else:
                            return QVariant(QtGui.QColor(Qt.transparent))
                    else:
                        if item.inWaitingArea:
                            return QVariant(QtGui.QIcon(':/new/prefix1/icons/redAndGreenBullet.png'))
                        else:
                            return QVariant(QtGui.QIcon(':/new/prefix1/icons/redBullet.png'))
        return QVariant()


    def setData(self, index, value, role=Qt.EditRole):
        row = index.row()
        item = self.scheduleItems[row] if 0 <= row < len(self.scheduleItems) else None
        if role == Qt.CheckStateRole and self.itemsAreCheckable and item:
            item.checked = forceBool(value)
            item.save()
            if QtGui.qApp.syncCheckableAndInvitiation():
                self.setInvitation(row, forceBool(value))
                self.emitAllDataChanged()
            if item.clientId == QtGui.qApp.currentClientId():
                QtGui.qApp.emitCurrentClientInfoChanged()
            return True
        return False


    def setSchedules(self, schedules):
        if self.schedules == schedules:
            self.updateData()
        else:
            self.schedules = schedules
            self.mapClientIdToString = {}
            if schedules:
                personId = schedules[0].personId
                if self.personId != personId:
                    self.personSpecialityId = forceRef(QtGui.qApp.db.translate('Person', 'id', personId, 'speciality_id'))
                    self.personId = personId
                self.loadData()
            else:
                self.personId = None
                self.personSpecialityId = None
                self.loadData()
            self.reset()


    def collectScheduleItems(self):
        newItems = []
        for schedule in self.schedules:
            newItems.extend(schedule.items)
        newItems.sort(key=lambda scheduleItem: (scheduleItem.overtime, scheduleItem.time))
        for item in newItems:
            appointmentPurposeId = item.appointmentPurposeId
            item.enableQueueing = isAppointmentEnabled(appointmentPurposeId, self.parent.getCurrentPersonId())
        self.scheduleItems = newItems


    def loadData(self):
        self.collectScheduleItems()
        self.overtimeEnabled = len(self.scheduleItems) > 0 and (
            QtGui.qApp.userHasRight(urQueueOverTime) or
            self.personId == QtGui.qApp.userId and QtGui.qApp.userHasRight(urQueueToSelfOverTime)
            )


    def updateData(self):
        if self.schedules:
            oldItems = self.scheduleItems
            oldLen = len(oldItems)
            for schedule in self.schedules:
                schedule.reloadItems()
            self.collectScheduleItems()
            for item in self.scheduleItems:
                appointmentPurposeId = item.appointmentPurposeId
                item.enableQueueing = isAppointmentEnabled(appointmentPurposeId, self.parent.getCurrentPersonId())
            newItems = self.scheduleItems
            newLen = len(newItems)
            if oldLen < newLen:
                # добавилось
                self.beginInsertRows(QModelIndex(), oldLen, newLen-1)
                self.endInsertRows()
            elif oldLen > newLen:
                # удалилось
                self.beginRemoveRows(QModelIndex(), newLen, oldLen-1)
                self.endRemoveRows()
            for row in xrange(min(oldLen, newLen)):
                oldItem = oldItems[row]
                newItem = newItems[row]
                if oldItem.time != newItem.time:
                    self.emitVerticalHeaderChanged(row)
                if oldItem.clientId != newItem.clientId or oldItem.checked != newItem.checked:
                    self.emitDataChanged(row)


    def reset(self):                                # см. примечание 1
        QAbstractTableModel.reset(self)             # см. примечание 1
        self.emitRowCountChanged()                  # см. примечание 1


    def endInsertRows(self):                        # см. примечание 1
        QAbstractTableModel.endInsertRows(self)     # см. примечание 1
        self.emitRowCountChanged()                  # см. примечание 1


    def endRemoveRows(self):                        # см. примечание 1
        QAbstractTableModel.endRemoveRows(self)     # см. примечание 1
        self.emitRowCountChanged()                  # см. примечание 1


    def emitRowCountChanged(self):                  # см. примечание 1
        self.emit(SIGNAL('rowCountChanged()'))      # см. примечание 1


    def emitAllDataChanged(self):
        begIndex = self.index(0, 0)
        endIndex = self.index(self.rowCount(), 0)
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), begIndex, endIndex)


    def emitDataChanged(self, row):
        index = self.index(row, 0)
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)


    def emitVerticalHeaderChanged(self, row):
        self.emit(SIGNAL('headerDataChanged(Qt::Orientation, int, int)'), Qt.Vertical,  row, row)


    def getSchedule(self, row):
        scheduleItem = self.getScheduleItem(row)
        if scheduleItem:
            scheduleId = scheduleItem.scheduleId
            for schedule in self.schedules:
                if schedule.id == scheduleId:
                    return schedule
        return None


    def findScheduleItemRow(self, scheduleItemId):
        for row, item in enumerate(self.scheduleItems):
            if item.id == scheduleItemId:
                return row
        return -1


    def getScheduleItem(self, row):
        if self.scheduleItems and 0 <= row < len(self.scheduleItems):
            return self.scheduleItems[row]
        else:
            return None


    def createOvertimeScheduleItem(self, schedule):
        result = CScheduleItem()
        result.scheduleId = schedule.id
        result.time = QDateTime(schedule.date, schedule.endTime)
        result.appointmentPurposeId = schedule.appointmentPurposeId
        result.overtime = True
        return result

    def getTime(self, row):
        item = self.getScheduleItem(row)
        if item and not item.overtime:
            return item.time
        else:
            return QDateTime()


    def isChecked(self, row):
        item = self.getScheduleItem(row)
        return item.checked if item else None


    def setChecked(self, row, checked):
        item = self.getScheduleItem(row)
        if item:
            item.checked = checked
            item.save()


    def findClientRow(self, clientId):
        for row, item in enumerate(self.scheduleItems):
            if item.clientId == clientId:
                return row
        return -1


    def getClientId(self, row):
        item = self.getScheduleItem(row)
        return item.clientId if item else None


    def getClientText(self, row):
        clientId = self.getClientId(row)
        return self.getTextForClientId(clientId) if clientId else None


    def getComplaint(self, row):
        item = self.getScheduleItem(row)
        return item.complaint if item else None


    def setComplaint(self, row, complaint):
        item = self.getScheduleItem(row)
        if item:
            item.complaint = complaint
            item.save()


    def getInvitation(self, row):
        item = self.getScheduleItem(row)
        return item.invitation if item else None


    def setInvitation(self, row, invitation):
        item = self.getScheduleItem(row)
        if item:
            item.invitation = invitation
            item.save()
            if invitation:
                for i, item in enumerate(self.scheduleItems):
                    if i != row and item.clientId and item.invitation:
                        item.invitation = False
                        item.save()


#    def cancelInvitation(self, row):
#        item = self.getScheduleItem(row)
#        if item:
#            item.invitation = False
#            item.save()


    def getReferral(self, row):
        referral = CReferral()
        item = self.getScheduleItem(row)
        if item:
            referral.srcOrgId        = item.srcOrgId
            referral.srcPerson       = item.srcPerson
            referral.srcSpecialityId = item.srcSpecialityId
            referral.srcNumber       = item.srcNumber
            referral.srcDate         = item.srcDate
        return referral


    def setReferral(self, row, referral):
        item = self.getScheduleItem(row)
        if item:
            item.srcOrgId        = referral.srcOrgId
            item.srcPerson       = referral.srcPerson
            item.srcSpecialityId = referral.srcSpecialityId
            item.srcNumber       = referral.srcNumber
            item.srcDate         = referral.srcDate
            item.save()


    def getQueuedClientsCount(self):
        return sum(schedule.getQueuedClientsCount() for schedule in self.schedules)


#    def getExternalQueuedCount(self):
#        assert False
#        # внешняя запись:
#        result = 0
#        for item in self.schedule.items:
#            if (    item.clientId
#                and item.recordClass != CScheduleItem.rcSamson
#               ):
#                result += 1
#        return result


    def getQueuedCount(self, row):
        # количество записанных по Schedule из заданной строки
        def getOwnQueuedCount(schedule):
            # записано из самсона самим пользователем по заданному schedule
            return sum(1
                       for item in schedule.items
                       if      item.clientId
                and item.recordClass == CScheduleItem.rcSamson
                and item.recordPersonId == QtGui.qApp.userId
                      )

        def getConsultancyQueuedCount(schedule):
        # консультативная запись:
            # записано из самсона пользователем со специальностью по заданному schedule
            return sum(1
                       for item in schedule.items
                       if     item.clientId
                and item.recordClass == CScheduleItem.rcSamson
                and self.getPersonSpecialityId(item.recordPersonId)
                          and item.recordPersonId != schedule.personId
                      )

        def getPrimaryQueuedCount(schedule):
            # первичная запись:
            # recordClass = самсон и записавшее лицо не имеет специальности
            return sum(1
                       for item in schedule.items
                       if     item.clientId
                          and item.recordClass == CScheduleItem.rcSamson
                          and self.getPersonSpecialityId(item.recordPersonId) is None
                      )

        specialityId = QtGui.qApp.userSpecialityId
        schedule = self.getSchedule(row)
        if specialityId:
            if schedule.personId == QtGui.qApp.userId:
                return getOwnQueuedCount(schedule)
            else:
                return getConsultancyQueuedCount(schedule)
        else:
            return getPrimaryQueuedCount(schedule)


# ######################################################################


def locFormatTime(time):
    return time.toString('H:mm') if time else '--:--'


def getQuota(personId, count):
    # def divideQoutes(quotes, enablements):
    #     assert len(quotes) == len(enablements)
    #
    #     t = sum(enablements)
    #     if t == len(quotes):
    #         return quotes
    #     elif t == 0:
    #         return [0.0]*len(quotes)
    #     elif t == 1:
    #         return [ 100.0 if enable else 0.0 for enable in enablements ]
    #     else:
    #         enabled = disabled = 0.0
    #         for i, enable in enumerate(enablements):
    #             if enable:
    #                enabled += quotes[i]
    #             else:
    #                disabled += quotes[i]
    #         if enabled>0:
    #             for i, enable in enumerate(enablements):
    #                 if enable:
    #                    quotes[i] += disabled*quotes[i]/enabled
    #                 else:
    #                    quotes[i] = 0.0
    #         return quotes

    db = QtGui.qApp.db
    table = db.table('Person')
    record = db.getRecord(table, ['ownQuota', 'consultancyQuota', 'primaryQuota', 'externalQuota'], personId)
    if not record:
        return 0

    quotes = [ forceDouble(record.value('ownQuota')),
               forceDouble(record.value('consultancyQuota')),
               forceDouble(record.value('primaryQuota')),
               forceDouble(record.value('externalQuota'))
             ]

    # appointmentPurpose = CAppointmentPurposeCache.getItem(appointmentPurposeId)
    # if appointmentPurpose:
    #     enablements = (appointmentPurpose.enableOwnRecord,
    #                    appointmentPurpose.enableConsultancyRecord,
    #                    appointmentPurpose.enablePrimaryRecord,
    #                    appointmentPurpose.enableRecordViaInfomat or appointmentPurpose.enableRecordViaCallCenter or appointmentPurpose.enableRecordViaInternet
    #                   )
    #     quotes = divideQoutes(quotes, enablements)

    if personId == QtGui.qApp.userId:
        quota = quotes[0]
    elif QtGui.qApp.userSpecialityId:
        quota = quotes[1]
    else:
        quota = quotes[2]
    return math.ceil(quota*count/100.0)


def isAppointmentEnabled(appointmentPurposeId, personId):
    appointmentPurpose = CAppointmentPurposeCache.getItem(appointmentPurposeId)
    if appointmentPurpose:
        if personId == QtGui.qApp.userId:
            return appointmentPurpose.enableOwnRecord
        elif forceRef(QtGui.qApp.db.translate('rbPost', 'id', QtGui.qApp.userPostId, 'code')) == 6000:
            return appointmentPurpose.enableRecordViaCallCenter
        elif QtGui.qApp.userSpecialityId:
            return appointmentPurpose.enableConsultancyRecord
        else:
            return appointmentPurpose.enablePrimaryRecord
    else:
        return True


def isAppointmentEnabledForClient(appointmentPurposeId, personId, date, clientId):
    appointmentPurpose = CAppointmentPurposeCache.getItem(appointmentPurposeId)
    if appointmentPurpose:
        if clientId:
            db = QtGui.qApp.db
            clientRecord = db.getRecord('Client', ('sex', 'birthDate'), clientId)
            clientSex = forceInt(clientRecord.value('sex'))
            clientAge = calcAgeTuple(forceDate(clientRecord.value('birthDate')), date)
            if not appointmentPurpose.applicable(clientSex, clientAge):
                return False

        if personId == QtGui.qApp.userId:
            return appointmentPurpose.enableOwnRecord
        elif forceRef(QtGui.qApp.db.translate('rbPost', 'id', QtGui.qApp.userPostId, 'code')) == 6000:
            return appointmentPurpose.enableRecordViaCallCenter
        elif QtGui.qApp.userSpecialityId:
            return appointmentPurpose.enableConsultancyRecord
        else:
            return appointmentPurpose.enablePrimaryRecord
    return True

def isAppointmentEnabledForDate(scheduleItem, personId):
    db = QtGui.qApp.db
    id_ = scheduleItem.id if scheduleItem.id else '-1'
    isAvalibleForExternal = forceBool(db.translate('Person', 'id', personId, 'availableForExternal'))
    table = db.table('GetPositionList')
    record = db.getRecordEx(table, table['id'], [table['code_last'].eq(14), table['code'].eq(getPostIdentCodeByPersonId(personId))])
    isInListForInterofficeRecord = True if record and forceRef(record.value('id')) else False
    isInterofficeRecord = not isAvalibleForExternal or isInListForInterofficeRecord
    AppointmentPerson = db.getRecord('Schedule', ('Schedule.date<=%s or (Schedule.date<=%s and Schedule.person_id = %s  AND (SELECT ap.enablePrimaryRecord = 0  AND ap.enableConsultancyRecord = 0  AND ap.enableRecordViaInfomat  = 0  AND ap.enableRecordViaCallCenter = 0  AND ap.enableRecordViaInternet = 0  FROM Schedule_Item si LEFT JOIN rbAppointmentPurpose ap ON si.appointmentPurpose_id = ap.id  WHERE si.id= %s) ) or (SELECT f.code IS not NULL and f.code!=2 FROM Schedule_Item si LEFT JOIN rbAppointmentPurpose ap ON si.appointmentPurpose_id = ap.id   LEFT JOIN rbFinance f ON ap.finance_id = f.id WHERE si.id=%s) as check_' % (db.dateAdd('current_date', 'day', '14') if not isInterofficeRecord else db.dateAdd('current_date', 'day', '30'),db.dateAdd('current_date', 'day', '120'), QtGui.qApp.userId, id_, id_)),forceInt(scheduleItem.record.value('master_id')))
    check = forceInt(AppointmentPerson.value('check_'))
    return check

def isReferralRequired(appointmentPurposeId):
    appointmentPurpose = CAppointmentPurposeCache.getItem(appointmentPurposeId)
    if appointmentPurpose:
        return appointmentPurpose.requireReferral
    return False


def getPostIdentCodeByPersonId(personId):
    db = QtGui.qApp.db

    tablePost = db.table('rbPost')
    tablePerson = db.table('Person')
    tablePostIdentification = db.table('rbPost_Identification')
    tableAccountingSystem = db.table('rbAccountingSystem')

    table = tablePost.leftJoin(tablePerson, tablePost['id'].eq(tablePerson['post_id']))
    table = table.leftJoin(tablePostIdentification, tablePost['id'].eq(tablePostIdentification['master_id']))
    table = table.leftJoin(tableAccountingSystem, tablePostIdentification['system_id'].eq(tableAccountingSystem['id']))

    cond = [
        tableAccountingSystem['urn'].eq('urn:oid:1.2.643.5.1.13.13.11.1002'),
        tablePerson['id'].eq(personId)
    ]

    postRecord = db.getRecordEx(table, tablePostIdentification['value'], cond)
    if postRecord:
        return forceRef(postRecord.value('value'))
    return None


def checkInterofficeRecord(self, personId, scheduleItem=None):
    if QtGui.qApp.isReStagingInQueue():
        return True
    db = QtGui.qApp.db
    postIdentificationCode = getPostIdentCodeByPersonId(personId)
    appointmentPurpose = CAppointmentPurposeCache.getItem(scheduleItem.appointmentPurposeId)

    if scheduleItem and appointmentPurpose:
        recordFinance = getScheduleItemIdFinance(scheduleItem)
        if recordFinance and (forceString(recordFinance.value('code')) != '' and forceString(recordFinance.value('code')) != '2'):
            return True

    if not self.postForMainLogicRecord and not self.postForInterofficeRecord:
        records = db.getRecordList('GetPositionList', ['code_last', 'code'], 'code_last IN (13,14)')
        for record in records:
            if record.value('code_last') == 13:
                self.postForMainLogicRecord.append(forceRef(record.value('code')))
            else:
                self.postForInterofficeRecord.append(forceRef(record.value('code')))

    if getPostIdentCodeByPersonId(QtGui.qApp.userId) in self.postForInterofficeRecord:
        QtGui.QMessageBox.warning(self, u'Внимание!', u'Для вашей специальности запрещена запись в график!')
        return False

    if postIdentificationCode in self.postForMainLogicRecord:
        isExternal = forceBool(QtGui.qApp.db.translate('Person', 'id', personId, 'availableForExternal'))
        if not isExternal:
            if appointmentPurpose and (not appointmentPurpose.enablePrimaryRecord
                    and not appointmentPurpose.enableConsultancyRecord
                    and not appointmentPurpose.enableRecordViaInfomat
                    and not appointmentPurpose.enableRecordViaCallCenter
                    and not appointmentPurpose.enableRecordViaInternet
                    and appointmentPurpose.enableOwnRecord):
                return True
            else:
                if personId == QtGui.qApp.userId:
                    QtGui.QMessageBox.warning(self, u'Внимание!', u'Возможна только межкабинетная запись!')
                    return False
                elif forceRef(db.translate('rbPost', 'id', QtGui.qApp.userPostId, 'code')) == 6000 or not QtGui.qApp.userSpecialityId:
                    QtGui.QMessageBox.warning(self, u'Внимание!', u'Запись доступна только врачу!')
                    return False
                elif not appointmentPurpose or appointmentPurpose.enableConsultancyRecord:
                    return True
                else:
                    QtGui.QMessageBox.warning(self, u'Внимание!',
                                              u'В назначении приёма отсутствует разрешение на запись для консультации!')
                    return False
        else:
            return True
    elif postIdentificationCode in self.postForInterofficeRecord:
        if personId == QtGui.qApp.userId:
            QtGui.QMessageBox.warning(self, u'Внимание!', u'Для вашей специальности запрещена запись в график!')
            return False
        elif forceRef(db.translate('rbPost', 'id', QtGui.qApp.userPostId, 'code')) == 6000 or not QtGui.qApp.userSpecialityId:
            QtGui.QMessageBox.warning(self, u'Внимание!', u'Запись доступна только врачу!')
            return False
        elif not appointmentPurpose or appointmentPurpose.enableConsultancyRecord:
            return True
        else:
            QtGui.QMessageBox.warning(self, u'Внимание!',
                                      u'В назначении приёма отсутствует разрешение на запись для консультации!')
            return False

    return True


class CActivityTreeItem(CTreeItemWithId):
    def __init__(self, parent, name, id):
        CTreeItemWithId.__init__(self, parent, name, id)


    def loadChildren(self):
        return []


class CActivityRootTreeItem(CActivityTreeItem):
    def __init__(self):
        CActivityTreeItem.__init__(self, None, u'-', None)


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


class CActivityModel(CTreeModel):
    def __init__(self, parent=None):
        CTreeModel.__init__(self, parent, CActivityRootTreeItem())
        self.rootItemVisible = False


    def reload(self):
        self._rootItem.loadChildren()
        self.reset()


    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            return QVariant(u'Виды деятельности')
        return QVariant()


class CResourcesPersonnelModelMixin(object):
    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        if role != Qt.DisplayRole:
            if role == Qt.ToolTipRole:
                personIdList = self.getItemIdList(index)
                if personIdList and len(personIdList) == 1:
                    text = self.getPersonStr(personIdList[0])
                    return toVariant(text)
            elif role == Qt.FontRole:
                item = index.internalPointer()
                if len(item._items) > 0:
                    ret = QtGui.QFont()
                    ret.setBold( 1 )
                    return ret
            else:
                return QVariant()
        item = index.internalPointer()
        return item.data(index.column())


    def getPersonStr(self, id):
        result = []
        if id:
            personInfo = getPersonInfo(id)
            result.append( personInfo['fullName'] )
            if personInfo['specialityName']:
                result.append(personInfo['specialityName'])
            if personInfo['orgStructureName']:
                result.append(u'подразделение: ' + personInfo['orgStructureName'])
            if personInfo['postName']:
                result.append(u'должность: ' + personInfo['postName'])
            if personInfo['tariffCategoryName']:
                result.append(u'категория: ' + personInfo['tariffCategoryName'])
        return ', '.join(result)


class CFlatResourcesPersonnelModel(CResourcesPersonnelModelMixin, CFlatOrgPersonnelModel):
    pass


class CResourcesPersonnelModel(CResourcesPersonnelModelMixin, COrgPersonnelModel):
    pass


class CQueueItemInfo(CInfo):
    def __init__(self, context, time, clientId, checked, complaint, recordPersonId, recordDatetime, overtime=None):
        CInfo.__init__(self, context)
        self.setOkLoaded()
        self._clientId = clientId
        self.time = CTimeInfo(time)
        self.client = self.getInstance(CClientInfo, clientId)
        self.checked = checked
        self.complaints = complaint
        self.overtime = overtime
        self.recordDatetime = CDateTimeInfo(recordDatetime)
        self.setPerson = self.getInstance(CPersonInfo, recordPersonId)

    def __nonzero__(self):
        return self._clientId is not None

