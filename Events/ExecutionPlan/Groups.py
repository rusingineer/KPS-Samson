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

from PyQt4.QtCore import QDate

from Events.ActionStatus import CActionStatus

from library.Utils import forceDate, forceDateTime, forceInt, toVariant

from Events.ExecutionPlan.ExecutionPlanType import executionPlanType


_emptyExecutionPlan = object()


class CActionExecutionPlanGroup(object):
    def __init__(self, executionPlan=None):
        self._executionPlan = executionPlan
        self._requireEP = False
        self._items = []
        self._copiedFrom = None


    def addDaysToEP(self, daysCount, quantityAdd=0, skipAfterLastDayCourse=0, isLastDayCourse=False):
        ept = executionPlanType(self._executionPlan)
        return ept.addDaysToEP(daysCount, quantityAdd=quantityAdd, skipAfterLastDayCourse=skipAfterLastDayCourse, isLastDayCourse=isLastDayCourse)


    def hasSavedItems(self):
        for item in self._executionPlan.items:
            if item.id:
                return True
        return False


    def begDate(self):
        return self._executionPlan.begDate


    def begTime(self):
        return self._executionPlan.begTime


    def planEndDate(self):
        if self._executionPlan.duration:
            return self._executionPlan.begDate.addDays((self._executionPlan.duration or 1) - 1)
        else:
            return self._executionPlan.begDate.addDays(len(self._executionPlan.items))


    def setBegDate(self, begDate):
        self._executionPlan.begDate = begDate


    def setBegTime(self, begTime):
        self._executionPlan.begTime = begTime


    def quantity(self):
        return self._executionPlan.quantity


    def duration(self):
        return self._executionPlan.duration


    def aliquoticity(self):
        return self._executionPlan.aliquoticity


    def periodicity(self):
        return self._executionPlan.periodicity


    def note(self):
        return self._executionPlan.note


    def getSmnnUUID(self):
        return self._executionPlan.smnnUUID


    def getLfFormId(self):
        return self._executionPlan.lfFormId


    def scheduleWeekendDays(self):
        return self._executionPlan.scheduleWeekendDays


    def setQuantity(self, value):
        self._executionPlan.quantity = value


    def setDuration(self, value):
        self._executionPlan.duration = value


    def setAliquoticity(self, value):
        self._executionPlan.aliquoticity = value


    def setPeriodicity(self, value):
        self._executionPlan.periodicity = value


    def setNote(self, value):
        self._executionPlan.note = value


    def setScheduleWeekendDays(self, value):
        self._executionPlan.scheduleWeekendDays = value


    def getItemsByDate(self, date):
        return self._executionPlan.items.getItemsByDate(date)


    def getCountItemsByDate(self, date):
        return self._executionPlan.items.getCountItemsByDate(date)


    def getMaxItemDate(self):
        return max([i.date for i in self._executionPlan.items])


    def existsDoneAfterDate(self, date):
        items = sorted(list(self._executionPlan.items), key=lambda x: x.date)
        for item in items:
            if item.date >= date and item.executedDatetime:
                return True
        return False


    def existsDoneActionAfterDate(self, date):
        items = sorted(list(self._executionPlan.items), key=lambda x: x.date)
        for item in items:
            if item.date > date and (item.action or item.executedDatetime):
                return True
        return False


    def existsDoneActionItemExecToDate(self, date):
        items = sorted(list(self._executionPlan.items), key=lambda x: x.date)
        for item in items:
            if item.date == date and (item.action or item.executedDatetime):
                return True
        return False


    def setItemsByDate(self, date, items):
        self._executionPlan.setItemsByDate(date, items)


    def setItemsByLastDate(self, date, items):
        self._executionPlan.setItemsByLastDate(date, items)


    def setDosageInExists(self, dosage):
        self._executionPlan.setDosageInExists(dosage)

    
    def setDosageToDateFirstItemInExists(self, dosage, date):
        self._executionPlan.setDosageToDateFirstItemInExists(dosage, date)
    
    
    def setDosageToProcentInExists(self, procent, change):
        self._executionPlan.setDosageToProcentInExists(procent, change)


    def setIsDirtyInExists(self, value):
        self._executionPlan.setIsDirtyInExists(value)


    def setDosageToDateToProcentInExists(self, procent, change, date):
        self._executionPlan.setDosageToDateToProcentInExists(procent, change, date)


    def setIsDirtyInExists(self, value):
        self._executionPlan.setIsDirtyInExists(value)


    def setCalculationDosageInExists(self, calculationParam):
        self._executionPlan.setCalculationDosageInExists(calculationParam)


    def setCalculationDosageToDateInExists(self, calculationParam, date):
        self._executionPlan.setCalculationDosageToDateInExists(calculationParam, date)


    def setDosageNomenclatureInExists(self, dosage, nomenclatureId):
        self._executionPlan.setDosageNomenclatureInExists(dosage, nomenclatureId)


    def setDosageNomenclatureFromDate(self, dosage, nomenclatureId, date):
        self._executionPlan.setDosageNomenclatureFromDate(dosage, nomenclatureId, date)


    def deleteItemsByDate(self, date):
        self._executionPlan.deleteItemsByDate(date)


    def getItemsByDateTime(self, datetime):
        return self._executionPlan.items.getItemsByDateTime(datetime)


    def getExecutionPlan(self):
        return self._executionPlan


    def hasExecutedItems(self):
        for item in self._executionPlan.items:
            if item.executedDatetime:
                return True
        return False


    def hasNotExecutedItems(self):
        for item in self._executionPlan.items:
            if not item.executedDatetime:
                return True
        return False


    def groupDataNotChanged(self):
        if self._executionPlan and len(self._executionPlan.items) > 0 and self._executionPlan.items[0].executionPlan:
            dosageValuesList = []
    #        quantity = self._executionPlan.items[0].executionPlan.quantity
            duration = self._executionPlan.items[0].executionPlan.duration
            aliquoticity = self._executionPlan.items[0].executionPlan.aliquoticity
            periodicity = self._executionPlan.items[0].executionPlan.periodicity
            planItemsCount = len(self._executionPlan.items)
    #        if quantity <= 0:
    #            return False
            if periodicity == 0:
                if duration*aliquoticity != planItemsCount:
                    return False
            else:
                if (duration-(aliquoticity*periodicity))*aliquoticity != planItemsCount:
                    return False
            for item in self._executionPlan.items:
               if item.nomenclature and item.nomenclature.dosage not in dosageValuesList:
                   dosageValuesList.append(item.nomenclature.dosage)
            if len(dosageValuesList) > 1:
                return False
        return True

    def groupDataNotChangedEx(self):
        if self._executionPlan and len(self._executionPlan.items) > 0 and self._executionPlan.items[0].executionPlan:
            duration = self._executionPlan.items[0].executionPlan.duration
            aliquoticity = self._executionPlan.items[0].executionPlan.aliquoticity
            periodicity = self._executionPlan.items[0].executionPlan.periodicity
            planItemsCount = len(self._executionPlan.items)
            if periodicity == 0:
                if duration*aliquoticity != planItemsCount:
                    return False
            else:
                if (duration-(aliquoticity*periodicity))*aliquoticity != planItemsCount:
                    return False
        return True        


    def copy(self):
        copiedEp = self._executionPlan.makeCopy() if self._executionPlan else None
        result = CActionExecutionPlanGroup(copiedEp)
        result._requireEP = self._requireEP
        result._items = self._items
        result._copiedFrom = self
        return result

    def mergeIntoOrigin(self):
        assert self._copiedFrom
        self._executionPlan.mergeIntoOrigin()

    @property
    def requireEP(self):
        return self._requireEP

    @property
    def nomenclatureId(self):
        return self._getItemNomenclatureId(self._items[0])

    @property
    def actionTypeId(self):
        return self._items[0].action.getType().id

    @property
    def orgStructureId(self):
        return self._items[0].action.getOrgStructureId()

    def setOrgStructureId(self, value):
        return self._items[0].action.setOrgStructureId(value)

    def lastOrgStructureId(self):
        items = self._items
        cnt = len(items)-1
        for row, item in enumerate(items):
            if item.action.executionPlanManager.hasItemsToDo():
                return item.action.getOrgStructureId()
            elif row == cnt:
                return item.action.getOrgStructureId()
        return None

    def setLastOrgStructureId(self, value):
        row = -1
        items = self._items
        for i, item in enumerate(items):
            if item.action.executionPlanManager.hasItemsToDo():
                row = i
                break
        if row >= 0 and row < len(self._items):
            return self._items[row].action.setOrgStructureId(value)
        return None

    @property
    def smnnUUID(self):
        return self._getItemSmnnUUID(self._items[0])

    @property
    def smnnGrlsLfId(self):
        return self._getItemSmnnGrlsLfId(self._items[0])

    def _getItemNomenclatureId(self, item):
        return item.action.findNomenclaturePropertyValue()

    def _getItemSmnnUUID(self, item):
        return item.action.getSmnnUUIDPropertyValue()

    def _getItemSmnnGrlsLfId(self, item):
        return item.action.getSmnnGrlsLfPropertyValue()

    @property
    def items(self):
        return self._items

    def addItem(self, item):
        if self._executionPlan is _emptyExecutionPlan:
            return False

        if not self._executionPlan:
            self._executionPlan = item.action.executionPlanManager.executionPlan or _emptyExecutionPlan
            self._requireEP = item.action.executionPlanManager.initialized
            self._items.append(item)
            return True

        if not self._requireEP:
            return False

        if not item.action.executionPlanManager.executionPlan:
            return False

        if item.action.executionPlanManager.executionPlan.id:
            if item.action.executionPlanManager.executionPlan.id != self._executionPlan.id:
                return False
        else:
            if item.action.executionPlanManager.executionPlan is not self._executionPlan:
                return False

        self._items.append(item)

        if item.action.getId():
            self._sortLoadedItems()

        return True

    def removeItem(self, item):
        self._items.remove(item)

    def inMonth(self, date):
        lower = QDate(date.year(), date.month(), 1)
        higher = QDate(date.year(), date.month(), date.daysInMonth())
        return self.inPeriod(lower, higher)

    def inPeriod(self, lower, higher):
        return (
            (not lower or lower <= self._executionPlan.begDate)
            and
            (not higher or self._executionPlan.begDate <= higher)
        )

    def _sortLoadedItems(self):
        # Этот метод вызыватся когда мы пересортируем загруженные из БД записи.
        # То есть должен быть маппинг id действия с расписанием выполнения
        orders = {}
        for epi in self._executionPlan.items:
            orders[epi.actionId] = epi.idx

        self._items.sort(key=lambda item: orders[item.action.getId()])

    def checkOnlyActual(self, onlyActual):
        if onlyActual:
            if len(self._executionPlan.items) != len(self._items):
                return False

            return not all([forceInt(i.record.value('status')) == CActionStatus.finished for i in self._items])

        return True

    @classmethod
    def makeFrom(cls, obj):
        if isinstance(obj, cls):
            return obj
        return obj.epGroup
    
    
class CExecutionPlanProxyModelGroup(object):
    def __init__(self, model):
        self._model = model
        self._epGroup = CActionExecutionPlanGroup()
        self._reversedItems = None
        self._mapItem2Row = {}
        self._mapRow2Item = {}
        self._mapProxyRow2ModelRow = {}
        self._expanded = False
        self._headModelRow = None
        self._actionTypeId = None
        self.idx = None
        self._copiedFrom = None
        self._isDirty = False

    def addDaysToEP(self, daysCount, quantityAdd=0, skipAfterLastDayCourse=0, isLastDayCourse=False):
        return self._epGroup.addDaysToEP(daysCount, quantityAdd=quantityAdd, skipAfterLastDayCourse=skipAfterLastDayCourse, isLastDayCourse=isLastDayCourse)

    def getSortValue(self, key):
        flatCode = self.items[-1].action.actionType().flatCode
        if key == 'idx':
            return forceInt(self.items[-1].record.value('idx'))
        elif key == 'begDate' or key == 'endDate':
            return forceDateTime(self.items[-1].record.value(key))
        elif key == "alfalab":
            return (forceDate(self.items[-1].record.value('directionDate')),
                    self.items[-1].action[u'Группа забора'] if flatCode == 'referralLisLab' else flatCode,
                    self.items[-1].action.getPrescriptionId() or flatCode == 'referralLisLab' and self.items[-1].action.getId() or 99999999999,
                    0 if flatCode == 'referralLisLab' else 1)
        return None

    def bindModel(self, model):
        self._model = model

    def hasSavedItems(self):
        return self._epGroup.hasSavedItems()

    def isDirty(self):
        return self._isDirty


    def setIsDirty(self, dirty=True):
        self._isDirty = dirty


    def begDate(self):
        return self._epGroup.begDate()

    def begTime(self):
        return self._epGroup.begTime()


    def directionDate(self):
        return self.headItem.action.getDirectionDate()

    def getActionTypeGroupId(self):
        return self.headItem.action.getActionTypeGroupId()

    def setDirectionDate(self, directionDate):
        return self.headItem.action.setDirectionDate(directionDate)

    def planEndDate(self):
        return self._epGroup.planEndDate()

    def setBegDate(self, begDate):
        self._epGroup.setBegDate(begDate)
        if len(self._mapItem2Row) != 1:
            return
        action = self.headItem.action
        action.setBegDate(begDate)

    def setBegTime(self, begTime):
        self._epGroup.setBegTime(begTime)
        if len(self._mapItem2Row) != 1:
            return
        action = self.headItem.action
        action.setBegTime(begTime)


    def setEndDate(self, endDate):
        if len(self._mapItem2Row) != 1:
            return
        action = self.headItem.action
        action.setEndDate(endDate)


    def setPlanEndDate(self, planEndDate):
        if len(self._mapItem2Row) != 1:
            return
        action = self.headItem.action
        action.setPlannedEndDate(planEndDate)


    def quantity(self):
        return self._epGroup.quantity()


    def duration(self):
        return self._epGroup.duration()


    def aliquoticity(self):
        return self._epGroup.aliquoticity()


    def periodicity(self):
        return self._epGroup.periodicity()

    def note(self):
        return self._epGroup.note()

    def getOrgStructureId(self):
        return self._epGroup.orgStructureId


    def getLastOrgStructureId(self):
        return self._epGroup.lastOrgStructureId()


    def updateSpecifiedName(self):
        if len(self._mapItem2Row) != 1:
            return
        action = self.headItem.action
        if action:
            action.updateSpecifiedName()

    def setDuration(self, value, updateExecutionPlan=True):
        if len(self._mapItem2Row) != 1:
            return

        action = self.headItem.action
        action.setDuration(value)

        if not self._epGroup._executionPlan.__origin__ and updateExecutionPlan:
            action.updateExecutionPlanByRecord()
            self._epGroup._executionPlan = action.getExecutionPlan()
        else:
            self._epGroup._executionPlan.duration = value
            if updateExecutionPlan:
                firstCurrentItemNeedToUpdate = self._epGroup._executionPlan.items.updateByEP(
                    self._epGroup._executionPlan
                )
                if firstCurrentItemNeedToUpdate:
                    action.executionPlanManager.setExecutionPlan(self._epGroup.getExecutionPlan(), force=True)
                    action.executionPlanManager.setCurrentItemIndex(0)
                    action.executionPlanManager._bindCurrentItemWithAction()


    def recalculateEP(self):
        if len(self._mapItem2Row) != 1:
            return
        action = self.headItem.action
        action.updateExecutionPlanByRecord()
        self._epGroup._executionPlan = action.getExecutionPlan()


    def setQuantity(self, value, updateExecutionPlan=True):
        if len(self._mapItem2Row) != 1:
            return
        action = self.headItem.action
        action.setQuantity(value)
        if not self._epGroup._executionPlan.__origin__ and updateExecutionPlan:
            action.updateExecutionPlanByRecord()
            self._epGroup._executionPlan = action.getExecutionPlan()
        else:
            self._epGroup._executionPlan.quantity = value
            if updateExecutionPlan:
                firstCurrentItemNeedToUpdate = self._epGroup._executionPlan.items.updateByEP(self._epGroup._executionPlan)
                if firstCurrentItemNeedToUpdate:
                    action.executionPlanManager.setExecutionPlan(self._epGroup.getExecutionPlan(), force=True)
                    action.executionPlanManager.setCurrentItemIndex(0)
                    action.executionPlanManager._bindCurrentItemWithAction()

    def setAliquoticity(self, value, updateExecutionPlan=True):
        if len(self._mapItem2Row) != 1:
            return
        action = self.headItem.action
        action.setAliquoticity(value)
        if not self._epGroup._executionPlan.__origin__ and updateExecutionPlan:
            action.updateExecutionPlanByRecord()
            self._epGroup._executionPlan = action.getExecutionPlan()
        else:
            self._epGroup._executionPlan.aliquoticity = value
            if updateExecutionPlan:
                firstCurrentItemNeedToUpdate = self._epGroup._executionPlan.items.updateByEP(
                    self._epGroup._executionPlan
                )
                if firstCurrentItemNeedToUpdate:
                    action.executionPlanManager.setExecutionPlan(self._epGroup.getExecutionPlan(), force=True)
                    action.executionPlanManager.setCurrentItemIndex(0)
                    action.executionPlanManager._bindCurrentItemWithAction()


    def setPeriodicity(self, value, updateExecutionPlan=True):
        if len(self._mapItem2Row) != 1:
            return
        action = self.headItem.action
        action.setPeriodicity(value)
        if not self._epGroup._executionPlan.__origin__ and updateExecutionPlan:
            action.updateExecutionPlanByRecord()
            self._epGroup._executionPlan = action.getExecutionPlan()
        else:
            self._epGroup._executionPlan.periodicity = value
            if updateExecutionPlan:
                firstCurrentItemNeedToUpdate = self._epGroup._executionPlan.items.updateByEP(
                    self._epGroup._executionPlan
                )
                if firstCurrentItemNeedToUpdate:
                    action.executionPlanManager.setExecutionPlan(self._epGroup.getExecutionPlan(), force=True)
                    action.executionPlanManager.setCurrentItemIndex(0)
                    action.executionPlanManager._bindCurrentItemWithAction()


    def setNote(self, value, updateExecutionPlan=False):
        if len(self._mapItem2Row) != 1:
            return
        action = self.headItem.action
        action.setNote(value)
        if not self._epGroup._executionPlan.__origin__ and updateExecutionPlan:
            action.updateExecutionPlanByRecord()
            self._epGroup._executionPlan = action.getExecutionPlan()
        else:
            self._epGroup._executionPlan.setNote(value)


    def setLastOrgStructureId(self, value):
        self._epGroup.setLastOrgStructureId(value)


    def setOrgStructureId(self, value):
        if len(self._mapItem2Row) != 1:
            return
        action = self.headItem.action
        action.setOrgStructureId(value)


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
    
    
    def getItemsByDate(self, date):
        return self._epGroup.getItemsByDate(date)

    def getMaxItemDate(self):
        return self._epGroup.getMaxItemDate()

    def existsDoneAfterDate(self, date):
        return self._epGroup.existsDoneAfterDate(date)

    def existsDoneActionAfterDate(self, date):
        return self._epGroup.existsDoneActionAfterDate(date)

    def existsDoneActionItemExecToDate(self, date):
        return self._epGroup.existsDoneActionItemExecToDate(date)

    def setItemsByDate(self, date, items):
        self._epGroup.setItemsByDate(date, items)
    
    def setDosageToDateToProcentInExists(self, procent, change, date):
        self._epGroup.setDosageToDateToProcentInExists(procent, change, date)
        
    def setItemsByLastDate(self, date, items):
        self._epGroup.setItemsByLastDate(date, items)

    def setDosageInExists(self, dosage):
        self._epGroup.setDosageInExists(dosage)

    def setIsDirtyInExists(self, value):
        self._epGroup.setIsDirtyInExists(value)

    def setCalculationDosageInExists(self, calculationParam):
        self._epGroup.setCalculationDosageInExists(calculationParam)

    def setDosageNomenclatureInExists(self, dosage, nomenclatureId):
        self._epGroup.setDosageNomenclatureInExists(dosage, nomenclatureId)

    def setNomenclatureInExists(self, nomenclatureId):
        self._epGroup.setNomenclatureInExists(nomenclatureId)

    def setDosageNomenclatureFromDate(self, dosage, nomenclatureId, date):
        self._epGroup.setDosageNomenclatureFromDate(dosage, nomenclatureId, date)

    def deleteItemsByDate(self, date):
        self._epGroup.deleteItemsByDate(date)

    def getItemsByDateTime(self, datetime):
        return self._epGroup.getItemsByDateTime(datetime)

    def hasExecutedItems(self):
        return self._epGroup.hasExecutedItems()

    def hasNotExecutedItems(self):
        return self._epGroup.hasNotExecutedItems()

    def groupDataNotChanged(self):
        return self._epGroup.groupDataNotChanged()

    def groupDataNotChangedEx(self):
        return self._epGroup.groupDataNotChangedEx()        

    def prepareToSave(self):
        self.mergeIntoOrigin()

    def copy(self):
        result = CExecutionPlanProxyModelGroup(self._model)
        result._copiedFrom = self
        result._epGroup = self._epGroup.copy()
        result._reversedItems = self._reversedItems
        result._mapItem2Row = self._mapItem2Row
        result._mapRow2Item = self._mapRow2Item
        result._mapProxyRow2ModelRow = self._mapProxyRow2ModelRow
        result._expanded = self._expanded
        result._headModelRow = self._headModelRow
        result._actionTypeId = self._actionTypeId
        return result

    def mergeIntoOrigin(self):
        assert self._copiedFrom

        currentIndex = self.headItem.action.executionPlanManager.getCurrentItemIndex()

        self._epGroup.mergeIntoOrigin()
        self._copiedFrom._mapItem2Row = self._mapItem2Row
        self._copiedFrom._mapRow2Item = self._mapRow2Item
        self._copiedFrom._mapProxyRow2ModelRow = self._mapProxyRow2ModelRow
        self._copiedFrom._expanded = self._expanded
        self._copiedFrom._headModelRow = self._headModelRow

        self.headItem.action.executionPlanManager.setExecutionPlan(self._epGroup.getExecutionPlan(), force=True)
        if currentIndex:
            self.headItem.action.executionPlanManager.setCurrentItemIndex(currentIndex)

    def checkOnlyActual(self, onlyActual):
        return self._epGroup.checkOnlyActual(onlyActual)

    @property
    def epGroup(self):
        return self._epGroup

    @property
    def model(self):
        return self._model

    @property
    def items(self):
        items = self._epGroup.items or []
        if self.expanded:
            if self._reversedItems is None:
                self._reversedItems = items[::-1]

            return self._reversedItems

        return items

    @property
    def orderedItems(self):
        return self._epGroup.items

    @property
    def actionTypeId(self):
        return self._epGroup.actionTypeId

    @property
    def orgStructureId(self):
        return self._epGroup.orgStructureId

    @property
    def lastOrgStructureId(self):
        return self._epGroup.lastOrgStructureId

    @property
    def requireEP(self):
        return self._epGroup.requireEP

    @property
    def nomenclatureId(self):
        return self._epGroup.nomenclatureId

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
        return self._epGroup.items[0]

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
        return self._mapRow2Item[self._mapProxyRow2ModelRow[proxyRow]]

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
        return self.requireEP and self.itemsCount() > 1

    def mapRows(self, proxyRow, item):
        modelRow = self._mapItem2Row[item]
        self._mapProxyRow2ModelRow[proxyRow] = modelRow

    def inMonth(self, date):
        return self._epGroup.inMonth(date)

    def inPeriod(self, begDate, endDate):
        return self._epGroup.inPeriod(begDate, endDate)

    def itemsCount(self):
        return len(self._epGroup.items)

    def setExpanded(self, value):
        if self.requireEP:
            self._expanded = value
            self._headModelRow = None

    def addItem(self, modelRow, item):
        if not self._epGroup.addItem(item):
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
        self._epGroup.removeItem(item)
        del self._mapItem2Row[item]
        del self._mapRow2Item[modelRow]
        del self._mapProxyRow2ModelRow[proxyRow]
        self._prepareOrderView()

    def isGrouped(self):
        return hasattr(self, 'groupingItem') and self.groupingItem and self.currentItem 
    
    def isGroupedAndSaved(self):
        return self.currentItem and forceInt(self.currentItem._record.value('id')) and forceInt(self.currentItem._record.value('group_id'))
    
    @property
    def proxyRows(self):
        return self._mapProxyRow2ModelRow.keys()
    
    
    @property
    def groupingItem(self):
        headRow = 0 if self.expanded else -1
        return self.items[headRow].action.executionPlanManager.groupingItem
    
    @property
    def groupingInfo(self):
        headRow = 0 if self.expanded else -1
        return self.items[headRow].action.executionPlanManager.groupingInfo
    
    def appendGroupingInfo(self, value):
        headRow = 0 if self.expanded else -1
        self.items[headRow].action.executionPlanManager.groupingInfo.append(value)
    
    def removeGroupingInfo(self, value):
        headRow = 0 if self.expanded else -1
        self.items[headRow].action.executionPlanManager.groupingInfo.remove(value)
    
    def clearGroupingInfo(self):
        headRow = 0 if self.expanded else -1
        self.items[headRow].action.executionPlanManager.groupingInfo = []
    
    def setGroupingItem(self, value):
        headRow = 0 if self.expanded else -1
        self.items[headRow].action.executionPlanManager.groupingItem = value
    
    @property
    def currentItem(self):
        headRow = 0 if self.expanded else -1
        return self.items[headRow].action.executionPlanManager._currentItem

    def _prepareOrderView(self):
        self._headModelRow = None
        self._reversedItems = None

    def __contains__(self, item):
        return item in self._epGroup.items

    def __iter__(self):
        return iter(self.items)

    def __len__(self):
        return len(self._epGroup.items) if self._expanded else 1 if len(self._epGroup.items) else 0
