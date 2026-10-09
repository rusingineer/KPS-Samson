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

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QDate, QDateTime, QObject, QSize, QTimer, QVariant, pyqtSignature, SIGNAL

from Users.Rights import urQueueingOutreaching, urAdmin
from library.DialogBase       import CConstructHelperMixin
from library.DockWidget       import CDockWidget
from library.InDocTable       import CRecordListModel, CDateInDocTableCol, CTimeInDocTableCol, CRBInDocTableCol, CInDocTableCol
from library.PreferencesMixin import CPreferencesMixin, CContainerPreferencesMixin
from library.RecordLock       import CRecordLockMixin
from library.Utils            import forceBool, forceDate, forceDateTime, forceInt, forceRef, forceString, forceTime, formatNum, getPref, setPref, toVariant, calcAgeTuple

from Events.Utils             import getDeathDate
from Orgs.OrgStructComboBoxes import COrgStructureModel
from Orgs.Utils import findOrgStructuresByAddress, getPersonInfo

from Registry.BeforeRecordClient          import printOrderByScheduleItem
from Registry.ReferralEditDialog          import inputReferral
from Registry.HomeCallRequestsWindow      import CHomeCallRequestsWindow
from Registry.RegistrySuspenedAppointment import setRegistrySuspenedAppointment
from Registry.RegistryProphylaxisPlanning import setRegistryProphylaxisPlanningList
from Registry.ResourcesDock import (CActivityModel,
                                    CResourcesPersonnelModel,
                                    CFlatResourcesPersonnelModel,
                                    getQuota,
                                    isAppointmentEnabledForClient,
                                    isReferralRequired, isAppointmentEnabledForDate, checkInterofficeRecord
                                    )
from Registry.Utils                       import getClientAddressEx, CCheckNetMixin, getClientAttachEx, createRelatedActionTMK
from Timeline.Schedule import CSchedule, CScheduleItem, getScheduleItemIdListForClient, getScheduleItemIdFinance, \
    getExceptionSpecialty, getScheduleItemIdListForClient_OMS, getDynamicItemType, checkIsNKTReservedForTMK

from Registry.Ui_FreeQueueDockContent  import Ui_Form
from library.crbcombobox import CRBComboBox


class CFreeQueueDockWidget(CDockWidget):
    def __init__(self, parent):
        CDockWidget.__init__(self, parent)
        self.setWindowTitle(u'Номерки')
        self.setFeatures(QtGui.QDockWidget.AllDockWidgetFeatures)
        self.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
        self.content = None
        self.contentPreferences = {}
        self.connect(QtGui.qApp, SIGNAL('dbConnectionChanged(bool)'), self.onConnectionChanged)
        self.setVisible(False)


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


    def setFilter(self, appointmentType, orgStructureId, specialityId, personId, begDate):
        if isinstance(self.content, CFreeQueueDockContent):
            self.content.setFilter(appointmentType, orgStructureId, specialityId, personId, begDate)


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
            self.content = None
        if self.isVisible():
            self.content = CFreeQueueDockContent(self)
            self.content.loadPreferences(self.contentPreferences)
            self.setWidget(self.content)
            self.emit(SIGNAL('contentCreated(QDockWidget*)'), self)


    def onDBDisconnected(self):
        self.setWidget(None)
        if self.content:
            self.updateContentPreferences()
            self.content.setParent(None)
            self.content.deleteLater()
            self.content = None
        if self.isVisible():
            self.content = QtGui.QLabel(u'необходимо\nподключение\nк базе данных', self)
            self.content.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            self.content.setDisabled(True)
            self.setWidget(self.content)
        self.emit(SIGNAL('contentDestroyed(QDockWidget*)'), self)


    def showEvent(self, event):
        if not self.content:
            self.onConnectionChanged(bool(QtGui.qApp.db))


class CFreeQueueDockContent(QtGui.QWidget, Ui_Form, CConstructHelperMixin, CContainerPreferencesMixin, CCheckNetMixin, CRecordLockMixin):
    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)
        CCheckNetMixin.__init__(self)
        CRecordLockMixin.__init__(self)

        self.updateQueueTableLockCnt = 0 # Запрещаю обновление во время работы конструктора

        self.groupingSpeciality = forceBool(QtGui.qApp.preferences.appPrefs.get('groupingSpeciality', True))
        self.activityListIsShown = forceBool(QtGui.qApp.preferences.appPrefs.get('activityListIsShown', False))
        orgStructureFilter = None
        if QtGui.qApp.preferences.appPrefs.get('TimetableOrgStructureCheckedNames'):
            preferenceFilter = [forceInt(checkedId) for checkedId in QtGui.qApp.preferences.appPrefs.get('TimetableOrgStructureCheckedNames').toList()]
            if preferenceFilter:
                orgStructureFilter = 'OrgStructure.id NOT IN ({0})'.format(','.join(map(str, preferenceFilter)))

        self.addModels('OrgStructure', COrgStructureModel(self, QtGui.qApp.currentOrgId(), filter=orgStructureFilter))
        self.addModels('Activity',     CActivityModel(self))
        self.addModels('AmbQueue',     CQueueModel(self))

        self.addObject('actFindArea',       QtGui.QAction(u'Найти участок', self))
        self.addObject('actAmbCreateOrder', QtGui.QAction(u'Поставить в очередь', self))
        self.addObject('actAmbCreateOrderUrgent', QtGui.QAction(u'Поставить в очередь неотложно', self))
        self.addObject('actAmbCreateOrderTMK', QtGui.QAction(u'Поставить в очередь на ТМК', self))
        self.addObject('actAmbReserveOrder', QtGui.QAction(u'Выполнить бронирование', self))
        self.addObject('actAmbUnreserveOrder', QtGui.QAction(u'Отменить бронирование', self))
        self.addObject('actRegistrySuspenedAppointment', QtGui.QAction(u'Зарегистрировать пациента в Журнале отложной записи', self))
        self.addObject('actRegistryProphylaxisPlanning', QtGui.QAction(u'Зарегистрировать пациента в Журнале планирования профилактического наблюдения', self))

        self.timer = QTimer(self)
        self.timer.setObjectName('timer')
        self.timer.setInterval(60*1000) # раз в минуту
        self.timerCountMinute = 0

        self.setupUi(self)

        self.cmbAppointmentType.addItem(CSchedule.atNames[CSchedule.atAmbulance], CSchedule.atAmbulance)
        self.cmbAppointmentType.addItem(CSchedule.atNames[CSchedule.atHome], CSchedule.atHome)
        self.cmbAppointmentType.setValue(CSchedule.atAmbulance)

        self.cmbAppointmentPurpose.setTable('rbAppointmentPurpose')
        for treeWidget in (self.treeOrgStructure, self.treeOrgPersonnel):
            treeWidget.setIndentation(12)
            treeWidget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        verticalHeader = self.tblAmbQueue.verticalHeader()
#        verticalHeader.show()
        verticalHeader.setResizeMode(QtGui.QHeaderView.Fixed)
        self.setModels(self.tblAmbQueue,      self.modelAmbQueue,     self.selectionModelAmbQueue)

        self.connect(QtGui.qApp.mainWindow, SIGNAL('dockWidgetCreated(QDockWidget*)'), self.onDockWidgetCreate)
        dockResources = QtGui.qApp.mainWindow.dockResources
        if dockResources:
            self.connect(dockResources, SIGNAL('contentCreated(QDockWidget*)'), self.onResourcesDockContentCreate)
            self.connect(dockResources, SIGNAL('contentDestroyed(QDockWidget*)'), self.onResourcesDockContentDestroy)
            self.connect(dockResources, SIGNAL('visibilityChanged(QDockWidget*, bool)'), self.onResourcesDockVisibilityChange)
            if dockResources.content:
                self.connect(dockResources.content, SIGNAL('appointmentTypeChanged(int)'), self.onResourcesDockAppointmentTypeChange)
        self.resourcesAtHomeSelected = bool(dockResources and dockResources.isVisible() and dockResources.content and dockResources.content.appointmentType == CSchedule.atHome)

        self.connect(QtGui.qApp.mainWindow.centralWidget, SIGNAL('mdiSubwindowShow(QWidget*)'), self.onSubwindowShow)
        self.connect(QtGui.qApp.mainWindow.centralWidget, SIGNAL('mdiSubwindowClose(QWidget*)'), self.onSubwindowClose)
        homeCallRequests = QtGui.qApp.mainWindow.homeCallRequests
        self.homeCallRequestsVisible = bool(homeCallRequests and homeCallRequests.isVisible())

        self.modelAmbQueue.appointmentType = self.getAppointmentType()

        self.setPersonnelWidgetMode(self.groupingSpeciality)

        self.treeOrgStructure.createPopupMenu([self.actFindArea])
        self.tblAmbQueue.createPopupMenu([self.actAmbCreateOrder, self.actAmbCreateOrderUrgent, self.actAmbCreateOrderTMK, self.actAmbReserveOrder, self.actAmbUnreserveOrder])
        self.setOrgStructureWidgetMode(self.activityListIsShown)

        self.cmbAppointmentType.setValue(CSchedule.atAmbulance)
        self.setDateRange()
        self.onCurrentUserIdChanged()

        self.connect(self.treeOrgStructure.popupMenu(), SIGNAL('aboutToShow()'), self.popupMenuTreeOrgStructureAboutToShow)
        self.connect(self.tblAmbQueue.popupMenu(), SIGNAL('aboutToShow()'), self.popupMenuAmbAboutToShow)

        self.treeOrgPersonnel.createPopupMenu([self.actRegistrySuspenedAppointment, self.actRegistryProphylaxisPlanning])
        self.connect(self.treeOrgPersonnel.popupMenu(), SIGNAL('aboutToShow()'), self.popupMenuOrgPersonnelAboutToShow)
        self.treeOrgStructureHeader = self.treeOrgStructure.header()
        self.treeOrgStructureHeader.setClickable(True)
        QObject.connect(self.treeOrgStructureHeader, SIGNAL('sectionClicked(int)'), self.onOSTreeHeaderClicked)

        self.treeOrgPersonnel.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.personnelTreeHeader = self.treeOrgPersonnel.header()
        self.personnelTreeHeader.setClickable(True)
        QObject.connect(self.personnelTreeHeader, SIGNAL('sectionClicked(int)'),
                               self.onPersonnelTreeHeaderClicked)

        self.connect(QtGui.qApp, SIGNAL('currentOrgIdChanged()'), self.onCurrentOrgIdChanged)
        self.connect(QtGui.qApp, SIGNAL('currentUserIdChanged()'), self.onCurrentUserIdChanged)

        self.prevClientId = None
        self.prevComplaints = ''
        self.reservedRow = -1

        toUpdate = self.updateQueueTableLockCnt
        self.updateQueueTableLockCnt = None
        if toUpdate:
            self.updateQueueTable()

        self.postForMainLogicRecord = []
        self.postForInterofficeRecord = []

        # Сложно было придумать название, так что сделаю примерно как и 2 других списков должностей
        # Должности с которым нужно проверять резерв НКТ талонов для ТМК
        self.postForCheckNKTReservedForTMK = []

        reloadIconPixmap = QtGui.QStyle.SP_BrowserReload
        reloadIcon = self.style().standardIcon(reloadIconPixmap)
        self.btnUpdateItems.setIcon(reloadIcon)
        self.btnUpdateItems.clicked.connect(self.updateQueueTable)

        self.timer.start()


    def getScheduleItemsChain(self, firstItem, length):
        """
        Получает из БД последовательность талончиков начиная с firstItem (включительно) и до количества length
        Соответствие количества полученных из БД талончиков и переданной длины не проверяется
        :param firstItem: первый талончик в цепочке последовательных
        :type firstItem: CScheduleItem
        :param length: длина цепочки последовательных талончиков (включая первый переданный)
        :type length: int
        :return: Список последовательных талончиков начиная с первого переданного
        :rtype: list
        """
        db = QtGui.qApp.db
        idxList = []
        scheduleItemsList = [firstItem]
        table = db.forceTable('Schedule_Item')
        for i in xrange(firstItem.idx + 1, firstItem.idx + length):
            idxList.append(i)
        records = db.getRecordList(table, where=[table['master_id'].eq(firstItem.scheduleId), table['deleted'].eq(0),
                                                 table['idx'].inlist(idxList)])
        for record in records:
            scheduleItemsList.append(CScheduleItem(record))
        return scheduleItemsList


    def popupMenuOrgPersonnelAboutToShow(self):
        currentClientId = QtGui.qApp.currentClientId()
        self.actRegistrySuspenedAppointment.setEnabled(bool(currentClientId))
        self.actRegistryProphylaxisPlanning.setEnabled(bool(currentClientId))


    def setPersonnelWidgetMode(self, groupingSpeciality):
        if hasattr(self, 'selectionModelPersonnel'):
            self.disconnect(self.selectionModelPersonnel,
                            SIGNAL('selectionChanged(const QItemSelection &, const QItemSelection &)'),
                            self.on_selectionModelPersonnel_selectionChanged)
            del self.selectionModelPersonnel
        self.treeOrgPersonnel.setModel(None)
        if groupingSpeciality:
            self.addModels('Personnel', CResourcesPersonnelModel([], self))
        else:
            self.addModels('Personnel', CFlatResourcesPersonnelModel([], self))
        self.setModels(self.treeOrgPersonnel, self.modelPersonnel, self.selectionModelPersonnel)
        self.connect(self.selectionModelPersonnel,
                     SIGNAL('selectionChanged(const QItemSelection &, const QItemSelection &)'),
                     self.on_selectionModelPersonnel_selectionChanged)
        QtGui.qApp.preferences.appPrefs['groupingSpeciality'] = self.groupingSpeciality = groupingSpeciality
        if self.activityListIsShown:
            self.updatePersonnelActivity()
        else:
            self.updatePersonnel()


    def setPersonnelTreeShown(self):
        if not self.groupingSpeciality:
            self.setPersonnelWidgetMode(True)


    def setPersonnelFlatListShown(self):
        if self.groupingSpeciality:
            self.setPersonnelWidgetMode(False)


    def onPersonnelTreeHeaderClicked(self, col):
        self.setPersonnelWidgetMode(not self.groupingSpeciality)


    def setOrgStructureWidgetMode(self, activityListIsShown):
        self.treeOrgStructure.setModel(None)
        if activityListIsShown:
            self.setModels(self.treeOrgStructure, self.modelActivity, self.selectionModelActivity)
            self.updatePersonnelActivity()
        else:
            self.setModels(self.treeOrgStructure, self.modelOrgStructure, self.selectionModelOrgStructure)
            orgStructureIndex = self.modelOrgStructure.findItemId(QtGui.qApp.currentOrgStructureId())
            if orgStructureIndex and orgStructureIndex.isValid():
                self.treeOrgStructure.setCurrentIndex(orgStructureIndex)
                self.treeOrgStructure.setExpanded(orgStructureIndex, True)
            self.updatePersonnel()
        QtGui.qApp.preferences.appPrefs['activityListIsShown'] = self.activityListIsShown = activityListIsShown


    def setOrgStructureTreeShown(self):
        if self.activityListIsShown:
            self.setOrgStructureWidgetMode(False)


    def setActivityListShown(self):
        if not self.activityListIsShown:
            self.setOrgStructureWidgetMode(True)


    def onOSTreeHeaderClicked(self, col):
        self.setOrgStructureWidgetMode(not self.activityListIsShown)


    def sizeHint(self):
        return QSize(10, 10)


    def getCurrentPersonId(self):
        treeIndex = self.treeOrgPersonnel.currentIndex()
        personIdList = self.modelPersonnel.getItemIdList(treeIndex)
        if personIdList and len(personIdList) == 1:
            return personIdList[0]
        else:
            return None


    def getCurrentDate(self):
        return self.edtBegDate.date()


    def getCurrentPersonIdList(self):
        treeIndex = self.treeOrgPersonnel.currentIndex()
        return self.modelPersonnel.getItemIdList(treeIndex)


    def getCurrentOrgSrtuctureId(self):
        treeIndex = self.treeOrgStructure.currentIndex()
        return self.modelOrgStructure.itemId(treeIndex)


    def onCurrentOrgIdChanged(self):
        if self.activityListIsShown:
            self.modelActivity.reload()
        else:
            self.modelOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.updatePersonnel()


    def onCurrentUserIdChanged(self):
        if QtGui.qApp.userOrgStructureId:
            index = self.modelOrgStructure.findItemId(QtGui.qApp.userOrgStructureId)
            if index and index.isValid():
                self.treeOrgStructure.setCurrentIndex(index)
        if QtGui.qApp.userSpecialityId:
            index = self.modelPersonnel.findPersonId(QtGui.qApp.userId)
            if index and index.isValid():
                self.treeOrgPersonnel.setCurrentIndex(index)


    def setDateRange(self):
        today = QDate.currentDate()
        self.edtBegDate.setDateRange(today, today.addYears(1))


    def getPersonIdList(self):
        personIdSet = set()
        for treeIndex in self.treeOrgPersonnel.selectedIndexes():
            personIdSet.update(self.modelPersonnel.getItemIdList(treeIndex))
        return list(personIdSet)


    def checkApplicable(self, personId, clientId, date):
        return (    self.checkClientAttach(personId, clientId, date, True)
                and (   self.checkClientAttendance(personId, clientId)
                     or self.confirmClientAttendance(self, personId, clientId)
                    )
                and self.confirmClientPolicyConstraint(self, clientId)
               )


    def updatePersonnel(self):
        treeIndex = self.treeOrgStructure.currentIndex()
        orgStructureIdList = self.modelOrgStructure.getItemIdList(treeIndex)
        begDate = self.edtBegDate.date()
        self.modelPersonnel.setOrgStructureIdList(self.modelOrgStructure.orgId, orgStructureIdList, begDate)
        if self.modelOrgStructure.isLeaf(treeIndex):
            self.treeOrgPersonnel.expandAll()
            self.treeOrgPersonnel.setCurrentIndex(self.modelPersonnel.getFirstLeafIndex())
        self.updateQueueTable()


    def updatePersonnelActivity(self):
        treeIndex = self.treeOrgStructure.currentIndex()
        activityIdList = self.modelActivity.getItemIdList(treeIndex)
        begDate = self.edtBegDate.date()
        self.modelPersonnel.setActivityIdList(QtGui.qApp.currentOrgId(), activityIdList, begDate)
        if self.modelActivity.isLeaf(treeIndex):
            self.treeOrgPersonnel.expandAll()
            self.treeOrgPersonnel.setCurrentIndex(self.modelPersonnel.getFirstLeafIndex())
        self.updateQueueTable()


    def getActivityId(self):
        activityPref = QtGui.qApp.getGlobalPreference('23') # WTF!
        if self.activityListIsShown and activityPref == u'да': # WTF again!
            treeIndex = self.treeOrgStructure.currentIndex()
            activityIdList = self.modelActivity.getItemIdList(treeIndex)
            return activityIdList[0] if activityIdList else None
        else:
            return None
    

    def onSubwindowShow(self, widget):
        if isinstance(widget, CHomeCallRequestsWindow):
            self.homeCallRequestsVisible = True
            self.updateAppointmentType()
    

    def onSubwindowClose(self, widget):
        if isinstance(widget, CHomeCallRequestsWindow):
            self.homeCallRequestsVisible = False
            self.updateAppointmentType()
    

    def onDockWidgetCreate(self, widget):
        if widget == QtGui.qApp.mainWindow.dockResources:
            self.connect(widget, SIGNAL('contentCreated(QDockWidget*)'), self.onResourcesDockContentCreate)
            self.connect(widget, SIGNAL('contentDestroyed(QDockWidget*)'), self.onResourcesDockContentDestroy)
            self.connect(widget, SIGNAL('visibilityChanged(QDockWidget*, bool)'), self.onResourcesDockVisibilityChange)
            if widget.content:
                self.connect(widget.content, SIGNAL('appointmentTypeChanged(int)'), self.onResourcesDockAppointmentTypeChange)
            self.resourcesAtHomeSelected = bool(widget.isVisible() and widget.content and hasattr(widget.content, 'appointmentType') and widget.content.appointmentType == CSchedule.atHome)
            self.updateAppointmentType()


    def onResourcesDockContentCreate(self, widget):
        self.connect(widget, SIGNAL('appointmentTypeChanged(int)'), self.onResourcesDockAppointmentTypeChange)
        self.resourcesAtHomeSelected = bool(widget.isVisible() and widget.content and hasattr(widget.content, 'appointmentType') and widget.content.appointmentType == CSchedule.atHome)
        self.updateAppointmentType()


    def onResourcesDockContentDestroy(self, widget):
        self.resourcesAtHomeSelected = False
        self.updateAppointmentType()


    def onResourcesDockVisibilityChange(self, widget, visible):
        self.resourcesAtHomeSelected = bool(visible and widget.content and hasattr(widget.content, 'appointmentType') and widget.content.appointmentType == CSchedule.atHome)
        self.updateAppointmentType()


    def onResourcesDockAppointmentTypeChange(self, appointmentType):
        dockResources = QtGui.qApp.mainWindow.dockResources
        self.resourcesAtHomeSelected = (dockResources.isVisible() and appointmentType == CSchedule.atHome)
        self.updateAppointmentType()
    

    def updateAppointmentType(self):
        if (self.getAppointmentType() != self.modelAmbQueue.appointmentType):
            self.updateQueueTable()


    def getAppointmentType(self):
        if self.homeCallRequestsVisible or self.resourcesAtHomeSelected:
            return CSchedule.atHome
        else:
            return CSchedule.atAmbulance


    def updateQueueTable(self):
        # Есть два сценария, когда происходит массовое обновление условий отбора,
        # (в конструкторе, при подборе номерка)
        # и последовательное управление фильтром вызывает последовательное срабатывание
        # сигналов, каждое из которых потребует обновления таблицы
        # я не думаю что это очень хорошо, поэтому делаю такой "замок".
        # Альтернативы такому решению:
        # - использовать blockSignal на виджетах фильтра
        # - вместо обновления посылать себе асинхронный сигнал (или event?),
        #   который будет доставлен после всех настроек фильтров,
        #   а таблицу обновлять в обработчике этого сигнала (события?)
        if self.updateQueueTableLockCnt is not None:
            self.updateQueueTableLockCnt += 1
            return

        self.timer.stop()
        try:
            appointmentType = self.cmbAppointmentType.value()
            if self.chkEnableAppointmentPurpose.isChecked():
                appointmentPurposeId = self.cmbAppointmentPurpose.value()
            else:
                appointmentPurposeId = None

            begDate = self.edtBegDate.date()
            if self.chkEnableTime.isChecked():
                begTime = self.edtBegTime.time()
                endTime = self.edtEndTime.time()
                timeRange = begTime, endTime
            else:
                timeRange = None

            activityId = self.getActivityId()
            personIdList = self.getPersonIdList()
            self.modelAmbQueue.setFilter(appointmentType,
                                         appointmentPurposeId,
                                         begDate,
                                         timeRange,
                                         activityId,
                                         personIdList
                                        )
        finally:
            self.timer.start()


    def queueingEnabled(self, scheduleItemId, date, personId, specialityId, clientId, scheduleItem, recordType):
        deathDate = getDeathDate(clientId)
        if deathDate:
            QtGui.QMessageBox.warning(self, u'Внимание!', u'Этот пациент не может быть записан к врачу, потому что есть отметка что он уже умер %s' % forceString(deathDate))
            return False

        capacity, busy, appointmentPurposeId = self.getQueueDetails(scheduleItemId, personId)

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

        # 4889 "По поручению МЗ сделать проверку на один нкт талон врача, чтобы на него можно было записать только на тмк"
        if (
                scheduleItem
                and not scheduleItem.overtime
                and recordType != 4
                and getDynamicItemType(scheduleItem, personId) == scheduleItem.NKT
                and self.modelAmbQueue.appointmentType == CSchedule.atAmbulance
        ):
            if checkIsNKTReservedForTMK(self, personId, date, clientId):
                return False

        quota = getQuota(personId, capacity)
        if quota<=busy:
            message = u'Квота на запись исчерпана.'
            if QtGui.qApp.userHasRight(urQueueingOutreaching):
                message += u'\nВсё равно продолжить?'
                buttons = QtGui.QMessageBox.Yes | QtGui.QMessageBox.No
            else:
                buttons = QtGui.QMessageBox.Ok
            return QtGui.QMessageBox.critical(self,
                                              u'Внимание!',
                                              message,
                                              buttons) == QtGui.QMessageBox.Yes
        scheduleItemIdList = getScheduleItemIdListForClient(clientId, specialityId, date, '1')
        if scheduleItemIdList:
            scheduleItemIdList_OMS = getScheduleItemIdListForClient_OMS(scheduleItemIdList)
            exceptionSpecialty = getExceptionSpecialty(specialityId)
            checkFinance = None
            if scheduleItemId and appointmentPurposeId:
                recordFinance = getScheduleItemIdFinance(scheduleItem)
                if recordFinance:
                    checkFinance = forceString(recordFinance.value('code'))
                else:
                    checkFinance = None
            if QtGui.qApp.isReStagingInQueue() or (checkFinance and checkFinance != '2') or not scheduleItemIdList_OMS or exceptionSpecialty == 1 or self.cmbAppointmentType.value() == 2:
                messageBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning, u'Внимание!', u'Этот пациент уже записан к врачу этой специальности\nВы подтверждаете повторную запись?')
            else:
                messageBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning, u'Внимание!', u'Этот пациент уже записан к врачу этой специальности')
            messageBox.setWindowFlags(messageBox.windowFlags() | Qt.WindowStaysOnTopHint)
            if QtGui.qApp.isReStagingInQueue() or (checkFinance and checkFinance != '2') or not scheduleItemIdList_OMS or exceptionSpecialty == 1:
                messageBox.addButton(u'Ок', QtGui.QMessageBox.YesRole)
            messageBox.addButton(u'Отмена', QtGui.QMessageBox.NoRole)
            confirmation = messageBox.exec_()
            if (confirmation == 1 or not (QtGui.qApp.isReStagingInQueue() or (checkFinance and checkFinance != '2') or not scheduleItemIdList_OMS or exceptionSpecialty == 1)) and self.cmbAppointmentType.value() != 2:
                return False

        return True


    def getAppointmentPurposeId(self, scheduleItemId):
        db = QtGui.qApp.db
        scheduleId = forceRef(db.translate('Schedule_Item', 'id', scheduleItemId, 'master_id'))
        if scheduleId:
            return forceRef(db.translate('Schedule', 'id', scheduleId, 'appointmentPurpose_id'))
        return None


    def getQueueDetails(self, scheduleItemId, personId):
        db = QtGui.qApp.db
        scheduleId = forceRef(db.translate('Schedule_Item', 'id', scheduleItemId, 'master_id'))
        if scheduleId:
            # capacity = forceInt(db.translate('Schedule', 'id', scheduleId, 'capacity'))
            table = tableScheduleItem = db.table('vScheduleItem')
            tableAppointmentPurpose = db.table('rbAppointmentPurpose')
            table = table.leftJoin(tableAppointmentPurpose,
                                   tableAppointmentPurpose['id'].eq(tableScheduleItem['appointmentPurpose_id']))
            cond = [tableScheduleItem['master_id'].eq(scheduleId),
                db.joinOr([tableScheduleItem['appointmentPurpose_id'].isNull(),
                               db.joinAnd([tableAppointmentPurpose['enableOwnRecord'].eq(1),
                                           tableScheduleItem['person_id'].eq(QtGui.qApp.userId)
                                           ]),
                               tableAppointmentPurpose['enableConsultancyRecord'
                               if QtGui.qApp.userSpecialityId
                               else 'enablePrimaryRecord'
                               ].eq(1)
                               ])
                              ]
            capacity = db.getCount(table, where=cond)

            appointmentPurposeId = forceRef(db.translate('Schedule_Item', 'id', scheduleItemId, 'appointmentPurpose_id'))

            tableVScheduleItem = db.table('vScheduleItem')
            cond = [ tableVScheduleItem['master_id'].eq(scheduleId),
                     tableVScheduleItem['client_id'].isNotNull()
                   ]
            table = tableVScheduleItem
            if QtGui.qApp.userSpecialityId:
                if personId == QtGui.qApp.userId:
                    # записано самим
                    cond.append(tableVScheduleItem['recordClass'].eq(CScheduleItem.rcSamson))
                    cond.append(tableVScheduleItem['recordPerson_id'].eq(personId))
                else:
                    # записано коллегами
                    tablePerson = db.table('Person')
                    table = table.leftJoin(tablePerson, tablePerson['id'].eq(tableVScheduleItem['recordPerson_id']))
                    cond.append(tableVScheduleItem['recordClass'].eq(CScheduleItem.rcSamson))
                    cond.append(tablePerson['speciality_id'].isNotNull())
                    cond.append(tableVScheduleItem['recordPerson_id'].ne(tableVScheduleItem['person_id']))
            else:
                # первичная запись
                tablePerson = db.table('Person')
                table = table.leftJoin(tablePerson, tablePerson['id'].eq(tableVScheduleItem['recordPerson_id']))
                cond.append(tableVScheduleItem['recordClass'].eq(CScheduleItem.rcSamson))
                cond.append(tablePerson['speciality_id'].isNull())
#внешняя запись
#               tablePerson = db.table('Person')
#                table = table.leftJoin(tablePerson, tablePerson['id'].eq(tableVScheduleItem['recordPerson_id']))
#                cond.append(tableVScheduleItem['recordClass'].ne(CScheduleItem.rcSamson))

            busy = db.getCount(table, where=cond)
        else:
            capacity = busy = 0
            appointmentPurposeId = None
        return capacity, busy, appointmentPurposeId


    def createOrder(self, row, scheduleItemId, date, personId, clientId, isUrgent = 0, recordType = None):
        if scheduleItemId and clientId and self.checkApplicable(personId, clientId, date):
            specialityId = self.getPersonSpecialityId(personId)
            orgStructureId = self.getPersonOrgStructureId(personId)
            scheduleItem = self.modelAmbQueue.getScheduleItem(row)
            skipMessageBox = False
            if ( specialityId
                and orgStructureId
                and self.queueingEnabled(scheduleItemId, date, personId, specialityId, clientId, scheduleItem, recordType)
               ):
                if self.reserveOrder(row):
                    if self.edtCountTickets.value() > 1 and QtGui.QMessageBox.warning(self,
                             u'Внимание!',
                             u'Выбранный пациент будет записан на %s номерка(ов) подряд.\nВы уверены, что хотите продолжить запись?' % self.edtCountTickets.value(),
                             QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                             QtGui.QMessageBox.No) == QtGui.QMessageBox.No:
                        self.releaseLock()
                        return False
                    try:
                        referralRequired = any(isReferralRequired( self.getAppointmentPurposeId(self.modelAmbQueue.getScheduleItemId(row+i)
                                                                                               )
                                                                 )
                                                for i in xrange(self.edtCountTickets.value())
                                              )
                        if referralRequired:
                            referral = inputReferral(self)
                            if not referral:
                                return False
                        else:
                            referral = None

                        currentDateTime = QDateTime.currentDateTime()
                        db = QtGui.qApp.db
                        db.transaction()
                        try:
                            complaint = ''
                            dataChanged = False
                            if scheduleItem:
                                itemsList = self.getScheduleItemsChain(scheduleItem, self.edtCountTickets.value())
                                firstAppointment = itemsList[0].appointmentPurposeId
                                controlledSpeciality = True if getExceptionSpecialty(specialityId) == 0 else False
                                for i in itemsList:
                                    if i.clientId or forceBool(i.value('deleted')):
                                        dataChanged = True
                                        break
                                    appointmentPurpose = i.appointmentPurposeId
                                    if len(itemsList) > 1 and self.checkScheduleItemsInOrder(appointmentPurpose, controlledSpeciality, firstAppointment):
                                        dataChanged = True
                                        skipMessageBox = True
                                        break
                                    i.clientId = clientId
                                    i.recordDatetime = currentDateTime
                                    i.recordPersonId = QtGui.qApp.userId
                                    i.checked = False
                                    i.complaint = complaint
                                    i.isUrgent = isUrgent
                                    if recordType:
                                        i.recordType = recordType
                                    if referral:
                                        i.srcOrgId = referral.srcOrgId
                                        i.srcPerson = referral.srcPerson
                                        i.srcSpecialityId = referral.srcSpecialityId
                                        i.srcNumber = referral.srcNumber
                                        i.srcDate = referral.srcDate
                                    scheduleItemId = i.save()
                                    if recordType and recordType == 4 and scheduleItemId:
                                        if not createRelatedActionTMK(self, clientId, personId, i.time, scheduleItemId):
                                            db.rollback()
                                            return False
                                    QtGui.qApp.emitCurrentClientInfoJLWChanged(scheduleItemId)
                            if not dataChanged:
                                db.commit()
                                return True
                            else:
                                db.rollback()
                        except:
                            db.rollback()
                            raise
                    finally:
                        self.releaseLock()
                if not skipMessageBox:
                    QtGui.QMessageBox.warning( self,
                        u'Внимание!',
                        u'Запись на это время невозможна, так как оно уже занято',
                        QtGui.QMessageBox.Ok,
                        QtGui.QMessageBox.Ok)
        return False


    def checkScheduleItemsInOrder(self, appointmentPurpose, controlledSpeciality, firstAppointment=None):
        """
        Проверяет слот записи на НЕ! соответствие ограничениям по И38
        :param appointmentPurpose: Назначение приёма слота из списка
        :param controlledSpeciality: Является ли специальностью контролируемой МИАЦ
        :param firstAppointment: Назначение приёма первого слота для проверки соответствия последующих
        :return: Bool
        """
        if (not firstAppointment or not appointmentPurpose) and controlledSpeciality:
            QtGui.QMessageBox.warning(self,
                                      u'Внимание!',
                                      u'Запись на это время невозможна, так как в номерках отсутствует назначение приёма',
                                      QtGui.QMessageBox.Ok,
                                      QtGui.QMessageBox.Ok)
            return True
        if appointmentPurpose != firstAppointment:
            QtGui.QMessageBox.warning(self,
                                      u'Внимание!',
                                      u'Запись на это время невозможна, так как назначения приёма в номерках отличаются',
                                      QtGui.QMessageBox.Ok,
                                      QtGui.QMessageBox.Ok)
            return True
        db = QtGui.qApp.db
        finance = db.translate('rbAppointmentPurpose', 'id', appointmentPurpose,
                               'finance_id')
        if not forceInt(finance) and controlledSpeciality:
            QtGui.QMessageBox.warning(self,
                                      u'Внимание!',
                                      u'Запись на это время невозможна, так как в номерках имеется назначение приёма без финансирования',
                                      QtGui.QMessageBox.Ok,
                                      QtGui.QMessageBox.Ok)
            return True
        elif forceString(db.translate('rbFinance', 'id', forceInt(finance), 'name')) == u'ОМС' and controlledSpeciality:
            QtGui.QMessageBox.warning(self,
                                      u'Внимание!',
                                      u'Запись на это время невозможна, так как в номерках имеется назначение приёма с финансированием "ОМС"',
                                      QtGui.QMessageBox.Ok,
                                      QtGui.QMessageBox.Ok)
            return True
        return False


    def reserveOrder(self, row):
        self.releaseLock()
        lockSuccessful = True
        firstScheduleItem = self.modelAmbQueue.getScheduleItem(row)
        if firstScheduleItem:
            itemsList = self.getScheduleItemsChain(firstScheduleItem, self.edtCountTickets.value())
            for i in itemsList:
                if not self.lock('Schedule_Item', i.id):
                    lockSuccessful = False
                    break
            if lockSuccessful:
                self.modelAmbQueue.updateLockInfo()
                lockSuccessful = firstScheduleItem.id == self.modelAmbQueue.getScheduleItemId(row)
        else:
            lockSuccessful = False

        if lockSuccessful:
            self.lblReservedOrder.setText(u'БРОНЬ')
        else:
            self.releaseLock()
        return lockSuccessful


    def releaseLock(self):
        CRecordLockMixin.releaseLock(self)
        self.reservedRow = -1
        self.lblReservedOrder.setText(u'')
        self.timerCountMinute = 0
        self.modelAmbQueue.updateLockInfo()


    def filterStructureId(self, idList, topOrgStructureId):
        index = self.modelOrgStructure.findItemId(topOrgStructureId)
        childrenIdList = self.modelOrgStructure.getItemIdList(index)
        filteredList = list(set(childrenIdList).intersection(set(idList)))
        if filteredList:
            filteredList.sort()
            return filteredList[0]
        else:
            return None


    def popupMenuTreeOrgStructureAboutToShow(self):
        currentClientId = QtGui.qApp.currentClientId()
        self.actFindArea.setEnabled(bool(currentClientId))


    def popupMenuAmbAboutToShow(self):
        currentClientId = QtGui.qApp.currentClientId()
        clientIsNotAlive = forceDateTime(QtGui.qApp.db.translate('Client', 'id', currentClientId, 'deathDate'))
        self.actAmbCreateOrder.setEnabled(bool(currentClientId) and not clientIsNotAlive)
        self.actAmbCreateOrderUrgent.setEnabled(bool(currentClientId) and not clientIsNotAlive)
        self.actAmbCreateOrderTMK.setEnabled(bool(currentClientId) and not clientIsNotAlive)
        if QtGui.qApp.defaultKLADR()[:2] != u'23':
            self.actAmbReserveOrder.setVisible(True)
            self.actAmbUnreserveOrder.setVisible(True)
            self.actAmbReserveOrder.setEnabled(bool(currentClientId))
            self.actAmbUnreserveOrder.setEnabled(bool(currentClientId and self.locked()))
        else:
            self.actAmbReserveOrder.setVisible(False)
            self.actAmbUnreserveOrder.setVisible(False)

    def ambCreateOrder(self, row, clientId, isUrgent = 0, recordType = None):
        clientIsNotAlive = forceDateTime(QtGui.qApp.db.translate('Client', 'id', clientId, 'deathDate'))
        if clientId and row >= 0 and not clientIsNotAlive:
            scheduleItemId, date, time, index, personId, office, begTime, endTime = self.modelAmbQueue.getTimeTableDetails(row)
            if clientId and self.createOrder(row, scheduleItemId, date, personId, clientId, isUrgent, recordType):
                printOrderByScheduleItem(self, scheduleItemId, clientId)
#                printOrder(self, clientId, 0, date, office, personId, index+1, time, False, unicode(formatTimeRange((begTime, endTime))), '')


    def setFilter(self, appointmentType, orgStructureId, specialityId, personId, begDate):
        self.updateQueueTableLockCnt = 0
        try:
            self.cmbAppointmentType.setValue(appointmentType)
            self.edtBegDate.setDate(begDate)
            self.chkEnableTime.setChecked(False)

            if orgStructureId:
                index = self.modelOrgStructure.findItemId(orgStructureId)
                if index and index.isValid():
                    self.setOrgStructureTreeShown()
                    self.treeOrgStructure.setCurrentIndex(index)

            if personId:
                index = self.modelPersonnel.findPersonId(personId)
                if index and index.isValid():
                    self.treeOrgPersonnel.setCurrentIndex(index)

            elif specialityId:
                self.setPersonnelTreeShown()
                index = self.modelPersonnel.findSpecialityId(specialityId)
                if index and index.isValid():
                    self.treeOrgPersonnel.setCurrentIndex(index)

        finally:
            toUpdate = self.updateQueueTableLockCnt
            self.updateQueueTableLockCnt = None
            if toUpdate:
                self.updateQueueTable()

        return self.modelAmbQueue.rowCount()>0


    @pyqtSignature('')
    def on_timer_timeout(self):
        if self.timerCountMinute > 2:
            self.releaseLock()
        else:
            self.timerCountMinute += 1
        self.setDateRange()
        if self.isVisible():
            self.modelAmbQueue.updateData()


    @pyqtSignature('QDate')
    def on_edtBegDate_dateChanged(self):
        self.updateQueueTable()


    @pyqtSignature('')
    def on_btnSetToday_clicked(self):
        today = QDate.currentDate()
        self.edtBegDate.setDate(today)


    @pyqtSignature('bool')
    def on_chkEnableTime_toggled(self, checked):
        self.updateQueueTable()


    @pyqtSignature('QTime')
    def on_edtBegTime_timeChanged(self, value):
        self.updateQueueTable()


    @pyqtSignature('QTime')
    def on_edtEndTime_timeChanged(self, value):
        self.updateQueueTable()


    @pyqtSignature('int')
    def on_cmbAppointmentType_currentIndexChanged(self, index):
        self.updateQueueTable()


    @pyqtSignature('bool')
    def on_chkEnableAppointmentPurpose_toggled(self, checked):
        self.updateQueueTable()


    @pyqtSignature('int')
    def on_cmbAppointmentPurpose_currentIndexChanged(self, index):
        self.updateQueueTable()


    @pyqtSignature('int')
    def on_edtCountTickets_valueChanged(self, value):
        self.on_actAmbUnreserveOrder_triggered()
        self.modelAmbQueue.countTickets = value
        self.updateQueueTable()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelOrgStructure_currentChanged(self, current, previous):
        if not hasattr(self, 'groupingSpeciality'):
            self.groupingSpeciality = forceBool(QtGui.qApp.preferences.appPrefs.get('groupingSpeciality', True))
        self.updatePersonnel()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelActivity_currentChanged(self, current, previous):
        if not hasattr(self, 'groupingSpeciality'):
            self.groupingSpeciality = forceBool(QtGui.qApp.preferences.appPrefs.get('groupingSpeciality', True))
        self.updatePersonnelActivity()


    def on_selectionModelPersonnel_selectionChanged(self, selected, deselected):
        self.updateQueueTable()


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


    @pyqtSignature('QModelIndex')
    def on_tblAmbQueue_doubleClicked(self, index):
        if QtGui.qApp.doubleClickQueueFreeOrder() == 2:
            self.on_actAmbReserveOrder_triggered()
        else:
            self.on_actAmbCreateOrder_triggered()


    @pyqtSignature('')
    def on_actAmbCreateOrder_triggered(self):
        clientId = QtGui.qApp.currentClientId()
#        if not self.reservedRowList:
        row = self.tblAmbQueue.currentIndex().row()
        self.ambCreateOrder(row, clientId)
#        else:
#            for row in self.reservedRowList:
#                self.ambCreateOrder(row, clientId)
        self.on_actAmbUnreserveOrder_triggered()
        QtGui.qApp.emitCurrentClientInfoChanged()
        self.updateQueueTable()
    
    
    @pyqtSignature('')
    def on_actAmbCreateOrderUrgent_triggered(self):
        clientId = QtGui.qApp.currentClientId()
        row = self.tblAmbQueue.currentIndex().row()
        self.ambCreateOrder(row, clientId, isUrgent=1)
        self.on_actAmbUnreserveOrder_triggered()
        QtGui.qApp.emitCurrentClientInfoChanged()
        self.updateQueueTable()


    @pyqtSignature('')
    def on_actAmbCreateOrderTMK_triggered(self):
        clientId = QtGui.qApp.currentClientId()
        row = self.tblAmbQueue.currentIndex().row()
        self.ambCreateOrder(row, clientId, recordType=4)
        self.on_actAmbUnreserveOrder_triggered()
        QtGui.qApp.emitCurrentClientInfoChanged()
        self.updateQueueTable()


    @pyqtSignature('')
    def on_actAmbReserveOrder_triggered(self):
        row = self.tblAmbQueue.currentIndex().row()
        self.reserveOrder(row)
        self.updateQueueTable()


    @pyqtSignature('')
    def on_actAmbUnreserveOrder_triggered(self):
        self.releaseLock()


    @pyqtSignature('')
    def on_actRegistrySuspenedAppointment_triggered(self):
        setRegistrySuspenedAppointment(self, QtGui.qApp.currentClientId())


    @pyqtSignature('')
    def on_actRegistryProphylaxisPlanning_triggered(self):
        registry = QtGui.qApp.mainWindow.registry
        if registry:
            clientIdList = registry.tblClients.selectedItemIdList()
            if clientIdList:
                setRegistryProphylaxisPlanningList(self, clientIdList)


    @pyqtSignature('int')
    def on_modelAmbQueue_dataLoadDone(self, count):
        if count == 0:
            text = u'Список пуст'
        else:
            text = u'В списке '+formatNum(count, (u'номерок', u'номерка', u'номерков'))
        self.lblQueueItemsCount.setText(text)


class CQueueModel(CRecordListModel):
    __pyqtSignals__ = ('beforeReset()',
                       'afterReset()',
                       'dataLoadDone(int)',
                      )

    def __init__(self,  parent):
        CRecordListModel.__init__(self, parent)
        self.addCol(CDateInDocTableCol(u'Дата', 'date', 20)).setReadOnly()
        self.addCol(CTimeInDocTableCol(u'Время', 'time', 20)).setReadOnly()
        self.addCol(CRBInDocTableCol(u'Врач', 'person_id', 20, 'vrbPersonWithSpeciality')).setReadOnly()
        self.addCol(CRBInDocTableCol(u'Назначение', 'appointmentPurpose_id', 20, 'rbAppointmentPurpose', showFields=CRBComboBox.showCodeAndName, addNone=False)).setReadOnly()
        self.addCol(CInDocTableCol(u'Каб', 'office', 6)).setReadOnly()

        self.appointmentType      = None
        self.appointmentPurposeId = None
        self.begDate = None
        self.timeRange = None
        self.activityId = None
        self.appointmentType = CSchedule.atAmbulance
        self.personIdList         = []

        self.countTickets = 1
        self.mapKeyToIndex = {}
        self.lockInfo = {}
        self.lockInfoTimeStamp = None


    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if index.column() == 3:
                row = index.row()
                item = self._items[row]
                appointmentPurposeId = forceRef(item.value('appointmentPurpose_id'))
                if appointmentPurposeId:
                    return CRecordListModel.data(self, index, role)
            else:
                return CRecordListModel.data(self, index, role)
        elif role == Qt.ForegroundRole:
            row = index.row()
            item = self._items[row]
            scheduleItemId = forceRef(item.value('id'))
            if scheduleItemId:
                if self.getLockInfo(scheduleItemId):
                    return toVariant(QtGui.QBrush(Qt.red))
            if index.column() == 0:
                row = index.row()
                item = self._items[row]
                date = forceDate(item.value('date'))
                if date:
                    dow = QtGui.qApp.calendarInfo.getDayOfWeekInt(*date.getDate())
                    if dow is None:
                        dow = date.dayOfWeek()
                        if dow in (6, 7):
                            return QVariant(QtGui.QBrush(Qt.red))
                        else:
                            return QVariant()
                    return QVariant(QtGui.QBrush(Qt.red))
        elif role == Qt.FontRole:
            row = index.row()
            item = self._items[row]
            scheduleItemId = forceRef(item.value('id'))
            if scheduleItemId:
                personId = self.getLockInfo(scheduleItemId)
                if personId:
                    font = QtGui.QFont()
                    if personId == QtGui.qApp.userId:
                        font.setBold(True)
                    else:
                        font.setItalic(True)
                    return QVariant(font)
        return QVariant()


    def getLockInfo(self, scheduleItemId):
        if not self.lockInfoTimeStamp or self.lockInfoTimeStamp.addSecs(15) < QDateTime().currentDateTime():
            self.updateLockInfoInt()
        return self.lockInfo.get(scheduleItemId)


    def getKey(self, row):
        item = self._items[row]
        return forceDateTime(item.value('time')), forceRef(item.value('person_id'))


    def getTimeTableDetails(self, row):
        item = self._items[row]
        scheduleItemId = forceRef(item.value('id'))
        db = QtGui.qApp.db
        record = db.getRecord('vScheduleItem', 'idx, begTime, endTime', scheduleItemId)

        result = (forceRef(item.value('id')),
                  forceDate(item.value('date')),
                  forceTime(item.value('time')),
                  forceInt(record.value('idx')),     # seq.no
                  forceRef(item.value('person_id')),
                  forceString(item.value('office')),
                  forceTime(record.value('begTime')),
                  forceTime(record.value('endTime')),
                 )
        return result


    def getScheduleItemId(self, row):
        if 0<=row<len(self._items):
            item = self._items[row]
            return forceRef(item.value('id'))
        else:
            return None


    def getScheduleItem(self, row):
        scheduleItemId = self.getScheduleItemId(row)
        record = QtGui.qApp.db.getRecord('Schedule_Item', '*', scheduleItemId) if scheduleItemId else None
        return CScheduleItem(record) if record else None


    def lookupRowByKey(self, key):
        lookupTime, lookupPersonId = key
        for row, item in enumerate(self._items):
            time = forceDateTime(item.value('time'))
            personId = forceRef(item.value('person_id'))
            if (time>lookupTime or lookupTime==time and personId>=lookupPersonId):
                return row
        return len(self._items)-1


    def setFilter(self,
                  appointmentType,
                  appointmentPurposeId,
                  begDate,
                  timeRange,
                  activityId,
                  personIdList
                 ):
        if (    self.appointmentType != appointmentType
             or self.appointmentPurposeId != appointmentPurposeId
             or self.begDate != begDate
             or self.timeRange != timeRange
             or self.activityId != activityId
             or self.personIdList != personIdList
           ):
            self.appointmentType      = appointmentType
            self.appointmentPurposeId = appointmentPurposeId
            self.begDate = begDate
            self.timeRange = timeRange
            self.activityId = activityId
            self.personIdList         = personIdList
            self.loadData()
            self.reset()
        else:
            self.updateData()


    def loadData(self):
        if self.personIdList:
            self._items = self.loadItems(self.personIdList)
        else:
            self._items = []
        self.emit(SIGNAL('dataLoadDone(int)'), len(self._items))

    
    def loadItems(self, personIdList):
        now = QDateTime.currentDateTime()
        db = QtGui.qApp.db
        table = tableScheduleItem = db.table('vScheduleItem')
        tablePerson = db.table('Person')
        tableAppointmentPurpose = db.table('rbAppointmentPurpose')
        tablePost = db.table('rbPost')
        tablePostIdentification = db.table('rbPost_Identification')
        tableAccountingSystem = db.table('rbAccountingSystem')
        table = table.innerJoin(tablePerson, tablePerson['id'].eq(tableScheduleItem['person_id']))
        table = table.leftJoin(tableAppointmentPurpose, tableAppointmentPurpose['id'].eq(tableScheduleItem['appointmentPurpose_id']))
        table = table.leftJoin(tablePost, tablePost['id'].eq(tablePerson['post_id']))
        table = table.leftJoin(tablePostIdentification, tablePostIdentification['master_id'].eq(tablePost['id']))
        table = table.leftJoin(tableAccountingSystem, tableAccountingSystem['id'].eq(tablePostIdentification['system_id']))
        cond = [ # table['deleted'].eq(0),
                    tableScheduleItem['person_id'].inlist(personIdList),
                    tableScheduleItem['client_id'].isNull(),
                    tableScheduleItem['appointmentType'].eq(self.appointmentType),
                    tableScheduleItem['reasonOfAbsence_id'].isNull(),
                    db.joinOr([tableScheduleItem['appointmentPurpose_id'].isNull(),
                            db.joinAnd([ tableAppointmentPurpose['enableOwnRecord'].eq(1),
                                            tableScheduleItem['person_id'].eq(QtGui.qApp.userId)
                                        ]),
                            tableAppointmentPurpose['enableConsultancyRecord'
                                                    if QtGui.qApp.userSpecialityId
                                                    else 'enablePrimaryRecord'
                                                    ].eq(1)
                            ]
                            ),
#                     table['overtime'].eq(0),
                    tableScheduleItem['time'].ge(now),
                    tableAccountingSystem['urn'].eq('urn:oid:1.2.643.5.1.13.13.11.1002')
                ]
        if self.begDate:
            cond.append(tableScheduleItem['date'].ge(self.begDate))
        if self.timeRange:
            cond.append('TIME(time) BETWEEN %s AND %s'
                        % (
                            db.formatTime(self.timeRange[0]),
                            db.formatTime(self.timeRange[1])
                            )
                        )
        if self.appointmentType:
            cond.append(tableScheduleItem['appointmentType'].eq(self.appointmentType))
        else:
            cond.append(tableScheduleItem['appointmentType'].eq(CSchedule.atAmbulance))
        if self.appointmentPurposeId:
            cond.append('appointmentPurpose_id = %d' % self.appointmentPurposeId)
        if self.activityId:
            cond.append('activity_id = %d or activity_id is NULL' % self.activityId)
        cond.append( 'Person.lastAccessibleTimelineDate IS NULL OR vScheduleItem.date<=Person.lastAccessibleTimelineDate')
        if QtGui.qApp.isTimelineAccessibilityDays() == 1:
            cond.append( 'Person.timelineAccessibleDays <= 0 OR vScheduleItem.date<=%s'%db.dateAdd('current_date', 'day', 'Person.timelineAccessibleDays'))
        if self.countTickets>1:
            for offset in xrange(1, self.countTickets):
                offsetTableName = 'SI_%d' % offset
                offsetTable = db.table('Schedule_Item').alias(offsetTableName)
                offsetCond = '%(offsetTableName)s.master_id = vScheduleItem.master_id'     \
                                ' AND %(offsetTableName)s.idx = vScheduleItem.idx+%(offset)d' \
                                ' AND %(offsetTableName)s.client_id IS NULL' \
                                ' AND %(offsetTableName)s.deleted = 0' % {
                                    'offset': offset,
                                    'offsetTableName': offsetTableName
                                                                        }
                cond.append(db.existsStmt(offsetTable, offsetCond))
        return db.getRecordList(table, [tableScheduleItem['id'],
                                                tableScheduleItem['date'],
                                                tableScheduleItem['time'],
                                                tableScheduleItem['person_id'],
                                                tableScheduleItem['appointmentPurpose_id'],
                                                tableScheduleItem['office'],
                                                tableScheduleItem['reasonOfAbsence_id'],
                                                tablePost['code'],
                                                tablePostIdentification['value'].alias('post')],
                                                cond,
                                                'time',
                                                500)     

    def updateLockInfoInt(self):
        db = QtGui.qApp.db
        tableAppLock = db.table('AppLock')
        tableAppLock_Detail = db.table('AppLock_Detail')
        queryTable = tableAppLock_Detail.leftJoin(tableAppLock, tableAppLock_Detail['master_id'].eq(tableAppLock['id']))
        records = db.getRecordList(queryTable,
                                   [tableAppLock_Detail['recordId'],
                                    tableAppLock['person_id']
                                   ],
                                   [tableAppLock_Detail['tableName'].eq('Schedule_Item'),
                                    'AppLock.retTime>=%s'%db.dateAdd('current_timestamp',  'minute',  -3)
                                   ]
                                  )
        self.lockInfo = {}
        for record in records:
            key = forceInt(record.value('recordId'))
            val = forceInt(record.value('person_id'))
            self.lockInfo[key] = val
        self.lockInfoTimeStamp = QDateTime.currentDateTime()


    def updateData(self):
        self.emit(SIGNAL('beforeReset()'))
        self.loadData()
        self.updateLockInfoInt()
        self.reset()
        self.emit(SIGNAL('afterReset()'))


    def updateLockInfo(self):
        self.emit(SIGNAL('beforeReset()'))
        self.updateLockInfoInt()
        self.reset()
        self.emit(SIGNAL('afterReset()'))



# ######################################################################


def locFormatTime(time):
    return time.toString('H:mm') if time else '--:--'

