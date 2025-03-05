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

from collections import namedtuple

from .Errors import UnsupportedExecutionPlanType

# from library.Utils import pyDate, toVariant, forceDouble


_itemData = namedtuple('itemData', 'idx aliquoticityIdx execDate')
_itemDataNE = namedtuple('itemData', 'idx execDate')


def _calculateItemsData(begDate, duration, periodicity, aliquoticity, quantity, daysExecutionPlan=[]):
    result = []
    plannedEndDate = begDate.addDays(duration - 1)
    execDate = begDate
    idx = 0
    aliquoticityIdx = 0
    execAliquoticity = aliquoticity if aliquoticity > 0 else 1
    if daysExecutionPlan:
        for day in daysExecutionPlan:
            for _ in xrange(execAliquoticity):
                if quantity > 0:
                    result.append(_itemData(idx, aliquoticityIdx, day))
                    idx += 1
                    quantity -= 1
                else:
                    break
            aliquoticityIdx += 1
    elif duration > 0:
        while quantity > 0:
            if execDate <= plannedEndDate:
                for _ in xrange(execAliquoticity):
                    result.append(_itemData(idx, aliquoticityIdx, execDate))
                    idx += 1
                    quantity -= 1
                execDate = execDate.addDays(periodicity + 1)
                aliquoticityIdx += 1
            else:
                break
    elif duration == 0:
        while quantity > 0:
            for _ in xrange(execAliquoticity):
                result.append(_itemData(idx, aliquoticityIdx, execDate))
                idx += 1
                quantity -= 1
            execDate = execDate.addDays(periodicity + 1)
            aliquoticityIdx += 1
    return result


def _calculateItemsDataNE(begDate, duration, periodicity, aliquoticity):
    result = []
    plannedEndDate = begDate.addDays(duration - 1)
    execDate = begDate
    idx = 0
    while execDate <= plannedEndDate:
        for _ in xrange(aliquoticity):
            result.append(_itemDataNE(idx, execDate))
            idx += 1
        execDate = execDate.addDays(periodicity + 1)
    return result


class CExecutionPlanType(object):
    type = None

    def __init__(self, executionPlan):
        self._executionPlan = executionPlan


class CActionExecutionPlanType(CExecutionPlanType):
    type = 0

    def addNewDateTimeItem(self, date=None, time=None):
        from .ExecutionPlan import CActionExecutionPlanItem

        item = CActionExecutionPlanItem()
        item.date = date
        item.time = time
        item.executionPlan = self._executionPlan

        return item


    def createItems(self, begDate, begTime, duration, periodicity, aliquoticity, quantity, isNomenclatureExecution=False, daysExecutionPlan=[]):
        from .ExecutionPlan import CActionExecutionPlanItem
        if isNomenclatureExecution:
            return self.createItemsNE(begDate, begTime, duration, periodicity, aliquoticity, quantity, daysExecutionPlan)
        result = []
        execDate = begDate
        idx = 0
        aliquoticityIdx = 0
        execQuantity = quantity
        execAliquoticity = aliquoticity if aliquoticity > 0 else 1
        if daysExecutionPlan:
            for day in daysExecutionPlan:
                for _ in xrange(execAliquoticity):
                    if execQuantity > 0:
                        item = CActionExecutionPlanItem()
                        item.idx = idx
                        item.aliquoticityIdx = aliquoticityIdx
                        item.date = day
                        item.time = begTime if (idx == 0 and begTime) else None
                        item.executionPlan = self._executionPlan
                        result.append(item)
                        idx += 1
                        execQuantity -= 1
                    else:
                        break
                aliquoticityIdx += 1
        elif duration > 0:
            plannedEndDate = begDate.addDays(duration - 1)
            while execQuantity > 0:
                if execDate <= plannedEndDate:
                    for _ in xrange(execAliquoticity):
                        item = CActionExecutionPlanItem()
                        item.idx = idx
                        item.aliquoticityIdx = aliquoticityIdx
                        item.date = execDate
                        item.time = begTime if (idx == 0 and begTime) else None
                        item.executionPlan = self._executionPlan
                        result.append(item)
                        idx += 1
                        execQuantity -= 1
                    execDate = execDate.addDays(periodicity + 1)
                    aliquoticityIdx += 1
                else:
                    break
        elif duration == 0:
            while execQuantity > 0:
                for _ in xrange(execAliquoticity):
                    item = CActionExecutionPlanItem()
                    item.idx = idx
                    item.aliquoticityIdx = aliquoticityIdx
                    item.date = execDate
                    item.time = begTime if (idx == 0 and begTime) else None
                    item.executionPlan = self._executionPlan
                    result.append(item)
                    idx += 1
                    execQuantity -= 1
                execDate = execDate.addDays(periodicity + 1)
                aliquoticityIdx += 1
        return result


    def addDaysToEP(self, daysCount, isNomenclatureExecution=False, quantityAdd=0, skipAfterLastDayCourse=0, isLastDayCourse=False):
        from .ExecutionPlan import CActionExecutionPlanItem
        if isNomenclatureExecution:
            return self.addDaysToEPNE(daysCount, quantityAdd=quantityAdd, skipAfterLastDayCourse=skipAfterLastDayCourse, isLastDayCourse=isLastDayCourse)
        currentDuration = self._executionPlan.duration
        periodicity = self._executionPlan.periodicity
        aliquoticity = self._executionPlan.aliquoticity
        quantity = self._executionPlan.quantity
        newQuantity = quantity + quantityAdd
        begDate = self._executionPlan.begDate
        begTime = self._executionPlan.begTime
#        daysExecutionPlan = self._executionPlan.daysExecutionPlan
        if skipAfterLastDayCourse > 0:
            newDuration = currentDuration + daysCount + skipAfterLastDayCourse
        else:
            newDuration = currentDuration + daysCount
        plannedEndDate = begDate.addDays(newDuration - 1)
        #itemsData = _calculateItemsData(begDate, currentDuration, periodicity, aliquoticity, quantity, daysExecutionPlan)
        #idx, execDate = itemsData[-1].idx, itemsData[-1].execDate
        execDate = self._executionPlan.items.getMaxDateToItems()
        idx = self._executionPlan.items.getIdxToItems()
        lastDateCourse = execDate
        if skipAfterLastDayCourse > 0:
            execDate = execDate.addDays(skipAfterLastDayCourse)
        dates2items = {}
        newItems = []
        init = False
        aliquoticityIdx = 0
        aliquoticity = aliquoticity if aliquoticity > 0 else 1
        if quantityAdd:
            quantity = quantityAdd
        while quantity > 0:
            if execDate <= plannedEndDate:
                if init:
                    existsItems = self._executionPlan.items.getItemsByDate(execDate)
                    s = len(existsItems) if existsItems else 0
                    for _ in xrange(s, aliquoticity):
                        item = CActionExecutionPlanItem()
                        item.idx = idx
                        item.aliquoticityIdx = aliquoticityIdx
                        item.date = execDate
                        item.time = begTime if (idx == 0 and begTime) else None
                        item.executionPlan = self._executionPlan
                        idx += 1
                        dates2items.setdefault(execDate, []).append(item)
                        newItems.append(item)
                        quantity -= 1
                    aliquoticityIdx += 1
                    if existsItems:
                        for i in existsItems:
                            dates2items.setdefault(execDate, []).append(i)
                else:
                    init = True
                execDate = execDate.addDays(periodicity + 1)
            else:
                break
        self._executionPlan.duration = newDuration
        self._executionPlan.quantity = newQuantity
        if isLastDayCourse and lastDateCourse:
            newItems = []
            for date in sorted(dates2items.keys()):
                items = dates2items[date]
                newItems.extend(self._executionPlan.items.setItemsByLastDate(date, items))
        else:
            for date in sorted(dates2items.keys()):
                items = dates2items[date]
                self._executionPlan.items.setItemsByDate(date, items, new=True)
        return newItems


    def createItemsNE(self, begDate, begTime, duration, periodicity, aliquoticity, quantity, daysExecutionPlan=[]):
        from .ExecutionPlan import CActionExecutionPlanItem
        result = []
        plannedEndDate = begDate.addDays(duration - 1)
        execDate = begDate
        idx = 0
        aliquoticityIdx = 0
        execQuantity = quantity
        execAliquoticity = aliquoticity if aliquoticity > 0 else 1
        if daysExecutionPlan:
            for day in daysExecutionPlan:
                for _ in xrange(execAliquoticity):
                    if execQuantity > 0:
                        item = CActionExecutionPlanItem()
                        item.idx = idx
                        item.aliquoticityIdx = aliquoticityIdx
                        item.date = day
                        item.time = begTime if (idx == 0 and begTime) else None
                        item.executionPlan = self._executionPlan
                        result.append(item)
                        idx += 1
                        execQuantity -= 1
                    else:
                        break
                aliquoticityIdx += 1
        else:
            while execDate <= plannedEndDate:
                for _ in xrange(aliquoticity):
                    item = CActionExecutionPlanItem()
                    item.idx = idx
                    item.date = execDate
                    item.time = begTime if (idx == 0 and begTime) else None
                    item.executionPlan = self._executionPlan
                    result.append(item)
                    idx += 1

                execDate = execDate.addDays(periodicity + 1)
        return result


    def addDaysToEPNE(self, daysCount, quantityAdd=0, skipAfterLastDayCourse=0, isLastDayCourse=False):
        from .ExecutionPlan import CActionExecutionPlanItem

        currentDuration = self._executionPlan.duration
        periodicity = self._executionPlan.periodicity
        aliquoticity = self._executionPlan.aliquoticity
        begDate = self._executionPlan.begDate
        begTime = self._executionPlan.begTime
        if skipAfterLastDayCourse > 0:
            newDuration = currentDuration + daysCount + skipAfterLastDayCourse
        else:
            newDuration = currentDuration + daysCount
        plannedEndDate = begDate.addDays(newDuration - 1)
        quantity = self._executionPlan.quantity
        newQuantity = quantity + quantityAdd
#        daysExecutionPlan = self._executionPlan.daysExecutionPlan
##        itemsData = _calculateItemsDataNE(begDate, currentDuration, periodicity, aliquoticity)
#        itemsData = _calculateItemsData(begDate, currentDuration, periodicity, aliquoticity, quantity, daysExecutionPlan)
#        idx, execDate = itemsData[-1].idx, itemsData[-1].execDate
        execDate = self._executionPlan.items.getMaxDateToItems()
        idx = self._executionPlan.items.getIdxToItems()
        lastDateCourse = execDate
        if skipAfterLastDayCourse > 0:
            execDate = execDate.addDays(skipAfterLastDayCourse)
        dates2items = {}
        newItems = []
        init = False
        while execDate <= plannedEndDate:
            if init:
                existsItems = self._executionPlan.items.getItemsByDate(execDate)
                s = len(existsItems) if existsItems else 0
                for _ in xrange(s, aliquoticity):
                    item = CActionExecutionPlanItem()
                    item.idx = idx
                    item.date = execDate
                    item.time = begTime if (idx == 0 and begTime) else None
                    item.executionPlan = self._executionPlan
                    idx += 1
                    dates2items.setdefault(execDate, []).append(item)
                    newItems.append(item)

                if existsItems:
                    for i in existsItems:
                        dates2items.setdefault(execDate, []).append(i)
            else:
                init = True
            execDate = execDate.addDays(periodicity + 1)
        self._executionPlan.duration = newDuration
        self._executionPlan.quantity = newQuantity
        if isLastDayCourse and lastDateCourse:
            newItems = []
            for date in sorted(dates2items.keys()):
                items = dates2items[date]
                newItems.extend(self._executionPlan.items.setItemsByLastDate(date, items))
        else:
            for date in sorted(dates2items.keys()):
                items = dates2items[date]
                self._executionPlan.items.setItemsByDate(date, items, new=True)
        return newItems


    def calculateItemsCount(self, begDate, duration, periodicity, aliquoticity, quantity, daysExecutionPlan=[]):
        itemsData = _calculateItemsData(begDate, duration, periodicity, aliquoticity, quantity, daysExecutionPlan)
        if itemsData:
            return itemsData[-1].idx
        return 0


    def bindItemWithAction(self, item, action):
        item.action = action
        item.actionId = action.id


    def defaultExecutionPlanCount(self):
        begDate = self._executionPlan.begDate
        duration = self._executionPlan.duration
        aliquoticity = self._executionPlan.aliquoticity
        quantity = self._executionPlan.quantity
        plannedEndDate = begDate.addDays(duration - 1)
        execDate = begDate
        c = 0
        if duration > 0:
            while quantity > 0:
                if execDate <= plannedEndDate:
                    for _ in xrange(aliquoticity):
                        execDate = execDate.addDays(1)
                        c += 1
                        quantity -= 1
                else:
                    break
        elif duration == 0:
            c = quantity
        return c


    def defaultExecutionPlanCountNE(self):
        begDate = self._executionPlan.begDate
        duration = self._executionPlan.duration
        aliquoticity = self._executionPlan.aliquoticity
        plannedEndDate = begDate.addDays(duration - 1)
        execDate = begDate
        c = 0
        while execDate <= plannedEndDate:
            for _ in xrange(aliquoticity):
                execDate = execDate.addDays(1)
                c += 1
        return c


class CNomenclatureExecutionPlanType(CActionExecutionPlanType):
    type = 1

    def addNewDateTimeItem(self):
        from .ExecutionPlan import CActionExecutionPlanItemNomenclature

        actionItem = CActionExecutionPlanType.addNewDateTimeItem(self)
        item = CActionExecutionPlanItemNomenclature()
        item.actionExecutionPlanItem = actionItem
        actionItem.nomenclature = item
        return actionItem


    def addDaysToEP(self, daysCount, quantityAdd=0, skipAfterLastDayCourse=0, isLastDayCourse=False):
        from .ExecutionPlan import CActionExecutionPlanItemNomenclature

        items = CActionExecutionPlanType.addDaysToEP(self, daysCount, isNomenclatureExecution=True, quantityAdd=quantityAdd, skipAfterLastDayCourse=skipAfterLastDayCourse, isLastDayCourse=isLastDayCourse)
        for item in items:
            if item.nomenclature:
                ni = CActionExecutionPlanItemNomenclature()
                ni.dosage = item.nomenclature.dosage
                ni.nomenclatureId = item.nomenclature.nomenclatureId
                item.nomenclature = ni
                ni.actionExecutionPlanItem = item
        return items


    def createItems(self, begDate, begTime, duration, periodicity, aliquoticity, quantity, daysExecutionPlan=[]):
        from .ExecutionPlan import CActionExecutionPlanItemNomenclature

        result = []
        for actionItem in CActionExecutionPlanType.createItems(
                self,
                begDate,
                begTime,
                duration,
                periodicity,
                aliquoticity,
                quantity,
                isNomenclatureExecution=True,
                daysExecutionPlan=daysExecutionPlan):
            item = CActionExecutionPlanItemNomenclature()
            item.actionExecutionPlanItem = actionItem
            actionItem.nomenclature = item
            result.append(actionItem)

        return result


_executionPlanTypes = {
    CActionExecutionPlanType.type: CActionExecutionPlanType,
    CNomenclatureExecutionPlanType.type: CNomenclatureExecutionPlanType
}


def executionPlanType(executionPlan):
    if executionPlan.type not in _executionPlanTypes:
        raise UnsupportedExecutionPlanType()
    return _executionPlanTypes[executionPlan.type](executionPlan)
