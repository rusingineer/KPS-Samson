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

import math
from PyQt4.QtCore import QDateTime, QVariant

from library.blmodel.Model import CModel, CDocumentModel
from library.blmodel.ModelAttribute import (
    CIntAttribute,
    CDateTimeAttribute,
    CDateAttribute,
    CRefAttribute,
    CTimeAttribute,
    CDoubleAttribute,
    CStringAttribute
)
from library.blmodel.ModelRelationship import CRelationship #, CManyRelationship
from library.blmodel.Query import CQuery
from library.CachedProperty import cached_property

#from library.Utils import pyDate, toVariant, forceDouble

from .ExecutionPlanType import executionPlanType, CNomenclatureExecutionPlanType


class Items(list):
    def __init__(self, *args, **kwargs):
        self._mapDateTimeToItems = {}
        self._mapDateToItems = {}
        list.__init__(self, *args, **kwargs)
        self._remap()


    def append(self, items):
        list.append(self, items)
        self._remap()


    def extend(self, items):
        list.extend(self, items)
        self._remap()


    def remove(self, item):
        list.remove(self, item)
        self._remap()


    def __add__(self, items):
        result = list.__add__(self, items)
        return Items(result)


    def __iadd__(self, items):
        self.extend(items)
        return self


    def __setitem__(self, index, value):
        list.__setitem__(self, index, value)
        self._remap()


    def _remap(self):
        self._mapDateTimeToItems.clear()
        self._mapDateToItems.clear()
        for idx, item in enumerate(self):
            item.idx = idx
            year = item.date.year()
            month = item.date.month()
            day = item.date.day()
            hour = item.time.hour() if item.time else 0
            minute = item.time.minute() if item.time else 0
            self._mapDateTimeToItems.setdefault((year, month, day, hour, minute), []).append(item)
            self._mapDateToItems.setdefault((year, month, day), []).append(item)


    def _remapIdx(self):
        for idx, item in enumerate(self):
            if not bool(item.date):
                item.idx = item.aliquoticityIdx
                self.insert(item.aliquoticityIdx, self.pop(idx))
        for idx, item in enumerate(self):
            item.idx = idx
        aliquoticityIdxList = []
        for idx, item in enumerate(self):
            if item.aliquoticityIdx not in aliquoticityIdxList:
                for idxAliq, itemAliq in enumerate(self):
                    if item.aliquoticityIdx == itemAliq.aliquoticityIdx:
                        itemAliq.aliquoticityIdx = item.idx
                aliquoticityIdxList.append(item.aliquoticityIdx)


    def getItemsByDateTime(self, datetime):
        date = datetime.date()
        time = datetime.time()
        return self._mapDateTimeToItems.get(
            (date.year(), date.month(), date.day(), time.hour(), time.minute())
        )


    def getItemsByDate(self, date):
        return self._mapDateToItems.get(
            (date.year(), date.month(), date.day())
        )


    def getCountItemsByDate(self, date):
        items = self._mapDateToItems.get((date.year(), date.month(), date.day()))
        return len(items) if items else 0


    def getCountItemsNotExecutedByDate(self, date):
        result = 0
        items = self._mapDateToItems.get((date.year(), date.month(), date.day()))
        for item in items:
            if not item.executedDatetime:
                result += 1
        return result


    def deleteItemsByDate(self, date):
        dateKey = (date.year(), date.month(), date.day())
        if dateKey not in self._mapDateToItems:
            return

        items = self.getItemsByDate(date)
        for item in items:
            list.remove(self, item)

        del self._mapDateToItems[dateKey]
        dtKeys = [
            key for key in
            self._mapDateTimeToItems.keys()
            if dateKey == key[:3]
        ]

        for k in dtKeys:
            del self._mapDateTimeToItems[k]

        for x, item in enumerate(self):
            if not item.executedDatetime:
                item.setIsDirty(True)
                self[x] = item

        self._remap()


    def setItemsByDate(self, date, items, new=False, isLastDayCourse=False):
        dateKey = (date.year(), date.month(), date.day())
        if dateKey in self._mapDateToItems:
            self._setInExistsDate(date, items, new=new)
            return

        elif min(self._mapDateToItems.keys()) > dateKey:
            itemsToPass = []
            for i in items:
                itemToPass = i.makeCopy(new=True) if not new else i
                if i.nomenclature:
                    nomenclatureItem = CActionExecutionPlanItemNomenclature()
                    nomenclatureItem.nomenclatureId = i.nomenclature.nomenclatureId
                    nomenclatureItem.dosage = i.nomenclature.dosage
                    itemToPass.nomenclature = nomenclatureItem
                    nomenclatureItem.actionExecutionPlanItem = itemToPass

                itemToPass.date = date
                itemToPass.actionId = itemToPass.action = itemToPass.executedDatetime = itemToPass.id = None
                itemToPass.setIsDirty(True)
                itemsToPass.append(itemToPass)
            self[0: 0] = itemsToPass
            self._remap()
            return

        elif max(self._mapDateToItems.keys()) < dateKey:
            cnt = len(self)
            itemsToPass = []
            for i in items:
                itemToPass = i.makeCopy(new=True) if not new else i
                if i.nomenclature:
                    nomenclatureItem = CActionExecutionPlanItemNomenclature()
                    nomenclatureItem.nomenclatureId = i.nomenclature.nomenclatureId
                    nomenclatureItem.dosage = i.nomenclature.dosage
                    itemToPass.nomenclature = nomenclatureItem
                    nomenclatureItem.actionExecutionPlanItem = itemToPass

                itemToPass.date = date
                itemToPass.actionId = itemToPass.action = itemToPass.executedDatetime = itemToPass.id = None
                itemToPass.setIsDirty(True)
                itemsToPass.append(itemToPass)
            self[cnt: cnt] = itemsToPass
            self._remap()
            return

        else:
            self._setInSpaceDay(date, items, new=new)


    def getMaxDateToItems(self):
        return max([i.date for i in self])


    def getIdxToItems(self):
        return len(self)


    def setItemsByLastDate(self, date, items):
        dateKey = (date.year(), date.month(), date.day())
        if dateKey in self._mapDateToItems:
            return []
        maxDateItems = max(self._mapDateToItems.keys())
        if maxDateItems and maxDateItems < dateKey:
            lastItems = self._mapDateToItems.get(maxDateItems)
            idx = len(self)
            itemsToPass = []
            for i in lastItems:
                itemToPass = i.makeCopy(new=True)
                if i.nomenclature:
                    nomenclatureItem = CActionExecutionPlanItemNomenclature()
                    nomenclatureItem.nomenclatureId = i.nomenclature.nomenclatureId
                    nomenclatureItem.dosage = i.nomenclature.dosage
                    itemToPass.nomenclature = nomenclatureItem
                    nomenclatureItem.actionExecutionPlanItem = itemToPass
                itemToPass.date = date
                itemToPass.idx = idx
                itemToPass.actionId = itemToPass.action = itemToPass.executedDatetime = itemToPass.id = None
                itemToPass.setIsDirty(True)
                itemsToPass.append(itemToPass)
                idx += 1
            self.extend(itemsToPass)
            self._remap()
            return itemsToPass
        return []


    def _setInSpaceDay(self, date, items, new=False):
        point = 0
        for x, item in enumerate(self):
            if item.date > date:
                break
            point = x

        itemsToPass = []
        for i in items:
            itemToPass = i.makeCopy(new=True) if not new else i
            if i.nomenclature:
                nomenclatureItem = CActionExecutionPlanItemNomenclature()
                nomenclatureItem.nomenclatureId = i.nomenclature.nomenclatureId
                nomenclatureItem.dosage = i.nomenclature.dosage
                itemToPass.nomenclature = nomenclatureItem
                nomenclatureItem.actionExecutionPlanItem = itemToPass

            itemToPass.date = date
            itemToPass.actionId = itemToPass.action = itemToPass.executedDatetime = itemToPass.id = None
            itemToPass.setIsDirty(True)
            itemsToPass.append(itemToPass)

        self[point: point] = itemsToPass
        self._remap()


    def setDosageToProcentInExists(self, procent, change):
        self.sort(key=lambda i: i.date)
        for x, item in enumerate(self):
            # Заменять можно только не выполненные
            if not item.executedDatetime and item.nomenclature:
                newDosage = item.nomenclature.dosage
                procentDosage = (newDosage*procent)/100.0
                if change == 1:
                    newDosage = math.floor(newDosage - procentDosage)
                elif change == 2:
                    newDosage = math.floor(newDosage + procentDosage)
                item.nomenclature.dosage = newDosage
                nomenclatureItem = item.nomenclature
                nomenclatureItem.actionExecutionPlanItem = item
                item.setIsDirty(True)
                self[x] = item
        self._remap()


    def setDosageToDateToProcentInExists(self, procent, change, date):
        self.sort(key=lambda i: i.date)
        for x, item in enumerate(self):
            # Заменять можно только не выполненные
            if item.date == date and not item.executedDatetime and item.nomenclature:
                newDosage = item.nomenclature.dosage
                procentDosage = (newDosage*procent)/100.0
                if change == 1:
                    newDosage = math.floor(newDosage - procentDosage)
                elif change == 2:
                    newDosage = math.floor(newDosage + procentDosage)
                item.nomenclature.dosage = newDosage
                nomenclatureItem = item.nomenclature
                nomenclatureItem.actionExecutionPlanItem = item
                item.setIsDirty(True)
                self[x] = item
                break
        self._remap()


    def setCalculationDosageInExists(self, calculationParam):
        self.sort(key=lambda i: i.date)
        for x, item in enumerate(self):
            # Заменять можно только не выполненные
            if not item.executedDatetime and item.nomenclature:
                newDosage = item.nomenclature.dosage
                newDosage = math.floor(newDosage*calculationParam)
                item.nomenclature.dosage = newDosage
                nomenclatureItem = item.nomenclature
                nomenclatureItem.actionExecutionPlanItem = item
                item.setIsDirty(True)
                self[x] = item
        self._remap()


    def setCalculationDosageToDateInExists(self, calculationParam, date):
        self.sort(key=lambda i: i.date)
        for x, item in enumerate(self):
            # Заменять можно только не выполненные
            if item.date == date and not item.executedDatetime and item.nomenclature:
                newDosage = item.nomenclature.dosage
                newDosage = math.floor(newDosage*calculationParam)
                item.nomenclature.dosage = newDosage
                nomenclatureItem = item.nomenclature
                nomenclatureItem.actionExecutionPlanItem = item
                item.setIsDirty(True)
                self[x] = item
                break
        self._remap()
        
    
    def setDosageInExists(self, dosage):
        self.sort(key=lambda i: i.date)
        for x, item in enumerate(self):
            # Заменять можно только не выполненные
            if not item.executedDatetime and item.nomenclature:
                item.nomenclature.dosage = dosage
                nomenclatureItem = item.nomenclature
                nomenclatureItem.actionExecutionPlanItem = item
                item.setIsDirty(True)
                self[x] = item
        self._remap()

    
    def setDosageToDateFirstItemInExists(self, dosage, date):
        self.sort(key=lambda i: i.date)
        for x, item in enumerate(self):
            # Заменять можно только не выполненные
            if item.date == date and not item.executedDatetime and item.nomenclature:
                item.nomenclature.dosage = dosage
                nomenclatureItem = item.nomenclature
                nomenclatureItem.actionExecutionPlanItem = item
                item.setIsDirty(True)
                self[x] = item
                break
        self._remap()
        

    def setDosageNomenclatureInExists(self, dosage, nomenclatureId):
        self.sort(key=lambda i: i.date)
        for x, item in enumerate(self):
            # Заменять можно только не выполненные
            if not item.executedDatetime and item.nomenclature:
                item.nomenclature.dosage = dosage
                item.nomenclature.nomenclatureId = nomenclatureId
                nomenclatureItem = item.nomenclature
                nomenclatureItem.actionExecutionPlanItem = item
                item.setIsDirty(True)
                self[x] = item
        self._remap()


    def setDosageNomenclatureFromDate(self, dosage, nomenclatureId, date):
        self.sort(key=lambda i: i.date)
        for x, item in enumerate(self):
            # Заменять можно только не выполненные
            if item.date > date and not item.executedDatetime:
                if not item.nomenclature:
                    nomenclatureItem = CActionExecutionPlanItemNomenclature()
                    nomenclatureItem.dosage = dosage
                    nomenclatureItem.nomenclatureId = nomenclatureId
                    item.nomenclature = nomenclatureItem
                    nomenclatureItem.actionExecutionPlanItem = item
                else:
                    item.nomenclature.dosage = dosage
                    item.nomenclature.nomenclatureId = nomenclatureId
                    nomenclatureItem = item.nomenclature
                    nomenclatureItem.actionExecutionPlanItem = item
                item.setIsDirty(True)
                self[x] = item
        self._remap()


    def setIsDirtyInExists(self, value):
        self.sort(key=lambda i: i.date)
        for x, item in enumerate(self):
            if not item.executedDatetime:
                item.setIsDirty(value)
                self[x] = item
        self._remap()


    def _setInExistsDate(self, date, items, new=False):
        startX = len(self)
        stopX = startX + 1

        d = None

        getItemIdentuty = lambda x: x.id if x.id else (id(x), 'm')
        mapDateItemsById = {}
        updDateItemsById = {}

        self.sort(key=lambda i: i.date)

        calculated = False
        for x, item in enumerate(self):
            if date == item.date:
                identity = getItemIdentuty(item)
                mapDateItemsById[identity] = item

            if calculated:
                continue

            if d is None:
                # Заменять можно только не выполненные
                if date == item.date and not item.executedDatetime:
                    d = item.date
                    startX = x
                    updDateItemsById[identity] = item
            else:
                if d != item.date:
                    stopX = x
                    calculated = True
                elif d == item.date and not item.executedDatetime:
                        updDateItemsById[identity] = item

        itemsToPass = []
        for i in items:
            identity = getItemIdentuty(i)
            if identity in mapDateItemsById:
                if identity in updDateItemsById:
                    toChangeItem = updDateItemsById[identity]
                    toChangeItem.time = i.time
                    if toChangeItem.nomenclature:
                        toChangeItem.nomenclature.dosage = i.nomenclature.dosage
                    toChangeItem.setIsDirty(True)
                    itemsToPass.append(toChangeItem)
                continue

            itemToPass = i.makeCopy(new=True) if not new else i
            if i.nomenclature:
                nomenclatureItem = CActionExecutionPlanItemNomenclature()
                nomenclatureItem.nomenclatureId = i.nomenclature.nomenclatureId
                nomenclatureItem.dosage = i.nomenclature.dosage
                itemToPass.nomenclature = nomenclatureItem
                nomenclatureItem.actionExecutionPlanItem = itemToPass

            itemToPass.date = date
            itemToPass.actionId = itemToPass.action = itemToPass.executedDatetime = itemToPass.id = None
            itemToPass.setIsDirty(True)
            itemsToPass.append(itemToPass)

        if itemsToPass:
            self[startX: stopX] = itemsToPass
        self._remap()


    def __contains__(self, item):
        if item.id:
            return item.id in [i.id for i in self]
        return list.__contains__(self, item)


    def index(self, item, start=None, stop=None):
        args = tuple()
        if start is not None:
            args += (start, )
            if stop is not None:
                args += (stop, )

        if item.id:
            return [i.id for i in self].index(item.id, *args)

        return list.index(self, item, *args)


    def updateByEP(self, ep):
        suggestedItems = executionPlanType(ep).createItems(
            ep.begDate,
            ep.begTime,
            ep.duration,
            ep.periodicity,
            ep.aliquoticity,
            ep.quantity,
            daysExecutionPlan=ep.daysExecutionPlan
        )

        lastExecutedItemDT = None

        for item in self:
            if item.executedDatetime:
                if lastExecutedItemDT is None:
                    lastExecutedItemDT = QDateTime(item.date, item.time)
                else:
                    lastExecutedItemDT = max(QDateTime(item.date, item.time), lastExecutedItemDT)

        if lastExecutedItemDT is None:
            newItems = suggestedItems
        else:
            aliquoticity = ep.aliquoticity or 1

            newItems = []

            lastExecutedItemDTCount = 0
            for item in self:
                dt = QDateTime(item.date, item.time)
                if dt < lastExecutedItemDT:
                    newItems.append(item)
                elif dt == lastExecutedItemDT and item.executedDatetime and lastExecutedItemDTCount < aliquoticity:
                    newItems.append(item)
                    lastExecutedItemDTCount += 1

            for item in suggestedItems:
                dt = QDateTime(item.date, item.time)
                if dt > lastExecutedItemDT:
                    newItems.append(item)
                elif dt == lastExecutedItemDT and lastExecutedItemDTCount < aliquoticity:
                    newItems.append(item)
                    lastExecutedItemDTCount += 1

        self[:] = newItems
        self._remap()
        return lastExecutedItemDT is None


class CActionExecutionPlan(CDocumentModel):
    __itemsInitialized__ = False

    tableName = 'ActionExecutionPlan'

    begDate = CDateAttribute()
    begTime = CTimeAttribute()
    type = CIntAttribute()
    duration = CIntAttribute()
    periodicity = CIntAttribute()
    aliquoticity = CIntAttribute()
    quantity = CIntAttribute()
    daysExecutionPlan = []
    scheduleWeekendDays = CStringAttribute()
    note = CStringAttribute()
    smnnUUID = CStringAttribute()
    lfFormId = CRefAttribute(name='lfForm_id')


    @property
    def itemsInitialized(self):
        return self.__itemsInitialized__


    @cached_property
    def items(self):
        return self.getItems()


    def hasItemsToDo(self):
        for item in self.items:
            if not item.executedDatetime:
                return True
        return False


    def setItemsByDate(self, date, items, isLastDayCourse=False):
        self.items.setItemsByDate(date, items, isLastDayCourse=isLastDayCourse)


    def setItemsByLastDate(self, date, items):
        self.items.setItemsByLastDate(date, items)


    def setDosageInExists(self, dosage):
        self.items.setDosageInExists(dosage)

    
    def setDosageToDateFirstItemInExists(self, dosage, date):
        self.items.setDosageToDateFirstItemInExists(dosage, date)
        
    
    def setDosageToProcentInExists(self, procent, change):
        self.items.setDosageToProcentInExists(procent, change)


    def setDosageToDateToProcentInExists(self, procent, change, date):
        self.items.setDosageToDateToProcentInExists(procent, change, date)

    


    def setIsDirtyInExists(self, value):
        self.items.setIsDirtyInExists(value)


    def setCalculationDosageInExists(self, calculationParam):
        self.items.setCalculationDosageInExists(calculationParam)


    def setCalculationDosageToDateInExists(self, calculationParam, date):
        self.items.setCalculationDosageToDateInExists(calculationParam, date)


    def setDosageNomenclatureInExists(self, dosage, nomenclatureId):
        self.items.setDosageNomenclatureInExists(dosage, nomenclatureId)


    def setDosageNomenclatureFromDate(self, dosage, nomenclatureId, date):
        self.items.setDosageNomenclatureFromDate(dosage, nomenclatureId, date)


    def getCountItemsByDate(self, date):
        return self.items.getCountItemsByDate(date)


    def getCountItemsNotExecutedByDate(self, date):
        return self.items.getCountItemsNotExecutedByDate(date)


    def getMaxDateToItems(self):
        return self.items.getMaxDateToItems()


    def getAliquoticity(self):
        return self.aliquoticity


    def getNote(self):
        return self.note


    def setNote(self, note):
        self.note = note


    def getSmnnUUID(self):
        return self.smnnUUID


    def setSmnnUUID(self, smnnUUID):
        self.smnnUUID = smnnUUID


    def getLfFormId(self):
        return self.lfFormId


    def setLfFormId(self, lfFormId):
        self.lfFormId = lfFormId


    def deleteItemsByDate(self, date):
        self.items.deleteItemsByDate(date)


    def loadItems(self, alreadyLoaded=None):
        self.items = self.getItems(alreadyLoaded)


    def getItems(self, alreadyLoaded=None):
        if not self.id:
            return None

        alreadyLoaded = alreadyLoaded or []

        where = [CActionExecutionPlanItem.masterId == self.id]
        if alreadyLoaded:
            where.append(
                CActionExecutionPlanItem.id.notInlist([i.id for i in alreadyLoaded if i and i.id])
            )

        query = CQuery(
            CActionExecutionPlanItem,
            CActionExecutionPlanItem.tableName,
            where=where,
            order=[CActionExecutionPlanItem.date.fullName,
                   CActionExecutionPlanItem.idx.fullName]
        )

        loadedItems = query.getList()
        items = loadedItems + alreadyLoaded
        items.sort(key=lambda epi: epi.idx)
        result = Items(items)
        # bind items objects with self
        for r in result:
            r.executionPlan = self

        self.__itemsInitialized__ = True

        return result


    @items.onValueSet
    def onItemsSet(self):
        self.__itemsInitialized__ = True
        items = self.items
        if not isinstance(items, Items):
            if isinstance(items, list):
                self.items = Items(items)
            else:
                raise ValueError("Expected list subclass instance, got %s" % str(type(items)))


    def defaultExecutionPlanCount(self):
        if self.type == CNomenclatureExecutionPlanType.type:
            return executionPlanType(self).defaultExecutionPlanCountNE()
        else:
            return executionPlanType(self).defaultExecutionPlanCount()


    def createItems(self, daysExecutionPlan=[]):
        if self.items:
            return
        self.daysExecutionPlan = daysExecutionPlan
        self.items = executionPlanType(self) \
            .createItems(
                self.begDate,
                self.begTime,
                self.duration,
                self.periodicity,
                self.aliquoticity,
                self.quantity,
                daysExecutionPlan=self.daysExecutionPlan
        )
        return self.items


    def createNewDateTimeItem(self, date, time):
        return executionPlanType(self).addNewDateTimeItem(date, time)


    def addNewDateTimeItem(self, date, time):
        item = self.createNewDateTimeItem(date, time)
        item.idx = len(self.items)
        self.items.append(item)
        return item


    def addItem(self, item):
        item.idx = len(self.items)
        self.items.append(item)


    def updateQuantity(self):
        quantity = 0
        datePrev = None
        for item in self.items:
            date = item.date
            aliquoticity = self.getCountItemsByDate(date)
            if item.action:
                item.action._record.setValue('aliquoticity', QVariant(aliquoticity))
            if date != datePrev:
                datePrev = date
                quantity += aliquoticity
        maxDate = self.getMaxDateToItems()
        self.quantity = quantity
        for row, item in enumerate(self.items):
            if item.action:
                if row > 0:
                    quantity -= 1
                duration = max(item.date.daysTo(maxDate) + 1, 1)
                item.action._record.setValue('quantity', QVariant(quantity if quantity > 0 else 0))
                item.action._record.setValue('duration', QVariant(duration if duration > 0 else 1))


    def setScheduleWeekendDays(self, value):
        self.scheduleWeekendDays = value


    def makeCopy(self, new=False):
        result = CDocumentModel.makeCopy(self, new=new)
        items = self.items or []
        copiedItems = []
        for item in items:
            copiedItems.append(item.makeCopy(new=new))
        result.items = copiedItems
        return result


    def mergeIntoOrigin(self):
        CDocumentModel.mergeIntoOrigin(self)
        origin = self.__origin__

        items = self.items or []
        for item in items:
            if item.__origin__:
                item.mergeIntoOrigin()

        origin.items = items


class CActionExecutionPlanItem(CModel):
    tableName = 'ActionExecutionPlan_Item'

    masterId = CRefAttribute(name='master_id')
    actionId = CRefAttribute(name='action_id')
    idx = CIntAttribute()
    aliquoticityIdx = CIntAttribute()
    date = CDateAttribute()
    time = CTimeAttribute()
    executedDatetime = CDateTimeAttribute()
    executionPlan = CRelationship(CActionExecutionPlan, 'masterId')
    action = CRelationship('CActionBLModel', 'actionId')
    nomenclature = CRelationship(
        'CActionExecutionPlanItemNomenclature',
        'id',
        'actionExecutionPlanItemId'
    )
    groupId = CRefAttribute(name='group_id')
    isDirty = False


    @classmethod
    def copyFrom(cls, item, new=False):
        newItem = cls._copyFrom(item, new=new)
        newItem.executionPlan = item.executionPlan
        newItem.action = item.action
        newItem.nomenclature = item.nomenclature.makeCopy(new=new) if item.nomenclature else None
        if newItem.nomenclature:
            newItem.nomenclature.actionExecutionPlanItem = newItem
        return newItem


    def getDateTime(self):
        return QDateTime(self.date, self.time)


    def makeCopy(self, new=False):
        result = CModel.makeCopy(self, new=new)
        result.executionPlan = self.executionPlan
        result.action = self.action

        n = self.nomenclature.makeCopy(new=new) if self.nomenclature else None
        result.nomenclature = n

        return result


    def mergeIntoOrigin(self):
        CModel.mergeIntoOrigin(self)
        origin = self.__origin__
        origin.action = self.action

        if self.nomenclature:
            self.nomenclature.mergeIntoOrigin()
            originNomenclature = self.nomenclature.__origin__
        else:
            originNomenclature = None

        origin.nomenclature = originNomenclature


    def getIsDirty(self):
        return self.isDirty


    def setIsDirty(self, dirty=True):
        self.isDirty = dirty


class CActionExecutionPlanItemNomenclature(CModel):
    tableName = 'ActionExecutionPlan_Item_Nomenclature'

    actionExecutionPlanItemId = CRefAttribute(name='actionExecutionPlan_item_id')
    nomenclatureId = CRefAttribute(name='nomenclature_id')
    dosage = CDoubleAttribute()
    actionExecutionPlanItem = CRelationship(CActionExecutionPlanItem, 'actionExecutionPlanItemId')


    @classmethod
    def copyFrom(cls, item, new=False):
        newItem = cls._copyFrom(item, new=new)
        newItem.actionExecutionPlanItem = item.actionExecutionPlanItem
        return newItem
