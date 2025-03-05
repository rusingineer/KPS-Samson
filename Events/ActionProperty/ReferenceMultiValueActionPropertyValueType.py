# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2021 SAMSON Group. All rights reserved.
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

from library.MultivalueComboBox import CRBMultivalueComboBox, CMultivalueComboBox
from library.PrintInfo import CRBInfo, CInfo
from library.Utils import forceString, trim

from ActionPropertyValueType import CActionPropertyValueType
from library.crbcombobox import CRBModelDataCache


class CReferenceMultiActionPropertyValueType(CActionPropertyValueType):
    name = 'ReferenceMulti'
    variantType = QVariant.String

    def __init__(self, domain=None):
        CActionPropertyValueType.__init__(self, domain)
        try:
            domainObj = json.loads(domain)
            tableName = domainObj.get('tableName', None)
        except:
            tableName = domain
        self._tableName = tableName
        self._addNone = True
        self._needCache = True
        self._filter = ''
        self._order = ''
        self._specialValues = None
        self._data = None
        self._mapShown2Id = {}
        self._mapId2Shown = {}
        self._initRB()


    def _initRB(self):
        import re
        self._data = CRBModelDataCache.getData(self._tableName,
                                               self._addNone,
                                               self._filter,
                                               self._order,
                                               self._specialValues,
                                               self._needCache)
        for itemIndex in xrange(self._data.getCount()):
            _id = self._data.getId(itemIndex)
            shown = u' | '.join([unicode(self._data.getCode(itemIndex)), unicode(self._data.getName(itemIndex))])

            self._mapId2Shown[str(_id)] = re.sub(r"\s+", " ", shown)
            self._mapShown2Id[re.sub(r"\s+", " ", shown)] = unicode(_id)


    class CPropEditor(CRBMultivalueComboBox):
        def __init__(self, action, domain, parent, clientId, eventTypeId):
            CRBMultivalueComboBox.__init__(self, parent)
            try:
                domainObj = json.loads(domain)
                tableName = domainObj.get('tableName', None)
            except:
                tableName = domain
                domainObj = {}
            codeObj = domainObj.get('code', None)
            db = QtGui.qApp.db
            table = db.table(tableName)
            _filter = ''
            if codeObj is not None:
                ok, codes = CActionPropertyValueType._checkAndNormalizeCodeObj(codeObj)
                if ok:
                    _filter = db.joinOr([table['code'].like(code) for code in codes])
                else:
                    raise Exception(u'Неправильное описание code в «%s»' % domain)
            self.setTable(tableName, filter=_filter)


        def setValue(self, value):
            val = u''
            value = forceString(value)
            if value:
                idList = [trim(_id) for _id in value.split(u',')]
                if idList:
                    value = [self._mapId2Shown[_id] for _id in idList]
                    if value:
                        val = u'‚'.join(value)  # изменяю разделитель строки с простой запятой на "нижняя одиночная кавычка" http://htmlbook.ru/samhtml/tekst/spetssimvoly
            CMultivalueComboBox.setValue(self, val)


    class CRBInfoEx(CRBInfo):
        def __init__(self, context, tableName, _id):
            CInfo.__init__(self, context)
            self.id = _id
            self.tableName = tableName


    @staticmethod
    def convertDBValueToPyValue(value):
        return forceString(value)


    convertQVariantToPyValue = convertDBValueToPyValue


    def toText(self, v):
        value = forceString(v)
        if value:
            idList = [trim(_id) for _id in value.split(',')]
            if idList:
                value = [self._mapId2Shown[_id] for _id in idList]
                if value:
                    return u'‚ '.join(value)
        return u''


    def toInfo(self, context, v):
        value = forceString(v)
        infoList = []
        if value:
            infoList = [CReferenceMultiActionPropertyValueType.CRBInfoEx(context, self._tableName, trim(_id)) for _id in value.split(',')]
        return infoList


    def getTableName(self):
        return self.tableNamePrefix + 'String'
