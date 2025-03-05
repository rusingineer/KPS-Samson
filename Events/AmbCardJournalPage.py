# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2019 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4                 import QtGui
from PyQt4.QtCore          import QDate, QDateTime, QObject, QTime, Qt, pyqtSignature, SIGNAL

from library.PrintInfo          import CInfoContext
from library.PrintTemplates     import ( applyTemplateList,
                                         getPrintTemplates,
                                         CPrintAction,
                                       )
from library.TableModel         import ( CTableModel,
                                         CDateCol,
                                         CDateTimeCol,
                                         CDoubleCol,
                                         CEnumCol,
                                         CRefBookCol,
                                         CTextCol,
                                       )
from library.Utils              import forceDate, forceRef, forceString
from Events.Action              import CAction
from Events.ActionInfo          import CCookedActionInfo
from Events.ActionStatus        import CActionStatus
from Events.EventInfo           import CEventInfo
from Events.Utils               import orderTexts, getEventContext, getEventContextData
from Registry.RegistryTable     import codeIsPrimary
from Registry.Utils             import getClientString


from Events.Ui_AmbCardJournalPage import Ui_AmbCardJournalPage


class CAmbCardJournalPage(QtGui.QWidget, Ui_AmbCardJournalPage):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self._clientId = None
        self.setupUi(self)
        self._filter = {}

        #comboboxes
        self.cmbEventType.setTable('EventType', addNone=True)
        self.cmbScene.setTable('rbScene', addNone=True)

        #models
        self.modelEvents = CEventsTableModel(self)
        self.selectionModelEvents = QtGui.QItemSelectionModel(self.modelEvents, self)
        self.modelActions = CActionsTableModel(self)
        self.selectionModelActions = QtGui.QItemSelectionModel(self.modelActions, self)

        #views
        self.tblEvents.setModel(self.modelEvents)
        self.tblEvents.setSelectionModel(self.selectionModelEvents)
        self.tblActions.setModel(self.modelActions)
        self.tblActions.setSelectionModel(self.selectionModelActions)

        #connects WTF?!
        self.connect(self.selectionModelEvents, SIGNAL('currentChanged(QModelIndex,QModelIndex)'),
                     self.on_selectionModelEventsCurrentChanged)
        self.connect(self.selectionModelActions, SIGNAL('currentChanged(QModelIndex,QModelIndex)'),
                     self.on_selectionModelActionsCurrentChanged)

        QObject.connect(self.tblEvents.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.setSortEvents)
        QObject.connect(self.tblActions.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.setSortActions)
        self.connect(self.btnSelect, SIGNAL('printByTemplate(int)'), self.on_btnSelect_printByTemplate)

        self._onApplyFilter()
        self.tblEvents.enableColsHide()
        self.tblEvents.enableColsMove()
        self.tblActions.enableColsHide()
        self.tblActions.enableColsMove()
        self.cmbRelation.setCurrentIndex(0)
        self.orderEvents = u''
        self.orderActions = u''
        self.cmbActionType.setClass(None)
        self.cmbActionType.setClassesVisible(True)
        self.setVisibleButtonPages(False)
        self.currentEventTemplateId = None
        self.eventTemplateIdList = []
        self.eventData = {}
        self.currentActionTemplateId = None
        self.actionTemplateIdList = []
        self.actionData = {}
        self.isFocusWidget = 0
        self.lblTemplateName.setText(u'Выводить название шаблона')
        self.edtEndTime.setTime(QTime(23, 59))

        self.actShowPacsImages = QtGui.QAction(u'Показать снимки', self)
        pacsAddress = forceString(QtGui.qApp.preferences.appPrefs.get('pacsAddress', ''))
        if not pacsAddress:
            self.actShowPacsImages.setEnabled(False)
        self.tblActions.addPopupAction(self.actShowPacsImages)
        #self.actShowPacsImages.triggered.connect(self.on_actShowPacsImages)



    def resetSortTable(self):
        headerEvents=self.tblEvents.horizontalHeader()
        headerEvents.setSortIndicatorShown(False)
        headerEvents.setSortIndicator(0, Qt.AscendingOrder)
        self.modelEvents.headerSortingCol[0] = not Qt.AscendingOrder
        headerActions=self.tblActions.horizontalHeader()
        headerActions.setSortIndicatorShown(False)
        headerActions.setSortIndicator(0, Qt.AscendingOrder)
        self.modelActions.headerSortingCol[0] = not Qt.AscendingOrder


    def getBegDatePrimaryEvent(self):
        if self._clientId:
            db = QtGui.qApp.db
            tableEvent = db.table('Event')
            cond = [tableEvent['deleted'].eq(0),
                    tableEvent['client_id'].eq(self._clientId)]
            return forceDate(db.getMin(tableEvent, tableEvent['setDate'].name(), cond))
        return QDate()


    def setClientId(self, clientId):
        if self._clientId != clientId:
            self._clientId = clientId
            self.updateEvents()
        self.setWindowTitle(u'Пациент: %s' % (getClientString(self._clientId) if self._clientId else u'не известен'))
        self.edtBegDate.setDate(self.getBegDatePrimaryEvent())
        self.getUpdateInfo()


    def _onResetFilter(self):
        self._filter = {}
        self.edtBegDate.setDate(self.getBegDatePrimaryEvent())
        self.edtBegTime.setTime(QTime())
        self.edtEndDate.setDate(QDate.currentDate())
        self.edtEndTime.setTime(QTime(23, 59))
        self.cmbRelation.setCurrentIndex(2)
        self.cmbLPU.setValue(None)
        self.cmbEventSetPerson.setValue(None)
        self.cmbEventType.setValue(None)
        self.cmbClass.setCurrentIndex(0)
        self.cmbActionType.setClass(None)
        self.cmbActionType.setValue(None)
        self.cmbScene.setValue(None)


    def _onApplyFilter(self):
        self._filter['begDateTime']      = QDateTime(self.edtBegDate.date(), self.edtBegTime.time())
        self._filter['endDateTime']      = QDateTime(self.edtEndDate.date(), self.edtEndTime.time())
        self._filter['relation']         = self.cmbRelation.currentIndex()
        self._filter['LPUId']            = self.cmbLPU.value()
        self._filter['eventSetPersonId'] = self.cmbEventSetPerson.value()
        self._filter['eventTypeId']      = self.cmbEventType.value()
        self._filter['actionClass']      = self.cmbClass.currentIndex()
        self._filter['actionTypeId']     = self.cmbActionType.value()
        self._filter['actionTypeIdList'] = []
        modelIndex = self.cmbActionType.currentModelIndex()
        if modelIndex and modelIndex.isValid():
            self._filter['actionTypeIdList'] = self.cmbActionType._model.getItemIdList(modelIndex)
        self._filter['sceneId']          = self.cmbScene.value()


    def updateEvents(self, actionId = None):
        begDateTime      = self._filter['begDateTime']
        endDateTime      = self._filter['endDateTime']
        LPUId            = self._filter['LPUId']
        eventSetPersonId = self._filter['eventSetPersonId']
        eventTypeId      = self._filter['eventTypeId']
        relation         = self._filter['relation']

        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        tableAction = db.table('Action')
        fields = tableEvent['id'].name()
        if not self.orderEvents:
            self.orderEvents = u'Event.setDate'
        if relation != 1:
            queryTable = tableEvent.leftJoin(tableEventType, db.joinAnd([tableEventType['id'].eq(tableEvent['eventType_id']), tableEventType['context'].ne(u'flag'), tableEventType['code'].ne(u'flag')]))
            cond = [tableEvent['deleted'].eq(0),
                    tableEvent['client_id'].eq(self._clientId),
                    tableEventType['code'].ne('queue')]
            if begDateTime and begDateTime.isValid():
                cond.append(tableEvent['setDate'].ge(begDateTime))
            if endDateTime and endDateTime.isValid():
                cond.append(tableEvent['setDate'].le(endDateTime))
            if LPUId:
                cond.append(tableEvent['org_id'].eq(LPUId))
            if eventSetPersonId:
                cond.append(tableEvent['setPerson_id'].eq(eventSetPersonId))
            if eventTypeId:
                cond.append(tableEvent['eventType_id'].eq(eventTypeId))
            idList = db.getIdList(queryTable, fields, cond, self.orderEvents)
        elif actionId:
            cond = [tableEvent['deleted'].eq(0),
                    tableAction['id'].eq(actionId)]
            queryTable = tableEvent.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
            idList = db.getDistinctIdList(queryTable, fields, cond, self.orderEvents)
        else:
            idList = []
        self.tblEvents.setIdList(idList)


    def updateActions(self, eventId = None):
        actionClass      = self._filter['actionClass']
        actionTypeId     = self._filter['actionTypeId']
        actionTypeIdList = self._filter['actionTypeIdList']
        relation         = self._filter['relation']
#        sceneId          = self._filter['sceneId']
        begDateTime      = self._filter['begDateTime']
        endDateTime      = self._filter['endDateTime']
        db = QtGui.qApp.db
        tableAction = db.table('Action')
        tableActionType = db.table('ActionType')
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        fields = tableAction['id'].name()
        cond = [tableAction['deleted'].eq(0)]
        queryTable = tableAction
        queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
        queryTable = queryTable.leftJoin(tableEventType, db.joinAnd([tableEventType['id'].eq(tableEvent['eventType_id']), tableEventType['context'].ne(u'flag'), tableEventType['code'].ne(u'flag')]))
        queryTable = queryTable.innerJoin(tableActionType, tableAction['actionType_id'].eq(tableActionType['id']))
        if actionClass:            
            cond.append(tableActionType['class'].eq(actionClass-1))
            cond.append(tableActionType['deleted'].eq(0))
        if actionTypeIdList:
            cond.append(tableAction['actionType_id'].inlist(actionTypeIdList))
        elif actionTypeId:
            cond.append(tableAction['actionType_id'].eq(actionTypeId))
        if self.cbHaveTemplate.isChecked():
            cond.append(tableActionType['context'].ne(''))            
        if relation == 0:
            if eventId:
                cond.append(tableAction['event_id'].eq(eventId))
            else:
                self.tblActions.setIdList([])
                return
        else:
            if begDateTime and begDateTime.isValid():
                cond.append(tableAction['begDate'].ge(begDateTime))
            if endDateTime and endDateTime.isValid():
                cond.append(tableAction['begDate'].le(endDateTime))
            cond.append(tableEvent['client_id'].eq(self._clientId))

        if not self.orderActions:
            self.orderActions = u'begDate'
        order = self.orderActions.replace('begDate', 'Action.begDate').replace('endDate', 'Action.endDate')

        idList = db.getIdList(queryTable, fields, cond, order)
        self.tblActions.setIdList(idList)


    @pyqtSignature('QAbstractButton*')
    def on_filterButtonBox_clicked(self, button):
        buttonCode = self.filterButtonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.getUpdateInfo()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self._onResetFilter()
            self.getUpdateInfo()


    def getUpdateInfo(self):
        self._onApplyFilter()
        relation = self._filter['relation']
        if relation == 0:
            self.updateEvents()
        elif relation == 1:
            self.updateActions()
        elif relation == 2:
            self.updateEvents()
            self.updateActions()


    def setupBtnSelectMenu(self):
        menu = self.getPrintBtnMenu()
        self.btnSelect.setMenu(menu)
        self.btnSelect.setEnabled(bool(menu))


    def getPrintBtnMenu(self):
        menu = QtGui.QMenu()
        if self.isFocusWidget == 1:
            eventItem = self.tblEvents.currentItem()
            eventTypeId = forceRef(eventItem.value('eventType_id'))
            context = getEventContext(eventTypeId)
        else:
            actionItem = self.tblActions.currentItem()
            if actionItem:
                actionTypeId = forceRef(actionItem.value('actionType_id'))
                db = QtGui.qApp.db
                context = forceString(db.translate('ActionType', 'id', actionTypeId, 'context'))

        templates = getPrintTemplates(context, inAmbCard=True)
        if templates:
            for i, template in enumerate(templates):
                action = CPrintAction(template.name, template.id, self.btnSelect, self.btnSelect)
                menu.addAction(action)
        else:
            act = menu.addAction(u'Нет шаблонов печати')
            act.setEnabled(False)
        menu.addSeparator()
        return menu


    @pyqtSignature('int')
    def on_btnSelect_printByTemplate(self, templateId):
        self.getSelectedTemplate(templateId)


    def getSelectedTemplate(self, templateId):
        from Events.EditDispatcher      import getEventFormClass
        self.txtAmbCardReport.setText(u'')
        QtGui.qApp.setWaitCursor()
        try:
            if self.isFocusWidget == 1:
                eventItem = self.tblEvents.currentItem()
                eventId = forceRef(eventItem.value('id'))
                if eventId:
                    if templateId and templateId not in self.eventTemplateIdList:
                        self.eventTemplateIdList.append(templateId)
                    formClass = getEventFormClass(eventId)
                    dialog = formClass(self)
                    try:
                        db = QtGui.qApp.db
                        dialog.load(eventId)
                        record = db.getRecord(db.table(dialog._tableName), '*', dialog._id)
                        dialog.setRecord(record)
                        self.eventData = getEventContextData(dialog)
                        self.currentEventTemplateId = templateId
                        QtGui.qApp.call(self, applyTemplateList, (self, self.currentEventTemplateId, [self.eventData], self.txtAmbCardReport))
                        self.btnNextEnabled(self.currentEventTemplateId, self.eventTemplateIdList)
                        self.btnBackEnabled(self.currentEventTemplateId, self.eventTemplateIdList)
                    finally:
                        dialog.deleteLater()
                else:
                    self.txtAmbCardReport.setText(u'')
            else:
                actionItem = self.tblActions.currentItem()
                if actionItem:
                    actionId = forceRef(actionItem.value('id'))
                    eventId = forceRef(actionItem.value('event_id'))
                    if templateId and templateId not in self.actionTemplateIdList:
                            self.actionTemplateIdList.append(templateId)
                    self.setVisibleButtonPages(bool(len(self.actionTemplateIdList) > 1))
                    context = CInfoContext()
                    eventInfo = context.getInstance(CEventInfo, eventId)
                    eventActions = eventInfo.actions
                    eventActions._idList = [actionId]
                    eventActions._items  = [CCookedActionInfo(context, actionItem, CAction(record=actionItem))]
                    eventActions._loaded = True
                    action = eventInfo.actions[0]
                    self.actionData = { 'event' : eventInfo,
                                         'action': action,
                                         'client': eventInfo.client,
                                         'actions':eventActions,
                                         'currentActionIndex': 0,
                                         'tempInvalid': None
                                       }
                    self.currentActionTemplateId = templateId
                    QtGui.qApp.call(self, applyTemplateList, (self, self.currentActionTemplateId, [self.actionData], self.txtAmbCardReport))
                    applyTemplateList(self, self.currentActionTemplateId, [self.actionData], self.txtAmbCardReport)
                    self.btnNextEnabled(self.currentActionTemplateId, self.actionTemplateIdList)
                    self.btnBackEnabled(self.currentActionTemplateId, self.actionTemplateIdList)
        except:
            self.txtAmbCardReport.setText(u'ОШИБКА ЗАПОЛНЕНИЯ ШАБЛОНА')
        finally:
           QtGui.qApp.restoreOverrideCursor()


    def btnNextEnabled(self, templateId, templateIdList):
        self.btnNext.setEnabled(True)
        if templateId in templateIdList:
            currentIndex = templateIdList.index(templateId)
            countTemplateId = len(templateIdList)
            if currentIndex >= countTemplateId - 1:
                self.btnNext.setEnabled(False)


    def btnBackEnabled(self, templateId, templateIdList):
        self.btnBack.setEnabled(True)
        if templateId in templateIdList:
            currentIndex = templateIdList.index(templateId)
#            countTemplateId = len(templateIdList)
            if currentIndex == 0:
                self.btnBack.setEnabled(False)


    def on_selectionModelEventsCurrentChanged(self, current, previous):
        self.isFocusWidget = 1
        relation = self._filter['relation']
        if relation == 0:
            eventId = self.tblEvents.itemId(current)
            self.updateActions(eventId)
        self.getEventTemplate(current)
        parObject = QObject.parent(self)
        if parObject:
            if hasattr(parObject, 'btnRowSelect'):
                parObject.getBtnRowSelectText()
            if hasattr(parObject, 'setEnabledButtonPages'):
                parObject.setEnabledButtonPages()


    def getEventTemplate(self, current):
        from Events.EditDispatcher      import getEventFormClass
        self.setupBtnSelectMenu()
        self.currentEventTemplateId = None
        self.eventTemplateIdList = []
        self.eventData = {}
        self.btnBack.setEnabled(False)
        self.txtAmbCardReport.setText(u'')
        QtGui.qApp.setWaitCursor()
        try:
            eventId = self.tblEvents.itemId(current)
            if eventId:
                db = QtGui.qApp.db
                tableRBPrintTemplate = db.table('rbPrintTemplate')
                eventItem = self.tblEvents.currentItem()
                eventTypeId = forceRef(eventItem.value('eventType_id'))
                tContext = getEventContext(eventTypeId)
                records = db.getDistinctIdList('rbPrintTemplate', 'id', [tableRBPrintTemplate['context'].eq(tContext), tableRBPrintTemplate['inAmbCard'].eq(1), tableRBPrintTemplate['deleted'].eq(0)], 'code, name, id')
                for templateId in records:
                    if templateId and templateId not in self.eventTemplateIdList:
                        self.eventTemplateIdList.append(templateId)
                self.setVisibleButtonPages(bool(len(self.eventTemplateIdList) > 1))
                formClass = getEventFormClass(eventId)
                dialog = formClass(self)
                try:
                    dialog.load(eventId)
                    record = db.getRecord(db.table(dialog._tableName), '*', dialog._id)
                    dialog.setRecord(record)
                    self.eventData = getEventContextData(dialog)
                    self.currentEventTemplateId = self.eventTemplateIdList[0] if self.eventTemplateIdList else None
                    QtGui.qApp.call(self, applyTemplateList, (self, self.currentEventTemplateId, [self.eventData], self.txtAmbCardReport))

                finally:
                    dialog.deleteLater()
            else:
                self.txtAmbCardReport.setText(u'')
        except:
            self.txtAmbCardReport.setText(u'ОШИБКА ЗАПОЛНЕНИЯ ШАБЛОНА')
        finally:
           QtGui.qApp.restoreOverrideCursor()


    def setVisibleButtonPages(self, isEnable):
        self.btnBack.setVisible(isEnable)
        self.btnNext.setVisible(isEnable)
        self.btnNext.setEnabled(isEnable)


    def turnOverThePagesNext(self, templateId, templateIdList, data):
        self.txtAmbCardReport.setText(u'')
        if templateId in templateIdList:
            currentIndex = templateIdList.index(templateId)
            countTemplateId = len(templateIdList)
            if currentIndex >= countTemplateId - 1:
                self.btnNext.setEnabled(False)
            else:
                QtGui.qApp.setWaitCursor()
                try:
                    templateId = templateIdList[currentIndex+1]
                    QtGui.qApp.call(self, applyTemplateList, (self, templateId, [data], self.txtAmbCardReport))
                    currentIndex = templateIdList.index(templateId)
                    if currentIndex >= countTemplateId - 1:
                        self.btnNext.setEnabled(False)
                finally:
                   QtGui.qApp.restoreOverrideCursor()
        return templateId


    def turnOverThePagesBack(self, templateId, templateIdList, data):
        self.txtAmbCardReport.setText(u'')
        if templateId in templateIdList:
            currentIndex = templateIdList.index(templateId)
            countTemplateId = len(templateIdList)
            if currentIndex == 0:
                self.btnBack.setEnabled(False)
            elif currentIndex <= countTemplateId - 1:
                QtGui.qApp.setWaitCursor()
                try:
                    templateId = templateIdList[currentIndex-1]
                    QtGui.qApp.call(self, applyTemplateList, (self, templateId, [data], self.txtAmbCardReport))
                    currentIndex = templateIdList.index(templateId)
                    if currentIndex == 0:
                        self.btnBack.setEnabled(False)
                finally:
                   QtGui.qApp.restoreOverrideCursor()
        return templateId


    @pyqtSignature('')
    def on_btnNext_clicked(self):
        self.btnBack.setEnabled(True)
        if self.isFocusWidget == 1:
            self.currentEventTemplateId = self.turnOverThePagesNext(self.currentEventTemplateId, self.eventTemplateIdList, self.eventData)
        elif self.isFocusWidget == 2:
            self.currentActionTemplateId = self.turnOverThePagesNext(self.currentActionTemplateId, self.actionTemplateIdList, self.actionData)
        else:
            self.setVisibleButtonPages(False)


    @pyqtSignature('')
    def on_btnBack_clicked(self):
        self.btnNext.setEnabled(True)
        if self.isFocusWidget == 1:
            self.currentEventTemplateId = self.turnOverThePagesBack(self.currentEventTemplateId, self.eventTemplateIdList, self.eventData)
        elif self.isFocusWidget == 2:
            self.currentActionTemplateId = self.turnOverThePagesBack(self.currentActionTemplateId, self.actionTemplateIdList, self.actionData)
        else:
            self.setVisibleButtonPages(False)


    def on_selectionModelActionsCurrentChanged(self, current, previous):
        self.currentActionTemplateId = None
        self.actionTemplateIdList = []
        self.actionData = {}
        self.btnBack.setEnabled(False)
        if self.isFocusWidget != 1:
            self.getActionTemplate()
        relation = self._filter['relation']
        actionId = self.tblActions.itemId(current)
        if relation == 1:
            self.updateEvents(actionId)
        parObject = QObject.parent(self)
        if parObject:
            if hasattr(parObject, 'btnRowSelect'):
                parObject.getBtnRowSelectText()
            if hasattr(parObject, 'setEnabledButtonPages'):
                parObject.setEnabledButtonPages()


    def getActionTemplate(self):
        self.txtAmbCardReport.setText(u'')
        self.setupBtnSelectMenu()
        QtGui.qApp.setWaitCursor()
        try:
            actionItem = self.tblActions.currentItem()
            if actionItem:
                actionId = forceRef(actionItem.value('id'))
                actionTypeId = forceRef(actionItem.value('actionType_id'))
                eventId = forceRef(actionItem.value('event_id'))
                db = QtGui.qApp.db
                tableRBPrintTemplate = db.table('rbPrintTemplate')
                tContext = forceString(db.translate('ActionType', 'id', actionTypeId, 'context'))
                records = db.getDistinctIdList('rbPrintTemplate', 'id', [tableRBPrintTemplate['context'].eq(tContext), tableRBPrintTemplate['inAmbCard'].eq(1), tableRBPrintTemplate['deleted'].eq(0)], 'code, name, id')
                for templateId in records:
                    if templateId and templateId not in self.actionTemplateIdList:
                        self.actionTemplateIdList.append(templateId)
                self.setVisibleButtonPages(bool(len(self.actionTemplateIdList) > 1))
                context = CInfoContext()
                eventInfo = context.getInstance(CEventInfo, eventId)
                eventActions = eventInfo.actions
                eventActions._idList = [actionId]
                eventActions._items  = [CCookedActionInfo(context, actionItem, CAction(record=actionItem))]
                eventActions._loaded = True
                action = eventInfo.actions[0]
                self.actionData = { 'event' : eventInfo,
                                     'action': action,
                                     'client': eventInfo.client,
                                     'actions':eventActions,
                                     'currentActionIndex': 0,
                                     'tempInvalid': None
                                   }
                self.currentActionTemplateId = self.actionTemplateIdList[0] if self.actionTemplateIdList else None
                QtGui.qApp.setWaitCursor()
                try:
                    QtGui.qApp.call(self, applyTemplateList, (self, self.currentActionTemplateId, [self.actionData], self.txtAmbCardReport))
                finally:
                    QtGui.qApp.restoreOverrideCursor()
        except:
            self.txtAmbCardReport.setText(u'ОШИБКА ЗАПОЛНЕНИЯ ШАБЛОНА')
        finally:
           QtGui.qApp.restoreOverrideCursor()


    @pyqtSignature('int')
    def on_cmbClass_currentIndexChanged(self, index):
        self.cmbActionType.setClass((index-1) if index else None)


    @pyqtSignature('QModelIndex')
    def on_tblEvents_clicked(self, index):
        self.isFocusWidget = 1


    @pyqtSignature('QModelIndex')
    def on_tblActions_clicked(self, index):
        if self.isFocusWidget == 1:
            self.isFocusWidget = 2
            self.on_selectionModelActionsCurrentChanged(index, None)
#            self.currentActionTemplateId = None
#            self.actionTemplateIdList = []
#            self.actionData = {}
#            self.btnBack.setEnabled(False)
#            self.getActionTemplate()
        else:
            self.isFocusWidget = 2


    @pyqtSignature('int')
    def on_cmbRelation_currentIndexChanged(self, index):
        enable = bool(index != 1)
        self.cmbLPU.setEnabled(enable)
        self.cmbEventSetPerson.setEnabled(enable)
        self.cmbEventType.setEnabled(enable)


    def setSortEvents(self, col):
        name = self.modelEvents.cols()[col].fields()[0]
        self.orderEvents = name
        header=self.tblEvents.horizontalHeader()
        header.setSortIndicatorShown(True)
        header.setClickable(True)
        sortAscending = self.modelEvents.headerSortingCol.get(col, False)
        header.setSortIndicator(col, Qt.AscendingOrder if sortAscending else Qt.DescendingOrder)
        self.orderEvents = self.orderEvents + (' ASC' if sortAscending else u' DESC')
        self.modelEvents.headerSortingCol[col] = not sortAscending
        self.getUpdateInfo()


    def setSortActions(self, col):
        name = self.modelActions.cols()[col].fields()[0]
        self.orderActions = name
        header=self.tblActions.horizontalHeader()
        header.setSortIndicatorShown(True)
        header.setClickable(True)
        sortAscending = self.modelActions.headerSortingCol.get(col, False)
        header.setSortIndicator(col, Qt.AscendingOrder if sortAscending else Qt.DescendingOrder)
        self.orderActions = self.orderActions + (' ASC' if sortAscending else u' DESC')
        self.modelActions.headerSortingCol[col] = not sortAscending
        self.getUpdateInfo()


class CEventsTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent, [
            CDateTimeCol(   u'Дата начала',                  ['setDate'], 8),
            CDateTimeCol(   u'Дата окончания',               ['execDate'], 8),
            CDateTimeCol(   u'Дата следующей явки',          ['nextEventDate'], 8),
            CRefBookCol(u'Тип события',                  ['eventType_id'], 'EventType', 10, showFields=2),
            CRefBookCol(u'Ответственный',                ['setPerson_id'], 'vrbPersonWithSpeciality', 20, showFields=2),
            CRefBookCol(u'Выполнивший сотрудник',        ['execPerson_id'], 'vrbPersonWithSpeciality', 20, showFields=2),
            CRefBookCol(u'Патрон',                       ['relative_id'], 'Client', 20, showFields=2),
            CTextCol(   u'Идентификатор события',        ['id'], 30),
            CTextCol(   u'Номер документа',        ['externalId'], 30),
            CDateCol(   u'Дата предыдущего события',     ['prevEventDate'], 8),
            CTextCol(   u'Является продолжением события',['prevEvent_id'],  6),
            CRefBookCol(u'МЭС',                          ['MES_id'], 'mes.MES', 15),
            CRefBookCol(u'Особенность выполнения МЭС',   ['mesSpecification_id'], 'rbMesSpecification', 15),
            CEnumCol(   u'Первичный',                    ['isPrimary'], codeIsPrimary, 8),
            CEnumCol(   u'Порядок',                      ['order'], orderTexts, 8),
            CEnumCol(   u'Состояние события',            ['isClosed'], [u'не закрыто', u'закрыто'], 8),
            CRefBookCol(u'Результат',                    ['result_id'], 'rbResult', 40),
            CRefBookCol(u'Тип актива',                   ['typeAsset_id'], 'rbEmergencyTypeAsset', 20, showFields=2),
            CRefBookCol(u'Куратор',                      ['curator_id'], 'vrbPersonWithSpeciality', 20, showFields=2),
            CRefBookCol(u'Ассистент',                    ['assistant_id'], 'vrbPersonWithSpeciality', 20, showFields=2),
            CRefBookCol(u'Модель пациента',              ['patientModel_id'], 'rbPatientModel', 20, showFields=2),
            CRefBookCol(u'Вид лечения',                  ['cureType_id'], 'rbCureType', 20, showFields=2),
            CRefBookCol(u'Метод лечения',                ['cureMethod_id'], 'rbCureMethod', 20, showFields=2),
            CTextCol(   u'Флаги финансирования',         ['payStatus'], 8),
            CDoubleCol(   u'Сумма по услугам',           ['totalCost'], 8),
            CTextCol(   u'Примечание',                   ['note'],  6)
            ], 'Event')
        self.headerSortingCol = {}


class CActionsTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent, [
            CDateTimeCol(u'Дата назначения',                     ['directionDate'], 8),
            CDateTimeCol(u'Дата начала работы',                  ['begDate'], 8),
            CDateTimeCol(u'Плановая дата выполнения',            ['plannedEndDate'], 8),
            CRefBookCol(u'Тип действия',                         ['actionType_id'], 'ActionType', 10, showFields=2),
            CDateTimeCol(u'Дата выполнения',                     ['endDate'], 8),
            CRefBookCol(u'Исполнитель',                          ['person_id'], 'vrbPersonWithSpeciality', 20, showFields=2),
            CTextCol(   u'Уточненное наименование',              ['specifiedName'],  6),
            CTextCol(   u'Событие к которому относится действие',['event_id'],  6),
            CEnumCol(   u'Статус выполнения',                    ['status'], CActionStatus.names, 8),
            CRefBookCol(u'Назначивший',                          ['setPerson_id'], 'vrbPersonWithSpeciality', 20, showFields=2),
            CEnumCol(   u'Является срочным',                     ['isUrgent'], [u'нет', u'да'], 8),
            CTextCol(   u'Кабинет',                              ['office'],  6),
            CDoubleCol( u'Количество',                           ['amount'], 8),
            CDoubleCol( u'УЕТ',                                  ['uet'], 8),
            CEnumCol(   u'Выставлять счет',                      ['expose'], [u'нет', u'да'], 8),
            CTextCol(   u'Флаги финансирования',                 ['payStatus'], 8),
            CEnumCol(   u'Флаг считать',                         ['account'], [u'нет', u'да'], 8),
            CTextCol(   u'МКБ',                                  ['MKB'], 8),
            CTextCol(   u'Морфология МКБ',                       ['morphologyMKB'], 8),
            CRefBookCol(u'Тип финансирования',                   ['finance_id'], 'rbFinance', 20, showFields=2),
            CRefBookCol(u'Ссылка на назначение',                 ['prescription_id'], 'Action', 20, showFields=2),
            CRefBookCol(u'Ссылка на журнал забора тканей',       ['takenTissueJournal_id'], 'TakenTissueJournal', 20, showFields=2),
            CDateTimeCol(u'Дата и время согласования',           ['coordDate'], 8),
            CTextCol(   u'Сотрудник ЛПУ, согласовавший действие',['coordAgent'], 8),
            CTextCol(   u'Представитель плательщика (сотрудник СМО), согласовавший действие',['coordInspector'], 8),
            CTextCol(   u'Текст согласования',                   ['coordText'], 8),
            CRefBookCol(u'Ассистент',                            ['assistant_id'], 'vrbPersonWithSpeciality', 20, showFields=2),
            CEnumCol(   u'Предварительный результат',            ['preliminaryResult'], [u'не определен', u'получен', u'без результата'], 8),
            CTextCol(   u'Длительность',                         ['duration'],  6),
            CTextCol(   u'Периодичность',                        ['periodicity'],  6),
            CTextCol(   u'Кратность',                            ['aliquoticity'],  6),
            CRefBookCol(u'Накладная движения ЛСиИМН',            ['stockMotion_id'], 'StockMotion', 20, showFields=2),
            CRefBookCol(u'Визит',                                ['visit_id'], 'Visit', 20, showFields=2),
            CTextCol(   u'Примечание',                           ['note'],  6)
            ], 'Action')
        self.headerSortingCol = {}

