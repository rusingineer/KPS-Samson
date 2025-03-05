# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2024 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

import json

from PyQt4 import QtGui
from PyQt4.QtCore import QVariant

from library.PrintInfo import CRBInfoWithIdentification
from library.CRBSearchComboBox  import CRBSearchComboBox
from library.Utils              import forceRef, forceString, trim
from library.database           import decorateString

from ActionPropertyValueType import CActionPropertyValueType


class CReferenceActionPropertyValueType(CActionPropertyValueType):
    name         = 'Reference'
    variantType  = QVariant.Int

    def __init__(self, domain=None):
        self.domainTable = u''
        if domain:
            if domain.lstrip().startswith('{'):  # через JSON
                self.domainTable = forceString(json.loads(domain).get(u'table', u''))
            else:  # через «таблица;поле;свойство»
                self.domainTable = domain.split(';')[0]
                if ' WHERE ' in self.domainTable:
                    idx = self.domainTable.index(' WHERE')
                    self.domainTable = self.domainTable[:idx]
        CActionPropertyValueType.__init__(self, domain)


    class CPropEditor(CRBSearchComboBox):
        def __init__(self, action, domain, parent, clientId, eventTypeId):
            CRBSearchComboBox.__init__(self, parent)
            self.initializeEditor(action, domain)


        def initializeEditor(self, action, domain):
            if domain and domain.lstrip().startswith('{'):
                self._initializeEditorJSON(action, domain)
            else:
                self._initializeEditorDefault(action, domain)


        # через «таблица;поле;свойство»
        def _initializeEditorDefault(self, action, domain):
            if action and domain:
                domainList = domain.split(u';') # engl
                if len(domainList) != 3:
                    domainList = domain.split(u';') # rus
                if len(domainList) == 3:
                    tableName = trim(domainList[0])
                    fieldName = trim(domainList[1])
                    propertyName = trim(domainList[2])
                    valueId = action[propertyName] if (propertyName in action._actionType._propertiesByName) else None
                    if valueId:
                        cond = fieldName + ' = ' + forceString(valueId)
                        if ' WHERE ' in tableName:
                            tableName, where = tableName.split(' WHERE ')[:2]
                            cond = '(%s) AND (%s)' % (cond, where)
                        self.setTable(tableName.strip(), filter=cond)
                        return
            if ' WHERE ' in domain:
                db = QtGui.qApp.db
                tableName, cond = domain.split(' WHERE ', 1)
                if '{action.setPersonId}' in cond:
                    setPersonId = action.getSetPersonId()
                    cond = cond.replace('{action.setPersonId}', unicode(setPersonId) if setPersonId else 'NULL')
                if '{action.personId}' in cond:
                    personId = action.getPersonId()
                    cond = cond.replace('{action.personId}', unicode(personId) if personId else 'NULL')
                if '{action.createPersonId}' in cond:
                    createPersonId = action.getCreatePersonId()
                    cond = cond.replace('{action.createPersonId}', unicode(createPersonId) if createPersonId else 'NULL')
                if '{action.modifyPersonId}' in cond:
                    modifyPersonId = action.getModifyPersonId()
                    cond = cond.replace('{action.modifyPersonId}', unicode(modifyPersonId) if modifyPersonId else 'NULL')
                if '{action.begDate}' in cond:
                    begDate = action.getBegDate()
                    cond = cond.replace('{action.begDate}', db.formatDate(begDate) if not begDate.isNull() else 'NULL')
                if '{action.begDatetime}' in cond:
                    begDatetime = action.getBegDatetime()
                    cond = cond.replace('{action.begDatetime}', db.formatDate(begDatetime) if not begDatetime.isNull() else 'NULL')
                if '{action.endDate}' in cond:
                    endDate = action.getEndDate()
                    cond = cond.replace('{action.endDate}', db.formatDate(endDate) if not endDate.isNull() else 'NULL')
                if '{action.endDatetime}' in cond:
                    endDatetime = action.getEndDatetime()
                    cond = cond.replace('{action.endDatetime}', db.formatDate(endDatetime) if not endDatetime.isNull() else 'NULL')
                if '{currentPersonId}' in cond:
                    currentPersonId = QtGui.qApp.userId
                    cond = cond.replace('{currentPersonId}', unicode(currentPersonId) if currentPersonId else 'NULL')
                self.setTable(tableName.strip(), filter=cond)
                return
            self.setTable(domain)


        # через JSON
        def _initializeEditorJSON(self, action, domain):
            if action and domain:
                obj = json.loads(domain)
                tableName = obj.get(u'table', u'').strip()
                fields = obj.get(u'fields', {})
                where = obj.get(u'where', [])
                identify = obj.get(u'identify', {})

                if not tableName:
                    raise Exception(u'Отсутствует название справочной таблицы в «%s»' % domain)
                if not isinstance(tableName, basestring):
                    raise Exception(u'Неправильное описание справочной таблицы в «%s»' % domain)

                if isinstance(fields, dict):
                    if not all(isinstance(k, basestring) for k in fields.keys()):
                        raise Exception(u'Неправильное описание полей для фильтрации в «%s»' % domain)
                    if not all(isinstance(v, basestring) for v in fields.values()):
                        raise Exception(u'Неправильное описание полей для фильтрации в «%s»' % domain)
                else:
                    raise Exception(u'Неправильное описание полей для фильтрации в «%s»' % domain)

                ok, cond = CActionPropertyValueType._checkAndNormalizeCodeObj(where)
                if not ok:
                    raise Exception(u'Неправильное описание where в «%s»' % domain)

                if isinstance(identify, dict):
                    if not all(isinstance(k, basestring) for k in fields.keys()):
                        raise Exception(u'Неправильное описание полей для идентификации в «%s»' % domain)
                    if not all(isinstance(v, basestring) for v in fields.values()):
                        raise Exception(u'Неправильное описание полей для идентификации в «%s»' % domain)
                else:
                    raise Exception(u'Неправильное описание полей для идентификации в «%s»' % domain)

                for fieldName, propName in fields.items():
                    if propName in action._actionType._propertiesByName:
                        valueId = action[propName]
                        if valueId:
                            cond.append(fieldName + ' = ' + decorateString(forceString(valueId)))

                stmt = (u'EXISTS(SELECT NULL'
                        u' FROM {tableId}'
                        u' JOIN rbAccountingSystem ON {tableId}.system_id = rbAccountingSystem.id'
                        u' WHERE {tableId}.deleted = 0 AND {tableId}.master_id = {masterTable}.id'
                        u' AND urn = "{urn}" AND {values})')
                for urn, values in identify.items():
                    ok, normValues = CActionPropertyValueType._checkAndNormalizeCodeObj(values)
                    if not ok:
                        raise Exception(u'Неправильное описание значений для идентификации в «%s»' % domain)
                    tableId = tableName + u'_Identification'
                    values = QtGui.qApp.db.joinOr([
                        (tableId + u'.value LIKE ' + decorateString(v))
                        for v in normValues
                    ])
                    cond.append(stmt.format(tableId=tableId, masterTable=tableName, urn=urn, values=values))

                self.setTable(tableName, filter=QtGui.qApp.db.joinAnd(cond))


        def setValue(self, value):
            CRBSearchComboBox.setValue(self, forceRef(value))


        def lookup(self):
            self.setCodeFilter(self._searchString)
            if bool(self._searchString) and self._model.rowCount() > 1:
                self.setCurrentIndex(1)
            else:
                self.setCurrentIndex(0)



    @staticmethod
    def convertDBValueToPyValue(value):
        return forceRef(value)


    convertQVariantToPyValue = convertDBValueToPyValue


    def toText(self, v):
        return forceString(QtGui.qApp.db.translate(self.domainTable, 'id', v, 'CONCAT(code,\' | \',name)'))


    def toInfo(self, context, v):
        info = CRBInfoWithIdentification(context, v)
        info.tableName = self.domainTable
        return info


    def getTableName(self):
        return self.tableNamePrefix + self.domainTable

