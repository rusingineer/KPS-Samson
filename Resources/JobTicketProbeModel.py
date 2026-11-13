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

import functools
import json

import requests
from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QEvent, QLocale, QVariant, SIGNAL

from library.crbcombobox import CRBComboBox, CRBModelDataCache
from library.DateEdit import CDateEdit
from library.PreferencesMixin import CPreferencesMixin
from library.TreeModel import CTreeModel, CTreeItem
from library.exception        import CException
from library.Utils            import (
                                        calcAgeTuple,
                                        forceBool,
                                        forceDate,
                                        forceDouble,
                                        forceInt,
                                        forceRef,
                                        forceString,
                                        getPref,
                                        setPref,
                                        formatShortName,
                                     )

from TissueJournal.Utils import getActualEquipmentId, getActualSpecimenTypeId
from RefBooks.Equipment.Protocol import CEquipmentProtocol


from Resources.BarCodeActionExecutingContext import CBarCodeActionExecutingContext


ITEM_CHECKED_COLUMN     = 0
ITEM_TEXT_VALUE_COLUMN  = 0
EQUIPMENT_ID_COLUMN     = 1
SPECIMEN_TYPE_ID_COLUMN = 2
ITEM_BACKGROUND_COLUMN  = 3
EXTERNAL_ID_COLUMN      = 4
ITEM_AMOUNT_COLUMN      = 5

class CJobTicketProbeBaseItem(CTreeItem):
    def __init__(self, parent, id, model, **kwargs):
        self._id                     = id
        self._model                  = model
        self._isChecked              = False
        self._externalId             = None
        self._equipmentId            = None
        self._specimenTypeId         = None
        self._externalIdIsByBarCode  = False

        self._allowedEquipIdList     = self.__getAllowedEquipIdList()
        self._canBeChecked           = kwargs.get('canBeChecked', False)
        self._editableExternalId     = kwargs.get('editableExternalId', False)
        self._editableEquipmentId    = kwargs.get('editableEquipmentId', False)
        self._editableSpecimenTypeId = kwargs.get('editableSpecimenTypeId', False)
        self._course                 = kwargs.get('course', 1)


        CTreeItem.__init__(self, parent, self._getValue())

    @property
    def externalIdIsByBarCode(self):
        return self._externalIdIsByBarCode

    @property
    def externalId(self):
        return self._externalId

    def setExternalIdIsByBarCode(self, value):
        self._externalIdIsByBarCode = value
        for children in self.items():
            children.setExternalIdIsByBarCode(value)


    def isActualCourseNumber(self, courseNumber):
        if not self.isCourseJobTicket:
            return True
        if type(self) is CJobTicketCourseItem:
            return self._course == courseNumber
        elif isinstance(self._parent, CJobTicketProbeBaseItem):
            return self._parent.isActualCourseNumber(courseNumber)
        return False

    @property
    def isCourseJobTicket(self):
        return self._model.isCourseJobTicket

    def getMaxCourseNumber(self):
        return self._model.getMaxCourseNumber()

    def getCurrentCourse(self):
        return self._model.getCurrentCourse()

    def __getAllowedEquipIdList(self):
        testId = getattr(self, 'testId', lambda: None)()
        if testId:
            return QtGui.qApp.db.getIdList('rbEquipment_Test', 'equipment_id', 'test_id = %d' % testId)
        return []

    def _getValue(self):
        assert False


    def testId(self):
        return None


    def columnCount(self):
        return 1


    def model(self):
        return self._model


    def id(self):
        return self._id


    def loadChildren(self):
        return []


    def background(self, column):
        return QVariant()


    def font(self, column):
        return QVariant()


    def amount(self, column):
        return QVariant()


    def checked(self, column):
        if self.canBeChecked(column):
            return QVariant(self._isChecked)
        return QVariant()


    def canBeChecked(self, column):
        if column in self.model().checkableColumnList():
            return self._canBeChecked
        return False


    def isEditable(self, column):
        return self.editableExternalId(column) or self.editableEquipmentId(column) or self.editableSpecimenTypeId(column)


    def editableExternalId(self, column):
        if column == EXTERNAL_ID_COLUMN:
            return self._editableExternalId
        return False


    def editableEquipmentId(self, column):
        if column == EQUIPMENT_ID_COLUMN:
            return self._editableEquipmentId
        return False


    def editableSpecimenTypeId(self, column):
        if column == SPECIMEN_TYPE_ID_COLUMN:
            return self._editableSpecimenTypeId
        return False


    def flags(self, index=None):
        flags = CTreeItem.flags(self)
        if not self.saved():
            if index and index.isValid():
                column = index.column()
                if self.canBeChecked(column):
                    flags |= Qt.ItemIsUserCheckable

                if (self.editableExternalId(column)
                        or self.editableEquipmentId(column)
                        or self.editableSpecimenTypeId(column)):

                    flags |= Qt.ItemIsEditable
            if not self.isActualCourseNumber(self.getCurrentCourse()):
                flags &= ~Qt.ItemIsEnabled
        else:
            flags &= ~Qt.ItemIsEnabled
        return flags

    def hasEditableFlag(self):
        flags = self.flags()
        return (flags & Qt.ItemIsEnabled) == Qt.ItemIsEnabled

    def setChecked(self, value, recurse = True):
        if not self.saved():
            self._isChecked = value
            if self._items and recurse:
                for item in self._items:
                    item.setChecked(value)
            self.checkIsChecked()


    def hasExternalId(self):
        return bool(self._externalId)


    def canSetExternalId(self):
        result = self.editableExternalId(EXTERNAL_ID_COLUMN) and not self.saved()
        return result


    def isAssigned(self):
        return False


    def isAssignable(self):
        return False


    def setExternalId(self, value, depth=False, setSame=False, recurse=True):
        if not self.saved():
            if self.canSetExternalId():
                if depth:
                    if forceBool(self.checked(ITEM_CHECKED_COLUMN)):
                        self._externalId = value
                else:
                    if setSame:
                        self.setSameExternalId(value)
                    self._externalId = value
            if self._items and recurse:
                for item in self._items:
                    CJobTicketProbeBaseItem.setExternalId(item, value, depth=depth)


    def setEquipmentId(self, equipmentId, recurse = True):
        if not self.saved():
            if self._allowedEquipIdList:
                self._equipmentId = equipmentId if equipmentId in self._allowedEquipIdList else None
                self._specimenTypeId = getActualSpecimenTypeId(self.testId(), self._equipmentId)
            if self._items and recurse:
                for item in self._items:
                    item.setEquipmentId(equipmentId)



    def specimenTypeId(self):
        return self._specimenTypeId

    def setSpecimenTypeId(self, specimenTypeId):
        if not self.saved():
            self._specimenTypeId = specimenTypeId


    def setSameChecked(self, value):
        pass


    def setSameExternalId(self, value):
        pass


    def absoluteItemList(self, lst):
        lst.append(self)
        if self._items:
            for item in self._items:
                item.absoluteItemList(lst)


    def resetItems(self):
        self._items = None


    def data(self, column):
        if column == EXTERNAL_ID_COLUMN:
            if self._externalId:
                return QVariant(self._externalId)
            return QVariant()
        elif column == ITEM_AMOUNT_COLUMN:
            return self.amount(column)
        elif column == EQUIPMENT_ID_COLUMN:
            data = CRBModelDataCache.getData('rbEquipment', addNone=True)
            res = data.getStringById(self._equipmentId, CRBComboBox.showCodeAndName)
            if len(res)>1 and res[0] == '0' and res[1] == ' ':
                res = ''
            return res
        elif column == SPECIMEN_TYPE_ID_COLUMN:
            data = CRBModelDataCache.getData('rbSpecimenType', addNone=True)
            res = data.getStringById(self._specimenTypeId, CRBComboBox.showCodeAndName)
            if len(res)>1 and res[0] == '0' and res[1] == ' ':
                res = ''
            return res
        else:
            return CTreeItem.data(self, column)


    def checkEquipmentId(self):
        equipId = []
        for item in self.items():
            if isinstance(equipId, list):
                equipId = item._equipmentId
            if equipId != item._equipmentId:
                equipId = None
        if not isinstance(equipId, list):
            self._equipmentId = equipId
        if self.parent():
            self.parent().checkEquipmentId()


    def checkExternalId(self):
        externalId = []
        for item in self.items():
            if isinstance(externalId, list):
                externalId = item._externalId
            if externalId != item._externalId:
                externalId = None
        if not isinstance(externalId, list):
            self._externalId = externalId
        if self.parent():
            self.parent().checkExternalId()

    def checkIsChecked(self):
        checked = []
        for item in self.items():
            if isinstance(checked, list):
                checked = item._isChecked
            if checked != item._isChecked:
                checked = False
        if not isinstance(checked, list):
            self._isChecked = checked
        if self.parent():
            self.parent().checkIsChecked()


    def setEditorData(self, column, editor, value):
        if column == EXTERNAL_ID_COLUMN:
            editor.setText(forceString(value))
        elif column in (EQUIPMENT_ID_COLUMN, SPECIMEN_TYPE_ID_COLUMN):
            editor.setValue(forceRef(value))


    def getEditorData(self, column, editor):
        if column == EXTERNAL_ID_COLUMN:
            for item in self.items():
                item.setExternalId(unicode(editor.text()))
            return unicode(editor.text())
        elif column in (EQUIPMENT_ID_COLUMN, SPECIMEN_TYPE_ID_COLUMN):
            for item in self.items():
                if column == EQUIPMENT_ID_COLUMN:
                    item.setEquipmentId(forceRef(editor.value()))
                elif column == SPECIMEN_TYPE_ID_COLUMN:
                    item.setSpecimenTypeId(forceRef(editor.value()))
            return editor.value()


    def createEditor(self, parent, column):
        editor = None
        if column == EXTERNAL_ID_COLUMN:
            editor = QtGui.QLineEdit(parent)
        elif column == EQUIPMENT_ID_COLUMN:
            editor = CRBComboBox(parent)
            editor.setTable('rbEquipment', addNone=True)
            if self._allowedEquipIdList:
                editor.setFilter(filter='id in (%s)'%','.join(str(x) for x in self._allowedEquipIdList))
        elif column == SPECIMEN_TYPE_ID_COLUMN:
            editor = CSpecimenTypeComboBox(parent)
            editor.setExternalFilter(self.testId(), self._equipmentId)
        return editor


    def saved(self):
        #return False
        res = False
        for item in self.items():
            if not item.saved():
                return False
            else:
                res = True
        return res


    def containerTypeId(self):
        return None


class CJobTicketProbeTestItem(CJobTicketProbeBaseItem):
    cacheValuesById  = {}
    cacheSavedValues = {}
    def __init__(self, parent, propertyType, model, eventId=None, actionId=None, course=1):
        self._propertyType   = propertyType
        self._isChecked      = False
        self._probeId        = None
        self._saved          = False
        CJobTicketProbeBaseItem.__init__(self, parent, propertyType.id, model,
                                         canBeChecked=True,
                                         editableExternalId=True,
                                         editableEquipmentId=True,
                                         editableSpecimenTypeId=True,
                                         course=course)
        self._saved = self._isItemSaved()
        if not self._saved:
            self._equipmentId    = getActualEquipmentId(self.testId(), self.model()._orgStructureId)
            self._specimenTypeId = getActualSpecimenTypeId(self.testId(), self._equipmentId)
            if self.isAssigned():
                self._isChecked = True


    def containerTypeId(self):
        return self.parent().containerTypeId()


    def _isItemSaved(self):
        if self.isCourseJobTicket:
            return self._isItemSavedInCourse()
        return self._isItemSavedNotInCourse()
    
    
    def tissueTypeId(self):
        return self.model().getTissueTypeIdForAction(self.parent().action().getId())

    def _isItemSavedNotInCourse(self):
        tissueTypeId = self.tissueTypeId()
        if self.model().hasSavedTakenTissue(tissueTypeId):
            takenTissueId = self.model().takenTissueId(tissueTypeId)
            return self.__checkItemSaved(takenTissueId)
        return False

    def _isItemSavedInCourse(self):
        model = self.model()
        tissueTypeId = self.tissueTypeId()
        if model.isCoursePassed(self._course) or (model.isLastCoursePart() and model.hasSavedTakenTissue(tissueTypeId)):
            takenTissueId = model.getTakenTissueIdByCourseNumber(self._course, tissueTypeId)
            if takenTissueId:
                return self.__checkItemSaved(takenTissueId)
        return False


    def __checkItemSaved(self, takenTissueId):
            testId = self.testId()
            savedValues = self.__isItemSaved(takenTissueId, testId)
            saved, probeId, externalId, equipmentId, specimenTypeId = savedValues
            if saved:
                self.setExternalId(externalId)
                self._probeId = probeId
                self._equipmentId = equipmentId
                self._specimenTypeId = specimenTypeId
            # self.setChecked(saved)
            self._isChecked = True
            return saved


    @classmethod
    def __isItemSaved(cls, takenTissueId, testId):
        savedValues = cls.cacheSavedValues.get( (takenTissueId, testId), None)
        if savedValues is None:
            db = QtGui.qApp.db
            tableProbe = db.table('Probe')
            cond = [tableProbe['test_id'].eq(testId), tableProbe['takenTissueJournal_id'].eq(takenTissueId)]
            record = db.getRecordEx(tableProbe, 'id, externalId,equipment_id,specimenType_id', cond)
            if record:
                probeId = forceRef(record.value('id'))
                externalId = forceString(record.value('externalId'))
                equipmentId = forceRef(record.value('equipment_id'))
                specimenTypeId = forceRef(record.value('specimenType_id'))
            else:
                probeId = externalId = equipmentId = specimenTypeId = None
            savedValues = bool(probeId), probeId, externalId, equipmentId, specimenTypeId
            cls.cacheSavedValues[(takenTissueId, testId)] = savedValues
        return savedValues


    def saved(self):
        return self._saved


    def probeId(self):
        return self._probeId


    def setSaved(self, value, probeId):
        self._saved = value
        self._probeId = probeId


    def getProperty(self):
        return self.getAction().getPropertyById(self.propertyType().id)


    def isAssigned(self):
        return self.getProperty().isAssigned()


    def isAssignable(self):
        if self.model().checkAssignable():
            return self.propertyType().isAssignable
        return False


    def getAction(self):
        return self.parent().action()


    def testId(self):
        return self._propertyType.testId


    def propertyType(self):
        return self._propertyType


    def editableSpecimenTypeId(self, column):
        result = CJobTicketProbeBaseItem.editableSpecimenTypeId(self, column)
        result = result and bool(self._equipmentId)
        return result


    def setEditorData(self, column, editor, value):
        if column == EXTERNAL_ID_COLUMN:
            editor.setText(forceString(value))
        elif column in (EQUIPMENT_ID_COLUMN, SPECIMEN_TYPE_ID_COLUMN):
            editor.setValue(forceRef(value))


    def getEditorData(self, column, editor):
        if column == EXTERNAL_ID_COLUMN:
            return unicode(editor.text())
        elif column in (EQUIPMENT_ID_COLUMN, SPECIMEN_TYPE_ID_COLUMN):
            return editor.value()


    def equipmentId(self):
        return self._equipmentId


    def _getValue(self):
        testId = self._propertyType.testId
        mapItemByTestId(testId, self)
        return self.__getValue(testId)


    def setSameChecked(self, value):
        sameItems = self.getSameItems()
        for item in sameItems:
            item.setChecked(value, setSame=False)


    def setSameExternalId(self, value):
        sameItems = self.getSameItems()
        for item in sameItems:
            item.setExternalId(value, setSame=False)


    def getSameItems(self):
        items = getItemsByTestId(self.testId())
        return [item for item in items if item._id != self._id]


    @classmethod
    def __getValue(cls, testId):
        value = cls.cacheValuesById.get(testId, None)
        if value is None:
            value = forceString(QtGui.qApp.db.translate('rbTest', 'id', testId, 'CONCAT_WS(\' | \', code, name)'))
            if not value:
                value = '_invalid_'
            cls.cacheValuesById[testId] = value
        return value


    @classmethod
    def reset(cls):
        cls.cacheValuesById.clear()
        cls.cacheSavedValues.clear()


class CJobTicketProbeActionItem(CJobTicketProbeBaseItem):
    def __init__(self, parent, action, model, course=1):
        self._action       = action
        actionRecord       = action.getRecord()
        self._actionId     = forceRef(actionRecord.value('id'))
        self._eventId      = action.getEventId()
        self._actionTypeId = forceRef(actionRecord.value('actionType_id'))
        self._amount       = None
        CJobTicketProbeBaseItem.__init__(self, parent, self._actionId, model,
                                         canBeChecked=True, editableExternalId=True, editableEquipmentId=True,
                                         course=course)


    def _getValue(self):
        actionType = self._action.getType()
        return u' | '.join([actionType.code, actionType.name])


    def loadChildren(self):
        result = []
        clientSex, clientAge = getClientInfoByAction(self._action)
        actionType = self._action.getType()
        propertyTypeList = actionType.getPropertiesById().items()
        propertyTypeList.sort(key=lambda x: (x[1].idx, x[0]))
        propertyTypeList = [x[1] for x in propertyTypeList if x[1].applicable(clientSex, clientAge)]
        for propertyType in propertyTypeList:
            if propertyType.testId:
                if not self.isCourseJobTicket or self.isActualCourseNumber(propertyType.course):
                    testItem = CJobTicketProbeTestItem(self, propertyType, self.model(), self._eventId, self._actionId,
                                                       course=self._course)
                    result.append(testItem)
        return result


    def containerTypeId(self):
        return self.parent().containerTypeId()


    def action(self):
        return self._action


    def amount(self, column):
        if column == ITEM_AMOUNT_COLUMN:
            if self._actionTypeId:
                if self._amount is None:
                    amount = getAmountForActionTypeId(self._actionTypeId)
                    self._amount = QVariant(QLocale().toString(amount, 'f', 2))
                return self._amount
        return QVariant()

    def setEquipmentId(self, equipmentId, recurse = True):
        self._equipmentId = equipmentId
        self._specimenTypeId = getActualSpecimenTypeId(self.testId(), self._equipmentId)
        if self._items and recurse:
            for item in self._items:
                item.setEquipmentId(equipmentId)
        self.checkEquipmentId()


class CJobTicketProbeContainerItem(CJobTicketProbeBaseItem):
    def __init__(self, parent, containerTypeId, model, course=1):
        self._capacity = None
        self._amount = None
        self._code = None
        boldFont = QtGui.QFont()
        boldFont.setWeight(QtGui.QFont.Bold)
        self._qBoldFont = QVariant(boldFont)
        CJobTicketProbeBaseItem.__init__(self, parent, containerTypeId, model,
                                         canBeChecked=True, editableExternalId=True, editableEquipmentId=True,
                                         course=course)

    def _getValue(self):
        record = QtGui.qApp.db.getRecord('rbContainerType',
                                         'CONCAT_WS(\' | \', code, name) AS val, color, amount', self._id)
        if record:
            self._color = QtGui.QColor(forceString(record.value('color')))
            self._capacity = forceDouble(record.value('amount'))
            return forceString(record.value('val'))
        else:
            self._color = QtGui.QColor()
            return ''


    def loadChildren(self):
        result = []
        actionList = self.getActionListByContainerTypeId(self._id)
        for action in actionList:
            actionItem = CJobTicketProbeActionItem(self, action, self.model(), course=self._course)
            if actionItem.items():
                result.append(actionItem)
        return result


    def containerTypeId(self):
        return self._id


    def getActionListByContainerTypeId(self, containerTypeId):
        return self.model().getActionListByContainerTypeId(containerTypeId)


    def columnCount(self):
        return 4


    def background(self, column):
        if column == ITEM_BACKGROUND_COLUMN:
            return QVariant(self._color)
        return CJobTicketProbeBaseItem.background(self, column)


    def font(self, column):
        if column == ITEM_AMOUNT_COLUMN:
            return self._qBoldFont
        return CJobTicketProbeBaseItem.font(self, column)


    def amount(self, column):
        if column == ITEM_AMOUNT_COLUMN:
            if self._capacity:
                if self._amount is None:
                    amountForCaontainerTypeId = getAmountForContainerTypeId(self._id)
                    self._amount = QVariant(int(amountForCaontainerTypeId/self._capacity)+1)
                return self._amount
        return QVariant()

    def setEquipmentId(self, equipmentId, recurse = True):
        if self._allowedEquipIdList:
            self._equipmentId = equipmentId if equipmentId in self._allowedEquipIdList else None
        else:
            self._equipmentId = equipmentId
        self._specimenTypeId = getActualSpecimenTypeId(self.testId(), self._equipmentId)
        if self._items and recurse:
            for item in self._items:
                item.setEquipmentId(equipmentId)
        self.checkEquipmentId()
    
    def getCode(self):
        return self._code if self._code else forceString(QtGui.qApp.db.translate('rbContainerType', 'id', self._id, 'code'))
    
    def __lt__(self, other):
        return self.getCode() < other.getCode()


class CJobTicketCourseItem(CJobTicketProbeBaseItem):
    def __init__(self, parent, course, actionList, model):
        self.__actionList = actionList
        CJobTicketProbeBaseItem.__init__(self, parent, None, model, course=course)

    def _getValue(self):
        return '%s' % self._course

    def loadChildren(self):
        db = QtGui.qApp.db
        existsContainerTypeId = []
        model = self.model()
        result = []
        
        for action in self.__actionList:
            actionRecord = action.getRecord()
            tissueTypeId = model.getTissueTypeIdForAction(action.getId())
            if tissueTypeId:
                actionTypeId = forceRef(actionRecord.value('actionType_id'))
                condTmpl = 'course=%d AND master_id=%d AND tissueType_id=%d AND (jobType_id=%d OR jobType_id IS NULL)'
                cond = condTmpl % (self._course, actionTypeId, tissueTypeId, model.jobTypeId)
                containerTypeId = self._getContainerTypeId(cond, actionTypeId)
                
                if containerTypeId:
                    if containerTypeId not in existsContainerTypeId:
                        existsContainerTypeId.append(containerTypeId)
                        containerItem = CJobTicketProbeContainerItem(self, containerTypeId, self.model(),
                                                                     course=self._course)
                        result.append(containerItem)
                    self.mapContainerTypeIdToActionList(containerTypeId, action)

        return result

    def mapContainerTypeIdToActionList(self, containerTypeId, action):
        self.model().mapContainerTypeIdToActionRecordList(containerTypeId, action)

    def _getContainerTypeId(self, cond, actionTypeId):
        db = QtGui.qApp.db
        # Сначала мы будем пытаться подобрать по типу работы, по этому отфильтруем записи которые имеют точное указание
        # Если по нашему сусловию типа работы ничего не подберется, тогда по порядку мы возьмем первую запись
        # без кокретного типа работы.
        oder = 'jobType_id IS NULL DESC, idx'
        record = db.getRecordEx('ActionType_TissueType', 'containerType_id, amount, course', cond, oder)
        if record:
            amount = forceDouble(record.value('amount'))
            course = forceInt(record.value('course'))
            mapAmountForActionTypeId(actionTypeId, amount)
            containerTypeId = forceRef(record.value('containerType_id'))
            self.model().mapCourseToContainerTypeIdList(course, containerTypeId)
            calcAmountForContainerTypeId(containerTypeId, amount)
            return containerTypeId
        return None


class CJobTicketProbeRootItem(CJobTicketProbeBaseItem):
    def __init__(self, model):
        CJobTicketProbeBaseItem.__init__(self, None, None, model)

    def _getValue(self):
        return u'Все'

    def loadChildren(self, actionList=None):
        if actionList is None:
            actionList = self.model().actionList()

        if self.isCourseJobTicket:
            return self.__loadChildrenCourses(actionList)
        else:
            return self.__loadChildrenContainers(actionList)

    def __loadChildrenCourses(self, actionList):
        courses2Actions = {}

        result = []
        CTissueAmountForContainerType.reset()

        model = self.model()
        for action in actionList:
            for course in xrange(1, action.maxPropertiesCourse()+1):
                courses2Actions.setdefault(course, []).append(action)
            mapClientInfoByAction(action)

        for course in xrange(1, self.getMaxCourseNumber() + 1):
            result.append(CJobTicketCourseItem(self, course, courses2Actions.get(course, []), model))

        return result

    def __loadChildrenContainers(self, actionList):
        result = []
        existsContainerTypeId = []
        CTissueAmountForContainerType.reset()
        db = QtGui.qApp.db
        for action in actionList:
            mapClientInfoByAction(action)
            actionRecord = action.getRecord()
            tissueTypeId = self.model().getTissueTypeIdForAction(action.getId())
            if tissueTypeId:
                actionTypeId = forceRef(actionRecord.value('actionType_id'))
                condTmpl = 'master_id=%d AND tissueType_id=%d AND (jobType_id=%d OR jobType_id IS NULL)'
                cond =  condTmpl % (actionTypeId, tissueTypeId, self.model().jobTypeId)
                containerTypeId = self._getContainerTypeId(cond, actionTypeId)
                
                if containerTypeId:
                    if containerTypeId not in existsContainerTypeId:
                        existsContainerTypeId.append(containerTypeId)
                        containerItem = CJobTicketProbeContainerItem(self, containerTypeId, self.model())
                        result.append(containerItem)
                    self.mapContainerTypeIdToActionList(containerTypeId, action)
                    
        result.sort()
        return result

    def _getContainerTypeId(self, cond, actionTypeId):
        db = QtGui.qApp.db
        # Сначала мы будем пытаться подобрать по типу работы, по этому отфильтруем записи которые имеют точное указание
        # Если по нашему сусловию типа работы ничего не подберется, тогда по порядку мы возьмем первую запись
        # без кокретного типа работы.
        oder = 'jobType_id IS NULL DESC, idx'
        record = db.getRecordEx('ActionType_TissueType', 'containerType_id, amount, course', cond, oder)
        if record:
            amount = forceDouble(record.value('amount'))
            course = forceInt(record.value('course'))
            mapAmountForActionTypeId(actionTypeId, amount)
            containerTypeId = forceRef(record.value('containerType_id'))
            self.model().mapCourseToContainerTypeIdList(course, containerTypeId)
            calcAmountForContainerTypeId(containerTypeId, amount)
            return containerTypeId
        return None

    def mapContainerTypeIdToActionList(self, containerTypeId, action):
        self.model().mapContainerTypeIdToActionRecordList(containerTypeId, action)

    def setEquipmentId(self, equipmentId, recurse = True):
        if self._allowedEquipIdList:
            self._equipmentId = equipmentId if equipmentId in self._allowedEquipIdList else None
        else:
            self._equipmentId = equipmentId
        self._specimenTypeId = getActualSpecimenTypeId(self.testId(), self._equipmentId)
        if self._items and recurse:
            for item in self._items:
                item.setEquipmentId(equipmentId)
        self.checkEquipmentId()


class CJobTicketProbeModel(CTreeModel):
    def __init__(self, parent):
        CTreeModel.__init__(self, parent, CJobTicketProbeRootItem(self))
        self.rootItemVisible = False
        self._actionList = []
        self._mapContainerTypeIdToActionList = {}
        self._mapCourseToContainerTypeIdList = {}
        self._parent = parent
        self._jobTypeId = None
        self.resetCache()
        self._checkAssignable = False
        self._orgStructureId = None
        
        
    def getTissueTypeIdForAction(self, actionId):
        for tissueTypeId, (records, actionIdList) in self._parent.actualByTissueType.items():
            if actionId in actionIdList:
                return tissueTypeId
        return self._parent.cmbTissueType.value()

    def getTakenTissueIdByCourseNumber(self, course, tissueTypeId=None):
        return self._parent.getTakenTissueIdByCourseNumber(course, tissueTypeId)

    def hasSavedTakenTissue(self, tissueTypeId=None):
        if tissueTypeId is None:
            tissueTypeId = self.suggestedTissueTypeId()
        return tissueTypeId in self._parent.takenTissueRecords

    def isLastCoursePart(self):
        return self._parent.isLastCoursePart()

    def getMaxCourseNumber(self):
        return self._parent.getMaxCourseNumber()

    def getCurrentCourse(self):
        return self._parent._courseNumber

    def mapCourseToContainerTypeIdList(self, course, containerId):
        self._mapCourseToContainerTypeIdList.setdefault(course, set()).add(containerId)

    def getCourseContainerTypeIdList(self, course):
        return list(self._mapCourseToContainerTypeIdList.get(course, []))

    @property
    def isCourseJobTicket(self):
        return self._parent.isCourseJobTicket

    def isAllAvailableExternalIdByBarCode(self):
        # Так сделано чтобы корректно проверять не валидные ситуации
        # при которых нет ни одного редактируемого CJobTicketProbeTestItem
        result = False
        for item in self.absoluteItemList():
            if isinstance(item, CJobTicketProbeTestItem) and item.hasEditableFlag():
                if not (item.externalId and item.externalIdIsByBarCode):
                    return False
                result = True
        return result


    @property
    def jobTypeId(self):
        return self._jobTypeId


    def setCheckAssignable(self, value):
        self._checkAssignable = value
    
    
    def setOrgStructureId(self, orgStructureId):
        self._orgStructureId = orgStructureId


    def checkAssignable(self):
        return self._checkAssignable


    def resetCache(self):
        resetCache()


    def checkableColumnList(self):
        return [ITEM_CHECKED_COLUMN]


    def currentEnteredTakenTissueExternalId(self):
        return unicode(self._parent.edtTissueExternalId.text())


    def suggestedTissueTypeId(self):
        return self._parent.cmbTissueType.value()


    def saveTakenTissueRecord(self):
        if self._parent.saveTakenTissueRecord():
            jobTicketId = self._parent.itemId()
            if jobTicketId:
                self._parent._saveInternals(jobTicketId)
            return True
        return False
    

    def takenTissueRecord(self, tissueTypeId=None):
        if tissueTypeId is None:
            tissueTypeId = self.suggestedTissueTypeId()
        return self._parent.takenTissueRecords.get(tissueTypeId)


    def takenTissueId(self, tissueTypeId=None):
        TTJR = self.takenTissueRecord(tissueTypeId)
        return forceRef(TTJR.value('id')) if TTJR else None


    def getTakenTissueIdForItem(self, item):
        tissueTypeId = self.getTissueTypeIdForAction(item.parent().action().getId())
        if self.isCourseJobTicket:
            return self.getTakenTissueIdByCourseNumber(item._course, tissueTypeId)
        else:
            return self.takenTissueId(tissueTypeId)


    def mapContainerTypeIdToActionRecordList(self, containerTypeId, action):
        actionList = self._mapContainerTypeIdToActionList.setdefault(containerTypeId, [])
        if not self.isActionInActionList(action, actionList):
            actionList.append(action)


    def isActionInActionList(self, action, actionList):
        actionId = action.getId()
        return any( act.getId() == actionId
                    for act in actionList
                  )


    def getActionListByContainerTypeId(self, containerTypeId):
        return self._mapContainerTypeIdToActionList.get(containerTypeId, [])


    def columnCount(self, index=None):
        return 6


    def rowCount(self, parent=None):
        return CTreeModel.rowCount(self, parent)


    def setActionList(self, actionList, force=False):
        if actionList != self._actionList or force:
            self._actionList = actionList
            self.reset()

    def setJobTypeId(self, jobTypeId):
        self._jobTypeId = jobTypeId


    def loadChildrenItems(self):
        self._rootItem.loadChildren(self._actionList)
        self.reset()



    def actionList(self):
        return self._actionList


    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        if role == Qt.DisplayRole:
            item = index.internalPointer()
            if item:
                return item.data(index.column())
        elif role == Qt.BackgroundRole:
            item = index.internalPointer()
            if item:
                return item.background(index.column())
        elif role == Qt.CheckStateRole:
            item = index.internalPointer()
            if item:
                return item.checked(index.column())
        elif role == Qt.FontRole:
            item = index.internalPointer()
            if item:
                return item.font(index.column())
        return QVariant()


    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                if section == ITEM_TEXT_VALUE_COLUMN:
                    return QVariant(u'Пробы')
                elif section == EQUIPMENT_ID_COLUMN:
                    return QVariant(u'Оборудование')
                elif section == SPECIMEN_TYPE_ID_COLUMN:
                    return QVariant(u'Тип образца')
                elif section == ITEM_BACKGROUND_COLUMN:
                    return QVariant(u'Цветовая маркировка')
                elif section == EXTERNAL_ID_COLUMN:
                    return QVariant(u'Идентификатор')
                elif section == ITEM_AMOUNT_COLUMN:
                    return QVariant(u'Количество')
        return QVariant()


    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False
        if role == Qt.CheckStateRole:
            column = index.column()
            if column == ITEM_CHECKED_COLUMN:
                item = index.internalPointer()
                if item and item.canBeChecked(column):
                    item.setChecked(not forceBool(item.checked(column)))
                    self.emitAllChanged()
                    return True
        elif role == Qt.EditRole:
            column = index.column()
            if column == EXTERNAL_ID_COLUMN:
                item = index.internalPointer()
                if item and item.editableExternalId(column):
                    item.setExternalId(forceString(value))
                    item.parent().checkExternalId()
                    self.emitAllChanged()
                    return True
            elif column == EQUIPMENT_ID_COLUMN:
                item = index.internalPointer()
                if item and item.editableEquipmentId(column):
                    item.setEquipmentId(forceRef(value))
                    item.parent().checkEquipmentId()
                    self.emitAllChanged()
                    return True
            elif column == SPECIMEN_TYPE_ID_COLUMN:
                item = index.internalPointer()
                if item and item.editableSpecimenTypeId(column):
                    item.setSpecimenTypeId(forceRef(value))
                    self.emitAllChanged()
                    return True
        return False


    def emitAllChanged(self):
        index1 = self.index(0, 0)
        index2 = self.index(self.rowCount(), self.columnCount())
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index1, index2)


    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        item = index.internalPointer()
        if not item:
            return Qt.NoItemFlags
        return item.flags(index)


    def absoluteItemList(self):
        result = []
        self.getRootItem().absoluteItemList(result)
        return result


    def resetItems(self):
        for item in self.absoluteItemList():
            item.resetItems()
        self._mapContainerTypeIdToActionList.clear()
        self.loadChildrenItems()


    def existCheckedProbeItems(self, notSaved=False):
        def filterFunc(item):
            if not (isinstance(item, CJobTicketProbeTestItem) and forceBool(item.checked(ITEM_CHECKED_COLUMN))):
                return False
                
            if self.isCourseJobTicket:
                tissueTypeId = self.getTissueTypeIdForAction(item.parent().action().getId())
                ttjr = self._parent.takenTissueRecords.get(tissueTypeId)
                currentCourse = forceInt(ttjr.value('course')) if ttjr else 1
                if item._course != currentCourse:
                    return False
                    
            if notSaved and item.saved():
                return False
                
            return True

        return filter(filterFunc, self.absoluteItemList())


    def askOkOrCancel(self, message):
        result = QtGui.QMessageBox.warning(self._parent,
                                           u'Внимание!',
                                           message,
                                           QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel,
                                           QtGui.QMessageBox.Cancel)
        return result == QtGui.QMessageBox.Ok


    def existsNotCheckedItems(self):
        def filterFunc(item):
            result = isinstance(item, CJobTicketProbeTestItem) and not forceBool(item.checked(ITEM_CHECKED_COLUMN))
            if result:
                result =  not item.saved()
            return result
        allItems = self.absoluteItemList()
        return filter(filterFunc, allItems)


    def isExistsNotCheckedItems(self):
        return bool(self.existsNotCheckedItems())

    def isExistsCheckedItems(self, notSaved=False):
        return bool(self.existCheckedProbeItems(notSaved))


    def getIsAutoSave(self):
        for item in self.absoluteItemList():
            if isinstance(item, CJobTicketProbeTestItem) and not item.saved():
                if not item._equipmentId:
                    return False
                isAutoSave = forceBool(QtGui.qApp.db.translate('rbEquipment', 'id', item._equipmentId, 'samplePreparationMode'))
                if not isAutoSave:
                    return False
        return True


    def registrateProbe(self, forceCheck=False):
        if forceCheck:
            self.getRootItem().setChecked(True)
            
        testItems = self.existCheckedProbeItems(notSaved=False)
        if not testItems:
            return

        unsavedTissues = {}
        for item in testItems:
            tissueTypeId = self.getTissueTypeIdForAction(item.parent().action().getId())
            if not self.takenTissueId(tissueTypeId):
                extId = forceString(item.data(EXTERNAL_ID_COLUMN))
                if tissueTypeId not in unsavedTissues or extId:
                    unsavedTissues[tissueTypeId] = extId

        if unsavedTissues:
            if not self.askOkOrCancel(u'Необходимо сохранить забор ткани для выбранных проб. Сохранить?'):
                return
                
            for tissueTypeId, extId in unsavedTissues.items():
                success = self._parent.saveSpecificTakenTissue(tissueTypeId, extId)
                if not success:
                    tissueName = forceString(QtGui.qApp.db.translate('rbTissueType', 'id', tissueTypeId, 'name'))
                    QtGui.QMessageBox.warning(self._parent, 
                        u'Внимание!', 
                        u'Не удалось сохранить забор для типа ткани "%s".' % tissueName,
                        QtGui.QMessageBox.Ok)
                    return

        testIdToProbeId = {}
        isAutoSave = True
        for item in testItems:
            if not item.saved() and item._equipmentId:
                if forceInt(QtGui.qApp.db.translate('rbEquipment', 'id', item._equipmentId, 'samplePreparationMode')) != 1:
                    isAutoSave = False
                    break
                    
        self.setProbesStatus(testIdToProbeId.values(), 1)
            
        if self.isExistsCheckedItems(True):
            if not isAutoSave and not self.askOkOrCancel(u'Вы уверены, что хотите зарегистрировать выбранные пробы?'):
                return
            self._registrateProbe()

        for item in self.absoluteItemList():
            if isinstance(item, CJobTicketProbeTestItem) and not item.saved() and not item._probeId:
                item.setSaved(False, None)

        db = QtGui.qApp.db
        tableClient = db.table('Client')
        tableTest = db.table('rbEquipment_Test')
        tableEquipment = db.table('rbEquipment')
        equipmentCache = {}
        taskMap = {}
        isOk = True
        
        for item in testItems:
            takenTissueId = self.getTakenTissueIdForItem(item)
            if not takenTissueId:
                continue

            if self.isCourseJobTicket:
                takenTissueRecord = db.getRecord('TakenTissueJournal', '*', takenTissueId)
                courseNumber = forceInt(takenTissueRecord.value('course')) if takenTissueRecord else 1
                if item._course != courseNumber:
                    continue

            if item.saved():
                equipmentId = item.equipmentId()
                equipment = equipmentCache.setdefault(equipmentId,  db.getRecord(tableEquipment, '*', equipmentId))
                if not equipment:
                    isOk = False
                    break
                protocol = forceInt(equipment.value('protocol'))
                if protocol != CEquipmentProtocol.samson:
                    continue
                
                taskKey = (equipment, item.externalId)
                if taskKey not in taskMap:
                    taskMap[taskKey] = { 
                        '_id'       : None,
                        'ttjid'     : takenTissueId,
                        'patient'   : None,
                        'ibm'       : None,
                        'tests'     : []
                    }
                task = taskMap[taskKey]
                
                action = item.getAction()
                prop = item.getProperty()
                testRec = db.getRecordEx(tableTest, ['hardwareTestCode', 'type'],  [tableTest['test_id'].eq(item.testId()), tableTest['equipment_id'].eq(equipmentId)])
                if testRec:
                    testType = forceInt(testRec.value(1))
                    if testType != 2:
                        continue
                    if not task['patient']:
                        patient = {}
                        clientId = action.event.client_id
                        clientRecord = db.getRecord(tableClient, 'Client.*, age(Client.birthDate, now()) as age',
                                                    clientId)
                        orgStructureRecord = db.getRecord('OrgStructure', '*', item._model._orgStructureId)
                        docRecord = db.getRecord('Person', '*', forceInt(action.getRecord().value('setPerson_id')))
                        patient['id'] = clientId
                        patient['lastName'] = forceString(clientRecord.value('lastName'))
                        patient['firstName'] = forceString(clientRecord.value('firstName'))
                        patient['patrName'] = forceString(clientRecord.value('patrName'))
                        patient['age'] = forceInt(clientRecord.value('age'))
                        patient['doc'] = formatShortName(forceString(docRecord.value('lastName')),
                                                         forceString(docRecord.value('firstName')), forceString(
                                docRecord.value('patrName'))) if docRecord else u'Не указан'
                        patient['otd'] = forceString(
                            orgStructureRecord.value('code')) if orgStructureRecord else u'Не указано'
                        task['patient'] = patient
                    test = { 'code':    forceString(testRec.value(0)),
                             'probeid': item._probeId
                           }
                    if prop._value:
                        test['result'] = unicode(prop._value)
                    task['tests'].append(test)
                    
        if isOk:
            for (equipment, externalId), task in taskMap.items():
                if task['tests']:
                    task['ibm'] = externalId
                    try:
                        params = json.loads(forceString(equipment.value('address')))
                        auth = params['auth']
                        addr = params['addr']
                    except:
                        isOk = False
                        equipmentId = forceRef(equipment.value('id'))
                        QtGui.qApp.log(u'Экспорт в лис', u'Некорректные настройки оборудования, id %d'%equipmentId)
                        break
                    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer %s'%auth}
                    r = requests.put('http://%s/task'%addr,  json=task,  headers = headers)
                    if r.status_code != 200:
                        isOk = False
                        QtGui.qApp.log(u'Экспорт в лис', r.content)

        if not isOk:
            QtGui.QMessageBox.warning(self._parent,
                                           u'Внимание!',
                                           u'Произошла ошибка при передаче в лис',
                                           QtGui.QMessageBox.Ok ,
                                           QtGui.QMessageBox.Ok)
        else:
            self.emitAllChanged()


    def _registrateProbe(self):
        db = QtGui.qApp.db
        db.transaction()
        try:
            testItems = self.existCheckedProbeItems(notSaved=True)
            testIdToProbeId = {}
            for item in testItems:
                takenTissueId = self.getTakenTissueIdForItem(item)
                if not takenTissueId:
                    continue
                    
                if self.isCourseJobTicket:
                    takenTissueRecord = db.getRecord('TakenTissueJournal', '*', takenTissueId)
                    courseNumber = forceInt(takenTissueRecord.value('course')) if takenTissueRecord else 1
                    if item._course != courseNumber:
                        continue
                else:
                    courseNumber = 1

                probeId = self.saveProbe(takenTissueId,
                                         item.propertyType(),
                                         forceString(item.data(EXTERNAL_ID_COLUMN)),
                                         [],
                                         testIdToProbeId,
                                         item.containerTypeId(),
                                         item,
                                         courseNumber)
                if probeId:
                    item.setSaved(True, probeId)

            self.setProbesStatus(testIdToProbeId.values(), 1)
            db.commit()
            
            self.emitAllChanged()
            self.resetItems()
            
        except Exception as e:
            db.rollback()
            QtGui.qApp.logCurrentException()
            QtGui.QMessageBox.critical(self._parent,
                                      u'Внимание!',
                                      ''.join([u'Произошла ошибка!\n', unicode(e)]),
                                      QtGui.QMessageBox.Ok,
                                      QtGui.QMessageBox.Ok)


    def saveProbe(self, takenTissueId, propertyType, externalId, testActionList,
                  testIdToProbeId, containerTypeId, item, courseNumber=1):
        testId = propertyType.testId
        equipmentId = item.equipmentId()
        specimenTypeId = item.specimenTypeId()
        if not equipmentId:
            return None

        if not specimenTypeId:
            specimenTypeId = getActualSpecimenTypeId(testId, equipmentId)
            if not specimenTypeId:
                raise CException(u'В Оборудовании не указан тип образца для теста')
            item.setSpecimenTypeId(specimenTypeId)

        probeId = testIdToProbeId.get(testId, None)
        
        if not externalId:
            externalId = forceString(QtGui.qApp.db.translate('TakenTissueJournal', 'id', takenTissueId, 'externalId'))

        if not externalId:
            return None
            
        action = item.getAction()
        isUrgent = forceInt(action.getRecord().value('isUrgent'))
        if not probeId:
            db = QtGui.qApp.db
            tableProbe = db.table('Probe')
            record = tableProbe.newRecord()
            record.setValue('course', QVariant(courseNumber))
            record.setValue('status', QVariant(0)) # без результата
            record.setValue('test_id', QVariant(testId))
            record.setValue('workTest_id', QVariant(testId))
            record.setValue('takenTissueJournal_id', QVariant(takenTissueId))
            record.setValue('typeName', QVariant(propertyType.typeName))
            record.setValue('norm', QVariant(propertyType.norm))
            record.setValue('unit_id', QVariant(propertyType.unitId))
            record.setValue('externalId', QVariant(externalId))
            record.setValue('containerType_id', QVariant(containerTypeId))
            record.setValue('equipment_id', QVariant(equipmentId))
            record.setValue('specimenType_id', QVariant(specimenTypeId))
            record.setValue('isUrgent',  QVariant(isUrgent))
            probeId = db.insertRecord(tableProbe, record)
            testIdToProbeId[testId] = probeId
            
        self.syncItemsForSaving(testId, externalId, probeId, testActionList)
        return probeId


    def setProbesStatus(self, probeIdList, status):
        db = QtGui.qApp.db
        if probeIdList:
            tableProbe = db.table('Probe')
            stmt = 'UPDATE Probe SET modifyDateTime=NOW(), status=%d WHERE %s' % (status, tableProbe['id'].inlist(probeIdList))
            db.query(stmt)


    def syncItemsForSaving(self, testId, externalId, probeId, testActionList):
        sameTestItems = getItemsByTestId(testId)
        for sameTestItem in sameTestItems:
            testAction = sameTestItem.getAction()
            if testAction not in testActionList:
                testActionList.append(testAction)
            sameTestItem.setChecked(True)
            sameTestItem.setExternalId(externalId)
            sameTestItem.setSaved(True, probeId)


    def loadAll(self):
        root = self.getRootItem()
        for item in root.items():
            self.__loadAll(item)
        if not self.isExistsCheckedItems():
            root.setChecked(True)
        if root.isCourseJobTicket:
            root.setChecked(True, recurse=True)


    def __loadAll(self, root):
        for item in root.items():
            self.__loadAll(item)
        if isinstance(root, CJobTicketProbeActionItem):
            root.checkEquipmentId()


    def saveFunc(self, record, status):
        record.setValue('status', status)
        tableProbe = QtGui.qApp.db.table('Probe')
        QtGui.qApp.db.updateRecord(tableProbe, record)


    def getRootEquipmentId(self):
        return self.getRootItem()._equipmentId


#            self.setItemValueToProperty(testAction, sameTestItem)
#
#
#    def setItemValueToProperty(self, action, item):
#        propertyType = item.propertyType()
#        property = action.getPropertyById(propertyType.id)
#        property.setValue(propertyType.convertQVariantToPyValue(item.data(EXTERNAL_ID_COLUMN)))


# ####################################################

class CItemDelegate(QtGui.QItemDelegate):
    def __init__(self, parent, barCodeExecutingContext):
        QtGui.QItemDelegate.__init__(self, parent)
        self.row = 0
        self.lastrow = 0
        self.column = 0
        self.editor = None
        self._view = parent
        self._barCodeExecutingContext = barCodeExecutingContext


    def createEditor(self, parent, option, index):
        item = index.internalPointer()
        column = index.column()
        editor = item.createEditor(parent, column)
        self.connect(editor, SIGNAL('commit()'), self.emitCommitData)
        self.connect(editor, SIGNAL('editingFinished()'), self.commitAndCloseEditor)
        self.editor   = editor
        self.row      = index.row()
        self.rowcount = index.model().rowCount(None)
        self.column   = column
        if self.column == EXTERNAL_ID_COLUMN:
            if not self._barCodeExecutingContext.canStarted:
                item.setExternalIdIsByBarCode(False)
                return editor

            self._barCodeExecutingContext.init(editor)
            callback = functools.partial(self._view.setExternalIdIsByBarCode, item)
            self._barCodeExecutingContext.setOnStop(callback)
            self._barCodeExecutingContext.setOnFail(callback)
            self._barCodeExecutingContext.start()
        return editor


    def setEditorData(self, editor, index):
        if editor is not None:
            item = index.internalPointer()
            if item:
                column = index.column()
                item.setEditorData(column, editor, item.data(column))


    def setModelData(self, editor, model, index):
        if editor is not None:
            item = index.internalPointer()
            column = index.column()
            model.setData(index, item.getEditorData(column, editor))
            self._barCodeExecutingContext.stop()
            setattr(self._barCodeExecutingContext, '_closeProbesAndCheckExternalId', column == EXTERNAL_ID_COLUMN)
            self._barCodeExecutingContext.setCanStarted(False)


    def emitCommitData(self):
        self._barCodeExecutingContext.resetDependincies()
        self.emit(SIGNAL('commitData(QWidget *)'), self.sender())


    def commitAndCloseEditor(self):
        self._barCodeExecutingContext.resetDependincies()
        editor = self.sender()
        self.emit(SIGNAL('commitData(QWidget *)'), editor)
        self.emit(SIGNAL('closeEditor(QWidget *,QAbstractItemDelegate::EndEditHint)'), editor, QtGui.QAbstractItemDelegate.NoHint)
        self._view.tryCloseProbesTreeEditorAndJTByBarCode()
        setattr(self._barCodeExecutingContext, '_closeProbesAndCheckExternalId', False)


    def eventFilter(self, object, event):
        def editorIsEmpty():
            if isinstance(self.editor, QtGui.QLineEdit):
                return self.editor.text() == ''
            if  isinstance(self.editor, QtGui.QComboBox):
                return self.editor.currentIndex() == 0
            if  isinstance(self.editor, CDateEdit):
                return not self.editor.dateIsChanged()
            if  isinstance(self.editor, QtGui.QDateEdit):
                return not self.editor.date().isValid()
            return False

        def editorCanEatTab():
            if  isinstance(self.editor, QtGui.QDateEdit):
                return self.editor.currentSection() != QtGui.QDateTimeEdit.YearSection
            return False

        def editorCanEatBacktab():
            if isinstance(self.editor, QtGui.QDateEdit):
                return self.editor.currentSection() != QtGui.QDateTimeEdit.DaySection
            return False


        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Tab:
                if editorCanEatTab():
                    self.editor.keyPressEvent(event)
                    return True
                if self.editor is not None:
                    self.parent().commitData(self.editor)
                self.parent().keyPressEvent(event)
                return True
            elif event.key() == Qt.Key_Backtab:
                if editorCanEatBacktab():
                    self.editor.keyPressEvent(event)
                    return True
                if self.editor is not None:
                    self.parent().commitData(self.editor)
                self.parent().keyPressEvent(event)
                return True
            elif event.key() == Qt.Key_Return:
                if isinstance(self.editor, QtGui.QLineEdit):
                    return QtGui.QItemDelegate.eventFilter(self, object, event)
        return QtGui.QItemDelegate.eventFilter(self, object, event)


class CJobTicketProbeTreeView(QtGui.QTreeView, CPreferencesMixin):
    def __init__(self, parent):
        QtGui.QTreeView.__init__(self, parent)
        self._probesTreeEditor = parent
        self._barCodeExecutingContext = CBarCodeActionExecutingContext(self, canStarted=False)
        delegate = CItemDelegate(self, self._barCodeExecutingContext)
        self.setItemDelegateForColumn(EQUIPMENT_ID_COLUMN,     delegate)
        self.setItemDelegateForColumn(SPECIMEN_TYPE_ID_COLUMN, delegate)
        self.setItemDelegateForColumn(EXTERNAL_ID_COLUMN,      delegate)
        self._popupMenu = QtGui.QMenu(self)
        self.connect(self._popupMenu, SIGNAL('aboutToShow()'), self.popupMenuAboutToShow)
        self._actRegistrateProbe = QtGui.QAction(u'Зарегистрировать пробы', self)
        self.connect(self._actRegistrateProbe, SIGNAL('triggered()'), self.registrateProbe)
        self._popupMenu.addAction(self._actRegistrateProbe)
        self._actScanBarCode = QtGui.QAction(self)
        self._actScanBarCode.setShortcuts(['Ctrl+B', 'Ctrl+Shift+B'])
        self.connect(self._actScanBarCode, SIGNAL('triggered()'), self.actScanBarcode_triggered)
        self.addAction(self._actScanBarCode)

    def tryCloseProbesTreeEditorAndJTByBarCode(self):
        if getattr(self._barCodeExecutingContext, '_closeProbesAndCheckExternalId', False):
            model = self.model()
            if model.isAllAvailableExternalIdByBarCode():
                self._probesTreeEditor.reject()
                model._parent.on_btnPrintTissueLabel_clicked(callingByBarCode=True)

    def registrateProbe(self):
        self.model().registrateProbe()

    def setExternalIdIsByBarCode(self, item):
        item.setExternalIdIsByBarCode(not self._barCodeExecutingContext.failed
                                      and self._barCodeExecutingContext.isWork())

    def actScanBarcode_triggered(self):
        self._barCodeExecutingContext.setCanStarted(True)
        items = self.model().absoluteItemList()
        if items:
            funcSetter = (self._setEditIfNotCourseJobTicket,
                          self._setEditIfCourseJobTicket)[self.model().isCourseJobTicket]
            for item in items:
                if funcSetter(item):
                    break

    def _setEditIfNotCourseJobTicket(self, item):
        if isinstance(item, CJobTicketProbeContainerItem) and forceString(item.data(EXTERNAL_ID_COLUMN)) == '':
            index = self.model().index(item.row(), EXTERNAL_ID_COLUMN)
            self.edit(index)
            return True
        return False

    def _setEditIfCourseJobTicket(self, item):
        if isinstance(item, CJobTicketProbeContainerItem) and forceString(item.data(EXTERNAL_ID_COLUMN)) == '':
            if not item.hasEditableFlag():
                return False
            parentIndex = self.model().index(item.parent().row(), EXTERNAL_ID_COLUMN)
            index = self.model().index(item.row(), EXTERNAL_ID_COLUMN, parentIndex)
            self.edit(index)
            return True
        return False

    def contextMenuEvent(self, event): # event: QContextMenuEvent
        self._popupMenu.exec_(event.globalPos())
        event.accept()

    def popupMenuAboutToShow(self):
        existCheckedProbeItems = self.model().existCheckedProbeItems(notSaved=True)
        self._actRegistrateProbe.setEnabled(bool(existCheckedProbeItems))

    def loadPreferences(self, preferences):
        model = self.model()
        for i in xrange(model.columnCount()):
            width = forceInt(getPref(preferences, 'col_'+str(i), None))
            if width:
                self.setColumnWidth(i, width)


    def savePreferences(self):
        preferences = {}
        model = self.model()
        if model:
            for i in xrange(model.columnCount()):
                width = self.columnWidth(i)
                setPref(preferences, 'col_'+str(i), QVariant(width))
        return preferences

# ####################################################


class CMapActionIdToClientInfo():
    cache = {}
    cacheByEventId = {}
    existsEventIdList = []

    @classmethod
    def update(cls, action):
        actionRecord = action.getRecord()
        eventId      = action.getEventId()
        actionId     = action.getId()
        if eventId not in cls.existsEventIdList:
            cls.existsEventIdList.append(eventId)
            db           = QtGui.qApp.db
            clientId     = forceRef(db.translate('Event', 'id', eventId, 'client_id'))
            clientRecord       = db.getRecord('Client', '*', clientId)
            if clientRecord:
                directionDate   = forceDate(actionRecord.value('directionDate'))
                clientSex       = forceInt(clientRecord.value('sex'))
                clientBirthDate = forceDate(clientRecord.value('birthDate'))
                clientAge       = calcAgeTuple(clientBirthDate, directionDate)
            else:
                clientSex = clientAge = None
            cls.cache[actionId] = (clientSex, clientAge)
            cls.cacheByEventId[eventId] = (clientSex, clientAge)
        else:
            cls.cache[actionId] = cls.cacheByEventId[eventId]


    @classmethod
    def get(cls, action):
        actionRecord = action.getRecord()
        actionId     = forceRef(actionRecord.value('id'))
        return cls.cache.get(actionId, (None, None))

    @classmethod
    def reset(cls):
        cls.cache.clear()
        cls.cacheByEventId.clear()
        cls.existsEventIdList = []

class CMapTestIdToItems():
    cache = {}

    @classmethod
    def update(cls, testId, item):
        itemList = cls.cache.setdefault(testId, [])
        if item not in itemList:
            itemList.append(item)


    @classmethod
    def getItems(cls, testId):
        return cls.cache.get(testId, [])


    @classmethod
    def reset(cls):
        cls.cache.clear()


class CTissueAmountForContainerType():
    cache = {}

    @classmethod
    def update(cls, containerTypeId, amount):
        existAmount = cls.cache.get(containerTypeId, 0.0)
        cls.cache[containerTypeId] = amount + existAmount

    @classmethod
    def get(cls, containerTypeId):
        return cls.cache.get(containerTypeId, 0.0)

    @classmethod
    def reset(cls):
        cls.cache.clear()



class CMapAmountToActionTypeId():
    cache = {}

    @classmethod
    def update(cls, actionTypeId, amount):
        if not actionTypeId in cls.cache:
            cls.cache[actionTypeId] = amount

    @classmethod
    def get(cls, actionTypeId):
        return cls.cache[actionTypeId]

    @classmethod
    def reset(cls):
        cls.cache.clear()


def resetCache():
    CMapActionIdToClientInfo.reset()
    CJobTicketProbeTestItem.reset()
    CMapTestIdToItems.reset()
    CTissueAmountForContainerType.reset()
    CMapAmountToActionTypeId.reset()


def getClientInfoByAction(action):
    return CMapActionIdToClientInfo.get(action)


def mapClientInfoByAction(action):
    CMapActionIdToClientInfo.update(action)


def getItemsByTestId(testId):
    return CMapTestIdToItems.getItems(testId)


def mapItemByTestId(testId, item):
    CMapTestIdToItems.update(testId, item)


def calcAmountForContainerTypeId(containerTypeId, amount):
    CTissueAmountForContainerType.update(containerTypeId, amount)


def getAmountForContainerTypeId(containerTypeId):
    return CTissueAmountForContainerType.get(containerTypeId)


def mapAmountForActionTypeId(actionTypeId, amount):
    CMapAmountToActionTypeId.update(actionTypeId, amount)


def getAmountForActionTypeId(actionTypeId):
    return CMapAmountToActionTypeId.get(actionTypeId)



# ##############################################################

class CSpecimenTypeComboBox(CRBComboBox):
    def __init__(self, parent):
        CRBComboBox.__init__(self, parent)
        self.setTable('rbSpecimenType', addNone=True, needCache=False)

    def setExternalFilter(self, testId=None, equipmentId=None):
        if testId or equipmentId:
            table = QtGui.qApp.db.table(self._tableName)
            filter = table['id'].inlist(self._getFilterList(testId, equipmentId))
            self.setFilter(filter)

    @staticmethod
    def _getFilterList(testId, equipmentId):
        db = QtGui.qApp.db
        table = db.table('rbEquipment_Test')
        cond = []
        if testId:
            cond.append(table['test_id'].eq(testId))
        if equipmentId:
            cond.append(table['equipment_id'].eq(equipmentId))
        return db.getDistinctIdList(table, 'specimenType_id', cond)
