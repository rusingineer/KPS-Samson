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
from collections import OrderedDict

from PyQt4 import QtGui
from PyQt4.QtCore import QVariant

from library.PrintInfo import CInfo
from library.CTableComboBox import CTableSearchComboBox
from library.Utils import forceRef, forceString
from library.database import decorateString

from ActionPropertyValueType import CActionPropertyValueType


class CReferenceColumnsActionPropertyValueType(CActionPropertyValueType):
    name = 'ReferenceColumns'
    variantType  = QVariant.Int

    def __init__(self, domain=None):
        self.domainTable = u''
        self.text = (None, None)
        self.columns = {}
        self.records = None
        if domain and domain.lstrip().startswith('{'):
            obj = json.loads(domain, object_pairs_hook=OrderedDict)
            self.fields = obj.get(u'fields', {})
        else:
            self.fields = {}
        if domain:
            if domain.lstrip().startswith('{'):  # через JSON
                self.domainTable = forceString(json.loads(domain).get(u'table', u''))
            else:  # через «таблица;поле;свойство»
                self.domainTable = domain.split(';')[0]
                if ' WHERE ' in self.domainTable:
                    idx = self.domainTable.index(' WHERE')
                    self.domainTable = self.domainTable[:idx]
        CActionPropertyValueType.__init__(self, domain)


    class CPropEditor(CTableSearchComboBox):
        def __init__(self, action, domain, parent, clientId, eventTypeId):
            CTableSearchComboBox.__init__(self, parent)
            self.initializeEditor(action, domain)


        def initializeEditor(self, action, domain):
            if domain and domain.lstrip().startswith('{'):
                self._initializeEditorJSON(action, domain)


        # через JSON
        def _initializeEditorJSON(self, action, domain):
            if action and domain:
                obj = json.loads(domain, object_pairs_hook=OrderedDict)
                dTableName = obj.get(u'table', u'').strip()
                if dTableName.replace('`','').startswith('v1') or dTableName.replace('`','').startswith('1'):
                    tableName = unicode(QtGui.qApp.db.db.databaseName()) + "." + dTableName
                else:
                    tableName = dTableName
                self.fields = obj.get(u'fields', {})
                where = obj.get(u'where', [])
                identify = obj.get(u'identify', {})
                if not tableName:
                    raise Exception(u'Отсутствует название справочной таблицы в «%s»' % domain)
                if not isinstance(tableName, basestring):
                    raise Exception(u'Неправильное описание справочной таблицы в «%s»' % domain)
            
                if isinstance(self.fields, dict):
                    if not all(isinstance(k, basestring) for k in self.fields.keys()):
                        raise Exception(u'Неправильное описание полей для фильтрации в «%s»' % domain)
                    if not all(isinstance(v, basestring) for v in self.fields.values()):
                        raise Exception(u'Неправильное описание полей для фильтрации в «%s»' % domain)
                else:
                    raise Exception(u'Неправильное описание полей для фильтрации в «%s»' % domain)

                ok, cond = CActionPropertyValueType._checkAndNormalizeCodeObj(where)
                if not ok:
                    raise Exception(u'Неправильное описание where в «%s»' % domain)

                if isinstance(identify, dict):
                    if not all(isinstance(k, basestring) for k in identify.keys()):
                        raise Exception(u'Неправильное описание полей для идентификации в «%s»' % domain)
                    if not all(isinstance(v, basestring) for v in identify.values()):
                        raise Exception(u'Неправильное описание полей для идентификации в «%s»' % domain)
                else:
                    raise Exception(u'Неправильное описание полей для идентификации в «%s»' % domain)

                for fieldName, propName in self.fields.items():
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

                self.setTable(tableName, fields=','+','.join(self.fields.keys()), fieldNames=list(self.fields.values()), order=','.join(self.fields.keys()), filter=QtGui.qApp.db.joinAnd(cond), rawTable=dTableName)


        def setValue(self, value):
            CTableSearchComboBox.setValue(self, forceRef(value))


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
        if not v:
            return u''
        if self.domainTable.replace('`','').startswith('v1') or self.domainTable.replace('`','').startswith('1'):
            tableName = unicode(QtGui.qApp.db.db.databaseName()) + "." + self.domainTable
        else:
            tableName = self.domainTable
        table = QtGui.qApp.db.table(tableName)
        nameField = table.findField('name')
        if nameField:
            field = "name"
        else:
            field = "*"
        if self.text[0] != v:
            self.text = (v, forceString(QtGui.qApp.db.translate(tableName, 'id', v, field)))
        return '' if self.text[1] is None else self.text[1]
    
    
    def getColumns(self, v):
        if self.domainTable.replace('`','').startswith('v1') or self.domainTable.replace('`','').startswith('1'):
            tableName = unicode(QtGui.qApp.db.db.databaseName()) + "." + self.domainTable
        else:
            tableName = self.domainTable
        table = QtGui.qApp.db.table(tableName)
        cols = [u'id']
        for fieldName, propName in self.fields.items():
            cols.append(fieldName)
        if v and (u'id' not in self.columns.keys() or self.columns[u'id'] != v):
            self.columns[u'id'] = v
            self.records = QtGui.qApp.db.getRecordList(table, cols, where=u'id={}'.format(v))
        elif not v:
            self.records = None
            self.columns['id'] = None
        for fieldName, propName in self.fields.items():
            if self.records:
                cleanFieldName = fieldName.strip(' `"[]')
                self.columns[fieldName] = forceString(self.records[0].value(cleanFieldName))
            elif not v:
                self.columns[fieldName] = ''
        return self.columns
    
    
    def toInfo(self, context, v):
        info = CReferenceColumnsInfo(context)
        info.id = v
        info.text = self.toText(v)
        info.tableName = self.domainTable
        for fieldName, propName in self.getColumns(v).items():
            safeName = fieldName.strip(' `"[]').replace('-', '_')
            setattr(info, safeName, propName)
        return info
    
    def getTableName(self):
        return self.tableNamePrefix + "Integer"
 
    
class CReferenceColumnsInfo(CInfo):
    u'Класс для ReferenceColumns'
    tableName = '' # for pylint

    def __init__(self, context):
        CInfo.__init__(self, context)
        self.id = None
        self.text = ''

    def __str__(self):
        return self.text
    
    def load(self):
        if not self._loaded:
            self._ok = bool(self.id)
            self._loaded = True
        return self
    
    def __nonzero__(self):
        if self.id:
            return True
        else:
            return False