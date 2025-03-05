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


from library.Utils import forceString, toVariant


class CActionPropertyValueTypeRegistry(object):
    # вспомогательное средство для создания CActionPropertyValueType по имени/обл.определения
    nameList = []
    mapNameToValueType = {}
    cache = {}

    @classmethod
    def register(cls, type_):
        cls.nameList.append(type_.name)
        cls.mapNameToValueType[type_.name.lower()] = type_


    @classmethod
    def normTypeName(cls, name):
        type_ = cls.mapNameToValueType.get(name.lower(), None)
        if type_:
            return type_.name
        else:
            return name


    @classmethod
    def get(cls, typeName, domain):
        name = typeName.lower()
        key = (name, domain)
        if key in cls.cache:
            result = cls.cache[key]
        else:
            result = cls.mapNameToValueType[name](domain)
            cls.cache[key] = result
        return result


    @classmethod
    def getDomainEditorClass(cls, name):
        # DomainEditor должен быть наследником QDialog,
        # и предоставлять методы setDomain, exec и getDomain
        # при этом под Domain подразумевается строка, скорее всего - в json
        type_ = cls.mapNameToValueType.get(name.lower(), None)
        if type_:
            return type_.getDomainEditorClass()
        else:
            return name


# ################################################


class CActionPropertyValueType(object):
    tableNamePrefix = 'ActionProperty_'
    expandingHeight = False
    preferredHeight = 1
    preferredHeightUnit = 1
    isCopyable = True
    isHtml = False
    isImage = False
    initPresetValue = False
    name = None  # for lint
    CPropEditor = None  # for lint
    cacheText = False

    def __init__(self, domain=None):
        self.domain = domain
        self.tableName = self.getTableName()

    @classmethod
    def getTableName(cls):
        return cls.tableNamePrefix + cls.name

    @staticmethod
    def convertPyValueToQVariant(value):
        return toVariant(value)

    @staticmethod
    def convertPyValueToDBValue(value):
        return toVariant(value)

    def getEditorClass(self):
        return self.CPropEditor

    @staticmethod
    def getDomainEditorClass():
        return None

    def toText(self, v):
        return v

    def toImage(self, v):
        return None

    def toInfo(self, context, v):
        return forceString(v) if v else ''

    def getPresetValue(self, action):
        return None

    def shownUp(self, action, clientId):
        pass

    @staticmethod
    def _checkAndNormalizeCodeObj(codeObj):
        if isinstance(codeObj, (basestring, int)):
            return True, [unicode(codeObj)]
        if isinstance(codeObj, list) and all(isinstance(code, (basestring, int)) for code in codeObj):
            return True, [unicode(code) for code in codeObj]
        return False, None
