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

from PyQt4.QtCore import QTime, QDateTime

from library.blmodel.Query import CQuery
from Events.BLModels.Action import CActionBLModel

from .ExecutionPlan import (
    CActionExecutionPlan,
    CActionExecutionPlanItem,
    CActionExecutionPlanItemNomenclature
)
from .ExecutionPlanType import (
    CActionExecutionPlanType,
    CNomenclatureExecutionPlanType,
    executionPlanType
)

from library.Utils import (
#    forceDouble,
    forceDate,
    forceInt,
    forceTime,
#    pyDate,
#    toVariant
)


class CActionExecutionPlanManager(object):
    def __init__(self, action):
        self._action = action
        self._executionPlan = None
        self._currentItem = None
        self._currentIndex = None
        self.groupingItem = None
        self.groupingInfo = []


    def setCurrentItemIndex(self, value=None):
        if self._currentItem is None:
            return

        if value is None and not self.executionPlan.id:
            value = len(self.executionPlan.items) - 1
            for idx, item in enumerate(self.executionPlan.items):
                if not item.executedDatetime:
                    value = idx
                    break

        if value is None:
            actionsIds = {}
            for item in self.executionPlan.items:
                if item.actionId:
                    actionsIds[item.actionId] = item
            if self._currentItem in self.executionPlan.items:
                self._currentIndex = self.executionPlan.items.index(self._currentItem)
                self._currentItem = self.executionPlan.items[self._currentIndex]
            elif self._currentItem.actionId in actionsIds.keys():
                self._currentIndex = self.executionPlan.items.index(actionsIds[self._currentItem.actionId])
                self.executionPlan.items[self._currentIndex] = self._currentItem
            else:
                self._currentIndex = None
                self._currentItem = None
        else:
            self._currentIndex = value
            self._currentItem = self.executionPlan.items[value]


    def setCurrentItemExecuted(self):
        if self._action.isFinished() and not (
                self._currentItem.executedDatetime and self._currentItem.executedDatetime.isValid()):
            self._currentItem.executedDatetime = QDateTime.currentDateTime()


    @property
    def currentItem(self):
        return self._currentItem


    def plannedEndDate(self):
        return self.executionPlan.begDate.addDays(self.executionPlan.duration)


    def getDuration(self):
        return self.executionPlan.duration


    @property
    def executionPlan(self):
        if self._executionPlan:
            return self._executionPlan
        elif self._currentItem:
            return self._currentItem.executionPlan
        return None


    def setExecutionPlan(self, executionPlan, force=False):
        assert self._executionPlan is None or self._executionPlan is executionPlan or force
        self._executionPlan = executionPlan


    def getCurrentDosage(self):
        return self._currentItem.nomenclature.dosage if self._currentItem.nomenclature else None


    def getCurrentNomenclatureId(self):
        return self._currentItem.nomenclature.nomenclatureId


    def minExecutionPlanDate(self):
        return self._currentItem.date


    def defaultExecutionPlanCount(self):
        if self._action.getType().isNomenclatureExpense:
            return self._executionPlan.defaultExecutionPlanCountNE()
        else:
            return self._executionPlan.defaultExecutionPlanCount()


    def setCurrentItem(self, item):
        self._currentItem = item
        self._executionPlan = item.executionPlan
        self._currentIndex = self.executionPlan.items.index(self._currentItem)


    def hasItemsToDo(self):
        return self.currentItem and not self.currentItem.executedDatetime
        # return self.executionPlan.hasItemsToDo()


    def getCurrentItemIndex(self):
        return self._currentIndex


    def getNextItem(self):
        if self._currentItem is None:
            return None
        
        if self._currentIndex is None:
            self._currentIndex = 0

        nextIndex = self._currentIndex + 1

        if nextIndex >= len(self._currentItem.executionPlan.items):
            return None

        return self._currentItem.executionPlan.items[nextIndex]


    def recountMixedOrder(self):
        items = self._currentItem.executionPlan.items
        self._currentItem.idx = 0
        dateTimeItems = {}
        for item in items[1:]:
            date = item.date
            time = item.time if item.time else QTime(0, 0)
            dateTimeItems[(date, time)] = item
        idx = 1
        for k in sorted(dateTimeItems.keys()):
            dateTimeItems[k].idx = idx
            idx += 1


    def recountOrder(self):
        items = self._currentItem.executionPlan.items
        if items[0] is not self._currentItem:
            raise RuntimeError()

        self._currentItem.idx = 0

        dateTimeItems = {}

        for item in items[1:]:
            date = item.date
            time = item.time if item.time else QTime(0, 0)
            dateTimeItems[(date, time)] = item

        idx = 1
        for k in sorted(dateTimeItems.keys()):
            dateTimeItems[k].idx = idx
            idx += 1


    def load(self, executionPlanRecord=None):
        actionId = self._action.getId()
        if not actionId:
            return
        if executionPlanRecord is not None:
            if executionPlanRecord:
                item = CActionExecutionPlanItem(record=executionPlanRecord[0])
            else:
                return
        else:
            item = CQuery(
                CActionExecutionPlanItem,
                CActionExecutionPlanItem.Table,
                fields=CActionExecutionPlanItem.FieldsList,
                where=CActionExecutionPlanItem.actionId == actionId,
                order=[CActionExecutionPlanItem.date.fullName,
                       CActionExecutionPlanItem.idx.fullName]
            ).getFirst()

        if item:
            self._currentItem = item


    def saveFromCurrentItems(self):
        if not self._currentItem:
            return

        self.save()
        nextItem = self.getNextItem()
        while nextItem:
            self.setCurrentItemIndex(self.executionPlan.items.index(nextItem))
            self.setCurrentItemExecuted()
            self.saveFromCurrentItem(nextItem)
            nextItem = self.getNextItem()


    def saveFromCurrentItem(self, currentItem):
        if not currentItem:
            return

        if currentItem.id and currentItem.executedDatetime:
            if not currentItem.actionId:
                currentItem.actionId = self._action.getId()
            CQuery.save(currentItem)
            return

        executionPlan = currentItem.executionPlan
        currentItem.actionId = self._action.getId()
        self.setCurrentItemExecuted()
        if executionPlan.id:
            CQuery.save(executionPlan)
            CQuery.save(currentItem)
            if currentItem.nomenclature:
                CQuery.save(currentItem.nomenclature)
            for item in executionPlan.items:
                if item != currentItem and (not item.id or item.getIsDirty()):
                    self._saveItem(item, executionPlan)
            return
        if not executionPlan.id:
            executionPlan.id = CQuery.save(executionPlan)
        itemIds = []
        for item in executionPlan.items:
            itemIds.append(self._saveItem(item, executionPlan))
        itemIdsToDlete = CQuery(CActionExecutionPlanItem, where=[CActionExecutionPlanItem.id.notInlist(itemIds), CActionExecutionPlanItem.masterId == executionPlan.id]).getIdList()
        CQuery.delete(CActionExecutionPlanItem, CActionExecutionPlanItem.id.inlist(itemIdsToDlete))
        CQuery.delete(CActionExecutionPlanItemNomenclature, CActionExecutionPlanItemNomenclature.actionExecutionPlanItemId.inlist(itemIdsToDlete))


    def save(self):
        if not self._currentItem:
            return

        if self._currentItem.id and self._currentItem.executedDatetime:
            if not self._currentItem.actionId:
                self._currentItem.actionId = self._action.getId()
            if self.groupingItem:
                if not self.groupingItem == self._currentItem:
                    self._currentItem._record.setValue('group_id', forceInt(self.groupingItem._record.value('id')))
            result = CQuery.save(self._currentItem)
            self._currentItem._record.setValue('id', result)
            if not forceInt(self._currentItem._record.value('group_id')):
                if self.groupingItem:
                    self._currentItem._record.setValue('group_id', result)
                    result = CQuery.save(self._currentItem)
            return

        executionPlan = self._currentItem.executionPlan

        self._currentItem.actionId = self._action.getId()
        self.setCurrentItemExecuted()

        if executionPlan.id:
            CQuery.save(executionPlan)
            if self.groupingItem:
                if not self.groupingItem == self._currentItem:
                    self._currentItem._record.setValue('group_id', forceInt(self.groupingItem._record.value('id')))
            result = CQuery.save(self._currentItem)
            self._currentItem._record.setValue('id', result)
            if not forceInt(self._currentItem._record.value('group_id')):
                if self.groupingItem:
                    self._currentItem._record.setValue('group_id', result)
                    result = CQuery.save(self._currentItem)
            if self._currentItem.nomenclature:
                CQuery.save(self._currentItem.nomenclature)

            for item in executionPlan.items:
                if item != self._currentItem and (not item.id or item.getIsDirty()):
                    self._saveItem(item, executionPlan)
            return

        if not executionPlan.id:
            executionPlan.id = CQuery.save(executionPlan)

        itemIds = []
        for item in executionPlan.items:
            itemIds.append(self._saveItem(item, executionPlan))

        itemIdsToDlete = CQuery(
            CActionExecutionPlanItem,
            where=[CActionExecutionPlanItem.id.notInlist(itemIds),
                   CActionExecutionPlanItem.masterId == executionPlan.id]
        ).getIdList()

        CQuery.delete(
            CActionExecutionPlanItem,
            CActionExecutionPlanItem.id.inlist(itemIdsToDlete)
        )

        CQuery.delete(
            CActionExecutionPlanItemNomenclature,
            CActionExecutionPlanItemNomenclature.actionExecutionPlanItemId.inlist(itemIdsToDlete)
        )


#    def _deleted(self):
#        if not self._currentItem:
#            return
#        itemIds = []
#        executionPlan = self._currentItem.executionPlan
#        for item in executionPlan.items:
#            itemIds.append(item.id)
#
#        itemIdsToDlete = CQuery(
#            CActionExecutionPlanItem,
#            where=[CActionExecutionPlanItem.id.notInlist(itemIds),
#                   CActionExecutionPlanItem.masterId == executionPlan.id]
#        ).getIdList()
#
#        CQuery.delete(
#            CActionExecutionPlanItem,
#            CActionExecutionPlanItem.id.inlist(itemIdsToDlete)
#        )
#
#        CQuery.delete(
#            CActionExecutionPlanItemNomenclature,
#            CActionExecutionPlanItemNomenclature.actionExecutionPlanItemId.inlist(itemIdsToDlete)
#        )


    def _saveItem(self, item, executionPlan):
        if item.id and item.executedDatetime:
            return item.id

        if not item.masterId:
            item.masterId = executionPlan.id

        if not item.actionId and item.action and item.action.id:
            item.actionId = item.action.id

        if self.groupingItem:
            if not self.groupingItem == item:
                item._record.setValue('group_id', forceInt(self.groupingItem._record.value('id')))
        itemId = CQuery.save(item)
        item._record.setValue('id', itemId )
        if not forceInt(item._record.value('group_id')):
            if self.groupingItem:
                item._record.setValue('group_id', itemId)
                itemId = CQuery.save(item)
        if item.nomenclature:
            if not item.nomenclature.nomenclatureId:
                nomenclatureId = self._action.findNomenclaturePropertyValue()
                if nomenclatureId:
                    item.nomenclature.nomenclatureId = nomenclatureId

            if item.nomenclature and not item.nomenclature.dosage:
                dosage = self._action.findDosagePropertyValue()
                if dosage:
                    item.nomenclature.dosage = dosage

            item.nomenclature.actionExecutionPlanItemId = item.id
            CQuery.save(item.nomenclature)
        return itemId


    def checkCurrentItem(self):
        executionPlan = self._currentItem.executionPlan
        for item in executionPlan.items:
            if not item.executedDatetime:
                if item is self._currentItem:
                    return
                item.action, self._currentItem.action = self._currentItem.action, None
                self._currentItem = item
                return


    @property
    def initialized(self):
        return bool(self._currentItem)


    def update(self, forceDuration=False, daysExecutionPlan=[]):
        record = self._action.getRecord()
        actionType = self._action.getType()
        if actionType.isNomenclatureExpense:
            duration = forceInt(record.value('duration')) or 1 # Длительность
        else:
            duration = forceInt(record.value('duration')) # Длительность

        # periodicity - это интервал. Сколько полных дней между назначениями
        periodicity = forceInt(record.value('periodicity'))

        # кратность
        aliquoticity = forceInt(record.value('aliquoticity')) or 1 # кратность

        # Количество процедур
        quantity = forceInt(record.value('quantity'))

        if not (duration >= 1 or aliquoticity >= 1 or quantity >= 1 or forceDuration):
            return

        showTime = actionType.showTime if actionType else False
        begDate = forceDate(record.value('begDate'))
        begTime = forceTime(record.value('begDate')) if showTime else None

        if not self._currentItem:
            self._create(begDate, begTime, duration, aliquoticity, periodicity, quantity, daysExecutionPlan=daysExecutionPlan)
            return

        self._update(begDate, begTime, duration, aliquoticity, periodicity, quantity, daysExecutionPlan=daysExecutionPlan)


    def loadExecutionPlan(self):
        return self._currentItem.executionPlan


    def _create(self, begDate, begTime, duration, aliquoticity, periodicity, quantity, daysExecutionPlan=[]):
        executionPlan = CActionExecutionPlan()

        if self._action.getType().isNomenclatureExpense:
            executionPlan.type = CNomenclatureExecutionPlanType.type
        else:
            executionPlan.type = CActionExecutionPlanType.type

        executionPlan.begDate = begDate
        executionPlan.begTime = begTime
        executionPlan.duration = duration
        executionPlan.aliquoticity = aliquoticity
        executionPlan.periodicity = periodicity
        executionPlan.quantity = quantity
        executionPlan.daysExecutionPlan = daysExecutionPlan
        items = executionPlan.createItems(daysExecutionPlan=daysExecutionPlan)

        self._currentItem = items[0] if len(items) > 0 else CActionExecutionPlanItem()
        self._executionPlan = self._currentItem.executionPlan = executionPlan
        self._bindCurrentItemWithAction()


    def _clear(self):
        self._currentItem =  CActionExecutionPlanItem()
        self._executionPlan = self._currentItem.executionPlan = CActionExecutionPlan()
        self._bindCurrentItemWithAction()


    def _update(self, begDate, begTime, duration, aliquoticity, periodicity, quantity, daysExecutionPlan=[]):
        self._currentItem.executionPlan = None
        self._executionPlan = None
        self._create(begDate, begTime, duration, aliquoticity, periodicity, quantity, daysExecutionPlan=daysExecutionPlan)


    def _bindCurrentItemWithAction(self):
        ept = executionPlanType(self._currentItem.executionPlan)
        action_bl = CActionBLModel(self._action.getRecord())
        ept.bindItemWithAction(self._currentItem, action_bl)


    def bindAction(self, action):
        self._action = action
        self._bindCurrentItemWithAction()
