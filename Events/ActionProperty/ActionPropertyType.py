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

from PyQt4 import QtGui
from PyQt4.QtCore import QIODevice, QString, QTextStream, QVariant

from Events.ActionProperty import CTextActionPropertyValueType, CStringActionPropertyValueType
from library.AgeSelector                 import parseAgeSelector, checkAgeSelector
from library.calc                        import functions, compileAndDetermineDependeces
from library.Utils                       import forceBool, forceDouble, forceInt, forceRef, forceString, forceStringEx

from ActionPropertyValueType             import CActionPropertyValueTypeRegistry

from BooleanActionPropertyValueType      import CBooleanActionPropertyValueType
from JobTicketActionPropertyValueType    import CJobTicketActionPropertyValueType
from NomenclatureActionPropertyValueType import CNomenclatureActionPropertyValueType
from NomenclatureActiveSubstanceActionPropertyValueType import CNomenclatureActiveSubstanceActionPropertyValueType
from NomenclatureUsingTypeActionPropertyValueType        import CNomenclatureUsingTypeActionPropertyValueType
from NomenclatureSmnnActionPropertyValueType import CNomenclatureSmnnActionPropertyValueType
from NomenclatureSmnnGrlsLfActionPropertyValueType import CNomenclatureSmnnGrlsLfActionPropertyValueType
from NomenclatureCalculationParamActionPropertyValueType import CNomenclatureCalculationParamActionPropertyValueType
from PacsActionPropertyValueType         import CPacsActionPropertyValueType
from UrlActionPropertyValueType          import CUrlActionPropertyValueType

from ActionPropertyTypeDataInheritance import CActionPropertyTypeDataInheritance


class CActionPropertyType(object):

    def __init__(self, record):
        self.initByRecord(record)


    def initByRecord(self, record):
        self.id = forceInt(record.value('id'))
        self.idx = forceInt(record.value('idx'))
        self.name = forceString(record.value('name'))
        self.shortName = forceString(record.value('shortName'))
        self.comment = forceString(record.value('comment'))
        self.descr = forceString(record.value('descr'))
        self.sectionCDA = forceString(record.value('sectionCDA'))
        self.var = forceString(record.value('var'))
        self.expr = forceString(record.value('expr'))
        self.typeName = forceString(record.value('typeName'))
        self.valueDomain = forceString(record.value('valueDomain'))
        self.dataInheritance = forceString(record.value('dataInheritance'))
        self.dataInheritanceExt = CActionPropertyTypeDataInheritance(self)
        self.valueType = self.getValueType()
        self.defaultValue = forceString(record.value('defaultValue'))
        self.isVector = forceBool(record.value('isVector'))
        self.isFill = forceBool(record.value('isFill'))
        self.unitIdAsQVariant = record.value('unit_id')
        self.normAsQVariant = record.value('norm')
        self.unitId = forceRef(self.unitIdAsQVariant)
        self.norm = forceString(self.normAsQVariant)
        self.templateId = forceRef(record.value('template_id'))
        self.sex = forceInt(record.value('sex'))
        self.penalty = forceInt(record.value('penalty'))
        age = forceStringEx(record.value('age'))
        self.age = parseAgeSelector(age) if age else None
        self.qVariantType = self.valueType.variantType
#        self.valueSqlFieldTemplate = QtSql.QSqlField('value', self.qVariantType) # wtf?unused
        self.convertDBValueToPyValue = self.valueType.convertDBValueToPyValue
        self.convertQVariantToPyValue = self.valueType.convertQVariantToPyValue
        self.convertPyValueToQVariant = self.valueType.convertPyValueToQVariant
        self.convertPyValueToDBValue  = self.valueType.convertPyValueToDBValue
        self.tableName = self.valueType.tableName
        self.visibleInJobTicket = forceBool(record.value('visibleInJobTicket'))
        self.visibleInTableEditor = forceInt(record.value('visibleInTableEditor'))
        self.isAssignable = forceBool(record.value('isAssignable')) and not self.expr
        self.testId = forceInt(record.value('test_id')) # wtf
        self.defaultEvaluation = forceInt(record.value('defaultEvaluation'))
        self.canChangeOnlyOwner = forceInt(record.value('canChangeOnlyOwner'))
        self.isActionNameSpecifier = forceBool(record.value('isActionNameSpecifier'))
        self.laboratoryCalculator = forceString(record.value('laboratoryCalculator')) # wtf
        self.inActionsSelectionTable = forceInt(record.value('inActionsSelectionTable')) #wtf
        self.editorSizeFactor = forceDouble(record.value('editorSizeFactor')) # wtf
        self.course = forceInt(record.value('course'))
        self.inPlanOperatingDay = forceInt(record.value('inPlanOperatingDay'))
        self.inMedicalDiagnosis = forceInt(record.value('inMedicalDiagnosis'))
        # depends: переменные, указанные в выражении
        # whatDepends: переменные, которые нужно перевычислить после этой.
        #              на самом деле это не просто список, а "план выполнения"
        if self.expr:
            self.co, self.depends = compileAndDetermineDependeces(self.var, self.expr, None)
        else:
            self.co = self.depends = None
        self.whatDepends = None


    @property
    def canBeInitializedBySameAction(self):
        return (
            self.canChangeOnlyOwner > 0
            or self.inActionsSelectionTable > 0
            or self.isActionNameSpecifier
        )


    def shownUp(self, action, clientId):
        self.valueType.shownUp(action, clientId)


    def getValueType(self):
        return CActionPropertyValueTypeRegistry.get(self.typeName, self.valueDomain)


    def getNewRecord(self):
        db = QtGui.qApp.db
        record = db.table('ActionProperty').newRecord()
##        record.append(QtSql.QSqlField(self.valueSqlFieldTemplate)) ???
        record.setValue('type_id', QVariant(self.id))
        record.setValue('unit_id', self.unitIdAsQVariant)
        record.setValue('norm',    self.normAsQVariant)
        return record


    def getValueTableName(self):
        return self.tableName


    def getValue(self, valueId, valueRecords=None):
        if valueRecords is not None:
            if self.isVector:
                result = []
                for record in valueRecords:
                    result.append(self.convertDBValueToPyValue(record.value('value')))
                return result
            else:
                for record in valueRecords:
                    if forceInt(record.value('`index`')) == 0:
                        return self.convertDBValueToPyValue(record.value('value'))
            return None

        db = QtGui.qApp.db
        valueTable = db.table(self.tableName)
        if self.isVector:
            stmt = db.selectStmt(valueTable, 'value', valueTable['id'].eq(valueId), '`index`')
            query = db.query(stmt)
            result = []
            while query.next():
                result.append(self.convertDBValueToPyValue(query.record().value(0)))
            return result
        else:
            stmt = db.selectStmt(valueTable, 'value', [valueTable['id'].eq(valueId), valueTable['index'].eq(0)])
            query = db.query(stmt)
            if query.next():
                return self.convertDBValueToPyValue(query.record().value(0))
            else:
                return None


    def storeRecord(self, record, value):
        db = QtGui.qApp.db
        valueTable  = db.table(self.tableName)
        valueId  = db.insertOrUpdate('ActionProperty', record)

        if self.isVector:
            vector  = value
            indexes = range(len(vector))
        else:
            if value is not None: # иначе не сохраняются нулевые значения тестов
                vector  = [value]
                indexes = [0]
            else:
                vector  = []
                indexes = []

        if indexes:
            stmt = QString()
            stream = QTextStream(stmt, QIODevice.WriteOnly)
            if db.name=='postgres':
                stream << ('INSERT INTO %s (id, index, value) VALUES ' %self.tableName)
            else:
                stream << ('INSERT INTO %s (id, `index`, value) VALUES ' %self.tableName)
            for index in indexes:
                val = self.convertPyValueToDBValue(vector[index])
                if index:
                    stream << ', '
                stream << ('(%d, %d, ' % (valueId, index))
                stream << db.formatQVariant(val.type(), val)
                stream << ')'
            if db.name=='postgres':
                stream << ' ON CONFLICT (id) DO UPDATE SET value = EXCLUDED.value'
            else:
                stream << ' ON DUPLICATE KEY UPDATE value = VALUES(value)'
            db.query(stmt)
            if self.isVector:
                db.deleteRecord(valueTable, [valueTable['id'].eq(valueId), 'NOT('+valueTable['index'].inlist(indexes)+')'])
        else:
            db.deleteRecord(valueTable, [valueTable['id'].eq(valueId)])
        return valueId


    def createEditor(self, action, editorParent, clientId, eventTypeId, eventEditor=None, readOnly=False):
        result = None
        editorClass = self.valueType.getEditorClass()
        if editorClass:
            if eventEditor:
                result = editorClass(action, self.valueDomain if self.typeName == 'Reference' else self.valueType.domain, editorParent, clientId, eventTypeId, eventEditor)
            else:
                if not readOnly:
                    result = editorClass(action, self.valueDomain if self.typeName == 'Reference' else self.valueType.domain, editorParent, clientId, eventTypeId)
                else:
                    result = editorClass(action, self.valueDomain if self.typeName == 'Reference' else self.valueType.domain, editorParent, clientId, eventTypeId, readOnly)
        return result


    def applicable(self, clientSex, clientAge):
        if self.sex and clientSex and clientSex != self.sex:
            return False
        if self.age and clientAge and not checkAgeSelector(self.age, clientAge):
            return False
        return True


    def getPreferredHeight(self):
        return self.valueType.preferredHeightUnit, self.valueType.preferredHeight


    def getHeightFactor(self):
        if self.editorSizeFactor > 0:
            return self.editorSizeFactor
        elif self.editorSizeFactor < 0:
            return 1.0 / abs(self.editorSizeFactor)
        else:
            return 1.0

    def isString(self):
        return isinstance(self.valueType, CStringActionPropertyValueType) or \
               isinstance(self.valueType, CTextActionPropertyValueType)


    def isBoolean(self):
        return isinstance(self.valueType, CBooleanActionPropertyValueType)


    def isHtml(self):
        return self.valueType.isHtml


    def isImage(self):
        return self.valueType.isImage


    def isPacsImage(self):
        return isinstance(self.valueType, CPacsActionPropertyValueType)


    def isJobTicketValueType(self):
        return isinstance(self.valueType, CJobTicketActionPropertyValueType)


    def isNomenclatureValueType(self):
        return isinstance(self.valueType, CNomenclatureActionPropertyValueType)


    def isNomenclatureActiveSubstanceValueType(self):
        return isinstance(self.valueType, CNomenclatureActiveSubstanceActionPropertyValueType)


    def isUrl(self):
        return isinstance(self.valueType, CUrlActionPropertyValueType)


    def isNomenclatureSmnnActionPropertyValueType(self):
        return isinstance(self.valueType, CNomenclatureSmnnActionPropertyValueType)


    def isNomenclatureSmnnGrlsLfActionPropertyValueType(self):
        return isinstance(self.valueType, CNomenclatureSmnnGrlsLfActionPropertyValueType)


    def isNomenclatureCalculationParamActionPropertyValueType(self):
        return isinstance(self.valueType, CNomenclatureCalculationParamActionPropertyValueType)


    def isNomenclatureUsingTypeActionPropertyValueType(self):
        return isinstance(self.valueType, CNomenclatureUsingTypeActionPropertyValueType)


    def evalValue(self, variables):
        try:
            result = eval(self.co, functions, variables)
        except (ZeroDivisionError, TypeError):
            result = None
        return result
