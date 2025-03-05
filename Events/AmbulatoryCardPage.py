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
from PyQt4.QtCore import QDate, QDateTime, QTime, Qt, pyqtSignature, SIGNAL, QVariant

from library.PrintInfo import CInfoContext
from library.PrintTemplates import applyTemplateList, CPrintAction, applyMultiTemplateList, getPrintTemplates

from library.TreeModel import CTreeModel, CTreeItemWithId
from library.Utils import forceDate, forceRef, forceString, toVariant, forceStringEx
from Events.ActionInfo import CActionInfo
from Events.EventInfo import CEventInfo
from Registry.Utils import getClientString

from Events.Ui_AmbulatoryCardPage import Ui_AmbulatoryCardPage


class CAmbulatoryCardPage(QtGui.QWidget, Ui_AmbulatoryCardPage):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setupUi(self)
        self.tblActions.setHeaderHidden(True)
        self._clientId = None
        self._filter = {}

        # models
        self.modelActions = CActionsTableModel(self)
        self.selectionModelActions = QtGui.QItemSelectionModel(self.modelActions, self)

        # views
        self.tblActions.setModel(self.modelActions)
        self.tblActions.setSelectionModel(self.selectionModelActions)

        self.connect(self.selectionModelActions, SIGNAL('currentChanged(QModelIndex,QModelIndex)'),
                     self.on_selectionModelActions_currentChanged)

        self.connect(self.btnSelect, SIGNAL('printByTemplate(int)'), self.on_btnSelect_printByTemplate)

        self._onResetFilter()
        self._onApplyFilter()
        self.setVisibleButtonPages(False)
        self.currentActionTemplateId = None
        self.actionTemplateIdList = []
        self.actionData = {}
        self.mapContextToPrintTemplateList = {}

    def setClientId(self, clientId):
        if self._clientId != clientId:
            self._clientId = clientId
        self.setWindowTitle(u'Пациент: %s' % (getClientString(self._clientId) if self._clientId else u'не известен'))
        self.getUpdateInfo()

    def _onResetFilter(self):
        self._filter = {}
        self.edtBegDate.setDate(QDate().currentDate().addMonths(-6))
        self.edtBegTime.setTime(QTime())
        self.edtEndDate.setDate(QDate().currentDate())
        self.edtEndTime.setTime(QTime(23, 59))
        self.cmbClass.setCurrentIndex(0)
        self.cmbActionType.setClass(None)
        self.cmbActionType.setValue(None)
        self.cbHaveTemplate.setChecked(True)
        self.lblTemplateName.setText('')

    def _onApplyFilter(self):
        self._filter['begDateTime'] = QDateTime(self.edtBegDate.date(), self.edtBegTime.time())
        self._filter['endDateTime'] = QDateTime(self.edtEndDate.date(), self.edtEndTime.time())
        self._filter['actionClass'] = self.cmbClass.currentIndex()
        self._filter['actionTypeId'] = self.cmbActionType.value()
        self._filter['haveTemplate'] = self.cbHaveTemplate.isChecked()
        self._filter['clientId'] = self._clientId
        self._filter['actionTypeIdList'] = []
        modelIndex = self.cmbActionType.currentModelIndex()
        if modelIndex and modelIndex.isValid() and modelIndex.internalPointer().id():
            self._filter['actionTypeIdList'] = self.cmbActionType.model().getItemIdList(modelIndex)

    def updateActions(self):
        self.tblActions.model().setFilter(self._filter)
        self.tblActions.model().loadData()
        self.tblActions.expandToDepth(0)

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
        self.updateActions()

    def setupBtnSelectMenu(self):
        menu = self.getPrintBtnMenu()
        self.btnSelect.setMenu(menu)
        self.btnSelect.setEnabled(bool(menu))

    def getPrintBtnMenu(self):
        menu = QtGui.QMenu()
        context = None
        record = self.tblActions.currentIndex().internalPointer().record
        if record:
            context = forceString(record.value('context'))
        if context:
            templates = self.getPrintTemplatesCache(context)
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
        self.tblActions.currentIndex().internalPointer().setTemplateId(templateId)

    def getSelectedTemplate(self, templateId):
        self.txtAmbulatoryCardReport.setText(u'')
        QtGui.qApp.setWaitCursor()
        try:
            actionItem = self.tblActions.currentIndex().internalPointer().record
            if actionItem:
                if templateId and templateId not in self.actionTemplateIdList:
                    self.actionTemplateIdList.append(templateId)
                self.setVisibleButtonPages(bool(len(self.actionTemplateIdList) > 1))
                self.actionData = self.tblActions.currentIndex().internalPointer().getActionData()
                self.currentActionTemplateId = templateId
                QtGui.qApp.call(self, applyTemplateList,
                                (self, self.currentActionTemplateId, [self.actionData], self.txtAmbulatoryCardReport))
                applyTemplateList(self, self.currentActionTemplateId, [self.actionData], self.txtAmbulatoryCardReport)
                self.btnNextEnabled(self.currentActionTemplateId, self.actionTemplateIdList)
                self.btnBackEnabled(self.currentActionTemplateId, self.actionTemplateIdList)
        except:
            self.txtAmbulatoryCardReport.setText(u'ОШИБКА ЗАПОЛНЕНИЯ ШАБЛОНА')
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
            if currentIndex == 0:
                self.btnBack.setEnabled(False)

    def setVisibleButtonPages(self, isEnable):
        self.btnBack.setVisible(isEnable)
        self.btnNext.setVisible(isEnable)
        self.btnNext.setEnabled(isEnable)
        self.btnSelect.setVisible(isEnable)

    def turnOverThePagesNext(self, templateId, templateIdList, data):
        self.txtAmbulatoryCardReport.setText('')
        if templateId in templateIdList:
            currentIndex = templateIdList.index(templateId)
            countTemplateId = len(templateIdList)
            if currentIndex >= countTemplateId - 1:
                self.btnNext.setEnabled(False)
            else:
                QtGui.qApp.setWaitCursor()
                try:
                    templateId = templateIdList[currentIndex + 1]
                    QtGui.qApp.call(self, applyTemplateList, (self, templateId, [data], self.txtAmbulatoryCardReport))
                    currentIndex = templateIdList.index(templateId)
                    if currentIndex >= countTemplateId - 1:
                        self.btnNext.setEnabled(False)
                finally:
                    QtGui.qApp.restoreOverrideCursor()
        return templateId

    def turnOverThePagesBack(self, templateId, templateIdList, data):
        self.txtAmbulatoryCardReport.setText('')
        if templateId in templateIdList:
            currentIndex = templateIdList.index(templateId)
            countTemplateId = len(templateIdList)
            if currentIndex == 0:
                self.btnBack.setEnabled(False)
            elif currentIndex <= countTemplateId - 1:
                QtGui.qApp.setWaitCursor()
                try:
                    templateId = templateIdList[currentIndex - 1]
                    QtGui.qApp.call(self, applyTemplateList, (self, templateId, [data], self.txtAmbulatoryCardReport))
                    currentIndex = templateIdList.index(templateId)
                    if currentIndex == 0:
                        self.btnBack.setEnabled(False)
                finally:
                    QtGui.qApp.restoreOverrideCursor()
        return templateId

    @pyqtSignature('')
    def on_btnNext_clicked(self):
        self.btnBack.setEnabled(True)
        self.currentActionTemplateId = self.turnOverThePagesNext(self.currentActionTemplateId,
                                                                 self.actionTemplateIdList, self.actionData)
        self.tblActions.currentIndex().internalPointer().setTemplateId(self.currentActionTemplateId)

    @pyqtSignature('')
    def on_btnBack_clicked(self):
        self.btnNext.setEnabled(True)
        self.currentActionTemplateId = self.turnOverThePagesBack(self.currentActionTemplateId,
                                                                 self.actionTemplateIdList, self.actionData)
        self.tblActions.currentIndex().internalPointer().setTemplateId(self.currentActionTemplateId)

    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelActions_currentChanged(self, current, previous):
        templateIdAndDataList = []
        currentItem = current.internalPointer()
        if currentItem.id():
            actionItem = currentItem.record
            templateIdAndDataList.append(
                self.getActionTemplate(forceString(actionItem.value('context')), currentItem.getActionData(),
                                       currentItem.getTemplateId(),
                                       btnUpdate=True))
        else:
            for item in currentItem.items():
                if item.id():
                    actionItem = item.record
                    templateIdAndDataList.append(
                        self.getActionTemplate(forceString(actionItem.value('context')), item.getActionData(),
                                               item.getTemplateId()))
                else:
                    for subItem in item.items():
                        if subItem.id():
                            actionItem = subItem.record
                            templateIdAndDataList.append(
                                self.getActionTemplate(forceString(actionItem.value('context')),
                                                       subItem.getActionData(), subItem.getTemplateId()))
        QtGui.qApp.setWaitCursor()
        try:
            QtGui.qApp.call(self, applyMultiTemplateList, (self, templateIdAndDataList, self.txtAmbulatoryCardReport))
        finally:
            QtGui.qApp.restoreOverrideCursor()

    def getPrintTemplatesCache(self, context):
        result = self.mapContextToPrintTemplateList.get(context, None)
        if result is None:
            result = getPrintTemplates(context, inAmbCard=True)
            self.mapContextToPrintTemplateList[context] = result
        return result

    def getActionTemplate(self, context, actionData=None, currentTemplateId=None, btnUpdate=False):
        actionTemplateList = self.getPrintTemplatesCache(context)
        actionTemplateIdList = [item.id for item in actionTemplateList]
        currentActionTemplateId = currentTemplateId if currentTemplateId else actionTemplateIdList[
            0] if actionTemplateIdList else None
        if btnUpdate:
            self.currentActionTemplateId = currentActionTemplateId
            self.actionTemplateIdList = actionTemplateIdList
            self.actionData = actionData
        else:
            self.currentActionTemplateId = None
            self.actionTemplateIdList = []
            self.actionData = {}
            self.btnBack.setEnabled(False)
        self.setVisibleButtonPages(bool(len(self.actionTemplateIdList) > 1))
        self.btnNextEnabled(self.currentActionTemplateId, self.actionTemplateIdList)
        self.btnBackEnabled(self.currentActionTemplateId, self.actionTemplateIdList)
        self.setupBtnSelectMenu()

        return currentActionTemplateId, actionData

    @pyqtSignature('int')
    def on_cmbClass_currentIndexChanged(self, index):
        self.cmbActionType.setClass((index - 1) if index else None)


class CActionsTableModel(CTreeModel):
    def __init__(self, parent=None):
        CTreeModel.__init__(self, parent, CActionsTableRootTreeItem(self))
        self._filter = {}
        self.mapGroupIdToItems = {}
        self.mapIdToItems = {}

    def setFilter(self, _filter):
        self._filter = _filter

    def loadData(self):
        actionClass = self._filter['actionClass']
        actionTypeId = self._filter['actionTypeId']
        actionTypeIdList = self._filter['actionTypeIdList']
        begDateTime = self._filter['begDateTime']
        endDateTime = self._filter['endDateTime']
        haveTemplate = self._filter['haveTemplate']
        clientId = self._filter['clientId']
        db = QtGui.qApp.db
        tableAction = db.table('Action')
        tableActionType = db.table('ActionType')
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        tableMAT = db.table('rbMedicalAidType')
        cond = [tableAction['deleted'].eq(0)]

        queryTable = tableAction.innerJoin(tableActionType, tableAction['actionType_id'].eq(tableActionType['id']))
        queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
        queryTable = queryTable.leftJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
        queryTable = queryTable.leftJoin(tableMAT, tableEventType['medicalAidType_id'].eq(tableMAT['id']))
        if actionClass:
            cond.append(tableActionType['class'].eq(actionClass - 1))
            cond.append(tableActionType['deleted'].eq(0))
        if actionTypeIdList:
            cond.append(tableAction['actionType_id'].inlist(actionTypeIdList))
        elif actionTypeId:
            cond.append(tableAction['actionType_id'].eq(actionTypeId))
        if haveTemplate:
            cond.append(tableActionType['context'].ne(''))
        if begDateTime and begDateTime.isValid():
            cond.append(tableAction['begDate'].ge(begDateTime))
        if endDateTime and endDateTime.isValid():
            cond.append(tableAction['begDate'].le(endDateTime))
        cond.append(tableEvent['client_id'].eq(clientId))
        cond.append(tableEvent['deleted'].eq(0))
        cond.append(tableActionType['flatCode'].ne('soc001'))
        codeList = ['21', '22', '31', '32', '01', '02', '271', '272', '261', '262', '211', '233', '244', '241']
        cond.append(db.joinOr([tableMAT['regionalCode'].inlist(codeList), tableActionType['flatCode'].eq('epikriz')]))
        self.mapGroupIdToItems = {}
        self.mapIdToItems = {}
        cols = [tableAction['id'], tableAction['event_id'], tableAction['begDate'], tableAction['directionDate'],
                tableAction['endDate'], tableAction['actionType_id'], tableActionType['code'], tableActionType['name'],
                tableActionType['context']]
        order = tableAction['begDate'].name()
        query = db.query(db.selectStmt(queryTable, cols, where=cond, order=order))
        while query.next():
            record = query.record()
            actionId = forceRef(record.value('id'))
            date = forceDate(record.value('begDate'))
            code = forceStringEx(record.value('code'))
            name = forceStringEx(record.value('name'))
            item = (actionId, code, name, record)
            items = self.mapGroupIdToItems.setdefault(date.toPyDate(), [])
            items.append(item)
            self.mapIdToItems[actionId] = item
        self.getRootItem().loadChildren()


class CActionsTableTreeItem(CTreeItemWithId):
    def __init__(self, parent, itemId, code, name, model, date, record):
        CTreeItemWithId.__init__(self, parent, name, itemId)
        self._model = model
        self._code = code
        self._name = name
        self._maxCodeLen = 5
        self.date = date
        self.record = record
        self._currentTemplateId = None
        self._actionData = {}
        if record:
            self.loadActionData()

    def loadChildren(self):
        return []

    def setTemplateId(self, templateId):
        self._currentTemplateId = templateId

    def getTemplateId(self):
        return self._currentTemplateId

    def loadActionData(self):
        actionId = forceRef(self.record.value('id'))
        eventId = forceRef(self.record.value('event_id'))
        context = CInfoContext()
        eventInfo = context.getInstance(CEventInfo, eventId)
        eventActions = [context.getInstance(CActionInfo, actionId)]
        action = context.getInstance(CActionInfo, actionId)
        self._actionData = {'event': eventInfo,
                            'action': action,
                            'client': eventInfo.client,
                            'actions': eventActions,
                            'currentActionIndex': 0,
                            'tempInvalid': None}

    def getActionData(self):
        return self._actionData

    def data(self, column):
        if column == 0:
            if self._code:
                s = '%-*s|%s' % (self._maxCodeLen, self._code, self._name)
            else:
                s = self._name
            return toVariant(s)
        else:
            return QVariant()


class CActionsTableRootTreeItem(CActionsTableTreeItem):
    def __init__(self, model):
        CActionsTableTreeItem.__init__(self, None, None, '', u'Амбулаторная карта', model, None, None)

    def loadChildren(self):
        self.removeChildren()
        result = []
        items = self._model.mapGroupIdToItems
        for date in sorted(items, reverse=True):
            result.append(CActionsTableDateTreeItem(self, date, self._model))
        return result

    def flags(self):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def reset(self):
        if self._items is None:
            return False
        else:
            self._items = None
            return True


class CActionsTableDateTreeItem(CActionsTableTreeItem):
    def __init__(self, parent, date, model):
        CActionsTableTreeItem.__init__(self, parent, None, '', date, model, date, None)

    def flags(self):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def loadChildren(self):
        result = []
        items = self._model.mapGroupIdToItems.get(self.date, None)
        for item in items:
            result.append(CActionsTableTreeItem(self, item[0], item[1], item[2], self._model, self.date, item[3]))
        return result
