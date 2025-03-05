# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2017 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################


from library.Utils  import forceBool, forceInt, forceRef, forceString, toVariant


class CActionProperty(object):
    def __init__(self, actionType, record=None, type=None, actionId=None, valueRecords=None):
        self._cachedText = None
        self._unitId = None
        self._norm = ''
        self._comment = ''
        self._templateId = None
        self._record = None
        self._changed = False
        self._isAssigned = False
        self._evaluation = None
        self._normChanged = False
        self._value = None
        self._id = None
        self.setType(type)
        if record:
            self.setRecord(record, actionType, valueRecords)
        elif self._type.isVector:
            self._value  = []
        elif self._type.defaultValue and actionId is None:
            self._value = self._type.convertDBValueToPyValue(toVariant(self._type.defaultValue))
            self._changed = True


    def setPresetValue(self, action):
        if self._type and not self._changed:
            self._value = self._type.valueType.getPresetValue(action)
            self._changed = bool(self._value)


    def setType(self, type):
        self._type = type
        if type:
            if type.isVector:
                self.getValue = self.getValueVector
                self.getText  = self.getTextVector
                self.getImage = self.getImageVector
                self.getInfo  = self.getInfoVector
            else:
                self.getValue = self.getValueScalar
                self.getText = self.getTextScalar
                self.getImage = self.getImageScalar
                self.getInfo = self.getInfoScalar
            self._unitId = type.unitId
            self._norm = type.norm
            self._templateId = type.templateId
            self._comment = type.comment


    def type(self):
        return self._type


    def applyDependents(self, action):
        if self.type().isNomenclatureValueType():
            nomenclatureId = self.getValue()
            if nomenclatureId:
                action.addNomenclatureEx(nomenclatureId)


    def preApplyDependents(self, action):
        if self.type().isNomenclatureValueType():
            nomenclatureId = self.getValue()
            if nomenclatureId:
                action.removeNomenclature(nomenclatureId)


    def setRecord(self, record, actionType, valueRecords=None):
        propertyTypeId = forceRef(record.value('type_id'))
        if self._type:
            assert self._type.id == propertyTypeId
        else:
            self.setType(actionType.getPropertyTypeById(propertyTypeId))
        self._record = record
        self._value = self._type.getValue(record.value('id'), valueRecords)
        self._unitId = forceRef(record.value('unit_id'))
        self._norm = forceString(record.value('norm'))
        self._isAssigned = forceBool(record.value('isAssigned'))
        self._id = forceRef(record.value('id'))
        evaluation = record.value('evaluation')
        self._evaluation = None if evaluation.isNull() else forceInt(evaluation)
        self._comment = forceString(record.value('comment'))


    def setNorm(self, norm):
        if self._norm != norm:
            self._normChanged = True
            self._norm = norm

    def setUnit(self, unitId):
        if self._unitId != unitId:
            self._changed = True
            self._unitId = unitId


    def getRecord(self):
        return self._record


    def save(self, actionId):
        if self._changed or self._normChanged:
            if not self._record:
                self._record = self._type.getNewRecord()
            self._record.setValue('action_id', toVariant(actionId))
            self._record.setValue('unit_id', toVariant(self._unitId))
            if self._normChanged:
                self._record.setValue('norm', toVariant(self._norm))
            self._record.setValue('isAssigned', toVariant(self._isAssigned))
            self._record.setValue('evaluation', toVariant(self._evaluation))
            self._record.setValue('unit_id', toVariant(self._unitId))
            self._record.setValue('comment', toVariant(self._comment))
            result = self._type.storeRecord(self._record, self._value)

#            if self.type().isJobTicketValueType():
#                from PyQt4 import QtGui
#                QtGui.qApp.makeJobTicketIdQueue(self.getValue())
            self._changed = False
        else:
            if self._record:
                result = forceRef(self._record.value('id'))
            else:
                result = None
        return result


    def getValueScalar(self):
        return self._value


    def getTextScalar(self):
        if self._type.valueType.cacheText and self._cachedText is None:
            self._cachedText = self._type.valueType.toText(self._value)
            result = self._cachedText
        elif self._cachedText is not None:
            result = self._cachedText
        else:
            result = self._type.valueType.toText(self._value)

        return result


    def getImageScalar(self):
        return self._type.valueType.toImage(self._value)


    def getInfoScalar(self, context):
        return self._type.valueType.toInfo(context, self._value)


    def getValueVector(self):
        return self._value[:] # shalow copy


    def getTextVector(self):
        toText = self._type.valueType.toText
        return [toText(x) for x in self._value]


    def getImageVector(self):
        toImage = self._type.valueType.toImage
        return [toImage(x) for x in self._value]


    def getInfoVector(self, context):
        toInfo = self._type.valueType.toInfo
        return [toInfo(context, x) for x in self._value]


    def setValue(self, value):
        try:
            value = self._type.valueType.convertDBValueToPyValue(toVariant(value))
        except:
            return
        if self._value != value:
            self._changed = True
            self._cachedText = None
        self._value = value


    def getUnitId(self):
        return self._unitId


    def getNorm(self):
        return self._norm

    def getId(self):
        return self._id

    def getTemplateId(self):
        return self._templateId


    def isAssigned(self):
        return self._isAssigned


    def setAssigned(self, isAssigned):
        if self._isAssigned != isAssigned:
            self._changed = True
        self._isAssigned = isAssigned


    def setUnitId(self, unitId):
        if self._unitId != unitId:
            self._changed = True
        self._unitId = unitId


    def getEvaluation(self):
        return self._evaluation


    def setEvaluation(self, evaluation):
        if self._evaluation != evaluation:
            self._changed = True
        self._evaluation = evaluation


    def getCommentType(self):
        if self._type:
            return self._type.comment
        else:
            return u''


    def getComment(self):
        return self._comment


    def setComment(self, comment):
        if self._comment != comment:
            self._changed = True
        self._comment = comment


    def copy(self, src):
        self.setAssigned(src.isAssigned())
        self.setValue(src.getValue())
        self.setEvaluation(src.getEvaluation())
        self.setComment(src.getComment())


    def copyIfNotEmpty(self, src):
        val = src.getValue()
        if val and not (isinstance(val, basestring) and val.isspace()):
            self.setAssigned(src.isAssigned())
            self.setValue(src.getValue())
            self.setEvaluation(src.getEvaluation())
            self.setComment(src.getComment())


    def copyIfNotIsspace(self, src):
        val = src.getValue()
        if not (isinstance(val, basestring) and val.isspace()):
            self.setAssigned(src.isAssigned())
            self.setValue(src.getValue())
            self.setEvaluation(src.getEvaluation())
            self.setComment(src.getComment())


    def copyIfString(self, src):
        val = src.getValue()
        if not (isinstance(val, basestring) and val.isspace()):
            if isinstance(val, basestring):
                oldValue = self.getValue()
                if oldValue:
                    oldValue += u'\n'
                    self.setValue(oldValue + src.getValue())
                else:
                    self.setValue(src.getValue())
            else:
                self.setAssigned(src.isAssigned())
                self.setValue(src.getValue())
                self.setEvaluation(src.getEvaluation())
                self.setComment(src.getComment())


    def getPreferredHeight(self):
        return self._type.getPreferredHeight()


    def isImage(self):
        return self._type.isImage()


    def isHtml(self):
        return self._type.isHtml()


    def isActionNameSpecifier(self):
        return self._type.isActionNameSpecifier

