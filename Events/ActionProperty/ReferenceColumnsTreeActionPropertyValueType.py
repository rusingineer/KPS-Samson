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
from library.CTableComboBox import CTableTreeSearchComboBox
from library.Utils import forceRef, forceString
from library.database import decorateString

from ActionPropertyValueType import CActionPropertyValueType


class CReferenceColumnsTreeActionPropertyValueType(CActionPropertyValueType):
    name = 'ReferenceColumnsTree'
    variantType = QVariant.Int

    def __init__(self, domain=None):
        self.domainTable = u''
        self.text = (None, None)
        self.columns = {}
        self.records = None
        self.parentCol = None
        self.childCol = None
        self.fullTextCol = None
        if domain and domain.lstrip().startswith('{'):
            obj = json.loads(domain, object_pairs_hook=OrderedDict)
            self.fields = obj.get(u'fields', [])
            self.parentCol = obj.get(u'parent', None)
            self.childCol = obj.get(u'child', None)
            self.fullTextCol = obj.get(u'fullText', None)
        else:
            self.fields = []
        if domain:
            if domain.lstrip().startswith('{'):
                self.domainTable = forceString(json.loads(domain).get(u'table', u''))
            else:
                self.domainTable = domain.split(';')[0]
                if ' WHERE ' in self.domainTable:
                    idx = self.domainTable.index(' WHERE')
                    self.domainTable = self.domainTable[:idx]
        CActionPropertyValueType.__init__(self, domain)


    class CPropEditor(CTableTreeSearchComboBox):
        def __init__(self, action, domain, parent, clientId, eventTypeId):
            CTableTreeSearchComboBox.__init__(self, parent)
            self._treeModel = None
            self._treePopup = None
            self._treeView = None
            self._pidField = None
            self.initializeEditor(action, domain)


        def initializeEditor(self, action, domain):
            if domain and domain.lstrip().startswith('{'):
                self._initializeEditorJSON(action, domain)


        def _initializeEditorJSON(self, action, domain):
            if action and domain:
                obj = json.loads(domain, object_pairs_hook=OrderedDict)
                dTableName = obj.get(u'table', u'').strip()
                if dTableName.replace('`','').startswith('v1') or dTableName.replace('`','').startswith('1'):
                    tableName = unicode(QtGui.qApp.db.db.databaseName()) + "." + dTableName
                else:
                    tableName = dTableName
                self.fields = obj.get(u'fields', [])
                where = obj.get(u'where', [])
                identify = obj.get(u'identify', {})
                parentCol = obj.get(u'parent', None)
                self.parentCol = parentCol
                childCol = obj.get(u'child', None)
                self.childCol = childCol
                orderCol = obj.get(u'order', None)

                if not tableName:
                    raise Exception(u'Отсутствует название справочной таблицы в «%s»' % domain)
                if not isinstance(tableName, basestring):
                    raise Exception(u'Неправильное описание справочной таблицы в «%s»' % domain)

                if isinstance(self.fields, list):
                    if not all(isinstance(k, basestring) for k in self.fields):
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
                self.setTable(tableName, 
                            fields=self.fields, 
                            order=','.join(self.fields),
                            parentCol = parentCol, 
                            childCol = childCol,
                            orderCol = orderCol,
                            filter=QtGui.qApp.db.joinAnd(cond),
                            rawTable=dTableName)


        def setValue(self, value):
            CTableTreeSearchComboBox.setValue(self, forceRef(value))


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

        if not self.parentCol:
            return u''

        if self.domainTable.replace('`','').startswith('v1') or self.domainTable.replace('`','').startswith('1'):
            tableName = unicode(QtGui.qApp.db.db.databaseName()) + "." + self.domainTable
        else:
            tableName = self.domainTable
        db = QtGui.qApp.db
        table = db.table(tableName)

        nameField = table.findField('name')
        nameField = 'name' if nameField else None
        
        if self.text[0] == v:
            return u'' if self.text[1] is None else self.text[1]

        parts = []
        currentId = v
        seenCodes = set()
        cols = [self.childCol, self.parentCol]
        if nameField:
            cols.insert(1, nameField)
        lookCol = 'id'
        while currentId:
            try:
                records = db.getRecordList(table, cols, where=u'{}={}'.format(lookCol, currentId))
            except Exception:
                records = []

            if records:
                record = records[0]
                if nameField:
                    try:
                        name = forceString(record.value(nameField))
                    except Exception:
                        name = None
                else:
                    name = forceString(record.value(0))

                parts.insert(0, name if name is not None else u'')
                try:
                    parentId = forceRef(record.value(self.parentCol))
                except Exception:
                    parentId = None
            else:
                break
            
            if not self.fullTextCol:
                break
            
            if not parentId:
                break

            if parentId in seenCodes:
                break
            seenCodes.add(parentId)

            try:
                parentRecords = db.getRecordList(table, [self.childCol], where=u"{}={}".format(self.childCol, parentId))
            except Exception:
                parentRecords = []
                
            if not parentRecords:
                break
            try:
                currentId = forceRef(parentRecords[0].value(self.childCol))
            except Exception:
                break
            lookCol = self.childCol

        text = u': '.join([p for p in parts if p])
        self.text = (v, text)
        return text



    def getColumns(self, v):
        if not v:
            return {}
        if self.domainTable.replace('`','').startswith('v1') or self.domainTable.replace('`','').startswith('1'):
            tableName = unicode(QtGui.qApp.db.db.databaseName()) + "." + self.domainTable
        else:
            tableName = self.domainTable 
        table = QtGui.qApp.db.table(tableName)
        cols = [u'id']
        for fieldName in self.fields:
            cols.append(fieldName)
        if v and (u'id' not in self.columns.keys() or self.columns[u'id'] != v):
            self.columns[u'id'] = v
            self.records = QtGui.qApp.db.getRecordList(table, cols, where=u'id={}'.format(v))
        elif not v:
            self.records = None
            self.columns['id'] = None
        for fieldName in self.fields:
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
