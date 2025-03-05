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

from PyQt4.QtCore import QDate

from Events.ActionStatus import CActionStatus

from library.Utils import forceDate, forceDateTime, forceInt, toVariant



_emptyExecutionPlan = object()


class CRelationsPlanGroup(object):
    def __init__(self, relatedActionTypes=None):
        self._relatedActionTypes = relatedActionTypes
        self._items = []
        self._copiedFrom = None


    def hasSavedItems(self):
        for item in self._relatedActionTypes.items:
            if item.id:
                return True
        return False


    def note(self):
        return self._relatedActionTypes.note


    def getSmnnUUID(self):
        return self._executionPlan.smnnUUID


    def getLfFormId(self):
        return self._executionPlan.lfFormId


    def setNote(self, value):
        self._relatedActionTypes.note = value


    def copy(self):
        copiedEp = self._relatedActionTypes.makeCopy() if self._relatedActionTypes else None
        result = CRelationsPlanGroup(copiedEp)
        result._items = self._items
        result._copiedFrom = self
        return result


    @property
    def actionTypeId(self):
        return self._items[0].action.getType().id


    @property
    def smnnUUID(self):
        return self._getItemSmnnUUID(self._items[0])

    @property
    def smnnGrlsLfId(self):
        return self._getItemSmnnGrlsLfId(self._items[0])

    def _getItemSmnnUUID(self, item):
        return item.action.getSmnnUUIDPropertyValue()

    def _getItemSmnnGrlsLfId(self, item):
        return item.action.getSmnnGrlsLfPropertyValue()

    @property
    def items(self):
        return self._items

    def addItem(self, item):
        self._items.append(item)

        if item.action.getId():
            self._sortLoadedItems()

        return True

    def removeItem(self, item):
        self._items.remove(item)
        

    def _sortLoadedItems(self):
        # Этот метод вызыватся когда мы пересортируем загруженные из БД записи.
        # То есть должен быть маппинг id действия с расписанием выполнения
        orders = {}
        if self._relatedActionTypes:
            for epi in self._relatedActionTypes.items:
                orders[epi.actionId] = epi.idx

            self._items.sort(key=lambda item: orders[item.action.getId()])

    @classmethod
    def makeFrom(cls, obj):
        if isinstance(obj, cls):
            return obj
        return obj.rGroup
    
    
class CRelationsProxyModelGroup(object):
    def __init__(self, model):
        self._model = model
        self._rGroup = CRelationsPlanGroup()
        self._reversedItems = None
        self._mapItem2Row = {}
        self._mapRow2Item = {}
        self._mapProxyRow2ModelRow = {}
        self._expanded = False
        self._headModelRow = None
        self._actionTypeId = None
        self.idx = None
        self._copiedFrom = None

    def getSortValue(self, key):
        if key == 'idx':
            return forceInt(self.items[-1].record.value('idx'))
        return None

    def bindModel(self, model):
        self._model = model

    def hasSavedItems(self):
        return self._rGroup.hasSavedItems()


    def note(self):
        return self._rGroup.note()

    def updateSpecifiedName(self):
        if len(self._mapItem2Row) != 1:
            return
        action = self.headItem.action
        if action:
            action.updateSpecifiedName()

    def copy(self):
        result = CRelationsProxyModelGroup(self._model)
        result._copiedFrom = self
        result._rGroup = self._rGroup.copy()
        result._reversedItems = self._reversedItems
        result._mapItem2Row = self._mapItem2Row
        result._mapRow2Item = self._mapRow2Item
        result._mapProxyRow2ModelRow = self._mapProxyRow2ModelRow
        result._expanded = self._expanded
        result._headModelRow = self._headModelRow
        result._actionTypeId = self._actionTypeId
        return result

    @property
    def rGroup(self):
        return self._rGroup

    @property
    def model(self):
        return self._model

    @property
    def items(self):
        items = self._rGroup.items or []

        return items

    @property
    def orderedItems(self):
        return self._rGroup.items

    @property
    def actionTypeId(self):
        return self._rGroup.actionTypeId

    @property
    def nomenclatureId(self):
        return self._rGroup.nomenclatureId

    @property
    def smnnUUID(self):
        return self._epGroup.smnnUUID

    @property
    def smnnGrlsLfId(self):
        return self._epGroup.smnnGrlsLfId

    @property
    def expanded(self):
        return self._expanded

    @property
    def firstItem(self):
        return self._rGroup.items[0]

    @property
    def headItem(self):
        return self.getHeadItem()

    def increaseItemsIdx(self, count, group):
        for item in self.items:
            record = item.record
            idx = forceInt(record.value('idx'))
            if idx and idx+count >= 0:
                record.setValue('idx', toVariant(idx+count))
            elif group.proxyRow:
                record.setValue('idx', toVariant(group.proxyRow))
            else:
                record.setValue('idx', toVariant(self.idx))
            self.idx = forceInt(record.value('idx'))

    def decreaseItemsIdx(self, count, group):
        for item in self.items:
            record = item.record
            idx = forceInt(record.value('idx'))
            if idx and idx-count >= 0:
                record.setValue('idx', toVariant(idx-count))
            elif group.proxyRow:
                record.setValue('idx', toVariant(group.proxyRow))
            else:
                record.setValue('idx', toVariant(self.idx))
            self.idx = forceInt(record.value('idx'))

    def canDownInGroup(self, proxyRow):
        return self._expanded

    def downProxyRow(self, proxyRow):
        return False

    def canUpInGroup(self, proxyRow):
        return self._expanded

    def upProxyRow(self, proxyRow):
        return False

    def getHeadItem(self):
        return self.items[0]

    def getItem(self, proxyRow):
        if self._expanded:
            return self._mapRow2Item[self._mapProxyRow2ModelRow[proxyRow]]
        else:
            return self._rGroup.items[0]

    def resetMapping(self, model):
        self._mapRow2Item.clear()
        self._mapItem2Row.clear()

        modelItems = model.items()
        for item in self.items:
            modelRow = modelItems.index(item)
            self._mapItem2Row[item] = modelRow
            self._mapRow2Item[modelRow] = item

        self._mapProxyRow2ModelRow.clear()
        self._prepareOrderView()

    def canBeGrouped(self):
        return self.itemsCount() > 1

    def mapRows(self, proxyRow, item):
        modelRow = self._mapItem2Row[item]
        self._mapProxyRow2ModelRow[proxyRow] = modelRow

    def itemsCount(self):
        return len(self._rGroup.items)

    def setExpanded(self, value):
        self._expanded = value

    def setNote(self, value, updateExecutionPlan=False):
        if len(self._mapItem2Row) != 1:
            return
        action = self.headItem.action
        action.setNote(value)
        if not self._rGroup._executionPlan.__origin__ and updateExecutionPlan:
            action.updateExecutionPlanByRecord()
            self._rGroup._executionPlan = action.getExecutionPlan()
        else:
            self._rGroup._executionPlan.setNote(value)


    def setSmnnUUID(self, value, updateExecutionPlan=False):
        if len(self._mapItem2Row) != 1:
            return
        action = self.headItem.action
        if not self._epGroup._executionPlan.__origin__ and updateExecutionPlan:
            action.updateExecutionPlanByRecord()
            self._epGroup._executionPlan = action.getExecutionPlan()
        else:
            self._epGroup._executionPlan.setSmnnUUID(value)


    def setLfFormId(self, value, updateExecutionPlan=False):
        if len(self._mapItem2Row) != 1:
            return
        action = self.headItem.action
        if not self._epGroup._executionPlan.__origin__ and updateExecutionPlan:
            action.updateExecutionPlanByRecord()
            self._epGroup._executionPlan = action.getExecutionPlan()
        else:
            self._epGroup._executionPlan.setLfFormId(value)


    def addItem(self, modelRow, item):
        if not self._rGroup.addItem(item):
            return False

        self._mapItem2Row[item] = modelRow
        self._mapRow2Item[modelRow] = item
        self._prepareOrderView()

        return True

    def bindFirstItemModelRow(self, modelRow):
        assert len(self._mapItem2Row) == 1
        item = self.headItem
        self._mapItem2Row[item] = modelRow
        self._mapRow2Item[modelRow] = item
        self._prepareOrderView()
        return True


    def getModelRow(self, proxyRow, model):
        if self._expanded:
            return self._mapProxyRow2ModelRow[proxyRow]

        if self._headModelRow is None:
            self._headModelRow = model.items().index(self.items[0])

        return self._headModelRow

    def getModelRows(self):
        return self._mapProxyRow2ModelRow.values()

    def isHeadItem(self, proxyRow, model):
        if self._headModelRow is None and self.items[0] in model.items():
            self._headModelRow = model.items().index(self.items[0])

        if not self._expanded:
            return True

        modelRow = self.getModelRow(proxyRow, model)
        return self._headModelRow == modelRow

    def deleteProxyRow(self, proxyRow, model):
        modelRow = self.getModelRow(proxyRow, model)
        item = self._mapRow2Item[modelRow]
        self._rGroup.removeItem(item)
        del self._mapItem2Row[item]
        del self._mapRow2Item[modelRow]
        del self._mapProxyRow2ModelRow[proxyRow]
        self._prepareOrderView()

    @property
    def proxyRows(self):
        return self._mapProxyRow2ModelRow.keys()

    def _prepareOrderView(self):
        self._headModelRow = None
        self._reversedItems = None

    def __contains__(self, item):
        return item in self._rGroup.items

    def __iter__(self):
        return iter(self.items)

    def __len__(self):
        return len(self._rGroup.items) if self._expanded else 1 if len(self._rGroup.items) else 0
